"""Accepted Decision 127 — the pre-F2 free-space admission guard.

Accepted **Decision 124 §9** (D124-R5) requires `>= 30 GiB` free **measured immediately before
opening F2**, explicitly not inherited from the run's starting gate. The complete-source path did
not contain that check: F1's
:meth:`~disclosure_drift.sec.census.CensusCatalog.count_persisted_accession_resolutions` returned
and F2's :func:`~disclosure_drift.m3.offline_parse.materialize_census_associations` was the very
next statement. Accepted **Decision 126 §7** (D126-R6) recorded that as the one blocker standing
between a passing live preflight and a complete-source run, ruled that no external sampler can
close it, and authorized exactly this guard.

Three claims carry it, and each is proved against a run built to break it:

**Below the floor refuses, and F2 never runs.** The refusal is proved by a *tripwire*: F2 is
replaced by a function that records the call and fails outright, so "F2 did not run" is
established by F2's own absence from the record rather than by inspecting the guard.

**At and above the floor admits.** The boundary is proved at exactly
``PRE_F2_MINIMUM_FREE_BYTES`` rather than near it, because an off-by-one at the floor is the one
error a "roughly 30 GiB" test cannot see.

**The guard runs after F1 and before F2.** Ordering is proved from a call log written by the
three real participants during one real end-to-end run, not from source inspection.

Everything runs over the Decision 116 synthetic world beneath ``tmp_path``. No test resolves,
opens, names, or infers the accepted private evidence root, none reads a real SEC artifact, none
touches a real catalog, and none runs a real source.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d116_single_source_canary as d116  # noqa: E402

from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.working_catalog import file_digest  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402

#: 30 GiB, stated independently of the constant under test so the pin is a second opinion rather
#: than a restatement of the same expression.
_THIRTY_GIB = 32_212_254_720


def _usage(free: int) -> SimpleNamespace:
    """A ``shutil.disk_usage`` stand-in. Only ``.free`` is read anywhere in the canary path."""
    return SimpleNamespace(total=free * 2, used=free, free=free)


def _fix_free(monkeypatch: pytest.MonkeyPatch, free: int) -> None:
    """Pin measured free space for the whole run, so the proof does not depend on the machine.

    Line 890 of the canary module is the **only** free-space comparison it contains; every other
    ``disk_usage`` call records a number into a result document. Pinning the measurement therefore
    controls the guard and nothing else.
    """
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: _usage(free))


# ==========================================================================
# The frozen constant
# ==========================================================================
def test_the_floor_is_exactly_thirty_gibibytes() -> None:
    """One frozen constant, pinned to its byte value rather than to its expression."""
    assert canary.PRE_F2_MINIMUM_FREE_BYTES == _THIRTY_GIB
    assert canary.PRE_F2_MINIMUM_FREE_BYTES == 30 * 1024**3
    assert "PRE_F2_MINIMUM_FREE_BYTES" in canary.__all__


# ==========================================================================
# A. Below the floor refuses, and F2 is never called
# ==========================================================================
def test_one_byte_below_the_floor_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    """The boundary is proved at the floor, and the refusal states every fact D127 requires."""
    _fix_free(monkeypatch, _THIRTY_GIB - 1)
    with pytest.raises(canary.SingleSourceCanaryError) as raised:
        canary._require_pre_f2_free_space(Path("/nonexistent-is-never-reached"))
    message = str(raised.value)
    assert str(_THIRTY_GIB - 1) in message
    assert str(_THIRTY_GIB) in message
    assert "refused before its single transaction opened" in message


def test_below_the_floor_the_f2_tripwire_is_never_reached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real run refuses at the boundary, and F2's own tripwire records that it never ran."""
    reached: list[str] = []

    def tripwire(*_args: Any, **_kwargs: Any) -> Any:
        reached.append("F2")
        message = "F2 must not be reachable below the admission floor"
        raise AssertionError(message)

    monkeypatch.setattr(canary, "materialize_census_associations", tripwire)
    _fix_free(monkeypatch, _THIRTY_GIB - 1)

    private = d116._private_root(tmp_path)
    database = d116._catalog(private)
    before = file_digest(database)[0]

    with pytest.raises(canary.SingleSourceCanaryError, match="pre-F2 free-space admission failed"):
        canary.run_single_source_canary(
            operational_catalog=database,
            tree=DataTree.from_root(private),
            work_root=tmp_path / "work",
            run_id="d127-refused",
            source_instance_id=d116._BULK_INSTANCE,
        )

    assert reached == []
    # Decision 116 §10 holds through the new refusal: a failed gate is not a partial write.
    assert file_digest(database)[0] == before


# ==========================================================================
# B. At and above the floor admits
# ==========================================================================
@pytest.mark.parametrize(
    ("free", "label"),
    [(_THIRTY_GIB, "exactly at the floor"), (_THIRTY_GIB + 1, "one byte above it")],
)
def test_at_or_above_the_floor_admits(
    free: int, label: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``>=`` is the rule, so the floor itself admits -- ``label`` names which case failed."""
    _fix_free(monkeypatch, free)
    assert canary._require_pre_f2_free_space(Path("/nonexistent-is-never-reached")) == free


# ==========================================================================
# C. The guard runs after F1 and before F2
# ==========================================================================
def test_the_guard_runs_after_f1_and_before_f2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ordering proved from one real run's call log, with all three participants real."""
    order: list[str] = []

    real_f1 = canary.CensusCatalog.count_persisted_accession_resolutions
    real_guard = canary._require_pre_f2_free_space
    real_f2 = canary.materialize_census_associations

    def logged_f1(self: Any, *args: Any, **kwargs: Any) -> Any:
        order.append("F1")
        return real_f1(self, *args, **kwargs)

    def logged_guard(directory: Path) -> int:
        order.append("GUARD")
        return real_guard(directory)

    def logged_f2(*args: Any, **kwargs: Any) -> Any:
        order.append("F2")
        return real_f2(*args, **kwargs)

    monkeypatch.setattr(canary.CensusCatalog, "count_persisted_accession_resolutions", logged_f1)
    monkeypatch.setattr(canary, "_require_pre_f2_free_space", logged_guard)
    monkeypatch.setattr(canary, "materialize_census_associations", logged_f2)
    _fix_free(monkeypatch, _THIRTY_GIB + 1)

    result, _private, _world = d116._run(tmp_path, run_id="d127-ordering")

    assert order == ["F1", "GUARD", "F2"]
    # The run completed normally above the floor: admission changes nothing about the outcome.
    assert result.association_totality
    assert result.operational_catalog_unchanged
