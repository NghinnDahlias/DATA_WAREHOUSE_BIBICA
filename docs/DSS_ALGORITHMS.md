# DSS phân bổ kho và rủi ro fulfillment

## Phạm vi quyết định

Đầu vào là batch tối đa50đơn nhu cầu mới, mỗi đơn có tỉnh khách và tối đa20SKU của cùng shop. Kho ứng viên chỉ là các warehouse_key của shop đó, thuộc hai nhãn vùng quan sát Hà Nội/Hồ Chí Minh. Sáu warehouse members vẫn độc lập theo shop, không biến hai nhãn vùng thành hai cơ sở dùng chung tồn kho.

Kết quả là phân bổ nguyên đơn có điều kiện trên các giả định người dùng cung cấp. Tất cả SKU trong đơn được giao cho một kho, không tách đơn hoặc tự chuyển tồn giữa shop. API không tạo shipment, không giữ chỗ tồn kho và không cập nhật fact lịch sử.

## Bằng chứng và chất lượng trường

| Trường | Có từ nguồn | Cách dùng |
|---|---|---|
| Tên kho gốc, warehouse scoped key | Có | Exact aliases HN/HCM, không suy từ tỉnh khách |
| Tỉnh khách | Có | Chuẩn chữ/tiền tố, giữ64tên lịch sử, Unknown kỹ thuật |
| SKU/tên sản phẩm/quantity | Có | SKU scoped theo shop, category name-only |
| Ngày gửi hàng | Có | Đã sửa header Unicode của Shopee và nạp lại |
| Delivered Time TikTok | Có | Thời điểm ghi nhận giao, không chứng minh khách thực nhận tuyệt đối |
| Thời gian hoàn thành Shopee | Có | Proxy ghi nhận hoàn thành, có thể trễ sau lúc giao |
| Trạng thái | Snapshot hiện tại | Tỷ lệ hủy hồi cứu, không tái dựng đầy đủ trạng thái tại as_of |
| Rating | TikTok, mẫu tự chọn | Đếm review riêng, review_date<=as_of, không nội suy cho Shopee |
| Tồn kho khả dụng/lô hàng | Không | Nhập scenario stocks, không gọi là stock thực |
| HSD/NSX/tuổi lô khi xuất | Không | Nhập remaining_shelf_days, không suy từ tên/date marketing |
| Năng lực xử lý kho | Không | capacity_orders theo batch scenario, thiếu nghĩa là không đặt giới hạn |
| Cước phí/distance/temperature/packing defect | Chưa có contract dùng được | Không dùng hàm chi phí hay spoilage model tự bịa |

Ngày ghi nhận không đủ không được thay bằng ngày tạo đơn. Lead time DSS dùng `(delivered_at-shipped_at)/86400` khi shipped>=created và delivered>=shipped. Không trim outlier bằng ngưỡng tùy ý. Thống kê n và chronology exclusions đi kèm.

## Cohort tuyến và fallback

`dss.v_route_orders` có một quan sát mỗi order/kho. Category thương mại Bánh/Kẹo/Ngũ cốc được lấy từ FK dòng lịch sử, gift/Unmapped-only không vào cohort DSS. Nhiều dòng SKU cùng kho không nhân order hoặc review. Nếu tỉnh trên các dòng của cùng order/kho không nhất quán thì route_province là Unknown.

Một đơn nhiều kho có thể đóng góp một lần cho từng kho. Không coi các nhóm này cộng được thành tổng orders, không phân bổ tiền order cho kho. Dữ liệu không có tracking parcel đáng tin để quy từng timestamp giao cho từng parcel, nên multi-warehouse timing cũng là proxy cấp đơn.

Trong cùng shop và cửa sổ history_start→as_of, ưu tiên warehouse+province có ít nhất20valid timing samples mặc định. Nếu thiếu, dùng warehouse trên mọi tỉnh khi đủ20mẫu, gắn `WAREHOUSE_ALL_PROVINCES` và requested_route_samples. Nếu cả hai thiếu, kho không đủ điều kiện. Không suy lead time từ khoảng cách hoặc tỉnh gần nhau. Input tỉnh không nhận diện bị từ chối.

Timing chỉ dùng delivery ghi nhận đến as_of. Review chỉ dùng review_date<=as_of. Category/name catalog là Type1 hiện hành, không giả là product history snapshot tại mọi cutoff. Trạng thái hủy là trạng thái snapshot cho cohort đơn, có thể được biết sau as_of khi nguồn thiếu ngày hủy. API luôn cảnh báo và không công bố predictive backtest cho risk score.

Các outcome có timestamp sau cutoff đã biết được loại khỏi denominator resolved/canceled của scoring và ghi known_future_outcomes_excluded. Trạng thái thiếu event time vẫn là snapshot có giới hạn, chưa tái dựng point-in-time đầy đủ.

Review gắn kho qua SKU lịch sử duy nhất trong đúng order. Order-only review chỉ gắn khi order có một warehouse phù hợp duy nhất. Đơn/SKU nhiều kho chưa phân biệt được thì giữ unattributed_reviews, không nhân cùng review cho từng kho. Review của gift-only/noncommercial không được suy thành lỗi một SKU thương mại.

## Scoring quy tắc

Ba thành phần là tỷ lệ hủy trên resolved orders, tỷ lệ duration vượt late_threshold_days trên valid timings, tỷ lệ review1–2sao trên accepted reviews. Resolved là COMPLETED/DELIVERED/CANCELED/RETURNED. PROCESSING/UNPAID/UNKNOWN không bị coi là thành công.

Ngưỡng review mặc định low_star_max=2 là cấu hình, có sensitivity1/2/3 qua Scenario và GET risk. Review caution công bố số1sao, số thấp theo ngưỡng, n review, Wilson interval, độ phủ orders và phần không gắn kho. Shopee thiếu rating source được báo UNAVAILABLE, không biến thành kho an toàn hoặc không có khiếu nại. Mean risk không thay mức nghiêm trọng từ nội dung review, nội dung được đánh giá offline trong assessment riêng có labels chưa được human validation.

Mỗi tỷ lệ có numerator và denominator riêng. Prior là cùng kho/shop trên mọi tỉnh, không dùng kho của shop khác. Với n quan sát và e sự kiện, prior rate p và pseudo-count a, tỷ lệ làm mượt là `(e+a*p)/(n+a)`. Mặc định a=20, có thể đổi trong scenario. Đây là regularization theo quy tắc.

Risk score =100×tổng effective_weight×smoothed_fraction. Default cancellation/late/review weights0,4/0,4/0,2. Thành phần n=0 là unavailable và effective_weight0, các trọng số khả dụng được chuẩn lại. Không gán thiếu review thành hài lòng hay rủi ro0. Trả available_weight_fraction, số quan sát, tỷ lệ gốc/làm mượt và weights thực dùng.

Evidence support SUPPORTED khi timing và resolved đều>=30, còn lại SPARSE. Fallback scope và sample sizes vẫn được trả riêng. Support là độ dày bằng chứng theo quy ước, không phải xác suất đúng. Review là route-level, không phải lỗi riêng của SKU. Không công bố calibrated failure probability, causal warehouse effect hoặc xác suất hư hỏng.

## Shelf-life cho bánh ăn sáng

Tên có ăn sáng/bữa sáng/breakfast hoặc token Hura được gắn breakfast_candidate để yêu cầu nhập hạn còn lại. Flag này không chứng minh bánh tươi, hạn ngắn hay NSX. Những tên Bánh khác vẫn có thể mô phỏng qua endpoint shelf-life khi canonical category là Bánh.

`p90_arrival_remaining = scenario_remaining_at_dispatch - historical_p90_lead - scenario_extra_delay`.

Candidate thỏa khi arrival remaining>=min_remaining_days và delivery p90+delay<=max_delivery_days. Breakfast candidate thiếu remaining_shelf_days không được phân bổ. HSD âm không hợp lệ. Một stock row là một nhóm tồn kho scenario gộp, không mô phỏng nhiều lô/FEFO hay tự nhận biết tuổi lô.

Theo background người dùng cung cấp, tên explicit ăn sáng/bữa sáng/breakfast mặc định chỉ đủ điều kiện xuất Hà Nội. Có thể thêm SKU qua breakfast_product_keys khi catalog đã xác nhận nhưng tên chưa thể hiện. Token Hura riêng chỉ giữ shelf caution, không tự suy mọi Hura thuộc nhóm mặc địnhHN.

HCM có thể là ngoại lệ TMĐT nếu Scenario.breakfast_exceptions khai đúng product_key/warehouse_key, reason HN_STOCKOUT_TRANSFER hoặc APPROVED_ECOMMERCE_EXCEPTION, evidence_ref và ecommerce_stock_confirmed=true. Stock cùng cặp cần stock_scope=ECOMMERCE và HSD phù hợp. Đây là xác nhận đầu vào scenario, DW chưa xác minh WMS thực. Generic stock hoặc historicalHCMsales không tự mở ngoại lệ. Stock_scope=WHOLESALE không dùng cho TMĐT ở mọi nhóm hàng. Ngoại lệ không bỏ qua tồn kho SKU khác hoặc constraints nguyên đơn.

Quan sát nguồn có1744dòng tên explicit breakfast gắnHCM và162gắnHN, khác thông lệ mới. Giữ facts lịch sử, yêu cầu xác nhận scopeSKU/hiệu lực và nhãn kho trước áp dụng vận hành. Kho khách khác vùng không tự chứng minh hết hàng hay sai quy trình, chuyển kho của hàng thường vẫn hợp lệ nếu đủ constraints.

Endpoint shelf-life còn tính chính xác trên SQL số duration lịch sử vượt `remaining-buffer-extra_delay`, chia cho n mẫu valid cùng scope tuyến/fallback, kèm Wilson95%interval. Đây là tần suất vượt ngưỡng giả định của durations quan sát, không phải xác suất bánh hỏng. Wilson là khoảng tham khảo theo mô hình mẫu độc lập, chưa xử lý tương quan thời gian/cluster.

## Tối ưu phân bổ

Binary variable x(order,warehouse) và u(order) unassigned. Mỗi đơn `SUM x+u=1`. Chỉ tạo biến kho cho candidate thỏa nguồn/store, category, bằng chứng, threshold, stock và shelf constraints.

- Tồn kho mỗi kho/SKU giới hạn tổng quantity của tất cả đơn được chọn, không chỉ kiểm từng đơn riêng.
- capacity_orders giới hạn số đơn của cả batch theo kho. Không tự chia thành daily capacity vì request không có lịch dispatch nhiều ngày.
- Mặc định stock_mode=required. Thiếu stock row thì candidate không đủ điều kiện. assume_available là lựa chọn minh thị, chỉ cho SKU đã quan sát tại kho đến cutoff, và tiếp tục bị đánh conditional.
- Stock scenario có thể khai một SKU chưa từng xuất từ kho cùng shop, nhưng đó là giả định bổ sung. Không nội suy SKU hoặc gộp kho khác shop.
- Mixed commercial+gift giữ đủ mọi SKU và được phân bổ khi gift có stockECOMMERCE minh thị. Gift không tham gia cohort/ranking thương mại. Gift-only và Unmapped cần manual review. Không ép giftpayment=0.

Candidate cost =risk_weight×risk_score/100 +(1-risk_weight)×p90_scenario_days/max_delivery_days. Feasible cost nằm0–1. Phạt unassigned bằng n_orders+1 để ưu tiên phục vụ nhiều đơn nhất trước khi tối thiểu tổng cost. Có epsilon nhỏ theo thứ tự candidate để ổn định tie. HiGHS qua scipy.optimize.milp, giới hạn10giây, yêu cầu chứng nhận optimum, mip_gap0. Kiểm lại nghiệm nguyên và mọi resource constraint. Không dùng nghiệm timeout chưa chứng nhận như optimum.

Variables, orders và resource rows được sắp theo stable order_ref/warehouse/product trước khi giải, do vậy đảo thứ tự input không thay mapping khi scenario tương đương. Post-check kiểm shape, finite values, bounds0–1, status, mip_gap, tính nguyên và constraints, kể cả khi backend báo success=True. Không có objective phân bổ cân bằng kho.

Đơn không phân bổ có lý do NO_FEASIBLE_WAREHOUSE hoặc SHARED_STOCK_OR_CAPACITY. Candidate giữ đầy đủ các lý do như thiếu stock, HSD, thiếu sample hoặc ngưỡng giao. Hàm mục tiêu không chứa profit hoặc chi phí vận tải chưa quan sát.

## What-if và sensitivity

Baseline và alternative đọc cùng PostgreSQL REPEATABLE READ snapshot, cùng đơn nhu cầu. Có thể đổi weights, min samples, delay, deadline, min remaining, stock/expiry và capacity. Trả changed_orders, các DEMO/order_ref bị đổi, số phục vụ tăng/giảm, từng phương án và factors.

Chỉ trả objective delta khi cấu hình utility weights/normalization giống nhau. Mean risk/time giữa các tập được phục vụ khác nhau không chứng minh cải thiện chất lượng. Giảm assignment có thể làm objective cost giảm, phải đọc unassigned_orders trước. Không có dữ liệu counterfactual để khẳng định thay kho đã tạo ra lợi ích thực.

## Nguồn triển khai kỹ thuật

Kiểm thử API theo TestClient và HTTP server riêng. Transaction read-only giữ nhất quán mỗi request, solver là mixed-integer optimizer chính thức của SciPy. [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), [Psycopg transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html), [SciPy milp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)
