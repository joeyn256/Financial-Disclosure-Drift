#!/usr/bin/env python3
"""M3.3-I/R mutation-campaign runner (Decision 076 section 9).

Reconstructs the M1-M38 campaign from its own durable record and re-executes any
subset of it against an explicitly supplied target, emitting machine-readable
JSON beside the existing Markdown artifact.

**This file is development and audit tooling. It is not part of the package.**
It lives under ``scripts/dev/`` rather than ``src/disclosure_drift/`` and is
never imported by production code; ``tests/unit/test_audit_tooling.py`` asserts
that, so the boundary is enforced rather than merely intended.

**Definitions are recovered, never invented.** Decision 075 section 6 forbids
fabricating a mutation definition, so every mutation's governing rule, target
file, semantic locus, exact anchor, exact replacement, and killing test
selection is parsed out of
``Docs/m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md``. That artifact is read
and never written. A mutation whose definition cannot be parsed exactly is
reported ``NOT_DURABLY_RECOVERABLE`` and stops the run for owner referral rather
than being guessed at.

**Safety, in the order the run enforces it.**

1. ``--target`` is required and names the tree to mutate. The authoritative
   repository -- the one containing this script -- is **refused** unless
   ``--allow-in-place`` is passed *and* its working tree is clean, so a
   disposable clone is the default and mutating real work in progress is not
   reachable by accident.
2. **Source isolation** is proved, not assumed. A probe subprocess imports a
   package module under the same environment the test subprocesses will use and
   reports the file it resolved. Unless that file lies inside the target tree,
   the run aborts -- otherwise the campaign would mutate one tree and test
   another, and every "kill" would be meaningless. This matters here because the
   package is installed editable from the authoritative repository, so a clone
   only wins when ``PYTHONPATH`` puts it first.
3. **Entry digests** are taken for every file any selected mutation touches, and
   the original bytes are held in memory for the whole run.
4. Each mutation writes inside ``try`` / ``finally``, and the ``finally``
   restores from those in-memory bytes -- not from a re-read, a backup file, or
   any VCS operation -- so a raising test cannot leave a mutation in place.
5. A **residue check** recomputes every touched file's digest at the end and
   fails the run on any mismatch.

A mutation is **KILLED** when its designated test selection fails, and a
**SURVIVOR** when it passes. An anchor that is absent is never silently skipped:
it is reported and counted as a survivor, so a stale definition can never be
mistaken for a kill.

**No wall-clock timestamp appears in the JSON.** Decision 076 section 9 keeps
clock readings out of governed deterministic identity, and omitting them also
makes two runs over the same target byte-comparable. The JSON is audit evidence;
it is never selection methodology.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Final, NamedTuple

CAMPAIGN_VERSION: Final = "m3.3-i-r-mutation-campaign/M1-M38"
RUNNER_VERSION: Final = "mutation-campaign-runner/1.0"
DEFAULT_ARTIFACT: Final = "Docs/m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md"
#: A module that exists only in this package, used to prove which tree the tests will import.
ISOLATION_PROBE_MODULE: Final = "disclosure_drift.m3.candidate_events"

MUTATION_HEADING: Final = re.compile(r"^### (M\d+) — (.+)$", re.MULTILINE)
TABLE_ROW: Final = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", re.MULTILINE)
PYTHON_FENCE: Final = re.compile(r"```python\n(.*?)\n```", re.DOTALL)
ANCHOR_MARKER: Final = "the first occurrence of"
REPLACEMENT_MARKER: Final = "is replaced by"


class RecoveryError(RuntimeError):
    """A mutation definition could not be recovered exactly from the durable record."""


class Mutation(NamedTuple):
    """One recovered mutation definition."""

    mutation_id: str
    description: str
    governing_rule: str
    source_path: str
    semantic_locus: str
    old_anchor: str
    replacement: str
    expected_test: tuple[str, ...]


class Outcome(NamedTuple):
    """The observed result of one mutation."""

    mutation: Mutation
    result: str
    survivor: bool | None


def _plain(value: str) -> str:
    """Strip the Markdown emphasis and code ticks the record's tables carry."""
    return value.replace("**", "").replace("`", "").strip()


def recover_definitions(text: str) -> list[Mutation]:
    """Parse every mutation definition out of the durable campaign record.

    Strict by intent: a block missing any field, or missing either of its two code fences, raises
    rather than yielding a partial definition. A partially recovered mutation is exactly the
    fabricated fact Decision 075 section 6 prohibits.
    """
    headings = list(MUTATION_HEADING.finditer(text))
    if not headings:
        message = "no mutation sections found in the campaign record"
        raise RecoveryError(message)

    mutations: list[Mutation] = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        block = text[heading.start() : end]
        identifier = heading.group(1)
        fields = {_plain(key): value for key, value in TABLE_ROW.findall(block)}

        try:
            source_path = _plain(fields["Target file"])
            governing_rule = _plain(fields["Governing rule"])
            semantic_locus = _plain(fields["Semantic locus"])
            selection = _plain(fields["Expected killing test selection"]).split()
        except KeyError as error:
            message = f"{identifier}: NOT_DURABLY_RECOVERABLE — missing field {error}"
            raise RecoveryError(message) from error

        old_anchor, replacement = _recover_edit(identifier, block)
        mutations.append(
            Mutation(
                mutation_id=identifier,
                description=heading.group(2).strip(),
                governing_rule=governing_rule,
                source_path=source_path,
                semantic_locus=semantic_locus,
                old_anchor=old_anchor,
                replacement=replacement,
                expected_test=tuple(selection),
            )
        )
    return mutations


def _recover_edit(identifier: str, block: str) -> tuple[str, str]:
    """Return the exact anchor and replacement for one mutation block."""
    anchor_at = block.find(ANCHOR_MARKER)
    replaced_at = block.find(REPLACEMENT_MARKER, anchor_at + 1)
    if anchor_at == -1 or replaced_at == -1:
        message = f"{identifier}: NOT_DURABLY_RECOVERABLE — edit markers absent"
        raise RecoveryError(message)
    old = PYTHON_FENCE.search(block, anchor_at)
    new = PYTHON_FENCE.search(block, replaced_at)
    if old is None or new is None or old.start() >= replaced_at:
        message = f"{identifier}: NOT_DURABLY_RECOVERABLE — code fences absent or out of order"
        raise RecoveryError(message)
    return old.group(1), new.group(1)


def digest(path: Path) -> str:
    """Return a file's SHA-256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authoritative_root() -> Path:
    """Return the repository this script lives in."""
    return Path(__file__).resolve().parent.parent.parent


def _git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(  # noqa: S603
        ["git", *arguments],  # noqa: S607
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def guard_target(target: Path, allow_in_place: bool) -> None:
    """Refuse to mutate the authoritative repository unless explicitly and safely permitted."""
    if target.resolve() != authoritative_root():
        return
    if not allow_in_place:
        message = (
            f"refusing to mutate the authoritative repository at {target}. Clone it to a "
            "disposable location and pass that as --target, or pass --allow-in-place if you "
            "genuinely mean to mutate this tree in place."
        )
        raise SystemExit(message)
    if _git(target, "status", "--porcelain=v1", "--untracked-files=all"):
        message = (
            "refusing --allow-in-place with a dirty working tree: restoration is only verifiable "
            "against a clean baseline. Commit or stash first."
        )
        raise SystemExit(message)


def subprocess_environment(target: Path) -> dict[str, str]:
    """Return the environment every probe and test subprocess runs under.

    ``PYTHONPATH`` puts the target's ``src`` first so a disposable clone wins over the editable
    install of the authoritative repository. ``PYTHONDONTWRITEBYTECODE`` stops a restored file
    from being shadowed by a stale ``.pyc`` that collides with it on ``(mtime, size)``.
    """
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    source_root = str(target / "src")
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = f"{source_root}{os.pathsep}{existing}" if existing else source_root
    return environment


def prove_source_isolation(target: Path, python: str) -> dict[str, object]:
    """Prove the tests will import the tree this run is about to mutate."""
    completed = subprocess.run(  # noqa: S603
        [python, "-c", f"import {ISOLATION_PROBE_MODULE} as m; print(m.__file__)"],
        cwd=target,
        env=subprocess_environment(target),
        capture_output=True,
        text=True,
        check=False,
    )
    resolved = completed.stdout.strip()
    inside = bool(resolved) and Path(resolved).resolve().is_relative_to(target.resolve())
    if not inside:
        message = (
            f"source isolation FAILED: {ISOLATION_PROBE_MODULE} resolved to {resolved or '(none)'}"
            f", which is outside the target {target}. Every result would describe a tree this run "
            "is not mutating."
        )
        raise SystemExit(message)
    return {"module": ISOLATION_PROBE_MODULE, "resolved_path": resolved, "inside_target": True}


def run_selection(target: Path, python: str, selection: tuple[str, ...]) -> bool:
    """Run one pytest selection; return whether it passed."""
    completed = subprocess.run(  # noqa: S603
        [python, "-m", "pytest", "-x", "-q", "--no-header", "-p", "no:cacheprovider", *selection],
        cwd=target,
        env=subprocess_environment(target),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def positive_control(target: Path, python: str, mutations: list[Mutation]) -> dict[str, object]:
    """Run every distinct selection against unmutated source before any mutation is applied.

    A selection that was already red would otherwise be miscounted as a kill by every mutation
    that uses it. Any failure here aborts before a single byte is changed.
    """
    selections = sorted({mutation.expected_test for mutation in mutations})
    results = {
        " ".join(selection): run_selection(target, python, selection) for selection in selections
    }
    failed = sorted(name for name, passed in results.items() if not passed)
    if failed:
        message = f"positive control FAILED before any mutation was applied: {failed}"
        raise SystemExit(message)
    return {"executed": True, "selections": sorted(results), "all_passed": True}


def execute(
    target: Path, python: str, mutations: list[Mutation], selected: list[Mutation]
) -> tuple[list[Outcome], dict[str, object]]:
    """Apply each selected mutation in isolation, restore it, and check for residue."""
    touched = sorted({mutation.source_path for mutation in selected})
    originals = {path: (target / path).read_bytes() for path in touched}
    entry_digests = {path: hashlib.sha256(data).hexdigest() for path, data in originals.items()}

    chosen = {mutation.mutation_id for mutation in selected}
    outcomes: list[Outcome] = []
    for mutation in mutations:
        if mutation.mutation_id not in chosen:
            outcomes.append(Outcome(mutation, "NOT_RUN", None))
            continue
        outcomes.append(_apply_one(target, python, mutation, originals))

    residual = sorted(path for path in touched if digest(target / path) != entry_digests[path])
    residue = {"checked": len(touched), "residual": len(residual), "paths": residual}
    if residual:
        message = f"RESIDUE: {residual} did not return to their entry digests"
        raise SystemExit(message)
    return outcomes, residue


def _apply_one(
    target: Path, python: str, mutation: Mutation, originals: dict[str, bytes]
) -> Outcome:
    """Apply one mutation, run its killing selection, and restore unconditionally."""
    path = target / mutation.source_path
    text = originals[mutation.source_path].decode("utf-8")
    if mutation.old_anchor not in text:
        # Never a silent skip: an absent anchor means the definition no longer describes the
        # source, which is a survivor-grade fact, not a pass.
        return Outcome(mutation, "SKIP_ANCHOR_NOT_FOUND", True)

    mutated = text.replace(mutation.old_anchor, mutation.replacement, 1)
    try:
        path.write_text(mutated, encoding="utf-8")
        passed = run_selection(target, python, mutation.expected_test)
    finally:
        path.write_bytes(originals[mutation.source_path])
    return Outcome(mutation, "SURVIVOR" if passed else "KILLED", passed)


def verify_anchors(target: Path, mutations: list[Mutation]) -> list[str]:
    """Return the ids of every mutation whose anchor is absent from the target source."""
    cache: dict[str, str] = {}
    missing: list[str] = []
    for mutation in mutations:
        if mutation.source_path not in cache:
            source = target / mutation.source_path
            cache[mutation.source_path] = (
                source.read_text(encoding="utf-8") if source.is_file() else ""
            )
        if mutation.old_anchor not in cache[mutation.source_path]:
            missing.append(mutation.mutation_id)
    return missing


def payload(
    target: Path,
    artifact: Path,
    mutations: list[Mutation],
    outcomes: list[Outcome],
    isolation: dict[str, object],
    control: dict[str, object],
    residue: dict[str, object],
    missing_anchors: list[str],
) -> dict[str, object]:
    """Build the deterministic machine-readable campaign payload."""
    return {
        "campaign_version": CAMPAIGN_VERSION,
        "runner_version": RUNNER_VERSION,
        "target_root": str(target),
        "target_sha": _git(target, "rev-parse", "HEAD"),
        "target_tree": _git(target, "rev-parse", "HEAD^{tree}"),
        "artifact": {"path": str(artifact), "sha256": digest(artifact)},
        "definitions_recovered": len(mutations),
        "anchors_resolved": len(mutations) - len(missing_anchors),
        "anchors_missing": missing_anchors,
        "source_isolation": isolation,
        "positive_control": control,
        "residue_result": residue,
        "summary": {
            "killed": sum(1 for o in outcomes if o.result == "KILLED"),
            "survivors": sum(1 for o in outcomes if o.survivor is True),
            "not_run": sum(1 for o in outcomes if o.result == "NOT_RUN"),
        },
        "mutations": [
            {
                "mutation_id": outcome.mutation.mutation_id,
                "governing_rule": outcome.mutation.governing_rule,
                "source_path": outcome.mutation.source_path,
                "semantic_locus": outcome.mutation.semantic_locus,
                "old_anchor": outcome.mutation.old_anchor,
                "replacement": outcome.mutation.replacement,
                "expected_test": list(outcome.mutation.expected_test),
                "result": outcome.result,
                "survivor": outcome.survivor,
            }
            for outcome in outcomes
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="mutation_campaign.py",
        description=(
            "Re-execute the recovered M1-M38 mutation campaign against an explicitly supplied "
            "target. Development and audit tooling; never imported by the package."
        ),
    )
    parser.add_argument("--target", type=Path, required=True, help="tree to mutate (a clone)")
    parser.add_argument(
        "--artifact", type=Path, help=f"campaign record (default: {DEFAULT_ARTIFACT})"
    )
    parser.add_argument(
        "--select", default="", help="comma-separated mutation ids to execute, e.g. M1,M32,M38"
    )
    parser.add_argument("--all", action="store_true", help="execute every recovered mutation")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="recover definitions and resolve anchors without executing anything",
    )
    parser.add_argument(
        "--skip-positive-control", action="store_true", help="do not run the control selections"
    )
    parser.add_argument(
        "--allow-in-place",
        action="store_true",
        help="permit mutating the authoritative repository (requires a clean working tree)",
    )
    parser.add_argument("--json", type=Path, help="write the machine-readable payload here")
    parser.add_argument("--python", default=sys.executable, help="interpreter for subprocesses")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the campaign and return a process exit code."""
    options = build_parser().parse_args(argv)
    target = options.target.resolve()
    if not (target / "src" / "disclosure_drift").is_dir():
        print(f"target {target} does not look like this repository", file=sys.stderr)
        return 2
    guard_target(target, options.allow_in_place)

    artifact = options.artifact or target / DEFAULT_ARTIFACT
    try:
        mutations = recover_definitions(artifact.read_text(encoding="utf-8"))
    except (RecoveryError, OSError) as error:
        print(f"campaign recovery FAILED: {error}", file=sys.stderr)
        return 2

    missing = verify_anchors(target, mutations)
    print(
        f"recovered {len(mutations)} definitions; anchors resolved "
        f"{len(mutations) - len(missing)}/{len(mutations)}"
    )
    if missing:
        print(f"  anchors NOT resolved: {missing}")

    selected: list[Mutation] = []
    if not options.verify_only:
        requested = {name.strip() for name in options.select.split(",") if name.strip()}
        selected = [m for m in mutations if options.all or m.mutation_id in requested]
        unknown = requested - {m.mutation_id for m in mutations}
        if unknown:
            print(f"unknown mutation ids: {sorted(unknown)}", file=sys.stderr)
            return 2

    isolation: dict[str, object] = {"executed": False}
    control: dict[str, object] = {"executed": False}
    residue: dict[str, object] = {"checked": 0, "residual": 0, "paths": []}
    outcomes = [Outcome(m, "NOT_RUN", None) for m in mutations]

    if selected:
        isolation = prove_source_isolation(target, options.python)
        print(f"source isolation proved: {isolation['resolved_path']}")
        if not options.skip_positive_control:
            control = positive_control(target, options.python, selected)
            print(f"positive control: {len(control['selections'])} selection(s), all PASS")
        outcomes, residue = execute(target, options.python, mutations, selected)
        for outcome in outcomes:
            if outcome.result != "NOT_RUN":
                print(f"  {outcome.mutation.mutation_id}: {outcome.result}")
        print(f"residue: {residue['residual']} residual of {residue['checked']} touched file(s)")

    if options.json is not None:
        document = payload(
            target, artifact, mutations, outcomes, isolation, control, residue, missing
        )
        options.json.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", "utf-8")
        print(f"wrote {options.json}")

    survivors = [o.mutation.mutation_id for o in outcomes if o.survivor is True]
    if missing or survivors:
        print(f"FAILED: missing anchors {missing}, survivors {survivors}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
