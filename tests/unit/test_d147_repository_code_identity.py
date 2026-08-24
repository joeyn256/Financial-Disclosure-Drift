"""Decision 147 — genuine repository code identity, proved against real Git repositories.

**What is under test, and why it exists.** Accepted Decision 145 §12 claimed that its continuity
mechanism prevented, *mechanically*, "a process continuing from a revision whose governing
semantics moved". The independent review Decision 145 itself required found that claim false and
recorded it as **D146-MAJOR-1**: the digest bound ten frozen constants plus
`disclosure_drift.__version__`, the literal `"0.1.0"`, moved by exactly one commit in the whole
history. The review proved it by mutation -- an accepted capacity floor relaxed `60 -> 1` GiB and an
admission guard deleted outright left the digest bit-identical. The owner sustained the finding and
chose the remedy: bind a genuine code identity. This file is the proof that it is genuine.

**The organising rule, and the reason this file exists separately.** D146 also recorded that the
D145 test named `test_a_successor_refuses_a_changed_code_revision` established the property only for
a version string that never moves -- a positive control that could not fail for the right reason.
So **nothing here is proved by a fake SHA**. The identity mechanism is exercised against real
temporary Git repositories with real commits, real trees, real dirty states and real untracked
files; the cross-phase refusals are driven through the production entry points; and the end-to-end
refusals run in real child processes, from real published checkouts, through the real operator
command. The pinned identity in `test_d145_phase_restart.py` is legitimate downstream fixture
precisely *because* this file exists.

**What it does not do.** It runs no canary, mints no authority, enables no network switch, creates
no migration, and touches the operator's real checkout in no way at all: every repository it commits
to is one it created under `tmp_path` and abandons.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d116_single_source_canary as d116  # noqa: E402
import test_d144_first_canary_transport_narrowing as d144  # noqa: E402
import test_d145_phase_restart as d145  # noqa: E402

from disclosure_drift.config import EVIDENCE_ROOT_ENV  # noqa: E402
from disclosure_drift.m3 import canary_phases as phases  # noqa: E402
from disclosure_drift.m3 import canary_runtime as runtime  # noqa: E402
from disclosure_drift.m3 import dock_transport as dt  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import repository_identity as ri  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402

_BULK = d116._BULK_INSTANCE
_QUALIFIED = ewr.QUALIFIED_EXTERNAL_VOLUME_UUID
_OTHER_UUID = "0BADCAFE-0000-0000-0000-000000000000"


# ==========================================================================
# Disposable real repositories
# ==========================================================================
def _git(root: Path, *arguments: str) -> str:
    """One Git command against a repository this test created, and its output."""
    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, test-owned repository
        ["git", "-C", str(root), *arguments],  # noqa: S607
        check=True,
        capture_output=True,
        timeout=120,
    )
    return completed.stdout.decode("utf-8").strip()


def _repository(root: Path, *, name: str = "repo") -> Path:
    """A real, empty Git repository with one committed governing file."""
    repository = root / name
    (repository / "src" / "disclosure_drift" / "m3").mkdir(parents=True)
    _governing(repository).write_text("GOVERNING = 1\n", encoding="utf-8")
    _git(repository, "init")
    _git(repository, "config", "user.email", "d147@example.invalid")
    _git(repository, "config", "user.name", "Decision 147 fixture")
    _git(repository, "config", "commit.gpgsign", "false")
    _git(repository, "add", "-A")
    _git(repository, "commit", "--no-verify", "--no-gpg-sign", "-m", "first")
    return repository


def _governing(repository: Path) -> Path:
    return repository / "src" / "disclosure_drift" / "m3" / "canary_phases.py"


def _commit(repository: Path, message: str) -> None:
    _git(repository, "add", "-A")
    _git(repository, "commit", "--no-verify", "--no-gpg-sign", "-m", message)


# ==========================================================================
# The pinned identity for the in-process phase tests in THIS file
# ==========================================================================
def _pin(head: str = "a" * 40, tree: str = "b" * 40) -> ri.RepositoryIdentity:
    return ri.RepositoryIdentity(
        contract=ri.REPOSITORY_IDENTITY_CONTRACT,
        head_sha=head,
        tree_sha=tree,
        dirty_tracked_paths=(),
        untracked_paths=(),
    )


@pytest.fixture(autouse=True)
def _pinned(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the derivation for in-process phase tests. The derivation itself is proved below."""
    monkeypatch.setattr(canary, "require_clean_running_repository", _pin)


def _repin(monkeypatch: pytest.MonkeyPatch, identity: ri.RepositoryIdentity) -> None:
    monkeypatch.setattr(canary, "require_clean_running_repository", lambda: identity)


# ==========================================================================
# §1. The identity is MEASURED, not declared — the real positive control
# ==========================================================================
def test_the_running_identity_is_the_one_git_reports_for_this_checkout() -> None:
    """**The mutation kill for "the helper returns a constant".**

    Derived by the package, compared against `git` run independently by the test. A helper that
    returned a constant, a version string, or anything not read from this repository fails here.
    """
    checkout = Path(canary.__file__).resolve().parents[3]
    identity = ri.running_repository_identity()
    assert identity.head_sha == _git(checkout, "rev-parse", "HEAD")
    assert identity.tree_sha == _git(checkout, "rev-parse", "HEAD^{tree}")
    assert identity.contract == ri.REPOSITORY_IDENTITY_CONTRACT
    assert identity.head_sha != identity.tree_sha


def test_a_tracked_content_change_and_a_new_commit_move_both_identities(tmp_path: Path) -> None:
    """**§6's positive control, in its exact shape.** commit A -> identity A; change governing
    tracked content, commit B -> identity B; A != B, in both the commit and the tree."""
    repository = _repository(tmp_path)
    first = ri.repository_identity_at(repository)

    _governing(repository).write_text("GOVERNING = 2\n", encoding="utf-8")
    _commit(repository, "second")
    second = ri.repository_identity_at(repository)

    assert first.head_sha != second.head_sha
    assert first.tree_sha != second.tree_sha
    assert first.clean and second.clean
    assert ri.repository_identity_at(repository) == second


def test_the_commit_identity_moves_even_when_the_tree_stands(tmp_path: Path) -> None:
    """**Why both fields exist.** An amend leaves the tree and moves the history; a tree
    comparison alone would admit it, and admitting it silently is not this mechanism's job."""
    repository = _repository(tmp_path)
    before = ri.repository_identity_at(repository)
    _git(repository, "commit", "--amend", "--no-verify", "--no-gpg-sign", "-m", "reworded")
    after = ri.repository_identity_at(repository)

    assert after.tree_sha == before.tree_sha
    assert after.head_sha != before.head_sha


# ==========================================================================
# §2. The clean-tree contract, against real ambiguous working trees
# ==========================================================================
def test_a_modified_tracked_file_makes_the_working_tree_ambiguous(tmp_path: Path) -> None:
    """The committed tree no longer describes what would run, and the path is named."""
    repository = _repository(tmp_path)
    _governing(repository).write_text("GOVERNING = 99\n", encoding="utf-8")
    identity = ri.repository_identity_at(repository)

    assert not identity.clean
    assert identity.dirty_tracked_paths == ("src/disclosure_drift/m3/canary_phases.py",)
    assert identity.untracked_paths == ()


def test_a_staged_but_uncommitted_change_is_also_ambiguous(tmp_path: Path) -> None:
    """Staging is not committing, and staging does not move the recorded `HEAD^{tree}`."""
    repository = _repository(tmp_path)
    _governing(repository).write_text("GOVERNING = 3\n", encoding="utf-8")
    _git(repository, "add", "-A")
    identity = ri.repository_identity_at(repository)

    assert not identity.clean
    assert identity.dirty_tracked_paths == ("src/disclosure_drift/m3/canary_phases.py",)


def test_an_untracked_non_ignored_file_makes_the_working_tree_ambiguous(tmp_path: Path) -> None:
    """A file no commit describes can sit on the import path, so it is ambiguity, not noise."""
    repository = _repository(tmp_path)
    (repository / "src" / "disclosure_drift" / "sitecustomize.py").write_text("", encoding="utf-8")
    identity = ri.repository_identity_at(repository)

    assert not identity.clean
    assert identity.dirty_tracked_paths == ()
    assert identity.untracked_paths == ("src/disclosure_drift/sitecustomize.py",)


def test_an_ignored_file_is_not_ambiguity(tmp_path: Path) -> None:
    """**The rule, stated and then proved.** The repository's own tracked ignore policy is what
    declares a path irrelevant -- and it has to, because importing the package writes
    `__pycache__` and a contract that refused that could never admit anything."""
    repository = _repository(tmp_path)
    (repository / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
    _commit(repository, "ignore policy")
    cache = repository / "src" / "disclosure_drift" / "m3" / "__pycache__"
    cache.mkdir()
    (cache / "canary_phases.cpython-312.pyc").write_bytes(b"\x00")

    identity = ri.repository_identity_at(repository)
    assert identity.clean
    assert identity.untracked_paths == ()


def test_the_clean_contract_refuses_an_ambiguous_tree_and_repairs_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The gate refuses a **real** dirty identity, and leaves the repository as it found it."""
    repository = _repository(tmp_path)
    _governing(repository).write_text("GOVERNING = 4\n", encoding="utf-8")
    before = _governing(repository).read_bytes()
    monkeypatch.setattr(
        ri, "running_repository_identity", lambda: ri.repository_identity_at(repository)
    )

    with pytest.raises(ri.RepositoryIdentityError) as refusal:
        ri.require_clean_running_repository()

    assert "NOT a resumable pause" in str(refusal.value)
    assert "src/disclosure_drift/m3/canary_phases.py" in str(refusal.value)
    assert _governing(repository).read_bytes() == before
    assert not ri.repository_identity_at(repository).clean


def test_the_clean_contract_admits_a_clean_tree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A test that only proved refusal would not prove the gate can ever be passed."""
    repository = _repository(tmp_path)
    monkeypatch.setattr(
        ri, "running_repository_identity", lambda: ri.repository_identity_at(repository)
    )
    assert ri.require_clean_running_repository() == ri.repository_identity_at(repository)


# ==========================================================================
# §3. The repository must be the one that CONTAINS the running code
# ==========================================================================
def test_a_subdirectory_is_not_a_repository_top_level(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    with pytest.raises(ri.RepositoryIdentityError, match="top level"):
        ri.repository_identity_at(repository / "src")


def test_a_path_outside_any_repository_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "loose"
    outside.mkdir()
    with pytest.raises(ri.RepositoryIdentityError):
        ri.repository_root_containing(outside)


def test_an_unreadable_object_name_is_refused_rather_than_folded() -> None:
    """A digest is only worth what its inputs are; a non-object-name never becomes one."""
    with pytest.raises(ri.RepositoryIdentityError, match="Git object name"):
        ri._object_name("not-a-sha", field="HEAD commit")
    assert ri._object_name(" " + "0" * 40 + "\n", field="HEAD commit") == "0" * 40


# ==========================================================================
# §4. The execution digest actually binds it — D146-MAJOR-1 and D146-MINOR-1
# ==========================================================================
def test_the_execution_digest_moves_when_the_repository_moves() -> None:
    """**The MAJOR-1 kill.** Two revisions, two digests. Nothing else in the fold changes."""
    first = canary.phase_execution_identity(repository=_pin(head="a" * 40, tree="b" * 40))
    moved_commit = canary.phase_execution_identity(repository=_pin(head="c" * 40, tree="b" * 40))
    moved_tree = canary.phase_execution_identity(repository=_pin(head="a" * 40, tree="d" * 40))

    assert len({first, moved_commit, moved_tree}) == 3


def test_the_execution_digest_moves_with_a_real_pair_of_commits(tmp_path: Path) -> None:
    """The same claim, with identities Git produced rather than identities the test wrote."""
    repository = _repository(tmp_path)
    first = canary.phase_execution_identity(repository=ri.repository_identity_at(repository))
    _governing(repository).write_text("GOVERNING = 5\n", encoding="utf-8")
    _commit(repository, "moved")
    second = canary.phase_execution_identity(repository=ri.repository_identity_at(repository))

    assert first != second


#: Every execution-governing capacity value on the F0/F1/F2 path, and what it governs.
#:
#: **D146-MINOR-1 made concrete.** Decision 145 §12 said the digest folded "the four capacity
#: floors" and it folded three; the review named `POST_F0` (an accepted post-phase invariant),
#: `F2_ALERT` and `F2_HARD_FLOOR` (the two continuous F2 thresholds) as unfolded. All six are
#: folded now. This table is the inventory, and the test below fails if a seventh appears.
_CAPACITY_POLICY: dict[str, str] = {
    "LAUNCH_MINIMUM_FREE_BYTES": "F0 admission floor",
    "POST_F0_MINIMUM_FREE_BYTES": "post-F0 invariant, enforced at the POST_F0 boundary",
    "PRE_F1_MINIMUM_FREE_BYTES": "F1 admission floor, re-enforced at the PRE_F1 boundary",
    "PRE_F2_MINIMUM_FREE_BYTES": "F2 admission floor, re-enforced inside the F2 process",
    "F2_ALERT_FREE_BYTES": "continuous F2 alert; decides what a capacity observation reports",
    "F2_HARD_FLOOR_FREE_BYTES": "continuous F2 hard stop; rolls F2's single transaction back",
}

#: Capacity-shaped values that are deliberately **not** folded, each with the reason.
_UNFOLDED: dict[str, str] = {
    # Accepted Decision 119 proves the page-cache budget evidence-neutral: it moves no row, no
    # ordering, no digest and no identity, so folding it would refuse continuations that are fine.
    "WORKING_CATALOG_CACHE_BYTES": "Decision 119: provably evidence-neutral",
    # Not a value at all: the D138-R5/R6 mapping from a boundary label to a floor already folded.
    "PHASE_MINIMUM_FREE_BYTES": "a derived mapping; every value in it is folded individually",
}


#: Every input `phase_execution_identity()` folds, in the order the source declares them.
#:
#: **Why the exact set is pinned rather than the count described.** `D146-MINOR-1` was a sentence
#: that said "four" where the code folded three, and the sentence went unchallenged because nothing
#: compared it to the code. A count in prose rots silently; a set compared against the source does
#: not. An input added or removed fails here and the record that describes the fold is corrected
#: with it.
_EXECUTION_IDENTITY_INPUTS: tuple[str, ...] = (
    "canary_contract",
    "restart_contract",
    "evidence_contract",
    "resolution_scope",
    "required_transport",
    "qualified_volume_uuid",
    "batch_size",
    "launch_minimum_free_bytes",
    "post_f0_minimum_free_bytes",
    "pre_f1_minimum_free_bytes",
    "pre_f2_minimum_free_bytes",
    "f2_alert_free_bytes",
    "f2_hard_floor_free_bytes",
    "package_version",
    "repository_identity_contract",
    "repository_head_sha",
    "repository_tree_sha",
)


def test_the_execution_identity_folds_exactly_the_recorded_inputs() -> None:
    """Seventeen inputs, read from the source rather than counted by hand."""
    import ast

    source = Path(canary.__file__).read_text(encoding="utf-8")
    function = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "phase_execution_identity"
    )
    call = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "execution_identity"
    )
    folded = tuple(key.value for key in call.args[0].keys)  # type: ignore[union-attr]

    assert folded == _EXECUTION_IDENTITY_INPUTS
    assert len(folded) == 17
    # The capacity half of the fold is exactly the inventory below, lowercased.
    assert {name for name in folded if name.endswith("_free_bytes")} == {
        name.lower() for name in _CAPACITY_POLICY
    }


def test_every_execution_governing_capacity_value_is_folded_or_explicitly_excluded() -> None:
    """**The MINOR-1 closure, made mechanical.** A capacity constant added later and left
    unclassified fails here rather than silently escaping the execution contract."""
    declared = {
        name
        for module in (ewr, canary)
        for name in vars(module)
        if name.endswith("_FREE_BYTES") or name.endswith("_CACHE_BYTES")
    }
    assert declared == set(_CAPACITY_POLICY) | set(_UNFOLDED), (
        "a capacity constant is neither folded into the execution contract nor explicitly "
        "excluded from it with a reason"
    )
    # The derived mapping carries no floor of its own: every value in it is folded by name.
    assert set(ewr.PHASE_MINIMUM_FREE_BYTES.values()) <= {
        getattr(ewr, name) for name in _CAPACITY_POLICY if hasattr(ewr, name)
    }


@pytest.mark.parametrize("constant", sorted(_CAPACITY_POLICY))
def test_the_execution_digest_moves_when_a_bound_capacity_value_moves(
    monkeypatch: pytest.MonkeyPatch, constant: str
) -> None:
    """**The exact mutation D146 used, generalised.** Relaxing any bound floor moves the digest."""
    before = canary.phase_execution_identity(repository=_pin())
    module = ewr if hasattr(ewr, constant) else canary
    monkeypatch.setattr(module, constant, getattr(module, constant) // 2)
    # `canary` imported the names, so the module that owns them is patched on both.
    if module is ewr and hasattr(canary, constant):
        monkeypatch.setattr(canary, constant, getattr(ewr, constant))

    assert canary.phase_execution_identity(repository=_pin()) != before


def test_the_page_cache_budget_still_moves_no_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Decision 119's exclusion is preserved, not quietly swept up by the widened fold."""
    before = canary.phase_execution_identity(repository=_pin())
    monkeypatch.setattr(canary, "WORKING_CATALOG_CACHE_BYTES", 1)
    assert canary.phase_execution_identity(repository=_pin()) == before


def test_the_declared_version_alone_is_no_longer_the_code_identity() -> None:
    """**D146-MAJOR-1 in one line.** The version string is still folded; it is no longer the
    only thing standing between a moved revision and an admitted continuation."""
    import disclosure_drift

    assert disclosure_drift.__version__ in ("0.1.0",)
    folded = canary.phase_execution_identity(repository=_pin())
    assert folded != canary.phase_execution_identity(repository=_pin(head="e" * 40))


# ==========================================================================
# §5. The production successor-admission path consumes it
# ==========================================================================
def test_the_checkpoint_records_the_repository_it_ran_under(tmp_path: Path) -> None:
    """Recorded as named fields as well as inside the digest, so a refusal can be diagnosed."""
    private, work = d145._world(tmp_path)
    d145._sequence(private, work, run_id="record", through="f0")
    ledger = d145._ledger(work, "record")
    try:
        stored = phases.read_phase_checkpoint(ledger, "f0")
    finally:
        ledger.close()
    assert stored is not None
    assert stored.repository_head_sha == _pin().head_sha
    assert stored.repository_tree_sha == _pin().tree_sha
    assert stored.contract == "m3.3-canary-phase-restart/2"


@pytest.mark.parametrize("phase", ["f1", "f2"])
@pytest.mark.parametrize("field", ["head", "tree"])
def test_a_successor_refuses_a_predecessor_from_another_revision(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str, field: str
) -> None:
    """**Both boundaries, both halves of the identity.** F1 and F2 each recompute in their own
    process and refuse a predecessor whose repository moved -- naming expected and observed."""
    private, work = d145._world(tmp_path)
    predecessor = {"f1": "f0", "f2": "f1"}[phase]
    d145._sequence(private, work, run_id="moved", through=predecessor)

    moved = _pin(head="c" * 40) if field == "head" else _pin(tree="d" * 40)
    _repin(monkeypatch, moved)
    with pytest.raises(phases.CanaryPhaseError, match=f"repository_{field}_sha") as refusal:
        d145._phase(private, work, phase, run_id="moved")

    assert "expected" in str(refusal.value)
    assert "observed" in str(refusal.value)
    assert getattr(moved, f"{field}_sha") in str(refusal.value)


def test_the_same_revision_admits_the_whole_sequence(tmp_path: Path) -> None:
    """A refusal test proves nothing unless the admission it mirrors is proved too."""
    private, work = d145._world(tmp_path)
    done = d145._sequence(private, work, run_id="admitted")

    assert [step.phase for step in done] == ["f0", "f1", "f2"]
    assert {step.repository_head_sha for step in done} == {_pin().head_sha}
    assert {step.repository_tree_sha for step in done} == {_pin().tree_sha}
    assert done[-1].result_document_written is True


def test_a_predecessor_checkpoint_without_a_repository_identity_is_not_continued(
    tmp_path: Path,
) -> None:
    """**The contract bump.** A version-1 checkpoint describes a phase that ran without recording
    which revision it ran, which is exactly the state a version-2 successor must not continue."""
    private, work = d145._world(tmp_path)
    d145._sequence(private, work, run_id="legacy", through="f0")
    ledger = d145._ledger(work, "legacy")
    try:
        key = f"{phases.PHASE_CHECKPOINT_KEY_PREFIX}f0"
        record = json.loads(str(ledger.recorded_value(key)))
        record["contract"] = "m3.3-canary-phase-restart/1"
        del record["repository_head_sha"]
        del record["repository_tree_sha"]
        ledger.record_value(key, json.dumps(record, sort_keys=True))
    finally:
        ledger.close()

    with pytest.raises(phases.CanaryPhaseError, match="could not be read as this build writes"):
        d145._phase(private, work, "f1", run_id="legacy")


def test_a_predecessor_checkpoint_from_the_earlier_contract_is_not_continued(
    tmp_path: Path,
) -> None:
    """And a checkpoint that still carries the version-1 contract label is refused on that alone."""
    private, work = d145._world(tmp_path)
    d145._sequence(private, work, run_id="contract", through="f0")
    d145._rewrite_checkpoint(work, "contract", "f0", contract="m3.3-canary-phase-restart/1")

    with pytest.raises(phases.CanaryPhaseError, match="does not continue from"):
        d145._phase(private, work, "f1", run_id="contract")


def test_the_production_phase_path_derives_the_identity_and_accepts_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """**No operator-supplied SHA, anywhere.** The run derives it; no parameter, environment
    variable or command-line option can declare one."""
    import inspect

    for entry in (canary.run_single_source_canary_phase, canary.run_canary_source_command):
        taken = set(inspect.signature(entry).parameters)
        assert not {name for name in taken if "repository" in name and name != "repository_root"}

    private, work = d145._world(tmp_path)
    calls: list[int] = []

    def _counted() -> ri.RepositoryIdentity:
        calls.append(1)
        return _pin()

    monkeypatch.setattr(canary, "require_clean_running_repository", _counted)
    d145._sequence(private, work, run_id="derived", through="f0")
    assert calls == [1], "the phase entry point derives the identity exactly once, itself"


def test_no_operator_surface_accepts_a_revision() -> None:
    """The CLI has no flag that could declare a repository commit or tree."""
    source = Path(canary.__file__).read_text(encoding="utf-8")
    assert "--repository-head" not in source
    assert "--repository-sha" not in source
    cli = Path(canary.__file__).resolve().parents[1] / "cli.py"
    text = cli.read_text(encoding="utf-8")
    for flag in ("--repository-head", "--repository-tree", "--repository-sha", "--revision"):
        assert flag not in text


# ==========================================================================
# §6. End to end, in real processes, from real published checkouts
# ==========================================================================
def _child(
    checkout: Path, private: Path, work: Path, phase: str, run_id: str
) -> subprocess.CompletedProcess[bytes]:
    """One phase through the real operator command, in its own process, from `checkout`."""
    environment = dict(os.environ)
    environment[EVIDENCE_ROOT_ENV] = str(private)
    environment["PYTHONPATH"] = str(checkout / "src")
    return subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
        [
            sys.executable,
            "-m",
            "disclosure_drift",
            "m3",
            "canary-source",
            "--mode",
            f"phase-{phase}",
            "--source-instance-id",
            _BULK,
            "--run-id",
            run_id,
            "--work-root",
            str(work),
        ],
        capture_output=True,
        check=False,
        timeout=600,
        cwd=checkout,
        env=environment,
    )


def test_a_governing_repository_change_between_phases_refuses_the_successor(
    tmp_path: Path,
) -> None:
    """**The whole of Decision 147, end to end, with nothing pinned and nothing faked.**

    F0 runs from a real published checkout at commit A. A governing tracked source file is then
    changed and committed, exactly as a revision moving between two phases would. F1, in its own
    process, derives the identity itself, sees commit B, and REFUSES -- naming both values. The
    world is left exactly as F0 left it: no repair, no resume, no second F0.
    """
    private, work = d145._world(tmp_path)
    checkout = d145.published_checkout(tmp_path)
    first = d145.head_of(checkout)

    admitted = _child(checkout, private, work, "f0", "revision")
    assert admitted.returncode == 0, admitted.stderr.decode("utf-8", errors="replace")
    assert first in admitted.stdout.decode("utf-8")

    governing = checkout / "src" / "disclosure_drift" / "m3" / "canary_phases.py"
    governing.write_text(
        governing.read_text(encoding="utf-8") + "\n# a governing revision that moved\n",
        encoding="utf-8",
    )
    _commit(checkout, "the revision moved")
    second = d145.head_of(checkout)
    assert second != first

    refused = _child(checkout, private, work, "f1", "revision")
    stderr = refused.stderr.decode("utf-8", errors="replace")
    assert refused.returncode != 0
    assert "repository_head_sha" in stderr
    assert first in stderr and second in stderr
    assert "not a resumable pause" in stderr

    ledger = d145._ledger(work, "revision")
    try:
        assert phases.read_phase_checkpoint(ledger, "f0") is not None
        assert phases.read_phase_checkpoint(ledger, "f1") is None
    finally:
        ledger.close()


def test_an_uncommitted_governing_change_refuses_before_anything_is_touched(
    tmp_path: Path,
) -> None:
    """A dirty tracked tree is refused in the real process, and the world is never created."""
    private, work = d145._world(tmp_path)
    checkout = d145.published_checkout(tmp_path)
    governing = checkout / "src" / "disclosure_drift" / "m3" / "canary_phases.py"
    governing.write_text(governing.read_text(encoding="utf-8") + "\n# uncommitted\n", "utf-8")

    refused = _child(checkout, private, work, "f0", "dirty")
    stderr = refused.stderr.decode("utf-8", errors="replace")
    assert refused.returncode != 0
    assert "clean tracked working tree" in stderr
    assert "src/disclosure_drift/m3/canary_phases.py" in stderr
    assert not (work / "dirty").exists(), "a refused phase creates no world"


def test_an_untracked_module_in_the_checkout_refuses(tmp_path: Path) -> None:
    """An untracked, non-ignored file can join the import graph, so it is refused too."""
    private, work = d145._world(tmp_path)
    checkout = d145.published_checkout(tmp_path)
    (checkout / "src" / "disclosure_drift" / "m3" / "extra.py").write_text("", encoding="utf-8")

    refused = _child(checkout, private, work, "f0", "untracked")
    stderr = refused.stderr.decode("utf-8", errors="replace")
    assert refused.returncode != 0
    assert "untracked, non-ignored (1): src/disclosure_drift/m3/extra.py" in stderr
    assert not (work / "untracked").exists()


def test_a_repository_that_merely_encloses_the_code_is_refused(tmp_path: Path) -> None:
    """**Why membership is checked.** Git walks upward, so an installed copy inside an unrelated
    repository would otherwise yield a real identity of the wrong code."""
    private, work = d145._world(tmp_path)
    foreign = _repository(tmp_path, name="foreign")
    published = d145.published_checkout(tmp_path, name="staged")
    target = foreign / "vendored"
    target.mkdir()
    (published / "src").rename(target / "src")
    (published / "configs").rename(foreign / "configs")

    environment = dict(os.environ)
    environment[EVIDENCE_ROOT_ENV] = str(private)
    environment["PYTHONPATH"] = str(target / "src")
    refused = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
        [
            sys.executable,
            "-m",
            "disclosure_drift",
            "m3",
            "canary-source",
            "--mode",
            "phase-f0",
            "--source-instance-id",
            _BULK,
            "--run-id",
            "foreign",
            "--work-root",
            str(work),
        ],
        capture_output=True,
        check=False,
        timeout=600,
        cwd=foreign,
        env=environment,
    )
    stderr = refused.stderr.decode("utf-8", errors="replace")
    assert refused.returncode != 0
    assert "does not track the modules that govern a canary phase" in stderr


# ==========================================================================
# §7. Everything Decision 147 must NOT have changed
# ==========================================================================
def test_the_migration_head_a_successor_continues_under_is_compared(tmp_path: Path) -> None:
    """**D146-OBS-3, closed with a focused test rather than an architecture change.**

    The review recorded that `migration_head` is bound in `require_phase_admission` but has no
    test of its own, because `_verify_attached` refuses a moved migration chain before admission
    is reached -- making the admission comparison defensive rather than load-bearing. That is a
    correct reading and no redesign follows from it; what was missing was a test that the
    defensive comparison is real. This is that test, taken against the primitive directly,
    because the production path cannot reach it.
    """
    private, work = d145._world(tmp_path)
    d145._sequence(private, work, run_id="head", through="f0")
    ledger = d145._ledger(work, "head")
    try:
        stored = phases.read_phase_checkpoint(ledger, "f0")
        assert stored is not None
        with pytest.raises(phases.CanaryPhaseError, match="migration_head"):
            phases.require_phase_admission(
                ledger,
                phase="f1",
                run_id="head",
                source_instance_id=stored.source_instance_id,
                execution_identity=stored.execution_identity,
                repository_head_sha=stored.repository_head_sha,
                repository_tree_sha=stored.repository_tree_sha,
                catalog_source_sha256=stored.catalog_source_sha256,
                migration_head=stored.migration_head + 1,
                plan_fingerprint=stored.plan_fingerprint,
            )
    finally:
        ledger.close()


def test_a_decoy_command_line_reads_as_a_live_predecessor_and_refuses(tmp_path: Path) -> None:
    """**D146-OBS-7, pinned as the accepted fail-closed behaviour rather than "corrected".**

    `process_is_live_canary` does not authenticate `argv[0]`, unlike `authenticate_canary_process`,
    so a decoy command line carrying this run's subcommand and `--run-id` reads as *alive*. The
    review classified that as fail-closed and it is: the two helpers answer questions whose safe
    directions are **opposite**. Authentication decides whether to SIGNAL, where being permissive
    means signalling the wrong process, so it must be strict. This decides whether a predecessor
    is GONE, where returning `True` refuses a successor and returning `False` admits one -- so an
    `argv[0]` condition here would make `True` harder to reach and could admit a successor while
    its predecessor was still writing. That is the dangerous direction, so the asymmetry is not a
    defect to be smoothed, and this test fails if a future change smooths it.
    """
    decoy = ("/bin/zsh", "m3", "canary-source", "--run-id", "obs7", "--mode", "phase-f1")
    assert runtime.process_is_live_canary(4242, run_id="obs7", argv_provider=lambda _p: decoy)
    assert not runtime.process_is_live_canary(4242, run_id="other", argv_provider=lambda _p: decoy)


def test_the_working_catalog_is_authenticated_by_its_migration_chain_and_not_its_bytes(
    tmp_path: Path,
) -> None:
    """**D146-OBS-1, recorded rather than expanded.**

    No digest of the working-catalog **file** is compared at attach, so a substituted copy of the
    same lineage and the same migration chain would be admitted. Reaching that state requires
    write access inside the disposable world -- an actor who has it can equally rewrite the ledger
    and the checkpoint -- so it sits outside the accepted threat model, and the owner's default is
    to record it rather than widen the model. What *is* enforced is asserted here, so the boundary
    is a stated one: the attached copy's migration chain must be the chain recorded at creation.
    """
    import ast

    private, work = d145._world(tmp_path)
    d145._sequence(private, work, run_id="attach", through="f0")
    assert (work / "attach" / "working_catalog.sqlite3").is_file()

    # What IS enforced: the attached copy's migration chain must be the recorded one.
    catalog_source = (Path(canary.__file__).parent / "working_catalog.py").read_text("utf-8")
    assert "_verify_attached" in catalog_source
    assert "migration chain does not match the one recorded" in catalog_source

    # What is NOT: the attach path digests nothing, and the checkpoint records no such digest.
    attach = next(
        node
        for node in ast.walk(ast.parse(Path(canary.__file__).read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef) and node.name == "attach_world"
    )
    called = {
        getattr(node.func, "id", "") for node in ast.walk(attach) if isinstance(node, ast.Call)
    }
    assert "file_digest" not in called
    assert not [name for name in phases.PhaseCheckpoint.__slots__ if "working_catalog" in name]


def test_the_checkpoint_write_is_serialised_by_the_host_execution_lock(tmp_path: Path) -> None:
    """**D146-OBS-2, recorded rather than redesigned.**

    Checkpoint create-once is a read-then-write under the host execution lock rather than an
    atomic `O_EXCL` like the neighbouring result document. The review called it non-exploitable
    because the lock serialises it, and the lock is what this asserts: a second canary process on
    this host cannot begin a phase at all, so it can never reach the read-then-write window.
    """
    private, work = d145._world(tmp_path)
    held = runtime.acquire_canary_execution_lock(
        private, detail={"run_id": "other", "mode": "phase-f0"}
    )
    try:
        with pytest.raises(runtime.CanaryRuntimeError):
            d145._phase(private, work, "f0", run_id="locked")
    finally:
        held.release()
    assert not (work / "locked").exists()


def test_mode_run_is_still_reachable_and_is_a_governance_boundary(tmp_path: Path) -> None:
    """**D146-OBS-6, carried forward exactly.** Decision 147 does not remove `--mode run`.

    The review recorded that mode selection is a governance boundary rather than a mechanical
    one. That is carried forward unchanged: the future real-canary authorization must authorize
    only `--mode phase-f0`, `phase-f1` and `phase-f2`, and must forbid `--mode run` for the
    authorized real canary. Nothing here creates or removes that boundary.
    """
    assert "run" not in canary.CANARY_PHASE_MODES
    assert callable(canary.run_single_source_canary)
    source = Path(canary.__file__).read_text(encoding="utf-8")
    assert 'mode != "run"' in source


def test_the_admission_side_predecessor_status_guard_is_kept(tmp_path: Path) -> None:
    """**D146-OBS-4, kept.** The guard is unreachable defensive redundancy, and stays.

    Decision 145 §19 disclosed that deleting it survives the suite, and the review confirmed it by
    mutation rather than accepting the disclosure. Neither is grounds for deleting it: a status a
    write-side guard already refuses is exactly the kind of thing a future write path could stop
    refusing, and removing the reader's check to improve a mutation score would trade a real
    invariant for a number.
    """
    source = Path(phases.__file__).read_text(encoding="utf-8")
    assert "predecessor.status != PHASE_STATUS_COMPLETE" in source
    assert "checkpoint.status != PHASE_STATUS_COMPLETE" in source


def test_the_three_phases_and_the_two_boundaries_are_unchanged() -> None:
    assert phases.CANARY_PHASE_SEQUENCE == ("f0", "f1", "f2")
    assert phases.PHASE_PREDECESSOR == {"f0": None, "f1": "f0", "f2": "f1"}
    assert phases.PHASE_SUCCESSOR == {"f0": "f1", "f1": "f2", "f2": None}
    assert sorted(canary.CANARY_PHASE_MODES) == ["phase-f0", "phase-f1", "phase-f2"]
    assert canary.PHASE_ADMISSION_FLOOR == {
        "f0": ewr.LAUNCH_MINIMUM_FREE_BYTES,
        "f1": ewr.PRE_F1_MINIMUM_FREE_BYTES,
        "f2": canary.PRE_F2_MINIMUM_FREE_BYTES,
    }


def test_the_pre_f2_gate_still_runs_in_the_f2_process_immediately_before_its_transaction() -> None:
    """**D126-R6 preserved.** Proved from the source, not from the docstring that describes it."""
    import ast

    source = Path(canary.__file__).read_text(encoding="utf-8")
    body = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "_phase_f2_body"
    )
    containment = next(node for node in ast.walk(body) if isinstance(node, ast.With))
    first, second = containment.body[0], containment.body[1]
    assert isinstance(first, ast.Expr)
    assert isinstance(first.value, ast.Call)
    assert first.value.func.id == "_require_pre_f2_free_space"  # type: ignore[attr-defined]
    assert isinstance(second, ast.Assign)
    assert second.value.func.id == "_f2"  # type: ignore[attr-defined]
    assert canary.PRE_F2_MINIMUM_FREE_BYTES == 50 * 1024**3


def test_the_stale_decision_126_rationale_is_marked_historical_and_both_are_named() -> None:
    """**MINOR-2 and OBS-5.** The docstring now separates what was true from what still binds."""
    lines = Path(canary.__file__).read_text(encoding="utf-8").splitlines()
    declaration = next(
        index for index, line in enumerate(lines) if line.startswith("PRE_F2_MINIMUM_FREE_BYTES")
    )
    start = declaration
    while start > 0 and lines[start - 1].startswith("#:"):
        start -= 1
    # Normalised: the comment prefix stripped, emphasis removed and whitespace collapsed, so the
    # assertions are about the sentences rather than about where the lines happened to wrap.
    docstring = re.sub(
        r"\s+", " ", " ".join(line.removeprefix("#:").strip() for line in lines[start:declaration])
    ).replace("*", "")
    assert docstring, "the constant carries no documentation at all"

    assert "HISTORICAL" in docstring and "CURRENT AND BINDING" in docstring
    # Both now-false Decision 126 rationale sentences -- D146-MINOR-2 named one, D146-OBS-5 the
    # other -- are marked historical rather than restated as present fact.
    assert "F1 returns and F2 begins in consecutive statements" in docstring
    assert "Nothing durable changes at the boundary" in docstring
    assert docstring.index("HISTORICAL") < docstring.index("consecutive statements")
    assert docstring.index("HISTORICAL") < docstring.index("Nothing durable changes")
    # The two reasons that carry D126-R6 are untouched, and are marked as still binding.
    binding = docstring[docstring.index("CURRENT AND BINDING") :]
    assert "advisory where admission has to be dispositive" in binding
    assert "Only the path that is about to open the transaction can decline to open it" in binding
    assert "Decision 126 itself is not rewritten" in docstring


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_the_topology_envelope_is_unchanged_at_every_phase(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str
) -> None:
    """The D142 §4 selection, the D140-R2 assertion, AC power and an open lid, all still refuse."""
    private, work = d145._world(tmp_path)

    d144._attach(monkeypatch, tmp_path, chain=d144._DIRECT)
    with pytest.raises(dt.DockTransportError, match="requires USB_VIA_THUNDERBOLT_DOCK"):
        d145._phase(private, work, phase, run_id="direct", asserted=_QUALIFIED)

    d144._attach(monkeypatch, tmp_path)
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the one qualified external"):
        d145._phase(private, work, phase, run_id="wrong", asserted=_OTHER_UUID)

    d144._attach(monkeypatch, tmp_path, on_ac=False)
    with pytest.raises(runtime.CanaryRuntimeError):
        d145._phase(private, work, phase, run_id="battery", asserted=_QUALIFIED)

    d144._attach(monkeypatch, tmp_path, lid_closed=True)
    with pytest.raises(runtime.CanaryRuntimeError):
        d145._phase(private, work, phase, run_id="lid", asserted=_QUALIFIED)


def test_a_qualified_dock_still_passes_every_phase(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The narrowing refuses what it must and admits what it must -- otherwise it proves nothing."""
    private, work = d145._world(tmp_path)
    d144._attach(monkeypatch, tmp_path)
    done = d145._sequence(private, work, run_id="dock", asserted=_QUALIFIED)
    assert [step.phase for step in done] == ["f0", "f1", "f2"]


def test_parse_bulk_remains_canary_unreachable() -> None:
    """**Unchanged and re-traced**, including through the module Decision 147 added."""
    for module in (canary, phases, runtime, ri):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "census_orchestrator" not in source
        assert "_parse_bulk" not in source

    probe = (
        "import sys;"
        "import disclosure_drift.m3.repository_identity;"
        "import disclosure_drift.m3.single_source_canary;"
        "print('census_orchestrator' in ' '.join(sys.modules))"
    )
    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, "-c", probe], capture_output=True, check=True, timeout=120
    )
    assert completed.stdout.decode("utf-8").strip() == "False"


def test_the_new_module_mints_no_authority_and_reaches_no_network() -> None:
    """Decision 147 is a correction. It authorizes nothing and enables nothing."""
    from disclosure_drift.m3 import e0

    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is None
    assert e0.M3_3_E0_EXECUTION_AUTHORITY is None
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None

    source = Path(ri.__file__).read_text(encoding="utf-8")
    for token in ("httpx", "m3_acquire_enabled", "EXECUTION_AUTHORITY", "SAFE_TO_EJECT"):
        assert token not in source


def test_the_identity_path_issues_read_only_git_subcommands_only() -> None:
    """**Read, never repair.** The Git subcommands the module can issue, proved from its own AST.

    Not a docstring promise and not a substring search: every `_git` call site is located and its
    subcommand read, so a future `checkout`, `stash`, `reset`, `clean`, `fetch` or `pull` fails
    here rather than being described as impossible.
    """
    import ast

    tree = ast.parse(Path(ri.__file__).read_text(encoding="utf-8"))
    issued = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_git"):
            continue
        arguments = node.args[1]
        assert isinstance(arguments, ast.List), "a git argv must be a literal list to be auditable"
        first = arguments.elts[0]
        assert isinstance(first, ast.Constant), "a git subcommand must be a literal"
        issued.add(first.value)

    assert issued == {"rev-parse", "status", "ls-files"}


def test_the_identity_path_only_ever_reads(tmp_path: Path) -> None:
    """A repository is left byte-identical by every function here, including a refusing one."""
    repository = _repository(tmp_path)
    before = _git(repository, "rev-parse", "HEAD"), _git(repository, "status", "--porcelain=v1")
    ri.repository_identity_at(repository)
    ri.repository_root_containing(repository / "src")
    _governing(repository).write_text("GOVERNING = 6\n", encoding="utf-8")
    ri.repository_identity_at(repository)
    _git(repository, "checkout", "--", ".")
    after = _git(repository, "rev-parse", "HEAD"), _git(repository, "status", "--porcelain=v1")
    assert before == after
