# Phase 3 — React BI và điều khiển DSS

Kiểm chứng local ngày 09/11/2026 trên repo `DATA_WAREHOUSE_BIBICA`. Đây là Phase 3 của phân công BI Analyst & Frontend Developer, khác cách đánh số Phase 0–11 trong master prompt dự án tham chiếu.

## Khởi động

PostgreSQL phải chạy trên loopback 55432, database riêng `bibica_repo` đã nạp bằng ETL của repo. Node được kiểm trên bản 22.19.0. Không dùng database `warehouse` của dự án cha.

Từ thư mục gốc repo trong workspace hiện hành:

```powershell
$env:BIBICA_DSN='postgresql://warehouse@127.0.0.1:55432/bibica_repo'
..\.venv\Scripts\python.exe -X utf8 scripts/migrate_api.py
..\.venv\Scripts\python.exe -X utf8 scripts/build_review_theme_features.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_api.ps1
npm --prefix frontend ci
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_frontend.ps1
```

React tại http://127.0.0.1:5174, API/docs tại http://127.0.0.1:8001/docs. Có thể dùng `npm --prefix frontend run dev`; Vite dùng cổng 5174 và strictPort. Cổng 5173 dành cho bản tham chiếu.

Trên checkout độc lập, cài Python dependencies vào môi trường của repo và dùng đường dẫn interpreter tương ứng. Không có import code từ dự án cha. Nếu DW chưa tồn tại, chạy ETL theo README trước khi migrate API.

`start_frontend.ps1` tái sử dụng tiến trình đã sở hữu khi PID và StartTime khớp; cổng bị chiếm bởi tiến trình khác sẽ báo lỗi. Dừng bằng `scripts/stop_frontend.ps1`. API có bộ start/stop riêng cùng cơ chế. Runtime/logs nằm trong `.runtime/`, không đưa vào Git.

## Kiểm thử

```powershell
$env:BIBICA_TEST_DSN='postgresql://warehouse@127.0.0.1:55432/postgres'
..\.venv\Scripts\python.exe -X utf8 scripts/run_tests.py
..\.venv\Scripts\python.exe -X utf8 scripts/verify_phase3.py
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run e2e
```

Backend tests tạo/xóa DB fixture ngẫu nhiên của chính bộ test. Không nạp fixture vào DW đầy đủ. Browser tests cần API và Vite đang chạy, dùng Edge local. Có thể đặt `BROWSER_PATH` và `PHASE3_URL` khi môi trường khác. Vitest chỉ tìm `tests/**/*.test.{js,jsx}`, không chạy nhầm Playwright.

Kết quả thực thi và giới hạn ở [QA/PHASE3_ACCEPTANCE.md](QA/PHASE3_ACCEPTANCE.md). `reports/phase3_api.json`, `phase3_frontend.json`, `phase3_browser.json`, `phase3_layouts.json` là bằng chứng riêng, không cộng số assertions vào số test case.

## Luồng sử dụng

- Overview hiển thị cùng lúc xu hướng, cửa hàng, danh mục và SKU, không chia các khối tổng quan sang tab. Bấm cột/điểm/nhóm hoặc dòng SKU để lọc chéo toàn dashboard; chip cho phép bỏ riêng một chiều. Ba điểm đáng chú ý mô tả tỷ trọng tiền, hủy có mẫu số và tỷ trọng sản lượng; không suy tăng trưởng hoặc nguyên nhân.
- Sales có các tab xu hướng, cửa hàng/trạng thái, danh mục/vùng kho, tỉnh và sản phẩm. Tải ranking khi cần; click hoặc Enter trên dòng sản phẩm để drilldown. Bảng phân trang theo chiều cao, đi cùng biểu đồ phù hợp; chart Top8 được đánh dấu khi bảng có nhiều nhóm hơn.
- Warehouse tách hiệu suất kho, thời gian giao, tỉnh nhận và tuyến kho–tỉnh. Kho giữ khóa theo shop, tỉnh khách độc lập với kho. Mỗi đơn có thể thuộc nhiều nhóm kho nên không cộng số đơn giữa nhóm.
- Customer tách điểm sao/danh mục và chủ đề đánh giá. Biểu đồ rating chỉ hiển thị tối đa 12 tháng gần nhất trong kỳ, theo cohort tháng đặt hàng. Chỉ TikTok có nguồn rating.
- DSS giữ cửa hàng/mốc lịch sử và nút chạy trên màn hình; nhập batch, cấu hình scenario, mô phỏng HSD với giả định và xem kết quả ở các tab. Kết quả tách so sánh và giải thích từng đơn. Tất cả thao tác gọi API thực.
- Bộ lọc thời gian, kênh, cửa hàng, vùng kho, kho scoped, danh mục, tỉnh khách, trạng thái và sản phẩm áp dụng lên KPI và các bảng phân tích. Đổi kênh/cửa hàng xóa lựa chọn SKU/kho không còn phù hợp. Trên mobile mở nút Bộ lọc để chỉnh, đóng lại để xem dữ liệu.

Ma trận risk `/dss/risk` hiện là cohort thương mại toàn shop. Khi chọn SKU/danh mục/trạng thái, tab tuyến báo giới hạn và không trình bày score chưa lọc như thể đã lọc. KPI/hiệu suất kho vẫn dùng đúng bộ lọc. Bộ lọc DSS là các input riêng theo shop và lịch sử, không tự lấy bộ lọc toàn cục của dashboard.

## Review themes và cập nhật dữ liệu

`dw.review_theme_feature` là bảng phụ trợ một review/row, thêm một FK tới fact review. Galaxy chính vẫn 12 dimension, 3 fact và 56 FK; toàn schema DW hiện có 57 FK khi tính bảng phụ trợ. Golden 15 bảng lõi giữ contract riêng, không đồng nhất số bảng core với bảng feature.

Script build đọc nguồn rating immutable trong bộ nhớ và chỉ lưu nhãn kiểm soát, severity, cờ có nội dung, audit version và SHA256 nguồn. Không lưu/đưa nội dung review hoặc thông tin người mua lên API. Tạo lại feature sau khi ETL/rating thay đổi. Toàn bộ thay thế feature nằm trong transaction và khóa advisory chung với ETL.

API chỉ dùng feature có SHA nguồn và audit version hiện hành. Thiếu/cũ/chưa đủ feature trả `UNAVAILABLE_INCOMPLETE_FEATURES`; trường phân tích chủ đề không bị giả thành số 0. Shopee trả `UNAVAILABLE_NO_SHOPEE_RATING_SOURCE`. Có thể phân tích sao độc lập khi feature nội dung chưa sẵn sàng.

Nhãn là `UNVALIDATED_HEURISTIC_MENTION`, một review có thể có nhiều nhãn. Tín hiệu an toàn cần đọc/xác minh; không phải khiếu nại đã xác nhận hoặc nguyên nhân do kho/carrier. Hứa gửi bù, đã gửi, khách nhận và đã giải quyết vẫn chưa có event nguồn để chứng nhận.

## Giới hạn vận hành

Giữ `SET LOCAL max_parallel_workers_per_gather=0`, grain và cùng-dòng EXISTS của Phase 2. SQL song song từng tái hiện sai số ở local; nguyên nhân gốc chưa được chứng minh đã sửa.

Tồn kho/HSD/năng lực/độ trễ trong DSS là input kịch bản. Batch mẫu chọn SKU từ catalog đúng shop, tạo nhu cầu và tài nguyên DEMO, thay batch/scenario đang nhập. Không phải tồn kho hay nhu cầu thực. Ngoại lệ bánh ăn sáng HCM cần bằng chứng scenario và tồn ECOMMERCE, không suy tồn từ lịch sử bán.

Triển khai production cần build và reverse proxy `/api` sang backend. `vite preview` mặc định không phải cấu hình production API proxy. Docker, cloud, remote CI, production load và điều phối WMS thực chưa được kiểm chứng trong lượt này.

## Follow-up hạn chế cuộn

Bản UI mới dùng một scenario/nhóm tham số tại mỗi thời điểm, bảng phân trang theo chiều cao, kho/category trong popup Lọc thêm. Xem QA/SCROLL_OPTIMIZATION.md. Chạy E2E với `$env:QA_REPORT_PREFIX='scroll'` để xuất reports/scroll_browser.json, không ghi đè snapshot ban đầu. Hiện có15browser journeys;34React tests. `scripts/finalize_phase3.py` là rollup snapshot trước follow-up; kiểm UI mới bằng scripts/verify_scroll_ui.py sau khi có các số đo và reports theo hướng dẫn QA.


### Làm rõ SKU và hạn dùng — 10/11/2026

Chọn sản phẩm là chọn một SKU của một shop; xem biến thể/mã SKU nguồn dưới tên. Tìm theo tên, native SKU, seller SKU hoặc biến thể; có phân trang, ưu tiên số đơn trong kỳ. Không cộng gộp SKU theo tên. Tiền KPI là tiền toàn đơn chứa SKU; units là số lượng của SKU đã chọn.

Tab **Mô phỏng HSD** không có HSD thực từ dataset. Không có NSX/HSD/lô hàng để kiểm tra hàng còn hạn. Ô hạn dùng còn lại để trống; phải tự nhập giả định. Thời gian giao lịch sử dùng để mô phỏng đệm hạn dùng, không xác nhận an toàn sản phẩm hay tuổi tồn kho. Nút chạy batch chỉ xuất hiện ở các tab phân bổ/kịch bản/kết quả, không ở mô phỏng HSD độc lập. Batch DEMO vẫn là giả định minh thị.


### Bố cục và lọc chéo — 10/11/2026

API /overview/dashboard giữ KPI, tháng/cửa hàng, danh mục, tỉnh và top8SKU theo sản lượng
trong cùng snapshot read-only. Bấm điểm tháng giữ giới hạn đầu/cuối của khoảng đang xem;
có select tháng để dùng bàn phím. Bấm cửa hàng, danh mục hoặc SKU đặt bộ lọc toàn cục;
chuyển Sales/Kho/Đánh giá giữ cohort. Điểm hủy dùng mẫu tối thiểu30đơn và hiện mẫu số.
Không diễn giải tỷ trọng hoặc tháng đầu/cuối chưa đủ thành tăng trưởng.

Bộ lọc modal có Escape, focus trap, đóng khi bấm ngoài và trả focus. Kho chỉ liệt kê member
của shop/kênh/vùng tương ứng; tỉnh nhận là chiều độc lập. Các token chỉ xóa một chiều;
đổi kênh/shop vẫn xóa SKU/kho không phù hợp. Brand và traffic chưa có trong read model
repo nên không được sao chép thành controls không tác dụng. HSD tiếp tục là giả định.

Kho/tuyến dùng chart số lượng/tỷ lệ/thời gian đúng đơn vị; tuyến4dòng/trang. Chủ đề đánh
giá nhìn chart và bảng cùng lúc; phương pháp mở khi cần. DSS so sánh có chart số đơn gán
kho cạnh bảng đầy đủ chỉ số, không dùng objective khác trọng số để vẽ lợi ích giả.
Các lưu ý KPI ở icon thông tin/title, lỗi và unavailable không bị che đi.
