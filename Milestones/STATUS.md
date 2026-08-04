# Milestones/STATUS.md — concrete-state ledger

**Purpose:** a short, current-state record of where the project stands — **Milestones 0, 1, and 2 are
formally closed; Milestone 3 master planning is complete at Decision 027 v0.2; Decisions 028 and 029
are accepted; the bounded M3.1 contract is accepted and implementation-authorized; and the M3.1
implementation is OWNER-ACCEPTED (accepted Decision 031, 2026-08-03, outcome
`M3_1_ACCEPTED_AND_COMPLETE`). Decision 029 code remediation is implemented, the
implementation is frozen at `970e050deb06910adcde8588101564beb7d19c74`, the first durable §17
review is complete and passed, and Decision 029 §12 steps 9, 10, and 11 are complete — the step 9
operational rehearsal passed with the M3.1A token emitted; the step 10 deterministic request plan
ran twice byte-identically (request-plan SHA-256
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, q = 70, 75 planned unique
logical requests, 801 maximum physical attempts); and the step 11 canonical budget display passed,
with the owner approving the exact hard request ceiling 801 on 2026-08-03. **Step 12 is signed and
complete on 2026-08-03**: the signing preflight validated the SEC contact identity at the boundary
(value never displayed) and synchronized `main` with the live remote, and the owner-signed Gate F
checklist (result `PASS`, no unresolved blocker) is durable private evidence, publicly referenced
in the evidence index. **Step 13 was owner-authorized and completed on 2026-08-03**: the Gate F
readiness token was emitted and durably recorded exactly once as immutable private evidence, bound
to the signed checklist, plan, budget, ceiling 801, and repository baseline, and the owner's
evidence-index attestation is recorded. **Step 14 is complete and passed (2026-08-03)**: the
independent M3.1 acceptance review by a fresh non-author session returned
`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS` (artifact SHA-256
`caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`, committed governance-only at
`24fba32413bb6c5dade60a64182e42510afe6f88`) with zero BLOCKER and zero MAJOR findings and three
MINOR findings the owner accepted as nonblocking. **The owner accepted M3.1 on 2026-08-03
(accepted Decision 031), step 15 recorded that acceptance, and step 16 created and pushed the
annotated `m3.1-complete` checkpoint tag** (tag object
`638a02b780d912ff7b37a2f523277b9d451a015a`, peeled to the acceptance commit
`4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`, verified locally and remotely). **Step 17 (2026-08-03,
under the owner's explicit step-17 authorization) closed M3-L11 and M3-L12 on their complete
closure-evidence lists and drafted the bounded M3.2 contract —
[`contracts/m3_2.md`](contracts/m3_2.md), `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE` —
completing the Decision 029 §12 seventeen-step sequence. The M3.2 contract is not accepted, M3.2
implementation is not authorized, live SEC access remains unauthorized, no acquisition has begun,
and no operational catalog exists.** **The independent M3.2 contract review completed 2026-08-04**
— verdict `M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS` (artifact SHA-256
`fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57`, committed governance-only at
`3fbaa12d671d0000f5b608bbf6fb271f78b4673f`) — and **accepted
[Decision 032](../Docs/Decisions/decision_032_m3_2_contract_corrections.md) (2026-08-04)** adopted
its findings and applied the bounded corrections. **The fresh independent no-subagent rereview of
the corrected contract completed 2026-08-04** — verdict
`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS` (artifact SHA-256
`91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf`, committed governance-only at
`3069b03ede9d805e9d0196a3e4c45c8cc68f42b7`; zero BLOCKER, zero MAJOR) — and **the owner accepted
the corrected contract unchanged at T1 (accepted
[Decision 034](../Docs/Decisions/decision_034_m3_2_contract_acceptance.md), 2026-08-04, outcome
`M3_2_CONTRACT_ACCEPTED_AT_T1`)**, so the contract now reads `ACCEPTED (T1) — DECISION 034
(2026-08-04) — IMPLEMENTATION NOT AUTHORIZED`. **T1 grants no later gate: M3.2 implementation
remains not authorized (T2 pending under all five Decision 024 §8 conditions) and not begun,
network and live SEC access remain unauthorized, no acquisition has occurred, and no operational
catalog exists.** The next authorized action is preparation and owner review of the bounded T2
implementation-authorization packet — preparing it authorizes nothing. This
file records
workflow state; it never overrides a decision record, a migration, or `src/disclosure_drift/`. When
this file and an authoritative source (`Docs/Decisions/` — with
`Docs/Decisions/decision_registry.md` authoritative for which decisions exist and their approval
status — a migration, or `src/disclosure_drift/`) appear to disagree, the authoritative source
controls — see CLAUDE.md's authority rules. `Docs/decision_index.md` is a navigation aid only and is
never consulted to establish that a decision exists or is approved.

No percentages are recorded here. A stage is accepted, blocked, deferred, or not started; nothing
here is scored.

Commit hashes below are **historical checkpoint references**, current as of the last time this file
was edited. They are not live. For the current branch, HEAD, tag, and migration state, run
`scripts/context_snapshot.sh` (or `make context`) — it reads Git directly and cannot go stale the way
a hand-maintained hash can.

## Milestone closure state

Recorded by [Decision 026](../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`), on
the final fresh independent rereview
`ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT`, with **no closeout blocker
remaining**.

| Milestone | State | Closure record | Completion tag |
|---|---|---|---|
| **Milestone 0** — research question, novelty boundary, preregistration, frozen definitions, registers | **`FORMALLY_CLOSED`** | Decision 026 §6 | `m0-complete` |
| **Milestone 1** — reproducible engineering foundation | **`FORMALLY_CLOSED`** | Decision 026 §7 | `m1-complete` |
| **Milestone 2** — M2.1 offline SEC policy, M2.2 controlled live-metadata readiness, M2.3 through accepted S6 | **`FORMALLY_CLOSED`** | Decision 026 §§8–10 | `m2-complete` |
| **Milestone 3** — M3.1–M3.5 | **Master planning complete; Decisions 028–031 accepted; the bounded M3.1 contract is accepted and implementation-authorized. M3.1 is OWNER-ACCEPTED (Decision 031, 2026-08-03, outcome `M3_1_ACCEPTED_AND_COMPLETE`)** — Decision 029 code remediation implemented; the implementation is frozen at `970e050deb06910adcde8588101564beb7d19c74`, and the **first durable §17 review is complete and passed** (`M3_1_SECTION_17_REVIEW: PASS`, artifact committed at `66e4c5433a393815c74f9e3087300613a516e2fb`, owner-accepted); Decision 029 §12 step 8 prepared and validated the external evidence root and operator manifest, and the **step 9 operational rehearsal ran once on 2026-08-03 and passed** — all twelve A1–A12 scenarios PASS, zero actual SEC requests, and `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED` emitted by the canonical command; **steps 10 and 11 are complete** — two byte-identical zero-request M3.2A plans (request-plan SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, q = 70, 75 planned unique logical requests, 801 maximum physical attempts) and a passing canonical budget display, with the **owner approving the exact hard request ceiling 801 on 2026-08-03** (three response-outcome expectations deliberately unresolved); **step 12 is signed and complete (2026-08-03)** — the sole hygiene blocker was resolved by accepted Decision 030, the signing preflight validated the SEC identity and synchronized `main` (`HEAD == origin/main`), and the **owner-signed Gate F checklist** (result `PASS`; every item accepted; no unresolved blocker) is immutable private evidence with its SHA-256 recorded in the public evidence index alongside the plans, receipts, and the owner-approved request budget (ceiling 801); **step 13 owner-authorized and completed (2026-08-03)** — the Gate F readiness token emitted and recorded exactly once as immutable private evidence bound to the signed checklist, plan, budget, and ceiling, with the owner's evidence-index attestation recorded; **Gate F readiness recorded; Gate F execution not begun and live SEC access not authorized**; **step 14 complete and passed (2026-08-03)** — the independent acceptance review returned `M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS` (artifact SHA-256 `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`, commit `24fba32413bb6c5dade60a64182e42510afe6f88`); **the owner accepted M3.1 on 2026-08-03 and step 15 records that acceptance (accepted Decision 031)**; **step 16 complete (2026-08-03)** — the annotated `m3.1-complete` checkpoint created and pushed (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`, verified locally and remotely); **step 17 complete (2026-08-03)** — M3-L11 and M3-L12 `CLOSED` on their complete closure-evidence lists and the bounded M3.2 contract drafted ([`contracts/m3_2.md`](contracts/m3_2.md), `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE`), completing the Decision 029 §12 sequence. **The M3.2 contract was subsequently reviewed, corrected (accepted Decision 032), rereviewed fresh with no subagents (`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS`, 2026-08-04), and ACCEPTED unchanged at T1 (accepted Decision 034, 2026-08-04); M3.2 implementation not authorized (T2 pending) and not begun** | Decision 024 §5.1; Decision 027 v0.2; accepted [Decision 028](../Docs/Decisions/decision_028_m3_1_readiness_corrections.md); accepted [Decision 029](../Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md); accepted [`contracts/m3_1.md`](contracts/m3_1.md); accepted [Decision 031](../Docs/Decisions/decision_031_m3_1_acceptance.md); accepted [Decision 034](../Docs/Decisions/decision_034_m3_2_contract_acceptance.md) | — |

**M2.3 Stage S6 is accepted and immutable at `m2.3-s6-complete`.** The three completion tags
**supplement** every earlier checkpoint tag and move, replace, or re-point none of them.

**Closure closed the milestones, not their obligations.** Every accepted limitation stays active and
is inherited by Milestone 3 — Decision 020 §19.1, Decision 021 §19, Decision 022's applicability
boundary, and Decision 023 §7's **O1**–**O4**, with **O1** still an unresolved future owner-ruling
condition (Decision 026 §12). **The project is not complete**: no live SEC pilot has been executed,
no real snapshot or real manifest exists, no root has been approved, and nothing has been published.

## Accepted baseline

- Branch: `main`.
- Closeout commit: the commit created by the 2026-07-31 governance-only closeout session
  ("Close Milestones 0 1 and 2"), carrying the three annotated completion tags `m0-complete`,
  `m1-complete`, and `m2-complete`. This file records no hash for it by design; resolve it live with
  `make context`.
- Accepted methodological checkpoint tag: `m2.3-s6-complete` -> the commit created by the 2026-07-31
  acceptance-recording session ("Complete M2.3 S6 deterministic pilot manifest"). This file records
  no hash for it by design; resolve it live with `make context`.
- Immediately preceding checkpoint tag: `m2.3-s5.4-complete` -> the commit created by the
  2026-07-30 checkpoint session ("Complete M2.3 S5.4 reserve architecture").
- Earlier checkpoint tag: `m2.3-s5-complete` -> the commit created by the 2026-07-29
  checkpoint session ("Complete M2.3 S5 joint selection checkpoint"). **`m2.3-s5-complete` and
  `m2.3-s5.4-complete` are immutable and were never moved, replaced, or re-pointed**;
  `m2.3-s5.4-complete` supplements rather than replaces `m2.3-s5-complete` (Decision 020 §§14.9, 15),
  and `m2.3-s6-complete` supplements both (Decision 021 §22, Decision 023 §8).
- Earlier accepted commits: `921f57b` ("Approve Decision 018 accession selection policy"),
  `3b01c50` ("Add repository orientation and stage-contract workflow"),
  `f490281` ("Optimize offline test execution and parallel validation").
- Earlier checkpoint tags: `m2.3-s4-complete` -> `e7157aa` ("Complete M2.3 S4 deterministic entity
  selection and persistence"); `m2.3-s3.2-complete` -> `5fb8e27`.
- Migrations end at `0013_m23_manifest_lifecycle_guards.sql`, created and accepted at Stage S6. See
  `src/disclosure_drift/storage/migrations/` for the authoritative list.

## Current phase

**Milestones 0, 1, and 2 are formally closed (Decision 026). Milestone 3 master planning is complete
at Decision 027 v0.2. Decision 028 records the accepted planner-v2, corrected A1–A12, reason-code,
receipt-v2, budget, ceiling, recovery, and M3-L11 rulings after
`INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`. The bounded M3.1 contract is accepted and
implementation-authorized, and the M3.1 implementation is **owner-accepted** (accepted Decision
031, 2026-08-03) — Decision 029
code remediation is implemented, the implementation is frozen at
`970e050deb06910adcde8588101564beb7d19c74`, and the first durable §17 review passed
(`M3_1_SECTION_17_REVIEW: PASS`, artifact committed at
`66e4c5433a393815c74f9e3087300613a516e2fb`), and Decision 029 §12 steps 9–11 are complete — the
step 9 rehearsal passed with the M3.1A token emitted, step 10 produced two byte-identical
zero-request plans (request-plan SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`),
and step 11's canonical budget display passed with the owner approving the exact hard request
ceiling 801 on 2026-08-03 — step 12 was signed and completed on 2026-08-03 (checklist result
`PASS`; the sole hygiene blocker having been resolved by accepted Decision 030), step 13
completed on 2026-08-03 under separate owner authorization with the Gate F readiness token
durably recorded, step 14 (the independent M3.1 acceptance review) completed and passed on
2026-08-03 (`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`; artifact SHA-256 `caf9f26e…`; commit
`24fba32…`), and the owner accepted M3.1 on 2026-08-03 with step 15 recording that acceptance
(accepted Decision 031, `M3_1_ACCEPTED_AND_COMPLETE`); step 16 created and pushed the annotated
`m3.1-complete` checkpoint (2026-08-03); and step 17 closed M3-L11 and M3-L12 and drafted the
bounded M3.2 contract ([`contracts/m3_2.md`](contracts/m3_2.md), then `DRAFT — PENDING OWNER
REVIEW AND ACCEPTANCE`) — while Gate F execution has not begun and live SEC access remains
unauthorized. The contract was then reviewed, corrected (accepted Decision 032), rereviewed fresh
with no subagents (`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS`, 2026-08-04), and
accepted unchanged at T1 (accepted Decision 034, 2026-08-04); M3.2 implementation remains not
authorized (T2 pending) and not begun.** The rest of this
section is the accepted historical record of how Milestone 2.3 reached that point.

M2.3 (deterministic pilot selection). Stage S4 (entity-only selection) is accepted. Decision 018
(Stage S5 accession selection policy) and Decision 019 (Stage S5 frozen-storage-to-pure-input
mapping policy) are both **approved by the project owner 2026-07-28**. Decision 020 (Stage S5.4
reserve architecture and quota-contribution membership) is **approved by the project owner
2026-07-30**.

**Stage S5.1 is accepted. Stage S5.2 is accepted. The combined S5.1–S5.3 checkpoint is
owner-accepted** (2026-07-29) and committed under the single commit boundary Decision 018 §22 fixes.
The final independent re-review's recommendation was **`ACCEPT_M23_S5_3_CHECKPOINT`**, on a final
accepted suite of **1661 passed, 1 skipped** (the one skip is pre-existing: the `[sec]` extra is not
installed). **No acceptance blocker remains.**

**Stage S5.4 (reserves) is complete and owner-accepted** (2026-07-30). Decision 020 remains
`APPROVED — OWNER APPROVED 2026-07-30`. The stage was implemented under a separately issued bounded
implementation prompt confined to twelve authorized paths, reviewed independently, corrected under
bounded fixes D1/T1/T2/T3, re-reviewed, and accepted on the final independent recommendation
**`ACCEPT_M23_S5_4_FOR_CHECKPOINT`**, on a final accepted suite of **1899 passed, 1 skipped** (same
pre-existing skip). Migration `0012_m23_selection_entity_reasons.sql` was created and accepted. Its
contract — [`Milestones/contracts/m23_s5_4.md`](contracts/m23_s5_4.md) — is now
**`ACCEPTED_AND_COMPLETE`** with **`IMPLEMENTATION_AUTHORIZATION: NO`** and **no active blocker**. The
checkpoint is tagged **`m2.3-s5.4-complete`**, supplementing the immutable `m2.3-s5-complete`. **No
active S5.4 blocker remains**, and further S5.4 change requires a new explicit owner authorization.

**Stage S6 (pilot manifest construction, terminal result identity, and the publication boundary) is
complete and owner-accepted** (2026-07-31). Its governance is accepted at **v0.5**: Decision 021 v0.5
is `ACCEPTED` (owner approved 2026-07-30), Decision 022 is `ACCEPTED` (owner approved 2026-07-31) for
crosswalk item-46 applicability, and **Decision 023 is `ACCEPTED` (owner approved 2026-07-31)** and
records acceptance itself, outcome **`M23_STAGE_S6_ACCEPTED_AND_COMPLETE`**. v0.2 applied six bounded
owner corrections issued after the focused independent governance review of v0.1; v0.3 applied one
further correction widening the structural-fingerprint tuple to five columns; v0.4 applied two
corrections issued after the focused independent governance review of v0.3 — the exhaustive 81-item
milestone-plan §10 crosswalk and the growth of migration `0013` from four triggers to five; and
**v0.5 applied one owner ruling issued after the focused independent governance review of v0.4** —
migration `0013` grows from five triggers to **eight**, closing selection-run replacement, deletion,
and identity mutation. **v0.1, v0.3, and v0.4 were each independently reviewed and none was approved;
v0.2 was never independently reviewed.** [`Milestones/contracts/m23_s6.md`](contracts/m23_s6.md) is
now `ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO`. **No stage contract currently
authorizes implementation.**

**The Milestone 2 / Milestone 3 boundary is recorded.** Decision 024
(`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED`) fixes accepted
S6 as the **final implementation stage of Milestone 2** and transfers the obligations formerly called
S7–S10 **intact** into Milestone 3 as **M3.1–M3.4**, adding **M3.5** for integrated real-pilot
acceptance and Milestone 3 closeout. **No Milestone 3 phase has begun and none is authorized**: no
publication, approval, CLI, live-metadata, real-snapshot, or Milestone 3 work exists, and no S7 or
Milestone 3 contract exists. **No S5 selection and no reserve is a published or owner-approved
input** — S6 creates only a `proposed` manifest, over fixtures. That audit, its bounded corrections,
and its rereviews are now complete, and **Milestone 2 is formally closed** (Decision 026). See
"Milestone closure state" above and "Current stage" below.

## Completed stages

- **Stage S3** — candidate/selection/manifest schema (migration `0009`). Governed by Decision 016.
- **Stage S4** — deterministic constrained entity-selector core (S4.1,
  `src/disclosure_drift/sec/entity_selector.py`) and candidate-snapshot reconstruction plus
  entity-selection persistence (S4.2, `src/disclosure_drift/sec/entity_selection_store.py`).
  Governed by Decision 013 §5 and Decision 017. Checkpointed at `m2.3-s4-complete` (`e7157aa`).
  Persists an **entity-only running draft**; `run_state` stays `running` because accession-level
  objective terms (S5) can still change the joint optimum — see
  `Docs/architecture_map.md` §5 and §6.
- **Migration `0010`** — seeds the frozen `PILOT_QUOTA_POLICY_VERSION` (Decision 017), additive only.
- **pytest-performance maintenance phase** — accepted. Nonblocking; see the maintenance note below.
- **S5 architecture preflight** — complete. Concluded that no migration-`0009` schema contradiction
  blocks S5, and that Decision 018 must exist before S5.1 implementation begins. The preflight's
  proposed rules were **proposals**, not policy; those the project owner approved are now frozen by
  Decision 018, and the record — not the preflight — is authoritative for each of them.
- **Decision 018** — approved by project owner (2026-07-28),
  `Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md`. Freezes Stage S5 accession
  selection policy: roles, caps, entity accession floors, the applicability-aware evidence penalty
  within the unchanged Decision 013 §5 objective order, canonical dashed accession identity and the
  tie-break formula, the deterministic `selected_order` rule, S4-draft disposition and a distinct
  content-derived S5 joint run, families and linked-amendment coverage, cross-cutting quota
  operationalization, node-limit/failure/retry semantics, and the S5.1–S6 stage boundaries.
  **Policy only — it authorizes no implementation and no repository code changed with it.**
- **Decision 019** — approved by project owner (2026-07-28),
  `Docs/Decisions/decision_019_m23_s5_storage_to_pure_input_mapping.md`. Approved **as written**,
  after a final independent audit whose recommendation was
  `ACCEPT_DECISION_019_FOR_OWNER_APPROVAL` (no ambiguities, no implementation blockers, no scope
  violations, total and deterministic mappings, compatible with the accepted S5.1 core, no required
  DDL, no new quota deferral, governance consistent); the audit's four documentation-precision notes
  are nonblocking and alter no approved mapping. Freezes the four storage-to-pure-input mappings —
  amendment-linkage evidence conversion, multi-registrant evidence aggregation, explicit pre-study
  support provenance, and former-name identity-evidence conversion — plus the snapshot-freeze
  obligations and the run-identity content they contribute. **Policy only — it modifies no accepted
  S5.1 artifact, authorizes no implementation, and no repository code changed with it.**
- **Stage S5.1** — pure accession-candidate and joint entity-accession selection core
  (`src/disclosure_drift/sec/accession_selector.py`) with its adversarial in-memory tests
  (`tests/unit/test_m23_accession_selector.py`). Governed by Decision 013 §5 and Decision 018.
  **Accepted** by project-owner adjudication and independent recheck. It remains the **sole
  methodological selector**; S5.2 adds no second implementation of any policy function.
  Committed at `m2.3-s5-complete` under the combined S5.1–S5.3 boundary.
- **Stage S5.2** — frozen accession reader, deterministic S5 run identity, transactional
  persistence, and deterministic reconstruction
  (`src/disclosure_drift/sec/accession_selection_store.py`) with
  `tests/unit/test_m23_accession_selection_store.py`. Governed by Decision 018 and Decision 019.
  **Accepted.** Also carries additive migration `0011` (INSERT-only, no DDL), the frozen
  `PILOT_JOINT_SELECTOR_POLICY_VERSION` constant, the five Decision 018 §21 reason codes, and the
  bounded migration-catalog test updates. Two defects found by independent review were corrected
  before acceptance: the stored-evidence-level run-identity correction, and the same-ID
  reconstruction integrity correction (both public entry points now fail closed on the same stored
  identity corruption, through one centralized comparison over every
  `JointSelectionRunIdentity` field).
- **Stage S5.3** — independent adversarial review of S5.1 and S5.2 together, and the combined
  S5.1–S5.3 acceptance checkpoint. **Complete and owner-accepted 2026-07-29.** Final independent
  recommendation **`ACCEPT_M23_S5_3_CHECKPOINT`**; final accepted suite **1661 passed, 1 skipped**;
  no implementation defects, no acceptance blockers, no scope violations. Checkpointed at
  `m2.3-s5-complete`.
- **Decision 020** — approved by project owner (2026-07-30),
  `Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md`. Freezes the Stage S5.4 architecture:
  quota-contribution membership published from the sole accepted S5.1 witness derivation; reserves,
  contributions, and members written inside the S5 run's single `running` window; reserves as
  subordinate content under the accepted S5 run ID with the input-schema version unchanged; the exact
  migration-`0012` DDL (§8.2); the enforcement-layer test scoping (§8.3); one authorized reason code;
  and the nine owner rulings (§14). Its **§19 records final acceptance of the implemented stage**.
- **Stage S5.4** — quota-contribution membership, reserve packages, replacement signatures, durable
  no-compatible-reserve dispositions, their persistence inside the existing single transaction, and
  fail-closed reconstruction. Governed by Decision 013 §6, Decision 016 §7, and Decision 020.
  **Complete and owner-accepted 2026-07-30.** Final independent recommendation
  **`ACCEPT_M23_S5_4_FOR_CHECKPOINT`**; final accepted suite **1899 passed, 1 skipped**; no acceptance
  defects, no ambiguities, no checkpoint blockers, no scope violations. Delivered across exactly twelve
  authorized paths: the additive S5.1 membership output in `sec/accession_selector.py`; the new pure
  `sec/reserve_selector.py`; contribution, member, reserve, and disposition persistence and
  reconstruction in `sec/accession_selection_store.py`; the one new reason code
  `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` in `reasons.py`; DDL-only migration
  `0012_m23_selection_entity_reasons.sql` reproducing the Decision 020 §8.2 SQL byte-for-byte; and
  seven test modules. Four defects found by independent review were corrected before acceptance
  (bounded fixes **D1, T1, T2, T3**): the filing-year derivation was centralized on the accepted-core
  helper so the reserve module holds no parser of its own and malformed non-null stored dates raise
  `GateFailureError`; persisted signatures gained independent recomputation from normalized content in
  repository tests; and multi-witness load-bearing entity contributions gained non-vacuous coverage.
  The accepted S5 selection, objective, quota results, amendment families, `selection_input_sha256`,
  and `selection_run_id` are **unchanged**, verified by running the pre-S5.4 code and the accepted code
  over the same frozen snapshot. Checkpointed at `m2.3-s5.4-complete`, supplementing the immutable
  `m2.3-s5-complete`.
- **Decision 021** — accepted by project owner (2026-07-30),
  `Docs/Decisions/decision_021_m23_s6_manifest_construction.md`, **v0.5**. Freezes the Stage S6
  architecture: every digest preimage, the root, `manifest_id` and its six-field immutability, the
  circularity exclusions and commitment closure, eligibility, the proposed-only boundary,
  reconstruction and replay, the thirteen-block document contract with the exhaustive 81-item §10
  crosswalk, the S4/S5 boundary, the complete eight-block migration-`0013` SQL and its nine digests,
  the §15.5 append-once and identity guarantee, the no-new-surfaces and CLI-narrowing rulings, and
  the S7–S10 boundary. Accepted on the fourth focused independent governance review
  (`ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL`); the first three each returned
  `REQUIRES_OWNER_CLARIFICATION`. **Remains the controlling S6 architecture record.**
- **Decision 022** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_022_m23_s6_reserve_rank_applicability.md`. The owner clarification of
  crosswalk item 46: reserve rank is applicable **once per persisted reserve package** and is
  **structurally not applicable** for a selected target carrying the persisted
  `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition instead; item 70 remains the total per-target
  coverage requirement; no synthetic package or invented rank may be created or serialized. Issued
  after a fresh independent S6 implementation audit correctly stopped under Decision 021 §§21 and
  13.3 and referred the conflict rather than resolving it. **Supersedes and amends nothing.**
- **Decision 023** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md`. Records **formal owner
  acceptance of Stage S6** (`M23_STAGE_S6_ACCEPTED_AND_COMPLETE`) on the final independent
  recommendation `ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING`; **ratifies three
  forced-consequence test paths**; records **four accepted nonblocking limitations O1–O4**; and
  authorizes exactly one commit, one push, the annotated tag `m2.3-s6-complete`, and one tag push.
  **Adds no architecture and reopens no ruling**; grants no Stage-S7 and no Milestone 3 authority.
- **Stage S6** — deterministic pilot-manifest construction, terminal result identity, and the
  publication boundary. Governed by Decision 013 §§7–8, Decision 016 §§1, 5, 8, Decision 018 §22,
  Decision 020 §§9, 11, 14.4, milestone plan §10/§16, and — controlling — Decision 021 v0.5 with
  Decision 022. **Complete and owner-accepted 2026-07-31.** Implemented under separately issued
  bounded authorizations, corrected once under Decision 022, rereviewed independently
  (`ACCEPT_M23_S6_IMPLEMENTATION_FOR_ACCEPTANCE_REVIEW`), and accepted on the final independent
  recommendation **`ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING`** — no methodological findings, no
  implementation defects, no test defects, no outstanding owner clarifications, no acceptance
  blockers. Final accepted suite **2324 passed, 2 skipped**, reproduced under the parallel and
  alternate-temp-root runs alike. Delivered across **ten** implementation and test paths: the new
  pure `release/pilot_manifest.py`; the new `sec/pilot_manifest_store.py`; DDL-only migration
  `0013_m23_manifest_lifecycle_guards.sql`, reproducing the Decision 021 §15.1 eight-block SQL
  byte-for-byte over a 10939-byte, 186-line statement region with all nine §15.3 digests; the two new
  S6 test modules; bounded edits to `test_m23_pilot_schema.py` and `test_migration_provenance.py`;
  and the three ratified forced-consequence test paths `test_storage_catalog.py`,
  `test_m23_entity_selection_store.py`, and `test_m23_accession_selection_store.py`. Unchanged and
  verified unchanged at acceptance: all 81 crosswalk rows and their totals (D 42 / T 30 / X 8 /
  S9 1 / S10 0 / unclassified 0), every hash preimage, all eight triggers, migrations `0009`–`0012`,
  and all accepted S4 and S5 behaviour. Checkpointed at `m2.3-s6-complete`, supplementing the
  immutable `m2.3-s5-complete` and `m2.3-s5.4-complete`.

- **Decision 024** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_024_m2_m3_boundary_governance.md`. The **Milestone 2 / Milestone 3
  boundary**: accepted S6 is the final implementation stage of Milestone 2; Milestone 2 consists of
  M2.1, M2.2, and M2.3 through accepted S6; **Milestone 2 is implementation-complete but not formally
  closed**, open only for the final integrated audit, bounded correction, rereview where required,
  and closeout; and the obligations formerly called S7–S10 move **intact** into Milestone 3 as
  **M3.1–M3.4**, with a new **M3.5** for integrated real-pilot acceptance and Milestone 3 closeout.
  Its §5.2 traceability table records every phase's inherited gates, prohibitions, required owner
  decision, required validation, and implementation-authorization status — **`NO` for every phase**.
  Formal outcome **`M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED`**. **Governance only**: it changed no
  production, test, migration, or configuration byte, granted no implementation authority, and
  authorized one commit and one push with **no tag**.

- **Decision 025** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_025_integrated_audit_documentation_corrections.md`. Records the **final
  independent integrated Milestones 1 and 2 audit** result `REQUIRES_BOUNDED_INTEGRATED_FIXES`, with
  **nine categories confirmed `INTEGRATED_ACCEPTANCE_CONFIRMED`** (Milestone 1, M2.1, M2.2, M2.3,
  Milestone 2 integrated, governance, reproducibility, security and leakage, test adequacy), the
  Milestone 3 boundary `GOVERNANCE_READY_IMPLEMENTATION_NOT_AUTHORIZED`, and the single
  `PROJECT_DOCUMENTATION_CLASSIFICATION: REQUIRES_BOUNDED_FIX`. **The audit found no implementation,
  methodology, migration, hashing, selection, manifest, leakage, security, or test defect.** It
  authorizes the bounded documentation correction — `Docs/sec_data_dictionary.md` extended from
  migrations `0001`–`0008` to `0001`–`0013`, covering the 22 `pilot_*` tables and the `0012`/`0013`
  trigger inventories — plus deviation-register navigation to `Docs/preregistration.md` §25. Formal
  outcome **`INTEGRATED_AUDIT_DOCUMENTATION_CORRECTIONS_AUTHORIZED`**. **Documentation and governance
  only**: no schema, migration, code, test, configuration, methodology, hash, or accepted decision
  outcome changed, and no implementation authority granted. It also records the **independence
  disclosure** that the same conversation authored Decisions 023 and 024, which establishes no
  technical defect but requires a **fresh independent verification** before closeout.

- **Decision 026** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md`. The **formal closeout of
  Milestones 0, 1, and 2**, recorded on the final fresh independent rereview
  `ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT` with **no closeout
  blocker remaining**. It records the closeout baseline, the eleven-step review chain from the
  stage-level implementation reviews through the explicit **Milestone 0** standalone audit, all
  sixteen final classifications, and what each milestone's closure covers: **Milestone 0** (§6)
  research question and framing, novelty review, preregistration, frozen cohorts, frozen outcome
  cutoffs, bootstrap seed `20260725`, the leakage register, the deviation register and D001, and the
  accepted governance foundation; **Milestone 1** (§7) repository and packaging foundation,
  configuration, cohort mirror enforcement, CLI and exit-code behaviour, offline safety, and secret
  and hygiene controls; **Milestone 2.1** (§8) offline SEC policy, identifier and temporal policy,
  response and rate-limit policy, the storage/provenance/schema-drift/release/forecast boundaries,
  and the CompanyFacts-disabled and Frames-prohibited policy; **Milestone 2.2** (§9) controlled
  live-metadata readiness, SEC identity requirements, transport isolation, deterministic request
  governance, raw-store provenance, and offline test and CI boundaries; and **Milestone 2.3 through
  S6** (§10) deterministic candidate and snapshot identity, entity and accession selection, reserves
  and dispositions, persistence, reconstruction and replay, selection-result sealing, manifest
  construction, canonical serialization, lifecycle enforcement, verification and atomicity, and the
  accepted limitations. Formal outcome **`MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`**. It
  authorizes the three annotated completion tags `m0-complete`, `m1-complete`, and `m2-complete` at
  the closeout commit, confirms every existing implementation-stage tag immutable, leaves the
  **inherited limitations register active** (§12), records the nonblocking `pilot_reserves`
  PK-superset UNIQUE presentation observation as requiring no correction (§13), and makes
  **`MILESTONE_3_MASTER_PLANNING`** the next authorized action. **Governance only**: it changed no
  production, test, migration, configuration, or CI byte, edits no earlier decision, and **grants no
  Milestone 3 implementation authority** — closure satisfies only the precondition Decision 024 §8
  imposed, and all five of that record's entry conditions still apply in full.

- **Decision 027 v0.1 (historical initial planning text)** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md`. The **Milestone 3 master
  plan and operational-readiness design**. It records the exact Milestones 0–2 closeout baseline
  verified live; confirms **Decision 024 controlling** for the M2 → M3 obligation transfer and
  **Decision 026 controlling** for the closeout; fixes the planned **M3.1–M3.5** phase map with each
  phase's network permission and completion token; introduces the **M3.1A / M3.1B** planning
  subdivision, which creates no new milestone and no new phase and takes no tag for M3.1A; requires a
  **documentation-first operator runbook** before any live access; requires the **complete offline
  rehearsal to pass before the first SEC request**; requires **one execution receipt per live
  command**; froze the **seven operational templates then present in v0.1**; requires the
  **Milestone 3 limitations register**, seeded with every inherited limitation and closing none;
  fixes the **sequential model
  and validation policy** — Opus Max for architecture, contracts, owner decisions, consequential
  methodology, focused independent reviews, exact-root approval preparation, and final integrated
  acceptance; Sonnet High or Max for bounded implementation; **Haiku nowhere on the critical path** —
  with targeted checks during implementation and one full suite plus every repository gate at each
  phase end; fixes the **one-implementation-commit-per-phase default** and the **annotated-tags-only,
  after-independent-acceptance-only** tag policy with the frozen future names `m3.1-complete`,
  `m3.2-complete`, `m3.3-complete`, `m3.4-complete`, and `m3-complete`; fixes the **focused
  independent-review policy**; confirms that **request-volume values may not be invented**, that a
  derivable count is computed from accepted offline inputs and reproduced, and that an underivable one
  is written `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` with its exact formula, its count
  dependencies, the future zero-request planning command, a hard ceiling, and mandatory owner approval
  before network enablement; confirms that **operational receipts are outside the accepted S5 and S6
  substantive identity graphs**; prohibits any execution receipt, receipt digest, timestamp, request
  count, response total, path, SEC identity, or operational state from contaminating candidate
  identity, selection identity, `selection_result_sha256`, any component digest,
  `root_manifest_sha256`, or `manifest_id`; and prohibits any full SEC identity, secret, personal
  path, raw response body, filing text, outcome value, or restricted substantive payload from
  appearing in a receipt. Formal outcome
  **`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`**. **Governance and documentation
  only**: it changed no production, test, migration, configuration, or CI byte, created no runtime
  code, CLI surface, or database table, created **no implementation contract**, and **grants no
  Milestone 3 implementation authority** — planning a phase is not authorization to begin it, all five
  Decision 024 §8 entry conditions still apply per phase, and implementation authorization remains
  `NO`. It authorized one planning/governance commit and one push, and **no tag**.
  **Next authorized action: `INDEPENDENT_M3_MASTER_PLAN_REVIEW`.**

- **Decision 027 v0.2** — accepted by project owner (2026-07-31), the **corrected** Milestone 3
  master plan. **The record has been `ACCEPTED` since v0.1; v0.2 does not change that and creates no
  second numbered decision.** v0.2 applies eleven bounded owner corrections issued after the required
  independent review of v0.1, recorded in its **§0 revision history**, superseding only the affected
  v0.1 operational-planning language: (1) **M3.1 rehearses acquisition only** — the snapshot,
  selection, reserve, sealing, manifest, and root scenarios move to **M3.3A**, under the frozen rule
  that **no scenario may be placed in a phase that lacks the production path it exercises**;
  (2) **M3.2 becomes two sequential windows** — M3.2A bootstrap, then transport disabled, objects
  frozen, dependent references **derived** from them, a second zero-request plan, and a **second
  exact owner approval**, then M3.2B — with **the 10% contingency withdrawn**; (3) **M3.3A** builds
  and rehearses the candidate-snapshot builder before **M3.3B** freezes anything real; (4) **M3.4
  always requires a bounded contract and is never documentary** — M3.4A validates a minimal
  approval-recording entry point against synthetic catalogs, M3.4B invokes it once after explicit
  approval, and **manual SQL against the real catalog is prohibited**; (5) the v0.1 derived counts,
  subtotal, plan hash, and maximum-attempt total are **withdrawn** — faithful to the accepted planner
  but **not** to Decision 013 §1 — and the resulting **`CURRENT_PLANNER_DISCREPANCY` is recorded,
  unresolved, and blocks Gate F**, with Decision 013 byte-unchanged; (6) **`A_max = 12` and
  `planned × 12` are withdrawn** — maximum reachable physical attempts is **derived per route from
  the implemented response-policy state machine and independently tested**; (7) **one** receipt
  integrity identity, `receipt_id`, with `receipt_content_sha256` **removed**; (8) every receipt field
  classified **required / conditionally required / prohibited by invocation mode**; (9) `rehearsal`
  and `dry_run` receipts report **zero actual network counts**, with simulated totals in the rehearsal
  evidence report; (10) a **two-layer evidence model** — the public repository tracks blank templates,
  planning records, the limitations register, and a new **evidence index** carrying artifact type,
  phase, status, SHA-256, and a non-sensitive reference identifier, while **completed operational
  evidence lives in an owner-controlled private evidence root outside the repository**; and (11) the
  claim that **any regeneration necessarily creates a new root is withdrawn as false** — unchanged
  governed state plus byte-identical canonical serialization produces the **same** root, an
  independently re-derived identical root **remains the same approved value**, and only a differing
  root, changed governed state, or a superseding manifest requires a new packet. **Governance and
  documentation only**: no production, test, migration, configuration, CI, or `.gitignore` byte
  changed; `Docs/Decisions/decision_013_pilot_selection_mechanics.md` is byte-unchanged; no runtime
  code, CLI surface, database table, or implementation contract was created; and **no Milestone 3
  implementation authority is granted**. It authorized one governance-only correction commit and one
  push, and **no tag**. **Next authorized action: `INDEPENDENT_M3_MASTER_PLAN_REREVIEW`.**

- **Decision 028 — accepted 2026-08-01.** The Decision 027 v0.2 rereview did not pass. Decision 028
  records the bounded reconciled corrections: planner policy
  `quarterly-index-instances/2.0`; the corrected A1–A12 matrix; future reason codes
  `SEC_REQUEST_CEILING_EXHAUSTED` and `SEC_ACQUISITION_INTERRUPTED`; ceiling equality; read-only
  M3.1 recovery inspection; `m3-execution-receipt/2.0`; corrected request-budget arithmetic; and the
  three-layer M3-L11 protection. It preserves Decision 013 and Decision 024, creates no contract,
  and grants no implementation or network authority. Its fresh independent rereview returned
  `INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`; formal outcome
  `M3_1_READINESS_CORRECTIONS_ACCEPTED`.

- **Milestone 3 master planning** — **complete at v0.2.** Delivered under Decision 027 across fourteen
  planning documents plus the navigation and status updates they require:
  [`Milestones/milestone_03_master_plan.md`](milestone_03_master_plan.md) (five phases, 36 specified
  fields each, the request-volume policy, and the mandatory contents of every future phase contract);
  [`Docs/m3/operator_runbook.md`](../Docs/m3/operator_runbook.md) (31 sequential Mac steps, every
  command labelled `AVAILABLE NOW` or `PLANNED — NOT YET IMPLEMENTED`);
  [`Docs/m3/offline_rehearsal_spec.md`](../Docs/m3/offline_rehearsal_spec.md) (**two** rehearsals —
  **A1–A12** acquisition at M3.1A before the first SEC request, and **E1–E8** execution at M3.3A
  before the real snapshot freeze — each scenario with setup, command, response, reason code,
  persisted state, files, receipt, rollback, recovery, and validation; **specified, neither
  implemented, and neither run**);
  [`Docs/m3/execution_receipt_spec.md`](../Docs/m3/execution_receipt_spec.md) (the proposed
  `m3-execution-receipt/2.0` design, one integrity identity, corrected field timing and per-mode
  classification —
  **creating no code and no table**);
  [`Docs/m3/limitations_register.md`](../Docs/m3/limitations_register.md) (**37 active entries and one
  recorded as closed**, including active **M3-L11** private-evidence protection and active
  **M3-L12** planner-v2 implementation; their owner rulings are recorded but neither is closed); and
  the **eight** templates
  under [`Docs/m3/templates/`](../Docs/m3/templates/request_budget.md), including the new public
  [`evidence_index.md`](../Docs/m3/templates/evidence_index.md). **No implementation, no contract, no
  network access, no metadata acquisition, no snapshot, no pilot run, no manifest, no approval, and no
  publication occurred; at that planning checkpoint no M3.1 contract had been drafted.**

## Bounded documentation fix — complete, rereviewed, and accepted

The fresh independent verification required by Decision 025 §§8–9 has **run**. It confirmed
**Decisions 023, 024, and 025 independently** — each `INDEPENDENT_ACCEPTANCE_CONFIRMED` — and found
**no methodological, implementation, test, or governance defect**: the migration chain, the nine
migration-`0013` digests, the 81-item crosswalk and its totals, the ten delivered S6 paths and the
three ratified forced-consequence test paths, the obligation transfer into M3.1–M3.5, the deviation
register, and the correction commit's nonchange were all reproduced independently rather than
inherited. It returned **`REQUIRES_BOUNDED_VERIFICATION_FIXES`** on exactly two documentation items:

- **DOC-1 (the closeout blocker).** `Docs/sec_data_dictionary.md` gave 21 of the 22 `pilot_*` tables
  the complete per-table schedule Decision 025 §6.1 requires;
  **`pilot_projection_recovery_events`** carried only its name, state class, and no-writer status.
- **DOC-2 (cosmetic, pre-existing).** Blank lines before registry rows `023`, `024`, and `025`
  terminated the Markdown Index table.

**Both are now corrected**, together with three non-material precision notes, under the authority
Decision 025 §6.1 already granted. **No new decision record was required and none was created.**
`Docs/sec_data_dictionary.md` gains §13.5 covering `pilot_projection_recovery_events` in full —
migration `0009`, purpose, owning stage, `Operational-only` state class, 12 columns, PK `event_id`,
FK `manifest_id` → `pilot_manifest_versions`, the exact uniqueness position, every material CHECK,
the append-only lifecycle and both immutability triggers, writer none, reader none, digest role
none, the explicit exclusion from every manifest, component-digest, selection-result, root, and
manifest-identity input, and an explicit future-stage boundary. **All 22 `pilot_*` tables now carry
the complete schedule**, and the count distinction is preserved: **21** introduced by migration
`0009`, **one** more by `0012`, **22** through `0013`.

**Documentation only.** No production, test, migration, configuration, CI, methodology, schema,
hash, or database-behaviour byte changed; Decisions 021–025, every completed contract, and
`Docs/preregistration.md` are byte-unchanged; no tag was created or moved.

**The independent rereview of this fix has since run and passed.**
`FRESH_INDEPENDENT_BOUNDED_DOCUMENTATION_REREVIEW` returned
**`ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT`**, confirming
`INTEGRATED_ACCEPTANCE_CONFIRMED` for Milestone 0, Milestone 1, M2.1, M2.2, M2.3, and Milestone 2
integrated; `INDEPENDENT_ACCEPTANCE_CONFIRMED` for Decisions 023, 024, and 025; and
`VERIFIED_COMPLETE` for the data dictionary, the deviation register, project governance,
reproducibility, security and leakage, test adequacy, and documentation — with closeout readiness
`READY_FOR_FORMAL_CLOSEOUT` and **no remaining closeout blocker**. It also explicitly completed the
outstanding **Milestone 0** closeout classification. **Milestones 0, 1, and 2 are now formally
closed** ([Decision 026](../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md)). Its one
nonblocking presentation observation — `pilot_reserves` carrying a UNIQUE that is a superset of its
own primary key, present so the run/snapshot-scoped children have a declared composite FK target —
affects no schema correctness, reproducibility, methodology, or closeout and required no correction
(Decision 026 §13). **That statement was accurate when written and is now historical.** Milestone 3
completed its M3.1 phase under `contracts/m3_1.md`: the M3.1 implementation is owner-accepted
(accepted Decision 031, 2026-08-03) and checkpointed at the annotated `m3.1-complete` tag; the
M3.2 contract exists only as an unaccepted draft (`contracts/m3_2.md`), and M3.2 remains
unauthorized and not begun.

## Current stage

**Milestones 0, 1, and 2 are `FORMALLY_CLOSED` (Decision 026,
`MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`), tagged `m0-complete`, `m1-complete`, and
`m2-complete` at the closeout commit. Milestone 3 master planning is `COMPLETE` at **Decision 027
v0.2** (`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`). Decision 028 is accepted after
`INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`, and **Decision 029 is accepted
(`M3_1_REHEARSAL_COMPLETENESS_AND_REASON_SEMANTICS_ACCEPTED`, owner approved 2026-08-02)**. The
bounded M3.1 contract is **accepted** with `IMPLEMENTATION_AUTHORIZATION: YES`, and the M3.1
implementation is **OWNER-ACCEPTED** (accepted [Decision 031](../Docs/Decisions/decision_031_m3_1_acceptance.md),
2026-08-03, outcome `M3_1_ACCEPTED_AND_COMPLETE`). The Decision 029 §11 code
remediation is implemented, the implementation is frozen at
`970e050deb06910adcde8588101564beb7d19c74`, and the **first durable §17 review** by a non-author
session is complete, passed with verdict `M3_1_SECTION_17_REVIEW: PASS`, and is owner-accepted, its
artifact committed governance-only at `66e4c5433a393815c74f9e3087300613a516e2fb`. Decision 029 §12
step 8 prepared and validated the external evidence root and operator manifest; the step 9
operational rehearsal ran once on 2026-08-03 and passed, emitting the M3.1A token; **step 10 ran
the deterministic zero-request M3.2A plan twice on 2026-08-03 with byte-identical results**
(request-plan SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; q = 70;
75 planned unique logical requests; 801 maximum physical attempts); **step 11 rendered the
canonical budget display and the owner approved the exact hard request ceiling 801 on
2026-08-03**, deliberately leaving three response-outcome expectations unresolved as
`EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN`; **accepted Decision 030 resolved the sole
step-12 hygiene blocker** by a provably non-substantive one-path provenance redaction of the §17
review artifact (verdict `M3_1_SECTION_17_REVIEW: PASS` unchanged; `make hygiene` passes with zero
findings); and **step 12 is signed and complete**: the signing preflight validated the SEC contact
identity at the canonical boundary (value never displayed), synchronized `main`
(`HEAD == origin/main` at `55cf244a00428fbc8fa38d7b70af1bac8a7c45e9`), and recorded the operator
acknowledgement, and the **owner-signed Gate F checklist** (result `PASS`; owner Joseph Nihill,
project owner acting through the ChatGPT owner decision; 2026-08-03) is immutable private
evidence, SHA-256 `34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc`, backed up
and publicly referenced in the evidence index. **Step 13 was owner-authorized and completed on
2026-08-03**: the Gate F readiness token was emitted and recorded exactly once as immutable
private evidence (SHA-256 `b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e`,
bound to the signed checklist `34fc0567…`, the plan `19be7bdc…`, the budget `2d453e0b…`, the
ceiling 801, and the checklist baseline `55cf244…`), the after-step-13 backup verified, and the
owner's evidence-index attestation of 2026-08-03 is recorded in the public index. **Step 14
completed and passed on 2026-08-03**: the independent M3.1 acceptance review by a fresh
non-author session returned `M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS` — artifact
`Docs/m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md`,
SHA-256 `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`, committed
governance-only at `24fba32413bb6c5dade60a64182e42510afe6f88` — with all validation gates green
(2739 passed, 1 pre-existing skip; the transport test ran), zero BLOCKER and zero MAJOR findings,
and three MINOR findings the owner accepted as nonblocking. **The owner accepted M3.1 on
2026-08-03** (verbatim instrument recorded by accepted
[Decision 031](../Docs/Decisions/decision_031_m3_1_acceptance.md), outcome
`M3_1_ACCEPTED_AND_COMPLETE`), and **step 15 records that acceptance in this governance-only
commit**. **Step 16 completed on 2026-08-03**: the annotated `m3.1-complete` checkpoint tag was created at
the acceptance commit and pushed (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled
target `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`, verified locally and remotely). **Step 17
completed on 2026-08-03** under the owner's explicit step-17 authorization: **M3-L11 and M3-L12
are `CLOSED`** on their complete closure-evidence lists, and the **bounded M3.2 contract is
drafted** at [`contracts/m3_2.md`](contracts/m3_2.md) with status `DRAFT — PENDING OWNER REVIEW
AND ACCEPTANCE` — completing the Decision 029 §12 seventeen-step sequence. **The token records
readiness only: Gate F execution has not begun, M3.2 implementation is not authorized, live SEC
access remains not authorized, no acquisition has begun, and no operational catalog exists. The
M3.2 contract — reviewed, corrected (accepted Decision 032), and rereviewed fresh with no
subagents (`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS`, artifact SHA-256 `91235a1a…`,
rereview commit `3069b03e…`) — is ACCEPTED unchanged at T1 (accepted Decision 034, 2026-08-04);
T1 grants no later gate, and the next authorized action is preparation and owner review of the
bounded T2 implementation-authorization packet.**
Nothing below is an active work item — the rest of this section is
the accepted record of the last implementation stage Milestone 2 closed over.

**M2.3 Stage S6 (pilot manifest construction, terminal result identity, and the publication
boundary) — complete, owner-accepted, and checkpointed.** Stage S5 is finished end to end: S5.1,
S5.2, and the combined S5.1–S5.3 checkpoint were owner-accepted 2026-07-29, and **S5.4 was
owner-accepted 2026-07-30** and checkpointed at `m2.3-s5.4-complete`. **Stage S6 was owner-accepted
2026-07-31** through
[Decision 023](../Docs/Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md) and
checkpointed at `m2.3-s6-complete`. **There is no active implementation contract**: every contract in
`Milestones/contracts/` is now `ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO`.

**What S6 delivered.** The eight component digests and `root_manifest_sha256` at their frozen
preimages; `selection_result_sha256` and its append-once sealing; `manifest_id` and its six-field
identity immutability; the complete thirteen-block pilot-manifest document, every one of the 81
atomic milestone-plan §10 items bound and asserted item by item; canonical JSON under
`DataTree.releases / "pilot"` with a content-derived filename; historical S5 reconstruction through
the accepted entry point; persistence of exactly one `proposed` manifest row atomically with its
document; public verification that re-derives everything and fails closed; write-free idempotent
replay; and DDL-only migration `0013` with its eight lifecycle, identity, replacement, and deletion
guards. **S6 creates only a `proposed` manifest, over fixtures.** No real snapshot exists, no
candidate-snapshot builder exists, no production catalog exists, and no code path approves or
publishes anything.

**Three forced-consequence test paths were ratified at acceptance** (Decision 023 §4). The S6
contract authorized seven implementation paths; migration `0013` forced three further test edits —
`tests/unit/test_storage_catalog.py` (the canonical migration chain is asserted by exact version and
name), and `tests/unit/test_m23_entity_selection_store.py` and
`tests/unit/test_m23_accession_selection_store.py` (their accepted corruption fixtures built their
preconditions with plain `UPDATE`s that trigger 8 now refuses). The final independent acceptance
review found the authorization gap and referred it rather than resolving it; the owner ratified all
three retroactively. **No production path changed, no S4 or S5 methodology changed, and no assertion
was removed, weakened, relaxed, skipped, or xfailed**; the rewritten corruption fixtures are narrower
and more fail-closed than the code they replaced. **The delivered S6 path set is therefore ten**, and
the ratification covers three named paths only — it is not a general widening.

**Accepted nonblocking S6 limitations** (Decision 023 §7). None is a defect; none requires an
implementation change.

- **O1 — an empty sole-carrier crosswalk family fails closed.** Where a §10 item has more than one
  serialized carrier, an empty family is accepted; where a family is an item's sole carrier, an empty
  family raises `GateFailureError`, as Decision 021 §21 designs. **No accepted current S5 plan
  reaches that condition.** If a lawful future run ever does, it is referred for an owner ruling —
  never resolved by reclassifying an item, adding a category, or changing a count.
- **O2 — the release root is assumed owner-controlled.** `Path.write_text` follows a symlink
  pre-positioned at the content-derived output path. Symlink-resistant publication was never an
  accepted S6 requirement. Verification still fails closed on wrong bytes, and no database row
  survives a failed write.
- **O3 — a pre-existing artifact at the content-derived path is outside the transaction's
  ownership.** Atomicity governs artifacts the current operation created: a fault leaves no new row
  and no new file. A pre-existing file at that exact name is not deleted; wrong bytes fail
  verification and an authorized retry repairs it.
- **O4 — item-46 enforcement is consistent defence in depth.** The Decision 022 applicability check
  and the per-record completeness check agree on every document; neither is vacuous. Reserve rank
  remains substantively enforced for every real package.

**Owner clarification recorded 2026-07-31 — Decision 022.** A fresh independent S6 implementation
audit confirmed the earlier bounded corrections and found one further conflict: a lawful, accepted,
feasible, sealed S5 run with **zero compatible reserve packages** — every selected target instead
carrying one persisted `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition, the shape Decision 020 §7.1
rules nonblocking and migration `0012` accepts as complete — passed all seven Decision 021 §11.2
eligibility conditions and sealed normally, but was refused at document verification because
crosswalk item 46's `reserves.packages[].reserve_rank` leaf cannot exist with zero packages. The audit
correctly stopped under Decision 021 §§21 and 13.3 and returned `REQUIRES_OWNER_CLARIFICATION`.
[Decision 022](../Docs/Decisions/decision_022_m23_s6_reserve_rank_applicability.md) is
**`ACCEPTED — OWNER APPROVED 2026-07-31`** and is the controlling record for that one point: reserve
rank is applicable **once per persisted reserve package** and is **structurally not applicable** for a
target carrying the disposition instead; **item 70 remains the total per-target coverage
requirement**; and no synthetic package, `reserve_rank = 0`, `null`, `"N/A"`, placeholder, or invented
rank may ever be created or serialized. Decision 021 remains `ACCEPTED` and otherwise unchanged — the
81-item crosswalk, its counts, every preimage, `manifest_id`, canonicalization, migration `0013`'s
bytes, its nine digests, and its eight triggers are all untouched.

**Active blocker: none.** Decision 021 v0.5 is `ACCEPTED` (owner approved 2026-07-30), Decision 022
is `ACCEPTED` (owner approved 2026-07-31), and Decision 023 is `ACCEPTED` (owner approved
2026-07-31). Both required independent reviews ran and passed — the fresh independent S6 rereview of
the corrected tree (`ACCEPT_M23_S6_IMPLEMENTATION_FOR_ACCEPTANCE_REVIEW`) and the separate final S6
acceptance review (`ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING`), neither performed by a session
that wrote the work it reviewed. No S5, S5.4, or S6 blocker remains.

**S6 governance was accepted at v0.5, and gated the stage in three steps — all now satisfied.**
[Decision 021](../Docs/Decisions/decision_021_m23_s6_manifest_construction.md) records the project
owner's S6 rulings and freezes the resulting architecture: the exact canonical preimage of
`selection_result_sha256` and of all eight manifest component hashes plus `root_manifest_sha256`; the
four terminal component boundaries, with the migration-`0012` reserve dispositions bound into
`reserves_sha256`; the source-content, candidate-table, quota-definition, and **eleven-field**
selector-policy allowlists, with dependency-lock, code-commit, Python-runtime, configuration,
decision-authority, and source-plan identity as **six** required explicit arguments never inferred
from Git, the environment, the interpreter, or the working tree; the `manifest_id` derivation and the
**immutability after insertion of all six manifest identity fields**; eight circularity exclusions
plus the commitment closure; fail-closed manifest eligibility; the proposed-only boundary; **the
complete pilot-manifest document contract — thirteen mandatory blocks operationalizing
[`milestone_2_3_pilot_selection_plan.md`](milestone_2_3_pilot_selection_plan.md) §10, with no
substantive serialized field left unbound by the root; S6 defines and fixture-tests the schema, S9
supplies the exact real-data instance — and the **exhaustive item-by-item §10 crosswalk** in §13.2.1
covering all **81** atomic §10 items in four categories with a frozen machine-checkable count of 42
direct, 30 transitive, 8 operationally excluded, 1 deferred to S9, 0 deferred to S10, and **0
unclassified****; the **five-column** structural-fingerprint partition rule; explicit
classification of six residual schema columns; canonical JSON under `DataTree.releases / "pilot"`;
and the complete frozen **eight-block** SQL and nine digests of one authorized future migration
`0013_m23_manifest_lifecycle_guards.sql` (§§15.1, 15.3), together with the **§15.5 append-once and
identity guarantee**. Its §3 records the **seven** schema gaps observed directly: `selection_result_sha256` is writable, overwritable, and clearable on any run in
any state **and a run can be inserted already `feasible` and already sealed**;
`pilot_manifest_versions` accepts — and approves — a manifest over a `running` or `infeasible` run,
including the permanently-`running` S4 draft; **no existing trigger protects any manifest identity
column**; **`INSERT OR REPLACE` rewrites a manifest row wholesale past every guard**, because every
existing manifest trigger is `BEFORE UPDATE` or `BEFORE DELETE` and SQLite fires no delete trigger for
replacement unless `PRAGMA recursive_triggers` is on, which this repository never sets; and — added
at v0.5 — **`pilot_selection_runs` itself is replaceable, deletable, and re-identifiable**, having no
delete guard of any kind and no trigger naming any identity column, so a sealed digest can be cleared
by `INSERT OR REPLACE`, the run removed by `DELETE`, and `selection_run_id`, `snapshot_id`, or
`selection_input_sha256` rewritten by direct `UPDATE` under either `recursive_triggers` setting.
**It authorized no implementation by itself.** Stage S6 required, in order: (1) a focused
independent governance **review of v0.5** of Decision 021 and the S6 contract — **SATISFIED
2026-07-30**, recommendation `ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL`; (2) owner acceptance of
Decision 021 v0.5 recorded in the registry — **SATISFIED 2026-07-30**; (3) a separately issued
bounded S6 implementation authorization — **SATISFIED**, issued and exercised, with one further
bounded correction authorized by Decision 022 §7.
[`Milestones/contracts/m23_s6.md`](contracts/m23_s6.md) is now `STATUS: ACCEPTED_AND_COMPLETE` with
`IMPLEMENTATION_AUTHORIZATION: NO`. It named **seven** authorized implementation paths — unchanged by
the v0.2, v0.3, v0.4, and v0.5 corrections, and preserved in the contract exactly as issued; the
delivered set is **ten**, the extra three ratified by Decision 023 §4. Every other path remains
prohibited.

**Four focused independent governance reviews have run; the fourth accepted the record.** The v0.1
review returned `REQUIRES_OWNER_CLARIFICATION` and produced owner corrections A–F, applied at v0.2;
**v0.2 was never independently reviewed**; v0.3 was reviewed on 2026-07-30 and also returned
`REQUIRES_OWNER_CLARIFICATION`, confirming the five-column fingerprint, the eleven-field §8.4 layer,
the acyclic digest graph, and the then-frozen four-block SQL and digests, while finding three
defects — an incomplete §10 crosswalk, identity immutability holding on the `UPDATE` path only, and
a "twelve blocks" heading over a thirteen-row table; v0.4 applied the two resulting owner
corrections; and the **v0.4 review**, also on 2026-07-30, returned `REQUIRES_OWNER_CLARIFICATION`
again — it accepted the crosswalk and the five-trigger manifest design and proved by direct probe
that `pilot_selection_runs` was still open to row replacement, deletion, and identity mutation.
**v0.5 applies the resulting owner ruling** and **withdraws the v0.4 five-block statement region, its
7436-byte and 129-line counts, and its concatenation digest `6bfb897c…` as a composition** — blocks
1–5 keep their exact bytes and their individual digests, which are **not** withdrawn — replacing it
with an **eight-block region of 10939 bytes over 186 lines**, digest `7f473802…`. The **v0.5 review** then returned
`ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL` with **no governance blockers and no owner
clarifications required**, having reproduced all nine §15.3 digests from the record bytes, applied
the extracted SQL to a scratch `0001`–`0012` catalog, and run 318 adversarial assertions across all
four `recursive_triggers` × `foreign_keys` combinations. **The project owner approved Decision 021
v0.5 on 2026-07-30**, with one editorial correction to §13.2.1's explanatory arithmetic —
**74 original bullets producing 81 atomic requirements** (74 + 7 compound splits = 81) — which
changes no crosswalk row, numbering, category total, digest preimage, trigger, or SQL byte.

**The v0.4 open finding is now closed (Decision 021 §19.11).** Triggers 6, 7, and 8 —
`pilot_selection_run_replacement_guard`, `pilot_selection_run_delete_guard`, and
`pilot_selection_run_identity_guard` — close run replacement, deletion, and identity mutation
respectively. **Trigger 2 was deliberately not widened or renamed**, so the seal lifecycle and run
identity stay separate, independently testable invariants. Decision 021 **§15.5** now states the
guarantee without qualification: every new run begins unsealed, an existing run cannot be replaced, a
run cannot be deleted, the persisted run identity cannot change, sealing occurs only through the
guarded update on an already-`feasible` run, a sealed digest cannot change or clear, identical
restatement stays idempotent, `selection_input_sha256` cannot change before or after sealing, and
`selection_result_sha256` is therefore **append-once and remains recomputable from its persisted
preimage** across every direct SQLite write path. `selection_input_schema_version` needs no guard: it
is not a `pilot_selection_runs` column at all, and is supplied as the accepted code constant
`ACCESSION_SELECTION_INPUT_SCHEMA_VERSION`.

**v0.2 applied six bounded owner corrections** issued after the focused independent governance review
of v0.1 (recommendation `REQUIRES_OWNER_CLARIFICATION`, 2026-07-30): (A) six-field manifest-identity
immutability; (B) migration `0013` grows from three triggers to **four** (five at v0.4), with completely restated
normative SQL and digests — the v0.1 SQL and digests are **withdrawn**; (C) the complete manifest
document contract, citing milestone plan §10 explicitly, with the consequent extension of
`selector_policy_sha256`; (D) the structural-fingerprint partition rule; (E) explicit classification
of six residual schema columns; (F) the CLI narrowing and the complete S7–S10 boundary.

**v0.3 applies one further bounded owner correction, to the fingerprint only.** The structural tuple
widens from three columns to **five** — `region`, `state`, `observed_type`, `member_name`,
`record_path` — under the same partition-and-equality rule, and the v0.2 accepted limitation claiming
`observed_type` and `record_path` were unbound is **withdrawn and replaced** with an accurate one:
`parser_run_id` is used only for cross-run consistency checking and excluded from identity, duplicate
identical rows are collapsed, row order is excluded, and all five substantive structural fields are
bound. The eleven-field `selector_policy_sha256` layer of v0.2 is accepted and unchanged.

**v0.4 applies two further bounded owner corrections, issued after the focused independent governance
review of v0.3 returned `REQUIRES_OWNER_CLARIFICATION`.** (A) **The exhaustive milestone-plan §10
crosswalk** (§13.2.1): the review found that nineteen §10 items and four partially covered items were
neither serialized nor classified while the record claimed only two deliberate omissions, so §10 is
now enumerated **atomically** — **81 items**, every compound bullet split — each classified into
exactly one of four categories, with a frozen count of 42 direct, 30 transitive, 8 operationally
excluded, 1 deferred to S9, 0 deferred to S10, and **0 unclassified**; §13.2's "twelve blocks"
heading over a thirteen-row table is corrected to thirteen in the same pass. (B) **Migration `0013`
grows from four triggers to five**: the review demonstrated that six-field identity immutability held
on the `UPDATE` path only, because `INSERT OR REPLACE` rewrites a manifest row wholesale — identity,
lineage, all eight component digests, the root, and the state — past trigger 4 and past all four of
migration `0009`'s manifest triggers, including over an `owner_approved` manifest. Trigger 5,
`pilot_manifest_versions_replacement_guard`, closes all three uniqueness routes with `BEFORE INSERT`
predicates that hold under every pragma setting. **The crosswalk required no preimage change**, and
blocks 1–4 keep their exact bytes and digests; the **v0.3 four-block region, its 4990-byte and
88-line counts, and its concatenation digest `51151767…` are withdrawn**, replaced at v0.4 by a
five-block region of 7436 bytes over 129 lines — **itself since withdrawn as a composition at v0.5**
in favour of the eight-block region of 10939 bytes over 186 lines.

**v0.5 applies one further bounded owner ruling, issued after the focused independent governance
review of v0.4.** That review accepted the 81-item §10 crosswalk and the five-trigger manifest design
and proved by direct probe that `pilot_selection_runs` was still open on the three fronts the
manifest table had just been closed on: **row replacement**, **deletion**, and **identity mutation**.
Migration `0013` therefore grows from five triggers to **eight** — trigger 6
`pilot_selection_run_replacement_guard`, trigger 7 `pilot_selection_run_delete_guard`, and trigger 8
`pilot_selection_run_identity_guard`, the last holding `selection_run_id`, `snapshot_id`, and
`selection_input_sha256` immutable. **Trigger 2 is neither widened nor renamed**, and blocks 1–5 are
retained byte-for-byte with their individual digests, which are **not** withdrawn; only the v0.4
five-block *composition* is. Decision 021 **§15.5** now states the append-once and identity guarantee
without qualification, and **§19.11 is closed**.

**v0.1 was reviewed but never approved and never left `PROPOSED`; v0.2 was never independently
reviewed and never approved; v0.3 and v0.4 were each independently reviewed and neither was accepted
for approval. All five are the same record, so nothing downstream was invalidated by any revision.**
No earlier conclusion carried over: each review reached its own conclusion, and the v0.5 review —
the one covering the eight-trigger SQL and the §15.5 guarantee — is the one the owner approved.

**The former Stages S7–S10 are now Milestone 3; at the Decision 024 boundary none had begun.** S6 delivered machinery plus a
fixture-tested document schema. [Decision 024](../Docs/Decisions/decision_024_m2_m3_boundary_governance.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`) transfers those obligations **intact** into Milestone 3:
Gate F live-metadata readiness becomes **M3.1**; controlled metadata-only SEC acquisition with Gate H
becomes **M3.2**; the frozen real candidate snapshot, deterministic execution, the exact real-data
manifest, and **the CLI output deferred from S6** become **M3.3**; explicit owner approval of the
exact root hash becomes **M3.4**; and a new **M3.5** covers integrated real-pilot acceptance and
Milestone 3 closeout. **No gate, prohibition, owner ruling, validation requirement, identity,
methodology, or accepted limitation was removed, weakened, renumbered, or rewritten by the move.**
No later phase is reachable: no candidate-snapshot builder and no production catalog exists. **At the
Decision 024 boundary no S7 or Milestone 3 contract existed and no Milestone 3 implementation
existed** — the bounded M3.1 contract and its implementation came afterwards; **no Gate F has passed,
no live-metadata allowlist exists, and no Milestone 3 phase after M3.1 has begun.** Neither S6
acceptance nor the boundary record authorizes any of it — **assignment to Milestone 3 is not
authorization to begin Milestone 3** (Decision 023 §9; Decision 024 §8).

**Stage S5.4 is complete and accepted.**
[`Milestones/contracts/m23_s5_4.md`](contracts/m23_s5_4.md) is now **`STATUS: ACCEPTED_AND_COMPLETE`**
with **`IMPLEMENTATION_AUTHORIZATION: NO`** — it remains on record as Stage S5.4's scope statement and
authorizes no new S5.4 implementation, exactly as the S5.1 and S5.2 contracts do for their stages. Any
future S5.4 change requires a **new explicit owner authorization** and its own contract.
[`Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md`](../Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md)
remains **`APPROVED — OWNER APPROVED 2026-07-30`** and is the controlling record for reserves; its
**§19 records the final acceptance**, and its **§19.1 records the five accepted methodological
limitations**. It authorizes no further implementation.

**What S5.4 delivered and what it left frozen.** Quota-contribution membership is published from the
sole accepted S5.1 witness derivation as one additive immutable output, and is the only membership
source for every consumer. Reserves, contributions, members, and dispositions are written inside the
S5 joint run's single `running` window, in one transaction, with the `running -> feasible` transition
as its last statement. Reserves are subordinate content under the accepted S5 run ID; each package
carries its own content-derived `reserve_package_id`. Migration `0012_m23_selection_entity_reasons.sql`
was created DDL-only, adding one `STRICT` table and four triggers and reproducing the Decision 020 §8.2
SQL byte-for-byte. Unchanged and verified unchanged: the S5 selection and objective, quota results,
amendment families, `selection_input_sha256` and `selection_run_id`, migrations `0009`–`0011`, every
policy version, `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` (still `pilot-joint-selection-input/1.0`,
not bumped), and `selection_result_sha256` (still `NULL`).

**Accepted methodological limitations, recorded for monitoring** (Decision 020 §19.1). None is a
defect; none requires an implementation change.

1. **Cross-anchor amendment-family resolution** follows the accepted resolved-root accession identity
   with no added anchor-equality condition, so an entity can be credited with a linked-amendment
   contribution for a unit named after a different anchor. Deterministic, conservative, and fail-closed
   for reserve construction; it neither weakens contribution-set equality nor alters run identity.
2. **Provenance-oriented union member sets** may contain more members than a minimal witness would
   require — the accepted consequence of the witness-union ruling. No minimal-witness optimization is
   authorized.
3. **Exact target-selected versus complete-replacement bundle comparison may reduce reserve
   availability.** No discretionary trimming, subset search, or package optimization is authorized to
   obtain compatibility.
4. **The seven named signature contribution values are counts of achieved units, not Boolean
   presence.** Intentionally conservative; it further reduces availability.
5. **The schema-layer subset/superset/empty transition-test observation is nonblocking** and was
   independently validated at acceptance (exact accepted; subset, superset, and empty each refused).
   Adding repository coverage at that layer is optional and at the owner's discretion.

**The owner's recorded S5.4 rulings**, all reflected in Decision 020 §14 and honoured by the accepted
implementation: exactly one rank-1 reserve package per target where a compatible reserve exists (no
multiple ranks at M2.3); no-compatible-reserve is target-specific, review-required, nonblocking, and
neither infeasibility nor node-limit exhaustion; `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` stays
`pilot-joint-selection-input/1.0`; `selection_result_sha256` stays `NULL` through S5.4; one additive
immutable S5.1 membership output; every selected entity including controls is a reserve target; a
replacement CIK may serve different targets, at most once per target, with no global uniqueness and no
cross-target assignment problem; exactly one new reason code, `REVIEW_PILOT_NO_COMPATIBLE_RESERVE`
(`REVIEW_PILOT_RESERVE_POOL_EXHAUSTED` is **not** authorized); and `m2.3-s5-complete` is immutable,
with `m2.3-s5.4-complete` supplementing it. A tenth ruling authorized migration `0012` in principle; an
eleventh is the test-scoping clarification (Decision 020 §8.3). All are satisfied.

**No stage contract currently authorizes implementation.** `Milestones/contracts/m23_s6.md`,
`m23_s5_4.md`, `m23_s5_2.md`, and `m23_s5_1.md` are **all closed and authorize nothing**; each
remains on record as its stage's scope statement. `ACTIVE_STAGE_CONTRACT` below names the S6 contract
because it is the most recent stage's contract and the snapshot script needs a resolvable path —
**authorization is carried by that contract's own status and by `IMPLEMENTATION_AUTHORIZATION` here,
which now read `ACCEPTED_AND_COMPLETE` and `NO`**, never by the fact that the marker names a path.
Per [`contracts/README.md`](contracts/README.md), a completed contract authorizes nothing further;
reopening a closed stage requires a new explicit owner authorization and its own contract.

**Milestone 2 implementation is complete at accepted S6; publication work has not begun and is not
authorized.** No manifest approval, publication, CLI, live-metadata, real-snapshot, or release work is
authorized (Decision 018 §22, Decision 021 §§4, 11.1, 16, 17; Decision 023 §9; Decision 024 §8); see
`Docs/architecture_map.md` §0 and §8. **No S5 selection and no reserve is a published or
owner-approved input** — the only manifest S6 can create is `proposed`, over fixtures. The **final
independent integrated Milestones 1 and 2 audit ran, its bounded corrections and rereviews completed,
and Milestone 2 is now formally closed** (Decision 026). Closure created no publication, approval,
CLI, live-metadata, or release authority — every prohibition above still stands.

**The S4 entity-only draft is unchanged.** It stays in `running` state, remains non-publishable, and
is excluded from S5 run identity and from every manifest input. It is never promoted, mutated,
deleted, or transformed into the S5 joint run (Decision 018 §§6, 27) — a permanently-`running` S4
draft is expected residue, not an abandoned run. S5.4 read it, wrote it, and changed it in no way.

## Next authorized action

**`OWNER_M3_2_T2_IMPLEMENTATION_AUTHORIZATION_DECISION`** — the ChatGPT owner's separate decision
on the prepared T2 packet, [`Docs/m3/m3_2_t2_implementation_authorization_packet.md`](../Docs/m3/m3_2_t2_implementation_authorization_packet.md)
(`PROPOSED — PENDING CHATGPT OWNER T2 DECISION`), prepared 2026-08-04 under
`OWNER_M3_2_T2_PACKET_PREPARATION_AUTHORIZATION: APPROVED`. The packet enumerates the exact
fifteen authorized paths (eight production, seven test), declines both conditional surfaces
(`sec/census_orchestrator.py`, `sec/index_retrieval.py`), discharges the accepted Decision 034 §6
R1 four-part requirement, fixes six bounded stages inside the contract §22 single-commit boundary,
and reproduces the proposed T2 instrument for the owner to issue, amend, or refuse. **Preparing
the packet authorized nothing and approved nothing** — T2 is ungranted until the owner issues that
instrument, and no executable byte may change before then. T3 (implementation acceptance), T4
(live-operation preflight), and each per-window T5 remain separate later owner acts.
**Nothing in this file authorizes a session to begin M3.2 implementation, enable SEC network
access or CompanyFacts, contact the SEC, begin acquisition, create or populate an operational
catalog, use the ceiling 801, or create any tag.**

`PREPARE_M3_2_T2_IMPLEMENTATION_AUTHORIZATION_PACKET` is **discharged (2026-08-04)** — the packet
described above was prepared, governance-only, changing no executable byte. Its historical
statement follows: preparation, for owner review, of the
bounded M3.2 T2 implementation-authorization packet (accepted
[Decision 034](../Docs/Decisions/decision_034_m3_2_contract_acceptance.md) §13; Decision 024 §8;
[`contracts/m3_2.md`](contracts/m3_2.md) §8, T2 row), as the owner directs. The packet must
satisfy all five Decision 024 §8 entry conditions and must carry the Decision 034 §6 R1 content:
the physical persistence location for item-level absent-object identities; the physical
representation of the `completed_with_absences` governance classification; the deterministic
linkage among the frozen receipt, the operational catalog, `m3 reconcile-requests`, and the
Gate H reconciliation; and tests proving `m3-execution-receipt/2.0` remains frozen with its
completion-status enumeration not silently extended. **Preparing or drafting the packet
authorizes nothing and approves nothing** — it must return to the ChatGPT owner for a separate
explicit T2 implementation-authorization decision, and no implementation may begin before that
decision. T3 (implementation acceptance), T4 (live-operation preflight), and T5 (per-window
live-operation authorization) remain separate later owner acts.
**Nothing in this file authorizes a session to begin M3.2 implementation, to enable SEC network
access or CompanyFacts, to begin acquisition, to create or populate an operational catalog, or to
create any tag.**

`FRESH_NO_SUBAGENT_INDEPENDENT_REREVIEW_OF_CORRECTED_M3_2_CONTRACT` is **discharged
(2026-08-04)**. The fresh independent rereview of the corrected contract by one non-author
session using no subagents completed 2026-08-04 with verdict
`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS` — zero BLOCKER, zero MAJOR, one MINOR (R1,
the receipt-enumeration surface, carried forward as mandatory T2-packet content by Decision 034
§6), one OPTIMIZATION (R2, nonblocking) — recorded in the durable artifact
`Docs/m3/reviews/m3_2_corrected_contract_independent_rereview_3bf9987dd72e1531da2f678fbbef735f37aefcf4.md`
(SHA-256 `91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf`, committed
governance-only at `3069b03ede9d805e9d0196a3e4c45c8cc68f42b7`), with independence, no-subagent
execution, and the container-continuity disclosure attested in the artifact's §1. **The owner
then accepted the corrected contract unchanged at T1** (accepted Decision 034, 2026-08-04,
`M3_2_CONTRACT_ACCEPTED_AT_T1`); acceptance grants no T2/T3/T4/T5 authority, enables no network
or CompanyFacts, and authorizes no acquisition, operational catalog, ceiling-801 use, or tag.

`CHATGPT_OWNER_REVIEW_AND_ACCEPTANCE_DECISION_FOR_M3_2_CONTRACT_DRAFT` is **discharged as a
correction decision (2026-08-04)**. The owner ordered the independent contract review of the
initial draft; it completed 2026-08-04 with verdict
`M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS` — zero BLOCKER; two MAJOR
(F1, completion semantics permitting false success; F2, boundary exactness including the unnamed
command-scoped network-enable change); four MINOR; one OPTIMIZATION — recorded in the durable
artifact
`Docs/m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md`
(SHA-256 `fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57`, committed
governance-only at `3fbaa12d671d0000f5b608bbf6fb271f78b4673f`). The owner adopted the findings in
the 2026-08-04 correction instrument recorded verbatim in accepted Decision 032
(`M3_2_CONTRACT_CORRECTIONS_RECORDED`), and the bounded corrections are applied: §14 separates
termination from successful completion and requires every required object present, hash-verified,
and fully provenanced, with any required-object absence enumerated in the window's receipt and
expressly owner-adjudicated before the between-windows freeze and before any M3.2B budget
approval; §16 names the single command-scoped network-enable configuration change
(`network.m3_acquire_enabled`, default `false`, read only by `m3 acquire --live`, with
`network.enabled` remaining `false` throughout every M3.2 window) and the complete expected
implementation and test surface including all six planned M3.2 commands; §12 gains the
conservative accounting rule for a hard-interrupted segment's unrecorded attempts; §20 gates
public indexing of the between-windows freeze artifacts on an authorized index-vocabulary
extension; §§5 and 15 explain the historical Gate-F-named unresolved-count sentinel without
renaming it; §18 requires a non-vacuous positive control for every critical refusal and
nonchange boundary; §19 names the exact nonchange proof; and the stale current-state prose in
[`contracts/README.md`](contracts/README.md) is corrected. **The review artifact is preserved unchanged
as a truthful correction review; per the owner's procedural ruling it does not satisfy the
acceptance-prerequisite review because its session used two read-only fact-gathering subagents
under the one-active-session restriction, so the corrected draft requires the fresh no-subagent
rereview above.** The correction decision authorizes no implementation, no network or
CompanyFacts enablement, no live SEC access, no acquisition, no operational catalog, and no use
of the M3.2A ceiling; implementation, test, script, and executable-configuration bytes remain
byte-identical to the frozen accepted SHA `970e050deb06910adcde8588101564beb7d19c74`.

`DECISION_029_SECTION_12_STEP_17` is **discharged — the seventeen-step sequence is complete.**
Under the owner's explicit step-17 authorization of 2026-08-03: **M3-L11 and M3-L12 were closed**
in the limitations register, each on its own complete closure-evidence list (bounded
implementation and tests in the frozen accepted tree; full validation; independent M3.1
acceptance `M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`; owner acceptance recorded by accepted
Decision 031; and the committed checkpoint — the verified annotated `m3.1-complete` tag), with
the Decision 030 Ruling D sequencing distinction preserved and Decision 013 byte-for-byte
unchanged; and the **bounded M3.2 contract was drafted** at
[`contracts/m3_2.md`](contracts/m3_2.md), status `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE`,
`IMPLEMENTATION_AUTHORIZATION: NO`, `NETWORK_AUTHORIZATION: NONE`. The draft implements master
plan M3.2 §§1–36 and global §16: the frozen M3.2A inputs (plan `19be7bdc…`, budget `2d453e0b…`,
ceiling 801, 75 logical requests, 70 quarterly indexes, 75 raw objects, 0 cache hits, no
contingency, 200.0 s spacing floor), strict stop-before-overflow, the accepted route allowlist
and denylist, redirect/attempt bounds, boundary-only SEC-identity handling, immutable raw-object
capture, per-command receipts, interruption and recovery behaviour, zero filing-body /
CompanyFacts / Frames / outcome access, no pilot selection during acquisition, the six-transition
owner gate ladder (T1 contract acceptance → T2 implementation authorization → T3 implementation
acceptance → T4 live-operation preflight → T5 separate per-window owner live-operation
authorization → T6 controlled execution, then canonical Gate H), and the M3.2B dependency
boundary (no planning before the M3.2A freeze; separately derived plan and budget; a separate
owner ceiling approval; no inheritance of the M3.2A ceiling). D023-O1 is carried forward as a
mandatory stop-and-refer condition. **The draft accepts nothing, implements nothing, enables
nothing, and contacts no SEC host.**

`DECISION_029_SECTION_12_STEP_16` is **discharged.** Under the owner's explicit step-16
authorization of 2026-08-03, the annotated checkpoint tag `m3.1-complete` was created exactly
once at the acceptance commit `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4` with the
convention-consistent annotation "Complete M3.1 acceptance checkpoint" (tag object
`638a02b780d912ff7b37a2f523277b9d451a015a`), pushed as the single ref
`refs/tags/m3.1-complete`, and verified locally and remotely (matching tag objects; matching
peeled targets; `HEAD == origin/main`; every prior tag unchanged; no tracked file changed; no
commit created).

`DECISION_029_SECTION_12_STEP_15` is **discharged.** Under the owner's explicit step-15
authorization of 2026-08-03, the owner's M3.1 acceptance is durably recorded: accepted
[Decision 031](../Docs/Decisions/decision_031_m3_1_acceptance.md) (`ACCEPTED — OWNER APPROVED
2026-08-03`, outcome `M3_1_ACCEPTED_AND_COMPLETE`) carries the verbatim owner instrument
(`OWNER_M3_1_ACCEPTANCE_DECISION: APPROVED`, 2026-08-03), bound to the independent-review commit
`24fba32413bb6c5dade60a64182e42510afe6f88` and review-artifact SHA-256
`caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`; the decision registry gains
row 031; M3-L11 and M3-L12 move to `CLOSURE-READY PENDING STEP 16` (neither closed — the
committed checkpoint tag is the sole remaining closure criterion); and this ledger records the
position. The acceptance commit is governance-only: implementation and test bytes remain
byte-identical to the frozen accepted SHA `970e050deb06910adcde8588101564beb7d19c74`. It creates
no tag and authorizes no Gate F execution, no live SEC access, and no M3.2 work.

`DECISION_029_SECTION_12_STEP_14` is **discharged.** The independent M3.1 acceptance review ran
on 2026-08-03 under explicit owner authorization, performed by a fresh session that authored none
of the M3.1 implementation, governance, review, rehearsal, planning, budget, checklist, token,
index, or status work. From a fresh external independent clone it re-ran the full phase-end
validation (ruff, format, mypy, full suite 2739 passed / 1 pre-existing skip with the transport
test run, sqlite-check, secrets, hygiene, context — all green), recomputed every accepted private
and public evidence SHA-256, independently reproduced the route witnesses, plan determinism, and
ceiling arithmetic (801 = 31 + 11 × 70), and answered all forty adversarial questions in the
accepting direction, including the step-13 token-mechanism and living-evidence-index authority
questions. Verdict: `M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`, with zero BLOCKER, zero MAJOR,
three MINOR findings (an environmental disk-exhaustion incident with a clean re-run;
same-device-only backups; the superseded M3-L12 register wording), and zero OPTIMIZATION
findings. Its durable artifact is
`Docs/m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md`
(SHA-256 `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`), committed
governance-only at `24fba32413bb6c5dade60a64182e42510afe6f88`. The review recorded a verdict
only; the owner's separate acceptance followed and is recorded by Decision 031.

`DECISION_029_SECTION_12_STEP_13` is **discharged.** The owner explicitly authorized step 13 on
2026-08-03. Every precondition was independently reverified read-only immediately beforehand (the
signed checklist's identity and `PASS` result; the exact acceptance reference; the operator
acknowledgement; the owner's evidence-index attestation; SEC identity valid at the boundary with
the value never displayed; network and CompanyFacts disabled; secrets, hygiene, and context
green; implementation bytes unchanged; zero live SEC requests; no prior token artifact or
emission). No canonical command exists for this token — the literal appears nowhere in the
implementation — so the recording used the repository's established governance-evidence
mechanism: a create-once, immutable private record in the evidence root's M3.1B run directory,
3,982 bytes, 62 lines, SHA-256
`b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e`, carrying the token literal
exactly once in its emitted-token field and binding it to the signed checklist
(`34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc`), the request plan
(`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`), the request budget
(`2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f`), the approved hard request
ceiling 801, the checklist baseline `55cf244a00428fbc8fa38d7b70af1bac8a7c45e9`, the public
step-12 recording commit `0334294bd420a829033094080a13e4df900da078`, and the date 2026-08-03 —
together with this public ledger marker. The after-step-13-token local backup verified completely
(14 files, every SHA-256 matching; `.env` excluded). The owner's evidence-index attestation is
recorded verbatim in the index's §8. The immutable signed checklist is unaltered: its signing-time
statement that the token was then unemitted remains historically correct. **The token records
readiness only.**

`DECISION_029_SECTION_12_STEP_12` is **signed and complete.** The final signing preflight
(2026-08-03) validated the owner-approved SEC contact identity at the canonical boundary
(`SEC contact identity: valid; value not displayed`; the value lives only in the ignored local
configuration and is never printed), synchronized `main` by one authorized, ancestry-proven,
normal fast-forward push and verified `HEAD == origin/main` at
`55cf244a00428fbc8fa38d7b70af1bac8a7c45e9`, and recorded the operator-runbook acknowledgement.
The owner then signed the checklist on 2026-08-03 — Owner **Joseph Nihill, project owner acting
through the ChatGPT owner decision**; Gate F result **`PASS`**; recorded acceptance reference
bound to the repository baseline `55cf244a00428fbc8fa38d7b70af1bac8a7c45e9`, the request-plan
SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, the request-budget
SHA-256 `2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f`, and the sanitized §17
review SHA-256 `9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3` (a transparent
recorded owner acceptance reference, not a handwritten, cryptographic, or third-party digital
signature). The **signed checklist** was instantiated once, immutably, in the evidence root's
M3.1B run directory — 23,463 bytes, 284 lines, SHA-256
`34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc` — with every template field
populated, every item `PASS`, no unresolved blocker, the operator acknowledgement and the
Decision 030 dispositions included, and the two explicit step-13 boundary lines preserved (the
readiness token **not emitted**; Gate F authorization **not granted**; the token literal occurs
nowhere in the artifact). The after-step-12-signed local backup verified completely (13 files,
every SHA-256 matching; `.env` excluded), and the public evidence index
([`Docs/m3/templates/evidence_index.md`](../Docs/m3/templates/evidence_index.md) — the recording
destination the M3.1 contract §6, master plan §§12.1/12.3 and M3.1 §30, and the operator runbook
name) now carries the eight non-sensitive M3.1A/M3.1B rows `EV-M31A-001`–`EV-M31B-006`,
including the signed checklist's digest; its §8 owner attestation remains pending.

The next required owner action: **review the bounded M3.2 contract draft and accept, correct, or
decline it** (transition T1 of the draft's §8 gate ladder), ordering its independent contract
review as the owner directs. Acceptance would be T1 only: M3.2 implementation authorization (T2,
under all five Decision 024 §8 conditions), implementation acceptance (T3), live-operation
preflight (T4), and each per-window live-operation authorization (T5) all remain separate,
explicit, later owner acts. No session may accept the contract, begin implementation, enable SEC
network access, or begin acquisition without them.

**The step-12 hygiene blocker is resolved.** Accepted
[Decision 030](../Docs/Decisions/decision_030_gate_f_step_12_owner_rulings_and_hygiene_remediation.md)
(`ACCEPTED — OWNER APPROVED 2026-08-03`, outcome
`GATE_F_STEP_12_OWNER_RULINGS_AND_HYGIENE_REMEDIATION_ACCEPTED`) authorized exactly one provably
non-substantive redaction of the machine-local absolute path material in the §17 review
artifact's clone-provenance sentence. The pre-redaction artifact identity
`sha256:73cb1eacf0fb5e29a8a1c2ea871692068caf3ebdc48cae161d6aef677ba8f3a3` remains the historical
identity of the owner-accepted review (its introducing commit is retained; history was not
rewritten); the sanitized tracked identity is
`sha256:9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3`. A normalized
comparison proved in both directions that the sole change is the approved substitution; the
verdict `M3_1_SECTION_17_REVIEW: PASS` occurs exactly once, unchanged; no completion-token
literal was added; implementation, test, script, and configuration bytes remain byte-identical to
the frozen reviewed SHA; the hygiene scanner was not weakened and no allowlist was created; and
`make hygiene` now passes with zero findings while `make secrets` continues to pass. Decision 030
also records the owner's Gate F interpretation rulings: the three request-budget response-outcome
markers are **permitted and nonblocking** (all §3 route counts resolved; the expectations are
intentionally resolved during controlled acquisition; no integer guessed);
**`M3-L12 GATE-F-FACING REQUIREMENT: SATISFIED`** — Gate-F-facing requirement satisfied;
administrative closure deferred to the later M3.1 acceptance and checkpoint sequence — blocking
neither checklist preparation, the owner step-12 signature, the step-13 readiness token, nor
beginning Gate F after valid step-13 authorization; and
**`D023-O1: LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED`**, stop-and-refer
if a lawful real run ever reaches it.

`DECISION_029_SECTION_12_STEP_9` is **discharged.** The single authorized offline operational
rehearsal ran on 2026-08-03 at `2026-08-03T12:35:01Z`, exit status `0`. All twelve A1–A12 scenarios
passed; `passed`, `complete`, `a_reachable_agrees`, and `a_reachable_fully_tested` are all true;
derived and tested route-key sets are equal across all nine routes with `unmeasured_routes` empty;
`actual_logical_request_count` and `actual_physical_attempt_count` are both `0`; and the canonical
command emitted `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED`, durably captured. Its three immutable
artifacts live under the external evidence root at
`runs/m3_1a_rehearsal_970e050deb06910adcde8588101564beb7d19c74/` — evidence report
`sha256:6308576a0a7df33813239f753b31b86754f3908d63d73e6521682db06a59e1e0`, receipt
`sha256:ea1f4be2c136827ac5d865eea0fabf73f0f716802e2ee8cd23aedf1965dbc81b` (`receipt_id`
`1c1980429833e41f6eaf07d3df7fb5a780daab2ffe291d9a67858821a1a618d6`), and stdout log
`sha256:4b42f95e4a00d5865eeb05ccc9f06fe08c51c68f07c56d5512d441c2ee7118ce`. The absolute private path
is never recorded here.

`DECISION_029_SECTION_12_STEP_10` is **discharged.** Under owner-supplied plan inputs (coverage
2009-01-01 → 2026-06-30, as-of 2026-06-30, calendar year 2026, an explicitly empty operator
calendar-evidence manifest, and a nonexistent operational catalog), `m3 plan-requests` ran exactly
twice on 2026-08-03 to different immutable output names and produced **byte-identical plans**:
request-plan SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` for both
files, under schema `m3-request-plan/1.0` and planner policy `quarterly-index-instances/2.0`. The
plan enumerates the seven M3.2A bootstrap routes with **q = 70** required quarterly-index
instances (2009QTR1–2026QTR2, including the closed 2026 Q2 required by Decision 013 §1), zero
already-satisfied instances, **75 planned unique logical requests**, **801 maximum physical
attempts**, 75 maximum new raw objects, 0 expected cache hits, and a 200.0-second rate-limiter
spacing floor. Both dry-run receipts validate (`invocation_mode` `dry_run`; actual logical-request
and physical-attempt counts both `0`). The accepted classification is
`STEP_10_PASS_BYTE_IDENTICAL`. The artifacts are immutable under the external evidence root at
`runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/` — both plans
`sha256:19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, receipts
`sha256:d7f602d8a537c925483cbb9b5021ca0313eb3288d26dcb7759aa9b1843f4f149` and
`sha256:ff116259d5f129aba94093bd0516b14fdbb4a5517538a2c29d59240823573111`, stdout logs
`sha256:e3bf5650871bde150dde4a2fe48f0bfbbb26e821a52750a9e90f000b2396cfff` and
`sha256:660e9c01396af9dfa471f160c6a11e8ecbee04b45db97f410286a02fa7d43bce`. The absolute private
path is never recorded here.

`DECISION_029_SECTION_12_STEP_11` is **discharged.** The read-only canonical `m3 show-budget`
command rendered the stored plan's eight governed budget quantities and the derived hard request
ceiling **801** (`31 + (11 × 70) = 801`), captured at
`runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/show_budget_stdout.log`
(`sha256:0e6722dcd960c54a49e4a1af44a5c15587d03109b262c7ee471a46b8071db508`); the accepted
classification is `STEP_11_BUDGET_DISPLAY_PASS`. **The owner approved the exact plan-bound hard
request ceiling 801 on 2026-08-03**, bound to request-plan SHA-256
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, with 75 planned unique logical
requests, 75 maximum new raw objects, 0 expected cache hits, and no contingency allowance. **Three
response-outcome quantities remain deliberately unresolved** as
`EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` by the owner's ruling — expected successful
responses, expected not-modified responses, and expected governed non-success responses; no
integer was approved or invented for them. The approval completes step 11 only: it does not
complete or sign the Gate F checklist, does not emit the readiness token, and does not authorize
live SEC access.

**Step 12 preparation is complete; the owner signature is outstanding.** The refreshed
after-step-11 local backup of the external evidence root verified completely (11 files, every
SHA-256 matching, including the canonical budget display and all step-9 and step-10 evidence),
and the private **M3.2A request-budget document** was then created once, immutably, in the
evidence root's M3.1B run directory — 21,633 bytes, 307 lines, SHA-256
`2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f` — recording the plan-derived
quantities, the per-route independently tested `A_reachable` witnesses, the verbatim owner ceiling
approval of 2026-08-03, and the three deliberately unresolved response-outcome markers. The
after-step-12-prep local backup then verified completely (12 files, every SHA-256 matching, budget
document included). **Both backups are same-device protection against accidental deletion only,
not an off-device or device-loss backup; a separate owner-controlled off-device backup remains an
owner matter.** The proposed completed Gate F checklist was prepared with every supported
non-owner field populated and returned for the owner's step-12 signature decision; **no owner
field was signed, the checklist was not written to the repository or the evidence root, the
readiness token was not emitted, and Gate F was not begun.** The one blocker that preparation
referred for owner adjudication — a machine-local absolute path in the committed §17 review
artifact's clone-provenance sentence — **is resolved by accepted Decision 030** (see the next
section): the redaction is proven non-substantive, the review verdict is unchanged, and
`make hygiene` now passes with zero findings.

`FIRST_DURABLE_M3_1_SECTION_17_REVIEW` is **discharged and historical.** The M3.1 implementation was
frozen at `970e050deb06910adcde8588101564beb7d19c74`; a session that wrote none of the M3.1 work
produced
[`Docs/m3/reviews/m3_1_section_17_review_970e050deb06910adcde8588101564beb7d19c74.md`](../Docs/m3/reviews/m3_1_section_17_review_970e050deb06910adcde8588101564beb7d19c74.md)
with the verdict **`M3_1_SECTION_17_REVIEW: PASS`**; that artifact was committed governance-only at
`66e4c5433a393815c74f9e3087300613a516e2fb`, with the implementation bytes unchanged across that
commit; and the project owner accepted the review and its artifact.

`INDEPENDENT_M3_1_CONTRACT_REVIEW` is likewise **discharged and historical**: `contracts/m3_1.md` was
reviewed, corrected, and accepted with `IMPLEMENTATION_AUTHORIZATION: YES`.

The
[Decision 029](../Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md)
§12 sequence is **complete — all seventeen steps discharged**. The M3.1A rehearsal token, the two
byte-identical zero-request plans, the passing canonical budget display, the owner-approved hard
request ceiling 801, the Decision 030 hygiene remediation and Gate F interpretation rulings, the
validated SEC contact identity (value never displayed), the operator acknowledgement, the
owner-signed Gate F checklist (result `PASS`, SHA-256 `34fc0567…`), the owner's evidence-index
attestation, the Gate F readiness-token record (SHA-256 `b06ae373…`, token emitted exactly once),
the passed independent step-14 acceptance review (verdict
`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`; artifact SHA-256 `caf9f26e…`; commit `24fba32…`),
the owner's M3.1 acceptance recorded by accepted Decision 031 (`M3_1_ACCEPTED_AND_COMPLETE`),
the verified annotated `m3.1-complete` checkpoint (step 16; tag object `638a02b7…`, peeled
`4cd2c72…`), and the step-17 closure recording and bounded M3.2 contract draft
([`contracts/m3_2.md`](contracts/m3_2.md)) all exist as durable evidence, with the evidence-root
states backed up same-device through the after-step-13-token snapshot and the public evidence
index carrying the non-sensitive references and the recorded owner attestation. **The readiness
token records readiness only: Gate F execution has not begun, and no live SEC access is
authorized.** M3.1 is **owner-accepted and checkpointed**; the M3.2 contract is **an unaccepted
draft**; M3.2 onward is **not authorized**.

Milestones 0, 1, and 2 are formally closed
([Decision 026](../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md),
`MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`), the closeout commit is pushed, and the three
annotated completion tags `m0-complete`, `m1-complete`, and `m2-complete` exist at it. **Milestone 3
master planning is complete at Decision 027 v0.2; accepted Decisions 028 and 029 are correction and
remediation records, not implementation contracts; and the separate M3.1 contract is accepted and
implementation-authorized, with its implementation present in the tree but not accepted.**

**The Decision 028 review chain produced the required pass.** The Decision 027 v0.1 review's eleven
corrections were recorded at v0.2. Later bounded documentation corrections were committed and pushed
at `c91af08`; they are not “uncommitted.” The subsequent focused architecture review and Sol
reconciliation found additional issues: M3-L12 is an inherited planner defect, A5 and A11 need
registered reasons, A1–A12 need corrected semantics, receipts must become v2 before the first
receipt exists, budget and ceiling language must be repaired, and M3-L11 needs three-layer
implementation protection. Accepted Decision 028 records those rulings, and its fresh rereview
returned `INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`.

**The focused rereview must verify** (Decision 027 §23):

- all Decision 024 obligations are represented **exactly once**;
- each M3 phase has complete inputs, outputs, permissions, stop conditions, validation, recovery,
  tokens, and checkpoint policy;
- **every corrected subdivision is internally consistent** — M3.1A rehearses only acquisition,
  M3.2's two windows each carry their own plan and approval, M3.3A precedes M3.3B, and M3.4 is never
  documentary;
- **no scenario is placed in a phase that lacks the production path it exercises**;
- the operator runbook is executable as documentation **without pretending planned commands already
  exist**;
- **no withdrawn count, plan hash, `A_max`, or contingency survives anywhere as an accepted value**;
- M3-L12 is correctly classified as an inherited implementation defect; Decision 013 is unchanged;
  the total order and `quarterly-index-instances/2.0` boundary are complete;
- request budgeting excludes cache hits before planning, never subtracts them twice, records maximum
  new raw objects correctly, and labels the rate-limiter expression only as a spacing floor;
- ceiling equality is `actual <= ceiling`, with a complete reconciled plan separately required;
- execution receipts use `m3-execution-receipt/2.0`, have feasible field timing, cannot contaminate
  accepted identities, and carry exactly one integrity identity;
- the corrected A1–A12 matrix, both new reason codes, and M3.1/M3.2 recovery ownership are internally
  executable and fail closed;
- M3-L11's ignore, hygiene, resolved-path, ancestor, and symlink protections are complete as future
  contract requirements;
- the two-layer evidence model is applied consistently across the master plan and every template;
- templates and limitations are complete;
- **no implementation authority was granted**;
- **no live access occurred.**

That sequence is complete through Decision 028 §14 step 4: Decision 028 passed review, was accepted,
validated, and checkpointed, and the bounded M3.1 contract has since been reviewed, corrected, and
**accepted** with `IMPLEMENTATION_AUTHORIZATION: YES` under all five Decision 024 §8 conditions.

**No Milestone 3 implementation authority exists beyond the bounded M3.1 grant.** Closure satisfied
only the precondition Decision 024 §8 imposed. All five Decision 024 §8 conditions are now satisfied
for M3.1 (a separate accepted governance record — Decision 028; a bounded implementation contract —
`contracts/m3_1.md`; explicit owner authorization under the 2026-08-01 delegation; exact path
authorization in §§6–7; and inherited prerequisite gates via Decision 026), so
`IMPLEMENTATION_AUTHORIZATION` reads `YES` for M3.1 and the M3.1 contract is **accepted**. The five
conditions remain unsatisfied for every later phase, whose authorization stays `NO`, and **no live
SEC access, real pilot execution, real snapshot, real manifest construction, root approval, or
publication is authorized.** **No Gate F has passed, the M3.3A execution rehearsal (E1–E8) has not
been run (the M3.1A acquisition rehearsal A1–A12 ran and passed on 2026-08-03), no live acquisition
occurred, and no Gate H has passed.**

**Two conditions remain owner-facing.** **D023-O1** is inherited and referred only if a real run
reaches it. **M3-L12**'s owner ruling is recorded (Decision 028 §4) and its planner-v2 correction
is implemented in the frozen reviewed tree — the accepted step-10 plan's required-quarter set
includes the **closed** 2026 Q2 exactly as Decision 013 §1 requires, under
`quarterly-index-instances/2.0` — while the register entry remains `ACTIVE` until independent
M3.1 acceptance and a committed checkpoint; Decision 013 remains byte-for-byte unchanged.

**Historical — the approval path that closed the first two gates.**
S6 governance is drafted and has been through **three** full review cycles: the v0.1 review returned
`REQUIRES_OWNER_CLARIFICATION` and produced six bounded corrections applied at v0.2; v0.3 widened the
structural-fingerprint tuple to five columns; the v0.3 review **also** returned
`REQUIRES_OWNER_CLARIFICATION`, producing the two corrections v0.4 applied; and the v0.4 review
returned it a **third** time, producing the v0.5 ruling that grows migration `0013` to eight
triggers. **v0.2 was never independently reviewed, and no completed review covers the eight-trigger
SQL or the §15.5 guarantee, so the review may not inherit an earlier recommendation.** Decision 021
v0.5 freezes the manifest, document, and terminal-result architecture, including the **exhaustive
81-item §10 crosswalk** (§13.2.1) and the complete **eight-block** migration-`0013` SQL (§15.1) with
its **nine** normative digests, byte and line counts, and concatenation rule (§15.3), and
`Milestones/contracts/m23_s6.md` was `BLOCKED_PENDING_DECISION_021` at the time and is now
`READY_FOR_IMPLEMENTATION`. The review covered that exact SQL and its digests, the **§15.5 append-once and identity guarantee** and its nine clauses, the
crosswalk and its frozen counts, every digest preimage in Decision 021 §§6–9 **including the
eleven-field §8.4 selector-policy layer and the §8.1 five-column fingerprint rule**, the §10
circularity exclusions and the §10.1 commitment closure, the §9.2 six-field identity-immutability
ruling, and the §13 document contract. After it, in order: owner approval of Decision 021 v0.5
recorded in the registry, then separately issued bounded S6 implementation prompts. **All three
gates closed**, the stage was implemented and independently accepted, and Decision 023 records the
result. The S6 handoff conditions in
[`Milestones/contracts/m23_s5_4.md`](contracts/m23_s5_4.md) record which prerequisites S5.4 already
satisfied; the fifth — `selection_result_sha256` — is now settled by Decision 021 §6, which populates
it at S6 under the existing `pilot-manifest/1.0` policy. No further S5.4 work is authorized without a
new explicit owner authorization.

## Deferred stages

- **S5.4 (reserves)** — no longer deferred and no longer current: **complete and owner-accepted
  2026-07-30**, checkpointed at `m2.3-s5.4-complete`. See "Completed stages" and "Current stage".
- **S6 (pilot manifest construction)** — no longer deferred and no longer current: **complete and
  owner-accepted 2026-07-31**, checkpointed at `m2.3-s6-complete`. See "Completed stages" and
  "Current stage". No manifest approval, publication, CLI, or release work is authorized (Decision
  018 §22, Decision 021 §§11.1, 16, 17; Decision 023 §9); see `Docs/architecture_map.md` §8.
- **The former Stages S7–S10** — **no longer Milestone 2 stages.** Decision 024 §5.1 transferred them
  **intact** into Milestone 3: Gate F live-metadata readiness → **M3.1**; controlled metadata-only SEC
  acquisition with Gate H → **M3.2**; the frozen real candidate snapshot, deterministic execution, the
  exact real-data manifest, and the CLI output deferred from S6 → **M3.3**; explicit owner approval of
  the exact root hash → **M3.4**. A new **M3.5** covers integrated real-pilot acceptance and Milestone
  3 closeout. **Every gate, prohibition, owner ruling, validation requirement, identity, methodology,
  and accepted limitation is preserved.** None has begun; none is authorized; none is reachable — no
  candidate-snapshot builder and no production catalog exists, and no S7 or Milestone 3 contract
  exists.
- **Milestone 2 / Milestone 3 boundary governance** — **complete.** Recorded in Decision 024,
  `ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED`. Governance
  only; it authorized no implementation and no tag.
- **Final independent integrated Milestones 1 and 2 audit** — **complete.** Read-only and
  adversarial; it returned `REQUIRES_BOUNDED_INTEGRATED_FIXES` with nine categories
  `INTEGRATED_ACCEPTANCE_CONFIRMED` and one bounded documentation finding, recorded in Decision 025.
  It recorded no closeout and authorized no implementation.
- **Bounded correction, independent verification, final bounded fix, and fresh rereview** —
  **complete.** The rereview returned
  `ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT` with no remaining
  closeout blocker, and explicitly completed the outstanding **Milestone 0** classification.
- **Formal Milestone 0, Milestone 1, and Milestone 2 closeout** — **complete.** Recorded in
  [Decision 026](../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md),
  `ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`.
  Governance only; it authorized one commit, one push, and the three annotated completion tags
  `m0-complete`, `m1-complete`, and `m2-complete`, and granted no implementation authority.
- **Milestone 3 master planning and governance** — **complete at v0.2.** Recorded in
  [Decision 027](../Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md),
  `ACCEPTED — OWNER APPROVED 2026-07-31`, outcome
  `M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`. Planning and documentation only; the
  v0.1 recording and the v0.2 correction each authorized one commit and one push, **no tag**, and
  granted no implementation authority. Neither implemented, contracted, enabled network access,
  acquired metadata, snapshotted, ran a pilot, built a manifest, approved a root, or published —
  Decision 026 §§19–20 observed in full.
- **Independent Milestone 3 master-plan review** — **complete for v0.1.** Its eleven corrections are
  applied and recorded in Decision 027 §0.
- **Independent Milestone 3 master-plan REREVIEW** — **complete; it passed**
  (`INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`, recorded by accepted Decision 028). Read-only and
  focused, by a session that authored neither v0.1 nor the v0.2 corrections; it recorded no
  acceptance of implementation and authorized none.
- **Milestone 3 implementation** — **the bounded M3.1 phase is complete and OWNER-ACCEPTED
  (accepted Decision 031, 2026-08-03, outcome `M3_1_ACCEPTED_AND_COMPLETE`); its implementation is
  frozen at `970e050deb06910adcde8588101564beb7d19c74`.**
  Decision 029 code remediation is complete, and the first durable §17 review passed
  (`M3_1_SECTION_17_REVIEW: PASS`, artifact committed at
  `66e4c5433a393815c74f9e3087300613a516e2fb`, owner-accepted). The Decision 029 §12 step 9
  operational rehearsal ran once on 2026-08-03 and passed, emitting the M3.1A token; steps 10 and
  11 completed on 2026-08-03 — two byte-identical zero-request plans (request-plan SHA-256
  `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`) and the owner-approved hard
  request ceiling 801; step 12 was signed and completed on 2026-08-03 — its sole hygiene blocker
  resolved by accepted Decision 030, the signing preflight satisfied, and the owner-signed Gate F
  checklist (result `PASS`, SHA-256 `34fc0567…`) durably recorded and publicly referenced in the
  evidence index; step 13 completed on 2026-08-03 under separate owner authorization — the Gate F
  readiness token recorded exactly once (record SHA-256 `b06ae373…`); step 14 (the independent
  acceptance review) completed and passed on 2026-08-03 (`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW:
  PASS`; artifact SHA-256 `caf9f26e…`; commit `24fba32…`); and the owner accepted M3.1 on
  2026-08-03, recorded at step 15 by accepted Decision 031. Step 16 created and pushed the
  annotated `m3.1-complete` checkpoint (2026-08-03; tag object `638a02b7…`, peeled `4cd2c72…`),
  and step 17 closed M3-L11 and M3-L12 and drafted the bounded M3.2 contract
  ([`contracts/m3_2.md`](contracts/m3_2.md), `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE`),
  completing the Decision 029 §12 sequence. Gate F execution has not begun. Every later
  Milestone 3 phase is **not
  started and not authorized**, requiring all five Decision 024 §8 entry conditions per phase.

## Nonblocking maintenance notes

- The pytest-performance maintenance phase (parallel/offline test execution optimization, commit
  `f490281`) is accepted and does not gate S5. It changed test execution mechanics only, not any
  frozen definition, decision, or migration.

## Accepted nonblocking notes carried forward from S5.3

None of these blocks the accepted checkpoint, and none is to be addressed by changing implementation
outside a future authorized stage.

- **S5.4 requires an explicit ruling or a public pure-output design for the quota-contribution
  membership** used by reserve/replacement signatures. This was an S5.4 input, not an S5.3 gap.
  **Resolved and closed** by Decision 020 §§5–6 and the accepted S5.4 implementation: membership is
  published from the accepted S5.1 witness derivation as one additive immutable output.
- **`selection_result_sha256` remained NULL at S5.3.** Accepted; populating it was not an S5.3
  obligation. **Owner ruling recorded 2026-07-29: it remained NULL through S5.4** (Decision 020 §9).
  The open S6 question (Decision 020 §14.4) was **settled by Decision 021 §6 and is now
  implemented and accepted**: Stage S6 seals it under the existing `pilot-manifest/1.0` policy at a
  frozen fourteen-field preimage, append-once on every direct SQLite write path (migration `0013`
  triggers 1 and 2, widened by triggers 6, 7, and 8 at v0.5), and Decision 021 §15.5's guarantee that
  it also **remains recomputable from its persisted preimage** was proven against the migration as
  written. It is `NULL` in any catalog no S6 seal has run against, and **no production catalog
  exists**. **Closed.**
- **Quota-contribution and quota-member rows remain intentionally absent at S5.2.** **Closed at
  S5.4**: all three membership families are now written inside the S5 run's single `running` window,
  in the same transaction as the selection, exactly as Decision 020 requires.
- **The node-budget count observation is nonblocking.**
- **The difficult-or-nonstandard-package quota remains an M2.5 verification obligation** (Decision
  018 §14) — excluded from hard feasibility, never proxied, never reported as satisfied.

## Machine-readable markers

The markers below are consumed by `scripts/context_snapshot.sh`. Keep each on its own line in the
`KEY: value` form; the script greps for the first match and does not parse Markdown structure.

`ACTIVE_STAGE_CONTRACT` is resolved by the script as a **file path**, whose own `STATUS:` marker is
then reported. It therefore always names a real contract file — it is not a place to record "none".
**Whether any implementation is authorized is carried by `IMPLEMENTATION_AUTHORIZATION` here and by
the named contract's own status**, which now read `NO` and `ACCEPTED_AND_COMPLETE` respectively:
`Milestones/contracts/m23_s6.md` is named because it is the most recent stage's contract and the
script needs a resolvable path, **not** because it authorizes anything. No stage contract currently
authorizes implementation.

The `MILESTONE_0_STATUS`, `MILESTONE_1_STATUS`, `MILESTONE_2_STATUS`, `MILESTONE_3_STATUS`,
`DECISION_026_STATUS`, `DECISION_027_STATUS`, and `DECISION_028_STATUS` markers use the same
single-line `KEY: value` form. The
snapshot script reads only `CURRENT_STAGE`, `ACTIVE_BLOCKER`, `ACTIVE_STAGE_CONTRACT`, and
`NEXT_AUTHORIZED_ACTION`; the rest are for a reader or a future tool, and adding one changes no
script behaviour.

```
MILESTONE_0_STATUS: FORMALLY_CLOSED — Decision 026 section 6; annotated tag m0-complete; frozen research definitions and standing limitations remain binding
MILESTONE_1_STATUS: FORMALLY_CLOSED — Decision 026 section 7; annotated tag m1-complete
MILESTONE_2_STATUS: FORMALLY_CLOSED — Decision 026 sections 8 to 10; accepted implementation ends at M2.3 Stage S6; annotated tag m2-complete; no live SEC pilot was executed
MILESTONE_3_STATUS: MASTER PLANNING COMPLETE; DECISIONS 028 THROUGH 031 ACCEPTED; M3.1 CONTRACT ACCEPTED AND IMPLEMENTATION-AUTHORIZED; M3.1 IMPLEMENTATION FROZEN AT 970e050deb06910adcde8588101564beb7d19c74 AND OWNER-ACCEPTED (DECISION 031, 2026-08-03, OUTCOME M3_1_ACCEPTED_AND_COMPLETE); DECISION 029 CODE REMEDIATION COMPLETE; FIRST DURABLE SECTION 17 REVIEW COMPLETE AND PASSED; DECISION 029 SECTION 12 STEPS 8 TO 11 COMPLETE; M3.1A TOKEN EMITTED AND DURABLY CAPTURED; TWO BYTE-IDENTICAL M3.2A PLANS WITH REQUEST-PLAN SHA-256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68; OWNER-APPROVED HARD REQUEST CEILING 801 ON 2026-08-03; DECISION 030 ACCEPTED 2026-08-03 AND THE SOLE STEP-12 HYGIENE BLOCKER RESOLVED BY A PROVEN NON-SUBSTANTIVE REDACTION (REVIEW VERDICT UNCHANGED; HYGIENE PASSES); STEP 12 SIGNED AND COMPLETE ON 2026-08-03 WITH CHECKLIST RESULT PASS AND THE SIGNED CHECKLIST DURABLY RECORDED; STEP 13 OWNER-AUTHORIZED AND COMPLETE ON 2026-08-03 WITH THE GATE F READINESS TOKEN EMITTED AND RECORDED EXACTLY ONCE; GATE F READINESS RECORDED; GATE F EXECUTION NOT BEGUN AND LIVE SEC ACCESS NOT AUTHORIZED; STEP 14 COMPLETE AND PASSED ON 2026-08-03 (M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS; ARTIFACT SHA-256 caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e; REVIEW COMMIT 24fba32413bb6c5dade60a64182e42510afe6f88); OWNER ACCEPTED M3.1 ON 2026-08-03 AND STEP 15 RECORDED THE ACCEPTANCE (DECISION 031); STEP 16 COMPLETE ON 2026-08-03 — ANNOTATED M3.1-COMPLETE TAG CREATED AND PUSHED (TAG OBJECT 638a02b780d912ff7b37a2f523277b9d451a015a; PEELED TARGET 4cd2c7299ae30ca499108bd7f0a17a0adaf215f4); STEP 17 COMPLETE ON 2026-08-03 — M3-L11 AND M3-L12 CLOSED ON THEIR COMPLETE CLOSURE-EVIDENCE LISTS AND THE BOUNDED M3.2 CONTRACT DRAFTED (Milestones/contracts/m3_2.md); THE DECISION 029 SECTION 12 SEQUENCE IS COMPLETE; INDEPENDENT M3.2 CONTRACT REVIEW COMPLETE 2026-08-04 (M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS; ARTIFACT SHA-256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57; REVIEW COMMIT 3fbaa12d671d0000f5b608bbf6fb271f78b4673f); DECISION 032 ACCEPTED 2026-08-04 AND THE BOUNDED CONTRACT CORRECTIONS APPLIED (M3.2 CONTRACT NOW DRAFT — CORRECTED (DECISION 032) — PENDING INDEPENDENT REREVIEW AND OWNER ACCEPTANCE); FRESH INDEPENDENT NO-SUBAGENT REREVIEW COMPLETE 2026-08-04 (M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS; ARTIFACT SHA-256 91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf; REREVIEW COMMIT 3069b03ede9d805e9d0196a3e4c45c8cc68f42b7; ZERO BLOCKER; ZERO MAJOR); M3.2 CONTRACT ACCEPTED UNCHANGED AT T1 (ACCEPTED DECISION 034, 2026-08-04, OUTCOME M3_2_CONTRACT_ACCEPTED_AT_T1); T2 IMPLEMENTATION AUTHORIZATION NOT GRANTED; M3.2 IMPLEMENTATION NOT AUTHORIZED AND NOT BEGUN; LIVE SEC ACCESS NOT AUTHORIZED; ACQUISITION NOT BEGUN; OPERATIONAL CATALOG ABSENT
M3_1_FROZEN_IMPLEMENTATION_SHA: 970e050deb06910adcde8588101564beb7d19c74 — the reviewed implementation tree; implementation bytes are unchanged at the governance commit that recorded the review
M3_1_SECTION_17_REVIEW_STATUS: COMPLETE — VERDICT M3_1_SECTION_17_REVIEW: PASS; artifact Docs/m3/reviews/m3_1_section_17_review_970e050deb06910adcde8588101564beb7d19c74.md; produced by a session that wrote none of the M3.1 work; committed governance-only at 66e4c5433a393815c74f9e3087300613a516e2fb; review and artifact accepted by the project owner; this marker is authoritative over any earlier wording elsewhere that predates the review
M3_1A_REHEARSAL_STATUS: COMPLETE AND PASSED — Decision 029 section 12 step 9 executed exactly once on 2026-08-03 at 12:35:01Z under explicit owner authorization, exit status 0; all twelve A1-A12 scenarios PASS; passed, complete, a_reachable_agrees, and a_reachable_fully_tested all true; derived and tested route-key sets equal across nine routes; unmeasured_routes empty; actual_logical_request_count 0 and actual_physical_attempt_count 0; no live SEC access; receipt completion_status complete with no reason_code; M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED emitted by the canonical command and durably captured; artifacts immutable under the external evidence root at runs/m3_1a_rehearsal_970e050deb06910adcde8588101564beb7d19c74/ with report sha256 6308576a0a7df33813239f753b31b86754f3908d63d73e6521682db06a59e1e0, receipt sha256 ea1f4be2c136827ac5d865eea0fabf73f0f716802e2ee8cd23aedf1965dbc81b, and stdout log sha256 4b42f95e4a00d5865eeb05ccc9f06fe08c51c68f07c56d5512d441c2ee7118ce; not rerunnable
M3_1A_EVIDENCE_BACKUP_STATUS: SAME-DEVICE SNAPSHOTS COMPLETE THROUGH STEP 13 — the external evidence root is snapshotted locally after step 9, after step 10, after step 11, after step-12 preparation, after the step-12 signature, and after the step-13 token recording; the after-step-11 snapshot (11 files), the after-step-12-prep snapshot (12 files, including the private request-budget document), the after-step-12-signed snapshot (13 files, including the owner-signed Gate F checklist), and the after-step-13-token snapshot (14 files, including the readiness-token record) each verified file-by-file by SHA-256 on 2026-08-03, include all step-9 artifacts, and exclude the ignored local configuration file; these snapshots are same-device protection against accidental deletion only, not an off-device or device-loss backup, and a separate owner-controlled off-device backup remains an owner matter; no absolute private path is recorded here
M3_1B_PLAN_STATUS: COMPLETE AND ACCEPTED — STEP_10_PASS_BYTE_IDENTICAL; m3 plan-requests ran exactly twice on 2026-08-03 to different immutable output names under owner-supplied explicit inputs (coverage 2009-01-01 to 2026-06-30, as-of 2026-06-30, calendar year 2026, explicitly empty operator calendar-evidence manifest, operational catalog nonexistent at planning); byte-identical plans with request_plan_sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68 under m3-request-plan/1.0 and quarterly-index-instances/2.0; q 70 (2009QTR1 to 2026QTR2 including closed 2026 Q2 per Decision 013 section 1); already-satisfied instances 0; planned unique logical requests 75; maximum physical attempts 801; maximum new raw objects 75; expected cache hits 0; rate-limiter spacing floor 200.0 seconds; both dry-run receipts validate with zero actual request counts; the runs are not rerunnable
M3_1B_CEILING_APPROVAL_STATUS: STEP 11 COMPLETE — STEP_11_BUDGET_DISPLAY_PASS; the canonical m3 show-budget stdout is durably captured with sha256 0e6722dcd960c54a49e4a1af44a5c15587d03109b262c7ee471a46b8071db508; OWNER_CEILING_APPROVAL APPROVED received 2026-08-03 for the exact plan-bound hard request ceiling 801 bound to request-plan sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68, with planned unique logical requests 75, maximum new raw objects 75, expected cache hits 0, and no contingency allowance; three response-outcome quantities remain deliberately unresolved as EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN (expected successful, expected not-modified, expected governed non-success) with no integer approved or invented; the approval does not complete or sign the Gate F checklist, does not emit the readiness token, and does not authorize live SEC access
M3_1B_BUDGET_DOCUMENT_STATUS: CREATED 2026-08-03 — the private M3.2A request-budget document was instantiated once, immutably, from Docs/m3/templates/request_budget.md into the external evidence root's M3.1B run directory (runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/request_budget.md); 21633 bytes, 307 lines, sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f; it records the plan-derived quantities, the per-route independently tested A_reachable witnesses, the verbatim owner ceiling approval of 2026-08-03, and the three deliberately unresolved response-outcome markers; the public evidence-index entry is deliberately deferred to the owner; the absolute private path is never recorded here
STEP_12_PREPARATION_STATUS: COMPLETE AND DISCHARGED — the proposed checklist was prepared with every supported non-owner field populated; the sole adjudicable finding was resolved by accepted Decision 030 (proven non-substantive one-path redaction; review verdict M3_1_SECTION_17_REVIEW: PASS unchanged; make hygiene passing); the owner-side signing-preflight acts were completed on 2026-08-03 (SEC identity validated at the boundary with the value never displayed; main synchronized by one ancestry-proven normal push; operator acknowledgement recorded) and the owner signed the checklist; see STEP_12_SIGNATURE_STATUS
STEP_12_SIGNATURE_STATUS: SIGNED AND COMPLETE 2026-08-03 — owner Joseph Nihill, project owner acting through the ChatGPT owner decision; Gate F checklist result PASS with every template field populated, every item PASS, and no unresolved blocker; recorded acceptance reference bound to repository baseline 55cf244a00428fbc8fa38d7b70af1bac8a7c45e9, request-plan sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68, request-budget sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f, and sanitized section 17 review sha256 9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3 (a transparent recorded owner acceptance reference, not a handwritten, cryptographic, or third-party digital signature); the signed checklist is immutable private evidence in the M3.1B run directory of the external evidence root, 23463 bytes, 284 lines, sha256 34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc, containing the operator acknowledgement, the Decision 030 dispositions, and the two explicit step-13 boundary lines; the readiness-token literal occurs nowhere in it, which was correct at signing time; step 13 was subsequently owner-authorized and completed on 2026-08-03 (see M3_1_GATE_F_READINESS_TOKEN_STATUS); Gate F execution is not begun and not authorized
M3_1_GATE_F_READINESS_TOKEN_STATUS: EMITTED AND RECORDED EXACTLY ONCE ON 2026-08-03 UNDER EXPLICIT OWNER STEP-13 AUTHORIZATION — no canonical command exists for this token (the literal appears nowhere in the implementation), so the recording is the repository's established governance-evidence mechanism: a create-once immutable private record in the evidence root's M3.1B run directory (3982 bytes, 62 lines, sha256 b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e) carrying the token literal exactly once in its emitted-token field, bound to the signed checklist sha256 34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc, request-plan sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68, request-budget sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f, hard request ceiling 801, checklist baseline 55cf244a00428fbc8fa38d7b70af1bac8a7c45e9, and public step-12 recording commit 0334294bd420a829033094080a13e4df900da078, plus this public ledger marker; the token records readiness only and authorizes no live SEC access, no Gate F execution, no M3.1 final acceptance, and no M3.2; every step-13 precondition was independently reverified read-only immediately before recording; not re-emittable
M3_1_INDEPENDENT_ACCEPTANCE_REVIEW_STATUS: COMPLETE AND PASSED — Decision 029 section 12 step 14 executed 2026-08-03 under explicit owner authorization by a fresh non-author session; verdict M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS; artifact Docs/m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md with sha256 caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e, committed governance-only at 24fba32413bb6c5dade60a64182e42510afe6f88; all validation gates green in a fresh external independent clone (2739 passed, 1 pre-existing skip; transport test ran; secrets and hygiene clean); every accepted private-evidence SHA-256 recomputed and matched; zero BLOCKER, zero MAJOR, three MINOR findings accepted by the owner as nonblocking (Decision 031), zero OPTIMIZATION; the review recorded a verdict only and did not itself accept M3.1
M3_1_ACCEPTANCE_STATUS: OWNER-ACCEPTED 2026-08-03 — recorded by accepted Decision 031 (outcome M3_1_ACCEPTED_AND_COMPLETE) at Decision 029 section 12 step 15; verbatim owner instrument OWNER_M3_1_ACCEPTANCE_DECISION: APPROVED bound to review commit 24fba32413bb6c5dade60a64182e42510afe6f88 and review-artifact sha256 caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e; accepts the frozen implementation 970e050deb06910adcde8588101564beb7d19c74 (tree d0c3c94cbf9128eaf0fdb1ef58179d9977d718d3), the signed Gate F checklist sha256 34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc, the readiness-token record sha256 b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e, the request plans sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68, the request budget sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f, and the exact hard request ceiling 801; the annotated m3.1-complete checkpoint was subsequently created and pushed at the acceptance commit under the owner's step-16 authorization (2026-08-03; tag object 638a02b780d912ff7b37a2f523277b9d451a015a); Gate F execution not begun; live SEC access not authorized; M3.2 not authorized and not begun
DECISION_031_STATUS: ACCEPTED — OWNER APPROVED 2026-08-03; outcome M3_1_ACCEPTED_AND_COMPLETE; records the owner's final M3.1 acceptance and its evidence bindings; accepts the step-14 review's three MINOR findings as nonblocking; sets M3-L11 and M3-L12 to CLOSURE-READY PENDING STEP 16 without closing either; creates no tag and grants no network, Gate F-execution, acquisition, or M3.2 authority
M3_2_CONTRACT_REVIEW_STATUS: COMPLETE 2026-08-04 — independent, adversarial review of the initial M3.2 contract draft at 536856325f6a655416d48276c5b93848cab388e8 by a fresh non-author session under the owner's 2026-08-03 authorization; verdict M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS; zero BLOCKER, two MAJOR (F1 completion semantics; F2 boundary exactness including the unnamed command-scoped network-enable change), four MINOR (F3 crash-segment accounting; F4 evidence-index vocabulary; F5 stale navigation prose; F6 sentinel naming), one OPTIMIZATION (F7 positive controls); all sixty-five adversarial questions answered and the four owner concerns determined (completion concern confirmed as F1; migration/catalog concern passed with no new migration needed; network-enable concern confirmed as part of F2; the unresolved-count sentinel correct as used); durable artifact Docs/m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md, sha256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57, committed governance-only at 3fbaa12d671d0000f5b608bbf6fb271f78b4673f; the artifact is preserved unchanged as a truthful correction review, and per the owner's Decision 032 procedural ruling it does not satisfy the acceptance-prerequisite review because its session used two read-only fact-gathering subagents; zero live SEC access; the review accepted nothing and authorized nothing
M3_2_T2_PACKET_STATUS: PROPOSED — PENDING CHATGPT OWNER T2 DECISION — Docs/m3/m3_2_t2_implementation_authorization_packet.md prepared 2026-08-04 under OWNER_M3_2_T2_PACKET_PREPARATION_AUTHORIZATION: APPROVED (preparation only; approval of the packet expressly withheld); formal state M3_2_T2_PACKET_PREPARED_PENDING_OWNER_DECISION; IMPLEMENTATION_AUTHORIZATION NO; NETWORK_AUTHORIZATION NONE; audits the five Decision 024 section 8 entry conditions and proposes exactly fifteen authorized paths — production configs/project.yaml (one key network.m3_acquire_enabled, default false, never committed true), src/disclosure_drift/config.py (one NetworkSection field), src/disclosure_drift/m3/acquisition.py (new driver), src/disclosure_drift/cli.py, src/disclosure_drift/m3/request_plan.py, src/disclosure_drift/m3/recovery.py, src/disclosure_drift/reasons.py (reserved, only if a genuinely unregistered condition appears, else a stop condition), src/disclosure_drift/m3/__init__.py; tests tests/unit/test_m3_acquisition.py, tests/unit/test_m3_dependent_plan.py, tests/unit/test_m3_recover.py (all new) plus bounded edits to tests/integration/test_m3_cli.py, tests/unit/test_m3_request_plan.py, tests/unit/test_m3_recovery.py, tests/unit/test_config.py; both conditional surfaces sec/census_orchestrator.py and sec/index_retrieval.py are DECLINED and remain prohibited (retrieve_instance already accepts an injected SecClient carrying the ceiling and an on_state persistence hook; CensusOrchestrator is the M2.2 surface and builds its own transport); discharges the Decision 034 section 6 R1 four-part requirement; fixes six bounded stages (boundary, driver, reconciliation, recovery, dependent plan, validation) inside the contract section 22 single-commit boundary with per-stage exit gates; names seven stop-and-return conditions; fixes the exact nonchange proof against baseline 3db7487e467eec3a19ee9115b9a48a4a7853b164; and reproduces the proposed T2 owner instrument unissued; the packet grants no T2, changes no executable byte, enables no network or CompanyFacts, authorizes no SEC contact, acquisition, operational catalog, ceiling-801 use, M3.2B work, Gate H, or tag
M3_2_CONTRACT_REREVIEW_STATUS: COMPLETE 2026-08-04 — fresh independent rereview of the corrected M3.2 contract by one non-author session using no subagents (Decision 032 section 6; Decision 033 section 10); verdict M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS; zero BLOCKER, zero MAJOR, one MINOR (R1 — the receipt-enumeration surface, carried forward as mandatory T2-packet content by Decision 034 section 6), one OPTIMIZATION (R2 — nonblocking); artifact Docs/m3/reviews/m3_2_corrected_contract_independent_rereview_3bf9987dd72e1531da2f678fbbef735f37aefcf4.md, sha256 91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf, committed governance-only at 3069b03ede9d805e9d0196a3e4c45c8cc68f42b7; independence, no-subagent execution, and the container-continuity disclosure attested in the artifact section 1; zero live SEC access; the rereview accepted nothing and authorized nothing
DECISION_034_STATUS: ACCEPTED — OWNER APPROVED 2026-08-04; outcome M3_2_CONTRACT_ACCEPTED_AT_T1; records the owner's verbatim T1 acceptance instrument ACCEPT_M3_2_CORRECTED_CONTRACT_AT_T1 bound to the PASS rereview (artifact sha256 91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf; rereview commit 3069b03ede9d805e9d0196a3e4c45c8cc68f42b7); accepts the corrected contract unchanged at T1 (accepted-text sha256 75e7e5a11f6e02933c878894091b4a38cef609a1568a6095b0dbb2841e23d8d3; post-acceptance file sha256 a5ac0e8d042d90a7cff43a476258523ab71977b4b3d50ffe6777424720ae4ab2, status/authority metadata only); accepts R1 as nonblocking and mandates the four-part T2-packet content; accepts R2 as nonblocking with no contract edit; preserves every residual limitation open; grants no T2/T3/T4/T5 authority, no network or CompanyFacts enablement, no live SEC access, no connectivity testing, no acquisition, no operational catalog, no ceiling-801 use, no tag, and no push
DECISION_033_STATUS: ACCEPTED — OWNER APPROVED 2026-08-04; outcome M3_2_CORRECTION_PASS_ADJUDICATED_AND_CLEANED_UP; records the owner's verbatim 2026-08-04 adjudication of the Decision 032 correction pass published at 96dea2b50b7e87243aad29032946ef8447033eb9: findings F1 through F7 accepted as substantively addressed; the prior review artifact preserved and expressly not the final independent acceptance review; a fresh non-author no-subagent rereview still mandatory; Docs/decision_index.md restored to its exact bytes at parent commit 3fbaa12d671d0000f5b608bbf6fb271f78b4673f because that path was outside the final authorized-path list (so Decision 032 sections 5.5 and 7 name an F5 correction target that now carries no correction, recorded in Decision 033 section 5 rather than by editing the accepted record, and the stale Decision-029 next-action sentence in the index remains an open nonblocking navigation-staleness item needing its own path authorization); the exact next-action marker corrected; the nonconforming published commit subject accepted as a non-substantive procedural deviation; no history rewrite authorized and none performed; accepted Decision 032 not edited; the corrected M3.2 contract remains unaccepted and byte-unchanged; implementation, network and CompanyFacts enablement, live SEC access, acquisition, operational-catalog creation, and ceiling use all remain unauthorized; creates no tag
DECISION_032_STATUS: ACCEPTED — OWNER APPROVED 2026-08-04; outcome M3_2_CONTRACT_CORRECTIONS_RECORDED; records the owner's verbatim 2026-08-04 correction instrument bound to review commit 3fbaa12d671d0000f5b608bbf6fb271f78b4673f and review-artifact sha256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57; adopts findings F1 through F7 and authorizes the bounded correction of the M3.2 contract draft, this durable recording, the related registry, status, and navigation updates, and one normal fast-forward push; requires a fresh independent rereview of the corrected contract by one non-author session using no subagents before owner acceptance; accepts no contract, authorizes no implementation, changes no executable byte, enables no network or CompanyFacts, authorizes no live SEC access, no acquisition, no operational catalog, and no use of the M3.2A ceiling; creates no tag
M3_1_CHECKPOINT_STATUS: COMPLETE — Decision 029 section 12 step 16 executed 2026-08-03 under explicit owner authorization; annotated tag m3.1-complete created exactly once at the acceptance commit 4cd2c7299ae30ca499108bd7f0a17a0adaf215f4 with annotation "Complete M3.1 acceptance checkpoint" (tag object 638a02b780d912ff7b37a2f523277b9d451a015a); pushed as the single ref refs/tags/m3.1-complete and verified locally and remotely (matching tag objects and peeled targets; HEAD == origin/main; every prior tag unchanged; no tracked file changed; no commit created); Decision 029 section 12 steps 1 through 16 discharged
M3_L11_M3_L12_STATUS: CLOSED 2026-08-03 — both entries closed under the owner's explicit Decision 029 section 12 step-17 closure authorization, each on its complete closure-evidence list (bounded implementation and tests in the frozen accepted tree 970e050deb06910adcde8588101564beb7d19c74; full validation; independent M3.1 acceptance M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS; owner acceptance recorded by accepted Decision 031; and the verified m3.1-complete checkpoint, tag object 638a02b780d912ff7b37a2f523277b9d451a015a, peeled 4cd2c7299ae30ca499108bd7f0a17a0adaf215f4); the Decision 030 Ruling D sequencing distinction is preserved (Gate-F-facing requirement satisfied before signing; administrative closure at the completed acceptance-and-checkpoint sequence); Decision 013 byte-for-byte unchanged; register totals 35 open, 3 closed; D023-O1 unchanged — LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED
M3_2_CONTRACT_STATUS: ACCEPTED (T1) — DECISION 034 (2026-08-04) — IMPLEMENTATION NOT AUTHORIZED — Milestones/contracts/m3_2.md drafted 2026-08-03 at Decision 029 section 12 step 17 under the owner's explicit step-17 authorization and corrected once on 2026-08-04 under accepted Decision 032 (independent contract review verdict M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS; review artifact sha256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57; review commit 3fbaa12d671d0000f5b608bbf6fb271f78b4673f; corrected sections 1, 2, 4, 5, 12, 14, 15, 16, 18, 19, 20, and 25); rereviewed fresh with no subagents on 2026-08-04 (M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS; artifact sha256 91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf; rereview commit 3069b03ede9d805e9d0196a3e4c45c8cc68f42b7; zero BLOCKER; zero MAJOR; R1 MINOR carried as mandatory T2-packet content by Decision 034 section 6; R2 OPTIMIZATION nonblocking); accepted unchanged at T1 by accepted Decision 034 (2026-08-04; accepted-text sha256 75e7e5a11f6e02933c878894091b4a38cef609a1568a6095b0dbb2841e23d8d3; post-acceptance file sha256 a5ac0e8d042d90a7cff43a476258523ab71977b4b3d50ffe6777424720ae4ab2 reflecting the Decision-034-authorized status/authority-metadata update only); bounded to master plan M3.2 sections 1-36 and global section 16; carries the frozen M3.2A inputs (request-plan sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68; request-budget sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f; owner-approved hard request ceiling 801; 75 planned unique logical requests; 70 required quarterly-index instances; 75 maximum new raw objects; 0 expected cache hits; no contingency; 200.0-second spacing floor), strict stop-before-overflow, the accepted route allowlist and denylist, boundary-only SEC-identity handling, immutable raw-object and receipt requirements, interruption and recovery behaviour, zero filing-body/CompanyFacts/Frames/outcome access, the six-transition owner gate ladder (T1 contract acceptance, T2 implementation authorization, T3 implementation acceptance, T4 live-operation preflight, T5 separate per-window owner live-operation authorization, T6 controlled execution, then canonical Gate H), and the M3.2B dependency boundary (separately derived plan, budget, and owner ceiling approval after the M3.2A freeze; no inheritance of the M3.2A ceiling); IMPLEMENTATION_AUTHORIZATION NO; NETWORK_AUTHORIZATION NONE; T1 acceptance grants no T2/T3/T4/T5 authority — the contract implements nothing, enables nothing, and contacts no SEC host until each later section-8 transition is separately granted
M3_EVIDENCE_INDEX_STATUS: LIVE — Docs/m3/templates/evidence_index.md is the completed public evidence index (the recording destination named by contract m3_1.md section 6, master plan sections 12.1/12.3 and M3.1 section 30, and the operator runbook); rows EV-M31A-001 through EV-M31B-006 recorded 2026-08-03 covering the rehearsal report and receipt, both request plans, both planning receipts, the owner-signed request budget, and the owner-signed Gate F checklist; digests, types, phases, statuses, dates, and non-sensitive notes only; no private path, identity, or receipt content; the section 8 owner attestation is recorded verbatim (owner Joseph Nihill, 2026-08-03, bound to commit 0334294bd420a829033094080a13e4df900da078 and checklist sha256 34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc); the index vocabulary defines no readiness-token artifact type, so the token is recorded in this ledger and as private evidence only
DECISION_030_STATUS: ACCEPTED — OWNER APPROVED 2026-08-03; outcome GATE_F_STEP_12_OWNER_RULINGS_AND_HYGIENE_REMEDIATION_ACCEPTED; authorizes exactly one proven non-substantive redaction of the section 17 review artifact's clone-provenance path material (pre-redaction sha256 73cb1eacf0fb5e29a8a1c2ea871692068caf3ebdc48cae161d6aef677ba8f3a3 remains the historical identity; sanitized sha256 9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3 is the current tracked identity; verdict unchanged; history not rewritten; scanner not weakened; no allowlist); rules the three request-budget response-outcome markers permitted and nonblocking with no integer guessed; records M3-L12 GATE-F-FACING REQUIREMENT: SATISFIED with administrative closure deferred to the later M3.1 acceptance and checkpoint sequence; records D023-O1: LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED; signs no checklist, emits no token, and grants no network, Gate F, or M3.2 authority
DECISION_026_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; outcome MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED; controls formal closeout and completion tags; grants no Milestone 3 authority
DECISION_027_STATUS: v0.2; ACCEPTED — OWNER APPROVED 2026-07-31; outcome M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED; controls the accepted Milestone 3 master plan as narrowly corrected by accepted Decision 028; grants no implementation authority
DECISION_029_STATUS: ACCEPTED — OWNER APPROVED 2026-08-02; outcome M3_1_REHEARSAL_COMPLETENESS_AND_REASON_SEMANTICS_ACCEPTED; narrowly supersedes two Decision 028 clauses only; controls the per-route full-path A_reachable witness (a zero U never waives it), the rehearsal-only manifest-resolution fixture, the single code OFFLINE_REHEARSAL_SCENARIO_MISMATCH (integrity, blocks_release true, requires_manual_review false by owner ruling), the four-predicate M3.1A token gate, and the first durable section 17 review artifact; changes no receipt schema field or digest preimage; creates no migration; grants no network authority and no tag
DECISION_028_STATUS: ACCEPTED — OWNER APPROVED 2026-08-01; outcome M3_1_READINESS_CORRECTIONS_ACCEPTED; independent rereview PASS; records planner-v2, corrected A1-A12, two future reason codes, receipt-v2, budget, ceiling, recovery-ownership, and M3-L11 rulings; grants no implementation or network authority
CURRENT_STAGE: MILESTONES 0, 1, AND 2 FORMALLY CLOSED; DECISIONS 028 THROUGH 031 ACCEPTED; M3.1 CONTRACT INDEPENDENTLY REVIEWED, CORRECTED, AND ACCEPTED; M3.1 IMPLEMENTATION FROZEN AT 970e050deb06910adcde8588101564beb7d19c74 AND OWNER-ACCEPTED (DECISION 031, 2026-08-03). THE FIRST DURABLE SECTION 17 REVIEW EXISTS, COVERS THAT FROZEN TREE, PASSED, AND IS OWNER-ACCEPTED. DECISION 029 SECTION 12 STEPS 8 TO 11 ARE COMPLETE; THE STEP 9 OPERATIONAL REHEARSAL RAN ONCE ON 2026-08-03 AND PASSED WITH THE M3.1A COMPLETION TOKEN EMITTED BY THE CANONICAL COMMAND AND DURABLY CAPTURED; STEP 10 PRODUCED TWO BYTE-IDENTICAL ZERO-REQUEST M3.2A PLANS ON 2026-08-03; STEP 11 PASSED THE CANONICAL BUDGET DISPLAY AND THE OWNER APPROVED THE EXACT HARD REQUEST CEILING 801 ON 2026-08-03; DECISION 030 IS ACCEPTED AND THE SOLE STEP-12 HYGIENE BLOCKER IS RESOLVED; STEP 12 IS SIGNED AND COMPLETE (2026-08-03) WITH CHECKLIST RESULT PASS AND THE SIGNED CHECKLIST DURABLY RECORDED AS PRIVATE EVIDENCE WITH ITS DIGEST IN THE PUBLIC EVIDENCE INDEX; STEP 13 WAS OWNER-AUTHORIZED AND COMPLETED ON 2026-08-03 — THE GATE F READINESS TOKEN IS EMITTED AND DURABLY RECORDED EXACTLY ONCE AS IMMUTABLE PRIVATE EVIDENCE AND IN THIS LEDGER; THE TOKEN RECORDS READINESS ONLY; STEP 14 COMPLETED AND PASSED ON 2026-08-03 (M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS; ARTIFACT SHA-256 caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e; COMMIT 24fba32413bb6c5dade60a64182e42510afe6f88); THE OWNER ACCEPTED M3.1 ON 2026-08-03 AND STEP 15 RECORDED THE ACCEPTANCE (DECISION 031; M3_1_ACCEPTED_AND_COMPLETE); GATE F EXECUTION HAS NOT BEGUN; STEP 16 COMPLETE — THE ANNOTATED M3.1-COMPLETE CHECKPOINT WAS CREATED AND PUSHED AT THE ACCEPTANCE COMMIT AND VERIFIED REMOTELY; STEP 17 COMPLETE — M3-L11 AND M3-L12 CLOSED AND THE BOUNDED M3.2 CONTRACT DRAFTED; THE DECISION 029 SECTION 12 SEQUENCE IS COMPLETE; THE INDEPENDENT M3.2 CONTRACT REVIEW COMPLETED 2026-08-04 (M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS; ARTIFACT SHA-256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57; REVIEW COMMIT 3fbaa12d671d0000f5b608bbf6fb271f78b4673f); ACCEPTED DECISION 032 (2026-08-04) ADOPTED THE FINDINGS AND THE BOUNDED CONTRACT CORRECTIONS WERE APPLIED; THE FRESH INDEPENDENT NO-SUBAGENT REREVIEW COMPLETED 2026-08-04 (M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS; ARTIFACT SHA-256 91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf; REREVIEW COMMIT 3069b03ede9d805e9d0196a3e4c45c8cc68f42b7; ZERO BLOCKER; ZERO MAJOR); THE OWNER ACCEPTED THE CORRECTED CONTRACT UNCHANGED AT T1 (ACCEPTED DECISION 034, 2026-08-04, OUTCOME M3_2_CONTRACT_ACCEPTED_AT_T1) AND THE REREVIEW AND ACCEPTANCE COMMITS ARE PUBLISHED; T1 GRANTS NO LATER GATE; THE BOUNDED T2 IMPLEMENTATION-AUTHORIZATION PACKET IS PREPARED (Docs/m3/m3_2_t2_implementation_authorization_packet.md; PROPOSED — PENDING CHATGPT OWNER T2 DECISION) AND APPROVES NOTHING; M3.2 IMPLEMENTATION NOT AUTHORIZED (T2 PENDING UNDER ALL FIVE DECISION 024 SECTION 8 CONDITIONS) AND NOT BEGUN; NO LIVE ACQUISITION OCCURRED; NO GATE H HAS PASSED; NEXT: THE OWNER'S SEPARATE T2 DECISION ON THE PREPARED PACKET
ACTIVE_BLOCKER: M3.2 IMPLEMENTATION BLOCKS ON T2 — THE M3.2 CONTRACT (Milestones/contracts/m3_2.md) IS ACCEPTED UNCHANGED AT T1 (ACCEPTED DECISION 034, 2026-08-04) AFTER ITS FRESH INDEPENDENT NO-SUBAGENT REREVIEW (M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS), AND THE BOUNDED T2 IMPLEMENTATION-AUTHORIZATION PACKET IS PREPARED (Docs/m3/m3_2_t2_implementation_authorization_packet.md; PROPOSED — PENDING CHATGPT OWNER T2 DECISION), BUT THE SEPARATE DECISION 024 SECTION 8 IMPLEMENTATION AUTHORIZATION (T2) HAS NOT BEEN GRANTED — PREPARING THE PACKET APPROVED NOTHING, AND THE NEXT STEP IS THE OWNER'S SEPARATE EXPLICIT T2 DECISION ON IT; T3, T4, AND EACH PER-WINDOW T5 REMAIN SEPARATE LATER OWNER ACTS; DECISION 029 SECTION 12 STEPS 1 THROUGH 17 ARE DISCHARGED AND NO LONGER BLOCK — M3.1 IS OWNER-ACCEPTED (DECISION 031) AND CHECKPOINTED AT THE VERIFIED m3.1-complete TAG; THE READINESS TOKEN RECORDS READINESS ONLY AND AUTHORIZES NO LIVE SEC ACCESS; M3-L11 AND M3-L12 ARE CLOSED; D023-O1 IS A LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED
DECISION_022_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; controls crosswalk item 46 reserve-rank applicability only
DECISION_023_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; outcome M23_STAGE_S6_ACCEPTED_AND_COMPLETE; controls S6 acceptance, delivered-path ratification, limitations O1-O4, and checkpoint authorization
DECISION_024_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; outcome M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED; controls the M2 to M3 phase boundary and five entry conditions; grants no implementation authority
DECISION_025_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; outcome INTEGRATED_AUDIT_DOCUMENTATION_CORRECTIONS_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION: NO — M3.1 is complete, owner-accepted (Decision 031), and checkpointed at m3.1-complete; the M3.1 contract's historical grant is exhausted and authorizes nothing further. The M3.2 contract is ACCEPTED unchanged at T1 (accepted Decision 034, 2026-08-04) and carries IMPLEMENTATION_AUTHORIZATION: NO — contract acceptance is not implementation authorization; T2 requires its own explicit owner authorization under all five Decision 024 section 8 conditions and has not been granted. No implementation, network enablement, live acquisition, real snapshot, real manifest, root approval, publication, or tag work is authorized
ACTIVE_STAGE_CONTRACT: Milestones/contracts/m3_2.md
NEXT_AUTHORIZED_ACTION: OWNER_M3_2_T2_IMPLEMENTATION_AUTHORIZATION_DECISION — the ChatGPT owner's separate decision on the prepared bounded T2 implementation-authorization packet at Docs/m3/m3_2_t2_implementation_authorization_packet.md (STATUS: PROPOSED — PENDING CHATGPT OWNER T2 DECISION; prepared 2026-08-04 under OWNER_M3_2_T2_PACKET_PREPARATION_AUTHORIZATION: APPROVED, which permitted preparation only). The packet audits all five Decision 024 section 8 entry conditions (conditions 1, 2, and 5 satisfied; condition 3 is the authorization it requests; condition 4 is the enumeration it proposes), enumerates the exact fifteen authorized paths (eight production, seven test), declines both conditional surfaces sec/census_orchestrator.py and sec/index_retrieval.py so they remain prohibited, discharges the accepted Decision 034 section 6 R1 four-part requirement (item-level absent-object identities persist in the operational catalog and a private absence-enumeration artifact, never in the frozen receipt; completed_with_absences is a window governance classification recorded in the Gate H checklist, the owner adjudication record, and this ledger, never a receipt completion_status value; the plan hash is the deterministic join key across receipt, catalog, m3 reconcile-requests, and Gate H; and six named non-vacuous tests prove m3-execution-receipt/2.0 stays frozen, including a positive control refusing completed_with_absences as a completion_status), fixes six bounded stages inside the contract section 22 single-commit boundary with per-stage exit gates, names seven stop-and-return conditions, fixes the exact nonchange proof against baseline 3db7487e467eec3a19ee9115b9a48a4a7853b164, and reproduces the proposed T2 instrument for the owner to issue, amend, or refuse. Preparing the packet authorized nothing and approved nothing: T2 remains ungranted until the owner issues that instrument, and no executable byte may change before then; implementation acceptance (T3), live-operation preflight (T4), and each per-window live-operation authorization (T5) remain separate later owner acts. This entry authorizes no session to begin M3.2 implementation, enable SEC network access or CompanyFacts, contact the SEC, begin acquisition, create or populate an operational catalog, use the M3.2A ceiling 801, or create any tag; network permission NONE; no tag
```
