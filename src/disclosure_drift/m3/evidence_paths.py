"""Evidence-root boundary validation (M3-L11, Decision 028 §11).

Completed operational evidence lives in an **owner-controlled private root outside the public
repository**. Three independent layers enforce that, because no single one is sufficient:

1. **A reserved root-level ``.gitignore`` entry** (``/.m3-private-evidence``). It stops accidental
   staging, and nothing more.
2. **An explicit repository-hygiene refusal of that reserved path.** This exists *because* of
   layer 1, not in addition to it: ``scripts/check_repo_hygiene.py`` enumerates candidates with
   ``git ls-files --cached --others --exclude-standard``, so an ignored path is invisible to the
   scanner. An ignore rule on its own would therefore **weaken** detection -- it would hide the
   very directory the scanner needs to refuse. Layer 2 closes that hole for a file, a directory,
   or a symlink at the reserved path.
3. **This module.** Layer 3 is the general protection and does not depend on the reserved name at
   all: it refuses any evidence root that resolves equal to, inside, or an ancestor of the
   checkout. Symlinks are resolved on both sides first, so an alias cannot launder containment.

Layer 3 is what a command calls. It never creates, writes, or reads the evidence root; it only
decides whether a supplied root is lawful, and refuses rather than falling back to a default.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

__all__ = [
    "RESERVED_EVIDENCE_DIRNAME",
    "EvidenceRootError",
    "require_external_evidence_root",
]

#: The repository-root path reserved so it can be refused. It is never a lawful evidence root.
RESERVED_EVIDENCE_DIRNAME: Final = ".m3-private-evidence"


class EvidenceRootError(ValueError):
    """Raised when a supplied evidence root is not a lawful external root.

    Refusal is the only outcome: there is no default root and no fallback. A command that
    cannot prove its evidence root is external must not write evidence at all.
    """


def _resolved(path: Path) -> Path:
    """Fully resolve a path, following symlinks, without requiring that it exist."""
    return Path(os.path.realpath(path))


def _comparable(path: Path) -> tuple[str, ...]:
    """Case-folded path components, for containment tests.

    macOS default volumes are case-insensitive, so a byte-wise comparison of two resolved paths
    can miss a case-variant containment. Folding case makes the refusal conservative: on a
    case-sensitive volume this can only ever refuse *more*, never less, and refusing a lawful
    root fails closed.
    """
    return tuple(part.casefold() for part in path.parts)


def _contains(ancestor: tuple[str, ...], descendant: tuple[str, ...]) -> bool:
    """Whether ``descendant`` lies strictly within ``ancestor``."""
    return len(descendant) > len(ancestor) and descendant[: len(ancestor)] == ancestor


def require_external_evidence_root(root: str | Path, repository_root: str | Path) -> Path:
    """Return the resolved evidence root, or refuse it.

    No refusal message names either resolved path. Master plan §17 stop condition 12 bars an
    absolute personal path from any output, and a refusal is printed to the operator, so naming the
    path here would leak exactly what this boundary exists to protect. The operator supplied the
    root and already knows it; the message states the rule that was broken.

    Refuses, with symlinks resolved on both sides beforehand:

    - a root that is not an absolute path;
    - a root equal to the checkout;
    - a root inside the checkout, including the reserved ``.m3-private-evidence`` path;
    - a root that is an ancestor of the checkout, which would place the whole checkout inside
      the evidence tree.
    """
    if isinstance(root, str) and not root.strip():
        message = "evidence root must be a non-empty absolute path outside the repository checkout"
        raise EvidenceRootError(message)

    supplied = Path(root)
    if not supplied.is_absolute():
        message = (
            "the supplied evidence root must be an absolute path; a relative path would be "
            "resolved against the working directory, which is not a stated external location"
        )
        raise EvidenceRootError(message)

    evidence = _resolved(supplied)
    checkout = _resolved(Path(repository_root))

    evidence_parts = _comparable(evidence)
    checkout_parts = _comparable(checkout)

    if evidence_parts == checkout_parts:
        message = (
            "the supplied evidence root is equal to the repository checkout; completed evidence "
            "must live in an owner-controlled private root outside the public repository"
        )
        raise EvidenceRootError(message)

    if _contains(checkout_parts, evidence_parts):
        reserved = (
            " (the reserved path is never a lawful evidence root)"
            if (RESERVED_EVIDENCE_DIRNAME.casefold() in evidence_parts)
            else ""
        )
        message = (
            f"the supplied evidence root is inside the repository checkout{reserved}; "
            f"completed evidence must live outside the public repository"
        )
        raise EvidenceRootError(message)

    if _contains(evidence_parts, checkout_parts):
        message = (
            "the supplied evidence root is an ancestor of the repository checkout and so contains "
            "it; the checkout must not lie inside the evidence tree"
        )
        raise EvidenceRootError(message)

    return evidence
