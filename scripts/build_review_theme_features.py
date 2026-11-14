"""Build privacy-preserving review topic features from the immutable ratings workbook."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg
from psycopg.rows import dict_row

from DW.etl.common import checksum, rows, source_path
from DW.etl.ratings import project_scraped_rating
from src.api.db import database_dsn
from src.dss.review_audit import VERSION, classify_review


def main():
    path = source_path("ratings")
    sha = checksum(path)
    parsed = []
    with psycopg.connect(database_dsn(), connect_timeout=5, row_factory=dict_row) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(4031262)")
        source = conn.execute(
            """
            SELECT source_file_key, sheet_name
            FROM dw.dim_source_file
            WHERE source_file_name = %s
              AND source_sha256 = %s
              AND source_kind = 'tiktok_reviews'
            ORDER BY source_file_key
            """,
            (path.name, sha),
        ).fetchall()

        if len(source) != 1:
            raise RuntimeError(
                f"Expected exactly one registered ratings source file; found {len(source)}. "
                "Check ETL registration and source checksum before building features."
            )

        source_file_key = source[0]["source_file_key"]
        sheet_name = source[0]["sheet_name"]

        review_rows = conn.execute(
            """
            SELECT physical_row_number, review_key
            FROM dw.fact_review_candidate
            WHERE source_file_key = %s
              AND source_sheet_name = %s
              AND review_quality_status = 'ACCEPTED'
            """,
            (source_file_key, sheet_name),
        ).fetchall()
        review_key_by_row = {r["physical_row_number"]: r["review_key"] for r in review_rows}

        # Source text exists only in process memory. Only controlled labels are persisted.
        for physical_row_number, raw_row in rows(path):
            review_key = review_key_by_row.get(physical_row_number)
            if review_key is None:
                continue
            projected = project_scraped_rating(raw_row)
            result = classify_review(projected.get("review_text"))
            parsed.append((
                review_key,
                json.dumps(result["labels"], ensure_ascii=False),
                result["severity"],
                result["text_present"],
                VERSION,
                sha,
            ))

        if len(parsed) != len(review_key_by_row):
            raise RuntimeError(
                f"Accepted DW reviews ({len(review_key_by_row)}) do not match parsed source rows "
                f"({len(parsed)}). No feature rows were written."
            )

        with conn.transaction():
            conn.execute("DELETE FROM dw.review_theme_feature")
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO dw.review_theme_feature
                        (review_key, labels, severity, text_present, audit_version, source_sha256)
                    VALUES (%s, %s::jsonb, %s, %s, %s, %s)
                    """,
                    parsed,
            )

        stored = conn.execute("SELECT count(*) AS n FROM dw.review_theme_feature").fetchone()["n"]
        if stored != len(parsed):
            raise RuntimeError(f"Feature row count mismatch: expected {len(parsed)}, got {stored}")

    print(f"PASS: built {len(parsed)} privacy-preserving review feature rows ({VERSION})")


if __name__ == "__main__":
    main()
