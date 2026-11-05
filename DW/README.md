# Chỉ mục DW

- `postgresql/`: DDL gốc giữ nguyên và migration030 bổ sung canonical category, operational state, source identity và FK theo kho/shop.
- Migration040 bổ sung analytics.v_orders/v_items/v_reviews và dss.v_route_orders cho API/DSS, không đổi Galaxy keys/grain. Xem docs/API_RUNBOOK.md và docs/DSS_ALGORITHMS.md ở repo root.
- `etl/run.py`: CLI ổn định. `sources.py`: projection/contracts; `engine.py`: COPY và transaction; `transform.sql`: DQ/dimensions; `facts.py`: upsert facts; `validation.py`: assertion gates; `processing.py`/`verify.py`: private layers và reload.
- `04_sql/olap/`: SQL tổng hợp và5materialized views.
- `architecture/`: kiến trúc, Galaxy, DBML và dictionary cập nhật từ database.
- `documentation/`: ETL/data layers/category/geography runbook.
- `07_documentation/implementation_status.md`: trạng thái hiện hành. Các snapshot kiểm chứng cũ được ghi nhãn lịch sử.
