"""Decision 131 Repairs A, B and C — bulk shard dispatch, parent binding, optional fields.

Three defects, repaired separately and proved separately.

**Repair A (accepted Decision 129 §5, D129-R3).** The bulk archive holds two legitimate JSON
member shapes: primary submissions documents named ``CIK##########.json``, and historical
overflow shards named ``CIK##########-submissions-NNN.json``. D128 routed all 5,337 shards
through ``parse_submissions_document``, whose contract is *one document describes one CIK*,
and they were refused — correctly. The defect was the dispatch, and it cost 3,037,614
accessions. A shard now reaches ``parse_historical_submissions`` under the registrant its
parent explicitly declared, and the dispatch is **order-independent**: the parent may sit
anywhere in the archive relative to its children (D129-R6).

**Repair B (accepted Decision 129 §6, D129-R4).** Every ``census_historical_references`` row
took one observation-wide registrant CIK, so 5,337 of 5,337 rows were wrong where 4,144
distinct registrants were represented. The compounding hazard was the reverse lookup's own
guard: it refuses zero candidates and refuses two, so one *consistently wrong* candidate
passed silently and was returned as authority.

**Repair C (accepted Decision 129 §8, D129-R7).** ``lei``, ``filings.recent.core_type`` and
``filings.recent.isXBRLNumeric`` are optional non-semantic SEC fields. Recognizing them stops
their mere presence being reported as schema drift; it makes nothing required and changes no
identity, cohort, or research definition.

Recognition is **non-blocking**, and the registries say so separately.
``ACCESSION_ARRAY_FIELDS`` means *this field's list shape is part of the parser contract*, and
a present non-list member of it quarantines the whole ``filings.recent`` block.
``KNOWN_OPTIONAL_RECENT_FIELDS`` means *this field is recognized and carries no such contract*.
Putting the two new names in the first registry -- which an earlier draft of this repair did --
would have made recognizing a non-semantic field newly capable of refusing every accession of a
registrant, which is worse than the drift report it replaced. The unknown-field walkers read
the union, ``RECOGNIZED_RECENT_FIELDS``; shape enforcement reads the array registry alone.

Everything here runs over synthetic archives and disposable catalogs beneath ``tmp_path``. No
test resolves, names, or infers the accepted private evidence root, none reads a real SEC
artifact, and none touches a real catalog.
"""

from __future__ import annotations

import dataclasses
import gc
import json
import sqlite3
import sys
import tracemalloc
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d110_bounded_parse_memory as world  # noqa: E402

from disclosure_drift.m3 import offline_parse as op  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.sec.parsers.base import RecordLocation  # noqa: E402
from disclosure_drift.sec.parsers.submissions import (  # noqa: E402
    ACCESSION_ARRAY_FIELDS,
    KNOWN_OPTIONAL_RECENT_FIELDS,
    RECOGNIZED_RECENT_FIELDS,
    HistoricalFileReference,
    parse_submissions_document,
)
from disclosure_drift.sec.snapshots import SnapshotStore  # noqa: E402
from disclosure_drift.storage.catalog import CatalogWriter  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402

_ARCHIVE_TIMESTAMP: tuple[int, int, int, int, int, int] = (2026, 1, 1, 0, 0, 0)


# ==========================================================================
# Fixture construction
# ==========================================================================
def _shard_name(cik: int, index: int = 1) -> str:
    return f"CIK{cik:010d}-submissions-{index:03d}.json"


def _primary(
    cik: int,
    *,
    accessions: int = 2,
    declares: tuple[str, ...] = (),
    extra: dict[str, Any] | None = None,
    extra_recent: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """One primary submissions document, named the way the real bulk archive names them."""
    padded = f"{cik:010d}"
    recent: dict[str, Any] = {
        "accessionNumber": [f"{padded}-24-{index:06d}" for index in range(accessions)],
        "filingDate": ["2024-02-01"] * accessions,
        "form": ["10-K"] * accessions,
    }
    recent.update(extra_recent or {})
    document: dict[str, Any] = {
        "cik": str(cik),
        "name": f"SYNTHETIC {cik}",
        "sic": "2834",
        "filings": {
            "recent": recent,
            "files": [
                {
                    "name": name,
                    "filingCount": 2,
                    "filingFrom": "2010-01-01",
                    "filingTo": "2010-12-31",
                }
                for name in declares
            ],
        },
    }
    document.update(extra or {})
    return f"CIK{padded}.json", document


def _shard(cik: int, index: int = 1, *, accessions: int = 3) -> tuple[str, dict[str, Any]]:
    """One historical overflow shard: parallel arrays and no registrant identity of its own."""
    padded = f"{cik:010d}"
    return _shard_name(cik, index), {
        "accessionNumber": [f"{padded}-10-{item:06d}" for item in range(accessions)],
        "filingDate": ["2010-03-01"] * accessions,
        "form": ["10-K"] * accessions,
    }


def _write_archive(path: Path, members: list[tuple[str, dict[str, Any]]]) -> bytes:
    """Write members in exactly the given order; archive order is the variable under test."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, document in members:
            info = zipfile.ZipInfo(name, date_time=_ARCHIVE_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, json.dumps(document, sort_keys=True))
    return path.read_bytes()


def _build(root: Path, members: list[tuple[str, dict[str, Any]]]) -> tuple[Path, DataTree]:
    tree = DataTree.from_root(root / "data")
    database = root / "catalog.sqlite3"
    raw = _write_archive(tree.data_root / world._ARCHIVE_RELATIVE, members)
    world._seed_catalog(database, tree, raw)
    return database, tree


def _stream(root: Path, members: list[tuple[str, dict[str, Any]]], **kwargs: Any) -> list[Any]:
    """Drive the production generator over one synthetic archive and collect what it yields."""
    database, tree = _build(root, members)
    observation = world._observation(tree, database)
    store = SnapshotStore(tree)
    store.adopt([observation])
    return list(op._stream_bulk_submissions(store, observation, **kwargs))


def _semantics(streamed: list[Any]) -> list[tuple[str, str, str]]:
    """The archive-order-independent content of a traversal.

    Member ordinals and the completeness digest are properties of the artifact's own byte
    order and are *supposed* to move when members are reordered. What may not move is the
    semantic content: which records exist, what they hash to, and which registrant each one
    is bound to.
    """
    rows: list[tuple[str, str, str]] = []
    for outcome, _references in streamed:
        for record in outcome.records:
            rows.append(
                (
                    record.native_identity,
                    record.record_sha256,
                    str(record.payload.get("cik", "")),
                )
            )
    return sorted(rows)


class _RecordingSidecar:
    """Captures the manifest entries ``CompactSourceEvidence`` writes, and nothing else."""

    def __init__(self) -> None:
        self.members: list[Any] = []
        self.sources: list[dict[str, Any]] = []

    def record_member(self, source_observation_id: str, entry: Any) -> None:
        self.members.append(entry)

    def record_source(self, **fields: Any) -> None:
        self.sources.append(fields)


# ==========================================================================
# 1-2. Semantic dispatch: each member shape reaches its own parser
# ==========================================================================
def test_a_primary_member_reaches_the_primary_submissions_parser(tmp_path: Path) -> None:
    streamed = _stream(tmp_path / "primary", [_primary(1)])

    assert len(streamed) == 1
    outcome, _references = streamed[0]
    assert outcome.parser_id == "submissions-json"
    assert [record.native_identity for record in outcome.records] == [
        "registrant:0000000001",
        "accession:0000000001-24-000000",
        "accession:0000000001-24-000001",
    ]


def test_a_historical_shard_reaches_the_historical_parser_and_never_the_primary_one(
    tmp_path: Path,
) -> None:
    """The D128 defect, stated as a test: a shard must not be handed to the primary parser.

    The primary parser is wrapped rather than asserted about after the fact, because the D128
    symptom was a *quarantine* — the shard reached the wrong parser and that parser refused it
    correctly. Watching what the parser was called with is the only way to tell "never
    dispatched there" from "dispatched there and rejected".
    """
    seen: list[str] = []

    def _watched(payload: Any, location: RecordLocation) -> Any:
        seen.append(str(location.member_name))
        return parse_submissions_document(payload, location)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(op, "parse_submissions_document", _watched)
        streamed = _stream(
            tmp_path / "shard",
            [_primary(1, declares=(_shard_name(1),)), _shard(1)],
        )

    assert seen == ["CIK0000000001.json"]
    assert len(streamed) == 2
    historical = streamed[1][0]
    assert historical.parser_id == "submissions-historical"
    assert not historical.quarantined
    assert [record.native_identity for record in historical.records] == [
        "accession:0000000001-10-000000",
        "accession:0000000001-10-000001",
        "accession:0000000001-10-000002",
    ]
    assert {record.payload["cik"] for record in historical.records} == {"0000000001"}


# ==========================================================================
# 3-5. Archive order does not decide correctness (D129-R6)
# ==========================================================================
def test_a_parent_before_its_shard_produces_the_expected_historical_rows(
    tmp_path: Path,
) -> None:
    streamed = _stream(
        tmp_path / "parent-first",
        [_primary(1, declares=(_shard_name(1),)), _shard(1)],
    )

    identities = [record.native_identity for outcome, _ in streamed for record in outcome.records]
    assert "accession:0000000001-10-000000" in identities


def test_a_shard_before_its_parent_produces_the_expected_historical_rows(
    tmp_path: Path,
) -> None:
    """The case D128's implementation could not have handled at all.

    A forward traversal that resolves a shard the moment it meets one is correct only when the
    declaring parent has already gone past. Deferring every shard to the end of the traversal
    is what removes that dependency.
    """
    streamed = _stream(
        tmp_path / "shard-first",
        [_shard(1), _primary(1, declares=(_shard_name(1),))],
    )

    identities = [record.native_identity for outcome, _ in streamed for record in outcome.records]
    assert "accession:0000000001-10-000000" in identities


def test_the_two_archive_orders_produce_identical_semantic_output(tmp_path: Path) -> None:
    """Order invariance stated over the whole semantic content, not one sampled row."""
    parent_first = _stream(
        tmp_path / "order-a",
        [
            _primary(1, declares=(_shard_name(1),)),
            _shard(1),
            _primary(2, declares=(_shard_name(2),)),
            _shard(2),
        ],
    )
    shard_first = _stream(
        tmp_path / "order-b",
        [
            _shard(2),
            _shard(1),
            _primary(2, declares=(_shard_name(2),)),
            _primary(1, declares=(_shard_name(1),)),
        ],
    )

    assert _semantics(parent_first) == _semantics(shard_first)
    historical = [
        (record.native_identity, record.payload["cik"])
        for outcome, _ in parent_first
        for record in outcome.records
        if outcome.parser_id == "submissions-historical"
    ]
    assert sorted(historical) == [
        ("accession:0000000001-10-000000", "0000000001"),
        ("accession:0000000001-10-000001", "0000000001"),
        ("accession:0000000001-10-000002", "0000000001"),
        ("accession:0000000002-10-000000", "0000000002"),
        ("accession:0000000002-10-000001", "0000000002"),
        ("accession:0000000002-10-000002", "0000000002"),
    ]


# ==========================================================================
# 6-8. Fail-closed binding (D129-R5)
# ==========================================================================
def test_a_shard_no_document_declares_fails_closed(tmp_path: Path) -> None:
    """Its own filename encodes a CIK. That is corroboration, and it rescues nothing."""
    with pytest.raises(op.OfflineParseError) as raised:
        _stream(tmp_path / "undeclared", [_primary(1), _shard(1)])

    assert "no primary submissions document declares it" in str(raised.value)
    assert "corroboration and never a binding" in str(raised.value)


def test_a_shard_two_registrants_declare_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(op.OfflineParseError) as raised:
        _stream(
            tmp_path / "ambiguous",
            [
                _primary(1, declares=(_shard_name(1),)),
                _primary(2, declares=(_shard_name(1),)),
                _shard(1),
            ],
        )

    assert "declared by 2 distinct registrants" in str(raised.value)


def test_a_filename_cik_contradicting_the_explicit_parent_fails_closed(
    tmp_path: Path,
) -> None:
    """Registrant 2 claims registrant 1's overflow file. Neither claim wins."""
    with pytest.raises(op.OfflineParseError) as raised:
        _stream(
            tmp_path / "contradiction",
            [_primary(2, declares=(_shard_name(1),)), _shard(1)],
        )

    assert "canonical filename encodes" in str(raised.value)


def test_the_same_parent_declaring_one_shard_twice_is_not_a_contradiction(
    tmp_path: Path,
) -> None:
    """Duplicate agreeing declarations are duplicates, not conflicts, and must not refuse."""
    streamed = _stream(
        tmp_path / "duplicate-declaration",
        [_primary(1, declares=(_shard_name(1), _shard_name(1))), _shard(1)],
    )

    historical = [
        outcome for outcome, _ in streamed if outcome.parser_id == "submissions-historical"
    ]
    assert len(historical) == 1
    assert len(historical[0].records) == 3


# ==========================================================================
# 9. One member, one final governed member record
# ==========================================================================
def test_a_deferred_shard_produces_exactly_one_member_evidence_row(tmp_path: Path) -> None:
    """And it is written only once the real historical parse has happened.

    A member recorded as ``parsed`` during the primary traversal — before its parser had run —
    would be a false witness in the D112 §4.A manifest. The deferred shard is absorbed in the
    deferred phase, so its single manifest entry carries the historical parse's real counts.
    """
    database, tree = _build(
        tmp_path / "evidence",
        [_primary(1, declares=(_shard_name(1),)), _shard(1), _primary(2)],
    )
    observation = world._observation(tree, database)
    store = SnapshotStore(tree)
    store.adopt([observation])
    sidecar = _RecordingSidecar()
    evidence = op.CompactSourceEvidence(
        source_observation_id=observation.observation_id,
        source_id=observation.source_id,
        artifact_sha256=observation.logical_sha256 or "",
        artifact_byte_length=observation.content_size_bytes or 0,
        sidecar=sidecar,
    )

    list(op._stream_bulk_submissions(store, observation, evidence=evidence))

    names = [entry.member_name for entry in sidecar.members]
    assert sorted(names) == sorted(["CIK0000000001.json", "CIK0000000002.json", _shard_name(1)])
    assert len(names) == len(set(names)) == 3
    assert len({entry.member_ordinal for entry in sidecar.members}) == 3
    shard_entry = next(entry for entry in sidecar.members if entry.member_name == _shard_name(1))
    assert shard_entry.disposition == "parsed"
    assert shard_entry.parsed_accessions == 3
    assert shard_entry.parsed_registrants == 0
    # The shard is absorbed last, after every primary, because that is when its parse happens.
    assert shard_entry.member_ordinal == max(entry.member_ordinal for entry in sidecar.members)


# ==========================================================================
# The diagnostic prefix keeps its bound, and claims nothing about shards
# ==========================================================================
def test_a_diagnostic_prefix_counts_a_deferred_shard_and_never_parses_it(
    tmp_path: Path,
) -> None:
    """A bounded prefix stops mid-archive, so its parent map is incomplete by construction.

    Resolving a shard against a half-built map would refuse a perfectly well-formed archive,
    so the deferred phase does not run under a cap at all. The shard still counts against the
    bound, because ``--member-limit`` bounds the members the traversal *handles*; it is simply
    never parsed. A prefix finalizes nothing and can never report success, so it makes no
    claim about the shard population either way.
    """
    database, tree = _build(
        tmp_path / "prefix",
        [_primary(1, declares=(_shard_name(1),)), _shard(1), _primary(2)],
    )
    observation = world._observation(tree, database)
    store = SnapshotStore(tree)
    store.adopt([observation])

    yielded = []
    with pytest.raises(op._DiagnosticPrefixLimit) as stopped:
        for item in op._stream_bulk_submissions(store, observation, max_members=2):
            yielded.append(item)

    assert stopped.value.members == 2
    # Two members handled: the primary (yielded) and the shard (deferred, counted, unparsed).
    assert len(yielded) == 1
    assert yielded[0][0].parser_id == "submissions-json"


def test_a_prefix_that_reaches_the_whole_archive_still_parses_no_shard(
    tmp_path: Path,
) -> None:
    """Even a cap as large as the archive stops before the deferred phase.

    The consumer's normal exhaustion path finalizes a parser run, and a bounded prefix must
    never reach it — so the cap always ends the traversal, and the deferred phase always sits
    on the far side of that end.
    """
    database, tree = _build(
        tmp_path / "prefix-whole",
        [_primary(1, declares=(_shard_name(1),)), _shard(1)],
    )
    observation = world._observation(tree, database)
    store = SnapshotStore(tree)
    store.adopt([observation])

    yielded = []
    with pytest.raises(op._DiagnosticPrefixLimit) as stopped:
        for item in op._stream_bulk_submissions(store, observation, max_members=99):
            yielded.append(item)

    assert stopped.value.members == 2
    assert [outcome.parser_id for outcome, _ in yielded] == ["submissions-json"]


# ==========================================================================
# 10-11. Per-reference parent binding survives persistence (D129-R4)
# ==========================================================================
def _historical_reference_rows(database: Path) -> list[tuple[str, str]]:
    with connect(database, writer=False) as connection:
        return sorted(
            (str(row["historical_file"]), str(row["registrant_cik_padded"]))
            for row in connection.execute(
                "SELECT historical_file, registrant_cik_padded FROM census_historical_references"
            )
        )


def test_two_parents_in_one_observation_persist_two_distinct_correct_ciks(
    tmp_path: Path,
) -> None:
    """The exact shape D128 got wrong: one bulk observation, many registrants.

    Both references belong to the same ``source_observation_id``. Under the old rule both took
    the CIK of whichever registrant record happened to sort first, so one of them was always
    wrong and neither was checkable.
    """
    root = tmp_path / "binding"
    database, tree = _build(
        root,
        [
            _primary(1, declares=(_shard_name(1),)),
            _shard(1),
            _primary(2, declares=(_shard_name(2),)),
            _shard(2),
        ],
    )
    locks = root / "locks"
    locks.mkdir()
    with CatalogWriter(database, locks) as writer:
        op.run_offline_metadata_parse(writer=writer, tree=tree)

    assert _historical_reference_rows(database) == [
        (_shard_name(1), "0000000001"),
        (_shard_name(2), "0000000002"),
    ]


def test_no_observation_wide_cik_leaks_onto_a_later_registrants_reference(
    tmp_path: Path,
) -> None:
    """A registrant that declares nothing must not lend its CIK to one that does.

    Registrant 1 sorts first and owns no overflow file at all. Under the observation-wide rule
    it would still have supplied the CIK for registrant 3's reference.
    """
    root = tmp_path / "leakage"
    database, tree = _build(
        root,
        [
            _primary(1),
            _primary(3, declares=(_shard_name(3),)),
            _shard(3),
        ],
    )
    locks = root / "locks"
    locks.mkdir()
    with CatalogWriter(database, locks) as writer:
        op.run_offline_metadata_parse(writer=writer, tree=tree)

    assert _historical_reference_rows(database) == [(_shard_name(3), "0000000003")]


def test_a_malformed_reference_is_preserved_under_its_own_declaring_registrant(
    tmp_path: Path,
) -> None:
    root = tmp_path / "malformed"
    database, tree = _build(
        root,
        [_primary(1), _primary(2, declares=("not-a-historical-name.json",))],
    )
    locks = root / "locks"
    locks.mkdir()
    with CatalogWriter(database, locks) as writer:
        op.run_offline_metadata_parse(writer=writer, tree=tree)

    with connect(database, writer=False) as connection:
        rows = [
            (str(row["observed_name"]), str(row["registrant_cik_padded"]))
            for row in connection.execute(
                "SELECT observed_name, registrant_cik_padded "
                "FROM census_malformed_historical_references"
            )
        ]
    assert rows == [("not-a-historical-name.json", "0000000002")]


# ==========================================================================
# 12. The reverse lookup no longer trusts a uniquely wrong answer (D129-R4)
# ==========================================================================
def _reference_catalog(rows: list[tuple[str, str]]) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE census_historical_references ("
        "source_observation_id TEXT, registrant_cik_padded TEXT, historical_file TEXT)"
    )
    connection.executemany(
        "INSERT INTO census_historical_references VALUES ('obs', ?, ?)",
        [(cik, name) for cik, name in rows],
    )
    return connection


def _historical_observation(name: str) -> Any:
    return SimpleNamespace(requested_url=f"https://example.invalid/submissions/{name}")


def test_the_reverse_lookup_accepts_a_persisted_cik_its_filename_corroborates() -> None:
    connection = _reference_catalog([("0000000001", _shard_name(1))])

    assert (
        op._historical_registrant_cik(connection, _historical_observation(_shard_name(1)))
        == "0000000001"
    )


def test_the_reverse_lookup_rejects_a_uniformly_wrong_persisted_cik() -> None:
    """Uniqueness was the only guard, and a uniformly wrong value satisfies it perfectly.

    This is the D128 state reproduced exactly: every row carries one registrant, so the
    ``len(rows) != 1`` check passes for every shard and returns the wrong registrant for all
    but one of them.
    """
    connection = _reference_catalog(
        [("0000000001", _shard_name(1)), ("0000000001", _shard_name(2))]
    )

    with pytest.raises(op.OfflineParseError) as raised:
        op._historical_registrant_cik(connection, _historical_observation(_shard_name(2)))

    assert "canonical filename encodes 0000000002" in str(raised.value)
    assert "refused rather than trusted for being unique" in str(raised.value)


def test_the_reverse_lookup_still_fails_closed_on_zero_and_on_two_candidates() -> None:
    empty = _reference_catalog([])
    with pytest.raises(op.OfflineParseError) as absent:
        op._historical_registrant_cik(empty, _historical_observation(_shard_name(1)))
    assert "resolves to 0 accepted registrant references" in str(absent.value)

    ambiguous = _reference_catalog([("0000000001", _shard_name(1)), ("0000000002", _shard_name(1))])
    with pytest.raises(op.OfflineParseError) as two:
        op._historical_registrant_cik(ambiguous, _historical_observation(_shard_name(1)))
    assert "resolves to 2 accepted registrant references" in str(two.value)


# ==========================================================================
# 13-16. Recognized optional fields (D129-R7)
# ==========================================================================
def _drift(document: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The registrant record's unknown-field paths and reason codes for one document."""
    outcome, _references = parse_submissions_document(
        document, RecordLocation("obs", "sec_bulk_submissions", member_name="m.json")
    )
    registrant = outcome.records[0]
    return registrant.unknown_fields, registrant.reason_codes


def test_lei_is_a_recognized_optional_top_level_field() -> None:
    _name, document = _primary(1, extra={"lei": "5493001KJTIIGC8Y1R12"})

    unknown, reasons = _drift(document)

    assert "lei" not in unknown
    assert unknown == ()
    assert reasons == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("core_type", ["10-K", "10-K"], id="core_type-list"),
        pytest.param("core_type", "10-K", id="core_type-scalar"),
        pytest.param("isXBRLNumeric", [1, 0], id="isXBRLNumeric-list"),
        pytest.param("isXBRLNumeric", 1, id="isXBRLNumeric-scalar"),
    ],
)
def test_a_recognized_recent_field_raises_no_drift_in_either_shape(
    field: str, value: object
) -> None:
    """Recognition is about the *name*, and it is deliberately shape-blind.

    Both shapes are covered together because the correction's whole content is that these two
    questions are separate: a list value must not be reported as an unknown field, and a scalar
    value must not become a blocking event merely because the name is now recognized.
    """
    _name, document = _primary(1, accessions=2, extra_recent={field: value})

    unknown, reasons = _drift(document)

    assert unknown == ()
    assert reasons == ()


def test_all_three_recognized_fields_together_raise_no_schema_drift() -> None:
    _name, document = _primary(
        1,
        extra={"lei": "5493001KJTIIGC8Y1R12"},
        extra_recent={"core_type": ["10-K", "10-K"], "isXBRLNumeric": [1, 0]},
    )

    unknown, reasons = _drift(document)

    assert unknown == ()
    assert "PARSER_SCHEMA_DRIFT_OBSERVED" not in reasons


def test_an_unregistered_field_is_still_reported_as_drift() -> None:
    """Recognition is not a general amnesty: a genuinely new field still surfaces."""
    _name, document = _primary(1, extra={"someBrandNewField": "x"})

    unknown, reasons = _drift(document)

    assert unknown == ("someBrandNewField",)
    assert "PARSER_SCHEMA_DRIFT_OBSERVED" in reasons


def test_recognition_does_not_make_the_new_fields_required() -> None:
    """A document without any of the three parses exactly as it did before."""
    _name, document = _primary(1)

    outcome, _references = parse_submissions_document(
        document, RecordLocation("obs", "sec_bulk_submissions", member_name="m.json")
    )

    assert not outcome.required_field_failures
    assert not outcome.quarantined
    assert len(outcome.records) == 3


def test_recognition_does_not_change_required_field_semantics() -> None:
    """The required accession columns are still required, and still block when absent.

    Stated on a document that also carries all three newly recognized fields, so the claim is
    specifically that recognizing them bought no leniency anywhere else: the missing ``form``
    column still quarantines the whole ``filings.recent`` block, still leaves the region's
    structural verdict ``malformed``, and still yields no accession record at all.
    """
    _name, document = _primary(
        1,
        extra={"lei": "5493001KJTIIGC8Y1R12"},
        extra_recent={"core_type": ["10-K", "10-K"], "isXBRLNumeric": [1, 0]},
    )
    del document["filings"]["recent"]["form"]

    outcome, _references = parse_submissions_document(
        document, RecordLocation("obs", "sec_bulk_submissions", member_name="m.json")
    )

    assert [record.native_identity for record in outcome.records] == ["registrant:0000000001"]
    assert outcome.quarantined
    assert "form" in outcome.quarantined[0].detail
    assert outcome.quarantined[0].reason_codes == ("SEC_SCHEMA_REQUIRED_FIELD_MISSING",)
    recent = next(item for item in outcome.structural if item.region == "filings.recent")
    assert recent.state == "malformed"


@pytest.mark.parametrize("field", ["core_type", "isXBRLNumeric"])
def test_a_recognized_field_that_is_not_a_list_blocks_nothing(field: str) -> None:
    """Recognition must not invent a refusal that did not exist before it.

    An earlier draft of this repair registered ``core_type`` and ``isXBRLNumeric`` in
    :data:`ACCESSION_ARRAY_FIELDS`, which is the registry of fields whose *list shape is part
    of the parser contract*. That made a present scalar a blocking ``malformed_nested_array``
    event, and a blocking event on ``filings.recent`` quarantines the **entire** recent block
    -- every accession of that registrant. Recognizing a non-semantic field would then have
    been strictly worse than the drift report it was meant to silence.

    A scalar in one of these keys is therefore treated exactly as any other non-list key in
    ``filings.recent`` already is: retained, surfaced as a normalization warning, non-blocking,
    and with every accession record still produced.
    """
    _name, document = _primary(1, accessions=2, extra_recent={field: "10-K"})

    outcome, _references = parse_submissions_document(
        document, RecordLocation("obs", "sec_bulk_submissions", member_name="m.json")
    )

    assert outcome.quarantined == ()
    assert [record.native_identity for record in outcome.records] == [
        "registrant:0000000001",
        "accession:0000000001-24-000000",
        "accession:0000000001-24-000001",
    ]
    recent = next(item for item in outcome.structural if item.region == "filings.recent")
    assert recent.state == "valid_present"
    warnings = outcome.records[1].normalization_warnings
    assert any(field in warning for warning in warnings)


@pytest.mark.parametrize("field", ["accessionNumber", "isXBRL", "primaryDocument"])
def test_a_contracted_array_field_that_is_not_a_list_is_still_blocking(field: str) -> None:
    """The pre-existing shape contract is untouched by the separation.

    ``ACCESSION_ARRAY_FIELDS`` keeps meaning exactly what it meant: a member of it that is
    present but is not a list is blocking drift. Proved across a required column, an optional
    flag column, and an optional text column, so the claim is about the registry rather than
    about one field that happens to be required anyway.
    """
    _name, document = _primary(1, extra_recent={field: "not-a-list"})

    outcome, _references = parse_submissions_document(
        document, RecordLocation("obs", "sec_bulk_submissions", member_name="m.json")
    )

    assert outcome.quarantined
    assert field in outcome.quarantined[0].detail
    assert "expected a list" in outcome.quarantined[0].detail
    recent = next(item for item in outcome.structural if item.region == "filings.recent")
    assert recent.state == "malformed"


def test_the_two_recent_registries_are_disjoint_and_their_union_is_recognized() -> None:
    """The separation stated as a property of the registries themselves.

    ``ACCESSION_ARRAY_FIELDS`` answers *is this field's list shape contracted?*;
    ``KNOWN_OPTIONAL_RECENT_FIELDS`` answers *is this field recognized without one?*; and the
    unknown-field walkers read the union. A field in both would make the two questions collide,
    which is the shape the correction removed.
    """
    assert set(ACCESSION_ARRAY_FIELDS) & set(KNOWN_OPTIONAL_RECENT_FIELDS) == set()
    assert set(RECOGNIZED_RECENT_FIELDS) == set(ACCESSION_ARRAY_FIELDS) | set(
        KNOWN_OPTIONAL_RECENT_FIELDS
    )
    assert set(KNOWN_OPTIONAL_RECENT_FIELDS) == {"core_type", "isXBRLNumeric"}


def test_the_historical_parser_shares_the_recognized_recent_arrays() -> None:
    """A shard carries the same columns, so recognition must reach it too."""
    from disclosure_drift.sec.parsers.historical import parse_historical_submissions

    _name, document = _shard(1, accessions=2)
    document["core_type"] = ["10-K", "10-K"]
    document["isXBRLNumeric"] = [1, 0]

    outcome = parse_historical_submissions(
        document,
        RecordLocation("obs", "sec_bulk_submissions", member_name=_shard_name(1)),
        registrant_cik="0000000001",
    )

    assert outcome.unknown_fields == ()
    assert len(outcome.records) == 2


# ==========================================================================
# Bounded residency over an archive that actually carries shards
# ==========================================================================
# The accepted Decision 110 §8 boundedness proof runs over the D110 fixture, and that fixture
# carries **zero** physical shard members: its documents *declare* overflow files the archive
# does not hold, so the deferred phase there is empty and D131's own residency is untested by
# it. These tests supply the missing case — real shard members, explicitly declared, spread
# through the traversal rather than clustered at its start.
#
# The threshold is the D110-style one (a traversal's second half sits no higher than its
# first), deliberately stated as a ratio. No absolute byte figure from any particular machine
# is encoded as a contract.
_PRIMARY_PARSER: str = "submissions-json"
_SHARD_PARSER: str = "submissions-historical"


def _residency_members(
    *, primaries: int, every: int, shard_accessions: int
) -> list[tuple[str, dict[str, Any]]]:
    """Primary documents with a real, explicitly declared shard every ``every`` members.

    Shards are spread across the whole traversal on purpose. Clustering them at the start
    would put every unit of deferred growth in the first half of the walk and make a
    second-half-versus-first-half comparison trivially satisfiable.
    """
    members: list[tuple[str, dict[str, Any]]] = []
    for index in range(primaries):
        cik = index + 1
        bears_shard = index % every == 0
        members.append(
            _primary(cik, accessions=2, declares=(_shard_name(cik),) if bears_shard else ())
        )
        if bears_shard:
            members.append(_shard(cik, accessions=shard_accessions))
    return members


def _shard_payload_bytes(members: list[tuple[str, dict[str, Any]]]) -> int:
    """Total encoded size of the shard members alone, as the archive stores them."""
    return sum(
        len(json.dumps(document, sort_keys=True).encode("utf-8"))
        for name, document in members
        if _shard_name(int(name[3:13])) == name
    )


def _walk_live_bytes(
    root: Path, members: list[tuple[str, dict[str, Any]]]
) -> tuple[list[int], int]:
    """Live traced memory at every *primary* boundary, and how many shards were then parsed.

    Live rather than peak, for the reason accepted Decision 110 §8's own boundary test gives:
    peak is monotonic by definition, so an assertion against it could not fail and would prove
    nothing. Only the primary phase is sampled — the deferred phase is a separate claim — but
    the whole stream is consumed, so the returned shard count is evidence that the fixture is
    genuinely shard-bearing rather than a repeat of the D110 world.
    """
    database, tree = _build(root, members)
    observation = world._observation(tree, database)
    store = SnapshotStore(tree)
    store.adopt([observation])

    live: list[int] = []
    shards = 0
    tracemalloc.start()
    try:
        for outcome, references in op._stream_bulk_submissions(store, observation):
            parser_id = outcome.parser_id
            del outcome, references
            if parser_id == _SHARD_PARSER:
                shards += 1
                continue
            gc.collect()
            live.append(tracemalloc.get_traced_memory()[0])
    finally:
        tracemalloc.stop()
    return live, shards


def test_a_shard_bearing_traversal_does_not_grow_across_primary_boundaries(
    tmp_path: Path,
) -> None:
    """Per-primary state stays bounded while shards are being deferred all around it."""
    members = _residency_members(primaries=60, every=3, shard_accessions=40)

    live, shards = _walk_live_bytes(tmp_path / "resident", members)

    assert len(live) == 60
    assert shards == 20
    half = len(live) // 2
    first = sum(live[:half]) / half
    second = sum(live[half:]) / (len(live) - half)
    assert second <= first * 1.10, {
        "first_half_mean": first,
        "second_half_mean": second,
        "ratio": second / first,
    }


def test_no_shard_payload_survives_the_primary_traversal(tmp_path: Path) -> None:
    """Deferred state is payload-independent: only names and ordinals are kept.

    Two archives with the **same** primary population and the **same** shard population differ
    only in how large each shard is. If a shard's bytes were retained by the traversal that met
    it, the live memory at the end of the primary phase would differ by the whole payload
    difference. It is required instead to differ by a small fraction of it — a ratio against
    the fixture's own sizes rather than a byte figure measured on one machine.
    """
    small = _residency_members(primaries=30, every=3, shard_accessions=2)
    large = _residency_members(primaries=30, every=3, shard_accessions=900)
    payload_delta = _shard_payload_bytes(large) - _shard_payload_bytes(small)
    assert payload_delta > 300_000, {"payload_delta": payload_delta}

    small_live, small_shards = _walk_live_bytes(tmp_path / "small", small)
    large_live, large_shards = _walk_live_bytes(tmp_path / "large", large)

    assert small_shards == large_shards == 10
    live_delta = large_live[-1] - small_live[-1]
    assert live_delta <= payload_delta * 0.05, {
        "payload_delta_bytes": payload_delta,
        "live_delta_bytes": live_delta,
        "fraction_of_payload": live_delta / payload_delta,
    }


def test_the_deferred_record_has_nowhere_to_put_a_payload() -> None:
    """Boundedness stated structurally, not only measured.

    A measurement can only show that today's implementation does not retain payloads. The
    record type is what makes retaining one impossible without a visible change: it is frozen,
    it uses ``slots``, and its two fields are a name and an ordinal.
    """
    names = [field.name for field in dataclasses.fields(op._DeferredHistoricalShard)]

    assert names == ["member_ordinal", "member_name"]
    record = op._DeferredHistoricalShard(member_ordinal=7, member_name=_shard_name(1))
    assert record.__slots__ == ("member_ordinal", "member_name")
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.member_name = "other.json"  # type: ignore[misc]


def test_the_parent_map_is_bounded_by_the_shard_population(tmp_path: Path) -> None:
    """Declarations naming files the archive does not hold are never retained.

    This is what keeps the second piece of deferred state bounded by *shards* rather than by
    *members*: 200 documents each declaring an overflow file grow the map by the one
    declaration that names a member the archive actually carries, not by 200.
    """
    declared: dict[str, set[str]] = {}
    present = _shard_name(1)
    references = tuple(
        HistoricalFileReference(
            name=_shard_name(cik),
            filing_count=1,
            filing_from="2010-01-01",
            filing_to="2010-12-31",
            location=RecordLocation("obs", "sec_bulk_submissions", member_name="m.json"),
            registrant_cik_padded=f"{cik:010d}",
        )
        for cik in range(1, 201)
    )

    op._declare_shard_parents(declared, references, frozenset({present}))

    assert set(declared) == {present}
    assert declared[present] == {"0000000001"}


# ==========================================================================
# The parser version the correction moves: submissions-json/1.2
# ==========================================================================
# Repair C changed what ``parse_submissions_document`` recognizes in ``filings.recent``, so the
# version stamped on its provenance must say so. There is exactly one declaration — the parser
# module's own ``PARSER_VERSION`` — and every other surface derives from it; these tests walk
# that chain end to end rather than re-pinning the string in several places.
#
# ``submissions-json/1.1`` is now **historical**: the operational catalog's existing rows carry
# it and are not rewritten, and a future conditional reuse of a 1.1 artifact must refuse
# compatibility rather than reuse it under a parser that no longer produced it. Migration
# ``0016`` is not implied — nothing about the persisted schema moves.
def test_the_implementation_declares_one_two_and_the_table_derives_it() -> None:
    from disclosure_drift.sec.parsers.submissions import PARSER_ID, PARSER_VERSION
    from disclosure_drift.sec.parsers.versions import PARSER_VERSIONS, parser_version_for

    assert PARSER_VERSION == "submissions-json/1.2"
    assert PARSER_VERSIONS[PARSER_ID] == "submissions-json/1.2"
    assert parser_version_for(PARSER_ID) == "submissions-json/1.2"


def test_the_live_source_registry_definition_agrees_with_one_two() -> None:
    """The registry derives the version; a stored second copy is what allows drift."""
    from disclosure_drift.sec.source_registry import SOURCES

    for source_id in ("sec_bulk_submissions", "sec_submissions_entity"):
        assert SOURCES[source_id].parser_version == "submissions-json/1.2"


def test_parser_output_provenance_carries_one_two() -> None:
    """The outcome and every record it produces are stamped with the running implementation."""
    _name, document = _primary(1, accessions=2)

    outcome, _references = parse_submissions_document(
        document, RecordLocation("obs", "sec_bulk_submissions", member_name="m.json")
    )

    assert outcome.parser_version == "submissions-json/1.2"
    assert {record.parser_version for record in outcome.records} == {"submissions-json/1.2"}


def test_a_disposable_working_catalog_persists_one_two(tmp_path: Path) -> None:
    """The value that reaches ``census_parser_runs.parser_version`` on a real run.

    Run over a synthetic archive beneath ``tmp_path`` against a create-once disposable catalog.
    No accepted evidence root is resolved, named, or inferred, and the operational catalog is
    not opened: this proves the version the *code path* writes, not what any governed catalog
    already holds.
    """
    database, tree = _build(
        tmp_path / "versioned", [_primary(1, declares=(_shard_name(1),)), _shard(1)]
    )

    report = world._run_streamed(database, tree, tmp_path / "locks")

    assert report.is_complete
    with connect(database, writer=False) as connection:
        runs = [
            (str(row["parser_id"]), str(row["parser_version"]), str(row["outcome"]))
            for row in connection.execute(
                "SELECT parser_id, parser_version, outcome FROM census_parser_runs"
            )
        ]
    assert runs == [("submissions-json", "submissions-json/1.2", "completed")]


def test_the_version_move_changes_no_e0_authority_or_state() -> None:
    """A parser version is provenance, never authority.

    Stated here because the two are easy to conflate: moving the version is exactly the kind of
    change that must *not* acquire, transition, or enable anything. All three E0 activation
    constants stay ``None``, so no execute mode is reachable and no catalog transition is armed.
    """
    from disclosure_drift.m3 import e0

    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is None
    assert e0.M3_3_E0_EXECUTION_AUTHORITY is None
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None


def test_a_one_one_artifact_is_no_longer_compatible_for_reuse() -> None:
    """1.1 is historical, so an artifact recorded under it must be reparsed, not reused."""
    from disclosure_drift.sec.parsers.versions import (
        ParserVersionError,
        require_parser_version,
        versions_agree,
    )

    assert versions_agree("submissions-json", "submissions-json/1.1") is False
    with pytest.raises(ParserVersionError, match="submissions-json/1.1"):
        require_parser_version(
            "submissions-json", "submissions-json/1.1", context="conditional reuse"
        )


# ==========================================================================
# The deferred twin defect: CensusOrchestrator._parse_bulk stays network-gated
# ==========================================================================
def test_the_orchestrator_bulk_parse_stays_unreachable_without_network(
    config_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same shard-dispatch defect still lives in ``CensusOrchestrator._parse_bulk``.

    ``_parse_bulk`` routes **every** ``.json`` member — historical shards included — through
    ``parse_submissions_document``, which is precisely what D128 did and what Repair A corrected
    in the offline path. It is deliberately **not** repaired here: the only way to reach it is
    ``CensusOrchestrator.run``, whose first two statements demand a SEC user agent and then call
    ``require_network()``. The corrected offline canary does not use it and E0 does not use it.

    **PRE-NETWORK BLOCKER.** No future network or live-retrieval authorization may reach
    ``CensusOrchestrator._parse_bulk`` until historical shard dispatch is repaired there. This
    test is the standing statement of the gate that makes the deferral safe: if the network gate
    ever stops guarding that path, this fails and the deferral has to be revisited.
    """
    import inspect

    from disclosure_drift.config import SEC_USER_AGENT_ENV, load_config
    from disclosure_drift.errors import NetworkDisabledError
    from disclosure_drift.sec.census_orchestrator import CensusOrchestrator

    source = inspect.getsource(CensusOrchestrator._parse_bulk)
    assert "parse_submissions_document" in source
    assert "parse_historical_submissions" not in source

    # A valid contact identity is supplied so the refusal reached is the *network* gate rather
    # than the user-agent guard that precedes it. Proving the wrong refusal would leave the
    # blocker unproved.
    monkeypatch.setenv(
        SEC_USER_AGENT_ENV, "Financial Disclosure Drift research@your-institution.edu"
    )
    config = load_config(config_file)
    assert config.network.enabled is False
    with pytest.raises(NetworkDisabledError):
        CensusOrchestrator(config).run()


def test_the_deferred_reopen_goes_through_the_public_archive_reader() -> None:
    """The reopen must be ``sec.archive``'s own public reader, not a private reach-in.

    Stated structurally because a local reimplementation would be *behaviourally identical
    today* and would only diverge later — which is exactly the failure mode a second copy of
    "how large may a member be" and "is this a regular file" produces. One implementation,
    reached through one public surface, is the property under test.
    """
    import inspect

    module_source = inspect.getsource(op)
    reopen_source = inspect.getsource(op._stream_deferred_historical_shards)

    assert "iter_named_members(" in reopen_source
    assert "zipfile.ZipFile" not in reopen_source
    for private in ("_read_member", "_refuse_implausible", "_refuse_special_member"):
        assert private not in module_source
