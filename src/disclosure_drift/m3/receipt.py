"""Milestone 3.1 execution receipts (``Docs/m3/execution_receipt_spec.md``, Decision 028 §§9-10).

A receipt is the smallest durable artifact that answers *what did that run actually do* -- counts,
classifications, versions, identifiers, and statuses. It is **operational evidence and never an
input to any governed identity** (spec §0). That property is asserted at the suite level by
rehearsal scenario A12, not by a per-receipt check; nothing here can be reached from
``snapshot_id``, any selection identity, any component digest, ``root_manifest_sha256``, or
``manifest_id``, because nothing in this module is ever handed to them.

What this module does guarantee:

* **The §4 classification table, enforced exactly.** Every field carries one class -- ``R``
  (required in all modes), ``C:<modes>`` (required in the named modes, **absent** outside them), or
  ``P:<modes>`` (prohibited in the named modes). There is no "optional" class, and an inapplicable
  field is *omitted*, never rendered as ``null`` or a placeholder.
* **§6 canonical serialization**, so two receipts are comparable and a written receipt round-trips
  byte-for-byte.
* **§13's single integrity identity.** ``receipt_id = SHA256(canonical bytes with ``receipt_id``
  omitted)``. There is exactly one, and a second receipt-integrity field is refused.
* **§14 validation, fail-closed**, at construction and again at inspection.
* **§5's prohibited-content scan**, applied to keys and to every nested string value.
* **§7 storage**: content-derived filename, written once, thereafter immutable, and always outside
  the public repository checkout.

Three classification rules in §4 are conditional on something other than the invocation mode, and
each is handled explicitly rather than being flattened into "optional":

``reason_code``, ``reason_detail``, ``interruption_state``,
``remaining_planned_logical_request_count``, ``consumed_request_count_carried_forward``
    Required exactly when their stated condition holds and **absent** when it does not. Every one of
    these conditions is decidable from the receipt itself, so all five are enforced both ways.

``recovery_predecessor_receipt_id``
    Its condition -- "a resumed run" -- is knowable only *from this field*. It is therefore
    permitted in any mode and never independently required; its presence is what makes the run a
    resumed one, which in turn makes ``consumed_request_count_carried_forward`` required in
    ``live``.

Schema ``3.0`` adds one field and restates one condition (accepted Decision 055 §7), and changes
nothing else. ``consumed_request_count_carried_forward`` means **cumulative physical attempts before
the current invocation**: required for a resume, required for a clean carry-in root, and omitted for
an ordinary zero-baseline fresh root. ``carry_in_authority_sha256`` names the one-use carry-in
authority a clean carry-in root consumed, and is required **only** there -- on a receipt with no
predecessor and a non-zero carried-forward count -- and absent on ordinary roots and on resumes.

**Version dispatch, not migration.** ``2.0`` receipts remain byte-unchanged, valid, readable, and
usable in mixed-version chains; reading dispatches on the version the document declares and nothing
here ever rewrites or upgrades a stored receipt. Only the writer moved.

``resulting_snapshot_id`` and the other ``resulting_*`` references
    §4.7 qualifies each with "where the command produced one". That condition is a fact about the
    command, not about the receipt, so the mode gate is enforced strictly -- they may never appear
    outside ``offline_execution`` (or ``approval``, for the two manifest references) -- while
    presence within those modes is the caller's assertion. Requiring them unconditionally would make
    an ``offline_execution`` command that seals no manifest unable to emit a receipt at all, which
    fails closed in the wrong direction.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.evidence_paths import require_external_evidence_root
from disclosure_drift.reasons import REASON_CODES

__all__ = [
    "COMPLETION_STATUSES",
    "COMPLETION_STATUSES_V4",
    "INTERRUPTION_STATES",
    "INTERRUPTION_STATES_V4",
    "INVOCATION_MODES",
    "INVOCATION_MODES_V4",
    "OPERATOR_RECEIPT_FILENAME",
    "PHASES",
    "PHASE_V4",
    "READABLE_RECEIPT_SCHEMA_VERSIONS",
    "RECEIPT_SCHEMA_VERSION",
    "RECEIPT_SCHEMA_VERSION_V2",
    "RECEIPT_SCHEMA_VERSION_V4",
    "REASON_CODES_V4",
    "RESPONSE_CLASSIFICATION_BUCKETS",
    "RUN_NAMESPACE_DIRNAME",
    "SCHEMA_DRIFT_OUTCOMES",
    "ZERO_NETWORK_MODES",
    "ZERO_NETWORK_MODES_V4",
    "ExecutionReceipt",
    "ExecutionReceiptV4",
    "ProhibitedReceiptContentError",
    "ReceiptChainResolutionError",
    "ReceiptError",
    "ReceiptValidationError",
    "ReceiptWriteError",
    "canonical_bytes",
    "compute_receipt_id",
    "content_derived_receipt_name",
    "inspect_receipt",
    "receipts_directory",
    "resolve_predecessor_receipt",
    "scan_for_prohibited_content",
    "validate_receipt_document",
    "write_receipt",
]

#: The schema this module **writes**. Decision 028 §9 fixed the v2 field set and Decision 045 froze
#: it; accepted Decision 055 §7 unfreezes it for exactly one backward-compatible successor, so the
#: writer emits ``3.0`` and nothing else. A further major version requires a new accepted decision,
#: which is why this is a constant and not a parameter (spec §12).
RECEIPT_SCHEMA_VERSION: Final = "m3-execution-receipt/3.0"

#: The predecessor schema. Receipts already written under it are **byte-unchanged, valid, readable,
#: and usable in mixed-version chains**, and are **never rewritten** (Decision 055 §7.1). Reading
#: dispatches on the version found in the document; it never upgrades one in place.
RECEIPT_SCHEMA_VERSION_V2: Final = "m3-execution-receipt/2.0"

#: The Decision 094 §10.1 successor. It exists for exactly the two new PRE-E0 operator commands
#: and **nothing else emits it**: `2.0` and `3.0` receipts stay byte-unchanged, their validators
#: and writer behavior are untouched, and every existing command still emits `3.0`. The delta is
#: deliberately one-directional -- v4 adds two zero-network invocation modes, a stage-specific
#: interruption vocabulary, and a stage-specific closed reason vocabulary, all of them
#: **version-scoped objects** that no v2/v3 validator can see. A `3.0` document naming a v4-only
#: mode or interruption state is refused by the `3.0` table, which is what keeps the isolation a
#: mechanical fact rather than a convention.
RECEIPT_SCHEMA_VERSION_V4: Final = "m3-execution-receipt/4.0"

#: Every schema version a reader accepts. The writer is :data:`RECEIPT_SCHEMA_VERSION` for every
#: pre-existing command; only the two Decision 094 commands call the explicit v4 builder.
READABLE_RECEIPT_SCHEMA_VERSIONS: Final = (
    RECEIPT_SCHEMA_VERSION_V2,
    RECEIPT_SCHEMA_VERSION,
    RECEIPT_SCHEMA_VERSION_V4,
)

INVOCATION_MODES: Final = ("approval", "dry_run", "live", "offline_execution", "rehearsal")
"""The five invocation modes (spec §4)."""

#: The only mode that places a request on the wire. Every other mode reports zero network activity,
#: and a non-zero count there is a fail-closed error rather than a reporting convention (§4.5.1).
ZERO_NETWORK_MODES: Final = ("approval", "dry_run", "offline_execution", "rehearsal")

PHASES: Final = (
    "M3.1A",
    "M3.1B",
    "M3.2A",
    "M3.2B",
    "M3.3A",
    "M3.3B",
    "M3.4A",
    "M3.4B",
    "M3.5",
)

COMPLETION_STATUSES: Final = (
    "complete",
    "failed",
    "interrupted",
    "stopped_at_ceiling",
    "stopped_by_gate",
)

SCHEMA_DRIFT_OUTCOMES: Final = ("blocked", "none", "unknown_fields_retained")

INTERRUPTION_STATES: Final = (
    "after_catalog_commit",
    "after_raw_store_write_before_catalog_commit",
    "before_raw_store_write",
    "during_manifest_write",
    "during_selection",
)

#: Every response falls in exactly one bucket, and there is no ``unclassified`` bucket (§4.5).
RESPONSE_CLASSIFICATION_BUCKETS: Final = (
    "cooldown",
    "fail",
    "proceed",
    "quarantine",
    "retry",
    "retry_after",
)

ACQUISITION_WINDOWS: Final = ("M3.2A", "M3.2B")

# --------------------------------------------------------------------------- #
# Decision 094 §10.1 -- the version-scoped `4.0` vocabulary
#
# Every object below is v4-only. None of it is added to the tuples above, none of it is
# reachable from `_RULES` or `_RULES_V3`, and none of it enters `reasons.py`. That is the
# whole point of the ruling: a v4 value in a v2/v3 document must fail closed.
# --------------------------------------------------------------------------- #
#: The two PRE-E0 invocation modes. Both are zero-network by construction: the commands
#: that emit them import no client, transport, socket, or SEC route on any code path.
INVOCATION_MODES_V4: Final = ("offline_catalog_transition", "offline_parse")

#: Both v4 modes place nothing on the wire, so both counts are fixed at zero (§7.3).
ZERO_NETWORK_MODES_V4: Final = INVOCATION_MODES_V4

#: Decision 094 §10.1 item 1: the already-accepted real-execution phase, deliberately reused
#: rather than inventing a new project phase for two commands inside an existing one.
PHASE_V4: Final = "M3.3B"

COMPLETION_STATUSES_V4: Final = ("complete", "failed", "interrupted")
"""The only three terminal statuses either PRE-E0 state machine can reach.

There is no ``stopped_at_ceiling`` -- the ceiling is zero and nothing is ever attempted -- and
no ``stopped_by_gate``: a refused predicate is a ``failed`` run with its own reason code, not a
fourth status that would let a refusal read as an orderly stop.
"""

#: Decision 094 §10.2's exact interruption vocabulary, in the order the ruling states it.
INTERRUPTION_STATES_V4: Final = (
    "before_backup",
    "during_backup",
    "after_backup_before_migration",
    "after_migration_0014_before_0015",
    "after_migration_0014_commit_before_event",
    "after_migration_0015_commit_before_event",
    "after_migration_0015_before_transition_freeze",
    "during_e0_source_parse",
    "after_e0_source_commit_before_event",
    "during_e0_full_index_observation_materialization",
    "after_e0_full_index_observations_before_resolution",
    "during_e0_accession_resolution",
    "after_e0_resolution_before_association_materialization",
    "during_e0_association_materialization",
    "after_e0_materialization_before_validation",
    "after_e0_validation_before_freeze",
)

REASON_CODES_V4: Final = (
    "PRE_E0_CATALOG_TRANSITION_FAILED",
    "PRE_E0_CATALOG_TRANSITION_INTERRUPTED",
    "M3_3_E0_OFFLINE_PARSE_FAILED",
    "M3_3_E0_OFFLINE_PARSE_INTERRUPTED",
)
"""Decision 094 §10.1's closed v4 reason vocabulary.

Stage-specific, release-blocking, and manual-review-required by the ruling's own words, and
deliberately **not** added to :mod:`disclosure_drift.reasons`: the repository-wide registry is a
prohibited path for this stage, and a four-code stage vocabulary does not need to become a
repository-wide one to be closed. A v2/v3 receipt still validates its ``reason_code`` against
the repository registry, exactly as before.
"""

_ALL_MODES: Final = frozenset(INVOCATION_MODES)
_LIVE: Final = frozenset({"live"})
_DRY_RUN_AND_LIVE: Final = frozenset({"dry_run", "live"})
_OFFLINE: Final = frozenset({"offline_execution"})
_OFFLINE_AND_APPROVAL: Final = frozenset({"offline_execution", "approval"})
_LIVE_AND_OFFLINE: Final = frozenset({"live", "offline_execution"})
_LIVE_AND_REHEARSAL: Final = frozenset({"live", "rehearsal"})
_REHEARSAL: Final = frozenset({"rehearsal"})

_SHA256_PATTERN: Final = re.compile(r"\A[0-9a-f]{64}\Z")
_TIMESTAMP_PATTERN: Final = re.compile(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\Z")

#: Values that stand in for an omission. §14 names an empty string, ``null``, and ``"N/A"``.
#:
#: Zero is deliberately absent: §14's "never ... ``0``" bars zero as a *stand-in for an omission*,
#: and a count of zero is a legitimate value for a field that applies. The omission is expressed by
#: the field being absent, which class conformance already enforces. ``"none"`` is likewise absent,
#: because it is a real ``schema_drift_outcome`` value.
_PLACEHOLDER_STRINGS: Final = frozenset({"", "-", "n/a", "null"})

#: The longest a ``reason_detail`` may be. §4.8 calls for "one short non-secret sentence"; a bound
#: is what makes that enforceable, and it also limits how much a free-text field could smuggle.
_REASON_DETAIL_MAX_CHARS: Final = 200


class ReceiptError(DisclosureDriftError):
    """Base class for every receipt failure. Every one of them is fail-closed."""


class ReceiptValidationError(ReceiptError):
    """Raised when a receipt violates the specification.

    The renderer refuses to emit and the inspector exits ``4``; there is no warning path and no
    "emit it anyway" flag.
    """


class ProhibitedReceiptContentError(ReceiptValidationError):
    """Raised when §5 prohibited content is found in a receipt.

    Encoding does not launder a prohibited value, so this is raised on the value as supplied rather
    than after any masking step -- §9's rule is that redaction happens at construction, and there is
    no "redact before sharing" step to forget.
    """


class ReceiptWriteError(ReceiptError):
    """Raised when writing a receipt would violate §7's write-once immutability."""


# --------------------------------------------------------------------------- #
# The §4 permitted-field table
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class _Rule:
    """One row of the §4 permitted-field table.

    ``modes`` is the set of invocation modes in which the field may appear at all; presence outside
    it is always an error. ``condition`` decides whether, inside those modes, the field is
    *required* or merely *permitted*.
    """

    name: str
    kind: str
    modes: frozenset[str]
    condition: str = "in_modes"
    values: tuple[str, ...] | None = None


_RULES: Final[tuple[_Rule, ...]] = (
    # §4.1 identity and provenance
    _Rule("receipt_schema_version", "string", _ALL_MODES),
    _Rule("receipt_id", "sha256", _ALL_MODES),
    _Rule("command_name", "string", _ALL_MODES),
    _Rule("command_version", "string", _ALL_MODES),
    _Rule("phase", "enum", _ALL_MODES, values=PHASES),
    _Rule("invocation_mode", "enum", _ALL_MODES, values=INVOCATION_MODES),
    _Rule("configuration_fingerprint", "sha256", _ALL_MODES),
    # §4.2 policy and definition versions
    _Rule("source_registry_version", "string", _DRY_RUN_AND_LIVE),
    _Rule("index_plan_policy_version", "string", _DRY_RUN_AND_LIVE),
    _Rule("request_plan_schema_version", "string", _DRY_RUN_AND_LIVE),
    _Rule("quota_policy_version", "string", _OFFLINE),
    _Rule("joint_selector_policy_version", "string", _OFFLINE),
    _Rule("replacement_signature_policy_version", "string", _OFFLINE),
    _Rule("manifest_hash_policy_version", "string", _OFFLINE_AND_APPROVAL),
    _Rule("selection_input_schema_version", "string", _OFFLINE),
    _Rule("parser_versions", "string_map", _LIVE_AND_OFFLINE),
    _Rule("cohort_definition_digest", "sha256", _OFFLINE),
    _Rule("migration_chain_head", "string", _ALL_MODES),
    # §4.3 timing
    _Rule("started_at_utc", "timestamp", _ALL_MODES),
    _Rule("completed_at_utc", "timestamp", _ALL_MODES),
    _Rule("elapsed_seconds", "number", _ALL_MODES),
    # §4.4 request plan and budget
    _Rule("acquisition_window", "enum", _DRY_RUN_AND_LIVE, values=ACQUISITION_WINDOWS),
    _Rule("request_plan_id", "string", _DRY_RUN_AND_LIVE),
    _Rule("request_plan_sha256", "sha256", _DRY_RUN_AND_LIVE),
    _Rule("approved_request_ceiling", "integer", _LIVE),
    _Rule("planned_logical_request_count", "integer", _DRY_RUN_AND_LIVE),
    _Rule("maximum_physical_attempt_count", "integer", _DRY_RUN_AND_LIVE),
    _Rule("planned_per_route", "count_map", _DRY_RUN_AND_LIVE),
    # §4.5 actual execution accounting
    _Rule("actual_logical_request_count", "integer", _ALL_MODES),
    _Rule("actual_physical_attempt_count", "integer", _ALL_MODES),
    _Rule("actual_per_route", "route_totals", _LIVE),
    _Rule("response_classification_totals", "classification_totals", _LIVE),
    _Rule("status_code_totals", "count_map", _LIVE),
    _Rule("raw_object_count", "integer", _LIVE),
    _Rule("duplicate_object_count", "integer", _LIVE),
    _Rule("cache_hit_count", "integer", _LIVE),
    _Rule("not_modified_count", "integer", _LIVE),
    _Rule("quarantined_object_count", "integer", _LIVE),
    _Rule("redirect_hop_count", "integer", _LIVE),
    _Rule("cooldown_count", "integer", _LIVE),
    _Rule(
        "remaining_planned_logical_request_count",
        "integer",
        _LIVE,
        condition="stopped_at_ceiling",
    ),
    # §4.6 drift outcomes
    _Rule("schema_drift_outcome", "enum", _LIVE_AND_REHEARSAL, values=SCHEMA_DRIFT_OUTCOMES),
    _Rule("schema_drift_event_count", "integer", _LIVE_AND_REHEARSAL),
    # §4.7 resulting governed identities, recorded as one-way references
    _Rule("resulting_snapshot_id", "string", _OFFLINE, condition="permitted"),
    _Rule("resulting_selection_run_id", "string", _OFFLINE, condition="permitted"),
    _Rule("resulting_selection_result_sha256", "sha256", _OFFLINE, condition="permitted"),
    _Rule(
        "resulting_root_manifest_sha256",
        "sha256",
        _OFFLINE_AND_APPROVAL,
        condition="permitted",
    ),
    _Rule("resulting_manifest_id", "string", _OFFLINE_AND_APPROVAL, condition="permitted"),
    # §4.8 completion and recovery
    _Rule("completion_status", "enum", _ALL_MODES, values=COMPLETION_STATUSES),
    _Rule("reason_code", "string", _ALL_MODES, condition="non_complete"),
    _Rule("reason_detail", "reason_detail", _ALL_MODES, condition="non_complete"),
    _Rule(
        "interruption_state",
        "enum",
        _ALL_MODES,
        condition="interrupted",
        values=INTERRUPTION_STATES,
    ),
    _Rule("recovery_predecessor_receipt_id", "sha256", _ALL_MODES, condition="permitted"),
    _Rule("consumed_request_count_carried_forward", "integer", _LIVE, condition="resumed"),
    _Rule("rehearsal_evidence_reference", "string", _REHEARSAL),
)

#: The ``3.0`` table (Decision 055 §§7.2-7.4). It is the ``2.0`` table with exactly two changes, and
#: no other field is added, removed, retyped, or re-moded:
#:
#: * ``consumed_request_count_carried_forward`` now means **cumulative physical attempts before the
#:   current invocation**, and is required for a resume *and* for a clean carry-in root, while still
#:   being omitted for an ordinary zero-baseline fresh root;
#: * ``carry_in_authority_sha256`` is new, and is required **only** on a clean carry-in root — one
#:   with no predecessor and a non-zero carried-forward count.
#:
#: The two conditions interlock, which is what makes every malformed combination fail closed
#: without a separate cross-field pass: an authority hash with a predecessor is a field present
#: outside its condition; a non-zero carried-forward count with no predecessor and no authority hash
#: leaves a required field missing; and a carried-forward count on an ordinary root is a
#: conditionally-required field present where it must be omitted.
_RULES_V3: Final[tuple[_Rule, ...]] = tuple(
    _Rule(
        "consumed_request_count_carried_forward",
        "integer",
        _LIVE,
        condition="carried_forward",
    )
    if rule.name == "consumed_request_count_carried_forward"
    else rule
    for rule in _RULES
) + (_Rule("carry_in_authority_sha256", "sha256", _LIVE, condition="carry_in_root"),)

_V4_MODES: Final = frozenset(INVOCATION_MODES_V4)
_V4_PARSE: Final = frozenset({"offline_parse"})

#: The ``4.0`` table (Decision 094 §10.1 items 3-4), written out in full rather than derived from
#: ``_RULES_V3``. Derivation would be shorter and wrong: v4's permitted set is a *different,
#: smaller* closed set, and every selection, quota, manifest, drift, route, classification, and
#: transport field is absent from it entirely -- so a document carrying one is refused by the
#: closed-field-set check outright, not merely found out of mode.
#:
#: ``offline_catalog_transition`` permits only the common identity, migration, timing,
#: zero-network, completion, reason, interruption, and predecessor fields. ``offline_parse``
#: additionally requires the parser versions and the cohort-definition digest, because it is the
#: mode that actually parses.
#:
#: No terminal-record field appears here. §10.1 makes the relationship deliberately one-way --
#: the receipt is written first and the terminal record binds its ``receipt_id`` -- which is what
#: prevents a receipt/terminal identity cycle.
_RULES_V4: Final[tuple[_Rule, ...]] = (
    # §4.1 identity and provenance
    _Rule("receipt_schema_version", "string", _V4_MODES),
    _Rule("receipt_id", "sha256", _V4_MODES),
    _Rule("command_name", "string", _V4_MODES),
    _Rule("command_version", "string", _V4_MODES),
    _Rule("phase", "enum", _V4_MODES, values=(PHASE_V4,)),
    _Rule("invocation_mode", "enum", _V4_MODES, values=INVOCATION_MODES_V4),
    _Rule("configuration_fingerprint", "sha256", _V4_MODES),
    _Rule("migration_chain_head", "string", _V4_MODES),
    # §4.2 policy and definition versions, narrowed to what the parsing mode needs
    _Rule("parser_versions", "string_map", _V4_PARSE),
    _Rule("cohort_definition_digest", "sha256", _V4_PARSE),
    # §4.3 timing
    _Rule("started_at_utc", "timestamp", _V4_MODES),
    _Rule("completed_at_utc", "timestamp", _V4_MODES),
    _Rule("elapsed_seconds", "number", _V4_MODES),
    # §4.5 accounting: both fixed at zero by the schema's zero-network mode set
    _Rule("actual_logical_request_count", "integer", _V4_MODES),
    _Rule("actual_physical_attempt_count", "integer", _V4_MODES),
    # §4.8 completion and recovery
    _Rule("completion_status", "enum", _V4_MODES, values=COMPLETION_STATUSES_V4),
    _Rule("reason_code", "string", _V4_MODES, condition="non_complete"),
    _Rule("reason_detail", "reason_detail", _V4_MODES, condition="non_complete"),
    _Rule(
        "interruption_state",
        "enum",
        _V4_MODES,
        condition="interrupted",
        values=INTERRUPTION_STATES_V4,
    ),
    _Rule("recovery_predecessor_receipt_id", "sha256", _V4_MODES, condition="permitted"),
)


@dataclass(frozen=True, slots=True)
class _Schema:
    """One receipt schema version: its permitted-field table, indexed for lookup.

    Reading dispatches on the version found in the document, so a ``2.0`` receipt is validated
    against the ``2.0`` table exactly as it always was — ``carry_in_authority_sha256`` is not a
    permitted field there, and the closed field set refuses it — while a ``3.0`` receipt is
    validated against the ``3.0`` table. Neither table can leak into the other.
    """

    version: str
    rules: tuple[_Rule, ...]
    #: The modes this version fixes at zero requests and zero attempts. On the schema, not at
    #: module level, because Decision 094 §10.1 requires every v4 vocabulary object to be
    #: version-scoped -- a shared tuple consulted by a common checker would not be.
    zero_network_modes: frozenset[str]
    #: The closed reason vocabulary this version validates against, or ``None`` for "use the
    #: repository-wide :mod:`disclosure_drift.reasons` registry" -- which is exactly what ``2.0``
    #: and ``3.0`` did before and still do. Decision 094 §10.1 gives v4 a stage-specific closed
    #: vocabulary precisely so the repository registry does not have to change.
    reason_codes: frozenset[str] | None = None

    @property
    def by_name(self) -> Mapping[str, _Rule]:
        return {rule.name: rule for rule in self.rules}

    @property
    def caller_fields(self) -> tuple[str, ...]:
        """Field names a caller supplies: neither the version nor the derived identity."""
        return tuple(
            rule.name
            for rule in self.rules
            if rule.name not in {"receipt_schema_version", "receipt_id"}
        )


_SCHEMA_V2: Final = _Schema(
    version=RECEIPT_SCHEMA_VERSION_V2,
    rules=_RULES,
    zero_network_modes=frozenset(ZERO_NETWORK_MODES),
)
_SCHEMA_V3: Final = _Schema(
    version=RECEIPT_SCHEMA_VERSION,
    rules=_RULES_V3,
    zero_network_modes=frozenset(ZERO_NETWORK_MODES),
)
_SCHEMA_V4: Final = _Schema(
    version=RECEIPT_SCHEMA_VERSION_V4,
    rules=_RULES_V4,
    zero_network_modes=frozenset(ZERO_NETWORK_MODES_V4),
    reason_codes=frozenset(REASON_CODES_V4),
)

_SCHEMAS: Final[Mapping[str, _Schema]] = {
    _SCHEMA_V2.version: _SCHEMA_V2,
    _SCHEMA_V3.version: _SCHEMA_V3,
    _SCHEMA_V4.version: _SCHEMA_V4,
}

_RULES_BY_NAME: Final[Mapping[str, _Rule]] = _SCHEMA_V3.by_name

#: Field names the caller supplies. ``receipt_schema_version`` is written by this module and
#: ``receipt_id`` is derived, so neither is a constructor argument.
_CALLER_FIELDS: Final = _SCHEMA_V3.caller_fields


# --------------------------------------------------------------------------- #
# §5 prohibited-content scan
# --------------------------------------------------------------------------- #
#: Key fragments that name a prohibited class outright. The permitted field set is closed, so this
#: can only fire on a document that already went wrong -- which is exactly what makes it a usable
#: positive control (§9.4, rehearsal A12(a)).
_PROHIBITED_KEY_FRAGMENTS: Final = (
    "api_key",
    "apikey",
    "auth",
    "cookie",
    "credential",
    "email",
    "password",
    "secret",
    "token",
    "user_agent",
    "useragent",
)

#: Value fragments that indicate a credential, a header, or a cookie, matched case-insensitively.
_PROHIBITED_VALUE_FRAGMENTS: Final = (
    "api_key",
    "apikey",
    "authorization",
    "basic ",
    "bearer ",
    "cookie",
    "password",
    "secret",
)

#: Top-level field names an accepted decision fixed that collide with a prohibited key *fragment*
#: without carrying anything prohibited. ``carry_in_authority_sha256`` (Decision 055 §7.3) contains
#: ``auth``, the fragment that guards against an ``authorization`` header; the field holds a SHA-256
#: digest of a public artifact and no header, credential, or identity.
#:
#: The exemption is deliberately as small as it can be: the exact name, at the **top level** only.
#: A nested key of the same name, any other key containing ``auth``, and the value scan over this
#: field's own contents are all unaffected — so a credential still cannot ride in under this name.
_KEY_FRAGMENT_EXEMPT_FIELDS: Final = frozenset({"carry_in_authority_sha256"})

_EMAIL_PATTERN: Final = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

#: An absolute or home-relative path anywhere inside a string. §5 forbids absolute personal paths
#: outright; paths are recorded relative to the data root or not at all. The leading boundary keeps
#: version strings such as ``m3-execution-receipt/2.0`` from matching.
_ABSOLUTE_PATH_PATTERN: Final = re.compile(r"(?:\A|\s)(?:/[^\s/]|~[/\\]|[A-Za-z]:[\\/])")


def _refuse(location: str, why: str) -> ProhibitedReceiptContentError:
    return ProhibitedReceiptContentError(f"prohibited content at {location}: {why}")


def _scan_string(location: str, value: str) -> None:
    lowered = value.casefold()
    if _EMAIL_PATTERN.search(value):
        raise _refuse(location, "an email address is personally identifying and is never recorded")
    if _ABSOLUTE_PATH_PATTERN.search(value):
        raise _refuse(
            location,
            "an absolute or home-relative path identifies a machine and a person; record paths "
            "relative to the data root or not at all",
        )
    for fragment in _PROHIBITED_VALUE_FRAGMENTS:
        if fragment in lowered:
            raise _refuse(location, f"the value carries a credential marker {fragment!r}")


def _scan_node(location: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                message = f"receipt key at {location} must be a string"
                raise ReceiptValidationError(message)
            child = f"{location}.{key}" if location else key
            lowered_key = key.casefold()
            if not (location == "" and key in _KEY_FRAGMENT_EXEMPT_FIELDS):
                for fragment in _PROHIBITED_KEY_FRAGMENTS:
                    if fragment in lowered_key:
                        raise _refuse(
                            child, f"the field name carries a prohibited marker {fragment!r}"
                        )
            _scan_string(child, key)
            _scan_node(child, item)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _scan_node(f"{location}[{index}]", item)
        return
    if isinstance(value, str):
        _scan_string(location, value)


def scan_for_prohibited_content(document: Mapping[str, object]) -> None:
    """Refuse any §5 prohibited content found in ``document``.

    Keys are scanned as well as values, and the walk descends into nested mappings, so a prohibited
    value cannot hide one level down. Raises :class:`ProhibitedReceiptContentError`.
    """
    _scan_node("", document)


# --------------------------------------------------------------------------- #
# §6 canonical serialization
# --------------------------------------------------------------------------- #
def _jsonable(value: object) -> object:
    """Render mappings as plain dictionaries so serialization sees no proxy or custom type."""
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def canonical_bytes(document: Mapping[str, object]) -> bytes:
    """Serialize ``document`` in the §6 canonical form.

    UTF-8 with no byte-order mark, LF only, keys sorted by code point at every level, no non-finite
    number, integers without a decimal point, absent fields omitted rather than rendered as
    ``null``, and exactly one trailing newline.
    """
    try:
        rendered = json.dumps(
            _jsonable(document),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except ValueError as exc:
        message = f"receipt is not canonically serializable: {exc}"
        raise ReceiptValidationError(message) from exc
    return f"{rendered}\n".encode()


def compute_receipt_id(document: Mapping[str, object]) -> str:
    """Return ``SHA256(canonical bytes with ``receipt_id`` omitted)`` -- the §13 identity."""
    preimage = {key: value for key, value in document.items() if key != "receipt_id"}
    return hashlib.sha256(canonical_bytes(preimage)).hexdigest()


# --------------------------------------------------------------------------- #
# §14 validation
# --------------------------------------------------------------------------- #
def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _as_int(value: object) -> int:
    """Narrow a value the field table has already typed as a count.

    Reached only after :func:`_check_kind`, so the guard here is a defensive restatement of an
    invariant rather than a second validation path -- and it still fails closed if that order
    ever changes.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"expected an integer count, found {type(value).__name__}"
        raise ReceiptValidationError(message)
    return value


def _check_kind(rule: _Rule, value: object) -> None:
    name = rule.kind
    if name == "string":
        if not isinstance(value, str):
            message = f"{rule.name} must be a string"
            raise ReceiptValidationError(message)
        return
    if name == "reason_detail":
        if not isinstance(value, str):
            message = f"{rule.name} must be a string"
            raise ReceiptValidationError(message)
        if "\n" in value or len(value) > _REASON_DETAIL_MAX_CHARS:
            message = (
                f"{rule.name} must be one short single-line sentence of at most "
                f"{_REASON_DETAIL_MAX_CHARS} characters"
            )
            raise ReceiptValidationError(message)
        return
    if name == "sha256":
        if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
            message = f"{rule.name} must be a lowercase 64-character SHA-256 digest"
            raise ReceiptValidationError(message)
        return
    if name == "timestamp":
        if not isinstance(value, str) or not _TIMESTAMP_PATTERN.fullmatch(value):
            message = f"{rule.name} must be an RFC 3339 UTC timestamp with a 'Z' suffix"
            raise ReceiptValidationError(message)
        return
    if name == "enum":
        permitted = rule.values or ()
        if value not in permitted:
            message = f"{rule.name} must be one of {', '.join(sorted(permitted))}"
            raise ReceiptValidationError(message)
        return
    if name == "integer":
        if not _is_integer(value) or _as_int(value) < 0:
            message = f"{rule.name} must be a non-negative integer"
            raise ReceiptValidationError(message)
        return
    if name == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            message = f"{rule.name} must be a number"
            raise ReceiptValidationError(message)
        if not math.isfinite(float(value)) or float(value) < 0:
            message = f"{rule.name} must be a finite non-negative number"
            raise ReceiptValidationError(message)
        return
    if name == "string_map":
        _check_mapping(rule, value, lambda item: isinstance(item, str) and bool(item.strip()))
        return
    if name == "count_map":
        _check_mapping(rule, value, lambda item: _is_integer(item) and _as_int(item) >= 0)
        return
    if name == "classification_totals":
        _check_classification_totals(rule, value)
        return
    if name == "route_totals":
        _check_route_totals(rule, value)
        return
    message = f"{rule.name} has no validation kind"  # pragma: no cover - table defect
    raise ReceiptValidationError(message)  # pragma: no cover


def _check_mapping(
    rule: _Rule,
    value: object,
    item_ok: Callable[[object], bool],
) -> None:
    if not isinstance(value, Mapping) or not value:
        message = f"{rule.name} must be a non-empty object"
        raise ReceiptValidationError(message)
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip():
            message = f"{rule.name} keys must be non-empty strings"
            raise ReceiptValidationError(message)
        if not item_ok(item):
            message = f"{rule.name} value for {key!r} is not of the required type"
            raise ReceiptValidationError(message)


def _check_classification_totals(rule: _Rule, value: object) -> None:
    if not isinstance(value, Mapping):
        message = f"{rule.name} must be an object"
        raise ReceiptValidationError(message)
    present = set(value)
    expected = set(RESPONSE_CLASSIFICATION_BUCKETS)
    if present != expected:
        missing = ", ".join(sorted(expected - present)) or "none"
        extra = ", ".join(sorted(present - expected)) or "none"
        message = (
            f"{rule.name} must carry exactly the buckets "
            f"{', '.join(RESPONSE_CLASSIFICATION_BUCKETS)} -- every response is in exactly one "
            f"bucket and there is no unclassified bucket (missing: {missing}; unexpected: {extra})"
        )
        raise ReceiptValidationError(message)
    for bucket, count in value.items():
        if not _is_integer(count) or _as_int(count) < 0:
            message = f"{rule.name} bucket {bucket!r} must be a non-negative integer"
            raise ReceiptValidationError(message)


def _check_route_totals(rule: _Rule, value: object) -> None:
    if not isinstance(value, Mapping) or not value:
        message = f"{rule.name} must be a non-empty object keyed by source_id"
        raise ReceiptValidationError(message)
    for source_id, totals in value.items():
        if not isinstance(source_id, str) or not source_id.strip():
            message = f"{rule.name} keys must be non-empty source identifiers"
            raise ReceiptValidationError(message)
        if not isinstance(totals, Mapping) or set(totals) != {
            "logical_request_count",
            "physical_attempt_count",
        }:
            message = (
                f"{rule.name} entry {source_id!r} must carry exactly logical_request_count and "
                f"physical_attempt_count"
            )
            raise ReceiptValidationError(message)
        for field_name, count in totals.items():
            if not _is_integer(count) or _as_int(count) < 0:
                message = f"{rule.name} entry {source_id!r} field {field_name} must be a count"
                raise ReceiptValidationError(message)


def _is_required(rule: _Rule, document: Mapping[str, object]) -> bool:
    """Whether ``rule``'s field must be present, given the rest of the document."""
    if rule.condition == "permitted":
        return False
    if rule.condition == "in_modes":
        return True
    status = document.get("completion_status")
    if rule.condition == "non_complete":
        return status != "complete"
    if rule.condition == "interrupted":
        return status == "interrupted"
    if rule.condition == "stopped_at_ceiling":
        return status == "stopped_at_ceiling"
    if rule.condition == "resumed":
        return "recovery_predecessor_receipt_id" in document
    if rule.condition == "carried_forward":
        # Decision 055 §7.2: a resume and a clean carry-in root both state what they inherit; an
        # ordinary zero-baseline fresh root states nothing and omits the field.
        #
        # A claimed *non-zero* baseline also counts as required, which is what keeps the refusal
        # accurate rather than merely present. Without it, a non-zero baseline naming no authority
        # is rejected here — for being a field present outside its condition — and the operator
        # never learns that the missing authority is the actual defect. With it, this rule is
        # satisfied and `carry_in_authority_sha256` reports the real problem. A zero baseline is
        # still refused on an ordinary root, because zero is not a carried-forward claim at all.
        carried = document.get("consumed_request_count_carried_forward")
        return (
            "recovery_predecessor_receipt_id" in document
            or "carry_in_authority_sha256" in document
            or (_is_integer(carried) and _as_int(carried) > 0)
        )
    if rule.condition == "carry_in_root":
        # Decision 055 §7.3: required only where there is no predecessor to inherit from and a
        # non-zero baseline is nonetheless claimed — which is exactly a clean carry-in root.
        carried = document.get("consumed_request_count_carried_forward")
        return (
            "recovery_predecessor_receipt_id" not in document
            and _is_integer(carried)
            and _as_int(carried) > 0
        )
    message = f"unknown condition {rule.condition!r}"  # pragma: no cover - table defect
    raise ReceiptValidationError(message)  # pragma: no cover


def _condition_text(rule: _Rule) -> str:
    return {
        "non_complete": "every non-complete completion status",
        "interrupted": "an interrupted run",
        "stopped_at_ceiling": "a run stopped at its ceiling",
        "resumed": "a resumed run",
        "carried_forward": "a resumed run or a clean carry-in root",
        "carry_in_root": "a clean carry-in root (no predecessor, non-zero carried-forward count)",
    }.get(rule.condition, "this invocation mode")


def _schema_for(document: Mapping[str, object]) -> _Schema:
    """Dispatch on the version the document declares (§12; Decision 055 §7.1).

    A reader dispatches on the version it finds. An unknown version is refused rather than assumed
    to be the current one, and an old receipt is never rewritten or upgraded in place.
    """
    version = document.get("receipt_schema_version")
    schema = _SCHEMAS.get(version) if isinstance(version, str) else None
    if schema is None:
        message = (
            f"receipt_schema_version {version!r} is not one of "
            f"{', '.join(repr(name) for name in READABLE_RECEIPT_SCHEMA_VERSIONS)}; a reader "
            f"dispatches on the version it finds and old receipts are never rewritten"
        )
        raise ReceiptValidationError(message)
    return schema


def _check_closed_field_set(document: Mapping[str, object], schema: _Schema) -> None:
    """No unknown field, and no placeholder standing in for an omission (§4, §6.8, §14)."""
    for key, value in document.items():
        rule = schema.by_name.get(key)
        if rule is None:
            message = (
                f"{key} is not a permitted {schema.version} receipt field; the permitted set is "
                f"closed and a new field requires a new accepted decision"
            )
            raise ReceiptValidationError(message)
        if value is None:
            message = (
                f"{key} is present as null; an inapplicable field is omitted, never rendered as "
                f"null or a placeholder"
            )
            raise ReceiptValidationError(message)
        if isinstance(value, str) and value.strip().casefold() in _PLACEHOLDER_STRINGS:
            message = f"{key} carries the placeholder {value!r}; omit the field instead"
            raise ReceiptValidationError(message)


def _check_class_conformance(
    document: Mapping[str, object],
    schema: _Schema,
    *,
    with_identity: bool,
) -> None:
    """Enforce the §4 table exactly: present in its modes, absent outside them."""
    mode = document["invocation_mode"]
    for rule in schema.rules:
        if rule.name == "receipt_id" and not with_identity:
            continue
        present = rule.name in document
        if mode not in rule.modes:
            if present:
                message = (
                    f"{rule.name} may not appear in a {mode!r} receipt; it is conditionally "
                    f"required only in {', '.join(sorted(rule.modes))} and is omitted elsewhere"
                )
                raise ReceiptValidationError(message)
            continue
        required = _is_required(rule, document)
        if required and not present:
            message = f"{rule.name} is required for {_condition_text(rule)} and is missing"
            raise ReceiptValidationError(message)
        if not required and present and rule.condition != "permitted":
            message = (
                f"{rule.name} is conditionally required only for {_condition_text(rule)}; it must "
                f"be omitted otherwise"
            )
            raise ReceiptValidationError(message)


def _check_accounting(document: Mapping[str, object], schema: _Schema) -> None:
    """§14 accounting, classification, timing, and zero-network consistency.

    Every vocabulary this reads comes from ``schema`` rather than from a module-level tuple, so
    the checker is shared but the vocabularies are not: Decision 094 §10.1 requires the v4
    objects to be version-scoped, and a common checker consulting a common tuple would silently
    have made them global.
    """
    mode = document["invocation_mode"]
    started = str(document["started_at_utc"])
    completed = str(document["completed_at_utc"])
    if _parse_timestamp(completed) < _parse_timestamp(started):
        message = "completed_at_utc precedes started_at_utc"
        raise ReceiptValidationError(message)

    logical = _as_int(document["actual_logical_request_count"])
    physical = _as_int(document["actual_physical_attempt_count"])

    if mode in schema.zero_network_modes and (logical or physical):
        message = (
            f"actual_logical_request_count and actual_physical_attempt_count must both be 0 in a "
            f"{mode!r} receipt; scripted responses, injected retries, and simulated cooldowns are "
            f"rehearsal facts and belong in the rehearsal evidence report, not in a receipt"
        )
        raise ReceiptValidationError(message)

    if physical < logical:
        message = (
            "actual_physical_attempt_count may not be fewer than actual_logical_request_count; "
            "one logical request costs at least one physical attempt"
        )
        raise ReceiptValidationError(message)

    ceiling = document.get("approved_request_ceiling")
    if ceiling is not None and physical > _as_int(ceiling):
        message = (
            f"actual_physical_attempt_count {physical} exceeds the approved_request_ceiling "
            f"{_as_int(ceiling)}; the ceiling is a hard bound, not a target"
        )
        raise ReceiptValidationError(message)

    # Decision 055 §7.4: in `3.0` the ceiling bounds *cumulative* consumption, so what a receipt
    # inherited and what it then placed are checked together. `actual_physical_attempt_count`
    # records this invocation's wire attempts only, so neither figure bounds the ceiling on its own.
    #
    # This rule is dispatched on the document's own version, and that is not a detail. Decision 055
    # §7.1 unfreezes the schema for a new writer version and requires existing `2.0` receipts to
    # stay byte-unchanged, valid, readable, and usable in mixed-version chains. `2.0` used
    # `consumed_request_count_carried_forward` under different semantics and was never validated
    # against a cumulative bound, so applying the new rule to old documents would retroactively
    # invalidate receipts that were correct when written — a rewrite of history by refusal rather
    # than the version dispatch the ruling calls for. A `2.0` receipt therefore keeps exactly the
    # bound it always had, checked above.
    carried = document.get("consumed_request_count_carried_forward")
    is_v3 = document.get("receipt_schema_version") == RECEIPT_SCHEMA_VERSION
    if is_v3 and ceiling is not None and carried is not None:
        cumulative = _as_int(carried) + physical
        if cumulative > _as_int(ceiling):
            message = (
                f"{_as_int(carried)} carried-forward plus {physical} actual physical attempt(s) is "
                f"{cumulative}, which exceeds the approved_request_ceiling {_as_int(ceiling)}; the "
                f"ceiling bounds cumulative consumption and is never reset by a new invocation"
            )
            raise ReceiptValidationError(message)

    planned_routes = document.get("planned_per_route")
    planned_total = document.get("planned_logical_request_count")
    if isinstance(planned_routes, Mapping) and planned_total is not None:
        summed = sum(_as_int(value) for value in planned_routes.values())
        if summed != _as_int(planned_total):
            message = (
                f"planned_per_route sums to {summed} but planned_logical_request_count is "
                f"{_as_int(planned_total)}"
            )
            raise ReceiptValidationError(message)

    actual_routes = document.get("actual_per_route")
    if isinstance(actual_routes, Mapping):
        summed_logical = sum(
            _as_int(totals["logical_request_count"]) for totals in actual_routes.values()
        )
        summed_physical = sum(
            _as_int(totals["physical_attempt_count"]) for totals in actual_routes.values()
        )
        if (summed_logical, summed_physical) != (logical, physical):
            message = (
                f"actual_per_route sums to {summed_logical} logical and {summed_physical} physical "
                f"but the receipt reports {logical} and {physical}"
            )
            raise ReceiptValidationError(message)

    classification = document.get("response_classification_totals")
    if isinstance(classification, Mapping):
        classified = sum(_as_int(count) for count in classification.values())
        if classified > physical:
            message = (
                f"response_classification_totals account for {classified} responses but only "
                f"{physical} physical attempts were placed; a response cannot precede its attempt"
            )
            raise ReceiptValidationError(message)

    remaining = document.get("remaining_planned_logical_request_count")
    if remaining is not None and _as_int(remaining) <= 0:
        message = (
            "remaining_planned_logical_request_count must be positive when a live run stops at its "
            "ceiling; a run with nothing left unattempted did not stop at a ceiling"
        )
        raise ReceiptValidationError(message)

    reason_code = document.get("reason_code")
    if reason_code is not None:
        registered = schema.reason_codes if schema.reason_codes is not None else set(REASON_CODES)
        if reason_code not in registered:
            registry = (
                f"the closed {schema.version} vocabulary ({', '.join(sorted(schema.reason_codes))})"
                if schema.reason_codes is not None
                else "disclosure_drift.reasons"
            )
            message = (
                f"reason_code {reason_code!r} is not registered in {registry}; an unregistered "
                f"code is a defect, not a new code"
            )
            raise ReceiptValidationError(message)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate(document: Mapping[str, object], *, with_identity: bool) -> None:
    """Run §14 in a fixed order, most severe first.

    Prohibited content is scanned before the identity is recomputed, because a receipt carrying a
    credential is a disclosure problem whether or not its digest happens to agree.
    """
    schema = _schema_for(document)

    _check_closed_field_set(document, schema)
    scan_for_prohibited_content(document)

    for name in ("invocation_mode", "phase", "completion_status"):
        if name not in document:
            message = f"{name} is required in every receipt and is missing"
            raise ReceiptValidationError(message)
        _check_kind(schema.by_name[name], document[name])

    _check_class_conformance(document, schema, with_identity=with_identity)

    for key, value in document.items():
        _check_kind(schema.by_name[key], value)

    _check_accounting(document, schema)

    if with_identity:
        expected = compute_receipt_id(document)
        if document["receipt_id"] != expected:
            message = (
                "receipt_id does not recompute over its excluding preimage; the receipt was "
                "altered after it was written"
            )
            raise ReceiptValidationError(message)


def validate_receipt_document(document: Mapping[str, object]) -> None:
    """Validate a complete receipt document, ``receipt_id`` included. Fail-closed (§14)."""
    _validate(document, with_identity=True)


# --------------------------------------------------------------------------- #
# Typed construction
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionReceipt:
    """One validated execution receipt.

    Construction validates: an invalid receipt cannot be built, so there is no window in which an
    unvalidated receipt could be serialized, written, or quoted. ``receipt_schema_version`` is
    supplied by this module and ``receipt_id`` is derived, so neither is a constructor argument --
    a caller cannot label a v2 receipt v1 or assert an identity it did not compute.
    """

    command_name: str
    command_version: str
    phase: str
    invocation_mode: str
    configuration_fingerprint: str
    migration_chain_head: str
    started_at_utc: str
    completed_at_utc: str
    elapsed_seconds: float
    actual_logical_request_count: int
    actual_physical_attempt_count: int
    completion_status: str

    source_registry_version: str | None = None
    index_plan_policy_version: str | None = None
    request_plan_schema_version: str | None = None
    quota_policy_version: str | None = None
    joint_selector_policy_version: str | None = None
    replacement_signature_policy_version: str | None = None
    manifest_hash_policy_version: str | None = None
    selection_input_schema_version: str | None = None
    parser_versions: Mapping[str, str] | None = None
    cohort_definition_digest: str | None = None

    acquisition_window: str | None = None
    request_plan_id: str | None = None
    request_plan_sha256: str | None = None
    approved_request_ceiling: int | None = None
    planned_logical_request_count: int | None = None
    maximum_physical_attempt_count: int | None = None
    planned_per_route: Mapping[str, int] | None = None

    actual_per_route: Mapping[str, Mapping[str, int]] | None = None
    response_classification_totals: Mapping[str, int] | None = None
    status_code_totals: Mapping[str, int] | None = None
    raw_object_count: int | None = None
    duplicate_object_count: int | None = None
    cache_hit_count: int | None = None
    not_modified_count: int | None = None
    quarantined_object_count: int | None = None
    redirect_hop_count: int | None = None
    cooldown_count: int | None = None
    remaining_planned_logical_request_count: int | None = None

    schema_drift_outcome: str | None = None
    schema_drift_event_count: int | None = None

    resulting_snapshot_id: str | None = None
    resulting_selection_run_id: str | None = None
    resulting_selection_result_sha256: str | None = None
    resulting_root_manifest_sha256: str | None = None
    resulting_manifest_id: str | None = None

    reason_code: str | None = None
    reason_detail: str | None = None
    interruption_state: str | None = None
    recovery_predecessor_receipt_id: str | None = None
    consumed_request_count_carried_forward: int | None = None
    carry_in_authority_sha256: str | None = None
    rehearsal_evidence_reference: str | None = None

    def __post_init__(self) -> None:
        _validate(self.preimage_document(), with_identity=False)

    def preimage_document(self) -> dict[str, object]:
        """The §13 preimage: every field except ``receipt_id``, omissions omitted."""
        document: dict[str, object] = {"receipt_schema_version": RECEIPT_SCHEMA_VERSION}
        for name in _CALLER_FIELDS:
            value = getattr(self, name)
            if value is None:
                continue
            document[name] = _jsonable(value)
        return document

    @property
    def receipt_id(self) -> str:
        """The single integrity identity (§13). Never random, never a timestamp."""
        return hashlib.sha256(canonical_bytes(self.preimage_document())).hexdigest()

    def as_document(self) -> dict[str, object]:
        """The complete receipt document, ``receipt_id`` included."""
        document = self.preimage_document()
        document["receipt_id"] = self.receipt_id
        return document

    def canonical_bytes(self) -> bytes:
        """The bytes written to the evidence root (§6)."""
        return canonical_bytes(self.as_document())


#: The v4 caller field set, derived from the v4 table alone. Kept separate from
#: :data:`_CALLER_FIELDS` so a v3 field can never be serialized into a v4 preimage.
_CALLER_FIELDS_V4: Final = _SCHEMA_V4.caller_fields


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionReceiptV4:
    """One validated ``m3-execution-receipt/4.0`` receipt (Decision 094 §10.1).

    A **separate class**, not a mode of :class:`ExecutionReceipt`. That is the isolation the
    ruling asks for made structural: this type cannot express a v3 field, :class:`ExecutionReceipt`
    cannot express a v4 mode, and neither can be relabelled as the other because both write their
    own ``receipt_schema_version``. Existing commands keep emitting ``3.0`` untouched; only the
    two Decision 094 operator commands construct this.

    Construction validates, exactly as v3 does, so an invalid v4 receipt cannot be built,
    serialized, written, or quoted.
    """

    command_name: str
    command_version: str
    invocation_mode: str
    configuration_fingerprint: str
    migration_chain_head: str
    started_at_utc: str
    completed_at_utc: str
    elapsed_seconds: float
    completion_status: str

    #: Fixed at zero by :data:`ZERO_NETWORK_MODES_V4`. Present as fields rather than as literals
    #: so a receipt states its accounting rather than having it assumed, and so the zero-network
    #: check has something real to refuse.
    actual_logical_request_count: int = 0
    actual_physical_attempt_count: int = 0

    parser_versions: Mapping[str, str] | None = None
    cohort_definition_digest: str | None = None

    reason_code: str | None = None
    reason_detail: str | None = None
    interruption_state: str | None = None
    recovery_predecessor_receipt_id: str | None = None

    #: Decision 094 §10.1 item 1: the accepted real-execution phase, not a new project phase.
    #: Fixed rather than supplied, so a caller cannot label a PRE-E0 receipt with another phase.
    phase: ClassVar[str] = PHASE_V4

    def __post_init__(self) -> None:
        _validate(self.preimage_document(), with_identity=False)

    def preimage_document(self) -> dict[str, object]:
        """The §13 preimage: every field except ``receipt_id``, omissions omitted."""
        document: dict[str, object] = {
            "receipt_schema_version": RECEIPT_SCHEMA_VERSION_V4,
            "phase": PHASE_V4,
        }
        for name in _CALLER_FIELDS_V4:
            if name == "phase":
                continue
            value = getattr(self, name)
            if value is None:
                continue
            document[name] = _jsonable(value)
        return document

    @property
    def receipt_id(self) -> str:
        """The single integrity identity (§13). Never random, never a timestamp."""
        return hashlib.sha256(canonical_bytes(self.preimage_document())).hexdigest()

    def as_document(self) -> dict[str, object]:
        """The complete receipt document, ``receipt_id`` included."""
        document = self.preimage_document()
        document["receipt_id"] = self.receipt_id
        return document

    def canonical_bytes(self) -> bytes:
        """The bytes written into the Decision 094 run namespace (§6)."""
        return canonical_bytes(self.as_document())


# --------------------------------------------------------------------------- #
# §7 storage: outside the repository, content-derived, write-once
# --------------------------------------------------------------------------- #
def receipts_directory(evidence_root: str | Path) -> Path:
    """The directory dedicated to receipts inside an evidence root (§7.1)."""
    return Path(evidence_root) / "receipts"


def write_receipt(
    receipt: ExecutionReceipt,
    *,
    evidence_root: str | Path,
    repository_root: str | Path,
) -> Path:
    """Write ``receipt`` once, under a content-derived name, outside the checkout.

    The evidence root is revalidated here rather than trusted from the caller, so no command can
    write a receipt into the public repository even by mistake. Rewriting a byte-identical receipt
    is a collision by identity and succeeds unchanged (§7.2); any other rewrite is refused, because
    a receipt is immutable and a correction is a new receipt (§7.5).
    """
    resolved = require_external_evidence_root(evidence_root, repository_root)
    directory = receipts_directory(resolved)
    payload = receipt.canonical_bytes()
    path = directory / f"receipt-{receipt.receipt_id}.json"

    if path.exists():
        if path.read_bytes() == payload:
            return path
        message = (
            f"a different receipt already exists at the content-derived name {path.name}; a "
            f"receipt is immutable and a correction is a new receipt, never an edit"
        )
        raise ReceiptWriteError(message)

    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / f".{path.name}.partial"
    temporary.write_bytes(payload)
    temporary.replace(path)
    return path


def inspect_receipt(path: str | Path) -> dict[str, object]:
    """Read, validate, and return a receipt document without modifying anything (§7, §14).

    Validation is repeated at inspection rather than trusted from construction: the file may have
    been altered, truncated, or reserialized since it was written.
    """
    payload = Path(path).read_bytes()
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        message = f"receipt at {Path(path).name} is not readable UTF-8 JSON: {exc}"
        raise ReceiptValidationError(message) from exc
    if not isinstance(document, dict):
        message = f"receipt at {Path(path).name} is not a JSON object"
        raise ReceiptValidationError(message)

    validate_receipt_document(document)

    if canonical_bytes(document) != payload:
        message = (
            "re-serializing the parsed receipt does not reproduce the file byte-for-byte; the "
            "stored bytes are not in canonical form"
        )
        raise ReceiptValidationError(message)
    return document


# --------------------------------------------------------------------------- #
# Predecessor location: the accepted receipt artifact locations, and only those
# --------------------------------------------------------------------------- #
#: The accepted per-run receipt artifact name. ``--receipt-out`` names a receipt explicitly, and the
#: accepted M3.2 convention gives each run its own namespace holding one receipt under this fixed
#: name -- ``runs/m3_2a_clean_carry_in/execution_receipt.json`` (Decision 061 §7.3) and the
#: Decision 062 continuation namespace beside it. A receipt written this way is **not** reachable by
#: the content-derived name, which is the whole reason this module has to know the convention.
OPERATOR_RECEIPT_FILENAME: Final = "execution_receipt.json"

#: The evidence-root directory holding one namespace per run. Discovery descends exactly one level
#: into it -- never recursively, and never into the raw store -- so the search is bounded and its
#: cost does not grow with acquired evidence.
RUN_NAMESPACE_DIRNAME: Final = "runs"


class ReceiptChainResolutionError(ReceiptValidationError):
    """A recorded predecessor did not resolve to exactly one valid receipt.

    Deliberately a :class:`ReceiptValidationError`: every existing caller already treats that as a
    stop, so a resolution refusal cannot be narrower than the broken-chain condition receipt spec
    §11.4 makes a stop condition. Refusal is the only outcome -- no receipt is ever synthesized,
    copied, renamed, or relocated to make a chain resolve.
    """


def content_derived_receipt_name(receipt_id: str) -> str:
    """The §7.2 content-derived filename for one receipt identity."""
    return f"receipt-{receipt_id}.json"


def _refuse_symlinked_descent(root: Path, candidate: Path) -> None:
    """Refuse a candidate that is, or is reached through, a symbolic link below ``root``.

    ``root`` is already fully resolved by :func:`require_external_evidence_root`, so every component
    strictly below it is a real name unless someone placed a link there. The walk is **lexical** on
    purpose: resolving first would follow every link and leave nothing to detect.
    """
    depth = len(root.parts)
    current = candidate
    while len(current.parts) > depth and current.parent != current:
        if current.is_symlink():
            message = (
                f"a component of the candidate receipt {candidate.name!r} is a symbolic link; "
                f"receipts are addressed by real paths only"
            )
            raise ReceiptChainResolutionError(message)
        current = current.parent


def _refuse_escaping_candidate(root: Path, candidate: Path) -> None:
    """Refuse a candidate whose resolved path leaves the governed evidence root.

    Kept independent of :func:`_refuse_symlinked_descent` rather than folded into it. The symlink
    walk refuses a *mechanism*; this refuses the *outcome*, so a path that escapes by any means the
    walk does not model is still refused instead of silently read.
    """
    resolved_root = Path(os.path.realpath(root))
    resolved = Path(os.path.realpath(candidate))
    if resolved != resolved_root and resolved_root not in resolved.parents:
        message = (
            f"the candidate receipt {candidate.name!r} resolves outside the evidence root; "
            f"predecessor resolution never reads a receipt the root does not govern"
        )
        raise ReceiptChainResolutionError(message)


def _search_directories(evidence_root: Path) -> tuple[Path, ...]:
    """The accepted receipt directories, in fixed deterministic order.

    Namespaces are sorted by name so the order does not depend on directory iteration order, which
    is filesystem-dependent and would make an ambiguity refusal depend on which candidate happened
    to be seen first.
    """
    directories = [receipts_directory(evidence_root)]
    namespaces = evidence_root / RUN_NAMESPACE_DIRNAME
    if namespaces.is_symlink():
        message = (
            f"the {RUN_NAMESPACE_DIRNAME!r} directory of the evidence root is a symbolic link; "
            f"run namespaces are addressed by real paths only"
        )
        raise ReceiptChainResolutionError(message)
    if namespaces.is_dir():
        directories.extend(
            sorted(
                (child for child in namespaces.iterdir() if child.is_dir()),
                key=lambda child: child.name,
            )
        )
    return tuple(directories)


def _identified_candidate(
    candidate: Path, receipt_id: str, *, name_asserts_identity: bool
) -> dict[str, object] | None:
    """Load one candidate and return it only if it *is* the requested receipt.

    A file at the content-derived name claims an identity, so a document that contradicts it is a
    defect and refuses. ``execution_receipt.json`` claims nothing, so a document with another
    identity is simply another run's receipt and is skipped -- that is what keeps an unrelated
    namespace from blocking a lawful chain.
    """
    try:
        document = inspect_receipt(candidate)
    except (OSError, ReceiptValidationError):
        if name_asserts_identity:
            raise
        # A malformed operator-named receipt can never satisfy the requested identity, so it is
        # skipped rather than raised: an unrelated damaged file in another namespace must not
        # decide the fate of a chain that does not reference it.
        return None

    if str(document["receipt_id"]) == receipt_id:
        return document
    if name_asserts_identity:
        message = (
            f"the receipt stored at the content-derived name for "
            f"{receipt_id[:12]}… records a different receipt_id; a receipt's name and its "
            f"validated identity may never disagree"
        )
        raise ReceiptChainResolutionError(message)
    return None


def resolve_predecessor_receipt(
    predecessor_receipt_id: str,
    *,
    head_directory: Path,
    evidence_root: Path | None = None,
) -> tuple[Path, dict[str, object]]:
    """Locate the one valid receipt whose validated identity is ``predecessor_receipt_id``.

    A chain head is written where its operator named it. ``--receipt-out`` has always allowed that,
    and the accepted M3.2 convention gives every run its own namespace, so the T7 continuation's
    predecessor sits in ``runs/m3_2a_clean_carry_in/`` while the head sits in
    ``runs/m3_2_decision_062_sic_continuation/``. Looking only beside the head therefore cannot find
    a lawful predecessor, and the chain reads as broken when it is intact.

    Resolution is by **recorded identity**, never by a caller-supplied replacement receipt: every
    candidate goes through the ordinary loader, schema validation, canonical-form check, and an
    exact ``receipt_id`` equality test, and a candidate that fails any of them is not the
    predecessor. The search is confined to the accepted receipt artifact locations beneath the
    governed evidence root, in this fixed order:

    1. ``<head directory>/receipt-<id>.json`` -- the existing accepted same-directory behaviour,
       tried first and semantically unchanged, so no chain that resolves today resolves differently;
    2. ``receipts/`` -- the §7.1 directory dedicated to receipts;
    3. ``runs/<namespace>/`` -- each run namespace, sorted by name,

    probing only the two accepted receipt filenames in each. Arbitrary JSON is never treated as a
    receipt, and nothing is copied, moved, renamed, rewritten, or synthesized.

    Args:
        predecessor_receipt_id: the identity the head receipt recorded.
        head_directory: the directory holding the chain head, searched first.
        evidence_root: the resolved governed evidence root that bounds cross-namespace discovery.
            ``None`` disables discovery entirely and leaves step 1 as the only behaviour, which is
            what a caller that cannot prove a root must get.

    Returns:
        The candidate's path and its validated document.

    Raises:
        ReceiptChainResolutionError: nothing matched, more than one distinct receipt matched, or a
            candidate was a symbolic link, escaped the root, or contradicted its own name.
        ReceiptValidationError: the receipt at the content-derived name exists but is not valid.
    """
    name = content_derived_receipt_name(predecessor_receipt_id)

    beside = Path(head_directory) / name
    if beside.is_symlink():
        message = (
            f"the receipt beside the chain head at the content-derived name for "
            f"{predecessor_receipt_id[:12]}… is a symbolic link; receipts are addressed by "
            f"real paths only"
        )
        raise ReceiptChainResolutionError(message)
    if beside.exists():
        # Unchanged: a malformed receipt at the name that claims this identity is a defect of that
        # receipt, never a reason to go looking for a different file that might be more agreeable.
        document = _identified_candidate(beside, predecessor_receipt_id, name_asserts_identity=True)
        if document is not None:
            return beside, document

    if evidence_root is None:
        message = (
            f"recovery_predecessor_receipt_id {predecessor_receipt_id[:12]}… does not resolve "
            f"to a readable receipt beside the chain head, and no evidence root was supplied to "
            f"search the accepted receipt locations "
            f"[category=no_evidence_root_for_discovery; candidate files examined=1; "
            f"valid matches=0; search scopes=<head directory>]"
        )
        raise ReceiptChainResolutionError(message)

    root = Path(evidence_root)
    matches: list[tuple[Path, dict[str, object]]] = []
    examined = 0
    scopes: list[str] = []
    for directory in _search_directories(root):
        scope = _relative_scope(root, directory)
        if scope not in scopes:
            scopes.append(scope)
        for filename, asserts in ((name, True), (OPERATOR_RECEIPT_FILENAME, False)):
            candidate = directory / filename
            _refuse_symlinked_descent(root, candidate)
            if not candidate.is_file():
                continue
            _refuse_escaping_candidate(root, candidate)
            if candidate == beside:
                continue  # already tried above; counting it twice would invent an ambiguity
            examined += 1
            document = _identified_candidate(
                candidate, predecessor_receipt_id, name_asserts_identity=asserts
            )
            if document is not None:
                matches.append((candidate, document))

    if not matches:
        # Sanitized on purpose, and every element earns its place: an operator staring at a broken
        # chain needs to know *which* identity failed, that the search actually ran, how much of the
        # governed tree it covered, and that the answer was zero rather than ambiguous. What it must
        # never carry is where the evidence root is, so the scopes below are relative names only and
        # the absolute root never appears. No SEC identity, no header, no response body reaches
        # here — this function has never seen one.
        message = (
            f"recovery_predecessor_receipt_id {predecessor_receipt_id[:12]}… does not resolve "
            f"to a readable receipt in any accepted receipt location beneath the evidence root "
            f"[category=no_candidate_matched; candidate files examined={examined}; "
            f"valid matches=0; search scopes={', '.join(scopes)}]"
        )
        raise ReceiptChainResolutionError(message)

    # Two files carrying the same validated identity are byte-identical: `receipt_id` is the digest
    # of the canonical preimage and `inspect_receipt` has already proved each file equals the
    # canonical form of what it parsed to, so equal identity forces equal bytes. Rather than rely on
    # that argument, the bytes are compared. Byte-identical copies are one receipt at two paths --
    # exactly the collision §7.2 already resolves by identity when a receipt is rewritten -- and the
    # first in the fixed search order is returned. Anything else is two different receipts claiming
    # one identity, which is refused: choosing between them is not this function's to make.
    payloads = {canonical_bytes(document) for _, document in matches}
    if len(payloads) > 1:
        message = (
            f"recovery_predecessor_receipt_id {predecessor_receipt_id[:12]}… resolves to "
            f"{len(matches)} candidate receipts whose contents differ; a receipt identity that "
            f"names more than one distinct receipt is refused, never chosen between "
            f"[category=ambiguous_distinct_candidates; candidate files examined={examined}; "
            f"valid matches={len(matches)}; distinct receipts={len(payloads)}; "
            f"search scopes={', '.join(scopes)}]"
        )
        raise ReceiptChainResolutionError(message)
    return matches[0]


def _relative_scope(root: Path, directory: Path) -> str:
    """One searched directory named relative to the evidence root, never absolutely.

    A diagnostic naming ``receipts/`` or ``runs/<namespace>/`` tells an operator exactly where the
    search looked; the same diagnostic naming the resolved root would publish the private evidence
    location into a message that reaches logs and reports. A directory that is somehow not beneath
    the root is reported as the fixed string below rather than by its path, so no fallback branch
    can leak one either.
    """
    try:
        relative = directory.relative_to(root)
    except ValueError:
        return "<outside the evidence root>"
    return str(relative) if str(relative) != "." else "<evidence root>"
