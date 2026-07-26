"""SEC schema-drift policy (assignment section 19).

Unknown extra fields are retained and logged. A missing required field never
receives a silent default: it raises so the caller stops and preserves evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from disclosure_drift.errors import SchemaDriftError

__all__ = [
    "DriftEvent",
    "DriftKind",
    "DriftReport",
    "inspect_payload",
]

DriftKind = Literal[
    "unknown_field_retained",
    "required_field_missing",
    "type_changed",
    "unexpected_null",
    "malformed_nested_array",
    "new_historical_file_reference",
]


@dataclass(frozen=True, slots=True)
class DriftEvent:
    """One observed schema difference."""

    kind: DriftKind
    field_path: str
    detail: str


@dataclass(frozen=True, slots=True)
class DriftReport:
    """Outcome of inspecting one payload against an expected shape."""

    source_class: str
    events: tuple[DriftEvent, ...]
    retained_unknown_fields: tuple[str, ...]

    @property
    def blocking_events(self) -> tuple[DriftEvent, ...]:
        """Events that must stop processing."""
        return tuple(
            event
            for event in self.events
            if event.kind
            in {
                "required_field_missing",
                "unexpected_null",
                "type_changed",
                "malformed_nested_array",
            }
        )

    @property
    def reason_codes(self) -> tuple[str, ...]:
        """Reason codes implied by this report."""
        return ("SEC_SCHEMA_REQUIRED_FIELD_MISSING",) if self.blocking_events else ()

    def require_usable(self) -> None:
        """Raise when a required field is missing or structurally invalid.

        Raises:
            SchemaDriftError: at least one blocking event was observed.
        """
        blocking = self.blocking_events
        if not blocking:
            return
        detail = "; ".join(f"{event.field_path}: {event.detail}" for event in blocking)
        message = (
            f"{self.source_class} payload is unusable: {detail}\n"
            "No default is applied. Preserve the payload and request review."
        )
        raise SchemaDriftError(message)


def inspect_payload(
    payload: Mapping[str, Any],
    *,
    source_class: str,
    required_fields: Mapping[str, type | tuple[type, ...]],
    optional_fields: Sequence[str] = (),
    array_fields: Sequence[str] = (),
) -> DriftReport:
    """Compare a payload against an expected shape without mutating it."""
    events: list[DriftEvent] = []

    for name, expected in required_fields.items():
        if name not in payload:
            events.append(
                DriftEvent("required_field_missing", name, "required field absent from payload")
            )
            continue
        value = payload[name]
        if value is None:
            events.append(DriftEvent("unexpected_null", name, "required field is null"))
            continue
        if not isinstance(value, expected):
            events.append(
                DriftEvent(
                    "type_changed",
                    name,
                    f"expected {_type_names(expected)}, observed {type(value).__name__}",
                )
            )

    for name in array_fields:
        if name not in payload:
            continue
        value = payload[name]
        if not isinstance(value, list):
            events.append(
                DriftEvent(
                    "malformed_nested_array",
                    name,
                    f"expected a list, observed {type(value).__name__}",
                )
            )

    known = set(required_fields) | set(optional_fields) | set(array_fields)
    unknown = tuple(sorted(set(payload) - known))
    for name in unknown:
        events.append(
            DriftEvent("unknown_field_retained", name, "unknown field retained and logged")
        )

    return DriftReport(
        source_class=source_class,
        events=tuple(events),
        retained_unknown_fields=unknown,
    )


def _type_names(expected: type | tuple[type, ...]) -> str:
    if isinstance(expected, tuple):
        return " or ".join(item.__name__ for item in expected)
    return expected.__name__
