"""Parser for the official SEC quarterly company index (``company.idx``).

The index is a fixed-width text listing of company name, form type, CIK, date filed,
and a file-name column. It is registered as a **coverage-reconciliation** source: it
tells the census which accessions the SEC lists for a quarter, so submissions-derived
coverage can be checked against it.

Boundaries enforced here:

* the file-name column is parsed as *metadata only*. The accession number is extracted
  from its text, and **no URL is ever constructed** from it. Stage M2.2 retrieves no
  accession index page, primary document, complete-submission file, or XBRL package;
* malformed lines are retained as parsed evidence, never skipped;
* duplicate rows are retained, never deduplicated;
* a structurally valid index with zero data rows is a genuine zero, distinguished from
  a truncated, unreadable, or header-only-with-no-separator file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik
from disclosure_drift.sec.parsers.base import (
    ParsedRecord,
    ParseOutcome,
    QuarantinedRecord,
    RecordLocation,
    StructuralObservation,
    StructuralState,
    count_duplicates,
)

__all__ = [
    "FULL_INDEX_PARSER_ID",
    "FULL_INDEX_PARSER_VERSION",
    "INDEX_ROW_PREFIX",
    "REGION_INDEX_ROWS",
    "IndexRow",
    "parse_company_index",
]

FULL_INDEX_PARSER_ID: Final = "company-idx"
FULL_INDEX_PARSER_VERSION: Final = "company-idx/1.0"
REGION_INDEX_ROWS: Final = "company_index.rows"

#: The native-identity prefix this parser stamps on every data row. Stated once here, where
#: the identity is built, so the readers that select index rows by it cannot drift from it.
INDEX_ROW_PREFIX: Final = "index_row:"

_SEPARATOR: Final = re.compile(r"^-{10,}\s*$")
_HEADER: Final = re.compile(r"company\s+name.*form\s+type.*cik", re.IGNORECASE)
_ACCESSION: Final = re.compile(r"(\d{10})-?(\d{2})-?(\d{6})")
_DATE: Final = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MIN_FIELDS: Final = 4


@dataclass(frozen=True, slots=True)
class IndexRow:
    """One parsed index row, retaining the source-native text."""

    company_name: str
    form_type: str
    cik_padded: str | None
    date_filed: str | None
    accession_plain: str | None
    raw_line: str
    line_number: int
    problems: tuple[str, ...] = ()

    @property
    def is_usable(self) -> bool:
        """Whether this row may take part in reconciliation."""
        return not self.problems and self.accession_plain is not None


def parse_company_index(text: str, location: RecordLocation) -> ParseOutcome:
    """Parse one preserved ``company.idx`` snapshot.

    Args:
        text: Preserved index bytes decoded as text.
        location: Source observation the index came from.

    Returns:
        A parse outcome with one record per data row, malformed rows both recorded and
        quarantined, duplicates retained, and an explicit structural verdict so a
        genuinely empty quarter is distinguishable from an unreadable file.
    """
    lines = text.splitlines()
    separator_at: int | None = None
    header_seen = False
    for index, line in enumerate(lines):
        if _HEADER.search(line):
            header_seen = True
        if _SEPARATOR.match(line):
            separator_at = index
            break

    if separator_at is None:
        return _unreadable(
            text,
            location,
            "wrong_type" if lines else "absent",
            (
                "no dashed separator line was found, so the fixed-width data section "
                "could not be located; the row count is unknown"
            ),
        )

    records: list[ParsedRecord] = []
    quarantined: list[QuarantinedRecord] = []
    rows: list[IndexRow] = []
    for offset, raw in enumerate(lines[separator_at + 1 :], start=separator_at + 2):
        if not raw.strip():
            continue
        row = _parse_row(raw, offset)
        rows.append(row)
        row_location = RecordLocation(
            observation_id=location.observation_id,
            source_id=location.source_id,
            record_path=REGION_INDEX_ROWS,
            record_index=offset,
        )
        records.append(
            ParsedRecord(
                native_identity=(f"{INDEX_ROW_PREFIX}{row.accession_plain or 'unparsed'}:{offset}"),
                payload={
                    "company_name": row.company_name,
                    "form_type": row.form_type,
                    "cik_padded": row.cik_padded,
                    "date_filed": row.date_filed,
                    "accession_plain": row.accession_plain,
                    "raw_line": row.raw_line,
                    "line_number": row.line_number,
                    "problems": list(row.problems),
                },
                location=row_location,
                parser_id=FULL_INDEX_PARSER_ID,
                parser_version=FULL_INDEX_PARSER_VERSION,
                normalization_warnings=row.problems,
            )
        )
        if row.problems:
            quarantined.append(
                QuarantinedRecord(
                    location=row_location,
                    parser_id=FULL_INDEX_PARSER_ID,
                    parser_version=FULL_INDEX_PARSER_VERSION,
                    reason_codes=("SEC_RESPONSE_MALFORMED",),
                    detail="; ".join(row.problems),
                    raw_excerpt=raw[:300],
                )
            )

    usable = [row for row in rows if row.is_usable]
    state: StructuralState = "valid_empty" if not rows else "valid_present"
    if rows and not usable:
        state = "malformed"
    detail = (
        f"{len(rows)} data rows parsed, {len(usable)} usable, "
        f"{len(rows) - len(usable)} malformed and retained"
        if rows
        else (
            "the index declares its header and separator and lists no filings; zero rows "
            "is a genuine observation for this quarter"
        )
    )
    return ParseOutcome(
        parser_id=FULL_INDEX_PARSER_ID,
        parser_version=FULL_INDEX_PARSER_VERSION,
        records=tuple(records),
        quarantined=tuple(quarantined),
        duplicate_identities=count_duplicates(
            [row.accession_plain for row in usable if row.accession_plain]
        ),
        normalization_warnings=(
            () if header_seen else ("no recognizable header row preceded the separator",)
        ),
        structural=(
            StructuralObservation(
                region=REGION_INDEX_ROWS,
                state=state,
                observed_type="text",
                location=RecordLocation(
                    observation_id=location.observation_id,
                    source_id=location.source_id,
                    record_path=REGION_INDEX_ROWS,
                ),
                row_count=len(rows),
                detail=detail,
                raw_excerpt=text[:500],
            ),
        ),
    )


def _parse_row(raw: str, line_number: int) -> IndexRow:
    """Split one fixed-width row, recording every problem rather than discarding it."""
    problems: list[str] = []
    fields = raw.split()
    if len(fields) < _MIN_FIELDS:
        return IndexRow(
            company_name=raw.strip(),
            form_type="",
            cik_padded=None,
            date_filed=None,
            accession_plain=None,
            raw_line=raw,
            line_number=line_number,
            problems=(f"row has {len(fields)} whitespace-separated fields, need at least 4",),
        )

    date_index = next((i for i, item in enumerate(fields) if _DATE.match(item)), None)
    if date_index is None or date_index < 3:
        problems.append("no ISO date-filed column was found in the expected position")
        date_filed = None
        cik_text = None
        form_type = ""
        company = raw.strip()
    else:
        date_filed = fields[date_index]
        cik_text = fields[date_index - 1]
        form_type = fields[date_index - 2]
        company = " ".join(fields[: date_index - 2]).strip()

    cik_padded: str | None = None
    if cik_text is not None:
        try:
            cik_padded = normalize_cik(cik_text)[1]
        except IdentifierError as exc:
            problems.append(f"CIK {cik_text!r} is not usable: {exc}")

    # The file-name column is read as text only. The accession number is extracted from
    # it as metadata; no URL is built, and no link is followed.
    match = _ACCESSION.search(fields[-1]) if fields else None
    accession = None
    if match is None:
        problems.append("no accession number could be read from the file-name column")
    else:
        accession = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    if not form_type:
        problems.append("no form type could be read")

    return IndexRow(
        company_name=company,
        form_type=form_type,
        cik_padded=cik_padded,
        date_filed=date_filed,
        accession_plain=accession,
        raw_line=raw,
        line_number=line_number,
        problems=tuple(problems),
    )


def _unreadable(
    text: str,
    location: RecordLocation,
    state: StructuralState,
    detail: str,
) -> ParseOutcome:
    """Return an outcome for an index whose data section could not be located."""
    return ParseOutcome(
        parser_id=FULL_INDEX_PARSER_ID,
        parser_version=FULL_INDEX_PARSER_VERSION,
        quarantined=(
            QuarantinedRecord(
                location=location,
                parser_id=FULL_INDEX_PARSER_ID,
                parser_version=FULL_INDEX_PARSER_VERSION,
                reason_codes=("SEC_RESPONSE_MALFORMED",),
                detail=detail,
                raw_excerpt=text[:500],
            ),
        ),
        structural=(
            StructuralObservation(
                region=REGION_INDEX_ROWS,
                state=state,
                observed_type="text",
                location=RecordLocation(
                    observation_id=location.observation_id,
                    source_id=location.source_id,
                    record_path=REGION_INDEX_ROWS,
                ),
                detail=detail,
                raw_excerpt=text[:500],
            ),
        ),
    )
