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

**No contract in this directory currently authorizes implementation**, S6 included — but for a
different reason than before: **every contract here is now accepted and closed**, and a completed
contract authorizes nothing further (see the rule above). All three S5 contracts and the S6 contract
are `ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO`.

**Nothing in this directory authorizes Milestone 3, live SEC work, real pilot execution, publication,
or manifest approval.** No S7 contract exists and no Milestone 3 contract exists.

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

**The next authorized action is
`FRESH_INDEPENDENT_INTEGRATED_CORRECTION_AND_GOVERNANCE_VERIFICATION`** — a fresh independent
session, which must have authored none of Decisions 023, 024, or 025 nor the documentation
corrections. It is read-only, records no closeout, and authorizes no implementation. Formal
Milestone 1 and Milestone 2 closeout follows only if that verification passes, in its own
governance-only session which controls the closeout tags, and **Milestones 1 and 2 are not closed
until then**.

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
