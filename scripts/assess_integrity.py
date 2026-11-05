"""Fresh read-only integrity/cohort/concurrency assessment, with aggregate-only reports."""
import concurrent.futures
import argparse
import hashlib
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx
import psycopg
from psycopg.rows import dict_row

from DW.etl.common import SOURCES, checksum
from src.api.db import database_dsn


def dump(name, value):
    folder = ROOT / 'reports/phase2_assessment'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf8')


def independent_kpis(connection, filters):
    """Use facts/dimensions directly, independently of API repository helpers and views."""
    if set(filters)-{'source','store','start_date','end_date','status','category','province','warehouse_key','warehouse_region','product_key'}:
        raise ValueError('Unknown oracle filter field')
    conditions = ['TRUE']
    line_conditions = ['TRUE']
    values = dict(filters)
    for field, expression in {
        'source': 'o.source_code=%(source)s', 'store': 'o.storefront_code=%(store)s',
        'start_date': 'o.order_date>=%(start_date)s', 'end_date': 'o.order_date<=%(end_date)s',
        'status': 'o.canonical_status=%(status)s',
    }.items():
        if field in filters:
            conditions.append(expression)
    for field, expression in {
        'category': 'i.canonical_category=%(category)s', 'province': 'i.customer_province=%(province)s',
        'warehouse_key': 'i.warehouse_key=%(warehouse_key)s',
        'warehouse_region': 'i.warehouse_region=%(warehouse_region)s',
        'product_key': 'i.product_key=%(product_key)s',
    }.items():
        if field in filters:
            line_conditions.append(expression)
    line_filter = ' AND '.join(line_conditions)
    if len(line_conditions) > 1:
        conditions.append('EXISTS(SELECT 1 FROM base_items i WHERE i.order_key=o.order_key AND '+line_filter+')')
    review_filter = 'TRUE'
    if 'end_date' in filters:
        review_filter += ' AND d.calendar_date<=%(end_date)s'
    if len(line_conditions) > 1:
        review_filter += ' AND EXISTS(SELECT 1 FROM selected_items i WHERE i.order_key=r.order_key AND i.product_key=r.source_product_sku_key)'
    query = '''WITH base_orders AS MATERIALIZED (
      SELECT f.order_key,f.order_amount_source,f.refund_amount_source,
        s.storefront_code,st.reviewed_status canonical_status,d.calendar_date order_date,
        CASE s.storefront_code WHEN 'bibica_tiktok_shop' THEN 'tiktok_bibica'
          WHEN 'bibica_official_store' THEN 'shopee_bibica' ELSE 'shopee_quasure' END source_code
      FROM dw.fact_order_lifecycle_candidate f JOIN dw.dim_storefront s USING(storefront_key)
      JOIN dw.dim_order_status st USING(order_status_key) JOIN dw.dim_date d ON d.date_key=f.created_date_key
    ), base_items AS MATERIALIZED (
      SELECT f.order_key,f.source_product_sku_key product_key,f.category_key,f.warehouse_key,
        f.quantity,f.gross_item_amount_source,f.net_item_amount_source,f.seller_discount_source,c.canonical_category,
        w.warehouse_region,p.normalized_province_name customer_province
      FROM dw.fact_order_line_candidate f LEFT JOIN dw.dim_category c USING(category_key)
      LEFT JOIN dw.dim_warehouse w USING(warehouse_key) LEFT JOIN dw.dim_province p USING(province_key)
    ), selected_orders AS MATERIALIZED (SELECT o.* FROM base_orders o WHERE '''+' AND '.join(conditions)+'''
    ), selected_items AS MATERIALIZED (SELECT i.*,o.canonical_status FROM base_items i JOIN selected_orders o USING(order_key)
      WHERE '''+line_filter+'''
    ), selected_reviews AS (
      SELECT r.* FROM dw.fact_review_candidate r JOIN selected_orders o USING(order_key)
      JOIN dw.dim_date d ON d.date_key=r.review_date_key WHERE '''+review_filter+'''
    ) SELECT o.*,i.*,r.*,
      o.completed_payable/nullif(o.completed_orders_with_payable,0) completed_aov,
      o.canceled_orders::numeric/nullif(o.orders,0) cancellation_rate,
      o.refund_positive_orders::numeric/nullif(o.refund_observed_orders,0) refund_order_rate,
      i.paired_discount/nullif(i.paired_gross,0) seller_discount_rate,
      r.low_reviews::numeric/nullif(r.reviews,0) low_review_rate,
      r.reviewed_tiktok_orders::numeric/nullif(o.tiktok_orders,0) review_order_coverage
      FROM (SELECT count(*) orders,count(*) FILTER(WHERE canonical_status='COMPLETED') completed_orders,
        count(*) FILTER(WHERE canonical_status='CANCELED') canceled_orders,
        sum(order_amount_source) booked_payable,count(order_amount_source) payable_observed_orders,
        sum(order_amount_source) FILTER(WHERE canonical_status='COMPLETED') completed_payable,
        count(order_amount_source) FILTER(WHERE canonical_status='COMPLETED') completed_orders_with_payable,
        sum(refund_amount_source) observed_refund,count(refund_amount_source) refund_observed_orders,
        count(*) FILTER(WHERE refund_amount_source>0) refund_positive_orders,
        count(*) FILTER(WHERE source_code='tiktok_bibica') tiktok_orders FROM selected_orders) o
      CROSS JOIN (SELECT count(*) accepted_lines,sum(quantity) units,sum(gross_item_amount_source) gross_item_value,
        sum(gross_item_amount_source) FILTER(WHERE canonical_status='COMPLETED') completed_gross_item_value,
        sum(quantity) FILTER(WHERE canonical_status='COMPLETED') completed_units,
        sum(net_item_amount_source) observed_item_payable,sum(seller_discount_source) seller_discount,
        sum(seller_discount_source) FILTER(WHERE gross_item_amount_source IS NOT NULL) paired_discount,
        sum(gross_item_amount_source) FILTER(WHERE seller_discount_source IS NOT NULL) paired_gross,
        count(*) FILTER(WHERE category_key IS NULL) unmapped_lines FROM selected_items) i
      CROSS JOIN (SELECT count(*) reviews,avg(star_level) review_stars_mean,
        count(*) FILTER(WHERE star_level<=2) low_reviews,count(DISTINCT order_key) reviewed_tiktok_orders
        FROM selected_reviews) r'''
    return connection.execute(query, values).fetchone()


def equal_measure(expected, actual):
    if expected is None:
        return actual is None
    return actual is not None and abs(Decimal(str(actual))-Decimal(str(expected))) <= Decimal('0.000000000001')


def verify_live_capabilities():
    """Short final regression against the server restarted with the refined DSS code."""
    checks={}
    with httpx.Client(base_url='http://127.0.0.1:8001',timeout=45) as client:
        meta=client.get('/api/v1/meta')
        capabilities=meta.json().get('data',{}).get('capabilities',{})
        checks['meta_http200']=meta.status_code==200
        expected=['customer_identity_analysis','complaint_lifecycle','replacement_promised','replacement_sent',
                  'replacement_received','replacement_resolved','warehouse_transfer_cause']
        checks['missing_data_capabilities_explicit_unavailable']=all(capabilities.get(k,{}).get('status')=='UNAVAILABLE' for k in expected)
        checks['replacement_missing_is_null_not_zero']=all(capabilities.get('replacement_'+stage,{}).get('value','MISSING') is None
            for stage in ['promised','sent','received','resolved'])
        response=client.get('/api/v1/overview/kpis')
        with psycopg.connect(database_dsn(),row_factory=dict_row,connect_timeout=5) as c:
            c.execute('SET TRANSACTION READ ONLY')
            expected_kpis=independent_kpis(c,{})
        checks['new_server_numeric_kpis_match_independent_sql']=response.status_code==200 and all(equal_measure(v,response.json().get('data',{}).get(k)) for k,v in expected_kpis.items())
        checks['customer_dimension_rejected']=client.get('/api/v1/analytics/customer').status_code==422
        invalid=client.get('/api/v1/overview/kpis',params={'customer':'SYNTHETIC_CUSTOMER_SENTINEL'})
        checks['unknown_customer_input_rejected_without_echo']=invalid.status_code==422 and 'SYNTHETIC_CUSTOMER_SENTINEL' not in invalid.text
        forbidden={'native_order_id','order_namespace','user_name','phone','tracking_number','review_text','buyer_id','customer_id'}
        def keys(value):
            if isinstance(value,dict):
                return set(value).union(*(keys(v) for v in value.values()))
            if isinstance(value,list):
                return set().union(*(keys(v) for v in value))
            return set()
        checks['no_buyer_fields_in_meta_kpis']=not(forbidden & keys([meta.json(),response.json()]))
    report={'status':'PASS' if all(checks.values()) else 'FAIL','executed_at':datetime.now(timezone.utc).isoformat(),
            'checks':checks,'numeric_measures_compared':len(expected_kpis),'capabilities':capabilities}
    dump('integrity_live_v2.json',report)
    print(json.dumps(report,ensure_ascii=False))
    return 0 if all(checks.values()) else 1


def main():
    checks, details = {}, {}
    dump('integrity.json', {'status':'RUNNING','started_at':datetime.now(timezone.utc).isoformat()})
    with psycopg.connect(database_dsn(), row_factory=dict_row, connect_timeout=5) as connection:
        connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        connection.execute("SET LOCAL statement_timeout='45s'")
        # Independent reference CTEs have no column statistics. Keep their joins set-based
        # rather than allowing repeated scans of materialized relations for sparse probes.
        # This affects this read-only oracle session only, never the API connection/planner.
        connection.execute('SET LOCAL enable_nestloop=off')
        checks['read_only_snapshot'] = connection.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        details['raw_sources'] = connection.execute('SELECT source_code,row_count,sha256 FROM ops.source_current ORDER BY 1').fetchall()
        checks['native_source_sha_unchanged'] = all(checksum(ROOT/'Data/Data_Source_Raw'/SOURCES[r['source_code']][0])==r['sha256'] for r in details['raw_sources'])
        validation = {
            'accepted_lines_match_staging': '''SELECT count(*) violations FROM dw.fact_order_line_candidate f
              FULL JOIN (SELECT l.* FROM staging.order_line l WHERE NOT EXISTS(SELECT 1 FROM ops.quarantine q
                WHERE q.source_code=l.source_code AND q.row_no=l.row_no)) l
              ON (f.source_code,f.physical_row_number)=(l.source_code,l.row_no)
              WHERE f.order_line_key IS NULL OR l.row_no IS NULL OR f.quantity IS DISTINCT FROM l.quantity
              OR f.gross_item_amount_source IS DISTINCT FROM l.gross OR f.net_item_amount_source IS DISTINCT FROM l.item_after
              OR f.seller_discount_source IS DISTINCT FROM l.seller_discount''',
            'accepted_reviews_match_staging': '''SELECT count(*) violations FROM dw.fact_review_candidate f
              FULL JOIN (SELECT r.* FROM staging.review r WHERE NOT EXISTS(SELECT 1 FROM ops.quarantine q
                WHERE q.source_code=r.source_code AND q.row_no=r.row_no)) r
              ON (f.source_code,f.physical_row_number)=(r.source_code,r.row_no)
              WHERE f.review_key IS NULL OR r.row_no IS NULL OR f.star_level IS DISTINCT FROM r.stars''',
            'historical_category_matches_source_line': '''SELECT count(*) violations FROM dw.fact_order_line_candidate f
              JOIN staging.order_line l ON (l.source_code,l.row_no)=(f.source_code,f.physical_row_number)
              LEFT JOIN dw.dim_category c ON c.category_key=f.category_key WHERE c.canonical_category IS DISTINCT FROM l.canonical_category''',
            'scoped_warehouse_matches_source_line': '''SELECT count(*) violations FROM dw.fact_order_line_candidate f
              JOIN staging.order_line l ON (l.source_code,l.row_no)=(f.source_code,f.physical_row_number)
              JOIN dw.dim_warehouse w USING(warehouse_key) WHERE w.storefront_key<>f.storefront_key
              OR w.warehouse_region IS DISTINCT FROM l.warehouse_region''',
            'customer_province_matches_source_line': '''SELECT count(*) violations FROM dw.fact_order_line_candidate f
              JOIN staging.order_line l ON (l.source_code,l.row_no)=(f.source_code,f.physical_row_number)
              JOIN dw.dim_province p USING(province_key) WHERE p.normalized_province_name IS DISTINCT FROM l.customer_province''',
            'no_order_money_on_line': 'SELECT count(*) violations FROM dw.fact_order_line_candidate WHERE order_amount_source IS NOT NULL OR shipping_buyer_charge_source IS NOT NULL',
            'no_orphan_review_orders': '''SELECT count(*) violations FROM dw.fact_review_candidate r LEFT JOIN dw.fact_order_lifecycle_candidate f USING(order_key) WHERE f.order_key IS NULL''',
            'review_linked_product_belongs_same_order': '''SELECT count(*) violations FROM dw.fact_review_candidate r WHERE source_product_sku_key IS NOT NULL AND NOT EXISTS(
              SELECT 1 FROM dw.fact_order_line_candidate l WHERE l.order_key=r.order_key AND l.source_product_sku_key=r.source_product_sku_key)''',
            'rating_lexical_ids_match_exact_staging': '''SELECT count(*) violations FROM dw.fact_review_candidate f
              JOIN staging.review r ON(r.source_code,r.row_no)=(f.source_code,f.physical_row_number)
              JOIN dw.dim_order_identity o USING(order_key) WHERE o.native_order_id IS DISTINCT FROM r.order_id
                OR f.source_product_id IS DISTINCT FROM r.payload->>'product_id'
                OR o.native_order_id !~ '^[0-9]{18}$' OR f.source_product_id !~ '^[0-9]{19}$' ''',
            'schema_foreign_keys_validated': "SELECT count(*) violations FROM pg_constraint WHERE connamespace='dw'::regnamespace AND contype='f' AND NOT convalidated",
        }
        for key, query in validation.items():
            number=connection.execute(query).fetchone()['violations']
            checks[key]=number==0
            details[key]={'violations':number}
        details['source_order_reconciliation']=connection.execute('''WITH accepted AS (
          SELECT l.* FROM staging.order_line l WHERE NOT EXISTS(SELECT 1 FROM ops.quarantine q
            WHERE(q.source_code,q.row_no)=(l.source_code,l.row_no))
        ), g AS (SELECT source_code,order_id,count(*) lines,CASE WHEN count(DISTINCT order_amount)=1 THEN min(order_amount) END amount,
          CASE WHEN count(DISTINCT refund)=1 THEN min(refund) END refund FROM accepted GROUP BY 1,2)
        SELECT g.source_code,count(*) orders,sum(g.lines) accepted_lines,
          count(*) FILTER(WHERE f.order_key IS NULL OR f.order_row_count<>g.lines OR f.order_amount_source IS DISTINCT FROM g.amount
            OR f.refund_amount_source IS DISTINCT FROM g.refund) violations
        FROM g JOIN dw.dim_storefront s ON s.storefront_code=CASE g.source_code WHEN 'tiktok_bibica' THEN 'bibica_tiktok_shop'
          WHEN 'shopee_bibica' THEN 'bibica_official_store' ELSE 'quasure_specialized_store' END
        LEFT JOIN dw.dim_order_identity o ON o.storefront_key=s.storefront_key AND o.native_order_id=g.order_id
        LEFT JOIN dw.fact_order_lifecycle_candidate f ON f.order_key=o.order_key GROUP BY 1 ORDER BY 1''').fetchall()
        checks['all_order_amounts_and_counts_from_source'] = all(r['violations']==0 for r in details['source_order_reconciliation'])
        details['order_status_timestamp_reconciliation']=connection.execute('''WITH groups AS (
          SELECT l.source_code,l.order_id,min(l.created) created,min(l.shipped) shipped,max(l.delivered) delivered,
            CASE WHEN count(DISTINCT status_raw)=1 THEN min(canonical_status) ELSE 'UNKNOWN' END status
          FROM staging.order_line l WHERE NOT EXISTS(SELECT 1 FROM ops.quarantine q WHERE(q.source_code,q.row_no)=(l.source_code,l.row_no)) GROUP BY 1,2)
          SELECT count(*) orders,count(*) FILTER(WHERE g.created IS DISTINCT FROM a.created_at OR g.shipped IS DISTINCT FROM a.shipped_at
            OR g.delivered IS DISTINCT FROM a.delivered_at OR g.status IS DISTINCT FROM a.canonical_status) violations
          FROM groups g JOIN dw.dim_storefront s ON s.storefront_code=CASE g.source_code WHEN 'tiktok_bibica' THEN 'bibica_tiktok_shop'
            WHEN 'shopee_bibica' THEN 'bibica_official_store' ELSE 'quasure_specialized_store' END
          JOIN dw.dim_order_identity o ON o.storefront_key=s.storefront_key AND o.native_order_id=g.order_id
          JOIN analytics.v_orders a ON a.order_key=o.order_key''').fetchone()
        checks['all_order_status_and_timestamps_from_source']=details['order_status_timestamp_reconciliation']['violations']==0
        details['money_missing_zero_conflicts']=connection.execute('''SELECT s.storefront_code,count(*) orders,
          count(*) FILTER(WHERE f.order_amount_source IS NULL) missing_payable,
          count(*) FILTER(WHERE f.order_amount_source=0) zero_payable,
          count(*) FILTER(WHERE f.refund_amount_source IS NULL) missing_refund,
          count(*) FILTER(WHERE f.refund_amount_source=0) zero_refund,
          count(*) FILTER(WHERE f.refund_amount_source>0) positive_refund,
          count(*) FILTER(WHERE f.reconciliation_status='CONFLICTING') reconciliation_conflicts
          FROM dw.fact_order_lifecycle_candidate f JOIN dw.dim_storefront s USING(storefront_key) GROUP BY 1 ORDER BY 1''').fetchall()
        details['unknown_geography']=connection.execute('''SELECT f.source_code,count(*) accepted_lines,
          count(*) FILTER(WHERE p.normalized_province_name='Unknown') unknown_customer_province,
          count(*) FILTER(WHERE w.warehouse_region='Unknown') unknown_warehouse_region
          FROM dw.fact_order_line_candidate f JOIN dw.dim_province p USING(province_key)
          JOIN dw.dim_warehouse w USING(warehouse_key) GROUP BY 1 ORDER BY 1''').fetchall()
        details['historical_vs_type1_category']=connection.execute('''SELECT f.source_code,count(*) accepted_lines,
          count(*) FILTER(WHERE f.category_key IS DISTINCT FROM p.category_key) lines_current_category_differs
          FROM dw.fact_order_line_candidate f JOIN dw.dim_source_product_sku p USING(source_product_sku_key) GROUP BY 1 ORDER BY 1''').fetchall()
        details['review_multiplicity']=connection.execute('''WITH groups AS (SELECT order_key,count(*) n FROM dw.fact_review_candidate GROUP BY 1)
          SELECT count(*) reviewed_orders,max(n) max_reviews_per_order,count(*) FILTER(WHERE n>1) multi_review_orders FROM groups''').fetchone()
        details['review_linkage']=connection.execute('SELECT product_linkage_status,count(*) reviews FROM dw.fact_review_candidate GROUP BY 1 ORDER BY 1').fetchall()
        details['review_temporal_quality']=connection.execute('''SELECT count(*) reviews,
          count(*) FILTER(WHERE r.review_date<o.order_date) reviews_before_order_date,
          min(r.review_date) first_review_date,max(r.review_date) last_review_date
          FROM analytics.v_reviews r JOIN analytics.v_orders o USING(order_key)''').fetchone()
        details['naive_fanout_demonstration']=connection.execute('''SELECT count(*) joined_rows,sum(f.order_amount_source) naive_repeated_order_payable,
          (SELECT sum(order_amount_source) FROM dw.fact_order_lifecycle_candidate) correct_order_payable
          FROM dw.fact_order_lifecycle_candidate f JOIN dw.fact_order_line_candidate i USING(order_key)
          LEFT JOIN dw.fact_review_candidate r USING(order_key)''').fetchone()
        checks['fanout_example_detects_inflation']=details['naive_fanout_demonstration']['naive_repeated_order_payable']>details['naive_fanout_demonstration']['correct_order_payable']
        stores=connection.execute('SELECT storefront_code FROM dw.dim_storefront ORDER BY 1').fetchall()
        sources=[r['source_code'] for r in details['raw_sources'] if r['source_code']!='ratings']
        categories=connection.execute('SELECT canonical_category FROM dw.dim_category ORDER BY priority').fetchall()
        wh=connection.execute('SELECT warehouse_key,warehouse_region FROM dw.dim_warehouse ORDER BY 1').fetchall()
        products=connection.execute('''SELECT f.source_product_sku_key product_key,count(*) lines FROM dw.fact_order_line_candidate f
          GROUP BY 1 ORDER BY lines DESC,product_key LIMIT 6''').fetchall()
        provinces=connection.execute('''SELECT p.normalized_province_name province,count(*) n FROM dw.fact_order_line_candidate f
          JOIN dw.dim_province p USING(province_key) GROUP BY 1 ORDER BY n DESC,province LIMIT 5''').fetchall()
        intersections=connection.execute('''SELECT f.source_code source,c.canonical_category category,w.warehouse_key,p.normalized_province_name province,
          to_char(d.calendar_date,'YYYY-MM-01') start_date,(date_trunc('month',d.calendar_date)+interval '1 month'-interval '1 day')::date end_date,count(*) n
          FROM dw.fact_order_line_candidate f JOIN dw.dim_category c USING(category_key) JOIN dw.dim_warehouse w USING(warehouse_key)
          JOIN dw.dim_province p USING(province_key) JOIN dw.dim_date d ON d.date_key=f.order_created_date_key
          GROUP BY 1,2,3,4,5,6 ORDER BY n DESC LIMIT 12''').fetchall()
        probes=[{}]+[{'source':s} for s in sources]+[{'store':s['storefront_code']} for s in stores]
        probes += [{'category':r['canonical_category']} for r in categories]
        probes += [{'warehouse_key':r['warehouse_key']} for r in wh]
        probes += [{'product_key':r['product_key']} for r in products]
        probes += [{'province':r['province']} for r in provinces]+[{'province':'Unknown'}]
        probes += [{'warehouse_region':region} for region in ['Hà Nội','Hồ Chí Minh']]
        probes += [{'status':s} for s in ['COMPLETED','CANCELED','PROCESSING','DELIVERED','RETURNED','UNKNOWN']]
        probes += [{k:str(v) if k.endswith('_date') else v for k,v in r.items() if k!='n'} for r in intersections]
        probes += [{'source':s,'category':c['canonical_category']} for s in sources for c in categories]
        probes += [{'start_date':'2030-01-01'},{'start_date':'2026-10-01','end_date':'2026-10-01'},
                   {'start_date':'2026-01-01','end_date':'2026-09-30','source':'tiktok_bibica'},
                   {'source':'shopee_bibica','store':'bibica_tiktok_shop'}]
        coverage=connection.execute('''SELECT source_code,min(order_date) first_date,max(order_date) last_date
          FROM analytics.v_orders GROUP BY 1 ORDER BY 1''').fetchall()
        common_start=max(r['first_date'] for r in coverage)
        common_end=min(r['last_date'] for r in coverage)
        details['observed_common_window']={'start_date':common_start,'end_date':common_end,
            'complete_daily_exports_proven':False,'source_ranges':coverage}
        probes += [{'source':source,'start_date':str(common_start),'end_date':str(common_end)} for source in sources]
        probes=list({json.dumps(p,ensure_ascii=False,sort_keys=True):p for p in probes}.values())
        results=[]
        with httpx.Client(base_url='http://127.0.0.1:8001', timeout=45) as client:
            for index,probe in enumerate(probes):
                (ROOT/'.runtime/integrity_progress.json').write_text(json.dumps({'index':index,'total':len(probes),'filters':probe},ensure_ascii=False),encoding='utf8')
                expected=independent_kpis(connection,probe)
                response=client.get('/api/v1/overview/kpis',params=probe)
                actual=response.json().get('data',{})
                mismatches=[field for field,value in expected.items() if not equal_measure(value,actual.get(field))]
                results.append({'filters':probe,'status':response.status_code,'measures_checked':len(expected),
                                'mismatched_measures':mismatches,'orders':expected['orders'],'reviews':expected['reviews'],
                                'mismatch_values':{field:{'expected':expected[field],'actual':actual.get(field)} for field in mismatches}})
            full_before=client.get('/api/v1/overview/kpis').json()['data']
        checks['all_multidimensional_api_measures_match_independent_sql']=all(r['status']==200 and not r['mismatched_measures'] for r in results)
        details['cohort_probes']=results
        details['cohort_probe_count']=len(results)
        details['measure_comparisons']=sum(r['measures_checked'] for r in results)
        details['customer_identity']={'status':'UNAVAILABLE','reason':'No verified privacy-safe customer dimension/key in this DW. Province is destination, not customer identity. Do not infer distinct buyers or cross-platform customer joins.'}
        details['resend_lifecycle']={'promised':'UNAVAILABLE','dispatched':'UNAVAILABLE','received':'UNAVAILABLE','resolved':'UNAVAILABLE',
            'reason':'Source snapshots have no verified complaint/resend event lifecycle. Missing is not zero or resolved.'}
        critical_filters={'source':'shopee_bibica','category':'Bánh'}
        critical_expected=independent_kpis(connection,critical_filters)
    def concurrent_read(index):
        started=time.perf_counter()
        source=sources[index%len(sources)]
        with httpx.Client(base_url='http://127.0.0.1:8001',timeout=45) as client:
            response=client.get('/api/v1/overview/kpis',params={'source':source})
            payload=response.json()
        data=payload.get('data',{})
        digest=hashlib.sha256(json.dumps(data,sort_keys=True).encode('utf8')).hexdigest()
        return {'source':source,'status':response.status_code,'elapsed_seconds':round(time.perf_counter()-started,4),'digest':digest}
    started=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        concurrent_results=list(executor.map(concurrent_read,range(24)))
    checks['bounded_concurrent_reads_success']=all(r['status']==200 for r in concurrent_results)
    checks['bounded_concurrent_reads_repeatable']=all(len({r['digest'] for r in concurrent_results if r['source']==s})==1 for s in sources)
    with httpx.Client(base_url='http://127.0.0.1:8001',timeout=45) as client:
        full_after=client.get('/api/v1/overview/kpis').json()['data']
    checks['concurrent_read_cohort_kpis_unchanged']=full_after==full_before
    def critical_read(index):
        with httpx.Client(base_url='http://127.0.0.1:8001',timeout=45) as client:
            response=client.get('/api/v1/overview/kpis',params=critical_filters)
        actual=response.json().get('data',{})
        return {'probe':index,'status':response.status_code,'mismatched_measures':[
            key for key,value in critical_expected.items() if not equal_measure(value,actual.get(key))]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        critical_results=list(executor.map(critical_read,range(16)))
    checks['critical_filtered_cohort_parallel_requests_consistent']=all(r['status']==200 and not r['mismatched_measures'] for r in critical_results)
    details['critical_filtered_cohort_recheck']={'filters':critical_filters,'workers':4,'requests':16,'numeric_measures':len(critical_expected),'results':critical_results}
    elapsed=[r['elapsed_seconds'] for r in concurrent_results]
    details['bounded_concurrency']={'workers':4,'requests':24,'combined_checks_elapsed_seconds':round(time.perf_counter()-started,4),
        'median_seconds':statistics.median(elapsed),'max_seconds':max(elapsed),'results':concurrent_results,
        'scope':'Concurrent read-only KPI requests, not load capacity/solver concurrency/ETL concurrency/crash recovery certification.'}
    result={'status':'PASS' if all(checks.values()) else 'FAIL','executed_at':datetime.now(timezone.utc).isoformat(),
        'checks':checks,'details':details,'limitations':['Read-only HTTP concurrency is bounded, not a production load test.',
        'Customer identity and resend-event lifecycle unavailable.',
        'Source reconciliation uses sanitized staging projections plus native SHA checks, not a new full native XLSX parse.',
        'Reference-only materialized CTE oracle uses SET LOCAL enable_nestloop=off. API planner/runtime is not modified.']}
    dump('integrity.json',result)
    print(json.dumps({'status':result['status'],'checks':checks,'probes':len(results),'measure_comparisons':details['measure_comparisons'],'concurrency':{k:v for k,v in details['bounded_concurrency'].items() if k!='results'}},ensure_ascii=False))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':
    try:
        parser=argparse.ArgumentParser()
        parser.add_argument('--live-capabilities-only',action='store_true')
        args=parser.parse_args()
        raise SystemExit(verify_live_capabilities() if args.live_capabilities_only else main())
    except Exception as error:
        dump('integrity.json',{'status':'FAIL','error_code':type(error).__name__,'executed_at':datetime.now(timezone.utc).isoformat()})
        raise
