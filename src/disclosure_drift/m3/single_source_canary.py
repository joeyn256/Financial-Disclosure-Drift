"""The disposable single-source compact canary execution path (accepted Decision 116).

**The gap this closes.** Decision 113 measured the compact evidence contract on real prefixes
of the real first planned source and Decision 115 was to run the first real *whole-source*
canary against it. It stopped before creating a disposable world, because no supported path
existed that could run exactly one governed source under the accepted compact contract and be
relied on to stop: the reachable production driver
(:func:`~disclosure_drift.m3.offline_parse.run_offline_metadata_parse`) loads the whole plan,
traverses every planned source, defaults to full evidence, and wires no D112 §8 sidecar. This
module is that path.

**It is not E0, and it is not a second parser.** Every parse, identity, digest, and durable row
comes from the accepted modules: :mod:`~disclosure_drift.m3.offline_parse` for the one-source
entry point and the write footprint, :mod:`~disclosure_drift.m3.working_catalog` for the D111
run-local working catalog, :mod:`~disclosure_drift.m3.compact_evidence` for the
``e0-compact-evidence/2`` contract and its sidecar, and
:class:`~disclosure_drift.sec.census.CensusCatalog` for persistence. What this module adds is
the seam: select one governed source, build a disposable world, bind the compact contract
explicitly, run that source, stop, and report.

Four boundaries make it safe, and each is structural rather than promised:

* **Read-only authoritative inputs.** The accepted operational catalog is opened through
  ``SQLITE_OPEN_READONLY`` on every path here -- once to select the source, once for D111 to
  copy from, and once afterwards to re-measure its digest. Nothing in this module can write
  one of its bytes, and no writer lease is taken on it, so a stale lease is not even reachable.
* **Writable non-authoritative outputs only.** Every write lands in a disposable world beneath
  an operator-supplied work root that is refused unless it lies outside both the repository
  checkout and the private evidence root. The working catalog, its progress ledger, the compact
  sidecar, and the result document are the only artifacts produced, and none is promoted.
* **Exactly one source.** The only selector is ``census_plan_sources.source_instance_id``, and
  it resolves through the accepted plan or is refused. There is no path argument, no
  all-sources fallback, no loop, and no continuation: one invocation materializes one source
  and returns.
* **No E0 authority and no E0 namespace.** This module imports :mod:`disclosure_drift.m3.e0`
  nowhere, consults no activation constant, creates no run namespace under the private root,
  and applies no migration. A successful canary is not an authorization for anything.

**Nothing here authorizes running a real source.** Building the path is separate from being
told to use it; the next real execution needs its own owner instrument.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.config import EVIDENCE_ROOT_ENV
from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.capacity_plan import plan_fingerprint
from disclosure_drift.m3.compact_evidence import (
    COMPACT_EVIDENCE,
    COMPACT_EVIDENCE_CONTRACT,
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    CompactEvidenceSidecar,
)
from disclosure_drift.m3.evidence_paths import require_external_evidence_root
from disclosure_drift.m3.external_working_root import (
    CapacityObservation,
    ExternalCanaryPreflight,
    F2CapacityGuard,
    observe_capacity,
    require_external_envelope,
    require_phase_free_space,
)
from disclosure_drift.m3.offline_parse import (
    DIAGNOSTIC_PREFIX_CLASSIFICATION,
    AssociationTotality,
    SelectedPlannedSource,
    SingleSourceOutcome,
    materialize_census_associations,
    materialize_one_planned_source,
    materialize_planned_source_prefix,
    select_planned_source,
    write_containment,
)
from disclosure_drift.m3.working_catalog import (
    WORKING_CATALOG_FILENAME,
    WorkingCatalog,
    cache_size_pragma,
    file_digest,
)
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.census import CensusCatalog, ResolutionEvidence
from disclosure_drift.storage.catalog import CatalogWriter, strictly_read_only_connection
from disclosure_drift.storage.sqlite import applied_versions, utc_now

__all__ = [
    "CANARY_BATCH_SIZE",
    "CANARY_CONTRACT",
    "CANARY_PREFIX_RESULT_FILENAME",
    "CANARY_RESULT_FILENAME",
    "CANARY_RESOLUTION_SCOPE",
    "OPERATIONAL_CATALOG_RELATIVE_PATH",
    "PRE_F2_MINIMUM_FREE_BYTES",
    "WORKING_CATALOG_CACHE_BYTES",
    "WORKING_CATALOG_CACHE_SIZE_PRAGMA",
    "CanaryPrefixResult",
    "CanaryPreflight",
    "CanaryResult",
    "CanaryWorld",
    "SingleSourceCanaryError",
    "create_world",
    "preflight_single_source_canary",
    "require_canary_work_root",
    "require_disposable_work_root",
    "resolve_private_root",
    "run_single_source_canary",
    "run_single_source_prefix_profile",
    "validate_run_id",
]


class SingleSourceCanaryError(DisclosureDriftError):
    """A canary precondition failed. Never worked around, never retried in place."""


#: This path's own contract identity, recorded in every result document so a later reader can
#: tell exactly which shape produced it. It is deliberately **not** an evidence contract: the
#: evidence contract is ``e0-compact-evidence/2`` and this module only binds it.
CANARY_CONTRACT: Final = "m3.3-single-source-canary/1.0"

#: The accepted catalog, relative to the private evidence root.
#:
#: Restated rather than imported for the same reason ``m3/e0.py`` restates it from
#: ``m3/acquisition.py``: this module must not import the E0 driver, and the value is one
#: literal. The three copies are pinned equal by test rather than kept in step by comment.
OPERATIONAL_CATALOG_RELATIVE_PATH: Final = "catalogs/m3_2a_operational.sqlite3"

#: The create-once result document, written into the disposable world when a run completes.
CANARY_RESULT_FILENAME: Final = "canary_result.json"

#: The create-once result document a bounded diagnostic prefix writes. A **different** name from
#: the complete-source one on purpose: a world holding a prefix result holds no canary result,
#: and no reader that goes looking for one can be handed the other.
CANARY_PREFIX_RESULT_FILENAME: Final = "canary_prefix_result.json"

#: The explicit page-cache budget the disposable canary's writable working catalog runs under
#: (accepted **Decision 119 §4**, ruling C1): 512 MiB.
#:
#: SQLite configures no ``cache_size`` unless one is asked for, so before this the working
#: catalog wrote through SQLite's own default of about 2 MiB. Accepted Decision 118 measured
#: that against a working set two orders of magnitude larger and found the resulting
#: random-write amplification -- a lower bound of 13.22x physical writes, a write-ahead log
#: lower bound of 169.61 GiB, and cold page access 45-85x warm -- to be the primary constraint
#: on real materialization throughput.
#:
#: It is an **execution parameter**, not an evidence semantic: it changes how much memory the
#: write may use and moves no row, no ordering, no digest, and no identity. It is bound here
#: rather than in :mod:`~disclosure_drift.m3.working_catalog` so that the D111 mechanism stays
#: opt-in and every other caller keeps the behaviour it already had.
WORKING_CATALOG_CACHE_BYTES: Final = 512 * 1024 * 1024

#: What :data:`WORKING_CATALOG_CACHE_BYTES` resolves to in SQLite's negative ``cache_size``
#: form, which is the value the writable working connection must report: ``-524288`` KiB.
WORKING_CATALOG_CACHE_SIZE_PRAGMA: Final = cache_size_pragma(WORKING_CATALOG_CACHE_BYTES)

#: Parts per real transaction, with write-ahead-log truncation at each boundary. This is the
#: configuration accepted **Decision 113 §14** measured the real densities under, so a canary
#: reproduces the measurement's own journal behaviour rather than inventing a second one.
CANARY_BATCH_SIZE: Final = 250

#: The scope one resolution pass is recorded under in the sidecar. A canary resolves the whole
#: working catalog exactly once, which is the same scope the accepted D113 §11 evidence uses.
CANARY_RESOLUTION_SCOPE: Final = "catalog"

#: The free-space floor that must hold on the run volume **immediately before F2 opens its
#: single transaction**: 50 GiB, ``53,687,091,200`` bytes.
#:
#: **The value is Decision 137's (D137-R5); the mechanism is Decision 127's, unchanged.** The
#: guard was introduced at 30 GiB, ``32,212,254,720`` bytes -- the figure accepted **Decision
#: 124 §9** (D124-R5) carried at the time. Accepted **Decision 135** §8 (D135-R3) then
#: reconciled the corrected complete-source run's capacity and found 30 GiB **inadequate** for
#: it, and accepted **Decision 136** §11 (D136-R11 item 6) made replacing that behaviour the
#: next stage's work rather than its own. This is that replacement: the constant moves, the
#: strict ``<`` comparison, the call site, and the refusal shape do not.
#:
#: The old 30 GiB behaviour has **no reachable path**. It was one constant read from one
#: comparison, so raising the constant retires it entirely rather than leaving a second branch
#: a caller could still select.
#:
#: It remains a *boundary* measurement: taken immediately before opening F2, and explicitly
#: **not** inherited from the run's starting free-space gate -- which is a different, larger
#: number for a different question (`185` GiB at ``PRE_LAUNCH``; see
#: :data:`~disclosure_drift.m3.external_working_root.LAUNCH_MINIMUM_FREE_BYTES`). The
#: **continuous** emergency floor *during* F2 is a third number and stays where D124-R5 put it,
#: at `10` GiB (:data:`~disclosure_drift.m3.external_working_root.F2_HARD_FLOOR_FREE_BYTES`).
#:
#: Accepted **Decision 126 §7** (D126-R6) records why it has to live here rather than in a
#: launch wrapper or an external sampler. F1 returns and F2 begins in consecutive statements, so
#: there is no window an outside process can occupy; nothing durable changes at the boundary, so
#: an observer cannot tell "F1 finished" from "F2 is about to open" by reading state; a signal
#: from outside is advisory where admission has to be dispositive; and free space sampled at any
#: instant before the call describes a different instant than the one that matters. Tightening a
#: sampler's cadence shrinks that race and never closes it. Only the path that is about to open
#: the transaction can decline to open it.
#:
#: It is an **admission predicate**, not a budget. It moves no row, no ordering, no digest, and
#: no identity, and F2's behaviour at or above the floor is exactly what it was before.
PRE_F2_MINIMUM_FREE_BYTES: Final = 50 * 1024**3

#: A run identity is a short, lowercase, filesystem-safe slug. It names one disposable world and
#: is never reused: an identity that already has a world is refused rather than resumed.
_RUN_ID_PATTERN: Final = r"\A[a-z0-9][a-z0-9_-]{0,127}\Z"

_DIRECTORY_MODE: Final = 0o700
_FILE_MODE: Final = 0o600

#: Exit codes, matching the repository's operator convention.
_EXIT_OK: Final = 0
_EXIT_GATE_FAILURE: Final = 4

#: How a run reports reaching one accepted capacity phase boundary (D137-R7).
#:
#: A callback rather than a field, because the boundaries live inside ``_materialize`` where the
#: result object does not exist yet, and because an internal-volume run passes ``None`` and is
#: then byte-for-byte the run it was before Decision 137.
_PhaseObserver = Callable[[str], None]


# --------------------------------------------------------------------------- #
# The private root, the work root, and the disposable world
# --------------------------------------------------------------------------- #
def resolve_private_root(
    repository_root: Path, *, environ: Mapping[str, str] | None = None
) -> Path:
    """Resolve the accepted private evidence root from the one recognized variable.

    Restated here rather than imported from the E0 module so this path carries no E0 import at
    all; the rule is the accepted external-root boundary either way, and the variable's name
    comes from :mod:`disclosure_drift.config` rather than from a second literal.

    The **value** is never returned to a renderer, written into a result document, or logged.
    Callers receive a path they open files with and report only names relative to a root.

    Raises:
        SingleSourceCanaryError: the variable is absent, blank, or not a lawful external root.
    """
    source = os.environ if environ is None else environ
    raw = source.get(EVIDENCE_ROOT_ENV)
    if raw is None or not raw.strip():
        message = (
            f"{EVIDENCE_ROOT_ENV} is not set; this command reads the accepted private root "
            "from that variable alone and has no default, no fallback, and no path option"
        )
        raise SingleSourceCanaryError(message)
    try:
        return require_external_evidence_root(raw, repository_root)
    except (ValueError, OSError) as exc:
        # The boundary's own messages never name either resolved path, so quoting the
        # exception text here cannot leak one.
        message = f"{EVIDENCE_ROOT_ENV} is not a lawful external evidence root: {exc}"
        raise SingleSourceCanaryError(message) from exc


def _comparable(path: Path) -> tuple[str, ...]:
    """Case-folded resolved components, so an alias or a case variant cannot launder a path."""
    return tuple(part.casefold() for part in Path(os.path.realpath(path)).parts)


def _within(ancestor: tuple[str, ...], descendant: tuple[str, ...]) -> bool:
    return len(descendant) > len(ancestor) and descendant[: len(ancestor)] == ancestor


def require_disposable_work_root(
    work_root: str | Path, repository_root: Path, private_root: Path
) -> Path:
    """Return the resolved work root a disposable world may be built under, or refuse.

    Two rules, both fail-closed and both stated on resolved, case-folded paths so a symlink or
    a case variant cannot launder containment:

    * the root must be **outside the repository checkout**, which is the accepted external-root
      boundary, reused rather than restated;
    * the root must be **outside the private evidence root**, and must not contain it. Accepted
      Decision 116 §7 puts every writable canary output outside the authoritative evidence
      tree, so a world beneath it -- or a work root that swallowed it -- is refused before
      anything is created.

    No message names either resolved path.

    Raises:
        SingleSourceCanaryError: the work root is not a lawful disposable location.
    """
    try:
        resolved = require_external_evidence_root(work_root, repository_root)
    except (ValueError, OSError) as exc:
        message = f"the canary work root is not a lawful external directory: {exc}"
        raise SingleSourceCanaryError(message) from exc
    work_parts = _comparable(resolved)
    private_parts = _comparable(private_root)
    if work_parts == private_parts or _within(private_parts, work_parts):
        message = (
            "the canary work root is the private evidence root or lies inside it; every "
            "writable canary output stays outside the authoritative evidence tree"
        )
        raise SingleSourceCanaryError(message)
    if _within(work_parts, private_parts):
        message = (
            "the canary work root contains the private evidence root; the authoritative "
            "evidence tree must not lie inside a disposable work tree"
        )
        raise SingleSourceCanaryError(message)
    return resolved


def _package_repository_root() -> Path:
    """The repository checkout this package is installed from.

    Derived from this module's own location rather than accepted as an argument, so a direct
    library caller cannot declare a decoy checkout and have a disposable world created inside
    the real one. It is the rule the operator surface already uses, one directory deeper
    because this module sits under ``m3``.
    """
    return Path(__file__).resolve().parents[3]


def _authoritative_private_root(repository_root: Path) -> Path | None:
    """The private evidence root this **process** declares, or ``None`` when it declares none.

    Read from the real process environment rather than from any argument, so the containment
    rule below cannot be declared away by the caller it constrains. When the variable is unset
    there is no authoritative evidence tree in this process for a work root to be inside of,
    and the rule has nothing to say; when it is set it must be lawful, exactly as it must be
    for every other surface that resolves it.
    """
    if not os.environ.get(EVIDENCE_ROOT_ENV, "").strip():
        return None
    return resolve_private_root(repository_root)


def require_canary_work_root(work_root: str | Path, *, tree: DataTree) -> Path:
    """Enforce the disposable work-root invariant at the **library** execution boundary.

    Accepted Decision 116 §7 puts every writable canary output outside the repository checkout
    and outside the authoritative evidence tree. That invariant belongs to the *run*, not to
    the operator surface: a direct library caller must not be able to reach a location the
    operator surface would have refused, so the run establishes it itself rather than trusting
    that whoever called it already did.

    One rule, not two. :func:`require_disposable_work_root` is the accepted primitive and stays
    the only place the rule is stated; this function applies it to each evidence root a run must
    stay clear of:

    * ``tree.data_root`` -- the evidence tree this very run reads its frozen artifacts from.
      Taken from the run's own input rather than declared beside it, so it cannot disagree with
      what the run actually opens;
    * the authoritative private evidence root the process declares, whenever it declares one.
      In ordinary operation these are the same root, because the operator surface builds the
      tree from it; they differ only for a caller reading a stand-in tree, and that caller is
      still held to the authoritative one.

    The repository checkout, absoluteness, and symlink resolution come from the same primitive
    and are derived rather than declared, so none of them is a caller's to soften.

    Returns:
        The resolved work root. Validating an already-validated root returns it unchanged, so
        the operator surface's early refusal and this one cannot disagree about a lawful root.

    Raises:
        SingleSourceCanaryError: the work root is not a lawful disposable location.
    """
    repository_root = _package_repository_root()
    resolved = require_disposable_work_root(work_root, repository_root, tree.data_root)
    authoritative = _authoritative_private_root(repository_root)
    if authoritative is not None:
        require_disposable_work_root(work_root, repository_root, authoritative)
    return resolved


def validate_run_id(run_id: str) -> str:
    """Return ``run_id`` if it is a lawful world name, else refuse.

    The identity becomes a directory name under the operator's work root, so it is validated
    rather than trusted: an absolute path, a parent reference, or a separator would place a
    disposable world somewhere the work-root boundary never approved.
    """
    if not re.fullmatch(_RUN_ID_PATTERN, run_id):
        message = (
            f"canary run identity {run_id!r} is not of the accepted shape; an identity is "
            "1-128 characters of lowercase letters, digits, underscore, and hyphen, "
            "starting alphanumeric"
        )
        raise SingleSourceCanaryError(message)
    return run_id


@dataclass(frozen=True, slots=True)
class CanaryWorld:
    """One disposable world: where a canary's writable outputs live, and nothing else.

    Every path here is beneath :attr:`directory`, which is beneath the operator's work root.
    None of them is under the private evidence root, and none is ever promoted.
    """

    run_id: str
    directory: Path

    @property
    def working_catalog(self) -> Path:
        """The D111 run-local working catalog."""
        return self.directory / WORKING_CATALOG_FILENAME

    @property
    def sidecar(self) -> Path:
        """The D112 §8 compact-evidence sidecar."""
        return self.directory / COMPACT_EVIDENCE_SIDECAR_FILENAME

    @property
    def result(self) -> Path:
        """The create-once result document."""
        return self.directory / CANARY_RESULT_FILENAME

    @property
    def prefix_result(self) -> Path:
        """The create-once result document a bounded diagnostic prefix writes."""
        return self.directory / CANARY_PREFIX_RESULT_FILENAME


def create_world(work_root: Path, run_id: str) -> CanaryWorld:
    """Create one disposable world exactly once, at mode ``0700``.

    ``mkdir`` without ``exist_ok`` is the create-once primitive: it is atomic, so two callers
    cannot both believe they created the world, and an identity whose world already exists is
    refused rather than resumed, repaired, or overwritten. A symlink at either the work root or
    the world path is refused before anything is created.

    Raises:
        SingleSourceCanaryError: the identity is unlawful, or its world already exists.
    """
    validate_run_id(run_id)
    if work_root.is_symlink():
        message = "the canary work root is a symbolic link and is refused"
        raise SingleSourceCanaryError(message)
    if not work_root.exists():
        work_root.mkdir(mode=_DIRECTORY_MODE, parents=True)
    if not work_root.is_dir():
        message = "the canary work root exists and is not a directory"
        raise SingleSourceCanaryError(message)
    target = work_root / run_id
    if target.is_symlink():
        message = f"canary world {run_id!r} exists as a symbolic link and is refused"
        raise SingleSourceCanaryError(message)
    if target.exists():
        message = (
            f"canary world {run_id!r} already exists; a disposable world is create-once and "
            "is never reused, resumed, repaired, or overwritten"
        )
        raise SingleSourceCanaryError(message)
    target.mkdir(mode=_DIRECTORY_MODE)
    target.chmod(_DIRECTORY_MODE)
    return CanaryWorld(run_id=run_id, directory=target)


def _write_once(path: Path, payload: bytes) -> None:
    """Create ``path`` with ``O_EXCL`` at mode ``0600`` and write it.

    ``O_CREAT | O_EXCL`` makes this write-once at the operating system rather than by a prior
    existence check, so completed run-local evidence has no window in which it could be
    silently replaced.
    """
    if path.exists() or path.is_symlink():
        message = f"{path.name} already exists; completed run-local evidence is never overwritten"
        raise SingleSourceCanaryError(message)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, _FILE_MODE)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    path.chmod(_FILE_MODE)


# --------------------------------------------------------------------------- #
# Preflight
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CanaryPreflight:
    """What a read-only canary preflight established. It creates nothing.

    Every field is measured from the world rather than asserted, and the accepted catalog is
    read through a strictly read-only handle, so running a preflight leaves it byte-identical.
    """

    run_id: str
    source_instance_id: str
    source_id: str
    plan_position: int
    plan_source_count: int
    plan_fingerprint: str
    observation_id: str | None
    retrieval_state: str
    snapshot_state: str
    parser_state: str
    migration_head: int
    operational_catalog_sha256: str
    operational_catalog_byte_length: int
    work_root_free_bytes: int
    world_absent: bool
    #: The page-cache budget the run would give its writable working catalog, and the
    #: ``PRAGMA cache_size`` value it resolves to. Reported by a preflight because a preflight
    #: creates nothing and therefore has no connection to read the effective value from: this
    #: is the **requested** setting, stated so it can be verified before a run rather than
    #: reconstructed after one. Both are host-independent constants, so a preflight record
    #: stays deterministic.
    working_catalog_cache_bytes: int | None
    working_catalog_cache_size_pragma: int | None

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "contract": CANARY_CONTRACT,
            "evidence_contract": COMPACT_EVIDENCE_CONTRACT,
            "run_id": self.run_id,
            "source_instance_id": self.source_instance_id,
            "source_id": self.source_id,
            "plan_position": self.plan_position,
            "plan_source_count": self.plan_source_count,
            "plan_fingerprint": self.plan_fingerprint,
            "observation_id": self.observation_id,
            "retrieval_state": self.retrieval_state,
            "snapshot_state": self.snapshot_state,
            "parser_state": self.parser_state,
            "migration_head": self.migration_head,
            "operational_catalog_sha256": self.operational_catalog_sha256,
            "operational_catalog_byte_length": self.operational_catalog_byte_length,
            "work_root_free_bytes": self.work_root_free_bytes,
            "world_absent": self.world_absent,
            "working_catalog_cache_bytes": self.working_catalog_cache_bytes,
            "working_catalog_cache_size_pragma": self.working_catalog_cache_size_pragma,
        }


def preflight_single_source_canary(
    *,
    operational_catalog: Path,
    work_root: Path,
    run_id: str,
    source_instance_id: str,
    cache_bytes: int | None = WORKING_CATALOG_CACHE_BYTES,
) -> CanaryPreflight:
    """Validate every predicate a run needs, read-only, and create nothing.

    Args:
        operational_catalog: The accepted catalog. Opened strictly read-only.
        work_root: The disposable work root free space is measured under.
        run_id: The world identity whose absence is checked.
        source_instance_id: The one planned source's own plan key.
        cache_bytes: The page-cache budget a run would request for its writable working
            catalog, reported rather than applied -- a preflight opens no writable connection.
            An unrepresentable budget is refused here, before a run could discover it.

    Raises:
        SingleSourceCanaryError: a predicate the run depends on does not hold.
        OfflineParseError: the identifier names no planned source, or names more than one.
    """
    cache_pragma = None if cache_bytes is None else cache_size_pragma(cache_bytes)
    validate_run_id(run_id)
    if not operational_catalog.is_file():
        message = "the accepted operational catalog does not exist at its fixed relative path"
        raise SingleSourceCanaryError(message)
    with strictly_read_only_connection(operational_catalog) as connection:
        selected = select_planned_source(connection, source_instance_id)
        fingerprint, _ = plan_fingerprint(connection)
        applied = applied_versions(connection)
    if not applied:
        message = "the accepted operational catalog records no applied migration"
        raise SingleSourceCanaryError(message)
    digest, byte_length = file_digest(operational_catalog)
    source = selected.source
    return CanaryPreflight(
        run_id=run_id,
        source_instance_id=source.source_instance_id,
        source_id=source.source_id,
        plan_position=selected.plan_position,
        plan_source_count=selected.plan_source_count,
        plan_fingerprint=fingerprint,
        observation_id=source.observation_id,
        retrieval_state=source.retrieval_state,
        snapshot_state=source.snapshot_state,
        parser_state=source.parser_state,
        migration_head=max(applied),
        operational_catalog_sha256=digest,
        operational_catalog_byte_length=byte_length,
        work_root_free_bytes=shutil.disk_usage(_measurable(work_root)).free,
        world_absent=not (work_root / run_id).exists(),
        working_catalog_cache_bytes=cache_bytes,
        working_catalog_cache_size_pragma=cache_pragma,
    )


def _measurable(path: Path) -> Path:
    """The nearest existing ancestor of ``path``, so free space can be measured before mkdir."""
    candidate = path
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #
class _WorkingCatalogWriter(CatalogWriter):
    """The accepted writer type, bound to a working catalog's already-open connection.

    The D111 working catalog owns its file and its connection: it creates the copy, opens
    exactly one writing handle on it, and closes that handle when its context ends. Taking a
    second :class:`CatalogWriter` lease on the same file would open a second writing handle
    for a serialization guarantee the single owner already provides.

    So this binds the accepted type to the connection D111 already holds. It acquires no
    lease, opens nothing, and closes nothing -- :class:`~disclosure_drift.sec.census.CensusCatalog`
    reads ``connection`` and nothing else, and the file it reads is a disposable run-local
    copy rather than the accepted catalog.
    """

    def __init__(self, working: WorkingCatalog) -> None:
        super().__init__(working.path, working.path.parent)
        self._connection = working.connection


@dataclass(frozen=True, slots=True)
class CanaryResult:
    """Everything one disposable single-source run established.

    Wide on purpose: accepted Decision 116 §9 fixes what a later execution report must be able
    to determine from one invocation, and a field that had to be recovered by re-opening the
    working catalog would be a field the report could get wrong. Every count is read from
    durable rows, every digest comes from the accepted compact-evidence contract, and every
    measurement is taken from the filesystem -- none is estimated here.
    """

    contract: str
    evidence_contract: str
    run_id: str
    started_at_utc: str
    completed_at_utc: str

    # -- the one source -------------------------------------------------- #
    source_instance_id: str
    source_id: str
    plan_position: int
    plan_source_count: int
    plan_fingerprint: str
    source_observation_id: str | None
    source_artifact_sha256: str
    source_artifact_byte_length: int
    disposition: str
    parser_state_before: str
    parser_state_after: str
    parser_run_id: str | None

    # -- what the traversal produced ------------------------------------- #
    members: int
    projection_records: int
    parsed_records: int
    quarantined_records: int
    omitted_field_observations: int
    materialized_field_observations: int

    # -- what the working catalog holds ---------------------------------- #
    canonical_accession_count: int
    registrant_count: int
    substantive_relation_count: int
    quarantined_record_count: int
    structural_observation_count: int
    accession_observation_count: int
    field_resolution_row_count: int
    cohort_resolution_row_count: int
    association_totality: Mapping[str, int]

    # -- resolution and corroboration ------------------------------------ #
    resolution_accessions: int
    implicit_resolutions: int
    explicit_resolutions: int
    omitted_field_rows: int
    materialized_field_rows: int
    omitted_cohort_rows: int
    materialized_cohort_rows: int
    index_rows: int
    corroborating_rows: int
    corroboration_exceptions: int
    unbound_accessions: int
    omitted_corroboration_observations: int

    # -- the accepted identities ----------------------------------------- #
    member_manifest_digest: str
    projection_digest: str
    resolution_digest: str
    corroboration_digest: str
    compact_evidence_identity: str

    # -- the disposable world -------------------------------------------- #
    world_relative_working_catalog: str
    world_relative_sidecar: str
    working_catalog_sha256: str
    working_catalog_byte_length: int
    #: The write-ahead log remaining **after** the run's final checkpoint, which is evidence
    #: that the log was reclaimed rather than a peak. Sampling the peak means watching the file
    #: during the run, which D116 §9 leaves to the outer operator rather than inventing here.
    working_catalog_wal_byte_length: int
    working_catalog_source_sha256: str
    migration_head: int

    # -- the accepted catalog, before and after -------------------------- #
    operational_catalog_sha256_before: str
    operational_catalog_sha256_after: str
    work_root_free_bytes_before: int
    work_root_free_bytes_after: int

    # -- the D137-R7 phase-boundary capacity evidence --------------------- #
    #: One record per accepted phase boundary the run reached, in order, for a run held to the
    #: Decision 137 external-volume requirement. Empty for every other run, which has no
    #: external volume to observe and no qualified temporary root to size.
    capacity_observations: tuple[Mapping[str, object], ...] = ()

    @property
    def operational_catalog_unchanged(self) -> bool:
        """Whether the accepted catalog is byte-identical to what the run started from."""
        return self.operational_catalog_sha256_before == self.operational_catalog_sha256_after

    def identities(self) -> Mapping[str, str]:
        """The five accepted identities, alone. Deterministic over one frozen artifact."""
        return {
            "member_manifest_digest": self.member_manifest_digest,
            "projection_digest": self.projection_digest,
            "resolution_digest": self.resolution_digest,
            "corroboration_digest": self.corroboration_digest,
            "compact_evidence_identity": self.compact_evidence_identity,
        }

    def as_record(self) -> Mapping[str, object]:
        """The complete result as a plain mapping, carrying no absolute path.

        The two world artifacts are named **relative to the disposable world**, so a result
        document can be read, quoted, or moved without disclosing where the world was built.

        ``capacity_observations`` is emitted only when the run actually took some. A run without
        an external-volume requirement takes none, and rendering an empty list for it would
        change the result document every previous canary produced -- including the byte-level
        evidence-equivalence the accepted Decision 119 cache-budget proof rests on. An absent
        key and an empty list say the same thing here, and only one of them is free.
        """
        record: dict[str, object] = {}
        for name in self.__slots__:
            if name == "capacity_observations" and not self.capacity_observations:
                continue
            record[name] = getattr(self, name)
        record["operational_catalog_unchanged"] = self.operational_catalog_unchanged
        return record


def _counts(connection: sqlite3.Connection) -> Mapping[str, int]:
    """Row counts for the tables a result reports, read from the working catalog."""
    tables = {
        "canonical_accession_count": "census_accessions",
        "registrant_count": "census_registrants",
        "quarantined_record_count": "census_quarantined_records",
        "structural_observation_count": "census_structural_observations",
        "accession_observation_count": "census_accession_observations",
        "field_resolution_row_count": "census_accession_field_resolutions",
        "cohort_resolution_row_count": "census_accession_cohort_resolutions",
    }
    counted = {
        key: int(
            connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]  # noqa: S608
        )
        for key, table in tables.items()
    }
    counted["substantive_relation_count"] = int(
        connection.execute(
            "SELECT COUNT(*) AS n FROM census_accession_registrants "
            "WHERE association_class = 'substantive'"
        ).fetchone()["n"]
    )
    return counted


def run_single_source_canary(
    *,
    operational_catalog: Path,
    tree: DataTree,
    work_root: Path,
    run_id: str,
    source_instance_id: str,
    batch_size: int = CANARY_BATCH_SIZE,
    cache_bytes: int | None = WORKING_CATALOG_CACHE_BYTES,
    require_volume_uuid: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> CanaryResult:
    """Run **exactly one** governed planned source into a disposable world, and stop.

    The whole path, in order:

    0. establish the write boundary: refuse any work root that is not a lawful disposable
       location, and — when it resolves onto an external volume — refuse it unless the complete
       Decision 137 envelope holds, before a directory, a catalog, or a result document exists
       to refuse it for;
    1. select the one source from the accepted plan, through a strictly read-only handle;
    2. create the disposable world, once, refusing an identity that already has one;
    3. copy the accepted catalog into a D111 run-local working catalog, read-only on the source;
    4. open the D112 §8 sidecar and bind
       :data:`~disclosure_drift.m3.compact_evidence.COMPACT_EVIDENCE` **explicitly**, so the
       full-observation default cannot be reached by omission;
    5. inside the accepted **R17** write containment, materialize that one source, resolve the
       working catalog once, and run the Decision 094 §6.4 association projection;
    6. record the D113 §§8-9 resolution and corroboration evidence into the sidecar;
    7. measure the world and re-measure the accepted catalog;
    8. write the create-once result document.

    There is no step 9. Nothing enumerates a second source, and the return is the end of the
    run rather than the end of an iteration.

    Args:
        operational_catalog: The accepted catalog. Opened strictly read-only, always.
        tree: The data tree the frozen source artifacts are read from.
        work_root: The disposable work root. Validated **here**, by
            :func:`require_canary_work_root`, before any world exists -- a caller's own prior
            validation is welcome and is never what this run relies on.
        run_id: This world's identity. Create-once.
        source_instance_id: The one planned source's own plan key.
        batch_size: Parts per real transaction, defaulting to the accepted D113 §14 value.
        cache_bytes: The page-cache budget for the **run-local writable** working catalog,
            defaulting to the accepted :data:`WORKING_CATALOG_CACHE_BYTES`. ``None`` restores
            SQLite's own default and is what the equivalence proof runs against: the budget is
            an execution parameter, so two runs that differ only in it must reach byte-identical
            evidence. It reaches no other connection and no other database.
        require_volume_uuid: An **assertion** that the working root is on the named volume, or
            ``None``. It is not the switch that decides whether the external envelope applies
            (Decision 138, D138-R1): **the resolved root decides that**, so an external root is
            protected whether or not this is supplied, and omitting it cannot disable a single
            guard. Supplying it can only add a requirement — it forces the envelope onto a root
            that would classify as internal — and it must be the one qualified volume
            (D138-R12). An internal root with no assertion is exactly what Decision 116 left it.
        environ: The environment ``SQLITE_TMPDIR`` is cross-checked against when an external
            volume is required; SQLite's own environment is the authority (D138-R3). Defaults to
            the process's own.

    Raises:
        ExternalWorkingRootError: the working root is external and a guard did not hold, an
            arbitrary volume was asserted, or the continuous ``DURING_F2`` floor was reached —
            in which case F2 rolled back and committed nothing.
        SingleSourceCanaryError: a canary precondition failed.
        OfflineParseError: any accepted fail-closed parse condition, unchanged.
        WorkingCatalogError: the disposable working catalog could not be built safely.
    """
    # 0. The write boundary, established before anything is measured, opened, or created.
    #    Accepted Decision 116 §7 is the run's own invariant, so an unlawful work root fails
    #    closed here rather than at whichever caller happened to check.
    resolved_work_root = require_canary_work_root(work_root, tree=tree)
    #    Decision 138 (D138-R1): whether the external envelope applies is decided by the
    #    resolved root itself, never by whether an argument was supplied. An external root gets
    #    identity by Volume UUID, isolation from the immutable D130 archive, the bounded archive
    #    precheck, the 185 GiB launch floor, and an explicit external SQLITE_TMPDIR -- all
    #    established here, before a world exists to place, and all refusing rather than falling
    #    back to internal storage. An internal root gets exactly what Decision 116 left it.
    external: ExternalCanaryPreflight | None = require_external_envelope(
        resolved_work_root,
        observed_at=utc_now(),
        environ=environ,
        asserted_uuid=require_volume_uuid,
    )
    started = utc_now()
    if not operational_catalog.is_file():
        message = "the accepted operational catalog does not exist at its fixed relative path"
        raise SingleSourceCanaryError(message)
    catalog_before, _ = file_digest(operational_catalog)
    free_before = shutil.disk_usage(_measurable(resolved_work_root)).free

    # 1. The one source, and the plan it came from. Strictly read-only: this handle cannot
    #    write, and it is closed before the working copy is taken.
    with strictly_read_only_connection(operational_catalog) as reader:
        selected = select_planned_source(reader, source_instance_id)
        fingerprint, _ = plan_fingerprint(reader)

    # 2. The disposable world. Create-once, and never under the private evidence root.
    world = create_world(resolved_work_root, run_id)

    observations: list[CapacityObservation] = []

    def record_phase(phase: str) -> None:
        """Record one accepted D137-R7 phase boundary, and enforce its floor -- D138-R5, R6.

        The observation is taken first and appended unconditionally, so a refusal still leaves
        the reading that caused it: `POST_F0` and `PRE_F1` are stop-and-report **gates**, and a
        gate that discards its own evidence tells the operator nothing. A measurement that could
        not be taken never reaches the comparison -- :func:`observe_capacity` has already
        refused it, which is why an unmeasurable boundary refuses rather than being admitted.
        """
        if external is None:  # pragma: no cover - never bound without an external requirement
            return
        observation = observe_capacity(
            phase,
            working_root=world.directory,
            database=world.working_catalog,
            wal=world.working_catalog.with_name(f"{WORKING_CATALOG_FILENAME}-wal"),
            temp_directory=external.temp_directory,
            volume=external.volume,
            observed_at=utc_now(),
        )
        observations.append(observation)
        require_phase_free_space(observation)

    observer: _PhaseObserver | None = None
    #    Decision 138 (D138-R8): continuous DURING_F2 enforcement lives INSIDE the process that
    #    executes F2, never in an optional second one. Bound only on the protected external
    #    path, and sharing the run's own observation list so its alerts land chronologically
    #    among the phase boundaries rather than in a parallel record.
    capacity_guard: F2CapacityGuard | None = None
    if external is not None:
        observations.append(external.observation)
        observer = record_phase
        capacity_guard = F2CapacityGuard(
            working_root=world.directory,
            volume=external.volume,
            record_into=observations,
        )

    # 3-7. Everything writable, inside the world.
    with WorkingCatalog(operational_catalog, world.directory, cache_bytes=cache_bytes) as working:
        sidecar = CompactEvidenceSidecar(world.sidecar)
        try:
            materialized = _materialize(
                working=working,
                tree=tree,
                selected=selected,
                sidecar=sidecar,
                batch_size=batch_size,
                observe=observer,
                capacity_guard=capacity_guard,
            )
            identities = _record_evidence(sidecar=sidecar, materialized=materialized)
            working.checkpoint()
            wal_bytes = working.wal_byte_length()
            source_sha256 = working.identity.source_file_sha256
            migration_head = working.identity.migration_head
        finally:
            sidecar.close()
    # Measured together, after the context closed the last handle, so the reported digest and
    # the reported length describe the same bytes rather than two moments.
    working_sha256, working_bytes = file_digest(world.working_catalog)

    catalog_after, _ = file_digest(operational_catalog)
    result = _result(
        world=world,
        started=started,
        selected=selected,
        fingerprint=fingerprint,
        materialized=materialized,
        identities=identities,
        working_sha256=working_sha256,
        working_bytes=working_bytes,
        wal_bytes=wal_bytes,
        source_sha256=source_sha256,
        migration_head=migration_head,
        catalog_before=catalog_before,
        catalog_after=catalog_after,
        free_before=free_before,
        free_after=shutil.disk_usage(world.directory).free,
        capacity_observations=tuple(observations),
    )
    # 8. Create-once. A second run that somehow reached this world would fail here rather
    #    than replace the evidence the first one wrote.
    _write_once(world.result, json.dumps(result.as_record(), indent=2, sort_keys=True).encode())
    return result


@dataclass(frozen=True, slots=True)
class _Materialized:
    """The one source's parse, the projection it produced, and the counts left behind."""

    outcome: SingleSourceOutcome
    totality: AssociationTotality
    counts: Mapping[str, int]
    resolution: ResolutionEvidence


def _require_pre_f2_free_space(directory: Path) -> int:
    """Refuse F2 unless the run volume holds :data:`PRE_F2_MINIMUM_FREE_BYTES` free.

    Free space is measured on ``directory``'s volume, which is the disposable world the working
    catalog and its write-ahead log live on -- the volume F2's transaction actually consumes.

    **Raising here is the whole mechanism.** The caller is the statement that would otherwise
    call :func:`~disclosure_drift.m3.offline_parse.materialize_census_associations` next, so a
    refusal lands **before** F2's single transaction opens rather than during it. Accepted
    Decision 116 §5 keeps the surrounding rule intact: a refused run leaves the accepted catalog
    unchanged, and a failed gate is reported rather than worked around or retried in place.

    No path is named in the refusal, in keeping with the rest of this module.

    Returns:
        The measured free bytes, when they meet the floor.

    Raises:
        SingleSourceCanaryError: less than :data:`PRE_F2_MINIMUM_FREE_BYTES` is free.
    """
    free = shutil.disk_usage(directory).free
    if free < PRE_F2_MINIMUM_FREE_BYTES:
        message = (
            f"pre-F2 free-space admission failed: {free} bytes free on the run volume, below "
            f"the required minimum of {PRE_F2_MINIMUM_FREE_BYTES} bytes "
            f"({PRE_F2_MINIMUM_FREE_BYTES // 1024**3} GiB); F2 was refused before its single "
            "transaction opened, so the association projection never began"
        )
        raise SingleSourceCanaryError(message)
    return free


def _materialize(
    *,
    working: WorkingCatalog,
    tree: DataTree,
    selected: SelectedPlannedSource,
    sidecar: CompactEvidenceSidecar,
    batch_size: int,
    observe: _PhaseObserver | None = None,
    capacity_guard: Callable[[], None] | None = None,
) -> _Materialized:
    """Parse one source, resolve, and project -- all inside the accepted write containment.

    The catalog is constructed with :data:`COMPACT_EVIDENCE` **here**, explicitly, and is the
    only ``CensusCatalog`` this path builds. That is what accepted Decision 116 §5 item 7 asks
    for: the compact contract is bound by the caller rather than inherited, so the
    full-observation default is unreachable by omission rather than merely unlikely.

    The run-local progress ledger records the D111 states truthfully around the parse: the
    source is ``in_progress`` before its first durable row, ``parsed`` once every row it implies
    is durable, and ``disposed`` only once the accepted terminal is known.
    """
    writer = _WorkingCatalogWriter(working)
    connection = working.connection
    catalog = CensusCatalog(writer, compact_evidence=COMPACT_EVIDENCE)
    source = selected.source
    with write_containment(connection):
        working.ledger.begin_source(source.source_instance_id, source.source_id)
        outcome = materialize_one_planned_source(
            writer=writer,
            tree=tree,
            catalog=catalog,
            selected=selected,
            sidecar=sidecar,
            batch_size=batch_size,
            checkpoint_batches=True,
        )
        working.ledger.mark_parsed(
            source.source_instance_id,
            parts=outcome.members,
            batches=outcome.outcome.parsed_records,
        )
        if observe is not None:
            # F0 has produced every durable row the source implies; F1 has not begun. The two
            # labels are recorded separately rather than folded, because the gap between them
            # is where a projection-sized allocation would first become visible.
            observe("POST_F0")
            observe("PRE_F1")
        # Decision 094 §6.4 order, unchanged: every persisted accession is resolved first,
        # because §6.2 item 5 reads the resolver's own output, and only then is the canonical
        # association relation projected.
        catalog.count_persisted_accession_resolutions(
            batch_size=batch_size, checkpoint_batches=True
        )
        # Accepted Decision 126 §7 (D126-R6) places the admission gate exactly here, between
        # F1's return and F2's call: this is the only point at which the measurement and the
        # transaction it admits cannot be separated by a race. Decision 137 (D137-R5) raised the
        # floor the gate compares against; it did not move the gate.
        if observe is not None:
            observe("POST_F1_PRE_F2")
        _require_pre_f2_free_space(working.path.parent)
        # Decision 138 (D138-R8, D138-R9): the pre-F2 gate says what must be true before the
        # transaction opens and says nothing about what happens inside it. `capacity_guard` is
        # sampled from F2's own innermost loop, so a floor reached mid-projection aborts from
        # within the open transaction and rolls it back. `None` on every unprotected path.
        totality = materialize_census_associations(
            connection, compact_evidence=True, capacity_guard=capacity_guard
        )
        if observe is not None:
            observe("POST_F2")
        counts = _counts(connection)
    working.ledger.mark_disposed(
        source.source_instance_id,
        outcome.outcome.disposition,
        detail=outcome.outcome.parser_state_after,
    )
    return _Materialized(
        outcome=outcome,
        totality=totality,
        counts=counts,
        resolution=catalog.resolution_evidence,
    )


def _record_evidence(
    *, sidecar: CompactEvidenceSidecar, materialized: _Materialized
) -> Mapping[str, str]:
    """Write the D113 §§8-9 evidence into the sidecar and return the five accepted identities.

    The resolution evidence is read off the catalog's accumulated
    :class:`~disclosure_drift.sec.census.ResolutionEvidence`, which is built under both evidence
    contracts because its digest is over the **logical** resolution set. Corroboration evidence
    exists only for a ``company.idx`` quarter; for any other source there is nothing to
    corroborate, so the digest is truthfully empty rather than fabricated.
    """
    resolution = materialized.resolution
    sidecar.record_resolution(
        resolution_scope=CANARY_RESOLUTION_SCOPE,
        accessions=resolution.accessions,
        implicit_resolutions=resolution.implicit,
        explicit_resolutions=resolution.explicit,
        omitted_field_rows=resolution.omitted_field_rows,
        materialized_field_rows=resolution.materialized_field_rows,
        omitted_cohort_rows=resolution.omitted_cohort_rows,
        materialized_cohort_rows=resolution.materialized_cohort_rows,
        completeness_digest=resolution.completeness_digest(),
    )
    outcome = materialized.outcome
    corroboration = outcome.corroboration
    observation = outcome.observation
    if corroboration is not None and observation is not None:
        sidecar.record_corroboration(
            source_observation_id=observation.observation_id,
            source_id=observation.source_id,
            artifact_sha256=observation.logical_sha256 or "",
            index_rows=corroboration.index_rows,
            corroborating=corroboration.corroborating,
            exceptions=corroboration.exceptions,
            unbound=len(corroboration.unbound),
            omitted_observations=corroboration.omitted_observations,
            materialized_observations=corroboration.written,
            corroboration_digest=corroboration.digest,
        )
    manifest = (
        "" if observation is None else sidecar.member_manifest_digest(observation.observation_id)
    )
    return {
        "member_manifest_digest": manifest,
        "projection_digest": outcome.completeness_digest,
        "resolution_digest": resolution.completeness_digest(),
        "corroboration_digest": "" if corroboration is None else corroboration.digest,
        "compact_evidence_identity": sidecar.identity(),
    }


def _result(
    *,
    world: CanaryWorld,
    started: str,
    selected: SelectedPlannedSource,
    fingerprint: str,
    materialized: _Materialized,
    identities: Mapping[str, str],
    working_sha256: str,
    working_bytes: int,
    wal_bytes: int,
    source_sha256: str,
    migration_head: int,
    catalog_before: str,
    catalog_after: str,
    free_before: int,
    free_after: int,
    capacity_observations: tuple[CapacityObservation, ...] = (),
) -> CanaryResult:
    """Assemble the accepted Decision 116 §9 result surface from measured values only."""
    outcome = materialized.outcome
    observation = outcome.observation
    corroboration = materialized.outcome.corroboration
    resolution = materialized.resolution
    return CanaryResult(
        contract=CANARY_CONTRACT,
        evidence_contract=COMPACT_EVIDENCE_CONTRACT,
        run_id=world.run_id,
        started_at_utc=started,
        completed_at_utc=utc_now(),
        source_instance_id=selected.source.source_instance_id,
        source_id=selected.source.source_id,
        plan_position=selected.plan_position,
        plan_source_count=selected.plan_source_count,
        plan_fingerprint=fingerprint,
        source_observation_id=None if observation is None else observation.observation_id,
        source_artifact_sha256="" if observation is None else (observation.logical_sha256 or ""),
        source_artifact_byte_length=(
            0 if observation is None else int(observation.content_size_bytes or 0)
        ),
        disposition=outcome.outcome.disposition,
        parser_state_before=outcome.outcome.parser_state_before,
        parser_state_after=outcome.outcome.parser_state_after,
        parser_run_id=outcome.outcome.parser_run_id,
        members=outcome.members,
        projection_records=outcome.records,
        parsed_records=outcome.outcome.parsed_records,
        quarantined_records=outcome.outcome.quarantined_records,
        omitted_field_observations=outcome.omitted_field_observations,
        materialized_field_observations=outcome.materialized_field_observations,
        canonical_accession_count=materialized.counts["canonical_accession_count"],
        registrant_count=materialized.counts["registrant_count"],
        substantive_relation_count=materialized.counts["substantive_relation_count"],
        quarantined_record_count=materialized.counts["quarantined_record_count"],
        structural_observation_count=materialized.counts["structural_observation_count"],
        accession_observation_count=materialized.counts["accession_observation_count"],
        field_resolution_row_count=materialized.counts["field_resolution_row_count"],
        cohort_resolution_row_count=materialized.counts["cohort_resolution_row_count"],
        association_totality=materialized.totality.as_record(),
        resolution_accessions=resolution.accessions,
        implicit_resolutions=resolution.implicit,
        explicit_resolutions=resolution.explicit,
        omitted_field_rows=resolution.omitted_field_rows,
        materialized_field_rows=resolution.materialized_field_rows,
        omitted_cohort_rows=resolution.omitted_cohort_rows,
        materialized_cohort_rows=resolution.materialized_cohort_rows,
        index_rows=0 if corroboration is None else corroboration.index_rows,
        corroborating_rows=0 if corroboration is None else corroboration.corroborating,
        corroboration_exceptions=0 if corroboration is None else corroboration.exceptions,
        unbound_accessions=0 if corroboration is None else len(corroboration.unbound),
        omitted_corroboration_observations=(
            0 if corroboration is None else corroboration.omitted_observations
        ),
        member_manifest_digest=identities["member_manifest_digest"],
        projection_digest=identities["projection_digest"],
        resolution_digest=identities["resolution_digest"],
        corroboration_digest=identities["corroboration_digest"],
        compact_evidence_identity=identities["compact_evidence_identity"],
        world_relative_working_catalog=WORKING_CATALOG_FILENAME,
        world_relative_sidecar=COMPACT_EVIDENCE_SIDECAR_FILENAME,
        working_catalog_sha256=working_sha256,
        working_catalog_byte_length=working_bytes,
        working_catalog_wal_byte_length=wal_bytes,
        working_catalog_source_sha256=source_sha256,
        migration_head=migration_head,
        operational_catalog_sha256_before=catalog_before,
        operational_catalog_sha256_after=catalog_after,
        work_root_free_bytes_before=free_before,
        work_root_free_bytes_after=free_after,
        capacity_observations=tuple(
            observation.as_record() for observation in capacity_observations
        ),
    )


# --------------------------------------------------------------------------- #
# The bounded diagnostic prefix
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CanaryPrefixResult:
    """What one bounded diagnostic member prefix measured. **Not a canary result.**

    Accepted **Decision 119 §8**. It is a separate type from :class:`CanaryResult`, written to a
    separate filename, and carrying a separate classification, because the one thing a prefix
    must never be is mistakable for a finished source. Read the field list for what is absent:
    there is no ``disposition``, no ``member_manifest_digest``, no ``projection_digest``, no
    ``resolution_digest``, no ``corroboration_digest``, and no ``compact_evidence_identity``.
    A prefix reached none of them, so it reports none of them, and no accepted complete-source
    identity can be synthesized from this document.

    What it does carry is measurement: how far the traversal got, what that cost, and enough
    durable state to tell a reader that the source was **not** finalized.
    """

    contract: str
    #: Always :data:`~disclosure_drift.m3.offline_parse.DIAGNOSTIC_PREFIX_CLASSIFICATION`.
    classification: str
    evidence_contract: str
    run_id: str
    started_at_utc: str
    completed_at_utc: str

    # -- the one source -------------------------------------------------- #
    source_instance_id: str
    source_id: str
    plan_position: int
    plan_source_count: int
    plan_fingerprint: str
    source_observation_id: str
    source_artifact_sha256: str
    source_artifact_byte_length: int

    # -- how far the traversal got --------------------------------------- #
    requested_member_limit: int
    members_processed: int
    #: The manifest ordinals actually recorded, which for a prefix of ``n`` members are
    #: ``0`` and ``n - 1``. ``-1`` in both when no member was recorded.
    member_ordinal_first: int
    member_ordinal_last: int
    recorded_member_count: int
    #: Payload bytes those members represent, summed from the manifest rows the traversal
    #: already wrote. Not re-read from the archive: this is the cost that was actually paid.
    member_payload_byte_length: int
    parsed_accession_count: int
    parsed_records: int
    omitted_field_observations: int
    materialized_field_observations: int

    # -- what is durable in the working catalog -------------------------- #
    #: Durable counts are read **after** the stop, so they are what survived the accepted
    #: batch semantics rather than what the traversal handed to them. A prefix that ends
    #: between two commit boundaries loses its open batch, exactly as any interruption does,
    #: so ``durable_*`` can legitimately trail ``members_processed``.
    durable_canonical_accession_count: int
    durable_parsed_record_count: int
    durable_accession_observation_count: int
    durable_parser_run_count: int
    #: Must be ``0``. A parser run that claimed a terminal would be a partial source wearing
    #: a success, which is exactly what the accepted interruption semantics prevent.
    durable_parser_runs_claiming_completion: int

    # -- proof that the source was not finalized ------------------------- #
    parser_state_before: str
    parser_state_after: str
    source_finalized: bool
    run_local_progress_state: str

    # -- the execution parameters ---------------------------------------- #
    batch_size: int
    working_catalog_cache_bytes: int | None
    working_catalog_cache_size_pragma: int | None
    #: What the writable working connection **reported**, read back from SQLite itself.
    working_catalog_effective_cache_size_pragma: int

    # -- the disposable world -------------------------------------------- #
    world_relative_working_catalog: str
    world_relative_sidecar: str
    working_catalog_byte_length: int
    working_catalog_wal_byte_length: int
    compact_sidecar_byte_length: int
    migration_head: int

    # -- the accepted catalog, before and after -------------------------- #
    operational_catalog_sha256_before: str
    operational_catalog_sha256_after: str
    work_root_free_bytes_before: int
    work_root_free_bytes_after: int

    @property
    def operational_catalog_unchanged(self) -> bool:
        """Whether the accepted catalog is byte-identical to what the profile started from."""
        return self.operational_catalog_sha256_before == self.operational_catalog_sha256_after

    def as_record(self) -> Mapping[str, object]:
        """The complete measurement as a plain mapping, carrying no absolute path."""
        record: dict[str, object] = {}
        for name in self.__slots__:
            record[name] = getattr(self, name)
        record["operational_catalog_unchanged"] = self.operational_catalog_unchanged
        return record


def _durable_prefix_counts(connection: sqlite3.Connection) -> Mapping[str, int]:
    """Row counts a prefix reports, read from the working catalog after it stopped."""
    tables = {
        "durable_canonical_accession_count": "census_accessions",
        "durable_parsed_record_count": "census_parsed_records",
        "durable_accession_observation_count": "census_accession_observations",
        "durable_parser_run_count": "census_parser_runs",
    }
    counted = {
        key: int(
            connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]  # noqa: S608
        )
        for key, table in tables.items()
    }
    counted["durable_parser_runs_claiming_completion"] = int(
        connection.execute(
            "SELECT COUNT(*) AS n FROM census_parser_runs WHERE outcome <> 'failed'"
        ).fetchone()["n"]
    )
    return counted


def _durable_parser_state(connection: sqlite3.Connection, selected: SelectedPlannedSource) -> str:
    """The plan row's ``parser_state`` as it stands in the working catalog after the stop."""
    row = connection.execute(
        "SELECT parser_state FROM census_plan_sources WHERE census_run_id = ? "
        "AND source_instance_id = ?",
        (selected.source.census_run_id, selected.source.source_instance_id),
    ).fetchone()
    if row is None:  # pragma: no cover - the row was read from this very catalog's copy
        message = "the planned source vanished from the working catalog between copy and read"
        raise SingleSourceCanaryError(message)
    return str(row["parser_state"])


def _recorded_members(sidecar_path: Path, observation_id: str) -> Mapping[str, int]:
    """Aggregate the manifest rows the prefix wrote, read-only, once, after the traversal.

    Deliberately one aggregate over rows that already exist rather than any measurement taken
    inside the hot loop: accepted **Decision 119 §8** puts per-record instrumentation outside
    this path, and a prefix that paid to measure itself would not be measuring the accepted
    path any more.
    """
    connection = sqlite3.connect(f"{sidecar_path.absolute().as_uri()}?mode=ro", uri=True)
    try:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT COUNT(*) AS members, "
            "COALESCE(SUM(payload_byte_length), 0) AS payload_bytes, "
            "COALESCE(SUM(parsed_accessions), 0) AS accessions, "
            "COALESCE(MIN(member_ordinal), -1) AS first_ordinal, "
            "COALESCE(MAX(member_ordinal), -1) AS last_ordinal "
            "FROM compact_source_members WHERE source_observation_id = ?",
            (observation_id,),
        ).fetchone()
    finally:
        connection.close()
    return {
        "members": int(row["members"]),
        "payload_bytes": int(row["payload_bytes"]),
        "accessions": int(row["accessions"]),
        "first_ordinal": int(row["first_ordinal"]),
        "last_ordinal": int(row["last_ordinal"]),
    }


def run_single_source_prefix_profile(
    *,
    operational_catalog: Path,
    tree: DataTree,
    work_root: Path,
    run_id: str,
    source_instance_id: str,
    member_limit: int,
    batch_size: int = CANARY_BATCH_SIZE,
    cache_bytes: int | None = WORKING_CATALOG_CACHE_BYTES,
    require_volume_uuid: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> CanaryPrefixResult:
    """Materialize the **first ``member_limit`` members** of one source, and stop. Diagnostic.

    Accepted **Decision 119 §6**. Every boundary :func:`run_single_source_canary` establishes is
    established here identically and through the same primitives -- the work root is refused
    unless it lies outside both the checkout and the authoritative evidence tree, the accepted
    catalog is opened strictly read-only on every path with no writer lease, the world is
    create-once, the D111 working catalog carries every write, and the compact contract is bound
    explicitly. The differences are that it stops after a bounded number of members and that it
    finalizes nothing.

    **It can never produce a canary success.** There is no path from here to a source
    disposition, to the catalog-wide resolution pass, to the Decision 094 §6.4 association
    projection, to a source-level compact evidence row, or to any of the five accepted
    identities. The run-local progress ledger is left recording ``in_progress``, which is the
    truth, and the result document is written under its own name with its own classification.

    Args:
        operational_catalog: The accepted catalog. Opened strictly read-only, always.
        tree: The data tree the frozen source artifacts are read from.
        work_root: The disposable work root, validated here before any world exists.
        run_id: This world's identity. Create-once.
        source_instance_id: The one planned source's own plan key.
        member_limit: How many governed members to traverse. Must be positive.
        batch_size: Parts per real transaction, defaulting to the accepted D113 §14 value.
        cache_bytes: The page-cache budget for the run-local writable working catalog.
        require_volume_uuid: An optional assertion, exactly as
            :func:`run_single_source_canary` takes it. The envelope itself is **mandatory for an
            external root here too** (D138-R1), so a diagnostic prefix cannot reach a volume the
            complete-source run would have refused, with or without the assertion. It records
            **no** phase-boundary capacity evidence: D137-R7 scopes that to a complete-source
            run, and this one finalizes nothing.
        environ: The environment ``SQLITE_TMPDIR`` is read from. Defaults to the process's own.

    Raises:
        SingleSourceCanaryError: a canary precondition failed, or the bound is not positive.
        ExternalWorkingRootError: an external volume was required and a D137 guard did not hold.
        OfflineParseError: any accepted fail-closed parse condition, unchanged.
        WorkingCatalogError: the disposable working catalog could not be built safely.
    """
    if member_limit <= 0:
        message = (
            f"a diagnostic prefix needs a positive --member-limit; got {member_limit}. There "
            "is no unbounded prefix: a complete source is what --mode run is for"
        )
        raise SingleSourceCanaryError(message)
    resolved_work_root = require_canary_work_root(work_root, tree=tree)
    require_external_envelope(
        resolved_work_root,
        observed_at=utc_now(),
        environ=environ,
        asserted_uuid=require_volume_uuid,
    )
    started = utc_now()
    if not operational_catalog.is_file():
        message = "the accepted operational catalog does not exist at its fixed relative path"
        raise SingleSourceCanaryError(message)
    catalog_before, _ = file_digest(operational_catalog)
    free_before = shutil.disk_usage(_measurable(resolved_work_root)).free

    with strictly_read_only_connection(operational_catalog) as reader:
        selected = select_planned_source(reader, source_instance_id)
        fingerprint, _ = plan_fingerprint(reader)

    world = create_world(resolved_work_root, run_id)

    with WorkingCatalog(operational_catalog, world.directory, cache_bytes=cache_bytes) as working:
        connection = working.connection
        sidecar = CompactEvidenceSidecar(world.sidecar)
        try:
            writer = _WorkingCatalogWriter(working)
            catalog = CensusCatalog(writer, compact_evidence=COMPACT_EVIDENCE)
            with write_containment(connection):
                working.ledger.begin_source(
                    selected.source.source_instance_id, selected.source.source_id
                )
                outcome = materialize_planned_source_prefix(
                    writer=writer,
                    tree=tree,
                    catalog=catalog,
                    selected=selected,
                    max_members=member_limit,
                    sidecar=sidecar,
                    batch_size=batch_size,
                    checkpoint_batches=True,
                )
            # Nothing between the stop and here advances the source: the ledger is left
            # ``in_progress``, and every statement below reads.
            counts = _durable_prefix_counts(connection)
            parser_state_after = _durable_parser_state(connection, selected)
            progress = working.ledger.progress(selected.source.source_instance_id)
            effective_cache = working.effective_cache_size_pragma
            requested_cache = working.requested_cache_bytes
            requested_cache_pragma = working.requested_cache_size_pragma
            migration_head = working.identity.migration_head
            working.checkpoint()
            wal_bytes = working.wal_byte_length()
        finally:
            sidecar.close()

    recorded = _recorded_members(world.sidecar, outcome.observation.observation_id)
    result = CanaryPrefixResult(
        contract=CANARY_CONTRACT,
        classification=DIAGNOSTIC_PREFIX_CLASSIFICATION,
        evidence_contract=COMPACT_EVIDENCE_CONTRACT,
        run_id=world.run_id,
        started_at_utc=started,
        completed_at_utc=utc_now(),
        source_instance_id=selected.source.source_instance_id,
        source_id=selected.source.source_id,
        plan_position=selected.plan_position,
        plan_source_count=selected.plan_source_count,
        plan_fingerprint=fingerprint,
        source_observation_id=outcome.observation.observation_id,
        source_artifact_sha256=outcome.observation.logical_sha256 or "",
        source_artifact_byte_length=int(outcome.observation.content_size_bytes or 0),
        requested_member_limit=outcome.requested_member_limit,
        members_processed=outcome.members_processed,
        member_ordinal_first=recorded["first_ordinal"],
        member_ordinal_last=recorded["last_ordinal"],
        recorded_member_count=recorded["members"],
        member_payload_byte_length=recorded["payload_bytes"],
        parsed_accession_count=recorded["accessions"],
        parsed_records=outcome.records,
        omitted_field_observations=outcome.omitted_field_observations,
        materialized_field_observations=outcome.materialized_field_observations,
        durable_canonical_accession_count=counts["durable_canonical_accession_count"],
        durable_parsed_record_count=counts["durable_parsed_record_count"],
        durable_accession_observation_count=counts["durable_accession_observation_count"],
        durable_parser_run_count=counts["durable_parser_run_count"],
        durable_parser_runs_claiming_completion=counts["durable_parser_runs_claiming_completion"],
        parser_state_before=selected.source.parser_state,
        parser_state_after=parser_state_after,
        source_finalized=outcome.source_finalized,
        run_local_progress_state="absent" if progress is None else progress.state,
        batch_size=batch_size,
        working_catalog_cache_bytes=requested_cache,
        working_catalog_cache_size_pragma=requested_cache_pragma,
        working_catalog_effective_cache_size_pragma=effective_cache,
        world_relative_working_catalog=WORKING_CATALOG_FILENAME,
        world_relative_sidecar=COMPACT_EVIDENCE_SIDECAR_FILENAME,
        working_catalog_byte_length=world.working_catalog.stat().st_size,
        working_catalog_wal_byte_length=wal_bytes,
        compact_sidecar_byte_length=world.sidecar.stat().st_size,
        migration_head=migration_head,
        operational_catalog_sha256_before=catalog_before,
        operational_catalog_sha256_after=file_digest(operational_catalog)[0],
        work_root_free_bytes_before=free_before,
        work_root_free_bytes_after=shutil.disk_usage(world.directory).free,
    )
    _write_once(
        world.prefix_result, json.dumps(result.as_record(), indent=2, sort_keys=True).encode()
    )
    return result


# --------------------------------------------------------------------------- #
# The operator surface
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CanaryOperatorResult:
    """One rendered operator outcome: an exit code and the lines to print.

    Deliberately its own small type rather than the E0 operator result: this path shares no
    authority, no namespace, and no terminal schema with E0, and reusing E0's rendering type
    would be the first thread of exactly the coupling accepted Decision 116 §5 item 13 forbids.
    """

    exit_code: int
    lines: tuple[str, ...]


def run_canary_source_command(
    *,
    mode: str,
    run_id: str,
    source_instance_id: str,
    work_root: str,
    repository_root: Path,
    environ: Mapping[str, str] | None = None,
    member_limit: int | None = None,
    require_volume_uuid: str | None = None,
) -> CanaryOperatorResult:
    """Run one ``m3 canary-source`` invocation and render it.

    Routing, boundary resolution, and rendering only. Every predicate, identity, and durable
    write lives above, so the operator surface cannot become a second place where a canary is
    judged runnable.

    The work root is refused here early, so an operator learns immediately and without a
    stack trace, and it is refused again by :func:`run_single_source_canary` itself. That is
    deliberate redundancy through **one** primitive rather than two rules: this refusal is a
    convenience, and the run's own is the invariant.

    No line this returns carries the private root, the work root, or any absolute path: the
    result is rendered from counts, digests, enum tokens, and world-relative names.

    **The member limit belongs to exactly one mode.** ``profile-prefix`` requires a positive
    one; ``preflight`` and ``run`` refuse one outright rather than ignoring it. That asymmetry
    is the point of accepted **Decision 119 §6**: ``run`` is the only mode that may establish a
    complete source, so it must not be reachable with a bound attached, not even a bound that
    would have been harmless.

    **The external-volume requirement is mandatory, not opt-in** (Decision 138, D138-R1). The
    resolved work root decides whether the envelope applies: a root on any volume other than the
    system one gets every Decision 137 launch guard whether or not ``--require-volume-uuid`` was
    typed, and the flag is an assertion that can only add a requirement, never remove one. That
    is the D137 independent review's MAJOR-1 closed: an operator could previously reach an
    unqualified disk, or the immutable D130 archive itself, simply by leaving the flag off. The
    requirement is established here so the operator learns immediately, and again inside the run
    -- the same deliberate redundancy through one primitive that the work root already uses. In
    ``preflight`` the guards are the whole point: the mode creates nothing, and its record
    carries what they established. **Passing a preflight is not an authorization to launch**
    (D137-R12); the corrected canary needs its own owner instrument.
    """
    limit = _validated_member_limit(mode, member_limit)
    private_root = resolve_private_root(repository_root, environ=environ)
    operational_catalog = private_root / OPERATIONAL_CATALOG_RELATIVE_PATH
    resolved_work_root = require_disposable_work_root(work_root, repository_root, private_root)
    external: ExternalCanaryPreflight | None = require_external_envelope(
        resolved_work_root,
        observed_at=utc_now(),
        environ=environ,
        asserted_uuid=require_volume_uuid,
    )
    if limit is not None:
        # ``profile-prefix`` is the only mode a bound can survive validation under, so this
        # branch is entered by the bound itself rather than by a second reading of the mode.
        prefix = run_single_source_prefix_profile(
            operational_catalog=operational_catalog,
            tree=DataTree.from_root(private_root),
            work_root=resolved_work_root,
            run_id=run_id,
            source_instance_id=source_instance_id,
            member_limit=limit,
            require_volume_uuid=require_volume_uuid,
            environ=environ,
        )
        return CanaryOperatorResult(
            exit_code=_EXIT_OK if prefix.operational_catalog_unchanged else _EXIT_GATE_FAILURE,
            lines=_render(prefix.as_record(), title="canary-source profile-prefix"),
        )
    if mode == "preflight":
        report = preflight_single_source_canary(
            operational_catalog=operational_catalog,
            work_root=resolved_work_root,
            run_id=run_id,
            source_instance_id=source_instance_id,
        )
        record = dict(report.as_record())
        if external is not None:
            record["external_volume"] = dict(external.as_record())
        return CanaryOperatorResult(
            exit_code=_EXIT_OK if report.world_absent else _EXIT_GATE_FAILURE,
            lines=_render(record, title="canary-source preflight"),
        )
    if mode != "run":
        message = (
            f"unknown canary mode {mode!r}; the modes are 'preflight', 'run', and 'profile-prefix'"
        )
        raise SingleSourceCanaryError(message)
    result = run_single_source_canary(
        operational_catalog=operational_catalog,
        tree=DataTree.from_root(private_root),
        work_root=resolved_work_root,
        run_id=run_id,
        source_instance_id=source_instance_id,
        require_volume_uuid=require_volume_uuid,
        environ=environ,
    )
    return CanaryOperatorResult(
        exit_code=_EXIT_OK if result.operational_catalog_unchanged else _EXIT_GATE_FAILURE,
        lines=_render(result.as_record(), title="canary-source run"),
    )


def _validated_member_limit(mode: str, member_limit: int | None) -> int | None:
    """Return the bound ``mode`` may run under: a positive one, or ``None`` for every other mode.

    Refusing a bound anywhere but the diagnostic prefix is what keeps ``run`` complete-source
    only, and returning the validated bound rather than merely checking it is what keeps the
    caller from having to read the mode a second time.

    Raises:
        SingleSourceCanaryError: the mode and the bound do not belong together.
    """
    if mode == "profile-prefix":
        if member_limit is None:
            message = (
                "canary mode 'profile-prefix' requires an explicit positive --member-limit; "
                "it has no default, because a prefix with no bound is a whole source"
            )
            raise SingleSourceCanaryError(message)
        if member_limit <= 0:
            message = (
                f"--member-limit must be positive; got {member_limit}. Zero and negative "
                "bounds are refused rather than read as 'every member'"
            )
            raise SingleSourceCanaryError(message)
        return member_limit
    if member_limit is not None:
        message = (
            f"canary mode {mode!r} takes no --member-limit; only 'profile-prefix' is bounded, "
            "and 'run' is complete-source-only so that it alone can establish a real source"
        )
        raise SingleSourceCanaryError(message)
    return None


def _render(record: Mapping[str, object], *, title: str) -> tuple[str, ...]:
    """Render one result mapping as aligned ``key  value`` lines, in key order."""
    width = max(len(key) for key in record)
    body = (f"{key:<{width}}  {json.dumps(record[key], sort_keys=True)}" for key in sorted(record))
    return (title, *body)
