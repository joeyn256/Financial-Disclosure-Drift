"""Identifiers, source addressing, reason registry, path policy, and guards."""

from __future__ import annotations

from pathlib import Path

import pytest

from disclosure_drift.paths import (
    DataTree,
    PathPolicyError,
    backup_root_status,
    relative_to_root,
    volume_verdict,
)
from disclosure_drift.reasons import (
    REASON_CODES,
    codes_for_category,
    reason,
    release_blocking_codes,
)
from disclosure_drift.sec.companyfacts_policy import (
    REQUIRED_FACT_PROVENANCE_FIELDS,
    CompanyFactsProhibitedError,
    fact_is_eligible_for_history,
    require_companyfacts_authorization,
    require_frames_prohibited,
)
from disclosure_drift.sec.identifiers import (
    CIK_MAX,
    CIK_PADDED_WIDTH,
    IdentifierError,
    cik_padded,
    normalize_cik,
    parse_accession,
)
from disclosure_drift.sec.sources import (
    APPROVED_SOURCE_PRECEDENCE,
    PROHIBITED_SOURCES,
    accession_index_json_url,
    complete_submission_url,
    master_index_url,
    submissions_json_url,
)

APPLE_CIK = 320193


# --------------------------------------------------------------------------- #
# Identifiers
# --------------------------------------------------------------------------- #
def test_dashed_and_plain_accessions_parse_identically() -> None:
    dashed = parse_accession("0000320193-24-000123")
    plain = parse_accession("000032019324000123")
    assert dashed.plain == plain.plain
    assert dashed.dashed == plain.dashed == "0000320193-24-000123"
    assert dashed.sequence == "000123"
    assert dashed.year_fragment == "24"


def test_submitter_cik_is_not_presented_as_the_registrant() -> None:
    accession = parse_accession("0001234567-24-000001")
    assert accession.submitter_cik_numeric == 1234567
    assert accession.submitter_cik_padded == "0001234567"
    assert not hasattr(accession, "registrant_cik_numeric")


def test_raw_accession_input_is_preserved() -> None:
    assert parse_accession("  0000320193-24-000123 ").raw == "  0000320193-24-000123 "


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "0000320193-2-000123",
        "0000320193-24-00012",
        "000032019324",
        "0000320193_24_000123",
        "abcdefghij-24-000123",
    ],
)
def test_malformed_accessions_are_rejected(value: str) -> None:
    with pytest.raises(IdentifierError):
        parse_accession(value)


@pytest.mark.parametrize("value", [APPLE_CIK, "320193", "0000320193", "CIK0000320193"])
def test_cik_forms_normalize_consistently(value: str | int) -> None:
    numeric, padded = normalize_cik(value)
    assert numeric == APPLE_CIK
    assert padded == "0000320193"
    assert cik_padded(value) == padded


@pytest.mark.parametrize(
    "value",
    [
        "-5",
        "+5",
        " 5 ",
        "5 ",
        " 5",
        "5.0",
        "5e3",
        "1_000",
        "1,000",
        "0x10",
        "",
        "   ",
        "abc",
        "CIK",
        "١٢٣",
    ],
)
def test_non_canonical_cik_strings_are_rejected_not_repaired(value: str) -> None:
    """Signs, whitespace, separators, and non-decimal forms are never stripped."""
    with pytest.raises(IdentifierError, match="malformed CIK"):
        normalize_cik(value)


@pytest.mark.parametrize("value", ["0", "0000000000", 0])
def test_zero_is_not_a_cik(value: str | int) -> None:
    with pytest.raises(IdentifierError, match="outside the valid range"):
        normalize_cik(value)


@pytest.mark.parametrize("value", [True, False])
def test_booleans_are_rejected(value: bool) -> None:
    with pytest.raises(IdentifierError, match="must not be a boolean"):
        normalize_cik(value)


def test_ten_digit_maximum_is_accepted() -> None:
    numeric, padded = normalize_cik("9999999999")
    assert numeric == CIK_MAX == 9_999_999_999
    assert padded == "9999999999"
    assert len(padded) == CIK_PADDED_WIDTH


@pytest.mark.parametrize("value", ["10000000000", "99999999999", 10_000_000_000])
def test_eleven_digit_values_are_rejected(value: str | int) -> None:
    with pytest.raises(IdentifierError):
        normalize_cik(value)


@pytest.mark.parametrize("value", [-5, -1, 0])
def test_non_positive_integers_are_rejected(value: int) -> None:
    with pytest.raises(IdentifierError, match="outside the valid range"):
        normalize_cik(value)


def test_leading_zeroes_are_representation_only() -> None:
    assert normalize_cik("0000000001") == (1, "0000000001")
    assert normalize_cik("1") == (1, "0000000001")
    assert normalize_cik("00000000000000001") == (1, "0000000001")


# --------------------------------------------------------------------------- #
# Source addressing
# --------------------------------------------------------------------------- #
def test_approved_precedence_starts_with_bulk_and_ends_with_aliases() -> None:
    assert APPROVED_SOURCE_PRECEDENCE[0] == "bulk_submissions"
    assert APPROVED_SOURCE_PRECEDENCE[-1] == "ticker_alias"
    assert "frames_api" in PROHIBITED_SOURCES


def test_urls_are_built_from_canonical_sec_hosts() -> None:
    assert submissions_json_url(APPLE_CIK).url.endswith("/submissions/CIK0000320193.json")
    assert master_index_url(2024, 1).url.endswith("/full-index/2024/QTR1/master.idx")
    index = accession_index_json_url(APPLE_CIK, "0000320193-24-000123")
    assert index.url.endswith("/data/320193/000032019324000123/index.json")
    submission = complete_submission_url(APPLE_CIK, "0000320193-24-000123")
    assert submission.url.endswith("0000320193-24-000123.txt")
    assert submission.logical_role == "complete_submission"


@pytest.mark.parametrize(("year", "quarter"), [(2024, 0), (2024, 5), (1900, 1)])
def test_invalid_index_coordinates_are_rejected(year: int, quarter: int) -> None:
    with pytest.raises(ValueError, match="range|quarter"):
        master_index_url(year, quarter)


# --------------------------------------------------------------------------- #
# Reason registry
# --------------------------------------------------------------------------- #
def test_registry_covers_the_required_policy_codes() -> None:
    required = {
        "ELIGIBLE_ORIGINAL_10K",
        "ELIGIBLE_TRANSITION_10KT",
        "SUPPORT_ONLY",
        "AMENDMENT_NON_TARGET",
        "EXCLUDED_ASSET_BACKED_ISSUER",
        "EXCLUDED_REGISTERED_INVESTMENT_COMPANY",
        "EXCLUDED_SHELL_COMPANY",
        "EXCLUDED_BLANK_CHECK_COMPANY",
        "EXCLUDED_UNSUPPORTED_FORM",
        "REVIEW_MULTI_REGISTRANT",
        "REVIEW_UNKNOWN_ISSUER_TYPE",
        "REVIEW_CONFLICTING_SIC",
        "REVIEW_POST_DE_SPAC_TRANSITION",
        "REVIEW_REGISTRANT_CIK_UNRESOLVED",
        "REVIEW_AMENDMENT_PARENT_UNRESOLVED",
        "REVIEW_MISSING_ACCEPTANCE_TIMESTAMP",
        "REVIEW_CORRECTION_CROSSES_COHORT_BOUNDARY",
        "REVIEW_AVAILABILITY_ORDER_INDETERMINATE",
        "RAW_FILE_CHECKSUM_MISMATCH",
        "REMOTE_CONTENT_CHANGED",
        "SEC_BLOCK_PAGE",
        "SEC_SCHEMA_REQUIRED_FIELD_MISSING",
    }
    assert required <= set(REASON_CODES)


def test_every_review_code_requires_manual_review() -> None:
    for code in codes_for_category("review"):
        assert reason(code).requires_manual_review


def test_eligibility_codes_never_block_release() -> None:
    for code in codes_for_category("eligible"):
        assert not reason(code).blocks_release


def test_release_blocking_codes_include_integrity_failures() -> None:
    blocking = set(release_blocking_codes())
    assert "RAW_FILE_CHECKSUM_MISMATCH" in blocking
    assert "REVIEW_AVAILABILITY_ORDER_INDETERMINATE" in blocking


def test_unregistered_codes_are_rejected() -> None:
    with pytest.raises(KeyError, match="unregistered reason code"):
        reason("MADE_UP_CODE")


def test_every_code_cites_a_decision_record() -> None:
    for item in REASON_CODES.values():
        assert item.decision_reference.startswith("Docs/Decisions/decision_")


# --------------------------------------------------------------------------- #
# Path policy
# --------------------------------------------------------------------------- #
def test_data_tree_layout(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    created = tree.ensure_tree()
    assert all(directory.is_dir() for directory in created)
    assert tree.catalog_database.name == "sec_ingestion.sqlite3"
    assert tree.audit == tmp_path / "audit" / "sec"
    assert tree.locks == tmp_path / "locks"


def test_accession_directory_is_accession_addressed(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    directory = tree.accession_directory("0000320193", "000032019324000123")
    assert directory == tree.raw_filings / "0000320193" / "000032019324000123"


@pytest.mark.parametrize(
    ("cik", "accession"),
    [("320193", "000032019324000123"), ("0000320193", "12345"), ("0000320193", "abc")],
)
def test_accession_directory_rejects_malformed_identity(
    tmp_path: Path, cik: str, accession: str
) -> None:
    with pytest.raises(PathPolicyError):
        DataTree.from_root(tmp_path).accession_directory(cik, accession)


def test_only_relative_paths_may_be_persisted(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    assert tree.relative(tree.audit) == "audit/sec"
    with pytest.raises(PathPolicyError, match="not inside the configured root"):
        relative_to_root(Path("/etc/passwd"), tmp_path)


def test_backup_root_is_optional_but_validated(tmp_path: Path) -> None:
    unset = backup_root_status("")
    assert not unset.configured
    with pytest.raises(PathPolicyError, match="not configured"):
        unset.require()

    missing = backup_root_status(str(tmp_path / "absent"))
    assert missing.configured
    with pytest.raises(PathPolicyError, match="does not exist"):
        missing.require()

    present = backup_root_status(str(tmp_path))
    assert present.require() == tmp_path


def test_volume_verdict_reports_shared_devices(tmp_path: Path) -> None:
    verdict = volume_verdict(tmp_path, tmp_path)
    assert not verdict.distinct
    assert "separate volumes" in verdict.detail


# --------------------------------------------------------------------------- #
# CompanyFacts and Frames guards
# --------------------------------------------------------------------------- #
def test_companyfacts_is_disabled_by_default() -> None:
    with pytest.raises(CompanyFactsProhibitedError, match="disabled by default"):
        require_companyfacts_authorization(enabled=False)


def test_companyfacts_requires_a_documented_need_and_approver() -> None:
    with pytest.raises(CompanyFactsProhibitedError, match="documented"):
        require_companyfacts_authorization(enabled=True, approved_by="owner")
    with pytest.raises(CompanyFactsProhibitedError, match="approver"):
        require_companyfacts_authorization(enabled=True, documented_need="unit reconciliation")


def test_documented_and_approved_companyfacts_use_is_permitted() -> None:
    authorization = require_companyfacts_authorization(
        enabled=True,
        documented_need="pilot unit reconciliation",
        approved_by="project owner",
    )
    assert authorization.enabled


def test_frames_api_is_always_prohibited() -> None:
    with pytest.raises(CompanyFactsProhibitedError, match="Frames API is prohibited"):
        require_frames_prohibited()


def test_facts_without_accession_provenance_are_ineligible() -> None:
    eligible, missing = fact_is_eligible_for_history({"concept": "Revenues"})
    assert not eligible
    assert "accession" in missing


def test_fully_provenanced_fact_is_eligible() -> None:
    fact = dict.fromkeys(REQUIRED_FACT_PROVENANCE_FIELDS, "present")
    eligible, missing = fact_is_eligible_for_history(fact)
    assert eligible
    assert missing == ()
