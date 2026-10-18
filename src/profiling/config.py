"""Phase 1 source contracts. Column names are checked against the actual exports."""

SOURCES = {
    "tiktok_sales": ("Tiktokshop_Bibica.csv", "tiktok", "Bibica TikTok Shop"),
    "tiktok_reviews": ("Tiktokshop_Bibica_Rating.csv", "review", "Bibica TikTok Shop"),
    "shopee_bibica": ("Shopee_Bibica.xlsx", "shopee", "Bibica Official Store"),
    "shopee_quasure": ("Shopee_Quasure.xlsx", "shopee", "Quasure specialized store"),
}

FIELDS = {
    "tiktok": {
        "order": "Order ID", "sku": "SKU ID", "product": "Product Name",
        "quantity": "Quantity", "status": "Order Status", "created": "Created Time",
        "paid": "Paid Time", "shipped": "Shipped Time", "delivered": "Delivered Time",
        "cancelled": "Cancelled Time", "package": "Package ID", "tracking": "Tracking ID",
        "unit_price": "SKU Unit Original Price", "gross": "SKU Subtotal Before Discount",
        "seller_discount": "SKU Seller Discount", "platform_discount": "SKU Platform Discount",
        "net_item": "SKU Subtotal After Discount", "order_amount": "Order Amount",
        "refund": "Order Refund Amount", "shipping": "Shipping Fee After Discount",
        "warehouse": "Warehouse Name", "province": "Province",
    },
    "shopee": {
        "order": "Mã đơn hàng", "sku": "SKU phân loại hàng", "product_sku": "SKU sản phẩm",
        "product": "Tên sản phẩm", "quantity": "Số lượng", "status": "Trạng Thái Đơn Hàng",
        "created": "Ngày đặt hàng", "paid": "Thời gian đơn hàng được thanh toán",
        "shipped": "Ngày gửi hàng", "delivered": "Thời gian giao hàng",
        "package": "Mã Kiện Hàng", "tracking": "Mã vận đơn",
        "unit_price": "Giá gốc", "seller_discount": "Người bán trợ giá",
        "platform_discount": "Được Shopee trợ giá", "net_item": "Giá ưu đãi",
        "order_amount": "Tổng giá trị đơn hàng (VND)",
        "payment": "Tổng số tiền Người mua thanh toán",
        "payment_alt": "Tổng số tiền người mua thanh toán",
        "returned_quantity": "Số lượng sản phẩm được hoàn trả",
        "refund_status": "Trạng thái Trả hàng/Hoàn tiền",
        "shipping": "Phí vận chuyển mà người mua trả",
        "warehouse": "Tên kho hàng", "province": "Tỉnh/Thành phố",
    },
    "review": {
        "order": "order_id", "product_id": "product_id", "product": "product_name",
        "sku_spec": "sku_specification", "rating": "star_level",
        "text": "review_text", "other_text": "other_text", "created": "review_date",
    },
}

NUMERIC = {"quantity", "returned_quantity", "unit_price", "gross", "seller_discount",
           "platform_discount", "net_item", "order_amount", "payment", "payment_alt",
           "refund", "shipping", "rating"}
DATES = {"created", "paid", "shipped", "delivered", "cancelled"}
PII_PARTS = ("buyer", "recipient", "phone", "address", "username", "người mua",
             "người nhận", "điện thoại", "địa chỉ", "user_name", "message", "ghi chú")
