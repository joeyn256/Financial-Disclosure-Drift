"""Decision 149 — the final pre-canary limitation cleanup.

**What this file closes.** Three items the
[Decision 148](../../Docs/Decisions/decision_148_m3_3_final_independent_d147_rereview.md)
independent re-review recorded against the Decision 147 tree and deliberately did not repair:

* **`D148-MINOR-1`** — the ``_git`` docstring claimed *"``PATH`` order decides nothing"* where
  :func:`shutil.which` **selects by ``PATH`` order**. Corrected prose, no behaviour change, and
  a machine-checkable assertion so the false claim cannot come back;
* **`D148-L3`** — Decision 147 refuses a deleted or renamed tracked path correctly, but had no
  test that said so. The review verified it by hand; this is the accepted coverage;
* **`D148-L2`** — ``--mode run`` derived no repository identity and was not refused on a governed
  external root. It is refused there now, and the phase modes are the only governed route.

**What it does not do.** It runs no canary, mints no authority, enables no network switch, creates
no migration, and touches the operator's real checkout in no way: every repository it commits to is
one it created under ``tmp_path`` and abandons.
"""

from __future__ import annotations

import ast
import inspect
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d116_single_source_canary as d116  # noqa: E402
import test_d144_first_canary_transport_narrowing as d144  # noqa: E402
import test_d145_phase_restart as d145  # noqa: E402
import test_d147_repository_code_identity as d147  # noqa: E402

from disclosure_drift.config import EVIDENCE_ROOT_ENV  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import repository_identity as ri  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402

_BULK = d116._BULK_INSTANCE
_QUALIFIED = ewr.QUALIFIED_EXTERNAL_VOLUME_UUID

# The real-Git fixtures are Decision 147's, reused rather than reimplemented: a second copy would
# be a second thing to keep true.
_git = d147._git
_repository = d147._repository
_governing = d147._governing


@pytest.fixture(autouse=True)
def _pinned(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the repository derivation for the phase tests. §2 proves the derivation itself."""
    monkeypatch.setattr(canary, "require_clean_running_repository", d147._pin)


# ==========================================================================
# §1. D148-MINOR-1 — the PATH claim, corrected and pinned
# ==========================================================================
#: The false claim, in the shape it was written. Matched loosely enough that a reworded revival
#: of the same assertion fails too, rather than only the exact original sentence.
_PATH_INDEPENDENCE_CLAIM = re.compile(
    r"``PATH``\s+order\s+decides\s+nothing|PATH\s+order\s+decides\s+nothing", re.IGNORECASE
)


def test_no_governing_surface_claims_path_order_independence() -> None:
    """**The `D148-MINOR-1` kill.** `shutil.which` selects by `PATH` order, so nothing may say
    otherwise -- not the module, not a decision record, not the runbook, not the status ledger."""
    root = Path(canary.__file__).resolve().parents[3]
    # Every executable surface, plus the one document an operator acts on. The decision records
    # are deliberately OUT of scope: Decision 148 recorded the false claim as a finding and
    # Decision 149 quotes it while correcting it, and a record of a defect is not a repetition
    # of it. What must never assert it again is the code, and the page the operator reads.
    surfaces = [
        *sorted((root / "src").rglob("*.py")),
        root / "Docs" / "m3" / "operator_runbook.md",
    ]
    offenders = [
        path.relative_to(root).as_posix()
        for path in surfaces
        if _PATH_INDEPENDENCE_CLAIM.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == [], f"a surface still claims PATH-order independence: {offenders}"


def test_the_git_docstring_states_the_property_that_is_actually_true() -> None:
    """A correction that only deleted the false sentence would leave the reader with nothing."""
    doc = inspect.getdoc(ri._git) or ""
    assert "selects by ``PATH`` order" in doc
    assert "host" in doc and "trust" in doc
    assert not _PATH_INDEPENDENCE_CLAIM.search(doc)


def test_the_correction_changed_no_behaviour() -> None:
    """**Prose only.** The resolution is still one `shutil.which`, and every Git call is still a
    read -- the two properties Decision 147 actually established, re-derived here from the AST."""
    tree = ast.parse(Path(ri.__file__).read_text(encoding="utf-8"))
    which = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "shutil.which"
    ]
    assert len(which) == 1
    assert [ast.unparse(argument) for argument in which[0].args] == ["'git'"]

    issued = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_git":
            arguments = node.args[1]
            assert isinstance(arguments, ast.List)
            first = arguments.elts[0]
            assert isinstance(first, ast.Constant)
            issued.add(first.value)
    assert issued == {"rev-parse", "status", "ls-files"}


# ==========================================================================
# §2. D148-L3 — deleted and renamed tracked paths, against real Git
# ==========================================================================
def test_a_tracked_file_deleted_in_the_worktree_is_ambiguity(tmp_path: Path) -> None:
    """The committed tree still describes a file that is no longer there to run."""
    repository = _repository(tmp_path)
    _governing(repository).unlink()
    identity = ri.repository_identity_at(repository)

    assert not identity.clean
    assert identity.dirty_tracked_paths == ("src/disclosure_drift/m3/canary_phases.py",)
    assert identity.untracked_paths == ()


def test_a_tracked_file_staged_for_deletion_is_ambiguity(tmp_path: Path) -> None:
    """Staging a deletion is not committing it, and it does not move ``HEAD^{tree}``."""
    repository = _repository(tmp_path)
    before = ri.repository_identity_at(repository).tree_sha
    _git(repository, "rm", "-q", "src/disclosure_drift/m3/canary_phases.py")
    identity = ri.repository_identity_at(repository)

    assert not identity.clean
    assert identity.dirty_tracked_paths == ("src/disclosure_drift/m3/canary_phases.py",)
    assert identity.tree_sha == before, "a staged deletion must not move the committed tree"


def test_a_tracked_file_renamed_with_git_mv_is_ambiguity_at_its_new_path(tmp_path: Path) -> None:
    """``git status --porcelain=v1`` reports a rename as ``old -> new``; the path recorded is the
    **new** one, because that is the file now on disk and therefore the one that could execute."""
    repository = _repository(tmp_path)
    _git(
        repository,
        "mv",
        "src/disclosure_drift/m3/canary_phases.py",
        "src/disclosure_drift/m3/renamed_canary.py",
    )
    identity = ri.repository_identity_at(repository)

    assert not identity.clean
    assert identity.dirty_tracked_paths == ("src/disclosure_drift/m3/renamed_canary.py",)
    assert identity.untracked_paths == ()


def test_an_unstaged_worktree_rename_is_ambiguity_twice_over(tmp_path: Path) -> None:
    """Git sees no rename here, and that is the safer reading: the old path is **missing** and the
    new one is a file no commit describes. Both halves refuse, and both are named."""
    repository = _repository(tmp_path)
    module = _governing(repository)
    module.rename(module.with_name("moved_canary.py"))
    identity = ri.repository_identity_at(repository)

    assert not identity.clean
    assert identity.dirty_tracked_paths == ("src/disclosure_drift/m3/canary_phases.py",)
    assert identity.untracked_paths == ("src/disclosure_drift/m3/moved_canary.py",)


@pytest.mark.parametrize("state", ["deleted", "staged-deleted", "renamed", "worktree-renamed"])
def test_every_one_of_those_states_refuses_through_the_clean_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, state: str
) -> None:
    """**Fail-closed, not merely reported.** Reporting a path is worth nothing unless the gate
    that consumes it refuses, so each state is driven through the production contract itself."""
    repository = _repository(tmp_path)
    module = _governing(repository)
    if state == "deleted":
        module.unlink()
    elif state == "staged-deleted":
        _git(repository, "rm", "-q", "src/disclosure_drift/m3/canary_phases.py")
    elif state == "renamed":
        _git(
            repository,
            "mv",
            "src/disclosure_drift/m3/canary_phases.py",
            "src/disclosure_drift/m3/renamed_canary.py",
        )
    else:
        module.rename(module.with_name("moved_canary.py"))

    monkeypatch.setattr(
        ri, "running_repository_identity", lambda: ri.repository_identity_at(repository)
    )
    with pytest.raises(ri.RepositoryIdentityError) as refusal:
        ri.require_clean_running_repository()

    assert "NOT a resumable pause" in str(refusal.value)
    assert "canary" in str(refusal.value)
    # And the repository is left exactly as it was found: a refusal repairs nothing.
    assert not ri.repository_identity_at(repository).clean


def test_a_clean_repository_is_still_admitted_after_all_of_that(tmp_path: Path) -> None:
    """The positive control the four refusals above are worth nothing without."""
    repository = _repository(tmp_path)
    identity = ri.repository_identity_at(repository)
    assert identity.clean
    assert identity.dirty_tracked_paths == ()
    assert identity.untracked_paths == ()


# ==========================================================================
# §3. D148-L2 — `--mode run` is refused where the external envelope governs
# ==========================================================================
def _operator(
    tmp_path: Path,
    temp: Path,
    *,
    mode: str,
    private: Path,
    run_id: str = "d149",
    asserted: str | None = _QUALIFIED,
) -> object:
    """One invocation of the real operator entry point, exactly as ``cli.py`` invokes it.

    ``private`` is built by the caller and reused across a phase sequence, because the accepted
    catalog fixture is create-once: seeding it a second time is a refusal, and it would be this
    helper's refusal rather than the property under test.
    """
    checkout = tmp_path / "checkout"
    checkout.mkdir(exist_ok=True)
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    return canary.run_canary_source_command(
        mode=mode,
        run_id=run_id,
        source_instance_id=_BULK,
        work_root=str(work),
        repository_root=checkout,
        require_volume_uuid=asserted,
        environ={EVIDENCE_ROOT_ENV: str(private), ewr.SQLITE_TMPDIR_ENV: str(temp)},
    )


def test_the_governed_external_route_refuses_mode_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**The `D148-L2` closure, and proof 1 of `D149-R3`.** A fully qualified external launch --
    the exact configuration the real canary runs in -- is refused for ``--mode run``."""
    private = d116._private_root(tmp_path)
    temp = d144._attach(monkeypatch, tmp_path)
    with pytest.raises(canary.SingleSourceCanaryError) as refusal:
        _operator(tmp_path, temp, mode="run", private=private)

    message = str(refusal.value)
    assert "refused on a working root the external envelope governs" in message
    assert "phase-f0" in message and "phase-f1" in message and "phase-f2" in message
    assert "no flag, environment variable or configuration key" in message
    assert not (tmp_path / "work" / "d149").exists(), "a refused run creates no world"


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_mode_remains_admitted_on_the_same_governed_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    """**Proofs 2, 3 and 4.** The refusal is narrow: it removes ``run`` and nothing else. Each
    phase is driven to admission through the same operator surface, in sequence, on the same
    qualified external configuration the ``run`` refusal above was taken on."""
    private = d116._private_root(tmp_path)
    temp = d144._attach(monkeypatch, tmp_path)
    for step in ("f0", "f1", "f2"):
        outcome = _operator(
            tmp_path, temp, mode=f"phase-{step}", private=private, run_id="d149-phases"
        )
        assert outcome.exit_code == 0, f"phase-{step} must remain admitted"  # type: ignore[attr-defined]
        if step == phase:
            break


def test_an_internal_root_still_runs_the_accepted_decision_116_path(tmp_path: Path) -> None:
    """**The bounded non-governed use `D149-R3` explicitly preserves.** An internal work root is
    not the governed external route and cannot be mistaken for it, so ``run`` is untouched."""
    private = d116._private_root(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    outcome = canary.run_canary_source_command(
        mode="run",
        run_id="d149-internal",
        source_instance_id=_BULK,
        work_root=str(tmp_path / "work"),
        repository_root=checkout,
        environ={EVIDENCE_ROOT_ENV: str(private)},
    )
    assert outcome.exit_code == 0
    assert "canary-source run" in "\n".join(outcome.lines)


def test_no_other_production_route_reaches_the_whole_run_entry_point() -> None:
    """**Proof 5.** The refusal is worth what its reachability analysis is worth.

    ``cli.py`` reaches the canary through exactly one function, and inside the module the whole-run
    entry point has exactly one caller -- the guarded operator surface. A future refactor that
    added a second route would fail here rather than quietly reopening the legacy path.
    """
    cli = Path(canary.__file__).resolve().parents[1] / "cli.py"
    cli_source = cli.read_text(encoding="utf-8")
    assert cli_source.count("run_canary_source_command") == 2, (
        "cli.py must reach the canary through exactly one entry point: its import and its call"
    )
    for forbidden in ("run_single_source_canary(", "run_single_source_canary_phase("):
        assert forbidden not in cli_source, f"cli.py must not reach {forbidden} directly"

    module = ast.parse(Path(canary.__file__).read_text(encoding="utf-8"))
    callers = {
        enclosing.name
        for enclosing in ast.walk(module)
        if isinstance(enclosing, ast.FunctionDef)
        for node in ast.walk(enclosing)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "run_single_source_canary"
    }
    assert callers == {"run_canary_source_command"}


def test_the_refusal_is_taken_before_the_run_is_entered() -> None:
    """A refusal that fired after the run started would still have created a world.

    Read from the source's own AST rather than inferred from a passing test, so a future edit that
    moved the guard below the call fails here even if every behavioural test still passed.
    """
    module = ast.parse(Path(canary.__file__).read_text(encoding="utf-8"))
    command = next(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef) and node.name == "run_canary_source_command"
    )
    guard = next(
        node
        for node in ast.walk(command)
        if isinstance(node, ast.If) and "mode == 'run'" in ast.unparse(node.test)
    )
    assert "external is not None" in ast.unparse(guard.test), "the guard must be envelope-keyed"
    assert any(isinstance(node, ast.Raise) for node in ast.walk(guard)), "the guard must refuse"
    call = next(
        node
        for node in ast.walk(command)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "run_single_source_canary"
    )
    assert guard.lineno < call.lineno, "the mode refusal must precede the whole-run call"


def test_decision_149_mints_no_authority_and_enables_nothing() -> None:
    """**Proof 6.** A cleanup is a cleanup: it authorizes nothing and switches nothing on."""
    from disclosure_drift.m3 import e0

    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is None
    assert e0.M3_3_E0_EXECUTION_AUTHORITY is None
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None

    for module in (canary, ri):
        source = Path(module.__file__).read_text(encoding="utf-8")
        for token in ("m3_acquire_enabled", "EXECUTION_AUTHORITY", "httpx", "http_client"):
            assert token not in source, f"{module.__name__} names {token}"
    # `SAFE_TO_EJECT` appears in `single_source_canary` exactly once, in prose stating that no
    # such state exists. Asserting its absence outright would forbid saying so.
    assert "There is no\n    ``SAFE_TO_EJECT`` state" in Path(canary.__file__).read_text(
        encoding="utf-8"
    )
    assert "SAFE_TO_EJECT" not in Path(ri.__file__).read_text(encoding="utf-8")


# ==========================================================================
# §4. What Decision 149 must NOT have changed
# ==========================================================================
def test_the_three_phases_and_the_two_boundaries_are_unchanged() -> None:
    """`D149-R6`: the phase architecture is preserved exactly."""
    from disclosure_drift.m3 import canary_phases as phases

    assert phases.CANARY_PHASE_SEQUENCE == ("f0", "f1", "f2")
    assert dict(phases.PHASE_PREDECESSOR) == {"f0": None, "f1": "f0", "f2": "f1"}
    assert dict(phases.PHASE_SUCCESSOR) == {"f0": "f1", "f1": "f2", "f2": None}
    assert set(canary.CANARY_PHASE_MODES) == {"phase-f0", "phase-f1", "phase-f2"}


def test_the_transport_pin_is_still_carried_by_every_production_envelope_call() -> None:
    """`D149` §11: the D144 tripwire, re-asserted against the module Decision 149 edited."""
    module = ast.parse(Path(canary.__file__).read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", "") == "require_external_envelope"
    ]
    assert len(calls) == 4
    for call in calls:
        keywords = {keyword.arg for keyword in call.keywords}
        assert "required_transport" in keywords


def test_parse_bulk_remains_canary_unreachable() -> None:
    """`D149-R5`: re-traced across the surfaces Decision 149 touched."""
    from disclosure_drift.m3 import canary_phases as phases

    for module in (canary, phases, ri):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "census_orchestrator" not in source
        assert "CensusOrchestrator" not in source
        assert "_parse_bulk" not in source


def test_the_repository_identity_contract_is_unchanged(tmp_path: Path) -> None:
    """`D149` §12: measured from the module's own location, both halves, no override."""
    checkout = Path(canary.__file__).resolve().parents[3]
    identity = ri.running_repository_identity()
    assert identity.head_sha == _git(checkout, "rev-parse", "HEAD")
    assert identity.tree_sha == _git(checkout, "rev-parse", "HEAD^{tree}")
    assert identity.contract == ri.REPOSITORY_IDENTITY_CONTRACT
    signature = set(inspect.signature(canary.run_canary_source_command).parameters)
    assert not {name for name in signature if "repository" in name and name != "repository_root"}


def test_a_successor_still_refuses_a_predecessor_from_another_revision(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`D149` §12: Decision 147's successor comparison survives the Decision 149 edits."""
    from disclosure_drift.m3 import canary_phases as phases

    private, work = d145._world(tmp_path)
    d145._sequence(private, work, run_id="d149-moved", through="f0")
    d147._repin(monkeypatch, d147._pin(head="c" * 40))
    with pytest.raises(phases.CanaryPhaseError, match="repository_head_sha"):
        d145._phase(private, work, "f1", run_id="d149-moved")
