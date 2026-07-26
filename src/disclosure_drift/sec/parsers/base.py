"""The parsed-source-record layer that sits between raw bytes and the census.

Three layers are preserved, and no parser is allowed to collapse them:

1. **Immutable raw source observation** — bytes as retrieved, hashed and stored by
   :mod:`disclosure_drift.sec.snapshots`. Never modified.
2. **Parsed source record** — this module. One record per source-native entity,
   keeping the source's own identifiers and field names, every unknown field, and a
   deterministic record hash. Nothing is normalized away at this layer.
3. **Normalized census observation** — derived from parsed records by the census, and
   the only layer the canonical registrant tables are written from.

Every parser records, per :class:`ParsedRecord` and :class:`ParseOutcome`:

* parser identifier and version;
* the source-observation identifier it read;
* the source member or record location;
* required-field failures;
* unknown fields;
* duplicate source records;
* normalization warnings;
* malformed-record quarantine;
* a deterministic record hash.

CIK identity is never inferred. A parser may not merge two CIKs because they share a
ticker, a name, or an exchange: such agreement is recorded as candidate evidence for
review, never applied.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final, Literal

from disclosure_drift.sec.schema_drift import DriftReport

__all__ = [
    "PARSER_LAYER_VERSION",
    "STRUCTURAL_REASON_BY_STATE",
    "ParseOutcome",
    "ParsedRecord",
    "QuarantinedRecord",
    "RecordLocation",
    "StructuralObservation",
    "StructuralState",
    "count_duplicates",
    "merge_outcomes",
    "record_hash",
]

PARSER_LAYER_VERSION: Final = "parsed-source-record/1.1"
RecordStatus = Literal["parsed", "quarantined"]

StructuralState = Literal[
    "valid_present",
    "valid_empty",
    "absent",
    "null",
    "wrong_type",
    "malformed",
    "unavailable",
    "indeterminate",
]
"""How one nested region of a source document was actually shaped.

Only ``valid_present`` and ``valid_empty`` permit a record count to be believed.
``valid_empty`` is a genuine zero: the region existed, was correctly typed, and
carried no rows. Every other state means the count is unknown, so a downstream
consumer must never read it as zero.
"""

STRUCTURAL_REASON_BY_STATE: Final[Mapping[StructuralState, str]] = {
    "valid_present": "",
    "valid_empty": "PARSER_STRUCTURE_VALID_EMPTY",
    "absent": "PARSER_STRUCTURE_ABSENT",
    "null": "PARSER_STRUCTURE_NULL",
    "wrong_type": "PARSER_STRUCTURE_WRONG_TYPE",
    "malformed": "PARSER_STRUCTURE_MALFORMED",
    "unavailable": "PARSER_STRUCTURE_INDETERMINATE",
    "indeterminate": "PARSER_STRUCTURE_INDETERMINATE",
}
"""The registered reason code each structural state carries."""

_COUNTABLE: Final[frozenset[str]] = frozenset({"valid_present", "valid_empty"})


def record_hash(
    payload: Mapping[str, Any],
    unknown_field_paths: Sequence[str] = (),
) -> str:
    """Return a deterministic SHA-256 over one parsed record.

    The hash covers an envelope of the source-native payload **and** the sorted
    unknown-field paths observed for it. Nested unknown fields therefore change the
    record hash even when they live in a region the record does not copy verbatim,
    which is what makes schema drift detectable by hash comparison alone.

    Keys are sorted and separators are fixed, so the same source content always
    produces the same hash regardless of dictionary ordering or platform.
    """
    envelope = {
        "payload": payload,
        "unknown_field_paths": sorted(unknown_field_paths),
    }
    canonical = json.dumps(
        envelope, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class RecordLocation:
    """Where a parsed record came from inside its source observation."""

    observation_id: str
    source_id: str
    member_name: str | None = None
    record_path: str | None = None
    record_index: int | None = None

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for the catalog and audit projection."""
        return {
            "observation_id": self.observation_id,
            "source_id": self.source_id,
            "member_name": self.member_name,
            "record_path": self.record_path,
            "record_index": self.record_index,
        }

    def describe(self) -> str:
        """Human-readable location, used in review messages."""
        parts = [self.source_id]
        if self.member_name:
            parts.append(self.member_name)
        if self.record_path:
            parts.append(self.record_path)
        if self.record_index is not None:
            parts.append(f"#{self.record_index}")
        return " / ".join(parts)


@dataclass(frozen=True, slots=True)
class ParsedRecord:
    """One source-native record, retained before any normalization."""

    native_identity: str
    payload: Mapping[str, Any]
    location: RecordLocation
    parser_id: str
    parser_version: str
    unknown_fields: tuple[str, ...] = ()
    normalization_warnings: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    duplicate_indicator: bool = False
    conflict_indicator: bool = False

    @property
    def record_sha256(self) -> str:
        """Deterministic hash of the payload and its observed unknown-field paths."""
        return record_hash(self.payload, self.unknown_fields)

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence."""
        return {
            "native_identity": self.native_identity,
            "record_sha256": self.record_sha256,
            "parser_id": self.parser_id,
            "parser_version": self.parser_version,
            "layer_version": PARSER_LAYER_VERSION,
            "location": dict(self.location.as_record()),
            "unknown_fields": list(self.unknown_fields),
            "normalization_warnings": list(self.normalization_warnings),
            "reason_codes": list(self.reason_codes),
            "duplicate_indicator": self.duplicate_indicator,
            "conflict_indicator": self.conflict_indicator,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class QuarantinedRecord:
    """One malformed source record, preserved rather than dropped."""

    location: RecordLocation
    parser_id: str
    parser_version: str
    reason_codes: tuple[str, ...]
    detail: str
    raw_excerpt: str = ""
    native_identity: str | None = None

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence."""
        return {
            "native_identity": self.native_identity,
            "parser_id": self.parser_id,
            "parser_version": self.parser_version,
            "layer_version": PARSER_LAYER_VERSION,
            "location": dict(self.location.as_record()),
            "reason_codes": list(self.reason_codes),
            "detail": self.detail,
            "raw_excerpt": self.raw_excerpt,
        }


@dataclass(frozen=True, slots=True)
class StructuralObservation:
    """A typed verdict on the shape of one nested region of a source document.

    This exists so that "zero records" can never be ambiguous. A region that was
    present, correctly typed, and empty is a genuine zero. A region that was absent,
    null, wrongly typed, internally inconsistent, or unreadable yields an unknown
    count and a release-blocking reason, and the raw payload is retained either way.
    """

    region: str
    state: StructuralState
    observed_type: str
    location: RecordLocation
    row_count: int | None = None
    detail: str = ""
    raw_excerpt: str = ""

    @property
    def reason_codes(self) -> tuple[str, ...]:
        """The registered reason code this state carries, if any."""
        code = STRUCTURAL_REASON_BY_STATE[self.state]
        return (code,) if code else ()

    @property
    def count_is_trustworthy(self) -> bool:
        """Whether ``row_count`` may be read as a real count, including zero."""
        return self.state in _COUNTABLE

    @property
    def is_genuine_zero(self) -> bool:
        """Whether this region genuinely contained no rows."""
        return self.state == "valid_empty" or (
            self.state == "valid_present" and self.row_count == 0
        )

    @property
    def blocks_success(self) -> bool:
        """Whether this structural verdict prevents a successful parser run."""
        return not self.count_is_trustworthy

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence and the QA projection."""
        return {
            "region": self.region,
            "state": self.state,
            "observed_type": self.observed_type,
            "location": dict(self.location.as_record()),
            "row_count": self.row_count,
            "count_is_trustworthy": self.count_is_trustworthy,
            "is_genuine_zero": self.is_genuine_zero,
            "reason_codes": list(self.reason_codes),
            "detail": self.detail,
            "raw_excerpt": self.raw_excerpt,
        }


@dataclass(frozen=True, slots=True)
class ParseOutcome:
    """Everything one parser run produced, including what it refused."""

    parser_id: str
    parser_version: str
    records: tuple[ParsedRecord, ...] = ()
    quarantined: tuple[QuarantinedRecord, ...] = ()
    duplicate_identities: tuple[tuple[str, int], ...] = ()
    required_field_failures: tuple[tuple[str, str], ...] = ()
    unknown_fields: tuple[str, ...] = ()
    normalization_warnings: tuple[str, ...] = ()
    drift_reports: tuple[DriftReport, ...] = field(default_factory=tuple)
    structural: tuple[StructuralObservation, ...] = field(default_factory=tuple)

    @property
    def reason_codes(self) -> tuple[str, ...]:
        """Reason codes implied by this run, sorted and deduplicated."""
        codes: set[str] = set()
        if self.unknown_fields:
            codes.add("PARSER_SCHEMA_DRIFT_OBSERVED")
        if self.duplicate_identities:
            codes.add("PARSER_DUPLICATE_SOURCE_RECORD")
        if self.required_field_failures:
            codes.add("SEC_SCHEMA_REQUIRED_FIELD_MISSING")
        for item in self.quarantined:
            codes.update(item.reason_codes)
        for observation in self.structural:
            codes.update(observation.reason_codes)
        return tuple(sorted(codes))

    @property
    def structural_failures(self) -> tuple[StructuralObservation, ...]:
        """Structural verdicts whose record counts may not be believed."""
        return tuple(item for item in self.structural if item.blocks_success)

    @property
    def counts_are_trustworthy(self) -> bool:
        """Whether every structural region permits its counts to be read.

        A parser run with zero records is a genuine zero only when this is true.
        """
        return not self.structural_failures

    def region_state(self, region: str) -> StructuralState | None:
        """Return the recorded structural state for ``region``, if observed."""
        for item in self.structural:
            if item.region == region:
                return item.state
        return None

    @property
    def counts(self) -> Mapping[str, int]:
        """Deterministic accounting for the QA report.

        ``parsed`` and ``quarantined`` are reported separately so that zero parsed
        records is never confused with a source that failed or was not retrieved,
        and ``structural_failures`` separates an unknown count from a real zero.
        """
        return {
            "parsed": len(self.records),
            "quarantined": len(self.quarantined),
            "duplicate_identities": len(self.duplicate_identities),
            "required_field_failures": len(self.required_field_failures),
            "unknown_fields": len(self.unknown_fields),
            "normalization_warnings": len(self.normalization_warnings),
            "structural_observations": len(self.structural),
            "structural_failures": len(self.structural_failures),
        }

    def summary(self) -> Mapping[str, object]:
        """Deterministic parser-run summary, including nested unknown-field paths."""
        return {
            "parser_id": self.parser_id,
            "parser_version": self.parser_version,
            "layer_version": PARSER_LAYER_VERSION,
            "counts": dict(self.counts),
            "counts_are_trustworthy": self.counts_are_trustworthy,
            "unknown_field_paths": list(self.unknown_fields),
            "normalization_warnings": list(self.normalization_warnings),
            "duplicate_identities": [list(item) for item in self.duplicate_identities],
            "required_field_failures": [list(item) for item in self.required_field_failures],
            "reason_codes": list(self.reason_codes),
            "structural": [item.as_record() for item in self.structural],
        }

    def by_identity(self) -> Mapping[str, tuple[ParsedRecord, ...]]:
        """Group parsed records by source-native identity, preserving duplicates."""
        grouped: dict[str, list[ParsedRecord]] = {}
        for item in self.records:
            grouped.setdefault(item.native_identity, []).append(item)
        return {key: tuple(value) for key, value in sorted(grouped.items())}


def merge_outcomes(
    parser_id: str,
    parser_version: str,
    outcomes: Iterable[ParseOutcome],
) -> ParseOutcome:
    """Combine per-member outcomes into one run-level outcome."""
    records: list[ParsedRecord] = []
    quarantined: list[QuarantinedRecord] = []
    duplicates: list[tuple[str, int]] = []
    failures: list[tuple[str, str]] = []
    unknown: set[str] = set()
    warnings: list[str] = []
    drift: list[DriftReport] = []
    structural: list[StructuralObservation] = []
    for outcome in outcomes:
        records.extend(outcome.records)
        quarantined.extend(outcome.quarantined)
        duplicates.extend(outcome.duplicate_identities)
        failures.extend(outcome.required_field_failures)
        unknown.update(outcome.unknown_fields)
        warnings.extend(outcome.normalization_warnings)
        drift.extend(outcome.drift_reports)
        structural.extend(outcome.structural)
    return ParseOutcome(
        parser_id=parser_id,
        parser_version=parser_version,
        records=tuple(records),
        quarantined=tuple(quarantined),
        duplicate_identities=tuple(duplicates),
        required_field_failures=tuple(failures),
        unknown_fields=tuple(sorted(unknown)),
        normalization_warnings=tuple(warnings),
        drift_reports=tuple(drift),
        structural=tuple(structural),
    )


def count_duplicates(identities: Sequence[str]) -> tuple[tuple[str, int], ...]:
    """Return identities that appeared more than once, with their counts."""
    seen: dict[str, int] = {}
    for identity in identities:
        seen[identity] = seen.get(identity, 0) + 1
    return tuple(sorted((key, value) for key, value in seen.items() if value > 1))
