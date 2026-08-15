"""Verified document-evidence vocabularies, applicability policy, and hash domains.

Governing records: Decision 082 §11 (the schema contract) and §12 (the protocol the schema
will later serve); Decision 083 **R63** (the four owner dispositions) and **R64** (the frozen
protocol version); Decision 087 §§4-9 (the implementation authorization and the semantics
enforced here). Migration ``0015`` is the persisted contract; this module is its executable
mirror, and neither derives authority from the other.

**Nothing here executes the protocol.** There is no reviewer, no classifier, no extraction,
and no inference: Decision 071 **IN-2** is not reversed and every Decision 082 §12.3
prohibition stands. What lives here is the vocabulary a future authorized stage must use,
the applicability rule that stage may not widen, and the hash domains its records are
identified by.

Three things this module is deliberately careful about.

**Verified applicability is a policy gate, not a comment.** Decision 083 **R63** item C
authorizes ``evidence_level = 'verified'`` for amendment purpose and amendment linkage /
explicit-original evidence **only**. Migration ``0015`` enforces that in the schema;
:func:`require_verified_evidence_applicable` enforces the same rule in code, so a caller
that never touches SQLite cannot widen it either.

**No private path is ever a governed value.** The Complete Submission Text bytes stay in the
private external evidence root (Decision 083 **R63** item A). This module resolves no path,
opens no file, and reads no environment variable; :func:`require_no_private_path` is the
validator that keeps a path out of a governed value in the first place.

**One hashing implementation.** Every digest below goes through
:func:`disclosure_drift.release.hashing.hash_table` under a **new** evidence-specific domain
(Decision 082 §11.3; Decision 087 §9). A new domain leaves every existing digest
byte-unchanged, which is exactly why the evidence layer can exist without disturbing one
accepted candidate or selection identity.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.release.hashing import hash_table

__all__ = [
    "ABSTENTION_REASONS",
    "ADJUDICATED_EVIDENCE_COLUMNS",
    "ADJUDICATED_EVIDENCE_DOMAIN",
    "ADJUDICATED_EVIDENCE_KINDS",
    "ADJUDICATION_TABLE_DOMAIN",
    "AGREEMENT_STATES",
    "ARTIFACT_COLUMNS",
    "ARTIFACT_DOMAIN",
    "AUTHORIZED_VERIFIED_EVIDENCE_DIMENSIONS",
    "DOCUMENT_EVIDENCE_PROTOCOL_VERSION",
    "PURPOSE_CATEGORIES",
    "REVIEWER_ROLES",
    "REVIEW_A_TABLE_DOMAIN",
    "REVIEW_B_TABLE_DOMAIN",
    "REVIEW_PASS_BY_ROLE",
    "REVIEW_RECORD_COLUMNS",
    "REVIEW_RECORD_DOMAIN",
    "SOURCE_CLASSES",
    "SPAN_COLUMNS",
    "SPAN_DOMAIN",
    "SPAN_ROLES",
    "SPAN_ROLES_BY_EVIDENCE_KIND",
    "VERIFIED_AGREEMENT_STATES",
    "VERIFIED_EVIDENCE_LEVEL",
    "adjudicated_evidence_table_sha256",
    "adjudication_sha256",
    "artifact_table_sha256",
    "contributing_review_ids_json",
    "require_no_private_path",
    "require_verified_evidence_applicable",
    "review_pass_table_sha256",
    "review_record_sha256",
    "span_sha256",
    "verified_evidence_is_applicable",
]

# --------------------------------------------------------------------------
# Frozen vocabularies. Every tuple below is migration 0015's own CHECK vocabulary,
# reproduced so that a caller can validate before it writes rather than discovering the
# constraint from an IntegrityError. The migration remains the persisted contract.
# --------------------------------------------------------------------------

#: Decision 083 R64. Storing this string is not executing the protocol it names.
DOCUMENT_EVIDENCE_PROTOCOL_VERSION: Final = "m3.3-document-evidence/1.0"

VERIFIED_EVIDENCE_LEVEL: Final = "verified"

#: Decision 080 R45 and Decision 082 R56: the native Complete Submission Text is the
#: accepted source. A second source class needs its own owner record.
SOURCE_CLASSES: Final[tuple[str, ...]] = ("complete_submission_text",)

#: Decision 083 R63 item D: role plus opaque epoch, never a personal identity.
REVIEWER_ROLES: Final[tuple[str, ...]] = ("review_a", "review_b", "adjudication")

#: The contract's ``review_pass`` column, keyed by the role it must agree with.
REVIEW_PASS_BY_ROLE: Final[Mapping[str, str]] = {
    "review_a": "A",
    "review_b": "B",
    "adjudication": "ADJUDICATION",
}

#: Decision 014 §6's three frozen categories, verbatim and unchanged.
PURPOSE_CATEGORIES: Final[tuple[str, ...]] = (
    "administrative_or_exhibit",
    "financial_or_xbrl_correction",
    "narrative_or_governance",
)

#: Decision 082 §12.2's allowed abstentions. An abstention is a recorded outcome, never a
#: skipped row (Decision 080 AP-1 totality).
ABSTENTION_REASONS: Final[tuple[str, ...]] = (
    "insufficient_text",
    "ambiguous_text",
    "not_issuer_authored",
    "artifact_unreadable",
)

ADJUDICATED_EVIDENCE_KINDS: Final[tuple[str, ...]] = ("amendment_purpose", "explicit_original")

AGREEMENT_STATES: Final[tuple[str, ...]] = ("agreed", "resolved", "conflicting", "abstained")

#: Decision 082 §12.6: only these two outcomes are ever eligible for ``verified``.
#: ``conflicting`` and ``abstained`` fail closed and earn nothing.
VERIFIED_AGREEMENT_STATES: Final[tuple[str, ...]] = ("agreed", "resolved")

SPAN_ROLES: Final[tuple[str, ...]] = (
    "amendment_purpose",
    "original_form",
    "original_filing_date",
    "original_accession",
)

#: Which span roles can back which adjudicated evidence kind.
SPAN_ROLES_BY_EVIDENCE_KIND: Final[Mapping[str, tuple[str, ...]]] = {
    "amendment_purpose": ("amendment_purpose",),
    "explicit_original": ("original_form", "original_filing_date", "original_accession"),
}

# --------------------------------------------------------------------------
# Verified applicability -- Decision 083 R63 item C, Decision 087 §5.4
# --------------------------------------------------------------------------

#: The **only** two dimensions that may carry ``evidence_level = 'verified'`` in M3.3 v1.
#:
#: ``amendment_linkage`` is the linkage dimension, and naming it here is not a second
#: semantic state: Decision 083 **R63** item B reuses
#: ``amendment_linkage_state = 'amends_original'`` for *what* the relationship is, and this
#: set governs only *how strongly* it was verified (Decision 087 §6). No
#: ``verified_amends_original`` exists anywhere.
AUTHORIZED_VERIFIED_EVIDENCE_DIMENSIONS: Final[frozenset[str]] = frozenset(
    {"amendment_purpose", "amendment_linkage"}
)


def verified_evidence_is_applicable(dimension: str) -> bool:
    """Whether ``dimension`` may carry a verified evidence level in M3.3 v1."""
    return dimension in AUTHORIZED_VERIFIED_EVIDENCE_DIMENSIONS


def require_verified_evidence_applicable(dimension: str) -> None:
    """Refuse a verified evidence level on an unauthorized dimension.

    Raises:
        GateFailureError: ``dimension`` is outside
            :data:`AUTHORIZED_VERIFIED_EVIDENCE_DIMENSIONS`. Size, industry, history,
            universe, cohort, XBRL eligibility, control predicates, and name/ticker are all
            outside it, and none of them is silently enabled by migration ``0015``.
    """
    if verified_evidence_is_applicable(dimension):
        return
    authorized = ", ".join(sorted(AUTHORIZED_VERIFIED_EVIDENCE_DIMENSIONS))
    message = (
        f"evidence_level 'verified' is not authorized for dimension {dimension!r}; "
        f"Decision 083 R63 item C authorizes it only for: {authorized}"
    )
    raise GateFailureError(message)


# --------------------------------------------------------------------------
# Private-evidence-root nonleakage -- Decision 083 R63 item A, Decision 087 §5.1
# --------------------------------------------------------------------------

#: Characters that cannot appear in a governed evidence value because a filesystem path
#: needs at least one of them. ``~`` is included for the shell-expanded home directory,
#: which is a private path even before it is resolved.
_PATH_CHARACTERS: Final[tuple[str, ...]] = ("/", "\\", ":", "~")

#: The one governed column that legitimately contains ``/`` and ``:`` -- the public EDGAR
#: source URL -- is validated by prefix instead.
PUBLIC_ARCHIVE_URL_PREFIX: Final = "https://www.sec.gov/Archives/"


def require_no_private_path(value: str, field: str) -> None:
    """Refuse a governed value that could carry a private filesystem path.

    The artifact bytes live in the private external evidence root and never enter the
    catalog, so no governed value has any reason to look like a path. This validator is the
    code-side half of the shape CHECKs migration ``0015`` puts on every text column.

    Raises:
        GateFailureError: ``value`` contains a path separator, a drive separator, or a home
            directory marker.
    """
    found = tuple(character for character in _PATH_CHARACTERS if character in value)
    if not found:
        return
    message = (
        f"{field} must never carry a private filesystem path; "
        f"value contains {found!r} and the private evidence root is never governed data"
    )
    raise GateFailureError(message)


def contributing_review_ids_json(review_ids: Iterable[str]) -> str:
    """Serialize contributing review identities exactly as migration ``0015`` validates.

    The migration checks this string by arithmetic rather than by ``json1``: for ``n``
    identities the canonical array is ``1 + 67n`` characters long and carries ``2n`` quotes,
    and every identity must appear inside it. Sorting makes the serialization deterministic,
    so the same contributing set always renders the same bytes.

    Raises:
        GateFailureError: the set is empty, holds a duplicate, or holds an identity that is
            not a 64-character lowercase hex digest.
    """
    ordered = sorted(review_ids)
    if not ordered:
        message = "adjudicated evidence must name at least one contributing review"
        raise GateFailureError(message)
    if len(set(ordered)) != len(ordered):
        message = f"contributing review identities must be distinct; received {ordered!r}"
        raise GateFailureError(message)
    for review_id in ordered:
        if len(review_id) != 64 or any(
            character not in "0123456789abcdef" for character in review_id
        ):
            message = f"contributing review identity {review_id!r} is not a lowercase hex digest"
            raise GateFailureError(message)
    return "[" + ",".join(f'"{review_id}"' for review_id in ordered) + "]"


# --------------------------------------------------------------------------
# Hash domains -- Decision 082 §11.3 and §12.7, Decision 087 §9
#
# Every name below is NEW. ``hash_table`` mixes the domain name into the digest before any
# row, so a new domain cannot collide with an existing one, and adding these leaves every
# accepted candidate, registrant, snapshot, and selection digest byte-unchanged. That is the
# whole reason the evidence layer needs no identity re-baseline of its own.
# --------------------------------------------------------------------------

ARTIFACT_DOMAIN: Final = "document_artifact"
REVIEW_RECORD_DOMAIN: Final = "document_review_record"
SPAN_DOMAIN: Final = "document_review_span"
ADJUDICATED_EVIDENCE_DOMAIN: Final = "document_adjudicated_evidence"

#: Decision 082 §12.7's three pass-level digests. Review A is frozen and hashed before
#: Review B begins, and Review B before adjudication begins; separate domains are what stop
#: one pass's frozen digest from being mistaken for another's.
REVIEW_A_TABLE_DOMAIN: Final = "document_review_a_table"
REVIEW_B_TABLE_DOMAIN: Final = "document_review_b_table"
ADJUDICATION_TABLE_DOMAIN: Final = "document_adjudication_table"

_TABLE_DOMAIN_BY_ROLE: Final[Mapping[str, str]] = {
    "review_a": REVIEW_A_TABLE_DOMAIN,
    "review_b": REVIEW_B_TABLE_DOMAIN,
    "adjudication": ADJUDICATION_TABLE_DOMAIN,
}

#: The governed column tuples, in migration ``0015``'s own column order. These are NEW
#: tuples in NEW domains; no existing tuple is widened (accepted Decision 084 R67).
ARTIFACT_COLUMNS: Final[tuple[str, ...]] = (
    "artifact_sha256",
    "accession_plain",
    "source_class",
    "byte_length",
    "source_url",
    "retrieval_receipt_id",
)

REVIEW_RECORD_COLUMNS: Final[tuple[str, ...]] = (
    "review_id",
    "review_epoch_id",
    "reviewer_role",
    "reviewer_model",
    "review_pass",
    "artifact_sha256",
    "accession_plain",
    "protocol_version",
    "purpose_category",
    "abstained",
    "abstention_reason",
    "original_form_asserted",
    "original_filing_date_asserted",
    "original_accession_asserted",
)

SPAN_COLUMNS: Final[tuple[str, ...]] = (
    "review_id",
    "span_ordinal",
    "span_role",
    "span_text_verbatim",
    "span_location",
)

ADJUDICATED_EVIDENCE_COLUMNS: Final[tuple[str, ...]] = (
    "accession_plain",
    "evidence_kind",
    "artifact_sha256",
    "adjudicated_value",
    "agreement_state",
    "contributing_review_ids_json",
    "evidence_level",
)


def _require_fields(fields: Mapping[str, object], expected: Sequence[str], label: str) -> None:
    """Refuse a preimage that is missing a governed field or carries an unexpected one."""
    if set(fields) == set(expected):
        return
    missing = sorted(set(expected) - set(fields))
    unexpected = sorted(set(fields) - set(expected))
    message = f"{label} preimage mismatch; missing={missing}, unexpected={unexpected}"
    raise GateFailureError(message)


def _row(domain: str, columns: Sequence[str], fields: Mapping[str, object], label: str) -> str:
    """Digest one governed row through the accepted table-hashing machinery."""
    _require_fields(fields, columns, label)
    return hash_table(domain, columns, [fields]).normalized_content_sha256


def _rows(domain: str, columns: Sequence[str], rows: Iterable[Mapping[str, object]]) -> str:
    """Digest a governed row set. ``hash_table`` sorts rendered rows, so order is immaterial."""
    return hash_table(domain, columns, rows).normalized_content_sha256


def review_record_sha256(fields: Mapping[str, object]) -> str:
    """Per-record digest for one review pass (Decision 082 §12.7).

    Timestamps are excluded from the preimage: two identical decisions recorded a second
    apart are the same evidence, and a clock reading is not part of what was decided.
    """
    return _row(REVIEW_RECORD_DOMAIN, REVIEW_RECORD_COLUMNS, fields, "review_record_sha256")


def span_sha256(fields: Mapping[str, object]) -> str:
    """Per-span digest binding verbatim text to its stable location (Decision 082 §12.5)."""
    return _row(SPAN_DOMAIN, SPAN_COLUMNS, fields, "span_sha256")


def adjudication_sha256(fields: Mapping[str, object]) -> str:
    """Per-row digest for one frozen adjudicated result."""
    return _row(
        ADJUDICATED_EVIDENCE_DOMAIN,
        ADJUDICATED_EVIDENCE_COLUMNS,
        fields,
        "adjudication_sha256",
    )


def artifact_table_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """Digest of the complete bound artifact set."""
    return _rows(ARTIFACT_DOMAIN, ARTIFACT_COLUMNS, rows)


def review_pass_table_sha256(reviewer_role: str, rows: Iterable[Mapping[str, object]]) -> str:
    """Digest of one pass's complete frozen record set (Decision 082 §12.7).

    Raises:
        GateFailureError: ``reviewer_role`` is not one of :data:`REVIEWER_ROLES`.
    """
    domain = _TABLE_DOMAIN_BY_ROLE.get(reviewer_role)
    if domain is None:
        message = (
            f"unknown reviewer role {reviewer_role!r}; expected one of {', '.join(REVIEWER_ROLES)}"
        )
        raise GateFailureError(message)
    return _rows(domain, REVIEW_RECORD_COLUMNS, rows)


def adjudicated_evidence_table_sha256(rows: Iterable[Mapping[str, object]]) -> str:
    """Digest of the complete frozen adjudication table (Decision 082 §12.7)."""
    return _rows(ADJUDICATED_EVIDENCE_DOMAIN, ADJUDICATED_EVIDENCE_COLUMNS, rows)
