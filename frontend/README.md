# Bibica Retail DSS Dashboard (React)

Giao diện phân tích dữ liệu bán lẻ Bibica gồm 5 màn hình, sử dụng bộ lọc dùng chung và kết nối Backend FastAPI qua API `/api/v1` (cổng 8001).

## Chạy dự án

### 1. Khởi chạy Backend

Mở terminal tại thư mục gốc của repository:

```powershell
# Tạo môi trường ảo (chỉ cần thực hiện lần đầu)
py -m venv .venv

# Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# Cài đặt dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Khởi chạy API
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001
```

Backend chạy tại `http://127.0.0.1:8001`.

Tài liệu API: `http://127.0.0.1:8001/docs`.

### 2. Khởi chạy Frontend

Mở terminal thứ hai tại thư mục gốc repository:

```powershell
cd frontend

# Cài đặt dependencies
npm install

# Khởi chạy môi trường phát triển
npm run dev
```

Truy cập: `http://localhost:5173`.

Các request `/api` được proxy tới Backend `127.0.0.1:8001` thông qua cấu hình Vite.

### 3. Kiểm thử và build

Thực hiện tại thư mục `frontend`:

```powershell
# Chạy kiểm thử
npm test

# Build production
npm run build
```

## Màn hình và phạm vi chức năng

| Trang | Nguồn API | Chức năng đã có | Giới hạn hiện tại |
|---|---|---|---|
| **Executive Overview** | `/overview/kpis`, `/analytics/{store,category,month}` | 5 KPI; giá trị đơn hoàn thành theo tháng và cửa hàng; mức đóng góp của cửa hàng và danh mục; chất lượng dữ liệu | Top sản phẩm được xem tại Sales Performance; chưa có KPI tăng trưởng (M17 UNAVAILABLE) |
| **Sales Performance** | `/overview/kpis`, `/analytics/*`, `/products` | Xu hướng theo kênh và tháng: giá trị đơn, số đơn, đơn hủy; phân tích theo cửa hàng, trạng thái, danh mục, vùng kho và tỉnh; xếp hạng sản phẩm; drill-down | Chưa có xu hướng ngày/tuần, số lượng bán theo tháng và tỷ lệ hủy theo sản phẩm |
| **Warehouse & Fulfillment** | `/overview/kpis`, `/operations/delivery`, `/analytics/*`, `/dss/risk` | Phân tích đơn hủy và thời gian giao theo kho, vùng kho và tỉnh; tuyến kho → tỉnh kèm điểm rủi ro | Tỷ lệ hủy theo kho chưa có endpoint tổng hợp riêng, hiện cần gọi KPI nhiều lần |
| **Customer Experience** | `/overview/kpis`, `/api/v1/customer/review-themes` | Số lượng đánh giá, điểm trung bình, tỷ lệ đánh giá 1–2 sao, độ phủ đánh giá, xu hướng theo tháng và danh mục; tổng hợp chủ đề đánh giá, số lượt nhắc đến, lượt nhắc đến trong đánh giá tiêu cực và tín hiệu cần xem xét về an toàn | Chưa có phân bố đầy đủ 1–5 sao và rating theo sản phẩm. Nhãn chủ đề được nhận diện bằng heuristic từ khóa, chưa được xác minh thủ công và không đại diện cho khiếu nại đã xác nhận |
| **DSS Simulation** | `/dss/allocate`, `/dss/what-if`, `/dss/sensitivity` | Nhập batch đơn hàng; thiết lập kịch bản tồn kho, công suất, độ trễ, ngưỡng và trọng số; so sánh phương án gốc với tối đa 4 phương án; xem kết quả phân bổ từng đơn và lý do loại kho; hỗ trợ kịch bản hạn sử dụng và ngoại lệ bữa sáng | Kết quả phụ thuộc dữ liệu và quy tắc của API DSS; tồn kho và hạn sử dụng trong mô phỏng là giả định kịch bản, không phải dữ liệu tồn kho thực tế |

## Review Themes – Customer Experience

Tính năng Review Themes được bổ sung nhằm hỗ trợ tổng hợp các chủ đề xuất hiện trong đánh giá khách hàng.

- Backend cung cấp endpoint `GET /api/v1/customer/review-themes`.
- Dữ liệu được lọc theo cohort dùng chung của repository.
- Kết quả tổng hợp gồm tổng số đánh giá, số đánh giá có nội dung, số đánh giá tiêu cực (1–2 sao), số đánh giá không có nhãn vấn đề rõ ràng và số đánh giá có tín hiệu an toàn cần xem xét.
- Các nhãn được tổng hợp theo số lượt nhắc đến và số lượt nhắc đến trong đánh giá tiêu cực.
- Bảng `dw.review_theme_feature` chỉ lưu nhãn, mức độ phân loại, cờ có nội dung đánh giá và phiên bản audit; không lưu nội dung review thô hoặc thông tin người mua.
- Nhãn được nhận diện bằng heuristic từ khóa, có trạng thái `UNVALIDATED_HEURISTIC_MENTION`.

**Lưu ý:** Nhãn chủ đề chỉ là tín hiệu hỗ trợ phân tích. Một đánh giá có thể có nhiều nhãn; nhãn không phải nguyên nhân, kết luận về chất lượng sản phẩm hoặc khiếu nại đã được xác minh.

## Quy ước hiển thị

Theo KPI Contract `2026-11-05-kpi-v1`:

- **Giá trị đơn hoàn thành** là tổng giá trị thanh toán quan sát của các đơn có trạng thái `COMPLETED`, mỗi đơn chỉ tính một lần. Không gọi chỉ số này là doanh thu thuần.
- Giá trị `NULL` được hiển thị là `—`, không tự động chuyển thành `0`.
- Không hiển thị phần trăm tăng/giảm so với kỳ trước do KPI M17 hiện ở trạng thái `UNAVAILABLE`.
- Không suy diễn lợi nhuận hoặc tồn kho thực tế từ dữ liệu hiện có.
- Bộ lọc **Kênh / cửa hàng** được gộp vì API hiện chỉ nhận một tham số `store`/`source`, chưa hỗ trợ lựa chọn tất cả kênh Shopee độc lập.
- Mặc định kỳ xem kết thúc trước ngày dữ liệu mới nhất 30 ngày (`MATURITY_DAYS` trong `context/FilterContext.jsx`) để hạn chế ảnh hưởng của các đơn mới chưa chuyển sang trạng thái hoàn thành. Khi kỳ xem chạm vào khoảng dữ liệu này, giao diện hiển thị cảnh báo.
- **Điểm rủi ro DSS** là chỉ số ưu tiên được tính theo quy tắc, không phải xác suất xảy ra rủi ro.
- Tồn kho, hạn sử dụng và các điều kiện phân bổ trong DSS là giả định đầu vào của kịch bản mô phỏng.
- **Review Themes** sử dụng nhãn heuristic từ khóa chưa được xác minh thủ công; không diễn giải nhãn thành khiếu nại đã xác nhận.

## Kiểm thử

Frontend hiện có 29 test, bao gồm:

- Kiểm thử lớp API và xử lý dữ liệu trả về.
- Kiểm thử dựng giao diện 5 màn hình.
- Kiểm thử bộ lọc và dữ liệu mẫu.
- Kiểm thử các luồng mô phỏng DSS và xử lý lỗi API.

**Trạng thái kiểm thử:** Lần chạy gần nhất được ghi nhận là 28/29 test đạt. Test còn lại liên quan đến selector `DEMO0` bị trùng giữa thẻ đơn hàng và bảng kết quả; đã có bản điều chỉnh selector và cần chạy lại `npm test` để xác nhận toàn bộ test đạt.

