"""The accepted Decision 112 compact E0 evidence contract.

**What the owner ruled.** For E0 the frozen immutable source artifact is the authoritative
complete raw evidence. E0's durable relational evidence exists to prove traversal, parser
disposition, canonical identity, canonical association, exceptions, lineage, and replayability
-- *not* to reproduce the raw JSON archive field by field in SQLite when those ordinary field
values are already preserved in the frozen artifact and are deterministically reconstructible
(D112 §3). One SQLite row per ordinary raw field observation is therefore no longer required.

This module is that contract, stated once so both the writer and the reader obey the same rule
and a test can hold them to it. It decides three things and nothing else:

1. **Which accession field observations carry information** (:func:`materialized_fields`).
   Everything else is omitted from ``census_accession_observations`` and remains
   cryptographically represented by the completeness digest below.
2. **How an omitted observation is reconstructed** from the canonical ``census_accessions``
   row (:func:`reconstructed_observations`), so every accepted downstream consumer sees the
   identical observation stream it saw before -- same values, same deterministic identifiers,
   same order.
3. **The completeness digest** (:class:`ProjectionDigest`), a deterministic ordered digest over
   *all* normalized parsed projections including the ordinary values no longer materialized as
   rows, reproducible by replaying the frozen artifact alone.

**The omission rule, and why it is safe.** An observation is omitted only when it is either
inert or exactly reconstructible:

* **Ungoverned fields are inert.** ``CANONICAL_FIELD_BY_SOURCE_FIELD`` is the complete set of
  source-native field names any accepted consumer reads: Decision 012 resolution drops every
  other name before looking at it, and the Decision 094 §6.2 membership projection selects only
  ``cik`` and ``cik_padded``. Persisting the rest writes rows that are read back and discarded.
  On E0's first planned source that is roughly eleven of every seventeen rows.
* **A governed field's canonical column is the observation.** ``census_accessions`` already
  stores each governed value together with the provenance triple the observation carried --
  ``source_observation_id``, ``parsed_record_id``, ``first_observed_at_utc`` -- and the
  observation identifier is a pure function of those. Where the raw value round-trips through
  that column exactly, the row is a duplicate of the canonical row.

**Everything that does not round-trip is materialized, deliberately.** A malformed date, a
value the canonical column normalises or drops, a blank membership rendering, and every field
of a second or competing witness all fail the round-trip and are written individually -- which
is the D112 §4.D exception evidence, not an exception to it. When a rival witness appears the
incumbent's rows are back-filled first, so a real disagreement is always represented by the
full set of rows that disagree rather than by the newcomer alone.

Nothing here deletes raw evidence. The frozen artifact is untouched and remains the complete
record; this is a derived index over it (D112 §5).

**The accepted Decision 113 extension (contract ``e0-compact-evidence/2``).** D112's own
principle -- persist an entry only where it carries information the canonical row does not
already carry -- was applied to the raw observation layer and left the two layers that D112 §7
measured as the remaining cost. D113 applies it to both:

4. **Implicit default resolutions** (:data:`DEFAULT_CANONICAL_RESOLUTION`,
   :func:`is_default_resolution`). A Decision 012 resolution whose complete governed content
   is a deterministic pure function of already-persisted canonical evidence is not written.
   Its content is *defined* by replaying the resolver over the reconstructed observation
   stream, so the logical resolution set is unchanged and only its physical row count moves
   (D113 §§4, 12). Anything carrying information beyond the canonical row -- a competing
   value, a conflict, ambiguity, a malformed alternative, a non-default authority choice, a
   prior-cohort history -- is materialized, because the rule is *checked* per accession rather
   than assumed: what is omitted is exactly what the reconstruction reproduces.
5. **Compact full-index corroboration** (:func:`corroboration_observations`,
   :func:`compact_index_payload`). A ``company.idx`` row that corroborates an already-canonical
   accession is represented by the parsed record the traversal already wrote -- accession
   identity, quarter identity, form, filing date, CIK, line number, and a ``record_sha256``
   over the **complete** raw row -- rather than by three further observation rows that repeat
   it. The row's duplicated ``raw_line`` payload is dropped for the same reason the accession
   payload was (D113 §§3.C, 9). Disagreement, ambiguity, malformed rows, and anything that
   changes association totality are stored explicitly and are never compacted into a boolean
   (D113 §10).

**Neither rule is trusted; both are bound.** :class:`ResolutionDigest` folds the *logical*
resolution -- implicit and explicit alike -- into one ordered digest, and
:class:`CorroborationDigest` does the same for every corroboration assertion, both from
artifact-derived ingredients only, so an independent replay reproduces them without reproducing
this run's identifiers (D113 §§8, 9).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

from disclosure_drift.sec.accession_resolution import (
    RESOLUTION_POLICY_VERSION,
    AccessionResolution,
)
from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik

__all__ = [
    "ALWAYS_ABSENT_RESOLUTION_FIELDS",
    "COMPACT_EVIDENCE_CONTRACT",
    "COMPACT_EVIDENCE_CONTRACT_V1",
    "DEFAULT_CANONICAL_RESOLUTION",
    "EVIDENCE_CONTRACT_KEY",
    "GOVERNED_ACCESSION_FIELDS",
    "INDEX_CORROBORATION_FIELDS",
    "INDEX_PAYLOAD_OMITTED_FIELDS",
    "MEMBERSHIP_ACCESSION_FIELDS",
    "CompactEvidencePolicy",
    "CompactEvidenceSidecar",
    "CorroborationDigest",
    "MemberManifestEntry",
    "ProjectionDigest",
    "ResolutionDigest",
    "canonical_projection",
    "compact_index_payload",
    "corroboration_observations",
    "is_default_resolution",
    "materialized_fields",
    "reconstructed_observations",
]

#: The Decision 112 contract, retained as a named historical constant. No E0 execution ever
#: ran under it -- D112 §6's capacity gate stopped before the first-source canary -- so no
#: durable evidence anywhere carries this label. It is kept so the version string is never
#: reused for different semantics, which is what D113 §11 forbids.
COMPACT_EVIDENCE_CONTRACT_V1: Final = "e0-compact-evidence/1"

#: The contract's explicit version. It is written into every run-local evidence record and
#: into the E0 freeze identity, so a later reader can never mistake compact evidence for the
#: full-observation evidence M2 acquisition produced under the earlier contract.
#:
#: **Version 2 is version 1 plus two rules, and changes none of version 1's.** The accession
#: observation omission rule, the parsed-record projection, and the projection digest are
#: exactly what D112 accepted. What ``/2`` adds is the Decision 113 implicit-resolution rule
#: (:data:`DEFAULT_CANONICAL_RESOLUTION`) and the full-index corroboration representation
#: (:func:`corroboration_observations`), neither of which ``/1`` can state.
COMPACT_EVIDENCE_CONTRACT: Final = "e0-compact-evidence/2"

#: The key a compact parsed-record payload carries so no reader can mistake a governed
#: projection for the complete raw record. A source-native SEC field name is camel-cased
#: alphanumerics, so a dunder key cannot collide with one.
EVIDENCE_CONTRACT_KEY: Final = "__evidence_contract__"

#: The accession fields ``census_accessions`` carries a canonical column for, in the order the
#: digest emits them. Every one is also a key of ``CANONICAL_FIELD_BY_SOURCE_FIELD``; the two
#: are kept in step by test rather than by comment.
GOVERNED_ACCESSION_FIELDS: Final[tuple[str, ...]] = (
    "acceptanceDateTime",
    "cik",
    "filingDate",
    "form",
    "primaryDocument",
    "reportDate",
)

#: The two field names the Decision 094 §6.2 membership projection reads. A blank or malformed
#: rendering of one of these is *not* inert -- it is counted as an invalid rendering and makes
#: its member unbindable -- so these never take the blank-value omission below.
MEMBERSHIP_ACCESSION_FIELDS: Final[frozenset[str]] = frozenset({"cik", "cik_padded"})


@dataclass(frozen=True, slots=True)
class CompactEvidencePolicy:
    """Whether one persistence path writes compact or full accession evidence.

    Off by default and everywhere it is not explicitly passed, so no existing caller, no
    historical M2 acquisition path, and no operational-catalog write changes behaviour. D112 §3
    limits the ruling to E0 successor execution and this object is how that limit is enforced
    in code rather than promised in prose.
    """

    enabled: bool = False
    contract: str = COMPACT_EVIDENCE_CONTRACT

    def __bool__(self) -> bool:
        return self.enabled


#: The full-observation contract, named so a caller states which one it means.
FULL_EVIDENCE: Final = CompactEvidencePolicy(enabled=False)

#: The D112 compact contract.
COMPACT_EVIDENCE: Final = CompactEvidencePolicy(enabled=True)


# --------------------------------------------------------------------------- #
# Canonical projection
# --------------------------------------------------------------------------- #
def _text(value: object) -> str | None:
    """``census.py``'s text normalisation, restated so the round-trip test is exact."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _date_text(value: object) -> str | None:
    """``census.py``'s date normalisation, restated for the same reason."""
    text = _text(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def _padded_cik(value: object) -> str | None:
    try:
        return normalize_cik(str(value))[1]
    except IdentifierError:
        return None


@dataclass(frozen=True, slots=True)
class CanonicalAccessionProjection:
    """The governed values ``census_accessions`` stores for one accession record.

    Built from the payload by exactly the transformations ``CensusCatalog._normalize_accession``
    applies, so ``value_for`` returns what the canonical column will actually hold rather than
    what it is expected to hold.
    """

    acceptance_timestamp: str | None
    registrant_cik_padded: str | None
    filing_date: str | None
    form: str | None
    primary_document: str | None
    report_date: str | None

    def value_for(self, field: str) -> str | None:
        """The canonical column value for one source-native governed field name."""
        return {
            "acceptanceDateTime": self.acceptance_timestamp,
            "cik": self.registrant_cik_padded,
            "filingDate": self.filing_date,
            "form": self.form,
            "primaryDocument": self.primary_document,
            "reportDate": self.report_date,
        }[field]

    def as_digest_mapping(self) -> Mapping[str, str | None]:
        """The projection as the completeness digest renders it."""
        return {field: self.value_for(field) for field in GOVERNED_ACCESSION_FIELDS}


def canonical_projection(payload: Mapping[str, object]) -> CanonicalAccessionProjection:
    """The canonical columns one accession payload produces."""
    return CanonicalAccessionProjection(
        acceptance_timestamp=_text(payload.get("acceptanceDateTime")),
        registrant_cik_padded=_padded_cik(payload.get("cik")),
        filing_date=_date_text(payload.get("filingDate")),
        form=_text(payload.get("form")),
        primary_document=_text(payload.get("primaryDocument")),
        report_date=_date_text(payload.get("reportDate")),
    )


# --------------------------------------------------------------------------- #
# The omission rule
# --------------------------------------------------------------------------- #
def _json(value: object) -> str:
    """``census.py``'s ``raw_value_json`` rendering, restated for the round-trip test."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _is_inert(value: object) -> bool:
    """Whether Decision 012 resolution discards this value before reading it.

    ``_field_observations`` skips ``None`` and any value whose text form is blank. Such a row
    is written, read back, and dropped, so omitting it cannot change a resolution.
    """
    return value is None or str(value).strip() == ""


def materialized_fields(
    payload: Mapping[str, object],
    *,
    first_witness: bool,
) -> tuple[str, ...]:
    """The payload fields whose observation rows this record must still write.

    Governed fields only: an ungoverned field is read by nothing and never appears here.

    Args:
        payload: The accession record's payload.
        first_witness: Whether this record created the canonical ``census_accessions`` row.
            A later witness carries provenance the canonical row does not, so every governed
            field it observes is materialized -- that is the conflicting-alternative-values
            evidence D112 §4.D requires, and the rival rows the conflict pass compares.

    Returns:
        The source-native field names to write, ascending, so the write order matches the
        full-observation path's ``sorted(payload.items())``.
    """
    projection = canonical_projection(payload)
    keep: list[str] = []
    for field in sorted(GOVERNED_ACCESSION_FIELDS):
        if field not in payload:
            continue
        raw = payload[field]
        if not first_witness:
            keep.append(field)
            continue
        if field not in MEMBERSHIP_ACCESSION_FIELDS and _is_inert(raw):
            # Read back and discarded by every consumer; the canonical column is NULL and the
            # reconstruction correctly emits nothing.
            continue
        canonical = projection.value_for(field)
        if canonical is None or _json(canonical) != _json(raw):
            # Malformed, normalised away, or otherwise not recoverable from the canonical
            # column. This is exactly D112 §4.D exception evidence.
            keep.append(field)
    return tuple(keep)


def omitted_field_count(payload: Mapping[str, object], *, first_witness: bool) -> int:
    """How many of this record's field observations the compact contract does not write."""
    return len(payload) - len(materialized_fields(payload, first_witness=first_witness))


# --------------------------------------------------------------------------- #
# Reconstruction
# --------------------------------------------------------------------------- #
#: The ``census_accessions`` columns each governed field is reconstructed from.
_RECONSTRUCTION_COLUMNS: Final[Mapping[str, str]] = {
    "acceptanceDateTime": "acceptance_datetime_sec_raw",
    "cik": "registrant_cik_padded",
    "filingDate": "filing_date_sec",
    "form": "form_type",
    "primaryDocument": "primary_document_name",
    "reportDate": "report_date",
}


def reconstructed_observations(
    row: Mapping[str, object],
) -> Iterator[tuple[str, object]]:
    """Yield the governed ``(field_name, value)`` pairs one canonical row implies.

    The inverse of the omission rule: for each governed field whose canonical column is
    non-NULL, the value the omitted observation carried. Yielded in ascending field order so a
    reconstructed stream and a materialized one interleave into the same order the
    full-observation path produced.

    A NULL column yields nothing, which is correct in both directions -- the field was absent,
    blank, or malformed, and in the malformed case its row was materialized instead.

    Args:
        row: One ``census_accessions`` row, with ``registrant_cik_padded`` supplied by the
            caller as ``printf('%010d', registrant_cik_numeric)`` so this function never has to
            know how the scalar is stored.
    """
    for field in sorted(GOVERNED_ACCESSION_FIELDS):
        value = row.get(_RECONSTRUCTION_COLUMNS[field])
        if value is None:
            continue
        yield field, value


# --------------------------------------------------------------------------- #
# Member manifest and completeness digest
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class MemberManifestEntry:
    """One archive member's D112 §4.A manifest row.

    Every field is a property of the frozen artifact and of the pure parse of it. Nothing here
    depends on a database identifier, a wall clock, or a write order, so replaying the artifact
    reproduces the entry exactly.
    """

    member_ordinal: int
    member_name: str
    payload_byte_length: int
    payload_sha256: str
    parsed_registrants: int
    parsed_accessions: int
    parsed_other: int
    quarantined: int
    structural_failures: int
    omitted_field_observations: int
    materialized_field_observations: int
    projection_digest: str
    disposition: str


class ProjectionDigest:
    """A deterministic ordered digest over every normalized parsed projection (D112 §4.E).

    One running SHA-256 over a canonical line per record and per member, in traversal order.
    Ordinary field values that are no longer materialized as rows are inside it, so an omitted
    observation stays cryptographically represented rather than merely trusted.

    Every ingredient comes from the frozen artifact and the pure parser: source identity, member
    identity and ordinal, record ordinal and class, native identity, the record's own content
    digest, the normalized governed projection, the canonical relation contribution, and the
    exception contribution. No parsed-record identifier, observation identifier, or timestamp
    enters, because those are properties of *this* write rather than of the evidence, and a
    replay must reach the same digest without reproducing them.

    Memory is one line at a time; nothing proportional to the source is retained.
    """

    __slots__ = ("_digest", "_member", "_records", "_source_id")

    #: The field separator, chosen for the same reason ``_stable_id`` chose it: it cannot occur
    #: in a member name, a field name, or JSON output.
    SEPARATOR: Final = "\x1f"

    def __init__(self, source_id: str) -> None:
        self._source_id = source_id
        self._digest = hashlib.sha256()
        self._member = hashlib.sha256()
        self._records = 0
        self._absorb(self._digest, ("source", source_id, COMPACT_EVIDENCE_CONTRACT))

    def _absorb(self, digest: hashlib._Hash, parts: Sequence[str]) -> None:
        digest.update(self.SEPARATOR.join(parts).encode("utf-8"))
        digest.update(b"\x1e")

    def begin_member(self, ordinal: int, member_name: str, payload_sha256: str) -> None:
        """Start one member's sub-digest."""
        self._member = hashlib.sha256()
        self._records = 0
        self._absorb(self._member, ("member", str(ordinal), member_name, payload_sha256))

    def record(
        self,
        *,
        ordinal: int,
        record_class: str,
        native_identity: str,
        record_sha256: str,
        governed: Mapping[str, str | None],
        relation: Sequence[str],
        exception: Sequence[str],
    ) -> None:
        """Absorb one parsed record's normalized projection.

        Args:
            ordinal: The record's position within its member.
            record_class: ``accession``, ``registrant``, or the record's own class prefix.
            native_identity: The parser's native identity for the record.
            record_sha256: The record's content digest, over the **full** raw record.
            governed: The normalized governed projection, rendered field by field.
            relation: The canonical accession-to-registrant contribution, ascending.
            exception: The record's exception contribution -- reason codes, unknown fields --
                ascending.
        """
        self._records += 1
        self._absorb(
            self._member,
            (
                "record",
                str(ordinal),
                record_class,
                native_identity,
                record_sha256,
                _json({key: governed[key] for key in sorted(governed)}),
                _json(sorted(relation)),
                _json(sorted(exception)),
            ),
        )

    def end_member(self) -> str:
        """Close the member, fold it into the source digest, and return its own digest."""
        member = self._member.hexdigest()
        self._absorb(self._digest, ("member-digest", str(self._records), member))
        return member

    def hexdigest(self) -> str:
        """The source's completeness digest so far."""
        return self._digest.hexdigest()


#: The accession-record fields a compact parsed-record payload retains. The six governed
#: fields, plus the accession number, which is the record's own identity rather than a field
#: value and is what makes the retained projection self-describing.
COMPACT_PARSED_RECORD_FIELDS: Final[frozenset[str]] = frozenset(
    {*GOVERNED_ACCESSION_FIELDS, "accessionNumber"}
)


def compact_parsed_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    """One accession record's payload reduced to what anything downstream reads (D112 §§4.B, 7).

    The full payload of an accession-class ``census_parsed_records`` row is read by **nothing**.
    The two readers of that column both restrict themselves by native identity -- historical
    references read a ``registrant:`` row, and full-index materialization reads an
    ``index_row:`` row -- and accession normalization reads the in-memory parsed record, never
    the persisted column. What the row is genuinely needed for is identity, provenance, and
    being the foreign-key target the canonical accession row names; none of that is carried by
    the payload.

    The row therefore stays and its ``record_sha256`` still digests the **complete** raw
    record, so identity is unchanged and the omission is detectable rather than silent. The
    omitted values remain in the frozen artifact and inside the completeness digest.

    Returns:
        The governed projection, carrying :data:`EVIDENCE_CONTRACT_KEY` so a reader can see at
        a glance that it is a projection and under which contract it was taken.
    """
    projected: dict[str, object] = {
        key: value for key, value in payload.items() if key in COMPACT_PARSED_RECORD_FIELDS
    }
    projected[EVIDENCE_CONTRACT_KEY] = COMPACT_EVIDENCE_CONTRACT
    return projected


# --------------------------------------------------------------------------- #
# The Decision 113 implicit resolution rule (D113 §§4-8)
# --------------------------------------------------------------------------- #
#: The name of the implicit rule an omitted Decision 012 resolution resolves under. It is
#: written into the run-local evidence, so a reader is told which rule reconstructs the rows
#: it cannot see rather than having to infer that any are missing.
DEFAULT_CANONICAL_RESOLUTION: Final = "DEFAULT_CANONICAL_RESOLUTION"

#: The Decision 012 canonical fields no source class in ``RESOLVABLE_SOURCE_IDS`` can carry,
#: so every accession's resolution of them is the identical ``absent`` result (D113 §6).
#:
#: This is a property of ``census.CANONICAL_FIELD_BY_SOURCE_FIELD``: no source-native field
#: name maps to either, so no observation of either can exist and no resolver branch but
#: ``absent`` is reachable. It is stated here as the contract's source-class metadata and held
#: in step with the map by test rather than by comment -- and it is deliberately *not* a
#: special case in the omission rule below. An accession that unexpectedly carried one would
#: differ from its reconstruction and would be materialized by the general rule, which is what
#: D113 §6's final paragraph requires.
ALWAYS_ABSENT_RESOLUTION_FIELDS: Final[frozenset[str]] = frozenset(
    {"amendment_relationship", "submitter_cik"}
)


def is_default_resolution(
    resolution: AccessionResolution,
    reconstructed: AccessionResolution,
) -> bool:
    """Whether one accession's resolution is exactly what its canonical evidence implies.

    The D113 §4 predicate, decided by **comparison rather than by rule**: ``reconstructed`` is
    the resolution the reader will rebuild from the canonical row, the corroboration
    assertions, and the frozen contract, and the row is omitted only when the real resolution
    is indistinguishable from it. Every §5 case -- a competing witness, a conflict, ambiguity,
    a malformed alternative, an authority-level choice, a prior-cohort history, any non-default
    resolution -- makes the two differ and is therefore materialized without needing its own
    clause here.

    ``resolution_hash`` covers every governed component of both the field resolutions and the
    cohort consequence and excludes the wall clock, which is precisely the comparison this
    predicate wants.
    """
    return resolution.resolution_hash() == reconstructed.resolution_hash()


class ResolutionDigest:
    """The D113 §8 resolution-completeness digest over the **logical** resolution set.

    One running SHA-256 over a canonical line per accession, in the order the resolution pass
    resolved them -- which is ascending accession order, because that is the order the accepted
    keyset scan produces -- covering *both* the implicitly reconstructed default resolutions and
    the explicitly materialized exception ones. Physical row omission cannot move it, which is
    exactly what makes it the evidence that omission changed nothing: the full-observation path
    and the compact path fold the same lines and reach the same digest.

    Every ingredient is the resolver's own output over evidence derived from the frozen
    artifact -- status, normalized value, authority class, correction reference, reason codes,
    materiality, blocking state, the resolver's own detail text, and the winning and competing
    **counts**. Observation identifiers themselves are excluded for the reason
    :class:`ProjectionDigest` excludes parsed-record identifiers: they are properties of *this*
    catalog's source registration rather than of the evidence, and a replay in a separate world
    must reach the same digest without reproducing them. The counts keep the structural fact --
    how many witnesses competed -- inside the digest.

    Memory is one line at a time; nothing proportional to the accession count is retained.
    """

    __slots__ = ("_accessions", "_digest")

    SEPARATOR: Final = "\x1f"

    def __init__(self) -> None:
        self._digest = hashlib.sha256()
        self._accessions = 0
        self._absorb(
            (
                "resolution",
                RESOLUTION_POLICY_VERSION,
                COMPACT_EVIDENCE_CONTRACT,
                DEFAULT_CANONICAL_RESOLUTION,
            )
        )

    def _absorb(self, parts: Sequence[str]) -> None:
        self._digest.update(self.SEPARATOR.join(parts).encode("utf-8"))
        self._digest.update(b"\x1e")

    def record(self, resolution: AccessionResolution) -> None:
        """Fold one accession's complete logical resolution into the digest."""
        self._accessions += 1
        fields: list[object] = []
        for name in sorted(resolution.fields):
            item = resolution.fields[name]
            fields.append(
                [
                    name,
                    item.status,
                    None if item.value is None else str(item.value),
                    item.authority,
                    item.correction_evidence_id,
                    sorted(item.reason_codes),
                    int(item.is_material),
                    int(item.blocks_dependents),
                    item.detail,
                    len(item.winning_observation_ids),
                    len(item.competing_observation_ids),
                ]
            )
        self._absorb(
            (
                "accession",
                resolution.accession_plain,
                _json(fields),
                _json(
                    [
                        resolution.official_filing_cohort,
                        resolution.accepted_cohort,
                        sorted(resolution.prior_filing_cohorts),
                        int(resolution.cohort_boundary_crossed),
                        int(resolution.requires_2024_approval),
                        sorted(resolution.extra_reason_codes),
                    ]
                ),
            )
        )

    @property
    def accessions(self) -> int:
        """How many accessions have been folded in."""
        return self._accessions

    def hexdigest(self) -> str:
        """The resolution-completeness digest so far."""
        digest = self._digest.copy()
        digest.update(f"count{self.SEPARATOR}{self._accessions}".encode())
        return digest.hexdigest()


# --------------------------------------------------------------------------- #
# The Decision 113 compact full-index corroboration representation (D113 §§9-10)
# --------------------------------------------------------------------------- #
#: The three source-native fields the accepted **R23** materialization observes from one
#: ``company.idx`` row, ascending, and the only definition of that set in the repository.
#: ``cik_padded`` is the one that establishes registrant membership (**R23** §5.2);
#: ``form_type`` and ``date_filed`` enter as consistency evidence only, and Decision 012 gives
#: ``full_index`` authority level 3, so neither can overwrite an authoritative value
#: established by an entity-submissions observation at level 2 (**R23** §5.5). Every one is a
#: key of ``census.CANONICAL_FIELD_BY_SOURCE_FIELD``, held so by test.
INDEX_CORROBORATION_FIELDS: Final[tuple[str, ...]] = ("cik_padded", "date_filed", "form_type")

#: The index-row payload key the compact contract does not persist (D113 §3.C). ``raw_line`` is
#: the complete source text of a row every other key of the same payload already decomposes,
#: and no accepted consumer reads it: the two readers of an ``index_row:`` payload take
#: ``accession_plain``, ``cik_padded``, ``form_type``, ``date_filed`` and ``problems``, and a
#: malformed row's raw text is separately retained by ``census_quarantined_records.raw_excerpt``.
#: ``record_sha256`` still digests the **complete** record including ``raw_line``, so the
#: omission is bound rather than silent and altering the omitted text still moves the identity.
INDEX_PAYLOAD_OMITTED_FIELDS: Final[frozenset[str]] = frozenset({"raw_line"})


def compact_index_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    """One ``company.idx`` row's payload without its duplicated raw line (D113 §3.C).

    Returns:
        Every other key unchanged, carrying :data:`EVIDENCE_CONTRACT_KEY` so the projection is
        self-describing rather than a payload that merely happens to be missing a field.
    """
    projected: dict[str, object] = {
        key: value for key, value in payload.items() if key not in INDEX_PAYLOAD_OMITTED_FIELDS
    }
    projected[EVIDENCE_CONTRACT_KEY] = COMPACT_EVIDENCE_CONTRACT
    return projected


def corroboration_observations(
    payload: Mapping[str, object],
    *,
    cik_padded: str,
) -> Iterator[tuple[str, object]]:
    """Yield the ``(field_name, value)`` pairs one index-row assertion implies.

    The inverse of the corroboration omission: exactly the pairs the accepted R23
    materialization would have written for this row, in ascending field order, with the CIK
    already canonicalized by the caller's identity check so the rendering matches the stored
    one byte for byte.

    Args:
        payload: The persisted ``index_row:`` parsed-record payload.
        cik_padded: The row's canonical zero-padded CIK, from the caller's identity check.
    """
    for field_name in INDEX_CORROBORATION_FIELDS:
        value = cik_padded if field_name == "cik_padded" else payload.get(field_name)
        if value is None:
            continue
        yield field_name, value


class CorroborationDigest:
    """The D113 §9 replay binding over every full-index corroboration assertion.

    One running SHA-256 over a canonical line per index row, in the traversal order the
    accepted materialization reads them, folding the row's own artifact-derived identity: its
    native identity, its content digest over the **complete** raw row, the accession it binds
    to, the CIK, form and filing date it asserts, and the disposition the materialization gave
    it. Replaying the frozen quarter reproduces every line.

    ``parsed_record_id`` and wall clocks are excluded for :class:`ProjectionDigest`'s reason.
    ``record_sha256`` is what keeps the omitted ``raw_line`` inside the binding: altering the
    raw text of a row moves its content digest and therefore moves this digest, which is the
    D113 §13.D proof.
    """

    __slots__ = ("_digest", "_rows")

    SEPARATOR: Final = "\x1f"

    def __init__(self, source_id: str, artifact_sha256: str) -> None:
        self._digest = hashlib.sha256()
        self._rows = 0
        self._absorb(("corroboration", source_id, artifact_sha256, COMPACT_EVIDENCE_CONTRACT))

    def _absorb(self, parts: Sequence[str]) -> None:
        self._digest.update(self.SEPARATOR.join(parts).encode("utf-8"))
        self._digest.update(b"\x1e")

    def record(
        self,
        *,
        native_identity: str,
        record_sha256: str,
        accession_plain: str,
        cik_padded: str,
        observed: Mapping[str, object],
        disposition: str,
    ) -> None:
        """Fold one index row's corroboration assertion into the digest."""
        self._rows += 1
        self._absorb(
            (
                "row",
                native_identity,
                record_sha256,
                accession_plain,
                cik_padded,
                _json({key: observed[key] for key in sorted(observed)}),
                disposition,
            )
        )

    @property
    def rows(self) -> int:
        """How many assertions have been folded in."""
        return self._rows

    def hexdigest(self) -> str:
        """The corroboration digest so far."""
        digest = self._digest.copy()
        digest.update(f"count{self.SEPARATOR}{self._rows}".encode())
        return digest.hexdigest()


# --------------------------------------------------------------------------- #
# The run-local evidence sidecar (D112 §8)
# --------------------------------------------------------------------------- #
#: The sidecar's fixed name inside the run-local working directory.
COMPACT_EVIDENCE_SIDECAR_FILENAME: Final = "compact_evidence.sqlite3"

#: The sidecar's explicit schema version. D112 §8 requires one, and requires it to be part of
#: the E0 freeze identity, so a later reader can tell exactly which shape it is looking at.
COMPACT_EVIDENCE_SCHEMA_VERSION: Final = 2

_SIDECAR_SCHEMA: Final = """
CREATE TABLE IF NOT EXISTS compact_evidence_schema (
    key                 TEXT PRIMARY KEY,
    value               TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS compact_source_members (
    source_observation_id TEXT NOT NULL,
    member_ordinal      INTEGER NOT NULL CHECK (member_ordinal >= 0),
    member_name         TEXT NOT NULL,
    payload_byte_length INTEGER NOT NULL CHECK (payload_byte_length >= 0),
    payload_sha256      TEXT NOT NULL,
    parsed_registrants  INTEGER NOT NULL CHECK (parsed_registrants >= 0),
    parsed_accessions   INTEGER NOT NULL CHECK (parsed_accessions >= 0),
    parsed_other        INTEGER NOT NULL CHECK (parsed_other >= 0),
    quarantined         INTEGER NOT NULL CHECK (quarantined >= 0),
    structural_failures INTEGER NOT NULL CHECK (structural_failures >= 0),
    omitted_field_observations INTEGER NOT NULL CHECK (omitted_field_observations >= 0),
    materialized_field_observations INTEGER NOT NULL
        CHECK (materialized_field_observations >= 0),
    projection_digest   TEXT NOT NULL,
    disposition         TEXT NOT NULL,
    PRIMARY KEY (source_observation_id, member_ordinal)
) STRICT;

CREATE TABLE IF NOT EXISTS compact_source_evidence (
    source_observation_id TEXT PRIMARY KEY,
    source_id           TEXT NOT NULL,
    artifact_sha256     TEXT NOT NULL,
    artifact_byte_length INTEGER NOT NULL CHECK (artifact_byte_length >= 0),
    members             INTEGER NOT NULL CHECK (members >= 0),
    records             INTEGER NOT NULL CHECK (records >= 0),
    omitted_field_observations INTEGER NOT NULL CHECK (omitted_field_observations >= 0),
    materialized_field_observations INTEGER NOT NULL
        CHECK (materialized_field_observations >= 0),
    completeness_digest TEXT NOT NULL,
    contract            TEXT NOT NULL,
    schema_version      INTEGER NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS compact_resolution_evidence (
    resolution_scope    TEXT PRIMARY KEY,
    policy_version      TEXT NOT NULL,
    implicit_rule       TEXT NOT NULL,
    always_absent_fields_json TEXT NOT NULL,
    accessions          INTEGER NOT NULL CHECK (accessions >= 0),
    implicit_resolutions INTEGER NOT NULL CHECK (implicit_resolutions >= 0),
    explicit_resolutions INTEGER NOT NULL CHECK (explicit_resolutions >= 0),
    omitted_field_rows  INTEGER NOT NULL CHECK (omitted_field_rows >= 0),
    materialized_field_rows INTEGER NOT NULL CHECK (materialized_field_rows >= 0),
    omitted_cohort_rows INTEGER NOT NULL CHECK (omitted_cohort_rows >= 0),
    materialized_cohort_rows INTEGER NOT NULL CHECK (materialized_cohort_rows >= 0),
    completeness_digest TEXT NOT NULL,
    contract            TEXT NOT NULL,
    schema_version      INTEGER NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS compact_corroboration_evidence (
    source_observation_id TEXT PRIMARY KEY,
    source_id           TEXT NOT NULL,
    artifact_sha256     TEXT NOT NULL,
    index_rows          INTEGER NOT NULL CHECK (index_rows >= 0),
    corroborating       INTEGER NOT NULL CHECK (corroborating >= 0),
    exceptions          INTEGER NOT NULL CHECK (exceptions >= 0),
    unbound             INTEGER NOT NULL CHECK (unbound >= 0),
    omitted_observations INTEGER NOT NULL CHECK (omitted_observations >= 0),
    materialized_observations INTEGER NOT NULL CHECK (materialized_observations >= 0),
    corroboration_digest TEXT NOT NULL,
    contract            TEXT NOT NULL,
    schema_version      INTEGER NOT NULL
) STRICT;
"""


class CompactEvidenceSidecar:
    """The run-local compact evidence: manifest, digests, and both compaction rules' results.

    D112 §§4.A, 4.E and 8 put the member manifest and the projection digest here. D113 §11 adds
    two more shapes, for the same reason and under the same rules: ``compact_resolution_evidence``,
    which records the implicit rule's name, the always-absent field set, the implicit/explicit
    split, the omitted and materialized row counts, and the resolution-completeness digest; and
    ``compact_corroboration_evidence``, which records each full-index quarter's row counts, its
    corroborating/exception split, and its corroboration digest. Both enter :meth:`identity`.

    It is deliberately **not** a migration and deliberately **not** a table in the working catalog.
    Migration ``0016`` is reserved for the later operational persistence bridge and the
    operational catalog stays at head ``0015``; the working catalog is a byte-for-byte schema
    twin of it and must stay one. The manifest and digest evidence has no home in ``0015`` --
    ``census_archive_members`` exists but is a table E0 is explicitly prohibited from writing --
    so it lives beside the working catalog in its own versioned file, which is exactly the
    shape D112 §8 authorizes.

    Everything it stores is a property of the frozen artifact and the pure parse of it, so an
    auditor replaying the artifact reproduces every row. Nothing here is promoted; consuming it
    later needs its own owner-approved bridge.
    """

    __slots__ = ("_connection", "_path")

    def __init__(self, path: Path) -> None:

        self._path = path
        self._connection = sqlite3.connect(path, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA synchronous = FULL")
        self._connection.executescript(_SIDECAR_SCHEMA)
        for key, value in (
            ("schema_version", str(COMPACT_EVIDENCE_SCHEMA_VERSION)),
            ("contract", COMPACT_EVIDENCE_CONTRACT),
        ):
            self._connection.execute(
                "INSERT INTO compact_evidence_schema (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    @property
    def path(self) -> Path:
        """Where the sidecar is stored."""
        return self._path

    def close(self) -> None:
        """Close the sidecar connection."""
        self._connection.close()

    def record_member(self, source_observation_id: str, entry: MemberManifestEntry) -> None:
        """Persist one member's manifest row."""
        self._connection.execute(
            "INSERT INTO compact_source_members (source_observation_id, member_ordinal, "
            "member_name, payload_byte_length, payload_sha256, parsed_registrants, "
            "parsed_accessions, parsed_other, quarantined, structural_failures, "
            "omitted_field_observations, materialized_field_observations, projection_digest, "
            "disposition) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(source_observation_id, member_ordinal) DO NOTHING",
            (
                source_observation_id,
                entry.member_ordinal,
                entry.member_name,
                entry.payload_byte_length,
                entry.payload_sha256,
                entry.parsed_registrants,
                entry.parsed_accessions,
                entry.parsed_other,
                entry.quarantined,
                entry.structural_failures,
                entry.omitted_field_observations,
                entry.materialized_field_observations,
                entry.projection_digest,
                entry.disposition,
            ),
        )

    def record_source(
        self,
        *,
        source_observation_id: str,
        source_id: str,
        artifact_sha256: str,
        artifact_byte_length: int,
        members: int,
        records: int,
        omitted_field_observations: int,
        materialized_field_observations: int,
        completeness_digest: str,
    ) -> None:
        """Persist one source's completeness digest and its totals."""
        self._connection.execute(
            "INSERT INTO compact_source_evidence (source_observation_id, source_id, "
            "artifact_sha256, artifact_byte_length, members, records, "
            "omitted_field_observations, materialized_field_observations, "
            "completeness_digest, contract, schema_version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(source_observation_id) DO UPDATE SET "
            "members = excluded.members, records = excluded.records, "
            "omitted_field_observations = excluded.omitted_field_observations, "
            "materialized_field_observations = excluded.materialized_field_observations, "
            "completeness_digest = excluded.completeness_digest",
            (
                source_observation_id,
                source_id,
                artifact_sha256,
                artifact_byte_length,
                members,
                records,
                omitted_field_observations,
                materialized_field_observations,
                completeness_digest,
                COMPACT_EVIDENCE_CONTRACT,
                COMPACT_EVIDENCE_SCHEMA_VERSION,
            ),
        )

    def source_evidence(self, source_observation_id: str) -> Mapping[str, object] | None:
        """One source's persisted evidence row, or ``None``."""
        row = self._connection.execute(
            "SELECT * FROM compact_source_evidence WHERE source_observation_id = ?",
            (source_observation_id,),
        ).fetchone()
        return None if row is None else dict(row)

    def members(self, source_observation_id: str) -> tuple[Mapping[str, object], ...]:
        """One source's manifest rows, in traversal order."""
        return tuple(
            dict(row)
            for row in self._connection.execute(
                "SELECT * FROM compact_source_members WHERE source_observation_id = ? "
                "ORDER BY member_ordinal",
                (source_observation_id,),
            ).fetchall()
        )

    def record_resolution(
        self,
        *,
        resolution_scope: str,
        accessions: int,
        implicit_resolutions: int,
        explicit_resolutions: int,
        omitted_field_rows: int,
        materialized_field_rows: int,
        omitted_cohort_rows: int,
        materialized_cohort_rows: int,
        completeness_digest: str,
    ) -> None:
        """Persist the D113 §8 resolution-completeness evidence for one resolution pass.

        The digest is over the **logical** resolution set, so the counts beside it are the
        only place the physical/logical split is recorded -- which is what lets a reader see
        that rows are missing on purpose rather than discover it.
        """
        self._connection.execute(
            "INSERT INTO compact_resolution_evidence (resolution_scope, policy_version, "
            "implicit_rule, always_absent_fields_json, accessions, implicit_resolutions, "
            "explicit_resolutions, omitted_field_rows, materialized_field_rows, "
            "omitted_cohort_rows, materialized_cohort_rows, completeness_digest, contract, "
            "schema_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(resolution_scope) DO UPDATE SET "
            "accessions = excluded.accessions, "
            "implicit_resolutions = excluded.implicit_resolutions, "
            "explicit_resolutions = excluded.explicit_resolutions, "
            "omitted_field_rows = excluded.omitted_field_rows, "
            "materialized_field_rows = excluded.materialized_field_rows, "
            "omitted_cohort_rows = excluded.omitted_cohort_rows, "
            "materialized_cohort_rows = excluded.materialized_cohort_rows, "
            "completeness_digest = excluded.completeness_digest",
            (
                resolution_scope,
                RESOLUTION_POLICY_VERSION,
                DEFAULT_CANONICAL_RESOLUTION,
                _json(sorted(ALWAYS_ABSENT_RESOLUTION_FIELDS)),
                accessions,
                implicit_resolutions,
                explicit_resolutions,
                omitted_field_rows,
                materialized_field_rows,
                omitted_cohort_rows,
                materialized_cohort_rows,
                completeness_digest,
                COMPACT_EVIDENCE_CONTRACT,
                COMPACT_EVIDENCE_SCHEMA_VERSION,
            ),
        )

    def record_corroboration(
        self,
        *,
        source_observation_id: str,
        source_id: str,
        artifact_sha256: str,
        index_rows: int,
        corroborating: int,
        exceptions: int,
        unbound: int,
        omitted_observations: int,
        materialized_observations: int,
        corroboration_digest: str,
    ) -> None:
        """Persist one full-index quarter's D113 §9 corroboration evidence."""
        self._connection.execute(
            "INSERT INTO compact_corroboration_evidence (source_observation_id, source_id, "
            "artifact_sha256, index_rows, corroborating, exceptions, unbound, "
            "omitted_observations, materialized_observations, corroboration_digest, contract, "
            "schema_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(source_observation_id) DO UPDATE SET "
            "index_rows = excluded.index_rows, corroborating = excluded.corroborating, "
            "exceptions = excluded.exceptions, unbound = excluded.unbound, "
            "omitted_observations = excluded.omitted_observations, "
            "materialized_observations = excluded.materialized_observations, "
            "corroboration_digest = excluded.corroboration_digest",
            (
                source_observation_id,
                source_id,
                artifact_sha256,
                index_rows,
                corroborating,
                exceptions,
                unbound,
                omitted_observations,
                materialized_observations,
                corroboration_digest,
                COMPACT_EVIDENCE_CONTRACT,
                COMPACT_EVIDENCE_SCHEMA_VERSION,
            ),
        )

    def resolution_evidence(self, resolution_scope: str) -> Mapping[str, object] | None:
        """One resolution pass's persisted evidence row, or ``None``."""
        row = self._connection.execute(
            "SELECT * FROM compact_resolution_evidence WHERE resolution_scope = ?",
            (resolution_scope,),
        ).fetchone()
        return None if row is None else dict(row)

    def corroboration_evidence(self, source_observation_id: str) -> Mapping[str, object] | None:
        """One full-index quarter's persisted corroboration evidence row, or ``None``."""
        row = self._connection.execute(
            "SELECT * FROM compact_corroboration_evidence WHERE source_observation_id = ?",
            (source_observation_id,),
        ).fetchone()
        return None if row is None else dict(row)

    def member_manifest_digest(self, source_observation_id: str) -> str:
        """A deterministic identity over one source's member manifest, and nothing else.

        The same rows :meth:`identity` folds for ``compact_source_members``, folded by the
        same rule and restricted to one source, so a caller can report the manifest's
        identity without either recomputing it from the parse or defining a second digest.
        An empty manifest -- a single-payload source parsed with no sidecar member -- still
        has an identity, which is the digest of the header alone.
        """
        digest = hashlib.sha256()
        digest.update(
            f"{COMPACT_EVIDENCE_CONTRACT}\x1f{COMPACT_EVIDENCE_SCHEMA_VERSION}\x1f"
            f"{source_observation_id}".encode()
        )
        self._fold(
            digest,
            self._connection.execute(
                "SELECT * FROM compact_source_members WHERE source_observation_id = ? "
                "ORDER BY member_ordinal",
                (source_observation_id,),
            ).fetchall(),
        )
        return digest.hexdigest()

    def identity(self) -> str:
        """A deterministic digest over everything the sidecar holds.

        Written into the E0 freeze identity as D112 §8 requires, so the compact evidence is
        bound to the run rather than merely accompanying it. Built from the rows in a fixed
        order, so two runs over the same frozen artifact produce the same identity.
        """
        digest = hashlib.sha256()
        digest.update(f"{COMPACT_EVIDENCE_CONTRACT}\x1f{COMPACT_EVIDENCE_SCHEMA_VERSION}".encode())
        for table, order in (
            ("compact_source_evidence", "source_observation_id"),
            ("compact_source_members", "source_observation_id, member_ordinal"),
            ("compact_resolution_evidence", "resolution_scope"),
            ("compact_corroboration_evidence", "source_observation_id"),
        ):
            self._fold(
                digest,
                self._connection.execute(
                    f"SELECT * FROM {table} ORDER BY {order}"  # noqa: S608 - fixed literals
                ).fetchall(),
            )
        return digest.hexdigest()

    @staticmethod
    def _fold(digest: hashlib._Hash, rows: Sequence[sqlite3.Row]) -> None:
        """Absorb sidecar rows into ``digest``, canonically and in the order given.

        Stated once so :meth:`identity` and :meth:`member_manifest_digest` cannot drift into
        two renderings of the same rows.
        """
        for row in rows:
            digest.update(_json({key: row[key] for key in sorted(row.keys())}).encode("utf-8"))
            digest.update(b"\x1e")
