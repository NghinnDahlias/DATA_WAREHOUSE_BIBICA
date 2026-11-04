# Bibica DW — Data Engineer & Database Architect

Read README.md, DW/documentation/etl_design.md and reports/etl_validation.json before changes.
Preserve the existing Galaxy tables, surrogate keys and scoped FKs; use additive migrations.
Work stays local. Do not commit/push unless explicitly requested. No buyer data or raw rows in logs/reports.
Data/Data_Source_Raw is immutable. data process/ and .runtime/ are private and ignored by Git.
Use a separate PostgreSQL database (local bibica_repo, port55432), never the parent warehouse DB.
Local Python: ../.venv/Scripts/python.exe -X utf8. This is only an interpreter location, not an import dependency.

DW/etl/run.py is the CLI entry; engine.py handles atomic snapshots, transform.sql dimensions/DQ,
facts.py stable-key fact upserts, validation.py executable gates, processing.py Raw/Silver/Golden.
SOURCES uses the new Tiktok_Rating_Bibica.xlsx. Select Ratings only; Nguon is metadata.
Never float/int-cast IDs. Recover numeric cells only from unique independent complete text IDs.
Category is name-only: explicit gift -> Bánh -> Kẹo -> Ngũ cốc. Bánh ngũ cốc is Bánh.
Four business category rows only; NULL + Unmapped is an audit state. Native TikTok category is metadata.
Keep gifts' positive observed payments. List value is not payment, revenue, profit or settlement.
Shopee seller discount is already a line total; never multiply by quantity.

Source+physical locator is current-state identity; checksum is provenance, not a new business row key.
Raw retains all records; quarantine excludes exact sales duplicates, semantic review repeats, invalid rows
and unmatched review orders from business facts. Never create sales identities just to match reviews.
Review product links use unique historical staging line names within the same TikTok order.
Warehouse is scoped by storefront; source labels map only to observed Hà Nội/Hồ Chí Minh city regions.
Customer province is independent, normalized by a spelling dictionary; no administrative-merger inference.
Every successful ETL refreshes OLAP in the same transaction. Missing sources/errors return nonzero.

Test with BIBICA_TEST_DSN pointing to an existing server DB; tests create/drop only their own random DBs.
DW.etl.verify similarly removes only its newly created disposable Golden reload database.
Never run full ETL over the parent's warehouse database or delete any existing database.
Do not reuse historical Phase1 PASS/counts for current source/schema. Read latest reports.
