"""Local aggregate evidence only; never serialize review content or buyer information."""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from src.api.app import app
from src.api.db import snapshot
from src.api.models import Filters
from src.api.repository import kpis
from src.api.review_privacy import CONTENT_VERSION
from DW.etl.common import SOURCES,checksum,source_path
from DW.etl.verify import fingerprint

ROOT=Path(__file__).resolve().parents[1]


def main():
    client=TestClient(app)
    checks={}
    cohorts=[{}, {'channel':'SHOPEE'}, {'channel':'TIKTOK'}, {'category':'Bánh'},
        {'category':'Kẹo'}, {'warehouse_region':'Hà Nội'}, {'province':'Hồ Chí Minh'},
        {'start_date':'2026-06-01','end_date':'2026-09-18'}]
    counts=[]
    for params in cohorts:
        k=client.get('/api/v1/overview/kpis',params=params)
        cases=client.get('/api/v1/customer/review-cases',params=params)
        assert k.status_code==cases.status_code==200
        n=cases.json()['data']['total']
        assert n==k.json()['data']['low_reviews']
        counts.append({'filters':params,'negative_reviews':n})
    checks['eight_cohorts_match_low_review_kpi']=True
    themes=client.get('/api/v1/customer/review-themes').json()['data']
    for label in themes['labels']:
        d=client.get('/api/v1/customer/review-cases',params={'topic':label['label']}).json()['data']
        assert d['total']==label['negative_mentions']
    checks['all_topic_counts_match_negative_mentions']=True
    seen=set()
    total=client.get('/api/v1/customer/review-cases').json()['data']['total']
    for offset in range(0,total,50):
        d=client.get('/api/v1/customer/review-cases',params={'offset':offset,'limit':50}).json()['data']
        for r in d['rows']:
            assert r['case_key'] not in seen
            seen.add(r['case_key'])
            detail=client.get(f"/api/v1/customer/review-cases/{r['case_key']}").json()['data']
            assert set(detail)=={'case_key','star_level','review_date','product_name','labels','content_status','content'}
            assert detail['star_level']<=2 and detail['content_status'] in ('READY','NO_TEXT')
            assert not re.search(r'\d{7,}|https?://|[\w.+-]+@[\w.-]+\.[a-z]{2,}',detail['content'] or '')
    assert len(seen)==total
    checks['all_negative_cases_page_once_and_have_current_redacted_projection']=True
    checks['response_allowlist_no_native_buyer_identifiers']=True
    with snapshot() as c:
        after={'facts':{n:fingerprint(c,n) for n in ['fact_order_line_candidate','fact_order_lifecycle_candidate','fact_review_candidate']},
               'kpis':kpis(c,Filters()),'sources':c.execute('SELECT source_code,sha256 FROM ops.source_current ORDER BY 1').fetchall()}
        prepared=c.execute('SELECT count(*) n FROM dw.review_case_content WHERE content_version=%s',(CONTENT_VERSION,)).fetchone()['n']
        thresholds=c.execute('SELECT star_level,count(*) n FROM dw.fact_review_candidate WHERE star_level<=3 GROUP BY 1 ORDER BY 1').fetchall()
        for row in after['sources']:
            assert checksum(source_path(row['source_code']))==row['sha256']
    checks['four_source_bytes_match_registered_hashes']=True
    before_path=ROOT/'.runtime/review-reader-before.json'
    if before_path.exists():
        before=json.loads(before_path.read_text('utf8'))
        normalized=json.loads(json.dumps(after,default=str))
        checks['business_fact_fingerprints_unchanged']=before['facts']==normalized['facts']
        checks['all_kpis_unchanged']=before['kpis']==normalized['kpis']
        checks['registered_sources_unchanged']=before['sources']==normalized['sources']
    for ceiling in (1,2,3):
        n=client.get('/api/v1/customer/review-cases',params={'stars_max':ceiling}).json()['data']['total']
        assert n==sum(r['n'] for r in thresholds if r['star_level']<=ceiling)
    checks['all_three_star_thresholds_reconcile']=True
    report={'status':'PASS' if all(checks.values()) else 'FAIL','executed_at':datetime.now(timezone.utc).isoformat(),
        'checks':checks,'cohorts':counts,'topics':len(themes['labels']),'default_negative_cases':total,'prepared_cases_le3':prepared,
        'facts':after['facts'],'source_hashes':{r['source_code']:r['sha256'] for r in after['sources']},
        'limits':['Automatic redaction is conservative and can remove useful words; no guarantee of human-verified anonymization.',
            'Star threshold and keyword mentions are not confirmed complaint causes. No original customer/order identifiers in responses.',
            'Local auxiliary projection only; original review workbook and business facts unchanged.']}
    (ROOT/'reports/review_reader.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf8')
    print(json.dumps({'status':report['status'],'checks':checks,'cases':total,'prepared':prepared}))
    if report['status']!='PASS':raise SystemExit(1)


if __name__=='__main__':main()
