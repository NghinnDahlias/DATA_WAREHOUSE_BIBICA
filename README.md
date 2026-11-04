# Bibica — PostgreSQL Galaxy DW & ETL

Phần Data Engineer & Database Architect, cập nhật 04/11/2026. Giữ constellation gốc và bổ sung migration: **12 dimension + 3 fact, 56 FK**, persistent sanitized raw/typed staging, canonical Category, kho xuất hàng và tỉnh khách nhận, current snapshot upsert và OLAP refresh có kiểm chứng.

Kết quả full-data: **127588 orders, 178517 accepted item lines, 5625 reviews**. Raw184529record:178832sales +5697rating. Quarantine315exact sales duplicates +66semantic repeated reviews +6invalid reviews. Các số này là snapshot đã chạy, không phải hằng số trong ETL.

## Chạy độc lập

Python3.12+ và PostgreSQL16+; install `python -m pip install -r requirements.txt`. Tạo database **riêng** `bibica_repo` bằng tài khoản có quyền phù hợp; không dùng database `warehouse` của dự án DSS cha. Không có lệnh drop database hiện hữu trong runbook.

```powershell
$env:BIBICA_DSN='postgresql://warehouse@127.0.0.1:55432/bibica_repo'
python -m DW.etl.run --process --dsn "$env:BIBICA_DSN"
python -m DW.etl.verify --dsn "$env:BIBICA_DSN" --rerun
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

13tests đã chạy PASS, gồm8profiling cũ và5tests hợp đồng/DB mới; DB tests chỉ tạo/xóa database ngẫu nhiên của chính test. Thiếu BIBICA_TEST_DSN thì3DB tests SKIP, không gọi là PASS. Full ETL có16gates; private layer/reload verifier có11checks. Đọc `reports/etl_validation.json`, `processing_verification.json`, `reference_reconciliation.json` để xem bằng chứng hiện hành.

- [Kiến trúc](DW/architecture/architecture_overview.md), [Galaxy](DW/architecture/1_galaxy_schema/galaxy_schema_candidate.md), [DBML](DW/architecture/2_erd/galaxy_schema.dbml), [Dictionary](DW/architecture/data_dictionary/data_dictionary.md).
- [ETL runbook](DW/documentation/etl_design.md), [Data layers](DW/documentation/DATA_LAYERS.md), [Category & Geography](DW/documentation/CANONICAL_GEOGRAPHY.md), [trạng thái nghiệm thu](DW/07_documentation/implementation_status.md).

Repo này hoàn thiện phạm vi DW/ETL/OLAP; không tuyên bố có frontend, API hay DSS riêng. Không chạy Docker/cloud/remote CI trong lần kiểm chứng này. Các tài liệu Phase1 và ảnh DB.png cũ là lịch sử, không thay bằng chứng cho schema hiện hành.
