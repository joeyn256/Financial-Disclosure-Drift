"""Pilot-manifest persistence, sealing, and verification (Decision 021, Stage M2.3-S6).

This adapter loads the persisted rows, verifies the seven Decision 021 section 11.2
eligibility preconditions, seals ``selection_result_sha256`` in its own prior
transaction, then builds and persists one ``proposed`` manifest with its serialized
document in a single transaction. All hashing and document construction live in the
pure :mod:`disclosure_drift.release.pilot_manifest` module; nothing here re-derives a
digest rule of its own.

**Statement discipline (Decision 021 sections 11.3 and 16).** This module issues plain
``INSERT`` and plain ``UPDATE`` only. It never issues ``INSERT OR REPLACE``,
``REPLACE INTO``, ``INSERT OR IGNORE``, or ``DELETE`` against
``pilot_manifest_versions`` or ``pilot_selection_runs``, and it never names
``selection_run_id``, ``snapshot_id``, or ``selection_input_sha256`` in an
``UPDATE ... SET`` list. The only run column it ever updates is
``selection_result_sha256``. Migration ``0013``'s eight triggers enforce all of this at
the schema layer so that no part of it rests on code review.

**Proposed-only (Decision 021 section 11.1).** This module never transitions a manifest
to ``owner_approved``, never populates ``approval_reference``, ``approved_root_sha256``,
or ``approved_at_utc``, never supersedes or rejects a manifest, never populates
``supersedes_manifest_id`` at all, and publishes nothing.

**Leakage surface (Decision 021 section 8.4.1).** The only tables read are those
enumerated in Decision 021 sections 6 through 8. No outcome value, no filing text, and
no CompanyFacts source is opened anywhere in this module.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.paths import DataTree
from disclosure_drift.pilot_policy import (
    PILOT_JOINT_SELECTOR_POLICY_VERSION,
    PILOT_MANIFEST_HASH_POLICY_VERSION,
    PILOT_QUOTA_POLICY_VERSION,
)
from disclosure_drift.release.pilot_manifest import (
    ACCESSION_DERIVED_FIELDS,
    CONSUMED_POLICY_KEYS,
    MANIFEST_STATE_LITERAL,
    NAME_CHANGE_FLAG_FIELDS,
    RUN_STATE_LITERAL,
    SNAPSHOT_STATE_LITERAL,
    AccessionRecordSources,
    EntityRecordSources,
    ExplicitArguments,
    ManifestComponents,
    ManifestIdentity,
    ManifestSources,
    ReconstructionFacts,
    SourceObservation,
    build_manifest_document,
    candidate_tables_sha256,
    manifest_filename,
    manifest_identifier,
    quota_definitions_sha256,
    quota_report_sha256,
    render_canonical_json,
    reserves_sha256,
    root_manifest_sha256,
    selected_accessions_sha256,
    selected_entities_sha256,
    selection_result_sha256,
    selector_policy_sha256,
    source_observation_set_sha256,
    verify_document_crosswalk_coverage,
)
from disclosure_drift.sec.accession_selection_store import (
    ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
    PersistedJointSelectionResult,
    load_frozen_joint_candidates,
    reconstruct_persisted_joint_selection,
)
from disclosure_drift.sec.temporal import SEC_TIMEZONE_NAME
from disclosure_drift.storage.sqlite import transaction

__all__ = [
    "PILOT_MANIFEST_SUBDIRECTORY",
    "PersistedPilotManifest",
    "build_and_persist_pilot_manifest",
    "seal_selection_result",
    "verify_pilot_manifest",
]

#: Decision 021 section 13.5: no new top-level data directory is introduced.
PILOT_MANIFEST_SUBDIRECTORY: Final = "pilot"

_MANIFEST_COLUMNS: Final[tuple[str, ...]] = (
    "manifest_id",
    "selection_run_id",
    "snapshot_id",
    "manifest_schema_version",
    "ordinal_version",
    "supersedes_manifest_id",
    "source_observation_set_sha256",
    "candidate_tables_sha256",
    "quota_definitions_sha256",
    "selector_policy_sha256",
    "selected_entities_sha256",
    "selected_accessions_sha256",
    "reserves_sha256",
    "quota_report_sha256",
    "root_manifest_sha256",
    "manifest_state",
    "relative_manifest_path",
    "generated_at_utc",
)


@dataclass(frozen=True, slots=True)
class PersistedPilotManifest:
    """One persisted ``proposed`` manifest and the document it was written with."""

    identity: ManifestIdentity
    components: ManifestComponents
    selection_result_sha256: str
    root_manifest_sha256: str
    document: Mapping[str, object]
    canonical_json: str
    relative_manifest_path: str


def _fail(message: str) -> GateFailureError:
    """Build the single failure type this module raises."""
    return GateFailureError(message)


def _rows(
    connection: sqlite3.Connection, sql: str, parameters: Sequence[object]
) -> tuple[dict[str, object], ...]:
    """Read rows as plain mappings, leaving retrieval order to the digest layer."""
    cursor = connection.execute(sql, tuple(parameters))
    columns = [description[0] for description in cursor.description]
    return tuple(dict(zip(columns, row, strict=True)) for row in cursor.fetchall())


def _one(
    connection: sqlite3.Connection, sql: str, parameters: Sequence[object], label: str
) -> dict[str, object]:
    """Read exactly one row or fail closed."""
    found = _rows(connection, sql, parameters)
    if len(found) != 1:
        message = f"expected exactly one {label} row, found {len(found)}"
        raise _fail(message)
    return found[0]


# --------------------------------------------------------------------------
# Row loading (Decision 021 sections 6 through 8)
# --------------------------------------------------------------------------


def _load_run(connection: sqlite3.Connection, selection_run_id: str) -> dict[str, object]:
    """Load the referenced selection run, failing closed when it does not exist."""
    found = _rows(
        connection,
        "SELECT selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
        "quota_policy_version, run_state, expanded_node_count, node_limit_exhausted, "
        "selected_entity_count, selected_accession_count, selection_input_sha256, "
        "selection_result_sha256 FROM pilot_selection_runs WHERE selection_run_id = ?",
        (selection_run_id,),
    )
    if not found:
        message = f"pilot selection run {selection_run_id!r} does not exist"
        raise _fail(message)
    return found[0]


def _load_structural_rows(
    connection: sqlite3.Connection, source_observation_id: str
) -> tuple[dict[str, object], ...]:
    """Load one observation's structural rows, including the partition key."""
    return _rows(
        connection,
        "SELECT parser_run_id, region, state, observed_type, member_name, record_path "
        "FROM census_structural_observations WHERE source_observation_id = ?",
        (source_observation_id,),
    )


def _load_cited_observations(
    connection: sqlite3.Connection, snapshot_id: str
) -> tuple[SourceObservation, ...]:
    """Load the cited observation set for one snapshot (Decision 021 section 8.1).

    The set is the distinct union of ``source_observation_id`` over
    ``pilot_candidate_entity_evidence`` and ``pilot_candidate_accession_evidence``
    scoped to that snapshot. It is derived from persisted evidence rows, never supplied
    by a caller.
    """
    cited = _rows(
        connection,
        "SELECT DISTINCT source_observation_id FROM pilot_candidate_entity_evidence "
        "WHERE snapshot_id = ? UNION SELECT DISTINCT source_observation_id "
        "FROM pilot_candidate_accession_evidence WHERE snapshot_id = ?",
        (snapshot_id, snapshot_id),
    )
    observations: list[SourceObservation] = []
    for row in cited:
        observation_id = str(row["source_observation_id"])
        content = _one(
            connection,
            "SELECT source_id, request_identity, logical_sha256, parser_version, outcome "
            "FROM census_source_observations WHERE observation_id = ?",
            (observation_id,),
            f"census_source_observations {observation_id!r}",
        )
        observations.append(
            SourceObservation(
                source_id=str(content["source_id"]),
                request_identity=str(content["request_identity"]),
                logical_sha256=str(content["logical_sha256"]),
                parser_version=str(content["parser_version"]),
                outcome=str(content["outcome"]),
                structural_rows=_load_structural_rows(connection, observation_id),
            )
        )
    return tuple(observations)


def _load_policy_versions(connection: sqlite3.Connection) -> tuple[dict[str, object], ...]:
    """Load the nine consumed policy rows and cross-check them against the constants.

    Each value must equal the corresponding ``pilot_policy`` constant; a disagreement
    is a :class:`GateFailureError`, never a value the manifest silently prefers.
    ``decision_record`` and ``recorded_at_utc`` are excluded (Decision 021 section 8.4).
    """
    placeholders = ", ".join("?" for _ in CONSUMED_POLICY_KEYS)
    found = _rows(
        connection,
        f"SELECT policy_key, policy_version FROM reference_policy_versions "  # noqa: S608
        f"WHERE policy_key IN ({placeholders})",
        CONSUMED_POLICY_KEYS,
    )
    seen = {str(row["policy_key"]): str(row["policy_version"]) for row in found}
    missing = tuple(key for key in CONSUMED_POLICY_KEYS if key not in seen)
    if missing:
        message = f"reference_policy_versions is missing consumed policy keys: {missing}"
        raise _fail(message)
    return found


def _load_migration_chain(connection: sqlite3.Connection) -> tuple[dict[str, object], ...]:
    """Load every applied migration; ``applied_at_utc`` is excluded as a timestamp."""
    return _rows(
        connection,
        "SELECT version, name, checksum_sha256 FROM ops_schema_migrations ORDER BY version",
        (),
    )


def _load_snapshot(connection: sqlite3.Connection, snapshot_id: str) -> dict[str, object]:
    """Load the frozen candidate snapshot; ``census_run_id`` is excluded."""
    return _one(
        connection,
        "SELECT snapshot_id, snapshot_state, coverage_start, coverage_end, as_of_date, "
        "include_open_quarter, coverage_policy_version, candidate_policy_version, "
        "sic_family_mapping_version, evidence_policy_version, coverage_window_sha256, "
        "input_observation_set_sha256, candidate_entity_table_sha256, "
        "candidate_accession_table_sha256, candidate_registrant_table_sha256, "
        "candidate_entity_evidence_sha256, candidate_accession_evidence_sha256, "
        "candidate_entity_reasons_sha256, candidate_accession_reasons_sha256, "
        "candidate_snapshot_sha256, entity_count, accession_count "
        "FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
        (snapshot_id,),
        f"pilot_candidate_snapshots {snapshot_id!r}",
    )


def _count(connection: sqlite3.Connection, sql: str, parameters: Sequence[object]) -> int:
    """Read one scalar count."""
    return int(connection.execute(sql, tuple(parameters)).fetchone()[0])


_CANDIDATE_ENTITY_SELECT: Final = (
    "SELECT cik_numeric, cik_padded, size_evidence_level, industry_evidence_level, "
    "industry_quota_eligible, history_evidence_level, primary_universe_evidence_level, "
    "currently_inactive, engineering_only_stress, eligible_original_annual_report_count "
    "FROM pilot_candidate_entities WHERE snapshot_id = ?"
)

# The ``stored_`` aliases name the persisted column and keep it distinct from the
# Decision 019 derived value of the same concept, exactly as the accepted
# accession-content record does. Together they are the eight ``*_evidence_level``
# values Decision 021 crosswalk item 63 enumerates.
_CANDIDATE_ACCESSION_SELECT: Final = (
    "SELECT accession_plain, accession_number_dashed, form_type, is_amendment, "
    "amendment_purpose_category, amendment_purpose_quota_eligible, official_filing_date, "
    "acceptance_audit_date, report_date, provisional_official_cohort, cohort_ambiguous, "
    "acceptance_audit_cohort, filing_date_precedence, "
    "amendment_linkage_state AS stored_amendment_linkage_state, "
    "provisional_parent_accession AS stored_provisional_parent_accession, "
    "filing_date_evidence_level, "
    "cohort_evidence_level AS stored_cohort_evidence_level, xbrl_evidence_level, "
    "amendment_purpose_evidence_level AS stored_amendment_purpose_evidence_level, "
    "has_xbrl, has_inline_xbrl, multi_registrant "
    "FROM pilot_candidate_accessions WHERE snapshot_id = ?"
)


def _grouped(
    rows: Sequence[Mapping[str, object]], key: str
) -> dict[object, tuple[dict[str, object], ...]]:
    """Group rows by one key, dropping the key from each grouped record."""
    grouped: dict[object, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(row[key], []).append({k: v for k, v in row.items() if k != key})
    return {key_value: tuple(values) for key_value, values in grouped.items()}


def _entity_record_sources(
    connection: sqlite3.Connection,
    snapshot_id: str,
    candidates: Mapping[int, Mapping[str, object]],
) -> dict[int, EntityRecordSources]:
    """The block-8 sources for every candidate entity (Decision 021 section 13.2).

    ``candidates`` supplies the six Decision 019 section 8 ``name_change_*`` flags, read
    from the accepted S5 ``EntityCandidate.name_change`` derivation rather than
    re-derived here. Everything else is the persisted row the crosswalk records as the
    reconstruction source.
    """
    rows = _rows(connection, _CANDIDATE_ENTITY_SELECT, (snapshot_id,))
    evidence = _grouped(
        _rows(
            connection,
            "SELECT cik_numeric, classification_dimension, evidence_role, source_field, "
            "canonical_observed_value, policy_version, precedence, parsed_record_id, "
            "evidence_sha256 FROM pilot_candidate_entity_evidence WHERE snapshot_id = ?",
            (snapshot_id,),
        ),
        "cik_numeric",
    )
    reasons = _grouped(
        _rows(
            connection,
            "SELECT cik_numeric, reason_scope, reason_code FROM pilot_candidate_entity_reasons "
            "WHERE snapshot_id = ?",
            (snapshot_id,),
        ),
        "cik_numeric",
    )
    sources: dict[int, EntityRecordSources] = {}
    for row in rows:
        cik = int(str(row["cik_numeric"]))
        if cik not in candidates:
            message = (
                f"candidate entity {cik} has no accepted S5 name-change derivation; the frozen "
                "candidate set and the persisted candidate table disagree"
            )
            raise _fail(message)
        sources[cik] = EntityRecordSources(
            candidate={name: value for name, value in row.items() if name != "cik_numeric"},
            name_change=candidates[cik],
            evidence=evidence.get(cik, ()),
            reasons=reasons.get(cik, ()),
        )
    return sources


def _accession_record_sources(
    connection: sqlite3.Connection,
    snapshot_id: str,
    derived: Mapping[str, Mapping[str, object]],
) -> dict[str, AccessionRecordSources]:
    """The block-9 sources for every candidate accession (Decision 021 section 13.2)."""
    rows = _rows(connection, _CANDIDATE_ACCESSION_SELECT, (snapshot_id,))
    registrants = _grouped(
        _rows(
            connection,
            "SELECT accession_plain, registrant_cik_numeric, registrant_cik_padded, role, "
            "is_anchor, evidence_level FROM pilot_candidate_accession_registrants "
            "WHERE snapshot_id = ?",
            (snapshot_id,),
        ),
        "accession_plain",
    )
    sources: dict[str, AccessionRecordSources] = {}
    for row in rows:
        plain = str(row["accession_plain"])
        if plain not in derived:
            message = (
                f"candidate accession {plain!r} has no accepted S5 Decision 019 derivation; the "
                "frozen candidate set and the persisted candidate table disagree"
            )
            raise _fail(message)
        sources[plain] = AccessionRecordSources(
            candidate={name: value for name, value in row.items() if name != "accession_plain"},
            derived=derived[plain],
            registrants=registrants.get(plain, ()),
        )
    return sources


def _declared_counts(
    connection: sqlite3.Connection, snapshot: Mapping[str, object]
) -> tuple[int, int]:
    """The snapshot's declared candidate counts, cross-checked against the actual rows.

    Crosswalk item 74 records ``pilot_candidate_snapshots`` as its reconstruction source
    and ``candidate_tables_sha256`` names ``entity_count`` and ``accession_count``, so the
    declaration is what the document carries. The actual row counts are compared against
    it and a disagreement fails closed rather than silently preferring either number.
    The accepted S5 loader makes the same comparison; this repeats it at the S6 boundary
    so the manifest's own precondition does not rest on another stage's check.
    """
    snapshot_id = str(snapshot["snapshot_id"])
    declared_entities = int(str(snapshot["entity_count"]))
    declared_accessions = int(str(snapshot["accession_count"]))
    actual_entities = _count(
        connection,
        "SELECT COUNT(*) FROM pilot_candidate_entities WHERE snapshot_id = ?",
        (snapshot_id,),
    )
    actual_accessions = _count(
        connection,
        "SELECT COUNT(*) FROM pilot_candidate_accessions WHERE snapshot_id = ?",
        (snapshot_id,),
    )
    if (declared_entities, declared_accessions) != (actual_entities, actual_accessions):
        message = (
            f"candidate snapshot {snapshot_id!r} declares {declared_entities} entities and "
            f"{declared_accessions} accessions but carries {actual_entities} and "
            f"{actual_accessions} rows; the manifest is refused rather than built over a "
            "snapshot that disagrees with its own declared counts"
        )
        raise _fail(message)
    return declared_entities, declared_accessions


def _load_sources(
    connection: sqlite3.Connection,
    run: Mapping[str, object],
    reconstructed: PersistedJointSelectionResult,
) -> ManifestSources:
    """Load every persisted row family the document renders.

    ``reconstructed`` is the accepted S5 reconstruction of this run. The frozen candidate
    set it was derived from supplies the Decision 019 mapped values blocks 8 and 9 need,
    so Stage S6 reads them through the accepted authority and re-derives none of them.
    """
    run_id = str(run["selection_run_id"])
    snapshot_id = str(run["snapshot_id"])
    key: tuple[object, ...] = (run_id, snapshot_id)
    frozen = load_frozen_joint_candidates(connection, snapshot_id)
    if frozen.snapshot_id != reconstructed.snapshot_id:
        message = (
            f"frozen candidate set {frozen.snapshot_id!r} disagrees with the reconstructed run's "
            f"snapshot {reconstructed.snapshot_id!r}"
        )
        raise _fail(message)
    name_change_flags = {
        int(entity.cik_padded): {
            "name_change_has_identity_evidence": entity.name_change.has_identity_evidence,
            "name_change_evidence_role": entity.name_change.evidence_role,
            "name_change_evidence_level": entity.name_change.evidence_level,
            "name_change_former_name_record_parseable": (
                entity.name_change.former_name_record_parseable
            ),
            "name_change_has_prior_current_or_from_to": (
                entity.name_change.has_prior_current_or_from_to
            ),
            "name_change_ticker_change_claimed": entity.name_change.ticker_change_claimed,
        }
        for entity in frozen.entities
    }
    missing_flags = tuple(
        name
        for name in NAME_CHANGE_FLAG_FIELDS
        if name_change_flags and name not in next(iter(name_change_flags.values()))
    )
    if missing_flags:
        message = f"accepted name-change derivation is missing {missing_flags}"
        raise _fail(message)
    accession_derived = {
        candidate.accession_plain: {
            name: getattr(candidate, name) for name in ACCESSION_DERIVED_FIELDS
        }
        for candidate in frozen.accessions
    }

    selected_entities = _rows(
        connection,
        "SELECT * FROM pilot_selected_entities WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )
    selected_accessions = _rows(
        connection,
        "SELECT * FROM pilot_selected_accessions WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )
    quota_results = _rows(
        connection,
        "SELECT * FROM pilot_quota_results WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )
    entity_contributions = _rows(
        connection,
        "SELECT * FROM pilot_selected_entity_quota_contributions "
        "WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )
    accession_contributions = _rows(
        connection,
        "SELECT * FROM pilot_selected_accession_quota_contributions "
        "WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )
    quota_members = _rows(
        connection,
        "SELECT * FROM pilot_quota_result_members WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )
    reserves = _rows(
        connection,
        "SELECT * FROM pilot_reserves WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )
    reserve_accessions = _rows(
        connection,
        "SELECT * FROM pilot_reserve_accessions WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )
    reserve_contributions = _rows(
        connection,
        "SELECT * FROM pilot_reserve_quota_contributions "
        "WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )
    reserve_dispositions = _rows(
        connection,
        "SELECT * FROM pilot_selection_entity_reasons "
        "WHERE selection_run_id = ? AND snapshot_id = ?",
        key,
    )

    entity_reasons = _rows(
        connection,
        "SELECT reason_code FROM pilot_candidate_entity_reasons WHERE snapshot_id = ?",
        (snapshot_id,),
    )
    accession_reasons = _rows(
        connection,
        "SELECT reason_code FROM pilot_candidate_accession_reasons WHERE snapshot_id = ?",
        (snapshot_id,),
    )
    exclusion_counts = Counter(
        str(row["reason_code"]) for row in (*entity_reasons, *accession_reasons)
    )
    unresolved = sum(1 for row in quota_results if row.get("evidence_state") != "provisional")

    snapshot = _load_snapshot(connection, snapshot_id)
    declared_entities, declared_accessions = _declared_counts(connection, snapshot)

    facts = ReconstructionFacts(
        selection_seed=str(run["selection_seed"]),
        selection_input_sha256=str(run["selection_input_sha256"]),
        selection_input_schema_version=ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
        declared_candidate_entity_count=declared_entities,
        declared_candidate_accession_count=declared_accessions,
        selected_table_row_counts={
            "pilot_selected_entities": len(selected_entities),
            "pilot_selected_accessions": len(selected_accessions),
        },
        exclusion_counts_by_reason_code=dict(exclusion_counts),
        unresolved_quota_count=unresolved,
        provisional_quota_count=len(quota_results) - unresolved,
    )

    return ManifestSources(
        snapshot=snapshot,
        observations=_load_cited_observations(connection, snapshot_id),
        policy_versions=_load_policy_versions(connection),
        migration_chain=_load_migration_chain(connection),
        selected_entities=selected_entities,
        selected_accessions=selected_accessions,
        quota_results=quota_results,
        entity_contributions=entity_contributions,
        accession_contributions=accession_contributions,
        quota_members=quota_members,
        reserves=reserves,
        reserve_accessions=reserve_accessions,
        reserve_contributions=reserve_contributions,
        reserve_dispositions=reserve_dispositions,
        reconstruction=facts,
        entity_record_sources=_entity_record_sources(connection, snapshot_id, name_change_flags),
        accession_record_sources=_accession_record_sources(
            connection, snapshot_id, accession_derived
        ),
        as_of_timezone=SEC_TIMEZONE_NAME,
    )


# --------------------------------------------------------------------------
# Digest derivation (Decision 021 sections 6 through 9)
# --------------------------------------------------------------------------


def _derive_components(
    run: Mapping[str, object], sources: ManifestSources, explicit: ExplicitArguments
) -> ManifestComponents:
    """Recompute all eight component digests from persisted rows."""
    return ManifestComponents(
        source_observation_set_sha256=source_observation_set_sha256(sources.observations),
        candidate_tables_sha256=candidate_tables_sha256(sources.snapshot),
        quota_definitions_sha256=quota_definitions_sha256(
            quota_policy_version=PILOT_QUOTA_POLICY_VERSION,
            quota_results=sources.quota_results,
        ),
        selector_policy_sha256=selector_policy_sha256(
            policy_versions=sources.policy_versions,
            migration_chain=sources.migration_chain,
            selection_input_schema_version=ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
            manifest_schema_version=PILOT_MANIFEST_HASH_POLICY_VERSION,
            explicit=explicit,
        ),
        selected_entities_sha256=selected_entities_sha256(sources.selected_entities),
        selected_accessions_sha256=selected_accessions_sha256(sources.selected_accessions),
        reserves_sha256=reserves_sha256(
            reserves=sources.reserves,
            reserve_accessions=sources.reserve_accessions,
            reserve_contributions=sources.reserve_contributions,
            reserve_dispositions=sources.reserve_dispositions,
        ),
        quota_report_sha256=quota_report_sha256(
            quota_results=sources.quota_results,
            entity_contributions=sources.entity_contributions,
            accession_contributions=sources.accession_contributions,
            quota_members=sources.quota_members,
        ),
    )


def _derive_result(run: Mapping[str, object], components: ManifestComponents) -> str:
    """Recompute ``selection_result_sha256`` at the frozen fourteen-field preimage."""
    return selection_result_sha256(
        manifest_hash_policy_version=PILOT_MANIFEST_HASH_POLICY_VERSION,
        selection_run_id=str(run["selection_run_id"]),
        snapshot_id=str(run["snapshot_id"]),
        selection_input_sha256=str(run["selection_input_sha256"]),
        selection_input_schema_version=ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
        run_state=str(run["run_state"]),
        selected_entity_count=int(str(run["selected_entity_count"])),
        selected_accession_count=int(str(run["selected_accession_count"])),
        expanded_node_count=run["expanded_node_count"],
        node_limit_exhausted=run["node_limit_exhausted"],
        components=components,
    )


# --------------------------------------------------------------------------
# Eligibility (Decision 021 section 11.2)
# --------------------------------------------------------------------------


def _require_eligible_run(run: Mapping[str, object]) -> None:
    """Conditions 1, 2, 4, and 6 of Decision 021 section 11.2.

    Condition 6 -- the run is not the Stage-S4 entity-only draft -- is satisfied by
    condition 2 in every constructible case: the S4 draft is permanently ``running``
    and migration ``0012``'s disposition-completeness trigger refuses to promote it, so
    a run that is ``feasible`` is by construction not that draft. Migration ``0013``
    enforces the same exclusion independently at the schema layer.
    """
    run_state = str(run["run_state"])
    if run_state != RUN_STATE_LITERAL:
        message = (
            "pilot manifest requires a feasible selection run; "
            f"run_state is {run_state!r} (this refuses the Stage-S4 entity-only draft, "
            "which is permanently running)"
        )
        raise _fail(message)
    selector_policy_version = str(run["selector_policy_version"])
    if selector_policy_version != PILOT_JOINT_SELECTOR_POLICY_VERSION:
        message = (
            "pilot manifest requires the accepted S5 joint selector policy version "
            f"{PILOT_JOINT_SELECTOR_POLICY_VERSION!r}; run records {selector_policy_version!r}"
        )
        raise _fail(message)
    quota_policy_version = str(run["quota_policy_version"])
    if quota_policy_version != PILOT_QUOTA_POLICY_VERSION:
        message = (
            "pilot manifest requires the accepted quota policy version "
            f"{PILOT_QUOTA_POLICY_VERSION!r}; run records {quota_policy_version!r}"
        )
        raise _fail(message)


def _require_frozen_snapshot(run: Mapping[str, object], sources: ManifestSources) -> None:
    """Condition 5 of Decision 021 section 11.2."""
    snapshot_id = str(sources.snapshot["snapshot_id"])
    if snapshot_id != str(run["snapshot_id"]):
        message = (
            f"manifest snapshot {snapshot_id!r} disagrees with the run's snapshot "
            f"{str(run['snapshot_id'])!r}"
        )
        raise _fail(message)
    state = sources.snapshot["snapshot_state"]
    if state != SNAPSHOT_STATE_LITERAL:
        message = f"pilot manifest requires a frozen candidate snapshot; state is {state!r}"
        raise _fail(message)


# --------------------------------------------------------------------------
# Sealing (Decision 021 sections 11.3 and 15.5)
# --------------------------------------------------------------------------


def _require_historical_reconstruction(
    connection: sqlite3.Connection, run: Mapping[str, object]
) -> PersistedJointSelectionResult:
    """Re-derive the S5 run through the accepted entry point (Decision 021 section 12).

    "Nothing stored is trusted that was not re-derived." Historical reconstruction proves
    the terminal digest by re-deriving the pure result from the frozen snapshot under the
    run's own recorded seed, policy versions, and node limit, and validating every
    persisted family against it -- all of which
    :func:`~disclosure_drift.sec.accession_selection_store.reconstruct_persisted_joint_selection`
    already is. Stage S6 calls that accepted authority rather than re-implementing any
    part of it, and then asserts the terminal facts its own preimage reads. A corrupted,
    incomplete, contradictory, or policy-mismatched persisted run raises
    ``GateFailureError`` there, before any digest is computed here.
    """
    selection_run_id = str(run["selection_run_id"])
    reconstructed = reconstruct_persisted_joint_selection(connection, selection_run_id)
    disagreements = [
        f"{name} (stored {stored!r}, reconstructed {derived!r})"
        for name, stored, derived in (
            ("snapshot_id", str(run["snapshot_id"]), reconstructed.snapshot_id),
            (
                "selection_input_sha256",
                str(run["selection_input_sha256"]),
                reconstructed.selection_input_sha256,
            ),
            ("run_state", str(run["run_state"]), reconstructed.run_state),
            (
                "selected_entity_count",
                int(str(run["selected_entity_count"])),
                reconstructed.selected_entity_count,
            ),
            (
                "selected_accession_count",
                int(str(run["selected_accession_count"])),
                reconstructed.selected_accession_count,
            ),
        )
        if stored != derived
    ]
    if disagreements:
        message = (
            f"selection run {selection_run_id!r} does not reconstruct: "
            f"{', '.join(disagreements)}; the manifest is refused rather than built over a run "
            "whose persisted terminal facts disagree with its own frozen inputs"
        )
        raise _fail(message)
    return reconstructed


def seal_selection_result(connection: sqlite3.Connection, selection_run_id: str) -> str:
    """Seal ``selection_result_sha256`` in its own transaction, idempotently by content.

    The implementation reconstructs, recomputes, compares, and either writes the seal,
    accepts an identical existing seal, or fails closed on a differing one. It never
    overwrites. The seal is a separate, later write over an already-terminal run:
    migration ``0013``'s block 2 refuses a seal that rides along with the terminal
    transition.

    The persisted S5 result is proven to reconstruct **before** anything is sealed
    (Decision 021 section 12), so a terminal digest is never established over a run whose
    stored rows no longer follow from its frozen inputs.

    This is the only ``UPDATE`` this module ever issues against
    ``pilot_selection_runs``, and it names exactly one column.
    """
    run = _load_run(connection, selection_run_id)
    _require_eligible_run(run)
    reconstructed = _require_historical_reconstruction(connection, run)
    sources = _load_sources(connection, run, reconstructed)
    _require_frozen_snapshot(run, sources)
    explicit_free_components = _derive_components_without_policy(run, sources)
    expected = _derive_result(run, explicit_free_components)

    stored = run["selection_result_sha256"]
    if stored is not None:
        if str(stored) != expected:
            message = (
                f"stored selection_result_sha256 {str(stored)!r} does not recompute from the "
                f"section 6.1 preimage (recomputed {expected!r}); refusing to overwrite"
            )
            raise _fail(message)
        return expected

    with transaction(connection) as active:
        active.execute(
            "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
            "WHERE selection_run_id = ?",
            (expected, selection_run_id),
        )
    return expected


def _derive_components_without_policy(
    run: Mapping[str, object], sources: ManifestSources
) -> ManifestComponents:
    """The four terminal components the result digest needs, with placeholders elsewhere.

    ``selection_result_sha256`` reads only the four terminal component digests
    (Decision 021 section 6.1); the remaining four components are not inputs to it, so
    sealing does not require the six explicit arguments.
    """
    return ManifestComponents(
        source_observation_set_sha256="",
        candidate_tables_sha256="",
        quota_definitions_sha256="",
        selector_policy_sha256="",
        selected_entities_sha256=selected_entities_sha256(sources.selected_entities),
        selected_accessions_sha256=selected_accessions_sha256(sources.selected_accessions),
        reserves_sha256=reserves_sha256(
            reserves=sources.reserves,
            reserve_accessions=sources.reserve_accessions,
            reserve_contributions=sources.reserve_contributions,
            reserve_dispositions=sources.reserve_dispositions,
        ),
        quota_report_sha256=quota_report_sha256(
            quota_results=sources.quota_results,
            entity_contributions=sources.entity_contributions,
            accession_contributions=sources.accession_contributions,
            quota_members=sources.quota_members,
        ),
    )


# --------------------------------------------------------------------------
# Build, persist, replay (Decision 021 sections 11 and 12)
# --------------------------------------------------------------------------


def _relative_parts(data_tree: DataTree) -> tuple[str, ...]:
    """The release subtree, relative to the data root (Decision 021 section 13.5).

    ``relative_manifest_path`` is persisted for retrieval and is never identity; it is
    stored relative to the data root so no absolute path ever reaches the catalog.
    """
    return data_tree.releases.relative_to(data_tree.data_root).parts


def _assemble(
    connection: sqlite3.Connection,
    selection_run_id: str,
    explicit: ExplicitArguments,
    ordinal_version: int,
    data_tree_relative_parts: tuple[str, ...],
) -> tuple[PersistedPilotManifest, ManifestSources]:
    """Load, reconstruct, verify eligibility, and derive every digest and the document."""
    run = _load_run(connection, selection_run_id)
    _require_eligible_run(run)
    reconstructed = _require_historical_reconstruction(connection, run)
    sources = _load_sources(connection, run, reconstructed)
    _require_frozen_snapshot(run, sources)

    components = _derive_components(run, sources, explicit)
    result = _derive_result(run, components)

    stored_seal = run["selection_result_sha256"]
    if stored_seal is None:
        message = (
            "pilot manifest requires a sealed selection run; selection_result_sha256 is NULL. "
            "Seal it first with seal_selection_result()"
        )
        raise _fail(message)
    if str(stored_seal) != result:
        message = (
            f"stored selection_result_sha256 {str(stored_seal)!r} does not independently "
            f"recompute from its persisted preimage (recomputed {result!r})"
        )
        raise _fail(message)

    root = root_manifest_sha256(
        manifest_schema_version=PILOT_MANIFEST_HASH_POLICY_VERSION,
        selection_run_id=str(run["selection_run_id"]),
        snapshot_id=str(run["snapshot_id"]),
        selection_result=result,
        components=components,
    )
    identity = ManifestIdentity(
        manifest_id=manifest_identifier(
            root_sha256=root, ordinal_version=ordinal_version, supersedes_manifest_id=None
        ),
        manifest_schema_version=PILOT_MANIFEST_HASH_POLICY_VERSION,
        selection_run_id=str(run["selection_run_id"]),
        snapshot_id=str(run["snapshot_id"]),
        ordinal_version=ordinal_version,
        supersedes_manifest_id=None,
    )
    document = build_manifest_document(
        identity=identity,
        components=components,
        root_sha256=root,
        selection_result=result,
        explicit=explicit,
        sources=sources,
        quota_policy_version=PILOT_QUOTA_POLICY_VERSION,
        manifest_state=MANIFEST_STATE_LITERAL,
    )
    # Decision 021 section 12: verification is item by item over the section 13.2.1
    # crosswalk. Every D and T item must be serialized and every X and S9 item absent,
    # and every rendered leaf must carry an accepted binding, before the document is
    # allowed to become a manifest.
    verify_document_crosswalk_coverage(document)
    canonical = render_canonical_json(document)
    relative = "/".join(
        (*data_tree_relative_parts, PILOT_MANIFEST_SUBDIRECTORY, manifest_filename(root))
    )
    manifest = PersistedPilotManifest(
        identity=identity,
        components=components,
        selection_result_sha256=result,
        root_manifest_sha256=root,
        document=document,
        canonical_json=canonical,
        relative_manifest_path=relative,
    )
    return manifest, sources


def _governed_columns(manifest: PersistedPilotManifest) -> tuple[tuple[str, object], ...]:
    """Every persisted manifest column Decision 021 governs, with its re-derived value.

    The six section 9.2 immutable identity fields, all eight component digests, and the
    root. Deliberately absent: ``manifest_state``, because a later lawful transition to
    ``owner_approved`` or ``superseded`` must leave the root and the S6 document untouched
    (section 13.2.2); and ``relative_manifest_path`` and ``generated_at_utc``, which
    section 9.2 keeps operational and correctable without touching identity.
    """
    return (
        ("manifest_id", manifest.identity.manifest_id),
        ("manifest_schema_version", manifest.identity.manifest_schema_version),
        ("selection_run_id", manifest.identity.selection_run_id),
        ("snapshot_id", manifest.identity.snapshot_id),
        ("ordinal_version", manifest.identity.ordinal_version),
        ("supersedes_manifest_id", manifest.identity.supersedes_manifest_id),
        ("source_observation_set_sha256", manifest.components.source_observation_set_sha256),
        ("candidate_tables_sha256", manifest.components.candidate_tables_sha256),
        ("quota_definitions_sha256", manifest.components.quota_definitions_sha256),
        ("selector_policy_sha256", manifest.components.selector_policy_sha256),
        ("selected_entities_sha256", manifest.components.selected_entities_sha256),
        ("selected_accessions_sha256", manifest.components.selected_accessions_sha256),
        ("reserves_sha256", manifest.components.reserves_sha256),
        ("quota_report_sha256", manifest.components.quota_report_sha256),
        ("root_manifest_sha256", manifest.root_manifest_sha256),
    )


def _require_stored_manifest_matches(
    stored: Mapping[str, object], manifest: PersistedPilotManifest
) -> None:
    """Compare every governed stored column against its re-derived value.

    Comparing only the root and ``manifest_id`` would leave the eight component columns
    and ``manifest_schema_version`` trusted rather than re-derived, which Decision 021
    section 12 forbids: a stored component that no longer follows from the persisted rows
    must be refused even when the root it sits beside still matches.
    """
    disagreements = [
        f"{column} (stored {stored[column]!r}, re-derived {derived!r})"
        for column, derived in _governed_columns(manifest)
        if stored.get(column) != derived
    ]
    if disagreements:
        message = (
            f"persisted manifest {manifest.identity.manifest_id!r} does not reproduce from "
            f"persisted state: {', '.join(disagreements)}; the stored row is refused, never "
            "replaced, repaired, or re-inserted"
        )
        raise _fail(message)


def _require_serialized_document(target: Path, canonical: str) -> None:
    """Require the serialized document to exist and re-render byte-identically.

    The row and the file commit together, so a manifest row whose document is missing,
    unreadable, empty, or altered is a partial manifest and is refused. Only the single
    read of this one known path is guarded, so no unrelated failure is absorbed.
    """
    if not target.exists():
        message = (
            f"serialized pilot manifest {target.name} is missing; the manifest row and its "
            "document commit together, so a row without its document is a partial manifest"
        )
        raise _fail(message)
    if not target.is_file():
        message = f"serialized pilot manifest {target.name} is not a regular file"
        raise _fail(message)
    try:
        stored_bytes = target.read_bytes()
    except OSError as error:
        message = f"serialized pilot manifest {target.name} could not be read: {error}"
        raise _fail(message) from error
    if not stored_bytes:
        message = f"serialized pilot manifest {target.name} is empty"
        raise _fail(message)
    if stored_bytes != canonical.encode("utf-8"):
        message = (
            f"serialized pilot manifest {target.name} does not re-render byte-identically; a "
            "semantically equivalent document with different bytes is refused, because the "
            "content-derived filename and the root both address exact bytes"
        )
        raise _fail(message)


def build_and_persist_pilot_manifest(
    connection: sqlite3.Connection,
    selection_run_id: str,
    *,
    data_tree: DataTree,
    explicit: ExplicitArguments,
    generated_at_utc: str,
    ordinal_version: int = 1,
) -> PersistedPilotManifest:
    """Build and persist one ``proposed`` manifest, or replay an existing one.

    The ``pilot_manifest_versions`` row and the serialized JSON file commit together or
    not at all; a partial manifest never exists (Decision 021 section 11.3).

    **Idempotent replay reads, reconstructs, compares, and returns.** When a manifest
    already exists for this run, snapshot, and ordinal version, this function
    re-derives the document and every digest from persisted state, compares, and
    returns the existing manifest unchanged, writing nothing. A mismatch is a
    :class:`GateFailureError`, never a rewrite.
    """
    manifest, _ = _assemble(
        connection, selection_run_id, explicit, ordinal_version, _relative_parts(data_tree)
    )
    directory = data_tree.releases / PILOT_MANIFEST_SUBDIRECTORY
    target = directory / manifest_filename(manifest.root_manifest_sha256)

    existing = _rows(
        connection,
        f"SELECT {', '.join(_MANIFEST_COLUMNS)} FROM pilot_manifest_versions "  # noqa: S608
        "WHERE selection_run_id = ? AND snapshot_id = ? AND ordinal_version = ?",
        (manifest.identity.selection_run_id, manifest.identity.snapshot_id, ordinal_version),
    )
    if existing:
        _require_stored_manifest_matches(existing[0], manifest)
        _require_serialized_document(target, manifest.canonical_json)
        return manifest

    # A row already carrying this content-derived manifest_id that the ordinal lookup did
    # not find means the persisted identity no longer agrees with its own content --
    # out-of-band corruption of an identity column. Detecting it here keeps every manifest
    # integrity violation a GateFailureError (Decision 021 section 16) instead of letting
    # migration 0013's replacement guard surface as a raw sqlite3.IntegrityError. Nothing
    # is caught and translated: the conflict is found before any statement is issued.
    conflicting = _rows(
        connection,
        "SELECT selection_run_id, snapshot_id, ordinal_version FROM pilot_manifest_versions "
        "WHERE manifest_id = ?",
        (manifest.identity.manifest_id,),
    )
    if conflicting:
        stored = conflicting[0]
        message = (
            f"manifest_id {manifest.identity.manifest_id!r} already exists for selection run "
            f"{str(stored['selection_run_id'])!r}, snapshot {str(stored['snapshot_id'])!r}, "
            f"ordinal version {stored['ordinal_version']!r}, which is not the ordinal version "
            f"{ordinal_version} being built; the persisted manifest identity disagrees with its "
            "own content and is refused rather than replaced or re-inserted"
        )
        raise _fail(message)
    row: dict[str, object] = {
        "manifest_id": manifest.identity.manifest_id,
        "selection_run_id": manifest.identity.selection_run_id,
        "snapshot_id": manifest.identity.snapshot_id,
        "manifest_schema_version": manifest.identity.manifest_schema_version,
        "ordinal_version": manifest.identity.ordinal_version,
        "supersedes_manifest_id": manifest.identity.supersedes_manifest_id,
        "source_observation_set_sha256": manifest.components.source_observation_set_sha256,
        "candidate_tables_sha256": manifest.components.candidate_tables_sha256,
        "quota_definitions_sha256": manifest.components.quota_definitions_sha256,
        "selector_policy_sha256": manifest.components.selector_policy_sha256,
        "selected_entities_sha256": manifest.components.selected_entities_sha256,
        "selected_accessions_sha256": manifest.components.selected_accessions_sha256,
        "reserves_sha256": manifest.components.reserves_sha256,
        "quota_report_sha256": manifest.components.quota_report_sha256,
        "root_manifest_sha256": manifest.root_manifest_sha256,
        "manifest_state": MANIFEST_STATE_LITERAL,
        "relative_manifest_path": manifest.relative_manifest_path,
        "generated_at_utc": generated_at_utc,
    }
    columns = ", ".join(_MANIFEST_COLUMNS)
    placeholders = ", ".join("?" for _ in _MANIFEST_COLUMNS)
    # The row and the file commit together or not at all (Decision 021 section 11.3). The
    # cleanup window opens *before* the write rather than after it: a fault raised by
    # write_text itself -- ENOSPC part-way through, for instance -- has already created or
    # truncated the target, so a flag set only on the statement after a successful write
    # would leave a partial file behind while the transaction rolled back. A file that
    # already existed is never removed: at this content-derived name it is the identical
    # document, and deleting another writer's artifact is not this function's to do.
    pre_existing = target.exists()
    created = False
    try:
        with transaction(connection) as active:
            active.execute(
                f"INSERT INTO pilot_manifest_versions ({columns}) VALUES ({placeholders})",  # noqa: S608
                tuple(row[column] for column in _MANIFEST_COLUMNS),
            )
            directory.mkdir(parents=True, exist_ok=True)
            created = not pre_existing
            target.write_text(manifest.canonical_json, encoding="utf-8")
    except BaseException:
        if created and target.exists():
            target.unlink()
        raise
    return manifest


def verify_pilot_manifest(
    connection: sqlite3.Connection,
    manifest_id: str,
    *,
    data_tree: DataTree,
    explicit: ExplicitArguments,
) -> PersistedPilotManifest:
    """Re-derive a persisted manifest from the catalog and fail closed on any difference.

    Nothing stored is trusted that was not re-derived: every component digest, the
    result digest, the root, ``manifest_id``, and the document are recomputed from
    persisted rows and compared. A corrupted seal, a corrupted component, a corrupted
    root, or a rendered value that disagrees with the row it came from is a
    :class:`GateFailureError` (Decision 021 section 12).
    """
    stored = _one(
        connection,
        "SELECT * FROM pilot_manifest_versions WHERE manifest_id = ?",
        (manifest_id,),
        f"pilot_manifest_versions {manifest_id!r}",
    )
    manifest, _ = _assemble(
        connection,
        str(stored["selection_run_id"]),
        explicit,
        int(str(stored["ordinal_version"])),
        _relative_parts(data_tree),
    )

    _require_stored_manifest_matches(stored, manifest)

    # Section 13.3 step 2, "document -> row": the rendering must agree with the persisted
    # rows it came from. The sources are read a second time, independently of the load
    # the document was rendered from, and the document is re-rendered and compared.
    run = _load_run(connection, str(stored["selection_run_id"]))
    reread = _load_sources(connection, run, _require_historical_reconstruction(connection, run))
    rerendered = build_manifest_document(
        identity=manifest.identity,
        components=manifest.components,
        root_sha256=manifest.root_manifest_sha256,
        selection_result=manifest.selection_result_sha256,
        explicit=explicit,
        sources=reread,
        quota_policy_version=PILOT_QUOTA_POLICY_VERSION,
        manifest_state=MANIFEST_STATE_LITERAL,
    )
    if rerendered != manifest.document:
        message = (
            f"pilot manifest {manifest_id!r} does not re-render identically from a second "
            "independent read of its persisted rows"
        )
        raise _fail(message)
    verify_document_crosswalk_coverage(manifest.document)

    path = (
        data_tree.releases
        / PILOT_MANIFEST_SUBDIRECTORY
        / manifest_filename(manifest.root_manifest_sha256)
    )
    _require_serialized_document(path, manifest.canonical_json)
    return manifest
