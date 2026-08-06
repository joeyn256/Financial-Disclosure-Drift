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
from disclosure_drift.m3.request_plan import (
    M3_2A_BOOTSTRAP_ROUTES,
    RequestPlan,
    request_plan_from_document,
)
from disclosure_drift.paths import DataTree, PathPolicyError
from disclosure_drift.sec.archive import ArchiveDefenceError, ArchiveMember, iter_members
from disclosure_drift.sec.http_client import ProhibitedRetrievalError, SecClient
from disclosure_drift.sec.index_plan import CoverageWindow, plan_index_instances
from disclosure_drift.sec.observation_catalog import ObservationRecorder
from disclosure_drift.sec.raw_store import LINEAGE_SUFFIX, RawStore
from disclosure_drift.sec.request_ceiling import (
    PhysicalAttemptCeiling,
    RequestCeilingExhaustedError,
)
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import (
    SourceSpec,
    filing_body_url_is_prohibited,
    require_registered,
)
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import applied_versions, integrity_report

__all__ = [
    "ACQUISITION_WINDOWS",
    "FINAL_MIGRATION_VERSION",
    "M3_2B_DEPENDENT_ROUTES",
    "OPERATIONAL_CATALOG_RELATIVE_PATH",
    "AcquisitionEngine",
    "AcquisitionError",
    "AcquisitionGateError",
    "CatalogPreparation",
    "CatalogPreparationError",
    "ContainmentError",
    "LiveOperationAuthorization",
    "LogicalRequest",
    "RecoveryObservation",
    "RequestOutcome",
    "StorageBinding",
    "StoragePreparationError",
    "WindowOutcome",
    "derive_logical_requests",
    "load_approved_plan",
    "observe_recovery_state",
    "prepare_operational_catalog",
    "prepare_storage",
    "resolve_within",
    "route_is_streamed",
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
        """Count of conditional requests confirming a preserved snapshot (§22 ``CACHE_HITS``)."""
        return sum(
            1
            for outcome in self.outcomes
            if outcome.disposition == "satisfied_reused" and outcome.satisfies_requirement
        )

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

    @staticmethod
    def _with_absence_reason(
        request: LogicalRequest,
        observation: SourceObservation,
    ) -> SourceObservation:
        """Attach the registered absence reason when a required index instance is left absent.

        The accepted response policy classifies a ``404`` on an archival path as absent evidence
        and deliberately attaches no reason code, because at that layer it is an ordinary outcome.
        At *this* layer it is a required object left absent, and T2 packet §10 item 1 makes the
        operational catalog the durable home of that fact. So the registered code is attached to
        the observation before it is committed, rather than only to the in-memory outcome — a
        reconciliation report read from the catalog alone must be able to see it.
        """
        if request.source_id != _INDEX_ROUTE:
            return observation
        if observation.outcome not in {"failed", "quarantined"}:
            return observation
        if _INDEX_ABSENT_REASON in observation.reason_codes:
            return observation
        return replace(
            observation,
            reason_codes=(*observation.reason_codes, _INDEX_ABSENT_REASON),
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
