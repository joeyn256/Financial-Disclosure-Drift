-- Disclosure Drift operational catalog, migration 0010 (Stage M2.3-S4, Decision 017).
-- Governing record: Docs/Decisions/decision_017_s4_quota_policy_and_control_evidence.md
--
-- Additive only: seeds the frozen PILOT_QUOTA_POLICY_VERSION into the existing
-- reference_policy_versions table (created by migration 0001), using the same
-- policy-seed format migration 0009 already established. No table, column, index,
-- or trigger is created, dropped, or altered; migration 0009 is untouched.

INSERT OR REPLACE INTO reference_policy_versions
    (policy_key, policy_version, decision_record, recorded_at_utc)
VALUES
    ('pilot_quota', 'm23-pilot-quota-policy-v1',
     'Docs/Decisions/decision_017_s4_quota_policy_and_control_evidence.md', '2026-07-28T00:00:00Z');
