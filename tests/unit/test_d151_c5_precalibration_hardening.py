"""D151-C5: targeted pre-calibration hardening -- the C4 findings, corrected and proved.

Four corrections, each proved against the attack that found it.

**C4 MINOR-1** -- the 50 GiB pre-F2 proof depended on the physical host having less than 50 GiB
free. It now runs through the accepted ``shutil.disk_usage`` seam at ``floor - 1`` and ``floor``
(``test_d151_c3_phase_runner``); the structural half of that proof lives here.

**C4 MINOR-2** -- the chunk child copied the coordinator's ``repository_head_sha`` and
``repository_tree_sha`` into its receipt without measuring anything. It now authenticates its own
code identity through the accepted ``require_clean_running_repository``, in its own process, before
it creates anything, and refuses a request that names any other commit or tree: I01-I10.

**C4 INFO-2** -- a consistent forgery of ``parser_id`` / ``parser_version`` across every chunk
receipt passed the chunk-to-chunk contract agreement. The contract is now held to the parser run
row the chunks actually wrote: P01-P05.

**C4 INFO-6** -- the accepted monolithic F0 finalizes its compact-evidence sidecar BEFORE the
blocking-terminal gate; the consolidated path merged it after. The ordering is confirmed from the
accepted source and behaviour, and the failed-F0 diagnostic state is now equivalent: C520-C523.

Every child process here is a real ``fork``/``exec`` of the interpreter, every repository is a real
Git repository, and the only seam is the accepted one-name redirect the whole D151 suite uses.
"""

from __future__ import annotations

import ast
import inspect
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c1_equivalence as eq  # noqa: E402
import test_d151_c3_phase_runner as pr  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3 import offline_parse  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.canary_phases import (  # noqa: E402
    PHASE_F0,
    PHASE_F1,
    CanaryPhaseError,
    read_phase_checkpoint,
    require_phase_admission,
)
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_RECEIPT_FILENAME,
    FINAL_WORLD_RECEIPT_FILENAME,
    ChunkEvidenceError,
    write_once_json,
)
from disclosure_drift.m3.chunk_storage import ChunkStorageError  # noqa: E402
from disclosure_drift.m3.compact_evidence import (  # noqa: E402
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    CompactEvidenceSidecar,
)
from disclosure_drift.m3.repository_identity import (  # noqa: E402
    RepositoryIdentity,
    RepositoryIdentityError,
    repository_identity_at,
)
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    WORKING_CATALOG_FILENAME,
    RunProgressLedger,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.sec.source_registry import SOURCES  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402

BATCH = 2


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The shared pin: a real, clean throwaway repository, through the accepted identity seam.

    The pin lives in ``test_d151_c1_chunk_plan`` and, since D151-C5, is applied inside every
    chunk child as well -- the child measures its own identity in its own process.
    """
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# Shared drivers
# ==========================================================================
def healthy_world(tmp_path: Path) -> tuple[Path, DataTree]:
    return c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)


def blocking_world(tmp_path: Path) -> tuple[Path, DataTree]:
    """A source that reaches the accepted ``failed`` parser terminal: blocking structural rows."""
    return c1.build_world(tmp_path, members=6, filings=2, shards=2, malformed=2)


def run_chunks(
    tmp_path: Path,
    database: Path,
    tree: DataTree,
    *,
    size: int = 2,
    label: str = "c",
    stop_after: int | None = None,
) -> Any:
    return c1x.run_chunked_f0(
        tmp_path,
        database,
        tree,
        chunk_members=size,
        label=label,
        batch_size=BATCH,
        stop_after=stop_after,
        repository=c1.PINNED,
    )


def consolidate(
    run: Any, database: Path, *, suffix: str = "", run_id: str = "c5-run"
) -> cc.ConsolidationResult:
    return cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / f"final{suffix}",
        run_id=run_id,
    )


def sealed_plan(root: Path, tree: DataTree, database: Path, *, chunk_members: int = 2) -> Any:
    """A plan written to disk with nothing executed yet: ``(plan, plan_path, chunk_root)``."""
    base = root / "plan-only"
    base.mkdir()
    plan = c1.build_plan(tree, database, chunk_members=chunk_members)
    plan_path = base / "plan.json"
    write_once_json(plan_path, dict(plan.as_record()))
    return plan, plan_path, base / "chunks"


def attempt_chunk(
    plan: Any,
    plan_path: Path,
    chunk_root: Path,
    index: int,
    *,
    database: Path,
    tree: DataTree,
    repository: RepositoryIdentity | None = None,
    parent_map_path: Path | None = None,
    predecessor_pid: int | None = None,
) -> tuple[Path, int, Any]:
    """Run chunk ``index`` in a fresh child and return ``(directory, attempt, outcome)``.

    ``outcome`` is the receipt on success, or the coordinator's refusal on failure.
    """
    bounds = plan.chunks[index]
    directory, attempt = ce.next_attempt_directory(chunk_root, bounds.chunk_id)
    request = c1x.chunk_request(
        plan_path=plan_path,
        chunk_id=bounds.chunk_id,
        attempt=attempt,
        attempt_directory=directory,
        database=database,
        tree=tree,
        parent_map_path=parent_map_path,
        batch_size=BATCH,
        repository=repository,
    )
    try:
        outcome: Any = ce.run_chunk(request, predecessor_pid=predecessor_pid)
    except ce.ChunkExecutionError as exc:
        outcome = exc
    return directory, attempt, outcome


def git(root: Path, *argv: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *argv], check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def commit_governing_change(root: Path, text: str) -> RepositoryIdentity:
    """Move the pinned repository's HEAD and tree with a real commit."""
    (root / "governing.txt").write_text(text, encoding="utf-8")
    git(root, "add", "governing.txt")
    git(root, "commit", "--quiet", "-m", "a governing change")
    return repository_identity_at(root)


def restore(root: Path, original: RepositoryIdentity, *, how: str) -> RepositoryIdentity:
    """Put the governing content back -- by a reset (same HEAD) or a revert (new HEAD)."""
    if how == "reset":
        git(root, "reset", "--hard", "--quiet", original.head_sha)
    else:
        git(root, "revert", "--no-edit", "HEAD")
    identity = repository_identity_at(root)
    assert identity.tree_sha == original.tree_sha
    assert identity.clean
    return identity


def receipt_path_of(run: Any, index: int) -> Path:
    bounds = run["plan"].chunks[index]
    receipt = run["receipts"][index]
    return (
        run["chunk_root"]
        / bounds.chunk_id
        / f"attempt-{receipt.attempt:03d}"
        / CHUNK_RECEIPT_FILENAME
    )


def edit_receipt(path: Path, mutate: Any) -> None:
    """Rewrite one chunk receipt in place, leaving every artifact byte-identical."""
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")


def artifact_bytes(run: Any) -> dict[str, bytes]:
    """Every chunk artifact except the receipts, by path."""
    return {
        path.relative_to(run["chunk_root"]).as_posix(): path.read_bytes()
        for path in sorted(run["chunk_root"].rglob("*"))
        if path.is_file() and path.name != CHUNK_RECEIPT_FILENAME
    }


def refusal_text(outcome: Any) -> str:
    assert isinstance(outcome, ce.ChunkExecutionError), outcome
    return str(outcome)


# ==========================================================================
# MINOR-1: the structural half (the behavioural proof is in test_d151_c3_phase_runner)
# ==========================================================================
def test_c501_c504_the_fifty_gib_proof_is_host_independent() -> None:
    """C501/C504: the constant is 50 GiB, and its proof never asks the physical host.

    The behavioural halves -- refused at ``floor - 1``, admitted at ``floor`` and ``floor + 1``,
    all through the accepted seam -- run in ``test_d151_c3_phase_runner``. This asserts the
    property C4 MINOR-1 named: the proof's source no longer removes the seam, no longer reads the
    host's own free space, and no longer asserts anything about it.
    """
    assert canary.PRE_F2_MINIMUM_FREE_BYTES == 50 * 1024**3
    source = inspect.getsource(pr.test_the_fifty_gib_guard_is_not_weakened)
    tree = ast.parse(inspect.cleandoc(source) if source.startswith(" ") else source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert "shutil" not in names
    assert "disk_usage" not in attributes and "disk_usage" not in names
    # Every free-space reading the proof hands the accepted machinery is the seam's, and the
    # seam is never removed: the readings are the floor's neighbours, and nothing else.
    readings = {
        ast.unparse(keyword.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "free_bytes"
    }
    assert readings == {"floor - 1", "floor", "floor + 1"}
    # The seam itself is untouched: the phase program pins the MEASUREMENT and nothing else.
    assert "shutil.disk_usage = lambda" in pr._PHASE_PROGRAM
    assert "PRE_F2_MINIMUM_FREE_BYTES" not in pr._PHASE_PROGRAM


# ==========================================================================
# MINOR-2: I01-I10 -- the chunk child authenticates its own code identity
# ==========================================================================
def test_i01_c506_a_correct_child_identity_executes_and_the_receipt_is_a_measurement(
    tmp_path: Path,
) -> None:
    """I01/C506: the pinned repository is the child's, so every chunk runs -- and records it."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    pinned = c1.pinned_repository()
    assert run["receipts"]
    for receipt in run["receipts"]:
        assert receipt.status == "complete"
        assert receipt.repository_head_sha == pinned.head_sha
        assert receipt.repository_tree_sha == pinned.tree_sha
    assert consolidate(run, database).receipt.status == "complete"


def test_c506_the_child_authenticates_before_any_read_or_write() -> None:
    """C506: structurally, the measurement is the FIRST thing the chunk body does.

    Located through the module's own syntax tree: the first statement of ``execute_chunk_body``
    after its docstring binds the result of ``authenticate_running_repository``, and every
    ``mkdir`` in the function comes after it.
    """
    source = Path(ce.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    body = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "execute_chunk_body"
    )
    first = body.body[1]  # body[0] is the docstring
    assert isinstance(first, ast.Assign)
    assert isinstance(first.value, ast.Call)
    assert isinstance(first.value.func, ast.Name)
    assert first.value.func.id == "authenticate_running_repository"
    creations = [
        node.lineno
        for node in ast.walk(body)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "mkdir"
    ]
    assert creations
    assert min(creations) > first.lineno


@pytest.mark.parametrize("field", ["head_sha", "tree_sha"])
def test_i02_i03_c507_c508_a04_a05_a_request_naming_another_revision_is_refused_by_the_child(
    tmp_path: Path, field: str
) -> None:
    """I02/I03: the coordinator's claim differs from the measurement -- the CHILD refuses.

    A04/A05: this is a stale coordinator identity, handed to a child whose code is the pinned
    revision. The refusal is the child's own, before anything is created.
    """
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    plan, plan_path, chunk_root = sealed_plan(tmp_path, tree, database)
    stale = replace(c1.pinned_repository(), **{field: "d" * 40})
    directory, attempt, outcome = attempt_chunk(
        plan, plan_path, chunk_root, 0, database=database, tree=tree, repository=stale
    )
    text = refusal_text(outcome)
    assert "exit status" in text
    assert "MEASURED by the chunk process itself" in text
    assert "refused before anything is created" in text
    # I08 / C513: nothing was created and no receipt exists, valid or otherwise.
    assert not directory.exists()
    assert ce.completed_chunk_receipt(chunk_root, plan.chunks[0].chunk_id) is None
    assert ce.next_attempt_directory(chunk_root, plan.chunks[0].chunk_id) == (directory, attempt)


@pytest.mark.parametrize("ambiguity", ["modified_tracked", "untracked"])
def test_i04_c509_a09_a_dirty_child_checkout_is_refused_by_the_accepted_predicate(
    tmp_path: Path, ambiguity: str
) -> None:
    """I04/C509/A09: the accepted clean-repository predicate refuses inside the child.

    The request names the clean pinned identity -- the coordinator's claim is perfectly
    consistent -- and the child still refuses, because what it measures is not clean.
    """
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    plan, plan_path, chunk_root = sealed_plan(tmp_path, tree, database)
    root = c1.PINNED_ROOT
    assert root is not None
    if ambiguity == "modified_tracked":
        (root / "governing.txt").write_text("an uncommitted edit\n", encoding="utf-8")
        expected = "modified tracked (1): governing.txt"
    else:
        (root / "untracked.py").write_text("# a file no commit describes\n", encoding="utf-8")
        expected = "untracked, non-ignored (1): untracked.py"
    directory, _attempt, outcome = attempt_chunk(
        plan, plan_path, chunk_root, 0, database=database, tree=tree
    )
    text = refusal_text(outcome)
    assert "clean tracked working tree" in text
    assert expected in text
    assert not directory.exists()
    assert ce.completed_chunk_receipt(chunk_root, plan.chunks[0].chunk_id) is None


def test_i05_c510_a_moved_child_head_is_refused(tmp_path: Path) -> None:
    """I05/C510: the request was built, then the governing revision moved. The child refuses."""
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    plan, plan_path, chunk_root = sealed_plan(tmp_path, tree, database)
    root = c1.PINNED_ROOT
    assert root is not None
    original = c1.pinned_repository()
    moved = commit_governing_change(root, "the revision moved after the request was built\n")
    assert moved.head_sha != original.head_sha
    assert moved.tree_sha != original.tree_sha
    directory, _attempt, outcome = attempt_chunk(
        plan, plan_path, chunk_root, 0, database=database, tree=tree, repository=original
    )
    text = refusal_text(outcome)
    assert "MEASURED by the chunk process itself" in text
    assert f"{original.head_sha}/{original.tree_sha}" in text
    assert f"{moved.head_sha}/{moved.tree_sha}" in text
    assert not directory.exists()


def test_i06_c511_a07_a08_a_governing_change_between_chunks_stops_the_successor(
    tmp_path: Path,
) -> None:
    """I06/C511/A07: chunk 0 valid -> governing code changed -> chunk 1 refuses.

    A08: reverting the edit before consolidation rescues nothing. Chunk 1 never completed, so
    the consolidator finds no verified copy of it; chunk 0 is untouched throughout.
    """
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    run = run_chunks(tmp_path, database, tree, stop_after=1)
    plan = run["plan"]
    assert plan.chunk_count == 2
    survivor = run["receipts"][0]
    root = c1.PINNED_ROOT
    assert root is not None
    original = c1.pinned_repository()
    commit_governing_change(root, "a governing change between chunk 0 and chunk 1\n")
    directory, _attempt, outcome = attempt_chunk(
        plan,
        run["plan_path"],
        run["chunk_root"],
        1,
        database=database,
        tree=tree,
        repository=original,
        predecessor_pid=survivor.pid,
    )
    assert "refused before anything is created" in refusal_text(outcome)
    assert not directory.exists()
    assert ce.completed_chunk_receipt(run["chunk_root"], plan.chunks[1].chunk_id) is None
    still_there = ce.completed_chunk_receipt(run["chunk_root"], plan.chunks[0].chunk_id)
    assert still_there is not None
    assert still_there[0].manifest.digest == survivor.manifest.digest
    # A08: the edit is reverted; the live identity is the original again; consolidation still
    # refuses, because the chunk that was refused under the changed code does not exist.
    restore(root, original, how="reset")
    with pytest.raises(ChunkStorageError, match="no verified copy on either tier"):
        consolidate(run, database)
    assert not (run["base"] / "final").exists()


@pytest.mark.parametrize("how", ["reset", "revert"])
def test_i07_c512_a08_a_later_revert_cannot_rescue_a_chunk_that_ran_under_changed_code(
    tmp_path: Path, how: str
) -> None:
    """I07/C512: code changed -> chunk executes under it -> code reverted -> consolidation.

    The coordinator re-derived the identity after the change, so chunk 1 ran with a request that
    matched its own measurement and completed. Its receipt records the CHANGED revision -- a
    measurement -- so after the revert it can never look as though it ran under the restored one,
    and the consolidator refuses it against chunk 0 whatever the live checkout says.
    """
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    run = run_chunks(tmp_path, database, tree, stop_after=1)
    plan = run["plan"]
    root = c1.PINNED_ROOT
    assert root is not None
    original = c1.pinned_repository()
    changed = commit_governing_change(root, "code that ran chunk 1\n")
    directory, _attempt, outcome = attempt_chunk(
        plan,
        run["plan_path"],
        run["chunk_root"],
        1,
        database=database,
        tree=tree,
        repository=changed,
        predecessor_pid=run["receipts"][0].pid,
    )
    assert not isinstance(outcome, Exception), outcome
    assert outcome.status == "complete"
    assert (outcome.repository_head_sha, outcome.repository_tree_sha) == (
        changed.head_sha,
        changed.tree_sha,
    )
    assert outcome.repository_tree_sha != original.tree_sha
    live = restore(root, original, how=how)
    assert live.tree_sha == original.tree_sha
    # The receipt on disk still says what it measured: the changed revision, not the restored one.
    stored = json.loads((directory / CHUNK_RECEIPT_FILENAME).read_text(encoding="utf-8"))
    assert stored["repository_tree_sha"] == changed.tree_sha != live.tree_sha
    with pytest.raises(cc.ChunkConsolidationError, match="executed under repository"):
        consolidate(run, database)
    assert not (run["base"] / "final").exists()


def test_i09_c514_the_accepted_mechanism_is_called_and_load_bearing_in_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """I09/C514: the chunk body calls the accepted predicate, once, and obeys its refusal."""
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    plan, plan_path, chunk_root = sealed_plan(tmp_path, tree, database)
    accepted = ce.require_clean_running_repository
    calls: list[RepositoryIdentity] = []

    def spy() -> RepositoryIdentity:
        identity = accepted()
        calls.append(identity)
        return identity

    monkeypatch.setattr(ce, "require_clean_running_repository", spy)
    directory, attempt = ce.next_attempt_directory(chunk_root, plan.chunks[0].chunk_id)
    receipt = ce.execute_chunk_body(
        c1x.chunk_request(
            plan_path=plan_path,
            chunk_id=plan.chunks[0].chunk_id,
            attempt=attempt,
            attempt_directory=directory,
            database=database,
            tree=tree,
            batch_size=BATCH,
        )
    )
    assert calls == [c1.pinned_repository()]
    assert receipt.repository_head_sha == calls[0].head_sha
    assert receipt.repository_tree_sha == calls[0].tree_sha

    def refuse() -> RepositoryIdentity:
        message = "synthetic refusal from the accepted mechanism"
        raise RepositoryIdentityError(message)

    monkeypatch.setattr(ce, "require_clean_running_repository", refuse)
    other, other_attempt = ce.next_attempt_directory(chunk_root, plan.chunks[1].chunk_id)
    with pytest.raises(RepositoryIdentityError, match="synthetic refusal"):
        ce.execute_chunk_body(
            c1x.chunk_request(
                plan_path=plan_path,
                chunk_id=plan.chunks[1].chunk_id,
                attempt=other_attempt,
                attempt_directory=other,
                database=database,
                tree=tree,
                batch_size=BATCH,
            )
        )
    assert not other.exists()


def test_i09_c514_the_accepted_mechanism_is_load_bearing_in_the_child_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """I09 in the real child: refusing inside the accepted mechanism refuses the chunk.

    The child's bootstrap replaces the accepted predicate with one that refuses, and nothing
    else. A child that did not call it would complete; this one exits non-zero, creates nothing,
    and names the refusal.
    """
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    plan, plan_path, chunk_root = sealed_plan(tmp_path, tree, database)
    program = (
        "import sys\n"
        "from disclosure_drift.m3 import chunk_execution as ce\n"
        "from disclosure_drift.m3.repository_identity import RepositoryIdentityError\n"
        "def _refuse():\n"
        "    raise RepositoryIdentityError('synthetic child refusal')\n"
        "ce.require_clean_running_repository = _refuse\n"
        "sys.exit(ce._child_main(sys.argv[1]))\n"
    )
    monkeypatch.setattr(ce, "_CHILD_BOOTSTRAP", program)
    directory, _attempt, outcome = attempt_chunk(
        plan, plan_path, chunk_root, 0, database=database, tree=tree
    )
    assert "synthetic child refusal" in refusal_text(outcome)
    assert not directory.exists()


def test_i10_no_second_git_parser_exists_in_chunk_execution() -> None:
    """I10: the child reaches the ONE accepted derivation, and implements none of its own."""
    source = Path(ce.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for needle in ('"git"', "'git'", "porcelain", "rev-parse", "ls-files", "show-toplevel"):
        assert needle not in source, needle
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    for forbidden in (
        "repository_identity_at",
        "running_repository_identity",
        "repository_root_containing",
        "_git",
        "environ",
        "getenv",
    ):
        assert forbidden not in names and forbidden not in attributes, forbidden
    # The only subprocess the module starts is the interpreter running the chunk child.
    spawns = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
    ]
    assert len(spawns) == 1
    argv = spawns[0].args[0]
    assert isinstance(argv, ast.List)
    executable = argv.elts[0]
    assert isinstance(executable, ast.Attribute)
    assert executable.attr == "executable"
    assert isinstance(executable.value, ast.Name)
    assert executable.value.id == "sys"
    # The accepted predicate is imported from the accepted module and called exactly once, inside
    # authenticate_running_repository.
    assert (
        "from disclosure_drift.m3.repository_identity import (\n"
        "    RepositoryIdentity,\n"
        "    require_clean_running_repository,\n"
        ")"
    ) in source
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "require_clean_running_repository"
    ]
    assert len(calls) == 1
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "authenticate_running_repository"
    )
    assert any(node is calls[0] for node in ast.walk(function))
    assert "authenticate_running_repository" in ce.__all__


# ==========================================================================
# INFO-2: P01-P05 -- parser identity must agree with the reduced run truth
# ==========================================================================
def test_p01_p03_c515_c517_one_forged_parser_identity_refuses(tmp_path: Path) -> None:
    """P01/P03: a single chunk that disagrees is refused by the chunk-to-chunk contract check."""
    database, tree = healthy_world(tmp_path)
    for field, value in (("parser_id", "forged-parser"), ("parser_version", "9.9.9-forged")):
        run = run_chunks(tmp_path, database, tree, label=f"one-{field}")
        edit_receipt(
            receipt_path_of(run, 1),
            lambda document, field=field, value=value: document["execution_contract"].__setitem__(
                field, value
            ),
        )
        with pytest.raises(cc.ChunkConsolidationError, match="different execution contract"):
            consolidate(run, database)
        assert not (run["base"] / "final").exists()


@pytest.mark.parametrize(
    ("field", "value"), [("parser_id", "forged-parser"), ("parser_version", "9.9.9-forged")]
)
def test_p02_p04_c516_c518_a10_a11_a12_a_unanimous_forgery_is_refused_by_the_run_row(
    tmp_path: Path, field: str, value: str
) -> None:
    """P02/P04: EVERY receipt forged consistently passes agreement -- and is refused by the truth.

    A10/A11: the receipts agree with one another perfectly. A12: what they say differs from the
    parser run row every chunk wrote into its manifest-bound catalog, and that row is what the
    final world is built from. Every artifact other than the receipts stays byte-identical, so
    the new predicate is the only thing standing between the forgery and a complete world.
    """
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    before = artifact_bytes(run)
    for index in range(len(run["receipts"])):
        edit_receipt(
            receipt_path_of(run, index),
            lambda document: document["execution_contract"].__setitem__(field, value),
        )
    assert artifact_bytes(run) == before
    # The chunk-to-chunk agreement check is satisfied: every chunk carries the same forged claim.
    inputs = cc.resolve_chunk_inputs(run["plan"], internal_root=run["chunk_root"])
    assert {getattr(item.receipt.execution_contract, field) for item in inputs} == {value}
    with pytest.raises(cc.ChunkConsolidationError) as raised:
        consolidate(run, database)
    assert "does not describe its own evidence" in str(raised.value)
    assert value in str(raised.value)
    world = run["base"] / "final"
    assert not (world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    assert not (world / COMPACT_EVIDENCE_SIDECAR_FILENAME).exists()
    # Refused before the reduced row was written: the transaction rolled back, so the world holds
    # no run row and no loaded table.
    with connect(world / WORKING_CATALOG_FILENAME, writer=False) as connection:
        counts = ce.table_row_counts(connection)
    assert counts["census_parser_runs"] == 0
    assert counts["census_parsed_records"] == 0
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
    finally:
        ledger.close()


def test_p02_the_truth_check_is_load_bearing(tmp_path: Path) -> None:
    """The mutation stated as a test: neutralise the truth check and the forgery completes."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    for index in range(len(run["receipts"])):
        edit_receipt(
            receipt_path_of(run, index),
            lambda document: document["execution_contract"].__setitem__("parser_id", "forged"),
        )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cc, "_require_parser_run_truth", lambda **_kwargs: None)
        bypassed = consolidate(run, database, suffix="-bypassed", run_id="bypassed")
    assert bypassed.receipt.status == "complete"
    # ... and with the check in place the same chunks are refused.
    with pytest.raises(cc.ChunkConsolidationError, match="does not describe its own evidence"):
        consolidate(run, database, suffix="-guarded", run_id="guarded")


def test_p05_c519_the_correct_parser_identity_admits_and_matches_the_run_row(
    tmp_path: Path,
) -> None:
    """P05/C519: the positive control -- contract == run row == the accepted constants."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    result = consolidate(run, database)
    assert result.receipt.status == "complete"
    contract = result.inputs[0].receipt.execution_contract
    with connect(result.world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
        rows = connection.execute(
            "SELECT parser_id, parser_version FROM census_parser_runs"
        ).fetchall()
    assert len(rows) == 1
    assert str(rows[0]["parser_id"]) == contract.parser_id == ce._BULK_PARSER_ID
    assert (
        str(rows[0]["parser_version"])
        == contract.parser_version
        == str(SOURCES[c1.SOURCE_ID].parser_version)
    )


def test_the_truth_check_does_not_promote_batch_size_into_semantics(tmp_path: Path) -> None:
    """``batch_size`` stays execution-only: no run row records it, and the truth check never
    reads it. The accepted chunk-to-chunk contract agreement already governs it (R23)."""
    source = inspect.getsource(cc._require_parser_run_truth)
    assert "batch_size" not in source.split('"""')[2]  # the code, not the docstring
    assert set(inspect.signature(cc._require_parser_run_truth).parameters) == {
        "contract",
        "parser_id",
        "parser_version",
    }


# ==========================================================================
# INFO-6: C520-C523 -- failed-F0 diagnostic sidecar parity
# ==========================================================================
def test_c520_the_accepted_f0_finalizes_its_sidecar_before_the_gate() -> None:
    """C520, from the accepted source: sidecar finalization -> require_f0_success -> terminal.

    Read from the accepted functions' own text rather than remembered. ``materialize_one_planned
    _source`` finishes the compact evidence -- the durable diagnostic sidecar's source row -- and
    only then returns; ``_f0`` calls it, then the gate, then the ledger terminal. And the
    consolidator now does the same three things in the same order.
    """
    materialize = inspect.getsource(offline_parse.materialize_one_planned_source)
    assert materialize.index("evidence.finish()") < materialize.rindex(
        "return SingleSourceOutcome("
    )
    f0 = inspect.getsource(canary._f0)
    assert (
        f0.index("materialize_one_planned_source(")
        < f0.index("require_f0_success(")
        < f0.index("mark_parsed(")
    )
    consolidator = inspect.getsource(cc.consolidate_chunks)
    assert (
        consolidator.index("_merge_sidecar(")
        < consolidator.index("require_f0_success(")
        < consolidator.index("mark_parsed(")
        < consolidator.index("write_phase_checkpoint(")
        < consolidator.index("FINAL_WORLD_RECEIPT_FILENAME")
    )


def test_c520_the_accepted_phase_machinery_leaves_a_finalized_sidecar_on_a_failed_f0(
    tmp_path: Path,
) -> None:
    """C520, behaviourally, through the ACCEPTED phase machinery in a fresh process.

    ``_run_phase_locked`` over a blocking source fails at the gate and leaves a world holding the
    durable rows, a finalized sidecar with the whole member manifest and the source row, a ledger
    still ``in_progress``, no F0 checkpoint and no result document.
    """
    database, tree = blocking_world(tmp_path)
    mono_root = tmp_path / "mono"
    (mono_root / "work").mkdir(parents=True)
    outcome = pr.run_accepted_phase(
        phase=PHASE_F0,
        work_root=mono_root / "work",
        database=database,
        tree=tree,
        run_id="mono-failed",
        check=False,
    )
    assert outcome.get("failed")
    assert "blocking terminal" in outcome["stderr"]
    world = mono_root / "work" / "mono-failed"
    assert {path.name for path in world.iterdir()} == {
        WORKING_CATALOG_FILENAME,
        PROGRESS_LEDGER_FILENAME,
        COMPACT_EVIDENCE_SIDECAR_FILENAME,
    }
    sidecar = CompactEvidenceSidecar(world / COMPACT_EVIDENCE_SIDECAR_FILENAME)
    try:
        evidence = sidecar.source_evidence(c1.OBSERVATION)
        members = sidecar.members(c1.OBSERVATION)
    finally:
        sidecar.close()
    assert evidence is not None
    assert int(evidence["members"]) == len(members) > 0
    assert str(evidence["completeness_digest"])
    measured = eq.measure(world)
    assert measured["parser_state"] == "failed"
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        progress = ledger.progress(c1.INSTANCE)
        assert progress is not None
        assert progress.state == "in_progress"
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
    finally:
        ledger.close()


def failed_chunked_world(tmp_path: Path, database: Path, tree: DataTree, *, size: int) -> Path:
    """A blocking source, chunked, consolidated, and refused by the accepted gate."""
    run = run_chunks(tmp_path, database, tree, size=size, label=f"failed-n{size}")
    world = run["base"] / "final"
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        consolidate(run, database)
    return world


@pytest.mark.parametrize("size", [1, 2, 3, 10_000])
def test_c521_a13_a_failed_chunked_f0_leaves_the_monolithic_diagnostic_state(
    tmp_path: Path, size: int
) -> None:
    """C521/A13: failed monolithic diagnostic rows + sidecar == failed chunked ones.

    Two accepted references, one blocking source, every partition size: the accepted ``_f0``
    driven directly (its gate raising), and the accepted phase machinery in a fresh process. The
    consolidated world the gate refused is measured with the SAME instrument the healthy
    equivalence uses -- every governed table, the run row, the plan terminal, the whole member
    manifest, the source evidence row, the manifest digest and the sidecar identity -- and every
    one of them is equal, subject only to the accepted wall-clock columns.
    """
    database, tree = blocking_world(tmp_path)
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        eq.monolithic_f0(database, tree, tmp_path / "mono", strict=True)
    reference = eq.measure(tmp_path / "mono")
    assert reference["parser_state"] == "failed"
    assert reference["source_evidence"]
    assert reference["members"]

    world = failed_chunked_world(tmp_path, database, tree, size=size)
    candidate = eq.measure(world)
    eq.assert_equivalent(reference, candidate)
    assert {path.name for path in world.iterdir()} == {
        path.name for path in (tmp_path / "mono").iterdir()
    }
    for directory in (world, tmp_path / "mono"):
        ledger = RunProgressLedger(directory / PROGRESS_LEDGER_FILENAME)
        try:
            progress = ledger.progress(c1.INSTANCE)
            assert progress is not None
            assert progress.state == "in_progress"
            assert read_phase_checkpoint(ledger, PHASE_F0) is None
        finally:
            ledger.close()


def test_c521_the_phase_machinery_reference_agrees_too(tmp_path: Path) -> None:
    """C521 against the accepted phase path: the fresh-process F0 world is the same world."""
    database, tree = blocking_world(tmp_path)
    mono_root = tmp_path / "mono"
    (mono_root / "work").mkdir(parents=True)
    outcome = pr.run_accepted_phase(
        phase=PHASE_F0,
        work_root=mono_root / "work",
        database=database,
        tree=tree,
        run_id="mono-failed",
        check=False,
    )
    assert outcome.get("failed")
    reference = eq.measure(mono_root / "work" / "mono-failed")
    world = failed_chunked_world(tmp_path, database, tree, size=2)
    eq.assert_equivalent(reference, eq.measure(world))


def test_c522_a14_a_failed_chunked_f0_still_has_no_terminal(tmp_path: Path) -> None:
    """C522/A14: the sidecar is there; the terminal is not. Failure remains failure."""
    database, tree = blocking_world(tmp_path)
    world = failed_chunked_world(tmp_path, database, tree, size=2)
    assert (world / COMPACT_EVIDENCE_SIDECAR_FILENAME).is_file()
    assert not (world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    assert not (world / "canary_result.json").exists()
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        progress = ledger.progress(c1.INSTANCE)
        assert progress is not None
        assert progress.state == "in_progress"
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
        assert read_phase_checkpoint(ledger, PHASE_F1) is None
    finally:
        ledger.close()
    with connect(world / WORKING_CATALOG_FILENAME, writer=False) as connection:
        row = connection.execute(
            "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
            (c1.INSTANCE,),
        ).fetchone()
        counts = ce.table_row_counts(connection)
    assert str(row["parser_state"]) == "failed"
    assert counts["census_parsed_records"] > 0


def test_c523_a15_a_failed_chunked_f0_still_cannot_admit_f1(tmp_path: Path) -> None:
    """C523/A15: refused by the accepted admission rule directly AND by the accepted machinery.

    The refused world is laid out where the accepted phase path expects it, and F1 is driven
    through ``_run_phase_locked`` in a fresh process: it attaches the world, finds no durable F0
    terminal, and refuses for the accepted reason.
    """
    database, tree = blocking_world(tmp_path)
    root = tmp_path / "chunked"
    (root / "work").mkdir(parents=True)
    run = run_chunks(root, database, tree, label="chunked-failed")
    world = root / "work" / "failed-run"
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        cc.consolidate_chunks(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            world_directory=world,
            run_id="failed-run",
        )
    assert (world / COMPACT_EVIDENCE_SIDECAR_FILENAME).is_file()
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        with pytest.raises(CanaryPhaseError, match="no durable terminal checkpoint"):
            require_phase_admission(
                ledger,
                phase=PHASE_F1,
                run_id="failed-run",
                source_instance_id=c1.INSTANCE,
                execution_identity="x",
                repository_head_sha="a" * 40,
                repository_tree_sha="b" * 40,
                catalog_source_sha256="c" * 64,
                migration_head=15,
                plan_fingerprint="f",
            )
    finally:
        ledger.close()
    outcome = pr.run_accepted_phase(
        phase=PHASE_F1,
        work_root=root / "work",
        database=database,
        tree=tree,
        run_id="failed-run",
        check=False,
    )
    assert outcome.get("failed")
    assert "no durable terminal checkpoint" in outcome["stderr"]


def test_the_sidecar_parity_path_cannot_bypass_the_gate(tmp_path: Path) -> None:
    """M9 stated as a test: merging the sidecar first does not weaken require_f0_success.

    With the accepted gate neutralised the blocking world completes -- the gate is load-bearing
    -- and with it in place the identical chunks are refused after the sidecar was merged.
    """
    database, tree = blocking_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cc, "require_f0_success", lambda outcome: outcome)
        bypassed = consolidate(run, database, suffix="-bypassed", run_id="bypassed")
    assert bypassed.receipt.status == "complete"
    assert bypassed.receipt.parser_state_after == "failed"
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        consolidate(run, database, suffix="-guarded", run_id="guarded")
    assert (run["base"] / "final-guarded" / COMPACT_EVIDENCE_SIDECAR_FILENAME).is_file()
    assert not (run["base"] / "final-guarded" / FINAL_WORLD_RECEIPT_FILENAME).exists()


def test_the_gate_still_sees_the_complete_outcome(tmp_path: Path) -> None:
    """The gate is asked over the complete derived outcome -- evidence totals included -- exactly
    as ``_f0`` asks it over the complete accepted outcome, and a healthy world still completes."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    seen: list[Any] = []
    accepted = cc.require_f0_success

    def observe(outcome: Any) -> Any:
        seen.append(outcome)
        return accepted(outcome)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cc, "require_f0_success", observe)
        result = consolidate(run, database)
    assert result.receipt.status == "complete"
    assert len(seen) == 1
    gated = seen[0]
    assert gated.members == result.receipt.members == run["plan"].total_members
    assert gated.completeness_digest == result.receipt.completeness_digest
    assert gated.outcome.parser_state_after == "completed"


# ==========================================================================
# Preservation: C526-C528 (C524/C525 are re-run through the existing hostile oracles)
# ==========================================================================
def test_c526_a17_the_large_table_merge_is_still_set_based() -> None:
    """C526/A17: nothing added by C5 walks a row. The three merge shapes are unchanged."""
    source = Path(cc.__file__).read_text(encoding="utf-8")
    assert 'f"{verb} {table} ({projection}) "' in source
    assert "ORDER BY {key}, chunk_ordinal" in source
    assert "ROW_NUMBER() OVER (PARTITION BY {key} ORDER BY chunk_ordinal)" in source
    assert "ORDER BY accession_observation_id, priority, chunk_ordinal" in source
    assert source.count("executemany(") == 1
    lines = source.splitlines()
    bodies = {
        node.name: "\n".join(lines[node.lineno - 1 : node.end_lineno])
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef)
    }
    for name in (
        "_sorted_bulk_load",
        "_keyed_first_last_load",
        "_load_accession_observations",
        "consolidate_chunks",
        "_require_parser_run_truth",
    ):
        body = bodies[name]
        assert "executemany" not in body, name
        assert "for row in" not in body, name
        assert "INSERT" not in body or "SELECT" in body, name


def test_c527_a18_the_single_pass_cap_is_unchanged() -> None:
    """C527/A18: nine chunks, ten attachments, one slot of headroom, no ten-chunk plan."""
    assert cp.SINGLE_PASS_CHUNK_CAP == 9
    assert cp.RESERVED_ATTACHMENT_HEADROOM == 1
    assert cc.attachment_limit() == 10
    assert cc.require_attachable(9, limit=10) == 9
    with pytest.raises(cc.ChunkConsolidationError, match="single-pass chunked-F0"):
        cc.require_attachable(10, limit=10)


def test_c528_a19_a20_activation_capacity_and_calibration_remain_closed() -> None:
    """C528/A19/A20: every authority and every capacity constant is still None; no CLI reach."""
    assert ce.REAL_CHUNKED_F0_EXECUTION_AUTHORITY == (
        "M3_3_D151_C12_ONE_REAL_30K_DENSE_PREFIX_INTERNAL_NVME_CALIBRATION_AUTHORIZED"
    )
    assert cs.REAL_CHUNK_TRANSFER_AUTHORITY is None
    assert cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    assert cp.PRODUCTION_CHUNK_MEMBERS is None
    assert cs.INTERNAL_RESERVE_BYTES is None
    assert cs.CHUNK_PEAK_REQUIREMENT_BYTES is None
    assert ce.require_real_chunk_execution_authority() == (
        "M3_3_D151_C12_ONE_REAL_30K_DENSE_PREFIX_INTERNAL_NVME_CALIBRATION_AUTHORIZED"
    )
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_chunk_transfer_authority()
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_internal_reclaim_authority()
    from disclosure_drift import cli

    cli_source = Path(cli.__file__).read_text(encoding="utf-8")
    for name in ("chunk_plan", "chunk_execution", "chunk_storage", "chunk_consolidation"):
        assert name not in cli_source, name
    for module in (ce, cc):
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert "environ" not in names and "environ" not in attributes, module.__name__
        assert "getenv" not in names and "getenv" not in attributes, module.__name__
        assert "DISCLOSURE_DRIFT" not in source, module.__name__
        assert "from disclosure_drift.m3.e0" not in source, module.__name__
    assert ChunkEvidenceError is not None
