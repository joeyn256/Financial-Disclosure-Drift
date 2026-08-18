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

from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik

__all__ = [
    "COMPACT_EVIDENCE_CONTRACT",
    "EVIDENCE_CONTRACT_KEY",
    "GOVERNED_ACCESSION_FIELDS",
    "MEMBERSHIP_ACCESSION_FIELDS",
    "CompactEvidencePolicy",
    "CompactEvidenceSidecar",
    "MemberManifestEntry",
    "ProjectionDigest",
    "canonical_projection",
    "materialized_fields",
    "reconstructed_observations",
]

#: The contract's explicit version. It is written into every run-local evidence record and
#: into the E0 freeze identity, so a later reader can never mistake compact evidence for the
#: full-observation evidence M2 acquisition produced under the earlier contract.
COMPACT_EVIDENCE_CONTRACT: Final = "e0-compact-evidence/1"

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
# The run-local evidence sidecar (D112 §8)
# --------------------------------------------------------------------------- #
#: The sidecar's fixed name inside the run-local working directory.
COMPACT_EVIDENCE_SIDECAR_FILENAME: Final = "compact_evidence.sqlite3"

#: The sidecar's explicit schema version. D112 §8 requires one, and requires it to be part of
#: the E0 freeze identity, so a later reader can tell exactly which shape it is looking at.
COMPACT_EVIDENCE_SCHEMA_VERSION: Final = 1

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
"""


class CompactEvidenceSidecar:
    """The run-local member manifest and completeness digest (D112 §§4.A, 4.E, 8).

    Deliberately **not** a migration and deliberately **not** a table in the working catalog.
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
        ):
            for row in self._connection.execute(
                f"SELECT * FROM {table} ORDER BY {order}"  # noqa: S608 - fixed literals
            ).fetchall():
                digest.update(_json({key: row[key] for key in sorted(row.keys())}).encode("utf-8"))
                digest.update(b"\x1e")
        return digest.hexdigest()
