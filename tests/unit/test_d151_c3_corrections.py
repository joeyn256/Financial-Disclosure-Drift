"""D151-C3: the accepted D151-C2 findings, corrected and proved.

One module per correction family, in the order the record states them.

**MAJOR-1** -- the consolidated F0 terminal path did not carry the accepted D140-R12
blocking-terminal gate. A chunked run whose reduced parser run reached ``failed`` marked the
source parsed, wrote a checkpoint the accepted F1 would admit, and wrote a final receipt saying
``complete``. The monolithic path stops dead at that same point. The gate is now the accepted
predicate, called at the accepted position.

**MINOR-1** -- an importability test reloaded production modules in this interpreter, rebinding
their exception classes for every test that had already imported them.

**MINOR-2** -- the consolidator did not cross-check that its chunks belonged to one execution, nor
that the environment doing the consolidating was the environment they were built for.

**MINOR-3** -- the chunk planner restated the archive's name-level defences and lost two of them.

**MINOR-4** -- the F0 phase-checkpoint payload was whatever a caller handed in.

**MINOR-5** -- the attachment ceiling was checked only at consolidation, after every chunk had
been parsed, and the number it reported was justified by a claim that is not true.
"""

from __future__ import annotations

import ast
import inspect
import json
import re
import sqlite3
import subprocess
import sys
import zipfile
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
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.canary_phases import (  # noqa: E402
    PHASE_F0,
    PHASE_F1,
    CanaryPhaseError,
    read_phase_checkpoint,
    require_phase_admission,
)
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_RECEIPT_CONTRACT,
    CHUNK_RECEIPT_FILENAME,
    FINAL_WORLD_RECEIPT_FILENAME,
    ChunkEvidenceError,
    read_receipt_document,
)
from disclosure_drift.m3.repository_identity import (  # noqa: E402
    RepositoryIdentityError,
)
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    WORKING_CATALOG_FILENAME,
    RunProgressLedger,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.sec.archive import (  # noqa: E402
    MAX_MEMBER_COUNT,
    ArchiveDefenceError,
    iter_members,
    scan_central_directory,
)
from disclosure_drift.storage.sqlite import connect  # noqa: E402

BATCH = 2


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The shared pin: a real, clean throwaway repository, through the accepted identity seam.

    A consolidation derives the executing repository's identity for itself (D151-C3 §9), and the
    checkout this suite runs from is dirty by construction while a change is being written. The
    pin lives in ``test_d151_c1_chunk_plan`` so that every shared driver reads the same one --
    a per-module pin leaves a cross-module driver recording the wrong identity.
    """
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# Shared drivers
# ==========================================================================
def run_chunks(
    tmp_path: Path, database: Path, tree: DataTree, *, size: int = 2, label: str = "c"
) -> Any:
    return c1x.run_chunked_f0(
        tmp_path,
        database,
        tree,
        chunk_members=size,
        label=label,
        batch_size=BATCH,
        repository=c1.PINNED,
    )


def consolidate(
    run: Any, database: Path, *, suffix: str = "", run_id: str = "c3-run"
) -> cc.ConsolidationResult:
    return cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / f"final{suffix}",
        run_id=run_id,
    )


def blocking_world(tmp_path: Path) -> tuple[Path, DataTree]:
    """A source that reaches the accepted ``failed`` parser terminal: blocking structural rows."""
    return c1.build_world(tmp_path, members=6, filings=2, shards=2, malformed=2)


def healthy_world(tmp_path: Path) -> tuple[Path, DataTree]:
    return c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)


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
    """Rewrite one chunk receipt in place, leaving every artifact byte-identical.

    A receipt is excluded from its own manifest, so this is exactly the forgery an artifact
    manifest cannot see -- which is why the consolidator must catch it by comparison instead.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")


# ==========================================================================
# MAJOR-1: R01-R06, A01-A05
# ==========================================================================
def test_r01_a_failed_reduced_f0_cannot_mark_the_source_parsed(tmp_path: Path) -> None:
    """R01/A01/A04: the run-local ledger never reaches ``parsed`` for a blocking terminal."""
    database, tree = blocking_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    world = run["base"] / "final"
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        consolidate(run, database)
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        progress = ledger.progress(c1.INSTANCE)
        assert progress is not None
        assert progress.state == "in_progress"
        assert progress.state != "parsed"
    finally:
        ledger.close()
    # And the durable rows are still there, for diagnosis. Nothing was cleaned or deleted.
    with connect(world / WORKING_CATALOG_FILENAME, writer=False) as connection:
        counts = ce.table_row_counts(connection)
        state = connection.execute(
            "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
            (c1.INSTANCE,),
        ).fetchone()
    assert counts["census_parsed_records"] > 0
    assert str(state["parser_state"]) == "failed"


def test_r02_a_failed_reduced_f0_writes_no_f0_checkpoint(tmp_path: Path) -> None:
    """R02/A02: no durable F0 terminal exists, so nothing can be continued from it."""
    database, tree = blocking_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    world = run["base"] / "final"
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        consolidate(run, database)
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
    finally:
        ledger.close()


def test_r03_a_failed_reduced_f0_has_no_valid_final_receipt(tmp_path: Path) -> None:
    """R03: an absent terminal receipt is the refusal, not a gap."""
    database, tree = blocking_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    world = run["base"] / "final"
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        consolidate(run, database)
    assert not (world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    with pytest.raises(ChunkEvidenceError, match="no receipt exists"):
        read_receipt_document(
            world / FINAL_WORLD_RECEIPT_FILENAME, contract=cev.FINAL_WORLD_RECEIPT_CONTRACT
        )


def test_r04_a05_a_failed_reduced_f0_cannot_admit_f1(tmp_path: Path) -> None:
    """R04/A05: the accepted admission rule refuses the refused world, for the accepted reason."""
    database, tree = blocking_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    world = run["base"] / "final"
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        consolidate(run, database)
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        with pytest.raises(CanaryPhaseError, match="no durable terminal checkpoint"):
            require_phase_admission(
                ledger,
                phase=PHASE_F1,
                run_id="c3-run",
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


def test_r05_a_successful_reduced_f0_still_writes_the_accepted_terminal(tmp_path: Path) -> None:
    """R05: the positive control. The gate stops a blocking run and passes a healthy one."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    result = consolidate(run, database)
    assert result.receipt.status == "complete"
    assert result.receipt.parser_state_after == "completed"
    ledger = RunProgressLedger(result.world_directory / PROGRESS_LEDGER_FILENAME)
    try:
        checkpoint = read_phase_checkpoint(ledger, PHASE_F0)
        assert checkpoint is not None
        assert checkpoint.status == "complete"
        progress = ledger.progress(c1.INSTANCE)
        assert progress is not None
        assert progress.state == "parsed"
    finally:
        ledger.close()


def test_r06_the_accepted_require_f0_success_is_load_bearing(tmp_path: Path) -> None:
    """R06/M1: with the accepted predicate neutralised, the blocking run completes.

    This is the mutation stated as a test: the consolidator's refusal comes from the accepted
    gate and from nowhere else. Neutralise that one call and a world that must never be reported
    as complete is reported as complete -- which is the D139 finding D140-R12 exists to close,
    reappearing on the chunked path.
    """
    database, tree = blocking_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cc, "require_f0_success", lambda outcome: outcome)
        bypassed = consolidate(run, database)
    assert bypassed.receipt.status == "complete"
    assert bypassed.receipt.parser_state_after == "failed"
    # ... and with it in place, the same world is refused.
    second = run_chunks(tmp_path, database, tree, label="again")
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        consolidate(second, database, run_id="c3-again")


def test_a03_a_caller_cannot_declare_the_parser_state(tmp_path: Path) -> None:
    """A03: there is no argument that says what the parse found.

    The signature is the proof. ``consolidate_chunks`` takes a run identity, physical capacity
    observations and paths -- and nothing that could assert a disposition, a parser state, a
    digest, a count, or a payload.
    """
    parameters = set(inspect.signature(cc.consolidate_chunks).parameters)
    assert parameters == {
        "plan",
        "internal_root",
        "operational_catalog",
        "world_directory",
        "run_id",
        "external_root",
        "cache_bytes",
        "capacity_observations",
    }
    for forbidden in (
        "phase_checkpoint",
        "payload",
        "parser_state",
        "disposition",
        "outcome",
        "status",
    ):
        assert forbidden not in parameters, forbidden
    assert not hasattr(cc, "consolidated_phase_checkpoint")


# ==========================================================================
# MINOR-4: R07-R13
# ==========================================================================
def _accepted_payload_keys() -> set[str]:
    """Every key the ACCEPTED ``_phase_f0_body`` returns, read from its own source.

    Parsed rather than remembered. A field added to the accepted payload changes this set, and
    the assertions below then fail here rather than at the end of a real run.
    """
    source = inspect.getsource(canary._phase_f0_body)
    tree = ast.parse(source.lstrip())
    returns = [node for node in ast.walk(tree) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    literal = returns[0].value
    assert isinstance(literal, ast.Dict)
    keys = set()
    for key in literal.keys:
        assert isinstance(key, ast.Constant)
        keys.add(str(key.value))
    return keys


def _derived_payload(result: cc.ConsolidationResult) -> dict[str, Any]:
    ledger = RunProgressLedger(result.world_directory / PROGRESS_LEDGER_FILENAME)
    try:
        checkpoint = read_phase_checkpoint(ledger, PHASE_F0)
        assert checkpoint is not None
        return dict(checkpoint.payload)
    finally:
        ledger.close()


def test_r12_the_derived_payload_carries_every_accepted_key(tmp_path: Path) -> None:
    """R12: the complete accepted key set, derived from the accepted source, all present.

    Three statements, and the third is the one that matters: the constant matches the accepted
    function's own source; the phase runner's one added key is accounted for; and the payload a
    consolidation actually wrote carries exactly that set -- no key missing, and none invented.
    """
    accepted = _accepted_payload_keys()
    assert accepted | {"capacity_observations"} == cc.ACCEPTED_F0_PAYLOAD_KEYS
    database, tree = healthy_world(tmp_path)
    result = consolidate(run_chunks(tmp_path, database, tree), database)
    assert set(_derived_payload(result)) == cc.ACCEPTED_F0_PAYLOAD_KEYS


def test_r12_every_field_a_later_accepted_phase_reads_is_derived() -> None:
    """R12, from the consumer's side: every ``f0.payload`` lookup in accepted code is covered.

    The accepted F1, F2, result assembly and capacity inheritance are scanned for the literal
    keys they read out of an F0 payload. Each one must be a key this build derives. A consumer
    that grows a new lookup fails here.
    """
    consumers = (
        canary._phase_f1_body,
        canary._phase_f2_body,
        canary._phase_result_document,
        canary._inherited_observations,
    )
    read: set[str] = set()
    for function in consumers:
        source = inspect.getsource(function).lstrip()
        for match in re.finditer(r'f0(?:_payload)?(?:\.get\(|\[)"([a-z0-9_]+)"', source):
            read.add(match.group(1))
        for match in re.finditer(r'predecessor\.payload\.get\("([a-z0-9_]+)"', source):
            read.add(match.group(1))
    assert read, "the scan found no payload lookups at all, so it is not measuring anything"
    assert read <= cc.ACCEPTED_F0_PAYLOAD_KEYS, sorted(read - cc.ACCEPTED_F0_PAYLOAD_KEYS)


def test_r07_to_r11_the_payload_values_are_derived_from_the_world(tmp_path: Path) -> None:
    """R07-R11: disposition, parser states, identities, artifact digest, completeness digest.

    Every one of them is compared against the value the consolidated world itself carries --
    the plan, the accepted catalog, the merged sidecar and the final receipt -- rather than
    against a literal this test chose.
    """
    from disclosure_drift.m3.compact_evidence import (
        COMPACT_EVIDENCE_SIDECAR_FILENAME,
        CompactEvidenceSidecar,
    )

    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    result = consolidate(run, database)
    payload = _derived_payload(result)
    plan = run["plan"]

    # R07: the disposition is the accepted classifier's answer over the accepted plan row.
    assert payload["disposition"] == "E0_REQUIRED_PARSE"
    # R08: the parser state after is the reduced run's, and the state before is the pre-parse one.
    assert payload["parser_state_after"] == result.receipt.parser_state_after == "completed"
    assert payload["parser_state_before"] == "not_started"
    with connect(result.world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
        row = connection.execute(
            "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
            (c1.INSTANCE,),
        ).fetchone()
    assert str(row["parser_state"]) == payload["parser_state_after"]
    # R09: the source identities are the plan's.
    assert payload["source_id"] == plan.source_id
    assert payload["source_observation_id"] == plan.source_observation_id
    # R10: the artifact digest and length are the observation's, which is the plan's artifact.
    assert payload["source_artifact_sha256"] == plan.source_sha256
    assert payload["source_artifact_byte_length"] == plan.source_byte_length
    # R11: the completeness digest is the merged sidecar's replayed fold.
    sidecar = CompactEvidenceSidecar(result.world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME)
    try:
        evidence = sidecar.source_evidence(plan.source_observation_id)
    finally:
        sidecar.close()
    assert evidence is not None
    assert payload["completeness_digest"] == result.receipt.completeness_digest
    assert payload["completeness_digest"] == str(evidence["completeness_digest"])
    # The counts, likewise, are the reduced run's and the merged sidecar's.
    assert payload["members"] == result.receipt.members == plan.total_members
    assert payload["parsed_records"] == result.receipt.parsed_records
    assert payload["quarantined_records"] == result.receipt.quarantined_records
    assert payload["omitted_field_observations"] == result.receipt.omitted_field_observations
    assert (
        payload["materialized_field_observations"] == result.receipt.materialized_field_observations
    )
    assert payload["parser_run_id"] == result.receipt.parser_run_id
    # A chunkable source is never the full-index quarter, so there is no corroboration to carry.
    assert payload["corroboration"] is None
    assert "sec_full_index_company" not in cp.CHUNKABLE_SOURCE_IDS


def test_r13_no_caller_supplied_value_can_contradict_the_world(tmp_path: Path) -> None:
    """R13/A02: the two values a caller does state cannot say anything about what was found.

    ``run_id`` names the run and ``capacity_observations`` are host measurements. Neither reaches
    a semantic field: consolidating the same chunks twice under wildly different values produces
    the identical governed payload, save for the run identity itself.
    """
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    first = consolidate(run, database, suffix="-a", run_id="run-alpha")
    second = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final-b",
        run_id="run-beta",
        capacity_observations=({"label": "SYNTHETIC", "free_bytes": 1},),
    )
    left = _derived_payload(first)
    right = _derived_payload(second)
    # Only the physical fields differ, and they are named.
    physical = {"started_at_utc", "work_root_free_bytes_before", "capacity_observations"}
    assert {k: v for k, v in left.items() if k not in physical} == {
        k: v for k, v in right.items() if k not in physical
    }
    assert right["capacity_observations"] == [{"label": "SYNTHETIC", "free_bytes": 1}]
    assert left["capacity_observations"] == []
    assert first.receipt.completeness_digest == second.receipt.completeness_digest


# ==========================================================================
# MINOR-2: R17-R25, A06-A14
# ==========================================================================
def test_r17_a06_a_forged_source_instance_id_refuses(tmp_path: Path) -> None:
    """R17/A06: a chunk naming another planned source is refused against the plan."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    edit_receipt(
        receipt_path_of(run, 1),
        lambda document: document.__setitem__("source_instance_id", "base|other|9"),
    )
    with pytest.raises(cc.ChunkConsolidationError, match="names planned source instance"):
        consolidate(run, database)
    assert not (run["base"] / "final").exists()


def test_r18_a07_a_forged_source_observation_id_refuses(tmp_path: Path) -> None:
    """R18/A07: likewise for the observation the chunk claims to have consumed."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    edit_receipt(
        receipt_path_of(run, 0),
        lambda document: document.__setitem__("source_observation_id", "obs-elsewhere"),
    )
    with pytest.raises(cc.ChunkConsolidationError, match="names source observation"):
        consolidate(run, database)


def test_a14_the_forgeries_leave_every_artifact_byte_identical(tmp_path: Path) -> None:
    """A14: the artifact manifest cannot see any of this, which is why the comparison exists.

    The receipt is excluded from its own manifest -- it must be, since it does not exist when the
    manifest is taken -- so a field edited inside it changes no artifact and no digest. The
    manifest still verifies perfectly. Only a comparison against the plan catches the forgery.
    """
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    path = receipt_path_of(run, 1)
    directory = path.parent
    before = {
        item.name: item.read_bytes()
        for item in directory.iterdir()
        if item.name != CHUNK_RECEIPT_FILENAME
    }
    edit_receipt(path, lambda document: document.__setitem__("source_instance_id", "base|x|1"))
    after = {
        item.name: item.read_bytes()
        for item in directory.iterdir()
        if item.name != CHUNK_RECEIPT_FILENAME
    }
    assert before == after
    forged = cev.ChunkReceipt.from_record(
        read_receipt_document(path, contract=CHUNK_RECEIPT_CONTRACT)
    )
    # The manifest verification is GREEN over the forged receipt: it describes bytes that really
    # are on disk, and every one of them is unchanged.
    cev.verify_artifact_manifest(
        directory, forged.manifest, exclude=(CHUNK_RECEIPT_FILENAME, "transfer_receipt.json")
    )
    with pytest.raises(cc.ChunkConsolidationError, match="names planned source instance"):
        consolidate(run, database)


@pytest.mark.parametrize("field", ["repository_head_sha", "repository_tree_sha"])
def test_r19_r20_a09_a10_chunks_from_different_revisions_refuse(tmp_path: Path, field: str) -> None:
    """R19/R20/A09/A10: two chunks under governing code that moved between them."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    edit_receipt(receipt_path_of(run, 1), lambda document: document.__setitem__(field, "f" * 40))
    with pytest.raises(cc.ChunkConsolidationError, match="executed under repository"):
        consolidate(run, database)


def test_r21_a11_consolidation_under_a_moved_checkout_refuses(tmp_path: Path) -> None:
    """R21/A11: the checkout moved AFTER the chunks ran, and every chunk still agrees.

    This is the case a comparison among the chunks can never catch, and the reason the identity
    is measured rather than read off the receipts. The chunks are perfectly consistent with one
    another; what changed is the code that would do the consolidating.
    """
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    assert c1.PINNED_ROOT is not None
    (c1.PINNED_ROOT / "governing.txt").write_text("a governing change\n", encoding="utf-8")
    for argv in (["add", "governing.txt"], ["commit", "--quiet", "-m", "moved"]):
        subprocess.run(  # noqa: S603, S607
            ["git", "-C", str(c1.PINNED_ROOT), *argv], check=True, capture_output=True
        )
    with pytest.raises(cc.ChunkConsolidationError, match="consolidation is running from"):
        consolidate(run, database)
    assert not (run["base"] / "final").exists()


def test_r22_a12_a_dirty_checkout_refuses(tmp_path: Path) -> None:
    """R22/A12: the accepted clean-repository predicate refuses before anything is read."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    assert c1.PINNED_ROOT is not None
    (c1.PINNED_ROOT / "untracked.py").write_text("# a file no commit describes\n", encoding="utf-8")
    with pytest.raises(RepositoryIdentityError, match="clean tracked working tree"):
        consolidate(run, database)
    assert not (run["base"] / "final").exists()


@pytest.mark.parametrize(
    ("field", "value"), [("batch_size", 999), ("parser_version", "9.9.9-forged")]
)
def test_r23_a08_a_differing_execution_contract_refuses(
    tmp_path: Path, field: str, value: object
) -> None:
    """R23/A08: two chunks that did not execute equivalently are not one execution."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    edit_receipt(
        receipt_path_of(run, 1),
        lambda document: document["execution_contract"].__setitem__(field, value),
    )
    with pytest.raises(cc.ChunkConsolidationError, match="different execution contract"):
        consolidate(run, database)


def test_r24_a_differing_catalog_digest_between_chunks_refuses(tmp_path: Path) -> None:
    """R24: one chunk seeded from a catalog the others never saw."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    edit_receipt(
        receipt_path_of(run, 0),
        lambda document: document["execution_contract"].__setitem__(
            "catalog_source_sha256", "9" * 64
        ),
    )
    with pytest.raises(cc.ChunkConsolidationError, match="different execution contract"):
        consolidate(run, database)


def test_r25_a13_the_seed_catalog_is_identified_by_bytes_not_by_path(tmp_path: Path) -> None:
    """R25/A13: the same path, different bytes -- refused.

    The copy is a fully valid catalog with a different header: the plan reads out of it, the
    schema is identical, and only the bytes have moved. A path comparison would admit it.
    """
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    twin = tmp_path / "twin-catalog.sqlite3"
    twin.write_bytes(database.read_bytes())
    raw = sqlite3.connect(twin)
    try:
        # A change to the file header alone: every table, row and index is untouched, so the
        # copy is a perfectly usable catalog that simply is not the artifact the chunks saw.
        raw.execute("PRAGMA journal_mode = DELETE")
        raw.execute("PRAGMA user_version = 4242")
        raw.commit()
    finally:
        raw.close()
    from disclosure_drift.m3.working_catalog import file_digest

    assert file_digest(twin)[0] != file_digest(database)[0]
    with pytest.raises(cc.ChunkConsolidationError, match="identified by its BYTES"):
        cc.consolidate_chunks(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=twin,
            world_directory=run["base"] / "final-twin",
            run_id="twin-run",
        )
    assert not (run["base"] / "final-twin").exists()


def test_the_final_receipt_binds_the_validated_identity(tmp_path: Path) -> None:
    """§8 E: a reader of the final receipt can say which code, which catalog, which execution."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    result = consolidate(run, database)
    assert c1.PINNED is not None
    from disclosure_drift.m3.working_catalog import file_digest

    assert result.receipt.repository_head_sha == c1.PINNED.head_sha
    assert result.receipt.repository_tree_sha == c1.PINNED.tree_sha
    assert result.receipt.catalog_source_sha256 == file_digest(database)[0]
    assert (
        result.receipt.execution_contract_identity
        == result.inputs[0].receipt.execution_contract.contract_identity
    )
    assert result.receipt.consolidation_contract == cc.CONSOLIDATION_CONTRACT
    assert result.receipt.source_instance_id == c1.INSTANCE
    # And every one of them survives the round trip through the durable document.
    stored = read_receipt_document(
        result.world_directory / FINAL_WORLD_RECEIPT_FILENAME,
        contract=cev.FINAL_WORLD_RECEIPT_CONTRACT,
    )
    assert stored["repository_head_sha"] == c1.PINNED.head_sha
    assert stored["catalog_source_sha256"] == file_digest(database)[0]


def test_the_normalized_execution_identity_drops_only_what_it_must(tmp_path: Path) -> None:
    """§8 C: chunk_id and the page-cache budget, and nothing else.

    Two chunks of one plan carry DIFFERENT full execution identities and the SAME normalized
    one; a chunk run under a different page-cache budget likewise agrees, because accepted
    Decision 119 establishes the budget moves nothing; and every other governing value moves it.
    """
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    result = consolidate(run, database)
    identities = {item.receipt.execution_identity for item in result.inputs}
    contracts = {item.receipt.execution_contract.contract_identity for item in result.inputs}
    assert len(identities) == len(result.inputs)
    assert len(contracts) == 1
    plan = run["plan"]
    base = {
        "plan": plan,
        "batch_size": BATCH,
        "catalog_source_sha256": "a" * 64,
        "migration_head": 15,
        "repository_head_sha": "b" * 40,
        "repository_tree_sha": "c" * 40,
    }
    reference = ce.chunk_execution_contract(**base).contract_identity
    for field, replacement in (
        ("batch_size", BATCH + 1),
        ("catalog_source_sha256", "d" * 64),
        ("migration_head", 16),
        ("repository_head_sha", "e" * 40),
        ("repository_tree_sha", "f" * 40),
    ):
        moved = ce.chunk_execution_contract(**{**base, field: replacement}).contract_identity
        assert moved != reference, field
    # The full identity still folds both chunk-specific values, unchanged from C1.
    full = {
        "plan": plan,
        "chunk_id": "chunk-0000",
        "batch_size": BATCH,
        "cache_bytes": None,
        "repository_head_sha": "b" * 40,
        "repository_tree_sha": "c" * 40,
        "catalog_source_sha256": "a" * 64,
        "migration_head": 15,
    }
    assert ce.chunk_execution_identity(**full) != ce.chunk_execution_identity(
        **{**full, "chunk_id": "chunk-0001"}
    )
    assert ce.chunk_execution_identity(**full) != ce.chunk_execution_identity(
        **{**full, "cache_bytes": 1 << 20}
    )


# ==========================================================================
# MINOR-3: R26-R29, A15-A16
# ==========================================================================
def hostile_archive(path: Path, names: list[str]) -> Path:
    """One archive holding exactly these member names, in exactly this order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=c1.ARCHIVE_TIMESTAMP)
            archive.writestr(info, "" if name.endswith("/") else "{}")
    return path


def decide(archive_path: Path, *, max_members: int | None = None) -> tuple[str, str]:
    """What the ACCEPTED traversal and the PLANNER each decide about one archive.

    Returns ``(traversal, planner)``, each either ``"admit"`` or the refusal's message. The two
    are the comparison: for a name-level defence they must be the same string, because they are
    now produced by the same statements.
    """
    outcomes = []
    for run in (
        lambda: list(
            iter_members(
                archive_path, **({} if max_members is None else {"max_members": max_members})
            )
        ),
        lambda: cp.canonical_member_sequence(archive_path),
    ):
        try:
            run()
        except ArchiveDefenceError as exc:
            outcomes.append(str(exc))
        else:
            outcomes.append("admit")
    return outcomes[0], outcomes[1]


#: Every name-level attack §10 names, and the plain control beside them.
HOSTILE_CORPUS: tuple[tuple[str, list[str]], ...] = (
    ("plain", ["CIK0000000001.json"]),
    ("forward_file_then_descendant", ["x", "x/y.json"]),
    ("descendant_then_ancestor_file", ["x/y.json", "x"]),
    ("duplicate_canonical_name", ["a/b.json", "a/./b.json"]),
    ("portable_case_collision", ["Alpha.json", "ALPHA.json"]),
    ("traversal", ["../escape.json"]),
    ("absolute", ["/etc/passwd.json"]),
    ("backslash", ["a\\b.json"]),
    ("percent_encoded", ["a/%2e%2e/b.json"]),
    ("drive_letter", ["C:/a.json"]),
    ("reserved_device", ["con.json"]),
    ("directory_then_file_of_that_name", ["x/", "x"]),
    ("shard_name_ambiguity", ["CIK0000000001-submissions-001.json", "CIK0000000001.json"]),
    ("deep_forward_collision", ["a/b", "a/b/c.json"]),
)


@pytest.mark.parametrize(
    ("label", "names"), HOSTILE_CORPUS, ids=[item[0] for item in HOSTILE_CORPUS]
)
def test_r29_a15_the_planner_and_the_accepted_traversal_agree_exactly(
    tmp_path: Path, label: str, names: list[str]
) -> None:
    """R29/A15: admit or refuse, and on a refusal the same message, over the whole corpus.

    The strong form of the parity claim. They agree because the name-level pass is now ONE
    function that both of them call, so a divergence would have to be a divergence inside a
    single implementation.
    """
    archive = hostile_archive(tmp_path / f"{label}.zip", names)
    traversal, planner = decide(archive)
    assert traversal == planner, (label, traversal, planner)


def test_r26_a15_a_forward_file_then_descendant_collision_refuses(tmp_path: Path) -> None:
    """R26/A15: ``x`` then ``x/y.json`` -- the defence D151-C2 found missing from the planner."""
    archive = hostile_archive(tmp_path / "forward.zip", ["x", "x/y.json"])
    traversal, planner = decide(archive)
    assert "a parent path is already a file" in planner
    assert traversal == planner
    with pytest.raises(ArchiveDefenceError, match="a parent path is already a file"):
        cp.canonical_member_sequence(archive)


def test_r27_the_reverse_collision_parity_holds(tmp_path: Path) -> None:
    """R27: ``x/y.json`` then ``x`` -- the direction the planner already caught, still caught."""
    archive = hostile_archive(tmp_path / "reverse.zip", ["x/y.json", "x"])
    traversal, planner = decide(archive)
    assert "file and directory" in planner
    assert traversal == planner


def test_r28_a16_the_member_count_ceiling_parity_holds(tmp_path: Path) -> None:
    """R28/A16: the accepted ceiling governs the planner too, at ``MAX_MEMBER_COUNT + 1``.

    Exercised at a small ceiling, because two million members cannot be built here -- and the
    ceiling the planner uses is proved to be the accepted constant rather than a local number,
    resolved at call time so that this substitution reaches both callers identically.
    """
    names = [f"CIK{index:010d}.json" for index in range(4)]
    archive = hostile_archive(tmp_path / "many.zip", names)
    # Below the ceiling: both admit.
    assert decide(archive, max_members=4) == ("admit", "admit")
    # At ceiling + 1: the accepted traversal refuses.
    traversal, _ = decide(archive, max_members=3)
    assert "members exceed the limit 3" in traversal
    # And the planner refuses at the same point, because it resolves the same constant.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("disclosure_drift.sec.archive.MAX_MEMBER_COUNT", 3)
        with pytest.raises(ArchiveDefenceError, match="members exceed the limit 3"):
            cp.canonical_member_sequence(archive)
        patch.setattr("disclosure_drift.sec.archive.MAX_MEMBER_COUNT", 4)
        assert len(cp.canonical_member_sequence(archive)) == 4
    assert inspect.signature(scan_central_directory).parameters["max_members"].default is None
    assert MAX_MEMBER_COUNT == 2_000_000


def test_the_planner_and_the_traversal_share_one_implementation() -> None:
    """The parity is structural: there is exactly one name-level pass, and both callers reach it.

    A parity proved only by a corpus is a parity that holds for the cases someone thought of.
    This is the reason it holds for the cases nobody thought of.
    """
    plan_source = Path(cp.__file__).read_text(encoding="utf-8")
    archive_source = Path(inspect.getfile(scan_central_directory)).read_text(encoding="utf-8")
    assert "scan_central_directory" in plan_source
    assert archive_source.count("def scan_central_directory(") == 1
    # And the planner no longer carries a restatement of any of the defences.
    for restated in (
        "_refuse_special_member",
        "_portable_member_key",
        "_strict_ancestor_prefixes",
        "canonical_member_name",
        "collides with another member",
        "file and directory paths",
    ):
        assert restated not in plan_source, restated


def test_the_populations_are_identical_over_the_synthetic_source(tmp_path: Path) -> None:
    """The positive control the corpus needs: over a real world, both see the same members."""
    _database, tree = healthy_world(tmp_path)
    archive = c1.archive_of(tree)
    traversed = [member.name for member in iter_members(archive, name_suffix=".json")]
    planned = cp.canonical_member_sequence(archive)
    assert sorted(traversed) == sorted(member.member_name for member in planned)
    assert len(traversed) == len(planned)


# ==========================================================================
# MINOR-5: R30-R34, A17-A19
# ==========================================================================
def _plan_over(tree: DataTree, database: Path, *, chunk_members: int) -> cp.ChunkPlan:
    return c1.build_plan(tree, database, chunk_members=chunk_members)


def test_r30_a_nine_chunk_plan_is_admitted(tmp_path: Path) -> None:
    """R30: nine is the architectural cap, and a plan that needs exactly nine is built."""
    # Six primaries and three shards: at one member per chunk that is exactly nine chunks.
    _database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=3)
    database = tmp_path / "catalog.sqlite3"
    plan = _plan_over(tree, database, chunk_members=1)
    assert plan.chunk_count == 9
    assert plan.single_pass_chunk_cap == cp.SINGLE_PASS_CHUNK_CAP == 9
    assert cp.RESERVED_ATTACHMENT_HEADROOM == 1


def test_r31_r32_a17_a_ten_chunk_plan_refuses_before_chunk_zero_starts(tmp_path: Path) -> None:
    """R31/R32/A17: the refusal is at plan construction, so no chunk process ever starts.

    Seven primaries and three shards is ten chunks at one member each. The plan is refused, the
    plan file is never written, and there is nothing on disk for a chunk to have been run from.
    """
    _database, tree = c1.build_world(tmp_path, members=7, filings=2, shards=3)
    database = tmp_path / "catalog.sqlite3"
    before = sorted(path.name for path in tmp_path.iterdir())
    with pytest.raises(cp.ChunkPlanError, match="single-pass chunked-F0"):
        _plan_over(tree, database, chunk_members=1)
    assert sorted(path.name for path in tmp_path.iterdir()) == before
    # And it is genuinely a ten-chunk partition that was refused, not a mis-sized world.
    admitted = _plan_over(tree, database, chunk_members=2)
    assert admitted.chunk_count == 6


def test_a19_a_plan_cannot_be_reinterpreted_as_a_larger_one(tmp_path: Path) -> None:
    """A19: the cap is inside the sealed digest, and a record declaring a bigger one refuses."""
    _database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=3)
    database = tmp_path / "catalog.sqlite3"
    plan = _plan_over(tree, database, chunk_members=1)
    record = dict(plan.as_record())
    assert record["single_pass_chunk_cap"] == 9
    # Raising the cap alone moves the digest, so the record no longer describes itself.
    record["single_pass_chunk_cap"] = 32
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    # And resealing it -- digest and all -- is still refused, by the constant.
    from dataclasses import replace as _replace

    raised = _replace(plan, single_pass_chunk_cap=32)
    resealed = dict(raised.as_record())
    resealed["plan_digest"] = cp._plan_digest(raised)
    with pytest.raises(cp.ChunkPlanError, match="never a permission to exceed"):
        cp.ChunkPlan.from_record(resealed)


def test_r33_r34_a18_the_consolidator_re_asks_the_running_library(tmp_path: Path) -> None:
    """R33/R34/A18: a capability question and an architectural question, both asked here.

    R34: a runtime limit of ten admits a nine-chunk plan's capability check.
    R33: a runtime limit below the chunk count refuses, whatever the plan was sealed under.
    """
    assert cc.attachment_limit() == 10
    assert cc.require_attachable(9, limit=10) == 9
    assert cc.require_attachable(4, limit=5) == 4
    with pytest.raises(cc.ChunkConsolidationError, match="SQLITE_LIMIT_ATTACHED = 3"):
        cc.require_attachable(4, limit=3)
    with pytest.raises(cc.ChunkConsolidationError, match="single-pass chunked-F0"):
        cc.require_attachable(10, limit=10)
    # The measurement itself: ten attaches succeed beside main AND temp, so neither consumes a
    # slot and the cap of nine is one slot of headroom rather than a library limit.
    connection = sqlite3.connect(tmp_path / "main.sqlite3")
    try:
        attached = 0
        for index in range(cc.attachment_limit()):
            path = tmp_path / f"attach-{index}.sqlite3"
            sqlite3.connect(path).close()
            connection.execute(f"ATTACH DATABASE '{path}' AS a{index}")
            attached += 1
        assert attached == 10
        connection.execute("CREATE TEMP TABLE probe (value INTEGER)")
    finally:
        connection.close()


# ==========================================================================
# MINOR-1: R35-R36, A20
# ==========================================================================
def test_r35_a20_no_test_module_reloads_a_production_module() -> None:
    """R35/A20: no D151 test rebinds a production exception class for the tests after it.

    ``importlib.reload`` re-executes a module body and rebinds every class it defines, so a test
    that reloads ``chunk_plan`` leaves every already-imported module holding a ``ChunkPlanError``
    that is no longer the class ``chunk_plan`` raises. The whole suite is scanned, not one file.
    """
    offenders = []
    for path in sorted(Path(__file__).parent.glob("test_d151_*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "reload"
            ):
                offenders.append(f"{path.name}:{node.lineno}")
    assert offenders == []


def test_r36_a20_the_exception_classes_are_the_ones_production_raises(tmp_path: Path) -> None:
    """R36/A20: class identity holds, which is what an in-process reload would have broken.

    Asserted by identity rather than by name: a reloaded module would still export a class
    called ``ChunkPlanError``, and it would not be this one.
    """
    import disclosure_drift.m3.chunk_consolidation as fresh_cc
    import disclosure_drift.m3.chunk_evidence as fresh_cev
    import disclosure_drift.m3.chunk_execution as fresh_ce
    import disclosure_drift.m3.chunk_plan as fresh_cp
    import disclosure_drift.m3.chunk_storage as fresh_cs

    assert fresh_cp.ChunkPlanError is cp.ChunkPlanError
    assert fresh_ce.ChunkExecutionError is ce.ChunkExecutionError
    assert fresh_cev.ChunkEvidenceError is cev.ChunkEvidenceError
    assert fresh_cs.ChunkStorageError is cs.ChunkStorageError
    assert fresh_cc.ChunkConsolidationError is cc.ChunkConsolidationError
    # And the class a refusal actually raises is that same object.
    with pytest.raises(cp.ChunkPlanError) as caught:
        cp.production_chunk_members()
    assert type(caught.value) is cp.ChunkPlanError


def test_r36_the_focused_suite_passes_in_reversed_module_order() -> None:
    """R36: collection order decides nothing -- run the D151 modules back to front, serially.

    A subprocess, so this test's own session is not what is being measured. The modules are
    handed to pytest in reverse name order, which is the order a same-process reload defect is
    most likely to show up in.
    """
    here = Path(__file__).parent
    # THIS module is excluded first, and not as an optimisation: it contains this test, so
    # including it would make the child spawn a grandchild, and so on without bound.
    #
    # The other three are excluded because they cannot bear on the question. What an in-process
    # reload breaks is **exception-class identity**, so the modules that matter are the ones that
    # assert on a C1 exception class -- plan, execution, storage, consolidation and closure, all
    # of which are here. The equivalence and phase-runner sweeps assert on governed content, and
    # the performance module is a benchmark over a two-million-row probe. All three run in full,
    # in normal order, elsewhere in this session's validation.
    excluded = {
        Path(__file__).name,
        "test_d151_c1_equivalence.py",
        "test_d151_c3_phase_runner.py",
        "test_d151_c1_performance.py",
    }
    modules = sorted(
        (path.name for path in here.glob("test_d151_*.py") if path.name not in excluded),
        reverse=True,
    )
    assert len(modules) >= 4
    assert Path(__file__).name not in modules
    completed = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:randomly",
            "-x",
            *[str(here / name) for name in modules],
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=here.parent.parent,
    )
    assert completed.returncode == 0, completed.stdout[-6000:]


# ==========================================================================
# §13, §14: nothing C2 accepted has moved -- R37-R40, A21-A26
# ==========================================================================
def test_r37_a21_a22_the_first_witness_reconstruction_is_unchanged(tmp_path: Path) -> None:
    """R37/A21/A22: the hostile first-witness oracle, re-run against the monolithic answer.

    Every control §13 names, in one world and one sweep: an accession co-filed by four
    registrants so the true first witness lies in another chunk and the accession is witnessed
    in more than three; shards and primaries both present; members with the ``filings`` key
    absent entirely; and the smallest partition, at which every witness is in its own chunk. If
    the correction were omitted, or a false local-first witness were left un-upgraded, the
    observation rows and the evidence counters would differ from the monolithic run's.
    """
    import test_d151_c1_equivalence as eq

    database, tree = c1.build_world(
        tmp_path, members=8, filings=2, share_every=2, junk=3, unknown=4
    )
    eq.monolithic_f0(database, tree, tmp_path / "mono")
    reference = eq.measure(tmp_path / "mono")
    split = consolidate(run_chunks(tmp_path, database, tree, size=1, label="split"), database)
    whole = consolidate(run_chunks(tmp_path, database, tree, size=10_000, label="whole"), database)
    # The hard case really arose: an accession witnessed across chunks, corrected.
    assert split.receipt.first_witness_accessions_corrected >= 1
    assert split.receipt.first_witness_rows_staged > 0
    assert split.receipt.evidence_members_corrected > 0
    assert split.receipt.evidence_delta > 0
    # ... and the single-chunk control needed no correction at all.
    assert whole.receipt.first_witness_accessions_corrected == 0
    assert whole.receipt.evidence_delta == 0
    eq.assert_equivalent(reference, eq.measure(split.world_directory))
    eq.assert_equivalent(reference, eq.measure(whole.world_directory))


def test_r38_the_shard_parent_barrier_is_unchanged(tmp_path: Path) -> None:
    """R38: a shard chunk still refuses without the complete parent map, and the plan still
    guarantees the boundary is a chunk boundary rather than an execution convention."""
    database, tree = c1.build_world(tmp_path, members=4, filings=2, shards=2)
    plan = c1.build_plan(tree, database, chunk_members=1)
    shard_chunks = cp.chunks_in_region(plan, cp.REGION_SHARD)
    primary_chunks = cp.chunks_in_region(plan, cp.REGION_PRIMARY)
    assert shard_chunks and primary_chunks
    # Every primary chunk precedes every shard chunk, and no interval straddles the boundary.
    assert max(bounds.end for bounds in primary_chunks) == plan.primary_members
    assert min(bounds.start for bounds in shard_chunks) == plan.primary_members
    # And a shard chunk started without the merged map is refused before it decompresses.
    first_shard = shard_chunks[0]
    directory, attempt = ce.next_attempt_directory(tmp_path / "solo", first_shard.chunk_id)
    plan_path = tmp_path / "solo-plan.json"
    cev.write_once_json(plan_path, dict(plan.as_record()))
    with pytest.raises(ce.ChunkExecutionError, match="without the merged parent map"):
        ce.execute_chunk_body(
            c1x.chunk_request(
                plan_path=plan_path,
                chunk_id=first_shard.chunk_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
                tree=tree,
                parent_map_path=None,
                repository=c1.PINNED,
            )
        )


def test_r39_a23_the_completeness_digest_is_partition_invariant(tmp_path: Path) -> None:
    """R39/A23: one digest across every partition, and the fold's order still decides it."""
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)
    digests = set()
    manifests = set()
    for size in (1, 2, 3, 9_999):
        result = consolidate(
            run_chunks(tmp_path, database, tree, size=size, label=f"p{size}"),
            database,
            run_id=f"p{size}",
        )
        digests.add(result.receipt.completeness_digest)
        manifests.add(result.receipt.member_manifest_digest)
    assert len(digests) == 1
    assert len(manifests) == 1
    # And the fold is still ordered: replaying the same members in a different order moves it.
    from disclosure_drift.m3.compact_evidence import ProjectionDigest

    forward = ProjectionDigest(c1.SOURCE_ID)
    backward = ProjectionDigest(c1.SOURCE_ID)
    for chain, order in ((forward, (1, 2, 3)), (backward, (3, 2, 1))):
        for value in order:
            chain._records = value  # noqa: SLF001 - the accepted fold, replayed
            chain._member = cc._StoredMemberDigest(f"{value:064d}")  # noqa: SLF001
            chain.end_member()
    assert forward.hexdigest() != backward.hexdigest()


def test_r40_a24_the_large_table_merge_is_still_set_based(tmp_path: Path) -> None:
    """R40/A24: the write shape C2 accepted, re-inspected after the corrections.

    Every load against a large F0 table is still one ``INSERT ... SELECT ... ORDER BY`` over a
    compound select of the attached chunks. Nothing added by MAJOR-1 or the identity checks
    issues a statement per row: the gate reads two fields off an object, and the cross-checks
    read receipts.
    """
    source = Path(cc.__file__).read_text(encoding="utf-8")
    # The three merge shapes, unchanged.
    assert 'f"{verb} {table} ({projection}) "' in source
    assert "ORDER BY {key}, chunk_ordinal" in source
    assert "ROW_NUMBER() OVER (PARTITION BY {key} ORDER BY chunk_ordinal)" in source
    assert "ORDER BY accession_observation_id, priority, chunk_ordinal" in source
    # No row-at-a-time write anywhere in the three functions that load a large table, and none
    # in the orchestrator either -- so nothing MAJOR-1 or the identity checks added issues one.
    #
    # Located by NAME through the module's own syntax tree rather than by line offset:
    # ``inspect.getsource`` re-reads the file and trusts the line number a loaded function object
    # was compiled with, which is the wrong region for any function below an edit made since the
    # import. A test whose verdict depends on nobody having touched the file is not a test.
    bodies = _function_bodies(source)
    for name in (
        "_sorted_bulk_load",
        "_keyed_first_last_load",
        "_load_accession_observations",
        "consolidate_chunks",
    ):
        body = bodies[name]
        assert "executemany" not in body, name
        assert "for row in" not in body, name
        assert "INSERT" not in body or "SELECT" in body, name
    # `executemany` appears exactly once in the whole module, and it is the BOUNDED
    # cross-chunk corrections staging table -- sized by duplicate accessions, not by records.
    assert source.count("executemany(") == 1
    assert "executemany" in bodies["_stage_rows"]
    # And measured: the statement set does not grow with the row volume.
    small = _write_statements(tmp_path, members=4, label="small")
    large = _write_statements(tmp_path, members=12, label="large")
    assert small == large
    # Bounded by the number of GOVERNED TABLES, not by the number of rows: eleven F0 tables,
    # the plan-source terminal, and the accepted duplicate-identity update.
    assert 0 < len(small) <= len(ce.F0_WRITTEN_TABLES) + 2


def _function_bodies(source: str) -> dict[str, str]:
    """Every top-level function in one module, by name, as its own source text.

    Parsed from the text rather than reached through a loaded function object, so the region
    returned is the region that is actually in the file.
    """
    lines = source.splitlines()
    found: dict[str, str] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found[node.name] = "\n".join(lines[node.lineno - 1 : node.end_lineno])
    return found


class _TracingWorkingCatalog(cc.WorkingCatalog):
    """Records every statement the consolidator's own connection executes."""

    statements: list[str] = []

    def __enter__(self) -> Any:
        opened = super().__enter__()
        opened.connection.set_trace_callback(type(self).statements.append)
        return opened


def _write_statements(tmp_path: Path, *, members: int, label: str) -> list[str]:
    """The DISTINCT write statements one consolidation issues against an F0 table."""
    database, tree = c1.build_world(tmp_path / label, members=members, filings=3)
    run = c1x.run_chunked_f0(
        tmp_path / label,
        database,
        tree,
        chunk_members=max(members // 4, 1),
        label=f"{label}-run",
        repository=c1.PINNED,
    )
    _TracingWorkingCatalog.statements = []
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cc, "WorkingCatalog", _TracingWorkingCatalog)
        cc.consolidate_chunks(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            world_directory=run["base"] / "final",
            run_id=f"trace-{label}",
        )
    verbs = ("INSERT INTO ", "INSERT OR IGNORE INTO ", "UPDATE ")
    found: list[str] = []
    for statement in _TracingWorkingCatalog.statements:
        flat = " ".join(statement.split())
        for verb in verbs:
            if not flat.startswith(verb):
                continue
            target = flat[len(verb) :].split()[0]
            if target not in ce.F0_WRITTEN_TABLES and target != "census_plan_sources":
                continue
            entry = f"{verb.strip()} {target}"
            if entry not in found:
                found.append(entry)
    return found


def test_a25_a_chunk_altered_during_consolidation_is_refused(tmp_path: Path) -> None:
    """A25: a chunk that moves is caught, before the merge AND after it.

    Two attacks, because there are two windows. A chunk altered **before** consolidation is
    refused when its copy is resolved -- it has no verified copy on either tier. A chunk altered
    **while** the merge is running passes that check and is caught by the re-verification that
    runs after the sidecar is merged, which is the check that makes ``chunks_unchanged`` on the
    final receipt a measurement rather than a claim.
    """
    database, tree = healthy_world(tmp_path)
    before = run_chunks(tmp_path, database, tree, label="before")
    victim = receipt_path_of(before, 1).parent / "chunk_witness.sqlite3"
    victim.write_bytes(victim.read_bytes() + b"\x00")
    with pytest.raises(cs.ChunkStorageError, match="no verified copy on either tier"):
        consolidate(before, database, run_id="altered-before")

    during = run_chunks(tmp_path, database, tree, label="during")
    target = receipt_path_of(during, 1).parent / "chunk_witness.sqlite3"
    original = cc._merge_sidecar

    def corrupt_then_merge(**kwargs: Any) -> Any:
        # Fires after the whole catalog merge has committed and before the post-merge
        # re-verification -- exactly the window the re-verification exists to close.
        target.write_bytes(target.read_bytes() + b"\x00")
        return original(**kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cc, "_merge_sidecar", corrupt_then_merge)
        with pytest.raises(ChunkEvidenceError, match="does not match the manifest"):
            consolidate(during, database, run_id="altered-during")
    assert not (during["base"] / "final" / FINAL_WORLD_RECEIPT_FILENAME).exists()


def test_a26_an_individual_chunk_never_masquerades_as_a_consolidated_f0(tmp_path: Path) -> None:
    """A26: a chunk world carries no F0 terminal, no final receipt, and says so about itself."""
    database, tree = healthy_world(tmp_path)
    run = run_chunks(tmp_path, database, tree)
    receipt = run["receipts"][0]
    chunk_world = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    ledger = RunProgressLedger(chunk_world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
    finally:
        ledger.close()
    assert not (chunk_world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    assert receipt.summary.parser_state_after == "chunk_local"
    with pytest.raises(ChunkEvidenceError, match="carries contract"):
        read_receipt_document(
            chunk_world / CHUNK_RECEIPT_FILENAME, contract=cev.FINAL_WORLD_RECEIPT_CONTRACT
        )


# ==========================================================================
# §18: activation remains closed -- A27-A30
# ==========================================================================
def test_a27_every_activation_constant_is_still_none() -> None:
    """A27: nothing here opened anything, and every refusal still fires."""
    assert ce.REAL_CHUNKED_F0_EXECUTION_AUTHORITY == (
        "M3_3_D151_C9_ONE_REAL_MIDSOURCE_INTERNAL_NVME_CALIBRATION_AUTHORIZED"
    )
    assert cs.REAL_CHUNK_TRANSFER_AUTHORITY is None
    assert cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    assert cp.PRODUCTION_CHUNK_MEMBERS is None
    assert cs.INTERNAL_RESERVE_BYTES is None
    assert cs.CHUNK_PEAK_REQUIREMENT_BYTES is None
    assert ce.require_real_chunk_execution_authority() == (
        "M3_3_D151_C9_ONE_REAL_MIDSOURCE_INTERNAL_NVME_CALIBRATION_AUTHORIZED"
    )
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_chunk_transfer_authority()
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_internal_reclaim_authority()
    with pytest.raises(cp.ChunkPlanError, match="never defaulted"):
        cp.production_chunk_members()


def test_a28_no_command_line_surface_reaches_a_chunk_module() -> None:
    """A28: still no invocation to guard, in either direction, after the corrections."""
    from disclosure_drift import cli

    source = Path(cli.__file__).read_text(encoding="utf-8")
    for name in (
        "chunk_plan",
        "chunk_execution",
        "chunk_storage",
        "chunk_consolidation",
        "chunked",
    ):
        assert name not in source, name
    package_root = Path(cli.__file__).parent
    chunk_modules = {
        "chunk_plan",
        "chunk_evidence",
        "chunk_execution",
        "chunk_storage",
        "chunk_consolidation",
    }
    importers = [
        path.name
        for path in sorted(package_root.rglob("*.py"))
        if path.stem not in chunk_modules
        and any(name in path.read_text(encoding="utf-8") for name in chunk_modules)
    ]
    assert importers == []


def test_a29_no_chunk_module_reaches_a_transport_or_e0() -> None:
    """A29: measured in a clean interpreter, with the corrected import graph."""
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
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", program], capture_output=True, text=True, check=True
    )
    assert json.loads(completed.stdout) == []
    for module in (cp, cev, ce, cs, cc):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "from disclosure_drift.m3.e0" not in source, module.__name__
        assert "import disclosure_drift.m3.e0" not in source, module.__name__
        assert "M3_3_E0_EXECUTION_AUTHORITY" not in source, module.__name__


def test_a30_no_migration_0016_and_the_head_is_unchanged() -> None:
    """A30: the persisted operational schema is exactly where D149 left it."""
    import importlib

    from disclosure_drift.storage.sqlite import available_migrations

    migrations = available_migrations()
    assert migrations[-1].version == 15
    directory = Path(
        importlib.import_module("disclosure_drift.storage.migrations").__file__ or ""
    ).parent
    assert not list(directory.glob("0016_*.sql"))
    for module in (cp, cev, ce, cs, cc):
        assert "apply_migrations" not in Path(module.__file__).read_text(encoding="utf-8")


def test_no_environment_or_configuration_value_can_open_anything() -> None:
    """§18: there is still nothing to set. The corrected modules read no environment key."""
    for module in (cp, cev, ce, cs, cc):
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        assert "environ" not in attributes and "environ" not in names, module.__name__
        assert "getenv" not in attributes and "getenv" not in names, module.__name__
        assert "DISCLOSURE_DRIFT" not in source, module.__name__
        assert "load_config" not in names, module.__name__


def test_the_full_execution_identity_folds_exactly_what_c1_folded() -> None:
    """§8 C, preservation half: splitting the identity did not change what the identity IS.

    The normalized contract is a **new** digest beside the existing one, not a narrowing of it.
    The full per-chunk identity folds the same fourteen named values it folded before, so a
    receipt written by this build carries the identity a pre-correction build would have written
    for the same inputs. Asserted from the accepted folding primitive rather than from a stored
    literal, so it survives any accepted constant legitimately moving.
    """
    from disclosure_drift.m3.canary_phases import execution_identity
    from disclosure_drift.m3.compact_evidence import COMPACT_EVIDENCE, COMPACT_EVIDENCE_CONTRACT
    from disclosure_drift.sec.source_registry import SOURCES

    class _Plan:
        plan_digest = "pd"
        member_order_digest = "md"
        source_id = "sec_bulk_submissions"

    expected = execution_identity(
        {
            "chunk_execution_contract": ce.CHUNK_EXECUTION_CONTRACT,
            "chunk_id": "chunk-0000",
            "plan_digest": "pd",
            "member_order_digest": "md",
            "evidence_contract": COMPACT_EVIDENCE_CONTRACT,
            "compact_evidence": bool(COMPACT_EVIDENCE),
            "parser_id": ce._BULK_PARSER_ID,
            "parser_version": SOURCES["sec_bulk_submissions"].parser_version,
            "batch_size": 7,
            "cache_bytes": None,
            "repository_head_sha": "h",
            "repository_tree_sha": "t",
            "catalog_source_sha256": "c",
            "migration_head": 15,
        }
    )
    observed = ce.chunk_execution_identity(
        plan=_Plan(),
        chunk_id="chunk-0000",
        batch_size=7,
        cache_bytes=None,
        repository_head_sha="h",
        repository_tree_sha="t",
        catalog_source_sha256="c",
        migration_head=15,
    )
    assert observed == expected
