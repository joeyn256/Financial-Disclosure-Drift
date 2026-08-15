-- Disclosure Drift operational catalog, migration 0014 (M3.3 pre-E0 correction).
-- Governing records: Decision 081 R46; Decision 082 section 10; Decision 083 R58-R62.
--
-- Purpose: a genuinely multi-registrant accession has no lawful single registrant
-- anchor. The schema through migration 0013 asserts one anyway -- three NOT NULL
-- scalar registrant columns and a freeze invariant demanding "exactly one anchor per
-- accession" -- so the catalog cannot represent the truth even when the parse knows it.
-- Decision 081 R46 prohibits every heuristic that would manufacture that anchor, and
-- Decision 083 R58 makes the relation, not a scalar, authoritative.
--
-- This migration is PROSPECTIVE and PRE-E0. Every affected table is empty (Decision 081
-- section 9: census_parser_runs, census_parsed_records, and census_accessions are all 0,
-- parser_state is not_started for all 76 accepted M3.2 plan sources, and no candidate
-- snapshot, selection run, or manifest version exists), so each STRICT-table rebuild
-- copies zero rows and no accepted real identity is rewritten. The migration is never
-- applied to the accepted private M3.2 operational catalog while any real E0 candidate,
-- snapshot, selection, or manifest identity exists (Decision 083 section 10); the
-- section 12 empty-table preconditions below are what enforce that mechanically.
--
-- Rollback is revert-and-rebuild from 0001-0013, exactly as Decision 082 section 10.12
-- states. Migrations are forward-only and no down-migration is proposed. Migrations
-- 0001-0013 are untouched, including 0003's and 0009's own bytes; what changes here is
-- the live schema those migrations produced, rebuilt in place.
--
-- Eight changes, at Decision 082 section 10.5's numbering:
--   1. census_accessions.registrant_cik_numeric NOT NULL -> nullable   (table rebuild)
--   2. new census_accession_registrants relation and index             (CREATE TABLE)
--   3. new per-accession registrant_set_completeness fact              (column, rebuild)
--   4. pilot_candidate_accessions.anchor_cik_numeric -> nullable       (table rebuild)
--   5. pilot_candidate_accession_registrants completeness extension    (table rebuild)
--   6. pilot_selected_accessions.anchor_cik_numeric -> nullable        (table rebuild)
--   7. replace the pilot_snapshot_freeze_requires_valid_state anchor clause
--   8. new freeze invariant: anchor present IFF exactly one established substantive
--      association -- plus the section 10.11 selection-attachment rule the composite
--      foreign key stops enforcing once the anchor may be NULL.
--
-- The application prepends BEGIN IMMEDIATE, records this migration's exact name and
-- checksum in ops_schema_migrations, commits that row in this same transaction, and
-- then restores PRAGMA foreign_keys. Every rebuild below therefore runs inside one
-- atomic schema transaction: there is no window in which a half-corrected schema is
-- durable.
--
-- PRAGMA legacy_alter_table is enabled for the duration and restored at the end. Each
-- rebuild is the documented create-copy-drop-rename sequence, and in the default
-- (non-legacy) mode ALTER TABLE ... RENAME reparses the WHOLE schema to rewrite
-- references to the renamed object. That reparse fails here for a reason that is
-- correct to bypass and nothing else: between DROP and RENAME the schema transiently
-- carries triggers on OTHER tables -- pilot_selection_run_requires_clean_non_feasible_result
-- and pilot_selection_run_feasible_requires_actual_results, both frozen verbatim from
-- Decision 021 section 15.1 by migration 0013 -- whose bodies read the table currently
-- being replaced. Nothing needs rewriting in the first place: every rebuilt table is
-- renamed BACK to its original name, so all existing foreign-key clauses and trigger
-- bodies already name the correct object once the rename completes. Legacy mode skips
-- the transient validation, not the rename. The alternative would be dropping and
-- reproducing the Decision 021 section 15.1 triggers inside this migration, which would
-- copy frozen accepted SQL into a new record for a purely mechanical ordering reason.
PRAGMA legacy_alter_table = ON;

-- --------------------------------------------------------------------------
-- Section 1. Preconditions -- every affected table must be empty
--
-- Decision 082 section 10.12's hard precondition, stated as executable SQL rather than
-- as prose an operator is trusted to have read. A non-empty table means a real identity
-- exists, which would make this a DATA migration rather than a prospective schema
-- correction -- a materially different act requiring its own authorization. RAISE(ABORT)
-- inside the migration transaction rolls the whole script back, so a catalog that fails
-- this gate is left byte-identical at 0013.
-- --------------------------------------------------------------------------

CREATE TEMPORARY TABLE _m0014_precondition_guard (n INTEGER PRIMARY KEY);

CREATE TEMPORARY TRIGGER _m0014_require_empty_tables
BEFORE INSERT ON _m0014_precondition_guard
BEGIN
    SELECT RAISE(ABORT, 'migration 0014 requires an empty census_accessions')
    WHERE EXISTS (SELECT 1 FROM census_accessions);
    SELECT RAISE(ABORT, 'migration 0014 requires an empty census_accession_observations')
    WHERE EXISTS (SELECT 1 FROM census_accession_observations);
    SELECT RAISE(ABORT, 'migration 0014 requires empty census_parsed_records')
    WHERE EXISTS (SELECT 1 FROM census_parsed_records);
    SELECT RAISE(ABORT, 'migration 0014 requires empty census_parser_runs')
    WHERE EXISTS (SELECT 1 FROM census_parser_runs);
    SELECT RAISE(ABORT, 'migration 0014 requires empty pilot_candidate_snapshots')
    WHERE EXISTS (SELECT 1 FROM pilot_candidate_snapshots);
    SELECT RAISE(ABORT, 'migration 0014 requires empty pilot_candidate_accessions')
    WHERE EXISTS (SELECT 1 FROM pilot_candidate_accessions);
    SELECT RAISE(ABORT, 'migration 0014 requires empty pilot_candidate_accession_registrants')
    WHERE EXISTS (SELECT 1 FROM pilot_candidate_accession_registrants);
    SELECT RAISE(ABORT, 'migration 0014 requires empty pilot_selection_runs')
    WHERE EXISTS (SELECT 1 FROM pilot_selection_runs);
    SELECT RAISE(ABORT, 'migration 0014 requires empty pilot_selected_accessions')
    WHERE EXISTS (SELECT 1 FROM pilot_selected_accessions);
    SELECT RAISE(ABORT, 'migration 0014 requires empty pilot_manifest_versions')
    WHERE EXISTS (SELECT 1 FROM pilot_manifest_versions);
END;

INSERT INTO _m0014_precondition_guard (n) VALUES (1);

DROP TRIGGER _m0014_require_empty_tables;
DROP TABLE _m0014_precondition_guard;

-- --------------------------------------------------------------------------
-- Section 2. census_accessions -- changes 1 and 3
--
-- The scalar registrant becomes nullable because Decision 083 R58 requires it to be
-- NULL for an established substantive set of cardinality > 1, and SQLite cannot relax
-- NOT NULL in place. registrant_set_completeness is the per-accession fact Decision 082
-- section 10.2 found missing: under Decision 072 R23 section 5.2 an accession with no
-- accepted full-index rows has an EMPTY associated set and is today indistinguishable
-- from a genuine single-registrant filing. Decision 083 R59 forbids reading that silence
-- as proof of a sole registrant, so the state defaults to 'unestablished' -- fail closed.
--
-- submitter_cik_numeric is deliberately UNCHANGED and stays NOT NULL. The submitter is a
-- real per-submission fact and is never promoted to registrant identity: that promotion
-- is exactly the MR-3(a) recommendation Decision 081 R46 section 3.2(7) rejected.
--
-- No provenance is lost when the scalar goes NULL. The observation that produced each
-- registrant value already lives in census_accession_observations with its own
-- source_observation_id and parsed_record_id, and Decision 012 field resolution already
-- records winning and competing observations. The scalar was a convenience projection.
-- --------------------------------------------------------------------------

CREATE TABLE census_accessions_m0014 (
    accession_plain     TEXT PRIMARY KEY,
    accession_dashed    TEXT NOT NULL UNIQUE,
    -- Decision 083 R58: factual only for an ESTABLISHED substantive set of cardinality
    -- exactly 1; NULL above it. No arbitrary primary CIK is ever written here.
    registrant_cik_numeric INTEGER REFERENCES census_registrants(cik_numeric),
    -- Decision 083 R59. 'unestablished' is the fail-closed default and is NEVER
    -- evidence of a sole registrant.
    registrant_set_completeness TEXT NOT NULL DEFAULT 'unestablished'
        CHECK (registrant_set_completeness IN ('established', 'unestablished')),
    submitter_cik_numeric INTEGER NOT NULL,
    form_type           TEXT NOT NULL,
    is_amendment        INTEGER NOT NULL CHECK (is_amendment IN (0, 1)),
    is_discovery_form   INTEGER NOT NULL CHECK (is_discovery_form IN (0, 1)),
    is_negative_control INTEGER NOT NULL CHECK (is_negative_control IN (0, 1)),
    filing_date_sec     TEXT,
    report_date         TEXT,
    acceptance_datetime_sec_raw TEXT,
    acceptance_date_sec TEXT,
    official_filing_temporal_cohort TEXT,
    accepted_temporal_cohort TEXT,
    date_divergence_reason TEXT,
    primary_document_name TEXT,
    xbrl_flag           INTEGER,
    inline_xbrl_flag    INTEGER,
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    parsed_record_id    TEXT NOT NULL REFERENCES census_parsed_records(parsed_record_id),
    first_observed_at_utc TEXT NOT NULL,
    latest_observed_at_utc TEXT NOT NULL
) STRICT;

INSERT INTO census_accessions_m0014 (
    accession_plain, accession_dashed, registrant_cik_numeric, submitter_cik_numeric,
    form_type, is_amendment, is_discovery_form, is_negative_control, filing_date_sec,
    report_date, acceptance_datetime_sec_raw, acceptance_date_sec,
    official_filing_temporal_cohort, accepted_temporal_cohort, date_divergence_reason,
    primary_document_name, xbrl_flag, inline_xbrl_flag, source_observation_id,
    parsed_record_id, first_observed_at_utc, latest_observed_at_utc)
SELECT
    accession_plain, accession_dashed, registrant_cik_numeric, submitter_cik_numeric,
    form_type, is_amendment, is_discovery_form, is_negative_control, filing_date_sec,
    report_date, acceptance_datetime_sec_raw, acceptance_date_sec,
    official_filing_temporal_cohort, accepted_temporal_cohort, date_divergence_reason,
    primary_document_name, xbrl_flag, inline_xbrl_flag, source_observation_id,
    parsed_record_id, first_observed_at_utc, latest_observed_at_utc
FROM census_accessions;

DROP TABLE census_accessions;
ALTER TABLE census_accessions_m0014 RENAME TO census_accessions;

-- --------------------------------------------------------------------------
-- Section 3. census_accession_registrants -- change 2
--
-- Decision 083 R58's canonical census-layer relation between an accession and ALL
-- substantive registrants established for it. Decision 082 section 10.4 found that no
-- durable census-level accession-to-registrant relation exists today: the association
-- set is recomputed at snapshot-build time, and the only durable census attribution was
-- the scalar this migration makes nullable. Once that scalar is NULL, census-layer
-- attribution would have no stored representation at all without this table.
--
-- inventory_accession_registrants (migration 0001) is the right SHAPE precedent but is
-- the M2.1 inventory layer and is not consumed by the census or pilot path; it is NOT
-- reused and is left untouched.
--
-- The relation is created EMPTY. Its writer is the real durable offline parse (M3.3-E0),
-- which is not authorized by Decision 083; until then an accession has no census-layer
-- association rows and its registrant_set_completeness stays 'unestablished', which is
-- the correct fail-closed reading and never a claim of sole registrancy.
-- --------------------------------------------------------------------------

CREATE TABLE census_accession_registrants (
    accession_plain         TEXT NOT NULL REFERENCES census_accessions(accession_plain),
    registrant_cik_numeric  INTEGER NOT NULL REFERENCES census_registrants(cik_numeric),
    registrant_cik_padded   TEXT NOT NULL
        CHECK (length(registrant_cik_padded) = 10
               AND registrant_cik_padded NOT GLOB '*[^0-9]*'),
    -- 'substantive' is a registrant association; 'submitter_only' is the noncontributing
    -- submitter Decision 019 section 6.2 keeps visible and never counts as a registrant.
    association_class       TEXT NOT NULL
        CHECK (association_class IN ('substantive', 'submitter_only')),
    evidence_level          TEXT NOT NULL
        CHECK (evidence_level IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
    source_observation_id   TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    parsed_record_id        TEXT REFERENCES census_parsed_records(parsed_record_id),
    first_observed_at_utc   TEXT NOT NULL,
    latest_observed_at_utc  TEXT NOT NULL,
    PRIMARY KEY (accession_plain, registrant_cik_numeric)
) STRICT;

CREATE INDEX idx_census_accession_registrants_cik
    ON census_accession_registrants (registrant_cik_numeric);

-- Decision 083 R58, enforced rather than documented: once the census layer establishes a
-- substantive set of cardinality > 1 for an accession, that accession's scalar registrant
-- MUST be NULL. There is no arbitrary primary CIK, so there is nothing lawful to leave in
-- the column. The guard fires on the relation write because that is when cardinality
-- becomes knowable, and again on any later attempt to write a scalar back.
CREATE TRIGGER census_accession_registrants_forbid_multi_scalar_insert
AFTER INSERT ON census_accession_registrants
WHEN NEW.association_class = 'substantive'
BEGIN
    SELECT RAISE(ABORT,
        'census accession with more than one substantive registrant must have a NULL registrant_cik_numeric')
    WHERE (
        SELECT COUNT(*) FROM census_accession_registrants
        WHERE accession_plain = NEW.accession_plain AND association_class = 'substantive'
    ) > 1
      AND (
        SELECT registrant_cik_numeric FROM census_accessions
        WHERE accession_plain = NEW.accession_plain
    ) IS NOT NULL;
END;

CREATE TRIGGER census_accessions_forbid_multi_scalar_update
BEFORE UPDATE OF registrant_cik_numeric ON census_accessions
WHEN NEW.registrant_cik_numeric IS NOT NULL
BEGIN
    SELECT RAISE(ABORT,
        'census accession with more than one substantive registrant must have a NULL registrant_cik_numeric')
    WHERE (
        SELECT COUNT(*) FROM census_accession_registrants
        WHERE accession_plain = NEW.accession_plain AND association_class = 'substantive'
    ) > 1;
END;

-- Decision 083 R59: 'established' is a claim that the COMPLETE substantive association
-- set is known, so it requires at least one substantive relation row to stand on. An
-- established set is never empty, and the claim can never be made by assertion alone.
CREATE TRIGGER census_accessions_established_requires_relation
BEFORE UPDATE OF registrant_set_completeness ON census_accessions
WHEN NEW.registrant_set_completeness = 'established'
BEGIN
    SELECT RAISE(ABORT,
        'census accession registrant_set_completeness = established requires at least one substantive association')
    WHERE NOT EXISTS (
        SELECT 1 FROM census_accession_registrants
        WHERE accession_plain = NEW.accession_plain AND association_class = 'substantive'
    );
END;

-- --------------------------------------------------------------------------
-- Section 4. pilot_candidate_accessions -- change 4
--
-- anchor_cik_numeric becomes nullable, and the accession carries the completeness state
-- its candidacy depends on. Two table CHECKs make Decision 083 R58's and R59's core
-- invariants structural rather than advisory:
--
--   * an anchor may exist only under 'established' -- silence never earns one;
--   * under 'established', the anchor is present EXACTLY when the accession is not
--     multi-registrant. Established cardinality is at least 1, so "anchor present" and
--     "cardinality exactly 1" are the same condition, and "anchor absent" and
--     "multi_registrant = 1" are the same condition.
--
-- The cardinality half of change 8 -- that a present anchor really is the sole
-- substantive association -- needs the registrant relation and is therefore a freeze
-- trigger clause (section 7 below), not a table CHECK.
--
-- Every other column, CHECK, key, and comment is reproduced unchanged from migration
-- 0009. This is a rebuild, not a redesign.
--
-- pilot_snapshot_freeze_requires_valid_state reads both candidate tables and is being
-- replaced by section 7 in any case. It is dropped here rather than there so that no
-- statement in this migration is ever prepared against a schema in which that trigger
-- names a table that does not currently exist. Dropping it early is ordering, not an
-- additional change: section 7 creates its replacement.
-- --------------------------------------------------------------------------

DROP TRIGGER pilot_snapshot_freeze_requires_valid_state;

CREATE TABLE pilot_candidate_accessions_m0014 (
    snapshot_id                     TEXT NOT NULL REFERENCES pilot_candidate_snapshots(snapshot_id),
    accession_plain                 TEXT NOT NULL,
    accession_number_dashed         TEXT NOT NULL,
    accession_tie_break_sha256      TEXT NOT NULL
        CHECK (length(accession_tie_break_sha256) = 64
               AND accession_tie_break_sha256 NOT GLOB '*[^0-9a-f]*'),
    -- Decision 083 R58: NULL whenever the accession does not have exactly one
    -- established substantive registrant.
    anchor_cik_numeric               INTEGER,
    -- Decision 083 R59: an unestablished set blocks candidacy entirely. The builder
    -- excludes such accessions before they reach a snapshot; the freeze guard in
    -- section 7 refuses any that arrive anyway.
    registrant_set_completeness      TEXT NOT NULL
        CHECK (registrant_set_completeness IN ('established', 'unestablished')),
    form_type                        TEXT NOT NULL REFERENCES reference_form_types(form_type),
    is_amendment                     INTEGER NOT NULL CHECK (is_amendment IN (0, 1)),
    official_filing_date             TEXT,
    report_date                      TEXT,
    acceptance_audit_date            TEXT,
    filing_date_evidence_level       TEXT NOT NULL
        CHECK (filing_date_evidence_level IN
               ('provisional', 'review_required', 'conflicting', 'unavailable')),
    filing_date_resolution_sha256    TEXT
        CHECK (filing_date_resolution_sha256 IS NULL
               OR (length(filing_date_resolution_sha256) = 64
                   AND filing_date_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    filing_date_precedence           INTEGER
        CHECK (filing_date_precedence IS NULL OR filing_date_precedence = 2),
    provisional_official_cohort      TEXT
        CHECK (provisional_official_cohort IS NULL OR provisional_official_cohort IN (
            'development', 'transition', 'primary_test', 'prospective', 'monitoring')),
    acceptance_audit_cohort           TEXT
        CHECK (acceptance_audit_cohort IS NULL OR acceptance_audit_cohort IN (
            'development', 'transition', 'primary_test', 'prospective', 'monitoring')),
    cohort_evidence_level             TEXT NOT NULL
        CHECK (cohort_evidence_level IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
    cohort_resolution_sha256          TEXT
        CHECK (cohort_resolution_sha256 IS NULL
               OR (length(cohort_resolution_sha256) = 64
                   AND cohort_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    cohort_ambiguous                  INTEGER NOT NULL DEFAULT 0 CHECK (cohort_ambiguous IN (0, 1)),
    has_xbrl                          INTEGER NOT NULL DEFAULT 0 CHECK (has_xbrl IN (0, 1)),
    has_inline_xbrl                   INTEGER NOT NULL DEFAULT 0 CHECK (has_inline_xbrl IN (0, 1)),
    xbrl_evidence_level               TEXT NOT NULL
        CHECK (xbrl_evidence_level IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
    xbrl_resolution_sha256            TEXT
        CHECK (xbrl_resolution_sha256 IS NULL
               OR (length(xbrl_resolution_sha256) = 64
                   AND xbrl_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    amendment_linkage_state            TEXT
        CHECK (amendment_linkage_state IS NULL OR amendment_linkage_state IN (
            'amends_original', 'amends_prior_amendment', 'supplements_original',
            'possible_amendment_of', 'unresolved_amendment')),
    provisional_parent_accession       TEXT,
    amendment_purpose_category         TEXT
        CHECK (amendment_purpose_category IS NULL OR amendment_purpose_category IN (
            'administrative_or_exhibit', 'financial_or_xbrl_correction', 'narrative_or_governance')),
    -- Decision 014 section 6: amendment purpose is marked 'provisional' or 'unproven'
    -- only during M2.3 (definitive verification is filing-body evidence, M2.5).
    -- 'unproven' is distinct from the general review_required/conflicting/unavailable
    -- vocabulary: it means the category IS assignable from metadata but not provable
    -- without document evidence -- the ordinary case for every M2.3 amendment.
    amendment_purpose_evidence_level   TEXT NOT NULL
        CHECK (amendment_purpose_evidence_level IN
               ('provisional', 'unproven', 'review_required', 'conflicting', 'unavailable')),
    amendment_purpose_resolution_sha256 TEXT
        CHECK (amendment_purpose_resolution_sha256 IS NULL
               OR (length(amendment_purpose_resolution_sha256) = 64
                   AND amendment_purpose_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    -- No amendment-purpose classification may satisfy an affirmative quota at the
    -- 'unproven' level (Decision 014 section 6); only 'provisional' can.
    amendment_purpose_quota_eligible   INTEGER NOT NULL DEFAULT 0
        CHECK (amendment_purpose_quota_eligible IN (0, 1)),
    base_eligible                      INTEGER NOT NULL DEFAULT 0 CHECK (base_eligible IN (0, 1)),
    stress_eligible                    INTEGER NOT NULL DEFAULT 0 CHECK (stress_eligible IN (0, 1)),
    support_eligible                   INTEGER NOT NULL DEFAULT 0 CHECK (support_eligible IN (0, 1)),
    control_eligible                   INTEGER NOT NULL DEFAULT 0 CHECK (control_eligible IN (0, 1)),
    multi_registrant                   INTEGER NOT NULL DEFAULT 0 CHECK (multi_registrant IN (0, 1)),
    recorded_at_utc                    TEXT NOT NULL,
    detail                             TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (snapshot_id, accession_plain),
    UNIQUE (snapshot_id, accession_number_dashed),
    CHECK (base_eligible = 0
           OR (is_amendment = 0 AND cohort_ambiguous = 0 AND provisional_official_cohort IS NOT NULL)),
    CHECK ((official_filing_date IS NULL) = (filing_date_resolution_sha256 IS NULL)),
    CHECK ((provisional_official_cohort IS NULL) = (cohort_resolution_sha256 IS NULL)),
    CHECK ((xbrl_resolution_sha256 IS NOT NULL) = (xbrl_evidence_level = 'provisional')),
    CHECK ((amendment_purpose_category IS NULL) = (amendment_purpose_resolution_sha256 IS NULL)),
    CHECK (amendment_purpose_quota_eligible = 0
           OR (amendment_purpose_category IS NOT NULL
               AND amendment_purpose_evidence_level = 'provisional')),
    CHECK (is_amendment = 1 OR (amendment_linkage_state IS NULL AND provisional_parent_accession IS NULL)),
    CHECK (is_amendment = 0 OR amendment_linkage_state IS NOT NULL),
    -- Decision 083 R58/R59: an anchor exists only under an established set.
    CHECK (anchor_cik_numeric IS NULL OR registrant_set_completeness = 'established'),
    -- Decision 083 R58 and Decision 072 R23 section 5.3 restated anchor-free: under an
    -- established set the anchor is present exactly when the accession is not
    -- multi-registrant. The extension is identical to "one anchor plus at least one
    -- distinct valid associated registrant"; only the false primacy is gone.
    CHECK (registrant_set_completeness <> 'established'
           OR ((anchor_cik_numeric IS NULL) = (multi_registrant = 1)))
) STRICT;

INSERT INTO pilot_candidate_accessions_m0014 (
    snapshot_id, accession_plain, accession_number_dashed, accession_tie_break_sha256,
    anchor_cik_numeric, registrant_set_completeness, form_type, is_amendment,
    official_filing_date, report_date, acceptance_audit_date, filing_date_evidence_level,
    filing_date_resolution_sha256, filing_date_precedence, provisional_official_cohort,
    acceptance_audit_cohort, cohort_evidence_level, cohort_resolution_sha256,
    cohort_ambiguous, has_xbrl, has_inline_xbrl, xbrl_evidence_level,
    xbrl_resolution_sha256, amendment_linkage_state, provisional_parent_accession,
    amendment_purpose_category, amendment_purpose_evidence_level,
    amendment_purpose_resolution_sha256, amendment_purpose_quota_eligible, base_eligible,
    stress_eligible, support_eligible, control_eligible, multi_registrant,
    recorded_at_utc, detail)
SELECT
    snapshot_id, accession_plain, accession_number_dashed, accession_tie_break_sha256,
    anchor_cik_numeric, 'established', form_type, is_amendment,
    official_filing_date, report_date, acceptance_audit_date, filing_date_evidence_level,
    filing_date_resolution_sha256, filing_date_precedence, provisional_official_cohort,
    acceptance_audit_cohort, cohort_evidence_level, cohort_resolution_sha256,
    cohort_ambiguous, has_xbrl, has_inline_xbrl, xbrl_evidence_level,
    xbrl_resolution_sha256, amendment_linkage_state, provisional_parent_accession,
    amendment_purpose_category, amendment_purpose_evidence_level,
    amendment_purpose_resolution_sha256, amendment_purpose_quota_eligible, base_eligible,
    stress_eligible, support_eligible, control_eligible, multi_registrant,
    recorded_at_utc, detail
FROM pilot_candidate_accessions;

DROP TABLE pilot_candidate_accessions;
ALTER TABLE pilot_candidate_accessions_m0014 RENAME TO pilot_candidate_accessions;

CREATE INDEX idx_pilot_candidate_accessions_cohort
    ON pilot_candidate_accessions (snapshot_id, provisional_official_cohort);
CREATE INDEX idx_pilot_candidate_accessions_eligibility
    ON pilot_candidate_accessions (snapshot_id, base_eligible, stress_eligible, support_eligible, control_eligible);
CREATE INDEX idx_pilot_candidate_accessions_tie_break
    ON pilot_candidate_accessions (snapshot_id, accession_tie_break_sha256);

CREATE TRIGGER pilot_candidate_accessions_insert_guard
BEFORE INSERT ON pilot_candidate_accessions
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = NEW.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession insert requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accessions_update_guard
BEFORE UPDATE ON pilot_candidate_accessions
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession update requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accessions_delete_guard
BEFORE DELETE ON pilot_candidate_accessions
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession delete requires a building snapshot'); END;

-- --------------------------------------------------------------------------
-- Section 5. pilot_candidate_accession_registrants -- change 5
--
-- The candidate-layer relation already carried the full set, already collapsed duplicate
-- rows to distinct canonical CIKs, and was already snapshot-scoped. It needed a
-- completeness and association-class extension, not a redesign (Decision 082 section
-- 10.4). Both new columns enter REGISTRANT_TABLE_COLUMNS, so Decision 083 R61's
-- requirement that candidate_registrant_table_sha256 BIND the relation is satisfied by
-- construction: the completeness state and the substantive/submitter split are inside
-- the governed digest rather than beside it.
--
-- The existing role vocabulary ('anchor', 'associated', 'submitter_only') is NOT
-- widened. What changes is when 'anchor' may be used, never what the words mean.
--
-- uq_pilot_candidate_accession_single_anchor is reproduced unchanged. It enforces AT
-- MOST one anchor per accession; zero anchors already satisfied it, which is exactly the
-- multi-registrant case, so it needed no correction.
-- --------------------------------------------------------------------------

CREATE TABLE pilot_candidate_accession_registrants_m0014 (
    snapshot_id             TEXT NOT NULL,
    accession_plain         TEXT NOT NULL,
    registrant_cik_numeric  INTEGER NOT NULL,
    registrant_cik_padded   TEXT NOT NULL,
    role                    TEXT NOT NULL CHECK (role IN ('anchor', 'associated', 'submitter_only')),
    is_anchor               INTEGER NOT NULL CHECK (is_anchor IN (0, 1)),
    -- Decision 019 section 6.2: a submitter that is not a registrant never establishes
    -- the set. Making that explicit lets every substantive-set calculation read one
    -- column instead of re-deriving the rule from the role vocabulary.
    association_class       TEXT NOT NULL
        CHECK (association_class IN ('substantive', 'submitter_only')),
    -- Decision 083 R59, carried per row so the relation is self-describing and the
    -- state is inside the governed digest.
    registrant_set_completeness TEXT NOT NULL
        CHECK (registrant_set_completeness IN ('established', 'unestablished')),
    evidence_level          TEXT NOT NULL
        CHECK (evidence_level IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
    recorded_at_utc         TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, accession_plain, registrant_cik_numeric),
    FOREIGN KEY (snapshot_id, accession_plain)
        REFERENCES pilot_candidate_accessions (snapshot_id, accession_plain),
    CHECK ((role = 'anchor') = (is_anchor = 1)),
    CHECK ((role = 'submitter_only') = (association_class = 'submitter_only')),
    -- Decision 083 R58/R59: an anchor role is available only under an established set.
    CHECK (role <> 'anchor' OR registrant_set_completeness = 'established')
) STRICT;

INSERT INTO pilot_candidate_accession_registrants_m0014 (
    snapshot_id, accession_plain, registrant_cik_numeric, registrant_cik_padded, role,
    is_anchor, association_class, registrant_set_completeness, evidence_level,
    recorded_at_utc)
SELECT
    snapshot_id, accession_plain, registrant_cik_numeric, registrant_cik_padded, role,
    is_anchor,
    CASE WHEN role = 'submitter_only' THEN 'submitter_only' ELSE 'substantive' END,
    'established', evidence_level, recorded_at_utc
FROM pilot_candidate_accession_registrants;

DROP TABLE pilot_candidate_accession_registrants;
ALTER TABLE pilot_candidate_accession_registrants_m0014
    RENAME TO pilot_candidate_accession_registrants;

-- A partial unique index alone cannot detect zero anchors; snapshot freeze
-- (see the trigger below) separately requires the exact anchor cardinality.
CREATE UNIQUE INDEX uq_pilot_candidate_accession_single_anchor
    ON pilot_candidate_accession_registrants (snapshot_id, accession_plain)
    WHERE is_anchor = 1;

CREATE INDEX idx_pilot_candidate_accession_registrants_cik
    ON pilot_candidate_accession_registrants (registrant_cik_numeric);

CREATE TRIGGER pilot_candidate_accession_registrants_insert_guard
BEFORE INSERT ON pilot_candidate_accession_registrants
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = NEW.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate registrant insert requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accession_registrants_update_guard
BEFORE UPDATE ON pilot_candidate_accession_registrants
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate registrant update requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accession_registrants_delete_guard
BEFORE DELETE ON pilot_candidate_accession_registrants
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate registrant delete requires a building snapshot'); END;

-- --------------------------------------------------------------------------
-- Section 6. pilot_selected_accessions -- change 6
--
-- anchor_cik_numeric becomes nullable on the same condition. The composite foreign key
-- to pilot_selected_entities is reproduced UNCHANGED and needs no trigger of its own:
-- SQLite's default MATCH SIMPLE semantics mean a composite foreign key is not enforced
-- for a row in which any column is NULL, so a NULL anchor satisfies it vacuously and
-- correctly. What that foreign key stops enforcing is replaced by the section 8
-- attachment rule below -- not left unenforced.
-- --------------------------------------------------------------------------

CREATE TABLE pilot_selected_accessions_m0014 (
    selection_run_id       TEXT NOT NULL,
    snapshot_id            TEXT NOT NULL,
    accession_plain        TEXT NOT NULL,
    -- Decision 083 R58/R61: NULL for an established multi-registrant accession. The
    -- relational registrant set is authoritative, and no replacement anchor is invented.
    anchor_cik_numeric     INTEGER,
    selected_order         INTEGER NOT NULL CHECK (selected_order >= 1),
    accession_hash_sha256  TEXT NOT NULL
        CHECK (length(accession_hash_sha256) = 64 AND accession_hash_sha256 NOT GLOB '*[^0-9a-f]*'),
    accession_role         TEXT NOT NULL CHECK (accession_role IN ('base', 'stress', 'support', 'control')),
    recorded_at_utc        TEXT NOT NULL,
    PRIMARY KEY (selection_run_id, snapshot_id, accession_plain),
    UNIQUE (selection_run_id, snapshot_id, selected_order),
    FOREIGN KEY (selection_run_id, snapshot_id)
        REFERENCES pilot_selection_runs (selection_run_id, snapshot_id),
    FOREIGN KEY (snapshot_id, accession_plain)
        REFERENCES pilot_candidate_accessions (snapshot_id, accession_plain),
    FOREIGN KEY (selection_run_id, snapshot_id, anchor_cik_numeric)
        REFERENCES pilot_selected_entities (selection_run_id, snapshot_id, cik_numeric)
) STRICT;

INSERT INTO pilot_selected_accessions_m0014 (
    selection_run_id, snapshot_id, accession_plain, anchor_cik_numeric, selected_order,
    accession_hash_sha256, accession_role, recorded_at_utc)
SELECT
    selection_run_id, snapshot_id, accession_plain, anchor_cik_numeric, selected_order,
    accession_hash_sha256, accession_role, recorded_at_utc
FROM pilot_selected_accessions;

DROP TABLE pilot_selected_accessions;
ALTER TABLE pilot_selected_accessions_m0014 RENAME TO pilot_selected_accessions;

CREATE INDEX idx_pilot_selected_accessions_anchor
    ON pilot_selected_accessions (selection_run_id, snapshot_id, anchor_cik_numeric);

CREATE TRIGGER pilot_selected_accessions_insert_guard
BEFORE INSERT ON pilot_selected_accessions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = NEW.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot selected accession write requires a running selection run'); END;
CREATE TRIGGER pilot_selected_accessions_update_guard
BEFORE UPDATE ON pilot_selected_accessions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot selected accession write requires a running selection run'); END;
CREATE TRIGGER pilot_selected_accessions_delete_guard
BEFORE DELETE ON pilot_selected_accessions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot selected accession write requires a running selection run'); END;

-- --------------------------------------------------------------------------
-- Section 7. The snapshot freeze invariant -- changes 7 and 8
--
-- The 0009 trigger demanded SUM(is_anchor) <> 1 be impossible: literally "freeze
-- requires exactly one anchor per accession". That is the false singleton, made a
-- release gate. It is replaced -- never merely relaxed -- by the exact Decision 083
-- R58/R59 conditions:
--
--   * every accession still has at least one registrant row (unchanged);
--   * every accession in a frozen snapshot is 'established' (R59: an unestablished set
--     blocks candidacy ENTIRELY, so one can never be frozen into a snapshot);
--   * the accession row and its registrant rows agree on the completeness state;
--   * anchor cardinality is EXACTLY 1 when the substantive set has cardinality 1, and
--     EXACTLY 0 above it -- no anchor exists for a joint filing;
--   * anchor_cik_numeric is non-NULL exactly when a sole substantive association exists,
--     and equals that association's CIK when present (change 8);
--   * multi_registrant agrees with the DISTINCT SUBSTANTIVE cardinality, restated
--     anchor-free at identical extension (Decision 072 R23 section 5.3).
--
-- Every other clause of the 0009 trigger -- the two count checks and the entity and
-- accession evidence-backing checks -- is reproduced byte-for-byte in its original
-- order. Only the anchor and multi_registrant clauses change. The DROP happened in
-- section 4, for the reparse-ordering reason stated there.
-- --------------------------------------------------------------------------

CREATE TRIGGER pilot_snapshot_freeze_requires_valid_state
BEFORE UPDATE OF snapshot_state ON pilot_candidate_snapshots
WHEN NEW.snapshot_state = 'frozen' AND OLD.snapshot_state = 'building'
BEGIN
    SELECT RAISE(ABORT, 'pilot snapshot freeze entity_count mismatch')
    WHERE NEW.entity_count IS NOT (
        SELECT COUNT(*) FROM pilot_candidate_entities WHERE snapshot_id = NEW.snapshot_id
    );
    SELECT RAISE(ABORT, 'pilot snapshot freeze accession_count mismatch')
    WHERE NEW.accession_count IS NOT (
        SELECT COUNT(*) FROM pilot_candidate_accessions WHERE snapshot_id = NEW.snapshot_id
    );
    SELECT RAISE(ABORT, 'pilot snapshot freeze requires at least one registrant row per accession')
    WHERE EXISTS (
        SELECT a.accession_plain FROM pilot_candidate_accessions AS a
        WHERE a.snapshot_id = NEW.snapshot_id
          AND NOT EXISTS (
              SELECT 1 FROM pilot_candidate_accession_registrants AS r
              WHERE r.snapshot_id = a.snapshot_id AND r.accession_plain = a.accession_plain
          )
    );
    SELECT RAISE(ABORT,
        'pilot snapshot freeze requires an established registrant set for every accession')
    WHERE EXISTS (
        SELECT 1 FROM pilot_candidate_accessions AS a
        WHERE a.snapshot_id = NEW.snapshot_id
          AND a.registrant_set_completeness <> 'established'
    ) OR EXISTS (
        SELECT 1 FROM pilot_candidate_accession_registrants AS r
        JOIN pilot_candidate_accessions AS a
          ON a.snapshot_id = r.snapshot_id AND a.accession_plain = r.accession_plain
        WHERE r.snapshot_id = NEW.snapshot_id
          AND r.registrant_set_completeness <> a.registrant_set_completeness
    );
    SELECT RAISE(ABORT,
        'pilot snapshot freeze requires exactly one anchor for a sole substantive registrant and none above it')
    WHERE EXISTS (
        SELECT 1 FROM pilot_candidate_accessions AS a
        WHERE a.snapshot_id = NEW.snapshot_id
          AND (
            SELECT COALESCE(SUM(r.is_anchor), 0) FROM pilot_candidate_accession_registrants AS r
            WHERE r.snapshot_id = a.snapshot_id AND r.accession_plain = a.accession_plain
          ) <> (
            CASE WHEN (
              SELECT COUNT(*) FROM pilot_candidate_accession_registrants AS r
              WHERE r.snapshot_id = a.snapshot_id AND r.accession_plain = a.accession_plain
                AND r.association_class = 'substantive'
            ) = 1 THEN 1 ELSE 0 END
          )
    );
    SELECT RAISE(ABORT,
        'pilot snapshot freeze requires anchor_cik_numeric to be the sole substantive registrant or NULL')
    WHERE EXISTS (
        SELECT 1 FROM pilot_candidate_accessions AS a
        WHERE a.snapshot_id = NEW.snapshot_id
          AND a.anchor_cik_numeric IS NOT (
            SELECT r.registrant_cik_numeric FROM pilot_candidate_accession_registrants AS r
            WHERE r.snapshot_id = a.snapshot_id AND r.accession_plain = a.accession_plain
              AND r.association_class = 'substantive'
              AND (
                SELECT COUNT(*) FROM pilot_candidate_accession_registrants AS s
                WHERE s.snapshot_id = a.snapshot_id AND s.accession_plain = a.accession_plain
                  AND s.association_class = 'substantive'
              ) = 1
          )
    );
    SELECT RAISE(ABORT, 'pilot snapshot freeze multi_registrant flag inconsistent with registrant rows')
    WHERE EXISTS (
        SELECT 1 FROM pilot_candidate_accessions AS a
        WHERE a.snapshot_id = NEW.snapshot_id
          AND a.multi_registrant <> (
            CASE WHEN (
              SELECT COUNT(*) FROM pilot_candidate_accession_registrants AS r
              WHERE r.snapshot_id = a.snapshot_id AND r.accession_plain = a.accession_plain
                AND r.association_class = 'substantive'
            ) >= 2 THEN 1 ELSE 0 END
          )
    );
    -- Decision 016 section 4: "A resolved value with no supporting evidence
    -- row is not a valid candidate row." Any resolved entity dimension
    -- (size/industry/history/primary_universe) requires at least one winning
    -- or supporting evidence row for that snapshot/cik/dimension; an
    -- unresolved (NULL) dimension requires none.
    SELECT RAISE(ABORT, 'pilot snapshot freeze requires entity evidence backing for every resolved dimension')
    WHERE EXISTS (
        SELECT 1 FROM pilot_candidate_entities AS e
        WHERE e.snapshot_id = NEW.snapshot_id
          AND (
            (e.size_resolution_sha256 IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM pilot_candidate_entity_evidence AS ev
                WHERE ev.snapshot_id = e.snapshot_id AND ev.cik_numeric = e.cik_numeric
                  AND ev.classification_dimension = 'size'
                  AND ev.evidence_role IN ('winning', 'supporting')
            ))
            OR (e.industry_resolution_sha256 IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM pilot_candidate_entity_evidence AS ev
                WHERE ev.snapshot_id = e.snapshot_id AND ev.cik_numeric = e.cik_numeric
                  AND ev.classification_dimension = 'industry'
                  AND ev.evidence_role IN ('winning', 'supporting')
            ))
            OR (e.history_resolution_sha256 IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM pilot_candidate_entity_evidence AS ev
                WHERE ev.snapshot_id = e.snapshot_id AND ev.cik_numeric = e.cik_numeric
                  AND ev.classification_dimension = 'history'
                  AND ev.evidence_role IN ('winning', 'supporting')
            ))
            OR (e.primary_universe_resolution_sha256 IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM pilot_candidate_entity_evidence AS ev
                WHERE ev.snapshot_id = e.snapshot_id AND ev.cik_numeric = e.cik_numeric
                  AND ev.classification_dimension = 'primary_universe'
                  AND ev.evidence_role IN ('winning', 'supporting')
            ))
          )
    );
    SELECT RAISE(ABORT, 'pilot snapshot freeze requires accession evidence backing for every resolved dimension')
    WHERE EXISTS (
        SELECT 1 FROM pilot_candidate_accessions AS a
        WHERE a.snapshot_id = NEW.snapshot_id
          AND (
            (a.filing_date_resolution_sha256 IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM pilot_candidate_accession_evidence AS ev
                WHERE ev.snapshot_id = a.snapshot_id AND ev.accession_plain = a.accession_plain
                  AND ev.classification_dimension = 'filing_date'
                  AND ev.evidence_role IN ('winning', 'supporting')
            ))
            OR (a.cohort_resolution_sha256 IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM pilot_candidate_accession_evidence AS ev
                WHERE ev.snapshot_id = a.snapshot_id AND ev.accession_plain = a.accession_plain
                  AND ev.classification_dimension = 'cohort'
                  AND ev.evidence_role IN ('winning', 'supporting')
            ))
            OR (a.xbrl_resolution_sha256 IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM pilot_candidate_accession_evidence AS ev
                WHERE ev.snapshot_id = a.snapshot_id AND ev.accession_plain = a.accession_plain
                  AND ev.classification_dimension = 'xbrl'
                  AND ev.evidence_role IN ('winning', 'supporting')
            ))
            OR ((a.amendment_purpose_resolution_sha256 IS NOT NULL OR a.amendment_linkage_state IS NOT NULL)
                AND NOT EXISTS (
                SELECT 1 FROM pilot_candidate_accession_evidence AS ev
                WHERE ev.snapshot_id = a.snapshot_id AND ev.accession_plain = a.accession_plain
                  AND ev.classification_dimension = 'amendment_purpose'
                  AND ev.evidence_role IN ('winning', 'supporting')
            ))
          )
    );
END;

-- --------------------------------------------------------------------------
-- Section 8. Selection attachment -- the second half of change 8
--
-- Decision 082 section 10.11: with a NULL anchor the composite foreign key from
-- pilot_selected_accessions to pilot_selected_entities stops enforcing, so the binding
-- it provided is restated explicitly:
--
--     A selected accession must have at least one substantive registrant association
--     that is a selected entity in the same selection run.
--
-- For a single-registrant accession this is byte-equivalent to the foreign key it
-- replaces. For a multi-registrant accession it is satisfied by ANY co-selected
-- substantive registrant, without designating one. ATTACHMENT IS NOT PRIMACY, and this
-- rule never writes a CIK into an anchor column.
--
-- BEFORE INSERT matches the timing of the foreign key it supplements: the selection
-- store writes selected entities before selected accessions, exactly as the existing
-- composite foreign key already requires.
-- --------------------------------------------------------------------------

CREATE TRIGGER pilot_selected_accession_requires_selected_registrant
BEFORE INSERT ON pilot_selected_accessions
BEGIN
    SELECT RAISE(ABORT,
        'selected accession requires at least one substantive registrant selected in the same run')
    WHERE NOT EXISTS (
        SELECT 1 FROM pilot_candidate_accession_registrants AS r
        JOIN pilot_selected_entities AS e
          ON e.selection_run_id = NEW.selection_run_id
         AND e.snapshot_id = NEW.snapshot_id
         AND e.cik_numeric = r.registrant_cik_numeric
        WHERE r.snapshot_id = NEW.snapshot_id
          AND r.accession_plain = NEW.accession_plain
          AND r.association_class = 'substantive'
    );
END;

-- Every rebuild is complete and every renamed table carries its original name again, so
-- the default whole-schema rename validation is restored for the rest of this
-- connection's life. The migration never leaves it relaxed.
PRAGMA legacy_alter_table = OFF;
