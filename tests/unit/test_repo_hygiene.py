"""Milestone 3.1: behavioural coverage of the repository-hygiene evidence-path refusal.

`scripts/check_repo_hygiene.py` is a standalone gate script, not part of the installed package,
so it is loaded here directly from its file path. These tests exercise
`check_reserved_evidence_path` -- layer 2 of the three-layer M3-L11 protection (Decision 028 §11) --
against the reserved evidence path materialised as a **regular file**, a **directory**, and a
**symlink**, and prove that each is refused with the expected reserved path and kind, while absence
is allowed.

The refusal is necessary *because* `/.m3-private-evidence` is in `.gitignore`. `candidate_files()`
enumerates through `git ls-files --exclude-standard`, so an ignored path is invisible to it and the
ignore rule alone would hide the very directory this gate must refuse. The check therefore inspects
the filesystem directly under an explicit root, independent of Git history, the system clock, the
network, the real SEC identity, and any machine-specific path.
`tests/unit/test_m3_evidence_paths.py` already asserts that this layer *exists*; these tests prove
that it *behaves*.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HYGIENE_SCRIPT = _REPO_ROOT / "scripts" / "check_repo_hygiene.py"


def _load_hygiene_module() -> ModuleType:
    """Load the standalone hygiene gate script as an importable module by file path."""
    spec = importlib.util.spec_from_file_location("check_repo_hygiene", _HYGIENE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_hygiene = _load_hygiene_module()
RESERVED_EVIDENCE_DIRNAME: str = _hygiene.RESERVED_EVIDENCE_DIRNAME
check_reserved_evidence_path = _hygiene.check_reserved_evidence_path


# --------------------------------------------------------------------------- #
# Absence is allowed
# --------------------------------------------------------------------------- #
def test_absence_of_the_reserved_path_is_allowed(tmp_path: Path) -> None:
    """A root with no reserved path present yields no finding."""
    assert check_reserved_evidence_path(tmp_path) == []


# --------------------------------------------------------------------------- #
# Each materialisation is refused, even though the path is git-ignored
# --------------------------------------------------------------------------- #
def test_a_reserved_regular_file_is_refused(tmp_path: Path) -> None:
    (tmp_path / RESERVED_EVIDENCE_DIRNAME).write_text("synthetic", encoding="utf-8")

    findings = check_reserved_evidence_path(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == RESERVED_EVIDENCE_DIRNAME
    assert "exists as a file" in findings[0].detail


def test_a_reserved_directory_is_refused(tmp_path: Path) -> None:
    (tmp_path / RESERVED_EVIDENCE_DIRNAME).mkdir()

    findings = check_reserved_evidence_path(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == RESERVED_EVIDENCE_DIRNAME
    assert "exists as a directory" in findings[0].detail


def test_a_reserved_symlink_to_a_directory_is_refused(tmp_path: Path) -> None:
    external = tmp_path / "external"
    external.mkdir()
    (tmp_path / RESERVED_EVIDENCE_DIRNAME).symlink_to(external, target_is_directory=True)

    findings = check_reserved_evidence_path(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == RESERVED_EVIDENCE_DIRNAME
    assert "exists as a symlink" in findings[0].detail


def test_a_reserved_symlink_is_classified_as_a_symlink_even_when_it_targets_a_file(
    tmp_path: Path,
) -> None:
    """A symlink is the bypass vector M3-L11 must catch; it is refused as a symlink, not a file."""
    target = tmp_path / "target.txt"
    target.write_text("synthetic", encoding="utf-8")
    (tmp_path / RESERVED_EVIDENCE_DIRNAME).symlink_to(target)

    findings = check_reserved_evidence_path(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == RESERVED_EVIDENCE_DIRNAME
    assert "exists as a symlink" in findings[0].detail


def test_a_broken_reserved_symlink_is_still_refused(tmp_path: Path) -> None:
    """A dangling symlink does not `exists()`, but `is_symlink()` still refuses it."""
    (tmp_path / RESERVED_EVIDENCE_DIRNAME).symlink_to(tmp_path / "does-not-exist")

    findings = check_reserved_evidence_path(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == RESERVED_EVIDENCE_DIRNAME
    assert "exists as a symlink" in findings[0].detail
