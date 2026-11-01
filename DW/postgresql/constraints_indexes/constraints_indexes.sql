BEGIN;

CREATE INDEX IF NOT EXISTS ix_dim_storefront_channel
    ON dw.dim_storefront (channel_key);
CREATE INDEX IF NOT EXISTS ix_dim_order_identity_storefront
    ON dw.dim_order_identity (storefront_key, native_order_id);
CREATE INDEX IF NOT EXISTS ix_dim_source_product_sku_storefront
    ON dw.dim_source_product_sku (storefront_key, native_sku_id);
CREATE INDEX IF NOT EXISTS ix_dim_source_product_sku_mapping
    ON dw.dim_source_product_sku (mapping_status, conformed_product_key);
CREATE INDEX IF NOT EXISTS ix_dim_warehouse_storefront
    ON dw.dim_warehouse (storefront_key, normalized_warehouse_name);
CREATE INDEX IF NOT EXISTS ix_dim_province_normalized
    ON dw.dim_province (normalized_province_name);
CREATE INDEX IF NOT EXISTS ix_dim_order_status_scope
    ON dw.dim_order_status (channel_key, storefront_key, native_status, mapping_version);
CREATE INDEX IF NOT EXISTS ix_dim_source_file_sha
    ON dw.dim_source_file (source_sha256);
CREATE INDEX IF NOT EXISTS ix_dim_ingestion_batch_file_status
    ON dw.dim_ingestion_batch (source_file_key, load_status, started_at);

CREATE INDEX IF NOT EXISTS ix_fact_order_line_order
    ON dw.fact_order_line_candidate (order_key);
CREATE INDEX IF NOT EXISTS ix_fact_order_line_storefront_date
    ON dw.fact_order_line_candidate (storefront_key, order_created_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_order_line_product
    ON dw.fact_order_line_candidate (source_product_sku_key);
CREATE INDEX IF NOT EXISTS ix_fact_order_line_warehouse_province
    ON dw.fact_order_line_candidate (warehouse_key, province_key);
CREATE INDEX IF NOT EXISTS ix_fact_order_line_status
    ON dw.fact_order_line_candidate (order_status_key);
CREATE INDEX IF NOT EXISTS ix_fact_order_line_batch
    ON dw.fact_order_line_candidate (ingestion_batch_key, source_file_key);

CREATE INDEX IF NOT EXISTS ix_fact_lifecycle_storefront_date
    ON dw.fact_order_lifecycle_candidate (storefront_key, created_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_lifecycle_status
    ON dw.fact_order_lifecycle_candidate (order_status_key, reconciliation_status);
CREATE INDEX IF NOT EXISTS ix_fact_lifecycle_batch
    ON dw.fact_order_lifecycle_candidate (ingestion_batch_key, source_file_key);

CREATE INDEX IF NOT EXISTS ix_fact_review_storefront_date
    ON dw.fact_review_candidate (storefront_key, review_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_review_order
    ON dw.fact_review_candidate (order_key);
CREATE INDEX IF NOT EXISTS ix_fact_review_rating
    ON dw.fact_review_candidate (star_level, product_linkage_status);
CREATE INDEX IF NOT EXISTS ix_fact_review_batch
    ON dw.fact_review_candidate (ingestion_batch_key, source_file_key);

COMMENT ON TABLE dw.fact_order_line_candidate IS
    'One physical non-empty sales-export row. Repeated order-SKU rows are retained; order-scoped amounts are non-additive here.';
COMMENT ON TABLE dw.fact_order_lifecycle_candidate IS
    'One storefront-scoped order after documented reconciliation. Not a blind GROUP BY of line rows.';
COMMENT ON TABLE dw.fact_review_candidate IS
    'One rating export row. Review text is excluded; product linkage is restricted until validated.';

COMMIT;
