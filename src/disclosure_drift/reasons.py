"""Machine-readable reason codes for eligibility, exclusion, review, and integrity.

Every excluded row carries at least one exclusion reason and every review row
carries at least one review reason (Decision 007 section 6, Decision 008 section 4).
Unknown classification never produces silent eligibility.

This registry seeds ``reference_reason_codes`` in the operational catalog.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

__all__ = [
    "REASON_CODES",
    "ReasonCategory",
    "ReasonCode",
    "codes_for_category",
    "reason",
    "release_blocking_codes",
]

ReasonCategory = Literal[
    "eligible",
    "support",
    "amendment",
    "excluded",
    "review",
    "integrity",
    "temporal",
    "provenance",
]
"""Reason categories.

``provenance`` records a neutral, expected fact about a source's lifecycle, such as
a living official dataset being updated. A provenance code never blocks a release
and never requires manual review: it exists so that ordinary change is recorded
rather than treated as an anomaly.
"""


@dataclass(frozen=True, slots=True)
class ReasonCode:
    """One machine-readable reason with its policy consequences."""

    code: str
    category: ReasonCategory
    description: str
    blocks_release: bool
    requires_manual_review: bool
    decision_reference: str


def _code(
    code: str,
    category: ReasonCategory,
    description: str,
    *,
    blocks_release: bool = False,
    requires_manual_review: bool = False,
    decision_reference: str,
) -> ReasonCode:
    return ReasonCode(
        code=code,
        category=category,
        description=description,
        blocks_release=blocks_release,
        requires_manual_review=requires_manual_review,
        decision_reference=decision_reference,
    )


_D007: Final = "Docs/Decisions/decision_007_sec_universe.md"
_D008: Final = "Docs/Decisions/decision_008_filing_inventory.md"
_D009: Final = "Docs/Decisions/decision_009_raw_data_governance.md"
_D010: Final = "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md"
_D011: Final = "Docs/Decisions/decision_011_edgar_operating_calendar_provenance.md"
_D012: Final = "Docs/Decisions/decision_012_accession_observation_resolution.md"
_D002: Final = "Docs/Decisions/decision_002_primary_outcome.md"
_D013: Final = "Docs/Decisions/decision_013_pilot_selection_mechanics.md"
_D014: Final = "Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md"
_D015: Final = "Docs/Decisions/decision_015_pilot_use_prohibition.md"
_D016: Final = "Docs/Decisions/decision_016_m23_schema_and_artifact_architecture.md"
_D018: Final = "Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md"
_D020: Final = "Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md"
_D028: Final = "Docs/Decisions/decision_028_m3_1_readiness_corrections.md"
_D029: Final = "Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md"
_D040: Final = "Docs/Decisions/decision_040_m3_2_t2_4_implementation_authorization.md"

_ALL: Final[tuple[ReasonCode, ...]] = (
    # --- eligibility -------------------------------------------------------- #
    _code(
        "ELIGIBLE_ORIGINAL_10K",
        "eligible",
        "Original annual report eligible as a primary target filing.",
        decision_reference=_D008,
    ),
    _code(
        "ELIGIBLE_TRANSITION_10KT",
        "eligible",
        "Original transition-period annual report eligible as a primary target filing.",
        decision_reference=_D008,
    ),
    _code(
        "SUPPORT_ONLY",
        "support",
        "Filing retained only as prior-year support; never a primary target.",
        decision_reference=_D008,
    ),
    _code(
        "AMENDMENT_NON_TARGET",
        "amendment",
        "Amendment retained with its own dates and cohorts; never a primary target.",
        decision_reference=_D008,
    ),
    # --- exclusions --------------------------------------------------------- #
    _code(
        "EXCLUDED_ASSET_BACKED_ISSUER",
        "excluded",
        "Asset-backed issuer excluded from the study universe.",
        decision_reference=_D007,
    ),
    _code(
        "EXCLUDED_REGISTERED_INVESTMENT_COMPANY",
        "excluded",
        "Registered investment company, fund, or ETF excluded from the study universe.",
        decision_reference=_D007,
    ),
    _code(
        "EXCLUDED_SHELL_COMPANY",
        "excluded",
        "Shell filing excluded for this accession; exclusion is accession-specific.",
        decision_reference=_D007,
    ),
    _code(
        "EXCLUDED_BLANK_CHECK_COMPANY",
        "excluded",
        "Blank-check filing excluded for this accession; exclusion is accession-specific.",
        decision_reference=_D007,
    ),
    _code(
        "EXCLUDED_UNSUPPORTED_FORM",
        "excluded",
        "Form outside the eligible study universe; retained as inventory or control evidence.",
        decision_reference=_D007,
    ),
    # --- review ------------------------------------------------------------- #
    _code(
        "REVIEW_MULTI_REGISTRANT",
        "review",
        "Accession lists multiple registrants; registrant relationships must be confirmed.",
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_UNKNOWN_ISSUER_TYPE",
        "review",
        "Issuer type could not be classified; eligibility must not be inferred.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_CONFLICTING_SIC",
        "review",
        "Conflicting SIC evidence across sources for the same accession.",
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_POST_DE_SPAC_TRANSITION",
        "review",
        "Issuer appears to have transitioned out of shell status; classification is per accession.",
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_REGISTRANT_CIK_UNRESOLVED",
        "review",
        "Registrant CIK could not be resolved; the accession prefix is not a substitute.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_AMENDMENT_PARENT_UNRESOLVED",
        "review",
        "Amendment parentage could not be established from evidence.",
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "REVIEW_MISSING_ACCEPTANCE_TIMESTAMP",
        "review",
        "No acceptance timestamp available; availability precision falls back to date level.",
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_CORRECTION_CROSSES_COHORT_BOUNDARY",
        "review",
        "A post-acceptance correction moves the filing across a frozen cohort boundary.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_COHORT_DIVERGENCE_BOUNDARY_CROSSING",
        "review",
        "Official-filing and acceptance cohorts differ across a frozen boundary.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_AVAILABILITY_ORDER_INDETERMINATE",
        "review",
        "Availability order between two accessions cannot be established at date precision; "
        "automatic historical use is blocked without asserting unavailability.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_ACCESSION_HEADER_SOURCE_CONFLICT",
        "review",
        "Co-authoritative accession-header sources disagree; neither may be chosen silently.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_PROVISIONAL_DATE_DISAGREEMENT",
        "review",
        "Provisional discovery sources disagree and no accession-header value is available yet.",
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_FILING_DATE_BEFORE_ACCEPTANCE",
        "review",
        "Official filing date precedes the acceptance date, which SEC mechanics do not explain.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_TIMEZONE_AMBIGUOUS",
        "review",
        "Acceptance wall-clock time occurs twice under the Eastern daylight-saving fall-back, "
        "so two UTC offsets are possible and none may be chosen automatically.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_TIMEZONE_NONEXISTENT",
        "review",
        "Acceptance wall-clock time does not exist under the Eastern daylight-saving "
        "spring-forward transition, so the value cannot be interpreted as supplied.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    # --- temporal classification -------------------------------------------- #
    _code(
        "SAME_DAY_FILING",
        "temporal",
        "Official filing date equals the SEC acceptance date.",
        decision_reference=_D010,
    ),
    _code(
        "EXPECTED_AFTER_CUTOFF_ROLLOVER",
        "temporal",
        "Accepted after the applicable SEC cutoff, with the official filing date on the next "
        "EDGAR operating day; explained, and still reported in the divergence audit.",
        decision_reference=_D010,
    ),
    _code(
        "POST_ACCEPTANCE_DATE_CORRECTION",
        "temporal",
        "Filing metadata or DATE AS OF CHANGE indicates an authorized later correction or "
        "filing-date adjustment; never treated as ordinary after-hours behaviour.",
        decision_reference=_D010,
    ),
    _code(
        "UNEXPLAINED_DATE_DIVERGENCE",
        "temporal",
        "The acceptance-to-filing-date difference cannot be established from the approved rules "
        "and preserved source evidence.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "COVERAGE_BOUNDARY_DIVERGENCE",
        "temporal",
        "One date maps to a frozen cohort while the other is unresolved or outside supported "
        "cohort coverage.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY",
        "review",
        "A purported SEC acceptance falls on a non-operating day; EDGAR does not "
        "ordinarily accept filings on weekends or federal holidays. The observation is "
        "preserved, automatic rollover classification is blocked, and reconciliation is "
        "required.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_CALENDAR_EVIDENCE_CONFLICT",
        "review",
        "Official calendar evidence disagrees for a date; every observation is preserved and "
        "the date resolves to unknown rather than being settled by source order.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D011,
    ),
    _code(
        "REVIEW_CALENDAR_DATE_UNKNOWN",
        "review",
        "No sufficient official SEC evidence establishes whether EDGAR operated on a date, so "
        "automated rollover classification is blocked.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D011,
    ),
    _code(
        "OPERATING_CALENDAR_UNAVAILABLE",
        "temporal",
        "No EDGAR operating calendar covered the dates, so rollover could not be established.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    # --- provenance: expected source lifecycle ------------------------------ #
    _code(
        "SOURCE_CONTENT_UPDATED",
        "provenance",
        "A living official source changed at the same identity, which is expected. The "
        "changed bytes become a new immutable observation, the prior observation is "
        "preserved, and the new observation supersedes it for future census runs.",
        decision_reference=_D009,
    ),
    _code(
        "SOURCE_CONTENT_UNCHANGED",
        "provenance",
        "A repeat retrieval returned bytes identical to the preserved object, so the "
        "stored payload is reused and the retrieval is still recorded.",
        decision_reference=_D009,
    ),
    _code(
        "SOURCE_SNAPSHOT_REUSED",
        "provenance",
        "A conditional request returned 304 and every reuse precondition held, so the "
        "verified preserved snapshot is reused.",
        decision_reference=_D009,
    ),
    _code(
        "SOURCE_CORRECTION_EXPLAINED",
        "provenance",
        "A dated artifact changed and an official SEC correction observation explains "
        "the change, so the update is recorded as expected rather than as a mutation.",
        decision_reference=_D009,
    ),
    _code(
        "PARSER_STRUCTURE_VALID_EMPTY",
        "provenance",
        "A nested source region was present, correctly typed, and genuinely empty, so "
        "zero records is a real observation rather than an absence of evidence.",
        decision_reference=_D008,
    ),
    # --- structural integrity of nested source regions ---------------------- #
    _code(
        "PARSER_STRUCTURE_ABSENT",
        "integrity",
        "A nested source region the schema requires was absent, so record counts derived "
        "from it are unknown and must never be reported as a genuine zero.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "PARSER_STRUCTURE_NULL",
        "integrity",
        "A nested source region was present but null, which is not an empty table; the "
        "raw payload is retained and the count stays unknown.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "PARSER_STRUCTURE_WRONG_TYPE",
        "integrity",
        "A nested source region carried an unexpected type, so it cannot be read as the "
        "structure the schema declares and its record count stays unknown.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "PARSER_STRUCTURE_MALFORMED",
        "integrity",
        "A nested source region was correctly typed but internally inconsistent, for "
        "example parallel columns of differing length; nothing is truncated or inferred.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "PARSER_STRUCTURE_INDETERMINATE",
        "integrity",
        "A nested source region could not be classified as valid, absent, or malformed, so "
        "it resolves to indeterminate rather than to any count.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "CALENDAR_CONTEXTUAL_DATE_RETAINED",
        "provenance",
        "A visible date was retained as contextual evidence only. A publication date, "
        "page-update date, filing deadline, example, navigation label, or date from "
        "another year asserts no EDGAR operating status.",
        decision_reference=_D011,
    ),
    _code(
        "REVIEW_CALENDAR_EVIDENCE_UNSUPPORTED",
        "review",
        "A reviewed manifest date is not supported by the retrieved document, so the date "
        "resolves to unknown rather than inheriting the manifest's asserted status.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D011,
    ),
    _code(
        "REVIEW_CALENDAR_EVIDENCE_AMBIGUOUS",
        "review",
        "The prose surrounding an affected date does not determine an operating status, so "
        "the date resolves to unknown rather than being read either way.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D011,
    ),
    _code(
        "REVIEW_CALENDAR_UNEXPECTED_AFFECTED_DATE",
        "review",
        "A document appears to assert an operating status for a date the reviewed manifest "
        "does not name; the observation is preserved and no status is applied.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D011,
    ),
    _code(
        "REVIEW_CALENDAR_STRUCTURE_UNRECOGNIZED",
        "review",
        "No official holiday table, caption, or heading was recognized on a calendar page, "
        "so no date was asserted; absence of a recognized structure is not absence of "
        "holidays.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D011,
    ),
    # --- full-index coverage reconciliation --------------------------------- #
    _code(
        "INDEX_ACCESSION_NOT_IN_SUBMISSIONS",
        "review",
        "The official quarterly index lists an accession that submissions metadata does "
        "not; both sides are retained and neither record is removed.",
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "SUBMISSIONS_ACCESSION_NOT_IN_INDEX",
        "review",
        "Submissions metadata lists an accession the official quarterly index does not; "
        "both sides are retained and neither record is removed.",
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "INDEX_SUBMISSIONS_FIELD_CONFLICT",
        "review",
        "The quarterly index and submissions metadata disagree on a compared field for "
        "one accession; both observations are preserved and neither is replaced.",
        requires_manual_review=True,
        decision_reference=_D012,
    ),
    _code(
        "INDEX_INSTANCE_UNAVAILABLE",
        "integrity",
        "A required quarterly index instance was not retrieved or not usably parsed, so "
        "coverage for that period cannot be confirmed.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "INDEX_REQUIRED_INSTANCE_MISSING",
        "integrity",
        "The census plan requires a quarterly index instance that is absent, so the "
        "census may not claim completion.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "INDEX_RECONCILIATION_INDETERMINATE",
        "review",
        "An index row or submissions record was malformed, so the comparison could not be "
        "made; the raw evidence is retained on both sides.",
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    # --- accession field resolution (Decision 012) -------------------------- #
    _code(
        "ACCESSION_FIELD_RESOLVED",
        "provenance",
        "A canonical accession field was resolved to a single authoritative value from "
        "the preserved observation set, deterministically and independently of order.",
        decision_reference=_D012,
    ),
    _code(
        "ACCESSION_FIELD_RESOLVED_BY_CORRECTION",
        "provenance",
        "An explicitly identified official SEC correction superseded an earlier value; "
        "every prior observation is preserved.",
        decision_reference=_D012,
    ),
    _code(
        "ACCESSION_FIELD_UNRESOLVED_EQUAL_AUTHORITY",
        "integrity",
        "Observations of equal authority disagree on a canonical field, so it stays "
        "unresolved rather than being settled by retrieval time or ingestion order.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D012,
    ),
    _code(
        "ACCESSION_FIELD_CONFLICT_MATERIAL",
        "integrity",
        "A material canonical field is unresolved, so downstream use depending on that "
        "field is blocked.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D012,
    ),
    _code(
        "ACCESSION_FIELD_CONFLICT_NON_MATERIAL",
        "review",
        "A non-material canonical field is unresolved. It does not block cohort "
        "assignment, but it is recorded and reviewed rather than silently settled.",
        requires_manual_review=True,
        decision_reference=_D012,
    ),
    _code(
        "ACCESSION_COHORT_BOUNDARY_CROSSED",
        "review",
        "A resolved filing-date correction moved an accession across a frozen cohort "
        "boundary; prior cohort observations are retained.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D012,
    ),
    _code(
        "ACCESSION_2024_COHORT_TRANSITION_REQUIRES_APPROVAL",
        "review",
        "Entry into or exit from the untouched 2024 primary-test cohort requires explicit "
        "approval; the transition is recorded and blocked until it is approved.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D012,
    ),
    _code(
        "ACCESSION_REGISTRANT_CONFLICT_PRESERVED",
        "integrity",
        "Registrant CIK observations disagree for one accession. Every observation is "
        "preserved and no CIK identities are merged.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D012,
    ),
    _code(
        "ACCESSION_SUBMITTER_DIFFERS_FROM_REGISTRANT",
        "review",
        "The submitter CIK differs from the registrant CIK, retained as a review signal "
        "for possible multi-registrant or agent-filed submissions.",
        requires_manual_review=True,
        decision_reference=_D012,
    ),
    _code(
        "REVIEW_CALENDAR_TARGET_YEAR_ABSENT",
        "review",
        "An annual-calendar instance carried no explicitly requested target year. The "
        "year is never inferred from the current date or the retrieval timestamp, so no "
        "operating status may be asserted from the snapshot.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D011,
    ),
    _code(
        "REVIEW_CALENDAR_TARGET_YEAR_UNSUPPORTED",
        "review",
        "A recognized official holiday structure asserts nothing for the requested year, "
        "so coverage for that year is unknown rather than empty.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D011,
    ),
    _code(
        "PARSER_HISTORICAL_REFERENCE_MALFORMED",
        "integrity",
        "A historical submissions reference lacked a usable name or carried unusable "
        "metadata; it is preserved as source evidence and never silently skipped.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    # --- integrity ---------------------------------------------------------- #
    _code(
        "SOURCE_IMMUTABLE_IDENTITY_MUTATED",
        "integrity",
        "A source defined as immutable changed its content at the same official "
        "identity; both observations are preserved and the census stops for review.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D009,
    ),
    _code(
        "SOURCE_DATED_ARTIFACT_CHANGED",
        "integrity",
        "A dated historical artifact changed with no explained SEC correction, or its "
        "period closure could not be established; the change is not accepted silently.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D009,
    ),
    _code(
        "SOURCE_VALIDATOR_CONTRADICTION",
        "integrity",
        "The same ETag or Last-Modified validator yielded different bytes, so the "
        "source's own cache validators cannot be trusted for this identity.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D009,
    ),
    _code(
        "SOURCE_HASH_DISAGREEMENT",
        "integrity",
        "Transport bytes and stored bytes do not reconcile under the recorded storage "
        "representation, so the stored object cannot be trusted as evidence.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D009,
    ),
    _code(
        "SOURCE_SNAPSHOT_REUSE_UNRECONCILED",
        "integrity",
        "A 304 reuse could not be reconciled with a recorded prior observation, so the "
        "response is failed closed and never read as an empty or new dataset.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D009,
    ),
    _code(
        "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        "integrity",
        "A redirect hop or final URL left the registered source's permitted URL family, "
        "changed host, downgraded the scheme, or entered a prohibited filing path.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "SEC_REDIRECT_DEPTH_EXCEEDED",
        "integrity",
        "A redirect chain looped or exceeded the permitted depth, so the retrieval is "
        "abandoned rather than followed further.",
        blocks_release=True,
        decision_reference=_D007,
    ),
    _code(
        "RAW_ARCHIVE_MEMBER_REFUSED",
        "integrity",
        "An archive member violated a canonicalization or expansion rule; the archive is "
        "preserved and quarantined rather than partially trusted.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D009,
    ),
    _code(
        "PARSER_SCHEMA_DRIFT_OBSERVED",
        "integrity",
        "A parsed source record carried unknown fields or a changed shape; the record is "
        "retained with its unknown fields for review rather than silently narrowed.",
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "PARSER_DUPLICATE_SOURCE_RECORD",
        "integrity",
        "A source document contained duplicate records for the same native identity; "
        "every observation is retained and none is chosen silently.",
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "AUDIT_PROJECTION_INCOMPLETE",
        "integrity",
        "The append-only audit projection is behind the authoritative catalog rows and "
        "must be rebuilt from them; the observations themselves remain recorded.",
        decision_reference=_D009,
    ),
    _code(
        "RAW_FILE_CHECKSUM_MISMATCH",
        "integrity",
        "Stored raw file does not match its recorded checksum; the file is quarantined, "
        "never replaced.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "REMOTE_CONTENT_CHANGED",
        "integrity",
        "A later response differs from an earlier observation; recorded as a new observation.",
        requires_manual_review=True,
        decision_reference=_D009,
    ),
    _code(
        "SEC_BLOCK_PAGE",
        "integrity",
        "SEC returned a block page; aggregate traffic halts and enters cooldown.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "SEC_SCHEMA_REQUIRED_FIELD_MISSING",
        "integrity",
        "A required SEC field is absent; no default is applied.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "SEC_RETRIES_EXHAUSTED",
        "integrity",
        "A transient failure persisted through the whole retry budget. The retrieval is "
        "terminal and is never reported as an empty or successful result.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "SEC_REQUEST_CEILING_EXHAUSTED",
        "integrity",
        "Planned work remains, but the next physical attempt would exceed the exact "
        "owner-approved ceiling. Distinct from SEC_RETRIES_EXHAUSTED, which means a "
        "single logical retrieval exhausted response-policy retries rather than that "
        "the window-wide physical-attempt ceiling was consumed.",
        blocks_release=True,
        decision_reference=_D028,
    ),
    _code(
        "SEC_ACQUISITION_INTERRUPTED",
        "integrity",
        "Acquisition was interrupted and no narrower registered reason applies. "
        "Distinct from RAW_PARTIAL_DOWNLOAD, which is specific to an actual partial "
        "transfer.",
        blocks_release=True,
        decision_reference=_D028,
    ),
    _code(
        "OFFLINE_REHEARSAL_SCENARIO_MISMATCH",
        "integrity",
        "An offline rehearsal scenario did not reach the state its specification names — a "
        "scripted path ending in the wrong terminal condition, a worst-path witness whose "
        "observed attempt count disagrees with the state machine, or a report whose tested "
        "route key set omits a derived route. It is an integrity failure of the evidence, "
        "not of acquisition: SEC_ACQUISITION_INTERRUPTED stays reserved for a genuine "
        "acquisition interruption and never stands in for a defective witness. Decision 029 "
        "rules requires_manual_review false; blocks_release is what stops a release here.",
        blocks_release=True,
        decision_reference=_D029,
    ),
    _code(
        "SEC_RESPONSE_EMPTY",
        "integrity",
        "SEC returned an empty body; a failure never becomes a valid empty result.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "SEC_RESPONSE_MALFORMED",
        "integrity",
        "SEC response could not be parsed as its declared type; payload quarantined.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "RAW_ARCHIVE_INVALID",
        "integrity",
        "Archive payload failed structural validation; payload quarantined.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "RAW_PARTIAL_DOWNLOAD",
        "integrity",
        "Transfer ended before completion; the partial file is preserved, never promoted.",
        decision_reference=_D009,
    ),
    _code(
        "PARSER_FAILURE_RECORDED",
        "integrity",
        "Parser failed; the failure is recorded and raw evidence is retained.",
        decision_reference=_D009,
    ),
    # --- M2.3 pilot: snapshot, cohort, and universe provenance (Decisions 002, 014, 016) ---- #
    _code(
        "PILOT_CANDIDATE_SNAPSHOT_FROZEN",
        "provenance",
        "The immutable pilot candidate snapshot was frozen with its deterministic hashes.",
        decision_reference=_D016,
    ),
    _code(
        "PILOT_CANDIDATE_SNAPSHOT_INVALIDATED",
        "provenance",
        "The pilot candidate snapshot was invalidated and cannot seed a selection run.",
        decision_reference=_D016,
    ),
    _code(
        "PILOT_PROVISIONAL_COHORT_PRECEDENCE_2",
        "temporal",
        "The cohort uses precedence-2 metadata and requires M2.5 verification.",
        decision_reference=_D014,
    ),
    _code(
        "PILOT_ENTITY_NOT_PRIMARY_UNIVERSE_ELIGIBLE",
        "excluded",
        "The entity is excluded from the primary research universe.",
        decision_reference=_D002,
    ),
    _code(
        "PILOT_ENGINEERING_ONLY_STRESS_CASE",
        "provenance",
        "The entity is retained only for engineering-coverage stress testing.",
        decision_reference=_D002,
    ),
    # --- M2.3 pilot: candidate-classification review states (Decisions 013, 014) ----------- #
    _code(
        "REVIEW_PILOT_SIZE_CATEGORY_UNAVAILABLE",
        "review",
        "The provisional filer-size category is missing, conflicting, or unresolved.",
        requires_manual_review=True,
        decision_reference=_D014,
    ),
    _code(
        "REVIEW_PILOT_SIC_UNMAPPED",
        "review",
        "The SIC does not map to an affirmative frozen industry family.",
        requires_manual_review=True,
        decision_reference=_D014,
    ),
    _code(
        "REVIEW_PILOT_SIC_ENGINEERING_ONLY",
        "review",
        "The SIC classification is review-required and cannot satisfy an affirmative industry "
        "quota.",
        requires_manual_review=True,
        decision_reference=_D014,
    ),
    _code(
        "REVIEW_PILOT_HISTORY_EVIDENCE_INSUFFICIENT",
        "review",
        "Available metadata cannot support an affirmative stable/eventful classification.",
        requires_manual_review=True,
        decision_reference=_D014,
    ),
    _code(
        "REVIEW_PILOT_AMENDMENT_PURPOSE_UNPROVEN",
        "review",
        "Amendment purpose is unproven from authorized M2.3 metadata.",
        requires_manual_review=True,
        decision_reference=_D014,
    ),
    _code(
        "REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE",
        "review",
        "Authorized metadata does not fully establish the accession's registrant set.",
        requires_manual_review=True,
        decision_reference=_D013,
    ),
    # --- M2.3 pilot: selection, reserve, and manifest integrity (Decisions 013, 016) -------- #
    _code(
        "PILOT_SELECTION_INFEASIBLE",
        "integrity",
        "Deterministic search proved that the frozen quotas cannot be satisfied.",
        blocks_release=True,
        decision_reference=_D013,
    ),
    _code(
        "PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN",
        "integrity",
        "Deterministic search exhausted its node limit without proving feasibility or "
        "infeasibility.",
        blocks_release=True,
        decision_reference=_D013,
    ),
    _code(
        "PILOT_RESERVE_SIGNATURE_INCOMPATIBLE",
        "integrity",
        "A reserve package does not preserve the complete replacement-compatibility signature.",
        blocks_release=True,
        decision_reference=_D016,
    ),
    _code(
        "PILOT_RESERVE_UNAVAILABLE",
        "integrity",
        "No deterministic compatible reserve package is available.",
        blocks_release=True,
        decision_reference=_D013,
    ),
    _code(
        "PILOT_MANIFEST_HASH_NOT_APPROVED",
        "integrity",
        "The exact proposed pilot manifest root hash has not received owner approval.",
        blocks_release=True,
        decision_reference=_D013,
    ),
    # --- M2.3 pilot: Stage S5 joint accession selection (Decision 018 section 21) ---------- #
    #
    # Exactly these five codes are approved; no alias, generalized variant, retry code,
    # reserve code, or ticker-warning code is added. Unresolved amendment parentage
    # reuses REVIEW_AMENDMENT_PARENT_UNRESOLVED, run-level infeasibility reuses
    # PILOT_SELECTION_INFEASIBLE, and node exhaustion reuses
    # PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN (Decision 018 section 21).
    _code(
        # Decision 018 sections 8 and 28: a cap violation is an infeasibility
        # condition, never a penalty and never a warning.
        "PILOT_ACCESSION_CAP_EXCEEDED",
        "integrity",
        "A per-CIK or global selected-accession cap would be exceeded.",
        blocks_release=True,
        decision_reference=_D018,
    ),
    _code(
        # Decision 018 section 9: a zero-accession or partially anchored entity
        # result can never be feasible or publishable.
        "PILOT_ENTITY_ACCESSION_FLOOR_UNMET",
        "integrity",
        "A selected entity does not meet its required selected-accession floor.",
        blocks_release=True,
        decision_reference=_D018,
    ),
    _code(
        # Decision 018 section 15 and Decision 019 sections 7.1 and 7.6: the marker is
        # provenance, not eligibility. It distinguishes an accession outside the frozen
        # windows by design from one whose cohort evidence is merely absent, and it is
        # carried at reason_scope 'cohort' only.
        "PILOT_ACCESSION_PRE_STUDY_SUPPORT",
        "provenance",
        "The accession precedes the frozen study windows and is eligible only as support.",
        decision_reference=_D018,
    ),
    _code(
        # Decision 018 section 14: excluded from hard feasibility, never proxied, never
        # reported as satisfied, and a mandatory M2.5 verification obligation.
        "REVIEW_PILOT_QUOTA_UNMEASURABLE_AT_M23",
        "review",
        "The quota is not measurable from authorized M2.3 metadata and is deferred to M2.5.",
        requires_manual_review=True,
        decision_reference=_D018,
    ),
    _code(
        # Decision 018 sections 7 and 28: a candidate-level failure -- the accession is
        # simply not selectable -- never a run-level failure.
        "REVIEW_PILOT_ACCESSION_ROLE_UNCLASSIFIED",
        "review",
        "The accession's frozen attributes do not map to exactly one selection role.",
        requires_manual_review=True,
        decision_reference=_D018,
    ),
    # --- M2.3 pilot: Stage S5.4 reserve construction (Decision 020 section 13) ------------- #
    #
    # Exactly one code is authorized. REVIEW_PILOT_RESERVE_POOL_EXHAUSTED is explicitly
    # not authorized and must not be added: each target's reserve is computed
    # independently of every other target's, so no pool-exhaustion state exists. No
    # integrity, retry, approximation, or substitution code is added either -- every
    # reserve integrity violation is a gate failure (Decision 020 section 10), and
    # Decision 013 section 6 forbids discretionary substitution outright.
    _code(
        # Decision 020 section 7.1: target-specific, review-required, and nonblocking.
        # It is not selection infeasibility and not node-limit exhaustion; the run still
        # reaches 'feasible' with the disposition durably recorded.
        "REVIEW_PILOT_NO_COMPATIBLE_RESERVE",
        "review",
        "No candidate preserves the target selected entity's complete quota-contribution "
        "signature, so that target has no reserve package.",
        requires_manual_review=True,
        decision_reference=_D020,
    ),
    # --- M3.2 T2.4: required-object availability (Decision 040 section 4) ------------------ #
    #
    # Exactly one code is approved; no alias and no second code is added, and no existing
    # reason is redefined or remapped. It marks a REQUIRED, non-quarterly-index M3.2A logical
    # request whose committed observation is terminally failed or quarantined: the required
    # object remains unavailable. It may coexist with a more specific accepted defect code
    # (for example SEC_RESPONSE_MALFORMED, RAW_ARCHIVE_INVALID, or RAW_ARCHIVE_MEMBER_REFUSED)
    # and never replaces the more specific cause. Quarterly index instances retain
    # INDEX_INSTANCE_UNAVAILABLE and the related accepted index codes; stopped, interrupted,
    # ceiling-exhausted, and not-attempted requests retain their run or request
    # classifications and do not receive this code merely for lacking an object;
    # recent-target 404 semantics are unchanged; no M3.2B mapping is authorized.
    _code(
        "SOURCE_REQUIRED_OBJECT_UNAVAILABLE",
        "integrity",
        "A required source object was not retrieved or not usably obtained at its "
        "registered identity, so the window cannot confirm the required object present.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D040,
    ),
)

REASON_CODES: Final[Mapping[str, ReasonCode]] = MappingProxyType({item.code: item for item in _ALL})
"""Every reason code, keyed by code."""


def reason(code: str) -> ReasonCode:
    """Return the registered reason code.

    Raises:
        KeyError: the code is not registered. Reason codes are a closed set;
            ad-hoc strings are not permitted in the catalog.
    """
    try:
        return REASON_CODES[code]
    except KeyError:
        message = f"unregistered reason code {code!r}; add it to disclosure_drift.reasons"
        raise KeyError(message) from None


def codes_for_category(category: ReasonCategory) -> tuple[str, ...]:
    """Return the registered codes in ``category``, sorted."""
    return tuple(sorted(item.code for item in _ALL if item.category == category))


def release_blocking_codes() -> tuple[str, ...]:
    """Return the codes whose presence blocks release freezing, sorted."""
    return tuple(sorted(item.code for item in _ALL if item.blocks_release))


def _validate_registry() -> None:
    """Assert registry invariants at import time."""
    if len(REASON_CODES) != len(_ALL):
        message = "duplicate reason code detected in the registry"
        raise AssertionError(message)
    for item in _ALL:
        if not item.code.isupper() or " " in item.code:
            message = f"reason code {item.code!r} must be upper snake case"
            raise AssertionError(message)
        if not item.description.endswith("."):
            message = f"reason code {item.code!r} needs a sentence description"
            raise AssertionError(message)
        if item.category == "review" and not item.requires_manual_review:
            message = f"review code {item.code!r} must require manual review"
            raise AssertionError(message)
        if item.category == "eligible" and (item.blocks_release or item.requires_manual_review):
            message = f"eligible code {item.code!r} must not block release or require review"
            raise AssertionError(message)


_validate_registry()
