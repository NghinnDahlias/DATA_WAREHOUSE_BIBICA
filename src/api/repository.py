"""Allowlisted aggregations with the same order/item/review filter semantics."""
from .models import Filters


def cohort(filters: Filters):
    order_terms = ['TRUE']
    item_terms = ['TRUE']
    params = {}
    for field, column in [('start_date', 'o.order_date >= '), ('end_date', 'o.order_date <= '),
                          ('source', 'o.source_code = '), ('store', 'o.storefront_code = '), ('channel', 'upper(o.channel_code) = '),
                          ('status', 'o.canonical_status = ')]:
        value = getattr(filters, field)
        if value is not None:
            order_terms.append(column + '%(' + field + ')s')
            params[field] = value
    for field, column in [('category', 'i.canonical_category'), ('warehouse_key', 'i.warehouse_key'),
                          ('warehouse_region', 'i.warehouse_region'), ('province', 'i.customer_province'),
                          ('product_key', 'i.product_key')]:
        value = getattr(filters, field)
        if value is not None:
            item_terms.append(column + ' = %(' + field + ')s')
            params[field] = value
    item_where = ' AND '.join(item_terms)
    if len(item_terms) > 1:
        order_terms.append('EXISTS(SELECT 1 FROM analytics.v_items i WHERE i.order_key=o.order_key AND ' + item_where + ')')
    review_terms = ['TRUE']
    if filters.end_date:
        review_terms.append('r.review_date <= %(end_date)s')
    if filters.category or filters.warehouse_key or filters.warehouse_region or filters.product_key or filters.province:
        review_terms.append('EXISTS(SELECT 1 FROM filtered_items i WHERE i.order_key=r.order_key AND i.product_key=r.product_key)')
    query = '''WITH filtered_orders AS (
      SELECT o.* FROM analytics.v_orders o WHERE ''' + ' AND '.join(order_terms) + '''
    ), filtered_items AS (
      SELECT i.*,o.canonical_status FROM analytics.v_items i JOIN filtered_orders o USING(order_key)
      WHERE ''' + item_where + '''
    ), filtered_reviews AS (
      SELECT r.* FROM analytics.v_reviews r JOIN filtered_orders o USING(order_key)
      WHERE ''' + ' AND '.join(review_terms) + ') '
    return query, params


def kpis(connection, filters):
    query, params = cohort(filters)
    return connection.execute(query + '''
    SELECT o.*,i.*,r.*,
      o.completed_payable/nullif(o.completed_orders_with_payable,0) completed_aov,
      o.canceled_orders::numeric/nullif(o.orders,0) cancellation_rate,
      o.refund_positive_orders::numeric/nullif(o.refund_observed_orders,0) refund_order_rate,
      i.paired_discount/nullif(i.paired_gross,0) seller_discount_rate,
      r.low_reviews::numeric/nullif(r.reviews,0) low_review_rate,
      r.reviewed_tiktok_orders::numeric/nullif(o.tiktok_orders,0) review_order_coverage
    FROM (
      SELECT count(*) orders,count(*) FILTER(WHERE canonical_status='COMPLETED') completed_orders,
        count(*) FILTER(WHERE canonical_status='CANCELED') canceled_orders,
        count(*) FILTER(WHERE canonical_status='UNKNOWN') unknown_status_orders,
        count(order_payable) payable_observed_orders,sum(order_payable) booked_payable,
        sum(order_payable) FILTER(WHERE canonical_status='COMPLETED') completed_payable,
        count(order_payable) FILTER(WHERE canonical_status='COMPLETED') completed_orders_with_payable,
        sum(observed_refund) observed_refund,count(observed_refund) refund_observed_orders,
        count(*) FILTER(WHERE observed_refund>0) refund_positive_orders,
        count(*) FILTER(WHERE reconciliation_status='CONFLICTING') conflicting_orders,
        count(*) FILTER(WHERE source_code='tiktok_bibica') tiktok_orders,
        CASE WHEN count(DISTINCT source_code)=1 THEN
          avg(extract(epoch FROM(delivered_at-created_at))/86400)
          FILTER(WHERE delivered_at>=created_at) END mean_created_to_recorded_delivery_days,
        count(*) FILTER(WHERE delivered_at>=created_at) delivery_observed_orders
      FROM filtered_orders) o CROSS JOIN (
      SELECT count(*) accepted_lines,sum(quantity) units,sum(gross_item_value) gross_item_value,
        sum(gross_item_value) FILTER(WHERE canonical_status='COMPLETED') completed_gross_item_value,
        sum(quantity) FILTER(WHERE canonical_status='COMPLETED') completed_units,
        sum(observed_item_payable) observed_item_payable,sum(seller_discount) seller_discount,
        count(seller_discount) seller_discount_observed_lines,
        sum(seller_discount) FILTER(WHERE gross_item_value IS NOT NULL) paired_discount,
        sum(gross_item_value) FILTER(WHERE seller_discount IS NOT NULL) paired_gross,
        count(*) FILTER(WHERE seller_discount IS NOT NULL AND gross_item_value IS NOT NULL) discount_paired_lines,
        count(*) FILTER(WHERE canonical_category IS NULL) unmapped_lines
      FROM filtered_items) i CROSS JOIN (
      SELECT count(*) reviews,avg(star_level) review_stars_mean,
        count(*) FILTER(WHERE star_level<=2) low_reviews,
        count(DISTINCT order_key) reviewed_tiktok_orders
      FROM filtered_reviews) r''', params).fetchone()


BREAKDOWNS = {
    'source': ('orders', 'source_code'), 'store': ('orders', 'storefront_code'),
    'status': ('orders', 'canonical_status'), 'month': ('orders', "to_char(order_date,'YYYY-MM')"),
    'category': ('items', 'canonical_category'), 'province': ('items', 'customer_province'),
    'warehouse': ('items', 'warehouse_key'), 'warehouse_region': ('items', 'warehouse_region'),
    'product': ('items', 'product_key'),
}


def breakdown(connection, filters, dimension, limit, offset):
    grain, column = BREAKDOWNS[dimension]
    query, params = cohort(filters)
    params.update(limit=limit, offset=offset)
    if grain == 'orders':
        measures = '''count(*) orders,sum(order_payable) FILTER(WHERE canonical_status='COMPLETED') completed_payable,
          count(*) FILTER(WHERE canonical_status='CANCELED') canceled_orders'''
    else:
        measures = '''count(*) accepted_lines,count(DISTINCT order_key) orders,
          sum(quantity) FILTER(WHERE canonical_status='COMPLETED') completed_units,
          sum(observed_item_payable) FILTER(WHERE canonical_status='COMPLETED') completed_observed_item_payable'''
    # Column and table fragments come only from the fixed allowlist above.
    return connection.execute(query + f'''SELECT {column} group_value,{measures},count(*) OVER() total_groups
      FROM filtered_{grain} GROUP BY 1 ORDER BY 1 NULLS LAST LIMIT %(limit)s OFFSET %(offset)s''', params).fetchall()


def metadata(connection):
    return {
        'stores': connection.execute('SELECT storefront_key,storefront_code,channel_key FROM dw.dim_storefront ORDER BY 1').fetchall(),
        'warehouses': connection.execute('SELECT warehouse_key,storefront_key,normalized_warehouse_name,warehouse_region FROM dw.dim_warehouse ORDER BY 1').fetchall(),
        'categories': connection.execute('SELECT canonical_category FROM dw.dim_category ORDER BY priority').fetchall(),
        'provinces': [r['province'] for r in connection.execute('SELECT DISTINCT normalized_province_name province FROM dw.dim_province ORDER BY 1')],
        'coverage': connection.execute('''SELECT source_code,min(order_date) first_order_date,max(order_date) last_order_date,
           count(*) orders,count(DISTINCT order_date) observed_days FROM analytics.v_orders GROUP BY 1 ORDER BY 1''').fetchall(),
        'capabilities': {
            'customer_identity_analysis': {'status':'UNAVAILABLE','reason':'No privacy-approved conformed customer identity in the DW; province is not customer identity.'},
            'complaint_lifecycle': {'status':'UNAVAILABLE','reason':'No dedicated complaint events and resolution history in the four source contracts.'},
            'replacement_promised': {'status':'UNAVAILABLE','value':None},
            'replacement_sent': {'status':'UNAVAILABLE','value':None},
            'replacement_received': {'status':'UNAVAILABLE','value':None},
            'replacement_resolved': {'status':'UNAVAILABLE','value':None},
            'warehouse_transfer_cause': {'status':'UNAVAILABLE','reason':'No stockout/transfer request event history. Observed warehouse is not a transfer cause.'},
        },
    }


def products(connection, filters, limit, offset, search, sort='key'):
    query, params = cohort(filters)
    params.update(limit=limit, offset=offset, search='%' + search + '%')
    ordering = {'orders':'orders DESC,i.product_key','units':'completed_units DESC NULLS LAST,i.product_key',
                'item_value':'completed_item_value DESC NULLS LAST,i.product_key'}.get(sort,'i.product_key')
    return connection.execute(query + '''SELECT i.product_key,max(i.product_name) product_name,
      max(s.storefront_code) storefront_code,max(p.native_sku_id) native_sku_id,
      max(p.variation_name) variation_name,count(DISTINCT i.order_key) orders,
      array_agg(DISTINCT i.canonical_category) historical_categories,count(*) accepted_lines,
      sum(i.quantity) FILTER(WHERE i.canonical_status='COMPLETED') completed_units,
      sum(i.observed_item_payable) FILTER(WHERE i.canonical_status='COMPLETED') completed_item_value,count(*) OVER() total_products
      FROM filtered_items i
      JOIN dw.dim_source_product_sku p ON p.source_product_sku_key=i.product_key
      JOIN dw.dim_storefront s ON s.storefront_key=i.storefront_key
      WHERE i.product_name ILIKE %(search)s OR p.native_sku_id ILIKE %(search)s
        OR p.seller_sku ILIKE %(search)s OR p.variation_name ILIKE %(search)s
      GROUP BY i.product_key ORDER BY ''' + ordering + ''' LIMIT %(limit)s OFFSET %(offset)s''', params).fetchall()


def overview_dashboard(connection, filters):
    """Linked overview, all panels on one read-only REPEATABLE READ snapshot."""
    query, params = cohort(filters)
    monthly = connection.execute(query + '''SELECT to_char(order_date,'YYYY-MM') period,
      storefront_code,count(*) orders,count(*) FILTER(WHERE canonical_status='CANCELED') canceled_orders,
      sum(order_payable) FILTER(WHERE canonical_status='COMPLETED') completed_payable
      FROM filtered_orders GROUP BY 1,2 ORDER BY 1,2''', params).fetchall()
    return {'kpis': kpis(connection, filters), 'monthly': monthly,
            'stores': breakdown(connection, filters, 'store', 200, 0),
            'categories': breakdown(connection, filters, 'category', 200, 0),
            'provinces': breakdown(connection, filters, 'province', 200, 0),
            'products': products(connection, filters, 8, 0, '', 'units')}


def delivery(connection, filters):
    query, params = cohort(filters)
    return connection.execute(query + '''SELECT source_code,count(*) orders,
      count(*) FILTER(WHERE delivered_at>=created_at) created_to_recorded_samples,
      avg(extract(epoch FROM(delivered_at-created_at))/86400)
        FILTER(WHERE delivered_at>=created_at) mean_created_to_recorded_days,
      count(*) FILTER(WHERE shipped_at>=created_at AND delivered_at>=shipped_at) shipped_to_recorded_samples,
      avg(extract(epoch FROM(delivered_at-shipped_at))/86400)
        FILTER(WHERE shipped_at>=created_at AND delivered_at>=shipped_at) mean_shipped_to_recorded_days
      FROM filtered_orders GROUP BY source_code ORDER BY source_code''', params).fetchall()
