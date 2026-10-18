# Source inventory

Read-only profile of the four prepared raw exports in `Data/Data_Source_Raw`. SHA-256 fingerprints and exact schemas are in `reports/source_inventory.json`. The assignment PDF was inspected separately; it has 7 pages and requires business requirements, multidimensional DW, ETL, DSS, and presentation.

| Source | Storefront | Rows | Columns | Sheet |
|---|---|---:|---:|---|
| Tiktokshop_Bibica.csv | Bibica TikTok Shop | 77,311 | 56 | csv |
| Tiktokshop_Bibica_Rating.csv | Bibica TikTok Shop | 5,625 | 10 | csv |
| Shopee_Bibica.xlsx | Bibica Official Store | 86,796 | 64 | orders |
| Shopee_Quasure.xlsx | Quasure specialized store | 14,725 | 63 | orders |

Missing exports: none.

## Date ranges and schema

Shopee Bibica-only fields: Phí thanh toán. Shopee Quasure-only fields: none.

### Tiktokshop_Bibica.csv

Empty fields: 1; constant non-private candidates: 3.

| Field | Earliest | Latest | Parse failures |
|---|---|---|---:|
| created | 2023-08-04T13:55:55 | 2026-10-17T09:21:39 | 0 |
| cancelled | 2023-08-04T15:10:26 | 2026-10-17T09:13:49 | 0 |
| paid | 2023-08-16T08:53:19 | 2026-10-17T09:49:56 | 0 |
| shipped | 2023-08-15T19:49:26 | 2026-10-16T16:38:18 | 0 |
| delivered | 2023-08-16T16:05:59 | 2026-10-17T09:49:56 | 0 |

Columns (name: inferred Python value type; blank count):

- Order ID: text/mixed; role `order`; 0 blanks
- Order Status: text/mixed; role `status`; 0 blanks
- Order Substatus: text/mixed; role `unclassified`; 0 blanks
- Cancelation/Return Type: text/mixed; role `unclassified`; 65,847 blanks
- Normal or Pre-order: text/mixed; role `unclassified`; 201 blanks
- SKU ID: text/mixed; role `sku`; 0 blanks
- Seller SKU: text/mixed; role `unclassified`; 1,188 blanks
- Product Name: text/mixed; role `product`; 0 blanks
- Variation: text/mixed; role `unclassified`; 0 blanks
- Quantity: text/mixed; role `quantity`; 0 blanks
- Sku Quantity of return: text/mixed; role `unclassified`; 0 blanks
- SKU Unit Original Price: text/mixed; role `unit_price`; 0 blanks
- SKU Subtotal Before Discount: text/mixed; role `gross`; 0 blanks
- SKU Platform Discount: text/mixed; role `platform_discount`; 0 blanks
- SKU Seller Discount: text/mixed; role `seller_discount`; 0 blanks
- SKU Subtotal After Discount: text/mixed; role `net_item`; 0 blanks
- Shipping Fee After Discount: text/mixed; role `shipping`; 0 blanks
- Original Shipping Fee: text/mixed; role `unclassified`; 0 blanks
- Shipping Fee Seller Discount: text/mixed; role `unclassified`; 0 blanks
- Shipping Fee Platform Discount: text/mixed; role `unclassified`; 0 blanks
- Payment platform discount: text/mixed; role `unclassified`; 76,627 blanks
- Taxes: text/mixed; role `unclassified`; 0 blanks
- Order Amount: text/mixed; role `order_amount`; 0 blanks
- Order Refund Amount: text/mixed; role `refund`; 66,032 blanks
- Created Time: text/mixed; role `created`; 0 blanks
- Paid Time: text/mixed; role `paid`; 10,232 blanks
- RTS Time: text/mixed; role `unclassified`; 9,537 blanks
- Shipped Time: text/mixed; role `shipped`; 10,428 blanks
- Delivered Time: text/mixed; role `delivered`; 11,524 blanks
- Cancelled Time: text/mixed; role `cancelled`; 66,401 blanks
- Cancel By: text/mixed; role `unclassified`; 66,310 blanks
- Cancel Reason: text/mixed; role `unclassified`; 66,310 blanks
- Fulfillment Type: text/mixed; role `unclassified`; 0 blanks
- Warehouse Name: text/mixed; role `warehouse`; 0 blanks
- Tracking ID: text/mixed; role `tracking`; 9,215 blanks
- Delivery Option: text/mixed; role `unclassified`; 8 blanks
- Shipping Provider Name: text/mixed; role `unclassified`; 9,215 blanks
- Buyer Message: text/mixed; role `private_or_source_specific`; 76,915 blanks
- Buyer Username: text/mixed; role `private_or_source_specific`; 924 blanks
- Recipient: text/mixed; role `private_or_source_specific`; 0 blanks
- Phone #: text/mixed; role `private_or_source_specific`; 0 blanks
- Country: text/mixed; role `unclassified`; 0 blanks
- Province: text/mixed; role `province`; 0 blanks
- District: text/mixed; role `unclassified`; 0 blanks
- Commune: text/mixed; role `unclassified`; 0 blanks
- Detail Address: text/mixed; role `private_or_source_specific`; 0 blanks
- Additional address information: text/mixed; role `private_or_source_specific`; 54,934 blanks
- Payment Method: text/mixed; role `unclassified`; 249 blanks
- Weight(kg): text/mixed; role `unclassified`; 0 blanks
- Product Category: text/mixed; role `unclassified`; 0 blanks
- Package ID: text/mixed; role `package`; 1,093 blanks
- Seller Note: text/mixed; role `unclassified`; 77,308 blanks
- Checked Status: text/mixed; role `unclassified`; 1,093 blanks
- Checked Marked by: empty; role `unclassified`; 77,311 blanks
- Order Channel: text/mixed; role `unclassified`; 0 blanks
- Creator Handle: text/mixed; role `unclassified`; 38,720 blanks

### Tiktokshop_Bibica_Rating.csv

Empty fields: 0; constant non-private candidates: 0.

| Field | Earliest | Latest | Parse failures |
|---|---|---|---:|
| created | 2023-08-24T00:00:00 | 2026-10-17T00:00:00 | 0 |

Columns (name: inferred Python value type; blank count):

- order_id: text/mixed; role `order`; 0 blanks
- star_level: text/mixed; role `rating`; 0 blanks
- user_name: text/mixed; role `private_or_source_specific`; 0 blanks
- product_id: text/mixed; role `product_id`; 0 blanks
- product_name: text/mixed; role `product`; 0 blanks
- sku_specification: text/mixed; role `sku_spec`; 0 blanks
- review_text: text/mixed; role `text`; 1,155 blanks
- review_date: text/mixed; role `created`; 0 blanks
- other_text: text/mixed; role `other_text`; 3,576 blanks
- source_csv: text/mixed; role `unclassified`; 0 blanks

### Shopee_Bibica.xlsx

Empty fields: 1; constant non-private candidates: 9.

| Field | Earliest | Latest | Parse failures |
|---|---|---|---:|
| created | 2024-12-01T00:40:00 | 2026-09-30T23:56:00 | 0 |
| paid | 2024-12-01T01:10:00 | 2026-10-01T23:49:00 | 0 |
| delivered | 2024-12-02T13:41:00 | 2026-10-02T16:16:00 | 0 |
| shipped | 2024-12-02T16:00:00 | 2026-10-02T16:00:00 | 0 |

Columns (name: inferred Python value type; blank count):

- Mã đơn hàng: text/mixed; role `order`; 0 blanks
- Mã Kiện Hàng: text/mixed; role `package`; 11,149 blanks
- Ngày đặt hàng: text/mixed; role `created`; 0 blanks
- Trạng Thái Đơn Hàng: text/mixed; role `status`; 0 blanks
- Sản Phẩm Bán Chạy: text/mixed; role `unclassified`; 0 blanks
- Lý do hủy: text/mixed; role `unclassified`; 74,012 blanks
- Nhận xét từ Người mua: text/mixed; role `private_or_source_specific`; 85,384 blanks
- Mã vận đơn: text/mixed; role `tracking`; 11,238 blanks
- Đơn Vị Vận Chuyển: text/mixed; role `unclassified`; 0 blanks
- Phương thức giao hàng: text/mixed; role `unclassified`; 11,149 blanks
- Loại đơn hàng: text/mixed; role `unclassified`; 81,721 blanks
- Ngày giao hàng dự kiến: text/mixed; role `unclassified`; 6,275 blanks
- Ngày gửi hàng: text/mixed; role `shipped`; 11,149 blanks
- Thời gian giao hàng: text/mixed; role `delivered`; 12,244 blanks
- Trạng thái Trả hàng/Hoàn tiền: text/mixed; role `refund_status`; 85,926 blanks
- SKU sản phẩm: text/mixed; role `product_sku`; 58,146 blanks
- Tên sản phẩm: text/mixed; role `product`; 0 blanks
- Cân nặng sản phẩm: text/mixed; role `unclassified`; 0 blanks
- Tổng cân nặng: text/mixed; role `unclassified`; 0 blanks
- Tên kho hàng: text/mixed; role `warehouse`; 0 blanks
- SKU phân loại hàng: text/mixed; role `sku`; 458 blanks
- Tên phân loại hàng: text/mixed; role `unclassified`; 25,742 blanks
- Giá gốc: text/mixed; role `unit_price`; 0 blanks
- Người bán trợ giá: text/mixed; role `seller_discount`; 0 blanks
- Được Shopee trợ giá: text/mixed; role `platform_discount`; 0 blanks
- Tổng số tiền được người bán trợ giá: text/mixed; role `unclassified`; 0 blanks
- Giá ưu đãi: text/mixed; role `net_item`; 0 blanks
- Số lượng: text/mixed; role `quantity`; 0 blanks
- Số lượng sản phẩm được hoàn trả: text/mixed; role `returned_quantity`; 0 blanks
- Tổng số tiền Người mua thanh toán: text/mixed; role `payment`; 0 blanks
- Tổng giá trị đơn hàng (VND): text/mixed; role `order_amount`; 0 blanks
- Mã giảm giá của Shop: text/mixed; role `unclassified`; 0 blanks
- Hoàn Xu: text/mixed; role `unclassified`; 0 blanks
- Mã giảm giá của Shopee: text/mixed; role `unclassified`; 0 blanks
- Chỉ tiêu Combo Khuyến Mãi: text/mixed; role `unclassified`; 0 blanks
- Giảm giá từ combo Shopee: text/mixed; role `unclassified`; 0 blanks
- Giảm giá từ Combo của Shop: text/mixed; role `unclassified`; 0 blanks
- Shopee Xu được hoàn: text/mixed; role `unclassified`; 0 blanks
- Số tiền được giảm khi thanh toán bằng thẻ Ghi nợ: text/mixed; role `unclassified`; 0 blanks
- Trade-in Discount: text/mixed; role `unclassified`; 0 blanks
- Trade-in Bonus: text/mixed; role `unclassified`; 0 blanks
- Phí vận chuyển (dự kiến): text/mixed; role `unclassified`; 0 blanks
- Trade-in Bonus by Seller: text/mixed; role `unclassified`; 0 blanks
- Phí vận chuyển mà người mua trả: text/mixed; role `shipping`; 0 blanks
- Phí vận chuyển tài trợ bởi Shopee (dự kiến): text/mixed; role `unclassified`; 0 blanks
- Phí vận chuyển trả hàng (đơn Trả hàng/hoàn tiền): text/mixed; role `unclassified`; 0 blanks
- Tổng số tiền người mua thanh toán: text/mixed; role `payment_alt`; 0 blanks
- Thời gian hoàn thành đơn hàng: text/mixed; role `unclassified`; 14,370 blanks
- Thời gian đơn hàng được thanh toán: text/mixed; role `paid`; 5,969 blanks
- Phương thức thanh toán: text/mixed; role `unclassified`; 0 blanks
- Phí cố định: text/mixed; role `unclassified`; 0 blanks
- Phí Dịch Vụ: text/mixed; role `unclassified`; 0 blanks
- Phí xử lý giao dịch: text/mixed; role `unclassified`; 8,254 blanks
- Phí thanh toán: text/mixed; role `unclassified`; 78,542 blanks
- Tiền ký quỹ: text/mixed; role `unclassified`; 0 blanks
- Người Mua: text/mixed; role `private_or_source_specific`; 314 blanks
- Tên Người nhận: text/mixed; role `private_or_source_specific`; 0 blanks
- Số điện thoại: text/mixed; role `private_or_source_specific`; 0 blanks
- Tỉnh/Thành phố: text/mixed; role `province`; 0 blanks
- TP / Quận / Huyện: text/mixed; role `unclassified`; 0 blanks
- Quận: text/mixed; role `unclassified`; 34,546 blanks
- Địa chỉ nhận hàng: text/mixed; role `private_or_source_specific`; 0 blanks
- Quốc gia: text/mixed; role `unclassified`; 0 blanks
- Ghi chú: empty; role `private_or_source_specific`; 86,796 blanks

### Shopee_Quasure.xlsx

Empty fields: 1; constant non-private candidates: 10.

| Field | Earliest | Latest | Parse failures |
|---|---|---|---:|
| created | 2025-04-21T17:31:00 | 2026-10-18T12:22:00 | 0 |
| delivered | 2025-04-22T15:58:00 | 2026-10-17T20:58:00 | 0 |
| paid | 2025-04-21T18:01:00 | 2026-10-18T12:22:00 | 0 |
| shipped | 2025-04-22T16:00:00 | 2026-10-17T16:00:00 | 0 |

Columns (name: inferred Python value type; blank count):

- Mã đơn hàng: text/mixed; role `order`; 0 blanks
- Mã Kiện Hàng: text/mixed; role `package`; 1,843 blanks
- Ngày đặt hàng: text/mixed; role `created`; 0 blanks
- Trạng Thái Đơn Hàng: text/mixed; role `status`; 0 blanks
- Sản Phẩm Bán Chạy: text/mixed; role `unclassified`; 0 blanks
- Lý do hủy: text/mixed; role `unclassified`; 12,616 blanks
- Nhận xét từ Người mua: text/mixed; role `private_or_source_specific`; 14,554 blanks
- Mã vận đơn: text/mixed; role `tracking`; 1,843 blanks
- Đơn Vị Vận Chuyển: text/mixed; role `unclassified`; 0 blanks
- Phương thức giao hàng: text/mixed; role `unclassified`; 1,843 blanks
- Loại đơn hàng: text/mixed; role `unclassified`; 14,424 blanks
- Ngày giao hàng dự kiến: text/mixed; role `unclassified`; 987 blanks
- Ngày gửi hàng: text/mixed; role `shipped`; 1,874 blanks
- Thời gian giao hàng: text/mixed; role `delivered`; 2,028 blanks
- Trạng thái Trả hàng/Hoàn tiền: text/mixed; role `refund_status`; 14,603 blanks
- SKU sản phẩm: text/mixed; role `product_sku`; 8,680 blanks
- Tên sản phẩm: text/mixed; role `product`; 0 blanks
- Cân nặng sản phẩm: text/mixed; role `unclassified`; 0 blanks
- Tổng cân nặng: text/mixed; role `unclassified`; 0 blanks
- Tên kho hàng: text/mixed; role `warehouse`; 0 blanks
- SKU phân loại hàng: text/mixed; role `sku`; 82 blanks
- Tên phân loại hàng: text/mixed; role `unclassified`; 6,053 blanks
- Giá gốc: text/mixed; role `unit_price`; 0 blanks
- Người bán trợ giá: text/mixed; role `seller_discount`; 0 blanks
- Được Shopee trợ giá: text/mixed; role `platform_discount`; 0 blanks
- Tổng số tiền được người bán trợ giá: text/mixed; role `unclassified`; 0 blanks
- Giá ưu đãi: text/mixed; role `net_item`; 0 blanks
- Số lượng: text/mixed; role `quantity`; 0 blanks
- Số lượng sản phẩm được hoàn trả: text/mixed; role `returned_quantity`; 0 blanks
- Tổng số tiền Người mua thanh toán: text/mixed; role `payment`; 0 blanks
- Tổng giá trị đơn hàng (VND): text/mixed; role `order_amount`; 0 blanks
- Mã giảm giá của Shop: text/mixed; role `unclassified`; 0 blanks
- Hoàn Xu: text/mixed; role `unclassified`; 0 blanks
- Mã giảm giá của Shopee: text/mixed; role `unclassified`; 0 blanks
- Chỉ tiêu Combo Khuyến Mãi: text/mixed; role `unclassified`; 0 blanks
- Giảm giá từ combo Shopee: text/mixed; role `unclassified`; 0 blanks
- Giảm giá từ Combo của Shop: text/mixed; role `unclassified`; 0 blanks
- Shopee Xu được hoàn: text/mixed; role `unclassified`; 0 blanks
- Số tiền được giảm khi thanh toán bằng thẻ Ghi nợ: text/mixed; role `unclassified`; 0 blanks
- Trade-in Discount: text/mixed; role `unclassified`; 0 blanks
- Trade-in Bonus: text/mixed; role `unclassified`; 0 blanks
- Phí vận chuyển (dự kiến): text/mixed; role `unclassified`; 0 blanks
- Trade-in Bonus by Seller: text/mixed; role `unclassified`; 0 blanks
- Phí vận chuyển mà người mua trả: text/mixed; role `shipping`; 0 blanks
- Phí vận chuyển tài trợ bởi Shopee (dự kiến): text/mixed; role `unclassified`; 0 blanks
- Phí vận chuyển trả hàng (đơn Trả hàng/hoàn tiền): text/mixed; role `unclassified`; 0 blanks
- Tổng số tiền người mua thanh toán: text/mixed; role `payment_alt`; 0 blanks
- Thời gian hoàn thành đơn hàng: text/mixed; role `unclassified`; 2,285 blanks
- Thời gian đơn hàng được thanh toán: text/mixed; role `paid`; 942 blanks
- Phương thức thanh toán: text/mixed; role `unclassified`; 0 blanks
- Phí cố định: text/mixed; role `unclassified`; 0 blanks
- Phí Dịch Vụ: text/mixed; role `unclassified`; 0 blanks
- Phí xử lý giao dịch: text/mixed; role `unclassified`; 0 blanks
- Tiền ký quỹ: text/mixed; role `unclassified`; 0 blanks
- Người Mua: text/mixed; role `private_or_source_specific`; 30 blanks
- Tên Người nhận: text/mixed; role `private_or_source_specific`; 0 blanks
- Số điện thoại: text/mixed; role `private_or_source_specific`; 0 blanks
- Tỉnh/Thành phố: text/mixed; role `province`; 0 blanks
- TP / Quận / Huyện: text/mixed; role `unclassified`; 0 blanks
- Quận: text/mixed; role `unclassified`; 8,820 blanks
- Địa chỉ nhận hàng: text/mixed; role `private_or_source_specific`; 0 blanks
- Quốc gia: text/mixed; role `unclassified`; 0 blanks
- Ghi chú: empty; role `private_or_source_specific`; 14,725 blanks
