# Nghiệm thu Phase 3 BI và React frontend — 09/11/2026

> UI/source hashes và số browser tests của snapshot này đã được supersede bởi [tối ưu cuộn](SCROLL_OPTIMIZATION.md), reports/scroll_acceptance.json. Giữ bản này làm lịch sử kiểm chứng Phase3 ban đầu.

**PASS cho các luồng local đã kiểm, kèm giới hạn dữ liệu/vận hành công bố dưới đây.** Đã fetch và fast-forward từ `be9117a` đến `96941fb70b135f72d040b6fe996421f465936eb6`, gồm 4 commit mới. Fetch cuối lượt vẫn xác nhận HEAD bằng origin/main. Các bản sửa và kiểm thử trong lượt này nằm local, chưa commit/push.

Phạm vi là repo con `DATA_WAREHOUSE_BIBICA`, PostgreSQL `bibica_repo:55432`, API 8001, React 5174. Không thay code/schema của dự án tham chiếu. Nguồn native bất biến, không xuất buyer data/raw review text. Đây là Phase 3 của phân công BI/frontend, không phải chạy lại Phase 3 ingestion của master prompt.

## Bằng chứng mới

| Kiểm tra đã thực thi | Kết quả | Tệp bằng chứng |
|---|---|---|
| Backend/DW/DSS/API regression |116/116 PASS, 0 failure/error/skip |reports/phase2_tests.json và log, lần chạy mới ngày09/11 |
| React/adapter/component |34/34 PASS |reports/phase3_frontend.json |
| Build production |PASS, Vite tạo dist thực |reports/phase3_build.json, .runtime/phase3-build.log |
| Browser Edge dùng API/PostgreSQL thật |12/12 PASS, 0 skip/flaky |reports/phase3_browser.json |
| Full-data API/KPI/source/FK |34/34 checks PASS, 27 requests |reports/phase3_api.json |
| Geometry 5 trang × 4 kích thước |20/20 vừa workspace viewport, không tràn ngang trang |reports/phase3_layouts.json |
| Nạp lại nhãn review |5625 rows, fingerprint logic trước/sau giống nhau |reports/phase3_features_replay.json |
| Runtime start/reuse/stop/restart |PASS, UI HTTP200 và API đúng bibica_repo |reports/phase3_runtime.json |
| Python compileall và git diff whitespace |PASS |reports/phase3_acceptance.json |

Unit tests dùng fixture và browser tests dùng dữ liệu thực là hai loại bằng chứng khác nhau. 34 API checks không phải 34 browser journeys. Geometry nằm trong một browser test và không cộng 20 measurements vào số test case.

Lần test đầu có27/29 frontend PASS. Các lỗi/selector cũ được giữ ở phase3_frontend_initial.json và phase3_browser_initial.json. Chuyển sang tab cũng đã được kiểm lại với các thao tác chọn tab thực; không dùng báo cáo trước đổi bố cục để chứng nhận bản sau.

## Đối chiếu công việc

| Yêu cầu | Kết quả kiểm thực tế |
|---|---|
| Dashboard React |5 route Overview/Sales/Warehouse/Customer/DSS dùng cùng API layer; smoke qua cả5, không có JavaScript exception |
| Sales Performance |KPI đơn, units hoàn thành, tiền đơn đúng grain; xu hướng theo kênh/shop; toggle chỉ tiêu, ranking, Enter/click drilldown SKU và picker scoped |
| Warehouse & Fulfillment |Hiệu suất/hủy theo6 kho scoped; thời gian theo nguồn giữ khác biệt Shopee proxy/TikTok delivery; tỉnh nhận và pagination tuyến; warehouse/date cohort khớp SQL EXISTS độc lập |
| Customer Experience |5625 reviews,262 review≤2 sao; mean/rate/coverage và danh mục; nhãn nội dung một review/row; Shopee công bố unavailable |
| Màn hình điều khiển DSS |Nhập batch/tài nguyên/tham số; allocate, what-if, sensitivity và shelf-life gọi API200 tại cả3shop; mở giải thích ứng viên; đổi ngày xóa kết quả HSD cũ |
| Filter |Ngày, kênh, cửa hàng, vùng kho, khóa kho, category, product; reset; kênh Shopee gồm2shop; đổi shop/kênh bỏ SKU/kho cũ; mobile mở/chỉnh/đóng bộ lọc |
| Tích hợp/UX |Empty state và503 không giữ KPI cũ như kết quả hiện tại; chống phản hồi tìm kiếm cũ; tab bàn phím; bảng dài phân trang; sidebar thu gọn và nút chạy DSS luôn truy cập được |

Risk tuyến hiện dùng cohort thương mại toàn shop. Nếu chọn SKU/danh mục, UI ẩn bảng risk chưa lọc và báo rõ giới hạn; không khẳng định endpoint này đã hỗ trợ cohort SKU. KPI/hiệu suất kho phía trên vẫn áp dụng bộ lọc. DSS có input shop/lịch sử riêng, không tự áp dụng filter toàn cục dashboard.

## Lỗi đã sửa

1. Batch mẫu gắn cứng key1365, có thể dùng nhầm SKU khi đổi shop hoặc DB có surrogate keys khác. Nay chọn sản phẩm thương mại từ catalog đúng shop/mốc lịch sử; ưu tiên tên breakfast khi có. Không tạo sản phẩm giả để đạt kết quả.
2. Test/demo lệch số scenario và endpoint; đã khôi phục baseline, ngoại lệ HCM và stress HSD, kiểm cả single/what-if/sensitivity. Tồn kho/HSD/capacity/evidence DEMO được ghi rõ là giả định.
3. Script feature gọi trực tiếp lỗi import DW. Đã sửa entry point, transaction/advisory lock, thêm SHA nguồn và kiểm audit version. Feature thiếu/cũ trả unavailable, không biến thành không có nội dung/không có vấn đề.
4. Truy vấn tháng và adapter biến tiền thiếu/tháng không có dòng thành0. Nay giữ NULL; nguồn/kỳ không quan sát không được dựng số0.
5. Kênh và shop bị gộp; nhãn Kho chỉ lọc vùng. Nay có channel filter API riêng và warehouse_key theo shop, giữ cùng-dòng EXISTS.
6. Bảng risk không áp dụng SKU/category nhưng trước đó vẫn hiện dưới bộ lọc. Nay công bố cohort chưa hỗ trợ và ẩn kết quả có thể gây hiểu nhầm.
7. Error sau reload có thể giữ dữ liệu cũ; tìm kiếm picker có thể nhận response cũ; sửa cả hai. Khóa thao tác form trong lúc DSS chạy để input không thay trước khi response về.
8. Sửa nhãn truy cập/select, thêm thao tác Enter trên bảng drilldown, tab có bàn phím, phân trang và bộ lọc mobile. jsdom31 không tương thích Node22.19 local được thay bằng jsdom26.1; Playwright nằm trong dependencies repo để tái lập.
9. UI mới dài1400–2600px ở desktop. Nay bỏ hero/copy thừa, giữ KPI, chia nhóm phân tích và bước DSS thành tab, sidebar mặc định thu gọn. Giữ nguyên các panel/API tốt sẵn có.

## Dữ liệu và mô phỏng

Không đổi127588 orders,178517 accepted item lines,5625 reviews; completed order payable **9.175.209.123 VND**, completed units **168.478**. Cả3 business fingerprints khớp baseline và SHA256 của4native sources khớp nguồn đăng ký. Data tree không thay đổi so với bản Phase2.

Galaxy lõi vẫn12dims/3facts/56FK. Phase3 bổ sung bảng phụ trợ `review_theme_feature` với1FK, nên toàn schema có57FK; không gọi bảng phụ trợ này là fact/dimension kinh doanh mới. Golden15 bảng lõi giữ contract riêng. Không chạy lại full native ETL/Golden export trong lượt UI này; đã chạy regression fixture, full-data read reconciliation và nạp/replay feature thực.

Nhãn nội dung được tạo đủ5625review và nạp lại cho cùng fingerprint logic. Có55 packaging mentions,22 missing-items,16 product-breakage,11 spoilage/expired; nhãn có thể chồng lấp và gồm cả rating tốt. Đó là heuristic mentions, không phải incident hay nguyên nhân đã xác nhận.

Demo TikTok đang lấy SKU breakfast từ catalog. Baseline phục vụ4/4đơn từHN; khi thay tồn/capacity và khai ngoại lệ ECOMMERCE,4/4đơn từHCM; stressHSD làm0/4đơn đủ điều kiện. Đó là thay đổi đầu ra trong giả định, không chứng minh đã hết hàng hay đã điều phối đơn thật. Cả3shop đã gọi đủ4nhóm endpoint trong browser tests, không ép mọi shop phải có kết quả phân bổ giống nhau.

## Kiểm tra bố cục và giới hạn

Đã đo1366×768,1280×720,1846×867 và390×844 trên cả5trang. Trang nằm trong viewport, không tràn ngang document. Số liệu clientHeight/scrollHeight của panel được giữ trong report, không dùng việc khóa body scroll để tuyên bố mọi nội dung đều hiện cùng lúc. Các bảng/giải thích/form dài cuộn trong panel; mobile và desktop thấp có thể cần cuộn panel. Toàn bộ tab đã được chuyển và kiểm còn truy cập được. Đã xem ảnh thật Overview, Customer, DSS, kết quả, tham số và chủ đề review trong `.runtime/phase3-*.png`.

Các giới hạn còn lại:

- Shopee không có nguồn rating. Không coi số0 quan sát là không có khiếu nại.
- Nhãn chủ đề chưa có human validation. Chưa có CRM complaint/replacement events để đo hứa, gửi, nhận và giải quyết.
- DSS là mô phỏng, chưa có tồn/lô/HSD/capacity/giữ chỗ WMS thật. Giữ điều kiện nghiệp vụ và hạn chế Phase2 trong PHASE2_ACCEPTANCE.md, gồm breakfast policy và Quasure/Pleasure.
- Giữ SQL serial guard. Root cause của sai lệch parallel query local chưa được chứng minh đã giải quyết.
- Biểu đồ rating chỉ tối đa12tháng gần nhất trong kỳ, theo cohort ngày tạo đơn. Maturity30ngày là tùy chọn xem, không xác nhận mọi đơn đã có kết quả cuối.
- Build còn cảnh báo chunk JavaScript khoảng792kB trước gzip. Local load đã kiểm; chưa benchmark mạng yếu/production hoặc xác nhận code splitting tối ưu.
- Docker/cloud/remote CI, production deployment/load, solver concurrency và crash recovery chưa chạy. PDF/ZIP cũ không phải package của Phase3 này.

Hướng dẫn chạy và làm mới nhãn ở [PHASE3_RUNBOOK.md](../PHASE3_RUNBOOK.md). Kết luận local không thay thế nghiệm thu vận hành thật hoặc quyền push/publish dữ liệu riêng tư.
