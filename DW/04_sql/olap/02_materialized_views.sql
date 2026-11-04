-- Bibica DW: source-safe OLAP materialized views.
-- Do not add order-level financial candidates to these marts.

CREATE SCHEMA IF NOT EXISTS mart;

DROP MATERIALIZED VIEW IF EXISTS mart.mv_order_counts_by_storefront;
CREATE MATERIALIZED VIEW mart.mv_order_counts_by_storefront AS
SELECT
    f.channel_key,
    c.channel_code,
    c.channel_name,
    f.storefront_key,
    s.storefront_code,
    s.storefront_name,
    COUNT(*) FILTER (
        WHERE f.reconciliation_status <> 'REVIEW_REQUIRED'
    ) AS order_count,
    COUNT(*) FILTER (
        WHERE f.reconciliation_status = 'REVIEW_REQUIRED'
    ) AS review_required_order_count
FROM dw.fact_order_lifecycle_candidate AS f
JOIN dw.dim_channel AS c ON c.channel_key = f.channel_key
JOIN dw.dim_storefront AS s ON s.storefront_key = f.storefront_key
GROUP BY
    f.channel_key, c.channel_code, c.channel_name,
    f.storefront_key, s.storefront_code, s.storefront_name;

CREATE UNIQUE INDEX ux_mv_order_counts_by_storefront
    ON mart.mv_order_counts_by_storefront (channel_key, storefront_key);

DROP MATERIALIZED VIEW IF EXISTS mart.mv_item_units_monthly;
CREATE MATERIALIZED VIEW mart.mv_item_units_monthly AS
SELECT
    f.channel_key,
    c.channel_code,
    f.storefront_key,
    s.storefront_code,
    s.storefront_name,
    d.year,
    d.month,
    COALESCE(SUM(f.quantity), 0) AS item_units,
    COALESCE(SUM(f.returned_quantity), 0) AS returned_units,
    COUNT(*) AS source_line_count
FROM dw.fact_order_line_candidate AS f
JOIN dw.dim_channel AS c ON c.channel_key = f.channel_key
JOIN dw.dim_storefront AS s ON s.storefront_key = f.storefront_key
JOIN dw.dim_date AS d ON d.date_key = f.order_created_date_key
GROUP BY
    f.channel_key, c.channel_code,
    f.storefront_key, s.storefront_code, s.storefront_name,
    d.year, d.month;

CREATE UNIQUE INDEX ux_mv_item_units_monthly
    ON mart.mv_item_units_monthly (channel_key, storefront_key, year, month);

DROP MATERIALIZED VIEW IF EXISTS mart.mv_tiktok_ratings_monthly;
CREATE MATERIALIZED VIEW mart.mv_tiktok_ratings_monthly AS
SELECT
    r.storefront_key,
    s.storefront_code,
    s.storefront_name,
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
JOIN dw.dim_storefront AS s ON s.storefront_key = r.storefront_key
JOIN dw.dim_date AS d ON d.date_key = r.review_date_key
GROUP BY
    r.storefront_key, s.storefront_code, s.storefront_name,
    d.year, d.month;

CREATE UNIQUE INDEX ux_mv_tiktok_ratings_monthly
    ON mart.mv_tiktok_ratings_monthly (storefront_key, year, month);

-- Refresh after an approved incremental ETL load:
-- REFRESH MATERIALIZED VIEW mart.mv_order_counts_by_storefront;
-- REFRESH MATERIALIZED VIEW mart.mv_item_units_monthly;
-- REFRESH MATERIALIZED VIEW mart.mv_tiktok_ratings_monthly;
