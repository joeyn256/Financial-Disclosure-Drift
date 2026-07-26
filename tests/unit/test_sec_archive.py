"""Defensive archive reading: traversal, duplicates, bombs, and corruption."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from disclosure_drift.sec.archive import (
    MAX_EXPANSION_RATIO,
    MAX_MEMBER_BYTES,
    ArchiveDefenceError,
    extract_members,
    iter_members,
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
