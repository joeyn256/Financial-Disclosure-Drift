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
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.evidence_paths import require_external_evidence_root
from disclosure_drift.reasons import REASON_CODES

__all__ = [
    "COMPLETION_STATUSES",
    "INTERRUPTION_STATES",
    "INVOCATION_MODES",
    "PHASES",
    "RECEIPT_SCHEMA_VERSION",
    "RESPONSE_CLASSIFICATION_BUCKETS",
    "SCHEMA_DRIFT_OUTCOMES",
    "ZERO_NETWORK_MODES",
    "ExecutionReceipt",
    "ProhibitedReceiptContentError",
    "ReceiptError",
    "ReceiptValidationError",
    "ReceiptWriteError",
    "canonical_bytes",
    "compute_receipt_id",
    "inspect_receipt",
    "receipts_directory",
    "scan_for_prohibited_content",
    "validate_receipt_document",
    "write_receipt",
]

#: The schema this module implements. Decision 028 §9 fixes the v2 field set; a new major version
#: requires a new accepted decision, so this is a constant and not a parameter (spec §12).
RECEIPT_SCHEMA_VERSION: Final = "m3-execution-receipt/2.0"

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

_RULES_BY_NAME: Final[Mapping[str, _Rule]] = {rule.name: rule for rule in _RULES}

#: Field names the caller supplies. ``receipt_schema_version`` is written by this module and
#: ``receipt_id`` is derived, so neither is a constructor argument.
_CALLER_FIELDS: Final = tuple(
    rule.name for rule in _RULES if rule.name not in {"receipt_schema_version", "receipt_id"}
)


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
            for fragment in _PROHIBITED_KEY_FRAGMENTS:
                if fragment in lowered_key:
                    raise _refuse(child, f"the field name carries a prohibited marker {fragment!r}")
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
    message = f"unknown condition {rule.condition!r}"  # pragma: no cover - table defect
    raise ReceiptValidationError(message)  # pragma: no cover


def _condition_text(rule: _Rule) -> str:
    return {
        "non_complete": "every non-complete completion status",
        "interrupted": "an interrupted run",
        "stopped_at_ceiling": "a run stopped at its ceiling",
        "resumed": "a resumed run",
    }.get(rule.condition, "this invocation mode")


def _check_closed_field_set(document: Mapping[str, object]) -> None:
    """No unknown field, and no placeholder standing in for an omission (§4, §6.8, §14)."""
    for key, value in document.items():
        rule = _RULES_BY_NAME.get(key)
        if rule is None:
            message = (
                f"{key} is not a permitted receipt field; the permitted set is closed and a new "
                f"field requires a new accepted decision"
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


def _check_class_conformance(document: Mapping[str, object], *, with_identity: bool) -> None:
    """Enforce the §4 table exactly: present in its modes, absent outside them."""
    mode = document["invocation_mode"]
    for rule in _RULES:
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


def _check_accounting(document: Mapping[str, object]) -> None:
    """§14 accounting, classification, timing, and zero-network consistency."""
    mode = document["invocation_mode"]
    started = str(document["started_at_utc"])
    completed = str(document["completed_at_utc"])
    if _parse_timestamp(completed) < _parse_timestamp(started):
        message = "completed_at_utc precedes started_at_utc"
        raise ReceiptValidationError(message)

    logical = _as_int(document["actual_logical_request_count"])
    physical = _as_int(document["actual_physical_attempt_count"])

    if mode in ZERO_NETWORK_MODES and (logical or physical):
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
    if reason_code is not None and reason_code not in REASON_CODES:
        message = (
            f"reason_code {reason_code!r} is not registered in disclosure_drift.reasons; an "
            f"unregistered code is a defect, not a new code"
        )
        raise ReceiptValidationError(message)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate(document: Mapping[str, object], *, with_identity: bool) -> None:
    """Run §14 in a fixed order, most severe first.

    Prohibited content is scanned before the identity is recomputed, because a receipt carrying a
    credential is a disclosure problem whether or not its digest happens to agree.
    """
    version = document.get("receipt_schema_version")
    if version != RECEIPT_SCHEMA_VERSION:
        message = (
            f"receipt_schema_version {version!r} is not {RECEIPT_SCHEMA_VERSION!r}; a reader "
            f"dispatches on the version it finds and old receipts are never rewritten"
        )
        raise ReceiptValidationError(message)

    _check_closed_field_set(document)
    scan_for_prohibited_content(document)

    for name in ("invocation_mode", "phase", "completion_status"):
        if name not in document:
            message = f"{name} is required in every receipt and is missing"
            raise ReceiptValidationError(message)
        _check_kind(_RULES_BY_NAME[name], document[name])

    _check_class_conformance(document, with_identity=with_identity)

    for key, value in document.items():
        _check_kind(_RULES_BY_NAME[key], value)

    _check_accounting(document)

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
