"""D151-C13: the set-based first-witness correction -- exact parity, then scaling (C8-M2).

The old correction (:func:`chunk_consolidation._first_witness_corrections`) walks the contested
accessions in Python and issues several statements per identity and per rival. The new one
(:func:`chunk_multipass.stage_first_witness_corrections`) ranks every input's canonical rows with
one window function and stages both halves of the correction with one ``INSERT ... SELECT`` each,
reaching the accepted identity and rendering functions as deterministic SQLite user functions.

Semantics first: the two implementations are run over the SAME loaded world and their staged
rowsets are compared exactly, over every hostile source shape and partition; then a scratch world
merged through the new path is compared with the single-pass world table by table (O9); then the
user functions are held to the accepted Python rendering over a hostile value corpus. Only then is
scaling measured: the old path's statement count grows with the contested population and the new
path's does not.
"""

from __future__ import annotations

import ast
import inspect
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c1_equivalence as eq  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3.compact_evidence import (  # noqa: E402
    GOVERNED_ACCESSION_FIELDS,
    materialized_fields,
    reconstructed_observations,
)
from disclosure_drift.m3.offline_parse import write_containment  # noqa: E402
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    WORKING_CATALOG_FILENAME,
    WorkingCatalog,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.sec.census import CensusCatalog, _stable_id  # noqa: E402
from disclosure_drift.sec.census import _json as _stable_json  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# The direct staging oracle
# ==========================================================================
def _loaded_world(
    directory: Path, database: Path, inputs: Any
) -> tuple[WorkingCatalog, list[str], Any]:
    """A scratch world with every input attached and every table but the observations loaded.

    Exactly the state both correction implementations run in: the same accepted primitives, in
    the same order, on the same connection. The caller runs the correction and closes the world.
    """
    world = WorkingCatalog(database, directory)
    world.__enter__()
    connection = world.connection
    contract = inputs[0].receipt.execution_contract
    aliases = list(cc._attach_all(connection, [item.catalog_path for item in inputs], "k"))
    indexes = cc._deferrable_indexes(connection)
    for name, _sql in indexes:
        connection.execute(f"DROP INDEX IF EXISTS {name}")
    connection.execute("BEGIN")
    with write_containment(connection):
        reduced = cc._reduced_parser_run(connection, aliases, contract=contract)
        for table in cc._LOAD_ORDER:
            if table == "census_accession_observations":
                continue
            if cc._MERGE_STRATEGY[table] == "keyed_first_last":
                cc._keyed_first_last_load(connection, table, aliases)
            else:
                cc._sorted_bulk_load(connection, table, aliases)
        cc._apply_duplicate_identities(connection, reduced)
    return world, aliases, (reduced, indexes)


def _staged_rows(connection: sqlite3.Connection) -> list[tuple[str, ...]]:
    return sorted(
        tuple(str(value) for value in row)
        for row in connection.execute(f"SELECT * FROM temp.{cc.CORRECTIONS_TABLE}")  # noqa: S608
    )


def _drop_staging(connection: sqlite3.Connection) -> None:
    connection.execute(f"DROP TABLE IF EXISTS temp.{cc.CORRECTIONS_TABLE}")
    connection.execute(f"DROP TABLE IF EXISTS temp.{cm.WITNESS_RANK_TABLE}")


def _inputs_for(tmp_path: Path, database: Path, tree: DataTree, *, size: int, label: str) -> Any:
    plan = c1.build_plan(tree, database, chunk_members=size)
    run = c13.execute_in_process(plan, tmp_path / label, database, tree)
    return cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"]), run


@pytest.mark.parametrize(
    ("label", "shape", "strict"), eq.SOURCES, ids=[item[0] for item in eq.SOURCES]
)
@pytest.mark.parametrize("size", [1, 2])
def test_p01_the_two_implementations_stage_identical_rowsets(
    tmp_path: Path, label: str, shape: dict[str, Any], strict: bool, size: int
) -> None:
    """Old and new, over the same loaded world: same contested count, same rows, same values."""
    database, tree = c1.build_world(tmp_path, **shape)
    inputs, _run = _inputs_for(tmp_path, database, tree, size=size, label=f"{label}-{size}")
    world, aliases, _ = _loaded_world(tmp_path / "scratch", database, inputs)
    try:
        connection = world.connection
        old = cc._first_witness_corrections(connection, aliases)
        old_rows = _staged_rows(connection)
        _drop_staging(connection)
        new = cm.stage_first_witness_corrections(connection, aliases)
        new_rows = _staged_rows(connection)
        assert new == old
        assert new_rows == old_rows
        assert len(new_rows) == new[1]
        connection.execute("ROLLBACK")
    finally:
        world.__exit__(None, None, None)
    assert strict in (True, False)


def test_p02_the_hard_case_really_arose_in_the_oracle(tmp_path: Path) -> None:
    """The parity oracle is only a proof if the contested population is non-empty somewhere."""
    database, tree = c1.build_world(
        tmp_path, members=8, filings=2, share_every=2, junk=3, unknown=4
    )
    inputs, _run = _inputs_for(tmp_path, database, tree, size=1, label="hard")
    world, aliases, _ = _loaded_world(tmp_path / "scratch", database, inputs)
    try:
        connection = world.connection
        contested, staged = cm.stage_first_witness_corrections(connection, aliases)
        assert contested == 1 and staged > 0
        rows = _staged_rows(connection)
        rivals = {row[3] for row in rows}
        assert len(rivals) == 4  # the winner's back-fill plus three rivals
        connection.execute("ROLLBACK")
    finally:
        world.__exit__(None, None, None)


def test_o8_a_one_chunk_ordinary_plan_needs_no_correction(tmp_path: Path) -> None:
    database, tree = c1.build_world(tmp_path, members=4, filings=2, share_every=2)
    plan = c1.build_plan(tree, database, chunk_members=10_000)
    assert plan.chunk_count == 1
    run = c13.execute_in_process(plan, tmp_path / "one", database, tree)
    result = cc.consolidate_chunks(
        plan=plan,
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final",
        run_id="o8",
    )
    assert result.receipt.first_witness_accessions_corrected == 0
    assert result.receipt.first_witness_rows_staged == 0
    assert result.receipt.evidence_delta == 0
    inputs = cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"])
    world, aliases, _ = _loaded_world(tmp_path / "scratch", database, inputs)
    try:
        assert cm.stage_first_witness_corrections(world.connection, aliases) == (0, 0)
        assert _staged_rows(world.connection) == []
        world.connection.execute("ROLLBACK")
    finally:
        world.__exit__(None, None, None)


def test_o9_the_merge_core_over_one_group_of_every_input_equals_the_single_pass_world(
    tmp_path: Path,
) -> None:
    """O9: all nine chunks as ONE group through the new core, against consolidate_chunks."""
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=3, share_every=2)
    inputs, run = _inputs_for(tmp_path, database, tree, size=1, label="nine")
    assert len(inputs) == 9
    single = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final",
        run_id="o9-single",
    )
    world, aliases, (reduced, indexes) = _loaded_world(tmp_path / "core", database, inputs)
    try:
        connection = world.connection
        corrected, staged = cm.stage_first_witness_corrections(connection, aliases)
        with write_containment(connection):
            cc._load_accession_observations(connection, aliases)
            CensusCatalog._candidate_edges(connection, c1.OBSERVATION, kind="company_name")
            CensusCatalog._candidate_edges(connection, c1.OBSERVATION, kind="ticker")
            CensusCatalog._mark_accession_conflicts(connection)
            connection.execute(
                "UPDATE census_plan_sources SET parser_state = ? WHERE source_instance_id = ?",
                (reduced.parser_state, c1.INSTANCE),
            )
        connection.execute("COMMIT")
        for _name, sql in indexes:
            connection.execute(sql)
        cc._detach_all(connection, aliases)
    finally:
        world.__exit__(None, None, None)
    assert (corrected, staged) == (
        single.receipt.first_witness_accessions_corrected,
        single.receipt.first_witness_rows_staged,
    )
    with connect(tmp_path / "core" / WORKING_CATALOG_FILENAME, writer=False) as core:
        core_digests = dict(cc.world_logical_digest(core))
    with connect(single.world_directory / WORKING_CATALOG_FILENAME, writer=False) as reference:
        single_digests = dict(cc.world_logical_digest(reference))
    assert core_digests == single_digests


def test_o10_reapplication_is_refused_at_staging_and_idempotent_at_load(tmp_path: Path) -> None:
    database, tree = c1.build_world(tmp_path, members=8, filings=2, share_every=2)
    inputs, _run = _inputs_for(tmp_path, database, tree, size=1, label="twice")
    world, aliases, _ = _loaded_world(tmp_path / "scratch", database, inputs)
    try:
        connection = world.connection
        cm.stage_first_witness_corrections(connection, aliases)
        with pytest.raises(cm.ChunkMultipassError, match="already been staged"):
            cm.stage_first_witness_corrections(connection, aliases)
        with write_containment(connection):
            cc._load_accession_observations(connection, aliases)
        once = sorted(
            tuple(str(v) for v in row)
            for row in connection.execute("SELECT * FROM census_accession_observations")
        )
        with write_containment(connection):
            cc._load_accession_observations(connection, aliases)
        twice = sorted(
            tuple(str(v) for v in row)
            for row in connection.execute("SELECT * FROM census_accession_observations")
        )
        assert once == twice
        connection.execute("ROLLBACK")
    finally:
        world.__exit__(None, None, None)


# ==========================================================================
# The user functions are the accepted rendering, exactly
# ==========================================================================
HOSTILE_VALUES: tuple[object, ...] = (
    'quote"back\\slash',
    "new" + chr(10) + "line" + chr(9) + "tab" + chr(13) + "return" + chr(0) + "nul" + chr(31),
    "caf" + chr(233) + " " + chr(0x1F600) + " " + chr(0x2028),
    "",
    " 10-K ",
    None,
    True,
    False,
    0,
    1,
    -5,
    1.5,
    1e16,
    1e-7,
    {"b": 1, "a": [1, 2, {"z": None, "y": "x"}]},
    [],
    ["a", 1, None, 2.5],
)


@pytest.mark.parametrize("value", HOSTILE_VALUES, ids=[repr(v)[:24] for v in HOSTILE_VALUES])
def test_p03_the_rival_rendering_is_the_accepted_one(value: object) -> None:
    payload: dict[str, object] = dict.fromkeys(GOVERNED_ACCESSION_FIELDS, value)
    payload["accessionNumber"] = "0000000001-24-000001"
    rendered = json.loads(cm._rival_fields_json(json.dumps(payload)))
    expected = {
        field: _stable_json(payload[field])
        for field in materialized_fields(payload, first_witness=False)
    }
    assert rendered == expected
    assert set(rendered) == set(GOVERNED_ACCESSION_FIELDS)
    # And through SQLite: json_each explodes the object into the exact rendered text.
    connection = sqlite3.connect(":memory:")
    try:
        cm._register_correction_functions(connection)
        rows = connection.execute(
            f"SELECT key, value FROM json_each({cm._FUNCTION_RIVAL_FIELDS}(?))",  # noqa: S608
            (json.dumps(payload),),
        ).fetchall()
    finally:
        connection.close()
    assert dict(rows) == expected


def test_p03_the_reconstruction_rendering_is_the_accepted_one() -> None:
    columns: dict[str, object] = {
        "acceptance_datetime_sec_raw": "2024-02-01T10:00:00.000Z",
        "registrant_cik_padded": "0000000001",
        "filing_date_sec": "2024-02-01",
        "form_type": 'x"y',
        "primary_document_name": None,
        "report_date": "caf" + chr(233),
    }
    rendered = json.loads(
        cm._reconstructed_fields_json(
            columns["acceptance_datetime_sec_raw"],
            columns["registrant_cik_padded"],
            columns["filing_date_sec"],
            columns["form_type"],
            columns["primary_document_name"],
            columns["report_date"],
        )
    )
    expected = {field: _stable_json(value) for field, value in reconstructed_observations(columns)}
    assert rendered == expected
    assert "primaryDocument" not in rendered and len(rendered) == 5
    connection = sqlite3.connect(":memory:")
    try:
        cm._register_correction_functions(connection)
        rows = connection.execute(
            "SELECT key, value FROM "  # noqa: S608
            f"json_each({cm._FUNCTION_RECONSTRUCTED_FIELDS}(?, ?, ?, ?, ?, ?))",
            tuple(columns.values()),
        ).fetchall()
        identity = connection.execute(
            f"SELECT {cm._FUNCTION_STABLE_ID}('accession-observation', ?, ?, ?, ?)",
            ("a", "b", "c", "d"),
        ).fetchone()[0]
    finally:
        connection.close()
    assert dict(rows) == expected
    assert identity == _stable_id("accession-observation", "a", "b", "c", "d")


def test_p03_a_lone_surrogate_is_refused_exactly_as_the_accepted_writer_refuses_it() -> None:
    lone = chr(0xD800)
    payload = {"form": lone, "accessionNumber": "x"}
    with pytest.raises(UnicodeEncodeError):
        cm._rival_fields_json(json.dumps(payload))
    connection = sqlite3.connect(":memory:")
    try:
        with pytest.raises(UnicodeEncodeError):
            connection.execute("SELECT ?", (lone,)).fetchone()
    finally:
        connection.close()


# ==========================================================================
# No per-accession Python loop on the multipass path
# ==========================================================================
def test_p04_the_staging_function_issues_no_statement_per_row() -> None:
    source = inspect.getsource(cm.stage_first_witness_corrections)
    tree = ast.parse(source)
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    loops = [node for node in ast.walk(function) if isinstance(node, ast.For | ast.While)]
    assert loops == []
    assert "executemany" not in source
    # One fetchall, and it is the refusal check for a repeated staging -- never a row walk.
    assert source.count("fetchall") == 1
    assert source.count("INSERT INTO temp.") == 2
    assert "ROW_NUMBER() OVER (PARTITION BY accession_plain ORDER BY chunk_ordinal)" in source
    module = Path(cm.__file__).read_text(encoding="utf-8")
    imported = {
        alias.name
        for node in ast.walk(ast.parse(module))
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "_first_witness_corrections" not in imported
    assert "_stage_rows" not in imported
    assert "cc._first_witness_corrections" not in module
    assert "chunk_consolidation._first_witness_corrections" not in module
    for body in ("merge_group_body", "finalize_multipass_body"):
        text = inspect.getsource(getattr(cm, body))
        assert "stage_first_witness_corrections(connection, aliases)" in text
        assert "for row in" not in text
    # The old loop still exists, untouched, for the single-pass consolidator.
    old = inspect.getsource(cc._first_witness_corrections)
    assert "for row in contested" in old and "for rival in rivals" in old


class _Trace:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def __call__(self, statement: str) -> None:
        self.statements.append(statement)


def _contested_members(contested: int, *, witnesses: int) -> list[tuple[str, dict[str, Any]]]:
    """``witnesses`` registrants that each file the SAME ``contested`` accessions, plus one own."""
    members = []
    for cik in range(1, witnesses + 1):
        numbers = [
            f"{cik:010d}-24-000000",
            *[f"9999999999-24-{index:06d}" for index in range(contested)],
        ]
        recent = {
            "accessionNumber": numbers,
            "filingDate": ["2024-02-01"] * len(numbers),
            "form": ["10-K"] * len(numbers),
            "reportDate": ["2023-12-31"] * len(numbers),
            "primaryDocument": [f"d{cik}.htm"] * len(numbers),
        }
        document = {
            "cik": str(cik),
            "name": f"CONTESTED {cik}",
            "sic": "2834",
            "fiscalYearEnd": "1231",
            "tickers": [f"CT{cik}"],
            "exchanges": ["Nasdaq"],
            "formerNames": [],
            "filings": {"recent": recent, "files": []},
        }
        members.append((f"CIK{cik:010d}.json", document))
    return members


def _measure(tmp_path: Path, *, contested: int, witnesses: int) -> dict[str, Any]:
    from test_d151_c13_multipass_semantics import build_custom_world

    database, tree = build_custom_world(
        tmp_path / f"c{contested}", _contested_members(contested, witnesses=witnesses)
    )
    plan = c1.build_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, tmp_path / f"run{contested}", database, tree)
    inputs = cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"])
    record: dict[str, Any] = {"contested": contested, "witnesses": witnesses}
    implementations = (
        ("old", cc._first_witness_corrections),
        ("new", cm.stage_first_witness_corrections),
    )
    for label, function in implementations:
        world, aliases, _ = _loaded_world(tmp_path / f"world-{label}-{contested}", database, inputs)
        try:
            connection = world.connection
            trace = _Trace()
            connection.set_trace_callback(trace)
            started = time.perf_counter()
            result = function(connection, aliases)
            wall = time.perf_counter() - started
            connection.set_trace_callback(None)
            rows = _staged_rows(connection)
            temp_pages = int(connection.execute("PRAGMA temp.page_count").fetchone()[0])
            page_size = int(connection.execute("PRAGMA temp.page_size").fetchone()[0])
            connection.execute("ROLLBACK")
        finally:
            world.__exit__(None, None, None)
        record[label] = {
            "result": list(result),
            "rows": len(rows),
            "digest": _stable_id(*[":".join(row) for row in rows]),
            "wall_seconds": round(wall, 4),
            "statements": len(trace.statements),
            "temp_bytes": temp_pages * page_size,
        }
    return record


def test_p05_the_new_path_scales_by_statement_count_and_stays_exact(tmp_path: Path) -> None:
    """Three contested populations: exact results at every scale; constant statement count."""
    records = [_measure(tmp_path, contested=count, witnesses=3) for count in (40, 400, 2000)]
    for record in records:
        assert record["old"]["result"] == record["new"]["result"]
        assert record["old"]["digest"] == record["new"]["digest"]
        assert record["old"]["rows"] == record["new"]["rows"]
        assert record["new"]["result"][0] == record["contested"]
        # Old: at least one statement per contested identity and per rival. New: constant.
        assert record["old"]["statements"] >= record["contested"] * 4
    new_counts = {record["new"]["statements"] for record in records}
    assert len(new_counts) == 1
    assert next(iter(new_counts)) <= 12
    assert records[-1]["old"]["statements"] > records[0]["old"]["statements"] * 10
    (tmp_path / "set_based_benchmark.json").write_text(json.dumps(records, indent=2))
    print("\nSET_BASED_BENCHMARK " + json.dumps(records))


def test_p06_a_missing_payload_or_canonical_row_is_refused_never_skipped(tmp_path: Path) -> None:
    """The set-based join could silently drop a rival with no payload; the predicate refuses."""
    database, tree = c1.build_world(tmp_path, members=8, filings=2, share_every=2)
    inputs, _run = _inputs_for(tmp_path, database, tree, size=1, label="orphans")
    world, aliases, _ = _loaded_world(tmp_path / "scratch", database, inputs)
    try:
        connection = world.connection
        union = cc._union_all(
            aliases, "census_accessions", "accession_plain, parsed_record_id", extra=" AS o"
        )
        ranked = connection.execute(
            "SELECT accession_plain, parsed_record_id, "  # noqa: S608
            "ROW_NUMBER() OVER (PARTITION BY accession_plain ORDER BY o) AS rn "
            f"FROM ({union})"
        ).fetchall()
        rival = next(row for row in ranked if int(row["rn"]) > 1)
        connection.execute(
            "DELETE FROM main.census_parsed_records WHERE parsed_record_id = ?",
            (str(rival["parsed_record_id"]),),
        )
        with pytest.raises(cm.ChunkMultipassError, match="parsed record is absent"):
            cm.stage_first_witness_corrections(connection, aliases)
        connection.execute("ROLLBACK")
    finally:
        world.__exit__(None, None, None)
    world, aliases, _ = _loaded_world(tmp_path / "scratch-winner", database, inputs)
    try:
        connection = world.connection
        connection.execute(
            "DELETE FROM main.census_accessions WHERE accession_plain = ?",
            (str(rival["accession_plain"]),),
        )
        with pytest.raises(cm.ChunkMultipassError, match="no loaded canonical row"):
            cm.stage_first_witness_corrections(connection, aliases)
        connection.execute("ROLLBACK")
    finally:
        world.__exit__(None, None, None)
