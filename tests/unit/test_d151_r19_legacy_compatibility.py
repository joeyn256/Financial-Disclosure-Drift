"""D151-C31R2-R19A-C2 §13, §33: the legacy route is byte for byte what it was, and stays TEMP.

The accepted finalizer bodies, the set-based staging, the whole-F0 counter derivation, the
production child entry and the calibration group body are pinned by source digest; the
accepted legacy proof ``test_c1717`` is pinned byte-identical and still proves TEMP behaviour on
this tree; legacy worlds carry no successor relation and successor worlds carry no TEMP
leftover; and every legacy reader refuses a successor artifact.
"""

from __future__ import annotations

import hashlib
import inspect
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c17_storage_binding as c17  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    ChunkEvidenceError,
    read_receipt_document,
)
from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME  # noqa: E402

#: SHA-256 of ``inspect.getsource`` of each accepted body at the R19A-C2 baseline (7a1fcf08).
#:
#: Decision 151 (Boundaries 2 and 3) re-pinned exactly two of them: the two level-1 GROUP bodies
#: now admit their inputs' manifest-bound parser-run semantics before the attempt directory
#: exists and write the ``/2`` intermediate receipt's observed-semantics fields. The two
#: finalizers, the set-based staging, the whole-F0 counter derivation and the production child
#: entry are byte-identical to the R19A-C2 baseline still, and the assertion form is unchanged.
PINNED_SOURCE = {
    "finalize_multipass_body": ("ce71509438ab4a3da99fa089887c75c592acd3c072841a438e03d3dbd84ed733"),
    "merge_group_body": ("a0090f772a23bc3a8e96d332b46d384447455cafe5e73c5067b6873f91e77e31"),
    "finalize_calibration_subset_body": (
        "1355dd634aba76ac144bec78d206a4d9736ce043660741d56cebf42582df2969"
    ),
    "merge_calibration_subset_group_body": (
        "a203e2f2dd85243ef9a860ebf2e00d1837f32514c694770418b243630072f1f8"
    ),
    "stage_first_witness_corrections": (
        "81e6463b64d17d6ce7eb0023850f302fcdbd4a4f8b56007bc4766e9cc0f11b3d"
    ),
    "_plan_first_witness_counters": (
        "c96652e661e990280d178194e89186a4dc77ec3dea8811cb5f75397bcbb2c833"
    ),
    "_child_main": ("8b83df5bae8ac813aa72018fc55841b00b51c7487a3845e4afa40281dda4e6d0"),
}
PINNED_C1717 = "5234c1fe73392f6b3e65853c02bf0de6b83ad0dfe20c6d72f32162c2becee25c"


def _digest(function: object) -> str:
    return hashlib.sha256(inspect.getsource(function).encode("utf-8")).hexdigest()  # type: ignore[arg-type]


def test_l01_the_legacy_bodies_and_test_c1717_are_byte_identical_to_the_baseline() -> None:
    for name, digest in PINNED_SOURCE.items():
        assert _digest(getattr(cm, name)) == digest, name
    assert _digest(c17.test_c1717_a_second_derivation_on_one_connection_refuses) == PINNED_C1717
    # The legacy bodies name no successor relation, contract or proof.
    for name in PINNED_SOURCE:
        source = inspect.getsource(getattr(cm, name))
        assert (
            "m3_l2_" not in source and "L2_" not in source and "_SuccessorRouteProof" not in source
        )
    # The committed literals the legacy route pins are untouched.
    assert cm.WITNESS_RANK_TABLE == "chunk_witness_rank"
    assert cc.CORRECTIONS_TABLE == "chunk_observation_corrections"
    assert cm.PLAN_WITNESS_TABLE == "plan_chunk_witnesses"
    assert cm.PLAN_WITNESS_RANK_TABLE == "plan_witness_rank"
    assert cm.PLAN_LEDGER_TABLE == "chunk_first_witness"


def test_l02_legacy_worlds_carry_no_successor_relation_and_the_successor_leaves_no_temp(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    assert estate.legacy is not None
    legacy_worlds = [estate.legacy["world_directory"]] + [
        Path(estate.succ["intermediates_root"]) / g.group_id / f"attempt-{r.attempt:03d}"
        for g, r in zip(estate.schedule.groups, estate.succ["intermediates"], strict=True)
    ]
    for world in legacy_worlds:
        connection = r19.readonly(world / WORKING_CATALOG_FILENAME)
        try:
            names = {
                str(row["name"])
                for row in connection.execute("SELECT name FROM main.sqlite_master")
            }
        finally:
            connection.close()
        assert not {name for name in names if name.startswith("m3_l2_")}, world.name
        assert not {name for name in names if name in c17.LEGACY_LEVEL_TWO_RELATIONS}, world.name
    cm.run_successor_multipass_final(r19.production_request(estate))
    connection = r19.readonly(estate.catalog)
    try:
        names = {
            str(row["name"]) for row in connection.execute("SELECT name FROM main.sqlite_master")
        }
        temp_names = {
            str(row["name"]) for row in connection.execute("SELECT name FROM temp.sqlite_master")
        }
    finally:
        connection.close()
    assert set(cm.L2_PERSISTENT_RELATIONS) <= names and temp_names == set()
    assert not {n for n in names if n in c17.LEGACY_LEVEL_TWO_RELATIONS}


def test_l03_the_legacy_temp_behaviour_is_unchanged_on_this_tree(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path)
    assert estate.legacy is not None
    catalog = estate.legacy["world_directory"] / WORKING_CATALOG_FILENAME
    intermediates = [
        Path(estate.legacy["intermediates_root"])
        / g.group_id
        / f"attempt-{r.attempt:03d}"
        / WORKING_CATALOG_FILENAME
        for g, r in zip(
            estate.legacy["schedule"].groups, estate.legacy["intermediates"], strict=True
        )
    ]
    connection = sqlite3.connect(str(catalog), isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        aliases = cc._attach_all(connection, intermediates, "k")
        first = cm.stage_first_witness_corrections(connection, aliases)
        names = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM temp.sqlite_master WHERE type = 'table'"
            )
        }
        assert {cm.WITNESS_RANK_TABLE, cc.CORRECTIONS_TABLE} <= names
        with pytest.raises(cm.ChunkMultipassError, match="already been staged on this connection"):
            cm.stage_first_witness_corrections(connection, aliases)
        cc._detach_all(connection, aliases)
        chunks = cc.resolve_chunk_inputs(estate.run["plan"], internal_root=estate.run["chunk_root"])
        counters = cm._plan_first_witness_counters(connection, chunks)
        with pytest.raises(cm.ChunkMultipassError, match="already derived on this connection"):
            cm._plan_first_witness_counters(connection, chunks)
        main_names = {
            str(row["name"]) for row in connection.execute("SELECT name FROM main.sqlite_master")
        }
        assert not {n for n in main_names if n.startswith("m3_l2_")}
    finally:
        connection.close()
    assert first[0] >= 0 and counters == r19.counters(estate.legacy["final"].as_record())


def test_l04_every_legacy_reader_refuses_a_successor_artifact(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached
    receipt = r19.receipt_files(estate.receipt_root)[0]
    with pytest.raises(ChunkEvidenceError, match="carries contract"):
        read_receipt_document(receipt, contract=cm.INTERMEDIATE_RECEIPT_CONTRACT)
    with pytest.raises(cm.ChunkMultipassError, match="is exact"):
        cm.read_calibration_subset_result(receipt)
    assert cm.completed_intermediate_receipt(estate.world.parent, estate.world.name) is None
    # The successor's own readers refuse a legacy document standing in for a stage receipt.
    legacy_final = estate.world / "final_world_receipt.json"
    with pytest.raises(
        cm.ChunkMultipassError, match="not persisted as its canonical bytes|carries contract"
    ):
        cm.read_stage_receipt(legacy_final)
