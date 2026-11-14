"""Read-only regression for SKU lookup and unchanged DW business data."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.api.db import snapshot
from scripts.verify_phase2 import business_fingerprints


def get(path, **params):
    with urlopen('http://127.0.0.1:8001/api/v1/' + path + '?' + urlencode(params), timeout=30) as response:
        return json.load(response)['data']


def main():
    before = json.loads((ROOT/'reports/phase3_api.json').read_text('utf8'))
    after = get('overview/kpis')
    checks = {'full_kpis_unchanged': all(after[k] == v for k, v in before['kpis'].items())}
    rare = get('overview/kpis', product_key=8)
    checks['reported_sku_kpis'] = (rare['orders'], rare['canceled_orders'], float(rare['completed_units']), float(rare['completed_payable'])) == (4, 3, 1, 57615)
    p = get('products', product_key=8)[0]
    checks['sku_text'] = isinstance(p['native_sku_id'], str)
    checks['sku_search'] = any(r['product_key'] == 8 for r in get('products', search=p['native_sku_id']))
    pages = get('products', search='Olive', sort='orders', limit=10) + get('products', search='Olive', sort='orders', limit=10, offset=10)
    checks['popularity_pages'] = [(r['orders'], r['product_key']) for r in pages] == sorted([(r['orders'], r['product_key']) for r in pages], key=lambda x: (-x[0], x[1]))
    with snapshot() as connection:
        fingerprints = business_fingerprints(connection)
        direct = connection.execute('''SELECT count(*) orders,count(*) FILTER(WHERE canonical_status='CANCELED') canceled,
          sum(order_payable) FILTER(WHERE canonical_status='COMPLETED') payable FROM analytics.v_orders o
          WHERE EXISTS(SELECT 1 FROM analytics.v_items i WHERE i.order_key=o.order_key AND i.product_key=8)''').fetchone()
    checks['direct_order_grain'] = (direct['orders'], direct['canceled'], float(direct['payable'])) == (4, 3, 57615)
    checks['business_fingerprints_unchanged'] = fingerprints == before['fingerprints']
    headers = json.loads((ROOT/'reports/product_filter_source_headers.json').read_text('utf8'))
    checks['no_native_expiry_headers'] = all(not x['expiry_headers'] for x in headers.values())
    report = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'executed_at': datetime.now(timezone.utc).isoformat(),
              'checks': checks, 'kpis': {k: after[k] for k in before['kpis']}, 'reported_sku': {'product_key': 8, 'orders': rare['orders'], 'canceled_orders': rare['canceled_orders'], 'completed_units': rare['completed_units'], 'completed_payable': rare['completed_payable']},
              'fingerprints': fingerprints, 'source_headers': headers,
              'source_hashes': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/api/repository.py', 'src/api/models.py', 'src/api/app.py', 'frontend/src/components/ProductPicker.jsx', 'frontend/src/pages/Dss.jsx']}}
    (ROOT/'reports/product_filter_reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
    print(json.dumps({'status': report['status'], 'checks': checks}))
    if not all(checks.values()): raise SystemExit(1)


if __name__ == '__main__':
    main()
