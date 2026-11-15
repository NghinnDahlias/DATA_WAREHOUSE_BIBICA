# Bibica Data Warehouse & DSS

Kho dữ liệu bán hàng đa kênh cho Shopee Bibica, Shopee Quasure và TikTok Bibica, kèm đánh giá TikTok, dashboard BI và mô phỏng hỗ trợ quyết định.

**Luồng dữ liệu:** nguồn → Raw → Silver → PostgreSQL Galaxy/Golden → FastAPI → React BI/DSS.

**Công nghệ:** Python, PostgreSQL, FastAPI, SciPy; React 18, Vite, Recharts và TanStack Table.

## Chức năng

- ETL có kiểm tra chất lượng, quarantine, incremental load và chống nạp trùng.
- Galaxy Schema với 12 dimension và 3 fact; kho theo cửa hàng, tỉnh khách độc lập.
- Dashboard tổng quan liên kết, phân tích doanh số, kho/giao hàng và trải nghiệm khách hàng.
- Bộ lọc dùng chung; thống kê theo yêu cầu; đọc review tiêu cực đã che thông tin cá nhân.
- DSS phân bổ kho, so sánh kịch bản và mô phỏng hạn dùng với giả định minh thị.

## Cấu trúc

```text
DW/           ETL, SQL, Galaxy Schema và tài liệu kho dữ liệu
src/          API, DSS và profiling
frontend/     React, component tests và browser tests
tests/        Python unit/integration tests
scripts/      Khởi chạy, kiểm định và đóng gói
docs/         Kiến trúc, KPI, thuật toán và hướng dẫn vận hành
```

## Chạy local

Yêu cầu: **Python 3.12+, Node.js 20+ và PostgreSQL 16+**. Các lệnh dưới đây chạy tại thư mục gốc repo bằng PowerShell.

### 1. Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix frontend ci
```

Tạo database riêng `bibica_repo` trên PostgreSQL đang chạy. Ví dụ cấu hình local:

```powershell
$env:BIBICA_DSN='postgresql://warehouse@127.0.0.1:55432/bibica_repo'
```

Đổi tài khoản/cổng theo môi trường của bạn. Biến môi trường phải được đặt trong phiên terminal; ứng dụng không tự đọc `.env`. Không dùng database `warehouse` của dự án tham chiếu.

### 2. Chuẩn bị dữ liệu và ETL

Nguồn được cung cấp riêng, không nằm trong gói source. Đặt bốn file vào `Data/Data_Source_Raw/`:

```text
Shopee_Bibica.xlsx
Shopee_Quasure.xlsx
Tiktokshop_Bibica.csv
Tiktok_Rating_Bibica.xlsx
```

Giữ nguyên file nguồn; workbook rating dùng sheet `Ratings`. Nạp DW và tạo ba lớp dữ liệu riêng tư:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m DW.etl.run --process --dsn "$env:BIBICA_DSN"
.\.venv\Scripts\python.exe -X utf8 scripts/migrate_api.py
.\.venv\Scripts\python.exe -X utf8 scripts/build_review_theme_features.py
.\.venv\Scripts\python.exe -X utf8 scripts/build_review_case_content.py
```

Nếu DW đã có dữ liệu, chạy migration khi nâng cấp và chuẩn bị lại review khi thay nguồn rating. File nguồn và `data process/Raw`, `Silver`, `Golden` giữ ở local.

### 3. Mở ứng dụng

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_api.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_frontend.ps1
```

- **Dashboard:** http://127.0.0.1:5174
- **API/OpenAPI:** http://127.0.0.1:8001/docs

Dừng bằng `scripts/stop_api.ps1` và `scripts/stop_frontend.ps1`. Các script chỉ dừng tiến trình do repo quản lý.

## Kiểm thử

Test được giữ trong `tests/`, `frontend/tests/` và `frontend/e2e/`.

```powershell
# Python portable: fixture tổng hợp, không cần dữ liệu bán hàng riêng
# Tài khoản DB cần quyền tạo database; test chỉ tạo/xóa DB ngẫu nhiên của chính nó.
$env:BIBICA_TEST_DSN='postgresql://warehouse@127.0.0.1:55432/postgres'
.\.venv\Scripts\python.exe -X utf8 scripts/run_tests.py --portable

# React và production build
npm --prefix frontend test
npm --prefix frontend run build

# E2E: cần frontend/API, DW đã nạp và Microsoft Edge
npm --prefix frontend run e2e
```

`--portable` bỏ đúng ba kiểm tra cần file nguồn/báo cáo profiling riêng; các test gốc vẫn được giữ. Không đặt `BIBICA_TEST_DSN` thì nhóm DB bị SKIP và báo cáo là PARTIAL. Toàn bộ suite, gồm kiểm tra dữ liệu riêng: `python scripts/run_tests.py`.

## Đóng gói source

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/package_source.py
```

Kết quả: **`dist/Bibica_DW_Source.zip`**, có source, SQL, tài liệu, test và manifest SHA-256. Script tự kiểm tra cấu trúc, nội dung và CRC của ZIP.

Gói không chứa dữ liệu gốc, nội dung review, Raw/Silver/Golden, báo cáo sinh tự động, log, `.env`, database, `.git`, dependencies hoặc build. Đây là **gói source**, cần PostgreSQL và nguồn được cấp phép để dựng lại dữ liệu; không phải bản DW đã nạp sẵn hay gói báo cáo/slide môn học.

## Quy ước dữ liệu

- Một fact tương ứng một đơn, một dòng hàng được chấp nhận hoặc một review. Tiền đơn được tính một lần, không cộng lặp theo dòng SKU.
- Cả ba nguồn dùng cùng bốn category: **Bánh, Kẹo, Ngũ cốc, Quà tặng**. Category TikTok gốc chỉ dùng truy vết.
- SKU và kho giữ phạm vi cửa hàng; không gộp sản phẩm chỉ vì trùng tên. Không suy kho từ tỉnh khách.
- Đánh giá chỉ có TikTok; thiếu nguồn không phải bằng 0. Nhãn chủ đề và che thông tin tự động cần được hiểu cùng giới hạn của chúng.
- Tồn kho, năng lực và hạn dùng trong DSS là đầu vào kịch bản. Không suy lợi nhuận hoặc nguyên nhân lỗi từ dữ liệu chưa đủ.

## Tài liệu

- [Galaxy Schema](DW/architecture/1_galaxy_schema/galaxy_schema_candidate.md) · [DBML](DW/architecture/2_erd/galaxy_schema.dbml)
- [ETL](DW/documentation/etl_design.md) · [Raw/Silver/Golden](DW/documentation/DATA_LAYERS.md)
- [KPI Contract](docs/KPI_CONTRACT.md) · [API](docs/API_RUNBOOK.md)
- [Thuật toán DSS](docs/DSS_ALGORITHMS.md) · [Đánh giá và giới hạn](docs/DSS_EVALUATION.md)
- [Frontend và review reader](docs/PHASE3_RUNBOOK.md) · [Trạng thái kiểm chứng](docs/PROJECT_STATE.md)
