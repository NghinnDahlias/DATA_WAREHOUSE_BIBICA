"""Streaming Bibica ETL: source files -> PostgreSQL candidate warehouse.

Run from the project root:

    python -m DW.etl.run --dry-run
    python -m DW.etl.run --load --dsn postgresql://...

The loader never publishes customer names, phone numbers, exact addresses,
buyer messages, or raw review text to the analytical tables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from src.profiling.config import FIELDS, SOURCES
from src.profiling.run import blank, number, profile, read_source, timestamp


ROOT = Path(__file__).resolve().parents[2]
DDL_FILES = (
    ROOT / "DW/postgresql/schemas/001_create_schemas.sql",
    ROOT / "DW/postgresql/tables/010_dw_dimensions.sql",
    ROOT / "DW/postgresql/tables/020_dw_facts.sql",
    ROOT / "DW/postgresql/constraints_indexes/constraints_indexes.sql",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text(value: Any) -> str | None:
    return None if blank(value) else str(value).strip()


def row_value(values: list[Any], index: dict[str, int], key: str) -> Any:
    position = index.get(key)
    return None if position is None or position >= len(values) else values[position]


def date_key(value: datetime | None) -> int | None:
    return None if value is None else value.year * 10000 + value.month * 100 + value.day


def time_key(value: datetime | None) -> int | None:
    return None if value is None else value.hour * 10000 + value.minute * 100 + value.second


def source_specs(data_dir: Path) -> list[tuple[str, Path, str, str]]:
    specs = []
    for kind, (filename, source_kind, storefront) in SOURCES.items():
        specs.append((kind, data_dir / filename, source_kind, storefront))
    return specs


def inspect_sources(data_dir: Path) -> list[dict[str, Any]]:
    """Validate headers and return aggregate source metadata without a DB."""
    output = []
    for kind, path, source_kind, storefront in source_specs(data_dir):
        if not path.is_file():
            raise FileNotFoundError(f"Missing source file: {path}")
        result = profile(path, source_kind, kind)
        inventory = result[0]
        output.append({
            "kind": kind,
            "file": path.name,
            "storefront": storefront,
            "records": inventory["records"],
            "columns": inventory["columns_count"],
            "sha256": sha256(path),
        })
    return output


def _insert_id(cur: Any, statement: str, params: tuple[Any, ...]) -> int:
    cur.execute(statement, params)
    row = cur.fetchone()
    if row is None:
        raise RuntimeError("Expected warehouse key was not returned")
    return int(row[0])


def _date_time_keys(cur: Any, value: datetime | None) -> tuple[int | None, int | None]:
    if value is None:
        return None, None
    dkey = date_key(value)
    tkey = time_key(value)
    date_id = _insert_id(
        cur,
        """INSERT INTO dw.dim_date
           (date_key, calendar_date, year, quarter, month, day, month_name, week_of_year)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (date_key) DO UPDATE SET calendar_date = EXCLUDED.calendar_date
           RETURNING date_key""",
        (dkey, value.date(), value.year, (value.month - 1) // 3 + 1,
         value.month, value.day, value.strftime("%B"), value.isocalendar().week),
    )
    time_id = _insert_id(
        cur,
        """INSERT INTO dw.dim_time
           (time_key, native_time, hour, minute, second)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (time_key) DO UPDATE SET native_time = EXCLUDED.native_time
           RETURNING time_key""",
        (tkey, value.time(), value.hour, value.minute, value.second),
    )
    return date_id, time_id


def _ensure_reference(cur: Any, kind: str, storefront: str, channel: str) -> tuple[int, int]:
    channel_key = _insert_id(
        cur,
        """INSERT INTO dw.dim_channel (channel_code, channel_name)
           VALUES (%s, %s) ON CONFLICT (channel_code)
           DO UPDATE SET channel_name = EXCLUDED.channel_name
           RETURNING channel_key""",
        (channel, channel.title()),
    )
    product_line = "Quasure" if "Quasure" in storefront else "Bibica"
    storefront_key = _insert_id(
        cur,
        """INSERT INTO dw.dim_storefront
           (channel_key, storefront_code, storefront_name, product_line)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (storefront_code) DO UPDATE
           SET channel_key = EXCLUDED.channel_key,
               storefront_name = EXCLUDED.storefront_name,
               product_line = EXCLUDED.product_line
           RETURNING storefront_key""",
        (channel_key, kind, storefront, product_line),
    )
    return channel_key, storefront_key


def _source_file_and_batch(cur: Any, path: Path, sheet: str, kind: str,
                           storefront: str, batch_id: str) -> tuple[int, int]:
    source_kind = "tiktok_reviews" if kind == "tiktok_reviews" else (
        "tiktok_sales" if kind == "tiktok_sales" else "shopee_orders"
    )
    file_key = _insert_id(
        cur,
        """INSERT INTO dw.dim_source_file
           (source_file_name, source_sha256, sheet_name, source_kind, source_storefront)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (source_file_name, source_sha256, sheet_name)
           DO UPDATE SET source_storefront = EXCLUDED.source_storefront
           RETURNING source_file_key""",
        (path.name, sha256(path), sheet, source_kind, storefront),
    )
    batch_key = _insert_id(
        cur,
        """INSERT INTO dw.dim_ingestion_batch
           (source_file_key, batch_id, started_at, load_status)
           VALUES (%s, %s, now(), 'STARTED')
           ON CONFLICT (batch_id) DO UPDATE SET source_file_key = EXCLUDED.source_file_key
           RETURNING ingestion_batch_key""",
        (file_key, batch_id),
    )
    return file_key, batch_key


def _order_key(cur: Any, channel_key: int, storefront_key: int, order_id: Any,
               channel_code: str, storefront_code: str) -> int | None:
    native = text(order_id)
    if native is None:
        return None
    namespace = f"{channel_code}|{storefront_code}|{native}"
    return _insert_id(
        cur,
        """INSERT INTO dw.dim_order_identity
           (channel_key, storefront_key, native_order_id, order_namespace)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (order_namespace) DO UPDATE
           SET native_order_id = EXCLUDED.native_order_id
           RETURNING order_key""",
        (channel_key, storefront_key, native, namespace),
    )


def _product_key(cur: Any, channel_key: int, storefront_key: int,
                 source_kind: str, values: list[Any], index: dict[str, int]) -> int | None:
    product_id = text(row_value(values, index, "product_id" if source_kind == "review" else "product_sku"))
    sku = text(row_value(values, index, "sku"))
    product = text(row_value(values, index, "product"))
    variation = text(row_value(values, index, "sku_spec"))
    if not any((product_id, sku, product, variation)):
        return None
    cur.execute(
        """SELECT source_product_sku_key
           FROM dw.dim_source_product_sku
           WHERE channel_key = %s AND storefront_key = %s
             AND native_product_id IS NOT DISTINCT FROM %s
             AND native_sku_id IS NOT DISTINCT FROM %s
             AND product_name IS NOT DISTINCT FROM %s
             AND variation_name IS NOT DISTINCT FROM %s
           LIMIT 1""",
        (channel_key, storefront_key, product_id, sku, product, variation),
    )
    existing = cur.fetchone()
    if existing is not None:
        return int(existing[0])
    return _insert_id(
        cur,
        """INSERT INTO dw.dim_source_product_sku
           (channel_key, storefront_key, native_product_id, native_sku_id,
            product_name, variation_name, mapping_status)
           VALUES (%s, %s, %s, %s, %s, %s, 'UNMAPPED')
           ON CONFLICT (source_product_sku_key) DO NOTHING
           RETURNING source_product_sku_key""",
        (channel_key, storefront_key, product_id, sku, product, variation),
    )


def _load_source(cur: Any, kind: str, path: Path, source_kind: str,
                 storefront: str, batch_id: str) -> int:
    channel = "tiktok" if source_kind in ("tiktok", "review") else "shopee"
    channel_key, storefront_key = _ensure_reference(cur, kind, storefront, channel)
    loaded = 0
    for sheet, header, rows, _fmt in read_source(path):
        lookup = {name: position for position, name in enumerate(header)}
        sheet_loaded = 0
        file_key, batch_key = _source_file_and_batch(
            cur, path, sheet, kind, storefront, f"{batch_id}:{kind}:{sheet}",
        )
        for physical_row, row in enumerate(rows, start=2):
            values = list(row)
            if not values or all(blank(value) for value in values):
                continue
            order_id = row_value(values, lookup, "order")
            order_key = _order_key(
                cur, channel_key, storefront_key, order_id, channel, kind,
            )
            if order_key is None:
                raise ValueError(f"{path.name}:{physical_row}: missing order identifier")
            product_key = _product_key(
                cur, channel_key, storefront_key, source_kind, values, lookup,
            )
            created = timestamp(row_value(values, lookup, "created"))
            created_date, created_time = _date_time_keys(cur, created)
            row_hash = hashlib.sha256(
                json.dumps(values, ensure_ascii=False, default=str).encode("utf-8")
            ).hexdigest()
            if source_kind == "review":
                review_text = text(row_value(values, lookup, "text"))
                cur.execute(
                    """INSERT INTO dw.fact_review_candidate
                       (order_key, channel_key, storefront_key, review_date_key,
                        review_time_key, source_file_key, ingestion_batch_key,
                        source_sheet_name, physical_row_number, source_row_hash,
                        source_product_id, source_product_sku_key, star_level,
                        has_review_text, review_text_length, product_linkage_status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                               %s, %s, %s, %s, %s, 'ORDER_ONLY')
                       ON CONFLICT (source_file_key, source_sheet_name,
                                    physical_row_number, ingestion_batch_key)
                       DO NOTHING""",
                    (order_key, channel_key, storefront_key, created_date,
                     created_time, file_key, batch_key, sheet, physical_row,
                     row_hash, text(row_value(values, lookup, "product_id")),
                     product_key, int(number(row_value(values, lookup, "rating")) or 0),
                     bool(review_text), len(review_text) if review_text else 0),
                )
            else:
                fields = FIELDS["tiktok"] if source_kind == "tiktok" else FIELDS["shopee"]
                parsed = {
                    key: number(row_value(values, lookup, key))
                    for key in ("quantity", "returned_quantity", "unit_price",
                                "gross", "net_item", "seller_discount",
                                "platform_discount", "shipping", "order_amount",
                                "refund", "payment", "payment_alt")
                }
                dates = {
                    key: timestamp(row_value(values, lookup, key))
                    for key in ("created", "paid", "shipped", "delivered", "cancelled")
                }
                date_ids = {key: _date_time_keys(cur, value) for key, value in dates.items()}
                cur.execute(
                    """INSERT INTO dw.fact_order_line_candidate
                       (order_key, channel_key, storefront_key, source_product_sku_key,
                        order_created_date_key, order_created_time_key, paid_date_key,
                        paid_time_key, shipped_date_key, shipped_time_key,
                        delivered_date_key, delivered_time_key, source_file_key,
                        ingestion_batch_key, source_sheet_name, physical_row_number,
                        source_row_hash, quantity, returned_quantity, unit_price_source,
                        gross_item_amount_source, net_item_amount_source,
                        seller_discount_source, platform_discount_source,
                        shipping_buyer_charge_source, order_amount_source)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                               %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                               %s, %s)
                       ON CONFLICT (source_file_key, source_sheet_name,
                                    physical_row_number, ingestion_batch_key)
                       DO NOTHING""",
                    (order_key, channel_key, storefront_key, product_key,
                     date_ids["created"][0], date_ids["created"][1],
                     date_ids["paid"][0], date_ids["paid"][1],
                     date_ids["shipped"][0], date_ids["shipped"][1],
                     date_ids["delivered"][0], date_ids["delivered"][1],
                     file_key, batch_key, sheet, physical_row, row_hash,
                     parsed["quantity"], parsed["returned_quantity"],
                     parsed["unit_price"], parsed["gross"], parsed["net_item"],
                     parsed["seller_discount"], parsed["platform_discount"],
                     parsed["shipping"], parsed["order_amount"]),
                )
            loaded += 1
            sheet_loaded += 1
        cur.execute(
            """UPDATE dw.dim_ingestion_batch
               SET completed_at = now(), load_status = 'LOADED',
                   row_count_read = %s, row_count_loaded = %s
               WHERE ingestion_batch_key = %s""",
            (sheet_loaded, sheet_loaded, batch_key),
        )
    return loaded


def load_postgres(data_dir: Path, dsn: str, batch_id: str) -> list[dict[str, Any]]:
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("Install dependencies first: python -m pip install -r requirements.txt") from exc
    summaries = []
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cur:
            for ddl in DDL_FILES:
                cur.execute(ddl.read_text(encoding="utf-8"))
            for kind, path, source_kind, storefront in source_specs(data_dir):
                summaries.append({
                    "kind": kind,
                    "rows_loaded": _load_source(
                        cur, kind, path, source_kind, storefront, batch_id,
                    ),
                })
        connection.commit()
    return summaries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "Data/Data_Source_Raw")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--load", action="store_true")
    parser.add_argument("--dsn", default=os.environ.get("BIBICA_DSN"))
    parser.add_argument("--batch-id", default=None)
    args = parser.parse_args(argv)
    if args.load and args.dry_run:
        parser.error("--load and --dry-run are mutually exclusive")
    if not args.load and not args.dry_run:
        parser.error("Choose --dry-run or --load")
    summary = inspect_sources(args.data_dir)
    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if not args.dsn:
        parser.error("--dsn or BIBICA_DSN is required with --load")
    batch_id = args.batch_id or datetime.now().strftime("bibica-%Y%m%d%H%M%S")
    print(json.dumps(load_postgres(args.data_dir, args.dsn, batch_id),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
