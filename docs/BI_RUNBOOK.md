# BI Dashboard và DSS

## Chạy giao diện

Cần PostgreSQL có DW và API đã sẵn sàng. Tại root repo:

```powershell
npm --prefix frontend ci
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_frontend.ps1
```

Dashboard: http://127.0.0.1:5174. `npm --prefix frontend run dev` chạy Vite trên cùng port. Dừng bằng `scripts/stop_frontend.ps1`.

Vite chuyển `/api` sang `http://127.0.0.1:8001`. Có thể đặt `BIBICA_API_PROXY` trong terminal để dùng backend local ở port khác; script frontend hỗ trợ `-Port`. Production cần reverse proxy tương ứng.

## Sử dụng

| Màn hình | Thao tác chính |
|---|---|
| Tổng quan | Lọc chéo từ biểu đồ/SKU, bỏ từng chip, mở Thống kê chỉ số |
| Sales Performance | Đổi measure, phân nhóm, xem category/kho/tỉnh và ranking SKU |
| Warehouse & Fulfillment | Xem hiệu suất, thời gian giao, địa lý và bằng chứng tuyến |
| Customer Experience | Chọn KPI/tab/chủ đề tiêu cực để đọc từng case, lọc mức sao và phân trang |
| DSS Simulation | Nhập batch và tài nguyên kịch bản, chạy phương án gốc/what-if/sensitivity |

Bộ lọc dùng chung: ngày tạo đơn, kênh, cửa hàng, trạng thái, category, tỉnh khách, vùng kho, kho và SKU. Kho được giới hạn theo shop; tỉnh khách là chiều độc lập. DSS có bộ tham số cửa hàng/cutoff/kịch bản riêng.

## Review tiêu cực

Mặc định 1–2 sao, có thể chọn 1 hoặc 1–3 sao. Chủ đề là nhãn từ khóa, không phải kết luận khiếu nại hay nguyên nhân. Danh sách bốn case mỗi trang và nội dung bên cạnh; review chỉ chấm sao ghi rõ không có ý kiến.

Nội dung được chuẩn bị offline từ review đã chấp nhận, che tự động thông tin cá nhân và phục vụ qua DB. Không có dữ liệu review Shopee. Việc che tự động có thể xóa từ hữu ích hoặc bỏ sót cách diễn đạt chưa nhận diện; không thay thế kiểm duyệt thủ công.

## Quy ước hiển thị

- Tiền hoàn thành/AOV dưới bộ lọc SKU vẫn là tiền toàn đơn chứa SKU, không phải doanh thu được phân bổ cho SKU.
- Giữ NULL và kỳ thiếu dữ liệu; không tự điền 0 hoặc tính tăng trưởng khi chưa có contract.
- Risk tuyến chưa hỗ trợ cohort SKU/category/status nên không hiển thị score toàn shop dưới các bộ lọc đó.
- Mô phỏng HSD cần nhập giả định; dataset không có NSX/HSD/lô hàng.
- Desktop ưu tiên một workspace, bảng phân trang; nội dung dài và mobile có thể cuộn trong panel.

## Kiểm thử

```powershell
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run e2e
```

Playwright cần Microsoft Edge và API/DB thật. Đặt `BROWSER_PATH` nếu browser ở đường dẫn khác; `PHASE3_URL` chỉ định URL frontend khi kiểm thử ở port khác.

Các lỗi/giới hạn DB và KPI: [API_RUNBOOK.md](API_RUNBOOK.md), [KPI_CONTRACT.md](KPI_CONTRACT.md).
