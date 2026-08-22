#!/usr/bin/env python3
"""The corrected M3.3 canary watchdog: verified stops, exact-PID probes, honest stalls.

Watchdog v1 was wrong in three separable ways during D128, and this file repairs each of
them separately (accepted Decision 129 §9, D129-R10 and D129-R11).

**1. A sent signal was reported as a stop.** ``kill`` succeeds when the signal is *delivered
to the kernel*, which says nothing about whether the target acted on it -- and the D128
target had ``SIGINT`` set to ``SIG_IGN`` before it started, so it never could. :func:`stop`
therefore sends the signal and then **watches the process actually go away**. If it is still
alive when the wait expires, the result is :data:`STOP_FAILED` and the watchdog says so.
It never escalates to ``SIGTERM`` or ``SIGKILL``: escalation would turn "we cannot stop this
cleanly" into a hard kill of a governed run mid-write, which is a different and worse
outcome, and the decision to do that belongs to the operator.

**2. The network probe could answer about the wrong process.** ``lsof`` treats bare selectors
as a union, so ``lsof -nP -p PID -i`` reports every internet file on the machine *or* every
file of that PID. The intersection form is ``-a``, and :func:`network_probe_command` is the
only place the argument vector is written down.

**3. No member growth was read as a stall forever.** Member-count stall detection is a
statement about *traversal*, and traversal ends long before the run does: F1, F2, and
finalization all run with the member count already final and correctly unchanging. Calling
that a stall is a false alert, and D128 produced one. :func:`member_stall_verdict` therefore
disables member-count alerting once the governed member count is reached. It invents no
replacement rule -- there is deliberately no wall-clock kill for F1 or F2 here -- and it
issues no query against the live working catalog: the counts are inputs.

Three further hardenings, each closing a way this file could have reported something untrue:

**4. An empty ``--expect-command`` authenticated nothing.** ``"" in observed`` is true of every
string, so an empty expectation turned the guard against a reused process id into a guard that
always passes -- while still *looking* like the target had been authenticated. It is now a
specific refusal, :data:`STOP_REFUSED_EMPTY_EXPECT`, and no signal is sent.

**5. The target could exit between the liveness check and the signal.** :func:`stop` proves the
process is alive and then signals it, and those are two syscalls with a gap. A target that
exits inside that gap made ``os.kill`` raise ``ProcessLookupError`` out of the watchdog as a
traceback. It is now :data:`STOP_ALREADY_GONE`: the target is gone, which is the outcome that
was wanted. ``PermissionError`` is **not** folded into that -- a signal we were not allowed to
send is a stop that did not happen, and it reports :data:`STOP_FAILED_PERMISSION`.

**6. ``observed > governed`` was silently read as a completed traversal.** More members seen
than the plan governs is not progress and not completion; it means the observed count and the
governed count do not describe the same thing. That is now its own verdict,
:data:`TRAVERSAL_INCONSISTENT`. Member-stall timing is disabled with it -- ordinary stall
semantics presuppose a bound the count has not passed -- and, exactly as for the completion
case, no kill rule is invented and no query is issued against the working catalog.

**7. A non-positive process id was taken at face value.** ``os.kill`` gives ``0`` and negative
ids a *different meaning* from "this process": ``0`` signals every process in the caller's own
process group -- run from the canary's pane, that is the canary and this watchdog together --
and ``-1`` signals every process the user is permitted to signal at all. ``lsof -p`` has the
same problem in the reading direction. Both are broadcasts wearing a process id's clothes, and
one mistyped ``--pid`` was enough to reach either. The domain is now stated once, in
:func:`non_targetable_pid_detail`, and both PID-taking operations refuse it before any
inspection: nothing is read about the process, and nothing is sent to it.

Nothing in this file reads a catalog, holds an authority constant, enables network, or
touches evidence. It signals one process id and reports what happened.

Exit codes:
    ``0``  the requested check passed, or the stop was confirmed.
    ``2``  a stall alert is raised (``stall``).
    ``3``  refused before acting -- the process id is not a single target, the target does not
           match its expected command, or the expectation itself was unusable.
    ``4``  the stop did not happen: :data:`STOP_FAILED`, or :data:`STOP_FAILED_PERMISSION`.
    ``5``  :data:`TRAVERSAL_INCONSISTENT` -- observed and governed member counts disagree in
           a way no stall or completion verdict can describe.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Final

ALERT_EXIT: Final = 2
REFUSED_EXIT: Final = 3
STOP_FAILED_EXIT: Final = 4
INCONSISTENT_EXIT: Final = 5

STOP_CONFIRMED: Final = "STOP_CONFIRMED"
STOP_FAILED: Final = "STOP_FAILED"
STOP_FAILED_PERMISSION: Final = "STOP_FAILED_SIGNAL_NOT_PERMITTED"
STOP_REFUSED: Final = "STOP_REFUSED_TARGET_MISMATCH"
STOP_REFUSED_EMPTY_EXPECT: Final = "STOP_REFUSED_EMPTY_EXPECT_COMMAND"
STOP_REFUSED_NON_POSITIVE_PID: Final = "STOP_REFUSED_NON_POSITIVE_PID"
STOP_ALREADY_GONE: Final = "STOP_TARGET_ALREADY_GONE"

PROBE_REFUSED_NON_POSITIVE_PID: Final = "PROBE_REFUSED_NON_POSITIVE_PID"

TRAVERSAL_INCOMPLETE: Final = "TRAVERSAL_INCOMPLETE"
TRAVERSAL_STALLED: Final = "MEMBER_TRAVERSAL_STALLED"
TRAVERSAL_COMPLETE: Final = "MEMBER_TRAVERSAL_COMPLETE_STALL_MONITORING_DISABLED"
TRAVERSAL_UNKNOWN: Final = "MEMBER_TRAVERSAL_UNKNOWN"
TRAVERSAL_INCONSISTENT: Final = "MEMBER_COUNT_INCONSISTENT_STALL_MONITORING_DISABLED"

DEFAULT_STALL_SECONDS: Final = 1800
DEFAULT_STOP_TIMEOUT_SECONDS: Final = 120.0
DEFAULT_POLL_SECONDS: Final = 1.0


# --------------------------------------------------------------------------- #
# The process-id domain, stated once
# --------------------------------------------------------------------------- #
def non_targetable_pid_detail(pid: int) -> str | None:
    """Return why ``pid`` names no single process, or ``None`` when it names one.

    **The one place the domain is written down.** Both PID-taking operations read it, so
    "which process ids may this watchdog act on" has a single answer rather than one answer
    per call site that could later disagree.

    A non-positive process id is not a target at all. Signalling a pid of ``0`` reaches every
    process in the *caller's own process group*, which for a watchdog invoked from the
    canary's pane is the canary and the watchdog together; a pid of ``-1`` reaches every
    process the user is permitted to signal. ``lsof -p 0`` and ``lsof -p -1`` are the same
    mistake in the reading direction: an answer about a set is not an answer about a target.

    A watchdog whose entire contract is *act on exactly the process you named* must not let
    an unchecked ``--pid`` decide which of those meanings applies, so the whole non-positive
    domain is refused before anything is read about the process and before anything is sent
    to it. The check is on the argument, not on the world: it needs no syscall of its own.
    """
    if pid > 0:
        return None
    return (
        f"process id {pid} is not a single target. os.kill treats 0 as the caller's own "
        "process group and -1 as every process this user may signal, so a non-positive id "
        "names a broadcast rather than the canary. Nothing was inspected and nothing was "
        "signalled. Pass the process id canary_launch.py recorded in its --pid-file."
    )


# --------------------------------------------------------------------------- #
# Member-count stall monitoring (Decision 129 §9, D129-R11)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class StallVerdict:
    """One member-stall evaluation, with the reason it reached that state.

    ``alert`` and ``inconsistent`` are separate on purpose. ``alert`` means *this looks like a
    stall*; ``inconsistent`` means *the two counts do not describe the same traversal, so no
    stall or completion claim can be made about them at all*. Folding the second into the first
    would report an accounting problem as a stall, and folding it into ``alert=False`` would
    let it exit ``0`` and pass unseen in a script.
    """

    state: str
    alert: bool
    message: str
    inconsistent: bool = False


def member_stall_verdict(
    *,
    observed_members: int,
    governed_members: int,
    seconds_since_member_change: float,
    stall_seconds: float = DEFAULT_STALL_SECONDS,
    phase: str | None = None,
) -> StallVerdict:
    """Decide whether an unchanging member count is a stall.

    The rule hinges on completeness rather than elapsed time:

    * ``observed < governed`` -- traversal is still running, so a member count that has not
      moved for ``stall_seconds`` is a real stall and is alerted.
    * ``observed == governed`` -- traversal is finished. The member count is *supposed* to be
      frozen from here on, and everything the run still has to do (F1, F2, finalization,
      checkpointing) happens with it frozen. Member-count alerting is disabled outright; no
      substitute wall-clock rule replaces it.
    * ``observed > governed`` -- the counts disagree. A traversal cannot pass its own governed
      bound, so one of the two numbers is not describing what it is believed to describe: a
      stale governed count, a count read from the wrong run, or an observation that is not the
      member count at all. This is reported as :data:`TRAVERSAL_INCONSISTENT` rather than
      quietly treated as the completion case, which is what the previous ``>=`` did. Member-
      stall timing is disabled with it, because ordinary stall semantics presuppose a bound
      the count has not passed. **No kill rule is invented**, and the working catalog is not
      queried to adjudicate: the counts are inputs here and stay inputs.

    ``phase`` is an optional operator-supplied label used only to make the message more
    useful. It is never consulted to decide anything, so a wrong or absent label cannot turn
    an alert into a silence.
    """
    where = f" during {phase}" if phase else ""
    if governed_members <= 0:
        return StallVerdict(
            state=TRAVERSAL_UNKNOWN,
            alert=False,
            message=(
                "the governed member count is not known, so no member-count claim can be "
                "made; absence of a count is not evidence of progress or of a stall"
            ),
        )
    if observed_members > governed_members:
        return StallVerdict(
            state=TRAVERSAL_INCONSISTENT,
            alert=False,
            inconsistent=True,
            message=(
                f"observed member count {observed_members} exceeds the governed member count "
                f"{governed_members}{where}, which a traversal cannot do. The two counts do "
                "not describe the same traversal, so neither a stall nor a completion verdict "
                "applies and member-stall timing is disabled. This watchdog invents no kill "
                "rule and issues no query against the working catalog; establish which count "
                "is wrong before acting on either."
            ),
        )
    if observed_members == governed_members:
        return StallVerdict(
            state=TRAVERSAL_COMPLETE,
            alert=False,
            message=(
                f"member traversal is complete at {observed_members}/{governed_members}"
                f"{where}; an unchanging member count is now the expected state and is not "
                "a stall. This watchdog raises no wall-clock alert for post-traversal work."
            ),
        )
    if seconds_since_member_change >= stall_seconds:
        return StallVerdict(
            state=TRAVERSAL_STALLED,
            alert=True,
            message=(
                f"member traversal is incomplete at {observed_members}/{governed_members}"
                f"{where} and the count has not moved for "
                f"{seconds_since_member_change:.0f}s, which is at or beyond the "
                f"{stall_seconds:.0f}s threshold"
            ),
        )
    return StallVerdict(
        state=TRAVERSAL_INCOMPLETE,
        alert=False,
        message=(
            f"member traversal is progressing at {observed_members}/{governed_members}"
            f"{where}; last change {seconds_since_member_change:.0f}s ago"
        ),
    )


# --------------------------------------------------------------------------- #
# Network probe (Decision 129 §9)
# --------------------------------------------------------------------------- #
def network_probe_command(pid: int) -> list[str]:
    """The exact argument vector that asks "does *this* process hold an internet file".

    ``-a`` is the whole point. Without it ``lsof`` unions its selectors and answers a
    question nobody asked -- every internet file on the host, or every file of this PID --
    which is the form watchdog v1 used and the reason its network evidence was unusable.

    A non-positive ``pid`` is refused **before the vector is built**, so no ``lsof`` command
    naming one can exist to be run by accident. Selecting a process group or every signalable
    process would answer about a set, which is the same defect ``-a`` is here to remove.

    Raises:
        ValueError: ``pid`` is not a single target. See :func:`non_targetable_pid_detail`.
    """
    refusal = non_targetable_pid_detail(pid)
    if refusal is not None:
        raise ValueError(refusal)
    return ["lsof", "-nP", "-a", "-p", str(pid), "-i"]


# --------------------------------------------------------------------------- #
# Stopping, and proving it stopped (Decision 129 §9, D129-R10)
# --------------------------------------------------------------------------- #
def process_state(pid: int) -> str:
    """The target's process state letter, or an empty string when it cannot be read."""
    try:
        completed = subprocess.run(  # noqa: S603
            ["/bin/ps", "-o", "state=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout.strip()


def process_is_alive(pid: int) -> bool:
    """Whether a process id still names a *running* process.

    ``signal 0`` performs the permission and existence checks and delivers nothing, which is
    the right primitive — but it is not the whole answer. A process that has already exited
    stays visible to it as a **zombie** until its parent reaps it, and a watchdog run from the
    shell that started the canary is exactly the case where that parent has not got round to
    it yet. Reading a stop as failed because the corpse is still in the table would be the
    mirror image of D128's mistake: reporting the wrong outcome from a syscall that answered
    a slightly different question than the one being asked.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # It exists and belongs to somebody else. "Alive" is the truthful answer, and it is
        # also the safe one: reporting a stop we could not have caused would be worse.
        return True
    return not process_state(pid).startswith("Z")


def process_command(pid: int) -> str:
    """The target's command line, or an empty string when it cannot be read."""
    try:
        completed = subprocess.run(  # noqa: S603
            ["/bin/ps", "-o", "command=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout.strip()


@dataclass(frozen=True, slots=True)
class StopResult:
    """What one stop attempt did, and what the target actually did about it."""

    outcome: str
    pid: int
    signal_sent: bool
    waited_seconds: float
    detail: str


def stop(
    pid: int,
    *,
    expect_command: str | None = None,
    timeout_seconds: float = DEFAULT_STOP_TIMEOUT_SECONDS,
    poll_seconds: float = DEFAULT_POLL_SECONDS,
    now: object = None,
) -> StopResult:
    """Send ``SIGINT`` once and require the target to actually terminate.

    ``pid`` must name a single process. A non-positive id is refused first of all, with no
    syscall performed and :data:`STOP_REFUSED_NON_POSITIVE_PID` returned, because ``os.kill``
    would read it as a process group or a broadcast rather than as the canary.

    ``expect_command`` is a substring the target's command line must contain. It is a guard
    against signalling a process id that has been reused, and it fails closed: an unreadable
    or non-matching command line refuses rather than signals. ``None`` means *no expectation
    was stated*, which is a different thing from an expectation that matches everything --
    an empty or whitespace-only string is refused outright, because ``"" in observed`` holds
    for every process on the machine and would report an authentication that never happened.

    Liveness and the signal are two syscalls with a gap between them, so a target that exits
    inside that gap is normal rather than exceptional: ``ProcessLookupError`` from the signal
    means the process is gone, which is what was wanted, and it returns
    :data:`STOP_ALREADY_GONE`. ``PermissionError`` is not treated that way -- a signal that
    could not be sent is a stop that did not happen (:data:`STOP_FAILED_PERMISSION`).

    No escalation. A target that survives produces :data:`STOP_FAILED`, and the caller is
    told plainly that the run is still going. Turning that into ``SIGKILL`` would end a
    governed run mid-write on the watchdog's own authority.
    """
    clock = time.monotonic if now is None else now
    # First, and before ``process_is_alive``: the argument domain is checked with no syscall
    # at all, so a broadcast id is refused without this watchdog having read anything about
    # a process group or sent anything to one.
    pid_refusal = non_targetable_pid_detail(pid)
    if pid_refusal is not None:
        return StopResult(
            outcome=STOP_REFUSED_NON_POSITIVE_PID,
            pid=pid,
            signal_sent=False,
            waited_seconds=0.0,
            detail=pid_refusal,
        )
    if expect_command is not None and not expect_command.strip():
        return StopResult(
            outcome=STOP_REFUSED_EMPTY_EXPECT,
            pid=pid,
            signal_sent=False,
            waited_seconds=0.0,
            detail=(
                f"--expect-command was given as {expect_command!r}, which every command line "
                "contains. That authenticates nothing while looking as though it does, so no "
                "signal was sent. Pass a substring that actually identifies the canary, or "
                "omit the option to state no expectation at all."
            ),
        )
    if not process_is_alive(pid):
        return StopResult(
            outcome=STOP_ALREADY_GONE,
            pid=pid,
            signal_sent=False,
            waited_seconds=0.0,
            detail=f"process {pid} does not exist; nothing was signalled",
        )
    if expect_command is not None:
        observed = process_command(pid)
        if expect_command not in observed:
            return StopResult(
                outcome=STOP_REFUSED,
                pid=pid,
                signal_sent=False,
                waited_seconds=0.0,
                detail=(
                    f"process {pid} does not match the expected command {expect_command!r}; "
                    "no signal was sent, because a reused process id must never be stopped "
                    "in a canary's name"
                ),
            )
    started = clock()
    try:
        os.kill(pid, signal.SIGINT)
    except ProcessLookupError:
        # The target exited between the liveness check above and this signal. Nothing was
        # delivered, and nothing needed to be: the process is gone.
        return StopResult(
            outcome=STOP_ALREADY_GONE,
            pid=pid,
            signal_sent=False,
            waited_seconds=clock() - started,
            detail=(
                f"process {pid} exited between the liveness check and the signal; nothing "
                "was delivered and the target is already gone"
            ),
        )
    except PermissionError:
        # Never folded into "already gone": the process is there and we were not allowed to
        # signal it, so the stop did not happen and must not be reported as one.
        return StopResult(
            outcome=STOP_FAILED_PERMISSION,
            pid=pid,
            signal_sent=False,
            waited_seconds=clock() - started,
            detail=(
                f"SIGINT to process {pid} was not permitted, so no signal was delivered and "
                "the stop did NOT succeed. The process belongs to another user; return to "
                "the operator rather than escalating or retrying under another identity."
            ),
        )
    while True:
        if not process_is_alive(pid):
            waited = clock() - started
            return StopResult(
                outcome=STOP_CONFIRMED,
                pid=pid,
                signal_sent=True,
                waited_seconds=waited,
                detail=(
                    f"SIGINT was delivered to process {pid} and the process terminated "
                    f"after {waited:.2f}s"
                ),
            )
        waited = clock() - started
        if waited >= timeout_seconds:
            return StopResult(
                outcome=STOP_FAILED,
                pid=pid,
                signal_sent=True,
                waited_seconds=waited,
                detail=(
                    f"SIGINT was sent to process {pid} and it is still alive after "
                    f"{waited:.2f}s. The stop did NOT succeed. No escalation to SIGTERM or "
                    "SIGKILL is performed here; treat the run as still going and return to "
                    "the operator."
                ),
            )
        time.sleep(poll_seconds)


# --------------------------------------------------------------------------- #
# Operator surface
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="canary_watchdog.py",
        description="Stall evaluation, exact-PID network probe, and verified stop.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    stall = sub.add_parser("stall", help="Evaluate whether an unchanging member count is a stall.")
    stall.add_argument("--observed-members", type=int, required=True)
    stall.add_argument("--governed-members", type=int, required=True)
    stall.add_argument("--seconds-since-member-change", type=float, required=True)
    stall.add_argument("--stall-seconds", type=float, default=float(DEFAULT_STALL_SECONDS))
    stall.add_argument("--phase", default=None, help="Optional label; never used to decide.")

    probe = sub.add_parser("network-probe", help="Print or run the exact-PID lsof intersection.")
    probe.add_argument(
        "--pid",
        type=int,
        required=True,
        help="The single process to ask about. A non-positive id builds no command at all.",
    )
    probe.add_argument("--print-only", action="store_true")

    stopper = sub.add_parser("stop", help="Send SIGINT once and verify the target terminated.")
    stopper.add_argument(
        "--pid",
        type=int,
        required=True,
        help="The single process to stop. A non-positive id is refused, never broadcast.",
    )
    stopper.add_argument(
        "--expect-command",
        default=None,
        help=(
            "Substring the target's command line must contain. Omit it to state no "
            "expectation; an empty or whitespace-only value is refused, because it would "
            "match every process."
        ),
    )
    stopper.add_argument("--timeout-seconds", type=float, default=DEFAULT_STOP_TIMEOUT_SECONDS)
    stopper.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "stall":
        verdict = member_stall_verdict(
            observed_members=args.observed_members,
            governed_members=args.governed_members,
            seconds_since_member_change=args.seconds_since_member_change,
            stall_seconds=args.stall_seconds,
            phase=args.phase,
        )
        print(f"{verdict.state}: {verdict.message}")
        if verdict.inconsistent:
            return INCONSISTENT_EXIT
        return ALERT_EXIT if verdict.alert else 0
    if args.command == "network-probe":
        try:
            command = network_probe_command(args.pid)
        except ValueError as exc:
            # Refused before the vector exists, so there is nothing here that could be run.
            print(f"{PROBE_REFUSED_NON_POSITIVE_PID}: {exc}")
            return REFUSED_EXIT
        if args.print_only:
            print(" ".join(command))
            return 0
        completed = subprocess.run(command, check=False)  # noqa: S603
        return completed.returncode
    result = stop(
        args.pid,
        expect_command=args.expect_command,
        timeout_seconds=args.timeout_seconds,
        poll_seconds=args.poll_seconds,
    )
    print(f"{result.outcome}: {result.detail}")
    if result.outcome in {STOP_FAILED, STOP_FAILED_PERMISSION}:
        return STOP_FAILED_EXIT
    if result.outcome in {STOP_REFUSED, STOP_REFUSED_EMPTY_EXPECT, STOP_REFUSED_NON_POSITIVE_PID}:
        return REFUSED_EXIT
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
