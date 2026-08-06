"""Milestone 3.2 bounded acquisition driver (accepted contract §§9-14; T2 packet §6, T2.2-T2.3).

This module is the **driver-side integration** of surfaces that already exist and are accepted.
It writes no storage layer, no catalog schema, and no transport of its own: the operational
catalog (:mod:`disclosure_drift.storage.catalog`), the immutable content-addressed raw store
(:mod:`disclosure_drift.sec.raw_store`), the observation recorder
(:mod:`disclosure_drift.sec.observation_catalog`), the snapshot store
(:mod:`disclosure_drift.sec.snapshots`), the response-policy client
(:mod:`disclosure_drift.sec.http_client`), the shared physical-attempt gate
(:mod:`disclosure_drift.sec.request_ceiling`), and the source registry
(:mod:`disclosure_drift.sec.source_registry`) are all consumed **unchanged**. Every one of them is
a prohibited path for this stage, which is precisely why the integration lives here.

Three properties are structural rather than conventional:

**No transport is constructible here.** Importing or constructing :class:`AcquisitionEngine` opens
no socket and builds no client. The transport arrives as an injected object, and the engine
refuses to run without an explicit :class:`LiveOperationAuthorization` that no configuration key,
contract acceptance, gate token, or ceiling value can synthesize. The complete live-authorization
conjunction is enforced by the later operator layer; what this module guarantees is a fail-closed
boundary that *makes* that conjunction enforceable, and a refusal that happens before the first
transport call rather than after it.

**The plan is consumed, never re-derived.** :meth:`AcquisitionEngine.preflight` binds an approved
plan by its own content hash, the named window, and the exact approved ceiling integer. A
mismatch on any of the three refuses before any wire activity (contract §9).

**Termination is not success.** A request that reaches a terminal disposition is *classified*; it
is satisfied only by a hash-verified, provenance-complete object (new, or a byte-identical reuse
that independently passes the same checks). A window with any required object absent is
incomplete, and :class:`WindowOutcome` cannot report otherwise — the distinction the accepted
contract §14 draws is represented in the type, not left to a caller's discipline.

**Routes are not interchangeable.** How a payload is retrieved, and what provenance it owes, are
read from the registered route specification rather than fixed uniformly: a bulk archive is
streamed rather than buffered (:func:`route_is_streamed`), and its validated members are recorded
as archive lineage beside it. Treating every route alike would quarantine the bulk submissions
object on size alone, and leave it without the member lineage its later reuse and reconciliation
depend on.

Recovery *observability* is provided here (partial objects, orphans, missing referents, uncertain
outcomes, cumulative attempt state). Recovery **repair**, reconciliation reporting, drift
inspection, and resume are stage T2.4 and are deliberately absent.
"""

from __future__ import annotations

import os
import re
import sqlite3
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal

from disclosure_drift.errors import (
    CatalogWriteError,
    DisclosureDriftError,
    RawObjectIntegrityError,
)
from disclosure_drift.m3.evidence_paths import require_external_evidence_root
from disclosure_drift.m3.receipt import ReceiptValidationError, inspect_receipt
from disclosure_drift.m3.recovery import (
    RecoveryState,
    inspect_recovery_state,
    read_only_catalog,
)
from disclosure_drift.m3.request_plan import (
    M3_2A_BOOTSTRAP_ROUTES,
    RequestPlan,
    derive_a_reachable,
    request_plan_from_document,
)
from disclosure_drift.paths import DataTree, PathPolicyError, relative_to_root
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.archive import ArchiveDefenceError, ArchiveMember, iter_members
from disclosure_drift.sec.http_client import ProhibitedRetrievalError, SecClient
from disclosure_drift.sec.index_plan import CoverageWindow, plan_index_instances
from disclosure_drift.sec.observation_catalog import (
    ObservationRecorder,
    RecoveryEvent,
    load_observations,
    open_recovery_state,
    rebuild_audit_projection,
    reconcile,
    record_recovery_events,
    resolve_recovery_state,
    validate_audit_projection,
)
from disclosure_drift.sec.raw_store import LINEAGE_SUFFIX, RawStore
from disclosure_drift.sec.request_ceiling import (
    PhysicalAttemptCeiling,
    RequestCeilingExhaustedError,
)
from disclosure_drift.sec.snapshots import SnapshotIndex, SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import (
    SOURCES,
    SourceSpec,
    filing_body_url_is_prohibited,
    require_registered,
)
from disclosure_drift.sec.urls import request_identity
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import applied_versions, integrity_report

__all__ = [
    "ACQUISITION_WINDOWS",
    "FINAL_MIGRATION_VERSION",
    "M3_2B_DEPENDENT_ROUTES",
    "OPERATIONAL_CATALOG_RELATIVE_PATH",
    "RECOVERY_ACTIONS",
    "AcquisitionEngine",
    "AcquisitionError",
    "AcquisitionGateError",
    "CatalogPreparation",
    "CatalogPreparationError",
    "CatalogReconstruction",
    "ContainmentError",
    "ContinuationProposal",
    "ContinuationRequest",
    "CumulativeAttemptAccounting",
    "DriftListingEntry",
    "LiveOperationAuthorization",
    "LogicalRequest",
    "ReconciliationItem",
    "RecoveryActionResult",
    "RecoveryObservation",
    "RepairRefusedError",
    "RequestOutcome",
    "RequestReconciliation",
    "StorageBinding",
    "StoragePreparationError",
    "StoreFinding",
    "WindowOutcome",
    "apply_recovery_action",
    "conditional_validators",
    "derive_logical_requests",
    "load_approved_plan",
    "observe_recovery_state",
    "prepare_operational_catalog",
    "prepare_storage",
    "propose_continuation",
    "reconcile_requests",
    "reconstruct_catalog_state",
    "resolve_within",
    "route_is_streamed",
    "verified_reusable_predecessor",
]

#: The operational catalog's path relative to the external evidence root (contract §16).
OPERATIONAL_CATALOG_RELATIVE_PATH: Final = "catalogs/m3_2a_operational.sqlite3"

#: The migration chain the operational catalog is created at. Contract §11 fixes it: "created
#: only inside an authorized window at migration chain ``0013``". No ``0014`` exists or is implied,
#: so a chain that ends anywhere else is a refusal rather than an upgrade.
FINAL_MIGRATION_VERSION: Final = 13

#: The two acquisition windows. A window name outside this set is refused rather than treated as
#: an unrecognized-but-harmless label.
ACQUISITION_WINDOWS: Final[tuple[str, ...]] = ("M3.2A", "M3.2B")

#: The two dependent route families of the M3.2B window (contract §6). Named here so window
#: separation can be enforced in **both** directions: a dependent request in M3.2A and a bootstrap
#: request in M3.2B are each contract §17 stop condition 5, and a guard that checks only one
#: direction leaves the other silently permitted.
M3_2B_DEPENDENT_ROUTES: Final[tuple[str, ...]] = (
    "sec_submissions_entity",
    "sec_submissions_historical",
)

_INDEX_ROUTE: Final = "sec_full_index_company"
_ANNOUNCEMENT_ROUTE: Final = "sec_edgar_calendar_announcement"
_INSTANCE_KEY_PATTERN: Final = re.compile(r"^(?P<year>\d{4})QTR(?P<quarter>[1-4])$")

#: Reason recorded when a required quarterly index instance is left absent (registered code;
#: `reasons.py` is untouched). The registry defines it as "a required quarterly index instance was
#: not retrieved or not usably parsed", which is exactly the archival-absence and quarantined-body
#: cases this driver must make durable rather than leave uncoded.
_INDEX_ABSENT_REASON: Final = "INDEX_INSTANCE_UNAVAILABLE"

#: Reason recorded when a REQUIRED non-quarterly-index M3.2A object is left terminally absent —
#: its committed observation is ``failed`` or ``quarantined`` (registered under Decision 040 §4).
#: It marks that the required object remains unavailable, and it coexists with — never replaces —
#: a more specific defect code such as ``SEC_RESPONSE_MALFORMED`` or ``RAW_ARCHIVE_INVALID``.
#: Quarterly index instances keep ``INDEX_INSTANCE_UNAVAILABLE``; stopped, interrupted,
#: ceiling-exhausted, and not-attempted requests keep their run classifications and never receive
#: this code merely for lacking an object; no M3.2B mapping is authorized.
_REQUIRED_OBJECT_ABSENT_REASON: Final = "SOURCE_REQUIRED_OBJECT_UNAVAILABLE"

#: Suffix filter for bulk-archive members. The submissions archive carries one JSON document per
#: filer; the accepted archive reader applies this filter and validates every member it yields.
_ARCHIVE_MEMBER_SUFFIX: Final = ".json"

#: Recorded on every observation this driver writes. Entity-specific routes additionally require a
#: purpose of at least twelve characters (``http_client.SecClient.fetch``), which this satisfies.
_ACQUISITION_PURPOSE: Final = (
    "acquire approved Milestone 3.2 metadata object under the owner-approved request plan"
)

RequestDisposition = Literal[
    "satisfied_new",
    "satisfied_duplicate",
    "satisfied_reused",
    "absent",
    "quarantined",
    "failed",
    "stopped",
    "not_attempted",
]
"""Terminal dispositions of one planned logical request.

Three of these are satisfying, and they are kept apart because the accepted accounting keeps them
apart: contract §22 reports ``NEW_RAW_OBJECTS``, ``DUPLICATES_RECONCILED``, and ``CACHE_HITS`` as
three separate quantities, and T2 packet §12 maps a reuse to ``cache_hit_count`` rather than to
``raw_object_count``. Collapsing them would make those figures underivable from a window outcome.

* ``satisfied_new`` — a new immutable object was promoted (``stored_new`` or ``superseded``).
* ``satisfied_duplicate`` — the response was byte-identical to the preserved object, which was
  reconciled and reused rather than rewritten (``unchanged_content``).
* ``satisfied_reused`` — a conditional request confirmed the preserved snapshot (``304``).

``stopped`` is distinct from ``not_attempted``: it marks a request that consumed one or more
physical attempts before the window stopped, which ``not_attempted`` would misreport as untouched.
"""

CompletionStatus = Literal[
    "complete",
    "incomplete",
    "stopped_at_ceiling",
    "stopped_by_gate",
    "failed",
]


class AcquisitionError(DisclosureDriftError):
    """Base class for every refusal this driver raises."""


class ContainmentError(AcquisitionError):
    """Raised when a governed path would escape the evidence root.

    No message names a resolved absolute path: the operator supplied the root and already knows
    it, and master plan §17 stop condition 12 bars an absolute personal path from any output.
    """


class CatalogPreparationError(AcquisitionError):
    """Raised when the operational catalog cannot be created or verified as required."""


class StoragePreparationError(AcquisitionError):
    """Raised when the isolated M3.2 data root cannot be prepared safely."""


class AcquisitionGateError(AcquisitionError):
    """Raised when a gate refuses, always before the wire activity it guards.

    Distinct from the two preparation errors so a caller can map a gate refusal to the exit code
    the accepted command surface reserves for it, without string-matching a message.
    """


#: Bounded operational failures a single request may raise once it has been placed: the object
#: store, the catalog, the path policy, and the filesystem beneath them. Enumerated rather than
#: caught as a base class on purpose — :class:`AcquisitionGateError` is also a
#: ``DisclosureDriftError``, and a gate refusal must never be swallowed into a request outcome.
#: A programmer error (``TypeError``, ``AttributeError``, ``KeyError``) is likewise absent and
#: still propagates, because turning a defect into a recorded "failed request" would hide it.
_OPERATIONAL_FAILURES: Final = (
    RawObjectIntegrityError,
    CatalogWriteError,
    PathPolicyError,
    sqlite3.Error,
    OSError,
)

#: Public description for each operational failure class, most specific first.
#:
#: These exceptions carry private arguments: an ``OSError`` names the absolute path it failed
#: on, a storage error names the object it refused to overwrite, and a SQLite error can name
#: the database file. Copying ``str(exc)`` into an outcome would publish an operator's private
#: evidence-root layout through a field the later operator surfaces, reports, and receipts all
#: read — the same absolute-path exposure the containment refusals are careful never to make.
#: So the detail is **built from this table**, never from the exception's own arguments: the
#: class name says what failed and the description says what kind of operation it was. Nothing
#: is concealed — an operational failure is still reported as one, still terminates the window,
#: and still leaves its committed rows observable.
_OPERATIONAL_FAILURE_DESCRIPTIONS: Final[tuple[tuple[type[BaseException], str], ...]] = (
    (ArchiveDefenceError, "an accepted archive protection refused the acquired archive"),
    (RawObjectIntegrityError, "an immutable raw object could not be written or verified"),
    (CatalogWriteError, "the operational catalog refused a write"),
    (PathPolicyError, "a governed path was refused by the path policy"),
    (sqlite3.Error, "the operational catalog reported a database error"),
    (OSError, "a filesystem operation failed"),
)


def _operational_detail(exc: BaseException) -> str:
    """A public description of one operational failure, carrying no private argument.

    Deliberately derived from the exception's *class* alone. The message, filename, and any
    other argument the exception carries are never read, so no absolute path, response body,
    or member payload can reach an outcome through this seam regardless of what the underlying
    library chose to put in them.
    """
    for kind, description in _OPERATIONAL_FAILURE_DESCRIPTIONS:
        if isinstance(exc, kind):
            return f"{type(exc).__name__}: {description}"
    return f"{type(exc).__name__}: an operational failure occurred"  # pragma: no cover - total


# --------------------------------------------------------------------------- #
# Containment — every governed path is proved inside the evidence root
# --------------------------------------------------------------------------- #
def resolve_within(root: Path, relative: str | Path, *, label: str) -> Path:
    """Return ``root / relative``, proved to stay inside ``root``.

    Containment is decided on **fully resolved** paths, so a symlink cannot launder an escape:
    a component that resolves outside the root is refused even when the lexical path looks
    contained. An absolute ``relative`` and any ``..`` component are refused outright rather than
    normalized, because normalizing an escape attempt into a lawful path is exactly the silent
    relaxation CLAUDE.md rule 12 forbids.

    The root itself is resolved first, which makes the check correct when the root is reached
    through a symlink (a macOS ``/tmp`` fixture, for instance) rather than refusing every path
    under such a root.

    Args:
        root: The containing directory. Must be absolute.
        relative: A path relative to ``root``.
        label: What the path is, for the refusal message. Never a resolved path.

    Raises:
        ContainmentError: the root is not absolute, or the result escapes it.
    """
    if not root.is_absolute():
        message = f"the {label} root must be an absolute path"
        raise ContainmentError(message)

    candidate = Path(relative)
    if candidate.is_absolute():
        message = (
            f"the {label} must be given relative to the evidence root; an absolute path is "
            "refused because it names a location the root does not govern"
        )
        raise ContainmentError(message)
    if ".." in candidate.parts:
        message = (
            f"the {label} contains a parent-directory component; a path that walks out of the "
            "evidence root is refused rather than normalized"
        )
        raise ContainmentError(message)

    resolved_root = Path(os.path.realpath(root))
    resolved = Path(os.path.realpath(root / candidate))
    if resolved != resolved_root and resolved_root not in resolved.parents:
        message = (
            f"the {label} resolves outside the evidence root; a symlink or link component may "
            "not move a governed artifact out of the root that governs it"
        )
        raise ContainmentError(message)
    return resolved


def _refuse_symlinked_ancestors(root: Path, target: Path, *, label: str) -> None:
    """Refuse when any component between ``root`` and ``target`` is a symlink.

    :func:`resolve_within` already proves the *destination* stays inside the root. This is the
    stricter check the accepted contract's stop condition 13 asks for — "symlink detection at any
    governed path" — and it refuses a symlink that happens to point back inside the root, which
    containment alone would allow.

    ``target`` must be the **lexical** ``root / relative`` path, not a resolved one: resolution
    has already followed every symlink, so a resolved path has none left to detect. Passing a
    resolved path here would make this check silently vacuous.
    """
    root_depth = len(root.parts)
    current = target
    while len(current.parts) > root_depth and current.parent != current:
        if current.is_symlink():
            message = (
                f"a component of the {label} is a symbolic link; governed artifacts are addressed "
                "by real paths only"
            )
            raise ContainmentError(message)
        current = current.parent


# --------------------------------------------------------------------------- #
# Subphase A.1 — the operational catalog
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CatalogPreparation:
    """The result of creating or opening one operational catalog."""

    database_path: Path
    lock_directory: Path
    applied_migrations: tuple[str, ...]
    seeded_counts: Mapping[str, int]
    migration_chain_head: int
    created: bool

    @property
    def chain_is_exact(self) -> bool:
        """Whether the applied chain ends exactly at the accepted final migration."""
        return self.migration_chain_head == FINAL_MIGRATION_VERSION


def prepare_operational_catalog(
    *,
    evidence_root: Path,
    relative_path: str | Path = OPERATIONAL_CATALOG_RELATIVE_PATH,
    lock_relative_path: str | Path | None = None,
    repository_root: Path | None = None,
) -> CatalogPreparation:
    """Create or open the operational catalog at the caller-supplied path.

    The caller always supplies the path; there is no default location and, deliberately, no
    fallback to a repository-local database — a missing or unusable root refuses rather than
    silently writing inside the checkout.

    The chain is applied through the accepted ``CatalogWriter.migrate()`` →
    ``seed_reference_data()`` idiom, which commits each migration with its immutable
    name/checksum provenance row and verifies the applied chain before and after. This function
    adds the two checks that idiom does not make: that the resulting chain **ends exactly** at
    :data:`FINAL_MIGRATION_VERSION`, and that the three SQLite integrity gates pass.

    Args:
        evidence_root: The owner-controlled external root. Validated as external when
            ``repository_root`` is supplied.
        relative_path: The catalog path relative to ``evidence_root``.
        lock_relative_path: Directory for the single-writer lease. Defaults to the catalog's own
            parent directory.
        repository_root: When given, ``evidence_root`` is additionally proved to be outside this
            checkout before anything is created.

    Raises:
        CatalogPreparationError: the chain, the seeds, or the integrity gates are not as required.
        ContainmentError: a governed path escapes the evidence root.
    """
    root = _validated_root(evidence_root, repository_root)
    database_path = resolve_within(root, relative_path, label="operational catalog")
    _refuse_symlinked_ancestors(root, root / relative_path, label="operational catalog path")

    lock_directory = (
        database_path.parent
        if lock_relative_path is None
        else resolve_within(root, lock_relative_path, label="catalog lock directory")
    )
    created = not database_path.exists()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    lock_directory.mkdir(parents=True, exist_ok=True)

    if not created:
        _refuse_inconsistent_recorded_chain(database_path)

    try:
        with CatalogWriter(database_path, lock_directory) as writer:
            applied = writer.migrate()
            seeded = writer.seed_reference_data()
            chain = applied_versions(writer.connection)
            report = integrity_report(writer.connection)
    except (DisclosureDriftError, sqlite3.Error) as exc:
        # A pre-existing database that is not this catalog surfaces as a raw sqlite3 error from
        # the accepted provenance check. Wrapping it keeps the refusal a domain fact — an
        # incompatible catalog — rather than leaking a driver-level error a caller would have to
        # string-match, and it keeps the refusal fail-closed either way.
        message = f"the operational catalog could not be prepared: {exc}"
        raise CatalogPreparationError(message) from exc

    if not chain:
        message = "the operational catalog carries no applied migration chain"
        raise CatalogPreparationError(message)
    head = chain[-1]
    if head != FINAL_MIGRATION_VERSION:
        message = (
            f"the operational catalog's migration chain ends at {head:04d}, not the accepted "
            f"{FINAL_MIGRATION_VERSION:04d}; this stage creates no migration, so a different "
            "chain head is an incompatible catalog rather than something to upgrade"
        )
        raise CatalogPreparationError(message)
    if tuple(chain) != tuple(range(1, FINAL_MIGRATION_VERSION + 1)):
        message = (
            "the operational catalog's migration chain is not contiguous from 0001 to "
            f"{FINAL_MIGRATION_VERSION:04d}; a gapped chain is refused rather than filled in"
        )
        raise CatalogPreparationError(message)
    if not report.passed:
        message = (
            "the operational catalog failed a SQLite integrity gate: "
            f"quick_check={report.quick_check}, integrity_check={report.integrity_check}, "
            f"foreign_key_violations={report.foreign_key_violations}"
        )
        raise CatalogPreparationError(message)

    return CatalogPreparation(
        database_path=database_path,
        lock_directory=lock_directory,
        applied_migrations=applied,
        seeded_counts=dict(seeded),
        migration_chain_head=head,
        created=created,
    )


def _refuse_inconsistent_recorded_chain(database_path: Path) -> None:
    """Refuse an existing database whose recorded chain is not a contiguous prefix.

    This is a **read-only pre-flight look**, not a second migrator. The accepted
    ``apply_migrations`` remains the sole authority on what may be applied and on checksum
    provenance; it already refuses an unknown version, a gap, or a checksum drift. What it cannot do
    is explain a *partially recorded* chain: re-applying `0006` onto a schema that already carries
    `0013`'s objects fails deep inside SQLite with "duplicate column name", which is fail-closed but
    tells an operator nothing about what is actually wrong.

    So this states the domain fact first — the recorded chain is inconsistent, and a partially
    initialized catalog is never repaired here — and leaves every consequential decision to the
    accepted migrator. A database this cannot read is passed through untouched: deciding it is
    unreadable is the migrator's job, not this function's.
    """
    try:
        with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            recorded = applied_versions(connection)
    except sqlite3.Error:
        return  # Not readable as SQLite; the accepted migrator issues the refusal.

    if not recorded:
        return  # An empty or freshly created file is migrated normally.
    expected = tuple(range(1, len(recorded) + 1))
    if tuple(recorded) == expected:
        return  # A contiguous prefix; the migrator applies whatever remains.

    message = (
        f"the existing operational catalog records migration versions {list(recorded)}, which is "
        "not a contiguous chain from 0001; a partially initialized or inconsistent catalog is "
        "refused rather than repaired, because completing it would apply schema over state this "
        "stage cannot account for"
    )
    raise CatalogPreparationError(message)


def _validated_root(evidence_root: Path, repository_root: Path | None) -> Path:
    """Resolve the evidence root, proving it external when a checkout is supplied."""
    if repository_root is not None:
        return require_external_evidence_root(evidence_root, repository_root)
    if not Path(evidence_root).is_absolute():
        message = "the evidence root must be an absolute path outside the repository checkout"
        raise ContainmentError(message)
    return Path(os.path.realpath(evidence_root))


# --------------------------------------------------------------------------- #
# Subphase A.2 — immutable content-addressed storage
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class StorageBinding:
    """The isolated M3.2 data root and the accepted stores bound to it."""

    data_root: Path
    tree: DataTree
    raw_store: RawStore
    snapshot_store: SnapshotStore


def prepare_storage(
    *,
    evidence_root: Path,
    data_root_relative: str | Path,
    repository_root: Path | None = None,
) -> StorageBinding:
    """Prepare the isolated M3.2 data root and bind the accepted stores to it.

    The stores are the accepted implementations, unmodified: :class:`RawStore` already provides
    ``.part`` staging, hash verification before promotion, atomic no-overwrite hard-link
    promotion, byte-identical reuse, differing-body supersession, quarantine that preserves rather
    than deletes, and ``O_CREAT|O_EXCL`` lineage intents. Nothing here re-implements or weakens
    any of that; this binds them to a proved-contained root.

    Raises:
        StoragePreparationError: the data root cannot be created.
        ContainmentError: the data root escapes the evidence root.
    """
    root = _validated_root(evidence_root, repository_root)
    data_root = resolve_within(root, data_root_relative, label="M3.2 data root")
    _refuse_symlinked_ancestors(root, root / data_root_relative, label="M3.2 data root")
    try:
        data_root.mkdir(parents=True, exist_ok=True)
        tree = DataTree.from_root(data_root)
        tree.ensure_tree()
    except OSError as exc:
        message = f"the M3.2 data root could not be prepared: {type(exc).__name__}"
        raise StoragePreparationError(message) from exc

    raw_store = RawStore(tree)
    return StorageBinding(
        data_root=data_root,
        tree=tree,
        raw_store=raw_store,
        snapshot_store=SnapshotStore(tree, raw_store),
    )


# --------------------------------------------------------------------------- #
# Subphase B.1 — the live-authorization boundary
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class LiveOperationAuthorization:
    """The explicit per-window authorization a live run requires.

    This object is **evidence that the operator layer performed the authorization checks**, not a
    grant of its own and not something this module can construct on a caller's behalf. It is
    deliberately inert: it carries no privilege, and every field it names is re-checked against
    the plan and the ceiling at preflight, so a fabricated instance buys nothing.

    The accepted contract §8 gate ladder is enforced by the later operator surface, which alone
    can read a configuration file, evaluate ``--live``, and confirm the per-window instrument.
    What this type provides is the seam that makes that conjunction *enforceable*: the engine
    refuses to reach a transport without one, and no configuration key, contract acceptance, T2
    acceptance, Gate F readiness token, or ceiling value can stand in for it.
    """

    window: str
    plan_sha256: str
    approved_ceiling: int
    authorization_reference: str

    def __post_init__(self) -> None:
        """Refuse an authorization that is not self-consistent."""
        if self.window not in ACQUISITION_WINDOWS:
            message = (
                f"window {self.window!r} is not one of the accepted acquisition windows "
                f"{ACQUISITION_WINDOWS}"
            )
            raise AcquisitionGateError(message)
        if len(self.plan_sha256) != 64 or not all(
            character in "0123456789abcdef" for character in self.plan_sha256
        ):
            message = "the authorized plan hash must be a lowercase hex SHA-256 digest"
            raise AcquisitionGateError(message)
        if self.approved_ceiling < 0:
            message = "the approved ceiling must not be negative"
            raise AcquisitionGateError(message)
        if not self.authorization_reference.strip():
            message = (
                "the authorization must name the owner instrument it records; an unnamed "
                "authorization is refused rather than treated as sufficient"
            )
            raise AcquisitionGateError(message)


# --------------------------------------------------------------------------- #
# Subphase B.2 — logical requests derived from the approved plan
# --------------------------------------------------------------------------- #
def route_is_streamed(spec: SourceSpec) -> bool:
    """Whether this route's payload must be streamed rather than buffered.

    Read from the **registered route specification**, never hardcoded per call site. A route
    registered as an archive is a bulk object: the accepted transport bound
    (``transport.MAX_IN_MEMORY_BYTES``, 64 MiB) exists precisely so such a payload is not pulled
    into memory, and the accepted response policy *quarantines* a buffered body that exceeds it. A
    driver that buffered the bulk submissions archive would therefore quarantine the one object
    contract §14 requires and §15 makes M3.2B depend on — not because anything was wrong with it,
    but because of how it was asked for.

    This is the same rule the accepted Stage M2.2 caller applies
    (``census_orchestrator``: ``stream=spec.expected_content == "zip"``), read from the same
    registry, so the two cannot drift apart.
    """
    return spec.expected_content == "zip"


@dataclass(frozen=True, slots=True)
class LogicalRequest:
    """One planned logical request: a registered route plus its instance parameters."""

    source_id: str
    instance_key: str
    parameters: Mapping[str, str]

    @property
    def identity_label(self) -> str:
        """A stable label for progress output and reconciliation joins."""
        return self.source_id if not self.instance_key else f"{self.source_id}:{self.instance_key}"


def derive_logical_requests(plan: RequestPlan) -> tuple[LogicalRequest, ...]:
    """Expand an approved plan into the exact logical requests it authorizes.

    The expansion is deterministic and total: routes are visited in plan order, and each route's
    instance list is derived from the plan's own recorded content rather than from the clock, the
    catalog, or the network. Nothing is invented — a route whose planned count cannot be matched
    to concrete instances refuses instead of guessing which instances were meant.

    Raises:
        AcquisitionGateError: a route's planned count and its derivable instances disagree, or a
            required index key is malformed.
    """
    requests: list[LogicalRequest] = []
    index_keys = _index_instance_keys(plan)

    for route in plan.routes:
        spec = require_registered(route.source_id)
        planned = route.planned_unique_logical_requests
        if planned == 0:
            continue
        if route.source_id == _INDEX_ROUTE:
            if len(index_keys) != planned:
                message = (
                    f"route {route.source_id!r} plans {planned} logical request(s) but the plan "
                    f"names {len(index_keys)} quarterly instance(s); the run consumes the "
                    "approved plan and never re-derives one"
                )
                raise AcquisitionGateError(message)
            requests.extend(
                LogicalRequest(
                    source_id=route.source_id,
                    instance_key=key,
                    parameters=_index_parameters(key),
                )
                for key in index_keys
            )
            continue
        if route.source_id == _ANNOUNCEMENT_ROUTE:
            # Manifest-resolved: the URL comes from the reviewed evidence manifest, never from a
            # caller. The approved M3.2A plan carries zero entries; a nonzero count therefore
            # needs a manifest this stage is not authorized to read, so it stops.
            message = (
                f"route {route.source_id!r} plans {planned} logical request(s), but a "
                "manifest-resolved announcement URL comes from the reviewed evidence manifest "
                "rather than from this driver; supply the manifest through the operator layer"
            )
            raise AcquisitionGateError(message)
        if planned != 1:
            message = (
                f"singleton route {route.source_id!r} plans {planned} logical requests; a "
                "singleton route addresses exactly one instance"
            )
            raise AcquisitionGateError(message)
        if spec.manifest_resolved:  # pragma: no cover - the announcement route returns above
            message = f"route {route.source_id!r} is manifest-resolved and needs a manifest entry"
            raise AcquisitionGateError(message)
        requests.append(LogicalRequest(source_id=route.source_id, instance_key="", parameters={}))
    _refuse_duplicate_identities(requests)
    return tuple(requests)


def _refuse_duplicate_identities(requests: Sequence[LogicalRequest]) -> None:
    """Refuse an expansion in which two planned requests address the same identity.

    Two requests for one identity retrieve one object, and the object store correctly
    deduplicates them — so both would classify as satisfied while only one required object exists.
    The window would then report every planned request satisfied on a smaller object set than it
    planned for, which is precisely the false success contract §14 forbids.

    Refused **before any transport**, and refused as a domain error rather than a classification:
    a plan that cannot state distinct work is not work this driver may start. No reason code is
    invented for it, because no request has been attempted and nothing is being classified.
    """
    seen: set[str] = set()
    duplicates: list[str] = []
    for request in requests:
        label = request.identity_label
        if label in seen:
            duplicates.append(label)
        seen.add(label)
    if duplicates:
        message = (
            f"the plan expands to repeated logical request identit(ies) {sorted(set(duplicates))}; "
            "two planned requests addressing one identity would retrieve one object and count "
            "twice toward satisfaction, so the expansion is refused before any attempt"
        )
        raise AcquisitionGateError(message)


def _index_instance_keys(plan: RequestPlan) -> tuple[str, ...]:
    """The quarterly instance keys the plan's index route intends to acquire.

    ``required_index_keys`` records every required instance, including those already satisfied
    when the plan was built and reported as ``expected_cache_hits``. The instances still to
    acquire are the required keys minus that many, taken from the front in the planner's own
    chronological order, which is how the planner excluded them.
    """
    required = plan.required_index_keys
    satisfied = plan.expected_cache_hits
    if satisfied < 0 or satisfied > len(required):
        message = (
            f"the plan reports {satisfied} expected cache hit(s) against "
            f"{len(required)} required index instance(s)"
        )
        raise AcquisitionGateError(message)
    remaining = required[satisfied:] if satisfied else required
    for key in remaining:
        if _INSTANCE_KEY_PATTERN.match(key) is None:
            message = f"required index key {key!r} is not a YYYYQTRn instance key"
            raise AcquisitionGateError(message)
    return tuple(remaining)


def _index_parameters(instance_key: str) -> Mapping[str, str]:
    """URL-template parameters for one quarterly index instance."""
    matched = _INSTANCE_KEY_PATTERN.match(instance_key)
    if matched is None:  # pragma: no cover - callers validate first
        message = f"required index key {instance_key!r} is not a YYYYQTRn instance key"
        raise AcquisitionGateError(message)
    return {"year": matched["year"], "quarter": matched["quarter"]}


def _closed_period_flags(plan: RequestPlan) -> Mapping[str, bool]:
    """Whether each planned quarterly instance names a closed period.

    A dated-snapshot identity behaves differently once its period closes: a changed body is
    ordinary while the quarter is open and an anomaly once it has closed. ``SnapshotStore.record``
    fails closed when this is unknown, so the flag is derived from the plan's own coverage inputs
    rather than defaulted.
    """
    window = CoverageWindow(
        coverage_start=plan.coverage_start,
        coverage_end=plan.coverage_end,
        as_of_date=plan.as_of_date,
        include_open_quarter=plan.include_open_quarter,
    )
    return {
        instance.instance_key: instance.is_finalized_period
        for instance in plan_index_instances(window).instances
    }


# --------------------------------------------------------------------------- #
# Subphase B.3 — outcomes
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RequestOutcome:
    """The terminal disposition of one logical request."""

    request: LogicalRequest
    disposition: RequestDisposition
    observation_id: str | None = None
    content_sha256: str | None = None
    relative_storage_path: str | None = None
    stored_size_bytes: int | None = None
    media_type: str | None = None
    http_status: int | None = None
    attempts: int = 0
    reason_codes: tuple[str, ...] = ()
    detail: str = ""

    @property
    def satisfies_requirement(self) -> bool:
        """Whether this outcome satisfies its planned logical request.

        A terminal classification never satisfies a request by itself (contract §14). Only a
        hash-verified, provenance-complete object does — newly stored, reconciled as a
        byte-identical duplicate, or a reuse that independently passed the same verification.
        """
        return self.disposition in {
            "satisfied_new",
            "satisfied_duplicate",
            "satisfied_reused",
        } and bool(self.content_sha256 and self.relative_storage_path)

    @property
    def is_terminal_classification(self) -> bool:
        """Whether the request reached a registered terminal disposition."""
        return self.disposition not in {"not_attempted", "stopped"}


@dataclass(frozen=True, slots=True)
class WindowOutcome:
    """The result of executing one acquisition window."""

    window: str
    plan_sha256: str
    approved_ceiling: int
    consumed_physical_attempts: int
    planned_logical_requests: int
    outcomes: tuple[RequestOutcome, ...]
    completion_status: CompletionStatus
    reason_codes: tuple[str, ...] = ()
    detail: str = ""
    progress_failures: tuple[str, ...] = ()
    """Operator progress-sink failures observed during the run.

    Recorded rather than raised: a failing progress sink is an operator-output problem, and it
    must not be able to discard a window whose objects are promoted and whose rows are committed.
    Populated entries never make a window successful on their own, and never make one unsuccessful
    either — they are reported so the operator can see their own output failed.
    """

    @property
    def satisfied(self) -> tuple[RequestOutcome, ...]:
        """Outcomes that genuinely satisfied their planned request."""
        return tuple(outcome for outcome in self.outcomes if outcome.satisfies_requirement)

    @property
    def absences(self) -> tuple[RequestOutcome, ...]:
        """Planned requests whose required object is absent.

        Item-level absent-object identities live in the operational catalog and in the later
        reconciliation report, never in the frozen receipt (Decision 034 §6 R1). This property is
        the in-memory view the driver exposes to its caller; it is not a receipt field.
        """
        return tuple(
            outcome
            for outcome in self.outcomes
            if not outcome.satisfies_requirement
            and outcome.disposition not in {"not_attempted", "stopped"}
        )

    @property
    def unattempted(self) -> tuple[RequestOutcome, ...]:
        """Planned requests never attempted, because the window stopped first.

        A request that consumed one or more physical attempts before the window stopped is
        ``stopped``, not ``not_attempted``, and is reported by :attr:`interrupted` instead — the
        attempts it consumed are real and are charged against the ceiling.
        """
        return tuple(outcome for outcome in self.outcomes if outcome.disposition == "not_attempted")

    @property
    def interrupted(self) -> tuple[RequestOutcome, ...]:
        """Planned requests that consumed attempts but reached no terminal classification."""
        return tuple(outcome for outcome in self.outcomes if outcome.disposition == "stopped")

    @property
    def new_raw_objects(self) -> int:
        """Count of newly promoted immutable objects (contract §22 ``NEW_RAW_OBJECTS``)."""
        return sum(
            1
            for outcome in self.outcomes
            if outcome.disposition == "satisfied_new" and outcome.satisfies_requirement
        )

    @property
    def duplicates_reconciled(self) -> int:
        """Count of byte-identical bodies reconciled to a preserved object (§22)."""
        return sum(
            1
            for outcome in self.outcomes
            if outcome.disposition == "satisfied_duplicate" and outcome.satisfies_requirement
        )

    @property
    def cache_hits(self) -> int:
        """Count of conditional requests lawfully confirming a preserved snapshot via ``304``.

        **Decision 040 §6 vocabulary ruling:** this quantity is the future receipt's
        ``not_modified_count`` — a request that was physically attempted with accepted validators
        and reconciled against the preserved evidence. It must **not** populate the future
        receipt's ``cache_hit_count``, which counts instances already satisfied and therefore
        never requested (a continuation proposal reports those separately as
        ``already_satisfied_excluded``). :attr:`not_modified_reuses` is the unambiguous name;
        this accepted alias is retained for existing callers.
        """
        return sum(
            1
            for outcome in self.outcomes
            if outcome.disposition == "satisfied_reused" and outcome.satisfies_requirement
        )

    @property
    def not_modified_reuses(self) -> int:
        """Conditional requests physically attempted and lawfully reconciled as ``304`` reuse.

        The future receipt's ``not_modified_count`` (Decision 040 §6), under a name no reader can
        mistake for the not-requested exclusion count the receipt calls ``cache_hit_count``.
        """
        return self.cache_hits

    @property
    def byte_identical_duplicates(self) -> int:
        """Physically retrieved ``200`` responses whose bytes matched preserved evidence.

        The future receipt's ``duplicate_object_count`` (Decision 040 §6), as the
        receipt-vocabulary name for :attr:`duplicates_reconciled`.
        """
        return self.duplicates_reconciled

    @property
    def planned_work_remains(self) -> bool:
        """Whether any planned logical request is still unsatisfied."""
        return len(self.satisfied) < self.planned_logical_requests

    @property
    def completed_successfully(self) -> bool:
        """Whether the window completed successfully under contract §14.

        Every required object present and verified, no absence, nothing left unattempted or
        interrupted, and no attempt beyond the ceiling. Termination alone is deliberately not
        enough, and no other combination of fields can be read as success.
        """
        return (
            self.completion_status == "complete"
            and not self.absences
            and not self.unattempted
            and not self.interrupted
            and len(self.satisfied) == self.planned_logical_requests
            and self.consumed_physical_attempts <= self.approved_ceiling
        )

    @property
    def classification_totals(self) -> Mapping[str, int]:
        """Per-disposition totals. Sums exactly to the planned logical request count."""
        totals: dict[str, int] = {
            "satisfied_new": 0,
            "satisfied_duplicate": 0,
            "satisfied_reused": 0,
            "absent": 0,
            "quarantined": 0,
            "failed": 0,
            "stopped": 0,
            "not_attempted": 0,
        }
        for outcome in self.outcomes:
            totals[outcome.disposition] += 1
        return totals


# --------------------------------------------------------------------------- #
# Subphase B.4 — the engine
# --------------------------------------------------------------------------- #
def _utc_now() -> str:
    """The governed clock's default: an explicit UTC instant in Z form."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class AcquisitionEngine:
    """Executes one acquisition window over an injected transport.

    Every collaborator is supplied explicitly. The engine constructs no transport, no client
    credential, and no ceiling of its own, and it reads no configuration file: a caller that
    cannot supply an authorized plan, the exact approved ceiling, an authenticated client, and an
    explicit :class:`LiveOperationAuthorization` simply cannot run it.

    Args:
        plan: The approved request plan, already parsed from its stored document.
        window: The window this run executes. Must match the plan's own window.
        ceiling: The shared cumulative physical-attempt gate, constructed by the caller with the
            exact approved integer. The engine never raises or replaces it.
        client: The accepted response-policy client, constructed by the caller over an injected
            transport and carrying ``ceiling`` so every wire attempt is counted.
        storage: The prepared data root and its accepted stores.
        recorder: The accepted observation recorder, bound to an open catalog writer.
        clock: Returns the UTC instant recorded on observations. Injected so a run is
            deterministic under test.
        progress: Optional per-request callback for operator output.
    """

    plan: RequestPlan
    window: str
    ceiling: PhysicalAttemptCeiling
    client: SecClient
    storage: StorageBinding
    recorder: ObservationRecorder
    clock: Callable[[], str] = _utc_now
    progress: Callable[[RequestOutcome], None] | None = None
    progress_failures: tuple[str, ...] = field(default=(), init=False)
    _authorization: LiveOperationAuthorization | None = field(default=None, init=False)
    _requests: tuple[LogicalRequest, ...] = field(default=(), init=False)

    # -- preflight ---------------------------------------------------------- #
    def preflight(self, authorization: LiveOperationAuthorization) -> tuple[LogicalRequest, ...]:
        """Validate every binding, and return the logical requests this window will place.

        Runs **before the first transport call** and refuses rather than continuing. The checks,
        in order: the authorization's window; the plan's own window; the plan hash; the ceiling
        equality; the ceiling's remaining headroom; every route's registration; and every route's
        constructed URL against the filing-body prohibition.

        Passing preflight authorizes nothing on its own — it records that the bindings this
        engine was given are mutually consistent. The operator layer remains responsible for the
        complete live-authorization conjunction.

        Raises:
            AcquisitionGateError: any binding does not match.
        """
        if authorization.window != self.window:
            message = (
                f"the authorization names window {authorization.window!r} but this run executes "
                f"{self.window!r}"
            )
            raise AcquisitionGateError(message)
        if self.window not in ACQUISITION_WINDOWS:
            message = f"window {self.window!r} is not an accepted acquisition window"
            raise AcquisitionGateError(message)
        if self.plan.acquisition_window != self.window:
            message = (
                f"the approved plan is for window {self.plan.acquisition_window!r}, not "
                f"{self.window!r}; a plan is never executed against another window"
            )
            raise AcquisitionGateError(message)

        actual_hash = self.plan.request_plan_sha256
        if actual_hash != authorization.plan_sha256:
            message = (
                "the approved plan hash does not match the authorization; the run consumes "
                "exactly the plan the owner approved"
            )
            raise AcquisitionGateError(message)
        if self.ceiling.approved_ceiling != authorization.approved_ceiling:
            message = (
                f"the supplied ceiling gate is set to {self.ceiling.approved_ceiling}, but the "
                f"authorization approves {authorization.approved_ceiling}; the ceiling must equal "
                "the approved integer exactly"
            )
            raise AcquisitionGateError(message)
        if self.plan.hard_request_ceiling != authorization.approved_ceiling:
            message = (
                f"the approved plan derives a ceiling of {self.plan.hard_request_ceiling}, but "
                f"the authorization approves {authorization.approved_ceiling}"
            )
            raise AcquisitionGateError(message)

        requests = derive_logical_requests(self.plan)
        if len(requests) != self.plan.planned_unique_logical_requests:
            message = (
                f"the plan totals {self.plan.planned_unique_logical_requests} logical requests "
                f"but expands to {len(requests)}"
            )
            raise AcquisitionGateError(message)
        self._verify_routes(requests)

        self._authorization = authorization
        self._requests = requests
        return requests

    def _verify_routes(self, requests: Sequence[LogicalRequest]) -> None:
        """Prove every planned route is registered, in-window, and not a filing body.

        Window membership is enforced in **both** directions. Contract §17 stop condition 5 names
        "a dependent request in M3.2A **or a bootstrap request in M3.2B**", so each window admits
        only its own families and nothing else — an allowlist of every registered source would
        enforce one half of that rule and silently permit the other.
        """
        allowed = (
            frozenset(M3_2A_BOOTSTRAP_ROUTES)
            if self.window == "M3.2A"
            else frozenset(M3_2B_DEPENDENT_ROUTES)
        )
        for request in requests:
            spec = require_registered(request.source_id)
            if request.source_id not in allowed:
                message = (
                    f"route {request.source_id!r} is not a {self.window} route; a dependent "
                    "request in the bootstrap window, or a bootstrap request in the dependent "
                    "window, is a stop condition"
                )
                raise AcquisitionGateError(message)
            url = spec.url(**dict(request.parameters))
            if filing_body_url_is_prohibited(url):
                message = (
                    f"route {request.source_id!r} constructs a filing-body or accession URL; "
                    "Milestone 3.2 acquires metadata only"
                )
                raise AcquisitionGateError(message)

    # -- execution ---------------------------------------------------------- #
    def run(self) -> WindowOutcome:
        """Execute the window and return its outcome.

        The loop stops before, never after, the attempt that would exceed the ceiling: headroom
        is checked before each logical request, and the shared gate additionally refuses inside
        the client so a retry, a redirect hop, or a controlled post-cooldown request cannot slip
        past. Requests not reached are recorded as ``not_attempted`` rather than omitted, so the
        classification totals always sum to the planned count.

        Raises:
            AcquisitionGateError: :meth:`preflight` has not run.
        """
        if self._authorization is None:
            message = (
                "preflight has not run; the engine refuses to reach a transport before its "
                "bindings and its explicit live authorization are validated"
            )
            raise AcquisitionGateError(message)

        closed_periods = _closed_period_flags(self.plan)
        outcomes: list[RequestOutcome] = []
        stopped: CompletionStatus | None = None
        stop_reasons: tuple[str, ...] = ()
        stop_detail = ""

        for index, request in enumerate(self._requests):
            if stopped is not None:
                outcomes.append(RequestOutcome(request=request, disposition="not_attempted"))
                continue
            if self.ceiling.is_exhausted:
                stopped = "stopped_at_ceiling"
                stop_reasons = ("SEC_REQUEST_CEILING_EXHAUSTED",)
                stop_detail = (
                    f"the approved ceiling {self.ceiling.approved_ceiling} was consumed with "
                    f"{len(self._requests) - index} planned logical request(s) remaining"
                )
                outcomes.append(RequestOutcome(request=request, disposition="not_attempted"))
                continue

            before = self.ceiling.consumed
            try:
                outcome = self._execute(request, closed_periods)
            except RequestCeilingExhaustedError as exc:
                # The ceiling refused an attempt *inside* this request — during a retry, a redirect
                # hop, or the controlled post-cooldown request. Attempts already consumed for it
                # are real, so it is `stopped`, never `not_attempted`.
                stopped = "stopped_at_ceiling"
                stop_reasons = (exc.reason_code,)
                stop_detail = str(exc)
                outcomes.append(
                    RequestOutcome(
                        request=request,
                        disposition="stopped",
                        attempts=self.ceiling.consumed - before,
                        reason_codes=(exc.reason_code,),
                        detail=str(exc),
                    )
                )
                continue
            except ProhibitedRetrievalError as exc:
                # A pre-transport policy refusal from the accepted client: an unregistered source,
                # a missing purpose, a filing-body URL, or a URL outside the registered family.
                # Preflight already proved none of those, so reaching here is an internal
                # inconsistency and the window stops. It carries no reason code: nothing was
                # placed and nothing is being classified, and the one registered code that might
                # look apt — SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY — is defined as a redirect hop
                # or final URL leaving the family, which this is not.
                stopped = "stopped_by_gate"
                stop_reasons = ()
                stop_detail = str(exc)
                outcomes.append(
                    RequestOutcome(
                        request=request,
                        disposition="stopped",
                        attempts=self.ceiling.consumed - before,
                        detail=str(exc),
                    )
                )
                continue
            except _OPERATIONAL_FAILURES as exc:
                # A storage, catalog, path-policy, or integrity failure after the request was
                # placed. Discarding the window here would throw away the classification of every
                # request already committed, along with the attempt accounting a later resume
                # needs, so the window terminates with a recorded outcome instead of an exception.
                # Nothing is repaired, retried, adopted, or deleted: the failure is reported and
                # the run stops. The detail names the failure class and a public description
                # only — never the exception's own arguments, which routinely carry an absolute
                # private path.
                stopped = "failed"
                stop_reasons = ()
                stop_detail = _operational_detail(exc)
                outcomes.append(
                    RequestOutcome(
                        request=request,
                        disposition="failed",
                        attempts=self.ceiling.consumed - before,
                        detail=stop_detail,
                    )
                )
                continue

            outcomes.append(outcome)
            self._report(outcome)

        return self._finalize(tuple(outcomes), stopped, stop_reasons, stop_detail)

    def _report(self, outcome: RequestOutcome) -> None:
        """Hand one outcome to the optional progress callback, defensively.

        The callback is operator output: observational, and never part of the acquisition result.
        A failing progress sink must not be able to discard a window whose objects are already
        promoted and whose rows are already committed, so its failure is contained here and
        recorded as an observable rather than propagated.
        """
        if self.progress is None:
            return
        try:
            self.progress(outcome)
        except Exception as exc:  # noqa: BLE001 - an operator sink may fail any way it likes
            # A sink that fails on a file or database carries the same private arguments the
            # run loop refuses to publish, so those classes get the public description. A sink
            # that raises deliberately keeps its own message: that message is the operator's
            # own text and is the only thing that makes their output failure diagnosable.
            detail = (
                _operational_detail(exc)
                if isinstance(exc, _OPERATIONAL_FAILURES)
                else f"{type(exc).__name__}: {exc}"
            )
            self.progress_failures = (
                *self.progress_failures,
                f"{outcome.request.identity_label}: {detail}",
            )

    def _execute(
        self,
        request: LogicalRequest,
        closed_periods: Mapping[str, bool],
    ) -> RequestOutcome:
        """Place one logical request, store its object, and record its observation.

        Streaming is chosen from the registered route specification, never fixed for every route:
        a bulk archive is streamed to its ``.part`` spool and promoted from there, while a bounded
        metadata document is buffered as before. See :func:`route_is_streamed`.
        """
        spec = require_registered(request.source_id)
        period_is_closed = (
            closed_periods.get(request.instance_key) if request.instance_key else None
        )
        with self.client.fetch(
            request.source_id,
            purpose=_ACQUISITION_PURPOSE,
            parameters=dict(request.parameters) or None,
            stream=route_is_streamed(spec),
        ) as result:
            observation = self.storage.snapshot_store.record(
                result,
                retrieved_at_utc=self.clock(),
                period_is_closed=period_is_closed,
            )
        observation = self._record_observation(spec, request, observation)
        return self._classify(request, observation)

    def _record_observation(
        self,
        spec: SourceSpec,
        request: LogicalRequest,
        observation: SourceObservation,
    ) -> SourceObservation:
        """Commit one observation, streaming archive lineage when the route owns one.

        The acquired object is the **archive itself**; members are lineage recorded beside it, not
        separately authorized retrievals. Three cases:

        * a newly promoted archive (``stored_new`` / ``superseded``) is opened through the accepted
          archive reader and its validated members are **streamed** into the observation's
          transaction;
        * a reused archive (``unchanged_content`` / ``reused_snapshot``) passes no explicit members
          — the accepted recorder resolves the owning observation's preserved lineage and verifies
          it identifies the same object, which is the reconciliation this stage owes;
        * every other outcome has no object to enumerate.

        Streaming is what makes the whole path bounded, and it moves the archive verdict from
        *before* the write to *during* it. A corrupt archive, a refused member, or an archive
        carrying none of the members it was retrieved for now surfaces mid-transaction, so the
        observation and any rows already written roll back together and the retrieval is recorded
        once, as ``quarantined``, with the accepted registered reason. The catalog therefore never
        sees a partial archive: it sees the whole lineage or none of it. The promoted object stays
        preserved on disk either way — nothing is deleted, repaired, or retried, and no member
        payload is written anywhere.
        """
        prepared = self._with_absence_reason(request, observation)
        if not route_is_streamed(spec) or observation.outcome not in {"stored_new", "superseded"}:
            self.recorder.record(prepared)
            return prepared

        try:
            self.recorder.record(prepared, members=self._archive_members(spec, observation))
        except ArchiveDefenceError as exc:
            quarantined = self._with_absence_reason(
                request,
                replace(
                    observation,
                    outcome="quarantined",
                    reason_codes=(exc.reason_code,),
                    detail=str(exc),
                ),
            )
            self.recorder.record(quarantined)
            return quarantined
        return prepared

    def _archive_members(
        self,
        spec: SourceSpec,
        observation: SourceObservation,
    ) -> Iterator[ArchiveMember]:
        """Yield the archive's validated members once, holding at most one at a time.

        A single pass over the accepted reader, with nothing accumulated. The reader is not
        re-entered, no member is retained after it is yielded, and the archive is read from the
        stored immutable object rather than from anything held in memory — which is what keeps the
        cost of recording lineage proportional to the largest single member instead of to the whole
        expanded archive. Every accepted archive protection still applies, unchanged and at its
        registered limits.

        An archive carrying no accepted member is refused **here**, at the end of the one pass,
        rather than by inspecting a materialized collection: emptiness is only knowable once the
        reader is exhausted, and raising the accepted defence error is what lets the caller record
        the retrieval as quarantined instead of committing an archive with no lineage.
        """
        seen = 0
        for member in iter_members(
            self.storage.snapshot_store.payload_path(observation),
            name_suffix=_ARCHIVE_MEMBER_SUFFIX,
            archive_relative_path=observation.relative_storage_path,
            archive_sha256=observation.logical_sha256,
        ):
            seen += 1
            yield member
        if seen == 0:
            message = (
                f"the {spec.source_id} archive carried no {_ARCHIVE_MEMBER_SUFFIX} members, so it "
                "cannot stand as the bootstrap metadata object it was retrieved to be"
            )
            raise ArchiveDefenceError(message, "RAW_ARCHIVE_INVALID")

    def _with_absence_reason(
        self,
        request: LogicalRequest,
        observation: SourceObservation,
    ) -> SourceObservation:
        """Attach the registered absence reason when a required object is left absent.

        The accepted response policy classifies a ``404`` on an archival path as absent evidence
        and deliberately attaches no reason code, because at that layer it is an ordinary outcome.
        At *this* layer it is a required object left absent, and the operational catalog is the
        durable home of that fact (T2 packet §10 item 1; Decision 040 §5). So the registered code
        is attached to the observation before it is committed, rather than only to the in-memory
        outcome — a reconciliation report read from the catalog alone must be able to see it.

        Two registered codes, split exactly as Decision 040 §4 fixes. A quarterly index instance
        keeps ``INDEX_INSTANCE_UNAVAILABLE`` in every window, unchanged. Every other required
        M3.2A request whose committed observation is terminally ``failed`` or ``quarantined``
        additionally carries ``SOURCE_REQUIRED_OBJECT_UNAVAILABLE`` beside — never instead of —
        any more specific defect code the policy already attached. The new mapping is bounded to
        the M3.2A window; Decision 040 authorizes no M3.2B mapping.
        """
        if observation.outcome not in {"failed", "quarantined"}:
            return observation
        if request.source_id == _INDEX_ROUTE:
            if _INDEX_ABSENT_REASON in observation.reason_codes:
                return observation
            return replace(
                observation,
                reason_codes=(*observation.reason_codes, _INDEX_ABSENT_REASON),
            )
        if self.window != "M3.2A":
            return observation
        if _REQUIRED_OBJECT_ABSENT_REASON in observation.reason_codes:
            return observation
        return replace(
            observation,
            reason_codes=(*observation.reason_codes, _REQUIRED_OBJECT_ABSENT_REASON),
        )

    def _classify(
        self,
        request: LogicalRequest,
        observation: SourceObservation,
    ) -> RequestOutcome:
        """Map one recorded observation to its terminal disposition.

        Verification is re-run rather than inferred: an observation that claims a payload is
        treated as satisfying its request only when the stored bytes still hash to the recorded
        ``content_sha256``. That is what keeps "terminally classified" and "satisfied" different
        facts rather than the same one under two names.
        """
        disposition: RequestDisposition
        if observation.outcome == "quarantined":
            disposition = "quarantined"
        elif observation.outcome == "failed":
            disposition = "absent" if observation.http_status == 404 else "failed"
        elif observation.outcome == "reused_snapshot":
            disposition = "satisfied_reused"
        elif observation.outcome == "unchanged_content":
            disposition = "satisfied_duplicate"
        else:
            disposition = "satisfied_new"

        if disposition in {
            "satisfied_new",
            "satisfied_duplicate",
            "satisfied_reused",
        } and not self._verified(observation):
            disposition = "failed"

        return RequestOutcome(
            request=request,
            disposition=disposition,
            observation_id=observation.observation_id,
            content_sha256=observation.content_sha256,
            relative_storage_path=observation.relative_storage_path,
            stored_size_bytes=observation.stored_size_bytes,
            media_type=observation.declared_content_type,
            http_status=observation.http_status,
            attempts=observation.attempts,
            reason_codes=observation.reason_codes,
            detail=observation.detail,
        )

    def _verified(self, observation: SourceObservation) -> bool:
        """Whether the observation's stored object exists and still hashes as recorded."""
        if not observation.relative_storage_path or not observation.content_sha256:
            return False
        try:
            self.storage.snapshot_store.verify_payload(observation)
        except DisclosureDriftError:
            return False
        except OSError:
            return False
        return True

    def _finalize(
        self,
        outcomes: tuple[RequestOutcome, ...],
        stopped: CompletionStatus | None,
        stop_reasons: tuple[str, ...],
        stop_detail: str,
    ) -> WindowOutcome:
        """Assemble the window outcome under the accepted completion semantics."""
        assert self._authorization is not None  # noqa: S101 - run() proves this first
        planned = len(self._requests)
        satisfied = sum(1 for outcome in outcomes if outcome.satisfies_requirement)

        if stopped is not None:
            status: CompletionStatus = stopped
            reasons = stop_reasons
            detail = stop_detail
        elif satisfied == planned:
            status = "complete"
            reasons = ()
            detail = "every planned logical request is satisfied by a verified object"
        else:
            status = "incomplete"
            reasons = ()
            detail = (
                f"{planned - satisfied} of {planned} planned logical request(s) left their "
                "required object absent; the window is not successfully complete and is not "
                "eligible for the freeze, dependent planning, or Gate H"
            )

        return WindowOutcome(
            window=self.window,
            plan_sha256=self._authorization.plan_sha256,
            approved_ceiling=self.ceiling.approved_ceiling,
            consumed_physical_attempts=self.ceiling.consumed,
            planned_logical_requests=planned,
            outcomes=outcomes,
            completion_status=status,
            reason_codes=reasons,
            detail=detail,
            progress_failures=self.progress_failures,
        )


# --------------------------------------------------------------------------- #
# Foundational recovery observability (inspection only; repair is stage T2.4)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RecoveryObservation:
    """What a read-only sweep of the data root and catalog can see.

    Deliberately observational. Nothing here resumes, retries, repairs, deletes, adopts, or
    resets a counter: the deterministic repair applier, the reconciliation report, drift
    inspection, and the resume boundary are stage T2.4.
    """

    partial_objects: tuple[str, ...]
    orphan_objects: tuple[str, ...]
    missing_referents: tuple[str, ...]
    consumed_physical_attempts: int
    approved_ceiling: int

    @property
    def is_clean(self) -> bool:
        """Whether nothing needs a later recovery decision."""
        return not (self.partial_objects or self.orphan_objects or self.missing_referents)

    @property
    def outcome_is_uncertain(self) -> bool:
        """Whether a transaction's durable outcome cannot be determined from what is visible.

        A catalog row whose object is missing is the uncertain case the accepted semantics treat
        as ``UNDETERMINED``: it cannot be told apart from a committed row whose object was never
        promoted. A caller that sees this must refer to the owner rather than resume (contract
        §12); this property states the fact and takes no action on it.
        """
        return bool(self.missing_referents)

    @property
    def remaining_headroom(self) -> int:
        """Ceiling headroom left, for a later resume decision that this does not make."""
        return max(0, self.approved_ceiling - self.consumed_physical_attempts)


def observe_recovery_state(
    *,
    storage: StorageBinding,
    observations: Sequence[SourceObservation],
    ceiling: PhysicalAttemptCeiling,
) -> RecoveryObservation:
    """Report what a read-only sweep can see, without changing anything.

    Args:
        storage: The prepared data root and its stores.
        observations: Committed catalog observations for this run.
        ceiling: The window's attempt gate, read for its cumulative state only.
    """
    recorded = {
        observation.relative_storage_path
        for observation in observations
        if observation.relative_storage_path
    }
    partial: list[str] = []
    orphans: list[str] = []
    tree = storage.tree
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.name.endswith((".reason", LINEAGE_SUFFIX)):
                continue
            relative = tree.relative(path)
            if path.name.endswith(".part"):
                partial.append(relative)
            elif relative not in recorded:
                orphans.append(relative)

    # A streamed body is spooled to `staging/sec` before it is ever promoted, so an interruption
    # mid-transfer leaves its `.part` there and nowhere else. Scanning only the raw subtrees would
    # report such a run as clean — which is exactly the state a later recovery decision must not
    # be allowed to miss. An orphan is not derivable here: a spool is by definition unpromoted and
    # has no catalog row to be missing from.
    partial.extend(_staging_partials(tree))

    missing = [
        relative for relative in sorted(recorded) if not (tree.data_root / relative).is_file()
    ]
    return RecoveryObservation(
        partial_objects=tuple(sorted(partial)),
        orphan_objects=tuple(orphans),
        missing_referents=tuple(missing),
        consumed_physical_attempts=ceiling.consumed,
        approved_ceiling=ceiling.approved_ceiling,
    )


def _staging_partials(tree: DataTree) -> list[str]:
    """Relative paths of streamed ``.part`` spools left in the staging tree.

    Read-only, and deliberately link-averse: a symlinked component is skipped rather than followed,
    because inspection must not be a way to reach outside the data root. Nothing here mutates,
    adopts, quarantines, or deletes a spool — that is the T2.4 repair applier's decision to make.
    """
    staging = tree.staging
    if not staging.is_dir() or staging.is_symlink():
        return []
    found: list[str] = []
    for path in sorted(staging.rglob("*")):
        if path.is_symlink() or not path.is_file() or not path.name.endswith(".part"):
            continue
        found.append(tree.relative(path))
    return found


def load_approved_plan(payload: bytes) -> RequestPlan:
    """Read an approved plan document, proving it canonical.

    A thin, deliberate re-export of the accepted reader: the driver consumes the stored plan the
    owner approved and never rebuilds one from inputs, so this is the only way a plan enters an
    acquisition run.
    """
    return request_plan_from_document(payload)


# =========================================================================== #
# Stage T2.4 — recovery, reconciliation, resume boundaries, and drift control
# (Decision 040 §§2–7. Everything below is read-only except the explicit
#  recovery-action applier, which mutates only when invoked with one action.)
# =========================================================================== #

#: The four deterministic recovery-action classes Decision 040 §2 (T2.4-D) authorizes. A request
#: naming anything else — including a would-be combined or list-valued action — is refused,
#: never coerced, and never partially applied.
RECOVERY_ACTIONS: Final[tuple[str, ...]] = (
    "adopt-orphan",
    "quarantine-partial",
    "rebuild-projection",
    "remove-stale-part",
)

#: The derived audit projection the rebuild action reconstructs — the accepted filename the
#: recorder, the read-only inspector, and ``observation_catalog.reconcile`` all share.
_PROJECTION_NAME: Final = "census_source_observations.jsonl"

#: Registered reason codes whose presence on a committed observation is a schema-drift event for
#: the deterministic drift listing (Decision 040 §2, T2.4-B). Whether an event blocks is read
#: from the registry's own ``blocks_release`` metadata, never re-declared here: a retained
#: unknown-field record and an ordinary living-source update are nonblocking, and every
#: immutable-identity mutation, validator contradiction, malformed payload, and invalid archive
#: blocks.
_DRIFT_REASON_CODES: Final[tuple[str, ...]] = (
    "PARSER_SCHEMA_DRIFT_OBSERVED",
    "RAW_ARCHIVE_INVALID",
    "RAW_ARCHIVE_MEMBER_REFUSED",
    "SEC_RESPONSE_MALFORMED",
    "SOURCE_CONTENT_UPDATED",
    "SOURCE_DATED_ARTIFACT_CHANGED",
    "SOURCE_IMMUTABLE_IDENTITY_MUTATED",
    "SOURCE_VALIDATOR_CONTRADICTION",
)

#: The exhaustive continuation-state partition. Every item state ``reconcile_requests`` emits
#: belongs to **exactly one** of the four sets below, and their union is the complete
#: emitted-state vocabulary — enforced fail-closed at emission, so a new state can never fall
#: through the partition silently. Continuation treatment is decided from this one mechanism:
#:
#: * **satisfying** — verified satisfying evidence; excluded from replay, never re-requested;
#: * **retryable** — genuinely retryable open work under the accepted Decision 040 semantics
#:   (failed, quarantined, stopped, absent, not attempted); included exactly once in the
#:   continuation remainder, because the work is still owed and is re-acquired under its own
#:   accounting, never reclassified in place;
#: * **blocking** — a defect that explicitly refuses continuation; never counted satisfied, and
#:   omitted from the transport remainder only because the whole proposal is refused;
#: * **uncertain** — durable persistence or attribution cannot be established; the proposal is
#:   ``UNDETERMINED`` and continuation is prohibited.
_SATISFYING_ITEM_STATES: Final[frozenset[str]] = frozenset(
    {
        "satisfied_duplicate",
        "satisfied_new",
        "satisfied_not_modified",
        "satisfied_superseding",
    }
)
_RETRYABLE_ITEM_STATES: Final[frozenset[str]] = frozenset(
    {"absent", "failed", "not_attempted", "quarantined", "stopped"}
)
_BLOCKING_ITEM_STATES: Final[frozenset[str]] = frozenset(
    {"archive_lineage_missing_or_invalid", "hash_mismatch"}
)
_UNCERTAIN_ITEM_STATES: Final[frozenset[str]] = frozenset({"row_without_object"})
_ITEM_STATE_VOCABULARY: Final[frozenset[str]] = (
    _SATISFYING_ITEM_STATES
    | _RETRYABLE_ITEM_STATES
    | _BLOCKING_ITEM_STATES
    | _UNCERTAIN_ITEM_STATES
)

#: Item conditions that escalate a retryable item to blocking treatment. A failed, quarantined,
#: or absent item carrying one of these has residual evidence that cannot be lawfully retried
#: without adjudication: its evidence is unusable or unverifiable, or its absence carries no
#: registered terminal reason and is an adjudication defect rather than ordinary open work.
_BLOCKING_ITEM_CONDITIONS: Final[frozenset[str]] = frozenset(
    {"absence_without_terminal_reason", "unverifiable_evidence"}
)

#: The generic write-ahead state scenario Decision 041 §6 fixes for the T2.4 applier. Stored
#: only in ``census_recovery_states``, whose schema does not constrain scenario vocabulary; it
#: must never be inserted into ``census_recovery_events``, whose scenario set is separately
#: CHECK-constrained.
_T2_4_STATE_SCENARIO: Final = "t2_4_recovery_action"

#: A staging spool's nonce, exactly as the accepted snapshot store names it:
#: ``{registered source_id}-{uuid4 hex}.part``. Registered source identifiers contain no ``-``,
#: so the rightmost ``-`` splits the route prefix from the nonce exactly.
_SPOOL_NONCE: Final = re.compile(r"^[0-9a-f]{32}$")


class RepairRefusedError(AcquisitionError):
    """Raised when the explicit recovery applier refuses a requested action.

    Refusal is the applier's default posture: an unknown or multi-action request, an action that
    differs from the deterministic recommendation, a stale or already-resolved target, any
    ``UNDETERMINED`` state, and any request whose one authorized primitive cannot be scoped to
    exactly the named target without unrelated mutation are all refused before anything mutates.
    """


# --------------------------------------------------------------------------- #
# T2.4-A — catalog-authoritative reconstruction
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CatalogReconstruction:
    """Catalog-authoritative state, rebuilt fresh at one continuation boundary.

    Decision 040 §2 (T2.4-A): the operational catalog is the durable source of truth. This is
    the composition that opens it read-only, loads every durable observation in the catalog's
    own deterministic order, and adopts them into a **fresh** :class:`SnapshotStore`. An earlier
    process's mutable in-memory snapshot state is discarded by construction — this composition
    simply does not accept one, so nothing can inherit it. Quarantined, failed, and otherwise
    unusable observations are adopted as *facts* (reconciliation must see them) but are never
    selectable for reuse: selection flows through the accepted ``latest_for`` usability rules,
    and :func:`verified_reusable_predecessor` re-verifies immutable evidence at the point of
    reuse.
    """

    observations: tuple[SourceObservation, ...]
    store: SnapshotStore
    archive_member_counts: Mapping[str, int]
    archive_lineage_mismatches: Mapping[str, int]
    blocked_recovery_states: int
    blocked_t2_4_recovery_states: int
    """Blocked write-ahead states carrying the exact T2.4 scenario.

    A subset of :attr:`blocked_recovery_states`. Kept separately because an unresolved
    ``t2_4_recovery_action`` block means a T2.4 recovery mutation may have begun without its
    completed event and exact resolution — persistence-uncertain state that a continuation
    proposal must classify ``UNDETERMINED``, not merely unsafe.
    """

    def latest_any(self, source_id: str, identity: str) -> SourceObservation | None:
        """The newest observation for one request identity, usable or not."""
        for observation in reversed(self.observations):
            if observation.source_id == source_id and observation.identity == identity:
                return observation
        return None

    def by_id(self, observation_id: str) -> SourceObservation | None:
        """The observation carrying ``observation_id``, or ``None``."""
        for observation in self.observations:
            if observation.observation_id == observation_id:
                return observation
        return None


def reconstruct_catalog_state(
    *,
    catalog_path: Path,
    storage: StorageBinding,
) -> CatalogReconstruction:
    """Rebuild lawful in-memory state from the durable catalog, writing nothing.

    The connection is the read-only inspector's own (``PRAGMA query_only``), so a write is
    impossible rather than merely unintended. Archive-member lineage is summarized per owning
    observation as bounded aggregates — a count and a mismatch count against the owner's own
    recorded archive identity — never materialized row by row, so a bulk archive's lineage
    cannot pull the whole expansion into memory.

    Raises:
        AcquisitionGateError: the catalog does not exist; reconstruction refuses to invent one.
    """
    if not Path(catalog_path).is_file():
        message = (
            "the operational catalog does not exist; catalog-authoritative reconstruction "
            "refuses to begin from anything but the durable catalog"
        )
        raise AcquisitionGateError(message)

    with read_only_catalog(Path(catalog_path)) as connection:
        observations = load_observations(connection)
        member_counts: dict[str, int] = {}
        for row in connection.execute(
            "SELECT observation_id, COUNT(*) AS members FROM census_archive_members "
            "GROUP BY observation_id ORDER BY observation_id"
        ).fetchall():
            member_counts[str(row["observation_id"])] = int(row["members"])
        mismatches: dict[str, int] = {}
        for observation in observations:
            if member_counts.get(observation.observation_id, 0) == 0:
                continue
            mismatch_row = connection.execute(
                "SELECT COUNT(*) AS mismatched FROM census_archive_members "
                "WHERE observation_id = ? AND (archive_relative_path IS NOT ? "
                "OR archive_sha256 IS NOT ?)",
                (
                    observation.observation_id,
                    observation.relative_storage_path,
                    observation.logical_sha256,
                ),
            ).fetchone()
            mismatched = int(mismatch_row["mismatched"])
            if mismatched:
                mismatches[observation.observation_id] = mismatched
        blocked = int(
            connection.execute(
                "SELECT COUNT(*) FROM census_recovery_states WHERE resolution_state = 'blocked'"
            ).fetchone()[0]
        )
        blocked_t2_4 = int(
            connection.execute(
                "SELECT COUNT(*) FROM census_recovery_states "
                "WHERE resolution_state = 'blocked' AND scenario = ?",
                (_T2_4_STATE_SCENARIO,),
            ).fetchone()[0]
        )

    store = SnapshotStore(storage.tree, storage.raw_store)
    store.adopt(observations)
    return CatalogReconstruction(
        observations=observations,
        store=store,
        archive_member_counts=member_counts,
        archive_lineage_mismatches=mismatches,
        blocked_recovery_states=blocked,
        blocked_t2_4_recovery_states=blocked_t2_4,
    )


def verified_reusable_predecessor(
    reconstruction: CatalogReconstruction,
    source_id: str,
    identity: str | None = None,
) -> SnapshotIndex | None:
    """The latest usable predecessor for one identity, re-verified now — or ``None``.

    Lawful reuse demands more than a row (Decision 040 §2, T2.4-A/C): the latest usable
    observation must resolve through the accepted evidence-owner chain, the owning object must
    still hash exactly as recorded, and an archive owner must carry complete, consistent member
    lineage. Anything less returns ``None`` — a quarantined, failed, missing, tampered, or
    lineage-less predecessor is simply not reusable, and the distinction is reported by the
    reconciliation rather than leaked here as an exception.
    """
    index = reconstruction.store.latest_for(source_id, identity)
    if not index.has_snapshot or index.evidence_observation_id is None:
        return None
    owner = reconstruction.by_id(index.evidence_observation_id)
    if owner is None:
        return None
    try:
        reconstruction.store.verify_payload(owner)
    except (DisclosureDriftError, OSError):
        return None
    spec = require_registered(source_id)
    if spec.expected_content == "zip":
        if reconstruction.archive_member_counts.get(owner.observation_id, 0) == 0:
            return None
        if reconstruction.archive_lineage_mismatches.get(owner.observation_id, 0):
            return None
    return index


def conditional_validators(
    reconstruction: CatalogReconstruction,
    source_id: str,
    identity: str | None = None,
) -> tuple[str | None, str | None] | None:
    """``(etag, last_modified)`` drawn from a lawful verified predecessor, else ``None``.

    Decision 040 §2 (T2.4-C): validators are supplied **only** from a predecessor that verifies
    at the point of reuse — never from an unverified, quarantined, superseded-away, or
    lineage-less row. A predecessor carrying neither validator yields ``None`` rather than an
    empty pair, because a conditional request with nothing to condition on is not one.
    """
    index = verified_reusable_predecessor(reconstruction, source_id, identity)
    if index is None:
        return None
    if index.etag is None and index.last_modified is None:
        return None
    return (index.etag, index.last_modified)


# --------------------------------------------------------------------------- #
# T2.4-B — deterministic reconciliation and drift inspection (read-only)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ReconciliationItem:
    """One planned logical request's durable, catalog-derived state."""

    position: int
    source_id: str
    identity_label: str
    request_identity: str
    state: str
    observation_id: str | None
    verified: bool
    excluded_from_continuation: bool
    attempts: int
    reason_codes: tuple[str, ...]
    conditions: tuple[str, ...]

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for serialization and comparison."""
        return {
            "attempts": self.attempts,
            "conditions": list(self.conditions),
            "excluded_from_continuation": self.excluded_from_continuation,
            "identity_label": self.identity_label,
            "observation_id": self.observation_id,
            "position": self.position,
            "reason_codes": list(self.reason_codes),
            "request_identity": self.request_identity,
            "source_id": self.source_id,
            "state": self.state,
            "verified": self.verified,
        }


def _classify_item(item: ReconciliationItem) -> str:
    """Assign one reconciliation item to exactly one continuation-treatment category.

    Total and fail-closed over :data:`_ITEM_STATE_VOCABULARY`: a state outside the partition
    raises instead of falling through, so every item contributes exactly once to continuation
    treatment. A retryable item whose conditions show unusable or unverifiable residual
    evidence, or an absence carrying no registered terminal reason, escalates to ``blocking`` —
    that evidence cannot be lawfully retried without adjudication.
    """
    state = item.state
    if state in _UNCERTAIN_ITEM_STATES:
        return "uncertain"
    if state in _BLOCKING_ITEM_STATES:
        return "blocking"
    if state in _SATISFYING_ITEM_STATES:
        return "satisfying"
    if state in _RETRYABLE_ITEM_STATES:
        if any(condition in _BLOCKING_ITEM_CONDITIONS for condition in item.conditions):
            return "blocking"
        return "retryable"
    message = (
        f"reconciliation emitted item state {state!r}, which is outside the exhaustive "
        "continuation-state partition; an unclassifiable state refuses rather than falls "
        "through every set"
    )
    raise AcquisitionGateError(message)


@dataclass(frozen=True, slots=True)
class StoreFinding:
    """One store-level inconsistency the reconciliation surfaces without acting on it."""

    kind: str
    relative_path: str | None
    observation_id: str | None

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for serialization and comparison."""
        return {
            "kind": self.kind,
            "observation_id": self.observation_id,
            "relative_path": self.relative_path,
        }


@dataclass(frozen=True, slots=True)
class DriftListingEntry:
    """One committed observation carrying registered drift reasons."""

    observation_id: str
    source_id: str
    request_identity: str
    reason_codes: tuple[str, ...]
    blocking: bool

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for serialization and comparison."""
        return {
            "blocking": self.blocking,
            "observation_id": self.observation_id,
            "reason_codes": list(self.reason_codes),
            "request_identity": self.request_identity,
            "source_id": self.source_id,
        }


@dataclass(frozen=True, slots=True)
class RequestReconciliation:
    """The deterministic plan-to-catalog reconciliation for one window.

    Read-only by construction: every input is durable state, every output is in-memory, and
    identical inputs produce a byte-identical :meth:`as_record` serialization. Item-level
    absence identities live here and in the catalog — never in a receipt (Decision 040 §9).
    """

    window: str
    plan_sha256: str
    items: tuple[ReconciliationItem, ...]
    out_of_plan: tuple[tuple[str, str], ...]
    store_findings: tuple[StoreFinding, ...]
    drift: tuple[DriftListingEntry, ...]
    blocked_recovery_states: int

    @property
    def totals(self) -> Mapping[str, int]:
        """Per-state item totals; always sums to the planned logical request count."""
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.state] = counts.get(item.state, 0) + 1
        return dict(sorted(counts.items()))

    @property
    def absences(self) -> tuple[ReconciliationItem, ...]:
        """Planned requests whose terminal disposition left the required object absent."""
        return tuple(
            item for item in self.items if item.state in {"absent", "failed", "quarantined"}
        )

    @property
    def absences_without_terminal_reason(self) -> tuple[ReconciliationItem, ...]:
        """Absences carrying no registered reason code — each one an adjudication defect."""
        return tuple(item for item in self.absences if not item.reason_codes)

    @property
    def already_satisfied_excluded_count(self) -> int:
        """Every request excluded from the future continuation run.

        The future receipt's ``cache_hit_count`` (Decision 040 §6): already satisfied by
        verified evidence and therefore never requested again. This is a **snapshot over the
        whole durable history**, so it deliberately **overlaps** the two historical disposition
        counters below — a request whose satisfying evidence is a lawful ``304``
        (:attr:`not_modified_count`) or a byte-identical ``200``
        (:attr:`duplicate_object_count`) is *also* excluded here. The three snapshot counters
        must never be summed as mutually exclusive outcomes. The future receipt mapping stays:
        excluded request → ``cache_hit_count``; physically requested lawful ``304`` →
        ``not_modified_count``; physically requested byte-identical ``200`` →
        ``duplicate_object_count``.
        """
        return sum(1 for item in self.items if item.excluded_from_continuation)

    @property
    def not_modified_count(self) -> int:
        """Items whose satisfying evidence is a lawful conditional ``304`` reuse.

        The future receipt's ``not_modified_count`` (Decision 040 §6): a request physically
        attempted with accepted validators and reconciled against preserved evidence. As a
        historical disposition counter it may overlap
        :attr:`already_satisfied_excluded_count` — the same item counts in both — so the two
        are never additive.
        """
        return sum(1 for item in self.items if item.state == "satisfied_not_modified")

    @property
    def duplicate_object_count(self) -> int:
        """Items whose satisfying evidence is a byte-identical ``200`` reconciliation.

        The future receipt's ``duplicate_object_count`` (Decision 040 §6): a physically
        retrieved response whose bytes matched preserved immutable evidence. As a historical
        disposition counter it may overlap :attr:`already_satisfied_excluded_count` — the same
        item counts in both — so the two are never additive.
        """
        return sum(1 for item in self.items if item.state == "satisfied_duplicate")

    @property
    def blocking_drift(self) -> tuple[DriftListingEntry, ...]:
        """Drift events whose registered reasons block."""
        return tuple(entry for entry in self.drift if entry.blocking)

    @property
    def nonblocking_drift(self) -> tuple[DriftListingEntry, ...]:
        """Drift events observed and retained without blocking."""
        return tuple(entry for entry in self.drift if not entry.blocking)

    @property
    def is_clean(self) -> bool:
        """Whether nothing requires adjudication, repair, or referral."""
        return (
            not self.absences
            and not self.out_of_plan
            and not self.store_findings
            and not self.blocking_drift
            and self.blocked_recovery_states == 0
            and all(_classify_item(item) == "satisfying" for item in self.items)
            and all(not item.conditions for item in self.items)
        )

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping: identical inputs serialize byte-identically."""
        return {
            "blocked_recovery_states": self.blocked_recovery_states,
            "drift": [entry.as_record() for entry in self.drift],
            "items": [item.as_record() for item in self.items],
            "out_of_plan": [list(pair) for pair in self.out_of_plan],
            "plan_sha256": self.plan_sha256,
            "store_findings": [finding.as_record() for finding in self.store_findings],
            "totals": dict(self.totals),
            "window": self.window,
        }


def _planned_request_identity(request: LogicalRequest) -> str:
    """The normalized request identity the driver records for one planned request."""
    spec = require_registered(request.source_id)
    url = spec.url(**dict(request.parameters))
    return request_identity(request.source_id, url, dict(request.parameters))


def _drift_flags(reason_codes: tuple[str, ...]) -> tuple[tuple[str, ...], bool]:
    """The drift-family codes on one observation, and whether any of them blocks."""
    family = tuple(code for code in reason_codes if code in _DRIFT_REASON_CODES)
    blocking = any(REASON_CODES[code].blocks_release for code in family if code in REASON_CODES)
    return family, blocking


def _evidence_conditions(
    reconstruction: CatalogReconstruction,
    observation: SourceObservation,
) -> tuple[str, ...]:
    """Why a usable-looking observation's evidence does not verify, as stable conditions."""
    conditions: list[str] = []
    owner_id = observation.reused_observation_id or observation.observation_id
    owner = reconstruction.by_id(owner_id) or observation
    try:
        path = reconstruction.store.payload_path(owner)
    except DisclosureDriftError:
        return ("row_without_object",)
    if not path.is_file():
        return ("row_without_object",)
    try:
        reconstruction.store.verify_payload(owner)
    except (DisclosureDriftError, OSError):
        conditions.append("hash_mismatch")
    spec = SOURCES.get(observation.source_id)
    if spec is not None and spec.expected_content == "zip":
        members = reconstruction.archive_member_counts.get(owner.observation_id, 0)
        mismatched = reconstruction.archive_lineage_mismatches.get(owner.observation_id, 0)
        if members == 0 or mismatched:
            conditions.append("archive_lineage_missing_or_invalid")
    return tuple(conditions)


def _item_for(
    position: int,
    request: LogicalRequest,
    reconstruction: CatalogReconstruction,
    in_flight_request_identity: str | None,
) -> ReconciliationItem:
    """Derive one planned request's item record from durable state alone."""
    identity = _planned_request_identity(request)
    predecessor = verified_reusable_predecessor(reconstruction, request.source_id, identity)
    latest = reconstruction.latest_any(request.source_id, identity)
    conditions: list[str] = []

    if predecessor is not None and predecessor.observation_id is not None:
        satisfying = reconstruction.by_id(predecessor.observation_id)
        state = {
            "stored_new": "satisfied_new",
            "superseded": "satisfied_superseding",
            "unchanged_content": "satisfied_duplicate",
            "reused_snapshot": "satisfied_not_modified",
        }[satisfying.outcome if satisfying is not None else "stored_new"]
        observation_id = predecessor.observation_id
        verified = True
        excluded = True
        attempts = satisfying.attempts if satisfying is not None else 0
        reason_codes = satisfying.reason_codes if satisfying is not None else ()
    elif latest is None:
        state = "not_attempted"
        observation_id = None
        verified = False
        excluded = False
        attempts = 0
        reason_codes = ()
        if identity == in_flight_request_identity:
            state = "stopped"
            conditions.append("receiptless_in_flight")
    else:
        observation_id = latest.observation_id
        verified = False
        excluded = False
        attempts = latest.attempts
        reason_codes = latest.reason_codes
        if latest.outcome == "quarantined":
            state = "quarantined"
        elif latest.outcome == "failed":
            state = "absent" if latest.http_status == 404 else "failed"
        else:
            evidence = _evidence_conditions(reconstruction, latest)
            conditions.extend(evidence)
            if "row_without_object" in evidence:
                state = "row_without_object"
            elif "archive_lineage_missing_or_invalid" in evidence:
                state = "archive_lineage_missing_or_invalid"
            elif "hash_mismatch" in evidence:
                state = "hash_mismatch"
            else:
                state = "failed"
                conditions.append("unverifiable_evidence")

    if state in {"absent", "failed", "quarantined"} and not reason_codes:
        conditions.append("absence_without_terminal_reason")
    family, blocking = _drift_flags(tuple(reason_codes))
    if family:
        conditions.append("drift_blocking" if blocking else "drift_nonblocking")

    return ReconciliationItem(
        position=position,
        source_id=request.source_id,
        identity_label=request.identity_label,
        request_identity=identity,
        state=state,
        observation_id=observation_id,
        verified=verified,
        excluded_from_continuation=excluded,
        attempts=attempts,
        reason_codes=tuple(reason_codes),
        conditions=tuple(conditions),
    )


def reconcile_requests(
    *,
    plan: RequestPlan,
    reconstruction: CatalogReconstruction,
    storage: StorageBinding,
    in_flight_request_identity: str | None = None,
) -> RequestReconciliation:
    """Reconcile the approved plan against durable catalog and object state. Writes nothing.

    Output order is the plan's own deterministic expansion order; store findings and drift
    entries are sorted; identical inputs produce a byte-identical serialization. Detection
    never repairs: an orphan, a partial, a missing referent, or blocking drift is *reported*,
    and every mutation belongs to the separately invoked recovery applier.
    """
    requests = derive_logical_requests(plan)
    items = tuple(
        _item_for(position, request, reconstruction, in_flight_request_identity)
        for position, request in enumerate(requests)
    )
    for item in items:
        if item.state not in _ITEM_STATE_VOCABULARY:
            message = (
                f"reconciliation emitted item state {item.state!r} for "
                f"{item.identity_label!r}, which is outside the exhaustive continuation-state "
                "vocabulary; emission refuses rather than letting a state fall through the "
                "partition"
            )
            raise AcquisitionGateError(message)

    planned = {(request.source_id, _planned_request_identity(request)) for request in requests}
    out_of_plan = tuple(
        sorted(
            {
                (observation.source_id, observation.identity)
                for observation in reconstruction.observations
                if (observation.source_id, observation.identity) not in planned
            }
        )
    )

    sweep = observe_recovery_state(
        storage=storage,
        observations=reconstruction.observations,
        ceiling=PhysicalAttemptCeiling(0),
    )
    findings: list[StoreFinding] = []
    for relative in sweep.partial_objects:
        findings.append(
            StoreFinding(kind="partial_object", relative_path=relative, observation_id=None)
        )
    for relative in sweep.orphan_objects:
        findings.append(
            StoreFinding(kind="orphan_object", relative_path=relative, observation_id=None)
        )
    referents = {
        observation.relative_storage_path: observation.observation_id
        for observation in reconstruction.observations
        if observation.relative_storage_path
    }
    for relative in sweep.missing_referents:
        findings.append(
            StoreFinding(
                kind="row_without_object",
                relative_path=relative,
                observation_id=referents.get(relative),
            )
        )
    findings.sort(key=lambda finding: (finding.kind, finding.relative_path or ""))

    drift: list[DriftListingEntry] = []
    for observation in reconstruction.observations:
        family, blocking = _drift_flags(observation.reason_codes)
        if family:
            drift.append(
                DriftListingEntry(
                    observation_id=observation.observation_id,
                    source_id=observation.source_id,
                    request_identity=observation.identity,
                    reason_codes=family,
                    blocking=blocking,
                )
            )
    drift.sort(key=lambda entry: entry.observation_id)

    return RequestReconciliation(
        window=plan.acquisition_window,
        plan_sha256=plan.request_plan_sha256,
        items=items,
        out_of_plan=out_of_plan,
        store_findings=tuple(findings),
        drift=tuple(drift),
        blocked_recovery_states=reconstruction.blocked_recovery_states,
    )


# --------------------------------------------------------------------------- #
# T2.4-C — continuation proposal and conservative attempt accounting
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CumulativeAttemptAccounting:
    """The Decision 040 §7 cumulative consumed-attempt calculation, or its refusal.

    Exactly three addends, each counted once: the resolvable predecessor receipt chain's
    cumulative attempts; committed observation attempts deterministically attributed after the
    final terminating receipt; and the full registered ``A_reachable`` for at most one
    identifiable receiptless in-flight request. Any attribution ambiguity is ``UNDETERMINED``
    and prohibits continuation — never estimated, never rounded down.
    """

    chain_consumed: int
    post_receipt_attempts: int
    in_flight_charge: int
    in_flight_request_identity: str | None
    undetermined: bool
    basis: str

    @property
    def cumulative_consumed(self) -> int:
        """The conservative cumulative total charged against the approved ceiling."""
        return self.chain_consumed + self.post_receipt_attempts + self.in_flight_charge


@dataclass(frozen=True, slots=True)
class ContinuationRequest:
    """One remaining logical request, with lawful conditional validators where they exist."""

    position: int
    source_id: str
    identity_label: str
    request_identity: str
    etag: str | None
    last_modified: str | None


@dataclass(frozen=True, slots=True)
class ContinuationProposal:
    """A deterministic, read-only continuation proposal (Decision 040 §2, T2.4-C).

    A proposal only: continuation **authorization** remains an explicit later owner act, and
    continuation **execution** — ``m3 acquire --resume-from`` wiring — remains deferred to the
    operator-surface stage. Nothing here places a request, constructs a transport, emits a
    receipt, or mutates any durable state.
    """

    permitted: bool
    determination: str
    refusal_reasons: tuple[str, ...]
    window: str
    plan_sha256: str
    approved_ceiling: int
    predecessor_receipt_id: str | None
    receipt_chain: tuple[str, ...]
    accounting: CumulativeAttemptAccounting
    remaining_headroom: int
    worst_case_remaining_attempts: int
    fits: bool
    already_satisfied_excluded: tuple[str, ...]
    remaining: tuple[ContinuationRequest, ...]
    reconciliation: RequestReconciliation
    inspection: RecoveryState

    @property
    def already_satisfied_excluded_count(self) -> int:
        """The future receipt's ``cache_hit_count``: satisfied, so never requested."""
        return len(self.already_satisfied_excluded)


def _parse_receipt_instant(value: object) -> datetime | None:
    """Parse one RFC 3339 UTC instant; ``None`` when it cannot be trusted for ordering."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _segment_after_receipt(
    observations: Sequence[SourceObservation],
    completed_at: datetime,
) -> tuple[int, int, frozenset[tuple[str, str]], str | None]:
    """Split committed attempts around the final terminating receipt, or explain why not.

    Returns ``(pre_attempts, post_attempts, post_identities, undetermined_basis)``. A row whose
    instant is unparseable, or that coincides exactly with the receipt boundary, cannot be
    attributed uniquely — that is ``UNDETERMINED``, not a rounding choice.
    """
    pre_attempts = 0
    post_attempts = 0
    post_identities: set[tuple[str, str]] = set()
    for observation in observations:
        instant = _parse_receipt_instant(observation.retrieved_at_utc)
        if instant is None:
            return (
                0,
                0,
                frozenset(),
                (
                    f"observation {observation.observation_id} carries no attributable UTC "
                    "instant, so the post-receipt attempt segment cannot be attributed uniquely"
                ),
            )
        if instant == completed_at:
            return (
                0,
                0,
                frozenset(),
                (
                    f"observation {observation.observation_id} coincides exactly with the "
                    "terminating receipt boundary, so its segment cannot be attributed uniquely"
                ),
            )
        if instant > completed_at:
            post_attempts += observation.attempts
            post_identities.add((observation.source_id, observation.identity))
        else:
            pre_attempts += observation.attempts
    return pre_attempts, post_attempts, frozenset(post_identities), None


@dataclass(frozen=True, slots=True)
class _SpoolInterpretation:
    """What the staging spools durably identify, or why they cannot be interpreted."""

    routes: tuple[str, ...]
    undetermined_basis: str | None


def _interpret_staging_spools(tree: DataTree) -> _SpoolInterpretation:
    """Interpret staging ``.part`` spools by the accepted naming structure, fail-closed.

    A spool identifies a **route** only, and only when it is a regular file contained in the
    accepted staging root whose name parses exactly as
    ``{registered source_id}-{32-hex nonce}.part`` — the structure the accepted snapshot store
    writes. A symlinked staging root, a symlinked or escaping spool, a prefix that is not a
    registered source identifier, and a malformed nonce are each refused as ``UNDETERMINED``:
    an ambiguous generic string split never stands in for the accepted structure, and
    uncertainty never becomes a zero charge.
    """
    staging = tree.staging
    if staging.is_symlink():
        return _SpoolInterpretation(
            (), "the staging root is a symbolic link, so spool evidence cannot be trusted"
        )
    if not staging.is_dir():
        return _SpoolInterpretation((), None)
    resolved_staging = Path(os.path.realpath(staging))
    routes: list[str] = []
    for path in sorted(staging.rglob("*.part")):
        if path.is_symlink():
            return _SpoolInterpretation(
                (),
                f"staging spool {path.name!r} is a symbolic link and is refused as "
                "identification evidence",
            )
        if not path.is_file():
            return _SpoolInterpretation(
                (), f"staging entry {path.name!r} is not a regular spool file"
            )
        resolved = Path(os.path.realpath(path))
        if resolved_staging != resolved.parent and resolved_staging not in resolved.parents:
            return _SpoolInterpretation(
                (), f"staging spool {path.name!r} resolves outside the accepted staging root"
            )
        prefix, separator, nonce = path.name.removesuffix(".part").rpartition("-")
        if not separator or prefix not in SOURCES or _SPOOL_NONCE.fullmatch(nonce) is None:
            return _SpoolInterpretation(
                (),
                f"staging spool {path.name!r} does not parse as the accepted "
                "'{source_id}-{uuid}.part' structure, so its route identity cannot be "
                "established",
            )
        routes.append(prefix)
    return _SpoolInterpretation(tuple(routes), None)


def _contradicting_store_evidence(
    tree: DataTree,
    observations: Sequence[SourceObservation],
) -> tuple[str, ...]:
    """Unaccounted raw-store artifacts that contradict any single lawful in-flight identity.

    Raw-side ``.part`` partials, orphan objects, and stray lineage intents each mark durable
    activity with no lawful route identity of their own. When any exists, a single in-flight
    request cannot reasonably be the whole story, so identification refuses rather than
    charging one request and silently zero-charging the rest. Read-only, and symlink-averse
    like the accepted read-only observer.
    """
    recorded = {
        observation.relative_storage_path
        for observation in observations
        if observation.relative_storage_path
    }
    findings: list[str] = []
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            if path.name.endswith(".reason"):
                continue
            relative = tree.relative(path)
            if path.name.endswith(LINEAGE_SUFFIX):
                object_path = path.with_name(path.name.removesuffix(LINEAGE_SUFFIX))
                object_relative = tree.relative(object_path)
                if object_relative not in recorded and not object_path.exists():
                    findings.append(relative)
                continue
            if path.name.endswith(".part") or relative not in recorded:
                findings.append(relative)
    return tuple(sorted(findings))


def _identify_in_flight(
    requests: Sequence[LogicalRequest],
    reconstruction: CatalogReconstruction,
    post_identities: frozenset[tuple[str, str]],
    spool_routes: tuple[str, ...],
) -> tuple[str | None, str | None]:
    """The one durably identified receiptless in-flight request, or why none can be named.

    Identification is evidence-based, never positional — plan-order position alone may never
    identify the request. A staging spool identifies a route; it identifies a logical request
    only when exactly one relevant spool exists, its route parses uniquely, exactly one
    unresolved planned request uses that route, every preceding planned request carries durable
    satisfying or terminal evidence, and no later request shows post-receipt activity. Any
    other reading — a route that disagrees with the sequential position, a shared route, or
    more than one possible in-flight request — is ``UNDETERMINED``, never a guess and never a
    zero charge.
    """
    if len(spool_routes) > 1:
        return None, (
            f"{len(spool_routes)} staging spools exist, so more than one in-flight request "
            "appears possible"
        )

    identities = [_planned_request_identity(request) for request in requests]
    unresolved: list[int] = []
    for position, request in enumerate(requests):
        satisfied = (
            verified_reusable_predecessor(reconstruction, request.source_id, identities[position])
            is not None
        )
        has_row = reconstruction.latest_any(request.source_id, identities[position]) is not None
        if not satisfied and not has_row:
            unresolved.append(position)

    if not spool_routes:
        return None, None

    route = spool_routes[0]
    matching = [position for position in unresolved if requests[position].source_id == route]
    if not matching:
        return None, (
            f"the staging spool identifies route {route!r}, but no unresolved planned request "
            "uses that route; the durable evidence contradicts every candidate identity"
        )
    if len(matching) > 1:
        return None, (
            f"{len(matching)} unresolved planned requests share the spool's route {route!r}, "
            "so the in-flight logical request cannot be identified uniquely"
        )
    candidate = matching[0]
    if unresolved[0] != candidate:
        return None, (
            f"the staging spool's route {route!r} disagrees with the first unresolved planned "
            "request in the sequential engine's order; plan-order position alone may never "
            "identify the request, so the contradiction is UNDETERMINED"
        )
    for position in range(candidate + 1, len(requests)):
        if (requests[position].source_id, identities[position]) in post_identities:
            return None, (
                "post-receipt activity exists for a request after the identified one, so more "
                "than one in-flight request appears possible"
            )
    return identities[candidate], None


def propose_continuation(
    *,
    plan: RequestPlan,
    receipt_chain_head: Path,
    catalog_path: Path,
    storage: StorageBinding,
    window: str,
    approved_ceiling: int,
) -> ContinuationProposal:
    """Derive the deterministic continuation proposal for one interrupted window.

    Read-only, and bound to everything Decision 040 §2 (T2.4-C) names: the predecessor
    receipt-chain identity, the exact plan hash, the exact acquisition window, the exact
    approved ceiling, the durable catalog and object state, and the cumulative attempt
    evidence. Every refusal is carried in the result rather than raised, so a refused proposal
    is itself deterministic evidence; only caller errors (a missing catalog or head receipt)
    raise.

    Raises:
        AcquisitionGateError: the window is not an accepted acquisition window.
        RecoveryInspectionError: the catalog or the head receipt does not exist.
    """
    if window not in ACQUISITION_WINDOWS:
        message = f"window {window!r} is not one of the accepted acquisition windows"
        raise AcquisitionGateError(message)

    refusals: list[str] = []
    if plan.acquisition_window != window:
        refusals.append(
            f"the approved plan is for window {plan.acquisition_window!r}, not {window!r}"
        )
    if approved_ceiling != plan.hard_request_ceiling:
        refusals.append(
            f"the supplied ceiling {approved_ceiling} does not equal the plan's approved "
            f"ceiling {plan.hard_request_ceiling}; the ceiling is never reinterpreted"
        )

    inspection = inspect_recovery_state(
        plan=plan,
        receipt_chain_head=receipt_chain_head,
        catalog_path=catalog_path,
        data_root=storage.data_root,
    )
    reconstruction = reconstruct_catalog_state(catalog_path=catalog_path, storage=storage)
    requests = derive_logical_requests(plan)

    predecessor_receipt_id: str | None = None
    completed_at: datetime | None = None
    undetermined_basis: str | None = None
    try:
        head = inspect_receipt(Path(receipt_chain_head))
    except (OSError, ReceiptValidationError) as exc:
        refusals.append(f"the predecessor receipt cannot be read as a valid receipt: {exc}")
        head = None
    if head is not None:
        predecessor_receipt_id = str(head["receipt_id"])
        if head.get("invocation_mode") != "live":
            refusals.append(
                "the predecessor receipt is not a live acquisition receipt; a continuation "
                "binds only to a live predecessor"
            )
        if head.get("acquisition_window") not in {None, window}:
            refusals.append(
                f"the predecessor receipt names window {head.get('acquisition_window')!r}, "
                f"not {window!r}"
            )
        head_ceiling = head.get("approved_request_ceiling")
        if head_ceiling is not None and head_ceiling != approved_ceiling:
            refusals.append(
                f"the predecessor receipt records approved ceiling {head_ceiling}, not "
                f"{approved_ceiling}; the ceiling is never raised, reset, or replaced"
            )
        completed_at = _parse_receipt_instant(head.get("completed_at_utc"))
        if completed_at is None:
            undetermined_basis = (
                "the predecessor receipt carries no attributable completion instant, so the "
                "post-receipt attempt segment cannot be attributed uniquely"
            )

    chain_resolved = all(
        condition.status == "MET"
        for condition in inspection.conditions
        if condition.number == "8.1"
    )
    if not chain_resolved and undetermined_basis is None:
        undetermined_basis = (
            "the predecessor receipt chain does not resolve, so cumulative consumption "
            "cannot be established"
        )

    pre_attempts = 0
    post_attempts = 0
    post_identities: frozenset[tuple[str, str]] = frozenset()
    if undetermined_basis is None and completed_at is not None:
        pre_attempts, post_attempts, post_identities, undetermined_basis = _segment_after_receipt(
            reconstruction.observations, completed_at
        )
    if undetermined_basis is None and pre_attempts > inspection.consumed_physical_attempts:
        undetermined_basis = (
            f"committed rows before the terminating receipt carry {pre_attempts} attempt(s) "
            f"but the receipt chain records {inspection.consumed_physical_attempts}; the "
            "evidence disagrees materially"
        )

    # In-flight identity is established from durable evidence only, never from plan position
    # alone. A streamed spool dies in staging under the accepted `{source_id}-{uuid}.part`
    # structure and identifies a route; raw-side partials, orphans, and stray lineage intents
    # are unaccounted activity with no lawful route identity of their own. Committed
    # post-receipt rows are already accounted exactly by `post_attempts` and are not in-flight
    # evidence — with no spool and no contradicting artifact there is nothing in flight to
    # charge, while any ambiguity is UNDETERMINED rather than a zero charge.
    in_flight_identity: str | None = None
    in_flight_charge = 0
    if undetermined_basis is None:
        spools = _interpret_staging_spools(storage.tree)
        if spools.undetermined_basis is not None:
            undetermined_basis = spools.undetermined_basis
        else:
            contradicting = _contradicting_store_evidence(storage.tree, reconstruction.observations)
            if spools.routes:
                in_flight_identity, in_flight_basis = _identify_in_flight(
                    requests, reconstruction, post_identities, spools.routes
                )
                if in_flight_identity is None:
                    undetermined_basis = in_flight_basis
                elif contradicting:
                    undetermined_basis = (
                        f"{len(contradicting)} unaccounted raw-store artifact(s) exist beside "
                        "the staging spool, so no single in-flight identity is uncontradicted "
                        "and more than one in-flight request appears possible"
                    )
                    in_flight_identity = None
                else:
                    in_flight_charge = derive_a_reachable(SOURCES[spools.routes[0]])
            elif contradicting:
                undetermined_basis = (
                    f"{len(contradicting)} unaccounted raw-store artifact(s) (a partial, an "
                    "orphan, or a stray lineage intent) exist with no lawful route identity, "
                    "so in-flight attribution cannot be established; uncertainty never becomes "
                    "a zero charge"
                )

    accounting = CumulativeAttemptAccounting(
        chain_consumed=inspection.consumed_physical_attempts,
        post_receipt_attempts=post_attempts,
        in_flight_charge=in_flight_charge,
        in_flight_request_identity=in_flight_identity,
        undetermined=undetermined_basis is not None,
        basis=(
            undetermined_basis
            if undetermined_basis is not None
            else "every attempt segment is attributed exactly once"
        ),
    )

    reconciliation = reconcile_requests(
        plan=plan,
        reconstruction=reconstruction,
        storage=storage,
        in_flight_request_identity=in_flight_identity,
    )

    # The exhaustive continuation-state partition is the single mechanism deciding every
    # item's treatment: satisfying items are excluded from replay; retryable items are the
    # remainder, each included exactly once; blocking items refuse the whole proposal and are
    # omitted from the transport remainder only because of that refusal; uncertain items make
    # the proposal UNDETERMINED.
    treatments = tuple((item, _classify_item(item)) for item in reconciliation.items)
    already_satisfied = tuple(
        item.identity_label for item, treatment in treatments if treatment == "satisfying"
    )
    blocking_items = tuple(item for item, treatment in treatments if treatment == "blocking")
    uncertain_items = tuple(item for item, treatment in treatments if treatment == "uncertain")
    remaining: list[ContinuationRequest] = []
    for item, treatment in treatments:
        if treatment != "retryable":
            continue
        validators = conditional_validators(reconstruction, item.source_id, item.request_identity)
        etag, last_modified = validators if validators is not None else (None, None)
        remaining.append(
            ContinuationRequest(
                position=item.position,
                source_id=item.source_id,
                identity_label=item.identity_label,
                request_identity=item.request_identity,
                etag=etag,
                last_modified=last_modified,
            )
        )

    cumulative = accounting.cumulative_consumed
    remaining_headroom = max(0, approved_ceiling - cumulative)
    worst_case = sum(derive_a_reachable(SOURCES[request.source_id]) for request in remaining)
    fits = not accounting.undetermined and worst_case <= remaining_headroom

    if accounting.undetermined:
        refusals.append(f"cumulative attempt accounting is UNDETERMINED: {accounting.basis}")
    if cumulative > approved_ceiling and not accounting.undetermined:
        refusals.append(
            f"cumulative consumption {cumulative} already exceeds the approved ceiling "
            f"{approved_ceiling}; no further physical request may occur"
        )
    if not fits and not accounting.undetermined and remaining:
        refusals.append(
            f"the worst-case remainder ({worst_case} attempt(s)) does not fit the remaining "
            f"headroom ({remaining_headroom}); stop for re-planning and a fresh exact owner "
            "approval — the ceiling is never raised"
        )
    if inspection.determination != "SAFE":
        refusals.append(
            f"the read-only inspection is {inspection.determination}: {inspection.basis}"
        )
    if reconstruction.blocked_t2_4_recovery_states:
        refusals.append(
            f"{reconstruction.blocked_t2_4_recovery_states} unresolved t2_4_recovery_action "
            "write-ahead state(s) remain blocked; a recovery mutation may have begun without "
            "its completed event and exact resolution, so continuation is prohibited until "
            "each is exactly resolved and a fresh inspection passes"
        )
    blocking_defects: list[str] = []
    if blocking_items:
        states = sorted({item.state for item in blocking_items})
        blocking_defects.append(f"{len(blocking_items)} item(s) in blocking state(s) {states}")
    if reconciliation.out_of_plan:
        blocking_defects.append(f"{len(reconciliation.out_of_plan)} out-of-plan observation(s)")
    if reconciliation.blocking_drift:
        blocking_defects.append(f"{len(reconciliation.blocking_drift)} blocking drift event(s)")
    if blocking_defects:
        refusals.append(
            "a blocking reconciliation defect refuses continuation: "
            + "; ".join(blocking_defects)
            + " — a blocking defect never counts as satisfied and never silently leaves the "
            "remainder; it is omitted from the transport remainder only because this whole "
            "proposal is refused"
        )
    if uncertain_items:
        labels = sorted(item.identity_label for item in uncertain_items)
        refusals.append(
            f"durable persistence cannot be established for {len(uncertain_items)} item(s) "
            f"{labels}; the state is persistence-uncertain and continuation is prohibited"
        )

    persistence_uncertain = bool(
        accounting.undetermined or uncertain_items or reconstruction.blocked_t2_4_recovery_states
    )
    determination = "UNDETERMINED" if persistence_uncertain else inspection.determination
    # ``permitted`` and the refusal explanations are one fact stated twice: a proposal is
    # permitted exactly when nothing appended a refusal reason, so a suppressed reason cannot
    # leave a silently refused (or silently permitted) proposal behind.
    permitted = not refusals
    return ContinuationProposal(
        permitted=permitted,
        determination=determination,
        refusal_reasons=tuple(refusals),
        window=window,
        plan_sha256=plan.request_plan_sha256,
        approved_ceiling=approved_ceiling,
        predecessor_receipt_id=predecessor_receipt_id,
        receipt_chain=inspection.receipt_chain,
        accounting=accounting,
        remaining_headroom=remaining_headroom,
        worst_case_remaining_attempts=worst_case,
        fits=fits,
        already_satisfied_excluded=already_satisfied,
        remaining=tuple(remaining),
        reconciliation=reconciliation,
        inspection=inspection,
    )


# --------------------------------------------------------------------------- #
# T2.4-D — the explicit, inert recovery-action library boundary
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RecoveryActionResult:
    """What one explicitly requested recovery action did, and what must happen next.

    No field here is the only continuation prohibition: the write-ahead
    ``census_recovery_states`` row this result names is the durable authority, and a restarted
    process recomputes from it. ``post_state_undetermined`` reports what *this invocation*
    could prove; the blocked-or-resolved row is what outlives it.
    """

    action: str
    target: str
    census_run_id: str
    recovery_state_id: str
    action_taken: str
    event_recorded: bool
    state_resolved: bool
    post_state_undetermined: bool
    detail: str

    @property
    def requires_fresh_inspection(self) -> bool:
        """A fresh read-only inspection is always required after a mutation."""
        return True

    @property
    def continuation_prohibited(self) -> bool:
        """Continuation stays prohibited until a fresh inspection returns ``SAFE``.

        When event recording, exact resolution, or the resolution readback failed, the state
        is ``UNDETERMINED`` and continuation is prohibited unconditionally — durably, through
        the still-blocked write-ahead row, not through this in-memory field alone (Decision
        040 §2, T2.4-D; Decision 041 §9).
        """
        return True


@dataclass(frozen=True, slots=True)
class _RepairSweep:
    """A read-only sweep of everything the four repair actions could lawfully target."""

    raw_partials: tuple[str, ...]
    staging_partials: tuple[str, ...]
    reconcile_orphans: tuple[str, ...]
    stray_lineage_intents: tuple[str, ...]
    projection_valid: bool


def _repair_sweep(catalog_path: Path, storage: StorageBinding) -> _RepairSweep:
    """Observe, without acting, exactly what ``observation_catalog.reconcile`` would touch.

    Symlink-averse in exact alignment with the accepted read-only observer: a symbolic link is
    skipped, never classified, so a symlinked staging ``.part`` can never become an authorized
    ``remove-stale-part`` candidate and a symlinked object can never become an orphan to adopt.
    The mutating boundary therefore refuses (target-not-a-candidate) exactly where the
    read-only sweep ignores, the link target stays untouched, and no containment protection is
    weakened.
    """
    tree = storage.tree
    with read_only_catalog(Path(catalog_path)) as connection:
        observations = load_observations(connection)
        projection_valid = validate_audit_projection(
            connection, tree.audit / _PROJECTION_NAME
        ).is_valid
    recorded = {
        observation.relative_storage_path
        for observation in observations
        if observation.relative_storage_path
    }

    raw_partials: list[str] = []
    staging_partials: list[str] = []
    orphans: list[str] = []
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings, tree.staging):
        if not root.is_dir() or root.is_symlink():
            continue
        in_staging = root == tree.staging
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            if path.name.endswith(".reason") or path.name.endswith(LINEAGE_SUFFIX):
                continue
            relative = relative_to_root(path, tree.data_root)
            if path.name.endswith(".part"):
                (staging_partials if in_staging else raw_partials).append(relative)
            elif relative not in recorded:
                orphans.append(relative)

    stray_intents: list[str] = []
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings):
        if not root.is_dir():
            continue
        for lineage in sorted(root.rglob(f"*{LINEAGE_SUFFIX}")):
            if lineage.is_symlink():
                continue
            object_path = lineage.with_name(lineage.name.removesuffix(LINEAGE_SUFFIX))
            object_relative = relative_to_root(object_path, tree.data_root)
            if object_relative in recorded or object_path.exists():
                continue
            stray_intents.append(relative_to_root(lineage, tree.data_root))

    return _RepairSweep(
        raw_partials=tuple(raw_partials),
        staging_partials=tuple(staging_partials),
        reconcile_orphans=tuple(orphans),
        stray_lineage_intents=tuple(stray_intents),
        projection_valid=projection_valid,
    )


def _refuse_repair(reason: str) -> RepairRefusedError:
    return RepairRefusedError(f"the recovery action is refused: {reason}")


def apply_recovery_action(
    *,
    action: str,
    target: str,
    plan: RequestPlan,
    receipt_chain_head: Path,
    catalog_path: Path,
    storage: StorageBinding,
    census_run_id: str,
    lock_directory: Path | None = None,
) -> RecoveryActionResult:
    """Apply exactly one explicitly requested, deterministically required recovery action.

    The applier never runs automatically — no reconstruction, reconciliation, inspection,
    drift, or proposal code calls it — and it refuses rather than adapts: an unknown or
    multi-action request, an ``UNDETERMINED`` state, a stale or already-resolved target, an
    action that differs from the deterministic recommendation, and a request its one authorized
    primitive cannot be scoped to are all refused before anything mutates.

    Every mutation is durably write-ahead protected (Decision 041 §8). The corrected sequence:
    the exact required action and target are recomputed and validated; the caller-supplied,
    already registered ``ops_ingestion_jobs.job_id`` is validated (no run identity is ever
    created, fabricated, or substituted here); a second action is refused while any
    ``t2_4_recovery_action`` state for that run remains unresolved; one opaque unique
    ``recovery_state_id`` is created and persisted ``blocked`` through the accepted
    :func:`open_recovery_state` primitive, committed **before** the mutation and verified
    through a genuinely fresh read-only connection; exactly one authorized mutation runs
    through the accepted primitive for its action class; the actual completed recovery event is
    recorded through the accepted :func:`record_recovery_events` surface with
    ``census_run_id=None`` (opening the block is not itself a recovery event, and no second
    state row is created); only after event recording succeeds is the exact state resolved
    through :func:`resolve_recovery_state`; and the resolution is verified through a fresh
    connection. A failure at any post-mutation step leaves the exact state ``blocked``, so a
    restarted process sees the unresolved block durably — no in-memory field is ever the only
    continuation prohibition. A committed resolution whose readback cannot complete leaves this
    invocation ``UNDETERMINED``; a later process recomputes from durable catalog state.

    Nothing acquired is ever deleted or overwritten; the one deletion this boundary performs is
    a staging spool proven never promoted, never catalogued, never referenced, and never a
    symbolic link. A fresh read-only inspection is required afterwards in every case, and this
    function deliberately does not run it — re-inspection after repair is the operator
    workflow's explicit next step, never an automatic continuation.

    Raises:
        RepairRefusedError: the request is refused; nothing was mutated. A refusal after the
            write-ahead block committed (a verification or scoping anomaly) leaves that block
            durably ``blocked`` for owner adjudication — fail closed, still with no mutation.
        RecoveryInspectionError: the catalog or head receipt is absent, so the pre-mutation
            inspection cannot even begin.
    """
    if action not in RECOVERY_ACTIONS:
        reason = (
            f"{action!r} is not one of the four authorized deterministic action classes "
            f"{RECOVERY_ACTIONS}; combined or unknown actions are never coerced"
        )
        raise _refuse_repair(reason)
    if not target or not target.strip():
        reason = "an explicit target is required; an empty target names nothing"
        raise _refuse_repair(reason)

    inspection = inspect_recovery_state(
        plan=plan,
        receipt_chain_head=receipt_chain_head,
        catalog_path=catalog_path,
        data_root=storage.data_root,
    )
    if inspection.determination == "UNDETERMINED":
        reason = (
            f"the read-only inspection is UNDETERMINED ({inspection.basis}); every action is "
            "refused from UNDETERMINED and the state is referred to the owner"
        )
        raise _refuse_repair(reason)

    sweep = _repair_sweep(catalog_path, storage)
    required: dict[str, tuple[str, ...]] = {
        "adopt-orphan": sweep.reconcile_orphans,
        "quarantine-partial": sweep.raw_partials,
        "remove-stale-part": sweep.staging_partials,
        "rebuild-projection": () if sweep.projection_valid else (_PROJECTION_NAME,),
    }
    if all(not targets for targets in required.values()):
        reason = "nothing requires repair; the request is stale or already resolved"
        raise _refuse_repair(reason)
    candidates = required[action]
    if not candidates:
        recommended = ", ".join(sorted(name for name, targets in required.items() if targets))
        reason = (
            f"{action!r} differs from the deterministic recommendation; the current state "
            f"requires only: {recommended}"
        )
        raise _refuse_repair(reason)
    if target not in candidates:
        reason = (
            f"target {target!r} is not a current {action!r} candidate; the request is stale, "
            "already resolved, or misidentified"
        )
        raise _refuse_repair(reason)

    tree = storage.tree
    lock_dir = Path(lock_directory) if lock_directory is not None else Path(catalog_path).parent

    # Per-action scoping preconditions, still before any write of any kind.
    if action == "adopt-orphan":
        if len(sweep.reconcile_orphans) != 1:
            reason = (
                f"{len(sweep.reconcile_orphans)} orphan(s) exist; the accepted reconciliation "
                "primitive cannot be scoped to exactly one authorized event while another "
                "orphan would also be processed — repair one state at a time or refer to the "
                "owner"
            )
            raise _refuse_repair(reason)
        if sweep.stray_lineage_intents:
            reason = (
                "a lineage intent without its raw object exists; the accepted reconciliation "
                "primitive would quarantine it alongside the requested adoption, which is an "
                "unrelated mutation — resolve it first or refer to the owner"
            )
            raise _refuse_repair(reason)
        if not sweep.projection_valid:
            reason = (
                "the audit projection requires recovery; the accepted reconciliation "
                "primitive would persist a projection incident alongside the requested "
                "adoption — rebuild the projection first"
            )
            raise _refuse_repair(reason)
    if action == "remove-stale-part":
        spool_path = tree.data_root / target
        if spool_path.is_symlink():
            reason = (
                "the staging spool is a symbolic link and is never a removal candidate; the "
                "link target stays untouched"
            )
            raise _refuse_repair(reason)
        if RawStore.lineage_path(spool_path).exists():
            reason = (
                "the staging spool carries a lineage intent, so it cannot be proven a "
                "never-promoted temporary; quarantine is the lawful disposition"
            )
            raise _refuse_repair(reason)

    # The caller-supplied run identity: required, existing, and free of unresolved T2.4
    # write-ahead states. This applier never creates an ingestion-job row, never invokes the
    # private census-orchestrator job creator, and never substitutes a receipt identity.
    if not census_run_id or not census_run_id.strip():
        reason = (
            "no census run identity was supplied; every mutating T2.4 recovery action "
            "requires a caller-supplied, already registered ops_ingestion_jobs.job_id"
        )
        raise _refuse_repair(reason)
    try:
        with read_only_catalog(Path(catalog_path)) as connection:
            job = connection.execute(
                "SELECT 1 FROM ops_ingestion_jobs WHERE job_id = ?",
                (census_run_id,),
            ).fetchone()
            unresolved = int(
                connection.execute(
                    "SELECT COUNT(*) FROM census_recovery_states "
                    "WHERE census_run_id = ? AND scenario = ? AND resolution_state = 'blocked'",
                    (census_run_id, _T2_4_STATE_SCENARIO),
                ).fetchone()[0]
            )
    except (DisclosureDriftError, sqlite3.Error, OSError) as exc:
        reason = (
            f"the run identity could not be validated against the catalog "
            f"({type(exc).__name__}); the action refuses before mutation"
        )
        raise _refuse_repair(reason) from exc
    if job is None:
        reason = (
            f"census run {census_run_id!r} does not resolve to a lawful existing governed "
            "ops_ingestion_jobs row; a run identity is required and is never created, "
            "fabricated, or substituted by this applier"
        )
        raise _refuse_repair(reason)
    if unresolved:
        reason = (
            f"{unresolved} unresolved t2_4_recovery_action write-ahead state(s) already exist "
            f"for run {census_run_id!r}; a second action is refused before mutation until "
            "each is exactly resolved"
        )
        raise _refuse_repair(reason)

    # Open and commit the write-ahead block before the mutation, then verify the exact row
    # through a genuinely fresh read-only connection.
    recovery_state_id = uuid.uuid4().hex
    try:
        with CatalogWriter(Path(catalog_path), lock_dir) as writer:
            open_recovery_state(
                writer,
                census_run_id=census_run_id,
                recovery_state_id=recovery_state_id,
                scenario=_T2_4_STATE_SCENARIO,
                action_taken=action,
                detail=(
                    f"write-ahead block for the explicitly requested recovery action "
                    f"{action!r} on target {target!r}"
                ),
                relative_path=target,
            )
    except (DisclosureDriftError, sqlite3.Error, OSError) as exc:
        reason = (
            f"the write-ahead recovery state could not be opened and committed "
            f"({type(exc).__name__}); the action refuses before mutation"
        )
        raise _refuse_repair(reason) from exc
    if not _verify_write_ahead_state(catalog_path, census_run_id, recovery_state_id, "blocked"):
        reason = (
            "the committed write-ahead block could not be verified through a fresh read-only "
            "connection; the action refuses before mutation"
        )
        raise _refuse_repair(reason)

    event: RecoveryEvent
    action_taken: str
    detail: str

    event_recorded = False
    state_resolved = False
    with CatalogWriter(Path(catalog_path), lock_dir) as writer:
        # Exactly one authorized mutation. A mutation failure raises out of this block with
        # nothing recorded and nothing resolved — the exact write-ahead state stays blocked,
        # which is precisely the durable fail-closed evidence a restarted process needs.
        if action == "adopt-orphan":
            report = reconcile(writer.connection, tree, quarantine_partial=False)
            # Exactly one orphan exists (proven above), so the one adoption-path event this
            # reconcile pass produced is necessarily the requested target's — whether the
            # authoritative path adopted it verified or preserved it in quarantine unproven,
            # in which case the event names the quarantine destination rather than the origin.
            matching = [
                item for item in report.events if item.scenario == "object_without_catalog_row"
            ]
            if not matching:
                reason = (
                    "the accepted reconciliation primitive reported no adoption event for "
                    "the requested orphan; the write-ahead block stays blocked for owner "
                    "adjudication"
                )
                raise _refuse_repair(reason)
            event = matching[0]
            action_taken = event.action_taken
            detail = event.detail
        elif action == "quarantine-partial":
            quarantined = storage.raw_store.quarantine(
                tree.data_root / target,
                "RAW_PARTIAL_DOWNLOAD",
                "interrupted transfer quarantined by the explicit recovery applier",
            )
            action_taken = "quarantined"
            detail = (
                "the partial raw object was preserved in quarantine through the accepted "
                "move-and-preserve path; nothing was deleted"
            )
            event = RecoveryEvent(
                scenario="interrupted_part_download",
                action_taken=action_taken,
                detail=detail,
                relative_path=relative_to_root(quarantined, tree.data_root),
            )
        elif action == "remove-stale-part":
            (tree.data_root / target).unlink()
            action_taken = "removed_never_promoted_temporary"
            detail = (
                "the stale staging spool was removed as a never-promoted, never-catalogued, "
                "never-referenced temporary; no acquired object was touched"
            )
            event = RecoveryEvent(
                scenario="interrupted_part_download",
                action_taken=action_taken,
                detail=detail,
                relative_path=target,
            )
        else:  # rebuild-projection
            # The accepted rebuild primitive, deliberately without a run identity: the
            # projection-specific bulk resolver is never reused for the write-ahead state,
            # which is resolved exactly, by primary key, below (Decision 041 §14).
            rebuilt = rebuild_audit_projection(writer.connection, tree.audit / _PROJECTION_NAME)
            action_taken = "projection_rebuilt"
            detail = (
                f"the derived audit projection was atomically reconstructed from {rebuilt} "
                "authoritative catalog row(s) through the accepted rebuild primitive"
            )
            event = RecoveryEvent(
                scenario="audit_projection_interrupted",
                action_taken=action_taken,
                detail=detail,
                relative_path=_PROJECTION_NAME,
            )

        # The actual completed recovery event, then — only after it succeeds — the exact
        # resolution of the write-ahead state. Order is load-bearing: an event-recording
        # failure must leave the state blocked, never resolved.
        event_recorded = _record_repair_event(writer, event)
        if event_recorded:
            state_resolved = _resolve_write_ahead(
                writer, census_run_id, recovery_state_id, action_taken, detail
            )

    resolution_verified = False
    if state_resolved:
        resolution_verified = _verify_write_ahead_state(
            catalog_path, census_run_id, recovery_state_id, "resolved"
        )

    if not event_recorded:
        detail = (
            f"{detail}; the recovery event could not be recorded, so the exact write-ahead "
            "state remains blocked, the state is UNDETERMINED, and continuation is prohibited"
        )
    elif not state_resolved:
        detail = (
            f"{detail}; the write-ahead state could not be exactly resolved and remains "
            "blocked; the state is UNDETERMINED and continuation is prohibited"
        )
    elif not resolution_verified:
        detail = (
            f"{detail}; exact resolution committed but its fresh readback could not complete, "
            "so this invocation is UNDETERMINED and must not authorize continuation; a later "
            "process recomputes from durable catalog state"
        )

    return RecoveryActionResult(
        action=action,
        target=target,
        census_run_id=census_run_id,
        recovery_state_id=recovery_state_id,
        action_taken=action_taken,
        event_recorded=event_recorded,
        state_resolved=state_resolved,
        post_state_undetermined=not (event_recorded and state_resolved and resolution_verified),
        detail=detail,
    )


def _verify_write_ahead_state(
    catalog_path: Path,
    census_run_id: str,
    recovery_state_id: str,
    expected: str,
) -> bool:
    """Read the exact write-ahead row through a genuinely fresh read-only connection."""
    try:
        with read_only_catalog(Path(catalog_path)) as connection:
            row = connection.execute(
                "SELECT scenario, resolution_state FROM census_recovery_states "
                "WHERE census_run_id = ? AND recovery_state_id = ?",
                (census_run_id, recovery_state_id),
            ).fetchone()
    except (DisclosureDriftError, sqlite3.Error, OSError):
        return False
    return (
        row is not None
        and str(row["scenario"]) == _T2_4_STATE_SCENARIO
        and str(row["resolution_state"]) == expected
    )


def _record_repair_event(writer: CatalogWriter, event: RecoveryEvent) -> bool:
    """Record the one actual completed recovery event, reporting failure as ``False``.

    ``census_run_id=None`` deliberately: the accepted function then writes only the actual
    ``census_recovery_events`` row and creates no second recovery-state row. The write-ahead
    state opened before the mutation is the only state row, and it is resolved exactly, by
    primary key, afterwards (Decision 041 §8 steps 9–11).
    """
    try:
        return record_recovery_events(writer, (event,), census_run_id=None) == 1
    except (DisclosureDriftError, sqlite3.Error, OSError):
        return False


def _resolve_write_ahead(
    writer: CatalogWriter,
    census_run_id: str,
    recovery_state_id: str,
    action_taken: str,
    detail: str,
) -> bool:
    """Exactly resolve the write-ahead state, reporting failure as ``False``."""
    try:
        return resolve_recovery_state(
            writer,
            census_run_id=census_run_id,
            recovery_state_id=recovery_state_id,
            action_taken=action_taken,
            detail=detail,
        )
    except (DisclosureDriftError, sqlite3.Error, OSError):
        return False
