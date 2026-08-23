#!/usr/bin/env python3
"""Launch a long-running M3.3 canary as the foreground process of its tmux pane.

**Why this file exists.** The D128 complete-source canary could not be stopped, and the
reason was the launch shape rather than the parser (accepted Decision 129 §9, D129-R10;
forensic result ``WATCHDOG_FALSE_ALERT_SIGNAL_NOT_DELIVERED_TO_CANARY``). The chain was a
non-interactive ``zsh`` that put the canary in the background with ``&``. POSIX requires a
shell without job control to start a background job with ``SIGINT`` and ``SIGQUIT`` set to
``SIG_IGN``, and CPython deliberately does **not** install its own ``SIGINT`` handler over an
inherited ``SIG_IGN``. Every later signal was therefore delivered to a process that had been
told, before it ever ran, to ignore it. The watchdog's ``kill`` returned success the whole
time, because ``kill`` reports that the signal was *sent*.

**The repair is the process chain, not the signal handling.** Nothing in the parser changes.
The canary runs as the foreground command of its pane, and **Decision 140** (D140-R6) fixes the
three things the D139 review found wrong with the shape around it:

    tmux new-session -d -s SESSION -e SQLITE_TMPDIR='/ABS/VOLUME/tmp' \\
        '/usr/bin/caffeinate -dims /usr/bin/time -l -o /ABS/INTERNAL/resource.log \\
             /ABS/REPO/.venv/bin/python /ABS/REPO/scripts/m3/canary_launch.py \\
                 --pid-file /ABS/INTERNAL/canary.pid \\
                 --stdout /ABS/INTERNAL/stdout.log \\
                 --stderr /ABS/INTERNAL/stderr.log \\
                 --work-root /ABS/VOLUME/WORKROOT \\
                 --require-sqlite-tmpdir -- \\
                 /ABS/REPO/.venv/bin/disclosure-drift m3 canary-source ...'

There is no ``&`` anywhere in that line.

**Why ``-e`` and not an exported variable.** ``SQLITE_TMPDIR`` exported in the launching shell
reaches the pane only when tmux starts a **new server**. Attaching to a server that is already
running gives the pane *that server's* environment, which was captured whenever it started -- so
the canary spills to the internal volume while the operator's shell shows the correct value.
``-e`` sets the variable on the session being created and does not depend on the server's age.

**Why ``caffeinate`` and ``time`` sit outside this script rather than in its ``exec``.** This
script records ``os.getpid()`` and then ``exec``s, so the recorded id is the id of the process
doing the work. If it ``exec``'d ``caffeinate`` instead, the pid file would name ``caffeinate``
and the accepted stop path would deliver ``SIGINT`` to a process that is not the canary --
reintroducing D128's defect by a different route. They are ancestors instead: ``caffeinate``
holds its assertions for the whole child lifetime, ``time -l`` reports the rusage of the process
it waited on, and the pid file still names the canary.

**``caffeinate -dims`` does not prevent lid-close sleep.** It asserts display, disk, idle-system
and user-active; a MacBook lid closing sleeps the machine anyway. That is a launch **condition**
in the runbook, not something this script can enforce -- see
:func:`disclosure_drift.m3.canary_runtime.require_launch_power_conditions`.

This script then **refuses to launch at all** if it finds ``SIGINT`` already ignored, so a
chain that reintroduces the D128 shape fails in the first second instead of after thirty-three
hours, and finally ``exec``s the real command, so the process the watchdog signals is the
process doing the work.

``exec`` matters twice over: it keeps the pane's process chain one process deep, and it
resets a handled signal to its default disposition in the new image while preserving an
ignored one. Passing the check and then ``exec``ing is therefore a proof that carries.

This script never launches anything by itself, holds no authority constant, reads no catalog,
takes no lease, and enables no network. It is a launcher.

Exit codes:
    ``3``  refused -- ``SIGINT`` is ignored, the command is unusable, a runtime-control path is
           not internal, or ``SQLITE_TMPDIR`` was required and is absent. Nothing was started.
    otherwise, whatever the exec'd command exits with, because this process became it.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import sys
from pathlib import Path

REFUSED: int = 3

SQLITE_TMPDIR_ENV: str = "SQLITE_TMPDIR"

UNSAFE_RUNTIME_PATH_REFUSAL: str = "LAUNCH_REFUSED_RUNTIME_PATH_NOT_INTERNAL"
"""Emitted when a pid, log or resource path would be written beneath the working root.

**D140-R10.** The accepted launcher wrote its pid file wherever the runbook told it, and the
runbook said ``<WORK_ROOT>/canary.pid`` -- so the first thing a launch did was create a file on
the external volume, *before* the application had authenticated the volume at all. It also put
the failure diagnosis inside the disposable tree, where a later disposal would take it.
"""

MISSING_TMPDIR_REFUSAL: str = "LAUNCH_REFUSED_SQLITE_TMPDIR_ABSENT"
"""Emitted when ``--require-sqlite-tmpdir`` is given and the variable is not in this environment.

The check is the proof that ``tmux -e`` actually reached the pane. Without it the shape fails
silently and SQLite spills to the internal volume for thirty hours.
"""

SIGINT_IGNORED_REFUSAL: str = "LAUNCH_REFUSED_SIGINT_IGNORED"
"""Emitted when the inherited ``SIGINT`` disposition is ``SIG_IGN``.

The exact D128 condition. A run started from here would be unstoppable by the accepted stop
mechanism, so it is not started.
"""


def sigint_is_ignored() -> bool:
    """Whether this process inherited ``SIGINT`` set to ``SIG_IGN``.

    CPython installs ``default_int_handler`` at startup **unless** the inherited disposition
    is ``SIG_IGN``, in which case it leaves it alone. So a plain read of the current handler
    distinguishes "a shell backgrounded us and disabled interrupts" from every healthy case.
    """
    return signal.getsignal(signal.SIGINT) is signal.SIG_IGN


def resolve_command(argv: list[str]) -> list[str]:
    """Return the command to exec with its executable resolved to an absolute path.

    Raises:
        ValueError: no command was given, or its executable cannot be found.
    """
    if not argv:
        message = "no command was given after '--'; there is nothing to launch"
        raise ValueError(message)
    executable = shutil.which(argv[0])
    if executable is None:
        message = f"command {argv[0]!r} was not found on PATH and cannot be launched"
        raise ValueError(message)
    return [executable, *argv[1:]]


def _comparable(path: Path) -> tuple[str, ...]:
    return tuple(part.casefold() for part in Path(os.path.realpath(path)).parts)


def is_inside(candidate: Path, ancestor: Path) -> bool:
    """Whether ``candidate`` is ``ancestor`` or lies beneath it, on resolved components.

    Component-wise on ``realpath`` output, so ``..``, a symlink and a case variant are all
    collapsed before anything is compared, and a sibling whose name merely *starts* with the
    ancestor's name is not mistaken for a child of it.
    """
    target = _comparable(candidate)
    root = _comparable(ancestor)
    return target == root or (len(target) > len(root) and target[: len(root)] == root)


def require_internal_runtime_paths(paths: list[Path], work_root: Path | None) -> None:
    """Refuse any runtime-control path that would land inside the working root -- D140-R10.

    Raises:
        ValueError: a path is inside the working root.
    """
    if work_root is None:
        return
    for path in paths:
        if is_inside(path, work_root):
            message = (
                "a runtime-control file would be written beneath the working root. The working "
                "root is on the external volume and has not been admitted when this script "
                "runs, and it is the tree a disposal would remove -- so a pid file, a log, or "
                "a resource report placed there is both premature and destructible. Put "
                "runtime control on internal storage"
            )
            raise ValueError(message)


def redirect_durably(stdout: Path | None, stderr: Path | None) -> None:
    """Point this process's stdout and stderr at files that outlive the pane -- D140-R6.

    Done **before** ``exec`` and with ``dup2``, so the exec'd image inherits the descriptors:
    the canary's output lands in the files whatever happens to the tmux pane, the terminal, or
    the ssh session. Opened for append, so a resumed or restarted launch never truncates the
    record of the one before it.

    The D139 review's point was narrow and correct: no required failure diagnosis may exist
    only in a pane's scrollback, because a pane closing takes it and a crash usually closes one.

    Raises:
        OSError: a log file could not be opened.
    """
    for path, stream in ((stdout, sys.stdout), (stderr, sys.stderr)):
        if path is None:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
        try:
            stream.flush()
            os.dup2(descriptor, stream.fileno())
        finally:
            os.close(descriptor)


def write_pid_file(path: Path, pid: int) -> None:
    """Record the PID the watchdog must signal.

    Written **before** ``exec`` on purpose: ``exec`` replaces the process image and keeps the
    process id, so the value recorded here is the id of the process that ends up doing the
    work. Deriving it later from ``tmux`` or ``ps`` would mean guessing which link of the
    chain is the real one, and D128 is what guessing costs.

    It belongs on **internal** storage (D140-R10): the stop path must be able to find the canary
    whether or not the external volume is still mounted, and a pid file inside the disposable
    world is removed by the disposal that makes finding it matter.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{pid}\n", encoding="utf-8")
    path.chmod(0o600)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="canary_launch.py",
        description=(
            "Refuse to start when SIGINT is ignored, record the launched PID, and exec the "
            "given command as the foreground process of this pane."
        ),
    )
    parser.add_argument(
        "--pid-file",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write this process's PID here before exec. The exec'd command keeps that PID.",
    )
    parser.add_argument(
        "--stdout",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Append this process's stdout here, before exec, so the canary's output survives "
            "the pane, the terminal and the process. Must not be inside --work-root."
        ),
    )
    parser.add_argument(
        "--stderr",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Append this process's stderr here, before exec. No required failure diagnosis may "
            "exist only in a pane's scrollback. Must not be inside --work-root."
        ),
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "The disposable working root the run will use. Given, every runtime-control path "
            "above is refused if it would land inside it (D140-R10). This script never creates, "
            "reads, writes or validates the working root itself -- the application does that."
        ),
    )
    parser.add_argument(
        "--require-sqlite-tmpdir",
        action="store_true",
        help=(
            "Refuse unless SQLITE_TMPDIR is set in THIS process's environment. It is the proof "
            "that 'tmux -e SQLITE_TMPDIR=...' actually reached the pane: an exported value does "
            "not reach a pane created on an already-running tmux server, and the failure is "
            "silent -- SQLite simply spills to the internal volume for the whole run."
        ),
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help=(
            "Report the inherited SIGINT disposition and exit without launching anything. "
            "The disposable positive control uses this; a real launch never does."
        ),
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        metavar="-- COMMAND [ARGS...]",
        help="The command to exec. Everything after '--' is passed through untouched.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ignored = sigint_is_ignored()
    if ignored:
        print(SIGINT_IGNORED_REFUSAL, file=sys.stderr)
        print(
            "SIGINT is set to SIG_IGN in this process, so the launched run could not be "
            "stopped by the accepted stop mechanism. Run the canary as the foreground "
            "command of its tmux pane and do not background it with '&'.",
            file=sys.stderr,
        )
        return REFUSED
    runtime_paths = [path for path in (args.pid_file, args.stdout, args.stderr) if path is not None]
    try:
        require_internal_runtime_paths(runtime_paths, args.work_root)
    except ValueError as exc:
        print(UNSAFE_RUNTIME_PATH_REFUSAL, file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return REFUSED
    if args.require_sqlite_tmpdir and not os.environ.get(SQLITE_TMPDIR_ENV, "").strip():
        print(MISSING_TMPDIR_REFUSAL, file=sys.stderr)
        print(
            f"{SQLITE_TMPDIR_ENV} is not set in this process. It is injected per pane with "
            "'tmux new-session -e SQLITE_TMPDIR=...'; exporting it in the launching shell does "
            "not reach a pane created on an already-running tmux server. Nothing was started.",
            file=sys.stderr,
        )
        return REFUSED
    if args.check_only:
        print("SIGINT_NOT_IGNORED")
        return 0

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    try:
        resolved = resolve_command(command)
    except ValueError as exc:
        print(f"LAUNCH_REFUSED_UNUSABLE_COMMAND: {exc}", file=sys.stderr)
        return REFUSED

    if args.pid_file is not None:
        write_pid_file(args.pid_file, os.getpid())
    try:
        redirect_durably(args.stdout, args.stderr)
    except OSError as exc:
        print(f"LAUNCH_REFUSED_UNWRITABLE_LOG: {type(exc).__name__}", file=sys.stderr)
        return REFUSED
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(resolved[0], resolved)  # noqa: S606 - resolved absolute path, no shell involved
    # Unreachable: a successful execv replaces this process image. Stated so the signature
    # stays honest rather than relying on a reader knowing that.
    return REFUSED  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
