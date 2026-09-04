"""D151-C31R2-R19A-C2 §31, §35: the failure-point table, stage by stage, in and across processes.

Every point of the accepted R18 crash/restart table is exercised on committed synthetic worlds:
before BEGIN, after the writes and before COMMIT, after COMMIT and before the checkpoint, after
the checkpoint and before the receipt, during receipt publication, and at the terminal record --
each classified from committed evidence, each converged without re-executing a committed stage,
and each refused loudly where the evidence conflicts. A stage boundary survives a fresh process
at every one of the first six stages and the run still equals the accepted legacy world.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import working_catalog as wc  # noqa: E402
from disclosure_drift.m3.chunk_evidence import FINAL_WORLD_RECEIPT_FILENAME  # noqa: E402


def _raise_once(monkeypatch: pytest.MonkeyPatch, name: str, *, when: Any = None) -> dict[str, int]:
    """Replace ``cm.<name>`` with a wrapper that raises on the first matching call."""
    original = getattr(cm, name)
    calls = {"n": 0}

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if when is None or when(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                message = f"injected failure in {name}"
                raise RuntimeError(message)
        return original(*args, **kwargs)

    monkeypatch.setattr(cm, name, wrapped)
    return calls


def _unit_identities(estate: r19.SuccessorWorld) -> dict[str, str]:
    return {
        str(row["stage_id"]): str(row["unit_identity"]) for row in r19.applied_units(estate.catalog)
    }


def test_b01_a_failure_before_begin_leaves_nothing_durable_and_the_stage_reruns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    before = _unit_identities(estate)
    _raise_once(monkeypatch, "_attach_for_stage", when=lambda c, ctx, stage: stage.stage_id == "S3")
    with pytest.raises(RuntimeError, match="_attach_for_stage"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    assert _unit_identities(estate) == before
    assert wc.normalized_wal_bytes(estate.catalog) == 0
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    assert outcome.completed_stage_ids[-1] == "S3"


def test_b02_a_failure_after_commit_before_the_checkpoint_converges_without_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S4"))
    _raise_once(monkeypatch, "checkpoint_main_truncate")
    with pytest.raises(RuntimeError, match="checkpoint_main_truncate"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S5"))
    # Committed, unfolded, unreceipted: the log holds S5, the row exists, no receipt exists.
    assert r19.stage_ids(estate.catalog)[-1] == "S5"
    assert not any("S5" in p.name for p in r19.receipt_files(estate.receipt_root))
    identities = _unit_identities(estate)
    monkeypatch.setattr(cm, "_stage_table_load", r19.pytest.fail)  # type: ignore[attr-defined]
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S5"))
    assert outcome.completed_stage_ids[-1] == "S5"
    assert _unit_identities(estate) == identities
    assert wc.normalized_wal_bytes(estate.catalog) == 0
    receipt = cm.read_stage_receipt(r19.receipt_files(estate.receipt_root)[-1])
    assert receipt["stage_id"] == "S5" and receipt["unit_identity"] == identities["S5"]


def test_b03_a_failure_after_the_checkpoint_before_the_receipt_converges_without_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S6"))
    _raise_once(monkeypatch, "_publish_stage_receipt")
    with pytest.raises(RuntimeError, match="_publish_stage_receipt"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S7"))
    assert r19.stage_ids(estate.catalog)[-1] == "S7"
    identities = _unit_identities(estate)
    count = r19.count(estate.catalog, "census_registrant_observations")
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S7"))
    assert outcome.completed_stage_ids[-1] == "S7"
    assert _unit_identities(estate) == identities
    assert r19.count(estate.catalog, "census_registrant_observations") == count


def test_b04_a_partial_receipt_is_a_loud_conflict_and_nothing_moves(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    receipt = r19.receipt_files(estate.receipt_root)[-1]
    payload = receipt.read_bytes()
    receipt.write_bytes(payload[: len(payload) // 2])  # a TEST-OWNED artifact, half-written
    identities = _unit_identities(estate)
    with pytest.raises(
        cm.ChunkMultipassError, match="not decodable|not persisted as its canonical"
    ):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S4"))
    assert _unit_identities(estate) == identities
    assert receipt.read_bytes() == payload[: len(payload) // 2]


def test_b05_every_early_stage_boundary_survives_a_fresh_process(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path)
    for stage_id in ("S0", "S1", "S2", "S3", "S4", "S5"):
        result = r19.spawn_production(
            tmp_path, r19.production_request(estate, stop_after=stage_id), label=stage_id
        )
        assert result["returncode"] == 0, result["stderr"][-2000:]
        assert result["result"]["stages"][-1] == stage_id
        assert r19.stage_ids(estate.catalog)[-1] == stage_id
        assert wc.normalized_wal_bytes(estate.catalog) == 0
    final = r19.spawn_production(tmp_path, r19.production_request(estate), label="final")
    assert final["returncode"] == 0 and final["result"]["terminal"]
    assert estate.legacy is not None
    r19.eq.assert_equivalent(
        r19.eq.measure(estate.legacy["world_directory"]), r19.eq.measure(estate.world)
    )


def test_b06_an_unknown_stop_stage_refuses_before_any_world_exists(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    with pytest.raises(cm.ChunkMultipassError, match="names no stage of this route"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S99"))
    assert not estate.world.exists() and not estate.receipt_root.exists()


def test_b07_result_ready_without_a_receipt_publishes_the_receipt_without_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path)
    _raise_once(monkeypatch, "write_once_json")
    with pytest.raises(RuntimeError, match="write_once_json"):
        cm.run_successor_multipass_final(r19.production_request(estate))
    assert r19.stage_ids(estate.catalog)[-1] == "S23P"
    assert not (estate.world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    identities = _unit_identities(estate)
    monkeypatch.setattr(cm, "_run_stage", r19.pytest.fail)  # type: ignore[attr-defined]
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached and outcome.final_receipt is not None
    assert _unit_identities(estate) == identities
    assert estate.legacy is not None
    assert r19.counters(estate.legacy["final"].as_record()) == r19.counters(outcome.final_receipt)


def test_b08_a_result_without_result_ready_is_a_conflict(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate))
    connection = r19.writer(estate.catalog)
    try:
        connection.execute(
            f"DELETE FROM main.{cm.L2_APPLIED_UNITS_TABLE} WHERE stage_id = 'S23P'"  # noqa: S608
        )
    finally:
        connection.close()
    with pytest.raises(cm.ChunkMultipassError, match="exists with no RESULT_READY unit"):
        cm.run_successor_multipass_final(r19.production_request(estate))
