"""Machine-readable, versioned KPI contract. Formulas are implemented in repository.py."""
VERSION = '2026-11-05-kpi-v1'
METRICS = [
    ('M01', 'orders', 'Đơn đặt', 'order', 'COUNT(*)', 'orders'),
    ('M02', 'booked_payable', 'Thanh toán đặt hàng quan sát', 'order', 'SUM(order_payable)', 'VND'),
    ('M03', 'completed_payable', 'Thanh toán đơn hoàn thành', 'order', 'SUM(order_payable) FILTER COMPLETED', 'VND'),
    ('M04', 'gross_item_value', 'Giá trị hàng gốc', 'item', 'SUM(gross_item_value)', 'VND'),
    ('M05', 'completed_gross_item_value', 'Giá trị hàng gốc hoàn thành', 'item', 'SUM(gross_item_value) FILTER COMPLETED', 'VND'),
    ('M06', 'completed_units', 'Sản lượng hoàn thành', 'item', 'SUM(quantity) FILTER COMPLETED', 'units'),
    ('M07', 'completed_aov', 'AOV thanh toán hoàn thành', 'order', 'M03 / completed_orders_with_payable', 'VND/order'),
    ('M08', 'cancellation_rate', 'Tỷ lệ hủy', 'order', 'canceled_orders / M01', 'fraction'),
    ('M09', 'observed_refund', 'Hoàn tiền quan sát', 'order', 'SUM(observed_refund)', 'VND'),
    ('M10', 'refund_order_rate', 'Tỷ lệ đơn ghi hoàn tiền', 'order', 'refund_positive_orders / refund_observed_orders', 'fraction'),
    ('M11', 'seller_discount', 'Trợ giá người bán', 'item', 'SUM(seller_discount)', 'VND'),
    ('M12', 'seller_discount_rate', 'Áp lực giảm giá', 'item', 'SUM(discount) / SUM(gross) on same observed pair cohort', 'fraction'),
    ('M13', 'mean_created_to_recorded_delivery_days', 'Ngày tạo đến ghi giao/hoàn thành', 'order', 'AVG(delivered_at-created_at) WHERE >=0', 'days'),
    ('M14', 'review_stars_mean', 'Điểm sao', 'review', 'AVG(star_level)', 'stars'),
    ('M15', 'low_review_rate', 'Review thấp', 'review', 'COUNT(star_level<=2) / reviews', 'fraction'),
    ('M16', 'review_order_coverage', 'Độ phủ đánh giá TikTok quan sát', 'order', 'reviewed_tiktok_orders / tiktok_orders in order cohort', 'fraction'),
]


def contract():
    return {
        'version': VERSION,
        'metrics': [dict(zip(('id', 'key', 'label', 'grain', 'formula', 'unit'), values)) for values in METRICS],
        'unavailable_metrics': [
            {'id': 'M17', 'key': 'growth', 'status': 'UNAVAILABLE',
             'reason': 'Ngày/tháng quan sát không chứng minh snapshot xuất đủ ngày để tính tăng trưởng.'},
            {'id': 'M18', 'key': 'cross_platform_discount', 'status': 'UNAVAILABLE',
             'reason': 'Chưa có contract gộp chiết khấu sàn cross-platform cùng ngữ nghĩa per-unit/per-line.'},
        ],
        'policies': [
            'NULL khác 0. Tổng không có quan sát là NULL. Coverage và mẫu số đi kèm.',
            'COMPLETED khác DELIVERED. UNKNOWN nằm trong mẫu số đơn.',
            'Tiền đơn tính một lần. Kho/category lọc bằng EXISTS trên cùng dòng.',
            'Category lịch sử từ tên dòng, không dùng category gốc TikTok.',
            'Shopee ghi thời gian hoàn thành, TikTok ghi Delivered Time. Không gộp thành SLA vận chuyển thực.',
            'Review trong cohort ngày tạo đơn và review_date <= end_date nếu có. Không nối nhân với dòng hàng.',
            'Không có lợi nhuận, quyết toán, tồn kho hoặc hạn dùng quan sát.',
        ],
    }
