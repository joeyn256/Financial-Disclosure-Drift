"""The one synthetic base-case design both M3.3 rehearsal tracks are built from.

**R28** (Decision 073 §4) requires Track A and Track B to be *paired siblings from the
same synthetic base case design*. This module is that base case: it materializes a
disposable data tree and catalog carrying accepted-shaped **stored source objects** and
the accepted ``census_plan_sources`` rows that bind them, and then drives the real
:func:`~disclosure_drift.m3.offline_parse.run_offline_metadata_parse` over them so the
census layer is *derived by the production path* rather than hand-written.

Nothing here is real. Every CIK, accession, company name, and SIC code is synthetic, no
byte of it comes from the accepted private M3.2 evidence, and no code path in this
module opens a socket, constructs a transport, or resolves a host.

**Two facts this fixture stipulates are recorded rather than hidden.**

1. **The census amendment-relationship resolutions.** No accepted source field maps to
   the Decision 012 canonical field ``amendment_relationship``
   (``sec/census.py``'s ``CANONICAL_FIELD_BY_SOURCE_FIELD``), so an offline parse of
   accepted metadata resolves it for no accession, and the accepted Decision 008
   ``link_amendment`` machinery reaches at best ``possible_amendment_of`` without an
   explicit parent reference from a filing header — which M3.3 may not read. This
   fixture therefore *stipulates* resolved census amendment-relationship evidence, so
   the downstream linked-amendment quota is exercisable. It is a **census-layer input
   fact, identical in Track A and Track B**, and it is not an amendment-*purpose* fact:
   R28's equivalence is unaffected. The real-path consequence is reported as a finding,
   never presented as real feasibility.
2. **Nothing else.** Every other candidate fact below is derived by the production
   offline parse and the production candidate builder from the stored objects.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.offline_parse import OfflineParseReport, run_offline_metadata_parse
from disclosure_drift.paths import DataTree
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.storage.catalog import ELIGIBLE_FORM_TYPES, CatalogWriter
from disclosure_drift.storage.sqlite import apply_migrations, connect, transaction

__all__ = [
    "AMENDMENT_RELATIONSHIP_STIPULATION",
    "CENSUS_RUN_ID",
    "COVERAGE_END",
    "COVERAGE_START",
    "AccessionSpec",
    "EntitySpec",
    "RehearsalWorld",
    "WorldDesign",
    "base_case_design",
    "build_rehearsal_world",
]

CENSUS_RUN_ID: Final = "job-rehearsal-census-1"
COVERAGE_START: Final = "2009-01-01"
COVERAGE_END: Final = "2026-06-30"
_AT: Final = "2026-01-01T00:00:00Z"

#: The label under which this fixture records the one census fact it stipulates rather
#: than derives. Documentation only: it is never a persisted vocabulary value.
AMENDMENT_RELATIONSHIP_STIPULATION: Final = "SYNTHETIC_CENSUS_STIPULATION"

_RESOLUTION_POLICY: Final = "accession-resolution/1.0"

#: Decision 014 §2's SEC ``category`` strings, one per frozen size stratum.
_SIZE_CATEGORY: Final[Mapping[str, str]] = {
    "large_accelerated": "Large accelerated filer",
    "accelerated": "Accelerated filer",
    "non_accelerated_or_smaller": "Non-accelerated filer",
}

#: One SIC per frozen industry family, each inside Decision 014 §4's frozen ranges.
#: ``operating_financial_institutions`` is **6712**: the accepted S4 ``_operating_eligible``
#: requires an operating-financial candidate to be simultaneously industry-quota eligible,
#: primary-universe ineligible, and ``engineering_only_stress``, and Decision 016 §2 fixes
#: 6712 as exactly that engineering-only operating-financial stratum.
_INDUSTRY_SIC: Final[Mapping[str, str]] = {
    "technology_and_communications": "3571",
    "operating_financial_institutions": "6712",
    "industrial_and_materials": "3312",
    "consumer_retail_and_services": "5211",
    "healthcare_and_life_sciences": "8011",
    "energy_and_utilities": "1311",
}

#: R20/R26 control evidence. RIC/ETF and shell are SIC-established; asset-backed and
#: foreign-private-issuer are established by an exact form in stored submissions history.
_CONTROL_SIC: Final[Mapping[str, str]] = {
    "registered_investment_company_or_etf": "6726",
    "shell_or_blank_check_issuer": "6770",
    "asset_backed_issuer": "3711",
    "foreign_private_issuer": "3721",
}
_CONTROL_EXTRA_FORM: Final[Mapping[str, str]] = {
    "asset_backed_issuer": "10-D",
    "foreign_private_issuer": "20-F",
}

_SIZE_SEQUENCE: Final[tuple[str, ...]] = (
    ("large_accelerated",) * 7 + ("accelerated",) * 7 + ("non_accelerated_or_smaller",) * 6
)
_INDUSTRY_SEQUENCE: Final[tuple[str, ...]] = (
    ("technology_and_communications",) * 4
    + ("operating_financial_institutions",) * 4
    + ("industrial_and_materials",) * 3
    + ("consumer_retail_and_services",) * 3
    + ("healthcare_and_life_sciences",) * 3
    + ("energy_and_utilities",) * 3
)

#: Every SIC the design uses, as the accepted SIC authority carries them.
_SIC_AUTHORITY: Final[tuple[str, ...]] = tuple(
    sorted({*_INDUSTRY_SIC.values(), *_CONTROL_SIC.values()})
)


class RehearsalWorldError(DisclosureDriftError):
    """The synthetic base case could not be materialized. Never worked around."""


@dataclass(frozen=True, slots=True)
class AccessionSpec:
    """One synthetic filing, as the accepted submissions document carries it."""

    cik: int
    year: int
    seq: int
    form: str = "10-K"
    inline_xbrl: bool = True
    xbrl: bool = True
    #: The accession this one amends, in plain form. Stipulated census evidence.
    parent_plain: str | None = None
    #: Extra registrant CIKs the accepted ``company.idx`` lists for this accession.
    co_registrants: tuple[int, ...] = ()
    #: A year-end filing whose SEC acceptance lands in the next cohort. The accepted
    #: resolver then marks the cohort boundary crossed, which under Decision 018 §7
    #: makes the accession ineligible for the base role and therefore unselectable --
    #: history evidence that contributes to Decision 014 §5's four-original ``stable``
    #: condition without enlarging the selection search.
    boundary_crossing: bool = False

    @property
    def dashed(self) -> str:
        """The canonical dashed rendering."""
        return f"{self.cik:010d}-{self.year % 100:02d}-{self.seq:06d}"

    @property
    def plain(self) -> str:
        """The canonical plain rendering."""
        return self.dashed.replace("-", "")

    @property
    def filing_date(self) -> str:
        """A deterministic filing date; a boundary-crossing filing sits at year end."""
        return f"{self.year}-12-29" if self.boundary_crossing else f"{self.year}-03-01"

    @property
    def report_date(self) -> str:
        """A fiscal-year-end report date, constant month/day so no FYE drift arises."""
        return f"{self.year - 1}-12-31"

    @property
    def acceptance_value(self) -> str:
        """The raw SEC acceptance value, in the fourteen-digit shape the accepted
        ``sec/temporal.acceptance_date_sec`` requires.

        Amendments accept later in the day than any original, so Decision 019 §5.9's
        strict ordering gate is met by construction rather than by coincidence. A
        boundary-crossing filing accepts in the first days of the following year, which
        is what puts its filing and acceptance cohorts on opposite sides of a frozen
        boundary.
        """
        hour = 20 if self.form.endswith("/A") else 17
        if self.boundary_crossing:
            return f"{self.year + 1:04d}0103{hour:02d}0000"
        return f"{self.year:04d}0301{hour:02d}0000"


@dataclass(frozen=True, slots=True)
class EntitySpec:
    """One synthetic registrant and everything the submissions document declares."""

    cik: int
    name: str
    sic: str
    category: str | None = None
    entity_type: str = "operating"
    former_names: tuple[str, ...] = ()
    accessions: tuple[AccessionSpec, ...] = ()

    @property
    def padded(self) -> str:
        """The canonical zero-padded CIK."""
        return f"{self.cik:010d}"


@dataclass(frozen=True, slots=True)
class WorldDesign:
    """The complete synthetic base case, before any catalog exists."""

    entities: tuple[EntitySpec, ...]

    @property
    def accessions(self) -> tuple[AccessionSpec, ...]:
        """Every accession in the design, in entity then accession order."""
        return tuple(item for entity in self.entities for item in entity.accessions)


@dataclass(frozen=True, slots=True)
class RehearsalWorld:
    """One materialized disposable world, ready for candidate construction."""

    database: Path
    tree: DataTree
    lock_root: Path
    design: WorldDesign
    parse_report: OfflineParseReport
    stipulated_amendment_links: int = 0
    #: Reported so the fixture's own reductions are visible (CLAUDE.md rule 11).
    census_accession_count: int = 0
    census_registrant_count: int = 0
    extras: Mapping[str, object] = field(default_factory=dict)


# --------------------------------------------------------------------------
# The base-case design
# --------------------------------------------------------------------------


def base_case_design() -> WorldDesign:
    """The frozen synthetic base case both tracks are constructed from.

    Composition, and why each piece is there:

    * **20 operating registrants** covering the frozen size (7/7/6), industry
      (4/4/3/3/3/3), and history (10 stable / 10 eventful) strata exactly.
    * **Stable** entities carry four eligible original annual reports each, because
      Decision 014 §5 requires at least four before ``stable`` may be assigned, and
      carry **no** affirmatively observed event flag.
    * **Eventful** entities are eventful for an affirmative reason each: six declare a
      canonical ``inactive`` entity status (also the ``MIN_INACTIVE_EVENTFUL`` six),
      three additionally file a ``10-KT/A`` (transition report and fiscal-year-end
      change), and four carry a single former name (name transition).
    * **Six** stable entities carry a 2009 pre-study original and a 2010 development
      original, so the six-distinct-entity support/target pair quota is reachable.
    * **Two** eventful entities have an accession the accepted ``company.idx`` lists a
      second registrant for, so ``multi_registrant`` is established through **R23**'s
      real materialization path rather than declared.
    * **Four boundary controls**, one per frozen kind, each established by exactly one
      **R20** predicate.
    """
    entities: list[EntitySpec] = []
    for slot in range(20):
        cik = slot + 1
        stable = slot < 10
        inactive = 10 <= slot < 16
        transition = 10 <= slot < 13
        renamed = 16 <= slot < 20
        multi = slot in (16, 17)
        entities.append(
            EntitySpec(
                cik=cik,
                name=f"Synthetic Issuer {cik:03d} Inc",
                sic=_INDUSTRY_SIC[_INDUSTRY_SEQUENCE[slot]],
                category=_SIZE_CATEGORY[_SIZE_SEQUENCE[slot]],
                entity_type="inactive" if inactive else "operating",
                former_names=(f"Synthetic Predecessor {cik:03d} Inc",) if renamed else (),
                accessions=_operating_accessions(
                    cik,
                    slot,
                    stable=stable,
                    transition=transition,
                    multi_registrant=multi,
                ),
            )
        )
    for offset, (kind, sic) in enumerate(sorted(_CONTROL_SIC.items())):
        cik = 101 + offset
        extra = _CONTROL_EXTRA_FORM.get(kind)
        accessions = [AccessionSpec(cik=cik, year=2020, seq=1)]
        if extra is not None:
            accessions.append(AccessionSpec(cik=cik, year=2019, seq=1, form=extra))
        entities.append(
            EntitySpec(
                cik=cik,
                name=f"Synthetic Control {kind}",
                sic=sic,
                category=None,
                entity_type="control",
                accessions=tuple(accessions),
            )
        )
    return WorldDesign(entities=tuple(entities))


def _operating_accessions(
    cik: int,
    slot: int,
    *,
    stable: bool,
    transition: bool,
    multi_registrant: bool,
) -> tuple[AccessionSpec, ...]:
    """One operating registrant's filings, chosen to reach the frozen quotas.

    Only the accessions a quota actually needs are made selectable. Decision 014 §5's
    ``stable`` rule wants four eligible original annual reports per stable registrant,
    but the frozen quotas need at most two of them selected, so the remainder are
    **boundary-crossing** filings: real eligible originals in the candidate pool,
    ineligible for the base role under Decision 018 §7, and therefore absent from the
    accepted selector's search space. That keeps the exhaustive branch-and-bound over a
    pool the frozen caps can actually bound, without weakening a single rule.
    """
    items: list[AccessionSpec] = []
    if stable:
        if slot < 6:
            # Pre-study support, then the 2010 development target it pairs with.
            items.append(AccessionSpec(cik=cik, year=2009, seq=1, xbrl=False, inline_xbrl=False))
            items.append(AccessionSpec(cik=cik, year=2010, seq=2, inline_xbrl=False))
            items.append(AccessionSpec(cik=cik, year=2021, seq=3, boundary_crossing=True))
            items.append(AccessionSpec(cik=cik, year=2023, seq=4, boundary_crossing=True))
            # A resolvable amendment of the selected 2010 target: linked-amendment
            # coverage needs both halves of the witness to be selectable.
            items.append(
                AccessionSpec(
                    cik=cik,
                    year=2017,
                    seq=5,
                    form="10-K/A",
                    parent_plain=AccessionSpec(cik=cik, year=2010, seq=2).plain,
                )
            )
        else:
            items.append(AccessionSpec(cik=cik, year=2018, seq=1))
            for index, year in enumerate((2021, 2023, 2025)):
                items.append(
                    AccessionSpec(cik=cik, year=year, seq=index + 2, boundary_crossing=True)
                )
    elif slot >= 16:
        # Name-transition registrants carry the 2025 original the recency quota needs,
        # two of them with the co-registrant the accepted index establishes.
        items.append(
            AccessionSpec(
                cik=cik,
                year=2025,
                seq=1,
                co_registrants=(900 + cik,) if multi_registrant else (),
            )
        )
    else:
        items.append(AccessionSpec(cik=cik, year=2024, seq=1))
        if transition:
            items.append(
                AccessionSpec(
                    cik=cik,
                    year=2025,
                    seq=2,
                    form="10-KT/A",
                    parent_plain=AccessionSpec(cik=cik, year=2024, seq=1).plain,
                )
            )
    return tuple(items)


# --------------------------------------------------------------------------
# Materialization
# --------------------------------------------------------------------------


def build_rehearsal_world(
    *,
    tree: DataTree,
    database: Path,
    lock_root: Path,
    design: WorldDesign | None = None,
    include_unavailable_source: bool = True,
    include_validation_only_source: bool = True,
) -> RehearsalWorld:
    """Materialize one disposable world and derive its census layer offline.

    Args:
        tree: The disposable data tree the stored objects are written under.
        database: The disposable catalog path. It is created and migrated here.
        lock_root: Where the catalog writer lease is taken.
        design: The base case; :func:`base_case_design` when omitted.
        include_unavailable_source: Add one accepted-as-failed planned source so the
            **R18** category-B branch is exercised on a real run.
        include_validation_only_source: Add one calendar planned source so the **R18**
            category-C branch — deliberately untouched — is exercised on a real run.

    Raises:
        RehearsalWorldError: the fixture could not be materialized truthfully.
    """
    plan = design or base_case_design()
    objects = _write_stored_objects(tree, plan)
    with connect(database, writer=True) as connection:
        apply_migrations(connection)
        _seed_reference(connection)
        _seed_observations_and_plan(
            connection,
            objects,
            include_unavailable_source=include_unavailable_source,
            include_validation_only_source=include_validation_only_source,
        )
    with CatalogWriter(database, lock_root) as writer:
        report = run_offline_metadata_parse(writer=writer, tree=tree)
    stipulated = _stipulate_census_facts(database, plan)
    counts = _census_counts(database)
    return RehearsalWorld(
        database=database,
        tree=tree,
        lock_root=lock_root,
        design=plan,
        parse_report=report,
        stipulated_amendment_links=stipulated["amendment_relationships"],
        census_accession_count=counts["accessions"],
        census_registrant_count=counts["registrants"],
        extras=dict(objects.digests),
    )


@dataclass(frozen=True, slots=True)
class _StoredObjects:
    """Every stored object this world writes, and the digests that verify them."""

    entries: tuple[tuple[str, str, str, str, int], ...]
    digests: Mapping[str, str]


def _write_stored_objects(tree: DataTree, design: WorldDesign) -> _StoredObjects:
    """Write the accepted-shaped stored objects this world parses, and hash them."""
    entries: list[tuple[str, str, str, str, int]] = []
    digests: dict[str, str] = {}

    def store(observation_id: str, source_id: str, relative: str, payload: bytes) -> None:
        target = tree.data_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        digests[observation_id] = digest
        entries.append((observation_id, source_id, relative, digest, len(payload)))

    for entity in design.entities:
        store(
            f"obs-submissions-{entity.padded}",
            "sec_submissions_entity",
            f"raw/sec/bulk/CIK{entity.padded}.json",
            _submissions_document(entity),
        )
    store("obs-sic-1", "sec_sic_code_list", "raw/sec/bulk/sic.html", _sic_document())
    store(
        "obs-index-1",
        "sec_full_index_company",
        "raw/sec/indexes/company_rehearsal.idx",
        _company_index(design),
    )
    return _StoredObjects(entries=tuple(entries), digests=digests)


def _submissions_document(entity: EntitySpec) -> bytes:
    """One accepted-shaped entity submissions document, canonically serialized."""
    accessions = sorted(entity.accessions, key=lambda item: (item.filing_date, item.dashed))
    recent: dict[str, list[object]] = {
        "accessionNumber": [item.dashed for item in accessions],
        "filingDate": [item.filing_date for item in accessions],
        "reportDate": [item.report_date for item in accessions],
        "acceptanceDateTime": [item.acceptance_value for item in accessions],
        "form": [item.form for item in accessions],
        "isXBRL": [int(item.xbrl) for item in accessions],
        "isInlineXBRL": [int(item.inline_xbrl) for item in accessions],
        "primaryDocument": [f"{item.plain}.htm" for item in accessions],
    }
    payload: dict[str, object] = {
        "cik": entity.padded,
        "name": entity.name,
        "sic": entity.sic,
        "entityType": entity.entity_type,
        "fiscalYearEnd": "1231",
        "formerNames": [{"name": name} for name in entity.former_names],
        "filings": {"recent": recent, "files": []},
    }
    if entity.category is not None:
        payload["category"] = entity.category
    return json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _sic_document() -> bytes:
    """The accepted SIC code list, in the HTML table shape the accepted parser reads."""
    rows = "".join(
        f"<tr><td>{code}</td><td>Office of Synthetic Issuers</td>"
        f"<td>Synthetic industry {code}</td></tr>"
        for code in _SIC_AUTHORITY
    )
    document = (
        "<html><body><table>"
        "<tr><th>SIC Code</th><th>Office</th><th>Industry Title</th></tr>"
        f"{rows}</table></body></html>"
    )
    return document.encode("utf-8")


def _company_index(design: WorldDesign) -> bytes:
    """A synthetic ``company.idx`` in the fixed-width shape the accepted parser reads.

    Every accession appears under its own registrant, and an accession declaring
    co-registrants appears once more per co-registrant — which is exactly how the real
    index carries a multi-registrant filing, and the only accepted route by which
    **R23** establishes one.
    """
    header = (
        "Company Name                  Form Type   CIK         Date Filed  File Name\n"
        + "-" * 100
        + "\n"
    )
    lines: list[str] = []
    for entity in design.entities:
        for item in entity.accessions:
            for cik in (item.cik, *item.co_registrants):
                name = entity.name if cik == item.cik else f"Synthetic Co-Registrant {cik}"
                lines.append(
                    f"{name:<30}{item.form:<12}{cik:<12}{item.filing_date:<12}"
                    f"edgar/data/{cik}/{item.dashed}.txt\n"
                )
    return (header + "".join(sorted(lines))).encode("utf-8")


def _seed_reference(connection: sqlite3.Connection) -> None:
    """The reference rows a migrated catalog does not carry by itself."""
    with transaction(connection) as active:
        for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
            active.execute(
                "INSERT OR REPLACE INTO reference_form_types (form_type, is_amendment, "
                "is_eligible_universe, description, decision_record) VALUES (?, ?, ?, ?, ?)",
                (form_type, int(is_amendment), int(eligible), description, "D007"),
            )
        for code in REASON_CODES.values():
            active.execute(
                "INSERT OR REPLACE INTO reference_reason_codes (reason_code, category, "
                "description, blocks_release, requires_manual_review, decision_record) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    code.code,
                    code.category,
                    code.description,
                    int(code.blocks_release),
                    int(code.requires_manual_review),
                    code.decision_reference,
                ),
            )
        active.execute(
            "INSERT OR REPLACE INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
            "started_at_utc, detail) VALUES (?, 'sec_census', 'completed', 'M2.2', ?, '')",
            (CENSUS_RUN_ID, _AT),
        )


def _seed_observations_and_plan(
    connection: sqlite3.Connection,
    objects: _StoredObjects,
    *,
    include_unavailable_source: bool,
    include_validation_only_source: bool,
) -> None:
    """Record every stored object as an accepted observation, and plan-bind it."""
    with transaction(connection) as active:
        for index, (observation_id, source_id, relative, digest, size) in enumerate(
            objects.entries
        ):
            active.execute(
                "INSERT INTO census_source_observations (observation_id, source_id, "
                "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
                "stored_sha256, logical_sha256, content_sha256, stored_size_bytes, "
                "content_size_bytes, storage_representation, relative_storage_path, "
                "parser_version, recorded_at_utc) VALUES (?, ?, ?, ?, 'census', ?, "
                "'stored_new', ?, ?, ?, ?, ?, 'identical', ?, ?, ?)",
                (
                    observation_id,
                    source_id,
                    f"req/{source_id}/{index}",
                    f"https://example.invalid/{relative}",
                    _AT,
                    digest,
                    digest,
                    digest,
                    size,
                    size,
                    relative,
                    "rehearsal-fixture/1.0",
                    _AT,
                ),
            )
            active.execute(
                "INSERT INTO census_plan_sources (census_run_id, source_instance_id, "
                "source_id, request_identity, required, source_scope, retrieval_state, "
                "snapshot_state, parser_state, catalog_state, qa_state, "
                "unresolved_blocking_reasons_json, observation_id, successful_terminal, "
                "updated_at_utc) VALUES (?, ?, ?, ?, 1, 'base', 'retrieved', 'verified', "
                "'not_started', 'committed', 'passed', '[]', ?, 1, ?)",
                (
                    CENSUS_RUN_ID,
                    f"base|{source_id}|{index}",
                    source_id,
                    f"req/{source_id}/{index}",
                    observation_id,
                    _AT,
                ),
            )
        if include_unavailable_source:
            # R18 category B: accepted as failed, preserved as failed, never fabricated.
            active.execute(
                "INSERT INTO census_plan_sources (census_run_id, source_instance_id, "
                "source_id, request_identity, required, source_scope, retrieval_state, "
                "snapshot_state, parser_state, catalog_state, qa_state, "
                "unresolved_blocking_reasons_json, observation_id, successful_terminal, "
                "updated_at_utc) VALUES (?, 'base|unavailable|0', 'sec_submissions_historical', "
                "'req/historical/0', 1, 'base', 'failed', 'missing', 'not_started', "
                "'not_started', 'unknown', '[]', NULL, 0, ?)",
                (CENSUS_RUN_ID, _AT),
            )
        if include_validation_only_source:
            # R18 category C: deliberately untouched, and still enumerated.
            active.execute(
                "INSERT INTO census_plan_sources (census_run_id, source_instance_id, "
                "source_id, request_identity, required, source_scope, retrieval_state, "
                "snapshot_state, parser_state, catalog_state, qa_state, "
                "unresolved_blocking_reasons_json, observation_id, successful_terminal, "
                "updated_at_utc) VALUES (?, 'base|calendar|0', 'sec_edgar_filing_calendar', "
                "'req/calendar/0', 0, 'base', 'retrieved', 'verified', 'not_started', "
                "'committed', 'passed', '[]', ?, 1, ?)",
                (CENSUS_RUN_ID, objects.entries[0][0], _AT),
            )


def _stipulate_census_facts(database: Path, design: WorldDesign) -> Mapping[str, int]:
    """Record the two census facts this fixture stipulates rather than derives.

    Both are **census-layer input facts written identically into both tracks**, and
    neither carries amendment-*purpose* content, so **R28**'s equivalence is untouched.

    ``amendment_relationship``: no accepted source field maps to that Decision 012
    canonical field, so an offline parse resolves it for no accession and the
    linked-amendment quota could not be exercised at all. The real-path consequence is
    accepted **R32** (Decision 074 §3) and is recorded as an open gate, never as real
    feasibility.

    ``cohort_boundary_crossed`` is **no longer stipulated**: accepted **R33**
    (Decision 074 §5) makes it a same-build production derivation from this build's own
    resolved official filing date and acceptance audit date, so the filler originals
    become base-ineligible through the production rule rather than through a fixture.
    """
    written = 0
    with connect(database, writer=True) as connection, transaction(connection) as active:
        for item in design.accessions:
            if item.parent_plain is None:
                continue
            active.execute(
                "INSERT OR REPLACE INTO census_accession_field_resolutions (accession_plain, "
                "field_name, status, resolved_value, authority_class, policy_version, "
                "is_material, blocks_dependents, detail, resolution_sha256, resolved_at_utc) "
                "VALUES (?, 'amendment_relationship', 'resolved', ?, 'entity_submissions', ?, "
                "1, 0, ?, ?, ?)",
                (
                    item.plain,
                    item.parent_plain,
                    _RESOLUTION_POLICY,
                    AMENDMENT_RELATIONSHIP_STIPULATION,
                    hashlib.sha256(
                        f"{item.plain}|amendment_relationship|{item.parent_plain}".encode()
                    ).hexdigest(),
                    _AT,
                ),
            )
            written += 1
    return {"amendment_relationships": written}


def _census_counts(database: Path) -> Mapping[str, int]:
    """The derived census layer's size, reported rather than assumed."""
    with connect(database, writer=False) as connection:
        return {
            "accessions": int(
                connection.execute("SELECT COUNT(*) FROM census_accessions").fetchone()[0]
            ),
            "registrants": int(
                connection.execute("SELECT COUNT(*) FROM census_registrants").fetchone()[0]
            ),
        }


def design_accession_index(design: WorldDesign) -> Mapping[str, AccessionSpec]:
    """Every designed accession, keyed by its canonical plain form."""
    return {item.plain: item for item in design.accessions}


def designed_forms(design: WorldDesign) -> Sequence[str]:
    """Every distinct form the design declares, sorted."""
    return sorted({item.form for item in design.accessions})
