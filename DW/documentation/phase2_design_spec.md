# Phase2 — Implementation handoff

Thiết kế đã được hiện thực và tinh chỉnh04/11/2026; tài liệu này thay trạng thái candidate-only cũ.

- Kiến trúc hiện hành: `../architecture/architecture_overview.md`.
- Grain/PK/FK: `../architecture/1_galaxy_schema/galaxy_schema_candidate.md`, DBML và dictionary kế bên.
- ETL: `etl_design.md`; raw/silver/golden: `DATA_LAYERS.md`; taxonomy/geography: `CANONICAL_GEOGRAPHY.md`.
- Trạng thái đã kiểm chứng: `../07_documentation/implementation_status.md` và `../../reports/etl_validation.json`, `processing_verification.json`.

Giữ3storefront, scoped native IDs, role-playing time, order-vs-item grain và privacy boundary. Bổ sung category, warehouse/province normalization, quarantine, source-change upserts, persistent audit và refresh/assertion gates. Không biến source-safe observed payment thành accounting net revenue.
