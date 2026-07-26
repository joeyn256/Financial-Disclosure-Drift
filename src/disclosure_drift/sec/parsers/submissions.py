"""Parser for official SEC submissions documents (bulk members and entity files).

One submissions document describes one CIK: its current name, former names, tickers,
exchanges, SIC, fiscal year end, and its accession-level filing metadata, plus
references to historical overflow files holding older accessions.

What this parser does:

* declares its expected shape explicitly and reports drift instead of assuming it;
* keeps every source-native field name and value on the parsed record;
* retains unknown fields, including nested dotted paths, rather than narrowing;
* expands ``filings.recent`` parallel arrays into one record per accession, refusing
  the document when the arrays disagree in length rather than truncating to the
  shortest;
* records ``filings.files`` historical references as *references only* — nothing is
  retrieved here, and a malformed entry is preserved rather than skipped;
* quarantines a malformed accession record and keeps parsing the rest;
* never constructs a filing-body, primary-document, or accession-index URL;
* never merges CIKs. A shared ticker, name, or exchange is candidate evidence for
  review, never an identity decision.

**Zero is never inferred.** Every nested region carries an explicit
:class:`~disclosure_drift.sec.parsers.base.StructuralObservation`, so these cases stay
distinguishable rather than all collapsing to "no accessions":

===============================  =================  =======================
Observed shape                   Structural state   Count meaning
===============================  =================  =======================
``filings.recent`` present, rows  ``valid_present``  real count
``filings.recent`` present, no rows ``valid_empty``  real zero
``filings`` key absent            ``absent``         unknown
``recent`` key absent             ``absent``         unknown
``recent`` is ``null``            ``null``           unknown
``recent`` is a list or scalar    ``wrong_type``     unknown
columns of differing length       ``malformed``      unknown
===============================  =================  =======================

Only the first two permit a record count to be believed. Every other state carries a
release-blocking reason code, retains the raw payload and the exact field location,
and therefore prevents required-source success and census completion.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

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
from disclosure_drift.sec.schema_drift import DriftReport, inspect_payload

__all__ = [
    "ACCESSION_ARRAY_FIELDS",
    "HISTORICAL_FILE_NAME_PATTERN",
    "PARSER_ID",
    "PARSER_VERSION",
    "REGION_FILES",
    "REGION_FILINGS",
    "REGION_RECENT",
    "HistoricalFileReference",
    "parse_submissions_document",
]

PARSER_ID: Final = "submissions-json"
PARSER_VERSION: Final = "submissions-json/1.1"

REGION_FILINGS: Final = "filings"
REGION_RECENT: Final = "filings.recent"
REGION_FILES: Final = "filings.files"

HISTORICAL_FILE_NAME_PATTERN: Final = re.compile(r"^CIK[0-9]{10}-submissions-[0-9]{3}\.json$")
"""The only shape a historical submissions reference name may take.

A name outside this shape is preserved as evidence and refused for retrieval, so a
reference can never be turned into an arbitrary URL.
"""

_FILINGS_KNOWN_KEYS: Final[frozenset[str]] = frozenset({"recent", "files"})
_HISTORICAL_KNOWN_KEYS: Final[frozenset[str]] = frozenset(
    {"name", "filingCount", "filingFrom", "filingTo"}
)
_FORMER_NAME_KNOWN_KEYS: Final[frozenset[str]] = frozenset({"name", "from", "to"})
_ADDRESS_KNOWN_KEYS: Final[frozenset[str]] = frozenset(
    {
        "street1",
        "street2",
        "city",
        "stateOrCountry",
        "zipCode",
        "stateOrCountryDescription",
        "isForeignLocation",
        "foreignStateTerritory",
        "country",
        "countryCode",
    }
)
_ADDRESS_KINDS: Final[frozenset[str]] = frozenset({"mailing", "business"})
_FLAG_KNOWN_KEYS: Final[frozenset[str]] = frozenset()

_REQUIRED_TOP_LEVEL: Final[Mapping[str, type | tuple[type, ...]]] = {
    "cik": (str, int),
    "name": str,
    "filings": dict,
}
_OPTIONAL_TOP_LEVEL: Final[tuple[str, ...]] = (
    "entityType",
    "sic",
    "sicDescription",
    "ein",
    "description",
    "website",
    "investorWebsite",
    "category",
    "fiscalYearEnd",
    "stateOfIncorporation",
    "stateOfIncorporationDescription",
    "phone",
    "addresses",
    "flags",
    "insiderTransactionForOwnerExists",
    "insiderTransactionForIssuerExists",
    "ownerOrg",
)
_ARRAY_TOP_LEVEL: Final[tuple[str, ...]] = ("tickers", "exchanges", "formerNames")

ACCESSION_ARRAY_FIELDS: Final[tuple[str, ...]] = (
    "accessionNumber",
    "filingDate",
    "reportDate",
    "acceptanceDateTime",
    "act",
    "form",
    "fileNumber",
    "filmNumber",
    "items",
    "size",
    "isXBRL",
    "isInlineXBRL",
    "primaryDocument",
    "primaryDocDescription",
)
"""Parallel arrays expected inside ``filings.recent``.

``primaryDocument`` is retained as metadata. It is never turned into a URL: Stage
M2.2 retrieves no primary document.
"""

_REQUIRED_ACCESSION_FIELDS: Final[tuple[str, ...]] = (
    "accessionNumber",
    "filingDate",
    "form",
)


@dataclass(frozen=True, slots=True)
class HistoricalFileReference:
    """One ``filings.files`` reference, recorded but not retrieved.

    A malformed entry is still represented here so that it is preserved as source
    evidence. ``is_retrievable`` is the only gate the orchestrator may use: an entry
    with an unusable name or unusable metadata is never queued for retrieval, and
    ``problems`` explains why.
    """

    name: str | None
    filing_count: int | None
    filing_from: str | None
    filing_to: str | None
    location: RecordLocation
    problems: tuple[str, ...] = ()
    raw_entry: Mapping[str, Any] | None = None
    unknown_fields: tuple[str, ...] = ()

    @property
    def is_retrievable(self) -> bool:
        """Whether this reference may be queued for a controlled retrieval."""
        return self.name is not None and not self.problems

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence."""
        return {
            "name": self.name,
            "filing_count": self.filing_count,
            "filing_from": self.filing_from,
            "filing_to": self.filing_to,
            "location": dict(self.location.as_record()),
            "problems": list(self.problems),
            "unknown_fields": list(self.unknown_fields),
            "is_retrievable": self.is_retrievable,
            "raw_entry": None if self.raw_entry is None else dict(self.raw_entry),
            "retrieved": False,
        }


def _regions_when_document_unusable(
    payload: Mapping[str, Any],
    location: RecordLocation,
    why: str,
) -> tuple[StructuralObservation, ...]:
    """Classify the nested regions when the enclosing document is itself unusable.

    Without this, a document that fails top-level validation would carry no structural
    verdict at all, and a consumer checking whether counts may be believed would be
    told "yes" about a document nothing could be counted from. Every region therefore
    resolves to a concrete state here: the real shape where it can be determined, and
    ``indeterminate`` where the enclosing failure makes it unknowable.
    """
    verdicts: list[StructuralObservation] = []
    filings, verdict = _classify_region(
        payload, "filings", REGION_FILINGS, location, dict, "object"
    )
    if verdict is not None:
        verdicts.append(verdict)
    else:
        verdicts.append(
            _structural(
                location,
                REGION_FILINGS,
                "indeterminate",
                filings,
                f"filings is present but the enclosing document is unusable: {why}",
            )
        )
    for region in (REGION_RECENT, REGION_FILES):
        verdicts.append(
            _structural(
                location,
                region,
                "indeterminate",
                payload.get("filings"),
                f"{region} could not be evaluated because the document is unusable: {why}",
            )
        )
    return tuple(verdicts)


def parse_submissions_document(
    payload: Mapping[str, Any],
    location: RecordLocation,
) -> tuple[ParseOutcome, tuple[HistoricalFileReference, ...]]:
    """Parse one submissions document into parsed source records.

    Returns:
        The parse outcome, whose records are one registrant record followed by one
        record per accession, and the historical-file references the document names.
        References are returned for the orchestrator to decide about; this parser
        performs no retrieval.
    """
    drift = inspect_payload(
        payload,
        source_class="sec_submissions_document",
        required_fields=_REQUIRED_TOP_LEVEL,
        optional_fields=_OPTIONAL_TOP_LEVEL,
        array_fields=_ARRAY_TOP_LEVEL,
    )
    failures = tuple((event.field_path, event.detail) for event in drift.blocking_events)
    if failures:
        rendered = "; ".join(f"{name}: {why}" for name, why in failures)
        return (
            ParseOutcome(
                parser_id=PARSER_ID,
                parser_version=PARSER_VERSION,
                quarantined=(
                    QuarantinedRecord(
                        location=location,
                        parser_id=PARSER_ID,
                        parser_version=PARSER_VERSION,
                        reason_codes=("SEC_SCHEMA_REQUIRED_FIELD_MISSING",),
                        detail=f"submissions document is unusable: {rendered}",
                        raw_excerpt=_excerpt(payload),
                    ),
                ),
                required_field_failures=failures,
                unknown_fields=drift.retained_unknown_fields,
                drift_reports=(drift,),
                structural=_regions_when_document_unusable(payload, location, rendered),
            ),
            (),
        )

    warnings: list[str] = []
    cik_padded = _normalized_cik(payload.get("cik"), warnings)
    if cik_padded is None or not str(payload.get("name") or "").strip():
        identity_failures: list[tuple[str, str]] = []
        if cik_padded is None:
            identity_failures.append(("cik", "CIK is not canonically usable"))
        if not str(payload.get("name") or "").strip():
            identity_failures.append(("name", "registrant name is empty"))
        return (
            ParseOutcome(
                parser_id=PARSER_ID,
                parser_version=PARSER_VERSION,
                quarantined=(
                    QuarantinedRecord(
                        location=location,
                        parser_id=PARSER_ID,
                        parser_version=PARSER_VERSION,
                        reason_codes=("SEC_SCHEMA_REQUIRED_FIELD_MISSING",),
                        detail="; ".join(
                            f"{field}: {detail}" for field, detail in identity_failures
                        ),
                        raw_excerpt=_excerpt(payload),
                    ),
                ),
                required_field_failures=tuple(identity_failures),
                unknown_fields=drift.retained_unknown_fields,
                normalization_warnings=tuple(warnings),
                drift_reports=(drift,),
                structural=_regions_when_document_unusable(
                    payload,
                    location,
                    "; ".join(f"{field}: {detail}" for field, detail in identity_failures),
                ),
            ),
            (),
        )
    nested_unknown = _nested_unknown_paths(payload)
    all_unknown = tuple(sorted({*drift.retained_unknown_fields, *nested_unknown}))
    registrant = _registrant_record(payload, location, cik_padded, all_unknown, warnings)
    block = _accession_records(payload, location, cik_padded)
    references, reference_rejects, files_structural = _historical_references(payload, location)

    identities = [registrant.native_identity, *[item.native_identity for item in block.records]]
    outcome = ParseOutcome(
        parser_id=PARSER_ID,
        parser_version=PARSER_VERSION,
        records=(registrant, *block.records),
        quarantined=(*block.quarantined, *reference_rejects),
        duplicate_identities=count_duplicates(identities),
        unknown_fields=all_unknown,
        normalization_warnings=tuple(warnings),
        drift_reports=(drift, *block.drift),
        structural=(*block.structural, *files_structural),
    )
    return outcome, references


# --------------------------------------------------------------------------- #
# Registrant
# --------------------------------------------------------------------------- #
def _registrant_record(
    payload: Mapping[str, Any],
    location: RecordLocation,
    cik_padded: str | None,
    unknown_fields: tuple[str, ...],
    warnings: list[str],
) -> ParsedRecord:
    """Build the source-native registrant record.

    Alias fields are copied verbatim. Tickers and exchanges are alias evidence for
    this CIK only: they never link one CIK to another.
    """
    native = dict(payload)
    native.pop("filings", None)
    former = payload.get("formerNames")
    if former is not None and not isinstance(former, list):
        warnings.append("formerNames was not a list; the raw value is retained as-is")
    tickers = _as_list(payload.get("tickers"))
    exchanges = _as_list(payload.get("exchanges"))
    if tickers and exchanges and len(tickers) != len(exchanges):
        warnings.append(
            f"tickers ({len(tickers)}) and exchanges ({len(exchanges)}) differ in length; "
            "pairs are not inferred and both lists are retained"
        )
    return ParsedRecord(
        native_identity=f"registrant:{cik_padded or payload.get('cik')}",
        payload=native,
        location=location,
        parser_id=PARSER_ID,
        parser_version=PARSER_VERSION,
        unknown_fields=unknown_fields,
        normalization_warnings=tuple(warnings),
        reason_codes=(("PARSER_SCHEMA_DRIFT_OBSERVED",) if unknown_fields else ()),
    )


# --------------------------------------------------------------------------- #
# Accessions
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class _AccessionBlock:
    """Result of reading ``filings.recent``, with its structural verdict attached."""

    records: tuple[ParsedRecord, ...]
    quarantined: tuple[QuarantinedRecord, ...]
    drift: tuple[DriftReport, ...]
    structural: tuple[StructuralObservation, ...]


def _region_location(location: RecordLocation, region: str) -> RecordLocation:
    """Return the exact nested location a structural verdict refers to."""
    return RecordLocation(
        observation_id=location.observation_id,
        source_id=location.source_id,
        member_name=location.member_name,
        record_path=region,
    )


def _structural(
    location: RecordLocation,
    region: str,
    state: StructuralState,
    observed: object,
    detail: str,
    row_count: int | None = None,
) -> StructuralObservation:
    """Build one structural verdict, always retaining an excerpt of what was seen."""
    return StructuralObservation(
        region=region,
        state=state,
        observed_type=type(observed).__name__,
        location=_region_location(location, region),
        row_count=row_count,
        detail=detail,
        raw_excerpt=_excerpt_value(observed),
    )


def _classify_region(
    container: Mapping[str, Any],
    key: str,
    region: str,
    location: RecordLocation,
    expected: type | tuple[type, ...],
    expected_name: str,
) -> tuple[Any | None, StructuralObservation | None]:
    """Classify one nested region, returning its value or a blocking verdict.

    Absence, an explicit ``null``, and a wrong type are three different findings and
    are never collapsed into "empty".
    """
    if key not in container:
        return None, _structural(
            location,
            region,
            "absent",
            container,
            f"{region!r} is absent from the document, so its record count is unknown "
            "and must not be read as zero",
        )
    value = container[key]
    if value is None:
        return None, _structural(
            location,
            region,
            "null",
            value,
            f"{region!r} is present but null, which is not an empty {expected_name}",
        )
    if not isinstance(value, expected):
        return None, _structural(
            location,
            region,
            "wrong_type",
            value,
            f"{region!r} is a {type(value).__name__}, not a {expected_name}",
        )
    return value, None


def _accession_records(
    payload: Mapping[str, Any],
    location: RecordLocation,
    cik_padded: str | None,
) -> _AccessionBlock:
    filings, verdict = _classify_region(
        payload, "filings", REGION_FILINGS, location, dict, "object"
    )
    if verdict is not None:
        return _AccessionBlock((), (), (), (verdict,))
    assert filings is not None  # noqa: S101 - narrowed by the verdict guard

    recent, verdict = _classify_region(filings, "recent", REGION_RECENT, location, dict, "object")
    if verdict is not None:
        return _AccessionBlock((), (), (), (verdict,))
    assert recent is not None  # noqa: S101 - narrowed by the verdict guard

    columns = {name: value for name, value in recent.items() if isinstance(value, list)}
    non_list = tuple(sorted(set(recent) - set(columns)))
    if not recent:
        # Present, correctly typed, and carrying no columns at all: a real zero.
        return _AccessionBlock(
            (),
            (),
            (),
            (
                _structural(
                    location,
                    REGION_RECENT,
                    "valid_empty",
                    recent,
                    "filings.recent is present, correctly typed, and empty; zero "
                    "accessions is a genuine observation for this registrant",
                    row_count=0,
                ),
            ),
        )
    drift = inspect_payload(
        recent,
        source_class="sec_submissions_recent",
        required_fields=dict.fromkeys(_REQUIRED_ACCESSION_FIELDS, list),
        array_fields=ACCESSION_ARRAY_FIELDS,
    )
    if drift.blocking_events:
        quarantined = QuarantinedRecord(
            location=_region_location(location, REGION_RECENT),
            parser_id=PARSER_ID,
            parser_version=PARSER_VERSION,
            reason_codes=("SEC_SCHEMA_REQUIRED_FIELD_MISSING",),
            detail=(
                "filings.recent is unusable: "
                + "; ".join(
                    f"{event.field_path}: {event.detail}" for event in drift.blocking_events
                )
            ),
            raw_excerpt=_excerpt(recent),
            native_identity=f"registrant:{cik_padded}",
        )
        return _AccessionBlock(
            (),
            (quarantined,),
            (drift,),
            (
                _structural(
                    location,
                    REGION_RECENT,
                    "malformed",
                    recent,
                    "filings.recent is present but does not declare the required "
                    "parallel columns as lists",
                ),
            ),
        )

    lengths = {name: len(value) for name, value in columns.items()}
    distinct = set(lengths.values())
    if len(distinct) > 1:
        # Truncating to the shortest array would silently drop accessions, so the
        # whole block is quarantined and preserved for review instead.
        quarantined = QuarantinedRecord(
            location=_region_location(location, REGION_RECENT),
            parser_id=PARSER_ID,
            parser_version=PARSER_VERSION,
            reason_codes=("SEC_SCHEMA_REQUIRED_FIELD_MISSING",),
            detail=(
                "filings.recent parallel arrays disagree in length "
                f"({sorted(lengths.items())}); records are not truncated to the shortest"
            ),
            raw_excerpt=_excerpt(recent),
            native_identity=f"registrant:{cik_padded}",
        )
        return _AccessionBlock(
            (),
            (quarantined,),
            (drift,),
            (
                _structural(
                    location,
                    REGION_RECENT,
                    "malformed",
                    recent,
                    "filings.recent parallel columns disagree in length "
                    f"({sorted(lengths.items())}), so the row count is unknown",
                ),
            ),
        )

    total = next(iter(distinct), 0)
    records: list[ParsedRecord] = []
    rejected: list[QuarantinedRecord] = []
    for index in range(total):
        row = {name: values[index] for name, values in columns.items()}
        accession = str(row.get("accessionNumber") or "").strip()
        row_location = RecordLocation(
            observation_id=location.observation_id,
            source_id=location.source_id,
            member_name=location.member_name,
            record_path="filings.recent",
            record_index=index,
        )
        missing = [
            name for name in _REQUIRED_ACCESSION_FIELDS if not str(row.get(name) or "").strip()
        ]
        if missing:
            rejected.append(
                QuarantinedRecord(
                    location=row_location,
                    parser_id=PARSER_ID,
                    parser_version=PARSER_VERSION,
                    reason_codes=("SEC_SCHEMA_REQUIRED_FIELD_MISSING",),
                    detail=(
                        f"accession record is missing required field(s) {missing}; no "
                        "default is applied and the record is preserved for review"
                    ),
                    raw_excerpt=_excerpt(row),
                    native_identity=accession or None,
                )
            )
            continue
        payload_row = dict(row)
        payload_row["cik"] = cik_padded or payload.get("cik")
        records.append(
            ParsedRecord(
                native_identity=f"accession:{accession}",
                payload=payload_row,
                location=row_location,
                parser_id=PARSER_ID,
                parser_version=PARSER_VERSION,
                unknown_fields=tuple(
                    f"filings.recent.{name}"
                    for name in sorted(set(columns) - set(ACCESSION_ARRAY_FIELDS))
                ),
                normalization_warnings=(
                    (f"non-array keys in filings.recent retained: {non_list}",) if non_list else ()
                ),
            )
        )
    structural = _structural(
        location,
        REGION_RECENT,
        "valid_empty" if total == 0 else "valid_present",
        recent,
        (
            "filings.recent declares its columns and carries no rows; zero accessions "
            "is a genuine observation"
            if total == 0
            else f"filings.recent carries {total} consistent parallel rows"
        ),
        row_count=total,
    )
    return _AccessionBlock(tuple(records), tuple(rejected), (drift,), (structural,))


# --------------------------------------------------------------------------- #
# Historical references
# --------------------------------------------------------------------------- #
def _historical_references(
    payload: Mapping[str, Any],
    location: RecordLocation,
) -> tuple[
    tuple[HistoricalFileReference, ...],
    tuple[QuarantinedRecord, ...],
    tuple[StructuralObservation, ...],
]:
    """Read ``filings.files`` without discarding anything.

    Every entry becomes a reference, valid or not. A malformed entry is additionally
    quarantined so it is visible as source evidence, and a valid sibling is still
    returned and still retrievable.
    """
    filings = payload.get("filings")
    if not isinstance(filings, dict):
        # The absence of ``filings`` is already classified by _accession_records; the
        # files region is simply not observable here.
        return (), (), ()

    files, verdict = _classify_region(filings, "files", REGION_FILES, location, list, "array")
    if verdict is not None:
        return (), (), (verdict,)
    assert files is not None  # noqa: S101 - narrowed by the verdict guard

    if not files:
        return (
            (),
            (),
            (
                _structural(
                    location,
                    REGION_FILES,
                    "valid_empty",
                    files,
                    "filings.files is an explicit empty list: this registrant has no "
                    "historical overflow files, which is a genuine zero",
                    row_count=0,
                ),
            ),
        )

    references: list[HistoricalFileReference] = []
    rejected: list[QuarantinedRecord] = []
    malformed = 0
    for index, entry in enumerate(files):
        entry_location = RecordLocation(
            observation_id=location.observation_id,
            source_id=location.source_id,
            member_name=location.member_name,
            record_path=REGION_FILES,
            record_index=index,
        )
        if not isinstance(entry, dict):
            malformed += 1
            references.append(
                HistoricalFileReference(
                    name=None,
                    filing_count=None,
                    filing_from=None,
                    filing_to=None,
                    location=entry_location,
                    problems=(f"entry is a {type(entry).__name__}, not an object",),
                    raw_entry=None,
                )
            )
            rejected.append(
                _reject_historical(
                    entry_location,
                    f"filings.files[{index}] is a {type(entry).__name__}, not an object; "
                    "the entry is preserved and never silently skipped",
                    entry,
                )
            )
            continue

        problems: list[str] = []
        raw_name = entry.get("name")
        name = None if raw_name is None else str(raw_name).strip()
        if not name:
            problems.append("entry carries no usable name")
        elif not HISTORICAL_FILE_NAME_PATTERN.match(name):
            problems.append(
                f"name {name!r} does not match the official historical submissions "
                f"pattern {HISTORICAL_FILE_NAME_PATTERN.pattern}"
            )
        filing_count = _as_int(entry.get("filingCount"))
        if "filingCount" in entry and filing_count is None:
            problems.append(f"filingCount {entry.get('filingCount')!r} is not an integer")
        elif filing_count is not None and filing_count < 0:
            problems.append(f"filingCount {filing_count} is negative")
        unknown = tuple(sorted(set(entry) - _HISTORICAL_KNOWN_KEYS))

        references.append(
            HistoricalFileReference(
                name=name or None,
                filing_count=filing_count,
                filing_from=_as_text(entry.get("filingFrom")),
                filing_to=_as_text(entry.get("filingTo")),
                location=entry_location,
                problems=tuple(problems),
                raw_entry=dict(entry),
                unknown_fields=unknown,
            )
        )
        if problems:
            malformed += 1
            rejected.append(
                _reject_historical(
                    entry_location,
                    "; ".join(problems),
                    entry,
                )
            )

    state: StructuralState = "malformed" if malformed else "valid_present"
    detail = (
        f"filings.files carries {len(files)} entries, {malformed} of them malformed and "
        "preserved as evidence; valid siblings remain retrievable"
        if malformed
        else f"filings.files carries {len(files)} well-formed references"
    )
    structural = _structural(location, REGION_FILES, state, files, detail, row_count=len(files))
    return tuple(references), tuple(rejected), (structural,)


def _reject_historical(
    location: RecordLocation,
    detail: str,
    entry: object,
) -> QuarantinedRecord:
    return QuarantinedRecord(
        location=location,
        parser_id=PARSER_ID,
        parser_version=PARSER_VERSION,
        reason_codes=("PARSER_HISTORICAL_REFERENCE_MALFORMED",),
        detail=detail,
        raw_excerpt=_excerpt_value(entry),
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _normalized_cik(value: object, warnings: list[str]) -> str | None:
    """Return the zero-padded CIK, recording a warning when it is unusable.

    The raw value stays on the parsed record either way: normalization never
    replaces what the source said.
    """
    if value is None:
        return None
    try:
        return normalize_cik(str(value))[1]
    except IdentifierError as exc:
        warnings.append(f"cik {value!r} could not be normalized: {exc}")
        return None


def _nested_unknown_paths(payload: Mapping[str, Any]) -> tuple[str, ...]:
    """Return dotted paths of unknown fields inside the regions this parser models.

    Top-level unknowns are already reported by :func:`inspect_payload`. This walker
    covers the nested regions, so an unknown scalar, list, or object added by the SEC
    inside ``filings``, ``formerNames``, ``addresses``, or ``flags`` is recorded with
    its exact path rather than passing unnoticed.
    """
    found: set[str] = set()

    filings = payload.get("filings")
    if isinstance(filings, dict):
        found.update(f"filings.{key}" for key in set(filings) - _FILINGS_KNOWN_KEYS)

    former = payload.get("formerNames")
    if isinstance(former, list):
        for index, entry in enumerate(former):
            if isinstance(entry, dict):
                found.update(
                    f"formerNames[{index}].{key}" for key in set(entry) - _FORMER_NAME_KNOWN_KEYS
                )

    addresses = payload.get("addresses")
    if isinstance(addresses, dict):
        found.update(f"addresses.{key}" for key in set(addresses) - _ADDRESS_KINDS)
        for kind, block in addresses.items():
            if isinstance(block, dict):
                found.update(f"addresses.{kind}.{key}" for key in set(block) - _ADDRESS_KNOWN_KEYS)

    flags = payload.get("flags")
    if isinstance(flags, dict):
        found.update(f"flags.{key}" for key in set(flags) - _FLAG_KNOWN_KEYS)

    files = filings.get("files") if isinstance(filings, dict) else None
    if isinstance(files, list):
        for index, entry in enumerate(files):
            if isinstance(entry, dict):
                found.update(
                    f"filings.files[{index}].{key}" for key in set(entry) - _HISTORICAL_KNOWN_KEYS
                )

    recent = filings.get("recent") if isinstance(filings, dict) else None
    if isinstance(recent, dict):
        found.update(f"filings.recent.{key}" for key in set(recent) - set(ACCESSION_ARRAY_FIELDS))

    return tuple(sorted(found))


def _as_list(value: object) -> Sequence[Any]:
    return value if isinstance(value, list) else ()


def _as_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _as_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _excerpt(payload: Mapping[str, Any], limit: int = 500) -> str:
    text = repr(dict(payload))
    return text if len(text) <= limit else text[:limit] + "…"


def _excerpt_value(value: object, limit: int = 500) -> str:
    """Retain what was actually observed, whatever its type."""
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "…"
