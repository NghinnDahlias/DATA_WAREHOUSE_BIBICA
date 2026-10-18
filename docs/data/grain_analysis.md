# Grain and key analysis

Counts are from every nonempty data row. A physical row locator remains the safe provisional source key; no order-SKU uniqueness is assumed.

| Source | Rows | Orders | SKUs | Order-SKU | Repeated order-SKU groups | Full duplicates | Multi-SKU orders |
|---|---:|---:|---:|---:|---:|---:|---:|
| tiktok_sales | 77,311 | 63,744 | 731 | 77,311 | 0 | 0 | 8,895 |
| tiktok_reviews | 5,625 | 4,661 | 0 | 0 | 0 | 0 | 0 |
| shopee_bibica | 86,796 | 54,015 | 643 | 85,814 | 323 | 315 | 17,850 |
| shopee_quasure | 14,725 | 9,829 | 75 | 14,639 | 4 | 0 | 3,049 |

shopee_bibica also has 458 rows without a SKU identifier; these are excluded from order-SKU combination counts.
shopee_quasure also has 82 rows without a SKU identifier; these are excluded from order-SKU combination counts.

## Candidate grain

Sales exports appear to contain product/variant lines, with package and order context. Repeated order-SKU pairs must be retained until their cause (split packages, repeated line, or export duplication) is resolved. Ratings are review records, not sales lines. No stable review ID exists in this export; the composite fingerprint is only a collision diagnostic.

Order ID intersections and package/tracking multiplicity are in `reports/key_uniqueness.json`; review candidate collisions are in `reports/review_profile.json`. Storefront plus order ID is the minimum order namespace.

Review candidate fingerprint collisions: 256 additional rows share `(order_id, product_id, review_date, review_text, other_text)`; they are not automatically duplicate customer opinions.

| Source | Repeated order-package-SKU rows | Repeated order-tracking-SKU rows | Orders with multiple packages | Orders with multiple tracking IDs |
|---|---:|---:|---:|---:|
| tiktok_sales | 0 | 0 | 0 | 0 |
| tiktok_reviews | 0 | 0 | 0 | 0 |
| shopee_bibica | 462 | 462 | 0 | 0 |
| shopee_quasure | 2 | 2 | 0 | 0 |
