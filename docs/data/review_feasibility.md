# Review intelligence feasibility

Review rows: 5,625. Negative (1–2 stars): 262 (0.046578). Nonempty review text: 4,470 (0.794667).

Order match: 5,625 rows (1.0). Exact normalized name proxy within matched order: 5,625 rows (1.0). This proxy is not a verified product-ID/SKU join.

Reviews linked to multi-product sales orders: 1,262; one review may describe the whole order. Exact review-to-line linkage remains unresolved. The ratings file is a pre-merged export, so a complete order match is not independent evidence that the original scraper linkage was correct.

Rating distribution, monthly volume, text lengths, encoding indicators and review key collisions are in `reports/review_profile.json`.

Candidate labels: packaging damage; product quality; missing/incorrect items; delivery; expectation mismatch; service; other. Accent-folded substring counts in the JSON are only exploratory and can overlap. Negation, slang, spelling variation and abbreviations require manual validation. No review text or customer identifier is published.

The starter keyword list left 4,407 of 4,470 nonempty reviews unclassified. This is a taxonomy feasibility signal, not a measured complaint prevalence.
