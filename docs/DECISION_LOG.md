# Quyết định DW, API, DSS và React BI

## 15/11/2026 — Keep agent instructions outside the deliverable

The user requested moving AGENTS.md outside the project and updating Git. Preserve its
bytes in a separate local notes folder; remove it from the repository and source ZIP.
Enforce the exclusion in the packager itself, not only Git/Docker ignore rules. Synthetic
archive fixtures also contain agent files to verify they cannot enter future packages.

## 15/11/2026 — Package runnable source with explicit artifact boundaries

Keep tests and working business modules. Archive only proven obsolete root replay logs
and the superseded schema image; preserve historical evidence needed by audit scripts.
Use a source allowlist for ZIP packaging instead of zipping the checkout or trusting only
.gitignore, because native Data files were historically tracked. Never include raw data,
review content, private layers, reports, runtime, credentials, dependencies or builds.

Preserve the original profiling tests. Offer a portable test profile excluding precisely
the three checks needing private files/reports; record exclusions separately from skips.
Verify the actual extracted archive against disposable fixture databases. Rewrite README
as current run/test/package instructions and keep historical progress in dedicated docs.
Do not push cleanup or regenerate coursework PDFs unless separately requested.

## 15/11/2026 — Publish source following the user's request

The user authorized publishing the statistics modal, tooltip fixes and negative-review
reader source after local verification. Include code, migration, synthetic tests and
documentation only. Exclude every new/changed report, prepared review content, raw source,
processing layer, runtime and backup. Use a normal push and verify origin/main afterwards.

## 15/11/2026 — Put extra statistics on demand and read negative opinions safely

Replace the overview ribbon with a statistics modal; remove the redundant month dropdown
while retaining chart drilldown. Reset HTML tooltip line height and portal column tooltips
to avoid clipping/overlapping text inherited from compact SVG layout styles.

Use an offline redacted review display projection, not workbook reads per API request or
original free text in business facts. Bind each record to accepted review PK, source SHA,
row hash and content version; stale/missing records are unavailable. Keep review grain,
shared cohort/cutoff and source-scoped product/warehouse rules. Topic filters require current
feature SHA/audit version. Detail access respects the same filters, star ceiling and topic.
Never return native customer/order identifiers. No inferred complaint causality/resolution.

Show a short paginated case list beside readable text. Inspection exposed a partial fifth
card at desktop height, so use four compact rows per page and verify the list's own overflow,
not only document height. Prefer a record with opinion text initially; preserve star-only
records in counts and explicitly state no text. Automatic redaction can over-remove or miss
unrecognized personal phrasing; do not certify it as manually verified anonymization.
Keep content, generated evidence and source data local; no new push requested.

## 14/11/2026 — Publish the verified source on explicit request

Publish the current child-repository source and documentation to origin/main using a normal
push. Retain all new/changed reports locally after automatic approval rejected the broader
payload containing private-data-derived analytical reports. Preserve the original local application and existing raw
Data tree. Do not include private processing, runtime, dependencies, builds or credentials.
Keep prior acceptance reports unchanged as dated evidence; record the new pre-push checks
separately so historical full-suite validation is not presented as a fresh execution.

## 10/11/2026 — Linked overview instead of fragmented overview tabs

Use one read-only /overview/dashboard snapshot so all overview panels share the same
cohort and do not independently race. Reuse existing financial grain/filter functions,
keep serialSQLguard and key-scoped product identity. Add allowlisted unit/item-value sort
for observed source-line product ranking; preserve legacy default key order.

Consolidate overview into a2x2workspace. Chart/row/insight selection updates the shared
filter; removable chips provide a clear way back. Keep detailed tabs only for distinct
analysis tasks, each with a fitting chart beside/above the data table. Use measured adaptive
pagination (route4/page); cap long product titles with full identity available in tooltip
and picker. Do not use zoom/clipping or hide numeric columns to claim fit.

Move semantics to info controls/titles while keeping errors, unavailable states, evidence
sample sizes and hypothetical-HSD notice. Add province/status controls already supported
by API; do not fake brand/traffic controls absent from the repo DW model. Hide route scores
under unsupported status/product/category cohorts. Descriptive insights do not infer growth
or causality. Preserve both local applications for comparison; code stays uncommitted and
unpushed. Actual evidence and readiness boundaries: docs/QA/LINKED_DASHBOARD.md and
reports/linked_acceptance.json; prior fixed-count/hash acceptance files are historical.


## 10/11/2026 — Native SKU identity and honest scenario inputs

Keep scoped native product identities; do not merge identical names/seller SKU. Improve
lookup context and popularity paging instead. Preserve order-grain money and filtered line
units; explicitly explain that selected-SKU order payable is not SKU revenue. Preserve native
IDs as strings end-to-end. Product sort is allowlisted, default remains key for compatibility.

There is no observed NSX/HSD/lot contract. Remove the silent30day preset and label the
standalone shelf-life function a hypothetical simulation requiring explicit remaining-life
input. Historical delivery evidence alone cannot establish actual expiry/freshness. Hide
unrelated allocation actions/errors in this tab. No DW migration or ETL required. New QA
report docs/QA/PRODUCT_FILTER_AND_ASSUMPTIONS.md records fresh execution and limitations.


## 09/11/2026 — Hạn chế cuộn trong panel

- Đo actualscrollHeight/clientHeight cho từngtab và trạng thái mở sâu. Không giảm font số liệu xuống mức khóđọc hoặc chỉẩnscrollbar. Giữ dữliệu và businesslogic, thay nhómcontrols/pagination.
- Tách scenario và nhóm tham số; parentgiữstate, kiểm payloadthực với input42units qua nhiều lần đổitab. Batchphântrang vẫn gửiđủđơn; testthêm/xóa/trởlạitrang chứngminh khôngmấtbatch.
- Bảng thay pageSize theo chiều cao panel, UIviewportthấp dùngítdòng hơn. Chúgiải/cảnhbáo dài mởkhi cần, countđơnchưagán và heuristicstatus khôngbỏ.
- APIstall được ghi riêng; đọcDBtrựctiếp khỏe, restartđúngownedPID+StartTime rồi retest. Không gánnguyênnhânchoschema/UI hoặc claimđãfixbackend khi chưa cóbằngchứng.

## 09/11/2026 — Cập nhật và kiểm thử Phase3

1. Fast-forward4commit từremote96941fb, giữ toàn bộ panel/API sẵn có và sửa trực tiếp các lỗi có bằng chứng. Không thay schema Galaxy lõi, không phụ thuộc code bản cha, không push thay đổi mới khi chưa có yêu cầu.
2. Channel filter được bổ sung vào sharedcohort, cùng khóa kho scoped. Order money tiếp tục EXISTS cùng dòng và không allocatecho kho/category. Giữ SQLserialguard.
3. Feature review là bảng phụ trợ với FK, SHA nguồn và auditversion; script chỉ lưu controlledlabels/flags. Chưa đủ feature thì unavailable, không giảzero. Build/replay có transaction và sharedadvisorylock; sourcebytes không đổi.
4. React giữ KPI+tab/viewport thay hero/page dài. Danh sách dài phân trang, panel dài cuộn cục bộ; mobilefilter đóng/mở. Không dùng CSS khóa body để khẳng định mọi nội dung đều xuất hiện đồng thời. Geometry report giữ cả client/scroll metrics và đã xem screenshot.
5. Batch DEMO chọnSKU động đúngshop, stock/HSD/capacity và evidenceDEMOghi rõ giảđịnh. Form khóa trongkhi chạy, đổi ngàylịch sử xóa shelfresultcũ; singleallocation không bị chặn bởi phươngán phụ chưahợp lệ.
6. Route riskAPI chưa có cohort SKU/category. UI công bố giới hạn và ẩn score chưalọc; không nới nghĩa dữliệu hoặc đổi scoringPhase2 để che thiếu capability. Đã kiểm thông báo này cùng các KPI đãlọc.
7. Bộkiểm tách34Reactfixturetests khỏi12browserjourneys dùngAPI/DBthật và34full-dataassertions. Currentacceptance lưu source/evidence hashes; initialFAIL giữ lịch sử. Không công bố productionready hoặc Docker/cloud/CI chưa thực thi.

## Lịch sử Phase2

9. Kiểm toán nghiệp vụ bổ sung dùng background đã được người dùng chốt, giữ dữ liệu lịch sử và thêm HN-default/explicitHCMexception cho breakfast proposals. Nguồn ghiHCMnhiều hơnHN nên không suy wholesale/stockout/nhãnđảo để giải thích. ManualSKUoverride vàsource-scopedstore/warehouse giữ rõ.
10. Tách gift khỏi historicalcommercial scoring cohort nhưng cho mixedfulfillment giữ đủgiftSKU khi có stockECOMMERCE minh thị. Không tự bỏgiftkhỏi nguyênđơn hoặc ép tiền gift0. Unmapped/gift-onlymanualreview.
11. Fix malformed/nonoptimal solver result vàcanonical variable/resource order sau test tái hiện. Reviewnegative threshold được cấu hình1/2/3, historicalSKUwarehouse linkage tránh nhân review, knownfuturecancel/delivery timestamps được loại trong scoring. Customer/complaint/replacement stages thiếu nguồn công bốUNAVAILABLE.
12. Tái hiện SQLnondeterminism trên localparallelquery mode2 với12/24mismatch, mode0khớp24/24. Giữ sessionAPI max_parallel_workers_per_gather=0, không thay globalPostgreSQL. Underlyingrootcause còn mở, nghiệmthu có điều kiện trên supportedruntime đã retest. Không tái gán toàn bộ mismatch cho công cụ test.

1. Giữ Galaxy và toàn bộ scoped keys/index/ETL tốt sẵn có. Chỉ thêm read views/index migration040, src/api và src/dss trong repo, không import code của cha. Backend dùng port8001 và DBbibica_repo, read-only transactions để tách rõ runtime.
2. KPI Contract dùng cùng M01–M16 đã đối soát của dự án tham chiếu. Order money chỉ lifecycle, line filters ở same-line EXISTS, review tổng hợp riêng. Không công bố net revenue/profit hay mixed-source delivery mean gây sai ngữ nghĩa.
3. Phục hồi Shopee shipped time bằng exact NFC header từ original columns, version bump riêng hai nguồn và reload bằng cache chính repo đã xác minh hashes. Không sửa raw/native bytes hoặc parser ID rating. Business fingerprints được kiểm nguyên vẹn, shipped coverage được kiểm riêng.
4. Binary MILP cho nguyên đơn với lexicographic served-count trước cost vì batch nhỏ và hai kho mỗi shop. Hard aggregate resource constraints giữ consistency, all-unassigned luôn là phương án khả thi. Solver cần optimum certificate và post-check constraints. Không gọi API thao tác kho thực.
5. Route statistics cùng shop/kho/tỉnh với warehouse fallback có nhãn rõ, risk index có factors và missing-data weights. Stock/expiry/capacity/delay là scenario inputs. Không suy stock/HSD từ tên, không biến historical fractions thành calibrated probabilities.
6. Temporal holdout chỉ kiểm duration, không gắn predictive accuracy cho snapshot cancellation/review score thiếu label thời điểm. Train outcomes đều đã ghi nhận trước cutoff. P90coverage thấp hơn90%được công bố nguyên trạng.
7. Thêm ANALYZE sau load/upgrade vì timeout thực đã tái hiện do cardinality nhỏ chưa có statistics. Không tắt planner safeguards hoặc tăng timeout để che lỗi. Thêm regression và chạy lại cả fixture/full-data/reload.
8. Toàn bộ Phase2 giữ local, chưa có quyền commit/push mới. Tests/evidence được chạy mới, không kế thừa PASS cũ. Các báo cáo PRIVATE layers tiếp tục ignored, report API/DSS chỉ có aggregate/hash/catalog và các nhu cầu DEMO.
