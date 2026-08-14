#!/usr/bin/env python3
"""Git target verification helper (Decision 076 section 8).

Every review packet in this project opens by re-running the same eight to ten Git
commands and transcribing their output by hand: branch, HEAD, tree, parent,
``origin/main`` agreement, a tag object, a clean working tree. Hand transcription
is where a baseline claim goes wrong, and a wrong baseline invalidates everything
built on it. This script performs those checks and reports them in a form a
reviewer can cite directly.

It is **read-only by construction**. It runs ``rev-parse``, ``status``,
``rev-list``, and ``diff --name-only`` and nothing else: it never fetches, never
pulls, never checks out, never resets, and never writes to the object store or
the working tree. A check that would require network access is not offered
rather than being offered and skipped.

Nothing milestone-specific is hard-coded. Every expected value is supplied by the
caller, so the script does not age with the milestone that prompted it::

    scripts/verify_target.py \\
        --clean \\
        --branch main \\
        --head 96336cad6f03403e2dfac7aa1e7fe9c030fa8c9e \\
        --tree b87a91b48405408db9b05f7305ebe3eb821a8dbf \\
        --parent 62482e25a047533205bc8810b55fcb5b668ab777 \\
        --head-equals-origin-main \\
        --tag m3.2-complete=2865a1479e4576dc18a4098c928b278812f38d00

Checks run against ``--target``, which defaults to ``HEAD``. The exit status is 0
only when every requested check passes; any mismatch, and any check that cannot
be evaluated, exits nonzero.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Final, NamedTuple

#: Reported in the JSON payload so a consumer can tell which contract produced it.
TOOL_VERSION: Final = "verify-target/1.0"


class Check(NamedTuple):
    """One verification and its outcome."""

    name: str
    expected: str
    observed: str
    passed: bool


class GitError(RuntimeError):
    """A read-only Git query failed."""


def git(repo: Path, *arguments: str) -> str:
    """Run one read-only Git command and return its stripped stdout."""
    completed = subprocess.run(  # noqa: S603
        ["git", *arguments],  # noqa: S607
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        message = f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        raise GitError(message)
    return completed.stdout.strip()


def _resolve(repo: Path, revision: str) -> str:
    """Return the full object id a revision names."""
    return git(repo, "rev-parse", "--verify", revision)


def check_clean(repo: Path) -> Check:
    """Verify the working tree has no staged, unstaged, or untracked change."""
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    return Check("working_tree_clean", "clean", "clean" if not status else "dirty", not status)


def check_equals(name: str, expected: str, observed: str) -> Check:
    """Compare an expected object id against an observed one, allowing an abbreviation."""
    matched = observed.startswith(expected) if expected else False
    return Check(name, expected, observed, matched)


def collect(repo: Path, options: argparse.Namespace) -> list[Check]:
    """Run every requested check and return the results in a stable order."""
    checks: list[Check] = []
    target = _resolve(repo, options.target)

    if options.clean:
        checks.append(check_clean(repo))
    if options.branch is not None:
        checks.append(
            check_equals("branch", options.branch, git(repo, "rev-parse", "--abbrev-ref", "HEAD"))
        )
    if options.head is not None:
        checks.append(check_equals("head", options.head, _resolve(repo, "HEAD")))
    checks.append(Check("target", options.target, target, True))
    if options.tree is not None:
        checks.append(check_equals("tree", options.tree, _resolve(repo, f"{target}^{{tree}}")))
    if options.parent is not None:
        checks.append(check_equals("parent", options.parent, _resolve(repo, f"{target}^")))
    if options.origin_main is not None:
        checks.append(
            check_equals("origin_main", options.origin_main, _resolve(repo, "origin/main"))
        )
    if options.head_equals_origin_main:
        head = _resolve(repo, "HEAD")
        checks.append(check_equals("head_equals_origin_main", head, _resolve(repo, "origin/main")))
    for specification in options.tag or []:
        checks.append(_check_tag(repo, specification))
    if options.child_of is not None:
        parents = git(repo, "rev-list", "--parents", "-n", "1", target).split()[1:]
        expected = _resolve(repo, options.child_of)
        observed = ",".join(parents) if parents else "(root commit)"
        checks.append(Check("child_of", expected, observed, expected in parents))
    if options.changed_paths_under:
        checks.append(_check_changed_paths(repo, target, options.changed_paths_under))
    return checks


def _check_tag(repo: Path, specification: str) -> Check:
    """Verify a tag exists, and that its object id matches when one is given.

    ``--tag name`` asserts only existence. ``--tag name=<sha>`` asserts the id of the tag object
    itself -- for an annotated tag that is the tag object, not the commit it points at, which is
    the distinction a checkpoint claim usually turns on.
    """
    name, _, expected = specification.partition("=")
    try:
        observed = git(repo, "rev-parse", "--verify", name)
    except GitError:
        return Check(f"tag:{name}", expected or "exists", "(absent)", False)
    if not expected:
        return Check(f"tag:{name}", "exists", observed, True)
    return check_equals(f"tag:{name}", expected, observed)


def _check_changed_paths(repo: Path, target: str, prefixes: list[str]) -> Check:
    """Verify every path the target changed against its first parent lies under a given prefix.

    This is the evidence-only assertion: a commit claiming to add nothing but evidence can be
    held to it mechanically instead of by reading the diff.
    """
    changed = [
        line for line in git(repo, "diff", "--name-only", f"{target}^", target).split("\n") if line
    ]
    outside = sorted(path for path in changed if not any(path.startswith(p) for p in prefixes))
    return Check(
        "changed_paths_under",
        ",".join(prefixes),
        f"{len(changed)} changed, {len(outside)} outside" + (f": {outside}" if outside else ""),
        not outside,
    )


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="verify_target.py",
        description="Verify Git baseline invariants read-only. Never fetches, pulls, or mutates.",
    )
    parser.add_argument(
        "--repo", type=Path, default=None, help="repository root (default: this one)"
    )
    parser.add_argument("--target", default="HEAD", help="commit under review (default: HEAD)")
    parser.add_argument("--clean", action="store_true", help="require a clean working tree")
    parser.add_argument("--branch", help="expected current branch name")
    parser.add_argument("--head", help="expected HEAD object id")
    parser.add_argument("--tree", help="expected tree of the target")
    parser.add_argument("--parent", help="expected first parent of the target")
    parser.add_argument("--origin-main", help="expected origin/main object id")
    parser.add_argument(
        "--head-equals-origin-main",
        action="store_true",
        help="require HEAD and origin/main to agree (compares refs already present locally)",
    )
    parser.add_argument(
        "--tag",
        action="append",
        metavar="NAME[=SHA]",
        help="require a tag to exist, and to have this object id when one is given",
    )
    parser.add_argument("--child-of", help="require this commit to be a parent of the target")
    parser.add_argument(
        "--changed-paths-under",
        nargs="+",
        default=[],
        metavar="PREFIX",
        help="require every path the target changed to lie under one of these prefixes",
    )
    parser.add_argument("--json", action="store_true", help="emit the result as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the requested checks and return a process exit code."""
    options = build_parser().parse_args(argv)
    repo = (options.repo or Path(__file__).resolve().parent.parent).resolve()

    try:
        checks = collect(repo, options)
    except GitError as error:
        print(f"verify-target ERROR: {error}", file=sys.stderr)
        return 2

    passed = sum(1 for check in checks if check.passed)
    if options.json:
        print(
            json.dumps(
                {
                    "tool_version": TOOL_VERSION,
                    "repository": str(repo),
                    "passed": passed,
                    "total": len(checks),
                    "ok": passed == len(checks),
                    "checks": [check._asdict() for check in checks],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"verify-target: {passed}/{len(checks)} checks passed")
        for check in checks:
            mark = "PASS" if check.passed else "FAIL"
            print(f"  {mark} {check.name:<24} expected={check.expected} observed={check.observed}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
