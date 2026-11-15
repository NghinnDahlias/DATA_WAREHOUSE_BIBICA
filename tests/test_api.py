import os
import tempfile
import unittest
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from fastapi.testclient import TestClient

from DW.etl.engine import load_postgres
from DW.etl.sources import project
from src.api.app import app
from src.api.db import database_dsn, snapshot
from tests.test_etl import rating, sales, write


class APISafety(unittest.TestCase):
    def test_parent_database_guard(self):
        with patch.dict(os.environ, {'BIBICA_DSN':'postgresql://warehouse@127.0.0.1:55432/warehouse'}):
            with self.assertRaises(ValueError):database_dsn()

    def test_validation_does_not_echo_input(self):
        client=TestClient(app)
        text='PRIVATE_SENTINEL'
        response=client.get('/api/v1/overview/kpis',params={'status':text})
        self.assertEqual(response.status_code,422)
        self.assertNotIn(text,response.text)

    def test_database_error_is_sanitized(self):
        with patch('src.api.app.snapshot',side_effect=psycopg.OperationalError('PRIVATE_DSN_SENTINEL')):
            response=TestClient(app).get('/health')
        self.assertEqual(response.status_code,503)
        self.assertNotIn('PRIVATE_DSN_SENTINEL',response.text)

    def test_shopee_shipped_header_is_nfc(self):
        record=sales(False,**{'Ngày gửi hàng':'2026-10-02 10:00:00'})
        self.assertEqual(project('shopee_bibica',2,record)['shipped'],'2026-10-02 10:00:00')


@unittest.skipUnless(os.getenv('BIBICA_TEST_DSN'),'Set BIBICA_TEST_DSN for disposable PostgreSQL API tests')
class APIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=os.environ['BIBICA_TEST_DSN'];cls.db='bibica_api_'+uuid.uuid4().hex[:12]
        with psycopg.connect(cls.server,autocommit=True) as c:
            c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(cls.db)))
        cls.dsn=make_conninfo(cls.server,dbname=cls.db)
        cls.directory=tempfile.TemporaryDirectory();folder=Path(cls.directory.name)
        try:
            shipped={'Ngày gửi hàng':'2026-10-02 10:00:00','Thời gian hoàn thành đơn hàng':'2026-10-05 10:00:00'}
            write(folder,'shopee_bibica',[sales(False,**shipped)])
            write(folder,'shopee_quasure',[sales(False,**shipped)])
            base={'Product Name':'Bánh Hura TEST','Warehouse Name':'BIBICA HN',
                  'Shipped Time':'2026-10-02 10:00:00','Delivered Time':'2026-10-04 10:00:00'}
            rows=[sales(**base),sales(**{**base,'SKU ID':'2000000000000000002','Product Name':'Kẹo TEST',
                    'Quantity':'1','Warehouse Name':'BIBICA HCM'}),
                  sales(**{**base,'Order ID':'100000000000000002','Order Status':'Cancelled','Order Amount':'0',
                    'Shipped Time':'','Delivered Time':'','Cancelled Time':'2026-10-01 12:00:00'}),
                  sales(**{**base,'Order ID':'100000000000000003','Warehouse Name':'BIBICA HCM',
                    'Delivered Time':'2026-10-06 10:00:00','Order Amount':'100'}),
                  sales(**{**base,'Order ID':'100000000000000004','Order Status':'In Transit','Delivered Time':'','Order Amount':'100'}),
                  sales(**{**base,'Order ID':'100000000000000005','SKU ID':'other','Product Name':'Mystery TEST','Warehouse Name':'BIBICA HCM','Order Amount':'200'}),
                  sales(**{**base,'Order ID':'100000000000000006','SKU ID':'gift','Product Name':'[QUÀ TẶNG] Bánh TEST','Warehouse Name':'BIBICA HCM','Order Amount':'50'})]
            write(folder,'tiktok_bibica',rows)
            r1=rating();r1['data3']='Bánh Hura TEST'
            r2={**rating(),'product_id':'3000000000000000002','data2':'3000000000000000002','data3':'Kẹo TEST','rating':'1'}
            r3={**rating('100000000000000003'),'data3':'Bánh Hura TEST','rating':'2'}
            write(folder,'ratings',[r1,r2,r3])
            load_postgres(folder,cls.dsn,'api-tests')
            cls.environment=patch.dict(os.environ,{'BIBICA_DSN':cls.dsn});cls.environment.start()
            cls.client=TestClient(app)
            with psycopg.connect(cls.dsn) as c:
                cls.product=c.execute("SELECT source_product_sku_key FROM dw.dim_source_product_sku WHERE product_name='Bánh Hura TEST'").fetchone()[0]
                cls.warehouses=dict(c.execute("SELECT warehouse_region,warehouse_key FROM dw.dim_warehouse WHERE storefront_key=(SELECT storefront_key FROM dw.dim_storefront WHERE storefront_code='bibica_tiktok_shop')").fetchall())
        except Exception:
            cls.directory.cleanup()
            with psycopg.connect(cls.server,autocommit=True) as c:c.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(cls.db)))
            raise

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop();cls.directory.cleanup()
        with psycopg.connect(cls.server,autocommit=True) as c:
            c.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(cls.db)))

    def kpi(self,**params):
        response=self.client.get('/api/v1/overview/kpis',params=params)
        self.assertEqual(response.status_code,200,response.text)
        return response.json()['data']

    def test_phase3_channel_filter_and_absent_shopee_reviews(self):
        shopee = self.kpi(channel='SHOPEE')
        self.assertEqual(shopee['orders'], self.kpi(source='shopee_bibica')['orders'] + self.kpi(source='shopee_quasure')['orders'])
        self.assertEqual(self.kpi(channel='TIKTOK')['orders'], self.kpi(source='tiktok_bibica')['orders'])
        self.assertEqual(self.kpi(channel='SHOPEE', store='bibica_tiktok_shop')['orders'], 0)
        r = self.client.get('/api/v1/customer/review-themes', params={'channel':'SHOPEE'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['data']['availability'], 'UNAVAILABLE_NO_SHOPEE_RATING_SOURCE')
        self.assertIsNone(r.json()['data']['safety_signal_reviews'])

    def test_review_case_cohort_pagination_freshness_and_privacy(self):
        from src.api.review_privacy import CONTENT_VERSION
        from src.dss.review_audit import VERSION
        path='/api/v1/customer/review-cases'
        baseline=self.kpi()
        missing=self.client.get(path).json()['data']
        self.assertEqual(missing['total'],baseline['low_reviews'])
        self.assertTrue(all(r['content_status']=='UNAVAILABLE_NOT_PREPARED' for r in missing['rows']))
        try:
            with psycopg.connect(self.dsn) as c:
                c.execute('''INSERT INTO dw.review_case_content(review_key,source_sha256,source_row_hash,content_version,redacted_text)
                    SELECT r.review_key,s.source_sha256,r.source_row_hash,%s,'bánh bị vỡ [đã ẩn số]'
                    FROM dw.fact_review_candidate r JOIN dw.dim_source_file s USING(source_file_key) WHERE star_level<=3''',(CONTENT_VERSION,))
                c.execute('''INSERT INTO dw.review_theme_feature(review_key,labels,severity,text_present,audit_version,source_sha256)
                    SELECT r.review_key,'["product_breakage_mention"]'::jsonb,'FULFILLMENT_DAMAGE_SIGNAL',true,%s,s.source_sha256
                    FROM dw.fact_review_candidate r JOIN dw.dim_source_file s USING(source_file_key) WHERE star_level<=2''',(VERSION,))
            page=self.client.get(path,params={'limit':1}).json()['data']
            self.assertEqual(page['total'],2)
            key=page['rows'][0]['case_key']
            detail=self.client.get(f'{path}/{key}').json()['data']
            self.assertEqual(detail['content_status'],'READY')
            self.assertEqual(detail['content'],'bánh bị vỡ [đã ẩn số]')
            self.assertEqual(set(detail),{'case_key','star_level','review_date','product_name','labels','content_status','content'})
            second=self.client.get(path,params={'offset':1,'limit':1}).json()['data']
            self.assertNotEqual(second['rows'][0]['case_key'],key)
            self.assertEqual(self.client.get(path,params={'offset':20}).json()['data']['total'],2)
            self.assertEqual(self.client.get(path,params={'topic':'product_breakage_mention'}).json()['data']['total'],2)
            self.assertEqual(self.client.get(path,params={'topic':'missing_items_mention'}).json()['data']['total'],0)
            self.assertEqual(self.client.get(f'{path}/{key}',params={'channel':'SHOPEE'}).status_code,404)
            self.assertEqual(self.client.get(path,params={'channel':'SHOPEE'}).json()['data']['total'],0)
            self.assertEqual(self.client.get(path,params={'category':'Quà tặng'}).json()['data']['total'],0)
            self.assertEqual(self.client.get(path,params={'product_key':self.product}).json()['data']['total'],1)
            with psycopg.connect(self.dsn) as c:
                positive=c.execute('SELECT review_key FROM dw.fact_review_candidate WHERE star_level>3 LIMIT 1').fetchone()[0]
                c.execute('UPDATE dw.review_case_content SET source_sha256=%s WHERE review_key=%s',('stale',key))
            self.assertEqual(self.client.get(f'{path}/{positive}').status_code,404)
            stale=self.client.get(f'{path}/{key}').json()['data']
            self.assertEqual(stale['content_status'],'UNAVAILABLE_NOT_PREPARED')
            self.assertIsNone(stale['content'])
            self.assertEqual(self.kpi(),baseline)
        finally:
            with psycopg.connect(self.dsn) as c:
                c.execute('DELETE FROM dw.review_case_content')
                c.execute('DELETE FROM dw.review_theme_feature')

    def test_review_case_query_validation(self):
        path='/api/v1/customer/review-cases'
        for params in [{'stars_max':0},{'stars_max':4},{'topic':"'; DROP TABLE test"},{'limit':201},{'offset':-1}]:
            self.assertEqual(self.client.get(path,params=params).status_code,422)

    def test_phase3_feature_coverage_version_and_source_freshness(self):
        from src.dss.review_audit import VERSION
        path = '/api/v1/customer/review-themes'
        self.assertEqual(self.client.get(path).json()['data']['availability'], 'UNAVAILABLE_INCOMPLETE_FEATURES')
        try:
            with psycopg.connect(self.dsn) as c:
                c.execute("""INSERT INTO dw.review_theme_feature(review_key,labels,severity,text_present,audit_version,source_sha256)
                    SELECT r.review_key,'["packaging_damage_mention"]'::jsonb,'FULFILLMENT_DAMAGE_SIGNAL',true,%s,s.source_sha256
                    FROM dw.fact_review_candidate r JOIN dw.dim_source_file s USING(source_file_key)""", (VERSION,))
            d = self.client.get(path).json()['data']
            self.assertEqual(d['availability'], 'READY')
            self.assertEqual(d['audited_reviews'], 3)
            self.assertEqual(d['labels'][0]['mentions'], 3)
            self.assertEqual(d['labels'][0]['negative_mentions'], 2)
            with psycopg.connect(self.dsn) as c:
                c.execute("UPDATE dw.review_theme_feature SET source_sha256='stale' WHERE review_key=(SELECT min(review_key) FROM dw.review_theme_feature)")
            d = self.client.get(path).json()['data']
            self.assertEqual(d['availability'], 'UNAVAILABLE_INCOMPLETE_FEATURES')
            self.assertIsNone(d['text_present_reviews'])
            self.assertEqual(d['labels'], [])
            with psycopg.connect(self.dsn) as c:
                c.execute("UPDATE dw.review_theme_feature SET audit_version='old'")
            self.assertEqual(self.client.get(path).json()['data']['audited_reviews'], 0)
        finally:
            with psycopg.connect(self.dsn) as c:
                c.execute('DELETE FROM dw.review_theme_feature')

    def payload(self):
        return {'store':'bibica_tiktok_shop','as_of':'2026-10-18','orders':[
            {'order_ref':'DEMO','province':'Đồng Nai','items':[{'product_key':self.product,'quantity':2}]}],
            'scenario':{'min_route_samples':1,'risk_weight':0,'stocks':[{'warehouse_key':k,'product_key':self.product,'units':10,'remaining_shelf_days':30} for k in self.warehouses.values()]}}

    def test_health_schema_and_contract(self):
        self.assertTrue(self.client.get('/health').json()['data']['ready'])
        spec=self.client.get('/openapi.json').json()
        self.assertIn('/api/v1/dss/what-if',spec['paths'])
        self.assertEqual(len(self.client.get('/api/v1/kpi-contract').json()['data']['metrics']),16)
        self.assertEqual(len(self.client.get('/api/v1/kpi-contract').json()['data']['unavailable_metrics']),2)
        self.assertEqual(len(self.client.get('/api/v1/meta').json()['data']['categories']),4)

    def test_order_money_not_multiplied(self):
        data=self.kpi()
        self.assertEqual((data['orders'],data['accepted_lines'],data['reviews']),(8,9,3))
        self.assertEqual(float(data['completed_payable']),890)
        self.assertEqual(float(data['completed_units']),13)
        self.assertIsNone(data['mean_created_to_recorded_delivery_days'])

    def test_same_line_warehouse_category_filter(self):
        data=self.kpi(store='bibica_tiktok_shop',category='Bánh',warehouse_key=self.warehouses['Hồ Chí Minh'])
        self.assertEqual(data['orders'],1)
        self.assertEqual(float(data['completed_payable']),100)
        self.assertEqual(data['reviews'],1)

    def test_empty_null_and_inclusive_date(self):
        empty=self.kpi(start_date='2030-01-01')
        self.assertEqual(empty['orders'],0);self.assertIsNone(empty['booked_payable']);self.assertIsNone(empty['completed_aov'])
        self.assertEqual(self.kpi(start_date='2026-10-01',end_date='2026-10-01')['orders'],8)
        self.assertEqual(self.kpi(end_date='2026-10-03')['reviews'],0)

    def test_invalid_and_injection_inputs(self):
        for params in [{'category':'Unknown'},{'start_date':'2026-11-01','end_date':'2026-10-01'},
                       {'store':"x';DROP TABLE dw.dim_category;--"},{'arbitrary_sql':'SELECT 1'}]:
            self.assertEqual(self.client.get('/api/v1/overview/kpis',params=params).status_code,422)
        self.assertEqual(self.kpi(province="x';DROP TABLE dw.dim_category;--")['orders'],0)

    def test_pagination_and_product_search(self):
        response=self.client.get('/api/v1/products',params={'limit':1,'offset':1})
        self.assertEqual(response.status_code,200);self.assertEqual(len(response.json()['data']),1)
        self.assertEqual(self.client.get('/api/v1/analytics/source?limit=201').status_code,422)
        self.assertEqual(self.client.get('/api/v1/analytics/raw_sql').status_code,422)
        self.assertEqual(self.client.get('/api/v1/products',params={'search':"';DROP TABLE dw.dim_category;--"}).json()['data'],[])

    def test_readonly_snapshot(self):
        with snapshot() as c:
            self.assertEqual(c.execute('SHOW transaction_read_only').fetchone()['transaction_read_only'],'on')
            self.assertEqual(c.execute('SHOW max_parallel_workers_per_gather').fetchone()['max_parallel_workers_per_gather'],'0')
            with self.assertRaises(psycopg.errors.ReadOnlySqlTransaction):c.execute('DELETE FROM dw.dim_category')

    def test_product_identity_preserves_native_sku_and_store(self):
        response=self.client.get('/api/v1/products',params={'product_key':self.product})
        self.assertEqual(response.status_code,200)
        row=response.json()['data'][0]
        with psycopg.connect(self.dsn) as c:
            native=c.execute('SELECT native_sku_id FROM dw.dim_source_product_sku WHERE source_product_sku_key=%s',(self.product,)).fetchone()[0]
        self.assertEqual(row['native_sku_id'],native)
        self.assertIsInstance(row['native_sku_id'],str)
        self.assertEqual(row['storefront_code'],'bibica_tiktok_shop')
        found=self.client.get('/api/v1/products',params={'search':native,'sort':'orders'}).json()['data']
        self.assertTrue(any(p['product_key']==self.product for p in found))

    def test_product_popularity_paging_and_sort_allowlist(self):
        rows=self.client.get('/api/v1/products',params={'sort':'orders'}).json()['data']
        self.assertEqual([(r['orders'],r['product_key']) for r in rows],sorted([(r['orders'],r['product_key']) for r in rows],key=lambda x:(-x[0],x[1])))
        second=self.client.get('/api/v1/products',params={'sort':'orders','limit':1,'offset':1}).json()['data']
        self.assertEqual(second[0]['product_key'],rows[1]['product_key'])
        self.assertEqual(self.client.get('/api/v1/products',params={'sort':'orders;DROP TABLE x'}).status_code,422)

    def test_linked_dashboard_reconciles_all_panels_to_filtered_orders(self):
        for params in [{},{'store':'bibica_tiktok_shop'},{'status':'CANCELED'},
                       {'product_key':self.product,'category':'Bánh','province':'Đồng Nai'}]:
            with self.subTest(params=params):
                response=self.client.get('/api/v1/overview/dashboard',params=params)
                self.assertEqual(response.status_code,200)
                board=response.json()['data']
                independent=self.client.get('/api/v1/overview/kpis',params=params).json()['data']
                self.assertEqual(board['kpis'],independent)
                self.assertEqual(sum(r['orders'] for r in board['stores']),independent['orders'])
                self.assertEqual(sum(r['orders'] for r in board['monthly']),independent['orders'])
                self.assertEqual(sum(Decimal(r['completed_payable'] or '0') for r in board['monthly']),Decimal(independent['completed_payable'] or '0'))
                self.assertEqual(sum(Decimal(r['completed_units'] or '0') for r in board['categories']),Decimal(independent['completed_units'] or '0'))

    def test_linked_dashboard_empty_and_rank_grain(self):
        empty=self.client.get('/api/v1/overview/dashboard',params={'province':'NONEXISTENT TEST'}).json()['data']
        self.assertEqual(empty['kpis']['orders'],0)
        self.assertEqual(empty['products'],[])
        rows=self.client.get('/api/v1/products',params={'sort':'units'}).json()['data']
        units=[Decimal(r['completed_units']) for r in rows if r['completed_units'] is not None]
        self.assertEqual(units,sorted(units,reverse=True))
        for r in rows:
            filtered=self.kpi(product_key=r['product_key'])
            self.assertEqual(r['completed_units'],filtered['completed_units'])
            self.assertIn('completed_item_value',r)

    def test_geography_not_warehouse_inferred(self):
        data=self.kpi(province='Đồng Nai')
        self.assertEqual(data['orders'],8)
        response=self.client.get('/api/v1/operations/delivery')
        self.assertTrue(all(r['shipped_to_recorded_samples']>0 for r in response.json()['data']))

    def test_allocate_real_sql_evidence(self):
        response=self.client.post('/api/v1/dss/allocate',json=self.payload())
        self.assertEqual(response.status_code,200,response.text)
        data=response.json()['data'];self.assertEqual(data['summary']['assigned_orders'],1)
        self.assertEqual(data['assignments'][0]['warehouse_key'],self.warehouses['Hà Nội'])
        self.assertFalse(data['operationally_verified'])

    def test_shelf_life_cutoff_and_delay(self):
        body={'store':'bibica_tiktok_shop','product_key':self.product,'warehouse_key':self.warehouses['Hà Nội'],
              'province':'Đồng Nai','as_of':'2026-10-18','remaining_shelf_days':5,'min_route_samples':1}
        a=self.client.post('/api/v1/dss/shelf-life',json=body)
        self.assertEqual(a.status_code,200,a.text)
        b=self.client.post('/api/v1/dss/shelf-life',json={**body,'extra_delay_days':10}).json()['data']
        self.assertTrue(a.json()['data']['shelf_life']['feasible']);self.assertFalse(b['shelf_life']['feasible'])
        self.assertEqual(b['historical_threshold_exceedance']['fraction'],1)
        body['as_of']='2026-10-01'
        self.assertEqual(self.client.post('/api/v1/dss/shelf-life',json=body).json()['data']['status'],'INSUFFICIENT_EVIDENCE')

    def test_risk_and_time_weights_change_assignment(self):
        body=self.payload()
        body['scenario']['risk_weights']={'cancellation':.8,'late_delivery':.2,'low_review':0}
        fast=self.client.post('/api/v1/dss/allocate',json=body).json()['data']
        body['scenario']['risk_weight']=1
        safer=self.client.post('/api/v1/dss/allocate',json=body).json()['data']
        self.assertNotEqual(fast['assignments'][0]['warehouse_key'],safer['assignments'][0]['warehouse_key'])

    def test_multiwarehouse_reviews_attributed_once_by_historical_sku(self):
        from src.dss.evidence import profiles
        with snapshot() as c:
            result=profiles(c,'bibica_tiktok_shop',date(2026,10,18),None,5)
        north=result[(self.warehouses['Hà Nội'],'Đồng Nai')]
        south=result[(self.warehouses['Hồ Chí Minh'],'Đồng Nai')]
        self.assertEqual((int(north['reviews']),int(south['reviews'])),(1,2))
        self.assertEqual((int(north['low_reviews']),int(south['low_reviews'])),(0,2))

    def test_dss_rating_threshold_sensitivity_and_missing_availability(self):
        from src.dss.evidence import profiles
        with snapshot() as c:
            counts=[int(profiles(c,'bibica_tiktok_shop',date(2026,10,18),None,5,t)[(self.warehouses['Hồ Chí Minh'],'Đồng Nai')]['low_reviews']) for t in [1,2,3]]
        self.assertEqual(counts,[1,2,2])
        response=self.client.get('/api/v1/overview/kpis',params={'source':'shopee_bibica'})
        self.assertEqual(response.json()['meta']['metric_availability']['review_metrics'],'UNAVAILABLE_NO_SHOPEE_RATING_SOURCE')
        self.assertEqual(self.client.get('/api/v1/dss/risk',params={'store':'bibica_tiktok_shop','as_of':'2026-10-18','low_star_max':4}).status_code,422)

    def test_known_future_cancel_outcome_excluded_from_dss(self):
        from src.dss.evidence import profiles
        with psycopg.connect(self.dsn) as c:
            key=c.execute("SELECT order_lifecycle_key FROM dw.fact_order_lifecycle_candidate f JOIN dw.dim_order_status s USING(order_status_key) WHERE s.reviewed_status='CANCELED'").fetchone()[0]
            original=c.execute('SELECT cancelled_date_key FROM dw.fact_order_lifecycle_candidate WHERE order_lifecycle_key=%s',(key,)).fetchone()[0]
            c.execute('UPDATE dw.fact_order_lifecycle_candidate SET cancelled_date_key=20261006 WHERE order_lifecycle_key=%s',(key,))
        try:
            with snapshot() as c:
                rows=profiles(c,'bibica_tiktok_shop',date(2026,10,3),None,5)
            row=rows[(self.warehouses['Hà Nội'],'Đồng Nai')]
            self.assertEqual(row['canceled_orders'],0)
            self.assertGreater(row['known_future_outcomes_excluded'],0)
        finally:
            with psycopg.connect(self.dsn) as c:c.execute('UPDATE dw.fact_order_lifecycle_candidate SET cancelled_date_key=%s WHERE order_lifecycle_key=%s',(original,key))

    def test_what_if_and_sensitivity_same_snapshot(self):
        body=self.payload();baseline=body.pop('scenario')
        alternative={**baseline,'capacity_orders':{str(self.warehouses['Hà Nội']):0}}
        response=self.client.post('/api/v1/dss/what-if',json={**body,'baseline':baseline,'alternative':alternative})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['data']['alternatives'][0]['comparison']['changed_orders'],1)
        response=self.client.post('/api/v1/dss/sensitivity',json={**body,'baseline':baseline,'alternatives':[alternative]})
        self.assertEqual(response.status_code,200,response.text)

    def test_dss_cross_store_and_missing_inventory(self):
        body=self.payload();body['scenario']={}
        self.assertEqual(self.client.post('/api/v1/dss/allocate',json=body).json()['data']['summary']['assigned_orders'],0)
        body=self.payload();body['store']='bibica_official_store'
        self.assertEqual(self.client.post('/api/v1/dss/allocate',json=body).status_code,422)

    def test_review_and_timing_no_lookahead(self):
        data=self.client.get('/api/v1/dss/risk',params={'store':'bibica_tiktok_shop','as_of':'2026-10-03'}).json()['data']
        self.assertTrue(all(r['timing_samples']==0 and int(r['reviews'])==0 for r in data))

    def test_risk_cohort_excludes_gift_and_unmapped_only_orders(self):
        with snapshot() as c:
            self.assertEqual(c.execute("SELECT count(*) n FROM dss.v_route_orders WHERE storefront_code='bibica_tiktok_shop'").fetchone()['n'],5)

    def test_small_dimension_statistics_updated_after_etl(self):
        with snapshot() as c:
            self.assertEqual(c.execute("SELECT reltuples::integer n FROM pg_class WHERE oid='dw.dim_category'::regclass").fetchone()['n'],4)

    def test_solver_failure_returns_sanitized_503(self):
        with patch('src.api.dss_routes.service.allocate',side_effect=RuntimeError('PRIVATE_SENTINEL')):
            response=self.client.post('/api/v1/dss/allocate',json=self.payload())
        self.assertEqual(response.status_code,503)
        self.assertNotIn('PRIVATE_SENTINEL',response.text)

    def test_api_no_private_fields(self):
        for endpoint in ['/api/v1/overview/kpis','/api/v1/products','/api/v1/quality','/api/v1/meta']:
            text=self.client.get(endpoint).text
            for field in ['native_order_id','order_namespace','review_text','user_name','phone','tracking']:
                self.assertNotIn('"'+field+'"',text)
