-- Disclosure Drift operational catalog, migration 0007 (Stage M2.2-R2.7).
-- Governing records: Decisions 008, 009, 012.
--
-- Quarterly index instances are retrieved sequentially in chronological order by a
-- single worker through the existing SEC client. Each instance's progress is persisted
-- transactionally so a stopped run resumes from the earliest unsatisfied required
-- instance rather than starting over, and a fully verified satisfied instance is never
-- retrieved again merely because an earlier process stopped.
--
-- Nothing here mutates a previous snapshot. A new source version or an explicit refresh
-- creates a new observation and a new reconciliation result under the existing
-- versioning policy; failed evidence is preserved, never overwritten or deleted.

ALTER TABLE census_index_instances
    ADD COLUMN lifecycle_state TEXT NOT NULL DEFAULT 'planned';
ALTER TABLE census_index_instances
    ADD COLUMN instance_kind TEXT NOT NULL DEFAULT 'required_closed_quarter';
ALTER TABLE census_index_instances
    ADD COLUMN reconciled INTEGER NOT NULL DEFAULT 0;
ALTER TABLE census_index_instances
    ADD COLUMN satisfied INTEGER NOT NULL DEFAULT 0;
ALTER TABLE census_index_instances
    ADD COLUMN logical_retrievals INTEGER NOT NULL DEFAULT 0;
ALTER TABLE census_index_instances
    ADD COLUMN http_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE census_index_instances
    ADD COLUMN parsed_row_count INTEGER;
ALTER TABLE census_index_instances
    ADD COLUMN reason_codes_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE census_index_instances
    ADD COLUMN detail TEXT NOT NULL DEFAULT '';
ALTER TABLE census_index_instances
    ADD COLUMN updated_at_utc TEXT;

CREATE INDEX IF NOT EXISTS idx_census_index_instance_state
    ON census_index_instances(census_run_id, lifecycle_state);
CREATE INDEX IF NOT EXISTS idx_census_index_instance_satisfied
    ON census_index_instances(satisfied);

-- Append-only lifecycle history. Every transition is retained, including failures, so a
-- resumed run can prove what an earlier process had already done.
CREATE TABLE IF NOT EXISTS census_index_instance_events (
    event_id            TEXT PRIMARY KEY,
    census_run_id       TEXT NOT NULL,
    instance_key        TEXT NOT NULL,
    lifecycle_state     TEXT NOT NULL CHECK (lifecycle_state IN (
                            'planned', 'retrieval_started', 'retrieved',
                            'validly_reused', 'parsed', 'reconciled', 'satisfied',
                            'failed', 'blocked', 'unavailable', 'indeterminate')),
    observation_id      TEXT,
    logical_retrievals  INTEGER NOT NULL DEFAULT 0,
    http_attempts       INTEGER NOT NULL DEFAULT 0,
    reason_codes_json   TEXT NOT NULL DEFAULT '[]',
    detail              TEXT NOT NULL DEFAULT '',
    occurred_at_utc     TEXT NOT NULL
) STRICT;

CREATE INDEX IF NOT EXISTS idx_census_index_events_instance
    ON census_index_instance_events(census_run_id, instance_key, occurred_at_utc);

-- Per-run accounting, kept separate from per-instance rows so logical retrievals and
-- actual HTTP attempts can never be conflated in a report.
CREATE TABLE IF NOT EXISTS census_index_retrieval_accounting (
    census_run_id       TEXT PRIMARY KEY,
    instances_planned   INTEGER NOT NULL DEFAULT 0,
    instances_already_satisfied INTEGER NOT NULL DEFAULT 0,
    logical_budget      INTEGER NOT NULL DEFAULT 0,
    logical_retrievals_initiated INTEGER NOT NULL DEFAULT 0,
    http_attempts       INTEGER NOT NULL DEFAULT 0,
    retries             INTEGER NOT NULL DEFAULT 0,
    instances_successful INTEGER NOT NULL DEFAULT 0,
    instances_failed    INTEGER NOT NULL DEFAULT 0,
    instances_remaining INTEGER NOT NULL DEFAULT 0,
    stopped_early       INTEGER NOT NULL DEFAULT 0 CHECK (stopped_early IN (0, 1)),
    stop_reason         TEXT,
    recorded_at_utc     TEXT NOT NULL
) STRICT;

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('index_retrieval_orchestration', '1.0',
     'Docs/Decisions/decision_008_filing_inventory.md', '2026-07-26T00:00:00Z');
