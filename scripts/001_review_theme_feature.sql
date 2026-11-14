-- Compatibility entry point. Run scripts/migrate_api.py to apply the canonical schema.
-- Only controlled review labels; no raw text.
CREATE TABLE IF NOT EXISTS dw.review_theme_feature (
    review_key       bigint PRIMARY KEY
        REFERENCES dw.fact_review_candidate(review_key) ON DELETE CASCADE,
    labels           jsonb NOT NULL DEFAULT '[]'::jsonb,
    severity         text NOT NULL,
    text_present     boolean NOT NULL,
    audit_version    text NOT NULL,
    audited_at       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_review_theme_labels_array
        CHECK (jsonb_typeof(labels) = 'array'),
    CONSTRAINT ck_review_theme_severity
        CHECK (severity IN (
            'UNKNOWN',
            'SAFETY_SIGNAL_REQUIRES_REVIEW',
            'FULFILLMENT_DAMAGE_SIGNAL',
            'OTHER_EXPLICIT_MENTION'
        ))
);
CREATE INDEX IF NOT EXISTS ix_review_theme_feature_audit_version
    ON dw.review_theme_feature(audit_version);

-- Bind feature rows to the immutable ratings snapshot, avoiding stale labels after ETL.
ALTER TABLE dw.review_theme_feature ADD COLUMN IF NOT EXISTS source_sha256 text;
