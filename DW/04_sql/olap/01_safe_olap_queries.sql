-- Bibica DW: safe OLAP queries.
-- Excludes paid revenue, net sales, GMV, and refund cash value.

-- Distinct scoped orders from the lifecycle grain.
SELECT
    f.channel_key,
    f.storefront_key,
    COUNT(*) AS order_count
FROM dw.fact_order_lifecycle_candidate AS f
WHERE f.reconciliation_status <> 'REVIEW_REQUIRED'
GROUP BY f.channel_key, f.storefront_key
ORDER BY f.channel_key, f.storefront_key;

-- Item units by month and storefront.
SELECT
    f.channel_key,
    f.storefront_key,
    d.year,
    d.month,
    SUM(f.quantity) AS item_units,
    SUM(f.returned_quantity) AS returned_units
FROM dw.fact_order_line_candidate AS f
JOIN dw.dim_date AS d ON d.date_key = f.order_created_date_key
GROUP BY f.channel_key, f.storefront_key, d.year, d.month
ORDER BY f.channel_key, f.storefront_key, d.year, d.month;

-- Item units by source SKU.
SELECT
    f.channel_key,
    f.storefront_key,
    f.source_product_sku_key,
    SUM(f.quantity) AS item_units,
    SUM(f.returned_quantity) AS returned_units
FROM dw.fact_order_line_candidate AS f
GROUP BY f.channel_key, f.storefront_key, f.source_product_sku_key
ORDER BY item_units DESC NULLS LAST;

-- TikTok rating count and 1-2-star rate by month.
SELECT
    r.storefront_key,
    d.year,
    d.month,
    COUNT(*) AS rating_count,
    COUNT(*) FILTER (WHERE r.star_level IN (1, 2)) AS low_star_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE r.star_level IN (1, 2))
        / NULLIF(COUNT(*), 0),
        2
    ) AS low_star_rate_pct,
    COUNT(*) FILTER (WHERE r.has_review_text) AS review_text_count
FROM dw.fact_review_candidate AS r
JOIN dw.dim_date AS d ON d.date_key = r.review_date_key
GROUP BY r.storefront_key, d.year, d.month
ORDER BY r.storefront_key, d.year, d.month;

-- Reconciliation quality distribution; diagnostic, not a financial KPI.
SELECT
    f.channel_key,
    f.storefront_key,
    f.reconciliation_status,
    COUNT(*) AS order_count
FROM dw.fact_order_lifecycle_candidate AS f
GROUP BY f.channel_key, f.storefront_key, f.reconciliation_status
ORDER BY f.channel_key, f.storefront_key, f.reconciliation_status;
