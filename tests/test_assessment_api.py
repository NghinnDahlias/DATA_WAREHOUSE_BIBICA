"""Additional business-cohort regression tests on a newly created disposable DB."""
import concurrent.futures
import os
import unittest

from fastapi.testclient import TestClient

from src.api.app import app
import tests.test_api as fixture_api


@unittest.skipUnless(os.getenv('BIBICA_TEST_DSN'),'Set BIBICA_TEST_DSN for disposable assessment tests')
class BusinessCohortAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_api.APIIntegration.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixture_api.APIIntegration.tearDownClass.__func__(cls)

    def test_five_dimensional_same_line_cohort(self):
        response=self.client.get('/api/v1/overview/kpis',params={
            'source':'tiktok_bibica','category':'Bánh','warehouse_key':self.warehouses['Hồ Chí Minh'],
            'province':'Đồng Nai','status':'COMPLETED','start_date':'2026-10-01','end_date':'2026-10-01'})
        self.assertEqual(response.status_code,200)
        data=response.json()['data']
        self.assertEqual(data['orders'],1)
        self.assertEqual(float(data['completed_payable']),100)
        self.assertEqual(float(data['completed_units']),2)
        # Date cutoff is order_date inclusive and review_date<=end_date, not review_date-as-order_date.
        self.assertEqual(data['reviews'],0)

    def test_source_store_contradiction_and_unknown_destination(self):
        from scripts.assess_integrity import independent_kpis
        with self.assertRaises(ValueError):
            independent_kpis(None,{'source_code':'tiktok_bibica'})
        for filters in [{'source':'shopee_bibica','store':'bibica_tiktok_shop'},{'province':'Unknown'}]:
            data=self.client.get('/api/v1/overview/kpis',params=filters).json()['data']
            self.assertEqual(data['orders'],0)
            self.assertIsNone(data['completed_payable'])
            self.assertIsNone(data['low_review_rate'])

    def test_rating_rate_denominator_is_review_not_all_orders(self):
        data=self.client.get('/api/v1/overview/kpis').json()['data']
        self.assertEqual(data['reviews'],3)
        self.assertEqual(data['low_reviews'],2)
        self.assertAlmostEqual(float(data['low_review_rate']),2/3)
        self.assertNotEqual(float(data['low_review_rate']),2/data['orders'])
        self.assertEqual(data['reviewed_tiktok_orders'],2)

    def test_customer_identity_is_not_an_invented_dimension(self):
        capabilities=self.client.get('/api/v1/meta').json()['data']['capabilities']
        self.assertEqual(capabilities['customer_identity_analysis']['status'],'UNAVAILABLE')
        for stage in ['promised','sent','received','resolved']:
            self.assertEqual(capabilities['replacement_'+stage],{'status':'UNAVAILABLE','value':None})
        self.assertEqual(self.client.get('/api/v1/analytics/customer').status_code,422)
        self.assertEqual(self.client.get('/api/v1/overview/kpis',params={'customer':'synthetic'}).status_code,422)

    def test_missing_month_is_no_row_and_null_sums(self):
        params={'start_date':'2030-01-01','end_date':'2030-01-31'}
        self.assertEqual(self.client.get('/api/v1/analytics/month',params=params).json()['data'],[])
        data=self.client.get('/api/v1/overview/kpis',params=params).json()['data']
        self.assertEqual(data['orders'],0)
        self.assertIsNone(data['seller_discount_rate'])

    def test_parallel_readonly_kpis_repeatable(self):
        def read(_):
            return TestClient(app).get('/api/v1/overview/kpis').json()['data']
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results=list(executor.map(read,range(9)))
        self.assertTrue(all(row==results[0] for row in results))
        self.assertEqual(results[0]['orders'],8)
