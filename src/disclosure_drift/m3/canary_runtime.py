"""Host-level runtime control for one corrected complete-source canary.

**What this module is for.** Everything the corrected canary needs from the *host* rather than
from the volume, the catalog, or the parse: where its runtime control files live, whether another
canary is already running, whether the process a stop command is about to signal really is the
canary, whether the machine's power and lid state permit a thirty-hour run, and -- after a
failure -- exactly which paths would be eligible for disposal if the owner ever authorized any.

**Why it is a module of its own.** The D139 review's findings split cleanly in two.
:mod:`~disclosure_drift.m3.external_working_root` answers questions about *the volume*: which one
is this, how much room is left, is the archive intact. Nothing here asks any of those. Forcing a
host-level ``flock``, a ``pmset`` reading, and a process-identity check into that module would put
four unrelated subsystems behind one import and make each harder to reason about; forcing them
into :mod:`~disclosure_drift.m3.single_source_canary` would put them inside the run they exist to
constrain from outside.

**It starts nothing and authorizes nothing.** Every function here refuses, reports, or returns a
handle. None creates a world, a run identity, a launch receipt, or an execution namespace, and
none carries or implies the owner instrument a corrected complete-source canary still needs.
Nothing here deletes anything, on any path, ever.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.storage.sqlite import utc_now

__all__ = [
    "CANARY_EXECUTION_LOCK_RELATIVE_PATH",
    "CANARY_RUNTIME_RELATIVE_PATH",
    "AuthenticatedCanaryProcess",
    "CanaryExecutionLock",
    "CanaryRuntimeError",
    "PowerState",
    "ReclaimReadiness",
    "acquire_canary_execution_lock",
    "authenticate_canary_process",
    "canary_execution_lock_path",
    "canary_runtime_directory",
    "failed_world_reclaim_readiness",
    "read_pid_record",
    "require_internal_runtime_path",
    "require_launch_power_conditions",
    "free_bytes",
    "power_state",
    "runtime_directory_for",
    "write_pid_record",
]


class CanaryRuntimeError(DisclosureDriftError):
    """Raised when a host-level runtime precondition for the corrected canary does not hold."""


# --------------------------------------------------------------------------- #
# Where runtime control lives -- D140-R10 (MINOR-4)
# --------------------------------------------------------------------------- #
#: The internal runtime/evidence directory, relative to the accepted private evidence root.
#:
#: **D140-R10.** The accepted launcher wrote its pid file wherever it was told, and the runbook
#: told it ``<WORK_ROOT>/canary.pid`` -- so the very first thing a launch did was create a file on
#: the external volume, *before* the application's safety envelope had run at all. That inverts
#: the order the envelope exists to impose. Runtime control now lives on **internal** storage,
#: independent of the working root, and the run's own admission is what decides whether the
#: external volume is ever touched.
#:
#: It is also where D140-R6 requires stdout, stderr, the resource report and the pid record to
#: live, so that a failure diagnosis survives the pane, the process, and the volume.
CANARY_RUNTIME_RELATIVE_PATH: Final = "runs/m3_3_canary_runtime"

#: The **host-level** complete-source canary execution lock, relative to the private root.
#:
#: **D140-R16.** One path for every run, deliberately: a per-run lock would let two canaries with
#: different ``--run-id`` values execute at once, which is exactly the case the D139 review raised
#: as MINOR-6. It is not a second writer-lease architecture -- it holds no state, adopts nothing,
#: recovers nothing, and grants no authority. It answers one question: *is a complete-source
#: canary already running on this host?*
CANARY_EXECUTION_LOCK_RELATIVE_PATH: Final = "locks/m3_3_complete_source_canary.lock"

_DIRECTORY_MODE: Final = 0o700
_FILE_MODE: Final = 0o600

_RUN_ID_PATTERN: Final = re.compile(r"\A[a-z0-9][a-z0-9_-]{0,127}\Z")


def canary_runtime_directory(private_root: Path) -> Path:
    """The internal runtime/evidence directory, created at ``0700`` if absent."""
    directory = private_root / CANARY_RUNTIME_RELATIVE_PATH
    directory.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    return directory


def runtime_directory_for(private_root: Path, run_id: str) -> Path:
    """One run's internal runtime directory. Created if absent; never on the external volume.

    Raises:
        CanaryRuntimeError: ``run_id`` is not a lawful run identity.
    """
    if not _RUN_ID_PATTERN.match(run_id):
        message = (
            f"run identity {run_id!r} is not lawful, so no runtime directory is derived from "
            "it; an identity that cannot be validated is refused rather than sanitized"
        )
        raise CanaryRuntimeError(message)
    directory = canary_runtime_directory(private_root) / run_id
    directory.mkdir(mode=_DIRECTORY_MODE, exist_ok=True)
    return directory


def require_internal_runtime_path(
    candidate: Path,
    *,
    work_root: Path,
    archive: Path | None = None,
) -> Path:
    """Return ``candidate`` resolved, or refuse it as a runtime-control location -- D140-R10.

    Three refusals, each on resolved, case-folded components so that ``..``, a symlink, and a
    case variant cannot launder any of them:

    * the path is **inside the proposed work root** -- the D139 MINOR-4 case exactly. A pid or
      log file written there lands on the external volume before the envelope has admitted it,
      and lands *inside the disposable world's tree*, where a later disposal would take the
      failure diagnosis with it;
    * the path **is, or is inside, the immutable D130 archive**;
    * the path is the work root itself.

    Raises:
        CanaryRuntimeError: the path is not a lawful runtime-control location.
    """
    resolved = Path(os.path.realpath(candidate))
    parts = _comparable(resolved)
    root_parts = _comparable(work_root)
    if parts == root_parts or _within(root_parts, parts):
        message = (
            "a canary runtime-control file may not be written beneath the working root. The "
            "working root is on the external volume and has not been admitted when the "
            "launcher runs, and it is the tree a disposal would remove -- so a pid file, a log "
            "or a status record placed there is both premature and destructible. Runtime "
            "control belongs on internal storage"
        )
        raise CanaryRuntimeError(message)
    if archive is not None:
        archive_parts = _comparable(archive)
        if parts == archive_parts or _within(archive_parts, parts):
            message = (
                "a canary runtime-control file may not be written inside the immutable D130 "
                "archive; it is the only surviving copy of the D128 evidence and nothing is "
                "written into it"
            )
            raise CanaryRuntimeError(message)
    return resolved


def _comparable(path: Path) -> tuple[str, ...]:
    return tuple(part.casefold() for part in Path(os.path.realpath(path)).parts)


def _within(ancestor: tuple[str, ...], descendant: tuple[str, ...]) -> bool:
    return len(descendant) > len(ancestor) and descendant[: len(ancestor)] == ancestor


# --------------------------------------------------------------------------- #
# The host-level execution lock -- D140-R16 (MINOR-6)
# --------------------------------------------------------------------------- #
def canary_execution_lock_path(private_root: Path) -> Path:
    """The one host-level canary execution lock path."""
    path = private_root / CANARY_EXECUTION_LOCK_RELATIVE_PATH
    path.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    return path


class CanaryExecutionLock:
    """An exclusive, non-blocking, host-level lock on *running a complete-source canary*.

    **``flock`` and nothing else decides.** The file's contents are informational only: a
    process that died without cleaning up leaves its metadata behind, and that stale text must
    never be what blocks the next run -- the D139 review named that requirement explicitly. The
    kernel releases an ``flock`` when the holding process dies, whatever it left in the file, so
    "is a canary running?" is answered by attempting the lock rather than by reading anything.

    Held for the complete execution lifetime by holding the descriptor open. Released on
    :meth:`release`, on context-manager exit, and by the operating system on process death.
    """

    __slots__ = ("_descriptor", "path")

    def __init__(self, path: Path) -> None:
        self.path = path
        self._descriptor: int | None = None

    def acquire(self, *, detail: Mapping[str, object] | None = None) -> CanaryExecutionLock:
        """Take the lock, or refuse because another canary holds it.

        Raises:
            CanaryRuntimeError: another process holds the lock, or it could not be opened.
        """
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_RDWR, _FILE_MODE)
        except OSError as exc:
            message = (
                f"the canary execution lock could not be opened ({type(exc).__name__}); a lock "
                "that cannot be taken is not a lock that was free, so the run is refused"
            )
            raise CanaryRuntimeError(message) from exc
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(descriptor)
            message = (
                "another complete-source canary is already running on this host and holds the "
                "execution lock. At most one runs at a time, whatever its run identity: two "
                "concurrent runs would share one volume's free space while each measured it as "
                "though it were alone, and every capacity floor in the envelope would be wrong "
                "in the one direction that matters. This run is refused and nothing was started"
            )
            raise CanaryRuntimeError(message) from exc
        self._descriptor = descriptor
        payload = dict(detail or {})
        payload["acquired_at"] = utc_now()
        payload["pid"] = os.getpid()
        try:
            os.ftruncate(descriptor, 0)
            os.lseek(descriptor, 0, os.SEEK_SET)
            os.write(descriptor, json.dumps(payload, sort_keys=True).encode("utf-8"))
            os.fsync(descriptor)
        except OSError:  # pragma: no cover - the lock is held either way
            # Informational only. Failing to record who holds the lock does not un-hold it, and
            # refusing here would turn a cosmetic problem into a stopped run.
            pass
        return self

    def release(self) -> None:
        """Release the lock. Idempotent, and it never removes the lock file.

        Unlinking would be the classic race: another process may already have opened the same
        path and be about to lock the inode this one is deleting.
        """
        descriptor = self._descriptor
        if descriptor is None:
            return
        self._descriptor = None
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    @property
    def held(self) -> bool:
        """Whether this object currently holds the lock."""
        return self._descriptor is not None

    def __enter__(self) -> CanaryExecutionLock:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()


def acquire_canary_execution_lock(
    private_root: Path, *, detail: Mapping[str, object] | None = None
) -> CanaryExecutionLock:
    """Acquire the one host-level canary execution lock -- D140-R16.

    Raises:
        CanaryRuntimeError: another complete-source canary already holds it.
    """
    return CanaryExecutionLock(canary_execution_lock_path(private_root)).acquire(detail=detail)


# --------------------------------------------------------------------------- #
# Exact-process authentication for the stop path -- D140-R18 (INFO-6)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class AuthenticatedCanaryProcess:
    """One process proved to be *this* canary, by its pid record and its own argument vector."""

    pid: int
    run_id: str
    executable: str
    argv: tuple[str, ...]


def read_pid_record(path: Path) -> int:
    """Read the exact process id from a canonical pid record.

    Raises:
        CanaryRuntimeError: the record is absent, unreadable, or does not hold a single
            targetable process id.
    """
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        message = (
            f"the canary pid record could not be read ({type(exc).__name__}); the stop path "
            "reads the exact process id from that record and never searches for a process"
        )
        raise CanaryRuntimeError(message) from exc
    try:
        pid = int(raw)
    except ValueError as exc:
        message = (
            "the canary pid record does not hold a single integer process id; an unreadable "
            "record is refused rather than guessed at"
        )
        raise CanaryRuntimeError(message) from exc
    if pid <= 1:
        message = (
            f"the canary pid record holds {pid}, which is not a single targetable process. "
            "os.kill reads 0 as the caller's own process group and a negative value as a "
            "process group or a broadcast, and pid 1 is not a canary"
        )
        raise CanaryRuntimeError(message)
    return pid


def write_pid_record(path: Path, pid: int) -> Path:
    """Record the exact process id the stop path will authenticate and signal -- D140-R10.

    Written at ``0600`` into the **internal** runtime directory. The launcher writes it before
    ``exec``, because ``exec`` keeps the process id: the value recorded is the id of the process
    that ends up doing the work, rather than a link of a chain guessed at afterwards from
    ``tmux`` or ``ps``. D128 is what guessing costs.

    Raises:
        CanaryRuntimeError: the record could not be written.
    """
    try:
        path.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, _FILE_MODE)
        try:
            os.write(descriptor, f"{pid}\n".encode())
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        message = (
            f"the canary pid record could not be written ({type(exc).__name__}); without it the "
            "stop path would have to search for a process, which is what Decision 140 removes"
        )
        raise CanaryRuntimeError(message) from exc
    return path


def process_argv(pid: int) -> tuple[str, ...]:
    """One process's argument vector, read from ``ps``.

    Raises:
        CanaryRuntimeError: the command line could not be read at all.
    """
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, integer pid
            ["/bin/ps", "-ww", "-o", "args=", "-p", str(pid)],
            capture_output=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        message = (
            f"the command line of process {pid} could not be read ({type(exc).__name__}); an "
            "unauthenticated process is never signalled in a canary's name"
        )
        raise CanaryRuntimeError(message) from exc
    text = completed.stdout.decode("utf-8", errors="replace").strip()
    if not text:
        message = (
            f"process {pid} reports no command line, so it cannot be authenticated as the "
            "canary; no signal is sent"
        )
        raise CanaryRuntimeError(message)
    return tuple(text.split())


def authenticate_canary_process(
    *,
    pid_file: Path,
    run_id: str,
    expected_executables: Sequence[str] = ("disclosure-drift", "python", "python3", "python3.12"),
    subcommand: Sequence[str] = ("m3", "canary-source"),
    argv_provider: Callable[[int], Sequence[str]] | None = None,
) -> AuthenticatedCanaryProcess:
    """Prove that the process named by ``pid_file`` is this canary -- D140-R18.

    The D139 review's **INFO-6**: the accepted stop path authenticated with
    ``--expect-command "m3 canary-source"``, a **substring** test against a command line. An
    operator shell that had merely *typed* that command carries the text in its own command
    line, so the decoy authenticates perfectly -- and a substring cannot tell a process that
    **is** the canary from one that merely mentions it.

    Four conditions, and the first is what makes the rest sound:

    1. the process id comes from the **canonical pid record** and from nowhere else. Nothing is
       scanned, so no decoy can be *selected* however convincing it looks;
    2. ``argv[0]``'s basename is one of ``expected_executables``. This is the condition the
       decoy fails: a shell running the text has ``argv[0]`` of ``zsh``, ``bash`` or ``sh``,
       whatever the rest of its command line says;
    3. the ``subcommand`` tokens appear **adjacent and in order**;
    4. ``--run-id`` is followed by **exactly** this run's identity, so a different canary's
       process is never stopped in this one's name.

    Raises:
        CanaryRuntimeError: any condition does not hold. No signal is sent by this function --
            it authenticates and returns, and signalling is the caller's separate step.
    """
    pid = read_pid_record(pid_file)
    argv = process_argv(pid) if argv_provider is None else tuple(argv_provider(pid))
    if not argv:  # pragma: no cover - process_argv already refuses an empty command line
        message = f"process {pid} reports no command line and is not authenticated"
        raise CanaryRuntimeError(message)
    executable = Path(argv[0].lstrip("-")).name
    if executable not in set(expected_executables):
        message = (
            f"process {pid} runs {executable!r}, which is not a canary executable. The pid "
            "record names this process, so a mismatch means the id has been reused or the "
            "record is stale -- and a shell that merely quotes the canary's command line is "
            "exactly what this refuses. No signal was sent"
        )
        raise CanaryRuntimeError(message)
    tokens = list(subcommand)
    if not _contains_adjacent(argv, tokens):
        message = (
            f"process {pid} does not carry the canary subcommand {' '.join(tokens)!r} as "
            "adjacent arguments; it is not authenticated and no signal was sent"
        )
        raise CanaryRuntimeError(message)
    if not _contains_adjacent(argv, ["--run-id", run_id]):
        message = (
            f"process {pid} does not carry --run-id {run_id!r}; a canary is never stopped in "
            "another run's name, so no signal was sent"
        )
        raise CanaryRuntimeError(message)
    return AuthenticatedCanaryProcess(pid=pid, run_id=run_id, executable=executable, argv=argv)


def _contains_adjacent(argv: Sequence[str], tokens: Sequence[str]) -> bool:
    """Whether ``tokens`` appear consecutively and in order inside ``argv``."""
    span = len(tokens)
    if span == 0 or len(argv) < span:  # pragma: no cover - callers pass non-empty tokens
        return False
    return any(
        list(argv[index : index + span]) == list(tokens) for index in range(len(argv) - span + 1)
    )


# --------------------------------------------------------------------------- #
# Power and lid state -- D140-R20 (INFO-8)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class PowerState:
    """What the host reports about its power source and lid, each of which may be unknown."""

    on_ac_power: bool | None
    clamshell_closed: bool | None

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "on_ac_power": self.on_ac_power,
            "clamshell_closed": self.clamshell_closed,
        }


def _pmset_ac_power() -> bool | None:
    """Whether the host is drawing from AC, or ``None`` when it cannot be read."""
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
            ["/usr/bin/pmset", "-g", "ps"], capture_output=True, check=False, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = completed.stdout.decode("utf-8", errors="replace")
    if "AC Power" in text:
        return True
    if "Battery Power" in text:
        return False
    return None


def _ioreg_clamshell_closed() -> bool | None:
    """Whether the lid is closed, or ``None`` when the host does not report a clamshell."""
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
            ["/usr/sbin/ioreg", "-r", "-k", "AppleClamshellState", "-d", "4"],
            capture_output=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = completed.stdout.decode("utf-8", errors="replace")
    match = re.search(r'"AppleClamshellState"\s*=\s*(Yes|No)', text)
    if match is None:
        return None
    return match.group(1) == "Yes"


def power_state() -> PowerState:
    """Read the host's power source and lid state, each fail-soft to ``None``.

    Reading is deliberately separated from deciding: an unknown reading is a fact about the
    host, and :func:`require_launch_power_conditions` is where the policy about unknowns lives.
    """
    return PowerState(on_ac_power=_pmset_ac_power(), clamshell_closed=_ioreg_clamshell_closed())


def require_launch_power_conditions(
    *,
    state: PowerState | None = None,
    operator_asserts_power_conditions: bool = False,
) -> PowerState:
    """Refuse a thirty-hour launch on battery or with the lid shut -- D140-R20.

    **What this can and cannot do.** ``caffeinate`` holds power assertions; it does **not**
    prevent an ordinary MacBook lid-close from sleeping the machine, and nothing in software
    does. The D139 review's **INFO-8** is therefore resolved as an explicit *launch condition*
    rather than as a mechanism: the conditions are checked at launch, stated in the runbook, and
    remain the operator's to maintain for the whole run.

    Two refusals and one escape hatch:

    * the host reports **battery power** -> refused;
    * the host reports the lid **closed** -> refused;
    * either reading is **unknown** -> refused, *unless* the operator explicitly asserts the
      conditions. Unknown is not admitted silently, because on this host both readings are
      normally available and their absence means something changed.

    Raises:
        CanaryRuntimeError: the conditions do not hold, or are unknown and unasserted.
    """
    observed = power_state() if state is None else state
    if observed.on_ac_power is False:
        message = (
            "the host is running on battery power. A corrected complete-source canary runs for "
            "upwards of thirty hours and must stay on AC for all of it; the run is refused"
        )
        raise CanaryRuntimeError(message)
    if observed.clamshell_closed is True:
        message = (
            "the host reports its lid closed. caffeinate holds power assertions but does not "
            "prevent lid-close sleep, and a sleeping host with an external SQLite volume "
            "attached is exactly the failure this refuses in advance. The lid must stay open "
            "for the whole run unless the machine is in a separately proven clamshell setup"
        )
        raise CanaryRuntimeError(message)
    unknown = observed.on_ac_power is None or observed.clamshell_closed is None
    if unknown and not operator_asserts_power_conditions:
        message = (
            "the host's power source or lid state could not be read, and an unreadable "
            "condition is not a satisfied one. Either make both readable, or state the "
            "conditions explicitly -- on AC power, lid open, and staying that way -- as an "
            "operator assertion. Nothing is assumed on the operator's behalf"
        )
        raise CanaryRuntimeError(message)
    return observed


# --------------------------------------------------------------------------- #
# Failed-world reclaim readiness -- D140-R19 (INFO-7)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ReclaimReadiness:
    """What a failed disposable world is, and what *would* be eligible for disposal.

    **It deletes nothing**, and holding one is not an authorization to delete anything. Decision
    140 resolves the D139 review's **INFO-7** by making the post-failure position legible rather
    than by pretending the physical constraint behind it has gone: a late failure can leave a
    ~120 GiB world behind, and 185 GiB is then not available for a fresh attempt without
    reclaiming it. Disposal stays owner-gated.
    """

    run_id: str
    world_present: bool
    result_present: bool
    prefix_result_present: bool
    world_bytes: int | None
    database_bytes: int | None
    wal_bytes: int | None
    disposable_paths: tuple[str, ...]
    runtime_evidence: tuple[str, ...]
    observed_at: str

    @property
    def reclaim_ready(self) -> bool:
        """Whether this world is unambiguously a failed, disposable one.

        A world carrying a normal success result is **not** reclaim-ready: it is a completed
        run, and its evidence is the point of having done it.
        """
        return self.world_present and not self.result_present

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering. Paths are relative names, never absolute ones."""
        return {
            "run_id": self.run_id,
            "world_present": self.world_present,
            "result_present": self.result_present,
            "prefix_result_present": self.prefix_result_present,
            "world_bytes": self.world_bytes,
            "database_bytes": self.database_bytes,
            "wal_bytes": self.wal_bytes,
            "disposable_paths": list(self.disposable_paths),
            "runtime_evidence": list(self.runtime_evidence),
            "failed_world_reclaim_ready": self.reclaim_ready,
            "observed_at": self.observed_at,
            "deleted_anything": False,
        }


def _tree_bytes(directory: Path) -> int | None:
    try:
        total = 0
        for entry in directory.rglob("*"):
            if entry.is_file() and not entry.is_symlink():
                total += entry.stat().st_size
    except OSError:
        return None
    return total


def _length(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def failed_world_reclaim_readiness(
    *,
    work_root: Path,
    run_id: str,
    runtime_directory: Path | None = None,
    result_filename: str,
    prefix_result_filename: str,
    working_catalog_filename: str,
    observed_at: str | None = None,
) -> ReclaimReadiness:
    """Report what a failed world is and what would be eligible for disposal -- D140-R19.

    **Deletes nothing.** It stats, it measures, it names, and it returns. The one path it ever
    reports as disposable is the exact world directory for this exact run identity: never the
    work root, never a sibling world, never the D130 archive, and never the source artifact.

    Raises:
        CanaryRuntimeError: ``run_id`` is not a lawful run identity.
    """
    if not _RUN_ID_PATTERN.match(run_id):
        message = f"run identity {run_id!r} is not lawful; no world is identified from it"
        raise CanaryRuntimeError(message)
    world = work_root / run_id
    present = world.is_dir() and not world.is_symlink()
    result = world / result_filename
    prefix_result = world / prefix_result_filename
    database = world / working_catalog_filename
    wal = world / f"{working_catalog_filename}-wal"
    evidence: list[str] = []
    if runtime_directory is not None and runtime_directory.is_dir():
        evidence = sorted(entry.name for entry in runtime_directory.iterdir() if entry.is_file())
    return ReclaimReadiness(
        run_id=run_id,
        world_present=present,
        result_present=result.is_file(),
        prefix_result_present=prefix_result.is_file(),
        world_bytes=_tree_bytes(world) if present else None,
        database_bytes=_length(database),
        wal_bytes=_length(wal),
        # The exact world for this exact identity, and nothing else. Named relative to the work
        # root so that no operator surface prints an absolute personal path.
        disposable_paths=(run_id,) if present and not result.is_file() else (),
        runtime_evidence=tuple(evidence),
        observed_at=utc_now() if observed_at is None else observed_at,
    )


def free_bytes(path: Path) -> int | None:
    """Free bytes on ``path``'s filesystem, or ``None``. Used only for reporting."""
    try:
        return shutil.disk_usage(path).free
    except OSError:
        return None
