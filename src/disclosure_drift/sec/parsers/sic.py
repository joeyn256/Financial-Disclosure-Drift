"""Parser for the official SEC Standard Industrial Classification HTML table."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Final

from disclosure_drift.sec.parsers.base import (
    ParsedRecord,
    ParseOutcome,
    QuarantinedRecord,
    RecordLocation,
    count_duplicates,
)

__all__ = ["PARSER_ID", "PARSER_VERSION", "parse_sic_reference"]

PARSER_ID: Final = "sic-code-list"
PARSER_VERSION: Final = "sic-code-list/1.0"
_SIC: Final = re.compile(r"^[0-9]{4}$")


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() == "tr":
            self._row = []
        elif tag.lower() in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif lowered == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


def parse_sic_reference(html: str, location: RecordLocation) -> ParseOutcome:
    """Parse SIC rows by their four-digit code, preserving all source cells."""
    parser = _TableParser()
    parser.feed(html)
    positions = _header_positions(parser.rows)
    records: list[ParsedRecord] = []
    quarantined: list[QuarantinedRecord] = []
    for index, cells in enumerate(parser.rows):
        code_index = positions.get("sic")
        if code_index is None or code_index >= len(cells) or not _SIC.fullmatch(cells[code_index]):
            code_index = next((i for i, cell in enumerate(cells) if _SIC.fullmatch(cell)), None)
        if code_index is None:
            continue
        row_location = RecordLocation(
            observation_id=location.observation_id,
            source_id=location.source_id,
            record_path="table.tr",
            record_index=index,
        )
        code = cells[code_index]
        description_index = positions.get("description")
        office_index = positions.get("office")
        description = (
            cells[description_index]
            if description_index is not None and description_index < len(cells)
            else cells[-1]
            if len(cells) > 1
            else ""
        )
        office = (
            cells[office_index]
            if office_index is not None and office_index < len(cells)
            else next(
                (
                    cell
                    for index, cell in enumerate(cells)
                    if index not in {code_index, len(cells) - 1}
                ),
                None,
            )
        )
        if not description:
            quarantined.append(
                QuarantinedRecord(
                    location=row_location,
                    parser_id=PARSER_ID,
                    parser_version=PARSER_VERSION,
                    reason_codes=("SEC_SCHEMA_REQUIRED_FIELD_MISSING",),
                    detail=f"SIC {code} has no description",
                    raw_excerpt=repr(cells),
                    native_identity=f"sic:{code}",
                )
            )
            continue
        records.append(
            ParsedRecord(
                native_identity=f"sic:{code}",
                payload={
                    "sic": code,
                    "description": description,
                    "office": office,
                    "source_cells": cells,
                    "financial_sector_6000_6999": 6000 <= int(code) <= 6999,
                },
                location=row_location,
                parser_id=PARSER_ID,
                parser_version=PARSER_VERSION,
            )
        )
    if not records and not quarantined:
        quarantined.append(
            QuarantinedRecord(
                location=location,
                parser_id=PARSER_ID,
                parser_version=PARSER_VERSION,
                reason_codes=("SEC_RESPONSE_MALFORMED",),
                detail="official SIC HTML contained no recognizable four-digit SIC rows",
                raw_excerpt=html[:500],
            )
        )
    return ParseOutcome(
        parser_id=PARSER_ID,
        parser_version=PARSER_VERSION,
        records=tuple(records),
        quarantined=tuple(quarantined),
        duplicate_identities=count_duplicates([record.native_identity for record in records]),
    )


def _header_positions(rows: list[list[str]]) -> dict[str, int]:
    for cells in rows:
        normalized = [cell.casefold().replace("_", " ").strip() for cell in cells]
        sic = next((index for index, cell in enumerate(normalized) if "sic" in cell), None)
        description = next(
            (
                index
                for index, cell in enumerate(normalized)
                if "industry" in cell or "title" in cell or "description" in cell
            ),
            None,
        )
        office = next(
            (index for index, cell in enumerate(normalized) if "office" in cell),
            None,
        )
        if sic is not None and description is not None:
            result = {"sic": sic, "description": description}
            if office is not None:
                result["office"] = office
            return result
    return {}
