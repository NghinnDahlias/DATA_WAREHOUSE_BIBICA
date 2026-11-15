# Đánh giá DSS và giới hạn sử dụng

## Phạm vi chấp nhận

DSS phù hợp cho phân tích và mô phỏng có giải thích. Kết quả không phải lệnh vận hành kho, tồn kho đã giữ chỗ, dự báo hư hỏng hay xác suất lỗi đã hiệu chuẩn.

Kiểm định phần mềm gồm MILP so với exhaustive oracle cho batch nhỏ, ràng buộc tồn kho/năng lực toàn batch, nguyên đơn, phạm vi shop, expiry assumptions, sample fallback, tính lặp lại và what-if. Test API kiểm riêng grain tiền đơn/dòng/review, cutoff, bộ lọc cùng dòng, phân trang, NULL và an toàn truy vấn. Cách chạy nằm trong [TESTING.md](TESTING.md).

## Kiểm định thời gian giao lịch sử

Kết quả holdout đã đo trên snapshot nguồn: train gồm các đơn tạo và ghi nhận giao đến 01/09/2026; test từ 02/09/2026 đến cuối quan sát từng nguồn. Chỉ dùng duration hợp lệ và cohort thương mại. Tuyến có ít nhất 20 mẫu được dùng, thiếu thì fallback cùng kho/shop; baseline dùng median kho.

| Cửa hàng | Mẫu test | MAE median tuyến (ngày) | MAE baseline kho (ngày) | Test không vượt p90 train |
|---|---:|---:|---:|---:|
| Bibica Shopee | 5.784 | 1,3096 | 1,3905 | 88,33% |
| Bibica TikTok | 10.146 | 0,3688 | 0,6763 | 84,91% |
| Quasure Shopee | 1.744 | 1,2953 | 1,4070 | 89,39% |

Đây là kết quả kiểm định lịch sử, không phải số đo được chạy lại khi chỉnh tài liệu. Thống kê tuyến giảm sai số trong tập đã quan sát nhưng p90 train không đạt 90% coverage ở holdout. Không diễn giải p90 thành cam kết giao hàng hoặc an toàn hạn dùng.

## Diễn giải kết quả

- Xem số đơn chưa phân bổ trước khi so chi phí. Giảm đơn phục vụ có thể làm cost thấp hơn mà không phải cải thiện vận hành.
- Chỉ so delta objective khi weights và normalization tương thích. Thay weights thể hiện ưu tiên kịch bản, không chứng minh lợi ích thực tế.
- Thiếu hoặc không đủ stock/evidence phải trả UNASSIGNED có lý do, không ép một kho vào nghiệm.
- Mean risk/time của hai tập đơn khác nhau không chứng minh thay kho tạo ra tác động nhân quả.

## Giới hạn dữ liệu

| Nội dung | Giới hạn |
|---|---|
| Trạng thái hủy | Snapshot hiện tại; thiếu event history để tái dựng point-in-time đầy đủ |
| Vận chuyển | Shopee completion là proxy, TikTok Delivered Time là ghi nhận giao; không gộp thành cùng một SLA |
| Rating | Chỉ TikTok, mẫu tự chọn; một đơn có thể có nhiều review |
| Chủ đề/ý kiến | Nhãn từ khóa chưa xác minh, nội dung che thông tin tự động; không chứng nhận nguyên nhân hay xử lý khiếu nại |
| Tài nguyên | Tồn kho, năng lực, HSD và độ trễ bổ sung là đầu vào kịch bản |
| Danh tính khách | Không có chuẩn định danh liên thông các sàn |
| Tài chính | Tiền thanh toán quan sát không phải lợi nhuận hay doanh thu quyết toán |

Không công bố AUROC/accuracy dự báo cho rule risk index khi chưa có nhãn và lịch sử trạng thái phù hợp. Customer-service promise/dispatch/receipt/resolution cũng chưa có event nguồn để xác nhận.

Trước vận hành thực cần nguồn WMS/lô hàng, xác nhận chính sách nghiệp vụ, đánh giá drift, xác thực/giám sát và kiểm thử tải. Kết quả local không chứng nhận Docker/cloud, production WMS hoặc hiệu quả điều phối ngoài thực địa.
