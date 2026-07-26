-- Stage M2.2-R1 safety remediation.
-- The census completion claim is derived from explicit per-instance terminal
-- states, not from the absence of one QA status string.

CREATE TABLE IF NOT EXISTS census_plan_sources (
    census_run_id       TEXT NOT NULL REFERENCES ops_ingestion_jobs(job_id),
    source_instance_id  TEXT NOT NULL,
    source_id           TEXT NOT NULL,
    request_identity    TEXT NOT NULL,
    required            INTEGER NOT NULL CHECK (required IN (0, 1)),
    source_scope        TEXT NOT NULL CHECK (source_scope IN ('base', 'historical')),
    retrieval_state     TEXT NOT NULL CHECK (retrieval_state IN (
                              'not_retrieved', 'retrieved', 'reused', 'failed',
                              'blocked', 'unavailable', 'unknown', 'quarantined')),
    snapshot_state      TEXT NOT NULL CHECK (snapshot_state IN (
                              'not_verified', 'verified', 'missing', 'hash_mismatch',
                              'representation_mismatch')),
    parser_state        TEXT NOT NULL CHECK (parser_state IN (
                              'not_started', 'completed', 'quarantined', 'failed',
                              'missing')),
    catalog_state       TEXT NOT NULL CHECK (catalog_state IN (
                              'not_started', 'committed', 'failed')),
    qa_state            TEXT NOT NULL CHECK (qa_state IN (
                              'unknown', 'passed', 'blocked', 'failed')),
    unresolved_blocking_reasons_json TEXT NOT NULL DEFAULT '[]',
    observation_id      TEXT REFERENCES census_source_observations(observation_id),
    successful_terminal INTEGER NOT NULL CHECK (successful_terminal IN (0, 1)),
    updated_at_utc      TEXT NOT NULL,
    PRIMARY KEY (census_run_id, source_instance_id)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_census_plan_sources_run_required
    ON census_plan_sources(census_run_id, required, successful_terminal);
CREATE INDEX IF NOT EXISTS idx_census_plan_sources_identity
    ON census_plan_sources(source_id, request_identity);

CREATE TABLE IF NOT EXISTS census_recovery_states (
    census_run_id       TEXT NOT NULL REFERENCES ops_ingestion_jobs(job_id),
    recovery_state_id   TEXT NOT NULL,
    scenario            TEXT NOT NULL,
    observation_id      TEXT,
    relative_path       TEXT,
    resolution_state    TEXT NOT NULL CHECK (resolution_state IN (
                              'resolved', 'blocked')),
    action_taken        TEXT NOT NULL,
    detail              TEXT NOT NULL,
    recorded_at_utc     TEXT NOT NULL,
    PRIMARY KEY (census_run_id, recovery_state_id)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_census_recovery_states_run
    ON census_recovery_states(census_run_id, resolution_state);

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('census_completion_contract', 'm2.2-r1/1.0',
     'Docs/Decisions/decision_009_raw_data_governance.md', '2026-07-26T00:00:00Z'),
    ('catalog_writer_exclusivity', 'flock/1.0',
     'Docs/Decisions/decision_009_raw_data_governance.md', '2026-07-26T00:00:00Z');
