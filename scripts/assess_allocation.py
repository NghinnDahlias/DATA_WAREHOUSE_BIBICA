"""Independent oracle assessment using actual route aggregates and scenario resources."""
import io
import hashlib
import json
import random
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
code_files=['src/dss/allocation.py','src/dss/models.py','src/dss/evidence.py','src/dss/scoring.py',
            'tests/test_dss_business.py','scripts/assess_allocation.py']
code_hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in code_files}

from src.api.db import snapshot
from src.dss.allocation import candidates, optimize
from src.dss.evidence import breakfast_hn_default, context, profiles
from src.dss.models import AllocationRequest, Scenario
from tests.test_dss_business import exhaustive_oracle


def greedy_feasible(request,scenario,rows):
    """A time-first sequential baseline with the same hard resource constraints."""
    stock={(s.warehouse_key,s.product_key):s.units for s in scenario.stocks}
    capacity=dict(scenario.capacity_orders)
    served=[]
    for index,order in enumerate(request.orders):
        eligible=sorted((r for r in rows if r['order_index']==index and r['feasible']),
                        key=lambda r:(r['p90_scenario_delivery_days'],r['warehouse_key']))
        for route in eligible:
            warehouse=route['warehouse_key']
            if capacity.get(warehouse,1)<=0:
                continue
            if any(stock.get((warehouse,item.product_key),0)<item.quantity for item in order.items):
                continue
            capacity[warehouse]=capacity.get(warehouse,len(request.orders))-1
            for item in order.items:
                stock[(warehouse,item.product_key)]-=item.quantity
            served.append(route)
            break
    return {'assigned_orders':len(served),'objective_cost':sum(r['cost'] for r in served),
            'order_refs':[r['order_ref'] for r in served]}


def resource_check(request,scenario,result):
    demand={o.order_ref:o for o in request.orders}
    used_stock={}
    warehouse_orders={}
    for assigned in result['assignments']:
        warehouse=assigned['warehouse_key']
        if warehouse is None:
            continue
        warehouse_orders[warehouse]=warehouse_orders.get(warehouse,0)+1
        for item in demand[assigned['order_ref']].items:
            key=(warehouse,item.product_key)
            used_stock[key]=used_stock.get(key,0)+item.quantity
    stocks={(s.warehouse_key,s.product_key):s.units for s in scenario.stocks}
    return all(used_stock.get(key,0)<=value for key,value in stocks.items()) and all(
        warehouse_orders.get(key,0)<=maximum for key,maximum in scenario.capacity_orders.items())


def assess():
    started=time.perf_counter()
    checks={}
    cases=[]
    rng=random.Random(20261105)
    with snapshot() as connection:
        cutoff=connection.execute('SELECT max(order_date) cutoff FROM analytics.v_orders').fetchone()['cutoff']
        sources=connection.execute('SELECT source_code,sha256,parser_version,row_count FROM ops.source_current ORDER BY 1').fetchall()
        order_coverage=connection.execute('''WITH per_order AS (
          SELECT order_key,bool_or(canonical_category='Quà tặng') gift,
            bool_or(canonical_category IS NULL) unmapped,
            bool_or(canonical_category IN('Bánh','Kẹo','Ngũ cốc')) commercial
          FROM analytics.v_items GROUP BY order_key)
          SELECT o.source_code,count(*) orders,count(*) FILTER(WHERE gift) gift_orders,
            count(*) FILTER(WHERE gift AND commercial) mixed_commercial_gift_orders,
            count(*) FILTER(WHERE gift AND NOT coalesce(commercial,false)) gift_only_orders,
            count(*) FILTER(WHERE unmapped) unmapped_orders
          FROM analytics.v_orders o JOIN per_order USING(order_key) GROUP BY 1 ORDER BY 1''').fetchall()
        stores=connection.execute('SELECT storefront_code FROM dw.dim_storefront ORDER BY storefront_code').fetchall()
        for store in stores:
            code=store['storefront_code']
            catalog=connection.execute('''SELECT p.source_product_sku_key product_key,p.product_name,
                p.canonical_category,count(DISTINCT f.warehouse_key) warehouses
              FROM dw.dim_source_product_sku p JOIN dw.fact_order_line_candidate f USING(source_product_sku_key)
              JOIN dw.dim_storefront s ON s.storefront_key=p.storefront_key
              WHERE s.storefront_code=%s AND p.canonical_category IN('Bánh','Kẹo','Ngũ cốc')
              GROUP BY p.source_product_sku_key HAVING count(DISTINCT f.warehouse_key)=2
              ORDER BY p.source_product_sku_key''',(code,)).fetchall()
            products=[p for p in catalog if not breakfast_hn_default(p['product_name'])][:2]
            assert len(products)==2,'Need two scoped non-breakfast catalog SKUs for allocation oracle'
            product_keys=[p['product_key'] for p in products]
            observed_profiles=profiles(connection,code,cutoff,None,5)
            for case_id in range(30):
                orders=[{'order_ref':'SCENARIO'+str(i),'province':'Hà Nội' if i%2==0 else 'Hồ Chí Minh',
                         'items':[{'product_key':key,'quantity':rng.randint(1,3)} for key in product_keys]}
                        for i in range(3)]
                request=AllocationRequest(store=code,as_of=cutoff,orders=orders)
                ctx=context(connection,request)
                warehouses=[w['warehouse_key'] for w in ctx['warehouses']]
                scenario=Scenario(label='Synthetic resources over observed route history',max_delivery_days=14,
                    stocks=[{'warehouse_key':warehouse,'product_key':product,'units':rng.randint(0,8),
                             'remaining_shelf_days':30,'stock_scope':'ECOMMERCE'}
                            for warehouse in warehouses for product in product_keys],
                    capacity_orders={warehouse:rng.randint(0,3) for warehouse in warehouses})
                rows=candidates(request,scenario,ctx,observed_profiles)
                result=optimize(request,scenario,rows)
                oracle=exhaustive_oracle(request,scenario,rows)
                baseline=greedy_feasible(request,scenario,rows)
                actual=result['summary']
                oracle_equal=(actual['assigned_orders']==oracle['assigned_orders'] and
                              abs(actual['objective_cost']-oracle['objective_cost'])<1e-7)
                checks[code+'_'+str(case_id)]=oracle_equal and resource_check(request,scenario,result)
                cases.append({'store':code,'case':case_id,'product_keys':product_keys,
                              'candidate_routes':len(rows),'feasible_candidate_routes':sum(r['feasible'] for r in rows),
                              'assigned_orders':actual['assigned_orders'],'oracle_assigned_orders':oracle['assigned_orders'],
                              'objective_cost':actual['objective_cost'],'oracle_objective_cost':oracle['objective_cost'],
                              'greedy_baseline_assigned':baseline['assigned_orders'],
                              'oracle_equal':oracle_equal,'resources_valid':resource_check(request,scenario,result)})
    stream=io.StringIO()
    unit=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('tests.test_dss_business'))
    checks['business_test_suite']=unit.wasSuccessful() and not unit.skipped
    checks['optimizer_not_worse_than_feasible_greedy_on_served_count']=all(
        c['assigned_orders']>=c['greedy_baseline_assigned'] for c in cases)
    checks['all_three_shops']=len({c['store'] for c in cases})==3
    checks['source_code_stable_during_assessment']=all(
        hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in code_hashes.items())
    result={'status':'PASS' if all(checks.values()) else 'FAIL','executed_at':datetime.now(timezone.utc).isoformat(),
            'checks':checks,'scenario_cases':len(cases),'unit_tests':unit.testsRun,'unit_failures':len(unit.failures),
            'unit_errors':len(unit.errors),'unit_skips':len(unit.skipped),'elapsed_seconds':round(time.perf_counter()-started,3),
            'served_improvement_over_greedy_cases':sum(c['assigned_orders']>c['greedy_baseline_assigned'] for c in cases),
            'code_sha256':code_hashes,'source_snapshots':sources,
            'whole_order_coverage':order_coverage,
            'cases':cases,'limitations':[
                'Inventory, remaining life, capacities and incoming demands are synthetic scenario inputs.',
                'Historical route evidence is observed data, not a randomized warehouse comparison.',
                'No measured revenue, profit, avoided damage or real stock-out benefit is claimed.',
                'Oracle validates assignment optimization over eligible routes. Business eligibility has separate unit tests.',
                'A low-star threshold or risk weight is a stated scenario choice, not a calibrated business optimum.']}
    output=root/'reports/phase2_assessment'
    output.mkdir(parents=True,exist_ok=True)
    (output/'allocation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (output/'allocation_tests.log').write_text(stream.getvalue(),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','cases']},ensure_ascii=False))
    if not all(checks.values()):
        print(stream.getvalue())
    return 0 if all(checks.values()) else 1


if __name__=='__main__':
    raise SystemExit(assess())
