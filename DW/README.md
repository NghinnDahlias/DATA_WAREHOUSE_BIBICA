# Kho dữ liệu và ETL

- `postgresql/`: DDL, khóa, index và migration bổ sung cho read models.
- `etl/`: đọc nguồn, chuẩn hóa, DQ, upsert facts và xuất/kiểm định Raw–Silver–Golden.
- `04_sql/olap/`: SQL tổng hợp và materialized views.
- `architecture/`: Galaxy Schema, measure catalog, DBML và data dictionary.
- `documentation/`: thiết kế ETL, các lớp dữ liệu và quy tắc category/địa lý.

Grain: một đơn, một dòng hàng được chấp nhận, một review. Core Galaxy có 12 dimension và 3 fact; các bảng phụ trợ phục vụ nhãn/nội dung review không thay grain nghiệp vụ.

API/DSS dùng các read views trong migration040; nội dung review đã che thông tin dùng bảng phụ trợ migration050. Các nguồn không được sửa hoặc re-save. Tiền đơn không cộng lặp theo dòng SKU.

Chạy ETL và ứng dụng: [README chính](../README.md). Quy tắc chỉ số: [KPI Contract](../docs/KPI_CONTRACT.md). Kiểm định và test: [TESTING](../docs/TESTING.md).
