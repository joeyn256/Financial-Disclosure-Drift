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
