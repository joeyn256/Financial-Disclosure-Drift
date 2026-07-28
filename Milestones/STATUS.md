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
- Accepted baseline commit: `f490281` ("Optimize offline test execution and parallel validation").
- Accepted methodological checkpoint tag: `m2.3-s4-complete` -> `e7157aa` ("Complete M2.3 S4
  deterministic entity selection and persistence").
- Earlier checkpoint tag: `m2.3-s3.2-complete` -> `5fb8e27`.
- Migrations end at `0010_m23_quota_policy_reference.sql`. See
  `src/disclosure_drift/storage/migrations/` for the authoritative list.

## Current phase

M2.3 (deterministic pilot selection). Stage S4 (entity-only selection) is accepted. Stage S5
(joint entity-accession selection) has not started implementation and is blocked — see below.

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
  proposed rules are **proposed**, not accepted policy — see
  `Milestones/contracts/m23_s5_1.md` for which items remain open.

## Active blocker

Decision 018 does not yet exist. Stage S5.1 (accession candidate and joint-selection core) is
**BLOCKED_PENDING_DECISION_018** — see `Milestones/contracts/m23_s5_1.md`. Decision 018 must resolve,
at minimum: the accession objective, the stress-accession definition, inaccessible cross-cutting
quotas, canonical accession hashing and ordering, and the per-entity base-accession floor. Until
Decision 018 is approved by the project owner, no S5 implementation is authorized.

## Next authorized action

Produce and route Decision 018 for project-owner review. No code, schema, or test change for S5 is
authorized before that decision is approved — see `Milestones/contracts/m23_s5_1.md` (status
`BLOCKED_PENDING_DECISION_018`, "Implementation authorization: NO").

## Deferred stages

- **S5.2 / S5.3** — not started. Depend on S5.1, which is blocked on Decision 018.
- **S5.4 (reserves)** — not started. Reserves belong to the Stage-S5 envelope but are explicitly a
  later S5.4 boundary within it, per Decision 013 §6 and Decision 016 §7.
- **S6 (final manifest construction)** — not started. Out of scope until S5 is complete; see
  `Docs/architecture_map.md` §8.

## Nonblocking maintenance notes

- The pytest-performance maintenance phase (parallel/offline test execution optimization, commit
  `f490281`) is accepted and does not gate S5. It changed test execution mechanics only, not any
  frozen definition, decision, or migration.

## Machine-readable markers

The markers below are consumed by `scripts/context_snapshot.sh`. Keep each on its own line in the
`KEY: value` form; the script greps for the first match and does not parse Markdown structure.

```
CURRENT_STAGE: M2.3 Stage S5.1 (accession candidate and joint-selection core) — BLOCKED_PENDING_DECISION_018
ACTIVE_BLOCKER: Decision 018 (accession-selection policy) does not yet exist
ACTIVE_STAGE_CONTRACT: Milestones/contracts/m23_s5_1.md
NEXT_AUTHORIZED_ACTION: Produce and route Decision 018 for project-owner review; no S5 code/schema/test change until it is approved
```
