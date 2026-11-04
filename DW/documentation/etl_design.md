# Bibica E-Commerce DW - ETL Design

## 1. Objective

The ETL loads the four immutable exports into the PostgreSQL candidate warehouse
without changing source files or publishing unverified financial KPIs.

## 2. Pipeline

```text
Data/Data_Source_Raw
        |
        v
Extract: CSV quoted parser / streaming XLSX
        |
        v
Staging contract: typed values, source lineage, quality flags
        |
        v
Transform: source mapping, namespace keys, date/time roles, restricted fields
        |
        v
Load: dimensions -> order identity -> candidate facts
        |
        v
Validation: row counts, uniqueness, FK, quality and reconciliation checks
```

`DW/etl/extract/readers.py` implements source reading, header normalization,
row lineage and row-level validation. `DW/etl/run.py` implements typed
transformations and idempotent candidate-fact loading. Structural errors are
reported per source; row errors are collected with file, sheet and physical
row instead of stopping the complete batch. A physical staging table can be
added when replay audit requires retaining every intermediate value.

## 3. Source contracts

| Source | Object | Grain | Storefront |
|---|---|---|---|
| `Tiktokshop_Bibica.csv` | order-line and lifecycle candidates | one non-empty physical row | Bibica TikTok Shop |
| `Tiktokshop_Bibica_Rating.csv` | review candidate | one rating row | Bibica TikTok Shop |
| `Shopee_Bibica.xlsx/orders` | order-line and lifecycle candidates | one non-empty physical row | Bibica Official Store |
| `Shopee_Quasure.xlsx/orders` | order-line and lifecycle candidates | one non-empty physical row | Quasure specialized store |

Required headers are validated by `src/profiling/config.py`. Missing headers
fail the run; the ETL never guesses a replacement column.

## 4. Lineage and idempotency

Every load records:

- source filename and SHA-256;
- CSV or workbook sheet name;
- physical source row number;
- source row SHA-256;
- ingestion batch ID.

The fact uniqueness key is
`source_file + sheet + physical_row_number + ingestion_batch`. A source row
hash is diagnostic only: identical legitimate rows at different positions must
not be collapsed.

Use a stable `--batch-id` when replaying a batch. Re-running the same batch is
safe because source-file, row and batch uniqueness constraints make inserts
no-ops. A new batch intentionally creates a new lineage version. Storefront
codes are explicit (`bibica_tiktok_shop`, `bibica_official_store`, and
`quasure_specialized_store`); source `kind` is never used as a storefront.

## 5. Transform rules

1. Keep native order, SKU, product and status identifiers as text.
2. Namespace orders as `channel|storefront|native_order_id`.
3. Parse literal `-` as missing.
4. Parse dates without inventing missing lifecycle milestones.
5. Keep item-scoped and order-scoped amounts in separate source fields.
6. Never sum `order_amount_source` from the line fact.
7. Leave `shipping_buyer_charge_source` and `order_amount_source` NULL on
the line fact. Keep Shopee `Giá gốc`/`Giá ưu đãi` out of gross/net item
amounts; only TikTok's validated item-grain gross/net fields are loaded.
8. Store only review presence and length in analytical facts; do not load raw
review text, names, phone numbers, addresses or buyer messages.
9. Keep product linkage as `ORDER_ONLY` until an approved SKU crosswalk exists.
10. Populate warehouse, province and native order-status dimensions as
`PROVISIONAL` mappings when no reviewed mapping is available.

## 6. Load order

1. Apply schema, dimension, fact and constraint DDL.
2. Upsert `dim_channel` and `dim_storefront`.
3. Upsert `dim_source_file` and create `dim_ingestion_batch`.
4. Upsert order identity, source product/SKU, date and time dimensions.
5. Insert order-line or review facts with `ON CONFLICT DO NOTHING`.
6. Mark the ingestion batch `LOADED` with read/loaded counts.
7. Commit the complete batch transaction. Any failure rolls back the batch.

## 7. Operational commands

```powershell
python -m DW.etl.run --dry-run
python -m DW.etl.run --load --dsn "postgresql://user:password@localhost/bibica_dw"
python -m DW.etl.run --load --dsn "$env:BIBICA_DSN" --batch-id bibica-replay-20261101
```

Install the PostgreSQL driver with `python -m pip install -r requirements.txt`.

## 8. Required post-load validation

- Every source file has a matching `dim_source_file`.
- Batch read count equals the number of non-empty source rows.
- Fact physical-row keys are unique within a batch.
- All fact foreign keys resolve.
- No analytical table contains direct customer identifiers or raw review text.
- Order-level measures are queried only from the lifecycle fact.
- Duplicate and financial reconciliation flags remain visible for review.

## 9. Deferred decisions

The ETL intentionally does not solve repeated Shopee order-SKU meaning,
Shopee payment semantics, reviewed lifecycle statuses, timestamp timezone,
cross-platform SKU equivalence, or review-to-product linkage. These require
business confirmation before production KPI publication.
