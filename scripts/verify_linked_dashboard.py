"""Read-only full-data evidence for the linked dashboard. No raw records printed."""
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.api.db import snapshot
from scripts.verify_phase2 import business_fingerprints


def get(endpoint, params=None):
    with urlopen('http://127.0.0.1:8001/api/v1/'+endpoint+'?'+urlencode(params or {}), timeout=45) as response:
        return json.load(response)


def main():
    report={'executed_at':datetime.now(timezone.utc).isoformat(),'checks':{},'cohorts':[]}
    checks=report['checks']
    for params in [{},{'channel':'SHOPEE'},{'store':'bibica_tiktok_shop'},
                   {'store':'quasure_specialized_store'},{'status':'CANCELED'},
                   {'province':'Hà Nội','warehouse_region':'Hồ Chí Minh','category':'Bánh'},
                   {'product_key':8},{'product_key':8,'category':'Ngũ cốc'},
                   {'start_date':'2026-07-01','end_date':'2026-07-31','category':'Bánh'},
                   {'status':'COMPLETED','store':'bibica_official_store','province':'Hà Nội'}]:
        started=time.perf_counter()
        board=get('overview/dashboard',params)
        independent=get('overview/kpis',params)['data']
        d=board['data']
        conservation={
            'kpis_equal':d['kpis']==independent,
            'store_orders':sum(r['orders'] for r in d['stores'])==independent['orders'],
            'month_orders':sum(r['orders'] for r in d['monthly'])==independent['orders'],
            'month_money':sum(Decimal(r['completed_payable'] or '0') for r in d['monthly'])==Decimal(independent['completed_payable'] or '0'),
            'category_units':sum(Decimal(r['completed_units'] or '0') for r in d['categories'])==Decimal(independent['completed_units'] or '0'),
            'snapshot':board['meta']['snapshot']=='REPEATABLE READ',
        }
        # Rank money is source-line money, independent of the order payable KPI.
        for p in d['products']:
            assert isinstance(p['native_sku_id'],(str,type(None)))
        report['cohorts'].append({'filters':params,'checks':conservation,'orders':independent['orders'],
                                  'seconds':round(time.perf_counter()-started,3)})
    checks['all_cohorts_reconcile']=all(all(c['checks'].values()) for c in report['cohorts'])
    baseline=json.loads((ROOT/'reports/phase3_api.json').read_text('utf8'))
    with snapshot() as c:
        report['fingerprints']=business_fingerprints(c)
        checks['serial_sql_guard']=c.execute('SHOW max_parallel_workers_per_gather').fetchone()['max_parallel_workers_per_gather']=='0'
    checks['business_fingerprints_unchanged']=report['fingerprints']==baseline['fingerprints']
    full=get('overview/dashboard')['data']['kpis']
    report['kpis']={k:full[k] for k in baseline['kpis']}
    checks['full_kpis_unchanged']=report['kpis']==baseline['kpis']
    report['source_hashes']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
        for base in ['frontend/src','src/api'] for p in (ROOT/base).rglob('*') if p.is_file() and p.suffix in ['.py','.jsx','.js','.css']}
    report['status']='PASS' if all(checks.values()) else 'FAIL'
    (ROOT/'reports/linked_reconciliation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps({'status':report['status'],'cohorts':len(report['cohorts']),'checks':checks}))
    if report['status']!='PASS':raise SystemExit(1)


if __name__=='__main__':main()
