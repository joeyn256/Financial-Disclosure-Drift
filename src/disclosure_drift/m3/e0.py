"""PRE-E0 catalog transition and M3.3-E0 offline-parse operator surfaces.

Accepted **Decision 094** §§5-11, as corrected by accepted **Decision 095** R79-R82. This
module implements two bounded state machines and nothing else:

``m3 prepare-e0-catalog``
    The exact ``0013 -> 0014 -> 0015`` accepted-catalog transition (§5), with a verified
    backup, one continuous writer lease, a hash-chained event ledger, and a closed terminal
    record.

``m3 offline-parse``
    The real M3.3-E0 offline metadata parse (§9), whose durable write set is the sixteen
    tables of §6.1 plus the category-A ``census_plan_sources.parser_state`` transition.

**Neither execute mode is reachable.** Both activation constants land as ``None``
(§7.2), so ``execute`` returns exit ``3``. A later exact owner instrument may replace
**only** the named constant with its governed token. No operator flag, environment value,
preflight result, verify result, catalog state, receipt, or namespace can substitute for
it, and this module offers no other door.

Three boundaries are structural rather than promised:

* **No network capability.** Nothing here imports or constructs a client, transport,
  socket, HTTP library, SEC route, or acquisition orchestrator, and both terminal records
  state zero logical requests and zero physical attempts (§7.3).
* **No acquisition import.** :data:`OPERATIONAL_CATALOG_RELATIVE_PATH` is restated here
  under accepted Decision 095 R81 rather than imported from ``m3/acquisition.py``. It is a
  deliberate source-boundary duplication of one frozen literal, pinned by a direct equality
  test, and it is not a second operator choice, configuration field, or path-discovery rule.
  The Decision 094 §5.2 predicate 3 acquisition-completion binding is likewise **source-local**
  (accepted Decision 099 R97): it reuses only ``inspect_receipt`` and the Decision-063
  ``resolve_predecessor_receipt`` from ``m3/receipt.py``, and imports no recovery module,
  acquisition orchestrator, request-plan builder, or source registry.
* **No private-path disclosure.** The evidence root is read once from the fixed unlogged
  environment variable, resolved through the accepted external-root boundary, and cached.
  Its value never reaches a message, a log record, a receipt, a ledger event, a terminal
  record, or CLI output.

**This module executes nothing today.** A passing preflight is not authority; a complete
terminal record is not owner acceptance; and neither is progression to E1, E2, or M3.4.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import shutil
import sqlite3
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal

from disclosure_drift.config import EVIDENCE_ROOT_ENV
from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.evidence_paths import require_external_evidence_root
from disclosure_drift.m3.receipt import (
    INTERRUPTION_STATES_V4,
    OPERATOR_RECEIPT_FILENAME,
    RUN_NAMESPACE_DIRNAME,
    ExecutionReceiptV4,
    canonical_bytes,
    inspect_receipt,
    resolve_predecessor_receipt,
)
from disclosure_drift.release.hashing import TableHash, hash_release, hash_table, normalize_value
from disclosure_drift.storage.sqlite import (
    Migration,
    applied_versions,
    available_migrations,
    integrity_report,
)

if TYPE_CHECKING:  # pragma: no cover - typing only; keeps the runtime import graph small
    from collections.abc import Callable

    from disclosure_drift.m3.offline_parse import OfflineParseReport

try:  # pragma: no cover - supported CI and production platforms are Unix
    fcntl: Any = importlib.import_module("fcntl")
except ImportError:  # pragma: no cover
    fcntl = None

__all__ = [
    "E0_BACKUP_FILENAME",
    "E0_EVENTS_FILENAME",
    "E0_EVENT_TYPES",
    "E0_RUN_NAMESPACE",
    "E0_TERMINAL_FILENAME",
    "E0_TERMINAL_SCHEMA_VERSION",
    "EVENT_LEDGER_SCHEMA_VERSION",
    "EXIT_CONFIG_ERROR",
    "EXIT_GATE_FAILURE",
    "EXIT_OK",
    "EXIT_STAGE_NOT_ENABLED",
    "EXIT_USAGE",
    "M3_2_ACQUISITION_JOB_KIND",
    "M3_2_COMPLETION_BINDING",
    "M3_3_E0_EXECUTION_AUTHORITY",
    "MAXIMUM_RELEASE_HASH_BYTES",
    "OPERATIONAL_CATALOG_RELATIVE_PATH",
    "PRE_E0_CATALOG_TRANSITION_AUTHORITY",
    "TRANSITION_BACKUP_FILENAME",
    "TRANSITION_EVENTS_FILENAME",
    "TRANSITION_EVENT_TYPES",
    "TRANSITION_RUN_NAMESPACE",
    "TRANSITION_SOURCE_HEAD",
    "TRANSITION_TARGET_HEAD",
    "TRANSITION_TERMINAL_FILENAME",
    "TRANSITION_TERMINAL_SCHEMA_VERSION",
    "AcquisitionCompletionBinding",
    "AcquisitionReceiptPin",
    "CatalogSnapshotDigest",
    "E0Error",
    "EventLedger",
    "LedgerIntegrityError",
    "OperatorResult",
    "PreflightRefusalError",
    "PreflightReport",
    "StageNotEnabledError",
    "TerminalValidationError",
    "catalog_snapshot_digest",
    "compute_terminal_record_id",
    "estimate_release_hash_memory",
    "e0_preflight",
    "e0_verify",
    "read_event_ledger",
    "resolve_evidence_root",
    "result_token",
    "run_offline_parse_command",
    "run_prepare_e0_catalog_command",
    "transition_preflight",
    "transition_verify",
    "validate_e0_terminal",
    "validate_transition_terminal",
]


# --------------------------------------------------------------------------- #
# Frozen literals
# --------------------------------------------------------------------------- #
OPERATIONAL_CATALOG_RELATIVE_PATH: Final = "catalogs/m3_2a_operational.sqlite3"
"""The accepted catalog, relative to the private evidence root.

**Accepted Decision 095 R81.** The same literal is defined in ``m3/acquisition.py``, and
Decision 094 §7.3 forbids this module from importing an acquisition orchestrator, so the
value is restated rather than imported. That duplication is deliberate and is pinned:
``tests/unit/test_m3_e0.py`` imports both constants independently and requires exact
equality, so a mutation of either literal fails.

It creates no second operator choice. There is no ``--catalog`` option, no configuration
field, and no path-discovery rule; the catalog is always exactly this path beneath the one
resolved private root. It is also not permission to edit the acquisition constant.
"""

PRE_E0_CATALOG_TRANSITION_AUTHORITY: Final[str | None] = None
"""The governed token authorizing one real ``0013 -> 0014 -> 0015`` transition.

``None`` means the transition ``execute`` mode is **not enabled** and returns exit ``3``
(Decision 094 §7.2). A later exact owner instrument may replace **only** this constant with
its governed token, run the specified validation, and create a new local commit; the
SHA-256 of that token is then recorded as ``owner_authority_sha256`` in the terminal record.

No operator flag, environment value, preflight result, verify result, catalog state,
receipt, or namespace can substitute for it. Transition activation also cannot enable E0:
that is a separate constant, below, and a separate owner act.
"""

M3_3_E0_EXECUTION_AUTHORITY: Final[str | None] = None
"""The governed token authorizing one real M3.3-E0 offline parse.

``None`` means the E0 ``execute`` mode is **not enabled** and returns exit ``3``. Held
independently of :data:`PRE_E0_CATALOG_TRANSITION_AUTHORITY` on purpose: a successful
transition is not E0 authority, and E0 success is not linkage-gate closure or E1 authority.
"""

TRANSITION_RUN_NAMESPACE: Final = "m3_3_pre_e0_catalog_transition_0013_0015_v1"
E0_RUN_NAMESPACE: Final = "m3_3_e0_offline_parse_v1"
"""The two production run namespaces (Decision 094 §7.1).

Internal constants, not CLI options: an operator-selected namespace would be a degree of
freedom with nothing to constrain it, and the create-once rule is only meaningful against a
fixed name. Tests may pass their own temporary namespace matching
:data:`_NAMESPACE_PATTERN`.
"""

TRANSITION_SOURCE_HEAD: Final = 13
TRANSITION_TARGET_HEAD: Final = 15

#: Decision 094 §1.1's measured packaged digests, restated so a drifted migration file is
#: refused rather than applied. Keyed by the zero-padded version the terminal record uses.
PACKAGED_MIGRATION_SHA256: Final[Mapping[str, str]] = {
    "0014": "0490ea4e76cc365f03b851bd44a3b918f37109c97258abf5fb98d8070ccff9f1",
    "0015": "d7f22999cb3e6736c765de72a1031c170f2cb5547ccaccf7469a2d3be018835f",
}

#: Migration ``0014``'s executable empty-state guard (Decision 094 §1.3).
MIGRATION_0014_EMPTY_TABLES: Final[tuple[str, ...]] = (
    "census_accessions",
    "census_accession_observations",
    "census_parsed_records",
    "census_parser_runs",
    "pilot_candidate_snapshots",
    "pilot_candidate_accessions",
    "pilot_candidate_accession_registrants",
    "pilot_selection_runs",
    "pilot_selected_accessions",
    "pilot_manifest_versions",
)

#: Migration ``0015``'s executable empty-state guard (Decision 094 §1.3).
MIGRATION_0015_EMPTY_TABLES: Final[tuple[str, ...]] = (
    "pilot_candidate_snapshots",
    "pilot_candidate_accessions",
    "pilot_candidate_accession_registrants",
    "pilot_candidate_accession_evidence",
    "pilot_candidate_accession_reasons",
    "pilot_selection_runs",
    "pilot_selected_accessions",
    "pilot_reserve_accessions",
    "pilot_manifest_versions",
)

#: The union both guards imply, ordered and deduplicated so the precondition report has one
#: deterministic key order.
EMPTY_STATE_TABLES: Final[tuple[str, ...]] = tuple(
    sorted({*MIGRATION_0014_EMPTY_TABLES, *MIGRATION_0015_EMPTY_TABLES})
)

#: The accepted plan size E0 preflight requires (Decision 094 §1.2, §9.1).
PLANNED_SOURCE_COUNT: Final = 76


@dataclass(frozen=True, slots=True)
class AcquisitionReceiptPin:
    """One pinned accepted M3.2 completion receipt, by public name and exact identity.

    Every field is a fixed public value already published in accepted Decisions 061-063 and
    restated by Decision 099 §3. ``relative_path`` is private-root-relative, so nothing here
    is or discloses an absolute path.
    """

    label: str
    relative_path: str
    file_sha256: str
    receipt_id: str
    run_id: str
    completion_status: str
    request_plan_sha256: str


@dataclass(frozen=True, slots=True)
class AcquisitionCompletionBinding:
    """The exact accepted M3.2 completion chain Decision 094 §5.2 predicate 3 validates.

    A single frozen object rather than a scatter of module constants, because predicate 3 is
    one binding: the T7 head receipt, its T6 predecessor, the window they share, the head's
    exact completion facts, the accepted head observation, and the cumulative attempt total.
    Splitting them would let a later edit move one pin without moving the rest.
    """

    head: AcquisitionReceiptPin
    predecessor: AcquisitionReceiptPin
    acquisition_window: str
    head_logical_request_count: int
    head_physical_attempt_count: int
    head_observation_id: str
    cumulative_physical_attempt_count: int


M3_2_COMPLETION_BINDING: Final = AcquisitionCompletionBinding(
    head=AcquisitionReceiptPin(
        label="T7",
        relative_path="runs/m3_2_decision_062_sic_continuation/execution_receipt.json",
        file_sha256="ae8ace5dc62155c9dca395af238290b0bb5b99dc4e3f1741e3d8ff1c9ab9c3dd",
        receipt_id="7d72a5501f66d36af9024b80a64060668da315b8880fb5add028917d36ad12e1",
        run_id="m3-2-acquisition-b6f8bc7f48b94e6080038db575b204e5",
        completion_status="complete",
        request_plan_sha256="f77e003ccc0ed8f9c0e55065b3c211aa5e33c7abf86cc71cbe66d427611d890a",
    ),
    predecessor=AcquisitionReceiptPin(
        label="T6",
        relative_path="runs/m3_2a_clean_carry_in/execution_receipt.json",
        file_sha256="0278c857d7816a79907068513fe09d5b78fc3973ba415149fbc9d73605b5359c",
        receipt_id="37dd811497d4a57e8b911917ed6c0426a22f443c3ddd5aeba8d4da3e076f6a7c",
        run_id="m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44",
        completion_status="failed",
        request_plan_sha256="19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68",
    ),
    acquisition_window="M3.2A",
    head_logical_request_count=1,
    head_physical_attempt_count=1,
    head_observation_id="6e9d92c859bc48faa6c1c5e47c36fd8e",
    cumulative_physical_attempt_count=77,
)
"""The accepted M3.2 completion evidence (accepted Decision 099 §3, from Decisions 061-063).

**Fixed, not discovered.** Predicate 3 is a provenance binding, so nothing about it is an
operator choice, a search, a "most recent receipt" rule, or a value read from the catalog it is
meant to bind. A disposable test may substitute a synthetic binding in memory to build an
accepted-shaped chain; the shipped literals above are the accepted ones and are pinned by a
source-text assertion.
"""

#: The ``ops_ingestion_jobs.job_kind`` every M3.2 acquisition run is registered under. Restated
#: here rather than imported: Decision 094 §7.3 forbids importing the acquisition orchestrator.
M3_2_ACQUISITION_JOB_KIND: Final = "m3_2_acquisition"

#: The truthful ``ops_ingestion_jobs.job_state`` for each terminal receipt completion status.
#: A ``complete`` receipt beside a ``failed`` run row establishes nothing, and disagreement is
#: never reconciled by preferring one surface over the other.
_ACQUISITION_TERMINAL_JOB_STATES: Final[Mapping[str, str]] = {
    "complete": "completed",
    "failed": "failed",
    "stopped_at_ceiling": "failed",
    "stopped_by_gate": "failed",
}

TRANSITION_BACKUP_FILENAME: Final = "catalog_backup_0013.sqlite3"
TRANSITION_EVENTS_FILENAME: Final = "catalog_transition_events.jsonl"
TRANSITION_TERMINAL_FILENAME: Final = "catalog_transition_terminal.json"

E0_BACKUP_FILENAME: Final = "pre_e0_catalog_0015.sqlite3"
E0_EVENTS_FILENAME: Final = "e0_events.jsonl"
E0_TERMINAL_FILENAME: Final = "e0_terminal.json"

TRANSITION_TERMINAL_SCHEMA_VERSION: Final = "m3-3-pre-e0-catalog-transition-terminal/1.0"
E0_TERMINAL_SCHEMA_VERSION: Final = "m3-3-e0-terminal/1.0"
EVENT_LEDGER_SCHEMA_VERSION: Final = "m3-3-event-ledger/1.0"

TRANSITION_COMMAND_NAME: Final = "m3 prepare-e0-catalog"
E0_COMMAND_NAME: Final = "m3 offline-parse"
TRANSITION_COMMAND_VERSION: Final = "m3.3b-pre-e0-catalog-transition/1.0"
E0_COMMAND_VERSION: Final = "m3.3b-e0-offline-parse/1.0"

#: Decision 094 §5.2 predicate 11: three catalog copies plus a gibibyte of headroom.
DISK_HEADROOM_BYTES: Final = 1_073_741_824
DISK_CATALOG_MULTIPLE: Final = 3

#: Decision 094 §8.2's absolute per-table release-hash ceiling, and the fraction of physical
#: memory the same estimate may not exceed.
MAXIMUM_RELEASE_HASH_BYTES: Final = 2_147_483_648
PHYSICAL_MEMORY_FRACTION_DENOMINATOR: Final = 4

#: Decision 094 §8.2's conservative peak coefficients for one table's ``hash_table`` call:
#: the normalized rows are materialized, sorted, and encoded, so four times the normalized
#: UTF-8 length plus a fixed per-row object overhead bounds the peak.
_RELEASE_HASH_BYTE_MULTIPLE: Final = 4
_RELEASE_HASH_ROW_OVERHEAD: Final = 256

#: Test-only namespaces must match this; the two production namespaces are constants above.
_NAMESPACE_PATTERN: Final = r"\A[a-z0-9][a-z0-9_-]{0,127}\Z"

_LEASE_FILENAME: Final = "catalog_writer.lease"

_DIRECTORY_MODE: Final = 0o700
_FILE_MODE: Final = 0o600

EXIT_OK: Final = 0
EXIT_CONFIG_ERROR: Final = 1
EXIT_USAGE: Final = 2
EXIT_STAGE_NOT_ENABLED: Final = 3
EXIT_GATE_FAILURE: Final = 4

OperatorMode = Literal["preflight", "execute", "verify"]
OPERATOR_MODES: Final[tuple[str, ...]] = ("preflight", "execute", "verify")

TRANSITION_EVENT_TYPES: Final[tuple[str, ...]] = (
    "PREFLIGHT_PASSED",
    "BACKUP_VERIFIED",
    "MIGRATION_0014_COMMITTED",
    "MIGRATION_0015_COMMITTED",
    "POSTCHECK_PASSED",
    "EXECUTION_RECEIPT_WRITTEN",
    "FAILED",
    "INTERRUPTED",
)

E0_EVENT_TYPES: Final[tuple[str, ...]] = (
    "PREFLIGHT_PASSED",
    "BACKUP_VERIFIED",
    "SOURCE_DISPOSITION_RECORDED",
    "FULL_INDEX_OBSERVATIONS_MATERIALIZED",
    "ACCESSION_RESOLUTIONS_PERSISTED",
    "ASSOCIATIONS_MATERIALIZED",
    "VALIDATION_PASSED",
    "IDENTITIES_RECOMPUTED",
    "EXECUTION_RECEIPT_WRITTEN",
    "FAILED",
    "INTERRUPTED",
)

#: Decision 094 §10.2's closed ``details`` projection, per event type. ``details`` is not an
#: arbitrary JSON escape hatch: a key outside its event's tuple is refused, and so is a
#: required key that is missing. ``SOURCE_DISPOSITION_RECORDED``'s optional tail is the one
#: place a key may be absent, because a category-B or category-C source has no parser run.
_EVENT_DETAIL_KEYS: Final[Mapping[str, tuple[tuple[str, ...], tuple[str, ...]]]] = {
    "TRANSITION:PREFLIGHT_PASSED": (
        (
            "pre_migration_head",
            "catalog_bytes",
            "precondition_table_count",
            "pre_catalog_logical_sha256",
        ),
        (),
    ),
    "E0:PREFLIGHT_PASSED": (
        (
            "migration_head",
            "planned_source_count",
            "input_observation_set_sha256",
            "pre_e0_catalog_logical_sha256",
        ),
        (),
    ),
    "BACKUP_VERIFIED": (
        ("relative_path", "byte_length", "file_sha256", "catalog_logical_sha256"),
        (),
    ),
    "MIGRATION_0014_COMMITTED": (
        ("version", "name", "checksum_sha256", "integrity_check", "foreign_key_violations"),
        (),
    ),
    "MIGRATION_0015_COMMITTED": (
        ("version", "name", "checksum_sha256", "integrity_check", "foreign_key_violations"),
        (),
    ),
    "POSTCHECK_PASSED": (
        (
            "post_migration_head",
            "post_preexisting_content_sha256",
            "integrity_check",
            "foreign_key_violations",
        ),
        (),
    ),
    "SOURCE_DISPOSITION_RECORDED": (
        ("census_run_id", "source_instance_id", "source_id", "disposition", "parser_state_after"),
        ("parser_run_id", "parsed_records", "quarantined_records"),
    ),
    "FULL_INDEX_OBSERVATIONS_MATERIALIZED": (
        ("full_index_registrant_observation_count", "full_index_unbound_accession_count"),
        (),
    ),
    "ACCESSION_RESOLUTIONS_PERSISTED": (("accession_resolution_count",), ()),
    "VALIDATION_PASSED": (
        ("e0_catalog_state_sha256", "integrity_check", "foreign_key_violations"),
        (),
    ),
    "IDENTITIES_RECOMPUTED": (
        ("e0_catalog_state_sha256", "table_hash_count", "plan_parser_state_hash"),
        (),
    ),
    "EXECUTION_RECEIPT_WRITTEN": (("execution_receipt_id",), ()),
    "FAILED": (("reason_code", "reason_detail"), ()),
    "INTERRUPTED": (("reason_code", "reason_detail", "interruption_state"), ()),
}

#: ``ASSOCIATIONS_MATERIALIZED`` carries "every key of the §9.5 ``association_totality``
#: object". Resolved from the accepted dataclass rather than restated, so the two cannot
#: drift apart: a field added to the totality is automatically a permitted detail key.
ASSOCIATION_TOTALITY_KEYS: Final[tuple[str, ...]] = (
    "census_accession_count",
    "established_accession_count",
    "unestablished_accession_count",
    "substantive_relation_count",
    "established_zero_relation_count",
    "established_singleton_count",
    "established_multi_count",
    "singleton_scalar_mismatch_count",
    "multi_nonnull_scalar_count",
    "orphan_relation_count",
    "invalid_cik_rendering_count",
    "association_provenance_failure_count",
    "submissions_member_missing_full_index_count",
    "unbindable_registrant_member_count",
    "unestablished_membership_conflict_count",
)


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class E0Error(DisclosureDriftError):
    """Base class for every PRE-E0 failure. Every one of them is fail-closed."""


class StageNotEnabledError(E0Error):
    """The requested mode is not enabled by the current executable boundary (exit ``3``).

    Raised only by an ``execute`` mode whose source-bound activation constant is ``None``.
    It is deliberately its own class so no generic gate-failure handler can convert a
    "not authorized" into a "gate failed" or the reverse.
    """


class PreflightRefusalError(E0Error):
    """A preflight, integrity, identity, totality, freeze, or verification gate failed."""


class TerminalValidationError(E0Error):
    """A terminal record is not exactly the closed schema its status requires."""


class LedgerIntegrityError(E0Error):
    """An event ledger is truncated, reordered, mutated, or not hash-chained."""


class EvidenceRootUnsetError(E0Error):
    """The fixed private-root environment variable is absent or not a lawful external root.

    The message states the variable's **name** and the rule that was broken. It never states
    the value, a resolved path, or any component of one: this refusal is printed to an
    operator, and naming the path would leak exactly what the boundary exists to protect.
    """


# --------------------------------------------------------------------------- #
# Decision 094 §7.1 / Decision 095 R80 -- the one private-root resolution
# --------------------------------------------------------------------------- #
_RESOLVED_EVIDENCE_ROOT: Path | None = None


def resolve_evidence_root(
    repository_root: Path, *, environ: Mapping[str, str] | None = None
) -> Path:
    """Resolve the private evidence root once per process, and cache the reference.

    Accepted Decision 095 R80 makes ``DISCLOSURE_DRIFT_EVIDENCE_ROOT`` a **centrally
    recognized runtime root**: :mod:`disclosure_drift.config` knows the name so the process
    is not refused before dispatch, and applies nothing. This function is the only place the
    value is read, and it is read through the accepted external-root boundary, which refuses
    a relative path, the checkout, anything inside it, and any ancestor of it.

    The resolved reference is cached for the process (Decision 093 §10: resolved once,
    cached, with no ``$HOME`` traversal). The **value** is never returned to a renderer,
    written to a receipt, appended to a ledger, or logged; callers receive a path they use to
    open files and are expected to report only root-relative names.

    Args:
        repository_root: The checkout the root must lie outside of.
        environ: Environment mapping; :data:`os.environ` when omitted. Supplied by tests so a
            synthetic temporary root can be used without touching the ambient variable.

    Raises:
        EvidenceRootUnsetError: the variable is absent, blank, or not a lawful external root.
    """
    global _RESOLVED_EVIDENCE_ROOT  # noqa: PLW0603 - one process-lifetime cache, by design
    if environ is None and _RESOLVED_EVIDENCE_ROOT is not None:
        return _RESOLVED_EVIDENCE_ROOT
    source = os.environ if environ is None else environ
    raw = source.get(EVIDENCE_ROOT_ENV)
    if raw is None or not raw.strip():
        message = (
            f"{EVIDENCE_ROOT_ENV} is not set; this command reads the accepted private root "
            f"from that variable alone and has no default, no fallback, and no path option"
        )
        raise EvidenceRootUnsetError(message)
    try:
        resolved = require_external_evidence_root(raw, repository_root)
    except (ValueError, OSError) as exc:
        # The boundary's own messages never name either resolved path, which is why the
        # exception text may be quoted here without leaking one.
        message = f"{EVIDENCE_ROOT_ENV} is not a lawful external evidence root: {exc}"
        raise EvidenceRootUnsetError(message) from exc
    if environ is None:
        _RESOLVED_EVIDENCE_ROOT = resolved
    return resolved


def _reset_evidence_root_cache() -> None:
    """Clear the process cache. Test support only; no production caller."""
    global _RESOLVED_EVIDENCE_ROOT  # noqa: PLW0603 - mirrors the cache above
    _RESOLVED_EVIDENCE_ROOT = None


# --------------------------------------------------------------------------- #
# Decision 094 §8 -- run namespaces, containment, and create-once artifacts
# --------------------------------------------------------------------------- #
def validate_namespace(namespace: str) -> str:
    """Return ``namespace`` if it matches the accepted pattern, else refuse.

    The two production namespaces are constants and never pass through operator input; this
    exists because §7.1 lets **tests** call the library with their own temporary namespace,
    and an unvalidated one could escape the runs directory.
    """
    if not re.fullmatch(_NAMESPACE_PATTERN, namespace):
        message = (
            f"run namespace {namespace!r} is not of the accepted shape; a namespace is 1-128 "
            f"characters of lowercase letters, digits, underscore, and hyphen, starting "
            f"alphanumeric"
        )
        raise E0Error(message)
    return namespace


def _refuse_symlinked_descent(root: Path, candidate: Path) -> None:
    """Refuse if any component from ``root`` down to ``candidate`` is a symlink.

    Checked component by component rather than by comparing resolved paths, because a
    resolved comparison answers "where does this land" and the rule here is "was any step an
    alias at all". A symlinked run directory would place governed artifacts somewhere the
    write boundary never approved.
    """
    relative = candidate.relative_to(root)
    walked = root
    for part in relative.parts:
        walked = walked / part
        if walked.is_symlink():
            message = (
                f"the governed path component {part!r} is a symbolic link; run namespaces and "
                f"their artifacts are regular directories and files under the private root"
            )
            raise E0Error(message)


def resolve_within(root: Path, relative: str | Path, *, label: str) -> Path:
    """Resolve ``relative`` beneath ``root``, refusing any escape.

    Implemented here rather than imported from ``m3/acquisition.py``: Decision 094 §7.3
    forbids this module from importing an acquisition orchestrator, and the containment rule
    is four lines. No message names either absolute path.
    """
    candidate = Path(relative)
    if candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        message = f"the {label} path must be relative to the private root and may not ascend"
        raise E0Error(message)
    target = root / candidate
    if root not in target.parents and target != root:  # pragma: no cover - defensive
        message = f"the {label} path escapes the private root"
        raise E0Error(message)
    return target


def runs_directory(evidence_root: Path) -> Path:
    """The private root's ``runs/`` directory, which holds one namespace per run."""
    return evidence_root / RUN_NAMESPACE_DIRNAME


def namespace_directory(evidence_root: Path, namespace: str) -> Path:
    """The run directory for ``namespace``, without creating or touching anything."""
    return runs_directory(evidence_root) / validate_namespace(namespace)


def _fsync_directory(directory: Path) -> None:
    """Flush a directory entry so a created file survives a crash.

    Writing and fsyncing a file is not enough on its own: the *name* lives in the parent
    directory, and an unsynced parent can lose it. Decision 094 §8 requires both.
    """
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def create_run_namespace(evidence_root: Path, namespace: str) -> Path:
    """Create the fixed run directory exactly once, at mode ``0700``.

    Decision 094 §5.3 item 3: refuse a symlink and refuse any pre-existing path before
    creating. ``mkdir`` without ``exist_ok`` is the create-once primitive -- it is atomic, so
    two concurrent callers cannot both believe they created it, and a namespace is never
    reused.
    """
    validate_namespace(namespace)
    parent = runs_directory(evidence_root)
    if parent.is_symlink():
        message = "the private root's runs directory is a symbolic link"
        raise E0Error(message)
    if not parent.exists():
        parent.mkdir(mode=_DIRECTORY_MODE, parents=True)
        _fsync_directory(evidence_root)
    if not parent.is_dir():
        message = "the private root's runs path exists and is not a directory"
        raise E0Error(message)
    target = parent / namespace
    if target.is_symlink():
        message = f"run namespace {namespace!r} exists as a symbolic link and is refused"
        raise E0Error(message)
    if target.exists():
        message = (
            f"run namespace {namespace!r} already exists; a namespace is create-once and is "
            f"never reused, resumed, repaired, or overwritten"
        )
        raise E0Error(message)
    target.mkdir(mode=_DIRECTORY_MODE)
    target.chmod(_DIRECTORY_MODE)
    _fsync_directory(parent)
    return target


def write_once(path: Path, payload: bytes) -> None:
    """Create ``path`` with ``O_EXCL`` at mode ``0600``, write, and fsync it and its parent.

    ``O_CREAT | O_EXCL`` is what makes this write-once at the operating system rather than by
    a prior existence check, so no window exists in which a governed artifact could be
    replaced between the check and the write.
    """
    if path.is_symlink():
        message = f"{path.name} exists as a symbolic link and is refused"
        raise E0Error(message)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, _FILE_MODE)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    path.chmod(_FILE_MODE)
    _fsync_directory(path.parent)


def _precreate_exclusive(path: Path) -> None:
    """Create an empty ``0600`` file with ``O_EXCL`` and close it.

    Decision 094 §5.3 item 4 and finding m2: the backup is precreated at ``0600`` **before**
    SQLite opens it, so no window exists in which the destination is world-readable. SQLite
    creating the file itself would use the process umask.
    """
    if path.exists() or path.is_symlink():
        message = f"{path.name} already exists and is refused; the backup is create-once"
        raise E0Error(message)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, _FILE_MODE)
    os.close(descriptor)
    path.chmod(_FILE_MODE)


def file_digest(path: Path) -> tuple[str, int]:
    """Return ``(sha256, byte_length)`` for a completed file, read in bounded chunks."""
    digest = hashlib.sha256()
    length = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            length += len(chunk)
    return digest.hexdigest(), length


# --------------------------------------------------------------------------- #
# Decision 094 §8.2 -- exact catalog logical digests
# --------------------------------------------------------------------------- #
#: SQLite's own bookkeeping objects. Excluded from every projection: their contents are an
#: implementation detail of the file format, not application state, and including them would
#: make an identical logical catalog hash differently on two SQLite builds.
_INTERNAL_PREFIX: Final = "sqlite_"

#: The pseudo-table name the logical schema is hashed under (§8.2 item 4).
_SCHEMA_PSEUDO_TABLE: Final = "sqlite_schema"

#: The migration ledger, excluded from the pre-existing-content projection because the
#: transition legitimately appends to it. Excluding it is what lets equality prove that no
#: pre-existing *application* row changed while the schema and ledger changed truthfully.
_MIGRATION_LEDGER_TABLE: Final = "ops_schema_migrations"


def _user_tables(connection: sqlite3.Connection) -> tuple[str, ...]:
    """Every non-internal table in ``sqlite_schema``, by name, in name order."""
    return tuple(
        str(row["name"])
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type = 'table' ORDER BY name"
        ).fetchall()
        if not str(row["name"]).startswith(_INTERNAL_PREFIX)
    )


def _live_columns(connection: sqlite3.Connection, table: str) -> tuple[str, ...]:
    """Every live column of ``table`` in ``PRAGMA table_xinfo`` ``cid`` order.

    ``table_xinfo`` rather than ``table_info`` so a hidden or generated column is visible;
    ``hidden = 1`` (a virtual-table hidden column) and ``hidden = 2`` (a VIRTUAL generated
    column) carry no stored value, so they are excluded from a content projection while
    ``hidden = 3`` (STORED generated) is included.
    """
    return tuple(
        str(row["name"])
        for row in connection.execute(f"PRAGMA table_xinfo({_quote(table)})").fetchall()
        if int(row["hidden"]) not in (1, 2)
    )


def _quote(identifier: str) -> str:
    """Quote a SQLite identifier read back from ``sqlite_schema``.

    Table names come from the catalog's own schema, never from operator input, so this is a
    correctness measure for an unusual name rather than an injection boundary -- but it is
    written anyway, because "the name came from a trusted place" is exactly the reasoning
    that stops being true after a refactor.
    """
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    """Whether ``table`` exists in this catalog."""
    row = connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return row is not None


def _schema_pseudo_table_hash(connection: sqlite3.Connection) -> TableHash:
    """Hash the logical schema as a pseudo-table (§8.2 item 4).

    Exactly ``(type, name, tbl_name, sql)`` for non-internal tables, indexes, triggers, and
    views -- and deliberately **never** ``rootpage``, which is a physical page number that
    changes on a rebuild without any logical change and would make an identical schema hash
    differently after a VACUUM.
    """
    rows = [
        {
            "type": str(row["type"]),
            "name": str(row["name"]),
            "tbl_name": str(row["tbl_name"]),
            "sql": row["sql"],
        }
        for row in connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_schema ORDER BY type, name"
        ).fetchall()
        if not str(row["name"]).startswith(_INTERNAL_PREFIX)
    ]
    return hash_table(_SCHEMA_PSEUDO_TABLE, ("type", "name", "tbl_name", "sql"), rows)


def _hash_one_table(
    connection: sqlite3.Connection, table: str, columns: Sequence[str]
) -> TableHash:
    """Hash one table's rows over ``columns``, materializing only that table.

    Each table is hashed and released before the next is materialized (§8.2), which is what
    keeps peak memory to one table rather than to the whole catalog. The preflight estimator
    bounds that single table before any writer opens.
    """
    projection = ", ".join(_quote(column) for column in columns)
    cursor = connection.execute(f"SELECT {projection} FROM {_quote(table)}")  # noqa: S608
    rows = ({column: row[column] for column in columns} for row in cursor)
    return hash_table(table, tuple(columns), rows)


@dataclass(frozen=True, slots=True)
class CatalogSnapshotDigest:
    """One strictly read-only snapshot's §8.2 digests and its table projection.

    ``projection`` records the exact ``(table, columns)`` pairs this snapshot hashed. The
    post-transition pre-existing-content digest repeats *that* projection rather than
    re-enumerating the catalog, which is what makes the equality meaningful: a column
    migration ``0014`` or ``0015`` adds is excluded on both sides, so equality proves no
    pre-existing application row changed while permitting the schema to change truthfully.
    """

    #: ``None`` exactly when a recorded projection was replayed. Decision 094 §8.1 asks for
    #: ``pre_catalog_logical_sha256`` and both pre-existing-content digests, and for no
    #: post-transition full logical digest -- the schema legitimately changed, so a full
    #: digest could only ever differ and would prove nothing.
    catalog_logical_sha256: str | None
    preexisting_content_sha256: str
    projection: tuple[tuple[str, tuple[str, ...]], ...]
    table_count: int

    def require_full(self) -> str:
        """The full logical digest, or refuse rather than substitute a placeholder."""
        if self.catalog_logical_sha256 is None:  # pragma: no cover - defensive
            message = "a replayed projection carries no full catalog logical digest"
            raise PreflightRefusalError(message)
        return self.catalog_logical_sha256


def catalog_snapshot_digest(
    connection: sqlite3.Connection,
    *,
    projection: Sequence[tuple[str, Sequence[str]]] | None = None,
) -> CatalogSnapshotDigest:
    """Compute both §8.2 digest projections from **one** scan per table.

    Decision 094 §8.2 and adopted optimization O1: the full logical digest and the
    pre-existing-content digest need the same per-table content, so one scan updates both
    digest states rather than the catalog being walked twice.

    Args:
        connection: A strictly read-only connection to the snapshot being hashed.
        projection: When given, the exact ``(table, columns)`` pairs to hash for the
            pre-existing-content digest -- the head-``0013`` projection, replayed after the
            transition. When omitted, it is enumerated from this snapshot's own schema.

    Returns:
        Both digests plus the projection actually used, so a caller can replay it later.

    Raises:
        PreflightRefusalError: a recorded projection names a table or column this snapshot lacks.
    """
    if projection is None:
        pairs = tuple(
            (table, _live_columns(connection, table)) for table in _user_tables(connection)
        )
        replaying = False
    else:
        pairs = tuple((table, tuple(columns)) for table, columns in projection)
        replaying = True

    full: list[TableHash] = [] if replaying else [_schema_pseudo_table_hash(connection)]
    preexisting: list[TableHash] = []
    for table, columns in pairs:
        if replaying:
            if not _table_exists(connection, table):
                message = (
                    f"the recorded pre-existing projection names table {table!r}, which this "
                    f"snapshot does not carry; the transition may not drop a pre-existing table"
                )
                raise PreflightRefusalError(message)
            live = set(_live_columns(connection, table))
            missing = tuple(column for column in columns if column not in live)
            if missing:
                message = (
                    f"the recorded pre-existing projection names column(s) {missing} of "
                    f"{table!r}, which this snapshot does not carry"
                )
                raise PreflightRefusalError(message)
        digest = _hash_one_table(connection, table, columns)
        if not replaying:
            full.append(digest)
        if table != _MIGRATION_LEDGER_TABLE:
            preexisting.append(digest)
    return CatalogSnapshotDigest(
        catalog_logical_sha256=None if replaying else hash_release(full),
        preexisting_content_sha256=hash_release(preexisting),
        projection=pairs,
        table_count=len(pairs),
    )


def _physical_memory_bytes() -> int:
    """Total physical memory, or ``0`` when the platform will not say.

    A platform that will not answer must not silently pass the memory predicate, so the
    caller treats ``0`` as "no memory bound could be established" and refuses.
    """
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, ValueError, OSError):  # pragma: no cover - platform dependent
        return 0
    if pages <= 0 or page_size <= 0:  # pragma: no cover - platform dependent
        return 0
    return int(pages) * int(page_size)


@dataclass(frozen=True, slots=True)
class ReleaseHashEstimate:
    """The §8.2 pre-writer memory measurement for the largest table."""

    table_name: str
    row_count: int
    normalized_utf8_bytes: int
    estimated_peak_bytes: int
    physical_memory_bytes: int

    @property
    def memory_ceiling(self) -> int:
        """The lower of the absolute ceiling and one quarter of physical memory."""
        quarter = self.physical_memory_bytes // PHYSICAL_MEMORY_FRACTION_DENOMINATOR
        return min(MAXIMUM_RELEASE_HASH_BYTES, quarter) if quarter else 0

    @property
    def passes(self) -> bool:
        """Whether hashing this catalog may proceed."""
        ceiling = self.memory_ceiling
        return bool(ceiling) and self.estimated_peak_bytes <= ceiling


def estimate_release_hash_memory(connection: sqlite3.Connection) -> ReleaseHashEstimate:
    """Measure the conservative peak ``hash_table`` cost of the largest table (§8.2).

    Rows are **scanned, not buffered**: the running total is a pair of integers, so measuring
    whether the catalog can be hashed never itself materializes the catalog. The estimate is
    ``4 * normalized_utf8_bytes + 256 * row_count``, which bounds the normalized strings, the
    sort, and the per-row object overhead of one :func:`hash_table` call.

    This runs in preflight, **before** any writer opens, so an unhashable catalog refuses
    without having created a namespace, a lock, or a backup.
    """
    worst = ReleaseHashEstimate(
        table_name="",
        row_count=0,
        normalized_utf8_bytes=0,
        estimated_peak_bytes=0,
        physical_memory_bytes=_physical_memory_bytes(),
    )
    physical = worst.physical_memory_bytes
    for table in _user_tables(connection):
        columns = _live_columns(connection, table)
        if not columns:  # pragma: no cover - a table always has at least one column
            continue
        projection = ", ".join(_quote(column) for column in columns)
        rows = 0
        normalized = 0
        for row in connection.execute(f"SELECT {projection} FROM {_quote(table)}"):  # noqa: S608
            rows += 1
            # One separator between cells, matching hash_table's own rendering.
            normalized += len(columns) - 1
            for column in columns:
                normalized += len(normalize_value(row[column]).encode("utf-8"))
        estimate = _RELEASE_HASH_BYTE_MULTIPLE * normalized + _RELEASE_HASH_ROW_OVERHEAD * rows
        if estimate >= worst.estimated_peak_bytes:
            worst = ReleaseHashEstimate(
                table_name=table,
                row_count=rows,
                normalized_utf8_bytes=normalized,
                estimated_peak_bytes=estimate,
                physical_memory_bytes=physical,
            )
    return worst


# --------------------------------------------------------------------------- #
# Decision 094 §10.2 -- the hash-chained event ledger
# --------------------------------------------------------------------------- #
def _detail_rule(kind: str, event_type: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The required and optional ``details`` keys for one event of one state machine.

    ``PREFLIGHT_PASSED`` carries different facts for the two machines, so it is keyed by
    both; every other event type means the same thing wherever it appears.
    """
    if event_type == "ASSOCIATIONS_MATERIALIZED":
        return ASSOCIATION_TOTALITY_KEYS, ()
    scoped = _EVENT_DETAIL_KEYS.get(f"{kind}:{event_type}")
    if scoped is not None:
        return scoped
    rule = _EVENT_DETAIL_KEYS.get(event_type)
    if rule is None:
        message = f"event type {event_type!r} has no closed details projection"
        raise E0Error(message)
    return rule


def _check_details(kind: str, event_type: str, details: Mapping[str, object]) -> None:
    """Refuse a ``details`` object that is not exactly its closed projection.

    Decision 094 §10.2: ``details`` is not an arbitrary JSON escape hatch. A key outside the
    projection is refused, and so is a missing required key -- the second matters as much as
    the first, because an event that omits the fact it exists to record is not a smaller
    event, it is a false one.
    """
    required, optional = _detail_rule(kind, event_type)
    permitted = set(required) | set(optional)
    unknown = tuple(sorted(set(details) - permitted))
    if unknown:
        message = (
            f"{event_type} details carry key(s) {unknown} outside the closed projection "
            f"{tuple(sorted(permitted))}"
        )
        raise E0Error(message)
    missing = tuple(key for key in required if key not in details)
    if missing:
        message = f"{event_type} details are missing required key(s) {missing}"
        raise E0Error(message)


#: Value shapes an event may never carry (§10.2). Checked structurally rather than by a
#: blanket path detector: the values here are counts, digests, enum tokens, and root-relative
#: names, so anything that looks like an absolute path, a home reference, or an address is a
#: defect in the caller rather than a legitimate value needing an exemption.
_PROHIBITED_DETAIL_MARKERS: Final[tuple[str, ...]] = ("/", "\\", "~", "@", "\n")


def _check_detail_values(details: Mapping[str, object]) -> None:
    """Refuse an absolute path, a home reference, an address, or a multiline value."""
    for key, value in details.items():
        if value is None or isinstance(value, (bool, int, float)):
            continue
        if not isinstance(value, str):
            message = f"event detail {key!r} must be a string or a number"
            raise E0Error(message)
        if key == "relative_path":
            # The one field that legitimately contains separators. It is root-relative by
            # construction and is checked for that rather than for the absence of a slash.
            if value.startswith(("/", "~")) or ".." in Path(value).parts:
                message = "event detail 'relative_path' must be a private-root-relative path"
                raise E0Error(message)
            continue
        if any(marker in value for marker in _PROHIBITED_DETAIL_MARKERS):
            message = (
                f"event detail {key!r} carries a path, address, or newline; ledger details are "
                f"non-secret counts, digests, and tokens only"
            )
            raise E0Error(message)


def _event_digest(event: Mapping[str, object]) -> str:
    """``SHA256`` over the canonical event bytes with ``event_sha256`` omitted (§10.2).

    Omitting the field from its own preimage is the whole rule: no digest, identifier, event
    hash, receipt id, terminal id, catalog-state hash, or token may contain its own value in
    its preimage (§11).
    """
    preimage = {key: value for key, value in event.items() if key != "event_sha256"}
    return hashlib.sha256(canonical_bytes(preimage)).hexdigest()


class EventLedger:
    """One append-only, hash-chained JSONL ledger for one run namespace.

    Each append is newline-terminated and fsynced **before the next authoritative boundary**,
    so a crash can lose at most the event for a boundary that had already committed -- which
    is exactly the disclosed commit-before-event window the terminal schemas model, rather
    than an unbounded unknown.
    """

    def __init__(self, path: Path, namespace: str, kind: str) -> None:
        self._path = path
        self._namespace = validate_namespace(namespace)
        self._kind = kind
        self._sequence = 0
        self._previous: str | None = None
        self._head: str | None = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def event_count(self) -> int:
        return self._sequence

    @property
    def head_event_sha256(self) -> str | None:
        """The last appended event's digest, which the terminal record binds."""
        return self._head

    def append(
        self, event_type: str, details: Mapping[str, object], *, observed_at_utc: str
    ) -> Mapping[str, object]:
        """Append one validated event, fsync it, and return it.

        Raises:
            E0Error: the event type or its ``details`` is outside the closed schema.
        """
        permitted = TRANSITION_EVENT_TYPES if self._kind == "TRANSITION" else E0_EVENT_TYPES
        if event_type not in permitted:
            message = (
                f"{event_type!r} is not an allowed {self._kind.lower()} event; the vocabulary "
                f"is closed at {permitted}"
            )
            raise E0Error(message)
        _check_details(self._kind, event_type, details)
        _check_detail_values(details)

        self._sequence += 1
        event: dict[str, object] = {
            "schema_version": EVENT_LEDGER_SCHEMA_VERSION,
            "run_namespace": self._namespace,
            "sequence": self._sequence,
            "event_type": event_type,
            "observed_at_utc": observed_at_utc,
            "details": dict(details),
        }
        if self._previous is not None:
            event["previous_event_sha256"] = self._previous
        event["event_sha256"] = _event_digest(event)
        payload = canonical_bytes(event)

        descriptor = os.open(self._path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, _FILE_MODE)
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        self._path.chmod(_FILE_MODE)
        if self._sequence == 1:
            _fsync_directory(self._path.parent)

        self._previous = str(event["event_sha256"])
        self._head = self._previous
        return event


def read_event_ledger(path: Path, *, kind: str) -> tuple[Mapping[str, object], ...]:
    """Read and fully verify a ledger: chain, ordering, contiguity, and every digest.

    Detects truncation (a missing tail is only detectable against the terminal record's
    recorded count, which :func:`validate_transition_terminal` and :func:`validate_e0_terminal`
    compare), reordering (a sequence that is not contiguous from 1), and mutation (an event
    whose recomputed digest or recorded predecessor disagrees).

    Raises:
        LedgerIntegrityError: the ledger is not a valid chain.
    """
    permitted = TRANSITION_EVENT_TYPES if kind == "TRANSITION" else E0_EVENT_TYPES
    events: list[Mapping[str, object]] = []
    previous: str | None = None
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        message = "the event ledger's final line is not newline-terminated; it is truncated"
        raise LedgerIntegrityError(message)
    for index, line in enumerate(raw.splitlines(), start=1):
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            message = f"event ledger line {index} is not readable UTF-8 JSON: {exc}"
            raise LedgerIntegrityError(message) from exc
        if not isinstance(event, dict):
            message = f"event ledger line {index} is not a JSON object"
            raise LedgerIntegrityError(message)
        if canonical_bytes(event) != line + b"\n":
            message = f"event ledger line {index} is not in canonical form"
            raise LedgerIntegrityError(message)
        if event.get("schema_version") != EVENT_LEDGER_SCHEMA_VERSION:
            message = f"event ledger line {index} declares an unknown schema version"
            raise LedgerIntegrityError(message)
        if event.get("sequence") != index:
            message = (
                f"event ledger line {index} declares sequence {event.get('sequence')!r}; "
                f"sequences are positive and contiguous, so this ledger is reordered or gapped"
            )
            raise LedgerIntegrityError(message)
        event_type = event.get("event_type")
        if event_type not in permitted:
            message = f"event ledger line {index} declares event type {event_type!r}"
            raise LedgerIntegrityError(message)
        details = event.get("details")
        if not isinstance(details, dict):
            message = f"event ledger line {index} has no details object"
            raise LedgerIntegrityError(message)
        try:
            _check_details(kind, str(event_type), details)
        except E0Error as exc:
            message = f"event ledger line {index}: {exc}"
            raise LedgerIntegrityError(message) from exc
        recorded_previous = event.get("previous_event_sha256")
        if recorded_previous != previous:
            message = (
                f"event ledger line {index} binds predecessor {recorded_previous!r}; the "
                f"preceding event hashes to {previous!r}, so the chain is broken"
            )
            raise LedgerIntegrityError(message)
        expected = _event_digest(event)
        if event.get("event_sha256") != expected:
            message = f"event ledger line {index} does not recompute over its own preimage"
            raise LedgerIntegrityError(message)
        previous = expected
        events.append(event)
    return tuple(events)


# --------------------------------------------------------------------------- #
# Decision 094 §§8.1, 9.2, 11 -- closed terminal schemas and their identities
# --------------------------------------------------------------------------- #
TERMINAL_STATUSES: Final[tuple[str, ...]] = ("complete", "failed", "interrupted")

#: The two fields §11 omits from the identity preimage. ``result_token`` is derived *after*
#: ``terminal_record_id`` and contains it, so including either in the preimage would make the
#: record contain itself -- the exact self-reference §11 forbids.
_IDENTITY_EXCLUDED: Final[frozenset[str]] = frozenset({"terminal_record_id", "result_token"})

#: Fields every terminal record carries, whatever its status (§8.1 first row).
_TRANSITION_ALWAYS: Final[tuple[str, ...]] = (
    "schema_version",
    "record_type",
    "run_namespace",
    "command_name",
    "command_version",
    "status",
    "started_at_utc",
    "completed_at_utc",
    "owner_authority_sha256",
    "catalog_relative_path",
    "pre_migration_chain",
    "target_migration_chain",
    "packaged_migration_sha256",
    "precondition_counts",
    "pre_integrity",
    "pre_catalog_logical_sha256",
    "pre_preexisting_content_sha256",
    "event_ledger",
    "execution_receipt_id",
    "actual_logical_request_count",
    "actual_physical_attempt_count",
    "terminal_record_id",
    "result_token",
)

#: Fields whose presence is conditioned on status or on a durable event (§8.1 second table).
_TRANSITION_CONDITIONAL: Final[tuple[str, ...]] = (
    "post_migration_chain",
    "post_integrity",
    "post_preexisting_content_sha256",
    "backup",
    "applied_migrations",
    "failure",
)

_E0_ALWAYS: Final[tuple[str, ...]] = (
    "schema_version",
    "record_type",
    "run_namespace",
    "command_name",
    "command_version",
    "status",
    "started_at_utc",
    "completed_at_utc",
    "owner_authority_sha256",
    "catalog_relative_path",
    "pre_migration_chain",
    "transition_terminal_record_id",
    "transition_result_token",
    "configuration_fingerprint",
    "input_observation_set_sha256",
    "pre_e0_catalog_logical_sha256",
    "source_results",
    "source_result_counts",
    "pre_integrity",
    "event_ledger",
    "execution_receipt_id",
    "actual_logical_request_count",
    "actual_physical_attempt_count",
    "terminal_record_id",
    "result_token",
)

_E0_CONDITIONAL: Final[tuple[str, ...]] = (
    "post_migration_chain",
    "backup",
    "association_totality",
    "table_hashes",
    "plan_parser_state_hash",
    "e0_catalog_state_sha256",
    "post_integrity",
    "failure",
)

#: Accepted Decision 099 R96, from the Decision 094 §8.1 and §9.2 conditional-presence tables:
#: which terminal fields a **failed or interrupted** record may carry, keyed by the durable
#: event that permits them. In-memory assignment is not evidence that an event became durable,
#: so a disclosed failure derives its permitted field set from the ledger rather than from the
#: order in which the execute path happened to assign things.
_TRANSITION_EVENT_CONDITIONED_FIELDS: Final[Mapping[str, tuple[str, ...]]] = {
    "BACKUP_VERIFIED": ("backup",),
    "POSTCHECK_PASSED": ("post_preexisting_content_sha256",),
}

_E0_EVENT_CONDITIONED_FIELDS: Final[Mapping[str, tuple[str, ...]]] = {
    "BACKUP_VERIFIED": ("backup",),
    "ASSOCIATIONS_MATERIALIZED": ("association_totality",),
    "VALIDATION_PASSED": (
        "table_hashes",
        "plan_parser_state_hash",
        "e0_catalog_state_sha256",
        "post_integrity",
    ),
}

#: The fields §8.1 and §9.2 condition on ``failure.catalog_state_observed`` instead of on a
#: durable event. ``applied_migrations`` is deliberately here and not above: §8.1 lets it lead
#: the ledger by exactly one migration inside the disclosed commit-before-event window, so
#: pruning it against ``MIGRATION_*_COMMITTED`` would delete the very disclosure that window
#: exists to make.
_CATALOG_OBSERVED_FIELDS: Final[Mapping[str, tuple[str, ...]]] = {
    "catalog_transition": ("post_migration_chain", "post_integrity", "applied_migrations"),
    "m3_3_e0_offline_parse": ("post_migration_chain",),
}

_INTEGRITY_KEYS: Final[tuple[str, ...]] = (
    "quick_check",
    "integrity_check",
    "foreign_key_violations",
)
_BACKUP_KEYS: Final[tuple[str, ...]] = (
    "relative_path",
    "byte_length",
    "file_sha256",
    "catalog_logical_sha256",
    "integrity",
)
_LEDGER_KEYS: Final[tuple[str, ...]] = ("relative_path", "event_count", "head_event_sha256")
_FAILURE_KEYS: Final[tuple[str, ...]] = (
    "reason_code",
    "reason_detail",
    "catalog_state_observed",
)
_SOURCE_RESULT_REQUIRED: Final[tuple[str, ...]] = (
    "census_run_id",
    "source_instance_id",
    "source_id",
    "disposition",
    "parser_state_before",
    "parser_state_after",
    "parsed_records",
    "quarantined_records",
    "already_present",
    "ledger_event_present",
)
_SOURCE_RESULT_OPTIONAL: Final[tuple[str, ...]] = ("observation_id", "parser_run_id")
SOURCE_RESULT_COUNT_KEYS: Final[tuple[str, ...]] = (
    "planned_source_count",
    "required_parse_count",
    "accepted_unavailable_count",
    "validation_or_provenance_only_count",
    "parser_completed_count",
    "parser_failed_count",
    "parser_quarantined_count",
    "parsed_record_count",
    "quarantined_record_count",
    "full_index_registrant_observation_count",
    "full_index_unbound_accession_count",
    "accession_resolution_count",
    "submissions_membership_observation_count",
    "substantive_membership_observation_count",
)
SOURCE_DISPOSITIONS: Final[tuple[str, ...]] = (
    "E0_REQUIRED_PARSE",
    "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE",
    "E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY",
)


def _as_count(value: object, label: str) -> int:
    """Narrow a value a closed schema has already typed as a count, or refuse.

    A parsed JSON document yields ``object``, so the narrowing has to happen somewhere. Doing
    it once, and failing closed, is better than silencing the type checker at each call site:
    a terminal record carrying a string where a count belongs is a real defect.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"{label} must be an integer, found {type(value).__name__}"
        raise TerminalValidationError(message)
    return value


def _as_list(value: object, label: str) -> list[object]:
    """Narrow a value a closed schema has already typed as an ordered list, or refuse."""
    if not isinstance(value, list):
        message = f"{label} must be an ordered list"
        raise TerminalValidationError(message)
    return value


def _as_object(value: object, label: str) -> Mapping[str, object]:
    """Narrow a value a closed schema has already typed as an object, or refuse."""
    if not isinstance(value, Mapping):
        message = f"{label} must be a JSON object"
        raise TerminalValidationError(message)
    return value


def compute_terminal_record_id(document: Mapping[str, object]) -> str:
    """``SHA256`` of the canonical bytes with ``terminal_record_id`` and ``result_token`` omitted.

    Decision 094 §11 items 1 and 4: recomputation omits exactly the same two fields and must
    reproduce the persisted identity. Nothing else is excluded -- an identity that ignored a
    third field would be reproducible and still not bind the record.
    """
    preimage = {key: value for key, value in document.items() if key not in _IDENTITY_EXCLUDED}
    return hashlib.sha256(canonical_bytes(preimage)).hexdigest()


def result_token(record_type: str, status: str, terminal_record_id: str) -> str:
    """The §11 item 2 token, derived **only after** the identity it names.

    The ordering is the point: the token contains the identity, so the identity cannot
    contain the token. Deriving them in the other order, or in one step, would produce
    exactly the self-referential preimage §11 forbids.
    """
    if status not in TERMINAL_STATUSES:
        message = f"terminal status {status!r} is not one of {TERMINAL_STATUSES}"
        raise TerminalValidationError(message)
    prefix = (
        "M3_3_PRE_E0_CATALOG_TRANSITION"
        if record_type == "catalog_transition"
        else "M3_3_E0_OFFLINE_PARSE"
    )
    return f"{prefix}_{status.upper()}:{terminal_record_id}"


def _require_closed_object(
    label: str, value: object, keys: Sequence[str], *, optional: Sequence[str] = ()
) -> Mapping[str, object]:
    """Refuse an object that is not exactly its closed key set."""
    if not isinstance(value, Mapping):
        message = f"{label} must be a JSON object"
        raise TerminalValidationError(message)
    permitted = set(keys) | set(optional)
    unknown = tuple(sorted(set(value) - permitted))
    if unknown:
        message = f"{label} carries key(s) {unknown} outside its closed set"
        raise TerminalValidationError(message)
    missing = tuple(key for key in keys if key not in value)
    if missing:
        message = f"{label} is missing required key(s) {missing}"
        raise TerminalValidationError(message)
    return value


def _require_no_placeholder(document: Mapping[str, object]) -> None:
    """Refuse ``null``, ``"N/A"``, and every other stand-in for an omission (§8.1, §9.2).

    An inapplicable field is **absent**. A value that says "not applicable" is worse than an
    absent one: the conditional-presence table can prove an absence lawful, and cannot prove
    a placeholder anything at all.
    """
    for key, value in document.items():
        if value is None:
            message = f"{key} is present as null; an inapplicable field is omitted"
            raise TerminalValidationError(message)
        if isinstance(value, str) and value.strip().casefold() in {"", "-", "n/a", "null"}:
            message = f"{key} carries the placeholder {value!r}; omit the field instead"
            raise TerminalValidationError(message)
        if isinstance(value, Mapping):
            _require_no_placeholder(value)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping):
                    _require_no_placeholder(item)


def _conditional_presence(
    document: Mapping[str, object],
    *,
    field_name: str,
    required: bool,
) -> None:
    """Enforce one conditional-presence row exactly: present iff required."""
    present = field_name in document
    if required and not present:
        message = f"{field_name} is required for this status and event set, and is missing"
        raise TerminalValidationError(message)
    if not required and present:
        message = (
            f"{field_name} is present but this status and event set does not permit it; no "
            f"other omission is valid and no absent value is represented by a placeholder"
        )
        raise TerminalValidationError(message)


def _failure_shape(document: Mapping[str, object]) -> Mapping[str, object]:
    """The §8.1 closed failure object, with ``interruption_state`` iff interrupted."""
    status = document["status"]
    optional = ("interruption_state",) if status == "interrupted" else ()
    failure = _require_closed_object(
        "failure", document["failure"], _FAILURE_KEYS, optional=optional
    )
    if status == "interrupted" and "interruption_state" not in failure:
        message = "failure.interruption_state is required when status is 'interrupted'"
        raise TerminalValidationError(message)
    if not isinstance(failure["catalog_state_observed"], bool):
        message = "failure.catalog_state_observed must be a boolean"
        raise TerminalValidationError(message)
    return failure


def _validate_common(
    document: Mapping[str, object],
    *,
    schema_version: str,
    record_type: str,
    command_name: str,
    always: Sequence[str],
    conditional: Sequence[str],
    event_types: frozenset[str],
) -> tuple[str, bool]:
    """Validate the parts both terminal schemas share; return ``(status, catalog_observed)``."""
    _require_closed_object(f"{record_type} terminal record", document, always, optional=conditional)
    _require_no_placeholder(document)
    if document["schema_version"] != schema_version:
        message = f"terminal schema_version must be {schema_version!r}"
        raise TerminalValidationError(message)
    if document["record_type"] != record_type:
        message = f"terminal record_type must be {record_type!r}"
        raise TerminalValidationError(message)
    if document["command_name"] != command_name:
        message = f"terminal command_name must be {command_name!r}"
        raise TerminalValidationError(message)
    status = document["status"]
    if status not in TERMINAL_STATUSES:
        message = f"terminal status must be one of {TERMINAL_STATUSES}"
        raise TerminalValidationError(message)
    if document["catalog_relative_path"] != OPERATIONAL_CATALOG_RELATIVE_PATH:
        message = "terminal catalog_relative_path is not the fixed accepted catalog path"
        raise TerminalValidationError(message)
    for count in ("actual_logical_request_count", "actual_physical_attempt_count"):
        if document[count] != 0:
            message = f"{count} must be exactly 0; this command places nothing on the wire"
            raise TerminalValidationError(message)
    validate_namespace(str(document["run_namespace"]))
    _require_closed_object("pre_integrity", document["pre_integrity"], _INTEGRITY_KEYS)
    ledger = _require_closed_object("event_ledger", document["event_ledger"], _LEDGER_KEYS)
    if _as_count(ledger["event_count"], "event_ledger.event_count") < 1:
        message = "event_ledger.event_count must be positive; a run always records events"
        raise TerminalValidationError(message)

    _conditional_presence(document, field_name="failure", required=status != "complete")
    catalog_observed = True
    if status != "complete":
        failure = _failure_shape(document)
        catalog_observed = bool(failure["catalog_state_observed"])
        state = failure.get("interruption_state")
        if state is not None and state not in INTERRUPTION_STATES_V4:
            message = f"failure.interruption_state {state!r} is outside the closed vocabulary"
            raise TerminalValidationError(message)

    backup_present = "BACKUP_VERIFIED" in event_types
    _conditional_presence(
        document, field_name="backup", required=status == "complete" or backup_present
    )
    if "backup" in document:
        backup = _require_closed_object("backup", document["backup"], _BACKUP_KEYS)
        _require_closed_object("backup.integrity", backup["integrity"], _INTEGRITY_KEYS)

    identity = compute_terminal_record_id(document)
    if document["terminal_record_id"] != identity:
        message = (
            "terminal_record_id does not recompute over its excluding preimage; the record "
            "was altered after it was written"
        )
        raise TerminalValidationError(message)
    expected_token = result_token(record_type, str(status), identity)
    if document["result_token"] != expected_token:
        message = "result_token does not derive from the recomputed terminal_record_id"
        raise TerminalValidationError(message)
    return str(status), catalog_observed


def validate_transition_terminal(
    document: Mapping[str, object], *, event_types: frozenset[str]
) -> None:
    """Validate one ``catalog_transition`` terminal record exactly (Decision 094 §8.1).

    Args:
        document: The parsed terminal record.
        event_types: The event types actually present in the run's durable ledger. The
            conditional-presence table is written against durable events, not against what
            the record claims, so the two are cross-checked rather than one trusted.

    Raises:
        TerminalValidationError: any closed-set, presence, ordering, or identity rule failed.
    """
    status, catalog_observed = _validate_common(
        document,
        schema_version=TRANSITION_TERMINAL_SCHEMA_VERSION,
        record_type="catalog_transition",
        command_name=TRANSITION_COMMAND_NAME,
        always=_TRANSITION_ALWAYS,
        conditional=_TRANSITION_CONDITIONAL,
        event_types=event_types,
    )
    complete = status == "complete"
    _require_closed_object(
        "packaged_migration_sha256", document["packaged_migration_sha256"], ("0014", "0015")
    )
    for name in ("pre_migration_chain", "target_migration_chain"):
        _require_chain(document[name], name)

    observed = complete or catalog_observed
    _conditional_presence(document, field_name="applied_migrations", required=observed)
    _conditional_presence(document, field_name="post_migration_chain", required=observed)
    _conditional_presence(document, field_name="post_integrity", required=observed)
    _conditional_presence(
        document,
        field_name="post_preexisting_content_sha256",
        required=complete or "POSTCHECK_PASSED" in event_types,
    )
    if "post_integrity" in document:
        _require_closed_object("post_integrity", document["post_integrity"], _INTEGRITY_KEYS)
    if "post_migration_chain" in document:
        _require_chain(document["post_migration_chain"], "post_migration_chain")
    if "applied_migrations" in document:
        applied = _as_list(document["applied_migrations"], "applied_migrations")
        if len(applied) > 2:
            message = (
                "applied_migrations is the actual observed chain delta in order -- zero, one, "
                "or two entries -- and never repeats the thirteen predecessor records"
            )
            raise TerminalValidationError(message)
        for entry in applied:
            _require_closed_object(
                "applied_migrations entry", entry, ("version", "name", "checksum_sha256")
            )
        versions = [
            _as_count(_as_object(entry, "applied_migrations entry")["version"], "version")
            for entry in applied
        ]
        if versions != sorted(versions) or any(
            version not in (TRANSITION_SOURCE_HEAD + 1, TRANSITION_TARGET_HEAD)
            for version in versions
        ):
            message = "applied_migrations must be an ordered subset of exactly 0014 then 0015"
            raise TerminalValidationError(message)

    if complete:
        _require_exact_chain(document["post_migration_chain"], TRANSITION_TARGET_HEAD)
        exact = [
            _as_count(_as_object(entry, "applied_migrations entry")["version"], "version")
            for entry in _as_list(document["applied_migrations"], "applied_migrations")
        ]
        if exact != [TRANSITION_SOURCE_HEAD + 1, TRANSITION_TARGET_HEAD]:
            message = "a complete transition applied exactly 0014 then 0015"
            raise TerminalValidationError(message)
        _require_integrity_passed(document["pre_integrity"], "pre_integrity")
        _require_integrity_passed(document["post_integrity"], "post_integrity")
        pre_content = document["pre_preexisting_content_sha256"]
        if document["post_preexisting_content_sha256"] != pre_content:
            message = (
                "post_preexisting_content_sha256 differs from pre_preexisting_content_sha256; "
                "the schema transition changed a pre-existing application row"
            )
            raise TerminalValidationError(message)
        for event in ("MIGRATION_0014_COMMITTED", "MIGRATION_0015_COMMITTED"):
            if event not in event_types:
                message = f"a complete transition records a durable {event} event"
                raise TerminalValidationError(message)


def validate_e0_terminal(document: Mapping[str, object], *, event_types: frozenset[str]) -> None:
    """Validate one ``m3_3_e0_offline_parse`` terminal record exactly (Decision 094 §9.2).

    Raises:
        TerminalValidationError: any closed-set, presence, totality, or identity rule failed.
    """
    status, catalog_observed = _validate_common(
        document,
        schema_version=E0_TERMINAL_SCHEMA_VERSION,
        record_type="m3_3_e0_offline_parse",
        command_name=E0_COMMAND_NAME,
        always=_E0_ALWAYS,
        conditional=_E0_CONDITIONAL,
        event_types=event_types,
    )
    complete = status == "complete"
    _require_chain(document["pre_migration_chain"], "pre_migration_chain")
    _conditional_presence(
        document, field_name="post_migration_chain", required=complete or catalog_observed
    )
    if "post_migration_chain" in document:
        _require_chain(document["post_migration_chain"], "post_migration_chain")

    validated = complete or "VALIDATION_PASSED" in event_types
    for name in (
        "table_hashes",
        "plan_parser_state_hash",
        "e0_catalog_state_sha256",
        "post_integrity",
    ):
        _conditional_presence(document, field_name=name, required=validated)
    _conditional_presence(
        document,
        field_name="association_totality",
        required=complete or "ASSOCIATIONS_MATERIALIZED" in event_types,
    )
    if "association_totality" in document:
        totality = _require_closed_object(
            "association_totality", document["association_totality"], ASSOCIATION_TOTALITY_KEYS
        )
        _require_totality_invariants(totality)
    if "post_integrity" in document:
        _require_closed_object("post_integrity", document["post_integrity"], _INTEGRITY_KEYS)
    if "table_hashes" in document:
        entries = _as_list(document["table_hashes"], "table_hashes")
        names = []
        for entry in entries:
            record = _require_closed_object(
                "table_hashes entry",
                entry,
                ("table_name", "columns", "row_count", "normalized_content_sha256"),
            )
            names.append(str(record["table_name"]))
        if names != sorted(names):
            message = "table_hashes must be ordered by table name"
            raise TerminalValidationError(message)

    counts = _require_closed_object(
        "source_result_counts", document["source_result_counts"], SOURCE_RESULT_COUNT_KEYS
    )
    results = _as_list(document["source_results"], "source_results")
    seen: set[tuple[str, str]] = set()
    ordered: list[tuple[str, str]] = []
    for entry in results:
        record = _require_closed_object(
            "source_results entry", entry, _SOURCE_RESULT_REQUIRED, optional=_SOURCE_RESULT_OPTIONAL
        )
        if record["disposition"] not in SOURCE_DISPOSITIONS:
            message = f"source_results disposition {record['disposition']!r} is not an R18 value"
            raise TerminalValidationError(message)
        if not isinstance(record["ledger_event_present"], bool):
            message = "source_results.ledger_event_present must be a boolean"
            raise TerminalValidationError(message)
        key = (str(record["census_run_id"]), str(record["source_instance_id"]))
        if key in seen:
            message = f"source_results repeats the pair {key}; each appears exactly once"
            raise TerminalValidationError(message)
        seen.add(key)
        ordered.append(key)
    if ordered != sorted(ordered):
        message = "source_results must be ordered by (census_run_id, source_instance_id)"
        raise TerminalValidationError(message)

    disposition_total = sum(
        _as_count(counts[key], key)
        for key in (
            "required_parse_count",
            "accepted_unavailable_count",
            "validation_or_provenance_only_count",
        )
    )
    if disposition_total != len(results):
        message = (
            f"the three disposition counts sum to {disposition_total} but source_results holds "
            f"{len(results)} record(s)"
        )
        raise TerminalValidationError(message)

    if complete:
        if len(results) != PLANNED_SOURCE_COUNT:
            message = (
                f"a complete E0 terminal reconciles {PLANNED_SOURCE_COUNT}/{PLANNED_SOURCE_COUNT} "
                f"planned sources; this one carries {len(results)}"
            )
            raise TerminalValidationError(message)
        if (
            _as_count(counts["planned_source_count"], "planned_source_count")
            != PLANNED_SOURCE_COUNT
        ):
            message = f"planned_source_count must be {PLANNED_SOURCE_COUNT}"
            raise TerminalValidationError(message)
        if any(
            not _as_object(entry, "source_results entry")["ledger_event_present"]
            for entry in results
        ):
            message = "every source_results row of a complete run has ledger_event_present true"
            raise TerminalValidationError(message)
        _require_exact_chain(document["post_migration_chain"], TRANSITION_TARGET_HEAD)
        _require_integrity_passed(document["pre_integrity"], "pre_integrity")
        _require_integrity_passed(document["post_integrity"], "post_integrity")
    else:
        declared = _as_object(document.get("failure", {}), "failure").get("interruption_state")
        for entry in results:
            record = _as_object(entry, "source_results entry")
            if not record["ledger_event_present"] and (
                declared != "after_e0_source_commit_before_event"
            ):
                message = (
                    "a source_results row without its durable ledger event is lawful only in "
                    "the disclosed commit-before-event window, which must be stated as the "
                    "interruption state 'after_e0_source_commit_before_event'"
                )
                raise TerminalValidationError(message)


def _require_chain(value: object, label: str) -> tuple[int, ...]:
    """Refuse a migration chain that is not an ordered contiguous integer array from 1."""
    if not isinstance(value, list) or not value:
        message = f"{label} must be a non-empty ordered integer array"
        raise TerminalValidationError(message)
    versions = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            message = f"{label} must contain integers only"
            raise TerminalValidationError(message)
        versions.append(item)
    if tuple(versions) != tuple(range(1, len(versions) + 1)):
        message = f"{label} must be contiguous from 1; found {tuple(versions)}"
        raise TerminalValidationError(message)
    return tuple(versions)


def _require_exact_chain(value: object, head: int) -> None:
    """Refuse a chain whose head is not exactly ``head``."""
    versions = _require_chain(value, "migration chain")
    if versions[-1] != head:
        message = f"the migration chain must end exactly at {head:04d}; found {versions[-1]:04d}"
        raise TerminalValidationError(message)


def _require_integrity_passed(value: object, label: str) -> None:
    """Refuse an integrity object that does not pass all three gates."""
    report = _require_closed_object(label, value, _INTEGRITY_KEYS)
    if (
        report["quick_check"] != "ok"
        or report["integrity_check"] != "ok"
        or _as_count(report["foreign_key_violations"], f"{label}.foreign_key_violations") != 0
    ):
        message = f"{label} did not pass all three SQLite integrity gates"
        raise TerminalValidationError(message)


#: The six §9.5 counts fixed at zero. A nonzero one is a totality failure, never a state.
_TOTALITY_ZERO_KEYS: Final[tuple[str, ...]] = (
    "established_zero_relation_count",
    "singleton_scalar_mismatch_count",
    "multi_nonnull_scalar_count",
    "orphan_relation_count",
    "invalid_cik_rendering_count",
    "association_provenance_failure_count",
)


def _require_totality_invariants(totality: Mapping[str, object]) -> None:
    """Refuse an association totality that breaks a §9.5 invariant."""
    broken = tuple(key for key in _TOTALITY_ZERO_KEYS if _as_count(totality[key], key) != 0)
    if broken:
        message = f"association_totality breaks its zero-fixed invariant(s): {broken}"
        raise TerminalValidationError(message)
    established = _as_count(totality["established_accession_count"], "established")
    unestablished = _as_count(totality["unestablished_accession_count"], "unestablished")
    if established + unestablished != _as_count(totality["census_accession_count"], "total"):
        message = "association_totality's first three counts must partition every accession"
        raise TerminalValidationError(message)
    singleton = _as_count(totality["established_singleton_count"], "singleton")
    multi = _as_count(totality["established_multi_count"], "multi")
    if singleton + multi != established:
        message = "established singleton and multi counts must sum to the established count"
        raise TerminalValidationError(message)


# --------------------------------------------------------------------------- #
# Decision 094 §§5.2, 9.1 -- strictly read-only preflight
# --------------------------------------------------------------------------- #
def _read_only(catalog_path: Path) -> AbstractContextManager[sqlite3.Connection]:
    """A strictly read-only connection context manager for the catalog.

    Imported at call time rather than at module scope so ``m3/e0.py``'s own import graph stays
    as small as the no-network proof needs it to be.
    """
    from disclosure_drift.storage.catalog import strictly_read_only_connection

    return strictly_read_only_connection(catalog_path)


def input_observation_set_digest(connection: sqlite3.Connection) -> str:
    """The §9.3 ``input_observation_set_sha256``, over the accepted plan rows.

    SHA-256 over canonical JSON for the plan rows ordered by
    ``(census_run_id, source_instance_id)``, projecting exactly ``census_run_id``,
    ``source_instance_id``, ``source_id``, nullable ``observation_id``, and -- when bound --
    the accepted observation's ``request_identity``, ``logical_sha256``, ``parser_version``,
    and ``outcome``. Computed before any write and independently reproduced afterwards, so it
    proves E0 consumed the input set it claimed rather than one it created.
    """
    rows = connection.execute(
        "SELECT p.census_run_id, p.source_instance_id, p.source_id, p.observation_id, "
        "o.request_identity, o.logical_sha256, o.parser_version, o.outcome "
        "FROM census_plan_sources AS p "
        "LEFT JOIN census_source_observations AS o ON o.observation_id = p.observation_id "
        "ORDER BY p.census_run_id, p.source_instance_id"
    ).fetchall()
    projected: list[Mapping[str, object]] = []
    for row in rows:
        entry: dict[str, object] = {
            "census_run_id": str(row["census_run_id"]),
            "source_instance_id": str(row["source_instance_id"]),
            "source_id": str(row["source_id"]),
            "observation_id": None if row["observation_id"] is None else str(row["observation_id"]),
        }
        if row["observation_id"] is not None:
            for field_name in ("request_identity", "logical_sha256", "parser_version", "outcome"):
                value = row[field_name]
                entry[field_name] = None if value is None else str(value)
        projected.append(entry)
    payload = json.dumps(projected, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(f"{payload}\n".encode()).hexdigest()


def _load_terminal(
    terminal_path: Path, ledger_path: Path, *, kind: str
) -> tuple[Mapping[str, object], tuple[Mapping[str, object], ...]]:
    """Read, chain-verify, and schema-validate one run's ledger and terminal record.

    The ledger is verified **first**: the terminal's conditional-presence rules are written
    against durable events, so validating the record against a ledger that has not itself been
    proved intact would let a mutated ledger authorize a malformed record.
    """
    events = read_event_ledger(ledger_path, kind=kind)
    raw = terminal_path.read_bytes()
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        message = f"the terminal record is not readable UTF-8 JSON: {exc}"
        raise TerminalValidationError(message) from exc
    if not isinstance(document, dict):
        message = "the terminal record is not a JSON object"
        raise TerminalValidationError(message)
    if canonical_bytes(document) != raw:
        message = "the terminal record's stored bytes are not in canonical form"
        raise TerminalValidationError(message)
    event_types = frozenset(str(event["event_type"]) for event in events)
    if kind == "TRANSITION":
        validate_transition_terminal(document, event_types=event_types)
    else:
        validate_e0_terminal(document, event_types=event_types)
    bound = _as_object(document["event_ledger"], "event_ledger")
    if _as_count(bound["event_count"], "event_ledger.event_count") != len(events):
        message = (
            f"the terminal record binds {bound['event_count']} event(s) but the ledger holds "
            f"{len(events)}; the ledger is truncated or was appended to after the freeze"
        )
        raise LedgerIntegrityError(message)
    if events and bound["head_event_sha256"] != events[-1]["event_sha256"]:
        message = "the terminal record does not bind the ledger's actual head event"
        raise LedgerIntegrityError(message)
    return document, events


@dataclass(frozen=True, slots=True)
class PreflightReport:
    """One preflight's verdict and the non-secret facts it measured.

    ``lines`` is what the operator sees. Every entry is a count, a digest, an enum token, or
    a root-relative name -- never an absolute path, an evidence-root name, or an environment
    value, because a preflight report is printed and §7.1 forbids the value ever being shown.
    """

    passed: bool
    refusals: tuple[str, ...]
    facts: Mapping[str, object]

    @property
    def lines(self) -> tuple[str, ...]:
        """The rendered report, refusals last so the failure is the last thing read."""
        rendered = [f"  {key:<38}: {value}" for key, value in self.facts.items()]
        rendered.extend(f"  REFUSED: {reason}" for reason in self.refusals)
        return tuple(rendered)

    def require(self) -> None:
        """Raise unless every predicate passed.

        Raises:
            PreflightRefusalError: at least one predicate is false.
        """
        if self.passed:
            return
        message = "preflight refused: " + "; ".join(self.refusals)
        raise PreflightRefusalError(message)


def _lease_state(lock_directory: Path) -> tuple[bool, str | None, bool]:
    """Inspect the writer lease **without creating or acquiring anything** (§5.2 predicate 9).

    Returns ``(present, recorded_state, shared_lock_available)``. An absent lease passes the
    predicate outright: Decision 094 finding m1 is explicit that a read-only preflight must
    not create the lock file to find out whether it could be taken, and a shared non-blocking
    ``flock`` on an existing file is non-mutating.
    """
    path = lock_directory / _LEASE_FILENAME
    if not path.exists():
        return False, None, True
    if fcntl is None:  # pragma: no cover - supported platforms are Unix
        return True, None, False
    descriptor = os.open(path, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            return True, None, False
        try:
            raw = os.read(descriptor, 64 * 1024)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)
    try:
        recorded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return True, None, True
    state = recorded.get("state") if isinstance(recorded, dict) else None
    return True, (str(state) if state is not None else None), True


def _empty_state_counts(connection: sqlite3.Connection) -> Mapping[str, int]:
    """Row counts for every §1.3 guard table that exists in this catalog."""
    counts: dict[str, int] = {}
    for table in EMPTY_STATE_TABLES:
        if not _table_exists(connection, table):
            continue
        counts[table] = int(
            connection.execute(f"SELECT COUNT(*) FROM {_quote(table)}").fetchone()[0]  # noqa: S608
        )
    return counts


def _packaged_target_migrations() -> tuple[Migration, ...]:
    """The packaged ``0014`` and ``0015``, checked against §1.1's digests.

    A drifted migration file is refused here rather than applied and discovered afterwards,
    and ``0016`` is refused by construction: this selects by exact version, so a sixteenth
    packaged migration is never included in a prefix this module applies.
    """
    inventory = {migration.version: migration for migration in available_migrations()}
    selected: list[Migration] = []
    for version in (TRANSITION_SOURCE_HEAD + 1, TRANSITION_TARGET_HEAD):
        migration = inventory.get(version)
        if migration is None:
            message = f"packaged migration {version:04d} is absent"
            raise PreflightRefusalError(message)
        expected = PACKAGED_MIGRATION_SHA256[f"{version:04d}"]
        if migration.checksum_sha256 != expected:
            message = (
                f"packaged migration {version:04d} ({migration.name}) does not match the "
                f"accepted Decision 094 §1.1 digest; the file changed after acceptance"
            )
            raise PreflightRefusalError(message)
        selected.append(migration)
    return tuple(selected)


def _disk_predicate(catalog_path: Path, catalog_bytes: int) -> tuple[bool, int, int]:
    """Whether free space covers three catalog copies plus a gibibyte (§5.2 predicate 11)."""
    required = DISK_CATALOG_MULTIPLE * catalog_bytes + DISK_HEADROOM_BYTES
    available = shutil.disk_usage(catalog_path.parent).free
    return available >= required, available, required


def _network_switches_disabled(config: object) -> bool:
    """Whether both tracked network switches are off (§5.2 predicate 13).

    Read from the loaded configuration rather than from the YAML file, so a runtime override
    could not leave the file saying ``false`` while the process believed otherwise.
    """
    network = getattr(config, "network", None)
    enabled = bool(getattr(network, "enabled", True))
    acquire = bool(getattr(network, "m3_acquire_enabled", True))
    return not enabled and not acquire


@dataclass(frozen=True, slots=True)
class _CatalogFacts:
    """What one strictly read-only inspection of the accepted catalog established."""

    catalog_path: Path
    catalog_bytes: int
    applied: tuple[int, ...]
    integrity: Mapping[str, object]
    empty_state: Mapping[str, int]
    plan_total: int
    plan_not_started: int
    parser_runs: int
    digest: CatalogSnapshotDigest
    estimate: ReleaseHashEstimate


def _inspect_catalog(catalog_path: Path) -> _CatalogFacts:
    """Measure the accepted catalog through a strictly read-only handle.

    ``strictly_read_only_connection`` is not merely convention here: a read-write handle to a
    WAL-mode database checkpoints on close, which would rewrite durable bytes during what is
    supposed to be an inspection. Decision 093 §10 makes that one of the six mandatory
    execution invariants, and preflight is where it matters most.
    """
    from disclosure_drift.storage.catalog import strictly_read_only_connection

    with strictly_read_only_connection(catalog_path) as connection:
        report = integrity_report(connection)
        applied = applied_versions(connection)
        empty_state = _empty_state_counts(connection)
        plan_total = 0
        plan_not_started = 0
        if _table_exists(connection, "census_plan_sources"):
            plan_total = int(
                connection.execute("SELECT COUNT(*) FROM census_plan_sources").fetchone()[0]
            )
            plan_not_started = int(
                connection.execute(
                    "SELECT COUNT(*) FROM census_plan_sources WHERE parser_state = 'not_started'"
                ).fetchone()[0]
            )
        parser_runs = 0
        if _table_exists(connection, "census_parser_runs"):
            parser_runs = int(
                connection.execute("SELECT COUNT(*) FROM census_parser_runs").fetchone()[0]
            )
        estimate = estimate_release_hash_memory(connection)
        digest = catalog_snapshot_digest(connection)
    return _CatalogFacts(
        catalog_path=catalog_path,
        catalog_bytes=catalog_path.stat().st_size,
        applied=applied,
        integrity={
            "quick_check": report.quick_check,
            "integrity_check": report.integrity_check,
            "foreign_key_violations": report.foreign_key_violations,
        },
        empty_state=empty_state,
        plan_total=plan_total,
        plan_not_started=plan_not_started,
        parser_runs=parser_runs,
        digest=digest,
        estimate=estimate,
    )


def _effective_uid() -> int | None:
    """The effective operator's numeric identity, or ``None`` when the platform will not say.

    A platform that cannot answer must not silently pass the ownership half of §5.2 predicate
    10, so the caller treats ``None`` as "ownership could not be established" and refuses --
    the same rule :func:`_physical_memory_bytes` follows for the memory bound.
    """
    getter = getattr(os, "geteuid", None)
    if getter is None:  # pragma: no cover - supported CI and production platforms are Unix
        return None
    return int(getter())


def _short(value: object) -> str:
    """The first twelve characters of a digest or identity, for a printed report.

    Preflight output is read by an operator and reaches logs, so identities are rendered as
    prefixes: enough to tell two apart, never a full secret-shaped value.
    """
    return f"{str(value)[:12]}…"


def _pinned_receipt(
    evidence_root: Path, pin: AcquisitionReceiptPin
) -> tuple[Path, Mapping[str, object] | None, list[str]]:
    """Load one pinned M3.2 receipt from its fixed public relative name, or refuse.

    Four independent facts are required before the document is trusted at all: the artifact is a
    **regular, non-symlinked, contained** file beneath the private root; its stored bytes hash to
    the exact accepted digest; the accepted loader accepts its closed schema, canonical bytes,
    and self-derived identity; and the identity it derives is the accepted one. Each catches
    something the others do not -- a digest match cannot prove the schema, and a schema match
    cannot prove the bytes were not reserialized.

    No message quotes an :class:`OSError`, which ordinarily carries the offending filename and
    would be exactly the private absolute path this boundary exists to keep out of output.
    """
    refusals: list[str] = []
    path = resolve_within(
        evidence_root, pin.relative_path, label=f"{pin.label} M3.2 completion receipt"
    )
    if path.is_symlink() or not path.is_file():
        refusals.append(
            f"the accepted M3.2 {pin.label} completion receipt is not a regular file at the "
            f"fixed name {pin.relative_path}"
        )
        return path, None, refusals
    try:
        _refuse_symlinked_descent(evidence_root, path)
        digest, _length = file_digest(path)
    except E0Error as exc:
        refusals.append(f"the accepted M3.2 {pin.label} completion receipt is not contained: {exc}")
        return path, None, refusals
    except OSError as exc:
        refusals.append(
            f"the accepted M3.2 {pin.label} completion receipt could not be read "
            f"({type(exc).__name__})"
        )
        return path, None, refusals
    if digest != pin.file_sha256:
        refusals.append(
            f"the accepted M3.2 {pin.label} completion receipt hashes to {_short(digest)}, not "
            f"the accepted {_short(pin.file_sha256)}"
        )
        return path, None, refusals
    try:
        document = inspect_receipt(path)
    except DisclosureDriftError as exc:
        refusals.append(f"the accepted M3.2 {pin.label} completion receipt did not validate: {exc}")
        return path, None, refusals
    except OSError as exc:
        refusals.append(
            f"the accepted M3.2 {pin.label} completion receipt could not be read "
            f"({type(exc).__name__})"
        )
        return path, None, refusals
    if str(document.get("receipt_id")) != pin.receipt_id:
        refusals.append(
            f"the accepted M3.2 {pin.label} completion receipt derives identity "
            f"{_short(document.get('receipt_id'))}, not the accepted {_short(pin.receipt_id)}"
        )
        return path, None, refusals
    return path, document, refusals


def _receipt_count(document: Mapping[str, object], key: str) -> int:
    """One integer receipt field, narrowed from a parsed JSON document.

    An absent optional count is ``0``, which is its arithmetic meaning. A present value of any
    other type is ``-1``: the receipt loader has already refused a non-integer where the closed
    schema types a count, so this cannot arise from a valid receipt -- and if it somehow did, a
    negative contribution makes the cumulative comparison refuse rather than silently pass.
    """
    if key not in document:
        return 0
    value = document[key]
    return value if isinstance(value, int) and not isinstance(value, bool) else -1


def _receipt_fact_refusals(
    pin: AcquisitionReceiptPin,
    document: Mapping[str, object],
    binding: AcquisitionCompletionBinding,
    *,
    is_head: bool,
) -> list[str]:
    """Refuse a validated receipt whose recorded facts are not the accepted ones."""
    refusals: list[str] = []
    if document.get("completion_status") != pin.completion_status:
        refusals.append(
            f"the accepted M3.2 {pin.label} receipt records completion status "
            f"{document.get('completion_status')!r}, not {pin.completion_status!r}"
        )
    if document.get("acquisition_window") != binding.acquisition_window:
        refusals.append(
            f"the accepted M3.2 {pin.label} receipt records window "
            f"{document.get('acquisition_window')!r}, not {binding.acquisition_window!r}"
        )
    if document.get("request_plan_sha256") != pin.request_plan_sha256:
        refusals.append(
            f"the accepted M3.2 {pin.label} receipt executed plan "
            f"{_short(document.get('request_plan_sha256'))}, not the accepted "
            f"{_short(pin.request_plan_sha256)}"
        )
    if is_head:
        if document.get("actual_logical_request_count") != binding.head_logical_request_count:
            refusals.append(
                f"the accepted M3.2 {pin.label} receipt records "
                f"{document.get('actual_logical_request_count')!r} logical request(s), not "
                f"{binding.head_logical_request_count}"
            )
        if document.get("actual_physical_attempt_count") != binding.head_physical_attempt_count:
            refusals.append(
                f"the accepted M3.2 {pin.label} receipt records "
                f"{document.get('actual_physical_attempt_count')!r} physical attempt(s), not "
                f"{binding.head_physical_attempt_count}"
            )
        if document.get("recovery_predecessor_receipt_id") != binding.predecessor.receipt_id:
            refusals.append(
                f"the accepted M3.2 {pin.label} receipt names predecessor "
                f"{_short(document.get('recovery_predecessor_receipt_id'))}, not the accepted "
                f"{_short(binding.predecessor.receipt_id)}"
            )
    elif "recovery_predecessor_receipt_id" in document:
        refusals.append(
            f"the accepted M3.2 {pin.label} receipt names a predecessor; it is the chain root "
            f"and the accepted chain is exactly two receipts to root"
        )
    return refusals


def _acquisition_run_refusals(
    connection: sqlite3.Connection,
    pin: AcquisitionReceiptPin,
    document: Mapping[str, object],
) -> list[str]:
    """Refuse unless the fixed catalog carries exactly the accepted run row for this receipt.

    Zero rows, more than one, a non-acquisition job kind, another window, an untruthful terminal
    job state, a boundary instant that is not the receipt's, or an attempt ledger that disagrees
    with the receipt's own accounting each refuse. Nothing is repaired, preferred, or averaged:
    two durable surfaces that disagree establish nothing.
    """
    refusals: list[str] = []
    rows = connection.execute(
        "SELECT job_kind, stage, job_state, started_at_utc, finished_at_utc "
        "FROM ops_ingestion_jobs WHERE job_id = ?",
        (pin.run_id,),
    ).fetchall()
    if len(rows) != 1:
        refusals.append(
            f"the fixed catalog carries {len(rows)} run row(s) for the accepted M3.2 "
            f"{pin.label} run; exactly one is required"
        )
        return refusals
    row = rows[0]
    expected_state = _ACQUISITION_TERMINAL_JOB_STATES.get(str(document.get("completion_status")))
    checks: tuple[tuple[str, object, object], ...] = (
        ("job kind", row["job_kind"], M3_2_ACQUISITION_JOB_KIND),
        ("stage", row["stage"], document.get("acquisition_window")),
        ("job state", row["job_state"], expected_state),
        ("start instant", row["started_at_utc"], document.get("started_at_utc")),
        ("finish instant", row["finished_at_utc"], document.get("completed_at_utc")),
    )
    for name, found, expected in checks:
        if expected is None or found != expected:
            refusals.append(
                f"the accepted M3.2 {pin.label} run row's {name} does not equal the receipt's"
            )
    attempts = int(
        connection.execute(
            "SELECT COUNT(*) FROM ops_retrieval_attempts WHERE job_id = ?", (pin.run_id,)
        ).fetchone()[0]
    )
    if attempts != document.get("actual_physical_attempt_count"):
        refusals.append(
            f"the accepted M3.2 {pin.label} run holds {attempts} durable attempt row(s) but its "
            f"receipt records {document.get('actual_physical_attempt_count')!r}"
        )
    return refusals


def _head_observation_refusals(
    connection: sqlite3.Connection, binding: AcquisitionCompletionBinding
) -> list[str]:
    """Refuse unless the accepted head observation exists and is attributed to the head run.

    ``census_plan_sources`` is the accepted run-to-observation attribution relation: it carries
    ``census_run_id`` as an ``ops_ingestion_jobs.job_id`` and ``observation_id`` as a
    ``census_source_observations`` reference, which is exactly the pair predicate 3 binds. One
    observation may lawfully be planned under more than one instance of the same run, so the
    rule is that **every** attributing run is the accepted one, and at least one exists.
    """
    refusals: list[str] = []
    observations = int(
        connection.execute(
            "SELECT COUNT(*) FROM census_source_observations WHERE observation_id = ?",
            (binding.head_observation_id,),
        ).fetchone()[0]
    )
    if observations != 1:
        refusals.append(
            f"the fixed catalog carries {observations} row(s) for the accepted M3.2 head "
            f"observation; exactly one is required"
        )
    attributing = tuple(
        str(row["census_run_id"])
        for row in connection.execute(
            "SELECT DISTINCT census_run_id FROM census_plan_sources WHERE observation_id = ?",
            (binding.head_observation_id,),
        ).fetchall()
    )
    if attributing != (binding.head.run_id,):
        refusals.append(
            f"the accepted M3.2 head observation's durable run attribution is not exactly the "
            f"accepted T7 run; {len(attributing)} attributing run(s) were found"
        )
    return refusals


def _acquisition_completion_binding(
    *,
    evidence_root: Path,
    catalog_path: Path | None,
    binding: AcquisitionCompletionBinding,
) -> tuple[list[str], dict[str, object]]:
    """Decision 094 §5.2 predicate 3: the accepted M3.2 completion receipt and catalog binding.

    Strictly read-only and source-local (accepted Decision 099 R97). It reuses exactly two
    accepted mechanics -- :func:`~disclosure_drift.m3.receipt.inspect_receipt` for a receipt's
    schema, canonical bytes, and self-derived identity, and the Decision-063
    :func:`~disclosure_drift.m3.receipt.resolve_predecessor_receipt` for cross-namespace chain
    resolution -- and imports no recovery module, acquisition orchestrator, request-plan builder,
    source registry, client, transport, socket, HTTP library, or SEC route.

    Nothing here is discovered. The chain, its two identities, the window, the head's completion
    facts, the accepted observation, and the cumulative attempt total are all fixed by
    :data:`M3_2_COMPLETION_BINDING`: a predicate that searched for "the most recent receipt"
    would validate whatever it found, which is the opposite of a provenance binding.

    Returns:
        The collected refusals and the non-secret facts the report prints.
    """
    refusals: list[str] = []
    facts: dict[str, object] = {
        "m3_2_completion_receipt_head": _short(binding.head.receipt_id),
        "m3_2_completion_receipt_root": _short(binding.predecessor.receipt_id),
    }

    head_path, head, head_refusals = _pinned_receipt(evidence_root, binding.head)
    root_path, root, root_refusals = _pinned_receipt(evidence_root, binding.predecessor)
    refusals.extend(head_refusals)
    refusals.extend(root_refusals)
    if head is None or root is None:
        facts["m3_2_completion_binding"] = "REFUSED"
        return refusals, facts

    refusals.extend(_receipt_fact_refusals(binding.head, head, binding, is_head=True))
    refusals.extend(_receipt_fact_refusals(binding.predecessor, root, binding, is_head=False))

    # The chain is resolved by the accepted resolver rather than assumed from the two pins: that
    # is what refuses a missing, ambiguous, or substituted predecessor, and it is the surface
    # Decision 063 corrected for exactly this two-namespace chain.
    try:
        resolved_path, resolved = resolve_predecessor_receipt(
            binding.predecessor.receipt_id,
            head_directory=head_path.parent,
            evidence_root=evidence_root,
        )
    except DisclosureDriftError as exc:
        refusals.append(f"the accepted M3.2 completion chain did not resolve: {exc}")
    except OSError as exc:
        refusals.append(
            f"the accepted M3.2 completion chain could not be read ({type(exc).__name__})"
        )
    else:
        if resolved_path != root_path or canonical_bytes(resolved) != canonical_bytes(root):
            refusals.append(
                "the accepted M3.2 predecessor identity resolves to a receipt other than the "
                "accepted T6 receipt at its fixed name"
            )

    # Decision 055 §7.5's cumulative rule, restated rather than imported: the chain's own
    # attempts plus the carried-forward baseline of the single no-predecessor root, added
    # exactly once. The head's baseline is deliberately not added -- a resumed head inherits
    # from its predecessor, whose attempts are already in the sum.
    cumulative = (
        _receipt_count(head, "actual_physical_attempt_count")
        + _receipt_count(root, "actual_physical_attempt_count")
        + _receipt_count(root, "consumed_request_count_carried_forward")
    )
    facts["m3_2_cumulative_physical_attempts"] = cumulative
    if cumulative != binding.cumulative_physical_attempt_count:
        refusals.append(
            f"the accepted M3.2 chain accounts for {cumulative} cumulative physical attempt(s), "
            f"not the accepted {binding.cumulative_physical_attempt_count}"
        )

    if catalog_path is None:
        refusals.append(
            "the accepted M3.2 completion receipts could not be bound to the fixed catalog "
            "because the catalog was not measurable"
        )
    else:
        try:
            with _read_only(catalog_path) as connection:
                refusals.extend(_acquisition_run_refusals(connection, binding.head, head))
                refusals.extend(_acquisition_run_refusals(connection, binding.predecessor, root))
                refusals.extend(_head_observation_refusals(connection, binding))
        except (DisclosureDriftError, sqlite3.Error) as exc:
            refusals.append(f"the accepted M3.2 catalog binding could not be read: {exc}")
        except OSError as exc:
            refusals.append(
                f"the accepted M3.2 catalog binding could not be read ({type(exc).__name__})"
            )

    facts["m3_2_completion_binding"] = "REFUSED" if refusals else "validated"
    return refusals, facts


def _shared_preflight(
    *,
    evidence_root: Path,
    namespace: str,
    config: object,
    expected_head: int,
    lease_check: bool = True,
) -> tuple[list[str], dict[str, object], _CatalogFacts | None]:
    """The predicates both machines share, measured once.

    Every refusal is collected rather than raised at the first failure: an operator fixing one
    predicate should not have to rerun to discover the next three.

    ``lease_check`` is the accepted Decision 099 R98 replacement for filtering refusal text: the
    under-lease recheck passes ``False`` because **this process** now holds the lease predicate 9
    would otherwise be testing, and that is a control-flow fact the caller knows rather than
    something to be recovered from an English message. No other predicate is ever omitted.
    """
    refusals: list[str] = []
    facts: dict[str, object] = {}

    catalog_path = resolve_within(
        evidence_root, OPERATIONAL_CATALOG_RELATIVE_PATH, label="operational catalog"
    )
    facts["catalog_relative_path"] = OPERATIONAL_CATALOG_RELATIVE_PATH
    if not catalog_path.exists():
        refusals.append("the accepted catalog is absent beneath the resolved private root")
        return refusals, facts, None
    _refuse_symlinked_descent(evidence_root, catalog_path)

    measured = _inspect_catalog(catalog_path)
    facts["catalog_bytes"] = measured.catalog_bytes
    facts["applied_migration_head"] = f"{measured.applied[-1]:04d}" if measured.applied else "none"
    facts["applied_migration_count"] = len(measured.applied)
    facts["quick_check"] = measured.integrity["quick_check"]
    facts["integrity_check"] = measured.integrity["integrity_check"]
    facts["foreign_key_violations"] = measured.integrity["foreign_key_violations"]
    facts["precondition_table_count"] = len(measured.empty_state)
    facts["precondition_nonempty_tables"] = sum(
        1 for count in measured.empty_state.values() if count
    )
    facts["planned_source_count"] = measured.plan_total
    facts["planned_sources_not_started"] = measured.plan_not_started
    facts["census_parser_run_count"] = measured.parser_runs
    facts["largest_table"] = measured.estimate.table_name or "none"
    facts["release_hash_peak_estimate_bytes"] = measured.estimate.estimated_peak_bytes
    facts["release_hash_memory_ceiling_bytes"] = measured.estimate.memory_ceiling

    expected_chain = tuple(range(1, expected_head + 1))
    if measured.applied != expected_chain:
        refusals.append(
            f"the applied chain must be contiguous and exactly 0001-{expected_head:04d}; "
            f"found {len(measured.applied)} applied version(s)"
        )
    if (
        measured.integrity["quick_check"] != "ok"
        or measured.integrity["integrity_check"] != "ok"
        or measured.integrity["foreign_key_violations"] != 0
    ):
        refusals.append("the catalog did not pass all three SQLite integrity gates")

    nonempty = tuple(sorted(name for name, count in measured.empty_state.items() if count))
    if nonempty:
        refusals.append(f"the migration window is closed: guard table(s) {nonempty} carry rows")
    if measured.plan_total != PLANNED_SOURCE_COUNT:
        refusals.append(
            f"the accepted plan must carry exactly {PLANNED_SOURCE_COUNT} sources; "
            f"found {measured.plan_total}"
        )
    if measured.plan_not_started != measured.plan_total:
        refusals.append("every accepted plan source must still be parser_state = not_started")
    if measured.parser_runs:
        refusals.append("an E0 parser run already exists; a namespace is never reused")
    if not measured.estimate.passes:
        refusals.append(
            f"the per-table release-hash estimate {measured.estimate.estimated_peak_bytes} "
            f"exceeds the ceiling {measured.estimate.memory_ceiling}"
        )

    if lease_check:
        lock_directory = catalog_path.parent
        present, recorded_state, shareable = _lease_state(lock_directory)
        facts["writer_lease"] = "absent" if not present else (recorded_state or "unreadable")
        if present and not shareable:
            refusals.append(
                "another writer holds the catalog lease; elapsed time never permits takeover"
            )
        if present and recorded_state == "held":
            refusals.append("the recorded catalog writer lease state is 'held'")
    else:
        facts["writer_lease"] = "held by this run"

    run_directory = namespace_directory(evidence_root, namespace)
    facts["run_namespace"] = namespace
    if run_directory.exists() or run_directory.is_symlink():
        refusals.append(f"run namespace {namespace!r} already exists; it is create-once")
    # §5.2 predicate 10's second half, in full: the parent must **already** be a real directory
    # owned by the effective operator. Creating it here, or accepting an unowned one, would each
    # be a permissive reading of a predicate whose whole point is that the governed artifacts
    # land somewhere the operator already controls.
    parent = runs_directory(evidence_root)
    if parent.is_symlink() or not parent.is_dir():
        facts["runs_parent"] = "unsound"
        refusals.append(
            "the private root's runs directory must already exist as a real, non-symlinked "
            "directory before a run namespace may be created"
        )
    else:
        operator = _effective_uid()
        owner = parent.stat().st_uid
        facts["runs_parent"] = "owned by the operator" if operator == owner else "unsound"
        if operator is None:
            refusals.append(
                "the effective operator identity could not be established, so the private "
                "root's runs directory cannot be proved to be owned by the operator"
            )
        elif operator != owner:
            refusals.append(
                "the private root's runs directory is not owned by the effective operator"
            )

    ok, available, required = _disk_predicate(catalog_path, measured.catalog_bytes)
    facts["free_disk_bytes"] = available
    facts["required_disk_bytes"] = required
    if not ok:
        refusals.append(f"available bytes {available} are fewer than the required {required}")

    facts["network_switches_disabled"] = _network_switches_disabled(config)
    if not facts["network_switches_disabled"]:
        refusals.append("a tracked network switch is enabled")

    return refusals, facts, measured


def transition_preflight(
    *,
    evidence_root: Path,
    config: object,
    namespace: str = TRANSITION_RUN_NAMESPACE,
) -> PreflightReport:
    """Evaluate every Decision 094 §5.2 predicate, all thirteen. Strictly read-only.

    Predicate 3 -- the accepted M3.2 acquisition completion receipt and catalog binding -- is
    :func:`_acquisition_completion_binding`, added by accepted Decision 099 R97. The claim in
    this docstring's first line is therefore exact rather than aspirational; before that
    correction it was twelve of thirteen, which is the Decision 098 MAJOR-2 finding.

    Creates **nothing**: no directory, lock, backup, receipt, ledger, temporary file, schema
    row, or catalog page. That is not a convention here -- the catalog is opened through
    ``SQLITE_OPEN_READONLY`` and the writer lease is inspected without being created or
    acquired, so a preflight cannot consume the migration window it exists to measure.
    """
    refusals, facts, measured = _shared_preflight(
        evidence_root=evidence_root,
        config=config,
        namespace=namespace,
        expected_head=TRANSITION_SOURCE_HEAD,
    )
    binding_refusals, binding_facts = _acquisition_completion_binding(
        evidence_root=evidence_root,
        catalog_path=None if measured is None else measured.catalog_path,
        binding=M3_2_COMPLETION_BINDING,
    )
    facts.update(binding_facts)
    refusals.extend(binding_refusals)
    facts["target_migration_head"] = f"{TRANSITION_TARGET_HEAD:04d}"
    try:
        targets = _packaged_target_migrations()
    except PreflightRefusalError as exc:
        refusals.append(str(exc))
        targets = ()
    for migration in targets:
        facts[f"packaged_{migration.version:04d}_sha256"] = migration.checksum_sha256
    if any(migration.version > TRANSITION_TARGET_HEAD for migration in available_migrations()):
        refusals.append(
            f"a packaged migration beyond {TRANSITION_TARGET_HEAD:04d} exists; migration 0016 "
            f"is unauthorized and is never selected"
        )
    if measured is not None:
        facts["pre_catalog_logical_sha256"] = measured.digest.require_full()
        facts["pre_preexisting_content_sha256"] = measured.digest.preexisting_content_sha256
    facts["transition_execute_enabled"] = PRE_E0_CATALOG_TRANSITION_AUTHORITY is not None
    return PreflightReport(passed=not refusals, refusals=tuple(refusals), facts=facts)


def e0_preflight(
    *,
    evidence_root: Path,
    config: object,
    namespace: str = E0_RUN_NAMESPACE,
) -> PreflightReport:
    """Evaluate every Decision 094 §9.1 E0 predicate. Strictly read-only, creates nothing.

    E0's distinct requirements are the head-``0015`` chain, an owner-accepted **COMPLETE**
    transition terminal and token, and the exact input-observation digest. The shared
    predicates -- integrity, empty state, plan totality, lease, namespace, disk, memory, and
    network switches -- are the same measurements the transition makes.
    """
    refusals, facts, measured = _shared_preflight(
        evidence_root=evidence_root,
        config=config,
        namespace=namespace,
        expected_head=TRANSITION_TARGET_HEAD,
    )
    transition_directory = namespace_directory(evidence_root, TRANSITION_RUN_NAMESPACE)
    terminal_path = transition_directory / TRANSITION_TERMINAL_FILENAME
    facts["transition_terminal"] = "present" if terminal_path.exists() else "absent"
    if not terminal_path.exists():
        refusals.append(
            "the owner-accepted COMPLETE transition terminal record is absent; E0 requires it "
            "and absence is UNDETERMINED / NOT COMPLETE, never success"
        )
    else:
        try:
            terminal, events = _load_terminal(
                terminal_path,
                transition_directory / TRANSITION_EVENTS_FILENAME,
                kind="TRANSITION",
            )
        except (E0Error, OSError) as exc:
            refusals.append(f"the transition terminal record did not validate: {exc}")
        else:
            facts["transition_status"] = str(terminal["status"])
            facts["transition_terminal_record_id"] = str(terminal["terminal_record_id"])
            facts["transition_event_count"] = len(events)
            if terminal["status"] != "complete":
                refusals.append(
                    f"the transition terminal status is {terminal['status']!r}; only a COMPLETE "
                    f"and owner-accepted transition permits E0"
                )
    if measured is not None:
        facts["pre_e0_catalog_logical_sha256"] = measured.digest.require_full()
        with _read_only(measured.catalog_path) as connection:
            facts["input_observation_set_sha256"] = input_observation_set_digest(connection)
    facts["e0_execute_enabled"] = M3_3_E0_EXECUTION_AUTHORITY is not None
    return PreflightReport(passed=not refusals, refusals=tuple(refusals), facts=facts)


# --------------------------------------------------------------------------- #
# Decision 094 §§5.3, 9.1, 11 -- the two execute state machines
#
# Both are complete and neither is reachable. :func:`_require_activation` is the single
# door and it is shut: the module constants are ``None``, so every path below returns
# exit 3 before it can touch a lease, a namespace, or a catalog page.
# --------------------------------------------------------------------------- #
def _require_activation(constant: str | None, *, stage: str, constant_name: str) -> str:
    """Return the governed token, or refuse the stage (exit ``3``).

    The **only** production source of authority is the named module constant. No flag,
    environment value, ambient file, preflight result, verify result, catalog state, receipt,
    or namespace reaches this function, and none is consulted here. A later exact owner
    instrument replaces the constant's literal; nothing else enables the stage.

    Raises:
        StageNotEnabledError: the constant is ``None``.
    """
    if constant is None:
        message = (
            f"{stage} execute is not enabled by the current executable boundary: "
            f"{constant_name} is None. A governance record supplies authority; no flag, "
            f"environment value, catalog state, receipt, or namespace can substitute for it"
        )
        raise StageNotEnabledError(message)
    return constant


def _authority_digest(value: str) -> str:
    """``owner_authority_sha256``: the digest of the governed authority, never its value."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    """The accepted UTC timestamp rendering, shared with the catalog layer."""
    from disclosure_drift.storage.sqlite import utc_now

    return utc_now()


def _elapsed_seconds(started: str, completed: str) -> float:
    """Elapsed seconds between two accepted timestamps."""
    from datetime import datetime

    begin = datetime.fromisoformat(started.replace("Z", "+00:00"))
    end = datetime.fromisoformat(completed.replace("Z", "+00:00"))
    return max(0.0, (end - begin).total_seconds())


def _configuration_fingerprint(config: object) -> str:
    """A digest over effective NON-SECRET configuration.

    The SEC contact identity is never an input -- not even hashed -- because encoding does
    not launder a prohibited value. Only settings already safe to publish reach this.
    """
    sec = getattr(config, "sec", None)
    network = getattr(config, "network", None)
    payload = json.dumps(
        {
            "requests_per_second": getattr(sec, "requests_per_second", None),
            "burst": getattr(sec, "burst", None),
            "connect_timeout_seconds": getattr(sec, "connect_timeout_seconds", None),
            "read_timeout_seconds": getattr(sec, "read_timeout_seconds", None),
            "bulk_read_timeout_seconds": getattr(sec, "bulk_read_timeout_seconds", None),
            "max_retries": getattr(sec, "max_retries", None),
            "cooldown_seconds": getattr(sec, "cooldown_seconds", None),
            "network_enabled": getattr(network, "enabled", None),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ExecuteOutcome:
    """One completed, failed, or interrupted execute run's durable result."""

    status: str
    run_namespace: str
    terminal_record_id: str
    result_token: str
    execution_receipt_id: str
    event_count: int


def _verified_backup(
    *,
    writer_connection: sqlite3.Connection,
    destination: Path,
    source_digest: CatalogSnapshotDigest,
    expected_head: int,
) -> Mapping[str, object]:
    """Take, close, fsync, digest, and independently verify the backup (§5.3 items 4-5).

    Each step is load-bearing. The file is precreated at ``0600`` so it is never briefly
    world-readable (finding m2). The SQLite backup API is used because a naive copy of a WAL
    database is not consistent. The destination handle is **closed** before the digest,
    because hashing an open SQLite file hashes a state that may still change. The completed
    file and its parent are fsynced before anything downstream treats the backup as durable.
    """
    _precreate_exclusive(destination)
    target = sqlite3.connect(destination)
    try:
        writer_connection.backup(target)
        # The backup inherits the source's WAL journal mode, which would leave a `-wal` and a
        # `-shm` beside it. Those are lawful *operational* sidecars of the fixed catalog
        # (§8), but the run namespace's authorized write set is exactly four files -- so the
        # completed backup is converted to a self-contained rollback-journal database before
        # its handle closes. Journal mode is a file-format property, not content: every table,
        # column, and row is untouched, which the logical-digest comparison below proves.
        target.execute("PRAGMA journal_mode = DELETE")
    finally:
        target.close()
    descriptor = os.open(destination, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(destination.parent)

    digest, byte_length = file_digest(destination)
    with _read_only(destination) as backup:
        report = integrity_report(backup)
        chain = applied_versions(backup)
        backup_digest = catalog_snapshot_digest(backup)
    if chain != tuple(range(1, expected_head + 1)):
        message = f"the closed backup's migration chain is not exactly 0001-{expected_head:04d}"
        raise PreflightRefusalError(message)
    if not report.passed:
        message = "the closed backup did not pass all three SQLite integrity gates"
        raise PreflightRefusalError(message)
    if backup_digest.require_full() != source_digest.require_full():
        message = (
            "the closed backup's logical catalog digest differs from the source snapshot's; "
            "the backup is not a faithful copy and the run must not proceed"
        )
        raise PreflightRefusalError(message)
    return {
        "relative_path": f"{RUN_NAMESPACE_DIRNAME}/{destination.parent.name}/{destination.name}",
        "byte_length": byte_length,
        "file_sha256": digest,
        "catalog_logical_sha256": backup_digest.require_full(),
        "integrity": {
            "quick_check": report.quick_check,
            "integrity_check": report.integrity_check,
            "foreign_key_violations": report.foreign_key_violations,
        },
    }


def _freeze(
    *,
    directory: Path,
    ledger: EventLedger,
    receipt: ExecutionReceiptV4,
    terminal: dict[str, object],
    record_type: str,
    observed_at_utc: str,
) -> ExecuteOutcome:
    """The §11 freeze tail: receipt, its event, the terminal record, then reproduce it.

    The order is mandatory and the reasons interlock. The receipt is written first so the
    terminal can bind its identity without a cycle. ``EXECUTION_RECEIPT_WRITTEN`` is appended
    before the terminal so the terminal binds a ledger head that will not move afterwards --
    which is also why §10.2 deliberately has no ``TERMINAL_FROZEN`` event. The terminal is
    written last and write-once, then **reopened read-only** and its identity and token
    reproduced from the persisted bytes, because an identity only ever computed in memory has
    not been proved to be the one on disk.
    """
    receipt_bytes = receipt.canonical_bytes()
    receipt_id = str(receipt.receipt_id)
    write_once(directory / OPERATOR_RECEIPT_FILENAME, receipt_bytes)
    ledger.append(
        "EXECUTION_RECEIPT_WRITTEN",
        {"execution_receipt_id": receipt_id},
        observed_at_utc=observed_at_utc,
    )

    terminal["execution_receipt_id"] = receipt_id
    terminal["event_ledger"] = {
        "relative_path": f"{RUN_NAMESPACE_DIRNAME}/{directory.name}/{ledger.path.name}",
        "event_count": ledger.event_count,
        "head_event_sha256": ledger.head_event_sha256,
    }
    identity = compute_terminal_record_id(terminal)
    terminal["terminal_record_id"] = identity
    terminal["result_token"] = result_token(record_type, str(terminal["status"]), identity)

    kind = "TRANSITION" if record_type == "catalog_transition" else "E0"
    filename = TRANSITION_TERMINAL_FILENAME if kind == "TRANSITION" else E0_TERMINAL_FILENAME
    write_once(directory / filename, canonical_bytes(terminal))

    reopened, _ = _load_terminal(directory / filename, ledger.path, kind=kind)
    return ExecuteOutcome(
        status=str(reopened["status"]),
        run_namespace=str(reopened["run_namespace"]),
        terminal_record_id=str(reopened["terminal_record_id"]),
        result_token=str(reopened["result_token"]),
        execution_receipt_id=receipt_id,
        event_count=ledger.event_count,
    )


def _durable_event_types(path: Path, *, kind: str) -> frozenset[str] | None:
    """The event types the ledger **durably** holds, or ``None`` if it cannot be verified.

    An absent ledger file is not an unverifiable one: it is the verified fact that no event
    became durable, and the projection below then permits no event-conditioned field at all. A
    ledger that exists but is truncated, malformed, reordered, or unchained is a different
    answer entirely -- nothing can be concluded about which events are durable, so the caller
    must not manufacture a terminal record over it (accepted Decision 099 R96).
    """
    if not path.exists():
        return frozenset()
    try:
        events = read_event_ledger(path, kind=kind)
    except (E0Error, OSError):
        return None
    return frozenset(str(event["event_type"]) for event in events)


def _project_failure_terminal(
    terminal: dict[str, object],
    *,
    record_type: str,
    event_types: frozenset[str],
    catalog_observed: bool,
) -> None:
    """Remove every conditional field whose durable condition is absent (Decision 099 R96).

    The execute paths assign an event-conditioned value **before** appending the event that
    permits it -- necessarily so, since the event's own ``details`` carry that value. A failure
    inside that window would otherwise leave a create-once terminal record carrying a field its
    own closed validator refuses, which is Decision 098 MAJOR-1. Deriving the permitted set from
    the ledger closes the whole class rather than the two windows that were reproduced: assignment
    order stops being evidence of durability, because durability is read from the ledger.
    """
    conditioned = (
        _TRANSITION_EVENT_CONDITIONED_FIELDS
        if record_type == "catalog_transition"
        else _E0_EVENT_CONDITIONED_FIELDS
    )
    for event_type, fields in conditioned.items():
        if event_type in event_types:
            continue
        for field_name in fields:
            terminal.pop(field_name, None)
    if not catalog_observed:
        for field_name in _CATALOG_OBSERVED_FIELDS[record_type]:
            terminal.pop(field_name, None)


def _disclose_failure(
    *,
    directory: Path,
    ledger: EventLedger,
    terminal: dict[str, object],
    config: object,
    started: str,
    record_type: str,
    exc: BaseException,
    interruption: str | None,
    catalog_observed: bool,
    migration_chain_head: str,
) -> None:
    """Record a failed or interrupted run truthfully, then let the exception propagate.

    Decision 094 §5.4 and §9.1: a failed or interrupted run **preserves** its namespace and
    evidence and returns to the owner. Nothing here restores a catalog, deletes an artifact,
    retries, or resumes; the run is disclosed as exactly what it was.

    A ``KeyboardInterrupt`` or ``SystemExit`` is an *interruption* and a domain error is a
    *failure*, because those are genuinely different facts about the catalog: the first says
    the operator stopped the process at a known boundary, the second says a gate refused.
    """
    interrupted = isinstance(exc, (KeyboardInterrupt, SystemExit))
    status = "interrupted" if interrupted else "failed"
    is_transition = record_type == "catalog_transition"
    reason_code = (
        "PRE_E0_CATALOG_TRANSITION_INTERRUPTED"
        if is_transition and interrupted
        else "PRE_E0_CATALOG_TRANSITION_FAILED"
        if is_transition
        else "M3_3_E0_OFFLINE_PARSE_INTERRUPTED"
        if interrupted
        else "M3_3_E0_OFFLINE_PARSE_FAILED"
    )
    # One short non-secret sentence. The exception's own text may name a path, so only its
    # class is reported -- a refusal message is not worth leaking a private root for.
    detail = f"{type(exc).__name__} at boundary {interruption or 'unknown'}"
    completed = _utc_now()
    failure: dict[str, object] = {
        "reason_code": reason_code,
        "reason_detail": detail,
        "catalog_state_observed": catalog_observed,
    }
    if interrupted and interruption is not None:
        failure["interruption_state"] = interruption
    terminal["status"] = status
    terminal["completed_at_utc"] = completed
    terminal["failure"] = failure

    with suppress(E0Error, OSError):
        ledger.append(
            "INTERRUPTED" if interrupted else "FAILED",
            dict(failure) if interrupted else {"reason_code": reason_code, "reason_detail": detail},
            observed_at_utc=completed,
        )

    # Accepted Decision 099 R96. The ledger is read back and fully verified from disk before a
    # terminal is written over it, and the record's event-conditioned fields are derived from
    # the events that are actually durable there.
    kind = "TRANSITION" if is_transition else "E0"
    durable = _durable_event_types(ledger.path, kind=kind)
    if durable is None:
        # The ledger cannot be verified, so which events are durable is unknown and no lawful
        # terminal can be projected. The surviving artifacts stay UNDETERMINED / NOT COMPLETE,
        # which is what §5.4 already requires, and the original exception still propagates.
        return
    _project_failure_terminal(
        terminal,
        record_type=record_type,
        event_types=durable,
        catalog_observed=catalog_observed,
    )

    receipt = ExecutionReceiptV4(
        command_name=TRANSITION_COMMAND_NAME if is_transition else E0_COMMAND_NAME,
        command_version=TRANSITION_COMMAND_VERSION if is_transition else E0_COMMAND_VERSION,
        invocation_mode="offline_catalog_transition" if is_transition else "offline_parse",
        configuration_fingerprint=_configuration_fingerprint(config),
        migration_chain_head=migration_chain_head,
        started_at_utc=started,
        completed_at_utc=completed,
        elapsed_seconds=_elapsed_seconds(started, completed),
        completion_status=status,
        reason_code=reason_code,
        reason_detail=detail,
        interruption_state=failure.get("interruption_state"),  # type: ignore[arg-type]
        parser_versions=None if is_transition else {"offline_parse": E0_COMMAND_VERSION},
        cohort_definition_digest=None if is_transition else _cohort_digest(),
    )
    with suppress(E0Error, OSError):
        _freeze(
            directory=directory,
            ledger=ledger,
            receipt=receipt,
            terminal=terminal,
            record_type=record_type,
            observed_at_utc=completed,
        )


def _cohort_digest() -> str:
    """The accepted frozen cohort-definition digest, reused rather than redefined."""
    from disclosure_drift.m3.offline_execution import cohort_definition_digest

    return cohort_definition_digest()


def transition_execute(
    *,
    evidence_root: Path,
    config: object,
    namespace: str = TRANSITION_RUN_NAMESPACE,
) -> ExecuteOutcome:
    """Run the exact ``0013 -> 0014 -> 0015`` transition (Decision 094 §5.3).

    **Not reachable.** :data:`PRE_E0_CATALOG_TRANSITION_AUTHORITY` is ``None``, so the first
    statement refuses with exit ``3``. The machine below it is complete so that the later
    activation change is genuinely constant-only.

    Everything after the lease is acquired happens under **one continuous** writer lease: the
    mutable predicates are rechecked under it, the namespace and backup are created under it,
    both migrations are applied under it, and the identities are independently recomputed
    under it. Releasing and reacquiring between those steps would open a window in which
    another writer could change what the earlier step measured.

    Raises:
        StageNotEnabledError: the activation constant is ``None`` (exit ``3``).
        PreflightRefusalError: a predicate, integrity, or identity gate failed (exit ``4``).
    """
    from disclosure_drift.storage.catalog import CatalogWriter
    from disclosure_drift.storage.sqlite import apply_migrations

    authority = _require_activation(
        PRE_E0_CATALOG_TRANSITION_AUTHORITY,
        stage="prepare-e0-catalog",
        constant_name="PRE_E0_CATALOG_TRANSITION_AUTHORITY",
    )
    started = _utc_now()
    catalog_path = resolve_within(
        evidence_root, OPERATIONAL_CATALOG_RELATIVE_PATH, label="operational catalog"
    )
    targets = _packaged_target_migrations()
    inventory = available_migrations()

    terminal: dict[str, object] = {
        "schema_version": TRANSITION_TERMINAL_SCHEMA_VERSION,
        "record_type": "catalog_transition",
        "run_namespace": validate_namespace(namespace),
        "command_name": TRANSITION_COMMAND_NAME,
        "command_version": TRANSITION_COMMAND_VERSION,
        "started_at_utc": started,
        "owner_authority_sha256": _authority_digest(authority),
        "catalog_relative_path": OPERATIONAL_CATALOG_RELATIVE_PATH,
        "target_migration_chain": list(range(1, TRANSITION_TARGET_HEAD + 1)),
        "packaged_migration_sha256": {
            f"{migration.version:04d}": migration.checksum_sha256 for migration in targets
        },
        "actual_logical_request_count": 0,
        "actual_physical_attempt_count": 0,
    }
    applied_records: list[Mapping[str, object]] = []
    interruption = "before_backup"
    catalog_observed = False
    directory: Path | None = None
    ledger: EventLedger | None = None

    with CatalogWriter(catalog_path, catalog_path.parent) as writer:
        try:
            measured = _recheck_under_lease(
                evidence_root=evidence_root,
                config=config,
                namespace=namespace,
                expected_head=TRANSITION_SOURCE_HEAD,
                require_acquisition_binding=True,
            )
            terminal["pre_migration_chain"] = list(measured.applied)
            terminal["precondition_counts"] = dict(measured.empty_state)
            terminal["pre_integrity"] = dict(measured.integrity)
            terminal["pre_catalog_logical_sha256"] = measured.digest.require_full()
            terminal["pre_preexisting_content_sha256"] = measured.digest.preexisting_content_sha256

            directory = create_run_namespace(evidence_root, namespace)
            ledger = EventLedger(
                directory / TRANSITION_EVENTS_FILENAME, namespace, kind="TRANSITION"
            )
            ledger.append(
                "PREFLIGHT_PASSED",
                {
                    "pre_migration_head": f"{measured.applied[-1]:04d}",
                    "catalog_bytes": measured.catalog_bytes,
                    "precondition_table_count": len(measured.empty_state),
                    "pre_catalog_logical_sha256": measured.digest.require_full(),
                },
                observed_at_utc=_utc_now(),
            )

            interruption = "during_backup"
            backup = _verified_backup(
                writer_connection=writer.connection,
                destination=directory / TRANSITION_BACKUP_FILENAME,
                source_digest=measured.digest,
                expected_head=TRANSITION_SOURCE_HEAD,
            )
            terminal["backup"] = backup
            ledger.append(
                "BACKUP_VERIFIED",
                {
                    key: backup[key]
                    for key in (
                        "relative_path",
                        "byte_length",
                        "file_sha256",
                        "catalog_logical_sha256",
                    )
                },
                observed_at_utc=_utc_now(),
            )

            interruption = "after_backup_before_migration"
            for index, migration in enumerate(targets):
                # The accepted contiguous prefix through this migration, never the full
                # pending inventory. `prepare_operational_catalog()` is deliberately not used:
                # it selects every pending migration *and* calls `seed_reference_data()`,
                # whose timestamped INSERT OR REPLACE writes would alter pre-existing rows.
                prefix = tuple(item for item in inventory if item.version <= migration.version)
                apply_migrations(writer.connection, prefix)
                catalog_observed = True
                chain = applied_versions(writer.connection)
                report = integrity_report(writer.connection)
                # `catalog_state_observed` is now true, and §8.1 conditions these three fields on
                # exactly that. They are recorded **before** the two refusals below, so a refusal
                # that fires after a commit discloses the state it actually observed instead of
                # leaving a create-once record its own validator refuses. The success path
                # recomputes and overwrites all three from the post-loop measurement.
                terminal["applied_migrations"] = list(applied_records)
                terminal["post_migration_chain"] = list(chain)
                terminal["post_integrity"] = {
                    "quick_check": report.quick_check,
                    "integrity_check": report.integrity_check,
                    "foreign_key_violations": report.foreign_key_violations,
                }
                if chain[-1] != migration.version:
                    message = f"applying {migration.version:04d} did not move the chain head"
                    raise PreflightRefusalError(message)
                if not report.passed:
                    message = f"integrity failed after migration {migration.version:04d}"
                    raise PreflightRefusalError(message)
                applied_records.append(
                    {
                        "version": migration.version,
                        "name": migration.name,
                        "checksum_sha256": migration.checksum_sha256,
                    }
                )
                terminal["applied_migrations"] = list(applied_records)
                # The commit has happened; the event has not. A crash here is the disclosed
                # commit-before-event window, and the interruption state names it exactly.
                interruption = f"after_migration_{migration.version:04d}_commit_before_event"
                ledger.append(
                    f"MIGRATION_{migration.version:04d}_COMMITTED",
                    {
                        "version": f"{migration.version:04d}",
                        "name": migration.name,
                        "checksum_sha256": migration.checksum_sha256,
                        "integrity_check": report.integrity_check,
                        "foreign_key_violations": report.foreign_key_violations,
                    },
                    observed_at_utc=_utc_now(),
                )
                interruption = (
                    "after_migration_0014_before_0015"
                    if index == 0
                    else "after_migration_0015_before_transition_freeze"
                )

            post_report = integrity_report(writer.connection)
            post_chain = applied_versions(writer.connection)
            terminal["post_migration_chain"] = list(post_chain)
            terminal["post_integrity"] = {
                "quick_check": post_report.quick_check,
                "integrity_check": post_report.integrity_check,
                "foreign_key_violations": post_report.foreign_key_violations,
            }
            # §5.3 item 10: recomputed independently, through a separate strictly read-only
            # connection, while the writer context stays open solely to retain the flock.
            with _read_only(catalog_path) as after:
                replayed = catalog_snapshot_digest(after, projection=measured.digest.projection)
                post_empty = _empty_state_counts(after)
            regained = tuple(
                name for name, count in post_empty.items() if count and name in measured.empty_state
            )
            if regained:
                message = f"guard table(s) {regained} gained rows during the transition"
                raise PreflightRefusalError(message)
            terminal["post_preexisting_content_sha256"] = replayed.preexisting_content_sha256
            if replayed.preexisting_content_sha256 != terminal["pre_preexisting_content_sha256"]:
                message = (
                    "the transition changed a pre-existing application row: the pre-existing "
                    "content digest moved"
                )
                raise PreflightRefusalError(message)
            ledger.append(
                "POSTCHECK_PASSED",
                {
                    "post_migration_head": f"{post_chain[-1]:04d}",
                    "post_preexisting_content_sha256": replayed.preexisting_content_sha256,
                    "integrity_check": post_report.integrity_check,
                    "foreign_key_violations": post_report.foreign_key_violations,
                },
                observed_at_utc=_utc_now(),
            )

            completed = _utc_now()
            terminal["status"] = "complete"
            terminal["completed_at_utc"] = completed
            receipt = ExecutionReceiptV4(
                command_name=TRANSITION_COMMAND_NAME,
                command_version=TRANSITION_COMMAND_VERSION,
                invocation_mode="offline_catalog_transition",
                configuration_fingerprint=_configuration_fingerprint(config),
                migration_chain_head=f"{post_chain[-1]:04d}",
                started_at_utc=started,
                completed_at_utc=completed,
                elapsed_seconds=_elapsed_seconds(started, completed),
                completion_status="complete",
            )
            return _freeze(
                directory=directory,
                ledger=ledger,
                receipt=receipt,
                terminal=terminal,
                record_type="catalog_transition",
                observed_at_utc=completed,
            )
        except BaseException as exc:
            if directory is None or ledger is None:
                # Nothing durable was created, so there is nothing to disclose and the
                # catalog is untouched at 0013. The exception is the evidence.
                raise
            _disclose_failure(
                directory=directory,
                ledger=ledger,
                terminal=terminal,
                config=config,
                started=started,
                record_type="catalog_transition",
                exc=exc,
                interruption=interruption,
                catalog_observed=catalog_observed,
                migration_chain_head=f"{TRANSITION_SOURCE_HEAD + len(applied_records):04d}",
            )
            raise


def _recheck_under_lease(
    *,
    evidence_root: Path,
    config: object,
    namespace: str,
    expected_head: int,
    require_acquisition_binding: bool,
) -> _CatalogFacts:
    """Repeat every mutable predicate while the writer lease is held (§5.3 item 2).

    Predicate 9 -- the lease itself -- is the **only** predicate omitted, and it is omitted
    structurally: ``lease_check=False`` says "this process holds the lease", which is a fact the
    caller knows for certain. Accepted Decision 099 R98 replaced the previous English-substring
    filter over refusal text, whose correctness depended on message wording and whose
    sufficiency depended on an unasserted platform property. Any other divergence refuses
    **before** a namespace, a backup, or a catalog page exists.

    ``require_acquisition_binding`` carries §5.3 item 2's own scope: it repeats §5.2's
    predicates, so the transition rechecks predicate 3 under the lease. E0's predicate list is
    §9.1, which names the §5.2 disk and lock predicates and not the M3.2 completion binding, so
    E0 passes ``False`` rather than inheriting a predicate its own ruling does not state.
    """
    refusals, _, measured = _shared_preflight(
        evidence_root=evidence_root,
        config=config,
        namespace=namespace,
        expected_head=expected_head,
        lease_check=False,
    )
    if require_acquisition_binding:
        binding_refusals, _ = _acquisition_completion_binding(
            evidence_root=evidence_root,
            catalog_path=None if measured is None else measured.catalog_path,
            binding=M3_2_COMPLETION_BINDING,
        )
        refusals.extend(binding_refusals)
    if refusals:
        message = "under-lease recheck diverged: " + "; ".join(refusals)
        raise PreflightRefusalError(message)
    if measured is None:  # pragma: no cover - the recheck above already refused
        message = "the accepted catalog could not be measured under the lease"
        raise PreflightRefusalError(message)
    return measured


def _governed_state_identity(
    connection: sqlite3.Connection,
) -> tuple[list[Mapping[str, object]], str, str]:
    """The §9.4 governed state identity: sixteen table hashes plus the plan projection.

    Each table is hashed and released before the next is materialized, under the §8.2 bound
    preflight already proved. The plan projection is hashed by the same algorithm over exactly
    ``(census_run_id, source_instance_id, observation_id, parser_state)``, and
    ``e0_catalog_state_sha256`` is :func:`hash_release` over all seventeen records.

    Returns ``(table_hash_records, plan_parser_state_hash, e0_catalog_state_sha256)``.
    """
    from disclosure_drift.m3.offline_parse import E0_PERMITTED_TABLES

    records: list[TableHash] = []
    rendered: list[Mapping[str, object]] = []
    for table in sorted(E0_PERMITTED_TABLES):
        columns = _live_columns(connection, table)
        digest = _hash_one_table(connection, table, columns)
        records.append(digest)
        rendered.append(
            {
                "table_name": digest.table_name,
                "columns": list(digest.columns),
                "row_count": digest.row_count,
                "normalized_content_sha256": digest.normalized_content_sha256,
            }
        )
    plan_columns = ("census_run_id", "source_instance_id", "observation_id", "parser_state")
    plan_hash = _hash_one_table(connection, "census_plan_sources", plan_columns)
    records.append(plan_hash)
    return (
        rendered,
        plan_hash.normalized_content_sha256,
        hash_release(records),
    )


def _source_result_records(
    connection: sqlite3.Connection,
    report: OfflineParseReport,
    recorded: Mapping[tuple[str, str], bool],
) -> tuple[list[Mapping[str, object]], dict[str, int]]:
    """Build the §9.3 per-source records and their closed count object.

    Every count is a factual zero where applicable, never an omission placeholder, and every
    aggregate is reproduced from the records rather than carried separately.
    """
    plan_rows = {
        (str(row["census_run_id"]), str(row["source_instance_id"])): row
        for row in connection.execute(
            "SELECT census_run_id, source_instance_id, source_id, observation_id, parser_state "
            "FROM census_plan_sources"
        ).fetchall()
    }
    records: list[Mapping[str, object]] = []
    counts = dict.fromkeys(SOURCE_RESULT_COUNT_KEYS, 0)
    for outcome in report.outcomes:
        key = next(
            (pair for pair in plan_rows if pair[1] == outcome.source_instance_id),
            None,
        )
        if key is None:  # pragma: no cover - the plan is read from the same catalog
            message = f"planned source {outcome.source_instance_id!r} vanished mid-run"
            raise PreflightRefusalError(message)
        row = plan_rows[key]
        entry: dict[str, object] = {
            "census_run_id": key[0],
            "source_instance_id": key[1],
            "source_id": outcome.source_id,
            "disposition": outcome.disposition,
            "parser_state_before": outcome.parser_state_before,
            "parser_state_after": outcome.parser_state_after,
            "parsed_records": int(outcome.parsed_records),
            "quarantined_records": int(outcome.quarantined_records),
            "already_present": int(getattr(outcome, "already_present", 0)),
            "ledger_event_present": bool(recorded.get(key, False)),
        }
        if row["observation_id"] is not None:
            entry["observation_id"] = str(row["observation_id"])
        if outcome.parser_run_id is not None:
            entry["parser_run_id"] = str(outcome.parser_run_id)
        records.append(entry)
        if outcome.disposition == "E0_REQUIRED_PARSE":
            counts["required_parse_count"] += 1
        elif outcome.disposition == "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE":
            counts["accepted_unavailable_count"] += 1
        else:
            counts["validation_or_provenance_only_count"] += 1
        if outcome.parser_run_id is not None:
            state = outcome.parser_state_after
            if state == "quarantined":
                counts["parser_quarantined_count"] += 1
            elif state == "failed":
                counts["parser_failed_count"] += 1
            else:
                counts["parser_completed_count"] += 1
        counts["parsed_record_count"] += int(outcome.parsed_records)
        counts["quarantined_record_count"] += int(outcome.quarantined_records)

    counts["planned_source_count"] = len(plan_rows)
    counts["full_index_registrant_observation_count"] = int(
        report.full_index_registrant_observations
    )
    counts["full_index_unbound_accession_count"] = len(report.full_index_unbound_accessions)
    counts["accession_resolution_count"] = int(report.accession_resolutions)
    counts["submissions_membership_observation_count"] = int(
        report.submissions_membership_observations
    )
    counts["substantive_membership_observation_count"] = int(
        report.substantive_membership_observations
    )
    records.sort(key=lambda item: (str(item["census_run_id"]), str(item["source_instance_id"])))
    return records, counts


def e0_execute(
    *,
    evidence_root: Path,
    config: object,
    namespace: str = E0_RUN_NAMESPACE,
    data_root: Path | None = None,
) -> ExecuteOutcome:
    """Run the real M3.3-E0 offline metadata parse (Decision 094 §9.1).

    **Not reachable.** :data:`M3_3_E0_EXECUTION_AUTHORITY` is ``None``, so the first statement
    refuses with exit ``3``. The machine below it is complete so that the later activation
    change is genuinely constant-only.

    The write set is the §6.1 sixteen tables plus the category-A
    ``census_plan_sources.parser_state`` transition, enforced by the accepted SQLite
    authorizer inside :func:`~disclosure_drift.m3.offline_parse.run_offline_metadata_parse`.
    The association projection is part of **that same** ``CatalogWriter`` invocation, not a
    second catalog writer.

    Raises:
        StageNotEnabledError: the activation constant is ``None`` (exit ``3``).
        PreflightRefusalError: a predicate, totality, or identity gate failed (exit ``4``).
    """
    from disclosure_drift.m3.offline_parse import run_offline_metadata_parse
    from disclosure_drift.paths import DataTree
    from disclosure_drift.storage.catalog import CatalogWriter

    authority = _require_activation(
        M3_3_E0_EXECUTION_AUTHORITY,
        stage="offline-parse",
        constant_name="M3_3_E0_EXECUTION_AUTHORITY",
    )
    started = _utc_now()
    catalog_path = resolve_within(
        evidence_root, OPERATIONAL_CATALOG_RELATIVE_PATH, label="operational catalog"
    )
    transition_directory = namespace_directory(evidence_root, TRANSITION_RUN_NAMESPACE)
    transition_terminal, _ = _load_terminal(
        transition_directory / TRANSITION_TERMINAL_FILENAME,
        transition_directory / TRANSITION_EVENTS_FILENAME,
        kind="TRANSITION",
    )
    if transition_terminal["status"] != "complete":
        message = "E0 requires a COMPLETE owner-accepted transition terminal record"
        raise PreflightRefusalError(message)

    terminal: dict[str, object] = {
        "schema_version": E0_TERMINAL_SCHEMA_VERSION,
        "record_type": "m3_3_e0_offline_parse",
        "run_namespace": validate_namespace(namespace),
        "command_name": E0_COMMAND_NAME,
        "command_version": E0_COMMAND_VERSION,
        "started_at_utc": started,
        "owner_authority_sha256": _authority_digest(authority),
        "catalog_relative_path": OPERATIONAL_CATALOG_RELATIVE_PATH,
        "transition_terminal_record_id": str(transition_terminal["terminal_record_id"]),
        "transition_result_token": str(transition_terminal["result_token"]),
        "configuration_fingerprint": _configuration_fingerprint(config),
        "actual_logical_request_count": 0,
        "actual_physical_attempt_count": 0,
    }
    interruption = "before_backup"
    catalog_observed = False
    directory: Path | None = None
    ledger: EventLedger | None = None

    with CatalogWriter(catalog_path, catalog_path.parent) as writer:
        try:
            measured = _recheck_under_lease(
                evidence_root=evidence_root,
                config=config,
                namespace=namespace,
                expected_head=TRANSITION_TARGET_HEAD,
                require_acquisition_binding=False,
            )
            with _read_only(catalog_path) as before:
                input_digest = input_observation_set_digest(before)
            terminal["pre_migration_chain"] = list(measured.applied)
            terminal["pre_integrity"] = dict(measured.integrity)
            terminal["input_observation_set_sha256"] = input_digest
            terminal["pre_e0_catalog_logical_sha256"] = measured.digest.require_full()

            directory = create_run_namespace(evidence_root, namespace)
            ledger = EventLedger(directory / E0_EVENTS_FILENAME, namespace, kind="E0")
            ledger.append(
                "PREFLIGHT_PASSED",
                {
                    "migration_head": f"{measured.applied[-1]:04d}",
                    "planned_source_count": measured.plan_total,
                    "input_observation_set_sha256": input_digest,
                    "pre_e0_catalog_logical_sha256": measured.digest.require_full(),
                },
                observed_at_utc=_utc_now(),
            )

            interruption = "during_backup"
            backup = _verified_backup(
                writer_connection=writer.connection,
                destination=directory / E0_BACKUP_FILENAME,
                source_digest=measured.digest,
                expected_head=TRANSITION_TARGET_HEAD,
            )
            terminal["backup"] = backup
            ledger.append(
                "BACKUP_VERIFIED",
                {
                    key: backup[key]
                    for key in (
                        "relative_path",
                        "byte_length",
                        "file_sha256",
                        "catalog_logical_sha256",
                    )
                },
                observed_at_utc=_utc_now(),
            )

            interruption = "during_e0_source_parse"
            catalog_observed = True
            # §9.2 conditions `post_migration_chain` on `failure.catalog_state_observed`, which
            # is now true for the whole remaining run. E0 applies no migration, so the chain the
            # run observed under its own lease is the chain to disclose; recording it here is
            # what makes every failure from this point on representable rather than a record its
            # own validator refuses. The success path re-measures and overwrites it.
            terminal["post_migration_chain"] = list(measured.applied)
            tree = DataTree(evidence_root if data_root is None else data_root)
            report = run_offline_metadata_parse(writer=writer, tree=tree)

            recorded: dict[tuple[str, str], bool] = {}
            plan_run_ids = {
                str(row["source_instance_id"]): str(row["census_run_id"])
                for row in writer.connection.execute(
                    "SELECT census_run_id, source_instance_id FROM census_plan_sources"
                ).fetchall()
            }
            for outcome in report.outcomes:
                run_id = plan_run_ids[outcome.source_instance_id]
                details: dict[str, object] = {
                    "census_run_id": run_id,
                    "source_instance_id": outcome.source_instance_id,
                    "source_id": outcome.source_id,
                    "disposition": outcome.disposition,
                    "parser_state_after": outcome.parser_state_after,
                    "parsed_records": int(outcome.parsed_records),
                    "quarantined_records": int(outcome.quarantined_records),
                }
                if outcome.parser_run_id is not None:
                    details["parser_run_id"] = str(outcome.parser_run_id)
                ledger.append("SOURCE_DISPOSITION_RECORDED", details, observed_at_utc=_utc_now())
                recorded[(run_id, outcome.source_instance_id)] = True

            ledger.append(
                "FULL_INDEX_OBSERVATIONS_MATERIALIZED",
                {
                    "full_index_registrant_observation_count": int(
                        report.full_index_registrant_observations
                    ),
                    "full_index_unbound_accession_count": len(report.full_index_unbound_accessions),
                },
                observed_at_utc=_utc_now(),
            )
            ledger.append(
                "ACCESSION_RESOLUTIONS_PERSISTED",
                {"accession_resolution_count": int(report.accession_resolutions)},
                observed_at_utc=_utc_now(),
            )
            totality = report.association_totality.as_record()
            terminal["association_totality"] = dict(totality)
            ledger.append("ASSOCIATIONS_MATERIALIZED", dict(totality), observed_at_utc=_utc_now())

            interruption = "after_e0_materialization_before_validation"
            post_report = integrity_report(writer.connection)
            if not post_report.passed:
                message = "post-E0 integrity gates did not pass"
                raise PreflightRefusalError(message)
            post_chain = applied_versions(writer.connection)
            terminal["post_migration_chain"] = list(post_chain)
            terminal["post_integrity"] = {
                "quick_check": post_report.quick_check,
                "integrity_check": post_report.integrity_check,
                "foreign_key_violations": post_report.foreign_key_violations,
            }
            records, counts = _source_result_records(writer.connection, report, recorded)
            terminal["source_results"] = records
            terminal["source_result_counts"] = counts

            # §9.4: recomputed independently, through a separate fresh strictly read-only
            # connection, while the writer context stays open solely to retain the flock. No
            # write transaction remains open and the writer performs no later mutation.
            with _read_only(catalog_path) as after:
                table_hashes, plan_hash, state_hash = _governed_state_identity(after)
                reproduced_input = input_observation_set_digest(after)
            if reproduced_input != input_digest:
                message = "the input observation set digest did not reproduce after the parse"
                raise PreflightRefusalError(message)
            terminal["table_hashes"] = table_hashes
            terminal["plan_parser_state_hash"] = plan_hash
            terminal["e0_catalog_state_sha256"] = state_hash
            ledger.append(
                "VALIDATION_PASSED",
                {
                    "e0_catalog_state_sha256": state_hash,
                    "integrity_check": post_report.integrity_check,
                    "foreign_key_violations": post_report.foreign_key_violations,
                },
                observed_at_utc=_utc_now(),
            )
            with _read_only(catalog_path) as again:
                _, replay_plan_hash, replay_state_hash = _governed_state_identity(again)
            if (replay_plan_hash, replay_state_hash) != (plan_hash, state_hash):
                message = "the governed state identity did not reproduce independently"
                raise PreflightRefusalError(message)
            ledger.append(
                "IDENTITIES_RECOMPUTED",
                {
                    "e0_catalog_state_sha256": replay_state_hash,
                    "table_hash_count": len(table_hashes) + 1,
                    "plan_parser_state_hash": replay_plan_hash,
                },
                observed_at_utc=_utc_now(),
            )

            interruption = "after_e0_validation_before_freeze"
            completed = _utc_now()
            terminal["status"] = "complete"
            terminal["completed_at_utc"] = completed
            receipt = ExecutionReceiptV4(
                command_name=E0_COMMAND_NAME,
                command_version=E0_COMMAND_VERSION,
                invocation_mode="offline_parse",
                configuration_fingerprint=str(terminal["configuration_fingerprint"]),
                migration_chain_head=f"{post_chain[-1]:04d}",
                started_at_utc=started,
                completed_at_utc=completed,
                elapsed_seconds=_elapsed_seconds(started, completed),
                completion_status="complete",
                parser_versions={"offline_parse": E0_COMMAND_VERSION},
                cohort_definition_digest=_cohort_digest(),
            )
            return _freeze(
                directory=directory,
                ledger=ledger,
                receipt=receipt,
                terminal=terminal,
                record_type="m3_3_e0_offline_parse",
                observed_at_utc=completed,
            )
        except BaseException as exc:
            if directory is None or ledger is None:
                raise
            terminal.setdefault("source_results", [])
            terminal.setdefault("source_result_counts", dict.fromkeys(SOURCE_RESULT_COUNT_KEYS, 0))
            _disclose_failure(
                directory=directory,
                ledger=ledger,
                terminal=terminal,
                config=config,
                started=started,
                record_type="m3_3_e0_offline_parse",
                exc=exc,
                interruption=interruption,
                catalog_observed=catalog_observed,
                migration_chain_head=f"{TRANSITION_TARGET_HEAD:04d}",
            )
            raise


# --------------------------------------------------------------------------- #
# Decision 094 §7.2 -- verify: strictly read-only, repairs nothing
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class VerifyReport:
    """One verify mode's read-only verdict.

    ``UNDETERMINED / NOT COMPLETE`` is a first-class outcome, not an error dressed as one: a
    hard kill may leave no terminal file at all, and the absence of a valid terminal is never
    read as success.
    """

    determined: bool
    passed: bool
    facts: Mapping[str, object]
    refusals: tuple[str, ...]

    @property
    def lines(self) -> tuple[str, ...]:
        rendered = [f"  {key:<38}: {value}" for key, value in self.facts.items()]
        if not self.determined:
            rendered.append("  UNDETERMINED / NOT COMPLETE")
        rendered.extend(f"  REFUSED: {reason}" for reason in self.refusals)
        return tuple(rendered)


def _backup_refusals(directory: Path, document: Mapping[str, object], *, kind: str) -> list[str]:
    """Reproduce the run's persisted content identity from the backup it actually wrote.

    The backup is the transition's (and E0's) durable content identity: the terminal records its
    byte length, file digest, and full logical catalog digest, and the execute path proved that
    digest equal to the source snapshot's before any migration ran. Recomputing all three here
    is what makes ``backup`` a checked claim rather than a recorded one.

    Only the artifact's fixed **name** is taken from the recorded relative path; the directory
    is the namespace already resolved, so no path in the record can redirect this read.
    """
    recorded = document.get("backup")
    if not isinstance(recorded, Mapping):
        return []
    backup_path = directory / str(recorded["relative_path"]).rsplit("/", 1)[-1]
    if backup_path.is_symlink() or not backup_path.is_file():
        return ["the run's verified backup is absent or is not a regular file"]
    digest, length = file_digest(backup_path)
    if digest != recorded["file_sha256"] or length != recorded["byte_length"]:
        return ["the run's verified backup no longer hashes to the identity the terminal froze"]
    with _read_only(backup_path) as backup:
        logical = catalog_snapshot_digest(backup).require_full()
    refusals: list[str] = []
    if logical != recorded["catalog_logical_sha256"]:
        refusals.append(
            "the run's verified backup no longer reproduces the logical catalog digest the "
            "terminal froze"
        )
    recorded_pre = document.get(
        "pre_catalog_logical_sha256" if kind == "TRANSITION" else "pre_e0_catalog_logical_sha256"
    )
    if recorded_pre is not None and logical != recorded_pre:
        refusals.append(
            "the run's verified backup no longer reproduces the pre-run catalog logical digest "
            "the terminal froze"
        )
    return refusals


def _e0_identity_refusals(
    connection: sqlite3.Connection, document: Mapping[str, object]
) -> list[str]:
    """Independently reproduce the §9.4 governed-state identities from the fixed catalog.

    Only when the terminal carries them: they are permitted exactly when ``VALIDATION_PASSED``
    is durable, so a disclosed failure before that boundary has nothing to reproduce and is not
    made to look as though it does.
    """
    if "e0_catalog_state_sha256" not in document:
        return []
    table_hashes, plan_hash, state_hash = _governed_state_identity(connection)
    refusals: list[str] = []
    if state_hash != document["e0_catalog_state_sha256"]:
        refusals.append(
            "the fixed catalog no longer reproduces the E0 governed catalog-state identity"
        )
    if plan_hash != document.get("plan_parser_state_hash"):
        refusals.append("the fixed catalog no longer reproduces the E0 plan parser-state identity")
    if list(table_hashes) != document.get("table_hashes"):
        refusals.append("the fixed catalog no longer reproduces the E0 table hash records")
    return refusals


def _catalog_state_refusals(
    *, evidence_root: Path, directory: Path, document: Mapping[str, object], kind: str
) -> tuple[list[str], dict[str, object]]:
    """Compare the fixed catalog's current state with what this terminal record froze (§7.2).

    Accepted Decision 099 R98, correcting Decision 098 MINOR-2: §7.2's verify row lists "catalog
    state" among what verify validates, and the previous implementation never opened the catalog
    at all -- so a complete terminal verified PASS even after the accepted catalog had drifted
    from the chain and integrity report it recorded.

    Strictly read-only, through ``SQLITE_OPEN_READONLY``, exactly as preflight is. Each
    comparison is made only where the terminal actually asserts the fact, because a failed run
    that never observed catalog state asserts nothing about it and must not be measured as if
    it had.
    """
    refusals: list[str] = []
    facts: dict[str, object] = {}
    # Counted rather than assumed: a disclosed failure that never observed catalog state asserts
    # nothing to compare, and reporting "matches" for zero comparisons would be an overclaim of
    # exactly the kind this correction exists to remove.
    compared = 0
    try:
        catalog_path = resolve_within(
            evidence_root, OPERATIONAL_CATALOG_RELATIVE_PATH, label="operational catalog"
        )
        if not catalog_path.exists():
            refusals.append("the fixed catalog is absent beneath the resolved private root")
        else:
            _refuse_symlinked_descent(evidence_root, catalog_path)
            with _read_only(catalog_path) as connection:
                chain = list(applied_versions(connection))
                report = integrity_report(connection)
                facts["catalog_migration_head"] = f"{chain[-1]:04d}" if chain else "none"
                facts["catalog_integrity_check"] = report.integrity_check
                if "post_migration_chain" in document:
                    compared += 1
                    if document["post_migration_chain"] != chain:
                        refusals.append(
                            "the fixed catalog's applied migration chain is no longer the chain "
                            "this terminal record froze"
                        )
                recorded_integrity = document.get("post_integrity")
                if isinstance(recorded_integrity, Mapping):
                    compared += 1
                    if dict(recorded_integrity) != {
                        "quick_check": report.quick_check,
                        "integrity_check": report.integrity_check,
                        "foreign_key_violations": report.foreign_key_violations,
                    }:
                        refusals.append(
                            "the fixed catalog's integrity report is no longer the report this "
                            "terminal record froze"
                        )
                if kind == "E0" and "e0_catalog_state_sha256" in document:
                    compared += 3
                    refusals.extend(_e0_identity_refusals(connection, document))
            if isinstance(document.get("backup"), Mapping):
                compared += 1
                refusals.extend(_backup_refusals(directory, document, kind=kind))
    except (DisclosureDriftError, sqlite3.Error) as exc:
        refusals.append(f"the fixed catalog state could not be verified: {exc}")
    except OSError as exc:
        # An OSError ordinarily names the offending file, which here would be a private path.
        refusals.append(f"the fixed catalog state could not be verified ({type(exc).__name__})")
    facts["catalog_state_comparisons"] = compared
    facts["catalog_state_compared"] = "REFUSED" if refusals else "consistent"
    return refusals, facts


def _verify(
    *,
    evidence_root: Path,
    namespace: str,
    kind: str,
    terminal_filename: str,
    events_filename: str,
) -> VerifyReport:
    """Validate one durable namespace, and the catalog state it recorded, changing no byte."""
    facts: dict[str, object] = {"run_namespace": namespace}
    directory = namespace_directory(evidence_root, namespace)
    if not directory.is_dir():
        facts["run_directory"] = "absent"
        return VerifyReport(determined=False, passed=False, facts=facts, refusals=())
    facts["run_directory"] = "present"
    terminal_path = directory / terminal_filename
    events_path = directory / events_filename
    if not events_path.exists():
        facts["event_ledger"] = "absent"
        return VerifyReport(determined=False, passed=False, facts=facts, refusals=())
    if not terminal_path.exists():
        # A hard kill can leave a ledger and no terminal. That is exactly UNDETERMINED, and
        # the surviving ledger is still verified so the operator learns how far the run got.
        try:
            events = read_event_ledger(events_path, kind=kind)
        except (LedgerIntegrityError, OSError) as exc:
            return VerifyReport(determined=False, passed=False, facts=facts, refusals=(str(exc),))
        facts["event_count"] = len(events)
        facts["last_event"] = str(events[-1]["event_type"]) if events else "none"
        facts["terminal_record"] = "absent"
        return VerifyReport(determined=False, passed=False, facts=facts, refusals=())
    try:
        document, events = _load_terminal(terminal_path, events_path, kind=kind)
    except (E0Error, OSError) as exc:
        return VerifyReport(determined=True, passed=False, facts=facts, refusals=(str(exc),))
    facts["terminal_record"] = "present"
    facts["status"] = str(document["status"])
    facts["event_count"] = len(events)
    facts["terminal_record_id"] = str(document["terminal_record_id"])
    facts["result_token"] = str(document["result_token"])
    facts["execution_receipt_id"] = str(document["execution_receipt_id"])
    refusals: list[str] = []
    receipt_path = directory / OPERATOR_RECEIPT_FILENAME
    if not receipt_path.exists():
        refusals.append("the run's execution receipt is absent")
    else:
        try:
            receipt = inspect_receipt(receipt_path)
        except (DisclosureDriftError, OSError) as exc:
            refusals.append(f"the run's execution receipt did not validate: {exc}")
        else:
            if receipt["receipt_id"] != document["execution_receipt_id"]:
                refusals.append("the terminal record does not bind the run's actual receipt")
    for artifact in (terminal_path, events_path, receipt_path):
        if artifact.exists() and (artifact.stat().st_mode & 0o777) != _FILE_MODE:
            refusals.append(f"{artifact.name} is not mode 0600")
    if (directory.stat().st_mode & 0o777) != _DIRECTORY_MODE:
        refusals.append("the run directory is not mode 0700")
    catalog_refusals, catalog_facts = _catalog_state_refusals(
        evidence_root=evidence_root, directory=directory, document=document, kind=kind
    )
    facts.update(catalog_facts)
    refusals.extend(catalog_refusals)
    return VerifyReport(
        determined=True,
        passed=not refusals and document["status"] == "complete",
        facts=facts,
        refusals=tuple(refusals),
    )


def transition_verify(
    *, evidence_root: Path, namespace: str = TRANSITION_RUN_NAMESPACE
) -> VerifyReport:
    """Validate the transition namespace, receipt, ledger, terminal, catalog state, identities.

    Strictly read-only. It repairs nothing, resumes nothing, and restores nothing: a defect
    found here is preserved and returned to the owner (§11). The fixed catalog is opened
    read-only and its current chain and integrity are compared with what the terminal froze, and
    the run's verified backup is re-hashed against the content identity the terminal recorded.
    """
    return _verify(
        evidence_root=evidence_root,
        namespace=namespace,
        kind="TRANSITION",
        terminal_filename=TRANSITION_TERMINAL_FILENAME,
        events_filename=TRANSITION_EVENTS_FILENAME,
    )


def e0_verify(*, evidence_root: Path, namespace: str = E0_RUN_NAMESPACE) -> VerifyReport:
    """Validate the E0 namespace, receipt, ledger, terminal, catalog state, and identities.

    Strictly read-only. In addition to the shared checks, the §9.4 governed-state identities are
    **independently reproduced** from the fixed catalog whenever the terminal carries them, so a
    post-freeze mutation of any of the sixteen tables or of the plan projection is detected here
    rather than assumed away.
    """
    return _verify(
        evidence_root=evidence_root,
        namespace=namespace,
        kind="E0",
        terminal_filename=E0_TERMINAL_FILENAME,
        events_filename=E0_EVENTS_FILENAME,
    )


# --------------------------------------------------------------------------- #
# Decision 094 §7 -- the two operator surfaces
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class OperatorResult:
    """One operator invocation's exit code and rendered non-secret output."""

    exit_code: int
    lines: tuple[str, ...]


def _operator_command(
    *,
    mode: str,
    command: str,
    repository_root: Path,
    config: object,
    environ: Mapping[str, str] | None,
    preflight: Callable[..., PreflightReport],
    execute: Callable[..., ExecuteOutcome],
    verify: Callable[..., VerifyReport],
    activation: str | None,
    constant_name: str,
) -> OperatorResult:
    """Dispatch one mode, mapping every outcome onto the §7.3 exit table.

    The exit codes are not interchangeable and the mapping is deliberate: ``1`` is a
    configuration or private-root failure -- a mistake in the invocation; ``3`` is "this stage
    is not enabled", which is a governance fact and never a finding about the catalog; and
    ``4`` is a gate that actually ran and refused.

    **The activation check comes first, before the private root is even resolved.** That
    ordering is deliberate and is what makes exit ``3`` unconditional. If the root were
    resolved first, an unset variable would mask the "not enabled" answer behind exit ``1``,
    and a *set* variable would become a precondition for learning it -- which is exactly the
    kind of environment-value substitution §7.2 forbids. Whether the stage is enabled depends
    on the source constant and on nothing else, so nothing else is consulted before saying so.
    """
    if mode not in OPERATOR_MODES:
        return OperatorResult(
            exit_code=EXIT_USAGE,
            lines=(f"--mode must be one of {', '.join(OPERATOR_MODES)}",),
        )
    header = (f"{command} --mode {mode}",)
    if mode == "execute":
        try:
            _require_activation(activation, stage=command, constant_name=constant_name)
        except StageNotEnabledError as exc:
            return OperatorResult(exit_code=EXIT_STAGE_NOT_ENABLED, lines=(*header, f"  {exc}"))
    try:
        evidence_root = resolve_evidence_root(repository_root, environ=environ)
    except EvidenceRootUnsetError as exc:
        return OperatorResult(exit_code=EXIT_CONFIG_ERROR, lines=(*header, f"  {exc}"))
    try:
        if mode == "preflight":
            report = preflight(evidence_root=evidence_root, config=config)
            verdict = "PASS" if report.passed else "REFUSED"
            return OperatorResult(
                exit_code=EXIT_OK if report.passed else EXIT_GATE_FAILURE,
                lines=(*header, *report.lines, f"  preflight: {verdict}"),
            )
        if mode == "verify":
            result = verify(evidence_root=evidence_root)
            if not result.determined:
                return OperatorResult(
                    exit_code=EXIT_GATE_FAILURE,
                    lines=(*header, *result.lines),
                )
            verdict = "PASS" if result.passed else "REFUSED"
            return OperatorResult(
                exit_code=EXIT_OK if result.passed else EXIT_GATE_FAILURE,
                lines=(*header, *result.lines, f"  verify: {verdict}"),
            )
        outcome = execute(evidence_root=evidence_root, config=config)
    except StageNotEnabledError as exc:
        return OperatorResult(exit_code=EXIT_STAGE_NOT_ENABLED, lines=(*header, f"  {exc}"))
    except (DisclosureDriftError, sqlite3.Error) as exc:
        return OperatorResult(exit_code=EXIT_GATE_FAILURE, lines=(*header, f"  {exc}"))
    except OSError as exc:
        # An OSError ordinarily carries the offending filename, which may be an absolute
        # private path. Report the error class only.
        return OperatorResult(
            exit_code=EXIT_GATE_FAILURE,
            lines=(*header, f"  {type(exc).__name__} while reading or writing an artifact"),
        )
    return OperatorResult(
        exit_code=EXIT_OK,
        lines=(
            *header,
            f"  status                                : {outcome.status}",
            f"  run namespace                         : {outcome.run_namespace}",
            f"  terminal record id                    : {outcome.terminal_record_id}",
            f"  result token                          : {outcome.result_token}",
        ),
    )


def run_prepare_e0_catalog_command(
    *,
    mode: str,
    config: object,
    repository_root: Path,
    environ: Mapping[str, str] | None = None,
) -> OperatorResult:
    """``m3 prepare-e0-catalog --config … --mode {preflight,execute,verify}`` (§7.1).

    Takes no evidence-root, catalog, namespace, migration-list, force, resume, overwrite,
    repair, network, or output option. There is exactly one catalog, exactly one namespace,
    and exactly one lawful transition, and none of them is an operator choice.
    """
    return _operator_command(
        mode=mode,
        command=TRANSITION_COMMAND_NAME,
        repository_root=repository_root,
        config=config,
        environ=environ,
        preflight=transition_preflight,
        execute=transition_execute,
        verify=transition_verify,
        activation=PRE_E0_CATALOG_TRANSITION_AUTHORITY,
        constant_name="PRE_E0_CATALOG_TRANSITION_AUTHORITY",
    )


def run_offline_parse_command(
    *,
    mode: str,
    config: object,
    repository_root: Path,
    environ: Mapping[str, str] | None = None,
) -> OperatorResult:
    """``m3 offline-parse --config … --mode {preflight,execute,verify}`` (§7.1)."""
    return _operator_command(
        mode=mode,
        command=E0_COMMAND_NAME,
        repository_root=repository_root,
        config=config,
        environ=environ,
        preflight=e0_preflight,
        execute=e0_execute,
        verify=e0_verify,
        activation=M3_3_E0_EXECUTION_AUTHORITY,
        constant_name="M3_3_E0_EXECUTION_AUTHORITY",
    )
