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


def _rehearse(repo_root: Path, evidence_root: Path) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "m3",
            "rehearse",
            "--evidence-root",
            str(evidence_root),
            "--evidence-out",
            "reports/a1-a12.json",
            "--receipt-out",
            "receipts/rehearse.json",
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
            "--data-root",
            str(evidence_root / "data"),
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
        ["m3", "rehearse", "--evidence-root", str(evidence_root), "--scenarios", "A1,A2"],
        repo_root,
    )

    assert result.returncode == EXIT_OK
    assert "M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED" not in result.stdout


def test_an_unknown_scenario_is_a_gate_failure(repo_root: Path, evidence_root: Path) -> None:
    result = _run(
        ["m3", "rehearse", "--evidence-root", str(evidence_root), "--scenarios", "A99"],
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
    _run(["m3", "rehearse", "--evidence-root", str(evidence_root)], repo_root)

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


def test_rehearse_report_refuses_an_incomplete_record(repo_root: Path, evidence_root: Path) -> None:
    _rehearse(repo_root, evidence_root)
    path = evidence_root / "reports" / "a1-a12.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["complete"] = False
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
