"""Milestone 3.1 command group (`Milestones/contracts/m3_1.md` §9).

These tests drive the real CLI as a subprocess, so what they assert is what an operator would
actually see and what a gate would actually read: exit codes, the evidence-root boundary, the
completion token, and the two properties Gate F depends on — that two dry runs agree byte for byte,
and that no command discloses an absolute path or the SEC identity.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
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
    result = _run(["m3", "acquire"], repo_root)

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
    # The schema is untouched: Decision 029 registers a permitted value, not a schema element.
    assert receipt["receipt_schema_version"] == "m3-execution-receipt/2.0"
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
    assert "Safe-resume determination" in normalized
    assert "nothing was repaired" in normalized
    for label in (
        "interruption state",
        "consumed physical attempts",
        "orphan objects",
        "partial files",
        "determination",
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
    """§11 and stop condition 10: inspection never writes. Proven by byte comparison."""
    import hashlib

    _recovery_inputs(repo_root, evidence_root)
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(evidence_root.rglob("*"))
        if path.is_file()
    }

    _recovery_state(repo_root, evidence_root)

    after = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(evidence_root.rglob("*"))
        if path.is_file()
    }
    assert after == before


def test_recovery_state_takes_no_run_or_repair_flag(repo_root: Path, evidence_root: Path) -> None:
    """§9: "There is no `--run` shortcut and no repair flag"."""
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
