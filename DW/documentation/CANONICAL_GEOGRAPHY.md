# Category, kho xuất hàng và tỉnh khách nhận

`DW/etl/categorization.py::categorize_product(name)` là hàm phân loại duy nhất cho cả Shopee Bibica, Shopee Quasure và TikTok Bibica. Bộ quy tắc được giữ cùng nội dung với bản DSS tham chiếu.

1. Gift marker rõ: `[QUÀ TẶNG]`, `[QUÀ TẶNG KHÔNG BÁN]`, “quà tặng ngẫu nhiên”, “quà tặng không bán”, “tặng kèm” → **Quà tặng**.
2. Có từ bánh → **Bánh**.
3. Có từ kẹo → **Kẹo**.
4. Có cụm ngũ cốc → **Ngũ cốc**.
5. Không nhận diện: NULL category key/canonical_category + `Unmapped`; không tạo business category thứ năm.

Bánh ngũ cốc là Bánh. `[TẶNG QUÀ - DATE MỚI]` không tự biến một món bán thành gift. Tên bánh+kẹo theo Bánh priority và có flag kiểm toán. Không fuzzy matching, không suy từ SKU, không chuyển nhãn từ category TikTok. Category TikTok gốc chỉ là metadata ở raw/Silver/Product.

Product dimension dùng tên Type1 mới nhất, khóa theo SKU trong shop (thiếu SKU dùng hash tên+biến thể, có tài liệu giới hạn). Category của fact line theo chính tên ở dòng lịch sử. Không gộp SKU giữa shop/sàn. Giữ tiền hàng quà tặng quan sát cả 0 và dương, không coi list value là doanh thu.

## Hai vai trò địa lý độc lập

| Vai trò | Nguồn | Chuẩn hóa |
|---|---|---|
| Kho xuất hàng | Shopee `Tên kho hàng`; TikTok `Warehouse Name` | Giữ native label, scope theo storefront, thêm normalized warehouse và warehouse_region |
| Tỉnh khách nhận | Shopee `Tỉnh/Thành phố`; TikTok `Province` | Giữ native label và canonical tỉnh theo dictionary chữ/tiền tố; thiếu hoặc không nhận diện là Unknown/UNMAPPED |

| Nhãn kho quan sát | Tên kho chuẩn | Khu vực kho |
|---|---|---|
| Kho Hồ Chí Minh, HCM, BIBICA HCM | Kho Hồ Chí Minh | Hồ Chí Minh |
| Kho Hà Nội, HN, BIBICA HN | Kho Hà Nội | Hà Nội |

Khu vực kho ở đây là **thành phố suy được trực tiếp từ nhãn kho quan sát**, không phải mã kho vật lý hay phân vùng hành chính. Không suy kho từ tỉnh khách. Không coi kho cùng thành phố nhưng khác shop là cùng facility.

Dictionary tỉnh xử lý tiền tố Tỉnh/Tinh/Thành phố/Thanh pho/TP/Phố, khác dấu, hoa/thường và dấu nối theo tập tên xuất hiện trong dữ liệu. Huế/Thừa Thiên Huế, Bình Dương/Hồ Chí Minh và các tên lịch sử khác được giữ riêng: không suy sáp nhập hành chính hoặc đổi địa giới. Chỉ unaccent để exact lookup trong dictionary; không fuzzy-match tên chưa biết.

Kho đặt trên line fact vì một đơn có thể xuất qua nhiều kho. Province của lifecycle chỉ gắn khi raw province nhất quán trong đơn; conflict để NULL ở order scope, mỗi line vẫn giữ tỉnh của chính dòng đó.

`mart.v_item_business`, `mart.mv_warehouse_province` và `mart.mv_category_performance` dùng canonical fields. Units/list/observed-item-value cộng được ở line grain; distinct orders không cộng giữa kho/category. Không phân bổ tiền cấp đơn cho từng kho hoặc province khi chưa có quy tắc allocation được chứng minh.
