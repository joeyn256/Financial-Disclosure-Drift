"""D151-C19: the five D151-C18 findings, corrected and proved behaviourally.

**C18-MINOR-1 -- SQLite's own selection rule (C1901-C1905).** SQLite takes ``SQLITE_TMPDIR``
verbatim and uses it only if it is a directory it can write and search; otherwise it falls
through to ``TMPDIR`` silently. Both guards -- the accepted D137-R8 one and the multipass one --
now share ONE candidate validator that applies exactly that rule to the RAW value, so a
``chmod 500`` root or a value with surrounding whitespace refuses before governed use, and the
positive control shows SQLite opening its spill under the governed root.

**C18-INFO-1 -- the measured binding is durable (C1906-C1917).** The full measured
:class:`~disclosure_drift.m3.chunk_tiering.SqliteTempBinding` is folded into the sealed storage
plan, whose contract moved ``/1 -> /2`` under owner R4A; every merge child remeasures and must
match; a forged, edited, relabelled or superseded record refuses.

**C18-MINOR-2 -- the environment closure by binding (C1918-C1922).** ``from os import environ``,
subscripts, aliases and ``os.getenv`` are all seen. **C18-INFO-2 -- the transitive chain
(C1923-C1926)**, both import forms, bounded subprocess proved. **C18-INFO-3 (C1927)** the
counter prose is held to the measurement. **C1928-C1936** re-state the standing boundaries.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import os
import sqlite3
import subprocess
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c13_intermediates as c13i  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_c13_multipass_semantics as sem  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_evidence as cev  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3.chunk_evidence import write_once_json  # noqa: E402
from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME  # noqa: E402

OTHER_VOLUME = "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"
ADMITTED_ON = "not the one this consolidation was admitted on"
#: The launcher relays only the TAIL of a child's stderr, so a child-side refusal is recognized
#: by the closing clause of its message.
ADMITTED_ON_TAIL = "trusting a claim it had just contradicted"
SUPERSEDED = "superseded contract"
STALE = "not the identity of the record it accompanies"
SHAPE: dict[str, Any] = {"filings": 2, "share_every": 3, "junk": 4, "unknown": 5, "duplicate": True}
CURRENT_CONTRACT = "m3.3-chunked-f0-multipass-storage-plan/2"
SUPERSEDED_CONTRACT = "m3.3-chunked-f0-multipass-storage-plan/1"


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


def _volume(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """A synthetic volume laid out as the accepted D137 tests lay one out."""
    volume = tmp_path / "volume"
    archive = volume / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir(parents=True)
    work = volume / "work"
    work.mkdir()
    temp = volume / "tmp"
    temp.mkdir()
    return volume, work, temp, archive


def _reason(message: str) -> str:
    for key, needle in (
        ("not set", "is not set"),
        ("whitespace", "leading or trailing whitespace"),
        ("relative", "not an absolute path"),
        ("missing", "does not name an existing directory"),
        ("unusable", "cannot write and search"),
        ("volume", "not the accepted qualified volume"),
        ("volume", "must be counted by the same capacity model"),
    ):
        if needle in message:
            return key
    return "other:" + message[:80]


def _both_guards(
    work: Path, archive: Path, provider: Callable[[Path], ewr.VolumeIdentity]
) -> dict[str, str]:
    """Both guards on the CURRENT process environment, each reduced to its verdict class."""
    verdicts: dict[str, str] = {}
    try:
        ct.require_sqlite_temp_binding(charged_path=work / "world", provider=provider)
        verdicts["multipass"] = "ADMITTED"
    except ct.ChunkTieringError as exc:
        verdicts["multipass"] = _reason(str(exc))
    try:
        ewr.require_external_sqlite_tmpdir(
            working_root=work,
            archive=archive,
            expected_uuid=c13.SYNTHETIC_MERGE_VOLUME,
            provider=provider,
        )
        verdicts["d137_r8"] = "ADMITTED"
    except ewr.ExternalWorkingRootError as exc:
        verdicts["d137_r8"] = _reason(str(exc))
    return verdicts


def _two_volume_provider(temp_root: Path) -> Callable[[Path], ewr.VolumeIdentity]:
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

    return identify


def _skip_if_superuser() -> None:
    if os.geteuid() == 0:  # pragma: no cover - the governed processes never run as root
        pytest.skip("permission bits do not bind a superuser; SQLite's access test passes for root")


# ==========================================================================
# C1901-C1905: the guard admits only what SQLite will use -- C18-MINOR-1
# ==========================================================================
def test_c1901_a_temporary_root_sqlite_cannot_use_refuses_before_governed_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _skip_if_superuser()
    volume, work, temp, archive = _volume(tmp_path)
    provider = c13.synthetic_volume_provider()
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(temp))
    before = sorted(p.name for p in volume.rglob("*"))
    for mode in (0o500, 0o600, 0o000):  # no W_OK, no X_OK, neither
        temp.chmod(mode)
        try:
            assert not os.access(temp, os.W_OK | os.X_OK)
            verdicts = _both_guards(work, archive, provider)
            assert verdicts == {"multipass": "unusable", "d137_r8": "unusable"}, (
                oct(mode),
                verdicts,
            )
            assert sorted(p.name for p in volume.rglob("*")) == before
        finally:
            temp.chmod(0o700)
    # the same directory, usable again, admits -- the permission bits were the whole difference
    assert _both_guards(work, archive, provider) == {"multipass": "ADMITTED", "d137_r8": "ADMITTED"}


@pytest.mark.parametrize(
    ("label", "decorate"),
    [
        ("c1902-trailing-spaces", lambda value: value + "  "),
        ("c1902-trailing-newline", lambda value: value + "\n"),
        ("c1903-leading-space", lambda value: " " + value),
        ("c1903-leading-tab", lambda value: "\t" + value),
    ],
)
def test_c1902_c1903_a_whitespace_altered_temporary_root_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str, decorate: Callable[[str], str]
) -> None:
    _volume_, work, temp, archive = _volume(tmp_path)
    raw = decorate(str(temp))
    assert raw != raw.strip() and Path(raw.strip()).is_dir()
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, raw)
    provider = c13.synthetic_volume_provider()
    assert _both_guards(work, archive, provider) == {
        "multipass": "whitespace",
        "d137_r8": "whitespace",
    }, label
    # the normalized value is a valid candidate -- which is exactly why normalizing was the defect
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, raw.strip())
    assert _both_guards(work, archive, provider) == {"multipass": "ADMITTED", "d137_r8": "ADMITTED"}


#: A fresh interpreter: SQLite caches ``getenv("SQLITE_TMPDIR")`` on first use, so the spill
#: placement of THIS process could never be trusted to reflect a value set mid-test.
_SPILL_PROBE = textwrap.dedent(
    """
    import os, sqlite3, sys
    from pathlib import Path
    governed = os.path.realpath(sys.argv[1])
    db = sqlite3.connect(sys.argv[2], isolation_level=None)
    db.execute("PRAGMA cache_size = -200")
    db.execute(
        "CREATE TEMP TABLE big AS WITH RECURSIVE s(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM s "
        "WHERE i < 3000) SELECT i, randomblob(1500) AS b FROM s"
    )
    db.execute("SELECT COUNT(*) FROM (SELECT b FROM temp.big ORDER BY b)").fetchone()
    opened = []
    if sys.platform == "darwin":
        import fcntl
        for fd in os.listdir("/dev/fd"):
            try:
                raw = fcntl.fcntl(int(fd), fcntl.F_GETPATH, bytes(1024))
                opened.append(raw.rstrip(b"\\0").decode())
            except OSError:
                pass
    else:
        for fd in os.listdir("/proc/self/fd"):
            try:
                opened.append(os.readlink(f"/proc/self/fd/{fd}"))
            except OSError:
                pass
    spills = [p.split(" (deleted)")[0] for p in opened if "etilqs" in p]
    parents = {os.path.realpath(os.path.dirname(p)) for p in spills}
    print("UNDER_GOVERNED" if spills and parents == {governed} else "ELSEWHERE:" + ";".join(spills))
    """
)


def _spill_location(temp_value: str, database: Path) -> str:
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", _SPILL_PROBE, temp_value, str(database)],
        env={**os.environ, ewr.SQLITE_TMPDIR_ENV: temp_value},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr[-1500:]
    return completed.stdout.strip()


def test_c1904_a_usable_same_volume_root_admits_and_sqlite_really_spills_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _volume_, work, temp, archive = _volume(tmp_path)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(temp))
    provider = c13.synthetic_volume_provider()
    assert _both_guards(work, archive, provider) == {"multipass": "ADMITTED", "d137_r8": "ADMITTED"}
    binding = ct.require_sqlite_temp_binding(charged_path=work / "world", provider=provider)
    stat = temp.stat()
    assert (binding.temp_root_device, binding.temp_root_inode) == (stat.st_dev, stat.st_ino)
    # The admitted candidate is the one SQLite uses: a fresh process, a real spill, and the open
    # temporary file's directory is the governed root.
    assert _spill_location(str(temp), tmp_path / "probe.sqlite3") == "UNDER_GOVERNED"
    # And the two shapes the guard now refuses are exactly the ones SQLite bypasses.
    if os.geteuid() != 0:
        temp.chmod(0o500)
        try:
            assert _spill_location(str(temp), tmp_path / "probe2.sqlite3").startswith("ELSEWHERE")
        finally:
            temp.chmod(0o700)
    assert _spill_location(str(temp) + " ", tmp_path / "probe3.sqlite3").startswith("ELSEWHERE")


def test_c1905_the_d137_r8_and_multipass_guards_agree_on_every_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One validator, two guards: the matrix is the parity proof, and a mutant fixing only one
    guard changes one column."""
    volume, work, temp, archive = _volume(tmp_path)
    same = c13.synthetic_volume_provider()
    different = _two_volume_provider(temp)
    a_file = volume / "a-file"
    a_file.write_text("not a directory", encoding="utf-8")
    matrix: list[tuple[str, str | None, Callable[[Path], ewr.VolumeIdentity], str]] = [
        ("empty", "", same, "not set"),
        ("whitespace-only", "   ", same, "not set"),
        ("leading whitespace", " " + str(temp), same, "whitespace"),
        ("trailing whitespace", str(temp) + " ", same, "whitespace"),
        ("missing", None, same, "not set"),
        ("relative", "relative/tmp", same, "relative"),
        ("file, not directory", str(a_file), same, "missing"),
        ("absent directory", str(volume / "never-created"), same, "missing"),
        ("valid, same volume", str(temp), same, "ADMITTED"),
        ("valid, different volume", str(temp), different, "volume"),
    ]
    if os.geteuid() != 0:
        matrix.append(("permission unusable", str(temp), same, "unusable"))
    observed: dict[str, dict[str, str]] = {}
    for label, value, provider, expected in matrix:
        if value is None:
            monkeypatch.delenv(ewr.SQLITE_TMPDIR_ENV, raising=False)
        else:
            monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, value)
        if label == "permission unusable":
            temp.chmod(0o500)
        try:
            observed[label] = _both_guards(work, archive, provider)
        finally:
            if label == "permission unusable":
                temp.chmod(0o700)
        assert observed[label] == {"multipass": expected, "d137_r8": expected}, (label, observed)
    assert len(observed) == len(matrix)


# ==========================================================================
# C1906-C1910: the measured binding is durable and remeasured -- C18-INFO-1
# ==========================================================================
def _binding(**changes: Any) -> ct.SqliteTempBinding:
    base: dict[str, Any] = {
        "temp_root_device": 1,
        "temp_root_inode": 2,
        "temp_volume_uuid": c13.SYNTHETIC_MERGE_VOLUME,
        "temp_filesystem_type": "apfs",
        "temp_device_identifier": "disk-synthetic",
        "charged_volume_uuid": c13.SYNTHETIC_MERGE_VOLUME,
        "charged_filesystem_type": "apfs",
        "charged_device_identifier": "disk-synthetic",
    }
    base.update(changes)
    return ct.SqliteTempBinding(**base)


def _plan(binding: ct.SqliteTempBinding, **changes: Any) -> ct.MultipassStoragePlan:
    requirements = ct.MultipassStorageRequirements(
        internal_reserve_bytes=100,
        level_one_peak_ratio=1.5,
        level_two_peak_ratio=2.0,
        level_one_transient_bytes=7,
        level_two_transient_bytes=4096,
    )
    if changes:
        requirements = ct.MultipassStorageRequirements(
            **{**dict(requirements.as_record()), **changes}  # type: ignore[arg-type]
        )
    return ct.plan_multipass_storage(
        plan_digest="p",
        merge_schedule_digest="s",
        groups=[("group-0000", ["chunk-0000", "chunk-0001"]), ("group-0001", ["chunk-0002"])],
        chunk_bytes_by_id={"chunk-0000": 1000, "chunk-0001": 500, "chunk-0002": 2000},
        seed_catalog_bytes=50,
        requirements=requirements,
        sqlite_temp_binding=binding,
    )


def test_c1906_c1907_c1908_every_measured_binding_field_moves_the_storage_identity() -> None:
    base = _plan(_binding()).identity()
    moved = {
        "temp+charged volume uuid": _binding(
            temp_volume_uuid=OTHER_VOLUME, charged_volume_uuid=OTHER_VOLUME
        ),
        "temp filesystem type": _binding(temp_filesystem_type="exfat"),
        "temp device identifier": _binding(temp_device_identifier="disk9s1"),
        "charged filesystem type": _binding(charged_filesystem_type="exfat"),
        "charged device identifier": _binding(charged_device_identifier="disk9s1"),
        "temp root device": _binding(temp_root_device=7),
        "temp root inode": _binding(temp_root_inode=99),
    }
    identities = {label: _plan(binding).identity() for label, binding in moved.items()}
    assert base not in identities.values()
    assert len(set(identities.values())) == len(identities)
    # C1906/C1907: a volume identity is never allowed to move ALONE -- a binding whose two
    # volumes differ is not a binding and cannot be constructed, so no plan can record one.
    with pytest.raises(ct.ChunkTieringError, match="is not a binding"):
        _binding(temp_volume_uuid=OTHER_VOLUME)
    with pytest.raises(ct.ChunkTieringError, match="is not a binding"):
        _binding(charged_volume_uuid=OTHER_VOLUME)
    # The record is exact, path-free, and its fields are the ones the identity folds.
    record = dict(_binding().as_record())
    assert tuple(record) == ct.SQLITE_TEMP_BINDING_FIELDS
    assert ct.SqliteTempBinding.from_record(record) == _binding()
    assert "sqlite_temp_binding" in _plan(_binding()).as_record()
    assert _plan(_binding()).as_record()["sqlite_temp_binding"] == record


def test_c1909_a_serialized_or_forged_binding_cannot_replace_the_measurement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    measured = ct.require_sqlite_temp_binding(charged_path=tmp_path / "world")
    record = dict(measured.as_record())
    # A claim of equality is not a field anyone can set: extra keys, legacy shapes and edited
    # measurements all refuse at the comparison, and only the measurement itself agrees.
    for forged, needle in (
        ({**record, "same_volume": True}, "carries unexpected"),
        ({**record, "verified": True, "equal": True}, "carries unexpected"),
        (
            {
                "volume_uuid": c13.SYNTHETIC_MERGE_VOLUME,
                "filesystem_type": "apfs",
                "device_identifier": "disk-synthetic",
            },
            "pre-C19 three-field",
        ),
        ({**record, "temp_root_inode": record["temp_root_inode"] + 1}, ADMITTED_ON),  # type: ignore[operator]
        ({**record, "charged_device_identifier": "forged"}, ADMITTED_ON),
    ):
        with pytest.raises((cm.ChunkMultipassError, ct.ChunkTieringError), match=needle):
            cm._require_expected_binding(measured, forged, label="x")
    assert cm._require_expected_binding(measured, record, label="x") == measured
    # Through a real request: the body measures for itself and holds the request to it.
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    schedule = cm.derive_merge_schedule(run["plan"])
    root = run["base"] / "forged"
    root.mkdir()
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    group = schedule.groups[0]
    attempt = root / "intermediates" / group.group_id / "attempt-000"
    forged_request = c13.group_request(
        run,
        schedule_path=schedule_path,
        group_id=group.group_id,
        attempt=0,
        attempt_directory=attempt,
        database=database,
        expected_binding={**record, "temp_root_inode": record["temp_root_inode"] + 1},  # type: ignore[operator]
    )
    with pytest.raises(cm.ChunkMultipassError, match=ADMITTED_ON):
        cm.merge_group_body(forged_request)
    assert not (root / "intermediates").exists()
    # No request field says "same volume": the request carries a measurement, and nothing else.
    for request_type in (cm.GroupMergeRequest, cm.FinalMergeRequest):
        fields = set(inspect.signature(request_type).parameters)
        assert "expected_sqlite_temp_binding" in fields
        assert not {f for f in fields if "same" in f or "verified" in f or "equal" in f}


def test_c1910_a_child_whose_own_measurement_differs_from_the_expected_binding_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    schedule = cm.derive_merge_schedule(run["plan"])
    root = run["base"] / "child"
    root.mkdir()
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    group = schedule.groups[0]

    def request(attempt: int) -> cm.GroupMergeRequest:
        return c13.group_request(
            run,
            schedule_path=schedule_path,
            group_id=group.group_id,
            attempt=attempt,
            attempt_directory=root / "intermediates" / group.group_id / f"attempt-{attempt:03d}",
            database=database,
        )

    # (a) the durable expectation was measured against tmp_path/sqlite-temp; the REAL child runs
    # with a changed SQLITE_TMPDIR -- another usable directory on the same volume -- and refuses on
    # its own measurement, before any attempt directory exists.
    admitted_on = request(0)
    other = tmp_path / "other-temp"
    other.mkdir()
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(other))
    with pytest.raises(cm.ChunkMultipassError, match="NOT complete") as refusal:
        cm.run_group_merge(admitted_on)
    assert ADMITTED_ON_TAIL in str(refusal.value)
    assert not Path(admitted_on.attempt_directory).exists()
    # (b) the expectation says "same volume" -- it always does, by construction -- and the child's
    # OWN two-volume measurement disagrees: the guard refuses first, the record never decides.
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(tmp_path / "sqlite-temp"))
    mismatching = c13i.multipass_child_bootstrap(tmp_path / "repo").replace(
        f"volume_uuid={c13.SYNTHETIC_MERGE_VOLUME!r}",
        f"volume_uuid=({OTHER_VOLUME!r} if 'sqlite-temp' in str(path) else "
        f"{c13.SYNTHETIC_MERGE_VOLUME!r})",
    )
    monkeypatch.setattr(cm, "_CHILD_BOOTSTRAP", mismatching)
    second = request(1)
    with pytest.raises(cm.ChunkMultipassError, match="NOT complete") as refusal2:
        cm.run_group_merge(second)
    assert "must be counted by the same capacity model" in str(refusal2.value)
    assert not Path(second.attempt_directory).exists()
    # (c) positive control: same root, same volume, the child's measurement equals the
    # expectation, and the intermediate is built.
    monkeypatch.setattr(cm, "_CHILD_BOOTSTRAP", c13i.multipass_child_bootstrap(tmp_path / "repo"))
    receipt = cm.run_group_merge(request(2))
    assert receipt.status == "complete" and receipt.attempt == 2


# ==========================================================================
# C1911-C1917: the storage-plan contract moved /1 -> /2 -- owner R4A
# ==========================================================================
def test_c1911_c1912_a_sealed_document_round_trips_exactly_and_folds_the_binding() -> None:
    plan = _plan(_binding())
    document = plan.as_document()
    assert document["contract"] == CURRENT_CONTRACT == ct.MULTIPASS_STORAGE_PLAN_CONTRACT
    assert document[ct.STORAGE_PLAN_IDENTITY_KEY] == plan.identity()
    assert ct.MultipassStoragePlan.from_document(json.loads(json.dumps(document))) == plan
    assert ct.MultipassStoragePlan.from_document(document).identity() == plan.identity()
    # the identity is a digest over the record -- binding included -- and nothing else
    payload = json.dumps(dict(plan.as_record()), sort_keys=True, separators=(",", ":"))
    assert plan.identity() == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert "sqlite_temp_binding" in payload and c13.SYNTHETIC_MERGE_VOLUME in payload


def test_c1913_c1916_a_pre_c19_record_at_the_governed_location_refuses_and_is_never_upgraded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    root = run["base"] / "stale"
    root.mkdir()
    # A /1 record exactly as C17 wrote them: no binding, no sealed identity, contract /1.
    schedule = cm.derive_merge_schedule(run["plan"])
    inputs = cc.resolve_chunk_inputs(run["plan"], internal_root=run["chunk_root"])
    _sha, catalog_bytes = cm.file_digest(database)
    binding = ct.require_sqlite_temp_binding(charged_path=root)
    current = ct.plan_multipass_storage(
        plan_digest=run["plan"].plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        groups=[(g.group_id, g.chunk_ids) for g in schedule.groups],
        chunk_bytes_by_id={i.chunk_id: i.receipt.manifest.total_bytes for i in inputs},
        seed_catalog_bytes=catalog_bytes,
        requirements=c13.REQUIREMENTS,
        sqlite_temp_binding=binding,
    )
    legacy = json.loads(json.dumps(dict(current.as_record())))
    legacy["contract"] = SUPERSEDED_CONTRACT
    legacy.pop("sqlite_temp_binding")
    path = root / cm.STORAGE_PLAN_FILENAME
    write_once_json(path, legacy)
    before = path.read_bytes()
    with pytest.raises(ct.ChunkTieringError, match=SUPERSEDED):
        cm.run_multipass_f0(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=root,
            run_id="stale",
        )
    assert not (root / "intermediates").exists()
    assert path.read_bytes() == before  # C1916: never rewritten, never upgraded in place
    with pytest.raises(ct.ChunkTieringError, match=SUPERSEDED):
        ct.MultipassStoragePlan.from_document(legacy)
    with pytest.raises(ct.ChunkTieringError, match=SUPERSEDED):
        cm._record_storage_plan(path, current)
    assert path.read_bytes() == before


def test_c1914_c1915_a_relabelled_or_edited_record_with_a_stale_identity_refuses() -> None:
    plan = _plan(_binding())
    document = json.loads(json.dumps(dict(plan.as_document())))
    # C1914: a /1 record relabelled /2 carries the identity it was sealed with, not the one its
    # fields now have -- and a relabel without resealing refuses.
    relabelled = copy.deepcopy(document)
    as_one = {k: v for k, v in relabelled.items() if k != ct.STORAGE_PLAN_IDENTITY_KEY}
    as_one["contract"] = SUPERSEDED_CONTRACT
    relabelled[ct.STORAGE_PLAN_IDENTITY_KEY] = hashlib.sha256(
        json.dumps(as_one, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ct.ChunkTieringError, match=STALE):
        ct.MultipassStoragePlan.from_document(relabelled)
    # C1915: a changed binding under the old digest refuses; so does any other edited field.
    edited = copy.deepcopy(document)
    edited["sqlite_temp_binding"]["temp_root_inode"] += 1
    with pytest.raises(ct.ChunkTieringError, match=STALE):
        ct.MultipassStoragePlan.from_document(edited)
    edited_terms = copy.deepcopy(document)
    edited_terms["requirements"]["level_two_transient_bytes"] = 0
    with pytest.raises(ct.ChunkTieringError, match=STALE):
        ct.MultipassStoragePlan.from_document(edited_terms)
    # A resealed edit (correct digest) that smuggles a field the identity does not cover refuses.
    smuggled = copy.deepcopy(document)
    smuggled["operator_note"] = "trust me"
    with pytest.raises(ct.ChunkTieringError, match="not the ones its identity seals"):
        ct.MultipassStoragePlan.from_document(smuggled)
    # An unknown future contract is refused as firmly as the superseded one.
    unknown = copy.deepcopy(document)
    unknown["contract"] = "m3.3-chunked-f0-multipass-storage-plan/3"
    with pytest.raises(ct.ChunkTieringError, match="does not write"):
        ct.MultipassStoragePlan.from_document(unknown)


def test_c1917_no_code_path_writes_the_superseded_contract() -> None:
    assert ct.MULTIPASS_STORAGE_PLAN_CONTRACT == CURRENT_CONTRACT
    assert ct.SUPERSEDED_STORAGE_PLAN_CONTRACTS == (SUPERSEDED_CONTRACT,)
    assert _plan(_binding()).contract == CURRENT_CONTRACT
    assert _plan(_binding()).as_document()["contract"] == CURRENT_CONTRACT
    # The /1 literal survives in exactly one place: the superseded tuple that REFUSES it.
    for module in (ct, cm):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        parents: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        holders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == SUPERSEDED_CONTRACT:
                holder = node
                while holder in parents and not isinstance(holder, ast.AnnAssign | ast.Assign):
                    holder = parents[holder]
                target = getattr(holder, "target", None) or getattr(holder, "targets", [None])[0]
                holders.append(getattr(target, "id", None))
        assert holders == (["SUPERSEDED_STORAGE_PLAN_CONTRACTS"] if module is ct else []), (
            module.__name__,
            holders,
        )
    # And the other persisted contracts did not move.
    assert cp.CHUNK_PLAN_CONTRACT == "m3.3-chunked-f0-plan/2"
    assert cp.CALIBRATION_PLAN_CONTRACT == "m3.3-chunked-f0-calibration-plan/1"
    assert cp.MULTIPASS_PLAN_CONTRACT == "m3.3-chunked-f0-multipass-plan/1"
    assert cm.MERGE_SCHEDULE_CONTRACT == "m3.3-chunked-f0-merge-schedule/1"
    assert cm.INTERMEDIATE_RECEIPT_CONTRACT == "m3.3-chunked-f0-intermediate-receipt/2"
    assert cm.MULTIPASS_CONSOLIDATION_CONTRACT == "m3.3-chunked-f0-multipass-consolidation/1"
    assert cev.FINAL_WORLD_RECEIPT_CONTRACT == "m3.3-chunked-f0-final-receipt/2"


# ==========================================================================
# C1918-C1922: the environment closure sees every binding form -- C18-MINOR-2
# ==========================================================================
_ENVIRONMENT_PROBES: dict[str, str] = {
    "C1918 from os import environ; environ.get": (
        'from os import environ\n_PROBE = environ.get("FAKE_GOVERNANCE_BYPASS")\n'
    ),
    "C1919 os.environ[...]": 'import os\n_PROBE = os.environ["FAKE_GOVERNANCE_BYPASS"]\n',
    "C1920 from os import environ as _e; _e[...]": (
        'from os import environ as _e\n_PROBE = _e["FAKE_GOVERNANCE_BYPASS"]\n'
    ),
    "C1921 os.getenv": 'import os\n_PROBE = os.getenv("FAKE_GOVERNANCE_BYPASS")\n',
    "C1922 import os as _o; _o.environ.get": (
        'import os as _o\n_PROBE = _o.environ.get("FAKE_GOVERNANCE_BYPASS")\n'
    ),
    "os.environb": 'import os\n_PROBE = os.environb.get(b"FAKE_GOVERNANCE_BYPASS")\n',
    "from os import getenv as _g": 'from os import getenv as _g\n_PROBE = _g("FAKE")\n',
    "import os.path binds os": 'import os.path\n_PROBE = os.environ.get("FAKE")\n',
    "a default on the one permitted read": None,  # type: ignore[dict-item]
    "dynamic import": 'import importlib\n_PROBE = importlib.import_module("os").environ\n',
    "reflective lookup": 'import os\n_PROBE = getattr(os, "environ")\n',
}


def test_c1918_to_c1922_every_environment_access_shape_is_caught_in_both_new_modules() -> None:
    for module in (cm, ct):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert c13i.environment_closure_violations(module.__name__, source) == [], module.__name__
        for label, probe in _ENVIRONMENT_PROBES.items():
            if probe is None:
                if module is not ct:
                    continue
                mutated = source.replace(
                    "os.environ.get(SQLITE_TMPDIR_ENV)", 'os.environ.get(SQLITE_TMPDIR_ENV, "/tmp")'
                )
                assert mutated != source
            else:
                mutated = source + "\n" + probe
            violations = c13i.environment_closure_violations(module.__name__, mutated)
            assert violations, (module.__name__, label)
            assert all(line > 0 for line, _ in violations), (module.__name__, label, violations)
    # The one permitted read is exactly where the accepted design put it, exactly once.
    tiering = Path(ct.__file__).read_text(encoding="utf-8")
    reads = c13i.permitted_sqlite_tmpdir_reads(tiering, function="require_sqlite_temp_binding")
    assert len(reads) == 1
    assert c13i.environment_accesses(Path(cm.__file__).read_text(encoding="utf-8")) == []
    # And the prose states the ownership correctly (C19 §11).
    assert "the only environment this module reads" not in (cm.__doc__ or "")
    assert "THIS module reads no environment at all" in (cm.__doc__ or "")


# ==========================================================================
# C1923-C1926: the transitive capability proof covers the reached chain -- C18-INFO-2
# ==========================================================================
def test_c1923_the_reached_chain_includes_canary_runtime_and_is_exact() -> None:
    chain = c13i.reached_from(ewr.__name__)
    assert "disclosure_drift.m3.canary_runtime" in chain
    assert "disclosure_drift.m3.dock_transport" in chain
    assert chain == set(c13i.STORAGE_BINDING_CHAIN)
    tiering = Path(ct.__file__).read_text(encoding="utf-8")
    assert "disclosure_drift.m3.external_working_root" in c13i.package_imports(tiering)
    for name in chain:
        path = c13i.module_path(name)
        assert path is not None
        assert c13i.capability_violations(path.read_text(encoding="utf-8")) == [], name


@pytest.mark.parametrize(
    ("label", "probe"),
    [
        ("C1924 from socket import socket", "\nfrom socket import socket\n"),
        ("C1924 import socket", "\nimport socket\n"),
        ("C1924 from urllib.request import urlopen", "\nfrom urllib.request import urlopen\n"),
        ("C1924 import http.client", "\nimport http.client\n"),
        ("C1925 from shutil import rmtree", "\nfrom shutil import rmtree\n"),
        ("C1925 shutil.rmtree call", "\nimport shutil\n\n\ndef _p(x):\n    shutil.rmtree(x)\n"),
        ("C1925 from shutil import copyfile", "\nfrom shutil import copyfile\n"),
        ("C1925 from os import unlink", "\nfrom os import unlink\n"),
        ("C1925 os.remove call", "\nimport os\n\n\ndef _p(x):\n    os.remove(x)\n"),
        ("C1925 Path.unlink call", "\n\ndef _p(x):\n    x.unlink()\n"),
        (
            "C1926 shell=True",
            "\nimport subprocess\n\n\ndef _p(x):\n    subprocess.run(x, shell=True)\n",
        ),
        (
            "C1926 caller-controlled argv",
            "\nimport subprocess\n\n\ndef _p(x):\n    subprocess.run(x)\n",
        ),
        (
            "C1926 non-fixed program",
            '\nimport subprocess\n\n\ndef _p(x):\n    subprocess.run([x, "-a"])\n',
        ),
        (
            "C1926 unpacked arguments",
            '\nimport subprocess\n\n\ndef _p(x):\n    subprocess.run(["/bin/ls", *x])\n',
        ),
        (
            "C1926 from subprocess import run",
            "\nfrom subprocess import run\n\n\ndef _p(x):\n    run(x)\n",
        ),
        ("C1926 os.system", "\nimport os\n\n\ndef _p(x):\n    os.system(x)\n"),
    ],
)
def test_c1924_c1925_c1926_forbidden_capabilities_are_detected_by_both_import_forms(
    label: str, probe: str
) -> None:
    for name in sorted(c13i.STORAGE_BINDING_CHAIN):
        path = c13i.module_path(name)
        assert path is not None
        source = path.read_text(encoding="utf-8")
        assert c13i.capability_violations(source + probe), (label, name)


def test_c1926_the_accepted_bounded_subprocess_use_remains_valid() -> None:
    programs = {
        name: c13i.subprocess_programs(
            c13i.module_path(name).read_text(encoding="utf-8")  # type: ignore[union-attr]
        )
        for name in sorted(c13i.STORAGE_BINDING_CHAIN)
    }
    assert programs["disclosure_drift.m3.external_working_root"] == {"/usr/sbin/diskutil"}
    assert programs["disclosure_drift.m3.canary_runtime"] == {
        "/bin/ps",
        "/usr/bin/pmset",
        "/usr/sbin/ioreg",
    }
    assert programs["disclosure_drift.m3.dock_transport"] == {"/usr/sbin/ioreg"}
    assert programs["disclosure_drift.errors"] == set()
    assert programs["disclosure_drift.storage.sqlite"] == set()
    # A bounded, fixed-argv, read-only system query is NOT a violation: the detector distinguishes
    # the accepted capability from a forbidden one instead of banning the import.
    for name in c13i.STORAGE_BINDING_CHAIN:
        source = c13i.module_path(name).read_text(encoding="utf-8")  # type: ignore[union-attr]
        assert c13i.capability_violations(source) == [], name
        assert "shell=True" not in source, name


# ==========================================================================
# C1927: the counter prose is held to the measured statement count -- C18-INFO-3
# ==========================================================================
def _statements(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, members: int) -> tuple[int, int]:
    here = tmp_path / f"m{members}"
    _open(monkeypatch, here)
    database, tree = c1.build_world(here, members=members, shards=1, **SHAPE)
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, here / "run", database, tree)
    result = c13.merge_in_process(run, database, label="mp", run_id=f"c1927-{members}")
    inputs = cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"])
    connection = sqlite3.connect(
        str(result["world_directory"] / WORKING_CATALOG_FILENAME), isolation_level=None
    )
    connection.row_factory = sqlite3.Row
    statements: list[str] = []
    connection.set_trace_callback(statements.append)
    try:
        counters = cm._plan_first_witness_counters(connection, inputs)
    finally:
        connection.set_trace_callback(None)
        connection.close()
    assert counters[0] > 0
    return len(statements), len(inputs)


def test_c1927_the_counter_prose_states_the_measured_statement_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    small, small_chunks = _statements(tmp_path, monkeypatch, members=9)
    large, large_chunks = _statements(tmp_path, monkeypatch, members=19)
    assert (small_chunks, large_chunks) == (10, 20)
    per_chunk, remainder = divmod(large - small, large_chunks - small_chunks)
    assert remainder == 0
    constant = small - per_chunk * small_chunks
    docstring = inspect.getdoc(cm._plan_first_witness_counters) or ""
    assert f"{constant} + {per_chunk} * chunks" in docstring, (constant, per_chunk, docstring)
    assert "never with the accession or rival population" in docstring
    assert "plus two per chunk" not in docstring


# ==========================================================================
# C1928-C1936: the standing boundaries, re-stated on the C19 tree
# ==========================================================================
def test_c1928_c1929_c1935_authority_transients_and_every_production_term_stay_closed() -> None:
    assert c13i.committed_literal(cm, "REAL_MULTIPASS_F0_AUTHORITY") is None
    assert "NOT AUTHORIZED" in c13i.refusal_in_a_fresh_interpreter()
    for module, name in (
        (ce, "REAL_CHUNKED_F0_EXECUTION_AUTHORITY"),
        (cm, "REAL_MULTIPASS_F0_AUTHORITY"),
        (cs, "REAL_CHUNK_TRANSFER_AUTHORITY"),
        (cs, "REAL_INTERNAL_RECLAIM_AUTHORITY"),
        (cp, "PRODUCTION_CHUNK_MEMBERS"),
        (cs, "INTERNAL_RESERVE_BYTES"),
        (cs, "CHUNK_PEAK_REQUIREMENT_BYTES"),
        (ct, "MULTIPASS_LEVEL_ONE_PEAK_RATIO"),
        (ct, "MULTIPASS_LEVEL_TWO_PEAK_RATIO"),
        (ct, "MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES"),
        (ct, "MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES"),
        (ct, "PRODUCTION_SPILL_POLICY"),
        (ct, "QUALIFIED_EXTERNAL_TIER"),
    ):
        assert getattr(module, name) is None, name
        assert c13i.committed_literal(module, name) is None, name
    assert not hasattr(ct, "MULTIPASS_TRANSIENT_BYTES")
    requirements = ct.MultipassStorageRequirements(
        internal_reserve_bytes=1,
        level_one_peak_ratio=1.0,
        level_two_peak_ratio=1.0,
        level_one_transient_bytes=3,
        level_two_transient_bytes=5,
    )
    assert (
        requirements.transient_for(ct.MERGE_LEVEL_ONE),
        requirements.transient_for(ct.MERGE_LEVEL_TWO),
    ) == (3, 5)
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE"):
        ct.accepted_multipass_storage_requirements()


def test_c1933_the_d140_r12_order_is_unchanged_in_the_finalizer() -> None:
    source = inspect.getsource(cm.finalize_multipass_body)
    assert (
        source.index("_plan_first_witness_counters(")
        < source.index("_merge_sidecar(")
        < source.index("require_f0_success(")
        < source.index("mark_parsed(")
        < source.index("write_phase_checkpoint(")
        < source.index("FINAL_WORLD_RECEIPT_FILENAME")
    )
    # and the binding comparison sits before admission and before the world exists
    assert (
        source.index("require_real_multipass_authority()")
        < source.index("_require_expected_binding(")
        < source.index("_admit_merge_step(")
        < source.index("world_directory.mkdir(")
    )
    group = inspect.getsource(cm.merge_group_body)
    assert (
        group.index("require_real_multipass_authority()")
        < group.index("_require_expected_binding(")
        < group.index("_admit_merge_step(")
        < group.index("attempt_root.mkdir(")
    )
    orchestrator = inspect.getsource(cm.run_multipass_f0)
    assert (
        orchestrator.index("require_real_multipass_authority()")
        < orchestrator.index("accepted_multipass_storage_requirements()")
        < orchestrator.index("require_sqlite_temp_binding(")
        < orchestrator.index("multipass_root.mkdir(")
        < orchestrator.index("_record_storage_plan(")
    )


def test_c1930_w10_counters_and_the_durable_binding_travel_through_a_whole_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    database, tree = c1.build_world(tmp_path, members=9, shards=1, **SHAPE)
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, tmp_path / "run", database, tree)
    result = cm.run_multipass_f0(
        plan=plan,
        internal_root=run["chunk_root"],
        operational_catalog=database,
        multipass_root=run["base"] / "orch",
        run_id="c1930",
    )
    counters = tuple(
        int(result.receipt[name])  # type: ignore[call-overload]
        for name in (
            "first_witness_accessions_corrected",
            "first_witness_rows_staged",
            "evidence_members_corrected",
            "evidence_delta",
        )
    )
    assert counters == (3, 35, 4, 25)
    # The durable record: contract /2, the measured binding, the sealed identity -- recoverable.
    stored = json.loads((run["base"] / "orch" / cm.STORAGE_PLAN_FILENAME).read_text())
    recovered = ct.MultipassStoragePlan.from_document(stored)
    assert recovered == result.storage_plan
    assert recovered.contract == CURRENT_CONTRACT
    stat = (tmp_path / "sqlite-temp").stat()
    assert (
        recovered.sqlite_temp_binding.temp_root_device,
        recovered.sqlite_temp_binding.temp_root_inode,
    ) == (
        stat.st_dev,
        stat.st_ino,
    )
    assert recovered.sqlite_temp_binding.temp_volume_uuid == c13.SYNTHETIC_MERGE_VOLUME
    assert str(tmp_path) not in json.dumps(stored)
    # Every child request carried that binding, and every child remeasured and matched it.
    for request_path in sorted((run["base"] / "orch").rglob("*-request.json")):
        request = json.loads(request_path.read_text(encoding="utf-8"))
        assert request["expected_sqlite_temp_binding"] == stored["sqlite_temp_binding"]
    # A restart with the SAME temporary root continues; with a DIFFERENT one it refuses on the
    # recorded plan, before any child starts.
    other = tmp_path / "other-temp"
    other.mkdir()
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(other))
    with pytest.raises(cm.ChunkMultipassError, match="storage plan already recorded"):
        cm.run_multipass_f0(
            plan=plan,
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=run["base"] / "orch",
            run_id="c1930-restart",
        )
    # With the SAME root the recorded plan is the one recomputed, and the run resumes and reuses
    # every intermediate rather than rebuilding (the accepted r02 semantics, binding included).
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(tmp_path / "sqlite-temp"))
    resumed = cm.run_multipass_f0(
        plan=plan,
        internal_root=run["chunk_root"],
        operational_catalog=database,
        multipass_root=run["base"] / "orch-resume",
        run_id="c1930-same-root",
    )
    assert resumed.storage_plan.sqlite_temp_binding == result.storage_plan.sqlite_temp_binding
    # The independent restatement is read LAST: its read-only opens leave -wal/-shm beside the
    # chunk catalogs, which a later manifest verification would rightly refuse.
    assert counters == sem.whole_f0_counters(c13.chunk_directories(run))
