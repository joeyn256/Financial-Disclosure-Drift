"""Parsers for the official SEC ticker and exchange alias files.

Two shapes are handled, each declared explicitly:

* ``company_tickers.json`` — an object keyed by an opaque row index, each value
  carrying ``cik_str``, ``ticker``, and ``title``;
* ``company_tickers_exchange.json`` — a ``fields`` header plus a ``data`` matrix,
  parsed by looking up column positions **by name** rather than by fixed index, so a
  reordered or extended header does not silently shift values.

Both files are alias evidence for a CIK and nothing more. A shared ticker, name, or
exchange across two CIKs is recorded as candidate evidence for review; it never
merges identities, and neither file defines the study universe.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik
from disclosure_drift.sec.parsers.base import (
    ParsedRecord,
    ParseOutcome,
    QuarantinedRecord,
    RecordLocation,
    count_duplicates,
)

__all__ = [
    "EXCHANGE_PARSER_ID",
    "EXCHANGE_PARSER_VERSION",
    "TICKER_PARSER_ID",
    "TICKER_PARSER_VERSION",
    "candidate_shared_alias_edges",
    "parse_company_tickers",
    "parse_company_tickers_exchange",
]

TICKER_PARSER_ID: Final = "company-tickers"
TICKER_PARSER_VERSION: Final = "company-tickers/1.0"
EXCHANGE_PARSER_ID: Final = "company-tickers-exchange"
EXCHANGE_PARSER_VERSION: Final = "company-tickers-exchange/1.0"

_TICKER_FIELDS: Final[tuple[str, ...]] = ("cik_str", "ticker", "title")
_EXCHANGE_REQUIRED_COLUMNS: Final[tuple[str, ...]] = ("cik", "name", "ticker", "exchange")


def parse_company_tickers(
    payload: Mapping[str, Any],
    location: RecordLocation,
) -> ParseOutcome:
    """Parse ``company_tickers.json`` into parsed source records."""
    records: list[ParsedRecord] = []
    quarantined: list[QuarantinedRecord] = []
    unknown: set[str] = set()

    for index, (key, entry) in enumerate(sorted(payload.items(), key=lambda item: item[0])):
        row_location = RecordLocation(
            observation_id=location.observation_id,
            source_id=location.source_id,
            record_path=str(key),
            record_index=index,
        )
        if not isinstance(entry, dict):
            quarantined.append(
                _reject(
                    row_location,
                    TICKER_PARSER_ID,
                    TICKER_PARSER_VERSION,
                    f"row {key!r} is {type(entry).__name__}, not an object",
                    entry,
                )
            )
            continue
        unknown.update(set(entry) - set(_TICKER_FIELDS))
        cik_padded, problem = _padded_cik(entry.get("cik_str"))
        ticker = _text(entry.get("ticker"))
        if problem or not ticker:
            quarantined.append(
                _reject(
                    row_location,
                    TICKER_PARSER_ID,
                    TICKER_PARSER_VERSION,
                    problem or "row carries no ticker",
                    entry,
                )
            )
            continue
        records.append(
            ParsedRecord(
                native_identity=f"ticker_alias:{cik_padded}:{ticker}",
                payload=dict(entry),
                location=row_location,
                parser_id=TICKER_PARSER_ID,
                parser_version=TICKER_PARSER_VERSION,
                unknown_fields=tuple(sorted(set(entry) - set(_TICKER_FIELDS))),
            )
        )

    return ParseOutcome(
        parser_id=TICKER_PARSER_ID,
        parser_version=TICKER_PARSER_VERSION,
        records=tuple(records),
        quarantined=tuple(quarantined),
        duplicate_identities=count_duplicates([item.native_identity for item in records]),
        unknown_fields=tuple(sorted(unknown)),
    )


def parse_company_tickers_exchange(
    payload: Mapping[str, Any],
    location: RecordLocation,
) -> ParseOutcome:
    """Parse ``company_tickers_exchange.json`` into parsed source records.

    Column positions are resolved from the ``fields`` header by name. A missing
    required column fails the whole document rather than guessing positions.
    """
    fields = payload.get("fields")
    data = payload.get("data")
    if not isinstance(fields, list) or not isinstance(data, list):
        return ParseOutcome(
            parser_id=EXCHANGE_PARSER_ID,
            parser_version=EXCHANGE_PARSER_VERSION,
            quarantined=(
                _reject(
                    location,
                    EXCHANGE_PARSER_ID,
                    EXCHANGE_PARSER_VERSION,
                    "document does not carry a 'fields' header and a 'data' matrix",
                    payload,
                ),
            ),
            required_field_failures=(("fields/data", "header or matrix absent"),),
        )

    header = [str(name) for name in fields]
    positions = {name: header.index(name) for name in header}
    missing = [name for name in _EXCHANGE_REQUIRED_COLUMNS if name not in positions]
    if missing:
        return ParseOutcome(
            parser_id=EXCHANGE_PARSER_ID,
            parser_version=EXCHANGE_PARSER_VERSION,
            quarantined=(
                _reject(
                    location,
                    EXCHANGE_PARSER_ID,
                    EXCHANGE_PARSER_VERSION,
                    f"header {header} is missing required column(s) {missing}; column "
                    "positions are never guessed",
                    payload,
                ),
            ),
            required_field_failures=tuple(
                (name, "required column absent from the header") for name in missing
            ),
        )

    unknown = tuple(sorted(set(header) - set(_EXCHANGE_REQUIRED_COLUMNS)))
    records: list[ParsedRecord] = []
    quarantined: list[QuarantinedRecord] = []
    warnings: list[str] = []

    for index, row in enumerate(data):
        row_location = RecordLocation(
            observation_id=location.observation_id,
            source_id=location.source_id,
            record_path="data",
            record_index=index,
        )
        if not isinstance(row, list):
            quarantined.append(
                _reject(
                    row_location,
                    EXCHANGE_PARSER_ID,
                    EXCHANGE_PARSER_VERSION,
                    f"row is {type(row).__name__}, not a list",
                    row,
                )
            )
            continue
        if len(row) != len(header):
            quarantined.append(
                _reject(
                    row_location,
                    EXCHANGE_PARSER_ID,
                    EXCHANGE_PARSER_VERSION,
                    f"row has {len(row)} values but the header declares {len(header)}",
                    row,
                )
            )
            continue
        native = {name: row[positions[name]] for name in header}
        cik_padded, problem = _padded_cik(native.get("cik"))
        ticker = _text(native.get("ticker"))
        if problem:
            quarantined.append(
                _reject(
                    row_location,
                    EXCHANGE_PARSER_ID,
                    EXCHANGE_PARSER_VERSION,
                    problem,
                    native,
                )
            )
            continue
        if not _text(native.get("exchange")):
            warnings.append(
                f"row {index} for CIK {cik_padded} carries no exchange; the null is retained "
                "and no exchange is inferred"
            )
        records.append(
            ParsedRecord(
                native_identity=f"exchange_alias:{cik_padded}:{ticker or ''}",
                payload=native,
                location=row_location,
                parser_id=EXCHANGE_PARSER_ID,
                parser_version=EXCHANGE_PARSER_VERSION,
                unknown_fields=unknown,
            )
        )

    return ParseOutcome(
        parser_id=EXCHANGE_PARSER_ID,
        parser_version=EXCHANGE_PARSER_VERSION,
        records=tuple(records),
        quarantined=tuple(quarantined),
        duplicate_identities=count_duplicates([item.native_identity for item in records]),
        unknown_fields=unknown,
        normalization_warnings=tuple(warnings),
    )


def candidate_shared_alias_edges(
    outcome: ParseOutcome,
    *,
    alias_field: str = "ticker",
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return aliases claimed by more than one CIK, as review candidates only.

    Two CIKs sharing a ticker, a name, or an exchange are **not** the same registrant.
    This function exists so such agreement is surfaced for review; nothing in the
    census may use its output to merge CIK identities.
    """
    by_alias: dict[str, set[str]] = {}
    for record in outcome.records:
        alias = _text(record.payload.get(alias_field))
        cik = _text(record.payload.get("cik")) or _text(record.payload.get("cik_str"))
        if not alias or not cik:
            continue
        padded, problem = _padded_cik(cik)
        if problem or padded is None:
            continue
        by_alias.setdefault(alias, set()).add(padded)
    return tuple(
        (alias, tuple(sorted(ciks))) for alias, ciks in sorted(by_alias.items()) if len(ciks) > 1
    )


def _padded_cik(value: object) -> tuple[str | None, str | None]:
    """Return the zero-padded CIK, or a message explaining why it is unusable.

    The raw row is preserved on the parsed or quarantined record either way.
    """
    if value is None:
        return None, "row carries no CIK"
    try:
        return normalize_cik(str(value))[1], None
    except IdentifierError as exc:
        return None, f"CIK {value!r} is not usable: {exc}"


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _reject(
    location: RecordLocation,
    parser_id: str,
    parser_version: str,
    detail: str,
    payload: object,
) -> QuarantinedRecord:
    return QuarantinedRecord(
        location=location,
        parser_id=parser_id,
        parser_version=parser_version,
        reason_codes=("SEC_RESPONSE_MALFORMED",),
        detail=detail,
        raw_excerpt=_excerpt(payload),
    )


def _excerpt(payload: object, limit: int = 300) -> str:
    text = repr(payload)
    return text if len(text) <= limit else text[:limit] + "…"
