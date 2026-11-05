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
