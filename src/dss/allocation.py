"""Whole-order assignment via a small binary MILP, with explicit resource constraints."""
from collections import Counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from .evidence import choose_profile
from .scoring import score_profile, shelf_margin


def candidates(request, scenario, context, profiles):
    warehouses = {w['warehouse_key']: w for w in context['warehouses']}
    products = context['products']
    stocks = {(s.warehouse_key, s.product_key): s for s in scenario.stocks}
    exceptions = {(e.warehouse_key,e.product_key):e for e in scenario.breakfast_exceptions}
    referenced_warehouses = {s.warehouse_key for s in scenario.stocks} | set(scenario.capacity_orders) | set(scenario.extra_delay_days) | {e.warehouse_key for e in scenario.breakfast_exceptions}
    if not referenced_warehouses <= set(warehouses):
        raise ValueError('Warehouse inputs must belong to the requested storefront')
    if any(s.product_key not in products for s in scenario.stocks):
        raise ValueError('Stock product must be part of the requested batch')
    if any(e.product_key not in products for e in scenario.breakfast_exceptions) or not set(scenario.breakfast_product_keys)<=set(products):
        raise ValueError('Breakfast controls must refer to products in the requested batch')
    rows = []
    for order_index, order in enumerate(request.orders):
        has_commercial_product = any(products[i.product_key]['canonical_category'] in ['Bánh','Kẹo','Ngũ cốc'] for i in order.items)
        for key in warehouses:
            reasons = []
            profile = choose_profile(profiles, key, order.province, scenario.min_route_samples)
            risk = None
            p90 = None
            shelf = []
            delay = scenario.extra_delay_days.get(key, 0)
            if profile:
                risk = score_profile(profile, profiles.get((key, None)), scenario.risk_weights, scenario.prior_strength)
                p90 = float(profile['p90_lead_days']) + delay
                if risk['risk_score'] is None or risk['risk_score'] > scenario.max_risk_score:
                    reasons.append('RISK_THRESHOLD_OR_MISSING_SCORE')
                if p90 > scenario.max_delivery_days:
                    reasons.append('DELIVERY_THRESHOLD')
            else:
                reasons.append('INSUFFICIENT_TIMING_EVIDENCE')
            for item in order.items:
                product = products[item.product_key]
                stock = stocks.get((key, item.product_key))
                breakfast_default = product.get('breakfast_hn_default', False) or item.product_key in scenario.breakfast_product_keys
                if stock and stock.stock_scope == 'WHOLESALE':
                    reasons.append('WHOLESALE_STOCK_NOT_ECOMMERCE')
                if breakfast_default and warehouses[key]['warehouse_region'] == 'Hồ Chí Minh':
                    if (key,item.product_key) not in exceptions:
                        reasons.append('BREAKFAST_HN_DEFAULT_REQUIRES_EXPLICIT_EXCEPTION')
                    if stock is None or stock.stock_scope != 'ECOMMERCE':
                        reasons.append('BREAKFAST_HCM_REQUIRES_ECOMMERCE_STOCK')
                if product['canonical_category'] is None:
                    reasons.append('UNMAPPED_PRODUCT_MANUAL_REVIEW')
                if product['canonical_category'] == 'Quà tặng':
                    if not has_commercial_product:
                        reasons.append('GIFT_ONLY_ORDER_MANUAL_REVIEW')
                    if stock is None or stock.stock_scope != 'ECOMMERCE':
                        reasons.append('GIFT_REQUIRES_EXPLICIT_ECOMMERCE_STOCK')
                if stock is None:
                    if scenario.stock_mode == 'required':
                        reasons.append('MISSING_STOCK_SCENARIO')
                    elif (key, item.product_key) not in context['observed_pairs']:
                        reasons.append('NO_OBSERVED_SKU_AT_WAREHOUSE')
                elif stock.units < item.quantity:
                    reasons.append('INSUFFICIENT_SCENARIO_STOCK')
                if (product['breakfast_candidate'] or breakfast_default) and (stock is None or stock.remaining_shelf_days is None):
                    reasons.append('MISSING_BREAKFAST_SHELF_LIFE_SCENARIO')
                if stock and stock.remaining_shelf_days is not None and profile:
                    margin = shelf_margin(float(profile['p90_lead_days']), stock.remaining_shelf_days, delay, scenario.min_remaining_days)
                    shelf.append({'product_key': item.product_key, **margin})
                    if not margin['feasible']:
                        reasons.append('SHELF_LIFE_BUFFER')
            feasible = not reasons
            cost = None
            if feasible:
                cost = scenario.risk_weight * risk['risk_score'] / 100 + (1-scenario.risk_weight) * p90 / scenario.max_delivery_days
            rows.append({'order_index': order_index, 'order_ref': order.order_ref, 'warehouse_key': key,
                         'warehouse_region': warehouses[key]['warehouse_region'], 'feasible': feasible,
                         'reasons': sorted(set(reasons)), 'risk': risk, 'evidence': profile,
                         'p90_scenario_delivery_days': p90, 'shelf_life': shelf, 'cost': cost})
    return rows


def optimize(request, scenario, candidate_rows):
    feasible = sorted((r for r in candidate_rows if r['feasible']), key=lambda r:(r['order_ref'],r['warehouse_key']))
    n_orders = len(request.orders)
    order_indexes = sorted(range(n_orders),key=lambda i:request.orders[i].order_ref)
    n_vars = len(feasible) + n_orders
    # Feasible costs are in [0,1]. One unserved order costs > all served costs combined.
    penalty = n_orders + 1
    objective = [r['cost'] + j*1e-10 for j,r in enumerate(feasible)] + [penalty] * n_orders
    matrix, lower, upper = [], [], []
    for i in order_indexes:
        row = [int(r['order_index'] == i) for r in feasible] + [int(j == i) for j in order_indexes]
        matrix.append(row)
        lower.append(1)
        upper.append(1)
    for key, capacity in sorted(scenario.capacity_orders.items()):
        matrix.append([int(r['warehouse_key'] == key) for r in feasible] + [0]*n_orders)
        lower.append(0)
        upper.append(capacity)
    for stock in sorted(scenario.stocks,key=lambda s:(s.warehouse_key,s.product_key)):
        row = []
        for r in feasible:
            quantity = sum(i.quantity for i in request.orders[r['order_index']].items if i.product_key == stock.product_key)
            row.append(quantity if r['warehouse_key'] == stock.warehouse_key else 0)
        matrix.append(row + [0]*n_orders)
        lower.append(0)
        upper.append(stock.units)
    result = milp(np.array(objective), integrality=np.ones(n_vars), bounds=Bounds(0, 1),
        constraints=LinearConstraint(np.array(matrix, dtype=float), np.array(lower), np.array(upper)),
        options={'time_limit': 10.0, 'mip_rel_gap': 0.0})
    if (not result.success or getattr(result,'status',None)!=0 or result.x is None or
            getattr(result,'mip_gap',None) is None or not np.isfinite(result.mip_gap) or result.mip_gap>1e-8):
        raise RuntimeError('Allocation solver did not certify an optimum')
    if (np.shape(result.x)!=(n_vars,) or not np.all(np.isfinite(result.x)) or
            np.any(result.x < -1e-6) or np.any(result.x > 1+1e-6)):
        raise RuntimeError('Allocation result violated finite binary bounds')
    solution = np.rint(result.x)
    resources = np.array(matrix) @ solution
    if (np.max(np.abs(solution-result.x)) > 1e-6 or
            np.any(resources < np.array(lower)-1e-6) or np.any(resources > np.array(upper)+1e-6)):
        raise RuntimeError('Allocation result violated an integer resource constraint')
    selected = [r for j,r in enumerate(feasible) if result.x[j] > .5]
    selected_by_order = {r['order_index']: r for r in selected}
    assignments = []
    for index, order in enumerate(request.orders):
        chosen = selected_by_order.get(index)
        alternatives = [r for r in candidate_rows if r['order_index'] == index]
        assignments.append({'order_ref': order.order_ref, 'province': order.province,
            'warehouse_key': chosen['warehouse_key'] if chosen else None,
            'warehouse_region': chosen['warehouse_region'] if chosen else None,
            'status': 'CONDITIONAL_SCENARIO_ASSIGNMENT' if chosen else 'UNASSIGNED',
            'reason': 'MINIMUM_OBJECTIVE_WITHIN_BATCH_CONSTRAINTS' if chosen else
                      ('SHARED_STOCK_OR_CAPACITY' if any(r['feasible'] for r in alternatives) else 'NO_FEASIBLE_WAREHOUSE'),
            'stockout_cause_observed': False,
            'routing_interpretation': 'Scenario recommendation. Observed cross-region shipping does not prove stockout or a warehouse fault.',
            'candidates': alternatives})
    return {
        'scenario': scenario.model_dump(mode='json'), 'assignments': assignments,
        'summary': {'requested_orders': n_orders, 'assigned_orders': len(selected), 'unassigned_orders': n_orders-len(selected),
                    'warehouse_orders': dict(Counter(r['warehouse_key'] for r in selected)),
                    'mean_risk_score': sum(r['risk']['risk_score'] for r in selected)/len(selected) if selected else None,
                    'mean_p90_scenario_days': sum(r['p90_scenario_delivery_days'] for r in selected)/len(selected) if selected else None,
                    'objective_cost': sum(r['cost'] for r in selected)},
        'solver': {'method': 'binary MILP, whole order, maximize served then minimize weighted risk/time',
                   'optimal': True, 'mip_gap': float(result.mip_gap), 'candidate_count': len(candidate_rows)},
        'operationally_verified': False,
    }
