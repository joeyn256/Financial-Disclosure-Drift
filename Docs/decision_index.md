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
| SEC universe, canonical CIK identity | [007](Decisions/decision_007_sec_universe.md); [062](Decisions/decision_062_m3_2_terminal_failure_and_sic_endpoint_remediation.md) §5 (controls the `sec_sic_code_list` exact path and the source-registry version) | `src/disclosure_drift/sec/identifiers.py`, `src/disclosure_drift/sec/sources.py`, `src/disclosure_drift/sec/source_registry.py`, `src/disclosure_drift/sec/urls.py` | `0001`, `0003` | Approved; registry version `m2.2-source-registry/1.1` |
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

**What the planning pack did not claim, as at Decision 028 — historical.** No Gate F has passed.
**Neither offline rehearsal has been run.** No live acquisition occurred. No Gate H has passed. No
real snapshot, selection, manifest, or approval exists. **The M3.1 contract is accepted with
`IMPLEMENTATION_AUTHORIZATION: YES`, and its implementation exists in the tree without being
accepted; Decision 029 code remediation is implemented and the disposable-clone validation run on
the corrected tree is complete, and a frozen commit and the first durable §17 review remain
outstanding.**

**Current state.** Every clause in that paragraph except the last sentence has since been overtaken:
M3.1 is accepted and complete (Decision 031), Gate F passed, the A1–A12 rehearsal ran and passed,
M3.2A live acquisition completed, **Gate H is passed and owner-accepted**, and Milestone 3.2 is
complete and owner-accepted
([Decision 065](Decisions/decision_065_m3_2_final_acceptance_and_closeout.md), 2026-08-13). What
still holds: **no real snapshot, selection, manifest, or approval exists**, the M3.3A execution
rehearsal (E1–E8) had not been run, and M3.3 had not begun. **That sentence is historical as at its own record.** M3.3-I/R is authorized by accepted Decision 070, is implemented and rehearsed, and the E1–E8 rehearsal passes — while **M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 all remain separate owner gates and no real execution is authorized**.

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
— **as the state at the time it was written** — that no durable §17 review artifact existed. It
changes no receipt schema field or digest preimage, creates no migration, and grants no network
authority. That §17 review has since been produced and passed, and M3.1 is owner-accepted by
Decision 031; **`Milestones/STATUS.md` carries the live state**, and this index never does.

## Decisions 030–042 — M3.1 acceptance, the M3.2 contract, and staged T2 implementation

Brought current under [Decision 043](Decisions/decision_043_m3_2_g1_navigation_workflow_repair_authorization.md)
§§5 and 7, which is the explicit path authorization this file previously lacked. The rows are
**pointers only** — each states one decision's narrow topic and its formal outcome, and nothing
here approves, narrows, or amends anything. For existence and approval status use
[`Docs/Decisions/decision_registry.md`](Decisions/decision_registry.md); for current workflow state
use [`Milestones/STATUS.md`](../Milestones/STATUS.md).

| Decision | Date | Narrow topic | Formal outcome |
|---|---|---|---|
| [030](Decisions/decision_030_gate_f_step_12_owner_rulings_and_hygiene_remediation.md) | 2026-08-03 | Gate F step-12 owner rulings; the one hygiene blocker resolved by a proven non-substantive redaction, leaving the §17 review verdict unchanged | `GATE_F_STEP_12_OWNER_RULINGS_AND_HYGIENE_REMEDIATION_ACCEPTED` |
| [031](Decisions/decision_031_m3_1_acceptance.md) | 2026-08-03 | **Milestone 3.1 acceptance** — the frozen M3.1 implementation, the step-14 independent review, and the evidence bindings including the owner-approved hard request ceiling **801** | `M3_1_ACCEPTED_AND_COMPLETE` |
| [032](Decisions/decision_032_m3_2_contract_corrections.md) | 2026-08-04 | Adopts the independent M3.2 contract review's findings F1–F7, authorizes the bounded contract correction, and requires a fresh no-subagent rereview before acceptance | `M3_2_CONTRACT_CORRECTIONS_RECORDED` |
| [033](Decisions/decision_033_m3_2_correction_pass_adjudication.md) | 2026-08-04 | Adjudicates that correction pass; restores `Docs/decision_index.md` to its pre-edit bytes as out-of-envelope and records the resulting navigation staleness as an open item needing its own path authorization (**Decision 043 §5 is that authorization**) | `M3_2_CORRECTION_PASS_ADJUDICATED_AND_CLEANED_UP` |
| [034](Decisions/decision_034_m3_2_contract_acceptance.md) | 2026-08-04 | **Accepts the corrected M3.2 contract unchanged at T1.** T1 grants no later gate | `M3_2_CONTRACT_ACCEPTED_AT_T1` |
| [035](Decisions/decision_035_m3_2_t2_staged_implementation_authorization.md) | 2026-08-04 | **Staged T2 implementation authority, stage T2.1 only**; accepts the T2 packet (revision v2) as the controlling implementation plan; fixes the fifteen-path maximum T2 envelope and amends contract §22 to the T2.1–T2.6 cadence | `M3_2_T2_STAGED_IMPLEMENTATION_AUTHORIZED` |
| [036](Decisions/decision_036_m3_2_t2_1_stage_completion.md) | 2026-08-04 | Accepts and publishes **stage T2.1** — the configuration and fail-closed command-authority layer | `M3_2_T2_1_ACCEPTED_AND_PUBLISHED` |
| [037](Decisions/decision_037_m3_2_remaining_stage_combination.md) | 2026-08-04 | Consolidates the remaining work into **combined T2.2–T2.3, separate T2.4, and combined T2.5–T2.6**, and makes the T2.5–T2.6 commit the implementation-freeze candidate for the independent T3 review | `M3_2_REMAINING_STAGES_COMBINED` |
| [038](Decisions/decision_038_m3_2_t2_2_t2_3_path_envelope_amendment.md) | 2026-08-05 | Narrow path-envelope amendment **for combined T2.2–T2.3 only**, adding exactly `sec/observation_catalog.py` and `tests/unit/test_observation_catalog.py`, bound to that candidate tree; carries into no later stage | `M3_2_T2_2_T2_3_PATH_ENVELOPE_AMENDMENT_RECORDED` |
| [039](Decisions/decision_039_m3_2_t2_2_t2_3_stage_acceptance.md) | 2026-08-06 | Accepts and publishes **combined stage T2.2–T2.3** — catalog, immutable storage, and the acquisition engine | `M3_2_T2_2_T2_3_ACCEPTED_AND_COMPLETE` |
| [040](Decisions/decision_040_m3_2_t2_4_implementation_authorization.md) | 2026-08-06 | Authorizes **stage T2.4** (recovery, reconciliation, resume boundaries, drift control) in four subphases; approves exactly one new reason code `SOURCE_REQUIRED_OBJECT_UNAVAILABLE`; fixes `NO_NEW_MIGRATION_REQUIRED` and `NO_RECEIPT_SCHEMA_CHANGE_REQUIRED` | `M3_2_T2_4_IMPLEMENTATION_AUTHORIZED` |
| [041](Decisions/decision_041_m3_2_t2_4_recovery_state_primitive_authority.md) | 2026-08-06 | T2.4 correction authority: amends that envelope from eight paths to exactly ten, authorizes the two additive primitives `open_recovery_state` and `resolve_recovery_state`, and fixes the write-ahead sequence and failure outcomes | `M3_2_T2_4_RECOVERY_STATE_PRIMITIVE_AUTHORITY_RECORDED` |
| [042](Decisions/decision_042_m3_2_t2_4_acceptance_and_publication.md) | 2026-08-06 | Accepts and publishes **stage T2.4**. Discloses that no T2.4 rereview artifact file exists and expressly creates, reconstructs, and back-dates none | `M3_2_T2_4_ACCEPTED_AND_PUBLISHED` |

**Which record controls what, at a glance.** For the M3.2 contract's meaning read the accepted
contract itself, [`Milestones/contracts/m3_2.md`](../Milestones/contracts/m3_2.md), with Decision
034 for its acceptance. For *what a stage was allowed to touch* read the authorizing decision
(035 for T2.1; 035 as amended by 038 for T2.2–T2.3; 040 as amended by 041 for T2.4) — never the
acceptance decision, which records the outcome rather than the envelope. **Stage acceptance is not
overall M3.2 T3 implementation acceptance** — a distinction that was live while the stages ran.
**Both have since occurred:** combined T2.5–T2.6 was authorized (Decision 045) and its corrected
freeze candidate was accepted and published as T3 (Decision 046, 2026-08-07), and Milestone 3.2 as a
whole is now complete and owner-accepted
([Decision 065](Decisions/decision_065_m3_2_final_acceptance_and_closeout.md), 2026-08-13).

## Milestone 3.2 recovery, continuation, and reconciliation semantics — current rules

The recovery surfaces have been corrected several times as real operation exposed real defects.
These are the records that state the **current** rule; each supersedes only what it names, and every
earlier record remains historically accurate about the state it described.

| Question | Controlling record |
|---|---|
| Where a predecessor receipt may be found | [Decision 063](Decisions/decision_063_m3_2_cross_namespace_receipt_chain_recovery.md) §5 — by recorded identity, in the accepted receipt locations beneath the governed evidence root |
| Which receipt condition **8.12** compares the carry-in checkpoint against | [Decision 064](Decisions/decision_064_m3_2_final_recovery_semantics_and_precloseout_hardening.md) §2 — the chain's **root**, never its head |
| Which receipt condition **8.10** compares the supplied plan against | Decision 064 §2 — the chain's **head**; the two questions are distinct |
| Whether condition **8.2** can establish a successful `complete` head | Decision 064 §3 — yes, from the same ten durable conditions, with no fabricated interruption state |
| What `SAFE` means, and whether it permits acquiring again | Decision 064 §4 — evidence certainty only; a `complete` head is **non-resumable** and refuses before any transport is constructed |
| When `rebuild-projection` may proceed | Decision 064 §5 — an explicit eleven-condition action-specific gate; it repairs a **lagging** projection and refuses a **diverging** one |
| The order in which store uncertainty and the derived projection are repaired | Decision 064 §5.2 — adjudicate the store, then reconstruct the projection |
| How condition **8.8**'s remainder is counted | Decision 064 §6 — **per identity**, through the same expansion continuation enforcement uses |
| How an owner-superseded request identity is reconciled | Decision 064 §7 (with [Decision 062](Decisions/decision_062_m3_2_terminal_failure_and_sic_endpoint_remediation.md) §§7–8) — the same seventeen-condition verifier, paired flags, never inferred |
| Where a receipt physically lives | Decision 064 §8 — two accepted filename conventions; a receipt is addressed by its recorded identity |

## Milestone 3.2 — final acceptance and closeout — current rules

[Decision 065](Decisions/decision_065_m3_2_final_acceptance_and_closeout.md)
(`ACCEPTED — OWNER FINAL M3.2 CLOSEOUT 2026-08-13`) is the **last M3.2 acceptance record**. It closes
the milestone on the fresh independent final acceptance review's `PASS` at BLOCKER 0 / MAJOR 0 /
MINOR 0.

[Decision 066](Decisions/decision_066_m3_2_postcloseout_readonly_reconciliation_ci_correction.md)
(`ACCEPTED — OWNER POST-CLOSEOUT CI CORRECTION AUTHORIZATION 2026-08-13`) is a later
**post-closeout maintenance** record, not a second acceptance. It changes no accepted M3.2 fact and
moves no tag; it restores the already-accepted read-only reconciliation invariant that GitHub Actions
CI found broken on the closeout commit.

| Question | Controlling record |
|---|---|
| Is Milestone 3.2 complete | Decision 065 §3 — **yes**, `M3_2_FINAL_OWNER_ACCEPTANCE`, complete and owner-accepted |
| Is Gate H passed | Decision 065 §3 — **yes**, passed and **owner-accepted**, on the 30-of-30 offline candidate `PASS` (Decision 064) and the independent final audit |
| Is M3.2B required, pending, or authorized | Decision 065 §4 — **no** to all three. **CLOSED AS NOT EXECUTED / NOT REQUIRED**; it carries no latent acquisition or network authority and is never resurrectable from a historical M3.2 authorization |
| Does any further M3.2 SEC acquisition or network authority exist | Decision 065 §§3, 11 — **none**; every live grant and one-shot authority is permanently spent, and tracked switches remain `false` / `false` |
| Which commit carries the `m3.2-complete` tag, and who authorized it | Decision 065 §9 — the **governance closeout commit**, not the accepted implementation baseline `5c4c875e…`; authorized by `M3_2_CLOSEOUT_AND_TAG_OWNER_AUTHORIZED` |
| Is M3.3 begun or authorized | Decision 065 §11 — **neither**; it requires its own separate owner packet and accepted stage contract |
| What happened to OPT-1 and OPT-2 | Decision 065 §10 — both **DEFERRED**; neither is a blocker |
| May `m3 reconcile-requests` change a durable artifact | Decision 066 §4 R1 — **no**. It creates exactly its authorized report and leaves every pre-existing durable artifact, the main SQLite catalog included, byte-identical; transient `-wal` / `-shm` sidecars and the governed lease never licence a change to the main database bytes |
| Which record governs the read-only byte-comparison CI test | Decision 066 §4 R2 — that test is **normative**. It may be strengthened or refactored, never weakened, excluded, skipped, or dropped from the `[dev,sec]` suite |
| Did the post-closeout correction move `m3.2-complete` or change an accepted M3.2 fact | Decision 066 §§3, 4 R3 — **neither**. The tag, the closeout commit `2185f583…`, and the accepted implementation baseline `5c4c875e…` all stand; the correction commit becomes only the current software baseline proposed for M3.3 entry |

## Milestone 3.3 — snapshot authority and the offline parse prerequisite — current rules

[Decision 067](Decisions/decision_067_m3_3_snapshot_authority_and_offline_parse.md)
(`ACCEPTED — OWNER M3.3 GOVERNANCE RULINGS 2026-08-13`) is the **first M3.3 record**. It is a
**governance authority record and is not implementation authorization**: it resolves the two
entry-blocking owner rulings and issues four more, and it **accepts no contract**, enables no
network, and starts no work.
[Decision 068](Decisions/decision_068_m3_3_e0_contract_correction.md)
(`ACCEPTED — OWNER BOUNDED CONTRACT CORRECTION 2026-08-13`) is the **second M3.3 record**: after
the fresh independent review of the 067-corrected contract returned **FAIL** (BLOCKER 0 / MAJOR 1 /
MINOR 1 — artifact
[`Docs/m3/reviews/m3_3_corrected_contract_independent_review_c8acfef.md`](m3/reviews/m3_3_corrected_contract_independent_review_c8acfef.md),
immutable), it adopts those findings and issues **R17**, **R18**, and clarification **R16-C1** —
likewise governance-only, accepting no contract and starting no work.
[Decision 069](Decisions/decision_069_m3_3_contract_final_owner_acceptance.md)
(`ACCEPTED — OWNER FINAL M3.3 CONTRACT ACCEPTANCE 2026-08-13`) is the **third M3.3 record**: after
the fresh independent rereview of the Decisions-067–068-corrected contract **PASSED** (BLOCKER 0 /
MAJOR 0 / MINOR 0 / OBSERVATION 1 — frozen target `7bb36b8…`, immutable artifact
[`Docs/m3/reviews/m3_3_decisions_067_068_corrected_contract_fresh_rereview_7bb36b8.md`](m3/reviews/m3_3_decisions_067_068_corrected_contract_fresh_rereview_7bb36b8.md),
committed `033d0d9…`), it records the owner's acceptance of the rereview and of the contract, and
disposes the one observation (OBS-R1) as a nonblocking historical narrative erratum on Decision 068
§3.1 — without editing Decision 068. The accepted
[`Milestones/contracts/m3_3.md`](../Milestones/contracts/m3_3.md) is
`ACCEPTED — OWNER FINAL CONTRACT ACCEPTANCE — DECISION 069` with `CONTRACT_ACCEPTANCE: YES` and
**every executable-authority flag still closed**; `ACTIVE_STAGE_CONTRACT` now names it, and
**activation is navigation, not authorization**.

| Question | Controlling record |
|---|---|
| The exact candidate-snapshot identity preimages (**OR-1**) | Decision 067 §9 — the M3.3-GR eleven-digest matrix as the normative basis, subject to OQ-3/OQ-4/OQ-5/OQ-6/OQ-7/OQ-8 and the R16 expansion |
| Whether `input_observation_set_sha256` is the same digest as Decision 021 §8.1's `source_observation_set_sha256` | Decision 067 §9.1 — **definitionally identical**; computed before `INSERT` **and** independently recomputed from persisted evidence in the same authoritative transaction; **fail closed / roll back** on mismatch |
| The M3.2 → candidate read set and mapping (**OR-2**) | Decision 067 §10 — the 135-column mapping as the normative basis, with eight mandatory GV2 corrections |
| Whether the census parse layer is populated, and what M3.3 does about it | Decision 067 §2.1 (GV2-5/GV2-6) — **it is empty**, `parser_state` `not_started` for all 76 plan sources — and **§4 Ruling R13**: a **bounded offline metadata parse** is the prerequisite, binding every source through `census_plan_sources.observation_id`. **Not** an acquisition authority |
| Whether a uniformly empty `schema_fingerprint_sha256` may be used instead of parsing | Decision 067 §5 **Ruling R14** — **no**. Only a *legitimate* zero-structural-row result may use the accepted empty-row-set digest; a failed source is never a fabricated empty parse |
| Whether `evidence_sha256` keeps `source_observation_id` and `parsed_record_id` | Decision 067 §6 **Ruling R15** — **yes, ALT-3**; Decision 016 §4 retained exactly. Reparse is deterministic; only re-retrieval is not, and M3.3 forbids it. Limitation **D067-L1** records the bounded residue |
| The `evidence_sha256` call shape and the eight candidate `*_resolution_sha256` derivations | Decision 067 §7 **Ruling R16** — accepted `hash_table` only, no second hashing implementation, and a **candidate-layer** resolution digest that never reuses the census accession `resolution_sha256` |
| `coverage_policy_version`'s value | Decision 067 §8 — **`pilot-coverage/1.0`**. That record did not fix its executable home, leaving it an open implementation-packet path question (contract §20) — ***(NO LONGER OPEN: accepted [Decision 070](Decisions/decision_070_m3_3_i_r_implementation_authorization.md) §4 fixes the canonical executable home as `PILOT_COVERAGE_POLICY_VERSION` in `src/disclosure_drift/pilot_policy.py` at `pilot-coverage/1.0`, an engineering/provenance version only — no config setting, no environment variable, no `reference_policy_versions` seed row, and no migration. It discharges contract §20 and §23 item 28 for that constant and nothing else. Decision 067 §8 is not rewritten historically.)*** |
| The persisted evidence-role vocabulary | Decision 067 §8 — **`winning` / `competing` / `supporting`**, migration `0009`'s vocabulary; Decision 016 §4's wording is illustrative and historical |
| Whether the real offline parse may be run | Decision 067 §11 — **not yet**. **M3.3-E0** is a separate owner gate, it requires an independent read-only verification before **M3.3-E1**, and **there is no automatic E0 → E1 progression** |
| The exact E0 durable write set | **Decision 068 §3 Ruling R17** — exactly **fifteen tables** (the nine parse-layer tables plus the six companion tables the reusable accepted persistence path legitimately writes), mechanically verified; `census_qa_metrics` and all four index-side tables excluded; no second writer implementation |
| What "E0 completeness" means per planned source | **Decision 068 §4 Ruling R18** — exactly one **report-level** disposition per planned source: `E0_REQUIRED_PARSE`, `E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE`, or `E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY`; the 70 quarterly full-index sources are category C, deliberately untouched, with no `parser_state` mutation ***(SUPERSEDED ON ONE POINT by accepted [Decision 072](Decisions/decision_072_m3_3_full_index_multi_registrant_source_correction.md) §2, Ruling R22: `sec_full_index_company` is CANDIDATE-SUBSTANTIVE — each plan-bound full-index source is category **A** when usable and category **B** when accepted unavailable, and **NEVER category C**. R18's report-level disposition mechanics are otherwise unchanged and remain authoritative, and Decision 068 is not rewritten historically.)*** |
| Which evidence rows a candidate resolution digest binds | **Decision 068 §8 Clarification R16-C1** — exactly the persisted rows the accepted deterministic resolution procedure actually uses; substantive, mechanical, independently recomputable, I/R-exposed and I/R-tested; an undeterminable set stops and refers |
| Whether Decision 067 or 068 accepts the M3.3 contract or authorizes implementation | Decision 067 §12; Decision 068 §10 — **neither.** The required fresh independent rereview then ran, passed, and **Decision 069** recorded the separate owner acceptance act |
| Whether the M3.3 contract is accepted, and by what authority | **Decision 069 §3** — **yes**: `M3_3_CORRECTED_CONTRACT_FINAL_OWNER_ACCEPTED`, on the frozen accepted target `7bb36b8…` and the passing fresh rereview (`B0/M0/MIN0`, artifact committed `033d0d9…`). `ACTIVE_STAGE_CONTRACT` names the accepted contract |
| How Decision 068 §3.1's "exactly twenty-four durable-write statements" is read | **Decision 069 §4 (OBS-R1 erratum)** — as **19 execute sites, or 23 write clauses counting embedded upsert clauses**; the sixteen-distinct-tables resolution and the fifteen-table permitted E0 footprint are unchanged and correct, and Decision 068 is not edited |
| Whether contract acceptance authorizes implementation, E0, E1, E2, or M3.4 | **Decision 069 §§5–6 — no, none of them.** Acceptance is one Decision 024 §8 condition; the next act is a **separate owner M3.3-I/R implementation + rehearsal authorization packet**, and E0/E1/E2 each remain later separate owner gates |

[Decision 070](Decisions/decision_070_m3_3_i_r_implementation_authorization.md)
(`ACCEPTED — OWNER M3.3-I/R IMPLEMENTATION + REHEARSAL AUTHORIZATION 2026-08-13`) is the **fourth
M3.3 record** and the **only** authority under which M3.3 implementation may begin;
[Decision 071](Decisions/decision_071_m3_3_i_r_methodology_gap_adjudication.md),
[Decision 072](Decisions/decision_072_m3_3_full_index_multi_registrant_source_correction.md),
[Decision 073](Decisions/decision_073_m3_3_rehearsal_snapshot_bifurcation_and_amendment_purpose_blocker.md),
and
[Decision 074](Decisions/decision_074_m3_3_e5_reserve_rehearsal_and_real_linkage_gate.md)
then govern that same bounded stage without creating a new one. **The stage is now implemented and
rehearsed and still authorizes no real execution**: scenarios E1–E8 pass at their accepted track
assignment, the **R28** bridge is clean, and the mutation campaign M1–M38 is fully killed — none of
which is an authorization for M3.3-E0, M3.3-E1, M3.3-E2, or M3.4. **Two real-path feasibility gates
are open and independently auditable**, and they are never merged into one flag.

| Question | Controlling record |
|---|---|
| Under what authority M3.3 implementation may begin, and how far it extends | **Decision 070 §2** — exactly five things: implementing the accepted contract, its tests, **fixture / disposable-copy rehearsal**, narrow **R3** hardening, and the governance records the stage needs. **Not** `EV_ROOT`, E0, a real snapshot, a real selection, a real manifest or root, SEC, HTTP, network, reacquisition, CompanyFacts, Frames, filing bodies, methodology changes, or migrations |
| Where `coverage_policy_version` lives executably | **Decision 070 §4** — `PILOT_COVERAGE_POLICY_VERSION` in `src/disclosure_drift/pilot_policy.py` at `pilot-coverage/1.0`; an engineering/provenance version only, with **no** config setting, environment variable, `reference_policy_versions` seed row, or migration. Discharges contract §20 and §23 item 28 **for that constant and nothing else** |
| How each Decision 014 §5 event flag is **detected** | **Decision 071 §3 Ruling R19** — only from accepted, structured, explicit evidence that mechanically establishes it. **Lack of evidence is never a positive event**, and substring matching, regular expressions over status text, fuzzy matching, synonyms, name or ticker keywords, `entityType` inference, operator judgment, outcome data, filing narrative, and absence from an alias-only ticker list are all forbidden |
| How a candidate is **established** as a boundary control | **Decision 071 §4 Ruling R20** — four independent evidence predicates; **`entityType` may not assign `control_kind`**. Exactly one predicate assigns; zero means not a control; **more than one is conflicting, with no precedence defined** |
| What the XBRL resolution's `resolved_value` is | **Decision 071 §5 Ruling R21** — the canonical serialization of exactly `{has_inline_xbrl, has_xbrl}` through the **existing** accepted canonical-JSON serializer; `hash_table`'s internal separator is never an application-level encoding |
| Whether the 2009/2010 pair quota may be proved from one accession's flags | **Decision 071 §6 IN-3 — no.** A pair is a property of the **joint selection result**: one selected SUPPORT-role 2009 original and one selected BASE-role 2010 development target under one anchor CIK, both in the same run, counted **once per distinct entity**, at **six** distinct entities |
| Whether `sec_full_index_company` is candidate-substantive | **Decision 072 §2 Ruling R22 — yes.** Category **A** when usable, **B** when unavailable, and **never C**. A source does not become category C merely because current code lacks a candidate-facing route (**R25**) |
| How co-registrants and `multi_registrant` are established | **Decision 072 §3 Ruling R23** — from plan-bound accepted `company.idx` rows through the **existing** accepted parser and canonicalization; a full-index row **never creates** a candidate accession; `multi_registrant` is true **iff** one valid anchor plus at least one distinct valid associated registrant; submitter-only rows never make it true |
| Whether the multi-registrant quota may be deferred | **Decision 072 §4 Ruling R24 — no.** Measurable, hard, not deferred, not optional; the difficult-package exception is **not generalized** |
| The exact RIC/ETF SIC set | **Decision 072 §6 Ruling R26** — exactly **`{6722, 6726}`**; not broadened by proximity, and **`6798` is not included** |
| Why a builder-derived snapshot is expected to be infeasible | **Decision 073 §1** — the accepted builder assigns no affirmative `amendment_purpose_category` from authorized metadata, IN-2 forbids inventing one, the selector requires three distinct categories, and a `NULL` category produces no witness. **Not a selector defect and not a builder defect under IN-2** |
| How rehearsal is structured, and what Track B may and may not claim | **Decision 073 §§3–5 Rulings R27–R29** — two tracks that are never conflated; Track A must **prove** the infeasible disposition and is never modified to become feasible; Track B is explicitly governed, and every Track-B report states `FEASIBILITY SOURCE: EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT` and never implies real feasibility |
| What keeps Track B from being an easier universe | **Decision 073 §4 Ruling R28** — paired siblings from one synthetic base case, compared **mechanically before selector execution**, with an **explicit allowlist**; the bridge **fails on any difference outside it** |
| Whether the real builder can produce a feasible selection | **Decision 073 §6 Ruling R30 — unknown, and OPEN.** `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN`. **I/R passing does not authorize E0, and A1 passing does not by itself** |
| Whether every selected target must hold a reserve package | **Decision 074 §2 Ruling R31 — no.** Decision 020 §7 makes a target-specific `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition **lawful, durable, and nonblocking**. The old E5(a) requirement was production-invalid and is superseded; E5(a) now proves the **positive** compatible path at the **pure** reserve layer, E5(b) the zero-compatible case, and E5(c) the mixed case |
| Whether the real path can satisfy the linked-amendment quota | **Decision 074 §3 Ruling R32 — unknown, and OPEN.** `M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN`: no accepted source field maps to `amendment_relationship`, and `possible_amendment_of` / `unresolved_amendment` satisfy nothing. The quota is **not** lowered, deferred, or proxied |
| How `cohort_boundary_crossed` is derived | **Decision 074 §5 Ruling R33** — from **this build's own** resolved official filing date and acceptance audit date, in the **same** candidate-snapshot derivation. Both known and different ⇒ `TRUE`; both known and equal ⇒ `FALSE`; either unresolved, absent, or malformed ⇒ **review-required, never a silent `FALSE`** |
| What a future real E0 must report about acceptance evidence | **Decision 074 §6 Ruling R34** — the seven enumerated counts. Strict parsing and Decision 019's fail-closed ordering are retained; **no result is assumed today**, and this is an E0/E1 **verification condition**, not a third pre-E0 methodology gate |
| Whether a passing I/R, ultrareview, or independent acceptance authorizes real E0 | **Decision 074 §4 — no.** A separate Sol/GPT architecture disposition must first address **both** open real-path gates, and the two are **never merged into one vague flag** |

## Decision 075 — ACCEPTED (M3.3-I/R ultrareview bounded correction)

[Decision 075](Decisions/decision_075_m3_3_i_r_ultrareview_bounded_correction.md)
(`ACCEPTED — OWNER M3.3-I/R ULTRAREVIEW BOUNDED CORRECTION 2026-08-14`) is the **sixth M3.3
record**. The independent read-only **ultrareview** of the frozen I/R executable target `6f87abc…`
returned **BLOCKER 0 / MAJOR 0 / MINOR 3 / OPTIMIZATION 0 / OBSERVATION 6**, and the owner accepted
its architectural conclusion in full. Decision 075 authorizes **only** the bounded corrections those
three MINOR findings require. It **reopens no architecture and no methodology**, supersedes and
amends nothing in Decisions 001–074, and **grants no execution authority of any kind**.

**It was not an acceptance of the corrected target.** *(Current state: that corrected-target
rereview is **COMPLETE** and MIN-A is **CLOSED**; the requirement below is therefore satisfied and
historical. The live next act is stated under Decision 077.)*

| Question | Controlling record |
|---|---|
| What the ultrareview confirmed as correct, and may not be reopened | **Decision 075 §2** — R31/E5, R32, R33, R34, IMP-1/2/3, Track A, Track B, R28, the accepted joint selector, the 2009/2010 pair, persistence and run identity and reconstruction, the R3 replay standard, the seal/manifest separation, Decision 023 O1, the CLI real-gate refusals, and the network / private-data boundary |
| Which stale current-state pointers were corrected, and how | **Decision 075 §3.1 (MIN-1)** — the R18 full-index **category C** row, by the narrow-supersession model to Decision 072 R22; and the `coverage_policy_version` row, by a current pointer to Decision 070 §4. The index is **not** restructured and **Decision 068 is not rewritten historically** |
| The contracts-README link defect | **Decision 075 §3.2 (MIN-2)** — five Decision 070–074 links at `../Docs/…` corrected to `../../Docs/…`, mechanically verified, with no link text or decision semantics altered for style |
| Why the generated report now states **two** real-path gates | **Decision 075 §3.3 (MIN-3)** — `real_linked_amendment_feasibility_gate: OPEN` is added beside `real_amendment_purpose_feasibility_gate: OPEN`. The two are **never merged** into a generic `real_feasibility_gate`; `real_builder_feasibility_proved` stays a **third separate claim**; and the fixture-only `m3 rehearse-execution` summary prints both gates **by name** |
| Whether the execution-rehearsal report schema version is bumped | **Decision 075 §4 — no.** It remains `m3-3a-execution-rehearsal-report/1.0`. MIN-3 is an **additive completion** of an already-governed status block: it reinterprets, removes, and renames no key, alters no scenario or selector semantics, alters no persisted schema, and grants no authority |
| What the two adopted observations added | **Decision 075 §5** — **OBS-1**, a direct IMP-3 proof (the unrelated `10-D` exists in the source-history layer, never becomes a candidate accession, and is reported in `excluded_form_counts`, while **R20** still reads it); and **OBS-3**, one direct M3.3-level **strict-subset** E5 proof through the same accepted `build_reserve_packages`. **Both test-only**; `reserve_selector.py` is untouched |
| What OBS-6 requires before formal acceptance | **Decision 075 §6** — a durable, reviewable M1–M38 campaign record at `Docs/m3/reviews/m3_3_i_r_mutation_campaign_<CORRECTED_SHA>.md`. The runner is **not** added to production source, no mutated source or scratch file is committed, and facts are **recovered, never fabricated** |
| Whether the original implementer evidence was edited | **Decision 075 §7 — no.** [`m3_3_i_r_rehearsal_6f87abc.md`](m3/reviews/m3_3_i_r_rehearsal_6f87abc.md) is byte-unchanged historical evidence for target `6f87abc`; the corrected target gets its **own** new artifact |
| Whether anything about the real path changed | **Decision 075 §8 — no.** Both gates stay **OPEN** and unmerged, acceptance-ordering adequacy stays **PENDING FUTURE AUTHORIZED E0 VERIFICATION**, and **E0/E1/E2 remain unauthorized** |

## Decision 076 — ACCEPTED (M3.3 pre-acceptance infrastructure optimization)

[Decision 076](Decisions/decision_076_m3_3_preacceptance_infrastructure_optimization.md)
(`ACCEPTED — OWNER M3.3 PRE-ACCEPTANCE INFRASTRUCTURE OPTIMIZATION 2026-08-14`) is the **seventh
M3.3 record** and the only one that governs **infrastructure rather than methodology**. It changes
no research definition, no selector, no quota, no schema, no evidence identity, and no
authorization; it changes how the existing suite is scheduled and adds tooling. Both real-path
gates remain **OPEN**, and it is **not** a Fable acceptance.

| Question | Controlling record |
|---|---|
| The local full-suite standard | **Decision 076 §3 — R35, the Seven-Worker Full-Suite Development Standard.** Seven workers, three-run median below 80.0 seconds, achieved with no test deleted, skipped, `xfail`ed, mocked for timing, or otherwise weakened. Seven is a **measured local optimum, not a constant** |
| Whether the serial path survives | **Decision 076 §4 — yes, and it is never deleted.** `make test` and `make check` keep serial pytest; `make check-fast` is the same gate set with the parallel path substituted. No `-n` enters `addopts`, so a bare `pytest` stays serial |
| Which xdist mode, and why | **Decision 076 §4** — `worksteal`, chosen by measurement (60.75s against `load`'s 72.68s at seven workers, both 3949 passed / 1 skipped). **`loadfile` is prohibited** for this repository: grouping by file pins the two large modules to single workers |
| What `make links` checks | **Decision 076 §5** — every relative Markdown link resolves to a tracked path. Acceptance invariant `UNALLOWED_BROKEN_LINKS = 0`; **no link total is frozen** |
| What `make decision-refs` checks | **Decision 076 §6** — every `Decision NNN section N` citation names a section that exists, across the **three** section conventions the records actually use: numbered headings, ordered-list items under a numbered heading, and numbered lines inside a fenced verbatim owner instrument. Acceptance invariant `INVALID_DECISION_SECTION_REFS = 0` |
| Whether a gate may be made green by editing history | **Decision 076 §7 — no.** Every exception is exact — one file plus one target, or one file plus one decision-and-section — with a reason and a governing status. **No wildcard, no pattern, no per-line escape marker**, and an entry matching nothing **fails** the gate |
| Where the audit tools live and what they may do | **Decision 076 §8 and §9.** `scripts/verify_target.py` is read-only and hard-codes no milestone SHA. The mutation runner lives at `scripts/dev/`, is **never** imported by the package, refuses the authoritative repository unless explicitly and safely permitted, proves source isolation, restores from in-memory bytes, and checks residue |
| Where the M1–M38 definitions come from | **Decision 076 §9** — **recovered** from [`m3_3_i_r_mutation_campaign_06bb47a.md`](m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md), never invented, per Decision 075 §6. That artifact is read and never written, and a definition that cannot be recovered exactly stops for owner referral |
| Whether CI switches to seven workers | **Decision 076 §10 — no.** The measured optimum is machine-specific; CI keeps its serial run and is not altered by this stage. The Makefile accepts a worker override so CI can choose its own value once measured **there** |
| What is explicitly deferred | **Decision 076 §11** — eight items including the `evidence_reference` byte-digest question, all returned as **DEFERRED — REQUIRES SEPARATE OWNER ARCHITECTURE DECISION** |
| The adopted review-process rules | **Decision 076 §12** — **P1–P7**: invariants over incidental totals; real versus synthetic evidence root; defect-in-correction handling; claim-provenance labels; gate timings; machine-readable first; mechanical A/B branches. **Process rules, not methodology** |
| What the new gates found on their first run | **Decision 076 §13** — four **OPEN DEFECTS** in live M3.3-I/R source and tests of the same class as MIN-A, plus seven wrong citations inside immutable accepted records and two known-broken links. **None was corrected by Decision 076**; correcting the live four needed its own bounded owner authorization. *(Current state: those four are **RET-1**, since **CLOSED**. The seven in-record citations and two links remain documented historical exceptions.)* |
| Whether all five MIN-A references are mechanically detectable | **Decision 076 §13 — no, three of five.** Decision 075 genuinely **has** a section 6, so the two bare section-6 citations were pointing at the wrong section rather than a missing one. An existence gate cannot catch that, and a test keeps the limitation visible |

## Decision 077 — ACCEPTED (M3.3-I/R Fable acceptance findings, final bounded correction)

[Decision 077](Decisions/decision_077_m3_3_i_r_fable_acceptance_findings_correction.md)
(`ACCEPTED — OWNER M3.3-I/R FABLE ACCEPTANCE FINDINGS CORRECTION 2026-08-14`) is the **eighth M3.3
record**. The **first** formal Fable 5 Maximum M3.3-I/R acceptance review of target `46b6742…`
returned **BLOCKER 0 / MAJOR 0 / MINOR 2 / OPTIONAL 1 / OBSERVATION 3**. Decision 077 disposes those
findings and authorizes **only** the bounded correction they require: where live comments point,
what live navigation surfaces say the current stage is, and how the operator runs routine
validation. It changes **no** methodology, selector, quota, schema, identity, or authorization.

**It is not an acceptance, and it claims none.** *(Current state: the fresh Fable 5 Maximum formal
M3.3-I/R acceptance review this record named as its next act has since been run and **PASSED** at
B0/M0/MIN0, and **Sol/GPT has accepted M3.3-I/R** — see Decision 078 below. The sentence that a
further Opus ultrareview is neither authorized nor required still holds.)* Both real-path gates
remain **OPEN** and unmerged.

| Question | Controlling record |
|---|---|
| What a live authority pointer must name | **Decision 077 §2 — R36.** The **actual accepted section supporting the adjacent claim**. A structurally existing but **semantically unrelated** section is not acceptable, which is why `R20 §7` — resolving to Decision 071 §7, the calendar-source R18 recheck — was a defect an existence gate cannot see |
| Whether the section-reference gate is changed to catch this | **Decision 077 §2 — no.** `check_decision_section_refs.py` stays an **existence** checker, neither broadened nor weakened to force a result. **No semantic NLP checker is built.** Where structural existence and human semantic review disagree, **semantic review controls** |
| Whether correcting only a reviewer's listed sites is sufficient | **Decision 077 §2 — no.** Every live Decision 071–076 citation is swept. A site whose accepted target is not mechanically clear is **returned to the owner as a new MINOR**, never resolved by inventing an authority |
| Whether the `R19 §4.N` and `R23 §5.N` internal labels are defects | **Decision 077 §2 — no.** Decision 071 §3's R19 table keeps its original `4.1`–`4.12` row labels and Decision 072 §3's R23 table keeps its `§5.1`–`§5.6` aspect labels; both exist in the accepted records and name the right predicates. Because `R19 §4.N` can be misread as Decision 071 §4 — which is **R20** — the modules using that form now state the convention |
| What a current-state surface must say | **Decision 077 §3 — R37.** I/R implemented and rehearsed; Opus review work **complete**; MIN-A and RET-1 **CLOSED**; Decision 076 infrastructure complete; first Fable review **B0/M0/MIN2, not accepted**; Decision 077 applied; **fresh Fable acceptance next**; E0/E1/E2/M3.4 unauthorized; both gates **OPEN** |
| Whether accepted historical records are rewritten to match | **Decision 077 §3 — no.** Decision 075 §10 keeps its own next act and Decision 076 §13 keeps its RET-1 finding; both are historically true. Historical passages on a navigation surface may remain **when marked historical**; operative instructions may not |
| The routine local validation command | **Decision 077 §4 — R38.** **`make check-fast`**, whose pytest leg uses `WORKERS ?= 7` and `DIST ?= worksteal`. `make test` and `make check` remain the serial references; `make links` and `make decision-refs` are the governance gates |
| Whether seven workers is the CI standard | **Decision 077 §4 — no.** It is measured on the owner's machine, `WORKERS`/`DIST` are overridable, and CI was **not** switched under Decision 076 §10. R38 is workflow documentation and is **never** a precondition for an E0/E1/E2 authorization |
| How the `evidence_reference` observation was disposed | **Decision 077 §6 — OBS-1, DEFERRED.** It stays part of the Decision 076 deferred architecture question. **No** redefinition of `evidence_reference`, receipt, evidence, selection, manifest, or catalog-digest semantics |
| What was returned to the owner unresolved | **Decision 077 §7** — one new **MINOR**: `tests/unit/test_m3_support_target_pairs.py`'s `§17 item L`, which names no accepted record and was left byte-unchanged rather than guessed |

## Decision 078 — ACCEPTED (M3.3-I/R owner acceptance and the pre-E0 real-feasibility source audit)

[Decision 078](Decisions/decision_078_m3_3_i_r_owner_acceptance_and_real_feasibility_audit.md)
(`ACCEPTED — OWNER M3.3-I/R ACCEPTANCE AND PRE-E0 READ-ONLY SOURCE-AUDIT AUTHORIZATION 2026-08-14`)
is the **ninth M3.3 record**. It records **Sol/GPT's formal owner acceptance of the completed
M3.3-I/R stage** and authorizes **one** bounded read-only pre-E0 source audit. It does nothing else.

**M3.3-I/R is COMPLETE and OWNER ACCEPTED.** **It closes neither real-path gate**, and it
authorizes no real execution: M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 each remain a separate, unissued
owner gate.

| Question | Controlling record |
|---|---|
| Whether M3.3-I/R is accepted | **Decision 078 §1 — yes.** Accepted executable target `feaeaa4163587730d6b12ebb87aabf2fc215c8f3` at tree `3d33454a…`, `M3_3_I_R_STATUS: OWNER ACCEPTED / COMPLETE`, formal outcome `M3_3_I_R_OWNER_ACCEPTED` |
| What the acceptance rests on | **Decision 078 §1** — the final fresh Fable 5 Maximum formal independent acceptance review's **PASS at B0 / M0 / MIN0 / OPT0 / OBS1** (immutable artifact [`m3_3_i_r_formal_independent_acceptance_feaeaa4.md`](m3/reviews/m3_3_i_r_formal_independent_acceptance_feaeaa4.md), evidence commit `8c43edd…`), an optimized full check of **4029 passed / 1 skipped / 0 failed**, a clean live Decision-authority semantic review, and the four contract/plan item references adjudicated **4/4 CORRECT** |
| What a passing I/R proves | **Decision 078 §1 — that the accepted system operates correctly on a conforming feasible candidate snapshot, and nothing about real feasibility.** A review artifact is evidence; **this record**, not that artifact, is the acceptance |
| Whether the accepted I/R architecture may be reopened | **Decision 078 §1 — not without a newly discovered material defect** |
| The state of the two real-path gates | **Decision 078 §2 — both OPEN / ACTIVE and never merged.** `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` (Decision 073 R30) and `M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` (Decision 074 R32); `real_builder_feasibility_proved` remains **false**; acceptance-ordering adequacy remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION** (Decision 074 R34) |
| What the pre-E0 audit may do | **Decision 078 §3 — R39.** One bounded, **zero-network**, **read-only** inspection of the **already accepted** M3.2 source material, with true OS-level read-only handles where SQLite is involved, in-memory parsing and out-of-repository scratch permitted, and **counts reported, never the evidence-root path** |
| The two questions it answers | **Decision 078 §3.1** — independently, whether existing accepted sources suffice for (**A**) real amendment purpose and (**B**) real linked-amendment parentage, each `YES` / `NO` / `UNDETERMINED — <exact bounded reason>`. **Hopeful and probabilistic language is prohibited**, and a negative result is never withheld |
| What it may not do | **Decision 078 §3.3** — no mutation, snapshot, E0 write, E1, selection, persistence, seal, manifest, network, SEC retrieval, HTTP, reacquisition, filing body or header, CompanyFacts, Frames, or alternate URL. `REQUEST_CEILING` is **0**. **STOP** if the accepted evidence root cannot be mechanically identified without guessing |
| Who decides methodology | **Decision 078 §3.4 — Sol/GPT, not the auditor.** The audit may not weaken a quota, accept inferential parentage, accept `/A` as linkage, invent a category, authorize filing-body retrieval, reopen M3.2, or change the no-network rule |
| Which inferences stay prohibited | **Decision 078 §4** — purpose never from `/A` alone, XBRL presence, timing, sequence, company name, filename heuristic, amendment count, linkage state, or size; parentage never from `/A` alone, same CIK, same report date, date proximity, filing or accession order, document name, or filename. Both quotas stay hard — **8** linked-amendment entities, **3** purpose categories |
| What happens if a gate returns `NO` | **Decision 078 §5** — the minimum additional acquisition is **designed and not executed**, as a bounded option matrix, with **one shared source explicitly preferred** where both gates need one and sharing never forced |

*(Current state: **Decision 078 §3's ruling is numbered R39**, and **Decision 079 §3 independently
numbers a different ruling R39**. Neither amends the other. Always write **Decision 078 R39** or
**Decision 079 R39** — a bare "R39" is ambiguous and prohibited. See Decision 079 §1.)*

## Decision 079 — ACCEPTED (the pre-E0 ephemeral real-source parse and amendment-inventory audit)

[Decision 079](Decisions/decision_079_m3_3_pre_e0_ephemeral_real_source_parse_audit.md)
(`ACCEPTED — OWNER PRE-E0 EPHEMERAL REAL-SOURCE PARSE / AMENDMENT-INVENTORY AUDIT AUTHORIZATION
2026-08-14`) is the **tenth M3.3 record**. It authorizes **one** bounded pre-E0 audit that measures
the **real** amendment-candidate population from the **already acquired** accepted M3.2 raw objects,
and records **R39 (Decision 079)**, **R40**, **R41**, and **P8**. It does nothing else.

**It closes neither real-path gate**, and it authorizes no real execution: **M3.3-E0 durable
parsing**, M3.3-E1, M3.3-E2, and M3.4 each remain a separate, unissued owner gate.

| Question | Controlling record |
|---|---|
| What the durable catalog's zeros mean | **Decision 079 §2 — a structural zero, not an empirical one.** No parse has ever run, so `DURABLE_PARSED_AMENDMENT_POPULATION = 0` while `REAL_RAW_SOURCE_AMENDMENT_POPULATION = NOT YET MEASURED`. Measuring it requires **no new SEC request** |
| How to treat a hash/validator contradiction | **Decision 079 §3 — R39.** Byte-exact frozen SHA-256 plus a contradictory ad-hoc field-level checker is `VALIDATOR_CONFLICT`, **not** `ARTIFACT_IDENTITY_MISMATCH`, until a correct structured parse confirms it. A hash proves the bytes, not every semantic assertion — but a weaker substring/search checker may never overrule byte-exact identity |
| Which R39 is being cited | **Decision 079 §1 — always decision-qualified.** Decision 078 R39 is the read-only source audit; Decision 079 R39 is the validator-conflict rule. A bare "R39" is prohibited |
| What an ephemeral parse may do | **Decision 079 §4 — R40.** Accepted production parsers over accepted M3.2 raw objects, producing temporary records in Python memory or session scratch **outside** the repository and `EV_ROOT`. **Never** written to `census_parser_runs`, `census_parsed_records`, `census_accessions`, `census_accession_observations`, any candidate or selection table, or any accepted catalog. **No SQLite writer, no migration, no durable parser-state change** |
| What the audit output is worth | **Decision 079 §5 — R41.** Audit values only. They constitute no E0 census state, candidate record, evidence, resolution, selection eligibility, purpose classification, amendment relationship, or manifest input, and become durable real-pilot evidence only if a separately authorized stage persists and validates them |
| Which sources and forms are in scope | **Decision 079 §§7.3, 7.5** — only raw objects bound to accepted M3.2 plan sources by `census_plan_sources` / `census_source_observations` provenance; amendment-eligible forms are exactly **`10-K/A`** and **`10-KT/A`** against original-compatible **`10-K`** and **`10-KT`**, and no other form is added |
| Which parsers the audit must use | **Decision 079 §7.4** — the accepted pure parsers `submissions.py` and `full_index.py` with the accepted canonical normalization. **No new independent SEC parser**, no OCR, and no regex over raw JSON as a parser substitute. Machine-readable first (Decision 076 §12, P6) |
| What the audit may not conclude | **Decision 079 §7.7** — no purpose classification, no keyword inference from `primaryDocDescription`, no parent selection, no `amendment_relationship`, no date-proximity or accession-order linkage. Full index corroborates but **never overwrites** submissions facts, and no index-only accession becomes a candidate. Both quotas stay hard — **8** linked-amendment entities, **3** purpose categories |
| What nonmutation must prove | **Decision 079 §8** — HEAD, tree, receipt identity, raw-object count, catalog logical counts, main-DB and WAL size and mtime all unchanged; the three census counts still **0**; `parser_state` still `not_started` across all **76** plan sources. **SHM is a non-governed reader artifact** whose mtime may move under a genuine read-only WAL connection |
| What was returned to the owner unresolved | **Decision 079 §10** — one **OBS-1**: the R39 ruling-number collision, recorded with a mandatory citation convention rather than silently renumbering an owner-issued ruling |

*(Current state: the single Decision-079 audit **ran on 2026-08-14 and is consumed** — its findings
are owner-accepted by Decision 080 §2, and `REAL_PRIVATE_EPHEMERAL_PARSE_AUDIT_AUTHORIZATION` is
**CLOSED**. OBS-1 is **CLOSED** by Decision 080 §7: the operative validator-conflict citation is now
**Decision 080 R42**.)*

## Decision 080 — ACCEPTED (post-D079 owner adjudication and single-artifact source architecture)

[Decision 080](Decisions/decision_080_m3_3_post_d079_owner_adjudication_and_source_architecture.md)
(`ACCEPTED — OWNER POST-D079 ADJUDICATION AND SOURCE-ARCHITECTURE RULINGS 2026-08-14`) is the
**eleventh M3.3 record**. It accepts the Decision-079 audit findings as a frozen source-inventory
fact set, freezes **R42**–**R45**, and records **six architecture items PENDING OWNER ACCEPTANCE**.
It authorizes no real execution and no acquisition, and it does nothing else.

**It closes neither real-path gate**, and **M3.3-E0 durable parsing**, M3.3-E1, M3.3-E2, and M3.4
each remain a separate, unissued owner gate.

| Question | Controlling record |
|---|---|
| The frozen real amendment-inventory facts | **Decision 080 §2** — `REAL_RAW_TOTAL_AMENDMENT_CANDIDATES = 46912`; `FROZEN_COHORT_AMENDMENT_CANDIDATES = 20258` (16401 / 1750 / 861 / 711 / 535); `10-K/A` 46775, `10-KT/A` 137; 48199 raw rows before dedup; **568 multi-registrant accessions**; compatible-original diagnostic 4677 / 42159 / 75 / 1; XBRL 8424 true, inline 4199 true. **Audit facts under Decision 079 R41 — never durable E0 candidate evidence** |
| Which validator-conflict citation is live | **Decision 080 §3 — R42**, the operative prospective alias. Historical decision-qualified R39 citations stand; a bare "R39" stays prohibited; OBS-1 is **CLOSED** (§7) |
| Where the frozen 14-digit acceptance value comes from | **Decision 080 §4 — R43.** The native `<ACCEPTANCE-DATETIME>` header of a future owner-authorized Complete Submission Text is the intended higher authority (the Decision 012 §4 level-1 class); submissions values stay lower-authority corroboration; truncation, timezone arithmetic, duplicate-choosing, and registrant precedence are prohibited; fail-closed behavior remains until the native source exists; `REAL_ACCEPTANCE_ORDERING_ADEQUACY` stays **PENDING FUTURE AUTHORIZED E0 VERIFICATION** |
| Whether legacy original forms are admitted | **Decision 080 §5 — R44. No.** Original-compatible forms stay exactly `10-K` / `10-KT`; no `10-K405`, `10KSB`, or `NT 10-K`; no quota weakened |
| The preferred additional-source artifact | **Decision 080 §6 — R45.** The accession-level Complete Submission Text — native acceptance header, primary filing body, XBRL facts, Explanatory Note — as a **source candidate only, not acquisition authority**, with the frozen qualification that XBRL presence never implies `AmendmentDescription` exists |
| The multi-registrant representation | **Decision 080 §8 — findings F-MR-1–F-MR-6 and proposals MR-1–MR-5, PENDING OWNER ACCEPTANCE.** No accepted rule supplies a single lawful anchor for the 568; associations are preserved without migration; the duplicates are substantive associations forced through a single-valued model; the MR-3 anchor choice is the owner's |
| Verified amendment-purpose evidence | **Decision 080 §9 — YES, architecture-compatible; PENDING OWNER ACCEPTANCE.** The AP-1–AP-10 pre-registered dual-blind adjudication protocol over accepted stored artifacts, frozen and hash-sealed before pipeline use; requires a new owner ruling plus a future migration (`0009` excludes `verified` throughout); IN-2 not reversed; zero classifications performed |
| Explicit original / linkage evidence | **Decision 080 §10 — `REQUIRES_NEW_OWNER_RULING`, PENDING OWNER ACCEPTANCE.** The mechanism (explicit self-assertion resolved to exactly one catalog accession) contradicts no accepted prohibition, but the CST is not yet an accepted source and no evidence class authorizes it; required ruling content L-1–L-8 |
| The fixed source-verification sample | **Decision 080 §11 — design only, PENDING OWNER ACCEPTANCE.** `SAMPLE_N = 125`, deterministic hash-order selection, precommitted oversamples, `MAX_PHYSICAL_REQUESTS = 250`, mechanical measurements m1–m8, reconciliation against the frozen §2 totals. **Not executed** |
| Request economics | **Decision 080 §12 — PENDING OWNER ACCEPTANCE.** A 125/250; B expected 100–300, ceiling 400/800; **C (46912) REJECTED** — minimum acquisition consistent with non-cherry-picked evidence |
| Whether durable E0 may precede enrichment | **Decision 080 §13 — `E0_CAN_RUN_FAIL_CLOSED_BEFORE_ENRICHMENT`, PENDING OWNER ACCEPTANCE**, with three binding caveats: the enrichment ingest is **not E0**; the §8 ruling is recommended before E0; E1 stays expected-infeasible and separately gated. **The verdict does not authorize E0** |
| What happens next | **Decision 080 §16** — return to Sol/GPT for owner adjudication of the six pending items. No session may begin E0, any acquisition, or any implementation on the strength of this record |

*(Current state: the six pending items were **adjudicated by accepted Decision 081** on 2026-08-14 —
see below. Decision 080's **R42–R45** and its frozen Decision-079 fact set remain binding and
unchanged.)*

## Decision 081 — ACCEPTED (fixed Complete-Submission-Text source verification)

[Decision 081](Decisions/decision_081_m3_3_fixed_complete_submission_source_verification.md)
(`ACCEPTED — OWNER DECISION-080 ADJUDICATION AND FIXED SOURCE-VERIFICATION AUTHORIZATION
2026-08-14`) is the **twelfth M3.3 record**. It accepts the Decision-080 source-architecture review,
adjudicates its six pending items by freezing **R46**–**R50**, and fixes the exact boundary of **one**
bounded public-SEC source-verification sample.

**It closes neither real-path gate**, performs **zero** amendment-purpose classifications, resolves
**zero** real amendment parentage, and grants **no** quota credit. **M3.3-E0 durable parsing**,
M3.3-E1, M3.3-E2, and M3.4 each remain a separate, unissued owner gate.

| Question | Controlling record |
|---|---|
| Whether the Decision-080 review is accepted | **Decision 081 §2 — YES**, token `M3_3_DECISION_080_SOURCE_ARCHITECTURE_OWNER_ACCEPTED`. R42–R45 and the frozen Decision-079 fact set stand unchanged, still governed by Decision 079 R41 |
| How a multi-registrant accession is represented | **Decision 081 §3 — R46.** Relationally. A sole substantive registrant may be the scalar registrant; for more than one, **no** anchor may be chosen by first-write order, min/max CIK, archive path, record order, hash, a submissions-document occurrence, or a filing-agent/submitter heuristic — **the Decision 080 §8.3 MR-3(a) intrinsic-submitter recommendation is rejected**, and MR-3(c) blanket exclusion is not adopted either. No arbitrary scalar registrant may participate in tie-break identity, candidate identity, selection identity, history assignment, or quota credit; the scalar field becomes `NULL`/unresolved where it cannot be truthful. Migration **authorized in principle, not implemented**; any OR-1/R16 correction is returned to the owner with **no replacement singleton invented** |
| Whether verified amendment-purpose evidence may exist | **Decision 081 §4 — R47. In principle, yes**, under a pre-registered document-level protocol with eleven required properties (frozen protocol, frozen artifact SHA-256, exact document, exact span, two independent outcome-blind reviews, third adjudication or fail-closed, frozen adjudication, immutable provenance, no metadata overwrite, independent span review, post-freeze determinism). Three frozen categories unchanged; every classifier route prohibited; **zero classifications performed**; the required migration is **not authorized here** |
| When `amends_original` may be established | **Decision 081 §5 — R48.** Only on the amendment's own explicit identification of the original by compatible form (`10-K`/`10-KT`) plus exact stated filing date or accession, mapping to **exactly ONE** accepted catalog original under the same substantive registrant association, with no conflicting statement and the strict-later acceptance rule passing. Zero/multiple/conflict ⇒ unresolved or review. **Never** proximity, same-report-date, ordering, `/A`, or name inference. Decision 018 co-selection and the hard quota **8** unchanged |
| When M3.3-E0 may run | **Decision 081 §6 — R49.** The Decision 080 §13 verdict `E0_CAN_RUN_FAIL_CLOSED_BEFORE_ENRICHMENT` is accepted, **but E0 stays NOT AUTHORIZED** until **both** the Decision-081 sample has returned and been owner-adjudicated **and** the R46 correction has been implemented, independently reviewed, and owner-accepted. An owner sequencing gate, not a technical dependency claim |
| What network authority exists | **Decision 081 §7 — R50.** **ONE** bounded stage: SEC Complete Submission Text for the frozen sampled accessions only, `TARGET_SAMPLE_N` **125 max**, logical ceiling **125**, physical ceiling **250**, **2** attempts per accession, **1 sequential request per second**, no parallelism, no crawler behavior, SEC identity never printed, nothing outside the frozen sample, no off-`sec.gov` redirect. **Not** full-population acquisition |
| How the sample is drawn | **Decision 081 §§8.3–8.4.** Five frozen cohorts only, forms exactly `10-K/A` / `10-KT/A`, XBRL classes X0/X1/X2, deterministic ranking by ascending `sha256("d081-source-verification/1.0:" + accession_plain)` with no stochastic step. CORE 5 × 3 × **6** = **90**, plus oversamples **10** `10-KT/A` / **8** multi-registrant / **8** multiple-original / **8** zero-original / **1** missing-report-date. Undersized strata take all members; **no cross-stratum backfill**, so the final sample may be fewer than 125 |
| What must reconcile before any request | **Decision 081 §8.2** — the ephemeral Decision-079 population reproduction must return `REAL_RAW_TOTAL_AMENDMENT_CANDIDATES = 46912` and `FROZEN_COHORT_AMENDMENT_CANDIDATES = 20258`, or the session **STOPS before network** |
| What is measured | **Decision 081 §8.8 — M1–M10**: native `<ACCEPTANCE-DATETIME>` presence and strict-14-digit accession-bound validity; header accession and form; `AmendmentFlag`; `AmendmentDescription`; explicit amendment statement (**source-sufficiency only**); explicit original form/date/accession; the ZERO / EXACTLY_ONE / MULTIPLE lookup; and byte size |
| What the stage may never return | **Decision 081 §§8.9–8.10.** No `administrative` / `financial` / `narrative` classification of any real accession, and no `amends_original` written anywhere — only explicit-statement presence with its preserved span, and `ORIGINAL_LOOKUP_RESULT`. **No quota witness is created** |
| Whether a failing accession may be replaced | **Decision 081 §8.12 — no.** Every frozen sample accession appears exactly once including failures and absences; no substitution, no second sample, no post-retrieval edit; `SAMPLE_TOTALITY` is returned |
| What happens after the last request | **Decision 081 §8.13** — `NETWORK_AUTHORIZATION = SPENT / CLOSED`. No further SEC request may be made under Decision 081, no automatic enrichment, no "one more check" |
| What happens next | **Decision 081 §14** — execute the fixed verification **once**, then return to Sol/GPT. Results are not committed in that pass; E0, the multi-registrant correction, and enrichment all remain unstarted |

*(Current state: the fixed sample **has been executed and is owner-accepted** by accepted Decision 082
§2 — `SAMPLE_N` **108**, `SAMPLE_TOTALITY = PASS`, `NETWORK_AUTHORIZATION = SPENT / CLOSED`. **R46–R50
stand unchanged and Decision 081 is not rerun.** The executing-model deviation is recorded as
`D081_MODEL_DEVIATION_ACCEPTED_NO_RERUN`. The **R46** multi-registrant correction now has a written
implementation contract, **PENDING OWNER ACCEPTANCE** — see below.)*

## Decision 082 — ACCEPTED (D081 owner adjudication and the pre-E0 contracts)

[Decision 082](Decisions/decision_082_m3_3_d081_owner_adjudication_and_pre_e0_contracts.md)
(`ACCEPTED — OWNER D081 ADJUDICATION AND PRE-E0 CONTRACT FREEZE 2026-08-14`) is the **thirteenth M3.3
record**. It accepts the executed Decision-081 source-verification sample, freezes **R51**–**R57**,
and records **three design contracts as PENDING OWNER ACCEPTANCE**.

**It implements nothing** — no source, test, migration, schema, or config is touched. **It makes no
network request** and authorizes none (`REQUEST_CEILING = 0`). It closes neither real-path gate,
classifies **zero** real filings, resolves **zero** real parentage, and grants **no** quota credit.

| Question | Controlling record |
|---|---|
| Whether the executed D081 sample is accepted | **Decision 082 §2 — YES**, token `M3_3_DECISION_081_SOURCE_VERIFICATION_OWNER_ACCEPTED`. `SAMPLE_N` **108** (108 logical / 109 physical / 108 artifacts / 0 terminal absences), `SAMPLE_TOTALITY = PASS`, `NETWORK_AUTHORIZATION = SPENT / CLOSED`. Native 14-digit acceptance, header accession, and header form each **108/108**; `AmendmentDescription` nonempty **38/108**; explicit issuer-authored amendment statement **98/108**; any purpose-evidence source **101/108**; explicit original form **98/108**, filing date **98/108**, accession **0/108**. A sample of 108 rather than 125 is the **correct** outcome of the no-backfill rule, not a defect |
| How the frozen **M9** result is treated | **Decision 082 §2.1.** `EXACTLY_ONE` 50 / `ZERO` 38 / `MULTIPLE` 10 / `N/A` 10 is an **INSTRUMENT result**, **not** the final document-evidence linkage capability rate. Superseded for that purpose by **R53**. No category assigned, no `amendment_relationship` written, no quota witness created |
| The executing-model deviation | **Decision 082 §2.2 — `D081_MODEL_DEVIATION_ACCEPTED_NO_RERUN`.** Opus 5 was requested; Fable 5 executed. **NONBLOCKING PROCESS DEVIATION**: Decision 081 is **not rerun**, and the deterministic hash-frozen sample, ledger, artifacts, and measurements all stand |
| Status of the D079 compatible-original diagnostic | **Decision 082 §3 — R51.** 4677 / 42159 / 75 / 1 is **DEMOTED** from a frozen binding fact to a `HISTORICAL NON-GOVERNING AUDIT OBSERVATION` — never an E0 reconciliation gate, candidate or selection identity, quota or linkage evidence, or stop condition. **Decisions 079 and 080 are not rewritten**, and the rest of the frozen fact set (46912 / 20258) is untouched |
| The replacement diagnostic | **Decision 082 §4 — R52.** Union compatible originals (`10-K` / `10-KT`, exact `report_date`) across the **complete substantive registrant association set**, dedupe by canonical accession, classify ZERO / EXACTLY_ONE / MULTIPLE / NO_DATE. Measured **4286 / 42391 / 234 / 1**, summing to 46912. **Diagnostic only — ZERO linkage credit**, and it establishes no parentage, family identity, or quota contribution |
| How document assertions are extracted | **Decision 082 §5 — R53.** By **adjudication**, never by a regex or otherwise mechanical extractor. Six required fields (purpose span, original form, original filing date, original accession, source location, artifact SHA-256). **A fiscal-period end date is never substituted for an explicitly stated filing date.** The D081 extractor stays historical instrument evidence and **M9 is neither corrected nor rerun** |
| When the purpose gate may close | **Decision 082 §6 — R54.** Only on adjudicated witnesses for **each** of the three frozen categories, each with an accepted artifact SHA-256, exact span, protocol pass, and no unresolved conflict. This stage produces none, so `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` stays **OPEN** |
| When the linkage gate may close | **Decision 082 §7 — R55.** Only on **8 distinct substantive entities** whose amendments explicitly identify a compatible original form **and** an exact filing date or accession, resolve to **exactly one** original under the complete association set, carry no conflicting statement, and pass strict-later acceptance on the **R43** source. Witnesses need not become the selected pilot witnesses, and **no quota credit is persisted**. `M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` stays **OPEN** |
| Whether the source architecture works | **Decision 082 §8 — R56.** `COMPLETE_SUBMISSION_TEXT_SOURCE_FEASIBILITY = PROVED` and `NATIVE_ACCEPTANCE_SOURCE_FEASIBILITY = PROVED`. The CST is the **preferred single-artifact source**; structured XBRL is **supplementary only**; an **XBRL-only architecture is rejected** — the 38/108 `AmendmentDescription` rate against 98/108 issuer statements is the measured reason. **No further acquisition is authorized** |
| Whether **X1** stays a mandatory stratum | **Decision 082 §9 — R57. No.** `has_xbrl` true with `has_inline_xbrl` false is absent in `prospective` and `monitoring` and has one member in `primary_test`. XBRL state may still be recorded as a covariate; the D081 sample is unchanged |
| The **R46** implementation contract | **Decision 082 §10 — PENDING OWNER ACCEPTANCE, not implemented.** Answers A–L: relational representation with `anchor` permitted only for an **established** sole registrant; the census scalar `NULL` otherwise; a new `census_accession_registrants` relation; migration **`0014`** with eight changes over empty tables; **five** identities consuming the false singleton (tie-break, accession-table digest, registrant-table digest, snapshot digest, and transitively selection identity and the manifest root); byte-for-byte single-registrant preservation recommended via a non-CIK sentinel; Decision 072 R24 preserved and its R23 multi-registrant predicate restated with identical extension; the quota witness already accession-keyed and needing no anchor; an empty-table precondition and revert-and-rebuild rollback; and **fourteen** mutation tests. **Five open owner items**, including whether Decision 021 manifest **item 48 "anchor CIK"** may become nullable |
| The verified-evidence schema contract | **Decision 082 §11 — PENDING OWNER ACCEPTANCE, not implemented.** Four new append-only relations (`document_artifacts`, `document_review_records`, `document_review_spans`, `document_adjudicated_evidence`) plus the migration-`0009` CHECK widening that `verified` requires. **Exact identity implication:** adding a column to an existing digest tuple changes that digest even when the column is `NULL` everywhere, so the evidence layer must live entirely in **new** hashing domains — which leaves every accepted synthetic I/R identity byte-unchanged. Proposed migration **`0015`**, separate from `0014` and ordered after it |
| The future adjudication protocol | **Decision 082 §12 — PENDING OWNER ACCEPTANCE, not executed.** Sequential **Review A → Review B → adjudication** in separate fresh epochs over the **already stored** D081 artifacts at **zero** new SEC requests; no parallel sessions required. Defines review fields, allowed abstentions, the three verbatim categories, extraction rules X-1–X-6, span-citation and fail-closed rules, agreement and third-adjudication rules, five frozen hashes, and both feasibility-witness calculations. **No real filing is classified** |
| What happens next | **Decision 082 §15** — **owner adjudication of the three contracts**, and nothing else. No session may begin the R46 implementation, write any migration, execute any document review, or begin M3.3-E0 on the strength of this record |

*(Current state: all three contracts are **owner accepted** by accepted Decision 083 §2. The **R46**
contract was implemented and is now **owner accepted** (Decision 087 §2); the **verified-evidence
schema** contract is now **implementation authorized** with `MIGRATION_AUTHORIZED = 0015 only`
(Decision 087 §4); the **adjudication protocol** remains **execution deferred** — see below.)*

## Decision 083 — ACCEPTED (pre-E0 multi-registrant relational correction)

[Decision 083](Decisions/decision_083_m3_3_pre_e0_multi_registrant_correction.md)
(`ACCEPTED — OWNER ACCEPTANCE OF THE DECISION-082 CONTRACTS AND R46 IMPLEMENTATION AUTHORIZATION
2026-08-14`) is the **fourteenth M3.3 record**. It accepts the three Decision-082 contracts, freezes
**R58**–**R64**, and authorizes **exactly one** bounded implementation: the **R46** multi-registrant
relational correction and migration `0014`.

**It authorizes nothing else.** Migration `0015`, the verified-evidence schema, Review A, Review B,
the document adjudication, **M3.3-E0**, **M3.3-E1**, **M3.3-E2**, and **M3.4** all remain
unauthorized, and network, SEC, and HTTP authority remains **NONE** at `REQUEST_CEILING = 0`.

| Question | Controlling record |
|---|---|
| Whether the Decision-082 contracts are accepted | **Decision 083 §2 — YES**, token `M3_3_DECISION_082_PRE_E0_CONTRACTS_OWNER_ACCEPTED`. The pushed Decision-082 commit `5231359f…` is the **sole** Decision-082 execution; it is not rerun, replaced, rolled back, or duplicated, and the duplicate-delivery condition is **CLOSED**. `R46_MULTI_REGISTRANT_IMPLEMENTATION_CONTRACT = OWNER ACCEPTED / IMPLEMENTATION AUTHORIZED`; the other two are **OWNER ACCEPTED** with implementation and execution **DEFERRED** |
| How a multi-registrant accession is represented | **Decision 083 §3 — R58**, adjudicating Decision 082 §10.15 item 1. The new `census_accession_registrants` relation is adopted and is **authoritative**; an established sole registrant may occupy the scalar, an established set of cardinality > 1 forces the scalar **`NULL`**, and every listed anchor-selection heuristic — first/last write, min/max CIK, archive, record, hash, submissions occurrence, full-index row order, submitter, agent, URL, filename — is **prohibited** |
| What an incomplete registrant set does | **Decision 083 §4 — R59**, adjudicating Decision 082 §10.15 item 5. `registrant_set_completeness = unestablished` **blocks accession candidacy entirely**, not merely the scalar anchor, and fails closed with an explicit accepted reason. **Silence is never proof of a sole registrant** |
| What occupies the tie-break registrant slot | **Decision 083 §5 — R60**, adjudicating Decision 082 §10.15 item 2 as **H-a**. The exact sentinel `MULTI_REGISTRANT_NO_SINGLETON` is used **only** for an established set of cardinality > 1; it is never a CIK, never persisted in a CIK column, never an entity, and never a locator. Established single-registrant preimages stay **byte-for-byte identical**; unestablished sets hash nothing |
| What manifest item 48 asserts | **Decision 083 §6 — R61**, adjudicating Decision 082 §10.15 item 3. Decision 021 is **not rewritten**; prospectively item 48 is the factual CIK at cardinality 1 and **`NULL`** above it, with `candidate_registrant_table_sha256` binding the relation and **no fabricated anchor**. The five identity consumers **E1–E5** are accepted as prospectively changeable; `snapshot_id`, `entity_tie_break_sha256`, and the **R15**/**R16** preimages are unaffected, and a wider impact is a **STOP** |
| How a joint filing is attributed | **Decision 083 §7 — R62**, adjudicating Decision 082 §10.15 item 4 as **every substantive registrant**. Accession-domain calculations still deduplicate one joint filing as one accession; entity-domain metrics admit each truthful entity under their **existing** definitions; **no quota changes its declared domain**, and Decision 072's hard multi-registrant quota of **2** is unchanged |
| The verified-evidence schema | **Decision 083 §8 — R63. OWNER ACCEPTED / IMPLEMENTATION DEFERRED.** `document_artifacts` is a **catalog metadata relation** with no absolute private path and no `EV_ROOT` exposure; `amends_original` is **reused** with strength carried by `evidence_level = 'verified'`, so no second semantic state is invented; `verified` applies **only** to amendment purpose and linkage in M3.3 v1, enforced by the future migration; reviewer identity is a durable **opaque** review-epoch identifier plus role and model. **Migration `0015` is NOT authorized** |
| The document adjudication protocol | **Decision 083 §9 — R64. OWNER ACCEPTED / EXECUTION DEFERRED.** `PROTOCOL_VERSION m3.3-document-evidence/1.0` over **all 108** frozen D081 artifacts at **zero** new SEC requests; sequential Review A (Opus 5) → Review B (Fable 5) → adjudication (Opus 5), each a fresh epoch, the adjudication seeing A + B only once both are hash-frozen. **The independence unit is the epoch plus the frozen-input boundary**, so one operator may launch all three. An unresolvable conflict is **TERMINAL** for that protocol version and artifact set |
| What is authorized to be built | **Decision 083 §10 — the R46 correction and migration `0014` only.** `0014` is prospective and pre-E0: it never mutates the accepted private M3.2 catalog, and non-empty state requiring destructive reinterpretation is a **STOP**. Historical D070–D077 rehearsal evidence is **immutable**; affected synthetic scenarios get **new** expectations; `SINGLE_REGISTRANT_UNEXPECTED_IDENTITY_DELTAS = 0`; and all fourteen **MR-M1**–**MR-M14** protections are implemented at their exact definitions with **demonstrated** effectiveness |
| What happens next | **Decision 083 §13** — implement **R46** and `0014`, then **return to Sol/GPT**. Successful implementation is **not** acceptance: **R49** condition B needs a fresh independent review **and** owner acceptance. The implementing session does not self-review for formal acceptance |

*(Current state: the **R46** implementation and migration `0014` are **written and proved** but hit
one narrow owner-action stop at final validation. Accepted Decision 084 disposes of it — see below.
**R63**'s implementation deferral has since been **lifted** by accepted Decision 087 §4, so migration
`0015` is now authorized; **R64** remains **execution deferred**.)*

## Decision 084 — ACCEPTED (bounded continuation of the D083 correction)

[Decision 084](Decisions/decision_084_m3_3_d083_bounded_owner_action_continuation.md)
(`ACCEPTED — OWNER BOUNDED CONTINUATION OF THE D083 IMPLEMENTATION 2026-08-15`) is the **fifteenth
M3.3 record**. It resolves the single stop the Decision-083 implementation hit, and **nothing else**.

**It does not modify Decision 083**, and it does not redo, revert, or re-derive the implementation:
the existing uncommitted working tree is the continuation baseline and is **preserved**.

| Question | Controlling record |
|---|---|
| Why a continuation was needed at all | **Decision 084 §1.** The **R46** implementation is complete and proved — **MR-M1**–**MR-M14** all pass, **E1**–**E8** all pass, `SINGLE_REGISTRANT_UNEXPECTED_IDENTITY_DELTAS = 0`, the affected identity inventory did **not** exceed **E1**–**E5**, and every static gate passes — but migration `0014` moved the schema chain head past a constant living in a path Decision 083 §11 prohibited, so `make check-fast` could not pass without an owner ruling |
| The migration chain head | **Decision 084 §2 — R65.** `FINAL_MIGRATION_VERSION` in `src/disclosure_drift/m3/acquisition.py` moves **13 → 14** — that constant and **nothing else** in that file. It records a schema fact: it does **not** reopen M3.2, authorize acquisition, authorize network access, authorize applying `0014` to the accepted private M3.2 operational catalog, authorize writing accepted M3.2 evidence, move `m3.2-complete`, or grant **M3.3-E0**. Migration `0014` stays **prospective and pre-E0**, and the private catalog stays **untouched** |
| The joint support-pair caller | **Decision 084 §3 — R66.** Decision 083's **MINOR-1** is a correction-stage defect. `src/disclosure_drift/m3/offline_execution.py` is authorized **strictly at the `paired_accessions_from_rows` caller**, so a jointly filed 2009/2010 leg reaches its truthful substantive entities with **no arbitrary scalar anchor**; single-registrant behaviour stays **byte-for-byte identical**; an **unestablished** set **fails closed at zero credit**; and min/max CIK, first-write, submitter, row order, date proximity, name, ticker, and hash order are all prohibited routes. The pair quota, eligible forms, the 2009/2010 rule, and the methodology are **unchanged** |
| The narrower identity implementation | **Decision 084 §4 — R67. ACCEPTED.** `src/disclosure_drift/m3/candidate_identity.py` is **not** modified solely to widen `ACCESSION_TABLE_COLUMNS`, `REGISTRANT_TABLE_COLUMNS`, or `SNAPSHOT_CONTENT_FIELDS`, because widening them would move identities for **pure single-registrant** snapshots with no semantic change. The accepted stronger requirement: a pure single-registrant snapshot keeps **E1**–**E5** **byte-identical**, and a multi-registrant snapshot moves **only** what **R58**–**R62** require. The independent review **must verify** the relational set is genuinely bound — or the session **STOPS** |
| What happens next | **Decision 084 §6** — apply **R65** and **R66**, validate, commit the complete implementation as one commit parented on this governance commit, push once, and **return to Sol/GPT**. Migration `0015`, Review A, Review B, the adjudication, **E0**, **E1**, **E2**, and **M3.4** all remain unauthorized at `REQUEST_CEILING` 0 |

*(Current state: the **R46** implementation and migration `0014` are **committed** at
`09ee4422…` and the fresh formal independent acceptance review of that target **FAILED**. Accepted
Decision 085 disposes of its findings — see below.)*

## Decision 085 — ACCEPTED (D083/D084 formal-review findings and their correction)

[Decision 085](Decisions/decision_085_m3_3_d083_d084_formal_review_corrections.md)
(`ACCEPTED — OWNER ACCEPTANCE OF THE FORMAL REVIEW FINDINGS AND CORRECTION AUTHORIZATION
2026-08-15`) is the **sixteenth M3.3 record**. It accepts a **failed** review as a truthful review
result and authorizes the correction of **exactly its five findings**.

**It reopens nothing.** Decisions 083 and 084 are **not modified**, **R58**–**R67** are **not**
redesigned, the reviewed target `09ee4422…` **stands as committed**, and the frozen review artifact
is **immutable**.

| Question | Controlling record |
|---|---|
| What the formal review returned | **Decision 085 §2.** **FAIL** at **BLOCKER 0 / MAJOR 1 / MINOR 4** against frozen target `09ee4422…`, artifact [`m3_3_d083_d084_r46_formal_independent_acceptance_09ee442.md`](m3/reviews/m3_3_d083_d084_r46_formal_independent_acceptance_09ee442.md). Production behaviour was independently confirmed faithful to **R58**–**R62** and **R65**–**R67**, so the acceptance failure is primarily a **verification defect** |
| Which findings are corrected, and which are not | **Decision 085 §3.** **M-1** accepted, correction required, **acceptance-gating**; **MIN-1**–**MIN-4** accepted, correct now; **OBS-1**–**OBS-6** **not** authorized for correction. No other defect is corrected unless discovered while fixing one of the five and inseparable from it — a material unrelated defect is a **STOP** |
| The MR-M10 builder protection | **Decision 085 §4 — M-1.** The shipped MR-M10 test exercises only the freeze/schema backstop, and the exact derivation mutant inside `derive_candidate_snapshot` — absent establishment evidence silently read as **one** substantive registrant — **survived** every builder-invoking test. A dedicated **builder-level** test must exclude such an accession before snapshot entry, record `PILOT_ACCESSION_REGISTRANT_SET_UNESTABLISHED`, grant **no** entity/history/quota credit, and **fabricate no** scalar registrant; the exact mutant is then executed and must be **KILLED**. **MR-M10A** (builder) and **MR-M10B** (schema/freeze) are both retained |
| The migration comments | **Decision 085 §5 — MIN-1.** Migration `0014`'s claim that the new relational columns enter `REGISTRANT_TABLE_COLUMNS` is **false as to mechanism** under **R67**: the relational set is governed through the existing candidate registrant row representation and its digest. Only the comments change — no digest tuple is widened and **no executable semantics change** |
| The established-with-zero-relation state | **Decision 085 §6 — MIN-2.** The guard covers **UPDATE** only, so an **INSERT** can assert `established` with zero substantive relations. Because `0014` is not owner-accepted and touches no real E0 state, it is corrected **prospectively** so that false state cannot survive the completed transaction — the **real writer transaction is inspected first**, insertion ordering is respected, no impossible immediate trigger is created, the **narrowest** mechanism is used, **no fake registrant** is introduced, and probes **A–G** are required |
| The re-baseline provenance | **Decision 085 §7 — MIN-3.** An unverifiable "before" literal is **not retained**. The pre-correction state is independently reproduced from a **disposable** worktree of `6fdec2ed…`; either the exact reproduced value replaces the literal, or the false historical framing is removed. **No predecessor hash is fabricated**, every retained literal carries reproducible provenance, and `UNVERIFIABLE_PRECORRECTION_DIGESTS = 0` |
| The reserve per-CIK cap | **Decision 085 §8 — MIN-4.** `reserve_selector._caps_preserved` must attach an established multi-registrant bundle accession to **every** truthful substantive registrant for per-CIK / entity-domain cap accounting — never to the replacement, an anchor, the first registrant, the min/max CIK, or the submitter — while **accession-domain accounting still counts the filing once**. The cap value and research policy are **unchanged**; a policy-constant change is a **STOP** |
| What happens next | **Decision 085 §12** — commit this record as one governance-only commit, implement only **M-1** and **MIN-1**–**MIN-4**, re-run **MR-M1**–**MR-M14** including the exact MR-M10 mutant, run targeted and static validation and exactly one `make check-fast`, commit once, push once, and **return to Sol/GPT**. **R49** condition B stays **unsatisfied** until a fresh **genuine Claude Fable 5 maximum** review passes and Sol/GPT accepts; migration `0015`, Review A, Review B, the adjudication, **E0**, **E1**, **E2**, and **M3.4** all remain unauthorized at `REQUEST_CEILING` 0 |

*(Current state: the Decision-085 correction is **implemented and committed** at `1c5b0150…`, and
accepted Decision 086 adjudicates it — see below.)*

## Decision 086 — ACCEPTED (D085 correction adjudication and genuine Fable rereview)

[Decision 086](Decisions/decision_086_m3_3_d085_correction_owner_adjudication_and_fable_rereview.md)
(`ACCEPTED — OWNER ADJUDICATION OF THE D085 CORRECTIONS AND GENUINE FABLE REREVIEW AUTHORIZATION
2026-08-15`) is the **seventeenth M3.3 record**. It adjudicates a completed correction and commissions
the review that can accept it.

**It is governance only**, and it is **not** final owner acceptance of the R46 implementation.
Decisions 083, 084, and 085 are **not modified**, and no implementation byte changes with it.

| Question | Controlling record |
|---|---|
| Whether the D085 corrections stand | **Decision 086 §2.** The correction report is accepted as **truthful** and all five findings are **CLOSED FOR REREVIEW** — **M-1** on `MR_M10_DERIVATION_MUTANT = KILLED` with **MR-M10A** existing and **MR-M10B** retained, and **MIN-1**–**MIN-4** closed. The correction epoch reported no BLOCKER, MAJOR, or MINOR of its own. **This is acceptance of the corrections FOR REREVIEW, not final R46 acceptance** |
| The migration-checksum identity movement | **Decision 086 §3 — R68. ACCEPTED.** Correcting migration `0014`'s bytes moved the reserve-bearing fixture's `selector_policy_sha256`, `root_manifest_sha256`, and `manifest_id` along the accepted checksum → `migration_chain_sha256` → `selector_policy_sha256` → root/`manifest_id` path. Classified an **expected governed policy-binding consequence** — **not** a new R46 registrant-semantic identity consumer, **not** an expansion beyond **E1**–**E5**, **not** corruption, **not** a methodology change. R46 semantic movement and migration-policy movement stay **separately attributable**. The rereviewer must verify only those three moved and the **other seven components are byte-identical** (including `candidate_tables_sha256` and `selection_result_sha256`), and must **report** anything else that moved. **No implementation changes because of this ruling** |
| The duplicate final validation run | **Decision 086 §4 — R69. NONBLOCKING PROCESS DEVIATION.** Two `make check-fast` invocations on the identical unchanged tree, both exit 0, the second only to recover scrolled-past output, no tree edit between them and no gate iterated toward green. **No correction; Decision 085 is not rerun.** The normal rule stands: one routine final `make check-fast` per final tree unless a tree change, a nondeterminism investigation, or an authorized diagnostic need requires another |
| Which model the next formal review must be | **Decision 086 §5.** **Claude Fable 5 at maximum effort, in a genuine epoch.** The reviewer reports its actual harness/model identity **before** substantive review and **STOPS** with `M3_3_D085_R46_REREVIEW_INVALID_NOT_GENUINE_FABLE` on any mismatch. **Opus is never substituted for Fable**, and a mismatch is never handled by continuing and disclosing it afterward. The prior review's findings remain valid evidence even though its epoch did not satisfy this requirement |
| What the rereview targets | **Decision 086 §6.** Frozen target `1c5b0150…` at tree `1994e8bf…`; **this governance commit is authority about that target and never becomes it**. The rereviewer compares the original reviewed target `09ee4422…` to the corrected one, verifies the correction is **bounded** to **M-1** and **MIN-1**–**MIN-4** plus truthful governance publication, and **revalidates every formal acceptance property, not only the delta** |
| What happens next | **Decision 086 §8** — commit this record, push once, and **return to Sol/GPT**. The Fable rereview is **not** started in the Opus session that produced it. **R49** condition B stays **unsatisfied** until a genuine Fable 5 maximum review **passes** and Sol/GPT accepts the corrected implementation; migration `0015`, Review A, Review B, the adjudication, **E0**, **E1**, **E2**, and **M3.4** all remain unauthorized at `REQUEST_CEILING` 0 |

*(Current state: the commissioned genuine Fable 5 maximum rereview **ran and PASSED**, and Sol/GPT
**accepted** the corrected R46 implementation by accepted Decision 087 — see below.)*

## Decision 087 — ACCEPTED (final R46 owner acceptance and the verified-evidence schema authorization)

[Decision 087](Decisions/decision_087_m3_3_r46_owner_acceptance_and_verified_evidence_schema.md)
(`ACCEPTED — OWNER FINAL R46 ACCEPTANCE AND VERIFIED-EVIDENCE SCHEMA IMPLEMENTATION AUTHORIZATION
2026-08-15`) is the **eighteenth M3.3 record**. It closes the R46 correction and opens exactly one new
implementation stage.

**It grants no execution authority.** No document review runs, no filing is classified, no real
amendment parentage is resolved, no quota credit is granted, no feasibility gate closes, no real
offline parse begins, and no network, SEC, or HTTP request is made.

| Question | Controlling record |
|---|---|
| Whether R46 is accepted | **Decision 087 §2. ACCEPTED.** The corrected implementation frozen at `1c5b0150…` (tree `1994e8bf…`) is owner-accepted on the genuine Fable 5 maximum rereview's **PASS** at BLOCKER 0 / MAJOR 0 / MINOR 0. `M3_3_R49_CONDITION_B_SATISFIED`; `M3_3_PRE_E0_MULTI_REGISTRANT_HOLD_CLOSED`. No further R46 correction or review is required unless a later stage finds a genuinely **new** defect |
| What that acceptance does **not** grant | **Decision 087 §3.** R49 condition B is one precondition, not E0 authorization. **M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 all remain NOT AUTHORIZED**; network/SEC/HTTP is **NONE** at `REQUEST_CEILING = 0` |
| Whether the verified-evidence schema may be built | **Decision 087 §4.** The Decision 083 **R63** implementation deferral is **LIFTED**. `VERIFIED_EVIDENCE_SCHEMA_CONTRACT = OWNER ACCEPTED / IMPLEMENTATION AUTHORIZED`; `MIGRATION_AUTHORIZED = 0015 only`, separate from `0014`, which is neither rewritten nor squashed |
| What the four relations mean | **Decision 087 §5**, restating Decision 083 **R63** items A–D: `document_artifacts` is **catalog metadata only** with the artifact bytes staying in the private evidence root and **no `EV_ROOT` path persisted**; `document_review_records` must **mechanically distinguish** Review A / Review B / adjudication by durable **opaque epoch identifiers** plus role and model, with no personal name; `document_review_spans` carries exact source-span provenance with **no classifier invented**; `document_adjudicated_evidence` authorizes `verified` **only** for amendment purpose and linkage/explicit-original |
| Linkage semantics | **Decision 087 §6.** **No `verified_amends_original` state is invented.** The relationship reuses `amendment_linkage_state = amends_original`; verification strength lives in `evidence_level = verified` with its provenance |
| The evidence-level widening | **Decision 087 §7.** The Decision 080 §9.3 widening is implemented **for the authorized amendment-purpose dimension only**. No other dimension's validation is weakened, and no existing synthetic or rehearsal row is reinterpreted |
| Immutability | **Decision 087 §8.** Append-only and immutable once frozen, at the Decision 082 §11.2 statement. **No delete/update flexibility is invented for convenience** |
| Identity discipline | **Decision 087 §9.** New hash domains only, through the existing `release/hashing.py`; **no frozen column tuple widened** (accepted **R67**); the migration-chain movement along the **R68** path (`selector_policy_sha256`, `root_manifest_sha256`, `manifest_id`, block-5 row count) must be enumerated and distinguished from evidence-content movement; widening an owner-frozen candidate identity tuple is a **STOP** |
| Which paths the implementation may touch | **Decision 087 §13.** Decision 082 §11 states no path list, so §13 supplies one. It includes `FINAL_MIGRATION_VERSION` **14 → 15** in `acquisition.py` — that constant and nothing else in that file — on the identical owner interpretation accepted for **R65** |
| The required adversarial matrix | **Decision 087 §14 — VE-M1 … VE-M14**, demonstrated rather than named |
| What happens next | **Decision 087 §18** — implement `0015` and its authorized infrastructure, then **return to Sol/GPT**. The implementing session does **not** self-review and does **not** start Review A, Review B, the adjudication, or **E0** |

*(Current state: **R46 is owner accepted**, `M3_3_R49_CONDITION_B_SATISFIED`, and the pre-E0
multi-registrant hold is **closed**. Migration `0015` and the verified-evidence infrastructure were
implemented under this authority, and the fresh independent review of that implementation returned
**FAIL** — see Decision 088 below.)*

## Decision 088 — ACCEPTED (D087 review adjudication and the bounded correction)

[Decision 088](Decisions/decision_088_m3_3_d087_verified_evidence_review_corrections.md)
(`ACCEPTED — OWNER ADJUDICATION OF THE D087 INDEPENDENT REVIEW AND BOUNDED CORRECTION AUTHORIZATION
2026-08-15`) is the **nineteenth M3.3 record**. It adjudicates the failed independent review of the
Decision 087 implementation and authorizes exactly one bounded correction stage.

**It accepts nothing and grants no execution authority.** The verified-evidence schema is **not**
owner-accepted, no document review runs, no real evidence is created, and no network, SEC, or HTTP
request is made.

| Question | Controlling record |
|---|---|
| What the D087 independent review found | **Decision 088 §1. `FAIL` — BLOCKER 0 / MAJOR 1 / MINOR 3 / OBSERVATION 3** at frozen target `8c13fc79…` (tree `80dc6c05…`), token `M3_3_DECISION_087_VERIFIED_EVIDENCE_SCHEMA_INDEPENDENT_REVIEW_FAIL`. **The verdict is frozen and immutable**, reached before any correction authority existed. The review also confirmed the accepted architecture is sound, so **no redesign is authorized** |
| How each finding is disposed | **Decision 088 §2.** **M-1** accepted, correction required, **acceptance-gating**; **MIN-1**, **MIN-2**, **MIN-3** accepted, correct now; **OBS-2** comment only; **OBS-3** strengthen validation now; **OBS-1** non-gating and **deferred** |
| Why `INSERT OR REPLACE` is a defect and how it is closed | **Decision 088 §3.** The implicit delete fires no `BEFORE DELETE` trigger without `PRAGMA recursive_triggers`, which this project never sets. Closed by the accepted migration-`0013` **`BEFORE INSERT` replacement-guard** pattern over **every** unique route of **all four** relations, refusing `INSERT OR REPLACE`, a duplicate `INSERT`, and a silent `INSERT OR IGNORE`. The `BEFORE UPDATE`/`BEFORE DELETE` protections are **kept** |
| Cross-accession artifact binding | **Decision 088 §4.** Reviews and adjudications must bind an artifact whose **registered** accession matches their own. **No new accession identity is invented** |
| What `agreed` means | **Decision 088 §5.** Both contributing reviews must be **non-abstaining** and carry the asserted adjudicated value per kind (Decision 082 §12.6). **Abstention is not turned into a negative assertion.** The `verified` ⇒ `agreed`/`resolved` CHECK gains a **dedicated negative test** |
| The verified-candidate re-point door | **Decision 088 §6.** The guard must also fire when `accession_plain` changes while the level stays `verified` — by naming the column, **not** by candidate-identity redesign. Verified applicability is **not** widened |
| OBS-2 and OBS-3 | **Decision 088 §7.** The `0015` §1 comment is corrected (**comment only**); `span_location` becomes strict `bytes:<decimal>-<decimal>`, with **no fuzzy source-location semantics** |
| OBS-1's status | **Decision 088 §8.** **NON-GATING / DEFERRED / OPEN.** It must **never** be reported as fixed or closed |
| Who may correct, and who may accept | **Decision 088 §9.** The failed review's own epoch is reused **only** as the correction executor and is **not eligible** to accept its own corrected target. The acceptance rereview must be a **fresh `/clear` epoch** |
| Which paths the correction may touch | **Decision 088 §10.** Migration `0015` is corrected **in place**; **migration `0016` is not authorized** |
| The expected identity movement | **Decision 088 §11.** Only the accepted **R68** chain path may move; eight named components must stay **byte-identical**, and anything else moving is a **STOP** |
| The required adversarial matrix | **Decision 088 §12 — VE-M1 … VE-M14 re-run, plus VE-R1 … VE-R10**, demonstrated rather than named |
| What happens next | **Decision 088 §15** — correct the six findings, then **return to Sol/GPT**. **Successful correction is not acceptance** |

*(Current state: the D087 implementation **failed** its independent review and was corrected under
this authority. The corrections are now owner-adjudicated **for rereview** — see Decision 089
below.)*

## Decision 089 — ACCEPTED (D088 correction adjudication and the fresh rereview)

[Decision 089](Decisions/decision_089_m3_3_d088_correction_owner_adjudication_and_rereview.md)
(`ACCEPTED — OWNER ADJUDICATION OF THE D088 CORRECTIONS AND FRESH REREVIEW AUTHORIZATION
2026-08-15`) is the **twentieth M3.3 record**. It adjudicates the Decision 088 corrections and
commissions the fresh independent acceptance rereview.

**It accepts no schema and grants no execution authority.** No document review runs, no real
evidence is created, no migration is authorized, and no network, SEC, or HTTP request is made.

| Question | Controlling record |
|---|---|
| What the D088 corrections bought | **Decision 089 §2.** Acceptance of the **correction work, for rereview only** — `M3_3_DECISION_088_VERIFIED_EVIDENCE_CORRECTIONS_OWNER_ACCEPTED_FOR_REREVIEW`. **Not** final acceptance of the schema |
| What "closed for rereview" means | **Decision 089 §§3–4.** M-1, MIN-1, MIN-2, and MIN-3 are **CLOSED FOR REREVIEW**; OBS-2 and OBS-3 are **CLOSED**. The fresh reviewer **inherits no conclusion** and must independently re-prove the replacement door, both sides of the cross-accession binding, the `agreed`-state rule, and the candidate re-point guard |
| OBS-1's status | **Decision 089 §5. OPEN / NON-GATING / DEFERRED**, no correction authorized. The reviewer **confirms rather than assumes** its four mitigations, and **classifies any defect normally** if they prove false |
| OBS-A's status | **Decision 089 §6. OPEN FOR FRESH CONTRACT REREVIEW** — neither pre-accepted nor pre-condemned. The reviewer reads Decision 082 §§12.2/12.5/12.6, Decision 083 **R64**, and Decision 080 **AP-1**, evaluates the four abstention cases, and decides from the **contract** — **symmetry with `agreed` is not itself an argument**. MINOR or MAJOR on actual governed-state impact, or `OBS-A = CLOSED / NON-DEFECT` |
| OBS-B's status | **Decision 089 §7. ACCEPTED NON-DEFECT OBSERVATION.** The hard-to-reach `document_adjudicated_evidence_requires_bound_artifact` **may remain** as defence in depth and is **not removed because another guard fires first**; no reachability requirement is imposed for style |
| The expected identity movement | **Decision 089 §8.** Only the accepted policy chain may move, and the reviewer **independently reproduces** that the eight substantive manifest components stayed byte-identical. **No additional movement is authorized** |
| What the rereview targets, and how widely | **Decision 089 §9.** Target `746648285ec84d54a2ed7deaebc73f5c64b89d3d` (tree `1afd1c3b…`), compared against `8c13fc79…`. **The rereview is not limited to the correction delta** — the **full** verified-evidence acceptance boundary is revalidated |
| Who may perform it | **Decision 089 §10.** **Claude Fable 5, maximum effort, a fresh `/clear` epoch.** The session that reviewed and then corrected this target **must not** perform the rereview, and no conclusion of that session is inherited |
| What happens next | **Decision 089 §12** — run the fresh rereview, then return to Sol/GPT. Document Review A needs **both** a rereview **PASS** and **Sol/GPT final owner acceptance** |

*(Current state: the commissioned rereview **ran and PASSED** at BLOCKER 0 / MAJOR 0 / MINOR 0 /
OBSERVATION 4 (token `M3_3_D088_VERIFIED_EVIDENCE_FRESH_REREVIEW_PASSED_READY_FOR_OWNER_ACCEPTANCE`,
immutable artifact `Docs/m3/reviews/m3_3_d088_verified_evidence_fresh_rereview_7466482.md`), with
OBS-A determined **CLOSED / NON-DEFECT** and OBS-1 confirmed deferred — and **Sol/GPT then accepted
the schema and authorized Document Review A. See Decision 090 below.**)*

## Decision 090 — ACCEPTED (verified-evidence final acceptance and Review A authorization)

[Decision 090](Decisions/decision_090_m3_3_verified_evidence_owner_acceptance_and_review_a_authorization.md)
(`ACCEPTED — OWNER FINAL VERIFIED-EVIDENCE ACCEPTANCE AND DOCUMENT REVIEW A AUTHORIZATION
2026-08-15`) is the **twenty-first M3.3 record**. It accepts the corrected verified-evidence
infrastructure on the fresh rereview's PASS, and authorizes Document Review A.

**It executes nothing.** No document is reviewed by the record, no real evidence row is written, no
migration is authorized, and no network, SEC, or HTTP request is made. The recording governance
session does not execute Review A.

| Question | Controlling record |
|---|---|
| What was accepted, and on what basis | **Decision 090 §2.** The corrected infrastructure frozen at `746648285ec84d54a2ed7deaebc73f5c64b89d3d` (tree `1afd1c3b…`), on the fresh Fable 5 maximum rereview's **PASS at B0 / M0 / MIN0** — `M3_3_D088_VERIFIED_EVIDENCE_SCHEMA_OWNER_ACCEPTED`, `M3_3_MIGRATION_0015_OWNER_ACCEPTED`, `M3_3_VERIFIED_EVIDENCE_INFRASTRUCTURE_COMPLETE`. **No further D087/D088 correction or review is required** absent a genuinely new defect |
| The four observations | **Decision 090 §3.** **OBS-1** OPEN / DEFERRED / NON-GATING — never silently closed; **OBS-A** CLOSED / NON-DEFECT (faithful to the D082 §12.6 / R64 / AP-1 routing); **OBS-B** accepted non-defect, kept as defence in depth; **OBS-C** accepted non-defect — agreement consistency is intentionally per-kind/value-scoped, and auxiliary-assertion disagreement belongs to the frozen R64/AP-7 protocol |
| The frozen protocol boundary | **Decision 090 §4.** `m3.3-document-evidence/1.0` over **exactly** the 108 frozen D081 artifacts; Review A Opus 5 max, Review B Fable 5 max, adjudication Opus 5 max — three distinct fresh epochs; A and B mutually blind, adjudication seeing both only after their freeze |
| What Review A may do | **Decision 090 §5.** OFFLINE review of the 108 frozen artifacts, one fresh Opus 5 maximum epoch, no subagents or delegation; ONLY the accepted M3.3-v1 questions (purpose over the frozen three categories; explicit-original evidence under X-1…X-6); every positive assertion span-backed; abstention preferable to inference; governed schema rows with an opaque epoch and no personal identity; frozen and digest-sealed **before Review B begins**; totality 108/108 or STOP |
| What Review A may read | **Decision 090 §§5.3, 6.** The frozen artifact set and binding metadata only — READ-only private-root authority for the execution epoch, path never printed or persisted; no Review B/adjudication output, no answer set, no inherited D081 label; no SEC, no HTTP, no acquisition, no E0 |
| What Review A does not do | **Decision 090 §7.** Closes no feasibility gate, grants no quota credit, authorizes nothing downstream; its diagnostics are labeled **REVIEW-A-ONLY** |
| What stays unauthorized | **Decision 090 §8.** Review B, the adjudication, **M3.3-E0**, **E1**, **E2**, **M3.4**, all network/SEC/HTTP (`REQUEST_CEILING = 0`), and migration `0016` |
| What happens next | **Decision 090 §9** — execute Review A in a fresh Claude Opus 5 maximum epoch, then return to Sol/GPT |

*(Current state: **the §4/§5 dual-Claude execution workflow was prospectively superseded before any
review began — see Decision 091 below.** The schema/migration acceptance and all four observation
dispositions recorded here remain fully valid. The controlling execution protocol is now one Claude
Opus 5 maximum review followed by Sol/GPT owner adjudication.)*

## Decision 091 — ACCEPTED (the single-pass document-evidence protocol)

[Decision 091](Decisions/decision_091_m3_3_single_pass_document_evidence_protocol.md)
(`ACCEPTED — OWNER PROTOCOL CORRECTION: SINGLE-PASS DOCUMENT-EVIDENCE REVIEW 2026-08-15`) is the
**twenty-second M3.3 record**. It prospectively retires the dual-Claude Review A → Review B →
Claude-adjudication execution workflow — **before any review began, with zero real review rows in
existence** — and adopts one Claude Opus 5 maximum review followed by **Sol/GPT owner
adjudication**.

**It executes nothing and reopens nothing.** Migration `0015` and the accepted schema are
untouched, Decision 090's acceptance and observation dispositions remain fully valid, and no
network, SEC, or HTTP request is made.

| Question | Controlling record |
|---|---|
| What was retired, and from what factual state | **Decision 091 §3.** The dual-Claude A/B/adjudication execution sequence, superseded **prospectively**: Review A, Review B, and the adjudication had all NOT started and no real review row existed — nothing produced is invalidated |
| The controlling sequence now | **Decision 091 §4.** One Claude review over all 108 frozen D081 artifacts → freeze/content-address → return to Sol/GPT → **owner adjudication** (which replaces the retired Claude adjudication) → only then any feasibility/E0 determination |
| Who reviews | **Decision 091 §5.** **Claude Opus 5, maximum effort, one fresh `/clear` epoch**, no subagents, no delegation, no parallel workflows |
| What stays frozen | **Decision 091 §6.** `m3.3-document-evidence/1.0` unchanged: categories, X-1…X-6, span requirements, abstention vocabulary, applicability, verified semantics. **Only the workflow changes** |
| How a single pass fits the accepted schema | **Decision 091 §6.1 — confirmed by execution.** The pass carries on the existing `reviewer_role = 'review_a'` identity; Review-B/adjudication rows remain absent; no review-layer trigger requires a second pass; the pass freezes under `REVIEW_A_TABLE_DOMAIN`. Migration `0015` is **not** altered. Recorded consequence: `document_adjudicated_evidence` itself mechanically needs both passes, so persisting owner-adjudicated results there would need its own future authorization |
| The replacement authority | **Decision 091 §7.** `M3_3_SINGLE_DOCUMENT_EVIDENCE_REVIEW_AUTHORIZED` supersedes the Decision 090 §5 Review-A authorization: offline only, private-root READ ONLY for the execution epoch, totality 108/108 or STOP, output frozen with full counts and digest, path never printed |
| Sol/GPT's adjudication role | **Decision 091 §8.** Owner determines run acceptability, abstention/conflict disposition, verified-evidence acceptance, three-category witness, the 8-entity linkage standard, gate closure, and any E0 authorization |
| What the review may not do | **Decision 091 §9.** No self-granted verified credit, no gate closure, no E0, no candidate selection, no root approval |
| What happens next | **Decision 091 §11** — execute the single review in a fresh Opus 5 maximum epoch, then return the frozen output to Sol/GPT |

*(Current state: **the single document-evidence review RAN and its output is owner accepted — see
Decision 092 below.** Review B and Claude adjudication were never required and were never executed;
Sol/GPT owner adjudication is complete; **M3.3-E0 is now authorized** while E1, E2, and M3.4 remain
unauthorized; network/SEC/HTTP authority is NONE at `REQUEST_CEILING = 0`.)*

## Decision 092 — ACCEPTED (the evidence acceptance, the purpose gate, and E0)

[Decision 092](Decisions/decision_092_m3_3_d091_evidence_owner_adjudication_and_e0_authorization.md)
(`ACCEPTED — OWNER ADJUDICATION OF THE D091 DOCUMENT EVIDENCE, PURPOSE-GATE CLOSURE, AND M3.3-E0
AUTHORIZATION 2026-08-15`) is the **twenty-third M3.3 record**. It accepts the frozen single-Opus
document evidence, **closes the real amendment-purpose feasibility gate**, and **authorizes
M3.3-E0** — the first M3.3 execution authorization since the milestone opened.

**It executes nothing.** No document is re-reviewed, no evidence row is rewritten, no schema byte
changes, E0 is **not** started by this record, and no network, SEC, or HTTP request is made.

| Question | Controlling record |
|---|---|
| Whether the D091 review run is accepted | **Decision 092 §2 — yes.** `M3_3_DECISION_091_SINGLE_OPUS_EVIDENCE_REVIEW_OWNER_ACCEPTED` and `M3_3_REVIEW_A_DIGEST_D9C9D9C7_OWNER_ACCEPTED` at digest `d9c9d9c7…`, on 108/108 artifacts, 302 spans, and BLOCKER 0 / MAJOR 0 / MINOR 0 |
| What became of the disclosed freeze correction | **Decision 092 §3.** The preliminary digest `f88213ca…` is an **INVALID PRELIMINARY FREEZE ATTEMPT, NEVER OWNER ACCEPTED, SUPERSEDED BEFORE STAGE ACCEPTANCE**; `d9c9d9c7…` is the sole accepted digest. Ratified as a **NONBLOCKING PROCESS DEVIATION** — no judgment, category, assertion, abstention, or span text changed. The historical disclosure is **not** deleted |
| Which interpretive standards govern purpose | **Decision 092 §4.** **S-1** — independent co-equal purposes in different frozen categories ⇒ abstain `ambiguous_text`, with **no owner dominance rule added**. **S-2** — exhibit-only ⇒ `administrative_or_exhibit` unless the exhibit supplies or corrects substantive financial-statement, accounting, restatement, or XBRL content. **No new category is created** |
| Whether the amendment-purpose gate closes | **Decision 092 §6 — CLOSED.** `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_CLOSED`. All three frozen categories are witnessed by direct unflagged source-backed evidence, so the gate does **not** depend on the 32 high-judgment cases. **No claim is made that every amendment in the population is classifiable** |
| What the 96 form+date assertions are, and are not | **Decision 092 §7.** **OWNER ACCEPTED AS R52-ELIGIBLE REVIEW ASSERTIONS** — not verified linkage, not `amends_original`, no quota credit. The 6 form-only partials cannot contribute under **R48** and stay partial review evidence only |
| How form renderings normalize | **Decision 092 §8.** `Form 10KT` ⇒ `10-KT` and `Form 10–K` ⇒ `10-K` as identity-preserving typography **for this frozen evidence set only**; the informal `the Company 10-K` is accepted **case-specifically**. **No fuzzy form inference and no generic loose-text form parser is authorized** |
| Whether exhibit-index evidence and prior-amendment references are usable | **Decision 092 §9.** The exhibit-index footnote is accepted **X-1** evidence — the protocol never required an explanatory note; a prior-amendment reference does **not** invalidate a separate original-identifying statement, and **no transitive parentage is inferred** |
| The linkage gate | **Decision 092 §10 — still OPEN.** `M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN_PENDING_E0_R52_RESOLUTION`. D081 **M9 must not be used**, and no inference from shared CIK, shared report date, `/A` suffix, nearest prior filing, accession ordering, filing proximity, or name similarity |
| Why E0 is authorized now | **Decision 092 §11.** The remaining linkage uncertainty is **exact catalog resolution, not source discovery**, and R52 cannot complete until the accepted E0 originals catalog exists. `M3_3_E0_OWNER_AUTHORIZED` under the **already-accepted frozen E0 scope only** — no methodology broadening, no new SEC request, no network, accepted stored M3.2 source objects only |
| What happens after E0 | **Decision 092 §12.** A **READ-ONLY R52 resolution diagnostic** over exactly the 96 accepted assertions under the exact accepted semantics, reporting ZERO / EXACTLY_ONE / MULTIPLE plus the frozen NO_DATE state. **No verified linkage persisted, no quota credit granted**; only Sol/GPT may close the linkage gate |
| The persistence bridge | **Decision 092 §13.** `DEFERRED_PENDING_E0_R52` — no fabricated Review B, no fabricated adjudication, migration `0015` **not** modified |
| What happens next | **Decision 092 §16** — return to Sol/GPT; **M3.3-E0 runs in a separate session** under its accepted frozen scope, then the §12 R52 diagnostic returns to the owner |

*(Current state: **this is the controlling record on the amendment-purpose gate and on E0
authorization**, refined on two points by Decision 093 below — the exact linkage-resolution predicate
and the durable reproducibility of the accepted evidence. The purpose gate is **CLOSED**; the
linked-amendment gate is **OPEN pending E0 resolution**; **M3.3-E0 is AUTHORIZED and not yet
started**; E1, E2, and M3.4 remain unauthorized; migration `0016` is not authorized; network/SEC/HTTP
authority is NONE at `REQUEST_CEILING = 0` with new SEC requests 0. Earlier records stating the
purpose gate open or E0 unauthorized state their position as at their own acceptance and are **not**
rewritten.)*

## Decision 093 — ACCEPTED (evidence durability, and the linkage-resolution predicate)

[Decision 093](Decisions/decision_093_m3_3_review_evidence_durability_and_linkage_resolution.md)
(`ACCEPTED — OWNER D091 REVIEW-EVIDENCE DURABILITY CLOSURE AND PRE-E0 LINKAGE-RESOLUTION RULING
2026-08-15`) is the **twenty-fourth M3.3 record**. It makes the accepted D091 evidence durably
reproducible, pins the exact linkage-resolution predicate **before** E0 runs, and records two
read-only E0 preflight findings.

**It executes nothing.** No document is re-reviewed, no judgment changes, no schema byte changes, E0
is **not** started, and no network, SEC, or HTTP request is made.

| Question | Controlling record |
|---|---|
| What the durability gap was | **Decision 093 §3.** The prose review artifact carries all 108 rows but only **123 of 302** span locations — not enough to reconstruct the accepted rows or reproduce the accepted digests. A **durability/reproducibility gap**, not a judgment or digest defect, and not a reopening of the review |
| Where the accepted evidence now lives | **Decision 093 §4.** `Docs/m3/evidence/d091_review_a_d9c9d9c7/` — three canonical JSONL relations plus a manifest, exported from the frozen state with **no value invented and no timestamp generated**, and no document body, absolute path, evidence-root name, scratch path, session identifier, or personal name |
| Whether the accepted digests reproduce | **Decision 093 §5 — yes.** From the exported files **alone**, with the built catalog deliberately not opened: `ARTIFACT_TABLE_SHA256 b84495a4…` and `REVIEW_A_TABLE_SHA256 d9c9d9c7…` both reproduce, alongside every per-row digest and the accepted content counts. **27 checks pass** |
| Which date field resolves an amendment to its original | **Decision 093 §6 — the stated FILING date.** The candidate original's `filing_date` must **exactly equal** the issuer-stated `original_filing_date`. **`report_date` is NOT the matching field** — diagnostic only, and it may never create or destroy a match |
| What registrant scope the resolver uses | **Decision 093 §6A.** The **complete established association set**, unioned over `pilot_candidate_accession_registrants`. The nullable `anchor_cik_numeric` is **never** the scope for a multi-registrant accession; an unestablished set fails closed as `UNESTABLISHED_ASSOCIATION_SET` |
| What the input set is, and what the 6 partials do | **Decision 093 §6.** Exactly the **96** accepted form+date records. The **6** form-only partials are `NO_DATE / INELIGIBLE_FOR_LINKAGE_RESOLUTION`, carry no credit, and sit **outside the 96-match denominator** |
| How acceptance ordering is decided | **Decision 093 §7.** R43 native authority only — never `filing_date`, `report_date`, retrieval, filesystem, or insertion time. `ORDERING_PASS` / `ORDERING_FAIL` / `ORDERING_UNAVAILABLE`, and **missing ordering evidence is never read as PASS** |
| Whether E0 can supply the originals' acceptance timestamps | **Decision 093 §8 — `UNAVAILABLE`, and E0 is not blocked.** `census_accessions` is populated from the **lower-authority** submissions `acceptanceDateTime`; the native header exists only in the 108 D081 artifacts, which are the **amendments**. `REAL_ACCEPTANCE_ORDERING_ADEQUACY` **remains PENDING after E0** |
| Where E0 writes | **Decision 093 §9 — established, not invented.** Catalog at `<accepted private evidence root>/catalogs/m3_2a_operational.sqlite3` (`OPERATIONAL_CATALOG_RELATIVE_PATH`), confined to **R17**'s fifteen tables plus the `census_plan_sources.parser_state` transition; receipt at `runs/<E0 namespace>/execution_receipt.json` (`OPERATOR_RECEIPT_FILENAME`), namespace operator-selected create-once **by accepted design** |
| What E0 must obey when it runs | **Decision 093 §10 — six invariants.** Project Python 3.12 `.venv`; `connect()` used as a context manager; the private root resolved once and cached; **compute → validate → recompute every identity from persisted rows → verify integrity → then freeze**; **no digest computed from a preimage containing its own value**; per-column private-path validation with nonleakage never weakened |
| What happens next | **Decision 093 §14** — return to Sol/GPT; **M3.3-E0 runs in a NEW session** under its accepted scope and these invariants, then the §6–§7 resolution returns to the owner |

*(Current state: **the durability hold is CLOSED and the accepted D091 evidence is durably
reproducible from the repository.** The controlling linkage resolver is the association set plus the
stated filing date; `E0_ORIGINAL_ACCEPTANCE_TIMESTAMP_SOURCE` is **UNAVAILABLE** so
`REAL_ACCEPTANCE_ORDERING_ADEQUACY` remains pending after E0; **M3.3-E0 is AUTHORIZED and executable
in a new session but is not started**; E1, E2, M3.4, and migration `0016` remain unauthorized; the
deferred level-1 `filing_level_metadata` native-header class is **not** activated; network/SEC/HTTP
authority is NONE at `REQUEST_CEILING = 0`.)*

## Decision 094 — ACCEPTED (PRE-E0 executability redesign)

[Decision 094](Decisions/decision_094_m3_3_pre_e0_executability_redesign.md)
(`ACCEPTED — OWNER PRE-E0 REDESIGN AUTHORITY 2026-08-15`) is the **twenty-fifth M3.3 record**. It
accepts the PRE-E0 redesign after one fresh Opus 5 maximum read-only architecture challenge and
authorizes only its bounded implementation.

**It executes nothing.** No accepted-catalog migration, E0, linkage diagnostic, network, or later
stage runs; both execute activation constants remain `None`.

| Question | Controlling record |
|---|---|
| What is preserved | **Decision 094 §§2, 4.** D091 evidence/digests, D092 acceptance/purpose closure, D093 durability and exact linkage predicate, the open linkage gate, and the read-only owner-adjudicated diagnostic. The 96-outcome claim remains inference |
| What happens to the accepted catalog | **Decision 094 §5.** Future exact `0013 -> 0014 -> 0015` only, under a later activation instrument; preflight, continuous lease, `0600` backup, partial-head disclosure, no auto-resume/restore. `0016` excluded |
| What E0 may write | **Decision 094 §6.1.** The former fifteen plus only `census_accession_registrants`, with the existing category-A plan-state transition; exact contract amendment, no general widening |
| How canonical membership is derived | **Decision 094 §§6.2–6.4.** Set union of plan-bound submissions and full-index membership, submissions corroborated by full index, no scalar/anchor/heuristic, no invented registrant, R59 fail closed, completeness last |
| What consumers do | **Decision 094 §6.5.** Candidate and later linkage layers read the relation plus completeness, never observation/scalar fallback; history attributes an established joint filing to every substantive member |
| What the commands are | **Decision 094 §7.** `m3 prepare-e0-catalog` and `m3 offline-parse`, each with `preflight/execute/verify`; fixed namespaces and private-root environment boundary; source constants independently gate execute |
| What durable evidence exists | **Decision 094 §§8–10.** Two fixed private run directories; backup, hash-chained ledger, v4 receipt, terminal; exact conditional fields, identities, totality, and reconstruction |
| What freeze means | **Decision 094 §11.** Compute, validate, commit, independently recompute/verify under the same flock, write receipt/event/terminal, reproduce token, then release; no self-referential identity; post-freeze defect preserved and returned to owner |
| What the architecture challenge found | **Decision 094 §13.** Proposal digest `b01bd2736…`; `ACCEPT_WITH_BOUNDED_CORRECTIONS`, B2/M6/MIN10/OPT5; every finding owner-dispositioned, no Joey-reserved choice and no second architecture reviewer |
| What is authorized now | **Decision 094 §12.** One fresh attested Opus 5 maximum implementation on the exact executor paths, disposable fixtures, one local commit, no push. Real transition and E0 remain unauthorized/HELD |

*(Position at D094 acceptance: bounded implementation was next. Accepted Decision 095 below now
controls the correction/remediation boundary. E0 remains operationally **HELD**.)*

## Decision 095 — ACCEPTED (D094 bounded correction and one remediation)

[Decision 095](Decisions/decision_095_m3_3_d094_bounded_correction_and_remediation.md)
(`ACCEPTED — OWNER BOUNDED CORRECTION AND SINGLE REMEDIATION AUTHORITY 2026-08-15`) is the
**twenty-sixth M3.3 record**. It accepts no implementation bytes. It preserves Decision 094's
production architecture and corrects only the implementation boundary exposed by the first blocked
epoch.

| Question | Controlling record |
|---|---|
| Does missing registrant membership still fail closed | **Decision 095 §§2–3, R79. Yes.** D094 §6.2 condition 3 and §13 M6 stand; production E0 never invents an entity |
| What changes in the synthetic fixture | **Decision 095 §3, R79.** Support-only CIKs 917/918 receive accepted-shaped submissions objects with zero own filings so the production parser creates their registrant rows; `company.idx` remains the joint-filing membership source |
| How is the private-root variable admitted | **Decision 095 §4, R80.** `DISCLOSURE_DRIFT_EVIDENCE_ROOT` is centrally recognized as a runtime root, never a config override or persisted/logged value; a `cli.py` filtering bypass is prohibited |
| How does `e0.py` avoid an acquisition import | **Decision 095 §5, R81.** Restate exactly `catalogs/m3_2a_operational.sqlite3` and require an equality/drift test against the accepted acquisition constant |
| What happened to the first implementation run | **Decision 095 §1.** Blocked, no commit; two source files preserved as unreviewed WIP, never an accepted candidate |
| What is authorized now | **Decision 095 §§6–8, R82.** One fresh attested Opus 5 Maximum normal bounded remediation on D094 §12.1 plus the exact D095 additions; all D094 proofs plus D095 controls; one local implementation commit only after a passing final gate; no push |
| What remains held | **Decision 095 §§9–10.** Both execute constants `None`; no accepted-catalog migration, transition, E0, linkage, bridge, `0016`, later stage, network, SEC, HTTP, push, or tag |

*(Position at D095 acceptance: its one remediation was next. That run has since stopped blocked
with no commit; accepted Decision 096 below now controls the final correction/remediation boundary.
E0 remains operationally **HELD**.)*

## Decision 096 — ACCEPTED (final bounded PRE-E0 rehearsal correction and remediation)

[Decision 096](Decisions/decision_096_m3_3_final_pre_e0_rehearsal_correction_and_remediation.md)
(`ACCEPTED — OWNER FINAL BOUNDED CORRECTION AND SINGLE REMEDIATION AUTHORITY 2026-08-16`) is the
**twenty-seventh M3.3 record**. It accepts no implementation bytes and changes no Decision-094/095
production semantic.

| Question | Controlling record |
|---|---|
| What happened to the D095 remediation | **Decision 096 §1.** Fresh actual `claude-opus-5`; blocked with no commit; ten modified tracked files plus new `m3/e0.py` preserved as unaccepted WIP. Sol/GPT reproduced 79 passed / 4 failed |
| Where malformed full-index CIK refusal now belongs | **Decision 096 §3, R83.** At the pre-association E0 projection, not candidate derivation. Remove the stale E2 candidate-layer expectation and require a positive/adversarial `invalid_cik_rendering_count` proof in `test_m3_e0.py`, with no fallback or entity invention |
| How the R28 mutation is attributed | **Decision 096 §4, R84.** Canonical-relation `multi_registrant` stays unchanged after a post-projection observation mutation; the bridge must fail through `candidate_accession_evidence_sha256`, with the stale attribution absent |
| What model and effort evidence is required | **Decision 096 §5, R85.** Fresh Maximum parent dispatch plus actual `claude-opus-5` attestation. The absent CLI-visible effort flag is a disclosed, non-invalidating observability limitation and must not be fabricated |
| What path is added | **Decision 096 §6.1, R86.** Only `src/disclosure_drift/m3/execution_rehearsal.py`; the two affected test files were already authorized. `rehearsal_snapshot.py` is not added |
| What is authorized now | **Decision 096 §§6–7.** One final fresh bounded remediation; every remaining D094/D095 deliverable and proof; one successful `make check-fast`; one conditional local implementation commit; no push. No further autonomous remediation follows |
| What remains held | **Decision 096 §§8–9.** Both execute constants `None`; no private-root access, accepted-catalog migration, transition, E0, linkage diagnostic, persistence bridge, `0016`, later stage, network, SEC, HTTP, push, or tag |

*(Position after D096 acceptance: its final remediation was next. That run has since completed all
direct implementation/proof work but stopped at one inherited M19 audit-anchor failure with no
commit; accepted Decision 097 below now controls the exceptional one-file correction. E0 remains
operationally **HELD**.)*

## Decision 097 — ACCEPTED (M19 live-anchor supersession and exact audit correction)

[Decision 097](Decisions/decision_097_m3_3_m19_live_anchor_supersession_correction.md)
(`ACCEPTED — OWNER EXCEPTIONAL POST-D096 BLOCKER CORRECTION AUTHORITY 2026-08-16`) is the
**twenty-eighth M3.3 record**. It accepts no implementation bytes and changes no D094-D096
production semantic.

| Question | Controlling record |
|---|---|
| What happened to the D096 remediation | **Decision 097 §1.** Fresh actual `claude-opus-5`; D094-D096 implementation and direct proofs complete; sole `make check-fast` returned 4350 passed / 1 failed / 1 skipped on missing live anchor M19; no commit |
| What is M19's status | **Decision 097 §3, R87.** Its immutable historical definition and KILLED evidence stand; only live-target applicability is superseded by D094 §6.5 and D096 R83. Exact partition: 38 historical definitions, 37 live anchors, superseded `[M19]`, unexpected missing 0 |
| What replaces M19's live proof | **Decision 097 §3, R87.** D096 R83's positive/adversarial pre-association E0 proof: `invalid_cik_rendering_count`, rollback, no established projection, no invented entity, no candidate/scalar/observation fallback |
| What may change | **Decision 097 §4, R88.** Only `tests/unit/test_audit_tooling.py`; the runner, historical artifact, production source, and all D096 WIP bytes remain unchanged |
| What validation and commit are authorized | **Decision 097 §5, R89.** One fresh actual-`claude-opus-5` Maximum exceptional correction; red/green plus isolated non-vacuity; one post-correction `make check-fast`; one local implementation commit over the 22 exact-hash D096 paths plus the audit test only on full success; no push |
| What remains held | **Decision 097 §§7–8.** Both execute constants `None`; no private-root access, accepted-catalog migration, transition, E0, linkage diagnostic, persistence bridge, `0016`, later stage, network, SEC, HTTP, push, or tag |

*(Position after D097 acceptance: the one-file correction was next. It has since produced candidate
`1e200218…` and passed its one full gate, but the required independent review failed with two
MAJOR findings. Accepted Decision 098 below now controls. E0 remains operationally **HELD**.)*

## Decision 098 — ACCEPTED (D094 implementation review rejection and PRE-E0 hold)

[Decision 098](Decisions/decision_098_m3_3_d094_implementation_review_rejection_and_hold.md)
(`ACCEPTED — OWNER REVIEW ADJUDICATION AND HOLD 2026-08-16`) is the **twenty-ninth M3.3 record**.
It accepts the independent-review evidence, rejects but preserves the current candidate, and grants
no further correction or execution authority.

| Question | Controlling record |
|---|---|
| What candidate was reviewed | **Decision 098 §1.** Clean local unpushed HEAD `1e200218…`, tree `7d5f3aa9…`, exact 23-path D097 set; one `make check-fast` passed at 4351 passed / 1 skipped / 0 failed |
| Where is the review evidence | **Decision 098 §2, R90.** [`m3_3_d094_pre_e0_implementation_independent_review_1e20021.md`](m3/reviews/m3_3_d094_pre_e0_implementation_independent_review_1e20021.md), SHA-256 `07feb1608f85ae30b61ff3ec4cdc1fb67ad6b17da03fa6cebd97295174cf1beb`; fresh actual `claude-opus-5`; verdict B0/M2/MIN4/OPT1/OBS4 |
| What is MAJOR-1 | **Decision 098 §3, R91.** Event-conditioned fields can be assigned before their durable event, causing failure disclosure to write a create-once terminal its own validator refuses while suppressing the validation error |
| What is MAJOR-2 | **Decision 098 §4, R92.** Mandatory Decision-094 §5.2 predicate 3, the accepted M3.2 completion-receipt/catalog binding, is missing from both transition preflight and under-lease recheck and is not superseded |
| What happened to the other findings | **Decision 098 §5, R93.** Four MINORs and four observations are confirmed; one harmless redundant-condition optimization is deferred. None authorizes cleanup |
| Is the candidate accepted | **Decision 098 §6, R94.** No. Candidate `1e200218…` is preserved unchanged, clean, unpushed, and unaccepted. Both execute constants remain `None` |
| What may happen next | **Decision 098 §7.** A new Joey ruling is required before one exceptional bounded correction and corrected-target review boundary. No executor may start automatically |
| What remains held | **Decision 098 §§6–9.** Accepted-catalog migration, private-root access, transition, E0, linkage, bridge, `0016`, later stages, activation, network, SEC, HTTP, push, and tag; request ceiling 0 |

*(Current state: **PRE-E0 implementation acceptance is rejected pending a new Joey correction
ruling.** E0 is operationally **HELD**, and read-only analysis/governance recording is the only
authorized work.)*

## Decision 099 — ACCEPTED (post-D098 bounded correction and final PRE-E0 acceptance boundary)

[Decision 099](Decisions/decision_099_m3_3_post_d098_bounded_correction.md)
records Joey's explicit one-post-D098 correction authorization and Sol/GPT's exact technical
disposition.

| Question | Controlling answer |
|---|---|
| What may be corrected | **Decision 099 §§1–5, R95–R98.** Durable-event-derived failure terminal fields; the exact accepted T7→T6 completion-receipt/catalog binding in transition preflight and under lease; catalog-aware verify; structural lease-check omission; and the existing/operator-owned namespace parent |
| What is the exact receipt binding | **Decision 099 §3, R97.** Fixed accepted T7 and T6 paths, file digests, receipt ids, run ids, plan identities, exact two-receipt chain, 77 cumulative attempts, truthful catalog run rows/attempt ledgers, and exact T7 observation attribution, through the existing receipt loader and predecessor resolver only |
| What may the executor edit | **Decision 099 §5.** `m3/e0.py`, `test_m3_e0.py`, the E0 execution-record spec, operator runbook, and change-impact map; nothing else |
| What proof and commit are allowed | **Decision 099 §§7–8.** Targeted mutation/non-vacuity proof, one final `make check-fast`, and one local commit only on full success with subject `fix: close Decision 098 PRE-E0 review findings` |
| What model/review boundary applies | **Decision 099 §§6, 9.** One fresh actual-`claude-opus-5` Maximum executor, no delegation; then Sol direct corrected-target review, with no additional opinion or optimization pass |
| What happens on success | **Decision 099 §9.** Sol may owner-accept PRE-E0 if no BLOCKER/MAJOR or failed frozen proof remains, stop optimizing, and proceed to the separately governed transition/E0 sequence |
| What remains prohibited during correction | **Decision 099 §11.** Private-root access, accepted-catalog migration/transition, E0, activation, linkage, bridge, `0016`, later stages, network/SEC/HTTP, push, and tag; request ceiling 0 |

*(Current state: **the correction this record authorized was made, reviewed, and owner-accepted at
`3e8c82d1…`** by
[Decision 101](Decisions/decision_101_m3_3_d100_owner_acceptance_and_transition_e0_authorization.md).)*

## Decision 100 — ACCEPTED (category-A commit-before-event representability)

[Decision 100](Decisions/decision_100_m3_3_commit_before_event_representability.md)
dispositions the one residual Decision-094 §9.2 gap: a durable category-A database boundary the
failed set was required to state and the schema forbade it from stating.

| Question | Controlling answer |
|---|---|
| What was the gap | **Decision 100 §1, R99.** `run_offline_metadata_parse` commits one category-A plan-row boundary *per source, inside the call*, while every disposition event is appended after it returns. A failure in between left durable boundaries that the derivation dropped (it gated on the caller's in-flight interruption variable) and that a `failed` status could not state (§8.1 permits `interruption_state` only when interrupted) |
| How is membership decided now | **Decision 100 §2, R100.** From durable evidence alone: every durable `SOURCE_DISPOSITION_RECORDED` event plus every independently observed category-A `census_plan_sources.parser_state` boundary lacking one, deduplicated toward the event. No gate on the call stack |
| Which interruption state is used | **Decision 100 §2, R100.** The existing accepted §10.2 value `after_e0_source_commit_before_event`, derived from the resulting rows and disclosed ahead of the tail event. **No vocabulary amendment**: `INTERRUPTION_STATES_V4` and `m3/receipt.py` are unchanged |
| When may a failed terminal state it | **Decision 100 §2, R100.** Exactly when the record carries a `ledger_event_present = false` row, which is §9.3's own mandate. With no boundary row, §8.1's "iff interrupted" rule still governs, and the validator still refuses any other value wherever a boundary row appears |
| What about the receipt | **Decision 100 §2, R100.** Unchanged. §10.1 conditions the receipt's own field on an interrupted status, so a failed run states the window on the terminal and omits it from the receipt |
| What else was fixed | **Decision 100 §3, R101.** The tail `INTERRUPTED` event was copied from the terminal's `failure` object, carrying `catalog_state_observed`, which §10.2's closed projection refuses — so every append was refused and swallowed and an interrupted run recorded no `INTERRUPTED` event. It is now projected to the exact key set |
| Is anything representable but unstatable | **Decision 100 §4.** No. Rows A–F cover every lawful combination, and rows C and D hold on `failed` and `interrupted` runs alike |
| What may the executor edit | **Decision 100 §5.** `m3/e0.py`, `test_m3_e0.py`, and the E0 execution-record spec, plus this record and its registry/index rows; nothing else |
| What remains prohibited | **Decision 100 §8.** Private-root access, accepted-catalog migration/transition, E0, activation, linkage, bridge, `0016`, later stages, network/SEC/HTTP, push, and tag; request ceiling 0 |

*(Current state: **the residual §9.2 representability gap is closed and the corrected PRE-E0 target
is owner-accepted** by
[Decision 101](Decisions/decision_101_m3_3_d100_owner_acceptance_and_transition_e0_authorization.md).)*

## Decision 101 — ACCEPTED (D100 owner acceptance, and transition/E0 authority)

[Decision 101](Decisions/decision_101_m3_3_d100_owner_acceptance_and_transition_e0_authorization.md)
closes the PRE-E0 remediation chain and issues the two execution instruments Decision 094 §12.4
reserved for a later exact owner act.

| Question | Controlling answer |
|---|---|
| Is the PRE-E0 implementation accepted | **Decision 101 §1.** Yes — `M3_3_D100_PRE_E0_IMPLEMENTATION_OWNER_ACCEPTED` at implementation `3e8c82d1…`, tree `67564d3f…`, zero BLOCKER and zero MAJOR, on Sol's direct Decision 099 §9 review. The chain is **CLOSED**; no further PRE-E0 review, optimization, or re-run of the accepted validation evidence precedes execution |
| What happened to the review's MINORs | **Decision 101 §§2–4.** **R102** ratifies the catalog-observed claim/exposure correction as valid D099-R96-preserving work needing no further code change; **R103** defers the failure-only aggregate limitation; **R104** defers the interruption-state regression test. Neither deferral delays execution |
| How must a zeroed aggregate be read | **Decision 101 §3, R103.** On a **failed or interrupted** terminal, `submissions_membership_observation_count` and `substantive_membership_observation_count` are never authoritative measured values — the durable `source_results`, event ledger, catalog state, and `association_totality` are. On a **COMPLETE** run the limitation does not apply at all |
| Is the catalog transition authorized | **Decision 101 §7 — it was, and the grant is now spent.** The exact `0013 -> 0014 -> 0015` transition through the accepted operator surface was enabled by a constant-only activation of `PRE_E0_CATALOG_TRANSITION_AUTHORITY`, ran to a COMPLETE and verified terminal, and consumed its one authorization. Every Decision 094 §5.2 predicate and the under-lease recheck were required; migration `0016` is never selected. **[Decision 108](Decisions/decision_108_m3_3_e0_v2_execution_authorization.md) §3 (R119) has withdrawn the constant to `None`**, so `m3 prepare-e0-catalog --mode execute` returns exit `3` again and the spent D101 literal is retained nowhere in source. That withdrawal does not reach E0: E0 reads the completed transition *terminal record* as a predicate and no verification path recomputes an authority digest from the constant |
| Is M3.3-E0 authorized | **Decision 101 §8.** Yes, **conditionally** — one invocation, if and only if the transition completes and verifies, enabled by its own constant-only activation of `M3_3_E0_EXECUTION_AUTHORITY`. Every Decision 091–100 evidence, relation, no-fallback, projection, provenance, and identity rule is preserved |
| What is published, and when | **Decision 101 §§5–6.** One ordinary push of `main` to `origin/main` **before** the private catalog is touched; private-root access only afterwards, resolved through the accepted mechanism and never disclosed. No force push, rebase, amend, or tag |
| Where does the sequence stop | **Decision 101 §9.** After verified E0. No migration `0016`, persistence bridge, E1, E2, or M3.4. The read-only R52 linkage diagnostic may run only under unambiguous existing authority, and its results never become a new owner ruling |
| **Which E0 run namespace is current** | **Decision 103 §3 (R105) — `m3_3_e0_offline_parse_v2`.** It supersedes the E0 literal in Decision 094 §7.1 and **only** that literal. The generation advances by reviewed source change alone: there is no `--run-namespace`, environment override, or configuration field, and the transition namespace is unchanged |
| **What the interrupted `…_v1` E0 run is now** | **Decision 103 §4 (R106) — immutable interrupted evidence, classification `UNDETERMINED / NOT COMPLETE`.** Never repaired, resumed, overwritten, deleted, renamed, or read as a v2 prefix. The successor **validates** it — present, terminal-free, receipt-free, chain-valid, no closing event — rather than skipping it, and an absent v1 stops the successor instead of reading as a clean start |
| **How a stale catalog writer lease is reconciled** | **Decision 103 §§5–9 (R107–R111).** `m3 reconcile-writer-lease --config … --mode {preflight,execute}`, never automatic, gated by its own `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` constant. Eligibility is the conjunctive fail-closed `L1`–`L12` ladder: no elapsed time, dead PID, or free advisory lock authorizes takeover on its own. The lease transitions `held -> released` **without** `released_at_utc` and **with** `reconciliation_reason`, so voluntary release cannot be inferred; one write-once record binds both lease digests and the catalog's before/after identity. The ordinary E0 surfaces keep refusing a held lease |
| **Whether that reconciliation can actually be run** | **No — it already was, exactly once, and [Decision 107](Decisions/decision_107_m3_3_real_stale_writer_lease_reconciliation.md) §5 (R118) has withdrawn the authority.** `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` is back to `None`, so `m3 reconcile-writer-lease --mode execute` returns exit `3` again. Decision 107 §3 (R116) briefly set it to that record's token for **exactly one** real reconciliation; that reconciliation was executed and verified, and the grant was spent by its one use. The ladder would now refuse independently — the real lease records `released` and the create-once recovery namespace exists — but the constant is the first gate and it is shut. The rule Decision 104 §2 (R113) established is unchanged and is what made the instrument necessary: `None` means `execute` returns exit `3` ahead of private-root resolution and touches no private state, only a separate owner instrument may replace the literal, and a passing read-only `preflight` is a measurement rather than permission. **Activation is necessary and never sufficient** — the conjunctive fail-closed `L1`–`L12` ladder still runs in full. Decision 104 §3 (R114): the recovery record binds the authority **actually active** for the execution, never a literal in the record builder. A second real reconciliation needs both a new owner instrument and a reviewed source change to a `…_v2` recovery generation |
| **Is the stale-lease recovery implementation accepted** | **Yes — [Decision 106](Decisions/decision_106_m3_3_recovery_implementation_acceptance_and_preflight_authorization.md) §1**, at **BLOCKER 0 / MAJOR 0**, token `M3_3_D105_RECOVERY_IMPLEMENTATION_OWNER_ACCEPTED`: the D103 implementation `91f9058f…`, the D104 correction `104a5ec0…`, and the D105 correction `f22dacedd…`, tree `e322b382…`. The 64 KiB lease-reader bound is **non-blocking** — an oversized or unreadable lease fails closed. **No further independent review of this implementation is required.** §2 disposes of F1–F9 once, reopening no D103/D104/D105 ruling |
| **What may actually be run against the real private state now** | **Exactly one read-only measurement — [Decision 106](Decisions/decision_106_m3_3_recovery_implementation_acceptance_and_preflight_authorization.md) §6.** `m3 reconcile-writer-lease --mode preflight`, after successful publication only, through the accepted evidence-root resolver, measuring `L1`–`L11` plus the v1 predecessor state; `L12` is exempt as an execute-path control-flow property no read-only measurement can establish. §7 requires before/after nonmutation proof and §8 the **required stop**: acceptance is not activation, a passing preflight is not permission, `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` stays `None`, and real reconciliation and E0-v2 each still need their own separate owner instrument |
| **Whether M3.3-E0 (v2) may be executed now** | **Yes — exactly once, by accepted [Decision 108](Decisions/decision_108_m3_3_e0_v2_execution_authorization.md) §2 (R120).** `M3_3_E0_EXECUTION_AUTHORITY` carries exactly `M3_3_D108_E0_V2_EXECUTION_AUTHORIZED`, set by reviewed source change and by nothing else. This is the separate owner instrument Decision 107 §5 reserved: it is issued **on** the verified stale-lease recovery and the read-only successor preflight that followed it, never granted **by** them. Decision 107 §4 (R117) had set the constant to `None` before the lease was touched, precisely so one operation's success could not silently re-enable another. **Activation is necessary and never sufficient** — every frozen Decision 094 §5 predicate and Decision 103 §10 successor predicate still runs, conjunctively and fail-closed, and `preflight` stays a measurement rather than permission. The authorized operation is one `m3 offline-parse --config configs/project.yaml --mode execute` through the governed surface, with no direct-library substitute, no second `execute`, and no retry; §5 (R122) returns the constant to `None` once that invocation has returned, whatever its outcome. `PRE_E0_CATALOG_TRANSITION_AUTHORITY` and `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` are both `None` and stay disabled throughout |
| **What the real-state preflight measured** | **[Decision 107](Decisions/decision_107_m3_3_real_stale_writer_lease_reconciliation.md) §§1–2 — owner-accepted at BLOCKER 0 / MAJOR 0**, token `M3_3_D106_REAL_RECOVERY_PREFLIGHT_OWNER_ACCEPTED`. Every applicable Decision 103 §5 predicate `L1`–`L11` **PASS** against real private state; identities unchanged across the measurement; catalog chain `1..15` at head `0015`, `0016` absent, integrity PASS, foreign-key violations `0`, both accepted identities MATCH, 0-byte write-ahead log, recovery namespace **absent**, both network switches `false`. `L12` stays exempt. The v1 predecessor is accepted as permanently `UNDETERMINED / NOT COMPLETE` and is not modified |
| **What an existing but unreadable writer lease means to the ordinary gates** | **[Decision 105](Decisions/decision_105_m3_3_unreadable_writer_lease_fail_closed.md) §2 (R115) — it refuses.** Because Decision 103 §7 rewrites the lease **in place**, a crash-torn rewrite can leave a document that is not structurally readable, and such a document is **never** a released lease. An **existing** lease clears Decision 094 §5.2 predicate 9 only by being structurally valid — read through the same production reader the `L1`–`L12` ladder uses — and recording exactly `released`. A `held` lease keeps its own unchanged refusal; an **absent** lease keeps its accepted Decision 094 finding-m1 semantics, passes, and is still never created. No new lease-state vocabulary, no weakening of `read_persisted_lease`, and no reopening of Decision 103 or Decision 104 |
| **What happened to the one authorized E0-v2 execution** | **[Decision 109](Decisions/decision_109_m3_3_e0_v2_interruption.md) §2 — it was interrupted and is permanently `UNDETERMINED / NOT COMPLETE`.** It reached a durable `BACKUP_VERIFIED` at sequence 2 and no further; there is no terminal record, no execution receipt, and no closing event, because the kernel killed it outright and a jetsam kill runs no Python handler. The cause is **measured, not guessed**: `memorystatus: killing largest compressed process Python [67381] 33911 MB` after roughly 63 minutes under `swap_low` on an 8 GiB host, with 17 GiB free disk and no I/O error. **No catalog byte changed** — both accepted identities MATCH, the WAL is 0 bytes, the chain is `1..15` at head `0015`, all 76 sources are still `not_started`, and `census_parser_runs` is empty. v1 and v2 are immutable evidence; no v3 namespace exists. Two MAJORs are accepted there: **F1**, the parser is not safely executable on this host, and **F2**, ordinary lease acquisition destroys interruption provenance |
| **Why an ordinary writer refuses a `held` lease whose process is dead** | **[Decision 110](Decisions/decision_110_m3_3_e0_successor_safety_remediation.md) §5 — because a persisted lease is evidence before it is a lock.** `flock` lives on the open file description and the kernel drops it the moment a process dies, so a SIGKILL-class death leaves the lock free and the document still recording `held`; acquisition used to truncate that document as soon as it won the free lock, which is how D109 F2 destroyed the v2 run's lease 3.96 seconds after the kill. Acquisition now reads the pre-existing document through the production strict reader **before writing any byte**, and proceeds only on `absent` or a structurally valid `released`. A dead PID, an expired lease, and a free lock are each *true of every jetsam residue* and none of them is authority. Converting `held -> released` stays the governed [Decision 103](Decisions/decision_103_m3_3_e0_interruption_recovery.md) §3 (R3) reconciliation's job alone. A fail-fast create-once namespace check now runs ahead of lease acquisition so a doomed repeat never churns the lease at all — deliberately **not** authoritative by itself; the under-lease recheck remains |
| **What made E0 unable to parse its first planned source, and what changed** | **[Decision 110](Decisions/decision_110_m3_3_e0_successor_safety_remediation.md) §§7–8.** Measured: the first source is a 1.56 GB archive of 985,834 members expanding to 5.71 GB and parsing to ~22.5 M records, and the parser materialized every member and every member's outcome before persisting any of them — 92,639 bytes retained per member, ≈ 91 GB. Streaming the identical parse held memory **flat**, which is what identifies the accumulation rather than the traversal as the cause. Two further unbounded classes sat on the same call: run-level structural state whose summary rendering is ~1.35 GB and **exceeds SQLite's 1 GB cell limit** outright, and preloaded whole-catalog structures in the association projection, the totality measurement, and accession resolution. Peak memory may now depend only on a bounded chunk and explicitly bounded reduction state. **§8.2 discloses the one output change and asks the owner to ratify it**: a streamed run's `summary_json` keeps blocking structural detail only, with a self-describing `structural_detail` key, because the merged shape cannot be written at all. Disposition vocabulary, association and totality semantics, deterministic ordering, identity preimages, and linkage and source-selection methodology are unchanged |
| **Why E0's persistence was not executable within any time or journal budget, and what changed** | **[Decision 111](Decisions/decision_111_m3_3_e0_bounded_persistence_and_working_catalog.md) §§2–3.** Two monotone derivations — candidate lineage edges and accession conflict indicators — were recomputed after **every** record, which measured a 5× growth in the marginal cost of a 40-member block across the first 400 members; hoisting them writes the same rows and sustains **103.2 members/sec with flat block times**. A single transaction per source cannot bound its journal, so `BoundedTransaction` splits the logical write into bounded real transactions — **batch size is not observable in the result**, proved row for row at two materially different sizes. Partial progress must never be durable in the accepted catalog, so `WorkingCatalog` derives a writable twin through the online-backup interface from a strictly read-only handle, and run-local progress lives in a ledger **outside** the accepted schema because the accepted vocabularies have no in-progress term |
| **Whether E0 must write one SQLite row per raw field observation** | **No — [Decision 112](Decisions/decision_112_m3_3_compact_e0_evidence_contract.md) §1.** The frozen immutable source artifact is the authoritative complete raw evidence, and E0's relational evidence exists to prove traversal, disposition, canonical identity, canonical association, exceptions, lineage, and replayability. An observation is omitted **only** when it is inert — no accepted consumer reads the field name — or exactly reconstructible from the canonical `census_accessions` row, which already carries every governed value with the observation's provenance triple and therefore *is* the observation. Malformed values, values normalisation would rewrite, blank membership renderings, second witnesses, and conflicting alternatives are all **materialized**, and an incumbent is back-filled before any rival so the accepted conflict pass can still see both sides. The ruling is limited to E0 successor execution and rewrites no historical M2 acquisition evidence |
| **Whether the compact contract made E0 fit on this host** | **No — [Decision 112](Decisions/decision_112_m3_3_compact_e0_evidence_contract.md) §6, and the canary was therefore not run.** The contract did what it was asked to: measured on the real first source, `census_accession_observations` fell from a projected 204.2 GB to about **2.4 GB**, a **98.8 %** reduction, with linear growth, flat memory, and a bounded log. The complete 76-source working state still projects to **~186.5 GB against 86.3 GB free** — failing the ≥15 GiB reserve **on source 1 alone** — because the two dominant costs are outside the ruling: the Decision 012 resolution layer, now **67.7 %** of everything E0 persists at 4,172.8 B/accession, and the full-index corroboration layer at ~29.6 GB. §7 states both, measured, so the next ruling can be made on numbers |
| **Whether E0 must write one Decision 012 resolution row per accession** | **No — [Decision 113](Decisions/decision_113_m3_3_compact_derived_e0_evidence.md) §4.** A resolution whose complete governed content is a deterministic pure function of already-persisted canonical evidence is not written; its content is *defined* by replaying the accepted resolver over the reconstructed observation stream, so the logical resolution set is unchanged and only the physical row count moves. The rule is `DEFAULT_CANONICAL_RESOLUTION` and it is decided by **comparing whole resolutions**, never by a list of cases — a competing value, a conflict, ambiguity, a malformed alternative, an authority-level choice, a prior-cohort history, and an approved 2024 transition each make the reconstruction differ and are each materialized. §6 states the two fields no source class can carry once, as source-class metadata, rather than repeating them per accession; §7 applies the same rule to cohort resolution, omitted or materialized together with the field resolutions |
| **How a full-index row's corroboration is recorded** | **By the parsed record the traversal already wrote — [Decision 113](Decisions/decision_113_m3_3_compact_derived_e0_evidence.md) §9.** It carries accession identity, the quarter's source identity, the CIK, form, filing date, line number, and a `record_sha256` over the **complete** raw row, and corroboration presence is the accession's existence in `census_accessions`. The three observation rows that repeated it are not written, and the row's duplicated `raw_line` payload is dropped (§3.C) while its content digest still covers it. §10 keeps every disagreement, co-registrant, malformed row, and totality change explicit — a disagreement is never compacted into a boolean |
| **What a future E0 preflight must have free before it may start** | **The projected complete working state plus overhead plus a 25 GiB governed reserve — [Decision 113](Decisions/decision_113_m3_3_compact_derived_e0_evidence.md) §19.** The old predicate asked for three copies of the *current* catalog plus a gibibyte; the current catalog is the pre-E0 one, so it admitted any host with roughly 2.1 GB free while a complete execution needs two orders of magnitude more. The requirement is now computed from measured densities and the planned work, its identity digests every term, and a catalog whose source plan does not fingerprint identically to the plan the densities were measured over is refused rather than answered from a stale projection |
| **Whether exactly one governed planned source can be run under the compact contract, and be relied on to stop** | **Yes — [Decision 116](Decisions/decision_116_m3_3_disposable_single_source_canary_path.md) §§5–11.** Decision 115 authorized the first real single-source canary and stopped without executing (§3), because the reachable driver loads the whole plan, traverses every planned source, defaults to full evidence, and wires no Decision 112 §8 sidecar (§4). The path that closes that gap is **additive and canary-only**: the `m3 canary-source` operator surface over `m3/single_source_canary.py`, plus a one-source entry point beside the accepted whole-plan driver rather than in place of it, so every parse, identity, digest, and durable row still comes from the accepted modules. One invocation selects one `census_plan_sources` row by `source_instance_id` and refuses an absent or ambiguous one; there is no path argument and no all-source fallback; the accepted catalog is opened `SQLITE_OPEN_READONLY` on every path with no writer lease taken on it; `e0-compact-evidence/2` is bound **explicitly** at the one `CensusCatalog` constructed, so the full-observation default is unreachable by omission; the Decision 112 §8 sidecar is emitted; and the run **terminates after that one source**. It promotes nothing, applies no migration, imports `m3/e0.py` nowhere, names no activation constant, and creates no E0 run namespace |
| **Where a canary is allowed to write, and who enforces it** | **Outside both the checkout and the authoritative evidence tree, enforced by the run itself — [Decision 116](Decisions/decision_116_m3_3_disposable_single_source_canary_path.md) §7 as corrected by §21 (R11).** Every writable output — the Decision 111 run-local working catalog, its progress ledger, the compact sidecar, and one write-once result document — lives in a create-once disposable world beneath an operator-supplied work root, refused unless it lies outside the repository checkout **and** outside the private evidence root, and refused if it would contain that root. Containment is decided on fully resolved, case-folded paths, so neither a symlink nor a case variant launders it. **R11 moves that invariant from the operator wrapper into the production library boundary**: `run_single_source_canary()` refuses an unlawful work root itself, before any directory, catalog, sidecar, or result document exists, through the **same** `require_disposable_work_root()` primitive rather than a second implementation — applied to the evidence tree the run reads and to the authoritative root the process declares, with the checkout derived from the package's own location. The operator surface keeps its early refusal as a convenience, never as the invariant |
| **How a single-payload planned source is represented in the member manifest** | **As exactly one logical member — [Decision 116](Decisions/decision_116_m3_3_disposable_single_source_canary_path.md) §22 (R12), extending §6.** The frozen artifact itself is the single logical member, its frozen `relative_storage_path` is the deterministic logical member name, and the compact member-manifest binding binds that artifact's governed payload identity and length under the **same** accepted folding semantics. No absolute host path is part of the identity, and two independent worlds reach equal member-manifest, projection, resolution, corroboration, and compact-evidence identities for a streamed archive source and a single-payload source alike. This extends the accepted member representation to an already planned source class; it is **not** new semantic compaction, not permission to change archive-member semantics, and not permission to change the accepted digest folding rules |
| **Whether Decision 116 authorizes running a real source** | **No — [Decision 116](Decisions/decision_116_m3_3_disposable_single_source_canary_path.md) §§14, 18–19 and §23.** It authorizes implementation and tests only, over deterministic synthetic fixtures. No real SEC source was parsed, the real `sec_bulk_submissions` artifact was not opened, and no D115 run identity or world was created. The capacity blocker is cleared **on this host** by §2 (R6) — about 107.09 GiB available against about 90.54 GiB required under requirement identity `791618e0…`, which `capacity_plan.py` reproduces term for term — and **that is not E0-v3 authorization**. All three activation constants stay `None`, migration `0016` stays unapplied, the operational catalog stays at head `0015`, no E0-v3 namespace exists, semantic compaction stays closed, and both tracked network switches stay `false` at request ceiling `0`. The completion tokens state readiness for owner review and for owner acceptance of the correction; **neither is owner acceptance**, and the next real source parse requires a new owner instrument |
| **What the first real single-source canary established** | **A throughput failure, and a safety architecture that held — [Decision 117](Decisions/decision_117_m3_3_first_source_canary_throughput_failure.md) §§2–5.** The canary ran over the accepted `sec_bulk_submissions` first planned source and was **stopped at a throughput gate**: no source terminal, none of the five complete-source identities, and **no success token**. What held is the point of the record: the accepted operational catalog stayed byte-identical and was never opened for writing, every write landed in the run-local Decision 111 working catalog, memory stayed bounded, and committed batches were durable under a parser run that claimed nothing. The disposable world it left, about `25.65 GiB`, is **preserved diagnostic evidence** and may not be resumed, modified, promoted, vacuumed, reindexed, or deleted. Every value in the record is quoted from the accepting owner instrument rather than re-derived |
| **Why the first real canary was slow, and what that supersedes** | **SQLite random-write amplification against a working set far larger than cache residency — [Decision 118](Decisions/decision_118_m3_3_read_only_performance_diagnosis.md) §§1–2 (R22).** An `8 GiB` host, a `25.65 GiB` working catalog, and **no `cache_size` ever configured**, so about `2 MiB` of page cache carried the whole write: a `>= 169.61 GiB` write-ahead-log lower bound, a `>= 13.22x` physical-write amplification lower bound, cold access about `45-85x` warm, throughput decaying with database size, and CPU parsing **not** dominant. §3 (R21) supersedes the Decision 113 §14 performance samples **as a predictive assumption only** — they never left the RAM-resident regime — and with them the former 8-hour first-source gate, **without** authorizing a longer run. §4 (R23) records that projection, resolution, association, and final evidence remain unmeasured at real scale, so no retry follows from faster materialization alone. §5 (R24) records the capacity density as `STRAINED BUT NOT INVALIDATED` at about **`+28.2%`** above the accepted submissions density, with **no** capacity constant or model change |
| **What was changed in response, and what deliberately was not** | **One page-cache budget, and a way to measure it — [Decision 119](Decisions/decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md) §§3–4 and §§6–8.** C1 is an explicit **512 MiB** budget (`PRAGMA cache_size = -524288`) on the **run-local writable** Decision 111 working catalog alone, opt-in through a `cache_bytes` parameter defaulting to `None` and requested explicitly by the D116 canary path; it reaches neither the governed operational catalog, nor any read-only connection, nor any global default, and it is an **execution parameter rather than an evidence semantic** — two canaries over one catalog differing only in it produce identical evidence. **C1 is the only performance behaviour that moved** (§3): the sidecar autocommit cadence, `synchronous = FULL`, WAL, batch size `250`, per-batch checkpointing, `cache_spill`, `mmap_size`, the schema and its indexes, the parsers, the lookup logic, the source ordering, and every digest are unchanged, and Decision 118 §§5–7's deferrals stay deferred |
| **How the accepted materialization path can be measured without running a whole source** | **The bounded diagnostic prefix — [Decision 119](Decisions/decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md) §§6–8.** `m3 canary-source --mode profile-prefix --member-limit N` runs the **exact** accepted path — same selection, same member ordering, same parser, same persistence, same compact member recording, batch size `250`, the §4 budget — over the first *N* governed members and stops **before source-level finalization**. It can reach no `parser_state` transition, no **R23** full-index materialization, no resolution pass, no Decision 094 §6.4 association projection, and none of the five complete-source identities; its classification is `INCOMPLETE_DIAGNOSTIC_PREFIX`, deliberately not a member of the accepted `SourceDisposition` vocabulary, and it writes its own result document rather than the canary one. The bound is an **internal** stream parameter defaulting to `None` that `materialize_one_planned_source` does not expose, so the production path cannot supply one; `--mode run` stays complete-source-only and **refuses** a limit. Worlds are create-once and fail-closed, and nothing is promoted |
| **Whether Decision 119 authorizes running a real source** | **No — [Decision 119](Decisions/decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md) §§11 and 13.** It authorizes implementation and tests only, over deterministic synthetic fixtures. No real SEC source was parsed, no real prefix world was created, and the preserved D117 world was not opened. All three activation constants stay `None`, migration `0016` stays unapplied, the operational catalog stays at head `0015`, no E0-v3 namespace exists, and the D117 retry, the three-source canary, the real replay proof, network, acquisition, push, and tag all remain unauthorized at request ceiling `0`. Its completion token states readiness for owner review; **that is not owner acceptance** |

*(Current state: **the PRE-E0 chain is closed and execution is authorized.** The Decision 101 E0
invocation was **interrupted**; Decision 103 implements the successor generation and the governed
stale-lease recovery, and authorizes **implementation only** — reconciling the real lease and
running E0 v2 each still require a separate owner instrument. Decision 104 makes that boundary
executable: the recovery activation constant ships `None`, so the surface it implements is
**disabled as shipped**. Decision 105 closes the last acceptance issue on that implementation — an
existing lease the reader cannot account for now refuses at both ordinary gates instead of reading
as permission — and grants no authority of its own. **Decision 106 then owner-accepts that whole
implementation chain at BLOCKER 0 / MAJOR 0, publishes it, and authorizes exactly one read-only
real-state preflight** — acceptance of an implementation, never activation of an operation. That
preflight ran and measured `L1`–`L11` **PASS**, and **Decision 107 owner-accepts the measurement and
authorizes exactly one real reconciliation**: the recovery constant carries the D107 token for that
single use and returns to `None` afterwards, and `M3_3_E0_EXECUTION_AUTHORITY` is set to `None`
**first**, so clearing the lease cannot re-enable E0-v2 as a side effect. That reconciliation was
executed exactly once, verified, and owner-accepted, and **Decision 108 is the separate owner
instrument E0-v2 was awaiting**: §2 (R120) authorizes exactly one real execution and §3 (R119)
withdraws the spent transition grant at the same time, so E0 is the *only* execute surface open and
its own §5 (R122) shuts it again as soon as the one invocation has returned. Network, SEC, and HTTP
authority remain **NONE** at request ceiling **0** throughout, the ordinary authorized pushes
aside.)*

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
