"""Decision 140 — the corrections the D139 independent review required, each with its killer.

Every test here exists to **fail** if one specific correction is removed. The D139 review found
two majors, seven minors and ten informational items in the corrected canary's pre-launch
surface; this file proves each one closed, and the falsification runs recorded in Decision 140
§18 show which node each protection dies at when its production code is reverted.

The organising rule, stated once: a test that cannot fail proves nothing. **MINOR-3** was exactly
that -- an accepted assertion made on a list the harness never wrote to -- so the counters here
are owned by the caller and survive the exception that carries them out.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d116_single_source_canary as d116  # noqa: E402
import test_d138_safety_envelope_correction as d138  # noqa: E402

from disclosure_drift.m3 import canary_runtime as runtime  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import offline_parse as parse  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402

_QUALIFIED = ewr.QUALIFIED_EXTERNAL_VOLUME_UUID
_OTHER = "0BADCAFE-0000-0000-0000-000000000000"
_ARBITRARY = "11111111-2222-3333-4444-555555555555"
_REPO = Path(canary.__file__).resolve().parents[3]
_LAUNCHER = _REPO / "scripts" / "m3" / "canary_launch.py"


def _identity(uuid: str, mount: Path) -> ewr.VolumeIdentity:
    return ewr.VolumeIdentity(
        volume_uuid=uuid, mount_point=mount, filesystem_type="exfat", device_identifier="diskN sN"
    )


def _provider(mapping: dict[Path, str]) -> Any:
    """A substituted volume-identity provider keyed by ancestry rather than by device number.

    The module's own ``mount_point_of`` answers by device number, which on a temporary directory
    is always the host's own disk. Tests must never depend on the operator's SSD being attached,
    so a synthetic "volume" is any directory this mapping names, and a path beneath one resolves
    to it.
    """

    def _resolve(path: Path) -> ewr.VolumeIdentity:
        for candidate, uuid in mapping.items():
            if path == candidate or candidate in path.parents:
                return _identity(uuid, candidate)
        message = f"no volume is mounted for {path.name}"
        raise ewr.ExternalWorkingRootError(message)

    return _resolve


# ==========================================================================
# MAJOR-1 — the absent/stale mount can no longer reach an internal fallback
# ==========================================================================
def test_m1_a_volumes_path_is_an_external_intent_even_with_nothing_mounted(
    tmp_path: Path,
) -> None:
    """**D140-R1.** Intent is read from the name, so an absent volume cannot reclassify it.

    This is the whole of MAJOR-1 in one assertion. ``external_volume_candidate`` answers by
    device number on the nearest existing ancestor -- with the SSD unplugged that ancestor is
    ``/Volumes``, which is on the system root filesystem, so the intended external world
    classified **internal** and ran the accepted Decision 116 path with no guard at all.
    """
    named = Path("/Volumes/FDD-D140-NEVER-MOUNTED/fdd_canary/world")
    assert ewr.external_volume_intent(named) is True
    assert ewr.intended_volume_directory(named) == Path("/Volumes/FDD-D140-NEVER-MOUNTED")
    # Deliberately a name that is never mounted anywhere: the property being asserted is that
    # intent is read from the **name**, so it must not depend on what this host has attached.
    assert not Path("/Volumes/FDD-D140-NEVER-MOUNTED").exists()
    # An internal path carries no intent, so the accepted internal behaviour is untouched.
    assert ewr.external_volume_intent(tmp_path / "work") is False
    assert ewr.external_volume_intent(Path("/Volumes")) is False


def test_m1_the_uuid_assertion_is_mandatory_on_every_external_route(tmp_path: Path) -> None:
    """**D140-R2.** Omitting the assertion is itself the refusal, on intent and on residence."""
    named = Path("/Volumes/FDD-D140-NEVER-MOUNTED/fdd_canary/world")
    with pytest.raises(ewr.ExternalWorkingRootError, match="--require-volume-uuid is required"):
        ewr.require_external_envelope(named, observed_at="2026-08-23T00:00:00Z")


def test_m1_an_absent_volume_refuses_rather_than_degrading(tmp_path: Path) -> None:
    """**D140-R3.** The named volume is not mounted, so nothing authenticates and nothing runs."""
    named = Path("/Volumes/FDD-D140-NEVER-MOUNTED/fdd_canary/world")
    with pytest.raises(ewr.ExternalWorkingRootError, match="is not mounted"):
        ewr.require_external_envelope(
            named, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_m1_a_writable_stale_directory_at_the_mount_point_refuses(tmp_path: Path) -> None:
    """**D140-R3.** The case that permitted a *complete internal run*.

    A directory left behind at ``/Volumes/<name>`` exists, is a directory, and is writable. Every
    predicate that asks "can I create a world here?" says yes. The one that distinguishes it from
    a volume is whether it is a **mount point**, which is why that is the predicate.
    """
    volumes = tmp_path / "Volumes"
    stale = volumes / "SSK SSD"
    (stale / "fdd_canary").mkdir(parents=True)
    assert stale.is_dir() and os.access(stale, os.W_OK)
    assert stale.is_mount() is False
    # Even with a provider that would happily report the qualified UUID for it, the directory
    # is refused: it is not a mount point, so there is no volume there to authenticate.
    with pytest.raises(ewr.ExternalWorkingRootError, match="not a mount point"):
        ewr.require_mounted_volume_directory(stale, provider=_provider({stale: _QUALIFIED}))


def test_m1_an_absent_volume_directory_refuses_before_the_uuid_is_read(tmp_path: Path) -> None:
    """**D140-R3.** Nothing is asked of ``diskutil`` about a path with nothing mounted at it."""
    asked: list[Path] = []

    def _recording(path: Path) -> ewr.VolumeIdentity:  # pragma: no cover - must not be reached
        asked.append(path)
        return _identity(_QUALIFIED, path)

    with pytest.raises(ewr.ExternalWorkingRootError, match="is not mounted"):
        ewr.require_mounted_volume_directory(tmp_path / "absent", provider=_recording)
    assert asked == []


def test_m1_intended_volume_directory_is_the_mount_not_the_world(tmp_path: Path) -> None:
    """The authenticated unit is the volume, never a subdirectory an operator chose."""
    assert ewr.intended_volume_directory(Path("/Volumes/A/b/c/d")) == Path("/Volumes/A")


@pytest.mark.parametrize("asserted", [_OTHER, _ARBITRARY])
def test_m1_a_wrong_or_arbitrary_uuid_refuses_before_anything_is_measured(
    asserted: str, tmp_path: Path
) -> None:
    """**D138-R12, preserved.** The assertion is checked against the frozen identity."""
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the one qualified external"):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=asserted
        )


def test_m1_a_similarly_named_mounted_volume_refuses(tmp_path: Path) -> None:
    """A volume that is genuinely mounted, and genuinely not the one qualified."""
    volume = tmp_path / "SSK SSD 1"
    (volume / "work").mkdir(parents=True)
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        ewr.require_qualified_volume(volume / "work", provider=_provider({volume: _OTHER}))


def test_m1_a_genuinely_mounted_wrong_volume_refuses_on_its_uuid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The third predicate, reached only once the first two hold.

    ``_is_mount_point`` is substituted rather than a real volume mounted: the mount-state
    predicate has its own test above, and this one is about what happens **after** it passes.
    """
    monkeypatch.setattr(ewr, "_is_mount_point", lambda _path: True)
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        ewr.require_mounted_volume_directory(tmp_path, provider=_provider({tmp_path: _OTHER}))
    # The qualified volume, mounted where it says it is, passes.
    identity = ewr.require_mounted_volume_directory(
        tmp_path, provider=_provider({tmp_path: _QUALIFIED})
    )
    assert identity.volume_uuid == _QUALIFIED


def test_m1_an_internal_root_with_no_assertion_keeps_its_historical_behaviour(
    tmp_path: Path,
) -> None:
    """**Preserved.** The accepted Decision 116 path is byte-for-byte what it was."""
    assert (
        ewr.require_external_envelope(tmp_path / "work", observed_at="2026-08-23T00:00:00Z") is None
    )


def test_m1_an_internal_root_with_an_external_uuid_refuses(tmp_path: Path) -> None:
    """**Preserved.** The assertion can only ever *add* a requirement, never satisfy one."""
    with pytest.raises(ewr.ExternalWorkingRootError):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_m1_a_vanished_volume_is_caught_before_the_world_is_created(tmp_path: Path) -> None:
    """**D140-R4.** Re-authentication at the last safe point before ``mkdir``."""
    volume = tmp_path / "volume"
    work = volume / "work"
    work.mkdir(parents=True)
    admitted = ewr.AdmittedVolume(
        identity=_identity(_QUALIFIED, volume),
        mount_point=volume,
        device=work.stat().st_dev,
        work_root=work,
    )
    admitted.require_present()  # still there
    # The volume goes away between admission and creation.
    work.rmdir()
    volume.rmdir()
    with pytest.raises(ewr.ExternalWorkingRootError, match="no longer resolves beneath"):
        admitted.require_present()


def test_m1_create_world_never_recreates_a_vanished_mount_point(tmp_path: Path) -> None:
    """**D140-R5.** The race's payload: ``mkdir(parents=True)`` rebuilding the mount point.

    With the volume gone, the accepted ``create_world`` would have created the work root **and
    every parent above it** on the internal disk and built the world inside. Only ``/Volumes``
    being root-owned stood in the way, which is a permission accident and not a guard.
    """
    absent_root = tmp_path / "volume" / "work"
    with pytest.raises(canary.SingleSourceCanaryError, match="NOT created here"):
        canary.create_world(absent_root, "d140-race", require_existing_root=True)
    assert not absent_root.exists()
    assert not absent_root.parent.exists()
    # The accepted internal behaviour is unchanged when the flag is not set.
    world = canary.create_world(tmp_path / "internal" / "work", "d140-internal")
    assert world.directory.is_dir()


def test_m1_a_replaced_filesystem_is_refused_by_device_identity(tmp_path: Path) -> None:
    """**D140-R15.** Containment cannot see a swap; the pinned device number can."""
    volume = tmp_path / "volume"
    work = volume / "work"
    work.mkdir(parents=True)
    admitted = ewr.AdmittedVolume(
        identity=_identity(_QUALIFIED, volume),
        mount_point=volume,
        device=work.stat().st_dev + 9999,
        work_root=work,
    )
    with pytest.raises(ewr.ExternalWorkingRootError, match="different device identity"):
        admitted.require_present()


# ==========================================================================
# MINOR-1 — the temporary/spill measurement no longer claims a false zero
# ==========================================================================
def test_m_one_an_unlinked_spill_can_never_be_reported_as_a_measured_zero(tmp_path: Path) -> None:
    """**D140-R7.** SQLite unlinks ``etilqs_*`` immediately; a walk sees nothing.

    The directory below is empty in exactly the way a directory holding a two-gigabyte in-flight
    sort is empty. Decision 137 reported ``temp_bytes: 0`` for both.
    """
    temp = tmp_path / "temp"
    temp.mkdir()
    spill = temp / "etilqs_deadbeef"
    handle = spill.open("wb")
    try:
        handle.write(b"x" * 4096)
        handle.flush()
        spill.unlink()  # exactly what SQLite does, and the file is still being written
        assert list(temp.iterdir()) == []
        record = ewr.observe_capacity(
            "DURING_F2",
            working_root=tmp_path,
            temp_directory=temp,
            observed_at="2026-08-23T00:00:00Z",
        ).as_record()
    finally:
        handle.close()
    assert record["temp_bytes"] is None
    assert record["temp_measurement_status"] == ewr.UNMEASURED_UNLINKED_SQLITE_TEMP
    assert record["temp_visible_bytes"] == 0
    assert 0 not in {record["temp_bytes"]}


def test_m_one_no_unknown_is_serialized_as_a_numeric_zero(tmp_path: Path) -> None:
    """An unknown stays ``null`` through JSON, which is where a reader meets it."""
    observation = ewr.observe_capacity(
        "PRE_LAUNCH", working_root=tmp_path, observed_at="2026-08-23T00:00:00Z"
    )
    payload = json.loads(json.dumps(dict(observation.as_record())))
    assert payload["temp_bytes"] is None
    assert payload["temp_measurement_status"] == ewr.UNMEASURED_UNLINKED_SQLITE_TEMP


def test_m_one_capacity_decisions_still_use_filesystem_free_bytes(tmp_path: Path) -> None:
    """Free space remains authoritative: a ``statvfs`` counts allocated unlinked blocks."""
    observation = ewr.observe_capacity(
        "DURING_F2", working_root=tmp_path, observed_at="2026-08-23T00:00:00Z"
    )
    assert observation.free_bytes > 0
    assert ewr.f2_capacity_state(observation.free_bytes) == ewr.f2_capacity_state(
        observation.free_bytes
    )
    assert ewr.f2_capacity_state(ewr.F2_HARD_FLOOR_FREE_BYTES) == ewr.F2_HARD_STOP_STATE
    assert ewr.f2_capacity_state(ewr.F2_ALERT_FREE_BYTES) == ewr.F2_ALERT_STATE


# ==========================================================================
# MINOR-2 — a blocking F0 stops the run before F1
# ==========================================================================
def _outcome(state: str, disposition: str = "E0_REQUIRED_PARSE") -> Any:
    from disclosure_drift.m3.offline_parse import PlannedSourceOutcome, SingleSourceOutcome

    return SingleSourceOutcome(
        outcome=PlannedSourceOutcome(
            source_instance_id="instance",
            source_id="sec_bulk_submissions",
            disposition=disposition,
            parser_state_before="not_started",
            parser_state_after=state,
        ),
        observation=None,
    )


def test_m_two_a_failed_f0_stops_the_run(tmp_path: Path) -> None:
    """**D140-R12.** ``failed`` is the accepted terminal for *do not read these counts*."""
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        canary.require_f0_success(_outcome("failed"))


def test_m_two_an_accepted_unavailable_source_stops_the_run() -> None:
    """It leaves ``parser_state`` untouched, so the state gate alone would not catch it."""
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        canary.require_f0_success(
            _outcome("not_started", disposition="E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE")
        )


@pytest.mark.parametrize("state", ["completed", "quarantined"])
def test_m_two_an_accepted_terminal_proceeds_unchanged(state: str) -> None:
    """**D140-R12 widens nothing.** A quarantined parse already proceeds, and still does."""
    assert canary.require_f0_success(_outcome(state)).outcome.parser_state_after == state


def test_m_two_the_blocking_set_is_read_from_the_accepted_terminals() -> None:
    """No parser methodology is invented here: the states already existed."""
    assert frozenset({"failed"}) == canary.BLOCKING_PARSER_STATES
    assert "quarantined" not in canary.BLOCKING_PARSER_STATES
    assert (
        frozenset({"E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"}) == canary.BLOCKING_SOURCE_DISPOSITIONS
    )


# ==========================================================================
# MINOR-4 — runtime control never lands inside the working root
# ==========================================================================
def test_m_four_a_pid_path_inside_the_work_root_is_refused(tmp_path: Path) -> None:
    """**D140-R10.** The launcher's first act must not be a write to an unadmitted volume."""
    work = tmp_path / "volume" / "work"
    work.mkdir(parents=True)
    with pytest.raises(runtime.CanaryRuntimeError, match="may not be written beneath"):
        runtime.require_internal_runtime_path(work / "canary.pid", work_root=work)


def test_m_four_an_alias_into_the_work_root_is_refused(tmp_path: Path) -> None:
    """``..`` and a symlink are collapsed before anything is compared."""
    work = tmp_path / "work"
    work.mkdir()
    link = tmp_path / "innocent"
    link.symlink_to(work, target_is_directory=True)
    for candidate in (link / "canary.pid", tmp_path / "x" / ".." / "work" / "canary.pid"):
        with pytest.raises(runtime.CanaryRuntimeError):
            runtime.require_internal_runtime_path(candidate, work_root=work)


def test_m_four_a_path_inside_the_d130_archive_is_refused(tmp_path: Path) -> None:
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    with pytest.raises(runtime.CanaryRuntimeError, match="D130 archive"):
        runtime.require_internal_runtime_path(
            archive / "canary.pid", work_root=tmp_path / "work", archive=archive
        )


def test_m_four_an_internal_runtime_path_is_accepted(tmp_path: Path) -> None:
    internal = tmp_path / "internal" / "canary.pid"
    assert runtime.require_internal_runtime_path(internal, work_root=tmp_path / "work").name == (
        "canary.pid"
    )


def test_m_four_the_launcher_refuses_a_pid_path_under_the_work_root(tmp_path: Path) -> None:
    """The same rule at the process boundary, through the real script."""
    work = tmp_path / "work"
    work.mkdir()
    completed = subprocess.run(
        [
            sys.executable,
            str(_LAUNCHER),
            "--pid-file",
            str(work / "canary.pid"),
            "--work-root",
            str(work),
            "--check-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 3
    assert "LAUNCH_REFUSED_RUNTIME_PATH_NOT_INTERNAL" in completed.stderr
    assert not (work / "canary.pid").exists()


# ==========================================================================
# MINOR-5 — the temporary-root refusal says which root it is about
# ==========================================================================
def test_m_five_an_internal_temporary_root_names_the_temporary_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D140-R11.** Decision 137 said "selected working root" while rejecting ``SQLITE_TMPDIR``."""
    volume = tmp_path / "volume"
    work = volume / "work"
    work.mkdir(parents=True)
    internal_temp = tmp_path / "internal-temp"
    internal_temp.mkdir()
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(internal_temp))
    with pytest.raises(ewr.ExternalWorkingRootError) as raised:
        ewr.require_external_sqlite_tmpdir(
            working_root=work,
            archive=volume / ewr.D130_ARCHIVE_DIRECTORY_NAME,
            provider=_provider({volume: _QUALIFIED}),
        )
    message = str(raised.value)
    assert "SQLITE_TMPDIR names a temporary root" in message
    assert "The temporary root is rejected here, not the selected working root" in message
    assert str(internal_temp) not in message


def test_m_five_an_unset_temporary_root_still_says_it_is_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ewr.SQLITE_TMPDIR_ENV, raising=False)
    with pytest.raises(ewr.ExternalWorkingRootError, match="is not set"):
        ewr.require_external_sqlite_tmpdir(working_root=tmp_path, archive=tmp_path / "archive")


# ==========================================================================
# MINOR-6 — one complete-source canary per host, whatever its run identity
# ==========================================================================
def test_m_six_a_second_run_with_a_different_identity_is_refused(tmp_path: Path) -> None:
    """**D140-R16.** The lock is independent of ``run_id``, which is the whole point."""
    first = runtime.acquire_canary_execution_lock(tmp_path, detail={"run_id": "alpha"})
    try:
        with pytest.raises(runtime.CanaryRuntimeError, match="already running on this host"):
            runtime.acquire_canary_execution_lock(tmp_path, detail={"run_id": "beta"})
    finally:
        first.release()


def test_m_six_the_lock_is_released_on_clean_exit(tmp_path: Path) -> None:
    with runtime.acquire_canary_execution_lock(tmp_path) as held:
        assert held.held is True
    assert runtime.acquire_canary_execution_lock(tmp_path).release() is None


def test_m_six_stale_metadata_alone_never_blocks(tmp_path: Path) -> None:
    """A dead run's leftover text must not be what refuses the next one."""
    path = runtime.canary_execution_lock_path(tmp_path)
    path.write_text(json.dumps({"run_id": "ghost", "pid": 999999}), encoding="utf-8")
    lock = runtime.acquire_canary_execution_lock(tmp_path, detail={"run_id": "live"})
    lock.release()


def test_m_six_the_lock_is_released_when_the_holding_process_dies(tmp_path: Path) -> None:
    """``flock`` is released by the kernel, so no reaper and no lease recovery is needed."""
    program = (
        "import sys;"
        f"sys.path.insert(0, {str(_REPO / 'src')!r});"
        "from disclosure_drift.m3 import canary_runtime as r;"
        f"r.acquire_canary_execution_lock(__import__('pathlib').Path({str(tmp_path)!r}));"
        "print('held', flush=True)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=False
    )
    assert "held" in completed.stdout
    runtime.acquire_canary_execution_lock(tmp_path).release()


def test_m_six_the_lock_path_is_internal_and_cannot_collide_with_the_archive(
    tmp_path: Path,
) -> None:
    path = runtime.canary_execution_lock_path(tmp_path)
    assert ewr.D130_ARCHIVE_DIRECTORY_NAME not in str(path)
    assert path.is_relative_to(tmp_path)


# ==========================================================================
# INFO-5 — alert evidence is bounded in memory, not merely in cadence
# ==========================================================================
def _alerting_guard(tmp_path: Path, clock: list[float]) -> ewr.F2CapacityGuard:
    alert = ewr.F2_ALERT_FREE_BYTES - 1

    def _free(_path: Path) -> tuple[int, int]:
        return alert, alert * 10

    def _tick() -> float:
        return clock[0]

    return ewr.F2CapacityGuard(
        working_root=tmp_path, free_space=_free, clock=_tick, now=lambda: "2026-08-23T00:00:00Z"
    )


def test_i_five_a_thirty_hour_alert_does_not_grow_evidence_without_bound(
    tmp_path: Path,
) -> None:
    """**D140-R17.** Safety sampling stays at five seconds; the *evidence* is thinned.

    Thirty hours in the alert band is 21,600 samples at the accepted cadence. Decision 138
    appended an observation for every one of them.
    """
    clock = [0.0]
    guard = _alerting_guard(tmp_path, clock)
    for _ in range(21_600):
        guard()
        clock[0] += 5.0
    assert guard.samples == 21_600
    assert guard.alert_count == 21_600
    assert len(guard.observations) <= ewr.F2_ALERT_EVIDENCE_MAX_RECORDS
    assert guard.first_alert is not None
    assert guard.latest_alert is not None


def test_i_five_the_first_alert_is_always_retained(tmp_path: Path) -> None:
    clock = [0.0]
    guard = _alerting_guard(tmp_path, clock)
    guard()
    assert len(guard.observations) == 1
    assert guard.observations[0].phase == "DURING_F2"


def test_i_five_the_hard_stop_still_fires_immediately_at_a_sample(tmp_path: Path) -> None:
    """Thinning evidence must never thin enforcement."""

    def _free(_path: Path) -> tuple[int, int]:
        return ewr.F2_HARD_FLOOR_FREE_BYTES, ewr.F2_HARD_FLOOR_FREE_BYTES * 10

    guard = ewr.F2CapacityGuard(working_root=tmp_path, free_space=_free)
    with pytest.raises(ewr.F2CapacityHardStopError) as raised:
        guard()
    assert raised.value.record["hard_stop_reason"] == ewr.F2_HARD_STOP_REASON
    assert raised.value.record["f2_committed"] is False


# ==========================================================================
# INFO-3 — a vanished volume can never be read as healthy internal free space
# ==========================================================================
def test_i_three_a_lost_volume_hard_stops_before_free_space_is_trusted(
    tmp_path: Path,
) -> None:
    """**D140-R15.** The internal disk always looks healthy, which is the danger."""
    volume = tmp_path / "volume"
    work = volume / "work"
    work.mkdir(parents=True)
    admitted = ewr.AdmittedVolume(
        identity=_identity(_QUALIFIED, volume),
        mount_point=volume,
        device=work.stat().st_dev,
        work_root=work,
    )
    healthy = 500 * 1024**3

    def _free(_path: Path) -> tuple[int, int]:
        return healthy, healthy * 2

    guard = ewr.F2CapacityGuard(
        working_root=work,
        free_space=_free,
        admitted=admitted,
        identity_provider=_provider({volume: _QUALIFIED}),
    )
    guard()  # the volume is present: a normal sample, nothing recorded
    for child in sorted(work.parent.rglob("*"), reverse=True):
        child.rmdir()
    volume.rmdir()
    with pytest.raises(ewr.F2CapacityHardStopError) as raised:
        guard._sample()
    assert raised.value.record["hard_stop_reason"] == ewr.F2_VOLUME_IDENTITY_LOST_REASON
    assert raised.value.record["free_bytes"] is None
    assert raised.value.record["f2_transaction_rolled_back"] is True


def test_i_three_a_swapped_uuid_is_refused_at_reauthentication(tmp_path: Path) -> None:
    volume = tmp_path / "volume"
    volume.mkdir()
    admitted = ewr.AdmittedVolume(
        identity=_identity(_QUALIFIED, volume),
        mount_point=volume,
        device=volume.stat().st_dev,
        work_root=volume,
    )
    with pytest.raises(ewr.ExternalWorkingRootError, match="now reports"):
        admitted.reauthenticate(provider=_provider({volume: _OTHER}))


# ==========================================================================
# INFO-6 — the stop path authenticates the exact process, never a substring
# ==========================================================================
def test_i_six_a_shell_quoting_the_canary_command_is_never_signalled(tmp_path: Path) -> None:
    """**D140-R18.** The decoy the accepted ``--expect-command`` substring matched perfectly."""
    pid_file = tmp_path / "canary.pid"
    pid_file.write_text("4242\n", encoding="utf-8")

    def _decoy(_pid: int) -> tuple[str, ...]:
        return ("/bin/zsh", "-c", "disclosure-drift m3 canary-source --run-id d140-real")

    with pytest.raises(runtime.CanaryRuntimeError, match="not a canary executable"):
        runtime.authenticate_canary_process(
            pid_file=pid_file, run_id="d140-real", argv_provider=_decoy
        )


def test_i_six_a_different_run_is_never_stopped_in_this_runs_name(tmp_path: Path) -> None:
    pid_file = tmp_path / "canary.pid"
    pid_file.write_text("4242\n", encoding="utf-8")

    def _other(_pid: int) -> tuple[str, ...]:
        return ("/x/disclosure-drift", "m3", "canary-source", "--run-id", "some-other-run")

    with pytest.raises(runtime.CanaryRuntimeError, match="does not carry --run-id"):
        runtime.authenticate_canary_process(
            pid_file=pid_file, run_id="d140-real", argv_provider=_other
        )


def test_i_six_the_real_canary_authenticates(tmp_path: Path) -> None:
    pid_file = tmp_path / "canary.pid"
    pid_file.write_text("4242\n", encoding="utf-8")

    def _real(_pid: int) -> tuple[str, ...]:
        return (
            "/x/disclosure-drift",
            "m3",
            "canary-source",
            "--run-id",
            "d140-real",
            "--mode",
            "run",
        )

    authenticated = runtime.authenticate_canary_process(
        pid_file=pid_file, run_id="d140-real", argv_provider=_real
    )
    assert authenticated.pid == 4242
    assert authenticated.run_id == "d140-real"


@pytest.mark.parametrize("value", ["0", "-1", "1", "not-a-pid", ""])
def test_i_six_a_non_targetable_pid_record_is_refused(value: str, tmp_path: Path) -> None:
    """``os.kill`` reads 0 as a process group and a negative value as a broadcast."""
    pid_file = tmp_path / "canary.pid"
    pid_file.write_text(value, encoding="utf-8")
    with pytest.raises(runtime.CanaryRuntimeError):
        runtime.read_pid_record(pid_file)


# ==========================================================================
# INFO-7 — failed-world reclaim readiness names paths and deletes nothing
# ==========================================================================
def _world(work_root: Path, run_id: str, *, result: bool) -> Path:
    world = work_root / run_id
    world.mkdir(parents=True)
    (world / canary.WORKING_CATALOG_FILENAME).write_bytes(b"x" * 128)
    if result:
        (world / canary.CANARY_RESULT_FILENAME).write_text("{}", encoding="utf-8")
    return world


def _readiness(work_root: Path, run_id: str, runtime_directory: Path | None = None) -> Any:
    return runtime.failed_world_reclaim_readiness(
        work_root=work_root,
        run_id=run_id,
        runtime_directory=runtime_directory,
        result_filename=canary.CANARY_RESULT_FILENAME,
        prefix_result_filename=canary.CANARY_PREFIX_RESULT_FILENAME,
        working_catalog_filename=canary.WORKING_CATALOG_FILENAME,
    )


def test_i_seven_a_failed_world_is_reclaim_ready_and_names_only_itself(tmp_path: Path) -> None:
    """**D140-R19.** The physical constraint is not removed; the position is made legible."""
    work = tmp_path / "work"
    failed = _world(work, "d140-failed", result=False)
    _world(work, "d140-sibling", result=True)
    report = _readiness(work, "d140-failed")
    assert report.reclaim_ready is True
    assert report.disposable_paths == ("d140-failed",)
    assert "d140-sibling" not in report.disposable_paths
    assert report.world_bytes == 128
    assert failed.is_dir()  # nothing was deleted
    assert (work / "d140-sibling").is_dir()
    assert report.as_record()["deleted_anything"] is False


def test_i_seven_a_completed_world_is_never_reclaim_ready(tmp_path: Path) -> None:
    """A run that produced its result document is evidence, not rubbish."""
    work = tmp_path / "work"
    _world(work, "d140-done", result=True)
    report = _readiness(work, "d140-done")
    assert report.reclaim_ready is False
    assert report.disposable_paths == ()


def test_i_seven_no_absolute_path_reaches_the_record(tmp_path: Path) -> None:
    work = tmp_path / "work"
    _world(work, "d140-failed", result=False)
    assert str(tmp_path) not in json.dumps(dict(_readiness(work, "d140-failed").as_record()))


# ==========================================================================
# INFO-8 — power and lid are an explicit launch condition
# ==========================================================================
def test_i_eight_battery_power_refuses() -> None:
    """**D140-R20.** Thirty hours is not a battery-length run."""
    with pytest.raises(runtime.CanaryRuntimeError, match="battery power"):
        runtime.require_launch_power_conditions(
            state=runtime.PowerState(on_ac_power=False, clamshell_closed=False)
        )


def test_i_eight_a_closed_lid_refuses() -> None:
    """``caffeinate`` does not prevent lid-close sleep, and this does not pretend it does."""
    with pytest.raises(runtime.CanaryRuntimeError, match="lid closed"):
        runtime.require_launch_power_conditions(
            state=runtime.PowerState(on_ac_power=True, clamshell_closed=True)
        )


def test_i_eight_an_unknown_state_refuses_unless_the_operator_asserts_it() -> None:
    unknown = runtime.PowerState(on_ac_power=None, clamshell_closed=None)
    with pytest.raises(runtime.CanaryRuntimeError, match="could not be read"):
        runtime.require_launch_power_conditions(state=unknown)
    assert (
        runtime.require_launch_power_conditions(
            state=unknown, operator_asserts_power_conditions=True
        )
        is unknown
    )


def test_i_eight_good_conditions_pass() -> None:
    good = runtime.PowerState(on_ac_power=True, clamshell_closed=False)
    assert runtime.require_launch_power_conditions(state=good) is good


def test_i_eight_the_live_reading_is_structured_and_bounded() -> None:
    """The real host, read read-only. Either value may legitimately be unknown."""
    observed = runtime.power_state()
    assert set(observed.as_record()) == {"on_ac_power", "clamshell_closed"}
    assert observed.on_ac_power in {True, False, None}
    assert observed.clamshell_closed in {True, False, None}


# ==========================================================================
# INFO-9 / INFO-10 — the shard-to-parent structure is proved before F0 runs
# ==========================================================================
def _primary(cik: int, shards: list[str]) -> bytes:
    return json.dumps(
        {"cik": str(cik), "filings": {"files": [{"name": name} for name in shards]}}
    ).encode()


def _archive(tmp_path: Path, members: list[tuple[str, bytes]], name: str = "bulk.zip") -> Path:
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as archive:
        for member, payload in members:
            archive.writestr(member, payload)
    return path


_SHARD = "CIK0000000001-submissions-001.json"
_PRIMARY = "CIK0000000001.json"


def test_i_nine_shard_before_parent_resolves_and_is_observed(tmp_path: Path) -> None:
    """**D140-R21.** Archive order is irrelevant to the binding, and is still recorded."""
    archive = _archive(tmp_path, [(_SHARD, b"{}"), (_PRIMARY, _primary(1, [_SHARD]))], name="a.zip")
    proof = parse.structural_source_preflight(archive)
    assert proof.parent_map_sound is True
    assert proof.shard_before_parent is True
    assert proof.shard_members == 1
    assert proof.declared_shard_names == 1


def test_i_nine_parent_before_shard_resolves_too(tmp_path: Path) -> None:
    archive = _archive(tmp_path, [(_PRIMARY, _primary(1, [_SHARD])), (_SHARD, b"{}")], name="b.zip")
    proof = parse.structural_source_preflight(archive)
    assert proof.parent_map_sound is True
    assert proof.shard_before_parent is False


def test_i_nine_a_shard_no_document_declares_is_an_orphan(tmp_path: Path) -> None:
    """The exact condition F0 would have refused twenty-seven hours in."""
    archive = _archive(tmp_path, [(_SHARD, b"{}"), (_PRIMARY, _primary(1, []))], name="c.zip")
    proof = parse.structural_source_preflight(archive)
    assert proof.parent_map_sound is False
    assert proof.orphan_count == 1
    assert proof.orphan_shards == (_SHARD,)
    with pytest.raises(parse.OfflineParseError, match="no primary document declares"):
        parse.require_sound_parent_map(proof)


def test_i_nine_two_distinct_registrants_declaring_one_shard_refuses(tmp_path: Path) -> None:
    """**Exactly one** authoritative parent, and no tie is broken."""
    archive = _archive(
        tmp_path,
        [
            (_SHARD, b"{}"),
            (_PRIMARY, _primary(1, [_SHARD])),
            ("CIK0000000002.json", _primary(2, [_SHARD])),
        ],
        name="d.zip",
    )
    proof = parse.structural_source_preflight(archive)
    assert proof.duplicate_parent_count == 1
    assert proof.parent_map_sound is False
    with pytest.raises(parse.OfflineParseError, match="more than one"):
        parse.require_sound_parent_map(proof)


def test_i_nine_the_same_parent_declaring_twice_is_not_a_conflict(tmp_path: Path) -> None:
    """One registrant naming its own overflow file twice binds one parent, not two."""
    archive = _archive(
        tmp_path, [(_SHARD, b"{}"), (_PRIMARY, _primary(1, [_SHARD, _SHARD]))], name="e.zip"
    )
    assert parse.structural_source_preflight(archive).parent_map_sound is True


def test_i_nine_a_declared_parent_the_filename_contradicts_refuses(tmp_path: Path) -> None:
    """The filename stays **corroboration** and is never promoted to a binding."""
    archive = _archive(
        tmp_path, [(_SHARD, b"{}"), ("CIK0000000002.json", _primary(2, [_SHARD]))], name="f.zip"
    )
    proof = parse.structural_source_preflight(archive)
    assert proof.conflicting_parent_count == 1
    assert proof.parent_map_sound is False
    with pytest.raises(parse.OfflineParseError, match="contradicts"):
        parse.require_sound_parent_map(proof)


def test_i_ten_a_declaration_naming_an_absent_member_binds_nothing(tmp_path: Path) -> None:
    """Bounded exactly as the accepted traversal bounds it: by shards, not by declarations."""
    archive = _archive(
        tmp_path,
        [(_PRIMARY, _primary(1, ["CIK0000000001-submissions-999.json"]))],
        name="g.zip",
    )
    proof = parse.structural_source_preflight(archive)
    assert proof.shard_members == 0
    assert proof.declared_shard_names == 0
    assert proof.parent_map_sound is True


def test_i_ten_the_digest_is_permutation_deterministic(tmp_path: Path) -> None:
    """Two archives with the same structure in different member order agree."""
    first = _archive(tmp_path, [(_SHARD, b"{}"), (_PRIMARY, _primary(1, [_SHARD]))], name="h1.zip")
    second = _archive(tmp_path, [(_PRIMARY, _primary(1, [_SHARD])), (_SHARD, b"{}")], name="h2.zip")
    left = parse.structural_source_preflight(first)
    right = parse.structural_source_preflight(second)
    # The ordering *observation* differs, because it is a fact about the archive; the structural
    # facts the parent map is built from do not.
    assert left.shard_before_parent != right.shard_before_parent
    assert left.orphan_shards == right.orphan_shards
    assert left.shard_members == right.shard_members
    assert left.declared_shard_names == right.declared_shard_names


def test_i_ten_the_preflight_writes_nothing_and_opens_no_database(tmp_path: Path) -> None:
    """**Read only.** It runs before ``create_world``, so it must create nothing itself."""
    archive = _archive(tmp_path, [(_SHARD, b"{}"), (_PRIMARY, _primary(1, [_SHARD]))], name="i.zip")
    before = sorted(entry.name for entry in tmp_path.iterdir())
    parse.structural_source_preflight(archive)
    assert sorted(entry.name for entry in tmp_path.iterdir()) == before


# ==========================================================================
# MAJOR-2 — one canonical durable launch envelope
# ==========================================================================
_TMUX = shutil.which("tmux")


def _bsd_time_supported() -> bool:
    """Whether this host's ``/usr/bin/time`` understands BSD ``-l``.

    A **capability** probe rather than a platform check. ``time -l`` is a BSD flag: GNU
    ``time``, which is what a Linux CI runner has, rejects it. Decision 133 is the precedent --
    a macOS-only assumption baked into a test is a portability defect in the test, and the
    repair is to guard on the capability rather than to delete the coverage or to hard-code
    ``sys.platform``.

    The canonical launch command this test covers is macOS-operator-only anyway: it also uses
    ``caffeinate``, ``diskutil``, ``pmset`` and ``ioreg``.
    """
    binary = Path("/usr/bin/time")
    if not binary.exists():
        return False
    try:
        probe = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [str(binary), "-l", "/bin/echo", "probe"],
            capture_output=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return probe.returncode == 0


_BSD_TIME = _bsd_time_supported()


@pytest.mark.skipif(_TMUX is None, reason="tmux is not installed on this host")
def test_m2_an_existing_tmux_server_still_receives_the_governed_tmpdir(tmp_path: Path) -> None:
    """**D140-R6.** The exact failure: a pane on an already-running server.

    ``SQLITE_TMPDIR`` exported in the launching shell reaches a pane only when tmux starts a
    **new server**. Attach to one that is already running -- which is the normal case for an
    operator who has a tmux open -- and the pane gets that server's environment, captured
    whenever it started. The operator's shell shows the right value and SQLite spills to the
    internal volume for thirty hours.

    The server below is started with a **wrong** value and the caller's environment carries a
    third one, so the only way the pane can report the governed value is ``-e``.
    """
    assert _TMUX is not None
    socket = f"d140-{os.getpid()}"
    stale = str(tmp_path / "stale-server-tmpdir")
    governed = str(tmp_path / "governed-external-tmp")
    out = tmp_path / "pane.txt"
    base = [_TMUX, "-L", socket]
    env = dict(os.environ)
    env["SQLITE_TMPDIR"] = str(tmp_path / "callers-shell-tmpdir")
    try:
        # A server that already exists, holding the wrong value.
        subprocess.run(
            [*base, "new-session", "-d", "-s", "stale", "sleep", "30"],
            check=True,
            env={**os.environ, "SQLITE_TMPDIR": stale},
            capture_output=True,
        )
        subprocess.run(
            [
                *base,
                "new-session",
                "-d",
                "-s",
                "governed",
                "-e",
                f"SQLITE_TMPDIR={governed}",
                "sh",
                "-c",
                f'printf "%s" "$SQLITE_TMPDIR" > {out}',
            ],
            check=True,
            env=env,
            capture_output=True,
        )
        for _ in range(100):
            if out.exists() and out.read_text(encoding="utf-8"):
                break
            time.sleep(0.05)
    finally:
        subprocess.run([*base, "kill-server"], check=False, capture_output=True)
    observed = out.read_text(encoding="utf-8")
    assert observed == governed
    assert observed != stale
    assert observed != env["SQLITE_TMPDIR"]


def test_m2_the_launcher_refuses_when_the_tmpdir_never_reached_the_pane(tmp_path: Path) -> None:
    """The check that turns a silent misconfiguration into a first-second refusal."""
    completed = subprocess.run(
        [sys.executable, str(_LAUNCHER), "--require-sqlite-tmpdir", "--check-only"],
        capture_output=True,
        text=True,
        check=False,
        env={k: v for k, v in os.environ.items() if k != "SQLITE_TMPDIR"},
    )
    assert completed.returncode == 3
    assert "LAUNCH_REFUSED_SQLITE_TMPDIR_ABSENT" in completed.stderr


def test_m2_stdout_and_stderr_survive_the_process_that_wrote_them(tmp_path: Path) -> None:
    """**D140-R6.** No required failure diagnosis may live only in a pane's scrollback."""
    stdout = tmp_path / "internal" / "stdout.log"
    stderr = tmp_path / "internal" / "stderr.log"
    pid_file = tmp_path / "internal" / "canary.pid"
    completed = subprocess.run(
        [
            sys.executable,
            str(_LAUNCHER),
            "--pid-file",
            str(pid_file),
            "--stdout",
            str(stdout),
            "--stderr",
            str(stderr),
            "--work-root",
            str(tmp_path / "volume" / "work"),
            "--",
            "/bin/sh",
            "-c",
            "echo canary-stdout; echo canary-stderr >&2; exit 7",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # The process is gone; its output is not.
    assert completed.returncode == 7
    assert stdout.read_text(encoding="utf-8").strip() == "canary-stdout"
    assert stderr.read_text(encoding="utf-8").strip() == "canary-stderr"
    assert "canary-stdout" not in completed.stdout
    assert pid_file.read_text(encoding="utf-8").strip().isdigit()


def test_m2_the_pid_record_names_the_exec_ed_process(tmp_path: Path) -> None:
    """``exec`` keeps the process id, so the recorded id is the one doing the work."""
    pid_file = tmp_path / "internal" / "canary.pid"
    stdout = tmp_path / "internal" / "stdout.log"
    subprocess.run(
        [
            sys.executable,
            str(_LAUNCHER),
            "--pid-file",
            str(pid_file),
            "--stdout",
            str(stdout),
            "--",
            "/bin/sh",
            "-c",
            'printf "%s" "$$"',
        ],
        check=True,
        capture_output=True,
    )
    assert (
        pid_file.read_text(encoding="utf-8").strip() == stdout.read_text(encoding="utf-8").strip()
    )


@pytest.mark.skipif(not _BSD_TIME, reason="/usr/bin/time does not support the BSD -l flag here")
def test_m2_the_resource_report_is_captured_durably(tmp_path: Path) -> None:
    """**D140-R6 and INFO-4.** Peak RSS is measured, and it outlives the pane."""
    report = tmp_path / "internal" / "resource.log"
    report.parent.mkdir(parents=True)
    subprocess.run(
        ["/usr/bin/time", "-l", "-o", str(report), "/bin/echo", "measured"],
        check=True,
        capture_output=True,
    )
    text = report.read_text(encoding="utf-8")
    assert "maximum resident set size" in text
    assert any(
        line.strip().split()[0].isdigit() for line in text.splitlines() if "resident" in line
    )


def test_m2_caffeinate_holds_its_assertions_for_the_child_lifetime(tmp_path: Path) -> None:
    """**D140-R6.** ``-dims``, and the assertions are actually held while the child runs."""
    if not Path("/usr/bin/caffeinate").exists():  # pragma: no cover - macOS only
        pytest.skip("caffeinate is not available on this host")
    child = subprocess.Popen(
        ["/usr/bin/caffeinate", "-dims", "/bin/sleep", "5"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        held = ""
        for _ in range(60):
            observed = subprocess.run(
                ["/usr/bin/pmset", "-g", "assertions"], capture_output=True, text=True, check=False
            ).stdout
            if "caffeinate" in observed:
                held = observed
                break
            time.sleep(0.1)
        assert "caffeinate" in held
        assert child.poll() is None
    finally:
        child.kill()
        child.wait(timeout=10)


# ==========================================================================
# MINOR-7 — the source is authenticated before a world exists
# ==========================================================================
def test_m_seven_the_frozen_governed_identity_is_recorded_exactly() -> None:
    """The accepted M3.2 inventory facts, as executable constants."""
    assert canary.GOVERNED_SOURCE_BYTE_LENGTH == 1_556_847_020
    assert canary.GOVERNED_SOURCE_SHA256 == (
        "c85744be921b0dc5be4e3c7dd44552fc0f57d354d61df38cd92a13926982b82f"
    )
    assert canary.GOVERNED_SOURCE_MEMBERS == 985_834
    assert canary.GOVERNED_SOURCE_HISTORICAL_SHARDS == 5_337


def test_m_seven_an_unbound_source_refuses_before_a_world_exists(tmp_path: Path) -> None:
    """A source with no stored artifact cannot be authenticated, so it is refused."""
    from disclosure_drift.m3.offline_parse import PlannedSource, SelectedPlannedSource

    selected = SelectedPlannedSource(
        source=PlannedSource(
            census_run_id="run",
            source_instance_id="instance",
            source_id="sec_bulk_submissions",
            request_identity="identity",
            required=True,
            source_scope="base",
            retrieval_state="complete",
            snapshot_state="stored",
            parser_state="not_started",
            observation_id=None,
        ),
        plan_position=1,
        plan_source_count=1,
    )
    with pytest.raises(canary.SingleSourceCanaryError, match="not bound to a stored artifact"):
        canary.preauthenticate_source(
            tree=DataTree.from_root(tmp_path), selected=selected, observation=None
        )


# ==========================================================================
# INFO-1 / INFO-2 — F0, F1 and the F2 tail are actually sampled
# ==========================================================================
def test_i_one_f0_and_f1_are_sampled_rather_than_merely_bracketed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D140-R14.** Decision 138 left F0 and F1 entirely unobserved.

    Between ``PRE_LAUNCH`` and ``POST_F0`` the accepted run took **no** capacity reading at all,
    across roughly 985,000 parts and the great majority of a thirty-hour run; F1 was the same.
    The floors were real and nothing sampled them for hours at a time.

    The trace below records phase boundaries and guard samples in the order they happen, so a
    sample landing *between* two boundaries is what proves the interior of a phase is covered --
    which is precisely what bracketing it could not do.
    """
    private = d116._private_root(tmp_path)
    d138._external_volume(monkeypatch, tmp_path)
    (tmp_path / "work").mkdir(exist_ok=True)
    trace: list[str] = []

    real_observe = canary.observe_capacity

    def _tracing_observe(phase: str, **kwargs: Any) -> Any:
        trace.append(f"PHASE:{phase}")
        return real_observe(phase, **kwargs)

    monkeypatch.setattr(canary, "observe_capacity", _tracing_observe)

    class _TracingGuard(ewr.F2CapacityGuard):
        def __call__(self) -> None:
            trace.append("SAMPLE")
            # Forced to sample on every call: the interval is a cost control, and this test is
            # about whether the call site exists at all.
            self._sample()

    monkeypatch.setattr(canary, "F2CapacityGuard", _TracingGuard)

    result = canary.run_single_source_canary(
        operational_catalog=d116._catalog(private),
        tree=DataTree.from_root(private),
        work_root=tmp_path / "work",
        run_id="d140-sampled",
        source_instance_id=d116._BULK_INSTANCE,
        require_volume_uuid=_QUALIFIED,
    )

    assert "PHASE:POST_F0" in trace
    post_f0 = trace.index("PHASE:POST_F0")
    pre_f1 = trace.index("PHASE:PRE_F1")
    post_f1 = trace.index("PHASE:POST_F1_PRE_F2")
    post_f2 = trace.index("PHASE:POST_F2")
    members = result.members
    assert members > 0

    # **The assertion has to be about the interior, not about the phase.** Asserting merely that
    # *a* sample happened before POST_F0 is satisfied by the two fixed readings that bracket F0's
    # finalization block -- so it survives deleting the per-part call entirely, which is the one
    # thing INFO-1 is about. Counting is what distinguishes "sampled" from "sampled per unit of
    # work": with the loop call present the count grows with the number of parts, and without it
    # the count is a constant.
    f0_samples = trace[:post_f0].count("SAMPLE")
    assert f0_samples >= members, (
        f"F0 took {f0_samples} readings across {members} parts; sampling must scale with the "
        "work, not be a fixed bracket around it"
    )
    # F1's interior, on the same rule: one reading per resolved accession boundary.
    f1_samples = trace[pre_f1:post_f1].count("SAMPLE")
    assert f1_samples >= 1
    # F2, including its totality tail, between the pre-F2 boundary and POST_F2.
    assert "SAMPLE" in trace[post_f1:post_f2]


def test_i_two_the_f2_totality_tail_is_bracketed_by_readings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D140-R14.** Nothing can be sampled inside one aggregate SQL statement, so the tail is
    bracketed: a reading immediately before it and one immediately after."""
    source = Path(parse.__file__).read_text(encoding="utf-8")
    body = source.split("def materialize_census_associations")[1].split("\ndef ")[0]
    tail = body.split("totality = _measure_association_totality")
    assert len(tail) == 2
    assert "capacity_guard()" in tail[0].rsplit("\n\n", 1)[-1] or "capacity_guard()" in tail[0]
    assert "capacity_guard()" in tail[1]
