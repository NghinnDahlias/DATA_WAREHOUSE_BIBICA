# Đánh giá độc lập phân bổ kho Phase2

Ngày05/11/2026. Phạm vi gồm eligibility, whole-order MILP, stock/capacity/shelf constraints, policy bánh ăn sáng và diễn giải rủi ro. Không thay đổi raw, ETL, Galaxy hoặc mã production từ nhánh đánh giá độc lập này. Các sửa production do luồng chính thực hiện rồi được kiểm lại bằng bộ test này.

## Phương pháp và bằng chứng

`tests/test_dss_business.py` có25business test methods. Trong đó một test chạy30bài toán seeded với exhaustive oracle độc lập. `scripts/assess_allocation.py` đọc PostgreSQL read-only bibica_repo, dùng toàn bộ route aggregates đúng shop/kho/tỉnh, chọn hai SKU thương mại quan sát tại cả hai kho của mỗi shop, rồi chạy30resource scenarios/shop. Tổng90bài toán, mỗi bài3đơn nguyên, tối đa27phương án kho/unassigned được liệt kê độc lập.

Oracle không dùng ma trận ràng buộc hoặc hàm tối ưu của production. Nó tự cộng SKU quantities theo kho, kiểm capacity cả batch, ưu tiên số đơn phục vụ rồi so tổng unperturbed objective cost. Feasible route eligibility được kiểm bằng các test nghiệp vụ riêng, do vậy không dùng oracle optimization để chứng minh thay cho policy eligibility.

Baseline là time-first greedy theo thứ tự đơn, chỉ chọn khi toàn bộ SKU và capacity còn đủ. Đây là baseline khả thi cùng inputs, không phải heuristic khoảng cách địa lý hoặc phân bổ cân bằng.

Evidence hiện hành ở `reports/phase2_assessment/allocation.json`, `allocation_tests.log`. Report có SHA256 code liên quan và4source snapshots, kiểm code không đổi trong lúc đánh giá. Kết quả thất bại trước sửa được giữ ở allocation_initial.json và allocation_initial_tests.log. Không sử dụng61test cũ làm bằng chứng mới của các business rules bổ sung.

## Ma trận truy vết

| ID | Nghiệp vụ / grain / inputs | Công thức hoặc expected result | Test và evidence |
|---|---|---|---|
| A01 | Kho có hàng, nhiều đơn cùng SKU | Chọn kho có objective tốt hơn, không ép chia đều | balanced_split_is_not_an_objective, mọi đơn có thể cùngHN |
| A02 | Khách Hà Nội, stockHN=0, stockHCM đủ | HCM là phương án hợp lệ, không suy lịch sử cross-region chứng minh hết hàng | northern_customer_can_legitimately_ship_from_south |
| A03 | Mixed order2SKU, mỗi kho thiếu một SKU khác nhau | UNASSIGNED, không tách đơn hoặc gộp tồn giữa kho | whole_mixed_order_cannot_split_stock_across_warehouses |
| A04 | Hai đơn2units, toàn mạng chỉ có3units khả dụng tại một kho | Tối đa1đơn được phục vụ, không kiểm stock riêng từng đơn rồi oversell | network_shortage_does_not_oversell_stock, oracle independently sums quantities |
| A05 | CapacityHN=0,HCM=1 cho batch2đơn | Chỉ1đơn ởHCM | capacity_applies_to_full_batch |
| A06 | Nguồn tồn kho sỉ | WHOLESALE không đủ điều kiện phục vụ TMĐT | wholesale_stock_cannot_be_used_for_ecommerce |
| A07 | Tên explicit ăn sáng/bữa sáng/breakfast | Mặc địnhHN, HCM nhanh hơn không tự mở ngoại lệ | breakfast_defaults_to_hanoi_even_if_hcm_duration_is_lower |
| A08 | Hura chỉ là brand/family cue, không explicit breakfast | Không tự gán defaultHN vì brand, vẫn giữ shelf caution riêng | name_policy_distinguishes_explicit_breakfast_from_brand |
| A09 | BreakfastHN hết hàng, HCM có generic stock | Không tự giả ngoại lệ TMĐT, trảUNASSIGNED | hanoi_stockout_does_not_invent_southern_exception |
| A10 | BreakfastHCM được xác nhận scenario riêng | Cần exception scopedSKU/kho, reason/evidence_ref/confirmation, ECOMMERCEstock và HSD hợp lệ | documented_ecommerce_exception_allows_hcm vàexception validation tests |
| A11 | Có exception nhưng stockWHOLESALE/UNVERIFIED hoặc hạn còn1ngày | Exception không bỏ qua stock scope hoặc shelf buffer | exception_does_not_override_wholesale_stock_or_shelf_life |
| A12 | ManualSKU breakfast override và mixedSKU | Cùng defaultHN, exception không bỏ qua stockoutSKU khác | manual_breakfast_sku_override_uses_same_default_policy, breakfast_exception_does_not_override_other_sku_stockout |
| A13 | Mixed commercial+gift order | Giữ đủ giftSKU, chỉ phân bổ khi gift có stockECOMMERCE minh thị | mixed_commercial_gift_keeps_all_skus_with_explicit_gift_stock |
| A14 | Gift thiếu stock hoặc stock chỉUNVERIFIED/assume_available | Không tự giả tồn quà tặng | mixed_gift_cannot_use_missing_unverified_or_assumed_stock |
| A15 | Gift-only / mixedUnmapped | Manual review, không loại im một SKU rồi nhận đã phân bổ nguyên đơn | gift_only_requires_manual_review_even_with_stock, unmapped_sku_is_not_silently_removed_from_mixed_order |
| A16 | Cùng scenario, đảo orders/kho/stock/capacity dictionary | Maporder_ref→warehouse không đổi | reordered_orders_warehouses_and_resources_preserve_mapping |
| A17 | MILP seeded fixtures | Served count vàcost khớp exhaustive oracle đến7decimal places |30unit cases +90real-history scenarios |
| A18 | Solver timeout có feasible incumbent | Không tuyên bố optimum, trả failure để API xử lý503 | solver_timeout_with_feasible_incumbent_is_not_optimal |
| A19 | SolverNaN, bounds[-1,0,2], status1 hoặc mip_gap0,1 | Từ chối result không hữu hạn/binary/certified optimal | solver_nonfinite_bounds_and_nonoptimal_gap_rejected |
| A20 | Không có reviews so với có reviews nhưng0bad | Thành phần missing làunavailable, không phải0risk | reviews_missing_differ_from_zero_bad_reviews |
| A21 | Tăng review risk weight và giữ cùng counts | Score sensitivity có thể đổi, không gọi xác suất | review_weight_sensitivity_does_not_claim_probability |

Các quantities, tồn kho, HSD, capacity, incoming demand trong tests/scenarios là giả định. Route durations, cancellation và review aggregates trong90cases là quan sát từ DW thật. Tất cả số tiền được loại khỏi assignment objective vì chưa có contract giá trị đơn mới hoặc chi phí vận tải/hư hỏng.

## Kết quả và lỗi trước sửa

Baseline assessment thực đầu tiên chạy18test methods, có9failed assertion/subtest events và0errors. Các nhóm lỗi gồm HCM chưa có default-breakfast guard, dùng wholesale stock cho TMĐT, mapping phụ thuộc thứ tự input và solver result chưa kiểm hữu hạn/bounds/status/gap đầy đủ. Đây là các repro đã thực thi, không phải suy đoán dựa trên code đọc.

Sau sửa policy, mixed-gift eligibility và solver guards, lần chạy cuối lúc15:27UTC ngày05/11/2026 đạt25/25business test methods PASS,0fail/0error/0skip,90/90scenario cases khớp exhaustive oracle và không vi phạm aggregate stock/capacity, tổng7,118s. Kết quả hiện hành ở allocation.json, các lần chạy trung gian18/21methods không thay kết quả final25methods. MILP phục vụ nhiều hơn baseline greedy ở6/90cases. Kết quả này chỉ chứng minh lợi ích tối ưu trong các resource scenarios đã định nghĩa, không chứng minh doanh thu tăng hoặc số ca hư hỏng tránh được ngoài thực tế.

Objective ưu tiên số đơn được phục vụ trước tổng weighted risk/time. Nó có thể ưu tiên nhiều đơn ít hàng thay vì một đơn nhiều hàng, chưa tối đa doanh thu hoặc lợi nhuận. Không có giá trị đơn nhu cầu mới/chi phí vận tải/thiệt hại đã được xác thực để chứng minh tradeoff kinh tế. Ngưỡng hard delivery/HSD chặn phương án vi phạm trước khi tối ưu, do vậy nhiều đơn được phục vụ hơn chỉ được tính trong vùng khả thi đã cấu hình.

## Coverage whole-order và quà tặng

Đối chiếu toàn bộ lịch sử cho thấy5275mixed commercial+gift orders tại Shopee Bibica,347tại Quasure,1255tại TikTok Bibica, tổng6877đơn. Logic cũ từ chối mọi gift line nên đây là coverage gap đáng kể đối với whole-order fulfillment.

Sửa có giới hạn cho phép mixed commercial+gift khi có ít nhất một commercialSKU và giftstockECOMMERCE được nhập minh thị. Gift-only vẫn manual review, gift không tham gia historical commercial scoring cohort, mọi SKU vẫn dùng inventory constraint nguyên đơn. Không tự giả giftpayment=0 hoặc bỏ giftSKU khỏi đơn.

Có367/4/333orders tương ứng ba nguồn chứa UnmappedSKU, tổng704orders. Chưa phân loại được là điều kiện manual review. Các sốgift/Unmapped có thể chồng lấp và không được cộng thành một tổng backlog nếu chưa dùng union ở grain order.

## Kết luận readiness có điều kiện

Logic eligibility/tối ưu phù hợp cho DSS mô phỏng và đề xuất có giải thích sau các regression mới. Khách phía Bắc xuất từHCM không bị đánh lỗi chỉ vì khác vùng. Hai warehouse members cùng nhãn vùng của các shop vẫn có namespace độc lập. Không có objective cân bằng kho.

Để chốt Phase2 cần đọc đồng thời báo cáo này với rating/KPI/API assessment và các gates mới của luồng chính. Đây không phải chứng nhận tự động vận hành WMS. Nguồn chưa có tồn kho khả dụng theo lô, HSD thực, capacity thực, lý do stockout/chuyển kho hoặc stock reservation liên request. Constraints chỉ nhất quán trong một batch scenario, không giữ chỗ hàng cho các requests độc lập.

Historical risk score và p90 chưa được hiệu chuẩn thành xác suất thất bại/hư hỏng. Thay extra_delay làm p90 scenario/cost/feasibility thay đổi, thành phần late risk vẫn được diễn giải là tỷ lệ lịch sử theo ngưỡng cấu hình. Một review nghiêm trọng dù hiếm cần được trình bày riêng theo evidence trong review assessment, không được dùng mean score thấp thay thế xác minh nguyên nhân.

Lệnh tái lập từ root repo dùng `..\.venv\Scripts\python.exe -X utf8 scripts/assess_allocation.py`. PostgreSQL bibica_repo55432 phải đang chạy. Script chỉ đọc database và ghi aggregate/hash reports. Không cần source buyer rows trong log, không commit/push và không triển khai frontend.
