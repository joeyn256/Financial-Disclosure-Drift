"""The external working-root safety surface for one corrected complete-source canary.

**What this module is for.** Accepted **Decision 135** §10 (D135-R5) named three distinct steps --
selecting a path is not qualifying a volume, and qualifying a volume is not adopting it.
**Decision 136** completed the second: the exact SSK SSD was mechanically qualified, and a **narrow
one-canary exception** to the standing D125-R4 cold/archive-only rule was created for it
(D136-R8). This module is the third step's machinery: the fail-closed guards that must hold
before a future corrected complete-source canary may be launched onto that volume.

**It does not adopt the volume, and it starts nothing.** Every function here refuses or returns;
none creates a world, a run identity, a launch receipt, or an execution namespace. Decision 137
implements this surface and validates it; the corrected canary itself needs a separate owner
authorization that this module neither carries nor implies.

**No second root-selection mechanism.** The canary already takes an operator-supplied
``--work-root`` and re-asserts it inside the run through
:func:`~disclosure_drift.m3.single_source_canary.require_canary_work_root`. That surface is
sufficient and is reused unchanged; what was missing was not a way to *name* an external root
but a way to *authenticate* one. This module adds only the authentication:

* **Identity, on the stable Volume UUID** (D137-R1). ``disk4``/``disk4s2`` are attach-time
  identifiers that differ across reboots and re-plugs, and a mount path can be produced by any
  volume that happens to be named the same. The Volume UUID is the identity that survives both,
  so it is the only accepted one. A wrong UUID, an absent volume, and a lookup that fails are
  three different causes with **one** outcome: refusal. There is no fallback to internal storage.
* **Isolation from the immutable D130 archive** (D137-R3). The ~104 GB D128 archive shares this
  volume, and the accepted shape for the working world is a **sibling** tree at the volume root,
  never a child of the archive. Containment is decided on ``realpath``-resolved, case-folded path
  *components*, so ``..`` normalization, a symlink, a case variant, and a merely similar prefix
  are each handled correctly rather than approximately.
* **Capacity, measured where it will actually be consumed** (D137-R4, D137-R5). The launch floor
  and the pre-F2 floor are both measured on the filesystem hosting the **selected** working root.
  Measuring the internal Data volume while writing to an external one is the failure this exists
  to prevent.
* **Explicit SQLite temporary placement** (D137-R8). **Decision 124** §9 (D124-R5) has required an
  explicit ``SQLITE_TMPDIR`` since it was written, and D128 left its peak unmeasured.
  Unset, it is the operating system's temporary directory -- on the internal volume -- so a spill
  large enough to matter would land exactly where the capacity model says it must not.

**What this module claims about the filesystem, and what it does not** (D137-R11). Decision 136
established **process-crash recovery only** on this ExFAT volume. Nothing here claims journaled
filesystem semantics, power-loss safety, surprise-removal safety, or USB-bridge cache-flush
correctness; ExFAT has no metadata journal, and D136 could not distinguish a satisfied
``F_FULLFSYNC`` from a bridge ignoring one. The guards below reduce capacity and path risk. They
do not convert the volume into a journaled one.

The controlling records are, under ``Docs/Decisions/``:
``decision_124_m3_3_capacity_reconciliation.md``,
``decision_130_m3_3_d128_archival_and_reclamation.md``,
``decision_135_m3_3_corrected_run_capacity_reconciliation.md``, and
``decision_136_m3_3_external_ssd_active_volume_qualification.md``.
"""

from __future__ import annotations

import hashlib
import os
import plistlib
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.storage.sqlite import utc_now

__all__ = [
    "CAPACITY_PHASES",
    "D130_ARCHIVE_DIRECTORY_NAME",
    "D130_ARCHIVE_TAR_BYTE_LENGTH",
    "D130_ARCHIVE_TAR_NAME",
    "D130_COMPACT_PROOFS",
    "F2_ALERT_FREE_BYTES",
    "F2_ALERT_STATE",
    "F2_CAPACITY_MAX_SAMPLE_SECONDS",
    "F2_CAPACITY_SAMPLE_SECONDS",
    "F2_HARD_FLOOR_FREE_BYTES",
    "F2_HARD_STOP_REASON",
    "F2_HARD_STOP_STATE",
    "F2_MEASUREMENT_FAILED_REASON",
    "F2_NORMAL_STATE",
    "LAUNCH_MINIMUM_FREE_BYTES",
    "PHASE_MINIMUM_FREE_BYTES",
    "POST_F0_MINIMUM_FREE_BYTES",
    "PRE_F1_MINIMUM_FREE_BYTES",
    "QUALIFIED_EXTERNAL_VOLUME_UUID",
    "SQLITE_TMPDIR_ENV",
    "ArchiveProof",
    "CapacityObservation",
    "ExternalCanaryPreflight",
    "ExternalWorkingRootError",
    "F2CapacityGuard",
    "F2CapacityHardStopError",
    "VolumeIdentity",
    "VolumeIdentityProvider",
    "d130_archive_directory",
    "external_canary_preflight",
    "external_volume_candidate",
    "f2_capacity_state",
    "macos_volume_identity",
    "mount_point_of",
    "observe_capacity",
    "require_external_envelope",
    "require_launch_free_space",
    "require_outside_d130_archive",
    "require_phase_free_space",
    "require_qualified_volume",
    "verify_d130_archive",
]


class ExternalWorkingRootError(DisclosureDriftError):
    """Raised when an external working root cannot be proved safe for the corrected canary.

    Refusal is the only outcome this type carries. There is no fallback to internal storage, no
    "proceed and watch", and no automatic cleanup: a guard that cannot establish its condition
    refuses, and the operator is told which condition failed.
    """


class F2CapacityHardStopError(ExternalWorkingRootError):
    """The dedicated governed condition that aborts F2 from **inside** its transaction -- D138-R8.

    A distinct type rather than a message, because it is the only refusal in this module raised
    while a transaction is open, and the only one whose evidence has to outlive a rollback.
    :attr:`record` carries that evidence: it is built **before** the exception is raised and is
    held on the exception object, so it survives the ``ROLLBACK``
    :func:`~disclosure_drift.storage.sqlite.transaction` performs on the way out. Writing the
    hard-stop evidence into the transaction being rolled back would destroy exactly the record
    the operator needs (D138-R10).

    It is a subclass of :class:`ExternalWorkingRootError` so that a caller which already refuses
    on the external envelope cannot accidentally admit this one.
    """

    def __init__(self, message: str, *, record: Mapping[str, object]) -> None:
        super().__init__(message)
        #: The bounded D138-R10 hard-stop evidence. Deterministic and path-free.
        self.record: Mapping[str, object] = record


# --------------------------------------------------------------------------- #
# Frozen identities and floors
# --------------------------------------------------------------------------- #
#: The **only** externally authorized candidate volume, by accepted **Decision 136** §4 (D136-R1)
#: and **Decision 137** (D137-R1).
#:
#: The stable identity, deliberately. ``diskutil`` also reports ``disk4s2`` on physical ``disk4``
#: for this volume, and both are attach-time identifiers that will differ across reboots and
#: re-plugs; the Volume UUID will not. A mount path is insufficient for the same reason from the
#: other direction -- ``/Volumes/SSK SSD`` is whatever volume happens to be mounted there.
QUALIFIED_EXTERNAL_VOLUME_UUID: Final = "397A4D4A-9508-391E-814E-3B533C7BD049"

#: The immutable D130 archive directory's basename, at the qualified volume's root.
#:
#: Accepted **Decision 130** archived the D128 complete-first-source world here and proved the
#: internal copy deleted, so this tree is the **only** surviving copy of that evidence. Accepted
#: Decision 136 §10 (D136-R7) verified it untouched. Nothing may be written inside it.
D130_ARCHIVE_DIRECTORY_NAME: Final = "FDD_M3_3_D130_D128_ARCHIVE"

#: The ~`104` GB uncompressed PAX archive inside that directory. Its **length** is a compact
#: proof; its content is never read. Hashing `103,966,696,960` bytes to answer "is the archive
#: still there" would take longer than the check is worth and would buy nothing D130 §6 has not
#: already recorded.
D130_ARCHIVE_TAR_NAME: Final = "d128_complete_first_source_v1.pax.tar"

#: The accepted byte length of that archive, from **Decision 130** §6 (D130-R2).
D130_ARCHIVE_TAR_BYTE_LENGTH: Final = 103_966_696_960

#: The **free-space floor a corrected complete-source run must clear before it may start**:
#: `185` GiB, ``198,642,237,440`` bytes.
#:
#: Accepted **Decision 135** §7 (D135-R2) states the floor and §11 (D135-R7) states it at
#: ``PRE_LAUNCH`` with the breach behaviour
#: written out -- *refuse to launch; no partial start, no "proceed and watch"* -- and accepted
#: Decision 136 §5 (D136-R2) confirms it unchanged and still controlling after the volume
#: qualification measured `310,498,557,952` bytes free against it.
#:
#: It is measured on the filesystem hosting the **selected** working root (D137-R4). Measuring the
#: internal Data volume while the world is built on an external one would satisfy the arithmetic
#: and none of the intent.
LAUNCH_MINIMUM_FREE_BYTES: Final = 185 * 1024**3

#: The free-space floor that must hold **after F0 completes and before F1 begins**: `60` GiB,
#: ``64,424,509,440`` bytes.
#:
#: Accepted **Decision 135** §11 (D135-R7) states this row as a *stop-and-report* gate, not as a
#: planning note. Decision 137 recorded the ``POST_F0`` observation and enforced nothing, which the
#: D137 independent review raised as **MAJOR-3**; **Decision 138** (D138-R5) makes it executable.
#:
#: It is measured on the filesystem hosting the **active** working root. Below it, F1 does not
#: begin: nothing is deleted, nothing is cleaned, and the run stops and reports.
POST_F0_MINIMUM_FREE_BYTES: Final = 60 * 1024**3

#: The free-space floor that must hold **immediately before F1 begins**: `55` GiB,
#: ``59,055,800,320`` bytes.
#:
#: Accepted Decision 135 §11 (D135-R7), adopted as executable by **Decision 138** (D138-R6). It
#: stays a **separate named phase gate** even though ``POST_F0`` and ``PRE_F1`` occur close
#: together: the two answer different questions -- *did F0 leave enough behind?* and *is there
#: enough to start F1 with?* -- and folding them would lose the phase-boundary verification that
#: is the point of having both.
PRE_F1_MINIMUM_FREE_BYTES: Final = 55 * 1024**3

#: The **continuous** F2 planning-alert threshold: `20` GiB, ``21,474,836,480`` bytes.
#:
#: Accepted Decision 135 §11 (D135-R7) puts an alert here and the hard stop below it, so that the
#: operator sees a breach coming rather than only its arrival. Reaching it is a **report**, not a
#: stop, and never a deletion.
F2_ALERT_FREE_BYTES: Final = 20 * 1024**3

#: The **continuous** F2 emergency hard floor: `10` GiB, ``10,737,418,240`` bytes.
#:
#: Accepted **Decision 124** §9 (D124-R5), **unchanged** by Decision 137 (D137-R6). Raising the
#: pre-F2 admission gate from `30` GiB to `50` GiB says what must be true *before* the transaction
#: opens; it says nothing about the emergency floor *during* it, and the two are deliberately
#: different numbers for different questions.
#:
#: **F2 is a single transaction, so a stop here is a rollback.** The in-flight projection is
#: discarded rather than truncated, and the operator must be told that explicitly rather than
#: discovering it (D135-R7, D136-R11 item 7).
F2_HARD_FLOOR_FREE_BYTES: Final = 10 * 1024**3

#: The variable SQLite reads to place its temporary and spill files. Not a
#: ``DISCLOSURE_DRIFT_*`` variable: it belongs to SQLite, is read here rather than honoured as a
#: package override, and is never printed.
SQLITE_TMPDIR_ENV: Final = "SQLITE_TMPDIR"

F2_NORMAL_STATE: Final = "F2_CAPACITY_NORMAL"
F2_ALERT_STATE: Final = "F2_CAPACITY_ALERT"
F2_HARD_STOP_STATE: Final = "F2_CAPACITY_HARD_STOP"

#: The phase boundaries a corrected complete-source run records capacity at (D137-R7), in the
#: order they occur. The labels are the accepted Decision 135 §11 rows and are **not** invented
#: here; a measurement that could not be taken stays ``None`` rather than becoming a zero.
CAPACITY_PHASES: Final = (
    "PRE_LAUNCH",
    "POST_F0",
    "PRE_F1",
    "POST_F1_PRE_F2",
    "DURING_F2",
    "POST_F2",
)

#: The phase boundaries that are **gates** rather than only observations, and the floor each one
#: requires -- D138-R5 and D138-R6.
#:
#: ``PRE_LAUNCH`` is absent because :func:`require_launch_free_space` already enforces it before
#: any world exists, and ``POST_F1_PRE_F2`` is absent because accepted Decision 126 §7 (D126-R6)
#: places its `50` GiB gate at the one point where the measurement and the transaction it admits
#: cannot be separated by a race; both keep their own accepted call sites and are **not** moved
#: here. ``POST_F2`` is a report: there is nothing left to refuse.
PHASE_MINIMUM_FREE_BYTES: Final[Mapping[str, int]] = {
    "POST_F0": POST_F0_MINIMUM_FREE_BYTES,
    "PRE_F1": PRE_F1_MINIMUM_FREE_BYTES,
}


# --------------------------------------------------------------------------- #
# Volume identity
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class VolumeIdentity:
    """What one mounted volume is, as a structured record rather than parsed prose.

    ``volume_uuid`` is the only field any guard decides on. The rest are recorded so a refusal or
    an observation can be read afterwards without re-querying a volume that may by then be gone.
    """

    volume_uuid: str
    mount_point: Path
    filesystem_type: str
    device_identifier: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering that carries **no** absolute path.

        The mount point is deliberately absent. The Volume UUID is the identity every guard
        decides on, it is already published in accepted Decision 136, and it cannot be a personal
        path -- which the repository's own output rule bars from every operator surface.
        """
        return {
            "volume_uuid": self.volume_uuid,
            "filesystem_type": self.filesystem_type,
            "device_identifier": self.device_identifier,
        }


#: How a volume identity is obtained for a path.
#:
#: Substituting one is **the** test seam: no test in this repository may depend on the operator's
#: actual SSD being attached, mounted, or holding any particular amount of free space. Every guard
#: below takes ``provider=None`` and resolves :func:`macos_volume_identity` from module globals at
#: call time rather than binding it as a default argument, so a substitution reaches the composed
#: preflight and the run path too -- not only a directly-called guard.
VolumeIdentityProvider = Callable[[Path], VolumeIdentity]


def _nearest_existing(path: Path) -> Path:
    """The nearest existing ancestor of ``path``.

    A working root is measured and identified **before** it is created, so every guard here has
    to answer questions about a path that may not exist yet. Its nearest existing ancestor is on
    the same volume by construction, which is exactly what both questions need.
    """
    candidate = Path(os.path.realpath(path))
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def mount_point_of(path: Path) -> Path:
    """The mount point of the filesystem hosting ``path``.

    Walks upward while the device number is unchanged, which is the definition of a mount point
    rather than a guess at one. Derived rather than declared: an operator cannot assert that a
    path is on the external volume, and ``diskutil`` will not answer for an arbitrary
    subdirectory -- it accepts a mount point or a device node.

    Raises:
        ExternalWorkingRootError: the filesystem could not be identified.
    """
    try:
        candidate = _nearest_existing(path)
        device = candidate.stat().st_dev
        while candidate != candidate.parent:
            parent = candidate.parent
            if parent.stat().st_dev != device:
                return candidate
            candidate = parent
    except OSError as exc:
        message = (
            "the filesystem hosting the selected working root could not be identified "
            f"({type(exc).__name__}); an unidentifiable volume is refused rather than assumed"
        )
        raise ExternalWorkingRootError(message) from exc
    return candidate


def macos_volume_identity(path: Path) -> VolumeIdentity:
    """Read the volume identity for ``path`` from ``diskutil``'s **structured** output.

    ``diskutil info -plist`` is asked for the mount point :func:`mount_point_of` derived, and the
    reply is parsed as a property list. The human-oriented ``diskutil info`` table is never
    parsed: a structured form exists, so the fragile one is not used.

    Raises:
        ExternalWorkingRootError: the volume could not be identified, for any reason.
    """
    mount = mount_point_of(path)
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
            ["/usr/sbin/diskutil", "info", "-plist", str(mount)],
            capture_output=True,
            check=True,
            timeout=30,
        )
        parsed = plistlib.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, plistlib.InvalidFileException) as exc:
        message = (
            f"the volume hosting the selected working root could not be identified "
            f"({type(exc).__name__}); a lookup that fails is refused, never assumed to pass"
        )
        raise ExternalWorkingRootError(message) from exc
    uuid = parsed.get("VolumeUUID")
    if not isinstance(uuid, str) or not uuid.strip():
        message = (
            "the volume hosting the selected working root reports no Volume UUID; without a "
            "stable identity the volume cannot be authenticated and is refused"
        )
        raise ExternalWorkingRootError(message)
    return VolumeIdentity(
        volume_uuid=uuid.strip(),
        mount_point=mount,
        filesystem_type=str(parsed.get("FilesystemType", "")),
        device_identifier=str(parsed.get("DeviceIdentifier", "")),
    )


def require_qualified_volume(
    path: Path,
    *,
    expected_uuid: str = QUALIFIED_EXTERNAL_VOLUME_UUID,
    provider: VolumeIdentityProvider | None = None,
) -> VolumeIdentity:
    """Return the identity of ``path``'s volume, or refuse -- D137-R1.

    Four outcomes, one of which is a pass:

    * the volume reports the expected UUID -> **pass**, and its identity is returned;
    * it reports a different UUID -> **refused**;
    * there is no volume to report one, because nothing is mounted where the path points ->
      **refused**, by the mismatch its nearest existing ancestor produces or by the lookup
      failing outright;
    * the lookup itself fails -> **refused**.

    The comparison is case-insensitive because ``diskutil`` reports upper-case UUIDs and an
    operator may type either, and exact otherwise: no prefix, no substring, no normalization
    beyond case and surrounding whitespace.

    Raises:
        ExternalWorkingRootError: the volume is not the accepted qualified volume.
    """
    resolve = macos_volume_identity if provider is None else provider
    identity = resolve(path)
    if identity.volume_uuid.strip().casefold() != expected_uuid.strip().casefold():
        message = (
            f"the selected working root is on volume {identity.volume_uuid}, which is not the "
            f"accepted qualified volume {expected_uuid}; the corrected canary runs on that "
            "volume alone and never falls back to internal storage"
        )
        raise ExternalWorkingRootError(message)
    return identity


# --------------------------------------------------------------------------- #
# Archive isolation
# --------------------------------------------------------------------------- #
def _comparable(path: Path) -> tuple[str, ...]:
    """Case-folded ``realpath`` components.

    Comparing **components** rather than strings is what makes the three aliasing cases fall out
    together: ``realpath`` collapses ``..`` and follows symlinks before anything is compared, and
    a component-wise prefix cannot mistake a sibling whose name merely *starts* with the
    archive's name for a child of it. Folding case is conservative on a case-insensitive volume
    and can only ever refuse more.
    """
    return tuple(part.casefold() for part in Path(os.path.realpath(path)).parts)


def _within(ancestor: tuple[str, ...], descendant: tuple[str, ...]) -> bool:
    return len(descendant) > len(ancestor) and descendant[: len(ancestor)] == ancestor


def d130_archive_directory(volume_mount_point: Path) -> Path:
    """The immutable D130 archive directory on a qualified volume."""
    return volume_mount_point / D130_ARCHIVE_DIRECTORY_NAME


def require_outside_d130_archive(root: Path, *, archive: Path) -> Path:
    """Return the resolved ``root``, or refuse it for touching the archive -- D137-R3.

    Three refusals, each fail-closed and each stated on resolved, case-folded components:

    * the root **is** the archive directory;
    * the root lies **inside** it, which is the case a ``../`` path or a symlink would otherwise
      launder;
    * the archive lies **inside the root**, which the accepted sibling-tree shape excludes and
      which would place the only surviving copy of the D128 evidence inside a disposable tree.

    The third is the same rule the accepted
    :func:`~disclosure_drift.m3.single_source_canary.require_disposable_work_root` already states
    for the private evidence root, applied to the other tree that must not be swallowed.

    Raises:
        ExternalWorkingRootError: the working root is not isolated from the archive.
    """
    root_parts = _comparable(root)
    archive_parts = _comparable(archive)
    if root_parts == archive_parts:
        message = (
            "the selected working root is the immutable D130 archive directory; the corrected "
            "canary writes nothing inside that tree"
        )
        raise ExternalWorkingRootError(message)
    if _within(archive_parts, root_parts):
        message = (
            "the selected working root lies inside the immutable D130 archive directory; the "
            "accepted shape is a sibling tree at the volume root, never a child of the archive"
        )
        raise ExternalWorkingRootError(message)
    if _within(root_parts, archive_parts):
        message = (
            "the selected working root contains the immutable D130 archive directory; the only "
            "surviving copy of the D128 evidence must not lie inside a disposable working tree"
        )
        raise ExternalWorkingRootError(message)
    return Path(os.path.realpath(root))


# --------------------------------------------------------------------------- #
# Capacity
# --------------------------------------------------------------------------- #
def _free_bytes(path: Path) -> int:
    """Free bytes on the filesystem hosting ``path``, or refuse.

    Measured on the nearest existing ancestor, so a working root that does not exist yet is
    measured on the volume it would be created on rather than on whatever the process happens to
    be running from.

    Raises:
        ExternalWorkingRootError: free space could not be measured.
    """
    try:
        return shutil.disk_usage(_nearest_existing(path)).free
    except OSError as exc:
        message = (
            f"free space on the selected working root's volume could not be measured "
            f"({type(exc).__name__}); an unmeasurable volume is refused rather than admitted"
        )
        raise ExternalWorkingRootError(message) from exc


def require_launch_free_space(path: Path, *, minimum: int = LAUNCH_MINIMUM_FREE_BYTES) -> int:
    """Return free bytes on ``path``'s volume, or refuse to launch -- D137-R4.

    ``>=`` is the rule, so the floor itself admits. Nothing is deleted, moved, or cleaned to
    reach it: a shortfall is reported and the run does not start.

    Raises:
        ExternalWorkingRootError: less than ``minimum`` is free.
    """
    free = _free_bytes(path)
    if free < minimum:
        message = (
            f"launch free-space floor not met: {free} bytes free on the selected working root's "
            f"volume, below the required {minimum} bytes ({minimum // 1024**3} GiB); the "
            "corrected complete-source run is refused. Nothing was deleted or cleaned"
        )
        raise ExternalWorkingRootError(message)
    return free


def f2_capacity_state(free_bytes: int) -> str:
    """Classify continuous free space during F2 -- D137-R6.

    Both thresholds are inclusive, as accepted Decision 135 §11 states them: *alert at* `20` GiB,
    *hard stop at* `10` GiB. Above the alert threshold nothing is reported and nothing stops.

    The classification never deletes anything, and the alert state is deliberately **not** a
    stop: raising the pre-F2 admission gate to `50` GiB moved what must be true before the
    transaction opens, and left the `10` GiB emergency floor during it exactly where D124-R5 put
    it.
    """
    if free_bytes <= F2_HARD_FLOOR_FREE_BYTES:
        return F2_HARD_STOP_STATE
    if free_bytes <= F2_ALERT_FREE_BYTES:
        return F2_ALERT_STATE
    return F2_NORMAL_STATE


@dataclass(frozen=True, slots=True)
class CapacityObservation:
    """Capacity at one named phase boundary -- D137-R7.

    Every optional field is ``None`` when the measurement was not available. **An unknown
    measurement stays unknown**: reporting a missing WAL as ``0`` would be indistinguishable from
    a checkpointed one, which is precisely the confusion D128's evidence left behind.
    """

    phase: str
    free_bytes: int
    total_bytes: int
    volume: VolumeIdentity | None
    database_bytes: int | None
    wal_bytes: int | None
    temp_bytes: int | None
    observed_at: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        record: dict[str, object] = {
            "phase": self.phase,
            "free_bytes": self.free_bytes,
            "total_bytes": self.total_bytes,
            "database_bytes": self.database_bytes,
            "wal_bytes": self.wal_bytes,
            "temp_bytes": self.temp_bytes,
            "f2_capacity_state": f2_capacity_state(self.free_bytes),
            "observed_at": self.observed_at,
        }
        record["volume"] = None if self.volume is None else dict(self.volume.as_record())
        return record


def _directory_allocation(directory: Path | None) -> int | None:
    """Bytes allocated beneath ``directory``, or ``None`` when it cannot be measured.

    Used for the ``SQLITE_TMPDIR`` allocation Decision 136 §8 (D136-R5) left unmeasured. It walks
    the temporary directory only -- never the archive, and never the working world's large objects
    -- so the cost is bounded by how many spill files SQLite currently holds.
    """
    if directory is None:
        return None
    try:
        total = 0
        for entry in directory.rglob("*"):
            if entry.is_file() and not entry.is_symlink():
                total += entry.stat().st_size
    except OSError:
        return None
    return total


def _byte_length(path: Path | None) -> int | None:
    """``path``'s size, or ``None`` when there is nothing to measure."""
    if path is None:
        return None
    try:
        return path.stat().st_size
    except OSError:
        return None


def observe_capacity(
    phase: str,
    *,
    working_root: Path,
    database: Path | None = None,
    wal: Path | None = None,
    temp_directory: Path | None = None,
    volume: VolumeIdentity | None = None,
    observed_at: str,
) -> CapacityObservation:
    """Record capacity at one accepted phase boundary -- D137-R7.

    Raises:
        ExternalWorkingRootError: ``phase`` is not one of :data:`CAPACITY_PHASES`, or free space
            could not be measured. Phase labels are the accepted Decision 135 §11 set and are
            never invented at a call site.
    """
    if phase not in CAPACITY_PHASES:
        message = (
            f"{phase!r} is not an accepted capacity phase boundary; the accepted labels are "
            f"{', '.join(CAPACITY_PHASES)} and no other label is recorded"
        )
        raise ExternalWorkingRootError(message)
    measurable = _nearest_existing(working_root)
    try:
        usage = shutil.disk_usage(measurable)
    except OSError as exc:
        message = (
            f"capacity at {phase} could not be measured ({type(exc).__name__}); an unmeasurable "
            "boundary is reported as a failure rather than recorded as a zero"
        )
        raise ExternalWorkingRootError(message) from exc
    return CapacityObservation(
        phase=phase,
        free_bytes=usage.free,
        total_bytes=usage.total,
        volume=volume,
        database_bytes=_byte_length(database),
        wal_bytes=_byte_length(wal),
        temp_bytes=_directory_allocation(temp_directory),
        observed_at=observed_at,
    )


# --------------------------------------------------------------------------- #
# SQLITE_TMPDIR
# --------------------------------------------------------------------------- #
def require_external_sqlite_tmpdir(
    *,
    working_root: Path,
    archive: Path,
    environ: Mapping[str, str] | None = None,
    expected_uuid: str = QUALIFIED_EXTERNAL_VOLUME_UUID,
    provider: VolumeIdentityProvider | None = None,
) -> Path:
    """Return the explicit external SQLite temporary root, or refuse -- D137-R8.

    Validated rather than set. Assigning ``SQLITE_TMPDIR`` from inside library code would place a
    process-wide side effect in a path whose whole purpose is to refuse unsafe states, and would
    hide the very setting the operator has to be able to see. So the launcher sets it, the
    runbook says to, and this refuses if it is absent or wrong.

    **The environment validated is the environment SQLite consumes** (D138-R3). SQLite reads
    ``SQLITE_TMPDIR`` from the process environment and from nowhere else, so that is where this
    guard reads it from too. An explicitly supplied ``environ`` is a **test and caller seam, not
    a substitute source**: when one is given it must carry the identical value, and a
    disagreement is a refusal rather than a preference. Validating one mapping while SQLite reads
    another would prove nothing about where the spill actually lands, which was the D137
    independent review's MINOR on this guard.

    Five conditions, all fail-closed:

    * an explicitly supplied mapping **agrees** with the process environment;
    * the variable is **set** and non-blank -- unset means SQLite spills to the operating
      system's temporary directory on the **internal** volume, silently;
    * it is an **absolute** path to an existing directory;
    * it is **outside the immutable D130 archive**;
    * it is on the **same qualified external volume** as the working world.

    Raises:
        ExternalWorkingRootError: the temporary root is absent, unusable, or not external, or
            the supplied mapping is not what SQLite will read.
    """
    # What SQLite will actually consume, always. `os.environ` is not consulted "as a default":
    # it is the authority, because it is the only environment the spilling process has.
    consumed = os.environ.get(SQLITE_TMPDIR_ENV)
    if environ is not None:
        declared = environ.get(SQLITE_TMPDIR_ENV)
        if declared != consumed:
            message = (
                f"the {SQLITE_TMPDIR_ENV} value supplied for validation is not the one SQLite "
                "will read from the process environment; validating one environment while "
                "SQLite consumes another proves nothing about where the spill lands, so the "
                "disagreement is refused rather than resolved in either direction"
            )
            raise ExternalWorkingRootError(message)
    raw = consumed
    if raw is None or not raw.strip():
        message = (
            f"{SQLITE_TMPDIR_ENV} is not set; SQLite would spill temporary and sort files to the "
            "operating system's temporary directory on the internal volume, which the corrected "
            "canary's capacity model does not cover. It is required explicitly"
        )
        raise ExternalWorkingRootError(message)
    candidate = Path(raw.strip())
    if not candidate.is_absolute():
        message = (
            f"{SQLITE_TMPDIR_ENV} is not an absolute path; a relative temporary root resolves "
            "against the working directory, which is not a stated external location"
        )
        raise ExternalWorkingRootError(message)
    if not candidate.is_dir():
        message = (
            f"{SQLITE_TMPDIR_ENV} does not name an existing directory; the temporary root is "
            "created and verified before launch rather than discovered mid-transaction"
        )
        raise ExternalWorkingRootError(message)
    resolved = require_outside_d130_archive(candidate, archive=archive)
    temp_volume = require_qualified_volume(resolved, expected_uuid=expected_uuid, provider=provider)
    working_volume = require_qualified_volume(
        working_root, expected_uuid=expected_uuid, provider=provider
    )
    if temp_volume.volume_uuid.casefold() != working_volume.volume_uuid.casefold():
        message = (
            f"{SQLITE_TMPDIR_ENV} is on a different volume from the working world; SQLite's "
            "spill must be counted by the same capacity model as the world it serves"
        )
        raise ExternalWorkingRootError(message)
    return resolved


# --------------------------------------------------------------------------- #
# The bounded D130 archive pre/postcheck
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ArchiveProof:
    """One accepted D130 §6 identity: a compact file's digest, or the large tar's length alone."""

    name: str
    byte_length: int
    sha256: str | None


#: The accepted **Decision 130** §6 (D130-R2) compact proofs, and nothing beyond them.
#:
#: Four small files carry a digest; the `103,966,696,960`-byte archive carries a length and
#: **no digest** (D137-R10). This is the same bounded check accepted Decision 136 §10 (D136-R7)
#: ran in `0.040` s, and it is bounded for the same reason: re-hashing ~`104` GB to establish
#: that a directory is still intact is a cost with no corresponding finding.
D130_COMPACT_PROOFS: Final = (
    ArchiveProof(
        name=D130_ARCHIVE_TAR_NAME,
        byte_length=D130_ARCHIVE_TAR_BYTE_LENGTH,
        sha256=None,
    ),
    ArchiveProof(
        name="d128_source_manifest.tsv",
        byte_length=3_645,
        sha256="af5088e4ac1c387675d50ba933e187c20f95e0e4cb471bf157665f00e366fac4",
    ),
    ArchiveProof(
        name="d128_tar_member_manifest.tsv",
        byte_length=3_645,
        sha256="af5088e4ac1c387675d50ba933e187c20f95e0e4cb471bf157665f00e366fac4",
    ),
    ArchiveProof(
        name="d128_archive_receipt.txt",
        byte_length=6_343,
        sha256="63d8fc4b72e6d3f7e3996fa1b76133dcc15b44828fe3890dc6f8052ea6f46b94",
    ),
    ArchiveProof(
        name="d130_post_deletion_proof.txt",
        byte_length=4_251,
        sha256="8387e9eb9994c3aae4e5e7b023bba0d587df46e3bbb80d06e220030c395d507d",
    ),
)


def verify_d130_archive(
    archive: Path, *, proofs: tuple[ArchiveProof, ...] = D130_COMPACT_PROOFS
) -> tuple[str, ...]:
    """Return the differences between ``archive`` and its accepted governance identity.

    An empty tuple is the pass. The check is **read-only and bounded**: the large tar is
    ``stat``-ed and never opened, and only the four small files are hashed.

    Used twice around a future launch (D137-R10). As a **precheck** a non-empty result must
    refuse the launch; as a **postcheck** it must be reported as a blocker, because a difference
    after the run means the corrected canary disturbed the only surviving copy of the D128
    evidence.

    Differences name only the archive-relative filename, never an absolute path.
    """
    differences: list[str] = []
    if not archive.is_dir():
        return ("the D130 archive directory is absent or is not a directory",)
    for proof in proofs:
        member = archive / proof.name
        try:
            size = member.stat().st_size
        except OSError:
            differences.append(f"{proof.name}: absent or unreadable")
            continue
        if size != proof.byte_length:
            differences.append(f"{proof.name}: {size} bytes, accepted {proof.byte_length}")
        if proof.sha256 is None:
            continue
        try:
            digest = hashlib.sha256(member.read_bytes()).hexdigest()
        except OSError:
            differences.append(f"{proof.name}: unreadable")
            continue
        if digest != proof.sha256:
            differences.append(f"{proof.name}: digest {digest}, accepted {proof.sha256}")
    return tuple(differences)


# --------------------------------------------------------------------------- #
# The composed preflight
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ExternalCanaryPreflight:
    """What the external launch preflight established. It creates nothing.

    Holding this object is **not** an authorization to launch. Decision 137 implements and
    validates these guards; the corrected complete-source canary needs a separate owner
    instrument, and no field here supplies one (D137-R12).
    """

    volume: VolumeIdentity
    launch_free_bytes: int
    archive_differences: tuple[str, ...]
    sqlite_tmpdir_verified: bool
    observation: CapacityObservation
    #: The verified external ``SQLITE_TMPDIR``. Carried so a run can size its allocation at each
    #: later phase boundary without re-reading the environment, and deliberately **absent from**
    #: :meth:`as_record`: it is an absolute operator-chosen path, and no operator surface in this
    #: repository prints one.
    temp_directory: Path

    @property
    def archive_intact(self) -> bool:
        """Whether the bounded D130 compact proofs matched their accepted identity."""
        return not self.archive_differences

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "volume": dict(self.volume.as_record()),
            "launch_free_bytes": self.launch_free_bytes,
            "launch_minimum_free_bytes": LAUNCH_MINIMUM_FREE_BYTES,
            "archive_intact": self.archive_intact,
            "archive_differences": list(self.archive_differences),
            "sqlite_tmpdir_verified": self.sqlite_tmpdir_verified,
            "observation": dict(self.observation.as_record()),
            "canary_authorized": False,
        }


def external_canary_preflight(
    *,
    working_root: Path,
    observed_at: str,
    environ: Mapping[str, str] | None = None,
    expected_uuid: str = QUALIFIED_EXTERNAL_VOLUME_UUID,
    provider: VolumeIdentityProvider | None = None,
    require_archive: bool = True,
) -> ExternalCanaryPreflight:
    """Run every D137 launch guard against ``working_root``, read-only, and create nothing.

    In order, because each later guard depends on the earlier one having held:

    1. **identity** (D137-R1) -- authenticate the volume by its stable UUID;
    2. **isolation** (D137-R3) -- refuse a root that is, is inside, or contains the D130 archive;
    3. **archive integrity** (D137-R10) -- the bounded compact precheck, tar never opened;
    4. **capacity** (D137-R4) -- `>= 185` GiB free, measured on that volume;
    5. **temporary placement** (D137-R8) -- an explicit external ``SQLITE_TMPDIR``;
    6. **observation** (D137-R7) -- one ``PRE_LAUNCH`` record.

    Args:
        working_root: The root a future world would be created under. It need not exist.
        observed_at: The timestamp the observation carries, supplied rather than read so the
            record stays deterministic under test.
        environ: The environment ``SQLITE_TMPDIR`` is read from. Defaults to the process's.
        expected_uuid: The accepted qualified volume. Defaults to the D136 volume.
        provider: How volume identity is obtained. Substituted in tests.
        require_archive: Whether the D130 archive must be present and intact. ``True`` on the
            qualified volume, where the archive lives; a synthetic fixture volume has none.

    Raises:
        ExternalWorkingRootError: any guard did not hold. Nothing is created either way.
    """
    volume = require_qualified_volume(working_root, expected_uuid=expected_uuid, provider=provider)
    archive = d130_archive_directory(volume.mount_point)
    require_outside_d130_archive(working_root, archive=archive)
    differences = verify_d130_archive(archive) if require_archive else ()
    if differences:
        message = (
            "the D130 archive precheck differs from its accepted governance identity "
            f"({'; '.join(differences)}); the corrected canary is refused rather than launched "
            "beside an archive whose identity cannot be confirmed"
        )
        raise ExternalWorkingRootError(message)
    free = require_launch_free_space(working_root)
    temp_directory = require_external_sqlite_tmpdir(
        working_root=working_root,
        archive=archive,
        environ=environ,
        expected_uuid=expected_uuid,
        provider=provider,
    )
    observation = observe_capacity(
        "PRE_LAUNCH",
        working_root=working_root,
        temp_directory=temp_directory,
        volume=volume,
        observed_at=observed_at,
    )
    return ExternalCanaryPreflight(
        volume=volume,
        launch_free_bytes=free,
        archive_differences=differences,
        sqlite_tmpdir_verified=True,
        observation=observation,
        temp_directory=temp_directory,
    )


# --------------------------------------------------------------------------- #
# The mandatory external envelope -- D138-R1, D138-R2, D138-R12
# --------------------------------------------------------------------------- #
def external_volume_candidate(path: Path) -> bool:
    """Whether ``path`` would be created on a volume other than the system root's -- D138-R1.

    The D137 independent review's **MAJOR-1** was that the external safety envelope was reached
    only by *asking* for it: omitting ``--require-volume-uuid`` restored the pre-D137 path, so a
    working root on an unqualified external disk -- or inside the immutable D130 archive -- was
    admitted without a single guard running. **Protection may not be opt-in**, so the decision of
    whether an envelope is required has to be taken from the path itself rather than from an
    argument the operator can leave out.

    It is decided the same way :func:`mount_point_of` decides everything else: by device number,
    on the **nearest existing ancestor**, so the requested world is classified before it is
    created and no ``diskutil`` call is made for an internal root. A root whose derived mount
    point is the system root's is internal; anything else -- an external disk, a disk image, a
    network mount -- is external and must be positively authenticated.

    **Internal is the only answer that admits without proof**, so an unclassifiable root is
    refused rather than assumed internal: :func:`mount_point_of` raises, and that propagates.

    Raises:
        ExternalWorkingRootError: the filesystem hosting ``path`` could not be identified.
    """
    return mount_point_of(path) != mount_point_of(Path(os.sep))


def require_external_envelope(
    working_root: Path,
    *,
    observed_at: str,
    environ: Mapping[str, str] | None = None,
    asserted_uuid: str | None = None,
) -> ExternalCanaryPreflight | None:
    """Apply the complete external envelope when one is owed, and refuse when it cannot hold.

    The single decision point for **D138-R1**. Three outcomes:

    * the root is **internal** and no external assertion was made -> ``None``, and the caller's
      path is exactly what accepted Decision 116 left it. Historical internal behaviour is
      preserved byte for byte (D138-R1), because nothing here runs;
    * the root is **external**, by :func:`external_volume_candidate` or because the operator
      asserted a volume -> the **complete** D137 envelope runs, and every one of its guards must
      hold. Omitting the assertion cannot disable a single one of them;
    * any guard does not hold -> :class:`ExternalWorkingRootError`, with **no world created**.

    ``asserted_uuid`` is an **assertion, never a switch** (D138-R1). Supplying it can only ever
    *add* a requirement: it forces the envelope on a root that would otherwise be classified
    internal -- so asserting the qualified volume for an internal root refuses at the identity
    guard, which is the truth -- and it must itself be the one qualified volume. There is no
    generic external-volume authorization here (**D138-R12**): the single accepted external
    identity is :data:`QUALIFIED_EXTERNAL_VOLUME_UUID`, an arbitrary caller-supplied UUID is
    refused before anything is measured, and D125-R4 remains the general rule everywhere outside
    that one-canary exception.

    Args:
        working_root: The root a world would be created under. It need not exist.
        observed_at: The timestamp the ``PRE_LAUNCH`` observation carries.
        environ: The environment to cross-check ``SQLITE_TMPDIR`` against. See
            :func:`require_external_sqlite_tmpdir`; ``None`` reads the process environment alone.
        asserted_uuid: An operator assertion that the root is on a named volume, or ``None``.

    Raises:
        ExternalWorkingRootError: an arbitrary UUID was asserted, the root could not be
            classified, or any guard in the envelope did not hold.
    """
    if asserted_uuid is not None and (
        asserted_uuid.strip().casefold() != QUALIFIED_EXTERNAL_VOLUME_UUID.strip().casefold()
    ):
        message = (
            f"{asserted_uuid} is not the one qualified external volume "
            f"{QUALIFIED_EXTERNAL_VOLUME_UUID}; Decision 136 §11 (D136-R8) created a narrow "
            "one-canary exception for that volume alone and Decision 138 (D138-R12) creates no "
            "generic external-volume authorization, so an arbitrary identity is refused"
        )
        raise ExternalWorkingRootError(message)
    if asserted_uuid is None and not external_volume_candidate(working_root):
        return None
    return external_canary_preflight(
        working_root=working_root,
        observed_at=observed_at,
        environ=environ,
        expected_uuid=QUALIFIED_EXTERNAL_VOLUME_UUID,
    )


# --------------------------------------------------------------------------- #
# The POST_F0 and PRE_F1 phase gates -- D138-R5, D138-R6
# --------------------------------------------------------------------------- #
def require_phase_free_space(
    observation: CapacityObservation,
    *,
    floors: Mapping[str, int] = PHASE_MINIMUM_FREE_BYTES,
) -> CapacityObservation:
    """Return ``observation``, or refuse the phase it opens -- D138-R5 and D138-R6.

    Accepted Decision 135 §11 (D135-R7) states ``POST_F0`` `>= 60` GiB and ``PRE_F1`` `>= 55` GiB
    as **stop-and-report** rows. Decision 137 recorded both observations and enforced neither,
    which the D137 independent review raised as **MAJOR-3**; this is the enforcement.

    ``>=`` is the rule at both floors, so each floor itself admits and one byte below refuses. A
    phase with no floor is returned untouched, and a measurement that could not be taken never
    reaches here at all -- :func:`observe_capacity` has already refused it, which is why a
    measurement failure refuses rather than being compared against anything.

    **Nothing is deleted, moved, or cleaned to clear a floor**, here or anywhere in this module.

    Raises:
        ExternalWorkingRootError: the phase carries a floor and free space is below it.
    """
    floor = floors.get(observation.phase)
    if floor is None or observation.free_bytes >= floor:
        return observation
    message = (
        f"{observation.phase} free-space gate not met: {observation.free_bytes} bytes free on "
        f"the active working root's volume, below the required {floor} bytes "
        f"({floor // 1024**3} GiB). STOP AND REPORT: the next phase does not begin, and nothing "
        "was deleted or cleaned to reach the floor"
    )
    raise ExternalWorkingRootError(message)


# --------------------------------------------------------------------------- #
# The in-process continuous F2 guard -- D138-R8, D138-R9, D138-R10
# --------------------------------------------------------------------------- #
#: The longest wall-clock interval **D138-R9** permits between two intended ``DURING_F2``
#: readings. A long batch must not buy hours of unobserved F2 execution.
F2_CAPACITY_MAX_SAMPLE_SECONDS: Final = 60.0

#: The interval this implementation actually schedules, well inside that ceiling. One
#: ``statvfs`` per five seconds is free beside a traversal that writes tens of millions of rows,
#: and D138-R9 asks for a substantially shorter interval wherever the existing loop makes one
#: natural. F2's per-accession loop makes it natural.
F2_CAPACITY_SAMPLE_SECONDS: Final = 5.0

#: The reason recorded when the `10` GiB floor is reached.
F2_HARD_STOP_REASON: Final = "F2_CAPACITY_HARD_STOP"

#: The reason recorded when free space could not be measured at all during F2.
F2_MEASUREMENT_FAILED_REASON: Final = "F2_CAPACITY_MEASUREMENT_FAILED"


def _free_and_total(path: Path) -> tuple[int, int]:
    """Free and total bytes on the filesystem hosting ``path``. The guard's default provider."""
    usage = shutil.disk_usage(_nearest_existing(path))
    return usage.free, usage.total


class F2CapacityGuard:
    """Sample free space **inside** the running F2 transaction, and abort it -- D138-R8.

    The D137 independent review's **MAJOR-2** was that the `10` GiB ``DURING_F2`` floor existed
    only as a classification and an optional second process: the watchdog's ``capacity``
    subcommand could print exit `6` all day and F2 would keep writing. Enforcement that depends
    on a human starting another process is not enforcement, so this samples from **within** the
    process executing F2 and raises from **inside** its transaction.

    **Aborting from inside is the whole point.** F2 is one transaction, so the
    :func:`~disclosure_drift.storage.sqlite.transaction` context rolls it back on the way out:
    the in-flight association projection is discarded rather than truncated, and no partial F2
    association state can commit. Nothing is deleted, no signal is sent, and no escalation
    happens -- D131's no-escalation behaviour is untouched (D138-R8).

    Three states, from the accepted inclusive thresholds:

    * free `> 20` GiB -> normal, and nothing is recorded;
    * `10` GiB `<` free `<= 20` GiB -> a ``DURING_F2`` **alert** observation is recorded and F2
      **continues**;
    * free `<= 10` GiB -> :class:`F2CapacityHardStopError`, carrying its D138-R10 evidence.

    A **measurement failure fails closed through the same path** (D138-R8): a reading that cannot
    be taken is not a reading that passed.

    Sampling is **bounded by wall clock, not by iteration count** (D138-R9). The first call always
    samples -- that is the reading taken immediately before F2 starts -- and thereafter a call
    returns immediately unless :data:`F2_CAPACITY_SAMPLE_SECONDS` have elapsed on a **monotonic**
    clock, which cannot be walked backwards by a system time adjustment mid-run. Calling it more
    often is therefore free, which is what lets the call sit in F2's innermost loop.

    Both the clock and the free-space provider are constructor seams, so a test can drive either
    without a real disk and without waiting.
    """

    __slots__ = (
        "_clock",
        "_free_space",
        "_interval",
        "_last",
        "_now",
        "_root",
        "_volume",
        "hard_stop_record",
        "observations",
        "samples",
    )

    def __init__(
        self,
        *,
        working_root: Path,
        volume: VolumeIdentity | None = None,
        interval_seconds: float = F2_CAPACITY_SAMPLE_SECONDS,
        free_space: Callable[[Path], tuple[int, int]] | None = None,
        clock: Callable[[], float] | None = None,
        now: Callable[[], str] | None = None,
        record_into: list[CapacityObservation] | None = None,
    ) -> None:
        if interval_seconds > F2_CAPACITY_MAX_SAMPLE_SECONDS:
            message = (
                f"a {interval_seconds}s DURING_F2 sampling interval exceeds the "
                f"{F2_CAPACITY_MAX_SAMPLE_SECONDS}s ceiling D138-R9 permits between intended "
                "checks; a longer interval would let a batch run unobserved"
            )
            raise ExternalWorkingRootError(message)
        self._root = working_root
        self._volume = volume
        self._interval = interval_seconds
        self._free_space = _free_and_total if free_space is None else free_space
        self._clock = time.monotonic if clock is None else clock
        self._now = utc_now if now is None else now
        self._last: float | None = None
        #: Every ``DURING_F2`` alert observed, in order. Shared with the run's own list when one
        #: is supplied, so the alerts land chronologically among the phase boundaries.
        self.observations: list[CapacityObservation] = [] if record_into is None else record_into
        #: The D138-R10 evidence, once a hard stop has fired. Held here as well as on the
        #: exception so it survives both the rollback and the unwinding.
        self.hard_stop_record: Mapping[str, object] | None = None
        #: How many readings were actually taken. Proves the loop is sampled, not merely wrapped.
        self.samples = 0

    def __call__(self) -> None:
        """Sample if the interval has elapsed, and abort F2 if the floor is reached.

        Raises:
            F2CapacityHardStopError: free space is at or below the `10` GiB floor, or could not
                be measured. Raised while the F2 transaction is still open, so it rolls back.
        """
        tick = self._clock()
        if self._last is not None and (tick - self._last) < self._interval:
            return
        self._last = tick
        self._sample()

    def _sample(self) -> None:
        observed_at = self._now()
        self.samples += 1
        try:
            free, total = self._free_space(self._root)
        except (OSError, ExternalWorkingRootError) as exc:
            raise self._hard_stop(
                reason=F2_MEASUREMENT_FAILED_REASON,
                free_bytes=None,
                measurement_error=type(exc).__name__,
                observed_at=observed_at,
                detail=(
                    f"free space during F2 could not be measured ({type(exc).__name__}); an "
                    "unmeasurable volume is not a volume that passed, so F2 is aborted"
                ),
            ) from exc
        state = f2_capacity_state(free)
        if state == F2_HARD_STOP_STATE:
            raise self._hard_stop(
                reason=F2_HARD_STOP_REASON,
                free_bytes=free,
                measurement_error=None,
                observed_at=observed_at,
                detail=(
                    f"{free} bytes free during F2, at or below the continuous hard floor of "
                    f"{F2_HARD_FLOOR_FREE_BYTES} bytes "
                    f"({F2_HARD_FLOOR_FREE_BYTES // 1024**3} GiB)"
                ),
            )
        if state == F2_ALERT_STATE:
            self.observations.append(
                CapacityObservation(
                    phase="DURING_F2",
                    free_bytes=free,
                    total_bytes=total,
                    volume=self._volume,
                    database_bytes=None,
                    wal_bytes=None,
                    temp_bytes=None,
                    observed_at=observed_at,
                )
            )

    def _hard_stop(
        self,
        *,
        reason: str,
        free_bytes: int | None,
        measurement_error: str | None,
        observed_at: str,
        detail: str,
    ) -> F2CapacityHardStopError:
        """Build the D138-R10 evidence and the exception that carries it out of the rollback."""
        record: dict[str, object] = {
            "phase": "DURING_F2",
            "hard_stop_reason": reason,
            "free_bytes": free_bytes,
            "measurement_error": measurement_error,
            "threshold_bytes": F2_HARD_FLOOR_FREE_BYTES,
            "observed_at": observed_at,
            "volume": None if self._volume is None else dict(self._volume.as_record()),
            "f2_transaction_rolled_back": True,
            "f2_committed": False,
        }
        self.hard_stop_record = record
        message = (
            f"{detail}. F2 IS ABORTED FROM INSIDE ITS OWN TRANSACTION, WHICH ROLLS BACK: the "
            "in-flight association projection is DISCARDED, NOT TRUNCATED, and no partial F2 "
            "association state is committed. Nothing was deleted, signalled, or cleaned"
        )
        return F2CapacityHardStopError(message, record=record)
