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
- Accepted baseline commit: `3b01c50` ("Add repository orientation and stage-contract workflow").
- Previous accepted maintenance commit: `f490281` ("Optimize offline test execution and parallel
  validation").
- Accepted methodological checkpoint tag: `m2.3-s4-complete` -> `e7157aa` ("Complete M2.3 S4
  deterministic entity selection and persistence").
- Earlier checkpoint tag: `m2.3-s3.2-complete` -> `5fb8e27`.
- Migrations end at `0010_m23_quota_policy_reference.sql`. See
  `src/disclosure_drift/storage/migrations/` for the authoritative list.

## Current phase

M2.3 (deterministic pilot selection). Stage S4 (entity-only selection) is accepted. Decision 018
(Stage S5 accession selection policy) is **approved**, so Stage S5.1 is no longer blocked — but **no
S5 code, test, migration, reason code, or policy constant has been written**, and Decision 018
authorizes no implementation on its own. See "Current stage" below.

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

## Current stage

Stage S5.1 (accession candidate and joint-selection core) is **READY_FOR_IMPLEMENTATION** — see
`Milestones/contracts/m23_s5_1.md`. There is no active blocker.

"Ready" means the governing policy exists, not that work may begin: the stage contract's
**"Implementation authorization: NO"** stands until a separate implementation prompt is issued. No S5
code, test, migration, reason code, or policy constant exists yet.

## Next authorized action

Produce and route a bounded Stage S5.1 implementation plan/prompt for project-owner approval,
scoped by `Milestones/contracts/m23_s5_1.md` and governed by Decision 018. No S5 code, schema, test,
reason code, or policy constant may be written before that prompt is issued.

## Deferred stages

- **S5.2** — not started. Owns the frozen reader, canonical validation, deterministic run identity,
  transactionality, persistence, reconstruction, idempotence, **and** the two artifacts Decision 018
  §20 approved but did not create: the `PILOT_JOINT_SELECTOR_POLICY_VERSION` constant
  (`m23-joint-selector-policy-v1`) and additive, INSERT-only migration `0011`. **Migration `0011` is
  authorized but does not exist** — migrations still end at `0010`, and `0009`/`0010` are never
  edited.
- **S5.3** — not started. Independent adversarial review and the combined S5.1–S5.3 acceptance
  checkpoint (one commit boundary).
- **S5.4 (reserves)** — not started. Reserves belong to the Stage-S5 envelope but are explicitly a
  later S5.4 boundary within it, per Decision 013 §6, Decision 016 §7, and Decision 018 §22.
- **S6 (final manifest construction)** — not started. No manifest work is authorized before S6
  (Decision 018 §22); see `Docs/architecture_map.md` §8.

## Nonblocking maintenance notes

- The pytest-performance maintenance phase (parallel/offline test execution optimization, commit
  `f490281`) is accepted and does not gate S5. It changed test execution mechanics only, not any
  frozen definition, decision, or migration.

## Machine-readable markers

The markers below are consumed by `scripts/context_snapshot.sh`. Keep each on its own line in the
`KEY: value` form; the script greps for the first match and does not parse Markdown structure.

```
CURRENT_STAGE: M2.3 Stage S5.1 (accession candidate and joint-selection core) — READY_FOR_IMPLEMENTATION
ACTIVE_BLOCKER: none — Decision 018 approved 2026-07-28; implementation still requires a separate prompt (contract says "Implementation authorization: NO")
ACTIVE_STAGE_CONTRACT: Milestones/contracts/m23_s5_1.md
NEXT_AUTHORIZED_ACTION: Produce and route a bounded S5.1 implementation plan/prompt for owner approval; no S5 code/test/migration/reason code/policy constant until that prompt is issued
```
