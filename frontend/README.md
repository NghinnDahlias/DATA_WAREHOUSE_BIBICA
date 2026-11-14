# Bibica React Dashboard và DSS

React 18, Vite, Recharts và API FastAPI của chính repo. Overview là dashboard liên kết trên một màn hình; các trang chuyên sâu dùng cặp biểu đồ–bảng, sidebar thu gọn, bộ lọc dùng dữ liệu DW và điều khiển DSS thực. Không có mock runtime.

## Chạy trong workspace hiện tại

Tại root `DATA_WAREHOUSE_BIBICA`, PostgreSQL `bibica_repo` trên 55432 phải đã có dữ liệu ETL.

```powershell
$env:BIBICA_DSN='postgresql://warehouse@127.0.0.1:55432/bibica_repo'
..\.venv\Scripts\python.exe -X utf8 scripts/migrate_api.py
..\.venv\Scripts\python.exe -X utf8 scripts/build_review_theme_features.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_api.ps1
npm --prefix frontend ci
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_frontend.ps1
```

Giao diện http://127.0.0.1:5174, API http://127.0.0.1:8001/docs. `npm --prefix frontend run dev` cũng dùng cổng 5174. Trên môi trường độc lập, cài requirements vào venv repo và thay interpreter cho phù hợp.

## Kiểm thử

```powershell
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run e2e
```

Vitest dùng fixture API để kiểm component/adapter. Playwright dùng Edge, backend và PostgreSQL thực; cần khởi động hai dịch vụ trước. Đặt `BROWSER_PATH` khi Edge nằm ở vị trí khác. Kết quả thực tế nằm ở `../reports/phase3_*.json` và báo cáo [nghiệm thu](../docs/QA/PHASE3_ACCEPTANCE.md).

## Phạm vi

| Màn hình | Nội dung |
|---|---|
| Tổng quan | KPI, xu hướng, cửa hàng, danh mục, SKU và điểm đáng chú ý; bấm biểu đồ/dòng để lọc chéo |
| Sales Performance | Đơn/units/giá trị hoàn thành, xu hướng kênh/shop, trạng thái, tỉnh, ranking và drilldown SKU |
| Warehouse & Fulfillment | Hiệu suất kho scoped, hủy đơn, thời gian giao theo nguồn, tỉnh và risk tuyến |
| Customer Experience | Rating TikTok, tỷ lệ thấp/coverage, xu hướng tối đa 12 tháng, danh mục và nhãn nội dung |
| DSS Simulation | Batch, stock/capacity/weights/expiry/delay, allocate/what-if/sensitivity, mô phỏng HSD với giả định và giải thích |

Giữ NULL và tháng thiếu, không tự điền 0. M03 là thanh toán quan sát của đơn COMPLETED, không phải net revenue. M17 tăng trưởng chưa có contract. Rating Shopee thiếu nguồn là unavailable. Nhãn nội dung chưa được xác minh thủ công và không phải incident/quan hệ nhân quả đã xác nhận.

Bộ lọc kênh tách khỏi cửa hàng; kho tách khóa scoped khỏi nhãn vùng. Khi chọn SKU/danh mục/trạng thái, bảng risk tuyến công bố chưa hỗ trợ cohort này thay vì trình bày score toàn shop dưới bộ lọc. Các KPI và hiệu suất kho vẫn được lọc đúng.

DSS dùng input tài nguyên giả định; mẫu DEMO lấy SKU động từ catalog của shop đang chọn. Khung làm việc ở trong viewport, danh sách/chi tiết dài cuộn trong panel; mobile có bộ lọc đóng/mở. Đây không phải giao diện WMS hay cơ chế giữ chỗ tồn kho.

Hướng dẫn chi tiết, refresh feature, giới hạn và commands tại [PHASE3_RUNBOOK](../docs/PHASE3_RUNBOOK.md). Production cần reverse proxy `/api`; Vite dev được kiểm local, chưa triển khai cloud.

Bản tối ưu cuộn mới được kiểm riêng tại [SCROLL_OPTIMIZATION](../docs/QA/SCROLL_OPTIMIZATION.md). Phần tham số DSS chọn từng kịch bản và nhóm; kho/danh mục trong Lọc thêm; bảng tự phân trang theo chiều cao. Các ghi nhận12browser tests ở snapshot cũ được thay bằng15journeys hiện hành; số liệu API giữ nguyên.


Giao diện phân tích liên kết được kiểm chứng trong docs/QA/LINKED_DASHBOARD.md.
Bộ lọc chuyên sâu có cửa hàng, danh mục, trạng thái, tỉnh khách, vùng kho, kho theo shop
và SKU; ngày/kênh/khoảng nhanh nằm trên thanh chính. Bỏ từng chip để lùi bước phân tích.
/overview/dashboard trả các khối trên cùng snapshot REPEATABLE READ. Các chiều brand/
traffic chưa có trong read model của repo được giữ ngoài UI, không thêm bộ lọc giả.
