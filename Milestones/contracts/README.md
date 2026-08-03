# Milestones/contracts/ — purpose and structure

A **stage contract** is a short, per-stage scope document. It tells an engineering session what one
stage of implementation work is authorized to touch, which authorities govern it, which tests are the
minimum credible validation set, and where the commit boundary sits. It exists so that "what is this
stage allowed to do" has one short answer instead of requiring a fresh read of the full milestone
plan and every referenced decision every session.

## What a contract cannot do

- **A contract cannot override a decision record or a migration.** If a contract and
  `Docs/Decisions/` (or the schema a migration actually created) disagree, the decision record and
  the migration control. Fix the contract; do not treat the contract as authoritative over either.
- **A blocked contract is not authorization to implement.** A blocked status (for example the
  now-cleared `STATUS: BLOCKED_PENDING_DECISION_019` on the S5.2 contract) means exactly what it
  says: no implementation, no schema change, no new test asserting production behavior for that
  stage, until the named blocker clears. **A blocker clears only when the named decision is approved
  in `Docs/Decisions/decision_registry.md`** — a record still marked `PROPOSED — PENDING OWNER
  APPROVAL` leaves the contract blocked. Preparatory read-only work (further preflight, drafting the
  blocking decision itself) is not "implementation" and is not authorized by the contract either — it
  is authorized the same way any other work is, by the active milestone specification or an explicit
  instruction.
- **A cleared blocker is not authorization to implement either.** `STATUS:
  READY_FOR_IMPLEMENTATION` with `IMPLEMENTATION_AUTHORIZATION: YES` records that nothing external
  blocks the stage — it does not start the work. Where a contract says so (S5.2 did), a separately
  issued bounded implementation prompt is still required, and it may not widen the contract's
  authorized paths. Approving the decision that unblocked a stage never implements that stage.
- **A completed contract authorizes nothing further.** `STATUS: ACCEPTED_AND_COMPLETE` with
  `IMPLEMENTATION_AUTHORIZATION: NO` (the current state of both the S5.2 and the S5.4 contracts) means
  the stage shipped and was accepted; the contract stays on record as that stage's scope statement and
  never authorizes new work, the same way a superseded contract does. Reopening a completed stage
  requires a **new explicit owner authorization**, not a reading of the closed contract. The next stage
  needs its own contract.
- **A contract should link rather than duplicate decision text.** If a governing decision changes,
  every contract that copied its text instead of linking to it goes stale silently. Cite the decision
  ID and section; do not restate its content as contract prose.

## Required sections

Every contract in this directory contains:

1. **Status** — one line, machine-readable at the top: accepted / blocked (with the specific
   blocker) / superseded.
2. **Baseline prerequisites** — the accepted commit, checkpoint tag, and migration state the stage
   assumes. A session must reverify these live (`scripts/context_snapshot.sh`) before trusting them.
3. **Objective** — what the stage produces, in one or two sentences, citing the decision that defines
   it.
4. **Governing authorities** — the decision records, migrations, and policy modules that control this
   stage's behavior.
5. **In scope** — what this stage does.
6. **Deferred** — what this stage explicitly does not do, and which later stage owns it.
7. **Authorized paths** — files/directories this stage may create or modify.
8. **Prohibited paths** — files/directories this stage must not touch, stated explicitly rather than
   left to inference.
9. **Required APIs** — the public functions/classes the stage is expected to expose, where already
   proposed by an accepted preflight or decision. Anything not yet frozen by a decision is marked
   provisional.
10. **Required tests** — the minimum test categories the stage must ship with.
11. **Validation gates** — which `make` targets / scripts must pass before the stage is considered
    done.
12. **Commit boundary** — the point past which no further work under this contract is authorized
    without a new contract or explicit instruction.
13. **Stop conditions** — concrete situations in which a session must stop and report rather than
    proceed.

## Session discipline

**Each implementation session must verify the live baseline before relying on any contract.**
Commit hashes, tags, and migration counts recorded in a contract or in `Milestones/STATUS.md` are
point-in-time references, not live state. Run `scripts/context_snapshot.sh` (or `make context`) at
the start of a session and compare its output against what the contract assumes; stop and report a
mismatch rather than proceeding on a stale assumption.

## Index

`ACTIVE_STAGE_CONTRACT` in [`../STATUS.md`](../STATUS.md) names a contract file so that
`scripts/context_snapshot.sh` can resolve it and report its status; **whether any implementation is
authorized is carried by that contract's own status and by `IMPLEMENTATION_AUTHORIZATION` in
`STATUS.md`, not by the fact that the marker names a path.** A completed or superseded contract stays
on record as its stage's scope statement and never authorizes new work.

**The legacy S5 and S6 contracts in this directory are accepted and closed** — all three S5 contracts
and the S6 contract are `ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO`, and a
completed contract authorizes nothing further (see the rule above). **The M3.1 contract
[`m3_1.md`](m3_1.md) is the exception: it is accepted and carries bounded implementation
authorization** — `IMPLEMENTATION_AUTHORIZATION: YES`, `NETWORK_AUTHORIZATION_M3_1A: NONE`,
`NETWORK_AUTHORIZATION_M3_1B: ZERO LIVE REQUESTS` — over exactly its §§6–7 paths.

**Nothing in this directory authorizes live SEC work, real pilot execution, publication, or manifest
approval, and no contract for M3.2 or any later Milestone 3 phase exists.**

**The Milestone 2 / Milestone 3 boundary is recorded**, in
[Decision 024](../../Docs/Decisions/decision_024_m2_m3_boundary_governance.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED`). It fixes
accepted M2.3 S6 as the final implementation stage of Milestone 2 and transfers the obligations
formerly called S7–S10 **intact** into Milestone 3 as **M3.1–M3.4**, adding **M3.5** for integrated
real-pilot acceptance and Milestone 3 closeout.

**Decision 024 is governance only — it is a decision record, not a contract, and it appears nowhere
in this index as one.** It grants no implementation authority, and **assignment of an obligation to
Milestone 3 is not authorization to begin Milestone 3.** Each Milestone 3 phase will require its own
bounded implementation contract in this directory, a separate accepted governance record where
applicable, explicit owner authorization, exact path authorization, and satisfaction of its inherited
prerequisite gates — and none may begin before Milestone 1 and Milestone 2 closeout is complete.

**That audit has run.** It returned `REQUIRES_BOUNDED_INTEGRATED_FIXES`, confirming
`INTEGRATED_ACCEPTANCE_CONFIRMED` in nine categories with **no implementation, methodology,
migration, hashing, selection, manifest, leakage, security, or test defect**, and raising one bounded
documentation finding. That correction is complete and recorded in
[Decision 025](../../Docs/Decisions/decision_025_integrated_audit_documentation_corrections.md)
(`INTEGRATED_AUDIT_DOCUMENTATION_CORRECTIONS_AUTHORIZED`), which is a decision record, **not a
contract**, and grants no implementation authority.

**That verification has run.** It confirmed **Decisions 023, 024, and 025 independently** — each
`INDEPENDENT_ACCEPTANCE_CONFIRMED`, with **no methodological, implementation, test, or governance
defect** — and returned `REQUIRES_BOUNDED_VERIFICATION_FIXES` on two documentation items: one
closeout blocker (`Docs/sec_data_dictionary.md` gave 21 of 22 `pilot_*` tables the complete
Decision 025 §6.1 schedule; `pilot_projection_recovery_events` was incomplete) and one cosmetic
registry-rendering issue. **Both are corrected**, with three non-material precision notes, in a
documentation-only pass under the authority Decision 025 §6.1 already granted. **No new decision
record was required and none was created**, and **no contract in this directory changed.**

**That rereview has run and passed.** `FRESH_INDEPENDENT_BOUNDED_DOCUMENTATION_REREVIEW` returned
**`ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT`**, confirming
`INTEGRATED_ACCEPTANCE_CONFIRMED` for Milestone 0, Milestone 1, M2.1, M2.2, M2.3, and Milestone 2
integrated, and `VERIFIED_COMPLETE` across the data dictionary, deviation register, governance,
reproducibility, security and leakage, test adequacy, and documentation — with **no remaining
closeout blocker**. It also explicitly completed the outstanding **Milestone 0** closeout
classification.

**Milestones 0, 1, and 2 are therefore formally closed**, under
[Decision 026](../../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome
`MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`), with the annotated completion tags `m0-complete`,
`m1-complete`, and `m2-complete` at the closeout commit.

**Decision 026 is a decision record, not a contract, and it appears nowhere in this index as one.**
Like Decisions 024 and 025 before it, it authorizes no implementation and creates no contract.
**The legacy S5 and S6 contracts in this directory remain closed** — all three S5 contracts and the
S6 contract are `ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO`, unchanged by
closeout. **No Milestone 3 implementation contract was created at closeout** — closure satisfied only
the precondition Decision 024 §8 imposed. The bounded M3.1 contract [`m3_1.md`](m3_1.md) was drafted,
reviewed, and **accepted afterwards**, and now carries `IMPLEMENTATION_AUTHORIZATION: YES` over its
§§6–7 paths with zero live requests; **no contract for M3.2 or any later phase exists or is
authorized**, and all five Decision 024 §8 entry conditions still apply to every later phase.

**That master planning has run, and has since been corrected to v0.2.** It is recorded in
[Decision 027](../../Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
(**v0.2**, `ACCEPTED — OWNER APPROVED 2026-07-31`, outcome
`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`), with the roadmap in
[`../milestone_03_master_plan.md`](../milestone_03_master_plan.md) and the operational pack in
[`Docs/m3/`](../../Docs/m3/operator_runbook.md) — the operator runbook, the two offline rehearsal
specifications (**A1–A12** acquisition at M3.1A, **E1–E8** execution at M3.3A), the execution-receipt
specification, the limitations register, and the eight frozen templates.

**v0.2 applied eleven bounded owner corrections after the required independent review of v0.1**, all
recorded in Decision 027 §0. The four that bear on a future contract's shape: **M3.1 rehearses
acquisition only** — no scenario may be placed in a phase that lacks the production path it
exercises; **M3.2 runs in two sequential windows**, each with its own plan, budget, ceiling, and owner
approval, with the dependent counts **derived** from the frozen first-window objects rather than
estimated; **M3.3A** builds and rehearses the candidate-snapshot builder before **M3.3B** freezes
anything real; and **M3.4 always requires a contract and is never documentary**, with manual SQL
against the real catalog prohibited.

**Decision 027 is a decision record, not a contract, and it appears nowhere in this index as one.**
Like Decisions 024, 025, and 026 before it, it authorizes no implementation and **creates no
contract**. **Planning created no contract and left every then-existing contract closed**; the M3.1
contract was drafted and accepted afterwards.

The independent Decision 027 v0.2 rereview did not pass. Accepted
[Decision 028](../../Docs/Decisions/decision_028_m3_1_readiness_corrections.md) records the bounded
planner-v2, corrected A1–A12, reason-code, receipt-v2, budget, ceiling, recovery, and M3-L11 rulings
needed to correct the package. Its fresh independent rereview returned
`INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`, and the owner accepted it on 2026-08-01. **Decision 028
is also a decision record, not a contract. It authorizes no implementation.**

**The master plan is a plan, not an authorization.** It fixes, for each of M3.1–M3.5, the objective,
scope, non-scope, controlling decisions, required owner decisions, prerequisites, inputs, outputs,
authorized and prohibited path *categories*, network permission, permitted and prohibited SEC route
classes, request volume and its formula, hard ceiling, stop conditions, retry and drift boundaries,
leakage controls, provenance and receipt requirements, validation, rollback, recovery, replay
expectations, evidence packet, completion token, commit and tag policy, next action, and the
conditions preventing progression. **Its §16 additionally fixes the twenty mandatory contents of every
future Milestone 3 phase contract** — exact baseline, governing decisions, exact authorized and
prohibited paths, implementation authorization, network authorization, request ceiling, CLI interface,
storage/migration/identity effects, test requirements, targeted and phase-end validation, nonchange
proof, failure and rollback behaviour, commit and tag policy, completion report format, and the exact
completion token.

**The independent review and owner acceptance of [`m3_1.md`](m3_1.md) is discharged.** The contract
is `ACCEPTED_READY_FOR_IMPLEMENTATION` with `IMPLEMENTATION_AUTHORIZATION: YES`. **The
[Decision 029](../../Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md)
§11 code remediation is implemented and the disposable-clone validation run on the corrected working
tree is complete; a frozen commit and the first durable §17 review by a non-author session remain
outstanding.** A contract is only one
of Decision 024 §8's five entry conditions and never grants implementation authority on its own.
Every Milestone 3 phase gets its own contract in this directory, written to the required-sections
shape above and to the master plan's §16 additions.

**No Gate F has passed, neither offline rehearsal has been run to a passing token, no live
acquisition occurred, no Gate H has passed, and no real snapshot, selection, manifest, or approval
exists. The M3.1 implementation exists in the tree and is NOT accepted: Decision 029 code remediation
is implemented and the disposable-clone validation run on the corrected working tree is complete; a
frozen commit and the first durable §17 review remain outstanding, no durable §17 review artifact
exists and none covers the current tree, the M3.2A budget and ceiling are unapproved, and neither
completion token has been emitted.**

**Two active corrections block Gate F.** M3-L12 is an inherited exact-quarter-end planner defect:
the future contract must implement `quarterly-index-instances/2.0` while leaving Decision 013
byte-unchanged. M3-L11 requires the reserved-path ignore, hygiene refusal, and resolved-path CLI
protections. Their owner rulings are recorded by accepted Decision 028, but neither closes until
implementation, tests, independent acceptance, and a committed checkpoint exist. **A third correction
now joins them:** accepted [Decision 029](../../Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md)
requires an independently tested per-route `A_reachable` witness for **every** route — including one
planning zero requests — plus the single reason code `OFFLINE_REHEARSAL_SCENARIO_MISMATCH` and the
four-predicate M3.1A token gate.

- [`m3_1.md`](m3_1.md) — Milestone 3.1 acquisition-path rehearsal and Gate F.
  **Accepted; implementation exists and is not accepted.** `STATUS: ACCEPTED_READY_FOR_IMPLEMENTATION`,
  `IMPLEMENTATION_AUTHORIZATION: YES`, `NETWORK_AUTHORIZATION_M3_1A: NONE`,
  `NETWORK_AUTHORIZATION_M3_1B: ZERO LIVE REQUESTS`. Active blocker: **a frozen commit** and the
  **first durable §17 review** (the **Decision 029** code remediation is implemented and the
  disposable-clone validation run on the unfrozen tree is complete). No network access is authorized.

- [`m23_s6.md`](m23_s6.md) — Stage S6 (pilot manifest construction, terminal result identity, and the
  publication boundary). **Accepted and complete.** `STATUS: ACCEPTED_AND_COMPLETE`,
  `IMPLEMENTATION_AUTHORIZATION: NO`, active blocker **none**. Its controlling record,
  [Decision 021](../../Docs/Decisions/decision_021_m23_s6_manifest_construction.md), is at **v0.5**
  and **`ACCEPTED`** (owner approved 2026-07-30); item-46 applicability is controlled by
  [Decision 022](../../Docs/Decisions/decision_022_m23_s6_reserve_rank_applicability.md); and
  **owner acceptance of the stage is recorded in
  [Decision 023](../../Docs/Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md)**
  (`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `M23_STAGE_S6_ACCEPTED_AND_COMPLETE`). **All three
  gating conditions are satisfied**: the focused independent governance review of Decision 021 v0.5
  (complete 2026-07-30, `ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL`); owner acceptance of v0.5
  recorded in the registry; and the separately issued bounded implementation authorizations, which
  were issued and exercised. Implemented under those bounded prompts, corrected once under Decision
  022, rereviewed independently (`ACCEPT_M23_S6_IMPLEMENTATION_FOR_ACCEPTANCE_REVIEW`), and accepted
  on the final independent recommendation **`ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING`** with no
  blockers. Delivered the new `release/pilot_manifest.py` and `sec/pilot_manifest_store.py`, the
  DDL-only migration `0013_m23_manifest_lifecycle_guards.sql` — **eight triggers**, reproducing the
  Decision 021 §15.1 SQL byte-for-byte and its nine §15.3 digests — two new test modules, and bounded
  edits to `tests/unit/test_m23_pilot_schema.py` and `tests/unit/test_migration_provenance.py`.
  **The contract authorized seven paths; the delivered set is ten**, the extra three being
  `tests/unit/test_storage_catalog.py`, `tests/unit/test_m23_entity_selection_store.py`, and
  `tests/unit/test_m23_accession_selection_store.py` — forced consequences of migration `0013`,
  ratified retroactively by Decision 023 §4 and **not a general widening**. Checkpointed at
  `m2.3-s6-complete`, supplementing the immutable `m2.3-s5-complete` and `m2.3-s5.4-complete`. It
  authorized and still authorizes **no** manifest approval, publication, CLI surface, live metadata
  work, real candidate snapshot, or Stage S7–S10 activity — the obligations Decision 024 §5.1 renamed
  to **Milestone 3 phases M3.1–M3.4**, none of which is authorized or has begun. **It authorizes no
  new S6 implementation**;
  a future S6 change requires a new explicit owner authorization.

  **Contract revision without status change (2026-07-30).** This contract was revised in place when
  Decision 021 moved from v0.1 to v0.2, again to v0.3, to v0.4, and again to v0.5 — to carry in turn the
  four-trigger migration, the complete manifest document contract, the explicit residual schema
  exclusions, the six-field manifest-identity immutability ruling, the CLI and S7–S10 boundary, the
  five-column structural-fingerprint rule, the **exhaustive 81-item milestone-plan §10 crosswalk**,
  and finally the **eight-trigger** migration and its §15.5 append-once and identity guarantee. Its
  **seven authorized paths are unchanged across every one of those revisions**; its status and
  implementation authorization stayed unchanged through all of them and moved only on 2026-07-30,
  when the owner approved Decision 021 v0.5. This is the normal shape of a contract revision: a
  contract tracks its controlling record, and tracking it is never itself an authorization. **Three
  focused independent governance reviews ran against this stage before it was accepted — of
  Decision 021 v0.1, v0.3, and v0.4 — and all three returned `REQUIRES_OWNER_CLARIFICATION`. The
  fourth, of v0.5, returned `ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL` with no governance blockers,
  and the owner approved the record the same day.**

  **Second controlling record, added 2026-07-31 —
  [Decision 022](../../Docs/Decisions/decision_022_m23_s6_reserve_rank_applicability.md),
  `ACCEPTED — OWNER APPROVED 2026-07-31`.** A fresh independent S6 implementation audit found that a
  lawful, accepted, feasible, sealed S5 run with **zero compatible reserve packages** was refused at
  document verification, because crosswalk item 46's `reserves.packages[].reserve_rank` leaf cannot
  exist with zero packages — even though Decision 020 §7.1 and Decision 021 §11.2 both make that run
  manifest-eligible. The audit stopped under Decision 021 §§21 and 13.3 and returned
  `REQUIRES_OWNER_CLARIFICATION`. Decision 022 rules that reserve rank is applicable **once per
  persisted reserve package** and is **structurally not applicable** for a target carrying the
  `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition instead, that item 70 remains the total per-target
  coverage requirement, and that no synthetic package or invented rank may be created or serialized.
  **This contract's authorized paths are unchanged by it** — the correction lands inside
  `release/pilot_manifest.py`, `sec/pilot_manifest_store.py`, and the two S6 test modules, all
  already listed. Decision 021 is **not** amended: it remains `ACCEPTED`, and its crosswalk, counts,
  preimages, digests, and migration SQL are untouched. As always, a clarification is not an
  acceptance — a fresh independent S6 rereview and the separate final S6 acceptance review had both
  to pass before Stage S6 could be accepted, and neither could be run by a session that wrote the
  work it reviews. **Both ran and both passed**, which is what Decision 023 records.

  **Third controlling record, added 2026-07-31 —
  [Decision 023](../../Docs/Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md),
  `ACCEPTED — OWNER APPROVED 2026-07-31`.** It records formal owner acceptance of Stage S6
  (`M23_STAGE_S6_ACCEPTED_AND_COMPLETE`), ratifies the three forced-consequence test paths named
  above, records the four accepted nonblocking limitations O1–O4, and authorizes exactly one commit,
  one push, the annotated tag `m2.3-s6-complete`, and one tag push. It adds no architecture: Decision
  021 remains controlling for the S6 architecture and Decision 022 for item-46 applicability, and no
  hash preimage, digest, crosswalk row, classification total, migration byte, or S4/S5 behaviour
  changed at acceptance. **It grants no Stage-S7 and no Milestone 3 authority**, and defers the
  Milestone 2 / Milestone 3 boundary reorganization and the final integrated Milestone 2 audit to
  separate later sessions.
- [`m23_s5_4.md`](m23_s5_4.md) — Stage S5.4 (reserve packages, quota-contribution membership, and
  replacement signatures). **Accepted and complete.** `STATUS: ACCEPTED_AND_COMPLETE`,
  `IMPLEMENTATION_AUTHORIZATION: NO`, active blocker **none**. Implemented under a separately issued
  bounded S5.4 prompt confined to twelve authorized paths, reviewed independently, corrected under
  bounded fixes D1/T1/T2/T3, re-reviewed, and owner-accepted 2026-07-30 (final independent
  recommendation `ACCEPT_M23_S5_4_FOR_CHECKPOINT`; final accepted suite 1899 passed, 1 skipped).
  Delivered the additive S5.1 quota-contribution membership output, the new pure
  `sec/reserve_selector.py`, contribution/member/reserve/disposition persistence and reconstruction in
  `sec/accession_selection_store.py`, the one reason code `REVIEW_PILOT_NO_COMPATIBLE_RESERVE`, and
  DDL-only migration `0012_m23_selection_entity_reasons.sql` — **created and accepted**, reproducing
  the Decision 020 §8.2 SQL byte-for-byte and the only migration the stage authorized. Its controlling
  record, [Decision 020](../../Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md), is
  `APPROVED — OWNER APPROVED 2026-07-30`: the owner's nine rulings are in its §14, its migration ruling
  in §8.2, its test-scoping clarification in §8.3, and its **final acceptance and the five accepted
  methodological limitations in §19**. Committed and tagged `m2.3-s5.4-complete`, which **supplements**
  the immutable `m2.3-s5-complete`. **It authorizes no new S5.4 implementation**; a future S5.4 change
  requires a new explicit owner authorization.
- [`m23_s5_2.md`](m23_s5_2.md) — Stage S5.2 (frozen accession reader, run identity, and selection
  persistence). **Accepted and complete.** `STATUS: ACCEPTED_AND_COMPLETE`,
  `IMPLEMENTATION_AUTHORIZATION: NO`. Implemented under a separately issued bounded S5.2 prompt,
  reviewed independently under S5.3, and owner-accepted 2026-07-29 (final independent recommendation
  `ACCEPT_M23_S5_3_CHECKPOINT`; final accepted suite 1661 passed, 1 skipped). Delivered
  `sec/accession_selection_store.py` and its test module, additive migration `0011` (INSERT-only),
  `PILOT_JOINT_SELECTOR_POLICY_VERSION`, and the five Decision 018 §21 reason codes, under the
  storage-to-pure-input mappings frozen by
  [Decision 019](../../Docs/Decisions/decision_019_m23_s5_storage_to_pure_input_mapping.md).
  Committed at the combined S5.1–S5.3 checkpoint, tag `m2.3-s5-complete`. **It authorizes no new
  S5.2 implementation.**
- [`m23_s5_1.md`](m23_s5_1.md) — Stage S5.1 (accession candidate and joint-selection core).
  **Accepted; superseded as the active contract.** Its own header still reads
  `STATUS: READY_FOR_IMPLEMENTATION` (Decision 018's approval cleared the earlier
  `BLOCKED_PENDING_DECISION_018` state); the stage itself is accepted and closed. The stage's code —
  `sec/accession_selector.py` and `tests/unit/test_m23_accession_selector.py` — is accepted and was
  **committed at the combined S5.1–S5.3 checkpoint** (Decision 018 §22), tag `m2.3-s5-complete`. It
  remains the sole methodological selector.
