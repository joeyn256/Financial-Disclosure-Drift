"""Typed, fail-closed completion contract for the Stage M2.2 census."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = [
    "CatalogWriteState",
    "CensusCompletionDecision",
    "ParserTerminalState",
    "PlannedSourceState",
    "QATerminalState",
    "RetrievalTerminalState",
    "SnapshotVerificationState",
    "SourceScope",
]

SourceScope = Literal["base", "historical"]
RetrievalTerminalState = Literal[
    "not_retrieved",
    "retrieved",
    "reused",
    "failed",
    "blocked",
    "unavailable",
    "unknown",
    "quarantined",
]
SnapshotVerificationState = Literal[
    "not_verified",
    "verified",
    "missing",
    "hash_mismatch",
    "representation_mismatch",
]
ParserTerminalState = Literal[
    "not_started",
    "completed",
    "quarantined",
    "failed",
    "missing",
]
CatalogWriteState = Literal["not_started", "committed", "failed"]
QATerminalState = Literal["unknown", "passed", "blocked", "failed"]


@dataclass(frozen=True, slots=True)
class PlannedSourceState:
    """Terminal evidence for one source instance in one census run.

    An instance is a single normalized request identity. Base sources and every
    discovered historical submissions reference therefore have separate states.
    A structurally valid parser outcome with zero records is successful: record
    count is not part of this state machine.
    """

    instance_id: str
    source_id: str
    request_identity: str
    required: bool
    scope: SourceScope
    retrieval_state: RetrievalTerminalState = "not_retrieved"
    snapshot_state: SnapshotVerificationState = "not_verified"
    parser_state: ParserTerminalState = "not_started"
    catalog_state: CatalogWriteState = "not_started"
    qa_state: QATerminalState = "unknown"
    unresolved_blocking_reasons: tuple[str, ...] = ()
    observation_id: str | None = None

    @property
    def successful_terminal(self) -> bool:
        """Whether every required stage reached its verified success state."""
        return (
            self.retrieval_state in {"retrieved", "reused"}
            and self.snapshot_state == "verified"
            and self.parser_state == "completed"
            and self.catalog_state == "committed"
            and self.qa_state == "passed"
            and not self.unresolved_blocking_reasons
        )

    @property
    def blocks_completion(self) -> bool:
        """Whether this planned instance prevents a successful census."""
        return self.required and not self.successful_terminal

    def as_record(self) -> dict[str, object]:
        """Deterministic record for SQLite and the QA projection."""
        return {
            "instance_id": self.instance_id,
            "source_id": self.source_id,
            "request_identity": self.request_identity,
            "required": self.required,
            "scope": self.scope,
            "retrieval_state": self.retrieval_state,
            "snapshot_state": self.snapshot_state,
            "parser_state": self.parser_state,
            "catalog_state": self.catalog_state,
            "qa_state": self.qa_state,
            "unresolved_blocking_reasons": list(self.unresolved_blocking_reasons),
            "observation_id": self.observation_id,
            "successful_terminal": self.successful_terminal,
        }


@dataclass(frozen=True, slots=True)
class CensusCompletionDecision:
    """All independent gates needed to make a truthful completion claim."""

    sources: tuple[PlannedSourceState, ...]
    recovery_passed: bool
    recovery_blocking_reasons: tuple[str, ...]
    sqlite_integrity_passed: bool
    release_blocking_reason_count: int
    qa_report_written: bool
    audit_projection_complete: bool

    @property
    def incomplete_required_sources(self) -> tuple[PlannedSourceState, ...]:
        """Required source instances that did not reach verified success."""
        return tuple(source for source in self.sources if source.blocks_completion)

    @property
    def completed(self) -> bool:
        """Whether every explicit completion predicate is true."""
        return (
            not self.incomplete_required_sources
            and self.recovery_passed
            and not self.recovery_blocking_reasons
            and self.sqlite_integrity_passed
            and self.release_blocking_reason_count == 0
            and self.qa_report_written
            and self.audit_projection_complete
        )

    @property
    def detail(self) -> str:
        """Human-readable terminal state without a false success claim."""
        if self.completed:
            return "metadata census completed under the explicit M2.2-R1 completion contract"
        failures: list[str] = []
        if self.incomplete_required_sources:
            rendered = ", ".join(
                f"{source.source_id}[{source.instance_id}]"
                for source in self.incomplete_required_sources
            )
            failures.append(f"incomplete required sources: {rendered}")
        if not self.recovery_passed or self.recovery_blocking_reasons:
            failures.append("unresolved recovery state")
        if not self.sqlite_integrity_passed:
            failures.append("SQLite integrity gate failed")
        if self.release_blocking_reason_count:
            failures.append(
                f"{self.release_blocking_reason_count} unresolved release-blocking reason(s)"
            )
        if not self.qa_report_written:
            failures.append("QA report was not written")
        if not self.audit_projection_complete:
            failures.append("current-run audit projection is incomplete")
        return "metadata census incomplete: " + "; ".join(failures)

    def as_record(self) -> dict[str, object]:
        """Deterministic report representation."""
        return {
            "completed": self.completed,
            "detail": self.detail,
            "recovery_passed": self.recovery_passed,
            "recovery_blocking_reasons": list(self.recovery_blocking_reasons),
            "sqlite_integrity_passed": self.sqlite_integrity_passed,
            "release_blocking_reason_count": self.release_blocking_reason_count,
            "qa_report_written": self.qa_report_written,
            "audit_projection_complete": self.audit_projection_complete,
            "incomplete_required_source_ids": [
                source.instance_id for source in self.incomplete_required_sources
            ],
            "sources": [source.as_record() for source in self.sources],
        }
