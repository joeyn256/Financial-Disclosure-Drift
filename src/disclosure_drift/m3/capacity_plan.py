"""The accepted Decision 113 §19 E0 working-state capacity requirement.

**The defect this closes.** The E0 successor preflight asked whether free space covered three
copies of the *current* catalog plus a gibibyte. The current catalog is the pre-E0 one -- about
0.36 GB, because E0 has never run -- so the predicate admitted any host with about 2.1 GB free.
Decision 112 measured what E0 actually needs and it is two orders of magnitude larger. A
predicate that passes on a host which provably cannot finish is worse than no predicate: it
converts a refusal into a partial run that fills the system volume.

**What replaces it.** A requirement computed from *measured densities* and the *planned* work,
not from the size of the artifact that has not been written yet:

* each component's measured bytes per unit, with the record that measured it;
* the planned unit counts -- distinct accessions and full-index rows -- likewise measured;
* the fixed costs a run needs beside its working state: the pre-E0 backup, the peak
  write-ahead log, and promotion and recovery headroom;
* the governed reserve D113 §15 fixes.

**Staleness fails closed.** The densities were measured against one specific source plan. If the
plan changes -- a source added, removed, or no longer required -- the bound requirement no longer
describes the work, so :func:`capacity_verdict` refuses rather than answering from a number that
has stopped applying. That is what makes this a *plan identity* rather than a constant.

Nothing here grants, implies, or performs any execution. It answers one question -- would a real
execution have room to finish -- and the accepted answer on the host that measured it is **no**.
"""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

__all__ = [
    "E0_WORKING_STATE_REQUIREMENT",
    "GOVERNED_RESERVE_BYTES",
    "CapacityVerdict",
    "MeasuredDensity",
    "PlannedUnits",
    "WorkingStateRequirement",
    "capacity_verdict",
    "plan_fingerprint",
]

#: The reserve accepted **Decision 113 §15** requires to remain after everything a real E0
#: execution needs. It supersedes D112 §6's 15 GiB minimum for actual v3 authorization.
GOVERNED_RESERVE_BYTES: Final = 25 * 1024**3


@dataclass(frozen=True, slots=True)
class MeasuredDensity:
    """One component's measured storage cost per unit of planned work.

    ``measured_by`` is not decoration. A density is only as good as the run that produced it,
    and binding the record that produced it into :meth:`WorkingStateRequirement.identity` is
    what stops a later reader from treating an inherited number as freshly measured.
    """

    component: str
    unit: str
    bytes_per_unit: float
    measured_by: str


@dataclass(frozen=True, slots=True)
class PlannedUnits:
    """How much work the accepted source plan represents, measured rather than assumed."""

    unit: str
    count: int
    measured_by: str


@dataclass(frozen=True, slots=True)
class WorkingStateRequirement:
    """The projected final E0 working state, and the free space a real execution needs.

    Deliberately arithmetic over measurements rather than a single number: every term can be
    read, checked against the record that measured it, and re-measured, which is what D113 §19
    asks for in place of a stale ad-hoc byte count.
    """

    contract: str
    plan_fingerprint: str
    plan_sources: int
    densities: tuple[MeasuredDensity, ...]
    units: tuple[PlannedUnits, ...]
    fixed_costs: tuple[tuple[str, int], ...]
    reserve_bytes: int = GOVERNED_RESERVE_BYTES

    def _count(self, unit: str) -> int:
        for planned in self.units:
            if planned.unit == unit:
                return planned.count
        message = f"no planned unit count is bound for {unit!r}"
        raise KeyError(message)

    def component_bytes(self) -> Mapping[str, int]:
        """Each component's projected bytes, in the order the densities are declared."""
        return {
            density.component: int(density.bytes_per_unit * self._count(density.unit))
            for density in self.densities
        }

    def working_state_bytes(self) -> int:
        """The projected complete working state, every planned source included."""
        return sum(self.component_bytes().values())

    def overhead_bytes(self) -> int:
        """Everything a run needs beside its working state, before the governed reserve."""
        return sum(value for _, value in self.fixed_costs)

    def required_bytes(self) -> int:
        """Free space a real execution needs: working state, overhead, and the reserve."""
        return self.working_state_bytes() + self.overhead_bytes() + self.reserve_bytes

    def identity(self) -> str:
        """A deterministic digest over every term of this requirement.

        Written into the refusal so the number a preflight refused on can be traced back to the
        exact densities, counts, and plan it was computed from.
        """
        digest = hashlib.sha256()
        digest.update(f"{self.contract}\x1f{self.plan_fingerprint}\x1f{self.plan_sources}".encode())
        for density in self.densities:
            digest.update(
                f"\x1e{density.component}\x1f{density.unit}\x1f"
                f"{density.bytes_per_unit:.4f}\x1f{density.measured_by}".encode()
            )
        for planned in self.units:
            digest.update(
                f"\x1e{planned.unit}\x1f{planned.count}\x1f{planned.measured_by}".encode()
            )
        for name, value in self.fixed_costs:
            digest.update(f"\x1e{name}\x1f{value}".encode())
        digest.update(f"\x1ereserve\x1f{self.reserve_bytes}".encode())
        return digest.hexdigest()


def plan_fingerprint(connection: sqlite3.Connection) -> tuple[str, int]:
    """A deterministic identity for one catalog's E0 source plan, and its row count.

    Built from what the plan *is* -- which sources, how many instances of each, and which are
    required -- and from nothing that changes as a run progresses, so the same plan fingerprints
    identically before and after any parse.
    """
    digest = hashlib.sha256()
    total = 0
    # Positional access, because the caller's connection may or may not carry a row factory and
    # a fingerprint that depended on that would be a fingerprint of the caller, not of the plan.
    for source_id, required, instances in connection.execute(
        "SELECT source_id, required, COUNT(*) AS instances FROM census_plan_sources "
        "GROUP BY source_id, required ORDER BY source_id, required"
    ):
        total += int(instances)
        digest.update(f"{source_id}\x1f{int(required)}\x1f{int(instances)}\x1e".encode())
    return digest.hexdigest(), total


@dataclass(frozen=True, slots=True)
class CapacityVerdict:
    """What one capacity evaluation established. ``satisfied`` is the predicate."""

    available_bytes: int
    required_bytes: int
    working_state_bytes: int
    overhead_bytes: int
    reserve_bytes: int
    requirement_identity: str
    plan_fingerprint: str
    plan_matches: bool

    @property
    def satisfied(self) -> bool:
        """Whether a real execution has room to finish **and** the plan still matches.

        Both conditions fail closed. A plan the requirement was not measured against is not a
        pass with a caveat: it means the projection describes different work.
        """
        return self.plan_matches and self.available_bytes >= self.required_bytes

    @property
    def shortfall_bytes(self) -> int:
        """How much more free space is needed, or zero."""
        return max(0, self.required_bytes - self.available_bytes)

    def describe(self) -> str:
        """One line naming the number refused on and the requirement it came from."""
        if not self.plan_matches:
            return (
                f"the catalog's source plan {self.plan_fingerprint} is not the plan requirement "
                f"{self.requirement_identity} was measured against; the projected working state "
                "does not describe this plan"
            )
        return (
            f"available bytes {self.available_bytes} are fewer than the {self.required_bytes} "
            f"a complete execution requires (projected working state "
            f"{self.working_state_bytes}, overhead {self.overhead_bytes}, governed reserve "
            f"{self.reserve_bytes}; requirement {self.requirement_identity})"
        )


def capacity_verdict(
    path: Path,
    plan: tuple[str, int] | None = None,
    requirement: WorkingStateRequirement | None = None,
) -> CapacityVerdict:
    """Evaluate whether ``path``'s filesystem can hold a complete E0 execution.

    Args:
        path: Any path on the filesystem the working catalog would live on.
        plan: The catalog's ``(fingerprint, source count)`` from :func:`plan_fingerprint`,
            checked against the plan the densities were measured over. A caller that could not
            read the plan passes its unreadable answer rather than omitting it: an empty
            fingerprint equals no accepted requirement, so it fails closed. Omitted only by a
            caller that has already established the plan itself.
        requirement: The requirement to evaluate, defaulting to the accepted one.
    """
    accepted = requirement or E0_WORKING_STATE_REQUIREMENT
    fingerprint = accepted.plan_fingerprint
    matches = True
    if plan is not None:
        fingerprint, sources = plan
        matches = fingerprint == accepted.plan_fingerprint and sources == accepted.plan_sources
    return CapacityVerdict(
        available_bytes=shutil.disk_usage(path).free,
        required_bytes=accepted.required_bytes(),
        working_state_bytes=accepted.working_state_bytes(),
        overhead_bytes=accepted.overhead_bytes(),
        reserve_bytes=accepted.reserve_bytes,
        requirement_identity=accepted.identity(),
        plan_fingerprint=fingerprint,
        plan_matches=matches,
    )


def _densities() -> Sequence[MeasuredDensity]:
    """The accepted D113 §14 measured densities. See the record for the runs behind them."""
    return (
        MeasuredDensity(
            component="submissions working state",
            unit="distinct_accession",
            bytes_per_unit=_SUBMISSIONS_BYTES_PER_ACCESSION,
            measured_by="D113 §14",
        ),
        MeasuredDensity(
            component="full-index working state",
            unit="full_index_row",
            bytes_per_unit=_FULL_INDEX_BYTES_PER_ROW,
            measured_by="D113 §14",
        ),
        MeasuredDensity(
            component="base catalog and small sources",
            unit="plan_source",
            bytes_per_unit=_BASE_BYTES_PER_PLAN_SOURCE,
            measured_by="D113 §14",
        ),
    )


#: Measured bytes of durable working state per distinct accession, under the accepted
#: ``e0-compact-evidence/2`` contract, on real prefixes of the real first planned source: the
#: larger of the two measured prefixes, because the per-accession cost rises slowly with catalog
#: size (B-tree depth) and the smaller prefix would understate the whole source.
_SUBMISSIONS_BYTES_PER_ACCESSION: Final = 2163.6

#: Measured bytes of durable working state per parsed ``company.idx`` row, same contract,
#: measured as the difference one real quarter makes to a real catalog.
_FULL_INDEX_BYTES_PER_ROW: Final = 1213.9

#: The pre-E0 catalog and the five small sources, spread across the plan's source rows.
_BASE_BYTES_PER_PLAN_SOURCE: Final = 6_600_000.0

#: The accepted requirement. Every number in it is measured; none is aspirational.
E0_WORKING_STATE_REQUIREMENT: Final = WorkingStateRequirement(
    contract="e0-compact-evidence/2",
    plan_fingerprint="e002446a3b2e11f757fafc568e1404493c6a15775bff379f3da72e7f6a384b75",
    plan_sources=76,
    densities=tuple(_densities()),
    units=(
        PlannedUnits(
            unit="distinct_accession", count=21_500_264, measured_by="D112 §6 from D111 totals"
        ),
        PlannedUnits(unit="full_index_row", count=18_376_265, measured_by="D112 §6"),
        PlannedUnits(unit="plan_source", count=76, measured_by="census_plan_sources"),
    ),
    fixed_costs=(
        ("pre-E0 backup", 360_000_000),
        ("peak write-ahead log", 290_000_000),
        ("run evidence and recovery headroom", 400_000_000),
    ),
)
