"""D151-C22: the verified storage lifecycle over real chunk artifacts -- R3, R4, R6, R8.

Real chunked-F0 artifacts on disposable internal fixtures, the accepted placement and lifecycle
readers on top of a C22 receipt, the family-facing entry points refusing on their closed
constants before the tier is consulted, an isolated test authority over the fixture only, and
the multipass orchestrator's stat-only telemetry seam. The physical SSD is never touched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "unit"))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c13_intermediates as c13i  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_c22_host_a_ssd_qualification as c22q  # noqa: E402

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import chunk_transfer as x  # noqa: E402
from disclosure_drift.m3 import host_a_ssd_qualification as q  # noqa: E402
from disclosure_drift.m3.chunk_evidence import TRANSFER_RECEIPT_FILENAME  # noqa: E402


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    c13.open_synthetic_multipass(patcher, temp_root=tmp_path / "sqlite-temp")
    patcher.setattr(cm, "_CHILD_BOOTSTRAP", c13i.multipass_child_bootstrap(tmp_path / "repo"))
    yield
    patcher.undo()
    c1.unpin_repository()


def test_the_lifecycle_over_a_real_completed_chunk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2)
    run = c1x.run_chunked_f0(tmp_path, database, tree, chunk_members=2)
    plan, chunk_root = run["plan"], run["chunk_root"]
    record = c22q.qualification()
    dest = tmp_path / "external"
    dest.mkdir()
    provider = c22q.provider_for(record)
    entry = {
        "chunk_root": chunk_root,
        "chunk_id": "chunk-0000",
        "destination_root": dest,
        "qualification": record,
        "provider": provider,
    }
    # R8: the closed constant refuses first; nothing is copied and the tier is not consulted.
    assert cs.REAL_CHUNK_TRANSFER_AUTHORITY is None
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.transfer_completed_chunk(external_reserve_bytes=0, **entry)
    assert list(dest.iterdir()) == []
    # An isolated authority over this disposable fixture only.
    monkeypatch.setattr(cs, "REAL_CHUNK_TRANSFER_AUTHORITY", "c22-isolated-transfer")
    receipt = cs.transfer_completed_chunk(external_reserve_bytes=0, **entry)
    assert receipt.qualification_identity == record.qualification_identity
    # The accepted readers see one verified external copy whose identities agree.
    placement = cs.derive_chunk_placement(
        plan, "chunk-0000", internal_root=chunk_root, external_root=dest
    )
    assert placement.state == cs.STATE_INTERNAL_RECLAIM_ELIGIBLE and placement.has_verified_external
    assert placement.transfer_receipt is not None
    assert (
        placement.transfer_receipt.chunk_receipt_manifest_digest == receipt.source_manifest_digest
    )
    assert placement.transfer_receipt.contract == cs.VERIFIED_TRANSFER_RECEIPT_CONTRACT
    assert (
        json.loads((dest / "chunk-0000" / TRANSFER_RECEIPT_FILENAME).read_bytes())["contract"]
        == "m3.3-chunked-f0-transfer-receipt/2"
    )
    assert placement.internal_receipt is not None
    assert placement.internal_receipt.manifest.digest == receipt.source_manifest_digest
    assert (
        ct.derive_artifact_lifecycle(placement, external_root=dest)
        == ct.LIFECYCLE_EXTERNAL_COPY_VERIFIED
    )
    # The accepted eligibility predicate is complete on a C22 receipt, and still not a reclaim.
    accepted = ct.reclaim_eligibility(
        placement, transfer_record=receipt.bindings(), external_root=dest
    )
    assert accepted.eligible and accepted.reclaim_authority is None
    with_tier = ct.reclaim_eligibility_with_tier(
        placement, transfer_record=receipt.bindings(), external_root=dest, qualification=record
    )
    assert with_tier.eligible and with_tier.proofs["qualification_reclaim_capable"] is True
    with pytest.raises(ct.ChunkTieringError, match="NOT AUTHORIZED"):
        ct.require_internal_reclaim(with_tier)
    copy_only = ct.reclaim_eligibility_with_tier(
        placement,
        transfer_record=receipt.bindings(),
        external_root=dest,
        qualification=c22q.qualification(klass=q.CLASS_COPY_ONLY),
    )
    assert not copy_only.eligible and copy_only.proofs["qualification_reclaim_capable"] is False
    # The transfer is idempotent on agreeing identities, and no duplicate receipt is written.
    receipt_path = dest / "chunk-0000" / TRANSFER_RECEIPT_FILENAME
    before = receipt_path.read_bytes()
    assert cs.transfer_completed_chunk(external_reserve_bytes=0, **entry) == receipt
    assert receipt_path.read_bytes() == before
    with pytest.raises(x.ChunkTransferError, match="disagrees"):
        cs.transfer_completed_chunk(
            external_reserve_bytes=0,
            **{**entry, "qualification": c22q.qualification(klass=q.CLASS_COPY_ONLY)},
        )
    # R4: a verified transfer never implies a reclaim; the closed constant refuses first.
    assert cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    internal_before = sorted(str(p.relative_to(chunk_root)) for p in chunk_root.rglob("*"))
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.reclaim_transferred_chunk(**entry)
    assert sorted(str(p.relative_to(chunk_root)) for p in chunk_root.rglob("*")) == internal_before
    assert (
        x.derive_transfer_state(
            destination_root=dest, chunk_id="chunk-0000", source_directory=None
        ).state
        == x.STATE_TRANSFER_VERIFIED_RECEIPT_DURABLE
    )
    monkeypatch.setattr(cs, "REAL_INTERNAL_RECLAIM_AUTHORITY", "c22-isolated-reclaim")
    completion = cs.reclaim_transferred_chunk(**entry)
    assert completion.record_kind == x.RECLAIM_COMPLETE
    assert completion.deleted_entries == len(receipt.destination_entries) + 1
    after = cs.derive_chunk_placement(
        plan, "chunk-0000", internal_root=chunk_root, external_root=dest
    )
    assert after.state == cs.STATE_INTERNAL_RECLAIMED and after.internal_directory is None
    assert cs.authoritative_input(after) == (dest / "chunk-0000", cs.TIER_EXTERNAL)
    assert (
        x.derive_transfer_state(
            destination_root=dest, chunk_id="chunk-0000", source_directory=None
        ).state
        == x.STATE_RECLAIM_COMPLETE
    )
    # Every other chunk is exactly where it was.
    for bounds in plan.chunks[1:]:
        other = cs.derive_chunk_placement(
            plan, bounds.chunk_id, internal_root=chunk_root, external_root=dest
        )
        assert other.state == cs.STATE_COMPLETE_INTERNAL
    # A reclaimed chunk is no longer a source: nothing further can be deleted through it.
    with pytest.raises(cs.ChunkStorageError, match="no valid terminal receipt"):
        cs.reclaim_transferred_chunk(**entry)
    # C22E-R1: a legacy /1 copy made by the accepted single-pass writer is read by the accepted
    # readers, is never eligible under the tier-aware predicate, and is refused -- not upgraded --
    # by every C22 route; its receipt bytes are untouched afterwards.
    legacy_source = cs.completed_chunk_receipt(chunk_root, "chunk-0001")
    assert legacy_source is not None
    legacy = cs.transfer_chunk(
        source_directory=legacy_source[1],
        destination_directory=dest / "chunk-0001",
        destination_volume_uuid=c22q.VOLUME,
    )
    assert legacy.contract == cs.LEGACY_TRANSFER_RECEIPT_CONTRACT
    legacy_path = dest / "chunk-0001" / TRANSFER_RECEIPT_FILENAME
    legacy_bytes = legacy_path.read_bytes()
    legacy_placement = cs.derive_chunk_placement(
        plan, "chunk-0001", internal_root=chunk_root, external_root=dest
    )
    assert legacy_placement.state == cs.STATE_INTERNAL_RECLAIM_ELIGIBLE
    assert legacy_placement.transfer_receipt is not None
    assert legacy_placement.transfer_receipt.contract == cs.LEGACY_TRANSFER_RECEIPT_CONTRACT
    legacy_eligibility = ct.reclaim_eligibility_with_tier(
        legacy_placement,
        transfer_record=ct.transfer_receipt_bindings_of(legacy_placement.transfer_receipt),
        external_root=dest,
        qualification=record,
    )
    assert not legacy_eligibility.eligible
    assert legacy_eligibility.proofs["transfer_receipt_is_verified_v2"] is False
    with pytest.raises(x.ChunkTransferError, match="legacy"):
        cs.transfer_completed_chunk(external_reserve_bytes=0, **{**entry, "chunk_id": "chunk-0001"})
    with pytest.raises(x.ChunkTransferError, match="legacy"):
        cs.reclaim_transferred_chunk(**{**entry, "chunk_id": "chunk-0001"})
    assert legacy_path.read_bytes() == legacy_bytes
    assert cs.completed_chunk_receipt(chunk_root, "chunk-0001") is not None


def test_the_orchestrator_reports_stat_only_telemetry_for_every_merge(tmp_path: Path) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    root = run["base"] / "instrumented"
    temp_root = tmp_path / "sqlite-temp"
    temp_root.mkdir(exist_ok=True)
    ledger = x.InstrumentationLedger(
        tmp_path / "telemetry.jsonl",
        internal_path=run["chunk_root"],
        temp_root=temp_root,
        charged_directory=root,
        qualification_identity=None,
        tier_identity=None,
    )
    result = cm.run_multipass_f0(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        multipass_root=root,
        run_id="instrumented",
        telemetry=ledger,
    )
    steps = [group.group_id for group in result.schedule.groups] + ["final"]
    assert ledger.require_complete() == 2 * len(steps)
    lines = [
        json.loads(line)
        for line in (tmp_path / "telemetry.jsonl").read_bytes().decode("utf-8").splitlines()
    ]
    assert [line["phase"] for line in lines] == [
        phase for step in steps for phase in (f"merge_started:{step}", f"merge_child_exit:{step}")
    ]
    for line in lines:
        assert set(line) == set(x.SAMPLE_FIELDS)
        assert isinstance(line["wal_high_water_bytes"], int) and line["wal_high_water_bytes"] >= 0
        assert isinstance(line["sqlite_temp_high_water_bytes"], int)
        assert line["internal_low_water_bytes"] <= line["internal_free_bytes"]
    exits = [line for line in lines if line["phase"].startswith("merge_child_exit:")]
    assert all(line["process_exit_rss_reclaimed_bytes"] is not None for line in exits)
    assert result.receipt["chunks_unchanged"] is True
    # Nothing about the accepted run changed: every intermediate and the final world verify.
    assert len(result.intermediates) == len(result.schedule.groups)
