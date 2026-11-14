"""Read-only review topic aggregation using the repository's shared cohort filters."""
from . import repository
from src.dss.review_audit import VERSION


def fetch_review_themes(connection, filters):
    cte, params = repository.cohort(filters)
    params["audit_version"] = VERSION
    query = cte + """
    , feature_reviews AS (
        SELECT r.review_key, r.star_level, f.review_key AS feature_key, f.labels, f.severity, f.text_present
        FROM filtered_reviews r
        JOIN dw.fact_review_candidate base USING (review_key)
        JOIN dw.dim_source_file sf ON sf.source_file_key=base.source_file_key
        LEFT JOIN dw.review_theme_feature f ON f.review_key=r.review_key
          AND f.source_sha256=sf.source_sha256 AND f.audit_version=%(audit_version)s
    )
    SELECT
        count(*)::bigint AS total_reviews,
        count(feature_key)::bigint AS audited_reviews,
        count(*) FILTER (WHERE coalesce(text_present, false))::bigint AS text_present_reviews,
        count(*) FILTER (WHERE star_level <= 2)::bigint AS negative_reviews_le2,
        count(*) FILTER (
            WHERE feature_key IS NOT NULL AND labels = '[]'::jsonb
        )::bigint AS reviews_without_explicit_issue_label,
        count(*) FILTER (
            WHERE severity = 'SAFETY_SIGNAL_REQUIRES_REVIEW'
        )::bigint AS safety_signal_reviews,
        coalesce((
            SELECT jsonb_agg(jsonb_build_object(
                'label', x.label,
                'mentions', x.mentions,
                'negative_mentions', x.negative_mentions
            ) ORDER BY x.mentions DESC, x.label)
            FROM (
                SELECT
                    label,
                    count(*)::bigint AS mentions,
                    count(*) FILTER (WHERE star_level <= 2)::bigint AS negative_mentions
                FROM feature_reviews fr
                CROSS JOIN LATERAL jsonb_array_elements_text(
                    coalesce(fr.labels, '[]'::jsonb)
                ) AS label
                GROUP BY label
            ) x
        ), '[]'::jsonb) AS labels
    FROM feature_reviews
    """
    row = connection.execute(query, params).fetchone()
    shopee_only = filters.channel == 'SHOPEE' or filters.source in ('shopee_bibica','shopee_quasure') or filters.store in ('bibica_official_store','quasure_specialized_store')
    availability = ('UNAVAILABLE_NO_SHOPEE_RATING_SOURCE' if shopee_only else
                    'NO_OBSERVED_REVIEWS' if not row['total_reviews'] else
                    'READY' if row['audited_reviews'] == row['total_reviews'] else 'UNAVAILABLE_INCOMPLETE_FEATURES')
    if availability != 'READY':
        for field in ('text_present_reviews', 'reviews_without_explicit_issue_label', 'safety_signal_reviews'):
            row[field] = None
        row['labels'] = []
    return {
        "availability": availability,
        "audit_version": VERSION,
        **dict(row),
        "label_status": "UNVALIDATED_HEURISTIC_MENTION",
        "date_basis": "Order creation cohort with review_date <= end_date when supplied; start_date is not a review-date lower bound",
        "content_returned": False,
        "warning": (
            "Một đánh giá có thể có nhiều nhãn; nhãn là tín hiệu từ khóa chưa được xác minh thủ công, "
            "không phải nguyên nhân hay khiếu nại đã xác nhận."
        ),
    }
