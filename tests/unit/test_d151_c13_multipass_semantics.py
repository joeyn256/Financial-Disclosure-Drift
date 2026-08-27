"""D151-C13: the multipass semantic oracle -- multipass == single-pass == monolithic, exactly.

**The first test is the falsified case.** D151-C8 proved that a naive two-level merge is wrong:
a level-1 group winner that loses globally at level 2 is treated as a first witness inside its
group and as a rival by the accepted monolithic rule, and for a payload whose non-membership
governed fields are inert the difference is five observation rows. ``test_o1`` builds exactly that
world, runs the multipass with the level-2 correction NEUTRALISED and proves the final world is
short exactly those five rows -- the positive control -- and then runs the real level 2 and proves
the full ``census_accession_observations`` rowset equals the accepted monolithic one.

Every other oracle here compares FULL governed rowsets by content digest, every row count, the
member manifest row by row, the source evidence, the member manifest digest, the compact-evidence
sidecar identity, the completeness digest and the ``census_parser_runs`` row -- through the same
:func:`test_d151_c1_equivalence.measure` the D151-C1 proof uses -- against the accepted monolithic
F0 driven through the accepted ``_f0``. Where a single-pass partition of the same source exists,
the multipass world is compared against it as well, receipt semantics included.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c1_equivalence as eq  # noqa: E402
import test_d151_c3_corrections as c3  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.canary_phases import (  # noqa: E402
    PHASE_F0,
    PHASE_F1,
    CanaryPhaseError,
    read_phase_checkpoint,
    require_phase_admission,
)
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    FINAL_WORLD_RECEIPT_CONTRACT,
    FINAL_WORLD_RECEIPT_FILENAME,
    ChunkEvidenceError,
    read_receipt_document,
)
from disclosure_drift.m3.compact_evidence import GOVERNED_ACCESSION_FIELDS  # noqa: E402
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    WORKING_CATALOG_FILENAME,
    RunProgressLedger,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.sec.census import _stable_id  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402

#: The shared accession's plain form, as ``census_accessions`` keys it.
SHARED_PLAIN = c1.SHARED_ACCESSION.replace("-", "")


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The shared pin, through the accepted identity seam -- see ``test_d151_c1_chunk_plan``."""
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# Custom worlds
# ==========================================================================
def build_custom_world(
    root: Path, members: list[tuple[str, dict[str, Any]]]
) -> tuple[Path, DataTree]:
    """A disposable catalog and data tree over an explicitly authored member sequence."""
    import test_d110_bounded_parse_memory as d110

    tree = DataTree.from_root(root / "data")
    database = root / "catalog.sqlite3"
    raw = c1.write_archive(tree.data_root / c1.ARCHIVE_RELATIVE, members)
    d110._seed_catalog(database, tree, raw)
    return database, tree


def _with_inert_shared_fields(document: dict[str, Any]) -> dict[str, Any]:
    """Make the document's SHARED accession an inert-field payload whose form does not round-trip.

    The three non-required governed fields are present and blank -- inert to the compact contract,
    so a first witness materializes nothing for them and a canonical row reconstructs nothing --
    and ``form`` carries surrounding whitespace, which the canonical column strips, so it is the
    one field a first witness DOES materialize. The two required fields stay valid.
    """
    document = copy.deepcopy(document)
    recent = document["filings"]["recent"]
    total = len(recent["accessionNumber"])
    assert recent["accessionNumber"][-1] == c1.SHARED_ACCESSION
    recent["acceptanceDateTime"] = ["2024-02-01T10:00:00.000Z"] * (total - 1) + [""]
    recent["primaryDocument"][-1] = ""
    recent["reportDate"][-1] = ""
    recent["form"][-1] = " 10-K "
    return document


def o1_members(*, primaries: int, sharers: tuple[int, ...], inert: tuple[int, ...]) -> list[Any]:
    """``primaries`` documents, one shard each for the first two, sharing the accession as told."""
    built: list[tuple[str, dict[str, Any]]] = []
    for index in range(primaries):
        cik = index + 1
        has_shard = index < 2
        if has_shard:
            built.append(c1.shard_document(cik))
        name, document = c1.primary_document(
            cik,
            filings=1,
            declares=(f"CIK{cik:010d}-submissions-001.json",) if has_shard else (),
            share=index in sharers,
        )
        if index in inert:
            document = _with_inert_shared_fields(document)
        built.append((name, document))
    return built


def observation_rows(world_directory: Path, accession_plain: str) -> set[tuple[str, str, str, str]]:
    """Every observation row of one accession: ``(id, parsed_record_id, field, raw_value_json)``."""
    with connect(world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
        return {
            (
                str(row["accession_observation_id"]),
                str(row["parsed_record_id"]),
                str(row["field_name"]),
                str(row["raw_value_json"]),
            )
            for row in connection.execute(
                "SELECT accession_observation_id, parsed_record_id, field_name, raw_value_json "
                "FROM census_accession_observations WHERE accession_plain = ?",
                (accession_plain,),
            )
        }


def parsed_record_of(world_directory: Path, member_name: str, accession_dashed: str) -> str:
    """The parsed record one member wrote for one accession; the native identity is dashed."""
    with connect(world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
        row = connection.execute(
            "SELECT parsed_record_id FROM census_parsed_records "
            "WHERE member_name = ? AND native_identity = ?",
            (member_name, f"accession:{accession_dashed}"),
        ).fetchone()
    assert row is not None
    return str(row["parsed_record_id"])


def _naive_staging(connection: Any, aliases: Any) -> tuple[int, int]:
    """The NAIVE level 2: the intermediates' rows are merged and nothing is corrected."""
    connection.execute(
        f"CREATE TEMP TABLE {cc.CORRECTIONS_TABLE} ("  # noqa: S608
        "accession_observation_id TEXT, accession_plain TEXT, source_observation_id TEXT, "
        "parsed_record_id TEXT, field_name TEXT, raw_value_json TEXT, observed_at_utc TEXT, "
        "conflict_indicator INTEGER)"
    )
    return 0, 0


# ==========================================================================
# O1: the falsified case, killed
# ==========================================================================
def test_o1_a_group_winner_that_loses_globally_is_upgraded_to_a_rival(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O1, with its positive control.

    Ten primaries and two shards, one member per chunk: twelve chunks, scheduled ``9 / 1`` primary
    plus ``2`` shard. The shared accession is witnessed by members 0 and 1 -- both in group-0000,
    so the true first witness is back-filled INSIDE its group -- and by member 9, alone in
    group-0001, with inert non-membership fields and a form that does not round-trip. Member 9 wins
    its group and loses globally. Under the naive level 2 its record carries exactly one row (the
    form); the accepted rival rule requires six; the five missing rows are named below, and the
    real level 2 produces every one of them.
    """
    database, tree = build_custom_world(
        tmp_path, o1_members(primaries=10, sharers=(0, 1, 9), inert=(9,))
    )
    eq.monolithic_f0(database, tree, tmp_path / "mono")
    reference = eq.measure(tmp_path / "mono")
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    assert plan.chunk_count == 12
    run = c13.execute_in_process(plan, tmp_path / "run", database, tree)
    schedule = cm.derive_merge_schedule(plan)
    assert [(g.region, len(g.chunk_ids)) for g in schedule.groups] == [
        ("primary", 9),
        ("primary", 1),
        ("shard", 2),
    ]
    loser_chunk = cp.chunk_by_id(plan, "chunk-0009")
    assert loser_chunk.region == cp.REGION_PRIMARY and schedule.groups[1].chunk_ids == (
        "chunk-0009",
    )

    # Level 1, real, for both variants: the intermediates are the same immutable inputs.
    partial = c13.merge_in_process(run, database, label="shared-level-1", finalize=False)
    assert partial["intermediates"][0].first_witness_accessions_corrected == 1  # members 0 and 1
    assert partial["intermediates"][1].first_witness_accessions_corrected == 0  # member 9, alone

    # The positive control: level 2 with the correction neutralised is short exactly five rows.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cm, "stage_first_witness_corrections", _naive_staging)
        naive = cm.finalize_multipass_body(
            c13.final_request(
                run,
                schedule_path=partial["schedule_path"],
                intermediates_root=partial["intermediates_root"],
                world_directory=partial["multipass_root"] / "naive",
                database=database,
                run_id="o1-naive",
            )
        )
    assert naive.first_witness_accessions_corrected == 0
    loser_parsed = parsed_record_of(
        partial["multipass_root"] / "naive", "CIK0000000010.json", c1.SHARED_ACCESSION
    )
    expected_missing = {
        _stable_id("accession-observation", SHARED_PLAIN, c1.OBSERVATION, loser_parsed, field)
        for field in ("acceptanceDateTime", "cik", "filingDate", "primaryDocument", "reportDate")
    }
    mono_rows = observation_rows(tmp_path / "mono", SHARED_PLAIN)
    naive_rows = observation_rows(partial["multipass_root"] / "naive", SHARED_PLAIN)
    assert naive_rows < mono_rows
    assert {row[0] for row in mono_rows - naive_rows} == expected_missing
    assert len(mono_rows - naive_rows) == 5
    # The one row the loser's group DID produce is its non-round-tripping form, raw.
    assert (loser_parsed, "form", '" 10-K "') in {row[1:] for row in naive_rows}
    with pytest.raises(AssertionError):
        eq.assert_equivalent(reference, eq.measure(partial["multipass_root"] / "naive"))

    # The fix: the real level 2 stages the global loser upgrade; the world is the monolithic one.
    final = cm.finalize_multipass_body(
        c13.final_request(
            run,
            schedule_path=partial["schedule_path"],
            intermediates_root=partial["intermediates_root"],
            world_directory=partial["multipass_root"] / "final",
            database=database,
            run_id="o1-fixed",
        )
    )
    assert final.first_witness_accessions_corrected == 1
    fixed_rows = observation_rows(partial["multipass_root"] / "final", SHARED_PLAIN)
    assert fixed_rows == mono_rows
    assert {row[2] for row in fixed_rows if row[1] == loser_parsed} == set(
        GOVERNED_ACCESSION_FIELDS
    )
    eq.assert_equivalent(reference, eq.measure(partial["multipass_root"] / "final"))
    assert final.status == "complete"


# ==========================================================================
# O2-O7: the remaining first-witness oracle
# ==========================================================================
def _oracle(
    tmp_path: Path,
    database: Path,
    tree: DataTree,
    *,
    chunk_members: int,
    label: str,
    single_pass_chunk_members: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Monolithic reference, multipass candidate at ``chunk_members``, optional single-pass twin."""
    eq.monolithic_f0(database, tree, tmp_path / f"mono-{label}")
    reference = eq.measure(tmp_path / f"mono-{label}")
    plan = c13.multipass_plan(tree, database, chunk_members=chunk_members)
    run = c13.execute_in_process(plan, tmp_path / f"run-{label}", database, tree)
    result = c13.merge_in_process(run, database, label=f"multipass-{label}", run_id=label)
    candidate = eq.measure(result["world_directory"])
    eq.assert_equivalent(reference, candidate)
    if single_pass_chunk_members is not None:
        single = c1x.run_chunked_f0(
            tmp_path,
            database,
            tree,
            chunk_members=single_pass_chunk_members,
            label=f"single-{label}",
            batch_size=c13.BATCH,
            repository=c1.PINNED,
        )
        consolidated = cc.consolidate_chunks(
            plan=single["plan"],
            internal_root=single["chunk_root"],
            operational_catalog=database,
            world_directory=single["base"] / "final",
            run_id=f"single-{label}",
        )
        eq.assert_equivalent(reference, eq.measure(consolidated.world_directory))
        _assert_same_final_semantics(consolidated.receipt, result["final"])
        result["single"] = consolidated
    result["plan"] = plan
    result["run"] = run
    return reference, result


def _assert_same_final_semantics(
    single: cc.FinalWorldReceipt, multipass: cc.FinalWorldReceipt
) -> None:
    """The semantic half of two final receipts, equal; the mechanical half, named."""
    for field in (
        "contract",
        "plan_digest",  # differs: two partitions
        "source_instance_id",
        "source_observation_id",
        "source_sha256",
        "repository_head_sha",
        "repository_tree_sha",
        "catalog_source_sha256",
        "parser_run_id",
        "run_outcome",
        "parser_state_after",
        "members",
        "records",
        "parsed_records",
        "quarantined_records",
        "omitted_field_observations",
        "materialized_field_observations",
        "completeness_digest",
        "member_manifest_digest",
        "table_row_counts",
        "status",
    ):
        if field == "plan_digest":
            assert getattr(single, field) != getattr(multipass, field)
            continue
        assert getattr(single, field) == getattr(multipass, field), field
    assert single.consolidation_contract == cc.CONSOLIDATION_CONTRACT
    assert multipass.consolidation_contract == cm.MULTIPASS_CONSOLIDATION_CONTRACT
    assert single.chunk_count <= 9 < multipass.chunk_count


def test_o2_an_accession_witnessed_in_more_than_two_groups(tmp_path: Path) -> None:
    """Nineteen primaries sharing at 0, 9 and 18 -- one witness in each of three groups."""
    database, tree = c1.build_world(tmp_path, members=19, filings=1, shards=1, share_every=9)
    reference, result = _oracle(tmp_path, database, tree, chunk_members=1, label="o2")
    assert [(g.region, len(g.chunk_ids)) for g in result["schedule"].groups] == [
        ("primary", 9),
        ("primary", 9),
        ("primary", 1),
        ("shard", 1),
    ]
    assert result["final"].first_witness_accessions_corrected == 1
    assert result["final"].first_witness_rows_staged > 0
    assert reference["counts"] == eq.measure(result["world_directory"])["counts"]


def test_o3_a_canonical_raw_disagreement_keeps_the_raw_row_under_the_accepted_priority(
    tmp_path: Path,
) -> None:
    """The global winner materialized its raw form at level 1; the level-2 back-fill loses to it."""
    members = o1_members(primaries=10, sharers=(0, 9), inert=(0,))
    database, tree = build_custom_world(tmp_path, members)
    reference, result = _oracle(tmp_path, database, tree, chunk_members=1, label="o3")
    winner_parsed = parsed_record_of(
        result["world_directory"], "CIK0000000001.json", c1.SHARED_ACCESSION
    )
    rows = observation_rows(result["world_directory"], SHARED_PLAIN)
    assert (winner_parsed, "form", '" 10-K "') in {row[1:] for row in rows}
    assert (winner_parsed, "form", '"10-K"') not in {row[1:] for row in rows}
    assert rows == observation_rows(tmp_path / "mono-o3", SHARED_PLAIN)


def test_o4_one_identity_witnessed_many_times_in_one_group_and_again_in_another(
    tmp_path: Path,
) -> None:
    members = o1_members(primaries=12, sharers=(0, 1, 2, 3, 9, 11), inert=(9,))
    database, tree = build_custom_world(tmp_path, members)
    reference, result = _oracle(tmp_path, database, tree, chunk_members=1, label="o4")
    assert result["intermediates"][0].first_witness_accessions_corrected == 1
    assert result["intermediates"][1].first_witness_accessions_corrected == 1
    assert result["final"].first_witness_accessions_corrected == 1


def test_o5_moving_the_group_boundary_moves_nothing(tmp_path: Path) -> None:
    """Same members, same order, two partitions: groups ``9 / 9 / 2 + 2`` and ``9 / 1 + 1``."""
    database, tree = c1.build_world(
        tmp_path, members=20, filings=2, shards=2, share_every=3, junk=3, unknown=4
    )
    reference, narrow = _oracle(tmp_path, database, tree, chunk_members=1, label="o5-narrow")
    _reference, wide = _oracle(tmp_path, database, tree, chunk_members=2, label="o5-wide")
    assert [len(g.chunk_ids) for g in narrow["schedule"].groups] == [9, 9, 2, 2]
    assert [len(g.chunk_ids) for g in wide["schedule"].groups] == [9, 1, 1]
    assert narrow["final"].completeness_digest == wide["final"].completeness_digest
    assert narrow["final"].member_manifest_digest == wide["final"].member_manifest_digest
    assert dict(narrow["final"].table_row_counts) == dict(wide["final"].table_row_counts)
    eq.assert_equivalent(eq.measure(narrow["world_directory"]), eq.measure(wide["world_directory"]))


def test_o6_o7_the_region_barrier_and_the_uneven_final_group(tmp_path: Path) -> None:
    """Ten primaries and eight shards: a one-chunk primary group, and no group crosses regions."""
    database, tree = c1.build_world(tmp_path, members=10, filings=2, shards=8, share_every=2)
    reference, result = _oracle(
        tmp_path, database, tree, chunk_members=1, label="o6", single_pass_chunk_members=3
    )
    groups = result["schedule"].groups
    assert [(g.region, len(g.chunk_ids)) for g in groups] == [
        ("primary", 9),
        ("primary", 1),
        ("shard", 8),
    ]
    for group, intermediate in zip(groups, result["intermediates"], strict=True):
        assert intermediate.region == group.region
        assert intermediate.members == group.member_count
    assert result["single"].receipt.chunk_count == 7


def test_o7_the_thirty_four_chunk_shape_has_an_uneven_final_primary_group(tmp_path: Path) -> None:
    database, tree = c1.build_world(tmp_path, members=33, filings=1, shards=1, share_every=5)
    reference, result = _oracle(
        tmp_path, database, tree, chunk_members=1, label="o7", single_pass_chunk_members=5
    )
    assert [len(g.chunk_ids) for g in result["schedule"].groups] == [9, 9, 9, 6, 1]
    assert result["final"].chunk_count == 34
    assert result["single"].receipt.chunk_count == 8


# ==========================================================================
# The 10 / 18 / 34 sweep, over the hostile world shapes
# ==========================================================================
@pytest.mark.parametrize(
    ("members", "shards", "shape", "single"),
    [
        (9, 1, {"share_every": 3}, 3),
        (16, 2, {"share_every": 4, "junk": 3, "unknown": 4}, 4),
        (33, 1, {"share_every": 5, "duplicate": True}, 5),
        (14, 4, {"share_every": 2, "junk": 2, "unknown": 3, "duplicate": True}, 4),
    ],
    ids=["ten", "eighteen", "thirty-four", "eighteen-hostile"],
)
def test_the_multipass_world_equals_the_monolithic_and_single_pass_worlds(
    tmp_path: Path, members: int, shards: int, shape: dict[str, Any], single: int
) -> None:
    database, tree = c1.build_world(tmp_path, members=members, filings=2, shards=shards, **shape)
    reference, result = _oracle(
        tmp_path, database, tree, chunk_members=1, label="sweep", single_pass_chunk_members=single
    )
    assert result["plan"].chunk_count == members + shards
    assert result["final"].members == members + shards
    assert result["final"].status == "complete"
    assert reference["parser_state"] == "completed"


def test_the_multipass_world_is_accepted_by_f1_and_f2_and_admits_f1(tmp_path: Path) -> None:
    database, tree = c1.build_world(tmp_path, members=9, filings=2, shards=1, share_every=2)
    reference, result = _oracle(tmp_path, database, tree, chunk_members=1, label="f1f2")
    assert eq._f1_and_f2(result["world_directory"], database) == eq._f1_and_f2(
        tmp_path / "mono-f1f2", database
    )
    assert c1.PINNED is not None
    final = result["final"]
    contract = result["intermediates"][0].execution_contract
    ledger = RunProgressLedger(result["world_directory"] / PROGRESS_LEDGER_FILENAME)
    try:
        checkpoint = read_phase_checkpoint(ledger, PHASE_F0)
        assert checkpoint is not None and checkpoint.status == "complete"
        assert set(checkpoint.payload) == cc.ACCEPTED_F0_PAYLOAD_KEYS
        assert checkpoint.payload["completeness_digest"] == final.completeness_digest
        admission = require_phase_admission(
            ledger,
            phase=PHASE_F1,
            run_id="f1f2",
            source_instance_id=c1.INSTANCE,
            execution_identity=canary.phase_execution_identity(
                repository=c1.PINNED, batch_size=contract.batch_size
            ),
            repository_head_sha=c1.PINNED.head_sha,
            repository_tree_sha=c1.PINNED.tree_sha,
            catalog_source_sha256=final.catalog_source_sha256,
            migration_head=contract.migration_head,
            plan_fingerprint=eq._plan_fingerprint_of(database),
        )
        assert admission.predecessor is not None and admission.predecessor.phase == "f0"
        progress = ledger.progress(c1.INSTANCE)
        assert progress is not None and progress.state == "parsed"
    finally:
        ledger.close()


def test_the_projection_digest_chain_is_identical_across_all_three_paths(tmp_path: Path) -> None:
    """ProjectionDigest: a fold over canonical member order, and no boundary moves it."""
    database, tree = c1.build_world(tmp_path, members=16, filings=2, shards=2, share_every=4)
    reference, result = _oracle(
        tmp_path, database, tree, chunk_members=1, label="digest", single_pass_chunk_members=4
    )
    assert result["final"].completeness_digest == result["single"].receipt.completeness_digest
    assert (
        result["final"].completeness_digest == reference["source_evidence"]["completeness_digest"]
    )
    assert result["final"].member_manifest_digest == reference["manifest_digest"]
    # Group-local ordinals never leak: every intermediate's manifest is its canonical interval.
    for group, intermediate in zip(result["schedule"].groups, result["intermediates"], strict=True):
        assert intermediate.start == group.start and intermediate.end == group.end
        assert intermediate.members == group.member_count


def test_the_counters_compose_exactly_across_chunk_group_and_global_boundaries(
    tmp_path: Path,
) -> None:
    """No negative omitted count, no double correction, no clamp: the totals are the monolithic."""
    database, tree = c1.build_world(tmp_path, members=19, filings=2, shards=1, share_every=3)
    reference, result = _oracle(tmp_path, database, tree, chunk_members=1, label="counters")
    final = result["final"]
    source = reference["source_evidence"]
    assert final.omitted_field_observations == int(source["omitted_field_observations"])
    assert final.materialized_field_observations == int(source["materialized_field_observations"])
    assert final.records == int(source["records"])
    level_one_delta = sum(item.evidence_delta for item in result["intermediates"])
    assert level_one_delta > 0 and final.evidence_delta > 0
    # Within-chunk, within-group and cross-group deltas are disjoint and sum to the whole.
    chunk_materialized = sum(
        receipt.summary.materialized_field_observations for receipt in result["run"]["receipts"]
    )
    assert (
        chunk_materialized + level_one_delta + final.evidence_delta
        == final.materialized_field_observations
    )


# ==========================================================================
# Level 1 is nonterminal; level 2 is the accepted finalization
# ==========================================================================
def test_a_level_one_intermediate_is_never_a_final_world(tmp_path: Path) -> None:
    """A20/A21: no F0 checkpoint, F1 refuses, not a final receipt, no source parser state."""
    database, tree = c1.build_world(tmp_path, members=9, filings=2, shards=1)
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, tmp_path / "run", database, tree)
    partial = c13.merge_in_process(run, database, finalize=False)
    for group, receipt in zip(partial["schedule"].groups, partial["intermediates"], strict=True):
        directory = (
            partial["intermediates_root"] / group.group_id / f"attempt-{receipt.attempt:03d}"
        )
        assert not (directory / FINAL_WORLD_RECEIPT_FILENAME).exists()
        with pytest.raises(ChunkEvidenceError, match="carries contract"):
            read_receipt_document(
                directory / cm.INTERMEDIATE_RECEIPT_FILENAME, contract=FINAL_WORLD_RECEIPT_CONTRACT
            )
        ledger = RunProgressLedger(directory / PROGRESS_LEDGER_FILENAME)
        try:
            assert read_phase_checkpoint(ledger, PHASE_F0) is None
            progress = ledger.progress(c1.INSTANCE)
            assert progress is not None and progress.state == "in_progress"
            with pytest.raises(CanaryPhaseError, match="no durable terminal checkpoint"):
                require_phase_admission(
                    ledger,
                    phase=PHASE_F1,
                    run_id="c13",
                    source_instance_id=c1.INSTANCE,
                    execution_identity="x",
                    repository_head_sha=receipt.repository_head_sha,
                    repository_tree_sha=receipt.repository_tree_sha,
                    catalog_source_sha256=receipt.execution_contract.catalog_source_sha256,
                    migration_head=receipt.execution_contract.migration_head,
                    plan_fingerprint="fingerprint",
                )
        finally:
            ledger.close()
        with connect(directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
            state = connection.execute(
                "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
                (c1.INSTANCE,),
            ).fetchone()
            edges = connection.execute(
                "SELECT COUNT(*) AS n FROM census_candidate_lineage_edges"
            ).fetchone()
        assert str(state["parser_state"]) == "not_started"
        assert int(edges["n"]) == 0
        assert "parser_state_after" not in dict(receipt.as_record())
    assert not (partial["multipass_root"] / "final").exists()


def test_level_two_stops_at_the_accepted_d140_r12_gate(tmp_path: Path) -> None:
    """A blocking source: level 1 completes, level 2 refuses, nothing terminal exists."""
    database, tree = c1.build_world(tmp_path, members=9, filings=2, shards=1, malformed=2)
    eq.monolithic_f0(database, tree, tmp_path / "mono", strict=False)
    reference = eq.measure(tmp_path / "mono")
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, tmp_path / "run", database, tree)
    partial = c13.merge_in_process(run, database, finalize=False)
    world = partial["multipass_root"] / "final"
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        cm.finalize_multipass_body(
            c13.final_request(
                run,
                schedule_path=partial["schedule_path"],
                intermediates_root=partial["intermediates_root"],
                world_directory=world,
                database=database,
                run_id="blocking",
            )
        )
    # The merge was exact and complete -- the diagnostic rows and sidecar are the monolithic ones.
    candidate = eq.measure(world)
    eq.assert_equivalent(reference, candidate)
    assert candidate["parser_state"] == "failed"
    assert not (world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
        progress = ledger.progress(c1.INSTANCE)
        assert progress is not None and progress.state == "in_progress"
    finally:
        ledger.close()
    # And with the accepted gate neutralised, the same intermediates finalize -- the gate is the
    # refusal, and nothing else (the D151-C3 R06 proof, on the multipass path).
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cm, "require_f0_success", lambda outcome: outcome)
        bypassed = cm.finalize_multipass_body(
            c13.final_request(
                run,
                schedule_path=partial["schedule_path"],
                intermediates_root=partial["intermediates_root"],
                world_directory=partial["multipass_root"] / "bypassed",
                database=database,
                run_id="bypassed",
            )
        )
    assert bypassed.status == "complete" and bypassed.parser_state_after == "failed"


def test_the_final_receipt_binds_the_measured_identity_and_every_chunk(tmp_path: Path) -> None:
    database, tree = c1.build_world(tmp_path, members=9, filings=2, shards=1)
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, tmp_path / "run", database, tree)
    result = c13.merge_in_process(run, database)
    final = result["final"]
    assert c1.PINNED is not None
    assert final.contract == FINAL_WORLD_RECEIPT_CONTRACT
    assert final.consolidation_contract == cm.MULTIPASS_CONSOLIDATION_CONTRACT
    assert final.repository_head_sha == c1.PINNED.head_sha
    assert final.plan_digest == plan.plan_digest
    assert final.chunk_count == 10 == len(final.chunk_inputs)
    assert [item["chunk_id"] for item in final.chunk_inputs] == [b.chunk_id for b in plan.chunks]
    assert final.chunks_unchanged is True
    stored = read_receipt_document(
        result["world_directory"] / FINAL_WORLD_RECEIPT_FILENAME,
        contract=FINAL_WORLD_RECEIPT_CONTRACT,
    )
    assert stored["consolidation_contract"] == cm.MULTIPASS_CONSOLIDATION_CONTRACT
    assert stored["chunk_count"] == 10
    # Every chunk artifact and every intermediate is exactly as it was: nothing was deleted.
    for receipt in run["receipts"]:
        found = ce.completed_chunk_receipt(run["chunk_root"], receipt.chunk_id)
        assert found is not None and found[0].manifest.digest == receipt.manifest.digest
    for group in result["schedule"].groups:
        assert cm.completed_intermediate_receipt(result["intermediates_root"], group.group_id)


def test_the_hostile_c3_first_witness_world_holds_under_the_multipass(tmp_path: Path) -> None:
    """The D151-C3 R37 oracle world, widened to a multipass partition."""
    database, tree = c1.build_world(
        tmp_path, members=12, filings=2, shards=2, share_every=2, junk=3, unknown=4
    )
    reference, result = _oracle(
        tmp_path, database, tree, chunk_members=1, label="c3", single_pass_chunk_members=2
    )
    assert result["final"].first_witness_accessions_corrected >= 1
    assert c3.healthy_world is not None
