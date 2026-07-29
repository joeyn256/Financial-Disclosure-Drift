-- Disclosure Drift operational catalog, migration 0011 (Stage M2.3-S5.2, Decision 018).
-- Governing record: Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md
--
-- Additive only: seeds the frozen PILOT_JOINT_SELECTOR_POLICY_VERSION into the existing
-- reference_policy_versions table (created by migration 0001), using the same
-- policy-seed format migrations 0009 and 0010 already established. No table, column,
-- index, or trigger is created, dropped, or altered; migrations 0009 and 0010 are
-- untouched, and the accepted S4 'pilot_selector' row is left exactly as seeded.

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('pilot_joint_selector', 'm23-joint-selector-policy-v1',
     'Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md', '2026-07-28T00:00:00Z');
