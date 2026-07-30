-- Disclosure Drift operational catalog, migration 0012 (Stage M2.3-S5.4, Decision 020).
-- Governing record: Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md
--
-- DDL only. Creates exactly one new STRICT table, pilot_selection_entity_reasons, and
-- exactly four new triggers: fail-closed INSERT/UPDATE/DELETE lifecycle guards and one
-- additive feasible-transition disposition-completeness trigger. No policy-reference row
-- and no reason code is seeded here: reference_reason_codes is seeded at runtime from
-- reasons.py, and PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION and its
-- pilot_replacement_signature row already exist. No existing table, column, index,
-- trigger, or migration is created, dropped, altered, replaced, or reinterpreted;
-- migrations 0009, 0010, and 0011 are untouched.
--
-- Purpose: migration 0009 has no lawful location for a durable, target-specific record
-- that a selected entity's S5.4 reserve construction produced no compatible reserve --
-- no table carries all three of selection_run_id, a selected entity, and a
-- reference_reason_codes foreign key (Decision 020 section 8.1). The owner authorized
-- this one additive migration rather than weakening the durability requirement.
--
-- Every statement below is reproduced VERBATIM, byte for byte, from the normative SQL
-- frozen in Decision 020 section 8.2 -- the table and all four triggers. That SQL passed
-- the focused independent governance re-review of 2026-07-30. No implementation-time
-- reinterpretation, reformulation, optimization, or "equivalent" rewriting of it is
-- permitted: a difference between this file and the frozen section 8.2 SQL is a defect
-- in this file, never a correction to the decision record.

CREATE TABLE IF NOT EXISTS pilot_selection_entity_reasons (
    selection_run_id  TEXT NOT NULL,
    snapshot_id       TEXT NOT NULL,
    cik_numeric       INTEGER NOT NULL,
    reason_scope      TEXT NOT NULL CHECK (reason_scope IN ('reserve')),
    reason_code       TEXT NOT NULL REFERENCES reference_reason_codes(reason_code),
    recorded_at_utc   TEXT NOT NULL,
    -- One disposition per (run, snapshot, target, scope): reason_code is deliberately
    -- NOT part of the key, so a target can never carry two reserve dispositions.
    PRIMARY KEY (selection_run_id, snapshot_id, cik_numeric, reason_scope),
    FOREIGN KEY (selection_run_id, snapshot_id, cik_numeric)
        REFERENCES pilot_selected_entities (selection_run_id, snapshot_id, cik_numeric),
    -- Only the one authorized reserve-scope code may ever be stored (section 13).
    CHECK (reason_scope <> 'reserve'
           OR reason_code = 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE')
) STRICT;
CREATE TRIGGER pilot_selection_entity_reasons_insert_guard
BEFORE INSERT ON pilot_selection_entity_reasons
WHEN NOT EXISTS (
    SELECT 1 FROM pilot_selection_runs
    WHERE selection_run_id = NEW.selection_run_id AND run_state = 'running')
BEGIN
    SELECT RAISE(ABORT,
        'pilot selection entity reason insert requires an existing running selection run');
END;

CREATE TRIGGER pilot_selection_entity_reasons_update_guard
BEFORE UPDATE ON pilot_selection_entity_reasons
BEGIN
    -- Both the run being written from and the run being written to must exist and be
    -- running, so a row can never be moved onto a terminal run.
    SELECT RAISE(ABORT,
        'pilot selection entity reason update requires an existing running selection run')
    WHERE NOT EXISTS (
            SELECT 1 FROM pilot_selection_runs
            WHERE selection_run_id = OLD.selection_run_id AND run_state = 'running')
       OR NOT EXISTS (
            SELECT 1 FROM pilot_selection_runs
            WHERE selection_run_id = NEW.selection_run_id AND run_state = 'running');
    -- Target identity is immutable: a disposition row is never reassigned between runs,
    -- snapshots, or selected entities. All three columns are NOT NULL, so no comparison
    -- can yield NULL and silently skip this check.
    SELECT RAISE(ABORT,
        'pilot selection entity reason target identity is immutable')
    WHERE NEW.selection_run_id <> OLD.selection_run_id
       OR NEW.snapshot_id      <> OLD.snapshot_id
       OR NEW.cik_numeric      <> OLD.cik_numeric;
END;

CREATE TRIGGER pilot_selection_entity_reasons_delete_guard
BEFORE DELETE ON pilot_selection_entity_reasons
WHEN NOT EXISTS (
    SELECT 1 FROM pilot_selection_runs
    WHERE selection_run_id = OLD.selection_run_id AND run_state = 'running')
BEGIN
    SELECT RAISE(ABORT,
        'pilot selection entity reason delete requires an existing running selection run');
END;
CREATE TRIGGER pilot_selection_run_feasible_requires_reserve_disposition
BEFORE UPDATE OF run_state ON pilot_selection_runs
WHEN NEW.run_state = 'feasible' AND OLD.run_state = 'running'
BEGIN
    SELECT RAISE(ABORT,
        'pilot selection feasible transition requires exactly one reserve disposition per selected entity')
    WHERE EXISTS (
        SELECT 1 FROM pilot_selected_entities AS se
        WHERE se.selection_run_id = NEW.selection_run_id
          AND se.snapshot_id = NEW.snapshot_id
          AND ( (SELECT COUNT(*) FROM pilot_reserves AS r
                  WHERE r.selection_run_id = se.selection_run_id
                    AND r.snapshot_id = se.snapshot_id
                    AND r.target_cik_numeric = se.cik_numeric)
              + (SELECT COUNT(*) FROM pilot_selection_entity_reasons AS pr
                  WHERE pr.selection_run_id = se.selection_run_id
                    AND pr.snapshot_id = se.snapshot_id
                    AND pr.cik_numeric = se.cik_numeric
                    AND pr.reason_scope = 'reserve')
              ) <> 1
    );
    SELECT RAISE(ABORT,
        'pilot selection feasible transition requires every reserve package to be reserve_rank 1')
    WHERE EXISTS (
        SELECT 1 FROM pilot_reserves AS r
        WHERE r.selection_run_id = NEW.selection_run_id
          AND r.snapshot_id = NEW.snapshot_id
          AND r.reserve_rank <> 1
    );
    SELECT RAISE(ABORT,
        'pilot selection reserve-scope disposition admits only REVIEW_PILOT_NO_COMPATIBLE_RESERVE')
    WHERE EXISTS (
        SELECT 1 FROM pilot_selection_entity_reasons AS pr
        WHERE pr.selection_run_id = NEW.selection_run_id
          AND pr.snapshot_id = NEW.snapshot_id
          AND pr.reason_scope = 'reserve'
          AND pr.reason_code <> 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE'
    );
END;
