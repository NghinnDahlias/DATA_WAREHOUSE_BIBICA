> HISTORICAL SNAPSHOT — Nội dung bên dưới là kết quả trước refinement04/11/2026. Trạng thái/schema/source hiện hành xem README.md và DW/07_documentation/implementation_status.md; evidence mới ở reports/etl_validation.json, processing_verification.json, reference_reconciliation.json. Các giả định tài chính cũ không thay measure_catalog hiện hành.

# Decisions and unresolved assumptions

| Decision | Evidence | Status |
|---|---|---|
| PostgreSQL only; Kimball constellation candidate | Fixed project architecture and CO4031 multidimensional DW requirement | Adopted for later phases |
| Preserve TikTok, Shopee Bibica and Shopee Quasure as three storefront/channel members | Three sales exports and business context | Adopted |
| Keep Quasure as product-line attribute, not separate legal entity | Business context; no legal-entity field verified | Provisional |
| Source file + sheet + row locator is provisional raw row identity | Order-SKU collision counts in key report | Adopted for staging contract |
| Treat literal `-` as missing | 5,969 Bibica and 942 Quasure payment-time cells use this exact marker | Adopted for source contract |
| Defer net sales KPI | Order amount repetition and unresolved discounts/refunds | Open |
| Restrict review-to-product claims | Review product_id lacks verified sales crosswalk | Open |
| Exclude direct customer identifiers and detailed addresses from outputs | Raw schemas contain PII columns | Adopted |

No Phase 2 database, ETL, API or dashboard has been implemented.
