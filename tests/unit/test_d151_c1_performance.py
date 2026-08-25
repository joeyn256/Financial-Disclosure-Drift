"""D151-C1 §§26-28: the performance experiment, and the one claim it has to survive.

D151-C1 §16 makes PASS conditional on consolidation **not** recreating the monolithic random-write
bottleneck, and §35 says correct output that merely moves that bottleneck to the final merge is
not a pass. This module measures rather than asserts.

**The mechanism, measured machine-independently.** Accepted Decision 118 identified F0's
constraint as random-write amplification: rows keyed by content digests land on unpredictable
pages of a B-tree far larger than any page cache, so each insert dirties a fresh page. The
measurement here is **write-ahead-log bytes per row**, which is deterministic -- it counts pages
SQLite actually wrote, not how fast this laptop happened to write them. The same rows loaded in
key order write materially fewer, and the ratio grows as the tree outgrows the cache. That ratio
is exactly what a key-sorted bulk merge removes and what a record-by-record merge would keep.

**What this module cannot do, stated rather than implied.** Host B is capacity constrained. The
regime the architecture is *for* -- a two-hundred-gigabyte world on an external volume, with a
working set orders of magnitude past RAM -- is not reachable here, and no bounded synthetic
fixture on this host reaches it. So the wall-clock A/B below is reported as what it is: a
measurement at a scale where the whole database fits in the operating system's page cache, where
the chunked path's fixed per-chunk costs dominate, and where the amplification the architecture
removes is at its smallest. The extrapolation to Host A is labelled as extrapolation.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c1_equivalence as eq  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402

#: A row wide enough that a page holds few of them, so the page-touch pattern is what is measured
#: rather than the row-packing.
_PAYLOAD = "x" * 200

SYNTHETIC_VOLUME = "00000000-0000-0000-0000-0000C1C1C1C1"


def _rows(start: int, count: int) -> Any:
    for index in range(start, start + count):
        yield (hashlib.sha256(str(index).encode()).hexdigest(), index, _PAYLOAD)


def _open(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, isolation_level=None)
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA wal_autocheckpoint = 0")
    connection.execute("CREATE TABLE t (k TEXT PRIMARY KEY, n INTEGER, p TEXT) STRICT")
    return connection


def _wal_bytes(path: Path) -> int:
    wal = Path(f"{path}-wal")
    return wal.stat().st_size if wal.exists() else 0


def _load(path: Path, rows: list[tuple[str, int, str]], block: int) -> tuple[float, int]:
    """Load rows in the order given, and return wall time and total write-ahead-log bytes.

    The log is checkpointed and truncated at every block boundary, so the sum over blocks is the
    number of bytes SQLite genuinely wrote rather than the size the file happened to end at.
    """
    connection = _open(path)
    written = 0
    start = time.perf_counter()
    for offset in range(0, len(rows), block):
        connection.execute("BEGIN")
        connection.executemany("INSERT INTO t VALUES (?, ?, ?)", rows[offset : offset + block])
        connection.execute("COMMIT")
        written += _wal_bytes(path)
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    wall = time.perf_counter() - start
    connection.close()
    return wall, written


def _amplification(tmp_path: Path, total: int) -> dict[str, float]:
    unsorted_rows = list(_rows(0, total))
    sorted_rows = sorted(unsorted_rows)
    block = max(total // 8, 1)
    random_wall, random_bytes = _load(tmp_path / f"r{total}.sqlite3", unsorted_rows, block)
    sorted_wall, sorted_bytes = _load(tmp_path / f"s{total}.sqlite3", sorted_rows, block)
    return {
        "rows": total,
        "random_wall": random_wall,
        "sorted_wall": sorted_wall,
        "random_bytes_per_row": random_bytes / total,
        "sorted_bytes_per_row": sorted_bytes / total,
        "write_amplification": random_bytes / max(sorted_bytes, 1),
        "wall_ratio": random_wall / max(sorted_wall, 1e-9),
    }


# ==========================================================================
# §26/§16: the mechanism
# ==========================================================================
def test_a_random_key_load_writes_more_than_a_key_sorted_one(tmp_path: Path) -> None:
    """The load-bearing measurement, in bytes rather than seconds.

    Identical rows, identical schema, identical commit boundaries -- only the **order** differs.
    The random-key load is the shape the monolithic F0 writes in; the key-sorted load is the shape
    every consolidation statement writes in. If the two wrote the same number of bytes, the whole
    architecture would be pointless, and this would say so.
    """
    small = _amplification(tmp_path, 60_000)
    large = _amplification(tmp_path, 240_000)
    print(json.dumps({"small": small, "large": large}, indent=2))  # noqa: T201
    assert small["write_amplification"] > 1.0
    assert large["write_amplification"] > 1.0
    # The amplification is a function of tree size over cache size, so it grows with scale. A
    # fourfold data increase must not make it smaller.
    assert large["write_amplification"] >= small["write_amplification"] * 0.95
    assert large["random_bytes_per_row"] >= small["random_bytes_per_row"] * 0.95
    # And the key-sorted load stays flat, which is the property that makes the merge affordable.
    assert large["sorted_bytes_per_row"] <= small["sorted_bytes_per_row"] * 1.3


# ==========================================================================
# §26: the A/B over the real F0 path
# ==========================================================================
def _measure_chunked(
    tmp_path: Path, database: Path, tree: DataTree, *, size: int, label: str
) -> dict[str, Any]:
    start = time.perf_counter()
    run = c1x.run_chunked_f0(
        tmp_path, database, tree, chunk_members=size, label=label, batch_size=250
    )
    chunk_wall = time.perf_counter() - start
    start = time.perf_counter()
    result = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final",
    )
    consolidate_wall = time.perf_counter() - start
    chunk_bytes = sum(
        path.stat().st_size for path in run["chunk_root"].rglob("*") if path.is_file()
    )
    return {
        "chunks": run["plan"].chunk_count,
        "chunk_wall": chunk_wall,
        "consolidate_wall": consolidate_wall,
        "total_wall": chunk_wall + consolidate_wall,
        "chunk_bytes": chunk_bytes,
        "final_db_bytes": (result.world_directory / "working_catalog.sqlite3").stat().st_size,
        "peak_chunk_rss": max((r.rss_peak_bytes or 0) for r in run["receipts"]),
        "rows": sum(result.receipt.table_row_counts.values()),
        "members": result.receipt.members,
        "result": result,
    }


@pytest.mark.parametrize("members", [24, 48])
def test_the_ab_experiment_is_recorded_at_two_scales(tmp_path: Path, members: int) -> None:
    """A: monolithic. B: chunk execution. C: consolidation. D: B + C -- all recorded.

    **This test records; it does not race.** Every wall-clock figure is printed and none is
    asserted against another, because at a scale this small both sides are dominated by fixed
    costs that a two-to-three-hour chunk amortizes away entirely: an interpreter start, a package
    import, one copy of the accepted catalog and two manifest hashes per chunk on the chunked
    side, and one world creation, one attach pass and one index rebuild on the merge side. A
    threshold asserted here would be a measurement of this laptop, not of the architecture.

    The §16 question -- does the merge stay a fraction of the work or become the run? -- is
    asserted where it can be answered honestly: in
    :func:`test_the_merge_cost_grows_no_faster_than_the_data`, which compares the merge against
    itself at two scales, and in
    :func:`test_a_random_key_load_writes_more_than_a_key_sorted_one`, which counts bytes rather
    than seconds. What IS asserted here is structural and scale-free: the consolidated world is
    the size of the monolithic one rather than a multiple of it, and every consolidation reached
    its terminal.
    """
    database, tree = c1.build_world(
        tmp_path, members=members, filings=12, shards=members // 6, shared_alias=False
    )
    start = time.perf_counter()
    eq.monolithic_f0(database, tree, tmp_path / "mono")
    monolithic_wall = time.perf_counter() - start
    measured = {
        "members": members,
        "monolithic_wall": monolithic_wall,
        "monolithic_db_bytes": (tmp_path / "mono" / "working_catalog.sqlite3").stat().st_size,
        "chunked": {},
    }
    for size in (max(members // 6, 1), max(members // 2, 1), 10**9):
        record = _measure_chunked(tmp_path, database, tree, size=size, label=f"n{size}")
        result = record.pop("result")
        measured["chunked"][str(size)] = record
        # The final world is the size of the monolithic one, not a multiple of it -- the merge
        # produces ONE world rather than a world plus an intermediate the size of the world.
        assert record["final_db_bytes"] <= measured["monolithic_db_bytes"] * 1.2
        assert result.receipt.status == "complete"
        record["merge_share_of_monolithic"] = record["consolidate_wall"] / monolithic_wall
        record["total_over_monolithic"] = record["total_wall"] / monolithic_wall
    print(json.dumps(measured, indent=2))  # noqa: T201


def test_the_merge_cost_grows_no_faster_than_the_data(tmp_path: Path) -> None:
    """§16 restated as a scaling question: does consolidation stay a fraction, or become the run?

    Four times the rows must not cost more than about four times the merge. A merge that had
    inherited the monolithic random-write shape would grow superlinearly, because the cost per
    row of a random insert rises with the tree.
    """
    walls: dict[int, float] = {}
    rows: dict[int, int] = {}
    for members in (16, 64):
        root = tmp_path / f"m{members}"
        root.mkdir()
        database, tree = c1.build_world(
            root, members=members, filings=12, shards=members // 8, shared_alias=False
        )
        record = _measure_chunked(root, database, tree, size=max(members // 8, 1), label="run")
        record.pop("result")
        walls[members] = record["consolidate_wall"]
        rows[members] = record["rows"]
    growth = rows[64] / rows[16]
    cost = walls[64] / max(walls[16], 1e-9)
    print(json.dumps({"row_growth": growth, "merge_cost_growth": cost}, indent=2))  # noqa: T201
    assert growth > 3.0
    assert cost <= growth * 1.75


# ==========================================================================
# §27: the internal-hot / external-spill costs
# ==========================================================================
def test_the_transfer_and_readback_costs_are_recorded(tmp_path: Path) -> None:
    """§27: verified transfer, independent re-read, and consolidation from either tier.

    Every number here is measured on **local** storage. No real external SSD benchmark is
    authorized in C1, so the external tier is stood in for by a second directory on the same
    filesystem: what is measured is the *work* a transfer does -- one sequential read, one
    sequential write, and one full independent re-read and re-hash -- not the device that would
    do it. Scaling those bytes to a real device is extrapolation and is labelled as such.
    """
    database, tree = c1.build_world(tmp_path, members=24, filings=12, shards=4, shared_alias=False)
    run = c1x.run_chunked_f0(tmp_path, database, tree, chunk_members=6, label="tiers")
    external = tmp_path / "external"
    transferred = 0
    start = time.perf_counter()
    for bounds in run["plan"].chunks:
        placement = cs.derive_chunk_placement(
            run["plan"], bounds.chunk_id, internal_root=run["chunk_root"]
        )
        assert placement.internal_directory is not None
        receipt = cs.transfer_chunk(
            source_directory=placement.internal_directory,
            destination_directory=external / bounds.chunk_id,
            destination_volume_uuid=SYNTHETIC_VOLUME,
        )
        transferred += receipt.bytes_transferred
    transfer_wall = time.perf_counter() - start

    start = time.perf_counter()
    internal_result = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final-internal",
    )
    internal_wall = time.perf_counter() - start

    empty = tmp_path / "no-internal"
    empty.mkdir()
    start = time.perf_counter()
    external_result = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=empty,
        operational_catalog=database,
        world_directory=run["base"] / "final-external",
        external_root=external,
    )
    external_wall = time.perf_counter() - start

    print(  # noqa: T201
        json.dumps(
            {
                "chunks": run["plan"].chunk_count,
                "bytes_transferred": transferred,
                "transfer_wall": transfer_wall,
                "transfer_bytes_per_second": transferred / max(transfer_wall, 1e-9),
                "consolidate_from_internal_wall": internal_wall,
                "consolidate_from_external_wall": external_wall,
                "internal_chunk_bytes": sum(
                    path.stat().st_size for path in run["chunk_root"].rglob("*") if path.is_file()
                ),
                "external_chunk_bytes": sum(
                    path.stat().st_size for path in external.rglob("*") if path.is_file()
                ),
            },
            indent=2,
        )
    )
    # The tier a chunk is read from is a performance choice and never a semantic one.
    assert (
        eq.measure(external_result.world_directory)["tables"]
        == eq.measure(internal_result.world_directory)["tables"]
    )
    assert external_result.receipt.completeness_digest == (
        internal_result.receipt.completeness_digest
    )
    assert {item.tier for item in external_result.inputs} == {cs.TIER_EXTERNAL}
    assert {item.tier for item in internal_result.inputs} == {cs.TIER_INTERNAL}


def test_the_chunk_artifact_carries_the_seed_catalog_once_per_chunk(tmp_path: Path) -> None:
    """§14: what cloning the accepted catalog into every chunk actually costs, measured.

    The chunk world is a copy of the same accepted operational catalog the monolithic F0 copies,
    because that is what makes the two provably the same parse rather than merely similar ones.
    The cost is one seed copy per chunk, and it is recorded here rather than asserted away.
    """
    database, tree = c1.build_world(tmp_path, members=12, filings=8, shards=2, shared_alias=False)
    seed = database.stat().st_size
    run = c1x.run_chunked_f0(tmp_path, database, tree, chunk_members=4, label="seed")
    per_chunk = [
        sum(
            path.stat().st_size
            for path in (run["chunk_root"] / bounds.chunk_id / "attempt-000").iterdir()
            if path.is_file()
        )
        for bounds in run["plan"].chunks
    ]
    print(  # noqa: T201
        json.dumps(
            {
                "seed_catalog_bytes": seed,
                "chunks": run["plan"].chunk_count,
                "chunk_artifact_bytes": per_chunk,
                "seed_share_of_smallest_chunk": seed / min(per_chunk),
            },
            indent=2,
        )
    )
    assert all(size >= seed for size in per_chunk)
