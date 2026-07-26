"""Release manifests, gates, and diffs (Decision 009 section 10).

A frozen release is never edited. Freezing requires every blocking gate to pass;
incremental updates create a new release plus a diff.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from disclosure_drift.errors import GateFailureError
from disclosure_drift.release.hashing import TableHash, hash_release

__all__ = [
    "RELEASE_SCHEMA_VERSION",
    "GateOutcome",
    "ReleaseDiffEntry",
    "ReleaseManifest",
    "build_manifest",
    "diff_releases",
]

RELEASE_SCHEMA_VERSION = "sec_inventory/0.1"
GateResult = Literal["pass", "fail", "not_run"]


@dataclass(frozen=True, slots=True)
class GateOutcome:
    """One release gate's result."""

    gate_name: str
    result: GateResult
    blocks_release: bool
    evidence_artifact: str | None = None

    @property
    def is_blocking_failure(self) -> bool:
        """Whether this outcome prevents freezing."""
        return self.blocks_release and self.result != "pass"


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    """A release manifest containing only relative paths and content hashes."""

    release_id: str
    release_schema_version: str
    created_at_utc: str
    table_hashes: tuple[TableHash, ...]
    release_content_sha256: str
    gates: tuple[GateOutcome, ...]
    notes: str | None = None
    frozen_at_utc: str | None = None
    approvals: Mapping[str, str] = field(default_factory=dict)

    @property
    def blocking_failures(self) -> tuple[GateOutcome, ...]:
        """Gates that block freezing."""
        return tuple(gate for gate in self.gates if gate.is_blocking_failure)

    @property
    def can_freeze(self) -> bool:
        """Whether every blocking gate passed."""
        return not self.blocking_failures

    def require_freezable(self) -> None:
        """Raise unless the release may be frozen.

        Raises:
            GateFailureError: at least one blocking gate failed.
        """
        failures = self.blocking_failures
        if not failures:
            return
        listed = ", ".join(f"{gate.gate_name}={gate.result}" for gate in failures)
        message = f"release {self.release_id} cannot be frozen: {listed}"
        raise GateFailureError(message)

    def to_json(self) -> str:
        """Render the manifest deterministically."""
        payload = {
            "release_id": self.release_id,
            "release_schema_version": self.release_schema_version,
            "created_at_utc": self.created_at_utc,
            "frozen_at_utc": self.frozen_at_utc,
            "release_content_sha256": self.release_content_sha256,
            "tables": [
                {
                    "table": item.table_name,
                    "columns": list(item.columns),
                    "row_count": item.row_count,
                    "normalized_content_sha256": item.normalized_content_sha256,
                }
                for item in sorted(self.table_hashes, key=lambda item: item.table_name)
            ],
            "gates": [
                {
                    "gate_name": gate.gate_name,
                    "result": gate.result,
                    "blocks_release": gate.blocks_release,
                    "evidence_artifact": gate.evidence_artifact,
                }
                for gate in sorted(self.gates, key=lambda gate: gate.gate_name)
            ],
            "approvals": dict(sorted(self.approvals.items())),
            "notes": self.notes,
        }
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"

    def write(self, directory: Path) -> Path:
        """Write the manifest into ``directory`` and return its path."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.release_id}_manifest.json"
        if path.exists() and self.frozen_at_utc is not None:
            message = f"frozen release manifest {path.name} may not be rewritten"
            raise GateFailureError(message)
        path.write_text(self.to_json(), encoding="utf-8")
        return path


def build_manifest(
    release_id: str,
    created_at_utc: str,
    table_hashes: Sequence[TableHash],
    gates: Sequence[GateOutcome],
    *,
    notes: str | None = None,
    approvals: Mapping[str, str] | None = None,
) -> ReleaseManifest:
    """Assemble a manifest and compute the release-level content hash."""
    return ReleaseManifest(
        release_id=release_id,
        release_schema_version=RELEASE_SCHEMA_VERSION,
        created_at_utc=created_at_utc,
        table_hashes=tuple(table_hashes),
        release_content_sha256=hash_release(table_hashes),
        gates=tuple(gates),
        notes=notes,
        approvals=dict(approvals or {}),
    )


@dataclass(frozen=True, slots=True)
class ReleaseDiffEntry:
    """One difference between two releases."""

    table_name: str
    diff_kind: Literal["added", "removed", "changed"]
    detail: str


def diff_releases(
    earlier: Iterable[TableHash],
    later: Iterable[TableHash],
) -> tuple[ReleaseDiffEntry, ...]:
    """Compare two releases by normalized table-content hash."""
    before = {item.table_name: item for item in earlier}
    after = {item.table_name: item for item in later}
    entries: list[ReleaseDiffEntry] = []
    for name in sorted(set(before) | set(after)):
        if name not in before:
            entries.append(ReleaseDiffEntry(name, "added", "table appears in the later release"))
        elif name not in after:
            entries.append(ReleaseDiffEntry(name, "removed", "table absent from the later release"))
        elif before[name].normalized_content_sha256 != after[name].normalized_content_sha256:
            entries.append(
                ReleaseDiffEntry(
                    name,
                    "changed",
                    f"rows {before[name].row_count} -> {after[name].row_count}",
                )
            )
    return tuple(entries)
