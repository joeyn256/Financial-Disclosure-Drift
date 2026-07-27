-- Disclosure Drift operational catalog, migration 0008 (Stage M2.2-R3).
-- Governing record: Decision 009.
--
-- SQLite is authoritative. This migration makes observation-to-observation
-- lineage relational rather than advisory, and adds structured history for
-- deterministic JSONL projection recovery. Migrations 0001-0007 remain unchanged.

-- Rebuild is required because SQLite cannot add self-referential foreign keys or
-- table CHECK constraints with ALTER TABLE. Foreign-key enforcement is disabled
-- only around this transaction; application preflight validates every existing
-- row before this script is executed, and application postflight verifies the
-- resulting foreign-key graph.
PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

CREATE TABLE census_source_observations_r3 (
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
    transport_size_bytes  INTEGER CHECK (
                              transport_size_bytes IS NULL OR transport_size_bytes >= 0),
    content_size_bytes    INTEGER CHECK (
                              content_size_bytes IS NULL OR content_size_bytes >= 0),
    stored_size_bytes     INTEGER CHECK (
                              stored_size_bytes IS NULL OR stored_size_bytes >= 0),
    storage_representation TEXT CHECK (storage_representation IN (
                              'identical', 'deterministic_gzip') OR
                              storage_representation IS NULL),
    relative_storage_path TEXT,
    parser_version        TEXT,
    supersedes_observation_id TEXT,
    reused_observation_id TEXT,
    redirects_json        TEXT NOT NULL DEFAULT '[]',
    redirect_hops_json    TEXT NOT NULL DEFAULT '[]',
    attempts              INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    detail                TEXT NOT NULL DEFAULT '',
    projected_to_audit    INTEGER NOT NULL DEFAULT 0
                              CHECK (projected_to_audit IN (0, 1)),
    recorded_at_utc       TEXT NOT NULL,
    FOREIGN KEY (supersedes_observation_id)
        REFERENCES census_source_observations_r3 (observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY (reused_observation_id)
        REFERENCES census_source_observations_r3 (observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    CHECK (supersedes_observation_id IS NULL
           OR supersedes_observation_id <> observation_id),
    CHECK (reused_observation_id IS NULL
           OR reused_observation_id <> observation_id),
    CHECK (supersedes_observation_id IS NULL OR reused_observation_id IS NULL),
    CHECK ((outcome = 'superseded') = (supersedes_observation_id IS NOT NULL)),
    CHECK (outcome NOT IN ('unchanged_content', 'reused_snapshot')
           OR reused_observation_id IS NOT NULL),
    CHECK (reused_observation_id IS NULL
           OR outcome IN ('unchanged_content', 'reused_snapshot')),
    CHECK ((reused_observation_id IS NULL
            AND supersedes_observation_id IS NULL) OR (
           relative_storage_path IS NOT NULL
           AND relative_storage_path <> ''
           AND transport_sha256 IS NOT NULL
           AND transport_sha256 <> ''
           AND stored_sha256 IS NOT NULL
           AND stored_sha256 <> ''
           AND logical_sha256 IS NOT NULL
           AND logical_sha256 <> ''
           AND content_sha256 IS NOT NULL
           AND content_sha256 <> ''
           AND transport_size_bytes IS NOT NULL
           AND stored_size_bytes IS NOT NULL
           AND content_size_bytes IS NOT NULL
           AND storage_representation IS NOT NULL
           AND parser_version IS NOT NULL
           AND parser_version <> ''
           AND observed_content_kind IS NOT NULL
           AND observed_content_kind <> '')),
    CHECK ((reused_observation_id IS NULL
            AND supersedes_observation_id IS NULL) OR (
           logical_sha256 = content_sha256
           AND transport_sha256 = logical_sha256
           AND transport_size_bytes = content_size_bytes
           AND (storage_representation <> 'identical'
                OR (stored_sha256 = logical_sha256
                    AND stored_size_bytes = content_size_bytes))))
) STRICT;

INSERT INTO census_source_observations_r3 (
    observation_id, source_id, request_identity, requested_url, final_url,
    purpose, retrieved_at_utc, outcome, http_status, etag, last_modified,
    validators_sent_json, headers_json, declared_content_type,
    observed_content_kind, content_encoding, transport_sha256, stored_sha256,
    logical_sha256, content_sha256, transport_size_bytes, content_size_bytes,
    stored_size_bytes, storage_representation, relative_storage_path,
    parser_version, supersedes_observation_id, reused_observation_id,
    redirects_json, redirect_hops_json, attempts, detail, projected_to_audit,
    recorded_at_utc
)
SELECT
    observation_id, source_id, request_identity, requested_url, final_url,
    purpose, retrieved_at_utc, outcome, http_status, etag, last_modified,
    validators_sent_json, headers_json, declared_content_type,
    observed_content_kind, content_encoding, transport_sha256, stored_sha256,
    logical_sha256, content_sha256, transport_size_bytes, content_size_bytes,
    stored_size_bytes, storage_representation, relative_storage_path,
    parser_version, supersedes_observation_id, reused_observation_id,
    redirects_json, redirect_hops_json, attempts, detail, projected_to_audit,
    recorded_at_utc
FROM census_source_observations;

DROP TABLE census_source_observations;
ALTER TABLE census_source_observations_r3 RENAME TO census_source_observations;

CREATE INDEX idx_census_observations_identity
    ON census_source_observations (request_identity, retrieved_at_utc);
CREATE INDEX idx_census_observations_source
    ON census_source_observations (source_id, retrieved_at_utc);
CREATE INDEX idx_census_observations_projection
    ON census_source_observations (projected_to_audit);
CREATE INDEX idx_census_observations_supersedes
    ON census_source_observations (supersedes_observation_id);
CREATE INDEX idx_census_observations_reuses
    ON census_source_observations (reused_observation_id);

-- A combined graph walk rejects cycles that mix supersession and reuse edges.
-- UNION (rather than UNION ALL) also bounds traversal if corrupt legacy data is
-- encountered while a database is being diagnosed.
CREATE TRIGGER census_observation_lineage_insert
BEFORE INSERT ON census_source_observations
BEGIN
    SELECT RAISE(ABORT, 'observation lineage cycle')
    WHERE EXISTS (
        WITH RECURSIVE lineage(observation_id) AS (
            SELECT NEW.supersedes_observation_id
            WHERE NEW.supersedes_observation_id IS NOT NULL
            UNION
            SELECT NEW.reused_observation_id
            WHERE NEW.reused_observation_id IS NOT NULL
            UNION
            SELECT prior.supersedes_observation_id
            FROM census_source_observations AS prior
            JOIN lineage ON prior.observation_id = lineage.observation_id
            WHERE prior.supersedes_observation_id IS NOT NULL
            UNION
            SELECT prior.reused_observation_id
            FROM census_source_observations AS prior
            JOIN lineage ON prior.observation_id = lineage.observation_id
            WHERE prior.reused_observation_id IS NOT NULL
        )
        SELECT 1 FROM lineage WHERE observation_id = NEW.observation_id
    );

    SELECT RAISE(ABORT, 'incompatible supersession source or request identity')
    WHERE NEW.supersedes_observation_id IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM census_source_observations AS prior
          WHERE prior.observation_id = NEW.supersedes_observation_id
            AND (prior.source_id <> NEW.source_id
                 OR prior.request_identity <> NEW.request_identity)
      );
    SELECT RAISE(ABORT, 'supersession target is not a prior observation')
    WHERE NEW.supersedes_observation_id IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM census_source_observations AS prior
          WHERE prior.observation_id = NEW.supersedes_observation_id
            AND prior.retrieved_at_utc > NEW.retrieved_at_utc
      );
    SELECT RAISE(ABORT, 'supersession target is not usable preserved evidence')
    WHERE NEW.supersedes_observation_id IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM census_source_observations AS prior
          WHERE prior.observation_id = NEW.supersedes_observation_id
            AND (prior.outcome NOT IN (
                     'stored_new', 'superseded',
                     'unchanged_content', 'reused_snapshot')
                 OR prior.relative_storage_path IS NULL
                 OR prior.relative_storage_path = ''
                 OR prior.transport_sha256 IS NULL
                 OR prior.transport_sha256 = ''
                 OR prior.stored_sha256 IS NULL
                 OR prior.stored_sha256 = ''
                 OR prior.logical_sha256 IS NULL
                 OR prior.logical_sha256 = ''
                 OR prior.content_sha256 IS NULL
                 OR prior.content_sha256 = ''
                 OR prior.transport_size_bytes IS NULL
                 OR prior.stored_size_bytes IS NULL
                 OR prior.content_size_bytes IS NULL
                 OR prior.storage_representation IS NULL
                 OR prior.parser_version IS NULL
                 OR prior.parser_version = ''
                 OR prior.observed_content_kind IS NULL
                 OR prior.observed_content_kind = ''
                 OR prior.logical_sha256 <> prior.content_sha256
                 OR prior.transport_sha256 <> prior.logical_sha256
                 OR prior.transport_size_bytes <> prior.content_size_bytes
                 OR (prior.storage_representation = 'identical'
                     AND (prior.stored_sha256 <> prior.logical_sha256
                          OR prior.stored_size_bytes <> prior.content_size_bytes)))
      );

    SELECT RAISE(ABORT, 'incompatible reuse source or request identity')
    WHERE NEW.reused_observation_id IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM census_source_observations AS prior
          WHERE prior.observation_id = NEW.reused_observation_id
            AND (prior.source_id <> NEW.source_id
                 OR prior.request_identity <> NEW.request_identity)
      );
    SELECT RAISE(ABORT, 'reuse target is not a prior observation')
    WHERE NEW.reused_observation_id IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM census_source_observations AS prior
          WHERE prior.observation_id = NEW.reused_observation_id
            AND prior.retrieved_at_utc > NEW.retrieved_at_utc
      );
    SELECT RAISE(ABORT, 'reuse target does not own a verified raw object')
    WHERE NEW.reused_observation_id IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM census_source_observations AS prior
          WHERE prior.observation_id = NEW.reused_observation_id
            AND (prior.outcome NOT IN ('stored_new', 'superseded')
                 OR prior.relative_storage_path IS NULL
                 OR prior.transport_sha256 IS NULL
                 OR prior.stored_sha256 IS NULL
                 OR prior.logical_sha256 IS NULL
                 OR prior.content_sha256 IS NULL
                 OR prior.transport_size_bytes IS NULL
                 OR prior.stored_size_bytes IS NULL
                 OR prior.content_size_bytes IS NULL
                 OR prior.storage_representation IS NULL
                 OR prior.parser_version IS NULL
                 OR prior.observed_content_kind IS NULL
                 OR prior.relative_storage_path = ''
                 OR prior.transport_sha256 = ''
                 OR prior.stored_sha256 = ''
                 OR prior.logical_sha256 = ''
                 OR prior.content_sha256 = ''
                 OR prior.parser_version = ''
                 OR prior.observed_content_kind = ''
                 OR prior.logical_sha256 <> prior.content_sha256
                 OR prior.transport_sha256 <> prior.logical_sha256
                 OR prior.transport_size_bytes <> prior.content_size_bytes
                 OR (prior.storage_representation = 'identical'
                     AND (prior.stored_sha256 <> prior.logical_sha256
                          OR prior.stored_size_bytes <> prior.content_size_bytes)))
      );
    SELECT RAISE(ABORT, 'reused raw-object metadata mismatch')
    WHERE NEW.reused_observation_id IS NOT NULL
      AND EXISTS (
          SELECT 1 FROM census_source_observations AS prior
          WHERE prior.observation_id = NEW.reused_observation_id
            AND (prior.relative_storage_path IS NOT NEW.relative_storage_path
                 OR prior.transport_sha256 IS NOT NEW.transport_sha256
                 OR prior.stored_sha256 IS NOT NEW.stored_sha256
                 OR prior.logical_sha256 IS NOT NEW.logical_sha256
                 OR prior.content_sha256 IS NOT NEW.content_sha256
                 OR prior.transport_size_bytes IS NOT NEW.transport_size_bytes
                 OR prior.stored_size_bytes IS NOT NEW.stored_size_bytes
                 OR prior.content_size_bytes IS NOT NEW.content_size_bytes
                 OR prior.storage_representation IS NOT NEW.storage_representation
                 OR prior.parser_version IS NOT NEW.parser_version
                 OR prior.observed_content_kind IS NOT NEW.observed_content_kind)
      );

    -- If a deferred reference was inserted before its target in this transaction,
    -- validate those already-present dependants when the target arrives.
    SELECT RAISE(ABORT, 'deferred lineage has incompatible source or request identity')
    WHERE EXISTS (
        SELECT 1 FROM census_source_observations AS dependant
        WHERE (dependant.supersedes_observation_id = NEW.observation_id
               OR dependant.reused_observation_id = NEW.observation_id)
          AND (dependant.source_id <> NEW.source_id
               OR dependant.request_identity <> NEW.request_identity)
    );
    SELECT RAISE(ABORT, 'deferred lineage target is not prior')
    WHERE EXISTS (
        SELECT 1 FROM census_source_observations AS dependant
        WHERE (dependant.supersedes_observation_id = NEW.observation_id
               OR dependant.reused_observation_id = NEW.observation_id)
          AND NEW.retrieved_at_utc > dependant.retrieved_at_utc
    );
    SELECT RAISE(ABORT, 'deferred supersession target is not usable preserved evidence')
    WHERE EXISTS (
        SELECT 1 FROM census_source_observations AS dependant
        WHERE dependant.supersedes_observation_id = NEW.observation_id
          AND (NEW.outcome NOT IN (
                   'stored_new', 'superseded',
                   'unchanged_content', 'reused_snapshot')
               OR NEW.relative_storage_path IS NULL
               OR NEW.relative_storage_path = ''
               OR NEW.transport_sha256 IS NULL
               OR NEW.transport_sha256 = ''
               OR NEW.stored_sha256 IS NULL
               OR NEW.stored_sha256 = ''
               OR NEW.logical_sha256 IS NULL
               OR NEW.logical_sha256 = ''
               OR NEW.content_sha256 IS NULL
               OR NEW.content_sha256 = ''
               OR NEW.transport_size_bytes IS NULL
               OR NEW.stored_size_bytes IS NULL
               OR NEW.content_size_bytes IS NULL
               OR NEW.storage_representation IS NULL
               OR NEW.parser_version IS NULL
               OR NEW.parser_version = ''
               OR NEW.observed_content_kind IS NULL
               OR NEW.observed_content_kind = ''
               OR NEW.logical_sha256 <> NEW.content_sha256
               OR NEW.transport_sha256 <> NEW.logical_sha256
               OR NEW.transport_size_bytes <> NEW.content_size_bytes
               OR (NEW.storage_representation = 'identical'
                   AND (NEW.stored_sha256 <> NEW.logical_sha256
                        OR NEW.stored_size_bytes <> NEW.content_size_bytes)))
    );
    SELECT RAISE(ABORT, 'deferred reuse target does not own a verified raw object')
    WHERE EXISTS (
        SELECT 1 FROM census_source_observations AS dependant
        WHERE dependant.reused_observation_id = NEW.observation_id
          AND (NEW.outcome NOT IN ('stored_new', 'superseded')
               OR NEW.relative_storage_path IS NULL
               OR NEW.transport_sha256 IS NULL
               OR NEW.stored_sha256 IS NULL
               OR NEW.logical_sha256 IS NULL
               OR NEW.content_sha256 IS NULL
               OR NEW.transport_size_bytes IS NULL
               OR NEW.stored_size_bytes IS NULL
               OR NEW.content_size_bytes IS NULL
               OR NEW.storage_representation IS NULL
               OR NEW.parser_version IS NULL
               OR NEW.observed_content_kind IS NULL
               OR NEW.relative_storage_path = ''
               OR NEW.transport_sha256 = ''
               OR NEW.stored_sha256 = ''
               OR NEW.logical_sha256 = ''
               OR NEW.content_sha256 = ''
               OR NEW.parser_version = ''
               OR NEW.observed_content_kind = ''
               OR NEW.logical_sha256 <> NEW.content_sha256
               OR NEW.transport_sha256 <> NEW.logical_sha256
               OR NEW.transport_size_bytes <> NEW.content_size_bytes
               OR (NEW.storage_representation = 'identical'
                   AND (NEW.stored_sha256 <> NEW.logical_sha256
                        OR NEW.stored_size_bytes <> NEW.content_size_bytes)))
    );
    SELECT RAISE(ABORT, 'deferred reused raw-object metadata mismatch')
    WHERE EXISTS (
        SELECT 1 FROM census_source_observations AS dependant
        WHERE dependant.reused_observation_id = NEW.observation_id
          AND (dependant.relative_storage_path IS NOT NEW.relative_storage_path
               OR dependant.transport_sha256 IS NOT NEW.transport_sha256
               OR dependant.stored_sha256 IS NOT NEW.stored_sha256
               OR dependant.logical_sha256 IS NOT NEW.logical_sha256
               OR dependant.content_sha256 IS NOT NEW.content_sha256
               OR dependant.transport_size_bytes IS NOT NEW.transport_size_bytes
               OR dependant.stored_size_bytes IS NOT NEW.stored_size_bytes
               OR dependant.content_size_bytes IS NOT NEW.content_size_bytes
               OR dependant.storage_representation IS NOT NEW.storage_representation
               OR dependant.parser_version IS NOT NEW.parser_version
               OR dependant.observed_content_kind IS NOT NEW.observed_content_kind)
    );
END;

-- Lineage edges are immutable after insertion. Critical identity and raw-object
-- metadata cannot be changed while a row participates in lineage. The projection
-- flag remains intentionally updateable by the durable projection protocol.
CREATE TRIGGER census_observation_lineage_edge_immutable
BEFORE UPDATE OF observation_id, supersedes_observation_id, reused_observation_id
ON census_source_observations
WHEN OLD.observation_id IS NOT NEW.observation_id
  OR OLD.supersedes_observation_id IS NOT NEW.supersedes_observation_id
  OR OLD.reused_observation_id IS NOT NEW.reused_observation_id
BEGIN
    SELECT RAISE(ABORT, 'observation lineage is immutable');
END;

CREATE TRIGGER census_observation_lineage_identity_immutable
BEFORE UPDATE OF source_id, request_identity, retrieved_at_utc, outcome
ON census_source_observations
WHEN (
    OLD.supersedes_observation_id IS NOT NULL
    OR OLD.reused_observation_id IS NOT NULL
    OR EXISTS (
        SELECT 1 FROM census_source_observations AS dependant
        WHERE dependant.supersedes_observation_id = OLD.observation_id
           OR dependant.reused_observation_id = OLD.observation_id
    )
) AND (
    OLD.source_id IS NOT NEW.source_id
    OR OLD.request_identity IS NOT NEW.request_identity
    OR OLD.retrieved_at_utc IS NOT NEW.retrieved_at_utc
    OR OLD.outcome IS NOT NEW.outcome
)
BEGIN
    SELECT RAISE(ABORT, 'lineage identity metadata is immutable');
END;

CREATE TRIGGER census_observation_lineage_object_immutable
BEFORE UPDATE OF relative_storage_path, transport_sha256, stored_sha256,
                 logical_sha256, content_sha256, transport_size_bytes,
                 stored_size_bytes, content_size_bytes, storage_representation,
                 parser_version, observed_content_kind
ON census_source_observations
WHEN (
    OLD.supersedes_observation_id IS NOT NULL
    OR OLD.reused_observation_id IS NOT NULL
    OR EXISTS (
        SELECT 1 FROM census_source_observations AS dependant
        WHERE dependant.supersedes_observation_id = OLD.observation_id
           OR dependant.reused_observation_id = OLD.observation_id
    )
) AND (
    OLD.relative_storage_path IS NOT NEW.relative_storage_path
    OR OLD.transport_sha256 IS NOT NEW.transport_sha256
    OR OLD.stored_sha256 IS NOT NEW.stored_sha256
    OR OLD.logical_sha256 IS NOT NEW.logical_sha256
    OR OLD.content_sha256 IS NOT NEW.content_sha256
    OR OLD.transport_size_bytes IS NOT NEW.transport_size_bytes
    OR OLD.stored_size_bytes IS NOT NEW.stored_size_bytes
    OR OLD.content_size_bytes IS NOT NEW.content_size_bytes
    OR OLD.storage_representation IS NOT NEW.storage_representation
    OR OLD.parser_version IS NOT NEW.parser_version
    OR OLD.observed_content_kind IS NOT NEW.observed_content_kind
)
BEGIN
    SELECT RAISE(ABORT, 'lineage raw-object metadata is immutable');
END;

CREATE TABLE census_projection_recovery_events (
    event_id            TEXT PRIMARY KEY,
    detected_condition  TEXT NOT NULL,
    projection_path     TEXT NOT NULL,
    expected_count      INTEGER NOT NULL CHECK (expected_count >= 0),
    observed_count      INTEGER CHECK (observed_count IS NULL OR observed_count >= 0),
    rebuild_identity    TEXT,
    projection_sha256   TEXT,
    resolution_state    TEXT NOT NULL CHECK (resolution_state IN ('blocked', 'resolved')),
    release_blocking_before_resolution INTEGER NOT NULL
                            CHECK (release_blocking_before_resolution IN (0, 1)),
    detected_at_utc     TEXT NOT NULL,
    resolved_at_utc     TEXT,
    detail              TEXT NOT NULL DEFAULT '',
    CHECK ((resolution_state = 'resolved') = (resolved_at_utc IS NOT NULL))
) STRICT;

CREATE INDEX idx_census_projection_recovery_resolution
    ON census_projection_recovery_events (resolution_state, detected_at_utc);

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('migration_provenance', 'sha256-chain/1.0',
     'Docs/Decisions/decision_009_raw_data_governance.md', '2026-07-26T00:00:00Z'),
    ('observation_lineage', 'foreign-key-and-trigger/1.0',
     'Docs/Decisions/decision_009_raw_data_governance.md', '2026-07-26T00:00:00Z'),
    ('audit_projection_recovery', 'deterministic-rebuild/1.0',
     'Docs/Decisions/decision_009_raw_data_governance.md', '2026-07-26T00:00:00Z');

-- The application records this migration's exact name and checksum in
-- ops_schema_migrations and commits that row in this same transaction. It then
-- restores PRAGMA foreign_keys. Keeping bookkeeping inside the schema transaction
-- removes the crash window between durable DDL and durable provenance.
