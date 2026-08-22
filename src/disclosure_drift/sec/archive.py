"""Defensive reading of official SEC ZIP archives.

The bulk submissions archive is the census's primary source, so archive handling is
treated as hostile input even though the host is official.

Member names are **canonicalized first**, then checked for collisions, then checked
against expansion limits. Canonicalization refuses:

* ``..`` path components and absolute paths;
* Windows drive paths and backslash-separated paths;
* NUL characters and other control characters;
* percent-encoded traversal, which is refused rather than silently decoded;
* Unicode-normalization collisions, so two members cannot canonicalize alike;
* duplicate canonical names such as ``a/../b``, ``./b`` and ``b``;
* file-versus-directory collisions;
* symlink and other non-regular members, detected from archive metadata.

Directory entries are ignored for reading but still participate in collision
checks, so a directory entry cannot mask a file of the same canonical name.

Nothing is extracted to disk by default: members are read from their streams. When
a caller does need files on disk it must supply its own temporary directory, and
:func:`extract_members` never writes outside it. Archive bytes are never replaced by
their extracted contents; :class:`ArchiveMember` carries the lineage needed to tie a
member back to the preserved archive observation.
"""

from __future__ import annotations

import hashlib
import os
import stat
import unicodedata
import zipfile
from collections.abc import Iterator, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

from disclosure_drift.errors import RawObjectIntegrityError

__all__ = [
    "MAX_EXPANSION_RATIO",
    "MAX_MEMBER_BYTES",
    "MAX_MEMBER_COUNT",
    "MAX_TOTAL_EXPANDED_BYTES",
    "ArchiveDefenceError",
    "ArchiveMember",
    "ArchiveReport",
    "canonical_member_name",
    "extract_members",
    "iter_members",
    "iter_named_members",
    "safe_member_name",
]

MAX_MEMBER_BYTES: Final = 512 * 1024 * 1024
MAX_TOTAL_EXPANDED_BYTES: Final = 64 * 1024 * 1024 * 1024
MAX_EXPANSION_RATIO: Final = 2_000.0
MAX_MEMBER_COUNT: Final = 2_000_000
_READ_CHUNK_BYTES: Final = 1024 * 1024
_REASON_INVALID: Final = "RAW_ARCHIVE_INVALID"
_REASON_MEMBER: Final = "RAW_ARCHIVE_MEMBER_REFUSED"
_UNSAFE_CHARACTERS: Final = frozenset({"\x00"})
_PERCENT_TRAVERSAL: Final[tuple[str, ...]] = ("%2e", "%2f", "%5c", "%00")
_RESERVED_DEVICE_NAMES: Final[frozenset[str]] = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{index}" for index in range(1, 10)}
    | {f"lpt{index}" for index in range(1, 10)}
)


class ArchiveDefenceError(RawObjectIntegrityError):
    """Raised when an archive or member violates a defensive rule."""

    def __init__(self, message: str, reason_code: str = _REASON_MEMBER) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class ArchiveMember:
    """One validated archive member, with lineage back to the preserved archive."""

    name: str
    compressed_size: int
    uncompressed_size: int
    payload: bytes
    archive_relative_path: str | None = None
    archive_sha256: str | None = None
    member_index: int = 0

    @property
    def expansion_ratio(self) -> float:
        """Observed expansion ratio, or ``0.0`` when nothing was compressed."""
        if self.compressed_size <= 0:
            return 0.0
        return self.uncompressed_size / self.compressed_size

    @property
    def member_sha256(self) -> str:
        """Hash of this member's decompressed bytes.

        This is the member's *logical content* hash. It is never the transport hash
        of the archive and never the stored hash of the archive object.
        """
        return hashlib.sha256(self.payload).hexdigest()

    def lineage(self) -> dict[str, object]:
        """Deterministic archive-to-member lineage record."""
        return {
            "archive_relative_path": self.archive_relative_path,
            "archive_sha256": self.archive_sha256,
            "member_index": self.member_index,
            "member_name": self.name,
            "member_sha256": self.member_sha256,
            "member_compressed_size_bytes": self.compressed_size,
            "member_uncompressed_size_bytes": self.uncompressed_size,
        }


@dataclass(frozen=True, slots=True)
class ArchiveReport:
    """Accounting for one archive read."""

    members_read: int
    bytes_expanded: int
    directories_seen: int = 0
    refused: tuple[tuple[str, str], ...] = ()

    @property
    def reason_codes(self) -> tuple[str, ...]:
        """Reason codes implied by refusals."""
        return (_REASON_INVALID,) if self.refused else ()


def canonical_member_name(name: str) -> str:
    """Return the canonical form of an archive member name, or refuse it.

    Canonicalization is NFC Unicode normalization plus POSIX path normalization with
    ``.`` segments removed. Anything that could escape an extraction root, collide
    ambiguously, or smuggle an encoded separator is refused rather than repaired.

    Raises:
        ArchiveDefenceError: the name is unusable or hostile.
    """
    if not name:
        message = "refusing archive member with an empty name"
        raise ArchiveDefenceError(message)
    if any(character in name for character in _UNSAFE_CHARACTERS):
        message = f"refusing archive member with a NUL character: {name!r}"
        raise ArchiveDefenceError(message)
    if any(ord(character) < 0x20 for character in name):
        message = f"refusing archive member with a control character: {name!r}"
        raise ArchiveDefenceError(message)
    lowered = name.lower()
    if any(token in lowered for token in _PERCENT_TRAVERSAL):
        message = (
            f"refusing archive member with a percent-encoded path component: {name!r}; "
            "encoded separators are never decoded into a path here"
        )
        raise ArchiveDefenceError(message)
    if "\\" in name:
        message = f"refusing archive member with a backslash path: {name!r}"
        raise ArchiveDefenceError(message)

    normalized = unicodedata.normalize("NFC", name)
    if ":" in normalized.split("/", 1)[0]:
        message = f"refusing archive member with a drive-letter prefix: {name!r}"
        raise ArchiveDefenceError(message)

    candidate = PurePosixPath(normalized)
    if candidate.is_absolute():
        message = f"refusing absolute archive member name: {name!r}"
        raise ArchiveDefenceError(message)
    parts = [part for part in candidate.parts if part != "."]
    if any(part == ".." for part in parts):
        message = f"refusing archive member that escapes the extraction root: {name!r}"
        raise ArchiveDefenceError(message)
    if not parts:
        message = f"refusing archive member with no usable path: {name!r}"
        raise ArchiveDefenceError(message)
    for part in parts:
        if not part or not unicodedata.normalize("NFC", part).casefold():
            message = f"refusing archive member with an empty normalized component: {name!r}"
            raise ArchiveDefenceError(message)
        if part.endswith((".", " ")):
            message = f"refusing archive member with a trailing period or space component: {name!r}"
            raise ArchiveDefenceError(message)
        device_stem = part.split(".", 1)[0].casefold()
        if device_stem in _RESERVED_DEVICE_NAMES:
            message = f"refusing archive member with reserved device name {part!r}"
            raise ArchiveDefenceError(message)
    return "/".join(parts)


def _portable_member_key(canonical: str) -> str:
    """Return the platform-independent collision identity of a canonical path."""
    components = [
        unicodedata.normalize("NFC", component).casefold() for component in canonical.split("/")
    ]
    if not components or any(not component for component in components):
        message = f"refusing archive member with an empty portable component: {canonical!r}"
        raise ArchiveDefenceError(message)
    return "/".join(components)


def _strict_ancestor_prefixes(portable: str) -> tuple[str, ...]:
    """Return every strict ancestor prefix of a portable member key.

    For ``a/b/c`` this is ``("a", "a/b")`` — never ``a/b/c`` itself, and empty for a
    single-component key. Maintaining the union of these prefixes across admitted members
    turns the reverse-order file-versus-directory collision check — *does any admitted path
    lie beneath this file?* — into a constant-time membership test. ``portable`` is already in
    portable form (NFC-normalized, case-folded, ``/``-joined), so each prefix is too, and
    ``portable in ancestors`` is exactly ``any(existing.startswith(portable + "/"))`` over the
    admitted set: the string boundary that ``+ "/"`` enforced is the same one a path-component
    split enforces, so ``a`` never matches a sibling ``ab/…``.
    """
    components = portable.split("/")
    return tuple("/".join(components[:depth]) for depth in range(1, len(components)))


def safe_member_name(name: str) -> str:
    """Return the canonical name of a **file** member, refusing a directory entry.

    Directory entries are legitimate inside an archive but are never read as files;
    :func:`iter_members` skips them after registering them for collision checks.

    Raises:
        ArchiveDefenceError: the name is hostile or names a directory.
    """
    if name.endswith("/"):
        message = f"refusing to read directory entry {name!r} as a file member"
        raise ArchiveDefenceError(message)
    return canonical_member_name(name)


def iter_members(
    archive_path: Path,
    *,
    name_suffix: str | None = None,
    max_member_bytes: int = MAX_MEMBER_BYTES,
    max_total_bytes: int = MAX_TOTAL_EXPANDED_BYTES,
    max_ratio: float = MAX_EXPANSION_RATIO,
    max_members: int = MAX_MEMBER_COUNT,
    archive_relative_path: str | None = None,
    archive_sha256: str | None = None,
) -> Iterator[ArchiveMember]:
    """Yield validated members of an official SEC archive, read from their streams.

    Args:
        archive_path: Local path to the preserved archive. The archive itself is
            never modified or replaced.
        name_suffix: Optional suffix filter, for example ``".json"``.
        max_member_bytes: Refuse any member larger than this when expanded.
        max_total_bytes: Refuse the archive once cumulative expansion exceeds this.
        max_ratio: Refuse a member whose expansion ratio is implausible.
        max_members: Refuse an archive with more members than this.
        archive_relative_path: Lineage: the archive's path relative to the data root.
        archive_sha256: Lineage: the archive's recorded content hash.

    Raises:
        ArchiveDefenceError: the archive is corrupt or a member violates a rule.
    """
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            if len(entries) > max_members:
                message = (
                    f"refusing archive {archive_path.name}: {len(entries)} members exceed "
                    f"the limit {max_members}"
                )
                raise ArchiveDefenceError(message)

            files: dict[str, tuple[str, zipfile.ZipInfo]] = {}
            directories: set[str] = set()
            all_paths: set[str] = set()
            # The union of every admitted path's strict ancestor prefixes. It answers the
            # reverse-order collision — is some already-admitted path a descendant of this file? —
            # in constant time. The prior implementation rescanned the whole growing admitted set
            # per member, which is quadratic in the member count and was the accidental ~46-minute
            # stall on the 985,480-entry submissions archive (Decision 051 §4.1). The membership
            # test is semantically identical: see :func:`_strict_ancestor_prefixes`.
            strict_ancestors: set[str] = set()
            for info in entries:
                _refuse_special_member(info)
                canonical = canonical_member_name(info.filename)
                portable = _portable_member_key(canonical)
                if portable in all_paths:
                    message = (
                        f"refusing archive member {info.filename!r}: its portable path "
                        f"collides with another member after NFC normalization and case-folding"
                    )
                    raise ArchiveDefenceError(message)
                parent_keys = [
                    _portable_member_key(parent.as_posix())
                    for parent in PurePosixPath(canonical).parents
                    if parent.as_posix() != "."
                ]
                if any(parent in files for parent in parent_keys):
                    message = (
                        f"refusing archive member {info.filename!r}: a parent path is "
                        "already a file after portable canonicalization"
                    )
                    raise ArchiveDefenceError(message)
                if info.is_dir():
                    directories.add(portable)
                    all_paths.add(portable)
                    strict_ancestors.update(_strict_ancestor_prefixes(portable))
                    continue
                if portable in strict_ancestors:
                    message = (
                        f"refusing archive member {info.filename!r}: file and directory "
                        "paths collide after portable canonicalization"
                    )
                    raise ArchiveDefenceError(message)
                files[portable] = (canonical, info)
                all_paths.add(portable)
                strict_ancestors.update(_strict_ancestor_prefixes(portable))

            expanded = 0
            index = 0
            for canonical, info in files.values():
                if name_suffix is not None and not canonical.endswith(name_suffix):
                    continue
                _refuse_implausible(canonical, info, max_member_bytes, max_ratio)
                payload = _read_member(archive, info, canonical, max_member_bytes)
                expanded += len(payload)
                if expanded > max_total_bytes:
                    message = (
                        f"refusing archive {archive_path.name}: cumulative expansion "
                        f"{expanded} exceeds the limit {max_total_bytes}"
                    )
                    raise ArchiveDefenceError(message)
                yield ArchiveMember(
                    name=canonical,
                    compressed_size=info.compress_size,
                    uncompressed_size=len(payload),
                    payload=payload,
                    archive_relative_path=archive_relative_path,
                    archive_sha256=archive_sha256,
                    member_index=index,
                )
                index += 1
    except zipfile.BadZipFile as exc:
        message = (
            f"archive {archive_path.name} is corrupt and is quarantined rather than "
            f"treated as empty: {exc}"
        )
        raise ArchiveDefenceError(message, _REASON_INVALID) from exc


def iter_named_members(
    archive_path: Path,
    names: Sequence[str],
    *,
    max_member_bytes: int = MAX_MEMBER_BYTES,
    max_ratio: float = MAX_EXPANSION_RATIO,
) -> Iterator[tuple[str, bytes]]:
    """Yield exactly the named members of an archive, in the order requested.

    A **targeted** read rather than a second traversal: the central directory is scanned once
    to locate the requested canonical names, and only those members are decompressed. It exists
    for a caller that met a member during a full :func:`iter_members` pass, deliberately dropped
    its payload, and must now read that one member again by name — the bounded-residency shape
    accepted Decision 110 §8 requires of anything traversing the bulk archive.

    Everything is refused that :func:`iter_members` refuses about an individual member: names
    are canonicalized before anything else, non-regular members are refused, and declared size
    and expansion ratio are checked before a byte is read. What is deliberately **not**
    re-applied is the archive-level *cumulative* expansion cap: these bytes were already
    admitted under it during the full traversal, and re-counting a subset from zero would
    compare part of an archive against a whole-archive limit.

    Payload buffering is per member and no wider than :func:`iter_members`': one member is read,
    yielded, and dropped before the next is opened. Nothing is written to disk and nothing
    reaches the network.

    Args:
        archive_path: Local path to the preserved archive. It is never modified.
        names: The exact canonical member names to read. Order is the yield order, so the
            caller's sequence is the contract; a repeated name is refused rather than read
            twice.
        max_member_bytes: Refuse any requested member larger than this when expanded.
        max_ratio: Refuse a requested member whose expansion ratio is implausible.

    Raises:
        ArchiveDefenceError: the archive is corrupt; a name is hostile; a requested name is
            absent from the archive or resolves to more than one entry; a requested name is
            asked for twice; or a requested member violates a defensive rule.
    """
    wanted = set(names)
    if len(wanted) != len(names):
        repeated = sorted({name for name in names if list(names).count(name) > 1})
        message = (
            f"refusing a named-member read that asks for {repeated} more than once: the "
            "requested sequence is the yield order, so a repeated name has no unambiguous "
            "meaning and would decompress the same member twice"
        )
        raise ArchiveDefenceError(message)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            located: dict[str, zipfile.ZipInfo] = {}
            for info in archive.infolist():
                if info.is_dir():
                    continue
                _refuse_special_member(info)
                canonical = canonical_member_name(info.filename)
                if canonical not in wanted:
                    continue
                if canonical in located:
                    message = (
                        f"refusing archive member {canonical!r}: it resolves to more than "
                        "one entry, so the member the requested name refers to is ambiguous"
                    )
                    raise ArchiveDefenceError(message)
                located[canonical] = info
            for name in names:
                requested = located.get(name)
                if requested is None:
                    message = (
                        f"refusing to read archive member {name!r}: the archive does not "
                        "hold a member of exactly that canonical name"
                    )
                    raise ArchiveDefenceError(message)
                _refuse_implausible(name, requested, max_member_bytes, max_ratio)
                yield name, _read_member(archive, requested, name, max_member_bytes)
    except zipfile.BadZipFile as exc:
        message = (
            f"archive {archive_path.name} is corrupt and is refused rather than treated as "
            f"holding none of the requested members: {exc}"
        )
        raise ArchiveDefenceError(message, _REASON_INVALID) from exc


def extract_members(
    archive_path: Path,
    destination: Path,
    *,
    name_suffix: str | None = None,
) -> tuple[Path, ...]:
    """Write validated members beneath ``destination`` and return their paths.

    ``destination`` must already exist and is supplied by the caller, normally a
    temporary directory. Directory descriptors anchor every traversal step beneath
    that destination, and no existing final path is ever overwritten.

    Raises:
        ArchiveDefenceError: a member would be written outside ``destination``.
    """
    root = destination.resolve()
    if not root.is_dir():
        message = f"extraction destination {destination} does not exist"
        raise ArchiveDefenceError(message)
    written: list[Path] = []
    for member in iter_members(archive_path, name_suffix=name_suffix):
        target = root.joinpath(*member.name.split("/"))
        _write_member_exclusively(root, member)
        written.append(target)
    return tuple(written)


def _write_member_exclusively(root: Path, member: ArchiveMember) -> None:
    """Write one member through no-follow directory descriptors.

    Descriptor-relative traversal closes the check/use gap that would otherwise
    allow a parent directory to be replaced with a symlink between validation and
    creation. The final component is opened with ``O_EXCL`` and ``O_NOFOLLOW``.
    """
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW

    current_descriptor: int | None = None
    try:
        current_descriptor = os.open(root, directory_flags)
        components = member.name.split("/")
        for component in components[:-1]:
            with suppress(FileExistsError):
                os.mkdir(component, 0o700, dir_fd=current_descriptor)
            try:
                next_descriptor = os.open(
                    component,
                    directory_flags,
                    dir_fd=current_descriptor,
                )
            except OSError as exc:
                message = f"refusing archive member {member.name!r}: parent path is unsafe"
                raise ArchiveDefenceError(message) from exc
            os.close(current_descriptor)
            current_descriptor = next_descriptor

        file_flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            file_flags |= os.O_NOFOLLOW
        try:
            file_descriptor = os.open(
                components[-1],
                file_flags,
                0o600,
                dir_fd=current_descriptor,
            )
        except OSError as exc:
            message = (
                f"refusing to overwrite or follow an existing extraction target {member.name!r}"
            )
            raise ArchiveDefenceError(message) from exc
        try:
            with os.fdopen(file_descriptor, "wb") as handle:
                handle.write(member.payload)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            # The exclusively created target may be partial; preserve it for the
            # caller's temporary-directory cleanup and never replace another file.
            raise
    finally:
        if current_descriptor is not None:
            os.close(current_descriptor)


def _refuse_special_member(info: zipfile.ZipInfo) -> None:
    """Refuse a symlink, device, socket, or other non-regular member.

    Many writers store permission bits without file-type bits, so an absent type is
    not treated as suspicious; only an explicitly non-regular type is refused.
    """
    file_type = stat.S_IFMT(info.external_attr >> 16)
    if not file_type:
        return
    if file_type == stat.S_IFLNK:
        message = f"refusing symlink archive member {info.filename!r}"
        raise ArchiveDefenceError(message)
    if file_type not in {stat.S_IFREG, stat.S_IFDIR}:
        message = (
            f"refusing archive member {info.filename!r}: it is not a regular file or "
            f"directory (file type {file_type:#o})"
        )
        raise ArchiveDefenceError(message)


def _refuse_implausible(
    canonical: str,
    info: zipfile.ZipInfo,
    max_member_bytes: int,
    max_ratio: float,
) -> None:
    """Refuse a member whose declared size or expansion ratio is implausible."""
    if info.file_size > max_member_bytes:
        message = (
            f"refusing archive member {canonical!r}: declared size {info.file_size} "
            f"exceeds the limit {max_member_bytes}"
        )
        raise ArchiveDefenceError(message)
    if info.compress_size > 0 and info.file_size / info.compress_size > max_ratio:
        observed = info.file_size / info.compress_size
        message = (
            f"refusing archive member {canonical!r}: declared expansion ratio "
            f"{observed:.1f} exceeds {max_ratio}"
        )
        raise ArchiveDefenceError(message)


def _read_member(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    canonical: str,
    max_member_bytes: int,
) -> bytes:
    """Read one member from its stream, stopping if it exceeds its limit."""
    collected = bytearray()
    with archive.open(info, "r") as handle:
        while True:
            chunk = handle.read(_READ_CHUNK_BYTES)
            if not chunk:
                break
            collected.extend(chunk)
            if len(collected) > max_member_bytes:
                message = (
                    f"refusing archive member {canonical!r}: expanded size exceeds the "
                    f"limit {max_member_bytes} while streaming"
                )
                raise ArchiveDefenceError(message)
    return bytes(collected)
