"""Read-only recovery-state inspection (`Docs/m3/templates/interrupted_run_recovery.md`).

Two properties matter more than any individual determination:

**Inspection never repairs.** The template is explicit: `m3 recovery-state` "never adopts,
quarantines, rebuilds, reconciles, resumes, or calls `observation_catalog.reconcile()`"
(`interrupted_run_recovery.md:33-34`). The master plan deliverable is "the read-only
recovery-state inspection surface **and proof that it cannot invoke a writer**". These tests
supply that proof three ways: the module imports no writer, the catalog connection refuses
writes at the SQLite level, and every observable byte is unchanged across an inspection.

**`UNDETERMINED` is a stop condition, not a judgement call.** The governing documents name exactly
two triggers — a broken receipt chain and a row without its object — and deliberately do not give a
finer per-condition split. These tests pin those two literally and do not invent others.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from disclosure_drift.m3 import recovery as recovery_module
from disclosure_drift.m3.acquisition import register_acquisition_run
from disclosure_drift.m3.receipt import (
    ExecutionReceipt,
    ReceiptValidationError,
    canonical_bytes,
    write_receipt,
)
from disclosure_drift.m3.recovery import (
    CARRY_IN_ACQUISITION_WINDOW,
    CARRY_IN_APPROVED_REQUEST_CEILING,
    CARRY_IN_AUTHORITY_SCHEMA_VERSION,
    CARRY_IN_AUTHORIZING_DECISION_REFERENCE,
    CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT,
    CARRY_IN_HISTORICAL_ROUTE_ALLOCATION,
    CARRY_IN_REQUEST_PLAN_SHA256,
    RECOVERY_DETERMINATIONS,
    ConditionResult,
    RecoveryInspectionError,
    RecoveryState,
    _inspect_store,
    carry_in_checkpoint_disagreement,
    carry_in_checkpoint_key,
    establish_terminal_state,
    inspect_receiptless_first_invocation,
    inspect_recovery_state,
    read_only_catalog,
    walk_receipt_chain,
)
from disclosure_drift.m3.request_plan import (
    LEGACY_UNBOUND_PLAN,
    RequestPlan,
    build_m3_2a_request_plan,
)
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.http_client import FetchResult
from disclosure_drift.sec.observation_catalog import ObservationRecorder
from disclosure_drift.sec.raw_store import RawStore
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.storage.catalog import CatalogWriter

URL = "https://www.sec.gov/files/company_tickers.json"
_BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"

# Fixed instants for every ordering the receiptless attribution proves. Correctness never reads
# the test machine's clock (Decision 051 §11 item 3): each fixture event is pinned to one of these,
# and the proofs below are about their durable order, not about when the suite runs.
_BEFORE_RUN_AT = "2026-07-01T00:00:00Z"  # strictly before the fixture run's registered start
_REGISTERED_AT = "2026-08-01T12:00:00Z"  # the fixture run's registered start instant
_IN_WINDOW_AT = "2026-08-02T00:00:00Z"  # inside the run, before any fixture reservation
_RESERVED_AT = "2026-08-04T00:00:00Z"  # the fixture ledger reservation's pre-send commit
_AFTER_RESERVATION_AT = "2026-08-04T00:00:05Z"  # after the reservation: a post-ledger retrieval
_LATER_RUN_AT = "2026-08-05T00:00:00Z"  # a later governed acquisition run's start
_AFTER_LATER_RUN_AT = "2026-08-06T00:00:00Z"  # after the later run began: bounded out


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def observation(tree: DataTree) -> SourceObservation:
    """One stored, verifiable source observation, at a fixed instant inside the fixture run.

    The retrieval instant is pinned (after `_REGISTERED_AT`, before `_RESERVED_AT`) so every
    ordering the receiptless attribution proves is fixed evidence, never the test machine's clock.
    """
    return SnapshotStore(tree).record(
        FetchResult(
            outcome="retrieved",
            source_id="sec_company_tickers",
            url=URL,
            purpose="census ticker alias evidence",
            status=200,
            body=b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC"}}',
            etag='"fixture"',
            declared_content_type="application/json",
            attempts=1,
        ),
        retrieved_at_utc=_IN_WINDOW_AT,
    )


def build_catalog(tmp_path: Path, *, with_observation: bool = True) -> DataTree:
    """A migrated catalog with, optionally, one committed observation and its object."""
    tree = DataTree.from_root(tmp_path / "data")
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        if with_observation:
            recorder = ObservationRecorder(writer, tree)
            recorder.record(observation(tree))
            recorder.flush_projection()
    return tree


def plan() -> RequestPlan:
    """A small deterministic plan, so headroom arithmetic has real numbers."""
    return build_m3_2a_request_plan(
        coverage_start=date(2024, 1, 1),
        coverage_end=date(2024, 6, 30),
        as_of_date=date(2024, 6, 30),
        include_open_quarter=False,
        calendar_year=2024,
        calendar_evidence_entry_count=0,
        already_satisfied_index_keys=frozenset(),
        requests_per_second=5.0,
    )


def receipt(**overrides: object) -> ExecutionReceipt:
    """A `live` receipt describing an interrupted acquisition."""
    fields: dict[str, object] = {
        "command_name": "m3 acquire",
        "command_version": "m3.2a/1.0",
        "phase": "M3.2A",
        "invocation_mode": "live",
        "configuration_fingerprint": "a" * 64,
        "migration_chain_head": "0013_m23_manifest_lifecycle_guards",
        "started_at_utc": "2026-08-01T12:00:00Z",
        "completed_at_utc": "2026-08-01T12:00:09Z",
        "elapsed_seconds": 9.0,
        "source_registry_version": "m2.2-source-registry/1.0",
        "index_plan_policy_version": "quarterly-index-instances/2.0",
        "request_plan_schema_version": "m3-request-plan/1.0",
        "parser_versions": {"company-tickers": "1.0"},
        "acquisition_window": "M3.2A",
        "request_plan_id": "plan-0001",
        "request_plan_sha256": plan().request_plan_sha256,
        "approved_request_ceiling": 200,
        "planned_logical_request_count": 7,
        "maximum_physical_attempt_count": 60,
        "planned_per_route": {"sec_company_tickers": 7},
        "actual_logical_request_count": 1,
        "actual_physical_attempt_count": 1,
        "actual_per_route": {
            "sec_company_tickers": {"logical_request_count": 1, "physical_attempt_count": 1},
        },
        "response_classification_totals": {
            "proceed": 1,
            "retry": 0,
            "retry_after": 0,
            "cooldown": 0,
            "fail": 0,
            "quarantine": 0,
        },
        "status_code_totals": {"200": 1},
        "raw_object_count": 1,
        "duplicate_object_count": 0,
        "cache_hit_count": 0,
        "not_modified_count": 0,
        "quarantined_object_count": 0,
        "redirect_hop_count": 0,
        "cooldown_count": 0,
        "schema_drift_outcome": "none",
        "schema_drift_event_count": 0,
        "completion_status": "interrupted",
        "reason_code": "SEC_ACQUISITION_INTERRUPTED",
        "reason_detail": "the acquisition was interrupted before completion.",
        "interruption_state": "after_catalog_commit",
    }
    fields.update(overrides)
    return ExecutionReceipt(**fields)


def rehearsal_receipt() -> ExecutionReceipt:
    """A `rehearsal` receipt, which carries no request_plan_sha256 by classification."""
    return ExecutionReceipt(
        command_name="m3 rehearse",
        command_version="m3.1a/1.0",
        phase="M3.1A",
        invocation_mode="rehearsal",
        configuration_fingerprint="a" * 64,
        migration_chain_head="0013_m23_manifest_lifecycle_guards",
        started_at_utc="2026-08-01T12:00:00Z",
        completed_at_utc="2026-08-01T12:00:04Z",
        elapsed_seconds=4.0,
        actual_logical_request_count=0,
        actual_physical_attempt_count=0,
        completion_status="interrupted",
        reason_code="SEC_ACQUISITION_INTERRUPTED",
        reason_detail="the rehearsal was interrupted.",
        interruption_state="after_catalog_commit",
        schema_drift_outcome="none",
        schema_drift_event_count=0,
        rehearsal_evidence_reference="m3-1a-rehearsal-report-0001",
    )


def write_chain(tmp_path: Path, *receipts: ExecutionReceipt) -> Path:
    """Write receipts to an external evidence root; return the head receipt's path."""
    checkout = tmp_path / "checkout"
    checkout.mkdir(exist_ok=True)
    evidence = tmp_path / "evidence"
    head: Path | None = None
    for item in receipts:
        head = write_receipt(item, evidence_root=evidence, repository_root=checkout)
    assert head is not None
    return head


def inspect(tmp_path: Path, tree: DataTree, head: Path) -> RecoveryState:
    """Run the inspector against a prepared tree."""
    return inspect_recovery_state(
        plan=plan(),
        receipt_chain_head=head,
        catalog_path=tree.catalog_database,
        data_root=tree.data_root,
    )


def catalog_snapshot(tree: DataTree) -> dict[str, object]:
    """Every byte and row an inspection could plausibly disturb."""
    with sqlite3.connect(tree.catalog_database) as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
            for table in (
                "census_source_observations",
                "census_observation_reasons",
                "census_recovery_events",
                "census_recovery_states",
                "raw_objects",
            )
        }
    files = {
        str(path.relative_to(tree.data_root)): path.read_bytes()
        for path in sorted(tree.data_root.rglob("*"))
        if path.is_file() and path.suffix != ".db"
    }
    return {"counts": counts, "files": files}


# --------------------------------------------------------------------------- #
# Vocabulary
# --------------------------------------------------------------------------- #
def test_the_three_determinations_are_the_specified_set() -> None:
    assert set(RECOVERY_DETERMINATIONS) == {"SAFE", "UNSAFE", "UNDETERMINED"}


# --------------------------------------------------------------------------- #
# Proof that the inspector cannot invoke a writer
# --------------------------------------------------------------------------- #
def test_the_module_imports_no_writer() -> None:
    """The strongest available static proof: no writer name is bound in the module at all."""
    for forbidden in (
        "reconcile",
        "record_recovery_events",
        "rebuild_audit_projection",
        "ObservationRecorder",
        "CatalogWriter",
        "RawStore",
    ):
        assert not hasattr(recovery_module, forbidden), (
            f"{forbidden} is reachable from m3.recovery; the inspector must be provably unable "
            f"to invoke a writer"
        )


def test_the_inspection_connection_refuses_writes_at_the_sqlite_level(tmp_path: Path) -> None:
    """`PRAGMA query_only` makes a write fail closed rather than rely on discipline."""
    tree = build_catalog(tmp_path)
    with recovery_module.read_only_catalog(tree.catalog_database) as connection:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM census_source_observations")
        assert connection.execute("SELECT COUNT(*) FROM census_source_observations").fetchone()


def test_inspection_changes_no_row_and_no_byte(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())
    before = catalog_snapshot(tree)

    inspect(tmp_path, tree, head)

    assert catalog_snapshot(tree) == before


def test_inspection_creates_no_quarantine_object(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    inspect(tmp_path, tree, head)

    assert not list(tree.quarantine.glob("*"))


def test_inspection_leaves_an_orphan_in_place_rather_than_adopting_it(tmp_path: Path) -> None:
    """An orphan is an object on disk with no committed row. `reconcile` would adopt or
    quarantine it; the inspector must do neither."""
    tree = build_catalog(tmp_path, with_observation=False)
    orphan = tree.raw_bulk / "orphan-object.json"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_bytes(b'{"orphan":true}')
    RawStore.lineage_path(orphan).write_text('{"intent":"synthetic"}', encoding="utf-8")
    head = write_chain(tmp_path, receipt())
    before = catalog_snapshot(tree)

    inspect(tmp_path, tree, head)

    assert catalog_snapshot(tree) == before
    assert orphan.is_file()


def test_inspection_does_not_remove_a_partial_file(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    partial = tree.raw_indexes / "interrupted.json.abc123.part"
    partial.parent.mkdir(parents=True, exist_ok=True)
    partial.write_bytes(b"half a body")
    head = write_chain(tmp_path, receipt())

    inspect(tmp_path, tree, head)

    assert partial.is_file()
    assert partial.read_bytes() == b"half a body"


# --------------------------------------------------------------------------- #
# UNDETERMINED — the two named triggers, and only those
# --------------------------------------------------------------------------- #
def test_a_broken_receipt_chain_is_undetermined(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    # The head names a predecessor that was never written.
    head = write_chain(
        tmp_path,
        receipt(recovery_predecessor_receipt_id="c" * 64, consumed_request_count_carried_forward=4),
    )

    state = inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert "chain" in state.basis.lower()


def test_a_broken_chain_is_never_reconstructed_from_memory(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(
        tmp_path,
        receipt(recovery_predecessor_receipt_id="c" * 64, consumed_request_count_carried_forward=4),
    )

    state = inspect(tmp_path, tree, head)

    # The missing predecessor is reported as missing, not invented.
    assert state.receipt_chain == (head.name.split("receipt-")[1].removesuffix(".json"),)


def test_a_row_without_its_object_is_undetermined(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())
    # Remove the stored object, leaving its committed row behind.
    for path in sorted(tree.data_root.rglob("*.json*")):
        if path.is_file() and "audit" not in path.parts and not path.name.endswith(".lineage.json"):
            path.unlink()
            break

    state = inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"


def test_a_resolvable_chain_is_walked_oldest_last(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    first = receipt(completion_status="interrupted", command_version="m3.2a/0.9")
    checkout = tmp_path / "checkout"
    checkout.mkdir(exist_ok=True)
    evidence = tmp_path / "evidence"
    write_receipt(first, evidence_root=evidence, repository_root=checkout)
    second = receipt(
        recovery_predecessor_receipt_id=first.receipt_id,
        consumed_request_count_carried_forward=1,
    )
    head = write_receipt(second, evidence_root=evidence, repository_root=checkout)

    state = inspect(tmp_path, tree, head)

    assert state.receipt_chain == (second.receipt_id, first.receipt_id)
    assert state.determination in RECOVERY_DETERMINATIONS


def test_the_consumed_attempts_are_summed_across_the_chain(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir(exist_ok=True)
    evidence = tmp_path / "evidence"
    first = receipt(command_version="m3.2a/0.9")
    write_receipt(first, evidence_root=evidence, repository_root=checkout)
    second = receipt(
        recovery_predecessor_receipt_id=first.receipt_id,
        consumed_request_count_carried_forward=1,
    )
    head = write_receipt(second, evidence_root=evidence, repository_root=checkout)

    state = inspect(tmp_path, tree, head)

    assert state.consumed_physical_attempts == 2  # one per receipt in the chain


# --------------------------------------------------------------------------- #
# Each determination is actually reachable
# --------------------------------------------------------------------------- #
def test_a_clean_interrupted_run_is_safe(tmp_path: Path) -> None:
    """Without this, the inspector could never return SAFE and every other test would still pass."""
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    state = inspect(tmp_path, tree, head)

    assert state.determination == "SAFE"
    assert state.resume_authorized
    assert all(condition.status != "NOT MET" for condition in state.conditions)


def test_an_orphan_is_unsafe_not_undetermined(tmp_path: Path) -> None:
    """An orphan has a known cause, so a separately authorized repair can correct it."""
    tree = build_catalog(tmp_path)
    orphan = tree.raw_bulk / "orphan-object.json"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_bytes(b'{"orphan":true}')
    RawStore.lineage_path(orphan).write_text('{"intent":"synthetic"}', encoding="utf-8")
    head = write_chain(tmp_path, receipt())

    state = inspect(tmp_path, tree, head)

    assert state.determination == "UNSAFE"
    assert state.orphan_object_count == 1
    assert not state.resume_authorized
    assert "repair" in state.required_action.lower()


def test_the_remainder_fits_when_nothing_has_been_consumed(tmp_path: Path) -> None:
    """The ceiling is built per route, so a run that completed nothing needs exactly all of it."""
    tree = build_catalog(tmp_path, with_observation=False)
    head = write_chain(
        tmp_path,
        receipt(
            actual_logical_request_count=0,
            actual_physical_attempt_count=0,
            actual_per_route={
                "sec_company_tickers": {
                    "logical_request_count": 0,
                    "physical_attempt_count": 0,
                },
            },
            status_code_totals={"200": 0},
            raw_object_count=0,
            response_classification_totals={
                "proceed": 0,
                "retry": 0,
                "retry_after": 0,
                "cooldown": 0,
                "fail": 0,
                "quarantine": 0,
            },
        ),
    )

    state = inspect(tmp_path, tree, head)

    headroom = next(item for item in state.conditions if item.number == "8.8")
    assert headroom.status == "MET"


# --------------------------------------------------------------------------- #
# The conditions that gate a resume must be able to fail
# --------------------------------------------------------------------------- #
def test_a_plan_hash_that_differs_from_the_chain_is_unsafe(tmp_path: Path) -> None:
    """Resuming against a different plan would spend a budget nobody approved."""
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt(request_plan_sha256="b" * 64))

    state = inspect(tmp_path, tree, head)

    hash_condition = next(item for item in state.conditions if item.number == "8.10")
    assert hash_condition.status == "NOT MET"
    assert state.determination == "UNSAFE"


def test_a_chain_recording_no_plan_hash_cannot_establish_it_is_unchanged(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, rehearsal_receipt())

    state = inspect(tmp_path, tree, head)

    hash_condition = next(item for item in state.conditions if item.number == "8.10")
    assert hash_condition.status == "NOT MET"


def test_a_chain_without_an_interruption_state_is_not_established(tmp_path: Path) -> None:
    """8.2 must be decided by the recorded state, not by whether the chain resolved."""
    tree = build_catalog(tmp_path)
    head = write_chain(
        tmp_path,
        receipt(
            completion_status="complete",
            reason_code=None,
            reason_detail=None,
            interruption_state=None,
        ),
    )

    state = inspect(tmp_path, tree, head)

    established = next(item for item in state.conditions if item.number == "8.2")
    assert established.status == "NOT MET"
    assert state.determination == "UNSAFE"


def test_the_two_conditions_are_decided_independently(tmp_path: Path) -> None:
    """8.2 was previously a copy of 8.1; a resolved chain must not imply an established state."""
    tree = build_catalog(tmp_path)
    head = write_chain(
        tmp_path,
        receipt(
            completion_status="complete",
            reason_code=None,
            reason_detail=None,
            interruption_state=None,
        ),
    )

    state = inspect(tmp_path, tree, head)

    resolved = next(item for item in state.conditions if item.number == "8.1")
    established = next(item for item in state.conditions if item.number == "8.2")
    assert resolved.status == "MET"
    assert established.status == "NOT MET"


# --------------------------------------------------------------------------- #
# Determination surface
# --------------------------------------------------------------------------- #
def test_a_clean_state_records_every_condition(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    state = inspect(tmp_path, tree, head)

    numbers = [condition.number for condition in state.conditions]
    # 8.12 is the Decision 055 §7.5 carry-in/checkpoint cross-check, recorded on every inspection
    # and `N/A` where the chain's root carries no baseline to cross-check.
    assert numbers == [f"8.{index}" for index in range(1, 13)]


def test_every_condition_carries_one_of_the_three_statuses(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    state = inspect(tmp_path, tree, head)

    for condition in state.conditions:
        assert condition.status in {"MET", "NOT MET", "N/A"}


def test_the_selection_condition_is_not_applicable_without_a_selection_run(
    tmp_path: Path,
) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    state = inspect(tmp_path, tree, head)

    selection = next(item for item in state.conditions if item.number == "8.11")
    assert selection.status == "N/A"


def test_a_determination_always_states_its_basis(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    state = inspect(tmp_path, tree, head)

    assert state.basis.strip()
    assert state.required_action.strip()


def test_only_safe_authorizes_a_resume(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    state = inspect(tmp_path, tree, head)

    assert state.resume_authorized is (state.determination == "SAFE")


def test_the_record_carries_no_absolute_path(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    record = repr(inspect(tmp_path, tree, head).as_record())

    assert str(tmp_path) not in record


# --------------------------------------------------------------------------- #
# Input handling
# --------------------------------------------------------------------------- #
def test_a_missing_catalog_is_refused_rather_than_determined(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    with pytest.raises(RecoveryInspectionError, match="catalog"):
        inspect_recovery_state(
            plan=plan(),
            receipt_chain_head=head,
            catalog_path=tmp_path / "absent" / "catalog.db",
            data_root=tree.data_root,
        )


def test_a_missing_head_receipt_is_refused(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)

    with pytest.raises(RecoveryInspectionError, match="receipt"):
        inspect_recovery_state(
            plan=plan(),
            receipt_chain_head=tmp_path / "evidence" / "receipts" / "receipt-absent.json",
            catalog_path=tree.catalog_database,
            data_root=tree.data_root,
        )


# --------------------------------------------------------------------------- #
# Explicit receiptless first-invocation inspection (Decision 051 §7.4, §8; §5A)
# --------------------------------------------------------------------------- #
_RUN_ID = "incident-run-01"


def _register(
    tree: DataTree, run_id: str = _RUN_ID, *, started_at_utc: str = _REGISTERED_AT
) -> None:
    register_acquisition_run(
        catalog_path=tree.catalog_database,
        lock_directory=tree.locks,
        census_run_id=run_id,
        window="M3.2A",
        started_at_utc=started_at_utc,
        detail="interrupted initial invocation fixture",
    )


def _reserve(
    tree: DataTree,
    run_id: str,
    *,
    attempt_id: str,
    ordinal: int,
    url: str = _BULK_URL,
    started_at_utc: str = _RESERVED_AT,
) -> None:
    """Commit one durable `started` reservation, exactly as the pre-send ledger would."""
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.insert(
            "ops_retrieval_attempts",
            {
                "retrieval_attempt_id": attempt_id,
                "job_id": run_id,
                "source_url_canonical": url,
                "logical_role": "bulk_archive",
                "attempt_number": ordinal,
                "attempt_state": "started",
                "started_at_utc": started_at_utc,
            },
        )


def _receiptless(tree: DataTree, run_id: str = _RUN_ID) -> RecoveryState:
    return inspect_receiptless_first_invocation(
        plan=plan(),
        census_run_id=run_id,
        catalog_path=tree.catalog_database,
        data_root=tree.data_root,
    )


def _row_counts(tree: DataTree) -> tuple[int, int]:
    with sqlite3.connect(f"file:{tree.catalog_database}?mode=ro", uri=True) as connection:
        return (
            connection.execute("SELECT COUNT(*) FROM ops_retrieval_attempts").fetchone()[0],
            connection.execute("SELECT COUNT(*) FROM ops_ingestion_jobs").fetchone()[0],
        )


def test_receiptless_refuses_an_unregistered_run(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path, with_observation=False)
    with pytest.raises(RecoveryInspectionError, match="does not resolve"):
        _receiptless(tree, "no-such-run")


def test_receiptless_refuses_a_missing_catalog(tmp_path: Path) -> None:
    with pytest.raises(RecoveryInspectionError, match="does not exist"):
        inspect_receiptless_first_invocation(
            plan=plan(),
            census_run_id=_RUN_ID,
            catalog_path=tmp_path / "data" / "absent.sqlite3",
            data_root=tmp_path / "data",
        )


def test_receiptless_never_returns_safe_for_a_clean_catalog(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path, with_observation=True)  # committed, matched, no orphan
    _register(tree)
    state = _receiptless(tree)
    assert state.determination == "UNSAFE"  # never resume-eligible, but not ambiguous
    assert not state.resume_authorized
    assert state.receipt_chain == ()  # no receipt was walked
    assert state.interruption_state is None
    # The receipt-based conditions can never be met in this mode, which is what keeps SAFE
    # unreachable by construction.
    receipt_conditions = {c.number: c.status for c in state.conditions}
    assert receipt_conditions["8.1"] == "NOT MET"
    assert receipt_conditions["8.2"] == "NOT MET"
    assert receipt_conditions["8.10"] == "NOT MET"


def test_receiptless_incident_orphan_is_undetermined_with_consumed_one(tmp_path: Path) -> None:
    # The interrupted initial T5 invocation: a preserved raw object with lineage attempts=1, no
    # committed observation, and no receipt — the surfaces disagree (Decision 051 §3.12, §15).
    tree = build_catalog(tmp_path, with_observation=False)
    observation(tree)  # writes the raw object and its lineage, but commits no catalog row
    _register(tree)
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"
    assert state.consumed_physical_attempts == 1  # derived from durable raw lineage, not a literal
    assert state.orphan_object_count >= 1
    assert not state.resume_authorized


def test_receiptless_consumed_is_incident_baseline_plus_reservations(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path, with_observation=False)
    observation(tree)  # the incident baseline: raw lineage records attempts=1
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)  # one subsequent reservation
    state = _receiptless(tree)
    # 1 baseline + 1 reservation = 2. Never reset to 0, never double-counted to 3.
    assert state.consumed_physical_attempts == 2
    assert state.determination == "UNDETERMINED"


def test_receiptless_reservation_alone_is_counted_without_a_baseline(tmp_path: Path) -> None:
    # No raw object exists, so the baseline is 0; a single reservation is the whole consumed count.
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)
    state = _receiptless(tree)
    assert state.consumed_physical_attempts == 1
    assert state.determination in {"UNSAFE", "UNDETERMINED"}


def test_receiptless_determination_is_only_unsafe_or_undetermined(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path, with_observation=False)
    observation(tree)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)
    state = _receiptless(tree)
    assert state.determination in {"UNSAFE", "UNDETERMINED"}
    assert state.determination != "SAFE"
    assert not state.resume_authorized


def test_receiptless_inspection_writes_nothing(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path, with_observation=False)
    observation(tree)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)
    before = _row_counts(tree)
    _receiptless(tree)
    _receiptless(tree)  # repeatable and inert
    assert _row_counts(tree) == before  # no row added, removed, or mutated


# --------------------------------------------------------------------------- #
# Correction B — exact consumed-attempt reconciliation. The ledger is the primary surface, every
# selected-run reservation counts exactly once, and raw lineage enters only by durable run/event
# identity and order — never URL equality alone (Decision 051 §5, §6; data dictionary §5A;
# contract §12 accounting rules 1-5).
# --------------------------------------------------------------------------- #
def _write_lineage_manifest(
    tree: DataTree,
    *,
    source_id: str,
    attempts: object,
    name: str,
    url: str = URL,
    retrieved_at_utc: str | None = None,
) -> None:
    """Write one raw-object lineage manifest directly, for precise accounting-scope fixtures.

    The real store writes these beside a promoted object; here one is written alone so a single
    test controls its source identity, canonical URL, recorded attempt count, and retrieval
    instant without also standing up an object — which the pre-ledger accounting reads and the
    orphan scan ignores. ``retrieved_at_utc=None`` omits the field, for the absent-evidence cases.
    """
    raw_dir = tree.data_root / "raw" / "bulk"
    raw_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "manifest_version": "raw-object-lineage/1.0",
        "source_id": source_id,
        "requested_url": url,
        "final_url": url,
        "attempts": attempts,
    }
    if retrieved_at_utc is not None:
        payload["retrieved_at_utc"] = retrieved_at_utc
    (raw_dir / f"{name}.lineage.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_receiptless_counts_a_post_ledger_segment_once_not_twice(tmp_path: Path) -> None:
    """A retrieval whose preceding reservation accounts for it counts once, never twice."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    # A post-ledger bulk-archive retrieval: the reservation's pre-send commit strictly precedes
    # the retrieval instant its lineage records, and fully accounts for its one attempt.
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="submissions.zip",
        url=_BULK_URL,
        retrieved_at_utc=_AFTER_RESERVATION_AT,
    )
    state = _receiptless(tree)
    # The ledger is the authority for that segment; its lineage is not added a second time.
    assert state.consumed_physical_attempts == 1
    assert state.determination != "SAFE"


def test_receiptless_a_later_same_url_reservation_never_erases_earlier_lineage(
    tmp_path: Path,
) -> None:
    """Pre-ledger lineage plus a genuinely later same-URL reservation are two consumed attempts.

    URL identity does not prove event identity: the reservation's pre-send commit is strictly
    *after* the retrieval the lineage records, so it cannot be the reservation that accounted for
    that send. Both events consumed an attempt — the historical pre-ledger send (Decision 051 §5)
    and the durable reservation (§5A rule 2) — and neither absorbs the other.
    """
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="submissions.zip",
        url=_BULK_URL,
        retrieved_at_utc=_IN_WINDOW_AT,  # retrieved first...
    )
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)  # ...reserved later, same URL
    state = _receiptless(tree)
    assert state.consumed_physical_attempts == 2
    assert state.determination != "SAFE"


def test_receiptless_excludes_same_source_lineage_that_predates_the_selected_run(
    tmp_path: Path,
) -> None:
    """Older same-source lineage never enters the selected run's count.

    A manifest retrieved strictly before the run's registered start is proven to belong to an
    earlier accounting, however exactly its source and URL match the selected run's plan. Only the
    segment inside the run's window counts (Decision 051 §6.4's boundary discipline).
    """
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=5,
        name="older-run-segment",
        url=_BULK_URL,
        retrieved_at_utc=_BEFORE_RUN_AT,  # strictly before the selected run's start
    )
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="selected-run-segment",
        url=_BULK_URL,
        retrieved_at_utc=_IN_WINDOW_AT,
    )
    state = _receiptless(tree)
    assert state.consumed_physical_attempts == 1  # never 6: the older 5 are not this run's
    assert state.determination != "SAFE"


def test_receiptless_a_later_governed_run_start_bounds_later_lineage(tmp_path: Path) -> None:
    """Lineage retrieved after a later governed acquisition run began is never counted here."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _register(tree, "later-run-01", started_at_utc=_LATER_RUN_AT)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=3,
        name="later-run-segment",
        url=_BULK_URL,
        retrieved_at_utc=_AFTER_LATER_RUN_AT,  # after the later governed run began
    )
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="selected-run-segment",
        url=_BULK_URL,
        retrieved_at_utc=_IN_WINDOW_AT,
    )
    state = _receiptless(tree)
    assert state.consumed_physical_attempts == 1  # the 3 after the later run's start are excluded
    assert state.determination != "SAFE"


def test_receiptless_partial_ledger_coverage_is_undetermined_with_a_floor(tmp_path: Path) -> None:
    """Reservations that only partially account for a segment's attempts fail closed."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)  # one preceding reservation...
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=2,  # ...for a segment recording two sends: partially matched evidence
        name="submissions.zip",
        url=_BULK_URL,
        retrieved_at_utc=_AFTER_RESERVATION_AT,
    )
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"
    assert state.consumed_physical_attempts == 1  # the ledger's provable floor, never a guess
    assert "durable floor" in state.basis


def test_receiptless_an_in_scope_manifest_without_a_retrieval_instant_is_undetermined(
    tmp_path: Path,
) -> None:
    """A manifest that cannot be ordered against the run boundaries is never silently placed."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _write_lineage_manifest(
        tree, source_id="sec_bulk_submissions", attempts=1, name="unordered", url=_BULK_URL
    )
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"
    assert "cannot be reconciled" in state.basis
    assert state.consumed_physical_attempts == 0  # nothing provable: the floor holds at zero


def test_receiptless_a_malformed_retrieval_instant_is_undetermined(tmp_path: Path) -> None:
    """A retrieval instant that does not parse as a strict UTC instant proves no order."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="malformed-instant",
        url=_BULK_URL,
        retrieved_at_utc="not-an-instant",
    )
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"
    assert "cannot be reconciled" in state.basis


def test_receiptless_a_reservation_at_the_exact_retrieval_instant_is_undetermined(
    tmp_path: Path,
) -> None:
    """Equal instants prove no order between a reservation and a same-URL retrieval."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="simultaneous",
        url=_BULK_URL,
        retrieved_at_utc=_RESERVED_AT,  # exactly the reservation's commit instant
    )
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"
    assert state.consumed_physical_attempts == 1  # the reservation itself remains consumed


def test_receiptless_a_retrieval_at_the_selected_run_start_is_undetermined(tmp_path: Path) -> None:
    """A retrieval at exactly the run's registered start cannot be attributed to either side."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="boundary",
        url=_BULK_URL,
        retrieved_at_utc=_REGISTERED_AT,  # exactly the selected run's start instant
    )
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"
    assert state.consumed_physical_attempts == 0


def test_receiptless_a_retrieval_at_a_later_run_start_is_undetermined(tmp_path: Path) -> None:
    """A retrieval at exactly a later governed run's start is order-ambiguous, not excluded."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _register(tree, "later-run-01", started_at_utc=_LATER_RUN_AT)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="boundary",
        url=_BULK_URL,
        retrieved_at_utc=_LATER_RUN_AT,  # exactly the later run's start instant
    )
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"


def test_receiptless_a_manifest_without_source_identity_is_undetermined(tmp_path: Path) -> None:
    """Out-of-plan lineage is excluded only on proof; an absent identity is never proof."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    raw_dir = tree.data_root / "raw" / "bulk"
    raw_dir.mkdir(parents=True, exist_ok=True)
    payload = {"manifest_version": "raw-object-lineage/1.0", "attempts": 4}
    (raw_dir / "identityless.lineage.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
    )
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"
    assert state.consumed_physical_attempts == 0  # the 4 are never counted in, nor proven out


def test_receiptless_ignores_lineage_outside_the_plan_scope(tmp_path: Path) -> None:
    """Lineage for a source the interrupted run's plan does not include never changes the count."""
    tree = build_catalog(tmp_path, with_observation=False)
    observation(tree)  # the incident baseline: attempts=1, source_id in the plan
    _register(tree)
    _write_lineage_manifest(
        tree,
        source_id="sec_not_a_planned_route",
        attempts=5,
        name="unrelated",
        url="https://example.invalid/unrelated.json",
    )
    state = _receiptless(tree)
    # Only the in-scope incident attempt is counted; the unrelated 5 is excluded, never summed.
    assert state.consumed_physical_attempts == 1


def test_receiptless_fails_closed_on_a_malformed_in_scope_manifest(tmp_path: Path) -> None:
    """An in-scope manifest with no usable attempt count fails closed, never silently zero."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _write_lineage_manifest(
        tree,
        source_id="sec_company_tickers",
        attempts="not-a-count",
        name="broken",
        retrieved_at_utc=_IN_WINDOW_AT,  # provably in-window, so the attempt count is what fails
    )
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"
    assert "cannot be reconciled" in state.basis


def test_receiptless_fails_closed_on_an_unreadable_manifest(tmp_path: Path) -> None:
    """An unreadable lineage manifest is unattributable evidence, not silently a zero."""
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    raw_dir = tree.data_root / "raw" / "bulk"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "corrupt.lineage.json").write_text("{ not valid json", encoding="utf-8")
    state = _receiptless(tree)
    assert state.determination == "UNDETERMINED"


def test_receiptless_refuses_a_non_acquisition_job(tmp_path: Path) -> None:
    """The run id must be a governed M3.2 acquisition run, not merely any ingestion job."""
    tree = build_catalog(tmp_path, with_observation=False)
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.insert(
            "ops_ingestion_jobs",
            {
                "job_id": _RUN_ID,
                "job_kind": "m2_2_census",  # a real job row, but not an acquisition run
                "job_state": "running",
                "stage": "M3.2A",
                "started_at_utc": "2026-08-01T12:00:00Z",
            },
        )
    with pytest.raises(RecoveryInspectionError, match="not a governed M3.2 acquisition run"):
        _receiptless(tree)


def test_receiptless_refuses_a_run_whose_stage_is_a_different_window(tmp_path: Path) -> None:
    """A governed acquisition run for another window is not this plan's interrupted run."""
    tree = build_catalog(tmp_path, with_observation=False)
    register_acquisition_run(
        catalog_path=tree.catalog_database,
        lock_directory=tree.locks,
        census_run_id=_RUN_ID,
        window="M3.2B",  # a governed acquisition run, but for the other window
        started_at_utc="2026-08-01T12:00:00Z",
        detail="different-window fixture",
    )
    with pytest.raises(RecoveryInspectionError, match="records stage"):
        _receiptless(tree)  # plan() is M3.2A


# --------------------------------------------------------------------------- #
# M3-L14 — the global one-to-one reservation-consumption rule (Decision 055 §8, ruling 055-D).
#
# Coverage is decided across *all* owned receiptless lineage segments at once, not per manifest. A
# durable reservation may satisfy at most one segment, and any inability to establish an exact
# bijection is `UNDETERMINED` rather than a count that under-reports the durable floor.
# --------------------------------------------------------------------------- #
def test_receiptless_one_reservation_cannot_cover_two_owned_segments(tmp_path: Path) -> None:
    """The measured M3-L14 counterexample: 1 reservation + 2 owned same-URL segments.

    This is the exact case the independent rereview measured (limitations register **M3-L14**).
    Deciding coverage independently per manifest lets the single reservation satisfy *both*
    segments, reporting a consumed count of **1** with `UNSAFE` where the durable floor is **2**.
    Decision 055 §8 requires the fail-closed answer: one reservation can be consumed by at most one
    segment, the bijection cannot be established, and the determination is `UNDETERMINED`.
    """
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)  # exactly one durable reservation...
    for name in ("segment-one", "segment-two"):  # ...and two owned segments it could each cover
        _write_lineage_manifest(
            tree,
            source_id="sec_bulk_submissions",
            attempts=1,
            name=name,
            url=_BULK_URL,
            retrieved_at_utc=_AFTER_RESERVATION_AT,
        )

    state = _receiptless(tree)

    assert state.determination == "UNDETERMINED"  # never consumed count 1 with UNSAFE
    assert "durable floor" in state.basis
    assert not state.resume_authorized


def test_receiptless_a_reservation_is_consumed_by_at_most_one_segment(tmp_path: Path) -> None:
    """Two reservations and two owned same-URL segments still prove no exact assignment.

    Cardinality alone is not a bijection: both reservations precede both retrievals, so which
    reservation accounts for which segment is not provable. Fail closed rather than pair them by
    an arbitrary order.
    """
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)
    _reserve(tree, _RUN_ID, attempt_id="res-2", ordinal=2)
    for name in ("segment-one", "segment-two"):
        _write_lineage_manifest(
            tree,
            source_id="sec_bulk_submissions",
            attempts=1,
            name=name,
            url=_BULK_URL,
            retrieved_at_utc=_AFTER_RESERVATION_AT,
        )

    state = _receiptless(tree)

    assert state.determination == "UNDETERMINED"
    assert state.consumed_physical_attempts == 2  # the ledger's provable floor, never a guess


def test_receiptless_one_segment_with_two_eligible_reservations_is_undetermined(
    tmp_path: Path,
) -> None:
    """The **M3-L14** leftover counterexample: one counted attempt, two eligible reservations.

    The segment's single attempt is satisfiable — either reservation could account for it — so a
    rule that only asked "are there *enough* reservations?" reports coverage and a consumed count
    of 2 with `UNSAFE`. But one durable pre-send commit for that URL, before that retrieval, is
    then left unaccounted for by any lineage, and no exact bijection exists. Decision 055 §8 fails
    closed on the leftover contradiction rather than reporting a count it cannot prove.
    """
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)
    _reserve(tree, _RUN_ID, attempt_id="res-2", ordinal=2)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="only-segment",
        url=_BULK_URL,
        retrieved_at_utc=_AFTER_RESERVATION_AT,
    )

    state = _receiptless(tree)

    assert state.determination == "UNDETERMINED"
    assert state.consumed_physical_attempts == 2  # the ledger's provable floor, never a guess


def test_receiptless_one_segment_with_its_own_single_reservation_is_covered(
    tmp_path: Path,
) -> None:
    """The positive control for the leftover rule, so the refusal above is not blanket.

    One counted attempt against exactly one eligible reservation is a forced, exact assignment.
    The segment is covered, adds no second charge, and the count stands at the ledger's 1.
    """
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="only-segment",
        url=_BULK_URL,
        retrieved_at_utc=_AFTER_RESERVATION_AT,
    )

    state = _receiptless(tree)

    assert state.consumed_physical_attempts == 1, "covered exactly once, never double-charged"
    assert "exact ledger coverage is not provable" not in state.basis


def test_receiptless_two_distinct_url_segments_each_keep_their_own_reservation(
    tmp_path: Path,
) -> None:
    """Disjoint eligibility is still provable, so exact coverage survives the one-to-one rule.

    The positive half of the same rule: each reservation is eligible for exactly one segment, the
    assignment is forced, and neither segment adds a second charge. Without this, the correction
    could pass by making every multi-segment case `UNDETERMINED`.
    """
    tree = build_catalog(tmp_path, with_observation=False)
    _register(tree)
    _reserve(tree, _RUN_ID, attempt_id="res-1", ordinal=1, url=_BULK_URL)
    _reserve(tree, _RUN_ID, attempt_id="res-2", ordinal=2, url=URL)
    _write_lineage_manifest(
        tree,
        source_id="sec_bulk_submissions",
        attempts=1,
        name="bulk-segment",
        url=_BULK_URL,
        retrieved_at_utc=_AFTER_RESERVATION_AT,
    )
    _write_lineage_manifest(
        tree,
        source_id="sec_company_tickers",
        attempts=1,
        name="tickers-segment",
        url=URL,
        retrieved_at_utc=_AFTER_RESERVATION_AT,
    )

    state = _receiptless(tree)

    # Both segments are ledger-covered exactly once: the count is the two reservations, not four.
    assert state.consumed_physical_attempts == 2


# --------------------------------------------------------------------------- #
# The chain walker's carry-in arithmetic and its catalog cross-check
# (accepted Decision 055 §7.5, ruling 055-C)
#
#     cumulative = sum(actual_physical_attempt_count over every receipt in the chain)
#                + carried_forward of the single no-predecessor root only
#
# The root carry-in is added exactly once — never `N` alone, never double-counted.
# --------------------------------------------------------------------------- #
_AUTHORITY_SHA = "e" * 64


def frozen_plan() -> RequestPlan:
    """The **frozen** accepted M3.2A plan — the only one a carry-in may ever be bound to.

    Decision 055 §5 fixes the plan and its hash ``19be7bdc…`` and the cumulative ceiling ``801``,
    and both the artifact gate and the checkpoint cross-check now compare them literally. So a
    carry-in fixture built on this suite's small plan would not describe any burn the system can
    produce: it would exercise the cross-check against values no lawful consumption ever writes.
    """
    return build_m3_2a_request_plan(
        coverage_start=date(2009, 1, 1),
        coverage_end=date(2026, 6, 30),
        as_of_date=date(2026, 6, 30),
        include_open_quarter=False,
        calendar_year=2026,
        calendar_evidence_entry_count=0,
        already_satisfied_index_keys=frozenset(),
        requests_per_second=4.0,
        source_registry_version=LEGACY_UNBOUND_PLAN,
    )


def _carry_in_root(**overrides: object) -> ExecutionReceipt:
    """A clean carry-in root: no predecessor, a baseline of 1, and its authority hash.

    Its plan and ceiling are the frozen accepted ones, because that is what a lawful carry-in root
    records — the authority it consumed was bound to them literally before it could be admitted.
    """
    fields: dict[str, object] = {
        "consumed_request_count_carried_forward": 1,
        "carry_in_authority_sha256": _AUTHORITY_SHA,
        "request_plan_sha256": CARRY_IN_REQUEST_PLAN_SHA256,
        "approved_request_ceiling": CARRY_IN_APPROVED_REQUEST_CEILING,
    }
    fields.update(overrides)
    return receipt(**fields)


_CARRY_IN_RUN_ID = "carry-in-root-run-01"


def _checkpoint_document(**overrides: object) -> dict[str, object]:
    """The complete canonical consumption checkpoint (data dictionary §5B).

    Every value is the accepted Decision 055 one. The cross-check holds the durable record against
    the same constants, through the same validator, as the artifact gate holds the artifact — so a
    checkpoint carrying anything else records a burn the system could not have performed, however
    self-consistent it is and however well it agrees with the receipt beside it. Window, plan, and
    ceiling therefore also mirror the root receipt, which is exactly what one real burn produces:
    two surfaces recording the same accepted carry-in.
    """
    document: dict[str, object] = {
        "acquisition_window": CARRY_IN_ACQUISITION_WINDOW,
        "approved_request_ceiling": CARRY_IN_APPROVED_REQUEST_CEILING,
        "authority_sha256": _AUTHORITY_SHA,
        "authorized_census_run_id": _CARRY_IN_RUN_ID,
        "authorizing_decision_reference": CARRY_IN_AUTHORIZING_DECISION_REFERENCE,
        "consumed_request_count_carried_forward": CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT,
        "historical_route_allocation": dict(CARRY_IN_HISTORICAL_ROUTE_ALLOCATION),
        "request_plan_sha256": CARRY_IN_REQUEST_PLAN_SHA256,
        "schema_version": CARRY_IN_AUTHORITY_SCHEMA_VERSION,
    }
    document.update(overrides)
    return document


def _checkpoint_text(**overrides: object) -> str:
    """The exact bytes a lawful consumption writes: the canonical serialization, nothing else."""
    return canonical_bytes(_checkpoint_document(**overrides)).decode()


def _burn_authority(
    tree: DataTree,
    *,
    authority_sha256: str = _AUTHORITY_SHA,
    carried_forward: int = 1,
    value: str | None = None,
    register_run: bool = True,
    **overrides: object,
) -> None:
    """Record the durable consumption checkpoint a real carry-in root would have written.

    A real burn commits in the *same* transaction as its run's registration, so the fixture
    registers the run too: the cross-check proves the checkpoint's authorized run against durable
    catalog state, which is the only surface able to contradict it — no receipt field names a run.

    The stored value is the **canonical** serialization, because that is what
    ``CarryInAuthority.checkpoint_value`` writes and the cross-check now requires the stored TEXT to
    be exactly that. ``value`` overrides it for the cases that are *about* bad bytes.
    """
    if register_run:
        _register(tree, _CARRY_IN_RUN_ID)
    document = _checkpoint_document(
        authority_sha256=authority_sha256,
        consumed_request_count_carried_forward=carried_forward,
        **overrides,
    )
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.insert(
            "ops_checkpoints",
            {
                "checkpoint_key": carry_in_checkpoint_key(authority_sha256),
                "checkpoint_value": (
                    canonical_bytes(document).decode() if value is None else value
                ),
                "updated_at_utc": "2026-08-09T00:00:00Z",
            },
        )


def _carry_in_inspect(tmp_path: Path, tree: DataTree, head: Path) -> RecoveryState:
    """Inspect a carry-in chain against the frozen plan its receipts actually record."""
    return inspect_recovery_state(
        plan=frozen_plan(),
        receipt_chain_head=head,
        catalog_path=tree.catalog_database,
        data_root=tree.data_root,
    )


def test_the_walker_adds_the_root_carry_in_exactly_once(tmp_path: Path) -> None:
    """One receipt, one attempt, a baseline of 1: cumulative 2, never 1 and never 3."""
    head = write_chain(tmp_path, _carry_in_root())

    chain = walk_receipt_chain(head)

    assert chain.resolved
    assert chain.root_carried_forward == 1
    assert chain.consumed_physical_attempts == 2  # 1 carried in + 1 placed
    assert chain.root_carry_in_authority_sha256 == _AUTHORITY_SHA


def test_the_root_carry_in_is_counted_once_through_a_mixed_version_chain(tmp_path: Path) -> None:
    """A carry-in root under two resumes: the baseline is added once, at the root.

    Each receipt places one attempt, and each resume states the cumulative total before it. The
    walker must report 4 — three attempts plus the single carried-in baseline — rather than 7,
    which is what adding every receipt's stated carried-forward count would give.
    """
    root = _carry_in_root(command_version="m3.2a/0.9")
    middle = receipt(
        command_version="m3.2a/0.10",
        recovery_predecessor_receipt_id=root.receipt_id,
        consumed_request_count_carried_forward=2,  # the root's 1 carried in, plus its 1 attempt
    )
    head_receipt = receipt(
        recovery_predecessor_receipt_id=middle.receipt_id,
        consumed_request_count_carried_forward=3,
    )
    head = write_chain(tmp_path, root, middle, head_receipt)

    chain = walk_receipt_chain(head)

    assert chain.receipt_ids == (head_receipt.receipt_id, middle.receipt_id, root.receipt_id)
    assert chain.consumed_physical_attempts == 4  # never 3 (N alone), never 7 (double-counted)
    assert chain.root_carried_forward == 1


def test_an_ordinary_zero_baseline_chain_is_unchanged_by_the_carry_in_arithmetic(
    tmp_path: Path,
) -> None:
    """Every chain written before Decision 055 walks to exactly the count it always did."""
    root = receipt(command_version="m3.2a/0.9")
    head = write_chain(
        tmp_path,
        root,
        receipt(
            recovery_predecessor_receipt_id=root.receipt_id,
            consumed_request_count_carried_forward=1,
        ),
    )

    chain = walk_receipt_chain(head)

    assert chain.consumed_physical_attempts == 2
    assert chain.root_carried_forward == 0
    assert chain.root_carry_in_authority_sha256 is None


def test_a_carry_in_root_agreeing_with_its_checkpoint_is_not_undetermined(tmp_path: Path) -> None:
    """The positive control for every refusal below, and the strongest one available.

    A canonical checkpoint recording the accepted Decision 055 carry-in, a root receipt recording
    the same frozen plan and ceiling, and the governed run they burned alongside: the inspection
    reaches ``SAFE``. Nothing here is refused incidentally, so nothing below is refused vacuously.
    """
    tree = build_catalog(tmp_path)
    _burn_authority(tree)
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    statuses = {condition.number: condition.status for condition in state.conditions}
    assert statuses["8.12"] == "MET"
    assert state.determination == "SAFE"
    assert state.consumed_physical_attempts == 2


def test_a_carry_in_root_whose_checkpoint_is_missing_is_undetermined(tmp_path: Path) -> None:
    """§7.5: a claimed burn the catalog does not record cannot authorize continuation."""
    tree = build_catalog(tmp_path)  # no authority was ever burned here
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert not state.resume_authorized
    assert "no consumption checkpoint" in state.basis


def test_a_checkpoint_that_disagrees_with_the_root_receipt_is_undetermined(tmp_path: Path) -> None:
    """The two surfaces must agree exactly; neither is edited to match the other."""
    tree = build_catalog(tmp_path)
    _burn_authority(tree, carried_forward=7)  # the catalog says 7...
    head = write_chain(tmp_path, _carry_in_root())  # ...the receipt says 1

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert "disagree" in state.basis


def test_no_valid_receipt_can_claim_a_baseline_without_naming_its_authority() -> None:
    """The state is unreachable from either schema, and the cross-check still fails closed on it.

    Under `3.0` a non-zero baseline with no predecessor requires the authority hash; under `2.0` a
    carried-forward count requires a predecessor. So no valid receipt expresses "a root claiming a
    baseline from nowhere" at all. The cross-check refuses it anyway — defence in depth against a
    chain reaching it from somewhere these two tables do not govern.
    """
    with pytest.raises(ReceiptValidationError):
        receipt(consumed_request_count_carried_forward=1)  # 3.0: names no authority

    forged = recovery_module.ReceiptChainAccounting(
        receipt_ids=("a" * 64,),
        consumed_physical_attempts=2,
        interruption_state=None,
        resolved=True,
        detail="synthetic",
        root_carried_forward=1,
        root_carry_in_authority_sha256=None,
    )

    with sqlite3.connect(":memory:") as connection:
        disagreement = carry_in_checkpoint_disagreement(connection, forged)

    assert disagreement is not None
    assert "names no carry-in authority" in disagreement


# --------------------------------------------------------------------------- #
# The checkpoint is read as a whole document, not for one figure
# --------------------------------------------------------------------------- #
# Every case below is filed under the *correct* deterministic key and carries the *correct*
# carried-forward baseline. Comparing only the figure the arithmetic needs would pass all of them,
# which is exactly why the cross-check has to validate the record it is standing on.


@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        ({"request_plan_sha256": "b" * 64}, "different request plans"),
        ({"acquisition_window": "M3.2B"}, "different acquisition windows"),
        ({"approved_request_ceiling": 999}, "different approved ceilings"),
        ({"authorized_census_run_id": "never-registered-run"}, "no registered job"),
        ({"authorizing_decision_reference": "decision_055"}, "canonical 'Decision NNN'"),
        ({"schema_version": "m3-carry-in-authority/9.9"}, "declares schema"),
        ({"historical_route_allocation": {"sec_bulk_submissions": 4}}, "contradicts itself"),
        ({"historical_route_allocation": {"sec_not_a_route": 1}}, "not a registered source route"),
    ],
)
def test_a_correctly_keyed_checkpoint_with_a_wrong_field_is_undetermined(
    tmp_path: Path, override: dict[str, object], fragment: str
) -> None:
    """A right key and a matching baseline are not enough; the document must be the record."""
    tree = build_catalog(tmp_path)
    _burn_authority(tree, **override)
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert not state.resume_authorized
    assert fragment in state.basis


def test_a_checkpoint_whose_body_names_another_authority_is_undetermined(tmp_path: Path) -> None:
    """Filed under the right deterministic key, describing a different burn entirely.

    The key/document relationship is the one thing a lookup by key cannot check for itself: finding
    a row proves only that something was written there.
    """
    tree = build_catalog(tmp_path)
    _burn_authority(
        tree,
        value=_checkpoint_text(authority_sha256="d" * 64),
    )
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert "names a different authority" in state.basis


@pytest.mark.parametrize(
    ("value", "fragment"),
    [
        ("{not json", "not readable JSON"),
        ('["a", "list"]', "not a JSON object"),
        ('{"authority_sha256": "' + "e" * 64 + '"', "not readable JSON"),
        ('{"authority_sha256": "' + "e" * 64 + '"}', "missing required field"),
    ],
)
def test_a_malformed_checkpoint_document_is_undetermined(
    tmp_path: Path, value: str, fragment: str
) -> None:
    """Truncated, unparseable, and partial writes each fail closed rather than half-reading."""
    tree = build_catalog(tmp_path)
    _burn_authority(tree, value=value)
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert fragment in state.basis


def test_a_checkpoint_carrying_an_extra_field_is_undetermined(tmp_path: Path) -> None:
    """The record is a closed document: an unread field is refused, never ignored."""
    tree = build_catalog(tmp_path)
    _burn_authority(
        tree,
        value=_checkpoint_text(resume_authorized=True),
    )
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert "unpermitted field(s): resume_authorized" in state.basis


def test_two_checkpoints_claiming_one_authorized_run_are_undetermined(tmp_path: Path) -> None:
    """A run registers exactly once, so two authorities cannot both have burned alongside it."""
    tree = build_catalog(tmp_path)
    _burn_authority(tree)
    _burn_authority(tree, authority_sha256="c" * 64, register_run=False)
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert "same authorized run" in state.basis


# --------------------------------------------------------------------------- #
# The checkpoint must be *the* canonical record of *the* accepted carry-in
# --------------------------------------------------------------------------- #
# Two properties the cross-check above cannot get from agreement between surfaces:
#
# **The encoding is part of the record.** A consumption writes `canonical_bytes` of the closed
# document, so anything that merely parses to the right fields was written by something else.
#
# **Agreement is not authorization.** A forged root and a checkpoint forged to match it agree
# perfectly. Both are therefore held against the accepted Decision 055 constants — the same
# constants, through the same validator, as the artifact the operator supplies.


def test_a_semantically_identical_noncanonical_checkpoint_is_undetermined(tmp_path: Path) -> None:
    """Every field is right and every value is right; only the bytes are not what a burn writes."""
    tree = build_catalog(tmp_path)
    _burn_authority(tree, value=json.dumps(_checkpoint_document(), indent=2, sort_keys=True))
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert "not stored in canonical form" in state.basis


def test_a_duplicate_key_encoding_is_undetermined(tmp_path: Path) -> None:
    """`json.loads` keeps the last value silently, so the discarded one is never compared.

    The row below parses to exactly the accepted document — its *first* window value is the one no
    comparison would ever see. Canonical re-serialization is the only check that can notice.
    """
    canonical = _checkpoint_text()
    tree = build_catalog(tmp_path)
    _burn_authority(tree, value='{"acquisition_window":"M3.2B",' + canonical[1:])
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert "not stored in canonical form" in state.basis


@pytest.mark.parametrize(
    "allocation",
    [
        {"sec_bulk_submissions": 2, "sec_company_tickers": -1},
        {"sec_bulk_submissions": -1, "sec_company_tickers": 2},
        {"sec_bulk_submissions": True},
        {"": 1},
    ],
    ids=["negative-second", "negative-first", "boolean", "empty-key"],
)
def test_an_impossible_route_allocation_is_undetermined(
    tmp_path: Path, allocation: dict[str, object]
) -> None:
    """A negative count lets an allocation sum to a plausible baseline out of impossible parts.

    The first case is the measured one: two routes summing to the accepted baseline of ``1``, both
    registered, so every self-consistency comparison downstream passes on arithmetic no
    consumption could have produced.
    """
    tree = build_catalog(tmp_path)
    _burn_authority(tree, historical_route_allocation=allocation)
    head = write_chain(tmp_path, _carry_in_root())

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert not state.resume_authorized


@pytest.mark.parametrize(
    ("checkpoint_override", "root_override", "fragment"),
    [
        (
            {"historical_route_allocation": {"sec_company_tickers": 1}},
            {},
            "allocates the historical attempt",
        ),
        (
            {"request_plan_sha256": "b" * 64},
            {"request_plan_sha256": "b" * 64},
            "other than the frozen Decision 055 plan",
        ),
        (
            {"approved_request_ceiling": 802},
            {"approved_request_ceiling": 802},
            "names ceiling 802",
        ),
        ({"authorizing_decision_reference": "Decision 042"}, {}, "as its authorizing decision"),
    ],
    ids=["another-registered-route", "not-the-frozen-plan", "not-801", "not-decision-055"],
)
def test_a_checkpoint_that_is_not_the_accepted_carry_in_is_undetermined(
    tmp_path: Path,
    checkpoint_override: dict[str, object],
    root_override: dict[str, object],
    fragment: str,
) -> None:
    """A forged root agreeing with a forged checkpoint is still not the accepted carry-in.

    Each root receipt below is written to agree with its checkpoint exactly, so every comparison
    *between the two surfaces* passes. What refuses them is the comparison neither surface can
    influence: the fixed Decision 055 values.
    """
    tree = build_catalog(tmp_path)
    _burn_authority(tree, **checkpoint_override)
    head = write_chain(tmp_path, _carry_in_root(**root_override))

    state = _carry_in_inspect(tmp_path, tree, head)

    assert state.determination == "UNDETERMINED"
    assert not state.resume_authorized
    assert "does not record the accepted Decision 055 carry-in" in state.basis
    assert fragment in state.basis


# --------------------------------------------------------------------------- #
# Decision 062 §3 — condition 8.2 over a terminal, non-interrupted failure
# --------------------------------------------------------------------------- #
_TERMINAL_RUN_ID = "m3-2-acquisition-000000000000000000000000000000ff"


def _terminal_receipt(**overrides: object) -> ExecutionReceipt:
    """A correctly-written terminal *failed* receipt: no interruption state, and none owed.

    This is the shape the T6 clean carry-in invocation produced. The receipt schema requires
    `interruption_state` only for `interrupted`, so a `failed` receipt carrying one would be
    invalid — which is exactly why condition 8.2 could not previously be met by any clean
    terminal failure, and why Decision 062 generalized the predicate instead of inventing a state.
    """
    fields: dict[str, object] = {
        "completion_status": "failed",
        "reason_code": "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        "reason_detail": "the window ended incomplete with one planned request unsatisfied.",
        "interruption_state": None,
    }
    fields.update(overrides)
    return receipt(**fields)


def _register_terminal_run(
    tree: DataTree,
    *,
    job_state: str = "failed",
    stage: str = "M3.2A",
    started_at_utc: str = "2026-08-01T12:00:00Z",
    finished_at_utc: str = "2026-08-01T12:00:09Z",
    attempts: int = 1,
    job_id: str = _TERMINAL_RUN_ID,
) -> None:
    """Register the run row and pre-send ledger a terminal receipt must agree with."""
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.insert(
            "ops_ingestion_jobs",
            {
                "job_id": job_id,
                "job_kind": "m3_2_acquisition",
                "job_state": job_state,
                "stage": stage,
                "started_at_utc": started_at_utc,
                "finished_at_utc": finished_at_utc,
                "detail": "incomplete",
            },
        )
        for ordinal in range(attempts):
            writer.insert(
                "ops_retrieval_attempts",
                {
                    "retrieval_attempt_id": f"{job_id}-attempt-{ordinal}",
                    "job_id": job_id,
                    "source_url_canonical": URL,
                    "logical_role": "ticker_alias",
                    "attempt_number": ordinal + 1,
                    "attempt_state": "succeeded",
                    "started_at_utc": started_at_utc,
                    "finished_at_utc": finished_at_utc,
                },
            )


def _condition(state: RecoveryState, number: str) -> ConditionResult:
    """The one condition row with this number."""
    (found,) = [item for item in state.conditions if item.number == number]
    return found


def test_a_terminal_failed_receipt_establishes_its_end_state(tmp_path: Path) -> None:
    """The Decision 062 §3 positive case: every one of the ten conditions holds."""
    tree = build_catalog(tmp_path)
    _register_terminal_run(tree)
    head = write_chain(tmp_path, _terminal_receipt())

    state = inspect(tmp_path, tree, head)

    condition = _condition(state, "8.2")
    assert condition.status == "MET"
    assert condition.condition == "The terminal or interruption state is established, not guessed"
    assert "terminal state established" in condition.detail
    assert "'failed'" in condition.detail
    assert state.interruption_state is None
    assert state.determination == "SAFE"


@pytest.mark.parametrize("status", ["stopped_at_ceiling", "stopped_by_gate"])
def test_the_other_terminal_non_success_statuses_also_establish(
    tmp_path: Path, status: str
) -> None:
    """Gate-stopped and ceiling-stopped are terminal and non-successful in the same way."""
    tree = build_catalog(tmp_path)
    _register_terminal_run(tree)
    overrides: dict[str, object] = {"completion_status": status}
    if status == "stopped_at_ceiling":
        overrides["remaining_planned_logical_request_count"] = 6
    head = write_chain(tmp_path, _terminal_receipt(**overrides))

    assert _condition(inspect(tmp_path, tree, head), "8.2").status == "MET"


def test_a_genuinely_interrupted_receipt_is_unchanged(tmp_path: Path) -> None:
    """Negative control: the interruption path still settles 8.2, and settles it its own way.

    No run row and no pre-send ledger are registered here. If the interruption path had been
    replaced by the terminal one rather than joined to it, this would fail — so this test is what
    proves the generalization added a path instead of substituting one.
    """
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    state = inspect(tmp_path, tree, head)
    condition = _condition(state, "8.2")

    assert condition.status == "MET"
    assert condition.detail == (
        "interruption state recorded as 'after_catalog_commit' by the receipt schema"
    )
    assert state.interruption_state == "after_catalog_commit"


def test_a_complete_receipt_does_not_establish_a_terminal_failure(tmp_path: Path) -> None:
    """`complete` is terminal but successful, so it is not a state to recover from."""
    tree = build_catalog(tmp_path)
    _register_terminal_run(tree, job_state="completed")
    head = write_chain(
        tmp_path,
        receipt(
            completion_status="complete",
            reason_code=None,
            reason_detail=None,
            interruption_state=None,
        ),
    )

    condition = _condition(inspect(tmp_path, tree, head), "8.2")

    assert condition.status == "NOT MET"
    assert "not one of the terminal non-success statuses" in condition.detail


def test_a_receiptless_first_invocation_still_cannot_establish_anything(tmp_path: Path) -> None:
    """Decision 062 §3 is explicit: the terminal path never reaches a receiptless state.

    The run row and the pre-send ledger a terminal establishment would read are both present here.
    What is absent is the receipt — and that alone must keep 8.2 unmet and the determination
    `UNDETERMINED`, because everything the terminal path establishes, it establishes *from* a
    valid receipt.
    """
    tree = build_catalog(tmp_path)
    _register(tree)
    _register_terminal_run(tree)

    state = _receiptless(tree)
    condition = _condition(state, "8.2")

    assert condition.status == "NOT MET"
    assert "no receipt exists" in condition.detail
    assert "does not extend to a receiptless, crashed, killed, or uncertain state" in (
        condition.detail
    )
    assert state.determination == "UNDETERMINED"
    assert not state.resume_authorized


class TestTerminalEstablishmentMutations:
    """Non-vacuity: break one required fact at a time and watch 8.2 stop being met.

    Each case leaves every other condition satisfiable, so a `NOT MET` here is attributable to the
    mutation rather than to the fixture collapsing.
    """

    def test_no_registered_run_row_refuses(self, tmp_path: Path) -> None:
        tree = build_catalog(tmp_path)
        head = write_chain(tmp_path, _terminal_receipt())

        condition = _condition(inspect(tmp_path, tree, head), "8.2")

        assert condition.status == "NOT MET"
        assert "0 registered acquisition run(s) match" in condition.detail

    def test_two_matching_run_rows_refuse(self, tmp_path: Path) -> None:
        tree = build_catalog(tmp_path)
        _register_terminal_run(tree)
        _register_terminal_run(tree, job_id=f"{_TERMINAL_RUN_ID[:-2]}ee")
        head = write_chain(tmp_path, _terminal_receipt())

        condition = _condition(inspect(tmp_path, tree, head), "8.2")

        assert condition.status == "NOT MET"
        assert "2 registered acquisition run(s) match" in condition.detail

    def test_a_run_row_disagreeing_with_the_receipt_refuses(self, tmp_path: Path) -> None:
        """A `stopped` run beside a `failed` receipt is a disagreement, not a rounding."""
        tree = build_catalog(tmp_path)
        _register_terminal_run(tree, job_state="stopped")
        head = write_chain(tmp_path, _terminal_receipt())

        condition = _condition(inspect(tmp_path, tree, head), "8.2")

        assert condition.status == "NOT MET"
        assert "neither is edited to match the other" in condition.detail

    def test_a_ledger_disagreeing_with_the_receipt_refuses(self, tmp_path: Path) -> None:
        tree = build_catalog(tmp_path)
        _register_terminal_run(tree, attempts=3)
        head = write_chain(tmp_path, _terminal_receipt())

        condition = _condition(inspect(tmp_path, tree, head), "8.2")

        assert condition.status == "NOT MET"
        assert "the durable attempt count does not resolve" in condition.detail

    def test_an_unregistered_reason_code_refuses(self, tmp_path: Path) -> None:
        """Defence in depth, exercised at the predicate.

        A receipt *file* can never carry an unregistered code — the receipt schema refuses one
        before it is ever written, which is asserted below. The predicate checks the registry
        anyway, because it reads whatever the chain walk returns rather than re-validating, so the
        guard is exercised directly on a hand-built accounting.
        """
        with pytest.raises(ReceiptValidationError, match="is not registered"):
            _terminal_receipt(reason_code="MADE_UP_REASON")

        tree = build_catalog(tmp_path)
        _register_terminal_run(tree)
        head = write_chain(tmp_path, _terminal_receipt())
        walk = replace(walk_receipt_chain(head), head_reason_code="MADE_UP_REASON")

        with read_only_catalog(tree.catalog_database) as connection:
            established, detail = establish_terminal_state(
                connection, walk, integrity_passed=True, store=_inspect_store(connection, tree)
            )

        assert not established
        assert "is not registered" in detail

    def test_a_blocked_recovery_state_refuses(self, tmp_path: Path) -> None:
        """An unadjudicated mutation is an uncertain commit, so nothing terminal is established."""
        tree = build_catalog(tmp_path)
        _register_terminal_run(tree)
        with CatalogWriter(tree.catalog_database, tree.locks) as writer:
            writer.insert(
                "census_recovery_states",
                {
                    "census_run_id": _TERMINAL_RUN_ID,
                    "recovery_state_id": "f" * 32,
                    "scenario": "t2_4_recovery_action",
                    "resolution_state": "blocked",
                    "action_taken": "write_ahead_recorded",
                    "detail": "a recovery mutation began and awaits adjudication",
                    "recorded_at_utc": "2026-08-01T12:00:05Z",
                },
            )
        head = write_chain(tmp_path, _terminal_receipt())

        condition = _condition(inspect(tmp_path, tree, head), "8.2")

        assert condition.status == "NOT MET"
        assert "still uncertain" in condition.detail

    def test_an_unpromoted_partial_beside_a_terminal_receipt_refuses(self, tmp_path: Path) -> None:
        """Stricter than 8.6 on purpose: a mid-write beside a *terminal* receipt is unexplained."""
        tree = build_catalog(tmp_path)
        _register_terminal_run(tree)
        spool = tree.data_root / "raw" / "sec" / "bulk" / "sec_bulk_submissions-abc.part"
        spool.parent.mkdir(parents=True, exist_ok=True)
        spool.write_bytes(b"partial")
        head = write_chain(tmp_path, _terminal_receipt())

        state = inspect(tmp_path, tree, head)
        condition = _condition(state, "8.2")

        assert condition.status == "NOT MET"
        assert "unpromoted partial file(s) remain beside a terminal receipt" in condition.detail
        assert _condition(state, "8.6").status == "MET", (
            "8.6 still treats an unpromoted partial as ordinary; only 8.2 is stricter"
        )
