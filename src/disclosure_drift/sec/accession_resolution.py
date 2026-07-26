"""Deterministic, order-independent resolution of canonical accession fields.

Implements Decision 012 (`accession-resolution/1.0`).

Every source-native observation stays immutable. A canonical field is a *derived view*
over the observation set, computed per field rather than by choosing a whole-record
winner, because two sources may each be authoritative for different fields and a
correction may touch one field only.

Resolution order-independence is achieved by never consulting arrival order. Candidates
are sorted into a total order derived only from the evidence itself — authority class,
correction status, source version, then observation identifier as a final tie-break —
so the same observation set always produces the same canonical value, the same
unresolved statuses, and the same resolution hash.

Recency is not authority. A later retrieval of the same living source does not override
a conflict; only an explicitly identified official correction, or a higher authority
class, may supersede an earlier value. Equal authority with conflicting values stays
``unresolved``.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final, Literal

from disclosure_drift.sec.temporal import cohort_label_for_value

__all__ = [
    "AUTHORITY_LEVEL",
    "DEFERRED_AUTHORITY_CLASSES",
    "MATERIAL_FIELDS",
    "RESOLUTION_POLICY_VERSION",
    "RESOLVED_FIELDS",
    "AccessionFieldObservation",
    "AccessionResolution",
    "AuthorityClass",
    "FieldResolution",
    "ResolutionStatus",
    "authority_for_source",
    "resolve_accession",
    "resolve_field",
]

RESOLUTION_POLICY_VERSION: Final = "accession-resolution/1.0"

AuthorityClass = Literal[
    "filing_level_metadata",
    "entity_submissions",
    "full_index",
    "identity_alias",
]
AUTHORITY_LEVEL: Final[Mapping[AuthorityClass, int]] = {
    "filing_level_metadata": 1,
    "entity_submissions": 2,
    "full_index": 3,
    "identity_alias": 4,
}
"""Lower is more authoritative (Decision 012 section 4)."""

DEFERRED_AUTHORITY_CLASSES: Final[frozenset[str]] = frozenset({"filing_level_metadata"})
"""Level 1 needs accession-level retrieval, which Stage M2.2 prohibits."""

_SOURCE_AUTHORITY: Final[Mapping[str, AuthorityClass]] = {
    "sec_bulk_submissions": "entity_submissions",
    "sec_submissions_entity": "entity_submissions",
    "sec_submissions_historical": "entity_submissions",
    "sec_full_index_company": "full_index",
    "sec_company_tickers": "identity_alias",
    "sec_company_tickers_exchange": "identity_alias",
}

RESOLVED_FIELDS: Final[tuple[str, ...]] = (
    "form",
    "official_filing_date",
    "report_date",
    "acceptance_timestamp",
    "registrant_cik",
    "submitter_cik",
    "primary_document_metadata",
    "amendment_relationship",
)
MATERIAL_FIELDS: Final[frozenset[str]] = frozenset(
    {"form", "official_filing_date", "registrant_cik", "amendment_relationship"}
)
"""Fields whose unresolved state blocks downstream use (Decision 012 section 3)."""

_FILING_FIELDS: Final[frozenset[str]] = frozenset(RESOLVED_FIELDS)
ResolutionStatus = Literal["resolved", "resolved_by_correction", "unresolved", "absent"]


def authority_for_source(source_id: str) -> AuthorityClass:
    """Return the authority class registered for ``source_id``.

    Raises:
        KeyError: the source is not classified. Authority is explicit; an unclassified
            source never receives a default level.
    """
    try:
        return _SOURCE_AUTHORITY[source_id]
    except KeyError:
        known = ", ".join(sorted(_SOURCE_AUTHORITY))
        message = (
            f"source {source_id!r} has no registered accession-authority class. "
            f"Classified sources: {known}. Add it to Decision 012 before use."
        )
        raise KeyError(message) from None


@dataclass(frozen=True, slots=True)
class AccessionFieldObservation:
    """One immutable source-native observation of one accession field.

    ``observed_at_utc`` is recorded for audit only. It never participates in ranking:
    that is what keeps resolution independent of ingestion and retrieval order.
    """

    observation_id: str
    source_id: str
    accession_plain: str
    field_name: str
    value: object
    observed_at_utc: str
    source_version: str | None = None
    is_correction: bool = False
    correction_evidence_id: str | None = None

    @property
    def authority(self) -> AuthorityClass:
        """Authority class implied by the source."""
        return authority_for_source(self.source_id)

    @property
    def authority_level(self) -> int:
        """Numeric authority level; lower is stronger."""
        return AUTHORITY_LEVEL[self.authority]

    @property
    def carries_filing_authority(self) -> bool:
        """Whether this source may resolve a filing field at all.

        An identity-alias source contributes aliases only. It may never resolve a form,
        a date, or a CIK, however many times it is observed.
        """
        return self.authority != "identity_alias"

    @property
    def normalized_value(self) -> str:
        """Canonical comparable form of the observed value."""
        return _normalize(self.value)

    def rank(self) -> tuple[int, int, str, str]:
        """Total order derived only from the evidence, never from arrival order."""
        return (
            self.authority_level,
            0 if self.is_correction else 1,
            _version_key(self.source_version),
            self.observation_id,
        )


@dataclass(frozen=True, slots=True)
class FieldResolution:
    """The resolved view of one accession field."""

    field_name: str
    status: ResolutionStatus
    value: object | None
    authority: AuthorityClass | None
    winning_observation_ids: tuple[str, ...]
    competing_observation_ids: tuple[str, ...]
    correction_evidence_id: str | None
    reason_codes: tuple[str, ...]
    detail: str

    @property
    def is_material(self) -> bool:
        """Whether this field is material under Decision 012."""
        return self.field_name in MATERIAL_FIELDS

    @property
    def blocks_dependents(self) -> bool:
        """Whether downstream use depending on this field must be blocked."""
        return self.status == "unresolved" and self.is_material

    def resolution_hash(self) -> str:
        """Deterministic hash of this resolution, excluding wall-clock time."""
        return _hash(
            {
                "policy_version": RESOLUTION_POLICY_VERSION,
                "field": self.field_name,
                "status": self.status,
                "value": _normalize(self.value) if self.value is not None else None,
                "authority": self.authority,
                "winning": sorted(self.winning_observation_ids),
                "competing": sorted(self.competing_observation_ids),
                "correction_evidence_id": self.correction_evidence_id,
                "reason_codes": sorted(self.reason_codes),
            }
        )

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence."""
        return {
            "field_name": self.field_name,
            "status": self.status,
            "value": self.value,
            "authority_class": self.authority,
            "policy_version": RESOLUTION_POLICY_VERSION,
            "winning_observation_ids": list(self.winning_observation_ids),
            "competing_observation_ids": list(self.competing_observation_ids),
            "correction_evidence_id": self.correction_evidence_id,
            "reason_codes": list(self.reason_codes),
            "is_material": self.is_material,
            "blocks_dependents": self.blocks_dependents,
            "detail": self.detail,
            "resolution_sha256": self.resolution_hash(),
        }


@dataclass(frozen=True, slots=True)
class AccessionResolution:
    """Every field resolution for one accession, plus its cohort consequences."""

    accession_plain: str
    fields: Mapping[str, FieldResolution]
    official_filing_cohort: str
    accepted_cohort: str
    prior_filing_cohorts: tuple[str, ...] = ()
    cohort_boundary_crossed: bool = False
    requires_2024_approval: bool = False
    extra_reason_codes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def unresolved_fields(self) -> tuple[str, ...]:
        """Fields that could not be resolved, sorted."""
        return tuple(
            sorted(name for name, item in self.fields.items() if item.status == "unresolved")
        )

    @property
    def blocking_fields(self) -> tuple[str, ...]:
        """Material fields whose unresolved state blocks downstream use."""
        return tuple(sorted(name for name, item in self.fields.items() if item.blocks_dependents))

    @property
    def reason_codes(self) -> tuple[str, ...]:
        """Every reason code implied by this accession, sorted and deduplicated."""
        codes: set[str] = set(self.extra_reason_codes)
        for item in self.fields.values():
            codes.update(item.reason_codes)
        return tuple(sorted(codes))

    def value(self, field_name: str) -> object | None:
        """Resolved value for ``field_name``, or ``None`` when unresolved."""
        resolution = self.fields.get(field_name)
        return None if resolution is None else resolution.value

    def resolution_hash(self) -> str:
        """Deterministic hash over every field resolution and cohort consequence."""
        return _hash(
            {
                "policy_version": RESOLUTION_POLICY_VERSION,
                "accession": self.accession_plain,
                "fields": {
                    name: self.fields[name].resolution_hash() for name in sorted(self.fields)
                },
                "official_filing_cohort": self.official_filing_cohort,
                "accepted_cohort": self.accepted_cohort,
                "prior_filing_cohorts": sorted(self.prior_filing_cohorts),
                "cohort_boundary_crossed": self.cohort_boundary_crossed,
                "requires_2024_approval": self.requires_2024_approval,
                "extra_reason_codes": sorted(self.extra_reason_codes),
            }
        )

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence and the QA report."""
        return {
            "accession_plain": self.accession_plain,
            "policy_version": RESOLUTION_POLICY_VERSION,
            "fields": {name: dict(self.fields[name].as_record()) for name in sorted(self.fields)},
            "official_filing_temporal_cohort": self.official_filing_cohort,
            "accepted_temporal_cohort": self.accepted_cohort,
            "prior_filing_cohorts": list(self.prior_filing_cohorts),
            "cohort_boundary_crossed": self.cohort_boundary_crossed,
            "requires_2024_approval": self.requires_2024_approval,
            "unresolved_fields": list(self.unresolved_fields),
            "blocking_fields": list(self.blocking_fields),
            "reason_codes": list(self.reason_codes),
            "resolution_sha256": self.resolution_hash(),
        }


# --------------------------------------------------------------------------- #
# Field resolution
# --------------------------------------------------------------------------- #
def resolve_field(
    field_name: str,
    observations: Iterable[AccessionFieldObservation],
) -> FieldResolution:
    """Resolve one field from its observations, deterministically.

    Args:
        field_name: One of :data:`RESOLVED_FIELDS`.
        observations: Every observation of that field, in any order.

    Returns:
        A resolution whose value, status, and hash depend only on the observation set.
    """
    candidates = [item for item in observations if item.field_name == field_name]
    competing = tuple(sorted(item.observation_id for item in candidates))
    if not candidates:
        return FieldResolution(
            field_name=field_name,
            status="absent",
            value=None,
            authority=None,
            winning_observation_ids=(),
            competing_observation_ids=(),
            correction_evidence_id=None,
            reason_codes=(),
            detail="no observation of this field was recorded",
        )

    eligible = [item for item in candidates if item.carries_filing_authority]
    if not eligible:
        return FieldResolution(
            field_name=field_name,
            status="unresolved",
            value=None,
            authority=None,
            winning_observation_ids=(),
            competing_observation_ids=competing,
            correction_evidence_id=None,
            reason_codes=_conflict_codes(field_name),
            detail=(
                "only identity-alias sources observed this field; an alias source carries "
                "no filing-field authority"
            ),
        )

    ordered = sorted(eligible, key=lambda item: item.rank())
    best = ordered[0]

    # Only observations that tie on authority and correction status compete with the
    # leader. A weaker source never creates a conflict, and a later ordinary retrieval
    # never displaces a stronger one.
    peers = [
        item
        for item in ordered
        if item.authority_level == best.authority_level and item.is_correction == best.is_correction
    ]
    distinct = {item.normalized_value for item in peers}
    if len(distinct) > 1:
        return FieldResolution(
            field_name=field_name,
            status="unresolved",
            value=None,
            authority=best.authority,
            winning_observation_ids=(),
            competing_observation_ids=competing,
            correction_evidence_id=None,
            reason_codes=(
                "ACCESSION_FIELD_UNRESOLVED_EQUAL_AUTHORITY",
                *_conflict_codes(field_name),
            ),
            detail=(
                f"{len(peers)} observations of equal authority "
                f"({best.authority}) disagree: {sorted(distinct)}. Every observation is "
                "preserved and no value is guessed."
            ),
        )

    winners = tuple(
        sorted(
            item.observation_id for item in peers if item.normalized_value == best.normalized_value
        )
    )
    if best.is_correction:
        return FieldResolution(
            field_name=field_name,
            status="resolved_by_correction",
            value=best.value,
            authority=best.authority,
            winning_observation_ids=winners,
            competing_observation_ids=competing,
            correction_evidence_id=best.correction_evidence_id,
            reason_codes=("ACCESSION_FIELD_RESOLVED_BY_CORRECTION",),
            detail=(
                f"an official correction ({best.correction_evidence_id or 'unidentified'}) "
                f"supersedes earlier values; {len(candidates)} observations preserved"
            ),
        )
    return FieldResolution(
        field_name=field_name,
        status="resolved",
        value=best.value,
        authority=best.authority,
        winning_observation_ids=winners,
        competing_observation_ids=competing,
        correction_evidence_id=None,
        reason_codes=("ACCESSION_FIELD_RESOLVED",),
        detail=(
            f"resolved from authority class {best.authority}; "
            f"{len(candidates)} observations preserved"
        ),
    )


# --------------------------------------------------------------------------- #
# Accession resolution
# --------------------------------------------------------------------------- #
def resolve_accession(
    accession_plain: str,
    observations: Sequence[AccessionFieldObservation],
    *,
    prior_filing_dates: Sequence[str] = (),
    approved_2024_transition: bool = False,
) -> AccessionResolution:
    """Resolve every canonical field for one accession.

    Args:
        accession_plain: Accession number without dashes.
        observations: Every field observation for this accession, in any order.
        prior_filing_dates: Previously resolved official filing dates, retained so a
            correction's cohort consequences can be recorded rather than overwritten.
        approved_2024_transition: Whether entry into or exit from the 2024 primary-test
            cohort has been explicitly approved. Without approval the transition is
            recorded and blocked.

    Returns:
        The resolved view, including recomputed cohorts and cohort-boundary findings.
    """
    resolutions = {name: resolve_field(name, observations) for name in RESOLVED_FIELDS}

    filing = resolutions["official_filing_date"]
    acceptance = resolutions["acceptance_timestamp"]
    filing_cohort = (
        cohort_label_for_value(_as_date_text(filing.value))
        if filing.status in {"resolved", "resolved_by_correction"}
        else "unresolved"
    )
    accepted_cohort = (
        cohort_label_for_value(_as_date_text(acceptance.value))
        if acceptance.status in {"resolved", "resolved_by_correction"}
        else "unresolved"
    )

    prior_cohorts = tuple(
        sorted({cohort_label_for_value(value) for value in prior_filing_dates if value})
    )
    crossed = bool(prior_cohorts) and any(cohort != filing_cohort for cohort in prior_cohorts)
    touches_2024 = filing_cohort == "primary_test" or "primary_test" in prior_cohorts
    requires_approval = bool(crossed and touches_2024 and not approved_2024_transition)

    extra: list[str] = []
    if crossed:
        extra.append("ACCESSION_COHORT_BOUNDARY_CROSSED")
    if requires_approval:
        extra.append("ACCESSION_2024_COHORT_TRANSITION_REQUIRES_APPROVAL")
    registrant = resolutions["registrant_cik"]
    submitter = resolutions["submitter_cik"]
    if registrant.status == "unresolved":
        extra.append("ACCESSION_REGISTRANT_CONFLICT_PRESERVED")
    if (
        registrant.status in {"resolved", "resolved_by_correction"}
        and submitter.status in {"resolved", "resolved_by_correction"}
        and _normalize(registrant.value) != _normalize(submitter.value)
    ):
        extra.append("ACCESSION_SUBMITTER_DIFFERS_FROM_REGISTRANT")

    return AccessionResolution(
        accession_plain=accession_plain,
        fields=resolutions,
        official_filing_cohort=filing_cohort,
        accepted_cohort=accepted_cohort,
        prior_filing_cohorts=prior_cohorts,
        cohort_boundary_crossed=crossed,
        requires_2024_approval=requires_approval,
        extra_reason_codes=tuple(sorted(set(extra))),
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _conflict_codes(field_name: str) -> tuple[str, ...]:
    if field_name in MATERIAL_FIELDS:
        return ("ACCESSION_FIELD_CONFLICT_MATERIAL",)
    return ("ACCESSION_FIELD_CONFLICT_NON_MATERIAL",)


def _normalize(value: object) -> str:
    """Canonical comparable text for any observed value."""
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return json.dumps(
            {str(key): _normalize(item) for key, item in sorted(value.items())},
            sort_keys=True,
            separators=(",", ":"),
        )
    if isinstance(value, (list, tuple)):
        return json.dumps([_normalize(item) for item in value], separators=(",", ":"))
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _version_key(version: str | None) -> str:
    """Sort key that places a higher declared source version first.

    Versions are compared as zero-padded dotted integers where possible, so ``2`` sorts
    after ``10`` correctly. An absent version sorts last, because an unversioned
    observation never outranks a versioned one.
    """
    if not version:
        return "~"
    parts = version.replace("-", ".").split(".")
    padded = [part.rjust(8, "0") if part.isdigit() else part for part in parts]
    # Invert so that a higher version yields a smaller key.
    return "".join(
        chr(0x10FFFF - ord(character)) if character.isdigit() else character
        for character in ".".join(padded)
    )


def _as_date_text(value: object) -> str | None:
    """Return the date portion of a resolved value, when it has one."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:10]


def _hash(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
