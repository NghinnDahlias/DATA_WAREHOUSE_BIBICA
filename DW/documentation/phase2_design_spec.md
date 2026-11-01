# Bibica E-Commerce DW — Phase 2 Design Specification

## Status

**Design stage: candidate v0.1.** This document is ready for review as the logical design baseline. PostgreSQL DDL, ETL, materialized views, and production KPI publication are not yet implemented.

## Deliverables in this stage

* Galaxy Schema candidate with three facts and shared dimensions.
* Logical grain and key policy.
* Data dictionary.
* Measure and KPI safety policy.
* Decision log with unresolved assumptions.
* DBML ERD source.

## Source coverage

| Source | Business role | Modeled object |
|---|---|---|
| `Tiktokshop_Bibica.csv` | TikTok sales export | order-line and lifecycle candidates |
| `Tiktokshop_Bibica_Rating.csv` | TikTok rating export | review candidate |
| `Shopee_Bibica.xlsx` / `orders` | Shopee Bibica Official Store | order-line and lifecycle candidates |
| `Shopee_Quasure.xlsx` / `orders` | Quasure specialized store | order-line and lifecycle candidates |

## Design decisions

* Keep all three storefronts distinct.
* Namespace orders by channel + storefront + native order ID.
* Keep native IDs, statuses, timestamps, and source monetary fields.
* Preserve physical row locator and ingestion batch.
* Do not assume order-SKU uniqueness.
* Do not sum order-scoped amounts at line grain.
* Exclude direct customer identifiers and detailed addresses from analytical outputs.
* Treat Quasure as a product-line/storefront attribute, not automatically as a legal entity.

## Open decisions blocking production implementation

* Duplicate/repeated line meaning.
* Financial and refund semantics.
* Native status lifecycle mapping.
* Timestamp timezone and Shopee send/delivery field meaning.
* Source SKU crosswalk.
* Review product-level linkage.

## Next implementation order

1. Review and approve grain/key design.
2. Create PostgreSQL schemas: `raw`, `staging`, `dw`, and `mart`.
3. Add dimension and fact DDL with constraints and indexes.
4. Add source metadata and seed rows.
5. Implement extract/staging loaders with physical row lineage.
6. Implement transformations and mapping tables.
7. Implement idempotent incremental load and replay tests.
8. Add data-quality rules and validation SQL.
9. Add OLAP queries and materialized views using approved measures only.
10. Run end-to-end tests and update this specification.
