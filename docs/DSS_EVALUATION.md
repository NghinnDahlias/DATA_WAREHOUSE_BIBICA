# Đánh giá Phase2 — 05/11/2026

## Nghiệm thu nghiệp vụ mới

Đánh giá mở rộng hiện hành ở [PHASE2_ACCEPTANCE.md](QA/PHASE2_ACCEPTANCE.md) và các báo cáo QA đi kèm. 114tests,90scenario oracle,68cohort/2108measures,20integrity assertions và11review assertions đã chạy mới. Kết luận có điều kiện cho phân tích/mô phỏng. Breakfast defaultHN và SQL serial guard supersede hành vi demo trước đó. Các kết quả phần dưới là snapshot lần triển khai ban đầu, giữ cho truy vết, không thay evidence nghiệm thu mới.

## Snapshot triển khai ban đầu

Các kết quả dưới đây lấy từ lần chạy mới trong reports/phase2_tests.json, phase2_verification.json, etl_validation.json và processing_verification.json. Các báo cáo Phase1 hoặc refinement04/11được giữ làm lịch sử, không thay thế bằng chứng mới.

## Kết quả thực thi

| Phần | Kết quả |
|---|---|
| Automated regression | 61/61PASS,0fail/0error/0skip,13DW cũ +26DSS +22API/safety/integration |
| Full-data API/DSS |18/18assertions PASS, fingerprints orders/items/reviews giữ nguyên |
| ETL/OLAP |16/16gates PASS,127588orders/178517items/5625reviews |
| Raw/Silver/Golden |11/11checks PASS,15tables/56FK reload database mới riêng, replay0raw insert/update |
| Nguồn gốc |4native SHA256 giữ nguyên; quarantine315sales+66review duplicate+6invalid review |
| Category/địa lý |4category chuẩn,6warehouse members theo3shop, tỉnh khách độc lập |
| Review linkage |4870historical-name SKU links và755order-only |
| Runtime |32HTTP requests/16assertions PASS trên loopback8001, allocation/risk/shelf-life cả3shop |

KPI vẫn9175209123VND completed order payable và168478completed units. Số đơn93877COMPLETED và19230CANCELED trong127588orders. Tổng payable không nhân theo178517lines. Có957refund conflicts, không biến chúng thành hoàn tiền0 hoặc làm mất denominator orders.

## Hai lỗi tìm được và đã sửa

Shopee shipped field trước đây bị bỏ sót vì literal header decomposed không khớp header NFC của reader. Đã sửa `Ngày gửi hàng`, bump version riêng hai nguồn Shopee, tái xử lý88498sanitized projections thay đổi, xuất lại Golden và kiểm replay/reload. Đối soát fingerprints đầy đủ xác nhận tiền/quantity/status/Category/kho/tỉnh/reviews không đổi. Fingerprint cũ không gồm trường shipped vừa sửa nên coverage shipped được kiểm riêng.

Khi route cohort giới hạn đúng category thương mại, dimension nhỏ chưa được ANALYZE làm PostgreSQL ước lượng sai4category thành1250rows, query full-data timeout20s. ETL và upgrade script đã thêm ANALYZE sau load. Truy vấn profiles đo lại0.377s ở lần chẩn đoán, toàn full verifier sau sửa PASS. Có regression kiểm statistics dimension. Không coi timeout trước đó là thành công.

## Thời gian có thể quan sát

| Nguồn | Đơn có thời gian tạo→ghi giao | Đơn có duration gửi→ghi giao hợp lệ | Mean gửi→ghi giao, ngày |
|---|---:|---:|---:|
| Shopee Bibica |44382|43939|3,3560|
| Shopee Quasure |8214|8090|3,3738|
| TikTok Bibica |54037|54035|1,6476|

Đây là các tập có ghi nhận thời gian, khác denominator mọi đơn. Shopee completion proxy và TikTok Delivered Time không được gộp thành cùng một SLA vận chuyển. M13 đa nguồn trả NULL, bảng delivery trả từng nguồn. Dataset không đủ để định danh parcel hoặc kiểm ngày hỏng/hết hạn thực tế.

## Holdout theo thời gian

Train chỉ dùng đơn tạo và ghi giao đến hết01/09/2026. Test là đơn tạo từ02/09đến ngày cuối quan sát của từng nguồn. Chỉ đánh giá duration hợp lệ ở cohort thương mại. Mỗi route dùng median/p90 train nếu>=20mẫu, thiếu thì fallback cùng kho/shop. Baseline dùng median kho trên mọi tỉnh.

| Store | Test được chấm | MAE median tuyến, ngày | MAE baseline kho, ngày | Tỷ lệ test<=p90train |
|---|---:|---:|---:|---:|
| Bibica Shopee |5784|1,3096|1,3905|88,33%|
| Bibica TikTok |10146|0,3688|0,6763|84,91%|
| Quasure Shopee |1744|1,2953|1,4070|89,39%|

Thống kê tuyến giảm sai số duration so baseline kho trong các tập test đã quan sát. P90train không đạt90%coverage trên cả ba tập test, đặc biệt TikTok chỉ84,91%. Vì vậy p90 được dùng làm tham số lịch sử cho scenario, không chứng nhận90%giao đúng hạn hoặc an toàn HSD. Khả năng drift, thiếu outcome và khác biệt snapshot còn hiện hữu. Không chọn split/weight theo kết quả test rồi tuyên bố đã có calibration.

Risk score không được báo AUROC, failure probability hoặc accuracy dự báo vì không có dữ liệu point-in-time đủ mạnh và nhãn fulfillment failure nhất quán. Hủy có thể từ người mua, review thấp có thể do sản phẩm, nên hai tín hiệu này không chứng minh lỗi của kho. Counterfactual chuyển kho cho cùng đơn không được quan sát.

## Demo scenario trên lịch sử thật

Catalog SKU1365 trong database kiểm chứng là Combo Bánh Ăn Sáng Bibica. Đơn DEMO0–DEMO3 là nhu cầu giả định đến Hà Nội/Hồ Chí Minh/Đồng Nai/Hải Phòng, mỗi đơn2units. Stock100units/kho, HSD còn30ngày là giả định nhập rõ.

- Baseline phân bổ4/4đơn,2HN và2HCM. Mean historical rule score7,6479/100, mean route p90 dùng trong scenario1,5372ngày. Các giá trị này không phải rủi ro xác suất hay thời gian giao cam kết.
- Khóa năng lực HN về0 trong scenario làm2đơn đổi sangHCM, vẫn phục vụ4đơn. Cả batch vẫn tuân thủ tồn kho/capacity/whole-order constraints.
- Cho cả hai kho trễ thêm4ngày và chỉ còn5ngày HSD, buffer1ngày làm0/4đơn đủ điều kiện. Hệ thống trả4UNASSIGNED thay vì ép chọn một kho.
- Sensitivity chạy cả weight thời gian0/1 và capacity/shelf scenarios trong cùng snapshot. Fixture độc lập chứng minh thay risk/time weight có thể đổi kho, không hardcode mọi phương án phải đổi.

Input, factors, từng candidate và baseline/alternative thực tế có trong reports/phase2_demo.json. Đây là kiểm chứng phần mềm trên data lịch sử + assumption scenario, chưa phải thử nghiệm điều phối đơn ngoài thực địa.

## Hiệu năng và phạm vi kiểm chứng

Lần full verifier cuối đo TestClient meta0,193s, KPI0,193s, allocate0,520s, what-if1,026s, sensitivity3alternatives2,069s, shelf-life0,948s, risk0,605s. Đây là một lần chạy local, không phải benchmark tải nhiều người dùng. Live HTTP được kiểm riêng với32requests/16assertions PASS và ghi reports/phase2_live_http.json.

Unit MILP được so với exhaustive search cho batch nhỏ, kiểm aggregate stock/capacity, expiry boundaries, thiếu bằng chứng, gift/Unmapped exclusion, cross-store và repeatability. API kiểm cùng-dòng EXISTS, NULL/empty, dates inclusive, reviews/timing cutoff, SQL injection, sanitized503/422, read-only transaction và pagination. Các báo cáo chỉ có aggregates/hash/catalog thông thường, không buyer IDs/raw review text.

Frontend/browser, Docker/cloud/remote CI, authentication remote, crash recovery và tải đồng thời chưa được kiểm trong scope này. PDF/ZIP cũ của dự án cha không xác minh backend/DSS mới. Code/docs giữ local cho người dùng kiểm lại.
