import itertools
import unittest

from pydantic import ValidationError

from src.dss.allocation import candidates, optimize
from src.dss.evidence import breakfast_candidate, choose_profile
from src.dss.models import AllocationRequest, RiskWeights, Scenario
from src.dss.scoring import score_profile, shelf_margin, wilson_interval
from src.dss.service import compare


def profile(**changes):
    row = {'warehouse_key': 1, 'route_province': 'Hà Nội', 'orders': 100, 'resolved_orders': 100,
           'canceled_orders': 10, 'canceled_without_timestamp': 0, 'timing_samples': 80,
           'late_orders': 8, 'mean_lead_days': 2, 'median_lead_days': 2, 'p90_lead_days': 3,
           'invalid_chronology_orders': 0, 'reviews': 10, 'low_reviews': 1}
    row.update(changes)
    return row


def request(n=2):
    return AllocationRequest(store='bibica_tiktok_shop', as_of='2026-10-18',
        orders=[{'order_ref': 'O'+str(i), 'province': 'Hà Nội', 'items': [{'product_key': 7, 'quantity': 2}]} for i in range(n)])


def context():
    return {'warehouses': [{'warehouse_key': 1, 'warehouse_region': 'Hà Nội'}, {'warehouse_key': 2, 'warehouse_region': 'Hồ Chí Minh'}],
            'products': {7: {'canonical_category': 'Bánh', 'breakfast_candidate': False}}, 'observed_pairs': {(1,7),(2,7)}}


def profiles():
    return {(1,'Hà Nội'): profile(), (1,None): profile(),
            (2,'Hà Nội'): profile(warehouse_key=2,p90_lead_days=4,canceled_orders=20),
            (2,None): profile(warehouse_key=2,p90_lead_days=4,canceled_orders=20)}


class ScoringTests(unittest.TestCase):
    def test_known_weighted_score(self):
        self.assertAlmostEqual(score_profile(profile(),None,RiskWeights(),0)['risk_score'],10)

    def test_missing_reviews_are_not_zero(self):
        result=score_profile(profile(reviews=0,low_reviews=0),None,RiskWeights(),0)
        self.assertEqual(result['factors'][2]['smoothed_fraction'],None)
        self.assertAlmostEqual(result['factors'][0]['effective_weight'],.5)
        self.assertAlmostEqual(result['available_weight_fraction'],.8)

    def test_missing_all_is_unavailable(self):
        result=score_profile(profile(resolved_orders=0,canceled_orders=0,timing_samples=0,late_orders=0,reviews=0,low_reviews=0),None,RiskWeights(),20)
        self.assertIsNone(result['risk_score'])

    def test_cancellation_monotonic(self):
        a=score_profile(profile(),None,RiskWeights(),0)
        b=score_profile(profile(canceled_orders=30),None,RiskWeights(),0)
        self.assertGreater(b['risk_score'],a['risk_score'])

    def test_shrinkage_towards_baseline(self):
        result=score_profile(profile(resolved_orders=2,canceled_orders=2),profile(),RiskWeights(),20)
        self.assertAlmostEqual(result['factors'][0]['smoothed_fraction'],4/22)

    def test_boundaries(self):
        for fraction in [0,1]:
            result=score_profile(profile(canceled_orders=100*fraction,late_orders=80*fraction,low_reviews=10*fraction),None,RiskWeights(),0)
            self.assertAlmostEqual(result['risk_score'],100*fraction)
            self.assertFalse(result['calibrated_probability'])

    def test_fallback_is_explicit_and_minimum_samples_enforced(self):
        p=profiles();p[(1,'Hà Nội')]['timing_samples']=1
        self.assertEqual(choose_profile(p,1,'Hà Nội',20)['evidence_level'],'WAREHOUSE_ALL_PROVINCES')
        self.assertIsNone(choose_profile(p,1,'Hà Nội',100))

    def test_breakfast_cue_is_not_all_cakes(self):
        self.assertTrue(breakfast_candidate('Bánh Hura ăn sáng'))
        self.assertFalse(breakfast_candidate('Bánh quy'))


class ShelfTests(unittest.TestCase):
    def test_exact_boundary_is_feasible(self):
        self.assertTrue(shelf_margin(3,5,1,1)['feasible'])

    def test_delay_and_expiry_monotonicity(self):
        self.assertFalse(shelf_margin(3,5,2,1)['feasible'])
        self.assertFalse(shelf_margin(3,0,0,0)['feasible'])

    def test_wilson_empty_and_boundaries(self):
        self.assertIsNone(wilson_interval(0,0))
        self.assertAlmostEqual(wilson_interval(0,10)[0],0)
        self.assertAlmostEqual(wilson_interval(10,10)[1],1)


class ModelTests(unittest.TestCase):
    def test_input_guards(self):
        for kwargs in [{'risk_weights': {'cancellation':0,'late_delivery':0,'low_review':0}},
                       {'capacity_orders': {1:-1}}, {'extra_delay_days': {1:-1}},
                       {'stocks':[{'warehouse_key':1,'product_key':7,'units':1}]*2},
                       {'unknown':1}, {'max_delivery_days':float('nan')}]:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValidationError):
                Scenario(**kwargs)

    def test_unknown_province_duplicate_items_and_order_refs(self):
        for change in [{'province':'Nowhere'}, {'items':[{'product_key':7,'quantity':1}]*2}]:
            payload=request(1).model_dump(mode='json');payload['orders'][0].update(change)
            with self.assertRaises(ValidationError):AllocationRequest(**payload)
        payload=request(1).model_dump(mode='json');payload['orders']*=2
        with self.assertRaises(ValidationError):AllocationRequest(**payload)

    def test_dates_and_batch_limit(self):
        payload=request(1).model_dump(mode='json');payload['history_start']='2026-11-01'
        with self.assertRaises(ValidationError):AllocationRequest(**payload)
        payload=request(1).model_dump(mode='json');payload['orders']=[{**payload['orders'][0],'order_ref':'O'+str(i)} for i in range(51)]
        with self.assertRaises(ValidationError):AllocationRequest(**payload)


class AllocationTests(unittest.TestCase):
    def solve(self,scenario,ctx=None,p=None,n=2):
        req=request(n);rows=candidates(req,scenario,ctx or context(),p or profiles())
        return optimize(req,scenario,rows)

    def test_no_inventory_no_assignment_by_default(self):
        self.assertEqual(self.solve(Scenario())['summary']['assigned_orders'],0)

    def test_missing_inventory_assumption_explicit(self):
        result=self.solve(Scenario(stock_mode='assume_available'))
        self.assertEqual(result['summary']['assigned_orders'],2)
        self.assertFalse(result['operationally_verified'])

    def test_capacity_routes_to_other_warehouse(self):
        result=self.solve(Scenario(stock_mode='assume_available',capacity_orders={1:1}))
        self.assertEqual(sorted(a['warehouse_key'] for a in result['assignments']),[1,2])

    def test_shared_inventory_not_individual_only(self):
        result=self.solve(Scenario(stocks=[{'warehouse_key':1,'product_key':7,'units':3},{'warehouse_key':2,'product_key':7,'units':1}]))
        self.assertEqual(result['summary']['assigned_orders'],1)
        self.assertEqual(result['assignments'][1]['reason'],'SHARED_STOCK_OR_CAPACITY')

    def test_no_partial_split_of_whole_order(self):
        ctx=context();ctx['products'][8]={'canonical_category':'Kẹo','breakfast_candidate':False}
        req=request(1);req.orders[0].items.append(type(req.orders[0].items[0])(product_key=8,quantity=1))
        scenario=Scenario(stocks=[{'warehouse_key':1,'product_key':7,'units':3},{'warehouse_key':2,'product_key':8,'units':3}])
        self.assertEqual(optimize(req,scenario,candidates(req,scenario,ctx,profiles()))['summary']['assigned_orders'],0)

    def test_gift_and_unmapped_excluded(self):
        for category in ['Quà tặng',None]:
            ctx=context();ctx['products'][7]['canonical_category']=category
            self.assertEqual(self.solve(Scenario(stock_mode='assume_available'),ctx)['summary']['assigned_orders'],0)

    def test_breakfast_requires_shelf_life_and_expired_rejected(self):
        ctx=context();ctx['products'][7]['breakfast_candidate']=True
        for remaining in [None,2]:
            stocks=[{'warehouse_key':k,'product_key':7,'units':10,'remaining_shelf_days':remaining} for k in [1,2]]
            self.assertEqual(self.solve(Scenario(stocks=stocks),ctx)['summary']['assigned_orders'],0)
        stocks=[{'warehouse_key':k,'product_key':7,'units':10,'remaining_shelf_days':30} for k in [1,2]]
        self.assertEqual(self.solve(Scenario(stocks=stocks),ctx)['summary']['assigned_orders'],2)

    def test_cross_store_warehouse_and_stock_product_rejected(self):
        for scenario in [Scenario(capacity_orders={999:1}),Scenario(stocks=[{'warehouse_key':1,'product_key':999,'units':1}])]:
            with self.assertRaises(ValueError):self.solve(scenario)

    def test_thresholds_and_unknown_evidence_block(self):
        self.assertEqual(self.solve(Scenario(stock_mode='assume_available',max_delivery_days=1))['summary']['assigned_orders'],0)
        self.assertEqual(self.solve(Scenario(stock_mode='assume_available',max_risk_score=0))['summary']['assigned_orders'],0)
        self.assertEqual(self.solve(Scenario(stock_mode='assume_available',min_route_samples=1000))['summary']['assigned_orders'],0)

    def test_optimum_matches_exhaustive_search(self):
        req=request(3);scenario=Scenario(stock_mode='assume_available',capacity_orders={1:1,2:1})
        rows=candidates(req,scenario,context(),profiles());result=optimize(req,scenario,rows)
        possibilities=[]
        for choices in itertools.product([None,1,2],repeat=3):
            if choices.count(1)>1 or choices.count(2)>1:continue
            cost=sum(next(r['cost'] for r in rows if r['order_index']==i and r['warehouse_key']==k) if k else 4 for i,k in enumerate(choices))
            possibilities.append(cost)
        self.assertAlmostEqual(result['summary']['objective_cost']+4*result['summary']['unassigned_orders'],min(possibilities))

    def test_what_if_deltas_and_different_objective(self):
        baseline=self.solve(Scenario(stock_mode='assume_available'))
        after=self.solve(Scenario(stock_mode='assume_available',capacity_orders={1:0}))
        self.assertEqual(compare(baseline,after)['changed_orders'],2)
        after['scenario']['risk_weight']=0
        self.assertIsNone(compare(baseline,after)['objective_cost_delta'])

    def test_deterministic_repeat(self):
        a=self.solve(Scenario(stock_mode='assume_available'))
        b=self.solve(Scenario(stock_mode='assume_available'))
        self.assertEqual(a,b)
