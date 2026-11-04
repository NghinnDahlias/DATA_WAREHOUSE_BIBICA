# Measure catalog và grain hiện hành

| Measure | Nguồn/grain | Quy tắc |
|---|---|---|
| Orders | Lifecycle, một scoped order | COUNT(*); count theo warehouse/category là DISTINCT order và không cộng giữa nhóm |
| Completed order payable | Lifecycle + canonical COMPLETED | SUM(order_amount_source), mỗi đơn một lần; không gọi net/settlement revenue |
| Completed units | Accepted lines của order COMPLETED | SUM(quantity); không lấy duplicate/quarantine hoặc canceled lines làm completed sales |
| List value | Accepted line | TikTok SKU subtotal before discount; Shopee original unit price×quantity; không phải payment |
| Observed item payable | Accepted line | TikTok SKU subtotal after discount; Shopee cột uppercase Tổng số tiền Người mua thanh toán; giữ0/dương của gift |
| Seller subsidy | Accepted line | Nguồn đã là tổng dòng, không nhân quantity; không suy causal impact |
| Refund | Lifecycle | Một giá trị nhất quán/order hoặc NULL khi thiếu/mâu thuẫn; không mặc định NULL=0 |
| Star mean / low ratio | Accepted review | AVG(star_level), COUNT(stars<=2)/COUNT(review); không nhân với sales rows |
| Kho→tỉnh | Accepted line + scoped warehouse + customer province | Units/observed item value theo đúng line; không phân bổ tiền đơn tùy ý |

Native TikTok Product Category chỉ metadata. Canonical categories: Quà tặng/Bánh/Kẹo/Ngũ cốc; NULL/Unmapped chỉ audit. Tên Type1 Product và historical line có thể cho counts khác nhau, không cộng distinct SKUs/orders giữa category.

Đơn có tiền mâu thuẫn vẫn là một order, amount NULL/CONFLICTING và có bucket điều tra. Không loại đơn khỏi denominator chỉ vì amount mâu thuẫn. Không suy profit, conversion, ad ROI, inventory hoặc cross-platform customer identity.

Safe order-level example:
```sql
SELECT s.storefront_code,COUNT(*) orders,
 SUM(f.order_amount_source) FILTER(WHERE st.reviewed_status='COMPLETED') completed_order_payable
FROM dw.fact_order_lifecycle_candidate f JOIN dw.dim_storefront s USING(storefront_key)
JOIN dw.dim_order_status st USING(order_status_key) GROUP BY 1;
```

Không SUM order_amount_source từ line fact; hai line columns order_amount_source/shipping_buyer_charge_source được để NULL có chủ đích.
