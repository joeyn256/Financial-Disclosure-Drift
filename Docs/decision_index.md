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
| Manifest construction, terminal result identity, and the publication boundary | [013](Decisions/decision_013_pilot_selection_mechanics.md) §§7–8 (D12, D13); [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §§5, 8; [`milestone_2_3_pilot_selection_plan.md`](../Milestones/milestone_2_3_pilot_selection_plan.md) §10 (required manifest contents) and §16 (staged decomposition); [021](Decisions/decision_021_m23_s6_manifest_construction.md) v0.5 (**controlling; ACCEPTED 2026-07-30**) | `src/disclosure_drift/release/pilot_manifest.py` (pure — digests, root, `manifest_id`, document schema, canonical JSON) and `src/disclosure_drift/sec/pilot_manifest_store.py` (persistence, sealing, verification, replay). `src/disclosure_drift/release/manifest.py` is the **general SEC-inventory** release manifest, a distinct artifact that the pilot manifest never reuses | `0009` (`pilot_manifest_versions` schema); `0013` — **eight triggers**, reproducing the Decision 021 §15.1 SQL byte-for-byte | Approval semantics approved (Decision 013 §8); the S6 architecture is frozen by Decision 021 v0.5, **`ACCEPTED`, owner approved 2026-07-30**. Implementation is **Stage S6 — implemented, independently accepted, and checkpointed** at `m2.3-s6-complete` ([023](Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md), `M23_STAGE_S6_ACCEPTED_AND_COMPLETE`, owner approved 2026-07-31). S6 defines and fixture-tests the complete manifest document schema and creates only a `proposed` manifest; the exact real-data instance and CLI output are **Milestone 3 phase M3.3** and owner approval of the root hash is **M3.4** ([024](Decisions/decision_024_m2_m3_boundary_governance.md) §5.1; formerly Stages S9 and S10) — **neither of which is authorized, and neither has begun**. **For crosswalk item 46's reserve-rank applicability on a target with no compatible reserve package, [022](Decisions/decision_022_m23_s6_reserve_rank_applicability.md) controls** (`ACCEPTED — OWNER APPROVED 2026-07-31`); Decision 021 controls item 46 in every other respect |
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
| **The Stage S7–S10 boundary** and the review timing after it — the scope definitions [024](Decisions/decision_024_m2_m3_boundary_governance.md) §5.1 renames to **M3.1–M3.4** without altering their substance | §17 |
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

## Decision 024 — ACCEPTED (Milestone 2 boundary and Milestone 3 obligation transfer)

[Decision 024](Decisions/decision_024_m2_m3_boundary_governance.md) is
**`ACCEPTED — OWNER APPROVED 2026-07-31`** and **binding**. It **supersedes and amends nothing**:
Decisions 021, 022, and 023 all remain `ACCEPTED`, unchanged, and controlling for what they govern.
It is a **boundary and naming** record — **governance only, granting no implementation authority**.
Formal outcome: **`M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED`**.

| Topic | Decision 024 section |
|---|---|
| Why the record exists — the boundary the stopped integrated audit required | §1 |
| **Accepted S6 is the end of Milestone 2 implementation**, with the checkpoint identifiers | §2 |
| **The final scope of Milestone 2** — M2.1, M2.2, and M2.3 through accepted S6 | §3 |
| **Milestone 2 is not closed** *(as Decision 024 stood — the four steps §4 named are now complete and closure is recorded in Decision 026)* — open only for the audit, bounded correction, rereview, and closeout | §4 |
| **The obligation transfer** and the **M3.1–M3.5 phase map** | §5, §5.1 |
| **The traceability table** — per phase: inherited gates, prohibitions, owner decision, validation, implementation authorization | §5.2 |
| Confirmation that every former obligation is preserved intact | §5.3 |
| **What Milestone 3 inherits** — frozen definitions, temporal authority, identifiers, SEC controls, data-source prohibitions, leakage controls, S4/S5/S6, Decisions 013–024, accepted limitations | §6 |
| **Authority separation** — which of 021 / 022 / 023 / 024 controls what | §7 |
| **No implementation authority**; assignment to Milestone 3 is not authorization; the five entry conditions | §8 |
| **What happens next, in order** — audit, correction, closeout, then planning | §9 |
| Negative confirmations — nothing began, nothing live, nothing real, nothing approved, nothing published | §10 |
| What this record does not change | §11 |
| Checkpoint authorization — one commit, one push, **no tag** | §13 |

**Decision 024 remains controlling for the Milestone 2 → Milestone 3 obligation transfer**, and its
§§2, 3, 5–8, and 11 stand exactly as approved. Only its §§4 and 9 sequencing has been *completed*
rather than changed: the audit, the bounded corrections, and the rereviews all ran, and
**Milestone 2 is now formally closed** by Decision 026. Decision 024 §8's five entry conditions for
Milestone 3 implementation are **unaffected** and still apply in full.

**Where the former S7–S10 obligations went.** Decision 021 §17 defined them as Stages S7–S10 and
that text stands as written; Decision 024 §5.1 renames them without altering their substance. Read
Decision 021 §17 for the scope of each, and Decision 024 §5.2 for what each carries.

| Former | Now | One-line scope |
|---|---|---|
| S7 | **M3.1** | Controlled live-operation readiness; Gate F; no live access before every gate passes |
| S8 | **M3.2** | Controlled **metadata-only** SEC acquisition; Gate H; no filing body, CompanyFacts, Frames, outcome, or publication |
| S9 | **M3.3** | Frozen real pilot snapshot, deterministic execution, the exact real-data manifest and the CLI output deferred from S6, and the exact root hash — **no approval, no publication** |
| S10 | **M3.4** | **Explicit** owner approval of the exact root hash; no implied approval |
| — | **M3.5** | Integrated real-pilot acceptance and Milestone 3 closeout (**new at Decision 024**) |

## Decision 025 — ACCEPTED (integrated-audit documentation corrections)

[Decision 025](Decisions/decision_025_integrated_audit_documentation_corrections.md) is
**`ACCEPTED — OWNER APPROVED 2026-07-31`**. It records the final integrated Milestones 1–2 audit
result (`REQUIRES_BOUNDED_INTEGRATED_FIXES`), the nine categories confirmed
`INTEGRATED_ACCEPTANCE_CONFIRMED`, the single `PROJECT_DOCUMENTATION_CLASSIFICATION:
REQUIRES_BOUNDED_FIX`, the authorized documentation corrections, and the independence disclosure and
its handoff. Formal outcome **`INTEGRATED_AUDIT_DOCUMENTATION_CORRECTIONS_AUTHORIZED`**.
**Documentation and governance recording only — it grants no implementation authority and changes no
schema, migration, code, test, configuration, methodology, hash, or accepted decision outcome.**

| Topic | Decision 025 section |
|---|---|
| The audit result and why the record exists | §1 |
| The nine confirmed classifications and the evidence reproduced independently | §2 |
| The single bounded documentation classification | §3 |
| **The documentation defect** — the data dictionary's declared scope versus its content | §4 |
| **The navigation defect** — the deviation register was not clearly reachable | §5 |
| The authorized corrections | §6 |
| What the correction does not change | §7 |
| **The independence disclosure** and why it is recorded rather than absorbed | §8 |
| **The required sequence** — correction, fresh verification, closeout, then Milestone 3 planning | §9 |
| Checkpoint authorization — one commit, one push, **no tag** | §11 |

**That sequence is now complete.** The fresh verification ran, the bounded fixes it required were
made, the fresh independent rereview of those fixes passed, and formal closeout is recorded in
**Decision 026** below.

## Decision 026 — ACCEPTED (final closeout of Milestones 0, 1, and 2)

[Decision 026](Decisions/decision_026_milestones_0_1_2_final_closeout.md) is
**`ACCEPTED — OWNER APPROVED 2026-07-31`** and **binding**. It **supersedes and amends nothing**:
Decisions 001–025 all retain the authority they already hold, and **Decision 026 supersedes no
methodology record**. It is a **closeout** record — **governance only, granting no Milestone 3
implementation authority**. Formal outcome:
**`MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`**.

| Topic | Decision 026 section |
|---|---|
| Why the record exists — closure must bind, and a completion narrative does not | §1 |
| **The closeout baseline** — commit `65a57f40…`, branch `main`, `HEAD == origin/main`, clean tree, chain through `0013` | §2 |
| **The full review chain** — stage reviews, S6 acceptance, Decisions 023–025, the integrated audit, the bounded correction, the first independent verification, the final bounded fix, the final fresh rereview, and the explicit Milestone 0 standalone audit | §3 |
| **The final rereview outcome** `ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT` | §4 |
| **The sixteen final classifications**, recorded verbatim | §5 |
| **Formal closeout of Milestone 0** — research question, novelty review, preregistration, frozen cohorts, outcome cutoffs, seed `20260725`, leakage register, deviation register and D001, governance foundation | §6 |
| **Formal closeout of Milestone 1** — packaging, configuration, cohort mirror enforcement, CLI and exit codes, offline safety, secret and hygiene controls | §7 |
| **Formal closeout of Milestone 2.1** — offline SEC policy, identifiers and temporal policy, response and rate-limit policy, storage/provenance/schema-drift/release/forecast boundaries, CompanyFacts-disabled and Frames-prohibited | §8 |
| **Formal closeout of Milestone 2.2** — live-metadata readiness, SEC identity, transport isolation, request governance, raw-store provenance, offline test and CI boundaries | §9 |
| **Formal closeout of Milestone 2.3 through Stage S6** — candidate and snapshot identity, selection, reserves and dispositions, persistence, reconstruction and replay, sealing, manifest construction, canonical serialization, lifecycle enforcement, verification and atomicity, accepted limitations | §10 |
| **Completion confirmations** — implementation complete, migrations immutable, chain ends at `0013`, suite **2324 passed / 2 skipped**, all checks passed, no blocker | §11 |
| **The inherited limitations register stays ACTIVE** — nothing is closed or erased by closure; **O1 remains a future owner-ruling condition** | §12 |
| The nonblocking `pilot_reserves` PK-superset UNIQUE presentation observation — no correction required | §13 |
| **The formal outcome** `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED` | §14 |
| **Tag authorization** — the three annotated tags `m0-complete`, `m1-complete`, `m2-complete` | §15 |
| Existing implementation-stage tags remain immutable; the completion tags supplement them | §16 |
| **Milestone 3 becomes the next planning phase**, and **the next authorized action is `MILESTONE_3_MASTER_PLANNING`** | §§17–18 |
| **What Milestone 3 master planning may do** — define M3.1–M3.5, map inherited gates, the operator runbook, evidence packets, offline rehearsal requirements, proposed contracts and decisions | §19 |
| **What it may not do** — implement, create an authorizing contract, enable network access, acquire metadata, create a snapshot, run a pilot, construct a manifest, approve a root, publish | §20 |
| **No Milestone 3 implementation authority** — closure satisfies only Decision 024 §8's precondition; all five entry conditions still apply | §21 |
| Checkpoint authorization — one commit, one push, three annotated tags, one tag push | §22 |
| Negative confirmations and what this record does not change | §§23–24 |

**Which record answers which closeout question.** For whether a milestone is closed, what closure
covers, and what is authorized next, read **Decision 026**. For where Milestone 2 implementation ends
and where the former S7–S10 obligations went, read **Decision 024** — still controlling. For the
integrated audit's findings and the documentation corrections, read **Decision 025** — still
controlling. For the S6 architecture, item-46 applicability, and S6 acceptance, read **Decisions 021,
022, and 023** respectively.

## Decision 027 v0.2 — ACCEPTED (Milestone 3 master plan and operational readiness)

[Decision 027](Decisions/decision_027_m3_master_plan_and_operational_readiness.md) is at **v0.2
(2026-07-31)**, **`ACCEPTED — OWNER APPROVED 2026-07-31`**, and **binding**. **It has been accepted
since v0.1; v0.2 does not change that.** v0.2 applies eleven bounded owner corrections issued after
the required independent review of v0.1, recorded in its **§0 revision history**, and supersedes only
the affected v0.1 operational-planning language. It **supersedes and amends nothing**:
Decisions 001–026 all retain the authority they already hold, and **Decision 024 remains controlling
for the M2 → M3 obligation transfer** while **Decision 026 remains controlling for the Milestones 0–2
closeout**. It is a **planning and operational-readiness** record — **governance and documentation
only, granting no Milestone 3 implementation authority**. Formal outcome:
**`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`**.

| Topic | Decision 027 section |
|---|---|
| **The v0.2 revision history — the eleven independent-review corrections** | **§0** |
| Why the record exists — Milestone 3 is the first phase whose actions cannot be undone | §1 |
| **The exact Milestones 0–2 closeout baseline** — closeout commit, tag targets, migration state | §2 |
| **Decision 024 remains controlling** for the M2 → M3 obligation transfer | §3 |
| **Decision 026 remains controlling** for the Milestones 0–2 closeout | §4 |
| **The exact M3.1–M3.5 phase map**, with network permission and completion token per phase | §5 |
| **The frozen internal subdivisions** — M3.1A/B, M3.2A/B, M3.3A/B, M3.4A/B; no new milestone, no new phase, no tag for an internal part | §6 |
| M3.1 rehearses **acquisition only**; no scenario in a phase lacking its production path | §6.1 |
| M3.2's **two sequential acquisition windows**, the between-windows freeze and derivation, and the second owner approval | §6.2 |
| M3.3A builder and execution rehearsal, then M3.3B real execution | §6.3 |
| M3.4 **always contracted, never documentary**; manual SQL prohibited | §6.4 |
| **The operator-runbook requirement** — every command labelled, none overstated | §7 |
| **The mandatory offline rehearsal before the first SEC request** | §8 |
| **The execution-receipt requirement for every live command** | §9 |
| **The frozen eight-template operational set** | §10 |
| **The two-layer evidence model** — public index, private evidence root | §10.1 |
| **Deterministic root re-derivation** — regeneration alone never changes the root | §10.2 |
| **The Milestone 3 limitations register**, seeded and closing nothing | §11 |
| **The sequential model and validation policy** — Opus Max, Sonnet High/Max, no Haiku on the critical path | §12 |
| **Commit and tag policy** — one implementation commit per phase; frozen future tag names | §13 |
| **The focused independent-review policy** — no repeated broad audits, no self-review | §14 |
| **Request-volume values may not be invented, and none is frozen** | §15 |
| **M3-L12 planner-v2 correction** (`CURRENT_PLANNER_DISCREPANCY`) — owner ruling recorded by Decision 028 §4; implementation and acceptance still block Gate F | §15.1 |
| **How a deferred count is resolved** — `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` | §15.2 |
| **Maximum physical attempts is derived from the implemented state machine**, not asserted | §16 |
| **Operational receipts are outside the accepted S5 and S6 identity graphs** | §17 |
| **Nothing operational may contaminate a governed identity** | §18 |
| **No identity, secret, or restricted payload in a receipt** | §19 |
| **No Milestone 3 implementation authority is granted** | §20 |
| Formal outcome | §21 |
| Checkpoint authorization — one commit, one push, **no tag** | §22 |
| **The next authorized action — `INDEPENDENT_M3_MASTER_PLAN_REREVIEW`** | §23 |
| Only after that rereview may the bounded M3.1 contract be drafted | §24 |
| Negative confirmations, and what this record does not change | §§25–26 |

**Where the Milestone 3 planning artifacts live.**

| Artifact | Path |
|---|---|
| The master plan — five phases, 36 fields each, plus the future-contract requirements | [`Milestones/milestone_03_master_plan.md`](../Milestones/milestone_03_master_plan.md) |
| The Mac operator runbook | [`Docs/m3/operator_runbook.md`](m3/operator_runbook.md) |
| The offline-rehearsal specification, twenty scenarios | [`Docs/m3/offline_rehearsal_spec.md`](m3/offline_rehearsal_spec.md) |
| The execution-receipt specification | [`Docs/m3/execution_receipt_spec.md`](m3/execution_receipt_spec.md) |
| The Milestone 3 limitations register | [`Docs/m3/limitations_register.md`](m3/limitations_register.md) |
| Public evidence index | [`Docs/m3/templates/evidence_index.md`](m3/templates/evidence_index.md) |
| Request budget | [`Docs/m3/templates/request_budget.md`](m3/templates/request_budget.md) |
| Gate F checklist | [`Docs/m3/templates/gate_f_checklist.md`](m3/templates/gate_f_checklist.md) |
| Gate H checklist | [`Docs/m3/templates/gate_h_checklist.md`](m3/templates/gate_h_checklist.md) |
| Schema-drift incident | [`Docs/m3/templates/schema_drift_incident.md`](m3/templates/schema_drift_incident.md) |
| Interrupted-run recovery | [`Docs/m3/templates/interrupted_run_recovery.md`](m3/templates/interrupted_run_recovery.md) |
| Real-snapshot evidence packet | [`Docs/m3/templates/real_snapshot_evidence_packet.md`](m3/templates/real_snapshot_evidence_packet.md) |
| Root-hash approval packet | [`Docs/m3/templates/root_hash_approval_packet.md`](m3/templates/root_hash_approval_packet.md) |

**What the planning pack does not claim.** No Gate F has passed. **Neither offline rehearsal has been
run.** No live acquisition occurred. No Gate H has passed. No real snapshot, selection, manifest, or
approval exists. **The M3.1 contract is accepted with `IMPLEMENTATION_AUTHORIZATION: YES`, and its
implementation exists in the tree without being accepted; Decision 029 code remediation is
implemented and the disposable-clone validation run on the corrected tree is complete, and a frozen
commit and the first durable §17 review remain outstanding.**

**D023-O1 remains the sole unresolved owner-ruling condition** and is referred only if a real run
reaches it. Accepted Decision 028 records the owner rulings for **M3-L11** and **M3-L12**, preserving
Decision 013 and requiring the planner-v2 and private-evidence protections. Those entries remain
active until implementation, tests, independent acceptance, and checkpoint; Gate F cannot pass
while M3-L12 remains active.

## Decision 028 — ACCEPTED (Milestone 3.1 readiness corrections and owner rulings)

[Decision 028](Decisions/decision_028_m3_1_readiness_corrections.md) is **`ACCEPTED — OWNER APPROVED
2026-08-01`** after `INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`. It records the bounded correction
required after the independent Decision 027 v0.2 rereview returned `NEEDS_CORRECTION`. It is binding
for what it governs and grants no implementation, network, data, approval, or publication authority.

| Topic | Decision 028 section |
|---|---|
| Why the correction record is required and the verified `c91af08` baseline | §§1–2 |
| Decision 013 and Decision 024 remain unchanged and controlling | §3 |
| **M3-L12 is an inherited implementation defect; exact-quarter-end total order and `quarterly-index-instances/2.0`** | §4 |
| **The corrected A1–A12 matrix** | §5 |
| New future reason codes `SEC_REQUEST_CEILING_EXHAUSTED` and `SEC_ACQUISITION_INTERRUPTED` | §6 |
| **Ceiling equality:** `actual <= ceiling`, with completeness separately required | §7 |
| M3.1 read-only recovery inspection; M3.2 repair and resume | §8 |
| **Execution receipt `m3-execution-receipt/2.0` before the first receipt exists** | §9 |
| Correct request-budget arithmetic and rate-limiter spacing floor | §10 |
| Three-layer M3-L11 protection | §11 |
| Future implementation boundary and required independent rereview | §§12–13 |
| Acceptance/checkpoint sequence and next action | §§14–15 |
| Negative confirmations | §16 |

Decision 028 narrowly supersedes the affected Decision 027 operational language. It does not amend
Decision 013 or Decision 024, reopen Milestone 2, rewrite any historical v1 hash, or grant
implementation authority. Its rereview passed and it is accepted. The separate M3.1 contract is now
**accepted** with `IMPLEMENTATION_AUTHORIZATION: YES`, and `INDEPENDENT_M3_1_CONTRACT_REVIEW` is
discharged.

[Decision 029](Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md) —
`ACCEPTED — OWNER APPROVED 2026-08-02` — is the bounded M3.1 remediation record. It narrowly
supersedes **exactly two** Decision 028 clauses: §5's A6 language, to permit a rehearsal-only
manifest-resolution fixture that grants no retrieval authority; and §6's word "exactly" with §12's
closed-delta wording, to register one code, `OFFLINE_REHEARSAL_SCENARIO_MISMATCH` (category
`integrity`, `blocks_release=true`, `requires_manual_review=false`). It rules that **a zero
`U(route)` never waives the independent `A_reachable` witness**, requires **one realizable full-path
witness per route** in place of three separately measured terms, requires the M3.1A token to gate on
all four of `passed`, `complete`, `a_reachable_agrees`, and `a_reachable_fully_tested`, and records
that **no durable §17 review artifact exists and none covers the current tree**. It changes no
receipt schema field or digest preimage, creates no migration, and grants no network authority. The
Decision 029 §11 code remediation is implemented and the disposable-clone validation run on the
corrected tree is complete; the next action is a frozen commit and the **first durable §17 review**,
which reproduces and records that validation.

## Deviation register — where deviations are recorded

**[`Docs/preregistration.md`](preregistration.md) §25 is the canonical preregistration deviation
register.** It states the fields every deviation must record and holds the register itself.

- **Deviation D001** is currently the only entry: the cohort-assignment date-source rule and
  point-in-time boundary frozen by
  [Decision 010](Decisions/decision_010_temporal_availability_and_cohort_assignment.md), recorded as
  prospective, outcome-blind, and made before any filing was retrieved.
- **Accepted decision records may explain, justify, or approve a deviation**, and several do — but a
  decision record is not itself the register.
- **The preregistration section remains the register of record** unless a later accepted decision
  explicitly replaces it. None does.

`make cohorts` prints §25 among the governing records for the frozen cohort definitions, so the
register is reachable from the CLI as well as from this index.

## Full chronological registry

For every decision's exact status, supersession relationships, and date, use
[`Docs/Decisions/decision_registry.md`](Decisions/decision_registry.md) — it is the authoritative,
chronological record. This file is a topic-oriented convenience index over the same underlying
decisions and never overrides it.
