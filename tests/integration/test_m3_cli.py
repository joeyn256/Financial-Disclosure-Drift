"""Milestone 3.1 command group (`Milestones/contracts/m3_1.md` §9).

These tests drive the real CLI as a subprocess, so what they assert is what an operator would
actually see and what a gate would actually read: exit codes, the evidence-root boundary, the
completion token, and the two properties Gate F depends on — that two dry runs agree byte for byte,
and that no command discloses an absolute path or the SEC identity.
"""

from __future__ import annotations

import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

ENV_PREFIX = "DISCLOSURE_DRIFT_"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 1
EXIT_USAGE = 2
EXIT_GATE_FAILURE = 4

M3_COMMANDS = (
    "rehearse",
    "rehearse-report",
    "plan-requests",
    "show-budget",
    "show-receipt",
    "recovery-state",
)


def _run(
    arguments: list[str],
    cwd: Path,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    clean = {key: value for key, value in os.environ.items() if not key.startswith(ENV_PREFIX)}
    clean.update(env or {})
    return subprocess.run(
        [sys.executable, "-m", "disclosure_drift", *arguments],
        cwd=cwd,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    """An evidence root outside any repository checkout."""
    root = tmp_path / "private-evidence"
    root.mkdir()
    return root


def _rehearse(
    repo_root: Path,
    evidence_root: Path,
    *,
    evidence_out: str = "reports/a1-a12.json",
    receipt_out: str = "receipts/rehearse.json",
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "m3",
            "rehearse",
            "--evidence-root",
            str(evidence_root),
            "--evidence-out",
            evidence_out,
            "--receipt-out",
            receipt_out,
        ],
        repo_root,
    )


def _write_manifest(evidence_root: Path, approved: int = 0) -> None:
    """An operator-named calendar-evidence manifest with `approved` approved entries."""
    entries = [
        {"evidence_id": f"e{index}", "review_status": "approved"} for index in range(approved)
    ]
    entries.append({"evidence_id": "draft", "review_status": "draft"})
    path = evidence_root / "manifest.json"
    path.write_text(
        json.dumps({"manifest_version": "edgar-calendar-evidence/1.0", "entries": entries}),
        encoding="utf-8",
    )


def _plan(
    repo_root: Path,
    evidence_root: Path,
    out: str = "plans/m3-2a.json",
    *,
    approved_entries: int = 0,
) -> subprocess.CompletedProcess[str]:
    _write_manifest(evidence_root, approved_entries)
    return _run(
        [
            "m3",
            "plan-requests",
            "--evidence-root",
            str(evidence_root),
            "--calendar-evidence-manifest",
            "manifest.json",
            "--catalog",
            "catalog/catalog.db",
            "--coverage-start",
            "2024-01-01",
            "--coverage-end",
            "2024-06-30",
            "--as-of",
            "2024-06-30",
            "--calendar-year",
            "2024",
            "--plan-out",
            out,
            "--receipt-out",
            "receipts/plan.json",
        ],
        repo_root,
    )


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #
def test_the_m3_group_is_registered(repo_root: Path) -> None:
    result = _run(["m3", "--help"], repo_root)

    assert result.returncode == EXIT_OK
    normalized = " ".join(result.stdout.split())
    for command in M3_COMMANDS:
        assert command in normalized


def test_the_top_level_help_lists_the_m3_group(repo_root: Path) -> None:
    result = _run(["--help"], repo_root)

    assert result.returncode == EXIT_OK
    assert "m3" in " ".join(result.stdout.split())


def test_the_group_without_a_subcommand_prints_help(repo_root: Path) -> None:
    result = _run(["m3"], repo_root)

    assert result.returncode in {EXIT_OK, EXIT_USAGE}
    assert "rehearse" in result.stdout + result.stderr


def test_an_unknown_subcommand_is_a_usage_error(repo_root: Path) -> None:
    # `acquire` was this test's example until the M3.2 surfaces were recognized; a recognized
    # command refuses (EXIT_STAGE_NOT_ENABLED) rather than failing at the parser, so the
    # unknown-subcommand assertion needs a name that is genuinely not a command.
    result = _run(["m3", "no-such-subcommand"], repo_root)

    assert result.returncode == EXIT_USAGE


# --------------------------------------------------------------------------- #
# The evidence root is mandatory, absolute, and external
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("command", M3_COMMANDS)
def test_every_command_requires_an_evidence_root(repo_root: Path, command: str) -> None:
    result = _run(["m3", command], repo_root)

    assert result.returncode == EXIT_USAGE
    assert "--evidence-root" in result.stderr


def test_an_evidence_root_inside_the_checkout_is_refused(repo_root: Path) -> None:
    result = _run(
        [
            "m3",
            "show-budget",
            "--evidence-root",
            str(repo_root / "inside-the-checkout"),
            "--plan",
            "plan.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_CONFIG_ERROR
    assert "evidence root refused" in result.stderr
    # The refusal must not leak what the boundary exists to protect. Asserting only the message
    # prefix let an absolute-path leak pass unnoticed once already.
    assert str(repo_root) not in result.stderr
    assert str(repo_root) not in result.stdout


def test_a_refusal_names_no_absolute_path_for_any_command(
    repo_root: Path, evidence_root: Path
) -> None:
    """Master plan §17 stop condition 12: no absolute personal path in any output."""
    for command, argument in (
        ("show-budget", "--plan"),
        ("show-receipt", "--receipt"),
        ("rehearse-report", "--evidence"),
    ):
        result = _run(
            [
                "m3",
                command,
                "--evidence-root",
                str(repo_root / "inside-the-checkout"),
                argument,
                "artifact.json",
            ],
            repo_root,
        )
        combined = result.stdout + result.stderr
        assert str(repo_root) not in combined
        assert str(evidence_root) not in combined


def test_a_relative_evidence_root_is_refused(repo_root: Path) -> None:
    result = _run(
        ["m3", "show-budget", "--evidence-root", "relative/evidence", "--plan", "plan.json"],
        repo_root,
    )

    assert result.returncode == EXIT_CONFIG_ERROR


# --------------------------------------------------------------------------- #
# rehearse
# --------------------------------------------------------------------------- #
def test_rehearse_runs_all_twelve_and_emits_the_completion_token(
    repo_root: Path, evidence_root: Path
) -> None:
    result = _rehearse(repo_root, evidence_root)

    assert result.returncode == EXIT_OK
    normalized = " ".join(result.stdout.split())
    for scenario in ("A1", "A5", "A9", "A12"):
        assert scenario in normalized
    assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" in result.stdout


def test_rehearse_reports_zero_actual_network_requests(
    repo_root: Path, evidence_root: Path
) -> None:
    result = _rehearse(repo_root, evidence_root)

    assert "actual network requests : 0" in " ".join(result.stdout.split())


def test_rehearse_writes_its_evidence_report(repo_root: Path, evidence_root: Path) -> None:
    _rehearse(repo_root, evidence_root)

    written = evidence_root / "reports" / "a1-a12.json"
    assert written.is_file()
    document = json.loads(written.read_text(encoding="utf-8"))
    assert document["complete"] is True
    assert document["passed"] is True
    assert len(document["scenarios"]) == 12


def test_a_subset_runs_without_emitting_the_completion_token(
    repo_root: Path, evidence_root: Path
) -> None:
    result = _run(
        [
            "m3",
            "rehearse",
            "--evidence-root",
            str(evidence_root),
            "--evidence-out",
            "reports/subset.json",
            "--scenarios",
            "A1,A2",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_OK
    assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" not in result.stdout


def test_an_unknown_scenario_is_a_gate_failure(repo_root: Path, evidence_root: Path) -> None:
    result = _run(
        [
            "m3",
            "rehearse",
            "--evidence-root",
            str(evidence_root),
            "--evidence-out",
            "reports/bad.json",
            "--scenarios",
            "A99",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE


# --------------------------------------------------------------------------- #
# Receipts — every command that runs produces one
# --------------------------------------------------------------------------- #
def test_rehearse_writes_a_receipt(repo_root: Path, evidence_root: Path) -> None:
    """A passing rehearsal that produced no receipt is an incomplete command."""
    _rehearse(repo_root, evidence_root)

    written = evidence_root / "receipts" / "rehearse.json"
    assert written.is_file()
    document = json.loads(written.read_text(encoding="utf-8"))
    assert document["invocation_mode"] == "rehearsal"
    assert document["actual_logical_request_count"] == 0
    assert document["actual_physical_attempt_count"] == 0
    assert document["rehearsal_evidence_reference"].startswith("m3-1a-rehearsal-report-")


def test_plan_requests_writes_a_dry_run_receipt(repo_root: Path, evidence_root: Path) -> None:
    _plan(repo_root, evidence_root)

    written = evidence_root / "receipts" / "plan.json"
    assert written.is_file()
    document = json.loads(written.read_text(encoding="utf-8"))
    assert document["invocation_mode"] == "dry_run"
    assert document["actual_physical_attempt_count"] == 0
    # A dry run precedes owner approval, so it may not claim an approved ceiling.
    assert "approved_request_ceiling" not in document


def test_an_emitted_receipt_passes_show_receipt(repo_root: Path, evidence_root: Path) -> None:
    """The round trip proves the emitted receipt is well-formed, not merely written."""
    _rehearse(repo_root, evidence_root)

    result = _run(
        [
            "m3",
            "show-receipt",
            "--evidence-root",
            str(evidence_root),
            "--receipt",
            "receipts/rehearse.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_OK
    assert "validation" in " ".join(result.stdout.split())


def test_a_receipt_is_written_even_without_receipt_out(
    repo_root: Path, evidence_root: Path
) -> None:
    """ "No receipt" is not an available outcome for a command that ran."""
    _run(
        [
            "m3",
            "rehearse",
            "--evidence-root",
            str(evidence_root),
            "--evidence-out",
            "reports/named.json",
        ],
        repo_root,
    )

    receipts = list((evidence_root / "receipts").glob("receipt-*.json"))
    assert receipts, "the rehearsal produced no receipt under its content-derived name"


def test_the_dry_run_receipt_carries_the_plan_hash(repo_root: Path, evidence_root: Path) -> None:
    """recovery-state condition 8.10 compares against this value, so it must be recorded."""
    _plan(repo_root, evidence_root)

    plan_document = json.loads((evidence_root / "plans" / "m3-2a.json").read_text(encoding="utf-8"))
    receipt = json.loads((evidence_root / "receipts" / "plan.json").read_text(encoding="utf-8"))
    import hashlib

    expected = hashlib.sha256((evidence_root / "plans" / "m3-2a.json").read_bytes()).hexdigest()
    assert receipt["request_plan_sha256"] == expected
    assert plan_document["request_plan_schema_version"] == receipt["request_plan_schema_version"]


# --------------------------------------------------------------------------- #
# rehearse-report
# --------------------------------------------------------------------------- #
def test_rehearse_report_accepts_a_complete_passing_record(
    repo_root: Path, evidence_root: Path
) -> None:
    _rehearse(repo_root, evidence_root)

    result = _run(
        [
            "m3",
            "rehearse-report",
            "--evidence-root",
            str(evidence_root),
            "--evidence",
            "reports/a1-a12.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_OK
    assert "all twelve recorded : yes" in " ".join(result.stdout.split())


def test_rehearse_report_refuses_a_record_with_a_failed_scenario(
    repo_root: Path, evidence_root: Path
) -> None:
    """A summary claiming success cannot override a scenario the record shows as failed."""
    _rehearse(repo_root, evidence_root)
    path = evidence_root / "reports" / "a1-a12.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    for entry in document["scenarios"]:
        if entry["scenario_id"] == "A11":
            entry["passed"] = False
    path.write_text(json.dumps(document), encoding="utf-8")

    result = _run(
        [
            "m3",
            "rehearse-report",
            "--evidence-root",
            str(evidence_root),
            "--evidence",
            "reports/a1-a12.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE


def test_rehearse_report_refuses_an_incomplete_record(repo_root: Path, evidence_root: Path) -> None:
    _rehearse(repo_root, evidence_root)
    path = evidence_root / "reports" / "a1-a12.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    # Drop a scenario while leaving the summary claiming completeness: the verdict must come from
    # the record, not from the record's own claim about itself.
    document["scenarios"] = [
        entry for entry in document["scenarios"] if entry["scenario_id"] != "A11"
    ]
    path.write_text(json.dumps(document), encoding="utf-8")

    result = _run(
        [
            "m3",
            "rehearse-report",
            "--evidence-root",
            str(evidence_root),
            "--evidence",
            "reports/a1-a12.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE


# --------------------------------------------------------------------------- #
# plan-requests and show-budget
# --------------------------------------------------------------------------- #
def test_plan_requests_derives_a_plan_and_writes_it(repo_root: Path, evidence_root: Path) -> None:
    result = _plan(repo_root, evidence_root)

    assert result.returncode == EXIT_OK
    assert (evidence_root / "plans" / "m3-2a.json").is_file()
    normalized = " ".join(result.stdout.split())
    assert "hard request ceiling" in normalized
    assert "zero requests placed" in normalized


def test_two_dry_runs_produce_byte_identical_plans(repo_root: Path, evidence_root: Path) -> None:
    """Gate F requires exact agreement; a difference is the finding, not a retry trigger."""
    _plan(repo_root, evidence_root, out="plans/first.json")
    _plan(repo_root, evidence_root, out="plans/second.json")

    first = (evidence_root / "plans" / "first.json").read_bytes()
    second = (evidence_root / "plans" / "second.json").read_bytes()
    assert first == second


def test_show_budget_renders_the_plan_and_approves_nothing(
    repo_root: Path, evidence_root: Path
) -> None:
    _plan(repo_root, evidence_root)

    result = _run(
        ["m3", "show-budget", "--evidence-root", str(evidence_root), "--plan", "plans/m3-2a.json"],
        repo_root,
    )

    assert result.returncode == EXIT_OK
    normalized = " ".join(result.stdout.split())
    assert "hard request ceiling (derived)" in normalized
    assert "not approved by this command" in normalized


def test_the_ceiling_is_the_sum_of_planned_requests_times_a_reachable(
    repo_root: Path, evidence_root: Path
) -> None:
    _plan(repo_root, evidence_root)
    document = json.loads((evidence_root / "plans" / "m3-2a.json").read_text(encoding="utf-8"))

    expected = sum(
        route["planned_unique_logical_requests"] * route["a_reachable"]
        for route in document["routes"]
    )
    assert document["totals"]["hard_request_ceiling"] == expected


def test_an_artifact_path_escaping_the_evidence_root_is_refused(
    repo_root: Path, evidence_root: Path
) -> None:
    result = _run(
        ["m3", "show-budget", "--evidence-root", str(evidence_root), "--plan", "../escaped.json"],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE


# --------------------------------------------------------------------------- #
# The plan reads its explicit inputs rather than hardwiring them
# --------------------------------------------------------------------------- #
def test_the_manifest_entry_count_drives_the_announcement_route(
    repo_root: Path, evidence_root: Path
) -> None:
    """The operator-named manifest sets U(sec_edgar_calendar_announcement), not a constant."""
    _plan(repo_root, evidence_root, out="plans/two.json", approved_entries=2)
    document = json.loads((evidence_root / "plans" / "two.json").read_text(encoding="utf-8"))

    route = next(
        item
        for item in document["routes"]
        if item["source_id"] == "sec_edgar_calendar_announcement"
    )
    assert route["planned_unique_logical_requests"] == 2


def test_an_empty_manifest_lawfully_plans_zero_announcements(
    repo_root: Path, evidence_root: Path
) -> None:
    _plan(repo_root, evidence_root, out="plans/zero.json", approved_entries=0)
    document = json.loads((evidence_root / "plans" / "zero.json").read_text(encoding="utf-8"))

    route = next(
        item
        for item in document["routes"]
        if item["source_id"] == "sec_edgar_calendar_announcement"
    )
    assert route["planned_unique_logical_requests"] == 0


def test_only_approved_manifest_entries_are_counted(repo_root: Path, evidence_root: Path) -> None:
    """Every manifest written here carries one draft entry, which must never be planned."""
    _plan(repo_root, evidence_root, out="plans/three.json", approved_entries=3)
    document = json.loads((evidence_root / "plans" / "three.json").read_text(encoding="utf-8"))

    route = next(
        item
        for item in document["routes"]
        if item["source_id"] == "sec_edgar_calendar_announcement"
    )
    assert route["planned_unique_logical_requests"] == 3


def test_plan_requests_requires_its_explicit_inputs(repo_root: Path, evidence_root: Path) -> None:
    """§9 names --calendar-evidence-manifest and --catalog; neither may be inferred."""
    result = _run(
        [
            "m3",
            "plan-requests",
            "--evidence-root",
            str(evidence_root),
            "--coverage-start",
            "2024-01-01",
            "--coverage-end",
            "2024-06-30",
            "--as-of",
            "2024-06-30",
            "--calendar-year",
            "2024",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_USAGE
    assert "--calendar-evidence-manifest" in result.stderr or "--catalog" in result.stderr


def test_show_budget_renders_all_eight_governed_quantities(
    repo_root: Path, evidence_root: Path
) -> None:
    _plan(repo_root, evidence_root)

    result = _run(
        ["m3", "show-budget", "--evidence-root", str(evidence_root), "--plan", "plans/m3-2a.json"],
        repo_root,
    )

    normalized = " ".join(result.stdout.split())
    for quantity in (
        "planned unique logical requests",
        "maximum physical attempts",
        "expected successful responses",
        "expected cache hits",
        "expected not-modified responses",
        "expected governed non-success responses",
        "maximum new raw objects",
        "rate-limiter spacing floor",
    ):
        assert quantity in normalized


def test_an_underivable_expectation_is_marked_unresolved_not_zero(
    repo_root: Path, evidence_root: Path
) -> None:
    """A zero would read as an approved expectation of no successful responses."""
    _plan(repo_root, evidence_root)

    result = _run(
        ["m3", "show-budget", "--evidence-root", str(evidence_root), "--plan", "plans/m3-2a.json"],
        repo_root,
    )

    assert "EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN" in result.stdout


# --------------------------------------------------------------------------- #
# show-receipt
# --------------------------------------------------------------------------- #
def test_show_receipt_exits_four_on_a_defective_receipt(
    repo_root: Path, evidence_root: Path
) -> None:
    path = evidence_root / "receipts" / "receipt-broken.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"receipt_schema_version":"m3-execution-receipt/1.0"}\n', encoding="utf-8")

    result = _run(
        [
            "m3",
            "show-receipt",
            "--evidence-root",
            str(evidence_root),
            "--receipt",
            "receipts/receipt-broken.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE


def test_show_receipt_refuses_a_receipt_whose_predecessor_is_missing(
    repo_root: Path, evidence_root: Path
) -> None:
    """Receipt spec §11.4: a broken recovery chain is a stop condition."""
    import hashlib

    _rehearse(repo_root, evidence_root)
    original = json.loads(
        (evidence_root / "receipts" / "rehearse.json").read_text(encoding="utf-8")
    )
    original["recovery_predecessor_receipt_id"] = "c" * 64
    preimage = {key: value for key, value in original.items() if key != "receipt_id"}
    rendered = (
        json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    )
    original["receipt_id"] = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    broken = evidence_root / "receipts" / "broken.json"
    broken.write_text(
        json.dumps(original, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    result = _run(
        [
            "m3",
            "show-receipt",
            "--evidence-root",
            str(evidence_root),
            "--receipt",
            "receipts/broken.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "recovery_predecessor_receipt_id" in result.stderr
    assert str(evidence_root) not in result.stderr


def test_show_receipt_exits_four_on_a_missing_receipt(repo_root: Path, evidence_root: Path) -> None:
    result = _run(
        [
            "m3",
            "show-receipt",
            "--evidence-root",
            str(evidence_root),
            "--receipt",
            "receipts/absent.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE


# --------------------------------------------------------------------------- #
# Disclosure
# --------------------------------------------------------------------------- #
def test_no_command_prints_the_resolved_evidence_root(repo_root: Path, evidence_root: Path) -> None:
    """The root is validated and used, but its absolute value is never displayed."""
    rehearsal = _rehearse(repo_root, evidence_root)
    plan = _plan(repo_root, evidence_root)

    for result in (rehearsal, plan):
        assert str(evidence_root) not in result.stdout


def test_no_command_prints_the_sec_identity(repo_root: Path, evidence_root: Path) -> None:
    identity = "Rehearsal Operator operator@example.invalid"  # noqa: S105 - a contact identity
    rehearsal = _run(
        ["m3", "rehearse", "--evidence-root", str(evidence_root)],
        repo_root,
        env={"DISCLOSURE_DRIFT_SEC_USER_AGENT": identity},
    )

    assert identity not in rehearsal.stdout
    assert identity not in rehearsal.stderr


# --------------------------------------------------------------------------- #
# The completion token is gated on the A_reachable agreement, not merely told about it
# --------------------------------------------------------------------------- #
def _rehearse_in_process(
    monkeypatch: pytest.MonkeyPatch,
    evidence_root: Path,
    *,
    tested: dict[str, int],
    unmeasured: dict[str, str] | None = None,
) -> int:
    """Run `m3 rehearse` in-process over a report whose tested bounds are supplied.

    The gate cannot be reached from a subprocess without perturbing production code, so the report
    is substituted at the one seam the command reads it from. Everything else — the argument
    parsing, the artifact writes, the receipt, the token decision — is the real command.
    """
    from disclosure_drift import cli
    from disclosure_drift.m3.rehearsal import RehearsalReport, run_rehearsal

    real = run_rehearsal(["A1"], workspace_root=evidence_root)
    substituted = RehearsalReport(
        outcomes=real.outcomes,
        derived_a_reachable=real.derived_a_reachable,
        tested_a_reachable=tested,
        unmeasured_routes=unmeasured or {},
    )
    monkeypatch.setattr(cli, "run_rehearsal", lambda _requested, **_kwargs: substituted)
    return cli.main(
        [
            "m3",
            "rehearse",
            "--evidence-root",
            str(evidence_root),
            "--evidence-out",
            "reports/bounds.json",
            "--receipt-out",
            "receipts/bounds.json",
        ]
    )


def test_a_disagreeing_a_reachable_bound_is_a_gate_failure(
    monkeypatch: pytest.MonkeyPatch,
    evidence_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Master plan §17 stop condition 9.

    The summary printed the agreement all along; nothing acted on it. A route whose worst reachable
    path was never confirmed cannot back a ceiling, so the run must exit 4 and emit no token.
    """
    from disclosure_drift.m3.request_plan import derive_a_reachable
    from disclosure_drift.sec.source_registry import SOURCES

    disagreeing = {
        source_id: derive_a_reachable(spec) + 1 for source_id, spec in sorted(SOURCES.items())
    }

    code = _rehearse_in_process(monkeypatch, evidence_root, tested=disagreeing)

    assert code == EXIT_GATE_FAILURE
    captured = capsys.readouterr()
    assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" not in captured.out


def test_an_agreeing_a_reachable_bound_still_passes(
    monkeypatch: pytest.MonkeyPatch,
    evidence_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The inverse control: the gate must not refuse every run it is asked about."""
    from disclosure_drift.m3.request_plan import derive_a_reachable
    from disclosure_drift.sec.source_registry import SOURCES

    agreeing = {source_id: derive_a_reachable(spec) for source_id, spec in sorted(SOURCES.items())}

    code = _rehearse_in_process(monkeypatch, evidence_root, tested=agreeing)

    assert code == EXIT_OK
    captured = capsys.readouterr()
    assert "A_reachable agrees : yes" in " ".join(captured.out.split())


# --------------------------------------------------------------------------- #
# Decision 029 §6: the token needs four conjuncts, not three
# --------------------------------------------------------------------------- #
def _agreeing_bounds() -> dict[str, int]:
    from disclosure_drift.m3.request_plan import derive_a_reachable
    from disclosure_drift.sec.source_registry import SOURCES

    return {source_id: derive_a_reachable(spec) for source_id, spec in sorted(SOURCES.items())}


def test_an_omitted_tested_route_is_a_gate_failure(
    monkeypatch: pytest.MonkeyPatch,
    evidence_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The exact hole Decision 029 §6 closes.

    `a_reachable_agrees` quantifies over the *tested* keys, so a report that measures one route and
    omits the other eight satisfies it vacuously. Before the correction that record emitted the
    phase token; the ceiling it would have backed rests on eight untested bounds.
    """
    bounds = _agreeing_bounds()
    one_route = {"sec_company_tickers": bounds["sec_company_tickers"]}

    code = _rehearse_in_process(monkeypatch, evidence_root, tested=one_route)

    assert code == EXIT_GATE_FAILURE
    captured = capsys.readouterr()
    assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" not in captured.out
    assert "absent from the tested set" in captured.err


def test_a_forged_fully_tested_flag_beside_an_unmeasured_route_fails(
    monkeypatch: pytest.MonkeyPatch,
    evidence_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`a_reachable_fully_tested` is derived from `unmeasured_routes`, so it cannot be forged here.

    The route is both counted as tested and listed as unmeasured — a self-contradictory record. The
    gate must refuse it rather than believe the more convenient half.
    """
    bounds = _agreeing_bounds()

    code = _rehearse_in_process(
        monkeypatch,
        evidence_root,
        tested=bounds,
        unmeasured={"sec_edgar_calendar_announcement": "no witness was driven"},
    )

    assert code == EXIT_GATE_FAILURE
    captured = capsys.readouterr()
    assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" not in captured.out
    assert "no full-path witness" in captured.err


def test_an_evidence_gap_records_the_decision_029_reason_not_an_interruption(
    monkeypatch: pytest.MonkeyPatch,
    evidence_root: Path,
) -> None:
    """Decision 029 §5: a defective witness is an evidence-integrity failure, never an interruption.

    A rehearsal places no request, so it can interrupt no acquisition. Recording
    `SEC_ACQUISITION_INTERRUPTED` here would misreport a broken witness as a network event and
    corrupt the one code Decision 028 §6 reserves for a real interruption.
    """
    bounds = _agreeing_bounds()

    code = _rehearse_in_process(
        monkeypatch,
        evidence_root,
        tested=bounds,
        unmeasured={"sec_edgar_calendar_announcement": "no witness was driven"},
    )
    assert code == EXIT_GATE_FAILURE

    receipt = json.loads((evidence_root / "receipts" / "bounds.json").read_text())
    assert receipt["completion_status"] == "failed"
    assert receipt["reason_code"] == "OFFLINE_REHEARSAL_SCENARIO_MISMATCH"
    assert receipt["reason_code"] != "SEC_ACQUISITION_INTERRUPTED"
    # Decision 029 registers a permitted *value*, not a schema element, so this receipt carries
    # whatever the current writer schema is rather than pinning a version of its own here.
    from disclosure_drift.m3.receipt import RECEIPT_SCHEMA_VERSION

    assert receipt["receipt_schema_version"] == RECEIPT_SCHEMA_VERSION
    assert receipt["actual_logical_request_count"] == 0
    assert receipt["actual_physical_attempt_count"] == 0


def test_a_stored_report_with_an_omitted_route_fails_inspection(
    repo_root: Path, evidence_root: Path
) -> None:
    """`m3 rehearse-report` recomputes rather than trusts (Decision 029 §6).

    The stored booleans all claim success; the record's own numbers do not support them.
    """
    first = _rehearse(repo_root, evidence_root)
    assert first.returncode == EXIT_OK

    stored = evidence_root / "reports" / "a1-a12.json"
    document = json.loads(stored.read_text())
    keep = sorted(document["tested_a_reachable"])[0]
    document["tested_a_reachable"] = {keep: document["tested_a_reachable"][keep]}
    forged = evidence_root / "reports" / "forged.json"
    forged.write_text(json.dumps(document))

    result = _run(
        [
            "m3",
            "rehearse-report",
            "--evidence-root",
            str(evidence_root),
            "--evidence",
            "reports/forged.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" not in result.stdout


def test_a_stored_report_omitting_a_route_from_both_mappings_fails_inspection(
    repo_root: Path, evidence_root: Path
) -> None:
    """A record does not get to define its own route set (Decision 029 §6).

    Deleting a route from the tested mapping alone is the easy forgery. The hard one deletes it
    from *both* mappings: the two stored mappings then agree with each other perfectly, every
    stored boolean is true, and `unmeasured_routes` is empty. Only recomputing the authoritative
    nine-route derivation from the source registry refuses it.
    """
    first = _rehearse(repo_root, evidence_root)
    assert first.returncode == EXIT_OK

    stored = evidence_root / "reports" / "a1-a12.json"
    document = json.loads(stored.read_text())
    keep = sorted(document["derived_a_reachable"])[0]
    document["derived_a_reachable"] = {keep: document["derived_a_reachable"][keep]}
    document["tested_a_reachable"] = {keep: document["tested_a_reachable"][keep]}
    document["unmeasured_routes"] = {}
    document["a_reachable_agrees"] = True
    document["a_reachable_fully_tested"] = True
    forged = evidence_root / "reports" / "forged_both.json"
    forged.write_text(json.dumps(document))

    result = _run(
        [
            "m3",
            "rehearse-report",
            "--evidence-root",
            str(evidence_root),
            "--evidence",
            "reports/forged_both.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" not in result.stdout


def test_a_stored_report_with_equal_but_wrong_bounds_fails_inspection(
    repo_root: Path, evidence_root: Path
) -> None:
    """Agreement with itself is not agreement with the derivation (Decision 029 §6).

    Every route is present in both mappings and every pair matches, so a stored-versus-stored
    comparison sees a flawless record. The values are simply not the ones the response-policy loop
    derives — which is exactly the claim the M3.1A token is read as making.
    """
    first = _rehearse(repo_root, evidence_root)
    assert first.returncode == EXIT_OK

    stored = evidence_root / "reports" / "a1-a12.json"
    document = json.loads(stored.read_text())
    wrong = dict.fromkeys(document["derived_a_reachable"], 6)
    assert wrong != document["derived_a_reachable"], "the 7/11 routes make this a real forgery"
    document["derived_a_reachable"] = dict(wrong)
    document["tested_a_reachable"] = dict(wrong)
    document["unmeasured_routes"] = {}
    document["a_reachable_agrees"] = True
    document["a_reachable_fully_tested"] = True
    forged = evidence_root / "reports" / "forged_equal_but_wrong.json"
    forged.write_text(json.dumps(document))

    result = _run(
        [
            "m3",
            "rehearse-report",
            "--evidence-root",
            str(evidence_root),
            "--evidence",
            "reports/forged_equal_but_wrong.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" not in result.stdout


def test_a_stored_report_with_a_forged_fully_tested_flag_fails_inspection(
    repo_root: Path, evidence_root: Path
) -> None:
    """A non-empty `unmeasured_routes` refutes the flag beside it, whatever the flag says."""
    first = _rehearse(repo_root, evidence_root)
    assert first.returncode == EXIT_OK

    stored = evidence_root / "reports" / "a1-a12.json"
    document = json.loads(stored.read_text())
    document["a_reachable_fully_tested"] = True
    document["unmeasured_routes"] = {"sec_edgar_calendar_announcement": "not witnessed"}
    forged = evidence_root / "reports" / "forged_flag.json"
    forged.write_text(json.dumps(document))

    result = _run(
        [
            "m3",
            "rehearse-report",
            "--evidence-root",
            str(evidence_root),
            "--evidence",
            "reports/forged_flag.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE


def test_an_unmodified_stored_report_still_inspects_clean(
    repo_root: Path, evidence_root: Path
) -> None:
    """The inverse control: the stricter inspection must not refuse a genuine record."""
    first = _rehearse(repo_root, evidence_root)
    assert first.returncode == EXIT_OK

    stored = evidence_root / "reports" / "a1-a12.json"
    result = _run(
        [
            "m3",
            "rehearse-report",
            "--evidence-root",
            str(evidence_root),
            "--evidence",
            f"reports/{stored.name}",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_OK
    assert "A_reachable fully tested : yes" in " ".join(result.stdout.split())


def test_the_operator_manifest_branch_does_not_change_the_witness_requirement(
    repo_root: Path, evidence_root: Path, tmp_path: Path
) -> None:
    """Decision 029 §4.1: the witness survives unchanged in both manifest branches.

    An empty approved manifest makes `U(sec_edgar_calendar_announcement)` zero and a non-empty one
    makes it positive, so the route's *ceiling contribution* differs — but Gate F §3.10's evidence
    obligation does not, and the rehearsal never reads the operator manifest at all.
    """
    # A separate root per branch: the manifest is a write-once artifact, so one root cannot hold
    # both an empty and a populated version of it.
    populated_root = tmp_path / "populated-evidence"
    populated_root.mkdir()

    empty = _plan(repo_root, evidence_root, "plans/branch.json", approved_entries=0)
    populated = _plan(repo_root, populated_root, "plans/branch.json", approved_entries=2)
    assert empty.returncode == EXIT_OK
    assert populated.returncode == EXIT_OK

    def _announcement_count(root: Path) -> int:
        document = json.loads((root / "plans" / "branch.json").read_text())
        route = next(
            row
            for row in document["routes"]
            if row["source_id"] == "sec_edgar_calendar_announcement"
        )
        return int(route["planned_unique_logical_requests"])

    assert _announcement_count(evidence_root) == 0
    assert _announcement_count(populated_root) == 2

    rehearsed = _rehearse(repo_root, evidence_root)
    assert rehearsed.returncode == EXIT_OK
    report = json.loads((evidence_root / "reports" / "a1-a12.json").read_text())
    assert report["unmeasured_routes"] == {}
    assert report["a_reachable_fully_tested"] is True
    assert report["tested_a_reachable"]["sec_edgar_calendar_announcement"] == 6


# --------------------------------------------------------------------------- #
# plan-requests takes exactly the §9 argument list
# --------------------------------------------------------------------------- #
def test_plan_requests_rejects_an_undeclared_open_quarter_flag(
    repo_root: Path, evidence_root: Path
) -> None:
    """§9's argument list has no open-quarter switch.

    The flag changed the planned quarter set and therefore the hard ceiling the owner signs, so it
    is not a convenience: an invocation that names it must be a usage error rather than a quietly
    different budget.
    """
    _write_manifest(evidence_root, 0)
    result = _run(
        [
            "m3",
            "plan-requests",
            "--evidence-root",
            str(evidence_root),
            "--calendar-evidence-manifest",
            "manifest.json",
            "--catalog",
            "catalog/catalog.db",
            "--coverage-start",
            "2024-01-01",
            "--coverage-end",
            "2024-09-30",
            "--as-of",
            "2024-08-15",
            "--calendar-year",
            "2024",
            "--include-open-quarter",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_USAGE
    assert "--include-open-quarter" in result.stderr


def test_the_plan_always_excludes_the_provisional_open_quarter(
    repo_root: Path, evidence_root: Path
) -> None:
    """The inverse control for the removed flag.

    An as-of date inside an open quarter beyond the coverage end is exactly the invocation the flag
    used to change. The declared inputs must record the open quarter as excluded, so the ceiling is
    the closed-quarter one Decision 013 §1 requires and not a switchable value.
    """
    _write_manifest(evidence_root, 0)
    result = _run(
        [
            "m3",
            "plan-requests",
            "--evidence-root",
            str(evidence_root),
            "--calendar-evidence-manifest",
            "manifest.json",
            "--catalog",
            "catalog/catalog.db",
            "--coverage-start",
            "2024-01-01",
            "--coverage-end",
            "2024-09-30",
            "--as-of",
            "2024-08-15",
            "--calendar-year",
            "2024",
            "--plan-out",
            "plans/closed.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_OK
    document = json.loads((evidence_root / "plans" / "closed.json").read_text(encoding="utf-8"))
    assert document["inputs"]["include_open_quarter"] is False


# --------------------------------------------------------------------------- #
# Artifacts are write-once: re-running never overwrites an existing one (§11, §15)
# --------------------------------------------------------------------------- #
def test_rerunning_the_rehearsal_may_rewrite_byte_identical_evidence(
    repo_root: Path, evidence_root: Path
) -> None:
    """The inverse control. A write-once rule that refused every replay would be unusable."""
    first = _rehearse(repo_root, evidence_root, receipt_out="receipts/one.json")
    second = _rehearse(repo_root, evidence_root, receipt_out="receipts/two.json")

    assert first.returncode == EXIT_OK
    assert second.returncode == EXIT_OK, second.stderr


def test_the_rehearsal_refuses_to_overwrite_different_evidence(
    repo_root: Path, evidence_root: Path
) -> None:
    """§11: re-running never overwrites an existing artifact; §15: evidence is not rewritten."""
    _rehearse(repo_root, evidence_root, receipt_out="receipts/one.json")
    report = evidence_root / "reports" / "a1-a12.json"
    retained = b'{"retained":"operator evidence"}\n'
    report.write_bytes(retained)

    result = _rehearse(repo_root, evidence_root, receipt_out="receipts/two.json")

    assert result.returncode == EXIT_GATE_FAILURE
    assert "never overwrites an existing artifact" in result.stderr
    assert report.read_bytes() == retained, "the retained evidence was silently rewritten"
    assert str(evidence_root) not in result.stderr


def test_plan_requests_may_rewrite_a_byte_identical_plan(
    repo_root: Path, evidence_root: Path
) -> None:
    """The inverse control: two identical dry runs are the Gate F procedure, not an error."""
    _write_manifest(evidence_root, 0)
    arguments = [
        "m3",
        "plan-requests",
        "--evidence-root",
        str(evidence_root),
        "--calendar-evidence-manifest",
        "manifest.json",
        "--catalog",
        "catalog/catalog.db",
        "--coverage-start",
        "2024-01-01",
        "--coverage-end",
        "2024-06-30",
        "--as-of",
        "2024-06-30",
        "--calendar-year",
        "2024",
        "--plan-out",
        "plans/same.json",
    ]
    first = _run([*arguments, "--receipt-out", "receipts/one.json"], repo_root)
    second = _run([*arguments, "--receipt-out", "receipts/two.json"], repo_root)

    assert first.returncode == EXIT_OK
    assert second.returncode == EXIT_OK, second.stderr


def test_plan_requests_refuses_to_overwrite_a_different_plan(
    repo_root: Path, evidence_root: Path
) -> None:
    _plan(repo_root, evidence_root, out="plans/kept.json")
    stored = evidence_root / "plans" / "kept.json"
    retained = b'{"retained":"an approved plan"}\n'
    stored.write_bytes(retained)

    result = _plan(repo_root, evidence_root, out="plans/kept.json")

    assert result.returncode == EXIT_GATE_FAILURE
    assert "never overwrites an existing artifact" in result.stderr
    assert stored.read_bytes() == retained, "an approved plan was silently rewritten"


# --------------------------------------------------------------------------- #
# recovery-state
# --------------------------------------------------------------------------- #
def _recovery_inputs(repo_root: Path, evidence_root: Path) -> None:
    """A plan, a receipt chain head, and a migrated synthetic catalog below the evidence root."""
    from disclosure_drift.paths import DataTree
    from disclosure_drift.storage.catalog import CatalogWriter

    _plan(repo_root, evidence_root, out="plans/interrupted.json")
    tree = DataTree.from_root(evidence_root / "tree")
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()


def _recovery_state(
    repo_root: Path,
    evidence_root: Path,
    *,
    catalog: str = "catalog/sec_ingestion.sqlite3",
    data_root: str = "tree",
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "m3",
            "recovery-state",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/interrupted.json",
            "--receipt-chain-head",
            "receipts/plan.json",
            "--catalog",
            catalog,
            "--data-root",
            data_root,
        ],
        repo_root,
    )


def test_recovery_state_reports_a_determination_and_every_condition(
    repo_root: Path, evidence_root: Path
) -> None:
    """§9: the command prints the interruption point, the state, and one of the three verdicts."""
    _recovery_inputs(repo_root, evidence_root)

    result = _recovery_state(repo_root, evidence_root)

    normalized = " ".join(result.stdout.split())
    assert "Recovery determination" in normalized
    assert "nothing was repaired" in normalized
    for label in (
        "interruption state",
        "head completion status",
        "consumed physical attempts",
        "orphan objects",
        "partial files",
        "determination",
        # Decision 064 §4: reported beside the determination and separately from it, so an operator
        # can never read evidence certainty as permission to acquire again.
        "continuation permitted",
        "continuation remaining",
        "worst-case remaining attempts",
        "required action",
    ):
        assert label in normalized
    determination = next(
        line.split(":", 1)[1].strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("determination")
    )
    assert determination in {"SAFE", "UNSAFE", "UNDETERMINED"}
    # §9: exit 0 only for SAFE; the other two determinations exit 4.
    assert result.returncode == (EXIT_OK if determination == "SAFE" else EXIT_GATE_FAILURE)


def test_recovery_state_writes_nothing_it_inspected(repo_root: Path, evidence_root: Path) -> None:
    """§11 and stop condition 10: inspection never writes. Proven by byte comparison.

    SQLite's `-wal` and `-shm` sidecars are process-lifetime artefacts that appear and vanish
    around any connection, and a *strictly* read-only one leaves them behind because removing them
    would itself be a write — the same accepted treatment the transition-aware read-only test
    already applies (Decision 066 §4, R1). Everything else stays in scope, the writer lease
    included: what the claim is about is durable evidence — the catalog, the raw objects, the
    plans, and the receipts — and none of it may be added to, removed, or altered.
    """
    import hashlib

    def _durable() -> dict[Path, str]:
        return {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(evidence_root.rglob("*"))
            if path.is_file() and not path.name.endswith(("-wal", "-shm"))
        }

    _recovery_inputs(repo_root, evidence_root)
    before = _durable()

    _recovery_state(repo_root, evidence_root)

    assert _durable() == before


def test_recovery_state_takes_no_run_or_repair_flag(repo_root: Path, evidence_root: Path) -> None:
    """Ordinary receipt-chain mode rejects `--run` (it belongs only to receiptless mode, Decision
    051 §7.4) and there is no repair flag at all: the mode is never inferred or mixed.
    """
    for flag in ("--run", "--repair"):
        result = _run(
            [
                "m3",
                "recovery-state",
                "--evidence-root",
                str(evidence_root),
                "--plan",
                "plans/interrupted.json",
                "--receipt-chain-head",
                "receipts/plan.json",
                "--catalog",
                "catalog/sec_ingestion.sqlite3",
                "--data-root",
                "tree",
                flag,
            ],
            repo_root,
        )

        assert result.returncode == EXIT_USAGE
        assert flag in result.stderr


def _register_recovery_run(evidence_root: Path, run_id: str = "incident-run-01") -> None:
    """Register one acquisition run in the synthetic recovery catalog."""
    from disclosure_drift.m3.acquisition import register_acquisition_run
    from disclosure_drift.paths import DataTree

    tree = DataTree.from_root(evidence_root / "tree")
    register_acquisition_run(
        catalog_path=tree.catalog_database,
        lock_directory=tree.locks,
        census_run_id=run_id,
        window="M3.2A",
        started_at_utc="2026-08-01T12:00:00Z",
        detail="interrupted first invocation",
    )


def _receiptless_state(
    repo_root: Path,
    evidence_root: Path,
    *,
    run: str | None = "incident-run-01",
    receipt_head: str | None = None,
) -> subprocess.CompletedProcess[str]:
    argv = [
        "m3",
        "recovery-state",
        "--evidence-root",
        str(evidence_root),
        "--plan",
        "plans/interrupted.json",
        "--catalog",
        "catalog/sec_ingestion.sqlite3",
        "--data-root",
        "tree",
        "--receiptless-first-invocation",
    ]
    if run is not None:
        argv += ["--run", run]
    if receipt_head is not None:
        argv += ["--receipt-chain-head", receipt_head]
    return _run(argv, repo_root)


def test_recovery_state_receiptless_requires_run(repo_root: Path, evidence_root: Path) -> None:
    _recovery_inputs(repo_root, evidence_root)
    result = _receiptless_state(repo_root, evidence_root, run=None)
    assert result.returncode == EXIT_USAGE
    assert "--run" in result.stderr


def test_recovery_state_receiptless_conflicts_with_a_receipt_head(
    repo_root: Path, evidence_root: Path
) -> None:
    _recovery_inputs(repo_root, evidence_root)
    result = _receiptless_state(repo_root, evidence_root, receipt_head="receipts/plan.json")
    assert result.returncode == EXIT_USAGE  # argparse refuses the mutually exclusive combination


def test_recovery_state_requires_an_explicit_mode(repo_root: Path, evidence_root: Path) -> None:
    _recovery_inputs(repo_root, evidence_root)
    result = _run(
        [
            "m3",
            "recovery-state",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/interrupted.json",
            "--catalog",
            "catalog/sec_ingestion.sqlite3",
            "--data-root",
            "tree",
        ],
        repo_root,
    )
    assert result.returncode == EXIT_USAGE  # neither --receipt-chain-head nor receiptless was given


def test_recovery_state_receiptless_reports_a_non_safe_determination(
    repo_root: Path, evidence_root: Path
) -> None:
    _recovery_inputs(repo_root, evidence_root)
    _register_recovery_run(evidence_root)
    result = _receiptless_state(repo_root, evidence_root)

    determination = next(
        line.split(":", 1)[1].strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("determination")
    )
    # A receiptless first invocation is forensic only — never SAFE, never resume-eligible.
    assert determination in {"UNSAFE", "UNDETERMINED"}
    assert result.returncode == EXIT_GATE_FAILURE
    normalized = " ".join(result.stdout.split())
    assert "receipt chain length : 0" in normalized  # no chain was walked


def test_recovery_state_receiptless_refuses_an_unregistered_run(
    repo_root: Path, evidence_root: Path
) -> None:
    _recovery_inputs(repo_root, evidence_root)  # migrated catalog, but no run registered
    result = _receiptless_state(repo_root, evidence_root, run="never-registered")
    assert result.returncode == EXIT_GATE_FAILURE
    assert "does not resolve" in result.stderr


@pytest.mark.parametrize(
    "catalog",
    [
        "../../../../../../../etc/hosts",
        "/etc/hosts",
        "../../escaped.sqlite3",
    ],
)
def test_recovery_state_refuses_a_catalog_outside_the_evidence_root(
    repo_root: Path, evidence_root: Path, catalog: str
) -> None:
    """The catalog is an artifact argument, so the boundary binds it like every other one.

    Composing it with `--data-root` and opening the result directly let an absolute or climbing
    value reach any SQLite-readable file on the machine. The refusal names the bare filename only.
    """
    _recovery_inputs(repo_root, evidence_root)

    result = _recovery_state(repo_root, evidence_root, catalog=catalog)

    assert result.returncode == EXIT_GATE_FAILURE
    combined = result.stdout + result.stderr
    assert "artifact path" in result.stderr
    assert "evidence-root" in result.stderr or "evidence root" in result.stderr
    assert "/etc/hosts" not in combined
    assert str(evidence_root) not in combined
    # The refusal happens before inspection, so no determination is ever printed for it.
    assert "determination" not in combined


def test_a_contained_catalog_path_is_still_accepted(repo_root: Path, evidence_root: Path) -> None:
    """The inverse control: a boundary that refused every value would be equally broken.

    `tree/../tree/catalog/…` climbs and returns, staying inside the root, and must be accepted.
    """
    _recovery_inputs(repo_root, evidence_root)

    result = _recovery_state(
        repo_root, evidence_root, catalog="../tree/catalog/sec_ingestion.sqlite3"
    )

    assert "resolves outside the evidence root" not in result.stderr
    assert "determination" in result.stdout


# --------------------------------------------------------------------------- #
# The plan a resume is judged against is the stored one, not a rebuilt one
# --------------------------------------------------------------------------- #
def _catalog_with_satisfied_instances(evidence_root: Path, keys: tuple[str, ...]) -> None:
    """A synthetic catalog whose index instances are already retrieved and parse-usable.

    `plan-requests` excludes these before the plan is formed, so the stored plan has a *smaller*
    ceiling and a different hash than one rebuilt from its own recorded inputs would.
    """
    from disclosure_drift.paths import DataTree
    from disclosure_drift.sec.http_client import FetchResult
    from disclosure_drift.sec.observation_catalog import ObservationRecorder
    from disclosure_drift.sec.snapshots import SnapshotStore
    from disclosure_drift.storage.catalog import CatalogWriter

    tree = DataTree.from_root(evidence_root / "tree")
    tree.ensure_tree()
    # One retrieval the interrupted run had already completed, committed with its object on disk.
    # It is what the consumed attempt on the head receipt was spent on, so the headroom check has
    # a real completion to credit rather than an attempt charged against nothing.
    observation = SnapshotStore(tree).record(
        FetchResult(
            outcome="retrieved",
            source_id="sec_company_tickers",
            url="https://www.sec.gov/files/company_tickers.json",
            purpose="synthetic interrupted-run evidence",
            status=200,
            body=b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC"}}',
            etag='"synthetic"',
            declared_content_type="application/json",
            attempts=1,
        )
    )
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        ObservationRecorder(writer, tree).record(observation)
        for key in keys:
            year, quarter = key.split("QTR")
            writer.connection.execute(
                "INSERT OR REPLACE INTO census_index_instances (census_run_id, instance_key, "
                "year, quarter, required, retrieved, parse_usable, observation_id, "
                "recorded_at_utc) VALUES (?, ?, ?, ?, 1, 1, 1, NULL, '2024-07-01T00:00:00Z')",
                ("synthetic-run", key, int(year), int(quarter)),
            )
        ObservationRecorder(writer, tree).flush_projection()
    (evidence_root / "catalog").mkdir(parents=True, exist_ok=True)
    (evidence_root / "catalog" / "catalog.db").write_bytes(tree.catalog_database.read_bytes())


def _interrupted_head_receipt(evidence_root: Path, plan_sha256: str) -> None:
    """A live receipt describing an interruption and naming the plan the run was executing."""
    from disclosure_drift.m3.receipt import ExecutionReceipt

    receipt = ExecutionReceipt(
        command_name="m3 acquire",
        command_version="m3.2a/1.0",
        phase="M3.2A",
        invocation_mode="live",
        configuration_fingerprint="a" * 64,
        migration_chain_head="0013_m23_manifest_lifecycle_guards",
        started_at_utc="2026-08-01T12:00:00Z",
        completed_at_utc="2026-08-01T12:00:09Z",
        elapsed_seconds=9.0,
        source_registry_version="m2.2-source-registry/1.0",
        index_plan_policy_version="quarterly-index-instances/2.0",
        request_plan_schema_version="m3-request-plan/1.0",
        parser_versions={"company-tickers": "1.0"},
        acquisition_window="M3.2A",
        request_plan_id="plan-0001",
        request_plan_sha256=plan_sha256,
        approved_request_ceiling=200,
        planned_logical_request_count=7,
        maximum_physical_attempt_count=60,
        planned_per_route={"sec_company_tickers": 7},
        actual_logical_request_count=1,
        actual_physical_attempt_count=1,
        actual_per_route={
            "sec_company_tickers": {"logical_request_count": 1, "physical_attempt_count": 1}
        },
        response_classification_totals={
            "proceed": 1,
            "retry": 0,
            "retry_after": 0,
            "cooldown": 0,
            "fail": 0,
            "quarantine": 0,
        },
        status_code_totals={"200": 1},
        raw_object_count=0,
        duplicate_object_count=0,
        cache_hit_count=0,
        not_modified_count=0,
        quarantined_object_count=0,
        redirect_hop_count=0,
        cooldown_count=0,
        schema_drift_outcome="none",
        schema_drift_event_count=0,
        completion_status="interrupted",
        reason_code="SEC_ACQUISITION_INTERRUPTED",
        reason_detail="the acquisition was interrupted before any byte reached the raw store.",
        interruption_state="before_raw_store_write",
    )
    head = evidence_root / "receipts" / "head.json"
    head.parent.mkdir(parents=True, exist_ok=True)
    head.write_bytes(receipt.canonical_bytes())


def _interrupted_run(
    repo_root: Path, evidence_root: Path, *, satisfied: tuple[str, ...]
) -> dict[str, object]:
    """A stored plan, a matching head receipt, and a clean synthetic store."""
    import hashlib

    _catalog_with_satisfied_instances(evidence_root, satisfied)
    _write_manifest(evidence_root, 0)
    result = _run(
        [
            "m3",
            "plan-requests",
            "--evidence-root",
            str(evidence_root),
            "--calendar-evidence-manifest",
            "manifest.json",
            "--catalog",
            "catalog/catalog.db",
            "--coverage-start",
            "2000-01-01",
            "--coverage-end",
            "2024-06-30",
            "--as-of",
            "2024-06-30",
            "--calendar-year",
            "2024",
            "--plan-out",
            "plans/interrupted.json",
            "--receipt-out",
            "receipts/plan.json",
        ],
        repo_root,
    )
    assert result.returncode == EXIT_OK, result.stderr
    stored = (evidence_root / "plans" / "interrupted.json").read_bytes()
    _interrupted_head_receipt(evidence_root, hashlib.sha256(stored).hexdigest())
    document = json.loads(stored.decode("utf-8"))
    assert isinstance(document, dict)
    return document


def _determination(result: subprocess.CompletedProcess[str]) -> str:
    return next(
        line.split(":", 1)[1].strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("determination")
    )


def _condition(result: subprocess.CompletedProcess[str], number: str) -> str:
    line = next(
        item for item in result.stdout.splitlines() if item.strip().startswith(f"{number} ")
    )
    return "NOT MET" if "NOT MET" in line else "MET"


def test_a_plan_that_had_cache_hits_is_still_judged_against_itself(
    repo_root: Path, evidence_root: Path
) -> None:
    """The plan a run was executing is the stored document, never a rebuild from its inputs.

    Already-satisfied instances are excluded *before* the plan is formed and the satisfied set is
    not part of the plan payload, so a rebuild plans them again: a larger ceiling and a different
    hash. Judging the run against that rebuild made condition 8.10 fail for the very plan being
    executed — an inverse-control failure, a gate refusing the lawful case.
    """
    document = _interrupted_run(repo_root, evidence_root, satisfied=("2020QTR1",))
    assert document["expected_cache_hits"] == 1, "the fixture did not actually produce a cache hit"

    result = _run(
        [
            "m3",
            "recovery-state",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/interrupted.json",
            "--receipt-chain-head",
            "receipts/head.json",
            "--catalog",
            "catalog/sec_ingestion.sqlite3",
            "--data-root",
            "tree",
        ],
        repo_root,
    )

    assert _condition(result, "8.10") == "MET", result.stdout
    assert _condition(result, "8.8") == "MET", result.stdout
    assert _determination(result) == "SAFE", result.stdout
    assert result.returncode == EXIT_OK

    # And the fixture really is the case a rebuild would misjudge: replanning from the plan's own
    # recorded inputs, which carry no satisfied set, yields a larger ceiling and a different hash.
    import hashlib
    from datetime import date

    from disclosure_drift.m3.request_plan import build_m3_2a_request_plan

    inputs = document["inputs"]
    assert isinstance(inputs, dict)
    rebuilt = build_m3_2a_request_plan(
        coverage_start=date.fromisoformat(str(inputs["coverage_start"])),
        coverage_end=date.fromisoformat(str(inputs["coverage_end"])),
        as_of_date=date.fromisoformat(str(inputs["as_of_date"])),
        include_open_quarter=bool(inputs["include_open_quarter"]),
        calendar_year=int(inputs["calendar_year"]),
        calendar_evidence_entry_count=int(inputs["calendar_evidence_entry_count"]),
        already_satisfied_index_keys=frozenset(),
        requests_per_second=float(inputs["requests_per_second"]),
    )
    totals = document["totals"]
    assert isinstance(totals, dict)
    stored_bytes = (evidence_root / "plans" / "interrupted.json").read_bytes()
    assert rebuilt.hard_request_ceiling > int(str(totals["hard_request_ceiling"]))
    assert rebuilt.request_plan_sha256 != hashlib.sha256(stored_bytes).hexdigest()


def test_a_genuinely_unsafe_state_is_still_unsafe(repo_root: Path, evidence_root: Path) -> None:
    """The inverse control. A gate that now accepts everything is as broken as one that refused."""
    _interrupted_run(repo_root, evidence_root, satisfied=("2020QTR1",))
    orphan = evidence_root / "tree" / "raw" / "indexes" / "synthetic" / "orphan.bin"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_bytes(b"an object on disk with no committed row")

    result = _run(
        [
            "m3",
            "recovery-state",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/interrupted.json",
            "--receipt-chain-head",
            "receipts/head.json",
            "--catalog",
            "catalog/sec_ingestion.sqlite3",
            "--data-root",
            "tree",
        ],
        repo_root,
    )

    assert _condition(result, "8.5") == "NOT MET", result.stdout
    assert _determination(result) == "UNSAFE", result.stdout
    assert result.returncode == EXIT_GATE_FAILURE
    assert orphan.is_file(), "inspection deleted the orphan it was only supposed to report"


def test_a_plan_whose_bytes_were_edited_is_refused(repo_root: Path, evidence_root: Path) -> None:
    """The stored document is the authority, so it has to hash to what it claims.

    Trusting the parsed fields alone would let a hand-edited plan assert a ceiling and a hash its
    own bytes do not produce, which is exactly the substitution the plan hash exists to prevent.
    """
    _interrupted_run(repo_root, evidence_root, satisfied=("2020QTR1",))
    stored = evidence_root / "plans" / "interrupted.json"
    original = stored.read_bytes()
    # A derived per-route total edited to disagree with the route it is derived from. Reading the
    # parsed fields alone would recompute it and never notice; the bytes are the authority.
    tampered = original.replace(
        b'"maximum_physical_attempts":', b'"maximum_physical_attempts":9', 1
    )
    assert tampered != original
    stored.write_bytes(tampered)

    result = _run(
        [
            "m3",
            "recovery-state",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/interrupted.json",
            "--receipt-chain-head",
            "receipts/head.json",
            "--catalog",
            "catalog/sec_ingestion.sqlite3",
            "--data-root",
            "tree",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "does not reproduce the stored bytes" in result.stderr
    assert "determination" not in result.stdout
    assert str(evidence_root) not in result.stdout + result.stderr


# --------------------------------------------------------------------------- #
# §11: the synthetic data tree and catalog live below the external evidence root
# --------------------------------------------------------------------------- #
def test_rehearse_writes_its_synthetic_tree_below_the_evidence_root(
    repo_root: Path, evidence_root: Path, tmp_path: Path
) -> None:
    """§11 names the location, not just the isolation: "below the external evidence root".

    A system temporary directory is isolated but outside the boundary the operator named, so this
    watches the temp directory the harness would otherwise have used and requires it untouched,
    while requiring the rehearsal to have opened its scratch root inside the evidence root.
    """
    import tempfile

    system_temp = tmp_path / "system-temp"
    system_temp.mkdir()
    observed: list[str] = []
    real_temporary_directory = tempfile.TemporaryDirectory

    def _watched(*args: object, **kwargs: object) -> object:
        observed.append(str(kwargs.get("dir", "")))
        return real_temporary_directory(*args, **kwargs)  # type: ignore[arg-type]

    from disclosure_drift.m3 import rehearsal

    original = rehearsal.tempfile.TemporaryDirectory
    rehearsal.tempfile.TemporaryDirectory = _watched  # type: ignore[assignment,misc]
    try:
        rehearsal.run_rehearsal(["A1", "A9", "A11", "A12"], workspace_root=evidence_root)
    finally:
        rehearsal.tempfile.TemporaryDirectory = original  # type: ignore[misc]

    assert observed, "the rehearsal opened no scratch directory at all"
    for location in observed:
        assert location, "a scratch directory was opened without an explicit parent directory"
        assert Path(location).is_relative_to(evidence_root), (
            f"a synthetic data tree was opened at {location}, which is not below the evidence root"
        )


def test_rehearse_leaves_no_synthetic_tree_behind_and_reruns_identically(
    repo_root: Path, evidence_root: Path
) -> None:
    """Moving the tree must not defeat re-runnability or the write-once artifact rule.

    Gate F runs the command twice and compares bytes, so the synthetic tree has to be removed and
    the named artifacts have to remain byte-identical across runs.
    """
    first = _rehearse(repo_root, evidence_root, receipt_out="receipts/one.json")
    after_first = sorted(
        str(path.relative_to(evidence_root)) for path in evidence_root.rglob("*") if path.is_file()
    )
    evidence = (evidence_root / "reports" / "a1-a12.json").read_bytes()

    second = _rehearse(repo_root, evidence_root, receipt_out="receipts/two.json")

    assert first.returncode == EXIT_OK, first.stderr
    assert second.returncode == EXIT_OK, second.stderr
    assert (evidence_root / "reports" / "a1-a12.json").read_bytes() == evidence
    assert not (evidence_root / "rehearsal-workspace").exists(), (
        "the scratch workspace survived the invocation"
    )
    leftovers = [name for name in after_first if "rehearsal-workspace" in name]
    assert not leftovers, f"synthetic artifacts were retained as operator evidence: {leftovers}"


# --------------------------------------------------------------------------- #
# Milestone 3.2 operator surfaces (stage T2.5-T2.6, Decision 045 §4)
#
# Five of the six surfaces are offline in every mode. Only `m3 acquire --live` has a live path,
# and every test here proves it is refused before anything is constructed: no receipt is written,
# no HTTP library is imported, and no socket is touched.
# --------------------------------------------------------------------------- #
EXIT_STAGE_NOT_ENABLED = 3

M3_2_COMMANDS = (
    "acquire",
    "derive-dependent-plan",
    "reconcile-requests",
    "show-drift",
    "recover",
)

#: A controlled fixture value for the identity-gate tests. It uses the RFC-reserved `.invalid`
#: TLD, so it is not, and cannot become, a real contact address. The canonical validator refuses
#: every reserved placeholder domain, which is exactly the property the identity-gate tests below
#: assert: this suite never fabricates an identity that would pass a live gate (Decision 045 §11).
FIXTURE_PLACEHOLDER_IDENTITY = "Disclosure Drift CLI Fixture (cli-fixture@example.invalid)"


def _config_with_network(tmp_path: Path, repo_root: Path, *, enabled: bool, acquire: bool) -> Path:
    """Write a configuration that differs from the tracked one only in the network switches.

    The one further difference applies to the acquisition configuration alone: it raises
    ``requests_per_second`` to the schema maximum so the suite spends less of its time asleep. A
    clean M3.2A run executes the frozen 75-request plan, which at the tracked 4/s is roughly
    nineteen seconds of real sleeping per invocation and nothing else. The value stays inside the
    accepted bound — the project maximum is 8/s — so this is still a configuration the validator
    accepts, not a relaxed one. No assertion here observes spacing: the limiter has its own unit
    tests, and the API-level acquisition test injects a deterministic clock rather than relying on
    this value.
    """
    source = (repo_root / "configs" / "project.yaml").read_text(encoding="utf-8")
    replaced = source.replace("  enabled: false", f"  enabled: {str(enabled).lower()}", 1)
    replaced = replaced.replace(
        "  m3_acquire_enabled: false", f"  m3_acquire_enabled: {str(acquire).lower()}", 1
    )
    if acquire:
        replaced = replaced.replace("  requests_per_second: 4.0", "  requests_per_second: 8.0", 1)
    # A distinct name per combination: two configurations built in one test must not alias.
    destination = tmp_path / f"network-{str(enabled).lower()}-{str(acquire).lower()}.yaml"
    destination.write_text(replaced, encoding="utf-8")
    return destination


def _approved_plan(repo_root: Path, evidence_root: Path) -> Mapping[str, object]:
    """Derive and store one real M3.2A plan, and return its document."""
    _write_manifest(evidence_root)
    result = _run(
        [
            "m3",
            "plan-requests",
            "--evidence-root",
            str(evidence_root),
            "--coverage-start",
            "2010-01-01",
            "--coverage-end",
            "2010-06-30",
            "--as-of",
            "2010-07-01",
            "--calendar-year",
            "2010",
            "--calendar-evidence-manifest",
            "manifest.json",
            "--catalog",
            "runs/catalog.sqlite3",
            "--plan-out",
            "plans/m3_2a.json",
            "--receipt-out",
            "receipts/plan.json",
        ],
        repo_root,
    )
    assert result.returncode == EXIT_OK, result.stderr
    document = json.loads((evidence_root / "plans" / "m3_2a.json").read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _receipt_files(evidence_root: Path) -> list[str]:
    """Every receipt-looking artifact below the evidence root, for no-receipt assertions.

    The whole *relative path* is matched, not just the filename. Matching the name alone missed a
    receipt written as ``receipts/live.json`` — the exact name the operator interface uses — which
    made every no-receipt assertion weaker than it read.
    """
    return sorted(
        str(path.relative_to(evidence_root))
        for path in evidence_root.rglob("*")
        if path.is_file() and "receipt" in str(path.relative_to(evidence_root)).lower()
    )


@pytest.mark.parametrize("command", M3_2_COMMANDS)
def test_every_m3_2_command_is_recognized_by_the_parser(repo_root: Path, command: str) -> None:
    """Positive control: each surface parses, so its behaviour is reached rather than a typo."""
    result = _run(["m3", command, "--help"], repo_root)

    assert result.returncode == EXIT_OK
    assert command in result.stdout


def test_acquire_requires_an_explicit_mode(repo_root: Path, evidence_root: Path) -> None:
    """Neither mode is a default: acquire with no mode flag is a usage failure, never a run."""
    result = _run(["m3", "acquire", "--evidence-root", str(evidence_root)], repo_root)

    assert result.returncode == EXIT_USAGE
    assert "--show-scope or --live is required" in result.stderr
    assert "Traceback" not in result.stderr


def test_acquire_refuses_both_modes_at_once(repo_root: Path, evidence_root: Path) -> None:
    """A scope report never acquires, so the two modes cannot be requested together."""
    result = _run(
        ["m3", "acquire", "--evidence-root", str(evidence_root), "--live", "--show-scope"],
        repo_root,
    )

    assert result.returncode == EXIT_USAGE
    assert "mutually exclusive" in result.stderr


def test_show_scope_reports_the_window_authority_and_places_no_request(
    repo_root: Path, evidence_root: Path
) -> None:
    """`--show-scope` reports the required scope deterministically and writes nothing."""
    document = _approved_plan(repo_root, evidence_root)
    before = sorted(str(path.relative_to(evidence_root)) for path in evidence_root.rglob("*"))

    result = _run(
        [
            "m3",
            "acquire",
            "--evidence-root",
            str(evidence_root),
            "--show-scope",
            "--plan",
            "plans/m3_2a.json",
            "--window",
            "M3.2A",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_OK, result.stderr
    for required in (
        "allowed hosts",
        "method",
        "route allowlist",
        "prohibited route/family set",
        "approved plan sha256",
        "approved request ceiling",
        "consumed-count baseline",
    ):
        assert required in result.stdout
    assert "GET" in result.stdout
    assert str(document["totals"]["hard_request_ceiling"]) in result.stdout  # type: ignore[index]
    assert "consumed-count baseline" in result.stdout
    baseline = next(
        line for line in result.stdout.splitlines() if "consumed-count baseline" in line
    )
    assert baseline.rsplit(":", 1)[1].strip() == "0"
    # Zero artifacts: no catalog, no receipt, no report.
    assert sorted(str(path.relative_to(evidence_root)) for path in evidence_root.rglob("*")) == (
        before
    )


def test_show_scope_is_byte_deterministic(repo_root: Path, evidence_root: Path) -> None:
    """Positive control: two identical scope reports agree exactly, so the report is derived."""
    _approved_plan(repo_root, evidence_root)
    arguments = [
        "m3",
        "acquire",
        "--evidence-root",
        str(evidence_root),
        "--show-scope",
        "--plan",
        "plans/m3_2a.json",
        "--window",
        "M3.2A",
    ]

    first = _run(arguments, repo_root)
    second = _run(arguments, repo_root)

    assert first.returncode == second.returncode == EXIT_OK
    assert first.stdout == second.stdout


def test_show_scope_refuses_a_plan_for_another_window(repo_root: Path, evidence_root: Path) -> None:
    """A plan is never reported against a window it was not built for."""
    _approved_plan(repo_root, evidence_root)

    result = _run(
        [
            "m3",
            "acquire",
            "--evidence-root",
            str(evidence_root),
            "--show-scope",
            "--plan",
            "plans/m3_2a.json",
            "--window",
            "M3.2B",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "window" in result.stderr


def test_show_scope_requires_its_governed_inputs(repo_root: Path, evidence_root: Path) -> None:
    result = _run(
        ["m3", "acquire", "--evidence-root", str(evidence_root), "--show-scope"], repo_root
    )

    assert result.returncode == EXIT_USAGE
    assert "--plan" in result.stderr
    assert "--window" in result.stderr


@pytest.mark.parametrize(
    ("enabled", "acquire", "identity", "expected"),
    [
        (False, False, False, EXIT_STAGE_NOT_ENABLED),
        (False, True, False, EXIT_STAGE_NOT_ENABLED),
        (True, False, False, EXIT_STAGE_NOT_ENABLED),
        (True, True, False, EXIT_STAGE_NOT_ENABLED),
    ],
)
def test_live_acquire_refuses_every_incomplete_conjunction(
    repo_root: Path,
    tmp_path: Path,
    evidence_root: Path,
    enabled: bool,
    acquire: bool,
    identity: bool,
    expected: int,
) -> None:
    """Each live gate refuses on its own, and none of them writes a receipt.

    The rows walk the conjunction one element at a time: the global switch, the acquire-scoped
    switch, and the contact identity. Every row is exit 3 - a live operator gate unavailable or
    disabled - and no row leaves an artifact behind.
    """
    document = _approved_plan(repo_root, evidence_root)
    before = _receipt_files(evidence_root)
    config = _config_with_network(tmp_path, repo_root, enabled=enabled, acquire=acquire)
    environment = (
        {"DISCLOSURE_DRIFT_SEC_USER_AGENT": FIXTURE_PLACEHOLDER_IDENTITY} if identity else {}
    )

    result = _run(
        [
            "m3",
            "acquire",
            "--config",
            str(config),
            "--evidence-root",
            str(evidence_root),
            "--live",
            "--plan",
            "plans/m3_2a.json",
            "--window",
            "M3.2A",
            "--ceiling",
            str(document["totals"]["hard_request_ceiling"]),  # type: ignore[index]
            "--catalog",
            "catalog.sqlite3",
            "--data-root",
            "runs/live/data",
            "--receipt-out",
            "receipts/live.json",
        ],
        repo_root,
        env=environment,
    )

    assert result.returncode == expected, result.stderr
    assert "Traceback" not in result.stderr
    assert _receipt_files(evidence_root) == before, "a refused live invocation wrote a receipt"


def test_the_switch_rungs_open_before_the_identity_rung(
    repo_root: Path, tmp_path: Path, evidence_root: Path
) -> None:
    """Positive control for the gate ladder: it is not refusing everything at its first rung.

    With both tracked switches true and a placeholder identity supplied, the refusal names the
    *identity* gate rather than either switch - which proves the two switch rungs were evaluated
    and passed. It stops there deliberately: the canonical validator refuses every RFC-reserved
    placeholder domain, and Decision 045 §11 forbids fabricating an identity that would pass a
    live gate. The remaining conjunction elements - exact plan hash, exact window, exact ceiling
    equality, run registration ordering - are proved at the unit layer against an explicitly
    constructed operator gate, where the fixture values are controlled and no identity is needed.
    """
    document = _approved_plan(repo_root, evidence_root)
    before = _receipt_files(evidence_root)
    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)

    result = _run(
        [
            "m3",
            "acquire",
            "--config",
            str(config),
            "--evidence-root",
            str(evidence_root),
            "--live",
            "--plan",
            "plans/m3_2a.json",
            "--window",
            "M3.2A",
            "--ceiling",
            str(document["totals"]["hard_request_ceiling"]),  # type: ignore[index]
            "--catalog",
            "catalog.sqlite3",
            "--data-root",
            "runs/live/data",
            "--receipt-out",
            "receipts/live.json",
        ],
        repo_root,
        env={"DISCLOSURE_DRIFT_SEC_USER_AGENT": FIXTURE_PLACEHOLDER_IDENTITY},
    )

    assert result.returncode == EXIT_STAGE_NOT_ENABLED, result.stderr
    assert "SEC contact identity" in result.stderr
    assert "network.enabled" not in result.stderr
    assert "m3_acquire_enabled" not in result.stderr
    assert _receipt_files(evidence_root) == before


def test_live_acquire_requires_its_governed_arguments(
    repo_root: Path, tmp_path: Path, evidence_root: Path
) -> None:
    """A missing governed argument is a usage failure, never a silently defaulted run."""
    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)

    result = _run(
        ["m3", "acquire", "--config", str(config), "--evidence-root", str(evidence_root), "--live"],
        repo_root,
        env={"DISCLOSURE_DRIFT_SEC_USER_AGENT": FIXTURE_PLACEHOLDER_IDENTITY},
    )

    assert result.returncode == EXIT_USAGE
    for required in (
        "--plan",
        "--window",
        "--ceiling",
        "--catalog",
        "--data-root",
        "--receipt-out",
    ):
        assert required in result.stderr


def test_the_acquire_configuration_fixture_really_sets_both_switches(
    repo_root: Path, tmp_path: Path
) -> None:
    """Positive control: the conjunction fixture is not vacuous — it writes the true values."""
    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    text = config.read_text(encoding="utf-8")

    assert "  enabled: true" in text
    assert "  m3_acquire_enabled: true" in text


def test_the_configuration_fixture_does_not_alias_between_combinations(
    repo_root: Path, tmp_path: Path
) -> None:
    """Positive control: two combinations built in one test are distinct files."""
    acquire_on = _config_with_network(tmp_path, repo_root, enabled=False, acquire=True)
    acquire_off = _config_with_network(tmp_path, repo_root, enabled=False, acquire=False)

    assert acquire_on != acquire_off
    assert "m3_acquire_enabled: true" in acquire_on.read_text(encoding="utf-8")
    assert "m3_acquire_enabled: false" in acquire_off.read_text(encoding="utf-8")


def test_derive_dependent_plan_refuses_a_transport_capable_configuration(
    repo_root: Path, tmp_path: Path, evidence_root: Path
) -> None:
    """A configuration that could acquire is never the one that derives (Decision 045 §4.3)."""
    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=False)
    (evidence_root / "set.json").write_text("{}", encoding="utf-8")

    result = _run(
        [
            "m3",
            "derive-dependent-plan",
            "--config",
            str(config),
            "--evidence-root",
            str(evidence_root),
            "--from-window",
            "M3.2A",
            "--catalog",
            "catalog.sqlite3",
            "--data-root",
            "runs/data",
            "--reconciliation-set",
            "set.json",
            "--plan-out",
            "plans/m3_2b.json",
            "--receipt-out",
            "receipts/dependent.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "transport-capable" in result.stderr
    assert not (evidence_root / "plans" / "m3_2b.json").exists()
    assert not (evidence_root / "receipts" / "dependent.json").exists()


def test_derive_dependent_plan_refuses_a_source_window_other_than_m3_2a(
    repo_root: Path, evidence_root: Path
) -> None:
    (evidence_root / "set.json").write_text("{}", encoding="utf-8")

    result = _run(
        [
            "m3",
            "derive-dependent-plan",
            "--evidence-root",
            str(evidence_root),
            "--from-window",
            "M3.2B",
            "--catalog",
            "catalog.sqlite3",
            "--data-root",
            "runs/data",
            "--reconciliation-set",
            "set.json",
            "--plan-out",
            "plans/m3_2b.json",
            "--receipt-out",
            "receipts/dependent.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "M3.2A" in result.stderr
    assert not (evidence_root / "plans" / "m3_2b.json").exists()


def test_show_drift_refuses_an_unknown_run(repo_root: Path, evidence_root: Path) -> None:
    """There is no global-drift fallback: an unknown run identity fails closed with exit 4."""
    result = _run(
        [
            "m3",
            "show-drift",
            "--evidence-root",
            str(evidence_root),
            "--catalog",
            "catalog.sqlite3",
            "--run",
            "not-a-registered-run",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "Traceback" not in result.stderr
    assert _receipt_files(evidence_root) == []


def test_recover_refuses_an_unknown_run(repo_root: Path, evidence_root: Path) -> None:
    """Every mutating recovery action requires an already-registered M3.2 run identity."""
    result = _run(
        [
            "m3",
            "recover",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/m3_2a.json",
            "--receipt-chain-head",
            "receipts/head.json",
            "--catalog",
            "catalog.sqlite3",
            "--data-root",
            "runs/data",
            "--run",
            "fabricated-run-identity",
            "--action",
            "rebuild-projection",
            "--event",
            "census_source_observations.jsonl",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "Traceback" not in result.stderr


def test_recover_rejects_an_unregistered_action(repo_root: Path, evidence_root: Path) -> None:
    """Positive control: the action vocabulary is closed at the parser boundary."""
    result = _run(
        [
            "m3",
            "recover",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/m3_2a.json",
            "--receipt-chain-head",
            "receipts/head.json",
            "--catalog",
            "catalog.sqlite3",
            "--data-root",
            "runs/data",
            "--run",
            "any-run",
            "--action",
            "delete-everything",
            "--event",
            "target",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_USAGE


def test_no_refused_m3_2_command_emits_a_token_or_a_receipt(
    repo_root: Path, evidence_root: Path
) -> None:
    """No refusal may emit a completion token or leave a receipt behind."""
    invocations = (
        ["m3", "acquire", "--evidence-root", str(evidence_root)],
        ["m3", "show-drift", "--evidence-root", str(evidence_root), "--catalog", "c", "--run", "r"],
    )
    for arguments in invocations:
        result = _run(arguments, repo_root)
        combined = result.stdout + result.stderr
        assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" not in combined
        assert "M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION" not in combined
        assert "M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED" not in combined
        assert "receipt_id" not in combined

    assert _receipt_files(evidence_root) == []


def test_an_m3_2_refusal_discloses_no_identity_or_private_path(
    repo_root: Path, tmp_path: Path, evidence_root: Path
) -> None:
    """Not even with a real-looking identity in the environment and every switch enabled."""
    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    for command in M3_2_COMMANDS:
        result = _run(
            ["m3", command, "--config", str(config), "--evidence-root", str(evidence_root)],
            repo_root,
            env={"DISCLOSURE_DRIFT_SEC_USER_AGENT": FIXTURE_PLACEHOLDER_IDENTITY},
        )
        combined = result.stdout + result.stderr
        for marker in ("/Users/", "/home/", "C:\\Users", "@", "Authorization", "Bearer"):
            assert marker not in combined, f"m3 {command} disclosed {marker!r}"


def test_an_invalid_m3_2_argument_fails_at_the_parser_boundary(repo_root: Path) -> None:
    """Positive control: the parser still rejects an unknown option before any handler runs."""
    result = _run(["m3", "acquire", "--not-a-real-option"], repo_root)

    assert result.returncode == EXIT_USAGE


def _enclosing_function(lines: list[str], index: int) -> str:
    """The name of the module-level function whose body contains ``lines[index]``."""
    for number in range(index, -1, -1):
        if lines[number].startswith("def "):
            return lines[number].removeprefix("def ").split("(", 1)[0]
    return "<module scope>"


def _transport_reference_lines(source: str) -> list[int]:
    """Executable (non-comment, non-docstring-prose) references to the transport implementation."""
    return [
        number
        for number, line in enumerate(source.splitlines(), start=1)
        if "HttpxTransport" in line and not line.lstrip().startswith(("#", "*", '"', "'"))
    ]


def test_only_one_live_transport_construction_site_exists_on_the_m3_path(
    repo_root: Path,
) -> None:
    """Structural proof: the Milestone 3.2 path constructs a transport at exactly one site.

    Decision 045 §4.2 and §6 permit one auditable construction site for this stage. The proof is
    threefold: the acquisition driver declares no HTTP library among its module-level imports, so
    importing it builds nothing; across the whole M3 path plus the CLI the only executable
    references to a transport implementation are in ``m3/acquisition.py``; and every one of those
    references lies inside ``default_live_transport_factory``.

    ``sec/census_orchestrator.py`` is deliberately out of scope. It is the accepted, pre-existing
    Stage M2.2 census caller and a prohibited path for this stage: its construction site predates
    Decision 045 and is not the M3.2 one under test.
    """
    package = repo_root / "src" / "disclosure_drift"
    driver = package / "m3" / "acquisition.py"
    source = driver.read_text(encoding="utf-8")

    module_level = [
        line.strip() for line in source.splitlines() if line.startswith(("import ", "from "))
    ]
    assert module_level, "the driver declares imports at module level"
    for line in module_level:
        for forbidden in ("httpx", "socket", "urllib", "requests"):
            assert forbidden not in line, f"the driver must not import a transport: {line}"

    m3_path = [*sorted((package / "m3").rglob("*.py")), package / "cli.py"]
    elsewhere = [
        str(path.relative_to(package))
        for path in m3_path
        if path != driver and _transport_reference_lines(path.read_text(encoding="utf-8"))
    ]
    assert elsewhere == [], f"a transport is referenced outside the one site: {elsewhere}"

    lines = source.splitlines()
    references = _transport_reference_lines(source)
    assert references, "the driver no longer carries its construction site"
    enclosing = {_enclosing_function(lines, number - 1) for number in references}
    assert enclosing == {"default_live_transport_factory"}, enclosing


def test_the_construction_site_is_lazy_and_inside_the_factory_body(repo_root: Path) -> None:
    """Positive control: the one import is *inside* the factory, not at module scope.

    A module-level import would load the HTTP library on every import of the package, which is
    exactly what the no-network property depends on not happening. This is the complement of the
    test above: that one proves nothing references a transport elsewhere, this one proves the
    single reference is not itself a module-level import.
    """
    source = (repo_root / "src" / "disclosure_drift" / "m3" / "acquisition.py").read_text(
        encoding="utf-8"
    )
    lines = source.splitlines()
    imports = [
        number
        for number in _transport_reference_lines(source)
        if lines[number - 1].lstrip().startswith("from ")
    ]

    assert len(imports) == 1, "there is exactly one transport import"
    assert lines[imports[0] - 1].startswith("    "), "the transport import is not lazy"


@pytest.mark.parametrize("command", M3_2_COMMANDS)
def test_no_http_library_is_imported_by_a_refusal(repo_root: Path, command: str) -> None:
    """Runtime proof: refusing loads no HTTP library, so no transport was constructed.

    ``httpx`` is imported lazily and only where a transport is actually built, so its absence
    from ``sys.modules`` after a refusal proves the construction site was never reached. The
    policy module ``disclosure_drift.sec.http_client`` is deliberately not asserted on: it is a
    pre-existing transitive import of the CLI, present even for ``show-cohorts``, and importing
    a policy module builds nothing.
    """
    # A bare invocation of a surface with required arguments exits through argparse, so the
    # probe catches SystemExit: what is under test is which modules were loaded, not the code.
    probe = (
        "import sys; from disclosure_drift.cli import main\n"
        f"try:\n    main(['m3', {command!r}])\n"
        "except SystemExit:\n    pass\n"
        "print(sorted(m for m in sys.modules if m.split('.')[0] == 'httpx'))"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == EXIT_OK, result.stderr
    assert result.stdout.strip() == "[]", result.stdout


def test_the_m3_2_surfaces_touch_no_socket_in_process(
    repo_root: Path, evidence_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Behavioural proof: the surfaces run under the suite-wide socket guard without tripping it.

    ``tests/conftest.py`` replaces ``socket.socket``, ``socket.create_connection``, and
    ``socket.getaddrinfo`` with functions that raise. Driving the CLI in-process therefore proves
    these paths open no socket and resolve no hostname.
    """
    from disclosure_drift.cli import main

    configuration = str(repo_root / "configs" / "project.yaml")
    codes = [
        main(["m3", "acquire", "--config", configuration, "--evidence-root", str(evidence_root)]),
        main(
            [
                "m3",
                "show-drift",
                "--config",
                configuration,
                "--evidence-root",
                str(evidence_root),
                "--catalog",
                "catalog.sqlite3",
                "--run",
                "unknown",
            ]
        ),
    ]

    assert codes == [EXIT_USAGE, EXIT_GATE_FAILURE]
    assert "Traceback" not in capsys.readouterr().err


@pytest.mark.parametrize("command", ["census", "ingest-pilot"])
@pytest.mark.parametrize("enabled", [False, True])
def test_m2_2_commands_are_unaffected_by_the_acquire_switch(
    repo_root: Path, tmp_path: Path, command: str, enabled: bool
) -> None:
    """Behavioural proof: flipping the acquire-scoped switch changes no M2.2 command outcome."""
    with_acquire = _config_with_network(tmp_path, repo_root, enabled=enabled, acquire=True)
    without_acquire = _config_with_network(tmp_path, repo_root, enabled=enabled, acquire=False)

    first = _run(["sec", command, "--config", str(with_acquire)], repo_root)
    second = _run(["sec", command, "--config", str(without_acquire)], repo_root)

    assert first.returncode == second.returncode
    assert first.returncode != EXIT_OK
    assert "m3_acquire_enabled" not in first.stderr


def test_the_m2_2_network_gate_reads_only_the_global_switch(repo_root: Path) -> None:
    """Structural proof: the Stage M2.2 command path consults `network.enabled` alone."""
    cli_source = (repo_root / "src" / "disclosure_drift" / "cli.py").read_text(encoding="utf-8")
    start = cli_source.index("def _sec_command(")
    end = cli_source.index("\ndef ", start + 1)
    sec_command_body = cli_source[start:end]

    assert "config.network.enabled" in sec_command_body
    assert "m3_acquire_enabled" not in sec_command_body


# --------------------------------------------------------------------------- #
# Reconciliation, run-scoped drift, and recovery over a real acquired window
#
# These drive the operator commands against evidence a real acquisition produced, built here
# in-process over a scripted transport. Nothing below opens a socket.
# --------------------------------------------------------------------------- #
#: The fixture layout one acquisition writes below an evidence root.
_FIXTURE_CATALOG = "catalogs/m3_2a_operational.sqlite3"
_FIXTURE_DATA_ROOT = "runs/m3_2a/data"

#: A contact identity for the in-process acquisition fixtures. It is never validated by the
#: canonical validator here and never reaches a wire: the transport is always scripted.
_FIXTURE_AGENT = "Disclosure Drift Test Harness (offline-fixture@example.invalid)"


class _ScriptedTransport:
    """Replays scripted responses. Opens no socket."""

    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.closed = False

    def send(self, request: object) -> object:
        from dataclasses import replace  # noqa: PLC0415 - narrow local import

        if not self._responses:
            message = "the scripted transport was exhausted"
            raise AssertionError(message)
        response = self._responses.pop(0)
        if response.final_url == "":  # type: ignore[attr-defined]
            response = replace(response, final_url=request.url)  # type: ignore[arg-type]
        return response

    def close(self) -> None:
        self.closed = True


def _fixture_response(source_id: str, *, corrupt: bool = False) -> object:
    """One scripted 200 shaped to the route's registered expected content kind."""
    from disclosure_drift.sec.source_registry import SOURCES  # noqa: PLC0415
    from disclosure_drift.sec.transport import TransportResponse  # noqa: PLC0415

    expected = SOURCES[source_id].expected_content
    if expected == "zip":
        if corrupt:
            body, content_type = b"not-a-zip-archive", "application/zip"
        else:
            import io  # noqa: PLC0415
            import zipfile  # noqa: PLC0415

            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                info = zipfile.ZipInfo("CIK0000000001.json", date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                archive.writestr(info, b'{"cik":1}')
            body, content_type = buffer.getvalue(), "application/zip"
    elif expected == "html":
        body, content_type = b"<html><body>calendar</body></html>", "text/html"
    elif expected == "text":
        body, content_type = b"CIK|Company Name\n1|SYNTHETIC\n", "text/plain"
    else:
        body, content_type = b'{"ok":1}', "application/json"
    return TransportResponse(
        status=200, headers={"Content-Type": content_type}, final_url="", body=body
    )


def _acquired_window(evidence_root: Path, *, run_id: str, quarantine_bulk: bool = False) -> Path:
    """Run one acquisition over scripted responses, and return the stored plan's relative path.

    Built here rather than imported from the unit suite: a cross-test-module import depends on the
    repository root being importable, which is true for some pytest invocations and not others.
    Everything below uses the public acquisition API and a scripted transport, so it opens no
    socket and reaches no construction site.
    """
    from datetime import date  # noqa: PLC0415

    from disclosure_drift.m3.acquisition import (  # noqa: PLC0415
        LiveOperationAuthorization,
        LiveOperatorGate,
        derive_logical_requests,
        execute_live_acquisition,
        load_carry_in_authority,
        prepare_operational_catalog,
        prepare_storage,
    )
    from disclosure_drift.m3.request_plan import (  # noqa: PLC0415
        LEGACY_UNBOUND_PLAN,
        build_m3_2a_request_plan,
        canonical_plan_bytes,
    )
    from disclosure_drift.sec.http_client import RetrievalPolicy  # noqa: PLC0415
    from disclosure_drift.sec.rate_limit import AggregateRateLimiter  # noqa: PLC0415

    # The **frozen** accepted M3.2A plan. A clean M3.2A run carries a baseline in, a carry-in
    # authority binds the frozen plan and ceiling 801 literally, and the driver re-proves both
    # against the authority object it is handed - so this fixture drives the only configuration a
    # lawful clean run has, rather than a smaller one made to work by injecting an authority no
    # owner could mint.
    plan = build_m3_2a_request_plan(
        coverage_start=date(2009, 1, 1),
        coverage_end=date(2026, 6, 30),
        as_of_date=date(2026, 6, 30),
        include_open_quarter=False,
        calendar_year=2026,
        calendar_evidence_entry_count=0,
        already_satisfied_index_keys=frozenset(),
        requests_per_second=4.0,
        source_registry_version=LEGACY_UNBOUND_PLAN,
    )
    script = [_fixture_response(request.source_id) for request in derive_logical_requests(plan)]
    if quarantine_bulk:
        script[0] = _fixture_response("sec_bulk_submissions", corrupt=True)

    elapsed = [1000.0]

    def _clock() -> float:
        return elapsed[0]

    def _sleep(seconds: float) -> None:
        elapsed[0] += seconds

    execute_live_acquisition(
        plan=plan,
        window="M3.2A",
        approved_ceiling=plan.hard_request_ceiling,
        authorization=LiveOperationAuthorization(
            window="M3.2A",
            plan_sha256=plan.request_plan_sha256,
            approved_ceiling=plan.hard_request_ceiling,
            authorization_reference="OWNER_TEST_FIXTURE_AUTHORIZATION",
        ),
        gate=LiveOperatorGate(
            explicit_live=True,
            network_enabled=True,
            m3_acquire_enabled=True,
            sec_identity_validated=True,
            stage_authority_reference="OWNER_TEST_FIXTURE_STAGE_AUTHORITY",
        ),
        catalog=prepare_operational_catalog(
            evidence_root=evidence_root, relative_path=_FIXTURE_CATALOG
        ),
        storage=prepare_storage(evidence_root=evidence_root, data_root_relative=_FIXTURE_DATA_ROOT),
        user_agent=_FIXTURE_AGENT,
        requests_per_second=4.0,
        burst=1,
        policy=RetrievalPolicy(),
        transport_factory=lambda: _ScriptedTransport(script),  # type: ignore[arg-type,return-value]
        run_id_factory=lambda: run_id,
        clock=lambda: "2026-08-04T00:00:00Z",
        sleeper=_sleep,
        rate_limiter=AggregateRateLimiter(4.0, burst=1, clock=_clock, sleeper=_sleep),
        # M3-L16: an M3.2A run states the baseline it begins from. The authority is minted as
        # canonical bytes and admitted through the real artifact boundary, exactly as an operator's
        # would be, because the driver re-proves the fixed Decision 055 bindings and the canonical
        # external identity from the object it is handed - a directly constructed one buys nothing.
        carry_in=load_carry_in_authority(
            _carry_in_authority_bytes(run_id=run_id, evidence_sha256="f" * 64)
        ),
    )

    plan_path = evidence_root / "plans" / "acquired.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_bytes(canonical_plan_bytes(plan))
    assert (evidence_root / _FIXTURE_CATALOG).is_file()
    return Path("plans/acquired.json")


def _catalog_arguments() -> list[str]:
    """The data-root and catalog arguments matching the acquisition fixture layout.

    ``--catalog`` is named relative to ``--data-root``, so the fixture's root-relative catalog
    path is expressed by climbing back out of the data root exactly as an operator would.
    """
    climb = Path(*[".."] * len(Path(_FIXTURE_DATA_ROOT).parts))
    return ["--data-root", _FIXTURE_DATA_ROOT, "--catalog", str(climb / _FIXTURE_CATALOG)]


def test_reconcile_requests_exits_zero_on_a_complete_window_and_writes_its_report(
    repo_root: Path, evidence_root: Path
) -> None:
    plan_relative = _acquired_window(evidence_root, run_id="run-reconcile")

    result = _run(
        [
            "m3",
            "reconcile-requests",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            str(plan_relative),
            *_catalog_arguments(),
            "--report-out",
            "reports/reconciliation.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_OK, result.stderr
    report = evidence_root / "reports" / "reconciliation.json"
    assert report.is_file()
    document = json.loads(report.read_text(encoding="utf-8"))
    assert document["exit_is_clean"] is True
    assert document["absence_enumeration"] == []
    assert document["blocking_drift"] == []


def test_the_reconciliation_report_is_byte_deterministic(
    repo_root: Path, evidence_root: Path
) -> None:
    """Identical durable state produces identical report bytes, so two runs are comparable."""
    plan_relative = _acquired_window(evidence_root, run_id="run-deterministic")
    arguments = [
        "m3",
        "reconcile-requests",
        "--evidence-root",
        str(evidence_root),
        "--plan",
        str(plan_relative),
        *_catalog_arguments(),
    ]

    first = _run([*arguments, "--report-out", "reports/first.json"], repo_root)
    second = _run([*arguments, "--report-out", "reports/second.json"], repo_root)

    assert first.returncode == second.returncode == EXIT_OK, first.stderr + second.stderr
    assert (evidence_root / "reports" / "first.json").read_bytes() == (
        evidence_root / "reports" / "second.json"
    ).read_bytes()


def test_reconcile_requests_exits_four_on_an_absence_and_still_writes_the_report(
    repo_root: Path, evidence_root: Path
) -> None:
    """The evidence explaining a 4 is as load-bearing as the evidence explaining a 0."""
    plan_relative = _acquired_window(evidence_root, run_id="run-absent", quarantine_bulk=True)

    result = _run(
        [
            "m3",
            "reconcile-requests",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            str(plan_relative),
            *_catalog_arguments(),
            "--report-out",
            "reports/absent.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE, result.stdout
    document = json.loads((evidence_root / "reports" / "absent.json").read_text(encoding="utf-8"))
    assert document["exit_is_clean"] is False
    assert document["absence_enumeration"], "a quarantined required object is an absence"


def test_show_drift_exits_zero_for_a_clean_run_and_four_for_a_drifting_one(
    repo_root: Path, evidence_root: Path
) -> None:
    """Run scoping is real, and blocking drift is the exit-4 condition."""
    _acquired_window(evidence_root, run_id="run-clean")
    _acquired_window(evidence_root, run_id="run-drifting", quarantine_bulk=True)
    clean = _run(
        [
            "m3",
            "show-drift",
            "--evidence-root",
            str(evidence_root),
            "--catalog",
            _FIXTURE_CATALOG,
            "--run",
            "run-clean",
        ],
        repo_root,
    )
    drifting = _run(
        [
            "m3",
            "show-drift",
            "--evidence-root",
            str(evidence_root),
            "--catalog",
            _FIXTURE_CATALOG,
            "--run",
            "run-drifting",
        ],
        repo_root,
    )

    assert clean.returncode == EXIT_OK, clean.stderr
    assert "blocking drift events" in clean.stdout
    assert drifting.returncode == EXIT_GATE_FAILURE, drifting.stdout
    assert "BLOCKING" in drifting.stdout


def test_recover_refuses_a_run_registered_as_a_stage_m2_2_census(
    repo_root: Path, evidence_root: Path
) -> None:
    """A run identity that exists but is not an M3.2 acquisition run fails closed."""
    from disclosure_drift.m3.acquisition import ACQUISITION_JOB_KIND  # noqa: PLC0415
    from disclosure_drift.storage.catalog import CatalogWriter  # noqa: PLC0415

    plan_relative = _acquired_window(evidence_root, run_id="run-m3-2")
    catalog = evidence_root / _FIXTURE_CATALOG
    with CatalogWriter(catalog, catalog.parent) as writer, writer.batch():
        writer.insert(
            "ops_ingestion_jobs",
            {
                "job_id": "run-census",
                "job_kind": "sec_census",
                "job_state": "running",
                "stage": "M2.2",
                "started_at_utc": "2026-08-04T00:00:00Z",
                "detail": "a Stage M2.2 census run",
            },
        )
    assert ACQUISITION_JOB_KIND != "sec_census"

    result = _run(
        [
            "m3",
            "recover",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            str(plan_relative),
            "--receipt-chain-head",
            "receipts/head.json",
            *_catalog_arguments(),
            "--run",
            "run-census",
            "--action",
            "rebuild-projection",
            "--event",
            "census_source_observations.jsonl",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "job kind" in result.stderr


# --------------------------------------------------------------------------- #
# The reconciliation exit rule, one conjunct at a time (Decision 045 §4.4)
# --------------------------------------------------------------------------- #
def _reconciliation(**overrides: object) -> object:
    """A clean reconciliation, with exactly one conjunct spoiled per test.

    Driving the rule through the CLI can only ever exercise the conjuncts a fixture happens to
    produce together — a quarantined required object raises an absence *and* blocking drift at
    once, so each control masks the other and neither is individually load-bearing. Constructing
    the reconciliation directly is what makes one conjunct testable at a time.
    """
    from disclosure_drift.m3.acquisition import (  # noqa: PLC0415 - narrow local import
        DriftListingEntry,
        ReconciliationItem,
        RequestReconciliation,
        StoreFinding,
    )

    fields: dict[str, object] = {
        "window": "M3.2A",
        "plan_sha256": "0" * 64,
        "items": (),
        "out_of_plan": (),
        "store_findings": (),
        "drift": (),
        "blocked_recovery_states": 0,
    }
    builders = {
        "absence": lambda: {
            "items": (
                ReconciliationItem(
                    position=0,
                    source_id="sec_company_tickers",
                    identity_label="sec_company_tickers",
                    request_identity="identity",
                    state="absent",
                    observation_id=None,
                    verified=False,
                    excluded_from_continuation=False,
                    attempts=1,
                    reason_codes=("SOURCE_REQUIRED_OBJECT_UNAVAILABLE",),
                    conditions=(),
                ),
            )
        },
        "blocking_drift": lambda: {
            "drift": (
                DriftListingEntry(
                    observation_id="observation-0001",
                    source_id="sec_bulk_submissions",
                    request_identity="identity",
                    reason_codes=("RAW_ARCHIVE_INVALID",),
                    blocking=True,
                ),
            )
        },
        "nonblocking_drift": lambda: {
            "drift": (
                DriftListingEntry(
                    observation_id="observation-0002",
                    source_id="sec_company_tickers",
                    request_identity="identity",
                    reason_codes=("PARSER_SCHEMA_DRIFT_OBSERVED",),
                    blocking=False,
                ),
            )
        },
        "out_of_plan": lambda: {"out_of_plan": (("sec_sic_code_list", "identity"),)},
        "store_finding": lambda: {
            "store_findings": (
                StoreFinding(
                    kind="orphan_object",
                    relative_path="raw/bulk/orphan.json",
                    observation_id=None,
                ),
            )
        },
        "blocked_recovery_state": lambda: {"blocked_recovery_states": 1},
    }
    for name, enabled in overrides.items():
        if enabled:
            fields.update(builders[name]())
    return RequestReconciliation(**fields)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "conjunct",
    [
        "absence",
        "blocking_drift",
        "out_of_plan",
        "store_finding",
        "blocked_recovery_state",
    ],
)
def test_each_reconciliation_conjunct_alone_forces_the_governed_exit(conjunct: str) -> None:
    """Every defect refuses exit 0 on its own, so none is masked by the others."""
    from disclosure_drift.cli import _reconciliation_is_clean  # noqa: PLC0415 - narrow import

    assert _reconciliation_is_clean(_reconciliation(**{conjunct: True})) is False  # type: ignore[arg-type]


def test_positive_control_a_reconciliation_with_no_defect_is_clean() -> None:
    """Without this, every case above would pass against a rule that returns False always."""
    from disclosure_drift.cli import _reconciliation_is_clean  # noqa: PLC0415 - narrow import

    assert _reconciliation_is_clean(_reconciliation()) is True  # type: ignore[arg-type]


def test_nonblocking_drift_alone_does_not_force_the_governed_exit() -> None:
    """Decision 045 §4.4: remaining divergence that is nonblocking still permits exit 0."""
    from disclosure_drift.cli import _reconciliation_is_clean  # noqa: PLC0415 - narrow import

    assert _reconciliation_is_clean(_reconciliation(nonblocking_drift=True)) is True  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Genuine interruption -> receipt -> accepted recovery -> real CLI resume
#
# Decision 045 correction, MAJOR-1. These drive the *real* operator surfaces end to end:
# `m3 acquire --live` is interrupted at a real durable boundary, `m3 recovery-state` and
# `m3 recover` are the accepted recovery path, and the resume is the real
# `m3 acquire --live --resume-from`. Nothing here hand-builds a continuation proposal.
#
# Two seams are substituted, and only two: the HTTP transport (so no socket exists) and the SEC
# contact identity (so no real address is ever fabricated to pass a live gate). Everything between
# them is production code.
# --------------------------------------------------------------------------- #
_LIVE_CATALOG = "m3_2a_operational.sqlite3"
_LIVE_DATA_ROOT = "runs/m3_2a/data"
_PROJECTION_TARGET = "census_source_observations.jsonl"


class _InterruptScript:
    """The scripted response queue one in-process live invocation replays. Opens no socket."""

    def __init__(self) -> None:
        self.responses: list[object] = []
        self.constructions = 0
        self.sent = 0


def _fixture_body(source_id: str, marker: bytes) -> object:
    """One scripted ``200`` shaped to the route's registered expected content kind.

    ``marker`` differentiates otherwise identical bodies, so two instances of the same route do
    not collapse into a byte-identical duplicate and blur what a resume actually re-requested.
    """
    from disclosure_drift.sec.source_registry import SOURCES  # noqa: PLC0415
    from disclosure_drift.sec.transport import TransportResponse  # noqa: PLC0415

    expected = SOURCES[source_id].expected_content
    if expected == "zip":
        import io  # noqa: PLC0415
        import zipfile  # noqa: PLC0415

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo(
                f"CIK000000000{marker.decode()}.json", date_time=(1980, 1, 1, 0, 0, 0)
            )
            info.create_system = 3
            archive.writestr(info, b'{"cik":' + marker + b"}")
        body, content_type = buffer.getvalue(), "application/zip"
    elif expected == "html":
        body, content_type = b"<html><body>calendar " + marker + b"</body></html>", "text/html"
    elif expected == "text":
        body, content_type = b"CIK|Company Name\n" + marker + b"|SYNTHETIC\n", "text/plain"
    else:
        body, content_type = b'{"ok":' + marker + b"}", "application/json"
    return TransportResponse(
        status=200, headers={"Content-Type": content_type}, final_url="", body=body
    )


def _install_live_seams(monkeypatch: pytest.MonkeyPatch, script: _InterruptScript) -> None:
    """Substitute exactly two things: the transport implementation and the contact identity.

    The transport is replaced at ``sec.httpx_transport.HttpxTransport``, which is what the one
    auditable construction site imports at call time — so the production factory, the recording
    wrapper, and the whole live path really run, and only the socket-owning object is fake.

    The identity is stubbed at the canonical validator rather than fabricated: this suite never
    invents a contact value that would pass a live gate (Decision 045 §11), and the placeholder it
    returns stays in process memory. The receipt's prohibited-content scan bars it from every
    artifact, which the assertions below rely on rather than assume.
    """
    from dataclasses import replace as _replace  # noqa: PLC0415

    import disclosure_drift.sec.httpx_transport as httpx_transport  # noqa: PLC0415
    from disclosure_drift.config import ProjectConfig  # noqa: PLC0415

    class _Scripted:
        def __init__(self, *args: object, **kwargs: object) -> None:
            script.constructions += 1

        def send(self, request: object) -> object:
            if not script.responses:
                message = "the scripted transport was exhausted"
                raise AssertionError(message)
            script.sent += 1
            response = script.responses.pop(0)
            if response.final_url == "":  # type: ignore[attr-defined]
                response = _replace(response, final_url=request.url)  # type: ignore[arg-type]
            return response

        def close(self) -> None:
            return None

    monkeypatch.setattr(httpx_transport, "HttpxTransport", _Scripted)
    monkeypatch.setattr(
        ProjectConfig,
        "require_sec_user_agent",
        lambda self, env=None: FIXTURE_PLACEHOLDER_IDENTITY,
    )


def _live_plan(evidence_root: Path) -> object:
    """Derive the **frozen** accepted M3.2A plan and store it below the evidence root.

    These suites drive the only configuration a clean M3.2A run may lawfully have. Decision 055
    binds a carry-in authority to the frozen plan hash and to cumulative ceiling ``801`` literally,
    and M3-L16 requires every clean M3.2A invocation to carry a baseline in — so an acquisition
    under any other plan is not a thing the corrected system can perform, and testing one would
    prove nothing about the path an operator will actually take.
    """
    from datetime import date  # noqa: PLC0415

    from disclosure_drift.m3.request_plan import (  # noqa: PLC0415
        LEGACY_UNBOUND_PLAN,
        build_m3_2a_request_plan,
        canonical_plan_bytes,
    )

    plan = build_m3_2a_request_plan(
        coverage_start=date(2009, 1, 1),
        coverage_end=date(2026, 6, 30),
        as_of_date=date(2026, 6, 30),
        include_open_quarter=False,
        calendar_year=2026,
        calendar_evidence_entry_count=0,
        already_satisfied_index_keys=frozenset(),
        requests_per_second=4.0,
        source_registry_version=LEGACY_UNBOUND_PLAN,
    )
    destination = evidence_root / "plans" / "approved.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_plan_bytes(plan))
    return plan


def _carry_in_authority_bytes(*, run_id: str, evidence_sha256: str = "f" * 64) -> bytes:
    """The canonical bytes of one lawful carry-in authority artifact.

    Every binding is the accepted Decision 055 value, because both the CLI's artifact boundary and
    every production execution and consumption boundary compare them literally. Only the
    orphan-adoption references are synthetic — they name a later Path-B act that has not happened —
    and ``Decision 999`` is used as clearly synthetic data.

    Sole builder for both the on-disk artifacts the CLI reads and the in-process authority the
    acquisition fixture hands the driver, so no fixture can drift into minting something the
    artifact boundary would have refused.
    """
    from disclosure_drift.m3.acquisition import (  # noqa: PLC0415
        CARRY_IN_ACQUISITION_WINDOW,
        CARRY_IN_APPROVED_REQUEST_CEILING,
        CARRY_IN_AUTHORITY_SCHEMA_VERSION,
        CARRY_IN_AUTHORIZING_DECISION_REFERENCE,
        CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT,
        CARRY_IN_HISTORICAL_ROUTE_ALLOCATION,
        CARRY_IN_REQUEST_PLAN_SHA256,
    )
    from disclosure_drift.m3.receipt import canonical_bytes  # noqa: PLC0415

    return canonical_bytes(
        {
            "acquisition_window": CARRY_IN_ACQUISITION_WINDOW,
            "approved_request_ceiling": CARRY_IN_APPROVED_REQUEST_CEILING,
            "authorized_census_run_id": run_id,
            "authorizing_decision_reference": CARRY_IN_AUTHORIZING_DECISION_REFERENCE,
            "historical_consumed_request_count": CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT,
            "historical_route_allocation": dict(CARRY_IN_HISTORICAL_ROUTE_ALLOCATION),
            "orphan_adoption_decision_reference": "Decision 999",
            "orphan_adoption_evidence_sha256": evidence_sha256,
            "request_plan_sha256": CARRY_IN_REQUEST_PLAN_SHA256,
            "schema_version": CARRY_IN_AUTHORITY_SCHEMA_VERSION,
        }
    )


def _write_carry_in(evidence_root: Path, *, name: str, run_id: str) -> str:
    """Write one canonical carry-in authority artifact and return its safe relative path."""
    relative = f"authorities/{name}.json"
    destination = evidence_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(_carry_in_authority_bytes(run_id=run_id))
    return relative


def _acquire_argv(
    evidence_root: Path,
    config: Path,
    plan: object,
    *,
    receipt_out: str,
    resume_from: str | None = None,
    window: str = "M3.2A",
    ceiling: int | None = None,
    catalog: str = _LIVE_CATALOG,
    carry_in: str | None = "auto",
) -> list[str]:
    """One ``m3 acquire --live`` command line.

    A clean ``M3.2A`` invocation is given a carry-in authority by default, because M3-L16 makes one
    mandatory: without a baseline source the command refuses before it creates anything. Each
    authority is minted per ``receipt_out``, so a test that runs two clean acquisitions does not
    trip the single-use replay refusal instead of exercising what it means to. Pass
    ``carry_in=None`` to drive the refusal itself.
    """
    argv = [
        "m3",
        "acquire",
        "--config",
        str(config),
        "--evidence-root",
        str(evidence_root),
        "--live",
        "--plan",
        "plans/approved.json",
        "--window",
        window,
        "--ceiling",
        str(plan.hard_request_ceiling if ceiling is None else ceiling),  # type: ignore[attr-defined]
        "--data-root",
        _LIVE_DATA_ROOT,
        "--catalog",
        catalog,
        "--receipt-out",
        receipt_out,
    ]
    if resume_from is not None:
        argv += ["--resume-from", resume_from]
    elif carry_in == "auto" and window == "M3.2A":
        # Named from the receipt's stem alone, never its directory: `_receipt_files` matches the
        # whole relative path for the word "receipt", and an authority filed under a name carrying
        # it would register as a receipt and quietly weaken every no-receipt assertion.
        stem = Path(receipt_out).stem
        carry_in = _write_carry_in(evidence_root, name=stem, run_id=f"m3-2-acquisition-{stem}")
    if resume_from is None and carry_in not in {None, "auto"}:
        argv += ["--carry-in-authority", str(carry_in)]
    return argv


def _recovery_state_argv(evidence_root: Path) -> list[str]:
    return [
        "m3",
        "recovery-state",
        "--evidence-root",
        str(evidence_root),
        "--plan",
        "plans/approved.json",
        "--receipt-chain-head",
        "receipts/interrupted.json",
        "--catalog",
        _LIVE_CATALOG,
        "--data-root",
        _LIVE_DATA_ROOT,
    ]


def _recover_argv(
    evidence_root: Path, config: Path, *, run_id: str, action: str, event: str
) -> list[str]:
    return [
        "m3",
        "recover",
        "--config",
        str(config),
        "--evidence-root",
        str(evidence_root),
        "--plan",
        "plans/approved.json",
        "--receipt-chain-head",
        "receipts/interrupted.json",
        "--catalog",
        _LIVE_CATALOG,
        "--data-root",
        _LIVE_DATA_ROOT,
        "--run",
        run_id,
        "--action",
        action,
        "--event",
        event,
    ]


def _live_catalog_rows(evidence_root: Path, statement: str) -> list:
    import sqlite3 as _sqlite3  # noqa: PLC0415

    database = evidence_root / _LIVE_DATA_ROOT / _LIVE_CATALOG
    with _sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        connection.row_factory = _sqlite3.Row
        return connection.execute(statement).fetchall()


def _live_orphans(evidence_root: Path) -> list[str]:
    """Raw objects on disk that no committed row references."""
    data_root = evidence_root / _LIVE_DATA_ROOT
    recorded = {
        row["relative_storage_path"]
        for row in _live_catalog_rows(
            evidence_root, "SELECT relative_storage_path FROM census_source_observations"
        )
    }
    raw_root = data_root / "raw"
    return [
        str(path.relative_to(data_root))
        for path in sorted(raw_root.rglob("*"))
        if path.is_file()
        and not path.name.endswith((".lineage.json", ".part", ".reason"))
        and str(path.relative_to(data_root)) not in recorded
    ]


def _interrupt_method(
    monkeypatch: pytest.MonkeyPatch, owner: type, name: str, *, call: int, after: bool = False
) -> None:
    """Raise ``KeyboardInterrupt`` on the ``call``-th invocation of ``owner.name``."""
    original = getattr(owner, name)
    seen = {"count": 0}

    def _wrapper(self: object, *args: object, **kwargs: object) -> object:
        seen["count"] += 1
        fires = seen["count"] == call
        if fires and not after:
            raise KeyboardInterrupt
        value = original(self, *args, **kwargs)
        if fires and after:
            raise KeyboardInterrupt
        return value

    monkeypatch.setattr(owner, name, _wrapper)


#: The three governed interruption points, each with the durable state it must leave behind and
#: the accepted recovery actions the scenario genuinely requires before a resume may be SAFE.
_INTERRUPTION_SCENARIOS = {
    "I1_before_raw_store_write": {
        "owner": "snapshot_store",
        "after": False,
        "state": "before_raw_store_write",
        "committed": 1,
        "orphans": 0,
        "adopt_orphan": False,
        "remaining": 74,
    },
    "I2_after_raw_store_write_before_catalog_commit": {
        "owner": "recorder",
        "after": False,
        "state": "after_raw_store_write_before_catalog_commit",
        "committed": 1,
        "orphans": 1,
        "adopt_orphan": True,
        "remaining": 73,
    },
    "I3_after_catalog_commit": {
        "owner": "recorder",
        "after": True,
        "state": "after_catalog_commit",
        "committed": 2,
        "orphans": 0,
        "adopt_orphan": False,
        "remaining": 73,
    },
}


@pytest.mark.parametrize("scenario", sorted(_INTERRUPTION_SCENARIOS))
def test_a_real_interruption_recovers_to_safe_and_resumes_through_the_real_cli(
    repo_root: Path,
    evidence_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
) -> None:
    """The whole MAJOR-1 cycle, through the operator surfaces, for each interruption point.

    A lawful ``m3 acquire --live`` is interrupted at a real durable boundary; the terminating
    receipt records ``interrupted`` with the exact state; the accepted read-only inspection refuses
    to call it SAFE until the bounded recovery actions the scenario genuinely requires have run;
    and the real ``m3 acquire --live --resume-from`` then carries the consumed count forward,
    registers a new run identity, re-requests nothing already satisfied, and finishes the window.
    """
    from disclosure_drift.cli import main  # noqa: PLC0415
    from disclosure_drift.m3.acquisition import derive_logical_requests  # noqa: PLC0415
    from disclosure_drift.sec.observation_catalog import ObservationRecorder  # noqa: PLC0415
    from disclosure_drift.sec.snapshots import SnapshotStore  # noqa: PLC0415

    expected = _INTERRUPTION_SCENARIOS[scenario]
    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    script = _InterruptScript()
    _install_live_seams(monkeypatch, script)
    plan = _live_plan(evidence_root)
    requests = derive_logical_requests(plan)  # type: ignore[arg-type]
    bodies = [
        _fixture_body(item.source_id, str(index).encode()) for index, item in enumerate(requests)
    ]
    script.responses = list(bodies)

    owner = SnapshotStore if expected["owner"] == "snapshot_store" else ObservationRecorder
    _interrupt_method(monkeypatch, owner, "record", call=2, after=bool(expected["after"]))

    # ---- the interrupted invocation ---------------------------------------------------- #
    assert main(
        _acquire_argv(evidence_root, config, plan, receipt_out="receipts/interrupted.json")
    ) == (EXIT_GATE_FAILURE), "a recorded interruption is a governed non-success, never exit 0"
    monkeypatch.undo()
    _install_live_seams(monkeypatch, script)

    interrupted = json.loads(
        (evidence_root / "receipts" / "interrupted.json").read_text(encoding="utf-8")
    )
    assert interrupted["completion_status"] == "interrupted"
    assert interrupted["interruption_state"] == expected["state"]
    assert interrupted["reason_code"] == "SEC_ACQUISITION_INTERRUPTED"
    assert interrupted["invocation_mode"] == "live"
    assert FIXTURE_PLACEHOLDER_IDENTITY not in json.dumps(interrupted)

    # ---- the durable state the scenario must have left --------------------------------- #
    committed = _live_catalog_rows(
        evidence_root, "SELECT observation_id FROM census_source_observations"
    )
    assert len(committed) == expected["committed"]
    assert len(_live_orphans(evidence_root)) == expected["orphans"]
    jobs = _live_catalog_rows(evidence_root, "SELECT job_id, job_state FROM ops_ingestion_jobs")
    assert [row["job_state"] for row in jobs] == ["stopped"]
    first_run = jobs[0]["job_id"]

    # ---- the accepted recovery path ---------------------------------------------------- #
    # Recovery runs with the network window closed (Decision 064 §5, condition 10). That is the
    # operator discipline the rule encodes rather than an artefact of the harness: reconstructing
    # the derived projection while an acquisition path is open would produce a snapshot that is
    # stale the moment a further row commits. The projection rebuild refuses under the live
    # configuration and proceeds under the offline one, and the resume below reopens the window
    # under its own authority.
    offline = _config_with_network(tmp_path, repo_root, enabled=False, acquire=False)
    assert main(_recovery_state_argv(evidence_root)) == EXIT_GATE_FAILURE, (
        "an interrupted run is not SAFE until its bounded recovery actions have run"
    )
    assert (
        main(
            _recover_argv(
                evidence_root,
                config,
                run_id=first_run,
                action="rebuild-projection",
                event=_PROJECTION_TARGET,
            )
        )
        == EXIT_GATE_FAILURE
    ), "the projection rebuild refuses while a tracked acquisition switch is open"

    # Store uncertainty is adjudicated before the derived projection is reconstructed from the
    # catalog: an orphan means the authoritative observation set is still about to change, and the
    # rebuild refuses over one (Decision 064 §5, condition 6). The two guards compose in exactly
    # one order — adopt, then rebuild — and neither state is unreachable from the other.
    if expected["adopt_orphan"]:
        orphan = _live_orphans(evidence_root)[0]
        assert (
            main(
                _recover_argv(
                    evidence_root,
                    offline,
                    run_id=first_run,
                    action="rebuild-projection",
                    event=_PROJECTION_TARGET,
                )
            )
            == EXIT_GATE_FAILURE
        ), "the projection rebuild refuses while an orphan remains unadjudicated"
        assert (
            main(
                _recover_argv(
                    evidence_root, offline, run_id=first_run, action="adopt-orphan", event=orphan
                )
            )
            == EXIT_OK
        )
        assert _live_orphans(evidence_root) == [], "the orphan is reconciled, never deleted"
    assert (
        main(
            _recover_argv(
                evidence_root,
                offline,
                run_id=first_run,
                action="rebuild-projection",
                event=_PROJECTION_TARGET,
            )
        )
        == EXIT_OK
    )

    assert main(_recovery_state_argv(evidence_root)) == EXIT_OK, "the inspection now reports SAFE"

    # ---- the real resume ---------------------------------------------------------------- #
    satisfied_before = {
        row["relative_storage_path"]
        for row in _live_catalog_rows(
            evidence_root, "SELECT relative_storage_path FROM census_source_observations"
        )
    }
    script.responses = bodies[len(satisfied_before) :]
    sent_before = script.sent
    assert (
        main(
            _acquire_argv(
                evidence_root,
                config,
                plan,
                receipt_out="receipts/resumed.json",
                resume_from="receipts/interrupted.json",
            )
        )
        == EXIT_OK
    )

    resumed = json.loads((evidence_root / "receipts" / "resumed.json").read_text(encoding="utf-8"))
    assert resumed["completion_status"] == "complete"
    assert resumed["recovery_predecessor_receipt_id"] == interrupted["receipt_id"]
    # The predecessor's consumption is carried forward exactly, never reset to zero — and the
    # chain's root carry-in is added exactly once on the way through (Decision 055 §7.5). The
    # interrupted run is a clean carry-in root, so what the resume inherits is that root's own
    # wire attempts *plus* the single baseline it carried in: never one alone, never both twice.
    assert interrupted["consumed_request_count_carried_forward"] == 1
    assert interrupted["carry_in_authority_sha256"], "a clean carry-in root names its authority"
    assert resumed["consumed_request_count_carried_forward"] == (
        interrupted["actual_physical_attempt_count"]
        + interrupted["consumed_request_count_carried_forward"]
    )
    # A resume is not a carry-in root: it names a predecessor, so it carries no authority hash.
    assert "carry_in_authority_sha256" not in resumed
    # Only the remainder was placed: already-satisfied work is never re-requested.
    assert resumed["actual_logical_request_count"] == expected["remaining"]
    assert script.sent - sent_before == expected["remaining"]
    assert script.responses == [], "the resume placed exactly the scripted remainder"
    total = (
        resumed["consumed_request_count_carried_forward"] + resumed["actual_physical_attempt_count"]
    )
    assert total <= resumed["approved_request_ceiling"]

    # A run identifies one invocation: the resume registered its own, and did not adopt the first.
    runs = [
        row["job_id"]
        for row in _live_catalog_rows(
            evidence_root, "SELECT job_id FROM ops_ingestion_jobs ORDER BY rowid"
        )
    ]
    assert len(runs) == 2
    assert runs[0] == first_run
    assert runs[1] != first_run
    assert FIXTURE_PLACEHOLDER_IDENTITY not in json.dumps(resumed)


def test_an_ambiguous_interruption_writes_no_receipt_and_advertises_no_resume(
    repo_root: Path,
    evidence_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Interrupted *inside* the snapshot store, after promotion and before it returned.

    The invocation cannot tell that apart from a promotion that never happened, so it refuses to
    classify. No receipt is written at all — a receipt with no established interruption state
    would fail the accepted inspection's condition 8.2 anyway, and writing one would advertise a
    resume that cannot safely start. The evidence is preserved, not cleaned up.
    """
    from disclosure_drift.cli import main  # noqa: PLC0415
    from disclosure_drift.m3.acquisition import derive_logical_requests  # noqa: PLC0415
    from disclosure_drift.sec.snapshots import SnapshotStore  # noqa: PLC0415

    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    script = _InterruptScript()
    _install_live_seams(monkeypatch, script)
    plan = _live_plan(evidence_root)
    script.responses = [
        _fixture_body(item.source_id, str(index).encode())
        for index, item in enumerate(derive_logical_requests(plan))  # type: ignore[arg-type]
    ]
    _interrupt_method(monkeypatch, SnapshotStore, "record", call=2, after=True)

    assert main(_acquire_argv(evidence_root, config, plan, receipt_out="receipts/x.json")) == (
        EXIT_GATE_FAILURE
    )
    monkeypatch.undo()

    assert _receipt_files(evidence_root) == [], "no receipt is written for an unclassifiable stop"
    assert len(_live_orphans(evidence_root)) == 1, "the promoted object is preserved untouched"
    jobs = _live_catalog_rows(evidence_root, "SELECT job_state FROM ops_ingestion_jobs")
    assert [row["job_state"] for row in jobs] == ["stopped"]


def test_a_governed_failure_stays_failed_and_carries_no_interruption_state(
    repo_root: Path,
    evidence_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`interrupted` is not a catch-all: an ordinary terminal failure keeps its own status."""
    from disclosure_drift.cli import main  # noqa: PLC0415
    from disclosure_drift.m3.acquisition import derive_logical_requests  # noqa: PLC0415
    from disclosure_drift.sec.transport import TransportResponse  # noqa: PLC0415

    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    script = _InterruptScript()
    _install_live_seams(monkeypatch, script)
    plan = _live_plan(evidence_root)
    requests = derive_logical_requests(plan)  # type: ignore[arg-type]
    refusal = TransportResponse(status=404, headers={}, final_url="", body=b"")
    script.responses = [refusal] + [
        _fixture_body(item.source_id, str(index).encode())
        for index, item in enumerate(requests[1:], start=1)
    ]

    assert main(_acquire_argv(evidence_root, config, plan, receipt_out="receipts/failed.json")) == (
        EXIT_GATE_FAILURE
    )

    document = json.loads((evidence_root / "receipts" / "failed.json").read_text(encoding="utf-8"))
    assert document["completion_status"] == "failed"
    assert "interruption_state" not in document


# --------------------------------------------------------------------------- #
# Pre-catalog refusal ordering (Decision 045 correction, MINOR-2)
#
# A refusal decidable without durable state must leave no durable state. Each case below runs
# against an evidence root whose operational catalog does not exist, and proves it still does not
# exist afterwards — together with the exit class, no transport construction, and no receipt.
# --------------------------------------------------------------------------- #
def _live_catalog_path(evidence_root: Path) -> Path:
    return evidence_root / _LIVE_DATA_ROOT / _LIVE_CATALOG


def _refusal_case(
    name: str, evidence_root: Path, config: Path, plan: object
) -> tuple[list[str], int]:
    """One refusal invocation and the exit class it owes."""
    if name == "wrong_window":
        return (
            _acquire_argv(evidence_root, config, plan, receipt_out="r.json", window="M3.2B"),
            EXIT_GATE_FAILURE,
        )
    if name == "unaccepted_window":
        return (
            _acquire_argv(evidence_root, config, plan, receipt_out="r.json", window="M9.9Z"),
            EXIT_GATE_FAILURE,
        )
    if name == "ceiling_below":
        return (
            _acquire_argv(
                evidence_root,
                config,
                plan,
                receipt_out="r.json",
                ceiling=plan.hard_request_ceiling - 1,  # type: ignore[attr-defined]
            ),
            EXIT_GATE_FAILURE,
        )
    if name == "ceiling_above":
        return (
            _acquire_argv(
                evidence_root,
                config,
                plan,
                receipt_out="r.json",
                ceiling=plan.hard_request_ceiling + 1,  # type: ignore[attr-defined]
            ),
            EXIT_GATE_FAILURE,
        )
    if name == "plan_hash_mismatch":
        # The stored plan is bound by its own content hash, so an edited byte is a different
        # plan. The operator still names the ceiling the *original* plan derived, which is what
        # makes this a hash refusal rather than a ceiling one.
        stored = evidence_root / "plans" / "approved.json"
        document = json.loads(stored.read_text(encoding="utf-8"))
        document["expected_cache_hits"] = int(document["expected_cache_hits"]) + 1
        stored.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
        return (
            _acquire_argv(evidence_root, config, plan, receipt_out="r.json"),
            EXIT_GATE_FAILURE,
        )
    message = f"unknown refusal case {name!r}"
    raise AssertionError(message)


@pytest.mark.parametrize(
    "case",
    ["wrong_window", "unaccepted_window", "ceiling_below", "ceiling_above", "plan_hash_mismatch"],
)
def test_a_binding_refusal_creates_no_operational_catalog(
    repo_root: Path,
    evidence_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    """Every plan, window, and ceiling binding is proved before any durable state is created."""
    from disclosure_drift.cli import main  # noqa: PLC0415

    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    script = _InterruptScript()
    _install_live_seams(monkeypatch, script)
    plan = _live_plan(evidence_root)
    argv, expected_exit = _refusal_case(case, evidence_root, config, plan)
    assert not _live_catalog_path(evidence_root).exists()

    assert main(argv) == expected_exit
    assert not _live_catalog_path(evidence_root).exists(), "a refusal left an operational catalog"
    assert not (evidence_root / _LIVE_DATA_ROOT).exists(), "a refusal created a data root"
    assert script.constructions == 0, "a refusal reached the transport-construction site"
    assert _receipt_files(evidence_root) == []


def test_a_disabled_live_gate_creates_no_operational_catalog(
    repo_root: Path, evidence_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tracked switches refuse before anything durable exists."""
    from disclosure_drift.cli import main  # noqa: PLC0415

    config = _config_with_network(tmp_path, repo_root, enabled=False, acquire=False)
    script = _InterruptScript()
    _install_live_seams(monkeypatch, script)
    plan = _live_plan(evidence_root)

    assert main(_acquire_argv(evidence_root, config, plan, receipt_out="r.json")) == (
        EXIT_STAGE_NOT_ENABLED
    )
    assert not _live_catalog_path(evidence_root).exists()
    assert script.constructions == 0
    assert _receipt_files(evidence_root) == []


def test_an_unvalidated_identity_creates_no_operational_catalog(
    repo_root: Path, evidence_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The canonical validator runs — unstubbed — before anything durable exists."""
    from disclosure_drift.cli import main  # noqa: PLC0415

    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    monkeypatch.setenv("DISCLOSURE_DRIFT_SEC_USER_AGENT", FIXTURE_PLACEHOLDER_IDENTITY)
    plan = _live_plan(evidence_root)

    assert main(_acquire_argv(evidence_root, config, plan, receipt_out="r.json")) == (
        EXIT_STAGE_NOT_ENABLED
    )
    assert not _live_catalog_path(evidence_root).exists()
    assert _receipt_files(evidence_root) == []


def test_a_missing_explicit_live_authorization_creates_no_operational_catalog(
    repo_root: Path, evidence_root: Path, tmp_path: Path
) -> None:
    """No ``--live`` flag is a usage failure, and never a run that prepared anything."""
    from disclosure_drift.cli import main  # noqa: PLC0415

    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    _live_plan(evidence_root)

    assert (
        main(
            [
                "m3",
                "acquire",
                "--config",
                str(config),
                "--evidence-root",
                str(evidence_root),
                "--plan",
                "plans/approved.json",
                "--window",
                "M3.2A",
                "--data-root",
                _LIVE_DATA_ROOT,
                "--catalog",
                _LIVE_CATALOG,
            ]
        )
        == EXIT_USAGE
    )
    assert not _live_catalog_path(evidence_root).exists()
    assert _receipt_files(evidence_root) == []


def test_positive_control_the_same_invocation_does_create_the_catalog_when_it_is_lawful(
    repo_root: Path, evidence_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without this, every catalog-absence assertion above would pass against a broken command."""
    from disclosure_drift.cli import main  # noqa: PLC0415
    from disclosure_drift.m3.acquisition import derive_logical_requests  # noqa: PLC0415

    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    script = _InterruptScript()
    _install_live_seams(monkeypatch, script)
    plan = _live_plan(evidence_root)
    script.responses = [
        _fixture_body(item.source_id, str(index).encode())
        for index, item in enumerate(derive_logical_requests(plan))  # type: ignore[arg-type]
    ]

    assert main(_acquire_argv(evidence_root, config, plan, receipt_out="receipts/ok.json")) == (
        EXIT_OK
    )
    assert _live_catalog_path(evidence_root).is_file()
    assert script.constructions == 1


def test_an_m3_2a_run_without_a_baseline_source_creates_no_catalog_and_no_transport(
    repo_root: Path, evidence_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M3-L16 at the command surface: no carry-in, no resume, no run.

    The refusal is decidable from the operator's own arguments, so it lands with the other
    argument-decidable gates — before the operational catalog is created, before storage is
    prepared, and before any transport could be constructed. A run that silently restarted the
    consumed count at zero is exactly the stop condition M3-L16 records.
    """
    from disclosure_drift.cli import main  # noqa: PLC0415

    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    script = _InterruptScript()
    _install_live_seams(monkeypatch, script)
    plan = _live_plan(evidence_root)

    assert (
        main(
            _acquire_argv(
                evidence_root, config, plan, receipt_out="receipts/none.json", carry_in=None
            )
        )
        == EXIT_GATE_FAILURE
    )
    assert not _live_catalog_path(evidence_root).exists(), "no durable state was created"
    assert script.constructions == 0, "no transport was constructed"
    assert _receipt_files(evidence_root) == [], "a refused invocation writes no receipt"


def test_a_carry_in_and_a_resume_together_are_refused_at_the_command_surface(
    repo_root: Path, evidence_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exactly one baseline source. A carry-in root is never a resume, and the two never coexist."""
    from disclosure_drift.cli import main  # noqa: PLC0415

    config = _config_with_network(tmp_path, repo_root, enabled=True, acquire=True)
    script = _InterruptScript()
    _install_live_seams(monkeypatch, script)
    plan = _live_plan(evidence_root)
    authority = _write_carry_in(evidence_root, name="both", run_id="m3-2-acquisition-both")

    argv = _acquire_argv(
        evidence_root,
        config,
        plan,
        receipt_out="receipts/both.json",
        resume_from="receipts/interrupted.json",
    )
    argv += ["--carry-in-authority", authority]

    assert main(argv) == EXIT_USAGE
    assert not _live_catalog_path(evidence_root).exists()
    assert script.constructions == 0


# --------------------------------------------------------------------------- #
# Scoped SIGTERM handling (Decision 051 §7.3)
# --------------------------------------------------------------------------- #
class TestScopedSigterm:
    """`_scoped_sigterm_interruption` routes SIGTERM through the SIGINT lifecycle, in process."""

    def test_first_sigterm_raises_keyboard_interrupt_and_restores_prior_handler(self) -> None:
        from disclosure_drift.cli import _scoped_sigterm_interruption  # noqa: PLC0415

        def _prior(_signum: int, _frame: object) -> None:  # a distinctive prior disposition
            pass

        original = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, _prior)
        try:
            raised = False
            try:
                with _scoped_sigterm_interruption():
                    # Our handler is installed for the duration of the scope, not the prior one.
                    assert signal.getsignal(signal.SIGTERM) is not _prior
                    os.kill(os.getpid(), signal.SIGTERM)
                    # A pending signal is handled between bytecodes; force a few to run.
                    for _ in range(10000):
                        pass
            except KeyboardInterrupt:
                raised = True
            assert raised  # the first SIGTERM became a KeyboardInterrupt
            assert signal.getsignal(signal.SIGTERM) is _prior  # the prior handler is restored
        finally:
            signal.signal(signal.SIGTERM, original)

    def test_sigint_disposition_is_left_untouched(self) -> None:
        from disclosure_drift.cli import _scoped_sigterm_interruption  # noqa: PLC0415

        before = signal.getsignal(signal.SIGINT)
        with _scoped_sigterm_interruption():
            assert signal.getsignal(signal.SIGINT) is before  # SIGINT is never replaced
        assert signal.getsignal(signal.SIGINT) is before

    def test_scope_off_the_main_thread_is_a_noop_and_never_raises(self) -> None:
        import threading  # noqa: PLC0415

        from disclosure_drift.cli import _scoped_sigterm_interruption  # noqa: PLC0415

        errors: list[BaseException] = []

        def _worker() -> None:
            try:
                with _scoped_sigterm_interruption():
                    pass  # signal.signal off the main thread would raise; the guard must skip it
            except BaseException as exc:  # noqa: BLE001 - the test records any failure at all
                errors.append(exc)

        worker = threading.Thread(target=_worker)
        worker.start()
        worker.join()
        assert errors == []


# A disposable in-child driver: register a run, reserve one physical attempt through the ledger at
# the transport seam, signal readiness, and then block "mid-send" under the scoped SIGTERM. The
# reservation is committed *before* the blocking send begins, so when the parent delivers SIGTERM
# the durable `started` row already exists and no receipt is (or can be) written.
_SIGTERM_DRIVER = """
import sys, time
from pathlib import Path
from disclosure_drift.m3.acquisition import (
    OPERATIONAL_CATALOG_RELATIVE_PATH,
    PhysicalResponseLog,
    PreSendAttemptLedger,
    RecordingTransport,
    prepare_operational_catalog,
    register_acquisition_run,
)
from disclosure_drift.cli import _scoped_sigterm_interruption
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.sec.transport import SecRequest

evidence_root = Path(sys.argv[1])
ready = Path(sys.argv[2])


def _clock():
    return "2026-08-04T00:00:00Z"


prep = prepare_operational_catalog(
    evidence_root=evidence_root, relative_path=OPERATIONAL_CATALOG_RELATIVE_PATH
)
register_acquisition_run(
    catalog_path=prep.database_path,
    lock_directory=prep.lock_directory,
    census_run_id="proc-run",
    window="M3.2A",
    started_at_utc=_clock(),
    detail="sigterm fault injection",
)


class _Blocking:
    def send(self, request):
        ready.write_text("sent")  # the reservation is already committed before this runs
        time.sleep(60)  # block until the parent delivers SIGTERM
        raise SystemExit(0)  # never reached

    def close(self):
        pass


request = SecRequest(
    url="https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip",
    headers={},
    timeout_connect=1.0,
    timeout_read=1.0,
    purpose="acquire an approved Milestone 3.2 metadata object for an offline fixture",
    source_id="sec_bulk_submissions",
)
with CatalogWriter(prep.database_path, prep.lock_directory) as writer:
    ledger = PreSendAttemptLedger(writer=writer, job_id="proc-run", clock=_clock)
    recording = RecordingTransport(transport=_Blocking(), log=PhysicalResponseLog(), ledger=ledger)
    with _scoped_sigterm_interruption():
        recording.send(request)
"""


def test_sigterm_mid_send_leaves_a_durable_started_reservation(tmp_path: Path) -> None:
    """Process-level fault injection: a SIGTERM mid-send preserves the write-ahead reservation.

    This is the case a receipt cannot cover — the process is told to terminate while a physical send
    is in flight — so the durable `started` reservation is the protection. The child is killed with
    a real SIGTERM; the scoped handler turns it into the interruption lifecycle, and the reservation
    committed before the send survives.
    """
    evidence_root = tmp_path / "private-evidence"
    evidence_root.mkdir()
    ready = tmp_path / "ready"
    driver = tmp_path / "driver.py"
    driver.write_text(_SIGTERM_DRIVER, encoding="utf-8")

    child = subprocess.Popen(  # noqa: S603 - a trusted, in-repo driver script
        [sys.executable, str(driver), str(evidence_root), str(ready)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 30.0
        while not ready.exists() and time.monotonic() < deadline:
            if child.poll() is not None:
                stderr = (child.stderr.read() if child.stderr else "") or ""
                message = f"child exited before reserving; stderr:\n{stderr}"
                raise AssertionError(message)
            time.sleep(0.02)
        assert ready.exists(), "the child never reached the blocking send"

        child.send_signal(signal.SIGTERM)
        # If SIGTERM were not routed to the interruption lifecycle, the child would sleep 60s; the
        # tight wait budget is itself the proof that the interrupt was delivered and caught.
        returncode = child.wait(timeout=15)
    finally:
        if child.poll() is None:  # never leave a runaway child behind
            child.kill()
            child.wait(timeout=5)

    assert returncode != 0  # interrupted, not a clean completion of the 60s sleep

    catalog = evidence_root / "catalogs" / "m3_2a_operational.sqlite3"
    with sqlite3.connect(f"file:{catalog}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT job_id, attempt_number, attempt_state, finished_at_utc "
            "FROM ops_retrieval_attempts ORDER BY attempt_number"
        ).fetchall()

    # Exactly one durable reservation: the reserve committed it, and the signal handler — which
    # performs no writes — added nothing.
    assert len(rows) == 1
    assert rows[0]["job_id"] == "proc-run"
    assert rows[0]["attempt_number"] == 1
    assert rows[0]["attempt_state"] == "started"  # stranded but consumed; no fabricated receipt
    assert rows[0]["finished_at_utc"] is None


# --------------------------------------------------------------------------- #
# The clean-root carry-in interface at the operator surface
# (accepted Decision 055 §6, §7.5)
# --------------------------------------------------------------------------- #
def test_carry_in_authority_and_resume_from_are_mutually_exclusive(
    repo_root: Path, evidence_root: Path
) -> None:
    """§6: the carry-in interface is never resume, and the contradiction is a usage failure.

    Refused at dispatch, before a configuration is consulted, a plan is read, an artifact is
    opened, or any durable state is created — so nothing needs cleaning up after it.
    """
    before = sorted(str(path.relative_to(evidence_root)) for path in evidence_root.rglob("*"))

    result = _run(
        [
            "m3",
            "acquire",
            "--evidence-root",
            str(evidence_root),
            "--live",
            "--carry-in-authority",
            "authorities/carry-in.json",
            "--resume-from",
            "receipts/predecessor.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_USAGE
    assert "mutually exclusive" in result.stderr
    assert "never a resume" in result.stderr
    assert sorted(str(path.relative_to(evidence_root)) for path in evidence_root.rglob("*")) == (
        before
    )


def test_the_carry_in_flag_is_documented_on_the_acquire_surface(repo_root: Path) -> None:
    result = _run(["m3", "acquire", "--help"], repo_root)

    assert result.returncode == EXIT_OK
    assert "--carry-in-authority" in result.stdout


def test_show_scope_reports_the_walkers_cumulative_count_including_the_root_carry_in(
    repo_root: Path, evidence_root: Path
) -> None:
    """§7.5: `--show-scope` must agree with the receipt-chain walker, root carry-in included.

    The chain here is a carry-in root that placed one attempt on a baseline of one, followed by a
    resume that placed one more. The walker's answer is 3; reporting the head receipt alone, or
    omitting the root's baseline, would give 2. The command must print what the walker computes.
    """
    _approved_plan(repo_root, evidence_root)

    from disclosure_drift.m3.recovery import walk_receipt_chain

    root, head_path = _carry_in_chain(evidence_root)
    expected = walk_receipt_chain(head_path).consumed_physical_attempts
    assert expected == 3, "1 carried in + 1 placed by the root + 1 placed by the resume"

    result = _run(
        [
            "m3",
            "acquire",
            "--evidence-root",
            str(evidence_root),
            "--show-scope",
            "--plan",
            "plans/m3_2a.json",
            "--window",
            "M3.2A",
            "--receipt-chain-head",
            f"receipts/{head_path.name}",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_OK, result.stderr
    baseline = next(
        line for line in result.stdout.splitlines() if "consumed-count baseline" in line
    )
    assert baseline.rsplit(":", 1)[1].strip() == str(expected)
    carried = next(line for line in result.stdout.splitlines() if "carried in at root" in line)
    assert carried.rsplit(":", 1)[1].strip() == "1"
    assert root.receipt_id  # the root really is part of the reported chain
    chain_line = next(line for line in result.stdout.splitlines() if "receipt chain length" in line)
    assert chain_line.rsplit(":", 1)[1].strip() == "2"


def _carry_in_chain(evidence_root: Path) -> tuple[object, Path]:
    """Write a two-receipt chain rooted in a clean carry-in root, and return the head path."""
    from disclosure_drift.m3.receipt import ExecutionReceipt, write_receipt

    common: dict[str, object] = {
        "command_name": "m3 acquire",
        "command_version": "m3.2a/1.0",
        "phase": "M3.2A",
        "invocation_mode": "live",
        "configuration_fingerprint": "a" * 64,
        "migration_chain_head": "0013_m23_manifest_lifecycle_guards",
        "started_at_utc": "2026-08-01T12:00:00Z",
        "completed_at_utc": "2026-08-01T12:00:09Z",
        "elapsed_seconds": 9.0,
        "source_registry_version": "m2.2-source-registry/1.0",
        "index_plan_policy_version": "quarterly-index-instances/2.0",
        "request_plan_schema_version": "m3-request-plan/1.0",
        "parser_versions": {"company-tickers": "1.0"},
        "acquisition_window": "M3.2A",
        "request_plan_id": "plan-0001",
        "request_plan_sha256": "b" * 64,
        "approved_request_ceiling": 801,
        "planned_logical_request_count": 7,
        "maximum_physical_attempt_count": 60,
        "planned_per_route": {"sec_company_tickers": 7},
        "actual_logical_request_count": 1,
        "actual_physical_attempt_count": 1,
        "actual_per_route": {
            "sec_company_tickers": {"logical_request_count": 1, "physical_attempt_count": 1},
        },
        "response_classification_totals": {
            "proceed": 1,
            "retry": 0,
            "retry_after": 0,
            "cooldown": 0,
            "fail": 0,
            "quarantine": 0,
        },
        "status_code_totals": {"200": 1},
        "raw_object_count": 1,
        "duplicate_object_count": 0,
        "cache_hit_count": 0,
        "not_modified_count": 0,
        "quarantined_object_count": 0,
        "redirect_hop_count": 0,
        "cooldown_count": 0,
        "schema_drift_outcome": "none",
        "schema_drift_event_count": 0,
        "completion_status": "interrupted",
        "reason_code": "SEC_ACQUISITION_INTERRUPTED",
        "reason_detail": "the acquisition was interrupted before completion.",
        "interruption_state": "after_catalog_commit",
    }
    checkout = evidence_root.parent / "checkout"
    checkout.mkdir(exist_ok=True)
    root = ExecutionReceipt(
        **common,
        consumed_request_count_carried_forward=1,
        carry_in_authority_sha256="e" * 64,
    )
    write_receipt(root, evidence_root=evidence_root, repository_root=checkout)
    head = ExecutionReceipt(
        **{**common, "command_version": "m3.2a/1.1"},
        recovery_predecessor_receipt_id=root.receipt_id,
        consumed_request_count_carried_forward=2,
    )
    return root, write_receipt(head, evidence_root=evidence_root, repository_root=checkout)


# --------------------------------------------------------------------------- #
# Decision 062 §7 — the plan-transition flag at the operator surface
# --------------------------------------------------------------------------- #
def test_the_plan_transition_flag_is_opt_in_and_never_inferred(
    repo_root: Path, evidence_root: Path
) -> None:
    """Omitting it leaves condition 8.10 exactly as it was: the hash must be unchanged."""
    _recovery_inputs(repo_root, evidence_root)

    result = _recovery_state(repo_root, evidence_root)

    assert "--plan-transition-predecessor" not in result.stdout
    assert "8.10" in result.stdout


def test_an_unauthorized_plan_pair_is_refused_at_the_operator_surface(
    repo_root: Path, evidence_root: Path
) -> None:
    """The flag exposes one authorized substitution, not a general resume-against-another-plan.

    The predecessor named here is a real, canonical plan document — it is simply not the pair
    Decision 062 names, which is the only thing that makes a transition lawful.
    """
    _recovery_inputs(repo_root, evidence_root)

    result = _run(
        [
            "m3",
            "recovery-state",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/interrupted.json",
            "--plan-transition-predecessor",
            "plans/interrupted.json",
            "--receipt-chain-head",
            "receipts/plan.json",
            "--catalog",
            "catalog/sec_ingestion.sqlite3",
            "--data-root",
            "tree",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "plan transition is refused" in result.stderr
    assert "creates no general capability to resume against another plan" in result.stderr


def test_a_plan_transition_is_refused_in_receiptless_mode(
    repo_root: Path, evidence_root: Path
) -> None:
    """A transition binds to a predecessor receipt, and receiptless mode is defined by having none.

    Refused as a usage error rather than silently ignored: dropping it would report a
    determination the operator believes was reached under an authority.
    """
    _recovery_inputs(repo_root, evidence_root)

    result = _run(
        [
            "m3",
            "recovery-state",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/interrupted.json",
            "--plan-transition-predecessor",
            "plans/interrupted.json",
            "--receiptless-first-invocation",
            "--run",
            "some-run-id",
            "--catalog",
            "catalog/sec_ingestion.sqlite3",
            "--data-root",
            "tree",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_USAGE
    assert "not valid with --receiptless-first-invocation" in result.stderr


def test_acquire_refuses_a_plan_transition_without_a_resume(
    repo_root: Path, evidence_root: Path
) -> None:
    """A transition names the predecessor a continuation continues; without one there is nothing."""
    result = _run(
        [
            "m3",
            "acquire",
            "--live",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/approved.json",
            "--window",
            "M3.2A",
            "--ceiling",
            "801",
            "--catalog",
            "operational.sqlite3",
            "--data-root",
            "tree",
            "--receipt-out",
            "receipts/acquire.json",
            "--plan-transition-predecessor",
            "plans/predecessor.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_USAGE
    assert "--plan-transition-predecessor requires --resume-from" in result.stderr


def test_no_m3_command_reaches_the_network_with_a_plan_transition(
    repo_root: Path, evidence_root: Path
) -> None:
    """Decision 062 grants no live authority: the flag is offline, like the command carrying it."""
    _recovery_inputs(repo_root, evidence_root)

    result = _run(
        [
            "m3",
            "recovery-state",
            "--evidence-root",
            str(evidence_root),
            "--plan",
            "plans/interrupted.json",
            "--plan-transition-predecessor",
            "plans/interrupted.json",
            "--receipt-chain-head",
            "receipts/plan.json",
            "--catalog",
            "catalog/sec_ingestion.sqlite3",
            "--data-root",
            "tree",
        ],
        repo_root,
    )

    assert "sec.gov" not in result.stdout
    assert result.returncode in {EXIT_OK, EXIT_GATE_FAILURE}


# --------------------------------------------------------------------------- #
# Cross-namespace receipt chains (Decision 063)
# --------------------------------------------------------------------------- #
def _live_receipt(**overrides: object) -> object:
    """One minimal valid `live` receipt, built through the real constructor."""
    from disclosure_drift.m3.receipt import ExecutionReceipt

    fields: dict[str, object] = {
        "command_name": "m3 acquire",
        "command_version": "m3.2a/1.0",
        "phase": "M3.2A",
        "invocation_mode": "live",
        "configuration_fingerprint": "a" * 64,
        "migration_chain_head": "0013_m23_manifest_lifecycle_guards",
        "started_at_utc": "2026-08-01T12:00:00Z",
        "completed_at_utc": "2026-08-01T12:00:09Z",
        "elapsed_seconds": 9.0,
        "source_registry_version": "m2.2-source-registry/1.1",
        "index_plan_policy_version": "quarterly-index-instances/2.0",
        "request_plan_schema_version": "m3-request-plan/1.1",
        "parser_versions": {"sic-code-list": "1.0"},
        "acquisition_window": "M3.2A",
        "request_plan_id": "plan-0001",
        "request_plan_sha256": "b" * 64,
        "approved_request_ceiling": 801,
        "planned_logical_request_count": 75,
        "maximum_physical_attempt_count": 801,
        "planned_per_route": {"sec_full_index": 75},
        "actual_logical_request_count": 1,
        "actual_physical_attempt_count": 1,
        "actual_per_route": {
            "sec_full_index": {"logical_request_count": 1, "physical_attempt_count": 1},
        },
        "response_classification_totals": {
            "proceed": 1,
            "retry": 0,
            "retry_after": 0,
            "cooldown": 0,
            "fail": 0,
            "quarantine": 0,
        },
        "status_code_totals": {"200": 1},
        "raw_object_count": 1,
        "duplicate_object_count": 0,
        "cache_hit_count": 0,
        "not_modified_count": 0,
        "quarantined_object_count": 0,
        "redirect_hop_count": 0,
        "cooldown_count": 0,
        "schema_drift_outcome": "none",
        "schema_drift_event_count": 0,
        "completion_status": "complete",
    }
    fields.update(overrides)
    return ExecutionReceipt(**fields)


def test_show_receipt_resolves_a_chain_across_run_namespaces(
    repo_root: Path, evidence_root: Path
) -> None:
    """The real T7 shape, driven through the real CLI.

    `--receipt-out` puts each run's receipt in its own namespace, so the continuation's head is in
    `runs/m3_2_decision_062_sic_continuation/` while the receipt it names is in
    `runs/m3_2a_clean_carry_in/`. The chain is intact; the command must say so, and must reach
    length 2 rather than reporting a predecessor that does not resolve.
    """
    predecessor = _live_receipt(request_plan_id="plan-predecessor")
    head = _live_receipt(
        request_plan_id="plan-successor",
        recovery_predecessor_receipt_id=predecessor.receipt_id,  # type: ignore[attr-defined]
        consumed_request_count_carried_forward=1,
    )
    for item, namespace in (
        (predecessor, "m3_2a_clean_carry_in"),
        (head, "m3_2_decision_062_sic_continuation"),
    ):
        path = evidence_root / "runs" / namespace / "execution_receipt.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(item.canonical_bytes())  # type: ignore[attr-defined]

    result = _run(
        [
            "m3",
            "show-receipt",
            "--evidence-root",
            str(evidence_root),
            "--receipt",
            "runs/m3_2_decision_062_sic_continuation/execution_receipt.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_OK, result.stderr
    assert "recovery_chain_length" in result.stdout
    assert result.stdout.split("recovery_chain_length")[1].split("\n")[0].strip().endswith("2")
    assert str(evidence_root) not in result.stdout
    assert str(evidence_root) not in result.stderr


def test_show_receipt_still_refuses_a_predecessor_that_exists_nowhere(
    repo_root: Path, evidence_root: Path
) -> None:
    """Widening where a predecessor may be found never widens what counts as one.

    Same command, same layout, and a recorded identity no accepted receipt location holds: the
    chain is still refused, and no receipt is invented to close it.
    """
    head = _live_receipt(
        recovery_predecessor_receipt_id="c" * 64,
        consumed_request_count_carried_forward=1,
    )
    path = evidence_root / "runs" / "m3_2_decision_062_sic_continuation" / "execution_receipt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(head.canonical_bytes())  # type: ignore[attr-defined]

    result = _run(
        [
            "m3",
            "show-receipt",
            "--evidence-root",
            str(evidence_root),
            "--receipt",
            "runs/m3_2_decision_062_sic_continuation/execution_receipt.json",
        ],
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE
    assert "recovery_predecessor_receipt_id" in result.stderr
    assert str(evidence_root) not in result.stderr


# =========================================================================== #
# Decision 064 §7 — transition-aware `m3 reconcile-requests`
# =========================================================================== #
def _successor_plan_artifact(evidence_root: Path) -> Path:
    """Write the Decision 062 successor plan document and return its relative path.

    Identical to the predecessor in every input; the only difference is the source registry it is
    bound to, which is what moves exactly one request identity.
    """
    from datetime import date  # noqa: PLC0415

    from disclosure_drift.m3.request_plan import (  # noqa: PLC0415
        build_m3_2a_request_plan,
        canonical_plan_bytes,
    )

    plan = build_m3_2a_request_plan(
        coverage_start=date(2009, 1, 1),
        coverage_end=date(2026, 6, 30),
        as_of_date=date(2026, 6, 30),
        include_open_quarter=False,
        calendar_year=2026,
        calendar_evidence_entry_count=0,
        already_satisfied_index_keys=frozenset(),
        requests_per_second=4.0,
    )
    destination = evidence_root / "plans" / "successor.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_plan_bytes(plan))
    return Path("plans/successor.json")


def _predecessor_receipt_artifact(
    evidence_root: Path, *, source_registry_version: str = "m2.2-source-registry/1.0"
) -> Path:
    """A minimal valid live receipt recording what the predecessor run was bound to.

    The transition's registry-version condition asks what the predecessor *run recorded*, so the
    receipt is the only surface that can answer it. Nothing else about this receipt is load-bearing.
    """
    from disclosure_drift.m3.receipt import ExecutionReceipt, write_receipt  # noqa: PLC0415

    receipt = ExecutionReceipt(
        command_name="m3 acquire",
        command_version="m3.2a/1.0",
        phase="M3.2A",
        invocation_mode="live",
        configuration_fingerprint="a" * 64,
        migration_chain_head="0013_m23_manifest_lifecycle_guards",
        started_at_utc="2026-08-04T00:00:00Z",
        completed_at_utc="2026-08-04T00:00:09Z",
        elapsed_seconds=9.0,
        source_registry_version=source_registry_version,
        index_plan_policy_version="quarterly-index-instances/2.0",
        request_plan_schema_version="m3-request-plan/1.0",
        parser_versions={"company-tickers": "1.0"},
        acquisition_window="M3.2A",
        request_plan_id="plan-predecessor",
        request_plan_sha256=("19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68"),
        approved_request_ceiling=801,
        planned_logical_request_count=75,
        maximum_physical_attempt_count=801,
        planned_per_route={"sec_company_tickers": 75},
        actual_logical_request_count=1,
        actual_physical_attempt_count=1,
        actual_per_route={
            "sec_company_tickers": {"logical_request_count": 1, "physical_attempt_count": 1},
        },
        response_classification_totals={
            "proceed": 1,
            "retry": 0,
            "retry_after": 0,
            "cooldown": 0,
            "fail": 0,
            "quarantine": 0,
        },
        status_code_totals={"200": 1},
        raw_object_count=1,
        duplicate_object_count=0,
        cache_hit_count=0,
        not_modified_count=0,
        quarantined_object_count=0,
        redirect_hop_count=0,
        cooldown_count=0,
        schema_drift_outcome="none",
        schema_drift_event_count=0,
        completion_status="failed",
        reason_code="SEC_ACQUISITION_INTERRUPTED",
        reason_detail="the predecessor run ended terminally.",
    )
    checkout = evidence_root.parent / "predecessor-receipt-checkout"
    checkout.mkdir(parents=True, exist_ok=True)
    written = write_receipt(receipt, evidence_root=evidence_root, repository_root=checkout)
    return written.relative_to(evidence_root)


def _record_retired_sic_failure(evidence_root: Path) -> str:
    """Commit the one stranded observation the endpoint drift left behind, and return its identity.

    A fixture acquisition cannot produce this row: the driver always resolves URLs through the live
    source registry, so it retrieves the *successor* path whatever a plan document says it is bound
    to. The retired identity therefore has to be written directly, exactly as the real predecessor
    run committed it — a failed retrieval of the old exact path, with no stored object.
    """
    from disclosure_drift.m3.acquisition import (  # noqa: PLC0415
        PLAN_TRANSITION_OLD_URL,
        prepare_operational_catalog,
        prepare_storage,
    )
    from disclosure_drift.sec.observation_catalog import ObservationRecorder  # noqa: PLC0415
    from disclosure_drift.sec.snapshots import SourceObservation  # noqa: PLC0415
    from disclosure_drift.sec.urls import request_identity  # noqa: PLC0415
    from disclosure_drift.storage.catalog import CatalogWriter  # noqa: PLC0415

    preparation = prepare_operational_catalog(
        evidence_root=evidence_root, relative_path=_FIXTURE_CATALOG
    )
    storage = prepare_storage(evidence_root=evidence_root, data_root_relative=_FIXTURE_DATA_ROOT)
    identity = request_identity("sec_sic_code_list", PLAN_TRANSITION_OLD_URL, {})
    with CatalogWriter(preparation.database_path, preparation.lock_directory) as writer:
        ObservationRecorder(writer=writer, tree=storage.tree).record(
            SourceObservation(
                observation_id="retired" + "0" * 25,
                source_id="sec_sic_code_list",
                requested_url=PLAN_TRANSITION_OLD_URL,
                purpose="acquire the approved Milestone 3.2 metadata object",
                retrieved_at_utc="2026-08-04T00:00:00Z",
                outcome="failed",
                identity=identity,
                http_status=301,
                attempts=1,
                reason_codes=("SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",),
                detail="the retired exact path redirected outside the source boundary",
            )
        )
    return identity


def _reconcile_argv(
    evidence_root: Path, plan_relative: Path, *, report: str, extra: list[str] | None = None
) -> list[str]:
    return [
        "m3",
        "reconcile-requests",
        "--evidence-root",
        str(evidence_root),
        "--plan",
        str(plan_relative),
        *_catalog_arguments(),
        "--report-out",
        report,
        *(extra or []),
    ]


def test_reconcile_requests_refuses_half_a_plan_transition(
    repo_root: Path, evidence_root: Path
) -> None:
    """Neither half of the binding establishes a transition, so neither is accepted alone."""
    plan_relative = _acquired_window(evidence_root, run_id="run-half-transition")
    successor = _successor_plan_artifact(evidence_root)
    receipt_relative = _predecessor_receipt_artifact(evidence_root)

    only_plan = _run(
        _reconcile_argv(
            evidence_root,
            successor,
            report="reports/half-a.json",
            extra=["--plan-transition-predecessor", str(plan_relative)],
        ),
        repo_root,
    )
    only_receipt = _run(
        _reconcile_argv(
            evidence_root,
            successor,
            report="reports/half-b.json",
            extra=["--plan-transition-predecessor-receipt", str(receipt_relative)],
        ),
        repo_root,
    )

    assert only_plan.returncode == EXIT_USAGE, only_plan.stdout
    assert only_receipt.returncode == EXIT_USAGE, only_receipt.stdout
    assert not (evidence_root / "reports" / "half-a.json").exists(), (
        "a usage failure writes nothing"
    )
    assert not (evidence_root / "reports" / "half-b.json").exists()


def test_reconcile_requests_refuses_an_unauthorized_plan_pair(
    repo_root: Path, evidence_root: Path
) -> None:
    """A transition is never inferred: only the pair an accepted decision names is admitted."""
    plan_relative = _acquired_window(evidence_root, run_id="run-wrong-pair")
    receipt_relative = _predecessor_receipt_artifact(evidence_root)

    result = _run(
        _reconcile_argv(
            evidence_root,
            plan_relative,
            report="reports/wrong-pair.json",
            extra=[
                "--plan-transition-predecessor",
                str(plan_relative),
                "--plan-transition-predecessor-receipt",
                str(receipt_relative),
            ],
        ),
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE, result.stdout
    assert "plan transition is refused" in result.stderr
    assert not (evidence_root / "reports" / "wrong-pair.json").exists(), (
        "a refused transition never writes a report that could read as a clean reconciliation"
    )


def test_reconcile_requests_refuses_a_predecessor_receipt_recording_the_wrong_registry(
    repo_root: Path, evidence_root: Path
) -> None:
    """Condition 14 binds to what the predecessor run recorded, and it is checked literally."""
    _acquired_window(evidence_root, run_id="run-wrong-registry")
    predecessor = Path("plans/acquired.json")
    successor = _successor_plan_artifact(evidence_root)
    receipt_relative = _predecessor_receipt_artifact(
        evidence_root, source_registry_version="m2.2-source-registry/1.1"
    )

    result = _run(
        _reconcile_argv(
            evidence_root,
            successor,
            report="reports/wrong-registry.json",
            extra=[
                "--plan-transition-predecessor",
                str(predecessor),
                "--plan-transition-predecessor-receipt",
                str(receipt_relative),
            ],
        ),
        repo_root,
    )

    assert result.returncode == EXIT_GATE_FAILURE, result.stdout
    assert "source registry" in result.stderr


def test_the_authorized_transition_supersedes_exactly_the_retired_identity(
    repo_root: Path, evidence_root: Path
) -> None:
    """The whole point of the flag, end to end through the real command surface.

    The catalog holds the retired SIC identity and not the successor's. Reconciled against the
    successor plan **without** the flag, that identity is an ordinary blocking out-of-plan
    observation and the window can never come clean. **With** the authorized pair, it moves to
    `superseded_out_of_plan` — still listed, still visible, still satisfying nothing — and every
    other observation is untouched.
    """
    _acquired_window(evidence_root, run_id="run-transition")
    retired = _record_retired_sic_failure(evidence_root)
    predecessor = Path("plans/acquired.json")
    successor = _successor_plan_artifact(evidence_root)
    receipt_relative = _predecessor_receipt_artifact(evidence_root)

    without = _run(
        _reconcile_argv(evidence_root, successor, report="reports/without.json"), repo_root
    )
    with_authority = _run(
        _reconcile_argv(
            evidence_root,
            successor,
            report="reports/with.json",
            extra=[
                "--plan-transition-predecessor",
                str(predecessor),
                "--plan-transition-predecessor-receipt",
                str(receipt_relative),
            ],
        ),
        repo_root,
    )

    assert without.returncode == EXIT_GATE_FAILURE, without.stdout
    blocked = json.loads((evidence_root / "reports" / "without.json").read_text(encoding="utf-8"))
    assert blocked["plan_transition"] is None
    assert blocked["reconciliation"]["out_of_plan"], "the retired identity blocks without authority"
    assert blocked["reconciliation"]["superseded_out_of_plan"] == []

    assert with_authority.returncode == EXIT_OK, with_authority.stdout
    document = json.loads((evidence_root / "reports" / "with.json").read_text(encoding="utf-8"))
    assert document["reconciliation"]["out_of_plan"] == []
    superseded = document["reconciliation"]["superseded_out_of_plan"]
    assert len(superseded) == 1
    assert superseded == [["sec_sic_code_list", retired]]
    assert document["plan_transition"] == {
        "decision_reference": "Decision 062",
        "predecessor_plan_sha256": (
            "19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68"
        ),
        "successor_plan_sha256": (
            "f77e003ccc0ed8f9c0e55065b3c211aa5e33c7abf86cc71cbe66d427611d890a"
        ),
        "substituted_source_id": "sec_sic_code_list",
    }
    assert "superseded out-of-plan observations : 1" in " ".join(with_authority.stdout.split())
    assert "plan transition applied" in with_authority.stdout


def test_a_transition_aware_reconciliation_writes_only_its_report(
    repo_root: Path, evidence_root: Path
) -> None:
    """Read-only except the accepted report artifact, and zero network."""
    _acquired_window(evidence_root, run_id="run-transition-readonly")
    _record_retired_sic_failure(evidence_root)
    predecessor = Path("plans/acquired.json")
    successor = _successor_plan_artifact(evidence_root)
    receipt_relative = _predecessor_receipt_artifact(evidence_root)

    def _durable() -> dict[str, bytes]:
        # SQLite's `-wal` and `-shm` sidecars and the writer lease are process-lifetime artefacts
        # that appear and vanish around any connection, including a read-only one. What the claim
        # is about is durable evidence: the catalog itself, the raw objects, the plans, and the
        # receipts.
        transient = ("-wal", "-shm", ".lease")
        return {
            str(path.relative_to(evidence_root)): path.read_bytes()
            for path in sorted(evidence_root.rglob("*"))
            if path.is_file() and not path.name.endswith(transient)
        }

    before = _durable()

    result = _run(
        _reconcile_argv(
            evidence_root,
            successor,
            report="reports/readonly.json",
            extra=[
                "--plan-transition-predecessor",
                str(predecessor),
                "--plan-transition-predecessor-receipt",
                str(receipt_relative),
            ],
        ),
        repo_root,
    )

    assert result.returncode == EXIT_OK, result.stdout
    after = _durable()
    assert sorted(set(after) - set(before)) == ["reports/readonly.json"], (
        "the report is the only artifact written"
    )
    assert {name: after[name] for name in before} == before, "nothing existing was modified"


def test_a_reconciliation_never_checkpoints_a_pending_write_ahead_log(
    repo_root: Path, evidence_root: Path, stage_pending_wal: Callable[[Path], None]
) -> None:
    """The read-only claim has to cover the write no statement asks for.

    A read-*write* handle to a WAL-mode database checkpoints the pending log into the main file
    when the last connection closes. The catalog's durable bytes change, and every statement the
    command issued was a `SELECT` — so `PRAGMA query_only` sees nothing to refuse and the claim
    fails anyway. That is the defect Decision 066 R1 corrects, and it is invisible unless a
    pending log is actually staged, which is why this test stages one rather than hoping the
    fixture leaves one behind.
    """
    _acquired_window(evidence_root, run_id="run-pending-wal")
    retired = _record_retired_sic_failure(evidence_root)
    predecessor = Path("plans/acquired.json")
    successor = _successor_plan_artifact(evidence_root)
    receipt_relative = _predecessor_receipt_artifact(evidence_root)

    catalog = evidence_root / _FIXTURE_CATALOG
    stage_pending_wal(catalog)
    before = catalog.read_bytes()

    result = _run(
        _reconcile_argv(
            evidence_root,
            successor,
            report="reports/pending-wal.json",
            extra=[
                "--plan-transition-predecessor",
                str(predecessor),
                "--plan-transition-predecessor-receipt",
                str(receipt_relative),
            ],
        ),
        repo_root,
    )

    assert result.returncode == EXIT_OK, result.stdout
    assert catalog.read_bytes() == before, (
        "the pending log was folded into the durable catalog by a read-only command"
    )
    # And it reconciled properly *through* that pending log rather than by failing to read it.
    document = json.loads(
        (evidence_root / "reports" / "pending-wal.json").read_text(encoding="utf-8")
    )
    assert document["reconciliation"]["out_of_plan"] == []
    assert document["reconciliation"]["superseded_out_of_plan"] == [["sec_sic_code_list", retired]]
