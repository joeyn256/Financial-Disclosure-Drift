-- Disclosure Drift operational catalog, migration 0009 (Stage M2.3-S3.2).
-- Governing records: Decisions 002, 013, 014, 016.
--
-- Additive only: the M2.3 pilot candidate/selection/manifest table family.
-- No inventory_* table is referenced anywhere below (Decision 013 section 2:
-- inventory_accessions/inventory_accession_registrants are post-retrieval and
-- must not be relied upon before M2.5). Every table is STRICT. Content-derived
-- IDs and deterministic hashes are lowercase 64-character SHA-256 hex; evidence
-- levels exclude 'verified' throughout, since M2.3 evidence is metadata-only.

-- --------------------------------------------------------------------------
-- Candidate snapshot
-- --------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pilot_candidate_snapshots (
    snapshot_id                         TEXT PRIMARY KEY
        CHECK (length(snapshot_id) = 64 AND snapshot_id NOT GLOB '*[^0-9a-f]*'),
    census_run_id                       TEXT NOT NULL REFERENCES ops_ingestion_jobs(job_id),
    coverage_start                      TEXT NOT NULL,
    coverage_end                        TEXT NOT NULL,
    as_of_date                          TEXT NOT NULL,
    include_open_quarter                INTEGER NOT NULL DEFAULT 0
                                             CHECK (include_open_quarter = 0),
    coverage_policy_version             TEXT NOT NULL,
    candidate_policy_version            TEXT NOT NULL,
    sic_family_mapping_version          TEXT NOT NULL,
    evidence_policy_version             TEXT NOT NULL,
    coverage_window_sha256               TEXT NOT NULL
        CHECK (length(coverage_window_sha256) = 64
               AND coverage_window_sha256 NOT GLOB '*[^0-9a-f]*'),
    -- Required from INSERT onward, not only at freeze: snapshot_id is a
    -- content-derived ID fixed at row creation, and this hash is one of its
    -- declared inputs (Decision 016 section 1), so it must already be known
    -- when the ID is fixed rather than deferred to the freeze transition.
    input_observation_set_sha256         TEXT NOT NULL
        CHECK (length(input_observation_set_sha256) = 64
               AND input_observation_set_sha256 NOT GLOB '*[^0-9a-f]*'),
    candidate_entity_table_sha256        TEXT
        CHECK (candidate_entity_table_sha256 IS NULL
               OR (length(candidate_entity_table_sha256) = 64
                   AND candidate_entity_table_sha256 NOT GLOB '*[^0-9a-f]*')),
    candidate_accession_table_sha256     TEXT
        CHECK (candidate_accession_table_sha256 IS NULL
               OR (length(candidate_accession_table_sha256) = 64
                   AND candidate_accession_table_sha256 NOT GLOB '*[^0-9a-f]*')),
    candidate_registrant_table_sha256    TEXT
        CHECK (candidate_registrant_table_sha256 IS NULL
               OR (length(candidate_registrant_table_sha256) = 64
                   AND candidate_registrant_table_sha256 NOT GLOB '*[^0-9a-f]*')),
    candidate_entity_evidence_sha256     TEXT
        CHECK (candidate_entity_evidence_sha256 IS NULL
               OR (length(candidate_entity_evidence_sha256) = 64
                   AND candidate_entity_evidence_sha256 NOT GLOB '*[^0-9a-f]*')),
    candidate_accession_evidence_sha256  TEXT
        CHECK (candidate_accession_evidence_sha256 IS NULL
               OR (length(candidate_accession_evidence_sha256) = 64
                   AND candidate_accession_evidence_sha256 NOT GLOB '*[^0-9a-f]*')),
    candidate_entity_reasons_sha256      TEXT
        CHECK (candidate_entity_reasons_sha256 IS NULL
               OR (length(candidate_entity_reasons_sha256) = 64
                   AND candidate_entity_reasons_sha256 NOT GLOB '*[^0-9a-f]*')),
    candidate_accession_reasons_sha256   TEXT
        CHECK (candidate_accession_reasons_sha256 IS NULL
               OR (length(candidate_accession_reasons_sha256) = 64
                   AND candidate_accession_reasons_sha256 NOT GLOB '*[^0-9a-f]*')),
    candidate_snapshot_sha256            TEXT
        CHECK (candidate_snapshot_sha256 IS NULL
               OR (length(candidate_snapshot_sha256) = 64
                   AND candidate_snapshot_sha256 NOT GLOB '*[^0-9a-f]*')),
    snapshot_state                       TEXT NOT NULL
        CHECK (snapshot_state IN ('building', 'frozen', 'invalidated')),
    entity_count                         INTEGER CHECK (entity_count IS NULL OR entity_count >= 0),
    accession_count                      INTEGER
        CHECK (accession_count IS NULL OR accession_count >= 0),
    invalidated_reason_code              TEXT REFERENCES reference_reason_codes(reason_code),
    created_at_utc                       TEXT NOT NULL,
    frozen_at_utc                        TEXT,
    invalidated_at_utc                   TEXT,
    detail                               TEXT NOT NULL DEFAULT '',
    CHECK (snapshot_state <> 'building'
           OR (frozen_at_utc IS NULL AND candidate_snapshot_sha256 IS NULL)),
    CHECK (snapshot_state <> 'frozen'
           OR (frozen_at_utc IS NOT NULL
               AND candidate_snapshot_sha256 IS NOT NULL
               AND input_observation_set_sha256 IS NOT NULL
               AND candidate_entity_table_sha256 IS NOT NULL
               AND candidate_accession_table_sha256 IS NOT NULL
               AND candidate_registrant_table_sha256 IS NOT NULL
               AND candidate_entity_evidence_sha256 IS NOT NULL
               AND candidate_accession_evidence_sha256 IS NOT NULL
               AND candidate_entity_reasons_sha256 IS NOT NULL
               AND candidate_accession_reasons_sha256 IS NOT NULL
               AND entity_count IS NOT NULL
               AND accession_count IS NOT NULL)),
    CHECK (snapshot_state <> 'invalidated'
           OR (invalidated_at_utc IS NOT NULL AND invalidated_reason_code IS NOT NULL))
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_candidate_entities (
    snapshot_id                  TEXT NOT NULL REFERENCES pilot_candidate_snapshots(snapshot_id),
    cik_numeric                  INTEGER NOT NULL,
    cik_padded                   TEXT NOT NULL,
    entity_tie_break_sha256      TEXT NOT NULL
        CHECK (length(entity_tie_break_sha256) = 64
               AND entity_tie_break_sha256 NOT GLOB '*[^0-9a-f]*'),
    candidate_category            TEXT NOT NULL
        CHECK (candidate_category IN ('operating', 'control', 'ineligible')),
    control_kind                  TEXT
        CHECK (control_kind IS NULL OR control_kind IN (
            'registered_investment_company_or_etf', 'asset_backed_issuer',
            'shell_or_blank_check_issuer', 'foreign_private_issuer')),
    size_stratum                  TEXT
        CHECK (size_stratum IS NULL OR size_stratum IN (
            'large_accelerated', 'accelerated', 'non_accelerated_or_smaller')),
    size_evidence_level           TEXT NOT NULL
        CHECK (size_evidence_level IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
    size_resolution_sha256        TEXT
        CHECK (size_resolution_sha256 IS NULL
               OR (length(size_resolution_sha256) = 64
                   AND size_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    -- Canonical repository representation: exactly four numeric digits
    -- (zero-padded, e.g. '0100', '6021'); NULL when no SIC is on record.
    sic_code                      TEXT
        CHECK (sic_code IS NULL
               OR (length(sic_code) = 4 AND sic_code NOT GLOB '*[^0-9]*')),
    industry_family                TEXT
        CHECK (industry_family IS NULL OR industry_family IN (
            'technology_and_communications', 'operating_financial_institutions',
            'industrial_and_materials', 'consumer_retail_and_services',
            'healthcare_and_life_sciences', 'energy_and_utilities')),
    industry_quota_eligible        INTEGER NOT NULL DEFAULT 0
        CHECK (industry_quota_eligible IN (0, 1)),
    industry_evidence_level        TEXT NOT NULL
        CHECK (industry_evidence_level IN
               ('provisional', 'review_required', 'conflicting', 'unavailable')),
    industry_resolution_sha256     TEXT
        CHECK (industry_resolution_sha256 IS NULL
               OR (length(industry_resolution_sha256) = 64
                   AND industry_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    history_class                  TEXT CHECK (history_class IS NULL OR history_class IN ('stable', 'eventful')),
    history_evidence_level         TEXT NOT NULL
        CHECK (history_evidence_level IN
               ('provisional', 'review_required', 'conflicting', 'unavailable')),
    history_resolution_sha256      TEXT
        CHECK (history_resolution_sha256 IS NULL
               OR (length(history_resolution_sha256) = 64
                   AND history_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    currently_inactive              INTEGER NOT NULL DEFAULT 0 CHECK (currently_inactive IN (0, 1)),
    eligible_original_annual_report_count INTEGER NOT NULL DEFAULT 0
        CHECK (eligible_original_annual_report_count >= 0),
    primary_universe_eligible       INTEGER NOT NULL DEFAULT 0 CHECK (primary_universe_eligible IN (0, 1)),
    primary_universe_evidence_level TEXT NOT NULL
        CHECK (primary_universe_evidence_level IN
               ('provisional', 'review_required', 'conflicting', 'unavailable')),
    primary_universe_resolution_sha256 TEXT
        CHECK (primary_universe_resolution_sha256 IS NULL
               OR (length(primary_universe_resolution_sha256) = 64
                   AND primary_universe_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    engineering_only_stress         INTEGER NOT NULL DEFAULT 0 CHECK (engineering_only_stress IN (0, 1)),
    filing_time_name                TEXT NOT NULL,
    recorded_at_utc                 TEXT NOT NULL,
    detail                          TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (snapshot_id, cik_numeric),
    -- Direct, frozen structural implications only (Decision 002's full four-condition
    -- classification algorithm remains the candidate builder's responsibility).
    CHECK (primary_universe_eligible = 0 OR candidate_category = 'operating'),
    CHECK (engineering_only_stress = 0 OR primary_universe_eligible = 0),
    CHECK (primary_universe_eligible = 0 OR primary_universe_evidence_level = 'provisional'),
    CHECK (primary_universe_eligible = 0 OR primary_universe_resolution_sha256 IS NOT NULL),
    CHECK (primary_universe_eligible = 0
           OR sic_code IS NULL
           OR CAST(sic_code AS INTEGER) NOT BETWEEN 6000 AND 6999),
    CHECK (candidate_category = 'control' OR control_kind IS NULL),
    CHECK (candidate_category <> 'control' OR control_kind IS NOT NULL),
    CHECK ((size_stratum IS NULL) = (size_resolution_sha256 IS NULL)),
    CHECK ((industry_family IS NULL) = (industry_resolution_sha256 IS NULL)),
    CHECK ((history_class IS NULL) = (history_resolution_sha256 IS NULL)),
    CHECK (industry_quota_eligible = 0
           OR (industry_family IS NOT NULL AND industry_evidence_level = 'provisional'))
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_candidate_accessions (
    snapshot_id                     TEXT NOT NULL REFERENCES pilot_candidate_snapshots(snapshot_id),
    accession_plain                 TEXT NOT NULL,
    accession_number_dashed         TEXT NOT NULL,
    accession_tie_break_sha256      TEXT NOT NULL
        CHECK (length(accession_tie_break_sha256) = 64
               AND accession_tie_break_sha256 NOT GLOB '*[^0-9a-f]*'),
    anchor_cik_numeric               INTEGER NOT NULL,
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
    CHECK (is_amendment = 0 OR amendment_linkage_state IS NOT NULL)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_candidate_accession_registrants (
    snapshot_id             TEXT NOT NULL,
    accession_plain         TEXT NOT NULL,
    registrant_cik_numeric  INTEGER NOT NULL,
    registrant_cik_padded   TEXT NOT NULL,
    role                    TEXT NOT NULL CHECK (role IN ('anchor', 'associated', 'submitter_only')),
    is_anchor               INTEGER NOT NULL CHECK (is_anchor IN (0, 1)),
    evidence_level          TEXT NOT NULL
        CHECK (evidence_level IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
    recorded_at_utc         TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, accession_plain, registrant_cik_numeric),
    FOREIGN KEY (snapshot_id, accession_plain)
        REFERENCES pilot_candidate_accessions (snapshot_id, accession_plain),
    CHECK ((role = 'anchor') = (is_anchor = 1))
) STRICT;

-- A partial unique index alone cannot detect zero anchors; snapshot freeze
-- (see the trigger below) separately requires exactly one per accession.
CREATE UNIQUE INDEX IF NOT EXISTS uq_pilot_candidate_accession_single_anchor
    ON pilot_candidate_accession_registrants (snapshot_id, accession_plain)
    WHERE is_anchor = 1;

CREATE TABLE IF NOT EXISTS pilot_candidate_entity_evidence (
    evidence_id                TEXT PRIMARY KEY,
    snapshot_id                 TEXT NOT NULL,
    cik_numeric                 INTEGER NOT NULL,
    classification_dimension   TEXT NOT NULL
        CHECK (classification_dimension IN ('size', 'industry', 'history', 'primary_universe', 'identity')),
    evidence_role               TEXT NOT NULL CHECK (evidence_role IN ('winning', 'competing', 'supporting')),
    source_observation_id       TEXT NOT NULL,
    parsed_record_id            TEXT,
    source_field                 TEXT NOT NULL,
    canonical_observed_value     TEXT,
    policy_version               TEXT NOT NULL,
    precedence                   INTEGER NOT NULL CHECK (precedence >= 1),
    evidence_sha256              TEXT NOT NULL
        CHECK (length(evidence_sha256) = 64 AND evidence_sha256 NOT GLOB '*[^0-9a-f]*'),
    recorded_at_utc               TEXT NOT NULL,
    FOREIGN KEY (snapshot_id, cik_numeric)
        REFERENCES pilot_candidate_entities (snapshot_id, cik_numeric)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_candidate_accession_evidence (
    evidence_id                TEXT PRIMARY KEY,
    snapshot_id                 TEXT NOT NULL,
    accession_plain              TEXT NOT NULL,
    classification_dimension    TEXT NOT NULL
        CHECK (classification_dimension IN
               ('filing_date', 'cohort', 'xbrl', 'amendment_purpose', 'multi_registrant', 'identity')),
    evidence_role                TEXT NOT NULL CHECK (evidence_role IN ('winning', 'competing', 'supporting')),
    source_observation_id        TEXT NOT NULL,
    parsed_record_id             TEXT,
    source_field                  TEXT NOT NULL,
    canonical_observed_value      TEXT,
    policy_version                TEXT NOT NULL,
    precedence                    INTEGER NOT NULL CHECK (precedence >= 1),
    evidence_sha256                TEXT NOT NULL
        CHECK (length(evidence_sha256) = 64 AND evidence_sha256 NOT GLOB '*[^0-9a-f]*'),
    recorded_at_utc                 TEXT NOT NULL,
    FOREIGN KEY (snapshot_id, accession_plain)
        REFERENCES pilot_candidate_accessions (snapshot_id, accession_plain)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_candidate_entity_reasons (
    snapshot_id     TEXT NOT NULL,
    cik_numeric     INTEGER NOT NULL,
    reason_scope    TEXT NOT NULL
        CHECK (reason_scope IN ('eligibility', 'size', 'industry', 'history', 'primary_universe', 'identity')),
    reason_code     TEXT NOT NULL REFERENCES reference_reason_codes(reason_code),
    detail          TEXT NOT NULL DEFAULT '',
    recorded_at_utc TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, cik_numeric, reason_scope, reason_code),
    FOREIGN KEY (snapshot_id, cik_numeric)
        REFERENCES pilot_candidate_entities (snapshot_id, cik_numeric)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_candidate_accession_reasons (
    snapshot_id     TEXT NOT NULL,
    accession_plain TEXT NOT NULL,
    reason_scope    TEXT NOT NULL
        CHECK (reason_scope IN ('eligibility', 'cohort', 'xbrl', 'amendment', 'multi_registrant', 'identity')),
    reason_code     TEXT NOT NULL REFERENCES reference_reason_codes(reason_code),
    detail          TEXT NOT NULL DEFAULT '',
    recorded_at_utc TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, accession_plain, reason_scope, reason_code),
    FOREIGN KEY (snapshot_id, accession_plain)
        REFERENCES pilot_candidate_accessions (snapshot_id, accession_plain)
) STRICT;

-- --------------------------------------------------------------------------
-- Selection
-- --------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pilot_selection_runs (
    selection_run_id          TEXT PRIMARY KEY
        CHECK (length(selection_run_id) = 64 AND selection_run_id NOT GLOB '*[^0-9a-f]*'),
    snapshot_id                TEXT NOT NULL REFERENCES pilot_candidate_snapshots(snapshot_id),
    selection_seed             TEXT NOT NULL,
    selector_policy_version    TEXT NOT NULL,
    quota_policy_version       TEXT NOT NULL,
    search_node_limit          INTEGER NOT NULL CHECK (search_node_limit >= 1),
    expanded_node_count        INTEGER CHECK (expanded_node_count IS NULL OR expanded_node_count >= 0),
    node_limit_exhausted       INTEGER NOT NULL DEFAULT 0 CHECK (node_limit_exhausted IN (0, 1)),
    run_state                  TEXT NOT NULL CHECK (run_state IN (
        'planned', 'running', 'feasible', 'infeasible', 'infeasible_or_unproven', 'failed')),
    -- Increments exactly once on planned->running (to 1) and on each
    -- failed->running retry; stable on every other transition (Decision 016
    -- section 5 retry rule; see the attempt-tracking triggers below).
    current_attempt             INTEGER NOT NULL DEFAULT 1 CHECK (current_attempt >= 1),
    selected_entity_count       INTEGER CHECK (selected_entity_count IS NULL OR selected_entity_count >= 0),
    selected_accession_count    INTEGER
        CHECK (selected_accession_count IS NULL OR selected_accession_count >= 0),
    selection_input_sha256      TEXT NOT NULL
        CHECK (length(selection_input_sha256) = 64 AND selection_input_sha256 NOT GLOB '*[^0-9a-f]*'),
    selection_result_sha256     TEXT
        CHECK (selection_result_sha256 IS NULL
               OR (length(selection_result_sha256) = 64
                   AND selection_result_sha256 NOT GLOB '*[^0-9a-f]*')),
    failure_reason_code         TEXT REFERENCES reference_reason_codes(reason_code),
    started_at_utc               TEXT NOT NULL,
    finished_at_utc               TEXT,
    detail                        TEXT NOT NULL DEFAULT '',
    UNIQUE (selection_run_id, snapshot_id),
    -- SQLite CHECK expressions pass on NULL (only an explicit FALSE fails), so a
    -- bare ``selected_entity_count = 24`` silently admits a NULL declared count;
    -- IS NOT NULL is required explicitly on both feasible-state count columns.
    CHECK (run_state <> 'feasible'
           OR (selected_entity_count IS NOT NULL AND selected_entity_count = 24)),
    CHECK (run_state <> 'feasible' OR selected_accession_count IS NOT NULL),
    CHECK (run_state IN ('feasible', 'running')
           OR (selected_entity_count IS NULL OR selected_entity_count = 0)),
    CHECK (run_state IN ('feasible', 'running')
           OR (selected_accession_count IS NULL OR selected_accession_count = 0)),
    CHECK (node_limit_exhausted = 0 OR run_state = 'infeasible_or_unproven')
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_selection_run_events (
    event_id             TEXT PRIMARY KEY,
    selection_run_id     TEXT NOT NULL,
    snapshot_id          TEXT NOT NULL,
    from_state           TEXT NOT NULL CHECK (from_state IN (
        'planned', 'running', 'feasible', 'infeasible', 'infeasible_or_unproven', 'failed')),
    to_state             TEXT NOT NULL CHECK (to_state IN (
        'planned', 'running', 'feasible', 'infeasible', 'infeasible_or_unproven', 'failed')),
    attempt_number       INTEGER NOT NULL CHECK (attempt_number >= 1),
    expanded_node_count  INTEGER CHECK (expanded_node_count IS NULL OR expanded_node_count >= 0),
    reason_code          TEXT REFERENCES reference_reason_codes(reason_code),
    occurred_at_utc      TEXT NOT NULL,
    detail               TEXT NOT NULL DEFAULT '',
    -- One event may authorize exactly one retry attempt; a retry trigger
    -- matches on attempt_number, so a stale event can never be reused.
    UNIQUE (selection_run_id, attempt_number),
    FOREIGN KEY (selection_run_id, snapshot_id)
        REFERENCES pilot_selection_runs (selection_run_id, snapshot_id)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_selected_entities (
    selection_run_id      TEXT NOT NULL,
    snapshot_id           TEXT NOT NULL,
    cik_numeric           INTEGER NOT NULL,
    selected_order        INTEGER NOT NULL CHECK (selected_order >= 1),
    entity_hash_sha256    TEXT NOT NULL
        CHECK (length(entity_hash_sha256) = 64 AND entity_hash_sha256 NOT GLOB '*[^0-9a-f]*'),
    entity_role           TEXT NOT NULL CHECK (entity_role IN ('operating', 'control')),
    candidate_category    TEXT NOT NULL CHECK (candidate_category IN ('operating', 'control', 'ineligible')),
    size_stratum          TEXT,
    industry_family       TEXT,
    history_class         TEXT,
    control_kind          TEXT,
    recorded_at_utc       TEXT NOT NULL,
    PRIMARY KEY (selection_run_id, snapshot_id, cik_numeric),
    UNIQUE (selection_run_id, snapshot_id, selected_order),
    FOREIGN KEY (selection_run_id, snapshot_id)
        REFERENCES pilot_selection_runs (selection_run_id, snapshot_id),
    FOREIGN KEY (snapshot_id, cik_numeric)
        REFERENCES pilot_candidate_entities (snapshot_id, cik_numeric)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_selected_entity_quota_contributions (
    selection_run_id  TEXT NOT NULL,
    snapshot_id       TEXT NOT NULL,
    cik_numeric       INTEGER NOT NULL,
    quota_dimension   TEXT NOT NULL,
    quota_key         TEXT NOT NULL,
    recorded_at_utc   TEXT NOT NULL,
    PRIMARY KEY (selection_run_id, snapshot_id, cik_numeric, quota_dimension, quota_key),
    FOREIGN KEY (selection_run_id, snapshot_id, cik_numeric)
        REFERENCES pilot_selected_entities (selection_run_id, snapshot_id, cik_numeric)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_selected_accessions (
    selection_run_id       TEXT NOT NULL,
    snapshot_id            TEXT NOT NULL,
    accession_plain        TEXT NOT NULL,
    anchor_cik_numeric     INTEGER NOT NULL,
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

CREATE TABLE IF NOT EXISTS pilot_selected_accession_quota_contributions (
    selection_run_id  TEXT NOT NULL,
    snapshot_id       TEXT NOT NULL,
    accession_plain   TEXT NOT NULL,
    quota_dimension   TEXT NOT NULL,
    quota_key         TEXT NOT NULL,
    recorded_at_utc   TEXT NOT NULL,
    PRIMARY KEY (selection_run_id, snapshot_id, accession_plain, quota_dimension, quota_key),
    FOREIGN KEY (selection_run_id, snapshot_id, accession_plain)
        REFERENCES pilot_selected_accessions (selection_run_id, snapshot_id, accession_plain)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_reserves (
    reserve_package_id            TEXT PRIMARY KEY
        CHECK (length(reserve_package_id) = 64 AND reserve_package_id NOT GLOB '*[^0-9a-f]*'),
    selection_run_id               TEXT NOT NULL,
    snapshot_id                    TEXT NOT NULL,
    target_cik_numeric             INTEGER NOT NULL,
    replacement_cik_numeric        INTEGER NOT NULL,
    reserve_rank                   INTEGER NOT NULL CHECK (reserve_rank >= 1),
    replaces_signature_sha256      TEXT NOT NULL
        CHECK (length(replaces_signature_sha256) = 64 AND replaces_signature_sha256 NOT GLOB '*[^0-9a-f]*'),
    reserve_signature_sha256       TEXT NOT NULL
        CHECK (length(reserve_signature_sha256) = 64 AND reserve_signature_sha256 NOT GLOB '*[^0-9a-f]*'),
    signature_policy_version       TEXT NOT NULL,
    quota_policy_version            TEXT NOT NULL,
    reserve_tie_break_sha256       TEXT NOT NULL
        CHECK (length(reserve_tie_break_sha256) = 64 AND reserve_tie_break_sha256 NOT GLOB '*[^0-9a-f]*'),
    evidence_floor                  TEXT NOT NULL
        CHECK (evidence_floor IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
    recorded_at_utc                  TEXT NOT NULL,
    UNIQUE (selection_run_id, snapshot_id, target_cik_numeric, reserve_rank),
    -- FK target for the run/snapshot-scoped children below (section 6).
    UNIQUE (reserve_package_id, selection_run_id, snapshot_id),
    FOREIGN KEY (selection_run_id, snapshot_id)
        REFERENCES pilot_selection_runs (selection_run_id, snapshot_id),
    FOREIGN KEY (selection_run_id, snapshot_id, target_cik_numeric)
        REFERENCES pilot_selected_entities (selection_run_id, snapshot_id, cik_numeric),
    FOREIGN KEY (snapshot_id, replacement_cik_numeric)
        REFERENCES pilot_candidate_entities (snapshot_id, cik_numeric),
    -- Necessary, not sufficient: acceptance tests must independently recompute
    -- both signatures from normalized package content (Decision 016 section 7).
    CHECK (replaces_signature_sha256 = reserve_signature_sha256),
    CHECK (target_cik_numeric <> replacement_cik_numeric)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_reserve_accessions (
    reserve_package_id     TEXT NOT NULL,
    selection_run_id       TEXT NOT NULL,
    snapshot_id             TEXT NOT NULL,
    accession_plain         TEXT NOT NULL,
    accession_role          TEXT NOT NULL CHECK (accession_role IN ('base', 'stress', 'support', 'control')),
    accession_order         INTEGER NOT NULL CHECK (accession_order >= 1),
    accession_hash_sha256   TEXT NOT NULL
        CHECK (length(accession_hash_sha256) = 64 AND accession_hash_sha256 NOT GLOB '*[^0-9a-f]*'),
    recorded_at_utc         TEXT NOT NULL,
    PRIMARY KEY (reserve_package_id, accession_plain),
    UNIQUE (reserve_package_id, accession_order),
    FOREIGN KEY (reserve_package_id, selection_run_id, snapshot_id)
        REFERENCES pilot_reserves (reserve_package_id, selection_run_id, snapshot_id),
    -- Ties every reserve accession to a real candidate accession in the same
    -- snapshot the reserve package belongs to; a ghost accession cannot enter.
    FOREIGN KEY (snapshot_id, accession_plain)
        REFERENCES pilot_candidate_accessions (snapshot_id, accession_plain)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_reserve_quota_contributions (
    reserve_package_id  TEXT NOT NULL,
    selection_run_id    TEXT NOT NULL,
    snapshot_id          TEXT NOT NULL,
    quota_dimension      TEXT NOT NULL,
    quota_key             TEXT NOT NULL,
    recorded_at_utc       TEXT NOT NULL,
    PRIMARY KEY (reserve_package_id, quota_dimension, quota_key),
    FOREIGN KEY (reserve_package_id, selection_run_id, snapshot_id)
        REFERENCES pilot_reserves (reserve_package_id, selection_run_id, snapshot_id)
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_quota_results (
    quota_result_id         TEXT PRIMARY KEY,
    selection_run_id        TEXT NOT NULL,
    snapshot_id             TEXT NOT NULL,
    quota_dimension          TEXT NOT NULL,
    quota_key                TEXT NOT NULL,
    comparison_operator      TEXT NOT NULL CHECK (comparison_operator IN ('exact', 'at_least', 'at_most')),
    required_count            INTEGER NOT NULL CHECK (required_count >= 0),
    achieved_count            INTEGER NOT NULL CHECK (achieved_count >= 0),
    eligible_pool_count       INTEGER NOT NULL CHECK (eligible_pool_count >= 0),
    excluded_pool_count       INTEGER NOT NULL CHECK (excluded_pool_count >= 0),
    -- 'unproven' mirrors the amendment-purpose classification state (Decision
    -- 014 section 6); the pass-requires-provisional CHECK below (Decision 014
    -- section 1) keeps it, like every other non-provisional state, from ever
    -- satisfying an affirmative quota.
    evidence_state            TEXT NOT NULL
        CHECK (evidence_state IN
               ('provisional', 'review_required', 'conflicting', 'unavailable', 'unproven')),
    quota_result              TEXT NOT NULL CHECK (quota_result IN ('pass', 'fail', 'unproven')),
    binding_constraint         INTEGER NOT NULL DEFAULT 0 CHECK (binding_constraint IN (0, 1)),
    binding_evidence_sha256    TEXT
        CHECK (binding_evidence_sha256 IS NULL
               OR (length(binding_evidence_sha256) = 64
                   AND binding_evidence_sha256 NOT GLOB '*[^0-9a-f]*')),
    recorded_at_utc            TEXT NOT NULL,
    detail                     TEXT NOT NULL DEFAULT '',
    UNIQUE (selection_run_id, snapshot_id, quota_dimension, quota_key),
    -- FK target for pilot_quota_result_members below (section 6).
    UNIQUE (quota_result_id, selection_run_id, snapshot_id),
    FOREIGN KEY (selection_run_id, snapshot_id)
        REFERENCES pilot_selection_runs (selection_run_id, snapshot_id),
    CHECK (comparison_operator <> 'exact' OR quota_result <> 'pass' OR achieved_count = required_count),
    CHECK (comparison_operator <> 'at_least' OR quota_result <> 'pass' OR achieved_count >= required_count),
    CHECK (comparison_operator <> 'at_most' OR quota_result <> 'pass' OR achieved_count <= required_count),
    CHECK (quota_result <> 'fail' OR (
        (comparison_operator = 'exact' AND achieved_count <> required_count)
        OR (comparison_operator = 'at_least' AND achieved_count < required_count)
        OR (comparison_operator = 'at_most' AND achieved_count > required_count)
    )),
    -- Decision 014 section 1: only 'provisional' evidence may satisfy an
    -- affirmative quota; review_required/conflicting/unavailable/unproven cannot.
    CHECK (quota_result <> 'pass' OR evidence_state = 'provisional')
) STRICT;

CREATE TABLE IF NOT EXISTS pilot_quota_result_members (
    quota_result_id    TEXT NOT NULL,
    selection_run_id   TEXT NOT NULL,
    snapshot_id        TEXT NOT NULL,
    member_order       INTEGER NOT NULL CHECK (member_order >= 1),
    member_kind        TEXT NOT NULL CHECK (member_kind IN ('entity', 'accession')),
    cik_numeric        INTEGER,
    accession_plain    TEXT,
    recorded_at_utc     TEXT NOT NULL,
    PRIMARY KEY (quota_result_id, member_order),
    CHECK ((member_kind = 'entity') = (cik_numeric IS NOT NULL)),
    CHECK ((member_kind = 'accession') = (accession_plain IS NOT NULL)),
    FOREIGN KEY (quota_result_id, selection_run_id, snapshot_id)
        REFERENCES pilot_quota_results (quota_result_id, selection_run_id, snapshot_id),
    -- SQLite's default MATCH SIMPLE means a composite FK is not enforced when
    -- any of its columns is NULL, so exactly one of these two applies per row
    -- (member_kind's CHECK above guarantees cik_numeric/accession_plain are
    -- mutually exclusive) -- a ghost or cross-snapshot member fails to insert.
    FOREIGN KEY (selection_run_id, snapshot_id, cik_numeric)
        REFERENCES pilot_selected_entities (selection_run_id, snapshot_id, cik_numeric),
    FOREIGN KEY (selection_run_id, snapshot_id, accession_plain)
        REFERENCES pilot_selected_accessions (selection_run_id, snapshot_id, accession_plain)
) STRICT;

-- --------------------------------------------------------------------------
-- Manifest and projection
-- --------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pilot_manifest_versions (
    manifest_id                    TEXT PRIMARY KEY
        CHECK (length(manifest_id) = 64 AND manifest_id NOT GLOB '*[^0-9a-f]*'),
    selection_run_id                TEXT NOT NULL,
    snapshot_id                      TEXT NOT NULL,
    manifest_schema_version          TEXT NOT NULL,
    ordinal_version                  INTEGER NOT NULL CHECK (ordinal_version >= 1),
    supersedes_manifest_id           TEXT REFERENCES pilot_manifest_versions(manifest_id),
    source_observation_set_sha256    TEXT NOT NULL
        CHECK (length(source_observation_set_sha256) = 64
               AND source_observation_set_sha256 NOT GLOB '*[^0-9a-f]*'),
    candidate_tables_sha256          TEXT NOT NULL
        CHECK (length(candidate_tables_sha256) = 64 AND candidate_tables_sha256 NOT GLOB '*[^0-9a-f]*'),
    quota_definitions_sha256         TEXT NOT NULL
        CHECK (length(quota_definitions_sha256) = 64 AND quota_definitions_sha256 NOT GLOB '*[^0-9a-f]*'),
    selector_policy_sha256           TEXT NOT NULL
        CHECK (length(selector_policy_sha256) = 64 AND selector_policy_sha256 NOT GLOB '*[^0-9a-f]*'),
    selected_entities_sha256         TEXT NOT NULL
        CHECK (length(selected_entities_sha256) = 64 AND selected_entities_sha256 NOT GLOB '*[^0-9a-f]*'),
    selected_accessions_sha256       TEXT NOT NULL
        CHECK (length(selected_accessions_sha256) = 64 AND selected_accessions_sha256 NOT GLOB '*[^0-9a-f]*'),
    reserves_sha256                  TEXT NOT NULL
        CHECK (length(reserves_sha256) = 64 AND reserves_sha256 NOT GLOB '*[^0-9a-f]*'),
    quota_report_sha256              TEXT NOT NULL
        CHECK (length(quota_report_sha256) = 64 AND quota_report_sha256 NOT GLOB '*[^0-9a-f]*'),
    root_manifest_sha256             TEXT NOT NULL
        CHECK (length(root_manifest_sha256) = 64 AND root_manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
    manifest_state                    TEXT NOT NULL
        CHECK (manifest_state IN ('proposed', 'owner_approved', 'rejected', 'superseded')),
    approval_reference                 TEXT,
    approved_root_sha256                TEXT
        CHECK (approved_root_sha256 IS NULL
               OR (length(approved_root_sha256) = 64 AND approved_root_sha256 NOT GLOB '*[^0-9a-f]*')),
    relative_manifest_path               TEXT NOT NULL
        CHECK (relative_manifest_path <> ''
               AND relative_manifest_path NOT LIKE '/%'
               AND relative_manifest_path NOT GLOB '[A-Za-z]:*'
               AND relative_manifest_path NOT LIKE '\%'
               AND relative_manifest_path NOT LIKE './%'
               AND relative_manifest_path NOT LIKE '%//%'
               AND relative_manifest_path NOT LIKE '%..%'),
    generated_at_utc                     TEXT NOT NULL,
    approved_at_utc                      TEXT,
    rejected_at_utc                      TEXT,
    superseded_at_utc                    TEXT,
    detail                                TEXT NOT NULL DEFAULT '',
    UNIQUE (selection_run_id, snapshot_id, ordinal_version),
    FOREIGN KEY (selection_run_id, snapshot_id)
        REFERENCES pilot_selection_runs (selection_run_id, snapshot_id),
    CHECK (supersedes_manifest_id IS NULL OR supersedes_manifest_id <> manifest_id),
    CHECK (manifest_state <> 'proposed' OR approved_at_utc IS NULL),
    CHECK (manifest_state NOT IN ('owner_approved', 'superseded')
           OR (approved_at_utc IS NOT NULL AND approval_reference IS NOT NULL
               AND approved_root_sha256 IS NOT NULL)),
    CHECK (manifest_state NOT IN ('owner_approved', 'superseded')
           OR approved_root_sha256 = root_manifest_sha256),
    CHECK (manifest_state <> 'rejected' OR rejected_at_utc IS NOT NULL),
    CHECK (manifest_state <> 'superseded' OR superseded_at_utc IS NOT NULL)
) STRICT;

CREATE UNIQUE INDEX IF NOT EXISTS uq_pilot_manifest_single_active_approval
    ON pilot_manifest_versions (selection_run_id, snapshot_id)
    WHERE manifest_state = 'owner_approved';

CREATE TABLE IF NOT EXISTS pilot_projection_recovery_events (
    event_id                             TEXT PRIMARY KEY,
    manifest_id                          TEXT NOT NULL REFERENCES pilot_manifest_versions(manifest_id),
    expected_projection_identity         TEXT,
    observed_projection_identity         TEXT,
    expected_count                       INTEGER CHECK (expected_count IS NULL OR expected_count >= 0),
    observed_count                       INTEGER CHECK (observed_count IS NULL OR observed_count >= 0),
    resolution_state                     TEXT NOT NULL CHECK (resolution_state IN ('blocked', 'resolved')),
    release_blocking_before_resolution    INTEGER NOT NULL
        CHECK (release_blocking_before_resolution IN (0, 1)),
    release_blocking_after_resolution     INTEGER
        CHECK (release_blocking_after_resolution IS NULL OR release_blocking_after_resolution IN (0, 1)),
    occurred_at_utc                       TEXT NOT NULL,
    resolved_at_utc                       TEXT,
    detail                                 TEXT NOT NULL DEFAULT '',
    CHECK ((resolution_state = 'resolved') = (resolved_at_utc IS NOT NULL)),
    CHECK (resolution_state = 'blocked' OR release_blocking_after_resolution IS NOT NULL)
) STRICT;

-- --------------------------------------------------------------------------
-- Indexes
-- --------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_pilot_candidate_snapshots_state
    ON pilot_candidate_snapshots (snapshot_state, created_at_utc);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_entities_strata
    ON pilot_candidate_entities (snapshot_id, size_stratum, industry_family, history_class);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_entities_tie_break
    ON pilot_candidate_entities (snapshot_id, entity_tie_break_sha256);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_accessions_cohort
    ON pilot_candidate_accessions (snapshot_id, provisional_official_cohort);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_accessions_eligibility
    ON pilot_candidate_accessions (snapshot_id, base_eligible, stress_eligible, support_eligible, control_eligible);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_accessions_tie_break
    ON pilot_candidate_accessions (snapshot_id, accession_tie_break_sha256);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_accession_registrants_cik
    ON pilot_candidate_accession_registrants (registrant_cik_numeric);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_entity_evidence_parent
    ON pilot_candidate_entity_evidence (snapshot_id, cik_numeric, classification_dimension);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_accession_evidence_parent
    ON pilot_candidate_accession_evidence (snapshot_id, accession_plain, classification_dimension);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_entity_reasons_code
    ON pilot_candidate_entity_reasons (reason_code);
CREATE INDEX IF NOT EXISTS idx_pilot_candidate_accession_reasons_code
    ON pilot_candidate_accession_reasons (reason_code);
CREATE INDEX IF NOT EXISTS idx_pilot_selection_runs_state
    ON pilot_selection_runs (run_state, started_at_utc);
CREATE INDEX IF NOT EXISTS idx_pilot_selection_run_events_run
    ON pilot_selection_run_events (selection_run_id, occurred_at_utc);
CREATE INDEX IF NOT EXISTS idx_pilot_selected_accessions_anchor
    ON pilot_selected_accessions (selection_run_id, snapshot_id, anchor_cik_numeric);
CREATE INDEX IF NOT EXISTS idx_pilot_reserves_target
    ON pilot_reserves (selection_run_id, snapshot_id, target_cik_numeric, reserve_rank);
CREATE INDEX IF NOT EXISTS idx_pilot_reserves_signature
    ON pilot_reserves (replaces_signature_sha256);
CREATE INDEX IF NOT EXISTS idx_pilot_quota_results_result
    ON pilot_quota_results (quota_result);
CREATE INDEX IF NOT EXISTS idx_pilot_manifest_versions_state
    ON pilot_manifest_versions (manifest_state, generated_at_utc);
CREATE INDEX IF NOT EXISTS idx_pilot_projection_recovery_manifest
    ON pilot_projection_recovery_events (manifest_id, resolution_state);

-- --------------------------------------------------------------------------
-- Triggers: snapshot lifecycle (Decision 016 section 5, section 6)
-- --------------------------------------------------------------------------

-- A new row must begin building: freeze/invalidation are transitions, never
-- an initial state (blocks a direct INSERT that bypasses every freeze check).
CREATE TRIGGER pilot_snapshot_insert_must_be_building
BEFORE INSERT ON pilot_candidate_snapshots
WHEN NEW.snapshot_state <> 'building'
BEGIN
    SELECT RAISE(ABORT, 'a new pilot candidate snapshot must begin in building state');
END;

CREATE TRIGGER pilot_snapshot_transition_guard
BEFORE UPDATE OF snapshot_state ON pilot_candidate_snapshots
WHEN NOT (
    OLD.snapshot_state = NEW.snapshot_state
    OR (OLD.snapshot_state = 'building' AND NEW.snapshot_state IN ('frozen', 'invalidated'))
    OR (OLD.snapshot_state = 'frozen' AND NEW.snapshot_state = 'invalidated')
)
BEGIN
    SELECT RAISE(ABORT, 'illegal pilot snapshot state transition');
END;

-- Once frozen, every content, policy, coverage, hash, and provenance field is
-- immutable -- including on the frozen->invalidated transition itself, so
-- frozen_at_utc and the frozen hashes can never be cleared or overwritten
-- (Decision 016 section 5: "never cleared or overwritten on that transition").
CREATE TRIGGER pilot_snapshot_frozen_fields_immutable
BEFORE UPDATE ON pilot_candidate_snapshots
WHEN OLD.snapshot_state = 'frozen'
BEGIN
    SELECT RAISE(ABORT, 'pilot snapshot frozen fields are immutable')
    WHERE NEW.census_run_id IS NOT OLD.census_run_id
       OR NEW.coverage_start IS NOT OLD.coverage_start
       OR NEW.coverage_end IS NOT OLD.coverage_end
       OR NEW.as_of_date IS NOT OLD.as_of_date
       OR NEW.include_open_quarter IS NOT OLD.include_open_quarter
       OR NEW.coverage_policy_version IS NOT OLD.coverage_policy_version
       OR NEW.candidate_policy_version IS NOT OLD.candidate_policy_version
       OR NEW.sic_family_mapping_version IS NOT OLD.sic_family_mapping_version
       OR NEW.evidence_policy_version IS NOT OLD.evidence_policy_version
       OR NEW.coverage_window_sha256 IS NOT OLD.coverage_window_sha256
       OR NEW.input_observation_set_sha256 IS NOT OLD.input_observation_set_sha256
       OR NEW.candidate_entity_table_sha256 IS NOT OLD.candidate_entity_table_sha256
       OR NEW.candidate_accession_table_sha256 IS NOT OLD.candidate_accession_table_sha256
       OR NEW.candidate_registrant_table_sha256 IS NOT OLD.candidate_registrant_table_sha256
       OR NEW.candidate_entity_evidence_sha256 IS NOT OLD.candidate_entity_evidence_sha256
       OR NEW.candidate_accession_evidence_sha256 IS NOT OLD.candidate_accession_evidence_sha256
       OR NEW.candidate_entity_reasons_sha256 IS NOT OLD.candidate_entity_reasons_sha256
       OR NEW.candidate_accession_reasons_sha256 IS NOT OLD.candidate_accession_reasons_sha256
       OR NEW.candidate_snapshot_sha256 IS NOT OLD.candidate_snapshot_sha256
       OR NEW.entity_count IS NOT OLD.entity_count
       OR NEW.accession_count IS NOT OLD.accession_count
       OR NEW.frozen_at_utc IS NOT OLD.frozen_at_utc;
END;

CREATE TRIGGER pilot_snapshot_no_delete
BEFORE DELETE ON pilot_candidate_snapshots
WHEN OLD.snapshot_state IN ('frozen', 'invalidated')
BEGIN
    SELECT RAISE(ABORT, 'frozen or invalidated pilot snapshots are undeletable');
END;

-- Freezing requires the declared counts and anchor/multi-registrant
-- consistency to hold over the actual candidate rows (Decision 016 section 6).
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
    SELECT RAISE(ABORT, 'pilot snapshot freeze requires exactly one anchor per accession')
    WHERE EXISTS (
        SELECT accession_plain FROM pilot_candidate_accession_registrants
        WHERE snapshot_id = NEW.snapshot_id
        GROUP BY accession_plain
        HAVING SUM(is_anchor) <> 1
    ) OR EXISTS (
        SELECT a.accession_plain FROM pilot_candidate_accessions AS a
        WHERE a.snapshot_id = NEW.snapshot_id
          AND NOT EXISTS (
              SELECT 1 FROM pilot_candidate_accession_registrants AS r
              WHERE r.snapshot_id = a.snapshot_id AND r.accession_plain = a.accession_plain
          )
    );
    SELECT RAISE(ABORT, 'pilot snapshot freeze multi_registrant flag inconsistent with registrant rows')
    WHERE EXISTS (
        SELECT a.accession_plain FROM pilot_candidate_accessions AS a
        WHERE a.snapshot_id = NEW.snapshot_id
          AND (
            (a.multi_registrant = 1 AND (
                SELECT COUNT(*) FROM pilot_candidate_accession_registrants AS r
                WHERE r.snapshot_id = a.snapshot_id AND r.accession_plain = a.accession_plain
            ) < 2)
            OR (a.multi_registrant = 0 AND (
                SELECT COUNT(*) FROM pilot_candidate_accession_registrants AS r
                WHERE r.snapshot_id = a.snapshot_id AND r.accession_plain = a.accession_plain
            ) > 1
            AND NOT EXISTS (
                SELECT 1 FROM pilot_candidate_accession_reasons AS ar
                WHERE ar.snapshot_id = a.snapshot_id AND ar.accession_plain = a.accession_plain
                  AND ar.reason_scope = 'multi_registrant'
            ))
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
-- Triggers: candidate child rows are writable only while building
-- (Decision 016 section 6; rule 3 of the migration-runner requirements)
-- --------------------------------------------------------------------------

CREATE TRIGGER pilot_candidate_entities_insert_guard
BEFORE INSERT ON pilot_candidate_entities
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = NEW.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate entity insert requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_entities_update_guard
BEFORE UPDATE ON pilot_candidate_entities
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate entity update requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_entities_delete_guard
BEFORE DELETE ON pilot_candidate_entities
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate entity delete requires a building snapshot'); END;

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

CREATE TRIGGER pilot_candidate_entity_evidence_insert_guard
BEFORE INSERT ON pilot_candidate_entity_evidence
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = NEW.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate entity evidence insert requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_entity_evidence_update_guard
BEFORE UPDATE ON pilot_candidate_entity_evidence
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate entity evidence update requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_entity_evidence_delete_guard
BEFORE DELETE ON pilot_candidate_entity_evidence
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate entity evidence delete requires a building snapshot'); END;

CREATE TRIGGER pilot_candidate_accession_evidence_insert_guard
BEFORE INSERT ON pilot_candidate_accession_evidence
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = NEW.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession evidence insert requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accession_evidence_update_guard
BEFORE UPDATE ON pilot_candidate_accession_evidence
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession evidence update requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accession_evidence_delete_guard
BEFORE DELETE ON pilot_candidate_accession_evidence
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession evidence delete requires a building snapshot'); END;

CREATE TRIGGER pilot_candidate_entity_reasons_insert_guard
BEFORE INSERT ON pilot_candidate_entity_reasons
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = NEW.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate entity reason insert requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_entity_reasons_update_guard
BEFORE UPDATE ON pilot_candidate_entity_reasons
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate entity reason update requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_entity_reasons_delete_guard
BEFORE DELETE ON pilot_candidate_entity_reasons
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate entity reason delete requires a building snapshot'); END;

CREATE TRIGGER pilot_candidate_accession_reasons_insert_guard
BEFORE INSERT ON pilot_candidate_accession_reasons
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = NEW.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession reason insert requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accession_reasons_update_guard
BEFORE UPDATE ON pilot_candidate_accession_reasons
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession reason update requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accession_reasons_delete_guard
BEFORE DELETE ON pilot_candidate_accession_reasons
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession reason delete requires a building snapshot'); END;

-- --------------------------------------------------------------------------
-- Triggers: selection-run lifecycle (Decision 016 section 5, section 6)
-- --------------------------------------------------------------------------

CREATE TRIGGER pilot_selection_run_transition_guard
BEFORE UPDATE OF run_state ON pilot_selection_runs
WHEN NOT (
    OLD.run_state = NEW.run_state
    OR (OLD.run_state = 'planned' AND NEW.run_state = 'running')
    OR (OLD.run_state = 'running'
        AND NEW.run_state IN ('feasible', 'infeasible', 'infeasible_or_unproven', 'failed'))
    OR (OLD.run_state = 'failed' AND NEW.run_state = 'running')
)
BEGIN
    SELECT RAISE(ABORT, 'illegal pilot selection run state transition');
END;

CREATE TRIGGER pilot_selection_run_requires_frozen_snapshot
BEFORE UPDATE OF run_state ON pilot_selection_runs
WHEN NEW.run_state = 'running' AND OLD.run_state IN ('planned', 'failed')
BEGIN
    SELECT RAISE(ABORT, 'pilot selection run cannot enter running without a frozen snapshot')
    WHERE (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = NEW.snapshot_id) <> 'frozen';
END;

-- Attempt tracking (Decision 016 section 5 retry rule): current_attempt may
-- change only on planned->running (must become 1) or failed->running (must
-- increment by exactly one and be backed by a matching, previously unused
-- retry event) -- never silently on any other transition or column update.
CREATE TRIGGER pilot_selection_run_initial_attempt
BEFORE UPDATE OF run_state ON pilot_selection_runs
WHEN NEW.run_state = 'running' AND OLD.run_state = 'planned'
BEGIN
    SELECT RAISE(ABORT, 'pilot selection run must establish attempt 1 on its initial running transition')
    WHERE NEW.current_attempt <> 1;
END;

CREATE TRIGGER pilot_selection_run_retry_requires_event
BEFORE UPDATE OF run_state ON pilot_selection_runs
WHEN OLD.run_state = 'failed' AND NEW.run_state = 'running'
BEGIN
    SELECT RAISE(ABORT, 'pilot selection retry must increment current_attempt by exactly one')
    WHERE NEW.current_attempt <> OLD.current_attempt + 1;
    SELECT RAISE(ABORT,
        'pilot selection retry requires a recorded, previously unused retry event for the new attempt')
    WHERE NOT EXISTS (
        SELECT 1 FROM pilot_selection_run_events
        WHERE selection_run_id = NEW.selection_run_id AND snapshot_id = NEW.snapshot_id
          AND from_state = 'failed' AND to_state = 'running'
          AND attempt_number = NEW.current_attempt
    );
END;

-- A stale retry event's attempt_number can never match a later NEW.current_attempt
-- (which strictly increases), and UNIQUE (selection_run_id, attempt_number) on
-- pilot_selection_run_events prevents inserting two events for the same attempt,
-- so one recorded event can never authorize more than the one retry it names.
CREATE TRIGGER pilot_selection_run_attempt_guard
BEFORE UPDATE OF run_state, current_attempt ON pilot_selection_runs
WHEN NEW.current_attempt <> OLD.current_attempt
     AND NOT (
         (OLD.run_state = 'planned' AND NEW.run_state = 'running')
         OR (OLD.run_state = 'failed' AND NEW.run_state = 'running')
     )
BEGIN
    SELECT RAISE(ABORT,
        'pilot selection run current_attempt may change only on planned->running or failed->running');
END;

-- Non-feasible terminal transitions must leave the run with zero durable
-- result rows, so a failed run is genuinely clean and retryable and so
-- 'infeasible'/'infeasible_or_unproven' never carry a partial manifest
-- (Decision 013 section 6). Checked against actual rows in every result
-- family, never a declared count column.
CREATE TRIGGER pilot_selection_run_requires_clean_non_feasible_result
BEFORE UPDATE OF run_state ON pilot_selection_runs
WHEN OLD.run_state = 'running' AND NEW.run_state IN ('failed', 'infeasible', 'infeasible_or_unproven')
BEGIN
    SELECT RAISE(ABORT,
        'pilot selection run must have zero durable result rows before a non-feasible terminal transition')
    WHERE EXISTS (SELECT 1 FROM pilot_selected_entities WHERE selection_run_id = NEW.selection_run_id)
       OR EXISTS (
           SELECT 1 FROM pilot_selected_entity_quota_contributions WHERE selection_run_id = NEW.selection_run_id)
       OR EXISTS (SELECT 1 FROM pilot_selected_accessions WHERE selection_run_id = NEW.selection_run_id)
       OR EXISTS (
           SELECT 1 FROM pilot_selected_accession_quota_contributions
           WHERE selection_run_id = NEW.selection_run_id)
       OR EXISTS (SELECT 1 FROM pilot_reserves WHERE selection_run_id = NEW.selection_run_id)
       OR EXISTS (SELECT 1 FROM pilot_reserve_accessions WHERE selection_run_id = NEW.selection_run_id)
       OR EXISTS (SELECT 1 FROM pilot_reserve_quota_contributions WHERE selection_run_id = NEW.selection_run_id)
       OR EXISTS (SELECT 1 FROM pilot_quota_results WHERE selection_run_id = NEW.selection_run_id)
       OR EXISTS (SELECT 1 FROM pilot_quota_result_members WHERE selection_run_id = NEW.selection_run_id);
END;

-- Feasible finalization must hold against actual rows, not only the declared
-- count columns (the literal-24 CHECK on selected_entity_count stays; this
-- closes the gap where a declared count could diverge from what was truly
-- written, and requires materialized selected_order to be contiguous).
CREATE TRIGGER pilot_selection_run_feasible_requires_actual_results
BEFORE UPDATE OF run_state ON pilot_selection_runs
WHEN NEW.run_state = 'feasible' AND OLD.run_state = 'running'
BEGIN
    SELECT RAISE(ABORT, 'pilot selection feasible transition requires exactly 24 actual selected entities')
    WHERE (SELECT COUNT(*) FROM pilot_selected_entities WHERE selection_run_id = NEW.selection_run_id) <> 24;
    -- A NULL declared count must fail this gate outright, and a NULL on either
    -- side of ``<>`` otherwise evaluates to NULL (never TRUE) in SQLite, which
    -- would silently let the RAISE below skip firing; both branches are named
    -- explicitly so a NULL declared count can never pass by comparison silence.
    SELECT RAISE(ABORT, 'pilot selection feasible transition requires selected_entity_count to equal actual rows')
    WHERE NEW.selected_entity_count IS NULL
       OR NEW.selected_entity_count
          <> (SELECT COUNT(*) FROM pilot_selected_entities WHERE selection_run_id = NEW.selection_run_id);
    SELECT RAISE(ABORT,
        'pilot selection feasible transition requires selected_accession_count to equal actual rows')
    WHERE NEW.selected_accession_count IS NULL
       OR NEW.selected_accession_count
          <> (SELECT COUNT(*) FROM pilot_selected_accessions WHERE selection_run_id = NEW.selection_run_id);
    SELECT RAISE(ABORT, 'pilot selection feasible transition requires contiguous entity selected_order')
    WHERE (SELECT MIN(selected_order) FROM pilot_selected_entities WHERE selection_run_id = NEW.selection_run_id)
          <> 1
       OR (SELECT MAX(selected_order) FROM pilot_selected_entities WHERE selection_run_id = NEW.selection_run_id)
          <> (SELECT COUNT(*) FROM pilot_selected_entities WHERE selection_run_id = NEW.selection_run_id);
    SELECT RAISE(ABORT, 'pilot selection feasible transition requires contiguous accession selected_order')
    WHERE (SELECT COUNT(*) FROM pilot_selected_accessions WHERE selection_run_id = NEW.selection_run_id) > 0
      AND (
        (SELECT MIN(selected_order) FROM pilot_selected_accessions WHERE selection_run_id = NEW.selection_run_id)
        <> 1
        OR (SELECT MAX(selected_order) FROM pilot_selected_accessions WHERE selection_run_id = NEW.selection_run_id)
           <> (SELECT COUNT(*) FROM pilot_selected_accessions WHERE selection_run_id = NEW.selection_run_id)
      );
    -- Decision 013 section 6: a reserve's quota-contribution set must be the
    -- exact set the target selected entity was chosen to satisfy -- not a
    -- subset, not a superset. Symmetric-difference check per reserve package.
    SELECT RAISE(ABORT,
        'pilot selection feasible transition requires each reserve quota-contribution set '
        || 'to match its target entity signature')
    WHERE EXISTS (
        SELECT r.reserve_package_id FROM pilot_reserves AS r
        WHERE r.selection_run_id = NEW.selection_run_id AND r.snapshot_id = NEW.snapshot_id
          AND (
            EXISTS (
                SELECT 1 FROM pilot_reserve_quota_contributions AS rqc
                WHERE rqc.reserve_package_id = r.reserve_package_id
                  AND NOT EXISTS (
                      SELECT 1 FROM pilot_selected_entity_quota_contributions AS seqc
                      WHERE seqc.selection_run_id = r.selection_run_id
                        AND seqc.snapshot_id = r.snapshot_id
                        AND seqc.cik_numeric = r.target_cik_numeric
                        AND seqc.quota_dimension = rqc.quota_dimension
                        AND seqc.quota_key = rqc.quota_key
                  )
            )
            OR EXISTS (
                SELECT 1 FROM pilot_selected_entity_quota_contributions AS seqc
                WHERE seqc.selection_run_id = r.selection_run_id
                  AND seqc.snapshot_id = r.snapshot_id
                  AND seqc.cik_numeric = r.target_cik_numeric
                  AND NOT EXISTS (
                      SELECT 1 FROM pilot_reserve_quota_contributions AS rqc
                      WHERE rqc.reserve_package_id = r.reserve_package_id
                        AND rqc.quota_dimension = seqc.quota_dimension
                        AND rqc.quota_key = seqc.quota_key
                  )
            )
          )
    );
END;

CREATE TRIGGER pilot_selection_run_events_immutable_update
BEFORE UPDATE ON pilot_selection_run_events
BEGIN SELECT RAISE(ABORT, 'pilot selection run events are append-only'); END;
CREATE TRIGGER pilot_selection_run_events_immutable_delete
BEFORE DELETE ON pilot_selection_run_events
BEGIN SELECT RAISE(ABORT, 'pilot selection run events are append-only'); END;

-- --------------------------------------------------------------------------
-- Triggers: selected/reserve/quota rows may be inserted, updated, or deleted
-- only while their selection run is 'running'; once the run leaves 'running'
-- for any terminal state, they are immutable and undeletable (Decision 016
-- section 6). The run-level trigger above additionally requires zero such
-- rows before a non-feasible terminal transition, so that state is durable.
-- --------------------------------------------------------------------------

CREATE TRIGGER pilot_selected_entities_insert_guard
BEFORE INSERT ON pilot_selected_entities
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = NEW.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot selected entity write requires a running selection run'); END;
CREATE TRIGGER pilot_selected_entities_update_guard
BEFORE UPDATE ON pilot_selected_entities
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot selected entity write requires a running selection run'); END;
CREATE TRIGGER pilot_selected_entities_delete_guard
BEFORE DELETE ON pilot_selected_entities
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot selected entity write requires a running selection run'); END;

CREATE TRIGGER pilot_selected_entity_quota_contributions_insert_guard
BEFORE INSERT ON pilot_selected_entity_quota_contributions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = NEW.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot selected entity quota contribution write requires a running selection run'); END;
CREATE TRIGGER pilot_selected_entity_quota_contributions_update_guard
BEFORE UPDATE ON pilot_selected_entity_quota_contributions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot selected entity quota contribution write requires a running selection run'); END;
CREATE TRIGGER pilot_selected_entity_quota_contributions_delete_guard
BEFORE DELETE ON pilot_selected_entity_quota_contributions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot selected entity quota contribution write requires a running selection run'); END;

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

CREATE TRIGGER pilot_selected_accession_quota_contributions_insert_guard
BEFORE INSERT ON pilot_selected_accession_quota_contributions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = NEW.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT,
    'pilot selected accession quota contribution write requires a running selection run'); END;
CREATE TRIGGER pilot_selected_accession_quota_contributions_update_guard
BEFORE UPDATE ON pilot_selected_accession_quota_contributions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT,
    'pilot selected accession quota contribution write requires a running selection run'); END;
CREATE TRIGGER pilot_selected_accession_quota_contributions_delete_guard
BEFORE DELETE ON pilot_selected_accession_quota_contributions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT,
    'pilot selected accession quota contribution write requires a running selection run'); END;

CREATE TRIGGER pilot_reserves_insert_guard
BEFORE INSERT ON pilot_reserves
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = NEW.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot reserve write requires a running selection run'); END;
CREATE TRIGGER pilot_reserves_update_guard
BEFORE UPDATE ON pilot_reserves
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot reserve write requires a running selection run'); END;
CREATE TRIGGER pilot_reserves_delete_guard
BEFORE DELETE ON pilot_reserves
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot reserve write requires a running selection run'); END;

CREATE TRIGGER pilot_reserve_accessions_insert_guard
BEFORE INSERT ON pilot_reserve_accessions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = NEW.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot reserve accession write requires a running selection run'); END;
CREATE TRIGGER pilot_reserve_accessions_update_guard
BEFORE UPDATE ON pilot_reserve_accessions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot reserve accession write requires a running selection run'); END;
CREATE TRIGGER pilot_reserve_accessions_delete_guard
BEFORE DELETE ON pilot_reserve_accessions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot reserve accession write requires a running selection run'); END;

CREATE TRIGGER pilot_reserve_quota_contributions_insert_guard
BEFORE INSERT ON pilot_reserve_quota_contributions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = NEW.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot reserve quota contribution write requires a running selection run'); END;
CREATE TRIGGER pilot_reserve_quota_contributions_update_guard
BEFORE UPDATE ON pilot_reserve_quota_contributions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot reserve quota contribution write requires a running selection run'); END;
CREATE TRIGGER pilot_reserve_quota_contributions_delete_guard
BEFORE DELETE ON pilot_reserve_quota_contributions
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot reserve quota contribution write requires a running selection run'); END;

CREATE TRIGGER pilot_quota_results_insert_guard
BEFORE INSERT ON pilot_quota_results
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = NEW.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot quota result write requires a running selection run'); END;
CREATE TRIGGER pilot_quota_results_update_guard
BEFORE UPDATE ON pilot_quota_results
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot quota result write requires a running selection run'); END;
CREATE TRIGGER pilot_quota_results_delete_guard
BEFORE DELETE ON pilot_quota_results
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot quota result write requires a running selection run'); END;

CREATE TRIGGER pilot_quota_result_members_insert_guard
BEFORE INSERT ON pilot_quota_result_members
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = NEW.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot quota result member write requires a running selection run'); END;
CREATE TRIGGER pilot_quota_result_members_update_guard
BEFORE UPDATE ON pilot_quota_result_members
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot quota result member write requires a running selection run'); END;
CREATE TRIGGER pilot_quota_result_members_delete_guard
BEFORE DELETE ON pilot_quota_result_members
WHEN (SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = OLD.selection_run_id) <> 'running'
BEGIN SELECT RAISE(ABORT, 'pilot quota result member write requires a running selection run'); END;

-- --------------------------------------------------------------------------
-- Triggers: manifest lifecycle (Decision 016 section 5, section 6, section 8)
-- --------------------------------------------------------------------------

CREATE TRIGGER pilot_manifest_transition_guard
BEFORE UPDATE OF manifest_state ON pilot_manifest_versions
WHEN NOT (
    OLD.manifest_state = NEW.manifest_state
    OR (OLD.manifest_state = 'proposed' AND NEW.manifest_state IN ('owner_approved', 'rejected'))
    OR (OLD.manifest_state = 'owner_approved' AND NEW.manifest_state = 'superseded')
)
BEGIN
    SELECT RAISE(ABORT, 'illegal pilot manifest state transition');
END;

-- A proposed successor may exist -- and may itself already be approved -- before
-- the old approved manifest is superseded; this only requires that, at the
-- moment of supersession, some *other* manifest already references this one
-- via supersedes_manifest_id (self-supersession is separately rejected by a
-- table CHECK).
CREATE TRIGGER pilot_manifest_supersession_requires_successor
BEFORE UPDATE OF manifest_state ON pilot_manifest_versions
WHEN NEW.manifest_state = 'superseded' AND OLD.manifest_state = 'owner_approved'
BEGIN
    SELECT RAISE(ABORT,
        'pilot manifest supersession requires a distinct successor referencing it via supersedes_manifest_id')
    WHERE NOT EXISTS (
        SELECT 1 FROM pilot_manifest_versions
        WHERE supersedes_manifest_id = NEW.manifest_id AND manifest_id <> NEW.manifest_id
    );
END;

CREATE TRIGGER pilot_manifest_hashes_immutable
BEFORE UPDATE OF source_observation_set_sha256, candidate_tables_sha256, quota_definitions_sha256,
                 selector_policy_sha256, selected_entities_sha256, selected_accessions_sha256,
                 reserves_sha256, quota_report_sha256, root_manifest_sha256
ON pilot_manifest_versions
BEGIN
    SELECT RAISE(ABORT, 'pilot manifest component and root hashes are immutable');
END;

CREATE TRIGGER pilot_manifest_versions_no_delete
BEFORE DELETE ON pilot_manifest_versions
BEGIN SELECT RAISE(ABORT, 'pilot manifest rows are undeletable'); END;

-- --------------------------------------------------------------------------
-- Triggers: projection-recovery events are append-only (Decision 016 section
-- 3, section 6), mirroring pilot_selection_run_events. The blocked/resolved
-- lifecycle is represented as a sequence of distinct appended events, not
-- in-place mutation of one row.
-- --------------------------------------------------------------------------

CREATE TRIGGER pilot_projection_recovery_events_immutable_update
BEFORE UPDATE ON pilot_projection_recovery_events
BEGIN SELECT RAISE(ABORT, 'pilot projection recovery events are append-only'); END;
CREATE TRIGGER pilot_projection_recovery_events_immutable_delete
BEFORE DELETE ON pilot_projection_recovery_events
BEGIN SELECT RAISE(ABORT, 'pilot projection recovery events are append-only'); END;

-- --------------------------------------------------------------------------
-- Policy-version provenance (Decision 016 section 1; matches pilot_policy.py)
-- --------------------------------------------------------------------------

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('pilot_candidate', 'pilot-candidate/1.0',
     'Docs/Decisions/decision_013_pilot_selection_mechanics.md', '2026-07-27T00:00:00Z'),
    ('pilot_evidence', 'pilot-evidence/1.0',
     'Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md', '2026-07-27T00:00:00Z'),
    ('pilot_sic_family_mapping', 'sic-family-mapping/0.2',
     'Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md', '2026-07-27T00:00:00Z'),
    ('pilot_selector', 'deterministic-constrained/1.0',
     'Docs/Decisions/decision_013_pilot_selection_mechanics.md', '2026-07-27T00:00:00Z'),
    ('pilot_replacement_signature', 'quota-contribution/1.0',
     'Docs/Decisions/decision_013_pilot_selection_mechanics.md', '2026-07-27T00:00:00Z'),
    ('pilot_manifest_hash', 'pilot-manifest/1.0',
     'Docs/Decisions/decision_013_pilot_selection_mechanics.md', '2026-07-27T00:00:00Z'),
    ('pilot_primary_universe_boundary', 'sic-6000-6999/1.0',
     'Docs/Decisions/decision_002_primary_outcome.md', '2026-07-27T00:00:00Z');
