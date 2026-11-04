from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from src.profiling.config import FIELDS
from src.profiling.run import blank, norm, number, read_source, timestamp


@dataclass(frozen=True)
class SourceSpec:
    name: str
    path: Path
    source_kind: str
    channel_code: str
    storefront_code: str
    storefront_name: str


@dataclass(frozen=True)
class SourceRow:
    spec: SourceSpec
    sheet_name: str
    physical_row_number: int
    values: tuple[Any, ...]
    lookup: dict[str, int]
    source_row_hash: str

    def value(self, key: str) -> Any:
        position = self.lookup.get(key)
        if position is None or position >= len(self.values):
            return None
        return self.values[position]


@dataclass(frozen=True)
class RowError:
    file: str
    sheet: str
    row: int
    code: str
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "sheet": self.sheet,
            "row": self.row,
            "code": self.code,
            "message": self.message,
        }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_rows(spec: SourceSpec) -> tuple[list[SourceRow], list[RowError]]:
    rows: list[SourceRow] = []
    errors: list[RowError] = []
    if not spec.path.is_file():
        errors.append(RowError(spec.path.name, "", 0, "missing_file", str(spec.path)))
        return rows, errors

    expected = FIELDS[spec.source_kind]
    for sheet_name, header, source_iter, _format in read_source(spec.path):
        header_lookup = {norm(name): position for position, name in enumerate(header)}
        missing = [
            name for name in expected.values() if norm(name) not in header_lookup
        ]
        if missing:
            errors.append(RowError(
                spec.path.name, sheet_name, 1, "missing_headers", ", ".join(missing),
            ))
            continue
        lookup = {
            logical: header_lookup[norm(source_name)]
            for logical, source_name in expected.items()
        }
        for physical_row, raw_row in enumerate(source_iter, start=2):
            values = list(raw_row)
            if not values or all(blank(value) for value in values):
                continue
            row_hash = hashlib.sha256(
                json.dumps(values, ensure_ascii=False, default=str).encode("utf-8")
            ).hexdigest()
            rows.append(SourceRow(
                spec, sheet_name, physical_row, tuple(values), lookup, row_hash,
            ))
    return rows, errors


def validate_row(row: SourceRow) -> list[RowError]:
    errors: list[RowError] = []
    prefix = (row.spec.path.name, row.sheet_name, row.physical_row_number)
    if blank(row.value("order")):
        errors.append(RowError(*prefix, "missing_order_id", "order identifier is blank"))
    if blank(row.value("created")):
        errors.append(RowError(*prefix, "missing_created", "created timestamp is blank"))
    elif timestamp(row.value("created")) is None:
        errors.append(RowError(*prefix, "invalid_created", "created timestamp cannot be parsed"))

    if row.spec.source_kind == "review":
        rating = number(row.value("rating"))
        if rating is None or not 1 <= rating <= 5:
            errors.append(RowError(*prefix, "invalid_rating", "rating must be between 1 and 5"))
        return errors

    if blank(row.value("status")):
        errors.append(RowError(*prefix, "missing_status", "native order status is blank"))
    for key in ("quantity", "unit_price", "net_item", "order_amount"):
        value = row.value(key)
        if not blank(value) and number(value) is None:
            errors.append(RowError(*prefix, f"invalid_{key}", f"{key} is not numeric"))
    for key in ("warehouse", "province"):
        if blank(row.value(key)):
            errors.append(RowError(*prefix, f"missing_{key}", f"{key} is blank"))
    return errors


def inspect_source(spec: SourceSpec) -> dict[str, Any]:
    rows, structural_errors = source_rows(spec)
    row_errors = [error for row in rows for error in validate_row(row)]
    errors = structural_errors + row_errors
    invalid_rows = {(error.sheet, error.row) for error in row_errors}
    return {
        "source": spec.name,
        "file": spec.path.name,
        "channel": spec.channel_code,
        "storefront": spec.storefront_code,
        "storefront_name": spec.storefront_name,
        "source_kind": spec.source_kind,
        "sha256": file_sha256(spec.path) if spec.path.is_file() else None,
        "rows": len(rows),
        "columns": len(rows[0].values) if rows else 0,
        "valid_rows": len(rows) - len(invalid_rows),
        "structural_errors": [error.as_dict() for error in structural_errors[:100]],
        "row_validation_errors": [error.as_dict() for error in row_errors[:100]],
        "error_count": len(errors),
        "errors": [error.as_dict() for error in errors[:100]],
        "errors_truncated": max(0, len(errors) - 100),
        "row_objects": rows,
        "structural_error": bool(structural_errors),
    }


def source_specs(data_dir: Path, sources: dict[str, tuple[str, str, str]]) -> list[SourceSpec]:
    storefronts = {
        "Bibica TikTok Shop": ("tiktok", "bibica_tiktok_shop"),
        "Bibica Official Store": ("shopee", "bibica_official_store"),
        "Quasure specialized store": ("shopee", "quasure_specialized_store"),
    }
    specs = []
    for name, (filename, source_kind, storefront_name) in sources.items():
        channel_code, storefront_code = storefronts[storefront_name]
        specs.append(SourceSpec(
            name, data_dir / filename, source_kind, channel_code,
            storefront_code, storefront_name,
        ))
    return specs
