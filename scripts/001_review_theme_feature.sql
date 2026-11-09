-- Stores only review-level audit labels and flags. Never stores review text or buyer data.
CREATE TABLE IF NOT EXISTS dw.review_theme_feature (
    review_key BIGINT PRIMARY KEY REFERENCES dw.fact_review_candidate(review_key) ON DELETE CASCADE,
    labels JSONB NOT NULL DEFAULT '[]'::jsonb,
    severity TEXT NOT NULL,
    text_present BOOLEAN NOT NULL,
    audit_version TEXT NOT NULL,
    audited_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT review_theme_labels_array CHECK (jsonb_typeof(labels) = 'array'),
    CONSTRAINT ck_review_theme_severity CHECK (
        severity IN (
            'UNKNOWN',
            'SAFETY_SIGNAL_REQUIRES_REVIEW',
            'FULFILLMENT_DAMAGE_SIGNAL',
            'OTHER_EXPLICIT_MENTION'
        )
    )
);

CREATE INDEX IF NOT EXISTS ix_review_theme_feature_audit_version
    ON dw.review_theme_feature(audit_version);