# Modeling readiness

## Preliminary constellation

- `fact_order_line_candidate`: product/variant source row, with source row locator and order/package references. Grain is provisional because repeated order-SKU groups total 327.
- `fact_order_lifecycle_candidate`: one storefront-scoped order; use only attributes verified constant within an order or separately reconciled.
- `fact_review_candidate`: one rating export row with provisional row locator; link to order where measured, product only when validated.
- Shared dimensions: date/time roles, channel, storefront, source-specific product/SKU mapping, warehouse, normalized destination province, and reviewed order status. Quasure line classification should be product metadata and may occur in both Shopee stores.

## Phase 2 data contracts

1. Preserve source file name, SHA-256, sheet, physical row locator and ingestion batch. Idempotent load key must include source identity and row identity; content hash alone cannot distinguish legitimate identical lines.
2. Retain source-native identifiers as strings; key orders by channel + storefront + order ID until cross-source namespace is reconciled.
3. Keep native status and timestamps; add reviewed status mapping with version and timezone. Treat literal `-` as a missing-value marker, not a timestamp; do not infer missing milestones.
4. Keep item- and order-scoped money in separate staging fields. Never aggregate order totals over lines; only publish verified KPI definitions.
5. Drop names, phones, exact addresses and buyer messages from analytical dimensions. Province may be normalized. Review text requires restricted handling and redacted inspection.
6. Preserve raw files unchanged; incremental ingestion uses source fingerprint and stable batch metadata, with replay/upsert behavior tested in Phase 2.

## Open decisions

Confirm duplicate line meaning; financial formulas and refund semantics; native status mapping; SKU crosswalk; review product-level linkage; timestamp timezone. Physical PostgreSQL DDL is intentionally deferred.
