# ETL / ELT hiện hành và vận hành

Giữ PostgreSQL, scoped dimensions/facts và COPY loader; sửa snapshot semantics và bổ sung contracts/quality/provenance.

1. Kiểm đủ4native files trước khi thay dữ liệu; chọn orders hoặc Ratings, không đọc Nguon như reviews.
2. Raw copy giữ nguyên bytes, manifest SHA256; native sources read-only. Silver giữ original decoded values, thêm canonical metadata; không thay ID bằng float, apostrophe hay Excel formula.
3. Project từng record vào raw.source_row sanitized JSONB. Giữ source physical locator và original row hash. Product names giữ để phân loại/lineage, không lưu tên/địa chỉ/điện thoại người mua hoặc free review text.
4. Cùng rule-based categorization cho3sales sources; kho alias nguồn và tỉnh spelling dictionary độc lập. Giữ native category/province/warehouse bên cạnh canonical fields.
5. Ghi typed staging views và ops.quarantine: exact sales duplicates, semantic repeated reviews, invalid rows và reviews không có sales order. Raw luôn giữ đủ.
6. Nạp dimensions → order identities → current facts, giữ surrogate keys thích hợp. Lifecycle gom một lần mỗi order; amount/refund mâu thuẫn NULL và CONFLICTING.
7. Item/review current key source_code+physical_row_number. Source checksum đổi thì upsert snapshot, rút các locators bị xóa; không cộng hai phiên bản file. Lifecycle cập nhật status/money/dates/line count. Replay raw cùng SHA/parser version có0insert/0update.
8. Ghép review SKU theo historical staging names, duy nhất trong order; Product Type1 không thay tên lịch sử. Product ID trong review không được giả làm SKU.
9. Tính5OLAP MVs cùng transaction; đối soát source/quarantine→facts→marts bằng assertion có raise. Thiếu source/header hoặc lỗi giữa chừng rollback transaction; ops.etl_run ghi FAILED, CLI exit1. Không báo thành công phần dữ liệu thiếu.
10. Golden export snapshot REPEATABLE READ, schema/types/PK/FK thật từ PostgreSQL. Verifier reload toàn bộ15bảng vào DB mới và kiểm fingerprints/FKs; chỉ DB đó được cleanup.

Concurrency: session advisory lock bảo vệ DDL trước data transaction; cùng khóa transaction bảo vệ source snapshots/transforms. OS file lock bảo vệ process exports. Native code đọc streaming XLSX/CSV và COPY records; riêng profiling giữ một số aggregate/set trong RAM. Chưa tuyên bố đã benchmark giới hạn memory/concurrency/crash recovery đầy đủ.

DDL gốc có BEGIN/COMMIT nên migration chạy trước data transaction; đây không phải cam kết rollback schema DDL cùng dữ liệu. Dữ liệu source snapshots/facts/MVs được commit atomically.

## Lệnh

```powershell
python -m DW.etl.run --dry-run
python -m DW.etl.run --process --dsn "$env:BIBICA_DSN"
python -m DW.etl.verify --dsn "$env:BIBICA_DSN" --rerun
$env:BIBICA_TEST_DSN='postgresql://warehouse@127.0.0.1:55432/postgres'
python -m unittest discover -s tests -v
```

DSN phải trỏ DB riêng của repo. Xem README/.env.example. `--seed-silver` chỉ dành cache local đã kiểm chứng (xem DATA_LAYERS.md); mặc định đọc native files, chạy độc lập với project cha.

Giới hạn: đây là incremental theo **source snapshot/physical locator**, không phải CDC/event ingestion. Nếu source sắp xếp lại hàng, các locators được upsert theo snapshot mới; không khẳng định ổn định business line ID qua mọi reorder. Tồn kho, cost, settlement revenue, profit và causal promotion impact không được suy ra từ export.
