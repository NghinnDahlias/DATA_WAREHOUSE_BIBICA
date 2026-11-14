# SKU lookup and shelf-life assumptions — 10/11/2026

Current local follow-up to Phase3/compact UI. No commit or push. API8001, frontend5174,
database bibica_repo55432; parent runtime/database untouched.

## Reported product filter

The reported selection is product_key8, Shopee Bibica, variation10 Cốm +10 Bơ Sữa.
Direct order-grain SQL and restarted HTTP API agree:4orders,3canceled,1completed unit,
57615VND completed order payable (UI rounds58k),75%cancellation. These are valid for
this SKU. Similar titles and even the same seller SKU do not prove the same native SKU.
No product keys were merged, reclassified or reassigned.

Lookup now exposes shop, native SKU as text, variation and order count; search includes
name/native SKU/seller SKU/variation. UI pages10results, orders descending with key tie-break.
Default API ordering remains key for compatibility. Sort is allowlisted. Selected chips
retain identity and full tooltip, with change/clear actions. Old async search responses
cannot overwrite a newer query. Ranking drilldown retains the same metadata.

Sales explains that money is the complete order payable of orders containing the selected
SKU, once per order; units only count matching completed SKU lines. No SKU revenue
allocation is implied. Financial formulas are unchanged.

## Shelf-life correction

Native header inspection found no structured manufacturing/expiry/shelf-life columns:
Shopee Bibica64, Quasure63, TikTok sales56, ratings29projected headers.
See reports/product_filter_source_headers.json. A marketing title or a review mentioning
freshness does not supply a lot expiry date or remaining shelf-life.

The old form's30days was a preset scenario assumption, not source data. It has been removed.
The tab is now **Mô phỏng HSD**, with explicit source-absence notice and required manual
remaining-life assumption. Without it the UI refuses the request. Batch execution buttons
and unrelated batch errors are hidden on this independent simulator tab. The API/model
continues to compare an explicitly supplied assumption with observed historical delivery
durations; it does not validate actual freshness, food safety, lot expiry or stock age.
DEMO batch resources remain clearly labeled scenario inputs.

## Executed checks

| Check | Actual result | Evidence |
|---|---|---|
| Backend regression |118passed,0fail/error/skip, disposable test DBs | reports/phase2_tests.json/log |
| React regression |38passed,0failed | reports/product_filter_frontend.json |
| Edge integration |17passed,0failed/skipped/flaky | reports/product_filter_browser.json |
| Production frontend build |PASS; existing large-bundle warning remains | .runtime/product-filter-build.log |
| Read-only KPI/identity/fingerprint checks |8/8PASS | reports/product_filter_reconciliation.json |
| Geometry |20screen measurements; desktop main panels max0px overflow | reports/product_filter_layouts.json |
| Expanded geometry |51panels, max2px vertical/0px horizontal overflow | reports/scroll_detail_layouts.json |
| Reported selected SKU layout |1366x768document; panel336/336px | reports/product_filter_selected_layout.json |

Backend new checks cover text native IDs, identity, native SKU search, popularity paging,
stable ordering and invalid sort rejection. React checks cover long ID precision, lookup
mapping, same-title distinct SKU selection, paging and stale-response rejection.
Edge explicitly covers the reported4order SKU and an empty HSD assumption blocking
requests, plus real three-shop DSS flows with a manually entered test assumption.
Screenshots .runtime/hsd-assumptions.png, sku-choices.png and sku-selected.png were inspected.

Full data remains127588orders/178517items/5625reviews,9175209123VND completed payable,
168478completed units. All three business fingerprints equal the previous Phase3 snapshot.
No ETL/DDL/Golden refresh was necessary or executed for these read-model/UI changes.
OpenAPI regenerated. Legacy Phase3/scroll acceptance hashes and fixed test counts are
historical snapshots; this report supersedes them for the changed lookup/UI source.
Docker/cloud/CI/production load and PDF/ZIP regeneration were not executed.

Reproduce: scripts/run_tests.py with BIBICA_TEST_DSN pointing at the local server DB;
npm --prefix frontend test; npm --prefix frontend run build;
QA_REPORT_PREFIX=product_filter npm --prefix frontend run e2e;
../.venv/Scripts/python.exe -X utf8 scripts/verify_product_filter.py.

An initial backend test run failed due to a misplaced assertion in the new test and
sandbox restrictions; assertion placement was corrected and the complete118test run
was repeated successfully. Only the final results above are acceptance evidence.
