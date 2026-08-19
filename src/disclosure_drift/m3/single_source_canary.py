"""The disposable single-source compact canary execution path (accepted Decision 116).

**The gap this closes.** Decision 113 measured the compact evidence contract on real prefixes
of the real first planned source and Decision 115 was to run the first real *whole-source*
canary against it. It stopped before creating a disposable world, because no supported path
existed that could run exactly one governed source under the accepted compact contract and be
relied on to stop: the reachable production driver
(:func:`~disclosure_drift.m3.offline_parse.run_offline_metadata_parse`) loads the whole plan,
traverses every planned source, defaults to full evidence, and wires no D112 §8 sidecar. This
module is that path.

**It is not E0, and it is not a second parser.** Every parse, identity, digest, and durable row
comes from the accepted modules: :mod:`~disclosure_drift.m3.offline_parse` for the one-source
entry point and the write footprint, :mod:`~disclosure_drift.m3.working_catalog` for the D111
run-local working catalog, :mod:`~disclosure_drift.m3.compact_evidence` for the
``e0-compact-evidence/2`` contract and its sidecar, and
:class:`~disclosure_drift.sec.census.CensusCatalog` for persistence. What this module adds is
the seam: select one governed source, build a disposable world, bind the compact contract
explicitly, run that source, stop, and report.

Four boundaries make it safe, and each is structural rather than promised:

* **Read-only authoritative inputs.** The accepted operational catalog is opened through
  ``SQLITE_OPEN_READONLY`` on every path here -- once to select the source, once for D111 to
  copy from, and once afterwards to re-measure its digest. Nothing in this module can write
  one of its bytes, and no writer lease is taken on it, so a stale lease is not even reachable.
* **Writable non-authoritative outputs only.** Every write lands in a disposable world beneath
  an operator-supplied work root that is refused unless it lies outside both the repository
  checkout and the private evidence root. The working catalog, its progress ledger, the compact
  sidecar, and the result document are the only artifacts produced, and none is promoted.
* **Exactly one source.** The only selector is ``census_plan_sources.source_instance_id``, and
  it resolves through the accepted plan or is refused. There is no path argument, no
  all-sources fallback, no loop, and no continuation: one invocation materializes one source
  and returns.
* **No E0 authority and no E0 namespace.** This module imports :mod:`disclosure_drift.m3.e0`
  nowhere, consults no activation constant, creates no run namespace under the private root,
  and applies no migration. A successful canary is not an authorization for anything.

**Nothing here authorizes running a real source.** Building the path is separate from being
told to use it; the next real execution needs its own owner instrument.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.config import EVIDENCE_ROOT_ENV
from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.capacity_plan import plan_fingerprint
from disclosure_drift.m3.compact_evidence import (
    COMPACT_EVIDENCE,
    COMPACT_EVIDENCE_CONTRACT,
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    CompactEvidenceSidecar,
)
from disclosure_drift.m3.evidence_paths import require_external_evidence_root
from disclosure_drift.m3.offline_parse import (
    AssociationTotality,
    SelectedPlannedSource,
    SingleSourceOutcome,
    materialize_census_associations,
    materialize_one_planned_source,
    select_planned_source,
    write_containment,
)
from disclosure_drift.m3.working_catalog import (
    WORKING_CATALOG_FILENAME,
    WorkingCatalog,
    file_digest,
)
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.census import CensusCatalog, ResolutionEvidence
from disclosure_drift.storage.catalog import CatalogWriter, strictly_read_only_connection
from disclosure_drift.storage.sqlite import applied_versions, utc_now

__all__ = [
    "CANARY_BATCH_SIZE",
    "CANARY_CONTRACT",
    "CANARY_RESULT_FILENAME",
    "CANARY_RESOLUTION_SCOPE",
    "OPERATIONAL_CATALOG_RELATIVE_PATH",
    "CanaryPreflight",
    "CanaryResult",
    "CanaryWorld",
    "SingleSourceCanaryError",
    "create_world",
    "preflight_single_source_canary",
    "require_canary_work_root",
    "require_disposable_work_root",
    "resolve_private_root",
    "run_single_source_canary",
    "validate_run_id",
]


class SingleSourceCanaryError(DisclosureDriftError):
    """A canary precondition failed. Never worked around, never retried in place."""


#: This path's own contract identity, recorded in every result document so a later reader can
#: tell exactly which shape produced it. It is deliberately **not** an evidence contract: the
#: evidence contract is ``e0-compact-evidence/2`` and this module only binds it.
CANARY_CONTRACT: Final = "m3.3-single-source-canary/1.0"

#: The accepted catalog, relative to the private evidence root.
#:
#: Restated rather than imported for the same reason ``m3/e0.py`` restates it from
#: ``m3/acquisition.py``: this module must not import the E0 driver, and the value is one
#: literal. The three copies are pinned equal by test rather than kept in step by comment.
OPERATIONAL_CATALOG_RELATIVE_PATH: Final = "catalogs/m3_2a_operational.sqlite3"

#: The create-once result document, written into the disposable world when a run completes.
CANARY_RESULT_FILENAME: Final = "canary_result.json"

#: Parts per real transaction, with write-ahead-log truncation at each boundary. This is the
#: configuration accepted **Decision 113 §14** measured the real densities under, so a canary
#: reproduces the measurement's own journal behaviour rather than inventing a second one.
CANARY_BATCH_SIZE: Final = 250

#: The scope one resolution pass is recorded under in the sidecar. A canary resolves the whole
#: working catalog exactly once, which is the same scope the accepted D113 §11 evidence uses.
CANARY_RESOLUTION_SCOPE: Final = "catalog"

#: A run identity is a short, lowercase, filesystem-safe slug. It names one disposable world and
#: is never reused: an identity that already has a world is refused rather than resumed.
_RUN_ID_PATTERN: Final = r"\A[a-z0-9][a-z0-9_-]{0,127}\Z"

_DIRECTORY_MODE: Final = 0o700
_FILE_MODE: Final = 0o600

#: Exit codes, matching the repository's operator convention.
_EXIT_OK: Final = 0
_EXIT_GATE_FAILURE: Final = 4


# --------------------------------------------------------------------------- #
# The private root, the work root, and the disposable world
# --------------------------------------------------------------------------- #
def resolve_private_root(
    repository_root: Path, *, environ: Mapping[str, str] | None = None
) -> Path:
    """Resolve the accepted private evidence root from the one recognized variable.

    Restated here rather than imported from the E0 module so this path carries no E0 import at
    all; the rule is the accepted external-root boundary either way, and the variable's name
    comes from :mod:`disclosure_drift.config` rather than from a second literal.

    The **value** is never returned to a renderer, written into a result document, or logged.
    Callers receive a path they open files with and report only names relative to a root.

    Raises:
        SingleSourceCanaryError: the variable is absent, blank, or not a lawful external root.
    """
    source = os.environ if environ is None else environ
    raw = source.get(EVIDENCE_ROOT_ENV)
    if raw is None or not raw.strip():
        message = (
            f"{EVIDENCE_ROOT_ENV} is not set; this command reads the accepted private root "
            "from that variable alone and has no default, no fallback, and no path option"
        )
        raise SingleSourceCanaryError(message)
    try:
        return require_external_evidence_root(raw, repository_root)
    except (ValueError, OSError) as exc:
        # The boundary's own messages never name either resolved path, so quoting the
        # exception text here cannot leak one.
        message = f"{EVIDENCE_ROOT_ENV} is not a lawful external evidence root: {exc}"
        raise SingleSourceCanaryError(message) from exc


def _comparable(path: Path) -> tuple[str, ...]:
    """Case-folded resolved components, so an alias or a case variant cannot launder a path."""
    return tuple(part.casefold() for part in Path(os.path.realpath(path)).parts)


def _within(ancestor: tuple[str, ...], descendant: tuple[str, ...]) -> bool:
    return len(descendant) > len(ancestor) and descendant[: len(ancestor)] == ancestor


def require_disposable_work_root(
    work_root: str | Path, repository_root: Path, private_root: Path
) -> Path:
    """Return the resolved work root a disposable world may be built under, or refuse.

    Two rules, both fail-closed and both stated on resolved, case-folded paths so a symlink or
    a case variant cannot launder containment:

    * the root must be **outside the repository checkout**, which is the accepted external-root
      boundary, reused rather than restated;
    * the root must be **outside the private evidence root**, and must not contain it. Accepted
      Decision 116 §7 puts every writable canary output outside the authoritative evidence
      tree, so a world beneath it -- or a work root that swallowed it -- is refused before
      anything is created.

    No message names either resolved path.

    Raises:
        SingleSourceCanaryError: the work root is not a lawful disposable location.
    """
    try:
        resolved = require_external_evidence_root(work_root, repository_root)
    except (ValueError, OSError) as exc:
        message = f"the canary work root is not a lawful external directory: {exc}"
        raise SingleSourceCanaryError(message) from exc
    work_parts = _comparable(resolved)
    private_parts = _comparable(private_root)
    if work_parts == private_parts or _within(private_parts, work_parts):
        message = (
            "the canary work root is the private evidence root or lies inside it; every "
            "writable canary output stays outside the authoritative evidence tree"
        )
        raise SingleSourceCanaryError(message)
    if _within(work_parts, private_parts):
        message = (
            "the canary work root contains the private evidence root; the authoritative "
            "evidence tree must not lie inside a disposable work tree"
        )
        raise SingleSourceCanaryError(message)
    return resolved


def _package_repository_root() -> Path:
    """The repository checkout this package is installed from.

    Derived from this module's own location rather than accepted as an argument, so a direct
    library caller cannot declare a decoy checkout and have a disposable world created inside
    the real one. It is the rule the operator surface already uses, one directory deeper
    because this module sits under ``m3``.
    """
    return Path(__file__).resolve().parents[3]


def _authoritative_private_root(repository_root: Path) -> Path | None:
    """The private evidence root this **process** declares, or ``None`` when it declares none.

    Read from the real process environment rather than from any argument, so the containment
    rule below cannot be declared away by the caller it constrains. When the variable is unset
    there is no authoritative evidence tree in this process for a work root to be inside of,
    and the rule has nothing to say; when it is set it must be lawful, exactly as it must be
    for every other surface that resolves it.
    """
    if not os.environ.get(EVIDENCE_ROOT_ENV, "").strip():
        return None
    return resolve_private_root(repository_root)


def require_canary_work_root(work_root: str | Path, *, tree: DataTree) -> Path:
    """Enforce the disposable work-root invariant at the **library** execution boundary.

    Accepted Decision 116 §7 puts every writable canary output outside the repository checkout
    and outside the authoritative evidence tree. That invariant belongs to the *run*, not to
    the operator surface: a direct library caller must not be able to reach a location the
    operator surface would have refused, so the run establishes it itself rather than trusting
    that whoever called it already did.

    One rule, not two. :func:`require_disposable_work_root` is the accepted primitive and stays
    the only place the rule is stated; this function applies it to each evidence root a run must
    stay clear of:

    * ``tree.data_root`` -- the evidence tree this very run reads its frozen artifacts from.
      Taken from the run's own input rather than declared beside it, so it cannot disagree with
      what the run actually opens;
    * the authoritative private evidence root the process declares, whenever it declares one.
      In ordinary operation these are the same root, because the operator surface builds the
      tree from it; they differ only for a caller reading a stand-in tree, and that caller is
      still held to the authoritative one.

    The repository checkout, absoluteness, and symlink resolution come from the same primitive
    and are derived rather than declared, so none of them is a caller's to soften.

    Returns:
        The resolved work root. Validating an already-validated root returns it unchanged, so
        the operator surface's early refusal and this one cannot disagree about a lawful root.

    Raises:
        SingleSourceCanaryError: the work root is not a lawful disposable location.
    """
    repository_root = _package_repository_root()
    resolved = require_disposable_work_root(work_root, repository_root, tree.data_root)
    authoritative = _authoritative_private_root(repository_root)
    if authoritative is not None:
        require_disposable_work_root(work_root, repository_root, authoritative)
    return resolved


def validate_run_id(run_id: str) -> str:
    """Return ``run_id`` if it is a lawful world name, else refuse.

    The identity becomes a directory name under the operator's work root, so it is validated
    rather than trusted: an absolute path, a parent reference, or a separator would place a
    disposable world somewhere the work-root boundary never approved.
    """
    if not re.fullmatch(_RUN_ID_PATTERN, run_id):
        message = (
            f"canary run identity {run_id!r} is not of the accepted shape; an identity is "
            "1-128 characters of lowercase letters, digits, underscore, and hyphen, "
            "starting alphanumeric"
        )
        raise SingleSourceCanaryError(message)
    return run_id


@dataclass(frozen=True, slots=True)
class CanaryWorld:
    """One disposable world: where a canary's writable outputs live, and nothing else.

    Every path here is beneath :attr:`directory`, which is beneath the operator's work root.
    None of them is under the private evidence root, and none is ever promoted.
    """

    run_id: str
    directory: Path

    @property
    def working_catalog(self) -> Path:
        """The D111 run-local working catalog."""
        return self.directory / WORKING_CATALOG_FILENAME

    @property
    def sidecar(self) -> Path:
        """The D112 §8 compact-evidence sidecar."""
        return self.directory / COMPACT_EVIDENCE_SIDECAR_FILENAME

    @property
    def result(self) -> Path:
        """The create-once result document."""
        return self.directory / CANARY_RESULT_FILENAME


def create_world(work_root: Path, run_id: str) -> CanaryWorld:
    """Create one disposable world exactly once, at mode ``0700``.

    ``mkdir`` without ``exist_ok`` is the create-once primitive: it is atomic, so two callers
    cannot both believe they created the world, and an identity whose world already exists is
    refused rather than resumed, repaired, or overwritten. A symlink at either the work root or
    the world path is refused before anything is created.

    Raises:
        SingleSourceCanaryError: the identity is unlawful, or its world already exists.
    """
    validate_run_id(run_id)
    if work_root.is_symlink():
        message = "the canary work root is a symbolic link and is refused"
        raise SingleSourceCanaryError(message)
    if not work_root.exists():
        work_root.mkdir(mode=_DIRECTORY_MODE, parents=True)
    if not work_root.is_dir():
        message = "the canary work root exists and is not a directory"
        raise SingleSourceCanaryError(message)
    target = work_root / run_id
    if target.is_symlink():
        message = f"canary world {run_id!r} exists as a symbolic link and is refused"
        raise SingleSourceCanaryError(message)
    if target.exists():
        message = (
            f"canary world {run_id!r} already exists; a disposable world is create-once and "
            "is never reused, resumed, repaired, or overwritten"
        )
        raise SingleSourceCanaryError(message)
    target.mkdir(mode=_DIRECTORY_MODE)
    target.chmod(_DIRECTORY_MODE)
    return CanaryWorld(run_id=run_id, directory=target)


def _write_once(path: Path, payload: bytes) -> None:
    """Create ``path`` with ``O_EXCL`` at mode ``0600`` and write it.

    ``O_CREAT | O_EXCL`` makes this write-once at the operating system rather than by a prior
    existence check, so completed run-local evidence has no window in which it could be
    silently replaced.
    """
    if path.exists() or path.is_symlink():
        message = f"{path.name} already exists; completed run-local evidence is never overwritten"
        raise SingleSourceCanaryError(message)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, _FILE_MODE)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    path.chmod(_FILE_MODE)


# --------------------------------------------------------------------------- #
# Preflight
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CanaryPreflight:
    """What a read-only canary preflight established. It creates nothing.

    Every field is measured from the world rather than asserted, and the accepted catalog is
    read through a strictly read-only handle, so running a preflight leaves it byte-identical.
    """

    run_id: str
    source_instance_id: str
    source_id: str
    plan_position: int
    plan_source_count: int
    plan_fingerprint: str
    observation_id: str | None
    retrieval_state: str
    snapshot_state: str
    parser_state: str
    migration_head: int
    operational_catalog_sha256: str
    operational_catalog_byte_length: int
    work_root_free_bytes: int
    world_absent: bool

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "contract": CANARY_CONTRACT,
            "evidence_contract": COMPACT_EVIDENCE_CONTRACT,
            "run_id": self.run_id,
            "source_instance_id": self.source_instance_id,
            "source_id": self.source_id,
            "plan_position": self.plan_position,
            "plan_source_count": self.plan_source_count,
            "plan_fingerprint": self.plan_fingerprint,
            "observation_id": self.observation_id,
            "retrieval_state": self.retrieval_state,
            "snapshot_state": self.snapshot_state,
            "parser_state": self.parser_state,
            "migration_head": self.migration_head,
            "operational_catalog_sha256": self.operational_catalog_sha256,
            "operational_catalog_byte_length": self.operational_catalog_byte_length,
            "work_root_free_bytes": self.work_root_free_bytes,
            "world_absent": self.world_absent,
        }


def preflight_single_source_canary(
    *,
    operational_catalog: Path,
    work_root: Path,
    run_id: str,
    source_instance_id: str,
) -> CanaryPreflight:
    """Validate every predicate a run needs, read-only, and create nothing.

    Raises:
        SingleSourceCanaryError: a predicate the run depends on does not hold.
        OfflineParseError: the identifier names no planned source, or names more than one.
    """
    validate_run_id(run_id)
    if not operational_catalog.is_file():
        message = "the accepted operational catalog does not exist at its fixed relative path"
        raise SingleSourceCanaryError(message)
    with strictly_read_only_connection(operational_catalog) as connection:
        selected = select_planned_source(connection, source_instance_id)
        fingerprint, _ = plan_fingerprint(connection)
        applied = applied_versions(connection)
    if not applied:
        message = "the accepted operational catalog records no applied migration"
        raise SingleSourceCanaryError(message)
    digest, byte_length = file_digest(operational_catalog)
    source = selected.source
    return CanaryPreflight(
        run_id=run_id,
        source_instance_id=source.source_instance_id,
        source_id=source.source_id,
        plan_position=selected.plan_position,
        plan_source_count=selected.plan_source_count,
        plan_fingerprint=fingerprint,
        observation_id=source.observation_id,
        retrieval_state=source.retrieval_state,
        snapshot_state=source.snapshot_state,
        parser_state=source.parser_state,
        migration_head=max(applied),
        operational_catalog_sha256=digest,
        operational_catalog_byte_length=byte_length,
        work_root_free_bytes=shutil.disk_usage(_measurable(work_root)).free,
        world_absent=not (work_root / run_id).exists(),
    )


def _measurable(path: Path) -> Path:
    """The nearest existing ancestor of ``path``, so free space can be measured before mkdir."""
    candidate = path
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #
class _WorkingCatalogWriter(CatalogWriter):
    """The accepted writer type, bound to a working catalog's already-open connection.

    The D111 working catalog owns its file and its connection: it creates the copy, opens
    exactly one writing handle on it, and closes that handle when its context ends. Taking a
    second :class:`CatalogWriter` lease on the same file would open a second writing handle
    for a serialization guarantee the single owner already provides.

    So this binds the accepted type to the connection D111 already holds. It acquires no
    lease, opens nothing, and closes nothing -- :class:`~disclosure_drift.sec.census.CensusCatalog`
    reads ``connection`` and nothing else, and the file it reads is a disposable run-local
    copy rather than the accepted catalog.
    """

    def __init__(self, working: WorkingCatalog) -> None:
        super().__init__(working.path, working.path.parent)
        self._connection = working.connection


@dataclass(frozen=True, slots=True)
class CanaryResult:
    """Everything one disposable single-source run established.

    Wide on purpose: accepted Decision 116 §9 fixes what a later execution report must be able
    to determine from one invocation, and a field that had to be recovered by re-opening the
    working catalog would be a field the report could get wrong. Every count is read from
    durable rows, every digest comes from the accepted compact-evidence contract, and every
    measurement is taken from the filesystem -- none is estimated here.
    """

    contract: str
    evidence_contract: str
    run_id: str
    started_at_utc: str
    completed_at_utc: str

    # -- the one source -------------------------------------------------- #
    source_instance_id: str
    source_id: str
    plan_position: int
    plan_source_count: int
    plan_fingerprint: str
    source_observation_id: str | None
    source_artifact_sha256: str
    source_artifact_byte_length: int
    disposition: str
    parser_state_before: str
    parser_state_after: str
    parser_run_id: str | None

    # -- what the traversal produced ------------------------------------- #
    members: int
    projection_records: int
    parsed_records: int
    quarantined_records: int
    omitted_field_observations: int
    materialized_field_observations: int

    # -- what the working catalog holds ---------------------------------- #
    canonical_accession_count: int
    registrant_count: int
    substantive_relation_count: int
    quarantined_record_count: int
    structural_observation_count: int
    accession_observation_count: int
    field_resolution_row_count: int
    cohort_resolution_row_count: int
    association_totality: Mapping[str, int]

    # -- resolution and corroboration ------------------------------------ #
    resolution_accessions: int
    implicit_resolutions: int
    explicit_resolutions: int
    omitted_field_rows: int
    materialized_field_rows: int
    omitted_cohort_rows: int
    materialized_cohort_rows: int
    index_rows: int
    corroborating_rows: int
    corroboration_exceptions: int
    unbound_accessions: int
    omitted_corroboration_observations: int

    # -- the accepted identities ----------------------------------------- #
    member_manifest_digest: str
    projection_digest: str
    resolution_digest: str
    corroboration_digest: str
    compact_evidence_identity: str

    # -- the disposable world -------------------------------------------- #
    world_relative_working_catalog: str
    world_relative_sidecar: str
    working_catalog_sha256: str
    working_catalog_byte_length: int
    #: The write-ahead log remaining **after** the run's final checkpoint, which is evidence
    #: that the log was reclaimed rather than a peak. Sampling the peak means watching the file
    #: during the run, which D116 §9 leaves to the outer operator rather than inventing here.
    working_catalog_wal_byte_length: int
    working_catalog_source_sha256: str
    migration_head: int

    # -- the accepted catalog, before and after -------------------------- #
    operational_catalog_sha256_before: str
    operational_catalog_sha256_after: str
    work_root_free_bytes_before: int
    work_root_free_bytes_after: int

    @property
    def operational_catalog_unchanged(self) -> bool:
        """Whether the accepted catalog is byte-identical to what the run started from."""
        return self.operational_catalog_sha256_before == self.operational_catalog_sha256_after

    def identities(self) -> Mapping[str, str]:
        """The five accepted identities, alone. Deterministic over one frozen artifact."""
        return {
            "member_manifest_digest": self.member_manifest_digest,
            "projection_digest": self.projection_digest,
            "resolution_digest": self.resolution_digest,
            "corroboration_digest": self.corroboration_digest,
            "compact_evidence_identity": self.compact_evidence_identity,
        }

    def as_record(self) -> Mapping[str, object]:
        """The complete result as a plain mapping, carrying no absolute path.

        The two world artifacts are named **relative to the disposable world**, so a result
        document can be read, quoted, or moved without disclosing where the world was built.
        """
        record: dict[str, object] = {}
        for name in self.__slots__:
            record[name] = getattr(self, name)
        record["operational_catalog_unchanged"] = self.operational_catalog_unchanged
        return record


def _counts(connection: sqlite3.Connection) -> Mapping[str, int]:
    """Row counts for the tables a result reports, read from the working catalog."""
    tables = {
        "canonical_accession_count": "census_accessions",
        "registrant_count": "census_registrants",
        "quarantined_record_count": "census_quarantined_records",
        "structural_observation_count": "census_structural_observations",
        "accession_observation_count": "census_accession_observations",
        "field_resolution_row_count": "census_accession_field_resolutions",
        "cohort_resolution_row_count": "census_accession_cohort_resolutions",
    }
    counted = {
        key: int(
            connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]  # noqa: S608
        )
        for key, table in tables.items()
    }
    counted["substantive_relation_count"] = int(
        connection.execute(
            "SELECT COUNT(*) AS n FROM census_accession_registrants "
            "WHERE association_class = 'substantive'"
        ).fetchone()["n"]
    )
    return counted


def run_single_source_canary(
    *,
    operational_catalog: Path,
    tree: DataTree,
    work_root: Path,
    run_id: str,
    source_instance_id: str,
    batch_size: int = CANARY_BATCH_SIZE,
) -> CanaryResult:
    """Run **exactly one** governed planned source into a disposable world, and stop.

    The whole path, in order:

    0. establish the write boundary: refuse any work root that is not a lawful disposable
       location, before a directory, a catalog, or a result document exists to refuse it for;
    1. select the one source from the accepted plan, through a strictly read-only handle;
    2. create the disposable world, once, refusing an identity that already has one;
    3. copy the accepted catalog into a D111 run-local working catalog, read-only on the source;
    4. open the D112 §8 sidecar and bind
       :data:`~disclosure_drift.m3.compact_evidence.COMPACT_EVIDENCE` **explicitly**, so the
       full-observation default cannot be reached by omission;
    5. inside the accepted **R17** write containment, materialize that one source, resolve the
       working catalog once, and run the Decision 094 §6.4 association projection;
    6. record the D113 §§8-9 resolution and corroboration evidence into the sidecar;
    7. measure the world and re-measure the accepted catalog;
    8. write the create-once result document.

    There is no step 9. Nothing enumerates a second source, and the return is the end of the
    run rather than the end of an iteration.

    Args:
        operational_catalog: The accepted catalog. Opened strictly read-only, always.
        tree: The data tree the frozen source artifacts are read from.
        work_root: The disposable work root. Validated **here**, by
            :func:`require_canary_work_root`, before any world exists -- a caller's own prior
            validation is welcome and is never what this run relies on.
        run_id: This world's identity. Create-once.
        source_instance_id: The one planned source's own plan key.
        batch_size: Parts per real transaction, defaulting to the accepted D113 §14 value.

    Raises:
        SingleSourceCanaryError: a canary precondition failed.
        OfflineParseError: any accepted fail-closed parse condition, unchanged.
        WorkingCatalogError: the disposable working catalog could not be built safely.
    """
    # 0. The write boundary, established before anything is measured, opened, or created.
    #    Accepted Decision 116 §7 is the run's own invariant, so an unlawful work root fails
    #    closed here rather than at whichever caller happened to check.
    resolved_work_root = require_canary_work_root(work_root, tree=tree)
    started = utc_now()
    if not operational_catalog.is_file():
        message = "the accepted operational catalog does not exist at its fixed relative path"
        raise SingleSourceCanaryError(message)
    catalog_before, _ = file_digest(operational_catalog)
    free_before = shutil.disk_usage(_measurable(resolved_work_root)).free

    # 1. The one source, and the plan it came from. Strictly read-only: this handle cannot
    #    write, and it is closed before the working copy is taken.
    with strictly_read_only_connection(operational_catalog) as reader:
        selected = select_planned_source(reader, source_instance_id)
        fingerprint, _ = plan_fingerprint(reader)

    # 2. The disposable world. Create-once, and never under the private evidence root.
    world = create_world(resolved_work_root, run_id)

    # 3-7. Everything writable, inside the world.
    with WorkingCatalog(operational_catalog, world.directory) as working:
        sidecar = CompactEvidenceSidecar(world.sidecar)
        try:
            materialized = _materialize(
                working=working,
                tree=tree,
                selected=selected,
                sidecar=sidecar,
                batch_size=batch_size,
            )
            identities = _record_evidence(sidecar=sidecar, materialized=materialized)
            working.checkpoint()
            wal_bytes = working.wal_byte_length()
            source_sha256 = working.identity.source_file_sha256
            migration_head = working.identity.migration_head
        finally:
            sidecar.close()
    # Measured together, after the context closed the last handle, so the reported digest and
    # the reported length describe the same bytes rather than two moments.
    working_sha256, working_bytes = file_digest(world.working_catalog)

    catalog_after, _ = file_digest(operational_catalog)
    result = _result(
        world=world,
        started=started,
        selected=selected,
        fingerprint=fingerprint,
        materialized=materialized,
        identities=identities,
        working_sha256=working_sha256,
        working_bytes=working_bytes,
        wal_bytes=wal_bytes,
        source_sha256=source_sha256,
        migration_head=migration_head,
        catalog_before=catalog_before,
        catalog_after=catalog_after,
        free_before=free_before,
        free_after=shutil.disk_usage(world.directory).free,
    )
    # 8. Create-once. A second run that somehow reached this world would fail here rather
    #    than replace the evidence the first one wrote.
    _write_once(world.result, json.dumps(result.as_record(), indent=2, sort_keys=True).encode())
    return result


@dataclass(frozen=True, slots=True)
class _Materialized:
    """The one source's parse, the projection it produced, and the counts left behind."""

    outcome: SingleSourceOutcome
    totality: AssociationTotality
    counts: Mapping[str, int]
    resolution: ResolutionEvidence


def _materialize(
    *,
    working: WorkingCatalog,
    tree: DataTree,
    selected: SelectedPlannedSource,
    sidecar: CompactEvidenceSidecar,
    batch_size: int,
) -> _Materialized:
    """Parse one source, resolve, and project -- all inside the accepted write containment.

    The catalog is constructed with :data:`COMPACT_EVIDENCE` **here**, explicitly, and is the
    only ``CensusCatalog`` this path builds. That is what accepted Decision 116 §5 item 7 asks
    for: the compact contract is bound by the caller rather than inherited, so the
    full-observation default is unreachable by omission rather than merely unlikely.

    The run-local progress ledger records the D111 states truthfully around the parse: the
    source is ``in_progress`` before its first durable row, ``parsed`` once every row it implies
    is durable, and ``disposed`` only once the accepted terminal is known.
    """
    writer = _WorkingCatalogWriter(working)
    connection = working.connection
    catalog = CensusCatalog(writer, compact_evidence=COMPACT_EVIDENCE)
    source = selected.source
    with write_containment(connection):
        working.ledger.begin_source(source.source_instance_id, source.source_id)
        outcome = materialize_one_planned_source(
            writer=writer,
            tree=tree,
            catalog=catalog,
            selected=selected,
            sidecar=sidecar,
            batch_size=batch_size,
            checkpoint_batches=True,
        )
        working.ledger.mark_parsed(
            source.source_instance_id,
            parts=outcome.members,
            batches=outcome.outcome.parsed_records,
        )
        # Decision 094 §6.4 order, unchanged: every persisted accession is resolved first,
        # because §6.2 item 5 reads the resolver's own output, and only then is the canonical
        # association relation projected.
        catalog.count_persisted_accession_resolutions(
            batch_size=batch_size, checkpoint_batches=True
        )
        totality = materialize_census_associations(connection, compact_evidence=True)
        counts = _counts(connection)
    working.ledger.mark_disposed(
        source.source_instance_id,
        outcome.outcome.disposition,
        detail=outcome.outcome.parser_state_after,
    )
    return _Materialized(
        outcome=outcome,
        totality=totality,
        counts=counts,
        resolution=catalog.resolution_evidence,
    )


def _record_evidence(
    *, sidecar: CompactEvidenceSidecar, materialized: _Materialized
) -> Mapping[str, str]:
    """Write the D113 §§8-9 evidence into the sidecar and return the five accepted identities.

    The resolution evidence is read off the catalog's accumulated
    :class:`~disclosure_drift.sec.census.ResolutionEvidence`, which is built under both evidence
    contracts because its digest is over the **logical** resolution set. Corroboration evidence
    exists only for a ``company.idx`` quarter; for any other source there is nothing to
    corroborate, so the digest is truthfully empty rather than fabricated.
    """
    resolution = materialized.resolution
    sidecar.record_resolution(
        resolution_scope=CANARY_RESOLUTION_SCOPE,
        accessions=resolution.accessions,
        implicit_resolutions=resolution.implicit,
        explicit_resolutions=resolution.explicit,
        omitted_field_rows=resolution.omitted_field_rows,
        materialized_field_rows=resolution.materialized_field_rows,
        omitted_cohort_rows=resolution.omitted_cohort_rows,
        materialized_cohort_rows=resolution.materialized_cohort_rows,
        completeness_digest=resolution.completeness_digest(),
    )
    outcome = materialized.outcome
    corroboration = outcome.corroboration
    observation = outcome.observation
    if corroboration is not None and observation is not None:
        sidecar.record_corroboration(
            source_observation_id=observation.observation_id,
            source_id=observation.source_id,
            artifact_sha256=observation.logical_sha256 or "",
            index_rows=corroboration.index_rows,
            corroborating=corroboration.corroborating,
            exceptions=corroboration.exceptions,
            unbound=len(corroboration.unbound),
            omitted_observations=corroboration.omitted_observations,
            materialized_observations=corroboration.written,
            corroboration_digest=corroboration.digest,
        )
    manifest = (
        "" if observation is None else sidecar.member_manifest_digest(observation.observation_id)
    )
    return {
        "member_manifest_digest": manifest,
        "projection_digest": outcome.completeness_digest,
        "resolution_digest": resolution.completeness_digest(),
        "corroboration_digest": "" if corroboration is None else corroboration.digest,
        "compact_evidence_identity": sidecar.identity(),
    }


def _result(
    *,
    world: CanaryWorld,
    started: str,
    selected: SelectedPlannedSource,
    fingerprint: str,
    materialized: _Materialized,
    identities: Mapping[str, str],
    working_sha256: str,
    working_bytes: int,
    wal_bytes: int,
    source_sha256: str,
    migration_head: int,
    catalog_before: str,
    catalog_after: str,
    free_before: int,
    free_after: int,
) -> CanaryResult:
    """Assemble the accepted Decision 116 §9 result surface from measured values only."""
    outcome = materialized.outcome
    observation = outcome.observation
    corroboration = materialized.outcome.corroboration
    resolution = materialized.resolution
    return CanaryResult(
        contract=CANARY_CONTRACT,
        evidence_contract=COMPACT_EVIDENCE_CONTRACT,
        run_id=world.run_id,
        started_at_utc=started,
        completed_at_utc=utc_now(),
        source_instance_id=selected.source.source_instance_id,
        source_id=selected.source.source_id,
        plan_position=selected.plan_position,
        plan_source_count=selected.plan_source_count,
        plan_fingerprint=fingerprint,
        source_observation_id=None if observation is None else observation.observation_id,
        source_artifact_sha256="" if observation is None else (observation.logical_sha256 or ""),
        source_artifact_byte_length=(
            0 if observation is None else int(observation.content_size_bytes or 0)
        ),
        disposition=outcome.outcome.disposition,
        parser_state_before=outcome.outcome.parser_state_before,
        parser_state_after=outcome.outcome.parser_state_after,
        parser_run_id=outcome.outcome.parser_run_id,
        members=outcome.members,
        projection_records=outcome.records,
        parsed_records=outcome.outcome.parsed_records,
        quarantined_records=outcome.outcome.quarantined_records,
        omitted_field_observations=outcome.omitted_field_observations,
        materialized_field_observations=outcome.materialized_field_observations,
        canonical_accession_count=materialized.counts["canonical_accession_count"],
        registrant_count=materialized.counts["registrant_count"],
        substantive_relation_count=materialized.counts["substantive_relation_count"],
        quarantined_record_count=materialized.counts["quarantined_record_count"],
        structural_observation_count=materialized.counts["structural_observation_count"],
        accession_observation_count=materialized.counts["accession_observation_count"],
        field_resolution_row_count=materialized.counts["field_resolution_row_count"],
        cohort_resolution_row_count=materialized.counts["cohort_resolution_row_count"],
        association_totality=materialized.totality.as_record(),
        resolution_accessions=resolution.accessions,
        implicit_resolutions=resolution.implicit,
        explicit_resolutions=resolution.explicit,
        omitted_field_rows=resolution.omitted_field_rows,
        materialized_field_rows=resolution.materialized_field_rows,
        omitted_cohort_rows=resolution.omitted_cohort_rows,
        materialized_cohort_rows=resolution.materialized_cohort_rows,
        index_rows=0 if corroboration is None else corroboration.index_rows,
        corroborating_rows=0 if corroboration is None else corroboration.corroborating,
        corroboration_exceptions=0 if corroboration is None else corroboration.exceptions,
        unbound_accessions=0 if corroboration is None else len(corroboration.unbound),
        omitted_corroboration_observations=(
            0 if corroboration is None else corroboration.omitted_observations
        ),
        member_manifest_digest=identities["member_manifest_digest"],
        projection_digest=identities["projection_digest"],
        resolution_digest=identities["resolution_digest"],
        corroboration_digest=identities["corroboration_digest"],
        compact_evidence_identity=identities["compact_evidence_identity"],
        world_relative_working_catalog=WORKING_CATALOG_FILENAME,
        world_relative_sidecar=COMPACT_EVIDENCE_SIDECAR_FILENAME,
        working_catalog_sha256=working_sha256,
        working_catalog_byte_length=working_bytes,
        working_catalog_wal_byte_length=wal_bytes,
        working_catalog_source_sha256=source_sha256,
        migration_head=migration_head,
        operational_catalog_sha256_before=catalog_before,
        operational_catalog_sha256_after=catalog_after,
        work_root_free_bytes_before=free_before,
        work_root_free_bytes_after=free_after,
    )


# --------------------------------------------------------------------------- #
# The operator surface
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CanaryOperatorResult:
    """One rendered operator outcome: an exit code and the lines to print.

    Deliberately its own small type rather than the E0 operator result: this path shares no
    authority, no namespace, and no terminal schema with E0, and reusing E0's rendering type
    would be the first thread of exactly the coupling accepted Decision 116 §5 item 13 forbids.
    """

    exit_code: int
    lines: tuple[str, ...]


def run_canary_source_command(
    *,
    mode: str,
    run_id: str,
    source_instance_id: str,
    work_root: str,
    repository_root: Path,
    environ: Mapping[str, str] | None = None,
) -> CanaryOperatorResult:
    """Run one ``m3 canary-source`` invocation and render it.

    Routing, boundary resolution, and rendering only. Every predicate, identity, and durable
    write lives above, so the operator surface cannot become a second place where a canary is
    judged runnable.

    The work root is refused here early, so an operator learns immediately and without a
    stack trace, and it is refused again by :func:`run_single_source_canary` itself. That is
    deliberate redundancy through **one** primitive rather than two rules: this refusal is a
    convenience, and the run's own is the invariant.

    No line this returns carries the private root, the work root, or any absolute path: the
    result is rendered from counts, digests, enum tokens, and world-relative names.
    """
    private_root = resolve_private_root(repository_root, environ=environ)
    operational_catalog = private_root / OPERATIONAL_CATALOG_RELATIVE_PATH
    resolved_work_root = require_disposable_work_root(work_root, repository_root, private_root)
    if mode == "preflight":
        report = preflight_single_source_canary(
            operational_catalog=operational_catalog,
            work_root=resolved_work_root,
            run_id=run_id,
            source_instance_id=source_instance_id,
        )
        return CanaryOperatorResult(
            exit_code=_EXIT_OK if report.world_absent else _EXIT_GATE_FAILURE,
            lines=_render(report.as_record(), title="canary-source preflight"),
        )
    if mode != "run":
        message = f"unknown canary mode {mode!r}; the modes are 'preflight' and 'run'"
        raise SingleSourceCanaryError(message)
    result = run_single_source_canary(
        operational_catalog=operational_catalog,
        tree=DataTree.from_root(private_root),
        work_root=resolved_work_root,
        run_id=run_id,
        source_instance_id=source_instance_id,
    )
    return CanaryOperatorResult(
        exit_code=_EXIT_OK if result.operational_catalog_unchanged else _EXIT_GATE_FAILURE,
        lines=_render(result.as_record(), title="canary-source run"),
    )


def _render(record: Mapping[str, object], *, title: str) -> tuple[str, ...]:
    """Render one result mapping as aligned ``key  value`` lines, in key order."""
    width = max(len(key) for key in record)
    body = (f"{key:<{width}}  {json.dumps(record[key], sort_keys=True)}" for key in sorted(record))
    return (title, *body)
