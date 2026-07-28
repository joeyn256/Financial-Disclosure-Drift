# Decision Index — topic lookup

**Purpose:** a topic-oriented way into `Docs/Decisions/`, for a reader who knows the *subject* they
need (e.g. "hashing") but not which decision number covers it. This index complements
[`Docs/Decisions/decision_registry.md`](Decisions/decision_registry.md), which is chronological and
authoritative on supersession; it does not replace it.

**This index cannot amend, approve, or narrow a decision.** Every row below is a pointer. When this
index and a decision record disagree, or when this index is stale relative to a newer decision, the
decision record in `Docs/Decisions/` controls — read the cited section, not this table, before acting
on it. See `Docs/Decisions/decision_registry.md` for how supersession between decisions works.

| Topic | Authoritative decision(s) | Executable owner module | Relevant migration | Status |
|---|---|---|---|---|
| Primary outcome, company universe, `primary_universe_eligible` | [002](Decisions/decision_002_primary_outcome.md) | `src/disclosure_drift/sec/entity_selector.py` (consumes the flag; the flag itself is resolved by the frozen candidate snapshot) | `0009` (`pilot_candidate_entities.primary_universe_eligible`) | Approved (2026-07-27 primary-universe-boundary clarification); outcome *implementation* not authorized in the current stage |
| Cohort authority (windows, maturity gates, bootstrap seed) | [003 v0.2](Decisions/decision_003_temporal_split.md) | `src/disclosure_drift/cohorts.py` | `0001` | Approved |
| SEC universe, canonical CIK identity | [007](Decisions/decision_007_sec_universe.md) | `src/disclosure_drift/sec/identifiers.py`, `src/disclosure_drift/sec/sources.py`, `src/disclosure_drift/sec/source_registry.py` | `0001`, `0003` | Approved |
| Raw-data governance and storage architecture | [009](Decisions/decision_009_raw_data_governance.md) | `src/disclosure_drift/sec/raw_store.py`, `src/disclosure_drift/storage/catalog.py`, `src/disclosure_drift/release/hashing.py` (§10 hashing) | `0001`, `0002`, `0008` | Approved (append-only; CLAUDE.md rule 6) |
| EDGAR operating-calendar provenance | [011](Decisions/decision_011_edgar_operating_calendar_provenance.md) | `src/disclosure_drift/sec/calendar.py`, `src/disclosure_drift/sec/calendar_evidence.py` | `0003` | Approved |
| Accession observation field resolution | [012](Decisions/decision_012_accession_observation_resolution.md) | `src/disclosure_drift/sec/accession_resolution.py`, `src/disclosure_drift/sec/observation_catalog.py` | `0006`, `0008` | Approved |
| Temporal availability / cohort date-source rule | [010](Decisions/decision_010_temporal_availability_and_cohort_assignment.md) (controls over 003 on this point) | `src/disclosure_drift/sec/temporal.py`, `src/disclosure_drift/sec/availability.py` | `0004`–`0008` | Approved |
| Amendment treatment | [008](Decisions/decision_008_filing_inventory.md) §2 | `src/disclosure_drift/sec/amendments.py` | `0002`, `0008` | Approved |
| Pilot entity quotas | [013](Decisions/decision_013_pilot_selection_mechanics.md) §3–4; [014](Decisions/decision_014_pilot_evidence_and_classification_policy.md) | `src/disclosure_drift/sec/entity_selector.py` | `0009` | Approved; S4 implemented and checkpointed (`m2.3-s4-complete`) |
| Accession quotas and caps | [013](Decisions/decision_013_pilot_selection_mechanics.md) §3–4 (entity-level counting units already frozen) | none yet — S5.1 not implemented | `0009` (schema only) | **Partially open** — entity-level counting units are frozen; accession-specific interpretation is **Pending — required before S5.1** (Decision 018) |
| Deterministic objective order (selector policy) | [013](Decisions/decision_013_pilot_selection_mechanics.md) §5 (D10) | `src/disclosure_drift/sec/entity_selector.py` (entity terms only) | — | Entity-level objective approved and implemented; accession-level terms **Pending — required before S5.1** (Decision 018) |
| Evidence rules (levels, resolution, normalization) | [014](Decisions/decision_014_pilot_evidence_and_classification_policy.md); [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §4 | `src/disclosure_drift/sec/entity_selection_store.py` | `0009` | Approved |
| Prohibited pilot uses | [015](Decisions/decision_015_pilot_use_prohibition.md); see also `Docs/leakage_register.md` L19 | — (policy, not a single module) | — | Approved |
| Schema and lifecycle (candidate/selection/manifest tables, state machines) | [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §3, §5 | `src/disclosure_drift/storage/migrations/0009_m23_pilot_schema.sql` | `0009` | Approved; Stage S3 schema exists for both entity and accession tables, but accession tables have no writer yet |
| Hashing (manifest / content-hash contract) | [013](Decisions/decision_013_pilot_selection_mechanics.md) §7 (D12); [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §8 | `src/disclosure_drift/release/hashing.py` | — | Precedent and boundaries approved; **canonical accession hash representation Pending — required before S5.1** (Decision 018) |
| Reserves | [013](Decisions/decision_013_pilot_selection_mechanics.md) §6 (D11); [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §7 | none yet | `0009` (schema only) | Policy approved; belongs to the Stage-S5 envelope as the later **S5.4** boundary — not started |
| Manifest publication | [013](Decisions/decision_013_pilot_selection_mechanics.md) §8 (D13) | `src/disclosure_drift/release/manifest.py` (general release manifest; pilot-specific manifest serialization not yet implemented) | `0009` (`pilot_manifest_versions` schema only) | Approval-semantics policy approved; implementation is **Stage S6**, not started |
| Quota-policy version | [017](Decisions/decision_017_s4_quota_policy_and_control_evidence.md) | `src/disclosure_drift/pilot_policy.py` (`PILOT_QUOTA_POLICY_VERSION`) | `0010` | Approved and implemented |
| Control structural evidence | [017](Decisions/decision_017_s4_quota_policy_and_control_evidence.md) §3 | `src/disclosure_drift/sec/entity_selector.py` (`CONTROL_QUOTAS`) | `0009`, `0010` | Approved and implemented |

## Decision 018 — pending

**Decision 018 must appear only as:**

> Pending — required before S5.1

Decision 018 does not exist yet. Nothing in this repository resolves any of the topic categories
below on Decision 018's behalf. The categories are listed so a reader can see the scope of what is
open; **this index supplies no answers, and the list is not guaranteed exhaustive** — Decision 018's
actual scope is whatever the project owner approves, and a further gap found during implementation
is a "stop and report" condition, never grounds for inferring an answer:

- the accession objective and its lexicographic composition with the already-frozen entity objective;
- the stress-accession definition;
- inaccessible / unmeasurable cross-cutting quotas and how the selector must handle them;
- canonical accession hashing (representation, field list, ordering);
- accession selected-order rule;
- per-entity base-accession floor;
- disposition of the S4 entity-only running draft once accession-level selection exists, and whether
  the S5 run is a distinct content-derived run;
- accession-family treatment (whether amendment families are grouped, how, and whether family
  identity constrains selection or enters any hash);
- `failed -> running` retry ownership (which module, if any, orchestrates a recorded retry event);
- accession-selection reason codes (whether new `reference_reason_codes` entries are required).

See [`Milestones/contracts/m23_s5_1.md`](../Milestones/contracts/m23_s5_1.md) for how these gaps
block Stage S5.1, and `Milestones/STATUS.md` for the current blocker statement.

## Full chronological registry

For every decision's exact status, supersession relationships, and date, use
[`Docs/Decisions/decision_registry.md`](Decisions/decision_registry.md) — it is the authoritative,
chronological record. This file is a topic-oriented convenience index over the same underlying
decisions and never overrides it.
