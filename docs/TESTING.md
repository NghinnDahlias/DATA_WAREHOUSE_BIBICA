# Kiểm thử và kiểm định dữ liệu

## Python

Tại root repo, sau khi cài dependencies và khởi động PostgreSQL:

```powershell
$env:BIBICA_TEST_DSN='postgresql://warehouse@127.0.0.1:55432/postgres'
.\.venv\Scripts\python.exe -X utf8 scripts/run_tests.py
```

Test DB chỉ tạo/xóa database ngẫu nhiên của chính nó; cần quyền CREATE DATABASE. Không đặt DSN thì nhóm này SKIP và báo cáo PARTIAL.

`tests/` gồm ETL/parser, duplicate/upsert/retraction/rollback, profiling, API/cohort, MILP và ràng buộc DSS, review/che thông tin. Test tạo báo cáo profiling bằng fixture trong thư mục tạm, không kiểm PASS bằng báo cáo lịch sử có sẵn.

Hai kiểm tra hợp đồng nguồn đọc file trong `Data/Data_Source_Raw/`. Nếu chưa có nguồn, dùng `--portable`; hai kiểm tra được loại khỏi profile và ghi rõ. Mọi test fixture còn lại vẫn chạy.

## Frontend và browser

```powershell
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run e2e
```

Vitest/Testing Library kiểm component, adapter và trạng thái bất đồng bộ. Playwright dùng Edge và API/DB thật, kiểm các màn hình, filter, SKU drilldown, DSS, popup, review reader và kích thước hiển thị. Browser tests cần DW đã nạp và hai dịch vụ đang chạy.

## Dữ liệu thật

```powershell
.\.venv\Scripts\python.exe -X utf8 -m DW.etl.verify --dsn "$env:BIBICA_DSN" --rerun
.\.venv\Scripts\python.exe -X utf8 scripts/verify_review_reader.py
```

Golden verifier kiểm hash/reconciliation, replay, nạp lại vào database mới do chính verifier tạo. Reader verifier đối chiếu cohort/KPI, chủ đề, phân trang, nội dung đã che và source freshness.

`scripts/assess_integrity.py`, `assess_allocation.py`, `assess_reviews.py` cung cấp kiểm định sâu bằng SQL/oracle và bằng chứng lịch sử. Báo cáo kết quả được sinh vào `reports/`, không có sẵn trong Git. Profiling sinh ghi chú tại `reports/profiling/`, không ghi đè tài liệu bàn giao.

## Phạm vi kết quả

Các bước khởi động lại, native ETL/Golden replay, cài dependencies, browser và unit tests là các kiểm tra riêng. PASS ở một bước không thay thế các bước khác. Docker/cloud/remote CI, tải production và điều phối kho thực không được chứng nhận từ các test local này.

## Kiểm chứng bản bàn giao — 15/11/2026

Đã clone dự án sang thư mục riêng và chạy lại từ cây source không có báo cáo lịch sử hay ghi chú làm việc:

| Kiểm tra | Kết quả |
|---|---|
| Python unit/integration | 125 PASS, 0 fail/error/skip |
| Cài frontend theo lockfile | npm ci PASS |
| React tests | 46 PASS |
| Production frontend build | PASS |
| Browser E2E với API của bản clone | 26 PASS, 0 failed/skipped/flaky |

Python dùng môi trường dependencies đã có; frontend được cài mới trong bản clone. Test DB dùng fixture/database tạm; browser đọc DW dữ liệu thật đã nạp sẵn. Build còn cảnh báo bundle lớn và dependencies hiện hành có cảnh báo deprecation. Đây không phải kiểm chứng nạp lại toàn bộ nguồn vào DW trống hoặc vận hành production.
