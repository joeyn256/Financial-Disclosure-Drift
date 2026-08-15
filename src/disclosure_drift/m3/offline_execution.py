"""Workstream I7 — the offline execution driver over the accepted downstream machinery.

Everything below **calls** the accepted S4/S5/S6 modules and reimplements none of them.
The joint selector, the selection store, the reserve selector, the seal, the manifest
builder, and the manifest verifier are used exactly as accepted (M3.3 contract §5, §20:
*reused, never edited*); this module is the seam that drives them in one governed order
and proves the properties the contract requires of that order:

1. load the frozen candidates through the accepted Decision 019 §S5.2 mapping;
2. build the accepted joint-selector input and run the **single** accepted selector;
3. verify the 2009/2010 pair rule against the **joint result** (Decision 071 IN-3);
4. persist through the accepted store, inside its own single ``running`` window;
5. reconstruct independently through the accepted entry point and compare;
6. replay **write-free** to the **R3** standard — durable-byte equality, strictly
   read-only handles, no writer lease;
7. seal ``selection_result_sha256`` in its own prior transaction;
8. build, verify, and replay the manifest, keeping the seal/manifest boundary intact.

**Running this against the accepted real private catalog is M3.3-E1/E2, separate owner
gates.** Nothing here supplies one: no return value, token, or successful run is an
authorization, and the module reads no configuration that could grant itself one.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.m3.support_target_pairs import (
    PRE_STUDY_SUPPORT_REASON_CODE,
    REQUIRED_SUPPORT_TARGET_PAIR_ENTITIES,
    PairedAccession,
    paired_accessions_from_rows,
    support_target_pair_entities,
)
from disclosure_drift.paths import DataTree
from disclosure_drift.release.pilot_manifest import ExplicitArguments
from disclosure_drift.sec.accession_selection_store import (
    JointSelectionRunIdentity,
    PersistedJointSelectionResult,
    build_joint_selection_run_identity,
    execute_and_persist_joint_selection,
    load_frozen_joint_candidates,
    reconstruct_persisted_joint_selection,
)
from disclosure_drift.sec.pilot_manifest_store import (
    PersistedPilotManifest,
    build_and_persist_pilot_manifest,
    seal_selection_result,
    verify_pilot_manifest,
)
from disclosure_drift.storage.catalog import CatalogWriter, strictly_read_only_connection

__all__ = [
    "OFFLINE_EXECUTION_MODE",
    "cohort_definition_digest",
    "offline_execution_policy_versions",
    "ExecutionInputs",
    "ManifestOutcome",
    "PairVerification",
    "ReplayProof",
    "SelectionOutcome",
    "build_and_verify_manifest",
    "durable_digest",
    "execute_selection",
    "render_command_invocation",
    "replay_selection_write_free",
    "seal_and_replay_manifest",
    "verify_support_target_pairs",
]

#: The receipt ``invocation_mode`` every M3.3 offline execution command reports
#: (contract §6 item 5). Network counts are always zero under it.
OFFLINE_EXECUTION_MODE: Final = "offline_execution"

#: Matches anything that could carry a personal path or an SEC identity into rendered
#: output: an absolute POSIX or Windows path, a URL, or a ``~`` home reference.
_PROHIBITED_RENDERING: Final = re.compile(
    r"(^|[\s=:])(/[^\s]*|~[^\s]*|[A-Za-z]:\\[^\s]*|[a-z]+://[^\s]*)"
)


@dataclass(frozen=True, slots=True)
class ExecutionInputs:
    """The caller-supplied run inputs. **None is inferred** from Git or the environment.

    ``node_limit`` is **OR-7** and stays deferred: an implementation may not choose a
    production value, so a caller must state one and a rehearsal states an explicitly
    test-only one.
    """

    snapshot_id: str
    node_limit: int
    occurred_at_utc: str
    event_id: str


@dataclass(frozen=True, slots=True)
class PairVerification:
    """The Decision 071 IN-3 pair rule, evaluated on the joint selection result."""

    entities: tuple[int, ...]
    required: int = REQUIRED_SUPPORT_TARGET_PAIR_ENTITIES
    inspected_accessions: int = 0

    @property
    def satisfied(self) -> bool:
        """Whether six distinct entities each contributed a complete pair."""
        return len(self.entities) >= self.required

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, identity-free rendering for the rehearsal evidence."""
        return {
            "distinct_pair_entities": len(self.entities),
            "required": self.required,
            "satisfied": self.satisfied,
            "inspected_accessions": self.inspected_accessions,
        }


@dataclass(frozen=True, slots=True)
class SelectionOutcome:
    """One persisted selection, with its independent reconstruction and pair proof."""

    identity: JointSelectionRunIdentity
    persisted: PersistedJointSelectionResult
    reconstructed: PersistedJointSelectionResult
    pairs: PairVerification

    @property
    def feasible(self) -> bool:
        """Whether the accepted selector reached ``feasible``."""
        return self.persisted.run_state == "feasible"


@dataclass(frozen=True, slots=True)
class ReplayProof:
    """Evidence that a replay read, reconstructed, compared, and returned."""

    digest_before: str
    digest_after: str
    strictly_read_only: bool
    replays: int

    @property
    def write_free(self) -> bool:
        """Durable-byte equality across every replay, to the **R3** standard."""
        return self.digest_before == self.digest_after and self.strictly_read_only

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering. Digests are content, never paths."""
        return {
            "write_free": self.write_free,
            "strictly_read_only": self.strictly_read_only,
            "replays": self.replays,
            "durable_digest_before": self.digest_before,
            "durable_digest_after": self.digest_after,
        }


@dataclass(frozen=True, slots=True)
class ManifestOutcome:
    """The sealed result, the built manifest, and its verification and replay."""

    selection_result_sha256: str
    manifest: PersistedPilotManifest
    verified_root_sha256: str
    replayed_root_sha256: str
    document_bytes_identical: bool

    @property
    def identical_root_on_replay(self) -> bool:
        """Decision 021 §12: regeneration from unchanged state never changes the root."""
        return (
            self.manifest.root_manifest_sha256
            == self.verified_root_sha256
            == self.replayed_root_sha256
            and self.document_bytes_identical
        )

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering. Identities only — never a path, never a row."""
        return {
            "selection_result_sha256": self.selection_result_sha256,
            "root_manifest_sha256": self.manifest.root_manifest_sha256,
            "manifest_id": self.manifest.identity.manifest_id,
            "verified_root_sha256": self.verified_root_sha256,
            "replayed_root_sha256": self.replayed_root_sha256,
            "document_bytes_identical": self.document_bytes_identical,
            "identical_root_on_replay": self.identical_root_on_replay,
        }


# --------------------------------------------------------------------------
# Step 1-4: load, select, verify the pair rule, persist
# --------------------------------------------------------------------------


def execute_selection(*, writer: CatalogWriter, inputs: ExecutionInputs) -> SelectionOutcome:
    """Run and persist one joint selection over a frozen candidate snapshot.

    The accepted store owns the transaction, the lifecycle, and every persisted row; the
    only work this function adds is deriving the run identity through the accepted
    entry point so it can be reported, verifying the pair rule against the joint result,
    and reconstructing the run independently afterwards.

    Raises:
        GateFailureError: any accepted fail-closed condition, unchanged.
    """
    connection = writer.connection
    candidate_set = load_frozen_joint_candidates(connection, inputs.snapshot_id)
    identity = build_joint_selection_run_identity(candidate_set, node_limit=inputs.node_limit)
    persisted = execute_and_persist_joint_selection(
        connection,
        inputs.snapshot_id,
        node_limit=inputs.node_limit,
        occurred_at_utc=inputs.occurred_at_utc,
        event_id=inputs.event_id,
    )
    if persisted.selection_run_id != identity.selection_run_id:
        message = (
            "the persisted run identity does not equal the identity derived from the same "
            "frozen snapshot and inputs; the run is refused rather than reconciled"
        )
        raise GateFailureError(message)
    reconstructed = reconstruct_persisted_joint_selection(connection, persisted.selection_run_id)
    pairs = verify_support_target_pairs(connection, persisted.selection_run_id)
    return SelectionOutcome(
        identity=identity,
        persisted=persisted,
        reconstructed=reconstructed,
        pairs=pairs,
    )


def verify_support_target_pairs(
    connection: sqlite3.Connection, selection_run_id: str
) -> PairVerification:
    """Evaluate the Decision 071 IN-3 pair rule against one persisted joint result.

    A pair is a property of the **result**, never of one accession: both halves must be
    selected in the same run, both must carry their frozen role, and each contributing
    entity counts exactly once. The rule itself lives in the pure
    :mod:`~disclosure_drift.m3.support_target_pairs` module; this reads the rows it needs
    and refuses to guess any of them.

    **Accepted Decision 084 R66.** The complete substantive registrant association set is
    read alongside the selected rows and handed to the pure rule, because under
    **Decision 083 R58** a jointly filed accession has **no anchor** and under **R62** it
    belongs to every substantive registrant's history. Without the set, a joint 2009 or
    2010 leg would silently contribute nothing.

    The read is `association_class = 'substantive'` on the governed candidate relation --
    the same predicate every other consumer uses -- so a submitter-only row never buys pair
    credit, and no CIK is ever chosen by minimum, maximum, first write, submitter, row
    order, date proximity, name, ticker, or hash. An accession whose set was never
    established has **no rows here at all**, which is exactly the fail-closed, zero-credit
    outcome R66 requires: the mapping is a lookup, never a default.

    Nothing about the frozen pair rule moves: the quota, the eligible forms, the 2009/2010
    years, and the accession-domain deduplication all live in the pure module and are
    untouched.
    """
    selected = [
        dict(row)
        for row in connection.execute(
            "SELECT s.accession_plain, s.accession_role, a.anchor_cik_numeric "
            "FROM pilot_selected_accessions AS s "
            "JOIN pilot_candidate_accessions AS a ON a.accession_plain = s.accession_plain "
            "AND a.snapshot_id = s.snapshot_id WHERE s.selection_run_id = ? "
            "ORDER BY s.accession_plain",
            (selection_run_id,),
        ).fetchall()
    ]
    if not selected:
        return PairVerification(entities=())
    candidates = {
        str(row["accession_plain"]): dict(row)
        for row in connection.execute(
            "SELECT c.accession_plain, c.form_type, c.is_amendment, c.official_filing_date, "
            "c.provisional_official_cohort FROM pilot_candidate_accessions AS c "
            "JOIN pilot_selection_runs AS r ON r.snapshot_id = c.snapshot_id "
            "WHERE r.selection_run_id = ?",
            (selection_run_id,),
        ).fetchall()
    }
    marked = [
        str(row["accession_plain"])
        for row in connection.execute(
            "SELECT DISTINCT p.accession_plain FROM pilot_candidate_accession_reasons AS p "
            "JOIN pilot_selection_runs AS r ON r.snapshot_id = p.snapshot_id "
            "WHERE r.selection_run_id = ? AND p.reason_code = ?",
            (selection_run_id, PRE_STUDY_SUPPORT_REASON_CODE),
        ).fetchall()
    ]
    registrants: dict[str, list[int]] = {}
    for row in connection.execute(
        "SELECT g.accession_plain, g.registrant_cik_numeric "
        "FROM pilot_candidate_accession_registrants AS g "
        "JOIN pilot_selection_runs AS r ON r.snapshot_id = g.snapshot_id "
        "WHERE r.selection_run_id = ? AND g.association_class = 'substantive' "
        "ORDER BY g.accession_plain, g.registrant_cik_numeric",
        (selection_run_id,),
    ).fetchall():
        registrants.setdefault(str(row["accession_plain"]), []).append(
            int(row["registrant_cik_numeric"])
        )
    assembled: tuple[PairedAccession, ...] = paired_accessions_from_rows(
        selected, candidates, marked, registrants
    )
    return PairVerification(
        entities=support_target_pair_entities(assembled),
        inspected_accessions=len(assembled),
    )


# --------------------------------------------------------------------------
# Step 5-6: independent reconstruction and write-free replay
# --------------------------------------------------------------------------


def durable_digest(database: Path) -> str:
    """The SHA-256 of the main database file's durable bytes.

    The main file alone is the **R3** equality target: transient ``-wal`` and ``-shm``
    sidecars are separately governed and are deliberately not hashed here.
    """
    return hashlib.sha256(database.read_bytes()).hexdigest()


def replay_selection_write_free(
    database: Path, selection_run_id: str, *, replays: int = 2
) -> ReplayProof:
    """Replay a persisted run through a strictly read-only handle, twice.

    Every read is issued through :func:`strictly_read_only_connection`, which opens
    ``SQLITE_OPEN_READONLY``: SQLite cannot checkpoint, cannot write, and takes no writer
    lease, so the proof does not rest on nobody having issued a mutating statement. The
    durable digest is taken before and after and compared.

    Raises:
        GateFailureError: a replay changed a durable byte, or the reconstructions
            disagreed between replays.
    """
    if replays < 1:
        message = "a write-free replay proof requires at least one replay"
        raise GateFailureError(message)
    before = durable_digest(database)
    fingerprints: list[str] = []
    read_only = True
    for _ in range(replays):
        with strictly_read_only_connection(database) as connection:
            # The handle's read-only status is **observed**, not asserted, and it is
            # observed **before** `query_only` is set: a logical convention on an
            # OS-level read-write handle would otherwise pass a claim it cannot support.
            read_only = read_only and _write_refused(connection)
            connection.execute("PRAGMA query_only = TRUE")
            result = reconstruct_persisted_joint_selection(connection, selection_run_id)
            fingerprints.append(
                "|".join(
                    (
                        result.selection_run_id,
                        result.snapshot_id,
                        result.run_state,
                        str(result.selected_entity_count),
                        str(result.selected_accession_count),
                        result.selection_input_sha256,
                    )
                )
            )
    after = durable_digest(database)
    if len(set(fingerprints)) != 1:
        message = "two replays of the same persisted run reconstructed differently"
        raise GateFailureError(message)
    if before != after:
        message = (
            "replay changed a durable byte of the main database file; the R3 write-free "
            "standard is durable-byte equality and this fails closed"
        )
        raise GateFailureError(message)
    if not read_only:
        message = (
            "a replay connection accepted a write; the R3 standard requires a true "
            "OS-level strictly read-only handle, not a logical convention"
        )
        raise GateFailureError(message)
    return ReplayProof(
        digest_before=before, digest_after=after, strictly_read_only=read_only, replays=replays
    )


def _write_refused(connection: sqlite3.Connection) -> bool:
    """Whether this connection actually refuses a write, probed rather than assumed."""
    try:
        connection.execute(
            "UPDATE pilot_selection_runs SET detail = detail WHERE selection_run_id IS NULL"
        )
    except sqlite3.Error:
        return True
    return False


# --------------------------------------------------------------------------
# Step 7-8: seal, manifest, verification, identical-root replay
# --------------------------------------------------------------------------


def seal_and_replay_manifest(
    *,
    writer: CatalogWriter,
    selection_run_id: str,
    data_tree: DataTree,
    explicit: ExplicitArguments,
    generated_at_utc: str,
) -> ManifestOutcome:
    """Seal the terminal result, then build, verify, and replay the manifest.

    The **seal is a separate, prior transaction** from the manifest write (contract §15,
    §17), and this function keeps that boundary: it seals, and only then constructs. A
    valid sealed selection with no manifest is a lawful state, and reaching it authorizes
    no manifest construction of its own.
    """
    connection = writer.connection
    sealed = seal_selection_result(connection, selection_run_id)
    return build_and_verify_manifest(
        writer=writer,
        selection_run_id=selection_run_id,
        data_tree=data_tree,
        explicit=explicit,
        generated_at_utc=generated_at_utc,
        sealed=sealed,
    )


def build_and_verify_manifest(
    *,
    writer: CatalogWriter,
    selection_run_id: str,
    data_tree: DataTree,
    explicit: ExplicitArguments,
    generated_at_utc: str,
    sealed: str,
) -> ManifestOutcome:
    """Construct one ``proposed`` manifest, verify it, and replay it for an equal root.

    Verification re-derives every digest from persisted rows and re-renders the document;
    the replay then re-enters the accepted construction path and must return the
    **identical** root and identical document bytes, which is what proves regeneration
    alone never changes the root (rehearsal scenario E8(a)).
    """
    connection = writer.connection
    built = build_and_persist_pilot_manifest(
        connection,
        selection_run_id,
        data_tree=data_tree,
        explicit=explicit,
        generated_at_utc=generated_at_utc,
    )
    verified = verify_pilot_manifest(
        connection, built.identity.manifest_id, data_tree=data_tree, explicit=explicit
    )
    replayed = build_and_persist_pilot_manifest(
        connection,
        selection_run_id,
        data_tree=data_tree,
        explicit=explicit,
        generated_at_utc=generated_at_utc,
    )
    return ManifestOutcome(
        selection_result_sha256=sealed,
        manifest=built,
        verified_root_sha256=verified.root_manifest_sha256,
        replayed_root_sha256=replayed.root_manifest_sha256,
        document_bytes_identical=built.canonical_json == replayed.canonical_json,
    )


# --------------------------------------------------------------------------
# Crosswalk item 80 — the CLI output Decision 021 §16 deferred from S6
# --------------------------------------------------------------------------


def render_command_invocation(argv: Sequence[str]) -> str:
    """Render the milestone-plan §10 "command invocation" field (crosswalk item 80).

    Decision 021 §16 deferred this field to M3.3 because it is a property of the command
    that produced the manifest rather than of the manifest's content. Contract §19 and
    §26 item 11 require the rendered field to carry **no personal path and no SEC
    identity at any nesting depth**, so an argument that looks like an absolute path, a
    home reference, a drive path, or a URL is refused rather than truncated, redacted, or
    silently dropped — a redaction would still be an assertion about a path.

    Raises:
        GateFailureError: an argument could carry a personal path or an SEC identity.
    """
    rendered = " ".join(argv)
    if not rendered.strip():
        message = "the command-invocation field requires the invoked command"
        raise GateFailureError(message)
    if _PROHIBITED_RENDERING.search(rendered):
        message = (
            "the command-invocation field may contain no absolute path, home reference, "
            "drive path, or URL; the invocation is refused rather than redacted"
        )
        raise GateFailureError(message)
    return rendered


# --------------------------------------------------------------------------
# Receipt provenance (contract §6 item 5; execution_receipt_spec §4.2)
# --------------------------------------------------------------------------


def cohort_definition_digest() -> str:
    """A content digest over the frozen cohort definitions, for receipt provenance.

    Computed from :data:`~disclosure_drift.cohorts.FROZEN_COHORTS` itself, so a receipt
    records the cohort set the run actually ran under rather than a restated literal. No
    clock, path, or environment value enters it.
    """
    from disclosure_drift.cohorts import FROZEN_COHORTS

    payload = "|".join(
        f"{name}:{window.start.isoformat()}:{window.end.isoformat()}"
        for name, window in sorted(FROZEN_COHORTS.items())
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def offline_execution_policy_versions() -> Mapping[str, str]:
    """The accepted policy versions an ``offline_execution`` receipt must record.

    Every value is read from the accepted constant that owns it; none is restated as a
    literal here, so a receipt cannot disagree with the code that produced the run.
    """
    from disclosure_drift.pilot_policy import (
        PILOT_JOINT_SELECTOR_POLICY_VERSION,
        PILOT_MANIFEST_HASH_POLICY_VERSION,
        PILOT_QUOTA_POLICY_VERSION,
        PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION,
    )
    from disclosure_drift.sec.accession_selection_store import (
        ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
    )

    return {
        "quota_policy_version": PILOT_QUOTA_POLICY_VERSION,
        "joint_selector_policy_version": PILOT_JOINT_SELECTOR_POLICY_VERSION,
        "replacement_signature_policy_version": PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION,
        "manifest_hash_policy_version": PILOT_MANIFEST_HASH_POLICY_VERSION,
        "selection_input_schema_version": ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
    }
