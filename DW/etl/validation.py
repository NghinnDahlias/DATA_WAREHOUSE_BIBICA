"""Executable gates raise on a nonzero violation count, rather than merely printing it."""
def _check(c,tests):
    checks={k:c.execute(s).fetchone()['n']==0 for k,s in tests.items()}
    if not all(checks.values()):raise RuntimeError('Reconciliation failed: '+','.join(k for k,v in checks.items() if not v))
    return checks

def validate(c):
    return _check(c,{
      'four_sources':"SELECT abs(count(*)-4) n FROM ops.source_current",
      'four_business_categories':"SELECT abs(count(*)-4) n FROM dw.dim_category",
      'accepted_line_count':"SELECT abs((SELECT count(*) FROM staging.order_line l WHERE NOT EXISTS(SELECT 1 FROM ops.quarantine q WHERE(q.source_code,q.row_no)=(l.source_code,l.row_no)))-(SELECT count(*) FROM dw.fact_order_line_candidate)) n",
      'accepted_review_count':"SELECT abs((SELECT count(*) FROM staging.review r WHERE NOT EXISTS(SELECT 1 FROM ops.quarantine q WHERE(q.source_code,q.row_no)=(r.source_code,r.row_no)))-(SELECT count(*) FROM dw.fact_review_candidate)) n",
      'review_sales_order':"SELECT count(*) n FROM dw.fact_review_candidate r LEFT JOIN dw.fact_order_lifecycle_candidate o USING(order_key) WHERE o.order_key IS NULL",
      'line_units':"SELECT count(*) n FROM dw.fact_order_line_candidate f JOIN staging.order_line l ON(l.source_code,l.row_no)=(f.source_code,f.physical_row_number) WHERE f.quantity IS DISTINCT FROM l.quantity OR f.gross_item_amount_source IS DISTINCT FROM l.gross OR f.seller_discount_source IS DISTINCT FROM l.seller_discount",
      'historical_category':"SELECT count(*) n FROM dw.fact_order_line_candidate f JOIN staging.order_line l ON(l.source_code,l.row_no)=(f.source_code,f.physical_row_number) LEFT JOIN dw.dim_category c ON c.category_key=f.category_key WHERE c.canonical_category IS DISTINCT FROM l.canonical_category",
      'order_money':"SELECT count(*) n FROM dw.fact_order_lifecycle_candidate f JOIN dw.dim_order_identity o USING(order_key) JOIN order_group g ON g.storefront_key=o.storefront_key AND g.order_id=o.native_order_id WHERE f.order_amount_source IS DISTINCT FROM g.amount OR f.order_row_count<>g.line_count",
      'warehouse_fk':"SELECT count(*) n FROM dw.fact_order_line_candidate WHERE warehouse_key IS NULL",
      'no_order_money_on_lines':"SELECT count(*) n FROM dw.fact_order_line_candidate WHERE order_amount_source IS NOT NULL OR shipping_buyer_charge_source IS NOT NULL",
    })

def olap_checks(c):
    return _check(c,{
      'olap_line_reconciliation':"SELECT abs((SELECT count(*) FROM dw.fact_order_line_candidate)-(SELECT coalesce(sum(source_line_count),0) FROM mart.mv_item_units_monthly)) n",
      'olap_order_reconciliation':"SELECT abs((SELECT count(*) FROM dw.fact_order_lifecycle_candidate)-(SELECT coalesce(sum(order_count),0) FROM mart.mv_order_counts_by_storefront)) n",
      'olap_review_reconciliation':"SELECT abs((SELECT count(*) FROM dw.fact_review_candidate)-(SELECT coalesce(sum(rating_count),0) FROM mart.mv_tiktok_ratings_monthly)) n",
      'olap_conflict_bucket':"SELECT abs((SELECT count(*) FROM dw.fact_order_lifecycle_candidate WHERE reconciliation_status IN ('CONFLICTING','REVIEW_REQUIRED'))-(SELECT coalesce(sum(review_required_order_count),0) FROM mart.mv_order_counts_by_storefront)) n",
      'olap_warehouse_lines':"SELECT abs((SELECT count(*) FROM dw.fact_order_line_candidate)-(SELECT coalesce(sum(accepted_lines),0) FROM mart.mv_warehouse_province)) n",
      'olap_category_lines':"SELECT abs((SELECT count(*) FROM dw.fact_order_line_candidate WHERE category_key IS NOT NULL)-(SELECT coalesce(sum(accepted_lines),0) FROM mart.mv_category_performance)) n",
    })
