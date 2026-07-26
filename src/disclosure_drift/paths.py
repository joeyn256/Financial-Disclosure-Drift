"""Filesystem path policy for Disclosure Drift (Decision 009).

Two runtime roots exist: ``DISCLOSURE_DRIFT_DATA_ROOT`` and
``DISCLOSURE_DRIFT_BACKUP_ROOT``. Both may be absolute machine-local paths. The
audit directory is always ``{data_root}/audit/sec`` and is not separately
configurable.

Database rows, manifests, and releases persist **only** paths relative to their
configured root. :func:`relative_to_root` is the single choke point that enforces
this, so no absolute personal path can reach a committed or exported artifact.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "SEC_SUBTREES",
    "BackupRootStatus",
    "DataTree",
    "PathPolicyError",
    "VolumeVerdict",
    "backup_root_status",
    "relative_to_root",
    "volume_verdict",
]


class PathPolicyError(DisclosureDriftError):
    """Raised when a path violates the storage policy."""


SEC_SUBTREES: Final[tuple[str, ...]] = (
    "raw/sec/bulk",
    "raw/sec/indexes",
    "raw/sec/filings",
    "raw/sec/quarantine",
    "staging/sec",
    "catalog",
    "releases/sec_inventory",
    "audit/sec",
    "locks",
)
"""Relative subtrees created under the data root."""

CATALOG_FILENAME: Final = "sec_ingestion.sqlite3"


@dataclass(frozen=True, slots=True)
class DataTree:
    """Resolved locations under a single data root."""

    data_root: Path

    @classmethod
    def from_root(cls, data_root: Path | str) -> DataTree:
        """Build a tree from ``data_root``, expanding ``~`` but never resolving symlinks."""
        return cls(data_root=Path(data_root).expanduser())

    # -- directories ------------------------------------------------------- #
    @property
    def raw_bulk(self) -> Path:
        """Bulk archive downloads."""
        return self.data_root / "raw" / "sec" / "bulk"

    @property
    def raw_indexes(self) -> Path:
        """EDGAR master-index downloads."""
        return self.data_root / "raw" / "sec" / "indexes"

    @property
    def raw_filings(self) -> Path:
        """Accession-addressed filing objects."""
        return self.data_root / "raw" / "sec" / "filings"

    @property
    def quarantine(self) -> Path:
        """Preserved damaged or unparseable payloads."""
        return self.data_root / "raw" / "sec" / "quarantine"

    @property
    def staging(self) -> Path:
        """Short-lived staging artifacts."""
        return self.data_root / "staging" / "sec"

    @property
    def catalog_dir(self) -> Path:
        """Operational catalog directory."""
        return self.data_root / "catalog"

    @property
    def catalog_database(self) -> Path:
        """Operational SQLite catalog path."""
        return self.catalog_dir / CATALOG_FILENAME

    @property
    def releases(self) -> Path:
        """Frozen Parquet releases."""
        return self.data_root / "releases" / "sec_inventory"

    @property
    def audit(self) -> Path:
        """Readable JSONL event logs; always ``{data_root}/audit/sec``."""
        return self.data_root / "audit" / "sec"

    @property
    def locks(self) -> Path:
        """Writer leases and rate-limiter coordination files."""
        return self.data_root / "locks"

    # -- operations -------------------------------------------------------- #
    def all_directories(self) -> tuple[Path, ...]:
        """Return every managed directory, in creation order."""
        return tuple(self.data_root / subtree for subtree in SEC_SUBTREES)

    def ensure_tree(self) -> tuple[Path, ...]:
        """Create every managed directory if absent and return them."""
        created = self.all_directories()
        for directory in created:
            directory.mkdir(parents=True, exist_ok=True)
        return created

    def accession_directory(self, cik_padded: str, accession_plain: str) -> Path:
        """Return the accession-addressed directory for a filing's raw objects."""
        if not cik_padded.isdigit() or len(cik_padded) != 10:
            message = f"cik_padded must be ten digits, received {cik_padded!r}"
            raise PathPolicyError(message)
        if not accession_plain.isdigit() or len(accession_plain) != 18:
            message = f"accession_plain must be eighteen digits, received {accession_plain!r}"
            raise PathPolicyError(message)
        return self.raw_filings / cik_padded / accession_plain

    def relative(self, path: Path) -> str:
        """Return ``path`` relative to this data root as a POSIX string."""
        return relative_to_root(path, self.data_root)


def relative_to_root(path: Path | str, root: Path | str) -> str:
    """Return ``path`` expressed relative to ``root`` as a POSIX string.

    This is the only sanctioned way to produce a path for storage in the catalog,
    a manifest, or a release.

    Raises:
        PathPolicyError: ``path`` is not inside ``root``.
    """
    candidate = Path(path).expanduser()
    base = Path(root).expanduser()
    try:
        relative = candidate.relative_to(base)
    except ValueError:
        message = (
            f"{candidate} is not inside the configured root {base}\n"
            "Only paths relative to a configured root may be persisted."
        )
        raise PathPolicyError(message) from None
    if relative.is_absolute() or ".." in relative.parts:
        message = f"refusing to persist non-relative path {relative}"
        raise PathPolicyError(message)
    return relative.as_posix()


@dataclass(frozen=True, slots=True)
class VolumeVerdict:
    """Whether two roots appear to live on different physical volumes."""

    distinct: bool
    data_device: int | None
    backup_device: int | None
    detail: str


def volume_verdict(data_root: Path, backup_root: Path) -> VolumeVerdict:
    """Compare device identifiers for the two roots.

    Advisory in Stage M2.1. Distinct volumes become a precondition for broad
    ingestion (Decision 009 section 9).
    """
    try:
        data_device = data_root.expanduser().stat().st_dev
    except OSError:
        return VolumeVerdict(False, None, None, f"data root {data_root} is not accessible")
    try:
        backup_device = backup_root.expanduser().stat().st_dev
    except OSError:
        return VolumeVerdict(
            False, data_device, None, f"backup root {backup_root} is not accessible"
        )
    distinct = data_device != backup_device
    detail = (
        "data and backup roots are on different devices"
        if distinct
        else "data and backup roots share one device; broad ingestion requires separate volumes"
    )
    return VolumeVerdict(distinct, data_device, backup_device, detail)


@dataclass(frozen=True, slots=True)
class BackupRootStatus:
    """Configured state of the backup root."""

    configured: bool
    path: Path | None
    exists: bool
    detail: str

    def require(self) -> Path:
        """Return the backup root or raise an actionable error.

        Raises:
            PathPolicyError: the backup root is unset or missing.
        """
        if self.path is None:
            message = (
                "backup root is not configured\n"
                "Fix: set DISCLOSURE_DRIFT_BACKUP_ROOT to a writable location on a "
                "different physical volume from the data root."
            )
            raise PathPolicyError(message)
        if not self.exists:
            message = (
                f"backup root {self.path} does not exist\n"
                "Fix: create the directory or correct DISCLOSURE_DRIFT_BACKUP_ROOT."
            )
            raise PathPolicyError(message)
        return self.path


def backup_root_status(raw_value: str | None = None) -> BackupRootStatus:
    """Report the backup-root state without requiring it.

    Offline work does not need a backup root; commands that perform backup or
    restore call :meth:`BackupRootStatus.require`.
    """
    value = os.environ.get("DISCLOSURE_DRIFT_BACKUP_ROOT") if raw_value is None else raw_value
    if value is None or not value.strip():
        return BackupRootStatus(False, None, False, "not configured")
    path = Path(value.strip()).expanduser()
    exists = path.is_dir()
    detail = "configured" if exists else "configured but missing"
    return BackupRootStatus(True, path, exists, detail)
