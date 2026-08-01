"""Milestone 3.1: the evidence-root boundary (M3-L11, Decision 028 §11).

Completed operational evidence lives in an owner-controlled private root **outside** the public
repository. Decision 028 §11 requires three independent layers, because no one of them is
sufficient:

1. a reserved root-level ``.gitignore`` entry, which stops accidental staging;
2. an explicit repository-hygiene refusal of that reserved path -- necessary precisely *because*
   the hygiene scanner enumerates through ``git ls-files --exclude-standard``, so an ignored path
   is invisible to it and the ignore rule alone would **weaken** detection; and
3. this module: a resolved-path refusal of any evidence root equal to, inside, or an ancestor of
   the checkout, with symlinks resolved so an alias cannot bypass the check.

These tests exercise layer 3 and assert that layers 1 and 2 exist.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from disclosure_drift.m3.evidence_paths import (
    RESERVED_EVIDENCE_DIRNAME,
    EvidenceRootError,
    require_external_evidence_root,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Lawful roots
# --------------------------------------------------------------------------- #
def test_a_sibling_root_outside_the_checkout_is_lawful(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    evidence = tmp_path / "evidence"
    evidence.mkdir()

    resolved = require_external_evidence_root(evidence, checkout)

    assert resolved == evidence.resolve()
    assert resolved.is_absolute()


def test_a_root_on_a_wholly_unrelated_path_is_lawful(tmp_path: Path) -> None:
    checkout = tmp_path / "a" / "checkout"
    checkout.mkdir(parents=True)
    evidence = tmp_path / "b" / "private-evidence"
    evidence.mkdir(parents=True)

    assert require_external_evidence_root(evidence, checkout) == evidence.resolve()


# --------------------------------------------------------------------------- #
# The three named containment vectors
# --------------------------------------------------------------------------- #
def test_a_root_equal_to_the_checkout_is_refused(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()

    with pytest.raises(EvidenceRootError, match="equal to"):
        require_external_evidence_root(checkout, checkout)


def test_a_root_inside_the_checkout_is_refused(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    (checkout / "nested" / "evidence").mkdir(parents=True)

    with pytest.raises(EvidenceRootError, match="inside"):
        require_external_evidence_root(checkout / "nested" / "evidence", checkout)


def test_the_reserved_in_tree_path_is_refused(tmp_path: Path) -> None:
    """The reserved path is never a lawful operational evidence root."""
    checkout = tmp_path / "checkout"
    reserved = checkout / RESERVED_EVIDENCE_DIRNAME
    reserved.mkdir(parents=True)

    with pytest.raises(EvidenceRootError):
        require_external_evidence_root(reserved, checkout)


def test_a_root_containing_the_checkout_is_refused(tmp_path: Path) -> None:
    """An ancestor root would place the whole checkout inside the evidence tree."""
    evidence = tmp_path / "outer"
    checkout = evidence / "checkout"
    checkout.mkdir(parents=True)

    with pytest.raises(EvidenceRootError, match="ancestor|contains"):
        require_external_evidence_root(evidence, checkout)


# --------------------------------------------------------------------------- #
# Symlink aliases cannot bypass the check
# --------------------------------------------------------------------------- #
def test_a_symlink_pointing_into_the_checkout_is_refused(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    (checkout / "inside").mkdir(parents=True)
    alias = tmp_path / "alias"
    alias.symlink_to(checkout / "inside", target_is_directory=True)

    with pytest.raises(EvidenceRootError):
        require_external_evidence_root(alias, checkout)


def test_a_symlink_pointing_at_the_checkout_itself_is_refused(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(checkout, target_is_directory=True)

    with pytest.raises(EvidenceRootError):
        require_external_evidence_root(alias, checkout)


def test_a_symlinked_checkout_cannot_hide_containment(tmp_path: Path) -> None:
    """Resolving only one side would let an aliased checkout slip past."""
    real_checkout = tmp_path / "real"
    (real_checkout / "inside").mkdir(parents=True)
    aliased_checkout = tmp_path / "aliased"
    aliased_checkout.symlink_to(real_checkout, target_is_directory=True)

    with pytest.raises(EvidenceRootError):
        require_external_evidence_root(real_checkout / "inside", aliased_checkout)


# --------------------------------------------------------------------------- #
# Case-insensitive containment (macOS default volumes)
# --------------------------------------------------------------------------- #
def test_containment_is_detected_case_insensitively(tmp_path: Path) -> None:
    """A byte-wise comparison would miss a case-variant path on a case-insensitive volume."""
    checkout = tmp_path / "Checkout"
    checkout.mkdir()
    variant = tmp_path / "CHECKOUT"

    with pytest.raises(EvidenceRootError):
        require_external_evidence_root(variant, checkout)


# --------------------------------------------------------------------------- #
# Fail closed on unusable input
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("supplied", ["", "   "])
def test_an_empty_root_is_refused(supplied: str, tmp_path: Path) -> None:
    with pytest.raises(EvidenceRootError, match="absolute"):
        require_external_evidence_root(supplied, tmp_path)


def test_a_relative_root_is_refused(tmp_path: Path) -> None:
    """An operator must state an absolute external path, never one resolved from the cwd."""
    with pytest.raises(EvidenceRootError, match="absolute"):
        require_external_evidence_root(Path("evidence"), tmp_path)


# --------------------------------------------------------------------------- #
# Layers 1 and 2 exist in the live repository
# --------------------------------------------------------------------------- #
def test_layer_one_the_reserved_ignore_rule_exists() -> None:
    gitignore = (_REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert f"/{RESERVED_EVIDENCE_DIRNAME}" in gitignore.split()


def test_layer_two_the_hygiene_refusal_names_the_reserved_path() -> None:
    hygiene = (_REPO_ROOT / "scripts" / "check_repo_hygiene.py").read_text(encoding="utf-8")
    assert RESERVED_EVIDENCE_DIRNAME in hygiene
