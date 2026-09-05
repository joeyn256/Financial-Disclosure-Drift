"""D151-C31R2-R20-C1: S18 recovery, its publication protocol, and the runtime tool manifest.

What is proved here, over the committed synthetic worlds every accepted multipass test uses:

* R20-MAJOR-1 -- an abort inside the S18 sidecar BUILD no longer leaves a partial artifact at
  the canonical name. The build happens inside the stage attempt's own create-once directory;
  a watchdog abort, an instrumentation refusal and a genuine process death each leave the
  canonical name absent and the failed attempt preserved, and a later authorized invocation
  completes. A finished staged artifact that was never published is reused without rebuilding,
  and a published artifact whose applied unit never committed converges through AUTHENTICATE;
* R20-MINOR-5, folded -- refusing a partial or conflicting canonical sidecar no longer creates
  the ``-wal`` and ``-shm`` the refusal itself used to leave behind. The whole inventory of the
  world directory is unchanged by the refusal, inode, size and mtime included;
* §6 -- the watchdog samples the log the statements are actually growing: the staged sidecar's,
  never an absent canonical pathname. BUILD and AUTHENTICATE coverage stay exact, and a
  reuse-only attempt fabricates no BUILD journal;
* R20-MAJOR-2 -- the declared runtime influence set covers the five further first-party modules
  a traced successor invocation executes. Every declared member's bytes participate in the
  identity, and a changed member refuses at the manifest gate before any semantic mutation;
* the publication primitive itself -- one hard link, same filesystem, never an overwrite.

The deferred R20 minors (1 through 4) are untouched by design and are not asserted here.
"""

from __future__ import annotations

import ast
import errno
import json
import os
import sqlite3
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_r19_cross_store_recovery as cross  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
import test_d151_r19b_statement_progress as sp  # noqa: E402

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import working_catalog as wc  # noqa: E402
from disclosure_drift.m3.chunk_evidence import file_sha256  # noqa: E402
from disclosure_drift.m3.compact_evidence import COMPACT_EVIDENCE_SIDECAR_FILENAME  # noqa: E402


@pytest.fixture(autouse=True)
def _seams(tmp_path: Path) -> Any:
    """The accepted seams for BOTH routes in one process, as the cross-store module opens them."""
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    c13.open_synthetic_multipass(patcher, temp_root=tmp_path / "sqlite-temp")
    patcher.setattr(ewr, "macos_volume_identity", c13.synthetic_volume_provider())
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# Shared readers -- every one of them observes and changes nothing
# ==========================================================================
SIDECAR_NAMES = (
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    COMPACT_EVIDENCE_SIDECAR_FILENAME + "-wal",
    COMPACT_EVIDENCE_SIDECAR_FILENAME + "-shm",
)


def _inventory(directory: Path) -> dict[str, tuple[int, int, int, str | None]]:
    """Every regular file of one directory by name: inode, size, mtime and content digest."""
    out: dict[str, tuple[int, int, int, str | None]] = {}
    for path in sorted(directory.iterdir()):
        status = path.lstat()
        digest = file_sha256(path)[0] if path.is_file() and not path.is_symlink() else None
        out[path.name] = (status.st_ino, status.st_size, status.st_mtime_ns, digest)
    return out


def _wal_mode_header(path: Path) -> bool:
    """Whether a SQLite main file's header declares write-ahead logging.

    Bytes 18 and 19 are the file-format write and read versions: 2 is WAL, 1 is the rollback
    journal. It matters here because only a WAL-mode database makes a reader build the ``-wal``
    and ``-shm`` this correction must not create, so a rollback-mode fixture cannot tell a
    ``mode=ro`` open from an ``immutable=1`` one.
    """
    with path.open("rb") as handle:
        header = handle.read(20)
    return header[18] == 2 and header[19] == 2


def _sidecar_state(world: Path) -> dict[str, int | None]:
    return {
        name: (world / name).stat().st_size if (world / name).exists() else None
        for name in SIDECAR_NAMES
    }


def _s18_stage_directory(catalog: Path) -> Path:
    plan = cm._read_stored_stage_plan(r19.readonly(catalog))
    stage = next(item for item in plan.stages if item.stage_id == "S18")
    return plan.statement_progress_root / cm._stage_directory_name(stage)


def _attempts(catalog: Path) -> list[Path]:
    directory = _s18_stage_directory(catalog)
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if path.is_dir())


def _staged(attempt: Path) -> Path:
    return attempt / cm._S18_STAGING_SIDECAR_FILENAME


def _manifest(attempt: Path) -> Path:
    return attempt / cm._S18_STAGING_MANIFEST_FILENAME


def _units(catalog: Path) -> dict[str, cm.AppliedUnit]:
    return {
        unit.stage_id: unit
        for unit in (cm.AppliedUnit.from_row(row) for row in r19.applied_units(catalog))
    }


def _s18_witness(catalog: Path) -> dict[str, Any]:
    return dict(_units(catalog)["S18"].outcome_witness)


def _s18_statements(catalog: Path) -> list[dict[str, Any]]:
    execution_set = _units(catalog)["S18"].statement_execution_set
    assert execution_set is not None
    return [dict(item) for item in execution_set["statements"]]  # type: ignore[union-attr]


def _decision(catalog: Path, attempt_ordinal: int) -> dict[str, Any]:
    """The journaled path decision of one S18 attempt, read back from its sealed journal."""
    attempt = _s18_stage_directory(catalog) / f"attempt-{attempt_ordinal:03d}"
    journals = sorted(attempt.glob("statement-*.jsonl"))
    reading = wc.read_statement_journal(journals[0])
    assert reading.events[0]["statement_id"].endswith("path_decision")  # type: ignore[union-attr]
    return dict(reading.events[0]["decision"])  # type: ignore[arg-type]


def _committed_prefix(catalog: Path, receipt_root: Path) -> dict[str, Any]:
    """Every unit identity and receipt digest committed BEFORE S18, by stage ordinal."""
    plan = cm._read_stored_stage_plan(r19.readonly(catalog))
    s18 = next(item for item in plan.stages if item.stage_id == "S18").ordinal
    units = {
        unit.stage_id: unit.unit_identity
        for unit in (cm.AppliedUnit.from_row(row) for row in r19.applied_units(catalog))
        if unit.stage_ordinal < s18
    }
    receipts = {
        path.name: file_sha256(path)[0]
        for path in r19.receipt_files(receipt_root)
        if int(path.name.split("-")[1]) < s18
    }
    return {"units": units, "receipts": receipts}


def _to_s17c(estate: r19.SuccessorWorld) -> None:
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S17C"))
    assert outcome.completed_stage_ids[-1] == "S17C"


def _watchdog_abort(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the real COMPACT_EVIDENCE watchdog to trip on the first sidecar statement."""
    monkeypatch.setattr(cm, "_monotonic_ns", sp.fast_clock())
    real_growth = cm._TransactionWatch.growth

    def growth(self: Any, observation: Any) -> int:
        value = int(real_growth(self, observation))
        if self.role == cm._ROLE_COMPACT_EVIDENCE:
            return int(r19.SYNTHETIC_OBSERVABILITY["wal_watchdog_max_uncommitted_frames"]) + 7
        return value

    monkeypatch.setattr(cm._TransactionWatch, "growth", growth)


def _instrumentation_abort(monkeypatch: pytest.MonkeyPatch, *, after: int = 6) -> None:
    """Fail the peak-RSS helper once the S18 build is under way."""
    calls = {"n": 0}
    real = cm.process_peak_resident_bytes

    def flaky() -> int | None:
        calls["n"] += 1
        return None if calls["n"] > after else real()

    monkeypatch.setattr(cm, "process_peak_resident_bytes", flaky)


# ==========================================================================
# 1 -- the normal build still produces the canonical sidecar and its semantics
# ==========================================================================
def test_r01_a_normal_build_publishes_the_same_canonical_sidecar_and_semantics(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert outcome.completed_stage_ids[-1] == "S18"
    sidecar = estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    assert sidecar.is_file() and not sidecar.is_symlink()
    assert _sidecar_state(estate.world)[SIDECAR_NAMES[1]] is None
    assert _sidecar_state(estate.world)[SIDECAR_NAMES[2]] is None
    witness = _s18_witness(estate.catalog)
    assert estate.legacy is not None
    legacy = estate.legacy["final"].as_record()
    assert witness["completeness_digest"] == legacy["completeness_digest"]
    assert witness["member_manifest_digest"] == legacy["member_manifest_digest"]
    assert (witness["sidecar_sha256"], witness["sidecar_byte_length"]) == file_sha256(sidecar)
    # The publication record: one hard link from this attempt, and the staging name is gone.
    publication = dict(witness["sidecar_publication"])
    assert publication["protocol"] == wc.STAGED_ARTIFACT_PUBLICATION_PROTOCOL
    assert publication["published"] is True
    assert publication["reused_without_rebuild"] is False
    assert publication["staging_name_removed"] is True
    assert publication["staging_name_removal_error"] is None
    assert publication["canonical_inode"] == sidecar.stat().st_ino
    assert publication["byte_length"] == witness["sidecar_byte_length"]
    assert publication["retained_attempt_bytes"] == 0
    assert sidecar.stat().st_nlink == 1
    attempts = _attempts(estate.catalog)
    assert [path.name for path in attempts] == ["attempt-000"]
    assert not _staged(attempts[0]).exists()
    # The completion manifest is retained as the durable statement that this attempt finished.
    sealed = json.loads(_manifest(attempts[0]).read_bytes())
    assert sealed["contract"] == cm._S18_STAGING_CONTRACT
    assert sealed["attempt_ordinal"] == 0
    assert sealed["completeness_digest"] == witness["completeness_digest"]
    assert sealed["input_identities"] == [
        str(item["manifest_digest"])
        for item in cm._read_stored_stage_plan(r19.readonly(estate.catalog)).intermediates
    ]


# ==========================================================================
# 2, 3 -- a watchdog abort and an instrumentation refusal during the BUILD
# ==========================================================================
@pytest.mark.parametrize("cause", ["WATCHDOG_ABORT", "INSTRUMENTATION_FAILURE"])
def test_r02_r03_an_abort_during_the_build_leaves_no_canonical_sidecar_and_a_retry_completes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cause: str
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    _to_s17c(estate)
    before_world = _inventory(estate.world)
    before_prefix = _committed_prefix(estate.catalog, estate.receipt_root)
    if cause == "WATCHDOG_ABORT":
        _watchdog_abort(monkeypatch)
    else:
        _instrumentation_abort(monkeypatch)
    with pytest.raises(cm.ChunkMultipassError) as info:
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert cause in str(info.value)
    monkeypatch.undo()

    # The canonical name is untouched: no sidecar, and no residue beside one.
    assert _sidecar_state(estate.world) == dict.fromkeys(SIDECAR_NAMES)
    assert _inventory(estate.world) == before_world
    assert r19.stage_ids(estate.catalog)[-1] == "S17C"
    # The failed attempt is preserved, unfinished and unpromotable: bytes, but no manifest.
    attempts = _attempts(estate.catalog)
    assert [path.name for path in attempts] == ["attempt-000"]
    assert _staged(attempts[0]).is_file()
    retained = _staged(attempts[0]).stat().st_size
    assert retained > 0
    assert not _manifest(attempts[0]).exists()

    # A later authorized invocation allocates a NEW attempt and completes. Nothing about the
    # inputs, the bound watchdog or the StagePlan moved between the failure and the retry.
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert outcome.completed_stage_ids[-1] == "S18"
    assert (estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME).is_file()
    assert [path.name for path in _attempts(estate.catalog)] == ["attempt-000", "attempt-001"]
    # The preserved failed attempt is exactly where it was, and is reported for storage planning.
    assert _staged(_attempts(estate.catalog)[0]).stat().st_size == retained
    decision = _decision(estate.catalog, 1)
    assert decision["selected_path"] == "BUILD"
    # Nothing about the run, the StagePlan, the registry, the stage or the inputs moved between
    # the failed attempt and its retry: recovery is proved under one fixed binding.
    assert _decision(estate.catalog, 0)["staging"]["binding"] == decision["staging"]["binding"]
    assert decision["staging"]["retained_attempt_bytes"] == retained
    published = dict(_s18_witness(estate.catalog)["sidecar_publication"])
    assert published["retained_attempt_bytes"] == retained
    assert decision["staging"]["reused_attempt_ordinal"] is None
    assert decision["staging"]["retained_attempts"][0]["complete"] is False
    assert decision["staging"]["retained_attempts"][0]["has_completion_manifest"] is False
    # 9 -- every unit and receipt committed before S18 is byte-for-byte what it was.
    after_prefix = _committed_prefix(estate.catalog, estate.receipt_root)
    assert after_prefix == before_prefix


# ==========================================================================
# 4 -- a genuine process death during the BUILD, in a fresh interpreter
# ==========================================================================
KILL_MID_BUILD = (
    "import os as _os;"
    "_n=[0];_orig=cm._StageInstrumentation.sidecar_runner;"
    "cm._StageInstrumentation.sidecar_runner=("
    "lambda self,c,s,p,k,o: _os._exit(9) if (_n.__setitem__(0,_n[0]+1) or _n[0]) > 2 "
    "else _orig(self,c,s,p,k,o));"
)


def test_r04_a_process_death_during_the_build_leaves_no_canonical_sidecar_and_a_retry_completes(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    _to_s17c(estate)
    before_world = _inventory(estate.world)
    before_prefix = _committed_prefix(estate.catalog, estate.receipt_root)
    killed = r19.spawn_production(
        tmp_path,
        r19.production_request(estate, stop_after="S18"),
        label="killed",
        extra=KILL_MID_BUILD,
    )
    assert killed["returncode"] == -9 or killed["returncode"] == 9, killed

    assert _sidecar_state(estate.world) == dict.fromkeys(SIDECAR_NAMES)
    assert _inventory(estate.world) == before_world
    assert r19.stage_ids(estate.catalog)[-1] == "S17C"
    attempts = _attempts(estate.catalog)
    assert _staged(attempts[-1]).is_file() and not _manifest(attempts[-1]).exists()
    # A killed writer leaves a live log beside the staged artifact; that is exactly why the
    # candidate is classified incomplete rather than adopted, and it is never checkpointed here.
    assert (attempts[-1] / (cm._S18_STAGING_SIDECAR_FILENAME + "-wal")).exists()
    staged_before = _inventory(attempts[-1])

    resumed = r19.spawn_production(
        tmp_path, r19.production_request(estate, stop_after="S18"), label="resumed"
    )
    assert resumed["returncode"] == 0, resumed["stderr"][-3000:]
    assert resumed["result"]["stages"][-1] == "S18"
    assert (estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME).is_file()
    assert _inventory(attempts[-1]) == staged_before
    assert _decision(estate.catalog, 1)["selected_path"] == "BUILD"
    assert _committed_prefix(estate.catalog, estate.receipt_root) == before_prefix


# ==========================================================================
# 5 -- a complete staged artifact is published without being rebuilt
# ==========================================================================
def test_r05_a_complete_staged_artifact_is_reused_and_published_without_a_rebuild(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path)
    _to_s17c(estate)
    fired = {"done": False}

    def raise_once(staged: Path, canonical: Path) -> Any:
        if not fired["done"]:
            fired["done"] = True
            message = "injected crash after the completion manifest, before the link"
            raise RuntimeError(message)
        return wc.publish_staged_artifact(staged, canonical)

    monkeypatch.setattr(cm, "publish_staged_artifact", raise_once)
    with pytest.raises(RuntimeError, match="before the link"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    monkeypatch.undo()
    assert not (estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME).exists()
    first = _attempts(estate.catalog)[0]
    assert _staged(first).is_file() and _manifest(first).is_file()
    sealed = json.loads(_manifest(first).read_bytes())

    # The retry rebuilds nothing: _merge_sidecar may not run at all.
    monkeypatch.setattr(cm, "_merge_sidecar", cross._never("_merge_sidecar"))
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert outcome.completed_stage_ids[-1] == "S18"
    sidecar = estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    assert sidecar.is_file() and not _staged(first).exists()
    witness = _s18_witness(estate.catalog)
    publication = dict(witness["sidecar_publication"])
    assert publication["published"] is True
    assert publication["reused_without_rebuild"] is True
    assert publication["from_attempt_ordinal"] == 0
    assert publication["retained_attempt_bytes"] == 0
    assert witness["completeness_digest"] == sealed["completeness_digest"]
    assert witness["member_manifest_digest"] == sealed["member_manifest_digest"]
    assert estate.legacy is not None
    assert (
        witness["completeness_digest"] == estate.legacy["final"].as_record()["completeness_digest"]
    )
    # 10 -- reuse is AUTHENTICATE, and no BUILD journal is fabricated for it.
    decision = _decision(estate.catalog, 1)
    assert decision["selected_path"] == "AUTHENTICATE"
    assert decision["staging"]["authenticated_artifact"] == cm._S18_SOURCE_STAGED
    assert decision["staging"]["reused_attempt_ordinal"] == 0
    assert decision["sidecar_file_state"]["lstat_class"] == "absent"
    operations = [str(item["operation"]) for item in _s18_statements(estate.catalog)]
    assert not [item for item in operations if "merge_sidecar" in item or "member_deltas" in item]
    assert operations[0] == "path_decision"


# ==========================================================================
# 6 -- published, but the applied unit never committed
# ==========================================================================
def test_r06_a_published_sidecar_without_its_unit_converges_through_authenticate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path)
    cross._raise_once_for(monkeypatch, cm._BINDING_SIDECAR)
    with pytest.raises(RuntimeError, match="sidecar binding"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    sidecar = estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    assert sidecar.is_file() and r19.stage_ids(estate.catalog)[-1] == "S17C"
    published = _inventory(estate.world)[COMPACT_EVIDENCE_SIDECAR_FILENAME]

    monkeypatch.setattr(cm, "_merge_sidecar", cross._never("_merge_sidecar"))
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert outcome.completed_stage_ids[-1] == "S18"
    # The canonical artifact is the same inode and the same bytes: nothing was republished.
    assert _inventory(estate.world)[COMPACT_EVIDENCE_SIDECAR_FILENAME] == published
    decision = _decision(estate.catalog, 1)
    assert decision["selected_path"] == "AUTHENTICATE"
    assert decision["staging"]["authenticated_artifact"] == cm._S18_SOURCE_CANONICAL
    assert decision["staging"]["watched_database_is_canonical"] is True
    publication = dict(_s18_witness(estate.catalog)["sidecar_publication"])
    assert publication["published"] is False
    assert "already present" in str(publication["reason"])


# ==========================================================================
# 7 -- a conflicting canonical destination is never overwritten
# ==========================================================================
def test_r07_the_publication_never_overwrites_an_existing_canonical_target(
    tmp_path: Path,
) -> None:
    staged = tmp_path / "staged.sqlite3"
    staged.write_bytes(b"staged-artifact")
    canonical = tmp_path / "canonical.sqlite3"
    canonical.write_bytes(b"someone-elses-artifact")
    before = _inventory(tmp_path)
    with pytest.raises(wc.WorkingCatalogError, match="NEVER overwritten"):
        wc.publish_staged_artifact(staged, canonical)
    assert _inventory(tmp_path) == before
    # The kernel-level guarantee, proved with the prior existence check removed: the link
    # itself refuses, so a caller whose check raced still cannot overwrite anything.
    with pytest.raises(FileExistsError):
        os.link(staged, canonical)
    assert _inventory(tmp_path) == before


def test_r07b_the_publication_refuses_a_logged_artifact_a_foreign_device_and_a_non_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = tmp_path / "world"
    world.mkdir()
    staged = tmp_path / "staged.sqlite3"
    staged.write_bytes(b"staged-artifact")
    for suffix in wc.CLOSED_DATABASE_SIDECAR_SUFFIXES:
        residue = staged.with_name(staged.name + suffix)
        residue.write_bytes(b"")
        with pytest.raises(wc.WorkingCatalogError, match="closed, self-contained"):
            wc.publish_staged_artifact(staged, world / "published.sqlite3")
        residue.unlink()
    assert not (world / "published.sqlite3").exists()
    # A directory is not an artifact, and an absent one is refused rather than assumed.
    with pytest.raises(wc.WorkingCatalogError, match="not a regular file"):
        wc.publish_staged_artifact(world, tmp_path / "published.sqlite3")
    with pytest.raises(wc.WorkingCatalogError, match="could not be measured"):
        wc.publish_staged_artifact(tmp_path / "absent.sqlite3", tmp_path / "published.sqlite3")
    # A canonical parent on another device refuses BEFORE the link, so a cross-device
    # publication never gets as far as EXDEV with a finished artifact already written.
    real_stat = Path.stat
    foreign = staged.lstat().st_dev + 1

    def stat_with_foreign_device(self: Path, *args: Any, **kwargs: Any) -> Any:
        status = real_stat(self, *args, **kwargs)
        if self != world:
            return status
        fields = list(status)
        fields[2] = foreign  # st_dev, in os.stat_result's ten-field ordering
        return os.stat_result(fields)

    monkeypatch.setattr(Path, "stat", stat_with_foreign_device)
    with pytest.raises(wc.WorkingCatalogError, match="different devices"):
        wc.publish_staged_artifact(staged, world / "published.sqlite3")
    monkeypatch.undo()
    assert not (world / "published.sqlite3").exists()
    assert staged.read_bytes() == b"staged-artifact"


def test_r07c_the_publication_is_one_hard_link_that_survives_its_own_interruption(
    tmp_path: Path,
) -> None:
    world = tmp_path / "world"
    world.mkdir()
    staged = tmp_path / "attempt" / "staged.sqlite3"
    staged.parent.mkdir()
    staged.write_bytes(b"a finished artifact")
    canonical = world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    record = wc.publish_staged_artifact(staged, canonical)
    assert record["protocol"] == wc.STAGED_ARTIFACT_PUBLICATION_PROTOCOL
    assert record["staged_inode"] == record["canonical_inode"] == canonical.stat().st_ino
    assert record["byte_length"] == len(b"a finished artifact")
    assert record["staging_name_removed"] is True
    assert canonical.read_bytes() == b"a finished artifact"
    assert not staged.exists() and canonical.stat().st_nlink == 1
    # The interrupted-between-link-and-removal state: two names, one inode, no extra bytes.
    second = tmp_path / "attempt" / "second.sqlite3"
    second.write_bytes(b"another finished artifact")
    other = world / "other.sqlite3"
    os.link(second, other)
    assert second.stat().st_ino == other.stat().st_ino
    assert other.stat().st_nlink == 2


# ==========================================================================
# 8 -- refusing a partial canonical sidecar changes nothing at all
# ==========================================================================
def test_r08_a_partial_canonical_sidecar_is_refused_with_no_side_effect_whatever(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    _to_s17c(estate)
    # The partial artifact a genuinely interrupted build leaves: a WAL-mode database, closed.
    # Its shape matters -- a rollback-journal database cannot distinguish a `mode=ro` open from
    # an `immutable=1` one, because only a WAL-mode header makes a reader build the -wal and
    # -shm this refusal must not create.
    _instrumentation_abort(monkeypatch)
    with pytest.raises(cm.ChunkMultipassError, match="INSTRUMENTATION_FAILURE"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    monkeypatch.undo()
    sidecar = estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    sidecar.write_bytes(_staged(_attempts(estate.catalog)[0]).read_bytes())
    assert _wal_mode_header(sidecar), "the fixture must be a WAL-mode database to be meaningful"
    before = _inventory(estate.world)
    assert set(before) & {SIDECAR_NAMES[1], SIDECAR_NAMES[2]} == set()

    with pytest.raises(cm.ChunkMultipassError, match="preserved exactly as it is"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    # R20-MINOR-5, folded: the refusal adds no -wal and no -shm, and moves no inode, size or
    # mtime of anything already there. The whole directory is what it was.
    assert _inventory(estate.world) == before
    assert r19.stage_ids(estate.catalog)[-1] == "S17C"
    decision = _decision(estate.catalog, 1)
    assert decision["selected_path"] is None
    assert decision["sidecar_file_state"]["complete"] is False
    # And the hand-made rollback-journal shape the accepted tests use refuses identically.
    other = r19.prepare(tmp_path / "rollback", legacy=False)
    _to_s17c(other)
    handle = sqlite3.connect(other.world / COMPACT_EVIDENCE_SIDECAR_FILENAME)
    handle.execute("CREATE TABLE compact_source_evidence (source_observation_id TEXT)")
    handle.close()
    other_before = _inventory(other.world)
    with pytest.raises(cm.ChunkMultipassError, match="preserved exactly as it is"):
        cm.run_successor_multipass_final(r19.production_request(other, stop_after="S18"))
    assert _inventory(other.world) == other_before


def test_r09_a_logged_candidate_is_never_declared_complete_by_a_log_blind_read(
    tmp_path: Path,
) -> None:
    """The classifier refuses a logged artifact on metadata, and reads only a logless one."""
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    sidecar = estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    assert _wal_mode_header(sidecar)
    context = cm._resolve_successor_context(
        r19.production_request(estate, stop_after="S18"),
        cm._mint_successor_route_proof(
            cm.SUCCESSOR_ROUTE_PRODUCTION, gate=lambda: None, gate_name="t"
        ),
    )
    # POSITIVE CONTROL: these exact bytes ARE a complete sidecar, and classifying them creates
    # nothing beside them. Without this, the refusal below could be caused by anything.
    logless = tmp_path / "logless" / COMPACT_EVIDENCE_SIDECAR_FILENAME
    logless.parent.mkdir()
    logless.write_bytes(sidecar.read_bytes())
    assert cm._sidecar_is_complete(logless, context) is True
    assert sorted(path.name for path in logless.parent.iterdir()) == [
        COMPACT_EVIDENCE_SIDECAR_FILENAME
    ]
    # The same complete main file, with a log beside it: the artifact is not self-contained,
    # so it is refused on metadata alone and is never opened. A log-blind read of the main
    # file would have declared it complete -- which is exactly what must not happen.
    logged = tmp_path / "logged" / COMPACT_EVIDENCE_SIDECAR_FILENAME
    logged.parent.mkdir()
    logged.write_bytes(sidecar.read_bytes())
    log = logged.with_name(logged.name + "-wal")
    log.write_bytes(b"\x00" * 4096)
    before = _inventory(logged.parent)
    assert cm._sidecar_is_complete(logged, context) is False
    assert _inventory(logged.parent) == before
    # An index without a log is refused the same way, and a zero-length log too.
    for residue in (logged.name + "-shm", logged.name + "-journal"):
        log.unlink()
        logged.with_name(residue).write_bytes(b"")
        assert cm._sidecar_is_complete(logged, context) is False
        logged.with_name(residue).unlink()
        log.write_bytes(b"\x00" * 4096)


# ==========================================================================
# 11 -- the watchdog samples the log the statements are actually growing
# ==========================================================================
def test_r11_the_watchdog_samples_the_staging_log_not_the_canonical_pathname(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    _to_s17c(estate)
    observed: list[Path] = []
    real_observe = cm.observe_wal

    def recording(path: Path, *, expected_page_size: int) -> Any:
        observed.append(Path(path))
        return real_observe(path, expected_page_size=expected_page_size)

    monkeypatch.setattr(cm, "observe_wal", recording)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert outcome.completed_stage_ids[-1] == "S18"
    monkeypatch.undo()

    canonical_wal = estate.world / (COMPACT_EVIDENCE_SIDECAR_FILENAME + "-wal")
    staged_wal = _attempts(estate.catalog)[0] / (cm._S18_STAGING_SIDECAR_FILENAME + "-wal")
    assert staged_wal in observed
    assert canonical_wal not in observed
    # It watched a live log rather than an absent name: some sealed BUILD statement observed a
    # nonzero write-ahead log on the compact-evidence role.
    sidecar_statements = [
        item
        for item in _s18_statements(estate.catalog)
        if item["database_role"] == "COMPACT_EVIDENCE"
    ]
    lengths = []
    for statement in sidecar_statements:
        plan = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
        reading = wc.read_statement_journal(
            plan.statement_progress_root / str(statement["journal_relative_path"])
        )
        measurements = reading.events[0].get("measurements")
        if isinstance(measurements, dict):
            lengths.append(int(measurements["wal"]["byte_length"]))
    assert max(lengths) > 0
    assert _decision(estate.catalog, 0)["staging"]["watched_database_is_canonical"] is False
    assert (
        _decision(estate.catalog, 0)["staging"]["watched_database_name"]
        == cm._S18_STAGING_SIDECAR_FILENAME
    )


def test_r11b_the_abort_record_reports_the_log_the_aborted_statements_were_growing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    _to_s17c(estate)
    _watchdog_abort(monkeypatch)
    with pytest.raises(cm.ChunkMultipassError, match="WATCHDOG_ABORT"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    monkeypatch.undo()
    abort = json.loads(
        (_s18_stage_directory(estate.catalog) / "abort-attempt-000.json").read_bytes()
    )
    assert abort["cause"] == "WATCHDOG_ABORT"
    assert abort["stage_id"] == "S18" and abort["applied_unit_inserted"] is False
    # The record names the database its ABORT_WAL_NORMALIZED was measured against, and it is
    # the staged artifact the aborted statements were growing -- not the canonical pathname.
    assert abort["abort_wal_probed_database"] == cm._S18_STAGING_SIDECAR_FILENAME
    assert abort["ABORT_WAL_NORMALIZED"] is True
    assert not (estate.world / (COMPACT_EVIDENCE_SIDECAR_FILENAME + "-wal")).exists()


# ==========================================================================
# 10 -- exact BUILD and AUTHENTICATE coverage, both routes
# ==========================================================================
BUILD_ONLY = (
    "member_deltas.create_temp",
    "member_deltas.summary",
    "merge_sidecar.insert_members",
    "merge_sidecar.summary",
    "merge_sidecar.digest_replay",
)
UNCONDITIONAL = (
    "path_decision",
    "sidecar.member_manifest_rows",
    "sidecar.identity_fold:compact_source_evidence",
    "sidecar.identity_fold:compact_source_members",
    "sidecar.identity_fold:compact_resolution_evidence",
    "sidecar.identity_fold:compact_corroboration_evidence",
)


def test_r10_build_and_authenticate_coverage_stay_exact_across_a_staged_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    execution_set = _units(estate.catalog)["S18"].statement_execution_set
    assert execution_set is not None
    assert execution_set["selected_path"] == "BUILD"
    coverage = {
        str(item["statement_id"]).removeprefix("S18/"): item["expected"]
        for item in execution_set["coverage"]  # type: ignore[union-attr]
    }
    assert set(coverage) == set(BUILD_ONLY) | set(UNCONDITIONAL)
    observed = [str(item["operation"]) for item in _s18_statements(estate.catalog)]
    assert len(observed) == len(BUILD_ONLY) + len(UNCONDITIONAL)

    # A reuse-only attempt, over a fresh estate: exactly the unconditional set, nothing more.
    other = r19.prepare(tmp_path / "reuse", legacy=False)
    _to_s17c(other)
    fired = {"done": False}

    def raise_once(staged: Path, canonical: Path) -> Any:
        if not fired["done"]:
            fired["done"] = True
            message = "injected crash before the link"
            raise RuntimeError(message)
        return wc.publish_staged_artifact(staged, canonical)

    monkeypatch.setattr(cm, "publish_staged_artifact", raise_once)
    with pytest.raises(RuntimeError, match="before the link"):
        cm.run_successor_multipass_final(r19.production_request(other, stop_after="S18"))
    monkeypatch.undo()
    monkeypatch.setattr(cm, "_merge_sidecar", cross._never("_merge_sidecar"))
    cm.run_successor_multipass_final(r19.production_request(other, stop_after="S18"))
    reuse_set = _units(other.catalog)["S18"].statement_execution_set
    assert reuse_set is not None
    assert reuse_set["selected_path"] == "AUTHENTICATE"
    reuse_coverage = {
        str(item["statement_id"]).removeprefix("S18/")
        for item in reuse_set["coverage"]  # type: ignore[union-attr]
    }
    assert reuse_coverage == set(UNCONDITIONAL)
    assert [str(item["operation"]) for item in _s18_statements(other.catalog)] == list(
        UNCONDITIONAL
    )


# ==========================================================================
# 12 -- the terminal, its semantics and the existing R21 gate
# ==========================================================================
def test_r12_the_terminal_is_semantically_the_legacy_final_and_stays_r21_ready(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached and outcome.final_receipt is not None
    assert list(outcome.completed_stage_ids) == list(r19.PRODUCTION_STAGE_IDS_10)
    assert estate.legacy is not None
    legacy = estate.legacy["final"].as_record()
    assert r19.counters(legacy) == r19.counters(outcome.final_receipt)
    witness = _s18_witness(estate.catalog)
    assert witness["completeness_digest"] == legacy["completeness_digest"]
    assert witness["member_manifest_digest"] == legacy["member_manifest_digest"]
    ready = cm.require_r21_observability_ready(
        outcome.final_receipt, stage_receipt_root=estate.receipt_root
    )
    assert ready["r21_observability_ready"] is True
    assert ready["current_observability_gap_count"] == 0
    # The world's own artifact manifest never names a staging artifact: staging lives in the
    # receipt estate, which is disjoint from the world by contract.
    names = {str(entry["relative_path"]) for entry in outcome.final_receipt["manifest"]["entries"]}
    assert COMPACT_EVIDENCE_SIDECAR_FILENAME in names
    assert not [name for name in names if "staging" in name]


# ==========================================================================
# Both routes -- the calibration successor recovers identically
# ==========================================================================
def test_r13_the_calibration_route_recovers_from_an_s18_abort_the_same_way(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = cross.calibration_estate(tmp_path)
    world = Path(cross.calibration_request(estate).world_directory)
    catalog = world / wc.WORKING_CATALOG_FILENAME
    cross.run_calibration_in_process(estate, cross.calibration_request(estate, stop_after="S17C"))
    assert r19.stage_ids(catalog)[-1] == "S17C"
    before_world = _inventory(world)

    _instrumentation_abort(monkeypatch)
    with pytest.raises(cm.ChunkMultipassError, match="INSTRUMENTATION_FAILURE"):
        cross.run_calibration_in_process(
            estate, cross.calibration_request(estate, stop_after="S18")
        )
    monkeypatch.undo()
    assert _inventory(world) == before_world
    assert not (world / COMPACT_EVIDENCE_SIDECAR_FILENAME).exists()
    assert r19.stage_ids(catalog)[-1] == "S17C"
    attempts = _attempts(catalog)
    assert _staged(attempts[-1]).is_file() and not _manifest(attempts[-1]).exists()

    outcome = cross.run_calibration_in_process(
        estate, cross.calibration_request(estate, stop_after="S18")
    )
    assert outcome.completed_stage_ids[-1] == "S18"
    assert (world / COMPACT_EVIDENCE_SIDECAR_FILENAME).is_file()
    witness = _s18_witness(catalog)
    assert dict(witness["sidecar_publication"])["published"] is True
    assert _decision(catalog, 1)["staging"]["binding"]["route"] == cm.SUCCESSOR_ROUTE_CALIBRATION


def test_r14_a_staged_artifact_of_another_binding_is_preserved_and_never_adopted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    _to_s17c(estate)
    fired = {"done": False}

    def raise_once(staged: Path, canonical: Path) -> Any:
        if not fired["done"]:
            fired["done"] = True
            message = "injected crash before the link"
            raise RuntimeError(message)
        return wc.publish_staged_artifact(staged, canonical)

    monkeypatch.setattr(cm, "publish_staged_artifact", raise_once)
    with pytest.raises(RuntimeError, match="before the link"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    monkeypatch.undo()
    first = _attempts(estate.catalog)[0]
    sealed = json.loads(_manifest(first).read_bytes())
    # The manifest names another StagePlan: the artifact is no longer THIS attempt's to publish.
    _manifest(first).unlink()
    _manifest(first).write_bytes(
        json.dumps({**sealed, "stage_plan_identity": "0" * 64}).encode("utf-8")
    )
    staged_before = _inventory(first)

    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert outcome.completed_stage_ids[-1] == "S18"
    decision = _decision(estate.catalog, 1)
    assert decision["selected_path"] == "BUILD"
    assert decision["staging"]["reused_attempt_ordinal"] is None
    assert decision["staging"]["retained_attempts"][0]["binds_this_attempt"] is False
    assert decision["staging"]["retained_attempts"][0]["complete"] is False
    assert _inventory(first) == staged_before


def _stage_a_complete_unpublished_attempt(
    estate: r19.SuccessorWorld, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Finish an S18 build and crash between the completion manifest and the link."""
    fired = {"done": False}

    def raise_once(staged: Path, canonical: Path) -> Any:
        if not fired["done"]:
            fired["done"] = True
            message = "injected crash before the link"
            raise RuntimeError(message)
        return wc.publish_staged_artifact(staged, canonical)

    monkeypatch.setattr(cm, "publish_staged_artifact", raise_once)
    with pytest.raises(RuntimeError, match="before the link"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    monkeypatch.undo()
    first = _attempts(estate.catalog)[0]
    assert _staged(first).is_file() and _manifest(first).is_file()
    return first


def test_r15_a_reused_attempt_whose_manifest_disagrees_is_refused_not_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    _to_s17c(estate)
    first = _stage_a_complete_unpublished_attempt(estate, monkeypatch)
    sealed = json.loads(_manifest(first).read_bytes())
    _manifest(first).unlink()
    _manifest(first).write_bytes(
        json.dumps({**sealed, "completeness_digest": "0" * 64}).encode("utf-8")
    )
    before = _inventory(first)
    with pytest.raises(cm.ChunkMultipassError, match="its completion manifest sealed"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    # Nothing is published, and the disagreeing attempt is left exactly where it is.
    assert not (estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME).exists()
    assert _inventory(first) == before
    assert r19.stage_ids(estate.catalog)[-1] == "S17C"


def test_r16_directory_enumeration_order_decides_no_staged_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    _to_s17c(estate)
    first = _stage_a_complete_unpublished_attempt(estate, monkeypatch)
    real_iterdir = Path.iterdir

    def reversed_iterdir(self: Path) -> Any:
        return iter(sorted(real_iterdir(self), reverse=True))

    monkeypatch.setattr(Path, "iterdir", reversed_iterdir)
    monkeypatch.setattr(cm, "_merge_sidecar", cross._never("_merge_sidecar"))
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    monkeypatch.undo()
    assert outcome.completed_stage_ids[-1] == "S18"
    assert not _staged(first).exists()
    publication = dict(_s18_witness(estate.catalog)["sidecar_publication"])
    assert publication["reused_without_rebuild"] is True
    assert publication["from_attempt_ordinal"] == 0
    assert publication["retained_attempt_bytes"] == 0


# ==========================================================================
# R20-MAJOR-2 -- the declared runtime influence set
# ==========================================================================
#: Every first-party module the authenticated R20 trace observed executing a real function
#: inside one `run_successor_multipass_final` call -- probes/successor_invocation_modules.json.
R20_TRACED_MODULES = frozenset(
    {
        "disclosure_drift.m3.canary_phases",
        "disclosure_drift.m3.canary_runtime",
        "disclosure_drift.m3.capacity_plan",
        "disclosure_drift.m3.chunk_consolidation",
        "disclosure_drift.m3.chunk_evidence",
        "disclosure_drift.m3.chunk_execution",
        "disclosure_drift.m3.chunk_multipass",
        "disclosure_drift.m3.chunk_plan",
        "disclosure_drift.m3.chunk_storage",
        "disclosure_drift.m3.chunk_tiering",
        "disclosure_drift.m3.compact_evidence",
        "disclosure_drift.m3.external_working_root",
        "disclosure_drift.m3.offline_parse",
        "disclosure_drift.m3.repository_identity",
        "disclosure_drift.m3.single_source_canary",
        "disclosure_drift.m3.working_catalog",
        "disclosure_drift.sec.census",
        "disclosure_drift.sec.identifiers",
        "disclosure_drift.sec.observation_catalog",
        "disclosure_drift.sec.snapshots",
        "disclosure_drift.storage.catalog",
        "disclosure_drift.storage.sqlite",
    }
)

#: The five R20-MAJOR-2 named, with the reached function that puts each inside the invocation.
R20_ADDED_MODULES = {
    "disclosure_drift.m3.capacity_plan": "plan_fingerprint",
    "disclosure_drift.m3.external_working_root": "require_usable_sqlite_temp_root",
    "disclosure_drift.sec.identifiers": "normalize_cik",
    "disclosure_drift.sec.observation_catalog": "load_observations",
    "disclosure_drift.sec.snapshots": "has_payload",
}


def test_m01_the_declared_influence_set_covers_every_module_the_r20_trace_reached() -> None:
    declared = {str(entry["module"]) for entry in cm._runtime_tool_manifest().entries}
    assert declared >= R20_TRACED_MODULES
    assert set(R20_ADDED_MODULES) <= declared
    # The declared error-path dependency a happy-path trace does not reach stays declared.
    assert "disclosure_drift.errors" in declared
    assert declared == R20_TRACED_MODULES | {"disclosure_drift.errors"}
    # Every module is named once, and every reached function genuinely lives in the module the
    # manifest declares it under.
    modules = [str(entry["module"]) for entry in cm._runtime_tool_manifest().entries]
    assert len(modules) == len(set(modules))
    for module, function in R20_ADDED_MODULES.items():
        source = Path(
            next(file for name, file in cm._TOOL_MANIFEST_MODULES if name == module)
        ).read_text(encoding="utf-8")
        assert f"def {function}(" in source, module


def test_m02_every_declared_members_bytes_participate_in_the_runtime_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = cm._runtime_tool_manifest()
    package_root = Path(str(cm.__file__)).parent.parent
    for index, (module, file) in enumerate(cm._TOOL_MANIFEST_MODULES):
        relative = module.removeprefix("disclosure_drift.").replace(".", "/")
        assert Path(str(file)) == package_root / f"{relative}.py", module
        changed = tmp_path / f"changed-{index:03d}.py"
        changed.write_bytes(Path(str(file)).read_bytes() + b"\n# changed\n")
        monkeypatch.setattr(
            cm,
            "_TOOL_MANIFEST_MODULES",
            tuple(
                (name, str(changed) if name == module else path)
                for name, path in cm._TOOL_MANIFEST_MODULES
            ),
        )
        moved = cm._runtime_tool_manifest()
        assert moved.identity != baseline.identity, module
        assert (
            dict(moved.source_file_digests())[module]
            != dict(baseline.source_file_digests())[module]
        ), module
        monkeypatch.undo()
    assert cm._runtime_tool_manifest().identity == baseline.identity


@pytest.mark.parametrize("module", sorted(R20_ADDED_MODULES))
def test_m03_a_changed_new_member_refuses_at_the_manifest_gate_before_any_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module: str
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    bound = cm._read_stored_stage_plan(r19.readonly(estate.catalog)).tool_manifest_identity
    assert bound == cm._runtime_tool_manifest().identity
    original = next(file for name, file in cm._TOOL_MANIFEST_MODULES if name == module)
    changed = tmp_path / "changed.py"
    changed.write_bytes(Path(str(original)).read_bytes() + b"\n# changed\n")
    monkeypatch.setattr(
        cm,
        "_TOOL_MANIFEST_MODULES",
        tuple(
            (name, str(changed) if name == module else file)
            for name, file in cm._TOOL_MANIFEST_MODULES
        ),
    )
    # The manifest gate itself refuses -- named directly, so no earlier repository-cleanliness
    # or StagePlan refusal can be mistaken for this one.
    with pytest.raises(cm.ChunkMultipassError, match="tool-manifest identity"):
        cm._require_runtime_tool_identity(bound, label="r20-c1")
    # And end to end, the next stage refuses and commits nothing.
    with pytest.raises(
        cm.ChunkMultipassError, match="tool-manifest identity|minimal StagePlan identity"
    ):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S4"))
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2", "S3"]
    monkeypatch.undo()
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S4"))
    assert outcome.completed_stage_ids[-1] == "S4"


def _first_party_modules_executed(work: Callable[[], object]) -> set[str]:
    """Every first-party module that executes a real (non-import) function inside ``work``.

    The tracer is installed only for the duration of the call, so what it records is the
    influence set of THAT invocation rather than of the whole test process. A module-level
    frame is an import, not execution, and is not counted.
    """
    package_root = Path(str(cm.__file__)).parent.parent
    prefix = str(package_root)
    seen: set[str] = set()

    def tracer(frame: Any, event: str, _arg: Any) -> Any:
        if event != "call" or frame.f_code.co_name == "<module>":
            return None
        filename = frame.f_code.co_filename
        if filename.startswith(prefix):
            relative = Path(filename).relative_to(package_root).with_suffix("")
            seen.add("disclosure_drift." + ".".join(relative.parts))
        return None

    sys.settrace(tracer)
    threading.settrace(tracer)
    try:
        work()
    finally:
        sys.settrace(None)
        threading.settrace(None)
    return seen


def test_m06_the_declared_influence_set_is_derived_from_a_traced_invocation(
    tmp_path: Path,
) -> None:
    """R20-MAJOR-2's own required correction: derive the set, do not pin its size.

    The production successor is run end to end under a scoped tracer, and every first-party
    module that actually executes inside it must be declared. This is the check that would
    have caught the five omissions rather than restating them, and it moves on its own when
    the successor's dependencies move.
    """
    estate = r19.prepare(tmp_path, legacy=False)
    declared = {str(entry["module"]) for entry in cm._runtime_tool_manifest().entries}
    reached = _first_party_modules_executed(
        lambda: cm.run_successor_multipass_final(r19.production_request(estate))
    )
    assert reached - declared == set(), sorted(reached - declared)
    # The five R20 named are genuinely reached, so their declaration is not decorative.
    assert set(R20_ADDED_MODULES) <= reached
    # And the S12 correction UDF's own dependency chain is inside that reached set.
    assert {
        "disclosure_drift.sec.identifiers",
        "disclosure_drift.sec.observation_catalog",
        "disclosure_drift.sec.snapshots",
    } <= reached


def test_m07_the_calibration_route_reaches_nothing_the_manifest_does_not_declare(
    tmp_path: Path,
) -> None:
    """The other successor route, traced the same way -- §8 asks for both."""
    estate = cross.calibration_estate(tmp_path)
    declared = {str(entry["module"]) for entry in cm._runtime_tool_manifest().entries}
    reached = _first_party_modules_executed(
        lambda: cross.run_calibration_in_process(estate, cross.calibration_request(estate))
    )
    assert reached - declared == set(), sorted(reached - declared)
    assert {
        "disclosure_drift.m3.capacity_plan",
        "disclosure_drift.m3.external_working_root",
    } <= reached


def test_m04_the_declared_set_is_not_discovered_at_runtime_and_binds_source_bytes_only() -> None:
    # AST, not substring: this module DESCRIBES the indirection it refuses to use, and a text
    # ban cannot tell that prose from a call.
    tree = ast.parse(Path(str(cm.__file__)).read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not imported & {"importlib", "pkgutil"}
    referenced = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    for forbidden in ("__import__", "import_module", "walk_packages", "iter_modules", "modules"):
        assert forbidden not in referenced, forbidden
    assert isinstance(cm._TOOL_MANIFEST_MODULES, tuple)
    for module, file in cm._TOOL_MANIFEST_MODULES:
        assert isinstance(module, str) and Path(str(file)).suffix == ".py"
    manifest = cm._runtime_tool_manifest()
    for entry in manifest.entries:
        relative = str(entry["module"]).removeprefix("disclosure_drift.").replace(".", "/")
        path = Path(str(cm.__file__)).parent.parent / f"{relative}.py"
        assert (entry["sha256"], entry["byte_length"]) == file_sha256(path), entry["module"]


def test_m05_the_new_members_are_declared_provenance_and_never_new_capability() -> None:
    """The five modules are hashed, not called: chunk_multipass gained no capability with them."""
    tree = ast.parse(Path(str(cm.__file__)).read_text(encoding="utf-8"))
    aliases = {
        "disclosure_drift.m3.capacity_plan": "_capacity_plan_module",
        "disclosure_drift.m3.external_working_root": "_external_working_root_module",
        "disclosure_drift.sec.identifiers": "_identifiers_module",
        "disclosure_drift.sec.observation_catalog": "_observation_catalog_module",
        "disclosure_drift.sec.snapshots": "_snapshots_module",
    }
    imported = {
        alias.name: alias.asname
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name in aliases
    }
    assert imported == aliases
    for name, alias in aliases.items():
        attributes = sorted(
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == alias
        )
        assert attributes == ["__file__"], name
    # None of the five is imported FROM, so no name of theirs enters this module's namespace.
    assert not [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module in aliases
    ]


# ==========================================================================
# The publication primitive's remaining refusals
# ==========================================================================
def test_p01_a_failed_staging_removal_never_revokes_a_proved_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = tmp_path / "world"
    world.mkdir()
    staged = tmp_path / "staged.sqlite3"
    staged.write_bytes(b"finished")
    canonical = world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    real_unlink = Path.unlink

    def refusing_unlink(self: Path, *args: Any, **kwargs: Any) -> None:
        if self == staged:
            raise OSError(errno.EPERM, "refused")
        real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", refusing_unlink)
    record = wc.publish_staged_artifact(staged, canonical)
    monkeypatch.undo()
    assert record["staging_name_removed"] is False
    assert "EPERM" in str(record["staging_name_removal_error"]) or "refused" in str(
        record["staging_name_removal_error"]
    )
    # The publication itself stands: the canonical name is the staged inode.
    assert canonical.stat().st_ino == staged.stat().st_ino
    assert canonical.read_bytes() == b"finished"


def test_p02_a_publication_that_links_the_wrong_inode_refuses_and_removes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world = tmp_path / "world"
    world.mkdir()
    staged = tmp_path / "staged.sqlite3"
    staged.write_bytes(b"the verified artifact")
    impostor = tmp_path / "impostor.sqlite3"
    impostor.write_bytes(b"a different artifact")
    canonical = world / COMPACT_EVIDENCE_SIDECAR_FILENAME

    real_link = os.link

    def wrong_link(source: Any, destination: Any) -> None:
        real_link(impostor, destination)

    monkeypatch.setattr(wc.os, "link", wrong_link)
    with pytest.raises(wc.WorkingCatalogError, match="not the staged inode"):
        wc.publish_staged_artifact(staged, canonical)
    monkeypatch.undo()
    # The staging name is left in place, because the published inode was never proved.
    assert staged.read_bytes() == b"the verified artifact"
    assert canonical.stat().st_ino == impostor.stat().st_ino


def test_p03_the_compact_evidence_binding_is_never_moved_under_a_live_watch() -> None:
    """Binding the sidecar database is a before-the-first-statement operation.

    Moving it under a live watch would move the watchdog off the log it has been sampling and
    silence a genuine breach, so it refuses instead. Driven over a stub rather than a live
    stage: the method reads exactly the two attributes below and nothing else.
    """
    stub = SimpleNamespace(_watches={}, _sidecar_path=Path("/world/compact_evidence.sqlite3"))
    cm._StageInstrumentation.bind_sidecar_database(stub, Path("/attempt/staged.sqlite3"))
    assert stub._sidecar_path == Path("/attempt/staged.sqlite3")
    stub._watches[cm._ROLE_COMPACT_EVIDENCE] = object()
    with pytest.raises(cm._InstrumentationAbortError, match="never rebound"):
        cm._StageInstrumentation.bind_sidecar_database(stub, Path("/elsewhere/other.sqlite3"))
    assert stub._sidecar_path == Path("/attempt/staged.sqlite3")
