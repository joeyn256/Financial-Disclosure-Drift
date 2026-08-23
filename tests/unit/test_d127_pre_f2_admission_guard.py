"""Accepted Decision 127 — the pre-F2 free-space admission guard, at the Decision 137 floor.

**The floor moved; nothing else did.** Decision 127 introduced this guard at `30` GiB, the figure
accepted Decision 124 §9 (D124-R5) carried then. Accepted **Decision 135** §8 (D135-R3)
reconciled the corrected complete-source run's capacity and found `30` GiB **inadequate** for it;
accepted **Decision 136** §11 (D136-R11 item 6) made replacing that behaviour Decision 137's work.
Decision 137 (**D137-R5**) raised the constant to `50` GiB, ``53,687,091,200`` bytes, and moved
neither the strict ``<`` comparison, nor the call site between F1 and F2, nor the refusal's shape.

So this file is **not** rewritten for a new guard: every claim below is Decision 127's own claim,
re-proved at the floor that now controls. The superseded `30` GiB amount is kept as a named
constant and given its own test, because "the old value no longer admits" is a claim about a
specific number and cannot be shown by testing a different one.

Accepted **Decision 124 §9** (D124-R5) requires the measurement **immediately before opening
F2**, explicitly not inherited from the run's starting gate. The complete-source path did
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
error a "roughly 50 GiB" test cannot see.

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

#: 50 GiB, stated independently of the constant under test so the pin is a second opinion rather
#: than a restatement of the same expression. This is the accepted D137-R5 floor.
_FIFTY_GIB = 53_687_091_200

#: 30 GiB — the **superseded** D127 floor. Retained rather than deleted so the claim "the old
#: amount no longer admits" can be proved against the exact number that used to.
_THIRTY_GIB = 32_212_254_720


def _usage(free: int) -> SimpleNamespace:
    """A ``shutil.disk_usage`` stand-in. Only ``.free`` is read anywhere in the canary path."""
    return SimpleNamespace(total=free * 2, used=free, free=free)


def _fix_free(monkeypatch: pytest.MonkeyPatch, free: int) -> None:
    """Pin measured free space for the whole run, so the proof does not depend on the machine.

    The pre-F2 guard holds the **only** free-space comparison the canary module contains; every
    other ``disk_usage`` call records a number into a result document. Pinning the measurement
    therefore controls the guard and nothing else.
    """
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: _usage(free))


# ==========================================================================
# The frozen constant
# ==========================================================================
def test_the_floor_is_exactly_fifty_gibibytes() -> None:
    """One frozen constant, pinned to its byte value rather than to its expression."""
    assert canary.PRE_F2_MINIMUM_FREE_BYTES == _FIFTY_GIB
    assert canary.PRE_F2_MINIMUM_FREE_BYTES == 50 * 1024**3
    assert "PRE_F2_MINIMUM_FREE_BYTES" in canary.__all__


def test_the_superseded_thirty_gibibyte_floor_is_gone() -> None:
    """The old value is not merely smaller than the new one; it is not the constant."""
    assert canary.PRE_F2_MINIMUM_FREE_BYTES != _THIRTY_GIB
    assert canary.PRE_F2_MINIMUM_FREE_BYTES > _THIRTY_GIB


# ==========================================================================
# A. Below the floor refuses, and F2 is never called
# ==========================================================================
def test_one_byte_below_the_floor_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    """The boundary is proved at the floor, and the refusal states every fact D127 requires."""
    _fix_free(monkeypatch, _FIFTY_GIB - 1)
    with pytest.raises(canary.SingleSourceCanaryError) as raised:
        canary._require_pre_f2_free_space(Path("/nonexistent-is-never-reached"))
    message = str(raised.value)
    assert str(_FIFTY_GIB - 1) in message
    assert str(_FIFTY_GIB) in message
    assert "refused before its single transaction opened" in message


def test_the_superseded_thirty_gibibyte_amount_no_longer_admits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D137-R5: the exact amount that used to pass now refuses, and says which floor it missed.

    This is the falsification the replacement rests on. Proving that `50` GiB admits would leave
    open the possibility that `30` GiB still did too -- through a second branch, a fallback, or a
    caller-supplied override. There is none: the old amount is refused by the only comparison the
    module contains.
    """
    _fix_free(monkeypatch, _THIRTY_GIB)
    with pytest.raises(canary.SingleSourceCanaryError) as raised:
        canary._require_pre_f2_free_space(Path("/nonexistent-is-never-reached"))
    message = str(raised.value)
    assert str(_THIRTY_GIB) in message
    assert str(_FIFTY_GIB) in message
    assert "50 GiB" in message


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
    _fix_free(monkeypatch, _FIFTY_GIB - 1)

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
    [(_FIFTY_GIB, "exactly at the floor"), (_FIFTY_GIB + 1, "one byte above it")],
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
    _fix_free(monkeypatch, _FIFTY_GIB + 1)

    result, _private, _world = d116._run(tmp_path, run_id="d127-ordering")

    assert order == ["F1", "GUARD", "F2"]
    # The run completed normally above the floor: admission changes nothing about the outcome.
    assert result.association_totality
    assert result.operational_catalog_unchanged
