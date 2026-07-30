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

**No contract in this directory currently authorizes implementation.** All three S5 contracts are
accepted and closed. The next stage, S6, has no contract yet and needs one, together with its own owner
authorization, before any S6 work begins.

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
