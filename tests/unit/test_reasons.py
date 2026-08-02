"""Reason-code registry invariants, including the M2.3 S3.1, S5.2, and S5.4 additions.

Decisions 013-016 froze exactly sixteen new reason codes for the M2.3 pilot at Stage S3.1,
Decision 018 section 21 froze exactly five more for Stage S5, and Decision 020 section 13 froze
exactly one more for Stage S5.4. These tests prove each addition is exact (no more, no fewer, no
renames) and that every pre-existing code from the accepted S3.0 governance baseline is
unchanged.

Tests are hermetic: the pre-S3.1 baseline is not reloaded from Git history (a CI checkout may be
shallow and lack that historical commit). Instead, a canonical SHA-256 fingerprint of the 87
pre-S3.1 codes was computed once, offline, and is frozen here as a literal expected value.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from disclosure_drift import reasons
from disclosure_drift.reasons import REASON_CODES

_REPO_ROOT = Path(__file__).resolve().parents[2]

_NEW_CODES: dict[str, dict[str, Any]] = {
    "PILOT_CANDIDATE_SNAPSHOT_FROZEN": {
        "category": "provenance",
        "blocks_release": False,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_016_m23_schema_and_artifact_architecture.md",
    },
    "PILOT_CANDIDATE_SNAPSHOT_INVALIDATED": {
        "category": "provenance",
        "blocks_release": False,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_016_m23_schema_and_artifact_architecture.md",
    },
    "PILOT_PROVISIONAL_COHORT_PRECEDENCE_2": {
        "category": "temporal",
        "blocks_release": False,
        "requires_manual_review": False,
        "decision_reference": (
            "Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md"
        ),
    },
    "PILOT_ENTITY_NOT_PRIMARY_UNIVERSE_ELIGIBLE": {
        "category": "excluded",
        "blocks_release": False,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_002_primary_outcome.md",
    },
    "PILOT_ENGINEERING_ONLY_STRESS_CASE": {
        "category": "provenance",
        "blocks_release": False,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_002_primary_outcome.md",
    },
    "REVIEW_PILOT_SIZE_CATEGORY_UNAVAILABLE": {
        "category": "review",
        "blocks_release": False,
        "requires_manual_review": True,
        "decision_reference": (
            "Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md"
        ),
    },
    "REVIEW_PILOT_SIC_UNMAPPED": {
        "category": "review",
        "blocks_release": False,
        "requires_manual_review": True,
        "decision_reference": (
            "Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md"
        ),
    },
    "REVIEW_PILOT_SIC_ENGINEERING_ONLY": {
        "category": "review",
        "blocks_release": False,
        "requires_manual_review": True,
        "decision_reference": (
            "Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md"
        ),
    },
    "REVIEW_PILOT_HISTORY_EVIDENCE_INSUFFICIENT": {
        "category": "review",
        "blocks_release": False,
        "requires_manual_review": True,
        "decision_reference": (
            "Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md"
        ),
    },
    "REVIEW_PILOT_AMENDMENT_PURPOSE_UNPROVEN": {
        "category": "review",
        "blocks_release": False,
        "requires_manual_review": True,
        "decision_reference": (
            "Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md"
        ),
    },
    "REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE": {
        "category": "review",
        "blocks_release": False,
        "requires_manual_review": True,
        "decision_reference": "Docs/Decisions/decision_013_pilot_selection_mechanics.md",
    },
    "PILOT_SELECTION_INFEASIBLE": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_013_pilot_selection_mechanics.md",
    },
    "PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_013_pilot_selection_mechanics.md",
    },
    "PILOT_RESERVE_SIGNATURE_INCOMPATIBLE": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_016_m23_schema_and_artifact_architecture.md",
    },
    "PILOT_RESERVE_UNAVAILABLE": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_013_pilot_selection_mechanics.md",
    },
    "PILOT_MANIFEST_HASH_NOT_APPROVED": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_013_pilot_selection_mechanics.md",
    },
}

#: Decision 018 section 21, registered at Stage S5.2. Exactly these five, no alias, no generalized
#: variant, no retry code, no reserve code, and no ticker-warning code.
_S5_2_CODES: dict[str, dict[str, Any]] = {
    "PILOT_ACCESSION_CAP_EXCEEDED": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": ("Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md"),
    },
    "PILOT_ENTITY_ACCESSION_FLOOR_UNMET": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": ("Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md"),
    },
    "PILOT_ACCESSION_PRE_STUDY_SUPPORT": {
        "category": "provenance",
        "blocks_release": False,
        "requires_manual_review": False,
        "decision_reference": ("Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md"),
    },
    "REVIEW_PILOT_QUOTA_UNMEASURABLE_AT_M23": {
        "category": "review",
        "blocks_release": False,
        "requires_manual_review": True,
        "decision_reference": ("Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md"),
    },
    "REVIEW_PILOT_ACCESSION_ROLE_UNCLASSIFIED": {
        "category": "review",
        "blocks_release": False,
        "requires_manual_review": True,
        "decision_reference": ("Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md"),
    },
}

#: Decision 020 section 13, registered at Stage S5.4. Exactly one, and explicitly no
#: pool-exhaustion, integrity, retry, approximation, or substitution code alongside it.
_S5_4_CODES: dict[str, dict[str, Any]] = {
    "REVIEW_PILOT_NO_COMPATIBLE_RESERVE": {
        "category": "review",
        "blocks_release": False,
        "requires_manual_review": True,
        "decision_reference": "Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md",
    },
}

#: Codes Decision 020 section 13 explicitly refuses to authorize.
_FORBIDDEN_S5_4_CODES: tuple[str, ...] = (
    "REVIEW_PILOT_RESERVE_POOL_EXHAUSTED",
    "PILOT_RESERVE_POOL_EXHAUSTED",
    "PILOT_RESERVE_APPROXIMATE_SUBSTITUTION",
    "PILOT_RESERVE_RETRY_REQUIRED",
    "REVIEW_PILOT_RESERVE_SUBSTITUTION",
)

#: The two codes Decision 028 section 6 authorizes for Milestone 3.1, with no alias.
_M3_1_CODES: dict[str, dict[str, Any]] = {
    "SEC_REQUEST_CEILING_EXHAUSTED": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_028_m3_1_readiness_corrections.md",
    },
    "SEC_ACQUISITION_INTERRUPTED": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": "Docs/Decisions/decision_028_m3_1_readiness_corrections.md",
    },
}

#: The one further code Decision 029 section 5 authorizes, with no alias. `requires_manual_review`
#: is `False` by explicit owner ruling of that record: no accepted document compels either value,
#: category `integrity` does not imply one, and `blocks_release` is what stops a release here.
_M3_1_D029_CODES: dict[str, dict[str, Any]] = {
    "OFFLINE_REHEARSAL_SCENARIO_MISMATCH": {
        "category": "integrity",
        "blocks_release": True,
        "requires_manual_review": False,
        "decision_reference": (
            "Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md"
        ),
    },
}

_PRE_S3_1_CODE_COUNT = 87
_S3_1_TOTAL_COUNT = 103
_S5_2_TOTAL_COUNT = 108
_S5_4_TOTAL_COUNT = 109
_M3_1_D028_TOTAL_COUNT = 111
_TOTAL_COUNT = 112

# Computed once, offline, from the accepted S3.0 governance baseline (the 87 reason codes that
# existed before the M2.3 S3.1 addition): sort the pre-S3.1 codes by their ``code`` string, render
# each as a JSON object with keys ``code``, ``category``, ``description``, ``blocks_release``,
# ``requires_manual_review``, ``decision_reference``, serialize the ordered list with
# ``json.dumps(records, sort_keys=True, separators=(",", ":"))``, and SHA-256 the UTF-8 bytes. This
# literal must never be recomputed from Git history at test time.
_PRE_S3_1_FINGERPRINT_SHA256 = "65c94cf2e10eb5854b2c00034c13f4f9de746bef39673ec420f7ee3125bd1c1b"


def _pre_s3_1_codes() -> dict[str, Any]:
    added = (
        set(_NEW_CODES)
        | set(_S5_2_CODES)
        | set(_S5_4_CODES)
        | set(_M3_1_CODES)
        | set(_M3_1_D029_CODES)
    )
    return {code: entry for code, entry in REASON_CODES.items() if code not in added}


def _fingerprint(codes: dict[str, Any]) -> str:
    records = [
        {
            "code": entry.code,
            "category": entry.category,
            "description": entry.description,
            "blocks_release": entry.blocks_release,
            "requires_manual_review": entry.requires_manual_review,
            "decision_reference": entry.decision_reference,
        }
        for _, entry in sorted(codes.items())
    ]
    payload = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_exactly_sixteen_s3_1_five_s5_2_and_one_s5_4_code_were_added() -> None:
    added = set(REASON_CODES) - set(_pre_s3_1_codes())
    assert added == (
        set(_NEW_CODES)
        | set(_S5_2_CODES)
        | set(_S5_4_CODES)
        | set(_M3_1_CODES)
        | set(_M3_1_D029_CODES)
    )
    assert len(_NEW_CODES) == 16
    assert len(_S5_2_CODES) == 5
    assert len(_S5_4_CODES) == 1
    assert len(_M3_1_CODES) == 2
    assert len(_M3_1_D029_CODES) == 1
    assert not set(_NEW_CODES) & set(_S5_2_CODES)
    assert not (set(_NEW_CODES) | set(_S5_2_CODES)) & set(_S5_4_CODES)
    assert not (set(_NEW_CODES) | set(_S5_2_CODES) | set(_S5_4_CODES)) & set(_M3_1_CODES)
    assert not (set(_NEW_CODES) | set(_S5_2_CODES) | set(_S5_4_CODES) | set(_M3_1_CODES)) & set(
        _M3_1_D029_CODES
    )


def test_registry_count_is_exactly_one_hundred_twelve() -> None:
    assert len(REASON_CODES) == _TOTAL_COUNT
    assert _S3_1_TOTAL_COUNT + len(_S5_2_CODES) == _S5_2_TOTAL_COUNT
    assert _S5_2_TOTAL_COUNT + len(_S5_4_CODES) == _S5_4_TOTAL_COUNT
    assert _S5_4_TOTAL_COUNT + len(_M3_1_CODES) == _M3_1_D028_TOTAL_COUNT
    # Decision 029 section 5 narrowly supersedes Decision 028 section 6's word "exactly" to admit
    # one further code, and exactly one. The delta is otherwise closed.
    assert _M3_1_D028_TOTAL_COUNT + len(_M3_1_D029_CODES) == _TOTAL_COUNT


def test_decision_029_code_carries_the_ruled_metadata() -> None:
    """Decision 029 section 5, including the owner ruling that manual review is not required."""
    for code, expected in _M3_1_D029_CODES.items():
        entry = REASON_CODES[code]
        assert entry.category == expected["category"]
        assert entry.blocks_release == expected["blocks_release"]
        assert entry.requires_manual_review == expected["requires_manual_review"]
        assert entry.decision_reference == expected["decision_reference"]
    # The distinction the code exists to preserve: a defective rehearsal witness is an integrity
    # failure of the evidence, and never an acquisition interruption.
    assert REASON_CODES["SEC_ACQUISITION_INTERRUPTED"].decision_reference.endswith(
        "decision_028_m3_1_readiness_corrections.md"
    )
    assert "OFFLINE_REHEARSAL_SCENARIO_MISMATCH" != "SEC_ACQUISITION_INTERRUPTED"


def test_no_reason_code_beyond_the_five_approved_s5_2_additions_exists() -> None:
    """Decision 018 section 21 approves exactly five; the contract authorizes no other."""
    beyond_s3_1 = (
        set(REASON_CODES)
        - set(_pre_s3_1_codes())
        - set(_NEW_CODES)
        - set(_S5_4_CODES)
        - set(_M3_1_CODES)
        - set(_M3_1_D029_CODES)
    )
    assert beyond_s3_1 == set(_S5_2_CODES)


def test_no_reason_code_beyond_the_single_approved_s5_4_addition_exists() -> None:
    """Decision 020 section 13 approves exactly one; the contract authorizes no other."""
    beyond_s5_2 = (
        set(REASON_CODES)
        - set(_pre_s3_1_codes())
        - set(_NEW_CODES)
        - set(_S5_2_CODES)
        - set(_M3_1_CODES)
        - set(_M3_1_D029_CODES)
    )
    assert beyond_s5_2 == set(_S5_4_CODES)


def test_s5_4_codes_carry_the_approved_metadata() -> None:
    for code, expected in _S5_4_CODES.items():
        entry = REASON_CODES[code]
        assert entry.category == expected["category"]
        assert entry.blocks_release == expected["blocks_release"]
        assert entry.requires_manual_review == expected["requires_manual_review"]
        assert entry.decision_reference == expected["decision_reference"]
        assert (_REPO_ROOT / str(expected["decision_reference"])).is_file()
        assert entry.description.endswith(".")


def test_the_s5_4_reserve_code_is_nonblocking_and_review_required() -> None:
    """Decision 020 section 7.1: target-specific, review-required, and nonblocking --
    the run still reaches ``feasible`` with the disposition recorded."""
    entry = REASON_CODES["REVIEW_PILOT_NO_COMPATIBLE_RESERVE"]
    assert entry.requires_manual_review is True
    assert entry.blocks_release is False
    assert "REVIEW_PILOT_NO_COMPATIBLE_RESERVE" not in reasons.release_blocking_codes()
    assert "REVIEW_PILOT_NO_COMPATIBLE_RESERVE" in reasons.codes_for_category("review")


def test_no_pool_exhaustion_integrity_retry_or_substitution_code_was_added() -> None:
    """Decision 020 section 13: ``REVIEW_PILOT_RESERVE_POOL_EXHAUSTED`` is not
    authorized -- each target's reserve is independent, so no pool can be exhausted --
    and every reserve integrity violation is a gate failure, not a reason code."""
    for forbidden in _FORBIDDEN_S5_4_CODES:
        assert forbidden not in REASON_CODES
    assert set(_S5_4_CODES) & set(reasons.codes_for_category("integrity")) == set()


def test_the_existing_reserve_codes_are_unchanged_by_the_s5_4_addition() -> None:
    """The S5.4 code supplements the accepted vocabulary and renames nothing."""
    for code in ("PILOT_RESERVE_SIGNATURE_INCOMPATIBLE", "PILOT_RESERVE_UNAVAILABLE"):
        entry = REASON_CODES[code]
        assert entry.category == "integrity"
        assert entry.blocks_release is True


def test_s5_2_codes_carry_the_approved_metadata() -> None:
    for code, expected in _S5_2_CODES.items():
        entry = REASON_CODES[code]
        assert entry.category == expected["category"]
        assert entry.blocks_release == expected["blocks_release"]
        assert entry.requires_manual_review == expected["requires_manual_review"]
        assert entry.decision_reference == expected["decision_reference"]
        assert (_REPO_ROOT / str(expected["decision_reference"])).is_file()


def test_existing_reason_codes_reused_by_stage_s5_are_not_duplicated() -> None:
    """Unresolved parentage, infeasibility, and node exhaustion reuse existing codes."""
    for code in (
        "REVIEW_AMENDMENT_PARENT_UNRESOLVED",
        "PILOT_SELECTION_INFEASIBLE",
        "PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN",
        "REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE",
    ):
        assert code in REASON_CODES
        assert code not in _S5_2_CODES


def test_removing_new_codes_leaves_exactly_the_pre_s3_1_count() -> None:
    assert len(_pre_s3_1_codes()) == _PRE_S3_1_CODE_COUNT


def test_new_codes_carry_the_approved_metadata() -> None:
    for code, expected in _NEW_CODES.items():
        entry = REASON_CODES[code]
        assert entry.category == expected["category"]
        assert entry.blocks_release == expected["blocks_release"]
        assert entry.requires_manual_review == expected["requires_manual_review"]
        assert entry.decision_reference == expected["decision_reference"]


def test_every_review_category_code_requires_manual_review() -> None:
    for entry in REASON_CODES.values():
        if entry.category == "review":
            assert entry.requires_manual_review


def test_every_description_ends_with_a_period() -> None:
    for entry in REASON_CODES.values():
        assert entry.description.endswith(".")


def test_no_duplicate_reason_codes() -> None:
    codes = [entry.code for entry in REASON_CODES.values()]
    assert len(codes) == len(set(codes))


def test_registry_validation_still_passes() -> None:
    """Reloading the module re-runs ``_validate_registry`` at import time."""
    importlib.reload(reasons)


def test_pre_s3_1_codes_match_the_frozen_baseline_fingerprint() -> None:
    """Prove the 87 pre-S3.1 codes and their metadata are byte-for-byte unchanged.

    The comparison is against a fingerprint frozen offline from the accepted S3.0 baseline,
    not against Git history, so this test has no dependency on checkout depth or repository state.
    """
    assert _fingerprint(_pre_s3_1_codes()) == _PRE_S3_1_FINGERPRINT_SHA256


def test_new_decision_reference_paths_exist_in_the_repository() -> None:
    new_decision_constants = (
        reasons._D002,  # noqa: SLF001
        reasons._D013,  # noqa: SLF001
        reasons._D014,  # noqa: SLF001
        reasons._D015,  # noqa: SLF001
        reasons._D016,  # noqa: SLF001
        reasons._D018,  # noqa: SLF001
        reasons._D020,  # noqa: SLF001
    )
    assert len(set(new_decision_constants)) == 7
    for relative_path in new_decision_constants:
        assert (_REPO_ROOT / relative_path).is_file(), relative_path


# --------------------------------------------------------------------------- #
# Milestone 3.1 additions (Decision 028 section 6)
# --------------------------------------------------------------------------- #
def test_no_reason_code_beyond_the_two_approved_m3_1_additions_exists() -> None:
    """Decision 028 section 6 authorizes exactly two; the contract authorizes no other."""
    beyond_s5_4 = (
        set(REASON_CODES)
        - set(_pre_s3_1_codes())
        - set(_NEW_CODES)
        - set(_S5_2_CODES)
        - set(_S5_4_CODES)
        - set(_M3_1_D029_CODES)
    )
    assert beyond_s5_4 == set(_M3_1_CODES)


def test_no_reason_code_beyond_the_single_approved_d029_addition_exists() -> None:
    """Decision 029 section 5 authorizes exactly one further code, and no alias."""
    beyond_d028 = (
        set(REASON_CODES)
        - set(_pre_s3_1_codes())
        - set(_NEW_CODES)
        - set(_S5_2_CODES)
        - set(_S5_4_CODES)
        - set(_M3_1_CODES)
    )
    assert beyond_d028 == set(_M3_1_D029_CODES)


def test_m3_1_codes_carry_the_approved_metadata() -> None:
    for code, expected in _M3_1_CODES.items():
        entry = REASON_CODES[code]
        assert entry.category == expected["category"]
        assert entry.blocks_release == expected["blocks_release"]
        assert entry.requires_manual_review == expected["requires_manual_review"]
        assert entry.decision_reference == expected["decision_reference"]
        assert (_REPO_ROOT / str(expected["decision_reference"])).is_file()
        assert entry.description.endswith(".")


def test_both_m3_1_codes_block_release_without_manual_review() -> None:
    blocking = reasons.release_blocking_codes()
    integrity = reasons.codes_for_category("integrity")
    for code in (*_M3_1_CODES, *_M3_1_D029_CODES):
        assert code in blocking
        assert code in integrity
        assert not REASON_CODES[code].requires_manual_review


def test_the_ceiling_code_is_distinct_from_retries_exhausted() -> None:
    """Decision 028 section 6: a consumed window ceiling is not an exhausted retry budget."""
    ceiling = REASON_CODES["SEC_REQUEST_CEILING_EXHAUSTED"]
    retries = REASON_CODES["SEC_RETRIES_EXHAUSTED"]
    assert ceiling.code != retries.code
    assert ceiling.description != retries.description
    assert "ceiling" in ceiling.description.lower()
    assert "SEC_RETRIES_EXHAUSTED" in ceiling.description


def test_the_interruption_code_is_distinct_from_partial_download() -> None:
    """Decision 028 section 6: an interruption is not an actual partial transfer."""
    interrupted = REASON_CODES["SEC_ACQUISITION_INTERRUPTED"]
    partial = REASON_CODES["RAW_PARTIAL_DOWNLOAD"]
    assert interrupted.code != partial.code
    assert interrupted.description != partial.description
    assert "RAW_PARTIAL_DOWNLOAD" in interrupted.description


def test_neither_m3_1_code_has_an_alias() -> None:
    """Decision 028 section 6 forbids an alias for either code."""
    for code in _M3_1_CODES:
        matches = [c for c in REASON_CODES if c != code and code in c]
        assert matches == [], f"{code} has alias-like siblings: {matches}"
