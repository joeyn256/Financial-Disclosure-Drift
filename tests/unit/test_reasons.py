"""Reason-code registry invariants, including the M2.3 S3.1 pilot vocabulary addition.

Decisions 013-016 froze exactly sixteen new reason codes for the M2.3 pilot. These tests prove the
addition is exact (no more, no fewer, no renames) and that every pre-existing code from the accepted
S3.0 governance baseline (commit ``0cd5e1ee9eb475724fc5be3d93271b078d847077``) is unchanged.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from disclosure_drift import reasons
from disclosure_drift.reasons import REASON_CODES, ReasonCode

_BASELINE_COMMIT = "0cd5e1ee9eb475724fc5be3d93271b078d847077"
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


def _load_baseline_reason_codes() -> dict[str, ReasonCode]:
    """Load ``REASON_CODES`` exactly as committed at the accepted S3.0 governance baseline."""
    result = subprocess.run(
        ["git", "show", f"{_BASELINE_COMMIT}:src/disclosure_drift/reasons.py"],
        cwd=_REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    module_name = "disclosure_drift._reasons_s3_0_baseline"
    module = ModuleType(module_name)
    sys.modules[module_name] = module
    try:
        exec(compile(result.stdout, "<baseline reasons.py>", "exec"), module.__dict__)  # noqa: S102
        baseline: dict[str, ReasonCode] = dict(module.__dict__["REASON_CODES"])
    finally:
        del sys.modules[module_name]
    return baseline


@pytest.fixture(scope="module")
def baseline_codes() -> dict[str, ReasonCode]:
    """The reason-code registry as it stood at the accepted S3.0 baseline commit."""
    return _load_baseline_reason_codes()


def test_exactly_sixteen_new_codes_were_added(baseline_codes: dict[str, ReasonCode]) -> None:
    added = set(REASON_CODES) - set(baseline_codes)
    assert added == set(_NEW_CODES)
    assert len(added) == 16


def test_registry_count_increased_by_exactly_sixteen(
    baseline_codes: dict[str, ReasonCode],
) -> None:
    assert len(REASON_CODES) == len(baseline_codes) + 16


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


def test_pre_s3_1_codes_remain_present_and_unchanged(
    baseline_codes: dict[str, ReasonCode],
) -> None:
    for code, baseline_entry in baseline_codes.items():
        current_entry = REASON_CODES[code]
        assert current_entry.category == baseline_entry.category
        assert current_entry.description == baseline_entry.description
        assert current_entry.blocks_release == baseline_entry.blocks_release
        assert current_entry.requires_manual_review == baseline_entry.requires_manual_review
        assert current_entry.decision_reference == baseline_entry.decision_reference


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
