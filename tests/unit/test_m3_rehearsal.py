"""Offline acquisition-path rehearsal, A1-A12 (`Docs/m3/offline_rehearsal_spec.md`).

What these tests guard is mostly *the harness*, not the scenarios: the scenarios assert their own
conditions and report findings, so the risk is not that one silently fails but that one silently
does not run, or that the `A_reachable` confirmation is a tautology rather than evidence.

Accordingly they pin: the registry is exactly the twelve mandatory scenarios; no skip path exists;
the rehearsal places no real request; and the tested `A_reachable` is measured by execution rather
than copied from the derivation it is supposed to confirm.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from disclosure_drift.m3 import rehearsal
from disclosure_drift.m3.rehearsal import (
    REHEARSAL_REPORT_SCHEMA_VERSION,
    SCENARIO_IDS,
    RehearsalError,
    RehearsalReport,
    run_rehearsal,
    scenario_titles,
)
from disclosure_drift.m3.request_plan import derive_a_reachable
from disclosure_drift.sec import http_client
from disclosure_drift.sec.calendar_evidence import (
    CALENDAR_EVIDENCE_MANIFEST,
    CalendarEvidenceError,
)
from disclosure_drift.sec.response_policy import MAX_TRANSIENT_RETRIES
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.sec.urls import MAX_REDIRECT_DEPTH


@pytest.fixture(scope="module")
def report(tmp_path_factory: pytest.TempPathFactory) -> RehearsalReport:
    """One full rehearsal, reused across assertions: it drives the real client many times."""
    return run_rehearsal(workspace_root=tmp_path_factory.mktemp("evidence"))


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


# --------------------------------------------------------------------------- #
# One named test per scenario (contract §12; spec §6 pass criterion 1)
# --------------------------------------------------------------------------- #
def _scenario(scenario_id: str, workspace_root: Path) -> None:
    """Run one scenario on its own and fail with the assertions it found untrue.

    Contract §12 requires "one named test per scenario ... none skipped or `xfail`ed". A single
    aggregate assertion over the whole report satisfies neither obligation: it names no scenario,
    so a reader cannot tell from the test list that all twelve exist, and a failure reports one
    collapsed message rather than the scenario that produced it.
    """
    report = run_rehearsal([scenario_id], workspace_root=workspace_root)

    assert tuple(outcome.scenario_id for outcome in report.outcomes) == (scenario_id,)
    outcome = report.outcomes[0]
    assert outcome.passed, f"{scenario_id}: {outcome.detail}"
    assert outcome.title.strip()
    # Every scenario records what it observed. A record with no findings would report that a
    # scenario passed without saying what it saw.
    assert outcome.findings, f"{scenario_id} recorded no observed findings"


def test_a1_all_success_acquisition(tmp_path: Path) -> None:
    _scenario("A1", tmp_path)


def test_a2_retry_then_success(tmp_path: Path) -> None:
    _scenario("A2", tmp_path)


def test_a3_retry_after_usable_and_unusable(tmp_path: Path) -> None:
    _scenario("A3", tmp_path)


def test_a4_cooldown_and_block_page_termination(tmp_path: Path) -> None:
    _scenario("A4", tmp_path)


def test_a5_stop_before_budget_overflow(tmp_path: Path) -> None:
    _scenario("A5", tmp_path)


def test_a6_route_allowlist_and_denylist_enforcement(tmp_path: Path) -> None:
    _scenario("A6", tmp_path)


def test_a7_unknown_field_retention(tmp_path: Path) -> None:
    _scenario("A7", tmp_path)


def test_a8_blocking_schema_drift(tmp_path: Path) -> None:
    _scenario("A8", tmp_path)


def test_a9_byte_identical_duplicate_and_valid_304(tmp_path: Path) -> None:
    _scenario("A9", tmp_path)


def test_a10_changed_body_new_observation_behaviour(tmp_path: Path) -> None:
    _scenario("A10", tmp_path)


def test_a11_raw_store_and_catalog_interruption_recovery(tmp_path: Path) -> None:
    _scenario("A11", tmp_path)


def test_a12_receipt_non_contamination_and_non_vacuous_scanning(tmp_path: Path) -> None:
    _scenario("A12", tmp_path)


def test_there_is_a_named_test_for_every_registered_scenario() -> None:
    """The registry and the named tests above cannot drift apart unnoticed."""
    named = {
        name.split("_", 2)[1].upper()
        for name in globals()
        if name.startswith("test_a") and name.split("_", 2)[1].lstrip("a").isdigit()
    }
    assert named == set(SCENARIO_IDS)


def test_an_unknown_scenario_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RehearsalError, match="A13"):
        run_rehearsal(["A13"], workspace_root=tmp_path)


def test_a_subset_runs_but_does_not_claim_completeness(tmp_path: Path) -> None:
    partial = run_rehearsal(["A1", "A2"], workspace_root=tmp_path)

    assert not partial.complete
    assert tuple(outcome.scenario_id for outcome in partial.outcomes) == ("A1", "A2")


def test_scenarios_run_in_registry_order_regardless_of_request_order(tmp_path: Path) -> None:
    partial = run_rehearsal(["A9", "A2"], workspace_root=tmp_path)

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


# --------------------------------------------------------------------------- #
# Decision 029: every route gets one realizable full-path witness
# --------------------------------------------------------------------------- #
def test_every_registered_route_is_witnessed(report: RehearsalReport) -> None:
    """Decision 029 section 4.1: a zero `U(route)` never waives the independent witness.

    The announcement route plans zero requests against an empty approved operator manifest and so
    contributes zero to any ceiling — and still needs a tested bound, because Gate F section 9.3's
    arithmetic and Gate F section 3.10's evidence obligation are separate requirements.
    """
    assert report.unmeasured_routes == {}
    assert report.a_reachable_fully_tested
    assert set(report.tested_a_reachable) == set(SOURCES)
    assert "sec_edgar_calendar_announcement" in report.tested_a_reachable


def test_the_witness_reproduces_the_six_seven_eleven_shape(report: RehearsalReport) -> None:
    """Decision 029 section 7's table, observed rather than asserted."""
    for source_id in (
        "sec_bulk_submissions",
        "sec_company_tickers",
        "sec_company_tickers_exchange",
        "sec_sic_code_list",
        "sec_edgar_calendar_announcement",
    ):
        assert report.tested_a_reachable[source_id] == 6
    assert report.tested_a_reachable["sec_edgar_filing_calendar"] == 7
    assert report.tested_a_reachable["sec_full_index_company"] == 11


def test_a_path_pinned_route_actively_rejects_an_offered_redirect() -> None:
    """Returning zero hops without exercising the resolver would prove only that nobody asked."""
    witness = rehearsal._measure_full_path("sec_company_tickers")  # noqa: SLF001

    assert witness.defect is None
    assert witness.redirect_offered
    assert witness.accepted_hops == 0
    assert witness.attempts == 6


def test_a_hop_accepting_route_walks_its_whole_redirect_frontier() -> None:
    witness = rehearsal._measure_full_path("sec_full_index_company")  # noqa: SLF001

    assert witness.defect is None
    assert witness.accepted_hops == MAX_REDIRECT_DEPTH
    assert witness.attempts == 11


@pytest.mark.parametrize(
    "source_id",
    [
        "sec_bulk_submissions",
        "sec_company_tickers",
        "sec_company_tickers_exchange",
        "sec_sic_code_list",
        "sec_edgar_calendar_announcement",
    ],
)
def test_every_zero_hop_route_observes_and_refuses_an_actual_redirect(source_id: str) -> None:
    """Decision 029 §7: zero hops must be a refusal the resolver recorded, not a silence.

    Each of these routes has its path pinned, so its `A_reachable` of 6 depends on the redirect
    term being genuinely zero. The witness therefore offers a redirect back to the URL just
    requested and requires the policy layer to record refusing it — an observation neither the
    attempt count nor the hop count can supply on its own.
    """
    if SOURCES[source_id].manifest_resolved:
        with rehearsal._rehearsal_manifest_resolution():  # noqa: SLF001
            witness = rehearsal._measure_full_path(source_id)  # noqa: SLF001
    else:
        witness = rehearsal._measure_full_path(source_id)  # noqa: SLF001

    assert witness.defect is None
    assert witness.redirect_offered
    assert witness.accepted_hops == 0
    assert witness.attempts == 6
    assert "redirect(s) served and observed" in witness.detail


def test_replacing_the_redirect_with_a_success_makes_the_witness_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deletion this witness previously survived (Decision 029 §7).

    The mutilated script keeps every attempt: four retryable responses, the unqualified 429, and a
    sixth response that is a terminal success instead of the redirect. The attempt count is
    therefore still 6 — identical to the honest witness — so any check inferring "a redirect was
    offered" from how many attempts were spent passes here while proving nothing. Only inspecting
    what the transport actually served refuses it.
    """

    def _without_the_redirect(hop_targets: object, source_id: str) -> list[object]:  # noqa: ARG001
        responses = [rehearsal._scripted(503) for _ in range(MAX_TRANSIENT_RETRIES - 1)]  # noqa: SLF001
        responses.append(rehearsal._scripted(429))  # noqa: SLF001
        responses.append(rehearsal._scripted_for(source_id))  # noqa: SLF001
        return responses

    monkeypatch.setattr(rehearsal, "_witness_responses", _without_the_redirect)
    witness = rehearsal._measure_full_path("sec_company_tickers")  # noqa: SLF001

    assert witness.attempts == 6, "the mutilation must not change the attempt count"
    assert not witness.redirect_offered
    assert witness.defect is not None
    assert "assumed rather than observed" in witness.defect


def test_removing_the_cooldown_segment_makes_the_witness_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A witness that still passes with a segment deleted is measuring something else.

    Dropping the unqualified 429 removes the single cooldown continue, so the loop goes terminal on
    the exhausted retry budget and never reaches the redirect frontier at all.
    """

    def _without_cooldown(
        hop_targets: object,  # noqa: ARG001 - the mutilated script ignores the frontier
        source_id: str,  # noqa: ARG001
    ) -> list[object]:
        return [rehearsal._scripted(503) for _ in range(MAX_TRANSIENT_RETRIES + 2)]  # noqa: SLF001

    monkeypatch.setattr(rehearsal, "_witness_responses", _without_cooldown)
    witness = rehearsal._measure_full_path("sec_company_tickers")  # noqa: SLF001

    assert witness.defect is not None
    assert witness.attempts == MAX_TRANSIENT_RETRIES
    assert not witness.redirect_offered


def test_removing_the_retry_segment_makes_the_witness_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without the retryable prefix the cooldown arrives early and the count is not the bound."""

    def _without_retries(hop_targets: object, source_id: str) -> list[object]:  # noqa: ARG001
        return [
            rehearsal._scripted(429),  # noqa: SLF001
            rehearsal._scripted(302, headers={"Location": rehearsal._ECHO_REQUEST_URL}),  # noqa: SLF001
        ]

    monkeypatch.setattr(rehearsal, "_witness_responses", _without_retries)
    witness = rehearsal._measure_full_path("sec_company_tickers")  # noqa: SLF001

    assert witness.attempts == 2
    assert witness.attempts != derive_a_reachable(SOURCES["sec_company_tickers"])


# --------------------------------------------------------------------------- #
# Decision 029: the manifest-resolution fixture is bounded and non-persistent
# --------------------------------------------------------------------------- #
def test_the_manifest_fixture_never_enters_the_source_manifest() -> None:
    """The source-controlled manifest is empty before and after the witness (Decision 011 s8)."""
    assert dict(CALENDAR_EVIDENCE_MANIFEST) == {}
    with rehearsal._rehearsal_manifest_resolution():  # noqa: SLF001
        witness = rehearsal._measure_full_path("sec_edgar_calendar_announcement")  # noqa: SLF001
    assert witness.defect is None
    assert witness.attempts == 6
    assert dict(CALENDAR_EVIDENCE_MANIFEST) == {}


def test_the_manifest_fixture_answers_for_exactly_one_identity() -> None:
    """It widens nothing: every other evidence id still reaches the real, empty resolver."""
    with rehearsal._rehearsal_manifest_resolution():  # noqa: SLF001
        resolver = http_client.require_evidence
        assert resolver(rehearsal._REHEARSAL_ANNOUNCEMENT_EVIDENCE_ID).url  # noqa: SLF001
        with pytest.raises(CalendarEvidenceError):
            resolver("some-other-evidence-id")


def test_the_production_resolver_is_restored_after_an_exception() -> None:
    """A seam left open by a raising witness would outlive the rehearsal."""
    original = http_client.require_evidence

    with pytest.raises(RuntimeError), rehearsal._rehearsal_manifest_resolution():  # noqa: SLF001
        message = "a scenario raised"
        raise RuntimeError(message)

    assert http_client.require_evidence is original


def test_the_fixture_asserts_no_real_date_and_is_not_approved() -> None:
    """If it ever escaped, it could not be mistaken for a reviewed determination."""
    entry = rehearsal._REHEARSAL_ANNOUNCEMENT_ENTRY  # noqa: SLF001

    assert entry.affected_dates == ()
    assert entry.affected_range_start is None
    assert entry.affected_range_end is None
    assert not entry.is_approved
    assert entry.url.startswith("https://www.sec.gov/")


def test_the_fixture_is_absent_from_the_serialized_report(report: RehearsalReport) -> None:
    """It is never serialized into a report, receipt, plan, catalog, or raw object."""
    payload = report.canonical_bytes().decode()

    assert rehearsal._REHEARSAL_ANNOUNCEMENT_EVIDENCE_ID not in payload  # noqa: SLF001
    assert rehearsal._REHEARSAL_ANNOUNCEMENT_URL not in payload  # noqa: SLF001


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


# --------------------------------------------------------------------------- #
# A7 and A8 exercise the real parser and schema-drift path, not a restatement of it
# --------------------------------------------------------------------------- #
def _detail(scenario_id: str, workspace_root: Path) -> tuple[bool, str]:
    outcome = run_rehearsal([scenario_id], workspace_root=workspace_root).outcomes[0]
    return outcome.passed, outcome.detail


def test_a7_fails_when_schema_drift_inspection_goes_blind(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A7 must be sensitive to the production drift path, not merely to the raw bytes.

    Both scenarios once asserted only that `SecClient.fetch` returned the body it was given, so
    they passed with every callable in `sec/parsers/base.py` and `sec/schema_drift.py` replaced by
    a stub. This substitutes a drift inspection that reports nothing and requires A7 to notice.
    """
    from disclosure_drift.sec import schema_drift
    from disclosure_drift.sec.parsers import submissions

    def _blind(*_args: object, **kwargs: object) -> schema_drift.DriftReport:
        return schema_drift.DriftReport(
            source_class=str(kwargs.get("source_class", "")),
            events=(),
            retained_unknown_fields=(),
        )

    monkeypatch.setattr(submissions, "inspect_payload", _blind)
    passed, detail = _detail("A7", tmp_path)

    assert not passed, "A7 passed with schema-drift inspection reporting nothing"
    assert "retained" in detail


def test_a8_fails_when_structural_verdicts_carry_no_reason_code(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A8 must read the codes the accepted parser layer really emits for each structural state."""
    from disclosure_drift.sec.parsers import base

    monkeypatch.setattr(
        base,
        "STRUCTURAL_REASON_BY_STATE",
        dict.fromkeys(base.STRUCTURAL_REASON_BY_STATE, ""),
    )
    passed, detail = _detail("A8", tmp_path)

    assert not passed, "A8 passed with every structural reason code suppressed"
    assert "PARSER_STRUCTURE" in detail


def test_a8_fails_when_an_unusable_count_is_reported_as_trustworthy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The false-zero property is the point of A8: an unknown count must never read as zero."""
    from disclosure_drift.sec.parsers import base

    monkeypatch.setattr(
        base.StructuralObservation, "count_is_trustworthy", property(lambda _self: True)
    )
    passed, detail = _detail("A8", tmp_path)

    assert not passed, "A8 passed with every unusable count reported as believable"
    assert "trustworthy counts" in detail
