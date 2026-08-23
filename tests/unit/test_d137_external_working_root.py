"""Accepted Decision 137 — the external working-root guards, proved by counterexample.

Every claim here is stated as *what stops being possible*, because that is what a fail-closed
guard is for. A test that only shows the good path passing would leave every one of these
questions open: does a **different** volume pass? does a path that resolves **into** the archive
pass? does `185` GiB **minus one byte** pass? does an **internal** temporary directory pass? So
each guard is exercised at its boundary and against the exact state it exists to refuse.

**No test here touches the operator's SSD.** Volume identity is supplied through the accepted
:data:`~disclosure_drift.m3.external_working_root.VolumeIdentityProvider` seam, free space through
a pinned ``shutil.disk_usage``, and the D130 archive through a synthetic fixture whose "tar" is a
few bytes of the wrong content at a stated length. Nothing is mounted, written, ejected, or
measured on a real external device, and the real `104` GB archive is never opened.

**Nothing here authorizes a canary.** These guards decide whether a launch *may* be attempted;
accepted Decision 137 (D137-R12) reserves the decision that it *is* attempted to a separate owner
instrument, and no test asserts one exists.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d116_single_source_canary as d116  # noqa: E402
import test_d131_signal_and_monitor as d131  # noqa: E402

from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.working_catalog import file_digest  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]

#: The accepted qualified volume, restated independently of the constant so the pin is a second
#: opinion rather than an echo of the value under test (accepted Decision 136 §4, D136-R1).
_QUALIFIED = "397A4D4A-9508-391E-814E-3B533C7BD049"

#: Any other volume. The exact string does not matter; that it is not the accepted one does.
_OTHER = "0BADCAFE-0000-0000-0000-000000000000"

#: `185` GiB and `50` GiB, in bytes, both stated as literals for the same reason.
_LAUNCH_FLOOR = 198_642_237_440
_PRE_F2_FLOOR = 53_687_091_200


# ==========================================================================
# Fixtures: a synthetic qualified volume, and a synthetic D130 archive
# ==========================================================================
def _provider(mapping: dict[Path, str], *, fail: bool = False) -> ewr.VolumeIdentityProvider:
    """A volume-identity provider that answers from a table instead of from ``diskutil``.

    A path is answered by the longest mapped prefix, which is how a real mount point behaves:
    everything beneath it is on it. An unmapped path is "no volume here" -- the missing-mount
    case -- and ``fail=True`` makes every lookup raise, which is the lookup-error case.
    """

    def lookup(path: Path) -> ewr.VolumeIdentity:
        if fail:
            message = "the volume lookup failed"
            raise ewr.ExternalWorkingRootError(message)
        resolved = Path(os.path.realpath(path))
        best: Path | None = None
        for mount in mapping:
            on_it = resolved == mount or mount in resolved.parents
            if on_it and (best is None or len(mount.parts) > len(best.parts)):
                best = mount
        if best is None:
            message = "no volume is mounted at the selected working root"
            raise ewr.ExternalWorkingRootError(message)
        return ewr.VolumeIdentity(
            volume_uuid=mapping[best],
            mount_point=best,
            filesystem_type="exfat",
            device_identifier="diskN sN",
        )

    return lookup


def _fake_usage(free: int, total: int = 500_000_000_000) -> SimpleNamespace:
    """A ``shutil.disk_usage`` stand-in. Only ``.free`` and ``.total`` are read anywhere."""
    return SimpleNamespace(total=total, used=total - free, free=free)


def _pin_free(monkeypatch: pytest.MonkeyPatch, free: int) -> None:
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: _fake_usage(free))


# ==========================================================================
# A. The volume identity guard — D137-R1
# ==========================================================================
def test_the_expected_uuid_passes(tmp_path: Path) -> None:
    """The accepted volume is authenticated, and its identity is returned rather than assumed."""
    volume = tmp_path / "volume"
    (volume / "world").mkdir(parents=True)
    identity = ewr.require_qualified_volume(
        volume / "world", expected_uuid=_QUALIFIED, provider=_provider({volume: _QUALIFIED})
    )
    assert identity.volume_uuid == _QUALIFIED
    assert identity.mount_point == volume


def test_a_wrong_uuid_is_refused(tmp_path: Path) -> None:
    """A different volume mounted where the right one was is the case a mount path cannot see."""
    volume = tmp_path / "volume"
    (volume / "world").mkdir(parents=True)
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        ewr.require_qualified_volume(
            volume / "world", expected_uuid=_QUALIFIED, provider=_provider({volume: _OTHER})
        )


def test_a_missing_volume_is_refused(tmp_path: Path) -> None:
    """Nothing mounted where the root points refuses; it does not fall back to internal storage."""
    with pytest.raises(ewr.ExternalWorkingRootError, match="no volume is mounted"):
        ewr.require_qualified_volume(
            tmp_path / "absent", expected_uuid=_QUALIFIED, provider=_provider({})
        )


def test_a_lookup_failure_is_refused(tmp_path: Path) -> None:
    """A lookup that fails is refused, never treated as an unauthenticated pass."""
    with pytest.raises(ewr.ExternalWorkingRootError):
        ewr.require_qualified_volume(
            tmp_path, expected_uuid=_QUALIFIED, provider=_provider({}, fail=True)
        )


def test_the_uuid_comparison_is_case_insensitive_and_otherwise_exact(tmp_path: Path) -> None:
    """``diskutil`` reports upper case; an operator may type either. A prefix is still wrong."""
    volume = tmp_path / "volume"
    volume.mkdir()
    lowered = _QUALIFIED.lower()
    assert (
        ewr.require_qualified_volume(
            volume, expected_uuid=_QUALIFIED, provider=_provider({volume: lowered})
        ).volume_uuid
        == lowered
    )
    truncated = _QUALIFIED[:-1]
    with pytest.raises(ewr.ExternalWorkingRootError):
        ewr.require_qualified_volume(
            volume, expected_uuid=_QUALIFIED, provider=_provider({volume: truncated})
        )


def test_the_frozen_uuid_is_the_decision_136_volume() -> None:
    """One frozen identity, pinned to its literal rather than to whatever is attached today."""
    assert ewr.QUALIFIED_EXTERNAL_VOLUME_UUID == _QUALIFIED
    assert "QUALIFIED_EXTERNAL_VOLUME_UUID" in ewr.__all__


def test_the_mount_point_is_derived_from_device_numbers_not_from_the_path(tmp_path: Path) -> None:
    """``mount_point_of`` walks device boundaries, so an operator cannot assert a mount point."""
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    # Everything under tmp_path is one filesystem, so the walk must not stop inside it.
    assert ewr.mount_point_of(nested) == ewr.mount_point_of(tmp_path)


def test_the_mount_point_of_a_path_that_does_not_exist_yet_is_its_volume(tmp_path: Path) -> None:
    """A working root is identified before it is created, so an absent path must still answer."""
    assert ewr.mount_point_of(tmp_path / "not-created-yet") == ewr.mount_point_of(tmp_path)


# ==========================================================================
# B. Archive isolation — D137-R3
# ==========================================================================
def test_a_sibling_tree_at_the_volume_root_is_accepted(tmp_path: Path) -> None:
    """The accepted shape: beside the archive, not beneath it."""
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    sibling = tmp_path / "FDD_M3_3_D137_WORLD"
    assert ewr.require_outside_d130_archive(sibling, archive=archive) == Path(
        os.path.realpath(sibling)
    )


def test_the_archive_directory_itself_is_refused(tmp_path: Path) -> None:
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    with pytest.raises(ewr.ExternalWorkingRootError, match="is the immutable D130 archive"):
        ewr.require_outside_d130_archive(archive, archive=archive)


def test_a_child_of_the_archive_is_refused(tmp_path: Path) -> None:
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    with pytest.raises(ewr.ExternalWorkingRootError, match="lies inside the immutable D130"):
        ewr.require_outside_d130_archive(archive / "world", archive=archive)


def test_a_dot_dot_path_that_normalizes_into_the_archive_is_refused(tmp_path: Path) -> None:
    """``realpath`` collapses ``..`` **before** anything is compared, so this cannot launder."""
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    (tmp_path / "elsewhere").mkdir()
    laundered = tmp_path / "elsewhere" / ".." / ewr.D130_ARCHIVE_DIRECTORY_NAME / "world"
    with pytest.raises(ewr.ExternalWorkingRootError, match="lies inside the immutable D130"):
        ewr.require_outside_d130_archive(laundered, archive=archive)


def test_a_symlink_resolving_into_the_archive_is_refused(tmp_path: Path) -> None:
    """Symlinks are followed on both sides, so an alias is not a way in."""
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    (archive / "inside").mkdir(parents=True)
    alias = tmp_path / "innocent-looking"
    alias.symlink_to(archive / "inside", target_is_directory=True)
    with pytest.raises(ewr.ExternalWorkingRootError, match="lies inside the immutable D130"):
        ewr.require_outside_d130_archive(alias, archive=archive)


def test_a_benign_similarly_prefixed_sibling_is_not_falsely_refused(tmp_path: Path) -> None:
    """Containment is decided on path **components**; a shared name prefix is not containment.

    A string ``startswith`` check would refuse this, and refusing a lawful root is a bug even
    though it fails in the safe direction: the operator would have no correct path to offer.
    """
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    lookalike = tmp_path / f"{ewr.D130_ARCHIVE_DIRECTORY_NAME}_WORKING"
    assert ewr.require_outside_d130_archive(lookalike, archive=archive)


def test_a_working_root_that_would_swallow_the_archive_is_refused(tmp_path: Path) -> None:
    """The volume root is not a lawful working root.

    The archive would then be inside a disposable tree -- the shape the accepted sibling layout
    exists to avoid.
    """
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    with pytest.raises(ewr.ExternalWorkingRootError, match="contains the immutable D130"):
        ewr.require_outside_d130_archive(tmp_path, archive=archive)


# ==========================================================================
# C. The launch free-space floor — D137-R4
# ==========================================================================
def test_the_launch_floor_is_exactly_one_hundred_and_eighty_five_gibibytes() -> None:
    assert ewr.LAUNCH_MINIMUM_FREE_BYTES == _LAUNCH_FLOOR
    assert ewr.LAUNCH_MINIMUM_FREE_BYTES == 185 * 1024**3


@pytest.mark.parametrize(
    ("free", "label"),
    [(_LAUNCH_FLOOR, "exactly at the floor"), (_LAUNCH_FLOOR + 1, "one byte above it")],
)
def test_at_or_above_the_launch_floor_admits(
    free: int, label: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``>=`` is the rule, so the floor itself admits -- ``label`` names which case failed."""
    _pin_free(monkeypatch, free)
    assert ewr.require_launch_free_space(tmp_path) == free


def test_one_byte_below_the_launch_floor_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The boundary is proved at the floor: an off-by-one here is what a "roughly" test misses."""
    _pin_free(monkeypatch, _LAUNCH_FLOOR - 1)
    with pytest.raises(ewr.ExternalWorkingRootError) as raised:
        ewr.require_launch_free_space(tmp_path)
    message = str(raised.value)
    assert str(_LAUNCH_FLOOR - 1) in message
    assert str(_LAUNCH_FLOOR) in message
    assert "Nothing was deleted or cleaned" in message


def test_the_launch_floor_measures_the_selected_root_not_the_process_volume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D137-R4: the measurement is taken on the path handed in, not on some other filesystem."""
    seen: list[Path] = []

    def record(path: Path) -> SimpleNamespace:
        seen.append(Path(path))
        return _fake_usage(_LAUNCH_FLOOR)

    monkeypatch.setattr(shutil, "disk_usage", record)
    target = tmp_path / "external" / "world"
    target.mkdir(parents=True)
    ewr.require_launch_free_space(target)
    assert seen == [target]


def test_an_unmeasurable_volume_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A measurement that cannot be taken fails closed rather than admitting on a missing value."""

    def explode(_path: Path) -> SimpleNamespace:
        raise OSError(5, "Input/output error")

    monkeypatch.setattr(shutil, "disk_usage", explode)
    with pytest.raises(ewr.ExternalWorkingRootError, match="could not be measured"):
        ewr.require_launch_free_space(tmp_path)


# ==========================================================================
# D. The pre-F2 floor points at the active working volume — D137-R5
# ==========================================================================
def test_the_pre_f2_guard_measures_the_working_worlds_own_volume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate is dispositive only if it measures the volume F2 will actually consume."""
    seen: list[Path] = []

    def record(path: Path) -> SimpleNamespace:
        seen.append(Path(path))
        return _fake_usage(_PRE_F2_FLOOR)

    monkeypatch.setattr(shutil, "disk_usage", record)
    world = tmp_path / "external-volume" / "world"
    world.mkdir(parents=True)
    assert canary._require_pre_f2_free_space(world) == _PRE_F2_FLOOR
    assert seen == [world]


def test_the_pre_f2_floor_matches_the_decision_137_value() -> None:
    """One number, two places it must agree: the canary constant and the D137 byte literal."""
    assert canary.PRE_F2_MINIMUM_FREE_BYTES == _PRE_F2_FLOOR


# ==========================================================================
# E. Continuous F2 monitoring — D137-R6
# ==========================================================================
def test_the_continuous_thresholds_are_twenty_and_ten_gibibytes() -> None:
    """The admission gate moved to `50` GiB; these two did not move with it."""
    assert ewr.F2_ALERT_FREE_BYTES == 20 * 1024**3 == 21_474_836_480
    assert ewr.F2_HARD_FLOOR_FREE_BYTES == 10 * 1024**3 == 10_737_418_240


@pytest.mark.parametrize(
    ("free", "expected"),
    [
        (ewr.F2_ALERT_FREE_BYTES + 1, ewr.F2_NORMAL_STATE),
        (ewr.F2_ALERT_FREE_BYTES, ewr.F2_ALERT_STATE),
        (ewr.F2_HARD_FLOOR_FREE_BYTES + 1, ewr.F2_ALERT_STATE),
        (ewr.F2_HARD_FLOOR_FREE_BYTES, ewr.F2_HARD_STOP_STATE),
        (0, ewr.F2_HARD_STOP_STATE),
    ],
)
def test_the_continuous_states_are_classified_at_their_boundaries(free: int, expected: str) -> None:
    """Both thresholds are inclusive, and the band between them alerts without stopping."""
    assert ewr.f2_capacity_state(free) == expected


def test_one_byte_above_the_hard_floor_does_not_hard_stop() -> None:
    """Raising the admission gate to `50` GiB must not have raised the emergency floor with it."""
    assert ewr.f2_capacity_state(ewr.F2_HARD_FLOOR_FREE_BYTES + 1) != ewr.F2_HARD_STOP_STATE


# ==========================================================================
# F. Phase-boundary observability — D137-R7
# ==========================================================================
def test_the_accepted_phase_labels_are_the_decision_135_set() -> None:
    assert ewr.CAPACITY_PHASES == (
        "PRE_LAUNCH",
        "POST_F0",
        "PRE_F1",
        "POST_F1_PRE_F2",
        "DURING_F2",
        "POST_F2",
    )


def test_an_invented_phase_label_is_refused(tmp_path: Path) -> None:
    """Stage values are not invented at a call site; the accepted set is the whole set."""
    with pytest.raises(ewr.ExternalWorkingRootError, match="not an accepted capacity phase"):
        ewr.observe_capacity("MID_F1", working_root=tmp_path, observed_at="2026-08-23T00:00:00Z")


def test_an_unknown_measurement_stays_unknown(tmp_path: Path) -> None:
    """``None``, never ``0``: a missing WAL and a checkpointed one must stay distinguishable."""
    observation = ewr.observe_capacity(
        "PRE_LAUNCH", working_root=tmp_path, observed_at="2026-08-23T00:00:00Z"
    )
    assert observation.database_bytes is None
    assert observation.wal_bytes is None
    assert observation.temp_bytes is None
    assert observation.free_bytes > 0


def test_a_measured_observation_records_what_it_could_measure(tmp_path: Path) -> None:
    """Sizes come from the filesystem, and the record carries no absolute path."""
    database = tmp_path / "working.sqlite3"
    database.write_bytes(b"x" * 4096)
    wal = tmp_path / "working.sqlite3-wal"
    wal.write_bytes(b"y" * 512)
    temp = tmp_path / "temp"
    temp.mkdir()
    (temp / "etilqs_1").write_bytes(b"z" * 1024)
    observation = ewr.observe_capacity(
        "DURING_F2",
        working_root=tmp_path,
        database=database,
        wal=wal,
        temp_directory=temp,
        volume=ewr.VolumeIdentity(
            volume_uuid=_QUALIFIED,
            mount_point=tmp_path,
            filesystem_type="exfat",
            device_identifier="diskN sN",
        ),
        observed_at="2026-08-23T00:00:00Z",
    )
    record = observation.as_record()
    assert record["database_bytes"] == 4096
    assert record["wal_bytes"] == 512
    assert record["temp_bytes"] == 1024
    assert record["phase"] == "DURING_F2"
    assert record["f2_capacity_state"] in {
        ewr.F2_NORMAL_STATE,
        ewr.F2_ALERT_STATE,
        ewr.F2_HARD_STOP_STATE,
    }
    assert str(tmp_path) not in repr(record)


# ==========================================================================
# G. SQLITE_TMPDIR — D137-R8
# ==========================================================================
def _external_world(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A synthetic qualified volume with an archive, a working root, and a temporary root."""
    volume = tmp_path / "volume"
    archive = volume / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir(parents=True)
    work = volume / "FDD_M3_3_D137_WORK"
    work.mkdir()
    temp = volume / "FDD_M3_3_D137_TMP"
    temp.mkdir()
    return volume, work, temp


def test_an_explicit_external_temporary_root_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    volume, work, temp = _external_world(tmp_path)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(temp))
    resolved = ewr.require_external_sqlite_tmpdir(
        working_root=work,
        archive=volume / ewr.D130_ARCHIVE_DIRECTORY_NAME,
        environ={ewr.SQLITE_TMPDIR_ENV: str(temp)},
        expected_uuid=_QUALIFIED,
        provider=_provider({volume: _QUALIFIED}),
    )
    assert resolved == Path(os.path.realpath(temp))


def test_an_unset_temporary_root_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unset means SQLite spills to the internal volume silently. That is the failure."""
    volume, work, _temp = _external_world(tmp_path)
    monkeypatch.delenv(ewr.SQLITE_TMPDIR_ENV, raising=False)
    with pytest.raises(ewr.ExternalWorkingRootError, match="is not set"):
        ewr.require_external_sqlite_tmpdir(
            working_root=work,
            archive=volume / ewr.D130_ARCHIVE_DIRECTORY_NAME,
            environ={},
            expected_uuid=_QUALIFIED,
            provider=_provider({volume: _QUALIFIED}),
        )


def test_an_internal_temporary_root_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact silent-fallback case.

    A temporary root on a volume that is not the qualified one is refused, so SQLite cannot spill
    onto internal storage while the world it serves is external.
    """
    volume, work, _temp = _external_world(tmp_path)
    internal = tmp_path / "internal"
    internal.mkdir()
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(internal))
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        ewr.require_external_sqlite_tmpdir(
            working_root=work,
            archive=volume / ewr.D130_ARCHIVE_DIRECTORY_NAME,
            environ={ewr.SQLITE_TMPDIR_ENV: str(internal)},
            expected_uuid=_QUALIFIED,
            provider=_provider({volume: _QUALIFIED, internal: _OTHER}),
        )


def test_a_temporary_root_inside_the_archive_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    volume, work, _temp = _external_world(tmp_path)
    archive = volume / ewr.D130_ARCHIVE_DIRECTORY_NAME
    inside = archive / "tmp"
    inside.mkdir()
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(inside))
    with pytest.raises(ewr.ExternalWorkingRootError, match="lies inside the immutable D130"):
        ewr.require_external_sqlite_tmpdir(
            working_root=work,
            archive=archive,
            environ={ewr.SQLITE_TMPDIR_ENV: str(inside)},
            expected_uuid=_QUALIFIED,
            provider=_provider({volume: _QUALIFIED}),
        )


def test_a_relative_or_absent_temporary_root_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    volume, work, _temp = _external_world(tmp_path)
    archive = volume / ewr.D130_ARCHIVE_DIRECTORY_NAME
    for value, expected in (
        ("relative/tmp", "not an absolute path"),
        (str(volume / "never-created"), "does not name an existing directory"),
    ):
        monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, value)
        with pytest.raises(ewr.ExternalWorkingRootError, match=expected):
            ewr.require_external_sqlite_tmpdir(
                working_root=work,
                archive=archive,
                environ={ewr.SQLITE_TMPDIR_ENV: value},
                expected_uuid=_QUALIFIED,
                provider=_provider({volume: _QUALIFIED}),
            )


# ==========================================================================
# H. The bounded D130 archive pre/postcheck — D137-R10
# ==========================================================================
def test_the_archive_proofs_are_the_decision_130_identities() -> None:
    """Four digests and one length. The `104` GB tar carries no digest, by design."""
    by_name = {proof.name: proof for proof in ewr.D130_COMPACT_PROOFS}
    tar = by_name[ewr.D130_ARCHIVE_TAR_NAME]
    assert tar.sha256 is None
    assert tar.byte_length == 103_966_696_960
    assert sum(1 for proof in ewr.D130_COMPACT_PROOFS if proof.sha256 is not None) == 4
    assert {proof.name for proof in ewr.D130_COMPACT_PROOFS if proof.sha256 is not None} == {
        "d128_source_manifest.tsv",
        "d128_tar_member_manifest.tsv",
        "d128_archive_receipt.txt",
        "d130_post_deletion_proof.txt",
    }


def _synthetic_archive(root: Path) -> tuple[Path, tuple[ewr.ArchiveProof, ...]]:
    """A small stand-in archive, and the proof table that describes it.

    The accepted digests are of files this repository does not contain, so the fixture writes its
    own bytes and computes the table over them. It keeps the accepted table's **shape** exactly:
    four members carry a digest, and the stand-in for the large tar carries a length and
    ``None``. The accepted literals themselves are pinned separately, above.

    The stand-in tar is a few bytes rather than `104` GB. Creating the real length would only
    prove that ``truncate`` works.
    """
    archive = root / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir(parents=True)
    proofs: list[ewr.ArchiveProof] = []
    for proof in ewr.D130_COMPACT_PROOFS:
        member = archive / proof.name
        payload = b"d137-fixture-" + proof.name.encode()
        member.write_bytes(payload)
        proofs.append(
            ewr.ArchiveProof(
                name=proof.name,
                byte_length=len(payload),
                sha256=(None if proof.sha256 is None else hashlib.sha256(payload).hexdigest()),
            )
        )
    return archive, tuple(proofs)


def test_an_intact_archive_reports_no_differences(tmp_path: Path) -> None:
    archive, proofs = _synthetic_archive(tmp_path)
    assert ewr.verify_d130_archive(archive, proofs=proofs) == ()


def test_the_large_tar_is_never_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Proved by a tripwire on the read itself, not by reading the source -- D137-R10.

    ``verify_d130_archive`` is run with a tripwire installed over :meth:`Path.read_bytes` that
    fails outright if the tar is ever opened. The check still returns "no differences", so the
    tar's `103,966,696,960` bytes were never touched -- which is the whole point of pairing a
    length-only proof with four small digests.
    """
    archive, proofs = _synthetic_archive(tmp_path)
    reached: list[str] = []
    real_read = Path.read_bytes

    def tripwire(self: Path) -> bytes:
        if self.name == ewr.D130_ARCHIVE_TAR_NAME:
            reached.append(self.name)
            message = "the D130 archive tar must never be read"
            raise AssertionError(message)
        return real_read(self)

    monkeypatch.setattr(Path, "read_bytes", tripwire)
    assert ewr.verify_d130_archive(archive, proofs=proofs) == ()
    assert reached == []


def test_a_wrong_length_is_reported(tmp_path: Path) -> None:
    archive, proofs = _synthetic_archive(tmp_path)
    member = archive / "d128_archive_receipt.txt"
    member.write_bytes(member.read_bytes() + b"!")
    differences = ewr.verify_d130_archive(archive, proofs=proofs)
    assert any("d128_archive_receipt.txt" in difference for difference in differences)


def test_a_wrong_digest_at_the_right_length_is_reported(tmp_path: Path) -> None:
    """Length alone is not the proof for the small files; the digest is."""
    archive, proofs = _synthetic_archive(tmp_path)
    member = archive / "d128_archive_receipt.txt"
    payload = bytearray(member.read_bytes())
    payload[0] ^= 0xFF
    member.write_bytes(bytes(payload))
    differences = ewr.verify_d130_archive(archive, proofs=proofs)
    assert any("digest" in difference for difference in differences)


def test_a_wrong_tar_length_is_reported(tmp_path: Path) -> None:
    """The tar has no digest, so its length is the only thing standing between it and a swap."""
    archive, proofs = _synthetic_archive(tmp_path)
    (archive / ewr.D130_ARCHIVE_TAR_NAME).write_bytes(b"short")
    differences = ewr.verify_d130_archive(archive, proofs=proofs)
    assert any(ewr.D130_ARCHIVE_TAR_NAME in difference for difference in differences)


def test_an_absent_member_is_reported(tmp_path: Path) -> None:
    archive, proofs = _synthetic_archive(tmp_path)
    (archive / "d130_post_deletion_proof.txt").unlink()
    assert any(
        "absent" in difference for difference in ewr.verify_d130_archive(archive, proofs=proofs)
    )


def test_an_absent_archive_directory_is_reported(tmp_path: Path) -> None:
    assert ewr.verify_d130_archive(tmp_path / "nothing-here") == (
        "the D130 archive directory is absent or is not a directory",
    )


# ==========================================================================
# I. The composed preflight — every guard, in order
# ==========================================================================
def test_the_composed_preflight_passes_and_authorizes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every guard holds, one PRE_LAUNCH observation is recorded, and no authority is implied."""
    volume, work, temp = _external_world(tmp_path)
    _pin_free(monkeypatch, _LAUNCH_FLOOR)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(temp))
    preflight = ewr.external_canary_preflight(
        working_root=work,
        observed_at="2026-08-23T00:00:00Z",
        environ={ewr.SQLITE_TMPDIR_ENV: str(temp)},
        expected_uuid=_QUALIFIED,
        provider=_provider({volume: _QUALIFIED}),
        require_archive=False,
    )
    assert preflight.volume.volume_uuid == _QUALIFIED
    assert preflight.launch_free_bytes == _LAUNCH_FLOOR
    assert preflight.sqlite_tmpdir_verified is True
    assert preflight.observation.phase == "PRE_LAUNCH"
    record = preflight.as_record()
    assert record["canary_authorized"] is False
    # D137-R12: nothing was created. No world, no run id, no receipt, no namespace.
    assert sorted(p.name for p in volume.iterdir()) == sorted(
        [ewr.D130_ARCHIVE_DIRECTORY_NAME, "FDD_M3_3_D137_WORK", "FDD_M3_3_D137_TMP"]
    )
    assert list(work.iterdir()) == []


@pytest.mark.parametrize(
    ("break_it", "expected"),
    [
        ("uuid", "not the accepted qualified volume"),
        ("archive", "lies inside the immutable D130"),
        ("capacity", "launch free-space floor not met"),
        ("tmpdir", "is not set"),
    ],
)
def test_the_composed_preflight_refuses_when_any_single_guard_fails(
    break_it: str, expected: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One broken condition at a time, so each refusal is attributed to its own guard."""
    volume, work, temp = _external_world(tmp_path)
    archive = volume / ewr.D130_ARCHIVE_DIRECTORY_NAME
    uuid = _OTHER if break_it == "uuid" else _QUALIFIED
    root = (archive / "world") if break_it == "archive" else work
    if break_it == "archive":
        root.mkdir()
    _pin_free(monkeypatch, _LAUNCH_FLOOR - 1 if break_it == "capacity" else _LAUNCH_FLOOR)
    environ = {} if break_it == "tmpdir" else {ewr.SQLITE_TMPDIR_ENV: str(temp)}
    with pytest.raises(ewr.ExternalWorkingRootError, match=expected):
        ewr.external_canary_preflight(
            working_root=root,
            observed_at="2026-08-23T00:00:00Z",
            environ=environ,
            expected_uuid=_QUALIFIED,
            provider=_provider({volume: uuid}),
            require_archive=False,
        )


def test_the_preflight_refuses_when_the_archive_precheck_differs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A launch beside an archive whose identity cannot be confirmed is refused -- D137-R10."""
    volume = tmp_path / "volume"
    work = volume / "FDD_M3_3_D137_WORK"
    work.mkdir(parents=True)
    temp = volume / "FDD_M3_3_D137_TMP"
    temp.mkdir()
    (volume / ewr.D130_ARCHIVE_DIRECTORY_NAME).mkdir()
    _pin_free(monkeypatch, _LAUNCH_FLOOR)
    with pytest.raises(ewr.ExternalWorkingRootError, match="archive precheck differs"):
        ewr.external_canary_preflight(
            working_root=work,
            observed_at="2026-08-23T00:00:00Z",
            environ={ewr.SQLITE_TMPDIR_ENV: str(temp)},
            expected_uuid=_QUALIFIED,
            provider=_provider({volume: _QUALIFIED}),
            require_archive=True,
        )


# ==========================================================================
# J. The run path is held to the same guards — no escape to internal storage
# ==========================================================================
def test_a_run_on_a_wrong_volume_is_refused_before_a_world_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The library boundary, not only the operator surface: D137-R1 with nothing created."""
    private = d116._private_root(tmp_path)
    database = d116._catalog(private)
    before = file_digest(database)[0]
    work = tmp_path / "work"
    monkeypatch.setattr(ewr, "macos_volume_identity", _provider({tmp_path: _OTHER}))

    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        canary.run_single_source_canary(
            operational_catalog=database,
            tree=DataTree.from_root(private),
            work_root=work,
            run_id="d137-refused",
            source_instance_id=d116._BULK_INSTANCE,
            require_volume_uuid=_QUALIFIED,
        )

    assert not (work / "d137-refused").exists()
    assert file_digest(database)[0] == before


def test_a_run_with_no_requirement_is_unchanged(tmp_path: Path) -> None:
    """``require_volume_uuid=None`` is the accepted Decision 116 path, byte for byte.

    The result document must carry **no** ``capacity_observations`` key: adding one would change
    every canary result ever produced, including the byte-level evidence-equivalence the accepted
    Decision 119 cache-budget proof rests on.
    """
    result, _private, _world = d116._run(tmp_path, run_id="d137-internal")
    assert result.capacity_observations == ()
    assert "capacity_observations" not in result.as_record()


def test_an_external_run_records_every_phase_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D137-R7 over a real run: the five phase boundaries, in order.

    ``DURING_F2`` does not appear here, and the reason changed with accepted **Decision 138**.
    It is no longer that F2 cannot be sampled in-process -- D138-R8 samples it from inside the
    transaction, and D138-R9 bounds the interval. It is that this run never enters the alert
    band: a ``DURING_F2`` record is written only when free space falls to `20` GiB or below, so
    a healthy F2 records none and an invented one would still be a measurement never taken. See
    ``test_d138_safety_envelope_correction.py`` for the alert and hard-stop behaviour.
    """
    private = d116._private_root(tmp_path)
    database = d116._catalog(private)
    volume = tmp_path
    temp = tmp_path / "external-tmp"
    temp.mkdir()
    monkeypatch.setattr(ewr, "macos_volume_identity", _provider({volume: _QUALIFIED}))
    monkeypatch.setattr(ewr, "verify_d130_archive", lambda _archive: ())
    # Accepted Decision 138 (D138-R3): the environment a guard validates must be the one SQLite
    # will actually read, so the process environment carries the same value the mapping does.
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(temp))
    # Pinned above both floors, because the machine a test runs on is not the qualified volume
    # and its actual free space is not what this test is about. (Left unpinned, this run is
    # refused by the 185 GiB launch guard -- which is the guard working, not a test failure.)
    _pin_free(monkeypatch, _LAUNCH_FLOOR + 1)

    result = canary.run_single_source_canary(
        operational_catalog=database,
        tree=DataTree.from_root(private),
        work_root=tmp_path / "work",
        run_id="d137-external",
        source_instance_id=d116._BULK_INSTANCE,
        require_volume_uuid=_QUALIFIED,
        environ={ewr.SQLITE_TMPDIR_ENV: str(temp)},
    )

    phases = [str(observation["phase"]) for observation in result.capacity_observations]
    assert phases == ["PRE_LAUNCH", "POST_F0", "PRE_F1", "POST_F1_PRE_F2", "POST_F2"]
    assert "DURING_F2" not in phases
    record = result.as_record()
    assert record["capacity_observations"]
    assert result.operational_catalog_unchanged
    # Every observation carries the qualified volume's identity and no absolute path.
    for observation in result.capacity_observations:
        volume_record = observation["volume"]
        assert isinstance(volume_record, dict)
        assert volume_record["volume_uuid"] == _QUALIFIED
    document = tmp_path / "work" / "d137-external" / canary.CANARY_RESULT_FILENAME
    assert str(tmp_path) not in document.read_text(encoding="utf-8")


# ==========================================================================
# K. The watchdog's continuous capacity subcommand — D137-R6
# ==========================================================================
#: The watchdog module the accepted D131 suite already loads, reused rather than loaded a second
#: time. Two live copies of a standalone script would each hold their own module state, and a
#: monkeypatch applied to one would silently not reach the other.
_watchdog = d131._watchdog


@pytest.mark.parametrize(
    ("free", "state", "exit_code"),
    [
        (ewr.F2_ALERT_FREE_BYTES + 1, ewr.F2_NORMAL_STATE, 0),
        (ewr.F2_ALERT_FREE_BYTES, ewr.F2_ALERT_STATE, _watchdog.ALERT_EXIT),
        (ewr.F2_HARD_FLOOR_FREE_BYTES + 1, ewr.F2_ALERT_STATE, _watchdog.ALERT_EXIT),
        (
            ewr.F2_HARD_FLOOR_FREE_BYTES,
            ewr.F2_HARD_STOP_STATE,
            _watchdog.CAPACITY_HARD_STOP_EXIT,
        ),
    ],
)
def test_the_watchdog_classifies_and_exits_at_each_threshold(
    free: int, state: str, exit_code: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One reading, one classification, one exit code -- and never a signal."""
    monkeypatch.setattr(_watchdog.shutil, "disk_usage", lambda _path: _fake_usage(free))
    verdict = _watchdog.capacity_verdict(str(tmp_path))
    assert verdict.state == state
    assert verdict.free_bytes == free
    assert _watchdog.main(["capacity", "--path", str(tmp_path)]) == exit_code


def test_the_watchdog_hard_stop_states_that_f2_rolls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D137-R6: the operator must be told the cost of stopping, not left to infer it."""
    monkeypatch.setattr(
        _watchdog.shutil, "disk_usage", lambda _path: _fake_usage(ewr.F2_HARD_FLOOR_FREE_BYTES)
    )
    message = _watchdog.capacity_verdict(str(tmp_path)).message
    assert "ROLLS THE IN-FLIGHT PROJECTION BACK" in message
    assert "discarded, not truncated" in message
    assert "Nothing was signalled, deleted, or cleaned" in message


def test_the_watchdog_capacity_check_deletes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No automatic cleanup at any threshold: the tree is byte-identical afterwards."""
    (tmp_path / "keep-me").write_bytes(b"evidence")
    monkeypatch.setattr(
        _watchdog.shutil, "disk_usage", lambda _path: _fake_usage(ewr.F2_HARD_FLOOR_FREE_BYTES)
    )
    _watchdog.main(["capacity", "--path", str(tmp_path)])
    assert (tmp_path / "keep-me").read_bytes() == b"evidence"


def test_an_unmeasurable_path_refuses_rather_than_passing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reading that could not be taken is its own outcome, never a satisfied threshold."""

    def explode(_path: Any) -> SimpleNamespace:
        raise OSError(5, "Input/output error")

    monkeypatch.setattr(_watchdog.shutil, "disk_usage", explode)
    assert _watchdog.main(["capacity", "--path", str(tmp_path)]) == _watchdog.REFUSED_EXIT


def test_the_watchdog_capacity_path_sends_no_signal() -> None:
    """The accepted D131 no-escalation invariant is unchanged by the capacity addition."""
    source = (_REPO_ROOT / "scripts/m3/canary_watchdog.py").read_text(encoding="utf-8")
    body = source.split("def capacity_verdict(")[1].split("\ndef ")[0]
    for forbidden in ("os.kill", "signal.", "unlink", "rmtree", "remove("):
        assert forbidden not in body


def test_the_watchdog_shares_the_packages_frozen_thresholds() -> None:
    """One definition, not two: a monitor that disagrees with its gate is worse than none."""
    assert _watchdog.F2_ALERT_FREE_BYTES is ewr.F2_ALERT_FREE_BYTES
    assert _watchdog.F2_HARD_FLOOR_FREE_BYTES is ewr.F2_HARD_FLOOR_FREE_BYTES
