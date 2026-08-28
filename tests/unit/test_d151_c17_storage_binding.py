"""D151-C17: the D151-C16 MINOR corrections, proved behaviourally.

**C16-MINOR-1 -- the level-2 transient allowance is its own term.** C1701-C1707 hold the storage
model to two independent transient quantities: each refuses on its own, neither stands in for the
other, each step records the level it was charged at, and the sealed storage identity moves when
either moves. C1706 holds the level-2 term's own definition to the COMPLETE measurement target --
the free-space drawdown high-water on the bound volume, not a table enumeration and not a
traversal of the temporary root, which D140-R7 already established cannot see an in-flight spill.

**C16-MINOR-2 -- SQLite's spill is bound to the charged filesystem.** C1708-C1716 hold every
world-creating path to a measured volume-identity comparison through the accepted D137-R8
provider, before any world, attempt directory or database exists, in the orchestrator and again
in each merge child, with no request field, environment value or configuration key able to forge
it.

**C16-MINOR-3 -- the three counter refusal branches are covered.** C1717-C1719 reach each branch
of :func:`~disclosure_drift.m3.chunk_multipass._plan_first_witness_counters` by its intended
route and require its own message, not an unrelated integrity error.
"""

from __future__ import annotations

import ast
import inspect
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c13_intermediates as c13i  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3.chunk_evidence import write_once_json  # noqa: E402
from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME  # noqa: E402

OTHER_VOLUME = "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"
MISMATCH = "must be counted by the same capacity model"
#: A measured-shaped binding for storage plans built without a temporary root -- D151-C19 R4.
BINDING = ct.SqliteTempBinding.from_record(c13.INERT_BINDING_RECORD)
SHAPE: dict[str, Any] = {"filings": 2, "share_every": 3, "junk": 4, "unknown": 5, "duplicate": True}


@pytest.fixture(autouse=True)
def _pinned(tmp_path: Path) -> Any:
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


def _open(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    c13.open_synthetic_multipass(monkeypatch, temp_root=tmp_path / "sqlite-temp")
    monkeypatch.setattr(cm, "_CHILD_BOOTSTRAP", c13i.multipass_child_bootstrap(tmp_path / "repo"))


def _requirements(**changes: Any) -> ct.MultipassStorageRequirements:
    base: dict[str, Any] = {
        "internal_reserve_bytes": 100,
        "level_one_peak_ratio": 1.5,
        "level_two_peak_ratio": 2.0,
        "level_one_transient_bytes": 7,
        "level_two_transient_bytes": 4096,
    }
    base.update(changes)
    return ct.MultipassStorageRequirements(**base)


def _two_volumes(monkeypatch: pytest.MonkeyPatch, temp_root: Path) -> None:
    """A provider that reports a DIFFERENT volume for the temporary root than for the world."""
    resolved = Path(temp_root).resolve()

    def identify(path: Path) -> ewr.VolumeIdentity:
        here = Path(path).resolve()
        different = here == resolved or resolved in here.parents
        return ewr.VolumeIdentity(
            volume_uuid=OTHER_VOLUME if different else c13.SYNTHETIC_MERGE_VOLUME,
            mount_point=Path("/"),
            filesystem_type="apfs",
            device_identifier="disk-synthetic",
        )

    monkeypatch.setattr(ewr, "macos_volume_identity", identify)


# ==========================================================================
# C1701-C1707: the two transient allowances are independent -- C16-MINOR-1
# ==========================================================================
def test_c1701_the_level_two_step_states_and_charges_its_own_transient_term() -> None:
    requirements = _requirements()
    plan = ct.plan_multipass_storage(
        plan_digest="p",
        merge_schedule_digest="s",
        groups=[("group-0000", ["chunk-0000"]), ("group-0001", ["chunk-0001"])],
        chunk_bytes_by_id={"chunk-0000": 1000, "chunk-0001": 2000},
        seed_catalog_bytes=50,
        requirements=requirements,
        sqlite_temp_binding=BINDING,
    )
    by_step = {step.step: step for step in plan.steps}
    assert set(by_step) == {"group-0000", "group-0001", "final"}
    for name in ("group-0000", "group-0001"):
        assert by_step[name].level == ct.MERGE_LEVEL_ONE
        assert by_step[name].transient_bytes == 7
    assert by_step["final"].level == ct.MERGE_LEVEL_TWO
    assert by_step["final"].transient_bytes == 4096
    # C1704: the final step used the level-2 number and not the level-1 number.
    assert by_step["final"].transient_bytes != by_step["group-0000"].transient_bytes
    assert by_step["final"].required_free_bytes == (
        by_step["final"].peak_bytes + 100 + requirements.level_two_transient_bytes
    )
    assert "level" in dict(by_step["final"].as_record())


def test_c1702_a_none_level_two_transient_refuses_even_with_level_one_frozen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from disclosure_drift.m3 import chunk_storage as cs

    monkeypatch.setattr(cs, "INTERNAL_RESERVE_BYTES", 1 << 30)
    monkeypatch.setattr(ct, "MULTIPASS_LEVEL_ONE_PEAK_RATIO", 1.0)
    monkeypatch.setattr(ct, "MULTIPASS_LEVEL_TWO_PEAK_RATIO", 1.0)
    monkeypatch.setattr(ct, "MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES", 1 << 20)
    assert ct.MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES is None
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE") as refusal:
        ct.accepted_multipass_storage_requirements()
    message = str(refusal.value)
    assert "MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES" in message
    assert "MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES" not in message


def test_c1703_a_none_level_one_transient_refuses_even_with_level_two_frozen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from disclosure_drift.m3 import chunk_storage as cs

    monkeypatch.setattr(cs, "INTERNAL_RESERVE_BYTES", 1 << 30)
    monkeypatch.setattr(ct, "MULTIPASS_LEVEL_ONE_PEAK_RATIO", 1.0)
    monkeypatch.setattr(ct, "MULTIPASS_LEVEL_TWO_PEAK_RATIO", 1.0)
    monkeypatch.setattr(ct, "MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES", 1 << 20)
    assert ct.MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES is None
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE") as refusal:
        ct.accepted_multipass_storage_requirements()
    message = str(refusal.value)
    assert "MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES" in message
    assert "MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES" not in message


def test_c1707_no_level_falls_back_to_the_other_and_none_defaults_to_zero() -> None:
    requirements = _requirements()
    assert requirements.transient_for(ct.MERGE_LEVEL_ONE) == 7
    assert requirements.transient_for(ct.MERGE_LEVEL_TWO) == 4096
    for level in ("", "final", "level-3", "LEVEL-1", "group-0000", None):
        with pytest.raises(ct.ChunkTieringError, match="charged at exactly one of"):
            requirements.transient_for(level)  # type: ignore[arg-type]
    # A record that carries the superseded generic term is refused, never reinterpreted.
    record = dict(requirements.as_record())
    assert "transient_bytes" not in record
    legacy = {k: v for k, v in record.items() if not k.endswith("transient_bytes")}
    legacy["transient_bytes"] = 7
    with pytest.raises(ct.ChunkTieringError, match="superseded generic"):
        ct.MultipassStorageRequirements.from_record(legacy)
    # A record missing one level's term is refused rather than defaulted to zero.
    for dropped in ("level_one_transient_bytes", "level_two_transient_bytes"):
        partial = {k: v for k, v in record.items() if k != dropped}
        with pytest.raises(ct.ChunkTieringError, match="missing"):
            ct.MultipassStorageRequirements.from_record(partial)
    assert ct.MultipassStorageRequirements.from_record(record) == requirements


def test_c1705_the_storage_identity_moves_with_either_transient_term() -> None:
    def identity(**changes: Any) -> str:
        return ct.plan_multipass_storage(
            plan_digest="p",
            merge_schedule_digest="s",
            groups=[("group-0000", ["chunk-0000"])],
            chunk_bytes_by_id={"chunk-0000": 1000},
            seed_catalog_bytes=50,
            requirements=_requirements(**changes),
            sqlite_temp_binding=BINDING,
        ).identity()

    base = identity()
    assert identity(level_one_transient_bytes=8) != base
    assert identity(level_two_transient_bytes=4097) != base
    assert identity(level_one_transient_bytes=8) != identity(level_two_transient_bytes=8)
    assert identity() == base
    # And a sealed plan cannot be re-read as though the other level's allowance had applied:
    # every step's record names its level, so swapping the two numbers is a different identity.
    swapped = identity(level_one_transient_bytes=4096, level_two_transient_bytes=7)
    assert swapped != base


def test_c1706_the_level_two_term_defines_the_complete_measurement_target() -> None:
    """The definition a future storage-qualification session is bound by."""
    source = Path(ct.__file__).read_text(encoding="utf-8")
    start = source.index("#: The LEVEL-2 transient allowance")
    end = source.index("MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES: Final", start)
    definition = source[start:end]
    # It names the whole coexisting set D151-C16 measured, not the two D151-C15 named.
    for table in (
        "chunk_observation_corrections",
        "chunk_witness_rank",
        "plan_chunk_witnesses",
        "plan_witness_rank",
        "chunk_first_witness",
        "chunk_member_delta",
    ):
        assert table in definition, table
    # It says the named tables are NOT the quantity, and that sorter/workfile space is unnamed.
    assert "sorter" in definition and "workfile" in definition.replace("WORKFILES", "workfiles")
    assert "a sum of estimated table sizes" in definition
    # It states the accepted method, and rules out the two wrong ones.
    assert "FREE-SPACE DRAWDOWN" in definition
    assert "high-water" in definition
    assert "never from a directory walk" in definition
    assert "never from a schema enumeration" in definition
    assert "D140-R7" in definition
    # And it is a distinct term from level 1, which cannot satisfy it.
    assert "never satisfied by :data:`MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES`" in definition


# ==========================================================================
# C1708-C1716: the SQLite temp/world volume binding -- C16-MINOR-2
# ==========================================================================
def test_c1708_the_same_measured_volume_admits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    binding = ct.require_sqlite_temp_binding(charged_path=tmp_path / "not-created-yet")
    assert binding.charged_volume_uuid == binding.temp_volume_uuid == c13.SYNTHETIC_MERGE_VOLUME
    record = dict(binding.as_record())
    assert "mount_point" not in record and str(tmp_path) not in json.dumps(record)
    # C19-R4: the temporary root is identified by device and inode, never by path.
    stat = (tmp_path / "sqlite-temp").stat()
    assert (binding.temp_root_device, binding.temp_root_inode) == (stat.st_dev, stat.st_ino)


def test_c1709_a_mismatched_measured_volume_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    _two_volumes(monkeypatch, tmp_path / "sqlite-temp")
    with pytest.raises(ct.ChunkTieringError, match=MISMATCH) as refusal:
        ct.require_sqlite_temp_binding(charged_path=tmp_path / "world")
    assert OTHER_VOLUME in str(refusal.value)


def test_c1709b_an_absent_unusable_or_disagreeing_temp_root_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    charged = tmp_path / "world"
    monkeypatch.delenv(ewr.SQLITE_TMPDIR_ENV)
    with pytest.raises(ct.ChunkTieringError, match="is not set"):
        ct.require_sqlite_temp_binding(charged_path=charged)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, "   ")
    with pytest.raises(ct.ChunkTieringError, match="is not set"):
        ct.require_sqlite_temp_binding(charged_path=charged)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, "relative/temp")
    with pytest.raises(ct.ChunkTieringError, match="not an absolute path"):
        ct.require_sqlite_temp_binding(charged_path=charged)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(tmp_path / "absent"))
    with pytest.raises(ct.ChunkTieringError, match="does not name an existing directory"):
        ct.require_sqlite_temp_binding(charged_path=charged)
    # A supplied mapping that disagrees with what SQLite will read proves nothing -- D138-R3.
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(tmp_path / "sqlite-temp"))
    with pytest.raises(ct.ChunkTieringError, match="is not the one SQLite will read"):
        ct.require_sqlite_temp_binding(
            charged_path=charged, environ={ewr.SQLITE_TMPDIR_ENV: str(tmp_path)}
        )

    # An identity that cannot be read is refused, never assumed to match.
    def unreadable(path: Path) -> ewr.VolumeIdentity:
        message = "synthetic identity failure"
        raise ewr.ExternalWorkingRootError(message)

    monkeypatch.setattr(ewr, "macos_volume_identity", unreadable)
    with pytest.raises(ct.ChunkTieringError, match="could not be identified"):
        ct.require_sqlite_temp_binding(charged_path=charged)


def test_c1710_c1711_the_refusal_precedes_every_world_and_every_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing is created anywhere: no directory, no attempt, no world, no SQLite file."""
    _open(monkeypatch, tmp_path)
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    _two_volumes(monkeypatch, tmp_path / "sqlite-temp")
    base = run["base"]
    schedule = cm.derive_merge_schedule(run["plan"])
    root = base / "bound"
    root.mkdir()
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    group = schedule.groups[0]
    attempt = root / "intermediates" / group.group_id / "attempt-000"
    world = root / "final"
    before = {str(p.relative_to(base)) for p in base.rglob("*")}

    with pytest.raises(ct.ChunkTieringError, match=MISMATCH):
        cm.run_multipass_f0(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=base / "orchestrated",
            run_id="c1710",
        )
    assert not (base / "orchestrated").exists()

    with pytest.raises(ct.ChunkTieringError, match=MISMATCH):
        cm.merge_group_body(
            c13.group_request(
                run,
                schedule_path=schedule_path,
                group_id=group.group_id,
                attempt=0,
                attempt_directory=attempt,
                database=database,
            )
        )
    assert not attempt.exists() and not (root / "intermediates").exists()

    with pytest.raises(ct.ChunkTieringError, match=MISMATCH):
        cm.finalize_multipass_body(
            c13.final_request(
                run,
                schedule_path=schedule_path,
                intermediates_root=root / "intermediates",
                world_directory=world,
                database=database,
                run_id="c1711",
            )
        )
    assert not world.exists()
    assert {str(p.relative_to(base)) for p in base.rglob("*")} == before
    # No SQLite database was created by any of the three: the chunk catalogs the run already had
    # are untouched, and neither merge root gained one.
    assert not list(root.rglob(WORKING_CATALOG_FILENAME))
    assert not (base / "orchestrated").exists()


@pytest.mark.parametrize(
    "kind",
    [cm.MULTIPASS_REQUEST_KIND_GROUP, cm.MULTIPASS_REQUEST_KIND_FINAL],
    ids=["c1712", "c1713"],
)
def test_c1712_c1713_each_merge_child_rechecks_the_binding_for_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """A REAL child, whose parent said nothing, refuses on its own measurement."""
    _open(monkeypatch, tmp_path)
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    base = run["base"]
    schedule = cm.derive_merge_schedule(run["plan"])
    root = base / "child"
    root.mkdir()
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    group = schedule.groups[0]
    if kind == cm.MULTIPASS_REQUEST_KIND_GROUP:
        target = root / "intermediates" / group.group_id / "attempt-000"
        request = c13.group_request(
            run,
            schedule_path=schedule_path,
            group_id=group.group_id,
            attempt=0,
            attempt_directory=target,
            database=database,
        )
    else:
        partial = c13.merge_in_process(run, database, label="prepared", finalize=False)
        target = partial["multipass_root"] / "final"
        request = c13.final_request(
            run,
            schedule_path=partial["schedule_path"],
            intermediates_root=partial["intermediates_root"],
            world_directory=target,
            database=database,
            run_id="c1712",
        )
    path = root / f"{kind}-request.json"
    path.write_text(json.dumps(dict(request.as_record())), encoding="utf-8")

    # The child's own bootstrap reports a DIFFERENT volume for the temporary root. The parent
    # process is not involved: it neither measured nor asserted anything for this child.
    mismatching = c13i.multipass_child_bootstrap(tmp_path / "repo").replace(
        f"volume_uuid={c13.SYNTHETIC_MERGE_VOLUME!r}",
        f"volume_uuid=({OTHER_VOLUME!r} if 'sqlite-temp' in str(path) "
        f"else {c13.SYNTHETIC_MERGE_VOLUME!r})",
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", mismatching, str(path)], capture_output=True, text=True, check=False
    )
    assert completed.returncode != 0
    assert MISMATCH in completed.stderr, completed.stderr[-2000:]
    assert not target.exists()
    # Positive control: the same child, same request, matching volumes -> it completes.
    ok = subprocess.run(  # noqa: S603
        [sys.executable, "-c", c13i.multipass_child_bootstrap(tmp_path / "repo"), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0, ok.stderr[-3000:]
    assert target.exists()


def test_c1714_c1716_nothing_in_a_request_environment_or_config_can_forge_the_binding() -> None:
    """The guard takes no claim from anyone: it measures, and only measures."""
    source = Path(cm.__file__).read_text(encoding="utf-8")
    tiering = Path(ct.__file__).read_text(encoding="utf-8")
    # No request field, on either request type, can assert anything about volumes.
    for request_type in (cm.GroupMergeRequest, cm.FinalMergeRequest):
        fields = set(inspect.signature(request_type).parameters)
        assert not {
            f for f in fields if "volume" in f or "same_volume" in f or "tmpdir" in f.lower()
        }
    # Production passes the guard exactly two things, and a provider is never one of them.
    calls = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "require_sqlite_temp_binding"
    ]
    assert len(calls) == 3, len(calls)
    for call in calls:
        assert not call.args
        assert {keyword.arg for keyword in call.keywords} == {"charged_path"}
    # C1716: no configuration key or command-line surface, and one environment name only.
    assert "load_config" not in tiering and "argparse" not in tiering
    assert tiering.count("os.environ") == 1
    assert "os.environ.get(SQLITE_TMPDIR_ENV)" in tiering
    # The comparison is of measured identities, never of path text.
    assert "volume_uuid.strip().casefold()" in tiering


def test_c1715_the_authority_still_refuses_before_the_binding_is_consulted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Authority stays FIRST: with it closed, the binding is never even measured."""
    database, _tree, run = c13i.ten_chunk_run(tmp_path)

    def tripwire(*_args: Any, **_kwargs: Any) -> Any:
        message = "the temp binding was measured before the authority refused"
        raise AssertionError(message)

    monkeypatch.setattr(cm, "require_sqlite_temp_binding", tripwire)
    monkeypatch.setattr(cm, "accepted_multipass_storage_requirements", lambda: c13.REQUIREMENTS)
    with pytest.raises(cm.ChunkMultipassError, match="NOT AUTHORIZED"):
        cm.run_multipass_f0(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=run["base"] / "auth-first",
            run_id="c1715",
        )
    with pytest.raises(cm.ChunkMultipassError, match="NOT AUTHORIZED"):
        cm.merge_group_body(
            c13.group_request(
                run,
                schedule_path=run["base"] / "absent.json",
                group_id="group-0000",
                attempt=0,
                attempt_directory=run["base"] / "auth-first-group",
                database=database,
            )
        )
    assert not (run["base"] / "auth-first").exists()


# ==========================================================================
# C1717-C1719: the three counter refusal branches -- C16-MINOR-3
# ==========================================================================
def _final_world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Path]:
    _open(monkeypatch, tmp_path)
    database, tree = c1.build_world(tmp_path, members=9, shards=1, **SHAPE)
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, tmp_path / "run", database, tree)
    result = c13.merge_in_process(run, database, label="mp", run_id="branches")
    inputs = cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"])
    return inputs, result["world_directory"] / WORKING_CATALOG_FILENAME


def _witnesses(inputs: Any) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for item in inputs:
        attached = sqlite3.connect(f"file:{item.catalog_path}?immutable=1", uri=True)
        try:
            for accession, parsed in attached.execute(
                "SELECT accession_plain, parsed_record_id FROM census_accessions"
            ):
                seen.setdefault(str(accession), []).append(str(parsed))
        finally:
            attached.close()
    return seen


def test_c1717_a_second_derivation_on_one_connection_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs, catalog = _final_world(tmp_path, monkeypatch)
    connection = sqlite3.connect(str(catalog), isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        first = cm._plan_first_witness_counters(connection, inputs)
        assert first[0] > 0 and first[1] > 0
        names = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM temp.sqlite_master WHERE type = 'table'"
            )
        }
        assert {cm.PLAN_WITNESS_TABLE, cm.PLAN_WITNESS_RANK_TABLE, cm.PLAN_LEDGER_TABLE} <= names
        with pytest.raises(cm.ChunkMultipassError, match="already derived on this connection"):
            cm._plan_first_witness_counters(connection, inputs)
        # The refusal is a refusal, not a silent reuse: the first run's temp truth is untouched
        # and no second, doubled population was appended to it.
        assert (
            connection.execute(
                f"SELECT COUNT(*) AS n FROM temp.{cm.PLAN_WITNESS_TABLE}"  # noqa: S608
            ).fetchone()["n"]
            == connection.execute(
                f"SELECT COUNT(*) AS n FROM temp.{cm.PLAN_WITNESS_RANK_TABLE}"  # noqa: S608
            ).fetchone()["n"]
        )
    finally:
        connection.close()


def test_c1718_a_contested_accession_with_no_canonical_row_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs, catalog = _final_world(tmp_path, monkeypatch)
    contested = sorted(a for a, ids in _witnesses(inputs).items() if len(ids) > 1)
    assert contested, "the fixture produced no cross-chunk accession"
    connection = sqlite3.connect(str(catalog), isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "DELETE FROM census_accessions WHERE accession_plain = ?", (contested[0],)
        )
        with pytest.raises(cm.ChunkMultipassError) as refusal:
            cm._plan_first_witness_counters(connection, inputs)
    finally:
        connection.close()
    message = str(refusal.value)
    assert "has no canonical row in the final world" in message
    assert "refused rather than derived against a row that is not there" in message
    assert "parsed record" not in message


def test_c1719_a_rival_with_no_parsed_record_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs, catalog = _final_world(tmp_path, monkeypatch)
    rivals = [ids[1] for ids in _witnesses(inputs).values() if len(ids) > 1]
    assert rivals, "the fixture produced no later-chunk witness"
    connection = sqlite3.connect(str(catalog), isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "DELETE FROM census_parsed_records WHERE parsed_record_id = ?", (rivals[0],)
        )
        with pytest.raises(cm.ChunkMultipassError) as refusal:
            cm._plan_first_witness_counters(connection, inputs)
    finally:
        connection.close()
    message = str(refusal.value)
    assert "has no parsed record in the final world" in message
    assert "refused rather than derived from nothing" in message
    assert "canonical row" not in message


# ==========================================================================
# C1720: C8-M2 stays closed in the COMMITTED tree
# ==========================================================================
def test_c1720_the_counter_derivation_is_o_chunks_and_never_o_accessions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The chunk count is held FIXED while the accession population grows.

    D151-C16 confirmed C8-M2 closed with an independent probe that was never committed, so the
    committed tree could not have caught a regression to a query per rival. This is that guard,
    kept narrow: two worlds, the same ten-chunk partition, very different populations, and an
    identical statement count. If any round trip became per-accession or per-rival, the second
    world would issue more statements than the first.
    """
    measured: dict[int, tuple[int, int, int, tuple[int, int, int, int]]] = {}
    for filings in (2, 6):
        here = tmp_path / f"f{filings}"
        _open(monkeypatch, here)
        database, tree = c1.build_world(here, members=9, shards=1, **{**SHAPE, "filings": filings})
        plan = c13.multipass_plan(tree, database, chunk_members=1)
        run = c13.execute_in_process(plan, here / "run", database, tree)
        result = c13.merge_in_process(
            run, database, label=f"mp{filings}", run_id=f"c1720-{filings}"
        )
        inputs = cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"])
        catalog = result["world_directory"] / WORKING_CATALOG_FILENAME
        connection = sqlite3.connect(str(catalog), isolation_level=None)
        connection.row_factory = sqlite3.Row
        statements: list[str] = []
        connection.set_trace_callback(statements.append)
        try:
            counters = cm._plan_first_witness_counters(connection, inputs)
        finally:
            connection.set_trace_callback(None)
            connection.close()
        probe = sqlite3.connect(str(catalog), isolation_level=None)
        accessions = probe.execute("SELECT COUNT(*) AS n FROM census_accessions").fetchone()[0]
        probe.close()
        measured[filings] = (len(statements), len(inputs), accessions, counters)
        assert counters[0] > 0 and counters[1] > 0
    small, large = measured[2], measured[6]
    assert small[1] == large[1] == 10, measured
    # The test only discriminates if the population it varies actually grew -- accessions, and
    # the CONTESTED and staged-row populations a per-rival implementation would iterate.
    assert large[2] > small[2], measured
    assert large[3][0] > small[3][0], measured
    assert large[3][1] > small[3][1], measured
    assert small[0] == large[0], measured
