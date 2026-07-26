-- Disclosure Drift operational catalog, migration 0001.
-- Governing records: Decisions 007, 008, 009, 010.
-- Every table is STRICT. Timestamps are ISO-8601 TEXT; booleans are INTEGER 0/1.
-- Paths are stored relative to a configured root; absolute paths are rejected upstream.

-- --------------------------------------------------------------------------
-- Reference
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reference_policy_versions (
    policy_key        TEXT PRIMARY KEY,
    policy_version    TEXT NOT NULL,
    decision_record   TEXT NOT NULL,
    recorded_at_utc   TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS reference_form_types (
    form_type         TEXT PRIMARY KEY,
    is_amendment      INTEGER NOT NULL CHECK (is_amendment IN (0, 1)),
    is_eligible_universe INTEGER NOT NULL CHECK (is_eligible_universe IN (0, 1)),
    description       TEXT NOT NULL,
    decision_record   TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS reference_reason_codes (
    reason_code       TEXT PRIMARY KEY,
    category          TEXT NOT NULL,
    description       TEXT NOT NULL,
    blocks_release    INTEGER NOT NULL CHECK (blocks_release IN (0, 1)),
    requires_manual_review INTEGER NOT NULL CHECK (requires_manual_review IN (0, 1)),
    decision_record   TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS reference_cohort_definitions (
    cohort_name       TEXT PRIMARY KEY,
    window_start      TEXT NOT NULL,
    window_end        TEXT NOT NULL,
    role              TEXT NOT NULL,
    assignment_date_source TEXT NOT NULL,
    decision_record   TEXT NOT NULL
) STRICT;

-- Created empty in Stage M2.1. Populated in Stage M2.2 from an approved SEC
-- snapshot with provenance; never seeded from remembered values.
CREATE TABLE IF NOT EXISTS reference_sic_codes (
    sic_code          TEXT PRIMARY KEY,
    description       TEXT NOT NULL,
    office            TEXT,
    source_snapshot_id TEXT NOT NULL,
    source_url        TEXT NOT NULL,
    retrieved_at_utc  TEXT NOT NULL
) STRICT;

-- --------------------------------------------------------------------------
-- Operational
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ops_schema_migrations (
    version           INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    checksum_sha256   TEXT NOT NULL,
    applied_at_utc    TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS ops_writer_leases (
    lease_id          TEXT PRIMARY KEY,
    writer_pid        INTEGER NOT NULL,
    host_fingerprint  TEXT NOT NULL,
    acquired_at_utc   TEXT NOT NULL,
    expires_at_utc    TEXT NOT NULL,
    released_at_utc   TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS ops_ingestion_jobs (
    job_id            TEXT PRIMARY KEY,
    job_kind          TEXT NOT NULL,
    job_state         TEXT NOT NULL CHECK (
        job_state IN ('pending', 'running', 'stopped', 'completed', 'failed', 'cooldown')
    ),
    stage             TEXT NOT NULL,
    started_at_utc    TEXT NOT NULL,
    finished_at_utc   TEXT,
    detail            TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS ops_job_events (
    event_id          TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL REFERENCES ops_ingestion_jobs(job_id),
    event_kind        TEXT NOT NULL,
    occurred_at_utc   TEXT NOT NULL,
    event_payload_json TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS ops_retrieval_attempts (
    retrieval_attempt_id TEXT PRIMARY KEY,
    job_id            TEXT REFERENCES ops_ingestion_jobs(job_id),
    source_url_canonical TEXT NOT NULL,
    logical_role      TEXT NOT NULL,
    attempt_number    INTEGER NOT NULL CHECK (attempt_number >= 1),
    attempt_state     TEXT NOT NULL CHECK (
        attempt_state IN ('started', 'succeeded', 'failed', 'quarantined', 'abandoned')
    ),
    started_at_utc    TEXT NOT NULL,
    finished_at_utc   TEXT,
    action_taken      TEXT,
    reason_code       TEXT REFERENCES reference_reason_codes(reason_code)
) STRICT;

CREATE TABLE IF NOT EXISTS ops_checkpoints (
    checkpoint_key    TEXT PRIMARY KEY,
    checkpoint_value  TEXT NOT NULL,
    updated_at_utc    TEXT NOT NULL
) STRICT;

-- --------------------------------------------------------------------------
-- Raw catalog
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_source_snapshots (
    snapshot_id       TEXT PRIMARY KEY,
    source_class      TEXT NOT NULL,
    source_url_canonical TEXT NOT NULL,
    retrieved_at_utc  TEXT NOT NULL,
    content_sha256    TEXT NOT NULL,
    notes             TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS raw_objects (
    raw_object_id     TEXT PRIMARY KEY,
    logical_role      TEXT NOT NULL,
    source_url_canonical TEXT NOT NULL,
    accession_plain   TEXT,
    cik_padded        TEXT,
    first_seen_at_utc TEXT NOT NULL,
    latest_observation_id TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS raw_object_observations (
    observation_id    TEXT PRIMARY KEY,
    raw_object_id     TEXT NOT NULL REFERENCES raw_objects(raw_object_id),
    retrieval_attempt_id TEXT NOT NULL REFERENCES ops_retrieval_attempts(retrieval_attempt_id),
    relative_storage_path TEXT NOT NULL,
    media_type        TEXT,
    content_encoding_received TEXT,
    content_sha256    TEXT NOT NULL,
    stored_sha256     TEXT NOT NULL,
    content_size_bytes INTEGER NOT NULL CHECK (content_size_bytes >= 0),
    stored_size_bytes INTEGER NOT NULL CHECK (stored_size_bytes >= 0),
    compression       TEXT NOT NULL CHECK (compression IN ('none', 'gzip')),
    retrieved_at_utc  TEXT NOT NULL,
    supersedes_observation_id TEXT REFERENCES raw_object_observations(observation_id),
    reason_code       TEXT REFERENCES reference_reason_codes(reason_code),
    UNIQUE (raw_object_id, content_sha256, retrieved_at_utc)
) STRICT;

CREATE TABLE IF NOT EXISTS raw_http_responses (
    response_id       TEXT PRIMARY KEY,
    retrieval_attempt_id TEXT NOT NULL REFERENCES ops_retrieval_attempts(retrieval_attempt_id),
    http_status       INTEGER,
    retry_after_seconds REAL,
    action_taken      TEXT NOT NULL,
    halts_aggregate_traffic INTEGER NOT NULL CHECK (halts_aggregate_traffic IN (0, 1)),
    observed_at_utc   TEXT NOT NULL,
    detail            TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS raw_quarantine_objects (
    quarantine_id     TEXT PRIMARY KEY,
    raw_object_id     TEXT REFERENCES raw_objects(raw_object_id),
    retrieval_attempt_id TEXT REFERENCES ops_retrieval_attempts(retrieval_attempt_id),
    relative_storage_path TEXT NOT NULL,
    quarantine_reason_code TEXT NOT NULL REFERENCES reference_reason_codes(reason_code),
    quarantined_at_utc TEXT NOT NULL,
    detail            TEXT NOT NULL
) STRICT;

-- --------------------------------------------------------------------------
-- Inventory
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_accessions (
    accession_plain   TEXT PRIMARY KEY,
    accession_number_dashed TEXT NOT NULL UNIQUE,
    submitter_cik_numeric INTEGER NOT NULL,
    form_type         TEXT NOT NULL REFERENCES reference_form_types(form_type),
    filing_date_sec   TEXT,
    date_as_of_change TEXT,
    acceptance_datetime_sec_raw TEXT,
    acceptance_date_sec TEXT,
    acceptance_datetime_et TEXT,
    acceptance_datetime_utc TEXT,
    resolved_value_source TEXT,
    correction_status TEXT NOT NULL DEFAULT 'none',
    public_availability_date_proxy TEXT,
    availability_precision TEXT CHECK (availability_precision IN ('timestamp', 'date')),
    availability_basis TEXT CHECK (
        availability_basis IN
        ('same_day_acceptance', 'later_official_filing_date', 'filing_date_only')
    ),
    official_filing_temporal_cohort TEXT,
    accepted_temporal_cohort TEXT,
    date_divergence   INTEGER NOT NULL DEFAULT 0 CHECK (date_divergence IN (0, 1)),
    cohort_boundary_crossing INTEGER NOT NULL DEFAULT 0 CHECK (cohort_boundary_crossing IN (0, 1)),
    coverage_boundary_divergence INTEGER NOT NULL DEFAULT 0
        CHECK (coverage_boundary_divergence IN (0, 1)),
    date_divergence_reason TEXT,
    divergence_explained INTEGER NOT NULL DEFAULT 1 CHECK (divergence_explained IN (0, 1)),
    inventory_role    TEXT NOT NULL CHECK (
        inventory_role IN
        ('primary_target', 'support_only', 'amendment_non_target', 'control_evidence', 'excluded')
    ),
    primary_target_flag INTEGER NOT NULL CHECK (primary_target_flag IN (0, 1)),
    eligibility_state TEXT NOT NULL CHECK (
        eligibility_state IN ('eligible', 'excluded', 'review_required')
    ),
    xbrl_amendment_flag INTEGER CHECK (xbrl_amendment_flag IN (0, 1)),
    first_seen_at_utc TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS inventory_accession_registrants (
    accession_plain   TEXT NOT NULL REFERENCES inventory_accessions(accession_plain),
    registrant_cik_numeric INTEGER NOT NULL,
    registrant_cik_padded TEXT NOT NULL,
    is_primary_registrant INTEGER CHECK (is_primary_registrant IN (0, 1)),
    evidence_source   TEXT NOT NULL,
    PRIMARY KEY (accession_plain, registrant_cik_numeric)
) STRICT;

CREATE TABLE IF NOT EXISTS inventory_filing_documents (
    document_id       TEXT PRIMARY KEY,
    accession_plain   TEXT NOT NULL REFERENCES inventory_accessions(accession_plain),
    sequence_number   INTEGER,
    document_filename TEXT NOT NULL,
    document_type     TEXT,
    logical_role      TEXT NOT NULL,
    size_bytes        INTEGER,
    raw_object_id     TEXT REFERENCES raw_objects(raw_object_id),
    listed_by_index   INTEGER NOT NULL CHECK (listed_by_index IN (0, 1)),
    UNIQUE (accession_plain, document_filename)
) STRICT;

CREATE TABLE IF NOT EXISTS inventory_accession_observations (
    observation_id    TEXT PRIMARY KEY,
    accession_plain   TEXT NOT NULL REFERENCES inventory_accessions(accession_plain),
    field_name        TEXT NOT NULL,
    source_class      TEXT NOT NULL,
    precedence_rank   INTEGER NOT NULL,
    raw_value         TEXT NOT NULL,
    parsed_value      TEXT,
    snapshot_id       TEXT REFERENCES raw_source_snapshots(snapshot_id),
    observed_at_utc   TEXT NOT NULL,
    conflict_kind     TEXT,
    UNIQUE (accession_plain, field_name, source_class, raw_value, snapshot_id)
) STRICT;

CREATE TABLE IF NOT EXISTS inventory_amendment_relationships (
    relationship_id   TEXT PRIMARY KEY,
    amendment_accession_plain TEXT NOT NULL REFERENCES inventory_accessions(accession_plain),
    parent_accession_plain TEXT REFERENCES inventory_accessions(accession_plain),
    relationship      TEXT NOT NULL CHECK (
        relationship IN
        ('amends_original', 'amends_prior_amendment', 'supplements_original',
         'possible_amendment_of', 'unresolved_amendment')
    ),
    evidence          TEXT NOT NULL,
    established_at_utc TEXT NOT NULL,
    UNIQUE (amendment_accession_plain, parent_accession_plain, relationship)
) STRICT;

CREATE TABLE IF NOT EXISTS inventory_classifications (
    classification_id TEXT PRIMARY KEY,
    accession_plain   TEXT NOT NULL REFERENCES inventory_accessions(accession_plain),
    issuer_type       TEXT NOT NULL,
    shell_state_for_accession TEXT NOT NULL,
    size_stratum      TEXT,
    industry_group    TEXT,
    sic_code          TEXT,
    evidence          TEXT NOT NULL,
    classified_at_utc TEXT NOT NULL,
    UNIQUE (accession_plain)
) STRICT;

CREATE TABLE IF NOT EXISTS inventory_reasons (
    accession_plain   TEXT NOT NULL REFERENCES inventory_accessions(accession_plain),
    reason_code       TEXT NOT NULL REFERENCES reference_reason_codes(reason_code),
    detail            TEXT,
    recorded_at_utc   TEXT NOT NULL,
    PRIMARY KEY (accession_plain, reason_code)
) STRICT;

CREATE TABLE IF NOT EXISTS inventory_company_aliases (
    alias_id          TEXT PRIMARY KEY,
    cik_numeric       INTEGER NOT NULL,
    cik_padded        TEXT NOT NULL,
    alias_kind        TEXT NOT NULL CHECK (alias_kind IN ('company_name', 'ticker')),
    alias_value       TEXT NOT NULL,
    alias_valid_from  TEXT,
    alias_valid_to    TEXT,
    evidence_accession_plain TEXT REFERENCES inventory_accessions(accession_plain),
    UNIQUE (cik_numeric, alias_kind, alias_value, alias_valid_from)
) STRICT;

CREATE TABLE IF NOT EXISTS inventory_company_lineage (
    lineage_id        TEXT PRIMARY KEY,
    from_cik_numeric  INTEGER NOT NULL,
    to_cik_numeric    INTEGER NOT NULL,
    lineage_relationship TEXT NOT NULL CHECK (
        lineage_relationship IN
        ('successor_of', 'predecessor_of', 'merged_into', 'reorganized_as',
         'reverse_merger_with', 'de_spac_of')
    ),
    evidence          TEXT NOT NULL,
    observed_at_utc   TEXT NOT NULL,
    UNIQUE (from_cik_numeric, to_cik_numeric, lineage_relationship)
) STRICT;

-- --------------------------------------------------------------------------
-- Audit
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_inventory_events (
    event_id          TEXT PRIMARY KEY,
    accession_plain   TEXT,
    event_kind        TEXT NOT NULL,
    event_payload_json TEXT NOT NULL,
    occurred_at_utc   TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS audit_classification_events (
    event_id          TEXT PRIMARY KEY,
    accession_plain   TEXT NOT NULL,
    previous_state    TEXT,
    new_state         TEXT NOT NULL,
    reason_code       TEXT REFERENCES reference_reason_codes(reason_code),
    occurred_at_utc   TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS audit_checksum_events (
    event_id          TEXT PRIMARY KEY,
    raw_object_id     TEXT NOT NULL,
    observation_id    TEXT,
    expected_sha256   TEXT NOT NULL,
    observed_sha256   TEXT NOT NULL,
    outcome           TEXT NOT NULL CHECK (outcome IN ('match', 'mismatch')),
    occurred_at_utc   TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS audit_schema_events (
    event_id          TEXT PRIMARY KEY,
    source_class      TEXT NOT NULL,
    schema_drift_kind TEXT NOT NULL,
    field_path        TEXT NOT NULL,
    detail            TEXT NOT NULL,
    occurred_at_utc   TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS audit_parser_runs (
    parser_run_id     TEXT PRIMARY KEY,
    parser_name       TEXT NOT NULL,
    parser_version    TEXT NOT NULL,
    accession_plain   TEXT,
    started_at_utc    TEXT NOT NULL,
    finished_at_utc   TEXT,
    outcome           TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS audit_parser_failures (
    failure_id        TEXT PRIMARY KEY,
    parser_run_id     TEXT NOT NULL REFERENCES audit_parser_runs(parser_run_id),
    accession_plain   TEXT,
    raw_object_id     TEXT,
    failure_reason_code TEXT NOT NULL REFERENCES reference_reason_codes(reason_code),
    detail            TEXT NOT NULL,
    occurred_at_utc   TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS audit_release_diffs (
    diff_id           TEXT PRIMARY KEY,
    release_id        TEXT NOT NULL,
    compared_release_id TEXT,
    table_name        TEXT NOT NULL,
    diff_kind         TEXT NOT NULL CHECK (
        diff_kind IN ('added', 'removed', 'changed', 'cohort_reassigned')
    ),
    row_key           TEXT NOT NULL,
    detail            TEXT NOT NULL
) STRICT;

-- --------------------------------------------------------------------------
-- Releases
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS release_inventory_releases (
    release_id        TEXT PRIMARY KEY,
    release_schema_version TEXT NOT NULL,
    created_at_utc    TEXT NOT NULL,
    frozen_at_utc     TEXT,
    release_content_sha256 TEXT,
    catalog_sha256    TEXT,
    notes             TEXT
) STRICT;

CREATE TABLE IF NOT EXISTS release_membership (
    release_id        TEXT NOT NULL REFERENCES release_inventory_releases(release_id),
    accession_plain   TEXT NOT NULL REFERENCES inventory_accessions(accession_plain),
    inventory_role    TEXT NOT NULL,
    PRIMARY KEY (release_id, accession_plain)
) STRICT;

CREATE TABLE IF NOT EXISTS release_files (
    release_file_id   TEXT PRIMARY KEY,
    release_id        TEXT NOT NULL REFERENCES release_inventory_releases(release_id),
    table_name        TEXT NOT NULL,
    relative_file_path TEXT NOT NULL,
    normalized_content_sha256 TEXT NOT NULL,
    file_sha256       TEXT,
    row_count         INTEGER NOT NULL CHECK (row_count >= 0),
    UNIQUE (release_id, table_name)
) STRICT;

CREATE TABLE IF NOT EXISTS release_acceptance_results (
    result_id         TEXT PRIMARY KEY,
    release_id        TEXT NOT NULL REFERENCES release_inventory_releases(release_id),
    gate_name         TEXT NOT NULL,
    gate_result       TEXT NOT NULL CHECK (gate_result IN ('pass', 'fail', 'not_run')),
    blocks_release    INTEGER NOT NULL CHECK (blocks_release IN (0, 1)),
    evidence_artifact TEXT,
    evaluated_at_utc  TEXT NOT NULL,
    UNIQUE (release_id, gate_name)
) STRICT;

-- --------------------------------------------------------------------------
-- Indexes
-- --------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_accessions_official_cohort
    ON inventory_accessions(official_filing_temporal_cohort);
CREATE INDEX IF NOT EXISTS idx_accessions_divergence
    ON inventory_accessions(cohort_boundary_crossing, coverage_boundary_divergence);
CREATE INDEX IF NOT EXISTS idx_registrants_cik ON inventory_accession_registrants(registrant_cik_numeric);
CREATE INDEX IF NOT EXISTS idx_observations_accession ON inventory_accession_observations(accession_plain);
CREATE INDEX IF NOT EXISTS idx_reasons_code ON inventory_reasons(reason_code);
CREATE INDEX IF NOT EXISTS idx_raw_observations_object ON raw_object_observations(raw_object_id);
CREATE INDEX IF NOT EXISTS idx_attempts_state ON ops_retrieval_attempts(attempt_state);
