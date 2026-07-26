"""Parsers for approved official SEC sources.

Each parser reads one immutable source observation and produces parsed source
records that keep the source's own identifiers, field names, and unknown fields. The
census normalizes those records; the parsers never write canonical registrant tables
directly, and never merge CIK identities.
"""

from __future__ import annotations

from disclosure_drift.sec.parsers.base import (
    PARSER_LAYER_VERSION,
    ParsedRecord,
    ParseOutcome,
    QuarantinedRecord,
    RecordLocation,
    merge_outcomes,
    record_hash,
)
from disclosure_drift.sec.parsers.calendar import (
    parse_calendar_announcement,
    parse_edgar_calendar,
)
from disclosure_drift.sec.parsers.historical import parse_historical_submissions
from disclosure_drift.sec.parsers.sic import parse_sic_reference
from disclosure_drift.sec.parsers.submissions import parse_submissions_document
from disclosure_drift.sec.parsers.tickers import (
    parse_company_tickers,
    parse_company_tickers_exchange,
)

__all__ = [
    "PARSER_LAYER_VERSION",
    "ParseOutcome",
    "ParsedRecord",
    "QuarantinedRecord",
    "RecordLocation",
    "merge_outcomes",
    "record_hash",
    "parse_calendar_announcement",
    "parse_company_tickers",
    "parse_company_tickers_exchange",
    "parse_edgar_calendar",
    "parse_historical_submissions",
    "parse_sic_reference",
    "parse_submissions_document",
]
