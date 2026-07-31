"""S5.2 -- frozen accession reader, joint run identity, and selection persistence:
focused adversarial test suite.

Every test builds its own frozen candidate snapshot in a freshly created temporary
SQLite database. No test opens a persistent repository database, performs a network
call, reads an ``inventory_*`` or ``census_*`` table, or edits an accepted S5.1 or S4
artifact.

The plan objects below are *inputs only*. None of them computes or pre-bakes an
expected answer: every expected value is either a literal frozen by Decision 018 or
Decision 019, or is produced by the accepted pure S5.1 core itself.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from typing import Final

import pytest

from disclosure_drift import pilot_policy
from disclosure_drift.errors import GateFailureError
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.release.hashing import hash_table
from disclosure_drift.sec import accession_selection_store
from disclosure_drift.sec.accession_selection_store import (
    ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
    FrozenJointCandidateSet,
    JointSelectionRunIdentity,
    PersistedJointSelectionResult,
    build_joint_selection_run_identity,
    execute_and_persist_joint_selection,
    load_frozen_joint_candidates,
    reconstruct_persisted_joint_selection,
)
from disclosure_drift.sec.accession_selector import (
    DEFERRED_QUOTA_KEY,
    NOT_APPLICABLE,
    QUOTA_DIMENSION_ACCESSION_CAP,
    QUOTA_DIMENSION_CROSS_CUTTING,
    AccessionCandidate,
    JointSelectionResult,
    accession_selection_rank,
    derive_amendment_families,
    solve_joint_selection,
)
from disclosure_drift.sec.entity_selection_store import execute_and_persist_entity_selection
from disclosure_drift.sec.entity_selector import (
    CONTROL_QUOTAS,
    MIN_INACTIVE_EVENTFUL,
    OPERATING_FINANCIAL_INDUSTRY,
    PILOT_SELECTION_SEED,
    TOTAL_OPERATING,
    selection_rank,
)
from disclosure_drift.storage.catalog import ELIGIBLE_FORM_TYPES
from disclosure_drift.storage.sqlite import apply_migrations, connect, transaction

_NODE_LIMIT: Final = 2_000_000
_SNAPSHOT_ID: Final = "a" * 64
_AT: Final = "2026-01-01T00:00:00Z"
_UNRESOLVED_PARENT: Final = "REVIEW_AMENDMENT_PARENT_UNRESOLVED"
_MULTI_INCOMPLETE: Final = "REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE"
_PRE_STUDY: Final = "PILOT_ACCESSION_PRE_STUDY_SUPPORT"
#: Sentinel meaning "inherit the official filing date"; distinct from a stored NULL.
_INHERIT: Final = "<inherit-official-filing-date>"

SIZE_SEQUENCE: Final = (
    ["large_accelerated"] * 7 + ["accelerated"] * 7 + ["non_accelerated_or_smaller"] * 6
)
INDUSTRY_SEQUENCE: Final = (
    ["technology_and_communications"] * 4
    + [OPERATING_FINANCIAL_INDUSTRY] * 4
    + ["industrial_and_materials"] * 3
    + ["consumer_retail_and_services"] * 3
    + ["healthcare_and_life_sciences"] * 3
    + ["energy_and_utilities"] * 3
)
HISTORY_SEQUENCE: Final = ["stable"] * 10 + ["eventful"] * 10
PURPOSE_CATEGORIES: Final = (
    "administrative_or_exhibit",
    "financial_or_xbrl_correction",
    "narrative_or_governance",
)


def _hex(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def dashed(cik: int, year: int, seq: int) -> str:
    return f"{cik:010d}-{year % 100:02d}-{seq:06d}"


def plain(cik: int, year: int, seq: int) -> str:
    return dashed(cik, year, seq).replace("-", "")


def canonical_former_name(prior: str, current: str) -> str:
    payload = {"current_name": current, "prior_name": prior, "relationship": "prior_current"}
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def canonical_from_to(source: str, target: str) -> str:
    payload = {"from_name": source, "relationship": "from_to", "to_name": target}
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


# --------------------------------------------------------------------------
# Snapshot plan -- inputs only
# --------------------------------------------------------------------------


@dataclass
class IdentityEvidencePlan:
    """One ``pilot_candidate_entity_evidence`` row on the ``identity`` dimension."""

    source_field: str = "former_name_relationship"
    evidence_role: str = "winning"
    canonical_observed_value: str | None = None
    parsed_record_id: str | None = "parsed-record-1"
    tag: str = "1"


@dataclass
class EntityPlan:
    cik: int
    category: str = "operating"
    size: str | None = None
    industry: str | None = None
    history: str | None = None
    inactive: bool = False
    control_kind: str | None = None
    identity_evidence: list[IdentityEvidencePlan] = field(default_factory=list)
    identity_reason: bool = False


@dataclass
class RegistrantPlan:
    cik: int
    role: str = "anchor"
    evidence_level: str = "provisional"
    padded_override: str | None = None


@dataclass
class AccessionPlan:
    cik: int
    year: int
    seq: int = 1
    form: str = "10-K"
    is_amendment: bool = False
    filing_date: str | None = None
    filing_date_null: bool = False
    report_date: str | None = None
    #: ``_INHERIT`` means "use the official filing date"; ``None`` stores a real NULL.
    acceptance_audit_date: str | None = _INHERIT
    acceptance_audit_cohort: str | None = None
    cohort: str | None = "development"
    cohort_evidence_level: str = "provisional"
    cohort_ambiguous: bool = False
    has_xbrl: bool = True
    has_inline_xbrl: bool = True
    xbrl_provisional: bool = True
    linkage_state: str | None = None
    parent_plain: str | None = None
    purpose_category: str | None = None
    purpose_evidence_level: str = "unavailable"
    base_eligible: bool = False
    stress_eligible: bool = False
    support_eligible: bool = False
    control_eligible: bool = False
    multi_registrant: bool = False
    registrants: list[RegistrantPlan] | None = None
    reasons: list[tuple[str, str]] = field(default_factory=list)
    dashed_override: str | None = None
    plain_override: str | None = None
    tie_break_override: str | None = None
    identity_evidence: bool = False

    @property
    def plain(self) -> str:
        return self.plain_override or plain(self.cik, self.year, self.seq)

    @property
    def dashed(self) -> str:
        return self.dashed_override or dashed(self.cik, self.year, self.seq)


@dataclass
class Plan:
    entities: list[EntityPlan] = field(default_factory=list)
    accessions: list[AccessionPlan] = field(default_factory=list)

    def entity(self, cik: int) -> EntityPlan:
        return next(entry for entry in self.entities if entry.cik == cik)

    def accession(self, number: str) -> AccessionPlan:
        return next(entry for entry in self.accessions if entry.dashed == number)


# --------------------------------------------------------------------------
# Plan -> frozen snapshot
# --------------------------------------------------------------------------


def _seed_reference_data(connection: sqlite3.Connection) -> None:
    with transaction(connection) as c:
        for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
            c.execute(
                "INSERT OR REPLACE INTO reference_form_types "
                "(form_type, is_amendment, is_eligible_universe, description, decision_record) "
                "VALUES (?, ?, ?, ?, 'Docs/Decisions/decision_007_sec_universe.md')",
                (form_type, int(is_amendment), int(eligible), description),
            )
        for code in REASON_CODES.values():
            c.execute(
                "INSERT OR REPLACE INTO reference_reason_codes "
                "(reason_code, category, description, blocks_release, requires_manual_review, "
                "decision_record) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    code.code,
                    code.category,
                    code.description,
                    int(code.blocks_release),
                    int(code.requires_manual_review),
                    code.decision_reference,
                ),
            )
        c.execute(
            "INSERT OR REPLACE INTO ops_ingestion_jobs "
            "(job_id, job_kind, job_state, stage, started_at_utc, detail) "
            "VALUES ('job-1', 'sec_census', 'completed', 'M2.2', '2026-01-01T00:00:00Z', '')"
        )


def _insert_entity(c: sqlite3.Connection, snapshot_id: str, entry: EntityPlan) -> None:
    padded = f"{entry.cik:010d}"
    if entry.category == "control":
        c.execute(
            "INSERT INTO pilot_candidate_entities "
            "(snapshot_id, cik_numeric, cik_padded, entity_tie_break_sha256, candidate_category, "
            "control_kind, size_evidence_level, industry_evidence_level, history_evidence_level, "
            "primary_universe_eligible, primary_universe_evidence_level, filing_time_name, "
            "recorded_at_utc) VALUES (?, ?, ?, ?, 'control', ?, 'unavailable', 'unavailable', "
            "'unavailable', 0, 'unavailable', ?, ?)",
            (
                snapshot_id,
                entry.cik,
                padded,
                selection_rank(padded, PILOT_SELECTION_SEED),
                entry.control_kind,
                f"Synthetic Control {entry.cik}",
                _AT,
            ),
        )
        return
    financial = entry.industry == OPERATING_FINANCIAL_INDUSTRY
    c.execute(
        "INSERT INTO pilot_candidate_entities "
        "(snapshot_id, cik_numeric, cik_padded, entity_tie_break_sha256, candidate_category, "
        "size_stratum, size_evidence_level, size_resolution_sha256, industry_family, "
        "industry_quota_eligible, industry_evidence_level, industry_resolution_sha256, "
        "history_class, history_evidence_level, history_resolution_sha256, currently_inactive, "
        "primary_universe_eligible, primary_universe_evidence_level, "
        "primary_universe_resolution_sha256, engineering_only_stress, filing_time_name, "
        "recorded_at_utc) VALUES (?, ?, ?, ?, 'operating', ?, 'provisional', ?, ?, 1, "
        "'provisional', ?, ?, 'provisional', ?, ?, ?, 'provisional', ?, ?, ?, ?)",
        (
            snapshot_id,
            entry.cik,
            padded,
            selection_rank(padded, PILOT_SELECTION_SEED),
            entry.size,
            _hex(f"size:{entry.cik}"),
            entry.industry,
            _hex(f"industry:{entry.cik}"),
            entry.history,
            _hex(f"history:{entry.cik}"),
            int(entry.inactive),
            0 if financial else 1,
            None if financial else _hex(f"pu:{entry.cik}"),
            int(financial),
            f"Synthetic Issuer {entry.cik}",
            _AT,
        ),
    )
    dimensions = ("size", "industry", "history") + (() if financial else ("primary_universe",))
    for dimension in dimensions:
        _insert_entity_evidence(
            c,
            snapshot_id,
            cik=entry.cik,
            dimension=dimension,
            evidence_role="winning",
            source_field="field-1",
            canonical_observed_value=None,
            parsed_record_id=None,
            tag=dimension,
        )


def _insert_entity_evidence(
    c: sqlite3.Connection,
    snapshot_id: str,
    *,
    cik: int,
    dimension: str,
    evidence_role: str,
    source_field: str,
    canonical_observed_value: str | None,
    parsed_record_id: str | None,
    tag: str,
) -> None:
    c.execute(
        "INSERT INTO pilot_candidate_entity_evidence "
        "(evidence_id, snapshot_id, cik_numeric, classification_dimension, evidence_role, "
        "source_observation_id, parsed_record_id, source_field, canonical_observed_value, "
        "policy_version, precedence, evidence_sha256, recorded_at_utc) "
        "VALUES (?, ?, ?, ?, ?, 'obs-1', ?, ?, ?, 'policy/1.0', 1, ?, ?)",
        (
            _hex(f"entity-evidence:{cik}:{dimension}:{source_field}:{tag}"),
            snapshot_id,
            cik,
            dimension,
            evidence_role,
            parsed_record_id,
            source_field,
            canonical_observed_value,
            _hex(f"entity-evidence-sha:{cik}:{dimension}:{source_field}:{tag}"),
            _AT,
        ),
    )


def _insert_accession(c: sqlite3.Connection, snapshot_id: str, entry: AccessionPlan) -> None:
    filing_date = (
        None
        if entry.filing_date_null
        else (entry.filing_date if entry.filing_date is not None else f"{entry.year}-03-15")
    )
    report_date = entry.report_date if entry.report_date is not None else f"{entry.year - 1}-12-31"
    acceptance = (
        filing_date if entry.acceptance_audit_date == _INHERIT else entry.acceptance_audit_date
    )
    tie_break = entry.tie_break_override or accession_selection_rank(
        f"{entry.cik:010d}", entry.dashed, PILOT_SELECTION_SEED
    )
    c.execute(
        "INSERT INTO pilot_candidate_accessions "
        "(snapshot_id, accession_plain, accession_number_dashed, accession_tie_break_sha256, "
        "anchor_cik_numeric, form_type, is_amendment, official_filing_date, report_date, "
        "acceptance_audit_date, filing_date_evidence_level, filing_date_resolution_sha256, "
        "filing_date_precedence, provisional_official_cohort, acceptance_audit_cohort, "
        "cohort_evidence_level, cohort_resolution_sha256, cohort_ambiguous, has_xbrl, "
        "has_inline_xbrl, xbrl_evidence_level, xbrl_resolution_sha256, amendment_linkage_state, "
        "provisional_parent_accession, amendment_purpose_category, "
        "amendment_purpose_evidence_level, amendment_purpose_resolution_sha256, "
        "amendment_purpose_quota_eligible, base_eligible, stress_eligible, support_eligible, "
        "control_eligible, multi_registrant, recorded_at_utc) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'provisional', ?, 2, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
        "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            snapshot_id,
            entry.plain,
            entry.dashed,
            tie_break,
            entry.cik,
            entry.form,
            int(entry.is_amendment),
            filing_date,
            report_date,
            acceptance,
            None if filing_date is None else _hex(f"filing:{entry.plain}"),
            entry.cohort,
            entry.acceptance_audit_cohort,
            entry.cohort_evidence_level,
            None if entry.cohort is None else _hex(f"cohort:{entry.plain}"),
            int(entry.cohort_ambiguous),
            int(entry.has_xbrl),
            int(entry.has_inline_xbrl),
            "provisional" if entry.xbrl_provisional else "unavailable",
            _hex(f"xbrl:{entry.plain}") if entry.xbrl_provisional else None,
            entry.linkage_state,
            entry.parent_plain,
            entry.purpose_category,
            entry.purpose_evidence_level,
            None if entry.purpose_category is None else _hex(f"purpose:{entry.plain}"),
            int(
                entry.purpose_category is not None and entry.purpose_evidence_level == "provisional"
            ),
            int(entry.base_eligible),
            int(entry.stress_eligible),
            int(entry.support_eligible),
            int(entry.control_eligible),
            int(entry.multi_registrant),
            _AT,
        ),
    )
    for dimension in ("filing_date", "cohort", "xbrl", "amendment_purpose"):
        if dimension == "cohort" and entry.cohort is None:
            continue
        if dimension == "xbrl" and not entry.xbrl_provisional:
            continue
        if (
            dimension == "amendment_purpose"
            and entry.linkage_state is None
            and entry.purpose_category is None
        ):
            continue
        c.execute(
            "INSERT INTO pilot_candidate_accession_evidence "
            "(evidence_id, snapshot_id, accession_plain, classification_dimension, evidence_role, "
            "source_observation_id, source_field, policy_version, precedence, evidence_sha256, "
            "recorded_at_utc) VALUES (?, ?, ?, ?, 'winning', 'obs-1', 'field-1', 'policy/1.0', 1, "
            "?, ?)",
            (
                _hex(f"accession-evidence:{entry.plain}:{dimension}"),
                snapshot_id,
                entry.plain,
                dimension,
                _hex(f"accession-evidence-sha:{entry.plain}:{dimension}"),
                _AT,
            ),
        )
    if entry.identity_evidence:
        c.execute(
            "INSERT INTO pilot_candidate_accession_evidence "
            "(evidence_id, snapshot_id, accession_plain, classification_dimension, evidence_role, "
            "source_observation_id, parsed_record_id, source_field, policy_version, precedence, "
            "evidence_sha256, recorded_at_utc) VALUES (?, ?, ?, 'identity', 'winning', 'obs-1', "
            "'parsed-1', 'former_name_relationship', 'policy/1.0', 1, ?, ?)",
            (
                _hex(f"accession-identity:{entry.plain}"),
                snapshot_id,
                entry.plain,
                _hex(f"accession-identity-sha:{entry.plain}"),
                _AT,
            ),
        )
    registrants = (
        entry.registrants if entry.registrants is not None else [RegistrantPlan(cik=entry.cik)]
    )
    for registrant in registrants:
        c.execute(
            "INSERT INTO pilot_candidate_accession_registrants "
            "(snapshot_id, accession_plain, registrant_cik_numeric, registrant_cik_padded, role, "
            "is_anchor, evidence_level, recorded_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                snapshot_id,
                entry.plain,
                registrant.cik,
                registrant.padded_override or f"{registrant.cik:010d}",
                registrant.role,
                int(registrant.role == "anchor"),
                registrant.evidence_level,
                _AT,
            ),
        )
    for scope, code in entry.reasons:
        c.execute(
            "INSERT INTO pilot_candidate_accession_reasons "
            "(snapshot_id, accession_plain, reason_scope, reason_code, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?)",
            (snapshot_id, entry.plain, scope, code, _AT),
        )


def write_plan(connection: sqlite3.Connection, plan: Plan, snapshot_id: str = _SNAPSHOT_ID) -> str:
    """Materialize one plan as a frozen candidate snapshot."""
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_candidate_snapshots "
            "(snapshot_id, census_run_id, coverage_start, coverage_end, as_of_date, "
            "include_open_quarter, coverage_policy_version, candidate_policy_version, "
            "sic_family_mapping_version, evidence_policy_version, coverage_window_sha256, "
            "input_observation_set_sha256, snapshot_state, created_at_utc) "
            "VALUES (?, 'job-1', '2009-01-01', '2026-06-30', '2026-06-30', 0, 'coverage/1.0', "
            "?, ?, ?, ?, ?, 'building', ?)",
            (
                snapshot_id,
                pilot_policy.PILOT_CANDIDATE_POLICY_VERSION,
                pilot_policy.SIC_FAMILY_MAPPING_VERSION,
                pilot_policy.PILOT_EVIDENCE_POLICY_VERSION,
                _hex(f"coverage:{snapshot_id}"),
                _hex(f"observations:{snapshot_id}"),
                _AT,
            ),
        )
        for entity in plan.entities:
            _insert_entity(c, snapshot_id, entity)
            for row in entity.identity_evidence:
                _insert_entity_evidence(
                    c,
                    snapshot_id,
                    cik=entity.cik,
                    dimension="identity",
                    evidence_role=row.evidence_role,
                    source_field=row.source_field,
                    canonical_observed_value=row.canonical_observed_value,
                    parsed_record_id=row.parsed_record_id,
                    tag=row.tag,
                )
            if entity.identity_reason:
                c.execute(
                    "INSERT INTO pilot_candidate_entity_reasons "
                    "(snapshot_id, cik_numeric, reason_scope, reason_code, recorded_at_utc) "
                    "VALUES (?, ?, 'identity', 'REVIEW_PILOT_SIZE_CATEGORY_UNAVAILABLE', ?)",
                    (snapshot_id, entity.cik, _AT),
                )
        for accession in plan.accessions:
            _insert_accession(c, snapshot_id, accession)

    with transaction(connection) as c:
        c.execute(
            "UPDATE pilot_candidate_snapshots SET snapshot_state = 'frozen', frozen_at_utc = ?, "
            "entity_count = ?, accession_count = ?, candidate_entity_table_sha256 = ?, "
            "candidate_accession_table_sha256 = ?, candidate_registrant_table_sha256 = ?, "
            "candidate_entity_evidence_sha256 = ?, candidate_accession_evidence_sha256 = ?, "
            "candidate_entity_reasons_sha256 = ?, candidate_accession_reasons_sha256 = ?, "
            "candidate_snapshot_sha256 = ? WHERE snapshot_id = ?",
            (
                _AT,
                len(plan.entities),
                len(plan.accessions),
                *(
                    _hex(f"{part}:{snapshot_id}")
                    for part in (
                        "entities",
                        "accessions",
                        "registrants",
                        "entity-evidence",
                        "accession-evidence",
                        "entity-reasons",
                        "accession-reasons",
                        "snapshot",
                    )
                ),
                snapshot_id,
            ),
        )
    return snapshot_id


#: Catalogs this suite built for the test now running. The corruption fixtures
#: below accept nothing else, so they cannot touch a real catalog even by mistake.
_SCRATCH_CATALOGS: set[Path] = set()


@pytest.fixture
def db(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """A migrated, reference-seeded temporary catalog."""
    path = tmp_path / "catalog.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection)
        _seed_reference_data(connection)
        _SCRATCH_CATALOGS.add(path.resolve())
        try:
            yield connection
        finally:
            _SCRATCH_CATALOGS.discard(path.resolve())


def frozen(connection: sqlite3.Connection, plan: Plan) -> FrozenJointCandidateSet:
    write_plan(connection, plan)
    return load_frozen_joint_candidates(connection, _SNAPSHOT_ID)


def candidate(loaded: FrozenJointCandidateSet, number: str) -> AccessionCandidate:
    return next(a for a in loaded.accessions if a.accession_number_dashed == number)


# --------------------------------------------------------------------------
# Plans
# --------------------------------------------------------------------------


def minimal_plan() -> Plan:
    """One operating entity and one original 10-K: the smallest conforming snapshot."""
    return Plan(
        entities=[
            EntityPlan(
                cik=1,
                size=SIZE_SEQUENCE[0],
                industry=INDUSTRY_SEQUENCE[0],
                history=HISTORY_SEQUENCE[0],
            )
        ],
        accessions=[AccessionPlan(cik=1, year=2020, seq=1, base_eligible=True)],
    )


def amendment_plan(**overrides: object) -> Plan:
    """An original 10-K plus one 10-K/A that resolves to it."""
    plan = minimal_plan()
    amendment = AccessionPlan(
        cik=1,
        year=2021,
        seq=2,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_original",
        parent_plain=plain(1, 2020, 1),
        purpose_category=PURPOSE_CATEGORIES[0],
        purpose_evidence_level="provisional",
    )
    for key, value in overrides.items():
        setattr(amendment, key, value)
    plan.accessions.append(amendment)
    return plan


def feasible_plan() -> Plan:
    """A tight, fully feasible pool under the complete frozen quota set.

    Composition mirrors the accepted S5.1 suite's fixture: 20 operating entities each
    with one base accession; slots 0-5 additionally carry a 2009 pre-study support
    accession paired with a 2010 development target; slots 0-7 each carry one amendment
    of their own base, of which slots 5-7 are 10-KT/A; four boundary controls each carry
    one control-role original. Every amendment is accepted strictly after its original.
    """
    plan = Plan()
    for slot in range(TOTAL_OPERATING):
        cik = slot + 1
        plan.entities.append(
            EntityPlan(
                cik=cik,
                size=SIZE_SEQUENCE[slot],
                industry=INDUSTRY_SEQUENCE[slot],
                history=HISTORY_SEQUENCE[slot],
                inactive=HISTORY_SEQUENCE[slot] == "eventful"
                and 10 <= slot < 10 + MIN_INACTIVE_EVENTFUL,
                identity_evidence=(
                    [
                        IdentityEvidencePlan(
                            canonical_observed_value=canonical_former_name(
                                f"Old Issuer {cik}", f"New Issuer {cik}"
                            )
                        )
                    ]
                    if slot < 4
                    else []
                ),
            )
        )
        if slot < 6:
            plan.accessions.append(
                AccessionPlan(
                    cik=cik,
                    year=2009,
                    seq=1,
                    support_eligible=True,
                    cohort=None,
                    cohort_evidence_level="unavailable",
                    has_xbrl=False,
                    has_inline_xbrl=False,
                    reasons=[("cohort", _PRE_STUDY)],
                )
            )
            base_year = 2010
            base = AccessionPlan(
                cik=cik, year=base_year, seq=2, base_eligible=True, has_inline_xbrl=False
            )
        elif slot < 12:
            base = AccessionPlan(
                cik=cik, year=2024, seq=2, base_eligible=True, cohort="primary_test"
            )
        elif slot < 16:
            base = AccessionPlan(
                cik=cik, year=2025, seq=2, base_eligible=True, cohort="prospective"
            )
        else:
            base = AccessionPlan(
                cik=cik, year=2018, seq=2, base_eligible=True, multi_registrant=slot in (16, 17)
            )
            if slot in (16, 17):
                base.registrants = [
                    RegistrantPlan(cik=cik),
                    RegistrantPlan(cik=900 + cik, role="associated"),
                ]
        plan.accessions.append(base)
        if slot < 8:
            plan.accessions.append(
                AccessionPlan(
                    cik=cik,
                    year=base.year + 1,
                    seq=3,
                    form="10-KT/A" if slot >= 5 else "10-K/A",
                    is_amendment=True,
                    stress_eligible=True,
                    cohort="development" if base.year < 2022 else "prospective",
                    linkage_state="amends_original",
                    parent_plain=base.plain,
                    purpose_category=PURPOSE_CATEGORIES[slot % 3],
                    purpose_evidence_level="provisional",
                )
            )
    for offset, kind in enumerate(CONTROL_QUOTAS):
        cik = 101 + offset
        plan.entities.append(EntityPlan(cik=cik, category="control", control_kind=kind))
        plan.accessions.append(
            AccessionPlan(cik=cik, year=2020, seq=2, control_eligible=True, cohort="development")
        )
    return plan


# --------------------------------------------------------------------------
# 1: reader, conversion, and canonical validation
# --------------------------------------------------------------------------


def test_conforming_snapshot_loads_into_the_accepted_pure_inputs(db: sqlite3.Connection) -> None:
    loaded = frozen(db, minimal_plan())
    assert loaded.snapshot_id == _SNAPSHOT_ID
    assert loaded.entity_count == 1
    assert loaded.accession_count == 1
    assert len(loaded.entities) == 1
    assert len(loaded.accessions) == 1
    only = loaded.accessions[0]
    assert isinstance(only, AccessionCandidate)
    assert only.accession_number_dashed == dashed(1, 2020, 1)
    assert only.accession_plain == plain(1, 2020, 1)
    assert only.anchor_cik_padded == "0000000001"
    assert only.cohort_applicability == "applies"
    assert only.amendment_linkage_evidence_level == NOT_APPLICABLE
    assert only.multi_registrant_evidence_level == NOT_APPLICABLE
    assert only.amendment_purpose_evidence_level == NOT_APPLICABLE


def test_declared_accession_count_cannot_drift_from_the_frozen_rows(
    db: sqlite3.Connection,
) -> None:
    """The loader's count check is defence in depth; the schema already forbids drift.

    Migration 0009's freeze trigger requires ``accession_count`` to equal the actual row
    count at freeze time, and its frozen-fields-immutable trigger forbids changing it
    afterwards, so no frozen snapshot can declare a count its rows do not support.
    """
    write_plan(db, minimal_plan())
    with (
        pytest.raises(sqlite3.IntegrityError, match="frozen fields are immutable"),
        transaction(db) as c,
    ):
        c.execute(
            "UPDATE pilot_candidate_snapshots SET accession_count = 5 WHERE snapshot_id = ?",
            (_SNAPSHOT_ID,),
        )
    with (
        pytest.raises(sqlite3.IntegrityError, match="accession_count mismatch"),
        transaction(db) as c,
    ):
        c.execute(
            "INSERT INTO pilot_candidate_snapshots "
            "(snapshot_id, census_run_id, coverage_start, coverage_end, as_of_date, "
            "include_open_quarter, coverage_policy_version, candidate_policy_version, "
            "sic_family_mapping_version, evidence_policy_version, coverage_window_sha256, "
            "input_observation_set_sha256, snapshot_state, created_at_utc) "
            "VALUES ('b', 'job-1', '2009-01-01', '2026-06-30', '2026-06-30', 0, 'coverage/1.0', "
            "?, ?, ?, ?, ?, 'building', ?)".replace("'b'", "?"),
            (
                "b" * 64,
                pilot_policy.PILOT_CANDIDATE_POLICY_VERSION,
                pilot_policy.SIC_FAMILY_MAPPING_VERSION,
                pilot_policy.PILOT_EVIDENCE_POLICY_VERSION,
                _hex("coverage-b"),
                _hex("observations-b"),
                _AT,
            ),
        )
        c.execute(
            "UPDATE pilot_candidate_snapshots SET snapshot_state = 'frozen', frozen_at_utc = ?, "
            "entity_count = 0, accession_count = 3, candidate_entity_table_sha256 = ?, "
            "candidate_accession_table_sha256 = ?, candidate_registrant_table_sha256 = ?, "
            "candidate_entity_evidence_sha256 = ?, candidate_accession_evidence_sha256 = ?, "
            "candidate_entity_reasons_sha256 = ?, candidate_accession_reasons_sha256 = ?, "
            "candidate_snapshot_sha256 = ? WHERE snapshot_id = ?",
            (_AT, *(_hex(f"b{index}") for index in range(8)), "b" * 64),
        )


def test_plain_and_dashed_disagreement_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    plan.accessions[0].dashed_override = "0000000001-20-000009"
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="inconsistent"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_non_canonical_dashed_form_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    plan.accessions[0].dashed_override = "1-20-1"
    plan.accessions[0].plain_override = "000000000120000001"
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="canonical dashed form"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_stored_tie_break_hash_mismatch_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    plan.accessions[0].tie_break_override = "0" * 64
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="accession_tie_break_sha256"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_stored_tie_break_hash_matches_the_decision_018_formula(db: sqlite3.Connection) -> None:
    loaded = frozen(db, minimal_plan())
    expected = hashlib.sha256(
        f"{PILOT_SELECTION_SEED}|0000000001|{dashed(1, 2020, 1)}".encode()
    ).hexdigest()
    row = db.execute(
        "SELECT accession_tie_break_sha256 FROM pilot_candidate_accessions "
        "WHERE accession_plain = ?",
        (plain(1, 2020, 1),),
    ).fetchone()
    assert row["accession_tie_break_sha256"] == expected
    assert loaded.accessions[0].rank == expected


def test_non_frozen_snapshot_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    with transaction(db) as c:
        c.execute(
            "INSERT INTO pilot_candidate_snapshots "
            "(snapshot_id, census_run_id, coverage_start, coverage_end, as_of_date, "
            "include_open_quarter, coverage_policy_version, candidate_policy_version, "
            "sic_family_mapping_version, evidence_policy_version, coverage_window_sha256, "
            "input_observation_set_sha256, snapshot_state, created_at_utc) "
            "VALUES (?, 'job-1', '2009-01-01', '2026-06-30', '2026-06-30', 0, 'coverage/1.0', "
            "?, ?, ?, ?, ?, 'building', ?)",
            (
                _SNAPSHOT_ID,
                pilot_policy.PILOT_CANDIDATE_POLICY_VERSION,
                pilot_policy.SIC_FAMILY_MAPPING_VERSION,
                pilot_policy.PILOT_EVIDENCE_POLICY_VERSION,
                _hex("coverage"),
                _hex("observations"),
                _AT,
            ),
        )
        for entity in plan.entities:
            _insert_entity(c, _SNAPSHOT_ID, entity)
    with pytest.raises(GateFailureError, match="not frozen"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_contradictory_cohort_evidence_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    plan.accessions[0].cohort = None
    plan.accessions[0].cohort_evidence_level = "provisional"
    plan.accessions[0].base_eligible = False
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="contradictory cohort evidence"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


# --------------------------------------------------------------------------
# 2: Decision 019 section 5 -- amendment-linkage evidence
# --------------------------------------------------------------------------


def test_original_maps_to_structurally_inapplicable_linkage(db: sqlite3.Connection) -> None:
    loaded = frozen(db, minimal_plan())
    original = candidate(loaded, dashed(1, 2020, 1))
    assert original.amendment_linkage_state is None
    assert original.provisional_parent_accession_dashed is None
    assert original.amendment_linkage_evidence_level == NOT_APPLICABLE


@pytest.mark.parametrize("state", ("amends_original", "supplements_original"))
def test_resolved_state_against_an_original_maps_to_provisional(
    db: sqlite3.Connection, state: str
) -> None:
    loaded = frozen(db, amendment_plan(linkage_state=state))
    amendment = candidate(loaded, dashed(1, 2021, 2))
    assert amendment.amendment_linkage_evidence_level == "provisional"
    assert amendment.provisional_parent_accession_dashed == dashed(1, 2020, 1)
    assert amendment.amendment_linkage_state == state


def test_possible_amendment_of_maps_to_review_required_without_a_parent(
    db: sqlite3.Connection,
) -> None:
    plan = amendment_plan(
        linkage_state="possible_amendment_of", reasons=[("amendment", _UNRESOLVED_PARENT)]
    )
    loaded = frozen(db, plan)
    amendment = candidate(loaded, dashed(1, 2021, 2))
    assert amendment.amendment_linkage_evidence_level == "review_required"
    assert amendment.provisional_parent_accession_dashed is None


def test_unresolved_amendment_maps_to_unavailable_without_a_parent(
    db: sqlite3.Connection,
) -> None:
    plan = amendment_plan(
        linkage_state="unresolved_amendment",
        parent_plain=None,
        reasons=[("amendment", _UNRESOLVED_PARENT)],
    )
    loaded = frozen(db, plan)
    amendment = candidate(loaded, dashed(1, 2021, 2))
    assert amendment.amendment_linkage_evidence_level == "unavailable"
    assert amendment.provisional_parent_accession_dashed is None


def test_unresolved_state_yields_a_singleton_family_and_no_linked_contribution(
    db: sqlite3.Connection,
) -> None:
    """Decision 019 section 5.5: the stored candidate parent never reaches S5.1."""
    plan = amendment_plan(
        linkage_state="possible_amendment_of", reasons=[("amendment", _UNRESOLVED_PARENT)]
    )
    loaded = frozen(db, plan)
    families, _roots = derive_amendment_families(loaded.accessions)
    singleton = next(f for f in families if f.family_id == dashed(1, 2021, 2))
    assert singleton.members == (dashed(1, 2021, 2),)
    assert singleton.resolved is False
    assert singleton.reason == "unresolved_parent"


def test_resolved_state_whose_parent_is_absent_maps_to_review_required(
    db: sqlite3.Connection,
) -> None:
    plan = amendment_plan(parent_plain=plain(1, 2019, 9))
    loaded = frozen(db, plan)
    amendment = candidate(loaded, dashed(1, 2021, 2))
    assert amendment.amendment_linkage_evidence_level == "review_required"
    assert amendment.provisional_parent_accession_dashed is None


@pytest.mark.parametrize(
    ("state", "parent_is_amendment"),
    (
        ("amends_original", True),
        ("supplements_original", True),
        ("amends_prior_amendment", False),
    ),
)
def test_parent_type_mismatch_fails_closed(
    db: sqlite3.Connection, state: str, parent_is_amendment: bool
) -> None:
    plan = minimal_plan()
    if parent_is_amendment:
        parent = AccessionPlan(
            cik=1,
            year=2020,
            seq=5,
            form="10-K/A",
            is_amendment=True,
            stress_eligible=True,
            linkage_state="unresolved_amendment",
            reasons=[("amendment", _UNRESOLVED_PARENT)],
        )
        plan.accessions.append(parent)
        parent_plain_value = parent.plain
    else:
        parent_plain_value = plain(1, 2020, 1)
    plan.accessions.append(
        AccessionPlan(
            cik=1,
            year=2021,
            seq=2,
            form="10-K/A",
            is_amendment=True,
            stress_eligible=True,
            linkage_state=state,
            parent_plain=parent_plain_value,
        )
    )
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="is_amendment="):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_valid_amends_prior_amendment_chain_maps_to_provisional(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    first = AccessionPlan(
        cik=1,
        year=2021,
        seq=2,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_original",
        parent_plain=plain(1, 2020, 1),
    )
    second = AccessionPlan(
        cik=1,
        year=2022,
        seq=3,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_prior_amendment",
        parent_plain=first.plain,
    )
    plan.accessions.extend([first, second])
    loaded = frozen(db, plan)
    assert candidate(loaded, first.dashed).amendment_linkage_evidence_level == "provisional"
    outer = candidate(loaded, second.dashed)
    assert outer.amendment_linkage_evidence_level == "provisional"
    assert outer.provisional_parent_accession_dashed == first.dashed


def test_parent_cycle_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    first = AccessionPlan(
        cik=1,
        year=2021,
        seq=2,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_prior_amendment",
    )
    second = AccessionPlan(
        cik=1,
        year=2022,
        seq=3,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_prior_amendment",
        parent_plain=first.plain,
    )
    first.parent_plain = second.plain
    plan.accessions.extend([first, second])
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="revisits"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_intermediate_unresolved_amendment_is_a_dead_end(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    middle = AccessionPlan(
        cik=1,
        year=2021,
        seq=2,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="unresolved_amendment",
        reasons=[("amendment", _UNRESOLVED_PARENT)],
    )
    outer = AccessionPlan(
        cik=1,
        year=2022,
        seq=3,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_prior_amendment",
        parent_plain=middle.plain,
    )
    plan.accessions.extend([middle, outer])
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="unresolved_amendment, a dead end"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_intermediate_possible_amendment_without_a_parent_is_a_dead_end(
    db: sqlite3.Connection,
) -> None:
    plan = minimal_plan()
    middle = AccessionPlan(
        cik=1,
        year=2021,
        seq=2,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="possible_amendment_of",
        reasons=[("amendment", _UNRESOLVED_PARENT)],
    )
    outer = AccessionPlan(
        cik=1,
        year=2022,
        seq=3,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_prior_amendment",
        parent_plain=middle.plain,
    )
    plan.accessions.extend([middle, outer])
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="possible_amendment_of with no stored candidate"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_intermediate_possible_amendment_with_a_parent_continues_the_walk(
    db: sqlite3.Connection,
) -> None:
    """Decision 019 section 5.4.2: the stored diagnostic parent never becomes an S5.1 edge."""
    plan = minimal_plan()
    middle = AccessionPlan(
        cik=1,
        year=2021,
        seq=2,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="possible_amendment_of",
        parent_plain=plain(1, 2020, 1),
        reasons=[("amendment", _UNRESOLVED_PARENT)],
    )
    outer = AccessionPlan(
        cik=1,
        year=2022,
        seq=3,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_prior_amendment",
        parent_plain=middle.plain,
    )
    plan.accessions.extend([middle, outer])
    loaded = frozen(db, plan)

    intermediate = candidate(loaded, middle.dashed)
    assert intermediate.amendment_linkage_evidence_level == "review_required"
    assert intermediate.provisional_parent_accession_dashed is None
    outer_candidate = candidate(loaded, outer.dashed)
    assert outer_candidate.amendment_linkage_evidence_level == "provisional"
    assert outer_candidate.provisional_parent_accession_dashed == middle.dashed

    families, _roots = derive_amendment_families(loaded.accessions)
    unresolved = {family.family_id for family in families if not family.resolved}
    assert middle.dashed in unresolved
    assert outer.dashed in unresolved


def test_resolved_state_without_a_stored_parent_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(db, amendment_plan(parent_plain=None))
    with pytest.raises(GateFailureError, match="carries no parent identity"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_unresolved_amendment_with_a_stored_parent_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(
        db,
        amendment_plan(
            linkage_state="unresolved_amendment", reasons=[("amendment", _UNRESOLVED_PARENT)]
        ),
    )
    with pytest.raises(GateFailureError, match="cannot also carry the stored parent"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_malformed_stored_parent_identity_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(db, amendment_plan(parent_plain="not-eighteen-digits"))
    with pytest.raises(GateFailureError, match="eighteen decimal digits"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_self_referential_stored_parent_fails_closed(db: sqlite3.Connection) -> None:
    plan = amendment_plan()
    plan.accessions[-1].parent_plain = plan.accessions[-1].plain
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="self-referential"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_linkage_state_on_a_non_amendment_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    with pytest.raises(sqlite3.IntegrityError):
        write_plan(
            db,
            Plan(
                entities=plan.entities,
                accessions=[
                    AccessionPlan(
                        cik=1, year=2020, seq=1, base_eligible=True, linkage_state="amends_original"
                    )
                ],
            ),
        )


def test_resolved_state_with_an_unresolved_parent_reason_fails_closed(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, amendment_plan(reasons=[("amendment", _UNRESOLVED_PARENT)]))
    with pytest.raises(GateFailureError, match="contradicts its stored"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_unresolved_state_without_its_review_reason_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(db, amendment_plan(linkage_state="possible_amendment_of"))
    with pytest.raises(GateFailureError, match="requires a REVIEW_AMENDMENT_PARENT_UNRESOLVED"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


# --------------------------------------------------------------------------
# 3: Decision 019 section 5.9 -- amendment acceptance ordering
# --------------------------------------------------------------------------


def test_strictly_later_acceptance_date_is_admitted(db: sqlite3.Connection) -> None:
    plan = amendment_plan(acceptance_audit_date="2021-03-16")
    plan.accessions[0].acceptance_audit_date = "2021-03-15"
    loaded = frozen(db, plan)
    assert candidate(loaded, dashed(1, 2021, 2)).amendment_linkage_evidence_level == "provisional"


@pytest.mark.parametrize(
    ("amendment_date", "original_date", "expected"),
    (
        ("2021-03-14", "2021-03-15", "not strictly later"),
        ("2021-03-15", "2021-03-15", "not strictly later"),
        (None, "2021-03-15", "exact YYYY-MM-DD acceptance_audit_date"),
        ("2021-03-16", None, "requires an exact YYYY-MM-DD"),
        ("2021-13-45", "2021-03-15", "exact YYYY-MM-DD acceptance_audit_date"),
        ("2021-02-30", "2021-03-15", "exact YYYY-MM-DD acceptance_audit_date"),
        ("2021-03-16", "not-a-date", "requires an exact YYYY-MM-DD"),
    ),
)
def test_acceptance_ordering_gate_is_total(
    db: sqlite3.Connection,
    amendment_date: str | None,
    original_date: str | None,
    expected: str,
) -> None:
    plan = amendment_plan(acceptance_audit_date=amendment_date)
    plan.accessions[0].acceptance_audit_date = original_date
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match=expected):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_ordering_failure_leaves_the_stored_representation_untouched(
    db: sqlite3.Connection,
) -> None:
    """No downgrade, no re-pointing, no synthesized unresolved-parent reason row."""
    plan = amendment_plan(acceptance_audit_date="2021-03-14")
    plan.accessions[0].acceptance_audit_date = "2021-03-15"
    write_plan(db, plan)
    before = _snapshot_fingerprint(db)
    with pytest.raises(GateFailureError):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)
    assert _snapshot_fingerprint(db) == before
    assert (
        db.execute(
            "SELECT COUNT(*) FROM pilot_candidate_accession_reasons WHERE reason_code = ?",
            (_UNRESOLVED_PARENT,),
        ).fetchone()[0]
        == 0
    )


def _snapshot_fingerprint(connection: sqlite3.Connection) -> tuple[object, ...]:
    return tuple(
        tuple(tuple(row) for row in connection.execute(f"SELECT * FROM {table}"))  # noqa: S608
        for table in (
            "pilot_candidate_accessions",
            "pilot_candidate_accession_reasons",
            "pilot_candidate_accession_registrants",
            "pilot_candidate_entity_evidence",
        )
    )


def test_ordering_is_measured_against_the_transitive_root_not_the_immediate_parent(
    db: sqlite3.Connection,
) -> None:
    plan = minimal_plan()
    plan.accessions[0].acceptance_audit_date = "2020-03-15"
    first = AccessionPlan(
        cik=1,
        year=2021,
        seq=2,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_original",
        parent_plain=plain(1, 2020, 1),
        acceptance_audit_date="2023-03-15",
    )
    second = AccessionPlan(
        cik=1,
        year=2022,
        seq=3,
        form="10-K/A",
        is_amendment=True,
        stress_eligible=True,
        linkage_state="amends_prior_amendment",
        parent_plain=first.plain,
        acceptance_audit_date="2021-03-15",
    )
    plan.accessions.extend([first, second])
    loaded = frozen(db, plan)
    # 2021-03-15 precedes its immediate amendment parent but follows the root original.
    assert candidate(loaded, second.dashed).amendment_linkage_evidence_level == "provisional"


def test_absent_parent_is_never_reported_as_an_ordering_failure(db: sqlite3.Connection) -> None:
    plan = amendment_plan(parent_plain=plain(1, 2019, 9), acceptance_audit_date=None)
    loaded = frozen(db, plan)
    assert candidate(loaded, dashed(1, 2021, 2)).amendment_linkage_evidence_level == (
        "review_required"
    )


def test_acceptance_audit_cohort_is_never_used_for_ordering(db: sqlite3.Connection) -> None:
    plan = amendment_plan(acceptance_audit_date=None, acceptance_audit_cohort="prospective")
    plan.accessions[0].acceptance_audit_date = "2020-03-15"
    plan.accessions[0].acceptance_audit_cohort = "development"
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="exact YYYY-MM-DD acceptance_audit_date"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


# --------------------------------------------------------------------------
# 4: Decision 019 section 6 -- multi-registrant evidence
# --------------------------------------------------------------------------


def registrant_plan(
    *, flag: bool, registrants: list[RegistrantPlan], reasons: list[tuple[str, str]] | None = None
) -> Plan:
    plan = minimal_plan()
    plan.accessions[0].multi_registrant = flag
    plan.accessions[0].registrants = registrants
    plan.accessions[0].reasons = reasons or []
    return plan


def test_single_registrant_maps_to_structurally_inapplicable(db: sqlite3.Connection) -> None:
    loaded = frozen(db, registrant_plan(flag=False, registrants=[RegistrantPlan(cik=1)]))
    assert loaded.accessions[0].multi_registrant_evidence_level == NOT_APPLICABLE


def test_qualifying_all_provisional_set_maps_to_provisional(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        registrant_plan(
            flag=True,
            registrants=[RegistrantPlan(cik=1), RegistrantPlan(cik=901, role="associated")],
        ),
    )
    assert loaded.accessions[0].multi_registrant_evidence_level == "provisional"


@pytest.mark.parametrize(
    ("levels", "expected"),
    (
        (("provisional", "review_required"), "review_required"),
        (("provisional", "unavailable"), "unavailable"),
        (("provisional", "conflicting"), "conflicting"),
        (("unavailable", "review_required"), "review_required"),
        (("unavailable", "conflicting"), "conflicting"),
        (("review_required", "conflicting"), "conflicting"),
    ),
)
def test_weaker_state_precedence_is_deterministic(
    db: sqlite3.Connection, levels: tuple[str, str], expected: str
) -> None:
    loaded = frozen(
        db,
        registrant_plan(
            flag=True,
            registrants=[
                RegistrantPlan(cik=1, evidence_level=levels[0]),
                RegistrantPlan(cik=901, role="associated", evidence_level=levels[1]),
            ],
        ),
    )
    assert loaded.accessions[0].multi_registrant_evidence_level == expected


def test_submitter_only_rows_never_establish_the_registrant_set(db: sqlite3.Connection) -> None:
    write_plan(
        db,
        registrant_plan(
            flag=True,
            registrants=[RegistrantPlan(cik=1), RegistrantPlan(cik=902, role="submitter_only")],
        ),
    )
    with pytest.raises(GateFailureError, match="without a qualifying registrant set"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_submitter_only_evidence_never_affects_the_aggregate(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        registrant_plan(
            flag=True,
            registrants=[
                RegistrantPlan(cik=1),
                RegistrantPlan(cik=901, role="associated"),
                RegistrantPlan(cik=902, role="submitter_only", evidence_level="conflicting"),
            ],
        ),
    )
    assert loaded.accessions[0].multi_registrant_evidence_level == "provisional"


def test_flag_zero_without_associated_rows_is_not_a_divergence(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        registrant_plan(
            flag=False,
            registrants=[RegistrantPlan(cik=1), RegistrantPlan(cik=902, role="submitter_only")],
            reasons=[("multi_registrant", "REVIEW_PILOT_AMENDMENT_PURPOSE_UNPROVEN")],
        ),
    )
    assert loaded.accessions[0].multi_registrant_evidence_level == NOT_APPLICABLE


def test_the_single_permitted_divergence_requires_the_exact_code(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        registrant_plan(
            flag=False,
            registrants=[RegistrantPlan(cik=1), RegistrantPlan(cik=901, role="associated")],
            reasons=[("multi_registrant", _MULTI_INCOMPLETE)],
        ),
    )
    assert loaded.accessions[0].multi_registrant_evidence_level == NOT_APPLICABLE


@pytest.mark.parametrize(
    "reasons",
    (
        [("multi_registrant", "REVIEW_PILOT_AMENDMENT_PURPOSE_UNPROVEN")],
        [
            ("multi_registrant", _MULTI_INCOMPLETE),
            ("multi_registrant", "REVIEW_PILOT_AMENDMENT_PURPOSE_UNPROVEN"),
        ],
        [("eligibility", _MULTI_INCOMPLETE), ("multi_registrant", "REVIEW_PILOT_SIC_UNMAPPED")],
    ),
)
def test_every_other_divergence_shape_fails_closed(
    db: sqlite3.Connection, reasons: list[tuple[str, str]]
) -> None:
    write_plan(
        db,
        registrant_plan(
            flag=False,
            registrants=[RegistrantPlan(cik=1), RegistrantPlan(cik=901, role="associated")],
            reasons=reasons,
        ),
    )
    with pytest.raises(GateFailureError, match="authorized only by exactly one"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_anchor_registrant_must_match_the_accession_anchor(db: sqlite3.Connection) -> None:
    write_plan(db, registrant_plan(flag=False, registrants=[RegistrantPlan(cik=77)]))
    with pytest.raises(GateFailureError, match="does not match anchor_cik_numeric"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_non_canonical_registrant_padding_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(
        db, registrant_plan(flag=False, registrants=[RegistrantPlan(cik=1, padded_override="1")])
    )
    with pytest.raises(GateFailureError, match="not the canonical rendering"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_duplicate_registrant_padded_identity_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(
        db,
        registrant_plan(
            flag=True,
            registrants=[
                RegistrantPlan(cik=1),
                RegistrantPlan(cik=901, role="associated", padded_override="0000000001"),
            ],
        ),
    )
    with pytest.raises(GateFailureError, match="not the canonical rendering"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_registrant_digest_uses_the_frozen_label_and_column_order() -> None:
    """Decision 019 section 6.6.1 fixes the domain label, column order, and row set."""
    rows = [
        {
            "registrant_cik_padded": "0000000001",
            "role": "anchor",
            "is_anchor": 1,
            "evidence_level": "provisional",
        },
        {
            "registrant_cik_padded": "0000000901",
            "role": "associated",
            "is_anchor": 0,
            "evidence_level": "provisional",
        },
    ]
    columns = ("registrant_cik_padded", "role", "is_anchor", "evidence_level")
    forward = hash_table("pilot_candidate_accession_registrants", columns, rows)
    reverse = hash_table("pilot_candidate_accession_registrants", columns, list(reversed(rows)))
    assert forward.normalized_content_sha256 == reverse.normalized_content_sha256
    assert (
        hash_table("other_label", columns, rows).normalized_content_sha256
        != forward.normalized_content_sha256
    )


def _accession_hash(connection: sqlite3.Connection, plan: Plan) -> str:
    return frozen(connection, plan).accession_content_sha256


def test_registrant_row_order_does_not_change_candidate_content(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    registrants = [RegistrantPlan(cik=1), RegistrantPlan(cik=901, role="associated")]
    first = _accession_hash(db, registrant_plan(flag=True, registrants=registrants))
    with connect(tmp_path / "second.sqlite3", writer=True) as other:
        apply_migrations(other)
        _seed_reference_data(other)
        second = _accession_hash(
            other, registrant_plan(flag=True, registrants=list(reversed(registrants)))
        )
    assert first == second


def test_registrant_evidence_level_changes_candidate_content(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    first = _accession_hash(
        db,
        registrant_plan(
            flag=True,
            registrants=[RegistrantPlan(cik=1), RegistrantPlan(cik=901, role="associated")],
        ),
    )
    with connect(tmp_path / "second.sqlite3", writer=True) as other:
        apply_migrations(other)
        _seed_reference_data(other)
        second = _accession_hash(
            other,
            registrant_plan(
                flag=True,
                registrants=[
                    RegistrantPlan(cik=1),
                    RegistrantPlan(cik=901, role="associated", evidence_level="conflicting"),
                ],
            ),
        )
    assert first != second


def test_submitter_only_rows_are_material_candidate_content(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    base = [RegistrantPlan(cik=1), RegistrantPlan(cik=901, role="associated")]
    first = _accession_hash(db, registrant_plan(flag=True, registrants=base))
    with connect(tmp_path / "second.sqlite3", writer=True) as other:
        apply_migrations(other)
        _seed_reference_data(other)
        second = _accession_hash(
            other,
            registrant_plan(
                flag=True, registrants=[*base, RegistrantPlan(cik=902, role="submitter_only")]
            ),
        )
    assert first != second


def _two_accession_registrant_plan(first_associate: int, second_associate: int) -> Plan:
    plan = minimal_plan()
    plan.accessions[0].multi_registrant = True
    plan.accessions[0].registrants = [
        RegistrantPlan(cik=1),
        RegistrantPlan(cik=first_associate, role="associated"),
    ]
    plan.accessions.append(
        AccessionPlan(
            cik=1,
            year=2021,
            seq=4,
            base_eligible=True,
            multi_registrant=True,
            registrants=[
                RegistrantPlan(cik=1),
                RegistrantPlan(cik=second_associate, role="associated"),
            ],
        )
    )
    return plan


def test_registrant_digest_is_paired_with_its_own_accession_identity(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    """Two accessions with swapped registrant content stay distinguishable (section 10)."""
    first = _accession_hash(db, _two_accession_registrant_plan(901, 902))
    with connect(tmp_path / "second.sqlite3", writer=True) as other:
        apply_migrations(other)
        _seed_reference_data(other)
        second = _accession_hash(other, _two_accession_registrant_plan(902, 901))
    assert first != second


# --------------------------------------------------------------------------
# 5: Decision 019 section 7 -- explicit pre-study support provenance
# --------------------------------------------------------------------------


def pre_study_plan(**overrides: object) -> Plan:
    plan = minimal_plan()
    support = AccessionPlan(
        cik=1,
        year=2009,
        seq=5,
        support_eligible=True,
        cohort=None,
        cohort_evidence_level="unavailable",
        has_xbrl=False,
        has_inline_xbrl=False,
        reasons=[("cohort", _PRE_STUDY)],
    )
    for key, value in overrides.items():
        setattr(support, key, value)
    plan.accessions.append(support)
    return plan


def test_the_exact_pre_study_conjunction_maps_to_pre_study(db: sqlite3.Connection) -> None:
    loaded = frozen(db, pre_study_plan())
    support = candidate(loaded, dashed(1, 2009, 5))
    assert support.cohort_applicability == "pre_study"
    assert support.cohort_evidence_level == NOT_APPLICABLE
    assert support.provisional_official_cohort is None


@pytest.mark.parametrize(
    ("overrides", "expected"),
    (
        ({"form": "10-KT"}, "not an original 10-K"),
        ({"year": 2010}, "is not in 2009"),
        ({"filing_date": "2010-03-15"}, "is not in 2009"),
        ({"filing_date_null": True}, "is not in 2009"),
        ({"filing_date": "2009-02-30"}, "is not in 2009"),
        ({"support_eligible": False}, "support_eligible = 0"),
        ({"cohort_ambiguous": True}, "cohort_ambiguous = 1"),
        ({"cohort": "development", "cohort_evidence_level": "provisional"}, "is not NULL"),
    ),
)
def test_each_pre_study_condition_failure_fails_closed(
    db: sqlite3.Connection, overrides: dict[str, object], expected: str
) -> None:
    write_plan(db, pre_study_plan(**overrides))
    with pytest.raises(GateFailureError, match=expected):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_the_marker_on_a_base_eligible_accession_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(
        db,
        pre_study_plan(
            base_eligible=True, cohort="development", cohort_evidence_level="provisional"
        ),
    )
    with pytest.raises(GateFailureError, match="base_eligible = 1"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_the_marker_on_an_amendment_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(
        db,
        pre_study_plan(
            form="10-K/A",
            is_amendment=True,
            linkage_state="unresolved_amendment",
            reasons=[("cohort", _PRE_STUDY), ("amendment", _UNRESOLVED_PARENT)],
        ),
    )
    with pytest.raises(GateFailureError, match="not an original 10-K"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_a_null_cohort_without_the_marker_stays_applicable(db: sqlite3.Connection) -> None:
    plan = pre_study_plan(reasons=[])
    loaded = frozen(db, plan)
    support = candidate(loaded, dashed(1, 2009, 5))
    assert support.cohort_applicability == "applies"
    assert support.cohort_evidence_level == "unavailable"
    assert support.provisional_official_cohort is None


def test_the_loader_never_manufactures_the_pre_study_marker(db: sqlite3.Connection) -> None:
    frozen(db, pre_study_plan(reasons=[]))
    assert (
        db.execute(
            "SELECT COUNT(*) FROM pilot_candidate_accession_reasons WHERE reason_code = ?",
            (_PRE_STUDY,),
        ).fetchone()[0]
        == 0
    )


def test_in_window_cohort_evidence_is_carried_through_unchanged(db: sqlite3.Connection) -> None:
    loaded = frozen(db, minimal_plan())
    only = loaded.accessions[0]
    assert only.cohort_applicability == "applies"
    assert only.cohort_evidence_level == "provisional"
    assert only.provisional_official_cohort == "development"


# --------------------------------------------------------------------------
# 6: Decision 019 section 8 -- former-name identity evidence
# --------------------------------------------------------------------------


def identity_plan(rows: list[IdentityEvidencePlan]) -> Plan:
    plan = minimal_plan()
    plan.entities[0].identity_evidence = rows
    return plan


def six(loaded: FrozenJointCandidateSet, cik: int = 1) -> tuple[object, ...]:
    evidence = next(
        entry.name_change for entry in loaded.entities if entry.cik_padded == f"{cik:010d}"
    )
    return (
        evidence.has_identity_evidence,
        evidence.evidence_role,
        evidence.evidence_level,
        evidence.former_name_record_parseable,
        evidence.has_prior_current_or_from_to,
        evidence.ticker_change_claimed,
    )


def test_branch_1_no_identity_rows(db: sqlite3.Connection) -> None:
    assert six(frozen(db, identity_plan([]))) == (
        False,
        "supporting",
        "unavailable",
        False,
        False,
        False,
    )


def test_branch_2_ticker_only(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        identity_plan(
            [IdentityEvidencePlan(source_field="ticker_change", evidence_role="supporting")]
        ),
    )
    assert six(loaded) == (True, "supporting", "unavailable", False, False, True)


@pytest.mark.parametrize(
    "payload",
    (
        canonical_former_name("Old Name", "New Name"),
        canonical_from_to("Old Name", "New Name"),
    ),
)
def test_branch_3_single_valid_winning_row(db: sqlite3.Connection, payload: str) -> None:
    loaded = frozen(db, identity_plan([IdentityEvidencePlan(canonical_observed_value=payload)]))
    assert six(loaded) == (True, "winning", "provisional", True, True, False)


@pytest.mark.parametrize(
    "payload",
    (
        canonical_former_name("Acme Corp", "ACME CORP"),
        canonical_former_name("Acme Corp", "Acme Corp"),
        canonical_former_name("", "Acme Corp"),
        canonical_from_to("Acme Corp", ""),
    ),
)
def test_branch_4_single_winning_row_failing_a_content_test(
    db: sqlite3.Connection, payload: str
) -> None:
    loaded = frozen(db, identity_plan([IdentityEvidencePlan(canonical_observed_value=payload)]))
    assert six(loaded) == (True, "winning", "review_required", False, False, False)


def test_branch_5_competing_rows_only(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        identity_plan(
            [
                IdentityEvidencePlan(
                    evidence_role="supporting",
                    canonical_observed_value=canonical_former_name("Old A", "New A"),
                    tag="a",
                ),
                IdentityEvidencePlan(
                    evidence_role="competing",
                    canonical_observed_value=canonical_former_name("Old B", "New B"),
                    tag="b",
                ),
            ]
        ),
    )
    assert six(loaded) == (True, "competing", "review_required", True, True, False)


def test_branch_5_supporting_rows_only(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        identity_plan(
            [
                IdentityEvidencePlan(
                    evidence_role="supporting",
                    canonical_observed_value=canonical_former_name("Old A", "New A"),
                    tag="a",
                )
            ]
        ),
    )
    assert six(loaded) == (True, "supporting", "review_required", True, True, False)


def test_branch_5_records_structure_not_contribution(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        identity_plan(
            [
                IdentityEvidencePlan(
                    evidence_role="competing",
                    canonical_observed_value=canonical_former_name("Same", "same"),
                    tag="a",
                )
            ]
        ),
    )
    assert six(loaded) == (True, "competing", "review_required", False, False, False)


def test_branch_6_two_distinct_winning_payloads(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        identity_plan(
            [
                IdentityEvidencePlan(
                    canonical_observed_value=canonical_former_name("Old A", "New A"), tag="a"
                ),
                IdentityEvidencePlan(
                    canonical_observed_value=canonical_former_name("Old B", "New B"), tag="b"
                ),
            ]
        ),
    )
    assert six(loaded) == (True, "winning", "conflicting", True, True, False)


def test_branch_6_reports_false_when_any_winning_payload_fails_content(
    db: sqlite3.Connection,
) -> None:
    loaded = frozen(
        db,
        identity_plan(
            [
                IdentityEvidencePlan(
                    canonical_observed_value=canonical_former_name("Old A", "New A"), tag="a"
                ),
                IdentityEvidencePlan(
                    canonical_observed_value=canonical_former_name("Same", "SAME"), tag="b"
                ),
            ]
        ),
    )
    assert six(loaded) == (True, "winning", "conflicting", False, False, False)


def test_competing_rows_never_override_a_single_valid_winning_row(
    db: sqlite3.Connection,
) -> None:
    loaded = frozen(
        db,
        identity_plan(
            [
                IdentityEvidencePlan(
                    canonical_observed_value=canonical_former_name("Old A", "New A"), tag="a"
                ),
                IdentityEvidencePlan(
                    evidence_role="competing",
                    canonical_observed_value=canonical_former_name("Old B", "New B"),
                    tag="b",
                ),
            ]
        ),
    )
    assert six(loaded) == (True, "winning", "provisional", True, True, False)


def test_the_ticker_flag_is_orthogonal_to_the_former_name_branch(db: sqlite3.Connection) -> None:
    loaded = frozen(
        db,
        identity_plan(
            [
                IdentityEvidencePlan(
                    canonical_observed_value=canonical_former_name("Old A", "New A"), tag="a"
                ),
                IdentityEvidencePlan(
                    source_field="ticker_change", evidence_role="competing", tag="t"
                ),
            ]
        ),
    )
    assert six(loaded) == (True, "winning", "provisional", True, True, True)


def test_byte_identical_duplicate_winning_rows_fail_closed(db: sqlite3.Connection) -> None:
    payload = canonical_former_name("Old A", "New A")
    write_plan(
        db,
        identity_plan(
            [
                IdentityEvidencePlan(canonical_observed_value=payload, tag="a"),
                IdentityEvidencePlan(canonical_observed_value=payload, tag="b"),
            ]
        ),
    )
    with pytest.raises(GateFailureError, match="byte-identical"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


@pytest.mark.parametrize(
    ("payload", "expected"),
    (
        (
            json.dumps({"current_name": "B", "prior_name": "A", "relationship": "prior_current"}),
            "canonical reserialization",
        ),
        (canonical_former_name(" Acme ", "New"), "not byte-identical to its normalized form"),
        (canonical_former_name("Acme Corp", "New"), "not byte-identical to its normalized"),
        (
            canonical_former_name(unicodedata.normalize("NFD", "Café"), "New"),
            "not byte-identical to its normalized",
        ),
        ('{"current_name":"B","prior_name":"A","relationship":"from_to"}', "does not match the"),
        (
            '{"current_name":"B","extra":"x","prior_name":"A","relationship":"prior_current"}',
            "key set",
        ),
        ('{"current_name":null,"prior_name":"A","relationship":"prior_current"}', "not a JSON"),
        ("not json at all", "strict JSON"),
        ('["a","b"]', "not a JSON object"),
        ("", "NULL or empty"),
    ),
)
def test_structurally_corrupt_former_name_payloads_fail_closed(
    db: sqlite3.Connection, payload: str, expected: str
) -> None:
    write_plan(db, identity_plan([IdentityEvidencePlan(canonical_observed_value=payload)]))
    with pytest.raises(GateFailureError, match=expected):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_null_former_name_payload_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(db, identity_plan([IdentityEvidencePlan(canonical_observed_value=None)]))
    with pytest.raises(GateFailureError, match="NULL or empty"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_identity_row_without_a_parsed_record_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(
        db,
        identity_plan(
            [
                IdentityEvidencePlan(
                    canonical_observed_value=canonical_former_name("Old", "New"),
                    parsed_record_id=None,
                )
            ]
        ),
    )
    with pytest.raises(GateFailureError, match="NULL parsed_record_id"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_unknown_identity_source_field_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(
        db, identity_plan([IdentityEvidencePlan(source_field="legal_name_history", tag="x")])
    )
    with pytest.raises(GateFailureError, match="unsupported at Stage S5"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_identity_dimension_accession_evidence_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    plan.accessions[0].identity_evidence = True
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="identity-dimension accession evidence"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_identity_scope_entity_reason_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    plan.entities[0].identity_reason = True
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="identity-scope entity reasons"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_identity_scope_accession_reason_fails_closed(db: sqlite3.Connection) -> None:
    plan = minimal_plan()
    plan.accessions[0].reasons = [("identity", "REVIEW_PILOT_SIC_UNMAPPED")]
    write_plan(db, plan)
    with pytest.raises(GateFailureError, match="identity-scope accession reasons"):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


@pytest.mark.parametrize(
    ("rows", "expected"),
    (
        (
            [
                IdentityEvidencePlan(source_field="ticker_change", tag="a"),
                IdentityEvidencePlan(source_field="ticker_change", tag="b"),
            ],
            "ticker_change",
        ),
        (
            [
                IdentityEvidencePlan(
                    source_field="ticker_change", canonical_observed_value='{"ticker":"ACME"}'
                )
            ],
            "non-NULL canonical_observed_value",
        ),
        (
            [IdentityEvidencePlan(source_field="ticker_change", parsed_record_id=None)],
            "NULL parsed_record_id",
        ),
    ),
)
def test_ticker_row_violations_fail_closed(
    db: sqlite3.Connection, rows: list[IdentityEvidencePlan], expected: str
) -> None:
    write_plan(db, identity_plan(rows))
    with pytest.raises(GateFailureError, match=expected):
        load_frozen_joint_candidates(db, _SNAPSHOT_ID)


def test_a_ticker_only_entity_never_contributes_to_the_name_change_quota(
    db: sqlite3.Connection,
) -> None:
    loaded = frozen(db, identity_plan([IdentityEvidencePlan(source_field="ticker_change")]))
    evidence = loaded.entities[0].name_change
    assert evidence.ticker_change_claimed is True
    assert evidence.evidence_level == "unavailable"
    assert evidence.former_name_record_parseable is False


# --------------------------------------------------------------------------
# 7: deterministic run identity (Decision 018 section 26; Decision 019 section 10)
# --------------------------------------------------------------------------


def identity_for(
    connection: sqlite3.Connection, plan: Plan, **overrides: object
) -> JointSelectionRunIdentity:
    loaded = frozen(connection, plan)
    keywords: dict[str, object] = {"node_limit": _NODE_LIMIT}
    keywords.update(overrides)
    return build_joint_selection_run_identity(loaded, **keywords)  # type: ignore[arg-type]


def identity_in_new_database(
    tmp_path: Path, name: str, plan: Plan, **overrides: object
) -> JointSelectionRunIdentity:
    with connect(tmp_path / name, writer=True) as other:
        apply_migrations(other)
        _seed_reference_data(other)
        return identity_for(other, plan, **overrides)


def test_run_identity_is_deterministic_across_databases(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    first = identity_for(db, feasible_plan())
    second = identity_in_new_database(tmp_path, "second.sqlite3", feasible_plan())
    assert first == second
    assert len(first.selection_run_id) == 64
    assert first.selection_run_id == first.selection_run_id.lower()


def test_repeated_identity_derivation_is_stable(db: sqlite3.Connection) -> None:
    loaded = frozen(db, feasible_plan())
    first = build_joint_selection_run_identity(loaded, node_limit=_NODE_LIMIT)
    second = build_joint_selection_run_identity(loaded, node_limit=_NODE_LIMIT)
    assert first == second


@pytest.mark.parametrize(
    "overrides",
    (
        {"node_limit": _NODE_LIMIT + 1},
        {"selection_seed": "some-other-seed"},
        {"selector_policy_version": "m23-joint-selector-policy-v2"},
        {"quota_policy_version": "m23-pilot-quota-policy-v2"},
    ),
)
def test_run_identity_is_sensitive_to_every_policy_input(
    db: sqlite3.Connection, tmp_path: Path, overrides: dict[str, object]
) -> None:
    baseline = identity_for(db, minimal_plan())
    changed = identity_in_new_database(tmp_path, "changed.sqlite3", minimal_plan(), **overrides)
    assert changed.selection_run_id != baseline.selection_run_id
    assert changed.selection_input_sha256 != baseline.selection_input_sha256


def test_a_non_positive_node_limit_is_rejected(db: sqlite3.Connection) -> None:
    loaded = frozen(db, minimal_plan())
    with pytest.raises(GateFailureError, match="positive integer"):
        build_joint_selection_run_identity(loaded, node_limit=0)


def test_acceptance_audit_date_is_material_run_identity_content(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    """Section 10: including an accession no section 5.9 check reads."""
    baseline = identity_for(db, minimal_plan())
    changed_plan = minimal_plan()
    changed_plan.accessions[0].acceptance_audit_date = "2020-03-16"
    changed = identity_in_new_database(tmp_path, "changed.sqlite3", changed_plan)
    assert changed.selection_run_id != baseline.selection_run_id


@pytest.mark.parametrize(
    "mutation",
    (
        "linkage",
        "reason",
        "registrant",
        "identity_evidence",
        "entity_reason",
        "pre_study",
    ),
)
def test_every_material_normalized_input_changes_the_run_identity(
    db: sqlite3.Connection, tmp_path: Path, mutation: str
) -> None:
    baseline_plan = amendment_plan()
    baseline_plan.accessions[0].registrants = [RegistrantPlan(cik=1)]
    changed_plan = amendment_plan()
    changed_plan.accessions[0].registrants = [RegistrantPlan(cik=1)]
    if mutation == "linkage":
        changed_plan.accessions[-1].linkage_state = "supplements_original"
    elif mutation == "reason":
        changed_plan.accessions[0].reasons = [("eligibility", "SUPPORT_ONLY")]
    elif mutation == "registrant":
        changed_plan.accessions[0].registrants = [
            RegistrantPlan(cik=1, evidence_level="review_required")
        ]
    elif mutation == "identity_evidence":
        changed_plan.entities[0].identity_evidence = [
            IdentityEvidencePlan(
                canonical_observed_value=canonical_former_name("Old", "New"), tag="a"
            )
        ]
    elif mutation == "entity_reason":
        changed_plan.entities[0].identity_evidence = [
            IdentityEvidencePlan(source_field="ticker_change", tag="t")
        ]
    else:
        changed_plan.accessions.append(
            AccessionPlan(
                cik=1,
                year=2009,
                seq=7,
                support_eligible=True,
                cohort=None,
                cohort_evidence_level="unavailable",
                has_xbrl=False,
                has_inline_xbrl=False,
                reasons=[("cohort", _PRE_STUDY)],
            )
        )
    baseline = identity_for(db, baseline_plan)
    changed = identity_in_new_database(tmp_path, "changed.sqlite3", changed_plan)
    assert changed.selection_run_id != baseline.selection_run_id


def test_row_insertion_order_does_not_change_the_run_identity(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    forward = feasible_plan()
    reversed_plan = feasible_plan()
    reversed_plan.entities.reverse()
    reversed_plan.accessions.reverse()
    for accession in reversed_plan.accessions:
        if accession.registrants:
            accession.registrants.reverse()
    for entity in reversed_plan.entities:
        entity.identity_evidence.reverse()
    baseline = identity_for(db, forward)
    permuted = identity_in_new_database(tmp_path, "permuted.sqlite3", reversed_plan)
    assert permuted == baseline


def test_the_s4_entity_only_draft_never_reaches_the_s5_identity(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    plan = feasible_plan()
    write_plan(db, plan)
    s4 = execute_and_persist_entity_selection(
        db, _SNAPSHOT_ID, occurred_at_utc=_AT, event_id="s4-event"
    )
    assert s4.run_state == "running"
    with_draft = build_joint_selection_run_identity(
        load_frozen_joint_candidates(db, _SNAPSHOT_ID), node_limit=_NODE_LIMIT
    )
    without_draft = identity_in_new_database(tmp_path, "clean.sqlite3", feasible_plan())
    assert with_draft == without_draft
    assert with_draft.selection_run_id != s4.selection_run_id
    assert with_draft.selection_input_sha256 != s4.selection_input_sha256


def test_the_input_schema_version_is_part_of_the_identity_record() -> None:
    assert ACCESSION_SELECTION_INPUT_SCHEMA_VERSION == "pilot-joint-selection-input/1.0"


# --------------------------------------------------------------------------
# 7b: stored-versus-derived candidate content (independent S5.2 review finding)
#
# Decision 018 section 3.4 makes the cohort dimension structurally inapplicable on a
# valid pre-study accession, and the amendment-purpose dimension structurally
# inapplicable on an original, so both derived pure-input values are
# ``not_applicable`` whatever the frozen row stores. The stage contract still requires
# the **complete** normalized frozen accession-candidate content in run identity, so
# the stored value must move the identity even though it moves nothing the selector
# sees. This mirrors the linkage pair, where the stored state and stored parent are
# already recorded beside their derived counterparts.
# --------------------------------------------------------------------------


def original_purpose_plan(stored_level: str) -> Plan:
    """A conforming snapshot whose single original stores ``stored_level``.

    An original carries no ``amendment_purpose_category``, so
    ``amendment_purpose_quota_eligible`` stays 0 and migration 0009's freeze trigger
    requires no amendment-purpose evidence row; every stored level is conforming.
    """
    plan = minimal_plan()
    plan.accessions[0].purpose_evidence_level = stored_level
    return plan


def pre_study_cohort_plan(stored_level: str) -> Plan:
    """A conforming snapshot with one valid Decision 019 section 7.2 pre-study accession."""
    plan = minimal_plan()
    plan.accessions.append(
        AccessionPlan(
            cik=1,
            year=2009,
            seq=7,
            support_eligible=True,
            cohort=None,
            cohort_evidence_level=stored_level,
            has_xbrl=False,
            has_inline_xbrl=False,
            reasons=[("cohort", _PRE_STUDY)],
        )
    )
    return plan


def loaded_and_identity(
    connection: sqlite3.Connection, plan: Plan
) -> tuple[FrozenJointCandidateSet, JointSelectionRunIdentity]:
    loaded = frozen(connection, plan)
    return loaded, build_joint_selection_run_identity(loaded, node_limit=_NODE_LIMIT)


def loaded_and_identity_in_new_database(
    tmp_path: Path, name: str, plan: Plan
) -> tuple[FrozenJointCandidateSet, JointSelectionRunIdentity]:
    with connect(tmp_path / name, writer=True) as other:
        apply_migrations(other)
        _seed_reference_data(other)
        return loaded_and_identity(other, plan)


def test_stored_amendment_purpose_evidence_level_is_material_run_identity_content(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    """Two conforming snapshots differing only in the stored level on an original."""
    baseline_set, baseline = loaded_and_identity(db, original_purpose_plan("unavailable"))
    changed_set, changed = loaded_and_identity_in_new_database(
        tmp_path, "changed.sqlite3", original_purpose_plan("conflicting")
    )
    number = dashed(1, 2020, 1)

    # Both load, and the derived pure input is structurally inapplicable in both.
    assert len(baseline_set.accessions) == len(changed_set.accessions) == 1
    assert candidate(baseline_set, number).amendment_purpose_evidence_level == NOT_APPLICABLE
    assert candidate(changed_set, number).amendment_purpose_evidence_level == NOT_APPLICABLE
    # The accepted S5.1 inputs are byte-equivalent; only the frozen row differs.
    assert baseline_set.accessions == changed_set.accessions
    assert baseline_set.entities == changed_set.entities
    assert baseline_set.entity_content_sha256 == changed_set.entity_content_sha256

    assert baseline_set.accession_content_sha256 != changed_set.accession_content_sha256
    assert baseline.selection_input_sha256 != changed.selection_input_sha256
    assert baseline.selection_run_id != changed.selection_run_id


def test_stored_cohort_evidence_level_is_material_run_identity_content(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    """Two conforming snapshots differing only in the stored level on a pre-study row."""
    baseline_set, baseline = loaded_and_identity(db, pre_study_cohort_plan("unavailable"))
    changed_set, changed = loaded_and_identity_in_new_database(
        tmp_path, "changed.sqlite3", pre_study_cohort_plan("review_required")
    )
    number = dashed(1, 2009, 7)

    assert len(baseline_set.accessions) == len(changed_set.accessions) == 2
    for loaded in (baseline_set, changed_set):
        pre_study = candidate(loaded, number)
        assert pre_study.cohort_applicability == "pre_study"
        assert pre_study.cohort_evidence_level == NOT_APPLICABLE
        assert pre_study.provisional_official_cohort is None
    assert baseline_set.accessions == changed_set.accessions
    assert baseline_set.entities == changed_set.entities
    assert baseline_set.entity_content_sha256 == changed_set.entity_content_sha256

    assert baseline_set.accession_content_sha256 != changed_set.accession_content_sha256
    assert baseline.selection_input_sha256 != changed.selection_input_sha256
    assert baseline.selection_run_id != changed.selection_run_id


@pytest.mark.parametrize("mutation", ("in_window_cohort_level", "amendment_purpose_level"))
def test_derived_evidence_levels_remain_material(
    db: sqlite3.Connection, tmp_path: Path, mutation: str
) -> None:
    """The fix adds stored values; it never displaces the derived ones.

    On an in-window accession and on an amendment the stored level *is* the derived
    level, so changing it must still move the identity.
    """
    if mutation == "in_window_cohort_level":
        baseline_plan = minimal_plan()
        changed_plan = minimal_plan()
        changed_plan.accessions[0].cohort_evidence_level = "review_required"
    else:
        baseline_plan = amendment_plan(purpose_category=None, purpose_evidence_level="unavailable")
        changed_plan = amendment_plan(
            purpose_category=None, purpose_evidence_level="review_required"
        )
    baseline = identity_for(db, baseline_plan)
    changed = identity_in_new_database(tmp_path, "changed.sqlite3", changed_plan)
    assert changed.selection_input_sha256 != baseline.selection_input_sha256
    assert changed.selection_run_id != baseline.selection_run_id


def test_the_stored_parent_identity_remains_material_where_the_derived_one_is_dropped(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    """Decision 019 section 5.5 drops the parent pointer; the stored value still counts."""

    def possible_amendment_plan(parent_seq: int) -> Plan:
        plan = minimal_plan()
        plan.accessions.append(AccessionPlan(cik=1, year=2019, seq=4, base_eligible=True))
        plan.accessions.append(
            AccessionPlan(
                cik=1,
                year=2021,
                seq=5,
                form="10-K/A",
                is_amendment=True,
                stress_eligible=True,
                linkage_state="possible_amendment_of",
                parent_plain=plain(1, 2020 if parent_seq == 1 else 2019, parent_seq),
                reasons=[("amendment", _UNRESOLVED_PARENT)],
            )
        )
        return plan

    baseline_set, baseline = loaded_and_identity(db, possible_amendment_plan(1))
    changed_set, changed = loaded_and_identity_in_new_database(
        tmp_path, "changed.sqlite3", possible_amendment_plan(4)
    )
    number = dashed(1, 2021, 5)
    for loaded in (baseline_set, changed_set):
        amendment = candidate(loaded, number)
        assert amendment.amendment_linkage_evidence_level == "review_required"
        assert amendment.provisional_parent_accession_dashed is None
    assert baseline_set.accessions == changed_set.accessions
    assert baseline.selection_input_sha256 != changed.selection_input_sha256
    assert baseline.selection_run_id != changed.selection_run_id


def test_operational_timestamps_stay_excluded_from_the_run_identity(
    db: sqlite3.Connection, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Decision 016 section 8: every ``recorded_at_utc`` and freeze timestamp is excluded."""
    baseline = identity_for(db, pre_study_cohort_plan("unavailable"))
    monkeypatch.setattr(sys.modules[__name__], "_AT", "2031-05-05T05:05:05Z")
    changed = identity_in_new_database(
        tmp_path, "changed.sqlite3", pre_study_cohort_plan("unavailable")
    )
    assert changed == baseline


def test_acceptance_audit_cohort_stays_immaterial_to_the_run_identity(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    """Decision 019 section 5.9.1: no rule reads it, and the correction did not add it."""
    changed_plan = minimal_plan()
    changed_plan.accessions[0].acceptance_audit_cohort = "monitoring"
    baseline = identity_for(db, minimal_plan())
    changed = identity_in_new_database(tmp_path, "changed.sqlite3", changed_plan)
    assert changed == baseline


def test_accession_content_columns_are_exactly_the_authorized_set() -> None:
    """Pins the hashed column list so no unauthorized column silently becomes material."""
    assert accession_selection_store._ACCESSION_CONTENT_COLUMNS == (  # noqa: SLF001
        "accession_plain",
        "accession_number_dashed",
        "anchor_cik_padded",
        "form_type",
        "is_amendment",
        "official_filing_date",
        "report_date",
        "acceptance_audit_date",
        "cohort_applicability",
        "provisional_official_cohort",
        "cohort_ambiguous",
        "filing_date_evidence_level",
        "cohort_evidence_level",
        "stored_cohort_evidence_level",
        "xbrl_evidence_level",
        "amendment_purpose_evidence_level",
        "stored_amendment_purpose_evidence_level",
        "amendment_linkage_evidence_level",
        "multi_registrant_evidence_level",
        "has_xbrl",
        "has_inline_xbrl",
        "stored_amendment_linkage_state",
        "stored_provisional_parent_accession",
        "provisional_parent_accession_dashed",
        "amendment_purpose_category",
        "amendment_purpose_quota_eligible",
        "base_eligible",
        "stress_eligible",
        "support_eligible",
        "control_eligible",
        "multi_registrant",
        "registrant_content_sha256",
    )
    for excluded in (
        "acceptance_audit_cohort",
        "filing_date_precedence",
        "filing_date_resolution_sha256",
        "cohort_resolution_sha256",
        "xbrl_resolution_sha256",
        "amendment_purpose_resolution_sha256",
        "recorded_at_utc",
        "detail",
    ):
        assert excluded not in accession_selection_store._ACCESSION_CONTENT_COLUMNS  # noqa: SLF001


def varied_stored_levels_plan() -> Plan:
    """Four accessions whose stored evidence levels differ from one another."""
    plan = minimal_plan()
    plan.accessions[0].purpose_evidence_level = "conflicting"
    plan.accessions.append(
        AccessionPlan(
            cik=1, year=2019, seq=4, base_eligible=True, purpose_evidence_level="unproven"
        )
    )
    for seq, stored in ((7, "unavailable"), (8, "review_required")):
        plan.accessions.append(
            AccessionPlan(
                cik=1,
                year=2009,
                seq=seq,
                support_eligible=True,
                cohort=None,
                cohort_evidence_level=stored,
                has_xbrl=False,
                has_inline_xbrl=False,
                reasons=[("cohort", _PRE_STUDY)],
            )
        )
    return plan


def test_row_permutation_stays_invariant_across_varied_stored_levels(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    """The added fields are per-row content, so ``hash_table``'s sort still absorbs order."""
    reversed_plan = varied_stored_levels_plan()
    reversed_plan.accessions.reverse()
    baseline = identity_for(db, varied_stored_levels_plan())
    permuted = identity_in_new_database(tmp_path, "permuted.sqlite3", reversed_plan)
    assert permuted == baseline


def test_the_pure_result_is_unchanged_when_only_stored_inapplicable_values_change(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    """A stored structurally inapplicable value moves the identity and nothing else."""
    changed_plan = feasible_plan()
    changed_plan.accession(dashed(1, 2009, 1)).cohort_evidence_level = "review_required"
    changed_plan.accession(dashed(1, 2010, 2)).purpose_evidence_level = "conflicting"

    baseline_set, baseline = loaded_and_identity(db, feasible_plan())
    changed_set, changed = loaded_and_identity_in_new_database(
        tmp_path, "changed.sqlite3", changed_plan
    )
    assert baseline_set.accessions == changed_set.accessions
    assert baseline_set.entities == changed_set.entities

    first = solve_joint_selection(
        baseline_set.entities, baseline_set.accessions, node_limit=_NODE_LIMIT
    )
    second = solve_joint_selection(
        changed_set.entities, changed_set.accessions, node_limit=_NODE_LIMIT
    )
    assert first.status == "feasible"
    assert first == second
    assert baseline.selection_run_id != changed.selection_run_id


# --------------------------------------------------------------------------
# 8: persistence, reconstruction, idempotence, and lifecycle gates
# --------------------------------------------------------------------------


def run_once(
    connection: sqlite3.Connection,
    *,
    node_limit: int = _NODE_LIMIT,
    occurred_at_utc: str = _AT,
    event_id: str = "event-1",
) -> PersistedJointSelectionResult:
    return execute_and_persist_joint_selection(
        connection,
        _SNAPSHOT_ID,
        node_limit=node_limit,
        occurred_at_utc=occurred_at_utc,
        event_id=event_id,
    )


def test_feasible_run_persists_a_complete_result(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    assert persisted.run_state == "feasible"
    assert persisted.result.status == "feasible"
    assert persisted.selected_entity_count == 24
    assert persisted.selected_accession_count == len(persisted.result.selected_accessions)
    assert persisted.node_limit == _NODE_LIMIT
    assert persisted.node_limit_exhausted is False
    assert persisted.expanded_node_count == persisted.result.expanded_node_count
    assert persisted.selector_policy_version == pilot_policy.PILOT_JOINT_SELECTOR_POLICY_VERSION
    assert persisted.quota_policy_version == pilot_policy.PILOT_QUOTA_POLICY_VERSION
    assert persisted.selection_seed == PILOT_SELECTION_SEED

    row = db.execute(
        "SELECT run_state, selector_policy_version, node_limit_exhausted, selection_result_sha256, "
        "search_node_limit FROM pilot_selection_runs WHERE selection_run_id = ?",
        (persisted.selection_run_id,),
    ).fetchone()
    assert row["run_state"] == "feasible"
    assert row["selector_policy_version"] == "m23-joint-selector-policy-v1"
    assert row["node_limit_exhausted"] == 0
    assert row["selection_result_sha256"] is None
    assert row["search_node_limit"] == _NODE_LIMIT


def test_selected_accession_order_is_the_frozen_decision_018_key(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    rows = db.execute(
        "SELECT accession_plain, anchor_cik_numeric, selected_order, accession_hash_sha256 "
        "FROM pilot_selected_accessions WHERE selection_run_id = ? ORDER BY selected_order",
        (persisted.selection_run_id,),
    ).fetchall()
    assert [row["selected_order"] for row in rows] == list(range(1, len(rows) + 1))
    keys = [
        (
            row["accession_hash_sha256"],
            f"{row['anchor_cik_numeric']:010d}",
            f"{row['accession_plain'][:10]}-{row['accession_plain'][10:12]}-"
            f"{row['accession_plain'][12:]}",
        )
        for row in rows
    ]
    assert keys == sorted(keys)
    assert [key[0] for key in keys] == [
        accession_selection_rank(key[1], key[2], PILOT_SELECTION_SEED) for key in keys
    ]


def test_selected_accession_roles_are_persisted_exactly(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    rows = db.execute(
        "SELECT accession_plain, accession_role FROM pilot_selected_accessions "
        "WHERE selection_run_id = ?",
        (persisted.selection_run_id,),
    ).fetchall()
    by_plain = {row["accession_plain"]: row["accession_role"] for row in rows}
    counts: dict[str, int] = {}
    for role in by_plain.values():
        counts[role] = counts.get(role, 0) + 1
    assert counts == {"support": 6, "base": 20, "stress": 8, "control": 4}
    assert by_plain[plain(1, 2009, 1)] == "support"
    assert by_plain[plain(1, 2010, 2)] == "base"
    assert by_plain[plain(1, 2011, 3)] == "stress"
    assert by_plain[plain(101, 2020, 2)] == "control"
    for selected in persisted.result.selected_accessions:
        assert by_plain[selected.accession_plain] == selected.accession_role


def test_quota_results_are_persisted_once_each_including_the_deferred_row(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    rows = db.execute(
        "SELECT quota_dimension, quota_key, comparison_operator, required_count, achieved_count, "
        "eligible_pool_count, excluded_pool_count, evidence_state, quota_result "
        "FROM pilot_quota_results WHERE selection_run_id = ?",
        (persisted.selection_run_id,),
    ).fetchall()
    keys = [(row["quota_dimension"], row["quota_key"]) for row in rows]
    assert len(keys) == len(set(keys))
    expected = {(d.dimension, d.key) for d in persisted.result.entity_quota_results} | {
        (d.dimension, d.key) for d in persisted.result.accession_quota_results
    }
    assert set(keys) == expected

    deferred = next(row for row in rows if row["quota_key"] == DEFERRED_QUOTA_KEY)
    assert deferred["quota_dimension"] == QUOTA_DIMENSION_CROSS_CUTTING
    assert deferred["quota_result"] == "unproven"
    assert deferred["evidence_state"] == "unavailable"
    assert deferred["achieved_count"] == 0
    assert deferred["eligible_pool_count"] == 0
    assert deferred["required_count"] == 6

    caps = [row for row in rows if row["quota_dimension"] == QUOTA_DIMENSION_ACCESSION_CAP]
    assert len(caps) == 4
    assert all(row["comparison_operator"] == "at_most" for row in caps)
    assert all(row["quota_result"] == "pass" for row in caps)


def test_reconstruction_round_trips_the_pure_result(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    again = reconstruct_persisted_joint_selection(db, persisted.selection_run_id)
    assert again == persisted
    assert again.result == persisted.result
    assert again.result.objective == persisted.result.objective


def test_reconstruction_is_independent_of_sqlite_retrieval_order(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    orders = [
        reconstruct_persisted_joint_selection(db, persisted.selection_run_id).result
        for _ in range(3)
    ]
    assert orders[0] == orders[1] == orders[2] == persisted.result


def test_a_second_identical_invocation_is_idempotent(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    first = run_once(db)
    counts_before = _result_row_counts(db)
    second = run_once(db, occurred_at_utc="2026-02-02T00:00:00Z", event_id="event-2")
    assert second.selection_run_id == first.selection_run_id
    assert second == first
    assert _result_row_counts(db) == counts_before
    assert db.execute("SELECT COUNT(*) FROM pilot_selection_runs").fetchone()[0] == 1


def _result_row_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
        for table in (
            "pilot_selection_runs",
            "pilot_selection_run_events",
            "pilot_selected_entities",
            "pilot_selected_accessions",
            "pilot_quota_results",
            "pilot_quota_result_members",
            "pilot_selected_entity_quota_contributions",
            "pilot_selected_accession_quota_contributions",
            "pilot_reserves",
            "pilot_reserve_accessions",
            "pilot_reserve_quota_contributions",
            "pilot_selection_entity_reasons",
        )
    }


def test_audit_metadata_never_enters_the_run_identity(
    db: sqlite3.Connection, tmp_path: Path
) -> None:
    write_plan(db, feasible_plan())
    first = run_once(db, occurred_at_utc="2026-01-01T00:00:00Z", event_id="event-a")
    with connect(tmp_path / "second.sqlite3", writer=True) as other:
        apply_migrations(other)
        _seed_reference_data(other)
        write_plan(other, feasible_plan())
        second = execute_and_persist_joint_selection(
            other,
            _SNAPSHOT_ID,
            node_limit=_NODE_LIMIT,
            occurred_at_utc="2030-12-31T23:59:59Z",
            event_id="event-b",
        )
    assert second.selection_run_id == first.selection_run_id
    assert second.selection_input_sha256 == first.selection_input_sha256


def test_a_conflicting_same_id_replay_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    _corrupt_stored_run_identity(
        db,
        "UPDATE pilot_selection_runs SET selection_input_sha256 = ? WHERE selection_run_id = ?",
        ("0" * 64, persisted.selection_run_id),
    )
    with pytest.raises(GateFailureError, match="refusing to overwrite"):
        run_once(db)


@pytest.mark.parametrize("state", ("planned", "running", "failed"))
def test_every_unusable_same_id_state_gate_fails(db: sqlite3.Connection, state: str) -> None:
    write_plan(db, feasible_plan())
    identity = build_joint_selection_run_identity(
        load_frozen_joint_candidates(db, _SNAPSHOT_ID), node_limit=_NODE_LIMIT
    )
    _insert_run_in_state(db, identity, state)
    with pytest.raises(GateFailureError, match="Decision 018 section 18"):
        run_once(db)
    assert (
        db.execute(
            "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?",
            (identity.selection_run_id,),
        ).fetchone()["run_state"]
        == state
    )
    assert db.execute("SELECT COUNT(*) FROM pilot_selection_runs").fetchone()[0] == 1


def _insert_run_in_state(
    connection: sqlite3.Connection, identity: JointSelectionRunIdentity, state: str
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_selection_runs "
            "(selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
            "quota_policy_version, search_node_limit, run_state, selection_input_sha256, "
            "started_at_utc) VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?)",
            (
                identity.selection_run_id,
                identity.snapshot_id,
                identity.selection_seed,
                identity.selector_policy_version,
                identity.quota_policy_version,
                identity.node_limit,
                identity.selection_input_sha256,
                _AT,
            ),
        )
        if state == "planned":
            return
        c.execute(
            "INSERT INTO pilot_selection_run_events "
            "(event_id, selection_run_id, snapshot_id, from_state, to_state, attempt_number, "
            "occurred_at_utc) VALUES ('preexisting', ?, ?, 'planned', 'running', 1, ?)",
            (identity.selection_run_id, identity.snapshot_id, _AT),
        )
        c.execute(
            "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
            (identity.selection_run_id,),
        )
        if state == "failed":
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'failed', finished_at_utc = ? "
                "WHERE selection_run_id = ?",
                (_AT, identity.selection_run_id),
            )


def test_no_retry_entry_point_exists() -> None:
    exported = set(accession_selection_store.__all__)
    assert not any("retry" in name.lower() for name in exported)
    assert not any(
        "retry" in name.lower()
        for name in dir(accession_selection_store)
        if callable(getattr(accession_selection_store, name, None))
    )


def test_infeasible_run_persists_no_selected_or_quota_rows(db: sqlite3.Connection) -> None:
    write_plan(db, minimal_plan())
    persisted = run_once(db)
    assert persisted.run_state == "infeasible"
    assert persisted.result.status == "infeasible"
    assert persisted.result.selected_accessions == ()
    assert persisted.result.objective is None
    assert persisted.selected_entity_count == 0
    assert persisted.selected_accession_count == 0
    counts = _result_row_counts(db)
    assert counts["pilot_selected_entities"] == 0
    assert counts["pilot_selected_accessions"] == 0
    assert counts["pilot_quota_results"] == 0
    row = db.execute(
        "SELECT failure_reason_code, node_limit_exhausted FROM pilot_selection_runs "
        "WHERE selection_run_id = ?",
        (persisted.selection_run_id,),
    ).fetchone()
    assert row["failure_reason_code"] == "PILOT_SELECTION_INFEASIBLE"
    assert row["node_limit_exhausted"] == 0


def test_node_limit_exhaustion_persists_no_selection(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db, node_limit=1)
    assert persisted.run_state == "infeasible_or_unproven"
    assert persisted.node_limit_exhausted is True
    assert persisted.result.selected_accessions == ()
    assert persisted.result.selected_operating == ()
    assert persisted.result.objective is None
    counts = _result_row_counts(db)
    assert counts["pilot_selected_entities"] == 0
    assert counts["pilot_selected_accessions"] == 0
    assert counts["pilot_quota_results"] == 0
    row = db.execute(
        "SELECT failure_reason_code, node_limit_exhausted FROM pilot_selection_runs "
        "WHERE selection_run_id = ?",
        (persisted.selection_run_id,),
    ).fetchone()
    assert row["failure_reason_code"] == "PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN"
    assert row["node_limit_exhausted"] == 1


def test_an_injected_failure_rolls_the_whole_attempt_back(
    db: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_plan(db, feasible_plan())

    def explode(*_args: object, **_keywords: object) -> None:
        message = "injected persistence failure"
        raise RuntimeError(message)

    monkeypatch.setattr(accession_selection_store, "_insert_quota_result", explode)
    with pytest.raises(RuntimeError, match="injected persistence failure"):
        run_once(db)
    assert _result_row_counts(db) == dict.fromkeys(_result_row_counts(db), 0)


def test_the_s4_draft_is_never_used_as_an_input_or_mutated(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    s4 = execute_and_persist_entity_selection(
        db, _SNAPSHOT_ID, occurred_at_utc=_AT, event_id="s4-event"
    )
    before = tuple(
        db.execute(
            "SELECT * FROM pilot_selection_runs WHERE selection_run_id = ?", (s4.selection_run_id,)
        ).fetchone()
    )
    persisted = run_once(db)
    after = tuple(
        db.execute(
            "SELECT * FROM pilot_selection_runs WHERE selection_run_id = ?", (s4.selection_run_id,)
        ).fetchone()
    )
    assert after == before
    assert persisted.selection_run_id != s4.selection_run_id
    assert persisted.run_state == "feasible"
    assert (
        db.execute(
            "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?",
            (s4.selection_run_id,),
        ).fetchone()["run_state"]
        == "running"
    )


def test_no_manifest_reserve_or_publication_row_is_written(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    run_once(db)
    for table in (
        "pilot_manifest_versions",
        "pilot_reserves",
        "pilot_reserve_accessions",
        "pilot_reserve_quota_contributions",
        "pilot_projection_recovery_events",
    ):
        assert connection_count(db, table) == 0


def connection_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608


def test_exactly_one_lifecycle_event_is_recorded_per_attempt(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    rows = db.execute(
        "SELECT from_state, to_state, attempt_number FROM pilot_selection_run_events "
        "WHERE selection_run_id = ?",
        (persisted.selection_run_id,),
    ).fetchall()
    assert [(row["from_state"], row["to_state"], row["attempt_number"]) for row in rows] == [
        ("planned", "running", 1)
    ]


@pytest.mark.parametrize(
    ("column", "value", "expected"),
    (
        ("expanded_node_count", 999_999, "expanded_node_count"),
        ("selected_accession_count", 3, "declares"),
        ("selector_policy_version", "tampered/1.0", "does not match the identity re-derived"),
        ("search_node_limit", 4242, "does not match the identity re-derived"),
        ("selection_seed", "tampered-seed", "does not match the identity re-derived"),
    ),
)
def test_persisted_corruption_is_detected_on_reconstruction(
    db: sqlite3.Connection, column: str, value: object, expected: str
) -> None:
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    with transaction(db) as c:
        c.execute(
            f"UPDATE pilot_selection_runs SET {column} = ? WHERE selection_run_id = ?",  # noqa: S608
            (value, persisted.selection_run_id),
        )
    with pytest.raises(GateFailureError, match=expected):
        reconstruct_persisted_joint_selection(db, persisted.selection_run_id)


def test_reconstructing_an_unknown_run_fails_closed(db: sqlite3.Connection) -> None:
    with pytest.raises(GateFailureError, match="no pilot selection run exists"):
        reconstruct_persisted_joint_selection(db, "f" * 64)


def test_reconstructing_an_incomplete_run_fails_closed(db: sqlite3.Connection) -> None:
    write_plan(db, feasible_plan())
    identity = build_joint_selection_run_identity(
        load_frozen_joint_candidates(db, _SNAPSHOT_ID), node_limit=_NODE_LIMIT
    )
    _insert_run_in_state(db, identity, "planned")
    with pytest.raises(GateFailureError, match="carries no complete persisted result"):
        reconstruct_persisted_joint_selection(db, identity.selection_run_id)


def test_composite_foreign_keys_reject_an_unanchored_selected_accession(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, feasible_plan())
    identity = build_joint_selection_run_identity(
        load_frozen_joint_candidates(db, _SNAPSHOT_ID), node_limit=_NODE_LIMIT
    )
    _insert_run_in_state(db, identity, "running")
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), transaction(db) as c:
        c.execute(
            "INSERT INTO pilot_selected_accessions "
            "(selection_run_id, snapshot_id, accession_plain, anchor_cik_numeric, selected_order, "
            "accession_hash_sha256, accession_role, recorded_at_utc) "
            "VALUES (?, ?, ?, 1, 1, ?, 'base', ?)",
            (
                identity.selection_run_id,
                identity.snapshot_id,
                plain(1, 2010, 2),
                _hex("hash"),
                _AT,
            ),
        )


def test_migration_0011_seeds_the_exact_joint_selector_policy_row(db: sqlite3.Connection) -> None:
    row = db.execute(
        "SELECT policy_version, decision_record FROM reference_policy_versions "
        "WHERE policy_key = 'pilot_joint_selector'"
    ).fetchone()
    assert row is not None
    assert row["policy_version"] == pilot_policy.PILOT_JOINT_SELECTOR_POLICY_VERSION
    assert row["policy_version"] == "m23-joint-selector-policy-v1"
    assert row["decision_record"] == (
        "Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md"
    )
    s4_row = db.execute(
        "SELECT policy_version FROM reference_policy_versions WHERE policy_key = 'pilot_selector'"
    ).fetchone()
    assert s4_row["policy_version"] == pilot_policy.PILOT_SELECTOR_POLICY_VERSION
    assert s4_row["policy_version"] == "deterministic-constrained/1.0"


# --------------------------------------------------------------------------
# 9: same-ID stored-versus-derived identity integrity (independent S5.3 finding)
#
# Decision 018 section 18 makes a same-ID terminal run idempotently reusable only when
# the values it recorded are the ones that produced it. Both public entry points must
# therefore refuse the *same* stored corruption. Before this section existed, the
# idempotent branch of ``execute_and_persist_joint_selection`` supplied its own freshly
# derived identity to ``_reconstruct``, so a directly mutated stored
# ``selector_policy_version``, ``quota_policy_version``, or ``search_node_limit`` was
# accepted there while ``reconstruct_persisted_joint_selection`` rejected it.
#
# ``pilot_selection_runs`` carries no immutable-write trigger on its non-state columns
# (migration 0009 guards ``run_state`` transitions and the child result tables), so these
# tests plant their corruption with a plain UPDATE and remove no guard.
# --------------------------------------------------------------------------


#: Every stored column the content-derived identity is built from, with a value that is
#: schema-valid but wrong. ``selection_seed`` and ``selection_input_sha256`` already
#: failed closed on both paths; they are kept here so a future change cannot regress
#: them while the three that did not are fixed.
IDENTITY_COLUMN_TAMPERS: Final[tuple[tuple[str, object], ...]] = (
    ("selector_policy_version", "tampered-selector/9.9"),
    ("quota_policy_version", "tampered-quota/9.9"),
    ("selection_seed", "tampered-seed"),
    ("search_node_limit", 4242),
    ("selection_input_sha256", "0" * 64),
)


def whole_database(connection: sqlite3.Connection) -> dict[str, list[tuple[object, ...]]]:
    """Every row of every pilot table, ordered deterministically for exact comparison."""
    tables = [
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'pilot_%' "
            "ORDER BY name"
        ).fetchall()
    ]
    return {
        table: sorted(
            tuple(row)
            for row in connection.execute(f"SELECT * FROM {table}").fetchall()  # noqa: S608
        )
        for table in tables
    }


def tampered_run(connection: sqlite3.Connection, column: str, value: object) -> str:
    """Persist a valid feasible run, then mutate one stored identity column.

    ``selection_input_sha256`` is one of the three columns migration 0013 trigger 8
    holds immutable, so the mutation is applied through
    :func:`_corrupt_stored_run_identity`. The other four parametrized columns are
    not named by that trigger and need no bypass, but they take the same path so
    this helper keeps one code path and every parametrization reaches both public
    paths below with the guard reinstalled.
    """
    write_plan(connection, feasible_plan())
    persisted = run_once(connection)
    assert persisted.run_state == "feasible"
    _corrupt_stored_run_identity(
        connection,
        f"UPDATE pilot_selection_runs SET {column} = ? WHERE selection_run_id = ?",  # noqa: S608
        (value, persisted.selection_run_id),
    )
    return persisted.selection_run_id


@pytest.mark.parametrize(("column", "value"), IDENTITY_COLUMN_TAMPERS)
def test_both_public_paths_reject_a_tampered_stored_identity_column(
    db: sqlite3.Connection, column: str, value: object
) -> None:
    """The designated reconstruction path and the idempotent replay path agree."""
    selection_run_id = tampered_run(db, column, value)
    with pytest.raises(GateFailureError):
        reconstruct_persisted_joint_selection(db, selection_run_id)
    with pytest.raises(GateFailureError):
        run_once(db, occurred_at_utc="2027-03-03T00:00:00Z", event_id="replay")


@pytest.mark.parametrize(("column", "value"), IDENTITY_COLUMN_TAMPERS)
def test_a_rejected_tampered_replay_changes_nothing(
    db: sqlite3.Connection, column: str, value: object
) -> None:
    """No new run, no attempt event, no replacement ID, no rewritten row."""
    selection_run_id = tampered_run(db, column, value)
    before = whole_database(db)
    with pytest.raises(GateFailureError):
        run_once(db, occurred_at_utc="2027-03-03T00:00:00Z", event_id="replay")
    assert whole_database(db) == before
    assert db.execute("SELECT COUNT(*) FROM pilot_selection_runs").fetchone()[0] == 1
    assert (
        db.execute("SELECT selection_run_id FROM pilot_selection_runs").fetchone()[
            "selection_run_id"
        ]
        == selection_run_id
    )
    events = db.execute(
        "SELECT from_state, to_state, attempt_number FROM pilot_selection_run_events"
    ).fetchall()
    assert [(e["from_state"], e["to_state"], e["attempt_number"]) for e in events] == [
        ("planned", "running", 1)
    ]


def test_both_paths_reject_a_run_that_no_longer_derives_its_own_run_id(
    db: sqlite3.Connection,
) -> None:
    """A self-consistent forgery: tampered seed plus the digest that seed really yields.

    The stored input hash now agrees with a re-derivation under the tampered seed, so the
    digest comparison alone would pass; only the run ID still disagrees.
    """
    write_plan(db, feasible_plan())
    persisted = run_once(db)
    forged = build_joint_selection_run_identity(
        load_frozen_joint_candidates(db, _SNAPSHOT_ID),
        node_limit=_NODE_LIMIT,
        selection_seed="tampered-seed",
    )
    assert forged.selection_run_id != persisted.selection_run_id
    assert forged.selection_input_sha256 != persisted.selection_input_sha256
    _corrupt_stored_run_identity(
        db,
        "UPDATE pilot_selection_runs SET selection_seed = ?, selection_input_sha256 = ? "
        "WHERE selection_run_id = ?",
        ("tampered-seed", forged.selection_input_sha256, persisted.selection_run_id),
    )
    with pytest.raises(GateFailureError, match="selection_run_id"):
        reconstruct_persisted_joint_selection(db, persisted.selection_run_id)
    with pytest.raises(GateFailureError):
        run_once(db, occurred_at_utc="2027-03-03T00:00:00Z", event_id="replay")
    assert db.execute("SELECT COUNT(*) FROM pilot_selection_runs").fetchone()[0] == 1


def test_the_identity_comparison_covers_every_field_of_the_identity_record() -> None:
    """Pins the comparison to the real dataclass, so a new identity field is not missed."""
    names = tuple(entry.name for entry in fields(JointSelectionRunIdentity))
    assert names == (
        "snapshot_id",
        "selection_seed",
        "selector_policy_version",
        "quota_policy_version",
        "node_limit",
        "selection_input_sha256",
        "selection_run_id",
    )
    stored = JointSelectionRunIdentity(
        snapshot_id=_SNAPSHOT_ID,
        selection_seed=PILOT_SELECTION_SEED,
        selector_policy_version=pilot_policy.PILOT_JOINT_SELECTOR_POLICY_VERSION,
        quota_policy_version=pilot_policy.PILOT_QUOTA_POLICY_VERSION,
        node_limit=_NODE_LIMIT,
        selection_input_sha256=_hex("input"),
        selection_run_id=_hex("run"),
    )
    accession_selection_store._require_stored_identity_matches(stored, stored)  # noqa: SLF001
    replacements: dict[str, object] = {
        "snapshot_id": "b" * 64,
        "selection_seed": "other-seed",
        "selector_policy_version": "other-selector/1.0",
        "quota_policy_version": "other-quota/1.0",
        "node_limit": _NODE_LIMIT + 1,
        "selection_input_sha256": _hex("other-input"),
        "selection_run_id": _hex("other-run"),
    }
    assert set(replacements) == set(names)
    for field_name, replacement in replacements.items():
        derived = replace(stored, **{field_name: replacement})
        with pytest.raises(GateFailureError, match=field_name):
            accession_selection_store._require_stored_identity_matches(stored, derived)  # noqa: SLF001


def test_an_untampered_completed_run_still_replays_and_reconstructs(
    db: sqlite3.Connection,
) -> None:
    """The fix refuses corruption only; a valid terminal run is unchanged in every way."""
    write_plan(db, feasible_plan())
    first = run_once(db)
    counts_before = _result_row_counts(db)
    state_before = whole_database(db)

    replayed = run_once(db, occurred_at_utc="2027-04-04T00:00:00Z", event_id="replay")
    rebuilt = reconstruct_persisted_joint_selection(db, first.selection_run_id)

    assert replayed == first
    assert rebuilt == first
    assert isinstance(replayed.result, JointSelectionResult)
    assert replayed.result == first.result == rebuilt.result
    assert replayed.result.status == "feasible"
    assert replayed.selection_seed == first.selection_seed
    assert replayed.selector_policy_version == pilot_policy.PILOT_JOINT_SELECTOR_POLICY_VERSION
    assert replayed.quota_policy_version == pilot_policy.PILOT_QUOTA_POLICY_VERSION
    assert replayed.node_limit == _NODE_LIMIT
    assert _result_row_counts(db) == counts_before
    assert whole_database(db) == state_before


# --------------------------------------------------------------------------
# 12: Stage S5.4 -- contribution, member, reserve, and disposition persistence
# --------------------------------------------------------------------------
#
# Decision 020 sections 5 and 10. Migration 0009 refuses every contribution,
# member, and reserve write once a run leaves ``running`` and refuses
# ``feasible -> running`` outright, so all of this lands inside the single
# existing transaction with the terminal transition as its last statement.


def reserve_plan() -> Plan:
    """The accepted feasible pool plus one spare operating candidate.

    Twenty-one operating candidates compete for twenty slots, so exactly one is
    left unselected and becomes a compatible replacement for the entities sharing
    its stratum -- a run with **both** reserve packages and no-compatible-reserve
    dispositions, which is what the migration-0012 trigger requires to be total.
    """
    plan = feasible_plan()
    plan.entities.append(
        EntityPlan(
            cik=200,
            size=SIZE_SEQUENCE[18],
            industry=INDUSTRY_SEQUENCE[18],
            history=HISTORY_SEQUENCE[18],
        )
    )
    plan.accessions.append(AccessionPlan(cik=200, year=2018, seq=2, base_eligible=True))
    return plan


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple[object, ...]]:
    return sorted(
        tuple(row)
        for row in connection.execute(f"SELECT * FROM {table}").fetchall()  # noqa: S608
    )


def _count(connection: sqlite3.Connection, table: str) -> int:
    value = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
    assert isinstance(value, int)
    return value


def _database_path(connection: sqlite3.Connection) -> str:
    row = connection.execute("PRAGMA database_list").fetchone()
    return str(row["file"])


def _require_scratch_catalog(path: str) -> str:
    """Refuse to hand back anything but a catalog this suite itself created.

    The two helpers below deliberately remove a lifecycle guard, so they must be
    structurally incapable of running against a real catalog. This is an allowlist
    rather than a location test: a path qualifies only because the ``db`` fixture
    built it for the running test and registered it in :data:`_SCRATCH_CATALOGS`.
    A repository or production catalog can never be in that set, and, unlike a
    check against the interpreter's temporary root, this holds under ``--basetemp``,
    ``PYTEST_DEBUG_TEMPROOT``, a relocated ``TMPDIR``, and xdist alike.
    """
    resolved = Path(path).resolve()
    if resolved not in _SCRATCH_CATALOGS:
        message = (
            f"refusing to disable a lifecycle guard on {resolved}: corruption fixtures "
            "run only against a throwaway catalog created by this suite's own fixture"
        )
        raise AssertionError(message)
    return str(resolved)


def _corrupt_stored_run_identity(
    connection: sqlite3.Connection, sql: str, parameters: tuple[object, ...]
) -> None:
    """Rewrite a stored ``pilot_selection_runs`` identity column out of band.

    Migration 0013 trigger 8 ``pilot_selection_run_identity_guard`` makes
    ``selection_run_id``, ``snapshot_id``, and ``selection_input_sha256`` immutable
    on every ordinary connection (Decision 021 section 15.5), and
    ``tests/unit/test_m23_pilot_schema.py`` proves that directly for all three
    columns. Historically corrupted storage must still fail closed anyway: a row
    whose bytes were altered before that guard existed, or by something that is not
    this application, has to be refused by reconstruction and by same-ID replay
    rather than trusted or silently overwritten. That state is no longer reachable
    through the guarded path, so it is constructed here instead -- on a raw
    connection to the throwaway per-test catalog, in autocommit, with foreign keys
    ON and exactly one trigger dropped. Every other guard stays installed, so the
    resulting row is precisely what the ordinary pre-0013 write produced and nothing
    else was relaxed to obtain it.

    The drop is unconditional so this fixture has a single code path, and the
    trigger is reinstalled from its own captured ``sqlite_master`` definition in a
    ``finally`` block before the caller regains control. The bypass therefore lasts
    exactly one statement: every assertion the calling test then makes runs against
    a fully guarded catalog.
    """
    raw = sqlite3.connect(
        _require_scratch_catalog(_database_path(connection)), isolation_level=None
    )
    try:
        raw.execute("PRAGMA foreign_keys = ON")
        definition = raw.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
            ("pilot_selection_run_identity_guard",),
        ).fetchone()
        assert definition is not None, "pilot_selection_run_identity_guard is not installed"
        raw.execute("DROP TRIGGER pilot_selection_run_identity_guard")
        try:
            raw.execute(sql, parameters)
        finally:
            raw.execute(str(definition[0]))
        restored = raw.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'trigger' AND name = ?",
            ("pilot_selection_run_identity_guard",),
        ).fetchone()[0]
        assert restored == 1, "the identity guard was not reinstalled after the corruption"
    finally:
        raw.close()


_CORRUPTION_VERBS: Final[dict[str, str]] = {
    "UPDATE": "update",
    "DELETE": "delete",
    "INSERT": "insert",
}


def _blocking_guard(sql: str) -> str:
    """The single migration-0009 lifecycle guard that blocks this exact statement.

    The guards are named ``pilot_<table>_<verb>_guard``, so the statement's own verb and
    target table identify the one that has to come out -- and only that one.
    """
    match = re.match(
        r"\s*(UPDATE|DELETE\s+FROM|INSERT\s+INTO)\s+(?P<table>[a-z_][a-z0-9_]*)",
        sql,
        re.IGNORECASE,
    )
    assert match is not None, f"cannot identify the target table of {sql!r}"
    verb = _CORRUPTION_VERBS[match.group(1).split()[0].upper()]
    return f"{match.group('table')}_{verb}_guard"


def _corrupt_sealed_row(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[object, ...],
    *,
    foreign_keys: bool = True,
) -> None:
    """Corrupt a row of a sealed feasible run, bypassing one lifecycle guard.

    Migration 0009 makes a completed run immutable through the application
    connection, which is exactly the property under test elsewhere. Reconstruction
    must still fail closed if the stored bytes are altered some other way, so the
    corruption is applied on a raw connection to the throwaway per-test catalog with
    **only the single guard that blocks this exact statement** removed, and with that
    guard reinstalled from its own captured ``sqlite_master`` definition in a ``finally``
    block before the caller regains control. Every other guard -- including all eight of
    migration 0013's -- stays installed, so the assertions the calling test then makes run
    against a fully guarded catalog.

    ``foreign_keys`` stays on unless the corruption being modelled is precisely a broken
    reference: removing a parent row is the "missing row" corruption class reconstruction
    has to refuse, and it cannot be constructed while the reference is enforced. Each
    caller that turns it off says why.

    This helper serves the child tables of a run. A ``pilot_selection_runs``
    identity column is corrupted by :func:`_corrupt_stored_run_identity` instead,
    which is narrower.
    """
    guard = _blocking_guard(sql)
    raw = sqlite3.connect(_require_scratch_catalog(_database_path(connection)))
    try:
        raw.execute(f"PRAGMA foreign_keys = {'ON' if foreign_keys else 'OFF'}")
        definition = raw.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?", (guard,)
        ).fetchone()
        assert definition is not None, f"{guard} is not installed"
        raw.execute(f"DROP TRIGGER {guard}")  # noqa: S608
        try:
            raw.execute(sql, parameters)
            raw.commit()
        finally:
            raw.execute(str(definition[0]))
            raw.commit()
        restored = raw.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'trigger' AND name = ?", (guard,)
        ).fetchone()[0]
        assert restored == 1, f"{guard} was not reinstalled after the corruption"
    finally:
        raw.close()


#: Corruptions that model a broken reference rather than an altered value: a removed
#: parent row, a re-keyed parent that orphans its children, or a pointer retargeted at a
#: row that does not exist. Each is a state reconstruction must refuse, and none can be
#: constructed while the reference it breaks is still enforced.
_REFERENTIAL_CORRUPTIONS: Final[tuple[str, ...]] = (
    "DELETE FROM pilot_reserves",
    "SET replacement_cik_numeric = 999",
    "SET reserve_package_id =",
    "SET cik_numeric = 999",
)


def _breaks_a_reference(statement: str) -> bool:
    """Whether this corruption is one of the referential cases above."""
    return any(marker in statement for marker in _REFERENTIAL_CORRUPTIONS)


def test_a_feasible_run_persists_mixed_reserve_and_reason_dispositions(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    assert persisted.run_state == "feasible"
    packages = db.execute(
        "SELECT target_cik_numeric, replacement_cik_numeric, reserve_rank FROM pilot_reserves"
    ).fetchall()
    reasons_rows = db.execute(
        "SELECT cik_numeric, reason_scope, reason_code FROM pilot_selection_entity_reasons"
    ).fetchall()
    assert packages
    assert reasons_rows
    assert {row["reserve_rank"] for row in packages} == {1}
    assert {row["reason_scope"] for row in reasons_rows} == {"reserve"}
    assert {row["reason_code"] for row in reasons_rows} == {"REVIEW_PILOT_NO_COMPATIBLE_RESERVE"}
    covered = {row["target_cik_numeric"] for row in packages}
    uncovered = {row["cik_numeric"] for row in reasons_rows}
    selected = {int(c.cik_padded) for c in persisted.result.selected_entities}
    assert not covered & uncovered
    assert covered | uncovered == selected
    assert len(covered) + len(uncovered) == 24


def test_a_replacement_may_serve_two_persisted_targets(db: sqlite3.Connection) -> None:
    """Packages are independent contingencies, so cross-target reuse survives
    persistence unchanged (Decision 020 section 7)."""
    write_plan(db, reserve_plan())
    run_once(db)
    rows = db.execute(
        "SELECT replacement_cik_numeric, COUNT(*) AS packages FROM pilot_reserves "
        "GROUP BY replacement_cik_numeric"
    ).fetchall()
    assert rows
    assert max(row["packages"] for row in rows) >= 2


def test_no_persisted_replacement_is_itself_selected(db: sqlite3.Connection) -> None:
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    selected = {int(c.cik_padded) for c in persisted.result.selected_entities}
    rows = db.execute(
        "SELECT target_cik_numeric, replacement_cik_numeric FROM pilot_reserves"
    ).fetchall()
    assert rows
    for row in rows:
        assert row["replacement_cik_numeric"] not in selected
        assert row["replacement_cik_numeric"] != row["target_cik_numeric"]


def test_every_persisted_package_carries_its_bundle_and_contribution_signature(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, reserve_plan())
    run_once(db)
    packages = [
        row["reserve_package_id"]
        for row in db.execute("SELECT reserve_package_id FROM pilot_reserves").fetchall()
    ]
    assert packages
    for package_id in packages:
        assert _count_for(db, "pilot_reserve_accessions", package_id) >= 1
        assert _count_for(db, "pilot_reserve_quota_contributions", package_id) >= 1


def _count_for(connection: sqlite3.Connection, table: str, package_id: str) -> int:
    value = connection.execute(
        f"SELECT COUNT(*) FROM {table} WHERE reserve_package_id = ?",  # noqa: S608
        (package_id,),
    ).fetchone()[0]
    assert isinstance(value, int)
    return value


def test_every_persisted_reserve_contribution_set_equals_its_targets(
    db: sqlite3.Connection,
) -> None:
    """The invariant migration 0009's feasible-transition trigger enforces, checked
    again against the persisted rows on both sides."""
    write_plan(db, reserve_plan())
    run_once(db)
    packages = db.execute(
        "SELECT reserve_package_id, target_cik_numeric FROM pilot_reserves"
    ).fetchall()
    assert packages
    for package in packages:
        reserve_set = {
            (row["quota_dimension"], row["quota_key"])
            for row in db.execute(
                "SELECT quota_dimension, quota_key FROM pilot_reserve_quota_contributions "
                "WHERE reserve_package_id = ?",
                (package["reserve_package_id"],),
            ).fetchall()
        }
        target_set = {
            (row["quota_dimension"], row["quota_key"])
            for row in db.execute(
                "SELECT quota_dimension, quota_key FROM pilot_selected_entity_quota_contributions "
                "WHERE cik_numeric = ?",
                (package["target_cik_numeric"],),
            ).fetchall()
        }
        assert reserve_set == target_set
        assert reserve_set


def test_the_three_membership_families_reproduce_the_pure_output(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    membership = persisted.result.quota_contributions
    entity_rows = {
        (f"{row['cik_numeric']:010d}", row["quota_dimension"], row["quota_key"])
        for row in db.execute(
            "SELECT cik_numeric, quota_dimension, quota_key "
            "FROM pilot_selected_entity_quota_contributions"
        ).fetchall()
    }
    accession_rows = {
        (row["accession_plain"], row["quota_dimension"], row["quota_key"])
        for row in db.execute(
            "SELECT accession_plain, quota_dimension, quota_key "
            "FROM pilot_selected_accession_quota_contributions"
        ).fetchall()
    }
    assert entity_rows == set(membership.entity_contributions())
    assert accession_rows == set(membership.accession_contributions())
    assert _count(db, "pilot_quota_result_members") == len(membership.quota_members())
    assert entity_rows
    assert accession_rows


def test_persisted_achieved_counts_equal_their_persisted_member_counts(
    db: sqlite3.Connection,
) -> None:
    """The Decision 020 section 6 invariant, observed end to end on stored rows."""
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    measured = {
        (row["quota_dimension"], row["quota_key"]): row["achieved_count"]
        for row in db.execute(
            "SELECT quota_dimension, quota_key, achieved_count FROM pilot_quota_results"
        ).fetchall()
    }
    membership = persisted.result.quota_contributions
    for dimension, key in membership.contribution_keys():
        assert membership.achieved_count(dimension, key) == measured[(dimension, key)]


def test_the_deferred_quota_persists_no_member_or_contribution_row(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, reserve_plan())
    run_once(db)
    for table, column in (
        ("pilot_selected_entity_quota_contributions", "quota_key"),
        ("pilot_selected_accession_quota_contributions", "quota_key"),
    ):
        rows = db.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {column} = ?",  # noqa: S608
            (DEFERRED_QUOTA_KEY,),
        ).fetchone()[0]
        assert rows == 0
    deferred_id = db.execute(
        "SELECT quota_result_id FROM pilot_quota_results WHERE quota_key = ?",
        (DEFERRED_QUOTA_KEY,),
    ).fetchone()["quota_result_id"]
    members = db.execute(
        "SELECT COUNT(*) FROM pilot_quota_result_members WHERE quota_result_id = ?",
        (deferred_id,),
    ).fetchone()[0]
    assert members == 0


def test_a_non_feasible_run_persists_no_contribution_member_or_reserve_row(
    db: sqlite3.Connection,
) -> None:
    plan = feasible_plan()
    plan.accessions = [a for a in plan.accessions if a.dashed != dashed(1, 2010, 2)]
    write_plan(db, plan)
    persisted = run_once(db)
    assert persisted.run_state != "feasible"
    for table in (
        "pilot_selected_entity_quota_contributions",
        "pilot_selected_accession_quota_contributions",
        "pilot_quota_result_members",
        "pilot_reserves",
        "pilot_reserve_accessions",
        "pilot_reserve_quota_contributions",
        "pilot_selection_entity_reasons",
    ):
        assert _count(db, table) == 0


def test_the_terminal_transition_is_the_last_write_of_the_transaction(
    db: sqlite3.Connection,
) -> None:
    """One explicit transaction, with ``running -> feasible`` last: no reserve,
    contribution, member, or disposition row is written after it."""
    write_plan(db, reserve_plan())
    statements: list[str] = []
    db.set_trace_callback(statements.append)
    try:
        run_once(db)
    finally:
        db.set_trace_callback(None)
    normalized = [" ".join(entry.split()) for entry in statements]
    feasible_positions = [
        index
        for index, entry in enumerate(normalized)
        if entry.startswith("UPDATE pilot_selection_runs SET run_state = 'feasible'")
    ]
    # SQLite traces the parent statement once per trigger sub-program, so a single
    # UPDATE surfaces as one contiguous run of identical trace lines.
    assert feasible_positions
    assert len({normalized[index] for index in feasible_positions}) == 1
    assert feasible_positions == list(range(feasible_positions[0], feasible_positions[-1] + 1))
    tail = normalized[feasible_positions[-1] + 1 :]
    assert not [entry for entry in tail if entry.upper().startswith("INSERT INTO PILOT_")]
    assert not [entry for entry in tail if entry.upper().startswith("UPDATE PILOT_")]
    assert not [entry for entry in tail if entry.upper().startswith("DELETE FROM PILOT_")]
    # Only the commit and the read-only reconstruction reads follow the transition.
    assert "COMMIT" in tail
    assert all(entry == "COMMIT" or entry.upper().startswith("SELECT") for entry in tail)
    assert normalized.count("BEGIN IMMEDIATE") == 1
    assert normalized.count("COMMIT") == 1
    assert normalized.count("ROLLBACK") == 0


@pytest.mark.parametrize(
    "table",
    (
        "pilot_selected_entity_quota_contributions",
        "pilot_selected_accession_quota_contributions",
        "pilot_quota_result_members",
        "pilot_reserves",
        "pilot_reserve_accessions",
        "pilot_reserve_quota_contributions",
        "pilot_selection_entity_reasons",
    ),
)
def test_a_failure_at_any_new_row_family_rolls_the_whole_run_back(
    db: sqlite3.Connection, table: str
) -> None:
    """Nothing is partially persisted: an injected failure while writing any new
    family leaves no lifecycle row, no event, and no result row at all."""
    write_plan(db, reserve_plan())

    def authorizer(action: int, first: str | None, *_rest: object) -> int:
        if action == sqlite3.SQLITE_INSERT and first == table:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    db.set_authorizer(authorizer)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            run_once(db)
    finally:
        db.set_authorizer(None)
    assert _result_row_counts(db) == dict.fromkeys(_result_row_counts(db), 0)
    assert _count(db, "pilot_selection_runs") == 0
    assert _count(db, "pilot_selection_run_events") == 0


def test_an_idempotent_replay_writes_no_duplicate_reserve_or_membership_row(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, reserve_plan())
    first = run_once(db)
    before = whole_database(db)
    counts_before = _result_row_counts(db)
    replayed = run_once(db, occurred_at_utc="2027-05-05T00:00:00Z", event_id="replay")
    assert replayed == first
    assert whole_database(db) == before
    assert _result_row_counts(db) == counts_before
    assert counts_before["pilot_reserves"] > 0
    assert counts_before["pilot_selection_entity_reasons"] > 0


def test_no_row_is_written_after_the_run_reaches_feasible(db: sqlite3.Connection) -> None:
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    with (
        pytest.raises(sqlite3.IntegrityError, match="requires a running selection run"),
        transaction(db) as c,
    ):
        c.execute(
            "INSERT INTO pilot_selected_entity_quota_contributions "
            "(selection_run_id, snapshot_id, cik_numeric, quota_dimension, quota_key, "
            "recorded_at_utc) VALUES (?, ?, ?, 'cross_cutting', 'late', '2027-01-01T00:00:00Z')",
            (
                persisted.selection_run_id,
                _SNAPSHOT_ID,
                int(persisted.result.selected_entities[0].cik_padded),
            ),
        )
    with (
        pytest.raises(sqlite3.IntegrityError, match="requires an existing running selection run"),
        transaction(db) as c,
    ):
        c.execute(
            "INSERT INTO pilot_selection_entity_reasons "
            "(selection_run_id, snapshot_id, cik_numeric, reason_scope, reason_code, "
            "recorded_at_utc) VALUES (?, ?, ?, 'reserve', "
            "'REVIEW_PILOT_NO_COMPATIBLE_RESERVE', '2027-01-01T00:00:00Z')",
            (
                persisted.selection_run_id,
                _SNAPSHOT_ID,
                int(persisted.result.selected_entities[0].cik_padded),
            ),
        )


def test_reconstruction_round_trips_every_new_row_family(db: sqlite3.Connection) -> None:
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    rebuilt = reconstruct_persisted_joint_selection(db, persisted.selection_run_id)
    assert rebuilt == persisted
    assert rebuilt.result.quota_contributions == persisted.result.quota_contributions
    assert rebuilt.result.quota_contributions.units


@pytest.mark.parametrize(
    ("statement", "parameters", "message"),
    (
        (
            "DELETE FROM pilot_selected_entity_quota_contributions "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_selected_entity_quota_contributions)",
            (),
            "pilot_selected_entity_quota_contributions",
        ),
        (
            "UPDATE pilot_selected_entity_quota_contributions SET quota_key = 'tampered' "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_selected_entity_quota_contributions)",
            (),
            "pilot_selected_entity_quota_contributions",
        ),
        (
            "DELETE FROM pilot_selected_accession_quota_contributions "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_selected_accession_quota_contributions)",
            (),
            "pilot_selected_accession_quota_contributions",
        ),
        (
            "DELETE FROM pilot_quota_result_members "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_quota_result_members)",
            (),
            "pilot_quota_result_members",
        ),
        (
            "UPDATE pilot_quota_result_members SET member_order = 99 "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_quota_result_members)",
            (),
            "pilot_quota_result_members",
        ),
    ),
)
def test_corrupted_contribution_or_member_rows_fail_closed(
    db: sqlite3.Connection, statement: str, parameters: tuple[object, ...], message: str
) -> None:
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    _corrupt_sealed_row(db, statement, parameters)
    with pytest.raises(GateFailureError, match=message):
        reconstruct_persisted_joint_selection(db, persisted.selection_run_id)


@pytest.mark.parametrize(
    ("statement", "message"),
    (
        (
            "DELETE FROM pilot_reserves WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserves)",
            "pilot_reserves",
        ),
        (
            "UPDATE pilot_reserves SET reserve_rank = 2 "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserves)",
            "pilot_reserves",
        ),
        (
            "UPDATE pilot_reserves SET replacement_cik_numeric = 999 "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserves)",
            "pilot_reserves",
        ),
        (
            "UPDATE pilot_reserves SET reserve_package_id = 'f' || substr(reserve_package_id, 2) "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserves)",
            "pilot_reserves",
        ),
        (
            "UPDATE pilot_reserves SET replaces_signature_sha256 = "
            "'0000000000000000000000000000000000000000000000000000000000000000', "
            "reserve_signature_sha256 = "
            "'0000000000000000000000000000000000000000000000000000000000000000' "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserves)",
            "pilot_reserves",
        ),
        (
            "UPDATE pilot_reserves SET evidence_floor = 'unavailable' "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserves)",
            "pilot_reserves",
        ),
        (
            "DELETE FROM pilot_reserve_accessions "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserve_accessions)",
            "pilot_reserve_accessions",
        ),
        (
            "DELETE FROM pilot_reserve_quota_contributions "
            "WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserve_quota_contributions)",
            "pilot_reserve_quota_contributions",
        ),
    ),
)
def test_corrupted_reserve_rows_fail_closed(
    db: sqlite3.Connection, statement: str, message: str
) -> None:
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    _corrupt_sealed_row(db, statement, (), foreign_keys=not _breaks_a_reference(statement))
    with pytest.raises(GateFailureError, match=message):
        reconstruct_persisted_joint_selection(db, persisted.selection_run_id)


def test_a_malformed_signature_is_refused_at_the_check_constraint(
    db: sqlite3.Connection,
) -> None:
    """The owning enforcement boundary for a malformed digest is the
    ``pilot_reserves`` CHECK constraint, so that state never reaches reconstruction
    (Decision 020 section 8.3, item 4). The reconstruction shape gate remains as
    defence in depth and is deliberately not the layer proved here."""
    write_plan(db, reserve_plan())
    run_once(db)
    raw = sqlite3.connect(_database_path(db))
    try:
        raw.execute("PRAGMA foreign_keys = OFF")
        raw.execute("DROP TRIGGER IF EXISTS pilot_reserves_update_guard")
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            raw.execute(
                "UPDATE pilot_reserves SET replaces_signature_sha256 = 'NOT-A-DIGEST', "
                "reserve_signature_sha256 = 'NOT-A-DIGEST' "
                "WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserves)"
            )
    finally:
        raw.close()


def test_a_signature_that_no_longer_derives_from_its_content_fails_closed(
    db: sqlite3.Connection,
) -> None:
    """A well-formed digest that is not the one the package's own content derives is
    constructible, and reconstruction refuses it."""
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    _corrupt_sealed_row(
        db,
        "UPDATE pilot_reserves SET replaces_signature_sha256 = ?, reserve_signature_sha256 = ? "
        "WHERE rowid = (SELECT MIN(rowid) FROM pilot_reserves)",
        ("a" * 64, "a" * 64),
    )
    with pytest.raises(GateFailureError, match="pilot_reserves"):
        reconstruct_persisted_joint_selection(db, persisted.selection_run_id)


@pytest.mark.parametrize(
    "statement",
    (
        "DELETE FROM pilot_selection_entity_reasons "
        "WHERE rowid = (SELECT MIN(rowid) FROM pilot_selection_entity_reasons)",
        "UPDATE pilot_selection_entity_reasons SET cik_numeric = 999 "
        "WHERE rowid = (SELECT MIN(rowid) FROM pilot_selection_entity_reasons)",
    ),
    ids=("missing", "retargeted"),
)
def test_corrupted_disposition_rows_fail_closed(db: sqlite3.Connection, statement: str) -> None:
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    _corrupt_sealed_row(db, statement, (), foreign_keys=not _breaks_a_reference(statement))
    with pytest.raises(GateFailureError, match="pilot_selection_entity_reasons"):
        reconstruct_persisted_joint_selection(db, persisted.selection_run_id)


def test_a_reason_row_beside_a_reserve_package_fails_closed(db: sqlite3.Connection) -> None:
    """The two dispositions are mutually exclusive: a target holding both is
    refused even if the row was written outside the lifecycle guards."""
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    covered = db.execute("SELECT target_cik_numeric FROM pilot_reserves LIMIT 1").fetchone()[
        "target_cik_numeric"
    ]
    _corrupt_sealed_row(
        db,
        "INSERT INTO pilot_selection_entity_reasons "
        "(selection_run_id, snapshot_id, cik_numeric, reason_scope, reason_code, "
        "recorded_at_utc) VALUES (?, ?, ?, 'reserve', "
        "'REVIEW_PILOT_NO_COMPATIBLE_RESERVE', '2027-01-01T00:00:00Z')",
        (persisted.selection_run_id, _SNAPSHOT_ID, covered),
    )
    with pytest.raises(GateFailureError, match="pilot_selection_entity_reasons"):
        reconstruct_persisted_joint_selection(db, persisted.selection_run_id)


def test_a_conflicting_same_id_replay_is_refused_with_reserves_present(
    db: sqlite3.Connection,
) -> None:
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    assert _count(db, "pilot_reserves") > 0
    _corrupt_stored_run_identity(
        db,
        "UPDATE pilot_selection_runs SET selection_input_sha256 = ? WHERE selection_run_id = ?",
        ("0" * 64, persisted.selection_run_id),
    )
    with pytest.raises(GateFailureError, match="refusing to overwrite"):
        run_once(db, occurred_at_utc="2027-06-06T00:00:00Z", event_id="conflict")


def test_the_s4_draft_is_untouched_by_reserve_persistence(db: sqlite3.Connection) -> None:
    """Decision 018 section 6 and Decision 020 section 11: the S4 entity-only draft
    stays ``running``, non-publishable, and excluded from every S5.4 artifact."""
    write_plan(db, reserve_plan())
    draft = execute_and_persist_entity_selection(
        db,
        _SNAPSHOT_ID,
        node_limit=_NODE_LIMIT,
        occurred_at_utc=_AT,
        event_id="s4-draft-event",
    )
    draft_rows_before = _rows(db, "pilot_selection_runs")
    persisted = run_once(db, event_id="s5-event")
    assert persisted.selection_run_id != draft.selection_run_id
    draft_after = db.execute(
        "SELECT * FROM pilot_selection_runs WHERE selection_run_id = ?",
        (draft.selection_run_id,),
    ).fetchone()
    before = next(row for row in draft_rows_before if row[0] == draft.selection_run_id)
    assert tuple(draft_after) == before
    for table in ("pilot_reserves", "pilot_selection_entity_reasons"):
        rows = db.execute(
            f"SELECT COUNT(*) FROM {table} WHERE selection_run_id = ?",  # noqa: S608
            (draft.selection_run_id,),
        ).fetchone()[0]
        assert rows == 0


def test_no_manifest_or_publication_row_is_written_by_stage_s5_4(
    db: sqlite3.Connection,
) -> None:
    """Stage S6 is not begun: no manifest version, no projection recovery event, and
    ``selection_result_sha256`` still NULL (Decision 020 sections 2 and 9)."""
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    assert _count(db, "pilot_manifest_versions") == 0
    assert _count(db, "pilot_projection_recovery_events") == 0
    stored = db.execute(
        "SELECT selection_result_sha256 FROM pilot_selection_runs WHERE selection_run_id = ?",
        (persisted.selection_run_id,),
    ).fetchone()["selection_result_sha256"]
    assert stored is None
    assert _count(db, "pilot_reserves") > 0


# --------------------------------------------------------------------------
# 13: Decision 016 section 7 -- independent recomputation of both signatures
# --------------------------------------------------------------------------
#
# "Acceptance tests must independently recompute both signatures from normalized
# source content (not merely compare the two stored hash columns) and assert the
# recomputed values equal the stored ones and equal each other."
#
# Everything below is reassembled from persisted rows by this module. It calls no
# production signature constructor, no helper that returns an already-assembled
# signature mapping, and never uses one stored digest as the other's expected
# value; the only production code reused is the generic content-hashing primitive
# ``release.hashing.hash_table`` and the canonical CIK renderer.

#: Decision 016 section 7's frozen input list, transcribed from the decision record.
#: The signature is hashed under this exact sorted column vector.
_SIGNATURE_FIELDS: Final[tuple[str, ...]] = (
    "accession_counts_by_role",
    "amendment_purpose_contributions",
    "control_kind",
    "entity_role",
    "eventful_and_currently_inactive",
    "evidence_floor",
    "history_class",
    "industry_family",
    "industry_quota_eligible",
    "inline_xbrl_contribution",
    "multi_registrant_contribution",
    "name_change_contribution",
    "original_2024_contribution",
    "original_2025_2026_contribution",
    "pre_inline_xbrl_contribution",
    "primary_universe_eligible",
    "quota_policy_version",
    "signature_policy_version",
    "size_stratum",
    "support_pair_contribution",
)

#: Strongest to weakest, per ``pilot_reserves.evidence_floor``'s frozen vocabulary.
_FLOOR_ORDER: Final[tuple[str, ...]] = (
    "provisional",
    "review_required",
    "conflicting",
    "unavailable",
)
_ROLE_ORDER: Final[tuple[str, ...]] = ("base", "control", "stress", "support")

#: The quotas whose contribution unit is an accession identity, so the count is the
#: number of qualifying accessions in the side's own bundle.
_ACCESSION_UNIT_QUOTAS: Final[tuple[str, ...]] = (
    "multi_registrant_accessions",
    "pre_inline_xbrl_originals",
    "inline_xbrl_originals",
)
#: The quotas whose contribution unit is the entity, so the count is 0 or 1 and is
#: read off the side's own persisted contribution key set.
_ENTITY_UNIT_QUOTAS: Final[tuple[str, str]] = (
    "name_change_entities",
    "support_target_pair_entities",
)
_YEAR_UNIT_QUOTAS: Final[tuple[str, str]] = (
    "original_2024_entities",
    "original_2025_2026_entities",
)


def _candidate_accessions(
    connection: sqlite3.Connection, plains: Sequence[str]
) -> dict[str, sqlite3.Row]:
    """The frozen candidate row behind each accession of one side's bundle."""
    rows: dict[str, sqlite3.Row] = {}
    for plain in plains:
        row = connection.execute(
            "SELECT accession_plain, form_type, is_amendment, official_filing_date, "
            "has_inline_xbrl, multi_registrant, amendment_purpose_category, "
            "amendment_purpose_quota_eligible, amendment_purpose_evidence_level, "
            "filing_date_evidence_level, cohort_evidence_level, xbrl_evidence_level, "
            "provisional_official_cohort FROM pilot_candidate_accessions "
            "WHERE snapshot_id = ? AND accession_plain = ?",
            (_SNAPSHOT_ID, plain),
        ).fetchone()
        assert row is not None, plain
        rows[plain] = row
    return rows


def _independent_evidence_floor(candidates: dict[str, sqlite3.Row]) -> str:
    """The weakest structurally applicable evidence level across a bundle.

    Decision 016 section 7's own wording, over Decision 018 section 3.4's
    applicability model. Only the dimensions the snapshot *stores* are read here.
    Amendment-linkage and multi-registrant evidence levels are derived by the S5.2
    loader (Decision 019 sections 5 and 6) rather than stored, so this reassembly
    asserts the bundle contains no amendment and no multi-registrant accession
    instead of silently ignoring those dimensions: a fixture that changes shape
    fails loudly here rather than quietly weakening the comparison.
    """
    weakest = 0
    for row in candidates.values():
        assert not row["is_amendment"], "extend this reassembly before using an amendment bundle"
        assert not row["multi_registrant"], "extend this reassembly for multi-registrant bundles"
        levels = [row["filing_date_evidence_level"], row["xbrl_evidence_level"]]
        if row["provisional_official_cohort"] is not None:
            levels.append(row["cohort_evidence_level"])
        for level in levels:
            assert level in _FLOOR_ORDER, level
            weakest = max(weakest, _FLOOR_ORDER.index(level))
    return _FLOOR_ORDER[weakest]


def _independent_role_counts(roles: Sequence[str]) -> str:
    counts = dict.fromkeys(_ROLE_ORDER, 0)
    for role in roles:
        counts[role] += 1
    return "|".join(f"{role}={counts[role]}" for role in _ROLE_ORDER)


def _independent_contribution_counts(
    candidates: dict[str, sqlite3.Row], contribution_keys: set[str]
) -> dict[str, int]:
    """How many achieved units of each named quota this side's bundle supplies.

    Accession-unit quotas are counted from the bundle's own frozen attributes;
    entity-unit quotas are 0 or 1 and are read from the side's persisted
    contribution key set, which is exactly what the schema records for them.
    """
    counts = dict.fromkeys((*_ACCESSION_UNIT_QUOTAS, *_ENTITY_UNIT_QUOTAS, *_YEAR_UNIT_QUOTAS), 0)
    for row in candidates.values():
        original_annual = not row["is_amendment"] and row["form_type"] in ("10-K", "10-KT")
        if row["multi_registrant"]:
            counts["multi_registrant_accessions"] += 1
        if original_annual:
            key = "inline_xbrl_originals" if row["has_inline_xbrl"] else "pre_inline_xbrl_originals"
            counts[key] += 1
    for key in (*_ENTITY_UNIT_QUOTAS, *_YEAR_UNIT_QUOTAS):
        counts[key] = 1 if key in contribution_keys else 0
    return counts


def _independent_purpose_categories(candidates: dict[str, sqlite3.Row]) -> str:
    return "|".join(
        sorted(
            {
                row["amendment_purpose_category"]
                for row in candidates.values()
                if row["amendment_purpose_quota_eligible"]
                and row["amendment_purpose_category"] is not None
            }
        )
    )


def _independent_signature_fields(
    entity: sqlite3.Row,
    *,
    entity_role: str,
    candidates: dict[str, sqlite3.Row],
    roles: Sequence[str],
    contribution_keys: set[str],
    signature_policy_version: str,
    quota_policy_version: str,
) -> dict[str, object]:
    """Decision 016 section 7's twenty inputs, assembled here from persisted rows."""
    counts = _independent_contribution_counts(candidates, contribution_keys)
    assembled: dict[str, object] = {
        "signature_policy_version": signature_policy_version,
        "quota_policy_version": quota_policy_version,
        "entity_role": entity_role,
        "control_kind": entity["control_kind"],
        "size_stratum": entity["size_stratum"],
        "industry_family": entity["industry_family"],
        "industry_quota_eligible": bool(entity["industry_quota_eligible"]),
        "history_class": entity["history_class"],
        "eventful_and_currently_inactive": (
            entity["history_class"] == "eventful" and bool(entity["currently_inactive"])
        ),
        "primary_universe_eligible": bool(entity["primary_universe_eligible"]),
        "name_change_contribution": counts["name_change_entities"],
        "support_pair_contribution": counts["support_target_pair_entities"],
        "multi_registrant_contribution": counts["multi_registrant_accessions"],
        "pre_inline_xbrl_contribution": counts["pre_inline_xbrl_originals"],
        "inline_xbrl_contribution": counts["inline_xbrl_originals"],
        "original_2024_contribution": counts["original_2024_entities"],
        "original_2025_2026_contribution": counts["original_2025_2026_entities"],
        "amendment_purpose_contributions": _independent_purpose_categories(candidates),
        "accession_counts_by_role": _independent_role_counts(roles),
        "evidence_floor": _independent_evidence_floor(candidates),
    }
    assert tuple(sorted(assembled)) == _SIGNATURE_FIELDS
    return assembled


def _independent_digest(fields_by_name: dict[str, object]) -> str:
    """Hash one assembled input with the generic accepted content primitive."""
    return hash_table(
        "pilot_reserve_signature", _SIGNATURE_FIELDS, [fields_by_name]
    ).normalized_content_sha256


def _target_side(
    connection: sqlite3.Connection, run_id: str, package: sqlite3.Row
) -> tuple[dict[str, object], set[str]]:
    """Reassemble the target's signature input from its own persisted rows."""
    target_cik = package["target_cik_numeric"]
    entity = connection.execute(
        "SELECT control_kind, size_stratum, industry_family, history_class "
        "FROM pilot_selected_entities WHERE selection_run_id = ? AND snapshot_id = ? "
        "AND cik_numeric = ?",
        (run_id, _SNAPSHOT_ID, target_cik),
    ).fetchone()
    assert entity is not None
    candidate_entity = connection.execute(
        "SELECT candidate_category, control_kind, size_stratum, industry_family, "
        "industry_quota_eligible, history_class, currently_inactive, primary_universe_eligible "
        "FROM pilot_candidate_entities WHERE snapshot_id = ? AND cik_numeric = ?",
        (_SNAPSHOT_ID, target_cik),
    ).fetchone()
    assert candidate_entity is not None
    # the selected row and the frozen candidate row must agree on the shared columns
    for column in ("control_kind", "size_stratum", "industry_family", "history_class"):
        assert entity[column] == candidate_entity[column]

    accessions = connection.execute(
        "SELECT accession_plain, accession_role FROM pilot_selected_accessions "
        "WHERE selection_run_id = ? AND snapshot_id = ? AND anchor_cik_numeric = ? "
        "ORDER BY accession_plain",
        (run_id, _SNAPSHOT_ID, target_cik),
    ).fetchall()
    plains = [row["accession_plain"] for row in accessions]
    keys = {
        row["quota_key"]
        for row in connection.execute(
            "SELECT quota_key FROM pilot_selected_entity_quota_contributions "
            "WHERE selection_run_id = ? AND snapshot_id = ? AND cik_numeric = ?",
            (run_id, _SNAPSHOT_ID, target_cik),
        ).fetchall()
    }
    assembled = _independent_signature_fields(
        candidate_entity,
        entity_role=candidate_entity["candidate_category"],
        candidates=_candidate_accessions(connection, plains),
        roles=[row["accession_role"] for row in accessions],
        contribution_keys=keys,
        signature_policy_version=package["signature_policy_version"],
        quota_policy_version=package["quota_policy_version"],
    )
    return assembled, set(plains)


def _replacement_side(
    connection: sqlite3.Connection, package: sqlite3.Row
) -> tuple[dict[str, object], set[str]]:
    """Reassemble the replacement's signature input from the package's own rows."""
    replacement_cik = package["replacement_cik_numeric"]
    candidate_entity = connection.execute(
        "SELECT candidate_category, control_kind, size_stratum, industry_family, "
        "industry_quota_eligible, history_class, currently_inactive, primary_universe_eligible "
        "FROM pilot_candidate_entities WHERE snapshot_id = ? AND cik_numeric = ?",
        (_SNAPSHOT_ID, replacement_cik),
    ).fetchone()
    assert candidate_entity is not None
    accessions = connection.execute(
        "SELECT accession_plain, accession_role FROM pilot_reserve_accessions "
        "WHERE reserve_package_id = ? ORDER BY accession_order",
        (package["reserve_package_id"],),
    ).fetchall()
    plains = [row["accession_plain"] for row in accessions]
    keys = {
        row["quota_key"]
        for row in connection.execute(
            "SELECT quota_key FROM pilot_reserve_quota_contributions WHERE reserve_package_id = ?",
            (package["reserve_package_id"],),
        ).fetchall()
    }
    assembled = _independent_signature_fields(
        candidate_entity,
        entity_role=candidate_entity["candidate_category"],
        candidates=_candidate_accessions(connection, plains),
        roles=[row["accession_role"] for row in accessions],
        contribution_keys=keys,
        signature_policy_version=package["signature_policy_version"],
        quota_policy_version=package["quota_policy_version"],
    )
    return assembled, set(plains)


def _persisted_packages(connection: sqlite3.Connection, run_id: str) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT reserve_package_id, target_cik_numeric, replacement_cik_numeric, "
        "replaces_signature_sha256, reserve_signature_sha256, signature_policy_version, "
        "quota_policy_version, evidence_floor FROM pilot_reserves "
        "WHERE selection_run_id = ? AND snapshot_id = ? ORDER BY reserve_package_id",
        (run_id, _SNAPSHOT_ID),
    ).fetchall()


def test_both_persisted_signatures_recompute_from_normalized_persisted_content(
    db: sqlite3.Connection,
) -> None:
    """Decision 016 section 7's recomputation obligation, discharged independently.

    Each side's twenty frozen inputs are reassembled here from persisted rows and
    hashed with the generic content primitive; the target digest is compared with
    ``replaces_signature_sha256`` and the replacement digest with
    ``reserve_signature_sha256``. Neither stored column is used as the other's
    expected value, and no production signature code runs.
    """
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    assert persisted.run_state == "feasible"
    packages = _persisted_packages(db, persisted.selection_run_id)
    assert packages, "the fixture must persist at least one reserve package"

    for package in packages:
        target_fields, target_plains = _target_side(db, persisted.selection_run_id, package)
        replacement_fields, replacement_plains = _replacement_side(db, package)

        # independently obtained, and disjoint: a target is never its own replacement
        assert target_plains
        assert replacement_plains
        assert not target_plains & replacement_plains
        assert package["target_cik_numeric"] != package["replacement_cik_numeric"]

        target_digest = _independent_digest(target_fields)
        replacement_digest = _independent_digest(replacement_fields)
        assert target_digest == package["replaces_signature_sha256"]
        assert replacement_digest == package["reserve_signature_sha256"]
        assert target_digest == replacement_digest
        # the independently derived floor is the one the package stored
        assert target_fields["evidence_floor"] == package["evidence_floor"]
        assert replacement_fields["evidence_floor"] == package["evidence_floor"]


def _perturb(value: object) -> object:
    """Any materially different value of the same shape, never equal to the input."""
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if value is None:
        return "perturbed"
    assert isinstance(value, str)
    return f"{value}-perturbed"


@pytest.mark.parametrize("field_name", _SIGNATURE_FIELDS)
def test_perturbing_one_normalized_signature_input_changes_the_digest(
    db: sqlite3.Connection, field_name: str
) -> None:
    """Every one of Decision 016 section 7's twenty inputs is load-bearing.

    Proved from the independently reassembled mapping, so a field that silently
    stopped entering the production hash would still be caught here by the stored
    digest comparison in the test above.
    """
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    package = _persisted_packages(db, persisted.selection_run_id)[0]
    baseline, _plains = _replacement_side(db, package)
    assert _independent_digest(baseline) == package["reserve_signature_sha256"]

    altered = dict(baseline)
    altered[field_name] = _perturb(baseline[field_name])
    assert altered[field_name] != baseline[field_name], field_name
    assert _independent_digest(altered) != package["reserve_signature_sha256"]


def test_the_persisted_run_identity_is_the_one_its_own_frozen_inputs_derive(
    db: sqlite3.Connection,
) -> None:
    """Run identity is unchanged by S5.4: it is still derived from the frozen inputs
    alone, and no reserve, contribution, or member row enters it (Decision 020
    section 9)."""
    write_plan(db, reserve_plan())
    persisted = run_once(db)
    loaded = load_frozen_joint_candidates(db, _SNAPSHOT_ID)
    identity = build_joint_selection_run_identity(loaded, node_limit=_NODE_LIMIT)
    assert persisted.selection_run_id == identity.selection_run_id
    assert persisted.selection_input_sha256 == identity.selection_input_sha256
    assert _count(db, "pilot_reserves") > 0
    assert _count(db, "pilot_selected_entity_quota_contributions") > 0
