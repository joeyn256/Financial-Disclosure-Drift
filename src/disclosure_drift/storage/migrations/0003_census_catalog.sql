-- Disclosure Drift registrant census, migration 0003.
-- Parsed source records remain distinct from normalized census observations.

CREATE TABLE IF NOT EXISTS census_parser_runs (
    parser_run_id       TEXT PRIMARY KEY,
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    parser_id           TEXT NOT NULL,
    parser_version      TEXT NOT NULL,
    started_at_utc      TEXT NOT NULL,
    finished_at_utc     TEXT NOT NULL,
    parsed_count        INTEGER NOT NULL CHECK (parsed_count >= 0),
    quarantined_count   INTEGER NOT NULL CHECK (quarantined_count >= 0),
    outcome             TEXT NOT NULL CHECK (outcome IN ('completed', 'completed_with_quarantine',
                                'failed')),
    summary_json        TEXT NOT NULL,
    UNIQUE (source_observation_id, parser_id, parser_version)
) STRICT;

CREATE TABLE IF NOT EXISTS census_parsed_records (
    parsed_record_id    TEXT PRIMARY KEY,
    parser_run_id       TEXT NOT NULL REFERENCES census_parser_runs(parser_run_id),
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    native_identity     TEXT NOT NULL,
    record_sha256       TEXT NOT NULL,
    member_name         TEXT,
    record_path         TEXT,
    record_index        INTEGER,
    payload_json        TEXT NOT NULL,
    unknown_fields_json TEXT NOT NULL DEFAULT '[]',
    warnings_json       TEXT NOT NULL DEFAULT '[]',
    reason_codes_json   TEXT NOT NULL DEFAULT '[]',
    duplicate_indicator INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_indicator IN (0, 1)),
    conflict_indicator  INTEGER NOT NULL DEFAULT 0 CHECK (conflict_indicator IN (0, 1)),
    recorded_at_utc     TEXT NOT NULL,
    UNIQUE (source_observation_id, parser_run_id, native_identity, record_sha256,
            member_name, record_path, record_index)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_census_parsed_identity
    ON census_parsed_records(native_identity);
CREATE INDEX IF NOT EXISTS idx_census_parsed_observation
    ON census_parsed_records(source_observation_id);

CREATE TABLE IF NOT EXISTS census_quarantined_records (
    quarantine_record_id TEXT PRIMARY KEY,
    parser_run_id       TEXT NOT NULL REFERENCES census_parser_runs(parser_run_id),
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    native_identity     TEXT,
    member_name         TEXT,
    record_path         TEXT,
    record_index        INTEGER,
    reason_codes_json   TEXT NOT NULL,
    detail              TEXT NOT NULL,
    raw_excerpt         TEXT NOT NULL,
    recorded_at_utc     TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS census_historical_references (
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    registrant_cik_padded TEXT NOT NULL,
    historical_file      TEXT NOT NULL,
    filing_count         INTEGER,
    filing_from          TEXT,
    filing_to            TEXT,
    member_name          TEXT,
    record_index         INTEGER,
    retrieval_status     TEXT NOT NULL CHECK (retrieval_status IN
                              ('not_retrieved', 'retrieved', 'unavailable', 'failed',
                               'blocked', 'unknown')),
    PRIMARY KEY (source_observation_id, registrant_cik_padded, historical_file)
) STRICT;

CREATE TABLE IF NOT EXISTS census_registrants (
    cik_numeric          INTEGER PRIMARY KEY,
    cik_padded           TEXT NOT NULL UNIQUE,
    first_observed_at_utc TEXT NOT NULL,
    latest_observed_at_utc TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS census_registrant_observations (
    registrant_observation_id TEXT PRIMARY KEY,
    cik_numeric          INTEGER NOT NULL REFERENCES census_registrants(cik_numeric),
    observation_kind    TEXT NOT NULL CHECK (observation_kind IN
                              ('company_name', 'former_name', 'ticker', 'exchange',
                               'sic', 'fiscal_year_end', 'entity_type', 'filing_status')),
    value_text           TEXT NOT NULL,
    valid_from           TEXT,
    valid_to             TEXT,
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    parsed_record_id     TEXT NOT NULL REFERENCES census_parsed_records(parsed_record_id),
    source_field         TEXT NOT NULL,
    observed_at_utc      TEXT NOT NULL,
    UNIQUE (cik_numeric, observation_kind, value_text, valid_from, valid_to,
            source_observation_id, parsed_record_id)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_census_registrant_history
    ON census_registrant_observations(cik_numeric, observation_kind);

CREATE TABLE IF NOT EXISTS census_candidate_lineage_edges (
    candidate_edge_id   TEXT PRIMARY KEY,
    from_cik_padded     TEXT NOT NULL,
    to_cik_padded       TEXT NOT NULL,
    evidence_kind       TEXT NOT NULL,
    evidence_value      TEXT NOT NULL,
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    status              TEXT NOT NULL CHECK (status = 'candidate_only'),
    detail              TEXT NOT NULL,
    UNIQUE (from_cik_padded, to_cik_padded, evidence_kind, evidence_value,
            source_observation_id),
    CHECK (from_cik_padded <> to_cik_padded)
) STRICT;

CREATE TABLE IF NOT EXISTS census_accessions (
    accession_plain     TEXT PRIMARY KEY,
    accession_dashed    TEXT NOT NULL UNIQUE,
    registrant_cik_numeric INTEGER NOT NULL REFERENCES census_registrants(cik_numeric),
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

CREATE TABLE IF NOT EXISTS census_accession_observations (
    accession_observation_id TEXT PRIMARY KEY,
    accession_plain     TEXT NOT NULL REFERENCES census_accessions(accession_plain),
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    parsed_record_id    TEXT NOT NULL REFERENCES census_parsed_records(parsed_record_id),
    field_name          TEXT NOT NULL,
    raw_value_json      TEXT NOT NULL,
    observed_at_utc     TEXT NOT NULL,
    conflict_indicator INTEGER NOT NULL DEFAULT 0 CHECK (conflict_indicator IN (0, 1)),
    UNIQUE (accession_plain, source_observation_id, parsed_record_id, field_name)
) STRICT;

CREATE TABLE IF NOT EXISTS census_calendar_days (
    calendar_date       TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN ('operating', 'non_operating',
                                'unknown')),
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    evidence_id         TEXT NOT NULL,
    derivation_version  TEXT NOT NULL,
    conflicting         INTEGER NOT NULL CHECK (conflicting IN (0, 1)),
    detail              TEXT NOT NULL,
    PRIMARY KEY (calendar_date, source_observation_id, evidence_id, derivation_version)
) STRICT;

CREATE TABLE IF NOT EXISTS census_qa_metrics (
    census_run_id       TEXT NOT NULL,
    metric_name         TEXT NOT NULL,
    dimension_json      TEXT NOT NULL DEFAULT '{}',
    metric_status       TEXT NOT NULL CHECK (metric_status IN
                              ('value', 'zero', 'unavailable', 'failed', 'blocked',
                               'unknown', 'not_retrieved')),
    metric_value        INTEGER,
    detail              TEXT NOT NULL,
    recorded_at_utc     TEXT NOT NULL,
    PRIMARY KEY (census_run_id, metric_name, dimension_json)
) STRICT;

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('registrant_census', '1.0',
     'Docs/Decisions/decision_007_sec_universe.md', '2026-07-26T00:00:00Z'),
    ('parsed_source_record', '1.0',
     'Docs/Decisions/decision_009_raw_data_governance.md', '2026-07-26T00:00:00Z');
