"""Read-only review topic aggregation using the repository's shared cohort filters."""
from . import repository


def fetch_review_themes(connection, filters):
    cte, params = repository.cohort(filters)
    query = cte + """
    , feature_reviews AS (
        SELECT r.review_key, r.star_level, f.labels, f.severity, f.text_present
        FROM filtered_reviews r
        LEFT JOIN dw.review_theme_feature f USING (review_key)
    )
    SELECT
        count(*)::bigint AS total_reviews,
        count(*) FILTER (WHERE coalesce(text_present, false))::bigint AS text_present_reviews,
        count(*) FILTER (WHERE star_level <= 2)::bigint AS negative_reviews_le2,
        count(*) FILTER (
            WHERE coalesce(labels, '[]'::jsonb) = '[]'::jsonb
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
    return {
        **dict(row),
        "label_status": "UNVALIDATED_HEURISTIC_MENTION",
        "date_basis": "review_date, with order cohort filters inherited from repository.cohort",
        "content_returned": False,
        "warning": (
            "Một đánh giá có thể có nhiều nhãn; nhãn là tín hiệu từ khóa chưa được xác minh thủ công, "
            "không phải nguyên nhân hay khiếu nại đã xác nhận."
        ),
    }
