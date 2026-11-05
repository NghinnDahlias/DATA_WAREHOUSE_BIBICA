"""Business regression and an independent exhaustive optimizer for small batches."""
import itertools
import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from pydantic import ValidationError

from src.dss.allocation import candidates, optimize
from src.dss.evidence import breakfast_hn_default
from src.dss.models import AllocationRequest, Scenario
from src.dss.scoring import score_profile


def fixture_request(orders=None):
    return AllocationRequest(store='bibica_tiktok_shop', as_of='2026-10-18', orders=orders or [
        {'order_ref':'NORTH','province':'Hà Nội','items':[{'product_key':7,'quantity':2}]},
        {'order_ref':'SOUTH','province':'Hồ Chí Minh','items':[{'product_key':7,'quantity':2}]},
    ])


def fixture_context(breakfast=False):
    return {
        'warehouses':[{'warehouse_key':1,'warehouse_region':'Hà Nội'},
                      {'warehouse_key':2,'warehouse_region':'Hồ Chí Minh'}],
        'products':{7:{'canonical_category':'Bánh' if breakfast else 'Kẹo',
                       'breakfast_candidate':breakfast,'breakfast_hn_default':breakfast,
                       'product_name':'Bánh ăn sáng TEST' if breakfast else 'Kẹo TEST'},
                    8:{'canonical_category':'Bánh','breakfast_candidate':False,
                       'breakfast_hn_default':False,'product_name':'Bánh quy TEST'}},
        'observed_pairs':{(warehouse,product) for warehouse in [1,2] for product in [7,8]},
    }


def fixture_profiles(equal=False):
    result={}
    for warehouse in [1,2]:
        p90=2.0 if equal or warehouse==1 else 3.0
        for province in ['Hà Nội','Hồ Chí Minh',None]:
            result[(warehouse,province)]={
                'warehouse_key':warehouse,'route_province':province,'orders':100,
                'resolved_orders':90,'canceled_orders':9,'canceled_without_timestamp':0,
                'timing_samples':80,'late_orders':4,'mean_lead_days':p90-.5,
                'median_lead_days':p90-.5,'p90_lead_days':p90,
                'invalid_chronology_orders':0,'reviews':20,'low_reviews':2,
            }
    return result


def stock_rows(units=20,breakfast=False):
    return [{'warehouse_key':w,'product_key':p,'units':units,
             'remaining_shelf_days':30 if breakfast or p==8 else None,
             'stock_scope':'ECOMMERCE'} for w in [1,2] for p in [7,8]]


def solve(request,scenario,context=None,profiles=None):
    rows=candidates(request,scenario,context or fixture_context(),profiles or fixture_profiles())
    return optimize(request,scenario,rows),rows


def exhaustive_oracle(request,scenario,candidate_rows):
    """Enumerate whole-order choices, checking batch resources independently of MILP."""
    choices=[]
    for order in request.orders:
        eligible=[row for row in candidate_rows if row['order_ref']==order.order_ref and row['feasible']]
        choices.append([None]+eligible)
    limits={(s.warehouse_key,s.product_key):s.units for s in scenario.stocks}
    best=None
    for assignment in itertools.product(*choices):
        capacity={}
        units={}
        for order,route in zip(request.orders,assignment):
            if route is None:
                continue
            key=route['warehouse_key']
            capacity[key]=capacity.get(key,0)+1
            for item in order.items:
                pair=(key,item.product_key)
                units[pair]=units.get(pair,0)+item.quantity
        if any(capacity.get(key,0)>maximum for key,maximum in scenario.capacity_orders.items()):
            continue
        if any(units.get(pair,0)>maximum for pair,maximum in limits.items()):
            continue
        served=sum(route is not None for route in assignment)
        cost=sum(route['cost'] for route in assignment if route is not None)
        objective=(-served,cost)
        if best is None or objective<best:
            best=objective
    return {'assigned_orders':-best[0],'objective_cost':best[1]}


def allocation_map(result):
    return {a['order_ref']:a['warehouse_key'] for a in result['assignments']}


class WarehouseBusinessTests(unittest.TestCase):
    def test_balanced_split_is_not_an_objective(self):
        request=fixture_request()
        result,_=solve(request,Scenario(stocks=stock_rows()))
        self.assertEqual(result['summary']['warehouse_orders'],{1:2})

    def test_northern_customer_can_legitimately_ship_from_south(self):
        request=fixture_request()
        stocks=stock_rows()
        for stock in stocks:
            if stock['warehouse_key']==1:
                stock['units']=0
        result,_=solve(request,Scenario(stocks=stocks))
        self.assertEqual(allocation_map(result),{'NORTH':2,'SOUTH':2})
        self.assertNotIn('STOCKOUT_INFERRED_FROM_HISTORY',str(result))

    def test_whole_mixed_order_cannot_split_stock_across_warehouses(self):
        request=fixture_request([{'order_ref':'MIX','province':'Hà Nội','items':[
            {'product_key':7,'quantity':2},{'product_key':8,'quantity':1}]}])
        stocks=stock_rows()
        for stock in stocks:
            if (stock['warehouse_key'],stock['product_key']) in [(1,8),(2,7)]:
                stock['units']=0
        result,_=solve(request,Scenario(stocks=stocks))
        self.assertEqual(result['summary']['assigned_orders'],0)

    def test_network_shortage_does_not_oversell_stock(self):
        request=fixture_request()
        stocks=stock_rows(units=0)
        next(s for s in stocks if s['warehouse_key']==1 and s['product_key']==7)['units']=3
        result,rows=solve(request,Scenario(stocks=stocks))
        self.assertEqual(result['summary']['assigned_orders'],1)
        self.assertEqual(result['summary']['assigned_orders'],exhaustive_oracle(request,Scenario(stocks=stocks),rows)['assigned_orders'])

    def test_capacity_applies_to_full_batch(self):
        request=fixture_request()
        result,_=solve(request,Scenario(stocks=stock_rows(),capacity_orders={1:0,2:1}))
        self.assertEqual(result['summary']['assigned_orders'],1)
        self.assertEqual(result['summary']['warehouse_orders'],{2:1})

    def test_wholesale_stock_cannot_be_used_for_ecommerce(self):
        stocks=[{**row,'stock_scope':'WHOLESALE'} for row in stock_rows()]
        result,_=solve(fixture_request(),Scenario(stocks=stocks))
        self.assertEqual(result['summary']['assigned_orders'],0)

    def test_mixed_commercial_gift_keeps_all_skus_with_explicit_gift_stock(self):
        request=fixture_request([{'order_ref':'MIX','province':'Hà Nội','items':[
            {'product_key':7,'quantity':2},{'product_key':9,'quantity':1}]}])
        ctx=fixture_context();ctx['products'][9]={'canonical_category':'Quà tặng','breakfast_candidate':False,
            'breakfast_hn_default':False,'product_name':'[QUÀ TẶNG] TEST'}
        stocks=stock_rows()+[{'warehouse_key':w,'product_key':9,'units':1,'stock_scope':'ECOMMERCE'} for w in [1,2]]
        result,_=solve(request,Scenario(stocks=stocks),ctx)
        self.assertEqual(result['summary']['assigned_orders'],1)
        self.assertEqual(result['summary']['warehouse_orders'],{1:1})

    def test_mixed_gift_cannot_use_missing_unverified_or_assumed_stock(self):
        request=fixture_request([{'order_ref':'MIX','province':'Hà Nội','items':[
            {'product_key':7,'quantity':2},{'product_key':9,'quantity':1}]}])
        ctx=fixture_context();ctx['products'][9]={'canonical_category':'Quà tặng','breakfast_candidate':False,
            'breakfast_hn_default':False,'product_name':'[QUÀ TẶNG] TEST'}
        ctx['observed_pairs'].update({(1,9),(2,9)})
        for gift_stocks in [[],[{'warehouse_key':w,'product_key':9,'units':1,'stock_scope':'UNVERIFIED'} for w in [1,2]]]:
            result,_=solve(request,Scenario(stock_mode='assume_available',stocks=stock_rows()+gift_stocks),ctx)
            self.assertEqual(result['summary']['assigned_orders'],0)

    def test_gift_only_requires_manual_review_even_with_stock(self):
        request=fixture_request([{'order_ref':'GIFT','province':'Hà Nội','items':[{'product_key':9,'quantity':1}]}])
        ctx=fixture_context();ctx['products'][9]={'canonical_category':'Quà tặng','breakfast_candidate':False,
            'breakfast_hn_default':False,'product_name':'[QUÀ TẶNG] TEST'}
        stocks=[{'warehouse_key':w,'product_key':9,'units':1,'stock_scope':'ECOMMERCE'} for w in [1,2]]
        result,_=solve(request,Scenario(stocks=stocks),ctx)
        self.assertEqual(result['summary']['assigned_orders'],0)

    def test_unmapped_sku_is_not_silently_removed_from_mixed_order(self):
        request=fixture_request([{'order_ref':'MIX','province':'Hà Nội','items':[
            {'product_key':7,'quantity':2},{'product_key':9,'quantity':1}]}])
        ctx=fixture_context();ctx['products'][9]={'canonical_category':None,'breakfast_candidate':False,
            'breakfast_hn_default':False,'product_name':'Unmapped TEST'}
        stocks=stock_rows()+[{'warehouse_key':w,'product_key':9,'units':1,'stock_scope':'ECOMMERCE'} for w in [1,2]]
        result,_=solve(request,Scenario(stocks=stocks),ctx)
        self.assertEqual(result['summary']['assigned_orders'],0)


class BreakfastBusinessTests(unittest.TestCase):
    def test_name_policy_distinguishes_explicit_breakfast_from_brand(self):
        self.assertTrue(breakfast_hn_default('Combo Bánh ăn sáng Bibica'))
        self.assertTrue(breakfast_hn_default('Bánh bữa sáng'))
        self.assertFalse(breakfast_hn_default('Bánh Hura Deli TEST'))
        self.assertFalse(breakfast_hn_default('Bánh quy TEST'))

    def test_breakfast_defaults_to_hanoi_even_if_hcm_duration_is_lower(self):
        profiles=fixture_profiles()
        for (warehouse,_),profile in profiles.items():
            profile['p90_lead_days']=4 if warehouse==1 else 1
        result,_=solve(fixture_request(),Scenario(stocks=stock_rows(breakfast=True)),fixture_context(True),profiles)
        self.assertEqual(result['summary']['warehouse_orders'],{1:2})

    def test_hanoi_stockout_does_not_invent_southern_exception(self):
        stocks=stock_rows(breakfast=True)
        for stock in stocks:
            if stock['warehouse_key']==1:
                stock['units']=0
        result,_=solve(fixture_request(),Scenario(stocks=stocks),fixture_context(True))
        self.assertEqual(result['summary']['assigned_orders'],0)

    def test_documented_ecommerce_exception_allows_hcm(self):
        stocks=stock_rows(breakfast=True)
        scenario=Scenario(stocks=stocks,capacity_orders={1:0},breakfast_exceptions=[{
            'product_key':7,'warehouse_key':2,'reason':'APPROVED_ECOMMERCE_EXCEPTION',
            'evidence_ref':'SCENARIO-E1','ecommerce_stock_confirmed':True}])
        result,_=solve(fixture_request(),scenario,fixture_context(True))
        self.assertEqual(result['summary']['warehouse_orders'],{2:2})

    def test_exception_does_not_override_wholesale_stock_or_shelf_life(self):
        for scope,remaining in [('WHOLESALE',30),('UNVERIFIED',30),('ECOMMERCE',1)]:
            stocks=[{**s,'stock_scope':scope,'remaining_shelf_days':remaining} for s in stock_rows(breakfast=True)]
            scenario=Scenario(stocks=stocks,capacity_orders={1:0},breakfast_exceptions=[{
                'product_key':7,'warehouse_key':2,'reason':'HN_STOCKOUT_TRANSFER',
                'evidence_ref':'SCENARIO-E2','ecommerce_stock_confirmed':True}])
            result,_=solve(fixture_request(),scenario,fixture_context(True))
            self.assertEqual(result['summary']['assigned_orders'],0)

    def test_exception_requires_explicit_evidence_and_true_confirmation(self):
        for change in [{'evidence_ref':''},{'ecommerce_stock_confirmed':False}]:
            exception={'product_key':7,'warehouse_key':2,'reason':'HN_STOCKOUT_TRANSFER',
                       'evidence_ref':'SCENARIO-E3','ecommerce_stock_confirmed':True,**change}
            with self.assertRaises(ValidationError):
                Scenario(breakfast_exceptions=[exception])

    def test_manual_breakfast_sku_override_uses_same_default_policy(self):
        request=fixture_request()
        scenario=Scenario(stocks=stock_rows(breakfast=True),breakfast_product_keys=[7],capacity_orders={1:0})
        result,_=solve(request,scenario)
        self.assertEqual(result['summary']['assigned_orders'],0)

    def test_exception_is_scoped_to_requested_sku_and_store_warehouse(self):
        request=fixture_request()
        for changes in [{'warehouse_key':999},{'product_key':999}]:
            exception={'product_key':7,'warehouse_key':2,'reason':'APPROVED_ECOMMERCE_EXCEPTION',
                       'evidence_ref':'SCENARIO-E4','ecommerce_stock_confirmed':True,**changes}
            scenario=Scenario(stocks=stock_rows(breakfast=True),breakfast_exceptions=[exception])
            with self.assertRaises(ValueError):
                solve(request,scenario,fixture_context(True))

    def test_breakfast_exception_does_not_override_other_sku_stockout(self):
        request=fixture_request([{'order_ref':'MIX','province':'Hồ Chí Minh','items':[
            {'product_key':7,'quantity':2},{'product_key':8,'quantity':1}]}])
        stocks=stock_rows(breakfast=True)
        next(s for s in stocks if s['warehouse_key']==2 and s['product_key']==8)['units']=0
        scenario=Scenario(stocks=stocks,capacity_orders={1:0},breakfast_exceptions=[{
            'product_key':7,'warehouse_key':2,'reason':'APPROVED_ECOMMERCE_EXCEPTION',
            'evidence_ref':'SCENARIO-E5','ecommerce_stock_confirmed':True}])
        result,_=solve(request,scenario,fixture_context(True))
        self.assertEqual(result['summary']['assigned_orders'],0)


class OptimizerOracleTests(unittest.TestCase):
    def test_seeded_cases_match_independent_exhaustive_oracle(self):
        rng=random.Random(20261105)
        for case in range(30):
            orders=[{'order_ref':'O'+str(i),'province':'Hà Nội' if i%2==0 else 'Hồ Chí Minh',
                     'items':[{'product_key':7,'quantity':rng.randint(1,3)},
                              {'product_key':8,'quantity':rng.randint(1,2)}]} for i in range(3)]
            request=fixture_request(orders)
            scenario=Scenario(stocks=[{**s,'units':rng.randint(0,8)} for s in stock_rows()],
                              capacity_orders={1:rng.randint(0,3),2:rng.randint(0,3)})
            result,rows=solve(request,scenario)
            expected=exhaustive_oracle(request,scenario,rows)
            with self.subTest(case=case):
                self.assertEqual(result['summary']['assigned_orders'],expected['assigned_orders'])
                self.assertAlmostEqual(result['summary']['objective_cost'],expected['objective_cost'],places=7)

    def test_reordered_orders_warehouses_and_resources_preserve_mapping(self):
        orders=[{'order_ref':ref,'province':'Hà Nội','items':[{'product_key':7,'quantity':2}]} for ref in ['C','A','B']]
        scenario=Scenario(stocks=stock_rows(units=2),capacity_orders={1:1,2:1})
        original,_=solve(fixture_request(orders),scenario,profiles=fixture_profiles(equal=True))
        ctx=fixture_context();ctx['warehouses'].reverse()
        reversed_scenario=Scenario(stocks=list(reversed(stock_rows(units=2))),capacity_orders={2:1,1:1})
        changed,_=solve(fixture_request(list(reversed(orders))),reversed_scenario,ctx,fixture_profiles(equal=True))
        self.assertEqual(allocation_map(original),allocation_map(changed))

    def test_solver_timeout_with_feasible_incumbent_is_not_optimal(self):
        request=fixture_request([{'order_ref':'A','province':'Hà Nội','items':[{'product_key':7,'quantity':1}]}])
        scenario=Scenario(stock_mode='assume_available')
        rows=candidates(request,scenario,fixture_context(),fixture_profiles())
        with patch('src.dss.allocation.milp',return_value=SimpleNamespace(success=False,status=1,x=np.array([1,0,0]),mip_gap=.1)):
            with self.assertRaises(RuntimeError):
                optimize(request,scenario,rows)

    def test_solver_nonfinite_bounds_and_nonoptimal_gap_rejected(self):
        request=fixture_request([{'order_ref':'A','province':'Hà Nội','items':[{'product_key':7,'quantity':1}]}])
        scenario=Scenario(stock_mode='assume_available')
        rows=candidates(request,scenario,fixture_context(),fixture_profiles())
        for vector,status,gap in [([float('nan'),0,1],0,0),([-1,0,2],0,0),([1,0,0],1,.1),([1,0,0],0,.1)]:
            with self.subTest(vector=vector,status=status,gap=gap):
                result=SimpleNamespace(success=True,status=status,x=np.array(vector),mip_gap=gap)
                with patch('src.dss.allocation.milp',return_value=result),self.assertRaises(RuntimeError):
                    optimize(request,scenario,rows)


class RiskInterpretationTests(unittest.TestCase):
    def test_reviews_missing_differ_from_zero_bad_reviews(self):
        profile=fixture_profiles()[(1,'Hà Nội')]
        zero=score_profile({**profile,'low_reviews':0},None,Scenario().risk_weights,0)
        missing=score_profile({**profile,'reviews':0,'low_reviews':0},None,Scenario().risk_weights,0)
        self.assertIsNotNone(zero['factors'][2]['smoothed_fraction'])
        self.assertIsNone(missing['factors'][2]['smoothed_fraction'])
        self.assertLess(missing['available_weight_fraction'],zero['available_weight_fraction'])

    def test_review_weight_sensitivity_does_not_claim_probability(self):
        profile=fixture_profiles()[(1,'Hà Nội')]
        worse={**profile,'low_reviews':10}
        weight0=Scenario(risk_weights={'cancellation':1,'late_delivery':0,'low_review':0}).risk_weights
        weight1=Scenario(risk_weights={'cancellation':0,'late_delivery':0,'low_review':1}).risk_weights
        self.assertEqual(score_profile(profile,None,weight0,0)['risk_score'],score_profile(worse,None,weight0,0)['risk_score'])
        self.assertGreater(score_profile(worse,None,weight1,0)['risk_score'],score_profile(profile,None,weight1,0)['risk_score'])
        self.assertFalse(score_profile(worse,None,weight1,0)['calibrated_probability'])
