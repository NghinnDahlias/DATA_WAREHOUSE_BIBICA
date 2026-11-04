\set ON_ERROR_STOP on
\pset pager off

-- No restricted financial columns in approved marts.
SELECT table_schema, table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'mart'
  AND table_name IN (
      'mv_order_counts_by_storefront',
      'mv_item_units_monthly',
      'mv_tiktok_ratings_monthly'
  )
  AND column_name IN (
      'order_amount_source',
      'buyer_payment_source_1',
      'buyer_payment_source_2',
      'refund_amount_source',
      'net_sales',
      'paid_revenue'
  );

SELECT COUNT(*) AS violations
FROM mart.mv_item_units_monthly
WHERE item_units < 0 OR returned_units < 0;

SELECT COUNT(*) AS violations
FROM mart.mv_tiktok_ratings_monthly
WHERE low_star_rate_pct < 0 OR low_star_rate_pct > 100;

WITH fact_agg AS (
    SELECT
        f.channel_key,
        f.storefront_key,
        d.year,
        d.month,
        COALESCE(SUM(f.quantity), 0) AS item_units,
        COALESCE(SUM(f.returned_quantity), 0) AS returned_units
    FROM dw.fact_order_line_candidate AS f
    JOIN dw.dim_date AS d ON d.date_key = f.order_created_date_key
    GROUP BY f.channel_key, f.storefront_key, d.year, d.month
)
SELECT COUNT(*) AS violations
FROM fact_agg AS x
FULL OUTER JOIN mart.mv_item_units_monthly AS v
  ON v.channel_key = x.channel_key
 AND v.storefront_key = x.storefront_key
 AND v.year = x.year
 AND v.month = x.month
WHERE x.channel_key IS NULL
   OR v.channel_key IS NULL
   OR x.item_units IS DISTINCT FROM v.item_units
   OR x.returned_units IS DISTINCT FROM v.returned_units;

WITH fact_agg AS (
    SELECT
        channel_key,
        storefront_key,
        COUNT(*) AS order_count
    FROM dw.fact_order_lifecycle_candidate
    WHERE reconciliation_status <> 'REVIEW_REQUIRED'
    GROUP BY channel_key, storefront_key
)
SELECT COUNT(*) AS violations
FROM fact_agg AS x
FULL OUTER JOIN mart.mv_order_counts_by_storefront AS v
  ON v.channel_key = x.channel_key
 AND v.storefront_key = x.storefront_key
WHERE x.channel_key IS NULL
   OR v.channel_key IS NULL
   OR x.order_count IS DISTINCT FROM v.order_count;

SELECT schemaname, matviewname, ispopulated
FROM pg_matviews
WHERE schemaname = 'mart'
ORDER BY matviewname;
