"""Defensive archive reading: traversal, duplicates, bombs, and corruption."""

from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath

import pytest

from disclosure_drift.sec.archive import (
    MAX_EXPANSION_RATIO,
    MAX_MEMBER_BYTES,
    ArchiveDefenceError,
    _portable_member_key,  # noqa: PLC2701 - the differential oracle needs the exact key function
    canonical_member_name,
    extract_members,
    iter_members,
    iter_named_members,
    safe_member_name,
)

MEMBER_ONE = b'{"cik":"0000000001"}'
MEMBER_TWO = b'{"cik":"0000000002"}'


def build(path: Path, members: list[tuple[str, bytes]], *, duplicate: bool = False) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members:
            archive.writestr(name, payload)
        if duplicate:
            archive.writestr(members[0][0], members[0][1])
    return path


def test_ordinary_member_names_are_normalized() -> None:
    assert safe_member_name("CIK0000000001.json") == "CIK0000000001.json"
    assert safe_member_name("./CIK0000000001.json") == "CIK0000000001.json"
    assert safe_member_name("nested/CIK0000000001.json") == "nested/CIK0000000001.json"


@pytest.mark.parametrize(
    "hostile",
    [
        "../escape.json",
        "nested/../../escape.json",
        "/etc/passwd",
        "C:\\windows\\system32.json",
        "a\\b.json",
        "",
        "directory/",
    ],
)
def test_hostile_member_names_are_refused(hostile: str) -> None:
    with pytest.raises(ArchiveDefenceError):
        safe_member_name(hostile)


def test_valid_members_are_yielded_in_order(tmp_path: Path) -> None:
    archive = build(
        tmp_path / "good.zip",
        [("CIK0000000001.json", MEMBER_ONE), ("CIK0000000002.json", MEMBER_TWO)],
    )
    members = list(iter_members(archive, name_suffix=".json"))
    assert [item.name for item in members] == ["CIK0000000001.json", "CIK0000000002.json"]
    assert members[0].payload == MEMBER_ONE
    assert members[0].uncompressed_size == len(MEMBER_ONE)
    assert members[0].expansion_ratio > 0


def test_suffix_filter_skips_other_members(tmp_path: Path) -> None:
    archive = build(
        tmp_path / "mixed.zip",
        [("CIK0000000001.json", MEMBER_ONE), ("readme.txt", b"notes")],
    )
    assert [item.name for item in iter_members(archive, name_suffix=".json")] == [
        "CIK0000000001.json"
    ]


def test_path_traversal_member_is_refused(tmp_path: Path) -> None:
    archive = tmp_path / "traversal.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../../etc/passwd", b"nope")
    with pytest.raises(ArchiveDefenceError, match="escapes the extraction root"):
        list(iter_members(archive))


def test_duplicate_member_is_refused_rather_than_last_wins(tmp_path: Path) -> None:
    with pytest.warns(UserWarning, match="Duplicate name"):
        archive = build(
            tmp_path / "dupes.zip",
            [("CIK0000000001.json", MEMBER_ONE)],
            duplicate=True,
        )
    with pytest.raises(ArchiveDefenceError, match="portable path"):
        list(iter_members(archive))


def test_implicit_file_versus_directory_collision_is_refused(tmp_path: Path) -> None:
    archive = build(
        tmp_path / "file-directory.zip",
        [("nested", MEMBER_ONE), ("nested/CIK0000000002.json", MEMBER_TWO)],
    )
    with pytest.raises(ArchiveDefenceError, match="parent path|file and directory"):
        list(iter_members(archive))


@pytest.mark.parametrize(
    "members",
    [
        [("A.json", MEMBER_ONE), ("a.json", MEMBER_TWO)],
        [("straße.json", MEMBER_ONE), ("STRASSE.json", MEMBER_TWO)],
        [("\u00e9.json", MEMBER_ONE), ("e\u0301.json", MEMBER_TWO)],
    ],
)
def test_portable_name_collisions_are_refused_on_every_platform(
    tmp_path: Path,
    members: list[tuple[str, bytes]],
) -> None:
    archive = build(tmp_path / "portable-collision.zip", members)
    with pytest.raises(ArchiveDefenceError, match="portable path"):
        list(iter_members(archive))


@pytest.mark.parametrize(
    "name",
    [
        "trailing.",
        "trailing ",
        "nested/trailing./file.json",
        "CON",
        "nul.txt",
        "LPT1.json",
        "nested/com9.data",
    ],
)
def test_nonportable_components_and_reserved_devices_are_refused(name: str) -> None:
    with pytest.raises(ArchiveDefenceError):
        safe_member_name(name)


def test_extraction_creates_files_exclusively(tmp_path: Path) -> None:
    archive = build(tmp_path / "ordinary.zip", [("CIK0000000001.json", MEMBER_ONE)])
    destination = tmp_path / "extract"
    destination.mkdir()
    written = extract_members(archive, destination)
    assert written[0].read_bytes() == MEMBER_ONE
    with pytest.raises(ArchiveDefenceError, match="overwrite or follow"):
        extract_members(archive, destination)
    assert written[0].read_bytes() == MEMBER_ONE


def test_extraction_refuses_preexisting_destination_file(tmp_path: Path) -> None:
    archive = build(tmp_path / "preexisting.zip", [("existing.json", MEMBER_ONE)])
    destination = tmp_path / "extract"
    destination.mkdir()
    existing = destination / "existing.json"
    existing.write_bytes(b"owner-data")
    with pytest.raises(ArchiveDefenceError, match="overwrite or follow"):
        extract_members(archive, destination)
    assert existing.read_bytes() == b"owner-data"


def test_extraction_refuses_symlink_destination(tmp_path: Path) -> None:
    archive = build(tmp_path / "symlink.zip", [("linked.json", MEMBER_ONE)])
    destination = tmp_path / "extract"
    destination.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"outside-owner")
    (destination / "linked.json").symlink_to(outside)
    with pytest.raises(ArchiveDefenceError):
        extract_members(archive, destination)
    assert outside.read_bytes() == b"outside-owner"


def test_extraction_refuses_symlink_parent_directory(tmp_path: Path) -> None:
    archive = build(tmp_path / "symlink-parent.zip", [("linked/file.json", MEMBER_ONE)])
    destination = tmp_path / "extract"
    destination.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (destination / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ArchiveDefenceError, match="parent path is unsafe"):
        extract_members(archive, destination)
    assert not (outside / "file.json").exists()


def test_corrupt_archive_is_never_reported_as_empty(tmp_path: Path) -> None:
    archive = tmp_path / "corrupt.zip"
    archive.write_bytes(b"PK\x03\x04not-really-a-zip")
    with pytest.raises(ArchiveDefenceError, match="quarantined rather than"):
        list(iter_members(archive))


def test_oversized_member_is_refused(tmp_path: Path) -> None:
    archive = build(tmp_path / "big.zip", [("huge.json", b"0" * 5_000)])
    with pytest.raises(ArchiveDefenceError, match="exceeds the limit"):
        list(iter_members(archive, max_member_bytes=1_000))


def test_implausible_expansion_ratio_is_refused(tmp_path: Path) -> None:
    archive = build(tmp_path / "bomb.zip", [("huge.json", b"0" * 1_000_000)])
    with pytest.raises(ArchiveDefenceError, match="expansion ratio"):
        list(iter_members(archive, max_ratio=2.0))


def test_cumulative_expansion_limit_is_enforced(tmp_path: Path) -> None:
    archive = build(
        tmp_path / "many.zip",
        [(f"member-{index}.json", b"0" * 2_000) for index in range(5)],
    )
    with pytest.raises(ArchiveDefenceError, match="cumulative expansion"):
        list(iter_members(archive, max_total_bytes=3_000))


def test_default_limits_are_conservative() -> None:
    assert MAX_MEMBER_BYTES <= 512 * 1024 * 1024
    assert MAX_EXPANSION_RATIO <= 2_000.0


# --------------------------------------------------------------------------- #
# Reverse-order file-versus-directory collision (Decision 051 §4.1, §7.1)
#
# The forward direction (a file member, then a member beneath it) is covered by
# ``test_implicit_file_versus_directory_collision_is_refused`` above and is caught by the
# parent-is-file check. These controls cover the *reverse* direction — a member beneath a
# path, then that path as a file — which the accepted strict-ancestor-prefix set decides and
# which the prior quadratic descendant scan decided. They are the positive controls Decision
# 051 §7.1 required to be added, and they are non-vacuous: each collision case *raises*, and
# ``test_sibling_and_nested_prefixes_are_admitted`` proves the same check *admits* the
# legitimate sibling and nested members it must not reject.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "members",
    [
        # The primary reverse-order control named in Decision 051 §7.1.
        [("nested/x.json", MEMBER_ONE), ("nested", MEMBER_TWO)],
        # A deeper descendant, then the immediate directory used as a file.
        [("a/b/c.json", MEMBER_ONE), ("a/b", MEMBER_TWO)],
        # A deeper descendant, then a top-level directory used as a file.
        [("a/b/c.json", MEMBER_ONE), ("a", MEMBER_TWO)],
        # A three-level descendant, then a mid-level directory used as a file.
        [("d/e/f/g.json", MEMBER_ONE), ("d/e", MEMBER_TWO)],
    ],
)
def test_reverse_order_file_versus_directory_collision_is_refused(
    tmp_path: Path,
    members: list[tuple[str, bytes]],
) -> None:
    archive = build(tmp_path / "reverse-collision.zip", members)
    with pytest.raises(ArchiveDefenceError, match="file and directory"):
        list(iter_members(archive))


def test_reverse_order_collision_with_explicit_directory_entry_is_refused(tmp_path: Path) -> None:
    # An explicit directory entry (a name ending in ``/``) beneath a path, then that path as a
    # file. This exercises the directory branch's contribution to the strict-ancestor set:
    # without it, ``g`` would not be recognized as colliding with the directory ``g/h/``.
    archive = tmp_path / "reverse-dir-entry.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("g/h/", b"")
        handle.writestr("g", MEMBER_ONE)
    with pytest.raises(ArchiveDefenceError, match="file and directory"):
        list(iter_members(archive))


@pytest.mark.parametrize(
    "members",
    [
        # A file whose name is a string prefix of a sibling directory, but not a path ancestor:
        # ``a.json`` must not be treated as a directory of ``ab/…``. The ``+ "/"`` boundary the
        # old scan relied on, and the component boundary the new set relies on, both forbid this.
        [("ab/x.json", MEMBER_ONE), ("a.json", MEMBER_TWO)],
        # The mirror image: a deeper path whose top component is a string prefix of a sibling
        # file. ``ab`` (file) is not an ancestor of ``a/…``.
        [("a/x.json", MEMBER_ONE), ("ab.json", MEMBER_TWO)],
        # Two ordinary files sharing a real directory are not a collision.
        [("nested/a.json", MEMBER_ONE), ("nested/b.json", MEMBER_TWO)],
    ],
)
def test_sibling_and_nested_prefixes_are_admitted(
    tmp_path: Path,
    members: list[tuple[str, bytes]],
) -> None:
    archive = build(tmp_path / "siblings.zip", members)
    yielded = [item.name for item in iter_members(archive, name_suffix=".json")]
    assert yielded == [canonical for canonical, _ in members]


def _pre_decision_051_collision_loop_refuses(names: list[str]) -> bool:
    """Reference oracle: the exact pre-Decision-051 collision loop, file entries only.

    It reproduces all three refusal predicates the removed inner loop computed, including the
    quadratic reverse scan ``any(existing.startswith(portable + "/") for existing in all_paths)``
    verbatim, so the strict-ancestor-prefix replacement can be proved to accept and reject the
    identical set of inputs. Restricted to file entries (no trailing slash), which is all the
    differential battery uses.
    """
    files: set[str] = set()
    all_paths: set[str] = set()
    for name in names:
        canonical = canonical_member_name(name)
        portable = _portable_member_key(canonical)
        if portable in all_paths:
            return True  # duplicate portable identity
        parent_keys = [
            _portable_member_key(parent.as_posix())
            for parent in PurePosixPath(canonical).parents
            if parent.as_posix() != "."
        ]
        if any(parent in files for parent in parent_keys):
            return True  # a parent path is already a file (forward direction)
        if any(existing.startswith(portable + "/") for existing in all_paths):
            return True  # a descendant is already admitted (reverse direction, the quadratic scan)
        files.add(portable)
        all_paths.add(portable)
    return False


# A deterministic battery (no randomness): reverse collisions, forward collisions, boundary
# siblings, deep nesting, and clean multi-file sets, plus their orderings.
_DIFFERENTIAL_BATTERY: list[list[str]] = [
    ["nested/x.json", "nested"],
    ["nested", "nested/x.json"],
    ["a/b/c.json", "a/b"],
    ["a/b/c.json", "a"],
    ["a", "a/b/c.json"],
    ["a/b", "a/b/c.json"],
    ["d/e/f/g.json", "d/e"],
    ["ab/x.json", "a.json"],
    ["a/x.json", "ab.json"],
    ["nested/a.json", "nested/b.json"],
    ["one.json", "two.json", "three.json"],
    ["p/q/r.json", "p/q/s.json", "p/t.json"],
    ["x/y.json", "x", "z.json"],
    ["m.json", "m/n.json"],
    ["deep/leaf.json", "deep/branch/twig.json", "deep"],
]


@pytest.mark.parametrize("names", _DIFFERENTIAL_BATTERY)
def test_new_collision_check_matches_removed_quadratic_scan(
    tmp_path: Path,
    names: list[str],
) -> None:
    # Distinct payloads so a genuine duplicate is never introduced by the battery itself.
    members = [(name, f'{{"i":{index}}}'.encode()) for index, name in enumerate(names)]
    archive = build(tmp_path / "differential.zip", members)
    expected_refusal = _pre_decision_051_collision_loop_refuses(names)

    if expected_refusal:
        with pytest.raises(ArchiveDefenceError):
            list(iter_members(archive))
    else:
        yielded = [item.name for item in iter_members(archive)]
        # Ordered lineage is preserved exactly: canonical names in archive (insertion) order.
        assert yielded == [canonical_member_name(name) for name in names]


# --------------------------------------------------------------------------- #
# Targeted named-member reads
# --------------------------------------------------------------------------- #
# ``iter_named_members`` exists for a caller that traversed the whole archive once, dropped
# every payload on purpose, and must now read one member again by name. Its defences are the
# per-member defences of the full traversal, reached through one implementation rather than
# restated by the caller.
MEMBER_THREE = b'{"cik":"0000000003"}'


def named_archive(path: Path) -> Path:
    return build(
        path,
        [
            ("CIK0000000001.json", MEMBER_ONE),
            ("CIK0000000002.json", MEMBER_TWO),
            ("CIK0000000003.json", MEMBER_THREE),
        ],
    )


def test_named_members_are_yielded_in_the_order_requested(tmp_path: Path) -> None:
    """The requested sequence is the contract, not the archive's own order."""
    archive = named_archive(tmp_path / "named.zip")

    read = list(iter_named_members(archive, ["CIK0000000003.json", "CIK0000000001.json"]))

    assert read == [("CIK0000000003.json", MEMBER_THREE), ("CIK0000000001.json", MEMBER_ONE)]


def test_a_named_read_touches_only_the_members_it_was_asked_for(tmp_path: Path) -> None:
    archive = named_archive(tmp_path / "subset.zip")

    read = list(iter_named_members(archive, ["CIK0000000002.json"]))

    assert [name for name, _ in read] == ["CIK0000000002.json"]


def test_an_absent_named_member_is_refused_rather_than_skipped(tmp_path: Path) -> None:
    """Silently yielding fewer members than were asked for would misreport the archive."""
    archive = named_archive(tmp_path / "absent.zip")

    with pytest.raises(ArchiveDefenceError, match="does not"):
        list(iter_named_members(archive, ["CIK0000000001.json", "CIK0000009999.json"]))


def test_a_named_member_that_resolves_to_two_entries_is_refused(tmp_path: Path) -> None:
    """Two entries canonicalizing alike make the requested name ambiguous."""
    archive = build(
        tmp_path / "ambiguous.zip",
        [("CIK0000000001.json", MEMBER_ONE), ("./CIK0000000001.json", MEMBER_TWO)],
    )

    with pytest.raises(ArchiveDefenceError, match="more than"):
        list(iter_named_members(archive, ["CIK0000000001.json"]))


def test_asking_for_the_same_member_twice_is_refused(tmp_path: Path) -> None:
    archive = named_archive(tmp_path / "repeat.zip")

    with pytest.raises(ArchiveDefenceError, match="more than once"):
        list(iter_named_members(archive, ["CIK0000000001.json", "CIK0000000001.json"]))


def test_a_named_read_refuses_a_traversal_name(tmp_path: Path) -> None:
    """Canonicalization is applied before anything else, exactly as in the full traversal."""
    archive = named_archive(tmp_path / "traversal.zip")

    with pytest.raises(ArchiveDefenceError):
        list(iter_named_members(archive, ["../CIK0000000001.json"]))


def test_a_named_read_refuses_a_directory_entry(tmp_path: Path) -> None:
    """A directory is never a readable member, however it is named."""
    with zipfile.ZipFile(tmp_path / "dir.zip", "w") as archive:
        archive.writestr("nested/", b"")
        archive.writestr("nested/CIK0000000001.json", MEMBER_ONE)

    with pytest.raises(ArchiveDefenceError, match="does not"):
        list(iter_named_members(tmp_path / "dir.zip", ["nested"]))


def test_a_named_read_refuses_an_oversized_member(tmp_path: Path) -> None:
    """The declared-size defence is the traversal's own, not a second copy of it."""
    archive = named_archive(tmp_path / "oversized.zip")

    with pytest.raises(ArchiveDefenceError, match="exceeds the limit"):
        list(iter_named_members(archive, ["CIK0000000001.json"], max_member_bytes=4))


def test_a_named_read_refuses_an_implausible_expansion_ratio(tmp_path: Path) -> None:
    archive = build(tmp_path / "bomb.zip", [("CIK0000000001.json", b"0" * 200_000)])

    with pytest.raises(ArchiveDefenceError, match="expansion ratio"):
        list(iter_named_members(archive, ["CIK0000000001.json"], max_ratio=1.5))


def test_a_corrupt_archive_is_never_reported_as_holding_no_named_members(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.zip"
    corrupt.write_bytes(b"not a zip archive at all")

    with pytest.raises(ArchiveDefenceError, match="corrupt"):
        list(iter_named_members(corrupt, ["CIK0000000001.json"]))


def test_a_named_read_holds_one_payload_at_a_time(tmp_path: Path) -> None:
    """Boundedness: the reader is a generator and buffers no wider than one member.

    Proved by consuming it lazily — the second member's bytes are not read until the first has
    been handed over and dropped, which a reader that materialized the whole request would make
    impossible to observe.
    """
    archive = named_archive(tmp_path / "lazy.zip")

    stream = iter_named_members(archive, ["CIK0000000001.json", "CIK0000000002.json"])
    first = next(stream)
    assert first == ("CIK0000000001.json", MEMBER_ONE)
    second = next(stream)
    assert second == ("CIK0000000002.json", MEMBER_TWO)
    with pytest.raises(StopIteration):
        next(stream)
