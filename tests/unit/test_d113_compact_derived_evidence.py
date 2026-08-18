"""The accepted Decision 113 compact derived resolution and corroboration evidence.

D112 applied one principle -- persist an entry only where it carries information the canonical
row does not already carry -- to the raw observation layer, and measured what it left behind:
the Decision 012 resolution layer at 4,172.8 bytes per accession, 67.7 % of everything E0
persists, and the full-index corroboration layer at about 29.6 GB across seventy quarters.
D113 is the owner's ruling that the same principle reaches both.

This module holds the proofs. Four claims carry the contract:

**Logical equivalence (§12).** Omitting a resolution row must not change the resolution. The
comparison is *logical*, not physical: every accession's complete field and cohort resolution is
rendered from the persisted rows where they exist and from the reconstruction where they do not,
and the two contracts must agree exactly -- status, value, authority, winning and competing
identifier lists, reason codes, materiality, blocking state, detail text, cohorts, and prior
cohorts. That is strictly stronger than the physical row comparison it replaces, because it
holds over the same columns *and* requires the omitted rows to be rebuildable from what remains.

**Sufficiency (§12).** The D093 §6 linkage resolver must answer every classification against a
connection on which the field-observation tables *and both resolution tables* are unreadable, so
a resolver that reached for one fails rather than quietly succeeding.

**Replay (§§8, 9).** The resolution-completeness digest is over the full logical resolution set,
implicit and explicit alike, so the full-observation path and the compact path reach the same
value; and a second, independent world built from the same frozen artifacts reproduces it, along
with the corroboration digest, the member manifest, and the compact-evidence identity.

**Non-vacuity (§13).** Four mutations, each of which must break something: treating a conflict
as an implicit default, dropping a corroboration assertion, altering an implicitly reconstructed
resolution, and altering the omitted ``raw_line`` of a full-index row.

The world is the hostile D112 fixture, reused rather than re-invented: a joint filing whose
witnesses agree, a joint filing whose witnesses disagree on ``form``, a malformed ``filingDate``,
a blank ``reportDate``, a whitespace-padded ``form``, absent optional fields, ungoverned fields,
and a ``company.idx`` quarter carrying both a corroborating row and a co-registrant row. Under
D113 that fixture splits five ways -- five accessions keep explicit resolutions and three become
implicit, one of them corroborated by the index -- which is what makes each branch reachable.

Everything runs over synthetic archives and disposable catalogs beneath ``tmp_path``. No test
resolves, opens, names, or infers the accepted private evidence root, none reads a real SEC
artifact, and none touches a real catalog.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d112_compact_evidence as d112  # noqa: E402

from disclosure_drift.m3 import offline_parse as op  # noqa: E402
from disclosure_drift.m3.compact_evidence import (  # noqa: E402
    ALWAYS_ABSENT_RESOLUTION_FIELDS,
    COMPACT_EVIDENCE_CONTRACT,
    COMPACT_EVIDENCE_CONTRACT_V1,
    COMPACT_EVIDENCE_SCHEMA_VERSION,
    DEFAULT_CANONICAL_RESOLUTION,
    INDEX_CORROBORATION_FIELDS,
    INDEX_PAYLOAD_OMITTED_FIELDS,
    CorroborationDigest,
    ResolutionDigest,
    corroboration_observations,
)
from disclosure_drift.sec.accession_resolution import (  # noqa: E402
    RESOLVED_FIELDS,
    AccessionResolution,
)
from disclosure_drift.sec.census import (  # noqa: E402
    CANONICAL_FIELD_BY_SOURCE_FIELD,
    reconstructed_accession_resolution,
)
from disclosure_drift.storage.sqlite import connect, transaction  # noqa: E402

_ORDINARY = d112._plain(d112._ORDINARY)
_INDEX_JOINT = d112._plain(d112._INDEX_JOINT)
_JOINT_CONFLICT = d112._plain(d112._JOINT_CONFLICT)


@pytest.fixture(scope="module")
def both_paths(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """One hostile world, run once under each evidence contract. The runs are pure."""
    root = tmp_path_factory.mktemp("d113")
    return d112._run(root / "full", compact=False), d112._run(root / "compact", compact=True)


# ==========================================================================
# The contract itself
# ==========================================================================
def test_the_contract_version_moved_and_the_old_one_is_not_reused() -> None:
    """D113 §11: ``/1`` cannot state the new rules, so ``/2`` states them and ``/1`` stands."""
    assert COMPACT_EVIDENCE_CONTRACT == "e0-compact-evidence/2"
    assert COMPACT_EVIDENCE_CONTRACT_V1 == "e0-compact-evidence/1"
    assert COMPACT_EVIDENCE_CONTRACT != COMPACT_EVIDENCE_CONTRACT_V1
    assert COMPACT_EVIDENCE_SCHEMA_VERSION == 2


def test_the_always_absent_fields_are_a_property_of_the_source_class(
    both_paths: tuple[Path, Path],
) -> None:
    """D113 §6: no source-native name maps to them, so no accession can resolve them.

    The contract states the set once; this derives it from the accepted field map instead, so
    a later source that *did* carry one would break the test rather than silently inherit an
    ``absent`` rule that no longer holds.
    """
    derived = frozenset(RESOLVED_FIELDS) - frozenset(CANONICAL_FIELD_BY_SOURCE_FIELD.values())
    assert derived == ALWAYS_ABSENT_RESOLUTION_FIELDS
    full, compact = both_paths
    with connect(full, writer=False) as reference:
        rows = reference.execute(
            "SELECT DISTINCT status FROM census_accession_field_resolutions "
            "WHERE field_name IN (?, ?)",
            tuple(sorted(ALWAYS_ABSENT_RESOLUTION_FIELDS)),
        ).fetchall()
    assert [str(row["status"]) for row in rows] == ["absent"]
    with connect(compact, writer=False) as subject:
        remaining = int(
            subject.execute(
                "SELECT COUNT(*) FROM census_accession_field_resolutions "
                "WHERE field_name IN (?, ?)",
                tuple(sorted(ALWAYS_ABSENT_RESOLUTION_FIELDS)),
            ).fetchone()[0]
        )
    # Not zero: an accession D113 §5 materializes keeps its whole resolution, always-absent
    # fields included, because the rule is per accession rather than per field. What must have
    # gone is the row for every accession whose resolution is the implicit default.
    assert 0 < remaining < 2 * _accession_count(full)


def test_the_index_corroboration_fields_are_all_canonical() -> None:
    """The three observed index fields are exactly the ones Decision 012 already maps."""
    assert set(INDEX_CORROBORATION_FIELDS) <= set(CANONICAL_FIELD_BY_SOURCE_FIELD)
    assert tuple(sorted(INDEX_CORROBORATION_FIELDS)) == INDEX_CORROBORATION_FIELDS
    assert frozenset({"raw_line"}) == INDEX_PAYLOAD_OMITTED_FIELDS


# ==========================================================================
# D113 §12 -- logical information equivalence
# ==========================================================================
def _accession_count(database: Path) -> int:
    with connect(database, writer=False) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM census_accessions").fetchone()[0])


def _rendered(resolution: AccessionResolution) -> dict[str, Any]:
    """One accession's complete governed resolution, rendered identically for both paths.

    Every component D113 §12 names is here -- status, value, authority, both identifier lists,
    reason codes, materiality, blocking state, the resolver's detail text, and every cohort
    consequence -- and nothing that is a wall clock.
    """
    return {
        "fields": {
            name: {
                "status": item.status,
                "value": None if item.value is None else str(item.value),
                "authority": item.authority,
                "winning": sorted(item.winning_observation_ids),
                "competing": sorted(item.competing_observation_ids),
                "correction": item.correction_evidence_id,
                "reasons": sorted(item.reason_codes),
                "material": item.is_material,
                "blocking": item.blocks_dependents,
                "detail": item.detail,
            }
            for name, item in sorted(resolution.fields.items())
        },
        "official_filing_temporal_cohort": resolution.official_filing_cohort,
        "accepted_temporal_cohort": resolution.accepted_cohort,
        "prior_filing_cohorts": sorted(resolution.prior_filing_cohorts),
        "cohort_boundary_crossed": resolution.cohort_boundary_crossed,
        "requires_2024_approval": resolution.requires_2024_approval,
        # The persisted cohort row carries the accession's *whole* reason-code union rather
        # than only the cohort-level extras, so the rendering matches the column it is
        # compared against rather than the attribute that happens to share its name.
        "cohort_reason_codes": sorted(resolution.reason_codes),
    }


def _persisted_resolution(connection: sqlite3.Connection, accession: str) -> dict[str, Any] | None:
    """One accession's resolution as its persisted rows state it, or ``None`` if omitted."""
    fields = connection.execute(
        "SELECT field_name, status, resolved_value, authority_class, "
        "winning_observation_ids_json, competing_observation_ids_json, correction_evidence_id, "
        "reason_codes_json, is_material, blocks_dependents, detail "
        "FROM census_accession_field_resolutions WHERE accession_plain = ?",
        (accession,),
    ).fetchall()
    cohort = connection.execute(
        "SELECT official_filing_temporal_cohort, accepted_temporal_cohort, "
        "prior_filing_cohorts_json, cohort_boundary_crossed, requires_2024_approval, "
        "reason_codes_json FROM census_accession_cohort_resolutions WHERE accession_plain = ?",
        (accession,),
    ).fetchone()
    if not fields or cohort is None:
        return None
    return {
        "fields": {
            str(row["field_name"]): {
                "status": str(row["status"]),
                "value": None if row["resolved_value"] is None else str(row["resolved_value"]),
                "authority": row["authority_class"],
                "winning": sorted(json.loads(str(row["winning_observation_ids_json"]))),
                "competing": sorted(json.loads(str(row["competing_observation_ids_json"]))),
                "correction": row["correction_evidence_id"],
                "reasons": sorted(json.loads(str(row["reason_codes_json"]))),
                "material": bool(row["is_material"]),
                "blocking": bool(row["blocks_dependents"]),
                "detail": str(row["detail"]),
            }
            for row in sorted(fields, key=lambda item: str(item["field_name"]))
        },
        "official_filing_temporal_cohort": str(cohort["official_filing_temporal_cohort"]),
        "accepted_temporal_cohort": str(cohort["accepted_temporal_cohort"]),
        "prior_filing_cohorts": sorted(json.loads(str(cohort["prior_filing_cohorts_json"]))),
        "cohort_boundary_crossed": bool(cohort["cohort_boundary_crossed"]),
        "requires_2024_approval": bool(cohort["requires_2024_approval"]),
        "cohort_reason_codes": sorted(json.loads(str(cohort["reason_codes_json"]))),
    }


def _logical_resolutions(database: Path) -> dict[str, dict[str, Any]]:
    """Every accession's complete logical Decision 012 resolution.

    The persisted rows where they exist; the D113 §4 reconstruction where they do not. The
    caller cannot tell which produced which, which is the whole claim.
    """
    with connect(database, writer=False) as connection:
        accessions = [
            str(row["accession_plain"])
            for row in connection.execute(
                "SELECT accession_plain FROM census_accessions ORDER BY accession_plain"
            ).fetchall()
        ]
        result: dict[str, dict[str, Any]] = {}
        for accession in accessions:
            persisted = _persisted_resolution(connection, accession)
            result[accession] = persisted or _rendered(
                reconstructed_accession_resolution(connection, accession)
            )
        return result


def _implicit_accessions(database: Path) -> set[str]:
    """The accessions whose resolution rows the compact contract did not write."""
    with connect(database, writer=False) as connection:
        return {
            str(row["accession_plain"])
            for row in connection.execute(
                "SELECT accession_plain FROM census_accessions WHERE accession_plain NOT IN "
                "(SELECT accession_plain FROM census_accession_field_resolutions)"
            ).fetchall()
        }


def test_every_logical_resolution_is_identical(both_paths: tuple[Path, Path]) -> None:
    """§12: the complete Decision 012 field and cohort resolutions, accession by accession."""
    full, compact = both_paths
    assert _logical_resolutions(compact) == _logical_resolutions(full)


def test_rows_were_actually_omitted(both_paths: tuple[Path, Path]) -> None:
    """The non-vacuity guard: a contract that wrote everything would pass the test above."""
    full, compact = both_paths
    assert not _implicit_accessions(full)
    implicit = _implicit_accessions(compact)
    assert implicit, "the compact path must omit at least one accession's resolution"
    with connect(full, writer=False) as a, connect(compact, writer=False) as b:
        for table in ("census_accession_field_resolutions", "census_accession_cohort_resolutions"):
            before = int(a.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608
            after = int(b.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608
            assert 0 < after < before


def test_an_implicit_accession_reconstructs_to_exactly_the_row_that_was_not_written(
    both_paths: tuple[Path, Path],
) -> None:
    """The reconstruction is the omitted row, not an approximation of it.

    Asked of the compact catalog *after* canonical projection and after the association
    projection has run, which is the state a real reader meets. Both rewrite
    ``census_accessions``; if either moved a value the reconstruction depends on, the answer
    here would differ from the row the full path holds.
    """
    full, compact = both_paths
    implicit = _implicit_accessions(compact)
    assert implicit
    with connect(full, writer=False) as reference, connect(compact, writer=False) as subject:
        for accession in sorted(implicit):
            expected = _persisted_resolution(reference, accession)
            assert expected is not None
            assert _rendered(reconstructed_accession_resolution(subject, accession)) == expected


def test_a_corroborated_accession_is_among_the_implicit_ones(
    both_paths: tuple[Path, Path],
) -> None:
    """The interesting branch is reachable: an omitted resolution over a corroborated accession.

    Its ``form`` and ``official_filing_date`` resolutions name a *second* competing observation
    that no row in the compact catalog holds -- the index row's -- so reconstructing it requires
    the corroboration assertion and not merely the canonical accession row.
    """
    _, compact = both_paths
    assert _ORDINARY in _implicit_accessions(compact)
    with connect(compact, writer=False) as connection:
        resolution = reconstructed_accession_resolution(connection, _ORDINARY)
        assert len(resolution.fields["form"].competing_observation_ids) == 2
        assert len(resolution.fields["official_filing_date"].competing_observation_ids) == 2
        assert resolution.fields["form"].authority == "entity_submissions"
        stored = int(
            connection.execute(
                "SELECT COUNT(*) FROM census_accession_observations WHERE accession_plain = ?",
                (_ORDINARY,),
            ).fetchone()[0]
        )
    assert stored == 0


def test_a_disagreeing_or_co_registrant_index_row_stays_explicit(
    both_paths: tuple[Path, Path],
) -> None:
    """§10: a row that changes the association set is never compacted into a corroboration."""
    full, compact = both_paths

    def index_observations(database: Path) -> dict[str, int]:
        with connect(database, writer=False) as connection:
            return {
                str(row["accession_plain"]): int(row["rows"])
                for row in connection.execute(
                    "SELECT o.accession_plain, COUNT(*) AS rows "
                    "FROM census_accession_observations AS o "
                    "JOIN census_source_observations AS s "
                    "  ON s.observation_id = o.source_observation_id "
                    "WHERE s.source_id = 'sec_full_index_company' "
                    "GROUP BY o.accession_plain"
                ).fetchall()
            }

    before = index_observations(full)
    after = index_observations(compact)
    assert before[_ORDINARY] == 3, "the fixture must carry a purely corroborating index row"
    # Two index rows on one accession: a co-registrant and a corroboration of the submissions
    # registrant. The full contract writes three observations for each; the compact contract
    # keeps the co-registrant's three and omits the corroboration's, on the same accession.
    assert before[_INDEX_JOINT] == 6, "the fixture must carry a co-registrant index row"
    assert _ORDINARY not in after
    assert after[_INDEX_JOINT] == 3


# ==========================================================================
# D113 §12 -- downstream sufficiency, with the resolution tables denied too
# ==========================================================================
_DENIED_TABLES = (
    "census_accession_observations",
    "census_parsed_records",
    "census_accession_field_resolutions",
    "census_accession_cohort_resolutions",
)


def _connection_without_redundant_tables(database: Path) -> sqlite3.Connection:
    """A read-only connection on which every observation and resolution table raises."""
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row

    def authorizer(action: int, first: str | None, *_rest: object) -> int:
        if first in _DENIED_TABLES:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(authorizer)
    return connection


@pytest.mark.parametrize("table", _DENIED_TABLES)
def test_the_denial_harness_denies_every_named_table(
    both_paths: tuple[Path, Path], table: str
) -> None:
    """The sufficiency proof is worthless if the authorizer is inert, so it is tested first."""
    _, compact = both_paths
    connection = _connection_without_redundant_tables(compact)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608
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
def test_r52_linkage_resolves_with_both_resolution_tables_denied(
    both_paths: tuple[Path, Path], registrant: int, form: str, filing_date: str
) -> None:
    """§12's R52 clause: sufficiency proved by removing the fallback, not asserted."""
    full, compact = both_paths
    with connect(full, writer=False) as reference:
        expected = d112._linkage_resolution(
            reference,
            asserted_form=form,
            asserted_filing_date=filing_date,
            registrant_cik=registrant,
        )
    connection = _connection_without_redundant_tables(compact)
    try:
        actual = d112._linkage_resolution(
            connection,
            asserted_form=form,
            asserted_filing_date=filing_date,
            registrant_cik=registrant,
        )
    finally:
        connection.close()
    assert actual == expected


def test_association_totality_is_unchanged(both_paths: tuple[Path, Path]) -> None:
    """§12: the association set, its completeness, and the corroboration it depends on."""
    full, compact = both_paths

    def state(database: Path) -> list[tuple[Any, ...]]:
        with connect(database, writer=False) as connection:
            return sorted(
                tuple(row)
                for row in connection.execute(
                    "SELECT a.accession_plain, a.registrant_cik_numeric, "
                    "a.registrant_set_completeness, r.registrant_cik_padded, "
                    "r.association_class, r.evidence_level "
                    "FROM census_accessions AS a "
                    "LEFT JOIN census_accession_registrants AS r "
                    "  ON r.accession_plain = a.accession_plain"
                ).fetchall()
            )

    established = state(full)
    assert any(row[2] == "established" for row in established), (
        "the fixture must establish at least one association set or corroboration proves nothing"
    )
    assert state(compact) == established


# ==========================================================================
# D113 §§8, 9 -- the completeness and corroboration digests, and their replay
# ==========================================================================
@pytest.fixture(scope="module")
def evidence(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    """The run-local evidence each contract accumulated over the same world."""
    root = tmp_path_factory.mktemp("d113-evidence")
    captured: dict[str, dict[str, Any]] = {}
    for name, compact in (("full", False), ("compact", True)):
        capture: dict[str, Any] = {}
        capture["database"] = d112._run(root / name, compact=compact, capture=capture)
        captured[name] = capture
    return captured


def test_the_resolution_digest_is_over_the_logical_set_and_not_the_physical_one(
    evidence: dict[str, dict[str, Any]],
) -> None:
    """§8: the same digest under both contracts, because omission is not part of it.

    This is the sharpest single statement of §12. One value covers every accession's complete
    resolution -- implicitly reconstructed and explicitly materialized alike -- so a compact run
    that lost, altered, or invented any part of any resolution could not reach it.
    """
    full = evidence["full"]["resolution_evidence"]
    compact = evidence["compact"]["resolution_evidence"]
    assert full.completeness_digest() == compact.completeness_digest()
    assert full.accessions == compact.accessions > 0
    assert full.implicit == 0
    assert compact.implicit > 0
    assert compact.explicit > 0
    assert compact.omitted_field_rows == compact.implicit * len(RESOLVED_FIELDS)
    assert (
        compact.materialized_field_rows + compact.omitted_field_rows == full.materialized_field_rows
    )


def test_the_resolution_digest_replays_in_an_independent_world(
    tmp_path: Path, evidence: dict[str, dict[str, Any]]
) -> None:
    """§8: a second world built from scratch over the same frozen artifacts agrees.

    Nothing is shared -- separate archives on disk, separate catalogs, separate connections,
    separate identifiers -- so an ingredient that was a property of *this* write rather than of
    the evidence would move the digest and fail here.
    """
    capture: dict[str, Any] = {}
    d112._run(tmp_path / "replay", compact=True, capture=capture)
    assert (
        capture["resolution_evidence"].completeness_digest()
        == evidence["compact"]["resolution_evidence"].completeness_digest()
    )


def test_the_corroboration_digest_replays_and_counts_what_it_compacted(
    tmp_path: Path, evidence: dict[str, dict[str, Any]]
) -> None:
    """§9: the quarter's assertions are bound, replayable, and honestly counted."""
    compact = evidence["compact"]["corroboration"]
    full = evidence["full"]["corroboration"]
    assert compact.index_rows == full.index_rows > 0
    assert compact.corroborating > 0, "the fixture must carry a purely corroborating row"
    assert compact.exceptions > 0, "and a row D113 §10 keeps explicit"
    assert full.corroborating == 0
    assert compact.omitted_observations == compact.corroborating * len(INDEX_CORROBORATION_FIELDS)
    assert compact.written + compact.omitted_observations == full.written
    # The digest is over the assertions and their dispositions, so the two contracts reach
    # different values -- and a replay of the same contract reaches the same one.
    assert compact.digest != full.digest
    capture: dict[str, Any] = {}
    d112._run(tmp_path / "replay", compact=True, capture=capture)
    assert capture["corroboration"].digest == compact.digest


def test_the_sidecar_carries_both_new_evidence_shapes(
    tmp_path: Path, evidence: dict[str, dict[str, Any]]
) -> None:
    """§11: the run-local schema states the rules it applied, and binds them into its identity."""
    from disclosure_drift.m3.compact_evidence import CompactEvidenceSidecar

    resolution = evidence["compact"]["resolution_evidence"]
    corroboration = evidence["compact"]["corroboration"]
    observation = evidence["compact"]["index_observation"]
    sidecar = CompactEvidenceSidecar(tmp_path / "compact_evidence.sqlite3")
    try:
        empty = sidecar.identity()
        sidecar.record_resolution(
            resolution_scope="catalog",
            accessions=resolution.accessions,
            implicit_resolutions=resolution.implicit,
            explicit_resolutions=resolution.explicit,
            omitted_field_rows=resolution.omitted_field_rows,
            materialized_field_rows=resolution.materialized_field_rows,
            omitted_cohort_rows=resolution.omitted_cohort_rows,
            materialized_cohort_rows=resolution.materialized_cohort_rows,
            completeness_digest=resolution.completeness_digest(),
        )
        sidecar.record_corroboration(
            source_observation_id=observation.observation_id,
            source_id=observation.source_id,
            artifact_sha256=str(observation.logical_sha256),
            index_rows=corroboration.index_rows,
            corroborating=corroboration.corroborating,
            exceptions=corroboration.exceptions,
            unbound=len(corroboration.unbound),
            omitted_observations=corroboration.omitted_observations,
            materialized_observations=corroboration.written,
            corroboration_digest=corroboration.digest,
        )
        stored = sidecar.resolution_evidence("catalog")
        assert stored is not None
        assert stored["implicit_rule"] == DEFAULT_CANONICAL_RESOLUTION
        assert json.loads(str(stored["always_absent_fields_json"])) == sorted(
            ALWAYS_ABSENT_RESOLUTION_FIELDS
        )
        assert stored["completeness_digest"] == resolution.completeness_digest()
        assert stored["contract"] == COMPACT_EVIDENCE_CONTRACT
        assert stored["schema_version"] == COMPACT_EVIDENCE_SCHEMA_VERSION
        assert sidecar.corroboration_evidence(observation.observation_id) is not None
        # Both shapes are inside the identity D113 §11 requires the freeze to bind.
        assert sidecar.identity() != empty
    finally:
        sidecar.close()


# ==========================================================================
# D113 §13 -- non-vacuity: four mutations, each of which must break something
# ==========================================================================
def _mutated(
    source: Path, destination: Path, statements: list[tuple[str, tuple[Any, ...]]]
) -> Path:
    """A copy of one catalog with the given statements applied. Never the original."""
    destination.write_bytes(source.read_bytes())
    with connect(destination, writer=True) as connection, transaction(connection) as active:
        for statement, parameters in statements:
            active.execute(statement, parameters)
    return destination


def test_a_treating_a_conflict_as_an_implicit_default_breaks_the_result(
    both_paths: tuple[Path, Path], tmp_path: Path
) -> None:
    """§13.A: the default rule is not applicable to a conflict, and applying it changes the result.

    The fixture's joint filing disagrees on ``form``: its resolution is ``unresolved`` and
    material, and no canonical accession row can imply that -- a canonical row states one value
    and therefore implies agreement. The mutation applies the default rule where D113 §5 forbids
    it, by removing both the resolution rows *and* the exception observations that carry the
    disagreement, which is exactly what "treating a conflict as an implicit default" would mean.
    The reconstruction then reports ``resolved`` where the truth is ``unresolved``, and the
    logical resolution set no longer matches the full-observation path.

    What this does **not** claim is that omitting a conflicting accession's resolution rows on
    their own is lossy. It is not, and that is a property of the contract rather than an
    accident: the exception observations D112 materializes are what carry the disagreement, so
    the reconstruction rebuilds it. The predicate refuses such an accession anyway, because
    ``prior_filing_cohorts`` and an approved 2024 transition live nowhere else -- which is why
    the rule is decided by comparison and not by a list of cases.
    """
    full, compact = both_paths
    with connect(compact, writer=False) as connection:
        before = _persisted_resolution(connection, _JOINT_CONFLICT)
    assert before is not None
    assert before["fields"]["form"]["status"] == "unresolved"
    assert before["fields"]["form"]["blocking"] is True
    broken = _mutated(
        compact,
        tmp_path / "conflict.sqlite3",
        [
            (
                "DELETE FROM census_accession_field_resolutions WHERE accession_plain = ?",
                (_JOINT_CONFLICT,),
            ),
            (
                "DELETE FROM census_accession_cohort_resolutions WHERE accession_plain = ?",
                (_JOINT_CONFLICT,),
            ),
            (
                "DELETE FROM census_accession_observations WHERE accession_plain = ?",
                (_JOINT_CONFLICT,),
            ),
        ],
    )
    with connect(broken, writer=False) as connection:
        reconstructed = reconstructed_accession_resolution(connection, _JOINT_CONFLICT)
    assert reconstructed.fields["form"].status == "resolved"
    assert not reconstructed.fields["form"].blocks_dependents
    assert _rendered(reconstructed) != before
    assert _logical_resolutions(broken) != _logical_resolutions(full)


def test_the_omission_predicate_refuses_what_the_canonical_row_cannot_carry() -> None:
    """D113 §5 in one assertion, over the predicate rather than over a catalog.

    ``prior_filing_cohorts`` and an approved 2024 transition are recorded in the resolution and
    nowhere else, so a reconstruction that assumed neither would silently drop both. The
    predicate compares whole resolutions, so it refuses them without needing a clause for each.
    """
    from disclosure_drift.m3.compact_evidence import is_default_resolution
    from disclosure_drift.sec.accession_resolution import resolve_accession

    observations = [
        d113_observation("form", "10-K"),
        d113_observation("official_filing_date", "2024-02-01"),
    ]
    default = resolve_accession("000000000124000001", observations)
    assert is_default_resolution(default, default)
    with_history = resolve_accession(
        "000000000124000001", observations, prior_filing_dates=("2021-02-01",)
    )
    assert not is_default_resolution(with_history, default)
    conflicted = resolve_accession(
        "000000000124000001",
        [*observations, d113_observation("form", "10-K/A", suffix="-rival")],
    )
    assert conflicted.fields["form"].status == "unresolved"
    assert not is_default_resolution(conflicted, default)


def d113_observation(field: str, value: str, *, suffix: str = "") -> Any:
    """One synthetic Decision 012 observation, for predicate tests that need no catalog."""
    from disclosure_drift.sec.accession_resolution import AccessionFieldObservation

    return AccessionFieldObservation(
        observation_id=f"obs-{field}{suffix}",
        source_id="sec_bulk_submissions",
        accession_plain="000000000124000001",
        field_name=field,
        value=value,
        observed_at_utc="2026-01-01T00:00:00Z",
    )


def test_b_dropping_a_corroboration_assertion_changes_the_governed_result(
    both_paths: tuple[Path, Path], tmp_path: Path
) -> None:
    """§13.B: the assertion is what establishes corroboration, so losing it must be visible.

    Deleting the corroborating index row's parsed record -- the assertion itself -- must remove
    the accession's full-index membership and therefore its corroboration. §6.2 condition 2
    counts an uncorroborated member, so the association set can no longer be established.
    """
    _, compact = both_paths
    with connect(compact, writer=False) as connection:
        identity = str(
            connection.execute(
                "SELECT native_identity FROM census_parsed_records "
                "WHERE native_identity >= ? AND native_identity < ? ORDER BY native_identity",
                (
                    f"{op.INDEX_ROW_PREFIX}{d112._ORDINARY}:",
                    f"{op.INDEX_ROW_PREFIX}{d112._ORDINARY};",
                ),
            ).fetchone()["native_identity"]
        )
    broken = _mutated(
        compact,
        tmp_path / "assertion.sqlite3",
        [("DELETE FROM census_parsed_records WHERE native_identity = ?", (identity,))],
    )
    with connect(broken, writer=True) as connection:
        groups = {
            group.accession_plain: group
            for group in op._stream_membership_groups(
                connection, op.membership_observation_sources(connection), compact=True
            )
        }
    assert _ORDINARY in groups
    assert not groups[_ORDINARY].full_index, "the corroboration must be gone"
    assert groups[_ORDINARY].submissions - groups[_ORDINARY].full_index, (
        "and the member must therefore be uncorroborated"
    )


def test_c_altering_an_implicitly_reconstructed_resolution_moves_the_digest(
    both_paths: tuple[Path, Path], tmp_path: Path
) -> None:
    """§13.C: the completeness digest is not a decoration over the omitted rows."""
    _, compact = both_paths
    with connect(compact, writer=False) as connection:
        original = ResolutionDigest()
        for accession in sorted(_implicit_accessions(compact)):
            original.record(reconstructed_accession_resolution(connection, accession))
    accession = sorted(_implicit_accessions(compact))[0]
    broken = _mutated(
        compact,
        tmp_path / "reconstruction.sqlite3",
        [
            (
                "UPDATE census_accessions SET form_type = '8-K' WHERE accession_plain = ?",
                (accession,),
            )
        ],
    )
    with connect(broken, writer=False) as connection:
        mutated = ResolutionDigest()
        for item in sorted(_implicit_accessions(compact)):
            mutated.record(reconstructed_accession_resolution(connection, item))
    assert mutated.hexdigest() != original.hexdigest()


def test_d_altering_an_omitted_full_index_field_moves_the_replay_binding(
    both_paths: tuple[Path, Path],
) -> None:
    """§13.D: ``raw_line`` is dropped from the payload but stays inside ``record_sha256``.

    The corroboration digest folds each row's content digest, and the content digest is taken
    over the **complete** parsed record. Altering the omitted raw text therefore moves the
    digest, which is what makes the omission bound rather than merely undetectable.
    """
    _, compact = both_paths
    with connect(compact, writer=False) as connection:
        rows = connection.execute(
            "SELECT native_identity, record_sha256, payload_json FROM census_parsed_records "
            "WHERE native_identity >= ? AND native_identity < ? ORDER BY native_identity",
            (op.INDEX_ROW_PREFIX, f"{op.INDEX_ROW_PREFIX};"),
        ).fetchall()
    assert rows

    def digest_of(alter: bool) -> str:
        digest = CorroborationDigest("sec_full_index_company", "artifact")
        for row in rows:
            payload = json.loads(str(row["payload_json"]))
            plain, cik = op._index_identity(payload)
            assert plain is not None and cik is not None
            digest.record(
                native_identity=str(row["native_identity"]),
                # The parser hashes the complete record, so a changed raw line changes this.
                record_sha256=("mutated" if alter else str(row["record_sha256"])),
                accession_plain=plain,
                cik_padded=cik,
                observed=dict(corroboration_observations(payload, cik_padded=cik)),
                disposition="corroborating",
            )
        return digest.hexdigest()

    assert digest_of(alter=True) != digest_of(alter=False)
    # And the omitted key really is absent from what the compact contract persisted.
    assert all("raw_line" not in json.loads(str(row["payload_json"])) for row in rows)


def test_the_accepted_totality_object_is_identical(
    evidence: dict[str, dict[str, Any]],
) -> None:
    """§12: the Decision 094 §9.5 totality, counter for counter, not merely its persisted rows.

    The counters are where a reconstruction that over-produced would show. An index row bound to
    an accession the authoritative layer does not carry writes no membership observation under
    the full contract, so a compact reconstruction that restored one anyway would hand the §6.4
    projection a group for an accession that does not exist and increment ``orphans``. The
    fixture carries exactly such a row so that this comparison can see it.
    """
    full = evidence["full"]
    compact = evidence["compact"]
    assert compact["unbound"] == full["unbound"]
    assert compact["unbound"], "the fixture must carry an index row that binds to nothing"
    assert compact["totality"] == full["totality"]


def test_a_multi_registrant_accession_keeps_its_reconstructed_membership(
    both_paths: tuple[Path, Path],
) -> None:
    """The scalar a reconstruction reads is cleared by §6.4 item 2, so it is back-filled first.

    The compact contract omits an accession's submissions-side ``cik`` observation because
    ``census_accessions.registrant_cik_numeric`` carries the identical value with the identical
    provenance. Decision 094 §6.4 item 2 then **clears that column** on a multi-registrant
    accession, before the second relation row is inserted. From that moment the omitted row is
    no longer reconstructible, so the completeness pass -- which re-derives the verdict rather
    than remembering it -- would read a group with no submissions side, find it unestablished,
    and disagree with the pass that counted it. The §9.5 totality invariant refuses that, which
    is how it was found: measured on the real first planned source with one real ``company.idx``
    quarter, 8 established multi-registrant accessions.

    The fixture reaches the same state deliberately: a joint filing whose co-registrant is
    bindable and whose submissions registrant the index also lists, so the accession is
    established with two members. Both contracts must hold the observation, one because it was
    never omitted and the other because it was written back before the column went.
    """
    full, compact = both_paths

    def established_multi(database: Path) -> set[str]:
        with connect(database, writer=False) as connection:
            return {
                str(row["accession_plain"])
                for row in connection.execute(
                    "SELECT a.accession_plain FROM census_accessions AS a "
                    "JOIN census_accession_registrants AS r "
                    "  ON r.accession_plain = a.accession_plain "
                    "  AND r.association_class = 'substantive' "
                    "WHERE a.registrant_set_completeness = 'established' "
                    "GROUP BY a.accession_plain HAVING COUNT(*) > 1"
                ).fetchall()
            }

    expected = established_multi(full)
    assert expected, "the fixture must establish a multi-registrant accession or this is vacuous"
    assert established_multi(compact) == expected

    def membership(database: Path, *, compact_evidence: bool) -> dict[str, set[str]]:
        """What the §6.2 projection actually reads, stored and reconstructed together."""
        seen: dict[str, set[str]] = {}
        with connect(database, writer=False) as connection:
            for row in op._merged_membership_rows(connection, compact=compact_evidence):
                seen.setdefault(str(row["accession_plain"]), set()).add(
                    f"{row['field_name']}={row['raw_value_json']}"
                )
        return seen

    stored = membership(full, compact_evidence=False)
    reconstructed = membership(compact, compact_evidence=True)
    for accession in sorted(expected):
        with connect(compact, writer=False) as connection:
            scalar = connection.execute(
                "SELECT registrant_cik_numeric FROM census_accessions WHERE accession_plain = ?",
                (accession,),
            ).fetchone()["registrant_cik_numeric"]
        assert scalar is None, "§6.4 item 2 must have cleared the scalar"
        assert reconstructed[accession] == stored[accession]
    # And nowhere else either: the whole membership stream both contracts project from.
    assert reconstructed == stored


# ==========================================================================
# D113 §19 -- the corrected capacity requirement
# ==========================================================================
def test_the_capacity_requirement_is_arithmetic_over_measured_terms() -> None:
    """§19: every term is readable, and the total is the sum of them plus the governed reserve.

    Stated as arithmetic rather than as a number so a reviewer can check the projection against
    the record's own table instead of trusting a constant.
    """
    from disclosure_drift.m3 import capacity_plan

    requirement = capacity_plan.E0_WORKING_STATE_REQUIREMENT
    components = requirement.component_bytes()
    assert set(components) == {density.component for density in requirement.densities}
    assert requirement.working_state_bytes() == sum(components.values())
    assert requirement.required_bytes() == (
        requirement.working_state_bytes()
        + requirement.overhead_bytes()
        + capacity_plan.GOVERNED_RESERVE_BYTES
    )
    assert capacity_plan.GOVERNED_RESERVE_BYTES == 25 * 1024**3
    assert every_density_names_its_source(requirement)
    # The projected working state is the record's §15 figure, not a placeholder.
    assert 60e9 < requirement.working_state_bytes() < 80e9


def every_density_names_its_source(requirement: Any) -> bool:
    """Whether every measured term carries the record that measured it."""
    return all(density.measured_by for density in requirement.densities) and all(
        planned.measured_by for planned in requirement.units
    )


def test_the_requirement_identity_is_pinned() -> None:
    """§19: changing a measured density must be a deliberate act, not a quiet edit.

    The identity digests every density, every planned count, every fixed cost, the reserve, and
    the plan fingerprint. Pinning it here is the same discipline Decision 094 §1.1 applies to
    the packaged migration digests: the number a future preflight refuses on cannot drift
    without this test saying so.
    """
    from disclosure_drift.m3 import capacity_plan

    assert capacity_plan.E0_WORKING_STATE_REQUIREMENT.identity() == (
        "791618e03a8ed6028d6b0ba70f1fca4473d2434b52e99ec1ddddaec97dba2b31"
    )


def test_the_plan_fingerprint_reads_the_plan_and_nothing_else(
    both_paths: tuple[Path, Path],
) -> None:
    """§19: the fingerprint is a property of the plan, stable across a run's progress.

    Taken over the same catalog before and after a complete parse, resolution, and association --
    which is the whole of what E0 writes -- it must not move, or the predicate would refuse a
    catalog merely because work had happened in it.
    """
    from disclosure_drift.m3 import capacity_plan

    full, compact = both_paths
    with connect(full, writer=False) as reference, connect(compact, writer=False) as subject:
        assert capacity_plan.plan_fingerprint(subject) == capacity_plan.plan_fingerprint(reference)
        fingerprint, sources = capacity_plan.plan_fingerprint(subject)
    assert len(fingerprint) == 64
    assert sources > 0
    assert fingerprint != capacity_plan.E0_WORKING_STATE_REQUIREMENT.plan_fingerprint
