# Bibica E-Commerce DW — Galaxy Schema Architecture

## 1. Purpose

This document defines the Phase 1.2 logical architecture for a PostgreSQL Kimball constellation candidate built from four prepared exports:

* TikTok Bibica sales.
* TikTok Bibica ratings.
* Shopee Bibica orders.
* Shopee Quasure orders.

The design supports order volume, item units, cancellation/return observations, fulfillment timing, source-native discount signals, ratings, and explainable DSS inputs. It does not authorize an accounting net-sales KPI.

## 2. Scope and boundaries

### In scope

* Three distinct storefront/channel members.
* Order-line, order-lifecycle, and review facts.
* Shared conformed dimensions where semantic compatibility is defensible.
* Source lineage, physical row identity, ingestion batch, replay, and quality status.
* Native fields retained beside normalized or reviewed fields.

### Out of scope for this design version

* Cross-platform SKU equivalence.
* Production financial settlement logic.
* Customer-level analytical dimensions.
* Raw review-text publication.
* Inference of missing lifecycle milestones.
* Automatic deletion or collapse of repeated order-SKU rows.

## 3. Layered architecture

```text
Data/Data_Source_Raw
        |
        v
raw / immutable source capture
        |
        v
staging / typed source rows + lineage + quality flags
        |
        v
warehouse / shared dimensions + candidate facts
        |
        v
mart / OLAP views and materialized views
        |
        v
reports / approved non-sensitive outputs
```

The four raw files remain unchanged. The warehouse is not a replacement for raw or staging; it is a modeled analytical layer.

## 4. Galaxy components

### 4.1 Shared dimensions

* `dim_channel`
* `dim_storefront`
* `dim_order_identity`
* `dim_date`
* `dim_time`
* `dim_source_product_sku`
* `dim_warehouse`
* `dim_province`
* `dim_order_status`
* `dim_source_file`
* `dim_ingestion_batch`

### 4.2 Fact tables

* `fact_order_line_candidate`: one physical non-empty sales-export row at provisional product/variant-line grain.
* `fact_order_lifecycle_candidate`: one storefront-scoped order after documented reconciliation.
* `fact_review_candidate`: one rating-export row.

The facts share dimensions but do not share a single universal grain. Cross-fact comparison must aggregate each fact at its own grain first.

## 5. Grain rules

| Fact | Grain | Consequence |
|---|---|---|
| `fact_order_line_candidate` | One source file + sheet + physical row at a product/variant export-line grain | Repeated order-SKU rows remain separate; line measures are additive only when their source scope is item-level |
| `fact_order_lifecycle_candidate` | One `(channel, storefront, native_order_id)` order | Order-level values are stored once only after constant-value or explicit reconciliation checks |
| `fact_review_candidate` | One rating export row | Review count is row-based; product/SKU linkage remains restricted unless validated |

## 6. Key and lineage policy

### 6.1 Warehouse keys

Dimensions and facts use PostgreSQL surrogate `bigint` keys. Native IDs remain `text` and are never cast to numeric identifiers.

### 6.2 Order namespace

```text
order_namespace = channel_code || '|' || storefront_code || '|' || native_order_id
```

This namespace is the unique business key of `dim_order_identity`.

### 6.3 Physical source-row identity

The idempotent source-row key is based on:

```text
source_file_key + sheet_name + physical_row_number + ingestion_batch_key
```

`source_row_hash` is retained for diagnostics and change detection. It is not sufficient by itself because legitimate identical rows can occur at different physical positions.

## 7. Slowly changing and versioned members

* `dim_order_status` is versioned by `mapping_version`, `effective_from`, `effective_to`, and `source_timezone`.
* `dim_source_product_sku`, `dim_warehouse`, and `dim_province` carry mapping status so unresolved mappings are visible.
* A later implementation may introduce SCD Type 2 surrogate versions; this candidate does not silently overwrite historical mappings.

## 8. Measure additivity policy

### Additive at line grain

* `quantity`, subject to status/lifecycle filter.
* `returned_quantity`, where available.
* Item-scoped source amount fields, only within their source and documented semantic scope.

### Non-additive or restricted

* `order_amount_source` on the line fact.
* Buyer-payment fields repeated on line rows.
* Refund candidates whose scope is not reconciled.
* Any cross-platform `net_sales` or paid-revenue measure.

### Required safe pattern

```sql
-- Safe only for item-scoped measures and an explicitly documented filter.
SELECT storefront_key, order_created_date_key, SUM(quantity)
FROM dw.fact_order_line_candidate
GROUP BY storefront_key, order_created_date_key;
```

Do not replace this with `SUM(order_amount_source)` from the line fact.

## 9. Privacy boundary

Analytical dimensions and published outputs exclude names, phone numbers, detailed addresses, buyer usernames, buyer messages, and customer identifiers. Province may be normalized. Review text is restricted and should be redacted in inspection and output.

## 10. Approval gates before physical DDL

The following must remain visible as open decisions until confirmed:

* Meaning of repeated order-SKU and repeated physical lines.
* Shopee payment-column and order-amount semantics.
* Native-to-reviewed lifecycle status mapping.
* Timestamp timezone and Shopee send/delivery semantics.
* Cross-platform SKU/product crosswalk.
* Review-to-product/SKU linkage.
