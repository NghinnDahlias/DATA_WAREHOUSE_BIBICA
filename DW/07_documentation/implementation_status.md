# Bibica DW - Phase 2 Implementation Status

## Status date

2026-11-04

## Technical implementation status

| Area | Status | Result |
|---|---|---|
| Galaxy schema | PASS | Facts, dimensions, grain, PK/FK and lineage model implemented |
| PostgreSQL DW | PASS | Schemas, tables, indexes and facts loaded |
| ETL/ELT | PASS | TikTok sales, TikTok ratings, Shopee Bibica and Shopee Quasure loaded |
| Source normalization | PASS | Source-native SKU, warehouse, province, time and status retained/normalized |
| Data quality | PASS with documented flags | Duplicate, repeated-line and timestamp flags retained without silent deletion |
| Incremental/idempotent load | PASS | Replay batches are `REPLAYED`; no new fact rows inserted on replay |
| OLAP queries | PASS | Safe order, item-unit and rating aggregations created |
| Materialized views | PASS | 3/3 views populated |
| OLAP validation | PASS | 0 restricted-column, negative-unit, rate, monthly-reconciliation or order-reconciliation violations |
| Architecture/ETL documentation | COMPLETE | Runbook, data dictionary, limitations and validation report updated |

## Materialized views

- `mart.mv_order_counts_by_storefront`
- `mart.mv_item_units_monthly`
- `mart.mv_tiktok_ratings_monthly`

## Financial safety boundary

The technical pipeline does not publish paid revenue, net sales,
cross-platform GMV, or cross-platform refund cash value. Source-native
financial fields remain provisional/reconciliation fields until their business
semantics are approved.

## Final gates

- **Technical Quality Gate: PASS**
- **Business/KPI Gate: CONDITIONAL**

The conditional status concerns business confirmation, not ETL or OLAP
execution. Open decisions include financial/refund semantics, native
lifecycle and timestamp interpretation, repeated order-SKU meaning,
cross-platform SKU crosswalk, and review product linkage.

## Validation references

- [ETL and data-quality validation](../05_data_quality/results/Bibica_ETL_DQ_Validation_2026-11-04.md)
- [Safe OLAP queries](../04_sql/olap/01_safe_olap_queries.sql)
- [Materialized views](../04_sql/olap/02_materialized_views.sql)
- [OLAP validation](../04_sql/olap/03_olap_validation.sql)
