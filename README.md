# Bibica — PostgreSQL Galaxy DW, API, DSS & React BI

Phase3 được cập nhật từ origin/main commit `96941fb` ngày09/11/2026, kèm sửa lỗi và kiểm chứng local. React gồm Overview, Sales, Warehouse, Customer Experience và DSS Simulation. Lệnh chạy, bộ lọc, refresh review themes và kiểm thử tại [Phase3 runbook](docs/PHASE3_RUNBOOK.md); kết quả thực tế tại [Phase3 acceptance](docs/QA/PHASE3_ACCEPTANCE.md). Các thay đổi kiểm thử/sửa lỗi hiện hành chưa commit/push.

DW/ETL giữ constellation gốc **12 dimension + 3 fact, 56 FK**. Phase2 backend/DSS cập nhật05/11/2026 bổ sung API PostgreSQL, KPI Contract, phân bổ kho HN/HCM, mô phỏng hạn dùng, risk scoring và what-if. Dữ liệu gốc/Silver/Golden riêng tư giữ ở local.

Kiểm toán nghiệp vụ mới mở rộng114tests,90scenario oracle,68cohort KPI và phân tích rating đa chiều. Kết luận readiness có điều kiện cho DSS phân tích/mô phỏng được ghi trong [báo cáo nghiệm thu](docs/QA/PHASE2_ACCEPTANCE.md). Các snapshot61tests trước đó là lịch sử. Bánh ăn sáng mặc địnhHN, ngoại lệHCM cần xác nhận scenario scopedSKU/kho. Giữ guard truy vấn tuần tự theo API_RUNBOOK để tránh sai lệch đã tái hiện ở local parallel query mode.

Kết quả full-data: **127588 orders, 178517 accepted item lines, 5625 reviews**. Raw184529record:178832sales +5697rating. Quarantine315exact sales duplicates +66semantic repeated reviews +6invalid reviews. Các số này là snapshot đã chạy, không phải hằng số trong ETL.

## Chạy độc lập

Python3.12+ và PostgreSQL16+; install `python -m pip install -r requirements.txt`. Tạo database **riêng** `bibica_repo` bằng tài khoản có quyền phù hợp; không dùng database `warehouse` của dự án DSS cha. Không có lệnh drop database hiện hữu trong runbook.

```powershell
$env:BIBICA_DSN='postgresql://warehouse@127.0.0.1:55432/bibica_repo'
python -m DW.etl.run --process --dsn "$env:BIBICA_DSN"
python -m DW.etl.verify --dsn "$env:BIBICA_DSN" --rerun
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_api.ps1
```

Trong workspace hiện tại có thể thay `python` bằng `..\.venv\Scripts\python.exe -X utf8`. Đó chỉ là interpreter; source code không import hoặc phụ thuộc project cha. Bản kiểm chứng local dùng database `bibica_repo` trên port55432.

`--load` chỉ nạp DW; `--process` tạo cả `data process/Raw`, `Silver`, `Golden`. `--dry-run` đọc/kiểm source contract, không chứng nhận reconciliation database. Thiếu source/header hoặc lỗi ETL trả exit khác0; thay dữ liệu được rollback toàn transaction.

Nguồn: `Shopee_Bibica.xlsx`, `Shopee_Quasure.xlsx`, `Tiktokshop_Bibica.csv`, **`Tiktok_Rating_Bibica.xlsx`**, sheet Ratings. Sheet Nguon không phải review. Không sửa/re-save source; không float-cast identifier. `data process/` chứa dữ liệu riêng tư và bị loại khỏi Git.

## Quy ước nghiệp vụ

- Cùng hàm tên sản phẩm cho cả3sales sources: Quà tặng → Bánh → Kẹo → Ngũ cốc. Native TikTok category chỉ metadata; Unmapped NULL + audit status.
- SKU scoped theo shop, đổi tên cập nhật Type1; category của transaction theo tên dòng lịch sử. Không fuzzy merge SKU giữa sàn.
- Kho theo source label, giữ6members theo shop, chuẩn khu vực Hà Nội/Hồ Chí Minh. Tỉnh khách là chiều riêng, chuẩn hóa chữ/tiền tố, không suy sáp nhập hành chính.
- Fact một đơn / một accepted source line / một accepted review. Tiền đơn chỉ tổng hợp một lần ở lifecycle fact. Giá gốc và observed item payable không phải doanh thu thuần hay lợi nhuận.
- Raw giữ đủ; quarantine không xóa source. Checksum là provenance; source+row locator là current-state key. Changed/deleted rows cập nhật/rút khỏi fact; replay cùng byte không nhân fact.
- Review phải có sales order; SKU match bằng normalized historical name duy nhất trong cùng order, không dùng latest Product name hoặc product_id=SKU giả định.

## Kiểm thử và tài liệu

```powershell
$env:BIBICA_TEST_DSN='postgresql://warehouse@127.0.0.1:55432/postgres'
python -m unittest discover -s tests -v
```

13tests DW cũ được giữ nguyên, bổ sung unit DSS và API/integration. Chạy `python scripts/run_tests.py` để ghi report mới ở reports/phase2_tests.json/log. Thiếu BIBICA_TEST_DSN thì DB tests SKIP, report PARTIAL. Full ETL có16gates, private layer/reload verifier có11checks. Full API/DSS đối soát bằng `python scripts/verify_phase2.py`, đọc reports/phase2_verification.json và docs/DSS_EVALUATION.md.

- [Kiến trúc](DW/architecture/architecture_overview.md), [Galaxy](DW/architecture/1_galaxy_schema/galaxy_schema_candidate.md), [DBML](DW/architecture/2_erd/galaxy_schema.dbml), [Dictionary](DW/architecture/data_dictionary/data_dictionary.md).
- [ETL runbook](DW/documentation/etl_design.md), [Data layers](DW/documentation/DATA_LAYERS.md), [Category & Geography](DW/documentation/CANONICAL_GEOGRAPHY.md), [trạng thái nghiệm thu](DW/07_documentation/implementation_status.md).
- [API runbook](docs/API_RUNBOOK.md), [KPI Contract](docs/KPI_CONTRACT.md), [Thuật toán DSS](docs/DSS_ALGORITHMS.md), [Đánh giá thực nghiệm](docs/DSS_EVALUATION.md), [trạng thái Phase2](docs/PROJECT_STATE.md).

API local tại http://127.0.0.1:8001/docs. Phase3 React BI chạy riêng tại http://127.0.0.1:5174, xem docs/PHASE3_RUNBOOK.md và docs/QA/PHASE3_ACCEPTANCE.md. Ghi chú Phase2 không có frontend là phạm vi lịch sử. DSS nhận nhu cầu/tồn kho/năng lực/HSD kịch bản và trả conditional assignments, không gọi tồn kho giả định là dữ liệu thực. Đọc API_RUNBOOK và DSS_ALGORITHMS để chạy demo và hiểu các giới hạn. Docker/cloud/remote CI chưa chạy. Các tài liệu Phase1 và ảnh DB.png cũ là lịch sử, không thay bằng chứng cho schema hiện hành.
