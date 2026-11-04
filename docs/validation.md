> HISTORICAL SNAPSHOT — Nội dung bên dưới là kết quả trước refinement04/11/2026. Trạng thái/schema/source hiện hành xem README.md và DW/07_documentation/implementation_status.md; evidence mới ở reports/etl_validation.json, processing_verification.json, reference_reconciliation.json. Các giả định tài chính cũ không thay measure_catalog hiện hành.

# Phase 1 validation

## Executed checks

| Check | Outcome |
|---|---|
| `python -m src.profiling.run` from project root | PASS, exit 0; profiled 4/4 raw exports |
| `python -m py_compile src/profiling/run.py src/profiling/documents.py src/profiling/config.py` | PASS |
| `python -m unittest discover -s tests -v` | PASS, 8/8 tests |
| Required Phase 1 subject/report files | PASS, 16/16 present |
| Source SHA-256 compared with `reports/source_inventory.json` | PASS, 4/4 unchanged |
| Expected date and numeric parse failures after `-` missing-value handling | 0 date; 0 numeric |
| Four sampled TikTok buyer PII values searched in generated docs/reports | 0 matches; this sample check is not a complete privacy audit |

The tests cover source discovery, CSV quoting and multiline text, XLSX streaming, duplicate and composite-key measurement, order-value repetition, Vietnamese date and numeric parsing, missing source handling, report presence, and deterministic profiling of a fixed fixture. The full source CLI completed successfully. A second byte-for-byte full-data rerun was not performed.

## Quality Gate 1: CONDITIONAL

All accessible sources were profiled, and the required Phase 1 artifacts were generated. The gate remains conditional because seller/platform discount and buyer payment semantics lack a validated accounting contract; Shopee's send/delivery time fields lack confirmed lifecycle meaning; repeated Shopee order-SKU lines need business explanation; and review-to-SKU linkage remains unverified. No production financial KPI or physical warehouse design is approved by these profiles.
