"""D151-C31R2-R19A-C2 §17, §18, §26: contracts, the StagePlan, and the runtime tool manifest.

The StagePlan is a pure function of durable inputs and recomputes its identity from its body;
the implementation files are re-hashed from disk at every admission and compared with the
StagePlan-bound identity rather than copied; every applied unit and receipt binds that identity
beside the receipt, manifest and selected-request identities of every intermediate; a changed
implementation file refuses the next stage; and every StagePlan refusal is a reader refusal.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3.chunk_evidence import file_sha256  # noqa: E402


def test_m01_the_runtime_tool_manifest_is_recomputed_from_disk_and_bound_everywhere(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    manifest = cm._runtime_tool_manifest()
    assert {entry["module"] for entry in manifest.entries} >= {
        "disclosure_drift.m3.chunk_multipass",
        "disclosure_drift.m3.chunk_consolidation",
        "disclosure_drift.m3.working_catalog",
        "disclosure_drift.m3.chunk_tiering",
    }
    # R19A-R1 MINOR-3 closed: every entry's digest and length are recomputed from the source
    # file on disk by the accepted hashing helper and compared with the manifest record.
    package_root = Path(str(cm.__file__)).parent.parent
    for entry in manifest.entries:
        relative = str(entry["module"]).removeprefix("disclosure_drift.").replace(".", "/")
        sha256, length = file_sha256(package_root / f"{relative}.py")
        assert entry["sha256"] == sha256, entry["module"]
        assert entry["byte_length"] == length, entry["module"]
    assert {entry["module"] for entry in manifest.entries} >= {
        "disclosure_drift.m3.canary_runtime",
        "disclosure_drift.errors",
    }
    assert manifest.as_record()["contract"] == cm.L2_TOOL_MANIFEST_CONTRACT
    plan = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
    assert plan.tool_manifest_identity == manifest.identity
    tool_manifest = plan.body["tool_manifest"]
    assert isinstance(tool_manifest, dict)
    assert tool_manifest["tool_manifest_identity"] == manifest.identity
    assert plan.body["source_file_digests"] == dict(manifest.source_file_digests())
    for row in r19.applied_units(estate.catalog):
        unit = cm.AppliedUnit.from_row(row)
        assert unit.tool_manifest_identity == manifest.identity
        assert unit.body["source_file_digests"] == dict(manifest.source_file_digests())
    for path in r19.receipt_files(estate.receipt_root):
        assert cm.read_stage_receipt(path)["tool_manifest_identity"] == manifest.identity


def test_m02_a_changed_implementation_file_refuses_and_a_copied_identity_is_never_trusted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    # A TEST-OWNED copy of one implementation file with one byte appended stands in for a tool
    # that changed between stages: the runtime manifest is re-hashed and refuses.
    changed = tmp_path / "chunk_tiering_changed.py"
    shutil.copyfile(ct.__file__, changed)
    changed.write_bytes(changed.read_bytes() + b"\n# changed\n")
    modules = tuple(
        (name, str(changed) if name == "disclosure_drift.m3.chunk_tiering" else file)
        for name, file in cm._TOOL_MANIFEST_MODULES
    )
    monkeypatch.setattr(cm, "_TOOL_MANIFEST_MODULES", modules)
    with pytest.raises(
        cm.ChunkMultipassError, match="tool-manifest identity|minimal StagePlan identity"
    ):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S4"))
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2", "S3"]
    monkeypatch.undo()
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S4"))
    assert outcome.completed_stage_ids[-1] == "S4"
    # A module not loaded from a .py source refuses rather than binding bytecode.
    monkeypatch.setattr(cm, "_TOOL_MANIFEST_MODULES", (("x", str(changed.with_suffix(".pyc"))),))
    with pytest.raises(cm.ChunkMultipassError, match="not loaded from a .py source"):
        cm._runtime_tool_manifest()


def test_m03_the_stage_plan_reader_recomputes_its_identity_and_refuses_every_broken_shape(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    plan = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
    record = dict(plan.as_record())
    assert cm.L2StagePlan.from_record(record).identity == plan.identity
    with pytest.raises(cm.ChunkMultipassError, match="does not describe its own body"):
        cm.L2StagePlan.from_record({**record, "stage_plan_identity": "0" * 64})
    # Every shape rule is checked on the body itself, so a body without its identity is read.
    record = {key: value for key, value in record.items() if key != "stage_plan_identity"}
    with pytest.raises(cm.ChunkMultipassError, match="carrying contract"):
        cm.L2StagePlan.from_record({**record, "contract": "m3.3-chunked-f0-l2-stage-plan/3"})
    with pytest.raises(cm.ChunkMultipassError, match="names route"):
        cm.L2StagePlan.from_record({**record, "route": "legacy"})
    with pytest.raises(cm.ChunkMultipassError, match="input_group_count"):
        cm.L2StagePlan.from_record({**record, "input_group_count": 9})
    with pytest.raises(cm.ChunkMultipassError, match="input_group_count"):
        cm.L2StagePlan.from_record({**record, "predecessor_completed_group_count": 9})
    with pytest.raises(cm.ChunkMultipassError, match="not contiguous"):
        cm.L2StagePlan.from_record({**record, "stage_graph": record["stage_graph"][1:]})  # type: ignore[index]
    with pytest.raises(cm.ChunkMultipassError, match="cache_bytes"):
        cm.L2StagePlan.from_record({**record, "cache_bytes": True})
    # Every binding §18 names is present in the body.
    for key in (
        "predecessor_run_id",
        "predecessor_checkpoint_count",
        "predecessor_tip_ordinal",
        "predecessor_tip_identity",
        "predecessor_completed_group_count",
        "plan_digest",
        "schedule_digest",
        "repository_head_sha",
        "repository_tree_sha",
        "tool_manifest_identity",
        "source_file_digests",
        "stage_graph",
        "expected_deferred_index_set_identity",
        "expected_deferred_index_count",
        "internal_relation_names",
        "cache_bytes",
        "stage_receipt_root",
        "canonical_world_path",
        "initialization_attempt_parent",
        "storage_requirement_identity",
        "semantic_policy_identities",
        "sqlite_temp_binding_identity",
    ):
        assert key in record, key
    assert record["expected_deferred_index_count"] == 5
    assert record["internal_relation_names"] == list(
        cm.L2_CONTROL_TABLES + cm.L2_PERSISTENT_RELATIONS
    )


def test_m04_every_unit_binds_the_intermediates_receipts_manifests_and_selected_requests(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    root = estate.succ["intermediates_root"]
    expected_manifests = [r.manifest.digest for r in estate.succ["intermediates"]]
    expected_receipts = []
    expected_requests = []
    for group, receipt in zip(estate.schedule.groups, estate.succ["intermediates"], strict=True):
        directory = root / group.group_id / f"attempt-{receipt.attempt:03d}"
        expected_receipts.append(file_sha256(directory / cm.INTERMEDIATE_RECEIPT_FILENAME)[0])
        expected_requests.append(
            file_sha256(
                root / group.group_id / f"{group.group_id}-{receipt.attempt:03d}-request.json"
            )[0]
        )
    for row in r19.applied_units(estate.catalog):
        unit = cm.AppliedUnit.from_row(row)
        assert unit.body["input_identities"] == expected_manifests
        assert unit.body["receipt_identities"] == expected_receipts
        assert unit.body["request_provenance_identities"] == expected_requests
    plan = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
    for descriptor, manifest, receipt, request in zip(
        plan.intermediates, expected_manifests, expected_receipts, expected_requests, strict=True
    ):
        assert descriptor["manifest_digest"] == manifest
        assert descriptor["receipt_document_sha256"] == receipt
        provenance = descriptor["group_request_provenance"]
        assert isinstance(provenance, dict) and provenance["sha256"] == request
        assert provenance["governed_manifest_member"] is False
        assert provenance["successor_semantic_input"] is False
        assert len(descriptor["governed_entries"]) == 6  # type: ignore[arg-type]
