"""S4.2 -- frozen candidate-snapshot reconstruction and entity-selection persistence:
focused adversarial test suite.

Every test uses a freshly created temporary SQLite database (never a persistent
repository database) and constructs its own minimal frozen candidate snapshot.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from disclosure_drift import pilot_policy
from disclosure_drift.errors import GateFailureError
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.entity_selection_store import (
    PersistedEntitySelectionResult,
    build_entity_selection_run_identity,
    execute_and_persist_entity_selection,
    load_frozen_entity_candidates,
    reconstruct_persisted_entity_selection,
)
from disclosure_drift.sec.entity_selector import (
    CONTROL_QUOTAS,
    HISTORY_QUOTAS,
    INDUSTRY_QUOTAS,
    MIN_INACTIVE_EVENTFUL,
    OPERATING_FINANCIAL_INDUSTRY,
    PILOT_SELECTION_SEED,
    SIZE_QUOTAS,
    TOTAL_CONTROLS,
    TOTAL_OPERATING,
    Candidate,
    selection_rank,
)
from disclosure_drift.storage.sqlite import (
    apply_migrations,
    available_migrations,
    connect,
    integrity_report,
    transaction,
)

_QUOTA_POLICY_VERSION_FOR_TESTS = "quota-policy-test-only/1.0"


def _hex(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _migrated_database(tmp_path: Path) -> Path:
    path = tmp_path / "catalog.db"
    with connect(path, writer=True) as connection:
        apply_migrations(connection, migrations=available_migrations())
    return path


def _seed_reason_codes(connection: sqlite3.Connection) -> None:
    """Seed ``reference_reason_codes`` for FK targets (mirrors
    ``CatalogWriter.seed_reference_data`` without its writer-lease machinery)."""
    with transaction(connection) as c:
        for code in REASON_CODES.values():
            c.execute(
                "INSERT OR REPLACE INTO reference_reason_codes "
                "(reason_code, category, description, blocks_release, "
                "requires_manual_review, decision_record) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    code.code,
                    code.category,
                    code.description,
                    int(code.blocks_release),
                    int(code.requires_manual_review),
                    code.decision_reference,
                ),
            )


def _seed_job(connection: sqlite3.Connection, job_id: str = "job-1") -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO ops_ingestion_jobs "
            "(job_id, job_kind, job_state, stage, started_at_utc, detail) "
            "VALUES (?, 'sec_census', 'completed', 'M2.2', '2026-01-01T00:00:00Z', '')",
            (job_id,),
        )


def _insert_building_snapshot(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    candidate_policy_version: str | None = None,
    sic_family_mapping_version: str | None = None,
    evidence_policy_version: str | None = None,
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_candidate_snapshots "
            "(snapshot_id, census_run_id, coverage_start, coverage_end, as_of_date, "
            "include_open_quarter, coverage_policy_version, candidate_policy_version, "
            "sic_family_mapping_version, evidence_policy_version, coverage_window_sha256, "
            "input_observation_set_sha256, snapshot_state, created_at_utc) "
            "VALUES (?, 'job-1', '2010-01-01', '2026-06-30', '2026-06-30', 0, "
            "'coverage/1.0', ?, ?, ?, ?, ?, 'building', '2026-01-01T00:00:00Z')",
            (
                snapshot_id,
                candidate_policy_version or pilot_policy.PILOT_CANDIDATE_POLICY_VERSION,
                sic_family_mapping_version or pilot_policy.SIC_FAMILY_MAPPING_VERSION,
                evidence_policy_version or pilot_policy.PILOT_EVIDENCE_POLICY_VERSION,
                _hex(f"coverage-window:{snapshot_id}"),
                _hex(f"obs:{snapshot_id}"),
            ),
        )


def _insert_operating_entity(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    cik: int,
    size: str,
    industry: str,
    history: str,
    inactive: bool,
    cik_padded_override: str | None = None,
    entity_tie_break_sha256_override: str | None = None,
) -> None:
    is_financial = industry == OPERATING_FINANCIAL_INDUSTRY
    cik_padded = cik_padded_override or f"{cik:010d}"
    entity_tie_break_sha256 = entity_tie_break_sha256_override or selection_rank(
        cik_padded, PILOT_SELECTION_SEED
    )
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_candidate_entities "
            "(snapshot_id, cik_numeric, cik_padded, entity_tie_break_sha256, "
            "candidate_category, size_stratum, size_evidence_level, size_resolution_sha256, "
            "industry_family, industry_quota_eligible, industry_evidence_level, "
            "industry_resolution_sha256, history_class, history_evidence_level, "
            "history_resolution_sha256, currently_inactive, primary_universe_eligible, "
            "primary_universe_evidence_level, primary_universe_resolution_sha256, "
            "engineering_only_stress, filing_time_name, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, 'operating', ?, 'provisional', ?, ?, 1, 'provisional', ?, "
            "?, 'provisional', ?, ?, ?, 'provisional', ?, ?, ?, '2026-01-01T00:00:00Z')",
            (
                snapshot_id,
                cik,
                cik_padded,
                entity_tie_break_sha256,
                size,
                _hex(f"size-resolution:{snapshot_id}:{cik}"),
                industry,
                _hex(f"industry-resolution:{snapshot_id}:{cik}"),
                history,
                _hex(f"history-resolution:{snapshot_id}:{cik}"),
                1 if inactive else 0,
                0 if is_financial else 1,
                None if is_financial else _hex(f"pu-resolution:{snapshot_id}:{cik}"),
                1 if is_financial else 0,
                f"Synthetic Issuer {cik}",
            ),
        )
        dimensions = ("size", "industry", "history") + (
            () if is_financial else ("primary_universe",)
        )
        for dimension in dimensions:
            c.execute(
                "INSERT INTO pilot_candidate_entity_evidence "
                "(evidence_id, snapshot_id, cik_numeric, classification_dimension, evidence_role, "
                "source_observation_id, source_field, policy_version, precedence, evidence_sha256, "
                "recorded_at_utc) "
                "VALUES (?, ?, ?, ?, 'winning', 'obs-1', 'field-1', 'policy/1.0', 1, ?, "
                "'2026-01-01T00:00:00Z')",
                (
                    _hex(f"evidence:{snapshot_id}:{cik}:{dimension}"),
                    snapshot_id,
                    cik,
                    dimension,
                    _hex(f"evidence-sha:{snapshot_id}:{cik}:{dimension}"),
                ),
            )


def _insert_control_entity(
    connection: sqlite3.Connection, *, snapshot_id: str, cik: int, kind: str
) -> None:
    cik_padded = f"{cik:010d}"
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_candidate_entities "
            "(snapshot_id, cik_numeric, cik_padded, entity_tie_break_sha256, "
            "candidate_category, control_kind, size_evidence_level, industry_evidence_level, "
            "history_evidence_level, primary_universe_eligible, primary_universe_evidence_level, "
            "filing_time_name, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, 'control', ?, 'unavailable', 'unavailable', 'unavailable', "
            "0, 'unavailable', ?, '2026-01-01T00:00:00Z')",
            (
                snapshot_id,
                cik,
                cik_padded,
                selection_rank(cik_padded, PILOT_SELECTION_SEED),
                kind,
                f"Synthetic Control {kind}",
            ),
        )


def _freeze_snapshot(connection: sqlite3.Connection, *, snapshot_id: str) -> None:
    entity_count = connection.execute(
        "SELECT COUNT(*) FROM pilot_candidate_entities WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchone()[0]
    with transaction(connection) as c:
        c.execute(
            "UPDATE pilot_candidate_snapshots SET snapshot_state = 'frozen', "
            "frozen_at_utc = '2026-01-02T00:00:00Z', candidate_snapshot_sha256 = ?, "
            "input_observation_set_sha256 = ?, candidate_entity_table_sha256 = ?, "
            "candidate_accession_table_sha256 = ?, candidate_registrant_table_sha256 = ?, "
            "candidate_entity_evidence_sha256 = ?, candidate_accession_evidence_sha256 = ?, "
            "candidate_entity_reasons_sha256 = ?, candidate_accession_reasons_sha256 = ?, "
            "entity_count = ?, accession_count = 0 WHERE snapshot_id = ?",
            (
                _hex(f"root:{snapshot_id}"),
                _hex(f"obs:{snapshot_id}"),
                _hex(f"entities:{snapshot_id}"),
                _hex(f"accessions:{snapshot_id}"),
                _hex(f"registrants:{snapshot_id}"),
                _hex(f"entity-evidence:{snapshot_id}"),
                _hex(f"accession-evidence:{snapshot_id}"),
                _hex(f"entity-reasons:{snapshot_id}"),
                _hex(f"accession-reasons:{snapshot_id}"),
                entity_count,
                snapshot_id,
            ),
        )


def build_minimal_feasible_snapshot(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    cik_offset: int = 0,
    candidate_policy_version: str | None = None,
    sic_family_mapping_version: str | None = None,
    evidence_policy_version: str | None = None,
    cik_padded_override_for_cik: int | None = None,
    cik_padded_override: str | None = None,
    entity_tie_break_sha256_override_for_cik: int | None = None,
    entity_tie_break_sha256_override: str | None = None,
) -> None:
    """Build and freeze the smallest exactly-fitting feasible 24-entity snapshot.

    20 operating entities with zero slack across size/industry/history (each
    quota bucket has exactly its required count) plus one entity per control
    kind. Exactly ``MIN_INACTIVE_EVENTFUL`` of the eventful entities are marked
    currently inactive. The optional ``*_override_for_cik``/``*_override``
    pairs let a caller corrupt exactly one entity's stored CIK padding or tie-
    break hash while everything else about the snapshot stays valid -- freeze
    itself does not (and per Decision 016 cannot be relied on to) validate
    either invariant, so this is the only way to construct a frozen snapshot
    the S4.2 reader must independently catch.
    """
    _insert_building_snapshot(
        connection,
        snapshot_id=snapshot_id,
        candidate_policy_version=candidate_policy_version,
        sic_family_mapping_version=sic_family_mapping_version,
        evidence_policy_version=evidence_policy_version,
    )
    size_labels = [key for key, count in SIZE_QUOTAS.items() for _ in range(count)]
    industry_labels = [key for key, count in INDUSTRY_QUOTAS.items() for _ in range(count)]
    history_labels = [key for key, count in HISTORY_QUOTAS.items() for _ in range(count)]
    assert len(size_labels) == len(industry_labels) == len(history_labels) == TOTAL_OPERATING

    cik = cik_offset + 1
    inactive_assigned = 0
    for size, industry, history in zip(size_labels, industry_labels, history_labels, strict=True):
        inactive = history == "eventful" and inactive_assigned < MIN_INACTIVE_EVENTFUL
        if inactive:
            inactive_assigned += 1
        _insert_operating_entity(
            connection,
            snapshot_id=snapshot_id,
            cik=cik,
            size=size,
            industry=industry,
            history=history,
            inactive=inactive,
            cik_padded_override=(
                cik_padded_override if cik == cik_padded_override_for_cik else None
            ),
            entity_tie_break_sha256_override=(
                entity_tie_break_sha256_override
                if cik == entity_tie_break_sha256_override_for_cik
                else None
            ),
        )
        cik += 1
    assert inactive_assigned == MIN_INACTIVE_EVENTFUL

    for kind in CONTROL_QUOTAS:
        _insert_control_entity(connection, snapshot_id=snapshot_id, cik=cik, kind=kind)
        cik += 1

    _freeze_snapshot(connection, snapshot_id=snapshot_id)


def _persist(
    connection: sqlite3.Connection,
    snapshot_id: str,
    *,
    event_id: str = "evt-1",
    occurred_at_utc: str = "2026-01-03T00:00:00Z",
    **kwargs: object,
) -> PersistedEntitySelectionResult:
    return execute_and_persist_entity_selection(
        connection,
        snapshot_id,
        quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS,
        occurred_at_utc=occurred_at_utc,
        event_id=event_id,
        **kwargs,  # type: ignore[arg-type]
    )


def test_smoke_execute_and_persist_and_reconstruct(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("smoke-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        assert result.is_entity_feasible_draft
        assert result.run_state == "running"
        assert len(result.selected_operating) == TOTAL_OPERATING
        assert len(result.selected_controls) == TOTAL_CONTROLS
        assert all(q.status == "pass" for q in result.quota_results)

        reconstructed = reconstruct_persisted_entity_selection(connection, result.selection_run_id)
        assert reconstructed == result

        report = integrity_report(connection)
        assert report.passed


# --------------------------------------------------------------------------
# 2-8: frozen snapshot reader validation
# --------------------------------------------------------------------------


def test_building_snapshot_is_rejected(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("building-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_building_snapshot(connection, snapshot_id=snapshot_id)
        with pytest.raises(GateFailureError, match="not frozen"):
            load_frozen_entity_candidates(connection, snapshot_id)


def test_invalidated_snapshot_is_rejected(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("invalidated-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _seed_reason_codes(connection)
        _insert_building_snapshot(connection, snapshot_id=snapshot_id)
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_candidate_snapshots SET snapshot_state = 'invalidated', "
                "invalidated_at_utc = '2026-01-02T00:00:00Z', "
                "invalidated_reason_code = 'PILOT_CANDIDATE_SNAPSHOT_INVALIDATED' "
                "WHERE snapshot_id = ?",
                (snapshot_id,),
            )
        with pytest.raises(GateFailureError, match="not frozen"):
            load_frozen_entity_candidates(connection, snapshot_id)


def test_missing_snapshot_id_is_rejected(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with (
        connect(path, writer=True) as connection,
        pytest.raises(GateFailureError, match="no pilot candidate snapshot exists"),
    ):
        load_frozen_entity_candidates(connection, _hex("does-not-exist"))


def test_snapshot_entity_count_mismatch_cannot_reach_a_frozen_state(tmp_path: Path) -> None:
    """Migration 0009's own freeze trigger already requires the declared
    ``entity_count`` to equal the actual row count at freeze time, and its
    frozen-fields-immutable trigger forbids changing ``entity_count`` (or any
    other frozen field) afterward -- so a frozen snapshot can never legally
    drift from its declared entity_count. This proves that invariant holds
    both at freeze time and after, which is why the S4.2 reader's own
    (redundant, defense-in-depth) entity-count check can never be exercised
    through the schema-respecting API.
    """
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("entity-count-mismatch")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_building_snapshot(connection, snapshot_id=snapshot_id)
        _insert_operating_entity(
            connection,
            snapshot_id=snapshot_id,
            cik=1,
            size="large_accelerated",
            industry="technology_and_communications",
            history="stable",
            inactive=False,
        )
        with (
            pytest.raises(sqlite3.IntegrityError, match="entity_count mismatch"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_candidate_snapshots SET snapshot_state = 'frozen', "
                "frozen_at_utc = '2026-01-02T00:00:00Z', candidate_snapshot_sha256 = ?, "
                "input_observation_set_sha256 = ?, candidate_entity_table_sha256 = ?, "
                "candidate_accession_table_sha256 = ?, candidate_registrant_table_sha256 = ?, "
                "candidate_entity_evidence_sha256 = ?, candidate_accession_evidence_sha256 = ?, "
                "candidate_entity_reasons_sha256 = ?, candidate_accession_reasons_sha256 = ?, "
                "entity_count = 2, accession_count = 0 WHERE snapshot_id = ?",
                (
                    _hex(f"root:{snapshot_id}"),
                    _hex(f"obs:{snapshot_id}"),
                    _hex(f"entities:{snapshot_id}"),
                    _hex(f"accessions:{snapshot_id}"),
                    _hex(f"registrants:{snapshot_id}"),
                    _hex(f"entity-evidence:{snapshot_id}"),
                    _hex(f"accession-evidence:{snapshot_id}"),
                    _hex(f"entity-reasons:{snapshot_id}"),
                    _hex(f"accession-reasons:{snapshot_id}"),
                    snapshot_id,
                ),
            )


@pytest.mark.parametrize(
    "column",
    ["candidate_policy_version", "sic_family_mapping_version", "evidence_policy_version"],
)
def test_policy_version_mismatch_is_rejected(tmp_path: Path, column: str) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex(f"policy-mismatch-{column}")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(
            connection, snapshot_id=snapshot_id, **{column: "not-the-frozen-version"}
        )
        with pytest.raises(GateFailureError, match="does not match the frozen"):
            load_frozen_entity_candidates(connection, snapshot_id)


def test_malformed_cik_padded_storage_is_rejected(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("malformed-cik-padded")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(
            connection,
            snapshot_id=snapshot_id,
            cik_padded_override_for_cik=1,
            cik_padded_override="9999999999",
        )
        with pytest.raises(GateFailureError, match="expected canonical"):
            load_frozen_entity_candidates(connection, snapshot_id)


def test_stored_entity_tie_break_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("tie-break-mismatch")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(
            connection,
            snapshot_id=snapshot_id,
            entity_tie_break_sha256_override_for_cik=1,
            entity_tie_break_sha256_override=_hex("wrong-tie-break"),
        )
        with pytest.raises(GateFailureError, match="entity_tie_break_sha256"):
            load_frozen_entity_candidates(connection, snapshot_id)


# --------------------------------------------------------------------------
# 9-13, 35: deterministic identity and hashing
# --------------------------------------------------------------------------


def test_s41_in_memory_and_s42_reconstruction_agree(tmp_path: Path) -> None:
    """S4.1 direct in-memory input and S4.2 frozen-snapshot reconstruction
    produce the same selected entities and ordering (#1)."""
    from disclosure_drift.sec.entity_selector import solve_entity_selection

    path = _migrated_database(tmp_path)
    snapshot_id = _hex("s41-vs-s42")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        candidate_set = load_frozen_entity_candidates(connection, snapshot_id)
        direct_result = solve_entity_selection(candidate_set.candidates)

        persisted = _persist(connection, snapshot_id)

        assert [c.cik_padded for c in direct_result.selected_operating] == [
            c.cik_padded for c in persisted.selected_operating
        ]
        assert [c.cik_padded for c in direct_result.selected_controls] == [
            c.cik_padded for c in persisted.selected_controls
        ]


def test_insertion_order_does_not_change_candidate_set_run_id_or_result(tmp_path: Path) -> None:
    snapshot_id = _hex("insertion-order-snapshot")

    # Fixed once, independent of scan order, so "reversed" changes only the
    # physical INSERT order below -- never the logical candidate content.
    size_labels = [key for key, count in SIZE_QUOTAS.items() for _ in range(count)]
    industry_labels = [key for key, count in INDUSTRY_QUOTAS.items() for _ in range(count)]
    history_labels = [key for key, count in HISTORY_QUOTAS.items() for _ in range(count)]
    inactive_assigned = 0
    operating_rows = []
    for cik, (size, industry, history) in enumerate(
        zip(size_labels, industry_labels, history_labels, strict=True), start=1
    ):
        inactive = history == "eventful" and inactive_assigned < MIN_INACTIVE_EVENTFUL
        if inactive:
            inactive_assigned += 1
        operating_rows.append((cik, size, industry, history, inactive))
    assert inactive_assigned == MIN_INACTIVE_EVENTFUL
    control_rows = [
        (TOTAL_OPERATING + 1 + index, kind) for index, kind in enumerate(CONTROL_QUOTAS)
    ]

    def build(path: Path, *, reversed_order: bool) -> None:
        with connect(path, writer=True) as connection:
            _seed_job(connection)
            _insert_building_snapshot(connection, snapshot_id=snapshot_id)
            ordered_operating = list(reversed(operating_rows)) if reversed_order else operating_rows
            for cik, size, industry, history, inactive in ordered_operating:
                _insert_operating_entity(
                    connection,
                    snapshot_id=snapshot_id,
                    cik=cik,
                    size=size,
                    industry=industry,
                    history=history,
                    inactive=inactive,
                )
            ordered_controls = list(reversed(control_rows)) if reversed_order else control_rows
            for cik, kind in ordered_controls:
                _insert_control_entity(connection, snapshot_id=snapshot_id, cik=cik, kind=kind)
            _freeze_snapshot(connection, snapshot_id=snapshot_id)

    _migrated_database(tmp_path / "forward")
    build(tmp_path / "forward" / "catalog.db", reversed_order=False)
    _migrated_database(tmp_path / "reverse")
    build(tmp_path / "reverse" / "catalog.db", reversed_order=True)

    forward_path = tmp_path / "forward" / "catalog.db"
    reverse_path = tmp_path / "reverse" / "catalog.db"
    with connect(forward_path, writer=True) as connection:
        forward_set = load_frozen_entity_candidates(connection, snapshot_id)
        forward_identity = build_entity_selection_run_identity(
            forward_set, quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS
        )
        forward_result = _persist(connection, snapshot_id)
    with connect(reverse_path, writer=True) as connection:
        reverse_set = load_frozen_entity_candidates(connection, snapshot_id)
        reverse_identity = build_entity_selection_run_identity(
            reverse_set, quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS
        )
        reverse_result = _persist(connection, snapshot_id)

    assert {c.cik_padded for c in forward_set.candidates} == {
        c.cik_padded for c in reverse_set.candidates
    }
    assert forward_identity.selection_run_id == reverse_identity.selection_run_id
    assert forward_identity.selection_input_sha256 == reverse_identity.selection_input_sha256
    assert [c.cik_padded for c in forward_result.selected_order] == [
        c.cik_padded for c in reverse_result.selected_order
    ]


def test_two_fresh_databases_produce_the_same_run_id_and_result(tmp_path: Path) -> None:
    snapshot_id = _hex("cross-database-snapshot")
    results = []
    for label in ("db-a", "db-b"):
        path = _migrated_database(tmp_path / label)
        with connect(path, writer=True) as connection:
            _seed_job(connection)
            build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
            results.append(_persist(connection, snapshot_id))

    first, second = results
    assert first.selection_run_id == second.selection_run_id
    assert first.selection_input_sha256 == second.selection_input_sha256
    assert [c.cik_padded for c in first.selected_order] == [
        c.cik_padded for c in second.selected_order
    ]


def test_different_audit_timestamps_and_event_ids_do_not_change_hashes(tmp_path: Path) -> None:
    snapshot_id = _hex("audit-metadata-snapshot")
    results = []
    for occurred_at_utc, event_id in (
        ("2026-01-03T00:00:00Z", "evt-a"),
        ("2027-06-15T12:34:56Z", "evt-completely-different"),
    ):
        path = _migrated_database(tmp_path / occurred_at_utc.replace(":", "-"))
        with connect(path, writer=True) as connection:
            _seed_job(connection)
            build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
            results.append(
                _persist(
                    connection, snapshot_id, occurred_at_utc=occurred_at_utc, event_id=event_id
                )
            )
    first, second = results
    assert first.selection_run_id == second.selection_run_id
    assert first.selection_input_sha256 == second.selection_input_sha256


def test_different_node_limit_changes_the_run_identity(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("node-limit-identity-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        candidate_set = load_frozen_entity_candidates(connection, snapshot_id)
        id_a = build_entity_selection_run_identity(
            candidate_set, quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS, node_limit=1000
        )
        id_b = build_entity_selection_run_identity(
            candidate_set, quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS, node_limit=2000
        )
        assert id_a.selection_run_id != id_b.selection_run_id
        assert id_a.selection_input_sha256 != id_b.selection_input_sha256


def test_different_selection_seed_changes_the_run_identity(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("seed-identity-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        candidate_set = load_frozen_entity_candidates(connection, snapshot_id)
        id_a = build_entity_selection_run_identity(
            candidate_set,
            quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS,
            selection_seed="seed-a",
        )
        id_b = build_entity_selection_run_identity(
            candidate_set,
            quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS,
            selection_seed="seed-b",
        )
        assert id_a.selection_run_id != id_b.selection_run_id
        assert id_a.selection_input_sha256 != id_b.selection_input_sha256


# --------------------------------------------------------------------------
# 14-24: entity-feasible running draft persistence
# --------------------------------------------------------------------------


def test_exactly_24_selected_entity_rows_are_persisted(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("count-24-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        count = connection.execute(
            "SELECT COUNT(*) FROM pilot_selected_entities WHERE selection_run_id = ?",
            (result.selection_run_id,),
        ).fetchone()[0]
        assert count == TOTAL_OPERATING + TOTAL_CONTROLS == 24


def test_selected_order_is_contiguous_and_deterministic(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("contiguous-order-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        orders = [
            row[0]
            for row in connection.execute(
                "SELECT selected_order FROM pilot_selected_entities WHERE selection_run_id = ? "
                "ORDER BY selected_order",
                (result.selection_run_id,),
            ).fetchall()
        ]
        assert orders == list(range(1, 25))
        # rerunning against the same snapshot with the same parameters is idempotent
        # and returns the identical deterministic order
        second = _persist(connection, snapshot_id)
        assert [c.cik_padded for c in second.selected_order] == [
            c.cik_padded for c in result.selected_order
        ]


def test_operating_and_control_roles_are_persisted_correctly(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("roles-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        rows = connection.execute(
            "SELECT entity_role, COUNT(*) AS n FROM pilot_selected_entities "
            "WHERE selection_run_id = ? GROUP BY entity_role",
            (result.selection_run_id,),
        ).fetchall()
        counts = {row["entity_role"]: row["n"] for row in rows}
        assert counts == {"operating": TOTAL_OPERATING, "control": TOTAL_CONTROLS}
        assert len(result.selected_operating) == TOTAL_OPERATING
        assert len(result.selected_controls) == TOTAL_CONTROLS


def test_all_entity_quota_contributions_are_materialized_correctly(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("contributions-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        rows = connection.execute(
            "SELECT quota_dimension, quota_key, COUNT(*) AS n FROM "
            "pilot_selected_entity_quota_contributions WHERE selection_run_id = ? "
            "GROUP BY quota_dimension, quota_key",
            (result.selection_run_id,),
        ).fetchall()
        counts = {(row["quota_dimension"], row["quota_key"]): row["n"] for row in rows}
        for key, required in SIZE_QUOTAS.items():
            assert counts[("size", key)] == required
        for key, required in INDUSTRY_QUOTAS.items():
            assert counts[("industry", key)] == required
        for key, required in HISTORY_QUOTAS.items():
            assert counts[("history", key)] == required
        for key, required in CONTROL_QUOTAS.items():
            assert counts[("control", key)] == required
        assert counts[("history_status", "eventful_currently_inactive")] >= MIN_INACTIVE_EVENTFUL
        assert counts[("summary", "operating_total")] == TOTAL_OPERATING
        assert counts[("summary", "total_controls")] == TOTAL_CONTROLS
        assert counts[("summary", "total_entities")] == TOTAL_OPERATING + TOTAL_CONTROLS


def test_operating_financial_engineering_only_entities_stay_universe_ineligible(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("financial-engineering-only-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        financial = [
            c for c in result.selected_operating if c.industry_group == OPERATING_FINANCIAL_INDUSTRY
        ]
        assert len(financial) == INDUSTRY_QUOTAS[OPERATING_FINANCIAL_INDUSTRY] == 4
        for candidate in financial:
            assert candidate.primary_universe_eligible is False
            assert candidate.engineering_only_stress is True
        nonfinancial = [
            c for c in result.selected_operating if c.industry_group != OPERATING_FINANCIAL_INDUSTRY
        ]
        for candidate in nonfinancial:
            assert candidate.primary_universe_eligible is True
            assert candidate.engineering_only_stress is False


def test_controls_receive_no_operating_quota_contributions(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("control-no-operating-contribution-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        control_ciks = tuple(int(c.cik_padded) for c in result.selected_controls)
        placeholders = ", ".join("?" for _ in control_ciks)
        rows = connection.execute(
            "SELECT DISTINCT quota_dimension FROM pilot_selected_entity_quota_contributions "  # noqa: S608
            f"WHERE selection_run_id = ? AND cik_numeric IN ({placeholders})",
            (result.selection_run_id, *control_ciks),
        ).fetchall()
        dimensions = {row["quota_dimension"] for row in rows}
        assert dimensions == {"control", "summary"}
        assert "size" not in dimensions
        assert "industry" not in dimensions
        assert "history" not in dimensions
        assert "history_status" not in dimensions


def test_all_entity_quota_results_and_members_reconstruct_correctly(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("quota-results-reconstruct-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        reconstructed = reconstruct_persisted_entity_selection(connection, result.selection_run_id)
        assert reconstructed.quota_results == result.quota_results
        assert len(reconstructed.quota_results) >= (
            len(SIZE_QUOTAS) + len(INDUSTRY_QUOTAS) + len(HISTORY_QUOTAS) + len(CONTROL_QUOTAS) + 4
        )


def test_achieved_counts_equal_normalized_contributions_and_members(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("achieved-counts-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        for quota in result.quota_results:
            quota_result_id_row = connection.execute(
                "SELECT quota_result_id FROM pilot_quota_results "
                "WHERE selection_run_id = ? AND quota_dimension = ? AND quota_key = ?",
                (result.selection_run_id, quota.dimension, quota.key),
            ).fetchone()
            member_count = connection.execute(
                "SELECT COUNT(*) FROM pilot_quota_result_members WHERE quota_result_id = ?",
                (quota_result_id_row["quota_result_id"],),
            ).fetchone()[0]
            contribution_count = connection.execute(
                "SELECT COUNT(*) FROM pilot_selected_entity_quota_contributions "
                "WHERE selection_run_id = ? AND quota_dimension = ? AND quota_key = ?",
                (result.selection_run_id, quota.dimension, quota.key),
            ).fetchone()[0]
            assert member_count == quota.achieved_count
            assert contribution_count == quota.achieved_count


def test_persisted_run_remains_running_after_entity_only_feasibility(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("stays-running-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        assert result.run_state == "running"
        row = connection.execute(
            "SELECT run_state, finished_at_utc FROM pilot_selection_runs "
            "WHERE selection_run_id = ?",
            (result.selection_run_id,),
        ).fetchone()
        assert row["run_state"] == "running"
        assert row["finished_at_utc"] is None


def test_selected_accession_count_and_rows_are_both_zero(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("zero-accessions-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        assert result.selected_accession_count == 0
        actual = connection.execute(
            "SELECT COUNT(*) FROM pilot_selected_accessions WHERE selection_run_id = ?",
            (result.selection_run_id,),
        ).fetchone()[0]
        assert actual == 0


def test_no_accession_reserve_manifest_or_projection_rows_are_created(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("no-s5-s6-rows-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        for table, column in (
            ("pilot_selected_accessions", "selection_run_id"),
            ("pilot_selected_accession_quota_contributions", "selection_run_id"),
            ("pilot_reserves", "selection_run_id"),
            ("pilot_reserve_accessions", "selection_run_id"),
            ("pilot_reserve_quota_contributions", "selection_run_id"),
        ):
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} = ?",  # noqa: S608
                (result.selection_run_id,),
            ).fetchone()[0]
            assert count == 0, f"{table} should have zero rows for an entity-only draft"
        manifest_count = connection.execute(
            "SELECT COUNT(*) FROM pilot_manifest_versions WHERE selection_run_id = ?",
            (result.selection_run_id,),
        ).fetchone()[0]
        assert manifest_count == 0
        projection_count = connection.execute(
            "SELECT COUNT(*) FROM pilot_projection_recovery_events WHERE manifest_id IN "
            "(SELECT manifest_id FROM pilot_manifest_versions WHERE selection_run_id = ?)",
            (result.selection_run_id,),
        ).fetchone()[0]
        assert projection_count == 0


# --------------------------------------------------------------------------
# 25-26: idempotence
# --------------------------------------------------------------------------


def test_repeated_execution_is_idempotent_after_full_content_verification(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("idempotent-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        first = _persist(connection, snapshot_id)
        second = _persist(connection, snapshot_id)
        third = _persist(connection, snapshot_id, event_id="evt-yet-another")
        assert first == second == third

        run_count = connection.execute(
            "SELECT COUNT(*) FROM pilot_selection_runs WHERE selection_run_id = ?",
            (first.selection_run_id,),
        ).fetchone()[0]
        assert run_count == 1
        selected_count = connection.execute(
            "SELECT COUNT(*) FROM pilot_selected_entities WHERE selection_run_id = ?",
            (first.selection_run_id,),
        ).fetchone()[0]
        assert selected_count == 24
        event_count = connection.execute(
            "SELECT COUNT(*) FROM pilot_selection_run_events WHERE selection_run_id = ?",
            (first.selection_run_id,),
        ).fetchone()[0]
        assert event_count == 1


def test_same_id_stored_content_mismatch_is_rejected_not_overwritten(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("content-mismatch-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET selection_input_sha256 = ? "
                "WHERE selection_run_id = ?",
                (_hex("tampered-input-hash"), result.selection_run_id),
            )
        with pytest.raises(GateFailureError, match="different stored selection_input_sha256"):
            _persist(connection, snapshot_id)
        # the tampered row was not silently replaced
        stored = connection.execute(
            "SELECT selection_input_sha256 FROM pilot_selection_runs WHERE selection_run_id = ?",
            (result.selection_run_id,),
        ).fetchone()["selection_input_sha256"]
        assert stored == _hex("tampered-input-hash")


# --------------------------------------------------------------------------
# 27-29: proven infeasibility and node-limit exhaustion
# --------------------------------------------------------------------------


def build_infeasible_snapshot_missing_industry(
    connection: sqlite3.Connection, *, snapshot_id: str
) -> None:
    """A snapshot with zero energy_and_utilities candidates: a proven
    infeasible pool that still satisfies the S3.2 freeze invariants."""
    _insert_building_snapshot(connection, snapshot_id=snapshot_id)
    size_labels = [key for key, count in SIZE_QUOTAS.items() for _ in range(count)]
    industry_labels = [
        key
        for key, count in INDUSTRY_QUOTAS.items()
        for _ in range(count if key != "energy_and_utilities" else 0)
    ]
    history_labels = [key for key, count in HISTORY_QUOTAS.items() for _ in range(count)]
    n = len(industry_labels)
    cik = 1
    inactive_assigned = 0
    for size, industry, history in zip(
        size_labels[:n], industry_labels, history_labels[:n], strict=True
    ):
        inactive = history == "eventful" and inactive_assigned < MIN_INACTIVE_EVENTFUL
        if inactive:
            inactive_assigned += 1
        _insert_operating_entity(
            connection,
            snapshot_id=snapshot_id,
            cik=cik,
            size=size,
            industry=industry,
            history=history,
            inactive=inactive,
        )
        cik += 1
    for kind in CONTROL_QUOTAS:
        _insert_control_entity(connection, snapshot_id=snapshot_id, cik=cik, kind=kind)
        cik += 1
    _freeze_snapshot(connection, snapshot_id=snapshot_id)


def test_proven_infeasible_creates_terminal_run_with_zero_durable_result_rows(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("proven-infeasible-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _seed_reason_codes(connection)
        build_infeasible_snapshot_missing_industry(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        assert result.run_state == "infeasible"
        assert not result.is_entity_feasible_draft
        assert result.selected_entity_count == 0
        assert result.selected_accession_count == 0
        assert result.selected_operating == ()
        assert result.selected_controls == ()
        assert result.quota_results == ()

        for table in (
            "pilot_selected_entities",
            "pilot_selected_entity_quota_contributions",
            "pilot_quota_results",
            "pilot_quota_result_members",
        ):
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE selection_run_id = ?",  # noqa: S608
                (result.selection_run_id,),
            ).fetchone()[0]
            assert count == 0, f"{table} must be empty for a proven-infeasible run"

        failure_reason = connection.execute(
            "SELECT failure_reason_code FROM pilot_selection_runs WHERE selection_run_id = ?",
            (result.selection_run_id,),
        ).fetchone()["failure_reason_code"]
        assert failure_reason == "PILOT_SELECTION_INFEASIBLE"


def test_node_exhaustion_creates_infeasible_or_unproven_with_zero_durable_rows(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("node-exhaustion-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _seed_reason_codes(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id, node_limit=1)
        assert result.run_state == "infeasible_or_unproven"
        assert not result.is_entity_feasible_draft
        assert result.node_limit_exhausted
        assert result.selected_entity_count == 0
        assert result.selected_accession_count == 0

        for table in (
            "pilot_selected_entities",
            "pilot_selected_entity_quota_contributions",
            "pilot_quota_results",
            "pilot_quota_result_members",
        ):
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE selection_run_id = ?",  # noqa: S608
                (result.selection_run_id,),
            ).fetchone()[0]
            assert count == 0

        failure_reason = connection.execute(
            "SELECT failure_reason_code FROM pilot_selection_runs WHERE selection_run_id = ?",
            (result.selection_run_id,),
        ).fetchone()["failure_reason_code"]
        assert failure_reason == "PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN"


def test_node_exhaustion_never_persists_a_partial_selection(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("node-exhaustion-partial-check-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _seed_reason_codes(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id, node_limit=1)
        assert result.selected_operating == ()
        assert result.selected_controls == ()
        assert result.selected_order == ()
        reconstructed = reconstruct_persisted_entity_selection(connection, result.selection_run_id)
        assert reconstructed.selected_operating == ()
        assert reconstructed.selected_controls == ()


# --------------------------------------------------------------------------
# 30: rollback on injected persistence failure
# --------------------------------------------------------------------------


def test_injected_persistence_failure_leaves_no_partial_durable_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import disclosure_drift.sec.entity_selection_store as store_module

    path = _migrated_database(tmp_path)
    snapshot_id = _hex("injected-failure-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)

        real_contributions = store_module._entity_quota_contributions
        calls = {"n": 0}

        def _flaky_contributions(candidate: Candidate) -> tuple[tuple[str, str], ...]:
            calls["n"] += 1
            if calls["n"] > 5:
                message = "injected persistence failure for test coverage"
                raise RuntimeError(message)
            return real_contributions(candidate)

        monkeypatch.setattr(store_module, "_entity_quota_contributions", _flaky_contributions)

        with pytest.raises(RuntimeError, match="injected persistence failure"):
            _persist(connection, snapshot_id)

        run_count = connection.execute("SELECT COUNT(*) FROM pilot_selection_runs").fetchone()[0]
        assert run_count == 0
        selected_count = connection.execute(
            "SELECT COUNT(*) FROM pilot_selected_entities"
        ).fetchone()[0]
        assert selected_count == 0
        event_count = connection.execute(
            "SELECT COUNT(*) FROM pilot_selection_run_events"
        ).fetchone()[0]
        assert event_count == 0

    monkeypatch.undo()
    with connect(path, writer=True) as connection:
        # the same snapshot can still be persisted cleanly afterward
        result = _persist(connection, snapshot_id)
        assert result.is_entity_feasible_draft


# --------------------------------------------------------------------------
# 31-34: cross-snapshot protection and reconstruction adversarial checks
# --------------------------------------------------------------------------


def test_cross_snapshot_writes_remain_impossible(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("cross-snapshot-primary")
    other_snapshot_id = _hex("cross-snapshot-other")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        _insert_building_snapshot(connection, snapshot_id=other_snapshot_id)
        result = _persist(connection, snapshot_id)

        with (
            pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"),
            transaction(connection) as c,
        ):
            c.execute(
                "INSERT INTO pilot_selected_entities "
                "(selection_run_id, snapshot_id, cik_numeric, selected_order, "
                "entity_hash_sha256, entity_role, candidate_category, recorded_at_utc) "
                "VALUES (?, ?, 999, 25, ?, 'operating', 'operating', '2026-01-01T00:00:00Z')",
                (result.selection_run_id, other_snapshot_id, _hex("ghost-entity-hash")),
            )


def test_reconstruction_rejects_missing_contribution_rows(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("missing-contribution-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        with transaction(connection) as c:
            c.execute(
                "DELETE FROM pilot_selected_entity_quota_contributions "
                "WHERE selection_run_id = ? AND quota_dimension = 'size' "
                "AND quota_key = 'large_accelerated' AND cik_numeric = ("
                "  SELECT cik_numeric FROM pilot_selected_entity_quota_contributions "
                "  WHERE selection_run_id = ? AND quota_dimension = 'size' "
                "  AND quota_key = 'large_accelerated' LIMIT 1"
                ")",
                (result.selection_run_id, result.selection_run_id),
            )
        with pytest.raises(GateFailureError, match="matching"):
            reconstruct_persisted_entity_selection(connection, result.selection_run_id)


def test_reconstruction_rejects_mismatched_declared_and_actual_counts(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("mismatched-counts-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        one_cik = int(result.selected_operating[-1].cik_padded)
        with transaction(connection) as c:
            c.execute(
                "DELETE FROM pilot_quota_result_members WHERE selection_run_id = ? "
                "AND cik_numeric = ?",
                (result.selection_run_id, one_cik),
            )
            c.execute(
                "DELETE FROM pilot_selected_entity_quota_contributions "
                "WHERE selection_run_id = ? AND cik_numeric = ?",
                (result.selection_run_id, one_cik),
            )
            c.execute(
                "DELETE FROM pilot_selected_entities "
                "WHERE selection_run_id = ? AND cik_numeric = ?",
                (result.selection_run_id, one_cik),
            )
        with pytest.raises(GateFailureError, match="declares selected_entity_count 24"):
            reconstruct_persisted_entity_selection(connection, result.selection_run_id)


def test_reconstruction_rejects_a_quota_result_inconsistent_with_members(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("inconsistent-members-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        quota_result_id = connection.execute(
            "SELECT quota_result_id FROM pilot_quota_results "
            "WHERE selection_run_id = ? AND quota_dimension = 'industry' "
            "AND quota_key = 'technology_and_communications'",
            (result.selection_run_id,),
        ).fetchone()["quota_result_id"]
        with transaction(connection) as c:
            c.execute(
                "DELETE FROM pilot_quota_result_members WHERE quota_result_id = ? "
                "AND member_order = 1",
                (quota_result_id,),
            )
        with pytest.raises(GateFailureError, match="pilot_quota_result_members rows exist"):
            reconstruct_persisted_entity_selection(connection, result.selection_run_id)


# --------------------------------------------------------------------------
# 36-38: safety
# --------------------------------------------------------------------------


def test_no_random_or_clock_call_influences_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import random
    import time

    def _blocked(*_args: object, **_kwargs: object) -> None:
        message = "execute_and_persist_entity_selection must never call random or the clock"
        raise AssertionError(message)

    monkeypatch.setattr(random, "random", _blocked)
    monkeypatch.setattr(random, "choice", _blocked)
    monkeypatch.setattr(time, "time", _blocked)
    monkeypatch.setattr(time, "monotonic", _blocked)

    path = _migrated_database(tmp_path)
    snapshot_id = _hex("no-random-clock-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        assert result.is_entity_feasible_draft


def test_no_network_call_is_made_during_persistence(tmp_path: Path) -> None:
    """``tests/conftest.py`` monkeypatches ``socket.socket``/``create_connection``/
    ``getaddrinfo`` to raise for every test in this session; a passing call to
    :func:`execute_and_persist_entity_selection` already proves no network call
    occurred. This test names that guarantee explicitly for the S4.2 store.
    """
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("no-network-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        assert result.is_entity_feasible_draft


def test_entity_selection_store_module_imports_a_minimal_surface() -> None:
    """Static proof: no filing-text, outcome, feature, model, or SEC-retrieval
    module is imported by the S4.2 store."""
    import ast

    source = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "disclosure_drift"
        / "sec"
        / "entity_selection_store.py"
    )
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    allowed_top_level = {
        "__future__",
        "hashlib",
        "sqlite3",
        "collections",
        "dataclasses",
        "typing",
        "disclosure_drift",
    }
    assert imported <= allowed_top_level


def test_no_persistent_repository_database_is_touched(tmp_path: Path) -> None:
    """Confirm this test module never opens or modifies a repository database."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    persistent_candidates = list((repo_root / "data").rglob("*.sqlite3")) + list(
        (repo_root / "data").rglob("*.db")
    )
    before = {candidate: candidate.stat().st_mtime for candidate in persistent_candidates}

    path = _migrated_database(tmp_path)
    snapshot_id = _hex("no-persistent-db-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        _persist(connection, snapshot_id)

    after_candidates = list((repo_root / "data").rglob("*.sqlite3")) + list(
        (repo_root / "data").rglob("*.db")
    )
    assert after_candidates == persistent_candidates
    after = {candidate: candidate.stat().st_mtime for candidate in after_candidates}
    assert before == after


# --------------------------------------------------------------------------
# 36-44: combined Opus S4 review -- quota-policy governance and existing-run
# fail-closed behavior (Decision 017)
# --------------------------------------------------------------------------


def test_control_quota_evidence_state_is_provisional(tmp_path: Path) -> None:
    """Decision 017 section 3: a passing control quota's persisted evidence_state
    is 'provisional', meaning the frozen control-kind classification is
    provisionally accepted -- not that every evidence dimension is resolved."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("control-evidence-state-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        result = _persist(connection, snapshot_id)
        assert result.is_entity_feasible_draft
        rows = connection.execute(
            "SELECT quota_key, evidence_state, quota_result FROM pilot_quota_results "
            "WHERE selection_run_id = ? AND quota_dimension = 'control'",
            (result.selection_run_id,),
        ).fetchall()
    assert rows
    for row in rows:
        assert row["quota_result"] == "pass"
        assert row["evidence_state"] == "provisional"


def test_default_quota_policy_version_is_the_frozen_constant(tmp_path: Path) -> None:
    """Decision 017 section 1: production callers may rely on the frozen
    PILOT_QUOTA_POLICY_VERSION default rather than inventing a value per call."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("default-quota-policy-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        candidate_set = load_frozen_entity_candidates(connection, snapshot_id)
        identity = build_entity_selection_run_identity(candidate_set)
        assert identity.quota_policy_version == pilot_policy.PILOT_QUOTA_POLICY_VERSION

        result = execute_and_persist_entity_selection(
            connection,
            snapshot_id,
            occurred_at_utc="2026-01-03T00:00:00Z",
            event_id="evt-default-policy",
        )
        assert result.quota_policy_version == pilot_policy.PILOT_QUOTA_POLICY_VERSION


def test_different_quota_policy_version_changes_the_run_identity(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("quota-policy-identity-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        candidate_set = load_frozen_entity_candidates(connection, snapshot_id)
        id_a = build_entity_selection_run_identity(
            candidate_set, quota_policy_version="quota-policy-a/1.0"
        )
        id_b = build_entity_selection_run_identity(
            candidate_set, quota_policy_version="quota-policy-b/1.0"
        )
        assert id_a.selection_run_id != id_b.selection_run_id
        assert id_a.selection_input_sha256 != id_b.selection_input_sha256


def test_existing_planned_run_fails_closed_rather_than_reconstructing_silently(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("existing-planned-run-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        candidate_set = load_frozen_entity_candidates(connection, snapshot_id)
        identity = build_entity_selection_run_identity(
            candidate_set, quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS
        )
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_selection_runs "
                "(selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
                "quota_policy_version, search_node_limit, run_state, selection_input_sha256, "
                "started_at_utc) VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?)",
                (
                    identity.selection_run_id,
                    snapshot_id,
                    identity.selection_seed,
                    pilot_policy.PILOT_SELECTOR_POLICY_VERSION,
                    _QUOTA_POLICY_VERSION_FOR_TESTS,
                    identity.node_limit,
                    identity.selection_input_sha256,
                    "2026-01-01T00:00:00Z",
                ),
            )
        with pytest.raises(GateFailureError, match="unusable state 'planned'"):
            _persist(connection, snapshot_id)


def test_existing_failed_run_fails_closed_rather_than_reconstructing_silently(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("existing-failed-run-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _seed_reason_codes(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        candidate_set = load_frozen_entity_candidates(connection, snapshot_id)
        identity = build_entity_selection_run_identity(
            candidate_set, quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS
        )
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_selection_runs "
                "(selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
                "quota_policy_version, search_node_limit, run_state, selection_input_sha256, "
                "selected_entity_count, selected_accession_count, failure_reason_code, "
                "started_at_utc, finished_at_utc) "
                "VALUES (?, ?, ?, ?, ?, ?, 'failed', ?, 0, 0, 'PILOT_SELECTION_INFEASIBLE', "
                "?, ?)",
                (
                    identity.selection_run_id,
                    snapshot_id,
                    identity.selection_seed,
                    pilot_policy.PILOT_SELECTOR_POLICY_VERSION,
                    _QUOTA_POLICY_VERSION_FOR_TESTS,
                    identity.node_limit,
                    identity.selection_input_sha256,
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T01:00:00Z",
                ),
            )
        with pytest.raises(GateFailureError, match="unusable state 'failed'"):
            _persist(connection, snapshot_id)


def test_existing_incomplete_running_run_fails_closed_rather_than_reconstructing_silently(
    tmp_path: Path,
) -> None:
    """A 'running' row with no persisted 24-entity draft yet (e.g. a crash between
    the planned->running transition and result persistence) is not a usable
    reconstruction target either."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("existing-incomplete-running-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        build_minimal_feasible_snapshot(connection, snapshot_id=snapshot_id)
        candidate_set = load_frozen_entity_candidates(connection, snapshot_id)
        identity = build_entity_selection_run_identity(
            candidate_set, quota_policy_version=_QUOTA_POLICY_VERSION_FOR_TESTS
        )
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_selection_runs "
                "(selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
                "quota_policy_version, search_node_limit, run_state, selection_input_sha256, "
                "started_at_utc) VALUES (?, ?, ?, ?, ?, ?, 'running', ?, ?)",
                (
                    identity.selection_run_id,
                    snapshot_id,
                    identity.selection_seed,
                    pilot_policy.PILOT_SELECTOR_POLICY_VERSION,
                    _QUOTA_POLICY_VERSION_FOR_TESTS,
                    identity.node_limit,
                    identity.selection_input_sha256,
                    "2026-01-01T00:00:00Z",
                ),
            )
        with pytest.raises(GateFailureError, match="unusable state 'running'"):
            _persist(connection, snapshot_id)


def test_existing_infeasible_terminal_run_reconstructs_normally_on_repeat_call(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("existing-infeasible-terminal-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _seed_reason_codes(connection)
        build_infeasible_snapshot_missing_industry(connection, snapshot_id=snapshot_id)
        first = _persist(connection, snapshot_id)
        assert first.run_state == "infeasible"
        second = _persist(connection, snapshot_id, event_id="evt-repeat-infeasible")
        assert second == first
