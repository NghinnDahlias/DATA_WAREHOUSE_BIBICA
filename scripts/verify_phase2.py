"""Full-data API/DSS verification. Emits aggregates and hashes, never buyer/source rows."""
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from fastapi.testclient import TestClient
from DW.etl.common import SOURCES, checksum
from src.api.app import app
from src.api.db import snapshot
from src.dss.evidence import breakfast_candidate


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf8')


def business_fingerprints(connection):
    queries = {
        'orders': '''SELECT a.source_code source,o.native_order_id id,a.created_at created,
          dp.calendar_date+tp.native_time paid,a.delivered_at delivered,a.canonical_status status,
          a.order_payable::numeric(20,2) amount,a.observed_refund::numeric(20,2) refund,a.order_row_count line_count
          FROM analytics.v_orders a JOIN dw.dim_order_identity o USING(order_key)
          JOIN dw.fact_order_lifecycle_candidate f USING(order_key)
          LEFT JOIN dw.dim_date dp ON dp.date_key=f.paid_date_key LEFT JOIN dw.dim_time tp ON tp.time_key=f.paid_time_key
          ORDER BY source,id''',
        'items': '''SELECT f.source_code source,f.physical_row_number locator,f.quantity::numeric(24,4) qty,
          f.gross_item_amount_source::numeric(20,2) gross,f.net_item_amount_source::numeric(20,2) payable,
          f.seller_discount_source::numeric(20,2) seller,f.platform_discount_source::numeric(20,2) platform,
          f.returned_quantity::numeric(24,4) returned,c.canonical_category category,w.warehouse_region,p.normalized_province_name province
          FROM dw.fact_order_line_candidate f LEFT JOIN dw.dim_category c USING(category_key)
          JOIN dw.dim_warehouse w USING(warehouse_key) JOIN dw.dim_province p USING(province_key) ORDER BY source,locator''',
        'reviews': '''SELECT r.physical_row_number locator,o.native_order_id id,p.product_nk sku,d.calendar_date date,
          r.star_level stars,r.match_confidence FROM dw.fact_review_candidate r JOIN dw.dim_order_identity o USING(order_key)
          LEFT JOIN dw.dim_source_product_sku p USING(source_product_sku_key) JOIN dw.dim_date d ON d.date_key=r.review_date_key ORDER BY locator''',
    }
    results = {}
    for grain, query in queries.items():
        digest = hashlib.sha256()
        count = 0
        with connection.cursor(name='phase2_'+grain) as cursor:
            cursor.execute(query)
            for row in cursor:
                digest.update(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode('utf8')+b'\n')
                count += 1
        results[grain] = {'rows': count, 'sha256': digest.hexdigest()}
    return results


def evaluate_timing(connection, split='2026-09-01'):
    # Training outcomes must be recorded by split. No future review or status is a predictor.
    return connection.execute('''WITH train AS (
      SELECT storefront_code,warehouse_key,route_province,GROUPING(route_province) rolled,
        count(*) n,percentile_cont(.5) WITHIN GROUP(ORDER BY lead_days) median,
        percentile_cont(.9) WITHIN GROUP(ORDER BY lead_days) p90
      FROM dss.v_route_orders WHERE order_date<=%(split)s::date AND delivered_at::date<=%(split)s::date AND lead_days IS NOT NULL
      GROUP BY GROUPING SETS((storefront_code,warehouse_key,route_province),(storefront_code,warehouse_key))
    ), held_out AS (
      SELECT r.*,CASE WHEN exact.n>=20 THEN exact.median ELSE base.median END predicted_median,
        CASE WHEN exact.n>=20 THEN exact.p90 ELSE base.p90 END predicted_p90,
        base.median baseline_median,exact.n exact_samples,base.n baseline_samples
      FROM dss.v_route_orders r LEFT JOIN train exact ON exact.rolled=0 AND exact.warehouse_key=r.warehouse_key
        AND exact.route_province=r.route_province AND exact.storefront_code=r.storefront_code
      LEFT JOIN train base ON base.rolled=1 AND base.warehouse_key=r.warehouse_key AND base.storefront_code=r.storefront_code
      WHERE r.order_date>%(split)s::date AND r.lead_days IS NOT NULL
    ) SELECT storefront_code,count(*) held_out_observations,
      count(*) FILTER(WHERE baseline_samples>=20) scored_observations,
      count(*) FILTER(WHERE exact_samples>=20) exact_route_supported_observations,
      avg(abs(lead_days-predicted_median)) FILTER(WHERE baseline_samples>=20) median_mae_days,
      avg(abs(lead_days-baseline_median)) FILTER(WHERE baseline_samples>=20) warehouse_baseline_mae_days,
      avg((lead_days<=predicted_p90)::integer) FILTER(WHERE baseline_samples>=20) historical_p90_holdout_coverage,
      min(order_date) first_test_order,max(order_date) last_test_order
      FROM held_out GROUP BY 1 ORDER BY 1''', {'split': split}).fetchall()


def main():
    dump(root/'reports/phase2_verification.json',{'status':'RUNNING','started_at':datetime.now(timezone.utc).isoformat()})
    checks, timings = {}, {}
    client = TestClient(app)

    def get(path, **kwargs):
        started = time.perf_counter()
        response = client.get(path, **kwargs)
        timings[path] = round(time.perf_counter()-started, 4)
        assert response.status_code == 200, (path, response.status_code, response.json().get('detail'))
        return response.json()['data']

    def post(path, body):
        started = time.perf_counter()
        response = client.post(path, json=body)
        timings[path] = round(time.perf_counter()-started, 4)
        assert response.status_code == 200, (path, response.status_code, response.json().get('detail'))
        return response.json()['data']

    meta = get('/api/v1/meta')
    kpis = get('/api/v1/overview/kpis')
    delivery = get('/api/v1/operations/delivery')
    with snapshot() as c:
        fingerprints = business_fingerprints(c)
        previous = json.loads((root/'reports/reference_reconciliation.json').read_text(encoding='utf8'))
        checks.update({grain+'_business_fingerprint_preserved': value == previous['fingerprints'][grain]['repo']
                       for grain,value in fingerprints.items()})
        source_rows = c.execute('SELECT source_code,sha256,row_count FROM ops.source_current ORDER BY 1').fetchall()
        checks['four_source_bytes_unchanged'] = all(checksum(root/'Data/Data_Source_Raw'/SOURCES[r['source_code']][0]) == r['sha256'] for r in source_rows) and len(source_rows)==4
        schema = c.execute("SELECT count(*) FILTER(WHERE contype='f') foreign_keys FROM pg_constraint WHERE connamespace='dw'::regnamespace AND conrelid <> 'dw.review_theme_feature'::regclass").fetchone()
        schema['tables'] = c.execute("SELECT count(*) n FROM information_schema.tables WHERE table_schema='dw' AND table_type='BASE TABLE' AND table_name <> 'review_theme_feature'").fetchone()['n']
        checks['galaxy_keys_preserved'] = schema == {'foreign_keys':56,'tables':15}
        independent = c.execute('''SELECT count(*) orders,sum(f.order_amount_source) FILTER(WHERE s.reviewed_status='COMPLETED') completed_payable
           FROM dw.fact_order_lifecycle_candidate f JOIN dw.dim_order_status s USING(order_status_key)''').fetchone()
        checks['api_order_money_independent_sql'] = kpis['orders']==independent['orders'] and Decimal(kpis['completed_payable'])==independent['completed_payable']
        checks['shopee_shipped_restored'] = all(r['shipped_to_recorded_samples']>0 for r in delivery)
        checks['mixed_source_delivery_disabled'] = kpis['mean_created_to_recorded_delivery_days'] is None
        checks['canonical_four_categories'] = {r['canonical_category'] for r in meta['categories']} == {'Bánh','Kẹo','Ngũ cốc','Quà tặng'}
        linkage = c.execute('SELECT product_linkage_status,count(*) reviews FROM dw.fact_review_candidate GROUP BY 1 ORDER BY 1').fetchall()
        training = evaluate_timing(c)
        # One catalog SKU observed at both warehouses, identified only for the scenario demo.
        choices = c.execute('''SELECT i.product_key,max(p.product_name) product_name,count(DISTINCT i.warehouse_key) warehouses,
           sum(i.quantity) units FROM analytics.v_items i JOIN analytics.v_orders o USING(order_key)
           JOIN dw.dim_source_product_sku p ON p.source_product_sku_key=i.product_key
           WHERE o.storefront_code='bibica_tiktok_shop' AND p.canonical_category='Bánh'
           GROUP BY i.product_key HAVING count(DISTINCT i.warehouse_key)=2 ORDER BY units DESC,i.product_key''').fetchall()
        product = next(p for p in choices if breakfast_candidate(p['product_name']))
    warehouses = [w['warehouse_key'] for w in meta['warehouses'] if w['storefront_key']==next(s['storefront_key'] for s in meta['stores'] if s['storefront_code']=='bibica_tiktok_shop')]
    cutoff = max(r['last_order_date'] for r in meta['coverage'])
    body = {'store':'bibica_tiktok_shop','as_of':cutoff,'orders':[
        {'order_ref':'DEMO'+str(i),'province':province,'items':[{'product_key':product['product_key'],'quantity':2}]}
        for i,province in enumerate(['Hà Nội','Hồ Chí Minh','Đồng Nai','Hải Phòng'])]}
    scenario = {'label':'Tồn kho và HSD giả định để thử thuật toán','stocks':[
        {'warehouse_key':key,'product_key':product['product_key'],'units':100,'remaining_shelf_days':30,'stock_scope':'ECOMMERCE'} for key in warehouses]}
    allocation = post('/api/v1/dss/allocate', {**body,'scenario':scenario})
    warehouse_regions={w['warehouse_key']:w['warehouse_region'] for w in meta['warehouses']}
    checks['default_breakfast_hanoi_policy'] = allocation['summary']['assigned_orders']==len(body['orders']) and all(a['warehouse_region']=='Hà Nội' for a in allocation['assignments'])
    blocked_key = max(allocation['summary']['warehouse_orders'],key=allocation['summary']['warehouse_orders'].get)
    exceptions=[{'warehouse_key':key,'product_key':product['product_key'],'reason':'APPROVED_ECOMMERCE_EXCEPTION',
                  'evidence_ref':'SCENARIO-HCM-EXCEPTION','ecommerce_stock_confirmed':True}
                for key in warehouses if warehouse_regions[key]=='Hồ Chí Minh']
    whatif_body = {**body,'baseline':scenario,'alternative':{**scenario,'label':'Khóa năng lực HN với ngoại lệ TMĐT HCM khai báo rõ',
        'capacity_orders':{str(blocked_key):0},'breakfast_exceptions':exceptions}}
    comparison = post('/api/v1/dss/what-if',whatif_body)
    checks['capacity_what_if_changes_real_decision'] = comparison['alternatives'][0]['comparison']['changed_orders']>0
    stressed = {**scenario,'label':'Trễ4ngày và chỉ còn5ngày HSD giả định',
               'extra_delay_days':{str(k):4 for k in warehouses},'stocks':[{**s,'remaining_shelf_days':5} for s in scenario['stocks']]}
    sensitivity = post('/api/v1/dss/sensitivity',{**body,'baseline':scenario,'alternatives':[stressed,{**scenario,'risk_weight':0},{**scenario,'risk_weight':1}]})
    checks['shelf_stress_reduces_assignments'] = sensitivity['alternatives'][0]['result']['summary']['assigned_orders']<allocation['summary']['assigned_orders']
    shelf_body = {'store':'bibica_tiktok_shop','product_key':product['product_key'],'warehouse_key':warehouses[0],
                  'province':'Hà Nội','as_of':cutoff,'remaining_shelf_days':30}
    shelf_base = post('/api/v1/dss/shelf-life',shelf_body)
    shelf_stressed = post('/api/v1/dss/shelf-life',{**shelf_body,'remaining_shelf_days':1,'extra_delay_days':2})
    checks['shelf_empirical_exceedance_monotonic'] = shelf_stressed['historical_threshold_exceedance']['fraction']>=shelf_base['historical_threshold_exceedance']['fraction']
    risk = get('/api/v1/dss/risk',params={'store':'bibica_tiktok_shop','as_of':cutoff,'limit':200})
    checks['risk_real_rates_and_uncalibrated'] = bool(risk) and all(0<=r['risk_score']<=100 and not r['calibrated_probability'] for r in risk)
    # All three source cohorts are evaluated, including aliases/warehouse filters.
    checks['source_kpis_reconcile'] = sum(get('/api/v1/overview/kpis',params={'source':r['source_code']})['orders'] for r in meta['coverage'])==kpis['orders']
    checks['empty_and_injection_safe'] = get('/api/v1/overview/kpis',params={'province':"';DROP SCHEMA dw CASCADE;--"})['orders']==0
    privacy_fields = ['native_order_id','order_namespace','user_name','review_text','phone','tracking_number']
    encoded = json.dumps([kpis,meta,allocation,comparison,shelf_base,risk],ensure_ascii=False)
    checks['no_buyer_fields_in_responses'] = all('"'+field+'"' not in encoded for field in privacy_fields)
    checks['timing_holdout_three_sources_executed'] = len(training)==3 and all(r['scored_observations']>0 for r in training)
    api_schema = client.get('/openapi.json').json()
    dump(root/'docs/api/openapi.json',api_schema)
    dump(root/'reports/phase2_demo.json',{'inputs':whatif_body,'allocation':allocation,'what_if':comparison,
         'sensitivity':sensitivity,'shelf_base':shelf_base,'shelf_stressed':shelf_stressed,
         'note':'Demand, inventory, expiry and capacity are explicitly simulated. Historical risk/lead aggregates are real.'})
    result = {'status':'PASS' if all(checks.values()) else 'FAIL','executed_at':datetime.now(timezone.utc).isoformat(),
        'checks':checks,'kpis':kpis,'source_rows':source_rows,'schema':schema,'business_fingerprints':fingerprints,
        'delivery_by_source':delivery,'review_linkage':linkage,'timing_holdout':{'split':'2026-09-01','results':training,
          'limitations':'Timing-only retrospective diagnostic. Snapshot cancellation/review risk is not predictively calibrated. No counterfactual routing outcome is observed.'},
        'demo_summary':{'product_key':product['product_key'],'product_name':product['product_name'],
            'allocation':allocation['summary'],'capacity_what_if':comparison['alternatives'][0]['comparison'],
            'shelf_stress':sensitivity['alternatives'][0]['result']['summary']},
        'api_elapsed_seconds':timings,'browser_ui_test':'OUT_OF_SCOPE','docker_cloud_remote_ci':'NOT_EXECUTED'}
    dump(root/'reports/phase2_verification.json',result)
    print(json.dumps({'status':result['status'],'checks':checks,'demo_summary':result['demo_summary'],'api_elapsed_seconds':timings},ensure_ascii=False,default=str))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        dump(root/'reports/phase2_verification.json',{'status':'FAIL','executed_at':datetime.now(timezone.utc).isoformat(),'error_code':type(error).__name__})
        raise
