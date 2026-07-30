# Decision Registry — Disclosure Drift

**Purpose:** a single index of every record in `Docs/Decisions/`, its current status, and any
supersession relationship between records. This registry does not itself change any frozen
definition. It reports what the existing decision records already say.

**Created:** 2026-07-27, during the M2.3 governance-repair exception (Decision 010 audit finding
C10: "No decision registry exists"; corrected-plan §7.5). Authority for creating this file is the
scoped documentation exception described in `Milestones/milestone_2_3_pilot_selection_plan.md`
§"Documentation authorization note".

**How to use this registry:** when two records appear to address the same topic, the record with
the later **Supersedes**/**Superseded by** relationship controls for the specific point it names.
A supersession is always partial unless the superseding record says otherwise — it never implies
the earlier record is wrong or withdrawn on any point it does not name.

## Index

| ID | Title | Date | Status | Supersedes | Superseded by | Governs |
|---|---|---|---|---|---|---|
| 001 | Milestone 0 Novelty Boundary | 2026-07-25 | Accepted working decision; final literature refresh still required | — | — | Milestone 0 |
| 002 | Primary Outcome and Company Universe | 2026-07-25 (approved and clarified 2026-07-27) | Approved by project owner, with a 2026-07-27 primary-universe-boundary clarification (`primary_universe_eligible` flag, engineering-only financial pilot entities, XBRL concept-hierarchy freezing rule) | — | — | Primary outcome definition |
| 003 (v0.1, archived) | Temporal Split and Holdout Protection | 2026-07-25 | Proposed freeze pending project-owner approval (draft; superseded by v0.2) | — | 003 (v0.2, live) | — |
| 003 (v0.2, live — `decision_003_temporal_split.md`) | Temporal Split and Holdout Protection | 2026-07-25 | Approved by project owner; **cohort date-source rule superseded in part** | 003 draft v0.1 | 010 (date-source rule only) | Cohort windows, maturity gates |
| 003 (v0.2, archived duplicate — `decision_003_temporal_split_v0_2.md`) | Temporal Split and Holdout Protection | 2026-07-25 | Unmodified historical snapshot — identical to the live 003 record as it stood before the 2026-07-27 governance-repair banner was added; left untouched by that repair | — | 010 (date-source rule only, via live 003) | — |
| 004 | Evaluation, Inference, and Rewrite Protocol | 2026-07-25 | Proposed freeze pending project-owner approval | — | — | Evaluation protocol |
| 005 | 2025 and 2026 Recency Extension | 2026-07-25 | Approved by project owner | — | — | Recency-cohort evaluation timing |
| 006 | Final Contribution Boundary | 2026-07-25 | Approved for Milestone 0 completion | Provisional contribution language in earlier charter versions | — | Milestone 0 completion |
| 007 | SEC Universe and Issuer Identity | 2026-07-25 | Approved by project owner | — | — | Milestone 2 onward |
| 008 | Filing Inventory and Amendment Policy | 2026-07-25 | Approved by project owner | — | — | Milestone 2 onward |
| 009 | Raw-Data Governance and Storage Architecture | 2026-07-25 | Approved by project owner | — | — | Milestone 2 onward |
| **010** | **Temporal Availability and Cohort Assignment** | 2026-07-25 | Approved by project owner | 003 (date-source rule only) | — | Milestone 2 onward — **controlling record for cohort date-source assignment (`official_filing_temporal_cohort`)** |
| 011 | EDGAR Operating-Calendar Provenance | 2026-07-26 | Approved by project owner | — | — | Stage M2.2 onward |
| 012 | Accession Observation Resolution | 2026-07-26 | Approved | nothing (extends 008, 010, 011) | — | Milestone 2, Stage M2.2-R2.3 |
| 013 | M2.3 Pilot Selection Mechanics (as-of cutoff, candidate storage, counting units, multi-registrant accounting, selector policy, reserves/substitution, manifest hashing, approval semantics) | 2026-07-27 | Approved by project owner | — | — | Milestone 2.3 onward |
| 014 | M2.3 Pilot Evidence Levels and Classification Policy (evidence-level taxonomy, filer-size classification, industry assignment and SIC-family mapping, stable/eventful history, amendment-purpose categories, provisional cohort assignment) | 2026-07-27 | Approved by project owner. §4 (SIC-to-industry-family mapping) was approved as a draft pending owner review on 2026-07-27 and was frozen as `sic-family-mapping/0.2` on 2026-07-27 during the same-day governance-repair correction pass. | — | — | Milestone 2.3 onward |
| 015 | M2.3 Pilot-Use Prohibition | 2026-07-27 | Approved by project owner | — | — | Milestone 2.3 onward; see `Docs/leakage_register.md` L19 |
| 016 | M2.3 Schema and Artifact Architecture (Stage S3 candidate/selection/manifest table family, ID scheme, lifecycle rules, integrity constraints, reserve-package signature model, hash boundaries) | 2026-07-27 | Approved by project owner | — | — | Milestone 2.3, Stage S3 onward (design only; no implementation authorized) |
| 017 | S4 Quota Policy Version and Boundary-Control Evidence Interpretation (frozen `PILOT_QUOTA_POLICY_VERSION`, `excluded_pool_count` definition, boundary-control structural-evidence interpretation, confirms Decision 013's objective is unchanged) | 2026-07-28 | Approved by project owner | — | — | Milestone 2.3, Stage S4 onward |
| 018 | [M2.3 Stage S5 Accession Selection Policy](decision_018_m23_s5_accession_selection_policy.md) (applicability-aware evidence penalty within the unchanged Decision 013 §5 objective; accession roles, caps, and entity accession floors; canonical dashed accession identity and tie-break formula; deterministic `selected_order`; S4-draft disposition and a distinct content-derived S5 joint run; accession families and linked-amendment coverage; fiscal-year-end and name-change derivation; 2009/2010 pairing; controlled deferral of the unmeasurable difficult-or-nonstandard-package quota; node-limit and failure semantics; retry prohibition; S5.1/S5.2 methodological boundary; future `PILOT_JOINT_SELECTOR_POLICY_VERSION`, future additive migration `0011`, and five future reason codes) | 2026-07-28 | Approved by project owner | — | — | Milestone 2.3, Stage S5 onward (policy only; **authorizes no implementation**) |
| 019 | [M2.3 Stage S5 Frozen-Storage-to-Pure-Input Mapping Policy](decision_019_m23_s5_storage_to_pure_input_mapping.md) (candidate-snapshot representation and loader-conversion rules for the four S5.1 pure inputs with no stored column: amendment-linkage evidence, multi-registrant evidence, explicit pre-study support provenance, and former-name identity evidence; snapshot-freeze validation obligations; run-identity content) | 2026-07-28 | **APPROVED — OWNER APPROVED 2026-07-28** | — | — | Milestone 2.3, Stage S5.2 onward (**clarifies** Decision 018 §§5.3, 13, 15, 19, 25; binding; authorizes no implementation — a separate bounded S5.2 implementation prompt is required) |
| 020 | [M2.3 Stage S5.4 Reserve Architecture and Quota-Contribution Membership](decision_020_m23_s5_4_reserve_architecture.md) (recommended architecture for reserves; quota-contribution membership published from the sole accepted S5.1 witness derivation; the single-`running`-window write boundary migration `0009`'s triggers impose; reserve purpose, target coverage, one rank-1 package per target, eligible pool, tie-break, signature and exact-equality rule, cross-target replacement reuse; identity and hashing separation with the input schema version unchanged; fail-closed failure and reconstruction rules; one authorized reason code; the nine owner rulings recorded, plus the §8.3 owner test-scoping clarification assigning each invariant to its owning enforcement layer; **and one future additive migration `0012_m23_selection_entity_reasons.sql` authorized in principle — one new STRICT `pilot_selection_entity_reasons` table plus four triggers whose complete SQL is frozen in §8.2: fail-closed INSERT/UPDATE/DELETE lifecycle guards with immutable target identity and an OLD-and-NEW running check, and an additive feasible-transition disposition-completeness trigger — not created by the record, editing no existing migration, and the only migration authorized for the stage**) | 2026-07-29 | **APPROVED — OWNER APPROVED 2026-07-30** | — | — | Milestone 2.3, Stage S5.4 onward (**interprets and extends** Decision 018 §§19, 22, 29 and operationalizes Decision 013 §6 and Decision 016 §7; binding). **Stage S5.4 is implemented, independently accepted, and checkpointed — final independent recommendation `ACCEPT_M23_S5_4_FOR_CHECKPOINT`, owner-accepted 2026-07-30, accepted suite 1899 passed and 1 skipped, migration `0012` created and accepted, twelve implementation paths delivered, five accepted methodological limitations recorded in §19.1, tagged `m2.3-s5.4-complete` supplementing the immutable `m2.3-s5-complete`. S6 remains excluded and not begun; no S5 selection or reserve is a manifest or publication input. It authorizes no further implementation — a new explicit owner authorization is required for any future S5.4 change.** |

## Controlling record by topic (quick lookup)

| Topic | Controlling record |
|---|---|
| Cohort windows, maturity gates, bootstrap seed | Decision 003 (v0.2, live), cohort windows unchanged by Decision 010 |
| **Cohort date-source rule** (which date assigns `official_filing_temporal_cohort`) | **Decision 010** — official SEC filing date, not acceptance date |
| Primary outcome formula | Decision 002 — approved by project owner (2026-07-27 clarification, corrected 2026-07-27, corrected again 2026-07-27 fourth pass: `primary_universe_eligible` is not a SIC-alone flag — it requires an eligible, non-control candidate, sufficiently resolved required evidence, SIC outside 6000–6999, and no other Decision 002 exclusion; the M2.3 pilot's **eight** primary-universe-ineligible entities — four boundary controls plus four operating-financial-institutions quota entities — are engineering-only and never enter primary outcome construction) |
| SEC universe, canonical CIK identity | Decision 007 |
| Filing inventory, amendment handling | Decision 008 |
| Raw-data storage architecture | Decision 009 |
| EDGAR operating-calendar provenance | Decision 011 |
| Accession observation field resolution | Decision 012 |
| M2.3 pilot selection mechanics | Decision 013 |
| M2.3 pilot evidence levels and classification | Decision 014 |
| M2.3 pilot-use prohibition | Decision 015 |
| M2.3 Stage S3 schema and artifact architecture | Decision 016 |
| M2.3 Stage S4 quota-policy version, `excluded_pool_count`, boundary-control evidence interpretation | Decision 017 |
| M2.3 Stage S5 accession selection policy (roles, caps, floors, accession identity and hashing, `selected_order`, S4-draft disposition and S5 run identity, families and linked amendments, cross-cutting quota operationalization, node-limit/failure/retry semantics, S5 stage boundaries) | Decision 018 |
| M2.3 Stage S5 frozen-storage-to-pure-input mapping | **Decision 019** — `APPROVED — OWNER APPROVED 2026-07-28`; the controlling record for amendment-linkage evidence conversion (§5), multi-registrant evidence aggregation (§6), explicit pre-study support provenance (§7), and former-name identity-evidence conversion (§8), plus the snapshot-freeze obligations (§9) and the run-identity content those mappings contribute (§10) |
| M2.3 Stage S5.4 reserve architecture and quota-contribution membership | **Decision 020 — `APPROVED — OWNER APPROVED 2026-07-30`; binding, and the controlling record for reserves at S5.4** alongside Decision 013 §6 and Decision 016 §7, which it operationalizes rather than replaces. The owner's nine rulings are in its §14, the migration-`0012` ruling in §8.2, and the test-scoping clarification in §8.3. The focused independent governance re-review of the exact `0012` DDL — table and all four triggers — recommended `ACCEPT_DECISION_020_FOR_OWNER_APPROVAL`, closing the 2026-07-29 lifecycle defect. The §8.2 SQL is frozen and was reproduced verbatim in migration `0012`, which is **created and accepted**. **Stage S5.4 is accepted and complete** (2026-07-30, `ACCEPT_M23_S5_4_FOR_CHECKPOINT`); §19 records that acceptance and §19.1 the five accepted methodological limitations. The record authorizes no further implementation |

## Open items this registry surfaces but does not resolve

- As of 2026-07-27: Decision 001 remains "Accepted working decision; final literature refresh still
  required" and Decision 004 remains "Proposed freeze pending project-owner approval" in their own
  files. This registry reports that status verbatim; it does not grant or withhold approval on
  their behalf. Decision 002 was approved and clarified on 2026-07-27 (see Index) and is no longer
  in this pending set. Anyone relying on Decision 004 (evaluation protocol) as *approved* should
  confirm current status directly, since this registry is a point-in-time index and the decision
  files are the source of truth.
- `decision_003_temporal_split.md` (unsuffixed, live) and `decision_003_temporal_split_v0_2.md`
  (archived) held byte-identical Decision 003 v0.2 content **before** the 2026-07-27
  governance-repair pass. Only the live file was then given the Decision 010 supersession banner,
  since it is the file named without a version suffix and is therefore treated as the live record.
  The archived `_v0_2` copy was left untouched and remains the unmodified historical snapshot of
  what the live file said before that banner was added.
