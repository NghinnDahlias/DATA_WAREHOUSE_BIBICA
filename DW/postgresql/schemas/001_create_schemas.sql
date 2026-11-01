BEGIN;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS mart;

COMMENT ON SCHEMA raw IS 'Immutable source capture layer. Raw exports remain unchanged.';
COMMENT ON SCHEMA staging IS 'Typed source rows, lineage, mapping and quality flags.';
COMMENT ON SCHEMA dw IS 'Kimball constellation candidate: shared dimensions and candidate facts.';
COMMENT ON SCHEMA mart IS 'Approved OLAP views/materialized views only.';

COMMIT;
