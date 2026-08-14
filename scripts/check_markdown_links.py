#!/usr/bin/env python3
"""Markdown relative-link gate (Decision 076 section 5).

Makes a broken relative Markdown link structurally detectable instead of
discoverable only when a reader follows it. Every navigation aid in this
repository -- ``Docs/decision_index.md``, ``Docs/architecture_map.md``,
``Docs/change_impact_map.md``, the contract README, ``CLAUDE.md`` itself -- is a
dense mesh of relative links, and a stale one is a bug in the pointer that this
gate now catches mechanically.

Scope: every ``.md`` file git tracks, plus untracked-not-ignored ones, matching
the enumeration used by ``check_no_secrets.py`` and ``check_repo_hygiene.py`` so
a file cannot escape one gate by escaping another.

What counts as a live link:

* inline links and images, ``[text](target)`` and ``![alt](target)``, including
  angle-bracket destinations and trailing titles;
* ordinary reference definitions, ``[label]: target``.

What is deliberately *not* treated as a live relative link:

* anything with a URI scheme (``https:``, ``mailto:``, ...) or a
  protocol-relative ``//`` prefix -- external, and never resolved here;
* a pure in-document anchor, ``#section`` -- an anchor, not a file path. A
  fragment on a file target (``foo.md#section``) is stripped, and the *file*
  half is resolved; the anchor half is not verified, which is a deliberate
  boundary rather than an oversight (see ``check_decision_section_refs.py`` for
  the section-level check this repository actually needs);
* anything inside a fenced code block, and anything inside an inline code span.
  Markdown does not linkify either, so neither is navigation. Masking preserves
  offsets, so ``[`Docs/x.md`](Docs/x.md)`` -- a code span in the link *text* --
  still has its destination checked.

A target resolves when it names a tracked path, or a directory that contains
one. Filesystem existence alone is not enough: an untracked or ignored file
resolves on the author's machine and nowhere else.

Known-broken links in immutable historical evidence are carried in
``ALLOWED_BROKEN``, which is exact by construction -- source file, target,
reason, and governing status, with no wildcard and no pattern. An entry that
matches nothing is itself a failure, so the allowlist cannot quietly rot into a
blanket exemption after the defect it names is gone.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Final, NamedTuple
from urllib.parse import unquote


class AllowedBroken(NamedTuple):
    """One exactly-scoped exemption for a known-broken historical link."""

    source: str
    target: str
    reason: str
    governing_status: str


#: Exact exemptions. Each names one source document and one literal link target.
#:
#: Both entries are in the same M3.2 independent review artifact: committed evidence bound to the
#: reviewed commit 3bf9987, introduced by 3069b03 and never modified since, and immutable under
#: the repository's evidence rules. Both were already broken when the artifact was accepted --
#: each writes ``../../Docs/Decisions/...`` from ``Docs/m3/reviews/``, which resolves to
#: ``Docs/Docs/Decisions/...``; the author meant ``../../Decisions/...``. Repairing them would
#: rewrite accepted evidence to satisfy a checker introduced afterwards, which Decision 076
#: section 7 prohibits, so the defect is recorded here instead of erased there. The cited
#: Decision 032 and Decision 033 records both exist and are unaffected; only these two links
#: into them are malformed.
_M3_2_REREVIEW: Final = (
    "Docs/m3/reviews/"
    "m3_2_corrected_contract_independent_rereview_3bf9987dd72e1531da2f678fbbef735f37aefcf4.md"
)
ALLOWED_BROKEN: Final[tuple[AllowedBroken, ...]] = (
    AllowedBroken(
        source=_M3_2_REREVIEW,
        target="../../Docs/Decisions/decision_032_m3_2_contract_corrections.md",
        reason=(
            "one path segment too many; resolves to Docs/Docs/Decisions/. The intended target, "
            "Docs/Decisions/decision_032_m3_2_contract_corrections.md, exists and is tracked."
        ),
        governing_status=(
            "immutable committed M3.2 review evidence bound to 3bf9987; not rewritten to "
            "satisfy a later checker (Decision 076 section 7)"
        ),
    ),
    AllowedBroken(
        source=_M3_2_REREVIEW,
        target="../../Docs/Decisions/decision_033_m3_2_correction_pass_adjudication.md",
        reason=(
            "one path segment too many; resolves to Docs/Docs/Decisions/. The intended target, "
            "Docs/Decisions/decision_033_m3_2_correction_pass_adjudication.md, exists and is "
            "tracked."
        ),
        governing_status=(
            "immutable committed M3.2 review evidence bound to 3bf9987; not rewritten to "
            "satisfy a later checker (Decision 076 section 7)"
        ),
    ),
)

MARKDOWN_SUFFIX: Final = ".md"
#: ``scheme:`` per RFC 3986. Matched anchored, so a bare ``foo:bar`` filename would count as a
#: scheme -- no such path exists here, and treating one as external is the safe direction.
SCHEME: Final = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
FENCE: Final = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
#: ``[label]: target`` with an optional title. Anchored per line over already-masked text.
REFERENCE_DEFINITION: Final = re.compile(
    r"^ {0,3}\[([^\]]+)\]:\s*(<[^>]*>|\S+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*$"
)


class Finding(NamedTuple):
    """One unresolved relative Markdown link."""

    source: str
    line_number: int
    target: str
    detail: str


class Link(NamedTuple):
    """One extracted link destination and where it was written."""

    line_number: int
    target: str


def repository_root() -> Path:
    """Return the repository root containing this script."""
    return Path(__file__).resolve().parent.parent


def tracked_paths(root: Path) -> list[str]:
    """Return tracked plus untracked-not-ignored paths."""
    completed = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=root,
        capture_output=True,
        check=True,
        text=True,
    )
    return sorted(entry for entry in completed.stdout.split("\0") if entry)


def resolvable_paths(paths: list[str]) -> set[str]:
    """Return every tracked path plus every directory on the way to one.

    A link may legitimately point at a directory (``Docs/Decisions/``), which never appears in
    ``git ls-files`` because git tracks files. Adding each ancestor makes a directory target
    resolve without weakening the rule that the destination must be tracked.
    """
    resolvable = set(paths)
    for entry in paths:
        parent = Path(entry).parent
        while parent != Path():
            resolvable.add(parent.as_posix())
            parent = parent.parent
    return resolvable


def _closes(match: re.Match[str] | None, fence: str) -> bool:
    """Whether a fence line terminates the open block of ``fence``."""
    if match is None:
        return False
    marker = match.group(1)
    return marker[0] == fence[0] and len(marker) >= len(fence)


def mask_code(text: str) -> str:
    """Blank out fenced code blocks and inline code spans, preserving every offset.

    Replacement is space-for-character rather than deletion so that line numbers and match
    offsets computed against the result are still true of the original document.
    """
    lines = text.split("\n")
    fence: str | None = None
    for index, line in enumerate(lines):
        match = FENCE.match(line)
        if fence is None:
            if match is not None and "`" not in match.group(2):
                fence = match.group(1)
                lines[index] = " " * len(line)
            continue
        # Inside a block: only a fence of the same character and at least the opening length
        # closes it, so a ``~~~`` line inside a ``` block is content, not a terminator.
        if _closes(match, fence):
            fence = None
        lines[index] = " " * len(line)
    return _mask_code_spans("\n".join(lines))


def _mask_code_spans(text: str) -> str:
    """Blank the interior of every inline code span, preserving offsets."""
    out = list(text)
    position = 0
    length = len(text)
    while position < length:
        if text[position] != "`":
            position += 1
            continue
        start = position
        while position < length and text[position] == "`":
            position += 1
        ticks = position - start
        closing = text.find("`" * ticks, position)
        # A run followed by no matching run is literal backticks, not an unterminated span.
        if closing == -1 or (closing + ticks < length and text[closing + ticks] == "`"):
            continue
        for index in range(position, closing):
            if out[index] != "\n":
                out[index] = " "
        position = closing + ticks
    return "".join(out)


def _destination(text: str, start: int) -> tuple[str, int] | None:
    """Read one inline-link destination beginning at the ``(`` at ``start``.

    Returns the raw destination and the offset just past the closing ``)``. Parentheses are
    tracked by depth rather than by regex so a destination containing a balanced pair is read
    whole, and an unbalanced one is rejected instead of silently truncated.
    """
    position = start + 1
    length = len(text)
    while position < length and text[position] in " \t\n":
        position += 1
    if position < length and text[position] == "<":
        end = text.find(">", position)
        if end == -1:
            return None
        destination = text[position + 1 : end]
        close = text.find(")", end)
        return (destination, close + 1) if close != -1 else None
    begin = position
    depth = 0
    while position < length:
        char = text[position]
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                break
            depth -= 1
        elif char in " \t\n":
            break
        position += 1
    destination = text[begin:position]
    while position < length and text[position] in " \t\n":
        position += 1
    # Skip an optional title before the closing parenthesis.
    if position < length and text[position] in "\"'":
        quote = text[position]
        end = text.find(quote, position + 1)
        if end == -1:
            return None
        position = end + 1
        while position < length and text[position] in " \t\n":
            position += 1
    if position >= length or text[position] != ")":
        return None
    return destination, position + 1


def extract_links(text: str) -> list[Link]:
    """Return every inline-link and reference-definition destination in a document."""
    masked = mask_code(text)
    links: list[Link] = []

    position = 0
    while True:
        bracket = masked.find("](", position)
        if bracket == -1:
            break
        parsed = _destination(masked, bracket + 1)
        if parsed is None:
            position = bracket + 2
            continue
        destination, position = parsed
        links.append(Link(masked.count("\n", 0, bracket) + 1, destination))

    for number, line in enumerate(masked.split("\n"), start=1):
        match = REFERENCE_DEFINITION.match(line)
        if match is not None:
            links.append(Link(number, match.group(2).strip("<>")))

    return sorted(links)


def is_external(target: str) -> bool:
    """Whether a destination points outside the repository and is not resolved here."""
    return target.startswith("//") or SCHEME.match(target) is not None


def resolve(source: str, target: str) -> str | None:
    """Return the repository-relative path a link names, or ``None`` if it names no file.

    ``None`` covers the deliberate non-file cases: empty destinations, pure anchors, and any
    target that escapes the repository root, which is reported by the caller as broken rather
    than resolved outside the tree.
    """
    without_fragment = target.split("#", 1)[0]
    if not without_fragment:
        return None
    decoded = unquote(without_fragment)
    if decoded.startswith("/"):
        # Root-relative: interpreted against the repository root, not the filesystem root.
        candidate = Path(decoded.lstrip("/"))
    else:
        candidate = Path(source).parent / decoded
    parts: list[str] = []
    for part in candidate.as_posix().split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return ".."
            parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def check_document(source: str, text: str, resolvable: set[str]) -> tuple[list[Finding], int]:
    """Return findings for one document and the number of relative links it was asked about."""
    findings: list[Finding] = []
    checked = 0
    for link in extract_links(text):
        target = link.target.strip()
        if not target or target.startswith("#") or is_external(target):
            continue
        checked += 1
        resolved = resolve(source, target)
        if resolved is None:
            continue
        if resolved == "..":
            findings.append(
                Finding(source, link.line_number, target, "link escapes the repository root")
            )
        elif resolved not in resolvable:
            findings.append(
                Finding(source, link.line_number, target, f"no tracked path at {resolved!r}")
            )
    return findings, checked


def partition(findings: list[Finding]) -> tuple[list[Finding], list[Finding], list[AllowedBroken]]:
    """Split findings into unallowed and allowed, and report allowlist entries that matched nothing.

    The third element is what keeps the allowlist honest. An entry naming a defect that no longer
    exists -- or one whose target was mistyped, and so never matched anything -- is a standing
    exemption for nothing, and is returned so the gate can fail on it.
    """
    allowed_keys = {(entry.source, entry.target) for entry in ALLOWED_BROKEN}
    unallowed = [f for f in findings if (f.source, f.target) not in allowed_keys]
    allowed = [f for f in findings if (f.source, f.target) in allowed_keys]
    matched = {(f.source, f.target) for f in allowed}
    unused = [entry for entry in ALLOWED_BROKEN if (entry.source, entry.target) not in matched]
    return unallowed, allowed, unused


def main() -> int:
    """Run the link gate and return a process exit code."""
    root = repository_root()
    paths = tracked_paths(root)
    resolvable = resolvable_paths(paths)
    documents = [entry for entry in paths if entry.endswith(MARKDOWN_SUFFIX)]

    findings: list[Finding] = []
    total_links = 0
    read = 0
    for source in documents:
        try:
            text = (root / source).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        read += 1
        document_findings, checked = check_document(source, text, resolvable)
        findings.extend(document_findings)
        total_links += checked

    unallowed, allowed, unused = partition(sorted(findings))

    if unallowed or unused:
        print(f"Markdown link check FAILED: {len(unallowed)} unallowed broken link(s).")
        for finding in unallowed:
            print(f"  {finding.source}:{finding.line_number}: {finding.target!r}")
            print(f"    {finding.detail}")
        for entry in unused:
            print(f"  allowlist entry matched nothing: {entry.source} -> {entry.target!r}")
            print("    the defect it exempts is gone or the entry is wrong; remove or fix it")
        return 1

    print(f"Markdown link check passed: {read} document(s), {total_links} relative link(s).")
    print(f"Unallowed broken links: 0. Allowed historical exceptions: {len(allowed)}.")
    for finding in allowed:
        print(f"  allowed: {finding.source}:{finding.line_number} -> {finding.target!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
