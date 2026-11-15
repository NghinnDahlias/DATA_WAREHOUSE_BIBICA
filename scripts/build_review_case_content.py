"""Prepare low-star review text for local UI; emit counts only, never raw text."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg.rows import dict_row
from DW.etl.common import checksum, rows, source_path
from DW.etl.ratings import project_scraped_rating
from src.api.db import database_dsn
from src.api.review_privacy import CONTENT_VERSION, redact_review


def main():
    path = source_path('ratings')
    sha = checksum(path)
    with psycopg.connect(database_dsn(), row_factory=dict_row) as c:
        c.execute('SELECT pg_advisory_xact_lock(4031262)')
        source = c.execute("SELECT source_file_key FROM dw.dim_source_file WHERE source_sha256=%s AND source_file_name=%s AND sheet_name='Ratings'", (sha, path.name)).fetchall()
        if len(source) != 1:
            raise RuntimeError('Ratings source checksum is not uniquely registered; run repository ETL first.')
        accepted = c.execute('''SELECT review_key,physical_row_number,source_row_hash,star_level
            FROM dw.fact_review_candidate WHERE source_file_key=%s AND star_level<=3
            AND review_quality_status='ACCEPTED' ''', (source[0]['source_file_key'],)).fetchall()
        by_row = {r['physical_row_number']: r for r in accepted}
        prepared = []
        for row_no, raw in rows(path):
            if row_no not in by_row:
                continue
            r = by_row[row_no]
            projected = project_scraped_rating(raw)
            if int(projected['star_level']) != r['star_level']:
                raise RuntimeError('Review source row no longer agrees with warehouse.')
            text = redact_review(projected.get('review_text'), [raw.get('name')])
            prepared.append((r['review_key'], sha, r['source_row_hash'], CONTENT_VERSION, text))
        if len(prepared) != len(accepted) or checksum(path) != sha:
            raise RuntimeError('Incomplete or changed source; no review content was written.')
        c.execute('DELETE FROM dw.review_case_content')
        if prepared:
            with c.cursor() as cur:
                cur.executemany('''INSERT INTO dw.review_case_content
                    (review_key,source_sha256,source_row_hash,content_version,redacted_text)
                    VALUES (%s,%s,%s,%s,%s)''', prepared)
    print(f'PASS: prepared {len(prepared)} redacted review cases; no source or business fact updates.')


if __name__ == '__main__':
    main()
