"""Reason-code registry invariants, including the M2.3 S3.1 pilot vocabulary addition.

Decisions 013-016 froze exactly sixteen new reason codes for the M2.3 pilot. These tests prove the
addition is exact (no more, no fewer, no renames) and that every pre-existing code from the accepted
S3.0 governance baseline is unchanged.

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

_PRE_S3_1_CODE_COUNT = 87
_PRE_S3_1_TOTAL_COUNT = 103

# Computed once, offline, from the accepted S3.0 governance baseline (the 87 reason codes that
# existed before the M2.3 S3.1 addition): sort the pre-S3.1 codes by their ``code`` string, render
# each as a JSON object with keys ``code``, ``category``, ``description``, ``blocks_release``,
# ``requires_manual_review``, ``decision_reference``, serialize the ordered list with
# ``json.dumps(records, sort_keys=True, separators=(",", ":"))``, and SHA-256 the UTF-8 bytes. This
# literal must never be recomputed from Git history at test time.
_PRE_S3_1_FINGERPRINT_SHA256 = "65c94cf2e10eb5854b2c00034c13f4f9de746bef39673ec420f7ee3125bd1c1b"


def _pre_s3_1_codes() -> dict[str, Any]:
    return {code: entry for code, entry in REASON_CODES.items() if code not in _NEW_CODES}


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


def test_exactly_sixteen_new_codes_were_added() -> None:
    added = set(REASON_CODES) - set(_pre_s3_1_codes())
    assert added == set(_NEW_CODES)
    assert len(added) == 16


def test_registry_count_is_exactly_one_hundred_three() -> None:
    assert len(REASON_CODES) == _PRE_S3_1_TOTAL_COUNT


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
    )
    assert len(set(new_decision_constants)) == 5
    for relative_path in new_decision_constants:
        assert (_REPO_ROOT / relative_path).is_file(), relative_path
