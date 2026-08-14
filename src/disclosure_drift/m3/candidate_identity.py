"""The OR-1 candidate-snapshot identity graph (accepted Decision 067 §§7, 9).

Every digest here is a call into the accepted ``release/hashing.py`` ``hash_table``
primitive. There is **no second hashing implementation, no parallel normalization, and
no alternative encoder** (M3.3 contract §10.1; Decision 021 §5): this module fixes the
domain names, the ordered field tuples, and the row scopes, and delegates all rendering
to :func:`~disclosure_drift.release.hashing.normalize_value`.

The graph is acyclic and is computed strictly bottom-up:

``coverage_window_sha256`` and ``input_observation_set_sha256`` -> ``snapshot_id``;
``evidence_sha256`` -> ``contributing_evidence_sha256`` -> the eight
``*_resolution_sha256`` columns -> the seven ``candidate_*_sha256`` family digests ->
``candidate_snapshot_sha256``. ``snapshot_id`` is excluded from all seven family
digests (**OQ-4**) and bound exactly once, in ``candidate_snapshot_sha256``.

``input_observation_set_sha256`` is **definitionally identical** to Decision 021 §8.1's
``source_observation_set_sha256`` (Decision 067 §9.1), so it is not redefined here: it
is the accepted :func:`release.pilot_manifest.source_observation_set_sha256`, re-exported
under its candidate-layer name so a caller cannot reach for a second derivation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.release.hashing import hash_table, normalize_value
from disclosure_drift.release.pilot_manifest import (
    SourceObservation,
    render_canonical_json,
    source_observation_set_sha256,
    structural_fingerprint_sha256,
)

__all__ = [
    "ACCESSION_EVIDENCE_COLUMNS",
    "ACCESSION_REASONS_COLUMNS",
    "ACCESSION_TABLE_COLUMNS",
    "CLASSIFICATION_COLUMNS_BY_DIMENSION",
    "COMPOSITE_RESOLUTION_DIMENSIONS",
    "COVERAGE_WINDOW_FIELDS",
    "ENTITY_EVIDENCE_COLUMNS",
    "ENTITY_REASONS_COLUMNS",
    "ENTITY_TABLE_COLUMNS",
    "EVIDENCE_PREIMAGE_FIELDS",
    "REGISTRANT_TABLE_COLUMNS",
    "RESOLUTION_DIMENSIONS",
    "RESOLUTION_EVIDENCE_COLUMNS",
    "RESOLUTION_PREIMAGE_FIELDS",
    "SNAPSHOT_CONTENT_FIELDS",
    "SNAPSHOT_IDENTITY_FIELDS",
    "CandidateEvidenceRow",
    "SourceObservation",
    "candidate_accession_evidence_sha256",
    "candidate_accession_reasons_sha256",
    "candidate_accession_table_sha256",
    "candidate_entity_evidence_sha256",
    "candidate_entity_reasons_sha256",
    "candidate_entity_table_sha256",
    "candidate_registrant_table_sha256",
    "candidate_snapshot_sha256",
    "contributing_evidence_sha256",
    "coverage_window_sha256",
    "evidence_sha256",
    "input_observation_set_sha256",
    "resolution_contributors",
    "resolution_sha256",
    "resolved_value_rendering",
    "snapshot_identity_sha256",
    "structural_fingerprint_sha256",
]

# --------------------------------------------------------------------------
# Domains. Every name below is a frozen ``hash_table`` domain and is never
# reused for a different preimage.
# --------------------------------------------------------------------------

_COVERAGE_WINDOW_DOMAIN: Final = "pilot_candidate_coverage_window"
_SNAPSHOT_IDENTITY_DOMAIN: Final = "pilot_candidate_snapshot_identity"
_SNAPSHOT_CONTENT_DOMAIN: Final = "pilot_candidate_snapshot_content"
_EVIDENCE_ROW_DOMAIN: Final = "pilot_candidate_evidence_row"
_RESOLUTION_EVIDENCE_DOMAIN: Final = "pilot_candidate_resolution_evidence"
_RESOLUTION_DOMAIN: Final = "pilot_candidate_resolution"

#: Decision 016 §1's five coverage-window inputs (GR proposal §A.1, adopted by
#: Decision 067 §9). Single-row call shape, so the column order is ``sorted``.
COVERAGE_WINDOW_FIELDS: Final[tuple[str, ...]] = (
    "as_of_date",
    "coverage_end",
    "coverage_policy_version",
    "coverage_start",
    "include_open_quarter",
)

#: Decision 016 §1's ``snapshot_id`` inputs (§A.3). ``census_run_id`` is excluded
#: explicitly, as are every timestamp, both counts, and all nine content digests.
SNAPSHOT_IDENTITY_FIELDS: Final[tuple[str, ...]] = (
    "candidate_policy_version",
    "coverage_window_sha256",
    "evidence_policy_version",
    "input_observation_set_sha256",
    "sic_family_mapping_version",
)

#: §A.11's twelve fields. ``candidate_snapshot_sha256`` excludes itself, and this is
#: the one place ``snapshot_id`` enters a candidate digest (**OQ-4**).
SNAPSHOT_CONTENT_FIELDS: Final[tuple[str, ...]] = (
    "accession_count",
    "candidate_accession_evidence_sha256",
    "candidate_accession_reasons_sha256",
    "candidate_accession_table_sha256",
    "candidate_entity_evidence_sha256",
    "candidate_entity_reasons_sha256",
    "candidate_entity_table_sha256",
    "candidate_registrant_table_sha256",
    "coverage_window_sha256",
    "entity_count",
    "input_observation_set_sha256",
    "snapshot_id",
)

#: **R15 / Decision 016 §4, retained exactly.** No field is removed and no surrogate
#: identifier is substituted. Single-row call shape, so the order is ``sorted``.
EVIDENCE_PREIMAGE_FIELDS: Final[tuple[str, ...]] = (
    "canonical_observed_value",
    "classification_dimension",
    "evidence_role",
    "parsed_record_id",
    "policy_version",
    "precedence",
    "source_field",
    "source_observation_id",
)

#: Decision 067 §7.2 step 1, multi-row, at exactly the stated field order.
RESOLUTION_EVIDENCE_COLUMNS: Final[tuple[str, ...]] = (
    "evidence_role",
    "precedence",
    "evidence_sha256",
)

#: Decision 067 §7.2 step 2, single-row, so the order is ``sorted``.
RESOLUTION_PREIMAGE_FIELDS: Final[tuple[str, ...]] = (
    "classification_dimension",
    "contributing_evidence_sha256",
    "evidence_policy_version",
    "resolved_value",
)

#: The eight columns Decision 067 §7.3 governs, keyed by their dimension.
RESOLUTION_DIMENSIONS: Final[Mapping[str, str]] = {
    "size": "size_resolution_sha256",
    "industry": "industry_resolution_sha256",
    "history": "history_resolution_sha256",
    "primary_universe": "primary_universe_resolution_sha256",
    "filing_date": "filing_date_resolution_sha256",
    "cohort": "cohort_resolution_sha256",
    "xbrl": "xbrl_resolution_sha256",
    "amendment_purpose": "amendment_purpose_resolution_sha256",
}

#: The persisted candidate classification column(s) each dimension resolves, which is
#: what Decision 067 §7.2's ``resolved_value`` renders. Seven dimensions are paired
#: with exactly one column by migration ``0009``'s own
#: ``(value IS NULL) = (hash IS NULL)`` checks. ``xbrl`` is the exception: ``0009``
#: ties its hash to the *evidence level* rather than to one flag, because the XBRL
#: classification is both flags, so both are bound rather than one silently dropped.
CLASSIFICATION_COLUMNS_BY_DIMENSION: Final[Mapping[str, tuple[str, ...]]] = {
    "size": ("size_stratum",),
    "industry": ("industry_family",),
    "history": ("history_class",),
    "primary_universe": ("primary_universe_eligible",),
    "filing_date": ("official_filing_date",),
    "cohort": ("provisional_official_cohort",),
    "xbrl": ("has_xbrl", "has_inline_xbrl"),
    "amendment_purpose": ("amendment_purpose_category",),
}

#: **R21** (Decision 071 §8). The one dimension whose resolved value binds two persisted
#: governed facts, and therefore renders through the accepted canonical-JSON serializer
#: rather than as a bare scalar. Every other dimension keeps its exact canonical
#: persisted scalar.
COMPOSITE_RESOLUTION_DIMENSIONS: Final[frozenset[str]] = frozenset({"xbrl"})

# --------------------------------------------------------------------------
# The seven candidate-family digest tuples (GR proposal §§A.4-A.10, adopted).
# ``snapshot_id``, ``recorded_at_utc``, ``detail``, and ``evidence_id`` are excluded
# from every one of them.
# --------------------------------------------------------------------------

ENTITY_TABLE_COLUMNS: Final[tuple[str, ...]] = (
    "cik_numeric",
    "cik_padded",
    "entity_tie_break_sha256",
    "candidate_category",
    "control_kind",
    "size_stratum",
    "size_evidence_level",
    "size_resolution_sha256",
    "sic_code",
    "industry_family",
    "industry_quota_eligible",
    "industry_evidence_level",
    "industry_resolution_sha256",
    "history_class",
    "history_evidence_level",
    "history_resolution_sha256",
    "currently_inactive",
    "eligible_original_annual_report_count",
    "primary_universe_eligible",
    "primary_universe_evidence_level",
    "primary_universe_resolution_sha256",
    "engineering_only_stress",
    "filing_time_name",
)

ACCESSION_TABLE_COLUMNS: Final[tuple[str, ...]] = (
    "accession_plain",
    "accession_number_dashed",
    "accession_tie_break_sha256",
    "anchor_cik_numeric",
    "form_type",
    "is_amendment",
    "official_filing_date",
    "report_date",
    "acceptance_audit_date",
    "filing_date_evidence_level",
    "filing_date_resolution_sha256",
    "filing_date_precedence",
    "provisional_official_cohort",
    "acceptance_audit_cohort",
    "cohort_evidence_level",
    "cohort_resolution_sha256",
    "cohort_ambiguous",
    "has_xbrl",
    "has_inline_xbrl",
    "xbrl_evidence_level",
    "xbrl_resolution_sha256",
    "amendment_linkage_state",
    "provisional_parent_accession",
    "amendment_purpose_category",
    "amendment_purpose_evidence_level",
    "amendment_purpose_resolution_sha256",
    "amendment_purpose_quota_eligible",
    "base_eligible",
    "stress_eligible",
    "support_eligible",
    "control_eligible",
    "multi_registrant",
)

REGISTRANT_TABLE_COLUMNS: Final[tuple[str, ...]] = (
    "accession_plain",
    "registrant_cik_numeric",
    "registrant_cik_padded",
    "role",
    "is_anchor",
    "evidence_level",
)

ENTITY_EVIDENCE_COLUMNS: Final[tuple[str, ...]] = (
    "cik_numeric",
    "classification_dimension",
    "evidence_role",
    "source_field",
    "canonical_observed_value",
    "policy_version",
    "precedence",
    "evidence_sha256",
)

ACCESSION_EVIDENCE_COLUMNS: Final[tuple[str, ...]] = (
    "accession_plain",
    "classification_dimension",
    "evidence_role",
    "source_field",
    "canonical_observed_value",
    "policy_version",
    "precedence",
    "evidence_sha256",
)

ENTITY_REASONS_COLUMNS: Final[tuple[str, ...]] = (
    "cik_numeric",
    "reason_scope",
    "reason_code",
)

ACCESSION_REASONS_COLUMNS: Final[tuple[str, ...]] = (
    "accession_plain",
    "reason_scope",
    "reason_code",
)


@dataclass(frozen=True, slots=True)
class CandidateEvidenceRow:
    """One persisted candidate evidence row, at the fields identity depends on.

    ``evidence_id``, ``snapshot_id``, the parent key, ``recorded_at_utc``, and free
    text are deliberately absent: Decision 067 §7.1 excludes all of them, and a field
    that cannot be read here cannot leak into a digest.
    """

    classification_dimension: str
    evidence_role: str
    source_observation_id: str
    parsed_record_id: str | None
    source_field: str
    canonical_observed_value: str | None
    policy_version: str
    precedence: int

    def preimage(self) -> dict[str, object]:
        """The exact R15 eight-field preimage, and nothing else."""
        return {
            "canonical_observed_value": self.canonical_observed_value,
            "classification_dimension": self.classification_dimension,
            "evidence_role": self.evidence_role,
            "parsed_record_id": self.parsed_record_id,
            "policy_version": self.policy_version,
            "precedence": self.precedence,
            "source_field": self.source_field,
            "source_observation_id": self.source_observation_id,
        }

    @property
    def evidence_sha256(self) -> str:
        """This row's content identity (Decision 067 §7.1)."""
        return evidence_sha256(self)


def _single_row(domain: str, fields: Mapping[str, object]) -> str:
    """The accepted single-row call shape: keys sorted, one row."""
    return hash_table(domain, tuple(sorted(fields)), [fields]).normalized_content_sha256


def _rows(domain: str, columns: Sequence[str], rows: Iterable[Mapping[str, object]]) -> str:
    """The accepted multi-row call shape at a frozen ordered column tuple."""
    return hash_table(domain, columns, rows).normalized_content_sha256


def _require_fields(fields: Mapping[str, object], expected: Sequence[str], label: str) -> None:
    """Refuse a preimage whose key set is not exactly the frozen tuple."""
    if tuple(sorted(fields)) != tuple(expected):
        message = f"{label} preimage must carry exactly {list(expected)}; received {sorted(fields)}"
        raise GateFailureError(message)


# --------------------------------------------------------------------------
# Layer 1: the snapshot's own inputs
# --------------------------------------------------------------------------


def coverage_window_sha256(fields: Mapping[str, object]) -> str:
    """§A.1 -- the five coverage-window fields, single-row."""
    _require_fields(fields, COVERAGE_WINDOW_FIELDS, "coverage_window_sha256")
    return _single_row(_COVERAGE_WINDOW_DOMAIN, fields)


def input_observation_set_sha256(observations: Sequence[SourceObservation]) -> str:
    """§A.2 / Decision 067 §9.1 -- **definitionally** Decision 021 §8.1's digest.

    Delegated, never reimplemented: a second derivation over the same declared content
    is exactly the competing definition Decision 067 §9.1 forbids.
    """
    return source_observation_set_sha256(observations)


def snapshot_identity_sha256(fields: Mapping[str, object]) -> str:
    """§A.3 -- ``snapshot_id``, single-row over exactly five inputs."""
    _require_fields(fields, SNAPSHOT_IDENTITY_FIELDS, "snapshot_id")
    return _single_row(_SNAPSHOT_IDENTITY_DOMAIN, fields)


# --------------------------------------------------------------------------
# Layer 2: evidence and resolution identity (R15, R16, R16-C1)
# --------------------------------------------------------------------------


def evidence_sha256(row: CandidateEvidenceRow) -> str:
    """R16 §7.1 -- content identity over R15's exact eight fields.

    ``canonical_observed_value`` is hashed in the representation already produced for
    persistence; this layer introduces no second substantive normalization, and a
    canonical ``NULL`` stays a canonical ``NULL``.
    """
    return _single_row(_EVIDENCE_ROW_DOMAIN, row.preimage())


def resolution_contributors(
    rows: Iterable[CandidateEvidenceRow],
) -> tuple[CandidateEvidenceRow, ...]:
    """**R16-C1** -- the one explicit deterministic contributor-membership function.

    ``rows`` are the persisted candidate evidence rows for one parent and one
    ``classification_dimension``. Membership mirrors the accepted deterministic
    resolution procedure (:func:`sec.accession_resolution.resolve_field`) applied at
    the candidate layer, per observed source field:

    1. group the dimension's rows by ``source_field`` -- resolution is per field, never
       by choosing a whole-record winner;
    2. keep only the rows at the **strongest** precedence in that group (Decision 010
       §4.1: a lower precedence is stronger). A weaker observation never contributes,
       and never creates a conflict;
    3. if those peers disagree on ``canonical_observed_value``, the field is
       **unresolved** and contributes **nothing** -- no value is guessed and no
       tie is broken;
    4. otherwise every peer contributes, ordered deterministically.

    It is therefore substantive rather than discretionary, is **never** inferred from
    ``evidence_role`` -- which appears in no filter here -- never admits an unrelated
    row merely for sharing the parent or the dimension, and is recomputable from
    persisted rows alone.
    """
    ordered = tuple(rows)
    dimensions = {row.classification_dimension for row in ordered}
    if len(dimensions) > 1:
        message = (
            "resolution contributors are selected within one classification dimension; "
            f"received {sorted(dimensions)}"
        )
        raise GateFailureError(message)
    contributors: list[CandidateEvidenceRow] = []
    for source_field in sorted({row.source_field for row in ordered}):
        group = [row for row in ordered if row.source_field == source_field]
        strongest = min(row.precedence for row in group)
        peers = [row for row in group if row.precedence == strongest]
        if len({row.canonical_observed_value for row in peers}) > 1:
            continue
        contributors.extend(peers)
    return tuple(
        sorted(
            contributors,
            key=lambda row: (row.precedence, row.evidence_role, row.evidence_sha256),
        )
    )


def contributing_evidence_sha256(contributors: Sequence[CandidateEvidenceRow]) -> str:
    """R16 §7.2 step 1 -- multi-row over ``(evidence_role, precedence, evidence_sha256)``."""
    return _rows(
        _RESOLUTION_EVIDENCE_DOMAIN,
        RESOLUTION_EVIDENCE_COLUMNS,
        [
            {
                "evidence_role": row.evidence_role,
                "precedence": row.precedence,
                "evidence_sha256": row.evidence_sha256,
            }
            for row in contributors
        ],
    )


def _canonical_flag(value: object) -> int | None:
    """One persisted nullable flag, as the canonical JSON value it is stored as."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    message = f"a persisted candidate flag must be an integer or NULL, got {value!r}"
    raise GateFailureError(message)


def resolved_value_rendering(dimension: str, classification: Mapping[str, object]) -> str:
    """The canonical persisted candidate classification value for one dimension.

    For the seven single-column dimensions this is literally that column's canonical
    value, rendered by the accepted :func:`normalize_value` and nothing else.

    ``xbrl`` binds two persisted governed facts, so **R21** fixes its logical resolved
    value as the canonical serialization of exactly ``{"has_inline_xbrl": ...,
    "has_xbrl": ...}`` through the repository's **existing accepted** canonical-JSON
    serializer (Decision 021 §13.5). No second serializer is created, and
    ``hash_table``'s internal unit separator is never used as an application-level
    encoding.
    """
    try:
        columns = CLASSIFICATION_COLUMNS_BY_DIMENSION[dimension]
    except KeyError:
        message = f"{dimension!r} is not one of the eight governed resolution dimensions"
        raise GateFailureError(message) from None
    missing = [column for column in columns if column not in classification]
    if missing:
        message = f"resolved value for {dimension!r} is missing column(s) {missing}"
        raise GateFailureError(message)
    if dimension in COMPOSITE_RESOLUTION_DIMENSIONS:
        return render_canonical_json(
            {column: _canonical_flag(classification[column]) for column in columns}
        )
    return normalize_value(classification[columns[0]])


def resolution_sha256(
    *,
    dimension: str,
    contributors: Sequence[CandidateEvidenceRow],
    evidence_policy_version: str,
    classification: Mapping[str, object],
) -> str:
    """R16 §7.2 step 2 -- one candidate-layer ``*_resolution_sha256``.

    The census accession ``resolution_sha256`` is **never** substituted for this
    (Decision 067 §10.7): this digest is computed here, from candidate evidence.
    """
    if dimension not in RESOLUTION_DIMENSIONS:
        message = f"{dimension!r} is not one of the eight governed resolution dimensions"
        raise GateFailureError(message)
    if not contributors:
        message = (
            f"a resolved {dimension!r} classification has no contributing candidate "
            "evidence; accepted evidence cannot establish it, so the snapshot is refused"
        )
        raise GateFailureError(message)
    fields = {
        "classification_dimension": dimension,
        "contributing_evidence_sha256": contributing_evidence_sha256(contributors),
        "evidence_policy_version": evidence_policy_version,
        "resolved_value": resolved_value_rendering(dimension, classification),
    }
    _require_fields(fields, RESOLUTION_PREIMAGE_FIELDS, "resolution_sha256")
    return _single_row(_RESOLUTION_DOMAIN, fields)


# --------------------------------------------------------------------------
# Layer 3: the seven candidate-family digests, then the snapshot content digest
# --------------------------------------------------------------------------


def candidate_entity_table_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """§A.4."""
    return _rows("pilot_candidate_entities", ENTITY_TABLE_COLUMNS, rows)


def candidate_accession_table_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """§A.5."""
    return _rows("pilot_candidate_accessions", ACCESSION_TABLE_COLUMNS, rows)


def candidate_registrant_table_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """§A.6."""
    return _rows("pilot_candidate_accession_registrants", REGISTRANT_TABLE_COLUMNS, rows)


def candidate_entity_evidence_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """§A.7."""
    return _rows("pilot_candidate_entity_evidence", ENTITY_EVIDENCE_COLUMNS, rows)


def candidate_accession_evidence_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """§A.8."""
    return _rows("pilot_candidate_accession_evidence", ACCESSION_EVIDENCE_COLUMNS, rows)


def candidate_entity_reasons_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """§A.9."""
    return _rows("pilot_candidate_entity_reasons", ENTITY_REASONS_COLUMNS, rows)


def candidate_accession_reasons_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """§A.10."""
    return _rows("pilot_candidate_accession_reasons", ACCESSION_REASONS_COLUMNS, rows)


def candidate_snapshot_sha256(fields: Mapping[str, object]) -> str:
    """§A.11 -- the terminal candidate identity, single-row over twelve fields.

    It excludes itself, ``census_run_id``, ``snapshot_state``, every timestamp, and
    every free-text field, so the graph stays acyclic.
    """
    _require_fields(fields, SNAPSHOT_CONTENT_FIELDS, "candidate_snapshot_sha256")
    return _single_row(_SNAPSHOT_CONTENT_DOMAIN, fields)
