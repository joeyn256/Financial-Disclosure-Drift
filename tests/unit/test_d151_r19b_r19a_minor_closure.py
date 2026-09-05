"""D151-C31R2-R19B-C2 §13-§16: the six R19A-R1 MINOR closures, proved on committed worlds.

* MINOR-1: a complete, authenticated initialization attempt beside a canonical world is a
  STAGE_CONFLICT; incomplete residue -- a directory with no catalog, a nonzero write-ahead log,
  a foreign StagePlan -- is preserved, classified through ``lstat`` and ``immutable=1`` only (no
  inventory, inode, length, digest or mtime moves and no sidecar is created), never promoted or
  checkpointed, and reported with its allocated bytes; a link or a malformed name beside the
  world refuses;
* MINOR-2: the runtime tool manifest binds ``canary_runtime`` and ``errors`` under its own
  dedicated contract, and every entry is the hashed source file;
* MINOR-3: the committed manifest test carries no vacuous assertion and calls the hashing helper;
* MINOR-4: ``STAGE_EXECUTE``, ``STAGE_COMMITTED_RECEIPT_PENDING`` and ``STAGE_COMPLETE`` are
  emitted by the production classification and reach the stage receipt, and the normalized WAL
  class is consumed by the production residue disposition;
* MINOR-5/6 are evidence-ledger closures published beside the R19A ledger, never inside it: the
  create-once writer such a record uses refuses a second write, which is what append-only means.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3.chunk_evidence import ChunkEvidenceError, file_sha256  # noqa: E402
from disclosure_drift.m3.chunk_execution import (  # noqa: E402
    ChunkExecutionError,
    write_once_canonical_json,
)
from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME  # noqa: E402


def _facts(root: Path) -> dict[str, tuple[Any, ...]]:
    """Every entry beneath ``root`` by lstat: class, inode, length, mtime_ns and digest."""
    facts: dict[str, tuple[Any, ...]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(dirnames):
            status = os.lstat(Path(dirpath) / name)
            facts[str(Path(dirpath, name).relative_to(root))] = ("dir", status.st_ino)
        for name in sorted(filenames):
            path = Path(dirpath) / name
            status = os.lstat(path)
            facts[str(path.relative_to(root))] = (
                "file",
                status.st_ino,
                status.st_size,
                status.st_mtime_ns,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
    return facts


def _mint() -> cm._SuccessorRouteProof:
    return cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_PRODUCTION, gate=lambda: None, gate_name="t"
    )


# ==========================================================================
# MINOR-1: sibling initialization attempts beside a canonical world
# ==========================================================================
def test_a01_a_complete_attempt_beside_the_canonical_world_is_a_conflict(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    orphan = estate.world.parent / f"{estate.world.name}.init-attempt-001"
    shutil.copytree(estate.world, orphan)
    before = (_facts(orphan), _facts(estate.world))
    with pytest.raises(
        cm.ChunkMultipassError, match="complete, authenticated initialization attempt"
    ):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S1"))
    # Nothing moved: the orphan is neither promoted, deleted nor opened through a folding
    # handle, the canonical world is untouched, and S1 never ran.
    assert (_facts(orphan), _facts(estate.world)) == before
    assert r19.stage_ids(estate.catalog) == ["S0"]
    assert not list(estate.receipt_root.glob("stage-001-*"))


def test_a02_incomplete_residue_is_preserved_classified_side_effect_free_and_reported(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    parent, name = estate.world.parent, estate.world.name
    stale = parent / f"{name}.init-attempt-003"
    stale.mkdir()
    (stale / "partial.txt").write_bytes(b"interrupted before any catalog existed")
    interrupted = parent / f"{name}.init-attempt-004"
    shutil.copytree(estate.world, interrupted)
    wal = interrupted / f"{WORKING_CATALOG_FILENAME}-wal"
    wal.write_bytes(bytes(32) + bytes(4120 * 3))  # a nonzero log: interrupted residue
    foreign = parent / f"{name}.init-attempt-005"
    shutil.copytree(estate.world, foreign)
    connection = r19.writer(foreign / WORKING_CATALOG_FILENAME)
    try:
        connection.execute(
            f"UPDATE main.{cm.L2_STAGE_PLAN_TABLE} SET stage_plan_identity = "  # noqa: S608
            "(CASE WHEN substr(stage_plan_identity, 1, 1) = '0' THEN '1' ELSE '0' END) "
            "|| substr(stage_plan_identity, 2)"
        )
    finally:
        connection.close()
    for sidecar in ("-wal", "-shm"):
        assert not os.path.lexists(foreign / f"{WORKING_CATALOG_FILENAME}{sidecar}")
    before = {p.name: _facts(p) for p in (stale, interrupted, foreign)}
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S1"))
    assert outcome.completed_stage_ids == ("S0", "S1")
    # Classification created nothing and moved nothing: no ``-wal``/``-shm`` beside the foreign
    # copy's catalog (an ``immutable=1`` read creates neither; ``mode=ro`` would), identical
    # inodes, lengths, digests and mtimes everywhere, the nonzero log never checkpointed.
    assert {p.name: _facts(p) for p in (stale, interrupted, foreign)} == before
    residue = {str(item["name"]): item for item in outcome.retained_attempt_residue}
    assert set(residue) == {stale.name, interrupted.name, foreign.name}
    assert residue[stale.name]["classification"] == "INCOMPLETE"
    assert residue[interrupted.name]["classification"] == "INCOMPLETE_NONZERO_WAL"
    assert residue[foreign.name]["classification"] == "INCOMPLETE"
    assert "another StagePlan identity" in str(residue[foreign.name]["reason"])
    for item in residue.values():
        assert int(item["allocated_bytes"]) >= int(item["logical_bytes"]) > 0  # type: ignore[call-overload]
        assert item["ordinal"] in {3, 4, 5}
    assert sorted(p.name for p in estate.world.iterdir()) == [
        "run_progress.sqlite3",
        WORKING_CATALOG_FILENAME,
    ]
    # A link or a malformed name beside the world is a conflict, and S2 never runs.
    link = parent / f"{name}.init-attempt-006"
    link.symlink_to(stale)
    with pytest.raises(cm.ChunkMultipassError, match="symbolic link"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    link.unlink()
    malformed = parent / f"{name}.init-attempt-7"
    malformed.mkdir()
    with pytest.raises(cm.ChunkMultipassError, match="malformed ordinal"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    malformed.rmdir()
    assert r19.stage_ids(estate.catalog) == ["S0", "S1"]
    # The classifier reads residue through immutable=1 only; no mode=ro classifier remains.
    source = inspect.getsource(cm._authenticate_attempt_immutable)
    assert "immutable=1" in source and "?mode=ro" not in source and "read_only" not in source
    assert not hasattr(cm, "_attempt_is_complete")
    residue_source = inspect.getsource(cm._classify_one_attempt)
    assert "read_only" not in residue_source and "mode=ro" not in residue_source


def test_a02b_an_absent_world_promotes_exactly_one_complete_attempt_and_keeps_residue(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    parent, name = estate.world.parent, estate.world.name
    complete = parent / f"{name}.init-attempt-002"
    shutil.move(str(estate.world), str(complete))
    interrupted = parent / f"{name}.init-attempt-001"
    shutil.copytree(complete, interrupted)
    (interrupted / f"{WORKING_CATALOG_FILENAME}-wal").write_bytes(bytes(32) + bytes(4120))
    before = _facts(interrupted)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    assert outcome.completed_stage_ids == ("S0",)
    assert estate.world.is_dir() and not complete.exists()
    assert _facts(interrupted) == before
    assert [item["classification"] for item in outcome.retained_attempt_residue] == [
        "INCOMPLETE_NONZERO_WAL"
    ]
    # Two complete attempts beside an absent world: a conflict, neither promoted.
    shutil.copytree(estate.world, parent / f"{name}.init-attempt-007")
    shutil.copytree(estate.world, parent / f"{name}.init-attempt-008")
    shutil.rmtree(estate.world)
    with pytest.raises(cm.ChunkMultipassError, match="2 complete initialization attempts"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    assert not estate.world.exists()


# ==========================================================================
# MINOR-2: the tool manifest
# ==========================================================================
def test_a03_the_tool_manifest_binds_canary_runtime_and_errors_under_its_own_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = cm._runtime_tool_manifest()
    modules = [str(entry["module"]) for entry in manifest.entries]
    assert "disclosure_drift.m3.canary_runtime" in modules
    assert "disclosure_drift.errors" in modules
    assert {
        "disclosure_drift.m3.chunk_multipass",
        "disclosure_drift.m3.working_catalog",
        "disclosure_drift.m3.chunk_consolidation",
        "disclosure_drift.m3.compact_evidence",
        "disclosure_drift.sec.census",
        "disclosure_drift.m3.chunk_execution",
    } <= set(modules)
    # D151-C31R2-R20-C1 (R20-MAJOR-2): the declared set is stated as the dependency set it must
    # cover, not as a number. R20 falsified R19B's completeness claim by tracing five further
    # first-party modules executing inside one successor invocation; the count moved with them
    # and would move again, so what is asserted here is coverage and uniqueness.
    assert len(modules) == len(set(modules))
    assert {
        "disclosure_drift.m3.capacity_plan",
        "disclosure_drift.m3.external_working_root",
        "disclosure_drift.sec.identifiers",
        "disclosure_drift.sec.observation_catalog",
        "disclosure_drift.sec.snapshots",
    } <= set(modules)
    assert cm.L2_TOOL_MANIFEST_CONTRACT == "m3.3-chunked-f0-l2-tool-manifest/1"
    assert manifest.as_record()["contract"] == cm.L2_TOOL_MANIFEST_CONTRACT
    assert cm.L2_TOOL_MANIFEST_CONTRACT not in {
        cm.L2_STAGE_PLAN_CONTRACT,
        cm.L2_STAGE_PLAN_CONTRACT_V2,
    }
    package_root = Path(str(cm.__file__)).parent.parent
    for entry in manifest.entries:
        relative = str(entry["module"]).removeprefix("disclosure_drift.").replace(".", "/")
        assert (entry["sha256"], entry["byte_length"]) == file_sha256(
            package_root / f"{relative}.py"
        ), entry["module"]
    # The identity is over the dedicated contract: the StagePlan contract does not describe it.
    body = {
        "contract": cm.L2_STAGE_PLAN_CONTRACT_V2,
        "entries": [dict(e) for e in manifest.entries],
    }
    assert cm._identity_of(body) != manifest.identity
    # A changed errors.py byte moves the identity: the module is genuinely bound.
    changed = tmp_path / "errors_changed.py"
    original = next(
        file for name, file in cm._TOOL_MANIFEST_MODULES if name == "disclosure_drift.errors"
    )
    changed.write_bytes(Path(str(original)).read_bytes() + b"\n# changed\n")
    monkeypatch.setattr(
        cm,
        "_TOOL_MANIFEST_MODULES",
        tuple(
            (name, str(changed) if name == "disclosure_drift.errors" else file)
            for name, file in cm._TOOL_MANIFEST_MODULES
        ),
    )
    assert cm._runtime_tool_manifest().identity != manifest.identity


# ==========================================================================
# MINOR-3: no vacuous assertion in the committed manifest test
# ==========================================================================
def test_a04_the_committed_manifest_test_carries_no_vacuous_assertion() -> None:
    path = Path(__file__).parent / "test_d151_r19_stage_manifest_binding.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.IfExp):
            assert not isinstance(node.test, ast.Constant), "constant-test conditional expression"
        if isinstance(node, ast.Assert):
            assert not isinstance(node.test, ast.Constant), "constant assertion"
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    m01 = next(node for name, node in functions.items() if name.startswith("test_m01"))
    called = {
        node.func.id
        for node in ast.walk(m01)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "file_sha256" in called
    source = ast.get_source_segment(path.read_text(encoding="utf-8"), m01) or ""
    assert 'entry["sha256"] == sha256' in source and 'entry["byte_length"] == length' in source


# ==========================================================================
# MINOR-4: the three classifications are emitted and observable
# ==========================================================================
def test_a05_the_three_classifications_are_emitted_and_reach_the_receipt(tmp_path: Path) -> None:
    assert (cm._STAGE_EXECUTE, cm._STAGE_COMMITTED_RECEIPT_PENDING, cm._STAGE_COMPLETE) == (
        "STAGE_EXECUTE",
        "STAGE_COMMITTED_RECEIPT_PENDING",
        "STAGE_COMPLETE",
    )
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    proof = _mint()
    ctx = cm._resolve_successor_context(r19.production_request(estate), proof)

    def classify() -> cm._Progress:
        with cm._successor_world_session(
            request=ctx.request, expected=ctx.stage_plan, proof=proof
        ) as session:
            return cm._classify(session, ctx)

    execute = classify()
    assert execute.classification == cm._STAGE_EXECUTE
    assert execute.next_stage is not None and execute.next_stage.stage_id == "S3"
    receipt = r19.receipt_files(estate.receipt_root)[-1]
    assert "S2" in receipt.name
    receipt.unlink()  # a TEST-OWNED artifact standing in for a crash before the receipt
    pending = classify()
    assert pending.classification == cm._STAGE_COMMITTED_RECEIPT_PENDING
    assert pending.pending is not None and pending.pending.stage_id == "S2"
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    converged = cm.read_stage_receipt(receipt)
    assert converged["contract"] == cm.L2_STAGE_RECEIPT_CONTRACT_V2
    assert converged["entry_classification"] == cm._STAGE_COMMITTED_RECEIPT_PENDING
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    executed = cm.read_stage_receipt(r19.receipt_files(estate.receipt_root)[-1])
    assert executed["stage_id"] == "S3"
    assert executed["entry_classification"] == cm._STAGE_EXECUTE
    assert executed["wal_residue_disposition"]["class"] == "NONE"
    cm.run_successor_multipass_final(r19.production_request(estate))
    complete = classify()
    assert complete.classification == cm._STAGE_COMPLETE and complete.terminal_complete
    # The normalized WAL class is consumed by the production residue disposition, not a test.
    disposition = inspect.getsource(cm._dispose_wal_residue)
    assert "_normalized_wal_class(" in disposition
    assert "_STAGE_COMMITTED_RECEIPT_PENDING" in inspect.getsource(cm._classify)
    assert "_STAGE_COMPLETE" in inspect.getsource(cm._classify)


# ==========================================================================
# MINOR-5/6: append-only evidence supersession
# ==========================================================================
def test_a06_a_supersession_record_is_create_once_and_never_rewrites_what_it_supersedes(
    tmp_path: Path,
) -> None:
    sealed = tmp_path / "P5_SEMANTIC_STAGE_GRAPH_COMPLETE.json"
    sealed.write_bytes(b'{"graph": "superseded narrative"}\n')
    sealed.chmod(0o444)
    before = (sealed.stat().st_ino, sealed.stat().st_size, sealed.read_bytes())
    record = {
        "contract": "m3.3-d151-r19a-evidence-supersession/1",
        "supersedes": sealed.name,
        "mark": "SUPERSEDED_REPORT_NARRATIVE_ONLY",
    }
    record["supersession_identity"] = cm._identity_of(record)
    path = write_once_canonical_json(tmp_path / "r19a_evidence_supersession.json", record)
    with pytest.raises((ChunkEvidenceError, ChunkExecutionError), match="create-once|exists"):
        write_once_canonical_json(path, {**record, "mark": "changed"})
    assert (sealed.stat().st_ino, sealed.stat().st_size, sealed.read_bytes()) == before
    assert (path.stat().st_mode & 0o7777) in {0o444, 0o600}
