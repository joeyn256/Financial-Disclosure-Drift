#!/usr/bin/env python3
"""Repository hygiene gate (assignment section 19, Decision 009).

Fails when any of the following is tracked or about to be tracked:

* a raw SEC payload or anything under ``data/`` other than ``data/README.md``;
* a SQLite database or its ``-wal`` / ``-shm`` companions;
* a Parquet release;
* a ``.part`` transfer artifact;
* a lock file.

Also fails when a tracked text file contains an absolute home-directory path,
which would leak a personal path into a committed manifest. Add
``hygiene-scan: allow`` to the offending line, or to the line directly above it,
to exempt a deliberate synthetic example.

Complements ``scripts/check_no_secrets.py``, which looks for credentials.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Final, NamedTuple

ALLOWED_DATA_FILES: Final[frozenset[str]] = frozenset({"data/README.md"})

#: Reserved Milestone 3 operational-evidence path (M3-L11, Decision 028 section 11). Never a
#: lawful evidence root, and never tracked. Kept in sync with
#: ``disclosure_drift.m3.evidence_paths.RESERVED_EVIDENCE_DIRNAME``; the hygiene gate is a
#: standalone script and does not import the package.
RESERVED_EVIDENCE_DIRNAME: Final[str] = ".m3-private-evidence"
FORBIDDEN_SUFFIXES: Final[tuple[str, ...]] = (
    ".sqlite",
    ".sqlite3",
    ".sqlite3-shm",
    ".sqlite3-wal",
    ".sqlite-shm",
    ".sqlite-wal",
    ".parquet",
    ".part",
    ".lock",
)
BINARY_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".gz", ".pyc", ".so"}
)
HOME_PATH_PATTERN: Final = re.compile(r"(?:/Users/|/home/|C:\\Users\\)[A-Za-z0-9._-]+/")
ALLOW_MARKER: Final = "hygiene-scan: allow"


class Finding(NamedTuple):
    """One hygiene violation."""

    path: str
    detail: str


def repository_root() -> Path:
    """Return the repository root containing this script."""
    return Path(__file__).resolve().parent.parent


def candidate_files(root: Path) -> list[str]:
    """Return tracked plus untracked-not-ignored paths."""
    completed = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=root,
        capture_output=True,
        check=True,
        text=True,
    )
    return sorted(entry for entry in completed.stdout.split("\0") if entry)


def check_reserved_evidence_path(root: Path) -> list[Finding]:
    """Refuse the reserved Milestone 3 evidence path, however it appears.

    This check exists *because* ``/.m3-private-evidence`` is in ``.gitignore``. ``candidate_files``
    enumerates with ``git ls-files --exclude-standard``, so an ignored path never appears in that
    list -- the ignore rule alone would hide the very directory this gate must refuse. The check
    therefore looks at the filesystem directly, and refuses a file, a directory, or a symlink at
    the reserved path (M3-L11, Decision 028 section 11).
    """
    reserved = root / RESERVED_EVIDENCE_DIRNAME
    if not reserved.exists() and not reserved.is_symlink():
        return []
    kind = "symlink" if reserved.is_symlink() else ("directory" if reserved.is_dir() else "file")
    return [
        Finding(
            RESERVED_EVIDENCE_DIRNAME,
            f"reserved Milestone 3 evidence path exists as a {kind}; completed operational "
            f"evidence must live in an owner-controlled private root outside this repository",
        )
    ]


def check_paths(files: list[str]) -> list[Finding]:
    """Return findings for forbidden paths and suffixes."""
    findings: list[Finding] = []
    for entry in files:
        if entry.startswith("data/") and entry not in ALLOWED_DATA_FILES:
            findings.append(Finding(entry, "only data/README.md may be tracked under data/"))
        if entry.endswith(FORBIDDEN_SUFFIXES):
            findings.append(Finding(entry, "generated or database artifact must not be tracked"))
        if entry == ".env":
            findings.append(Finding(entry, "environment file must not be tracked"))
        if entry == RESERVED_EVIDENCE_DIRNAME or entry.startswith(f"{RESERVED_EVIDENCE_DIRNAME}/"):
            findings.append(
                Finding(entry, "reserved Milestone 3 evidence path must never be tracked")
            )
    return findings


def check_home_paths(root: Path, files: list[str]) -> list[Finding]:
    """Return findings for absolute home paths inside tracked text files."""
    findings: list[Finding] = []
    for entry in files:
        if Path(entry).suffix.lower() in BINARY_SUFFIXES:
            continue
        try:
            text = (root / entry).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        for number, line in enumerate(lines, start=1):
            preceding = lines[number - 2] if number >= 2 else ""
            if ALLOW_MARKER in line or ALLOW_MARKER in preceding:
                continue
            match = HOME_PATH_PATTERN.search(line)
            if match is not None:
                findings.append(
                    Finding(f"{entry}:{number}", f"absolute home path {match.group(0)!r}")
                )
    return findings


def main() -> int:
    """Run the hygiene gate and return a process exit code."""
    root = repository_root()
    files = candidate_files(root)
    findings = (
        check_paths(files) + check_home_paths(root, files) + check_reserved_evidence_path(root)
    )

    if findings:
        print(f"Repository hygiene FAILED: {len(findings)} finding(s).")
        for finding in findings:
            print(f"  {finding.path}: {finding.detail}")
        return 1

    print(f"Repository hygiene passed: {len(files)} path(s) checked, 0 findings.")
    print("No raw SEC data, database, release, or personal path is tracked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
