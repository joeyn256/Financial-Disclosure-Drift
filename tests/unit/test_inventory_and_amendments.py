"""Eligibility classification, amendment linkage, and schema-drift policy."""

from __future__ import annotations

from datetime import date

import pytest

from disclosure_drift.errors import SchemaDriftError
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.amendments import (
    AmendmentCandidate,
    AmendmentEvidence,
    link_amendment,
)
from disclosure_drift.sec.inventory import AccessionFacts, IssuerType, classify_accession
from disclosure_drift.sec.schema_drift import inspect_payload

ORIGINAL = "000032019324000001"
AMENDMENT = "000032019324000002"


def facts(**overrides: object) -> AccessionFacts:
    base: dict[str, object] = {
        "accession_plain": ORIGINAL,
        "form_type": "10-K",
        "official_filing_date": date(2024, 2, 15),
        "issuer_type": "operating",
        "registrant_ciks": (320193,),
        "shell_for_accession": False,
    }
    base.update(overrides)
    return AccessionFacts(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #
def test_original_annual_report_is_a_primary_target() -> None:
    result = classify_accession(facts())
    assert result.inventory_role == "primary_target"
    assert result.primary_target_flag
    assert result.eligibility_state == "eligible"
    assert result.temporal_cohort == "primary_test"
    assert result.reason_codes == ("ELIGIBLE_ORIGINAL_10K",)


def test_transition_report_uses_its_own_code() -> None:
    result = classify_accession(facts(form_type="10-KT"))
    assert result.reason_codes[0] == "ELIGIBLE_TRANSITION_10KT"
    assert result.primary_target_flag


def test_amendment_is_never_a_primary_target() -> None:
    result = classify_accession(facts(form_type="10-K/A"))
    assert result.inventory_role == "amendment_non_target"
    assert not result.primary_target_flag
    assert "AMENDMENT_NON_TARGET" in result.reason_codes


def test_2009_filing_is_support_only() -> None:
    result = classify_accession(facts(official_filing_date=date(2009, 3, 2)))
    assert result.inventory_role == "support_only"
    assert not result.primary_target_flag
    assert result.temporal_cohort == "support_2009"
    assert "SUPPORT_ONLY" in result.reason_codes


def test_unsupported_form_is_retained_as_control_evidence() -> None:
    result = classify_accession(facts(form_type="20-F"))
    assert result.inventory_role == "control_evidence"
    assert result.eligibility_state == "excluded"
    assert result.reason_codes == ("EXCLUDED_UNSUPPORTED_FORM",)


@pytest.mark.parametrize(
    ("issuer_type", "expected"),
    [
        ("asset_backed", "EXCLUDED_ASSET_BACKED_ISSUER"),
        ("registered_investment_company", "EXCLUDED_REGISTERED_INVESTMENT_COMPANY"),
        ("shell_or_blank_check", "EXCLUDED_SHELL_COMPANY"),
        ("blank_check", "EXCLUDED_BLANK_CHECK_COMPANY"),
    ],
)
def test_issuer_type_exclusions(issuer_type: IssuerType, expected: str) -> None:
    result = classify_accession(facts(issuer_type=issuer_type))
    assert result.eligibility_state == "excluded"
    assert result.reason_codes == (expected,)


def test_operating_financial_institutions_are_flagged_not_excluded() -> None:
    result = classify_accession(facts(issuer_type="operating_financial_institution"))
    assert result.eligibility_state == "eligible"
    assert result.primary_target_flag


def test_unknown_issuer_type_never_becomes_silently_eligible() -> None:
    result = classify_accession(facts(issuer_type="unknown"))
    assert result.eligibility_state == "review_required"
    assert result.requires_review
    assert not result.primary_target_flag
    assert "REVIEW_UNKNOWN_ISSUER_TYPE" in result.reason_codes


def test_unknown_shell_state_requires_review() -> None:
    result = classify_accession(facts(shell_for_accession=None))
    assert result.eligibility_state == "review_required"
    assert "REVIEW_UNKNOWN_ISSUER_TYPE" in result.reason_codes


def test_shell_exclusion_is_accession_specific() -> None:
    excluded = classify_accession(facts(shell_for_accession=True))
    later = classify_accession(facts(shell_for_accession=False, was_shell_previously=True))
    assert excluded.eligibility_state == "excluded"
    assert later.eligibility_state == "review_required"
    assert "REVIEW_POST_DE_SPAC_TRANSITION" in later.reason_codes


def test_multiple_registrants_are_flagged_without_blocking_eligibility() -> None:
    result = classify_accession(facts(registrant_ciks=(320193, 789019)))
    assert "REVIEW_MULTI_REGISTRANT" in result.reason_codes
    assert result.eligibility_state == "eligible"


def test_unresolved_registrant_blocks_eligibility() -> None:
    result = classify_accession(facts(registrant_ciks=(), registrant_cik_resolved=False))
    assert result.eligibility_state == "review_required"
    assert "REVIEW_REGISTRANT_CIK_UNRESOLVED" in result.reason_codes


def test_conflicting_sic_evidence_requires_review() -> None:
    result = classify_accession(facts(sic_codes_observed=("3571", "6022")))
    assert "REVIEW_CONFLICTING_SIC" in result.reason_codes
    assert result.eligibility_state == "review_required"


def test_missing_filing_date_requires_review() -> None:
    result = classify_accession(facts(official_filing_date=None))
    assert result.temporal_cohort is None
    assert "SEC_SCHEMA_REQUIRED_FIELD_MISSING" in result.reason_codes
    assert result.eligibility_state == "review_required"


def test_xbrl_flag_disagreement_is_a_review_condition() -> None:
    result = classify_accession(facts(xbrl_amendment_flag=True))
    assert result.eligibility_state == "review_required"


def test_every_classification_reason_is_registered() -> None:
    samples = [
        facts(),
        facts(form_type="10-K/A"),
        facts(form_type="20-F"),
        facts(issuer_type="unknown"),
        facts(official_filing_date=date(2009, 3, 2)),
        facts(sic_codes_observed=("1", "2")),
    ]
    for sample in samples:
        for code in classify_accession(sample).reason_codes:
            assert code in REASON_CODES


# --------------------------------------------------------------------------- #
# Amendment linkage
# --------------------------------------------------------------------------- #
def candidate(accession: str, form: str, day: date, period: date | None) -> AmendmentCandidate:
    return AmendmentCandidate(
        accession_plain=accession,
        form_type=form,
        official_filing_date=day,
        period_of_report=period,
        registrant_ciks=(320193,),
    )


def test_explicit_reference_links_to_the_original() -> None:
    link = link_amendment(
        AmendmentEvidence(
            accession_plain=AMENDMENT,
            form_type="10-K/A",
            official_filing_date=date(2024, 5, 1),
            referenced_accession_plain=ORIGINAL,
            candidates=(candidate(ORIGINAL, "10-K", date(2024, 2, 15), date(2023, 12, 30)),),
        )
    )
    assert link.relationship == "amends_original"
    assert link.parent_accession_plain == ORIGINAL
    assert link.is_resolved
    assert not link.is_restatement_claim


def test_amendment_of_an_amendment_is_distinguished() -> None:
    link = link_amendment(
        AmendmentEvidence(
            accession_plain="000032019324000003",
            form_type="10-K/A",
            official_filing_date=date(2024, 6, 1),
            referenced_accession_plain=AMENDMENT,
            candidates=(candidate(AMENDMENT, "10-K/A", date(2024, 5, 1), date(2023, 12, 30)),),
        )
    )
    assert link.relationship == "amends_prior_amendment"


def test_supplement_is_not_a_replacement() -> None:
    link = link_amendment(
        AmendmentEvidence(
            accession_plain=AMENDMENT,
            form_type="10-K/A",
            official_filing_date=date(2024, 5, 1),
            referenced_accession_plain=ORIGINAL,
            declares_supplement_only=True,
            candidates=(candidate(ORIGINAL, "10-K", date(2024, 2, 15), date(2023, 12, 30)),),
        )
    )
    assert link.relationship == "supplements_original"


def test_single_period_match_is_only_a_possible_parent() -> None:
    link = link_amendment(
        AmendmentEvidence(
            accession_plain=AMENDMENT,
            form_type="10-K/A",
            official_filing_date=date(2024, 5, 1),
            period_of_report=date(2023, 12, 30),
            registrant_ciks=(320193,),
            candidates=(candidate(ORIGINAL, "10-K", date(2024, 2, 15), date(2023, 12, 30)),),
        )
    )
    assert link.relationship == "possible_amendment_of"
    assert "REVIEW_AMENDMENT_PARENT_UNRESOLVED" in link.reason_codes


def test_ambiguous_parentage_stays_unresolved() -> None:
    link = link_amendment(
        AmendmentEvidence(
            accession_plain=AMENDMENT,
            form_type="10-K/A",
            official_filing_date=date(2024, 5, 1),
            period_of_report=date(2023, 12, 30),
            registrant_ciks=(320193,),
            candidates=(
                candidate(ORIGINAL, "10-K", date(2024, 2, 15), date(2023, 12, 30)),
                candidate("000032019324000009", "10-K", date(2024, 2, 20), date(2023, 12, 30)),
            ),
        )
    )
    assert link.relationship == "unresolved_amendment"
    assert link.parent_accession_plain is None
    assert not link.is_resolved


def test_amendment_accepted_before_its_alleged_original_is_unresolved() -> None:
    link = link_amendment(
        AmendmentEvidence(
            accession_plain=AMENDMENT,
            form_type="10-K/A",
            official_filing_date=date(2024, 1, 10),
            referenced_accession_plain=ORIGINAL,
            candidates=(candidate(ORIGINAL, "10-K", date(2024, 2, 15), date(2023, 12, 30)),),
        )
    )
    assert link.relationship == "unresolved_amendment"
    assert "filed after the amendment" in link.evidence


def test_no_evidence_yields_unresolved_not_a_guess() -> None:
    link = link_amendment(
        AmendmentEvidence(
            accession_plain=AMENDMENT,
            form_type="10-K/A",
            official_filing_date=date(2024, 5, 1),
        )
    )
    assert link.relationship == "unresolved_amendment"
    assert link.parent_accession_plain is None


def test_xbrl_flag_conflict_adds_a_review_reason() -> None:
    link = link_amendment(
        AmendmentEvidence(
            accession_plain=AMENDMENT,
            form_type="10-K/A",
            official_filing_date=date(2024, 5, 1),
            referenced_accession_plain=ORIGINAL,
            xbrl_amendment_flag=False,
            candidates=(candidate(ORIGINAL, "10-K", date(2024, 2, 15), date(2023, 12, 30)),),
        )
    )
    assert link.relationship == "amends_original"
    assert "REVIEW_AMENDMENT_PARENT_UNRESOLVED" in link.reason_codes


# --------------------------------------------------------------------------- #
# Schema drift
# --------------------------------------------------------------------------- #
REQUIRED = {"cik": str, "filingDate": str, "form": str}


def test_unknown_fields_are_retained_and_logged() -> None:
    report = inspect_payload(
        {"cik": "320193", "filingDate": "2024-02-15", "form": "10-K", "newField": 1},
        source_class="submissions_api",
        required_fields=REQUIRED,
    )
    assert report.retained_unknown_fields == ("newField",)
    assert not report.blocking_events
    assert report.reason_codes == ()
    report.require_usable()


def test_missing_required_field_never_receives_a_default() -> None:
    report = inspect_payload(
        {"cik": "320193", "form": "10-K"},
        source_class="submissions_api",
        required_fields=REQUIRED,
    )
    assert [event.kind for event in report.blocking_events] == ["required_field_missing"]
    assert report.reason_codes == ("SEC_SCHEMA_REQUIRED_FIELD_MISSING",)
    with pytest.raises(SchemaDriftError, match="No default is applied"):
        report.require_usable()


def test_unexpected_null_is_blocking() -> None:
    report = inspect_payload(
        {"cik": "320193", "filingDate": None, "form": "10-K"},
        source_class="submissions_api",
        required_fields=REQUIRED,
    )
    assert [event.kind for event in report.blocking_events] == ["unexpected_null"]


def test_changed_type_is_blocking() -> None:
    report = inspect_payload(
        {"cik": 320193, "filingDate": "2024-02-15", "form": "10-K"},
        source_class="submissions_api",
        required_fields=REQUIRED,
    )
    assert [event.kind for event in report.blocking_events] == ["type_changed"]
    assert "observed int" in report.blocking_events[0].detail


def test_malformed_nested_array_is_blocking() -> None:
    report = inspect_payload(
        {"cik": "320193", "filingDate": "2024-02-15", "form": "10-K", "documents": {}},
        source_class="index_json",
        required_fields=REQUIRED,
        array_fields=["documents"],
    )
    assert [event.kind for event in report.blocking_events] == ["malformed_nested_array"]


def test_renamed_field_appears_as_missing_plus_unknown() -> None:
    report = inspect_payload(
        {"cik": "320193", "dateFiled": "2024-02-15", "form": "10-K"},
        source_class="submissions_api",
        required_fields=REQUIRED,
    )
    kinds = sorted(event.kind for event in report.events)
    assert kinds == ["required_field_missing", "unknown_field_retained"]
