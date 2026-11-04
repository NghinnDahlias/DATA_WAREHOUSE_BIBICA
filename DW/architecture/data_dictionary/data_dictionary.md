# Data dictionary từ PostgreSQL hiện thực

04/11/2026: 15tables, 56FK. Grain và semantics xem architecture_overview.md/measure_catalog.md.

## dw.dim_category

| Cột | Kiểu SQL | NULL |
|---|---|---|
| category_key | smallint | NO |
| canonical_category | text | NO |
| priority | smallint | NO |

Ràng buộc:

- `dim_category_canonical_category_check`: `CHECK ((canonical_category = ANY (ARRAY['Quà tặng'::text, 'Bánh'::text, 'Kẹo'::text, 'Ngũ cốc'::text])))`
- `dim_category_canonical_category_key`: `UNIQUE (canonical_category)`
- `dim_category_pkey`: `PRIMARY KEY (category_key)`
- `dim_category_priority_check`: `CHECK (((priority >= 1) AND (priority <= 4)))`
- `dim_category_priority_key`: `UNIQUE (priority)`

## dw.dim_channel

| Cột | Kiểu SQL | NULL |
|---|---|---|
| channel_key | bigint | NO |
| channel_code | text | NO |
| channel_name | text | NO |
| created_at | timestamp with time zone | NO |

Ràng buộc:

- `ck_dim_channel_code_nonblank`: `CHECK ((btrim(channel_code) <> ''::text))`
- `ck_dim_channel_name_nonblank`: `CHECK ((btrim(channel_name) <> ''::text))`
- `dim_channel_channel_code_key`: `UNIQUE (channel_code)`
- `dim_channel_pkey`: `PRIMARY KEY (channel_key)`

## dw.dim_date

| Cột | Kiểu SQL | NULL |
|---|---|---|
| date_key | integer | NO |
| calendar_date | date | NO |
| year | smallint | NO |
| quarter | smallint | NO |
| month | smallint | NO |
| day | smallint | NO |
| month_name | text | NO |
| week_of_year | smallint | NO |

Ràng buộc:

- `ck_dim_date_day`: `CHECK (((day >= 1) AND (day <= 31)))`
- `ck_dim_date_key_positive`: `CHECK ((date_key > 0))`
- `ck_dim_date_month`: `CHECK (((month >= 1) AND (month <= 12)))`
- `ck_dim_date_quarter`: `CHECK (((quarter >= 1) AND (quarter <= 4)))`
- `ck_dim_date_week`: `CHECK (((week_of_year >= 1) AND (week_of_year <= 53)))`
- `dim_date_calendar_date_key`: `UNIQUE (calendar_date)`
- `dim_date_pkey`: `PRIMARY KEY (date_key)`

## dw.dim_ingestion_batch

| Cột | Kiểu SQL | NULL |
|---|---|---|
| ingestion_batch_key | bigint | NO |
| source_file_key | bigint | NO |
| batch_id | text | NO |
| started_at | timestamp with time zone | NO |
| completed_at | timestamp with time zone | YES |
| load_status | text | NO |
| row_count_read | integer | YES |
| row_count_loaded | integer | YES |
| created_at | timestamp with time zone | NO |

Ràng buộc:

- `ck_dim_ingestion_batch_counts`: `CHECK ((((row_count_read IS NULL) OR (row_count_read >= 0)) AND ((row_count_loaded IS NULL) OR (row_count_loaded >= 0))))`
- `ck_dim_ingestion_batch_dates`: `CHECK (((completed_at IS NULL) OR (completed_at >= started_at)))`
- `ck_dim_ingestion_batch_status`: `CHECK ((load_status = ANY (ARRAY['STARTED'::text, 'LOADED'::text, 'FAILED'::text, 'REPLAYED'::text])))`
- `dim_ingestion_batch_batch_id_key`: `UNIQUE (batch_id)`
- `dim_ingestion_batch_pkey`: `PRIMARY KEY (ingestion_batch_key)`
- `fk_dim_ingestion_batch_source_file`: `FOREIGN KEY (source_file_key) REFERENCES dw.dim_source_file(source_file_key)`

## dw.dim_order_identity

| Cột | Kiểu SQL | NULL |
|---|---|---|
| order_key | bigint | NO |
| channel_key | bigint | NO |
| storefront_key | bigint | NO |
| native_order_id | text | NO |
| order_namespace | text | NO |
| created_at | timestamp with time zone | NO |

Ràng buộc:

- `ck_dim_order_identity_namespace_nonblank`: `CHECK ((btrim(order_namespace) <> ''::text))`
- `ck_dim_order_identity_native_nonblank`: `CHECK ((btrim(native_order_id) <> ''::text))`
- `dim_order_identity_order_namespace_key`: `UNIQUE (order_namespace)`
- `dim_order_identity_pkey`: `PRIMARY KEY (order_key)`
- `fk_dim_order_identity_channel`: `FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key)`
- `fk_dim_order_identity_storefront_scope`: `FOREIGN KEY (storefront_key, channel_key) REFERENCES dw.dim_storefront(storefront_key, channel_key)`
- `uq_dim_order_identity_key_scope`: `UNIQUE (order_key, channel_key, storefront_key)`
- `uq_dim_order_identity_native`: `UNIQUE (channel_key, storefront_key, native_order_id)`

## dw.dim_order_status

| Cột | Kiểu SQL | NULL |
|---|---|---|
| order_status_key | bigint | NO |
| channel_key | bigint | NO |
| storefront_key | bigint | NO |
| native_status | text | NO |
| reviewed_status | text | YES |
| mapping_version | text | YES |
| source_timezone | text | YES |
| effective_from | date | YES |
| effective_to | date | YES |
| created_at | timestamp with time zone | NO |

Ràng buộc:

- `ck_dim_order_status_dates`: `CHECK (((effective_to IS NULL) OR (effective_from IS NULL) OR (effective_to >= effective_from)))`
- `ck_dim_order_status_native_nonblank`: `CHECK ((btrim(native_status) <> ''::text))`
- `dim_order_status_pkey`: `PRIMARY KEY (order_status_key)`
- `fk_dim_order_status_channel`: `FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key)`
- `fk_dim_order_status_storefront_scope`: `FOREIGN KEY (storefront_key, channel_key) REFERENCES dw.dim_storefront(storefront_key, channel_key)`
- `uq_dim_order_status_key_scope`: `UNIQUE (order_status_key, channel_key, storefront_key)`

## dw.dim_province

| Cột | Kiểu SQL | NULL |
|---|---|---|
| province_key | bigint | NO |
| native_province_name | text | NO |
| normalized_province_name | text | YES |
| mapping_status | text | NO |
| mapping_version | text | YES |
| created_at | timestamp with time zone | NO |

Ràng buộc:

- `ck_dim_province_mapping_status`: `CHECK ((mapping_status = ANY (ARRAY['UNMAPPED'::text, 'PROVISIONAL'::text, 'VALIDATED'::text, 'REJECTED'::text])))`
- `ck_dim_province_name_nonblank`: `CHECK ((btrim(native_province_name) <> ''::text))`
- `dim_province_pkey`: `PRIMARY KEY (province_key)`
- `uq_dim_province_native`: `UNIQUE (native_province_name)`

## dw.dim_source_file

| Cột | Kiểu SQL | NULL |
|---|---|---|
| source_file_key | bigint | NO |
| source_file_name | text | NO |
| source_sha256 | text | NO |
| sheet_name | text | NO |
| source_kind | text | NO |
| source_storefront | text | NO |
| created_at | timestamp with time zone | NO |

Ràng buộc:

- `ck_dim_source_file_kind`: `CHECK ((source_kind = ANY (ARRAY['tiktok_sales'::text, 'tiktok_reviews'::text, 'shopee_orders'::text])))`
- `ck_dim_source_file_names_nonblank`: `CHECK (((btrim(source_file_name) <> ''::text) AND (btrim(sheet_name) <> ''::text) AND (btrim(source_storefront) <> ''::text)))`
- `ck_dim_source_file_sha256`: `CHECK ((source_sha256 ~ '^[0-9a-fA-F]{64}$'::text))`
- `dim_source_file_pkey`: `PRIMARY KEY (source_file_key)`
- `uq_dim_source_file_identity`: `UNIQUE (source_file_name, source_sha256, sheet_name)`

## dw.dim_source_product_sku

| Cột | Kiểu SQL | NULL |
|---|---|---|
| source_product_sku_key | bigint | NO |
| channel_key | bigint | NO |
| storefront_key | bigint | NO |
| native_product_id | text | YES |
| native_sku_id | text | YES |
| seller_sku | text | YES |
| product_name | text | YES |
| variation_name | text | YES |
| product_line | text | YES |
| conformed_product_key | text | YES |
| mapping_status | text | NO |
| mapping_version | text | YES |
| created_at | timestamp with time zone | NO |
| product_nk | text | YES |
| normalized_name | text | YES |
| category_key | smallint | YES |
| canonical_category | text | YES |
| category_original | text | YES |
| category_rule | text | YES |
| category_mapping_status | text | NO |

Ràng buộc:

- `ck_dim_source_product_sku_mapping_status`: `CHECK ((mapping_status = ANY (ARRAY['UNMAPPED'::text, 'PROVISIONAL'::text, 'VALIDATED'::text, 'REJECTED'::text])))`
- `dim_source_product_sku_category_key_fkey`: `FOREIGN KEY (category_key) REFERENCES dw.dim_category(category_key)`
- `dim_source_product_sku_pkey`: `PRIMARY KEY (source_product_sku_key)`
- `fk_dim_source_product_sku_channel`: `FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key)`
- `fk_dim_source_product_sku_storefront_scope`: `FOREIGN KEY (storefront_key, channel_key) REFERENCES dw.dim_storefront(storefront_key, channel_key)`
- `uq_dim_source_product_sku_key_scope`: `UNIQUE (source_product_sku_key, channel_key, storefront_key)`

## dw.dim_storefront

| Cột | Kiểu SQL | NULL |
|---|---|---|
| storefront_key | bigint | NO |
| channel_key | bigint | NO |
| storefront_code | text | NO |
| storefront_name | text | NO |
| product_line | text | YES |
| created_at | timestamp with time zone | NO |

Ràng buộc:

- `ck_dim_storefront_code_nonblank`: `CHECK ((btrim(storefront_code) <> ''::text))`
- `ck_dim_storefront_name_nonblank`: `CHECK ((btrim(storefront_name) <> ''::text))`
- `dim_storefront_pkey`: `PRIMARY KEY (storefront_key)`
- `dim_storefront_storefront_code_key`: `UNIQUE (storefront_code)`
- `fk_dim_storefront_channel`: `FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key)`
- `uq_dim_storefront_channel_code`: `UNIQUE (channel_key, storefront_code)`
- `uq_dim_storefront_key_channel`: `UNIQUE (storefront_key, channel_key)`

## dw.dim_time

| Cột | Kiểu SQL | NULL |
|---|---|---|
| time_key | integer | NO |
| native_time | time without time zone | NO |
| hour | smallint | NO |
| minute | smallint | NO |
| second | smallint | NO |

Ràng buộc:

- `ck_dim_time_hour`: `CHECK (((hour >= 0) AND (hour <= 23)))`
- `ck_dim_time_key_nonnegative`: `CHECK ((time_key >= 0))`
- `ck_dim_time_minute`: `CHECK (((minute >= 0) AND (minute <= 59)))`
- `ck_dim_time_second`: `CHECK (((second >= 0) AND (second <= 59)))`
- `dim_time_native_time_key`: `UNIQUE (native_time)`
- `dim_time_pkey`: `PRIMARY KEY (time_key)`

## dw.dim_warehouse

| Cột | Kiểu SQL | NULL |
|---|---|---|
| warehouse_key | bigint | NO |
| storefront_key | bigint | NO |
| native_warehouse_name | text | NO |
| normalized_warehouse_name | text | YES |
| mapping_status | text | NO |
| mapping_version | text | YES |
| created_at | timestamp with time zone | NO |
| warehouse_region | text | NO |

Ràng buộc:

- `ck_dim_warehouse_mapping_status`: `CHECK ((mapping_status = ANY (ARRAY['UNMAPPED'::text, 'PROVISIONAL'::text, 'VALIDATED'::text, 'REJECTED'::text])))`
- `ck_dim_warehouse_name_nonblank`: `CHECK ((btrim(native_warehouse_name) <> ''::text))`
- `dim_warehouse_pkey`: `PRIMARY KEY (warehouse_key)`
- `fk_dim_warehouse_storefront`: `FOREIGN KEY (storefront_key) REFERENCES dw.dim_storefront(storefront_key)`
- `uq_dim_warehouse_native`: `UNIQUE (storefront_key, native_warehouse_name)`
- `warehouse_store_scope_unique`: `UNIQUE (warehouse_key, storefront_key)`

## dw.fact_order_lifecycle_candidate

| Cột | Kiểu SQL | NULL |
|---|---|---|
| order_lifecycle_key | bigint | NO |
| order_key | bigint | NO |
| channel_key | bigint | NO |
| storefront_key | bigint | NO |
| order_status_key | bigint | YES |
| warehouse_key | bigint | YES |
| province_key | bigint | YES |
| created_date_key | integer | NO |
| created_time_key | integer | YES |
| paid_date_key | integer | YES |
| paid_time_key | integer | YES |
| shipped_date_key | integer | YES |
| shipped_time_key | integer | YES |
| delivered_date_key | integer | YES |
| delivered_time_key | integer | YES |
| cancelled_date_key | integer | YES |
| cancelled_time_key | integer | YES |
| source_file_key | bigint | NO |
| ingestion_batch_key | bigint | NO |
| order_row_count | integer | NO |
| order_amount_source | numeric(19,4) | YES |
| buyer_payment_source_1 | numeric(19,4) | YES |
| buyer_payment_source_2 | numeric(19,4) | YES |
| refund_amount_source | numeric(19,4) | YES |
| reconciliation_status | text | NO |
| loaded_at | timestamp with time zone | NO |

Ràng buộc:

- `ck_fact_lifecycle_reconciliation_status`: `CHECK ((reconciliation_status = ANY (ARRAY['CONSTANT'::text, 'CONFLICTING'::text, 'MISSING'::text, 'REVIEW_REQUIRED'::text])))`
- `ck_fact_lifecycle_row_count`: `CHECK ((order_row_count > 0))`
- `fact_order_lifecycle_candidate_order_key_key`: `UNIQUE (order_key)`
- `fact_order_lifecycle_candidate_pkey`: `PRIMARY KEY (order_lifecycle_key)`
- `fk_fact_lifecycle_batch`: `FOREIGN KEY (ingestion_batch_key) REFERENCES dw.dim_ingestion_batch(ingestion_batch_key)`
- `fk_fact_lifecycle_cancelled_date`: `FOREIGN KEY (cancelled_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_lifecycle_cancelled_time`: `FOREIGN KEY (cancelled_time_key) REFERENCES dw.dim_time(time_key)`
- `fk_fact_lifecycle_channel`: `FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key)`
- `fk_fact_lifecycle_created_date`: `FOREIGN KEY (created_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_lifecycle_created_time`: `FOREIGN KEY (created_time_key) REFERENCES dw.dim_time(time_key)`
- `fk_fact_lifecycle_delivered_date`: `FOREIGN KEY (delivered_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_lifecycle_delivered_time`: `FOREIGN KEY (delivered_time_key) REFERENCES dw.dim_time(time_key)`
- `fk_fact_lifecycle_order_scope`: `FOREIGN KEY (order_key, channel_key, storefront_key) REFERENCES dw.dim_order_identity(order_key, channel_key, storefront_key)`
- `fk_fact_lifecycle_paid_date`: `FOREIGN KEY (paid_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_lifecycle_paid_time`: `FOREIGN KEY (paid_time_key) REFERENCES dw.dim_time(time_key)`
- `fk_fact_lifecycle_province`: `FOREIGN KEY (province_key) REFERENCES dw.dim_province(province_key)`
- `fk_fact_lifecycle_shipped_date`: `FOREIGN KEY (shipped_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_lifecycle_shipped_time`: `FOREIGN KEY (shipped_time_key) REFERENCES dw.dim_time(time_key)`
- `fk_fact_lifecycle_source_file`: `FOREIGN KEY (source_file_key) REFERENCES dw.dim_source_file(source_file_key)`
- `fk_fact_lifecycle_status_scope`: `FOREIGN KEY (order_status_key, channel_key, storefront_key) REFERENCES dw.dim_order_status(order_status_key, channel_key, storefront_key)`
- `fk_fact_lifecycle_storefront_scope`: `FOREIGN KEY (storefront_key, channel_key) REFERENCES dw.dim_storefront(storefront_key, channel_key)`
- `fk_fact_lifecycle_warehouse`: `FOREIGN KEY (warehouse_key) REFERENCES dw.dim_warehouse(warehouse_key)`
- `lifecycle_warehouse_scope_fk`: `FOREIGN KEY (warehouse_key, storefront_key) REFERENCES dw.dim_warehouse(warehouse_key, storefront_key)`

## dw.fact_order_line_candidate

| Cột | Kiểu SQL | NULL |
|---|---|---|
| order_line_key | bigint | NO |
| order_key | bigint | NO |
| channel_key | bigint | NO |
| storefront_key | bigint | NO |
| source_product_sku_key | bigint | YES |
| warehouse_key | bigint | YES |
| province_key | bigint | YES |
| order_status_key | bigint | YES |
| order_created_date_key | integer | NO |
| order_created_time_key | integer | YES |
| paid_date_key | integer | YES |
| paid_time_key | integer | YES |
| shipped_date_key | integer | YES |
| shipped_time_key | integer | YES |
| delivered_date_key | integer | YES |
| delivered_time_key | integer | YES |
| source_file_key | bigint | NO |
| ingestion_batch_key | bigint | NO |
| source_sheet_name | text | NO |
| physical_row_number | integer | NO |
| source_row_hash | text | NO |
| quantity | numeric(18,4) | YES |
| returned_quantity | numeric(18,4) | YES |
| unit_price_source | numeric(19,4) | YES |
| gross_item_amount_source | numeric(19,4) | YES |
| net_item_amount_source | numeric(19,4) | YES |
| seller_discount_source | numeric(19,4) | YES |
| platform_discount_source | numeric(19,4) | YES |
| shipping_buyer_charge_source | numeric(19,4) | YES |
| order_amount_source | numeric(19,4) | YES |
| source_row_quality_status | text | NO |
| loaded_at | timestamp with time zone | NO |
| source_code | text | YES |
| category_key | smallint | YES |
| category_mapping_status | text | NO |

Ràng buộc:

- `ck_fact_order_line_quality_status`: `CHECK ((source_row_quality_status = ANY (ARRAY['ACCEPTED'::text, 'FLAGGED'::text, 'REJECTED_BY_CONTRACT'::text])))`
- `ck_fact_order_line_quantity`: `CHECK (((quantity IS NULL) OR (quantity >= (0)::numeric)))`
- `ck_fact_order_line_returned_quantity`: `CHECK (((returned_quantity IS NULL) OR (returned_quantity >= (0)::numeric)))`
- `ck_fact_order_line_row_number`: `CHECK ((physical_row_number > 0))`
- `ck_fact_order_line_source_hash`: `CHECK ((source_row_hash ~ '^[0-9a-fA-F]{64}$'::text))`
- `fact_order_line_candidate_category_key_fkey`: `FOREIGN KEY (category_key) REFERENCES dw.dim_category(category_key)`
- `fact_order_line_candidate_pkey`: `PRIMARY KEY (order_line_key)`
- `fk_fact_order_line_batch`: `FOREIGN KEY (ingestion_batch_key) REFERENCES dw.dim_ingestion_batch(ingestion_batch_key)`
- `fk_fact_order_line_channel`: `FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key)`
- `fk_fact_order_line_created_date`: `FOREIGN KEY (order_created_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_order_line_created_time`: `FOREIGN KEY (order_created_time_key) REFERENCES dw.dim_time(time_key)`
- `fk_fact_order_line_delivered_date`: `FOREIGN KEY (delivered_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_order_line_delivered_time`: `FOREIGN KEY (delivered_time_key) REFERENCES dw.dim_time(time_key)`
- `fk_fact_order_line_order_scope`: `FOREIGN KEY (order_key, channel_key, storefront_key) REFERENCES dw.dim_order_identity(order_key, channel_key, storefront_key)`
- `fk_fact_order_line_paid_date`: `FOREIGN KEY (paid_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_order_line_paid_time`: `FOREIGN KEY (paid_time_key) REFERENCES dw.dim_time(time_key)`
- `fk_fact_order_line_product_scope`: `FOREIGN KEY (source_product_sku_key, channel_key, storefront_key) REFERENCES dw.dim_source_product_sku(source_product_sku_key, channel_key, storefront_key)`
- `fk_fact_order_line_province`: `FOREIGN KEY (province_key) REFERENCES dw.dim_province(province_key)`
- `fk_fact_order_line_shipped_date`: `FOREIGN KEY (shipped_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_order_line_shipped_time`: `FOREIGN KEY (shipped_time_key) REFERENCES dw.dim_time(time_key)`
- `fk_fact_order_line_source_file`: `FOREIGN KEY (source_file_key) REFERENCES dw.dim_source_file(source_file_key)`
- `fk_fact_order_line_status_scope`: `FOREIGN KEY (order_status_key, channel_key, storefront_key) REFERENCES dw.dim_order_status(order_status_key, channel_key, storefront_key)`
- `fk_fact_order_line_storefront_scope`: `FOREIGN KEY (storefront_key, channel_key) REFERENCES dw.dim_storefront(storefront_key, channel_key)`
- `fk_fact_order_line_warehouse`: `FOREIGN KEY (warehouse_key) REFERENCES dw.dim_warehouse(warehouse_key)`
- `line_warehouse_scope_fk`: `FOREIGN KEY (warehouse_key, storefront_key) REFERENCES dw.dim_warehouse(warehouse_key, storefront_key)`
- `uq_fact_order_line_source_row`: `UNIQUE (source_file_key, source_sheet_name, physical_row_number)`

## dw.fact_review_candidate

| Cột | Kiểu SQL | NULL |
|---|---|---|
| review_key | bigint | NO |
| order_key | bigint | YES |
| channel_key | bigint | NO |
| storefront_key | bigint | NO |
| review_date_key | integer | NO |
| review_time_key | integer | YES |
| source_file_key | bigint | NO |
| ingestion_batch_key | bigint | NO |
| source_sheet_name | text | NO |
| physical_row_number | integer | NO |
| source_row_hash | text | NO |
| source_product_id | text | YES |
| source_product_sku_key | bigint | YES |
| star_level | smallint | NO |
| has_review_text | boolean | NO |
| review_text_length | integer | YES |
| product_linkage_status | text | NO |
| review_quality_status | text | NO |
| loaded_at | timestamp with time zone | NO |
| source_code | text | YES |
| match_confidence | text | NO |

Ràng buộc:

- `ck_fact_review_product_linkage`: `CHECK ((product_linkage_status = ANY (ARRAY['UNVERIFIED'::text, 'ORDER_ONLY'::text, 'VALIDATED'::text])))`
- `ck_fact_review_quality_status`: `CHECK ((review_quality_status = ANY (ARRAY['ACCEPTED'::text, 'FLAGGED'::text, 'RESTRICTED'::text])))`
- `ck_fact_review_row_number`: `CHECK ((physical_row_number > 0))`
- `ck_fact_review_source_hash`: `CHECK ((source_row_hash ~ '^[0-9a-fA-F]{64}$'::text))`
- `ck_fact_review_star_level`: `CHECK (((star_level >= 1) AND (star_level <= 5)))`
- `ck_fact_review_text_length`: `CHECK (((review_text_length IS NULL) OR (review_text_length >= 0)))`
- `ck_fact_review_text_presence`: `CHECK (((has_review_text AND (review_text_length IS NOT NULL) AND (review_text_length > 0)) OR ((NOT has_review_text) AND ((review_text_length IS NULL) OR (review_text_length = 0)))))`
- `fact_review_candidate_pkey`: `PRIMARY KEY (review_key)`
- `fk_fact_review_batch`: `FOREIGN KEY (ingestion_batch_key) REFERENCES dw.dim_ingestion_batch(ingestion_batch_key)`
- `fk_fact_review_channel`: `FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key)`
- `fk_fact_review_date`: `FOREIGN KEY (review_date_key) REFERENCES dw.dim_date(date_key)`
- `fk_fact_review_order_scope`: `FOREIGN KEY (order_key, channel_key, storefront_key) REFERENCES dw.dim_order_identity(order_key, channel_key, storefront_key)`
- `fk_fact_review_product_scope`: `FOREIGN KEY (source_product_sku_key, channel_key, storefront_key) REFERENCES dw.dim_source_product_sku(source_product_sku_key, channel_key, storefront_key)`
- `fk_fact_review_source_file`: `FOREIGN KEY (source_file_key) REFERENCES dw.dim_source_file(source_file_key)`
- `fk_fact_review_storefront_scope`: `FOREIGN KEY (storefront_key, channel_key) REFERENCES dw.dim_storefront(storefront_key, channel_key)`
- `fk_fact_review_time`: `FOREIGN KEY (review_time_key) REFERENCES dw.dim_time(time_key)`
- `uq_fact_review_source_row`: `UNIQUE (source_file_key, source_sheet_name, physical_row_number)`
