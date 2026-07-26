"""The single authoritative parser-version table.

**The parser implementation owns its identifier and version.** Every consumer — the
source registry, persisted parser runs, snapshot lineage, the census plan, conditional
reuse, and version comparison — obtains the value from here rather than declaring its
own copy. A version string is written down exactly once, in the module that implements
the parser, and this table collects those declarations by importing them.

That is why :data:`PARSER_VERSIONS` is built from the parser modules' own constants
rather than typed out again: a second hand-maintained copy is precisely the drift this
module exists to prevent. Before this table existed, the source registry carried its own
``parser_version`` strings and three of them had silently fallen behind their
implementations (``submissions-json`` at 1.0 against 1.1, and both calendar parsers at
1.0 against 2.0), so persisted provenance recorded a version that no longer described
the code that produced it.

Import direction matters: nothing here imports the source registry, so the registry can
import this module without a cycle.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.sec.parsers.calendar import (
    ANNOUNCEMENT_PARSER_ID,
    ANNOUNCEMENT_PARSER_VERSION,
    CALENDAR_PARSER_ID,
    CALENDAR_PARSER_VERSION,
)
from disclosure_drift.sec.parsers.full_index import (
    FULL_INDEX_PARSER_ID,
    FULL_INDEX_PARSER_VERSION,
)
from disclosure_drift.sec.parsers.historical import PARSER_ID as HISTORICAL_PARSER_ID
from disclosure_drift.sec.parsers.historical import (
    PARSER_VERSION as HISTORICAL_PARSER_VERSION,
)
from disclosure_drift.sec.parsers.sic import PARSER_ID as SIC_PARSER_ID
from disclosure_drift.sec.parsers.sic import PARSER_VERSION as SIC_PARSER_VERSION
from disclosure_drift.sec.parsers.submissions import PARSER_ID as SUBMISSIONS_PARSER_ID
from disclosure_drift.sec.parsers.submissions import (
    PARSER_VERSION as SUBMISSIONS_PARSER_VERSION,
)
from disclosure_drift.sec.parsers.tickers import (
    EXCHANGE_PARSER_ID,
    EXCHANGE_PARSER_VERSION,
    TICKER_PARSER_ID,
    TICKER_PARSER_VERSION,
)

__all__ = [
    "PARSER_VERSIONS",
    "ParserVersionError",
    "parser_version_for",
    "require_parser_version",
    "versions_agree",
]


class ParserVersionError(DisclosureDriftError):
    """Raised when a parser identity is unknown or a recorded version disagrees."""


_DECLARED: Final[tuple[tuple[str, str], ...]] = (
    (SUBMISSIONS_PARSER_ID, SUBMISSIONS_PARSER_VERSION),
    (HISTORICAL_PARSER_ID, HISTORICAL_PARSER_VERSION),
    (TICKER_PARSER_ID, TICKER_PARSER_VERSION),
    (EXCHANGE_PARSER_ID, EXCHANGE_PARSER_VERSION),
    (SIC_PARSER_ID, SIC_PARSER_VERSION),
    (CALENDAR_PARSER_ID, CALENDAR_PARSER_VERSION),
    (ANNOUNCEMENT_PARSER_ID, ANNOUNCEMENT_PARSER_VERSION),
    (FULL_INDEX_PARSER_ID, FULL_INDEX_PARSER_VERSION),
)

PARSER_VERSIONS: Final[Mapping[str, str]] = MappingProxyType(dict(_DECLARED))
"""Authoritative parser version for each parser identifier."""


def parser_version_for(parser_id: str) -> str:
    """Return the authoritative version for ``parser_id``.

    Raises:
        ParserVersionError: the parser identifier is not implemented. There is no
            default: an unknown parser must never receive a plausible-looking version.
    """
    try:
        return PARSER_VERSIONS[parser_id]
    except KeyError:
        known = ", ".join(sorted(PARSER_VERSIONS))
        message = (
            f"parser {parser_id!r} has no implementation declaring a version. "
            f"Implemented parsers: {known}."
        )
        raise ParserVersionError(message) from None


def versions_agree(parser_id: str, recorded_version: str | None) -> bool:
    """Whether ``recorded_version`` matches the implementation's current version.

    ``None`` never agrees: an observation with no recorded parser version cannot be
    proved compatible, so it is not reusable.
    """
    if recorded_version is None:
        return False
    return recorded_version == PARSER_VERSIONS.get(parser_id)


def require_parser_version(
    parser_id: str,
    recorded_version: str | None,
    *,
    context: str = "parser run",
) -> str:
    """Return the authoritative version, or fail closed on disagreement.

    Called before a parser run is persisted and before a preserved result is reused, so
    a stale or mismatched version stops the work rather than being written into
    provenance or silently trusted.

    Raises:
        ParserVersionError: the identifier is unknown, or the recorded version differs
            from the implementation's.
    """
    authoritative = parser_version_for(parser_id)
    if recorded_version is not None and recorded_version != authoritative:
        message = (
            f"{context} declares parser version {recorded_version!r} but the "
            f"{parser_id!r} implementation is {authoritative!r}. Provenance would record "
            "a version that did not produce the result, so the operation is refused. "
            "Reparse with the current implementation instead of reusing the older result."
        )
        raise ParserVersionError(message)
    return authoritative
