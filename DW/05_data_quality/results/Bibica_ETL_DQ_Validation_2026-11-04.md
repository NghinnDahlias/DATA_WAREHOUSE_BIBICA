# Bibica DW - ETL and Data Quality Validation

## 1. Scope

- Validation date: 2026-11-04
- Scope: ETL contract, PostgreSQL post-load quality gates, source-row lineage,
  idempotent replay, row-count integrity, and established source-quality flags.
- Raw exports were not modified.
- UNKNOWN SKU classification and further SKU investigation are out of scope.
- OLAP measures and materialized views are not included in this result.

## 2. ETL and replay result

| Check | Result |
|---|---:|
| Raw source files covered | 4/4 |
| Raw source rows | 184,457 |
| Order-line candidates | 178,832 |
| Order-lifecycle candidates | 127,588 |
| Review candidates | 5,625 |
| Replay batches | 4/4 `REPLAYED` |
| Rows inserted during replay | 0 |
| Fact-count change during replay | 0 |
| Automated tests | 8/8 PASS |
| Post-load quality gates | 16/16 PASS |

The replay uses the logical source-row identity:

```text
source_file_key + source_sheet_name + physical_row_number
```

`ingestion_batch_key` remains lineage metadata and is not part of the logical
fact idempotency key. A replay with eligible source rows and zero new fact
inserts is recorded as `REPLAYED`.

## 3. Post-load quality gates

All 16 checks passed:

- 4 source-file records and 4 loaded initial batches.
- 178,832 order-line rows, 127,588 lifecycle rows, and 5,625 review rows.
- Batch rows read and loaded both equal 184,457.
- No duplicate order-line or review source identities.
- No order line is missing a lifecycle row.
- No missing required lineage, date, row-count, or rating fields.
- Shopee line-level financial fields are all `NULL`.
- All review rows have `product_linkage_status = 'ORDER_ONLY'`.
- No duplicate native-status key exists within a channel/storefront scope.

## 4. Counts by source file

| Source file | Source kind | Storefront | Rows read | Rows loaded |
|---|---|---|---:|---:|
| `Shopee_Bibica.xlsx` | `shopee_orders` | Bibica Official Store | 86,796 | 86,796 |
| `Shopee_Quasure.xlsx` | `shopee_orders` | Quasure specialized store | 14,725 | 14,725 |
| `Tiktokshop_Bibica.csv` | `tiktok_sales` | Bibica TikTok Shop | 77,311 | 77,311 |
| `Tiktokshop_Bibica_Rating.csv` | `tiktok_reviews` | Bibica TikTok Shop | 5,625 | 5,625 |

## 5. Established source-quality flags

These are observations and handling decisions, not automatic row rejection.

| Source | Observed flags | Handling |
|---|---|---|
| TikTok sales | 77,311 rows; no full duplicates or repeated order-SKU groups | Preserve physical source rows and lineage. |
| TikTok ratings | 5,625 rows; 262 ratings at 1-2 stars; 4,470 rows contain review text | Keep review text restricted; retain only review metadata in analytical facts; linkage remains `ORDER_ONLY`. |
| Shopee Bibica | 86,796 rows; 315 full duplicate rows; 323 repeated order-SKU groups; 458 rows missing SKU | Retain physical rows and lineage; do not infer whether repeats are duplicates, split packages, or transactions. |
| Shopee Quasure | 14,725 rows; no full duplicate rows; 4 repeated order-SKU groups; 82 rows missing SKU | Retain physical rows and lineage; do not infer repeated-row meaning. |

Known timestamp sequence anomalies remain investigation flags. They are not
used to delete or reject raw rows. In particular, Shopee delivery/send fields
still require a reviewed lifecycle interpretation.

## 6. Repeated order-SKU diagnostic after load

The post-load diagnostic is informational and is not a quality-gate failure:

| Source file | Repeated order-SKU groups | Physical rows in repeated groups |
|---|---:|---:|
| `Shopee_Bibica.xlsx` | 342 | 891 |
| `Shopee_Quasure.xlsx` | 16 | 33 |

The difference between source profiling flags and this diagnostic is expected
because the checks use different grouping definitions. The source profiling
flag is retained as the documented source-quality baseline; the post-load
query groups loaded rows by source file, order key, and source SKU key.

## 7. Financial and semantic safeguards

- Shopee `Giá gốc` and `Giá ưu đãi` are not treated as verified line-level
  gross/net amounts.
- Line-level shipping and order amount fields remain `NULL`.
- TikTok gross/net item amounts are loaded only for the validated item grain.
- Order-level amounts remain in the lifecycle candidate fact and are not summed
  from the order-line fact.
- No paid-revenue or net-sales KPI is published by this validation.
- Names, phone numbers, detailed addresses, buyer messages, and raw review text
  are excluded from analytical facts.

## 8. Quality-gate decision

**CONDITIONAL PASS for the ETL/load stage.**

ETL execution, lineage, post-load integrity, replay behavior, and known source
quality flags are recorded and validated. The warehouse is not yet approved
for business-certified financial KPIs because the following decisions remain
open:

1. Shopee financial amount semantics, including buyer-payment columns.
2. Refund and return calculation semantics.
3. Native status to reviewed lifecycle mapping.
4. Timestamp timezone and lifecycle meaning.
5. Meaning of repeated order-SKU rows.
6. Cross-platform SKU crosswalk.
7. Review-to-SKU linkage policy.

## 9. Safe OLAP and materialized-view validation

The following SQL files were added and executed against the local PostgreSQL
database:

- `DW/04_sql/olap/01_safe_olap_queries.sql`
- `DW/04_sql/olap/02_materialized_views.sql`
- `DW/04_sql/olap/03_olap_validation.sql`

Three populated marts were created:

- `mart.mv_order_counts_by_storefront`
- `mart.mv_item_units_monthly`
- `mart.mv_tiktok_ratings_monthly`

Validation results:

| Check | Result |
|---|---:|
| Restricted financial columns exposed by approved marts | 0 |
| Negative item/returned units | 0 |
| Rating rates outside 0-100% | 0 |
| Monthly item-unit reconciliation violations | 0 |
| Storefront order reconciliation violations | 0 |
| Populated materialized views | 3/3 |

The first reconciliation run reported 39 false mismatches because the fact-side
check compared `NULL` returned-unit sums with the mart's `COALESCE(..., 0)`.
The validation query was corrected to use the same zero-normalization and then
returned zero violations.

## 10. Final gate and handoff

- Technical Quality Gate: **PASS**
- Business/KPI Gate: **CONDITIONAL**

The implementation status handoff is documented in
`DW/07_documentation/implementation_status.md`.

## 11. Next approved step

Run the existing OLAP SQL and materialized-view checks using only source-safe
measures. Do not publish cross-platform paid-revenue or net-sales totals until
the financial semantics are approved.
