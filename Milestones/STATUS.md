# Milestones/STATUS.md — concrete-state ledger

**Purpose:** a short, current-state record of where Milestone 2.3 stands. This file records
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

## Accepted baseline

- Branch: `main`.
- Accepted methodological checkpoint tag: `m2.3-s5.4-complete` -> the commit created by the
  2026-07-30 checkpoint session ("Complete M2.3 S5.4 reserve architecture"). This file records no
  hash for it by design; resolve it live with `make context`.
- Immediately preceding checkpoint tag: `m2.3-s5-complete` -> the commit created by the 2026-07-29
  checkpoint session ("Complete M2.3 S5 joint selection checkpoint"). **It is immutable and was never
  moved, replaced, or re-pointed**; `m2.3-s5.4-complete` supplements rather than replaces it
  (Decision 020 §§14.9, 15).
- Earlier accepted commits: `921f57b` ("Approve Decision 018 accession selection policy"),
  `3b01c50` ("Add repository orientation and stage-contract workflow"),
  `f490281` ("Optimize offline test execution and parallel validation").
- Earlier checkpoint tags: `m2.3-s4-complete` -> `e7157aa` ("Complete M2.3 S4 deterministic entity
  selection and persistence"); `m2.3-s3.2-complete` -> `5fb8e27`.
- Migrations end at `0012_m23_selection_entity_reasons.sql`, created and accepted at Stage S5.4. See
  `src/disclosure_drift/storage/migrations/` for the authoritative list.

## Current phase

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

The next stage is **M2.3 S6 (final manifest construction) — planning and implementation. S6 has not
begun**, is separately gated, and needs its own contract and owner authorization. No manifest,
publication, or release work is authorized. **No S5 selection and no reserve is yet a manifest or
publication input.** The full Milestone 2 integrated review occurs **only after S6 acceptance**. See
"Current stage" below.

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

## Current stage

**M2.3 Stage S6 (final manifest construction) — planning. Not begun.** Stage S5 is finished end to
end: S5.1, S5.2, and the combined S5.1–S5.3 checkpoint were owner-accepted 2026-07-29, and **S5.4 was
owner-accepted 2026-07-30** and checkpointed at `m2.3-s5.4-complete`. **There is no active
implementation contract.** S6 is separately gated: it needs its own decision-level design where the
existing records do not already settle a point, its own stage contract, and an explicit owner
authorization. **No S6 code, test, migration, schema, policy constant, or reason code exists or is
authorized.**

**Active blocker: none.** No S5.4 blocker remains, and no S5 acceptance blocker remains.

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

**No stage contract currently authorizes implementation.** `Milestones/contracts/m23_s5_4.md`,
`m23_s5_2.md`, and `m23_s5_1.md` are all closed and authorize nothing; each remains on record as its
stage's scope statement. `ACTIVE_STAGE_CONTRACT` below names the S5.4 contract because
`scripts/context_snapshot.sh` resolves that marker as a file path and it is the most recent stage's
contract — **authorization is carried by that contract's own status and by
`IMPLEMENTATION_AUTHORIZATION` here, both of which now read closed and `NO`**, never by the fact that
the marker names a path.

**S6 has not begun.** No manifest, publication, or release work is authorized before S6 (Decision 018
§22); see `Docs/architecture_map.md` §8. **No S5 selection and no reserve is a manifest or publication
input.** The **full Milestone 2 integrated review occurs only after S6 acceptance**, not before.

**The S4 entity-only draft is unchanged.** It stays in `running` state, remains non-publishable, and
is excluded from S5 run identity and from every manifest input. It is never promoted, mutated,
deleted, or transformed into the S5 joint run (Decision 018 §§6, 27) — a permanently-`running` S4
draft is expected residue, not an abandoned run. S5.4 read it, wrote it, and changed it in no way.

## Next authorized action

**Design and authorize Stage S6 (final manifest construction).** S5 is complete: S5.4 is
owner-accepted (2026-07-30) on the final independent recommendation
`ACCEPT_M23_S5_4_FOR_CHECKPOINT`, checkpointed at `m2.3-s5.4-complete`, with no active blocker. The
next step is S6 governance — a decision-level design where the existing records do not already settle a
point (including whether `selection_result_sha256` stays `NULL` beyond S5.4, Decision 020 §14.4), then
an S6 stage contract, then a separately issued bounded S6 implementation prompt. **Until all three
exist, no S6 code, test, migration, schema, policy constant, or reason code may be written**, and no
manifest, publication, or release work is authorized. The S6 handoff conditions in
[`Milestones/contracts/m23_s5_4.md`](contracts/m23_s5_4.md) record which prerequisites S5.4 already
satisfied. No further S5.4 work is authorized without a new explicit owner authorization.

## Deferred stages

- **S5.4 (reserves)** — no longer deferred and no longer current: **complete and owner-accepted
  2026-07-30**, checkpointed at `m2.3-s5.4-complete`. See "Completed stages" and "Current stage".
- **S6 (final manifest construction)** — **not started**, and the next stage. No manifest,
  publication, or release work is authorized before S6 (Decision 018 §22); see
  `Docs/architecture_map.md` §8. It needs its own governance, its own stage contract, and an explicit
  owner authorization. **No S5 selection and no reserve is a manifest or publication input.**
- **Full Milestone 2 integrated review** — not started; it occurs **only after S6 acceptance**.

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
- **`selection_result_sha256` remains NULL at S5.3.** Accepted; populating it was not an S5.3
  obligation. **Owner ruling recorded 2026-07-29: it remains NULL through S5.4** (Decision 020 §9).
  **Still `NULL` after S5.4 acceptance**; whether it stays `NULL` beyond S5.4 is an open S6 question
  (Decision 020 §14.4).
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
`Milestones/contracts/m23_s5_4.md` is named because it is the most recent stage's contract and the
script needs a resolvable path, **not** because it authorizes anything. No stage contract currently
authorizes implementation.

```
CURRENT_STAGE: M2.3 Stage S6 (final manifest construction) — PLANNING, not begun; Stage S5.4 (reserves) is complete and owner-accepted 2026-07-30 on the final independent recommendation ACCEPT_M23_S5_4_FOR_CHECKPOINT with an accepted suite of 1899 passed and 1 skipped, contract ACCEPTED_AND_COMPLETE, migration chain ending at 0012_m23_selection_entity_reasons.sql, checkpointed at m2.3-s5.4-complete supplementing the immutable m2.3-s5-complete; Decision 020 remains APPROVED — OWNER APPROVED 2026-07-30; S5.1, S5.2, and the combined S5.1-S5.3 checkpoint remain owner-accepted at m2.3-s5-complete
ACTIVE_BLOCKER: none — S5.4 is accepted and checkpointed with no remaining acceptance or checkpoint blocker, and no S5 acceptance blocker remains; S6 is not blocked, it is simply not yet designed or authorized
IMPLEMENTATION_AUTHORIZATION: NO — no stage contract currently authorizes implementation; Milestones/contracts/m23_s5_4.md is ACCEPTED_AND_COMPLETE and authorizes no new S5.4 work, and any future S5.4 change requires a new explicit owner authorization; S6 requires its own governance, its own stage contract, and a separately issued bounded S6 implementation prompt before any S6 code, test, migration, schema, policy constant, or reason code may be written; no S5 selection or reserve is a manifest or publication input
ACTIVE_STAGE_CONTRACT: Milestones/contracts/m23_s5_4.md
NEXT_AUTHORIZED_ACTION: Design and authorize Stage S6 — S6 governance first (including whether selection_result_sha256 stays NULL beyond S5.4, Decision 020 section 14.4), then an S6 stage contract, then a separately issued bounded S6 implementation prompt; no S6 code/test/migration/schema/policy constant/reason code before all three; no further S5.4 work without a new explicit owner authorization; the full Milestone 2 integrated review occurs only after S6 acceptance
```
