# Tối ưu hiển thị và hạn chế cuộn — 09/11/2026

Phạm vi là React trong repo `DATA_WAREHOUSE_BIBICA`, chạy tại5174 với API8001. Giữ toàn bộ thay đổi Phase3 đang có, không thay query/KPI/ETL/DSS engine, không commit/push. Bằng chứng UI mới supersede phần bố cục/source hashes của snapshot PHASE3_ACCEPTANCE.md trước tối ưu này.

## Thay đổi

- Bộ lọc desktop thu về một hàng. Kho/vùng/danh mục nằm trong bảng mở nhanh, giữ trạng thái đang lọc, nút Xong và phím Escape. Mobile vẫn có mở/đóng bộ lọc.
- KPI, tiêu đề và khoảng cách nhỏ hơn. Ghi chú dài vẫn có tooltip/nội dung truy cập; không xóa định nghĩa hay thay số liệu.
- Chủ đề review có các tab Biểu đồ, Bảng chi tiết, Phương pháp. Giữ số lượng, review tiêu cực, tín hiệu an toàn và cảnh báo heuristic chưa xác minh; không lặp biểu đồ và bảng nối dọc.
- Chỉnh một kịch bản DSS tại một thời điểm, chia nhóm Tồn kho/HSD, Năng lực/Giới hạn, Điểm rủi ro và Ngoại lệ. Trạng thái tham số nằm ở parent nên chuyển tab không mất dữ liệu. Form năng lực tận dụng hai cột, các input phụ không chen vào màn tồn kho.
- Bảng tự chọn3–10dòng/trang theo chiều cao panel. Tuyến kho–tỉnh5dòng/trang. Batch DSS4đơn/trang; dòng tồn kho3dòng/trang; kết quả phân bổ5đơn/trang. Toàn bộ dữ liệu vẫn được gửi tới DSS, không chỉ gửi trang đang thấy.
- Giải thích phân bổ chọn từng kịch bản thay vì xếp các bảng ứng viên nối dọc. Phần phương pháp/giới hạn và chẩn đoán dài mở khi cần. Cảnh báo số đơn chưa gán vẫn hiện.
- Biểu đồ tỷ lệ hủy kho là phần mở thêm bên cạnh bảng số liệu, không chiếm thêm một khối cao mặc định.

## Kiểm chứng đã chạy

| Phần | Kết quả |
|---|---|
| React/components |34/34 PASS, reports/scroll_frontend.json |
| Edge dùng API/DB thực |15/15 PASS,0skip/flaky, reports/scroll_browser.json |
| Tab chính |54 lượt xem trên1366×768,1280×720,1846×867; so sánh cùng route/tab/kích thước trước/sau |
| Nội dung mở sâu |51 panel PASS, gồm3nhóm review,3scenario×4nhóm tham số và2panel kết quả trên mỗi desktop |
| Build |Vite build thực, log .runtime/scroll-build.log; còn cảnh báo bundle lớn như trước |
| KPI/API |scripts/verify_scroll_ui.py đối chiếu full-data KPI và source hashes API/DSS với baseline Phase3 |

Bộ đo trước có41panel vượt chiều cao trong54lượt xem, độ tràn lớn nhất1300px. Sau tối ưu các panel chính trong cùng bộ đo không cần cuộn; sai số làm tròn tối đa1px ở lần đo. Không chỉ kiểm chiều cao document hoặc ẩn thanh cuộn để báo đạt: report giữ clientHeight/scrollHeight cho từng panel và kiểm riêng51trạng thái mở sâu với tolerance4px.

Browser tests giữ12journey Phase3 trước đó và thêm3journey: đo phần mở sâu, chuyển scenario/nhóm không mất input và kiểm payload thực, thêm/xóa đơn qua phân trang không mất batch. Bộ kiểm đầu có14/15PASS và phát hiện form năng lực tràn12px; đã sửa bố cục và chạy lại. Có giữ reports/scroll_browser_initial.json và log chẩn đoán trong.runtime.

Xem reports/scroll_comparison.json, scroll_detail_layouts.json, scroll_layouts.json và scroll_acceptance.json để lấy số đo/current hashes. Ảnh thực nằm trong.runtime/scroll-customer-chart.png, scroll-customer-table.png, scroll-dss-stock.png, scroll-dss-capacity.png và scroll-dss-explanation.png.

## Giới hạn và runtime

Kết quả layout áp dụng các cohort thật và DEMO đã kiểm. Tên SKU/giải thích rất dài, nhiều dòng sản phẩm và màn hình hẹp vẫn có thể cần cuộn cục bộ hoặc chuyển trang. Giữ font số liệu đọc được; không khẳng định mọi dữ liệu có thể hiện đồng thời.

Trong kiểm thử đã quan sát API không trả `/health` trong30giây. PostgreSQL kết nối trực tiếp0,02giây, không có session API đang chạy trong DB ở thời điểm chẩn đoán. Đã stop/start đúng API thuộc repo theo PID+StartTime; sau đó health200~0,30giây và KPI200~0,42giây. Nguyên nhân gốc chưa xác định; tối ưu UI không được coi là đã sửa sự cố backend này. Chi tiết reports/scroll_runtime_recovery.json. Bộ15journey cuối được chạy lại trên API đã phục hồi.

Không chạy lại ETL, backend116tests hoặc tái xuất Golden/PDF/ZIP trong lượt chỉ sửa UI. Không dùng kết quả test backend cũ như lần chạy mới. Các giới hạn Phase2 về stock/HSD/khiếu nại thực, review chỉ TikTok và SQL serial guard vẫn giữ nguyên. Không có chứng nhận cloud/production/concurrency/load từ các phép kiểm này.

Chạy lại từ root repo sau khi API/frontend đã chạy:

```powershell
npm --prefix frontend test -- --reporter=json --outputFile=../reports/scroll_frontend.json
$env:QA_REPORT_PREFIX='scroll'
npm --prefix frontend run e2e
npm --prefix frontend run build
```

Để xác minh số đo trước/sau, dùng bản đo đã lưu trong reports/scroll_comparison.json. Helper đo tại.runtime/measure_scroll.cjs là công cụ local của lượt kiểm; browser tests trong frontend/e2e/scroll.spec.js là phần kiểm tái lập được đi cùng source.
