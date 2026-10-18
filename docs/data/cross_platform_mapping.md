# Cross-platform schema mapping

The full machine-readable mapping is `reports/schema_mapping.csv`. Classifications describe semantic compatibility, not only matching names.

| Concept | TikTok | Shopee | Class |
|---|---|---|---|
| order_identifier | Order ID | Mã đơn hàng | DIRECT |
| product_identifier | — | SKU sản phẩm | AMBIGUOUS |
| sku_identifier | SKU ID | SKU phân loại hàng | AMBIGUOUS |
| quantity | Quantity | Số lượng | DIRECT |
| unit_price | SKU Unit Original Price | Giá gốc | AMBIGUOUS |
| gross_item_amount | SKU Subtotal Before Discount | — | DERIVED |
| seller_discount | SKU Seller Discount | Người bán trợ giá | AMBIGUOUS |
| platform_discount | SKU Platform Discount | Được Shopee trợ giá | AMBIGUOUS |
| net_item_amount | SKU Subtotal After Discount | Giá ưu đãi | AMBIGUOUS |
| buyer_payment | Order Amount | Tổng số tiền Người mua thanh toán | AMBIGUOUS |
| shipping_buyer_charge | Shipping Fee After Discount | Phí vận chuyển mà người mua trả | AMBIGUOUS |
| refund_amount | Order Refund Amount | — | UNAVAILABLE |
| order_status | Order Status | Trạng Thái Đơn Hàng | TRANSFORM |
| order_date | Created Time | Ngày đặt hàng | DIRECT |
| payment_date | Paid Time | Thời gian đơn hàng được thanh toán | DIRECT |
| shipping_date | Shipped Time | Ngày gửi hàng | AMBIGUOUS |
| delivery_date | Delivered Time | Thời gian giao hàng | AMBIGUOUS |
| storefront | — | — | DERIVED |
| sales_channel | — | — | DERIVED |
| warehouse | Warehouse Name | Tên kho hàng | AMBIGUOUS |
| destination_province | Province | Tỉnh/Thành phố | TRANSFORM |

DIRECT means a defensible same-level concept, not proven accounting equivalence. AMBIGUOUS fields remain source-specific in the Phase 2 contract. Source identity supplies channel and storefront. Preserve Bibica Official Store and Quasure specialized store as distinct storefront members; Quasure is a product line, not automatically a separate company.
