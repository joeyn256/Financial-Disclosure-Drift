"""Reconcile SEC full-index coverage against submissions-derived accessions.

The quarterly company index is a coverage check, not an authority for filing fields
(Decision 012 places it below entity submissions). Reconciliation therefore *compares*
and *reports*; it never merges identities, deletes a record, or silently replaces a
value because the two sides disagree.

Six comparison states are produced, and they are kept distinct because collapsing them
would turn missing evidence into apparent agreement:

``matching``
    Both sides list the accession and every compared field agrees.
``index_only``
    The index lists an accession that submissions metadata does not.
``submissions_only``
    Submissions metadata lists an accession the index does not.
``conflicting``
    Both sides list it and at least one compared field disagrees.
``unavailable``
    A required index instance was not retrieved, so no comparison is possible.
``indeterminate``
    The index row or the submissions record was malformed, so the comparison could not
    be made even though both sides nominally exist.

Eligibility comparison is restricted to approved forms. Control forms are retained with
their metadata but are never treated as eligibility evidence.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final, Literal

__all__ = [
    "COMPARED_FIELDS",
    "RECONCILIATION_POLICY_VERSION",
    "IndexInstance",
    "ReconciliationOutcome",
    "ReconciliationReport",
    "ReconciliationState",
    "SubmissionsAccession",
    "reconcile_index",
]

RECONCILIATION_POLICY_VERSION: Final = "full-index-reconciliation/1.0"

ReconciliationState = Literal[
    "matching",
    "index_only",
    "submissions_only",
    "conflicting",
    "unavailable",
    "indeterminate",
]

COMPARED_FIELDS: Final[tuple[str, ...]] = ("form_type", "cik_padded", "date_filed")
"""Fields compared between the two sides. Both sides' values are always retained."""

APPROVED_FORMS: Final[frozenset[str]] = frozenset({"10-K", "10-K/A", "10-KT", "10-KT/A"})
"""Forms in the eligible study universe; only these drive eligibility comparison."""


@dataclass(frozen=True, slots=True)
class IndexInstance:
    """One required quarterly index instance in the census plan."""

    year: int
    quarter: int
    retrieved: bool = False
    observation_id: str | None = None
    parse_usable: bool = False

    @property
    def instance_key(self) -> str:
        """Stable key for this instance."""
        return f"{self.year}QTR{self.quarter}"

    @property
    def is_satisfied(self) -> bool:
        """Whether this required instance was retrieved and parsed usably."""
        return self.retrieved and self.parse_usable


@dataclass(frozen=True, slots=True)
class SubmissionsAccession:
    """One accession as derived from submissions metadata."""

    accession_plain: str
    form_type: str | None
    cik_padded: str | None
    date_filed: str | None
    observation_id: str
    is_usable: bool = True


@dataclass(frozen=True, slots=True)
class ReconciliationOutcome:
    """One accession's comparison result, with both sides' lineage retained."""

    accession_plain: str | None
    state: ReconciliationState
    index_values: Mapping[str, object] = field(default_factory=dict)
    submissions_values: Mapping[str, object] = field(default_factory=dict)
    index_observation_id: str | None = None
    submissions_observation_id: str | None = None
    conflicting_fields: tuple[str, ...] = ()
    instance_key: str | None = None
    detail: str = ""
    is_approved_form: bool = False

    @property
    def reason_codes(self) -> tuple[str, ...]:
        """Reason codes implied by this comparison."""
        return {
            "matching": (),
            "index_only": ("INDEX_ACCESSION_NOT_IN_SUBMISSIONS",),
            "submissions_only": ("SUBMISSIONS_ACCESSION_NOT_IN_INDEX",),
            "conflicting": ("INDEX_SUBMISSIONS_FIELD_CONFLICT",),
            "unavailable": ("INDEX_INSTANCE_UNAVAILABLE",),
            "indeterminate": ("INDEX_RECONCILIATION_INDETERMINATE",),
        }[self.state]

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence."""
        return {
            "accession_plain": self.accession_plain,
            "state": self.state,
            "instance_key": self.instance_key,
            "index_values": dict(sorted(self.index_values.items())),
            "submissions_values": dict(sorted(self.submissions_values.items())),
            "index_observation_id": self.index_observation_id,
            "submissions_observation_id": self.submissions_observation_id,
            "conflicting_fields": list(self.conflicting_fields),
            "is_approved_form": self.is_approved_form,
            "reason_codes": list(self.reason_codes),
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Deterministic accounting for one reconciliation run."""

    outcomes: tuple[ReconciliationOutcome, ...]
    missing_instances: tuple[str, ...]
    policy_version: str = RECONCILIATION_POLICY_VERSION

    @property
    def counts(self) -> Mapping[str, int]:
        """Count of outcomes by state, including states with no members."""
        counts = dict.fromkeys(
            (
                "matching",
                "index_only",
                "submissions_only",
                "conflicting",
                "unavailable",
                "indeterminate",
            ),
            0,
        )
        for outcome in self.outcomes:
            counts[outcome.state] += 1
        return counts

    @property
    def blocks_completion(self) -> bool:
        """Whether reconciliation prevents a truthful completion claim.

        A missing required index instance blocks: coverage cannot be confirmed against
        evidence that was never retrieved.
        """
        return bool(self.missing_instances) or self.counts["unavailable"] > 0

    @property
    def reason_codes(self) -> tuple[str, ...]:
        """Every reason code implied by this run, sorted."""
        codes: set[str] = set()
        for outcome in self.outcomes:
            codes.update(outcome.reason_codes)
        if self.missing_instances:
            codes.add("INDEX_REQUIRED_INSTANCE_MISSING")
        return tuple(sorted(codes))

    def reconciliation_hash(self) -> str:
        """Deterministic hash over every outcome and missing instance."""
        payload = {
            "policy_version": self.policy_version,
            "missing_instances": sorted(self.missing_instances),
            "outcomes": sorted(
                (json.dumps(dict(item.as_record()), sort_keys=True, default=str))
                for item in self.outcomes
            ),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for the QA report."""
        return {
            "policy_version": self.policy_version,
            "counts": dict(self.counts),
            "missing_instances": list(self.missing_instances),
            "blocks_completion": self.blocks_completion,
            "reason_codes": list(self.reason_codes),
            "reconciliation_sha256": self.reconciliation_hash(),
            "outcomes": [dict(item.as_record()) for item in self.outcomes],
        }


def reconcile_index(
    index_rows: Iterable[Mapping[str, object]],
    submissions: Iterable[SubmissionsAccession],
    *,
    required_instances: Sequence[IndexInstance] = (),
    index_observation_id: str | None = None,
) -> ReconciliationReport:
    """Compare index coverage against submissions-derived accessions.

    Args:
        index_rows: Parsed index row payloads, as produced by the company-index parser.
        submissions: Accessions derived from submissions metadata.
        required_instances: Index instances the census plan requires. Any that were not
            retrieved and usably parsed block completion.
        index_observation_id: Observation the index rows came from, for lineage.

    Returns:
        A deterministic report. Nothing is merged, deleted, or replaced.
    """
    outcomes: list[ReconciliationOutcome] = []
    missing = tuple(
        sorted(item.instance_key for item in required_instances if not item.is_satisfied)
    )
    for item in required_instances:
        if item.is_satisfied:
            continue
        outcomes.append(
            ReconciliationOutcome(
                accession_plain=None,
                state="unavailable",
                instance_key=item.instance_key,
                index_observation_id=item.observation_id,
                detail=(
                    f"required index instance {item.instance_key} was not retrieved and "
                    "usably parsed, so coverage for it cannot be confirmed"
                ),
            )
        )

    # Group first, then emit. Grouping before emitting is what makes duplicate handling
    # independent of the order the rows arrive in: the representative row and the
    # reported duplicates are chosen by line number, not by which was seen first.
    grouped: dict[str, list[Mapping[str, object]]] = {}
    malformed_rows: list[Mapping[str, object]] = []
    for row in index_rows:
        accession = row.get("accession_plain")
        if not accession or (row.get("problems") or []):
            malformed_rows.append(row)
            continue
        grouped.setdefault(str(accession), []).append(row)

    for row in sorted(malformed_rows, key=_row_sort_key):
        outcomes.append(
            ReconciliationOutcome(
                accession_plain=(
                    str(row["accession_plain"]) if row.get("accession_plain") else None
                ),
                state="indeterminate",
                index_values=dict(row),
                index_observation_id=index_observation_id,
                detail=(
                    "the index row could not be read well enough to compare; it is "
                    "retained in full as source evidence"
                ),
            )
        )

    index_by_accession: dict[str, Mapping[str, object]] = {}
    for key, rows in sorted(grouped.items()):
        ordered = sorted(rows, key=_row_sort_key)
        index_by_accession[key] = ordered[0]
        if len(ordered) == 1:
            continue
        # Duplicate index rows are retained, never deduplicated.
        for duplicate in ordered[1:]:
            conflicts = _conflicts(ordered[0], duplicate)
            outcomes.append(
                ReconciliationOutcome(
                    accession_plain=key,
                    state="conflicting" if conflicts else "matching",
                    index_values=dict(duplicate),
                    submissions_values=dict(ordered[0]),
                    index_observation_id=index_observation_id,
                    conflicting_fields=conflicts,
                    detail=(
                        "the index lists this accession more than once; every row is "
                        "retained and none is removed"
                    ),
                    is_approved_form=_is_approved(duplicate.get("form_type")),
                )
            )

    submissions_by_accession = {item.accession_plain: item for item in submissions}

    for key in sorted(set(index_by_accession) | set(submissions_by_accession)):
        index_row: Mapping[str, object] | None = index_by_accession.get(key)
        derived = submissions_by_accession.get(key)
        # Each key comes from one or both mappings, so at least one side is present.
        # Handling each single-sided case first narrows both variables by control flow,
        # with no assertion needed to convince the type checker.
        if derived is None:
            if index_row is None:  # pragma: no cover - key originates from one mapping
                continue
            outcomes.append(
                ReconciliationOutcome(
                    accession_plain=key,
                    state="index_only",
                    index_values=dict(index_row),
                    index_observation_id=index_observation_id,
                    detail="the index lists this accession but submissions metadata does not",
                    is_approved_form=_is_approved(index_row.get("form_type")),
                )
            )
            continue
        if index_row is None:
            outcomes.append(
                ReconciliationOutcome(
                    accession_plain=key,
                    state="submissions_only",
                    submissions_values=_derived_values(derived),
                    submissions_observation_id=derived.observation_id,
                    detail="submissions metadata lists this accession but the index does not",
                    is_approved_form=_is_approved(derived.form_type),
                )
            )
            continue
        if not derived.is_usable:
            outcomes.append(
                ReconciliationOutcome(
                    accession_plain=key,
                    state="indeterminate",
                    index_values=dict(index_row),
                    submissions_values=_derived_values(derived),
                    index_observation_id=index_observation_id,
                    submissions_observation_id=derived.observation_id,
                    detail="the submissions-derived record was malformed, so no comparison",
                    is_approved_form=_is_approved(index_row.get("form_type")),
                )
            )
            continue
        conflicts = _conflicts(index_row, _derived_values(derived))
        outcomes.append(
            ReconciliationOutcome(
                accession_plain=key,
                state="conflicting" if conflicts else "matching",
                index_values=dict(index_row),
                submissions_values=_derived_values(derived),
                index_observation_id=index_observation_id,
                submissions_observation_id=derived.observation_id,
                conflicting_fields=conflicts,
                detail=(
                    f"compared fields disagree: {list(conflicts)}; both sides are retained"
                    if conflicts
                    else "the index and submissions metadata agree on every compared field"
                ),
                is_approved_form=_is_approved(index_row.get("form_type")),
            )
        )

    return ReconciliationReport(outcomes=tuple(outcomes), missing_instances=missing)


def _row_sort_key(row: Mapping[str, object]) -> tuple[int, str]:
    """Deterministic row order derived from the source, not from arrival order."""
    line = row.get("line_number")
    number = int(line) if isinstance(line, int) else 0
    return (number, json.dumps(dict(row), sort_keys=True, default=str))


def _derived_values(item: SubmissionsAccession) -> Mapping[str, object]:
    return {
        "form_type": item.form_type,
        "cik_padded": item.cik_padded,
        "date_filed": item.date_filed,
        "accession_plain": item.accession_plain,
    }


def _conflicts(
    left: Mapping[str, object],
    right: Mapping[str, object],
) -> tuple[str, ...]:
    """Return compared fields whose values disagree, ignoring absent values."""
    differing: list[str] = []
    for name in COMPARED_FIELDS:
        first = left.get(name)
        second = right.get(name)
        if first is None or second is None:
            continue
        if str(first).strip() != str(second).strip():
            differing.append(name)
    return tuple(differing)


def _differs(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return bool(_conflicts(left, right))


def _is_approved(form: object) -> bool:
    """Whether a form is in the eligible universe for eligibility comparison."""
    return form is not None and str(form).strip().upper() in APPROVED_FORMS
