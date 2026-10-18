"""Additional Phase 1 contracts and decision documents from measured aggregates."""
import csv

from .config import FIELDS


MAPPINGS = [
    ("order_identifier","order","order","DIRECT","Storefront must namespace Shopee order IDs; check cross-source collisions."),
    ("product_identifier",None,"product_sku","AMBIGUOUS","TikTok SKU ID is a variant ID; Shopee product SKU is seller-supplied."),
    ("sku_identifier","sku","sku","AMBIGUOUS","Platform SKU ID and seller variant SKU are different key systems."),
    ("quantity","quantity","quantity","DIRECT","Both represent unit count on source row, subject to return/cancel state."),
    ("unit_price","unit_price","unit_price","AMBIGUOUS","Shopee original price may be unit-level; validate invoice examples."),
    ("gross_item_amount","gross",None,"DERIVED","TikTok explicit subtotal; Shopee candidate original price times quantity requires validation."),
    ("seller_discount","seller_discount","seller_discount","AMBIGUOUS","Shopee seller subsidy and TikTok SKU discount need scope comparison."),
    ("platform_discount","platform_discount","platform_discount","AMBIGUOUS","Subsidy and discount labels may have different settlement scope."),
    ("net_item_amount","net_item","net_item","AMBIGUOUS","TikTok subtotal vs Shopee promotional unit price; do not equate."),
    ("buyer_payment","order_amount","payment","AMBIGUOUS","Order amount and buyer payment need reconciliation with shipping and refunds."),
    ("shipping_buyer_charge","shipping","shipping","AMBIGUOUS","TikTok after-discount fee vs Shopee buyer-paid fee."),
    ("refund_amount","refund",None,"UNAVAILABLE","Shopee has return status/quantity and return shipping fee, not verified cash refund."),
    ("order_status","status","status","TRANSFORM","Map native lifecycles after business review."),
    ("order_date","created","created","DIRECT","Timestamp parsing/timezone must be fixed in contract."),
    ("payment_date","paid","paid","DIRECT","Availability differs by status."),
    ("shipping_date","shipped","shipped","AMBIGUOUS","Shopee send date vs TikTok shipped time."),
    ("delivery_date","delivered","delivered","AMBIGUOUS","Shopee delivery time semantics need confirmation."),
    ("storefront",None,None,"DERIVED","Derive from source file identity; keep two Shopee stores distinct."),
    ("sales_channel",None,None,"DERIVED","Derive TikTok or Shopee from source file identity."),
    ("warehouse","warehouse","warehouse","AMBIGUOUS","Free-text location names require controlled mapping."),
    ("destination_province","province","province","TRANSFORM","Normalize geography spelling; exclude detailed address."),
]


def write_additional(docs, out, results, missing):
    source = {k:v[0] for k,v in results.items()}
    keys = {k:v[1] for k,v in results.items()}
    quality = {k:v[2] for k,v in results.items()}
    with (out/"schema_mapping.csv").open("w",encoding="utf-8-sig",newline="") as handle:
        writer=csv.writer(handle)
        writer.writerow(["business_concept","tiktok_field","shopee_field","classification","evidence_or_condition"])
        for concept,t,s,classification,note in MAPPINGS:
            writer.writerow([concept,FIELDS["tiktok"].get(t,"") if t else "",
                             FIELDS["shopee"].get(s,"") if s else "",classification,note])
    lines=["# Cross-platform schema mapping", "", "The full machine-readable mapping is `reports/schema_mapping.csv`. Classifications describe semantic compatibility, not only matching names.", "", "| Concept | TikTok | Shopee | Class |", "|---|---|---|---|"]
    for concept,t,s,classification,_ in MAPPINGS:
        lines.append(f"| {concept} | {FIELDS['tiktok'].get(t,'—') if t else '—'} | {FIELDS['shopee'].get(s,'—') if s else '—'} | {classification} |")
    lines += ["", "DIRECT means a defensible same-level concept, not proven accounting equivalence. AMBIGUOUS fields remain source-specific in the Phase 2 contract. Source identity supplies channel and storefront. Preserve Bibica Official Store and Quasure specialized store as distinct storefront members; Quasure is a product line, not automatically a separate company.", ""]
    (docs/"data/cross_platform_mapping.md").write_text("\n".join(lines),encoding="utf-8")

    questions=[
        ("How do order counts and item units trend by month/channel/storefront?","sales exports","order, created, quantity, status, storefront","distinct orders; sum units by status","month × channel × storefront","Status harmonization; source coverage differs","Baseline and scenario demand"),
        ("Which SKUs contribute most item volume by store?","sales exports","SKU, quantity, created, storefront","units by SKU","month × storefront × source SKU","SKU namespaces differ; canceled rows","Product prioritization"),
        ("How do cancellation rates vary by channel and store?","sales exports","order, status, created, storefront","canceled orders / eligible orders","month × storefront","Lifecycle map and eligible denominator unresolved","Fulfillment intervention"),
        ("Where are fulfillment delays concentrated?","sales exports","created, shipped, delivered, warehouse, province","median created→shipped and shipped→delivered duration","month × store × warehouse × province","Shopee date semantics; sparse timestamps","What-if service target"),
        ("How often are refunds/returns observed?","TikTok sales; Shopee sales","refund, returned quantity, return status, order","return/refund incidence","month × store","Cash refund comparable only for TikTok","Risk score"),
        ("What is the distribution of seller/platform discount signals?","sales exports","discount fields, quantity, order","discount field totals by native source","month × store","Financial scope and allocation unresolved","Promotion sensitivity"),
        ("How do ratings and negative review rates change over time?","TikTok ratings","star_level, review_date, order_id","ratings count; 1–2 star rate","month × TikTok shop","Selection bias; review timestamp","Quality prioritization"),
        ("Which complaint themes merit manual investigation?","TikTok ratings","review_text, star_level, order_id","keyword candidate counts, with manual precision review","month × candidate theme","No validated classifier; text coverage/negation","Explainable issue score"),
    ]
    lines=["# Business requirements", "", "Questions use observed columns only. Monetary sales KPIs remain provisional until financial semantics are resolved.", "", "| Objective/question | Sources | Required fields | KPI | Grain | Limitation | DSS relevance |", "|---|---|---|---|---|---|---|"]
    for row in questions: lines.append("| "+" | ".join(row)+" |")
    lines += ["", "These eight questions support the CO4031 requirement for a data warehouse centered on a real decision problem. DSS candidates are explainable scoring and what-if inputs, not implemented in Phase 1.", ""]
    (docs/"business/business_requirements.md").write_text("\n".join(lines),encoding="utf-8")

    repeated=sum(v["same_order_sku_repeated"] for k,v in keys.items() if k!="tiktok_reviews")
    lines=["# Modeling readiness", "", "## Preliminary constellation", "", "- `fact_order_line_candidate`: product/variant source row, with source row locator and order/package references. Grain is provisional because repeated order-SKU groups total "+f"{repeated:,}." , "- `fact_order_lifecycle_candidate`: one storefront-scoped order; use only attributes verified constant within an order or separately reconciled.", "- `fact_review_candidate`: one rating export row with provisional row locator; link to order where measured, product only when validated.", "- Shared dimensions: date/time roles, channel, storefront, source-specific product/SKU mapping, warehouse, normalized destination province, and reviewed order status. Quasure line classification should be product metadata and may occur in both Shopee stores.", "", "## Phase 2 data contracts", "", "1. Preserve source file name, SHA-256, sheet, physical row locator and ingestion batch. Idempotent load key must include source identity and row identity; content hash alone cannot distinguish legitimate identical lines.", "2. Retain source-native identifiers as strings; key orders by channel + storefront + order ID until cross-source namespace is reconciled.", "3. Keep native status and timestamps; add reviewed status mapping with version and timezone. Treat literal `-` as a missing-value marker, not a timestamp; do not infer missing milestones.", "4. Keep item- and order-scoped money in separate staging fields. Never aggregate order totals over lines; only publish verified KPI definitions.", "5. Drop names, phones, exact addresses and buyer messages from analytical dimensions. Province may be normalized. Review text requires restricted handling and redacted inspection.", "6. Preserve raw files unchanged; incremental ingestion uses source fingerprint and stable batch metadata, with replay/upsert behavior tested in Phase 2.", "", "## Open decisions", "", "Confirm duplicate line meaning; financial formulas and refund semantics; native status mapping; SKU crosswalk; review product-level linkage; timestamp timezone. Physical PostgreSQL DDL is intentionally deferred.", ""]
    (docs/"architecture/modeling_readiness.md").write_text("\n".join(lines),encoding="utf-8")

    observed=[f"{name}: {item['records']:,} rows, {item['columns_count']} columns" for name,item in source.items()]
    lines=["# Phase 1 progress", "", "Generated by `python -m src.profiling.run` against local raw exports.", "", "## Evidence completed", ""]
    lines += [f"- {x}" for x in observed]
    gate = "FAIL" if missing else "CONDITIONAL"
    lines += ["- Measured order/SKU collisions, full duplicates, blank and numeric/date diagnostics, status vocabularies, finance repetition, review ratings/text/linkage for accessible files.", "- Generated six machine-readable reports and eight subject-area documents, plus this progress and decisions file.", "- Source fingerprints in `reports/source_inventory.json`; no raw customer values emitted.", "", f"Missing exports: {', '.join(missing) if missing else 'none'}.", "", f"Validation execution details are in `docs/validation.md`. Quality Gate 1 is {gate}; financial semantics, source row key behavior and review product linkage require business confirmation.", ""]
    lines += ["## Local files created", "", "- `README.md`, `requirements.txt`, `.gitignore`", "- `src/__init__.py`, `src/profiling/__init__.py`, `src/profiling/config.py`, `src/profiling/run.py`, `src/profiling/documents.py`", "- `tests/test_profiling.py`", "- `docs/data/source_inventory.md`, `docs/data/grain_analysis.md`, `docs/data/data_quality_report.md`, `docs/data/cross_platform_mapping.md`, `docs/data/review_feasibility.md`", "- `docs/business/financial_definitions.md`, `docs/business/business_requirements.md`, `docs/architecture/modeling_readiness.md`", "- `docs/progress.md`, `docs/decisions.md`, `docs/validation.md`", "- `reports/source_inventory.json`, `reports/key_uniqueness.json`, `reports/data_quality.json`, `reports/schema_mapping.csv`, `reports/financial_reconciliation.json`, `reports/review_profile.json`", ""]
    (docs/"progress.md").write_text("\n".join(lines),encoding="utf-8")

    lines=["# Decisions and unresolved assumptions", "", "| Decision | Evidence | Status |", "|---|---|---|", "| PostgreSQL only; Kimball constellation candidate | Fixed project architecture and CO4031 multidimensional DW requirement | Adopted for later phases |", "| Preserve TikTok, Shopee Bibica and Shopee Quasure as three storefront/channel members | Three sales exports and business context | Adopted |", "| Keep Quasure as product-line attribute, not separate legal entity | Business context; no legal-entity field verified | Provisional |", "| Source file + sheet + row locator is provisional raw row identity | Order-SKU collision counts in key report | Adopted for staging contract |", "| Treat literal `-` as missing | 5,969 Bibica and 942 Quasure payment-time cells use this exact marker | Adopted for source contract |", "| Defer net sales KPI | Order amount repetition and unresolved discounts/refunds | Open |", "| Restrict review-to-product claims | Review product_id lacks verified sales crosswalk | Open |", "| Exclude direct customer identifiers and detailed addresses from outputs | Raw schemas contain PII columns | Adopted |", "", "No Phase 2 database, ETL, API or dashboard has been implemented.", ""]
    (docs/"decisions.md").write_text("\n".join(lines),encoding="utf-8")
