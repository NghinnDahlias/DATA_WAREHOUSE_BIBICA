> HISTORICAL SNAPSHOT — Nội dung bên dưới là kết quả trước refinement04/11/2026. Trạng thái/schema/source hiện hành xem README.md và DW/07_documentation/implementation_status.md; evidence mới ở reports/etl_validation.json, processing_verification.json, reference_reconciliation.json. Các giả định tài chính cũ không thay measure_catalog hiện hành.

# Financial definitions and reconciliation

Source monetary labels are not a signed accounting contract. Keep the source field and its grain explicit. `reports/financial_reconciliation.json` contains row sums, one-value-per-order sums and repeated/conflicting order counts.

| Source | Order amount raw row sum | Single-value order sum | Multirow orders repeating value | Conflicting multirow orders |
|---|---:|---:|---:|---:|
| tiktok_sales | 7959922115.0 | 5452176957.0 | 8895 | 0 |
| shopee_bibica | 12542350807.0 | 5925938361.0 | 18217 | 0 |
| shopee_quasure | 2257511602.0 | 1216846995.0 | 3070 | 0 |

## KPI status

- Order count: PARTIALLY VERIFIED. Count distinct `(storefront, order_id)`; lifecycle inclusion policy unresolved.
- Gross item value: PARTIALLY VERIFIED for TikTok only; source row has explicit SKU subtotal before discount. Shopee `Giá gốc` and `Giá ưu đãi` require quantity and discount interpretation.
- Paid revenue/net sales: UNRESOLVED. Buyer payment, order amount, discounts, shipping and refunds may have different scopes. No cross-platform sum is authorized yet.
- Refund value: UNRESOLVED. TikTok has `Order Refund Amount`; Shopee export has return quantity/status and return shipping fee, but no verified cash refund amount.
- Discounts: PARTIALLY VERIFIED as separate source components; seller/platform and per-item/per-order allocation need confirmation.

Do not sum repeated order-level amounts at line grain. Confirm representative platform settlement examples with business owner before production KPIs.

TikTok item equation `gross - seller discount - platform discount = net item` was testable on 77,311 rows; 0 differed by more than 1 currency unit.

shopee_bibica: the two buyer-payment columns differed on 80,747 of 86,796 comparable rows. The first column also varies within many multirow orders while the second is constant; their allocation and settlement meanings require confirmation.

shopee_quasure: the two buyer-payment columns differed on 13,829 of 14,725 comparable rows. The first column also varies within many multirow orders while the second is constant; their allocation and settlement meanings require confirmation.
