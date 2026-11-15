# Backend API

## Khởi chạy

Thực hiện tại root repo sau khi cài `requirements.txt` và nạp DW. PostgreSQL phải chạy trước; đặt `BIBICA_DSN` trong terminal, ứng dụng không tự đọc `.env`.

```powershell
$env:BIBICA_DSN='postgresql://warehouse@127.0.0.1:55432/bibica_repo'
.\.venv\Scripts\python.exe -X utf8 scripts/migrate_api.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_api.ps1
```

- API: http://127.0.0.1:8001
- Swagger: http://127.0.0.1:8001/docs
- OpenAPI: `/openapi.json`; bản schema trong [api/openapi.json](api/openapi.json).

Chạy foreground: `python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --no-access-log`.

Script start hỗ trợ `-Python` và `-Port`, ghi PID/StartTime, kiểm health và từ chối chiếm port đang có tiến trình khác. Dừng bằng `scripts/stop_api.ps1`; runtime/log nằm ở `.runtime/`.

## Endpoints

| Method | Route `/api/v1` | Nội dung |
|---|---|---|
| GET | `/meta`, `/kpi-contract` | Danh mục, phạm vi nguồn và định nghĩa KPI |
| GET | `/overview/kpis`, `/overview/dashboard` | KPI và dashboard cùng cohort |
| GET | `/analytics/{dimension}` | Tổng hợp theo chiều được cho phép |
| GET | `/products` | Tìm kiếm, phân trang và xếp hạng SKU |
| GET | `/operations/delivery`, `/quality` | Vận hành và chất lượng pipeline |
| GET | `/customer/review-themes` | Tổng hợp nhãn chủ đề |
| GET | `/customer/review-cases`, `/customer/review-cases/{case_key}` | Danh sách/chi tiết review đã che thông tin |
| GET | `/dss/risk` | Chỉ số tuyến và bằng chứng lịch sử |
| POST | `/dss/allocate`, `/dss/what-if`, `/dss/sensitivity` | Phân bổ và so sánh kịch bản |
| POST | `/dss/shelf-life` | Mô phỏng hạn dùng theo giả định |

`GET /health` kiểm kết nối và read models.

## Hợp đồng truy vấn

Các bộ lọc chung: `start_date`, `end_date`, `source`, `channel`, `store`, `category`, `product_key`, `warehouse_key`, `warehouse_region`, `province`, `status`. Ngày theo cohort đơn đặt, bao gồm cả hai đầu. Các endpoint phân trang có `limit` 1–200 và `offset` 0–100000.

API dùng SQL tham số hóa và allowlist cho dimension/sort; không nhận SQL tự do. Mỗi request đọc snapshot `REPEATABLE READ READ ONLY`, có timeout và guard `max_parallel_workers_per_gather=0`. Giữ guard này vì môi trường local đã tái hiện sai lệch khi bật parallel query; không tự bật lại khi chưa có kiểm chứng hồi quy.

Lỗi tham số trả 422 không echo nội dung nhập; lỗi DB trả 503 không lộ DSN. Tiền decimal được trả dạng chuỗi. API không đọc file nguồn trong request và không ghi lệnh điều phối kho.

## Chuẩn bị review

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/build_review_theme_features.py
.\.venv\Scripts\python.exe -X utf8 scripts/build_review_case_content.py
```

Chạy lại sau khi ETL/rating thay đổi. Nhãn cần khớp source SHA/audit version; nội dung cần khớp source SHA, row hash và content version. Dữ liệu thiếu hoặc hết hiệu lực là unavailable, không tự dùng lại bản cũ. API không trả danh tính khách hay mã đơn gốc.

## Kiểm thử và triển khai

Xem [TESTING.md](TESTING.md). DSS và các giả định được mô tả trong [DSS_ALGORITHMS.md](DSS_ALGORITHMS.md).

Cấu hình hiện hành phục vụ local. Truy cập từ bên ngoài cần bổ sung xác thực, HTTPS, reverse proxy và kiểm thử tải; chưa có chứng nhận vận hành production/WMS.
