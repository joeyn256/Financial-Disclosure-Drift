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

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from disclosure_drift.m3 import recovery as recovery_module
from disclosure_drift.m3.receipt import ExecutionReceipt, write_receipt
from disclosure_drift.m3.recovery import (
    RECOVERY_DETERMINATIONS,
    RecoveryInspectionError,
    RecoveryState,
    inspect_recovery_state,
)
from disclosure_drift.m3.request_plan import RequestPlan, build_m3_2a_request_plan
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.http_client import FetchResult
from disclosure_drift.sec.observation_catalog import ObservationRecorder
from disclosure_drift.sec.raw_store import RawStore
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.storage.catalog import CatalogWriter

URL = "https://www.sec.gov/files/company_tickers.json"


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def observation(tree: DataTree) -> SourceObservation:
    """One stored, verifiable source observation."""
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
        )
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
        "request_plan_sha256": "b" * 64,
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
# Determination surface
# --------------------------------------------------------------------------- #
def test_a_clean_state_records_every_condition(tmp_path: Path) -> None:
    tree = build_catalog(tmp_path)
    head = write_chain(tmp_path, receipt())

    state = inspect(tmp_path, tree, head)

    numbers = [condition.number for condition in state.conditions]
    assert numbers == [f"8.{index}" for index in range(1, 12)]


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
