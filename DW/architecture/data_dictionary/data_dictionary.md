# Bibica E-Commerce DW — Logical Data Dictionary

Status: **candidate / provisional**. Names and types are proposed for PostgreSQL implementation; unresolved business semantics are not silently converted into conformed KPIs.

## 1. Naming conventions

* `*_key`: warehouse surrogate key.
* `*_id`: source-native identifier or a stable logical identifier, stored as `text` unless explicitly stated otherwise.
* `*_date_key`: role-playing FK to `dim_date`.
* `*_time_key`: role-playing FK to `dim_time`.
* `*_source`: native/source-scoped measure whose accounting meaning is not yet conformed.
* `*_status`: lifecycle or quality state.

## 2. Shared dimensions

### 2.1 `dim_channel`

**Grain:** one sales channel.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `channel_key` | `bigint` | PK | no | Surrogate key |
| `channel_code` | `text` | UQ | no | `tiktok` or `shopee` |
| `channel_name` | `text` |  | no | Display name |

### 2.2 `dim_storefront`

**Grain:** one storefront within a channel.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `storefront_key` | `bigint` | PK | no | Surrogate key |
| `channel_key` | `bigint` | FK | no | Parent channel |
| `storefront_code` | `text` | UQ | no | Stable warehouse code |
| `storefront_name` | `text` |  | no | Bibica TikTok Shop, Bibica Official Store, or Quasure specialized store |
| `product_line` | `text` |  | yes | Product-line attribute; not a legal-entity key |

### 2.3 `dim_order_identity`

**Grain:** one channel + storefront + native order ID.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `order_key` | `bigint` | PK | no | Surrogate order key |
| `channel_key` | `bigint` | FK | no | Channel namespace |
| `storefront_key` | `bigint` | FK | no | Storefront namespace |
| `native_order_id` | `text` |  | no | Native ID retained as string |
| `order_namespace` | `text` | UQ | no | Concatenated unique namespace |

### 2.4 `dim_date`

**Grain:** one calendar date.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `date_key` | `integer` | PK | no | `YYYYMMDD` or documented warehouse key |
| `calendar_date` | `date` | UQ | no | Calendar date |
| `year` | `smallint` |  | no | Calendar year |
| `quarter` | `smallint` |  | no | 1–4 |
| `month` | `smallint` |  | no | 1–12 |
| `day` | `smallint` |  | no | Day of month |
| `month_name` | `text` |  | no | Display label |
| `week_of_year` | `smallint` |  | no | ISO week |

### 2.5 `dim_time`

**Grain:** one time-of-day value at the chosen precision.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `time_key` | `integer` | PK | no | Warehouse time key |
| `native_time` | `time` | UQ | no | Time without inferred timezone |
| `hour` | `smallint` |  | no | Hour |
| `minute` | `smallint` |  | no | Minute |
| `second` | `smallint` |  | no | Second |

Timezone is not stored as an inferred fact. The selected timezone must be documented in the ingestion contract.

### 2.6 `dim_source_product_sku`

**Grain:** one source-native product/variant identity in a storefront.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `source_product_sku_key` | `bigint` | PK | no | Surrogate key |
| `channel_key` | `bigint` | FK | no | Source channel |
| `storefront_key` | `bigint` | FK | no | Source storefront |
| `native_product_id` | `text` |  | yes | Source product identifier when available |
| `native_sku_id` | `text` |  | yes | TikTok SKU ID or Shopee SKU variant value |
| `seller_sku` | `text` |  | yes | Seller-provided SKU when available |
| `product_name` | `text` |  | yes | Source product name; not a verified cross-platform key |
| `variation_name` | `text` |  | yes | Source variation/specification |
| `product_line` | `text` |  | yes | Includes Quasure classification where applicable |
| `conformed_product_key` | `text` |  | yes | Future crosswalk key; not populated without validation |
| `mapping_status` | `text` |  | no | `UNMAPPED`, `PROVISIONAL`, `VALIDATED`, or documented equivalent |
| `mapping_version` | `text` |  | yes | Crosswalk version |

### 2.7 `dim_warehouse`

**Grain:** one source warehouse member.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `warehouse_key` | `bigint` | PK | no | Surrogate key |
| `storefront_key` | `bigint` | FK | no | Source context |
| `native_warehouse_name` | `text` |  | no | Original warehouse value |
| `normalized_warehouse_name` | `text` |  | yes | Controlled normalized value |
| `mapping_status` | `text` |  | no | Mapping confidence/state |
| `mapping_version` | `text` |  | yes | Normalization version |

### 2.8 `dim_province`

**Grain:** one normalized destination province.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `province_key` | `bigint` | PK | no | Surrogate key |
| `native_province_name` | `text` |  | no | Original province value |
| `normalized_province_name` | `text` |  | yes | Standardized province value |
| `mapping_status` | `text` |  | no | Mapping confidence/state |
| `mapping_version` | `text` |  | yes | Normalization version |

Only province is modeled. District, commune, exact address, recipient, phone, and buyer identifiers are excluded.

### 2.9 `dim_order_status`

**Grain:** one native status mapping for a channel/storefront and mapping version.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `order_status_key` | `bigint` | PK | no | Surrogate key |
| `channel_key` | `bigint` | FK | no | Source channel |
| `storefront_key` | `bigint` | FK | no | Source storefront |
| `native_status` | `text` |  | no | Exact source status |
| `reviewed_status` | `text` |  | yes | Reviewed lifecycle class |
| `mapping_version` | `text` |  | yes | Mapping version |
| `source_timezone` | `text` |  | yes | Contract value, not inferred from data |
| `effective_from` | `date` |  | yes | Mapping validity start |
| `effective_to` | `date` |  | yes | Mapping validity end |

### 2.10 `dim_source_file`

**Grain:** one source file/sheet identity.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `source_file_key` | `bigint` | PK | no | Surrogate key |
| `source_file_name` | `text` |  | no | Original filename |
| `source_sha256` | `char(64)` | UQ candidate | no | Source fingerprint |
| `sheet_name` | `text` |  | no | `csv` or workbook sheet |
| `source_kind` | `text` |  | no | `tiktok_sales`, `tiktok_reviews`, or `shopee_orders` |
| `source_storefront` | `text` |  | no | Source storefront label |

### 2.11 `dim_ingestion_batch`

**Grain:** one ingestion execution for one source file.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `ingestion_batch_key` | `bigint` | PK | no | Surrogate batch key |
| `source_file_key` | `bigint` | FK | no | Source identity |
| `batch_id` | `text` | UQ | no | Stable batch identifier |
| `started_at` | `timestamptz` |  | no | Execution start |
| `completed_at` | `timestamptz` |  | yes | Execution completion |
| `load_status` | `text` |  | no | `STARTED`, `LOADED`, `FAILED`, `REPLAYED`, or documented equivalent |
| `row_count_read` | `integer` |  | yes | Rows read |
| `row_count_loaded` | `integer` |  | yes | Rows accepted into staging/warehouse |

## 3. Fact tables

### 3.1 `fact_order_line_candidate`

**Grain:** one non-empty physical source row representing a product/variant export line with order/package context.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `order_line_key` | `bigint` | PK | no | Surrogate fact key |
| `order_key` | `bigint` | FK | no | Storefront-scoped order |
| `channel_key` | `bigint` | FK | no | Channel role |
| `storefront_key` | `bigint` | FK | no | Storefront role |
| `source_product_sku_key` | `bigint` | FK | yes | Source product/SKU when present |
| `warehouse_key` | `bigint` | FK | yes | Warehouse mapping |
| `province_key` | `bigint` | FK | yes | Province mapping |
| `order_status_key` | `bigint` | FK | yes | Native/reviewed status member |
| `order_created_date_key` | `integer` | FK | no | Created date |
| `order_created_time_key` | `integer` | FK | yes | Created time |
| `paid_date_key` | `integer` | FK | yes | Paid date |
| `paid_time_key` | `integer` | FK | yes | Paid time |
| `shipped_date_key` | `integer` | FK | yes | Shipped/send date |
| `shipped_time_key` | `integer` | FK | yes | Shipped/send time |
| `delivered_date_key` | `integer` | FK | yes | Delivered date |
| `delivered_time_key` | `integer` | FK | yes | Delivered time |
| `source_file_key` | `bigint` | FK | no | Source lineage |
| `ingestion_batch_key` | `bigint` | FK | no | Batch lineage |
| `source_sheet_name` | `text` |  | no | Source sheet captured on fact for audit |
| `physical_row_number` | `integer` |  | no | 1-based physical source row |
| `source_row_hash` | `char(64)` |  | no | Diagnostic content hash |
| `quantity` | `numeric(18,4)` |  | yes | Source row quantity |
| `returned_quantity` | `numeric(18,4)` |  | yes | Source return quantity where available |
| `unit_price_source` | `numeric(19,4)` |  | yes | Native source unit-price field |
| `gross_item_amount_source` | `numeric(19,4)` |  | yes | Native/derived item gross; source-specific |
| `net_item_amount_source` | `numeric(19,4)` |  | yes | Native item amount after discount; source-specific |
| `seller_discount_source` | `numeric(19,4)` |  | yes | Native seller discount |
| `platform_discount_source` | `numeric(19,4)` |  | yes | Native platform discount |
| `shipping_buyer_charge_source` | `numeric(19,4)` |  | yes | Native buyer shipping field |
| `order_amount_source` | `numeric(19,4)` |  | yes | Order-scoped candidate; non-additive on this fact |
| `source_row_quality_status` | `text` |  | no | Accepted/flagged/rejected-by-contract state; no silent deletion |

**Idempotency constraint:** unique on `(source_file_key, source_sheet_name, physical_row_number, ingestion_batch_key)` for the raw batch record. A separate current-state/replay policy is required before production upsert rules are finalized.

### 3.2 `fact_order_lifecycle_candidate`

**Grain:** one `(channel, storefront, native_order_id)` order after documented reconciliation.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `order_lifecycle_key` | `bigint` | PK | no | Surrogate fact key |
| `order_key` | `bigint` | FK/UQ | no | One lifecycle row per scoped order in this candidate |
| `channel_key` | `bigint` | FK | no | Channel |
| `storefront_key` | `bigint` | FK | no | Storefront |
| `order_status_key` | `bigint` | FK | yes | Reviewed/native status mapping |
| `warehouse_key` | `bigint` | FK | yes | Only if reconciled at order scope |
| `province_key` | `bigint` | FK | yes | Only normalized province |
| `created_date_key` | `integer` | FK | no | Order created date |
| `created_time_key` | `integer` | FK | yes | Order created time |
| `paid_date_key` | `integer` | FK | yes | Paid date |
| `paid_time_key` | `integer` | FK | yes | Paid time |
| `shipped_date_key` | `integer` | FK | yes | Shipped/send date |
| `shipped_time_key` | `integer` | FK | yes | Shipped/send time |
| `delivered_date_key` | `integer` | FK | yes | Delivered date |
| `delivered_time_key` | `integer` | FK | yes | Delivered time |
| `cancelled_date_key` | `integer` | FK | yes | Cancelled date |
| `cancelled_time_key` | `integer` | FK | yes | Cancelled time |
| `source_file_key` | `bigint` | FK | no | Source lineage |
| `ingestion_batch_key` | `bigint` | FK | no | Batch lineage |
| `order_row_count` | `integer` |  | no | Number of source rows contributing to order |
| `order_amount_source` | `numeric(19,4)` |  | yes | Retained only after reconciliation/flagging |
| `buyer_payment_source_1` | `numeric(19,4)` |  | yes | Shopee native payment field 1 |
| `buyer_payment_source_2` | `numeric(19,4)` |  | yes | Shopee native payment field 2 |
| `refund_amount_source` | `numeric(19,4)` |  | yes | TikTok candidate refund amount; not a conformed refund KPI |
| `reconciliation_status` | `text` |  | no | `CONSTANT`, `CONFLICTING`, `MISSING`, `REVIEW_REQUIRED`, or documented equivalent |

### 3.3 `fact_review_candidate`

**Grain:** one rating export row.

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `review_key` | `bigint` | PK | no | Surrogate fact key |
| `order_key` | `bigint` | FK | yes | Measured order match only |
| `channel_key` | `bigint` | FK | no | Review channel |
| `storefront_key` | `bigint` | FK | no | Review storefront |
| `review_date_key` | `integer` | FK | no | Review date |
| `review_time_key` | `integer` | FK | yes | Only if source provides a time |
| `source_file_key` | `bigint` | FK | no | Source lineage |
| `ingestion_batch_key` | `bigint` | FK | no | Batch lineage |
| `source_sheet_name` | `text` |  | no | Source sheet |
| `physical_row_number` | `integer` |  | no | Physical source row |
| `source_row_hash` | `char(64)` |  | no | Diagnostic content hash |
| `source_product_id` | `text` |  | yes | Raw source product ID retained as restricted/source field |
| `source_product_sku_key` | `bigint` | FK | yes | Only when validated; otherwise null |
| `star_level` | `smallint` |  | no | 1–5 source rating |
| `has_review_text` | `boolean` |  | no | Text presence flag |
| `review_text_length` | `integer` |  | yes | Length only; no text in analytical fact |
| `product_linkage_status` | `text` |  | no | `UNVERIFIED`, `ORDER_ONLY`, `VALIDATED`, or documented equivalent |
| `review_quality_status` | `text` |  | no | Quality/restriction state |

**Privacy rule:** raw review text is restricted to controlled staging/inspection and is not included in this analytical fact or published outputs.

## 4. Foreign-key summary

* Facts reference `dim_order_identity`, `dim_channel`, `dim_storefront`, source product/SKU, warehouse, province, status, date/time, source file, and ingestion batch as applicable.
* `dim_storefront.channel_key` references `dim_channel`.
* `dim_order_identity` references both channel and storefront.
* `dim_ingestion_batch.source_file_key` references `dim_source_file`.
* No FK is created for a polymorphic `entity_type/entity_id` pattern because this design does not use one.

## 5. Candidate checks before DDL

* Confirm whether `dim_time` uses second or minute grain.
* Confirm whether lifecycle facts are current-state rows or batch snapshots.
* Confirm status mapping and timezone versioning.
* Confirm exact source field allocation for all financial columns.
* Confirm source-row idempotency behavior when the same file is replayed.
