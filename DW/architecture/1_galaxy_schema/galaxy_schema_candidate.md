# Galaxy Schema Candidate v0.1

## 1. Scope

This design covers the four prepared exports:

* TikTok Bibica sales.
* TikTok Bibica ratings.
* Shopee Bibica orders.
* Shopee Quasure orders.

The design keeps the three storefronts separate and uses a Kimball-style constellation with shared dimensions. It is intentionally **candidate/provisional** while financial semantics, SKU crosswalks, timestamp timezone, status mapping, and repeated-line meaning remain open.

## 2. Design principles

* Fact grain is defined before measures are added.
* Physical source-row identity is preserved; content hash alone is not an idempotent key.
* Order IDs are always namespaced by channel and storefront.
* Source-native monetary fields remain source-specific until their semantics are reconciled.
* Order-level amounts are never summed from an order-line fact.
* Source-native status is retained beside any reviewed status mapping.
* PII and detailed addresses are excluded from analytical dimensions and published outputs.

## 3. Fact tables

| Fact | Grain | Candidate primary key | Main foreign keys | Important measures/attributes |
|---|---|---|---|---|
| `fact_order_line_candidate` | One non-empty physical source row representing a product/variant export line, with order/package context | `order_line_key` | order identity, date/time roles, channel, storefront, source product/SKU, warehouse, province, status, source file, ingestion batch | quantity, returned quantity, source unit price, source gross item amount, source net item amount, seller/platform discount, buyer shipping charge, source row-level order amount; all source-scoped |
| `fact_order_lifecycle_candidate` | One order scoped by channel + storefront + native order ID | `order_lifecycle_key` | order identity, date/time roles, channel, storefront, status, warehouse, province, source file, ingestion batch | lifecycle timestamps, row count, reconciled source order amount where constant, source-specific payment/refund candidates, reconciliation flags |
| `fact_review_candidate` | One rating export row | `review_key` | order identity when measured, review date/time, channel, storefront, source file, ingestion batch; source product/SKU only when validated | star level, text-present flag, text length, restricted-linkage status; raw review text is not published |

### 3.1 Order-line rules

`fact_order_line_candidate` must not have a uniqueness rule on `(order, SKU)`. The observed data contains repeated order-SKU groups in Shopee exports, and the cause is unresolved. Each physical row remains traceable through source file, sheet, physical row number, and ingestion batch.

Order-level measures in this fact are non-additive candidate fields. They may be retained for reconciliation but must not be used in `SUM()` for business KPIs.

### 3.2 Order-lifecycle rules

The lifecycle fact is not a blind `GROUP BY order_id`. It may contain only attributes verified constant within the storefront-scoped order or values produced by a documented reconciliation rule. Conflicting source-scoped values must remain visible as candidates plus a reconciliation status.

### 3.3 Review rules

The review fact can link to `dim_order_identity` where the order match was measured. The review product ID/name must not be treated as a verified SKU/product join. Raw review text belongs in a restricted staging area and is excluded from analytical outputs.

## 4. Shared dimensions

| Dimension | Grain | Purpose |
|---|---|---|
| `dim_channel` | One sales channel | TikTok or Shopee. |
| `dim_storefront` | One storefront within a channel | Bibica TikTok Shop, Bibica Official Store, Quasure specialized store. |
| `dim_order_identity` | One channel + storefront + native order ID | Shared order namespace without customer identity. |
| `dim_date` | One calendar date | Role-playing order, payment, shipping, delivery, cancellation, completion, and review dates. |
| `dim_time` | One native time-of-day | Role-playing time for timestamp analysis. |
| `dim_source_product_sku` | One source-native product/variant identity | Keeps TikTok and Shopee key systems separate; includes mapping status and product-line metadata. |
| `dim_warehouse` | One source warehouse member | Stores native and normalized warehouse names with mapping status. |
| `dim_province` | One normalized destination province | Province only; no detailed address. |
| `dim_order_status` | One channel/storefront native status mapping version | Retains native status and reviewed status, effective dates, timezone, and mapping version. |
| `dim_source_file` | One source file/sheet identity | Stores filename, SHA-256, sheet, and source type. |
| `dim_ingestion_batch` | One ingestion execution for one source file | Supports replay, lineage, and idempotent loads. |

`dim_source_file` and `dim_ingestion_batch` are technical/audit dimensions shared by all facts. They are not customer or product dimensions.

## 5. Relationship map

```text
                         dim_date       dim_time
                             │              │
 dim_channel ───────┐       │              │       ┌── dim_order_status
 dim_storefront ────┼───────┼──────────────┼───────┤
 dim_order_identity ─┤       │              │       │
 dim_source_product ─┤       │              │       │
 dim_warehouse ──────┤       │              │       │
 dim_province ───────┤       │              │       │
 dim_source_file ────┤       │              │       │
 dim_ingestion_batch ┤       │              │       │
                      ▼       ▼              ▼       ▼
              fact_order_line_candidate   fact_order_lifecycle_candidate
                      ▲
                      │ order identity/date/channel/storefront/source lineage
                      ▼
                 fact_review_candidate
```

The diagram shows shared dimensions, not an instruction to duplicate dimension tables per fact.

## 6. Key strategy

### 6.1 Surrogate keys

* All warehouse dimensions and facts use PostgreSQL surrogate `bigint` keys.
* Foreign keys reference surrogate keys, not raw platform identifiers.
* Native identifiers remain separate `text` attributes.

### 6.2 Order identity

`dim_order_identity.order_namespace` is derived as:

```text
channel_code || '|' || storefront_code || '|' || native_order_id
```

It must be unique. Customer identifiers are not part of this key.

### 6.3 Source-row idempotency

The logical source-row identity contains:

```text
source file identity + sheet + physical row number + ingestion batch identity
```

The physical row number preserves legitimate identical rows at different locations. A content hash is retained for diagnostics, not used alone as the load key.

## 7. Financial field policy

Use explicit source-scoped columns such as:

* `gross_item_amount_source`
* `net_item_amount_source`
* `seller_discount_source`
* `platform_discount_source`
* `order_amount_source`
* `buyer_payment_source_1`
* `buyer_payment_source_2`
* `refund_amount_source`

Do not create or publish a conformed `net_sales` measure until the source settlement semantics are confirmed. The TikTok item equation is a validation observation, not authorization to combine all platform money fields.

## 8. Mapping policy

* TikTok `SKU ID` and Shopee `SKU phân loại hàng` remain source-native keys.
* A future crosswalk may map source-native keys to a conformed product/SKU, but its mapping status must be explicit.
* Quasure classification is product metadata and may occur in both Shopee storefront contexts.
* Warehouse names and provinces require controlled normalization tables with raw value, normalized value, and mapping status.

## 9. Not approved yet

The following are deliberately deferred:

* Production PostgreSQL DDL.
* Physical ETL implementation.
* Cross-platform SKU equivalence.
* Reviewed lifecycle status mapping.
* Timestamp timezone conversion.
* Net sales/paid revenue KPI.
* Automatic deletion or collapse of repeated lines.
