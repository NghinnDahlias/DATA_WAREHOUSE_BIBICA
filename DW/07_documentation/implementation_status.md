# Trạng thái DW và backend/DSS

## Phase2 mới — 05/11/2026

Backend API, KPI Contract M01–M16, whole-order warehouse allocation, breakfast shelf-life scenario, historical fulfillment risk, what-if/sensitivity đã triển khai local trong repo. 61/61tests,18/18full-data API/DSS assertions,16/16ETL gates và11/11layer checks chạy mới PASS. Schema vẫn12dims/3facts/56FK. Repo API tại loopback8001/docs, cách chạy và giới hạn ở docs/API_RUNBOOK.md và docs/DSS_EVALUATION.md.

Shopee shipped header được sửa và nạp lại, business fingerprints và raw bytes giữ nguyên. Thêm ANALYZE để sửa reproduced DSS timeout. Stock/HSD/capacity là scenario, risk không calibrated, chưa commit/push Phase2.

## Snapshot DW/ETL đã kiểm04/11/2026

| Hạng mục | Kết quả đã chạy |
|---|---|
| Galaxy/PostgreSQL | 12dims/3facts, 56FK; migration additive trên constellation gốc |
| Full ETL nguồn hiện hành | 127588 orders / 178517 accepted lines / 5625 reviews |
| Rating XLSX | Ratings only, lexical IDs,66semantic repeats +6invalid quarantined,4870historical SKU matches +755order-only |
| Category |4business categories, name-only thống nhất3sources, native TikTok category metadata |
| Kho/tỉnh |6warehouse members scoped theo shop,2warehouse city regions; customer province độc lập, alias controlled |
| Duplicate/DQ |315sales duplicates,66review duplicates,6invalid; raw giữ đủ184529record |
| Incremental | Fixture source update/rename/retraction/rollback PASS; full replay0raw insert/0update và fact fingerprints stable |
| OLAP |5populated MVs; 16/16load/reconciliation gates PASS |
| Raw/Silver/Golden |11/11verifier checks PASS;15Golden tables reload/FKs/fingerprints đã kiểm |
| Automated tests |13/13unittest PASS khi bật BIBICA_TEST_DSN; không dùng8test profiling cũ thay cho loader tests |

Đối chiếu bản DSS tham chiếu: `reports/reference_reconciliation.json` có fingerprints nghiệp vụ của127588orders,178517items và5625reviews; không so sánh surrogate keys giữa hai thiết kế khác nhau.

Thông tin tiền: completed observed order payable9175209123VND; completed units168478. Đây không phải doanh thu thuần/lợi nhuận hay chứng nhận kế toán. Gift observed payments0/dương đều giữ nguyên.

Snapshot04/11đã kiểm local với PostgreSQL18 và chỉ bao gồm DW/ETL. Backend/DSS mới được bổ sung05/11như phần đầu tài liệu. Docker/remote CI/cloud, crash recovery và load-test concurrency chưa chạy. Dữ liệu dẫn xuất riêng tư tiếp tục bị loại khỏi Git.
