import sys,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.api.db import snapshot
from src.api.models import Filters
from src.api.repository import kpis
from scripts.assess_integrity import independent_kpis,equal_measure

params={'source':'shopee_bibica','category':'Bánh'}
with snapshot() as c:
    c.execute('SET LOCAL enable_nestloop=off')
    expected=independent_kpis(c,params)
def probe(task):
    mode,index=task
    with snapshot() as c:
        c.execute('SET LOCAL max_parallel_workers_per_gather='+str(mode))
        actual=kpis(c,Filters(**params))
    mismatch={k:{'expected':str(v),'actual':str(actual.get(k))} for k,v in expected.items() if not equal_measure(v,actual.get(k))}
    return {'mode':mode,'probe':index,'mismatch':mismatch}
results=[]
for mode in [2,0]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        results.extend(executor.map(probe,[(mode,index) for index in range(24)]))
serial=[r for r in results if r['mode']==0]
parallel=[r for r in results if r['mode']==2]
report={'status':'SERIAL_MITIGATION_VERIFIED' if all(not r['mismatch'] for r in serial) else 'FAIL',
        'executed_at':datetime.now(timezone.utc).isoformat(),'queries_per_mode':24,'workers':4,
        'serial_mismatches':sum(bool(r['mismatch']) for r in serial),
        'parallel_mismatches':sum(bool(r['mismatch']) for r in parallel),'results':results,
        'scope':'Session-only read-only experiments. Underlying PostgreSQL parallel plan cause is not yet established. API runs with per-gather parallel workers disabled.'}
Path('reports/phase2_assessment/sql_parallel_diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False))
assert report['status']!='FAIL'
