-- Local, redacted display projection only. Original workbook remains private/immutable.
CREATE TABLE IF NOT EXISTS dw.review_case_content (
    review_key bigint PRIMARY KEY REFERENCES dw.fact_review_candidate(review_key) ON DELETE CASCADE,
    source_sha256 text NOT NULL,
    source_row_hash text NOT NULL,
    content_version text NOT NULL,
    redacted_text text NOT NULL CHECK (length(redacted_text) <= 4000),
    prepared_at timestamptz NOT NULL DEFAULT now()
);
