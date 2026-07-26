#!/usr/bin/env python3
"""Fail if a tracked or soon-to-be-tracked file appears to contain a secret.

Scope: every textual file git already tracks, plus untracked files that are not
ignored. Including not-yet-committed files makes the check meaningful before the
first commit, and ``.gitignore`` is respected, so ``.env`` and the data
directories are never read.

The research directories ``Docs/``, ``Literature/``, and ``Milestones/`` are
scanned as text — the acceptance requirement covers every tracked text file — but
this script never writes to them. Binary formats (spreadsheets, images,
archives, PDFs) are skipped, as is any file that does not decode as UTF-8.

Placeholder addresses on reserved example domains (``example.com`` and friends,
per RFC 2606) are recognized as intentional documentation and never reported, so
``.env.example`` passes cleanly.

Add ``secret-scan: allow`` to a line to exempt it deliberately.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Final, NamedTuple

BINARY_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        ".7z",
        ".bz2",
        ".dat",
        ".db",
        ".doc",
        ".docx",
        ".gif",
        ".gz",
        ".ico",
        ".jpeg",
        ".jpg",
        ".pdf",
        ".png",
        ".ppt",
        ".pptx",
        ".pyc",
        ".so",
        ".tar",
        ".tgz",
        ".webp",
        ".whl",
        ".xls",
        ".xlsx",
        ".zip",
    }
)
ALLOW_MARKER: Final = "secret-scan: allow"
PLACEHOLDER_DOMAIN_SUFFIXES: Final[tuple[str, ...]] = (
    "example.com",
    "example.org",
    "example.net",
    "example.edu",
    ".example",
    ".invalid",
    ".test",
    ".localhost",
)
TEMPLATE_DOMAIN_PREFIXES: Final[tuple[str, ...]] = ("your-", "your.", "yourdomain", "yourorg")

_ASSIGNMENT = re.compile(  # secret-scan: allow
    r"(?i)\b(api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?key|"
    r"auth[_-]?token|password|passwd|secret|token)\b\s*[:=]\s*"
    r"[\"']?([A-Za-z0-9/+=_\-]{12,})[\"']?"
)
_PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")  # secret-scan: allow
_AWS_ACCESS_KEY = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")  # secret-scan: allow
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_PLACEHOLDER_VALUES: Final[frozenset[str]] = frozenset(
    {
        "changeme",
        "placeholder",
        "your-key-here",
        "xxxxxxxxxxxx",
        "disclosure_drift",
        "disclosure-drift",
    }
)


class Finding(NamedTuple):
    """One suspected secret."""

    path: str
    line_number: int
    reason: str
    excerpt: str


def repository_root() -> Path:
    """Return the repository root containing this script."""
    return Path(__file__).resolve().parent.parent


def tracked_files(root: Path) -> list[str]:
    """Return in-scope textual file paths (tracked or untracked-not-ignored)."""
    completed = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=root,
        capture_output=True,
        check=True,
        text=True,
    )
    selected = [
        entry
        for entry in completed.stdout.split("\0")
        if entry and Path(entry).suffix.lower() not in BINARY_SUFFIXES
    ]
    return sorted(selected)


def _is_placeholder_email(address: str) -> bool:
    """Whether an address is documentation rather than a real contact.

    Two families are recognized: RFC 2606 reserved domains, and template domains
    of the ``your-something`` form used in instructions and test fixtures.
    """
    domain = address.rsplit("@", 1)[-1].lower()
    if domain.endswith(PLACEHOLDER_DOMAIN_SUFFIXES):
        return True
    return domain.startswith(TEMPLATE_DOMAIN_PREFIXES)


def _is_placeholder_value(value: str) -> bool:
    lowered = value.lower()
    if lowered in _PLACEHOLDER_VALUES:
        return True
    return bool(re.fullmatch(r"[x*]{4,}|<[^>]+>", lowered))


def scan_line(path: str, number: int, line: str) -> list[Finding]:
    """Return findings for a single line."""
    if ALLOW_MARKER in line:
        return []
    findings: list[Finding] = []
    excerpt = line.strip()[:120]

    if _PRIVATE_KEY.search(line):
        findings.append(Finding(path, number, "private key block", excerpt))
    if _AWS_ACCESS_KEY.search(line):
        findings.append(Finding(path, number, "AWS access key id", excerpt))
    for match in _ASSIGNMENT.finditer(line):
        value = match.group(2)
        if _is_placeholder_value(value):
            continue
        findings.append(Finding(path, number, f"assignment to {match.group(1)!r}", excerpt))
    for match in _EMAIL.finditer(line):
        address = match.group(0)
        if _is_placeholder_email(address):
            continue
        findings.append(Finding(path, number, f"non-placeholder email {address!r}", excerpt))
    return findings


def scan_repository(root: Path) -> tuple[list[Finding], int, int]:
    """Scan every in-scope file; return findings, files read, and files skipped."""
    findings: list[Finding] = []
    files = tracked_files(root)
    read = 0
    skipped = 0

    if ".env" in files:
        findings.append(Finding(".env", 0, "environment file is tracked", ".env"))

    for relative in files:
        try:
            text = (root / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            skipped += 1
            continue
        read += 1
        for number, line in enumerate(text.splitlines(), start=1):
            findings.extend(scan_line(relative, number, line))
    return findings, read, skipped


def main() -> int:
    """Run the scan and return a process exit code."""
    root = repository_root()
    findings, read, skipped = scan_repository(root)

    if findings:
        print(f"Secret scan FAILED: {len(findings)} finding(s).")
        for finding in findings:
            print(f"  {finding.path}:{finding.line_number}: {finding.reason}")
            print(f"    {finding.excerpt}")
        return 1

    print(f"Secret scan passed: {read} textual file(s) scanned, 0 findings.")
    print(f"Skipped {skipped} non-UTF-8 file(s); binary formats are excluded by suffix.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
