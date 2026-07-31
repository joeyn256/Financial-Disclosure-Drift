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
| Accession quotas and caps | [013](Decisions/decision_013_pilot_selection_mechanics.md) §3–4 (counting units); [018](Decisions/decision_018_m23_s5_accession_selection_policy.md) §7 (roles), §8 (caps), §9 (floors), §11–§16 (cross-cutting quotas) | `src/disclosure_drift/sec/accession_selector.py` | `0009`, `0011` | Approved and **implemented** — S5.1 owns the policy functions; accepted at `m2.3-s5-complete` |
| Deterministic objective order (selector policy) | [013](Decisions/decision_013_pilot_selection_mechanics.md) §5 (D10) — order unchanged; [018](Decisions/decision_018_m23_s5_accession_selection_policy.md) §3 (accession-specific reading of terms 2–7) | `src/disclosure_drift/sec/entity_selector.py` (entity terms only); `src/disclosure_drift/sec/accession_selector.py` (joint) | — | Entity-level objective approved and implemented; joint accession-level reading approved and **implemented**, accepted at `m2.3-s5-complete` |
| Evidence rules (levels, resolution, normalization) | [014](Decisions/decision_014_pilot_evidence_and_classification_policy.md); [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §4 | `src/disclosure_drift/sec/entity_selection_store.py` | `0009` | Approved |
| Prohibited pilot uses | [015](Decisions/decision_015_pilot_use_prohibition.md); see also `Docs/leakage_register.md` L19 | — (policy, not a single module) | — | Approved |
| Schema and lifecycle (candidate/selection/manifest tables, state machines) | [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §3, §5 | `src/disclosure_drift/storage/migrations/0009_m23_pilot_schema.sql` | `0009` | Approved; Stage S3 schema exists for both entity and accession tables, but accession tables have no writer yet |
| Hashing (manifest / content-hash contract) | [013](Decisions/decision_013_pilot_selection_mechanics.md) §7 (D12); [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §8; [018](Decisions/decision_018_m23_s5_accession_selection_policy.md) §5 (canonical dashed accession, tie-break formula), §26 (hashing/identity impact); [021](Decisions/decision_021_m23_s6_manifest_construction.md) §§5–10 (the exact manifest and terminal-result preimages) | `src/disclosure_drift/release/hashing.py`; `src/disclosure_drift/sec/accession_selection_store.py` (S5 run identity); `src/disclosure_drift/sec/reserve_selector.py` (reserve signatures and package identity); `src/disclosure_drift/release/pilot_manifest.py` (the manifest and terminal-result preimages) | `0009`, `0013` | Precedent, boundaries, canonical accession representation, S5 run identity, and reserve identity all approved and **implemented**; the **manifest and terminal-result preimages are frozen by Decision 021 v0.5 (`ACCEPTED`, owner approved 2026-07-30) and are now implemented and accepted** at Stage S6 (Decision 023, `M23_STAGE_S6_ACCEPTED_AND_COMPLETE`) |
| Reserves | [013](Decisions/decision_013_pilot_selection_mechanics.md) §6 (D11); [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §7; [020](Decisions/decision_020_m23_s5_4_reserve_architecture.md) (controlling) | `src/disclosure_drift/sec/reserve_selector.py`; persistence in `src/disclosure_drift/sec/accession_selection_store.py` | `0009`, `0012` | Approved and **implemented** — Stage S5.4, owner-accepted 2026-07-30, checkpointed at `m2.3-s5.4-complete`; reserves are not a manifest input before Stage S6 |
| Manifest construction, terminal result identity, and the publication boundary | [013](Decisions/decision_013_pilot_selection_mechanics.md) §§7–8 (D12, D13); [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §§5, 8; [`milestone_2_3_pilot_selection_plan.md`](../Milestones/milestone_2_3_pilot_selection_plan.md) §10 (required manifest contents) and §16 (staged decomposition); [021](Decisions/decision_021_m23_s6_manifest_construction.md) v0.5 (**controlling; ACCEPTED 2026-07-30**) | `src/disclosure_drift/release/pilot_manifest.py` (pure — digests, root, `manifest_id`, document schema, canonical JSON) and `src/disclosure_drift/sec/pilot_manifest_store.py` (persistence, sealing, verification, replay). `src/disclosure_drift/release/manifest.py` is the **general SEC-inventory** release manifest, a distinct artifact that the pilot manifest never reuses | `0009` (`pilot_manifest_versions` schema); `0013` — **eight triggers**, reproducing the Decision 021 §15.1 SQL byte-for-byte | Approval semantics approved (Decision 013 §8); the S6 architecture is frozen by Decision 021 v0.5, **`ACCEPTED`, owner approved 2026-07-30**. Implementation is **Stage S6 — implemented, independently accepted, and checkpointed** at `m2.3-s6-complete` ([023](Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md), `M23_STAGE_S6_ACCEPTED_AND_COMPLETE`, owner approved 2026-07-31). S6 defines and fixture-tests the complete manifest document schema and creates only a `proposed` manifest; the exact real-data instance and CLI output are Stage S9 and owner approval of the root hash is Stage S10 — **none of which is authorized**. **For crosswalk item 46's reserve-rank applicability on a target with no compatible reserve package, [022](Decisions/decision_022_m23_s6_reserve_rank_applicability.md) controls** (`ACCEPTED — OWNER APPROVED 2026-07-31`); Decision 021 controls item 46 in every other respect |
| Quota-policy version | [017](Decisions/decision_017_s4_quota_policy_and_control_evidence.md) | `src/disclosure_drift/pilot_policy.py` (`PILOT_QUOTA_POLICY_VERSION`) | `0010` | Approved and implemented |
| Control structural evidence | [017](Decisions/decision_017_s4_quota_policy_and_control_evidence.md) §3 | `src/disclosure_drift/sec/entity_selector.py` (`CONTROL_QUOTAS`) | `0009`, `0010` | Approved and implemented |

## Decision 018 — approved (Stage S5 accession selection policy)

[Decision 018](Decisions/decision_018_m23_s5_accession_selection_policy.md) is **approved by project
owner** and resolves every topic this section previously listed as pending. The section numbers below
are pointers into that record; **this index supplies no answers of its own** — read the cited section,
and treat a gap found during implementation as a "stop and report" condition, never grounds for
inferring an answer.

| Topic | Decision 018 section |
|---|---|
| Joint objective order (unchanged from Decision 013 §5) and the single-integer evidence term | §3.1–§3.2 |
| Accepted S4 entity behavior preserved (no retrofit) | §3.3 |
| Applicability-aware accession evidence penalty | §3.4 |
| Deterministic accession `selected_order` | §4 |
| Canonical dashed accession form, tie-break formula, loader fail-closed obligations | §5 |
| S4 entity-only draft disposition and the distinct content-derived S5 joint run | §6 |
| Accession roles (control / support / base / stress) | §7 |
| Frozen accession caps | §8 |
| Entity accession floors | §9 |
| Accession families, unresolved parentage, linked-amendment coverage | §10 |
| Control contribution to cross-cutting quotas | §11 |
| Fiscal-year-end-change derivation | §12 |
| Name-change contribution (name-only at M2.3) | §13 |
| Controlled deferral of the unmeasurable difficult-or-nonstandard-package quota | §14, §32 |
| 2009 support / 2010 target pairing | §15 |
| Hard vs deferred vs unsatisfiable quota dispositions | §16 |
| Node limit and failure semantics | §17 |
| Retry prohibition | §18 |
| S5.1 pure core vs S5.2 persistence boundary | §19 |
| Future `PILOT_JOINT_SELECTOR_POLICY_VERSION` and future additive migration `0011` | §20 |
| Future reason codes and existing codes reused | §21 |
| S5.1 / S5.2 / S5.3 / S5.4 / S6 stage boundaries | §22 |
| S5 leakage controls | §23 |

**Decision 018 authorized no implementation of its own.** Stage S5 was subsequently implemented under
separately issued bounded prompts and is now accepted: S5.1, S5.2, and the combined S5.1–S5.3
checkpoint at `m2.3-s5-complete`, and S5.4 at `m2.3-s5.4-complete`. Its §22 also fixes the S6
boundary, which [Decision 021](Decisions/decision_021_m23_s6_manifest_construction.md) now
operationalizes. See the closed contracts
[`m23_s5_1.md`](../Milestones/contracts/m23_s5_1.md), [`m23_s5_2.md`](../Milestones/contracts/m23_s5_2.md),
and [`m23_s5_4.md`](../Milestones/contracts/m23_s5_4.md), the now-closed
[`m23_s6.md`](../Milestones/contracts/m23_s6.md), and `Milestones/STATUS.md` for the current workflow
state.

## Decision 021 v0.5 — ACCEPTED (Stage S6 manifest construction)

[Decision 021](Decisions/decision_021_m23_s6_manifest_construction.md) is at **v0.5 (2026-07-30)**,
**`ACCEPTED`** (owner approved 2026-07-30), and **binding**. v0.2 applied six bounded owner
corrections issued after the focused independent governance review of v0.1; v0.3 applied one further
correction, widening the structural-fingerprint tuple from three columns to five; v0.4 applied two
corrections issued after the focused independent governance review of v0.3 — the exhaustive
item-by-item milestone-plan §10 crosswalk (§13.2.1, 81 atomic items, zero unclassified) and the
growth of migration `0013` from four triggers to five; and **v0.5 applies one owner ruling issued
after the focused independent governance review of v0.4, which also returned
`REQUIRES_OWNER_CLARIFICATION`** — migration `0013` grows from five triggers to **eight**, adding a
replacement guard, an unconditional delete guard, and an identity guard on `pilot_selection_runs`,
and §15.5 now states the append-once and identity guarantee without qualification. **v0.1, v0.3, and
v0.4 were each independently reviewed and none was approved; v0.2 was never independently reviewed**;
the focused independent governance review of v0.5 returned
`ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL` with no governance blockers, and the owner approved it
the same day. Its one editorial correction — **74 original bullets producing 81 atomic
requirements** — touches §13.2.1's explanatory arithmetic only. §19.11, the v0.4 open finding, is
**closed**. **Approval was not implementation**: separately issued bounded S6 implementation prompts
were required, were issued, and were exercised, and **Stage S6 is now implemented and accepted**
([Decision 023](Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md)).
The section numbers below are pointers into that record; this index supplies no answers of its own.

| Topic | Decision 021 section |
|---|---|
| Stage S6 scope and what it does not authorize | §4 |
| Hashing infrastructure and the mandatory reuse of `release/hashing.py` | §5 |
| `selection_result_sha256` — canonical preimage and exclusions | §6 |
| The four terminal component boundaries (entities, accessions, quota report, reserves) | §7 |
| Source-observation preimage, **the five-column structural-fingerprint partition rule**, and **the complete column classification of both census tables** | §8.1 |
| Candidate-table and quota-definition preimages | §8.2, §8.3 |
| **The eleven-field selector-policy preimage**, its six required explicit arguments, and the `leakage_attestation` literal | §8.4, §8.4.1 |
| `root_manifest_sha256` | §9 |
| `manifest_id` derivation, confirmed at review | §9.1 |
| **Six-field manifest-identity immutability after insertion** | §9.2 |
| Circularity exclusions | §10 |
| **Commitment closure — what the root commits versus what `manifest_id` commits** | §10.1 |
| Manifest lifecycle, the proposed-only boundary, eligibility, and transactions | §11 |
| Reconstruction and replay, including document verification | §12 |
| **The complete pilot-manifest document contract** — milestone plan §10 operationalized, thirteen mandatory blocks, the no-unbound-field rule, the operational envelope, encoding | §13 |
| **The exhaustive item-by-item milestone-plan §10 crosswalk** — 81 atomic items, four categories, frozen counts, zero unclassified | §13.2.1 |
| `manifest_state` as a fixed literal committed through the schema version | §13.2.2 |
| S4 exclusion and S5 authority | §14 |
| Schema ruling and the complete frozen **eight-block** migration-`0013` SQL, its nine digests, and verification | §15 |
| **The append-once and identity guarantee** — nine clauses across every direct SQLite write path | §15.5 |
| No new reason code, projection-recovery writer, or policy constant; **the CLI narrowing of milestone plan §16** | §16 |
| **The Stage S7–S10 boundary** and the Milestone 2 review timing (after S10) | §17 |
| Accepted limitations, and the **§19.11 finding — CLOSED at v0.5** — on `pilot_selection_runs` row replacement, deletion, and identity mutation | §19 |
| Test obligations, and the foreseeable bounded test-fixture consequence | §20 |
| Implementation stop conditions | §21 |
| Checkpoint boundary (`m2.3-s6-complete`) | §22 |

**One point of Decision 021 is clarified by a later record.** For **whether crosswalk item 46's
reserve rank must be rendered for a selected target that has no compatible reserve package**,
[Decision 022](Decisions/decision_022_m23_s6_reserve_rank_applicability.md) controls. Decision 021
remains controlling for everything else about item 46.

## Decision 022 — ACCEPTED (Stage S6 reserve-rank applicability)

[Decision 022](Decisions/decision_022_m23_s6_reserve_rank_applicability.md) is
**`ACCEPTED — OWNER APPROVED 2026-07-31`** and **binding**. It is an applicability clarification of
Decision 021 §13.2.1 item 46 and **supersedes and amends nothing**: Decision 021 remains `ACCEPTED`
and otherwise unchanged.

A fresh independent S6 implementation audit found that a lawful, accepted, feasible, sealed S5 run
with **zero compatible reserve packages** — every selected target instead carrying one persisted
`REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition, the shape Decision 020 §7.1 rules nonblocking and
migration `0012` accepts as complete — passed all seven Decision 021 §11.2 eligibility conditions and
sealed normally, but was then refused at document verification because item 46's
`reserves.packages[].reserve_rank` leaf cannot exist with zero packages. The audit stopped under
Decision 021 §§21 and 13.3 and returned `REQUIRES_OWNER_CLARIFICATION`.

| Topic | Decision 022 section |
|---|---|
| The conflict between item 46 and Decision 021 §11.2, and the accepted run shape that exposes it | §1 |
| **The owner ruling, recorded verbatim — ten clauses** | §2 |
| Why the applicability rule was adopted, and why zero-package ineligibility and a placeholder rank were **rejected** | §3 |
| Why no crosswalk reclassification is required, and the frozen counts restated | §4 |
| **Item 46 versus item 70** — per-package rank against per-target total coverage | §5 |
| The nonchange guarantees | §6 |
| Implementation consequences and the bounded authorized paths | §7 |
| Test consequences, including the dead `with_reserve=False` fixture path | §8 |
| The fresh-independent-rereview requirement before acceptance | §9 |

## Decision 023 — ACCEPTED (Stage S6 acceptance and path ratification)

[Decision 023](Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md) is
**`ACCEPTED — OWNER APPROVED 2026-07-31`** and **binding**. It **supersedes and amends nothing**:
Decisions 021 and 022 both remain `ACCEPTED`, unchanged, and controlling — 021 for the S6
architecture, 022 for crosswalk item-46 applicability. **Decision 023 adds acceptance, ratification,
accepted limitations, and checkpoint authorization; it adds no architecture and reopens no ruling.**

| Topic | Decision 023 section |
|---|---|
| Why the record exists — acceptance, a path-authorization gap, and four residual observations | §1 |
| The independent acceptance result, `ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING` | §2 |
| **Formal acceptance and the eighteen accepted S6 capabilities**; outcome `M23_STAGE_S6_ACCEPTED_AND_COMPLETE` | §3 |
| **Ratification of the three forced-consequence test paths**, the reason for each, and the basis | §4, §4.1 |
| What the ratification does **not** do — three named paths, not a general widening | §4.2 |
| What Decisions 021 and 022 retain | §5 |
| **The nine invariance confirmations** — crosswalk, totals, preimages, digests, triggers, migrations, S4, S5, no S7/M3 authority | §6 |
| **Accepted nonblocking limitations O1–O4** | §7 |
| **Checkpoint authorization** — one commit, one push, the annotated tag `m2.3-s6-complete`, one tag push | §8 |
| **The forward boundary** — no S7, no live SEC operation, no Milestone 3; boundary reorganization and the integrated Milestone 2 audit deferred; **Milestone 2 not closed** | §9 |

**Which record answers which S6 question.** For the architecture — preimages, the root, identity,
the document contract, the crosswalk, migration `0013` — read **Decision 021**. For whether item
46's reserve rank must be rendered for a target with no compatible reserve package, read
**Decision 022**. For whether the stage is accepted, which paths the delivered change set
legitimately contains, what limitations the project has agreed to live with, and what the checkpoint
authorizes, read **Decision 023**.

## Full chronological registry

For every decision's exact status, supersession relationships, and date, use
[`Docs/Decisions/decision_registry.md`](Decisions/decision_registry.md) — it is the authoritative,
chronological record. This file is a topic-oriented convenience index over the same underlying
decisions and never overrides it.
