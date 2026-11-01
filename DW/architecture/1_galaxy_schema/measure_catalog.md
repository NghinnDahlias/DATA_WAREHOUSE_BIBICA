# Bibica E-Commerce DW — Measure Catalog and KPI Safety

## 1. Measure classification

| Measure | Fact | Scope | Additivity | Status |
|---|---|---|---|---|
| `quantity` | order line | source row/item | Additive after documented lifecycle filtering | Candidate |
| `returned_quantity` | order line | source row/item | Additive within source/status scope | Candidate |
| `unit_price_source` | order line | source field | Non-additive | Retain native |
| `gross_item_amount_source` | order line | item/source | Additive only within validated source semantics | TikTok partially verified; Shopee unresolved |
| `net_item_amount_source` | order line | item/source | Additive only within validated source semantics | Source-specific |
| `seller_discount_source` | order line | source field | Source-scoped only | Partially verified |
| `platform_discount_source` | order line | source field | Source-scoped only | Partially verified |
| `shipping_buyer_charge_source` | order line/order source | source field | Do not cross-platform sum | Ambiguous |
| `order_amount_source` | line and lifecycle candidates | order scope | Non-additive on line fact | Unresolved |
| `buyer_payment_source_1` | lifecycle candidate | order/source | Non-additive until allocation/settlement semantics confirmed | Unresolved |
| `buyer_payment_source_2` | lifecycle candidate | order/source | Non-additive until allocation/settlement semantics confirmed | Unresolved |
| `refund_amount_source` | lifecycle candidate | source refund field | Source-specific; not cross-platform comparable | TikTok candidate only |
| `star_level` | review | review row | Average/rate only; count rows separately | Candidate |
| `has_review_text` | review | review row | Countable | Candidate |
| `review_text_length` | review | review row | Descriptive only | Candidate |

## 2. Approved Phase 1/Phase 2 candidate outputs

These outputs may be implemented with explicit source and status filters:

* Distinct order counts by `(storefront, native_order_id)` namespace.
* Item-unit volume by month, channel, storefront, and source SKU.
* Cancellation/return incidence after a reviewed lifecycle denominator is approved.
* Created-to-shipped and shipped-to-delivered durations only after Shopee timestamp semantics are approved.
* Rating count and 1–2-star rate for TikTok ratings.
* Exploratory complaint-theme candidates with manual validation labels.

## 3. Restricted outputs

Do not publish until business confirmation:

* Paid revenue.
* Net sales.
* Gross merchandise value combined across platforms.
* Cross-platform refund cash value.
* Discount totals treated as accounting amounts.
* Product-level review quality claims based only on the current proxy linkage.

## 4. Safe aggregation examples

```sql
-- Distinct scoped orders: order-level fact, no line multiplication.
SELECT storefront_key, COUNT(*) AS order_count
FROM dw.fact_order_lifecycle_candidate
WHERE reconciliation_status <> 'REVIEW_REQUIRED'
GROUP BY storefront_key;
```

```sql
-- Item units: line-level measure.
SELECT storefront_key, order_created_date_key, SUM(quantity) AS item_units
FROM dw.fact_order_line_candidate
GROUP BY storefront_key, order_created_date_key;
```

```sql
-- Unsafe: repeated order amount at line grain.
-- SELECT SUM(order_amount_source) FROM dw.fact_order_line_candidate;
```

## 5. Required metadata in downstream marts

Every financial or operational aggregate must retain:

* source channel and storefront;
* source field name or measure version;
* lifecycle/status inclusion rule;
* timezone/mapping version where relevant;
* quality/reconciliation status;
* a note when the measure is provisional.
