"""Full-data Phase 3 API evidence. Outputs aggregates and hashes, never source rows."""
import json
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from DW.etl.common import checksum
from DW.etl.sources import SOURCES
from src.api.app import app
from src.api.db import snapshot
from scripts.verify_phase2 import business_fingerprints


def main():
    path = ROOT / 'reports/phase3_api.json'
    report = {'status': 'RUNNING', 'executed_at': datetime.now(timezone.utc).isoformat(), 'checks': {}, 'requests': []}
    path.write_text(json.dumps(report, indent=2), encoding='utf8')
    checks = report['checks']
    client = TestClient(app)

    def get(url, params=None):
        t = time.perf_counter()
        r = client.get('/api/v1/' + url, params=params or {})
        report['requests'].append({'endpoint': url, 'status': r.status_code, 'seconds': round(time.perf_counter()-t, 4)})
        assert r.status_code == 200, (url, r.status_code)
        return r.json()['data']

    try:
        base = get('overview/kpis')
        checks['full_counts'] = (base['orders'], base['accepted_lines'], base['reviews']) == (127588, 178517, 5625)
        checks['money_and_units'] = Decimal(base['completed_payable']) == Decimal('9175209123') and Decimal(base['completed_units']) == Decimal('168478')
        meta = get('meta')
        checks['four_canonical_categories'] = {c['canonical_category'] for c in meta['categories']} == {'Bánh', 'Kẹo', 'Ngũ cốc', 'Quà tặng'}
        for channel, sources in [('SHOPEE', ['shopee_bibica', 'shopee_quasure']), ('TIKTOK', ['tiktok_bibica'])]:
            k = get('overview/kpis', {'channel': channel})
            individual = [get('overview/kpis', {'source': s}) for s in sources]
            checks['channel_' + channel] = k['orders'] == sum(x['orders'] for x in individual) and Decimal(k['completed_payable']) == sum(Decimal(x['completed_payable']) for x in individual)
        checks['contradictory_channel_store_empty'] = get('overview/kpis', {'channel': 'SHOPEE', 'store': 'bibica_tiktok_shop'})['orders'] == 0
        for dim in ['source', 'store', 'status', 'month', 'category', 'province', 'warehouse', 'warehouse_region', 'product']:
            rows = get('analytics/' + dim, {'limit': 200})
            checks['breakdown_' + dim] = bool(rows) and len(rows) <= 200
        for w in meta['warehouses']:
            params = {'warehouse_key': w['warehouse_key'], 'start_date': '2026-06-01', 'end_date': '2026-06-30'}
            actual = get('overview/kpis', params)
            with snapshot() as c:
                oracle = c.execute("""SELECT count(*) orders,sum(o.order_payable) FILTER(WHERE o.canonical_status='COMPLETED') completed
                    FROM analytics.v_orders o WHERE o.order_date BETWEEN '2026-06-01' AND '2026-06-30'
                    AND EXISTS(SELECT 1 FROM analytics.v_items i WHERE i.order_key=o.order_key AND i.warehouse_key=%s)""", (w['warehouse_key'],)).fetchone()
            checks['warehouse_date_' + str(w['warehouse_key'])] = actual['orders'] == oracle['orders'] and (Decimal(actual['completed_payable']) if actual['completed_payable'] is not None else None) == oracle['completed']
        themes = get('customer/review-themes')
        checks['all_reviews_audited'] = themes['availability'] == 'READY' and themes['audited_reviews'] == themes['total_reviews'] == 5625
        checks['negative_review_count'] = themes['negative_reviews_le2'] == 262
        checks['no_review_text_in_response'] = themes['content_returned'] is False and set(themes) == {'total_reviews', 'audited_reviews', 'text_present_reviews', 'negative_reviews_le2', 'reviews_without_explicit_issue_label', 'safety_signal_reviews', 'labels', 'availability', 'audit_version', 'label_status', 'date_basis', 'content_returned', 'warning'}
        for params in [{'channel':'SHOPEE'}, {'store':'bibica_official_store'}, {'store':'quasure_specialized_store'}]:
            r = get('customer/review-themes', params)
            checks['absent_ratings_' + next(iter(params.values()))] = r['availability'] == 'UNAVAILABLE_NO_SHOPEE_RATING_SOURCE' and r['safety_signal_reviews'] is None and r['labels'] == []
        with snapshot() as c:
            report['fingerprints'] = business_fingerprints(c)
            baseline = json.loads((ROOT / 'reports/reference_reconciliation.json').read_text(encoding='utf8'))
            for grain, value in report['fingerprints'].items():
                checks['unchanged_' + grain] = value == baseline['fingerprints'][grain]['repo']
            raw = c.execute('SELECT source_code,sha256 FROM ops.source_current ORDER BY 1').fetchall()
            checks['four_native_sources_unchanged'] = len(raw) == 4 and all(checksum(ROOT / 'Data/Data_Source_Raw' / SOURCES[r['source_code']][0]) == r['sha256'] for r in raw)
            n = c.execute("SELECT count(*) n FROM pg_constraint WHERE contype='f' AND connamespace='dw'::regnamespace").fetchone()['n']
            checks['56_core_fk_plus_one_theme_fk'] = n == 57
            label_counts = c.execute("""SELECT label,count(*) mentions,count(*) FILTER(WHERE r.star_level<=2) negative_mentions
                FROM dw.review_theme_feature f JOIN dw.fact_review_candidate r USING(review_key)
                CROSS JOIN LATERAL jsonb_array_elements_text(f.labels) label GROUP BY label ORDER BY label""").fetchall()
            checks['theme_aggregate_matches_review_grain'] = sorted(themes['labels'], key=lambda x:x['label']) == label_counts
            checks['sql_guard_retained'] = c.execute('SHOW max_parallel_workers_per_gather').fetchone()['max_parallel_workers_per_gather'] == '0'
        report['kpis'] = {k:base[k] for k in ['orders','accepted_lines','reviews','completed_payable','completed_units','low_reviews']}
        report['review_themes'] = themes
        report['status'] = 'PASS' if all(checks.values()) else 'FAIL'
    except Exception as error:
        report['status'] = 'FAIL'
        report['error_type'] = type(error).__name__
        raise
    finally:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf8')
    print(json.dumps({'status':report['status'], 'checks':len(checks), 'passed':sum(checks.values()), 'requests':len(report['requests'])}))
    if report['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
