"""Validate real reports and current source; do not synthesize test results."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT/name).read_text('utf8'))


def main():
    backend=read('reports/phase2_tests.json')
    frontend=read('reports/linked_frontend.json')
    browser=read('reports/linked_browser.json')['stats']
    focused=read('reports/linked_final_target_browser.json')['stats']
    reconciliation=read('reports/linked_reconciliation.json')
    main_layout=read('reports/linked_layouts.json')
    overview=read('reports/linked_board_layouts.json')
    details=read('reports/linked_detail_layouts.json')
    expanded=read('reports/scroll_detail_layouts.json')
    build_bytes=(ROOT/'.runtime/linked-board-build.log').read_bytes()
    build_log=build_bytes.decode('utf-16' if build_bytes.startswith(b'\xff\xfe') else 'utf-8-sig',errors='replace')
    checks={
        'backend':backend['status']=='PASS' and backend['tests']==120 and not any(backend[k] for k in ['failures','errors','skipped']),
        'frontend':frontend['success'] and frontend['numPassedTests']==41 and frontend['numFailedTests']==0,
        'browser':browser['expected']==22 and all(browser[k]==0 for k in ['unexpected','skipped','flaky']),
        'loaded_detail_and_sku_recheck':focused['expected']==2 and all(focused[k]==0 for k in ['unexpected','skipped','flaky']),
        'build':'built in' in build_log,
        'read_only_reconciliation':reconciliation['status']=='PASS' and len(reconciliation['cohorts'])==10 and all(reconciliation['checks'].values()),
        'current_source_hashes':all((ROOT/name).is_file() and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in reconciliation['source_hashes'].items()),
        'main_layouts':main_layout['status']=='PASS' and len(main_layout['measurements'])==20,
        'overview_cards':len(overview)==3 and all(r['docX']<=1 and r['docY']<=1 and all(c['overflow']<=3 for c in r['cards']) and all(t['x']<=1 for t in r['tables']) for r in overview),
        'all_detail_panels':len(details)==22 and all(p['vertical']<=4 and p['horizontal']<=4 for r in details for p in r['panels']),
        'expanded_panels':len(expanded)==45 and all(r['overflow']<=4 and r['horizontal']<=4 for r in expanded),
    }
    runtime={}
    for port,path in [(8001,'/health'),(5174,'/api/v1/overview/kpis'),(8000,'/health'),(5173,'/')]:
        with urlopen(f'http://127.0.0.1:{port}{path}',timeout=10) as response:
            runtime[str(port)]={'http':response.status}
            if port==8001:
                health=json.load(response)['data']
                runtime[str(port)]['database']=health['database']
                checks['repo_database_ready']=health['ready'] and health['database']=='bibica_repo'
    reports=['reports/phase2_tests.json','reports/linked_frontend.json','reports/linked_browser.json','reports/linked_final_target_browser.json',
             'reports/linked_reconciliation.json','reports/linked_layouts.json','reports/linked_board_layouts.json',
             'reports/linked_detail_layouts.json','reports/scroll_detail_layouts.json']
    report={'status':'PASS' if all(checks.values()) else 'FAIL','executed_at':datetime.now(timezone.utc).isoformat(),
            'checks':checks,'counts':{'backend':120,'frontend':41,'browser':22,'cohorts':10,'main_views':20,'overview_sizes':3,'detail_views':22,'expanded_views':45},
            'kpis':reconciliation['kpis'],'runtime':runtime,'source_hashes':reconciliation['source_hashes'],
            'evidence_hashes':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in reports},
            'limits':['Local only; no commit/push.','No ETL/schema/Golden changes.','Brand/traffic not present in repo read model.',
                      'Descriptive cohort insights only; no growth, profit, causality or calibrated failure probability.',
                      'Long content/mobile can scroll locally; no blanket guarantee for all possible inputs.',
                      'Existing large frontend bundle warning. No cloud/Docker/CI/production load/PDF/ZIP verification.']}
    (ROOT/'reports/linked_acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps({'status':report['status'],'checks':checks}))
    if report['status']!='PASS':raise SystemExit(1)


if __name__=='__main__':main()
