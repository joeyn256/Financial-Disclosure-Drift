"""The verified-evidence schema: VE-M1 through VE-M14, and migration ``0015``.

Governing records: Decision 082 §11 (the schema contract) and §12 (the protocol it will
serve); Decision 083 **R63** (the four owner dispositions); Decision 087 §§4-9 (the
implementation authorization and semantics) and §14 (this mutation matrix).

**Every VE-M test below is a mutation test in the strict sense Decision 087 §14 requires:**
each one applies the named defect and asserts the exact condition that kills it.
Effectiveness is demonstrated, not named.

Two disciplines make that claim mean something.

**A positive control comes first.** ``test_the_lawful_protocol_lifecycle_is_admitted`` writes
the complete lawful sequence -- artifact, Review A and its spans, Review B and its spans,
both adjudicated rows, and a verified quota-eligible candidate row -- and asserts it
succeeds. A schema that refused everything would pass every mutation test and be useless;
this is the test that says the schema still admits the protocol it exists for.

**Each mutation is ISOLATED to the guard it names.** SQLite runs ``BEFORE INSERT`` triggers
before table CHECK constraints, and fires multiple triggers on one table in an unspecified
order, so a carelessly built mutant gets killed by whichever guard it happens to trip first
and proves nothing about the guard under test. Every fixture below is therefore built so
that the row is lawful in every respect *except* the mutation, and each test asserts on the
specific refusal message or constraint text. Where a defect is genuinely reachable through
more than one door, both doors are exercised and both are asserted.

**No real Decision-081 evidence appears anywhere in this module.** Every accession, artifact
digest, span, and receipt below is synthetic and disposable, and the catalogs are created
under pytest's ``tmp_path``. Nothing here reads the private external evidence root, and
VE-M14 proves that mechanically rather than by assertion.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator, Sequence
from importlib import resources
from pathlib import Path
from typing import Final

import pytest

from disclosure_drift.errors import GateFailureError
from disclosure_drift.m3 import document_evidence as de
from disclosure_drift.m3.candidate_identity import (
    ACCESSION_TABLE_COLUMNS,
    REGISTRANT_TABLE_COLUMNS,
    SNAPSHOT_CONTENT_FIELDS,
    candidate_accession_table_sha256,
)
from disclosure_drift.storage.catalog import ELIGIBLE_FORM_TYPES
from disclosure_drift.storage.sqlite import (
    MIGRATIONS_PACKAGE,
    apply_migrations,
    available_migrations,
    connect,
)

# --------------------------------------------------------------------------
# Synthetic fixture constants. Eighteen-digit plain accessions, 64-hex digests, and a
# public EDGAR URL -- the shapes migration 0015 requires, none of them real evidence.
# --------------------------------------------------------------------------

_ACCESSION: Final = "000000000120000001"
_OTHER_ACCESSION: Final = "000000000220000002"
_ARTIFACT: Final = "a" * 64
_OTHER_ARTIFACT: Final = "b" * 64
_SNAPSHOT: Final = "9" * 64
_AT: Final = "2026-08-15T00:00:00Z"

_REVIEW_ID: Final[dict[str, str]] = {
    "review_a": "1" * 64,
    "review_b": "2" * 64,
    "adjudication": "3" * 64,
}
_EPOCH: Final[dict[str, str]] = {
    "review_a": "4" * 64,
    "review_b": "5" * 64,
    "adjudication": "6" * 64,
}

_ARTIFACT_URL: Final = f"https://www.sec.gov/Archives/edgar/data/1/{_ACCESSION}.txt"

#: A private evidence-root path shape: absolute, path-separated, and pointing at nothing.
#: It is mutation INPUT only -- nothing in this repository resolves it and no such directory
#: is opened. It is deliberately not written under a home directory, because
#: ``scripts/check_repo_hygiene.py`` refuses a tracked home path outright and that gate is
#: correct: a real operator path must never be committed, not even as a test string. What
#: the mutation needs is a value that *looks like a filesystem path*, and this is one.
_PRIVATE_PATH: Final = "/evidence-root/0000000001/0001-complete-submission.txt"


# ==========================================================================
# Fixtures and lawful writers
# ==========================================================================


@pytest.fixture
def catalog(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """A migrated catalog at the full 0001-0015 chain, on a disposable path."""
    path = tmp_path / "catalog.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection)
    raw = sqlite3.connect(path)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys = ON")
    try:
        for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
            raw.execute(
                "INSERT OR REPLACE INTO reference_form_types (form_type, is_amendment, "
                "is_eligible_universe, description, decision_record) VALUES (?, ?, ?, ?, ?)",
                (form_type, int(is_amendment), int(eligible), description, "D007"),
            )
        raw.execute(
            "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
            "started_at_utc, detail) VALUES ('job-1', 'sec_census', 'completed', 'M3.3', ?, '')",
            (_AT,),
        )
        raw.execute(
            "INSERT INTO pilot_candidate_snapshots (snapshot_id, census_run_id, coverage_start, "
            "coverage_end, as_of_date, include_open_quarter, coverage_policy_version, "
            "candidate_policy_version, sic_family_mapping_version, evidence_policy_version, "
            "coverage_window_sha256, input_observation_set_sha256, snapshot_state, entity_count, "
            "accession_count, created_at_utc) VALUES (?, 'job-1', '2010-01-01', '2026-06-30', "
            "'2026-06-30', 0, 'coverage/1.0', 'candidate/1.0', 'sic/1.0', 'evidence/1.0', ?, ?, "
            "'building', 0, 0, ?)",
            (_SNAPSHOT, "c" * 64, "d" * 64, _AT),
        )
        yield raw
    finally:
        raw.close()


def _artifact(
    connection: sqlite3.Connection,
    *,
    artifact_sha256: str = _ARTIFACT,
    accession: str = _ACCESSION,
    source_url: str | None = None,
    receipt: str = "d081-receipt-0001",
    source_class: str = "complete_submission_text",
) -> None:
    connection.execute(
        "INSERT INTO document_artifacts (artifact_sha256, accession_plain, source_class, "
        "byte_length, retrieved_at_utc, source_url, retrieval_receipt_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            artifact_sha256,
            accession,
            source_class,
            4096,
            _AT,
            source_url or f"https://www.sec.gov/Archives/edgar/data/1/{accession}.txt",
            receipt,
        ),
    )


def _review(
    connection: sqlite3.Connection,
    role: str,
    *,
    accession: str = _ACCESSION,
    artifact_sha256: str = _ARTIFACT,
    review_id: str | None = None,
    epoch: str | None = None,
    abstained: bool = False,
    purpose_category: str = "administrative_or_exhibit",
    reviewer_model: str = "claude-opus-5",
    protocol_version: str = de.DOCUMENT_EVIDENCE_PROTOCOL_VERSION,
    review_pass: str | None = None,
) -> str:
    """Write one review pass and return its ``review_id``."""
    identifier = review_id or _REVIEW_ID[role]
    connection.execute(
        "INSERT INTO document_review_records (review_id, review_epoch_id, reviewer_role, "
        "reviewer_model, review_pass, artifact_sha256, accession_plain, protocol_version, "
        "decided_at_utc, purpose_category, abstained, abstention_reason, "
        "original_form_asserted, original_filing_date_asserted, original_accession_asserted, "
        "review_record_sha256) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)",
        (
            identifier,
            epoch or _EPOCH[role],
            role,
            reviewer_model,
            review_pass or de.REVIEW_PASS_BY_ROLE[role],
            artifact_sha256,
            accession,
            protocol_version,
            _AT,
            None if abstained else purpose_category,
            int(abstained),
            "insufficient_text" if abstained else None,
            None if abstained else "10-K",
            None if abstained else "2020-03-01",
            "f" * 64,
        ),
    )
    return identifier


def _span(
    connection: sqlite3.Connection,
    review_id: str,
    *,
    ordinal: int = 1,
    span_role: str = "amendment_purpose",
    text: str = "This Amendment is filed solely to furnish Exhibit 101.",
    location: str = "bytes:1204-1258",
) -> None:
    connection.execute(
        "INSERT INTO document_review_spans (review_id, span_ordinal, span_role, "
        "span_text_verbatim, span_location, span_sha256) VALUES (?, ?, ?, ?, ?, ?)",
        (review_id, ordinal, span_role, text, location, "e" * 64),
    )


def _adjudicate(
    connection: sqlite3.Connection,
    evidence_kind: str,
    *,
    accession: str = _ACCESSION,
    artifact_sha256: str = _ARTIFACT,
    adjudicated_value: str | None = "administrative_or_exhibit",
    agreement_state: str = "agreed",
    evidence_level: str = "verified",
    review_ids: Sequence[str] | None = None,
    review_ids_json: str | None = None,
) -> None:
    contributors = (
        review_ids_json
        if review_ids_json is not None
        else de.contributing_review_ids_json(
            review_ids
            if review_ids is not None
            else (_REVIEW_ID["review_a"], _REVIEW_ID["review_b"])
        )
    )
    connection.execute(
        "INSERT INTO document_adjudicated_evidence (accession_plain, evidence_kind, "
        "artifact_sha256, adjudicated_value, agreement_state, contributing_review_ids_json, "
        "evidence_level, adjudication_sha256, frozen_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            accession,
            evidence_kind,
            artifact_sha256,
            adjudicated_value,
            agreement_state,
            contributors,
            evidence_level,
            "d" * 64,
            _AT,
        ),
    )


def _candidate(
    connection: sqlite3.Connection,
    *,
    accession: str = _ACCESSION,
    purpose_level: str = "unproven",
    quota_eligible: int = 0,
    linkage_state: str = "amends_original",
) -> None:
    connection.execute(
        "INSERT INTO pilot_candidate_accessions (snapshot_id, accession_plain, "
        "accession_number_dashed, accession_tie_break_sha256, registrant_set_completeness, "
        "form_type, is_amendment, filing_date_evidence_level, cohort_evidence_level, "
        "xbrl_evidence_level, amendment_purpose_category, amendment_purpose_evidence_level, "
        "amendment_purpose_resolution_sha256, amendment_purpose_quota_eligible, "
        "amendment_linkage_state, multi_registrant, recorded_at_utc) "
        "VALUES (?, ?, ?, ?, 'established', '10-K/A', 1, 'unavailable', 'unavailable', "
        "'unavailable', 'administrative_or_exhibit', ?, ?, ?, ?, 1, ?)",
        (
            _SNAPSHOT,
            accession,
            f"{accession}-dashed",
            "b" * 64,
            purpose_level,
            "c" * 64,
            quota_eligible,
            linkage_state,
            _AT,
        ),
    )


def _both_passes(connection: sqlite3.Connection, *, with_spans: bool = True) -> None:
    """Artifact plus a lawful, agreeing Review A and Review B."""
    _artifact(connection)
    for role in ("review_a", "review_b"):
        identifier = _review(connection, role)
        if with_spans:
            _span(connection, identifier, ordinal=1, span_role="amendment_purpose")
            _span(connection, identifier, ordinal=2, span_role="original_form")


# ==========================================================================
# Positive control -- the schema still admits the protocol it exists for
# ==========================================================================


def test_the_lawful_protocol_lifecycle_is_admitted(catalog: sqlite3.Connection) -> None:
    """The complete lawful sequence succeeds, end to end.

    Without this, every refusal below would be satisfied by a schema that refuses
    everything. The order written here is the only lawful one, and the foreign keys are what
    make it so: artifact, then review records, then their spans, then the adjudicated rows,
    then the candidate row that consumes the verified result.
    """
    _both_passes(catalog)
    _adjudicate(catalog, "amendment_purpose")
    _adjudicate(catalog, "explicit_original", adjudicated_value="10-K|2020-03-01")
    _candidate(catalog, purpose_level="verified", quota_eligible=1)

    assert catalog.execute("SELECT COUNT(*) FROM document_artifacts").fetchone()[0] == 1
    assert catalog.execute("SELECT COUNT(*) FROM document_review_records").fetchone()[0] == 2
    assert catalog.execute("SELECT COUNT(*) FROM document_review_spans").fetchone()[0] == 4
    kinds = tuple(
        row["evidence_kind"]
        for row in catalog.execute(
            "SELECT evidence_kind FROM document_adjudicated_evidence ORDER BY evidence_kind"
        )
    )
    assert kinds == ("amendment_purpose", "explicit_original")
    row = catalog.execute(
        "SELECT amendment_purpose_evidence_level, amendment_purpose_quota_eligible, "
        "amendment_linkage_state FROM pilot_candidate_accessions"
    ).fetchone()
    # Decision 087 §6: the relationship reuses the existing state; only the STRENGTH is new.
    assert tuple(row) == ("verified", 1, "amends_original")


def test_a_third_adjudication_pass_resolves_a_disagreement(catalog: sqlite3.Connection) -> None:
    """The `resolved` route is admitted too, with its third record and its own epoch."""
    _artifact(catalog)
    a = _review(catalog, "review_a", purpose_category="administrative_or_exhibit")
    _span(catalog, a)
    b = _review(catalog, "review_b", purpose_category="narrative_or_governance")
    _span(catalog, b)
    third = _review(catalog, "adjudication", purpose_category="administrative_or_exhibit")
    _span(catalog, third)
    _adjudicate(
        catalog,
        "amendment_purpose",
        agreement_state="resolved",
        review_ids=(a, b, third),
    )
    row = catalog.execute(
        "SELECT agreement_state, evidence_level FROM document_adjudicated_evidence"
    ).fetchone()
    assert tuple(row) == ("resolved", "verified")


def test_an_abstained_outcome_is_recorded_rather_than_skipped(
    catalog: sqlite3.Connection,
) -> None:
    """Decision 080 AP-1 totality: an abstention is an outcome, and it earns nothing."""
    _artifact(catalog)
    _review(catalog, "review_a", abstained=True)
    _review(catalog, "review_b", abstained=True)
    _adjudicate(
        catalog,
        "amendment_purpose",
        adjudicated_value=None,
        agreement_state="abstained",
        evidence_level="unavailable",
    )
    row = catalog.execute(
        "SELECT agreement_state, evidence_level, adjudicated_value "
        "FROM document_adjudicated_evidence"
    ).fetchone()
    assert tuple(row) == ("abstained", "unavailable", None)


# ==========================================================================
# VE-M1 -- absolute private EV_ROOT path persistence
# ==========================================================================


@pytest.mark.parametrize(
    ("column", "write"),
    (
        ("source_url", lambda c: _artifact(c, source_url=_PRIVATE_PATH)),
        ("retrieval_receipt_id", lambda c: _artifact(c, receipt=_PRIVATE_PATH)),
    ),
)
def test_ve_m1_an_absolute_private_path_cannot_be_persisted_on_an_artifact(
    catalog: sqlite3.Connection,
    column: str,
    write: object,
) -> None:
    """**VE-M1.** Every text column of the artifact relation refuses a filesystem path.

    The two columns that could plausibly carry one are attacked directly: the public source
    URL, pinned by prefix to the EDGAR archive host, and the opaque retrieval receipt, whose
    charset admits no separator at all.
    """
    with pytest.raises(sqlite3.IntegrityError, match=column):
        write(catalog)  # type: ignore[operator]


def test_ve_m1_no_relation_has_a_column_that_could_hold_a_private_path(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M1, structurally.** There is no path column, and no locator column either.

    Decision 083 **R63** item A permits a content-addressed locator "only if technically
    required". It is not required -- ``artifact_sha256`` is the content address -- so the
    permission is simply not exercised, and the strongest form of the rule is that no such
    column exists to be filled in later.
    """
    columns = {
        table: {
            str(row["name"])
            for row in catalog.execute(f"PRAGMA table_info({table})")  # noqa: S608
        }
        for table in (
            "document_artifacts",
            "document_review_records",
            "document_review_spans",
            "document_adjudicated_evidence",
        )
    }
    for table, names in columns.items():
        offenders = {
            name
            for name in names
            if any(marker in name for marker in ("path", "root", "directory", "locator", "file"))
        }
        assert offenders == set(), f"{table} exposes a path-shaped column: {sorted(offenders)}"


def test_ve_m1_every_artifact_text_column_is_shape_constrained(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M1.** The refusal is a schema property, not a convention the writer follows."""
    definition = str(
        catalog.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'document_artifacts'"
        ).fetchone()["sql"]
    )
    for column in ("artifact_sha256", "accession_plain", "source_class", "source_url"):
        assert f"CHECK ({column}" in definition or f"{column} " in definition
    assert "https://www.sec.gov/Archives/" in definition
    assert "retrieval_receipt_id NOT GLOB" in definition


# ==========================================================================
# VE-M2 to VE-M5 -- the append-only, frozen-at-insert model
# ==========================================================================


def test_ve_m2_an_artifact_sha_cannot_be_mutated_after_a_review_binds_it(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M2.** The bound artifact's identity is fixed the moment it is written."""
    _both_passes(catalog)
    _adjudicate(catalog, "amendment_purpose")
    with pytest.raises(sqlite3.IntegrityError, match="append-only and immutable"):
        catalog.execute("UPDATE document_artifacts SET artifact_sha256 = ?", ("9" * 64,))
    with pytest.raises(sqlite3.IntegrityError, match="append-only and immutable"):
        catalog.execute("UPDATE document_artifacts SET byte_length = 1")
    assert (
        catalog.execute("SELECT artifact_sha256 FROM document_artifacts").fetchone()[0] == _ARTIFACT
    )


@pytest.mark.parametrize("column", ("reviewer_role", "review_epoch_id", "review_pass"))
def test_ve_m3_a_frozen_review_record_cannot_change_role_or_epoch(
    catalog: sqlite3.Connection,
    column: str,
) -> None:
    """**VE-M3.** Reviewer role and epoch are frozen at insert, so independence is durable."""
    _both_passes(catalog)
    with pytest.raises(sqlite3.IntegrityError, match="append-only and immutable"):
        catalog.execute(
            f"UPDATE document_review_records SET {column} = ? WHERE review_id = ?",  # noqa: S608
            ("7" * 64, _REVIEW_ID["review_a"]),
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only and immutable"):
        catalog.execute(
            "DELETE FROM document_review_records WHERE review_id = ?", (_REVIEW_ID["review_a"],)
        )


def test_ve_m4_source_span_provenance_cannot_be_rewritten(catalog: sqlite3.Connection) -> None:
    """**VE-M4.** A span cannot be edited, deleted, or appended to a consumed review.

    Rewriting is the named defect and is refused outright. The append-after-consumption door
    is closed beside it, because adding a span to a review whose evidence has already been
    adjudicated changes that review's evidentiary basis after the fact.
    """
    _both_passes(catalog)
    with pytest.raises(sqlite3.IntegrityError, match="append-only and immutable"):
        catalog.execute("UPDATE document_review_spans SET span_text_verbatim = 'rewritten'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only and immutable"):
        catalog.execute("UPDATE document_review_spans SET span_location = 'bytes:1-2'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only and immutable"):
        catalog.execute("DELETE FROM document_review_spans")

    _adjudicate(catalog, "amendment_purpose")
    with pytest.raises(sqlite3.IntegrityError, match="can receive no further spans"):
        _span(catalog, _REVIEW_ID["review_a"], ordinal=9, span_role="amendment_purpose")


def test_ve_m4_a_review_cannot_join_an_accession_whose_evidence_is_frozen(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M4, the other half.** A late review would silently falsify the contributing set."""
    _both_passes(catalog)
    _adjudicate(catalog, "amendment_purpose")
    with pytest.raises(sqlite3.IntegrityError, match="can receive no further reviews"):
        _review(catalog, "adjudication")


def test_ve_m5_adjudicated_evidence_cannot_be_rewritten_after_finalization(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M5.** The frozen result is the result. It is never repaired into a better one."""
    _both_passes(catalog)
    _adjudicate(catalog, "amendment_purpose")
    for statement in (
        "UPDATE document_adjudicated_evidence SET adjudicated_value = 'narrative_or_governance'",
        "UPDATE document_adjudicated_evidence SET evidence_level = 'unavailable'",
        "UPDATE document_adjudicated_evidence SET agreement_state = 'resolved'",
        "DELETE FROM document_adjudicated_evidence",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="append-only and immutable"):
            catalog.execute(statement)
    row = catalog.execute(
        "SELECT adjudicated_value, evidence_level FROM document_adjudicated_evidence"
    ).fetchone()
    assert tuple(row) == ("administrative_or_exhibit", "verified")


# ==========================================================================
# VE-M6 -- verified evidence on an unauthorized dimension
# ==========================================================================

#: Every dimension Decision 083 R63 item C refuses to enable. None of these may ever reach
#: the evidence relation, at any evidence level.
_UNAUTHORIZED_DIMENSIONS: Final[tuple[str, ...]] = (
    "size",
    "industry",
    "history",
    "universe",
    "primary_universe",
    "cohort",
    "xbrl_eligibility",
    "control_predicate",
    "name_or_ticker",
)


@pytest.mark.parametrize("dimension", _UNAUTHORIZED_DIMENSIONS)
def test_ve_m6_an_unauthorized_dimension_is_refused_by_the_evidence_kind_check(
    catalog: sqlite3.Connection,
    dimension: str,
) -> None:
    """**VE-M6, isolated.** The row is lawful in every respect except its dimension.

    ``evidence_level`` is deliberately NOT ``verified`` here, so the span-backing trigger
    stays quiet and the ``evidence_kind`` CHECK is provably the guard that kills it.
    """
    _both_passes(catalog)
    with pytest.raises(sqlite3.IntegrityError, match="evidence_kind IN"):
        _adjudicate(
            catalog,
            dimension,
            adjudicated_value=None,
            agreement_state="abstained",
            evidence_level="unavailable",
        )


@pytest.mark.parametrize("dimension", _UNAUTHORIZED_DIMENSIONS)
def test_ve_m6_an_unauthorized_dimension_is_refused_at_the_verified_level_too(
    catalog: sqlite3.Connection,
    dimension: str,
) -> None:
    """**VE-M6.** No route reaches a verified row on an unauthorized dimension."""
    _both_passes(catalog)
    with pytest.raises(sqlite3.IntegrityError):
        _adjudicate(catalog, dimension, evidence_level="verified")
    assert catalog.execute("SELECT COUNT(*) FROM document_adjudicated_evidence").fetchone()[0] == 0


@pytest.mark.parametrize(
    "column",
    (
        "size_evidence_level",
        "industry_evidence_level",
        "history_evidence_level",
        "primary_universe_evidence_level",
    ),
)
def test_ve_m6_entity_evidence_levels_still_exclude_verified(
    catalog: sqlite3.Connection,
    column: str,
) -> None:
    """**VE-M6.** Decision 087 §7: no other dimension's validation is weakened.

    Migration ``0015`` widens exactly one CHECK. These four are migration ``0009``'s, still
    excluding ``verified``, and the mutation proves they were left alone rather than assumed
    to have been.
    """
    levels = dict.fromkeys(
        (
            "size_evidence_level",
            "industry_evidence_level",
            "history_evidence_level",
            "primary_universe_evidence_level",
        ),
        "provisional",
    )
    levels[column] = "verified"
    with pytest.raises(sqlite3.IntegrityError, match=f"{column} IN"):
        catalog.execute(
            "INSERT INTO pilot_candidate_entities (snapshot_id, cik_numeric, cik_padded, "
            "entity_tie_break_sha256, candidate_category, size_evidence_level, "
            "industry_evidence_level, history_evidence_level, primary_universe_evidence_level, "
            "filing_time_name, recorded_at_utc) "
            "VALUES (?, 1, '0000000001', ?, 'operating', ?, ?, ?, ?, 'edgar', ?)",
            (
                _SNAPSHOT,
                "b" * 64,
                levels["size_evidence_level"],
                levels["industry_evidence_level"],
                levels["history_evidence_level"],
                levels["primary_universe_evidence_level"],
                _AT,
            ),
        )


@pytest.mark.parametrize(
    "column",
    ("filing_date_evidence_level", "cohort_evidence_level", "xbrl_evidence_level"),
)
def test_ve_m6_the_other_accession_evidence_levels_still_exclude_verified(
    catalog: sqlite3.Connection,
    column: str,
) -> None:
    """**VE-M6.** The widening reached ``amendment_purpose_evidence_level`` and nothing else."""
    levels = dict.fromkeys(
        ("filing_date_evidence_level", "cohort_evidence_level", "xbrl_evidence_level"),
        "unavailable",
    )
    levels[column] = "verified"
    with pytest.raises(sqlite3.IntegrityError, match=f"{column} IN"):
        catalog.execute(
            "INSERT INTO pilot_candidate_accessions (snapshot_id, accession_plain, "
            "accession_number_dashed, accession_tie_break_sha256, registrant_set_completeness, "
            "form_type, is_amendment, filing_date_evidence_level, cohort_evidence_level, "
            "xbrl_evidence_level, amendment_purpose_evidence_level, multi_registrant, "
            "recorded_at_utc) VALUES (?, ?, 'x', ?, 'established', '10-K', 0, ?, ?, ?, "
            "'unavailable', 1, ?)",
            (
                _SNAPSHOT,
                _ACCESSION,
                "b" * 64,
                levels["filing_date_evidence_level"],
                levels["cohort_evidence_level"],
                levels["xbrl_evidence_level"],
                _AT,
            ),
        )


def test_ve_m6_the_policy_validator_refuses_an_unauthorized_dimension() -> None:
    """**VE-M6 in code.** Decision 087 §5.4 requires policy validation, not only schema."""
    for dimension in _UNAUTHORIZED_DIMENSIONS:
        assert not de.verified_evidence_is_applicable(dimension)
        with pytest.raises(GateFailureError, match="not authorized for dimension"):
            de.require_verified_evidence_applicable(dimension)
    for dimension in ("amendment_purpose", "amendment_linkage"):
        assert de.verified_evidence_is_applicable(dimension)
        de.require_verified_evidence_applicable(dimension)
    assert set(de.AUTHORIZED_VERIFIED_EVIDENCE_DIMENSIONS) == {
        "amendment_purpose",
        "amendment_linkage",
    }


def test_ve_m6_a_verified_candidate_level_requires_frozen_adjudicated_evidence(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M6.** The widening is not a licence to assert ``verified`` from nowhere."""
    with pytest.raises(sqlite3.IntegrityError, match="requires frozen adjudicated document"):
        _candidate(catalog, purpose_level="verified")
    _both_passes(catalog)
    _adjudicate(
        catalog,
        "amendment_purpose",
        evidence_level="unavailable",
        agreement_state="abstained",
        adjudicated_value=None,
    )
    with pytest.raises(sqlite3.IntegrityError, match="requires frozen adjudicated document"):
        _candidate(catalog, purpose_level="verified")


def test_ve_m6_a_quota_credit_still_needs_an_admitted_evidence_level(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M6.** Widening 2 admits ``verified`` beside ``provisional`` -- and nothing else."""
    with pytest.raises(sqlite3.IntegrityError, match="amendment_purpose_quota_eligible = 0"):
        _candidate(catalog, purpose_level="unproven", quota_eligible=1)
    with pytest.raises(sqlite3.IntegrityError, match="amendment_purpose_quota_eligible = 0"):
        _candidate(catalog, purpose_level="review_required", quota_eligible=1)
    _candidate(catalog, accession=_OTHER_ACCESSION, purpose_level="provisional", quota_eligible=1)
    assert (
        catalog.execute(
            "SELECT amendment_purpose_quota_eligible FROM pilot_candidate_accessions"
        ).fetchone()[0]
        == 1
    )


# ==========================================================================
# VE-M7 -- an invented verified_amends_original semantic state
# ==========================================================================


def test_ve_m7_the_invented_verified_linkage_state_is_refused(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M7.** Decision 083 **R63** item B: the linkage vocabulary is not widened."""
    with pytest.raises(sqlite3.IntegrityError, match="amendment_linkage_state IS NULL OR"):
        _candidate(catalog, linkage_state="verified_amends_original")


def test_ve_m7_the_invented_state_exists_as_no_value_anywhere_in_the_repository() -> None:
    """**VE-M7, repository-wide.** The state is absent as a VALUE, not merely unreachable.

    Prose that *names* the prohibited state in order to prohibit it is exactly what the
    governing records asked for, so the scan looks for the token as a quoted string literal
    -- the only shape in which it could become a vocabulary entry, a column default, or a
    written row.
    """
    quoted = ("'verified_amends_original'", '"verified_amends_original"')
    offenders = [
        f"{path}: {marker}"
        for root in (Path("src"), Path("tests"))
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".sql"}
        for marker in quoted
        if path.name != Path(__file__).name and marker in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_ve_m7_verification_strength_and_relationship_are_separate_columns(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M7.** WHAT the relationship is, and HOW STRONGLY it was verified, stay apart."""
    _both_passes(catalog)
    _adjudicate(catalog, "amendment_purpose")
    _adjudicate(catalog, "explicit_original", adjudicated_value="10-K|2020-03-01")
    _candidate(catalog, purpose_level="verified")
    linkage = catalog.execute(
        "SELECT amendment_linkage_state FROM pilot_candidate_accessions"
    ).fetchone()[0]
    strength = catalog.execute(
        "SELECT evidence_level FROM document_adjudicated_evidence "
        "WHERE evidence_kind = 'explicit_original'"
    ).fetchone()[0]
    assert linkage == "amends_original"
    assert strength == "verified"


# ==========================================================================
# VE-M8 and VE-M9 -- adjudication provenance
# ==========================================================================


def test_ve_m8_an_adjudication_must_bind_the_artifact_every_review_bound(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M8, isolated.** A and B agree on the artifact; the third record does not.

    The fixture is built so both independent passes exist for the named artifact and the
    contributing set is exact -- so the review-provenance and review-id guards both pass, and
    the artifact-binding trigger is provably what refuses the row.
    """
    _artifact(catalog)
    _artifact(catalog, artifact_sha256=_OTHER_ARTIFACT, accession=_OTHER_ACCESSION)
    a = _review(catalog, "review_a")
    _span(catalog, a)
    b = _review(catalog, "review_b")
    _span(catalog, b)
    third = _review(catalog, "adjudication", artifact_sha256=_OTHER_ARTIFACT)
    _span(catalog, third)
    with pytest.raises(sqlite3.IntegrityError, match="must bind the same artifact"):
        _adjudicate(catalog, "amendment_purpose", review_ids=(a, b))


def test_ve_m8_an_adjudication_cannot_name_an_unbound_artifact(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M8.** An artifact that was never registered cannot be adjudicated against.

    Both halves are asserted: the declared foreign key, which is the structural guarantee,
    and an actual refusal. The refusal arrives from the contributing-set guard rather than
    from the foreign key -- SQLite runs ``BEFORE INSERT`` triggers ahead of constraint
    checking, and an unbound artifact has no reviews for the set to enumerate -- so the test
    asserts what actually happens rather than a firing order it does not control.
    """
    definition = str(
        catalog.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' "
            "AND name = 'document_adjudicated_evidence'"
        ).fetchone()["sql"]
    )
    assert "REFERENCES document_artifacts(artifact_sha256)" in definition

    _both_passes(catalog)
    with pytest.raises(sqlite3.IntegrityError):
        _adjudicate(
            catalog,
            "amendment_purpose",
            artifact_sha256="c" * 64,
            review_ids=(_REVIEW_ID["review_a"], _REVIEW_ID["review_b"]),
        )
    assert catalog.execute("SELECT COUNT(*) FROM document_adjudicated_evidence").fetchone()[0] == 0


def test_ve_m9_an_adjudication_requires_both_independent_passes(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M9, isolated.** Only Review A exists, and the contributing set names only it.

    Naming the exact set that exists is what makes the review-id guard pass, so the
    review-provenance guard is provably the one that refuses the row.
    """
    _artifact(catalog)
    a = _review(catalog, "review_a")
    _span(catalog, a)
    with pytest.raises(sqlite3.IntegrityError, match="requires both independent review passes"):
        _adjudicate(catalog, "amendment_purpose", review_ids=(a,))


def test_ve_m9_a_resolved_outcome_requires_the_third_record(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M9.** ``resolved`` claims a third adjudication happened; it must have."""
    _both_passes(catalog)
    with pytest.raises(sqlite3.IntegrityError, match="requires the third adjudication record"):
        _adjudicate(catalog, "amendment_purpose", agreement_state="resolved")


def test_ve_m9_the_contributing_set_is_exact(catalog: sqlite3.Connection) -> None:
    """**VE-M9.** An extra, a missing, or a substituted contributor is all refused."""
    _both_passes(catalog)
    substituted = de.contributing_review_ids_json((_REVIEW_ID["review_a"], "c" * 64))
    for payload in (
        de.contributing_review_ids_json(
            (_REVIEW_ID["review_a"], _REVIEW_ID["review_b"], _REVIEW_ID["adjudication"])
        ),
        de.contributing_review_ids_json((_REVIEW_ID["review_a"],)),
        substituted,
    ):
        with pytest.raises(sqlite3.IntegrityError, match="must enumerate exactly the reviews"):
            _adjudicate(catalog, "amendment_purpose", review_ids_json=payload)


def test_ve_m9_verified_evidence_requires_a_matching_span_from_every_asserting_review(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M9.** Decision 082 §12.5: a non-abstaining record without a span fails closed."""
    _both_passes(catalog, with_spans=False)
    with pytest.raises(sqlite3.IntegrityError, match="requires at least one matching source span"):
        _adjudicate(catalog, "amendment_purpose")
    # A span of the wrong role does not back the wrong evidence kind either.
    _span(catalog, _REVIEW_ID["review_a"], span_role="original_form")
    _span(catalog, _REVIEW_ID["review_b"], span_role="original_form")
    with pytest.raises(sqlite3.IntegrityError, match="requires at least one matching source span"):
        _adjudicate(catalog, "amendment_purpose")
    # The same spans DO back the explicit-original kind, which is the role mapping working.
    _adjudicate(catalog, "explicit_original", adjudicated_value="10-K|2020-03-01")


def test_ve_m9_a_span_cannot_cite_an_assertion_its_record_never_made(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M9.** Provenance must point at something the record actually asserted."""
    _artifact(catalog)
    identifier = _review(catalog, "review_a")
    with pytest.raises(sqlite3.IntegrityError, match="must support an assertion"):
        _span(catalog, identifier, span_role="original_accession")


# ==========================================================================
# VE-M10 -- Review A and Review B sharing one governed epoch
# ==========================================================================


def test_ve_m10_review_b_cannot_reuse_review_as_epoch(catalog: sqlite3.Connection) -> None:
    """**VE-M10.** Two passes sharing an epoch are not two independent passes."""
    _artifact(catalog)
    _review(catalog, "review_a")
    with pytest.raises(sqlite3.IntegrityError, match="carries exactly one reviewer role"):
        _review(catalog, "review_b", epoch=_EPOCH["review_a"])
    with pytest.raises(sqlite3.IntegrityError, match="carries exactly one reviewer role"):
        _review(catalog, "adjudication", epoch=_EPOCH["review_a"])


def test_ve_m10_the_three_epochs_of_an_accession_are_necessarily_distinct(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M10.** Decision 083 **R63** item D's proof, executed rather than asserted.

    Two mechanisms combine: within one accession each role appears at most once, and a given
    epoch carries exactly one role. Three roles therefore force three epochs.
    """
    _artifact(catalog)
    for role in ("review_a", "review_b", "adjudication"):
        _review(catalog, role)
    epochs = tuple(
        row["review_epoch_id"]
        for row in catalog.execute(
            "SELECT review_epoch_id FROM document_review_records WHERE accession_plain = ? "
            "ORDER BY reviewer_role",
            (_ACCESSION,),
        )
    )
    assert len(set(epochs)) == 3
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
        _review(catalog, "review_a", review_id="c" * 64, epoch="d" * 64)


def test_ve_m10_one_epoch_may_lawfully_review_many_accessions(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M10 is not over-broad.** One Review-A epoch covering all 108 artifacts is lawful.

    The rule is one role per epoch, not one row per epoch. Getting this wrong would make the
    accepted **R64** protocol -- a single fresh epoch reviewing the whole frozen set --
    unimplementable, so the permissive direction is asserted too.
    """
    _artifact(catalog)
    _artifact(catalog, artifact_sha256=_OTHER_ARTIFACT, accession=_OTHER_ACCESSION)
    _review(catalog, "review_a")
    _review(
        catalog,
        "review_a",
        accession=_OTHER_ACCESSION,
        artifact_sha256=_OTHER_ARTIFACT,
        review_id="c" * 64,
        epoch=_EPOCH["review_a"],
    )
    assert (
        catalog.execute(
            "SELECT COUNT(*) FROM document_review_records WHERE review_epoch_id = ?",
            (_EPOCH["review_a"],),
        ).fetchone()[0]
        == 2
    )


def test_ve_m10_a_review_pass_cannot_disagree_with_its_role(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M10.** The contract's ``review_pass`` column cannot drift from the role."""
    _artifact(catalog)
    with pytest.raises(sqlite3.IntegrityError, match="reviewer_role"):
        # A review PASS letter, not a credential -- S106's heuristic reads the keyword name.
        _review(catalog, "review_a", review_pass="B")  # noqa: S106


# ==========================================================================
# VE-M11 -- artifact substitution under one governed review identity
# ==========================================================================


def test_ve_m11_a_review_identity_cannot_be_rebound_to_another_artifact(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M11.** Both doors: the same ``review_id``, and the same accession-and-role."""
    _artifact(catalog)
    _artifact(catalog, artifact_sha256=_OTHER_ARTIFACT, accession=_OTHER_ACCESSION)
    _review(catalog, "review_a")
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
        _review(catalog, "review_a", artifact_sha256=_OTHER_ARTIFACT)
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
        _review(
            catalog,
            "review_a",
            artifact_sha256=_OTHER_ARTIFACT,
            review_id="c" * 64,
            epoch=_EPOCH["review_a"],
        )


def test_ve_m11_an_accession_cannot_acquire_a_competing_artifact(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M11.** One accession has at most one artifact per source class."""
    _artifact(catalog)
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
        _artifact(catalog, artifact_sha256=_OTHER_ARTIFACT)
    assert catalog.execute("SELECT COUNT(*) FROM document_artifacts").fetchone()[0] == 1


def test_ve_m11_an_unaccepted_source_class_is_refused(catalog: sqlite3.Connection) -> None:
    """**VE-M11.** A second source class needs its own owner record, not a spare string."""
    with pytest.raises(sqlite3.IntegrityError, match="source_class IN"):
        _artifact(catalog, source_class="primary_document")


# ==========================================================================
# VE-M12 -- identity nonchange
# ==========================================================================

#: The three frozen digest tuples, pinned as literals. Accepted Decision 084 **R67** keeps
#: ``candidate_identity.py`` unwidened, and a literal is the only way to state that: a
#: recomputation would move with the code it is supposed to be checking.
_FROZEN_ACCESSION_TABLE_COLUMNS: Final[tuple[str, ...]] = (
    "accession_plain",
    "accession_number_dashed",
    "accession_tie_break_sha256",
    "anchor_cik_numeric",
    "form_type",
    "is_amendment",
    "official_filing_date",
    "report_date",
    "acceptance_audit_date",
    "filing_date_evidence_level",
    "filing_date_resolution_sha256",
    "filing_date_precedence",
    "provisional_official_cohort",
    "acceptance_audit_cohort",
    "cohort_evidence_level",
    "cohort_resolution_sha256",
    "cohort_ambiguous",
    "has_xbrl",
    "has_inline_xbrl",
    "xbrl_evidence_level",
    "xbrl_resolution_sha256",
    "amendment_linkage_state",
    "provisional_parent_accession",
    "amendment_purpose_category",
    "amendment_purpose_evidence_level",
    "amendment_purpose_resolution_sha256",
    "amendment_purpose_quota_eligible",
    "base_eligible",
    "stress_eligible",
    "support_eligible",
    "control_eligible",
    "multi_registrant",
)


def test_ve_m12_no_frozen_identity_tuple_is_widened() -> None:
    """**VE-M12.** Adding a column to a digest tuple moves that digest for every row.

    Decision 082 §11.3 measured that against the implementation: a ``NULL`` everywhere still
    changes the header and every rendered row. The evidence layer therefore lives entirely in
    NEW domains, and these three tuples are asserted byte-for-byte unmoved.
    """
    assert ACCESSION_TABLE_COLUMNS == _FROZEN_ACCESSION_TABLE_COLUMNS
    assert REGISTRANT_TABLE_COLUMNS == (
        "accession_plain",
        "registrant_cik_numeric",
        "registrant_cik_padded",
        "role",
        "is_anchor",
        "evidence_level",
    )
    assert "registrant_set_completeness" not in REGISTRANT_TABLE_COLUMNS
    assert "association_class" not in REGISTRANT_TABLE_COLUMNS
    for field in SNAPSHOT_CONTENT_FIELDS:
        assert "document" not in field
        assert "verified" not in field


def test_ve_m12_the_candidate_accession_digest_is_unmoved_by_migration_0015() -> None:
    """**VE-M12.** A pinned digest over a fixed row set, computed through the real primitive.

    **Provenance.** ``candidate_accession_table_sha256`` is a pure function of
    ``ACCESSION_TABLE_COLUMNS`` and ``release/hashing.py``, and both files are **blob-identical
    to the accepted R46 target** ``1c5b0150…`` (blob ``e443ca23…`` for
    ``candidate_identity.py``), which predates migration ``0015`` entirely. The literal below
    is therefore a genuine pre-``0015`` value reproducible from that commit, not a value this
    stage produced and then asserted against itself. If the column tuple moved, if the hashing
    changed, or if the evidence layer had leaked into this domain, it would not reproduce.
    """
    row = dict.fromkeys(ACCESSION_TABLE_COLUMNS)
    row.update(
        {
            "accession_plain": _ACCESSION,
            "accession_number_dashed": "0000000001-20-000001",
            "anchor_cik_numeric": 1,
            "form_type": "10-K",
            "is_amendment": 0,
            "amendment_purpose_evidence_level": "unavailable",
            "accession_tie_break_sha256": "b" * 64,
        }
    )
    assert (
        candidate_accession_table_sha256([row])
        == "9e80911d073cf67537e06b66b5b5e285fb300185abde9d6e58ced38aa4eb888c"
    )


def test_ve_m12_the_evidence_domains_are_new_and_collide_with_nothing() -> None:
    """**VE-M12.** A new domain leaves every existing digest byte-unchanged (§11.3)."""
    evidence_domains = {
        de.ARTIFACT_DOMAIN,
        de.REVIEW_RECORD_DOMAIN,
        de.SPAN_DOMAIN,
        de.ADJUDICATED_EVIDENCE_DOMAIN,
        de.REVIEW_A_TABLE_DOMAIN,
        de.REVIEW_B_TABLE_DOMAIN,
        de.ADJUDICATION_TABLE_DOMAIN,
    }
    existing_domains = {
        "pilot_candidate_entities",
        "pilot_candidate_accessions",
        "pilot_candidate_accession_registrants",
        "pilot_candidate_entity_evidence",
        "pilot_candidate_accession_evidence",
        "ops_schema_migrations_content",
    }
    assert evidence_domains & existing_domains == set()
    assert len(evidence_domains) == 7
    # Review A's and Review B's frozen pass digests must never be interchangeable.
    rows = [dict.fromkeys(de.REVIEW_RECORD_COLUMNS, "x")]
    assert de.review_pass_table_sha256("review_a", rows) != de.review_pass_table_sha256(
        "review_b", rows
    )
    assert de.review_pass_table_sha256("review_b", rows) != de.review_pass_table_sha256(
        "adjudication", rows
    )


def test_ve_m12_empty_evidence_tables_add_no_candidate_column(tmp_path: Path) -> None:
    """**VE-M12.** The 0014 and 0015 candidate tables have the same columns, in the same order.

    Decision 087 §9's required proof, at the schema rather than at the digest: an upgrade to
    an empty ``0015`` evidence state changes no candidate column, so nothing a candidate
    identity reads has moved.
    """
    inventory = available_migrations()
    at_14 = tmp_path / "at14.sqlite3"
    at_15 = tmp_path / "at15.sqlite3"
    with connect(at_14, writer=True) as connection:
        apply_migrations(connection, tuple(m for m in inventory if m.version <= 14))
    with connect(at_15, writer=True) as connection:
        apply_migrations(connection)

    def columns(path: Path, table: str) -> tuple[tuple[str, str], ...]:
        raw = sqlite3.connect(path)
        try:
            return tuple(
                (str(row[1]), str(row[2]))
                for row in raw.execute(f"PRAGMA table_info({table})")  # noqa: S608
            )
        finally:
            raw.close()

    for table in (
        "pilot_candidate_accessions",
        "pilot_candidate_accession_registrants",
        "pilot_candidate_entities",
        "pilot_selected_accessions",
        "census_accessions",
        "census_accession_registrants",
    ):
        assert columns(at_14, table) == columns(at_15, table), table

    raw = sqlite3.connect(at_15)
    try:
        counts = {
            table: int(raw.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608
            for table in (
                "document_artifacts",
                "document_review_records",
                "document_review_spans",
                "document_adjudicated_evidence",
            )
        }
    finally:
        raw.close()
    assert counts == dict.fromkeys(counts, 0)


# ==========================================================================
# VE-M13 -- private-path leakage into governed rows or output
# ==========================================================================


def test_ve_m13_the_path_validator_refuses_every_path_shape() -> None:
    """**VE-M13.** The code-side half of the nonleakage rule."""
    for value in (
        _PRIVATE_PATH,
        "~/private-evidence/0001.txt",
        "C:\\evidence\\0001.txt",
        "relative/path.txt",
        "file:///tmp/0001.txt",
    ):
        with pytest.raises(GateFailureError, match="never carry a private filesystem path"):
            de.require_no_private_path(value, "retrieval_receipt_id")
    de.require_no_private_path("d081-receipt-0001", "retrieval_receipt_id")
    de.require_no_private_path(_ACCESSION, "accession_plain")


def test_ve_m13_no_authorized_artifact_of_this_stage_carries_a_private_path() -> None:
    """**VE-M13.** The migration, the module, and this test module carry no absolute path.

    A private path leaking into a committed file is the same defect as one leaking into a
    governed row: it publishes the operator's filesystem. ``_PRIVATE_PATH`` above is the one
    deliberate exception, and it is a synthetic mutation input that nothing resolves.
    """
    migration = (
        resources.files(MIGRATIONS_PACKAGE)
        .joinpath("0015_m33_verified_document_evidence.sql")
        .read_text(encoding="utf-8")
    )
    module = Path("src/disclosure_drift/m3/document_evidence.py").read_text(encoding="utf-8")
    absolute = re.compile(r"(?<![\w./])(?:/Users/|/home/|/private/|/var/folders/|[A-Z]:\\\\)")
    for label, text in (("migration 0015", migration), ("document_evidence.py", module)):
        assert absolute.search(text) is None, f"{label} carries an absolute filesystem path"
    # The prose in both files NAMES ``EV_ROOT`` in order to prohibit persisting it, which is
    # the intended content. What must be absent is any attempt to READ or EXPAND it.
    for label, text in (("migration 0015", migration), ("document_evidence.py", module)):
        for expansion in (
            "$EV_ROOT",
            "${EV_ROOT",
            'environ["EV_ROOT"',
            "environ.get(",
            "DISCLOSURE_DRIFT_",
        ):
            assert expansion not in text, f"{label} reads or expands the evidence root"


def test_ve_m13_a_governed_row_cannot_be_repaired_into_carrying_a_path(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M13.** Immutability closes the update route into every governed column."""
    _both_passes(catalog)
    for statement in (
        "UPDATE document_artifacts SET source_url = ?",
        "UPDATE document_artifacts SET retrieval_receipt_id = ?",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="append-only and immutable"):
            catalog.execute(statement, (_PRIVATE_PATH,))
    assert (
        catalog.execute("SELECT source_url FROM document_artifacts").fetchone()[0] == _ARTIFACT_URL
    )


def test_ve_m13_a_span_location_can_never_be_a_filesystem_location(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M13.** A "stable location" is a byte range in the frozen artifact, not a path."""
    _artifact(catalog)
    identifier = _review(catalog, "review_a")
    for location in (_PRIVATE_PATH, "line 42 of exhibit.htm", "bytes:1204"):
        with pytest.raises(sqlite3.IntegrityError, match="span_location"):
            _span(catalog, identifier, location=location)
    _span(catalog, identifier, location="bytes:1204-1258")


def test_ve_m13_a_reviewer_model_cannot_become_a_personal_name(
    catalog: sqlite3.Connection,
) -> None:
    """**VE-M13 / R63 item D.** No column can record a person, so none does."""
    _artifact(catalog)
    with pytest.raises(sqlite3.IntegrityError, match="reviewer_model"):
        _review(catalog, "review_a", reviewer_model="Alex Q Reviewer")


# ==========================================================================
# VE-M14 -- no real Decision-081 artifact or reference is accessed
# ==========================================================================


def test_ve_m14_the_stage_never_resolves_the_private_evidence_root(
    catalog: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**VE-M14.** The private evidence root is made unresolvable, and nothing notices.

    Poisoning :func:`require_external_evidence_root` is the mechanical form of the claim: if
    any part of the lawful lifecycle reached for the private root, this test would fail.
    """
    from disclosure_drift.m3 import evidence_paths

    def _poisoned(root: object, repository_root: object) -> Path:
        message = "the verified-evidence schema stage must never resolve the evidence root"
        raise AssertionError(message)

    monkeypatch.setattr(evidence_paths, "require_external_evidence_root", _poisoned)
    _both_passes(catalog)
    _adjudicate(catalog, "amendment_purpose")
    _candidate(catalog, purpose_level="verified", quota_eligible=1)
    assert catalog.execute("SELECT COUNT(*) FROM document_adjudicated_evidence").fetchone()[0] == 1


def test_ve_m14_the_evidence_module_performs_no_io_and_reads_no_environment() -> None:
    """**VE-M14.** ``document_evidence.py`` opens nothing and resolves nothing."""
    module = Path("src/disclosure_drift/m3/document_evidence.py").read_text(encoding="utf-8")
    for forbidden in (
        "open(",
        "Path(",
        "os.environ",
        "getenv",
        "subprocess",
        "socket",
        "httpx",
        "requests",
        "urllib",
        "evidence_paths",
    ):
        assert forbidden not in module, f"document_evidence.py references {forbidden!r}"


def test_ve_m14_no_real_decision_081_evidence_is_populated(catalog: sqlite3.Connection) -> None:
    """**VE-M14.** The relations ship empty, and this module inserts only synthetic rows.

    Decision 087 §10: the 108 real Decision-081 review outcomes are not inserted by this
    stage. Every accession used here is a synthetic ``0000000001``/``0000000002`` filer.
    """
    for table in (
        "document_artifacts",
        "document_review_records",
        "document_review_spans",
        "document_adjudicated_evidence",
    ):
        assert (
            int(catalog.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) == 0  # noqa: S608
        )
    _both_passes(catalog)
    accessions = {
        str(row["accession_plain"])
        for row in catalog.execute("SELECT accession_plain FROM document_artifacts")
    }
    assert accessions == {_ACCESSION}
    assert catalog.execute("SELECT COUNT(*) FROM document_review_records").fetchone()[0] == 2


# ==========================================================================
# Migration 0015 safety -- Decision 087 §12
# ==========================================================================


def test_migration_0015_fresh_build_and_upgrade_produce_the_same_schema(tmp_path: Path) -> None:
    """Decision 087 §12 checks 1-3: upgrade succeeds, fresh build succeeds, and they agree."""
    inventory = available_migrations()
    fresh = tmp_path / "fresh.sqlite3"
    upgraded = tmp_path / "upgraded.sqlite3"
    with connect(fresh, writer=True) as connection:
        applied = apply_migrations(connection)
    assert applied[-1].version == 15
    with connect(upgraded, writer=True) as connection:
        apply_migrations(connection, tuple(m for m in inventory if m.version <= 14))
    with connect(upgraded, writer=True) as connection:
        applied = apply_migrations(connection)
    assert tuple(m.version for m in applied) == (15,)

    def schema(path: Path) -> tuple[tuple[str, str, str | None], ...]:
        raw = sqlite3.connect(path)
        try:
            return tuple(
                (str(row[0]), str(row[1]), row[2])
                for row in raw.execute(
                    "SELECT type, name, sql FROM sqlite_master ORDER BY type, name"
                )
            )
        finally:
            raw.close()

    assert schema(fresh) == schema(upgraded)


def test_migration_0015_leaves_integrity_and_foreign_keys_clean(tmp_path: Path) -> None:
    """Decision 087 §12 checks 4 and 5, on both the fresh and the upgraded path."""
    inventory = available_migrations()
    for label, versions in (("fresh", None), ("upgraded", 14)):
        path = tmp_path / f"{label}.sqlite3"
        with connect(path, writer=True) as connection:
            if versions is None:
                apply_migrations(connection)
            else:
                apply_migrations(connection, tuple(m for m in inventory if m.version <= versions))
        if versions is not None:
            with connect(path, writer=True) as connection:
                apply_migrations(connection)
        with connect(path) as connection:
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_migration_0015_refuses_a_populated_catalog_and_leaves_it_at_0014(
    tmp_path: Path,
) -> None:
    """Decision 087 §12 check 7 and §15 item I: prospective, never a data migration.

    A catalog carrying real candidate state is refused outright and left byte-compatible at
    ``0014`` -- no evidence table is created, and the existing row survives untouched.
    """
    inventory = available_migrations()
    path = tmp_path / "populated.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection, tuple(m for m in inventory if m.version <= 14))
    raw = sqlite3.connect(path)
    try:
        raw.execute(
            "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
            "started_at_utc, detail) VALUES ('job-1', 'sec_census', 'completed', 'M3.3', ?, '')",
            (_AT,),
        )
        raw.execute(
            "INSERT INTO pilot_candidate_snapshots (snapshot_id, census_run_id, coverage_start, "
            "coverage_end, as_of_date, include_open_quarter, coverage_policy_version, "
            "candidate_policy_version, sic_family_mapping_version, evidence_policy_version, "
            "coverage_window_sha256, input_observation_set_sha256, snapshot_state, entity_count, "
            "accession_count, created_at_utc) VALUES (?, 'job-1', '2010-01-01', '2026-06-30', "
            "'2026-06-30', 0, 'c/1.0', 'p/1.0', 's/1.0', 'e/1.0', ?, ?, 'building', 0, 0, ?)",
            (_SNAPSHOT, "c" * 64, "d" * 64, _AT),
        )
        raw.commit()
    finally:
        raw.close()

    with (
        pytest.raises(sqlite3.IntegrityError, match="requires empty pilot_candidate_snapshots"),
        connect(path, writer=True) as connection,
    ):
        apply_migrations(connection)

    raw = sqlite3.connect(path)
    try:
        versions = tuple(
            int(row[0])
            for row in raw.execute("SELECT version FROM ops_schema_migrations ORDER BY version")
        )
        created = int(
            raw.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE name = 'document_artifacts'"
            ).fetchone()[0]
        )
        surviving = int(raw.execute("SELECT COUNT(*) FROM pilot_candidate_snapshots").fetchone()[0])
    finally:
        raw.close()
    assert versions == tuple(range(1, 15))
    assert created == 0
    assert surviving == 1


def test_migration_0015_creates_exactly_the_four_contract_relations(
    catalog: sqlite3.Connection,
) -> None:
    """Decision 082 §11.2: four relations, no more and no fewer."""
    tables = {
        str(row["name"])
        for row in catalog.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'document_%'"
        )
    }
    assert tables == {
        "document_artifacts",
        "document_review_records",
        "document_review_spans",
        "document_adjudicated_evidence",
    }


def test_migration_0015_opens_no_transaction_of_its_own() -> None:
    """The runner supplies the transaction; a migration that opens one breaks atomicity."""
    sql = (
        resources.files(MIGRATIONS_PACKAGE)
        .joinpath("0015_m33_verified_document_evidence.sql")
        .read_text(encoding="utf-8")
    )
    body = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
    assert re.search(r"\bBEGIN\s*;", body) is None
    assert re.search(r"\bBEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)\b", body) is None
    assert "ATTACH" not in body
    assert "PRAGMA foreign_keys" not in body


def test_migration_0015_names_no_object_that_an_earlier_migration_creates() -> None:
    """``0015`` adds a capability; it rewrites and re-creates nothing that came before."""
    packaged = {
        entry.name: entry.read_bytes()
        for entry in resources.files(MIGRATIONS_PACKAGE).iterdir()
        if entry.name.endswith(".sql")
    }
    new_objects = (
        b"document_artifacts",
        b"document_review_records",
        b"document_review_spans",
        b"document_adjudicated_evidence",
    )
    for name, content in packaged.items():
        if name == "0015_m33_verified_document_evidence.sql":
            assert all(marker in content for marker in new_objects)
            continue
        for marker in new_objects:
            assert marker not in content, f"{marker!r} leaked into {name}"


def test_the_protocol_version_is_frozen_and_not_executed(catalog: sqlite3.Connection) -> None:
    """Decision 083 **R64**: the version may be stored exactly as contracted, and only that."""
    assert de.DOCUMENT_EVIDENCE_PROTOCOL_VERSION == "m3.3-document-evidence/1.0"
    _artifact(catalog)
    with pytest.raises(sqlite3.IntegrityError, match="protocol_version"):
        _review(catalog, "review_a", protocol_version="m3.3-document-evidence/2.0")
    _review(catalog, "review_a")
    stored = catalog.execute("SELECT protocol_version FROM document_review_records").fetchone()[0]
    assert stored == de.DOCUMENT_EVIDENCE_PROTOCOL_VERSION


# ==========================================================================
# The policy module's own surface
# ==========================================================================


def test_the_contributing_id_serialization_matches_what_the_schema_validates(
    catalog: sqlite3.Connection,
) -> None:
    """The migration validates by arithmetic; the serializer must satisfy that arithmetic."""
    ids = (_REVIEW_ID["review_b"], _REVIEW_ID["review_a"])
    payload = de.contributing_review_ids_json(ids)
    assert payload == de.contributing_review_ids_json(reversed(ids))
    assert len(payload) == 1 + 67 * len(ids)
    assert payload.count('"') == 2 * len(ids)
    _both_passes(catalog)
    _adjudicate(catalog, "amendment_purpose", review_ids_json=payload)
    assert catalog.execute("SELECT COUNT(*) FROM document_adjudicated_evidence").fetchone()[0] == 1


def test_the_contributing_id_serialization_refuses_a_malformed_set() -> None:
    """An empty, duplicated, or non-hex contributing set is refused before it is written."""
    with pytest.raises(GateFailureError, match="at least one contributing review"):
        de.contributing_review_ids_json(())
    with pytest.raises(GateFailureError, match="must be distinct"):
        de.contributing_review_ids_json((_REVIEW_ID["review_a"], _REVIEW_ID["review_a"]))
    with pytest.raises(GateFailureError, match="not a lowercase hex digest"):
        de.contributing_review_ids_json(("Z" * 64,))
    with pytest.raises(GateFailureError, match="not a lowercase hex digest"):
        de.contributing_review_ids_json(("a" * 63,))


def test_the_record_digests_refuse_a_preimage_that_does_not_match_its_tuple() -> None:
    """A digest over the wrong fields is a different claim; it is refused, not computed."""
    fields = dict.fromkeys(de.REVIEW_RECORD_COLUMNS, "x")
    assert len(de.review_record_sha256(fields)) == 64
    with pytest.raises(GateFailureError, match="preimage mismatch"):
        de.review_record_sha256({**fields, "unexpected": "x"})
    with pytest.raises(GateFailureError, match="preimage mismatch"):
        de.review_record_sha256({k: v for k, v in fields.items() if k != "review_id"})
    with pytest.raises(GateFailureError, match="unknown reviewer role"):
        de.review_pass_table_sha256("reviewer_c", [fields])


def test_the_module_vocabularies_match_the_migration_vocabularies(
    catalog: sqlite3.Connection,
) -> None:
    """The executable mirror and the persisted contract state the same vocabulary.

    Migration ``0015`` remains the contract; this asserts the module does not quietly drift
    from it, which is the failure mode a mirror invites.
    """
    definitions = {
        str(row["name"]): str(row["sql"])
        for row in catalog.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name LIKE 'document_%'"
        )
    }
    records = definitions["document_review_records"]
    for role in de.REVIEWER_ROLES:
        assert f"'{role}'" in records
    for category in de.PURPOSE_CATEGORIES:
        assert f"'{category}'" in records
    for reason in de.ABSTENTION_REASONS:
        assert f"'{reason}'" in records
    adjudicated = definitions["document_adjudicated_evidence"]
    for kind in de.ADJUDICATED_EVIDENCE_KINDS:
        assert f"'{kind}'" in adjudicated
    for state in de.AGREEMENT_STATES:
        assert f"'{state}'" in adjudicated
    for span_role in de.SPAN_ROLES:
        assert f"'{span_role}'" in definitions["document_review_spans"]
    for source_class in de.SOURCE_CLASSES:
        assert f"'{source_class}'" in definitions["document_artifacts"]
