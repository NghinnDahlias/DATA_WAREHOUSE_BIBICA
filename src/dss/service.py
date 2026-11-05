from DW.etl.geography import normalize_province

from . import evidence
from .allocation import candidates, optimize
from .models import AllocationRequest, Demand, Item
from .scoring import shelf_margin, wilson_interval


def allocate(connection, request, scenario, context=None):
    ctx = context or evidence.context(connection, request)
    profiles = evidence.profiles(connection, request.store, request.as_of, request.history_start, scenario.late_threshold_days, scenario.low_star_max)
    rows = candidates(request, scenario, ctx, profiles)
    return optimize(request, scenario, rows)


def compare(base, alternative):
    before = {a['order_ref']: a['warehouse_key'] for a in base['assignments']}
    changed = [a['order_ref'] for a in alternative['assignments'] if before[a['order_ref']] != a['warehouse_key']]
    bs, after = base['summary'], alternative['summary']
    same_policy = all(base['scenario'][k] == alternative['scenario'][k] for k in ['risk_weight', 'max_delivery_days', 'risk_weights', 'late_threshold_days', 'prior_strength', 'low_star_max'])
    return {'changed_orders': len(changed), 'changed_order_refs': changed,
            'assigned_orders_delta': after['assigned_orders']-bs['assigned_orders'],
            'objective_cost_delta': after['objective_cost']-bs['objective_cost'] if same_policy else None,
            'same_assigned_cohort': {k for k,v in before.items() if v is not None} == {a['order_ref'] for a in alternative['assignments'] if a['warehouse_key'] is not None},
            'interpretation': 'Scenario output difference only. Objectives with different weights are not comparable utilities.'}


def what_if(connection, request):
    ctx = evidence.context(connection, request)
    baseline = allocate(connection, request, request.baseline, ctx)
    alternatives = getattr(request, 'alternatives', None) or [request.alternative]
    results = []
    for scenario in alternatives:
        after = allocate(connection, request, scenario, ctx)
        results.append({'result': after, 'comparison': compare(baseline, after)})
    return {'baseline': baseline, 'alternatives': results, 'warnings': evidence.WARNINGS}


def shelf_life(connection, request):
    province = normalize_province(request.province)['customer_province']
    if province == 'Unknown':
        raise ValueError('Unrecognized province')
    batch = AllocationRequest(store=request.store, as_of=request.as_of,
        orders=[Demand(order_ref='SHELF', province=province, items=[Item(product_key=request.product_key, quantity=1)])])
    ctx = evidence.context(connection, batch)
    if request.warehouse_key not in {w['warehouse_key'] for w in ctx['warehouses']}:
        raise ValueError('Warehouse must belong to storefront')
    product = ctx['products'][request.product_key]
    if product['canonical_category'] != 'Bánh':
        raise ValueError('Shelf-life cake simulation requires a canonical Bánh product')
    profiles = evidence.profiles(connection, request.store, request.as_of, None, 5)
    profile = evidence.choose_profile(profiles, request.warehouse_key, province, request.min_route_samples)
    if profile is None:
        return {'status': 'INSUFFICIENT_EVIDENCE', 'product': product, 'warnings': evidence.WARNINGS}
    margin = shelf_margin(float(profile['p90_lead_days']), request.remaining_shelf_days,
                          request.extra_delay_days, request.min_remaining_days)
    threshold = request.remaining_shelf_days-request.min_remaining_days-request.extra_delay_days
    observations = evidence.shelf_observations(connection, request.store, request.as_of, request.warehouse_key,
        province, threshold, profile['evidence_level'] == 'WAREHOUSE_ALL_PROVINCES')
    return {'status': 'SCENARIO', 'product': product, 'evidence': profile, 'shelf_life': margin,
            'historical_threshold_exceedance': {**observations,
                'fraction': observations['exceedances']/observations['samples'] if observations['samples'] else None,
                'wilson_95_interval': wilson_interval(observations['exceedances'], observations['samples']),
                'meaning': 'Observed delivery durations exceeding scenario shelf-life buffer, not spoilage probability'},
            'warnings': evidence.WARNINGS}
