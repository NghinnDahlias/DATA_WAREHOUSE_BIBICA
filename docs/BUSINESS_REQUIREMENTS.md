# Yêu cầu nghiệp vụ

## Mục tiêu

Hợp nhất dữ liệu Shopee Bibica, Shopee Quasure và TikTok Bibica để phân tích doanh số, vận hành kho/giao hàng và trải nghiệm khách hàng; hỗ trợ so sánh phương án phân bổ đơn.

## Câu hỏi và chức năng

| Nhu cầu | Chức năng | Chỉ số chính |
|---|---|---|
| Tổng quan kinh doanh | Dashboard liên kết, bộ lọc và popup thống kê | Đơn đặt, tiền đơn hoàn thành, sản lượng, AOV, tỷ lệ hủy |
| Hiệu quả bán hàng | Phân tích theo thời gian, kênh, cửa hàng, category và SKU | Xu hướng, đóng góp, xếp hạng sản phẩm |
| Vận hành | Phân tích kho, tỉnh nhận và thời gian giao theo từng nguồn | Số mẫu, median/p90, hủy đơn, phạm vi tuyến |
| Trải nghiệm khách hàng | Rating TikTok, nhãn chủ đề và đọc case tiêu cực | Số review, điểm sao, tỷ lệ 1–2 sao, độ phủ |
| Quyết định phân bổ | Phân bổ nguyên đơn, what-if và sensitivity | Số đơn được phân bổ, ràng buộc, thời gian và rủi ro lịch sử |
| Chất lượng dữ liệu | ETL validation, quarantine và truy vết nguồn | Duplicates, thiếu dữ liệu, khóa ngoại, reconciliation |

## Quy tắc bắt buộc

- Phân biệt kênh, cửa hàng, SKU, kho xuất và tỉnh khách; giữ khóa theo phạm vi nguồn.
- Tiền đơn chỉ tính một lần; chỉ số dòng hàng và review tính ở grain riêng.
- Cùng bốn category Bánh/Kẹo/Ngũ cốc/Quà tặng cho cả ba nguồn, phân loại theo tên.
- Review chỉ có TikTok. Không có nguồn không đồng nghĩa khách không phản ánh vấn đề.
- Nhãn review là đề cập từ khóa chưa xác minh; chỉ hiển thị nội dung đã che thông tin cá nhân.
- Tồn kho, hạn dùng và năng lực xử lý trong DSS là giả định đầu vào, không phải dữ liệu vận hành đã quan sát.
- Không suy lợi nhuận, hiệu quả quảng cáo hay quan hệ nhân quả khi thiếu contract dữ liệu.

Các công thức và mẫu số thống nhất trong [KPI Contract](KPI_CONTRACT.md). Mô hình hỗ trợ quyết định và giới hạn nằm trong [DSS Algorithms](DSS_ALGORITHMS.md) và [DSS Evaluation](DSS_EVALUATION.md).
