# RAW → Silver → Golden

Pipeline chạy local bằng `python -m DW.etl.run --process --dsn "$env:BIBICA_DSN"`.

| Lớp | Vị trí | Nội dung và kiểm chứng |
|---|---|---|
| Nguồn bất biến | `Data/Data_Source_Raw/` | 4 file native hiện hành; không sửa/re-save Excel hoặc CSV nguồn |
| Raw | `data process/Raw/` | Bản sao byte-identical của 4 nguồn + manifest SHA256; phiên bản cũ được giữ trong history khi nguồn thay đổi |
| Silver | `data process/Silver/` | CSV giữ nguyên giá trị giải mã các cột nguồn, thêm canonical category cho 3 nguồn sales, kho chuẩn/khu vực kho/tỉnh khách, Source Row và source hash; rating giữ nguyên các cột scraper để truy vết |
| Golden | `data process/Golden/` | 12 dimension + 3 fact, mỗi bảng một CSV, schema SQL/JSON lấy từ PostgreSQL thật, PK/UQ/CHECK/FK và manifest; không phải bảng sales phẳng |

`raw.source_row` trong PostgreSQL chỉ giữ **sanitized projection**, không phải raw workbook chứa PII. `staging.order_line`/`staging.review` là typed views bền vững trên projection; `ops.quarantine` giữ reason và locator. Lỗi không bị làm mất dấu chỉ vì temp table hết transaction.

Toàn bộ `data process/` có thể chứa dữ liệu riêng tư và được `.gitignore` loại bỏ. Không đưa vào Git, ZIP công khai hoặc Docker context. Việc 4 nguồn đã được người dùng yêu cầu đưa lên Git trước đó không cho phép tự xuất bản dữ liệu dẫn xuất.

Native XLSX rating có ID text18/19digits. Khi mở CSV bằng Excel, phải import cột ID dạng Text; pipeline không dựa vào cách Excel tự hiển thị CSV, không chèn dấu nháy hoặc công thức vào ID.

`--seed-silver PATH` chỉ là tối ưu local từ cache đã kiểm chứng: kiểm source SHA, file SHA, số dòng và hash giá trị mọi cột gốc; đọc lại tên sản phẩm/kho/tỉnh gốc để tính canonical bằng code hiện hành. Không nhận category của cache làm nhãn chính thức. Không dùng cache tải không rõ nguồn. CLI mặc định vẫn đọc native source và không phụ thuộc thư mục dự án cha.

Chạy `python -m DW.etl.verify --dsn "$env:BIBICA_DSN" --rerun` để kiểm hashes, category/kho/tỉnh từng dòng Silver, replay 0 raw writes, fingerprints fact và nạp lại Golden với toàn bộ FK vào database mới tách biệt. Chỉ database kiểm chứng vừa tạo được xóa sau kiểm tra.
