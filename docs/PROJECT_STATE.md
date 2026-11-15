# Trạng thái DW, API, DSS và React BI

## 15/11/2026 — Cleanup and source packaging

Rewrote root/frontend README around current capabilities, standalone Windows setup, ETL,
review preparation, test commands and packaging. Removed four obsolete replay logs and
the old DB.png from source after hash-verified copies under .runtime/cleanup-20261115.
Kept current DBML/SQL and all original test methods. Reports remain local for audit scripts;
Git/Docker/source-archive rules exclude generated/private artifacts and future raw additions.

Added scripts/package_source.py with an explicit file allowlist, required source/test
checks, per-file SHA256 manifest and ZIP CRC/readback validation. Added three safety tests.
scripts/run_tests.py --portable excludes exactly three existing private-source/report
checks without editing their originals; all fixture tests remain. Standalone packages
create their own reports directory when tests run.

Fresh128Python/46React/build PASS; portable125tests PASS in a newly extracted source ZIP
without Data or historical reports, using disposable test databases and installed dependencies.
The existing frontend bundle-size warning remains. No UI/API/DSS/ETL business source changes,
native ETL/Golden replay, E2E rerun, database deletion, cloud/CI/Docker or new Git publication.
Artifact: dist/Bibica_DW_Source.zip; evidence: docs/QA/SOURCE_PACKAGE.md and local
reports/source_package.json. Original raw sources and private layers remain unchanged.
This is a source-only archive, not a preloaded DW or regenerated PDF/slide submission.

## 15/11/2026 — Publication of the review-reader source authorized

The user explicitly requested pushing the preceding UI/review-reader changes. Prepare a
normal source/documentation-only commit to origin/main; this supersedes the no-publication
status of the implementation snapshot below. Private review content, all generated reports,
raw Data, data process, database backups, builds and runtime remain local. Revalidate the
recorded source/evidence hashes before committing; verify the remote head after pushing.
Publication is not a deployment or an additional full test execution.

## 15/11/2026 — On-demand statistics, readable tooltips and negative-review reader

Removed the overview insight ribbon and month dropdown. Extra calculations now load in
the **Thống kê chỉ số** modal using the current filters. Monthly point/bar cross-filtering
remains. Fixed tooltip typography inherited from zero-line-height SVG containers; column
tooltips render in a viewport-clamped portal, with separate title/value rows.

Customer Experience adds a negative-review reading tab and clickable negative KPI/topic
bars/table rows. Reader uses four cases per page with a side-by-side opinion, 1/2/3-star
ceilings, topic selection and the existing global cohort. It initially selects a case with
text when available; star-only records are explicitly NO_TEXT. Source/native buyer/order
identifiers are not returned. Content is a conservative automatically redacted projection,
not a guarantee of human-verified anonymization; labels remain unvalidated keyword mentions.

Added auxiliary dw.review_case_content via migration050 (one review/PK, cascade FK),
offline scripts/build_review_case_content.py and source/version/row-hash guards. API reads
PostgreSQL only. Prepared448accepted cases <=3stars; default1–2stars gives262cases.
Original rating bytes, all four source hashes, three fact fingerprints and every KPI
matched the before snapshot. Core Galaxy/grains/keys and the original parent app unchanged.
No native ETL/Golden reload, no publication, Docker/cloud/CI or PDF/ZIP regeneration.

Executed:125backend tests,46React tests, production build and26Edge journeys PASS.
Final four browser rechecks cover the last reader paging/selection and fully-loaded
geometry updates; they supplement the26journeys, not four additional unique journeys.
Eightcohorts reconcile with low-review KPI; all topic counts and all262case details verified.
Sixloaded overview/reader viewport checks include1366x768,1280x720,390x844; desktop page,
card/panel and four-case list overflow are checked directly. Screenshots inspected.
Evidence: reports/review_reader.json, reports/review_ui_full_browser.json,
reports/review_ui_final_browser.json, reports/review_ui_acceptance.json and private runtime
logs/measurements. Older linked acceptance source hashes do not certify these changed files.
Build retains the existing large-bundle warning. Local UI5174/API8001/bibica_repo55432.

## 14/11/2026 — Source publication checks

The user explicitly authorized pushing the current source to origin/main. This supersedes
the earlier local-only publication notes; raw Data, private processing, reports and runtime
remain excluded. Fetched origin/main and confirmed no divergence before preparing the release.

Fresh checks: 120 backend tests PASS (0 failures/errors/skips), 41 React tests PASS,
production build PASS (existing bundle-size warning), and one real-API Edge smoke covering
all five screens PASS. The 42 source hashes and nine evidence hashes in the 10/11 linked
acceptance manifest still match. Its full 22-journey suite and geometry checks are historical
results, not rerun in this publication task. No ETL/Golden reload, raw changes, Docker/cloud,
remote CI or PDF/ZIP regeneration. Local publication evidence: reports/publish_20261114.json
(not included in the source release). Automatic approval review rejected the first push
because the commit included analytical reports derived from private warehouse data.
The source release therefore excludes the entire reports directory; historical and current
report references in documentation refer to local execution artifacts.
Commit/push and remote-head verification follow these checks; this entry is not push proof.

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


## Tối ưu hiển thị tiếp theo — PASS local, 09/11/2026

Theo yêu cầu hạn chế thanh cuộn, chỉ thay React và kiểm thử UI trong repo con. Đọc docs/QA/SCROLL_OPTIMIZATION.md và reports/scroll_acceptance.json; phần này supersede layout/source hashes của snapshot Phase3 bên dưới.

- Bộ lọc desktop một hàng, kho/vùng/category ở popup; KPI/spacing gọn. Review tách biểu đồ/bảng/phương pháp. DSS chọn từngscenario, chia4nhóm tham số, xem giải thích từngscenario; form và bảng không còn nối dọc nhiều khối.
- Bảng tự chọn3–10dòng theo chiều cao; tuyến5dòng/trang, batch4đơn/trang, tồn3dòng/trang, kết quả5đơn/trang. Payload vẫn chứa toàn bộbatch/scenario, chuyển nhóm không mất input.
- Cùng54lượt xem desktop1366×768/1280×720/1846×867:41vùng cuộn, max1300px trước →0vùng cuộn, sai sốmax1px sau.51panel mở sâu PASS, maxoverflow2px. Đã xem ảnh loaded review và DSS thực.
- Chạy mới34/34Reacttests,15/15Edgejourneys,0skip/flaky, build PASS. verify_scroll_ui.py11/11checks PASS; API/DSS implementation hashes vàfull-data KPI không đổi. Không chạy lại backend116tests/ETL/Golden hay sửa bản cha.
- Gặp1sự cố API khôngtrảhealth trong30s, DBtrực tiếp0,02s và khôngcósessionAPI. Đã restartownedAPI theoPID/StartTime, kiểmhealth/KPI200 và chạy lại15journeys cuối. Rootcausechưa xácđịnh, khônggọiUIchange làfixbackend. Evidence scroll_runtime_recovery.json.
- UI5174/API8001 vẫn chạy. Source/data riêngtư giữnguyên, khôngcommit/push. Danhsách/giảithích dàivà màn hìnhhẹp vẫn cóthể cuộn cục bộ. Không chứngnhậnproduction; PDF/ZIP chưa táixuất.

## Phase 3 BI/React — PASS local với giới hạn công bố, 09/11/2026

Đã fetch/fast-forward repo từ be9117a tới96941fb70b135f72d040b6fe996421f465936eb6 (4commit mới). Fetch cuối xác nhận origin/main vẫn cùng commit. Các sửa lỗi và QA của lượt này ở local, chưa commit/push. Đọc docs/QA/PHASE3_ACCEPTANCE.md và reports/phase3_acceptance.json; các ghi chú “chưa có frontend/không bắt đầu Phase3” bên dưới là lịch sử Phase2.

- React5màn dùng API thực, sidebar thu gọn, tab phân tích/bước DSS, bảng dài phân trang10dòng, mobile mở/đóng bộ lọc. Kênh tách shop, warehouse_key scoped tách vùng kho; giữ cùng-dòng EXISTS và canonical category. Các panel/API tốt sẵn có được giữ.
- Đã sửa batch mẫu key1365 hardcode thành chọn SKU động đúng shop; nạp feature review đúng entrypoint với SHA/auditversion và trạng thái unavailable nếu thiếu/cũ; NULL/monthgap không thành0; error không giữ KPI cũ; picker tránh response cũ; đổi ngày xóa shelf-life result cũ. DSS form khóa khi đang chạy để input và output khớp nhau.
- Chạy mới116/116backend tests,34/34React tests,12/12Edge journeys (0skip/flaky),34/34full-data API checks/27requests,20/20viewport measurements. Build/compileall/gitdiffcheck PASS.13/13rollup checks PASS, statusPASS_WITH_LIMITATIONS. E2E chạy allocate/what-if/sensitivity/shelf-life trên cả3shop, drilldown/filter/empty/error, các tab và mobilefilter.
- Review feature5625rows đã build và replay cùng fingerprintlogic. Galaxycore12dims/3facts/56FK giữ nguyên; bảngfeature phụ trợ thêm1FK (toàn schema57FK). Không thay127588orders/178517items/5625reviews, completedpayable9175209123VND vàcompletedunits168478;3fingerprints/4nativehashes giữ nguyên. Không chạy lạifullnativeETL/Golden export cho lượtUI này.
- UI http://127.0.0.1:5174, API http://127.0.0.1:8001/docs, DBbibica_repo55432. start_frontend.ps1/stop_frontend.ps1 đã kiểm ownedPID+StartTime, reuse, stop/restart và liveHTTP200; dịch vụ đang chạy. Bản cha5173/8000 độc lập.
- Các trang nằm trongviewport; nội dung dài vẫn cuộn trongpanel. Risk tuyến chưa hỗ trợ SKU/category và UI báo rõ/ẩn unfilteredscore khi chọn cácfilter đó; KPI/hiệu suất kho vẫnlọcđúng. ChỉTikTok córating, heuristicmentionschưa xác minh, WMS/CRM/stock/HSD/capacity thật unavailable hoặc scenario. Giữ serialSQLguard và nghiệmthu có điều kiện Phase2. ChunkJS khoảng792kB trướcgzip còn cảnh báo; cloud/Docker/CI/production load chưachạy. PDF/ZIP cũ khôngđượctái xuất.

Runbook docs/PHASE3_RUNBOOK.md; frontend/README.md và docs/api/openapi.json đã cập nhật. Reports phase3_api/frontend/browser/layouts/runtime/features_replay/build/acceptance.json là bằng chứng mới; initial reports giữ lỗi đã phát hiện, không dùng thay kết quả cuối.

# Phase 2 backend và DSS

## Phát hành Git theo yêu cầu — 05/11/2026

Người dùng đã yêu cầu commit/push bản Phase2 đã kiểm chứng. Phạm vi phát hành gồm code, tài liệu và QA tổng hợp. Các ghi chú chưa commit/push bên dưới là snapshot trước yêu cầu phát hành này. Điều kiện nghiệm thu vẫn theo PHASE2_ACCEPTANCE.md. Các trường trạng thái Git trong report được ghi tại thời điểm kiểm chứng, không thay cho lịch sử phát hành trên Git.

## Kiểm toán nghiệp vụ sâu — hoàn tất, nghiệm thu có điều kiện, 05/11/2026

Phần này supersede trạng thái61tests và demo2HN/2HCM của lần triển khai ban đầu bên dưới. Đã chạy mới114tests PASS,0fail/0error/0skip;90/90real-history resource scenarios khớp exhaustive oracle,25business methods;68cohort/2108KPI comparisons và20integrity checks PASS;11review audit checks,17axes/1939groups. Full-data18gates, ETL/OLAP16gates, private layers11checks/15Golden tables/56FK reload và replay0raw insert/update PASS. Live HTTP32requests/16checks vàcapabilities7checks PASS.

Đã sửa breakfastdefaultHN với ngoại lệHCM theoSKU/kho/evidence scenario, không dùng wholesale stock choTMĐT, mixedcommercial+gift với explicitgiftstock, malformed/nonoptimal solver guards và input-order invariance. Review gắn unique historicalSKU warehouse tránh fan-out; known future outcome timestamps được loại khỏi scoring, lowstar threshold1/2/3 có sensitivity và missing-review availability rõ.

Trong kiểm thử đồng thời, đường parallel SQL local có12/24query mismatch, mode0 có0/24. API hiện SET LOCAL max_parallel_workers_per_gather=0. Toàn ma trận68cohort và24+16bounded HTTP requests retest khớp trên cấu hình này. Nguyên nhân engine/plan gốc chưa xác định đầy đủ. Giữ guard đến khi điều tra và có regression chứng minh cho phép bật lại.

Rating262/5625<=2sao,194star1,448<=3, độphủ4661/63744TikTokorders7,312%. Labels offline là heuristic chưa có human validation,195/262negative causeUnknown. Source có162literal breakfast linesHN và1744HCM, khác thông lệ mới, cần xác nhận scopeSKU/nhãn kho/hiệu lực. Native storeQuasure chưa tự đổi thànhPleasure. Complaints/replacement workflow, stablecustomer identity, stock/HSD/capacity thực vẫnUNAVAILABLE/scenario.

Kết luận cho người dùng chốt là CONDITIONAL_ACCEPTANCE cho DSS phân tích/mô phỏng có giải thích. Điều kiện vận hành thực và nguyên nhân dữ liệu được công bố trong docs/QA/PHASE2_ACCEPTANCE.md. Source nguyên vẹn, khôngcommit/push. Evidence mới ở reports/phase2_assessment/, reports/phase2_acceptance.json. Không bắt đầuPhase3.

## Trạng thái cuối — 8/8 hạng mục hoàn tất local, 05/11/2026

Phần này supersede các snapshot đang thực hiện và số test cũ bên dưới. Toàn bộ code nằm trong repo này, dùng bibica_repo port55432. Dự án cha chỉ được tham chiếu. HEAD và origin/main được fetch lại cuối task, vẫn cùng8865cf4. Thay đổi Phase2 chưa commit/push.

| Thứ tự | Hạng mục | Kết quả và bằng chứng |
|---|---|---|
|1|Backend API PostgreSQL|src/api, migration040, OpenAPI;32HTTP requests thực HTTP200 |
|2|KPI Contract|M01–M16 thực thi, M17/M18 công bố UNAVAILABLE có lý do; multi-line/NULL/date/filter tests và full-data đối soát PASS |
|3|Phân bổ kho HN/HCM|Whole-order MILP, stock/capacity cả batch, scoped theo shop; chạy allocation trên cả3shop |
|4|Rủi ro bánh ăn sáng/HSD|Remaining life scenario trừ lịch sử p90/extra delay/buffer, empirical threshold exceedance; stress và cutoff PASS |
|5|Fulfillment scoring|Cancellation/late/review factors, n/missing weights/prior/fallback rõ ràng; cả3shop dùng dữ liệu thực |
|6|What-if/Sensitivity|Cùng snapshot, thay weights/stock/capacity/expiry/delay; demo2đơn đổi kho, shelf stress làm4đơn không đủ điều kiện |
|7|Unit/API/Integration|61/61tests PASS,0fail/0error/0skip;18/18full-data assertions;16/16live HTTP assertions |
|8|Tài liệu/đánh giá|KPI_CONTRACT, DSS_ALGORITHMS, DSS_EVALUATION, API_RUNBOOK, OpenAPI, AGENTS và decision log hoàn chỉnh |

Đã nạp lại ETL sau sửa Shopee shipped header. 127588orders/178517items/5625reviews,9175209123VND completed payable,168478completed units giữ nguyên. Bốn raw hashes và ba business fingerprints giữ nguyên. 16/16ETL/OLAP gates,11/11layer checks,15Golden tables/56FK reload và replay0insert/0update PASS. Golden/private processing vẫn ignored.

Regression cuối chạy lúc14:46UTC ngày05/11/2026,61tests trong12.587s. Live HTTP32requests/16assertions chạy trên server mới nạp code cuối, bao gồm allocation/risk/shelf-life của Shopee Bibica, Quasure và TikTok Bibica. Unit/API tests dùng database tự tạo riêng. Cả nguồn review, key linkage và canonical category không đổi.

API đang chạy tại http://127.0.0.1:8001/docs. scripts/start_api.ps1 đã kiểm start/stop/idempotent reuse, actual PID+StartTime được ghi .runtime/api-service.json. Health xác nhận database bibica_repo. Parent API8000 không bị thay thế.

Quyết định tự chọn trong phạm vi được giao gồm binary MILP, default weights0,4/0,4/0,2 và route minimum20samples, historical p90 làm ngưỡng scenario, no-stock mặc định UNASSIGNED. Tất cả tham số có thể đổi qua API. Tồn kho/HSD/capacity/delay và DEMO orders là giả định, không dữ liệu WMS thực. Điểm rủi ro không phải xác suất hiệu chuẩn. Holdout duration cóp90coverage84,91–89,39%, chưa có90%guarantee. Docker/cloud/CI/frontend-browser/concurrency/crash recovery chưa kiểm trong phạm vi này.

Evidence hiện hành ở reports/phase2_tests.json/log, phase2_verification.json, phase2_live_http.json, phase2_demo.json, etl_validation.json, processing_verification.json và phase2_final.json. Báo cáo tổng hợp ở docs/DSS_EVALUATION.md, cách tự kiểm ở docs/API_RUNBOOK.md.

## Lịch sử thực hiện

## 05/11/2026 — Khởi tạo trên repo hiện hành

Đối chiếu Git trực tiếp đã fetch origin/main, HEAD và remote cùng commit 8865cf42358d6601a56625301bb319792191b832. Checkout ban đầu sạch. Dự án cha chỉ được đọc tham chiếu. Không commit hoặc push trong yêu cầu này.

1. Backend PostgreSQL đã có API read-only, snapshot REPEATABLE READ, tham số hóa, OpenAPI, bộ lọc cùng grain, phân trang và allowlist dimension. Migration 040 chỉ bổ sung views/index, giữ nguyên 12dims/3facts/56FK. Đã thực thi migrate_api.py trên bibica_repo và TestClient health/meta/KPI HTTP200. Lỗi cấu trúc query pagination phát hiện tại smoke đã được sửa, cần kiểm lại trong bộ test đầy đủ.
2. KPI Contract M01–M16 đã hiện thực trực tiếp trong SQL theo cùng định nghĩa bản cha. Smoke thực tế 127588orders,178517items,5625reviews, completed payable9175209123VND, units168478. Không dùng old PASS làm kiểm chứng mới. Cần hoàn tất regression nhiều dòng/NULL/filters tại hạng mục7.

Audit phát hiện Shopee shipped time bị bỏ sót vì header decomposed Unicode trong parser. Nguồn thực dùng `Ngày gửi hàng`. Đã sửa exact NFC header, bump version riêng hai Shopee sources. Chưa nạp lại tại thời điểm ghi đoạn này. Không dùng thời gian tạo đơn thay thời gian xuất kho cho mô phỏng hạn dùng.

Tiếp theo thực thi DSS phân bổ, shelf-life, scoring, what-if, kiểm thử và tài liệu. Chỉ báo hoàn tất sau khi kiểm chứng đủ8hạng mục. Raw/private/runtime tiếp tục bị loại khỏi Git.

## Hạng mục3–6 đã hiện thực, kiểm thử đầu tiên

- Phân bổ nguyên đơn bằng binary MILP, scoped kho theo shop, ràng buộc tổng tồn kho SKU và năng lực cả batch. Không tạo lệnh vận hành. Khi thiếu stock mặc định không phân bổ, assume_available phải chọn minh thị.
- Shelf-life trừ p90 thời gian từ gửi đến ghi giao/hoàn thành và trễ kịch bản khỏi hạn dùng còn lại kịch bản. Breakfast cue theo tên chỉ là flag cần kiểm hạn, không suy HSD thực. SQL đếm tỷ lệ thời gian quan sát vượt ngưỡng, có Wilson interval và cảnh báo thiên lệch.
- Scoring kết hợp tỷ lệ hủy snapshot, giao vượt ngưỡng, review thấp, prior theo cùng kho/shop. Thành phần thiếu có effective weight0, không gán rủi ro0. Fallback kho trên mọi tỉnh được ghi rõ.
- What-if và sensitivity đọc cùng snapshot, thay weights, độ trễ, tồn kho, năng lực và hạn dùng, xuất thay đổi phân bổ. Objective khác weights không so delta utility.
-26unit DSS chạy PASS. Toàn suite đầu57tests có2FAIL do fixture kỳ vọng kho nhanh nhất trong khi cấu hình default ưu tiên cả rủi ro hủy. Sửa fixture đặt weight thời gian rõ ràng và thêm case đổi risk/time weight phải đổi kho. Chưa ghi PASS toàn suite tại snapshot này.
- Full process đã chạy lại,0insert/88498raw projections đổi do header gửi hàng được phục hồi; counts127588/178517/5625 và16ETL/OLAP gates PASS. Golden15tables/56FK tiếp tục xuất riêng tư. Cần verifier/replay cuối và báo cáo đánh giá thực.

## Hạng mục7 — Kiểm thử hồi quy đã thực thi

Toàn bộ58unittest chạy PASS,0fail/0error/0skip trong10.776s. Gồm13tests cũ,26unit DSS và19API/safety/integration tests. DB tests tạo/xóa riêng database ngẫu nhiên. Đã kiểm multi-line money, same-line EXISTS, date/NULL/empty, SQL injection, pagination, cutoff review/timing, cross-store keys, shelf stress, MILP so exhaustive search, batch capacity/stock, weight sensitivity và sanitation. Lần chạy thất bại trước được giữ mô tả ở trên, report hiện hành ở reports/phase2_tests.json/log.

Hạng mục8 đang bổ sung đánh giá holdout thời gian và full-data API/DSS, tài liệu công thức/giả định/runbook, kiểm live HTTP. Chỉ sau các bước này mới ghi trạng thái cuối.

Sau khi giới hạn route cohort vào category thương mại, kiểm full-data tái hiện timeout20s do dim_category4rows chưa có planner statistics, estimate lên1250rows và dẫn nested loop không phù hợp. Đã sửa ETL và migrate_api chạy ANALYZE sau load/upgrade, đo riêng profiles giảm xuống0.377s. Thêm regression kiểm stats dimension sau ETL. Báo cáo full-data được đổi sang RUNNING/FAIL khi chưa chạy xong để không giữ PASS cũ nếu có exception. Đang chạy lại toàn bộ gates cuối.
