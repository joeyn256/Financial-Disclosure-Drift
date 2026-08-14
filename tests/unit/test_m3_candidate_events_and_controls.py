"""R19 event-flag and R20 boundary-control matrices (Decision 071 §§3-4).

`R19 §4.N` below names row *N* of the predicate table in Decision 071 §3, whose original
`4.1`-`4.12` row labels the accepted record keeps. It is not Decision 071 §4, which is R20.

The negative half of this module is the load-bearing half. R19 and R20 exist because the
first-cut implementation inferred events and control kinds from free text; every
forbidden inference is asserted here to produce **no** flag, so a reintroduced heuristic
fails a test rather than passing silently.
"""

from __future__ import annotations

import itertools
import sqlite3

import pytest

from disclosure_drift.m3 import candidate_controls as controls
from disclosure_drift.m3 import candidate_events as events
from disclosure_drift.m3.candidate_classification import classify_history
from disclosure_drift.storage.sqlite import apply_migrations


def _evidence(**overrides: object) -> events.EntityEventEvidence:
    return events.EntityEventEvidence(**overrides)  # type: ignore[arg-type]


def _observed(**overrides: object) -> frozenset[str]:
    return events.detect_event_flags(_evidence(**overrides)).observed


# ==========================================================================
# R19 negative matrix -- every forbidden inference produces no flag
# ==========================================================================


@pytest.mark.parametrize(
    "value",
    [
        "Formerly Inactive Holdings Inc",
        "Inactive Minerals Corporation",
        "INACTIVE-LOOKING ENTERPRISES",
        "not inactive",
    ],
)
def test_a_name_like_status_string_never_creates_inactive(value: str) -> None:
    """R19 §4.1: no substring, no regex, no descriptive-text interpretation."""
    assert "inactive" not in _observed(status_values=(value,))


@pytest.mark.parametrize(
    "value", ["Acquired Brands Group", "Acquisition Corp", "was acquired in 2019"]
)
def test_a_name_like_string_never_creates_acquired(value: str) -> None:
    assert "acquired" not in _observed(status_values=(value,))


def test_absence_of_a_ticker_never_creates_delisted() -> None:
    """R19 §4.3: the company-ticker sources are alias sources, not a universe."""
    assert "delisted" not in _observed(status_values=())
    assert "delisted" not in _observed(status_values=("operating",))


@pytest.mark.parametrize("value", ["Bankruptcy Advisors Inc", "failed merger", "bankrupt-ish"])
def test_prose_never_creates_bankrupt_or_failed(value: str) -> None:
    assert "bankrupt_or_failed" not in _observed(status_values=(value,))


def test_generic_lineage_never_creates_a_reverse_merger_flag() -> None:
    """R19 §4.6: a predecessor/successor edge is not a de-SPAC proxy."""
    observed = _observed(lineage_evidence_kinds=frozenset({"company_name", "ticker"}))
    assert "reverse_merger_or_de_spac_review" not in observed
    assert "successor_or_predecessor_lineage" in observed


def test_ticker_reuse_alone_never_creates_succession_lineage() -> None:
    """R19 §4.5 names ticker reuse among the forbidden inferences."""
    assert "successor_or_predecessor_lineage" not in _observed(
        lineage_evidence_kinds=frozenset({"ticker"})
    )


def test_an_ordinary_resolved_amendment_never_creates_unusual_history() -> None:
    """R19 §4.11: only a non-ordinary lineage diagnostic establishes it."""
    assert "unusual_amendment_history" not in _observed(non_ordinary_amendment_lineage=False)
    assert "unusual_amendment_history" in _observed(non_ordinary_amendment_lineage=True)


def test_former_name_history_never_creates_an_identity_conflict() -> None:
    """R19 §4.12: a valid former-name transition is not a conflict."""
    observed = _observed(winning_provisional_former_name=True)
    assert "material_source_or_identity_conflict" not in observed
    assert "company_name_or_ticker_transition" in observed


def test_a_ticker_only_identity_claim_does_not_contribute() -> None:
    """R19 §4.9: M3.3 is name-only."""
    assert "company_name_or_ticker_transition" not in _observed(
        winning_provisional_former_name=False
    )


# ==========================================================================
# R19 positive matrix -- exact canonical evidence, and nothing looser
# ==========================================================================


@pytest.mark.parametrize("flag", sorted(events.CANONICAL_STATUS_TOKENS))
def test_the_exact_canonical_status_token_is_observed(flag: str) -> None:
    token = events.CANONICAL_STATUS_TOKENS[flag]
    assert flag in _observed(status_values=(token,))
    assert flag in _observed(status_values=(f"  {token.upper()}  ",))


@pytest.mark.parametrize("form", sorted(events.TRANSITION_REPORT_FORMS))
def test_a_transition_report_is_observed_by_exact_form(form: str) -> None:
    observed = _observed(eligible_forms=(form,))
    assert "transition_report_filed" in observed
    assert "fiscal_year_end_change" in observed


def test_an_ordinary_annual_form_is_not_a_transition_report() -> None:
    assert "transition_report_filed" not in _observed(eligible_forms=("10-K", "10-K/A"))


def test_fiscal_year_end_change_branch_b_uses_the_accepted_circular_rule() -> None:
    """R19 §4.7: circular month/day distance greater than the accepted tolerance."""
    changed = _observed(
        eligible_forms=("10-K", "10-K"),
        original_annual_report_dates=("2019-12-31", "2020-09-30"),
    )
    unchanged = _observed(
        eligible_forms=("10-K", "10-K"),
        original_annual_report_dates=("2019-12-31", "2020-12-28"),
    )
    assert "fiscal_year_end_change" in changed
    assert "fiscal_year_end_change" not in unchanged


def test_the_year_boundary_is_a_small_circular_distance() -> None:
    assert "fiscal_year_end_change" not in _observed(
        eligible_forms=("10-K", "10-K"),
        original_annual_report_dates=("2019-12-30", "2021-01-02"),
    )


@pytest.mark.parametrize(
    "dates", [("2019-12-31", None), (None, "2020-12-31"), ("bad", "2020-12-31")]
)
def test_an_unestablished_report_date_is_unresolved_not_no_change(
    dates: tuple[str | None, str | None],
) -> None:
    """R19 §4.7: never guessed, and never silently 'no change'."""
    detection = events.detect_event_flags(
        _evidence(eligible_forms=("10-K", "10-K"), original_annual_report_dates=dates)
    )
    assert "fiscal_year_end_change" not in detection.observed
    assert detection.unresolved == ("fiscal_year_end_change",)


def test_multi_registrant_and_material_conflict_are_passed_through_explicitly() -> None:
    assert "multi_registrant_annual_filing" in _observed(multi_registrant_annual_filing=True)
    assert "material_source_or_identity_conflict" in _observed(material_conflict=True)


def test_an_explicit_reverse_merger_edge_kind_would_be_observed() -> None:
    """The predicate is real, not unreachable-by-construction."""
    for kind in sorted(events.REVERSE_MERGER_EVIDENCE_KINDS):
        assert "reverse_merger_or_de_spac_review" in _observed(
            lineage_evidence_kinds=frozenset({kind})
        )


def test_every_registered_flag_is_reachable_by_some_predicate() -> None:
    """No flag is silently dead: each one has an evidence shape that observes it."""
    shapes: dict[str, dict[str, object]] = {
        **{
            flag: {"status_values": (token,)}
            for flag, token in events.CANONICAL_STATUS_TOKENS.items()
        },
        "successor_or_predecessor_lineage": {"lineage_evidence_kinds": frozenset({"company_name"})},
        "reverse_merger_or_de_spac_review": {
            "lineage_evidence_kinds": frozenset({"reverse_merger"})
        },
        "fiscal_year_end_change": {
            "eligible_forms": ("10-K", "10-K"),
            "original_annual_report_dates": ("2019-12-31", "2020-06-30"),
        },
        "transition_report_filed": {"eligible_forms": ("10-KT",)},
        "company_name_or_ticker_transition": {"winning_provisional_former_name": True},
        "multi_registrant_annual_filing": {"multi_registrant_annual_filing": True},
        "unusual_amendment_history": {"non_ordinary_amendment_lineage": True},
        "material_source_or_identity_conflict": {"material_conflict": True},
    }
    assert sorted(shapes) == sorted(events.EVENT_FLAGS)
    for flag, shape in shapes.items():
        assert flag in _observed(**shape), f"{flag} is unreachable"


# ==========================================================================
# Decision 071 §3.1 -- the history stratum
# ==========================================================================


def test_history_is_eventful_on_any_single_observed_flag() -> None:
    detection = events.detect_event_flags(_evidence(eligible_forms=("10-KT",)))
    assert classify_history(
        detection, eligible_original_annual_reports=1, evidence_available=True
    ) == ("eventful", "provisional")


def test_history_is_stable_only_with_no_flag_and_enough_originals() -> None:
    detection = events.detect_event_flags(_evidence())
    assert classify_history(
        detection, eligible_original_annual_reports=4, evidence_available=True
    ) == ("stable", "provisional")
    assert classify_history(
        detection, eligible_original_annual_reports=3, evidence_available=True
    ) == (None, "review_required")


def test_an_unresolved_required_fact_never_becomes_no_event() -> None:
    detection = events.detect_event_flags(
        _evidence(
            eligible_forms=("10-K", "10-K"), original_annual_report_dates=("2019-12-31", None)
        )
    )
    assert classify_history(
        detection, eligible_original_annual_reports=9, evidence_available=True
    ) == (None, "review_required")


def test_history_is_unavailable_without_any_entity_evidence() -> None:
    detection = events.detect_event_flags(_evidence())
    assert classify_history(
        detection, eligible_original_annual_reports=9, evidence_available=False
    ) == (None, "unavailable")


# ==========================================================================
# R20 -- the four control predicates
# ==========================================================================


def _control(**overrides: object) -> controls.ControlClassification:
    return controls.classify_control_kind(controls.ControlEvidence(**overrides))  # type: ignore[arg-type]


@pytest.mark.parametrize("sic", sorted(controls.RIC_ETF_SIC_CODES))
def test_the_ric_etf_predicate_is_the_accepted_sic_set(sic: str) -> None:
    verdict = _control(sic_code=sic, sic_resolved=True)
    assert verdict.control_kind == "registered_investment_company_or_etf"
    assert verdict.is_control


def test_the_asset_backed_predicate_is_an_exact_form_10_d() -> None:
    assert _control(submission_forms=frozenset({"10-D"})).control_kind == "asset_backed_issuer"
    assert _control(submission_forms=frozenset({"10-D/A"})).control_kind is None
    assert _control(submission_forms=frozenset({"10-K", "8-K"})).control_kind is None


@pytest.mark.parametrize("sic", sorted(controls.SHELL_BLANK_CHECK_SIC_CODES))
def test_the_shell_predicate_is_the_accepted_sic_set(sic: str) -> None:
    assert _control(sic_code=sic, sic_resolved=True).control_kind == "shell_or_blank_check_issuer"


@pytest.mark.parametrize("form", sorted(controls.FPI_ANNUAL_REPORT_FORMS))
def test_an_original_foreign_annual_report_satisfies_the_fpi_predicate(form: str) -> None:
    forms = controls.original_forms({form})
    assert _control(submission_forms=forms).control_kind == "foreign_private_issuer"


@pytest.mark.parametrize("form", ["20-F/A", "40-F/A"])
def test_an_amendment_alone_never_satisfies_the_fpi_predicate(form: str) -> None:
    """R20 (Decision 071 §4): do not count only an amendment."""
    forms = controls.original_forms({form})
    assert _control(submission_forms=forms).control_kind is None


def test_zero_predicates_is_not_a_boundary_control() -> None:
    verdict = _control(sic_code="3571", sic_resolved=True, submission_forms=frozenset({"10-K"}))
    assert verdict.status == "not_a_control"
    assert verdict.control_kind is None


@pytest.mark.parametrize(
    ("evidence", "expected"),
    [
        (
            {"sic_code": "6726", "sic_resolved": True, "submission_forms": frozenset({"10-D"})},
            ("asset_backed_issuer", "registered_investment_company_or_etf"),
        ),
        (
            {"sic_code": "6726", "sic_resolved": True, "submission_forms": frozenset({"20-F"})},
            ("foreign_private_issuer", "registered_investment_company_or_etf"),
        ),
        (
            {"sic_code": "6770", "sic_resolved": True, "submission_forms": frozenset({"10-D"})},
            ("asset_backed_issuer", "shell_or_blank_check_issuer"),
        ),
        (
            {"sic_code": "6770", "sic_resolved": True, "submission_forms": frozenset({"40-F"})},
            ("foreign_private_issuer", "shell_or_blank_check_issuer"),
        ),
        (
            {"submission_forms": frozenset({"10-D", "20-F"})},
            ("asset_backed_issuer", "foreign_private_issuer"),
        ),
    ],
)
def test_every_reachable_overlap_is_conflicting_and_assigns_no_kind(
    evidence: dict[str, object], expected: tuple[str, ...]
) -> None:
    """Decision 071 §4.1: no precedence, so an overlap resolves to neither kind."""
    verdict = _control(**evidence)
    assert verdict.status == "conflicting"
    assert verdict.control_kind is None
    assert tuple(sorted(verdict.satisfied)) == tuple(sorted(expected))


def test_the_two_sic_predicates_cannot_both_hold() -> None:
    """The sixth pair of the overlap matrix is structurally unreachable."""
    assert not controls.RIC_ETF_SIC_CODES & controls.SHELL_BLANK_CHECK_SIC_CODES


def test_a_triple_overlap_is_also_conflicting() -> None:
    verdict = _control(
        sic_code="6726", sic_resolved=True, submission_forms=frozenset({"10-D", "20-F"})
    )
    assert verdict.status == "conflicting"
    assert len(verdict.satisfied) == 3


def test_an_unresolved_or_conflicting_sic_supports_no_sic_predicate() -> None:
    """R20 (Decision 071 §4): missing, conflicting, or review-required SIC assigns nothing."""
    assert _control(sic_code="6726", sic_resolved=False).status == "not_a_control"
    assert _control(sic_code=None, sic_resolved=True).status == "not_a_control"


def test_control_evidence_cannot_carry_entity_type_or_a_name() -> None:
    """R20 (Decision 071 §4): ``entityType`` is not used at all, nor is a company name."""
    fields = set(controls.ControlEvidence.__dataclass_fields__)
    assert fields == {"sic_code", "sic_resolved", "submission_forms"}


def test_the_verdict_is_independent_of_form_input_order() -> None:
    forms = ["10-D", "20-F", "10-K"]
    verdicts = {
        _control(submission_forms=frozenset(order)).status
        for order in itertools.permutations(forms)
    }
    assert verdicts == {"conflicting"}


def test_the_four_kinds_are_exactly_the_persisted_vocabulary() -> None:
    """Migration ``0009``'s CHECK governs the stored contract, so R20 matches it."""
    connection = _schema()
    try:
        sql = str(
            connection.execute(
                "SELECT sql FROM sqlite_master WHERE name = 'pilot_candidate_entities'"
            ).fetchone()[0]
        )
    finally:
        connection.close()
    for kind in controls.BOUNDARY_CONTROL_KINDS:
        assert f"'{kind}'" in sql


# ==========================================================================
# IN-5 -- the mechanical 135-column recount
# ==========================================================================

_CANDIDATE_TABLE_COUNTS: dict[str, int] = {
    "pilot_candidate_snapshots": 28,
    "pilot_candidate_entities": 26,
    "pilot_candidate_accessions": 35,
    "pilot_candidate_accession_registrants": 8,
    "pilot_candidate_entity_evidence": 13,
    "pilot_candidate_accession_evidence": 13,
    "pilot_candidate_entity_reasons": 6,
    "pilot_candidate_accession_reasons": 6,
}


def _schema() -> sqlite3.Connection:
    """An in-memory catalog carrying the applied migration chain."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    apply_migrations(connection)
    return connection


def test_the_or_2_accounting_is_derived_from_the_applied_schema() -> None:
    """IN-5: derived per table from ``PRAGMA table_info``, never asserted as a literal."""
    connection = _schema()
    try:
        derived = {
            table: len(connection.execute(f"PRAGMA table_info({table})").fetchall())
            for table in _CANDIDATE_TABLE_COUNTS
        }
    finally:
        connection.close()
    assert derived == _CANDIDATE_TABLE_COUNTS
    assert sum(derived.values()) == 135
