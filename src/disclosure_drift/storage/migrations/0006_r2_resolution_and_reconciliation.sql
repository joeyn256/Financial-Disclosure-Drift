-- Disclosure Drift operational catalog, migration 0006 (Stage M2.2-R2.3 and R2.5).
-- Governing records: Decisions 008, 010, 012.
--
-- Canonical accession fields are derived views over immutable observations. This
-- migration persists the derivation itself, not just its result, so any canonical
-- value can be traced to the observations that produced it and re-resolving an
-- unchanged observation set reproduces the same hash.
--
-- Nothing here permits an observation to be edited or removed. Full-index
-- reconciliation records comparisons only: it never merges identities or deletes rows.

CREATE TABLE IF NOT EXISTS census_accession_field_resolutions (
    accession_plain     TEXT NOT NULL,
    field_name          TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN (
                            'resolved', 'resolved_by_correction', 'unresolved', 'absent')),
    resolved_value      TEXT,
    authority_class     TEXT CHECK (authority_class IN (
                            'filing_level_metadata', 'entity_submissions', 'full_index',
                            'identity_alias') OR authority_class IS NULL),
    policy_version      TEXT NOT NULL,
    winning_observation_ids_json  TEXT NOT NULL DEFAULT '[]',
    competing_observation_ids_json TEXT NOT NULL DEFAULT '[]',
    correction_evidence_id TEXT,
    reason_codes_json   TEXT NOT NULL DEFAULT '[]',
    is_material         INTEGER NOT NULL CHECK (is_material IN (0, 1)),
    blocks_dependents   INTEGER NOT NULL CHECK (blocks_dependents IN (0, 1)),
    detail              TEXT NOT NULL DEFAULT '',
    resolution_sha256   TEXT NOT NULL,
    resolved_at_utc     TEXT NOT NULL,
    PRIMARY KEY (accession_plain, field_name, policy_version)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_census_field_resolution_status
    ON census_accession_field_resolutions(status);
CREATE INDEX IF NOT EXISTS idx_census_field_resolution_blocking
    ON census_accession_field_resolutions(blocks_dependents);

-- Cohort consequences of a resolved filing date. Prior cohorts are retained rather
-- than overwritten, so a correction's effect stays auditable.
CREATE TABLE IF NOT EXISTS census_accession_cohort_resolutions (
    accession_plain     TEXT NOT NULL,
    policy_version      TEXT NOT NULL,
    official_filing_temporal_cohort TEXT NOT NULL,
    accepted_temporal_cohort TEXT NOT NULL,
    prior_filing_cohorts_json TEXT NOT NULL DEFAULT '[]',
    cohort_boundary_crossed INTEGER NOT NULL CHECK (cohort_boundary_crossed IN (0, 1)),
    requires_2024_approval INTEGER NOT NULL CHECK (requires_2024_approval IN (0, 1)),
    approval_reference  TEXT,
    reason_codes_json   TEXT NOT NULL DEFAULT '[]',
    resolution_sha256   TEXT NOT NULL,
    resolved_at_utc     TEXT NOT NULL,
    PRIMARY KEY (accession_plain, policy_version)
) STRICT;

-- Full-index coverage reconciliation. Both sides' values and lineage are retained for
-- every comparison, including the ones that disagree.
CREATE TABLE IF NOT EXISTS census_index_reconciliation (
    reconciliation_id   TEXT PRIMARY KEY,
    census_run_id       TEXT NOT NULL,
    accession_plain     TEXT,
    state               TEXT NOT NULL CHECK (state IN (
                            'matching', 'index_only', 'submissions_only', 'conflicting',
                            'unavailable', 'indeterminate')),
    instance_key        TEXT,
    index_values_json   TEXT NOT NULL DEFAULT '{}',
    submissions_values_json TEXT NOT NULL DEFAULT '{}',
    index_observation_id TEXT,
    submissions_observation_id TEXT,
    conflicting_fields_json TEXT NOT NULL DEFAULT '[]',
    is_approved_form    INTEGER NOT NULL DEFAULT 0 CHECK (is_approved_form IN (0, 1)),
    reason_codes_json   TEXT NOT NULL DEFAULT '[]',
    detail              TEXT NOT NULL DEFAULT '',
    policy_version      TEXT NOT NULL,
    recorded_at_utc     TEXT NOT NULL
) STRICT;

CREATE INDEX IF NOT EXISTS idx_census_reconciliation_state
    ON census_index_reconciliation(state);

-- Required index instances in the census plan. A missing instance blocks completion:
-- coverage cannot be confirmed against evidence that was never retrieved.
CREATE TABLE IF NOT EXISTS census_index_instances (
    census_run_id       TEXT NOT NULL,
    instance_key        TEXT NOT NULL,
    year                INTEGER NOT NULL,
    quarter             INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    required            INTEGER NOT NULL DEFAULT 1 CHECK (required IN (0, 1)),
    retrieved           INTEGER NOT NULL DEFAULT 0 CHECK (retrieved IN (0, 1)),
    parse_usable        INTEGER NOT NULL DEFAULT 0 CHECK (parse_usable IN (0, 1)),
    observation_id      TEXT,
    recorded_at_utc     TEXT NOT NULL,
    PRIMARY KEY (census_run_id, instance_key)
) STRICT;

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('accession_resolution', '1.0',
     'Docs/Decisions/decision_012_accession_observation_resolution.md',
     '2026-07-26T00:00:00Z'),
    ('full_index_reconciliation', '1.0',
     'Docs/Decisions/decision_008_filing_inventory.md', '2026-07-26T00:00:00Z');
