"""The accepted Decision 112 compact E0 evidence contract.

D111 closed E0's throughput, journal, and blast-radius defects and returned one MAJOR it could
not close: the persistence contract itself over-materializes real source evidence, projecting
about 246 GB for the first planned source before the resolution layer and the remaining 75
sources. D112 is the owner's answer -- the frozen artifact is the authoritative complete raw
evidence, and E0's relational evidence exists to prove traversal, identity, association,
exceptions, and replayability rather than to duplicate every ordinary raw field value into
SQLite.

This module holds the proofs. Three claims carry the whole contract, and each is proved against
a world built to break it rather than to agree with it:

**Equivalence.** Running the same synthetic sources through the full-observation path and the
compact path must produce byte-identical governed output -- the canonical accession set, the
registrant set, the accession-to-registrant relation, conflicts, quarantines, structural
failures, historical references, association totality, and every Decision 012 field and cohort
resolution. Only the count of redundant raw observation rows is allowed to differ, which is the
owner-approved semantic change (D112 §10).

**Sufficiency.** The D093 §6 linkage resolver must answer accession existence, exact form, exact
filing date, the complete registrant association set, set completeness, and the
`ZERO / EXACTLY_ONE / MULTIPLE / UNESTABLISHED_ASSOCIATION_SET` classification from the compact
canonical rows **alone**. That is proved by executing it against a connection on which every
field-observation table has been made unreadable, so a resolver that needed one would fail
rather than quietly succeed (D112 §9).

**Replay.** The completeness digest must be reproducible from the frozen artifact by a second,
independent traversal that shares no state with the first (D112 §§4.E, 14).

The fixture is deliberately hostile. It carries a joint filing whose two witnesses agree, a
joint filing whose witnesses disagree on `form`, a malformed `filingDate` that no canonical
column can hold, a blank `reportDate`, a `form` padded with whitespace that normalisation would
silently rewrite, absent optional fields, ungoverned fields that no consumer reads, and a
quarter of `company.idx` binding a second registrant to an accession the submissions layer
established. Every one of those is a branch of the omission rule.

Everything runs over synthetic archives and disposable catalogs beneath ``tmp_path``. No test
resolves, opens, names, or infers the accepted private evidence root, none reads a real SEC
artifact, and none touches a real catalog.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d110_bounded_parse_memory as world  # noqa: E402

from disclosure_drift.m3 import offline_parse as op  # noqa: E402
from disclosure_drift.m3.compact_evidence import (  # noqa: E402
    COMPACT_EVIDENCE,
    COMPACT_EVIDENCE_CONTRACT,
    COMPACT_EVIDENCE_SCHEMA_VERSION,
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    EVIDENCE_CONTRACT_KEY,
    FULL_EVIDENCE,
    GOVERNED_ACCESSION_FIELDS,
    CompactEvidenceSidecar,
    MemberManifestEntry,
    ProjectionDigest,
    canonical_projection,
    compact_parsed_payload,
    materialized_fields,
    reconstructed_observations,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.sec.census import (  # noqa: E402
    CANONICAL_FIELD_BY_SOURCE_FIELD,
    CensusCatalog,
)
from disclosure_drift.sec.observation_catalog import load_observations  # noqa: E402
from disclosure_drift.sec.source_registry import SOURCES  # noqa: E402
from disclosure_drift.storage.sqlite import connect, transaction  # noqa: E402

_BULK = "sec_bulk_submissions"
_INDEX = "sec_full_index_company"
_INDEX_OBSERVATION = "obs-full-index-1"
_INDEX_INSTANCE = "instance-full-index-1"
_INDEX_RELATIVE = "raw/sec/indexes/company.idx"


def _plain(dashed: str) -> str:
    """The canonical dash-free accession identity ``census_accessions`` keys on."""
    return dashed.replace("-", "")


# ==========================================================================
# A synthetic world built to break the omission rule
# ==========================================================================
def _filing(
    accession: str,
    *,
    form: str = "10-K",
    filing_date: str = "2024-02-01",
    report_date: str | None = "2023-12-31",
    acceptance: str | None = "2024-02-01T16:30:00.000Z",
    primary_document: str | None = "form10k.htm",
) -> dict[str, Any]:
    """One ``filings.recent`` row, with every optional field independently controllable."""
    row: dict[str, Any] = {
        "accessionNumber": accession,
        "filingDate": filing_date,
        "form": form,
        # Ungoverned throughout: no accepted consumer reads any of these, which is exactly
        # what the omission rule claims and what the inertness test holds it to.
        "act": "34",
        "fileNumber": "001-00001",
        "filmNumber": "24000001",
        "items": "",
        "size": 123456,
        "isXBRL": 1,
        "isInlineXBRL": 1,
        "primaryDocDescription": "ANNUAL REPORT",
    }
    if report_date is not None:
        row["reportDate"] = report_date
    if acceptance is not None:
        row["acceptanceDateTime"] = acceptance
    if primary_document is not None:
        row["primaryDocument"] = primary_document
    return row


#: Every accession the fixture creates, and what makes each one interesting.
_JOINT_AGREE = "0000000001-24-000001"
_JOINT_CONFLICT = "0000000001-24-000002"
_MALFORMED_DATE = "0000000001-24-000003"
_BLANK_REPORT = "0000000001-24-000004"
_PADDED_FORM = "0000000001-24-000005"
_SPARSE = "0000000001-24-000006"
_ORDINARY = "0000000002-24-000001"
_INDEX_JOINT = "0000000002-24-000002"


def _member_one() -> list[dict[str, Any]]:
    return [
        _filing(_JOINT_AGREE),
        _filing(_JOINT_CONFLICT, form="10-K"),
        # `filingDate` is a required field, so a malformed one is not quarantined -- it is
        # preserved as a value ``_date_text`` cannot hold, which the canonical column renders
        # NULL and the compact contract must therefore materialize.
        _filing(_MALFORMED_DATE, filing_date="2024-13-45"),
        # Blank optional value: written by the full path, discarded unread by every consumer,
        # and correctly omitted.
        _filing(_BLANK_REPORT, report_date=""),
        # Normalisation would silently rewrite this; the round-trip test refuses to let it.
        _filing(_PADDED_FORM, form="  10-K  "),
        # Every optional field absent.
        _filing(_SPARSE, report_date=None, acceptance=None, primary_document=None),
    ]


def _member_two() -> list[dict[str, Any]]:
    return [
        # The same two accessions from a second registrant: a joint filing. One pair agrees,
        # the other disagrees on `form`, which is a real Decision 012 conflict.
        _filing(_JOINT_AGREE),
        _filing(_JOINT_CONFLICT, form="10-K/A"),
        _filing(_ORDINARY),
        _filing(_INDEX_JOINT),
    ]


def _document(cik: int, filings: list[dict[str, Any]]) -> dict[str, Any]:
    padded = f"{cik:010d}"
    keys = sorted({key for row in filings for key in row})
    return {
        "cik": padded,
        "name": f"SYNTHETIC {cik}",
        "sic": "2834",
        "fiscalYearEnd": "1231",
        "tickers": [f"SY{cik}"],
        "exchanges": ["Nasdaq"],
        "formerNames": [{"name": f"OLD {cik}", "from": "2018-01-01", "to": "2020-01-01"}],
        "filings": {
            "recent": {key: [row.get(key, "") for row in filings] for key in keys},
            "files": [],
        },
    }


def _write_bulk_archive(path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "CIK0000000001-member-000000.json",
            json.dumps(_document(1, _member_one()), sort_keys=True),
        )
        archive.writestr(
            "CIK0000000002-member-000001.json",
            json.dumps(_document(2, _member_two()), sort_keys=True),
        )
    return path.read_bytes()


def _write_company_index(path: Path) -> bytes:
    """A ``company.idx`` quarter binding a third registrant to one established accession."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Company Name                  Form Type   CIK         Date Filed  File Name",
        "-" * 100,
        # A co-registrant the submissions layer could not state: full index is the only
        # accepted evidence that a filing is joint.
        f"SYNTHETIC 3                   10-K        3           2024-02-01  "
        f"edgar/data/3/{_INDEX_JOINT}.txt",
        # A corroborating row for an accession already established, same registrant.
        f"SYNTHETIC 2                   10-K        2           2024-02-01  "
        f"edgar/data/2/{_ORDINARY}.txt",
    ]
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    path.write_bytes(payload)
    return payload


def _seed_index_source(database: Path, payload: bytes) -> None:
    digest = hashlib.sha256(payload).hexdigest()
    with connect(database, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "INSERT INTO census_source_observations (observation_id, source_id, "
            "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
            "stored_sha256, logical_sha256, content_sha256, stored_size_bytes, "
            "content_size_bytes, storage_representation, relative_storage_path, "
            "parser_version, recorded_at_utc) VALUES (?, 'sec_full_index_company', "
            "'req/index/1', 'https://example.invalid/company.idx', 'census', ?, "
            "'stored_new', ?, ?, ?, ?, ?, 'identical', ?, 'company-idx/1.0', ?)",
            (
                _INDEX_OBSERVATION,
                world._AT,
                digest,
                digest,
                digest,
                len(payload),
                len(payload),
                _INDEX_RELATIVE,
                world._AT,
            ),
        )
        active.execute(
            "INSERT INTO census_plan_sources (census_run_id, source_instance_id, "
            "source_id, request_identity, required, source_scope, retrieval_state, "
            "snapshot_state, parser_state, catalog_state, qa_state, "
            "unresolved_blocking_reasons_json, observation_id, successful_terminal, "
            "updated_at_utc) VALUES (?, ?, 'sec_full_index_company', 'req/index/1', 1, "
            "'base', 'retrieved', 'verified', 'not_started', 'committed', 'passed', "
            "'[]', ?, 1, ?)",
            (world._RUN, _INDEX_INSTANCE, _INDEX_OBSERVATION, world._AT),
        )


def _build_world(root: Path) -> tuple[Path, DataTree]:
    """A disposable catalog plus data tree holding the hostile bulk archive and one index."""
    tree = DataTree.from_root(root / "data")
    database = root / "catalog.sqlite3"
    raw = _write_bulk_archive(tree.data_root / world._ARCHIVE_RELATIVE)
    world._seed_catalog(database, tree, raw)
    _seed_index_source(database, _write_company_index(tree.data_root / _INDEX_RELATIVE))
    return database, tree


# ==========================================================================
# Driving both contracts over the same world
# ==========================================================================
class _StubWriter:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection


def _run(root: Path, *, compact: bool) -> Path:
    """Parse, resolve, and associate the whole world under one evidence contract."""
    database, tree = _build_world(root)
    policy = COMPACT_EVIDENCE if compact else FULL_EVIDENCE
    store = op.SnapshotStore(tree)
    with connect(database, writer=True) as connection:
        store.adopt(load_observations(connection))
        observations = op._observations_by_id(connection)
        catalog = CensusCatalog(_StubWriter(connection), compact_evidence=policy)  # type: ignore[arg-type]

        bulk = observations[world._OBSERVATION]
        catalog.persist_streamed(
            op._stream_bulk_submissions(store, bulk),
            parser_id=op._BULK_PARSER_ID,
            parser_version=SOURCES[_BULK].parser_version,
            source_observation_id=bulk.observation_id,
        )
        index = observations[_INDEX_OBSERVATION]
        outcome, references = op._parse_source(connection, store, index)
        result = catalog.persist(
            outcome, historical_references=references, source_observation_id=index.observation_id
        )
        op._materialize_full_index_registrants(
            connection,
            observation=index,
            parser_run_id=result.parser_run_id,
            recorded=world._AT,
        )
        catalog.count_persisted_accession_resolutions()
        op.materialize_census_associations(connection, compact_evidence=compact)
    return database


@pytest.fixture(scope="module")
def both_paths(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """One world, run once under each contract. Module-scoped: the runs are pure."""
    root = tmp_path_factory.mktemp("d112")
    return _run(root / "full", compact=False), _run(root / "compact", compact=True)


def _rows(database: Path, table: str, *, drop: tuple[str, ...] = ()) -> list[tuple[Any, ...]]:
    with connect(database, writer=False) as connection:
        columns = [
            str(row["name"])
            for row in connection.execute(f"PRAGMA table_info({table})")  # noqa: S608
            if not str(row["name"]).endswith(("_at_utc", "_at")) and str(row["name"]) not in drop
        ]
        if not columns:
            return []
        projection = ", ".join(columns)
        return sorted(
            tuple(row)
            for row in connection.execute(f"SELECT {projection} FROM {table}")  # noqa: S608
        )


# ==========================================================================
# The omission rule itself
# ==========================================================================
def test_the_governed_field_set_is_exactly_what_a_consumer_reads() -> None:
    """Every governed field is a canonical field, and no canonical accession field is missed.

    The omission rule's whole safety argument is that an unlisted field is read by nothing.
    That argument is only as good as the two sets agreeing, so they are compared rather than
    described.
    """
    assert set(GOVERNED_ACCESSION_FIELDS) <= set(CANONICAL_FIELD_BY_SOURCE_FIELD)
    # The remaining canonical names belong to the full index, whose observations are always
    # materialized because they are a second witness by construction.
    assert set(CANONICAL_FIELD_BY_SOURCE_FIELD) - set(GOVERNED_ACCESSION_FIELDS) == {
        "cik_padded",
        "date_filed",
        "form_type",
    }


def test_an_ordinary_first_witness_materializes_nothing() -> None:
    payload = _filing(_ORDINARY)
    payload["cik"] = "0000000002"
    assert materialized_fields(payload, first_witness=True) == ()


def test_a_second_witness_materializes_every_governed_field() -> None:
    payload = _filing(_JOINT_AGREE)
    payload["cik"] = "0000000002"
    assert set(materialized_fields(payload, first_witness=False)) == {
        "acceptanceDateTime",
        "cik",
        "filingDate",
        "form",
        "primaryDocument",
        "reportDate",
    }


@pytest.mark.parametrize(
    ("payload_update", "expected"),
    [
        ({"filingDate": "2024-13-45"}, {"filingDate"}),
        ({"form": "  10-K  "}, {"form"}),
        ({"reportDate": "not-a-date"}, {"reportDate"}),
        ({"acceptanceDateTime": " 2024-02-01T16:30:00.000Z"}, {"acceptanceDateTime"}),
        ({"primaryDocument": " form10k.htm"}, {"primaryDocument"}),
        ({"cik": "2"}, {"cik"}),
        ({"reportDate": ""}, set()),
        ({"primaryDocument": ""}, set()),
    ],
)
def test_a_value_the_canonical_column_cannot_hold_is_materialized(
    payload_update: dict[str, Any], expected: set[str]
) -> None:
    """Malformed and normalised values are exception evidence; blank ones are inert.

    A blank optional value is dropped unread by Decision 012 resolution, so omitting it cannot
    change a resolution. A value the canonical column would rewrite or reject cannot be
    reconstructed and is therefore written individually -- which is D112 §4.D, not an
    exception to it.
    """
    payload = _filing(_ORDINARY)
    payload["cik"] = "0000000002"
    payload.update(payload_update)
    assert set(materialized_fields(payload, first_witness=True)) == expected


def test_a_blank_membership_rendering_is_never_treated_as_inert() -> None:
    """A blank ``cik`` is an invalid rendering the membership projection counts, not a nothing.

    This is the one place the inertness shortcut would have been wrong: Decision 012 drops a
    blank value, but ``_membership_cik`` counts it as an invalid rendering and makes its member
    unbindable. Omitting it would silently change association totality.
    """
    payload = _filing(_ORDINARY)
    payload["cik"] = ""
    assert "cik" in materialized_fields(payload, first_witness=True)


def test_the_reconstruction_inverts_the_projection() -> None:
    payload = _filing(_ORDINARY)
    payload["cik"] = "0000000002"
    projection = canonical_projection(payload)
    row = {
        "form_type": projection.form,
        "filing_date_sec": projection.filing_date,
        "report_date": projection.report_date,
        "acceptance_datetime_sec_raw": projection.acceptance_timestamp,
        "primary_document_name": projection.primary_document,
        "registrant_cik_padded": projection.registrant_cik_padded,
    }
    rebuilt = dict(reconstructed_observations(row))
    assert rebuilt == {field: payload[field] for field in GOVERNED_ACCESSION_FIELDS}


# ==========================================================================
# D112 §10 -- output and information equivalence
# ==========================================================================
_EQUAL_TABLES = (
    "census_parser_runs",
    "census_quarantined_records",
    "census_structural_observations",
    "census_registrants",
    "census_registrant_observations",
    "census_accessions",
    "census_accession_registrants",
    "census_accession_field_resolutions",
    "census_accession_cohort_resolutions",
    "census_historical_references",
    "census_malformed_historical_references",
    "census_candidate_lineage_edges",
)


@pytest.mark.parametrize("table", _EQUAL_TABLES)
def test_every_governed_table_is_row_identical(both_paths: tuple[Path, Path], table: str) -> None:
    """The canonical accession set, registrant set, relation, and resolutions are unchanged.

    This is the claim the owner-approved semantic change is allowed to cost nothing. The
    comparison is row for row over every column that is not a wall clock, including the
    resolution rows' winning and competing observation identifier lists -- which is the
    sharpest part of it, because those name observations the compact catalog never stored.
    """
    full, compact = both_paths
    assert _rows(compact, table) == _rows(full, table)


def test_parsed_records_agree_on_everything_but_the_redundant_payload(
    both_paths: tuple[Path, Path],
) -> None:
    """Identity, provenance, drift, and flags are identical; only the payload is projected."""
    full, compact = both_paths
    assert _rows(compact, "census_parsed_records", drop=("payload_json",)) == _rows(
        full, "census_parsed_records", drop=("payload_json",)
    )


def test_the_compact_payload_is_a_labelled_projection_of_accession_records_only(
    both_paths: tuple[Path, Path],
) -> None:
    """Only accession-class payloads shrink, and the projection says so about itself."""
    full, compact = both_paths
    with connect(full, writer=False) as reference, connect(compact, writer=False) as subject:
        for row in subject.execute(
            "SELECT parsed_record_id, native_identity, payload_json FROM census_parsed_records"
        ).fetchall():
            original = json.loads(
                str(
                    reference.execute(
                        "SELECT payload_json FROM census_parsed_records WHERE parsed_record_id = ?",
                        (str(row["parsed_record_id"]),),
                    ).fetchone()["payload_json"]
                )
            )
            payload = json.loads(str(row["payload_json"]))
            if not str(row["native_identity"]).startswith("accession:"):
                assert payload == original
                continue
            assert payload.pop(EVIDENCE_CONTRACT_KEY) == COMPACT_EVIDENCE_CONTRACT
            assert payload == {key: value for key, value in original.items() if key in payload}
            assert set(payload) <= {*GOVERNED_ACCESSION_FIELDS, "accessionNumber"}


def test_the_compact_observation_rows_are_a_subset_of_the_full_ones(
    both_paths: tuple[Path, Path],
) -> None:
    """Compaction only ever removes rows. It never invents an observation.

    Stated as a subset rather than as a count so a compact path that wrote a *different* row --
    a wrong identifier, a re-rendered value, a borrowed provenance -- fails here even if it
    happened to write the same number of them.
    """
    full, compact = both_paths
    stored = set(_rows(compact, "census_accession_observations"))
    assert stored < set(_rows(full, "census_accession_observations"))


def test_compaction_actually_removed_the_ordinary_rows(both_paths: tuple[Path, Path]) -> None:
    """The non-vacuity guard: a contract that quietly wrote everything would pass every
    equivalence test above and deliver nothing. It has to remove most of the rows."""
    full, compact = both_paths
    with connect(full, writer=False) as a, connect(compact, writer=False) as b:
        before = int(a.execute("SELECT COUNT(*) FROM census_accession_observations").fetchone()[0])
        after = int(b.execute("SELECT COUNT(*) FROM census_accession_observations").fetchone()[0])
    assert before > 0
    assert after < before / 2


def test_every_conflicting_observation_survives_compaction(both_paths: tuple[Path, Path]) -> None:
    """A disagreement is never thinned, and both sides of it are present.

    The conflict pass marks a row only when it can see a sibling that differs, so a contract
    that stored the newcomer and reconstructed the incumbent would silently lose every
    conflict. The fixture's joint filing disagrees on ``form`` precisely to make that
    detectable.
    """
    full, compact = both_paths

    def conflicting(database: Path) -> set[tuple[str, str, str]]:
        with connect(database, writer=False) as connection:
            return {
                (str(row["accession_plain"]), str(row["field_name"]), str(row["raw_value_json"]))
                for row in connection.execute(
                    "SELECT accession_plain, field_name, raw_value_json "
                    "FROM census_accession_observations WHERE conflict_indicator = 1"
                ).fetchall()
            }

    expected = conflicting(full)
    assert expected, "the fixture must produce a real conflict or it proves nothing"
    assert conflicting(compact) == expected


def test_the_joint_filing_reaches_the_same_association_state(both_paths: tuple[Path, Path]) -> None:
    """Association totality, cardinality, and the nulled scalar are identical."""
    full, compact = both_paths
    for database in both_paths:
        with connect(database, writer=False) as connection:
            rows = connection.execute(
                "SELECT accession_plain, COUNT(*) AS members FROM census_accession_registrants "
                "WHERE association_class = 'substantive' GROUP BY accession_plain "
                "HAVING members > 1"
            ).fetchall()
            assert rows, "the fixture must establish at least one multi-registrant accession"
            for row in rows:
                scalar = connection.execute(
                    "SELECT registrant_cik_numeric FROM census_accessions "
                    "WHERE accession_plain = ?",
                    (str(row["accession_plain"]),),
                ).fetchone()
                assert scalar["registrant_cik_numeric"] is None
    assert _rows(compact, "census_accession_registrants") == _rows(
        full, "census_accession_registrants"
    )


# ==========================================================================
# D112 §9 -- downstream sufficiency, proved by removing the fallback
# ==========================================================================
_FIELD_OBSERVATION_TABLES = ("census_accession_observations", "census_parsed_records")


def _linkage_resolution(
    connection: sqlite3.Connection,
    *,
    asserted_form: str,
    asserted_filing_date: str,
    registrant_cik: int,
) -> tuple[str, tuple[str, ...]]:
    """The accepted D093 §6 resolver, over the compact canonical evidence alone.

    Predicate B is an exact form match, predicate C an exact filing-date match, and D the union
    over the complete established association set, deduped by canonical accession. Registrant
    scope comes from ``census_accession_registrants`` and never from the nullable scalar, and an
    unestablished set fails closed.

    Every table it reads is a canonical one. Nothing here reads a field observation or a parsed
    record, which is what the test around it makes unfakeable.
    """
    accessions = [
        str(row["accession_plain"])
        for row in connection.execute(
            "SELECT r.accession_plain FROM census_accession_registrants AS r "
            "WHERE r.registrant_cik_numeric = ? AND r.association_class = 'substantive' "
            "ORDER BY r.accession_plain",
            (registrant_cik,),
        ).fetchall()
    ]
    if not accessions:
        return "ZERO", ()
    matches: list[str] = []
    for accession in accessions:
        row = connection.execute(
            "SELECT form_type, filing_date_sec, registrant_set_completeness "
            "FROM census_accessions WHERE accession_plain = ?",
            (accession,),
        ).fetchone()
        if row is None:
            continue
        if str(row["registrant_set_completeness"]) != "established":
            return "UNESTABLISHED_ASSOCIATION_SET", ()
        if str(row["form_type"]) == asserted_form and row["filing_date_sec"] == (
            asserted_filing_date
        ):
            matches.append(accession)
    unique = tuple(sorted(set(matches)))
    if not unique:
        return "ZERO", ()
    return ("EXACTLY_ONE" if len(unique) == 1 else "MULTIPLE"), unique


def _connection_without_field_observations(database: Path) -> sqlite3.Connection:
    """A read-only connection on which every field-observation table raises.

    An authorizer denies the table rather than the statement, so a resolver that reaches for
    one gets ``sqlite3.DatabaseError`` instead of quietly succeeding on evidence D112 §9 says
    it must not need. That is the difference between proving sufficiency and asserting it.
    """
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row

    def authorizer(action: int, first: str | None, *_rest: object) -> int:
        if first in _FIELD_OBSERVATION_TABLES:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(authorizer)
    return connection


def test_the_denial_harness_actually_denies(both_paths: tuple[Path, Path]) -> None:
    """The sufficiency proof is worthless if the authorizer is inert, so it is tested first."""
    _, compact = both_paths
    connection = _connection_without_field_observations(compact)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("SELECT COUNT(*) FROM census_accession_observations").fetchone()
    finally:
        connection.close()


@pytest.mark.parametrize(
    ("registrant", "form", "filing_date"),
    [
        (2, "10-K", "2024-02-01"),
        (3, "10-K", "2024-02-01"),
        (1, "10-K", "2024-02-01"),
        (2, "10-K", "1999-01-01"),
        (99, "10-K", "2024-02-01"),
    ],
)
def test_linkage_resolves_identically_from_compact_evidence_alone(
    both_paths: tuple[Path, Path], registrant: int, form: str, filing_date: str
) -> None:
    """§9 in one assertion: same classification, same accessions, no field observations read."""
    full, compact = both_paths
    with connect(full, writer=False) as reference:
        expected = _linkage_resolution(
            reference,
            asserted_form=form,
            asserted_filing_date=filing_date,
            registrant_cik=registrant,
        )
    connection = _connection_without_field_observations(compact)
    try:
        actual = _linkage_resolution(
            connection,
            asserted_form=form,
            asserted_filing_date=filing_date,
            registrant_cik=registrant,
        )
    finally:
        connection.close()
    assert actual == expected


def test_the_fixture_exercises_more_than_one_classification(both_paths: tuple[Path, Path]) -> None:
    """Non-vacuity: a resolver that always answered ``ZERO`` would pass the test above."""
    full, _ = both_paths
    with connect(full, writer=False) as connection:
        verdicts = {
            _linkage_resolution(
                connection,
                asserted_form="10-K",
                asserted_filing_date="2024-02-01",
                registrant_cik=cik,
            )[0]
            for cik in (1, 2, 3, 99)
        }
    assert len(verdicts) > 1


def test_accession_facts_are_readable_without_any_field_observation_table(
    both_paths: tuple[Path, Path],
) -> None:
    """Existence, exact form, exact filing date, and source disposition, from canonical rows."""
    _, compact = both_paths
    connection = _connection_without_field_observations(compact)
    try:
        row = connection.execute(
            "SELECT accession_plain, form_type, filing_date_sec, acceptance_datetime_sec_raw "
            "FROM census_accessions WHERE accession_plain = ?",
            (_plain(_ORDINARY),),
        ).fetchone()
        assert row is not None
        assert str(row["form_type"]) == "10-K"
        assert str(row["filing_date_sec"]) == "2024-02-01"
        dispositions = connection.execute(
            "SELECT parser_state FROM census_plan_sources ORDER BY source_instance_id"
        ).fetchall()
        assert [str(item["parser_state"]) for item in dispositions]
    finally:
        connection.close()


# ==========================================================================
# D112 §§4.E, 14 -- the completeness digest and its replay
# ==========================================================================
def _digest_of(tree: DataTree, database: Path) -> tuple[str, list[str]]:
    """Traverse the frozen archive and build the completeness digest from the parse alone."""
    store = op.SnapshotStore(tree)
    with connect(database, writer=False) as connection:
        store.adopt(load_observations(connection))
        observation = op._observations_by_id(connection)[world._OBSERVATION]
        digest = ProjectionDigest(observation.source_id)
        members: list[str] = []
        for ordinal, (outcome, _references) in enumerate(
            op._stream_bulk_submissions(store, observation)
        ):
            name = next(
                (record.location.member_name for record in outcome.records),
                f"member-{ordinal}",
            )
            digest.begin_member(ordinal, str(name), hashlib.sha256(str(name).encode()).hexdigest())
            for index, record in enumerate(outcome.records):
                projection = canonical_projection(record.payload)
                relation = (
                    [str(projection.registrant_cik_padded)]
                    if record.native_identity.startswith("accession:")
                    and projection.registrant_cik_padded
                    else []
                )
                digest.record(
                    ordinal=index,
                    record_class=record.native_identity.split(":", 1)[0],
                    native_identity=record.native_identity,
                    record_sha256=record.record_sha256,
                    governed=dict(projection.as_digest_mapping()),
                    relation=relation,
                    exception=list(record.reason_codes) + list(record.unknown_fields),
                )
            members.append(digest.end_member())
        return digest.hexdigest(), members


def test_the_completeness_digest_replays_from_the_frozen_artifact(tmp_path: Path) -> None:
    """§14: an independent second traversal reproduces the digest exactly.

    Two separately built worlds, two separate archives on disk, two traversals sharing no
    object. Equality is therefore a property of the frozen bytes and the pure parse of them,
    which is what makes the omitted ordinary values cryptographically represented rather than
    merely trusted.
    """
    first_database, first_tree = _build_world(tmp_path / "a")
    second_database, second_tree = _build_world(tmp_path / "b")
    assert _digest_of(first_tree, first_database) == _digest_of(second_tree, second_database)


def test_the_digest_covers_values_no_row_retains(tmp_path: Path) -> None:
    """Changing an omitted ordinary value must move the digest.

    ``reportDate`` on an ordinary first witness is exactly a value the compact contract does
    not materialize. If the digest did not bind it, the omission would be unrecoverable rather
    than merely unmaterialized.
    """
    database, tree = _build_world(tmp_path / "a")
    baseline, _members = _digest_of(tree, database)

    payload = _filing(_ORDINARY)
    payload["cik"] = "0000000002"
    unchanged = ProjectionDigest("sec_bulk_submissions")
    unchanged.begin_member(0, "m", "d")
    unchanged.record(
        ordinal=0,
        record_class="accession",
        native_identity=f"accession:{_ORDINARY}",
        record_sha256="x",
        governed=dict(canonical_projection(payload).as_digest_mapping()),
        relation=["0000000002"],
        exception=[],
    )
    unchanged.end_member()

    moved = dict(payload, reportDate="2022-12-31")
    changed = ProjectionDigest("sec_bulk_submissions")
    changed.begin_member(0, "m", "d")
    changed.record(
        ordinal=0,
        record_class="accession",
        native_identity=f"accession:{_ORDINARY}",
        record_sha256="x",
        governed=dict(canonical_projection(moved).as_digest_mapping()),
        relation=["0000000002"],
        exception=[],
    )
    changed.end_member()

    assert baseline
    assert unchanged.hexdigest() != changed.hexdigest()


def test_the_digest_binds_member_order(tmp_path: Path) -> None:
    """Two members swapped is a different traversal and must be a different digest."""
    forward = ProjectionDigest("sec_bulk_submissions")
    backward = ProjectionDigest("sec_bulk_submissions")
    for digest, order in ((forward, (0, 1)), (backward, (1, 0))):
        for ordinal in order:
            digest.begin_member(ordinal, f"member-{ordinal}", f"digest-{ordinal}")
            digest.end_member()
    assert forward.hexdigest() != backward.hexdigest()


# ==========================================================================
# The contract stays opt-in
# ==========================================================================
def test_the_full_contract_is_the_default() -> None:
    """No existing caller changes behaviour, which is how D112 §3's scope limit is enforced."""
    assert not FULL_EVIDENCE
    assert COMPACT_EVIDENCE
    connection = sqlite3.connect(":memory:")
    try:
        catalog = CensusCatalog(_StubWriter(connection))  # type: ignore[arg-type]
        assert catalog.compact_evidence == FULL_EVIDENCE
    finally:
        connection.close()


def test_the_compact_payload_helper_never_drops_a_governed_value() -> None:
    payload = _filing(_ORDINARY)
    payload["cik"] = "0000000002"
    projected = compact_parsed_payload(payload)
    for field in GOVERNED_ACCESSION_FIELDS:
        if field in payload:
            assert projected[field] == payload[field]
    assert "size" not in projected


# ==========================================================================
# Non-vacuity: the equivalence must be breakable
# ==========================================================================
def test_omitting_the_exception_rows_breaks_the_equivalence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Restore the over-eager contract and require the proof to notice.

    Every equivalence assertion above passes on a contract that writes *everything*, so the
    interesting failure mode is the opposite one: a contract that omits a row it needed. This
    mutation makes the writer omit every accession observation -- including the malformed
    values, the second witnesses, and the conflicting alternatives D112 §4.D requires -- and
    the governed output must stop matching. If it still matched, the exception rules would be
    decoration and the tests around them would prove nothing.
    """
    reference = _run(tmp_path / "reference", compact=False)
    monkeypatch.setattr(
        "disclosure_drift.sec.census.materialized_fields",
        lambda payload, *, first_witness: (),
    )
    mutated = _run(tmp_path / "mutated", compact=True)
    differences = [
        table
        for table in ("census_accession_field_resolutions", "census_accession_registrants")
        if _rows(mutated, table) != _rows(reference, table)
    ]
    assert differences, "omitting exception evidence must change a governed result"


def test_a_lossy_reconstruction_breaks_the_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Drop one governed field from the reconstruction and require the resolver to notice.

    The reader half of the contract carries as much weight as the writer half: if a
    reconstruction silently lost a value, the compact catalog would resolve fewer fields than
    the full one and no amount of writer-side care would show it.
    """
    reference = _run(tmp_path / "reference", compact=False)
    real = reconstructed_observations
    monkeypatch.setattr(
        "disclosure_drift.sec.census.reconstructed_observations",
        lambda row: ((field, value) for field, value in real(row) if field != "form"),
    )
    mutated = _run(tmp_path / "mutated", compact=True)
    assert _rows(mutated, "census_accession_field_resolutions") != _rows(
        reference, "census_accession_field_resolutions"
    )


def test_the_compared_tables_are_not_empty(both_paths: tuple[Path, Path]) -> None:
    """Guard against an equivalence proof that compares two empty catalogs."""
    full, _compact = both_paths
    with connect(full, writer=False) as connection:
        for table in _EQUAL_TABLES:
            if table in {
                "census_quarantined_records",
                "census_malformed_historical_references",
                "census_historical_references",
                "census_candidate_lineage_edges",
            }:
                continue
            count = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608
            assert count > 0, f"{table} is empty, so comparing it proves nothing"


# ==========================================================================
# D112 §§4.A, 4.E, 8 -- the run-local evidence sidecar
# ==========================================================================
def _record_evidence(root: Path, sidecar_path: Path | None) -> op.CompactSourceEvidence:
    """Traverse the frozen archive once, recording the manifest and completeness digest."""
    database, tree = _build_world(root)
    store = op.SnapshotStore(tree)
    with connect(database, writer=False) as connection:
        store.adopt(load_observations(connection))
        observation = op._observations_by_id(connection)[world._OBSERVATION]
    sidecar = None if sidecar_path is None else CompactEvidenceSidecar(sidecar_path)
    evidence = op.CompactSourceEvidence(
        source_observation_id=observation.observation_id,
        source_id=observation.source_id,
        artifact_sha256=str(observation.logical_sha256),
        artifact_byte_length=int(observation.content_size_bytes or 0),
        sidecar=sidecar,
    )
    for _outcome in op._stream_bulk_submissions(store, observation, evidence=evidence):
        pass
    evidence.finish()
    return evidence


def test_the_sidecar_records_a_manifest_row_for_every_member(tmp_path: Path) -> None:
    """§4.A: deterministic identity, payload length and digest, counts, and a disposition."""
    sidecar_path = tmp_path / COMPACT_EVIDENCE_SIDECAR_FILENAME
    evidence = _record_evidence(tmp_path / "world", sidecar_path)
    sidecar = CompactEvidenceSidecar(sidecar_path)
    try:
        members = sidecar.members(evidence.source_observation_id)
        assert len(members) == evidence.members == 2
        for ordinal, row in enumerate(members):
            assert row["member_ordinal"] == ordinal
            assert str(row["member_name"]).endswith(".json")
            assert int(row["payload_byte_length"]) > 0
            assert len(str(row["payload_sha256"])) == 64
            assert len(str(row["projection_digest"])) == 64
            assert row["disposition"] == "parsed"
        source = sidecar.source_evidence(evidence.source_observation_id)
        assert source is not None
        assert source["contract"] == COMPACT_EVIDENCE_CONTRACT
        assert source["schema_version"] == COMPACT_EVIDENCE_SCHEMA_VERSION
        assert int(source["records"]) == evidence.records
        # The whole point of the contract: most field observations are omitted, and the count
        # of what was omitted is itself durable rather than merely inferable.
        assert int(source["omitted_field_observations"]) > int(
            source["materialized_field_observations"]
        )
    finally:
        sidecar.close()


def test_the_sidecar_identity_is_reproducible_and_content_bound(tmp_path: Path) -> None:
    """§8: the sidecar's identity enters the freeze, so it must be deterministic and sensitive."""
    first = tmp_path / "one.sqlite3"
    second = tmp_path / "two.sqlite3"
    _record_evidence(tmp_path / "a", first)
    _record_evidence(tmp_path / "b", second)
    left, right = CompactEvidenceSidecar(first), CompactEvidenceSidecar(second)
    try:
        assert left.identity() == right.identity()
        right.record_member(
            "obs-extra",
            MemberManifestEntry(
                member_ordinal=0,
                member_name="extra.json",
                payload_byte_length=1,
                payload_sha256="0" * 64,
                parsed_registrants=0,
                parsed_accessions=0,
                parsed_other=0,
                quarantined=0,
                structural_failures=0,
                omitted_field_observations=0,
                materialized_field_observations=0,
                projection_digest="1" * 64,
                disposition="parsed",
            ),
        )
        assert left.identity() != right.identity()
    finally:
        left.close()
        right.close()


def test_the_recorder_changes_nothing_about_the_traversal(tmp_path: Path) -> None:
    """Recording evidence must not alter what the parse yields, or it is not evidence of it."""
    database, tree = _build_world(tmp_path / "world")
    store = op.SnapshotStore(tree)
    with connect(database, writer=False) as connection:
        store.adopt(load_observations(connection))
        observation = op._observations_by_id(connection)[world._OBSERVATION]
    plain = [
        [record.native_identity for record in outcome.records]
        for outcome, _ in op._stream_bulk_submissions(store, observation)
    ]
    evidence = op.CompactSourceEvidence(
        source_observation_id=observation.observation_id,
        source_id=observation.source_id,
        artifact_sha256=str(observation.logical_sha256),
        artifact_byte_length=int(observation.content_size_bytes or 0),
    )
    recorded = [
        [record.native_identity for record in outcome.records]
        for outcome, _ in op._stream_bulk_submissions(store, observation, evidence=evidence)
    ]
    assert recorded == plain
    assert evidence.digest.hexdigest()


def test_the_completeness_digest_survives_a_second_independent_run(tmp_path: Path) -> None:
    """§14: two runs over two separately written copies of the artifact agree exactly."""
    first = _record_evidence(tmp_path / "a", None)
    second = _record_evidence(tmp_path / "b", None)
    assert first.digest.hexdigest() == second.digest.hexdigest()
    assert first.omitted == second.omitted > 0
    assert first.materialized == second.materialized


# ==========================================================================
# The run-level duplicate flag: hoisted, and identical
# ==========================================================================
def test_the_duplicate_flag_is_unchanged_by_hoisting_the_identity_set(tmp_path: Path) -> None:
    """The merged path's duplicate verdict must not move when it stops being recomputed.

    ``_insert_record`` used to derive each record's run-level duplicate flag by scanning
    ``outcome.duplicate_identities`` -- a property of the whole source -- once per record. On
    one real median ``company.idx`` quarter that is 252,622 records against 62,266 duplicate
    identities, or 15.7 billion string comparisons for one of seventy quarters, and the source
    did not finish in twelve minutes. Membership in a set answers the identical question; this
    holds the two forms to the same answer on a world that actually contains a duplicate.
    """
    database, tree = world._world(tmp_path / "w", members=4, filings=3, duplicate=True)
    store = op.SnapshotStore(tree)
    with connect(database, writer=False) as connection:
        store.adopt(load_observations(connection))
        observation = op._observations_by_id(connection)[world._OBSERVATION]
    outcome, _references = op._parse_bulk_submissions(store, observation)
    assert outcome.duplicate_identities, "the fixture must contain a duplicate or it proves nothing"

    hoisted = frozenset(identity for identity, _ in outcome.duplicate_identities)
    for record in outcome.records:
        scanned = record.duplicate_indicator or any(
            identity == record.native_identity for identity, _ in outcome.duplicate_identities
        )
        assert (record.duplicate_indicator or record.native_identity in hoisted) == scanned
    assert any(record.native_identity in hoisted for record in outcome.records)
