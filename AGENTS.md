# Bibica DW, API & DSS

## Publication authorization — 05/11/2026

The user explicitly requested publishing the verified Phase2 code, documentation and
aggregate QA evidence to origin/main. Earlier local-only/no-push notes below describe
the pre-publication assessment snapshot. Private processing/runtime and native source
changes are excluded from this release. Conditional acceptance and the SQL guard remain.

## Latest business assessment — 05/11/2026

Read docs/QA/PHASE2_ACCEPTANCE.md and reports/phase2_acceptance.json first. Readiness is
CONDITIONAL_ACCEPTANCE for explainable analysis/scenarios, not production WMS or calibrated
failure prediction. This supersedes61test/unqualifiedcompletion snapshots below.
Fresh114tests PASS,25business methods,90scenario oracle cases,68cohorts/2108numeric comparisons,
20integrity assertions,11review assertions,17axes/1939groups. Full-data18/ETL16/layers11PASS.

API snapshots MUST retain SET LOCAL max_parallel_workers_per_gather=0. Local parallel mode2
reproduced12/24incorrect filtered results, mode0matched24/24; boundedHTTP24+16retainedcorrectness
after mitigation. Underlying engine/plan cause remains open. Do not silently re-enable it.
Diagnostic scripts/assess_sql_parallel.py and reports/phase2_assessment/sql_parallel_diagnostic.json.

Explicitbreakfast names defaultHN. HCM needs scopedBreakfastException reason/evidence_ref/true
scenario confirmation and ECOMMERCEstock+validremaininglife. Manualbreakfast_product_keys supported.
Hura alone is shelf caution, not proof allHura belongsHN-default. Wholesale stock cannot serveTMĐT.
Mixedcommercial+gift accepts only explicitgiftECOMMERCEstock, wholeorder constraints retained.
Gift-only/Unmapped manualreview. Historical commercial risk cohort still excludes gift/Unmapped.

Review warehouse attribution uses unique historicalSKU/order warehouse, ambiguity explicit.
low_star_max1/2/3 configurable, one-star/lowcounts/interval/coverage remain visible alongside score.
Knownfuture outcome timestamps excluded, missingeventtimes remain snapshot limitation.
No causal warehouse/carrier fault, no calibrated spoilage/failureprobability, no observedstockoutcause.
CSKH promise/dispatch/receipt/resolution andcustomeridentity are explicitUNAVAILABLE capabilities.

Source conflict requires humanbusiness review: literalbreakfast source-linesHN162/HCM1744;
do not rewrite history to match narrative. Native shopQuasure vs spokenPleasure needs approvedalias.
Sourcebytes/businessfingerprints remain unchanged. NoPhase3 orcommit/push in this assessment.

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

## Phase2 backend/DSS complete locally — 05/11/2026

Read docs/PROJECT_STATE.md, docs/DECISION_LOG.md, docs/KPI_CONTRACT.md,
docs/DSS_ALGORITHMS.md, docs/DSS_EVALUATION.md and docs/API_RUNBOOK.md before changes.
Git origin/main was fetched at start and matched HEAD8865cf4. This Phase2 is local,
not committed/pushed. Do not publish raw, derived private layers or runtime.

src/api implements FastAPI/read-only REPEATABLE READ PostgreSQL snapshots, KPI M01–M16,
same-line EXISTS category/warehouse/province filters, allowlisted aggregates, pagination,
sanitized errors, metadata/quality/delivery and OpenAPI. API does not read source files.
Migration040 adds analytics.v_orders/v_items/v_reviews and dss.v_route_orders, preserving
the12dims/3facts/56FK. No parent code import or parent schema dependency.

src/dss implements whole-order binary MILP allocation between this store's HN/HCM members,
scenario SKU stock and batch capacity, name-cued breakfast shelf-life, historical risk
scoring, what-if/sensitivity on one snapshot. Defaults require stock inputs; missing
stock means UNASSIGNED. assume_available must be explicit. Gift/Unmapped-only are excluded
from commercial DSS. Never force an infeasible order into a warehouse.

Inventory, remaining shelf-life, capacity and added delays are scenario inputs, not observed
data. Breakfast name cues do not prove freshness/expiry. Rule risk is not a calibrated
failure/spoilage probability. Shopee completion is a delivery proxy; only compare within
store. Timing/review events respect cutoff, cancellation is current snapshot and cannot
support point-in-time predictive claims. Route fallback, support and denominators are explicit.
Holdout p90 coverage84.91–89.39% did not establish90%guarantee. Read evaluation limitations.

Shopee shipped header fixed to NFC `Ngày gửi hàng`; its two source parser suffixes are
repo-current-v3-shipped. TikTok/rating keep repo-current-v2 and independent lexical-ID parser.
88498raw projections changed to restore shipped only; all3business fingerprints unchanged,
four raw bytes unchanged,127588orders/178517items/5625reviews,9175209123VND completed payable,
168478completed units. Do not remove ANALYZE after ETL/migrate_api. Small dimension stale
statistics caused a reproduced20sDSS timeout before this fix.

Fresh evidence61/61unittests (13old+26DSS+22API),0skip,18/18full-data API/DSS checks,
16/16ETL/OLAP gates,11/11private-layer checks and15Golden tables/56FK reload/replay PASS.
Live HTTP32requests/16assertions PASS, including allocation/risk/shelf-life for all3stores,
recorded in reports/phase2_live_http.json. Final rollup reports/phase2_final.json.
These are05/11execution results in reports/phase2_tests.json, phase2_verification.json,
etl_validation.json, processing_verification.json. Do not substitute older13test reports.

Start `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_api.ps1`.
Repo API/docs8001, parent8000 unchanged, PostgreSQL55432. Stop via scripts/stop_api.ps1,
which verifies owned PID+StartTime. Runtime state .runtime/api-service.json. Run tests with
BIBICA_TEST_DSN set via `python scripts/run_tests.py`; `python scripts/verify_phase2.py`
checks full-data API/DSS and writes aggregate/hash evidence. No browser/UI review was requested.
Docker/cloud/remoteCI/concurrent load/crash recovery/real WMS integration remain unexecuted.
