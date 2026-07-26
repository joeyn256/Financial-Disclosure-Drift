-- Disclosure Drift operational catalog, migration 0005 (Stage M2.2-R2).
-- Governing records: Decisions 008, 009, 010, 011.
--
-- R2.1 requires that "zero records" never be ambiguous. A nested source region
-- that was present, correctly typed, and empty is a genuine zero. A region that was
-- absent, null, wrongly typed, internally inconsistent, or unreadable yields an
-- unknown count, carries a release-blocking reason, and must prevent required-source
-- success. Those verdicts are persisted here rather than inferred from a row count.

CREATE TABLE IF NOT EXISTS census_structural_observations (
    structural_observation_id TEXT PRIMARY KEY,
    parser_run_id       TEXT NOT NULL REFERENCES census_parser_runs(parser_run_id),
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    region              TEXT NOT NULL,
    state               TEXT NOT NULL CHECK (state IN (
                            'valid_present', 'valid_empty', 'absent', 'null',
                            'wrong_type', 'malformed', 'unavailable', 'indeterminate')),
    observed_type       TEXT NOT NULL,
    member_name         TEXT,
    record_path         TEXT,
    row_count           INTEGER,
    count_is_trustworthy INTEGER NOT NULL CHECK (count_is_trustworthy IN (0, 1)),
    is_genuine_zero     INTEGER NOT NULL CHECK (is_genuine_zero IN (0, 1)),
    reason_codes_json   TEXT NOT NULL DEFAULT '[]',
    detail              TEXT NOT NULL DEFAULT '',
    raw_excerpt         TEXT NOT NULL DEFAULT '',
    recorded_at_utc     TEXT NOT NULL,
    UNIQUE (source_observation_id, parser_run_id, region, member_name)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_census_structural_state
    ON census_structural_observations(state);
CREATE INDEX IF NOT EXISTS idx_census_structural_untrustworthy
    ON census_structural_observations(count_is_trustworthy);

-- A malformed historical reference cannot be stored in census_historical_references:
-- that table's primary key requires a usable file name. Malformed entries are
-- preserved here instead of being skipped, with the raw entry retained verbatim.
CREATE TABLE IF NOT EXISTS census_malformed_historical_references (
    malformed_reference_id TEXT PRIMARY KEY,
    source_observation_id TEXT NOT NULL
        REFERENCES census_source_observations(observation_id),
    registrant_cik_padded TEXT,
    observed_name       TEXT,
    member_name         TEXT,
    record_index        INTEGER,
    problems_json       TEXT NOT NULL,
    unknown_fields_json TEXT NOT NULL DEFAULT '[]',
    raw_entry_json      TEXT NOT NULL,
    recorded_at_utc     TEXT NOT NULL,
    UNIQUE (source_observation_id, member_name, record_index)
) STRICT;

-- Valid references gain an explicit retrievability flag so the orchestrator never
-- has to re-derive it, and unknown keys observed on the entry are retained.
ALTER TABLE census_historical_references
    ADD COLUMN is_retrievable INTEGER NOT NULL DEFAULT 1;
ALTER TABLE census_historical_references
    ADD COLUMN unknown_fields_json TEXT NOT NULL DEFAULT '[]';

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('census_structural_evidence', '1.0',
     'Docs/Decisions/decision_008_filing_inventory.md', '2026-07-26T00:00:00Z');
