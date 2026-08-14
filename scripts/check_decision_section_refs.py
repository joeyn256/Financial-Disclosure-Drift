#!/usr/bin/env python3
"""Decision section-reference gate (Decision 076 section 6).

Catches the defect class that produced MIN-A: source or documentation text that
cites a decision record *by section*, where the record has no such section. The
citation reads as authority, resolves to nothing, and stays wrong until a human
happens to follow it. This gate resolves every one of them mechanically.

The rule is narrow on purpose. It validates only what this repository actually
writes, which was inventoried before the grammar was fixed:

* **Headings.** Every numbered decision heading in ``Docs/Decisions/`` matches
  one shape -- two to six ``#``, then ``N``, ``N.N``, or ``N.N.N``, then an
  optional ``.``. Nothing else is treated as a section. The leading component is
  capped at two digits so that a heading opening with a year, such as
  ``## 2025 maturity gate`` in Decision 003, is prose rather than section 2025.
* **Citations.** ``Decision NNN`` followed immediately by ``§``, ``§§``,
  ``section``, or ``sections``, then a section list. Matching is
  case-insensitive, because the status ledger writes citations in capitals.
  Lists and ranges are read (``§§7-8``, ``§§21 and 13``, ``sections 6 through
  8``) and every member is validated. Reading stops at the first token that is
  not a section number, so "Decision 013 section 5 and Decision 014 section 1"
  contributes 5 to the first record and 1 to the second, never 1 to the first.
  A bare "Decision 075" with no section marker asserts nothing about sections
  and is not a citation this gate can check.

Decisions 001-006 predate the numbered convention and use prose headings
(``## Decision``, ``## Reason``). Nothing in the repository cites them by
section, so they need no exception; a citation that appeared later would be
reported, which is the correct outcome -- there would be no section to resolve.

Decision NNN resolves to ``Docs/Decisions/decision_NNN_*.md``, preferring the
file without a ``_v0_N`` version suffix. Decision 003 is the only number with
archived versions, and the unsuffixed file is the live record.

Scope: every tracked or untracked-not-ignored textual file, matching the
enumeration used by the other gates. In Markdown, fenced code blocks are skipped
-- a fence quotes text rather than citing it, which is what lets an evidence
record reproduce a historical bad citation verbatim without the gate treating
the quotation as a live claim. Python and other sources are scanned whole.

That fence rule has a known cost, stated rather than hidden: the machine-readable
state block at the end of ``Milestones/STATUS.md`` is fenced, so citations inside
it are not checked. Nothing is lost in practice today -- the one stale citation
it carries is caught in three unfenced places -- but a citation written *only*
there would not be.

``ALLOWED_UNRESOLVED`` carries exact exceptions: one source file, one decision,
one section, a reason, and a governing status. No wildcard, no pattern, no
per-line escape marker. An entry that matches nothing fails the gate, so the
list cannot rot into a blanket exemption.
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
DECISIONS_DIR: Final = "Docs/Decisions"
#: ``decision_NNN_slug.md``. The optional trailing ``_v0_N`` marks an archived version.
DECISION_FILE: Final = re.compile(r"^decision_(\d{3})_(.+?)(_v\d+_\d+)?\.md$")
#: A numbered decision heading. The leading component is capped at two digits so a heading that
#: opens with a year is not read as a section number.
HEADING: Final = re.compile(r"^#{2,6}[ \t]+(\d{1,2}(?:\.\d+)*)\.?(?=[ \t]|$)")
#: ``Decision NNN`` immediately followed by a section marker. The marker is required: a bare
#: "Decision 075" names the record as a whole and asserts nothing about its sections.
CITATION_HEAD: Final = re.compile(
    r"(?i)\bDecision[ \t]+(\d{3})[ \t]*(?:§{1,2}[ \t]*|sections?[ \t]+)"
)
SECTION_NUMBER: Final = re.compile(r"\d{1,2}(?:\.\d+)*")
#: An ordered-list item at the left margin, and one nested a level in. Both define subsections of
#: the enclosing numbered heading; see :func:`parse_sections`.
TOP_LEVEL_ITEM: Final = re.compile(r"^(\d{1,2})\.[ \t]")
NESTED_ITEM: Final = re.compile(r"^[ \t]{1,6}(\d{1,2})\.[ \t]")
FENCE: Final = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
#: Separators between members of a section list, and between the ends of a range.
LIST_SEPARATORS: Final[tuple[str, ...]] = (",", "and", "&")
RANGE_SEPARATORS: Final[tuple[str, ...]] = ("-", "–", "—", "to", "through")
#: How far past a section number to look for a separator, and the widest range that may be
#: enumerated. Both are deliberately small: the job is to read a citation, not to parse prose.
LOOKAHEAD: Final = 12
MAX_RANGE: Final = 40


class AllowedUnresolved(NamedTuple):
    """One exactly-scoped exemption for a citation that cannot be resolved."""

    source: str
    decision: str
    section: str
    reason: str
    governing_status: str


#: Exact exceptions: one file, one decision, one section each. No wildcard, no pattern, no
#: directory-wide waiver. Two classes, and the difference between them matters.
#:
#: **Class 1 -- immutable accepted records.** The citation is wrong and the document may not be
#: rewritten. Decision 076 section 7 forbids editing accepted history to make a checker green.
#:
#: **Class 2 -- OPEN DEFECT, awaiting owner correction.** Four live citations in M3.3-I/R source
#: and tests, found by this gate on its first run. They are the same defect class as MIN-A, which
#: swept only Decision 075 citations and so left these standing. Correcting them is not within
#: Decision 076's authorized paths -- MIN-A needed its own owner authorization to change a single
#: docstring -- so they are recorded, reported, and returned to the owner rather than edited here.
#: Every run prints them, so the exemption is loud rather than quiet, and an entry that stops
#: matching fails the gate, so each one disappears from this list only when it is really fixed.
_IMMUTABLE_HISTORY: Final = (
    "immutable accepted record; not rewritten to satisfy a later checker (Decision 076 section 7)"
)
_OPEN_DEFECT: Final = (
    "OPEN DEFECT — reported to the project owner under Decision 076 section 6; correcting live "
    "M3.3-I/R source or tests is outside Decision 076's authorized paths and needs its own "
    "bounded owner authorization, exactly as MIN-A did"
)
ALLOWED_UNRESOLVED: Final[tuple[AllowedUnresolved, ...]] = (
    # ---- Class 2: open defects in the live M3.3-I/R target ----
    AllowedUnresolved(
        source="src/disclosure_drift/m3/execution_rehearsal.py",
        decision="074",
        section="3.1",
        reason=(
            "cites accepted R31, which is Decision 074 section 2 ('Ruling R31 — Reserve "
            "Rehearsal Totality Semantics'); section 3 is R32, a different ruling. The "
            "corrected-E5(a) content the comment describes is section 2.1. Decision 074 has "
            "no section 3.1."
        ),
        governing_status=_OPEN_DEFECT,
    ),
    AllowedUnresolved(
        source="src/disclosure_drift/m3/offline_parse.py",
        decision="071",
        section="13",
        reason=(
            "Decision 071 has sections 1-9 only. The cited R25 is Decision 072 section 5, and "
            "the calendar-source category-C content is Decision 071 section 7."
        ),
        governing_status=_OPEN_DEFECT,
    ),
    AllowedUnresolved(
        source="tests/unit/test_m3_offline_parse.py",
        decision="071",
        section="13",
        reason=(
            "same citation as src/disclosure_drift/m3/offline_parse.py; Decision 071 has "
            "sections 1-9 only."
        ),
        governing_status=_OPEN_DEFECT,
    ),
    AllowedUnresolved(
        source="tests/unit/test_m3_3_boundaries.py",
        decision="071",
        section="11",
        reason=(
            "Decision 071 has sections 1-9 only. No decision record names HttpxTransport and "
            "SecClient as the two construction points, so the intended target is not inferable "
            "from the records and is left for the owner to state."
        ),
        governing_status=_OPEN_DEFECT,
    ),
    # ---- Class 1: wrong citations inside immutable accepted records ----
    AllowedUnresolved(
        source="Docs/Decisions/decision_047_m3_2_t4_operational_preflight_authorization.md",
        decision="032",
        section="6.4",
        reason=(
            "Decision 032 section 6 is prose with no numbered items, so it has no 6.4. Two "
            "occurrences in this record, at lines 20 and 177."
        ),
        governing_status=_IMMUTABLE_HISTORY,
    ),
    AllowedUnresolved(
        source="Docs/Decisions/decision_063_m3_2_cross_namespace_receipt_chain_recovery.md",
        decision="062",
        section="21",
        reason="Decision 062 has sections 1-14; no section 21 exists in any form.",
        governing_status=_IMMUTABLE_HISTORY,
    ),
    AllowedUnresolved(
        source="Docs/Decisions/decision_065_m3_2_final_acceptance_and_closeout.md",
        decision="062",
        section="21",
        reason="Decision 062 has sections 1-14; no section 21 exists in any form.",
        governing_status=_IMMUTABLE_HISTORY,
    ),
    AllowedUnresolved(
        source="Docs/Decisions/decision_registry.md",
        decision="062",
        section="21",
        reason=(
            "the registry reports what Decisions 063 and 065 say, repeating their citation. "
            "Decision 062 has sections 1-14."
        ),
        governing_status=(
            "registry text mirrors the accepted records it indexes; correcting it independently "
            "would make the index disagree with its sources (Decision 076 section 7)"
        ),
    ),
    AllowedUnresolved(
        source="Docs/Decisions/decision_registry.md",
        decision="032",
        section="6.4",
        reason="Decision 032 section 6 is prose with no numbered items, so it has no 6.4.",
        governing_status=(
            "registry text mirrors the accepted records it indexes; correcting it independently "
            "would make the index disagree with its sources (Decision 076 section 7)"
        ),
    ),
    AllowedUnresolved(
        source="Docs/m3/templates/evidence_index.md",
        decision="032",
        section="6.4",
        reason="Decision 032 section 6 is prose with no numbered items, so it has no 6.4.",
        governing_status=_IMMUTABLE_HISTORY,
    ),
    AllowedUnresolved(
        source="Milestones/contracts/m3_2.md",
        decision="065",
        section="20",
        reason="Decision 065 has sections 1-11; no section 20 exists.",
        governing_status=(
            "accepted and closed M3.2 stage contract; Decision 076 does not authorize editing "
            "contracts under Milestones/contracts/"
        ),
    ),
)


class Finding(NamedTuple):
    """One citation naming a section that does not exist."""

    source: str
    line_number: int
    decision: str
    section: str
    detail: str


class Citation(NamedTuple):
    """One resolved section citation and where it was written."""

    line_number: int
    decision: str
    section: str


def repository_root() -> Path:
    """Return the repository root containing this script."""
    return Path(__file__).resolve().parent.parent


def tracked_files(root: Path) -> list[str]:
    """Return in-scope textual paths (tracked or untracked-not-ignored)."""
    completed = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=root,
        capture_output=True,
        check=True,
        text=True,
    )
    return sorted(
        entry
        for entry in completed.stdout.split("\0")
        if entry and Path(entry).suffix.lower() not in BINARY_SUFFIXES
    )


def decision_files(root: Path) -> dict[str, Path]:
    """Map each decision number to its live record, preferring the unsuffixed file."""
    records: dict[str, Path] = {}
    directory = root / DECISIONS_DIR
    if not directory.is_dir():
        return records
    for path in sorted(directory.iterdir()):
        match = DECISION_FILE.match(path.name)
        if match is None:
            continue
        number, _, version_suffix = match.groups()
        # The unsuffixed file is the live record and always wins. An archived `_v0_N` copy fills
        # in only where no unsuffixed file exists, so the outcome does not depend on scan order.
        if version_suffix is None or number not in records:
            records[number] = path
    return records


def _closes(match: re.Match[str] | None, fence: str) -> bool:
    """Whether a fence line terminates the open block of ``fence``."""
    if match is None:
        return False
    marker = match.group(1)
    return marker[0] == fence[0] and len(marker) >= len(fence)


def mask_fenced_blocks(text: str) -> str:
    """Blank every fenced code block, preserving line count and offsets.

    A fence quotes text; it does not cite it. This is what lets an evidence record reproduce a
    historical bad citation verbatim without the gate reading the quotation as a live claim.
    """
    lines = text.split("\n")
    fence: str | None = None
    for index, line in enumerate(lines):
        match = FENCE.match(line)
        if fence is None:
            if match is not None and "`" not in match.group(2):
                fence = match.group(1)
                lines[index] = ""
            continue
        if _closes(match, fence):
            fence = None
        lines[index] = ""
    return "\n".join(lines)


def parse_sections(text: str) -> set[str]:
    """Return every section number a decision record defines, under all three conventions.

    The records use three structures, all three of which are cited, and all three of which were
    inventoried before this function was written:

    1. **Numbered headings.** ``## 14. Owner rulings recorded``, ``### 3.3 MIN-3``,
       ``#### 8.2.1``. The dominant convention and the only one Decision 075 uses.
    2. **Ordered-list items under a numbered heading.** Decision 020 §14 records nine owner
       rulings as list items, and §14.4 is the fourth of them; Decision 021 §19 records eleven
       accepted limitations, and §19.11 is the eleventh. The item's own printed number is used,
       so a list that restarts still maps each citation onto the item a reader would count.
       One level of nesting is followed, which is what makes Decision 057 §5.2.8 resolve.
    3. **Numbered lines inside a fenced verbatim block.** Several records quote the owner's
       instrument whole -- Decision 040 §4 is the instrument, and citations such as Decision 040
       §11 name a section *of that instrument*, which outruns the record's own ten headings.

    Convention 3 is a deliberate widening with a stated cost: in a record that quotes a long
    numbered list, more bare integers count as sections than the record's own headings define, so
    detection there is weaker. It buys the absence of false positives against every record that
    reproduces an owner instrument, which is the trade this gate wants -- a gate that cries wolf
    on accepted history gets switched off, and one that is silent on Decision 075 is useless.
    """
    sections: set[str] = set()
    heading: str | None = None
    item: str | None = None
    fence: str | None = None

    for line in text.split("\n"):
        fence_match = FENCE.match(line)
        if fence is None:
            if fence_match is not None and "`" not in fence_match.group(2):
                fence = fence_match.group(1)
                continue
        else:
            if _closes(fence_match, fence):
                fence = None
            else:
                quoted = TOP_LEVEL_ITEM.match(line)
                if quoted is not None:
                    sections.add(quoted.group(1))
            continue

        head = HEADING.match(line)
        if head is not None:
            heading = head.group(1)
            item = None
            sections.add(heading)
            continue
        if heading is None:
            continue

        top = TOP_LEVEL_ITEM.match(line)
        if top is not None:
            item = top.group(1)
            sections.add(f"{heading}.{item}")
            continue
        nested = NESTED_ITEM.match(line)
        if nested is not None and item is not None:
            sections.add(f"{heading}.{item}.{nested.group(1)}")

    return sections


def _read_section_list(text: str, start: int) -> list[str]:
    """Read one section list beginning at ``start``.

    Returns every section the citation names, expanding integer ranges. Reading stops at the
    first token that is not a section number, so an adjacent sentence is never absorbed.
    """
    sections: list[str] = []
    position = _skip_spaces(text, start)
    while True:
        match = SECTION_NUMBER.match(text, position)
        if match is None:
            break
        current = match.group(0)
        sections.append(current)
        position = match.end()

        # An integer range: "9-11", "15–16", "6 through 8". Only whole-numbered endpoints can be
        # enumerated, and only over a short span, so a stray hyphen in prose cannot invent
        # sections. Anything else ends the list rather than guessing at it.
        consumed = _leading_separator(text[position : position + LOOKAHEAD], RANGE_SEPARATORS)
        if consumed is not None and "." not in current:
            end_match = SECTION_NUMBER.match(text, _skip_spaces(text, position + consumed))
            if end_match is None or "." in end_match.group(0):
                break
            first, last = int(current), int(end_match.group(0))
            if not 0 < last - first <= MAX_RANGE:
                break
            sections.extend(str(value) for value in range(first + 1, last + 1))
            position = end_match.end()

        # A list separator: ",", "and", "&", or the combined ", and".
        consumed = _leading_separator(text[position : position + LOOKAHEAD], LIST_SEPARATORS)
        if consumed is None:
            break
        position = _skip_spaces(text, position + consumed)
        combined = _leading_separator(text[position : position + LOOKAHEAD], LIST_SEPARATORS)
        if combined is not None:
            position = _skip_spaces(text, position + combined)
        # A repeated section mark, as in "sections 4 and §8".
        while position < len(text) and text[position] == "§":
            position = _skip_spaces(text, position + 1)
    return sections


def _skip_spaces(text: str, position: int) -> int:
    """Return the offset of the next non-space, non-tab character."""
    while position < len(text) and text[position] in " \t":
        position += 1
    return position


def _leading_separator(remainder: str, separators: tuple[str, ...]) -> int | None:
    """Return the consumed length if ``remainder`` opens with one of ``separators``."""
    stripped = remainder.lstrip(" \t")
    offset = len(remainder) - len(stripped)
    for separator in sorted(separators, key=len, reverse=True):
        if not stripped.startswith(separator):
            continue
        after = stripped[len(separator) :]
        # A word separator must end at a word boundary; a punctuation one need not.
        if separator[0].isalpha() and after[:1].isalnum():
            continue
        return offset + len(separator)
    return None


def parse_citations(text: str) -> list[Citation]:
    """Return every decision section citation in a document."""
    citations: list[Citation] = []
    for match in CITATION_HEAD.finditer(text):
        line_number = text.count("\n", 0, match.start()) + 1
        for section in _read_section_list(text, _skip_spaces(text, match.end())):
            citations.append(Citation(line_number, match.group(1), section))
    return citations


def check_document(
    source: str, text: str, sections_by_decision: dict[str, set[str]]
) -> list[Finding]:
    """Return findings for one document's citations."""
    scannable = mask_fenced_blocks(text) if source.endswith(".md") else text
    findings: list[Finding] = []
    for citation in parse_citations(scannable):
        known = sections_by_decision.get(citation.decision)
        if known is None:
            findings.append(
                Finding(
                    source,
                    citation.line_number,
                    citation.decision,
                    citation.section,
                    f"no decision record {citation.decision} exists in {DECISIONS_DIR}/",
                )
            )
        elif citation.section not in known:
            findings.append(
                Finding(
                    source,
                    citation.line_number,
                    citation.decision,
                    citation.section,
                    f"decision {citation.decision} defines no section {citation.section}",
                )
            )
    return findings


def _key(finding: Finding) -> tuple[str, str, str]:
    """Return the identity an exception entry is matched on."""
    return (finding.source, finding.decision, finding.section)


def partition(
    findings: list[Finding],
) -> tuple[list[Finding], list[Finding], list[AllowedUnresolved]]:
    """Split findings into unallowed and allowed, and report exceptions that matched nothing."""
    allowed_keys = {(e.source, e.decision, e.section) for e in ALLOWED_UNRESOLVED}
    unallowed = [f for f in findings if (f.source, f.decision, f.section) not in allowed_keys]
    allowed = [f for f in findings if (f.source, f.decision, f.section) in allowed_keys]
    matched = {(f.source, f.decision, f.section) for f in allowed}
    unused = [e for e in ALLOWED_UNRESOLVED if (e.source, e.decision, e.section) not in matched]
    return unallowed, allowed, unused


def scan_repository(root: Path) -> tuple[list[Finding], int, int]:
    """Scan every in-scope file; return findings, citations checked, and records indexed."""
    records = decision_files(root)
    sections_by_decision = {
        number: parse_sections(path.read_text(encoding="utf-8")) for number, path in records.items()
    }

    findings: list[Finding] = []
    checked = 0
    for source in tracked_files(root):
        try:
            text = (root / source).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scannable = mask_fenced_blocks(text) if source.endswith(".md") else text
        checked += len(parse_citations(scannable))
        findings.extend(check_document(source, text, sections_by_decision))
    return findings, checked, len(records)


def main() -> int:
    """Run the citation gate and return a process exit code."""
    root = repository_root()
    findings, checked, records = scan_repository(root)
    unallowed, allowed, unused = partition(sorted(findings))

    if unallowed or unused:
        print(f"Decision section references FAILED: {len(unallowed)} invalid citation(s).")
        for finding in unallowed:
            print(f"  {finding.source}:{finding.line_number}: {finding.detail}")
        for entry in unused:
            print(
                f"  exception matched nothing: {entry.source} -> "
                f"Decision {entry.decision} section {entry.section}"
            )
            print("    the citation it exempts is gone or the entry is wrong; remove or fix it")
        return 1

    print(f"Decision section references passed: {checked} citation(s) against {records} record(s).")
    print(f"Invalid citations: 0. Allowed documented exceptions: {len(allowed)}.")
    reasons = {(e.source, e.decision, e.section): e for e in ALLOWED_UNRESOLVED}
    for finding in allowed:
        entry = reasons[(finding.source, finding.decision, finding.section)]
        marker = "OPEN DEFECT" if entry.governing_status.startswith("OPEN DEFECT") else "historical"
        print(
            f"  allowed ({marker}): {finding.source}:{finding.line_number} -> "
            f"Decision {finding.decision} section {finding.section}"
        )
    open_defects = sum(1 for f in allowed if reasons[_key(f)].governing_status.startswith("OPEN"))
    if open_defects:
        print(
            f"{open_defects} of these are OPEN DEFECTS awaiting owner correction, not accepted "
            "exceptions. See ALLOWED_UNRESOLVED for each one's reason and governing status."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
