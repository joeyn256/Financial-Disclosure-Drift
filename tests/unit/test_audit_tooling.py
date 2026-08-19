"""Decision 076: behavioural coverage of the audit tooling.

`scripts/verify_target.py` (Decision 076 §8) and `scripts/dev/mutation_campaign.py`
(Decision 076 §9) are standalone development and audit tools rather than package modules, so they
are loaded here by file path, following `tests/unit/test_repo_hygiene.py`.

Three properties carry most of the weight, because each is a claim the tooling makes about itself
that a reader would otherwise have to take on trust:

* **The mutation runner is not part of the package.** Asserted by searching `src/` for any
  reference to it, so the boundary Decision 076 §9 draws is enforced rather than intended.
* **It refuses the authoritative repository.** Asserted directly against this repository.
* **All 38 definitions recover, and every live anchor but the two superseded ones resolves**
  against the live target. This is the §14 validation invariant kept standing: if M3.3 source
  drifts away from the durable campaign record, that record has stopped describing the executable
  target and this test says so. Both exceptions are ruled on rather than tolerated. Decision 097
  R87 disposes M19: Decision 094 §6.5 deleted the candidate-layer full-index observation query it
  mutates, and Decision 096 R83 moved that invariant to the pre-association E0 projection proved
  in `tests/unit/test_m3_e0.py`. Decision 114 R2 disposes M21: Decision 113 §9 replaced the
  preloaded whole-catalog accession set its anchor is written against with the per-accession
  primary-key lookup accepted Decision 110 §8 requires, which leaves the **R23** §5.1 predicate
  itself unchanged and still proved by `tests/unit/test_m3_offline_parse.py`. Both historical
  definitions and all four KILLED results stand untouched; only applicability to the *current*
  target is superseded, and the partition is asserted exactly, so a third missing anchor is a new
  failure rather than one the two absorb.

Both tools are additionally held to what they must *not* do -- no fetch, no pull, no mutation --
by parsing their source and collecting the subcommand of every Git call they make, rather than by
grepping for words that also occur in ordinary prose.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ARTIFACT = _REPO_ROOT / "Docs/m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md"


def _load(name: str, relative: str) -> ModuleType:
    """Load a standalone tool as an importable module by file path."""
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_verify = _load("verify_target", "scripts/verify_target.py")
_campaign = _load("mutation_campaign", "scripts/dev/mutation_campaign.py")


# --------------------------------------------------------------------------- #
# verify_target -- read-only by construction
# --------------------------------------------------------------------------- #

#: The only Git subcommands the helper may invoke. Every one reads; none reaches the network and
#: none writes. Decision 076 §8 makes read-only a structural property rather than a promise, so
#: this is asserted against the calls the source actually makes.
_READ_ONLY_GIT_SUBCOMMANDS = frozenset({"rev-parse", "status", "rev-list", "diff"})


def _invoked_git_subcommands(relative: str) -> set[str]:
    """Return the subcommand every ``git(repo, ...)`` call in a module names.

    Parsed rather than grepped: a substring search would trip over the *word* "clean" appearing
    as an expected value, and would miss a subcommand built at the call site.
    """
    tree = ast.parse((_REPO_ROOT / relative).read_text(encoding="utf-8"))
    subcommands: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = node.func
        if not isinstance(called, ast.Name) or called.id not in {"git", "_git"}:
            continue
        # Signature is git(repo, *arguments); the subcommand is the first argument after repo.
        assert len(node.args) >= 2, f"unexpected git() call shape at line {node.lineno}"
        first = node.args[1]
        assert isinstance(first, ast.Constant) and isinstance(first.value, str), (
            f"git() subcommand is not a literal at line {node.lineno}"
        )
        subcommands.add(first.value)
    return subcommands


def test_the_target_helper_invokes_only_read_only_git_subcommands() -> None:
    """A helper a reviewer runs against a live baseline must not be able to move it."""
    invoked = _invoked_git_subcommands("scripts/verify_target.py")
    assert invoked, "no git() calls were found; the parser is looking in the wrong place"
    assert invoked <= _READ_ONLY_GIT_SUBCOMMANDS


def test_the_mutation_runner_invokes_only_read_only_git_subcommands() -> None:
    """The runner reads Git for provenance only; restoration never goes through a VCS operation."""
    invoked = _invoked_git_subcommands("scripts/dev/mutation_campaign.py")
    assert invoked <= _READ_ONLY_GIT_SUBCOMMANDS


def test_an_expected_value_may_be_abbreviated() -> None:
    """Reviewers cite short SHAs; a prefix match is a match."""
    assert _verify.check_equals(
        "head", "96336ca", "96336cad6f03403e2dfac7aa1e7fe9c030fa8c9e"
    ).passed


def test_a_mismatched_value_fails() -> None:
    """The whole point: a wrong baseline must not pass quietly."""
    assert _verify.check_equals("head", "deadbeef", "96336cad").passed is False


def test_an_empty_expectation_never_passes_by_accident() -> None:
    """An empty expected value would prefix-match everything; it must not."""
    assert _verify.check_equals("head", "", "96336cad").passed is False


@pytest.fixture
def disposable_repo(tmp_path: Path) -> Path:
    """Return a tiny throwaway Git repository with one commit."""
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)  # noqa: S603, S607
    (tmp_path / "a.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "a.txt"], check=True)  # noqa: S603, S607
    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test",
            "commit",
            "-q",
            "-m",
            "one",
        ],
        check=True,
    )
    return tmp_path


def test_a_clean_tree_is_reported_clean_and_a_dirty_one_is_not(disposable_repo: Path) -> None:
    """Both directions, against a real repository rather than a mocked one."""
    assert _verify.check_clean(disposable_repo).passed is True
    (disposable_repo / "b.txt").write_text("untracked\n", encoding="utf-8")
    assert _verify.check_clean(disposable_repo).passed is False


def test_the_real_head_tree_and_parent_verify_against_this_repository() -> None:
    """The helper agrees with Git about this repository's own shape."""
    head = _verify.git(_REPO_ROOT, "rev-parse", "HEAD")
    tree = _verify.git(_REPO_ROOT, "rev-parse", "HEAD^{tree}")
    options = _verify.build_parser().parse_args(["--head", head, "--tree", tree])
    checks = _verify.collect(_REPO_ROOT, options)
    assert all(check.passed for check in checks), [c for c in checks if not c.passed]


def test_an_absent_tag_fails_rather_than_erroring(disposable_repo: Path) -> None:
    """A missing checkpoint is a finding, not a crash."""
    check = _verify._check_tag(disposable_repo, "no-such-tag=abc123")
    assert check.passed is False
    assert check.observed == "(absent)"


def test_the_helper_exits_nonzero_when_a_check_fails() -> None:
    """The exit status is what a review script actually branches on."""
    assert _verify.main(["--head", "0" * 40]) == 1


# --------------------------------------------------------------------------- #
# mutation_campaign -- recovered, never invented
# --------------------------------------------------------------------------- #


def test_the_runner_is_not_reachable_from_the_package() -> None:
    """Decision 076 §9: mutation tooling is never part of the package runtime."""
    offenders = [
        path.relative_to(_REPO_ROOT)
        for path in (_REPO_ROOT / "src").rglob("*.py")
        if "mutation_campaign" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_the_runner_lives_outside_the_package_tree() -> None:
    """Its location is the other half of the same boundary."""
    assert (_REPO_ROOT / "scripts/dev/mutation_campaign.py").is_file()
    assert not (_REPO_ROOT / "src/disclosure_drift/dev").exists()


def test_every_definition_is_recovered_from_the_durable_record() -> None:
    """All 38, with every field populated -- recovered, never re-invented (Decision 076 §9)."""
    mutations = _campaign.recover_definitions(_ARTIFACT.read_text(encoding="utf-8"))
    assert len(mutations) == 38
    assert [m.mutation_id for m in mutations] == [f"M{n}" for n in range(1, 39)]
    for mutation in mutations:
        assert mutation.governing_rule
        assert mutation.source_path.startswith("src/")
        assert mutation.semantic_locus
        assert mutation.old_anchor.strip()
        assert mutation.replacement.strip()
        assert mutation.old_anchor != mutation.replacement
        assert mutation.expected_test
        assert all(selection.startswith("tests/") for selection in mutation.expected_test)


#: The M1-M38 anchors whose applicability to the *live* target an owner ruling supersedes, in the
#: order ``verify_anchors`` reports them. Every historical definition and every KILLED result
#: remains valid for the frozen target it describes; what moved is the code, not the evidence.
#:
#: * **M19** -- Decision 097 R87. Decision 094 §6.5 deleted the candidate-layer full-index
#:   observation query it mutates, and Decision 096 R83 re-proved that invariant at the
#:   pre-association E0 projection.
#: * **M21** -- Decision 114 R2. Decision 113 §9 replaced the preloaded whole-catalog accession
#:   set its anchor is written against with the per-accession primary-key lookup accepted
#:   Decision 110 §8 requires for memory boundedness. The **R23** §5.1 predicate is unchanged.
#:
#: These are two exact dispositions, not a general exception: each is pinned below by file,
#: locus, and exact anchor text, and the partition is asserted as exact equality.
_SUPERSEDED_LIVE_ANCHORS = ["M19", "M21"]

#: A third anchor, used below to show the exact-equality assertion discriminates by anchor
#: identity rather than merely by count.
_CONTROL_ANCHOR = "M20"

#: The exact query M19 mutates, deleted from the candidate layer by Decision 094 §6.5. Spelled out
#: here rather than read back from the record, so a future edit to *either* one is visible.
_M19_ANCHOR = "\"WHERE o.field_name = 'cik_padded' AND s.source_id = 'sec_full_index_company' \""

#: The exact preloaded-set membership test M21 mutates, replaced by Decision 113 §9 and spelled
#: out for the same reason. ``known`` held one string per catalog accession -- roughly 21.5
#: million strings and about 2.9 GB on E0's first planned source -- which is the whole-catalog
#: preload accepted Decision 110 §8 required removed.
_M21_ANCHOR = (
    "            if plain not in known:\n"
    "                unbound.add(plain)\n"
    "                continue"
)

#: The live form of that same predicate. The canonical row is fetched by primary key instead, and
#: an accession the authoritative layer does not carry is still reported and skipped -- never
#: created. This is the **R23** §5.1 behaviour M21 covers, asserted against the shipped parser.
_M21_LIVE_PREDICATE = (
    "            if canonical is None:\n"
    "                unbound.add(plain)\n"
    "                continue"
)


def _mirrored_target(root: Path, relatives: set[str]) -> Path:
    """Mirror the campaign's target files into a disposable tree and return its root.

    ``verify_anchors`` resolves every definition's target file relative to the tree it is handed,
    so a mirror is what lets deliberate drift be exercised below without touching -- or needing to
    restore -- the authoritative repository.
    """
    for relative in sorted(relatives):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            (_REPO_ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8"
        )
    return root


def test_every_live_anchor_but_the_two_superseded_ones_resolves_against_the_live_target(
    tmp_path: Path,
) -> None:
    """Decision 076 §9's recovered definitions, held against the target they describe.

    A failure here does not mean the runner broke. It means the durable campaign record has
    stopped describing the executable target -- which is exactly the fact a reviewer needs before
    trusting any inherited campaign result.

    Exactly two anchors have legitimately stopped describing it, each disposed by its own owner
    ruling. Decision 097 R87 disposes M19, which mutates a candidate-layer full-index observation
    query that Decision 094 §6.5 deleted in favour of the canonical ``census_accession_registrants``
    relation plus ``registrant_set_completeness``, and whose invariant Decision 096 R83 re-proved at
    the pre-association E0 projection. Decision 114 R2 disposes M21, which mutates the preloaded
    whole-catalog accession set that Decision 113 §9 replaced with the per-accession primary-key
    lookup accepted Decision 110 §8 requires; its **R23** §5.1 predicate -- an index-only accession
    is *reported*, never manufactured -- is unchanged, and is asserted below against both the
    shipped parser and the killing test the definition itself names.

    So the truthful live partition is 38 definitions recovered, 36 anchors resolved,
    ``['M19', 'M21']`` superseded, and nothing else missing -- and that is asserted as exact
    equality, not as a tolerated exception.
    """
    mutations = _campaign.recover_definitions(_ARTIFACT.read_text(encoding="utf-8"))
    definitions = {mutation.mutation_id: mutation for mutation in mutations}

    # Every historical definition still recovers, in order: the supersessions below are statements
    # about two anchors' targets, and say nothing about the record's completeness.
    assert [mutation.mutation_id for mutation in mutations] == [f"M{n}" for n in range(1, 39)]

    # The live partition itself.
    assert _campaign.verify_anchors(_REPO_ROOT, mutations) == _SUPERSEDED_LIVE_ANCHORS

    # Both are pinned by file, locus, and the exact anchor text -- so a renamed, relocated, or
    # rewritten anchor cannot quietly inherit either disposition.
    m19 = definitions["M19"]
    assert m19.source_path == "src/disclosure_drift/m3/candidate_snapshot.py"
    assert "_read_full_index_registrants" in m19.semantic_locus
    assert m19.old_anchor == _M19_ANCHOR

    m21 = definitions["M21"]
    assert m21.source_path == "src/disclosure_drift/m3/offline_parse.py"
    assert "_materialize_full_index_registrants" in m21.semantic_locus
    assert m21.old_anchor == _M21_ANCHOR
    assert m21.expected_test == ("tests/unit/test_m3_offline_parse.py",)

    # M19's reason is Decision 094 §6.5's deletion, not drift: the removed fallback is gone from
    # the live candidate builder, and the canonical consumer source it was replaced by is present.
    builder = (_REPO_ROOT / m19.source_path).read_text(encoding="utf-8")
    assert "_read_full_index_registrants" not in builder
    assert _M19_ANCHOR not in builder
    assert "sec_full_index_company" not in builder
    assert "census_accession_registrants" in builder
    assert "registrant_set_completeness" in builder

    # M21's reason is Decision 113 §9's memory-bounded rewrite, not drift. The whole-catalog
    # preload is gone, the per-accession primary-key lookup that replaced it is present, and the
    # **R23** §5.1 predicate M21 covers is still written in the live parser.
    parser = (_REPO_ROOT / m21.source_path).read_text(encoding="utf-8")
    assert _M21_ANCHOR not in parser
    assert "not in known" not in parser
    assert "FROM census_accessions WHERE accession_plain = ?" in parser
    assert _M21_LIVE_PREDICATE in parser

    # ...and the killing test M21's own definition names still holds that predicate directly, so
    # the invariant is covered by a live proof rather than only by a superseded anchor.
    proof = (_REPO_ROOT / m21.expected_test[0]).read_text(encoding="utf-8")
    assert "def test_an_index_only_accession_is_reported_and_never_created" in proof

    # Neither ruling creates a generic missing-anchor exception, so the equality above must reject
    # any *other* or *additional* missing anchor. Exercised against a disposable mirror, which
    # first reproduces the live partition and is then deliberately drifted by one anchor.
    mirror = _mirrored_target(tmp_path / "mirror", {m.source_path for m in mutations})
    assert _campaign.verify_anchors(mirror, mutations) == _SUPERSEDED_LIVE_ANCHORS

    control = definitions[_CONTROL_ANCHOR]
    drifted = mirror / control.source_path
    drifted.write_text(
        drifted.read_text(encoding="utf-8").replace(control.old_anchor, "", 1), encoding="utf-8"
    )

    # One anchor missing *in addition* to the two superseded ones.
    additional = _campaign.verify_anchors(mirror, mutations)
    assert additional == ["M19", _CONTROL_ANCHOR, "M21"]
    assert additional != _SUPERSEDED_LIVE_ANCHORS

    # Dropping one superseded definition leaves the other plus the control: the same length as the
    # live partition and different identities, so this proves the assertion discriminates by
    # identity and not by length.
    different = _campaign.verify_anchors(mirror, [m for m in mutations if m.mutation_id != "M19"])
    assert different == [_CONTROL_ANCHOR, "M21"]
    assert different != _SUPERSEDED_LIVE_ANCHORS


def test_a_block_missing_a_field_is_not_durably_recoverable() -> None:
    """A partial definition is the fabricated fact Decision 075 §6 prohibits."""
    block = "### M1 — a mutation\n\n| Field | Value |\n|---|---|\n| Mutation ID | **M1** |\n"
    with pytest.raises(_campaign.RecoveryError, match="NOT_DURABLY_RECOVERABLE"):
        _campaign.recover_definitions(block)


def test_a_block_missing_its_code_fences_is_not_durably_recoverable() -> None:
    """Both halves of the edit must be present verbatim or the definition is not recovered."""
    block = (
        "### M1 — a mutation\n\n"
        "| Field | Value |\n|---|---|\n"
        "| Mutation ID | **M1** |\n"
        "| Governing rule | **R19** |\n"
        "| Target file | `src/x.py` |\n"
        "| Semantic locus | module scope |\n"
        "| Expected killing test selection | `tests/unit/test_x.py` |\n\n"
        "Exact mutation applied — the first occurrence of\n\nis replaced by\n"
    )
    with pytest.raises(_campaign.RecoveryError, match="NOT_DURABLY_RECOVERABLE"):
        _campaign.recover_definitions(block)


def test_the_authoritative_repository_is_refused() -> None:
    """Decision 076 §9: a disposable target is the default, and in-place must be explicit."""
    with pytest.raises(SystemExit, match="refusing to mutate the authoritative repository"):
        _campaign.guard_target(_REPO_ROOT, allow_in_place=False)


def test_a_disposable_target_is_permitted(tmp_path: Path) -> None:
    """The guard refuses one specific tree, not every tree."""
    _campaign.guard_target(tmp_path, allow_in_place=False)


def test_the_subprocess_environment_puts_the_target_source_first(tmp_path: Path) -> None:
    """A clone only wins over the editable install when its ``src`` leads ``PYTHONPATH``."""
    environment = _campaign.subprocess_environment(tmp_path)
    assert environment["PYTHONPATH"].split(":")[0] == str(tmp_path / "src")
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"


# --------------------------------------------------------------------------- #
# mutation_campaign -- the machine-readable payload
# --------------------------------------------------------------------------- #


def _sample_payload() -> dict[str, object]:
    """Build a payload over the real definitions without executing anything."""
    mutations = _campaign.recover_definitions(_ARTIFACT.read_text(encoding="utf-8"))
    outcomes = [_campaign.Outcome(mutation, "KILLED", False) for mutation in mutations]
    return _campaign.payload(
        _REPO_ROOT,
        _ARTIFACT,
        mutations,
        outcomes,
        {"module": "m", "resolved_path": "p", "inside_target": True},
        {"executed": True, "selections": [], "all_passed": True},
        {"checked": 11, "residual": 0, "paths": []},
        [],
    )


def test_the_payload_carries_every_field_decision_076_requires() -> None:
    """Decision 076 §9's schema, asserted field by field rather than by eye."""
    document = _sample_payload()
    assert set(document) == {
        "campaign_version",
        "runner_version",
        "target_root",
        "target_sha",
        "target_tree",
        "artifact",
        "definitions_recovered",
        "anchors_resolved",
        "anchors_missing",
        "source_isolation",
        "positive_control",
        "residue_result",
        "summary",
        "mutations",
    }
    assert set(document["mutations"][0]) == {  # type: ignore[index]
        "mutation_id",
        "governing_rule",
        "source_path",
        "semantic_locus",
        "old_anchor",
        "replacement",
        "expected_test",
        "result",
        "survivor",
    }


#: Key names that would carry a clock reading. Matched as whole underscore-delimited words, so
#: ``paths`` and ``mutations`` are not mistaken for ``at`` and ``time``.
_CLOCK_WORDS = frozenset(
    {"time", "timestamp", "date", "datetime", "started", "finished", "when", "at", "clock", "epoch"}
)


def test_the_payload_carries_no_wall_clock_reading() -> None:
    """Decision 076 §9 keeps clock readings out, which is also what makes runs comparable."""
    offenders = sorted(
        key for key in _all_keys(_sample_payload()) if set(key.lower().split("_")) & _CLOCK_WORDS
    )
    assert offenders == []


def _all_keys(value: object) -> set[str]:
    """Return every mapping key anywhere in a nested structure."""
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _all_keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _all_keys(item)}
    return set()


def test_the_payload_is_deterministic_and_serialisable() -> None:
    """Two builds over the same target must be byte-identical, so runs can be diffed."""
    first = json.dumps(_sample_payload(), indent=2, sort_keys=True)
    second = json.dumps(_sample_payload(), indent=2, sort_keys=True)
    assert first == second
    assert json.loads(first)["definitions_recovered"] == 38
