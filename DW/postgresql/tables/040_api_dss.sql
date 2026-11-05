-- Additive read models. No changes to Galaxy grain, keys or existing marts.
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS dss;

CREATE OR REPLACE VIEW analytics.v_orders AS
SELECT f.order_key, f.storefront_key, s.storefront_code, c.channel_code,
       CASE s.storefront_code WHEN 'bibica_tiktok_shop' THEN 'tiktok_bibica'
            WHEN 'bibica_official_store' THEN 'shopee_bibica'
            WHEN 'quasure_specialized_store' THEN 'shopee_quasure' END AS source_code,
       coalesce(st.reviewed_status, 'UNKNOWN') AS canonical_status,
       coalesce(p.normalized_province_name, 'Unknown') AS customer_province,
       d.calendar_date AS order_date,
       d.calendar_date + t.native_time AS created_at,
       sd.calendar_date + stm.native_time AS shipped_at,
       dd.calendar_date + dt.native_time AS delivered_at,
       cd.calendar_date + ct.native_time AS canceled_at,
       f.order_amount_source AS order_payable, f.refund_amount_source AS observed_refund,
       f.reconciliation_status, f.order_row_count
FROM dw.fact_order_lifecycle_candidate f
JOIN dw.dim_storefront s USING (storefront_key)
JOIN dw.dim_channel c ON c.channel_key = f.channel_key
LEFT JOIN dw.dim_order_status st ON st.order_status_key = f.order_status_key
LEFT JOIN dw.dim_province p ON p.province_key = f.province_key
JOIN dw.dim_date d ON d.date_key = f.created_date_key
LEFT JOIN dw.dim_time t ON t.time_key = f.created_time_key
LEFT JOIN dw.dim_date sd ON sd.date_key = f.shipped_date_key
LEFT JOIN dw.dim_time stm ON stm.time_key = f.shipped_time_key
LEFT JOIN dw.dim_date dd ON dd.date_key = f.delivered_date_key
LEFT JOIN dw.dim_time dt ON dt.time_key = f.delivered_time_key
LEFT JOIN dw.dim_date cd ON cd.date_key = f.cancelled_date_key
LEFT JOIN dw.dim_time ct ON ct.time_key = f.cancelled_time_key;

CREATE OR REPLACE VIEW analytics.v_items AS
SELECT f.order_line_key, f.order_key, f.source_code, f.storefront_key,
       f.source_product_sku_key AS product_key, p.product_name,
       f.category_key, cat.canonical_category, f.category_mapping_status,
       f.warehouse_key, w.warehouse_region, w.normalized_warehouse_name AS warehouse_name,
       coalesce(g.normalized_province_name, 'Unknown') AS customer_province,
       f.quantity, f.gross_item_amount_source AS gross_item_value,
       f.net_item_amount_source AS observed_item_payable,
       f.seller_discount_source AS seller_discount, f.returned_quantity
FROM dw.fact_order_line_candidate f
JOIN dw.dim_source_product_sku p USING (source_product_sku_key)
LEFT JOIN dw.dim_category cat ON cat.category_key = f.category_key
LEFT JOIN dw.dim_warehouse w ON w.warehouse_key = f.warehouse_key
LEFT JOIN dw.dim_province g ON g.province_key = f.province_key;

CREATE OR REPLACE VIEW analytics.v_reviews AS
SELECT r.review_key, r.order_key, r.source_product_sku_key AS product_key,
       d.calendar_date AS review_date, r.star_level, r.product_linkage_status
FROM dw.fact_review_candidate r
JOIN dw.dim_date d ON d.date_key = r.review_date_key;

-- One observation per scoped order/warehouse/customer province, never per SKU line.
-- An order shipped from multiple warehouses can appear in several route cohorts.
CREATE OR REPLACE VIEW dss.v_route_orders AS
SELECT o.*, x.warehouse_key, x.warehouse_region, x.route_province,
       CASE WHEN o.shipped_at >= o.created_at AND o.delivered_at >= o.shipped_at
            THEN extract(epoch FROM (o.delivered_at - o.shipped_at)) / 86400 END AS lead_days
FROM analytics.v_orders o
JOIN (SELECT order_key, warehouse_key, warehouse_region,
             CASE WHEN count(DISTINCT customer_province)=1 THEN min(customer_province)
                  ELSE 'Unknown' END AS route_province
      FROM analytics.v_items WHERE canonical_category IN ('Bánh','Kẹo','Ngũ cốc')
      GROUP BY order_key,warehouse_key,warehouse_region) x USING (order_key);

CREATE INDEX IF NOT EXISTS ix_phase2_line_order_product_warehouse
    ON dw.fact_order_line_candidate (order_key, source_product_sku_key, warehouse_key);
CREATE INDEX IF NOT EXISTS ix_phase2_review_order_date
    ON dw.fact_review_candidate (order_key, review_date_key);
