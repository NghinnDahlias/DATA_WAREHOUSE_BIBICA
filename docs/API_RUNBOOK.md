# Chạy backend và kiểm thử DSS

## Database và Python

Repo chạy độc lập với PostgreSQL16+ và Python3.12+. Cài requirements.txt vào môi trường riêng. Trong workspace hiện tại dùng interpreter `D:\Datawarehouse\.venv\Scripts\python.exe`, không có import nào vào dự án cha.

```powershell
Set-Location D:\Datawarehouse\DATA_WAREHOUSE_BIBICA
$env:BIBICA_DSN='postgresql://warehouse@127.0.0.1:55432/bibica_repo'
# Khi chuẩn bị một database repo mới, nạp full ETL trước.
..\.venv\Scripts\python.exe -X utf8 -m DW.etl.run --process --dsn $env:BIBICA_DSN
# Khi DW đã có sẵn, chỉ bổ sung read models mới.
..\.venv\Scripts\python.exe -X utf8 scripts/migrate_api.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_api.ps1
```

API lắng nghe loopback8001. Swagger tại http://127.0.0.1:8001/docs, OpenAPI tại /openapi.json. Bản source OpenAPI đã xuất ở docs/api/openapi.json. API cha8000 không bị thay thế. Chỉ DSN repo được dùng, tên database warehouse của cha bị guard từ chối. `.env.example` là mẫu, cần set environment thật, không tự load file.env.

Lần chạy thực trong task này dùng Silver cache của chính repo đã kiểm SHA nguồn/file/original values, tái tính projection theo header gửi hàng mới. CLI mặc định vẫn đọc4native sources. Không có phụ thuộc cache hoặc module của cha.

API chạy foreground cũng được dùng trên Windows/Linux từ repo root.

```powershell
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --no-access-log
```

start_api.ps1 ghi actual PID và StartTime, kiểm health, không chiếm port đang dùng. Có thể truyền -Python đường dẫn môi trường khác và -Port. Dừng bằng stop_api.ps1, chỉ dừng PID có cùng StartTime đã ghi. Runtime và log nằm ở .runtime/, access log tắt. PostgreSQL phải chạy trước. Không có lệnh xóa database đang tồn tại.

## Các API

| Method | Route | Nội dung |
|---|---|---|
| GET | /health | Kiểm connection và read models |
| GET | /api/v1/meta | Shops, kho scoped,4category, tỉnh, độ phủ ngày quan sát |
| GET | /api/v1/kpi-contract | M01–M16, version và chính sách |
| GET | /api/v1/overview/kpis | KPI trên cohort đã lọc, mẫu số/coverage |
| GET | /api/v1/analytics/{dimension} | source/store/status/month/category/province/warehouse/warehouse_region/product |
| GET | /api/v1/products | Catalog đang có accepted lines, tìm tên và phân trang |
| GET | /api/v1/operations/delivery | Hai duration khác nhau theo từng nguồn |
| GET | /api/v1/quality | Source SHA/parser versions, quarantine và ETL run gần nhất |
| GET | /api/v1/dss/risk | Route-level score thực, factors và sample counts |
| POST | /api/v1/dss/allocate | Phân bổ batch nguyên đơn có điều kiện |
| POST | /api/v1/dss/shelf-life | Bánh ăn sáng/hạn còn lại scenario và exceedance lịch sử |
| POST | /api/v1/dss/what-if | Baseline và một phương án mới |
| POST | /api/v1/dss/sensitivity | Baseline và tối đa8phương án |

Các GET phân tích có chung start_date/end_date/source/store/category/product_key/warehouse_key/warehouse_region/province/status. Ngày order inclusive. limit1–200, offset0–100000 ở endpoints có phân trang. Không có raw SQL endpoint, sort/group chỉ dùng allowlist. Invalid input trả422 không echo nội dung nhập, database bận/lỗi trả503 không lộ DSN. API bind local, chưa triển khai authentication cho remote access.

## Demo tương tác có thể chạy lại

Sau verify_phase2.py, reports/phase2_demo.json chứa inputs hợp lệ trên database full hiện hành, cùng kết quả thật. product_key và warehouse_key là surrogate của database này, lấy từ meta/products khi chạy trên DB khác. DEMO0–DEMO3 là mã nhu cầu mô phỏng, không phải mã đơn nguồn.

```powershell
$demo=Get-Content -Raw -Encoding utf8 reports/phase2_demo.json | ConvertFrom-Json
$body=$demo.inputs | ConvertTo-Json -Depth 40
$bytes=[System.Text.Encoding]::UTF8.GetBytes($body)
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/api/v1/dss/what-if -ContentType 'application/json; charset=utf-8' -Body $bytes
```

Đọc DSS_ALGORITHMS.md trước khi diễn giải kết quả. Stock100units/HSD30days và năng lực khóa một kho là giả định demo. Historical durations/cancellation/reviews lấy từ DW thật. Muốn dữ liệu stock thực cần nguồn WMS/lô hàng riêng có contract, chưa có trong4exports.

## Kiểm thử tái lập

```powershell
$env:BIBICA_TEST_DSN='postgresql://warehouse@127.0.0.1:55432/postgres'
..\.venv\Scripts\python.exe -X utf8 scripts/run_tests.py
..\.venv\Scripts\python.exe -X utf8 scripts/verify_phase2.py
..\.venv\Scripts\python.exe -X utf8 scripts/verify_live_api.py
..\.venv\Scripts\python.exe -X utf8 -m DW.etl.verify --dsn $env:BIBICA_DSN --rerun
```

Tests chỉ tạo/xóa DB ngẫu nhiên do chính chúng tạo, yêu cầu quyền CREATE DATABASE. Thiếu BIBICA_TEST_DSN làm DB tests SKIP và report PARTIAL. Không dùng skip làm full PASS. Full verifier chỉ đọc dữ liệu và ghi aggregate/hash reports. Golden verifier replay ETL trong repo rồi reload15bảng/56FK vào DB riêng mới tạo.

verify_live_api.py yêu cầu server8001 đang chạy, kiểm32HTTP requests cùng16assertions, gồm allocation/risk/shelf-life cả3shop. HTTP được kiểm độc lập với TestClient. API không có application cache, các request đọc snapshot database hiện hành sau ETL.

## Kiểm toán nghiệp vụ bổ sung

```powershell
..\.venv\Scripts\python.exe -X utf8 scripts/assess_integrity.py
..\.venv\Scripts\python.exe -X utf8 scripts/assess_integrity.py --live-capabilities-only
..\.venv\Scripts\python.exe -X utf8 scripts/assess_allocation.py
..\.venv\Scripts\python.exe -X utf8 scripts/assess_reviews.py
```

Ma trận và quyết định readiness ở docs/QA/PHASE2_ACCEPTANCE.md. Raw review text chỉ đọc trong offline audit, controlled labels/aggregate được xuất, API không đọc workbook trong request. Customer, complaints và từng stage replacement có statusUNAVAILABLE/valueNULL trong meta. Shopee review availability có nhãn riêng trên KPI envelope.

Scenario có stock_scopeECOMMERCE/WHOLESALE/UNVERIFIED, breakfast_product_keys và breakfast_exceptions theo SKU/kho. Ngưỡng low_star_max có thể1/2/3. Swagger/OpenAPI và reports/phase2_demo.json chứa schema/input hiện hành. Bánh ăn sáng mặc địnhHN, ngoại lệHCM cần khai đúng evidence scenario, không suy từ lịch sử xuất hàng.

API đặt SET LOCAL max_parallel_workers_per_gather=0 trong mỗi snapshot. Kiểm thực tái hiện local parallel-query mode2 sai lệch12/24 lần ở một cohort, mode0 khớp24/24. Đây là biện pháp đã kiểm trên runtime hiện hành, nguyên nhân engine/plan gốc chưa xác định đầy đủ. Giữ guard này đến khi điều tra và regression chứng minh có thể bật lại. scripts/assess_sql_parallel.py tái lập đối chứng read-only, report sql_parallel_diagnostic.json lưu cả kết quả sai có chủ đích của mode2. Requests HTTP vẫn được xử lý đồng thời, guard chỉ giới hạn parallel workers bên trong từng SQL statement.

Docker/cloud/remote CI/UI browser không nằm trong lần kiểm backend/DSS này. Chưa load-test nhiều người dùng hoặc crash recovery. Giới hạn20giây mỗi SQL statement,3giây chờ lock và10giây solver có thể trả503 thay vì trả kết quả chưa kiểm chứng.
