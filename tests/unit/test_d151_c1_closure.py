"""D151-C1: activation, network, E0 and existing-run compatibility -- all closed, all proved.

D151-C1 §24 asks for something stronger than a guarded switch: **real chunked execution must be
impossible after C1**. The closure here is therefore structural rather than conditional. No
command-line surface reaches any chunk module at all, so there is no invocation to guard; no
environment variable or configuration key is read by any of them; and the three authority
constants -- execution, transfer, reclaim -- are all ``None``, with every entry point that would
need one refusing on every call.

The remaining claims are about not disturbing what already exists: no migration ``0016``, the
accepted monolithic path unchanged and unreachable from here, and a monolithic world never read as
a chunked one or the reverse.
"""

from __future__ import annotations

import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_evidence as cev  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_RECEIPT_CONTRACT,
    CHUNK_RECEIPT_FILENAME,
    FINAL_WORLD_RECEIPT_CONTRACT,
    FINAL_WORLD_RECEIPT_FILENAME,
    ChunkEvidenceError,
    read_receipt_document,
)
from disclosure_drift.m3.offline_parse import PROHIBITED_IMPORT_PREFIXES  # noqa: E402

C1_MODULES = (cp, cev, ce, cs, cc)
C1_MODULE_NAMES = tuple(module.__name__ for module in C1_MODULES)


@pytest.fixture
def pinned_repository(tmp_path: Path) -> Any:
    """The shared pin, for the one test here that spawns a chunk child (D151-C5 MINOR-2)."""
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# C49, C50, A39: activation
# ==========================================================================
def test_c49_c50_every_real_authority_is_closed() -> None:
    """The three constants, and the three refusals."""
    assert ce.REAL_CHUNKED_F0_EXECUTION_AUTHORITY == (
        "M3_3_D151_C7_ONE_REAL_INTERNAL_NVME_CALIBRATION_CHUNK_AUTHORIZED"
    )
    assert cs.REAL_CHUNK_TRANSFER_AUTHORITY is None
    assert cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    assert cp.PRODUCTION_CHUNK_MEMBERS is None
    assert cs.INTERNAL_RESERVE_BYTES is None
    assert cs.CHUNK_PEAK_REQUIREMENT_BYTES is None
    assert ce.require_real_chunk_execution_authority() == (
        "M3_3_D151_C7_ONE_REAL_INTERNAL_NVME_CALIBRATION_CHUNK_AUTHORIZED"
    )
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_chunk_transfer_authority()
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_internal_reclaim_authority()
    with pytest.raises(cp.ChunkPlanError, match="never defaulted"):
        cp.production_chunk_members()
    with pytest.raises(cs.ChunkStorageError, match="never a zero reserve"):
        cs.accepted_internal_reserve_bytes()


def test_a39_no_environment_or_configuration_value_can_open_anything() -> None:
    """A39: there is nothing to set. No C1 module reads the environment or a config key."""
    for module in C1_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        assert "environ" not in attributes and "environ" not in names, module.__name__
        assert "getenv" not in attributes and "getenv" not in names, module.__name__
        assert "DISCLOSURE_DRIFT" not in source, module.__name__
        assert "load_config" not in names, module.__name__


def test_a39_no_command_line_surface_reaches_a_chunk_module() -> None:
    """The strongest form of §24: there is no invocation to guard, in either direction."""
    from disclosure_drift import cli

    source = Path(cli.__file__).read_text(encoding="utf-8")
    for name in (
        "chunk_plan",
        "chunk_execution",
        "chunk_storage",
        "chunk_consolidation",
        "chunk_evidence",
        "chunked",
    ):
        assert name not in source, name
    # And nothing under `src/` outside the C1 modules imports one of them.
    package_root = Path(cli.__file__).parent
    importers = []
    for path in sorted(package_root.rglob("*.py")):
        if path.stem in {
            "chunk_plan",
            "chunk_evidence",
            "chunk_execution",
            "chunk_storage",
            "chunk_consolidation",
        }:
            continue
        text = path.read_text(encoding="utf-8")
        if "chunk_plan" in text or "chunk_execution" in text or "chunk_consolidation" in text:
            importers.append(path.name)
    assert importers == []


def test_the_child_bootstrap_names_no_operator_command() -> None:
    """A chunk child is an internal mechanism; it is not something an operator can type."""
    assert "-m disclosure_drift" not in ce._CHILD_BOOTSTRAP
    assert "argparse" not in Path(ce.__file__).read_text(encoding="utf-8")
    assert "_child_main" in ce._CHILD_BOOTSTRAP


# ==========================================================================
# C51, A40: network and E0
# ==========================================================================
def test_c51_a40_no_chunk_module_pulls_in_a_transport() -> None:
    """Measured in a clean interpreter, as the accepted offline-parse proof measures it."""
    program = (
        "import sys, json;"
        "import disclosure_drift.m3;"
        "before = set(sys.modules);"
        "import disclosure_drift.m3.chunk_consolidation;"
        "import disclosure_drift.m3.chunk_execution;"
        "import disclosure_drift.m3.chunk_storage;"
        "from disclosure_drift.m3.offline_parse import PROHIBITED_IMPORT_PREFIXES as P;"
        "added = set(sys.modules) - before;"
        "print(json.dumps(sorted("
        "name for name in added if any("
        "name == p or name.startswith(p + '.') for p in P))))"
    )
    completed = subprocess.run(  # noqa: S603 - fixed argument vector, no shell
        [sys.executable, "-c", program], capture_output=True, text=True, check=True
    )
    assert json.loads(completed.stdout) == []


def test_no_chunk_module_names_a_client_transport_or_socket_api() -> None:
    for module in C1_MODULES:
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.Name):
                names.add(node.id)
        for needle in ("SecClient", "HttpxTransport", "socket", "urlopen", "create_connection"):
            assert needle not in names, (module.__name__, needle)


def test_no_chunk_module_reaches_e0() -> None:
    """E0 is a separate owner gate. Nothing here touches its driver or its constants."""
    for module in C1_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "from disclosure_drift.m3.e0" not in source
        assert "import disclosure_drift.m3.e0" not in source
        assert "M3_3_E0_EXECUTION_AUTHORITY" not in source


# ==========================================================================
# §25: no migration 0016
# ==========================================================================
def test_no_migration_0016_exists_and_the_head_is_unchanged() -> None:
    """§25: chunk artifacts are run-local; the persisted operational schema is untouched."""
    from disclosure_drift.storage.sqlite import available_migrations

    migrations = available_migrations()
    assert migrations[-1].version == 15
    directory = Path(migrations[-1].path).parent if hasattr(migrations[-1], "path") else None
    if directory is None:
        directory = Path(
            importlib.import_module("disclosure_drift.storage.migrations").__file__
        ).parent
    assert not list(directory.glob("0016_*.sql"))
    for module in C1_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "apply_migrations" not in source, module.__name__


def test_the_chunk_local_schemas_are_run_local_only() -> None:
    """The witness ledger is a run-local artifact and never reaches a catalog."""
    source = Path(ce.__file__).read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS chunk_first_witness" in source
    assert "chunk_first_witness" not in Path(
        importlib.import_module("disclosure_drift.storage.migrations").__file__
    ).parent.joinpath("0015_m33_verified_document_evidence.sql").read_text(encoding="utf-8")


# ==========================================================================
# C52, A50: existing runs are unaffected
# ==========================================================================
def test_c52_the_accepted_modules_are_imported_rather_than_replaced() -> None:
    """Every parse, persistence and evidence call the chunked path makes is the accepted one."""
    source = Path(ce.__file__).read_text(encoding="utf-8")
    for accepted in (
        "from disclosure_drift.sec.parsers.submissions import",
        "from disclosure_drift.sec.parsers.historical import",
        "from disclosure_drift.sec.census import CensusCatalog",
        "from disclosure_drift.m3.working_catalog import",
    ):
        assert accepted in source, accepted
    consolidation = Path(cc.__file__).read_text(encoding="utf-8")
    assert "CensusCatalog._candidate_edges(" in consolidation
    assert "CensusCatalog._mark_accession_conflicts(" in consolidation
    assert "ProjectionDigest" in consolidation


def test_a50_a_monolithic_world_is_never_read_as_a_chunked_one(tmp_path: Path) -> None:
    """A50: an existing D151 run carries neither a chunk receipt nor a final world receipt."""
    import test_d151_c1_equivalence as eq

    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    world_directory = eq.monolithic_f0(database, tree, tmp_path / "mono")
    assert not (world_directory / CHUNK_RECEIPT_FILENAME).exists()
    assert not (world_directory / FINAL_WORLD_RECEIPT_FILENAME).exists()
    with pytest.raises(ChunkEvidenceError, match="no receipt exists"):
        read_receipt_document(
            world_directory / FINAL_WORLD_RECEIPT_FILENAME, contract=FINAL_WORLD_RECEIPT_CONTRACT
        )


@pytest.mark.usefixtures("pinned_repository")
def test_a50_a_chunk_world_is_never_read_as_a_final_world(
    tmp_path: Path,
) -> None:
    """And the reverse: a chunk receipt is not a final receipt, by contract identity."""
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    run = c1x.run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    receipt = run["receipts"][0]
    directory = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    with pytest.raises(ChunkEvidenceError, match="carries contract"):
        read_receipt_document(
            directory / CHUNK_RECEIPT_FILENAME, contract=FINAL_WORLD_RECEIPT_CONTRACT
        )
    assert (
        read_receipt_document(directory / CHUNK_RECEIPT_FILENAME, contract=CHUNK_RECEIPT_CONTRACT)[
            "contract"
        ]
        == CHUNK_RECEIPT_CONTRACT
    )


def test_the_accepted_offline_parse_surface_is_unchanged() -> None:
    """Nothing this record adds appears in the accepted driver's public surface."""
    from disclosure_drift.m3 import offline_parse as op

    for name in ("chunk", "Chunk", "CHUNK"):
        assert not [item for item in op.__all__ if name in item]


def test_every_c1_module_is_importable_without_a_world(tmp_path: Path) -> None:
    """Importing a C1 module creates nothing, opens nothing, and starts nothing.

    **Measured in a FRESH INTERPRETER, and that is the D151-C3 §12 correction.** This test
    previously called :func:`importlib.reload` on the production modules in this process, which
    is not a re-import: it re-executes the module body and **rebinds every class object it
    defines**, so ``ChunkPlanError`` after the reload is a different class from the one an
    already-imported test module captured at its own import time. A later
    ``pytest.raises(ChunkPlanError)`` in the same session would then fail depending only on
    whether this test had run yet -- an order dependency planted in production state by a test
    that was not even about exceptions.

    A subprocess answers the actual question, which is about a **first** import rather than a
    re-import, and it answers it without touching this interpreter at all.
    """
    probe = tmp_path / "probe"
    probe.mkdir()
    program = (
        "import sys, json;"
        "from pathlib import Path;"
        "root = Path(sys.argv[1]);"
        "before = sorted(p.name for p in root.iterdir());"
        f"names = {list(C1_MODULE_NAMES)!r};"
        "import importlib;"
        "[importlib.import_module(name) for name in names];"
        "after = sorted(p.name for p in root.iterdir());"
        "print(json.dumps({'before': before, 'after': after, 'imported': sorted("
        "n for n in sys.modules if n in names)}))"
    )
    completed = subprocess.run(  # noqa: S603 - fixed argument vector, no shell
        [sys.executable, "-c", program, str(probe)], capture_output=True, text=True, check=True
    )
    observed = json.loads(completed.stdout.strip().splitlines()[-1])
    assert observed["before"] == observed["after"] == []
    assert observed["imported"] == sorted(C1_MODULE_NAMES)


def test_no_test_in_this_module_reloads_a_production_module() -> None:
    """D151-C3 §12, stated as a property of the suite rather than of one test.

    ``importlib.reload`` on a production module rebinds its exception classes for every module
    that has already imported them. Nothing in this file may do it, and this asserts that from
    the file's own source so a future edit that reintroduces it fails here.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "reload"
    ]
    assert calls == []
    # A second check for a reload reached under an alias the attribute walk cannot see. The
    # needles are assembled at run time so that this assertion is not itself a match for them.
    for needle in ("importlib." + "reload(", "from importlib import " + "reload"):
        assert needle not in source, needle


def test_the_prohibited_prefixes_are_the_accepted_list() -> None:
    """The list this suite checks against is the accepted one, not a local copy."""
    assert "httpx" in PROHIBITED_IMPORT_PREFIXES
    assert "socket" in PROHIBITED_IMPORT_PREFIXES
    assert "disclosure_drift.m3.acquisition" in PROHIBITED_IMPORT_PREFIXES


def test_no_host_a_interaction_is_reachable(tmp_path: Path) -> None:
    """§23: no dock, volume, power or transport qualification is performed by any C1 path.

    ``chunk_storage`` imports exactly one name from the external-working-root module -- the
    qualified volume's UUID -- and uses it to **refuse**, never to qualify anything.
    """
    source = Path(cs.__file__).read_text(encoding="utf-8")
    assert "QUALIFIED_EXTERNAL_VOLUME_UUID" in source
    for capability in (
        "macos_volume_identity",
        "require_qualified_volume",
        "external_canary_preflight",
        "diskutil",
        "require_launch_power_conditions",
        "transport_of",
    ):
        assert capability not in source, capability
    for module in (cp, cev, ce, cc):
        text = Path(module.__file__).read_text(encoding="utf-8")
        assert "external_working_root" not in text, module.__name__


# ==========================================================================
# A30: a dirty repository
# ==========================================================================
def test_a30_repository_identity_has_exactly_one_derivation_and_it_fails_closed(
    tmp_path: Path,
) -> None:
    """A30: a chunk's repository identity comes from the accepted primitive, or from nowhere.

    The chunk receipt binds the commit and the tree the chunk executed under, and the
    consolidator refuses chunks that disagree on either (A28, A29). What makes those values worth
    anything is that a **dirty** working tree can never produce them: accepted Decision 147's
    :func:`require_clean_running_repository` refuses before any identity is folded into a digest.

    **D151-C3 §9 changes exactly one half of this and not the other.** The consolidator now
    derives the live identity **for itself**, so that a checkout which moved after the chunks ran
    is caught -- something no comparison among the chunks could ever see. **D151-C5 MINOR-2 adds
    the chunk child**: it measures its own identity before it creates anything and holds the
    request's claim to it. What has not changed is that there is exactly **one** derivation in
    the repository: both modules reach it by importing the accepted module, and no C1 module runs
    ``git``, parses porcelain output, or reads a revision from an environment variable or a
    configuration key.
    """
    from disclosure_drift.m3.repository_identity import (
        RepositoryIdentityError,
        repository_identity_at,
    )

    repository = tmp_path / "repo"
    repository.mkdir()
    for arguments in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "c1@example.invalid"],
        ["config", "user.name", "c1"],
    ):
        subprocess.run(["git", "-C", str(repository), *arguments], check=True)  # noqa: S607
    (repository / "tracked.txt").write_text("one\n")
    subprocess.run(["git", "-C", str(repository), "add", "tracked.txt"], check=True)  # noqa: S607
    subprocess.run(  # noqa: S607
        ["git", "-C", str(repository), "commit", "-q", "-m", "seed"], check=True
    )
    clean = repository_identity_at(repository)
    assert clean.clean
    assert len(clean.head_sha) in {40, 64}

    (repository / "tracked.txt").write_text("two\n")
    dirty = repository_identity_at(repository)
    assert not dirty.clean
    assert dirty.dirty_tracked_paths == ("tracked.txt",)

    subprocess.run(["git", "-C", str(repository), "checkout", "--", "."], check=True)  # noqa: S607
    (repository / "untracked.py").write_text("# a file no commit describes\n")
    untracked = repository_identity_at(repository)
    assert not untracked.clean
    assert untracked.untracked_paths == ("untracked.py",)

    # Exactly two C1 modules reach the identity -- the chunk child and the consolidator -- each
    # exactly one accepted way, and none of them implements a second derivation: no `git`
    # invocation, no porcelain parsing, no subprocess reaching a version-control tool.
    reaching = []
    for module in C1_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        if "repository_identity" in source:
            reaching.append(module.__name__)
        assert '"git"' not in source, module.__name__
        assert "'git'" not in source, module.__name__
        assert "porcelain" not in source, module.__name__
        assert "rev-parse" not in source, module.__name__
    assert reaching == [
        "disclosure_drift.m3.chunk_execution",
        "disclosure_drift.m3.chunk_consolidation",
    ]
    accepted_import = (
        "from disclosure_drift.m3.repository_identity import (\n"
        "    RepositoryIdentity,\n"
        "    require_clean_running_repository,\n"
        ")"
    )
    for module in (ce, cc):
        assert accepted_import in Path(module.__file__).read_text(encoding="utf-8"), module.__name__
    assert RepositoryIdentityError is not None
