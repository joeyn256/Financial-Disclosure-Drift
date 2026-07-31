"""Deterministic pilot-manifest construction (Decision 021, Stage M2.3-S6).

Pure, in-memory, and side-effect free: this module opens no database, reads no
clock, touches no filesystem, consults no environment variable, invokes no Git,
and never reads ``sys.version`` (Decision 021 sections 8.4 and 21). Persistence,
row loading, and verification against a catalog live in
:mod:`disclosure_drift.sec.pilot_manifest_store`.

Every digest is computed with the existing primitives in
:mod:`disclosure_drift.release.hashing`, reused exactly as Decision 013 section 7
requires. **No second hashing implementation, no parallel normalization, and no
alternative canonical-JSON encoder exists here** (Decision 021 section 5).

The frozen column tuples below are normative in the order shown: reordering one
changes its digest. Where a tuple omits ``recorded_at_utc``, ``detail``, a path,
a timestamp, or an operational event ID, that omission is normative rather than
incidental (Decision 016 section 8; Decision 021 section 5).

This module builds the pilot manifest, which is a **distinct artifact** from the
SEC-inventory release manifest: it never reuses ``ReleaseManifest``,
``build_manifest``, or ``RELEASE_SCHEMA_VERSION`` from
:mod:`disclosure_drift.release.manifest` (Decision 021 section 13.6).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.reasons import reason
from disclosure_drift.release.hashing import hash_table, normalize_value

__all__ = [
    "ACCEPTED_RESERVE_RANK",
    "ACCESSION_CANDIDATE_FIELDS",
    "ACCESSION_DERIVED_FIELDS",
    "ACCESSION_REGISTRANT_RECORD_COLUMNS",
    "CANDIDATE_REASON_RECORD_COLUMNS",
    "CANDIDATE_TABLE_FIELDS",
    "CONSUMED_POLICY_KEYS",
    "CROSSWALK",
    "DOCUMENT_FIELD_BINDINGS",
    "ENTITY_CANDIDATE_FIELDS",
    "ENTITY_EVIDENCE_RECORD_COLUMNS",
    "LEAKAGE_ATTESTATION",
    "MANIFEST_STATE_LITERAL",
    "NAME_CHANGE_FLAG_FIELDS",
    "NOT_APPLICABLE_WITHOUT_RESERVE_PACKAGE",
    "NO_COMPATIBLE_RESERVE_REASON_CODE",
    "OPERATIONAL_ENVELOPE_FIELDS",
    "REQUIRED_DECISION_AUTHORITY_RECORDS",
    "RUN_STATE_LITERAL",
    "SNAPSHOT_STATE_LITERAL",
    "STRUCTURAL_FINGERPRINT_COLUMNS",
    "RESERVE_DISPOSITION_SCOPE",
    "AccessionRecordSources",
    "CrosswalkItem",
    "EntityRecordSources",
    "ExplicitArguments",
    "FieldBinding",
    "ManifestComponents",
    "ManifestIdentity",
    "ReserveCoverage",
    "SourceObservation",
    "build_manifest_document",
    "candidate_tables_sha256",
    "crosswalk_totals",
    "document_leaf_bindings",
    "manifest_filename",
    "manifest_identifier",
    "quota_definitions_sha256",
    "quota_report_sha256",
    "render_canonical_json",
    "reserve_coverage",
    "reserves_sha256",
    "root_manifest_sha256",
    "selected_accessions_sha256",
    "selected_entities_sha256",
    "selection_result_sha256",
    "selector_policy_sha256",
    "source_observation_set_sha256",
    "structural_fingerprint_sha256",
    "verify_document_crosswalk_coverage",
]

# --------------------------------------------------------------------------
# Frozen literals (Decision 021 sections 6.2, 8.2, 8.4, 13.2.2)
# --------------------------------------------------------------------------

#: Decision 021 section 6.2: the result digest is defined only for a feasible run.
RUN_STATE_LITERAL: Final = "feasible"
#: Decision 021 section 8.2: the candidate digest is defined only for a frozen snapshot.
SNAPSHOT_STATE_LITERAL: Final = "frozen"
#: Decision 021 section 13.2.2: Stage S6 builds only the proposed-manifest schema.
MANIFEST_STATE_LITERAL: Final = "proposed"
#: Decision 021 section 8.4: records which attestation was made; it does not prove it.
LEAKAGE_ATTESTATION: Final = "no-outcome-no-filing-text-no-companyfacts/1.0"

#: Decision 020 section 7.1 and migration ``0012``: the only reserve-scope disposition, read
#: from the accepted registry rather than restated, so the two cannot drift apart.
NO_COMPATIBLE_RESERVE_REASON_CODE: Final = reason("REVIEW_PILOT_NO_COMPATIBLE_RESERVE").code
#: Migration ``0012``'s ``reason_scope`` CHECK admits exactly this scope.
RESERVE_DISPOSITION_SCOPE: Final = "reserve"
#: Migration ``0012``'s feasible-transition trigger requires every reserve package to be rank 1,
#: which is the accepted ``reserve_selector.RESERVE_RANK``. Asserted equal in the S6 suite.
ACCEPTED_RESERVE_RANK: Final = 1

#: Decision 022: crosswalk item 46's reserve rank is applicable **once per persisted reserve
#: package**. Where the accepted S5.4 methodology produced no package for a target, the target
#: carries a ``REVIEW_PILOT_NO_COMPATIBLE_RESERVE`` disposition instead and there is no rank to
#: record, so with no packages at all the item is structurally not applicable rather than missing.
#: This is the complete set of items that structural non-applicability can reach; every other
#: ``D`` and ``T`` item stays unconditionally required.
NOT_APPLICABLE_WITHOUT_RESERVE_PACKAGE: Final[frozenset[int]] = frozenset({46})

#: Decision 021 section 8.4: the nine consumed ``reference_policy_versions`` keys.
CONSUMED_POLICY_KEYS: Final[tuple[str, ...]] = (
    "pilot_candidate",
    "pilot_evidence",
    "pilot_sic_family_mapping",
    "pilot_selector",
    "pilot_joint_selector",
    "pilot_quota",
    "pilot_replacement_signature",
    "pilot_manifest_hash",
    "pilot_primary_universe_boundary",
)

# --------------------------------------------------------------------------
# Frozen column tuples (Decision 021 sections 7, 8)
# --------------------------------------------------------------------------

SELECTED_ENTITY_COLUMNS: Final[tuple[str, ...]] = (
    "selection_run_id",
    "snapshot_id",
    "cik_numeric",
    "selected_order",
    "entity_hash_sha256",
    "entity_role",
    "candidate_category",
    "size_stratum",
    "industry_family",
    "history_class",
    "control_kind",
)

SELECTED_ACCESSION_COLUMNS: Final[tuple[str, ...]] = (
    "selection_run_id",
    "snapshot_id",
    "accession_plain",
    "anchor_cik_numeric",
    "selected_order",
    "accession_hash_sha256",
    "accession_role",
)

QUOTA_RESULT_COLUMNS: Final[tuple[str, ...]] = (
    "quota_result_id",
    "selection_run_id",
    "snapshot_id",
    "quota_dimension",
    "quota_key",
    "comparison_operator",
    "required_count",
    "achieved_count",
    "eligible_pool_count",
    "excluded_pool_count",
    "evidence_state",
    "quota_result",
    "binding_constraint",
    "binding_evidence_sha256",
)

ENTITY_CONTRIBUTION_COLUMNS: Final[tuple[str, ...]] = (
    "selection_run_id",
    "snapshot_id",
    "cik_numeric",
    "quota_dimension",
    "quota_key",
)

ACCESSION_CONTRIBUTION_COLUMNS: Final[tuple[str, ...]] = (
    "selection_run_id",
    "snapshot_id",
    "accession_plain",
    "quota_dimension",
    "quota_key",
)

QUOTA_MEMBER_COLUMNS: Final[tuple[str, ...]] = (
    "quota_result_id",
    "selection_run_id",
    "snapshot_id",
    "member_order",
    "member_kind",
    "cik_numeric",
    "accession_plain",
)

RESERVE_COLUMNS: Final[tuple[str, ...]] = (
    "reserve_package_id",
    "selection_run_id",
    "snapshot_id",
    "target_cik_numeric",
    "replacement_cik_numeric",
    "reserve_rank",
    "replaces_signature_sha256",
    "reserve_signature_sha256",
    "signature_policy_version",
    "quota_policy_version",
    "reserve_tie_break_sha256",
    "evidence_floor",
)

RESERVE_ACCESSION_COLUMNS: Final[tuple[str, ...]] = (
    "reserve_package_id",
    "selection_run_id",
    "snapshot_id",
    "accession_plain",
    "accession_role",
    "accession_order",
    "accession_hash_sha256",
)

RESERVE_CONTRIBUTION_COLUMNS: Final[tuple[str, ...]] = (
    "reserve_package_id",
    "selection_run_id",
    "snapshot_id",
    "quota_dimension",
    "quota_key",
)

RESERVE_DISPOSITION_COLUMNS: Final[tuple[str, ...]] = (
    "selection_run_id",
    "snapshot_id",
    "cik_numeric",
    "reason_scope",
    "reason_code",
)

SOURCE_OBSERVATION_CONTENT_COLUMNS: Final[tuple[str, ...]] = (
    "source_id",
    "request_identity",
    "logical_sha256",
    "parser_version",
    "schema_fingerprint_sha256",
    "outcome",
)

# --------------------------------------------------------------------------
# Document-only record projections (Decision 021 section 13.2 blocks 8 and 9)
#
# These tuples render values; they are **not** digest preimages and no digest is
# computed over them. Each name below is required by a named section 13.2.1 item
# and is read from the reconstruction source that item records. Decision 021
# section 13.3 forbids serializing a value no digest commits, so nothing is listed
# here that the crosswalk does not require.
# --------------------------------------------------------------------------

#: Block 8, per selected entity, read from ``pilot_candidate_entities`` -- the
#: reconstruction source recorded for items 31, 36, 38, 40, 41, and 43.
#: ``filing_time_name`` is deliberately absent: item 42 rules that names never enter a
#: hash or an ordering decision, so the document does not carry one either.
ENTITY_CANDIDATE_FIELDS: Final[tuple[str, ...]] = (
    "cik_padded",  # item 31
    "size_evidence_level",  # items 38, 43
    "industry_evidence_level",  # items 36, 43
    "industry_quota_eligible",  # item 36
    "history_evidence_level",  # item 43
    "primary_universe_evidence_level",  # item 43
    "currently_inactive",  # items 40, 41
    "engineering_only_stress",  # item 40
    "eligible_original_annual_report_count",  # item 40
)

#: Block 8, the six Decision 019 section 8 derived flags item 42 requires. They are read
#: from the accepted S5 ``EntityCandidate.name_change`` record, which is the accepted
#: derivation from ``pilot_candidate_entity_evidence``; Stage S6 re-derives none of them.
NAME_CHANGE_FLAG_FIELDS: Final[tuple[str, ...]] = (
    "name_change_has_identity_evidence",
    "name_change_evidence_role",
    "name_change_evidence_level",
    "name_change_former_name_record_parseable",
    "name_change_has_prior_current_or_from_to",
    "name_change_ticker_change_claimed",
)

#: Block 8, one classification-dimension evidence record (items 36, 38, 41, 42). The
#: column list is the accepted evidence-content shape minus its owner key, which is the
#: entity the record is nested under. ``evidence_id``, ``source_observation_id``, and
#: ``recorded_at_utc`` are per-row identity and timestamps, excluded as a class.
ENTITY_EVIDENCE_RECORD_COLUMNS: Final[tuple[str, ...]] = (
    "classification_dimension",
    "evidence_role",
    "source_field",
    "canonical_observed_value",
    "policy_version",
    "precedence",
    "parsed_record_id",
    "evidence_sha256",
)

#: Blocks 8 and 9, one candidate reason row (item 44), at the accepted reason-content
#: shape minus its owner key. ``detail`` and ``recorded_at_utc`` stay out.
CANDIDATE_REASON_RECORD_COLUMNS: Final[tuple[str, ...]] = ("reason_scope", "reason_code")

#: Block 9, per selected accession, read from ``pilot_candidate_accessions`` -- the
#: reconstruction source recorded for items 47, 50-60, and 63. The ``stored_`` prefixes
#: name the persisted column, distinguishing it from the Decision 019 derived value of
#: the same concept below, exactly as the accepted accession-content record does.
ACCESSION_CANDIDATE_FIELDS: Final[tuple[str, ...]] = (
    "accession_number_dashed",  # item 47
    "form_type",  # item 50
    "is_amendment",  # item 51
    "amendment_purpose_category",  # item 51
    "amendment_purpose_quota_eligible",  # item 51
    "official_filing_date",  # items 52, 58
    "acceptance_audit_date",  # items 53, 58
    "report_date",  # items 54, 55
    "provisional_official_cohort",  # items 56, 58
    "cohort_ambiguous",  # item 56
    "acceptance_audit_cohort",  # items 57, 58
    "filing_date_precedence",  # item 58
    "stored_amendment_linkage_state",  # item 59
    "stored_provisional_parent_accession",  # item 59
    "filing_date_evidence_level",  # item 63
    "stored_cohort_evidence_level",  # item 63
    "xbrl_evidence_level",  # item 63
    "stored_amendment_purpose_evidence_level",  # items 60, 63
    "has_xbrl",  # block 9
    "has_inline_xbrl",  # block 9
    "multi_registrant",  # item 49
)

#: Block 9, the Decision 019 derived values read from the accepted S5
#: ``AccessionCandidate``. Together with the four stored levels above these are the eight
#: ``*_evidence_level`` values item 63 enumerates. Stage S6 derives none of them.
ACCESSION_DERIVED_FIELDS: Final[tuple[str, ...]] = (
    "cohort_applicability",  # item 56
    "cohort_evidence_level",  # item 63
    "amendment_purpose_evidence_level",  # items 60, 63
    "amendment_linkage_evidence_level",  # items 60, 63
    "multi_registrant_evidence_level",  # item 63
    "provisional_parent_accession_dashed",  # item 59
)

#: Block 9, one per-accession registrant record (item 49), read from
#: ``pilot_candidate_accession_registrants``. ``recorded_at_utc`` stays out.
ACCESSION_REGISTRANT_RECORD_COLUMNS: Final[tuple[str, ...]] = (
    "registrant_cik_numeric",
    "registrant_cik_padded",
    "role",
    "is_anchor",
    "evidence_level",
)

#: Decision 021 sections 5 and 13.4: excluded from every digest and therefore, under the
#: section 13.3 completeness rule, from the document's substantive body as well. Asserted
#: by name so a projection that starts carrying one fails closed rather than leaking it.
OPERATIONAL_ENVELOPE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "recorded_at_utc",
        "generated_at_utc",
        "retrieved_at_utc",
        "applied_at_utc",
        "started_at_utc",
        "finished_at_utc",
        "frozen_at_utc",
        "created_at_utc",
        "invalidated_at_utc",
        "approved_at_utc",
        "rejected_at_utc",
        "superseded_at_utc",
        "approval_reference",
        "approved_root_sha256",
        "relative_manifest_path",
        "detail",
    }
)

#: Decision 021 section 8.4: items 14 and 58 are committed through
#: ``decision_authority_sha256`` **and nowhere else**, so the enumerated authority set is
#: only load-bearing if it actually names the record that fixes them. Decision 010 section
#: 5.2 fixes both the ``America/New_York`` zone and the 17:30 cutoff, so its record must be
#: present. Nothing further is required here: the record enumerates no other mandatory
#: member, and requiring one would be policy this module does not own.
REQUIRED_DECISION_AUTHORITY_RECORDS: Final[tuple[str, ...]] = (
    "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md",
)

#: Decision 021 section 8.1, frozen at v0.3. **This is the only structural-fingerprint
#: tuple.** The withdrawn three-column form must not appear anywhere, and no fallback
#: and no second fingerprint methodology exists.
STRUCTURAL_FINGERPRINT_COLUMNS: Final[tuple[str, ...]] = (
    "region",
    "state",
    "observed_type",
    "member_name",
    "record_path",
)

#: Decision 021 section 8.2: the frozen snapshot's own twenty-two fields.
CANDIDATE_TABLE_FIELDS: Final[tuple[str, ...]] = (
    "snapshot_id",
    "snapshot_state",
    "coverage_start",
    "coverage_end",
    "as_of_date",
    "include_open_quarter",
    "coverage_policy_version",
    "candidate_policy_version",
    "sic_family_mapping_version",
    "evidence_policy_version",
    "coverage_window_sha256",
    "input_observation_set_sha256",
    "candidate_entity_table_sha256",
    "candidate_accession_table_sha256",
    "candidate_registrant_table_sha256",
    "candidate_entity_evidence_sha256",
    "candidate_accession_evidence_sha256",
    "candidate_entity_reasons_sha256",
    "candidate_accession_reasons_sha256",
    "candidate_snapshot_sha256",
    "entity_count",
    "accession_count",
)

QUOTA_DEFINITION_COLUMNS: Final[tuple[str, ...]] = (
    "quota_dimension",
    "quota_key",
    "comparison_operator",
    "required_count",
)

POLICY_VERSION_COLUMNS: Final[tuple[str, ...]] = ("policy_key", "policy_version")

MIGRATION_CHAIN_COLUMNS: Final[tuple[str, ...]] = ("version", "name", "checksum_sha256")


# --------------------------------------------------------------------------
# Shared digest shapes (Decision 021 section 5)
# --------------------------------------------------------------------------


def _rows_digest(
    table_name: str, columns: Sequence[str], rows: Iterable[Mapping[str, object]]
) -> str:
    """Multi-row family digest at a frozen column tuple."""
    return hash_table(table_name, columns, rows).normalized_content_sha256


def _fields_digest(name: str, fields: Mapping[str, object]) -> str:
    """Single-row combination digest over named scalar fields, sorted by key."""
    return hash_table(name, tuple(sorted(fields)), [fields]).normalized_content_sha256


def _require_text(value: object, label: str) -> str:
    """Return a non-empty string argument or fail closed (Decision 021 section 8.4)."""
    if not isinstance(value, str) or not value.strip():
        message = f"{label} must be a non-empty string supplied explicitly by the caller"
        raise GateFailureError(message)
    return value


def _is_lower_hex(value: str) -> bool:
    """Whether every character is a lowercase hexadecimal digit."""
    return all(character in "0123456789abcdef" for character in value)


def _validated_authority_identifier(entry: object) -> str:
    """Validate one ``(decision record, content sha256)`` pair and return its identifier.

    The parameter is typed ``object`` deliberately: the declared field type describes what
    a correct caller supplies, and this function exists precisely for the callers that do
    not. Every structural check therefore runs at run time rather than being narrowed away.
    """
    if not isinstance(entry, tuple) or len(entry) != 2:
        message = (
            "each decision-authority record must be a "
            f"(record identifier, content sha256) pair; got {entry!r}"
        )
        raise GateFailureError(message)
    raw_identifier, digest = entry
    identifier = _require_text(raw_identifier, "decision-authority record identifier")
    if identifier.startswith("/") or ".." in identifier:
        message = (
            f"decision-authority record identifier {identifier!r} must be a relative "
            "repository path; no absolute path may appear in the manifest"
        )
        raise GateFailureError(message)
    if not isinstance(digest, str) or len(digest) != 64 or not _is_lower_hex(digest):
        message = (
            f"decision-authority record {identifier!r} must carry a 64-character "
            f"lowercase hexadecimal content digest; got {digest!r}"
        )
        raise GateFailureError(message)
    return identifier


# --------------------------------------------------------------------------
# Structural fingerprint (Decision 021 section 8.1)
# --------------------------------------------------------------------------


def structural_fingerprint_sha256(
    structural_rows: Iterable[Mapping[str, object]],
) -> str:
    """Derive ``schema_fingerprint_sha256`` for one cited source observation.

    The frozen seven-step rule, verbatim from Decision 021 section 8.1:

    1. partition the observation's ``census_structural_observations`` rows by
       ``parser_run_id``;
    2. normalize every value with :func:`normalize_value`, unchanged and not
       reimplemented, so ``NULL_SENTINEL`` keeps a SQL ``NULL`` distinct from the
       empty string in both the comparison and the digest;
    3. reduce each parser run to the distinct set of normalized five-column tuples,
       which is what makes a duplicate identical row and any retrieval ordering a
       no-op;
    4. require every parser run's set to be exactly equal;
    5. raise :class:`GateFailureError` when they differ -- **never** unioned,
       intersected, averaged, majority-voted, resolved by preferring a parser run, or
       silently discarded;
    6. hash the common distinct set exactly once at the normative column order;
    7. exclude ``parser_run_id``, which is the partition key for the consistency
       check and never enters the digest.

    An observation with no structural rows contributes the digest of the empty row
    set -- deterministic, and distinct from any populated shape.
    """
    by_run: dict[str, set[tuple[str, ...]]] = {}
    for row in structural_rows:
        parser_run_id = row.get("parser_run_id")
        if not isinstance(parser_run_id, str) or not parser_run_id:
            message = (
                "census_structural_observations row is missing its parser_run_id partition key"
            )
            raise GateFailureError(message)
        rendered = tuple(
            normalize_value(row.get(column)) for column in STRUCTURAL_FINGERPRINT_COLUMNS
        )
        by_run.setdefault(parser_run_id, set()).add(rendered)

    if not by_run:
        common: set[tuple[str, ...]] = set()
    else:
        runs = sorted(by_run)
        common = by_run[runs[0]]
        for parser_run_id in runs[1:]:
            if by_run[parser_run_id] != common:
                message = (
                    "structural parser runs disagree on the frozen "
                    f"{STRUCTURAL_FINGERPRINT_COLUMNS} shape for one source observation "
                    f"({runs[0]!r} versus {parser_run_id!r}); a structural divergence is never "
                    "unioned, intersected, averaged, majority-voted, resolved by preferring a "
                    "parser run, or discarded"
                )
                raise GateFailureError(message)

    rows = [dict(zip(STRUCTURAL_FINGERPRINT_COLUMNS, shape, strict=True)) for shape in common]
    return _rows_digest("census_structural_observation_shape", STRUCTURAL_FINGERPRINT_COLUMNS, rows)


@dataclass(frozen=True, slots=True)
class SourceObservation:
    """One cited ``census_source_observations`` row and its structural rows.

    Carries exactly Decision 016 section 8's source-content hash input list, and
    nothing else. ``observation_id``, timestamps, URL and redirect trace, headers and
    validators, transport and storage digests, sizes, representation, path, free text,
    and the five residual columns are all excluded by Decision 021 section 8.1.
    """

    source_id: str
    request_identity: str
    logical_sha256: str
    parser_version: str
    outcome: str
    structural_rows: tuple[Mapping[str, object], ...] = ()

    def content_row(self) -> dict[str, object]:
        """The six hashed fields, with the fingerprint derived from step 6 above."""
        return {
            "source_id": self.source_id,
            "request_identity": self.request_identity,
            "logical_sha256": self.logical_sha256,
            "parser_version": self.parser_version,
            "schema_fingerprint_sha256": structural_fingerprint_sha256(self.structural_rows),
            "outcome": self.outcome,
        }


def source_observation_set_sha256(observations: Sequence[SourceObservation]) -> str:
    """Layer 1 -- the cited observation set (Decision 021 section 8.1)."""
    return _rows_digest(
        "census_source_observation_content",
        SOURCE_OBSERVATION_CONTENT_COLUMNS,
        [observation.content_row() for observation in observations],
    )


# --------------------------------------------------------------------------
# Terminal component digests (Decision 021 section 7)
# --------------------------------------------------------------------------


def selected_entities_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """Layer 5 -- every selected entity at the frozen eleven columns (section 7.1)."""
    return _rows_digest("pilot_selected_entities", SELECTED_ENTITY_COLUMNS, rows)


def selected_accessions_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """Layer 6 -- every selected accession at the frozen seven columns (section 7.2)."""
    return _rows_digest("pilot_selected_accessions", SELECTED_ACCESSION_COLUMNS, rows)


def quota_report_sha256(
    *,
    quota_results: Iterable[Mapping[str, object]],
    entity_contributions: Iterable[Mapping[str, object]],
    accession_contributions: Iterable[Mapping[str, object]],
    quota_members: Iterable[Mapping[str, object]],
) -> str:
    """Layer 8 -- four sub-digests combined by one single-row digest (section 7.3)."""
    combined = {
        "quota_results": _rows_digest("pilot_quota_results", QUOTA_RESULT_COLUMNS, quota_results),
        "entity_contributions": _rows_digest(
            "pilot_selected_entity_quota_contributions",
            ENTITY_CONTRIBUTION_COLUMNS,
            entity_contributions,
        ),
        "accession_contributions": _rows_digest(
            "pilot_selected_accession_quota_contributions",
            ACCESSION_CONTRIBUTION_COLUMNS,
            accession_contributions,
        ),
        "quota_members": _rows_digest(
            "pilot_quota_result_members", QUOTA_MEMBER_COLUMNS, quota_members
        ),
    }
    return _fields_digest("pilot_quota_report", combined)


def reserves_sha256(
    *,
    reserves: Iterable[Mapping[str, object]],
    reserve_accessions: Iterable[Mapping[str, object]],
    reserve_contributions: Iterable[Mapping[str, object]],
    reserve_dispositions: Iterable[Mapping[str, object]],
) -> str:
    """Layer 7 -- packages, child rows, and the migration-0012 dispositions (section 7.4).

    Reserve child rows are hashed directly even though ``reserve_package_id`` already
    binds them through its own content-derived preimage: the redundancy localizes a
    corruption to the family that carries it. The dispositions are inside this digest
    so that "which targets have no reserve" is an approved fact rather than an
    inference.
    """
    combined = {
        "reserves": _rows_digest("pilot_reserves", RESERVE_COLUMNS, reserves),
        "reserve_accessions": _rows_digest(
            "pilot_reserve_accessions", RESERVE_ACCESSION_COLUMNS, reserve_accessions
        ),
        "reserve_contributions": _rows_digest(
            "pilot_reserve_quota_contributions",
            RESERVE_CONTRIBUTION_COLUMNS,
            reserve_contributions,
        ),
        "reserve_dispositions": _rows_digest(
            "pilot_selection_entity_reasons", RESERVE_DISPOSITION_COLUMNS, reserve_dispositions
        ),
    }
    return _fields_digest("pilot_reserve_report", combined)


# --------------------------------------------------------------------------
# Remaining component digests (Decision 021 sections 8.2, 8.3, 8.4)
# --------------------------------------------------------------------------


def candidate_tables_sha256(snapshot: Mapping[str, object]) -> str:
    """Layer 2 -- the frozen snapshot's own twenty-two fields (section 8.2).

    ``snapshot_state`` is the fixed literal ``"frozen"``: the implementation asserts
    the snapshot is frozen and fails closed otherwise, then contributes the constant,
    so a later invalidation never retroactively changes a manifest's candidate digest.
    ``census_run_id`` is excluded exactly as Decision 016 section 1 excludes it from
    ``snapshot_id``.
    """
    observed_state = snapshot.get("snapshot_state")
    if observed_state != SNAPSHOT_STATE_LITERAL:
        message = (
            "candidate_tables_sha256 is defined only for a frozen candidate snapshot; "
            f"snapshot_state is {observed_state!r}"
        )
        raise GateFailureError(message)
    fields = {name: snapshot.get(name) for name in CANDIDATE_TABLE_FIELDS}
    fields["snapshot_state"] = SNAPSHOT_STATE_LITERAL
    return _fields_digest("pilot_candidate_tables", fields)


def quota_definitions_sha256(
    *, quota_policy_version: str, quota_results: Iterable[Mapping[str, object]]
) -> str:
    """Layer 3 -- what was *required*, independently of what was achieved (section 8.3)."""
    content = _rows_digest("pilot_quota_definition_rows", QUOTA_DEFINITION_COLUMNS, quota_results)
    return _fields_digest(
        "pilot_quota_definitions",
        {
            "quota_policy_version": quota_policy_version,
            "quota_definitions_content_sha256": content,
        },
    )


@dataclass(frozen=True, slots=True)
class ExplicitArguments:
    """The six caller-supplied identity values Decision 021 section 8.4 requires.

    **All six are frozen inputs supplied by the caller.** This module must not invoke
    Git, read ``.git``, shell out, consult environment variables, read ``sys.version``,
    inspect the working tree, or otherwise infer build, runtime, configuration,
    authority, or plan identity. A missing or malformed value is a
    :class:`GateFailureError`, which keeps each one an auditable, deliberately supplied
    assertion rather than a property of whatever tree, interpreter, or shell happened
    to be present.
    """

    dependency_lock_sha256: str
    code_commit_identifier: str
    runtime_python_version: str
    configuration_sha256: str
    decision_authority_sha256: str
    source_plan_sha256: str
    #: The enumerated ``(decision record identifier, content sha256)`` pairs
    #: ``decision_authority_sha256`` covers. Block 4 serializes them and crosswalk item
    #: 11 records them as its own reconstruction source, so there is no default: an
    #: unstated authority set is a missing assertion, not an empty one.
    decision_authority_records: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        """Fail closed on any missing or malformed explicit argument."""
        for label in (
            "dependency_lock_sha256",
            "code_commit_identifier",
            "runtime_python_version",
            "configuration_sha256",
            "decision_authority_sha256",
            "source_plan_sha256",
        ):
            _require_text(getattr(self, label), f"ExplicitArguments.{label}")
        self._validate_authority_records()

    def _validate_authority_records(self) -> None:
        """Validate the enumerated authority set (Decision 021 sections 8.4 and 13.2).

        Every pair is checked structurally, the set is required to be unique and in
        canonical order, and the records whose rulings nothing else binds are required to
        be present. Nothing is inferred: no Git call, no filesystem read, no environment
        lookup, and no interpreter introspection happens here or anywhere in this module.
        """
        records = self.decision_authority_records
        if not isinstance(records, tuple) or not records:
            message = (
                "ExplicitArguments.decision_authority_records must enumerate the "
                "(decision record, content sha256) pairs decision_authority_sha256 covers; "
                "an empty authority set leaves milestone-plan items 11, 14, and 58 unbound"
            )
            raise GateFailureError(message)
        seen: list[str] = []
        for entry in records:
            identifier = _validated_authority_identifier(entry)
            if identifier in seen:
                message = (
                    f"decision-authority record {identifier!r} is enumerated more than once; a "
                    "duplicate or conflicting authority record is refused, never merged"
                )
                raise GateFailureError(message)
            seen.append(identifier)
        if seen != sorted(seen):
            message = (
                "decision-authority records must be supplied in canonical identifier order so "
                "the enumerated set has one rendering; expected " + repr(tuple(sorted(seen)))
            )
            raise GateFailureError(message)
        missing = tuple(
            record for record in REQUIRED_DECISION_AUTHORITY_RECORDS if record not in seen
        )
        if missing:
            message = (
                f"decision-authority records omit {missing}; Decision 021 section 8.4 commits "
                "the as-of time zone (item 14) and the after-hours state (item 58) through this "
                "set and nowhere else, so the record fixing them must be enumerated"
            )
            raise GateFailureError(message)


def selector_policy_sha256(
    *,
    policy_versions: Sequence[Mapping[str, object]],
    migration_chain: Sequence[Mapping[str, object]],
    selection_input_schema_version: str,
    manifest_schema_version: str,
    explicit: ExplicitArguments,
) -> str:
    """Layer 4 -- the manifest's policy and environment identity (section 8.4).

    Eleven fields exactly. ``reference_policy_versions.decision_record`` is excluded as
    a documentation pointer, and ``applied_at_utc`` is excluded from
    ``migration_chain_sha256`` like every other timestamp.
    """
    fields: dict[str, object] = {
        "policy_versions_sha256": _rows_digest(
            "reference_policy_versions_content", POLICY_VERSION_COLUMNS, policy_versions
        ),
        "selection_input_schema_version": selection_input_schema_version,
        "manifest_schema_version": manifest_schema_version,
        "migration_chain_sha256": _rows_digest(
            "ops_schema_migrations_content", MIGRATION_CHAIN_COLUMNS, migration_chain
        ),
        "dependency_lock_sha256": explicit.dependency_lock_sha256,
        "code_commit_identifier": explicit.code_commit_identifier,
        "runtime_python_version": explicit.runtime_python_version,
        "configuration_sha256": explicit.configuration_sha256,
        "decision_authority_sha256": explicit.decision_authority_sha256,
        "source_plan_sha256": explicit.source_plan_sha256,
        "leakage_attestation": LEAKAGE_ATTESTATION,
    }
    return _fields_digest("pilot_selector_policy", fields)


# --------------------------------------------------------------------------
# Result digest, root, and manifest identity (Decision 021 sections 6, 9, 9.1)
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ManifestComponents:
    """The eight component digests, in the Decision 013 section 7 layer order."""

    source_observation_set_sha256: str
    candidate_tables_sha256: str
    quota_definitions_sha256: str
    selector_policy_sha256: str
    selected_entities_sha256: str
    selected_accessions_sha256: str
    reserves_sha256: str
    quota_report_sha256: str


def selection_result_sha256(
    *,
    manifest_hash_policy_version: str,
    selection_run_id: str,
    snapshot_id: str,
    selection_input_sha256: str,
    selection_input_schema_version: str,
    run_state: str,
    selected_entity_count: int,
    selected_accession_count: int,
    expanded_node_count: object,
    node_limit_exhausted: object,
    components: ManifestComponents,
) -> str:
    """The terminal result digest over exactly fourteen fields (section 6.1).

    ``run_state`` is a fixed literal, not a read value: the run is asserted to be
    ``feasible`` and fails closed otherwise, then the constant is contributed, so a
    non-feasible run has no result digest at all rather than a differently-valued one.
    ``node_limit_exhausted`` is retained as a deliberate defensive constant so that a
    corrupted flag on a feasible row cannot pass unnoticed. ``search_node_limit``,
    ``selection_seed``, and both selector policy versions are not listed because they
    are already bound, exactly and without duplication, through
    ``selection_input_sha256``.
    """
    if run_state != RUN_STATE_LITERAL:
        message = (
            "selection_result_sha256 is defined only for a feasible selection run; "
            f"run_state is {run_state!r}"
        )
        raise GateFailureError(message)
    fields: dict[str, object] = {
        "manifest_hash_policy_version": manifest_hash_policy_version,
        "selection_run_id": selection_run_id,
        "snapshot_id": snapshot_id,
        "selection_input_sha256": selection_input_sha256,
        "selection_input_schema_version": selection_input_schema_version,
        "run_state": RUN_STATE_LITERAL,
        "selected_entity_count": selected_entity_count,
        "selected_accession_count": selected_accession_count,
        "expanded_node_count": expanded_node_count,
        "node_limit_exhausted": node_limit_exhausted,
        "selected_entities_sha256": components.selected_entities_sha256,
        "selected_accessions_sha256": components.selected_accessions_sha256,
        "quota_report_sha256": components.quota_report_sha256,
        "reserves_sha256": components.reserves_sha256,
    }
    return _fields_digest("pilot_selection_result", fields)


def root_manifest_sha256(
    *,
    manifest_schema_version: str,
    selection_run_id: str,
    snapshot_id: str,
    selection_result: str,
    components: ManifestComponents,
) -> str:
    """The root over exactly twelve fields (section 9).

    ``ordinal_version``, ``manifest_state``, every approval field,
    ``supersedes_manifest_id``, ``relative_manifest_path``, ``generated_at_utc``,
    ``detail``, ``manifest_id``, and every event ID are excluded normatively. The four
    terminal components appear here and again inside ``selection_result_sha256``: a
    deliberate diamond, not a cycle, so the root binds terminal content directly.
    """
    fields: dict[str, object] = {
        "manifest_schema_version": manifest_schema_version,
        "selection_run_id": selection_run_id,
        "snapshot_id": snapshot_id,
        "selection_result_sha256": selection_result,
        "source_observation_set_sha256": components.source_observation_set_sha256,
        "candidate_tables_sha256": components.candidate_tables_sha256,
        "quota_definitions_sha256": components.quota_definitions_sha256,
        "selector_policy_sha256": components.selector_policy_sha256,
        "selected_entities_sha256": components.selected_entities_sha256,
        "selected_accessions_sha256": components.selected_accessions_sha256,
        "reserves_sha256": components.reserves_sha256,
        "quota_report_sha256": components.quota_report_sha256,
    }
    return _fields_digest("pilot_root_manifest", fields)


def manifest_identifier(
    *, root_sha256: str, ordinal_version: int, supersedes_manifest_id: str | None
) -> str:
    """Derive the content-derived ``manifest_id`` (section 9.1).

    Exactly ``{root_manifest_sha256, ordinal_version, supersedes_manifest_id}``, with
    ``NULL_SENTINEL`` for an absent predecessor. This keeps ``manifest_id`` downstream
    of the root so no cycle forms, and lets two ordinal versions over one run be
    distinct rows even when their root content matches.
    """
    fields: dict[str, object] = {
        "root_manifest_sha256": root_sha256,
        "ordinal_version": ordinal_version,
        "supersedes_manifest_id": supersedes_manifest_id,
    }
    return _fields_digest("pilot_manifest_identity", fields)


@dataclass(frozen=True, slots=True)
class ManifestIdentity:
    """The identity a built manifest carries, all six fields fixed at INSERT."""

    manifest_id: str
    manifest_schema_version: str
    selection_run_id: str
    snapshot_id: str
    ordinal_version: int
    supersedes_manifest_id: str | None


def manifest_filename(root_sha256: str) -> str:
    """The content-derived filename (section 13.5)."""
    return f"pilot_manifest_{root_sha256}.json"


# --------------------------------------------------------------------------
# The milestone-plan section 10 crosswalk (Decision 021 section 13.2.1)
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CrosswalkItem:
    """One atomic milestone-plan section 10 requirement and where it lands.

    ``classification`` is exactly one of ``D`` (included directly -- a named field of a
    sections 6-9 preimage), ``T`` (included transitively through a named component
    digest, and serialized at the granularity section 10 requires), ``X``
    (operationally excluded by Decision 016 section 8, not serialized), or ``S9``
    (deferred to Stage S9 under an existing owner ruling). No fifth category exists and
    no item is unclassified.
    """

    number: int
    requirement: str
    group: str
    blocks: tuple[int, ...]
    classification: str


_Item = CrosswalkItem

#: Decision 021 section 13.2.1, frozen. Milestone plan section 10 contains 74 original
#: bullets; seven of them are compound and split into two requirements each, producing
#: **74 original bullets producing 81 atomic requirements** (74 + 7 = 81). Adding, moving,
#: or reclassifying an item is an owner-level act.
CROSSWALK: Final[tuple[CrosswalkItem, ...]] = (
    _Item(1, "manifest schema version", "Manifest identity", (1,), "D"),
    _Item(2, "manifest version (ordinal_version)", "Manifest identity", (1,), "D"),
    _Item(
        3,
        "status (proposed / owner-approved / rejected / superseded)",
        "Manifest identity",
        (1,),
        "T",
    ),
    _Item(4, "selection seed", "Manifest identity", (13,), "T"),
    _Item(5, "selection-policy version", "Manifest identity", (4,), "T"),
    _Item(6, "quota-policy version", "Manifest identity", (4,), "D"),
    _Item(7, "selector code commit", "Manifest identity", (3,), "D"),
    _Item(8, "Python version", "Manifest identity", (3,), "D"),
    _Item(9, "dependency-lock hash", "Manifest identity", (3,), "D"),
    _Item(10, "migration versions and checksums", "Manifest identity", (5,), "T"),
    _Item(11, "active decision-record hashes", "Manifest identity", (4,), "T"),
    _Item(12, "configuration hash", "Manifest identity", (3,), "D"),
    _Item(13, "as-of date", "Manifest identity", (7,), "D"),
    _Item(14, "as-of time zone", "Manifest identity", (7,), "T"),
    _Item(15, "source-plan hash", "Manifest identity", (6,), "D"),
    _Item(16, "candidate-pool hash", "Manifest identity", (7,), "D"),
    _Item(17, "source ID", "Source provenance", (6,), "D"),
    _Item(18, "source URL identity or approved source key", "Source provenance", (6,), "D"),
    _Item(19, "source observation ID", "Source provenance", (), "X"),
    _Item(20, "retrieval attempt ID", "Source provenance", (), "X"),
    _Item(21, "retrieved-at UTC", "Source provenance", (), "X"),
    _Item(22, "HTTP validator metadata", "Source provenance", (), "X"),
    _Item(23, "transport hash", "Source provenance", (), "X"),
    _Item(24, "decoded-content hash", "Source provenance", (6,), "D"),
    _Item(25, "stored-object hash", "Source provenance", (), "X"),
    _Item(26, "relative storage path", "Source provenance", (), "X"),
    _Item(27, "parser version", "Source provenance", (6,), "D"),
    _Item(28, "parser status", "Source provenance", (6,), "D"),
    _Item(29, "schema fingerprint", "Source provenance", (6,), "D"),
    _Item(30, "supersession lineage", "Source provenance", (), "X"),
    _Item(31, "padded CIK", "Entity records", (8,), "T"),
    _Item(32, "numeric CIK", "Entity records", (8,), "D"),
    _Item(33, "entity role", "Entity records", (8,), "D"),
    _Item(34, "operating or control classification", "Entity records", (8,), "D"),
    _Item(35, "industry family", "Entity records", (8,), "D"),
    _Item(36, "industry evidence basis", "Entity records", (8,), "T"),
    _Item(37, "filer-size category", "Entity records", (8,), "D"),
    _Item(38, "filer-size evidence basis", "Entity records", (8,), "T"),
    _Item(39, "history category", "Entity records", (8,), "D"),
    _Item(40, "event flags", "Entity records", (8, 11), "T"),
    _Item(41, "current-status evidence", "Entity records", (8,), "T"),
    _Item(42, "alias evidence", "Entity records", (8,), "T"),
    _Item(43, "provisional flags", "Entity records", (8,), "T"),
    _Item(44, "review reasons", "Entity records", (8, 12), "T"),
    _Item(45, "deterministic entity hash", "Entity records", (8,), "D"),
    _Item(46, "reserve rank", "Entity records", (12,), "D"),
    _Item(47, "canonical accession number", "Accession records", (9,), "D"),
    _Item(48, "anchor CIK", "Accession records", (9,), "D"),
    _Item(49, "registrant CIK relationships", "Accession records", (9,), "T"),
    _Item(50, "form", "Accession records", (9,), "T"),
    _Item(51, "original or amendment role", "Accession records", (9,), "T"),
    _Item(52, "official filing date", "Accession records", (9,), "T"),
    _Item(53, "acceptance timestamps", "Accession records", (9,), "T"),
    _Item(54, "report date", "Accession records", (9,), "T"),
    _Item(55, "fiscal year end", "Accession records", (9, 11), "T"),
    _Item(56, "official cohort", "Accession records", (9,), "T"),
    _Item(57, "acceptance audit cohort", "Accession records", (9,), "T"),
    _Item(58, "after-hours state", "Accession records", (9,), "T"),
    _Item(59, "amendment parent", "Accession records", (9,), "T"),
    _Item(60, "amendment evidence state", "Accession records", (9,), "T"),
    _Item(61, "base, stress, support, or control role", "Accession records", (9,), "D"),
    _Item(62, "cross-cutting quotas satisfied", "Accession records", (11,), "D"),
    _Item(63, "provisional-verification requirements", "Accession records", (9,), "T"),
    _Item(64, "deterministic accession hash", "Accession records", (9,), "D"),
    _Item(65, "required value", "Quota report", (10,), "D"),
    _Item(66, "achieved value", "Quota report", (10,), "D"),
    _Item(67, "selected members", "Quota report", (11,), "D"),
    _Item(68, "evidence level", "Quota report", (10,), "D"),
    _Item(69, "provisional count", "Quota report", (13,), "T"),
    _Item(70, "reserve coverage", "Quota report", (12,), "D"),
    _Item(71, "pass, fail, or unproven", "Quota report", (10,), "D"),
    _Item(72, "reason for failure", "Quota report", (10,), "D"),
    _Item(73, "canonical SQL/query or selector-input version", "Reconstruction fields", (13,), "D"),
    _Item(74, "candidate-table row counts", "Reconstruction fields", (13,), "D"),
    _Item(75, "selected-table row counts", "Reconstruction fields", (13,), "D"),
    _Item(76, "exclusion counts by reason", "Reconstruction fields", (13,), "T"),
    _Item(77, "unresolved counts", "Reconstruction fields", (13,), "T"),
    _Item(78, "input hashes", "Reconstruction fields", (2, 13), "D"),
    _Item(79, "output hashes", "Reconstruction fields", (2,), "D"),
    _Item(
        80,
        "command invocation with no personal path or SEC identity",
        "Reconstruction fields",
        (),
        "S9",
    ),
    _Item(
        81,
        "confirmation that no prohibited data source was read",
        "Reconstruction fields",
        (13,),
        "D",
    ),
)


def crosswalk_totals() -> dict[str, int]:
    """The frozen machine-checkable count (Decision 021 section 13.2.1)."""
    totals = {
        "total_section_10_items": len(CROSSWALK),
        "directly_included": sum(1 for item in CROSSWALK if item.classification == "D"),
        "transitively_included": sum(1 for item in CROSSWALK if item.classification == "T"),
        "operationally_excluded": sum(1 for item in CROSSWALK if item.classification == "X"),
        "deferred_to_s9": sum(1 for item in CROSSWALK if item.classification == "S9"),
        "deferred_to_s10": sum(1 for item in CROSSWALK if item.classification == "S10"),
    }
    classified = (
        totals["directly_included"]
        + totals["transitively_included"]
        + totals["operationally_excluded"]
        + totals["deferred_to_s9"]
        + totals["deferred_to_s10"]
    )
    totals["unclassified"] = totals["total_section_10_items"] - classified
    return totals


# --------------------------------------------------------------------------
# The pilot-manifest document (Decision 021 section 13)
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReconstructionFacts:
    """Block 13 -- historical reconstruction values read from persisted rows.

    The two candidate-table counts are the snapshot's **declared** ``entity_count`` and
    ``accession_count``: crosswalk item 74 records ``pilot_candidate_snapshots`` as its
    reconstruction source and ``candidate_tables_sha256`` names those two fields, so a
    separately recounted value would be a different number bound by nothing. The store
    validates the declarations against the actual row counts and fails closed on a
    disagreement rather than silently preferring either.
    """

    selection_seed: str
    selection_input_sha256: str
    selection_input_schema_version: str
    declared_candidate_entity_count: int
    declared_candidate_accession_count: int
    selected_table_row_counts: Mapping[str, int]
    exclusion_counts_by_reason_code: Mapping[str, int]
    unresolved_quota_count: int
    provisional_quota_count: int


@dataclass(frozen=True, slots=True)
class EntityRecordSources:
    """The block-8 values a selected entity carries beyond its section 7.1 columns.

    Every member is read from the reconstruction source the section 13.2.1 rows record:
    ``candidate`` from ``pilot_candidate_entities`` (items 31, 36, 38, 40, 41, 43),
    ``evidence`` from ``pilot_candidate_entity_evidence`` (items 36, 38, 41, 42),
    ``reasons`` from ``pilot_candidate_entity_reasons`` (item 44), and ``name_change``
    from the accepted S5 ``EntityCandidate.name_change`` derivation (item 42).
    """

    candidate: Mapping[str, object]
    name_change: Mapping[str, object]
    evidence: tuple[Mapping[str, object], ...]
    reasons: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class AccessionRecordSources:
    """The block-9 values a selected accession carries beyond its section 7.2 columns.

    ``candidate`` is the persisted ``pilot_candidate_accessions`` row (items 47, 50-60,
    63), ``derived`` the accepted S5 ``AccessionCandidate`` values Decision 019 maps from
    it (items 56, 59, 60, 63), and ``registrants`` the per-accession
    ``pilot_candidate_accession_registrants`` rows (item 49).
    """

    candidate: Mapping[str, object]
    derived: Mapping[str, object]
    registrants: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class ManifestSources:
    """Every persisted row family the document renders, as read from the catalog."""

    snapshot: Mapping[str, object]
    observations: tuple[SourceObservation, ...]
    policy_versions: tuple[Mapping[str, object], ...]
    migration_chain: tuple[Mapping[str, object], ...]
    selected_entities: tuple[Mapping[str, object], ...]
    selected_accessions: tuple[Mapping[str, object], ...]
    quota_results: tuple[Mapping[str, object], ...]
    entity_contributions: tuple[Mapping[str, object], ...]
    accession_contributions: tuple[Mapping[str, object], ...]
    quota_members: tuple[Mapping[str, object], ...]
    reserves: tuple[Mapping[str, object], ...]
    reserve_accessions: tuple[Mapping[str, object], ...]
    reserve_contributions: tuple[Mapping[str, object], ...]
    reserve_dispositions: tuple[Mapping[str, object], ...]
    reconstruction: ReconstructionFacts
    #: Keyed by ``cik_numeric`` and ``accession_plain`` respectively.
    entity_record_sources: Mapping[int, EntityRecordSources]
    accession_record_sources: Mapping[str, AccessionRecordSources]
    #: Crosswalk item 14, whose reconstruction source is Decision 010 section 5.2 and
    #: ``sec/calendar.py``; supplied as the accepted code constant, never inferred.
    as_of_timezone: str


def _projected(
    rows: Iterable[Mapping[str, object]], columns: Sequence[str]
) -> list[dict[str, object]]:
    """Render rows at a frozen column tuple, dropping every unhashed column."""
    return [{column: row.get(column) for column in columns} for row in rows]


def _ordered_by_record(
    rows: Iterable[Mapping[str, object]], columns: Sequence[str]
) -> list[dict[str, object]]:
    """Project rows and order them by their complete normalized rendering.

    Decision 021 section 13.5 requires arrays in deterministic order. Ordering on the
    whole rendered record -- rather than on one chosen key -- is the same rule
    ``hash_table`` already applies before digesting, so array order is independent of
    SQLite retrieval order without introducing a second ordering convention.
    """
    projected = _projected(rows, columns)
    return sorted(projected, key=lambda row: tuple(normalize_value(row[name]) for name in columns))


def _selected_order(row: Mapping[str, object], where: str) -> int:
    """Narrow one ``selected_order`` cell, failing closed on a malformed value.

    ``selected_order`` is an ``INTEGER NOT NULL CHECK (selected_order >= 1)`` column, so
    anything else in the rendered row is corrupted storage rather than an ordering
    question. ``bool`` is rejected explicitly because it is an ``int`` subclass.
    """
    value = row.get("selected_order")
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        message = (
            f"{where} carries a malformed selected_order {value!r}; a selected row's order is a "
            "positive integer and is never inferred, coerced, or defaulted"
        )
        raise GateFailureError(message)
    return value


def _ordered_by_selected_order(
    rows: Iterable[Mapping[str, object]], where: str
) -> list[Mapping[str, object]]:
    """Order selected rows by numeric ``selected_order`` (Decision 021 section 13.2).

    Blocks 8 and 9 are fixed as "ordered by ``selected_order``". The value is an integer,
    so it is ordered as one: rendering it as text first would sort 10 before 2 and put the
    frozen twenty-four-entity pilot out of its own selection order. A duplicate order is
    refused rather than resolved, because two rows claiming one position is corrupted
    storage that ``UNIQUE (selection_run_id, snapshot_id, selected_order)`` exists to
    prevent.
    """
    materialized = list(rows)
    seen: set[int] = set()
    for row in materialized:
        order = _selected_order(row, where)
        if order in seen:
            message = (
                f"{where} carries duplicate selected_order {order}; the document orders selected "
                "rows by a unique position and never collapses or reorders a collision"
            )
            raise GateFailureError(message)
        seen.add(order)
    return sorted(materialized, key=lambda row: _selected_order(row, where))


def _ordered_observations(
    observations: Sequence[SourceObservation],
) -> list[dict[str, object]]:
    """Cited observation content rows in deterministic order (section 13.5)."""
    rendered: list[dict[str, object]] = [observation.content_row() for observation in observations]
    return _sorted_by(rendered, ("source_id", "request_identity"))


def _sorted_by(rows: list[dict[str, object]], keys: Sequence[str]) -> list[dict[str, object]]:
    """Sort rendered rows by the normalized rendering of the named keys."""
    return sorted(rows, key=lambda row: tuple(normalize_value(row.get(key)) for key in keys))


def _one_projected(
    row: Mapping[str, object], columns: Sequence[str], where: str
) -> dict[str, object]:
    """Project one mapping at a frozen field tuple, failing closed on a missing name.

    ``_projected`` tolerates an absent column because a hashed row renders a SQL ``NULL``
    through ``NULL_SENTINEL``. A document record is different: a field the crosswalk
    requires must be *present*, so an absent key is corrupted or truncated input rather
    than a null value, and it is refused here instead of rendering as one.
    """
    missing = tuple(name for name in columns if name not in row)
    if missing:
        message = f"{where} is missing required document fields {missing}"
        raise GateFailureError(message)
    leaked = tuple(name for name in columns if name in OPERATIONAL_ENVELOPE_FIELDS)
    if leaked:
        message = (
            f"{where} would serialize the operational-envelope fields {leaked}, which Decision "
            "021 sections 5 and 13.4 exclude from every digest and from the substantive document"
        )
        raise GateFailureError(message)
    return {name: row[name] for name in columns}


def _entity_document_record(
    selected: Mapping[str, object], extra: Mapping[int, EntityRecordSources]
) -> dict[str, object]:
    """One block-8 record: the section 7.1 columns plus every item the crosswalk adds."""
    cik = selected.get("cik_numeric")
    if not isinstance(cik, int) or isinstance(cik, bool):
        message = f"selected entity carries a malformed cik_numeric {cik!r}"
        raise GateFailureError(message)
    if cik not in extra:
        message = (
            f"selected entity {cik} has no pilot_candidate_entities record to render its "
            "milestone-plan entity-record items from; the manifest is refused rather than "
            "serialized with a partial entity"
        )
        raise GateFailureError(message)
    source = extra[cik]
    record = _one_projected(selected, SELECTED_ENTITY_COLUMNS, f"selected entity {cik}")
    record.update(
        _one_projected(source.candidate, ENTITY_CANDIDATE_FIELDS, f"candidate entity {cik}")
    )
    record.update(
        _one_projected(source.name_change, NAME_CHANGE_FLAG_FIELDS, f"entity {cik} name change")
    )
    record["classification_evidence"] = _ordered_by_record(
        source.evidence, ENTITY_EVIDENCE_RECORD_COLUMNS
    )
    record["candidate_reasons"] = _ordered_by_record(
        source.reasons, CANDIDATE_REASON_RECORD_COLUMNS
    )
    return record


def _accession_document_record(
    selected: Mapping[str, object], extra: Mapping[str, AccessionRecordSources]
) -> dict[str, object]:
    """One block-9 record: the section 7.2 columns plus every item the crosswalk adds."""
    plain = selected.get("accession_plain")
    if not isinstance(plain, str) or not plain:
        message = f"selected accession carries a malformed accession_plain {plain!r}"
        raise GateFailureError(message)
    if plain not in extra:
        message = (
            f"selected accession {plain!r} has no pilot_candidate_accessions record to render its "
            "milestone-plan accession-record items from; the manifest is refused rather than "
            "serialized with a partial accession"
        )
        raise GateFailureError(message)
    source = extra[plain]
    record = _one_projected(selected, SELECTED_ACCESSION_COLUMNS, f"selected accession {plain!r}")
    record.update(
        _one_projected(source.candidate, ACCESSION_CANDIDATE_FIELDS, f"candidate {plain!r}")
    )
    record.update(_one_projected(source.derived, ACCESSION_DERIVED_FIELDS, f"derived {plain!r}"))
    record["registrants"] = _ordered_by_record(
        source.registrants, ACCESSION_REGISTRANT_RECORD_COLUMNS
    )
    return record


def build_manifest_document(
    *,
    identity: ManifestIdentity,
    components: ManifestComponents,
    root_sha256: str,
    selection_result: str,
    explicit: ExplicitArguments,
    sources: ManifestSources,
    quota_policy_version: str,
    manifest_state: str = MANIFEST_STATE_LITERAL,
) -> dict[str, object]:
    """Render the complete thirteen-block pilot-manifest document (section 13.2).

    Every value is either read from the persisted rows the digests were computed over
    or is one of the six explicit arguments section 8.4 requires: the document is a
    rendering, never a second source of truth. The operational envelope --
    ``relative_manifest_path``, ``generated_at_utc``, the approval fields, ``detail``,
    every ``recorded_at_utc``, and every event ID -- is excluded from the substantive
    body, and no absolute path and no SEC identity appears at any nesting depth
    (sections 13.3, 13.4). Selected rows are projected through the frozen field tuples
    rather than passed through whole, so a column the crosswalk does not name cannot
    reach the document by riding along on a ``SELECT *``.

    ``manifest_state`` is the fixed literal ``"proposed"``: Stage S6 builds only the
    proposed-manifest schema, so any other state is refused with ``GateFailureError``
    and the constant -- not the argument -- is what gets serialized (section 13.2.2).
    """
    if manifest_state != MANIFEST_STATE_LITERAL:
        message = (
            "Stage S6 builds only the proposed-manifest document schema; refusing to build one "
            f"for manifest_state {manifest_state!r}. Advancing a manifest past 'proposed' is an "
            "owner act outside the S6 implementation contract (Decision 021 sections 11.1, 13.2.2)"
        )
        raise GateFailureError(message)
    facts = sources.reconstruction
    document: dict[str, object] = {
        "manifest_identity": {
            "manifest_id": identity.manifest_id,
            "manifest_schema_version": identity.manifest_schema_version,
            "selection_run_id": identity.selection_run_id,
            "snapshot_id": identity.snapshot_id,
            "ordinal_version": identity.ordinal_version,
            "supersedes_manifest_id": identity.supersedes_manifest_id,
            "manifest_state": MANIFEST_STATE_LITERAL,
        },
        "hash_layers": {
            "source_observation_set_sha256": components.source_observation_set_sha256,
            "candidate_tables_sha256": components.candidate_tables_sha256,
            "quota_definitions_sha256": components.quota_definitions_sha256,
            "selector_policy_sha256": components.selector_policy_sha256,
            "selected_entities_sha256": components.selected_entities_sha256,
            "selected_accessions_sha256": components.selected_accessions_sha256,
            "reserves_sha256": components.reserves_sha256,
            "quota_report_sha256": components.quota_report_sha256,
            "selection_result_sha256": selection_result,
            "root_manifest_sha256": root_sha256,
        },
        "environment_identity": {
            "runtime_python_version": explicit.runtime_python_version,
            "dependency_lock_sha256": explicit.dependency_lock_sha256,
            "code_commit_identifier": explicit.code_commit_identifier,
            "configuration_sha256": explicit.configuration_sha256,
        },
        "active_authority": {
            "decision_authority_sha256": explicit.decision_authority_sha256,
            "decision_records": [
                {"decision_record": record, "content_sha256": digest}
                for record, digest in sorted(explicit.decision_authority_records)
            ],
            "policy_versions": _ordered_by_record(sources.policy_versions, POLICY_VERSION_COLUMNS),
        },
        "migration_chain": _projected(
            sorted(sources.migration_chain, key=lambda row: int(str(row.get("version")))),
            MIGRATION_CHAIN_COLUMNS,
        ),
        "source_plan_and_provenance": {
            "source_plan_sha256": explicit.source_plan_sha256,
            "cited_observations": _ordered_observations(sources.observations),
        },
        "candidate_snapshot": {
            **{name: sources.snapshot.get(name) for name in CANDIDATE_TABLE_FIELDS},
            "snapshot_state": SNAPSHOT_STATE_LITERAL,
            # Item 14: the EDGAR operating-calendar zone Decision 010 section 5.2 freezes,
            # supplied as the accepted code constant and bound through
            # decision_authority_sha256, never read from a clock or an environment.
            "as_of_timezone": sources.as_of_timezone,
        },
        "selected_entities": [
            _entity_document_record(row, sources.entity_record_sources)
            for row in _ordered_by_selected_order(
                sources.selected_entities, "pilot_selected_entities"
            )
        ],
        "selected_accessions": [
            _accession_document_record(row, sources.accession_record_sources)
            for row in _ordered_by_selected_order(
                sources.selected_accessions, "pilot_selected_accessions"
            )
        ],
        "quota_definitions_and_results": {
            "definitions": _ordered_by_record(sources.quota_results, QUOTA_DEFINITION_COLUMNS),
            "quota_policy_version": quota_policy_version,
            "results": _ordered_by_record(sources.quota_results, QUOTA_RESULT_COLUMNS),
        },
        "contributions_and_members": {
            "entity_contributions": _ordered_by_record(
                sources.entity_contributions, ENTITY_CONTRIBUTION_COLUMNS
            ),
            "accession_contributions": _ordered_by_record(
                sources.accession_contributions, ACCESSION_CONTRIBUTION_COLUMNS
            ),
            "quota_members": _ordered_by_record(sources.quota_members, QUOTA_MEMBER_COLUMNS),
        },
        "reserves": {
            "packages": _ordered_by_record(sources.reserves, RESERVE_COLUMNS),
            "reserve_accessions": _ordered_by_record(
                sources.reserve_accessions, RESERVE_ACCESSION_COLUMNS
            ),
            "reserve_contributions": _ordered_by_record(
                sources.reserve_contributions, RESERVE_CONTRIBUTION_COLUMNS
            ),
            "dispositions": _ordered_by_record(
                sources.reserve_dispositions, RESERVE_DISPOSITION_COLUMNS
            ),
        },
        "historical_reconstruction": {
            "selection_seed": facts.selection_seed,
            "selection_input_sha256": facts.selection_input_sha256,
            "selection_input_schema_version": facts.selection_input_schema_version,
            # Item 74: the snapshot's declared counts, which candidate_tables_sha256 names.
            "candidate_table_row_counts": {
                "pilot_candidate_accessions": facts.declared_candidate_accession_count,
                "pilot_candidate_entities": facts.declared_candidate_entity_count,
            },
            "selected_table_row_counts": dict(sorted(facts.selected_table_row_counts.items())),
            "exclusion_counts_by_reason_code": dict(
                sorted(facts.exclusion_counts_by_reason_code.items())
            ),
            "unresolved_quota_count": facts.unresolved_quota_count,
            "provisional_quota_count": facts.provisional_quota_count,
            "leakage_attestation": LEAKAGE_ATTESTATION,
        },
    }
    return document


#: Block name -> the section 13.2 block number it renders.
DOCUMENT_BLOCKS: Final[dict[str, int]] = {
    "manifest_identity": 1,
    "hash_layers": 2,
    "environment_identity": 3,
    "active_authority": 4,
    "migration_chain": 5,
    "source_plan_and_provenance": 6,
    "candidate_snapshot": 7,
    "selected_entities": 8,
    "selected_accessions": 9,
    "quota_definitions_and_results": 10,
    "contributions_and_members": 11,
    "reserves": 12,
    "historical_reconstruction": 13,
}


@dataclass(frozen=True, slots=True)
class FieldBinding:
    """The accepted binding of one serialized document leaf (Decision 021 section 13.3).

    ``digests`` names the digest or digests that commit this exact field; ``items`` names
    the milestone-plan section 10 requirements it discharges. ``items`` is empty only for
    a field section 13.2 requires as block content without section 10 enumerating it
    separately -- the manifest's own run and snapshot identity, for instance, which the
    root binds directly.
    """

    block: int
    digests: tuple[str, ...]
    items: tuple[int, ...] = ()


def _bind(
    target: dict[str, FieldBinding],
    prefix: str,
    columns: Sequence[str],
    *,
    block: int,
    digests: tuple[str, ...],
    items: tuple[int, ...] = (),
    per_field: Mapping[str, tuple[int, ...]] | None = None,
) -> None:
    """Register one binding per named field under ``prefix``."""
    for column in columns:
        numbers = (per_field or {}).get(column, items)
        target[f"{prefix}{column}"] = FieldBinding(block=block, digests=digests, items=numbers)


#: Per-field crosswalk item numbers for the block-8 candidate values.
_ENTITY_CANDIDATE_ITEMS: Final[dict[str, tuple[int, ...]]] = {
    "cik_padded": (31,),
    "size_evidence_level": (38, 43),
    "industry_evidence_level": (36, 43),
    "industry_quota_eligible": (36,),
    "history_evidence_level": (43,),
    "primary_universe_evidence_level": (43,),
    "currently_inactive": (40, 41),
    "engineering_only_stress": (40,),
    "eligible_original_annual_report_count": (40,),
}

#: Per-field crosswalk item numbers for the block-9 candidate and derived values.
_ACCESSION_CANDIDATE_ITEMS: Final[dict[str, tuple[int, ...]]] = {
    "accession_number_dashed": (47,),
    "form_type": (50,),
    "is_amendment": (51,),
    "amendment_purpose_category": (51,),
    "amendment_purpose_quota_eligible": (51,),
    "official_filing_date": (52, 58),
    "acceptance_audit_date": (53, 58),
    "report_date": (54, 55),
    "provisional_official_cohort": (56, 58),
    "cohort_ambiguous": (56,),
    "acceptance_audit_cohort": (57, 58),
    "filing_date_precedence": (58,),
    "stored_amendment_linkage_state": (59,),
    "stored_provisional_parent_accession": (59,),
    "filing_date_evidence_level": (63,),
    "stored_cohort_evidence_level": (63,),
    "xbrl_evidence_level": (63,),
    "stored_amendment_purpose_evidence_level": (60, 63),
    "has_xbrl": (63,),
    "has_inline_xbrl": (63,),
    "multi_registrant": (49,),
}
_ACCESSION_DERIVED_ITEMS: Final[dict[str, tuple[int, ...]]] = {
    "cohort_applicability": (56,),
    "cohort_evidence_level": (63,),
    "amendment_purpose_evidence_level": (60, 63),
    "amendment_linkage_evidence_level": (60, 63),
    "multi_registrant_evidence_level": (63,),
    "provisional_parent_accession_dashed": (59,),
}
_SELECTED_ENTITY_ITEMS: Final[dict[str, tuple[int, ...]]] = {
    "cik_numeric": (32,),
    "entity_role": (33,),
    "candidate_category": (34,),
    "control_kind": (34,),
    "industry_family": (35,),
    "size_stratum": (37,),
    "history_class": (39, 40),
    "entity_hash_sha256": (45,),
}
_SELECTED_ACCESSION_ITEMS: Final[dict[str, tuple[int, ...]]] = {
    "accession_plain": (47,),
    "anchor_cik_numeric": (48,),
    "accession_role": (61,),
    "accession_hash_sha256": (64,),
}
_CANDIDATE_SNAPSHOT_ITEMS: Final[dict[str, tuple[int, ...]]] = {
    "as_of_date": (13,),
    "candidate_snapshot_sha256": (16,),
    "entity_count": (74,),
    "accession_count": (74,),
}
_QUOTA_RESULT_ITEMS: Final[dict[str, tuple[int, ...]]] = {
    "required_count": (65,),
    "achieved_count": (66,),
    "evidence_state": (68, 69, 77),
    "quota_result": (71,),
    "binding_constraint": (72,),
    "binding_evidence_sha256": (72,),
}
_OBSERVATION_ITEMS: Final[dict[str, tuple[int, ...]]] = {
    "source_id": (17,),
    "request_identity": (18,),
    "logical_sha256": (24,),
    "parser_version": (27,),
    "outcome": (28,),
    "schema_fingerprint_sha256": (29,),
}


def _build_field_bindings() -> dict[str, FieldBinding]:
    """The accepted per-field binding table (Decision 021 sections 13.2, 13.2.1, 13.3).

    Field granularity is the point: under a block-level table any field added inside an
    existing block inherits that block's digests and is silently "bound", which is
    exactly what section 13.3's completeness obligation exists to prevent.
    """
    bindings: dict[str, FieldBinding] = {}
    root = ("root_manifest_sha256",)
    selector = ("selector_policy_sha256",)
    candidate = ("candidate_tables_sha256",)
    inputs = ("selection_input_sha256",)
    quota_report = ("quota_report_sha256",)

    # Block 1 -- manifest identity.
    bindings["manifest_identity.manifest_id"] = FieldBinding(1, ("manifest_id",), (79,))
    bindings["manifest_identity.manifest_schema_version"] = FieldBinding(
        1, ("root_manifest_sha256", "selector_policy_sha256"), (1,)
    )
    bindings["manifest_identity.selection_run_id"] = FieldBinding(1, root)
    bindings["manifest_identity.snapshot_id"] = FieldBinding(1, root)
    bindings["manifest_identity.ordinal_version"] = FieldBinding(1, ("manifest_id",), (2,))
    bindings["manifest_identity.supersedes_manifest_id"] = FieldBinding(1, ("manifest_id",))
    bindings["manifest_identity.manifest_state"] = FieldBinding(1, root, (3,))

    # Block 2 -- hash layers.
    for name in (
        "source_observation_set_sha256",
        "candidate_tables_sha256",
        "quota_definitions_sha256",
        "selector_policy_sha256",
        "selected_entities_sha256",
        "selected_accessions_sha256",
        "reserves_sha256",
        "quota_report_sha256",
        "selection_result_sha256",
    ):
        bindings[f"hash_layers.{name}"] = FieldBinding(2, root, (78,))
    bindings["hash_layers.root_manifest_sha256"] = FieldBinding(2, ("manifest_id",), (79,))

    # Block 3 -- environment and reproducibility identity.
    _bind(
        bindings,
        "environment_identity.",
        (
            "runtime_python_version",
            "dependency_lock_sha256",
            "code_commit_identifier",
            "configuration_sha256",
        ),
        block=3,
        digests=selector,
        per_field={
            "runtime_python_version": (8,),
            "dependency_lock_sha256": (9,),
            "code_commit_identifier": (7,),
            "configuration_sha256": (12,),
        },
    )

    # Block 4 -- active authority.
    bindings["active_authority.decision_authority_sha256"] = FieldBinding(4, selector, (11,))
    _bind(
        bindings,
        "active_authority.decision_records[].",
        ("decision_record", "content_sha256"),
        block=4,
        digests=selector,
        items=(11, 14, 58),
    )
    _bind(
        bindings,
        "active_authority.policy_versions[].",
        POLICY_VERSION_COLUMNS,
        block=4,
        digests=selector,
        items=(5, 6),
    )

    # Block 5 -- migration chain.
    _bind(
        bindings,
        "migration_chain[].",
        MIGRATION_CHAIN_COLUMNS,
        block=5,
        digests=selector,
        items=(10,),
    )

    # Block 6 -- source plan and per-source provenance.
    bindings["source_plan_and_provenance.source_plan_sha256"] = FieldBinding(6, selector, (15,))
    _bind(
        bindings,
        "source_plan_and_provenance.cited_observations[].",
        SOURCE_OBSERVATION_CONTENT_COLUMNS,
        block=6,
        digests=("source_observation_set_sha256",),
        per_field=_OBSERVATION_ITEMS,
    )

    # Block 7 -- candidate snapshot and candidate pool.
    _bind(
        bindings,
        "candidate_snapshot.",
        CANDIDATE_TABLE_FIELDS,
        block=7,
        digests=candidate,
        per_field=_CANDIDATE_SNAPSHOT_ITEMS,
    )
    bindings["candidate_snapshot.as_of_timezone"] = FieldBinding(7, selector, (14,))

    # Block 8 -- selected entity records.
    _bind(
        bindings,
        "selected_entities[].",
        SELECTED_ENTITY_COLUMNS,
        block=8,
        digests=("selected_entities_sha256",),
        per_field=_SELECTED_ENTITY_ITEMS,
    )
    _bind(
        bindings,
        "selected_entities[].",
        ENTITY_CANDIDATE_FIELDS,
        block=8,
        digests=("selection_input_sha256", "candidate_tables_sha256"),
        per_field=_ENTITY_CANDIDATE_ITEMS,
    )
    _bind(
        bindings,
        "selected_entities[].",
        NAME_CHANGE_FLAG_FIELDS,
        block=8,
        digests=inputs,
        items=(42,),
    )
    _bind(
        bindings,
        "selected_entities[].classification_evidence[].",
        ENTITY_EVIDENCE_RECORD_COLUMNS,
        block=8,
        digests=("selection_input_sha256", "candidate_tables_sha256"),
        items=(36, 38, 41, 42),
    )
    _bind(
        bindings,
        "selected_entities[].candidate_reasons[].",
        CANDIDATE_REASON_RECORD_COLUMNS,
        block=8,
        digests=("selection_input_sha256", "candidate_tables_sha256"),
        items=(44,),
    )

    # Block 9 -- selected accession records.
    _bind(
        bindings,
        "selected_accessions[].",
        SELECTED_ACCESSION_COLUMNS,
        block=9,
        digests=("selected_accessions_sha256",),
        per_field=_SELECTED_ACCESSION_ITEMS,
    )
    _bind(
        bindings,
        "selected_accessions[].",
        ACCESSION_CANDIDATE_FIELDS,
        block=9,
        digests=("selection_input_sha256", "candidate_tables_sha256"),
        per_field=_ACCESSION_CANDIDATE_ITEMS,
    )
    _bind(
        bindings,
        "selected_accessions[].",
        ACCESSION_DERIVED_FIELDS,
        block=9,
        digests=inputs,
        per_field=_ACCESSION_DERIVED_ITEMS,
    )
    _bind(
        bindings,
        "selected_accessions[].registrants[].",
        ACCESSION_REGISTRANT_RECORD_COLUMNS,
        block=9,
        digests=("selection_input_sha256", "candidate_tables_sha256"),
        items=(49,),
    )

    # Block 10 -- quota definitions and results.
    _bind(
        bindings,
        "quota_definitions_and_results.definitions[].",
        QUOTA_DEFINITION_COLUMNS,
        block=10,
        digests=("quota_definitions_sha256",),
        per_field={"required_count": (65,)},
    )
    bindings["quota_definitions_and_results.quota_policy_version"] = FieldBinding(
        10, ("quota_definitions_sha256",), (6,)
    )
    _bind(
        bindings,
        "quota_definitions_and_results.results[].",
        QUOTA_RESULT_COLUMNS,
        block=10,
        digests=quota_report,
        per_field=_QUOTA_RESULT_ITEMS,
    )

    # Block 11 -- contribution and member records.
    _bind(
        bindings,
        "contributions_and_members.entity_contributions[].",
        ENTITY_CONTRIBUTION_COLUMNS,
        block=11,
        digests=quota_report,
        items=(40, 55),
    )
    _bind(
        bindings,
        "contributions_and_members.accession_contributions[].",
        ACCESSION_CONTRIBUTION_COLUMNS,
        block=11,
        digests=quota_report,
        items=(62,),
    )
    _bind(
        bindings,
        "contributions_and_members.quota_members[].",
        QUOTA_MEMBER_COLUMNS,
        block=11,
        digests=quota_report,
        items=(67,),
    )

    # Block 12 -- reserve packages, child rows, and dispositions.
    _bind(
        bindings,
        "reserves.packages[].",
        RESERVE_COLUMNS,
        block=12,
        digests=("reserves_sha256",),
        per_field={"reserve_rank": (46, 70)},
    )
    _bind(
        bindings,
        "reserves.reserve_accessions[].",
        RESERVE_ACCESSION_COLUMNS,
        block=12,
        digests=("reserves_sha256",),
    )
    _bind(
        bindings,
        "reserves.reserve_contributions[].",
        RESERVE_CONTRIBUTION_COLUMNS,
        block=12,
        digests=("reserves_sha256",),
    )
    _bind(
        bindings,
        "reserves.dispositions[].",
        RESERVE_DISPOSITION_COLUMNS,
        block=12,
        digests=("reserves_sha256",),
        items=(44, 70),
    )

    # Block 13 -- historical reconstruction.
    bindings["historical_reconstruction.selection_seed"] = FieldBinding(13, inputs, (4,))
    bindings["historical_reconstruction.selection_input_sha256"] = FieldBinding(
        13, ("selection_result_sha256",), (78,)
    )
    bindings["historical_reconstruction.selection_input_schema_version"] = FieldBinding(
        13, ("selection_result_sha256", "selector_policy_sha256"), (73,)
    )
    for table in ("pilot_candidate_entities", "pilot_candidate_accessions"):
        bindings[f"historical_reconstruction.candidate_table_row_counts.{table}"] = FieldBinding(
            13, candidate, (74,)
        )
    for table in ("pilot_selected_entities", "pilot_selected_accessions"):
        bindings[f"historical_reconstruction.selected_table_row_counts.{table}"] = FieldBinding(
            13, ("selection_result_sha256",), (75,)
        )
    bindings["historical_reconstruction.exclusion_counts_by_reason_code.*"] = FieldBinding(
        13, ("candidate_tables_sha256", "selection_input_sha256"), (76,)
    )
    bindings["historical_reconstruction.unresolved_quota_count"] = FieldBinding(
        13, quota_report, (77,)
    )
    bindings["historical_reconstruction.provisional_quota_count"] = FieldBinding(
        13, quota_report, (69,)
    )
    bindings["historical_reconstruction.leakage_attestation"] = FieldBinding(13, selector, (81,))
    return bindings


#: Leaf path -> its accepted binding. Array indices are normalized to ``[]``, and the one
#: open-keyed map (exclusion counts, whose keys are reason codes) is normalized to ``*``.
DOCUMENT_FIELD_BINDINGS: Final[dict[str, FieldBinding]] = _build_field_bindings()

#: Paths whose trailing key is data rather than a schema field.
_OPEN_KEYED_PATHS: Final[tuple[str, ...]] = (
    "historical_reconstruction.exclusion_counts_by_reason_code",
)


def _normalized_leaf_path(path: str) -> str:
    """Collapse array indices, and open-keyed map keys, to their schema form."""
    collapsed = re.sub(r"\[\d+\]", "[]", path)
    for prefix in _OPEN_KEYED_PATHS:
        if collapsed.startswith(f"{prefix}."):
            return f"{prefix}.*"
    return collapsed


def document_leaf_bindings(document: Mapping[str, object]) -> dict[str, FieldBinding]:
    """Map every serialized leaf path to the binding of that exact field (section 13.3).

    Fails closed on a leaf the accepted table does not name. Adding a field to the
    document therefore requires adding it to a preimage and recording the binding here,
    which is precisely what section 13.3's first consequence demands: "A field that no
    digest commits may not be serialized."
    """
    bindings: dict[str, FieldBinding] = {}

    def walk(node: object, path: str) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else str(key))
            return
        if isinstance(node, (list, tuple)):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")
            return
        schema_path = _normalized_leaf_path(path)
        binding = DOCUMENT_FIELD_BINDINGS.get(schema_path)
        if binding is None:
            message = (
                f"serialized leaf {path!r} has no accepted binding: Decision 021 section 13.3 "
                "forbids serializing a value that no digest commits"
            )
            raise GateFailureError(message)
        bindings[path] = binding

    walk(document, "")
    return bindings


def _required_fields_at(prefix: str) -> set[str]:
    """Scalar leaf names the schema declares directly under ``prefix``."""
    marker = f"{prefix}." if prefix else ""
    return {
        path[len(marker) :]
        for path in DOCUMENT_FIELD_BINDINGS
        if path.startswith(marker) and "." not in path[len(marker) :]
    }


def _required_records_at(prefix: str) -> set[str]:
    """Nested record and array names the schema declares directly under ``prefix``.

    A binding path carrying a further separator beyond ``prefix`` names a value that
    lives inside a nested record or array, so the container holding it is itself part of
    the schema. It has to be required by name, because neither of the other two checks
    can see it: the scalar-field check above compares only non-container keys, and
    item-level coverage usually survives a dropped family, since the same section 10 item
    is generally discharged by some scalar elsewhere as well. Decision 021 section 13.2.1
    is explicit that a digest alone never discharges a requirement -- where section 10
    asks for full records, provenance entries, authority records, or reconstruction
    content, category T requires the values themselves -- so a document that has stopped
    carrying a record must fail closed rather than rest on the digest that covers it.
    """
    marker = f"{prefix}." if prefix else ""
    found: set[str] = set()
    for path in DOCUMENT_FIELD_BINDINGS:
        if not path.startswith(marker):
            continue
        head, separator, _ = path[len(marker) :].partition(".")
        if separator:
            found.add(head.removesuffix("[]"))
    return found


def _require_complete_records(document: Mapping[str, object]) -> None:
    """Every rendered container must carry the full field set its schema declares.

    Item-level coverage alone is too weak: with twenty-four entity records, dropping
    ``cik_padded`` from one of them still leaves item 31 "covered" by the other
    twenty-three. The obligation is per record, so each container instance is compared
    against the accepted binding table's field set for its own normalized path -- both
    its scalar fields and the nested records and arrays it is required to carry.
    """

    def walk(node: object, path: str) -> None:
        if isinstance(node, Mapping):
            prefix = _normalized_leaf_path(path) if path else ""
            if prefix not in _OPEN_KEYED_PATHS:
                where = path or "the document root"
                present = {
                    str(key)
                    for key, value in node.items()
                    if not isinstance(value, (Mapping, list, tuple))
                }
                missing = _required_fields_at(prefix) - present
                if missing:
                    message = (
                        f"{where} is missing the required document fields "
                        f"{tuple(sorted(missing))}; every rendered record carries the complete "
                        "field set Decision 021 section 13.2 fixes for it"
                    )
                    raise GateFailureError(message)
                carried = {
                    str(key)
                    for key, value in node.items()
                    if isinstance(value, (Mapping, list, tuple))
                }
                absent = _required_records_at(prefix) - carried
                if absent:
                    message = (
                        f"{where} is missing the required document records "
                        f"{tuple(sorted(absent))}; Decision 021 section 13.2.1 requires the "
                        "values themselves at section 10 granularity, so a covering digest never "
                        "discharges a record the document has stopped carrying"
                    )
                    raise GateFailureError(message)
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else str(key))
            return
        if isinstance(node, (list, tuple)):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(document, "")


@dataclass(frozen=True, slots=True)
class ReserveCoverage:
    """Which selected targets carry a reserve package and which carry a disposition.

    Decision 020 section 7.1 makes every selected target's reserve position total and mutually
    exclusive: exactly one rank-1 package, or exactly one
    ``REVIEW_PILOT_NO_COMPATIBLE_RESERVE`` disposition, never both and never neither.
    """

    targets_with_package: frozenset[int]
    targets_with_disposition: frozenset[int]


def _records_at(document: Mapping[str, object], *path: str) -> list[Mapping[str, object]]:
    """Read one rendered array of records, failing closed on a shape that is not one."""
    node: object = document
    for key in path:
        if not isinstance(node, Mapping) or key not in node:
            message = f"the rendered pilot manifest is missing the required array {'.'.join(path)}"
            raise GateFailureError(message)
        node = node[key]
    if not isinstance(node, list):
        message = f"{'.'.join(path)} must be a rendered array of records, not {type(node).__name__}"
        raise GateFailureError(message)
    records: list[Mapping[str, object]] = []
    for entry in node:
        if not isinstance(entry, Mapping):
            message = f"{'.'.join(path)} carries a record that is not a mapping: {entry!r}"
            raise GateFailureError(message)
        records.append(entry)
    return records


def _target_cik(record: Mapping[str, object], column: str, where: str) -> int:
    """Narrow one target CIK, refusing anything a persisted row could not have held."""
    value = record.get(column)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        message = (
            f"{where} carries a malformed {column} {value!r}; a target CIK is a positive integer "
            "and is never inferred, coerced, or defaulted"
        )
        raise GateFailureError(message)
    return value


def reserve_coverage(document: Mapping[str, object]) -> ReserveCoverage:
    """Prove every selected target's reserve position is total and mutually exclusive.

    Decision 022 makes crosswalk item 46's reserve rank applicable once per persisted reserve
    package, and structurally not applicable for a target that carries the persisted
    ``REVIEW_PILOT_NO_COMPATIBLE_RESERVE`` disposition instead. That exemption is only sound
    while the coverage it rests on is itself proven, so this function establishes the
    precondition: it derives the position of every selected target from the rendered
    ``pilot_reserves`` and ``pilot_selection_entity_reasons`` rows -- persisted state, never a
    caller flag, a fixture parameter, or a runtime assumption -- and fails closed on any target
    with both, any target with neither, a duplicate package or disposition, a package or
    disposition for an unselected target, a rank that is not the accepted rank, or a substituted
    reason code. Crosswalk item 70's total coverage requirement is exactly this proof.
    """
    selected = {
        _target_cik(record, "cik_numeric", "selected entity")
        for record in _records_at(document, "selected_entities")
    }
    packages: dict[int, int] = {}
    for record in _records_at(document, "reserves", "packages"):
        target = _target_cik(record, "target_cik_numeric", "reserve package")
        rank = record.get("reserve_rank")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank != ACCEPTED_RESERVE_RANK:
            message = (
                f"reserve package for target {target} carries reserve_rank {rank!r}; migration "
                f"0012 admits only rank {ACCEPTED_RESERVE_RANK}, and a rank is never invented, "
                "defaulted, or substituted"
            )
            raise GateFailureError(message)
        if target in packages:
            message = (
                f"target {target} carries more than one reserve package; Decision 020 section 7.1 "
                "admits exactly one rank-1 package per target"
            )
            raise GateFailureError(message)
        if target not in selected:
            message = (
                f"reserve package names target {target}, which is not a selected entity; a "
                "package for an unselected target is refused, never ignored"
            )
            raise GateFailureError(message)
        packages[target] = rank

    dispositions: set[int] = set()
    for record in _records_at(document, "reserves", "dispositions"):
        target = _target_cik(record, "cik_numeric", "reserve disposition")
        scope, code = record.get("reason_scope"), record.get("reason_code")
        if scope != RESERVE_DISPOSITION_SCOPE or code != NO_COMPATIBLE_RESERVE_REASON_CODE:
            message = (
                f"reserve disposition for target {target} carries reason_scope {scope!r} and "
                f"reason_code {code!r}; migration 0012 admits only "
                f"{RESERVE_DISPOSITION_SCOPE!r} / {NO_COMPATIBLE_RESERVE_REASON_CODE!r}"
            )
            raise GateFailureError(message)
        if target in dispositions:
            message = (
                f"target {target} carries more than one reserve disposition; exactly one is "
                "admitted per target"
            )
            raise GateFailureError(message)
        if target not in selected:
            message = (
                f"reserve disposition names target {target}, which is not a selected entity; an "
                "extra disposition is refused, never ignored"
            )
            raise GateFailureError(message)
        dispositions.add(target)

    both = tuple(sorted(set(packages) & dispositions))
    if both:
        message = (
            f"targets {both} carry both a reserve package and a no-compatible-reserve "
            "disposition; Decision 020 section 7.1 makes the two mutually exclusive"
        )
        raise GateFailureError(message)
    neither = tuple(sorted(selected - set(packages) - dispositions))
    if neither:
        message = (
            f"targets {neither} carry neither a reserve package nor a no-compatible-reserve "
            "disposition; Decision 020 section 7.1 makes every selected target's reserve "
            "position total, and crosswalk item 70 requires it in the document"
        )
        raise GateFailureError(message)
    return ReserveCoverage(
        targets_with_package=frozenset(packages), targets_with_disposition=frozenset(dispositions)
    )


def verify_document_crosswalk_coverage(
    document: Mapping[str, object],
) -> dict[int, tuple[str, ...]]:
    """Prove the rendered document discharges the crosswalk item by item (section 13.2.1).

    Every ``D`` and ``T`` item must be present in the document at the granularity section
    10 requires; every ``X`` and ``S9`` item must be absent from the substantive body; and
    every rendered record must carry its complete field set, so a value dropped from one
    record among many is caught rather than covered by its siblings.
    Returns the item-to-leaf map so a caller can compare each rendered value against the
    reconstruction source the crosswalk records for it.

    **Item 46 is applicable once per persisted reserve package (Decision 022).** A run whose
    accepted S5.4 methodology produced no compatible reserve for any target carries no package
    and therefore no rank, so the item is structurally not applicable rather than missing --
    but only once :func:`reserve_coverage` has proved that every selected target is instead
    covered by exactly one ``REVIEW_PILOT_NO_COMPATIBLE_RESERVE`` disposition. The exemption is
    never a global relaxation: with even one package present item 46 is required as usual, and
    no other ``D`` or ``T`` item is ever exempt.
    """
    leaves = document_leaf_bindings(document)
    _require_complete_records(document)
    coverage = reserve_coverage(document)
    covered: dict[int, list[str]] = {}
    for path, binding in leaves.items():
        for number in binding.items:
            covered.setdefault(number, []).append(path)
    required = {item.number for item in CROSSWALK if item.classification in {"D", "T"}}
    if not coverage.targets_with_package:
        required -= NOT_APPLICABLE_WITHOUT_RESERVE_PACKAGE
    missing = tuple(sorted(required - set(covered)))
    if missing:
        message = (
            f"the rendered pilot manifest does not carry milestone-plan section 10 items "
            f"{missing}; every D and T item must be serialized at section 10 granularity "
            "(Decision 021 sections 13.2.1, 13.3)"
        )
        raise GateFailureError(message)
    excluded = {item.number for item in CROSSWALK if item.classification in {"X", "S9"}}
    serialized = tuple(sorted(excluded & set(covered)))
    if serialized:
        message = (
            f"the rendered pilot manifest serializes operationally excluded or deferred "
            f"section 10 items {serialized}; an X item is not serialized and item 80 is deferred"
        )
        raise GateFailureError(message)
    return {number: tuple(sorted(paths)) for number, paths in covered.items()}


def render_canonical_json(document: Mapping[str, object]) -> str:
    """Serialize the document canonically (Decision 021 section 13.5).

    UTF-8, LF line endings, sorted object keys, arrays already in deterministic order,
    no nonfinite numbers, and relative paths only. Re-serializing the same manifest is
    byte-identical.
    """
    return (
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
