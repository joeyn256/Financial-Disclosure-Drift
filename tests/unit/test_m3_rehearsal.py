"""Offline acquisition-path rehearsal, A1-A12 (`Docs/m3/offline_rehearsal_spec.md`).

What these tests guard is mostly *the harness*, not the scenarios: the scenarios assert their own
conditions and report findings, so the risk is not that one silently fails but that one silently
does not run, or that the `A_reachable` confirmation is a tautology rather than evidence.

Accordingly they pin: the registry is exactly the twelve mandatory scenarios; no skip path exists;
the rehearsal places no real request; and the tested `A_reachable` is measured by execution rather
than copied from the derivation it is supposed to confirm.
"""

from __future__ import annotations

import pytest

from disclosure_drift.m3.rehearsal import (
    REHEARSAL_REPORT_SCHEMA_VERSION,
    SCENARIO_IDS,
    RehearsalError,
    RehearsalReport,
    run_rehearsal,
    scenario_titles,
)
from disclosure_drift.m3.request_plan import derive_a_reachable
from disclosure_drift.sec.source_registry import SOURCES


@pytest.fixture(scope="module")
def report() -> RehearsalReport:
    """One full rehearsal, reused across assertions: it drives the real client many times."""
    return run_rehearsal()


# --------------------------------------------------------------------------- #
# The registry is exactly the twelve mandatory scenarios
# --------------------------------------------------------------------------- #
def test_the_schema_version_is_fixed() -> None:
    assert REHEARSAL_REPORT_SCHEMA_VERSION == "m3-rehearsal-report/1.0"


def test_exactly_twelve_scenarios_are_registered() -> None:
    assert SCENARIO_IDS == (
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "A6",
        "A7",
        "A8",
        "A9",
        "A10",
        "A11",
        "A12",
    )
    assert len(set(SCENARIO_IDS)) == 12


def test_every_scenario_id_has_a_title() -> None:
    titles = scenario_titles()
    assert tuple(titles) == SCENARIO_IDS
    assert all(title.strip() for title in titles.values())


def test_all_twelve_run_and_the_report_is_complete(report: RehearsalReport) -> None:
    assert report.complete
    assert tuple(outcome.scenario_id for outcome in report.outcomes) == SCENARIO_IDS


def test_every_scenario_passes(report: RehearsalReport) -> None:
    failures = [
        f"{outcome.scenario_id}: {outcome.detail}"
        for outcome in report.outcomes
        if not outcome.passed
    ]
    assert not failures, "; ".join(failures)


def test_an_unknown_scenario_is_refused() -> None:
    with pytest.raises(RehearsalError, match="A13"):
        run_rehearsal(["A13"])


def test_a_subset_runs_but_does_not_claim_completeness() -> None:
    partial = run_rehearsal(["A1", "A2"])

    assert not partial.complete
    assert tuple(outcome.scenario_id for outcome in partial.outcomes) == ("A1", "A2")


def test_scenarios_run_in_registry_order_regardless_of_request_order() -> None:
    partial = run_rehearsal(["A9", "A2"])

    assert tuple(outcome.scenario_id for outcome in partial.outcomes) == ("A2", "A9")


# --------------------------------------------------------------------------- #
# Zero network activity
# --------------------------------------------------------------------------- #
def test_the_rehearsal_records_simulated_activity_not_network_activity(
    report: RehearsalReport,
) -> None:
    """Simulated totals are non-zero here, and never in a receipt's network fields."""
    assert report.simulated_physical_attempts > 0
    assert report.simulated_logical_requests > 0


def test_no_socket_is_opened(report: RehearsalReport) -> None:
    """The suite-wide socket guard raises on any real connection, so completing proves it."""
    assert report.complete


# --------------------------------------------------------------------------- #
# The A_reachable confirmation is evidence, not a tautology
# --------------------------------------------------------------------------- #
def test_the_tested_bound_is_measured_for_every_exercisable_route(report: RehearsalReport) -> None:
    exercisable = set(SOURCES) - set(report.unmeasured_routes)
    assert set(report.tested_a_reachable) == exercisable
    assert len(exercisable) >= 8


def test_the_derived_and_tested_bounds_agree(report: RehearsalReport) -> None:
    disagreements = {
        source_id: (report.derived_a_reachable[source_id], tested)
        for source_id, tested in report.tested_a_reachable.items()
        if report.derived_a_reachable[source_id] != tested
    }
    assert not disagreements, f"derived vs tested disagreement: {disagreements}"
    assert report.a_reachable_agrees


def test_the_bounds_are_not_uniform_so_agreement_is_informative(report: RehearsalReport) -> None:
    """If every route had the same bound, agreement would prove very little."""
    assert len(set(report.tested_a_reachable.values())) >= 3


def test_the_tested_bound_matches_the_known_per_route_shape(report: RehearsalReport) -> None:
    assert report.tested_a_reachable["sec_company_tickers"] == 6
    assert report.tested_a_reachable["sec_edgar_filing_calendar"] == 7
    assert report.tested_a_reachable["sec_full_index_company"] == 11


def test_an_unmeasurable_route_is_reported_rather_than_assumed(report: RehearsalReport) -> None:
    """Copying the derivation would make the confirmation circular; silence would hide the gap."""
    for source_id, reason in report.unmeasured_routes.items():
        assert source_id not in report.tested_a_reachable
        assert reason.strip()


def test_the_derivation_covers_every_registered_route(report: RehearsalReport) -> None:
    assert set(report.derived_a_reachable) == set(SOURCES)
    for source_id, spec in SOURCES.items():
        assert report.derived_a_reachable[source_id] == derive_a_reachable(spec)


# --------------------------------------------------------------------------- #
# The evidence report
# --------------------------------------------------------------------------- #
def test_the_report_serializes_canonically(report: RehearsalReport) -> None:
    payload = report.canonical_bytes()

    assert payload.endswith(b"\n")
    assert not payload.endswith(b"\n\n")
    assert b"\r" not in payload


def test_the_report_is_reproducible_from_the_same_outcomes(report: RehearsalReport) -> None:
    assert report.canonical_bytes() == report.canonical_bytes()


def test_the_evidence_reference_is_content_derived(report: RehearsalReport) -> None:
    assert report.evidence_reference.startswith("m3-1a-rehearsal-report-")
    assert len(report.evidence_reference) == len("m3-1a-rehearsal-report-") + 64


def test_the_report_carries_no_identity_or_absolute_path(report: RehearsalReport) -> None:
    text = report.canonical_bytes().decode("utf-8")

    assert "@" not in text
    assert "/Users/" not in text


def test_the_report_names_every_scenario(report: RehearsalReport) -> None:
    text = report.canonical_bytes().decode("utf-8")
    for scenario_id in SCENARIO_IDS:
        assert f'"{scenario_id}"' in text
