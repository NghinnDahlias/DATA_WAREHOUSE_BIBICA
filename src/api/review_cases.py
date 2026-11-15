"""Bounded review-grain drilldown, same cohort as KPIs; no native/buyer identifiers."""
from .repository import cohort
from .review_privacy import CONTENT_VERSION
from src.dss.review_audit import VERSION


def fetch_review_cases(c, filters, case_key=None):
    cte, params = cohort(filters)
    params.update(stars_max=filters.stars_max, topic=filters.topic,
                  audit_version=VERSION, content_version=CONTENT_VERSION,
                  limit=filters.limit, offset=filters.offset, case_key=case_key)
    cte += ''' , cases AS (
        SELECT r.review_key AS case_key,r.star_level,r.review_date,
          coalesce(raw.payload->>'product_name','Sản phẩm chưa liên kết') AS product_name,
          coalesce(f.labels,'[]'::jsonb) AS labels,
          CASE WHEN text.review_key IS NULL THEN 'UNAVAILABLE_NOT_PREPARED'
               WHEN text.redacted_text='' THEN 'NO_TEXT' ELSE 'READY' END AS content_status,
          text.redacted_text AS content
        FROM filtered_reviews r
        JOIN dw.fact_review_candidate base USING(review_key)
        JOIN dw.dim_source_file sf ON sf.source_file_key=base.source_file_key
        LEFT JOIN raw.source_row raw ON raw.source_code='ratings' AND raw.row_no=base.physical_row_number
        LEFT JOIN dw.review_theme_feature f ON f.review_key=r.review_key
          AND f.source_sha256=sf.source_sha256 AND f.audit_version=%(audit_version)s
        LEFT JOIN dw.review_case_content text ON text.review_key=r.review_key
          AND text.source_sha256=sf.source_sha256 AND text.source_row_hash=base.source_row_hash
          AND text.content_version=%(content_version)s
        WHERE r.star_level<=%(stars_max)s
          AND (%(topic)s::text IS NULL OR f.labels ? %(topic)s)
    ) '''
    if case_key is not None:
        return c.execute(cte+'SELECT * FROM cases WHERE case_key=%(case_key)s', params).fetchone()
    total = c.execute(cte+'SELECT count(*) total FROM cases', params).fetchone()['total']
    rows = c.execute(cte+'''SELECT case_key,star_level,review_date,product_name,labels,content_status,
        left(content,120) preview FROM cases ORDER BY review_date DESC NULLS LAST,case_key DESC
        LIMIT %(limit)s OFFSET %(offset)s''', params).fetchall()
    return {'total': total, 'rows': rows, 'limit': filters.limit, 'offset': filters.offset,
            'stars_max': filters.stars_max, 'topic': filters.topic,
            'definition': 'Số sao <= ngưỡng; nhãn từ khóa là đề cập chưa xác minh, không phải kết luận nguyên nhân.'}
