"""Decision 131 Repairs D and E — actual SIGINT delivery, and honest stall monitoring.

**Repair D (accepted Decision 129 §9, D129-R10).** D128's watchdog reported that it had
stopped the canary. It had not, and could not have: the launch chain was a non-interactive
``zsh`` that backgrounded the run with ``&``, which POSIX requires to start the job with
``SIGINT`` set to ``SIG_IGN``, and CPython leaves an inherited ``SIG_IGN`` in place. Forensic
result ``WATCHDOG_FALSE_ALERT_SIGNAL_NOT_DELIVERED_TO_CANARY``.

Two things follow, and both are proved here rather than argued:

* the future launch shape — a tmux pane whose foreground command is
  ``scripts/m3/canary_launch.py``, which ``exec``s the run — must not inherit ``SIG_IGN``,
  and the launcher must **refuse** when it does;
* a successful ``kill`` is not a stop. The watchdog must watch the target actually terminate,
  and must report ``STOP_FAILED`` when it does not, without escalating to ``SIGTERM`` or
  ``SIGKILL``.

**Repair E (accepted Decision 129 §9, D129-R11).** Member-count stall detection is a claim
about traversal. Once the governed member count is reached the count is *supposed* to stop
moving, and F1, F2, and finalization all run in that state. Treating it as a stall is a false
alert, so member-count alerting is disabled at completion — and nothing invents a wall-clock
kill rule to replace it.

**Four hardenings**, each closing a way the watchdog could itself do or report something
other than what it claimed:

* an empty ``--expect-command`` made ``"" in observed`` true of every process, so the guard
  against a reused process id passed unconditionally while still looking like an
  authentication. It is now a specific refusal and no signal is sent;
* liveness and the signal are two syscalls with a gap. A target that exits inside that gap
  raised ``ProcessLookupError`` out of the watchdog as a traceback; it is now the
  already-gone outcome. ``PermissionError`` is deliberately *not* folded in — a signal that
  could not be sent is a stop that did not happen;
* ``observed > governed`` was read as an ordinary completed traversal. A traversal cannot
  pass its own governed bound, so the two counts do not describe the same thing: that is now
  its own verdict with member-stall timing disabled, no invented kill rule, and no query
  against the working catalog;
* a non-positive ``--pid`` was taken at face value, and ``os.kill`` reads ``0`` as the
  caller's process group and ``-1`` as every process the user may signal. One mistyped
  argument was enough to broadcast from an instrument whose contract is *exactly the process
  you named*. The domain is now refused on the argument, before any syscall, by one
  definition both PID-taking operations read.

Every process these tests start is disposable, lives under ``tmp_path``, and holds no handle
in any Disclosure Drift path. No test signals a canary, opens a catalog, or touches evidence.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PYTHON = sys.executable


def _load(name: str, relative: str) -> ModuleType:
    """Load a standalone operator tool as an importable module by file path.

    The module is registered in ``sys.modules`` *before* it is executed because
    ``@dataclass`` resolves its own module out of ``sys.modules`` while the class body is
    being processed, and an unregistered module makes that lookup return ``None``.
    """
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_watchdog = _load("canary_watchdog", "scripts/m3/canary_watchdog.py")
_launch = _load("canary_launch", "scripts/m3/canary_launch.py")

_LAUNCHER = _REPO_ROOT / "scripts/m3/canary_launch.py"
_WATCHDOG = _REPO_ROOT / "scripts/m3/canary_watchdog.py"

_TARGET_SOURCE = """
import signal, sys, time
from pathlib import Path

root = Path(sys.argv[1])
handler = signal.getsignal(signal.SIGINT)
(root / "disposition.txt").write_text(
    "SIG_IGN" if handler is signal.SIG_IGN else "NOT_IGNORED", encoding="utf-8"
)
(root / "ready.txt").write_text("ready\\n", encoding="utf-8")
try:
    for _ in range(600):
        time.sleep(0.1)
except KeyboardInterrupt:
    (root / "interrupted.txt").write_text("interrupted\\n", encoding="utf-8")
    raise SystemExit(130)
raise SystemExit(9)
"""

_SURVIVOR_SOURCE = """
import signal, sys, time
from pathlib import Path

signal.signal(signal.SIGINT, signal.SIG_IGN)
(Path(sys.argv[1]) / "ready.txt").write_text("ready\\n", encoding="utf-8")
for _ in range(600):
    time.sleep(0.1)
"""

_TMUX = shutil.which("tmux")
_needs_tmux = pytest.mark.skipif(_TMUX is None, reason="tmux is not installed on this host")


def _wait_for(path: Path, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return True
        time.sleep(0.05)
    return False


def _write_target(root: Path, source: str, name: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    target = root / name
    target.write_text(source, encoding="utf-8")
    return target


# ==========================================================================
# 17. The exact future launch shape does not inherit SIGINT = SIG_IGN
# ==========================================================================
@_needs_tmux
def test_the_future_tmux_launch_shape_does_not_inherit_an_ignored_sigint(
    tmp_path: Path,
) -> None:
    """A disposable process started exactly the way the corrected runbook starts a canary.

    The shape is the claim: ``tmux new-session -d`` whose command is the launcher, which
    ``exec``s the work. There is no ``&`` anywhere in it. Every path component is quoted
    because the repository path contains spaces — an unquoted command string is itself a way
    to end up with a pane that dies silently.
    """
    root = tmp_path / "probe"
    target = _write_target(root, _TARGET_SOURCE, "probe_target.py")
    session = f"d131-probe-{os.getpid()}"
    pid_file = root / "probe.pid"
    command = (
        f"'{_PYTHON}' '{_LAUNCHER}' --pid-file '{pid_file}' -- "
        f"'{_PYTHON}' '{target}' '{root}' >'{root}/pane.log' 2>&1"
    )
    subprocess.run([_TMUX, "kill-session", "-t", session], check=False, capture_output=True)
    subprocess.run(  # noqa: S603
        [_TMUX, "new-session", "-d", "-s", session, command], check=True
    )
    try:
        assert _wait_for(root / "ready.txt"), (root / "pane.log").read_text(encoding="utf-8")
        assert (root / "disposition.txt").read_text(encoding="utf-8") == "NOT_IGNORED"
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        # exec keeps the process id, so the pid the watchdog is given is the working process.
        observed = _watchdog.process_command(pid)
        assert "probe_target.py" in observed
    finally:
        subprocess.run([_TMUX, "kill-session", "-t", session], check=False, capture_output=True)


def test_the_launcher_refuses_when_sigint_is_already_ignored(tmp_path: Path) -> None:
    """The D128 chain reproduced: a non-interactive shell that backgrounds the job.

    ``sh -c 'cmd &'`` is exactly what happened, and the launcher must refuse in the first
    second rather than start a run that cannot be stopped for the next thirty-three hours.
    """
    marker = tmp_path / "started.txt"
    script = _write_target(
        tmp_path,
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('started')\n",
        "should_not_run.py",
    )
    result = subprocess.run(  # noqa: S603
        [
            "/bin/sh",
            "-c",
            f"'{_PYTHON}' '{_LAUNCHER}' -- '{_PYTHON}' '{script}' & wait $!",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert _launch.SIGINT_IGNORED_REFUSAL in result.stderr
    assert not marker.exists()


def test_the_launcher_passes_in_the_foreground(tmp_path: Path) -> None:
    """The same shell, the same launcher, without the ``&`` — and it launches."""
    result = subprocess.run(  # noqa: S603
        ["/bin/sh", "-c", f"'{_PYTHON}' '{_LAUNCHER}' --check-only"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "SIGINT_NOT_IGNORED" in result.stdout


def test_the_launcher_reports_the_inherited_disposition_it_reads() -> None:
    assert _launch.sigint_is_ignored() is (signal.getsignal(signal.SIGINT) is signal.SIG_IGN)


# ==========================================================================
# 18-19. A stop is a termination, not a delivered signal
# ==========================================================================
def test_the_watchdog_stop_actually_terminates_a_normal_target(tmp_path: Path) -> None:
    root = tmp_path / "stoppable"
    target = _write_target(root, _TARGET_SOURCE, "probe_target.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    try:
        assert _wait_for(root / "ready.txt")
        result = _watchdog.stop(
            process.pid,
            expect_command="probe_target.py",
            timeout_seconds=20.0,
            poll_seconds=0.1,
        )

        assert result.outcome == _watchdog.STOP_CONFIRMED
        assert result.signal_sent is True
        assert result.waited_seconds < 20.0
        process.wait(timeout=10)
        assert (root / "interrupted.txt").exists()
    finally:
        if process.poll() is None:  # pragma: no cover - only on a failed stop
            process.kill()
            process.wait(timeout=10)


def test_the_watchdog_reports_stop_failed_when_the_target_survives(tmp_path: Path) -> None:
    """The D128 condition, made observable.

    The target ignores ``SIGINT`` exactly as D128's canary did. ``os.kill`` still succeeds —
    which is the whole trap — so the only way to tell the difference is to look at whether the
    process is still there.
    """
    root = tmp_path / "survivor"
    target = _write_target(root, _SURVIVOR_SOURCE, "survivor.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    try:
        assert _wait_for(root / "ready.txt")
        result = _watchdog.stop(
            process.pid,
            expect_command="survivor.py",
            timeout_seconds=2.0,
            poll_seconds=0.1,
        )

        assert result.outcome == _watchdog.STOP_FAILED
        assert result.signal_sent is True
        assert "did NOT succeed" in result.detail
        # No escalation: the target is still running, which is the point.
        assert process.poll() is None
        assert _watchdog.process_is_alive(process.pid)
    finally:
        process.kill()
        process.wait(timeout=10)


def test_the_watchdog_refuses_a_target_that_is_not_the_expected_command(
    tmp_path: Path,
) -> None:
    """A reused process id must never be stopped in a canary's name."""
    root = tmp_path / "mismatch"
    target = _write_target(root, _SURVIVOR_SOURCE, "survivor.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    try:
        assert _wait_for(root / "ready.txt")
        result = _watchdog.stop(
            process.pid,
            expect_command="disclosure-drift m3 canary-source",
            timeout_seconds=2.0,
        )

        assert result.outcome == _watchdog.STOP_REFUSED
        assert result.signal_sent is False
        assert process.poll() is None
    finally:
        process.kill()
        process.wait(timeout=10)


def test_stopping_an_absent_process_signals_nothing(tmp_path: Path) -> None:
    root = tmp_path / "gone"
    target = _write_target(root, _SURVIVOR_SOURCE, "survivor.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    process.kill()
    process.wait(timeout=10)

    result = _watchdog.stop(process.pid, timeout_seconds=1.0)

    assert result.outcome == _watchdog.STOP_ALREADY_GONE
    assert result.signal_sent is False


def test_an_unreaped_child_that_has_exited_is_not_alive(tmp_path: Path) -> None:
    """A corpse in the process table is not a running canary.

    ``kill(pid, 0)`` succeeds against a zombie, so a watchdog run from the shell that started
    the run would otherwise report ``STOP_FAILED`` for a process that had already stopped —
    the mirror image of D128's error, and just as misleading.
    """
    root = tmp_path / "zombie"
    target = _write_target(root, _SURVIVOR_SOURCE, "survivor.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    try:
        assert _wait_for(root / "ready.txt")
        process.send_signal(signal.SIGKILL)
        # Deliberately not reaped: ``process.wait()`` is what would remove the zombie.
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if _watchdog.process_state(process.pid).startswith("Z"):
                break
            time.sleep(0.05)

        assert _watchdog.process_state(process.pid).startswith("Z")
        assert _watchdog.process_is_alive(process.pid) is False
    finally:
        process.wait(timeout=10)


def test_the_stop_cli_exits_four_on_stop_failed(tmp_path: Path) -> None:
    """The operator surface must not exit ``0`` on a stop that did not happen."""
    root = tmp_path / "cli"
    target = _write_target(root, _SURVIVOR_SOURCE, "survivor.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    try:
        assert _wait_for(root / "ready.txt")
        result = subprocess.run(  # noqa: S603
            [
                _PYTHON,
                str(_WATCHDOG),
                "stop",
                "--pid",
                str(process.pid),
                "--expect-command",
                "survivor.py",
                "--timeout-seconds",
                "2",
                "--poll-seconds",
                "0.1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == _watchdog.STOP_FAILED_EXIT
        assert _watchdog.STOP_FAILED in result.stdout
    finally:
        process.kill()
        process.wait(timeout=10)


# ==========================================================================
# 20. The network probe asks about exactly one process
# ==========================================================================
def test_the_network_probe_uses_the_selector_intersection_form() -> None:
    """Without ``-a`` lsof unions its selectors and answers a question nobody asked."""
    command = _watchdog.network_probe_command(4242)

    assert command == ["lsof", "-nP", "-a", "-p", "4242", "-i"]
    assert command.index("-a") < command.index("-p") < command.index("-i")


def test_the_network_probe_names_exactly_the_requested_pid() -> None:
    assert "4242" in _watchdog.network_probe_command(4242)
    assert "4243" not in _watchdog.network_probe_command(4242)


# ==========================================================================
# 21-22. Member-count stall monitoring stops at traversal completion
# ==========================================================================
def test_a_frozen_member_count_during_traversal_is_a_stall() -> None:
    verdict = _watchdog.member_stall_verdict(
        observed_members=500_000,
        governed_members=985_834,
        seconds_since_member_change=1_900,
    )

    assert verdict.state == _watchdog.TRAVERSAL_STALLED
    assert verdict.alert is True


def test_a_moving_member_count_during_traversal_is_not_a_stall() -> None:
    verdict = _watchdog.member_stall_verdict(
        observed_members=500_000,
        governed_members=985_834,
        seconds_since_member_change=60,
    )

    assert verdict.state == _watchdog.TRAVERSAL_INCOMPLETE
    assert verdict.alert is False


def test_a_frozen_member_count_after_traversal_is_not_a_stall() -> None:
    """D128's false alert. F1, F2, and finalization all run with the count already final.

    The elapsed time is deliberately enormous: no wall clock may resurrect the alert once the
    governed member count has been reached, because there is no member left to traverse.
    """
    verdict = _watchdog.member_stall_verdict(
        observed_members=985_834,
        governed_members=985_834,
        seconds_since_member_change=6 * 60 * 60,
        phase="F2",
    )

    assert verdict.state == _watchdog.TRAVERSAL_COMPLETE
    assert verdict.alert is False
    assert "not a stall" in verdict.message
    assert "F2" in verdict.message


def test_an_unknown_governed_member_count_claims_nothing() -> None:
    verdict = _watchdog.member_stall_verdict(
        observed_members=0, governed_members=0, seconds_since_member_change=10_000
    )

    assert verdict.state == _watchdog.TRAVERSAL_UNKNOWN
    assert verdict.alert is False


def test_the_phase_label_cannot_turn_an_alert_into_a_silence() -> None:
    """``phase`` improves the message and decides nothing, so a wrong label is harmless."""
    alerting = _watchdog.member_stall_verdict(
        observed_members=10,
        governed_members=20,
        seconds_since_member_change=3_600,
        phase="F2",
    )

    assert alerting.state == _watchdog.TRAVERSAL_STALLED
    assert alerting.alert is True


def test_the_stall_cli_exit_code_follows_the_alert() -> None:
    incomplete = subprocess.run(  # noqa: S603
        [
            _PYTHON,
            str(_WATCHDOG),
            "stall",
            "--observed-members",
            "10",
            "--governed-members",
            "20",
            "--seconds-since-member-change",
            "3600",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    complete = subprocess.run(  # noqa: S603
        [
            _PYTHON,
            str(_WATCHDOG),
            "stall",
            "--observed-members",
            "20",
            "--governed-members",
            "20",
            "--seconds-since-member-change",
            "36000",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert incomplete.returncode == _watchdog.ALERT_EXIT
    assert _watchdog.TRAVERSAL_STALLED in incomplete.stdout
    assert complete.returncode == 0
    assert _watchdog.TRAVERSAL_COMPLETE in complete.stdout


# ==========================================================================
# 23. An expectation that authenticates nothing is refused, not honoured
# ==========================================================================
@pytest.mark.parametrize("expectation", ["", "   ", "\t\n"])
def test_an_empty_expect_command_refuses_and_signals_nothing(
    tmp_path: Path, expectation: str
) -> None:
    """``"" in observed`` is true of every process on the machine.

    Honouring an empty expectation would turn the guard against a reused process id into a
    guard that always passes — and, worse, into one that *reports* having authenticated the
    target. The refusal is specific rather than a generic mismatch, because the operator's
    mistake is in the argument, not in the process.
    """
    root = tmp_path / f"empty-{len(expectation)}"
    target = _write_target(root, _TARGET_SOURCE, "target.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    try:
        assert _wait_for(root / "ready.txt")

        result = _watchdog.stop(process.pid, expect_command=expectation, timeout_seconds=2.0)

        assert result.outcome == _watchdog.STOP_REFUSED_EMPTY_EXPECT
        assert result.signal_sent is False
        assert process.poll() is None
    finally:
        process.kill()
        process.wait(timeout=10)


def test_omitting_the_expectation_is_not_the_same_as_an_empty_one(tmp_path: Path) -> None:
    """``None`` states no expectation; ``""`` states one that cannot be met honestly."""
    root = tmp_path / "omitted"
    target = _write_target(root, _TARGET_SOURCE, "target.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    try:
        assert _wait_for(root / "ready.txt")

        result = _watchdog.stop(process.pid, expect_command=None, timeout_seconds=20.0)

        assert result.outcome == _watchdog.STOP_CONFIRMED
        assert result.signal_sent is True
    finally:
        if process.poll() is None:  # pragma: no cover - only on an unexpected survival
            process.kill()
        process.wait(timeout=10)


def test_the_stop_cli_refuses_an_empty_expect_command(tmp_path: Path) -> None:
    """The operator surface must not exit ``0`` on an authentication that never happened."""
    root = tmp_path / "cli-empty"
    target = _write_target(root, _TARGET_SOURCE, "target.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    try:
        assert _wait_for(root / "ready.txt")
        result = subprocess.run(  # noqa: S603
            [
                _PYTHON,
                str(_WATCHDOG),
                "stop",
                "--pid",
                str(process.pid),
                "--expect-command",
                "",
                "--timeout-seconds",
                "2",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == _watchdog.REFUSED_EXIT
        assert _watchdog.STOP_REFUSED_EMPTY_EXPECT in result.stdout
        assert process.poll() is None
        assert not (root / "interrupted.txt").exists()
    finally:
        process.kill()
        process.wait(timeout=10)


# ==========================================================================
# 24. The gap between proving liveness and sending the signal
# ==========================================================================
def test_a_target_that_exits_before_the_signal_is_reported_as_already_gone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exit-in-the-gap race is normal, not exceptional, and must not raise.

    Only the liveness check is doubled; the ``ProcessLookupError`` is a real one, raised by a
    real ``os.kill`` against a process id that has genuinely been reaped. Doubling the liveness
    check is what makes the race reproducible — the alternative is a test that depends on
    losing a scheduling race on purpose.
    """
    root = tmp_path / "race"
    target = _write_target(root, _SURVIVOR_SOURCE, "survivor.py")
    process = subprocess.Popen([_PYTHON, str(target), str(root)])  # noqa: S603
    process.kill()
    process.wait(timeout=10)
    monkeypatch.setattr(_watchdog, "process_is_alive", lambda _pid: True)

    result = _watchdog.stop(process.pid, timeout_seconds=2.0, poll_seconds=0.05)

    assert result.outcome == _watchdog.STOP_ALREADY_GONE
    assert result.signal_sent is False
    assert "between the liveness check and the signal" in result.detail


def test_a_signal_that_is_not_permitted_is_never_reported_as_a_stop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``PermissionError`` means the process is still there and we could not touch it.

    Folding it into the already-gone outcome would be D128's mistake in a new place: reporting
    a stop that did not happen. Both syscalls are doubled here rather than aimed at a real
    process this user may not signal, because the only honest live target for that is ``init``.
    """
    denied: list[tuple[int, int]] = []

    def refuse(pid: int, number: int) -> None:
        denied.append((pid, number))
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(_watchdog, "process_is_alive", lambda _pid: True)
    monkeypatch.setattr(os, "kill", refuse)

    result = _watchdog.stop(4242, timeout_seconds=2.0, poll_seconds=0.05)

    assert result.outcome == _watchdog.STOP_FAILED_PERMISSION
    assert result.outcome != _watchdog.STOP_ALREADY_GONE
    assert result.outcome != _watchdog.STOP_CONFIRMED
    assert result.signal_sent is False
    assert denied == [(4242, signal.SIGINT)]


def test_the_stop_cli_exits_four_when_the_signal_was_not_permitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stop that could not be attempted exits with the stop-failed code, never ``0``."""
    monkeypatch.setattr(_watchdog, "process_is_alive", lambda _pid: True)
    monkeypatch.setattr(
        os, "kill", lambda _pid, _number: (_ for _ in ()).throw(PermissionError(1, "denied"))
    )

    assert _watchdog.main(["stop", "--pid", "4242"]) == _watchdog.STOP_FAILED_EXIT


def test_no_escalation_path_exists_anywhere_in_the_watchdog() -> None:
    """The hardening added outcomes; it added no way to escalate.

    Stated over the file's own text because the claim is an absence, and an absence cannot be
    demonstrated by exercising a path that is not there.
    """
    source = _WATCHDOG.read_text(encoding="utf-8")
    signals_used = {
        node.attr
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "signal"
    }

    # The prose names SIGTERM and SIGKILL to say they are never sent; the code must not.
    assert signals_used == {"SIGINT"}
    assert source.count("os.kill(") == 2  # the liveness probe, and the one SIGINT
    for escalation in ("killpg", "pkill", "terminate(", "SIGKILL)", "SIGTERM)"):
        assert escalation not in source


# ==========================================================================
# 25. observed > governed is an inconsistency, not a completed traversal
# ==========================================================================
@pytest.mark.parametrize(
    ("observed", "governed", "expected_state", "expected_alert", "expected_inconsistent"),
    [
        pytest.param(
            500_000, 985_834, _watchdog.TRAVERSAL_STALLED, True, False, id="observed-below"
        ),
        pytest.param(
            985_834, 985_834, _watchdog.TRAVERSAL_COMPLETE, False, False, id="observed-equal"
        ),
        pytest.param(
            985_900,
            985_834,
            _watchdog.TRAVERSAL_INCONSISTENT,
            False,
            True,
            id="observed-above",
        ),
    ],
)
def test_the_three_member_count_relations_reach_three_distinct_verdicts(
    observed: int,
    governed: int,
    expected_state: str,
    expected_alert: bool,
    expected_inconsistent: bool,
) -> None:
    """All three relations in one place, because the defect was two of them colliding.

    The previous rule was ``observed >= governed``, which gave *above* the same verdict as
    *equal* — a traversal that had passed its own governed bound reported as one that had
    finished normally. The elapsed time is far beyond any threshold in every case, so nothing
    here is decided by the clock.
    """
    verdict = _watchdog.member_stall_verdict(
        observed_members=observed,
        governed_members=governed,
        seconds_since_member_change=6 * 60 * 60,
    )

    assert verdict.state == expected_state
    assert verdict.alert is expected_alert
    assert verdict.inconsistent is expected_inconsistent


def test_the_inconsistent_verdict_disables_stall_timing_and_invents_no_rule() -> None:
    """What it must say, and what it must not do.

    Member-stall timing is off because ordinary stall semantics presuppose a bound the count
    has not passed. No kill rule is invented in its place, and the working catalog is not
    consulted to decide which of the two counts is wrong — the counts are inputs here.
    """
    verdict = _watchdog.member_stall_verdict(
        observed_members=42,
        governed_members=40,
        seconds_since_member_change=0.0,
        phase="F2",
    )

    assert verdict.state == _watchdog.TRAVERSAL_INCONSISTENT
    assert verdict.inconsistent is True
    assert verdict.alert is False
    assert "42" in verdict.message
    assert "40" in verdict.message
    assert "F2" in verdict.message
    assert "invents no kill rule" in verdict.message
    assert "member-stall timing is disabled" in verdict.message


def test_the_stall_cli_gives_the_inconsistency_its_own_exit_code() -> None:
    """It must not exit ``0``: an unnoticed inconsistency is how a wrong count survives."""
    inconsistent = subprocess.run(  # noqa: S603
        [
            _PYTHON,
            str(_WATCHDOG),
            "stall",
            "--observed-members",
            "985900",
            "--governed-members",
            "985834",
            "--seconds-since-member-change",
            "10",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert inconsistent.returncode == _watchdog.INCONSISTENT_EXIT
    assert inconsistent.returncode not in {0, _watchdog.ALERT_EXIT}
    assert _watchdog.TRAVERSAL_INCONSISTENT in inconsistent.stdout


# ==========================================================================
# 26. A non-positive process id is a broadcast, and never reaches a syscall
# ==========================================================================
# ``os.kill(0, SIGINT)`` signals the caller's whole process group -- run from the canary's
# pane, that is the canary and this watchdog together -- and ``os.kill(-1, SIGINT)`` signals
# every process the user may signal. ``lsof -p`` reads the same way. One mistyped ``--pid``
# was therefore enough to turn an instrument whose entire contract is *act on exactly the
# process you named* into a broadcast. The domain is refused on the argument, before any
# syscall, so the refusal costs nothing and cannot itself touch a process.
@pytest.mark.parametrize("pid", [0, -1])
def test_stopping_a_non_positive_pid_refuses_before_any_inspection(
    pid: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither the signal nor the two ``ps`` reads may happen for a non-target.

    Every route out of this module to the operating system is replaced with something that
    fails loudly, so "nothing was reached" is proved by the guard holding rather than by an
    absence nobody checked.
    """
    touched: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        touched.append("reached")
        message = f"a non-positive pid ({pid}) reached the operating system"
        raise AssertionError(message)

    monkeypatch.setattr(os, "kill", forbidden)
    monkeypatch.setattr(_watchdog, "process_is_alive", forbidden)
    monkeypatch.setattr(_watchdog, "process_command", forbidden)
    monkeypatch.setattr(_watchdog.subprocess, "run", forbidden)

    result = _watchdog.stop(pid, expect_command="m3 canary-source", timeout_seconds=2.0)

    assert result.outcome == _watchdog.STOP_REFUSED_NON_POSITIVE_PID
    assert result.signal_sent is False
    assert result.waited_seconds == 0.0
    assert "not a single target" in result.detail
    assert touched == []


@pytest.mark.parametrize("pid", ["0", "-1"])
def test_the_stop_cli_refuses_a_non_positive_pid(pid: str) -> None:
    """The operator surface must name the refusal, and must not exit ``0``."""
    result = subprocess.run(  # noqa: S603
        [_PYTHON, str(_WATCHDOG), "stop", "--pid", pid, "--timeout-seconds", "2"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == _watchdog.REFUSED_EXIT
    assert _watchdog.STOP_REFUSED_NON_POSITIVE_PID in result.stdout


@pytest.mark.parametrize("pid", [0, -1])
def test_the_network_probe_builds_no_command_for_a_non_positive_pid(pid: int) -> None:
    """A command that cannot exist cannot be run by accident later."""
    with pytest.raises(ValueError, match="not a single target"):
        _watchdog.network_probe_command(pid)


@pytest.mark.parametrize("pid", ["0", "-1"])
def test_the_probe_cli_refuses_a_non_positive_pid_and_runs_no_lsof(
    pid: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``lsof`` is never executed, which is the claim the vector-level test cannot make."""
    ran: list[object] = []

    def record(command: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        # Returns a *successful* result on purpose. If the guard were removed this test would
        # then fail on its own claim -- lsof ran, and the exit code was not the refusal --
        # rather than incidentally, on the shape of a stand-in that returned nothing.
        ran.append(command)
        return subprocess.CompletedProcess(args=command, returncode=0)

    monkeypatch.setattr(_watchdog.subprocess, "run", record)

    assert _watchdog.main(["network-probe", "--pid", pid]) == _watchdog.REFUSED_EXIT
    assert ran == []


def test_a_positive_pid_is_still_accepted_by_both_operations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The positive control: the guard refuses a domain, not the operations themselves."""
    assert _watchdog.network_probe_command(4242) == ["lsof", "-nP", "-a", "-p", "4242", "-i"]
    assert _watchdog.non_targetable_pid_detail(4242) is None
    assert _watchdog.non_targetable_pid_detail(1) is None

    monkeypatch.setattr(_watchdog, "process_is_alive", lambda _pid: False)
    result = _watchdog.stop(4242, timeout_seconds=2.0)

    assert result.outcome == _watchdog.STOP_ALREADY_GONE


def test_one_definition_states_the_pid_domain_for_both_operations() -> None:
    """Centralized on purpose: two call sites reading one rule cannot drift apart.

    A per-call-site comparison would be correct today and is exactly the shape that lets one
    of them be relaxed later without the other noticing.
    """
    source = _WATCHDOG.read_text(encoding="utf-8")

    assert source.count("def non_targetable_pid_detail") == 1
    assert source.count("pid > 0") == 1
    assert "non_targetable_pid_detail(pid)" in inspect.getsource(_watchdog.stop)
    assert "non_targetable_pid_detail(pid)" in inspect.getsource(_watchdog.network_probe_command)
