-- Disclosure Drift operational catalog, migration 0002.
-- Governing records: Decisions 007, 009, 010, 011.
--
-- Authority: rows in census_source_observations are the operational source of
-- truth for what has been retrieved. The immutable raw objects are the evidence.
-- The JSONL audit file is a derived, append-only projection that must be
-- reconstructible from these rows, so a projection failure never makes an
-- observation appear unrecorded.
--
-- Three byte identities are stored separately and are never conflated:
--   transport_sha256  bytes as delivered by the transport for this response
--                     (HTTP content-coding already removed; content_encoding
--                     records what was declared)
--   stored_sha256     bytes actually written to disk under storage_representation
--   logical_sha256    the parser's input for this object; equals content_sha256,
--                     the Decision 009 integrity anchor
-- An archive member hash is never written into any of these columns: members live
-- in census_archive_members with explicit archive-to-member lineage.

CREATE TABLE IF NOT EXISTS census_source_observations (
    observation_id        TEXT PRIMARY KEY,
    source_id             TEXT NOT NULL,
    request_identity      TEXT NOT NULL,
    requested_url         TEXT NOT NULL,
    final_url             TEXT,
    purpose               TEXT NOT NULL,
    retrieved_at_utc      TEXT NOT NULL,
    outcome               TEXT NOT NULL CHECK (outcome IN (
                              'stored_new', 'unchanged_content', 'superseded',
                              'reused_snapshot', 'quarantined', 'failed')),
    http_status           INTEGER,
    etag                  TEXT,
    last_modified         TEXT,
    validators_sent_json  TEXT NOT NULL DEFAULT '{}',
    headers_json          TEXT NOT NULL DEFAULT '{}',
    declared_content_type TEXT,
    observed_content_kind TEXT,
    content_encoding      TEXT,
    transport_sha256      TEXT,
    stored_sha256         TEXT,
    logical_sha256        TEXT,
    content_sha256        TEXT,
    transport_size_bytes  INTEGER,
    content_size_bytes    INTEGER,
    stored_size_bytes     INTEGER,
    storage_representation TEXT CHECK (storage_representation IN (
                              'identical', 'deterministic_gzip') OR
                              storage_representation IS NULL),
    relative_storage_path TEXT,
    parser_version        TEXT,
    supersedes_observation_id TEXT,
    reused_observation_id TEXT,
    redirects_json        TEXT NOT NULL DEFAULT '[]',
    redirect_hops_json    TEXT NOT NULL DEFAULT '[]',
    attempts              INTEGER NOT NULL DEFAULT 0,
    detail                TEXT NOT NULL DEFAULT '',
    projected_to_audit    INTEGER NOT NULL DEFAULT 0
                              CHECK (projected_to_audit IN (0, 1)),
    recorded_at_utc       TEXT NOT NULL
) STRICT;

CREATE INDEX IF NOT EXISTS idx_census_observations_identity
    ON census_source_observations (request_identity, retrieved_at_utc);
CREATE INDEX IF NOT EXISTS idx_census_observations_source
    ON census_source_observations (source_id, retrieved_at_utc);
CREATE INDEX IF NOT EXISTS idx_census_observations_projection
    ON census_source_observations (projected_to_audit);

CREATE TABLE IF NOT EXISTS census_observation_reasons (
    observation_id    TEXT NOT NULL,
    reason_code       TEXT NOT NULL,
    detail            TEXT,
    recorded_at_utc   TEXT NOT NULL,
    PRIMARY KEY (observation_id, reason_code),
    FOREIGN KEY (observation_id) REFERENCES census_source_observations (observation_id),
    FOREIGN KEY (reason_code) REFERENCES reference_reason_codes (reason_code)
) STRICT;

-- Archive-to-member lineage. The archive object is never replaced by its members.
CREATE TABLE IF NOT EXISTS census_archive_members (
    observation_id            TEXT NOT NULL,
    member_index              INTEGER NOT NULL,
    member_name               TEXT NOT NULL,
    member_sha256             TEXT NOT NULL,
    member_compressed_size_bytes   INTEGER NOT NULL,
    member_uncompressed_size_bytes INTEGER NOT NULL,
    archive_relative_path     TEXT,
    archive_sha256            TEXT,
    recorded_at_utc           TEXT NOT NULL,
    PRIMARY KEY (observation_id, member_name),
    FOREIGN KEY (observation_id) REFERENCES census_source_observations (observation_id)
) STRICT;

CREATE TABLE IF NOT EXISTS census_recovery_events (
    event_id          TEXT PRIMARY KEY,
    scenario          TEXT NOT NULL CHECK (scenario IN (
                          'interrupted_part_download',
                          'object_without_catalog_row',
                          'catalog_row_without_object',
                          'audit_projection_interrupted',
                          'identical_content_rerun',
                          'changed_content_rerun',
                          'not_modified_reuse',
                          'quarantined_response')),
    observation_id    TEXT,
    relative_path     TEXT,
    action_taken      TEXT NOT NULL,
    detail            TEXT NOT NULL,
    occurred_at_utc   TEXT NOT NULL
) STRICT;

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('census_source_observations', '1.0',
     'Docs/Decisions/decision_009_raw_data_governance.md', '2026-07-26T00:00:00Z');
