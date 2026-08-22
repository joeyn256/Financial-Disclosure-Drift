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
The canary runs as the foreground command of its pane:

    tmux new-session -d -s SESSION \\
        '/ABS/REPO/.venv/bin/python /ABS/REPO/scripts/m3/canary_launch.py \\
             --pid-file /ABS/WORKROOT/canary.pid -- \\
             /ABS/REPO/.venv/bin/disclosure-drift m3 canary-source ...'

There is no ``&`` anywhere in that line. This script then **refuses to launch at all** if it
finds ``SIGINT`` already ignored, so a chain that reintroduces the D128 shape fails in the
first second instead of after thirty-three hours, and finally ``exec``s the real command, so
the process the watchdog signals is the process doing the work.

``exec`` matters twice over: it keeps the pane's process chain one process deep, and it
resets a handled signal to its default disposition in the new image while preserving an
ignored one. Passing the check and then ``exec``ing is therefore a proof that carries.

This script never launches anything by itself, holds no authority constant, reads no catalog,
takes no lease, and enables no network. It is a launcher.

Exit codes:
    ``3``  refused -- ``SIGINT`` is ignored, or the command is unusable. Nothing was started.
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


def write_pid_file(path: Path, pid: int) -> None:
    """Record the PID the watchdog must signal.

    Written **before** ``exec`` on purpose: ``exec`` replaces the process image and keeps the
    process id, so the value recorded here is the id of the process that ends up doing the
    work. Deriving it later from ``tmux`` or ``ps`` would mean guessing which link of the
    chain is the real one, and D128 is what guessing costs.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{pid}\n", encoding="utf-8")


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
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(resolved[0], resolved)  # noqa: S606 - resolved absolute path, no shell involved
    # Unreachable: a successful execv replaces this process image. Stated so the signature
    # stays honest rather than relying on a reader knowing that.
    return REFUSED  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
