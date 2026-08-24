"""Governed major-phase restart for the disposable single-source canary (Decision 145).

**What this module is, in one sentence.** It is the durable terminal checkpoint that lets one
major execution phase end in a process that then *exits*, and the next phase begin in a
different process that reconstructs everything it needs from state on disk.

**Why it exists.** Accepted **Decision 140** §17 inspected the corrected complete-source canary
for a governed pause and resume, refused to build one, and named the sound subset it *would*
accept: the ``F0 -> F1`` and ``F1 -> F2`` boundary recycles. Both were shown sound there
rather than assumed here -- F0's evidence is
exactly reconstructible from the durable sidecar because the completeness digest absorbs only
per-member digests and counts, and F1 writes through ``INSERT ... ON CONFLICT ... DO UPDATE``
plus a plain ``UPDATE``. Decision 145 implements exactly that subset and nothing wider.

**It is not pause/resume, and it never becomes it.** The restart right exists only *after* a
phase reaches durable terminal success. A crash, a kill, an out-of-memory termination, a closed
lid, or a physical disconnect part-way through a phase is an **interruption**, which the
accepted records already govern and which this module does not reinterpret. There is no
``SAFE_TO_EJECT`` state here, no storage detach right, no topology switch, and no continuation
across a suspended process. ``GOVERNED_PAUSE_RESUME`` remains ``NOT_IMPLEMENTED``.

**Where the checkpoint lives, and why it needed no migration.** In the accepted Decision 111
run-local progress ledger (``run_progress.sqlite3``), which already sits beside the working
catalog, already runs ``WAL`` with ``synchronous = FULL``, and already exists to record *the
attempt* rather than the census. Its ``run_working_catalog`` key/value table is the durable home
the checkpoint needed, so migration head stays ``0015`` and ``0016`` stays absent. The
compact-evidence sidecar keeps its own role unchanged: it is the evidence contract, and this is
execution state.

**Nothing here authorizes a canary.** No activation constant is read, no world is created, no
network switch is consulted, and a checkpoint is not an instrument.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.working_catalog import RunProgressLedger

__all__ = [
    "CANARY_PHASE_SEQUENCE",
    "PHASE_CHECKPOINT_KEY_PREFIX",
    "PHASE_F0",
    "PHASE_F1",
    "PHASE_F2",
    "PHASE_PREDECESSOR",
    "PHASE_RESTART_CONTRACT",
    "PHASE_STATUS_COMPLETE",
    "PHASE_SUCCESSOR",
    "CanaryPhaseError",
    "PhaseCheckpoint",
    "execution_identity",
    "stored_int",
    "read_phase_checkpoint",
    "require_phase_admission",
    "validate_phase",
    "write_phase_checkpoint",
]


class CanaryPhaseError(DisclosureDriftError):
    """A phase-restart precondition failed. Never worked around, never retried in place."""


#: This mechanism's own contract identity, written into every checkpoint so that a successor
#: built from a different shape refuses rather than misreading a record it half understands.
#:
#: **Version 2 is Decision 147.** The checkpoint gained the two repository code-identity fields
#: that D146-MAJOR-1 found missing, so a version-1 checkpoint describes a phase that ran without
#: recording which revision it ran -- exactly the state a version-2 successor must not continue
#: from. Bumping the contract makes that refusal mechanical rather than a missing-field accident.
PHASE_RESTART_CONTRACT: Final = "m3.3-canary-phase-restart/2"

#: The three major execution phases of the first complete-source canary, in the order they run.
#:
#: The names are **not invented here**. ``F0``, ``F1`` and ``F2`` are the accepted Decision 135
#: §11 capacity vocabulary, carried by
#: :data:`~disclosure_drift.m3.external_working_root.CAPACITY_PHASES` and by every ruling from
#: Decision 124 onwards. F0 is the one-source parse, F1 is the Decision 012 resolution pass over
#: every persisted accession, and F2 is the Decision 094 §6.4 association projection.
PHASE_F0: Final = "f0"
PHASE_F1: Final = "f1"
PHASE_F2: Final = "f2"

CANARY_PHASE_SEQUENCE: Final[tuple[str, ...]] = (PHASE_F0, PHASE_F1, PHASE_F2)

#: Which phase must have reached a durable terminal before each phase may begin. ``F0`` has no
#: predecessor: it is the phase that creates the world.
PHASE_PREDECESSOR: Final[Mapping[str, str | None]] = {
    PHASE_F0: None,
    PHASE_F1: PHASE_F0,
    PHASE_F2: PHASE_F1,
}

#: Which phase follows each one, or ``None`` for the last. ``F2`` has no successor: the run's
#: create-once result document is written in F2's own process and the canary stops there.
PHASE_SUCCESSOR: Final[Mapping[str, str | None]] = {
    PHASE_F0: PHASE_F1,
    PHASE_F1: PHASE_F2,
    PHASE_F2: None,
}

#: The only status a checkpoint is ever written with. There is deliberately no ``in_progress``
#: and no ``failed`` value: a checkpoint is written **after** the phase reached durable terminal
#: success and never before, so its presence is the completion proof and its absence is the
#: refusal. A phase that died part-way leaves no checkpoint, which is exactly right -- an
#: interrupted phase is not a restart boundary.
PHASE_STATUS_COMPLETE: Final = "complete"

#: The ledger key one phase's checkpoint is stored under.
PHASE_CHECKPOINT_KEY_PREFIX: Final = "phase_checkpoint:"


def validate_phase(phase: str) -> str:
    """Return ``phase``, or refuse an identifier this build does not execute.

    Raises:
        CanaryPhaseError: ``phase`` is not one of :data:`CANARY_PHASE_SEQUENCE`.
    """
    if phase not in CANARY_PHASE_SEQUENCE:
        message = (
            f"{phase!r} is not a canary execution phase; the phases are "
            f"{', '.join(CANARY_PHASE_SEQUENCE)} and no other label is executed"
        )
        raise CanaryPhaseError(message)
    return phase


def execution_identity(values: Mapping[str, object]) -> str:
    """Digest the frozen values that govern how a phase executes -- Decision 145 §12.

    **Pure, and deliberately given its inputs rather than reaching for them.** The constants
    that govern this path live in :mod:`~disclosure_drift.m3.single_source_canary`, which imports
    *this* module; computing them here would be a cycle, and a second copy of them here would be
    a second source of truth. The caller assembles the mapping from its own constants and this
    folds it.

    The digest is over canonical JSON with sorted keys, so it depends on the values and not on
    the order a caller happened to build them in.
    """
    payload = json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PhaseCheckpoint:
    """One phase's durable terminal record: what finished, and what it must be continued as.

    The identity fields are what a successor process authenticates itself against. They are the
    answer to *"is this the same governed run, of the same source, under the same governing
    code, against the same accepted catalog?"* -- and every one of them refuses rather than
    warns.

    The process fields are the Decision 145 §9 RAM-reclamation evidence. ``rss_peak_bytes`` is
    the process's **peak** resident size (``ru_maxrss``), not an instantaneous sample: it is
    what the platform actually offers without a subprocess, it is the high-water mark the
    reclamation argument is about, and it is reported as the peak rather than described as
    something narrower.
    """

    contract: str
    phase: str
    status: str
    run_id: str
    source_instance_id: str
    execution_identity: str
    #: The **repository code identity** this phase executed under -- Decision 147, closing
    #: D146-MAJOR-1. ``execution_identity`` folds both of these, so either one alone would already
    #: refuse a successor whose revision moved; they are recorded separately as well because a
    #: digest says only *that* something differs. A refusal has to be able to say expected HEAD
    #: ``X``, observed ``Y``, and a digest of seventeen inputs cannot.
    repository_head_sha: str
    repository_tree_sha: str
    catalog_source_sha256: str
    migration_head: int
    plan_fingerprint: str
    completed_at_utc: str
    pid: int
    rss_peak_bytes_at_start: int | None
    rss_peak_bytes_at_terminal: int | None
    payload: Mapping[str, object]

    def as_record(self) -> Mapping[str, object]:
        """The complete checkpoint as a plain mapping, carrying no absolute path."""
        return {
            "contract": self.contract,
            "phase": self.phase,
            "status": self.status,
            "run_id": self.run_id,
            "source_instance_id": self.source_instance_id,
            "execution_identity": self.execution_identity,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "catalog_source_sha256": self.catalog_source_sha256,
            "migration_head": self.migration_head,
            "plan_fingerprint": self.plan_fingerprint,
            "completed_at_utc": self.completed_at_utc,
            "pid": self.pid,
            "rss_peak_bytes_at_start": self.rss_peak_bytes_at_start,
            "rss_peak_bytes_at_terminal": self.rss_peak_bytes_at_terminal,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> PhaseCheckpoint:
        """Rebuild a checkpoint from its stored mapping, refusing one this build cannot read.

        Raises:
            CanaryPhaseError: a required field is absent or is not of the recorded type.
        """
        try:
            payload = record["payload"]
            if not isinstance(payload, Mapping):
                message = "a phase checkpoint payload is not a mapping and is refused"
                raise CanaryPhaseError(message)
            return cls(
                contract=str(record["contract"]),
                phase=str(record["phase"]),
                status=str(record["status"]),
                run_id=str(record["run_id"]),
                source_instance_id=str(record["source_instance_id"]),
                execution_identity=str(record["execution_identity"]),
                repository_head_sha=str(record["repository_head_sha"]),
                repository_tree_sha=str(record["repository_tree_sha"]),
                catalog_source_sha256=str(record["catalog_source_sha256"]),
                migration_head=stored_int(record["migration_head"]),
                plan_fingerprint=str(record["plan_fingerprint"]),
                completed_at_utc=str(record["completed_at_utc"]),
                pid=stored_int(record["pid"]),
                rss_peak_bytes_at_start=_optional_int(record.get("rss_peak_bytes_at_start")),
                rss_peak_bytes_at_terminal=_optional_int(record.get("rss_peak_bytes_at_terminal")),
                payload=dict(payload),
            )
        except (KeyError, TypeError, ValueError) as exc:
            message = (
                f"a phase checkpoint could not be read as this build writes them ({exc}); a "
                "checkpoint that cannot be read is never treated as a completed phase"
            )
            raise CanaryPhaseError(message) from exc


def stored_int(value: object) -> int:
    """One stored integer, refusing anything that is not one.

    A checkpoint field arrives as ``object`` because it was read back from JSON, and a field that
    is not a number must **refuse** rather than be coerced through whatever ``int`` would accept.
    ``bool`` is excluded deliberately: it is an ``int`` in Python and is never a count here.

    Raises:
        CanaryPhaseError: the value is not an integer this build will read as one.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        message = (
            f"a phase checkpoint field holds {type(value).__name__} where an integer is "
            "required; a checkpoint that cannot be read is never treated as a completed phase"
        )
        raise CanaryPhaseError(message)
    return int(value)


def _optional_int(value: object) -> int | None:
    return None if value is None else stored_int(value)


def _key(phase: str) -> str:
    return f"{PHASE_CHECKPOINT_KEY_PREFIX}{validate_phase(phase)}"


def write_phase_checkpoint(ledger: RunProgressLedger, checkpoint: PhaseCheckpoint) -> None:
    """Persist one phase's terminal checkpoint, exactly once.

    **Create-once at the boundary that matters.** A checkpoint already present for this phase is
    refused rather than overwritten: the phase it describes ran, and a second write would be
    either a duplicate execution recording itself or a later attempt erasing the evidence of an
    earlier one. Both are exactly what Decision 145 §13 exists to prevent.

    Raises:
        CanaryPhaseError: the phase already carries a checkpoint, or the record is malformed.
    """
    validate_phase(checkpoint.phase)
    if checkpoint.contract != PHASE_RESTART_CONTRACT:
        message = (
            f"a phase checkpoint carrying contract {checkpoint.contract!r} is refused; this "
            f"build writes {PHASE_RESTART_CONTRACT!r} and never adopts another shape"
        )
        raise CanaryPhaseError(message)
    if checkpoint.status != PHASE_STATUS_COMPLETE:
        message = (
            f"a phase checkpoint is written only at durable terminal success, with status "
            f"{PHASE_STATUS_COMPLETE!r}; {checkpoint.status!r} is refused. An interrupted phase "
            "leaves no checkpoint, which is what makes an absent one a refusal rather than a gap"
        )
        raise CanaryPhaseError(message)
    key = _key(checkpoint.phase)
    if ledger.recorded_value(key) is not None:
        message = (
            f"phase {checkpoint.phase!r} already carries a durable terminal checkpoint; it is "
            "create-once and is never overwritten, resumed, or repaired. A second write here "
            "would be a duplicate phase execution recording itself over the first one's evidence"
        )
        raise CanaryPhaseError(message)
    ledger.record_value(key, json.dumps(checkpoint.as_record(), sort_keys=True))


def read_phase_checkpoint(ledger: RunProgressLedger, phase: str) -> PhaseCheckpoint | None:
    """One phase's durable terminal checkpoint, or ``None`` when that phase never finished.

    Raises:
        CanaryPhaseError: a checkpoint exists and cannot be read as this build writes them.
    """
    raw = ledger.recorded_value(_key(phase))
    if raw is None:
        return None
    try:
        decoded = json.loads(raw)
    except ValueError as exc:
        message = (
            f"the durable checkpoint for phase {phase!r} is not decodable JSON; an unreadable "
            "checkpoint is refused rather than read as an unfinished phase"
        )
        raise CanaryPhaseError(message) from exc
    if not isinstance(decoded, dict):
        message = f"the durable checkpoint for phase {phase!r} is not a JSON object and is refused"
        raise CanaryPhaseError(message)
    checkpoint = PhaseCheckpoint.from_record(decoded)
    if checkpoint.contract != PHASE_RESTART_CONTRACT:
        message = (
            f"the durable checkpoint for phase {phase!r} carries contract "
            f"{checkpoint.contract!r}, which this build does not continue from; the expected "
            f"contract is {PHASE_RESTART_CONTRACT!r}"
        )
        raise CanaryPhaseError(message)
    if checkpoint.phase != phase:
        message = (
            f"the checkpoint stored for phase {phase!r} describes phase {checkpoint.phase!r}; a "
            "checkpoint is never read as a phase it does not name"
        )
        raise CanaryPhaseError(message)
    return checkpoint


@dataclass(frozen=True, slots=True)
class PhaseAdmission:
    """What a successor process proved before it began: the predecessor it is continuing."""

    phase: str
    predecessor: PhaseCheckpoint | None


def require_phase_admission(
    ledger: RunProgressLedger,
    *,
    phase: str,
    run_id: str,
    source_instance_id: str,
    execution_identity: str,
    repository_head_sha: str,
    repository_tree_sha: str,
    catalog_source_sha256: str,
    migration_head: int,
    plan_fingerprint: str,
) -> PhaseAdmission:
    """Admit one phase into a fresh process, or refuse it -- Decision 145 §§10, 12 and 13.

    Three questions, in order, and each of them is dispositive:

    1. **has this phase already run?** A phase carrying its own durable checkpoint is refused.
       Re-entering it would either duplicate persistent output or overwrite the evidence of the
       execution that produced it;
    2. **did the predecessor finish?** ``F0`` has none and needs none. Every other phase requires
       its predecessor's checkpoint to be **present** and to carry
       :data:`PHASE_STATUS_COMPLETE`. An absent checkpoint is an incomplete or failed
       predecessor, and it refuses -- the existence of a world directory, a working catalog, or
       any number of committed rows is never read as phase completion;
    3. **is it the same run, of the same code?** Run identity, source identity, the declared
       execution-contract identity, **the repository commit and the repository tree the
       predecessor executed from**, the accepted catalog's own digest, the migration head, and
       the plan fingerprint must all be exactly what the predecessor recorded. A successor never
       continues another run's checkpoint, and it never continues its own run under governing
       values -- or governing *code* -- that have moved.

    **The repository identity is compared twice, deliberately.** It is folded into
    ``execution_identity``, which is the admission key, and it is also compared field by field so
    that a refusal can name the expected and observed commit and tree. Decision 147 exists
    because D146-MAJOR-1 found the earlier digest binding no executable code at all; a mechanism
    that refuses correctly but cannot say *why* is only half of the correction.

    The successor process may not say *"the previous process already checked this"*. This runs
    in the successor, against state the predecessor wrote, every time.

    Raises:
        CanaryPhaseError: the phase already ran, the predecessor did not finish, or an identity
            does not match.
    """
    validate_phase(phase)
    if read_phase_checkpoint(ledger, phase) is not None:
        message = (
            f"phase {phase!r} has already reached its durable terminal in this run and is "
            "refused. A completed phase is never re-entered: repeating it would duplicate "
            "persistent phase output, and this path has no idempotent-replay contract that "
            "would make that harmless"
        )
        raise CanaryPhaseError(message)
    predecessor_phase = PHASE_PREDECESSOR[phase]
    if predecessor_phase is None:
        return PhaseAdmission(phase=phase, predecessor=None)
    predecessor = read_phase_checkpoint(ledger, predecessor_phase)
    if predecessor is None:
        message = (
            f"phase {phase!r} cannot begin: its predecessor {predecessor_phase!r} has no durable "
            "terminal checkpoint in this run. An incomplete or failed predecessor is never "
            "treated as a completed one, and the presence of a world, a working catalog, or "
            "committed rows is not phase-completion proof"
        )
        raise CanaryPhaseError(message)
    if predecessor.status != PHASE_STATUS_COMPLETE:
        message = (
            f"phase {phase!r} cannot begin: its predecessor {predecessor_phase!r} recorded "
            f"status {predecessor.status!r} rather than {PHASE_STATUS_COMPLETE!r}"
        )
        raise CanaryPhaseError(message)
    _require_identity(predecessor, "run_id", predecessor.run_id, run_id)
    _require_identity(
        predecessor, "source_instance_id", predecessor.source_instance_id, source_instance_id
    )
    # The named identities first and the aggregate digest LAST, deliberately. Every named field
    # is also folded into `execution_identity`, so comparing the digest first would make every
    # refusal say "execution_identity" and nothing else -- which is a correct refusal that cannot
    # be diagnosed. Checking the specific causes first means a moved revision reports the moved
    # revision, with both values, and the digest stays as the catch-all for anything a named
    # comparison would miss.
    _require_identity(
        predecessor, "repository_head_sha", predecessor.repository_head_sha, repository_head_sha
    )
    _require_identity(
        predecessor, "repository_tree_sha", predecessor.repository_tree_sha, repository_tree_sha
    )
    _require_identity(
        predecessor,
        "catalog_source_sha256",
        predecessor.catalog_source_sha256,
        catalog_source_sha256,
    )
    _require_identity(
        predecessor, "migration_head", str(predecessor.migration_head), str(migration_head)
    )
    _require_identity(
        predecessor, "plan_fingerprint", predecessor.plan_fingerprint, plan_fingerprint
    )
    _require_identity(
        predecessor, "execution_identity", predecessor.execution_identity, execution_identity
    )
    return PhaseAdmission(phase=phase, predecessor=predecessor)


def _require_identity(
    predecessor: PhaseCheckpoint, field: str, recorded: str, observed: str
) -> None:
    """Refuse a continuation whose identity does not match the predecessor's recorded one."""
    if recorded == observed:
        return
    message = (
        f"the {field} this process would continue under does not match the one phase "
        f"{predecessor.phase!r} recorded at its terminal: expected {recorded!r}, observed "
        f"{observed!r}. A successor process is a continuation of the SAME governed run: it never "
        "adopts another run's checkpoint, and it never continues its own run under governing "
        "values -- or governing code -- that have changed since the predecessor finished. The "
        "run is refused and nothing was started, nothing was checked out or repaired, and this "
        "is not a resumable pause"
    )
    raise CanaryPhaseError(message)
