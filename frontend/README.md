# Bibica BI & DSS Frontend

React 18 + Vite, Recharts, TanStack Table và CSS. Dữ liệu runtime lấy từ FastAPI/PostgreSQL; fixture chỉ dùng trong test.

## Chạy

Tại root repo, sau khi API và DW sẵn sàng:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
```

Dashboard: **http://127.0.0.1:5174**. Vite chuyển `/api` tới **http://127.0.0.1:8001**. Cách dựng DW và khởi chạy bằng script: [README chính](../README.md).

## Màn hình

| Trang | Nội dung |
|---|---|
| Tổng quan | KPI, xu hướng, cửa hàng, SKU, category; lọc chéo và popup thống kê |
| Sales Performance | Phân tích theo kênh/shop, trạng thái, kho, tỉnh và SKU |
| Warehouse & Fulfillment | Hiệu suất kho, giao hàng và rủi ro tuyến |
| Customer Experience | Điểm sao, chủ đề và đọc từng review tiêu cực đã che thông tin |
| DSS Simulation | Phân bổ đơn, what-if, sensitivity và mô phỏng hạn dùng |

Bộ lọc dùng chung gồm ngày, kênh, cửa hàng, trạng thái, category, tỉnh khách, vùng kho, kho và SKU. Phần DSS có bộ tham số kịch bản riêng.

## Kiểm thử

```powershell
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run e2e
```

- `tests/`: Vitest, React Testing Library và fixture API.
- `e2e/`: Playwright, Microsoft Edge và API/DB thật. Đặt `BROWSER_PATH` nếu cần dùng browser ở đường dẫn khác.

Review Shopee không có nguồn nên hiển thị unavailable. Nhãn review chưa xác minh; nội dung được che thông tin tự động. Tồn kho/HSD/năng lực DSS là giả định kịch bản. Production cần cấu hình reverse proxy `/api` tương ứng; Vite dev chỉ phục vụ local.

Chi tiết vận hành: [BI runbook](../docs/BI_RUNBOOK.md).
