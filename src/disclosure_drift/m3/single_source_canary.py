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

import disclosure_drift
from disclosure_drift.config import EVIDENCE_ROOT_ENV
from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.canary_phases import (
    CANARY_PHASE_SEQUENCE,
    PHASE_F0,
    PHASE_F1,
    PHASE_F2,
    PHASE_RESTART_CONTRACT,
    PHASE_STATUS_COMPLETE,
    PHASE_SUCCESSOR,
    PhaseCheckpoint,
    execution_identity,
    read_phase_checkpoint,
    require_phase_admission,
    stored_int,
    validate_phase,
    write_phase_checkpoint,
)
from disclosure_drift.m3.canary_runtime import (
    acquire_canary_execution_lock,
    process_is_live_canary,
    process_peak_resident_bytes,
)
from disclosure_drift.m3.capacity_plan import plan_fingerprint
from disclosure_drift.m3.compact_evidence import (
    COMPACT_EVIDENCE,
    COMPACT_EVIDENCE_CONTRACT,
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    CompactEvidenceSidecar,
)
from disclosure_drift.m3.dock_transport import TRANSPORT_DOCK
from disclosure_drift.m3.evidence_paths import require_external_evidence_root
from disclosure_drift.m3.external_working_root import (
    F2_ALERT_FREE_BYTES,
    F2_HARD_FLOOR_FREE_BYTES,
    LAUNCH_MINIMUM_FREE_BYTES,
    POST_F0_MINIMUM_FREE_BYTES,
    PRE_F1_MINIMUM_FREE_BYTES,
    QUALIFIED_EXTERNAL_VOLUME_UUID,
    CapacityObservation,
    ExternalCanaryPreflight,
    F2CapacityGuard,
    observe_capacity,
    require_external_envelope,
    require_phase_free_space,
)
from disclosure_drift.m3.offline_parse import (
    DIAGNOSTIC_PREFIX_CLASSIFICATION,
    STREAMED_SOURCE_IDS,
    AssociationTotality,
    FullIndexCorroboration,
    SelectedPlannedSource,
    SingleSourceOutcome,
    StructuralSourcePreflight,
    materialize_census_associations,
    materialize_one_planned_source,
    materialize_planned_source_prefix,
    planned_source_observation,
    require_sound_parent_map,
    select_planned_source,
    structural_source_preflight,
    write_containment,
)
from disclosure_drift.m3.repository_identity import (
    RepositoryIdentity,
    require_clean_running_repository,
)
from disclosure_drift.m3.working_catalog import (
    PROGRESS_LEDGER_FILENAME,
    WORKING_CATALOG_FILENAME,
    RunProgressLedger,
    WorkingCatalog,
    cache_size_pragma,
    file_digest,
)
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.census import CensusCatalog, ResolutionEvidence
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.storage.catalog import CatalogWriter, strictly_read_only_connection
from disclosure_drift.storage.sqlite import applied_versions, utc_now

__all__ = [
    "CANARY_BATCH_SIZE",
    "CANARY_CONTRACT",
    "CANARY_PHASE_MODES",
    "PHASE_ADMISSION_FLOOR",
    "CANARY_PREFIX_RESULT_FILENAME",
    "CANARY_RESULT_FILENAME",
    "CANARY_RESOLUTION_SCOPE",
    "FIRST_CANARY_REQUIRED_TRANSPORT",
    "OPERATIONAL_CATALOG_RELATIVE_PATH",
    "PRE_F2_MINIMUM_FREE_BYTES",
    "WORKING_CATALOG_CACHE_BYTES",
    "WORKING_CATALOG_CACHE_SIZE_PRAGMA",
    "CanaryPhaseResult",
    "CanaryPrefixResult",
    "CanaryPreflight",
    "CanaryResult",
    "CanaryWorld",
    "SingleSourceCanaryError",
    "attach_world",
    "create_world",
    "phase_execution_identity",
    "preflight_single_source_canary",
    "run_single_source_canary_phase",
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

#: The **one** transport every production first-canary path narrows the external working-root
#: envelope to: ``USB_VIA_THUNDERBOLT_DOCK``.
#:
#: **The selection is accepted Decision 142 §4 (D142-R2); the enforcement is Decision 144
#: (D144-R1).** Decision 141 built the narrowing mechanism and deliberately left it unused:
#: §16 (D141-R8) recognized two qualified topologies, refused a third, and said the choice of
#: *one* for the real canary was the owner's to make. Decision 142 made it. What the D143
#: independent review then found (MAJOR-1) is that the selection lived only in prose --
#: ``required_transport`` defaulted to ``None`` at all three production seams, which
#: :func:`~disclosure_drift.m3.dock_transport.require_qualified_transport` documents as
#: admitting *either* qualified topology. The whole envelope passed over a directly attached
#: qualified SSD, which is the operator fallback accepted Decision 142 §6 forbids in terms.
#:
#: **It is a module constant and deliberately not an operator input.** There is no CLI flag, no
#: configuration key, and no environment variable that supplies, widens, or disables it, and
#: none may be added: a selection an operator can retype under a refusal is the fallback D142 §6
#: rules out. Changing it is a reviewed source change against a later owner decision.
#:
#: **It narrows and never widens.** ``required_transport`` is checked *after* the observed class
#: has already had to be one of
#: :data:`~disclosure_drift.m3.dock_transport.QUALIFIED_TRANSPORT_CLASSES`, so this constant can
#: only ever turn an admission into a refusal. Every other guard -- the mandatory Volume UUID,
#: AC power and lid, D130 isolation, the archive precheck, the capacity floors, and
#: ``SQLITE_TMPDIR`` placement -- is untouched by it.
#:
#: **:data:`~disclosure_drift.m3.dock_transport.TRANSPORT_DIRECT` is not revoked** (D141-R8, and
#: D142 §5 restating it). It remains a separately qualified class, the library entry points
#: still admit it when nothing narrower is demanded, and a third topology still refuses. What is
#: narrowed is this repository's *first-canary* production envelope, and nothing else.
FIRST_CANARY_REQUIRED_TRANSPORT: Final = TRANSPORT_DOCK

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
#: Accepted **Decision 126 §7** (D126-R6) records why it has to live here rather than in a launch
#: wrapper or an external sampler, and **two of its four rationale sentences stopped describing
#: this architecture when Decision 145 split the run into three processes**. They are separated
#: from the binding invariant below rather than quietly dropped -- D146-MINOR-2 and D146-OBS-5,
#: corrected by Decision 147. **Decision 126 itself is not rewritten**: it recorded what was true
#: of the whole-run shape it governed, and its requirement is untouched.
#:
#: **HISTORICAL -- true of the pre-Decision-145 whole-run shape, and no longer true.** *"F1
#: returns and F2 begins in consecutive statements, so there is no window an outside process can
#: occupy"*: on the phased path there IS a window -- F1's process exits and F2's process starts.
#: *"Nothing durable changes at the boundary, so an observer cannot tell 'F1 finished' from 'F2
#: is about to open' by reading state"*: F1 now writes a durable terminal checkpoint, and reading
#: it is exactly how a successor tells those two states apart. Both sentences remain true of the
#: surviving whole-run path, where F1 and F2 still occur in consecutive statements.
#:
#: **CURRENT AND BINDING -- unchanged by Decision 145, and the reasons that carry D126-R6.** A
#: signal from outside is advisory where admission has to be dispositive; and free space sampled
#: at any instant before the call describes a different instant than the one that matters.
#: Tightening a sampler's cadence shrinks that race and never closes it. **Only the path that is
#: about to open the transaction can decline to open it** -- so the dispositive gate runs inside
#: the process that opens F2's transaction, immediately before it opens, on both paths. The
#: phased path takes it in :func:`_phase_f2_body`, inside F2's own ``write_containment`` and one
#: statement before ``_f2``; the whole-run path takes it in ``_materialize`` between F1's return
#: and F2's call. Neither the gate, its placement, nor its `50` GiB value moved.
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


def create_world(
    work_root: Path, run_id: str, *, require_existing_root: bool = False
) -> CanaryWorld:
    """Create one disposable world exactly once, at mode ``0700``.

    ``mkdir`` without ``exist_ok`` is the create-once primitive: it is atomic, so two callers
    cannot both believe they created the world, and an identity whose world already exists is
    refused rather than resumed, repaired, or overwritten. A symlink at either the work root or
    the world path is refused before anything is created.

    **``require_existing_root`` is the D140-R5 hardening**, and it is set for every run on the
    external volume. The D139 review's **MAJOR-1** included a race: the envelope authenticates
    the volume, and the world is created a moment later. If the volume disappears inside that
    gap, ``mkdir(parents=True)`` does not fail -- it **recreates the mount point** as an ordinary
    directory on the system root filesystem and builds the world inside it, and the run proceeds
    on internal storage. Nothing but ``/Volumes`` being root-owned stood in the way.

    With it set, the work root must **already exist**: only the final governed world directory is
    ever created, no parent is made, and a vanished volume produces a refusal rather than a
    freshly minted internal directory tree. The operator creates the work root during preflight,
    which the runbook already requires.

    Args:
        work_root: The disposable work root the world is created beneath.
        run_id: This world's identity. Create-once.
        require_existing_root: Refuse rather than create ``work_root`` and its parents.

    Raises:
        SingleSourceCanaryError: the identity is unlawful, its world already exists, or
            ``require_existing_root`` is set and the work root is not already a directory.
    """
    validate_run_id(run_id)
    if work_root.is_symlink():
        message = "the canary work root is a symbolic link and is refused"
        raise SingleSourceCanaryError(message)
    if require_existing_root and not work_root.is_dir():
        message = (
            "the canary work root does not exist as a directory on the authenticated external "
            "volume. It is NOT created here: creating it would recreate a mount point that has "
            "gone away, as an ordinary directory on the internal disk, and build the world "
            "inside it. The run is refused and nothing was created"
        )
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


# --------------------------------------------------------------------------- #
# Pre-world source authentication -- D140-R20 (MINOR-7) and D140-R21 (INFO-9/10)
# --------------------------------------------------------------------------- #
#: The accepted governed source artifact's SHA-256, from the frozen M3.2 inventory.
#:
#: **Identity is keyed on the digest, not on a name.** A source instance key is an operator- and
#: catalog-level identifier; the digest is the artifact. Keying the frozen expectations here on
#: the digest means they apply to exactly one file in the world and cannot be triggered by a
#: fixture that happens to share a naming convention.
GOVERNED_SOURCE_SHA256: Final = "c85744be921b0dc5be4e3c7dd44552fc0f57d354d61df38cd92a13926982b82f"

#: That artifact's accepted byte length.
GOVERNED_SOURCE_BYTE_LENGTH: Final = 1_556_847_020

#: The governed JSON member count the accepted structural facts record for it.
GOVERNED_SOURCE_MEMBERS: Final = 985_834

#: The historical shard member count the accepted structural facts record for it.
GOVERNED_SOURCE_HISTORICAL_SHARDS: Final = 5_337


@dataclass(frozen=True, slots=True)
class SourceAuthentication:
    """What the pre-world source check established. It creates nothing."""

    source_instance_id: str
    byte_length: int
    sha256: str
    governed_artifact: bool
    structural: StructuralSourcePreflight | None

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        record: dict[str, object] = {
            "source_instance_id": self.source_instance_id,
            "source_byte_length": self.byte_length,
            "source_sha256": self.sha256,
            "governed_artifact": self.governed_artifact,
        }
        record["structural"] = (
            None if self.structural is None else dict(self.structural.as_record())
        )
        return record


def preauthenticate_source(
    *,
    tree: DataTree,
    selected: SelectedPlannedSource,
    observation: SourceObservation | None,
    structural: bool = True,
) -> SourceAuthentication:
    """Prove the selected source is the artifact the catalog says it is -- **before** a world.

    The D139 review's **MINOR-7**: source integrity was verified by the parser, *during* F0 --
    which is after the disposable world exists, after the working catalog has been copied, and
    after the run has committed a world identity that is create-once and can never be reused. A
    source mismatch discovered there costs a run identity. Discovered here it costs nothing.

    Three things are established, in increasing strength:

    1. the artifact's **byte length** matches the observation the plan is bound to;
    2. its **SHA-256** matches that observation's recorded logical digest;
    3. when the artifact **is** the accepted governed source -- decided by that digest -- its
       frozen byte length, governed member count and historical shard count must all match, and
       its shard-to-parent structure must satisfy the accepted Decision 129 rule (D140-R21).

    **The parser's own verification is not weakened by this.** F0 re-reads and re-verifies the
    artifact through the same integrity-checking reader it always did; nothing here replaces
    that, and the second check is deliberately not skipped merely because a first one passed.

    Args:
        tree: The data tree the frozen source artifacts are read from.
        selected: The one source, from :func:`select_planned_source`.
        observation: The stored observation that source is bound to, from
            :func:`~disclosure_drift.m3.offline_parse.planned_source_observation`.
        structural: Whether to run the read-only structural preflight for a streamed source.

    Raises:
        SingleSourceCanaryError: the artifact is absent, or is not what the catalog records.
        OfflineParseError: the governed shard-to-parent structure is not sound.
    """
    bound = observation
    if bound is None or bound.relative_storage_path is None:
        message = (
            "the selected planned source is not bound to a stored artifact, so it cannot be "
            "authenticated before a world is created; the run is refused"
        )
        raise SingleSourceCanaryError(message)
    store = SnapshotStore(tree)
    store.adopt([bound])
    try:
        artifact = store.payload_path(bound)
        measured = artifact.stat().st_size
    except (OSError, DisclosureDriftError) as exc:
        message = (
            f"the selected source artifact could not be located or measured "
            f"({type(exc).__name__}); an unverifiable source is refused before a world exists"
        )
        raise SingleSourceCanaryError(message) from exc
    expected_bytes = bound.content_size_bytes
    if expected_bytes is not None and measured != expected_bytes:
        message = (
            f"the selected source artifact is {measured} bytes; the accepted observation "
            f"records {expected_bytes}. The source is refused BEFORE a world exists, so no "
            "disposable world and no create-once run identity were consumed"
        )
        raise SingleSourceCanaryError(message)
    digest, _ = file_digest(artifact)
    expected_digest = bound.logical_sha256
    if expected_digest is not None and digest != expected_digest:
        message = (
            "the selected source artifact's SHA-256 is not the digest the accepted observation "
            "records. The source is refused BEFORE a world exists; nothing was created, and "
            "the artifact is reported rather than re-recorded"
        )
        raise SingleSourceCanaryError(message)
    governed = digest == GOVERNED_SOURCE_SHA256
    if governed and measured != GOVERNED_SOURCE_BYTE_LENGTH:  # pragma: no cover - digest fixes it
        message = (
            f"the governed source artifact is {measured} bytes, not the accepted "
            f"{GOVERNED_SOURCE_BYTE_LENGTH}; the run is refused before a world exists"
        )
        raise SingleSourceCanaryError(message)
    proof: StructuralSourcePreflight | None = None
    if structural and bound.source_id in STREAMED_SOURCE_IDS:
        proof = require_sound_parent_map(structural_source_preflight(artifact))
        if governed and (
            proof.governed_members != GOVERNED_SOURCE_MEMBERS
            or proof.shard_members != GOVERNED_SOURCE_HISTORICAL_SHARDS
        ):
            message = (
                f"the governed source holds {proof.governed_members} members and "
                f"{proof.shard_members} historical shards; the accepted structural facts are "
                f"{GOVERNED_SOURCE_MEMBERS} and {GOVERNED_SOURCE_HISTORICAL_SHARDS}. The run is "
                "refused before a world exists rather than proceeding against a source whose "
                "shape is not the one the plan was built on"
            )
            raise SingleSourceCanaryError(message)
    return SourceAuthentication(
        source_instance_id=selected.source.source_instance_id,
        byte_length=measured,
        sha256=digest,
        governed_artifact=governed,
        structural=proof,
    )


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
    #    Decision 144 (D144-R1): and the envelope is narrowed to the ONE topology accepted
    #    Decision 142 §4 selected. The mechanism existed and no production caller supplied it,
    #    so the owner's selection was prose and a directly attached qualified SSD passed --
    #    including as the answer to a dock refusal, which D142 §6 forbids. There is no fallback
    #    here to take: the narrowing is a constant, and a refusal is a stop.
    external: ExternalCanaryPreflight | None = require_external_envelope(
        resolved_work_root,
        observed_at=utc_now(),
        environ=environ,
        asserted_uuid=require_volume_uuid,
        required_transport=FIRST_CANARY_REQUIRED_TRANSPORT,
    )
    started = utc_now()
    if not operational_catalog.is_file():
        message = "the accepted operational catalog does not exist at its fixed relative path"
        raise SingleSourceCanaryError(message)
    #    Decision 140 (D140-R16): at most ONE complete-source canary runs on this host, whatever
    #    its run identity. Two concurrent runs would each measure the same volume's free space as
    #    though they were alone on it, which makes every capacity floor in the envelope wrong in
    #    the one direction that matters. Taken before anything is measured or created, held for
    #    the whole run, and released by the operating system if this process dies.
    lock = acquire_canary_execution_lock(
        _private_root_of(operational_catalog), detail={"run_id": run_id, "mode": "run"}
    )
    try:
        return _run_locked(
            operational_catalog=operational_catalog,
            tree=tree,
            resolved_work_root=resolved_work_root,
            run_id=run_id,
            source_instance_id=source_instance_id,
            batch_size=batch_size,
            cache_bytes=cache_bytes,
            external=external,
            started=started,
        )
    finally:
        lock.release()


def _private_root_of(operational_catalog: Path) -> Path:
    """The private evidence root the accepted catalog sits under.

    Derived from the one fixed relative path the catalog is always at
    (:data:`OPERATIONAL_CATALOG_RELATIVE_PATH`), rather than taken as a second argument that a
    caller could disagree with the catalog about.
    """
    return operational_catalog.parent.parent


def _run_locked(
    *,
    operational_catalog: Path,
    tree: DataTree,
    resolved_work_root: Path,
    run_id: str,
    source_instance_id: str,
    batch_size: int,
    cache_bytes: int | None,
    external: ExternalCanaryPreflight | None,
    started: str,
) -> CanaryResult:
    """The run itself, with the host execution lock already held. See the caller."""
    catalog_before, _ = file_digest(operational_catalog)
    free_before = shutil.disk_usage(_measurable(resolved_work_root)).free

    # 1. The one source, and the plan it came from. Strictly read-only: this handle cannot
    #    write, and it is closed before the working copy is taken.
    with strictly_read_only_connection(operational_catalog) as reader:
        selected = select_planned_source(reader, source_instance_id)
        fingerprint, _ = plan_fingerprint(reader)
        observation = planned_source_observation(reader, selected)

    #    Decision 140 (D140-R20, D140-R21): the artifact is authenticated and its shard-to-parent
    #    structure is proved BEFORE a world exists. A source mismatch, or a parent map that F0
    #    would have refused twenty-seven hours in, costs nothing here -- no world, and no
    #    create-once run identity spent on a run that could never have finished.
    preauthenticate_source(tree=tree, selected=selected, observation=observation)

    # 2. The disposable world. Create-once, and never under the private evidence root.
    #    D140-R4: the volume is re-authenticated at the LAST safe point before the directory
    #    is created, so the gap between "the envelope held" and "the world exists" carries a
    #    check rather than an assumption. D140-R5: on the external path no parent is created,
    #    so a volume that vanished inside that gap cannot be silently replaced by a directory.
    if external is not None:
        external.admitted.reauthenticate()
    world = create_world(resolved_work_root, run_id, require_existing_root=external is not None)

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
            admitted=external.admitted,
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
    refusal lands **before** F2's single transaction opens rather than during it. That is true on
    both paths and is what accepted Decision 126 §7 (D126-R6) requires: the phased path calls it
    from :func:`_phase_f2_body`, **in the F2 process**, one statement before ``_f2``; the
    whole-run path calls it from ``_materialize`` between F1's return and F2's call. The process
    boundary Decision 145 introduced sits before this gate, never between it and the transaction.
    Accepted Decision 116 §5 keeps the surrounding rule intact: a refused run leaves the accepted
    catalog unchanged, and a failed gate is reported rather than worked around or retried in place.

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


#: ``census_plan_sources.parser_state`` values that **block** progression past F0 -- D140-R12.
#:
#: These are the existing accepted parser terminals, read rather than redefined: ``failed`` is
#: the accepted meaning of *no consumer may read this run's counts -- including zero -- as a real
#: observation*. Decision 140 does not invent a parser verdict; it stops the run at one that
#: already exists. ``quarantined`` -- the terminal for ``completed_with_quarantine`` -- is
#: deliberately **absent**: the accepted rules already permit a quarantined parse to proceed, and
#: D140-R12 widens nothing.
BLOCKING_PARSER_STATES: Final = frozenset({"failed"})

#: Source dispositions that block progression past F0, for the same reason -- D140-R12.
#:
#: ``E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE`` is the accepted classification for a source the
#: canary was asked to parse and could not. It leaves ``parser_state`` untouched rather than
#: setting it to ``failed``, so the parser-state gate alone would not catch it.
BLOCKING_SOURCE_DISPOSITIONS: Final = frozenset({"E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"})


def require_f0_success(outcome: SingleSourceOutcome) -> SingleSourceOutcome:
    """Return ``outcome``, or stop the run before F1 begins -- D140-R12.

    The D139 review found that a **blocking F0 failure did not stop the canary**: F0 could
    finish ``failed``, and F1, F2 and a normal ``canary_result.json`` followed anyway, with the
    operator exit code reporting success. A run that produced no usable parse would have been
    indistinguishable from one that worked, which is the single most consequential way this
    canary could mislead.

    The gate reads the **existing** accepted terminals -- :data:`BLOCKING_PARSER_STATES` and
    :data:`BLOCKING_SOURCE_DISPOSITIONS` -- and adds no parser methodology of its own. It sits
    between F0's return and F1's first call, so on a breach **F1 runs zero times, F2 runs zero
    times, no result document is written, and the operator exit is a gate failure**. The world
    stays exactly as it is: nothing is cleaned, nothing is deleted, and nothing is retried.

    Raises:
        SingleSourceCanaryError: F0 reached a blocking terminal.
    """
    state = outcome.outcome.parser_state_after
    disposition = outcome.outcome.disposition
    if state in BLOCKING_PARSER_STATES or disposition in BLOCKING_SOURCE_DISPOSITIONS:
        message = (
            f"F0 reached a blocking terminal (parser_state {state!r}, disposition "
            f"{disposition!r}) and the run STOPS AND REPORTS here. F1 does not begin, F2 does "
            "not begin, and no canary result document is written: a failed parse must never be "
            "reported as a completed canary. Nothing was deleted, cleaned, or retried, and the "
            "disposable world is left exactly as it is for diagnosis"
        )
        raise SingleSourceCanaryError(message)
    return outcome


def _bind_catalog(working: WorkingCatalog) -> tuple[_WorkingCatalogWriter, CensusCatalog]:
    """Bind the accepted writer and the compact-contract catalog to one working catalog.

    Stated once so the whole-run path and the accepted **Decision 145** phase path cannot drift
    into two bindings of the same thing. :data:`COMPACT_EVIDENCE` is passed **here**, explicitly,
    which is the accepted Decision 116 §5 item 7 requirement: the full-observation default is
    unreachable by omission rather than merely unlikely, on **every** path that runs a phase.
    """
    writer = _WorkingCatalogWriter(working)
    return writer, CensusCatalog(writer, compact_evidence=COMPACT_EVIDENCE)


def _f0(
    *,
    working: WorkingCatalog,
    tree: DataTree,
    selected: SelectedPlannedSource,
    writer: _WorkingCatalogWriter,
    catalog: CensusCatalog,
    sidecar: CompactEvidenceSidecar,
    batch_size: int,
    capacity_guard: Callable[[], None] | None,
) -> SingleSourceOutcome:
    """**Phase F0** -- parse the one governed source, and record what it produced.

    The run's longest phase by far: roughly twenty-seven hours over ~985,000 members on the
    first planned source. Every durable row it implies is committed when this returns, the
    compact sidecar holds the member manifest and the source completeness digest, and the
    run-local ledger reads ``parsed``.

    Extracted so that the whole-run path and the accepted **Decision 145** phase-restart path run
    the *same* F0 rather than two that must be kept in step. The caller supplies the write
    containment and the phase observations; nothing about the parse is decided here.
    """
    source = selected.source
    working.ledger.begin_source(source.source_instance_id, source.source_id)
    outcome = materialize_one_planned_source(
        writer=writer,
        tree=tree,
        catalog=catalog,
        selected=selected,
        sidecar=sidecar,
        batch_size=batch_size,
        checkpoint_batches=True,
        capacity_guard=capacity_guard,
    )
    # D140-R12: between F0's return and anything that reads its output. The ledger is not
    # marked parsed for a run that did not parse, and F1 is not reached at all.
    require_f0_success(outcome)
    working.ledger.mark_parsed(
        source.source_instance_id,
        parts=outcome.members,
        batches=outcome.outcome.parsed_records,
    )
    return outcome


def _f1(
    *,
    catalog: CensusCatalog,
    batch_size: int,
    capacity_guard: Callable[[], None] | None,
) -> int:
    """**Phase F1** -- the Decision 012 resolution pass over every persisted accession.

    Decision 094 §6.4 order, unchanged: every persisted accession is resolved **before** the
    association relation is projected, because §6.2 item 5 reads the resolver's own output.

    Its evidence accumulates on ``catalog`` as a ``ResolutionEvidence``, which is the
    one piece of cross-phase state that lives only in memory while the phase runs --
    and is exactly why accepted Decision 145 writes it to durable state at F1's terminal rather
    than carrying it in RAM across a process boundary it cannot cross.
    """
    return catalog.count_persisted_accession_resolutions(
        batch_size=batch_size, checkpoint_batches=True, capacity_guard=capacity_guard
    )


def _f2(
    *,
    connection: sqlite3.Connection,
    capacity_guard: Callable[[], None] | None,
) -> AssociationTotality:
    """**Phase F2** -- the Decision 094 §6.4 canonical association projection.

    One transaction, so a stop inside it is a rollback: the in-flight projection is discarded
    rather than truncated. ``capacity_guard`` is sampled from its innermost loop (D138-R8), which
    is what lets a continuous floor reached mid-projection abort from **inside** the open
    transaction.
    """
    return materialize_census_associations(
        connection, compact_evidence=True, capacity_guard=capacity_guard
    )


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
    writer, catalog = _bind_catalog(working)
    connection = working.connection
    source = selected.source
    with write_containment(connection):
        outcome = _f0(
            working=working,
            tree=tree,
            selected=selected,
            writer=writer,
            catalog=catalog,
            sidecar=sidecar,
            batch_size=batch_size,
            capacity_guard=capacity_guard,
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
        _f1(catalog=catalog, batch_size=batch_size, capacity_guard=capacity_guard)
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
        totality = _f2(connection=connection, capacity_guard=capacity_guard)
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
    outcome = materialized.outcome
    corroboration = outcome.corroboration
    observation = outcome.observation
    return _record_evidence_values(
        sidecar=sidecar,
        resolution=_resolution_record(resolution),
        corroboration=None if corroboration is None else _corroboration_record(corroboration),
        observation_id=None if observation is None else observation.observation_id,
        source_id=None if observation is None else observation.source_id,
        artifact_sha256="" if observation is None else (observation.logical_sha256 or ""),
        projection_digest=outcome.completeness_digest,
    )


def _resolution_record(resolution: ResolutionEvidence) -> Mapping[str, object]:
    """One resolution pass's eight accepted D113 §8 values, as plain data.

    The projection that makes F1's evidence **durable-shaped**: every field is a count or a hex
    digest, so the same eight values reach the sidecar whether they were produced a microsecond
    ago in this process or read back from a checkpoint written by one that has since exited.
    """
    return {
        "accessions": resolution.accessions,
        "implicit_resolutions": resolution.implicit,
        "explicit_resolutions": resolution.explicit,
        "omitted_field_rows": resolution.omitted_field_rows,
        "materialized_field_rows": resolution.materialized_field_rows,
        "omitted_cohort_rows": resolution.omitted_cohort_rows,
        "materialized_cohort_rows": resolution.materialized_cohort_rows,
        "completeness_digest": resolution.completeness_digest(),
    }


def _corroboration_record(corroboration: FullIndexCorroboration) -> Mapping[str, object]:
    """One full-index quarter's accepted D113 §9 corroboration values, as plain data."""
    return {
        "index_rows": corroboration.index_rows,
        "corroborating": corroboration.corroborating,
        "exceptions": corroboration.exceptions,
        "unbound": len(corroboration.unbound),
        "omitted_observations": corroboration.omitted_observations,
        "materialized_observations": corroboration.written,
        "corroboration_digest": corroboration.digest,
    }


def _record_evidence_values(
    *,
    sidecar: CompactEvidenceSidecar,
    resolution: Mapping[str, object],
    corroboration: Mapping[str, object] | None,
    observation_id: str | None,
    source_id: str | None,
    artifact_sha256: str,
    projection_digest: str,
) -> Mapping[str, str]:
    """Write the D113 §§8-9 evidence and return the five accepted identities -- one implementation.

    Given plain values rather than a live parse result, so the whole-run path and the accepted
    **Decision 145** phase path write **the same rows by the same rule**. A second copy of this
    for the phase path would be a second place the evidence contract could drift.
    """
    sidecar.record_resolution(
        resolution_scope=CANARY_RESOLUTION_SCOPE,
        accessions=stored_int(resolution["accessions"]),
        implicit_resolutions=stored_int(resolution["implicit_resolutions"]),
        explicit_resolutions=stored_int(resolution["explicit_resolutions"]),
        omitted_field_rows=stored_int(resolution["omitted_field_rows"]),
        materialized_field_rows=stored_int(resolution["materialized_field_rows"]),
        omitted_cohort_rows=stored_int(resolution["omitted_cohort_rows"]),
        materialized_cohort_rows=stored_int(resolution["materialized_cohort_rows"]),
        completeness_digest=str(resolution["completeness_digest"]),
    )
    if corroboration is not None and observation_id is not None:
        sidecar.record_corroboration(
            source_observation_id=observation_id,
            source_id=source_id or "",
            artifact_sha256=artifact_sha256,
            index_rows=stored_int(corroboration["index_rows"]),
            corroborating=stored_int(corroboration["corroborating"]),
            exceptions=stored_int(corroboration["exceptions"]),
            unbound=stored_int(corroboration["unbound"]),
            omitted_observations=stored_int(corroboration["omitted_observations"]),
            materialized_observations=stored_int(corroboration["materialized_observations"]),
            corroboration_digest=str(corroboration["corroboration_digest"]),
        )
    manifest = "" if observation_id is None else sidecar.member_manifest_digest(observation_id)
    return {
        "member_manifest_digest": manifest,
        "projection_digest": projection_digest,
        "resolution_digest": str(resolution["completeness_digest"]),
        "corroboration_digest": (
            "" if corroboration is None else str(corroboration["corroboration_digest"])
        ),
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
    # D144-R1: a diagnostic prefix of the first canary is measured over the topology the first
    # canary will run on, or it describes a configuration nobody selected. It narrows to the
    # same constant for the same reason the complete-source path does.
    require_external_envelope(
        resolved_work_root,
        observed_at=utc_now(),
        environ=environ,
        asserted_uuid=require_volume_uuid,
        required_transport=FIRST_CANARY_REQUIRED_TRANSPORT,
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
# --------------------------------------------------------------------------- #
# Governed major-phase restart -- accepted Decision 145
# --------------------------------------------------------------------------- #
#: The accepted free-space floor each phase is **admitted** under, by the phase it is about to
#: begin -- accepted Decision 145 §7.
#:
#: Every value here is an already-accepted constant used at its already-accepted meaning; not one
#: floor is invented, moved, or relaxed. ``F0`` starts a run from nothing and keeps the D137-R4
#: launch floor exactly. ``F1`` and ``F2`` **continue** one, and the launch floor answers a
#: question that is false by construction once F0 has written a hundred gibibytes -- *"is there
#: room to run the whole canary from nothing?"*. The questions a continuation must answer are the
#: accepted phase questions, and they already have accepted numbers: D138-R6's ``PRE_F1`` floor
#: before F1, and the Decision 126 §7 pre-F2 admission gate before F2.
#:
#: **Admission is not the only check either phase faces.** F1 records and enforces ``PRE_F1``
#: again through :func:`~disclosure_drift.m3.external_working_root.require_phase_free_space`, and
#: F2 runs :func:`_require_pre_f2_free_space` immediately before opening its transaction -- the
#: same deliberate redundancy through one primitive the work root already uses.
PHASE_ADMISSION_FLOOR: Final[Mapping[str, int]] = {
    PHASE_F0: LAUNCH_MINIMUM_FREE_BYTES,
    PHASE_F1: PRE_F1_MINIMUM_FREE_BYTES,
    PHASE_F2: PRE_F2_MINIMUM_FREE_BYTES,
}


#: The operator mode that runs each major phase, and the phase it runs -- accepted Decision 145.
#:
#: One mode per phase rather than a ``--mode phase --phase f1`` pair, deliberately: the mode a
#: governed run was launched under is then legible in ``ps`` output, in the host execution lock's
#: own detail record, and in the runbook, without a second argument that could disagree with it.
CANARY_PHASE_MODES: Final[Mapping[str, str]] = {
    f"phase-{phase}": phase for phase in CANARY_PHASE_SEQUENCE
}


def phase_execution_identity(
    *, repository: RepositoryIdentity, batch_size: int = CANARY_BATCH_SIZE
) -> str:
    """Digest what governs how this build executes a phase -- D145 §12, corrected by Decision 147.

    **What it is for.** A successor process is a continuation of the *same* governed run. It must
    refuse to continue a predecessor's checkpoint under code whose governing semantics have
    moved, and this is the mechanical form of that: the declared execution contract *and* the
    identity of the repository revision the code is running from are folded into one digest,
    recorded at each terminal, and re-derived and compared by the process that continues.

    **Why the repository identity is here, stated plainly.** Until Decision 147 this digest bound
    ten frozen constants plus ``disclosure_drift.__version__``, and the independent review
    Decision 145 itself demanded found -- **D146-MAJOR-1** -- that this bound no executable
    governing code at all: the version string is the literal ``"0.1.0"`` and has moved exactly
    once in the whole history, so an accepted capacity floor could be relaxed ``60 -> 1`` GiB and
    an admission guard deleted outright while the digest stayed bit-identical. It now folds the
    **repository commit and the repository tree** the running source was imported from, derived
    by :mod:`~disclosure_drift.m3.repository_identity` from Git rather than declared by anyone.
    A governing repository change between phases now refuses, mechanically.

    **Both halves, not one.** The frozen contract inputs are kept, and the code identity is added
    beside them: the repository identity is the backstop that catches *any* source change, and the
    declared inputs are what let a reader see which policy values a continuation is actually
    protected against. Neither replaces the other.

    **The capacity policy inputs, corrected.** Decision 145 §12 said this folded "the four
    capacity floors" and it folded three -- **D146-MINOR-1**. Every execution-governing capacity
    value on the F0/F1/F2 path is folded now: the three phase **admission** floors, the ``POST_F0``
    post-phase **invariant**, and the two **continuous F2** thresholds -- the alert that decides
    what a capacity observation reports, and the hard floor that rolls F2's single transaction
    back. Six, named individually rather than counted.

    **``cache_bytes`` is deliberately absent.** Accepted Decision 119's equivalence proof
    establishes that the page-cache budget moves no row, no ordering, no digest and no identity;
    folding a provably evidence-neutral execution parameter into a continuity check would refuse
    continuations that are provably fine. ``batch_size`` **is** folded in, because it decides
    when rows become durable and no accepted record blesses changing it mid-run.

    Args:
        repository: The identity of the repository the running source was imported from. Passed
            rather than fetched, so this function stays pure and the production path has exactly
            **one** derivation point -- :func:`run_single_source_canary_phase`, which derives it
            itself through
            :func:`~disclosure_drift.m3.repository_identity.require_clean_running_repository` and
            accepts no operator-supplied revision.
        batch_size: Parts per real transaction.
    """
    return execution_identity(
        {
            "canary_contract": CANARY_CONTRACT,
            "restart_contract": PHASE_RESTART_CONTRACT,
            "evidence_contract": COMPACT_EVIDENCE_CONTRACT,
            "resolution_scope": CANARY_RESOLUTION_SCOPE,
            "required_transport": FIRST_CANARY_REQUIRED_TRANSPORT,
            "qualified_volume_uuid": QUALIFIED_EXTERNAL_VOLUME_UUID,
            "batch_size": batch_size,
            "launch_minimum_free_bytes": LAUNCH_MINIMUM_FREE_BYTES,
            "post_f0_minimum_free_bytes": POST_F0_MINIMUM_FREE_BYTES,
            "pre_f1_minimum_free_bytes": PRE_F1_MINIMUM_FREE_BYTES,
            "pre_f2_minimum_free_bytes": PRE_F2_MINIMUM_FREE_BYTES,
            "f2_alert_free_bytes": F2_ALERT_FREE_BYTES,
            "f2_hard_floor_free_bytes": F2_HARD_FLOOR_FREE_BYTES,
            "package_version": disclosure_drift.__version__,
            "repository_identity_contract": repository.contract,
            "repository_head_sha": repository.head_sha,
            "repository_tree_sha": repository.tree_sha,
        }
    )


def attach_world(work_root: Path, run_id: str) -> CanaryWorld:
    """Open the disposable world a previous phase created. **It creates nothing.**

    The exact inverse of :func:`create_world`, and the inversion is the point:
    ``create_world`` refuses an identity whose world already exists, and this refuses one whose
    world does not. Between them there is no path that creates a world for a continuation, so a
    successor process can never manufacture the state it was supposed to inherit -- which is the
    failure mode that would turn "F0 finished" into "F0 was skipped".

    Raises:
        SingleSourceCanaryError: the identity is unlawful, or its world, working catalog, or
            run-local ledger is absent or is not what it must be.
    """
    validate_run_id(run_id)
    if work_root.is_symlink():
        message = "the canary work root is a symbolic link and is refused"
        raise SingleSourceCanaryError(message)
    if not work_root.is_dir():
        message = (
            "the canary work root does not exist as a directory; a phase continuation attaches "
            "to a world beneath it and never creates one, so an absent work root is a refusal"
        )
        raise SingleSourceCanaryError(message)
    target = work_root / run_id
    if target.is_symlink():
        message = f"canary world {run_id!r} exists as a symbolic link and is refused"
        raise SingleSourceCanaryError(message)
    if not target.is_dir():
        message = (
            f"canary world {run_id!r} does not exist; a phase continuation never creates the "
            "world it was supposed to inherit. Nothing was created and the run is refused"
        )
        raise SingleSourceCanaryError(message)
    world = CanaryWorld(run_id=run_id, directory=target)
    if not world.working_catalog.is_file():
        message = (
            f"canary world {run_id!r} holds no working catalog; there is no completed phase to "
            "continue from and nothing was created"
        )
        raise SingleSourceCanaryError(message)
    if world.result.exists():
        message = (
            f"canary world {run_id!r} already carries its create-once result document, so the "
            "run has already finished. A finished run is never re-entered"
        )
        raise SingleSourceCanaryError(message)
    return world


@dataclass(frozen=True, slots=True)
class CanaryPhaseResult:
    """What one major phase, running in one process, established -- accepted Decision 145.

    It is **not** a canary result and cannot be mistaken for one: it carries no association
    totality, no five accepted identities, and no complete-source claim, because a phase reached
    none of them. The run's :class:`CanaryResult` is written by F2's process alone.

    The process fields are the §9 RAM-reclamation evidence, recorded rather than asserted: this
    process's own id and peak resident size, the predecessor's, and the proof that the
    predecessor's process was gone before this one began.
    """

    contract: str
    phase: str
    successor_phase: str | None
    run_id: str
    source_instance_id: str
    started_at_utc: str
    completed_at_utc: str
    execution_identity: str
    #: The repository commit and tree this phase's process executed from -- Decision 147. Rendered
    #: so the operator, and the test that drives three real processes, can read the code identity
    #: a phase actually ran under rather than infer it from a digest of everything else as well.
    repository_head_sha: str
    repository_tree_sha: str

    # -- the RAM-reclamation evidence -- D145 §9 -------------------------- #
    pid: int
    rss_peak_bytes_at_start: int | None
    rss_peak_bytes_at_terminal: int | None
    predecessor_phase: str | None
    predecessor_pid: int | None
    predecessor_rss_peak_bytes_at_terminal: int | None
    #: Whether the predecessor's process was proved absent **before** this phase began. ``True``
    #: for every admitted continuation, because a live predecessor is a refusal rather than a
    #: recorded observation; ``None`` for F0, which has no predecessor to prove anything about.
    predecessor_process_gone: bool | None

    # -- what the phase left behind --------------------------------------- #
    world_relative_working_catalog: str
    world_relative_sidecar: str
    operational_catalog_sha256_before: str
    operational_catalog_sha256_after: str
    #: Written by F2's process only. ``False`` for F0 and F1, which finish a phase and not a run.
    result_document_written: bool
    capacity_observations: tuple[Mapping[str, object], ...] = ()

    @property
    def operational_catalog_unchanged(self) -> bool:
        """Whether the accepted catalog is byte-identical to what this phase started from."""
        return self.operational_catalog_sha256_before == self.operational_catalog_sha256_after

    def as_record(self) -> Mapping[str, object]:
        """The complete phase outcome as a plain mapping, carrying no absolute path."""
        record: dict[str, object] = {name: getattr(self, name) for name in self.__slots__}
        record["operational_catalog_unchanged"] = self.operational_catalog_unchanged
        return record


def run_single_source_canary_phase(
    *,
    phase: str,
    operational_catalog: Path,
    tree: DataTree,
    work_root: Path,
    run_id: str,
    source_instance_id: str,
    batch_size: int = CANARY_BATCH_SIZE,
    cache_bytes: int | None = WORKING_CATALOG_CACHE_BYTES,
    require_volume_uuid: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> CanaryPhaseResult:
    """Run **exactly one** major execution phase in **this** process, and stop -- Decision 145.

    The governed major-phase restart. One process per phase, so that a phase which reached its
    durable terminal can be followed by a process that *does not exist yet* -- and the memory the
    finished phase was holding is returned to the operating system by the only mechanism that
    genuinely returns it, which is the process ending.

    The sequence, and the whole of it::

        phase -> durable terminal checkpoint -> clean exit -> fresh process
              -> FULL reauthentication -> next phase

    **This is not pause/resume and grants no physical rights.** The restart right exists only
    *after* a phase reached durable terminal success. A crash, a kill, an out-of-memory
    termination, a closed lid, or a pulled cable part-way through a phase leaves **no
    checkpoint**, and an absent checkpoint refuses the successor: an interrupted run is still
    interrupted, governed exactly as accepted Decision 142 §8 already governs it. There is no
    ``SAFE_TO_EJECT`` state, the external volume must stay attached to the selected topology for
    the whole sequence, and ``GOVERNED_PAUSE_RESUME`` remains ``NOT_IMPLEMENTED``.

    **The successor trusts nothing the predecessor checked.** Every launch predicate is
    re-established here, in this process, before any work begins: **the identity of the Git
    revision this process's own source was imported from** (Decision 147), the work-root
    boundary, the complete Decision 137 external envelope narrowed to the Decision 142 §4
    topology, the exact Volume UUID, AC power and an open lid, D130 isolation, the external
    ``SQLITE_TMPDIR``, the host execution lock, the accepted catalog's own digest, and the
    predecessor's durable terminal checkpoint including the proof that its process is gone.

    **The code identity is recomputed here, not inherited.** F0 records the repository commit and
    tree it ran from; F1 derives them again in its own fresh process and refuses if they moved;
    F2 does the same. That is the correction Decision 147 makes to D146-MAJOR-1, and it is why a
    governing repository change between two phases stops the run instead of being invisible to
    it. Such a refusal is **terminal**: nothing is checked out, stashed, reset, fetched, cleaned
    or repaired, and it is not a resumable pause.

    Args:
        phase: Which major phase to run -- one of the three in
            :data:`~disclosure_drift.m3.canary_phases.CANARY_PHASE_SEQUENCE`.
            ``f0`` creates the disposable world; ``f1`` and ``f2`` attach to it and never create
            one.
        operational_catalog: The accepted catalog. Opened strictly read-only, always.
        tree: The data tree the frozen source artifacts are read from. Read by F0 alone -- F1 and
            F2 touch no artifact, which is why neither re-authenticates one.
        work_root: The disposable work root. Validated here, on every phase.
        run_id: This world's identity. Create-once at F0, and the identity every later phase must
            match exactly.
        source_instance_id: The one planned source's own plan key.
        batch_size: Parts per real transaction. Folded into the execution identity, so a
            continuation under a different value refuses.
        cache_bytes: The page-cache budget for the run-local working catalog. Deliberately **not**
            part of the execution identity; see :func:`phase_execution_identity`.
        require_volume_uuid: The mandatory external-volume assertion (D140-R2), re-supplied and
            re-checked on every phase.
        environ: The environment ``SQLITE_TMPDIR`` is cross-checked against.

    Raises:
        CanaryPhaseError: the phase already ran, its predecessor did not finish, an identity does
            not match, or the predecessor's process is still alive.
        ExternalWorkingRootError: the working root is external and a guard did not hold.
        SingleSourceCanaryError: a canary precondition failed.
    """
    validate_phase(phase)
    # 0a. WHICH CODE IS THIS -- Decision 147, closing D146-MAJOR-1. Derived from Git, in this
    #     process, from this module's own location: no flag, no environment variable and no
    #     argument can declare a revision, because a declared identity would make the continuity
    #     contract a statement of intent rather than a measurement. It runs FIRST, before the
    #     work root, the volume, the dock or the lock, because a process that cannot say which
    #     revision it is has no business touching the operator's hardware -- and because a
    #     refusal here costs nothing and reaches nothing.
    #
    #     A repository whose tracked tree is dirty, or which carries untracked non-ignored files,
    #     is REFUSED: the checkpoint records a committed tree, and that record is only worth
    #     anything if the committed tree is what ran. The refusal is terminal, not a pause --
    #     nothing is checked out, stashed, reset, cleaned, fetched or repaired.
    repository = require_clean_running_repository()
    # 0b. The write boundary and the complete envelope, exactly as the whole-run path establishes
    #    them, before anything is measured, opened, created, or attached to. D144-R1's narrowing
    #    is passed here too: a restart between phases must NOT be a way to reach a topology the
    #    owner did not select, so there is no seam here that admits a qualified direct attachment.
    resolved_work_root = require_canary_work_root(work_root, tree=tree)
    external: ExternalCanaryPreflight | None = require_external_envelope(
        resolved_work_root,
        observed_at=utc_now(),
        environ=environ,
        asserted_uuid=require_volume_uuid,
        required_transport=FIRST_CANARY_REQUIRED_TRANSPORT,
        minimum_free_bytes=PHASE_ADMISSION_FLOOR[phase],
    )
    started = utc_now()
    if not operational_catalog.is_file():
        message = "the accepted operational catalog does not exist at its fixed relative path"
        raise SingleSourceCanaryError(message)
    #    D140-R16, re-taken by every phase process rather than inherited. The lock is held for
    #    this phase's lifetime and released when this process exits, so at most one canary
    #    process executes on this host at any moment -- which is what the capacity model needs.
    lock = acquire_canary_execution_lock(
        _private_root_of(operational_catalog), detail={"run_id": run_id, "mode": f"phase-{phase}"}
    )
    try:
        return _run_phase_locked(
            phase=phase,
            operational_catalog=operational_catalog,
            tree=tree,
            resolved_work_root=resolved_work_root,
            run_id=run_id,
            source_instance_id=source_instance_id,
            batch_size=batch_size,
            cache_bytes=cache_bytes,
            external=external,
            started=started,
            repository=repository,
        )
    finally:
        lock.release()


def _run_phase_locked(  # noqa: PLR0913 - one phase, and every predicate it must re-establish
    *,
    phase: str,
    operational_catalog: Path,
    tree: DataTree,
    resolved_work_root: Path,
    run_id: str,
    source_instance_id: str,
    batch_size: int,
    cache_bytes: int | None,
    external: ExternalCanaryPreflight | None,
    started: str,
    repository: RepositoryIdentity,
) -> CanaryPhaseResult:
    """One phase, with the host execution lock already held. See the caller."""
    rss_at_start = process_peak_resident_bytes()
    # 1. The one source and the plan it came from, re-read live in THIS process through a
    #    strictly read-only handle. The plan fingerprint is the input identity a continuation is
    #    compared on, so it is derived rather than carried.
    with strictly_read_only_connection(operational_catalog) as reader:
        selected = select_planned_source(reader, source_instance_id)
        fingerprint, _ = plan_fingerprint(reader)
        observation = planned_source_observation(reader, selected)

    if phase == PHASE_F0:
        # D140-R20/R21: the artifact is authenticated and its shard-to-parent structure proved
        # BEFORE a world exists. F1 and F2 read no artifact at all, so neither re-authenticates
        # one -- re-digesting 1.5 GB to admit a phase that never opens it would be theatre.
        preauthenticate_source(tree=tree, selected=selected, observation=observation)
        free_before = shutil.disk_usage(_measurable(resolved_work_root)).free
        if external is not None:
            external.admitted.reauthenticate()
        world = create_world(resolved_work_root, run_id, require_existing_root=external is not None)
    else:
        world = attach_world(resolved_work_root, run_id)
        free_before = shutil.disk_usage(world.directory).free

    catalog_before = ""
    migration_head = 0
    with WorkingCatalog(
        operational_catalog, world.directory, cache_bytes=cache_bytes, attach=phase != PHASE_F0
    ) as working:
        identity = working.identity
        catalog_before = identity.source_file_sha256
        migration_head = identity.migration_head
        # 2. Admission. Has this phase already run, did its predecessor finish, and is this the
        #    same governed run under the same governing code? Every answer refuses.
        admission = require_phase_admission(
            working.ledger,
            phase=phase,
            run_id=run_id,
            source_instance_id=source_instance_id,
            execution_identity=phase_execution_identity(
                repository=repository, batch_size=batch_size
            ),
            repository_head_sha=repository.head_sha,
            repository_tree_sha=repository.tree_sha,
            catalog_source_sha256=identity.source_file_sha256,
            migration_head=identity.migration_head,
            plan_fingerprint=fingerprint,
        )
        predecessor = admission.predecessor
        predecessor_gone: bool | None = None
        if predecessor is not None:
            # 3. The RAM-reclamation property itself, enforced rather than hoped for: the phase
            #    before this one ran in a process that is GONE. A checkpoint is written before
            #    its process exits, so a checkpoint plus a live writer is exactly the state that
            #    must refuse -- two processes writing one working catalog is not a restart.
            if process_is_live_canary(predecessor.pid, run_id=run_id):
                message = (
                    f"the process that completed phase {predecessor.phase!r} (pid "
                    f"{predecessor.pid}) is still running this canary. A governed phase restart "
                    "is a CLEAN EXIT followed by a fresh process, never a second process joining "
                    "a live one, and two writers on one working catalog is not a restart. This "
                    "phase is refused and nothing was started"
                )
                raise SingleSourceCanaryError(message)
            predecessor_gone = True

        inherited = _inherited_observations(predecessor)
        observations: list[CapacityObservation] = []

        def record_phase(label: str) -> None:
            """Record one accepted D137-R7 boundary in this process, and enforce its floor."""
            if external is None:  # pragma: no cover - never bound without an external requirement
                return
            taken = observe_capacity(
                label,
                working_root=world.directory,
                database=world.working_catalog,
                wal=world.working_catalog.with_name(f"{WORKING_CATALOG_FILENAME}-wal"),
                temp_directory=external.temp_directory,
                volume=external.volume,
                observed_at=utc_now(),
            )
            observations.append(taken)
            require_phase_free_space(taken)

        capacity_guard: F2CapacityGuard | None = None
        if external is not None:
            observations.append(external.observation)
            capacity_guard = F2CapacityGuard(
                working_root=world.directory,
                volume=external.volume,
                record_into=observations,
                admitted=external.admitted,
            )

        context = _PhaseContext(
            phase=phase,
            working=working,
            world=world,
            tree=tree,
            selected=selected,
            sidecar=CompactEvidenceSidecar(world.sidecar),
            batch_size=batch_size,
            capacity_guard=capacity_guard,
            record_phase=record_phase,
            fingerprint=fingerprint,
            started=started,
            free_before=free_before,
            catalog_before=identity.source_file_sha256,
        )
        handoff: _F2Handoff | None = None
        try:
            if phase == PHASE_F0:
                payload = _phase_f0_body(context)
            elif phase == PHASE_F1:
                payload = _phase_f1_body(context)
            else:
                payload, handoff = _phase_f2_body(context)
        finally:
            context.sidecar.close()

    # 4. Everything above is committed and every handle on the working catalog is closed, so the
    #    digest and the byte length below describe the same bytes rather than two moments -- the
    #    accepted whole-run rule, unrelaxed.
    catalog_after, _ = file_digest(operational_catalog)
    observed = [*inherited, *(taken.as_record() for taken in observations)]
    result_written = False
    if handoff is not None:
        working_sha256, working_bytes = file_digest(world.working_catalog)
        result = _phase_result_document(
            handoff=handoff,
            working_sha256=working_sha256,
            working_bytes=working_bytes,
            run_id=run_id,
            selected=selected,
            fingerprint=fingerprint,
            catalog_after=catalog_after,
            free_after=shutil.disk_usage(world.directory).free,
            capacity_observations=tuple(observed),
        )
        # Create-once, and written BEFORE the terminal checkpoint. If this process died between
        # the two, the run's deliverable would still exist and F2 would refuse to run again --
        # `attach_world` refuses a world that already carries its result document.
        _write_once(world.result, json.dumps(result.as_record(), indent=2, sort_keys=True).encode())
        result_written = True

    # 5. The durable terminal checkpoint, written LAST and exactly once, through a short-lived
    #    handle of its own now that the working catalog's context has closed. Its presence is the
    #    completion proof, so it is never written before the thing it attests to is durable.
    checkpoint = PhaseCheckpoint(
        contract=PHASE_RESTART_CONTRACT,
        phase=phase,
        status=PHASE_STATUS_COMPLETE,
        run_id=run_id,
        source_instance_id=source_instance_id,
        execution_identity=phase_execution_identity(repository=repository, batch_size=batch_size),
        repository_head_sha=repository.head_sha,
        repository_tree_sha=repository.tree_sha,
        catalog_source_sha256=catalog_before,
        migration_head=migration_head,
        plan_fingerprint=fingerprint,
        completed_at_utc=utc_now(),
        pid=os.getpid(),
        rss_peak_bytes_at_start=rss_at_start,
        rss_peak_bytes_at_terminal=process_peak_resident_bytes(),
        payload={**payload, "capacity_observations": observed},
    )
    _write_terminal_checkpoint(world, checkpoint)
    return CanaryPhaseResult(
        contract=PHASE_RESTART_CONTRACT,
        phase=phase,
        successor_phase=PHASE_SUCCESSOR[phase],
        run_id=run_id,
        source_instance_id=source_instance_id,
        started_at_utc=started,
        completed_at_utc=checkpoint.completed_at_utc,
        execution_identity=checkpoint.execution_identity,
        repository_head_sha=checkpoint.repository_head_sha,
        repository_tree_sha=checkpoint.repository_tree_sha,
        pid=checkpoint.pid,
        rss_peak_bytes_at_start=checkpoint.rss_peak_bytes_at_start,
        rss_peak_bytes_at_terminal=checkpoint.rss_peak_bytes_at_terminal,
        predecessor_phase=None if predecessor is None else predecessor.phase,
        predecessor_pid=None if predecessor is None else predecessor.pid,
        predecessor_rss_peak_bytes_at_terminal=(
            None if predecessor is None else predecessor.rss_peak_bytes_at_terminal
        ),
        predecessor_process_gone=predecessor_gone,
        world_relative_working_catalog=WORKING_CATALOG_FILENAME,
        world_relative_sidecar=COMPACT_EVIDENCE_SIDECAR_FILENAME,
        operational_catalog_sha256_before=catalog_before,
        operational_catalog_sha256_after=catalog_after,
        result_document_written=result_written,
        capacity_observations=tuple(observed),
    )


def _inherited_observations(
    predecessor: PhaseCheckpoint | None,
) -> tuple[Mapping[str, object], ...]:
    """Every capacity observation the earlier phases of this run already recorded.

    Carried forward so the run's own result document holds one chronological capacity record
    across all three processes rather than three disconnected fragments.
    """
    if predecessor is None:
        return ()
    recorded = predecessor.payload.get("capacity_observations", ())
    if not isinstance(recorded, (list, tuple)):  # pragma: no cover - written as a list
        return ()
    return tuple(item for item in recorded if isinstance(item, Mapping))


def _write_terminal_checkpoint(world: CanaryWorld, checkpoint: PhaseCheckpoint) -> None:
    """Persist one phase's terminal checkpoint through a handle opened only to write it.

    Opened after the working catalog's own context has closed, so the checkpoint is the **last**
    durable act of the phase and cannot be written over work that is still in flight.
    """
    ledger = RunProgressLedger(world.directory / PROGRESS_LEDGER_FILENAME)
    try:
        write_phase_checkpoint(ledger, checkpoint)
    finally:
        ledger.close()


@dataclass(frozen=True, slots=True)
class _PhaseContext:
    """Everything one phase body needs, assembled once by the process that will run it."""

    phase: str
    working: WorkingCatalog
    world: CanaryWorld
    tree: DataTree
    selected: SelectedPlannedSource
    sidecar: CompactEvidenceSidecar
    batch_size: int
    capacity_guard: F2CapacityGuard | None
    record_phase: Callable[[str], None]
    fingerprint: str
    started: str
    free_before: int
    catalog_before: str


@dataclass(frozen=True, slots=True)
class _F2Handoff:
    """What F2's process measured inside its working-catalog context, for the result document.

    A small carrier rather than a wide argument list, and it exists because two of the values it
    holds -- the working catalog's digest and its byte length -- may only be measured **after**
    the last handle on that file is closed, so that they describe the same bytes rather than two
    moments. That is the accepted whole-run rule and it is not relaxed here.
    """

    identities: Mapping[str, str]
    counts: Mapping[str, int]
    totality: Mapping[str, int]
    wal_bytes: int
    source_sha256: str
    migration_head: int
    f0_payload: Mapping[str, object]
    f1_payload: Mapping[str, object]


def _phase_f0_body(context: _PhaseContext) -> Mapping[str, object]:
    """Run F0 in this process, and record what a later phase will need from it.

    **What the payload is, and what it is not.** It is not a second copy of F0's evidence: the
    member manifest, the source completeness digest and the per-member digests all live in the
    compact sidecar, durably, written as F0 ran. The payload carries the values that had **no
    durable home** -- the accepted parse disposition and parser states, the observation's own
    identity, the corroboration totals for a full-index quarter, and the run-level facts F0's
    process is the only one in a position to measure. That is exactly the bounded persistence
    accepted Decision 145 §7 authorizes, and no more.
    """
    working = context.working
    writer, catalog = _bind_catalog(working)
    with write_containment(working.connection):
        outcome = _f0(
            working=working,
            tree=context.tree,
            selected=context.selected,
            writer=writer,
            catalog=catalog,
            sidecar=context.sidecar,
            batch_size=context.batch_size,
            capacity_guard=context.capacity_guard,
        )
        # F0 has produced every durable row the source implies. The accepted POST_F0 gate is
        # this phase's terminal question -- *did F0 leave enough behind?* -- and PRE_F1 is the
        # next process's opening one, which is where the two labels now genuinely sit.
        context.record_phase("POST_F0")
    observation = outcome.observation
    corroboration = outcome.corroboration
    return {
        "started_at_utc": context.started,
        "plan_position": context.selected.plan_position,
        "plan_source_count": context.selected.plan_source_count,
        "operational_catalog_sha256_before": context.catalog_before,
        "work_root_free_bytes_before": context.free_before,
        "source_id": context.selected.source.source_id,
        "source_observation_id": None if observation is None else observation.observation_id,
        "source_artifact_sha256": (
            "" if observation is None else (observation.logical_sha256 or "")
        ),
        "source_artifact_byte_length": (
            0 if observation is None else int(observation.content_size_bytes or 0)
        ),
        "disposition": outcome.outcome.disposition,
        "parser_state_before": outcome.outcome.parser_state_before,
        "parser_state_after": outcome.outcome.parser_state_after,
        "parser_run_id": outcome.outcome.parser_run_id,
        "members": outcome.members,
        "projection_records": outcome.records,
        "parsed_records": outcome.outcome.parsed_records,
        "quarantined_records": outcome.outcome.quarantined_records,
        "omitted_field_observations": outcome.omitted_field_observations,
        "materialized_field_observations": outcome.materialized_field_observations,
        "completeness_digest": outcome.completeness_digest,
        "corroboration": (
            None if corroboration is None else dict(_corroboration_record(corroboration))
        ),
    }


def _phase_f1_body(context: _PhaseContext) -> Mapping[str, object]:
    """Run F1 in this process, and make its evidence durable before the process ends.

    **This is the correction the restart actually needed.** F1's evidence accumulates on the
    catalog object as a :class:`~disclosure_drift.sec.census.ResolutionEvidence` -- a rolling
    digest and seven counts -- and in the whole-run path it is read at the very end, long after
    F1 returned, because the same process is still holding it. A process that exits at F1's
    terminal would take it with it, and re-deriving it would mean **re-running F1**, which is
    precisely the duplicate phase execution accepted Decision 145 §13 prohibits. So F1's own
    process writes it down, at its own terminal, in the same eight accepted D113 §8 values the
    sidecar records.
    """
    working = context.working
    _writer, catalog = _bind_catalog(working)
    with write_containment(working.connection):
        # The accepted PRE_F1 gate, asked by the process that is about to begin F1.
        context.record_phase("PRE_F1")
        _f1(
            catalog=catalog,
            batch_size=context.batch_size,
            capacity_guard=context.capacity_guard,
        )
        context.record_phase("POST_F1_PRE_F2")
    return {"resolution": dict(_resolution_record(catalog.resolution_evidence))}


def _phase_f2_body(context: _PhaseContext) -> tuple[Mapping[str, object], _F2Handoff]:
    """Run F2 in this process, record the run's evidence, and finish the canary.

    F2 is the last phase, so its process does what the whole-run path does after F2 returns: it
    writes the D113 §§8-9 evidence into the sidecar from the durable values every phase left
    behind, records the accepted disposition in the run-local ledger, and truncates the
    write-ahead log. The create-once result document is written by its caller, once the last
    handle on the working catalog is closed.

    **The pre-F2 admission gate is where accepted Decision 126 §7 (D126-R6) put it** -- taken by
    the path that is about to open the transaction, immediately before it opens, in the same
    process. A restart between F1 and F2 does not move it, and could not: only the path that
    opens the transaction can decline to open it.
    """
    working = context.working
    ledger = working.ledger
    f0 = read_phase_checkpoint(ledger, PHASE_F0)
    f1 = read_phase_checkpoint(ledger, PHASE_F1)
    if f0 is None or f1 is None:  # pragma: no cover - admission already required both
        message = (
            "F2 cannot assemble the run's result: an earlier phase's durable checkpoint is "
            "absent. Nothing is estimated and nothing is re-run"
        )
        raise SingleSourceCanaryError(message)
    with write_containment(working.connection):
        _require_pre_f2_free_space(working.path.parent)
        totality = _f2(connection=working.connection, capacity_guard=context.capacity_guard)
        context.record_phase("POST_F2")
        counts = _counts(working.connection)
    resolution = _stored_mapping(f1.payload.get("resolution"), field="resolution")
    corroboration = _stored_mapping(
        f0.payload.get("corroboration"), field="corroboration", optional=True
    )
    identities = _record_evidence_values(
        sidecar=context.sidecar,
        resolution=resolution or {},
        corroboration=corroboration,
        observation_id=_optional_text(f0.payload.get("source_observation_id")),
        source_id=_optional_text(f0.payload.get("source_id")),
        artifact_sha256=str(f0.payload.get("source_artifact_sha256", "")),
        projection_digest=str(f0.payload.get("completeness_digest", "")),
    )
    working.ledger.mark_disposed(
        context.selected.source.source_instance_id,
        str(f0.payload["disposition"]),
        detail=str(f0.payload["parser_state_after"]),
    )
    working.checkpoint()
    handoff = _F2Handoff(
        identities=identities,
        counts=counts,
        totality=totality.as_record(),
        wal_bytes=working.wal_byte_length(),
        source_sha256=working.identity.source_file_sha256,
        migration_head=working.identity.migration_head,
        f0_payload=f0.payload,
        f1_payload=f1.payload,
    )
    return {"association_totality": dict(totality.as_record()), "counts": dict(counts)}, handoff


def _optional_text(value: object) -> str | None:
    """One optional stored string, or ``None`` -- never the string ``"None"``."""
    return None if value is None else str(value)


def _stored_mapping(
    value: object, *, field: str, optional: bool = False
) -> Mapping[str, object] | None:
    """One stored sub-record, refusing anything that is not one.

    Checkpoint payloads arrive as ``object`` because they were read back from JSON. A field that
    should carry a phase's evidence and does not is a **refusal**: a run whose evidence cannot be
    read is never finished with an estimate, and never by re-running the phase that produced it.

    Raises:
        SingleSourceCanaryError: the field is absent when required, or is not a mapping.
    """
    if value is None:
        if optional:
            return None
        message = (
            f"a phase checkpoint carries no {field!r}; the run's result is never assembled from "
            "an estimate and the phase that produced it is never re-run to recover it"
        )
        raise SingleSourceCanaryError(message)
    if not isinstance(value, Mapping):
        message = f"a phase checkpoint's {field!r} is not a mapping and is refused"
        raise SingleSourceCanaryError(message)
    return value


def _phase_result_document(
    *,
    handoff: _F2Handoff,
    working_sha256: str,
    working_bytes: int,
    run_id: str,
    selected: SelectedPlannedSource,
    fingerprint: str,
    catalog_after: str,
    free_after: int,
    capacity_observations: tuple[Mapping[str, object], ...],
) -> CanaryResult:
    """Assemble the accepted Decision 116 §9 result from what the three phases left durable.

    Every value here was either measured by this process or read from a phase checkpoint that a
    process wrote at its own terminal. **Nothing is estimated, and nothing is recomputed by
    re-running a phase.** The whole-run path assembles the identical surface from the same
    values held in memory; the accepted Decision 145 equivalence proof is that the two records
    agree field for field.
    """
    f0 = handoff.f0_payload
    f1 = handoff.f1_payload
    resolution = _stored_mapping(f1.get("resolution"), field="resolution") or {}
    corroborated = (
        _stored_mapping(f0.get("corroboration"), field="corroboration", optional=True) or {}
    )
    return CanaryResult(
        contract=CANARY_CONTRACT,
        evidence_contract=COMPACT_EVIDENCE_CONTRACT,
        run_id=run_id,
        started_at_utc=str(f0["started_at_utc"]),
        completed_at_utc=utc_now(),
        source_instance_id=selected.source.source_instance_id,
        source_id=str(f0["source_id"]),
        plan_position=stored_int(f0["plan_position"]),
        plan_source_count=stored_int(f0["plan_source_count"]),
        plan_fingerprint=fingerprint,
        source_observation_id=_optional_text(f0.get("source_observation_id")),
        source_artifact_sha256=str(f0["source_artifact_sha256"]),
        source_artifact_byte_length=stored_int(f0["source_artifact_byte_length"]),
        disposition=str(f0["disposition"]),
        parser_state_before=str(f0["parser_state_before"]),
        parser_state_after=str(f0["parser_state_after"]),
        parser_run_id=_optional_text(f0.get("parser_run_id")),
        members=stored_int(f0["members"]),
        projection_records=stored_int(f0["projection_records"]),
        parsed_records=stored_int(f0["parsed_records"]),
        quarantined_records=stored_int(f0["quarantined_records"]),
        omitted_field_observations=stored_int(f0["omitted_field_observations"]),
        materialized_field_observations=stored_int(f0["materialized_field_observations"]),
        canonical_accession_count=handoff.counts["canonical_accession_count"],
        registrant_count=handoff.counts["registrant_count"],
        substantive_relation_count=handoff.counts["substantive_relation_count"],
        quarantined_record_count=handoff.counts["quarantined_record_count"],
        structural_observation_count=handoff.counts["structural_observation_count"],
        accession_observation_count=handoff.counts["accession_observation_count"],
        field_resolution_row_count=handoff.counts["field_resolution_row_count"],
        cohort_resolution_row_count=handoff.counts["cohort_resolution_row_count"],
        association_totality=handoff.totality,
        resolution_accessions=stored_int(resolution["accessions"]),
        implicit_resolutions=stored_int(resolution["implicit_resolutions"]),
        explicit_resolutions=stored_int(resolution["explicit_resolutions"]),
        omitted_field_rows=stored_int(resolution["omitted_field_rows"]),
        materialized_field_rows=stored_int(resolution["materialized_field_rows"]),
        omitted_cohort_rows=stored_int(resolution["omitted_cohort_rows"]),
        materialized_cohort_rows=stored_int(resolution["materialized_cohort_rows"]),
        index_rows=stored_int(corroborated.get("index_rows", 0)),
        corroborating_rows=stored_int(corroborated.get("corroborating", 0)),
        corroboration_exceptions=stored_int(corroborated.get("exceptions", 0)),
        unbound_accessions=stored_int(corroborated.get("unbound", 0)),
        omitted_corroboration_observations=stored_int(corroborated.get("omitted_observations", 0)),
        member_manifest_digest=handoff.identities["member_manifest_digest"],
        projection_digest=handoff.identities["projection_digest"],
        resolution_digest=handoff.identities["resolution_digest"],
        corroboration_digest=handoff.identities["corroboration_digest"],
        compact_evidence_identity=handoff.identities["compact_evidence_identity"],
        world_relative_working_catalog=WORKING_CATALOG_FILENAME,
        world_relative_sidecar=COMPACT_EVIDENCE_SIDECAR_FILENAME,
        working_catalog_sha256=working_sha256,
        working_catalog_byte_length=working_bytes,
        working_catalog_wal_byte_length=handoff.wal_bytes,
        working_catalog_source_sha256=handoff.source_sha256,
        migration_head=handoff.migration_head,
        operational_catalog_sha256_before=str(f0["operational_catalog_sha256_before"]),
        operational_catalog_sha256_after=catalog_after,
        work_root_free_bytes_before=stored_int(f0["work_root_free_bytes_before"]),
        work_root_free_bytes_after=free_after,
        capacity_observations=capacity_observations,
    )


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

    **``run`` is refused where the external envelope governs** (Decision 149, D149-R3). Accepted
    Decision 145 decomposed the governed complete-source canary into three processes, and Decision
    147 bound each of them to the repository revision it executed under; a single whole-run process
    provides neither property. So on a root the external envelope governs -- the one the real
    canary runs on -- ``run`` refuses here and the phase modes are the only route. On an
    **internal** root ``run`` is untouched and remains exactly the accepted Decision 116 path,
    which is what the bounded library and development exercises use; that path cannot be mistaken
    for the governed one, because the governed one is external by construction. The rule is keyed
    on the envelope rather than on a second externality test, because D138-R1 already makes the
    resolved root the one thing that decides that question.

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
    phase = CANARY_PHASE_MODES.get(mode)
    # D144-R1: the operator surface narrows too, so `--mode preflight` answers the question the
    # operator is actually asking -- "is THIS the qualified launch configuration?" -- rather
    # than "is this A qualified configuration?". A preflight that went green over a direct
    # attachment would be the D142 §6 fallback with a receipt.
    external: ExternalCanaryPreflight | None = require_external_envelope(
        resolved_work_root,
        observed_at=utc_now(),
        environ=environ,
        asserted_uuid=require_volume_uuid,
        required_transport=FIRST_CANARY_REQUIRED_TRANSPORT,
        # Accepted Decision 145 §7: a phase that CONTINUES a run is admitted under the accepted
        # floor for the phase it is about to begin, never under the launch floor -- which asks
        # whether there is room to run the whole canary from nothing, and is false by
        # construction once F0 has written. Every other mode keeps the launch floor exactly.
        minimum_free_bytes=(
            LAUNCH_MINIMUM_FREE_BYTES if phase is None else PHASE_ADMISSION_FLOOR[phase]
        ),
    )
    # D149-R3: the governed external route runs the PHASED contract, and only that. Accepted
    # Decision 145 decomposed the complete-source canary into three processes precisely so a
    # finished phase's memory is reclaimed by the only mechanism that reclaims it, and Decision
    # 147 then bound each phase to the repository revision it executed under. `--mode run` is
    # neither: it is one process for the whole run, and it derives no repository identity. On an
    # INTERNAL root it remains exactly the accepted Decision 116 path, which is what the bounded
    # library and development exercises use. On a root the external envelope governs -- the one
    # the real canary runs on -- it is refused here, before the run is entered.
    #
    # Keyed on `external`, deliberately, because accepted Decision 138 (D138-R1) already makes
    # THE RESOLVED ROOT the single thing that decides whether this is a governed external run.
    # A second externality rule here would be a second source of truth for one question.
    if mode == "run" and external is not None:
        message = (
            "canary mode 'run' is refused on a working root the external envelope governs. The "
            "governed complete-source canary runs the accepted Decision 145 PHASED contract -- "
            f"{', '.join(sorted(CANARY_PHASE_MODES))} -- each in its own operating-system "
            "process, so a finished phase's memory is reclaimed by the process ending, and each "
            "phase records and re-derives the repository revision it executed under. A single "
            "whole-run process does neither. Nothing was created and no world was touched; there "
            "is no flag, environment variable or configuration key that admits 'run' here"
        )
        raise SingleSourceCanaryError(message)
    if phase is not None:
        outcome = run_single_source_canary_phase(
            phase=phase,
            operational_catalog=operational_catalog,
            tree=DataTree.from_root(private_root),
            work_root=resolved_work_root,
            run_id=run_id,
            source_instance_id=source_instance_id,
            require_volume_uuid=require_volume_uuid,
            environ=environ,
        )
        return CanaryOperatorResult(
            exit_code=_EXIT_OK if outcome.operational_catalog_unchanged else _EXIT_GATE_FAILURE,
            lines=_render(outcome.as_record(), title=f"canary-source {mode}"),
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
            f"unknown canary mode {mode!r}; the modes are 'preflight', 'run', 'profile-prefix', "
            f"and the accepted Decision 145 phase modes {', '.join(sorted(CANARY_PHASE_MODES))}"
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
