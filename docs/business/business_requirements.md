# Business requirements

Questions use observed columns only. Monetary sales KPIs remain provisional until financial semantics are resolved.

| Objective/question | Sources | Required fields | KPI | Grain | Limitation | DSS relevance |
|---|---|---|---|---|---|---|
| How do order counts and item units trend by month/channel/storefront? | sales exports | order, created, quantity, status, storefront | distinct orders; sum units by status | month × channel × storefront | Status harmonization; source coverage differs | Baseline and scenario demand |
| Which SKUs contribute most item volume by store? | sales exports | SKU, quantity, created, storefront | units by SKU | month × storefront × source SKU | SKU namespaces differ; canceled rows | Product prioritization |
| How do cancellation rates vary by channel and store? | sales exports | order, status, created, storefront | canceled orders / eligible orders | month × storefront | Lifecycle map and eligible denominator unresolved | Fulfillment intervention |
| Where are fulfillment delays concentrated? | sales exports | created, shipped, delivered, warehouse, province | median created→shipped and shipped→delivered duration | month × store × warehouse × province | Shopee date semantics; sparse timestamps | What-if service target |
| How often are refunds/returns observed? | TikTok sales; Shopee sales | refund, returned quantity, return status, order | return/refund incidence | month × store | Cash refund comparable only for TikTok | Risk score |
| What is the distribution of seller/platform discount signals? | sales exports | discount fields, quantity, order | discount field totals by native source | month × store | Financial scope and allocation unresolved | Promotion sensitivity |
| How do ratings and negative review rates change over time? | TikTok ratings | star_level, review_date, order_id | ratings count; 1–2 star rate | month × TikTok shop | Selection bias; review timestamp | Quality prioritization |
| Which complaint themes merit manual investigation? | TikTok ratings | review_text, star_level, order_id | keyword candidate counts, with manual precision review | month × candidate theme | No validated classifier; text coverage/negation | Explainable issue score |

These eight questions support the CO4031 requirement for a data warehouse centered on a real decision problem. DSS candidates are explainable scoring and what-if inputs, not implemented in Phase 1.
