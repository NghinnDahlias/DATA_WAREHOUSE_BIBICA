# Kiến trúc PostgreSQL Galaxy đã hiện thực

Cập nhật04/11/2026. **12dimension +3fact, 56FK thực tế**; không yêu cầu số bảng giống bản DSS tham chiếu vì technical dimensions được mô hình hóa riêng.

Luồng: immutable native sources → private Raw byte copies → sanitized raw.source_row + typed staging views + quarantine → DW shared dimensions/current facts →5OLAP materialized views → Golden CSV/schema snapshot.

| Fact | Grain | Khóa nghiệp vụ hiện hành |
|---|---|---|
| fact_order_line_candidate | Một dòng sales nguồn được chấp nhận | source_code + physical_row_number |
| fact_order_lifecycle_candidate | Một đơn trong channel/storefront | order_key, tương ứng scoped native_order_id |
| fact_review_candidate | Một review được chấp nhận | source_code + physical_row_number |

Tên bảng `_candidate` được giữ để không phá tích hợp sẵn; analytical facts hiện loại các dòng quarantine, không còn đồng nhất với raw candidates. Source hash/locator/batch vẫn trace được nhưng batch và checksum không tạo business row mới khi replay/update.

Shared business dimensions: channel, storefront, order identity, date, time, source product/SKU, warehouse, province, order status và category. Source file/ingestion batch là2technical dimensions, tổng12dimension. Raw native IDs là TEXT. Namespace order: channel|storefront|native_order_id.

Product natural key theo native SKU trong shop, thiếu dùng fallback hash tên+variant. Tên Type1 mới nhất; item category FK theo tên source line lịch sử. Không tự gộp SKU qua shop. Existing compatible SKU surrogate được tái sử dụng; những version duplicate theo logical locator ở DB cũ được lưu vào ops.migration_history trước khi hợp nhất current facts.

Kho có native label + normalized label + warehouse_region, FK kiểm cả storefront. Province native và canonical tách riêng; spelling dictionary giữ tên lịch sử, không suy địa giới. Nếu tỉnh/kho không nhất quán trong order, lifecycle dimension có thể NULL; item vẫn giữ nguồn ở đúng grain.

Created/paid/shipped/delivered/cancelled và review date/time là role-playing Date/Time. Contract export là giờ địa phương Asia/Ho_Chi_Minh, không giả định timestamp có timezone chuẩn khi nguồn không cung cấp. Không so completion Shopee với delivery TikTok như cùng một KPI.

Tiền cấp đơn chỉ ở lifecycle; tiền dòng là list value/observed item payable riêng, không settlement revenue. Reviews không nhân sales: unique historical normalized name trong cùng order hoặc order-only. Raw review text/buyer identity không vào DW facts; chỉ presence và actual length.

5marts: order counts, item units monthly, ratings monthly, warehouse→province và category performance. Rebuild/refresh nằm cùng transaction ETL; gates dừng commit khi sai. Distinct orders giữa kho/category không cộng được.

DDL và indices gốc được giữ; migration030 bổ sung. DBML và data dictionary lấy từ Golden schema JSON hiện thực. `DB.png` là ảnh thiết kế trước refinement và không phải sơ đồ hiện hành.
