"""D151-C31R2-R19A-C2 §33: staged equals monolithic -- the semantic oracles.

The six persistent successor relations hold exactly the rows the legacy TEMP relations hold when
the accepted legacy functions run over the same inputs; the four whole-F0 counters are the
accepted derivation's; the winner is the canonical-earliest input; the two closure keys stay
distinct; a second derivation refuses through applied-unit state with the exact legacy text and
leaves the first derivation intact; directory enumeration order decides nothing; and the
successor world is admitted by the accepted F1 and F2.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_equivalence as eq  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME  # noqa: E402


def _rows(
    connection: sqlite3.Connection, schema: str, table: str, columns: Sequence[str]
) -> list[tuple[Any, ...]]:
    projection = ", ".join(columns)
    return sorted(
        tuple(row)
        for row in connection.execute(f"SELECT {projection} FROM {schema}.{table}")  # noqa: S608
    )


RANK_COLUMNS = (
    "accession_plain",
    "source_observation_id",
    "parsed_record_id",
    "first_observed_at_utc",
    "chunk_ordinal",
    "witness_rank",
    "witnesses",
)
CORRECTION_COLUMNS = (
    "accession_observation_id",
    "accession_plain",
    "source_observation_id",
    "parsed_record_id",
    "field_name",
    "raw_value_json",
    "observed_at_utc",
    "conflict_indicator",
)


def test_s01_the_persistent_relations_equal_the_legacy_temp_relations_row_for_row(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached and outcome.final_receipt is not None
    # The legacy functions, run over a TEST-OWNED copy of the finished successor catalog with
    # the same intermediates attached: they build the TEMP relations from the same loaded rows.
    copy = tmp_path / "oracle"
    shutil.copytree(estate.world, copy)
    connection = sqlite3.connect(copy / WORKING_CATALOG_FILENAME, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        catalogs = [
            Path(estate.succ["intermediates_root"])
            / group.group_id
            / f"attempt-{receipt.attempt:03d}"
            / WORKING_CATALOG_FILENAME
            for group, receipt in zip(
                estate.schedule.groups, estate.succ["intermediates"], strict=True
            )
        ]
        aliases = cc._attach_all(connection, catalogs, "k")
        contested, staged = cm.stage_first_witness_corrections(connection, aliases)
        cc._detach_all(connection, aliases)
        assert _rows(connection, "temp", cm.WITNESS_RANK_TABLE, RANK_COLUMNS) == _rows(
            connection, "main", cm.L2_WITNESS_RANK_TABLE, RANK_COLUMNS
        )
        assert _rows(connection, "temp", cc.CORRECTIONS_TABLE, CORRECTION_COLUMNS) == _rows(
            connection, "main", cm.L2_CORRECTIONS_TABLE, CORRECTION_COLUMNS
        )
        units = {
            u.stage_id: u
            for u in (cm.AppliedUnit.from_row(r) for r in r19.applied_units(estate.catalog))
        }
        witness = units["S12"].outcome_witness
        assert (witness["contested"], witness["rows_staged"]) == (contested, staged)
        chunks = cc.resolve_chunk_inputs(estate.run["plan"], internal_root=estate.run["chunk_root"])
        legacy_counters = cm._plan_first_witness_counters(connection, chunks)
        assert legacy_counters == r19.counters(outcome.final_receipt)
        witness_columns = ("accession_plain", "parsed_record_id", "chunk_ordinal")
        assert _rows(connection, "temp", cm.PLAN_WITNESS_TABLE, witness_columns) == _rows(
            connection, "main", cm.L2_PLAN_WITNESS_TABLE, witness_columns
        )
        rank_columns = ("accession_plain", "parsed_record_id", "witness_rank", "witnesses")
        assert _rows(connection, "temp", cm.PLAN_WITNESS_RANK_TABLE, rank_columns) == _rows(
            connection, "main", cm.L2_PLAN_WITNESS_RANK_TABLE, rank_columns
        )
        ledger_columns = (
            "native_identity",
            "member_ordinal",
            "record_ordinal",
            "delta_materialized",
        )
        assert _rows(connection, "temp", cm.PLAN_LEDGER_TABLE, ledger_columns) == _rows(
            connection, "main", cm.L2_PLAN_LEDGER_TABLE, ledger_columns
        )
        assert _rows(
            connection, "temp", "chunk_member_delta", ("member_ordinal", "delta")
        ) == _rows(connection, "main", cm.L2_MEMBER_DELTA_TABLE, ("member_ordinal", "delta"))
    finally:
        connection.close()
    assert estate.legacy is not None
    assert r19.counters(estate.legacy["final"].as_record()) == r19.counters(outcome.final_receipt)


def test_s02_the_winner_is_the_canonical_earliest_input_and_the_closure_keys_stay_distinct(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate))
    connection = r19.readonly(estate.catalog)
    try:
        ranks = connection.execute(
            "SELECT accession_plain, chunk_ordinal, witness_rank, witnesses "  # noqa: S608
            f"FROM main.{cm.L2_PLAN_WITNESS_RANK_TABLE} r JOIN (SELECT accession_plain AS a, "
            f"parsed_record_id AS p, chunk_ordinal FROM main.{cm.L2_PLAN_WITNESS_TABLE}) w "
            "ON w.a = r.accession_plain AND w.p = r.parsed_record_id "
            "ORDER BY accession_plain, witness_rank"
        ).fetchall()
        by_accession: dict[str, list[tuple[int, int]]] = {}
        for row in ranks:
            by_accession.setdefault(str(row["accession_plain"]), []).append(
                (int(row["witness_rank"]), int(row["chunk_ordinal"]))
            )
        contested = {a: items for a, items in by_accession.items() if len(items) > 1}
        assert contested, "the fixture produced no cross-chunk accession"
        for items in contested.values():
            ordered = sorted(items)
            assert ordered[0][1] == min(o for _r, o in items)
            assert [rank for rank, _o in ordered] == list(range(1, len(items) + 1))
        # The member-delta reduction partitions by native_identity, never by accession_plain.
        oracle = sorted(
            tuple(row)
            for row in connection.execute(
                "WITH ranked AS (SELECT member_ordinal, delta_materialized, ROW_NUMBER() OVER "  # noqa: S608
                "(PARTITION BY native_identity ORDER BY member_ordinal, record_ordinal) AS rn "
                f"FROM main.{cm.L2_PLAN_LEDGER_TABLE}) "  # noqa: S608
                "SELECT member_ordinal, SUM(delta_materialized) FROM ranked WHERE rn > 1 "
                "GROUP BY member_ordinal"
            )
        )
        assert oracle == _rows(
            connection, "main", cm.L2_MEMBER_DELTA_TABLE, ("member_ordinal", "delta")
        )
    finally:
        connection.close()


def test_s03_a_second_derivation_refuses_with_the_legacy_text_and_leaves_the_first_intact(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S12"))
    units = [cm.AppliedUnit.from_row(r) for r in r19.applied_units(estate.catalog)]
    stage = next(
        s
        for s in cm.successor_stage_graph(cm.SUCCESSOR_ROUTE_PRODUCTION, 10)
        if s.stage_id == "S12"
    )
    before = (
        r19.count(estate.catalog, cm.L2_WITNESS_RANK_TABLE),
        r19.count(estate.catalog, cm.L2_CORRECTIONS_TABLE),
    )
    proof = cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_PRODUCTION, gate=lambda: None, gate_name="t"
    )
    context = cm._resolve_successor_context(r19.production_request(estate), proof)
    connection = r19.writer(estate.catalog)
    try:
        instr = cm._stage_instrumentation_for(context, stage, units)
        with pytest.raises(cm.ChunkMultipassError, match="already derived on this connection"):
            cm._stage_observation_corrections(connection, units, stage, instr)
        rank_stage = next(
            s
            for s in cm.successor_stage_graph(cm.SUCCESSOR_ROUTE_PRODUCTION, 10)
            if s.stage_id == "S11"
        )
        rank_instr = cm._stage_instrumentation_for(context, rank_stage, units)
        with pytest.raises(cm.ChunkMultipassError, match="already derived on this connection"):
            cm._stage_witness_rank(connection, (), units, rank_stage, rank_instr)
    finally:
        connection.close()
    assert (
        r19.count(estate.catalog, cm.L2_WITNESS_RANK_TABLE),
        r19.count(estate.catalog, cm.L2_CORRECTIONS_TABLE),
    ) == before
    assert r19.stage_ids(estate.catalog)[-1] == "S12"
    cm.run_successor_multipass_final(r19.production_request(estate))
    units = [cm.AppliedUnit.from_row(r) for r in r19.applied_units(estate.catalog)]
    counters_stage = next(
        s
        for s in cm.successor_stage_graph(cm.SUCCESSOR_ROUTE_PRODUCTION, 10)
        if s.stage_id == "S17C"
    )
    proof = cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_PRODUCTION, gate=lambda: None, gate_name="t"
    )
    context = cm._resolve_successor_context(r19.production_request(estate), proof)
    connection = r19.writer(estate.catalog)
    try:
        instr = cm._stage_instrumentation_for(context, counters_stage, units)
        with pytest.raises(cm.ChunkMultipassError, match="already derived on this connection"):
            cm._stage_counters_finalize(connection, context, units, counters_stage, instr)
    finally:
        connection.close()


def test_s04_directory_enumeration_order_decides_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    forward = r19.prepare(tmp_path / "forward", legacy=False)
    reverse = r19.prepare(tmp_path / "reverse", legacy=False)
    first = cm.run_successor_multipass_final(r19.production_request(forward))
    original = Path.iterdir

    def reversed_iterdir(self: Path) -> Any:
        return iter(sorted(original(self), reverse=True))

    monkeypatch.setattr(Path, "iterdir", reversed_iterdir)
    second = cm.run_successor_multipass_final(r19.production_request(reverse))
    monkeypatch.undo()
    assert first.final_receipt is not None and second.final_receipt is not None
    assert r19.counters(first.final_receipt) == r19.counters(second.final_receipt)
    for key in ("completeness_digest", "member_manifest_digest", "table_row_counts"):
        assert first.final_receipt[key] == second.final_receipt[key]
    eq.assert_equivalent(eq.measure(forward.world), eq.measure(reverse.world))


def test_s05_the_successor_world_is_admitted_by_the_accepted_f1_and_f2(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path)
    cm.run_successor_multipass_final(r19.production_request(estate))
    assert estate.legacy is not None
    successor = eq._f1_and_f2(estate.world, estate.database)
    legacy = eq._f1_and_f2(estate.legacy["world_directory"], estate.database)
    assert successor == legacy
