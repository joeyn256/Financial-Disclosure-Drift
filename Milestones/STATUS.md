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
- Accepted methodological checkpoint tag: `m2.3-s5-complete` -> the commit created by the
  2026-07-29 checkpoint session ("Complete M2.3 S5 joint selection checkpoint"). This file records
  no hash for it by design; resolve it live with `make context`.
- Previous accepted baseline commit: `921f57b` ("Approve Decision 018 accession selection policy").
- Earlier accepted commits: `3b01c50` ("Add repository orientation and stage-contract workflow"),
  `f490281` ("Optimize offline test execution and parallel validation").
- Earlier checkpoint tags: `m2.3-s4-complete` -> `e7157aa` ("Complete M2.3 S4 deterministic entity
  selection and persistence"); `m2.3-s3.2-complete` -> `5fb8e27`.
- Migrations end at `0011_m23_joint_selector_policy_reference.sql`. See
  `src/disclosure_drift/storage/migrations/` for the authoritative list.

## Current phase

M2.3 (deterministic pilot selection). Stage S4 (entity-only selection) is accepted. Decision 018
(Stage S5 accession selection policy) and Decision 019 (Stage S5 frozen-storage-to-pure-input
mapping policy) are both **approved by the project owner 2026-07-28**.

**Stage S5.1 is accepted. Stage S5.2 is accepted. The combined S5.1–S5.3 checkpoint is
owner-accepted** (2026-07-29) and committed under the single commit boundary Decision 018 §22 fixes.
The final independent re-review's recommendation was **`ACCEPT_M23_S5_3_CHECKPOINT`**, on a final
accepted suite of **1661 passed, 1 skipped** (the one skip is pre-existing: the `[sec]` extra is not
installed). **No acceptance blocker remains.**

The next project stage is **S5.4 (reserve design and implementation planning)**. **S5.4
implementation authorization is NO** until a separate bounded S5.4 contract and implementation
prompt are approved. **S6 has not begun**, and no manifest or publication work is authorized. See
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

## Current stage

**S5.4 (reserve design and implementation planning).** Reserve packages, reserve accession rows, and
replacement/substitution signatures are the S5.4 boundary within the Stage-S5 envelope (Decision 013
§6, Decision 016 §7, Decision 018 §22).

**Active blocker: none.**

**S5.4 implementation authorization is NO.** No reserve code, test, migration, reason code, or policy
constant may be written until **both** a separate bounded S5.4 stage contract **and** a separately
issued S5.4 implementation prompt are approved. No decision record, and no existing contract,
authorizes S5.4 implementation on its own.

**There is no active implementation contract.** `Milestones/contracts/m23_s5_2.md` is
`ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO` — it remains on record as Stage
S5.2's scope statement and **authorizes no new S5.2 implementation**. `ACTIVE_STAGE_CONTRACT` below
still names it because it is the most recent governing contract and because
`scripts/context_snapshot.sh` resolves that marker as a file path; authorization is carried by the
contract's own status, not by the path. Stage S5.1's contract
(`Milestones/contracts/m23_s5_1.md`) likewise remains on record as its accepted stage's scope
statement and authorizes nothing.

**S6 has not begun.** No manifest, publication, or release work is authorized before S6 (Decision
018 §22); see `Docs/architecture_map.md` §8. **No current S5 selection is a manifest or publication
input.**

**The S4 entity-only draft is unchanged.** It stays in `running` state, remains non-publishable, and
is excluded from S5 run identity and from every manifest input. It is never promoted, mutated,
deleted, or transformed into the S5 joint run (Decision 018 §§6, 27) — a permanently-`running` S4
draft is expected residue, not an abandoned run.

## Next authorized action

**Design Stage S5.4 (reserves) and draft its bounded stage contract.** Planning and design are
authorized; implementation is not. Writing any S5.4 code, test, migration, reason code, or policy
constant requires the approved S5.4 contract plus a separately issued bounded implementation prompt.

## Deferred stages

- **S5.4 (reserves)** — not started; the next stage to be designed and contracted. Reserves belong to
  the Stage-S5 envelope but are explicitly a later S5.4 boundary within it, per Decision 013 §6,
  Decision 016 §7, and Decision 018 §22.
- **S6 (final manifest construction)** — not started. No manifest work is authorized before S6
  (Decision 018 §22); see `Docs/architecture_map.md` §8.

## Nonblocking maintenance notes

- The pytest-performance maintenance phase (parallel/offline test execution optimization, commit
  `f490281`) is accepted and does not gate S5. It changed test execution mechanics only, not any
  frozen definition, decision, or migration.

## Accepted nonblocking notes carried forward from S5.3

None of these blocks the accepted checkpoint, and none is to be addressed by changing implementation
outside a future authorized stage.

- **S5.4 requires an explicit ruling or a public pure-output design for the quota-contribution
  membership** used by reserve/replacement signatures. This is an S5.4 input, not an S5.3 gap.
- **`selection_result_sha256` remains NULL at S5.3.** Accepted; populating it is not an S5.3
  obligation.
- **Quota-contribution and quota-member rows remain intentionally absent at S5.2.** Accepted.
- **The node-budget count observation is nonblocking.**
- **The difficult-or-nonstandard-package quota remains an M2.5 verification obligation** (Decision
  018 §14) — excluded from hard feasibility, never proxied, never reported as satisfied.

## Machine-readable markers

The markers below are consumed by `scripts/context_snapshot.sh`. Keep each on its own line in the
`KEY: value` form; the script greps for the first match and does not parse Markdown structure.

`ACTIVE_STAGE_CONTRACT` is resolved by the script as a **file path**, whose own `STATUS:` marker is
then reported. It therefore always names a real contract file — it is not a place to record "none".
**Whether any implementation is authorized is carried by `IMPLEMENTATION_AUTHORIZATION` here and by
the named contract's own status**, which currently read `NO` and `ACCEPTED_AND_COMPLETE`
respectively: there is no active implementation contract.

```
CURRENT_STAGE: M2.3 Stage S5.4 (reserve design and implementation planning) — DESIGN_AND_PLANNING; S5.1, S5.2, and the combined S5.1-S5.3 checkpoint are owner-accepted and checkpointed at m2.3-s5-complete
ACTIVE_BLOCKER: none — S5.3 acceptance is recorded (final independent recommendation ACCEPT_M23_S5_3_CHECKPOINT; final accepted suite 1661 passed, 1 skipped); no acceptance blocker remains
IMPLEMENTATION_AUTHORIZATION: NO — S5.4 implementation requires both a separate bounded S5.4 stage contract and a separately issued S5.4 implementation prompt; there is no active implementation contract, and no S5.4 or S6 code is authorized
ACTIVE_STAGE_CONTRACT: Milestones/contracts/m23_s5_2.md
NEXT_AUTHORIZED_ACTION: Design Stage S5.4 (reserves) and draft its bounded stage contract; no S5.4 code/test/migration/reason code/policy constant before that contract and a separate implementation prompt are approved; S6, manifest, publication, and release work remain unauthorized
```
