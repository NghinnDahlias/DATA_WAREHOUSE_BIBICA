"""Exercise the running loopback API over HTTP, including DSS for all three stores."""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import httpx
from DW.etl.categorization import categorize_product


def main(port):
    checks = {}
    requests = []
    summaries = []
    with httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=30) as client:
        def call(method, path, **kwargs):
            started = time.perf_counter()
            response = client.request(method, path, **kwargs)
            requests.append({'method':method,'path':path,'status':response.status_code,
                             'seconds':round(time.perf_counter()-started,4)})
            if response.status_code != 200:
                raise RuntimeError('Live API request failed')
            return response

        health = call('GET','/health').json()['data']
        checks['repository_database_ready'] = health['ready'] and health['database']=='bibica_repo'
        call('GET','/docs')
        call('GET','/openapi.json')
        meta = call('GET','/api/v1/meta').json()['data']
        full = call('GET','/api/v1/overview/kpis').json()['data']
        call('GET','/api/v1/kpi-contract')
        call('GET','/api/v1/quality')
        call('GET','/api/v1/operations/delivery')
        for dimension in ['source','store','status','month','category','province','warehouse','warehouse_region','product']:
            call('GET','/api/v1/analytics/'+dimension,params={'limit':2})
        cutoff = max(r['last_order_date'] for r in meta['coverage'])
        for store in meta['stores']:
            code = store['storefront_code']
            key = store['storefront_key']
            wh = [w['warehouse_key'] for w in meta['warehouses'] if w['storefront_key']==key]
            products = call('GET','/api/v1/products',params={'store':code,'category':'Bánh','limit':200}).json()['data']
            product = next(p for p in products if categorize_product(p['product_name']).canonical_category=='Bánh')
            scenario = {'max_delivery_days':14,'stocks':[
                {'warehouse_key':w,'product_key':product['product_key'],'units':100,'remaining_shelf_days':30} for w in wh]}
            body = {'store':code,'as_of':cutoff,'orders':[
                {'order_ref':'LIVE'+str(i),'province':p,'items':[{'product_key':product['product_key'],'quantity':2}]}
                for i,p in enumerate(['Hà Nội','Hồ Chí Minh'])],'scenario':scenario}
            result = call('POST','/api/v1/dss/allocate',json=body).json()['data']
            checks[code+'_allocation'] = result['summary']['assigned_orders']==2
            checks[code+'_scope'] = all(a['warehouse_key'] in wh for a in result['assignments'])
            risk = call('GET','/api/v1/dss/risk',params={'store':code,'as_of':cutoff,'limit':2}).json()['data']
            checks[code+'_observed_risk'] = bool(risk) and all(not r['calibrated_probability'] for r in risk)
            shelf = call('POST','/api/v1/dss/shelf-life',json={
                'store':code,'as_of':cutoff,'product_key':product['product_key'],'warehouse_key':wh[0],
                'province':'Hà Nội','remaining_shelf_days':30}).json()['data']
            checks[code+'_shelf_evidence'] = shelf['status']=='SCENARIO' and shelf['historical_threshold_exceedance']['samples']>0
            summaries.append({'store':code,'allocation':result['summary'],
                              'risk_components_available':risk[0]['available_weight_fraction']})
        demo = json.loads((root/'reports/phase2_demo.json').read_text(encoding='utf8'))
        result = call('POST','/api/v1/dss/what-if',json=demo['inputs']).json()['data']
        checks['live_what_if_changes_assignment'] = result['alternatives'][0]['comparison']['changed_orders']>0
        body = demo['inputs']
        sensitivity = {k:v for k,v in body.items() if k!='alternative'}
        sensitivity['alternatives'] = [body['alternative']]
        call('POST','/api/v1/dss/sensitivity',json=sensitivity)
        after = call('GET','/api/v1/overview/kpis').json()['data']
        checks['api_readonly_kpis_unchanged'] = after==full
        checks['all_http_200'] = all(r['status']==200 for r in requests)
    result = {'status':'PASS' if all(checks.values()) else 'FAIL',
              'executed_at':datetime.now(timezone.utc).isoformat(),'port':port,
              'checks':checks,'requests':requests,'store_summaries':summaries}
    (root/'reports/phase2_live_http.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],'checks':checks,'http_requests':len(requests),'store_summaries':summaries},ensure_ascii=False))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8001)
    raise SystemExit(main(parser.parse_args().port))
