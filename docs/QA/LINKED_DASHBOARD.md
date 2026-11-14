# Linked analytical dashboard — 10/11/2026

This local repo follow-up replaces the earlier tabbed overview and visual hierarchy.
Runtime:frontend5174/API8001/bibica_repo55432. Original application5173/API8000/warehouse
remains separate. No commit, push, raw-source changes, ETL, DDL or Golden reload.

## Resulting behavior

- Overview shows KPI, monthly trend, store contributions, category units and top8SKU
  together. Chart columns, real plot points, month selector, insight buttons and SKU rows
  update the shared filter. Individual filter chips remove one constraint; navigation to
  Sales/Warehouse/Customer retains the cohort. No overview tab switching is required.
- The advanced filter dialog includes store, canonical category, order status, customer
  province, warehouse region, store-scoped warehouse and SKU. Dates, platform and presets
  remain on the primary bar. The dialog supports Escape/backdrop close and focus return/trapping.
  Brand/TikTok acquisition traffic are not exposed: this repo DW read model does not yet
  contain these dimensions. No placeholder filters or raw-file queries were added.
- Sales pairs charts and tables for store/status, category/warehouse region, customer
  province and product ranking. Warehouse pairs performance, delivery duration and route
  tables with appropriate charts. Routes show4rows/page, all routes remain reachable.
  Review themes show chart and table together; methodology is expandable. DSS scenario
  comparison adds an assigned-order chart beside the existing complete comparison table.
- White cards on slate backgrounds, consistent store/category colors, compact KPI cards
  and readable data columns replace oversized cards and repeated captions. KPI semantics,
  limitations and quality notes remain available through information controls/titles.
  Errors/unavailable states and the explicit hypothetical-HSD notice remain visible.
- Desktop cards use measured height and adaptive table pagination; mobile stacks charts
  and tables with local scrolling. No page zoom, clipping of numeric columns, or hiding
  scrollbars is used to pass layout checks. Long names retain full identity in tooltips
  and the SKU picker, without merging same-title source products.

## Data contract and interpretation

New read-only GET /api/v1/overview/dashboard evaluates all panels on one REPEATABLE READ
snapshot with the existing serial SQL guard. It reuses the established cohort queries.
Monthly/store order counts and payable are conserved; category units are line-grain.
Product lookup additionally allows sort=units/item_value; default key ordering remains.
Native SKU IDs remain strings. TopSKU item value is observed completed source-line value,
not allocated full-order money. SKU-filtered KPI money still counts the whole matching
order once. Warehouse/province/category conditions still apply to the same source line.
No schema keys, canonical categories, parser rules, facts or DSS constraints were changed.

Insights are descriptive cohort facts:store share of completed money, observed cancellation
count/rate with denominator and minimum30orders, and category share of completed units.
They are not growth, causal fault attribution, forecast, profit, or calibrated probabilities.
Partial months and missing coverage remain explicit in the chart information control.
Chart axes use VND/counts/percentages/days as appropriate. Top8 charts are marked when
the paired table has more rows. Missing values remain absent/NULL rather than invented0.

Risk routes still use their commercial historical cohort. Product/category/status filters
hide unsupported route scores rather than presenting an unfiltered result as filtered.
Province selection restricts displayed routes; fallback evidence remains explicit. HSD
continues as an optional manual-assumption simulator, without a30day preset or lot data.

## Verification

Final acceptance is recorded in reports/linked_acceptance.json. Refer to its actual gates,
execution timestamps, source hashes and report hashes; older Phase3/scroll/product-filter
acceptance files are historical snapshots for paths changed by this follow-up.

Reproduce from repository root with its existing full database:

```powershell
$env:BIBICA_TEST_DSN='postgresql://warehouse@127.0.0.1:55432/postgres'
..\.venv\Scripts\python.exe -X utf8 scripts/run_tests.py
npm --prefix frontend test
npm --prefix frontend run build
$env:QA_REPORT_PREFIX='linked'
npm --prefix frontend run e2e
..\.venv\Scripts\python.exe -X utf8 scripts/verify_linked_dashboard.py
```

Backend fixtures create/drop only their own random databases. Full-data verification is
read-only. Browser runs use installed Edge and the actual local API through the Vite proxy.
Initial layout checks found and repaired header wrapping, hidden SKU numeric columns,
nested warehouse height and route spacing. Early browser failures also caught obsolete
selectors/page-size assumptions after the intentional UI changes; only the final run is
acceptance evidence. Existing large-bundle build warning remains; Docker/cloud/remote CI,
production load, PDF/ZIP regeneration and deployment were not executed in this task.


## Final executed results

| Gate | Actual result | Evidence |
|---|---|---|
| Backend |120passed,0fail/error/skip | reports/phase2_tests.json/log |
| React |41passed,0failed | reports/linked_frontend.json |
| Edge full suite |22passed,0failed/skipped/flaky | reports/linked_browser.json |
| Final fully-loaded/SKU rechecks |2passed,0failed | reports/linked_final_target_browser.json |
| Frontend production build |PASS; existing large-bundle warning | .runtime/linked-board-build.log |
| Independent KPI conservation |10cohorts ×6checks PASS | reports/linked_reconciliation.json |
| Data fingerprints |3/3match previous full-data snapshot | reports/linked_reconciliation.json |
| Default viewport measurements |20PASS across1366/1280/1846/390 | reports/linked_layouts.json |
| Overview card/table geometry |3desktop sizes, max0px overflow | reports/linked_board_layouts.json |
| Fully-loaded detail panels |22views, max4px vertical/0px horizontal | reports/linked_detail_layouts.json |
| Expanded themes/DSS |45panels, max0px vertical/horizontal | reports/scroll_detail_layouts.json |
| Current source/report/runtime manifest |12/12gates PASS | reports/linked_acceptance.json |

Full data remains127588orders/178517items/5625reviews,9175209123VND completed payable,
168478completed units. Native SKU text precision, canonical category, scoped warehouse
and geography semantics remain unchanged. Final numeric-column visibility and screenshots
were checked after data loaded, including long-name product ranking and review themes.
The focused recheck supplements the complete22journey suite after the last SKU cell styling
fix; it is not counted as two additional unique business journeys. Both5173and5174and their
respective APIs were HTTP200 in the final runtime gate.

The acceptance manifest records the actual executed_at timestamp in UTC and hashes of
current source and evidence files. It does not certify production, an ETL replay or the
older packaged submission. Run scripts/finalize_linked_dashboard.py to recheck it.
