"""Bibica ETL runner with cached dimensions and PostgreSQL COPY loading."""
from __future__ import annotations
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from src.profiling.config import SOURCES
from src.profiling.run import blank, number, timestamp
from .extract.readers import (
    SourceRow,
    SourceSpec,
    file_sha256,
    inspect_source,
    source_rows,
    source_specs,
    validate_row,
)
ROOT = Path(__file__).resolve().parents[2]
DDL_FILES = (
    ROOT / "DW/postgresql/schemas/001_create_schemas.sql",
    ROOT / "DW/postgresql/tables/010_dw_dimensions.sql",
    ROOT / "DW/postgresql/tables/020_dw_facts.sql",
    ROOT / "DW/postgresql/constraints_indexes/constraints_indexes.sql",
)
def text(value: Any) -> str | None:
    return None if blank(value) else str(value).strip()
def date_key(value: datetime | None) -> int | None:
    return None if value is None else value.year * 10000 + value.month * 100 + value.day
def time_key(value: datetime | None) -> int | None:
    return None if value is None else value.hour * 10000 + value.minute * 100 + value.second
def _insert_id(cur: Any, sql: str, params: tuple[Any, ...]) -> int:
    cur.execute(sql, params)
    row = cur.fetchone()
    if row is None:
        raise RuntimeError("PostgreSQL did not return a warehouse key")
    return int(row[0])
def _copy_rows(cur: Any, table: str, columns: Iterable[str], rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return
    column_sql = ", ".join(columns)
    with cur.copy(f"COPY {table} ({column_sql}) FROM STDIN") as copy:
        for row in rows:
            copy.write_row(row)
def _create_temp_tables(cur: Any) -> None:
    cur.execute("""
        CREATE TEMP TABLE tmp_bibica_orders (
            channel_key bigint NOT NULL,
            storefront_key bigint NOT NULL,
            native_order_id text NOT NULL,
            order_namespace text NOT NULL
        ) ON COMMIT DROP;
        CREATE TEMP TABLE tmp_bibica_products (
            channel_key bigint NOT NULL,
            storefront_key bigint NOT NULL,
            native_product_id text,
            native_sku_id text,
            product_name text,
            variation_name text
        ) ON COMMIT DROP;
        CREATE TEMP TABLE tmp_bibica_order_lines (
            order_key bigint NOT NULL,
            channel_key bigint NOT NULL,
            storefront_key bigint NOT NULL,
            source_product_sku_key bigint,
            warehouse_key bigint,
            province_key bigint,
            order_status_key bigint,
            order_created_date_key integer NOT NULL,
            order_created_time_key integer,
            paid_date_key integer,
            paid_time_key integer,
            shipped_date_key integer,
            shipped_time_key integer,
            delivered_date_key integer,
            delivered_time_key integer,
            source_file_key bigint NOT NULL,
            ingestion_batch_key bigint NOT NULL,
            source_sheet_name text NOT NULL,
            physical_row_number integer NOT NULL,
            source_row_hash text NOT NULL,
            quantity numeric(18,4),
            returned_quantity numeric(18,4),
            unit_price_source numeric(19,4),
            gross_item_amount_source numeric(19,4),
            net_item_amount_source numeric(19,4),
            seller_discount_source numeric(19,4),
            platform_discount_source numeric(19,4),
            shipping_buyer_charge_source numeric(19,4),
            order_amount_source numeric(19,4)
        ) ON COMMIT DROP;
        CREATE TEMP TABLE tmp_bibica_reviews (
            order_key bigint,
            channel_key bigint NOT NULL,
            storefront_key bigint NOT NULL,
            review_date_key integer NOT NULL,
            review_time_key integer,
            source_file_key bigint NOT NULL,
            ingestion_batch_key bigint NOT NULL,
            source_sheet_name text NOT NULL,
            physical_row_number integer NOT NULL,
            source_row_hash text NOT NULL,
            source_product_id text,
            source_product_sku_key bigint,
            star_level smallint NOT NULL,
            has_review_text boolean NOT NULL,
            review_text_length integer
        ) ON COMMIT DROP;
        CREATE TEMP TABLE tmp_bibica_lifecycle (
            order_key bigint NOT NULL,
            channel_key bigint NOT NULL,
            storefront_key bigint NOT NULL,
            order_status_key bigint,
            warehouse_key bigint,
            province_key bigint,
            created_date_key integer NOT NULL,
            created_time_key integer,
            paid_date_key integer,
            paid_time_key integer,
            shipped_date_key integer,
            shipped_time_key integer,
            delivered_date_key integer,
            delivered_time_key integer,
            cancelled_date_key integer,
            cancelled_time_key integer,
            source_file_key bigint NOT NULL,
            ingestion_batch_key bigint NOT NULL,
            order_row_count integer NOT NULL,
            order_amount_source numeric(19,4),
            buyer_payment_source_1 numeric(19,4),
            buyer_payment_source_2 numeric(19,4),
            refund_amount_source numeric(19,4),
            reconciliation_status text NOT NULL
        ) ON COMMIT DROP;
    """)
def _reference_keys(cur: Any, spec: SourceSpec) -> tuple[int, int]:
    channel_key = _insert_id(
        cur,
        """INSERT INTO dw.dim_channel (channel_code, channel_name)
        VALUES (%s, %s)
        ON CONFLICT (channel_code) DO UPDATE SET channel_name = EXCLUDED.channel_name
        RETURNING channel_key""",
        (spec.channel_code, spec.channel_code.title()),
    )
    product_line = "Quasure" if spec.storefront_code.startswith("quasure") else None
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
        (channel_key, spec.storefront_code, spec.storefront_name, product_line),
    )
    return channel_key, storefront_key
def _source_batch(cur: Any, spec: SourceSpec, sheet: str, batch_id: str) -> tuple[int, int]:
    source_kind = (
        "tiktok_reviews" if spec.source_kind == "review"
        else "tiktok_sales" if spec.source_kind == "tiktok"
        else "shopee_orders"
    )
    source_key = _insert_id(
        cur,
        """INSERT INTO dw.dim_source_file
        (source_file_name, source_sha256, sheet_name, source_kind, source_storefront)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source_file_name, source_sha256, sheet_name)
        DO UPDATE SET source_storefront = EXCLUDED.source_storefront
        RETURNING source_file_key""",
        (spec.path.name, file_sha256(spec.path), sheet, source_kind, spec.storefront_name),
    )
    ingestion_key = _insert_id(
        cur,
        """INSERT INTO dw.dim_ingestion_batch
        (source_file_key, batch_id, started_at, load_status)
        VALUES (%s, %s, now(), 'STARTED')
        ON CONFLICT (batch_id) DO UPDATE SET source_file_key = EXCLUDED.source_file_key
        RETURNING ingestion_batch_key""",
        (source_key, f"{batch_id}:{spec.name}:{sheet}"),
    )
    return source_key, ingestion_key
def _parsed_dates(row: SourceRow) -> dict[str, datetime | None]:
    return {
        name: timestamp(row.value(name))
        for name in ("created", "paid", "shipped", "delivered", "cancelled")
    }
def _prime_dimensions(
    cur: Any,
    spec: SourceSpec,
    rows: list[SourceRow],
    channel_key: int,
    storefront_key: int,
    order_cache: dict[str, int],
    product_cache: dict[tuple[Any, ...], int],
    date_cache: dict[datetime, tuple[int, int]],
    dimension_cache: dict[tuple[str, tuple[Any, ...]], int],
    status_cache: dict[tuple[str, str, str], int],
) -> None:
    cur.execute("TRUNCATE tmp_bibica_orders, tmp_bibica_products")
    orders = {
        native for native in (text(row.value("order")) for row in rows) if native
    }
    _copy_rows(
        cur,
        "tmp_bibica_orders",
        ("channel_key", "storefront_key", "native_order_id", "order_namespace"),
        [
            (channel_key, storefront_key, native,
             f"{spec.channel_code}|{spec.storefront_code}|{native}")
            for native in orders
        ],
    )
    cur.execute("""
        INSERT INTO dw.dim_order_identity
            (channel_key, storefront_key, native_order_id, order_namespace)
        SELECT DISTINCT channel_key, storefront_key, native_order_id, order_namespace
        FROM tmp_bibica_orders
        ON CONFLICT (order_namespace) DO NOTHING
    """)
    if orders:
        cur.execute(
            """SELECT native_order_id, order_key
            FROM dw.dim_order_identity
            WHERE channel_key = %s AND storefront_key = %s
              AND native_order_id = ANY(%s)""",
            (channel_key, storefront_key, list(orders)),
        )
        order_cache.update({str(native): int(key) for native, key in cur.fetchall()})
    product_rows = []
    for row in rows:
        product_id = text(row.value("product_id" if row.spec.source_kind == "review" else "product_sku"))
        sku = text(row.value("sku"))
        product = text(row.value("product"))
        variation = text(row.value("sku_spec"))
        if any((product_id, sku, product, variation)):
            product_rows.append((channel_key, storefront_key, product_id, sku, product, variation))
    _copy_rows(
        cur,
        "tmp_bibica_products",
        ("channel_key", "storefront_key", "native_product_id", "native_sku_id", "product_name", "variation_name"),
        product_rows,
    )
    cur.execute("""
        INSERT INTO dw.dim_source_product_sku
            (channel_key, storefront_key, native_product_id, native_sku_id,
             product_name, variation_name, mapping_status)
        SELECT DISTINCT p.channel_key, p.storefront_key, p.native_product_id,
                        p.native_sku_id, p.product_name, p.variation_name, 'PROVISIONAL'
        FROM tmp_bibica_products p
        WHERE NOT EXISTS (
            SELECT 1
            FROM dw.dim_source_product_sku d
            WHERE d.channel_key = p.channel_key
              AND d.storefront_key = p.storefront_key
              AND d.native_product_id IS NOT DISTINCT FROM p.native_product_id
              AND d.native_sku_id IS NOT DISTINCT FROM p.native_sku_id
              AND d.product_name IS NOT DISTINCT FROM p.product_name
              AND d.variation_name IS NOT DISTINCT FROM p.variation_name
        )
    """)
    cur.execute(
        """SELECT native_product_id, native_sku_id, product_name,
                         variation_name, source_product_sku_key
        FROM dw.dim_source_product_sku
        WHERE channel_key = %s AND storefront_key = %s""",
        (channel_key, storefront_key),
    )
    product_cache.update({
        (native_product_id, native_sku_id, product_name, variation_name): int(key)
        for native_product_id, native_sku_id, product_name, variation_name, key in cur.fetchall()
    })
    dates = {
        parsed
        for row in rows
        for parsed in _parsed_dates(row).values()
        if parsed is not None
    }
    _copy_rows(
        cur,
        "tmp_bibica_orders",
        ("channel_key", "storefront_key", "native_order_id", "order_namespace"),
        [],
    )
    if dates:
        cur.executemany(
            """INSERT INTO dw.dim_date
            (date_key, calendar_date, year, quarter, month, day, month_name, week_of_year)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date_key) DO NOTHING""",
            [
                (date_key(value), value.date(), value.year, (value.month - 1) // 3 + 1,
                 value.month, value.day, value.strftime("%B"), value.isocalendar().week)
                for value in dates
            ],
        )
        cur.executemany(
            """INSERT INTO dw.dim_time
            (time_key, native_time, hour, minute, second)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (time_key) DO NOTHING""",
            [
                (time_key(value), value.time(), value.hour, value.minute, value.second)
                for value in dates
            ],
        )
        cur.execute(
            "SELECT date_key, calendar_date FROM dw.dim_date WHERE calendar_date = ANY(%s)",
            ([value.date() for value in dates],),
        )
        date_values = {calendar_date: int(key) for key, calendar_date in cur.fetchall()}
        cur.execute(
            "SELECT time_key, native_time FROM dw.dim_time WHERE native_time = ANY(%s)",
            ([value.time() for value in dates],),
        )
        time_values = {native_time: int(key) for key, native_time in cur.fetchall()}
        date_cache.update({
            value: (date_values[value.date()], time_values[value.time()])
            for value in dates
        })
    warehouses = {
        text(row.value("warehouse"))
        for row in rows
        if text(row.value("warehouse")) is not None
    }
    cur.executemany(
        """INSERT INTO dw.dim_warehouse
        (storefront_key, native_warehouse_name, mapping_status)
        VALUES (%s, %s, 'PROVISIONAL')
        ON CONFLICT (storefront_key, native_warehouse_name) DO NOTHING""",
        [(storefront_key, value) for value in warehouses],
    )
    if warehouses:
        cur.execute(
            """SELECT native_warehouse_name, warehouse_key
            FROM dw.dim_warehouse
            WHERE storefront_key = %s AND native_warehouse_name = ANY(%s)""",
            (storefront_key, list(warehouses)),
        )
        dimension_cache.update({
            ("warehouse", (storefront_key, str(native))): int(key)
            for native, key in cur.fetchall()
        })
    provinces = {
        text(row.value("province"))
        for row in rows
        if text(row.value("province")) is not None
    }
    cur.executemany(
        """INSERT INTO dw.dim_province (native_province_name, mapping_status)
        VALUES (%s, 'PROVISIONAL')
        ON CONFLICT (native_province_name) DO NOTHING""",
        [(value,) for value in provinces],
    )
    if provinces:
        cur.execute(
            """SELECT native_province_name, province_key
            FROM dw.dim_province WHERE native_province_name = ANY(%s)""",
            (list(provinces),),
        )
        dimension_cache.update({
            ("province", (str(native),)): int(key)
            for native, key in cur.fetchall()
        })
    statuses = {
        text(row.value("status"))
        for row in rows
        if text(row.value("status")) is not None
    }
    cur.executemany(
        """INSERT INTO dw.dim_order_status
        (channel_key, storefront_key, native_status, reviewed_status)
        SELECT %s, %s, %s, NULL
        WHERE NOT EXISTS (
            SELECT 1 FROM dw.dim_order_status
            WHERE channel_key = %s AND storefront_key = %s
              AND native_status = %s
        )""",
        [
            (channel_key, storefront_key, value,
             channel_key, storefront_key, value)
            for value in statuses
        ],
    )
    if statuses:
        cur.execute(
            """SELECT native_status, order_status_key
            FROM dw.dim_order_status
            WHERE channel_key = %s AND storefront_key = %s
              AND native_status = ANY(%s)""",
            (channel_key, storefront_key, list(statuses)),
        )
        status_cache.update({
            (spec.storefront_code, spec.channel_code, str(native)): int(key)
            for native, key in cur.fetchall()
        })
def _one(values: set[Any]) -> Any:
    return next(iter(values)) if len(values) == 1 else None
def _reconcile_status(state: dict[str, Any]) -> str:
    collections = [*state["dates"].values(), *state["dimensions"].values(), *state["amounts"].values()]
    if any(len(values) > 1 for values in collections):
        return "CONFLICTING"
    return "CONSTANT" if any(values for values in collections) else "MISSING"
def _load_rows(
    cur: Any,
    spec: SourceSpec,
    rows: list[SourceRow],
    batch_id: str,
    errors: list[dict[str, Any]],
) -> dict[str, int]:
    channel_key, storefront_key = _reference_keys(cur, spec)
    order_cache: dict[str, int] = {}
    product_cache: dict[tuple[Any, ...], int] = {}
    date_cache: dict[datetime, tuple[int, int]] = {}
    dimension_cache: dict[tuple[str, tuple[Any, ...]], int] = {}
    status_cache: dict[tuple[str, str, str], int] = {}
    facts = defaultdict(int)
    by_sheet: dict[str, list[SourceRow]] = defaultdict(list)
    for row in rows:
        by_sheet[row.sheet_name].append(row)
    for sheet, sheet_rows in by_sheet.items():
        source_key, batch_key = _source_batch(cur, spec, sheet, batch_id)
        loaded_before = facts["order_line_rows"] + facts["review_rows"]
        valid_rows: list[SourceRow] = []
        for row in sheet_rows:
            row_errors = validate_row(row)
            if row_errors:
                errors.extend(error.as_dict() for error in row_errors)
            else:
                valid_rows.append(row)
        _prime_dimensions(
            cur, spec, valid_rows, channel_key, storefront_key, order_cache,
            product_cache, date_cache, dimension_cache, status_cache,
        )
        line_params: list[tuple[Any, ...]] = []
        review_params: list[tuple[Any, ...]] = []
        lifecycle_state: dict[int, dict[str, Any]] = {}
        for row in valid_rows:
            native_order = text(row.value("order"))
            if native_order is None:
                continue
            try:
                order_key = order_cache[native_order]
                product_id = text(row.value("product_id" if row.spec.source_kind == "review" else "product_sku"))
                identity = (
                    product_id,
                    text(row.value("sku")),
                    text(row.value("product")),
                    text(row.value("sku_spec")),
                )
                product_key = product_cache.get(identity)
                dates = _parsed_dates(row)
                date_ids = {
                    name: date_cache[value] if value is not None else (None, None)
                    for name, value in dates.items()
                }
                status_value = text(row.value("status"))
                status_key = status_cache.get(
                    (spec.storefront_code, spec.channel_code, status_value)
                ) if status_value else None
                warehouse_value = text(row.value("warehouse"))
                province_value = text(row.value("province"))
                warehouse_key = dimension_cache.get(("warehouse", (storefront_key, warehouse_value))) if warehouse_value else None
                province_key = dimension_cache.get(("province", (province_value,))) if province_value else None
                if spec.source_kind == "review":
                    review_text = text(row.value("text"))
                    review_params.append(
                        (order_key, channel_key, storefront_key, date_ids["created"][0],
                         date_ids["created"][1], source_key, batch_key, sheet,
                         row.physical_row_number, row.source_row_hash, product_id,
                         product_key, int(number(row.value("rating"))), bool(review_text),
                         len(review_text) if review_text else 0)
                    )
                    continue
                values = {
                    name: number(row.value(name))
                    for name in (
                        "quantity", "returned_quantity", "unit_price", "gross",
                        "net_item", "seller_discount", "platform_discount",
                    )
                }
                line_params.append(
                    (order_key, channel_key, storefront_key, product_key,
                     warehouse_key, province_key, status_key, date_ids["created"][0],
                     date_ids["created"][1], date_ids["paid"][0], date_ids["paid"][1],
                     date_ids["shipped"][0], date_ids["shipped"][1],
                     date_ids["delivered"][0], date_ids["delivered"][1], source_key,
                     batch_key, sheet, row.physical_row_number, row.source_row_hash,
                     values["quantity"], values["returned_quantity"], values["unit_price"],
                     values["gross"] if spec.source_kind == "tiktok" else None,
                     values["net_item"] if spec.source_kind == "tiktok" else None,
                     values["seller_discount"], values["platform_discount"], None, None)
                )
                state = lifecycle_state.setdefault(order_key, {
                    "row_count": 0,
                    "dates": defaultdict(set),
                    "dimensions": defaultdict(set),
                    "amounts": defaultdict(set),
                })
                state["row_count"] += 1
                for name, value in dates.items():
                    if value is not None:
                        state["dates"][name].add(value)
                for name, value in (
                    ("status", status_key), ("warehouse", warehouse_key), ("province", province_key)
                ):
                    if value is not None:
                        state["dimensions"][name].add(value)
                for name in ("order_amount", "payment", "payment_alt", "refund"):
                    value = number(row.value(name))
                    if value is not None:
                        state["amounts"][name].add(value)
            except Exception as exc:
                errors.append({
                    "file": row.spec.path.name,
                    "sheet": row.sheet_name,
                    "row": row.physical_row_number,
                    "code": "transform_row_error",
                    "message": str(exc),
                })
        cur.execute("""
            TRUNCATE tmp_bibica_order_lines, tmp_bibica_reviews, tmp_bibica_lifecycle
        """)
        _copy_rows(
            cur,
            "tmp_bibica_order_lines",
            ("order_key", "channel_key", "storefront_key", "source_product_sku_key",
             "warehouse_key", "province_key", "order_status_key",
             "order_created_date_key", "order_created_time_key", "paid_date_key",
             "paid_time_key", "shipped_date_key", "shipped_time_key",
             "delivered_date_key", "delivered_time_key", "source_file_key",
             "ingestion_batch_key", "source_sheet_name", "physical_row_number",
             "source_row_hash", "quantity", "returned_quantity", "unit_price_source",
             "gross_item_amount_source", "net_item_amount_source",
             "seller_discount_source", "platform_discount_source",
             "shipping_buyer_charge_source", "order_amount_source"),
            line_params,
        )
        _copy_rows(
            cur,
            "tmp_bibica_reviews",
            ("order_key", "channel_key", "storefront_key", "review_date_key",
             "review_time_key", "source_file_key", "ingestion_batch_key",
             "source_sheet_name", "physical_row_number", "source_row_hash",
             "source_product_id", "source_product_sku_key", "star_level",
             "has_review_text", "review_text_length"),
            review_params,
        )
        lifecycle_params = []
        for order_key, state in lifecycle_state.items():
            date_ids = {
                name: (date_cache[_one(values)] if len(values) == 1 else (None, None))
                for name, values in state["dates"].items()
            }
            amounts = state["amounts"]
            dimensions = state["dimensions"]
            lifecycle_params.append(
                (order_key, channel_key, storefront_key,
                 _one(dimensions["status"]), _one(dimensions["warehouse"]),
                 _one(dimensions["province"]), date_ids.get("created", (None, None))[0],
                 date_ids.get("created", (None, None))[1], date_ids.get("paid", (None, None))[0],
                 date_ids.get("paid", (None, None))[1], date_ids.get("shipped", (None, None))[0],
                 date_ids.get("shipped", (None, None))[1], date_ids.get("delivered", (None, None))[0],
                 date_ids.get("delivered", (None, None))[1], date_ids.get("cancelled", (None, None))[0],
                 date_ids.get("cancelled", (None, None))[1], source_key, batch_key,
                 state["row_count"], _one(amounts["order_amount"]), _one(amounts["payment"]),
                 _one(amounts["payment_alt"]), _one(amounts["refund"]), _reconcile_status(state))
            )
        _copy_rows(
            cur,
            "tmp_bibica_lifecycle",
            ("order_key", "channel_key", "storefront_key", "order_status_key",
             "warehouse_key", "province_key", "created_date_key", "created_time_key",
             "paid_date_key", "paid_time_key", "shipped_date_key", "shipped_time_key",
             "delivered_date_key", "delivered_time_key", "cancelled_date_key",
             "cancelled_time_key", "source_file_key", "ingestion_batch_key",
             "order_row_count", "order_amount_source", "buyer_payment_source_1",
             "buyer_payment_source_2", "refund_amount_source", "reconciliation_status"),
            lifecycle_params,
        )
        cur.execute("""
            INSERT INTO dw.fact_order_line_candidate (
                order_key, channel_key, storefront_key, source_product_sku_key,
                warehouse_key, province_key, order_status_key,
                order_created_date_key, order_created_time_key, paid_date_key,
                paid_time_key, shipped_date_key, shipped_time_key,
                delivered_date_key, delivered_time_key, source_file_key,
                ingestion_batch_key, source_sheet_name, physical_row_number,
                source_row_hash, quantity, returned_quantity, unit_price_source,
                gross_item_amount_source, net_item_amount_source,
                seller_discount_source, platform_discount_source,
                shipping_buyer_charge_source, order_amount_source
            )
            SELECT order_key, channel_key, storefront_key, source_product_sku_key,
                   warehouse_key, province_key, order_status_key,
                   order_created_date_key, order_created_time_key, paid_date_key,
                   paid_time_key, shipped_date_key, shipped_time_key,
                   delivered_date_key, delivered_time_key, source_file_key,
                   ingestion_batch_key, source_sheet_name, physical_row_number,
                   source_row_hash, quantity, returned_quantity, unit_price_source,
                   gross_item_amount_source, net_item_amount_source,
                   seller_discount_source, platform_discount_source,
                   shipping_buyer_charge_source, order_amount_source
            FROM tmp_bibica_order_lines
            ON CONFLICT (source_file_key, source_sheet_name,
                         physical_row_number) DO NOTHING
        """)
        facts["order_line_rows"] += max(cur.rowcount, 0)
        cur.execute("""
            INSERT INTO dw.fact_review_candidate (
                order_key, channel_key, storefront_key, review_date_key,
                review_time_key, source_file_key, ingestion_batch_key,
                source_sheet_name, physical_row_number, source_row_hash,
                source_product_id, source_product_sku_key, star_level,
                has_review_text, review_text_length, product_linkage_status
            )
            SELECT order_key, channel_key, storefront_key, review_date_key,
                   review_time_key, source_file_key, ingestion_batch_key,
                   source_sheet_name, physical_row_number, source_row_hash,
                   source_product_id, source_product_sku_key, star_level,
                   has_review_text, review_text_length, 'ORDER_ONLY'
            FROM tmp_bibica_reviews
            ON CONFLICT (source_file_key, source_sheet_name,
                         physical_row_number) DO NOTHING
        """)
        facts["review_rows"] += max(cur.rowcount, 0)
        cur.execute("""
            INSERT INTO dw.fact_order_lifecycle_candidate (
                order_key, channel_key, storefront_key, order_status_key,
                warehouse_key, province_key, created_date_key, created_time_key,
                paid_date_key, paid_time_key, shipped_date_key, shipped_time_key,
                delivered_date_key, delivered_time_key, cancelled_date_key,
                cancelled_time_key, source_file_key, ingestion_batch_key,
                order_row_count, order_amount_source, buyer_payment_source_1,
                buyer_payment_source_2, refund_amount_source, reconciliation_status
            )
            SELECT order_key, channel_key, storefront_key, order_status_key,
                   warehouse_key, province_key, created_date_key, created_time_key,
                   paid_date_key, paid_time_key, shipped_date_key, shipped_time_key,
                   delivered_date_key, delivered_time_key, cancelled_date_key,
                   cancelled_time_key, source_file_key, ingestion_batch_key,
                   order_row_count, order_amount_source, buyer_payment_source_1,
                   buyer_payment_source_2, refund_amount_source, reconciliation_status
            FROM tmp_bibica_lifecycle
            ON CONFLICT (order_key) DO NOTHING
        """)
        facts["lifecycle_rows"] += max(cur.rowcount, 0)
        cur.execute(
            """UPDATE dw.dim_ingestion_batch
            SET completed_at = now(),
                load_status = CASE
                    WHEN %s > 0 AND %s = 0 THEN 'REPLAYED'
                    ELSE 'LOADED'
                END,
                row_count_read = %s, row_count_loaded = %s
            WHERE ingestion_batch_key = %s""",
            (
                len(valid_rows),
                facts["order_line_rows"] + facts["review_rows"] - loaded_before,
                len(sheet_rows),
                facts["order_line_rows"] + facts["review_rows"] - loaded_before,
                batch_key,
            ),
        )
    return dict(facts)
def dry_run(data_dir: Path) -> tuple[dict[str, Any], int]:
    reports = []
    rows_read = 0
    valid_rows = 0
    all_errors: list[dict[str, Any]] = []
    for spec in source_specs(data_dir, SOURCES):
        report = inspect_source(spec)
        rows_read += report["rows"]
        valid_rows += report["valid_rows"]
        all_errors.extend(report["errors"])
        report.pop("row_objects", None)
        reports.append(report)
    result = {
        "rows_read": rows_read,
        "valid_rows": valid_rows,
        "errors": all_errors[:100],
        "errors_truncated": max(0, len(all_errors) - 100),
        "warnings": [
            "Shopee financial amount semantics are not verified",
            "Repeated order-SKU lines are retained",
            "Review product linkage is ORDER_ONLY",
        ],
        "load_ready": False,
        "sources": reports,
    }
    return result, 2 if all_errors else 0
def load_postgres(data_dir: Path, dsn: str, batch_id: str) -> dict[str, Any]:
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("Install requirements.txt before loading PostgreSQL") from exc
    errors: list[dict[str, Any]] = []
    facts: dict[str, int] = defaultdict(int)
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cur:
            for ddl_file in DDL_FILES:
                cur.execute(ddl_file.read_text(encoding="utf-8"))
            _create_temp_tables(cur)
            for spec in source_specs(data_dir, SOURCES):
                rows, source_errors = source_rows(spec)
                errors.extend(source_error.as_dict() for source_error in source_errors)
                if source_errors:
                    continue
                result = _load_rows(cur, spec, rows, batch_id, errors)
                for key, value in result.items():
                    facts[key] += value
        connection.commit()
    return {
        "facts": dict(facts),
        "error_count": len(errors),
        "errors": errors[:100],
        "errors_truncated": max(0, len(errors) - 100),
    }
def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "Data" / "Data_Source_Raw")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--load", action="store_true")
    parser.add_argument("--dsn", default=os.environ.get("BIBICA_DSN"))
    parser.add_argument("--batch-id", default=None)
    args = parser.parse_args(argv)
    if args.dry_run == args.load:
        parser.error("Choose exactly one of --dry-run or --load")
    if args.load and not args.dsn:
        parser.error("--dsn or BIBICA_DSN is required with --load")
    if args.dry_run:
        result, code = dry_run(args.data_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    batch_id = args.batch_id or datetime.now().strftime("bibica-%Y%m%d%H%M%S")
    print(json.dumps(load_postgres(args.data_dir, args.dsn, batch_id), ensure_ascii=False, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
