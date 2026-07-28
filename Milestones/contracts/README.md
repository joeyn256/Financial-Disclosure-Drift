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
- **A blocked contract is not authorization to implement.** `STATUS: BLOCKED_PENDING_DECISION_018`
  (or any other blocked status) means exactly what it says: no implementation, no schema change, no
  new test asserting production behavior for that stage, until the named blocker clears. Preparatory
  read-only work (further preflight, drafting the blocking decision itself) is not "implementation"
  and is not authorized by the contract either — it is authorized the same way any other work is,
  by the active milestone specification or an explicit instruction.
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

- [`m23_s5_1.md`](m23_s5_1.md) — Stage S5.1 (accession candidate and joint-selection core).
  `STATUS: BLOCKED_PENDING_DECISION_018`.
