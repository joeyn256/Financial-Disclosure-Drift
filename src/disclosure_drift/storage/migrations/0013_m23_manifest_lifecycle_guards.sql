-- Disclosure Drift operational catalog, migration 0013 (Stage M2.3-S6, Decision 021).
-- Governing record: Docs/Decisions/decision_021_m23_s6_manifest_construction.md
--
-- DDL only. Creates NO table, NO column, and NO index -- exactly eight new triggers:
-- five on pilot_selection_runs governing insertion, sealing, replacement, deletion,
-- and identity; and three closing the pilot_manifest_versions eligibility, identity,
-- and replacement gaps. No policy-reference row and no reason code is seeded here:
-- PILOT_MANIFEST_HASH_POLICY_VERSION and its pilot_manifest_hash row already exist
-- (Decision 021 section 6). No existing table, column, index, trigger, or migration is
-- created, dropped, altered, replaced, or reinterpreted; migrations 0009, 0010, 0011,
-- and 0012 are untouched, including their inherited OLD-only and NULL-comparison
-- behaviour, which is deliberately left alone.
--
-- Purpose: Decision 021 sections 3.1 through 3.6 record seven schema gaps observed by
-- direct probe. selection_result_sha256 was writable, overwritable, and clearable on any
-- run in any state, and pilot_selection_runs had no INSERT guard, so a run could be
-- created already feasible and already sealed. pilot_manifest_versions had no INSERT
-- guard and its composite foreign key constrained identity rather than run state, so a
-- manifest over the permanently-running Stage-S4 draft was accepted and approvable. No
-- trigger protected any manifest identity column. INSERT OR REPLACE rewrote a manifest
-- row wholesale -- identity, lineage, every component hash and the root alike -- past
-- every guard, because SQLite fires no BEFORE DELETE trigger for replacement unless
-- PRAGMA recursive_triggers is on and this project never sets it. And the selection run
-- itself was replaceable, deletable, and re-identifiable: a replacement omitting the
-- seal cleared it, a plain DELETE removed the run, and selection_run_id, snapshot_id,
-- and selection_input_sha256 were each rewritable by direct UPDATE.
--
-- Together with migrations 0009 and 0012, the eight triggers below establish the
-- Decision 021 section 15.5 guarantee: a run is inserted only unsealed, can never be
-- replaced or deleted, cannot have its persisted identity changed, seals only through
-- the guarded update on an already-feasible run, cannot have that seal changed or
-- cleared, tolerates an identical restatement, and therefore carries a
-- selection_result_sha256 that is append-once AND remains recomputable from its
-- persisted preimage across every direct SQLite write path.
--
-- Every statement below is reproduced VERBATIM, byte for byte, from the normative SQL
-- frozen in Decision 021 section 15.1 -- all eight triggers, in the frozen order. That
-- SQL was accepted by the project owner on 2026-07-30 following the focused independent
-- governance review of v0.5. No implementation-time reinterpretation, reformulation,
-- optimization, or "equivalent" rewriting of it is permitted: a difference between this
-- file and the frozen section 15.1 SQL is a defect in this file, never a correction to
-- the decision record. The statement region below -- from the first CREATE TRIGGER line
-- to end of file -- is exactly 10939 bytes over 186 lines and reproduces the section
-- 15.3 concatenation digest
-- 7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595. This header is not
-- part of the normative statement region and is not covered by that digest.

CREATE TRIGGER pilot_selection_run_insert_unsealed_guard
BEFORE INSERT ON pilot_selection_runs
WHEN NEW.selection_result_sha256 IS NOT NULL
BEGIN
    -- Every selection run begins unsealed. The terminal result digest is established
    -- only by the append-once UPDATE guard below, on a run that is already feasible, so
    -- a row can never be created pre-sealed and present a forged terminal identity to
    -- the manifest insert guard. Without this, append-once would hold on the UPDATE
    -- path only, and a direct INSERT could manufacture a feasible, sealed run.
    SELECT RAISE(ABORT,
        'pilot selection run must be inserted unsealed; selection_result_sha256 is set only by a later append-once seal on a feasible run');
END;

CREATE TRIGGER pilot_selection_run_result_hash_guard
BEFORE UPDATE OF selection_result_sha256 ON pilot_selection_runs
BEGIN
    -- Sealing is permitted only on a run that is feasible both before and after the
    -- write. run_state is NOT NULL, so neither comparison can yield NULL and silently
    -- skip this check.
    SELECT RAISE(ABORT,
        'pilot selection result hash may be set only on a feasible selection run')
    WHERE OLD.selection_result_sha256 IS NULL
      AND NEW.selection_result_sha256 IS NOT NULL
      AND (OLD.run_state <> 'feasible' OR NEW.run_state <> 'feasible');
    -- Once sealed the digest is immutable: it may neither change nor be cleared. IS NOT
    -- is NULL-safe, so clearing to NULL is caught by the same predicate that catches a
    -- changed value. Rewriting the identical value stays permitted, so a replay that
    -- recomputes the same digest is idempotent rather than a failure.
    SELECT RAISE(ABORT,
        'pilot selection result hash is immutable once set')
    WHERE OLD.selection_result_sha256 IS NOT NULL
      AND NEW.selection_result_sha256 IS NOT OLD.selection_result_sha256;
END;

CREATE TRIGGER pilot_manifest_versions_insert_guard
BEFORE INSERT ON pilot_manifest_versions
WHEN NOT EXISTS (
    SELECT 1 FROM pilot_selection_runs
    WHERE selection_run_id = NEW.selection_run_id
      AND snapshot_id = NEW.snapshot_id
      AND run_state = 'feasible'
      AND selection_result_sha256 IS NOT NULL)
BEGIN
    SELECT RAISE(ABORT,
        'pilot manifest insert requires an existing feasible selection run whose snapshot matches and whose selection_result_sha256 is sealed');
END;

CREATE TRIGGER pilot_manifest_versions_identity_guard
BEFORE UPDATE OF manifest_id, manifest_schema_version, selection_run_id, snapshot_id,
                 ordinal_version, supersedes_manifest_id
ON pilot_manifest_versions
BEGIN
    -- Both the run being written from and the run being written to must exist, be
    -- feasible, carry this manifest's snapshot, and be sealed, so a manifest row can
    -- never be moved onto an ineligible run. This is the Decision 020 section 8.2
    -- OLD-and-NEW correction, applied here from the start rather than inherited. The
    -- explicit NOT EXISTS form fails closed on a missing run, where migration 0009's
    -- (SELECT run_state ...) <> 'running' form would yield NULL and never fire.
    SELECT RAISE(ABORT,
        'pilot manifest update requires an existing feasible selection run whose snapshot matches and whose selection_result_sha256 is sealed')
    WHERE NOT EXISTS (
            SELECT 1 FROM pilot_selection_runs
            WHERE selection_run_id = OLD.selection_run_id
              AND snapshot_id = OLD.snapshot_id
              AND run_state = 'feasible'
              AND selection_result_sha256 IS NOT NULL)
       OR NOT EXISTS (
            SELECT 1 FROM pilot_selection_runs
            WHERE selection_run_id = NEW.selection_run_id
              AND snapshot_id = NEW.snapshot_id
              AND run_state = 'feasible'
              AND selection_result_sha256 IS NOT NULL);
    -- Manifest identity is immutable in all six of its fields: the content-derived
    -- manifest_id, the manifest_schema_version and run identity that root_manifest_sha256
    -- binds, and the ordinal_version and supersedes_manifest_id that the manifest_id
    -- preimage binds. IS NOT is NULL-safe throughout, so a nullable
    -- supersedes_manifest_id cannot yield NULL and silently skip this check. Rewriting
    -- all six identically stays permitted, so an idempotent restatement is a no-op
    -- rather than a failure.
    SELECT RAISE(ABORT,
        'pilot manifest identity is immutable: manifest_id, manifest_schema_version, selection_run_id, snapshot_id, ordinal_version, and supersedes_manifest_id may never change once inserted')
    WHERE NEW.manifest_id             IS NOT OLD.manifest_id
       OR NEW.manifest_schema_version IS NOT OLD.manifest_schema_version
       OR NEW.selection_run_id        IS NOT OLD.selection_run_id
       OR NEW.snapshot_id             IS NOT OLD.snapshot_id
       OR NEW.ordinal_version         IS NOT OLD.ordinal_version
       OR NEW.supersedes_manifest_id  IS NOT OLD.supersedes_manifest_id;
END;

CREATE TRIGGER pilot_manifest_versions_replacement_guard
BEFORE INSERT ON pilot_manifest_versions
BEGIN
    -- SQLite resolves an INSERT OR REPLACE conflict by deleting the conflicting row
    -- and inserting the new one. That implicit delete does not fire migration 0009's
    -- pilot_manifest_versions_no_delete trigger unless PRAGMA recursive_triggers is
    -- on, and this project never enables it, so replacement semantics would rewrite a
    -- manifest row wholesale -- identity, lineage, every component hash and the root
    -- alike -- while the BEFORE UPDATE identity guard never runs at all. A BEFORE
    -- INSERT trigger fires before conflict resolution can delete anything, so each
    -- predicate below holds on every connection whatever the pragma settings are.
    --
    -- Route 1 -- the TEXT PRIMARY KEY.
    SELECT RAISE(ABORT,
        'pilot manifest insert conflicts with an existing manifest_id; a manifest row is never replaced, and an identical replay must reconstruct and compare instead')
    WHERE EXISTS (
        SELECT 1 FROM pilot_manifest_versions
        WHERE manifest_id = NEW.manifest_id);
    -- Route 2 -- UNIQUE (selection_run_id, snapshot_id, ordinal_version).
    SELECT RAISE(ABORT,
        'pilot manifest insert conflicts with an existing ordinal version for this selection run and snapshot; a manifest row is never replaced')
    WHERE EXISTS (
        SELECT 1 FROM pilot_manifest_versions
        WHERE selection_run_id = NEW.selection_run_id
          AND snapshot_id = NEW.snapshot_id
          AND ordinal_version = NEW.ordinal_version);
    -- Route 3 -- the partial unique index uq_pilot_manifest_single_active_approval,
    -- which admits one owner_approved manifest per run and snapshot. Without this
    -- predicate an INSERT OR REPLACE carrying manifest_state 'owner_approved' would
    -- delete an already approved manifest and stand in its place under a different
    -- manifest_id, ordinal_version and root_manifest_sha256.
    SELECT RAISE(ABORT,
        'pilot manifest insert conflicts with the existing owner-approved manifest for this selection run and snapshot; an approved manifest is never replaced')
    WHERE NEW.manifest_state = 'owner_approved'
      AND EXISTS (
        SELECT 1 FROM pilot_manifest_versions
        WHERE selection_run_id = NEW.selection_run_id
          AND snapshot_id = NEW.snapshot_id
          AND manifest_state = 'owner_approved');
END;

CREATE TRIGGER pilot_selection_run_replacement_guard
BEFORE INSERT ON pilot_selection_runs
BEGIN
    -- A selection run is created once and never re-created. SQLite resolves an
    -- INSERT OR REPLACE conflict by deleting the conflicting row and inserting the
    -- new one, and that implicit delete fires no BEFORE DELETE trigger unless PRAGMA
    -- recursive_triggers is on, which this project never sets -- so without this
    -- predicate a replacement would silently clear a sealed selection_result_sha256,
    -- or repoint the run at another snapshot or input digest, while trigger 2 never
    -- ran. Both unique routes on this table (the selection_run_id PRIMARY KEY and
    -- UNIQUE (selection_run_id, snapshot_id)) require a matching selection_run_id, so
    -- this single EXISTS covers every constructible replacement conflict, and it
    -- refuses an ordinary duplicate INSERT and an INSERT OR IGNORE too rather than
    -- letting either pass silently. A genuinely new run is unaffected.
    SELECT RAISE(ABORT,
        'pilot selection run already exists for this selection_run_id; a run row is never replaced or re-inserted, and an identical replay must look up, reconstruct, and compare instead')
    WHERE EXISTS (
        SELECT 1 FROM pilot_selection_runs
        WHERE selection_run_id = NEW.selection_run_id);
END;

CREATE TRIGGER pilot_selection_run_delete_guard
BEFORE DELETE ON pilot_selection_runs
BEGIN
    -- Selection runs are permanent in every state. There is no S6-authorized deletion
    -- lifecycle: a planned, running, failed, infeasible, infeasible_or_unproven, or
    -- feasible run is history, and a feasible sealed run additionally carries the
    -- terminal result digest a manifest is built over. This mirrors migration 0009's
    -- pilot_manifest_versions_no_delete and is unconditional -- no child-row or
    -- foreign-key test is involved -- so it holds on every connection whatever the
    -- pragma settings are, and it closes replacement-driven deletion as well as a
    -- direct DELETE.
    SELECT RAISE(ABORT,
        'pilot selection runs are undeletable in every run state; there is no authorized deletion lifecycle');
END;

CREATE TRIGGER pilot_selection_run_identity_guard
BEFORE UPDATE OF selection_run_id, snapshot_id, selection_input_sha256
ON pilot_selection_runs
BEGIN
    -- Run identity is immutable from the moment the row exists. selection_run_id is
    -- content-derived (Decision 018 section 26), snapshot_id names the frozen snapshot
    -- the run consumed, and selection_input_sha256 is an input to the section 6.1
    -- selection_result_sha256 preimage -- so a mutable copy of any of the three can
    -- silently falsify a sealed terminal digest against its own preimage. Migrations
    -- 0009 to 0012 name none of these columns in any trigger, and foreign keys guard
    -- only the first two, only on a run that already has child rows, and only while
    -- PRAGMA foreign_keys is on. IS NOT is NULL-safe throughout, and rewriting all
    -- three identically stays permitted, so an idempotent restatement is a no-op
    -- rather than a failure.
    SELECT RAISE(ABORT,
        'pilot selection run identity is immutable: selection_run_id, snapshot_id, and selection_input_sha256 may never change once inserted')
    WHERE NEW.selection_run_id       IS NOT OLD.selection_run_id
       OR NEW.snapshot_id            IS NOT OLD.snapshot_id
       OR NEW.selection_input_sha256 IS NOT OLD.selection_input_sha256;
END;
