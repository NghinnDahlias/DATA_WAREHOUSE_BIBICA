# Bibica DW, API, DSS & React BI

## 15/11/2026 — Source cleanup and packaging

Read docs/QA/SOURCE_PACKAGE.md and latest PROJECT_STATE. Root/frontend README now describe
standalone setup/test/package. Four root replay logs and old DB.png were archived privately
then removed. All original tests and working API/DSS/ETL modules preserved. Three new package
safety tests:128fullPython/46React/build PASS;125portable tests PASS from extracted ZIP.
Portable profile excludes exactly3private source/report checks; originals remain unchanged.
Source ZIP is dist/Bibica_DW_Source.zip, built by scripts/package_source.py using an explicit
allowlist+SHA256+CRC, never raw Data/reviews/reports/private layers/runtime/dependencies/builds.
Gitignore is not a sufficient packaging boundary: original raw files are historically tracked.
Generated reports remain local for audit dependencies. No new push, E2E/nativeETL/Golden
replay or PDF/slide regeneration in cleanup. Exact archive evidence: reports/source_package.json.

## 15/11/2026 — Source publication requested

The user explicitly authorized pushing the latest verified UI/review-reader source.
Earlier no-push notes below are implementation snapshots. Only source, synthetic tests,
schema migration and documentation may be included; generated reports, all review content,
raw/private layers, runtime and backups remain local. Verify the actual remote head for
publication status; local acceptance remains reports/review_ui_acceptance.json.

## 15/11/2026 — Statistics modal and negative-review reading

Read the latest PROJECT_STATE/DECISION_LOG and local reports/review_ui_acceptance.json.
Overview ribbon/month dropdown removed; statistics are on demand. Tooltip HTML must reset
SVG wrapper line-height0; column hover uses a viewport-clamped portal. Reader opens from
negative KPI/tab/topic chart/table. Fourcase paging,1/2/3star ceilings and same global cohort.
Auxiliary dw.review_case_content is built offline from accepted rows only, with conservative
automatic redaction; no raw content/buyer/nativeorderIDs in responses. API reads DB only.
Require sourceSHA+rowhash+contentversion for text; sourceSHA+auditversion for topic labels.
262default low-star cases/448prepared <=3stars. Business fact fingerprints/KPIs/raw hashes
unchanged.125backend/46React/26Edge PASS plus final4focused rechecks; buildPASS with bundle
warning. Fully loaded list/card geometry checked. Prior linked sourcehash manifest is historical
for changed paths. No nativeETL/Goldenreload or new push. New content/DBbackup/reports stay private.

## 14/11/2026 — Publication authorized

The user requested pushing the current source to Git. Read the publication entry in
docs/PROJECT_STATE.md and local reports/publish_20261114.json. Earlier local-only/no-push entries
describe historical snapshots. Raw Data, reports and private data process/.runtime remain excluded.
Fresh 120 backend/41 React tests, build and five-screen real-API smoke passed. Source and
evidence hashes still match the 10/11 linked acceptance. Its full browser/layout suite
was not rerun for publication. Verify the actual Git remote head to establish push status.

## 10/11/2026 — Linked analytical UI verified locally

Read docs/QA/LINKED_DASHBOARD.md and reports/linked_acceptance.json. Overview now has
KPI/trend/store/category/topSKU on one linked screen. Shared advanced filters include
status/customer province plus shop/category/warehouse/SKU; individual chips undo one axis.
Charts/plot points/insight buttons/table rows drill into the same cohort. Details pair
charts and tables; themes show both together, DSS comparison has an assigned-order plot.
Teal/slate hierarchy, compact cards and optional explanations replace oversized captions.
No raw data/ETL/DDL/Golden changes; original5173 application source remains unchanged.

Fresh120backend/41React/22Edge PASS; final2focused rechecks PASS after fully-loaded SKU
layout fix, buildPASS (large-bundle warning remains).10full-data cohorts/60conservation
checks PASS;3business fingerprints and full KPIs unchanged.20default viewport checks,
3overview sizes max0px card/table overflow,22fully-loaded detail views max4px and45expanded
panels max0px overflow PASS. Screenshots inspected. Final manifest12/12gates PASS verifies
current source/report hashes and both runtimes. Repo5174/API8001/bibica_repo55432; parent
5173/API8000/warehouse preserved. No commit/push, cloud/CI/Docker/production load or package
regeneration. Historical sourcehash/count reports are superseded for these changed paths.

Brand/traffic are not present in the repo read model and no inert controls were fabricated.
Risk scores are hidden under unsupported product/category/status cohorts. HSD remains a
manual-assumption simulator. Insights are descriptive shares/rates with denominators, not
growth/profit/causal findings or calibrated failure predictions. Long content/mobile may
still scroll locally; do not claim universal no-scroll under every possible input.


## 10/11/2026 — SKU identity and shelf-life assumptions verified locally

Read docs/QA/PRODUCT_FILTER_AND_ASSUMPTIONS.md. Fixed ambiguous product lookup: shop,
variation and native SKU text, popularity sorting,10row paging, change selection and
stale-response protection. Same-name products remain distinct native/shop SKUs. Reported
SKU8confirmed4orders/3canceled/1completed unit/57615VND, not a KPI calculation defect.
Sales now explains full-order money versus selected-SKU units.

Native headers have no manufacturing/expiry/lot fields. Removed preset30days; renamed
HSD tab to explicit hypothetical simulation, requires manual input, hides unrelated batch
execution/errors. No actual expiry/freshness claim. Existing DEMO assumptions remain DEMO.

Executed118backend/38React/17Edge PASS; buildPASS (large-bundle warning);8read-only
reconciliation gatesPASS.20screen measurements, desktop main panel overflow0px;
51expanded panels max2px. Screenshots inspected.127588orders/178517items/5625reviews,
9175209123VND/168478completed units and3business fingerprints unchanged. No ETL/DDL/
Golden reload for this UI/read-model change. API8001restarted using owned PID guard,
frontend5174hotloaded; parent DB/runtime untouched. OpenAPI and KPI/runbook docs updated.
Evidence: reports/product_filter_*.json and reports/phase2_tests.json/log. Earlier fixed
counts/source-hash acceptance files are historical; new QA report supersedes changed paths.
Local only, no commit/push/cloud/CI/PDF/ZIP regeneration.


## Latest display-density follow-up — 09/11/2026

Read docs/QA/SCROLL_OPTIMIZATION.md and reports/scroll_acceptance.json first.
UI-only refinement, still local/uncommitted/unpushed. Fresh34React/15Edge journeys PASS;
54main desktop views reduced41scrolling panels/max1300px to0/max1px.51expanded panels PASS.
Compare panel clientHeight/scrollHeight, not just document fit. Long lists/forms and narrow
screens may still scroll locally. Table pages adapt3–10rows; route5/batch4/stock3/result5.
DSS scenario/group tabs retain parent state; payload includes every order, not only visiblepage.
API/DSS source hashes and full-data KPIs unchanged. No new backend116test or ETL execution.
API stalled once during work; directDB healthy, ownedAPI restarted and finalsuite passed.
Rootcause remains undetermined; reports/scroll_runtime_recovery.json, no productionclaim.
Repo UI5174/API8001/bibica_repo55432 stay separate from parent. Source/runtime remain private.
Earlier Phase3 source hashes/layout evidence are snapshots superseded for UI by scroll reports.

## Latest Phase 3 React BI verification — 09/11/2026

Read docs/QA/PHASE3_ACCEPTANCE.md, reports/phase3_acceptance.json and docs/PHASE3_RUNBOOK.md.
Fetched HEAD/origin main96941fb; current fixes/tests/docs remain local, uncommitted and unpushed.
Fresh116backend/34React/12Edge journeys PASS,34full-dataAPI checks and20viewport measurements;
feature5625rows rebuilt/replayed,3business fingerprints and4native source hashes unchanged.
CoreGalaxy12dims/3facts/56FK preserved; review_theme_feature auxiliary table adds1FK (57total).
SourceSHA+auditversion guard makes missing/stale labels unavailable. Keep serialSQLguard.

Repo frontend5174/API8001/bibica_repo55432 stay separate from parent5173/8000/warehouse.
Use scripts/start_frontend.ps1 and stop_frontend.ps1, ownedPID+StartTime checks tested.
React tab workspace uses one document viewport; long tables/forms/details scroll inside panels.
Globalchannel/store/scopedwarehouse/product filters affect dashboardcohorts. Route risk does not
support product/categorycohort: UI explicitly hides unfilteredscore under those filters.
DSS has separate shop/as_of/history inputs; DEMOstock/expiry/capacity are scenario assumptions.

No raw/review text/buyer data publication. data process/.runtime/node_modules/dist ignored.
No fullnativeETL/Goldenexport was rerun for this UI task. Cloud/Docker/CI/productionload and
oldPDF/ZIP regeneration unexecuted. Later Phase2-only notes below are historical snapshots.

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
