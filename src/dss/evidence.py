"""SQL-only historical aggregates. No inventory, expiry or counterfactual labels exist."""
import re


WARNINGS = [
    'Tồn kho, năng lực, hạn dùng còn lại và độ trễ tăng thêm là đầu vào kịch bản, chưa được xác minh.',
    'Điểm rủi ro là chỉ số ưu tiên quy tắc, không phải xác suất giao thất bại hay hư hỏng đã hiệu chuẩn.',
    'Shopee dùng thời gian hoàn thành làm proxy giao nhận. TikTok dùng Delivered Time. Chỉ so trong cùng shop.',
    'Trạng thái là snapshot hiện tại. Lọc as_of không tái tạo trạng thái lịch sử khi thiếu ngày hủy.',
    'Quan hệ kho-tỉnh là quan sát. Thay kho không được chứng minh gây cải thiện kết quả.',
    'Dữ liệu thời gian chỉ gồm đơn có ghi nhận giao, có thiên lệch chọn mẫu và censoring.',
]


def breakfast_candidate(name):
    # Product-family cue only. This does not prove freshness, expiry or a short shelf life.
    return bool(re.search(r'\b(hura|breakfast)\b|bữa sáng|ăn sáng', name.casefold()))


def breakfast_hn_default(name):
    """Explicit breakfast names only. Hura brand alone does not prove breakfast policy."""
    return bool(re.search(r'\bbreakfast\b|bữa sáng|ăn sáng', name.casefold()))


def context(connection, request):
    store = connection.execute('SELECT storefront_key FROM dw.dim_storefront WHERE storefront_code=%s', (request.store,)).fetchone()
    if not store:
        raise ValueError('Unknown storefront')
    warehouses = connection.execute('''SELECT warehouse_key,warehouse_region FROM dw.dim_warehouse
        WHERE storefront_key=%s AND warehouse_region IN ('Hà Nội','Hồ Chí Minh') ORDER BY warehouse_key''', (store['storefront_key'],)).fetchall()
    product_keys = sorted({i.product_key for o in request.orders for i in o.items})
    rows = connection.execute('''SELECT source_product_sku_key product_key,product_name,canonical_category
        FROM dw.dim_source_product_sku WHERE storefront_key=%s AND source_product_sku_key=ANY(%s)''', (store['storefront_key'], product_keys)).fetchall()
    products = {r['product_key']: {**r, 'breakfast_candidate': breakfast_candidate(r['product_name'] or ''),
                'breakfast_hn_default': breakfast_hn_default(r['product_name'] or '')} for r in rows}
    if set(products) != set(product_keys):
        raise ValueError('Every product must belong to the requested storefront')
    observed = connection.execute('''SELECT DISTINCT i.warehouse_key,i.product_key FROM analytics.v_items i
      JOIN analytics.v_orders o USING(order_key) WHERE o.storefront_key=%s AND o.order_date<=%s
      AND i.product_key=ANY(%s)''', (store['storefront_key'], request.as_of, product_keys)).fetchall()
    return {'warehouses': warehouses, 'products': products,
            'observed_pairs': {(r['warehouse_key'], r['product_key']) for r in observed}}


def profiles(connection, store, as_of, history_start, late_days, low_star_max=2):
    # Timing events must be observed by cutoff. Cancellation is a snapshot rate, labeled as such.
    rows = connection.execute('''WITH routes AS (
      SELECT r.*,CASE WHEN delivered_at::date<=%(cutoff)s THEN lead_days END observed_lead,
        CASE WHEN (canonical_status='CANCELED' AND canceled_at::date>%(cutoff)s)
               OR (canonical_status IN('COMPLETED','DELIVERED') AND delivered_at::date>%(cutoff)s)
             THEN 'UNKNOWN' ELSE canonical_status END scoring_status
      FROM dss.v_route_orders r WHERE storefront_code=%(store)s AND order_date<=%(cutoff)s
        AND (%(start)s::date IS NULL OR order_date>=%(start)s::date)
    ), review_locations AS (
      SELECT r.review_key,r.order_key,r.star_level,min(i.warehouse_key) warehouse_key,
        count(DISTINCT i.warehouse_key) candidate_warehouses
      FROM analytics.v_reviews r JOIN (SELECT DISTINCT order_key FROM routes) cohort USING(order_key)
      LEFT JOIN analytics.v_items i ON i.order_key=r.order_key AND (r.product_key IS NULL OR i.product_key=r.product_key)
        AND i.canonical_category IN ('Bánh','Kẹo','Ngũ cốc')
      WHERE r.review_date<=%(cutoff)s GROUP BY r.review_key,r.order_key,r.star_level
    ), reviews AS (
      SELECT warehouse_key,order_key,count(*) reviews,
        count(*) FILTER(WHERE star_level<=%(low_star)s) low_reviews,
        count(*) FILTER(WHERE star_level=1) one_star_reviews
      FROM review_locations WHERE candidate_warehouses=1 GROUP BY 1,2
    ), ambiguous AS (
      SELECT order_key,count(*) unattributed_reviews FROM review_locations WHERE candidate_warehouses<>1 GROUP BY 1
    ) SELECT warehouse_key,route_province,GROUPING(warehouse_key,route_province) grouping_level,
      count(*) orders,count(*) FILTER(WHERE scoring_status IN('COMPLETED','DELIVERED','CANCELED','RETURNED')) resolved_orders,
      count(*) FILTER(WHERE scoring_status='CANCELED') canceled_orders,
      count(*) FILTER(WHERE scoring_status='CANCELED' AND canceled_at IS NULL) canceled_without_timestamp,
      count(*) FILTER(WHERE scoring_status<>canonical_status) known_future_outcomes_excluded,
      count(observed_lead) timing_samples,
      count(*) FILTER(WHERE observed_lead>%(late)s) late_orders,
      avg(observed_lead) mean_lead_days,
      percentile_cont(.5) WITHIN GROUP(ORDER BY observed_lead) median_lead_days,
      percentile_cont(.9) WITHIN GROUP(ORDER BY observed_lead) p90_lead_days,
      count(*) FILTER(WHERE shipped_at<created_at OR delivered_at<shipped_at) invalid_chronology_orders,
      coalesce(sum(reviews.reviews),0) reviews,coalesce(sum(reviews.low_reviews),0) low_reviews,
      coalesce(sum(reviews.one_star_reviews),0) one_star_reviews,
      count(*) FILTER(WHERE reviews.reviews>0) reviewed_orders,
      coalesce(sum(ambiguous.unattributed_reviews),0) unattributed_reviews
    FROM routes LEFT JOIN reviews USING(order_key,warehouse_key) LEFT JOIN ambiguous USING(order_key)
    GROUP BY GROUPING SETS((warehouse_key,route_province),(warehouse_key))
    ORDER BY warehouse_key,grouping_level,route_province''',
      {'store': store, 'cutoff': as_of, 'start': history_start, 'late': late_days, 'low_star':low_star_max}).fetchall()
    # No global rollup across warehouses: a multi-warehouse order can belong to both.
    return {(r['warehouse_key'], r['route_province']): {**r,'low_star_max':low_star_max} for r in rows}


def choose_profile(profiles_by_route, warehouse_key, province, min_samples):
    exact = profiles_by_route.get((warehouse_key, province))
    if exact and exact['timing_samples'] >= min_samples:
        return {**exact, 'evidence_level': 'WAREHOUSE_PROVINCE'}
    fallback = profiles_by_route.get((warehouse_key, None))
    if fallback and fallback['timing_samples'] >= min_samples:
        return {**fallback, 'evidence_level': 'WAREHOUSE_ALL_PROVINCES',
                'requested_route_samples': exact['timing_samples'] if exact else 0}
    return None


def shelf_observations(connection, store, as_of, warehouse_key, province, threshold_days, fallback):
    return connection.execute('''SELECT count(*) samples,count(*) FILTER(WHERE lead_days>%(threshold)s) exceedances
      FROM dss.v_route_orders WHERE storefront_code=%(store)s AND warehouse_key=%(warehouse)s
        AND (%(fallback)s OR route_province=%(province)s) AND delivered_at::date<=%(cutoff)s
        AND order_date<=%(cutoff)s AND lead_days IS NOT NULL''',
      {'threshold': threshold_days, 'store': store, 'warehouse': warehouse_key, 'fallback': fallback,
       'province': province, 'cutoff': as_of}).fetchone()
