"""D151-C1: deterministic chunk identity, and the synthetic world every C1 proof runs against.

This module carries two things. The first is the **hostile synthetic bulk archive** the whole
D151-C1 suite is built on: primary submissions documents, historical overflow shards declared by
parents that may sit before or after them, accessions co-filed by several registrants, quarantined
records, unknown fields, cross-member duplicate identities, and blocking structural failures. No
test in this suite reads a real SEC artifact, resolves the private evidence root, or touches a real
catalog.

The second is the proof set for :mod:`~disclosure_drift.m3.chunk_plan`: that a chunk is a
deterministic interval over a canonical member ordering derived from the archive's own central
directory, that the ordering is exactly the accepted F0 absorb order, that a partition covers the
source once with no gap and no overlap, and that every way of lying to a chunk about which
partition or which artifact it belongs to is refused before a member is decompressed.
"""

from __future__ import annotations

import copy
import json
import subprocess
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from disclosure_drift.m3 import chunk_plan as cp
from disclosure_drift.m3 import repository_identity
from disclosure_drift.m3.chunk_plan import ChunkBounds, ChunkPlanError
from disclosure_drift.m3.offline_parse import OfflineParseError
from disclosure_drift.m3.repository_identity import RepositoryIdentity, repository_identity_at
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.archive import ArchiveDefenceError, iter_members

# ==========================================================================
# The synthetic world
# ==========================================================================
ARCHIVE_TIMESTAMP: tuple[int, int, int, int, int, int] = (2026, 1, 1, 0, 0, 0)
ARCHIVE_RELATIVE = "raw/sec/bulk/sec_bulk_submissions-synthetic.zip"
OBSERVATION = "obs-bulk-1"
INSTANCE = "base|sec_bulk_submissions|1"
SOURCE_ID = "sec_bulk_submissions"

#: One accession co-filed by several registrants. It is the whole reason the compact contract's
#: first-witness rule is a *whole-source* fact, and therefore the one thing a chunk cannot decide
#: for itself.
SHARED_ACCESSION = "0000000001-24-999999"


def primary_document(
    cik: int,
    *,
    filings: int,
    declares: tuple[str, ...] = (),
    share: bool = False,
    drop_filings: bool = False,
    duplicate_first: bool = False,
    junk_accession: bool = False,
    unknown_field: bool = False,
    shared_alias: bool = True,
    member_name: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """One primary submissions document, named the way the real bulk archive names them.

    ``member_name`` overrides the filename without touching the registrant the document declares.
    It exists for exactly one case: a member that repeats an **earlier** member's registrant, so
    that the two carry the same accession identities under two different member names -- which is
    what makes a duplicate identity a cross-*member*, and therefore a cross-*chunk*, fact.
    """
    padded = f"{cik:010d}"
    numbers = [f"{padded}-24-{index:06d}" for index in range(filings)]
    if share:
        numbers.append(SHARED_ACCESSION)
    if duplicate_first and numbers:
        numbers = [numbers[0], *numbers]
    if junk_accession:
        numbers = [*numbers, "not-an-accession-number"]
    recent = {
        "accessionNumber": numbers,
        "filingDate": ["2024-02-01"] * len(numbers),
        "form": ["10-K"] * len(numbers),
        "reportDate": ["2023-12-31"] * len(numbers),
        "primaryDocument": [f"d{cik}.htm"] * len(numbers),
    }
    document: dict[str, Any] = {
        "cik": str(cik),
        "name": f"SYNTHETIC {cik}",
        "sic": "2834",
        "fiscalYearEnd": "1231",
        "tickers": [f"SY{cik}", "SHARED"] if shared_alias else [f"SY{cik}"],
        "exchanges": ["Nasdaq"],
        "formerNames": [{"name": f"OLD {cik}", "from": "2018-01-01", "to": "2020-01-01"}],
        "filings": {
            "recent": recent,
            "files": [
                {
                    "name": name,
                    "filingCount": 2,
                    "filingFrom": "2010-01-01",
                    "filingTo": "2010-12-31",
                }
                for name in declares
            ],
        },
    }
    if unknown_field:
        document["someUnknownTopLevelField"] = "value"
    if drop_filings:
        document = copy.deepcopy(document)
        del document["filings"]
    return (member_name or f"CIK{padded}.json"), document


def shard_document(cik: int, index: int = 1, *, accessions: int = 3) -> tuple[str, dict[str, Any]]:
    """One historical overflow shard: parallel arrays and no registrant identity of its own."""
    padded = f"{cik:010d}"
    return f"CIK{padded}-submissions-{index:03d}.json", {
        "accessionNumber": [f"{padded}-10-{item:06d}" for item in range(accessions)],
        "filingDate": ["2010-03-01"] * accessions,
        "form": ["10-K"] * accessions,
    }


def entries(
    members: int,
    *,
    filings: int = 2,
    shards: int = 0,
    share_every: int = 0,
    malformed: int = 0,
    duplicate: bool = False,
    shard_first: bool = True,
    junk: int = 0,
    unknown: int = 0,
    shared_alias: bool = True,
) -> list[tuple[str, dict[str, Any]]]:
    """Build the archive's member sequence.

    ``shard_first`` writes each shard **before** the document that declares it, which is the
    ordering accepted Decision 129 §7 exists to survive and the ordering a chunked run has to
    survive twice: once inside a chunk and once across the region barrier.

    ``shared_alias`` gives every registrant one alias value in common, which makes the accepted
    candidate-lineage derivation emit a pair for every pair of registrants. That is the right
    stress for a correctness proof and exactly the wrong shape for a performance measurement --
    it is quadratic in the member count in the monolithic run and the chunked one alike -- so
    the scaling experiment turns it off and says so.
    """
    built: list[tuple[str, dict[str, Any]]] = []
    for index in range(members):
        # `duplicate` gives the LAST member the FIRST member's registrant and repeats one of its
        # accessions, which is the case a stream cannot decide locally: the repeat is detected
        # inside the last document, and the run-level verdict it produces applies to a record the
        # first member contributed and that was written long before. Across a partition, those
        # two members are in different chunks.
        repeats_first = duplicate and index == members - 1
        cik = 1 if repeats_first else index + 1
        has_shard = index < shards
        declares = (
            (f"CIK{cik:010d}-submissions-001.json",) if has_shard and not repeats_first else ()
        )
        if has_shard and shard_first:
            built.append(shard_document(cik))
        built.append(
            primary_document(
                cik,
                filings=filings,
                declares=declares,
                share=bool(share_every) and index % share_every == 0,
                drop_filings=index >= members - malformed,
                duplicate_first=duplicate and index == members - 1,
                junk_accession=bool(junk) and index % max(junk, 1) == 1,
                unknown_field=bool(unknown) and index % max(unknown, 1) == 0,
                shared_alias=shared_alias,
                member_name=f"CIK{index + 1:010d}.json" if repeats_first else None,
            )
        )
        if has_shard and not shard_first:
            built.append(shard_document(cik))
    return built


def write_archive(path: Path, members: list[tuple[str, dict[str, Any]]]) -> bytes:
    """Write members in exactly the given order; archive order is a variable under test."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, document in members:
            info = zipfile.ZipInfo(name, date_time=ARCHIVE_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, json.dumps(document, sort_keys=True))
        # A non-JSON member, so the governed-member filter is exercised on every path.
        archive.writestr(
            zipfile.ZipInfo("readme.txt", date_time=ARCHIVE_TIMESTAMP), "not a document"
        )
    return path.read_bytes()


def build_world(root: Path, **kwargs: Any) -> tuple[Path, DataTree]:
    """A disposable catalog and data tree holding one synthetic bulk archive."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    import test_d110_bounded_parse_memory as world  # noqa: PLC0415

    tree = DataTree.from_root(root / "data")
    database = root / "catalog.sqlite3"
    raw = write_archive(tree.data_root / ARCHIVE_RELATIVE, entries(**kwargs))
    world._seed_catalog(database, tree, raw)
    return database, tree


#: The repository identity every D151 driver records and every consolidation must measure.
#:
#: **One pin, in one place.** It lives in this module rather than in each test module because the
#: drivers are shared: a consolidation test may reach the equivalence module's driver, and a
#: per-module pin would then leave that driver recording the real working checkout while the
#: consolidator measured a temporary one. The reversed-order run found exactly that.
PINNED: RepositoryIdentity | None = None

#: Where that repository is, for the tests that need to move it or make it dirty.
PINNED_ROOT: Path | None = None


def pinned_repository() -> RepositoryIdentity:
    """The pinned identity, or a refusal.

    Raises:
        AssertionError: no test pinned a repository, so a driver would silently record the real
            working checkout's identity and a consolidation would refuse against it.
    """
    assert PINNED is not None, "no repository is pinned; call pin_repository in an autouse fixture"
    return PINNED


def unpin_repository() -> None:
    """Clear the pin at a fixture's teardown, beside undoing its monkeypatch."""
    global PINNED, PINNED_ROOT  # noqa: PLW0603 - the module-scoped pin this module owns
    PINNED = None
    PINNED_ROOT = None


def pin_repository(root: Path, monkeypatch: pytest.MonkeyPatch) -> RepositoryIdentity:
    """Make a REAL, clean Git repository the one the accepted identity mechanism reports.

    **This is the repository's own accepted test seam, not a bypass.** Exactly one name is
    redirected -- ``running_repository_identity``, which answers *which* repository is executing
    -- and it is redirected to :func:`repository_identity_at` over a repository that genuinely
    exists on disk, with a genuine commit and a genuine ``git status``. Every predicate downstream
    of it is the accepted one, unmodified: ``require_clean_running_repository`` still runs, still
    shells out to Git, and still refuses a dirty tree. That is what makes "a dirty repository
    refuses" a real proof here rather than a mocked one.

    It is needed because the suite runs from a working checkout that is, by definition, dirty
    while the change under test is being written.
    """
    root.mkdir(parents=True)
    for argv in (
        ["init", "--quiet", "--initial-branch=main"],
        ["config", "user.email", "d151@example.invalid"],
        ["config", "user.name", "D151"],
    ):
        subprocess.run(["git", "-C", str(root), *argv], check=True, capture_output=True)  # noqa: S603, S607
    (root / "governing.txt").write_text("the chunked-F0 governing revision\n", encoding="utf-8")
    subprocess.run(  # noqa: S603, S607
        ["git", "-C", str(root), "add", "governing.txt"], check=True, capture_output=True
    )
    subprocess.run(  # noqa: S603, S607
        ["git", "-C", str(root), "commit", "--quiet", "-m", "governing revision"],
        check=True,
        capture_output=True,
    )
    monkeypatch.setattr(
        repository_identity, "running_repository_identity", lambda: repository_identity_at(root)
    )
    identity = repository_identity.require_clean_running_repository()
    assert identity.clean
    global PINNED, PINNED_ROOT  # noqa: PLW0603 - the module-scoped pin this module owns
    PINNED, PINNED_ROOT = identity, root
    return identity


def observation_of(tree: DataTree, database: Path) -> Any:
    """The one stored bulk observation this world carries."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    import test_d110_bounded_parse_memory as world  # noqa: PLC0415

    return world._observation(tree, database)


def archive_of(tree: DataTree) -> Path:
    """The synthetic archive's path inside one data tree."""
    return tree.data_root / ARCHIVE_RELATIVE


def build_plan(tree: DataTree, database: Path, *, chunk_members: int) -> cp.ChunkPlan:
    """One chunk plan over this world's archive, at a caller-chosen partition size."""
    observation = observation_of(tree, database)
    return cp.build_chunk_plan(
        archive_path=archive_of(tree),
        source_instance_id=INSTANCE,
        source_observation_id=OBSERVATION,
        source_id=SOURCE_ID,
        source_sha256=observation.logical_sha256,
        source_byte_length=observation.content_size_bytes,
        chunk_members=chunk_members,
    )


@pytest.fixture
def world(tmp_path: Path) -> tuple[Path, DataTree]:
    """A world with shards, a co-filed accession, and a non-JSON member.

    Nine governed members -- six primaries and three shards -- which is exactly
    :data:`~disclosure_drift.m3.chunk_plan.SINGLE_PASS_CHUNK_CAP`. That is deliberate: the
    smallest partition this plan can express, one member per chunk, sits **on** the D151-C3 §11
    single-pass cap rather than below it, so every sweep over ``chunk_members=1`` is a run at the
    architectural boundary rather than a comfortable distance inside it.
    """
    return build_world(tmp_path, members=6, filings=2, shards=3, share_every=2)


# ==========================================================================
# The canonical member ordering
# ==========================================================================
def test_the_canonical_population_is_exactly_the_accepted_traversals(tmp_path: Path) -> None:
    """The plan partitions the same members F0 absorbs -- proved, not assumed."""
    _database, tree = build_world(tmp_path, members=6, filings=2, shards=3)
    archive = archive_of(tree)
    sequence = cp.canonical_member_sequence(archive)
    traversed = {
        member.member_index: member.name for member in iter_members(archive, name_suffix=".json")
    }
    assert {member.archive_ordinal: member.member_name for member in sequence} == traversed


def test_the_canonical_order_is_primaries_then_shards(tmp_path: Path) -> None:
    """Accepted Decision 129 §7 defers every shard, so F0 absorbs primaries first."""
    _database, tree = build_world(tmp_path, members=6, filings=2, shards=6, shard_first=True)
    sequence = cp.canonical_member_sequence(archive_of(tree))
    regions = [member.region for member in sequence]
    assert regions == [cp.REGION_PRIMARY] * 6 + [cp.REGION_SHARD] * 6
    assert [member.canonical_position for member in sequence] == list(range(12))
    primaries = [member for member in sequence if member.region == cp.REGION_PRIMARY]
    shards = [member for member in sequence if member.region == cp.REGION_SHARD]
    # Within each region, archive order is preserved exactly.
    assert primaries == sorted(primaries, key=lambda item: item.archive_ordinal)
    assert shards == sorted(shards, key=lambda item: item.archive_ordinal)
    # The archive really does interleave them, so the permutation is not a no-op.
    assert [member.archive_ordinal for member in shards] != sorted(
        member.archive_ordinal for member in primaries
    )


def test_the_ordering_digest_moves_when_a_member_moves(tmp_path: Path) -> None:
    """A27: a stale plan is refused because the ordering identity is content-derived."""
    left = tmp_path / "left.zip"
    right = tmp_path / "right.zip"
    write_archive(left, entries(4, filings=2, shards=2))
    reordered = entries(4, filings=2, shards=2)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    write_archive(right, reordered)
    assert cp.compute_member_order_digest(
        cp.canonical_member_sequence(left)
    ) != cp.compute_member_order_digest(cp.canonical_member_sequence(right))


def test_a_shard_shaped_name_beneath_a_directory_is_refused(tmp_path: Path) -> None:
    """A44/A45: a member whose *basename* is shard-shaped cannot be bound to a registrant."""
    path = tmp_path / "hostile.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("CIK0000000001.json", "{}")
        archive.writestr("nested/CIK0000000002-submissions-001.json", "{}")
    with pytest.raises(OfflineParseError, match="beneath a directory prefix"):
        cp.canonical_member_sequence(path)


def test_a_traversal_member_name_is_refused(tmp_path: Path) -> None:
    """A44: the accepted name-level archive defences apply to the plan's own read."""
    path = tmp_path / "escape.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../escape.json", "{}")
    with pytest.raises(ArchiveDefenceError):
        cp.canonical_member_sequence(path)


def test_a_colliding_member_name_is_refused(tmp_path: Path) -> None:
    """A05: two members that canonicalize alike are refused rather than deduplicated."""
    path = tmp_path / "collide.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("CIK0000000001.json", "{}")
        archive.writestr("./CIK0000000001.json", "{}")
    with pytest.raises(ArchiveDefenceError):
        cp.canonical_member_sequence(path)


def test_a_corrupt_archive_is_refused_rather_than_read_as_empty(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.zip"
    path.write_bytes(b"not a zip file at all")
    with pytest.raises(ArchiveDefenceError, match="corrupt"):
        cp.canonical_member_sequence(path)


# ==========================================================================
# C01-C05: plan identity and coverage
# ==========================================================================
def test_c01_same_source_and_size_produce_the_same_plan(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    first = build_plan(tree, database, chunk_members=3)
    second = build_plan(tree, database, chunk_members=3)
    assert first == second
    assert first.plan_digest == second.plan_digest


def test_c02_a_different_size_is_a_different_plan_identity(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    digests = {build_plan(tree, database, chunk_members=n).plan_digest for n in (1, 2, 3, 4)}
    assert len(digests) == 4


def test_a38_a_different_size_partitions_the_same_members(world: tuple[Path, DataTree]) -> None:
    """A38: N changes the partition, never the population or the ordering."""
    database, tree = world
    plans = [build_plan(tree, database, chunk_members=n) for n in (1, 2, 3, 4, 1000)]
    assert len({plan.member_order_digest for plan in plans}) == 1
    assert len({plan.total_members for plan in plans}) == 1


@pytest.mark.parametrize("size", [1, 2, 3, 5, 7, 1000])
def test_c03_c04_c05_a_partition_covers_the_source_exactly_once(
    world: tuple[Path, DataTree], size: int
) -> None:
    """C03 no gaps, C04 no overlap, C05 exact coverage once -- at every partition size."""
    database, tree = world
    plan = build_plan(tree, database, chunk_members=size)
    covered: list[int] = []
    for bounds in plan.chunks:
        covered.extend(range(bounds.start, bounds.end))
    assert covered == list(range(plan.total_members))
    assert plan.chunk_count == len(plan.chunks)


def test_no_chunk_straddles_the_region_boundary(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    for size in (1, 2, 3, 5, 1000):
        plan = build_plan(tree, database, chunk_members=size)
        for bounds in plan.chunks:
            region = cp.REGION_SHARD if bounds.start >= plan.primary_members else cp.REGION_PRIMARY
            assert bounds.region == region
            if region == cp.REGION_PRIMARY:
                assert bounds.end <= plan.primary_members


# ==========================================================================
# C06-C07 and the adversarial plan matrix
# ==========================================================================
def test_c06_a_different_artifact_is_refused(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    with pytest.raises(ChunkPlanError, match="SHA-256"):
        cp.verify_source_identity(
            plan, observed_sha256="0" * 64, observed_byte_length=plan.source_byte_length
        )
    with pytest.raises(ChunkPlanError, match="bytes where the chunk plan records"):
        cp.verify_source_identity(
            plan,
            observed_sha256=plan.source_sha256,
            observed_byte_length=plan.source_byte_length + 1,
        )


def test_c07_a_plan_whose_digest_does_not_describe_it_is_refused(
    world: tuple[Path, DataTree],
) -> None:
    """A07: the stored digest is recomputed and compared, never trusted."""
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    record = dict(plan.as_record())
    record["plan_digest"] = "0" * 64
    with pytest.raises(ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)


def test_a_plan_carrying_another_contract_is_refused(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    record = dict(build_plan(tree, database, chunk_members=3).as_record())
    record["contract"] = "someone-elses-plan/9"
    with pytest.raises(ChunkPlanError, match="never adopts another shape"):
        cp.ChunkPlan.from_record(record)


def test_a_plan_round_trips_through_its_own_record(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    assert cp.ChunkPlan.from_record(json.loads(json.dumps(dict(plan.as_record())))) == plan


def _resealed(plan: cp.ChunkPlan, chunks: tuple[ChunkBounds, ...]) -> dict[str, object]:
    """A tampered plan whose digest is recomputed, so only the coverage check can catch it."""
    tampered = replace(plan, chunks=chunks, chunk_count=len(chunks), plan_digest="")
    record = dict(tampered.as_record())
    record["plan_digest"] = cp._plan_digest(tampered)
    return record


def test_a01_a_shifted_bound_is_refused(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    shifted = list(plan.chunks)
    shifted[0] = replace(shifted[0], end=shifted[0].end + 1)
    with pytest.raises(ChunkPlanError, match="overlap|gap"):
        cp.ChunkPlan.from_record(_resealed(plan, tuple(shifted)))


def test_a02_a_gap_is_refused(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    with pytest.raises(ChunkPlanError, match="gap"):
        cp.ChunkPlan.from_record(_resealed(plan, plan.chunks[:1] + plan.chunks[2:]))


def test_a03_an_overlap_is_refused(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    overlapping = list(plan.chunks)
    overlapping[1] = replace(overlapping[1], start=overlapping[1].start - 1)
    with pytest.raises(ChunkPlanError, match="overlap"):
        cp.ChunkPlan.from_record(_resealed(plan, tuple(overlapping)))


def test_a04_a_duplicate_chunk_id_is_refused(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    duplicated = list(plan.chunks)
    duplicated[1] = replace(duplicated[1], chunk_id=duplicated[0].chunk_id)
    with pytest.raises(ChunkPlanError, match="repeats chunk identifier"):
        cp.ChunkPlan.from_record(_resealed(plan, tuple(duplicated)))


def test_a_short_partition_is_refused(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    with pytest.raises(ChunkPlanError, match="covers"):
        cp.ChunkPlan.from_record(_resealed(plan, plan.chunks[:-1]))


def test_an_empty_interval_is_refused(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    empty = (ChunkBounds(chunk_id="chunk-9999", region=cp.REGION_PRIMARY, start=0, end=0),)
    with pytest.raises(ChunkPlanError, match="empty or inverted"):
        cp.ChunkPlan.from_record(_resealed(plan, empty + plan.chunks))


def test_a_chunk_straddling_the_region_boundary_is_refused(
    world: tuple[Path, DataTree],
) -> None:
    """The region boundary is always a chunk boundary, and a plan that crosses it is refused.

    A chunk holding the last primary documents and the first shards would have to resolve a
    parent map that cannot be complete until every primary document has been read -- including
    the ones in later chunks. The condition is refused at plan level, before any chunk starts.
    """
    database, tree = world
    plan = build_plan(tree, database, chunk_members=10_000)
    assert len(plan.chunks) == 2
    straddling = (
        ChunkBounds(
            chunk_id="chunk-0000",
            region=cp.REGION_PRIMARY,
            start=0,
            end=plan.primary_members + 1,
        ),
        ChunkBounds(
            chunk_id="chunk-0001",
            region=cp.REGION_SHARD,
            start=plan.primary_members + 1,
            end=plan.total_members,
        ),
    )
    with pytest.raises(ChunkPlanError, match="straddles the primary/shard boundary"):
        cp.ChunkPlan.from_record(_resealed(plan, straddling))


def test_a_shard_chunk_may_not_precede_a_primary_chunk(world: tuple[Path, DataTree]) -> None:
    """The region barrier is a plan property, not an execution convention."""
    database, tree = world
    plan = build_plan(tree, database, chunk_members=1000)
    reordered = (plan.chunks[1], plan.chunks[0])
    with pytest.raises(ChunkPlanError):
        cp.ChunkPlan.from_record(_resealed(plan, reordered))


# ==========================================================================
# Chunk resolution
# ==========================================================================
def test_c08_a_chunk_resolves_only_its_own_ordinal_range(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    archive = archive_of(tree)
    seen: list[str] = []
    for bounds in plan.chunks:
        members = cp.resolve_chunk_members(plan, archive, bounds.chunk_id)
        assert [member.canonical_position for member in members] == list(
            range(bounds.start, bounds.end)
        )
        seen.extend(member.member_name for member in members)
    assert len(seen) == len(set(seen)) == plan.total_members


def test_a_chunk_over_a_moved_ordering_is_refused(tmp_path: Path) -> None:
    """C06/A27 at the chunk's own admission: the ordering digest is re-derived, not trusted."""
    database, tree = build_world(tmp_path, members=6, filings=2, shards=2)
    plan = build_plan(tree, database, chunk_members=3)
    other = tmp_path / "other.zip"
    write_archive(other, entries(7, filings=2, shards=2))
    with pytest.raises(ChunkPlanError, match="canonical member ordering digest"):
        cp.resolve_chunk_members(plan, other, plan.chunks[0].chunk_id)


def test_an_unknown_chunk_id_is_refused(world: tuple[Path, DataTree]) -> None:
    database, tree = world
    plan = build_plan(tree, database, chunk_members=3)
    with pytest.raises(ChunkPlanError, match="is not in this plan"):
        cp.chunk_by_id(plan, "chunk-9999")


# ==========================================================================
# Closed values
# ==========================================================================
def test_the_production_chunk_size_is_closed() -> None:
    """D151-C1 §5 and §28: C1 measures the sizing model and freezes no N."""
    assert cp.PRODUCTION_CHUNK_MEMBERS is None
    with pytest.raises(ChunkPlanError, match="never defaulted"):
        cp.production_chunk_members()


def test_a_non_chunkable_source_is_refused(tmp_path: Path) -> None:
    _database, tree = build_world(tmp_path, members=3, filings=1)
    with pytest.raises(ChunkPlanError, match="not a chunkable governed source"):
        cp.build_chunk_plan(
            archive_path=archive_of(tree),
            source_instance_id=INSTANCE,
            source_observation_id=OBSERVATION,
            source_id="sec_full_index_company",
            source_sha256="0" * 64,
            source_byte_length=1,
            chunk_members=2,
        )


@pytest.mark.parametrize("size", [0, -1])
def test_a_non_positive_chunk_size_is_refused(tmp_path: Path, size: int) -> None:
    database, tree = build_world(tmp_path, members=3, filings=1)
    with pytest.raises(ChunkPlanError, match="positive chunk size"):
        build_plan(tree, database, chunk_members=size)


def test_an_archive_with_no_governed_member_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "empty.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("readme.txt", "nothing here")
    with pytest.raises(ChunkPlanError, match="no governed"):
        cp.build_chunk_plan(
            archive_path=path,
            source_instance_id=INSTANCE,
            source_observation_id=OBSERVATION,
            source_id=SOURCE_ID,
            source_sha256="0" * 64,
            source_byte_length=path.stat().st_size,
            chunk_members=2,
        )
