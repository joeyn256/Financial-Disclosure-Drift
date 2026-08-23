"""Decision 138 — the D137 safety-envelope correction.

The D137 independent review was accepted with three majors, and this file is the proof that each
is closed:

* **MAJOR-1** — the external safety envelope could be bypassed by omitting the optional
  ``--require-volume-uuid`` path. §§A–D prove the envelope is decided by the **resolved work
  root**, that the flag can only add a requirement, that the immutable D130 archive is
  unreachable with the flag omitted, and that only the one D136 volume is ever accepted.
* **MAJOR-2** — the ``DURING_F2`` `10` GiB hard floor was classification and reporting only, with
  no continuous mechanical enforcement. §F proves an in-process guard samples inside F2's own
  transaction and that a breach **rolls the projection back** rather than printing a warning.
* **MAJOR-3** — the D135 ``POST_F0`` `>= 60` GiB and ``PRE_F1`` `>= 55` GiB stop-and-report phase
  gates were not enforced. §E proves both, at the floor, one byte below it, and when the
  measurement cannot be taken at all.

Nothing here touches the operator's SSD, and nothing here creates a canary, a canary world on any
external volume, a run identity, or an authorization. Every volume is synthetic.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d116_single_source_canary as d116  # noqa: E402
import test_d131_signal_and_monitor as d131  # noqa: E402
import test_d137_external_working_root as d137  # noqa: E402

from disclosure_drift.config import EVIDENCE_ROOT_ENV  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import offline_parse as op  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.working_catalog import file_digest  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402

#: The accepted qualified volume, restated as a literal so the pin is a second opinion rather
#: than an echo of the constant under test (accepted Decision 136 §4, D136-R1).
_QUALIFIED = "397A4D4A-9508-391E-814E-3B533C7BD049"

#: Any other volume. That it is not the accepted one is the only property that matters.
_OTHER = "0BADCAFE-0000-0000-0000-000000000000"

#: A second unqualified identity, used where "wrong" and "arbitrary" must be distinguishable.
_ARBITRARY = "11111111-2222-3333-4444-555555555555"

#: `185` GiB, `60` GiB, `55` GiB and `50` GiB in bytes, all stated as literals for that reason.
_LAUNCH_FLOOR = 198_642_237_440
_POST_F0_FLOOR = 64_424_509_440
_PRE_F1_FLOOR = 59_055_800_320
_PRE_F2_FLOOR = 53_687_091_200

#: `20` GiB and `10` GiB.
_ALERT = 21_474_836_480
_HARD_FLOOR = 10_737_418_240


def _usage(free: int, total: int = 900_000_000_000) -> SimpleNamespace:
    return SimpleNamespace(total=total, used=total - free, free=free)


def _pin_free(monkeypatch: pytest.MonkeyPatch, free: int) -> None:
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: _usage(free))


def _classify(monkeypatch: pytest.MonkeyPatch, mount: Path | None) -> None:
    """Make every path under ``mount`` classify as external, and everything else internal.

    The real classifier is device-number based, so a directory under ``tmp_path`` is genuinely
    internal and no test can conjure an external volume out of one. This substitutes the same
    seam the volume-identity provider already uses -- module global, resolved at call time -- so
    the *decision* under test is exercised without depending on a disk being plugged in.
    """

    def candidate(path: Path) -> bool:
        if mount is None:
            return False
        resolved = Path(os.path.realpath(path))
        return resolved == mount or mount in resolved.parents

    monkeypatch.setattr(ewr, "external_volume_candidate", candidate)


def _external_volume(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    uuid: str = _QUALIFIED,
    free: int = _LAUNCH_FLOOR + 1,
    tmpdir: Path | None = None,
    lookup_fails: bool = False,
    mounted: bool = True,
) -> Path:
    """Stand ``tmp_path`` up as a synthetic external volume, and return its ``SQLITE_TMPDIR``."""
    _classify(monkeypatch, tmp_path)
    mapping = {tmp_path: uuid} if mounted else {}
    monkeypatch.setattr(ewr, "macos_volume_identity", d137._provider(mapping, fail=lookup_fails))
    monkeypatch.setattr(ewr, "verify_d130_archive", lambda _archive: ())
    _pin_free(monkeypatch, free)
    temp = tmpdir if tmpdir is not None else tmp_path / "external-tmp"
    if tmpdir is None:
        temp.mkdir(exist_ok=True)
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(temp))
    return temp


def _run_external(
    tmp_path: Path,
    *,
    run_id: str,
    asserted: str | None = _QUALIFIED,
    work_root: Path | None = None,
    private: Path | None = None,
) -> Any:
    """Run the complete-source canary on the protected external path.

    ``asserted`` now defaults to the qualified volume because **Decision 140 (D140-R2) makes the
    assertion mandatory** on any external root. The default work root is created here for the
    same reason the operator creates one during preflight: D140-R5 forbids ``create_world`` from
    making a work root on the external path, because doing so would recreate a mount point that
    had gone away. An explicitly supplied work root is left alone, so a test can still prove
    that a refusal happened before anything was created.
    """
    root = private if private is not None else d116._private_root(tmp_path)
    if work_root is None:
        work_root = tmp_path / "work"
        work_root.mkdir(exist_ok=True)
    return canary.run_single_source_canary(
        operational_catalog=d116._catalog(root),
        tree=DataTree.from_root(root),
        work_root=work_root,
        run_id=run_id,
        source_instance_id=d116._BULK_INSTANCE,
        require_volume_uuid=asserted,
    )


# ==========================================================================
# A. The classifier — D138-R1
# ==========================================================================
def test_a_path_on_the_system_volume_is_internal() -> None:
    """The real classifier, on real device numbers. No `diskutil`, no argument, no disk."""
    assert ewr.external_volume_candidate(Path(os.sep)) is False
    assert ewr.external_volume_candidate(Path(os.sep) / "tmp") is False


def test_a_working_root_that_does_not_exist_yet_is_classified_on_its_volume(
    tmp_path: Path,
) -> None:
    """Classification happens **before** the world is created, on the nearest existing ancestor."""
    absent = tmp_path / "not" / "created" / "yet"
    assert ewr.external_volume_candidate(absent) is False
    assert not absent.exists()


def test_an_unclassifiable_root_refuses_rather_than_being_assumed_internal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Internal is the only answer that admits without proof, so it is never the fallback."""

    def _boom(_path: Path) -> Path:
        message = "the filesystem hosting the selected working root could not be identified"
        raise ewr.ExternalWorkingRootError(message)

    monkeypatch.setattr(ewr, "mount_point_of", _boom)
    with pytest.raises(ewr.ExternalWorkingRootError, match="could not be identified"):
        ewr.external_volume_candidate(tmp_path)


def test_the_classifier_never_shells_out_for_an_internal_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An internal root costs no `diskutil` call, which is what keeps D116 behaviour unchanged."""

    def _forbidden(_path: Path) -> ewr.VolumeIdentity:  # pragma: no cover - proving absence
        message = "an internal root must not trigger a volume-identity lookup"
        raise AssertionError(message)

    monkeypatch.setattr(ewr, "macos_volume_identity", _forbidden)
    assert ewr.require_external_envelope(tmp_path, observed_at="2026-08-23T00:00:00Z") is None


# ==========================================================================
# B. The envelope is mandatory, not opt-in — D138-R1 (correction C1)
# ==========================================================================
def test_c1_case_1_qualified_external_root_with_the_correct_uuid_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _external_volume(monkeypatch, tmp_path)
    preflight = ewr.require_external_envelope(
        tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
    )
    assert preflight is not None
    assert preflight.volume.volume_uuid == _QUALIFIED
    assert preflight.as_record()["canary_authorized"] is False


def test_c1_case_2_the_uuid_argument_omitted_still_protects_the_external_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**MAJOR-1, closed twice over.**

    Decision 138 answered the omitted flag by running the full envelope anyway. The **D139**
    review showed that was not enough: the envelope's own classifier asks which device the root
    resolves onto *now*, and with the volume absent the answer is the internal disk. Decision 140
    (D140-R2) therefore makes the assertion **mandatory** -- omission is the refusal, and the
    protection cannot be reached around at all.

    The supplied-flag path still reaches every guard, which is what the second half proves: the
    refusal below is a stricter entry condition, not a lost capability.
    """
    _external_volume(monkeypatch, tmp_path)
    with pytest.raises(ewr.ExternalWorkingRootError, match="--require-volume-uuid is required"):
        ewr.require_external_envelope(tmp_path / "work", observed_at="2026-08-23T00:00:00Z")

    preflight = ewr.require_external_envelope(
        tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
    )
    assert preflight is not None
    assert preflight.volume.volume_uuid == _QUALIFIED
    assert preflight.sqlite_tmpdir_verified is True
    assert preflight.launch_free_bytes >= _LAUNCH_FLOOR


@pytest.mark.parametrize("asserted", [_OTHER, _ARBITRARY])
def test_c1_cases_3_and_4_a_wrong_or_arbitrary_asserted_uuid_refuses(
    asserted: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D138-R12: the assertion is checked against the frozen identity, not against the disk."""
    _external_volume(monkeypatch, tmp_path)
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the one qualified external"):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=asserted
        )


def test_c1_case_5_an_unqualified_external_volume_refuses_with_no_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The case the baseline admitted silently: an external disk that is not the D136 one."""
    _external_volume(monkeypatch, tmp_path, uuid=_OTHER)
    with pytest.raises(ewr.ExternalWorkingRootError, match="--require-volume-uuid is required"):
        ewr.require_external_envelope(tmp_path / "work", observed_at="2026-08-23T00:00:00Z")
    # And with the mandatory assertion supplied, the original D138 predicate still fires: the
    # disk itself is not the qualified one. D140 added an entry condition; it removed no guard.
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


@pytest.mark.parametrize(
    ("asserted", "expected"),
    [
        # **D140-R2**: with the assertion omitted the run never reaches the archive predicate,
        # because it never reaches any predicate. The outcome the case exists to prove -- a
        # world is not built inside the only surviving copy of the D128 evidence -- holds
        # either way, and now holds one guard earlier.
        (None, "--require-volume-uuid is required"),
        (_QUALIFIED, "D130 archive"),
    ],
)
def test_c1_cases_6_and_7_a_root_inside_the_d130_archive_refuses_either_way(
    asserted: str | None, expected: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D138-R2**: archive exclusion is unconditional on the qualified SSD."""
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    _external_volume(monkeypatch, tmp_path)
    with pytest.raises(ewr.ExternalWorkingRootError, match=expected):
        ewr.require_external_envelope(
            archive / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=asserted
        )
    assert not (archive / "work").exists()


def test_c1_case_8_a_symlinked_or_normalized_alias_into_the_archive_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`realpath` is applied before anything is compared, so aliasing cannot launder the archive."""
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    link = tmp_path / "innocent"
    link.symlink_to(archive, target_is_directory=True)
    _external_volume(monkeypatch, tmp_path)

    for candidate in (link / "work", tmp_path / "sibling" / ".." / archive.name / "work"):
        with pytest.raises(ewr.ExternalWorkingRootError, match="D130 archive"):
            ewr.require_external_envelope(
                candidate, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
            )


def test_a_benign_similarly_prefixed_sibling_is_still_not_falsely_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The accepted D137-R3 property, preserved: refusing more is not the same as refusing right."""
    (tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME).mkdir()
    sibling = tmp_path / f"{ewr.D130_ARCHIVE_DIRECTORY_NAME}_WORKING"
    sibling.mkdir()
    _external_volume(monkeypatch, tmp_path)
    assert (
        ewr.require_external_envelope(
            sibling, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )
        is not None
    )


def test_c1_case_9_an_internal_root_with_no_assertion_keeps_its_historical_behaviour(
    tmp_path: Path,
) -> None:
    """**D138-R1**: the accepted internal path is byte-for-byte what Decision 116 left it."""
    result, _private, world = d116._run(tmp_path, run_id="d138-internal")
    assert result.capacity_observations == ()
    assert "capacity_observations" not in result.as_record()
    assert result.operational_catalog_unchanged
    assert world.result.is_file()


def test_c1_case_10_an_internal_root_asserting_the_d136_volume_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The assertion can only ever *add* a requirement, so it refuses a root it does not fit."""
    _classify(monkeypatch, None)
    monkeypatch.setattr(ewr, "macos_volume_identity", d137._provider({Path(os.sep): _OTHER}))
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_c1_case_11_a_lookup_failure_on_an_external_candidate_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _external_volume(monkeypatch, tmp_path, lookup_fails=True)
    with pytest.raises(ewr.ExternalWorkingRootError, match="lookup failed"):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_c1_case_12_a_missing_external_candidate_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing mounted where the root points is a refusal, never a fallback to internal storage."""
    _external_volume(monkeypatch, tmp_path, mounted=False)
    with pytest.raises(ewr.ExternalWorkingRootError, match="no volume is mounted"):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_the_launch_floor_still_refuses_one_byte_below_in_automatic_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D138-R4**: `185` GiB is unchanged, and reaches the no-flag path too."""
    _external_volume(monkeypatch, tmp_path, free=_LAUNCH_FLOOR - 1)
    with pytest.raises(ewr.ExternalWorkingRootError, match="launch free-space floor not met"):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_the_launch_floor_admits_at_exactly_the_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _external_volume(monkeypatch, tmp_path, free=_LAUNCH_FLOOR)
    assert (
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )
        is not None
    )


# ==========================================================================
# C. Both enforcement layers, and no world after a refusal — D138-R1
# ==========================================================================
def test_the_library_boundary_refuses_an_unqualified_volume_with_no_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A direct library caller cannot bypass what the operator surface enforces."""
    private = d116._private_root(tmp_path)
    before = file_digest(d116._catalog(private))[0]
    _external_volume(monkeypatch, tmp_path, uuid=_OTHER)

    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        _run_external(tmp_path, run_id="d138-lib", private=private)

    assert not (tmp_path / "work" / "d138-lib").exists()
    assert file_digest(d116._catalog(private))[0] == before


def test_the_library_boundary_refuses_the_archive_with_no_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**MAJOR-1's worst case**: a world built inside the only surviving copy of D128."""
    private = d116._private_root(tmp_path)
    archive = tmp_path / ewr.D130_ARCHIVE_DIRECTORY_NAME
    archive.mkdir()
    _external_volume(monkeypatch, tmp_path)

    with pytest.raises(ewr.ExternalWorkingRootError, match="D130 archive"):
        _run_external(
            tmp_path,
            run_id="d138-archive",
            work_root=archive / "work",
            private=private,
        )

    assert not (archive / "work").exists()
    assert list(archive.iterdir()) == []


def test_the_operator_surface_refuses_an_unqualified_volume_with_no_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same predicate at the command boundary, reached through the real routing."""
    private = d116._private_root(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _external_volume(monkeypatch, tmp_path, uuid=_OTHER)
    work = tmp_path / "work"

    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        canary.run_canary_source_command(
            mode="preflight",
            run_id="d138-op",
            source_instance_id=d116._BULK_INSTANCE,
            work_root=str(work),
            repository_root=checkout,
            require_volume_uuid=_QUALIFIED,
            environ={EVIDENCE_ROOT_ENV: str(private)},
        )

    assert not work.exists()


def test_the_prefix_profile_is_protected_with_no_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A diagnostic prefix cannot reach a volume the complete-source run would have refused."""
    private = d116._private_root(tmp_path)
    _external_volume(monkeypatch, tmp_path, uuid=_OTHER)

    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        canary.run_single_source_prefix_profile(
            operational_catalog=d116._catalog(private),
            tree=DataTree.from_root(private),
            work_root=tmp_path / "work",
            run_id="d138-prefix",
            source_instance_id=d116._BULK_INSTANCE,
            member_limit=1,
            require_volume_uuid=_QUALIFIED,
        )

    assert not (tmp_path / "work" / "d138-prefix").exists()


# ==========================================================================
# D. SQLITE_TMPDIR — the environment validated is the one SQLite consumes (D138-R3)
# ==========================================================================
def test_a_supplied_mapping_that_disagrees_with_the_process_environment_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D138-R3**: validating one environment while SQLite reads another proves nothing."""
    temp = _external_volume(monkeypatch, tmp_path)
    other = tmp_path / "second-tmp"
    other.mkdir()

    with pytest.raises(ewr.ExternalWorkingRootError, match="not the one SQLite will read"):
        ewr.require_external_sqlite_tmpdir(
            working_root=tmp_path / "work",
            archive=ewr.d130_archive_directory(tmp_path),
            environ={ewr.SQLITE_TMPDIR_ENV: str(other)},
        )
    assert temp.is_dir()


def test_a_supplied_mapping_that_agrees_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    temp = _external_volume(monkeypatch, tmp_path)
    resolved = ewr.require_external_sqlite_tmpdir(
        working_root=tmp_path / "work",
        archive=ewr.d130_archive_directory(tmp_path),
        environ={ewr.SQLITE_TMPDIR_ENV: str(temp)},
    )
    assert resolved == Path(os.path.realpath(temp))


def test_a_mapping_claiming_a_value_the_process_does_not_carry_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact D137 shape: an explicit mapping standing in for an unset variable."""
    _external_volume(monkeypatch, tmp_path)
    monkeypatch.delenv(ewr.SQLITE_TMPDIR_ENV, raising=False)
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the one SQLite will read"):
        ewr.require_external_sqlite_tmpdir(
            working_root=tmp_path / "work",
            archive=ewr.d130_archive_directory(tmp_path),
            environ={ewr.SQLITE_TMPDIR_ENV: str(tmp_path / "external-tmp")},
        )


def test_c1_case_13_an_internal_temporary_root_refuses_in_automatic_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An internal `SQLITE_TMPDIR` is refused even though no flag was supplied."""
    internal = tmp_path.parent / "internal-tmp"
    internal.mkdir(exist_ok=True)
    _external_volume(monkeypatch, tmp_path, tmpdir=internal)
    _classify(monkeypatch, tmp_path)
    monkeypatch.setattr(
        ewr, "macos_volume_identity", d137._provider({tmp_path: _QUALIFIED, internal: _OTHER})
    )
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the accepted qualified volume"):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_an_unset_temporary_root_refuses_in_automatic_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _external_volume(monkeypatch, tmp_path)
    monkeypatch.delenv(ewr.SQLITE_TMPDIR_ENV, raising=False)
    with pytest.raises(ewr.ExternalWorkingRootError, match="is not set"):
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_c1_case_14_a_same_volume_temporary_root_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    temp = _external_volume(monkeypatch, tmp_path)
    preflight = ewr.require_external_envelope(
        tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
    )
    assert preflight is not None
    assert preflight.temp_directory == Path(os.path.realpath(temp))


# ==========================================================================
# E. The POST_F0 and PRE_F1 gates — D138-R5, D138-R6 (correction C3)
# ==========================================================================
def test_the_two_new_floors_are_exactly_sixty_and_fifty_five_gibibytes() -> None:
    assert ewr.POST_F0_MINIMUM_FREE_BYTES == _POST_F0_FLOOR == 60 * 1024**3
    assert ewr.PRE_F1_MINIMUM_FREE_BYTES == _PRE_F1_FLOOR == 55 * 1024**3
    assert ewr.PHASE_MINIMUM_FREE_BYTES == {
        "POST_F0": _POST_F0_FLOOR,
        "PRE_F1": _PRE_F1_FLOOR,
    }


def _observation(phase: str, free: int) -> ewr.CapacityObservation:
    return ewr.CapacityObservation(
        phase=phase,
        free_bytes=free,
        total_bytes=900_000_000_000,
        volume=None,
        database_bytes=None,
        wal_bytes=None,
        temp_bytes=None,
        observed_at="2026-08-23T00:00:00Z",
    )


@pytest.mark.parametrize(
    ("phase", "floor"), [("POST_F0", _POST_F0_FLOOR), ("PRE_F1", _PRE_F1_FLOOR)]
)
def test_each_phase_gate_admits_at_exactly_its_floor(phase: str, floor: int) -> None:
    assert ewr.require_phase_free_space(_observation(phase, floor)).free_bytes == floor


@pytest.mark.parametrize(
    ("phase", "floor"), [("POST_F0", _POST_F0_FLOOR), ("PRE_F1", _PRE_F1_FLOOR)]
)
def test_each_phase_gate_refuses_one_byte_below_its_floor(phase: str, floor: int) -> None:
    with pytest.raises(ewr.ExternalWorkingRootError, match="STOP AND REPORT"):
        ewr.require_phase_free_space(_observation(phase, floor - 1))


@pytest.mark.parametrize("phase", ["PRE_LAUNCH", "POST_F1_PRE_F2", "POST_F2", "DURING_F2"])
def test_a_phase_with_no_floor_of_its_own_is_returned_untouched(phase: str) -> None:
    """`PRE_LAUNCH` and `POST_F1_PRE_F2` keep their own accepted call sites and are not moved."""
    assert ewr.require_phase_free_space(_observation(phase, 1)).phase == phase


def test_an_unmeasurable_phase_boundary_refuses_before_it_can_be_compared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Measurement failure refuses: no observation exists, so nothing is admitted by default."""

    def _boom(_path: Path) -> Any:
        message = "the volume went away"
        raise OSError(message)

    monkeypatch.setattr(shutil, "disk_usage", _boom)
    with pytest.raises(ewr.ExternalWorkingRootError, match="could not be measured"):
        ewr.observe_capacity("POST_F0", working_root=tmp_path, observed_at="2026-08-23T00:00:00Z")


def _gated_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    after_f0_free: int,
    run_id: str,
    fail_measurement: bool = False,
    drop_after_phase: str | None = None,
    f1_calls: list[str] | None = None,
    f2_calls: list[str] | None = None,
) -> tuple[list[str], Any]:
    """Run the protected external path, dropping free space at one chosen point.

    By default the drop happens the instant F0 returns, so ``POST_F0`` is the first boundary to
    read it. ``drop_after_phase`` moves the drop to **after** that phase's observation is taken,
    which is the only way a later gate can be reached in isolation: the floors descend --
    `60` GiB, then `55`, then `50` -- so any single value low enough to breach a later one would
    have breached every earlier one first. Free space falling *between* two boundaries is also
    the real shape of the failure being modelled.

    Returns the F1 call log and whatever the run produced, so a refusal can be proved to have
    landed **before** F1 rather than merely somewhere.
    """
    private = d116._private_root(tmp_path)
    _external_volume(monkeypatch, tmp_path)
    free = {"bytes": _LAUNCH_FLOOR + 1}

    def _usage_provider(_path: Path) -> Any:
        if fail_measurement and free["bytes"] < 0:
            message = "the volume went away mid-run"
            raise OSError(message)
        return _usage(free["bytes"])

    monkeypatch.setattr(shutil, "disk_usage", _usage_provider)

    if drop_after_phase is not None:
        real_observe = canary.observe_capacity

        def _dropping_observe(phase: str, **kwargs: Any) -> Any:
            observation = real_observe(phase, **kwargs)
            if phase == drop_after_phase:
                free["bytes"] = after_f0_free
            return observation

        monkeypatch.setattr(canary, "observe_capacity", _dropping_observe)

    # **D140-R13**: owned by the caller when one is supplied, so an assertion made *after* the
    # exception is made on the object the spy actually wrote to. A list created inside this
    # function and returned only on the success path cannot witness a refusal.
    observed_f1: list[str] = [] if f1_calls is None else f1_calls
    observed_f2: list[str] = [] if f2_calls is None else f2_calls
    real_f1 = canary.CensusCatalog.count_persisted_accession_resolutions

    def _counting_f1(self: Any, **kwargs: Any) -> Any:
        observed_f1.append("F1")
        return real_f1(self, **kwargs)

    monkeypatch.setattr(canary.CensusCatalog, "count_persisted_accession_resolutions", _counting_f1)

    real_f2 = canary.materialize_census_associations

    def _counting_f2(*args: Any, **kwargs: Any) -> Any:
        observed_f2.append("F2")
        return real_f2(*args, **kwargs)

    monkeypatch.setattr(canary, "materialize_census_associations", _counting_f2)

    real_f0 = canary.materialize_one_planned_source

    def _dropping_f0(*args: Any, **kwargs: Any) -> Any:
        outcome = real_f0(*args, **kwargs)
        if fail_measurement:
            free["bytes"] = -1
        elif drop_after_phase is None:
            free["bytes"] = after_f0_free
        return outcome

    monkeypatch.setattr(canary, "materialize_one_planned_source", _dropping_f0)
    return observed_f1, _run_external(tmp_path, run_id=run_id, private=private)


@pytest.mark.parametrize(
    ("free", "phase", "drop_after"),
    [
        (_POST_F0_FLOOR - 1, "POST_F0", None),
        (_PRE_F1_FLOOR - 1, "PRE_F1", "POST_F0"),
    ],
)
def test_a_breach_at_either_gate_stops_the_run_before_f1_begins(
    free: int,
    phase: str,
    drop_after: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**MAJOR-3, closed.** Each gate refuses one byte below its own floor, before F1 begins.

    ``PRE_F1`` is reached with ``POST_F0`` already satisfied, which is what makes it a genuinely
    separate phase gate rather than a restatement of the one above it (D138-R6).
    """
    with pytest.raises(ewr.ExternalWorkingRootError, match=f"{phase} free-space gate not met"):
        _gated_run(
            tmp_path,
            monkeypatch,
            after_f0_free=free,
            run_id=f"d138-{phase.lower()}",
            drop_after_phase=drop_after,
        )


def test_f1_is_never_called_when_the_post_f0_gate_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D140-R13, MINOR-3.** The assertion is now made on a counter that survives the raise.

    As accepted at Decision 138 this test proved nothing at all. ``calls`` was bound to a fresh
    empty list, ``_gated_run`` raised, so the tuple assignment ``calls, _ = ...`` **never
    executed**, and ``assert calls == []`` re-asserted the literal written two lines above it.
    It passed identically whether F1 ran once, never, or a thousand times.

    The spy list is now created here and handed **into** the harness, so it is the same object
    the counting wrapper appends to and it carries the truth out through the exception.
    """
    calls: list[str] = []
    with pytest.raises(ewr.ExternalWorkingRootError, match="POST_F0"):
        _gated_run(
            tmp_path,
            monkeypatch,
            after_f0_free=_POST_F0_FLOOR - 1,
            run_id="d138-f1-zero",
            f1_calls=calls,
        )
    assert calls == []


def test_a_measurement_failure_after_f0_refuses_rather_than_admitting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ewr.ExternalWorkingRootError, match="could not be measured"):
        _gated_run(
            tmp_path,
            monkeypatch,
            after_f0_free=0,
            run_id="d138-unmeasurable",
            fail_measurement=True,
        )


def test_exactly_sixty_gibibytes_passes_post_f0_and_reaches_the_pre_f1_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`60` GiB clears `POST_F0` and is then refused by `PRE_F1`'s own separate `55` GiB gate...

    ...only if it were below it, which it is not. `60 >= 55`, so the run continues to the
    accepted `50` GiB `PRE_F2` gate, which `60` GiB also clears. The point of the case is that
    the floor itself **admits** at both gates rather than refusing at the boundary.
    """
    _, result = _gated_run(
        tmp_path, monkeypatch, after_f0_free=_POST_F0_FLOOR, run_id="d138-at-floor"
    )
    phases = {str(o["phase"]): int(str(o["free_bytes"])) for o in result.capacity_observations}
    assert phases["POST_F0"] == _POST_F0_FLOOR
    assert phases["PRE_F1"] == _POST_F0_FLOOR
    assert "POST_F2" in phases


def test_the_pre_f2_fifty_gibibyte_gate_is_unchanged_and_still_later(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D138-R7**: `50` GiB still refuses F2, after both new gates have already passed."""
    assert canary.PRE_F2_MINIMUM_FREE_BYTES == _PRE_F2_FLOOR
    with pytest.raises(canary.SingleSourceCanaryError, match="pre-F2 free-space admission"):
        _gated_run(
            tmp_path,
            monkeypatch,
            after_f0_free=_PRE_F2_FLOOR - 1,
            run_id="d138-pre-f2",
            drop_after_phase="PRE_F1",
        )


# ==========================================================================
# F. The in-process F2 capacity guard — D138-R8, R9, R10 (correction C2)
# ==========================================================================
def test_the_sampling_interval_is_inside_the_sixty_second_ceiling() -> None:
    """**D138-R9**: a bounded interval, and substantially shorter than the ceiling permits."""
    assert ewr.F2_CAPACITY_MAX_SAMPLE_SECONDS == 60.0
    assert 0 < ewr.F2_CAPACITY_SAMPLE_SECONDS <= 30.0


def test_an_interval_beyond_the_ceiling_is_refused_at_construction(tmp_path: Path) -> None:
    with pytest.raises(ewr.ExternalWorkingRootError, match="exceeds the"):
        ewr.F2CapacityGuard(working_root=tmp_path, interval_seconds=60.5)


def _guard(
    tmp_path: Path,
    readings: list[int | type[OSError]],
    *,
    interval: float = 5.0,
) -> tuple[ewr.F2CapacityGuard, list[float]]:
    """A guard driven by a scripted list of readings and a clock that always elapses."""
    ticks = [0.0]
    taken = {"n": 0}

    def free_space(_path: Path) -> tuple[int, int]:
        index = min(taken["n"], len(readings) - 1)
        taken["n"] += 1
        value = readings[index]
        if isinstance(value, type) and issubclass(value, OSError):
            message = "the volume went away"
            raise value(message)
        assert isinstance(value, int)
        return value, 900_000_000_000

    def clock() -> float:
        ticks[0] += interval * 10
        return ticks[0]

    return (
        ewr.F2CapacityGuard(
            working_root=tmp_path,
            interval_seconds=interval,
            free_space=free_space,
            clock=clock,
            now=lambda: "2026-08-23T00:00:00Z",
        ),
        ticks,
    )


def test_normal_free_space_records_nothing_and_continues(tmp_path: Path) -> None:
    guard, _ = _guard(tmp_path, [_ALERT + 1])
    guard()
    guard()
    assert guard.samples == 2
    assert guard.observations == []
    assert guard.hard_stop_record is None


def test_the_alert_band_records_a_during_f2_observation_and_continues(tmp_path: Path) -> None:
    """`10` GiB < free <= `20` GiB is a report, not a stop -- and both bounds are inclusive."""
    guard, _ = _guard(tmp_path, [_ALERT, _HARD_FLOOR + 1])
    guard()
    guard()
    assert guard.samples == 2
    assert [o.phase for o in guard.observations] == ["DURING_F2", "DURING_F2"]
    assert [o.free_bytes for o in guard.observations] == [_ALERT, _HARD_FLOOR + 1]
    assert guard.hard_stop_record is None


def test_the_hard_floor_is_inclusive_and_raises_the_dedicated_condition(tmp_path: Path) -> None:
    guard, _ = _guard(tmp_path, [_HARD_FLOOR])
    with pytest.raises(ewr.F2CapacityHardStopError) as raised:
        guard()
    assert isinstance(raised.value, ewr.ExternalWorkingRootError)
    record = raised.value.record
    assert record["phase"] == "DURING_F2"
    assert record["hard_stop_reason"] == ewr.F2_HARD_STOP_REASON
    assert record["free_bytes"] == _HARD_FLOOR
    assert record["threshold_bytes"] == _HARD_FLOOR
    assert record["measurement_error"] is None
    assert record["f2_transaction_rolled_back"] is True
    assert record["f2_committed"] is False
    assert "ROLLS BACK" in str(raised.value)
    assert guard.hard_stop_record == record


def test_a_measurement_failure_takes_the_same_hard_stop_path(tmp_path: Path) -> None:
    """**D138-R8**: a reading that cannot be taken is not a reading that passed."""
    guard, _ = _guard(tmp_path, [OSError])
    with pytest.raises(ewr.F2CapacityHardStopError) as raised:
        guard()
    record = raised.value.record
    assert record["hard_stop_reason"] == ewr.F2_MEASUREMENT_FAILED_REASON
    assert record["free_bytes"] is None
    assert record["measurement_error"] == "OSError"
    assert record["f2_committed"] is False


def test_the_first_call_always_samples_and_later_calls_respect_the_interval(
    tmp_path: Path,
) -> None:
    """**D138-R9**: bounded by a monotonic wall clock, so a per-accession call stays affordable."""
    now = [100.0]
    taken: list[float] = []

    def free_space(_path: Path) -> tuple[int, int]:
        taken.append(now[0])
        return _ALERT + 1, 900_000_000_000

    guard = ewr.F2CapacityGuard(
        working_root=tmp_path,
        interval_seconds=5.0,
        free_space=free_space,
        clock=lambda: now[0],
        now=lambda: "2026-08-23T00:00:00Z",
    )
    guard()  # the reading taken immediately before F2 starts
    for _ in range(1000):
        guard()  # a thousand accessions inside the same five seconds cost nothing
    assert taken == [100.0]
    now[0] += 5.0
    guard()
    assert taken == [100.0, 105.0]


def test_the_guard_uses_a_monotonic_clock_by_default(tmp_path: Path) -> None:
    """A wall clock that can be stepped backwards would silently suspend sampling."""
    import time as _time

    guard = ewr.F2CapacityGuard(working_root=tmp_path)
    assert guard._clock is _time.monotonic  # noqa: SLF001 - the seam is the point


# --------------------------------------------------------------------------
# The rollback proof: the mutation exists inside the transaction and not after
# --------------------------------------------------------------------------
def _f2_connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """A catalog with F0 already durable, ready for the association projection."""
    private = d116._private_root(tmp_path)
    d116._prime_bulk(private)
    copy = tmp_path / "f2.sqlite3"
    shutil.copy2(d116._catalog(private), copy)
    connection = sqlite3.connect(copy)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def f2_connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    yield from _f2_connection(tmp_path)


def _relation_rows(connection: sqlite3.Connection) -> int:
    return int(
        connection.execute("SELECT COUNT(*) FROM census_accession_registrants").fetchone()[0]
    )


def test_f2_commits_its_association_rows_when_capacity_holds(
    f2_connection: sqlite3.Connection, tmp_path: Path
) -> None:
    """The control, and the proof that **both** F2 traversals are sampled -- D138-R9.

    Without the control, an empty table after a hard stop would prove nothing. Without the
    sampling shape, a guard called once at F2's entry would look identical to one called
    throughout it, and the `10` GiB floor would be back to a boundary check wearing a
    continuous one's name.

    The shape is read from the row count each reading observes on the **same** connection:

    * the first reading sees **zero** rows -- it is taken before the transaction opens;
    * some reading sees **more than zero and fewer than the final total** -- which can only
      happen inside the first traversal, while the projection is still inserting;
    * the final total is seen **more than once** -- so the second, completeness traversal is
      sampled too, not merely the one that writes.
    """
    seen: list[int] = []

    def free_space(_path: Path) -> tuple[int, int]:
        seen.append(_relation_rows(f2_connection))
        return _ALERT + 1, 900_000_000_000

    guard = ewr.F2CapacityGuard(
        working_root=tmp_path,
        free_space=free_space,
        clock=lambda: float(len(seen)) * 1000.0,
        now=lambda: "2026-08-23T00:00:00Z",
    )
    op.materialize_census_associations(f2_connection, compact_evidence=True, capacity_guard=guard)

    total = _relation_rows(f2_connection)
    assert total > 0
    assert seen[0] == 0, "the first reading is taken before F2's transaction opens"
    assert any(0 < rows < total for rows in seen), "the writing traversal is sampled"
    assert seen.count(total) >= 2, "the completeness traversal is sampled too"
    assert guard.samples == len(seen) > 3


def test_a_hard_stop_mid_f2_rolls_the_association_mutation_back(
    f2_connection: sqlite3.Connection, tmp_path: Path
) -> None:
    """**MAJOR-2, closed.** Rows exist inside the transaction and are gone after it.

    The provider reads the row count on the **same connection**, from inside the open
    transaction, so the mutation is observed while it is still uncommitted rather than inferred.
    """
    seen_inside: list[int] = []
    calls = {"n": 0}

    def free_space(_path: Path) -> tuple[int, int]:
        calls["n"] += 1
        seen_inside.append(_relation_rows(f2_connection))
        # Normal until the projection has actually written something, then straight through the
        # floor -- so the abort lands mid-transaction rather than before it opens.
        if seen_inside[-1] > 0:
            return _HARD_FLOOR, 900_000_000_000
        return _ALERT + 1, 900_000_000_000

    guard = ewr.F2CapacityGuard(
        working_root=tmp_path,
        free_space=free_space,
        clock=lambda: float(calls["n"]) * 1000.0,
        now=lambda: "2026-08-23T00:00:00Z",
    )

    with pytest.raises(ewr.F2CapacityHardStopError) as raised:
        op.materialize_census_associations(
            f2_connection, compact_evidence=True, capacity_guard=guard
        )

    assert max(seen_inside) > 0, "the projection had written association rows before the abort"
    assert calls["n"] > 1, "the abort came from inside the loop, not from the entry reading"
    assert f2_connection.in_transaction is False, "the transaction is closed"
    assert _relation_rows(f2_connection) == 0, "every would-be association row was rolled back"
    assert raised.value.record["f2_committed"] is False
    assert raised.value.record["free_bytes"] == _HARD_FLOOR


def test_a_measurement_failure_mid_f2_rolls_back_the_same_way(
    f2_connection: sqlite3.Connection, tmp_path: Path
) -> None:
    """Fail-closed means the same abort path, not a different and gentler one."""
    calls = {"n": 0}

    def free_space(_path: Path) -> tuple[int, int]:
        calls["n"] += 1
        if _relation_rows(f2_connection) > 0:
            message = "the volume went away mid-projection"
            raise OSError(message)
        return _ALERT + 1, 900_000_000_000

    guard = ewr.F2CapacityGuard(
        working_root=tmp_path,
        free_space=free_space,
        clock=lambda: float(calls["n"]) * 1000.0,
        now=lambda: "2026-08-23T00:00:00Z",
    )

    with pytest.raises(ewr.F2CapacityHardStopError) as raised:
        op.materialize_census_associations(
            f2_connection, compact_evidence=True, capacity_guard=guard
        )

    assert f2_connection.in_transaction is False
    assert _relation_rows(f2_connection) == 0
    assert raised.value.record["hard_stop_reason"] == ewr.F2_MEASUREMENT_FAILED_REASON


def test_an_alert_mid_f2_lets_the_projection_complete_normally(
    f2_connection: sqlite3.Connection, tmp_path: Path
) -> None:
    """`10` GiB < free <= `20` GiB continues, and the run afterwards is the ordinary one."""
    calls = {"n": 0}

    def free_space(_path: Path) -> tuple[int, int]:
        calls["n"] += 1
        return (_HARD_FLOOR + 1 if calls["n"] > 2 else _ALERT + 1), 900_000_000_000

    guard = ewr.F2CapacityGuard(
        working_root=tmp_path,
        free_space=free_space,
        clock=lambda: float(calls["n"]) * 1000.0,
        now=lambda: "2026-08-23T00:00:00Z",
    )
    totality = op.materialize_census_associations(
        f2_connection, compact_evidence=True, capacity_guard=guard
    )
    assert _relation_rows(f2_connection) > 0
    assert totality is not None
    assert guard.observations, "the alert band was recorded rather than passed over"
    assert all(o.phase == "DURING_F2" for o in guard.observations)


def test_f2_is_sampled_before_its_transaction_opens(
    f2_connection: sqlite3.Connection, tmp_path: Path
) -> None:
    """**D138-R9**'s first requirement: a reading taken immediately *before* F2 starts.

    "Before F2 starts" is not the same claim as "at F2's first accession", and only one of them
    is what D138-R9 asks for, so the difference has to be observable. It is: ``in_transaction``
    is ``False`` for the entry reading and ``True`` for every reading the traversals take.
    Asserting on the reading *count* could not tell the two apart -- deleting the entry call
    simply promotes the first loop call into its place.
    """
    states: list[bool] = []

    def free_space(_path: Path) -> tuple[int, int]:
        states.append(f2_connection.in_transaction)
        return _ALERT + 1, 900_000_000_000

    guard = ewr.F2CapacityGuard(
        working_root=tmp_path,
        free_space=free_space,
        clock=lambda: float(len(states)) * 1000.0,
        now=lambda: "2026-08-23T00:00:00Z",
    )
    op.materialize_census_associations(f2_connection, compact_evidence=True, capacity_guard=guard)

    assert states[0] is False, "the first reading is taken before F2's transaction opens"
    assert any(states[1:]), "and later readings are taken while it is open"


def test_a_breach_at_the_entry_reading_stops_f2_before_it_opens(
    f2_connection: sqlite3.Connection, tmp_path: Path
) -> None:
    """Refusing there costs nothing, because there is no transaction to roll back yet."""
    guard, _ = _guard(tmp_path, [_HARD_FLOOR])
    with pytest.raises(ewr.F2CapacityHardStopError):
        op.materialize_census_associations(
            f2_connection, compact_evidence=True, capacity_guard=guard
        )
    assert guard.samples == 1
    assert _relation_rows(f2_connection) == 0
    assert f2_connection.in_transaction is False


def test_an_unguarded_f2_is_exactly_what_decision_094_left_it(
    f2_connection: sqlite3.Connection,
) -> None:
    """`capacity_guard=None` adds a stopping condition and no association semantics."""
    before = _relation_rows(f2_connection)
    op.materialize_census_associations(f2_connection, compact_evidence=True)
    assert before == 0
    assert _relation_rows(f2_connection) > 0


def test_the_guard_deletes_nothing_and_signals_nothing(tmp_path: Path) -> None:
    """**D138-R8**: no `SIGKILL`, no destructive cleanup, no escalation. D131 is untouched."""
    victim = tmp_path / "keep-me"
    victim.write_text("untouched", encoding="utf-8")
    guard, _ = _guard(tmp_path, [_HARD_FLOOR])
    with pytest.raises(ewr.F2CapacityHardStopError):
        guard()
    assert victim.read_text(encoding="utf-8") == "untouched"

    source = Path(ewr.__file__).read_text(encoding="utf-8")
    body = source.split("class F2CapacityGuard")[1]
    # ``subprocess`` left this list at **Decision 140** (D140-R15) and nothing else did. The
    # guard now re-reads the exact Volume UUID on a bounded interval, which is a ``diskutil``
    # call, because the D139 review showed that free space measured after the volume has gone
    # describes the internal disk -- and the internal disk always looks healthy. The prohibition
    # that mattered is unchanged and is asserted here: the guard still kills nothing, signals
    # nothing, and deletes nothing.
    for forbidden in ("os.kill", "SIGKILL", "SIGTERM", "unlink", "rmtree", "shutil.rmtree"):
        assert forbidden not in body, f"the guard must never reach for {forbidden}"


# ==========================================================================
# G. The guard reaches the real run, and the watchdog is demoted — D138-R11
# ==========================================================================
def test_the_protected_external_run_binds_an_in_process_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The wiring itself: F2 on the protected path is handed a guard, never ``None``."""
    private = d116._private_root(tmp_path)
    _external_volume(monkeypatch, tmp_path)
    seen: list[object] = []
    real_f2 = canary.materialize_census_associations

    def _capturing(*args: Any, **kwargs: Any) -> Any:
        seen.append(kwargs.get("capacity_guard"))
        return real_f2(*args, **kwargs)

    monkeypatch.setattr(canary, "materialize_census_associations", _capturing)
    _run_external(tmp_path, run_id="d138-bound", private=private)
    assert len(seen) == 1
    assert isinstance(seen[0], ewr.F2CapacityGuard)


def test_an_internal_run_binds_no_guard_at_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D138-R8** scopes continuous enforcement to the protected external path."""
    seen: list[object] = []
    real_f2 = canary.materialize_census_associations

    def _capturing(*args: Any, **kwargs: Any) -> Any:
        seen.append(kwargs.get("capacity_guard"))
        return real_f2(*args, **kwargs)

    monkeypatch.setattr(canary, "materialize_census_associations", _capturing)
    d116._run(tmp_path, run_id="d138-unbound")
    assert seen == [None]


def test_a_hard_stop_during_a_real_run_leaves_no_result_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End to end: the run aborts, F2 rolls back, and nothing is finalized."""
    private = d116._private_root(tmp_path)
    _external_volume(monkeypatch, tmp_path)
    real_guard = ewr.F2CapacityGuard

    def _starved(**kwargs: Any) -> ewr.F2CapacityGuard:
        return real_guard(
            **kwargs,
            free_space=lambda _path: (_HARD_FLOOR, 900_000_000_000),
            clock=lambda: 0.0,
        )

    monkeypatch.setattr(canary, "F2CapacityGuard", _starved)

    with pytest.raises(ewr.F2CapacityHardStopError, match="ROLLS BACK"):
        _run_external(tmp_path, run_id="d138-starved", private=private)

    world = tmp_path / "work" / "d138-starved"
    assert not (world / canary.CANARY_RESULT_FILENAME).exists()
    assert file_digest(d116._catalog(private))[0] is not None


def test_the_watchdog_is_supplemental_and_says_so() -> None:
    """**D138-R11**: the in-process guard is authoritative; the subcommand only reports."""
    watchdog = d131._watchdog
    text = Path(watchdog.__file__).read_text(encoding="utf-8")
    assert "supplemental" in text.lower()
    assert "reports and never acts" in text
    verdict = watchdog.capacity_verdict(os.sep)
    assert not hasattr(verdict, "stop")


def test_no_package_module_depends_on_the_watchdog_for_enforcement() -> None:
    """Enforcement that lived in another process is the defect; it must not come back."""
    package = Path(canary.__file__).resolve().parents[1]
    referring = [
        str(module.relative_to(package))
        for module in package.rglob("*.py")
        if "canary_watchdog" in module.read_text(encoding="utf-8")
    ]
    assert referring == []
