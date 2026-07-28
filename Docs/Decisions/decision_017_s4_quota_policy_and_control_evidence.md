# Decision 017 — S4 Quota Policy Version and Boundary-Control Evidence Interpretation

**Date:** 2026-07-28
**Status:** Approved by project owner
**Type:** Implementation and provenance decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged by this record. No hypothesis, cohort window, maturity gate,
outcome definition, threshold, or seed is altered.
**Supersedes:** nothing. Freezes governance/policy points the combined Opus S4 review found open or
under-specified in Stage S4.1/S4.2: `quota_policy_version` had no frozen value (`entity_selection_store.py`
required it as an explicit argument with "no invented constant"); `excluded_pool_count` had no frozen
computation; and boundary-control evidence-state interpretation was undocumented.
**Governs:** Milestone 2.3, Stage S4 onward.
**Related:** Decision 013 (pilot selection mechanics — selector policy, D10), Decision 014 (evidence
levels and classification), Decision 016 (schema and artifact architecture, policy-constant
provenance)

## 1. Frozen quota-policy version

`PILOT_QUOTA_POLICY_VERSION = "m23-pilot-quota-policy-v1"`, defined in
`src/disclosure_drift/pilot_policy.py`. Migration `0010` seeds this exact value into the existing
`reference_policy_versions` table (`policy_key = 'pilot_quota'`), additively, using the same
policy-seed format migration `0009` already established. The Python constant and the seeded database
row must never diverge; a test asserts this.

S4.2 callers (`build_entity_selection_run_identity`, `execute_and_persist_entity_selection`) default
`quota_policy_version` to this frozen constant. This resolves the "no invented constant" ambiguity
`entity_selection_store.py` previously flagged: production callers now have an authoritative default
to use, while the parameter remains overridable for tests that must pin an arbitrary,
non-production value.

## 2. `excluded_pool_count` definition

For a quota tied to a specific dimension/key (`size`, `industry`, `history`, or `control`),
`excluded_pool_count` is the number of candidates in the raw candidate pool whose **raw
classification** matches that exact quota key but who cannot contribute because the applicable
eligibility or evidence gate fails (i.e., they are not present in the operating-eligible or, for
controls, the per-kind control-eligible set). A candidate belonging to another size stratum,
industry family, history class, or control kind is never counted against this quota, regardless of
its own eligibility.

For summary quotas:

- `summary.operating_total`: operating-category candidates that fail operating-slot admission.
- `summary.total_controls`: control-category candidates that fail control-slot admission (i.e., are
  not eligible for any control kind).
- `summary.total_entities`: the sum of the two counts above (operating and control categories are
  disjoint).

For `history_status.eventful_currently_inactive`: candidates that are raw `history_class = 'eventful'`
and `currently_inactive = true` but fail operating-slot admission.

A fully eligible, zero-slack candidate pool (every raw-matching candidate is fully eligible) reports
`excluded_pool_count = 0` for every quota. The column name (`excluded_pool_count`, on
`pilot_quota_results`) is unchanged; only its computation is corrected.

## 3. Boundary-control structural-evidence interpretation

Boundary-control membership (`control_kind`) is a frozen structural classification, established by
the frozen candidate snapshot (Stage S3), not a graded evidence judgment. A control candidate may
provisionally satisfy its control quota when: `candidate_category = 'control'`; `control_kind` is
exactly one approved control class; `primary_universe_eligible = false`; and it satisfies the
existing structural control-eligibility rule (`entity_selector._control_eligible`).

Size, industry, history, and primary-universe **evidence levels** are unrelated to the control-kind
classification and may remain `unavailable` for a control candidate without blocking its control
quota — those dimensions simply do not apply to a boundary control's own selection criterion.

For a passing control quota result, `pilot_quota_results.evidence_state = 'provisional'` means **the
frozen control-kind structural classification is provisionally accepted** — it is not a claim that
every evidence dimension recorded on that candidate's row is resolved. Every non-control affirmative
quota's `evidence_state = 'provisional'` requirement (Decision 014 section 1: only `'provisional'`
evidence may satisfy an affirmative quota) is unaffected by this interpretation and continues to fail
closed on `review_required`/`conflicting`/`unavailable`/`unproven` evidence.

## 4. Confirmation: the S4 objective is unchanged

This decision does not alter Decision 013 section 5's frozen selector objective. The S4 entity
objective remains, in order: (1) satisfy every hard entity quota; (2) minimize the sum of integer
`evidence_penalty` across all 24 selected entities (operating and control); (3) minimize the complete
sorted vector of all 24 selected entity hashes lexicographically; (4) canonical CIK only as the final
fallback after hash equality. Nothing in this record changes that ordering, the search's completeness
requirements, or its node-limit semantics.

## 5. Reason

The combined Opus S4 review found two governance gaps (no frozen `quota_policy_version`; no frozen
interpretation of control-quota `evidence_state = 'provisional'`) and one computation defect
(`excluded_pool_count` counted unrelated-stratum candidates as excluded). None of these are research
definitions and none reads, fits on, or is informed by any 2022–2026 outcome; all are
engineering/provenance policy choices about how the frozen S4 selector's diagnostics are computed and
versioned.
