"""Offline, read-only review assessment using controlled labels and SQL aggregates.

Private review text is streamed only into a deterministic local mention tagger.
Reports contain no buyer labels, source order IDs, review text or private row samples.
"""
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from DW.etl.common import SOURCES, checksum, money, rows
from DW.etl.ratings import project_scraped_rating
from src.api.db import snapshot
from src.dss.review_audit import VERSION, classify_review, operational_service_metrics, order_cluster_interval, rating_summary
from src.dss.scoring import wilson_interval


BASE = '''WITH features AS (
  SELECT * FROM jsonb_to_recordset(%(features)s::jsonb)
    AS f(row_no integer,labels jsonb,severity text,text_present boolean)
), product_attributes AS (
  SELECT order_key,product_key,
    CASE WHEN count(DISTINCT canonical_category)=1 AND bool_and(canonical_category IS NOT NULL)
      THEN min(canonical_category) ELSE 'Unmapped_or_ambiguous' END category,
    CASE WHEN count(DISTINCT warehouse_key)=1 THEN min(warehouse_region) ELSE 'Ambiguous' END warehouse,
    count(DISTINCT warehouse_key) warehouse_count
  FROM analytics.v_items GROUP BY order_key,product_key
), order_attributes AS (
  SELECT order_key,
    CASE WHEN count(DISTINCT warehouse_key)=1 THEN min(warehouse_region) ELSE 'Ambiguous' END warehouse,
    CASE WHEN count(DISTINCT customer_province)=1 THEN min(customer_province) ELSE 'Ambiguous' END province,
    count(DISTINCT warehouse_key) warehouse_count
  FROM analytics.v_items GROUP BY order_key
), review_base AS (
  SELECT r.review_key,r.order_key,r.product_key,r.star_level,r.review_date,r.product_linkage_status,
    o.storefront_code,o.source_code,o.channel_code,o.order_date,
    CASE WHEN o.shipped_at>=o.created_at AND o.delivered_at>=o.shipped_at THEN
      CASE WHEN o.delivered_at-o.shipped_at<=interval '2 days' THEN '0_to_2_days'
           WHEN o.delivered_at-o.shipped_at<=interval '5 days' THEN 'over2_to5_days' ELSE 'over5_days' END
      ELSE 'Unknown' END duration_bucket,
    coalesce(pa.category,'Unlinked') category,
    CASE WHEN pa.warehouse_count=1 THEN pa.warehouse ELSE oa.warehouse END warehouse,
    oa.province,
    CASE WHEN pa.warehouse_count=1 THEN 'MATCHED_PRODUCT_UNIQUE_WAREHOUSE'
         WHEN oa.warehouse_count=1 THEN 'UNIQUE_ORDER_WAREHOUSE' ELSE 'AMBIGUOUS_WAREHOUSE' END warehouse_attribution,
    f.labels,f.severity,f.text_present
  FROM analytics.v_reviews r JOIN dw.fact_review_candidate raw_review USING(review_key)
  JOIN analytics.v_orders o ON o.order_key=r.order_key
  LEFT JOIN product_attributes pa ON pa.order_key=r.order_key AND pa.product_key=r.product_key
  LEFT JOIN order_attributes oa ON oa.order_key=r.order_key
  JOIN features f ON f.row_no=raw_review.physical_row_number
) '''


def write_report(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf8')


def main():
    target = root/'reports/phase2_assessment'
    write_report(target/'reviews.json',{'status':'RUNNING','started_at':datetime.now(timezone.utc).isoformat()})
    features = []
    source = root/'Data/Data_Source_Raw'/SOURCES['ratings'][0]
    before_sha = checksum(source)
    with snapshot() as connection:
        source_metadata = connection.execute("SELECT sha256,row_count FROM ops.source_current WHERE source_code='ratings'").fetchone()
        accepted_rows = {r['physical_row_number']:r for r in connection.execute('SELECT physical_row_number,star_level FROM dw.fact_review_candidate')}
    assert before_sha == source_metadata['sha256'], 'Rating workbook differs from loaded source'
    source_count = 0
    projected_stars_match = True
    for locator, row in rows(source):
        source_count += 1
        if locator not in accepted_rows:
            continue
        projected = project_scraped_rating(row)
        projected_stars_match &= money(projected['star_level']) == accepted_rows[locator]['star_level']
        features.append({'row_no':locator,**{k:v for k,v in classify_review(projected['review_text']).items()
                                        if k in ['labels','severity','text_present']}})
    encoded = json.dumps(features,ensure_ascii=False,sort_keys=True)
    params = {'features':encoded}
    checks = {
        'native_rating_hash_matches_loaded_source':before_sha == source_metadata['sha256'],
        'native_rating_source_count_matches':source_count == source_metadata['row_count'],
        'every_accepted_review_tagged_once':len(features) == len(accepted_rows) and len({r['row_no'] for r in features})==len(features),
        'accepted_stars_match_native_projection':bool(projected_stars_match),
    }
    with snapshot() as connection:
        star_rows = connection.execute('SELECT star_level,count(*) n FROM analytics.v_reviews GROUP BY star_level ORDER BY star_level').fetchall()
        star_counts = {r['star_level']:r['n'] for r in star_rows}
        total = sum(star_counts.values())
        thresholds = [rating_summary(star_counts,t) for t in [1,2,3]]
        for threshold in thresholds:
            clusters = connection.execute('''SELECT count(*) n,count(*) FILTER(WHERE star_level<=%s) bad
                FROM analytics.v_reviews GROUP BY order_key''',(threshold['threshold'],)).fetchall()
            threshold['order_cluster_bootstrap_95_interval'] = order_cluster_interval([(r['n'],r['bad']) for r in clusters])
        source_coverage = connection.execute('''WITH review_cohort AS (
          SELECT o.source_code,count(*) reviews,count(DISTINCT r.order_key) reviewed_orders
          FROM analytics.v_reviews r JOIN analytics.v_orders o USING(order_key) GROUP BY o.source_code
        ) SELECT o.source_code,max(o.channel_code) platform,max(o.storefront_code) store,count(*) orders,
          CASE WHEN o.source_code='tiktok_bibica' THEN coalesce(max(r.reviews),0) END reviews,
          CASE WHEN o.source_code='tiktok_bibica' THEN coalesce(max(r.reviewed_orders),0) END reviewed_orders,
          CASE WHEN o.source_code='tiktok_bibica' THEN max(r.reviewed_orders)::numeric/count(*) END observed_review_order_coverage,
          CASE WHEN o.source_code='tiktok_bibica' THEN 'AVAILABLE_SELF_SELECTED_SAMPLE' ELSE 'UNAVAILABLE_NO_REVIEW_EXPORT' END review_status
          FROM analytics.v_orders o LEFT JOIN review_cohort r USING(source_code) GROUP BY o.source_code ORDER BY o.source_code''').fetchall()
        multiplicity = connection.execute('''SELECT n reviews_per_order,count(*) reviewed_orders FROM(
            SELECT order_key,count(*) n FROM analytics.v_reviews GROUP BY order_key)x GROUP BY n ORDER BY n''').fetchall()
        join_audit = connection.execute('''SELECT (SELECT count(*) FROM analytics.v_reviews) accepted_reviews,
          (SELECT count(*) FROM analytics.v_reviews r JOIN analytics.v_orders o USING(order_key)) reviews_order_join,
          (SELECT count(*) FROM analytics.v_reviews r JOIN analytics.v_items i ON i.order_key=r.order_key) naive_order_item_join_rows,
          (SELECT count(*) FROM analytics.v_reviews WHERE product_key IS NULL) unlinked_product_reviews,
          (SELECT count(*) FROM analytics.v_reviews r LEFT JOIN analytics.v_orders o USING(order_key) WHERE o.order_key IS NULL) orphan_order_reviews''').fetchone()
        feature_summary = connection.execute(BASE+'''SELECT count(*) reviews,count(*) FILTER(WHERE text_present) text_present_reviews,
          count(*) FILTER(WHERE jsonb_array_length(labels)=0) unknown_or_no_explicit_issue_reviews,
          count(*) FILTER(WHERE jsonb_array_length(labels)>1) multilabel_reviews,
          count(*) FILTER(WHERE severity='SAFETY_SIGNAL_REQUIRES_REVIEW') safety_signal_reviews,
          count(*) FILTER(WHERE severity='SAFETY_SIGNAL_REQUIRES_REVIEW' AND star_level>=4) high_star_safety_signal_reviews,
          count(*) FILTER(WHERE star_level<=2 AND jsonb_array_length(labels)=0) negative_without_explicit_issue_label,
          count(*) FILTER(WHERE star_level<=2 AND NOT text_present) negative_without_text,
          count(*) FILTER(WHERE province IN('Unknown','Ambiguous')) unknown_or_ambiguous_province,
          count(*) FILTER(WHERE warehouse_attribution='AMBIGUOUS_WAREHOUSE') ambiguous_warehouse
          FROM review_base''',params).fetchone()
        labels = connection.execute(BASE+'''SELECT label,count(*) mentions,count(*) FILTER(WHERE star_level<=2) negative_le2_mentions,
          count(*) FILTER(WHERE star_level>=4) high_star_mentions
          FROM review_base CROSS JOIN LATERAL jsonb_array_elements_text(labels) label GROUP BY label ORDER BY label''',params).fetchall()
        severities = connection.execute(BASE+'''SELECT severity,count(*) reviews,
          count(*) FILTER(WHERE star_level=1) star1,count(*) FILTER(WHERE star_level=2) star2,
          count(*) FILTER(WHERE star_level=3) star3,count(*) FILTER(WHERE star_level=4) star4,
          count(*) FILTER(WHERE star_level=5) star5 FROM review_base GROUP BY severity ORDER BY severity''',params).fetchall()
        dimensions = connection.execute(BASE+'''SELECT axis,group_value,count(*) reviews,
          count(DISTINCT order_key) reviewed_orders,count(*) FILTER(WHERE star_level=1) star1,
          count(*) FILTER(WHERE star_level<=2) negative_le2,count(*) FILTER(WHERE star_level<=3) negative_le3,
          avg(star_level) mean_stars,
          count(*) FILTER(WHERE severity='SAFETY_SIGNAL_REQUIRES_REVIEW') safety_signal_reviews,
          count(*) FILTER(WHERE jsonb_array_length(labels)=0) unknown_or_no_explicit_issue_reviews
          FROM review_base CROSS JOIN LATERAL (VALUES
            ('source',source_code),('store',storefront_code),('platform',channel_code),
            ('review_month',to_char(review_date,'YYYY-MM')),('order_month',to_char(order_date,'YYYY-MM')),
            ('category',category),('product',coalesce(product_key::text,'Unlinked')),
            ('warehouse',warehouse),('province',province),
            ('warehouse_province',jsonb_build_array(warehouse,province)::text),
            ('category_warehouse',jsonb_build_array(category,warehouse)::text),
            ('product_warehouse',jsonb_build_array(coalesce(product_key::text,'Unlinked'),warehouse)::text),
            ('category_province',jsonb_build_array(category,province)::text),
            ('category_warehouse_province',jsonb_build_array(category,warehouse,province)::text),
            ('delivery_duration',duration_bucket),
            ('warehouse_duration',jsonb_build_array(warehouse,duration_bucket)::text),
            ('category_duration',jsonb_build_array(category,duration_bucket)::text)
          ) dimensions(axis,group_value) GROUP BY axis,group_value ORDER BY axis,group_value''',params).fetchall()
        for group in dimensions:
            group['negative_review_rate_le2'] = group['negative_le2']/group['reviews']
            group['wilson_95_interval_le2'] = wilson_interval(group['negative_le2'],group['reviews'])
            group['sparse_cohort'] = group['reviews']<30
        axis_counts = Counter()
        for group in dimensions:
            axis_counts[group['axis']] += group['reviews']
        checks['one_review_per_dimension_grouping'] = bool(axis_counts) and all(n==total for n in axis_counts.values())
        checks['no_order_join_fanout'] = join_audit['accepted_reviews']==join_audit['reviews_order_join']==feature_summary['reviews']
        checks['no_orphan_review_orders'] = join_audit['orphan_order_reviews']==0
        checks['threshold_counts_nested'] = [r['negative_reviews'] for r in thresholds] == sorted(r['negative_reviews'] for r in thresholds)
        checks['source_review_absence_is_unavailable'] = all(r['reviews'] is None for r in source_coverage if r['source_code']!='tiktok_bibica')
        checks['negative_denominator_is_reviews'] = thresholds[1]['reviews']==total
        shop_mapping = connection.execute('''SELECT s.storefront_code,c.channel_code,count(*) catalog_skus,
          count(*) FILTER(WHERE lower(p.product_name) LIKE '%%quasure%%') quasure_named_skus,
          count(*) FILTER(WHERE lower(p.product_name) LIKE '%%pleasure%%') pleasure_named_skus
          FROM dw.dim_source_product_sku p JOIN dw.dim_storefront s USING(storefront_key)
          JOIN dw.dim_channel c ON c.channel_key=p.channel_key GROUP BY s.storefront_code,c.channel_code ORDER BY s.storefront_code''').fetchall()
        breakfast = connection.execute('''SELECT o.source_code,i.warehouse_region,count(*) accepted_lines,
          count(DISTINCT i.order_key) orders,count(DISTINCT i.product_key) historical_skus,sum(i.quantity) units
          FROM analytics.v_items i JOIN analytics.v_orders o USING(order_key)
          JOIN dw.fact_order_line_candidate fact ON fact.order_line_key=i.order_line_key
          JOIN staging.order_line line ON line.source_code=fact.source_code AND line.row_no=fact.physical_row_number
          WHERE i.canonical_category='Bánh' AND (lower(line.product_name) LIKE '%%ăn sáng%%' OR lower(line.product_name) LIKE '%%bữa sáng%%'
            OR lower(line.product_name) LIKE '%%breakfast%%')
          GROUP BY o.source_code,i.warehouse_region ORDER BY o.source_code,i.warehouse_region''').fetchall()
        date_checks = connection.execute('''SELECT count(*) FILTER(WHERE r.review_date<o.order_date) reviews_before_order,
          min(r.review_date) earliest_review,max(r.review_date) latest_review,
          min(o.order_date) earliest_reviewed_order,max(o.order_date) latest_reviewed_order
          FROM analytics.v_reviews r JOIN analytics.v_orders o USING(order_key)''').fetchone()
    checks['source_bytes_unchanged_after_read'] = checksum(source)==before_sha
    result = {
        'status':'PASS' if all(checks.values()) else 'FAIL','executed_at':datetime.now(timezone.utc).isoformat(),
        'audit_version':VERSION,'checks':checks,'threshold_sensitivity':thresholds,'star_counts':star_counts,
        'source_coverage':source_coverage,'order_review_multiplicity':multiplicity,'join_audit':join_audit,
        'content_summary':feature_summary,'content_labels':labels,'severity_by_stars':severities,
        'dimension_group_totals':dict(axis_counts),'shop_catalog_mapping':shop_mapping,
        'explicit_breakfast_name_observations':breakfast,'review_date_coherence':date_checks,
        'operational_service_metrics':operational_service_metrics(),
        'label_quality':{'status':'UNVALIDATED_HEURISTIC','module_regression_tests':19,
           'real_data_precision_recall':'UNAVAILABLE_NO_INDEPENDENT_HUMAN_LABELS',
           'method':'Conservative exact mentions, Unicode normalization, local negation suppression, multi-label, unknown retained',
           'seller_reply_history':'Not parsed as operational events. Only customer review_text projection is tagged.',
           'source_text_persisted_in_report':False},
        'customer_dimension':{'status':'UNAVAILABLE','reason':'No verified privacy-preserving stable customer key or cross-source identity contract. Raw buyer labels are not resolved identities.'},
        'causal_conclusion':'No causal attribution of defects to warehouse, carrier or distance. Ratings and durations are observational/self-selected.',
        'uncertainty_method':{'wilson':'Approximate review-level IID interval, not population satisfaction certainty.',
            'bootstrap':'2000 deterministic order-cluster resamples, seed20261105, retaining review multiplicity within order.',
            'remaining_limitations':'Self-selection, temporal dependence, unknown export completeness and unvalidated cause labels remain.'},
        'replacement_conclusion':'Mention/dispatch/receipt/resolution claims are separate text signals. None confirms typed operational completion.',
        'geography_conclusion':'Warehouse association uses unique matched-product warehouse or unique order warehouse. Ambiguity stays explicit. Province is independently normalized.',
        'shop_naming_conclusion':'Current source storefront is Quasure. Pleasure naming in business background is not silently substituted without an approved alias/mapping.',
        'content_feature_digest':hashlib.sha256(encoded.encode('utf8')).hexdigest(),
        'native_rating_sha256':before_sha,
    }
    write_report(target/'reviews_dimensions.json',{'executed_at':result['executed_at'],'groups':dimensions,
         'note':'Each axis partitions review grain once. Do not add counts across axes. Negative fraction uses reviews, not all orders.'})
    write_report(target/'reviews.json',result)
    print(json.dumps({'status':result['status'],'checks':checks,'threshold_sensitivity':thresholds,
         'content_summary':feature_summary,'content_labels':labels,'shop_catalog_mapping':shop_mapping,
         'source_coverage':source_coverage,'explicit_breakfast_name_observations':breakfast},ensure_ascii=False,default=str))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        write_report(root/'reports/phase2_assessment/reviews.json',{'status':'FAIL','error_code':type(error).__name__})
        raise
