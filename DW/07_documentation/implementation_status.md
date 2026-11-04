# Trạng thái Data Engineer & Database Architect — 04/11/2026

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

Đã kiểm local với PostgreSQL18. Chưa chạy Docker/remote CI/cloud, crash recovery và load-test concurrency. Phạm vi repo không bao gồm frontend/API/DSS riêng. Lịch sử phát hành source/docs được ghi trong Git; dữ liệu dẫn xuất riêng tư không nằm trong commit.
