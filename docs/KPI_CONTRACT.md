# KPI Contract v1 — 05/11/2026

Phiên bản máy đọc `2026-11-05-kpi-v1` ở `src/api/kpi_contract.py`, xuất qua `GET /api/v1/kpi-contract`. SQL thực thi ở `src/api/repository.py`. Định nghĩa đối chiếu với metric catalog bản tham chiếu, áp dụng trực tiếp trên Galaxy của repo này.

## Hạt dữ liệu và bộ lọc

`analytics.v_orders` một order_key, `analytics.v_items` một accepted source line, `analytics.v_reviews` một accepted review. Không trả native order ID hoặc thông tin người mua. SQL parameterized và read-only trong cùng snapshot REPEATABLE READ.

Ngày đầu/cuối bao gồm cả ngày, lọc theo ngày tạo đơn. `source`, `store`, `status` lọc orders. `category`, `product_key`, `warehouse_key`, `warehouse_region`, `province` ràng buộc trên cùng một dòng thông qua EXISTS khi tính KPI đơn. Các measures item chỉ dùng những dòng thỏa bộ lọc. Một đơn có nhiều category/kho có thể thuộc nhiều nhóm, không cộng distinct orders giữa nhóm.

Khi lọc một SKU, tiền hoàn thành/AOV vẫn là tiền của **toàn bộ đơn chứa SKU đó**, mỗi đơn chỉ tính một lần; không phải doanh thu được phân bổ riêng cho SKU. Số lượng bán chỉ cộng dòng của SKU đã lọc. Sản phẩm cùng tên nhưng khác native SKU hoặc cửa hàng giữ riêng; không gộp theo tên hay seller SKU. Danh sách tìm kiếm hiển thị shop, biến thể, mã SKU nguồn dạng chuỗi và số đơn trong kỳ, phân trang theo số đơn giảm dần rồi product_key.

Review được tính riêng trong cohort đơn, không join nhân với items. Nếu có end_date, chỉ lấy review_date đến hết ngày đó. Khi lọc thuộc tính dòng, review cần product link đã xác minh trong đúng đơn và đúng tập dòng đã lọc. ORDER_ONLY không được tự phân bổ cho SKU/kho. Bộ lọc này đo đánh giá của cohort ngày tạo đơn, không phải phân phối review theo ngày đăng độc lập.

## Công thức và coverage

| ID | Chỉ số | Công thức tại grain chính thức | Mẫu số / coverage |
|---|---|---|---|
| M01 | Đơn đặt | COUNT orders mọi trạng thái | UNKNOWN vẫn nằm trong mẫu số |
| M02 | Thanh toán đặt hàng quan sát | SUM order_payable | payable_observed_orders |
| M03 | Thanh toán đơn hoàn thành | SUM order_payable khi COMPLETED | completed_orders_with_payable |
| M04 | Giá trị hàng gốc | SUM gross_item_value | Accepted lines, khác tiền người mua trả |
| M05 | Hàng gốc hoàn thành | SUM gross khi order COMPLETED | Không coi DELIVERED là COMPLETED |
| M06 | Sản lượng hoàn thành | SUM quantity khi COMPLETED | Không tự trừ returned_quantity |
| M07 | AOV hoàn thành | M03 / completed_orders_with_payable | Không chia cho số dòng hay mọi đơn hoàn thành thiếu tiền |
| M08 | Tỷ lệ hủy | canceled_orders / M01 | Đơn tiền xung đột vẫn ở mẫu số |
| M09 | Hoàn tiền quan sát | SUM observed_refund ở order | refund_observed_orders, NULL khác0 |
| M10 | Tỷ lệ đơn ghi hoàn tiền | refund_positive_orders / refund_observed_orders | Không phải tỷ lệ trả hàng toàn hệ thống |
| M11 | Trợ giá người bán | SUM seller_discount ở item | seller_discount_observed_lines |
| M12 | Áp lực giảm giá | SUM discount / SUM gross trên cùng tập đủ cả2trường | discount_paired_lines, paired_discount, paired_gross |
| M13 | Ngày tạo đến ghi giao/hoàn thành | AVG delivered_at-created_at khi >=0 | delivery_observed_orders, chỉ trả mean khi một nguồn |
| M14 | Điểm sao | AVG star_level tại review | reviews |
| M15 | Review thấp | low_reviews / reviews | Stars1–2, không dùng denominator đơn |
| M16 | Độ phủ review TikTok quan sát | reviewed_tiktok_orders / tiktok_orders | Distinct order trong cùng cohort, review tự chọn |

SUM không có quan sát và phép chia mẫu số0 trả NULL. COUNT tập rỗng trả0. Tiền và decimal trả chuỗi JSON để giữ giá trị chính xác, tỷ lệ là fraction0–1, tiền VND. API có số đơn tiền xung đột, số dòng Unmapped và các mẫu số kèm theo.

Contract còn công bố M17growth và M18cross-platform discount ở unavailable_metrics cùng lý do. M17 thiếu bằng chứng coverage đầy đủ, M18 chưa có contract thống nhất đơn vị khoản trợ giá sàn. Hai chỉ số này không được tính bằng cách suy diễn từ snapshot.

`reconciliation_status=CONFLICTING` có thể do refund/status, không tự xóa một order_payable vẫn nhất quán. Không gán toàn bộ tài chính xung đột thành0. Refund TikTok có957order xung đột được giữ NULL. Shopee không có khoản hoàn tiền quan sát đáng tin để điền0.

## Trường nguồn và giới hạn

- Shopee cột lowercase `Tổng số tiền người mua thanh toán` là order payable đã đối soát. Cột uppercase là item payable. `Người bán trợ giá` đã là line total, không nhân quantity thêm lần nữa.
- TikTok Order Amount là order payable, SKU subtotals là line totals. Order Refund Amount nhất quán một giá trị/order mới được tổng hợp.
- Bốn category chuẩn từ cùng hàm tên sản phẩm, không dùng native TikTok category. KPI lịch sử dùng category FK của line. Product Type1 dùng cho catalog hiện hành.
- Shopee thời gian hoàn thành là proxy ghi nhận giao. TikTok Delivered Time là ghi nhận giao. M13 tổng nhiều nguồn trả NULL, endpoint operations/delivery tách từng nguồn và cung cấp cả shipped→recorded durations.
- Không đủ thông tin cho net revenue, quyết toán, margin, lợi nhuận, tồn kho thực, ROI quảng cáo hoặc causal uplift. Không xuất KPI thay thế có tên gây hiểu nhầm.

Kiểm chứng mới trong `reports/phase2_tests.json`, `reports/phase2_verification.json`. Đối soát đã chạy cả fixture multi-line, cùng-dòng category/kho, NULL/empty/date, status, review cutoff và fingerprints toàn bộ dữ liệu.

Kiểm toán bổ sung so68cohort/2108numeric measures với oracle độc lập trong reports/phase2_assessment/integrity.json. KPI envelope ghi rõ review_metricsUNAVAILABLE nếu chỉ lọc Shopee, dù count observed review records là0. Giá trị0đó không phải số khiếu nại0. Không có customer identity hoặc replacement lifecycle trong nguồn hợp đồng, meta công bố unavailable/null.


## Dashboard liên kết (10/11/2026)

/overview/dashboard sử dụng cùng cohort/order-line-review contract trong một REPEATABLE
READ snapshot có serialSQLguard. TopSKU sắp theo completed_units, trả completed_item_value
là tổng observed_item_payable của dòng hoàn thành; không phân bổ tiền toàn đơn cho SKU.
API products thêm sort=units/item_value theo allowlist; mặc định key giữ tương thích.

Insight chỉ là mô tả cohort hiện tại: tiền shop/tổng tiền, đơn hủy/số đơn (tối thiểu30mẫu),
sản lượng danh mục/tổng sản lượng đã lọc. Không có kỳ trước, tăng trưởng, dự báo, lời/lỗ
hoặc suy luận nguyên nhân. Danh mục NULL vẫn là trạng thái kiểm toán, không thêm business
category thứ5. Cột/nhãn trục tỷ lệ dùng phần trăm, thời gian dùng ngày, tiền dùng VND.

## Negative review case drilldown (15/11/2026)

`/customer/review-cases` and `/customer/review-cases/{case_key}` reuse the review cohort
above. Default stars_max=2; only 1/2/3 are accepted. Topic matches a current source-bound
keyword feature. Total is distinct accepted reviews, not topic mentions or order count.
List limit/offset are bounded; detail must match the same cohort, stars and topic, else404.
Only internal case key/date/star/product title/controlled labels and automatically redacted
opinion are returned. There are no native order/product/customer IDs or buyer attributes.
A missing or stale content projection is UNAVAILABLE_NOT_PREPARED; empty text is NO_TEXT,
never a fabricated opinion. Aggregate review-themes continues returning no review text.

The on-demand statistics dialog preserves null monetary/quantity denominators and shows
Shopee review metrics unavailable. Store order-money shares use disjoint shop groups;
category shares use completed units, never a sum/allocation of order money across categories.
