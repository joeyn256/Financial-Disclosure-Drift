"""D151-C31R2-R19B-C2 §12, §17-§23: source-scan conformance, request hardening, versioning,
the operation registry, dynamic SQL capture and the sqlite boundary.

* the consolidator keeps exactly one ``executemany(``, inside ``_stage_rows``, which stays a
  bounded control operation outside instrumentation; the scanned bodies keep their shape; the
  module reaches no environment, no ``DISCLOSURE_DRIFT`` text and no E0 import; the unaudited
  seam modules name no chunk-family module;
* the historical ``FinalMergeRequest`` keeps its field set, names and serialization byte for
  byte; a historical ``cache_bytes = null`` record parses and is refused by every successor
  (future Level-Two) execution boundary, with no substitution;
* a ``/1`` StagePlan parses for forensics and never executes; a ``/2`` plan requires every
  instrumentation field exactly, each moving the StagePlan identity; the tool manifest has its
  own contract;
* the registry is derived from the stage graph, its counts equal an independent enumeration,
  every SQLite operation is STATIC_SQL or DYNAMIC_SQL_CAPTURE, dynamic SQL is captured exactly
  at the boundary, the legacy ``None`` runner composes the same text, and every statement a
  stage transaction executes is either a journaled material statement or a control statement.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c13_intermediates as c13i  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import compact_evidence as ce  # noqa: E402
from disclosure_drift.m3 import working_catalog as wc  # noqa: E402
from disclosure_drift.m3.chunk_execution import F0_WRITTEN_TABLES  # noqa: E402

CHUNK_FAMILY = (
    "chunk_plan",
    "chunk_evidence",
    "chunk_execution",
    "chunk_storage",
    "chunk_consolidation",
    "chunk_multipass",
    "chunk_tiering",
)

#: The historical final-merge request's exact serialized field set, in ``as_record`` order --
#: the C31R2 ``final-request.json`` shape. Frozen here so a change to it is a failing test.
HISTORICAL_FINAL_REQUEST_FIELDS = (
    "kind",
    "plan_path",
    "schedule_path",
    "intermediates_root",
    "internal_root",
    "external_root",
    "operational_catalog",
    "world_directory",
    "run_id",
    "cache_bytes",
    "repository_head_sha",
    "repository_tree_sha",
    "storage_requirements",
    "expected_sqlite_temp_binding",
    "capacity_observations",
)


def _source(module: object) -> str:
    return Path(str(module.__file__)).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _bodies(source: str) -> dict[str, str]:
    lines = source.splitlines()
    return {
        node.name: "\n".join(lines[node.lineno - 1 : node.end_lineno])
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef)
    }


def _mint() -> cm._SuccessorRouteProof:
    return cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_PRODUCTION, gate=lambda: None, gate_name="t"
    )


def _units(estate: r19.SuccessorWorld) -> dict[str, cm.AppliedUnit]:
    return {
        u.stage_id: u
        for u in (cm.AppliedUnit.from_row(r) for r in r19.applied_units(estate.catalog))
    }


def _statements(unit: cm.AppliedUnit) -> list[dict[str, Any]]:
    assert unit.statement_execution_set is not None
    return [dict(item) for item in unit.statement_execution_set["statements"]]  # type: ignore[union-attr]


def _historical_record() -> dict[str, Any]:
    return {
        "kind": cm.MULTIPASS_REQUEST_KIND_FINAL,
        "plan_path": "/historical/multipass/chunk_plan.json",
        "schedule_path": "/historical/multipass/merge_schedule.json",
        "intermediates_root": "/historical/multipass/intermediates",
        "internal_root": "/historical/chunks",
        "external_root": None,
        "operational_catalog": "/historical/catalog.sqlite3",
        "world_directory": "/historical/multipass/final",
        "run_id": "d151-c31r2-20260830T150526Z",
        "cache_bytes": None,
        "repository_head_sha": "7a1fcf0831e9159a7b9f4ee9592b75497a1d5178",
        "repository_tree_sha": "f1d7c1125982c1d9e5e30bb19d972653a0e2dc8c",
        "storage_requirements": {
            "internal_reserve_bytes": 0,
            "level_one_peak_ratio": 1.0,
            "level_two_peak_ratio": 1.0,
            "level_one_transient_bytes": 0,
            "level_two_transient_bytes": 0,
        },
        "expected_sqlite_temp_binding": {"charged_volume_uuid": "x"},
        "capacity_observations": [],
    }


# ==========================================================================
# §12 -- consolidation source-text invariants (owner ruling C2-R1)
# ==========================================================================
def test_b01_the_consolidator_keeps_one_executemany_inside_stage_rows_and_its_scans_hold() -> None:
    source = _source(cc)
    assert source.count("executemany(") == 1
    tree = ast.parse(source)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "executemany"
    ]
    assert len(calls) == 1
    enclosing = [
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.lineno <= calls[0].lineno <= (node.end_lineno or node.lineno)
    ]
    assert enclosing == ["_stage_rows"]
    bodies = _bodies(source)
    # _stage_rows is the bounded control operation: never routed through the seam.
    assert cm.STAGE_ROWS_CLASSIFICATION == "BOUNDED_CONTROL_OPERATION"
    for token in ("statement_runner", "_run_statement", "StatementRunner"):
        assert token not in bodies["_stage_rows"], token
    # The accepted scanned bodies keep their shape; the seam helper adds no executemany.
    for name in (
        "_sorted_bulk_load",
        "_keyed_first_last_load",
        "_load_accession_observations",
        "consolidate_chunks",
        "_require_parser_run_truth",
    ):
        body = bodies[name]
        assert "executemany" not in body and "for row in" not in body, name
        assert "INSERT" not in body or "SELECT" in body, name
    assert "executemany" not in bodies["_run_statement"]
    for needle in (
        'f"{verb} {table} ({projection}) "',
        "ORDER BY {key}, chunk_ordinal",
        "ROW_NUMBER() OVER (PARTITION BY {key} ORDER BY chunk_ordinal)",
        "ORDER BY accession_observation_id, priority, chunk_ordinal",
    ):
        assert needle in source, needle
    # No environment, clock, free-space, process or journal logic in the consolidator.
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    for forbidden in ("environ", "getenv", "statvfs", "getrusage", "monotonic_ns", "fsync"):
        assert forbidden not in names and forbidden not in attributes, forbidden
    assert "DISCLOSURE_DRIFT" not in source
    assert "from disclosure_drift.m3.e0" not in source
    for forbidden in ("two_level", "multi_pass", "second_pass", "def _merge_pass"):
        assert forbidden not in source, forbidden
    # The seam-routed helpers are exactly the six, each with a keyword-only runner default None.
    for name in (
        "_sorted_bulk_load",
        "_keyed_first_last_load",
        "_reduced_parser_run",
        "_apply_duplicate_identities",
        "_member_deltas",
        "_merge_sidecar",
    ):
        parameter = inspect.signature(getattr(cc, name)).parameters["statement_runner"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is None
    # The two unaudited seam modules name no chunk-family module (a39/a28 closure scans).
    for module in (wc, ce):
        text = _source(module)
        for stem in CHUNK_FAMILY:
            assert stem not in text, (module.__name__, stem)


# ==========================================================================
# §17 -- historical request preserved, future boundaries gated
# ==========================================================================
def test_b02_the_historical_final_merge_request_serialization_is_byte_identical() -> None:
    assert tuple(inspect.signature(cm.FinalMergeRequest).parameters) == (
        *HISTORICAL_FINAL_REQUEST_FIELDS[1:],
        "kind",
    )
    record = _historical_record()
    request = cm.FinalMergeRequest.from_record(record)
    assert request.cache_bytes is None
    rendered = dict(request.as_record())
    assert tuple(rendered) == HISTORICAL_FINAL_REQUEST_FIELDS
    assert json.dumps(rendered, sort_keys=True) == json.dumps(record, sort_keys=True)
    assert json.dumps(rendered, sort_keys=True, indent=2, default=str).encode("utf-8") == (
        json.dumps(record, sort_keys=True, indent=2, default=str).encode("utf-8")
    )
    again = cm.FinalMergeRequest.from_record(rendered)
    assert dict(again.as_record()) == rendered
    assert "successor" not in inspect.getsource(cm.FinalMergeRequest)


def test_b03_a_historical_null_cache_request_is_readable_and_never_executable_by_the_successor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _historical_record()
    historical = cm.FinalMergeRequest.from_record(record)
    assert historical.cache_bytes is None
    # The successor reader refuses the historical shape outright.
    with pytest.raises(cm.ChunkMultipassError, match="could not be read"):
        cm.SuccessorFinalRequest.from_record(record)
    successor_shaped = {
        **record,
        "kind": cm.SUCCESSOR_REQUEST_KIND_FINAL,
        "route": cm.SUCCESSOR_ROUTE_PRODUCTION,
        "stage_receipt_root": "/historical/receipts",
        "predecessor_run_id": "pred",
        "predecessor_checkpoint_count": 46,
        "predecessor_tip_ordinal": 45,
        "predecessor_tip_identity": "x",
        "predecessor_completed_group_count": 5,
        "statement_observability": dict(r19.SYNTHETIC_OBSERVABILITY),
        "stop_after_stage": None,
    }
    with pytest.raises(cm.ChunkMultipassError, match="requires cache_bytes"):
        cm.SuccessorFinalRequest.from_record(successor_shaped)
    # No successor entry accepts the historical request object at all.
    with pytest.raises(cm.ChunkMultipassError, match="serves the production route only"):
        cm.run_successor_multipass_final(historical)  # type: ignore[arg-type]
    # The execution-boundary gate: every wrong shape refused, no substitution anywhere.
    for value in (None, True, False, 8_388_608.0, 0, -1024, 1000, "8388608"):
        with pytest.raises(cm.ChunkMultipassError, match="Level-Two execution boundary"):
            cm.require_executable_level_two_cache_bytes(value)
    assert cm.require_executable_level_two_cache_bytes(8_388_608) == 8_388_608
    tree = ast.parse(_source(cm))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    world_openings = [
        node
        for name in ("_initialize_world_attempt", "_successor_world_session")
        for node in ast.walk(functions[name])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "WorkingCatalog"
    ]
    assert len(world_openings) == 2
    for call in world_openings:
        cache = next(k for k in call.keywords if k.arg == "cache_bytes")
        assert (
            isinstance(cache.value, ast.Call)
            and isinstance(cache.value.func, ast.Name)
            and cache.value.func.id == "require_executable_level_two_cache_bytes"
        )
    constructions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "SuccessorFinalRequest"
    ]
    assert all(
        any(
            isinstance(parent, ast.FunctionDef)
            and parent.name == "from_record"
            and parent.lineno <= node.lineno <= (parent.end_lineno or parent.lineno)
            for parent in ast.walk(tree)
        )
        for node in constructions
    )
    for name in ("SQLITE_DEFAULT_CACHE_SIZE_PRAGMA", "DEFAULT_SYNTHETIC_CACHE_BYTES"):
        for function in ("_initialize_world_attempt", "_successor_world_session"):
            assert name not in inspect.getsource(getattr(cm, function)), (name, function)


# ==========================================================================
# §18-§19 -- contract versioning and the /2 StagePlan
# ==========================================================================
def test_b04_a_historical_v1_stage_plan_parses_and_never_executes(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S1"))
    stored = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
    assert stored.contract == cm.L2_STAGE_PLAN_CONTRACT_V2 and stored.executable
    v1_body = {
        key: value for key, value in stored.body.items() if key not in cm._STAGE_PLAN_V2_FIELDS
    }
    v1_body["contract"] = cm.L2_STAGE_PLAN_CONTRACT
    historical = cm.L2StagePlan.from_record(v1_body)
    assert historical.contract == cm.L2_STAGE_PLAN_CONTRACT and not historical.executable
    assert historical.identity != stored.identity
    with pytest.raises(cm.ChunkMultipassError, match="/1 StagePlan"):
        _ = historical.observability_terms
    # A world carrying a /1 plan is readable and is refused before any mutation.
    connection = r19.writer(estate.catalog)
    try:
        connection.execute(
            f"UPDATE main.{cm.L2_STAGE_PLAN_TABLE} "  # noqa: S608
            "SET contract = ?, stage_plan_identity = ?, body_json = ?",
            (cm.L2_STAGE_PLAN_CONTRACT, historical.identity, cm._json_text(dict(v1_body))),
        )
    finally:
        connection.close()
    assert cm._read_stored_stage_plan(r19.readonly(estate.catalog)).identity == historical.identity
    with pytest.raises(cm.ChunkMultipassError, match="NEVER executed"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    assert r19.stage_ids(estate.catalog) == ["S0", "S1"]
    assert cm.L2StagePlan.from_record(dict(stored.as_record())).identity == stored.identity


def test_b05_every_v2_field_is_required_exact_and_moves_the_identity(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    proof = _mint()
    plan = cm._resolve_successor_context(r19.production_request(estate), proof).stage_plan
    record = dict(plan.as_record())
    body = {key: value for key, value in record.items() if key != "stage_plan_identity"}
    for field in cm._STAGE_PLAN_V2_FIELDS:
        with pytest.raises(cm.ChunkMultipassError, match="lacks"):
            cm.L2StagePlan.from_record({k: v for k, v in body.items() if k != field})
    refusals = {
        "statement_progress_interval_seconds": (0, 301, True, 1.0),
        "progress_handler_vm_steps": (999, 100_001, True),
        "wal_watchdog_max_uncommitted_frames": (0, -1, True),
        "expected_page_size_bytes": (4095, 1 << 20, True),
        "wal_watchdog_storage_ceiling_bytes": (0, -1, True, 4096.0),
    }
    for field, values in refusals.items():
        for value in values:
            with pytest.raises(cm.ChunkMultipassError):
                cm.L2StagePlan.from_record({**body, field: value})
    assert cm.L2StagePlan.from_record({**body, "progress_handler_vm_steps": 1000}).executable
    assert cm.L2StagePlan.from_record({**body, "progress_handler_vm_steps": 100_000}).executable
    with pytest.raises(cm.ChunkMultipassError, match="statement_progress_root must be exactly"):
        cm.L2StagePlan.from_record({**body, "statement_progress_root": str(tmp_path / "x")})
    with pytest.raises(cm.ChunkMultipassError, match="statement_progress_root must be exactly"):
        cm.L2StagePlan.from_record(
            {
                **body,
                "statement_progress_root": str(
                    Path(str(body["stage_receipt_root"])) / ".." / "statement-progress"
                ),
            }
        )
    registry = list(body["statement_registry"])  # type: ignore[arg-type]
    with pytest.raises(cm.ChunkMultipassError, match="statement registry"):
        cm.L2StagePlan.from_record({**body, "statement_registry": registry[1:]})
    with pytest.raises(cm.ChunkMultipassError, match="statement registry"):
        cm.L2StagePlan.from_record({**body, "statement_registry_identity": "0" * 64})
    # Each instrumentation field moves the StagePlan identity, through the request.
    identities = {plan.identity}
    for field, value in (
        ("statement_progress_interval_seconds", 2),
        ("progress_handler_vm_steps", 2000),
        ("wal_watchdog_max_uncommitted_frames", 64),
    ):
        terms = {**r19.SYNTHETIC_OBSERVABILITY, field: value}
        moved = cm._resolve_successor_context(
            r19.production_request(estate, statement_observability=terms), proof
        ).stage_plan
        assert moved.identity not in identities
        identities.add(moved.identity)
    other = r19.R19B_REQUIREMENTS
    requirements = type(other)(
        internal_reserve_bytes=0,
        level_one_peak_ratio=1.0,
        level_two_peak_ratio=1.0,
        level_one_transient_bytes=0,
        level_two_transient_bytes=other.level_two_transient_bytes * 2,
    )
    moved = cm._resolve_successor_context(
        r19.production_request(estate, storage_requirements=dict(requirements.as_record())), proof
    ).stage_plan
    assert moved.identity not in identities
    assert moved.wal_watchdog_storage_ceiling_bytes == other.level_two_transient_bytes * 2
    # The page size is the world's page size, verified at every reopen.
    with pytest.raises(cm.ChunkMultipassError, match="page_size reads 4096"):
        cm.run_successor_multipass_final(
            r19.production_request(
                estate,
                stop_after="S0",
                statement_observability={
                    **r19.SYNTHETIC_OBSERVABILITY,
                    "expected_page_size_bytes": 8192,
                },
            )
        )
    assert not estate.world.exists()


def test_b06_every_new_contract_literal_is_exact_and_no_plan_contract_is_reused() -> None:
    expected = {
        "L2_STAGE_PLAN_CONTRACT": "m3.3-chunked-f0-l2-stage-plan/1",
        "L2_STAGE_PLAN_CONTRACT_V2": "m3.3-chunked-f0-l2-stage-plan/2",
        "L2_APPLIED_UNIT_CONTRACT_V2": "m3.3-chunked-f0-l2-applied-unit/2",
        "L2_STAGE_RECEIPT_CONTRACT_V2": "m3.3-chunked-f0-l2-stage-receipt/2",
        "L2_TOOL_MANIFEST_CONTRACT": "m3.3-chunked-f0-l2-tool-manifest/1",
        "L2_STATEMENT_REGISTRY_CONTRACT": "m3.3-chunked-f0-l2-statement-registry/1",
        "L2_STATEMENT_JOURNAL_CONTRACT": "m3.3-chunked-f0-l2-statement-journal/1",
        "L2_STATEMENT_EVENT_CONTRACT": "m3.3-chunked-f0-l2-statement-event/1",
        "L2_STATEMENT_EXECUTION_SET_CONTRACT": "m3.3-chunked-f0-l2-statement-execution-set/1",
    }
    for name, literal in expected.items():
        assert getattr(cm, name) == literal, name
        assert c13i.committed_literal(cm, name) == literal, name
    assert wc.STATEMENT_JOURNAL_CONTRACT == cm.L2_STATEMENT_JOURNAL_CONTRACT
    assert wc.STATEMENT_EVENT_CONTRACT == cm.L2_STATEMENT_EVENT_CONTRACT
    assert len(set(expected.values())) == len(expected)
    assert cm.ToolManifest(entries=(), identity="x").as_record()["contract"] == (
        cm.L2_TOOL_MANIFEST_CONTRACT
    )
    assert cm.STATEMENT_PROGRESS_DIRECTORY == "statement-progress"


# ==========================================================================
# §20-§21 -- the registry
# ==========================================================================
def _independent_operation_count(route: str, chunks: int) -> int:
    fan_in = cm.MERGE_FAN_IN
    batches = -(-chunks // fan_in)
    per_stage = {"S2": 3, "S3": 3, "S11": 3, "S12": 6, "S13": 2, "S14": 3, "S17C": 10, "S18": 11}
    total = sum(per_stage.values()) + 7 * 2  # S4..S10: load + count
    total += 5  # S16.0..S16.4
    total += batches * 2 * 2  # S17A/S17B per batch: insert + count
    if route == cm.SUCCESSOR_ROUTE_PRODUCTION:
        total += 1  # S15P
    total += 1  # reauthentication (S21P / S20C)
    total += 2  # terminal: table_row_counts + build_artifact_manifest
    return total


def test_b07_the_registry_equals_an_independent_enumeration_and_every_sql_op_is_identified() -> (
    None
):
    for route, chunks in (
        (cm.SUCCESSOR_ROUTE_PRODUCTION, 10),
        (cm.SUCCESSOR_ROUTE_PRODUCTION, 19),
        (cm.SUCCESSOR_ROUTE_CALIBRATION, 10),
    ):
        registry = cm.successor_statement_registry(route, chunks)
        assert len(registry) == _independent_operation_count(route, chunks), (route, chunks)
        counts = cm.registry_counts(registry)
        assert counts["MATERIAL_OPERATION_COUNT"] == len(registry)
        assert counts["MATERIAL_SQL_STATEMENT_COUNT"] == (
            counts["STATIC_SQL_DESCRIPTOR_COUNT"] + counts["DYNAMIC_SQL_CAPTURE_DESCRIPTOR_COUNT"]
        )
        assert counts["CALLABLE_NON_SQL_DESCRIPTOR_COUNT"] == 3
        assert counts["MATERIAL_SQL_STATEMENT_COUNT"] + 3 == len(registry)
        modes = {str(item["sql_identity_mode"]) for item in registry}
        assert modes == {"STATIC_SQL", "DYNAMIC_SQL_CAPTURE", "CALLABLE_NON_SQL"}
        for item in registry:
            assert item["instrumentation_required"] is True
            assert item["descriptor_identity"] == cm._identity_of(
                {k: v for k, v in item.items() if k != "descriptor_identity"}
            )
            if item["sql_identity_mode"] == "STATIC_SQL":
                assert isinstance(item["static_sql_sha256"], str)
                assert len(item["static_sql_sha256"]) == 64
            elif item["sql_identity_mode"] == "DYNAMIC_SQL_CAPTURE":
                assert item["static_sql_sha256"] is None
            else:
                assert item["operation_kind"] in {"callable", "path_decision"}
                assert item["watchdog_applicable"] is False
            if (
                item["database_role"] in {"WORKING_CATALOG", "COMPACT_EVIDENCE"}
                and item["sql_identity_mode"] != "CALLABLE_NON_SQL"
            ):
                assert item["watchdog_applicable"] is True
        statement_ids = [str(item["statement_id"]) for item in registry]
        assert len(statement_ids) == len(set(statement_ids))
        stage_ids = {str(item["stage_id"]) for item in registry}
        if route == cm.SUCCESSOR_ROUTE_PRODUCTION:
            assert "S15P" in stage_ids and "S23P" in stage_ids and "S21P" in stage_ids
        else:
            assert "S15P" not in stage_ids and "S21C" in stage_ids and "S20C" in stage_ids
    # The static digests are the digests of the exact texts the runtime executes.
    ten = {str(i["statement_id"]): i for i in cm.successor_statement_registry("production", 10)}
    sha = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()  # noqa: E731
    assert ten["S2/reduced_parser_run.insert_run_row"]["static_sql_sha256"] == sha(
        cc.REDUCED_PARSER_RUN_INSERT_SQL
    )
    assert ten["S2/count:census_parser_runs"]["static_sql_sha256"] == sha(
        "SELECT COUNT(*) AS n FROM main.census_parser_runs"
    )
    assert ten["S18/sidecar.member_manifest_rows"]["static_sql_sha256"] == sha(
        ce.MEMBER_MANIFEST_ROWS_SQL
    )
    assert ten["S3/apply_duplicate_identities.update"]["expected_executions"] == (
        "witness:S2.duplicate_identities"
    )
    assert ten["S14/candidate_edges.select"]["expected_executions"] == 2
    assert ten["S17A.1/counter_catalog.insert"]["expected_executions"] == 1  # 10 chunks: 9 + 1
    assert ten["S23P/table_row_counts"]["expected_executions"] == len(F0_WRITTEN_TABLES)
    assert ten["S18/merge_sidecar.insert_members"]["path"] == "BUILD"
    assert ten["S18/path_decision"]["path"] is None
    assert ten["S18/sidecar.identity_fold:compact_source_members"]["path"] is None
    # The registry identity binds route and chunk count.
    assert cm._registry_identity(
        "production", 10, cm.successor_statement_registry("production", 10)
    ) != (
        cm._registry_identity("production", 19, cm.successor_statement_registry("production", 19))
    )


def test_b08_dynamic_sql_is_captured_exactly_and_the_legacy_runner_composes_the_same_text(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S13"))
    units = _units(estate)
    aliases = tuple(f"k{i}" for i in range(len(estate.schedule.groups)))
    sha = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()  # noqa: E731
    # S2: the union select reconstructed independently equals the journaled runtime identity.
    projection = (
        "parser_run_id, source_observation_id, parser_id, parser_version, started_at_utc, "
        "finished_at_utc, parsed_count, quarantined_count, outcome, summary_json"
    )
    union = cc._union_all(aliases, "census_parser_runs", projection, extra=" AS chunk_ordinal")
    s2 = {item["operation"]: item for item in _statements(units["S2"])}
    assert s2["reduced_parser_run.select_chunk_runs"]["runtime_sql_sha256"] == sha(
        f"SELECT * FROM ({union}) ORDER BY chunk_ordinal"  # noqa: S608
    )
    assert s2["reduced_parser_run.select_chunk_runs"]["sql_identity_mode"] == "DYNAMIC_SQL_CAPTURE"
    assert s2["reduced_parser_run.insert_run_row"]["runtime_sql_sha256"] == sha(
        cc.REDUCED_PARSER_RUN_INSERT_SQL
    )
    # S3 / S10: the legacy None runner composes the very text the successor captured.
    for stage_id, table in (
        ("S3", "census_parsed_records"),
        ("S10", "census_malformed_historical_references"),
    ):
        connection = r19.readonly(estate.catalog)
        try:
            columns = cc._columns(connection, table)
        finally:
            connection.close()
        traced: list[str] = []
        probe = sqlite3.connect(":memory:")
        probe.set_trace_callback(traced.append)
        probe.row_factory = sqlite3.Row
        for alias in aliases:
            probe.execute(f"ATTACH DATABASE ':memory:' AS {alias}")
            probe.execute(f"CREATE TABLE {alias}.{table} ({', '.join(columns)})")  # noqa: S608
        probe.execute(f"CREATE TABLE {table} ({', '.join(columns)})")  # noqa: S608
        traced.clear()
        cc._sorted_bulk_load(probe, table, aliases)
        legacy_sql = [s for s in traced if s.startswith("INSERT")]
        assert len(legacy_sql) == 1
        item = next(
            i for i in _statements(units[stage_id]) if i["operation"] == "sorted_bulk_load.insert"
        )
        assert item["runtime_sql_sha256"] == sha(legacy_sql[0]), stage_id
        probe.close()
    # S13: the successor's own builder, reconstructed.
    connection = r19.readonly(estate.catalog)
    try:
        columns = cc._columns(connection, "census_accession_observations")
    finally:
        connection.close()
    projection = ", ".join(columns)
    parts = [
        f"SELECT {projection}, {ordinal} AS chunk_ordinal, 0 AS priority "  # noqa: S608
        f"FROM {alias}.census_accession_observations"
        for ordinal, alias in enumerate(aliases)
    ]
    parts.append(
        f"SELECT {projection}, 2147483647 AS chunk_ordinal, 1 AS priority "  # noqa: S608
        f"FROM main.{cm.L2_CORRECTIONS_TABLE}"
    )
    expected = (
        f"INSERT OR IGNORE INTO census_accession_observations ({projection}) "  # noqa: S608
        f"SELECT {projection} FROM ({' UNION ALL '.join(parts)}) "
        "ORDER BY accession_observation_id, priority, chunk_ordinal"
    )
    s13 = next(
        i
        for i in _statements(units["S13"])
        if i["operation"] == "load_accession_observations.insert"
    )
    assert s13["runtime_sql_sha256"] == sha(expected)
    # A changed builder context moves the runtime identity: three intermediates, not two.
    wider = r19.prepare(tmp_path / "wider", legacy=False, members=18, shards=1)
    assert len(wider.schedule.groups) == 3
    cm.run_successor_multipass_final(r19.production_request(wider, stop_after="S3"))
    wide = next(
        i for i in _statements(_units(wider)["S3"]) if i["operation"] == "sorted_bulk_load.insert"
    )
    narrow = next(
        i for i in _statements(units["S3"]) if i["operation"] == "sorted_bulk_load.insert"
    )
    assert wide["runtime_sql_sha256"] != narrow["runtime_sql_sha256"]
    assert wide["descriptor_identity"] == narrow["descriptor_identity"]


class _Recording(sqlite3.Connection):
    """A sqlite3 boundary double: records the exact SQL handed to ``execute``/``executemany``
    and the progress-handler installs around them, then performs the real call."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.database = str(args[0]) if args else str(kwargs.get("database", ""))
        self.seen: list[tuple[str, str, int]] = []
        self.handlers: list[tuple[str, int]] = []
        _RECORDED.append(self)

    def execute(self, sql: str, parameters: Any = ()) -> sqlite3.Cursor:  # type: ignore[override]
        self.seen.append(("execute", sql, _journal_bytes_on_disk()))
        return super().execute(sql, parameters)

    def executemany(self, sql: str, parameters: Any) -> sqlite3.Cursor:  # type: ignore[override]
        self.seen.append(("executemany", sql, _journal_bytes_on_disk()))
        return super().executemany(sql, parameters)

    def set_progress_handler(self, handler: Any, n: int) -> None:  # type: ignore[override]
        self.handlers.append(("installed" if handler is not None else "removed", n))
        super().set_progress_handler(handler, n)


_JOURNAL_DIRECTORY: list[Path] = []
_RECORDED: list[_Recording] = []


def _journal_bytes_on_disk() -> int:
    if not _JOURNAL_DIRECTORY:
        return -1
    return sum(p.stat().st_size for p in _JOURNAL_DIRECTORY[0].glob("statement-*.jsonl"))


def boundary_world(
    tmp_path: Path, stop_after: str = "S11"
) -> tuple[r19.SuccessorWorld, cm._StageContext, cm.L2Stage, list[cm.AppliedUnit]]:
    """A committed world, its context and the next stage -- for driving the runner directly."""
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after=stop_after))
    ctx = cm._resolve_successor_context(r19.production_request(estate), _mint())
    units = [cm.AppliedUnit.from_row(r) for r in r19.applied_units(estate.catalog)]
    stage = ctx.stages[len(units)]
    return estate, ctx, stage, units


def recording_connection(catalog: Path) -> _Recording:
    connection = sqlite3.connect(catalog, isolation_level=None, factory=_Recording)
    connection.row_factory = sqlite3.Row
    return connection


def test_b09_the_sqlite_boundary_hash_equals_the_journaled_runtime_sql_and_start_precedes_it(
    tmp_path: Path,
) -> None:
    """Owner ruling C2-R5: the boundary double, not another copy of the builder."""
    estate, ctx, stage, units = boundary_world(tmp_path, "S11")
    assert stage.stage_id == "S12"
    instr = cm._stage_instrumentation_for(ctx, stage, units)
    _JOURNAL_DIRECTORY[:] = [instr.attempt_directory]
    connection = recording_connection(estate.catalog)
    try:
        connection.execute("BEGIN IMMEDIATE")
        instr.begin_world_transaction(connection)
        connection.seen.clear()
        rows = instr.execute(
            connection,
            cm._SQL_S12_ORPHANED_WINNERS,
            (),
            operation="corrections.orphaned_winners",
            kind="fetchall",
        )
        connection.execute("ROLLBACK")
    finally:
        connection.close()
    assert isinstance(rows, list) and int(rows[0]["n"]) == 0
    material = [
        item
        for item in connection.seen
        if not item[1].startswith("PRAGMA") and item[1] != "ROLLBACK"
    ]
    assert len(material) == 1
    kind, observed_sql, journal_bytes_before_execute = material[0]
    assert kind == "execute"
    entry = instr.executions[-1].record
    assert entry["runtime_sql_sha256"] == hashlib.sha256(observed_sql.encode("utf-8")).hexdigest()
    # START was on disk (appended and fsynced) before sqlite3 saw the statement.
    assert journal_bytes_before_execute > 0
    journal = instr.attempt_directory / str(Path(str(entry["journal_relative_path"])).name)
    reading = wc.read_statement_journal(journal)
    assert reading.status == wc.JOURNAL_SEALED_SUCCESS
    assert reading.events[0]["event_kind"] == wc.EVENT_STATEMENT_START
    assert reading.events[0]["runtime_sql_sha256"] == entry["runtime_sql_sha256"]
    assert (reading.sha256, reading.byte_length) == (
        entry["journal_sha256"],
        entry["journal_byte_length"],
    )
    assert connection.handlers[-2:] == [("installed", 1000), ("removed", 0)]


def test_b10_no_material_statement_bypasses_the_journals_in_any_stage_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every ``execute`` a stage transaction issues on the world is a journaled material
    statement, a bounded control pass-through or a control statement -- counted at the Python
    boundary (a SQLite trace reports an upsert once per conflicting row and is not it)."""
    estate = r19.prepare(tmp_path, legacy=False)
    original_connect = sqlite3.connect

    def recording_connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        kwargs.setdefault("factory", _Recording)
        return original_connect(*args, **kwargs)

    _RECORDED.clear()
    monkeypatch.setattr(sqlite3, "connect", recording_connect)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S17C"))
    monkeypatch.undo()
    control_prefixes = (
        "PRAGMA",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "ATTACH DATABASE",
        "DETACH DATABASE",
        "CREATE TABLE",
        "DROP INDEX main.",
        "INSERT INTO main.m3_l2_applied_units",
        "INSERT INTO main.m3_l2_cross_store_bindings",
        "INSERT INTO main.m3_l2_deferred_indexes",
        "INSERT INTO main.m3_l2_stage_plan",
        "SELECT * FROM main.m3_l2_applied_units",
        "SELECT * FROM main.m3_l2_stage_plan",
        "SELECT * FROM main.m3_l2_cross_store_bindings",
        "SELECT ordinal, name, table_name, create_sql",
        "SELECT name FROM main.sqlite_master",
        "SELECT sql, tbl_name FROM main.sqlite_master",
        "SELECT name, sql, tbl_name FROM sqlite_master",
        "SELECT parser_state FROM census_plan_sources",
        "SELECT contract, successor_run_id",
        "SELECT 1",
    )
    catalog = str(estate.catalog)
    windows: list[list[str]] = []
    for connection in _RECORDED:
        if connection.database not in {catalog, str(estate.catalog.resolve())}:
            continue
        current: list[str] | None = None
        for _kind, sql, _bytes in connection.seen:
            if sql == "BEGIN IMMEDIATE":
                current = []
            elif sql == "COMMIT" and current is not None:
                windows.append(current)
                current = None
            elif current is not None:
                current.append(sql)
    units = [cm.AppliedUnit.from_row(row) for row in r19.applied_units(estate.catalog)]
    assert len(windows) == len(units) - 1  # S0 commits inside the initialization attempt
    for window, unit in zip(windows, units[1:], strict=True):
        material = [s for s in window if not s.strip().startswith(control_prefixes)]
        journaled = [
            item
            for item in _statements(unit)
            if item["database_role"] == "WORKING_CATALOG"
            and item["sql_identity_mode"] != "CALLABLE_NON_SQL"
        ]
        bounded = sum(
            int(value)
            for value in unit.statement_execution_set["bounded_control_executions"].values()  # type: ignore[index, union-attr]
        )
        assert len(material) == len(journaled) + bounded, (unit.stage_id, material)
        for item in journaled:
            assert len(str(item["runtime_sql_sha256"])) == 64
    by_stage = {u.stage_id: len(_statements(u)) for u in units}
    assert by_stage["S0"] == 0 and by_stage["S1"] == 0
    assert all(count >= 1 for stage_id, count in by_stage.items() if stage_id not in {"S0", "S1"})


def test_b11_an_unregistered_or_misdeclared_statement_is_refused_before_sqlite_sees_it(
    tmp_path: Path,
) -> None:
    estate, ctx, stage, units = boundary_world(tmp_path, "S11")
    instr = cm._stage_instrumentation_for(ctx, stage, units)
    connection = recording_connection(estate.catalog)
    try:
        connection.execute("BEGIN IMMEDIATE")
        instr.begin_world_transaction(connection)
        connection.seen.clear()
        with pytest.raises(cm.ChunkMultipassError, match="not a registered material operation"):
            instr.execute(connection, "SELECT 1", (), operation="nope", kind="fetchall")
        with pytest.raises(cm.ChunkMultipassError, match="executed as 'execute'"):
            instr.execute(
                connection,
                cm._SQL_S12_SUMMARY,
                (),
                operation="corrections.summary",
                kind="execute",
            )
        # A static statement whose text moved refuses before execution, journaled.
        with pytest.raises(cm.ChunkMultipassError, match="refused before sqlite3 saw it"):
            instr.execute(
                connection,
                cm._SQL_S12_SUMMARY + " ",
                (),
                operation="corrections.summary",
                kind="fetchall",
            )
        # The proxy refuses an unregistered statement and passes the bounded control prefix.
        proxy = instr.proxy(connection)
        with pytest.raises(cm.ChunkMultipassError, match="no registered operation"):
            proxy.execute("SELECT 2")
        connection.execute("ROLLBACK")
    finally:
        connection.close()
    assert not [s for s in connection.seen if not s[1].startswith("PRAGMA") and s[1] != "ROLLBACK"]
    assert instr.executions == []
    # The refused static statement left one SEALED failure journal: START (refused), ERROR.
    journals = sorted(instr.attempt_directory.glob("statement-*.jsonl"))
    assert len(journals) == 1
    reading = wc.read_statement_journal(journals[0])
    assert reading.status == wc.JOURNAL_SEALED_FAILURE
    assert [e["event_kind"] for e in reading.events] == [
        wc.EVENT_STATEMENT_START,
        wc.EVENT_STATEMENT_ERROR,
    ]
    assert "refused before sqlite3 saw it" in str(reading.events[0]["refused"])
    assert reading.events[1]["refused_before_execution"] is True


def test_b12_the_stage_rows_helper_stays_outside_instrumentation_on_the_legacy_route(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    assert estate.legacy is not None
    # The successor never reaches _stage_rows: no registry descriptor names it, and the
    # legacy staging function is untouched byte for byte relative to its own pinned digest.
    registry = cm.successor_statement_registry(cm.SUCCESSOR_ROUTE_PRODUCTION, 10)
    assert not [i for i in registry if "stage_rows" in str(i["source_callable"])]
    assert not [i for i in registry if "_first_witness_corrections" in str(i["source_callable"])]
    assert "statement_runner" not in inspect.getsource(cc._first_witness_corrections)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached and outcome.final_receipt is not None
    assert r19.counters(estate.legacy["final"].as_record()) == r19.counters(outcome.final_receipt)


def test_b13_a_helper_that_bypasses_the_runner_fails_exact_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A consolidation helper executing its SQL directly leaves no sealed journal for a required
    descriptor: the stage refuses before its applied unit, and nothing is committed."""
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    original = cc._sorted_bulk_load

    def bypassing(
        connection: sqlite3.Connection, table: str, aliases: Any, *, statement_runner: Any = None
    ) -> None:
        original(connection, table, aliases)  # the legacy None runner: direct execution

    monkeypatch.setattr(cm, "_sorted_bulk_load", bypassing)
    with pytest.raises(cm.ChunkMultipassError, match="coverage: S3/sorted_bulk_load.insert has 0"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    assert r19.count(estate.catalog, "census_parsed_records") == 0
    assert not [p for p in r19.receipt_files(estate.receipt_root) if "S3" in p.name]
    monkeypatch.undo()
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    assert outcome.completed_stage_ids[-1] == "S3"
