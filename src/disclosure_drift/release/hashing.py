"""Normalized table-content hashing for release reproducibility (Decision 009 §10).

Reproducibility is asserted on **content**, not on Parquet file bytes: stable
column order, stable row order, UTC-normalized timestamps, explicit Eastern filing
dates, and relative paths only. Building the same catalog state twice must produce
identical table hashes on any machine.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Final

from disclosure_drift.errors import GateFailureError

__all__ = [
    "NULL_SENTINEL",
    "TableHash",
    "hash_release",
    "hash_table",
    "normalize_value",
]

NULL_SENTINEL: Final = "\x00null"


def normalize_value(value: object) -> str:
    """Render one cell deterministically as text.

    Types are narrowed explicitly so the rendering of every supported cell type is
    visible here rather than delegated to an untyped ``str`` call.
    """
    if value is None:
        return NULL_SENTINEL
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, datetime):
        if value.tzinfo is None:
            message = "naive datetimes may not enter a release; normalize to UTC first"
            raise GateFailureError(message)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return repr(round(value, 12))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.hex()
    message = f"unsupported release cell type {type(value).__name__}"
    raise GateFailureError(message)


@dataclass(frozen=True, slots=True)
class TableHash:
    """Normalized content hash for one release table."""

    table_name: str
    columns: tuple[str, ...]
    row_count: int
    normalized_content_sha256: str


def hash_table(
    table_name: str,
    columns: Sequence[str],
    rows: Iterable[Mapping[str, object]],
) -> TableHash:
    """Hash a table's content with stable column and row order."""
    ordered_columns = tuple(columns)
    rendered = [
        "\x1f".join(normalize_value(row.get(column)) for column in ordered_columns) for row in rows
    ]
    rendered.sort()
    digest = hashlib.sha256()
    digest.update(table_name.encode("utf-8"))
    digest.update(b"\x1e")
    digest.update("\x1f".join(ordered_columns).encode("utf-8"))
    for line in rendered:
        digest.update(b"\x1e")
        digest.update(line.encode("utf-8"))
    return TableHash(
        table_name=table_name,
        columns=ordered_columns,
        row_count=len(rendered),
        normalized_content_sha256=digest.hexdigest(),
    )


def hash_release(table_hashes: Iterable[TableHash]) -> str:
    """Combine table hashes into one release-level content hash."""
    ordered = sorted(table_hashes, key=lambda item: item.table_name)
    payload = json.dumps(
        [
            {
                "table": item.table_name,
                "rows": item.row_count,
                "sha256": item.normalized_content_sha256,
            }
            for item in ordered
        ],
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
