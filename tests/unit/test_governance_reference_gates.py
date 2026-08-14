"""Decision 076: behavioural coverage of the two governance reference gates.

`scripts/check_markdown_links.py` (Decision 076 §5) and
`scripts/check_decision_section_refs.py` (Decision 076 §6) are standalone gate scripts rather than
package modules, so they are loaded here by file path, following
`tests/unit/test_repo_hygiene.py`.

Two kinds of test live here. Most are unit tests over synthetic documents, which is what makes the
grammar's boundaries assertable -- that a fence quotes rather than cites, that a year-leading
heading is prose, that reading a section list stops at the first non-number. The last of each group
is a repository invariant: the gate, run against this repository, reports zero unallowed findings.
Those two are the acceptance invariants Decision 076 §5 and §6 state, and they are deliberately
written as `== 0` rather than against a frozen link or citation total, per Decision 076 §12 (P1).

**The MIN-A effectiveness proof** is the point of the second group. It takes a real, currently
valid Decision 075 citation out of live source, substitutes each stale section MIN-A removed, and
asserts the gate rejects what it accepted a moment earlier. The stale citations are assembled at
runtime and never written as literals, because this file is itself scanned by the gate it tests --
a literal would make the repository fail its own gate.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> ModuleType:
    """Load a standalone gate script as an importable module by file path."""
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_links = _load("check_markdown_links")
_refs = _load("check_decision_section_refs")


def _expand(text: str) -> str:
    """Expand this file's citation shorthand: ``@NNN`` and ``@@NNN`` become real citations.

    The shorthand is not decoration. This file is scanned by the gate it tests, so a literal
    citation written here would be a live claim about a decision record -- and the deliberately
    invalid ones these tests need would make the repository fail its own gate. Composing them at
    runtime keeps the test data honest without planting a defect in the tree, and it is why no
    exemption for this file exists in ``ALLOWED_UNRESOLVED``.
    """
    return text.replace("@@", "DECISION ").replace("@", "Decision ")


# --------------------------------------------------------------------------- #
# Markdown link gate -- what counts as a live link
# --------------------------------------------------------------------------- #


def test_masking_preserves_every_offset() -> None:
    """Blanking code must not move a single character, or line numbers would drift."""
    text = "a\n```\n[x](gone.md)\n```\nb `[y](also-gone.md)` c\n"
    masked = _links.mask_code(text)
    assert len(masked) == len(text)
    assert masked.count("\n") == text.count("\n")


def test_a_link_inside_a_fence_is_not_navigation() -> None:
    """A fenced example is displayed, not followed."""
    text = "```\n[x](does-not-exist.md)\n```\n"
    assert _links.extract_links(text) == []


def test_a_link_inside_an_inline_code_span_is_not_navigation() -> None:
    """Markdown does not linkify inside a code span, so neither does this gate."""
    assert _links.extract_links("see `[x](does-not-exist.md)` here") == []


def test_a_code_span_in_the_link_text_still_leaves_the_destination_checkable() -> None:
    """The repository writes ``[`Docs/x.md`](Docs/x.md)`` constantly; masking must not hide it."""
    links = _links.extract_links("[`Docs/x.md`](Docs/x.md)")
    assert [link.target for link in links] == ["Docs/x.md"]


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        ("[a](target.md)", ["target.md"]),
        ("![alt](image.png)", ["image.png"]),
        ('[a](target.md "a title")', ["target.md"]),
        ("[a](<spaced target.md>)", ["spaced target.md"]),
        ("[label]: definition.md", ["definition.md"]),
        ('[label]: definition.md "title"', ["definition.md"]),
        ("[a](nested(paren).md)", ["nested(paren).md"]),
    ],
)
def test_every_supported_link_form_yields_its_destination(
    document: str, expected: list[str]
) -> None:
    """Inline links, images, titles, angle brackets, and reference definitions all resolve."""
    assert [link.target for link in _links.extract_links(document)] == expected


@pytest.mark.parametrize(
    "target",
    ["https://example.com/x", "http://example.com", "mailto:someone@example.com", "//example.com"],
)
def test_external_targets_are_never_resolved_as_paths(target: str) -> None:
    """A scheme or a protocol-relative prefix means the target is not this repository's."""
    assert _links.is_external(target) is True


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        ("Docs/a.md", "b.md", "Docs/b.md"),
        ("Docs/m3/reviews/a.md", "../../Decisions/d.md", "Docs/Decisions/d.md"),
        ("Docs/m3/reviews/a.md", "../../Docs/Decisions/d.md", "Docs/Docs/Decisions/d.md"),
        ("Docs/a.md", "./b.md", "Docs/b.md"),
        ("Docs/a.md", "b.md#anchor", "Docs/b.md"),
        ("Docs/a.md", "sub%20dir/b.md", "Docs/sub dir/b.md"),
        ("Docs/a.md", "/Makefile", "Makefile"),
        ("CLAUDE.md", "../escape.md", ".."),
        ("Docs/a.md", "#anchor-only", None),
    ],
)
def test_targets_resolve_against_the_containing_document(
    source: str, target: str, expected: str | None
) -> None:
    """Resolution is relative to the document, root-relative for a leading slash, anchors aside."""
    assert _links.resolve(source, target) == expected


def test_a_broken_relative_link_is_reported_and_a_good_one_is_not() -> None:
    """The gate's core judgement, on one document with one of each."""
    resolvable = {"Docs", "Docs/real.md"}
    findings, checked = _links.check_document(
        "Docs/a.md", "[good](real.md) and [bad](missing.md)", resolvable
    )
    assert checked == 2
    assert [finding.target for finding in findings] == ["missing.md"]


def test_an_untracked_target_does_not_resolve() -> None:
    """Existence on the author's machine is not resolution; the destination must be tracked."""
    findings, _ = _links.check_document("Docs/a.md", "[x](untracked.md)", {"Docs"})
    assert len(findings) == 1


def test_an_allowlist_entry_matching_nothing_is_surfaced(monkeypatch: pytest.MonkeyPatch) -> None:
    """A standing exemption for a defect that is gone is itself a defect."""
    stale = _links.AllowedBroken("Docs/a.md", "vanished.md", "reason", "status")
    monkeypatch.setattr(_links, "ALLOWED_BROKEN", (stale,))
    unallowed, allowed, unused = _links.partition([])
    assert (unallowed, allowed) == ([], [])
    assert unused == [stale]


def test_an_allowlisted_broken_link_is_allowed_not_hidden(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exempted finding still exists; it moves out of the failing set, not out of sight."""
    entry = _links.AllowedBroken("Docs/a.md", "missing.md", "reason", "status")
    monkeypatch.setattr(_links, "ALLOWED_BROKEN", (entry,))
    finding = _links.Finding("Docs/a.md", 1, "missing.md", "detail")
    unallowed, allowed, unused = _links.partition([finding])
    assert (unallowed, allowed, unused) == ([], [finding], [])


def test_the_repository_has_no_unallowed_broken_links() -> None:
    """Decision 076 §5's acceptance invariant, asserted as zero rather than as a link total."""
    paths = _links.tracked_paths(_REPO_ROOT)
    resolvable = _links.resolvable_paths(paths)
    findings: list[object] = []
    for source in (entry for entry in paths if entry.endswith(".md")):
        document_findings, _ = _links.check_document(
            source, (_REPO_ROOT / source).read_text(encoding="utf-8"), resolvable
        )
        findings.extend(document_findings)
    unallowed, _, unused = _links.partition(sorted(findings))  # type: ignore[arg-type]
    assert unallowed == []
    assert unused == []


# --------------------------------------------------------------------------- #
# Decision section gate -- the three section conventions
# --------------------------------------------------------------------------- #


def test_numbered_headings_are_sections() -> None:
    """Convention 1: the dominant style, at every heading depth the records use."""
    text = "## 1. One\n### 2.1 Two point one\n#### 3.4.5 Deep\n### 7 No trailing dot\n"
    assert _refs.parse_sections(text) == {"1", "2.1", "3.4.5", "7"}


def test_a_heading_opening_with_a_year_is_prose_not_a_section() -> None:
    """Decision 003 writes ``## 2025 maturity gate``; it defines no section 2025."""
    assert _refs.parse_sections("## 2025 maturity gate\n") == set()


def test_ordered_list_items_under_a_heading_are_subsections() -> None:
    """Convention 2: Decision 020 §14.4 is the fourth ruling in its section 14."""
    text = "## 14. Owner rulings\n\n1. First.\n2. Second.\n3. Third.\n4. Fourth.\n"
    assert _refs.parse_sections(text) == {"14", "14.1", "14.2", "14.3", "14.4"}


def test_one_level_of_list_nesting_is_followed() -> None:
    """Convention 2 continued: this is what makes Decision 057 §5.2.8 resolve."""
    text = "## 5. Rulings\n\n1. First.\n2. Second.\n   8. Nested eighth.\n"
    assert "5.2.8" in _refs.parse_sections(text)


def test_numbered_lines_inside_a_verbatim_fence_are_top_level_sections() -> None:
    """Convention 3: Decision 040 §4 quotes an instrument whose own numbering is cited."""
    text = (
        "## 4. The owner instrument (verbatim)\n\n"
        "```text\n11. Path envelope\n19. Obligations\n```\n"
    )
    sections = _refs.parse_sections(text)
    assert {"11", "19"} <= sections


def test_a_record_using_prose_headings_defines_no_sections() -> None:
    """Decisions 001-006 predate the numbered convention, so nothing resolves against them."""
    assert _refs.parse_sections("## Decision\n\n## Reason\n") == set()


# --------------------------------------------------------------------------- #
# Decision section gate -- the citation grammar
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("@075 §3.3", [("075", "3.3")]),
        ("@070 §4", [("070", "4")]),
        ("@016 section 7", [("016", "7")]),
        ("@016 Section 7", [("016", "7")]),
        ("@@062 SECTION 21", [("062", "21")]),
        ("@021 sections 11 and 13", [("021", "11"), ("021", "13")]),
        ("@013 §§7-8", [("013", "7"), ("013", "8")]),
        ("@027 §§15–16", [("027", "15"), ("027", "16")]),
        ("@021 sections 6 through 8", [("021", "6"), ("021", "7"), ("021", "8")]),
        ("@016 §§5, 8", [("016", "5"), ("016", "8")]),
    ],
)
def test_every_citation_form_the_repository_writes_is_read(
    text: str, expected: list[tuple[str, str]]
) -> None:
    """Single, plural, capitalised, listed, and ranged forms all yield their members."""
    assert [(c.decision, c.section) for c in _refs.parse_citations(_expand(text))] == expected


def test_reading_a_section_list_stops_at_the_first_non_number() -> None:
    """Two adjacent citations must not bleed into one another."""
    text = _expand("@013 section 5 and @014 section 1")
    assert [(c.decision, c.section) for c in _refs.parse_citations(text)] == [
        ("013", "5"),
        ("014", "1"),
    ]


def test_a_trailing_word_is_not_absorbed_as_a_section() -> None:
    """``§8 and the rest`` cites section 8 only."""
    citations = _refs.parse_citations(_expand("@024 §8 and the rest"))
    assert [c.section for c in citations] == ["8"]


def test_a_bare_decision_reference_asserts_nothing_about_sections() -> None:
    """Without a section marker there is no claim to check."""
    assert _refs.parse_citations(_expand("@075 is accepted")) == []


def test_a_citation_naming_a_missing_section_is_reported() -> None:
    """The gate's core judgement."""
    findings = _refs.check_document("a.py", _expand("@071 §13"), {"071": {"1", "2"}})
    assert len(findings) == 1
    assert (findings[0].decision, findings[0].section) == ("071", "13")


def test_a_citation_naming_a_record_that_does_not_exist_is_reported() -> None:
    """A citation to an absent decision resolves to nothing at all."""
    findings = _refs.check_document("a.py", _expand("@999 §1"), {"071": {"1"}})
    assert "no decision record 999" in findings[0].detail


def test_a_fenced_citation_in_markdown_is_a_quotation_not_a_claim() -> None:
    """This is what lets an evidence record reproduce a historical bad citation verbatim."""
    text = _expand("```text\n@071 §13\n```\n")
    assert _refs.check_document("Docs/a.md", text, {"071": {"1"}}) == []
    assert len(_refs.check_document("a.py", text, {"071": {"1"}})) == 1


def test_an_exception_matching_nothing_is_surfaced(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exception for a citation that is gone must not linger silently."""
    stale = _refs.AllowedUnresolved("a.py", "071", "13", "reason", "status")
    monkeypatch.setattr(_refs, "ALLOWED_UNRESOLVED", (stale,))
    unallowed, allowed, unused = _refs.partition([])
    assert (unallowed, allowed) == ([], [])
    assert unused == [stale]


def test_the_repository_has_no_invalid_decision_section_references() -> None:
    """Decision 076 §6's acceptance invariant, asserted as zero rather than as a citation total."""
    findings, checked, records = _refs.scan_repository(_REPO_ROOT)
    unallowed, _, unused = _refs.partition(sorted(findings))
    assert unallowed == []
    assert unused == []
    assert checked > 0
    assert records > 0


# --------------------------------------------------------------------------- #
# The MIN-A effectiveness proof
# --------------------------------------------------------------------------- #

#: The section numbers MIN-A removed from Decision 075 citations, assembled at runtime. Writing
#: any of these next to "Decision 075" as a literal would make this file fail the gate it tests.
_MIN_A_STALE_SECTIONS: tuple[str, ...] = ("6", "6.1", "6.2")
_CORRECTED_SECTIONS: tuple[str, ...] = ("3.3", "4")
_DECISION_075 = "075"
_LIVE_CITATION_SOURCE = Path("src/disclosure_drift/m3/execution_rehearsal.py")


def _decision_075_sections() -> set[str]:
    """Return the sections the accepted Decision 075 record actually defines."""
    record = _refs.decision_files(_REPO_ROOT)[_DECISION_075]
    return _refs.parse_sections(record.read_text(encoding="utf-8"))


def test_the_corrected_min_a_sections_exist_in_the_accepted_record() -> None:
    """MIN-A moved the citations onto §3.3 and §4; both must be real."""
    assert set(_CORRECTED_SECTIONS) <= _decision_075_sections()


def test_the_stale_min_a_subsections_do_not_exist() -> None:
    """§6.1 and §6.2 name nothing: Decision 075 §6 has no numbered subsections."""
    sections = _decision_075_sections()
    assert "6.1" not in sections
    assert "6.2" not in sections


def test_bare_section_6_is_a_real_section_and_so_is_structurally_undetectable() -> None:
    """An honest limit, asserted rather than glossed.

    Decision 075 §6 exists -- *OBS-6, the durable mutation-campaign record*. The two bare
    section-6 citations MIN-A corrected were pointing at the wrong section, not at a missing one,
    so an existence gate cannot catch them. Three of the five stale references are detectable
    here; the other two remain a reviewer's job. This test fails if that ever stops being true,
    which is the only way the limitation stays visible.
    """
    assert "6" in _decision_075_sections()


def _live_citation_line() -> str:
    """Return the real source line that currently cites Decision 075 by section."""
    text = (_REPO_ROOT / _LIVE_CITATION_SOURCE).read_text(encoding="utf-8")
    marker = f"Decision {_DECISION_075} §"
    lines = [line for line in text.split("\n") if marker in line]
    assert len(lines) == 1, f"expected exactly one live citation, found {len(lines)}"
    return lines[0]


def test_the_live_citation_passes_the_gate_unmutated() -> None:
    """The control: what the mutation is measured against."""
    sections = _decision_075_sections()
    findings = _refs.check_document(
        str(_LIVE_CITATION_SOURCE), _live_citation_line(), {_DECISION_075: sections}
    )
    assert findings == []


@pytest.mark.parametrize("stale", ["6.1", "6.2"])
def test_reverting_the_live_citation_to_a_stale_min_a_section_fails_the_gate(stale: str) -> None:
    """The effectiveness proof required by Decision 076 §6.

    Take the real corrected citation out of live source, put back the section MIN-A removed, and
    the gate that just passed now reports it. This is what makes the gate a control on the MIN-A
    defect class rather than a plausible-looking script.
    """
    assert stale in _MIN_A_STALE_SECTIONS
    original = _live_citation_line()
    mutated = original.replace(f"§{_CORRECTED_SECTIONS[0]}", f"§{stale}")
    assert mutated != original, "the mutation must actually change the citation"

    sections = _decision_075_sections()
    findings = _refs.check_document(str(_LIVE_CITATION_SOURCE), mutated, {_DECISION_075: sections})
    assert len(findings) == 1
    assert (findings[0].decision, findings[0].section) == (_DECISION_075, stale)
