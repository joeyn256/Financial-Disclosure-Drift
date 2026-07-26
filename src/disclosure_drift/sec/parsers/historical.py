"""Parser for SEC historical submissions overflow documents."""

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
from disclosure_drift.sec.parsers.submissions import ACCESSION_ARRAY_FIELDS

__all__ = ["PARSER_ID", "PARSER_VERSION", "parse_historical_submissions"]

PARSER_ID: Final = "submissions-historical"
PARSER_VERSION: Final = "submissions-historical/1.0"
_REQUIRED: Final[tuple[str, ...]] = ("accessionNumber", "filingDate", "form")


def parse_historical_submissions(
    payload: Mapping[str, Any],
    location: RecordLocation,
    *,
    registrant_cik: str | int,
) -> ParseOutcome:
    """Expand one historical document's parallel arrays without truncation."""
    try:
        cik_padded = normalize_cik(registrant_cik)[1]
    except IdentifierError as exc:
        return _document_failure(location, f"historical reference has invalid CIK: {exc}", payload)

    columns = {name: value for name, value in payload.items() if isinstance(value, list)}
    missing = tuple(name for name in _REQUIRED if name not in columns)
    if missing:
        return ParseOutcome(
            parser_id=PARSER_ID,
            parser_version=PARSER_VERSION,
            quarantined=(
                _quarantine(
                    location,
                    f"historical document is missing required array(s) {list(missing)}",
                    payload,
                    f"registrant:{cik_padded}",
                ),
            ),
            required_field_failures=tuple(
                (name, "required historical accession array is absent") for name in missing
            ),
            unknown_fields=tuple(sorted(set(payload) - set(ACCESSION_ARRAY_FIELDS))),
        )

    lengths = {name: len(values) for name, values in columns.items()}
    if len(set(lengths.values())) > 1:
        return _document_failure(
            location,
            f"historical parallel arrays disagree in length ({sorted(lengths.items())})",
            payload,
            native_identity=f"registrant:{cik_padded}",
        )

    unknown = tuple(sorted(set(payload) - set(ACCESSION_ARRAY_FIELDS)))
    records: list[ParsedRecord] = []
    quarantined: list[QuarantinedRecord] = []
    total = next(iter(lengths.values()), 0)
    for index in range(total):
        row = {name: values[index] for name, values in columns.items()}
        accession = _text(row.get("accessionNumber"))
        row_location = RecordLocation(
            observation_id=location.observation_id,
            source_id=location.source_id,
            member_name=location.member_name,
            record_path="historical",
            record_index=index,
        )
        absent = [name for name in _REQUIRED if not _text(row.get(name))]
        if absent:
            quarantined.append(
                _quarantine(
                    row_location,
                    f"historical accession is missing required field(s) {absent}",
                    row,
                    accession,
                )
            )
            continue
        native = dict(row)
        native["cik"] = cik_padded
        records.append(
            ParsedRecord(
                native_identity=f"accession:{accession}",
                payload=native,
                location=row_location,
                parser_id=PARSER_ID,
                parser_version=PARSER_VERSION,
                unknown_fields=unknown,
            )
        )

    return ParseOutcome(
        parser_id=PARSER_ID,
        parser_version=PARSER_VERSION,
        records=tuple(records),
        quarantined=tuple(quarantined),
        duplicate_identities=count_duplicates([record.native_identity for record in records]),
        unknown_fields=unknown,
    )


def _document_failure(
    location: RecordLocation,
    detail: str,
    payload: Mapping[str, Any],
    native_identity: str | None = None,
) -> ParseOutcome:
    return ParseOutcome(
        parser_id=PARSER_ID,
        parser_version=PARSER_VERSION,
        quarantined=(_quarantine(location, detail, payload, native_identity),),
        required_field_failures=(("parallel_arrays", detail),),
    )


def _quarantine(
    location: RecordLocation,
    detail: str,
    payload: object,
    native_identity: str | None,
) -> QuarantinedRecord:
    excerpt = repr(payload)
    return QuarantinedRecord(
        location=location,
        parser_id=PARSER_ID,
        parser_version=PARSER_VERSION,
        reason_codes=("SEC_SCHEMA_REQUIRED_FIELD_MISSING",),
        detail=detail,
        raw_excerpt=excerpt if len(excerpt) <= 500 else excerpt[:500] + "…",
        native_identity=native_identity,
    )


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
