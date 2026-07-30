# Decision 020 — M2.3 Stage S5.4 Reserve Architecture and Quota-Contribution Membership

**Date:** 2026-07-29 (owner rulings recorded 2026-07-29; approved 2026-07-30)
**Status:** APPROVED — OWNER APPROVED 2026-07-30
**Type:** Implementation and architecture decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged by this record. No hypothesis, cohort window, maturity gate,
outcome definition, threshold, or seed is altered.
**Supersedes:** nothing. **Interprets and extends** the Stage-S5 sub-stage boundary fixed by
[Decision 018](decision_018_m23_s5_accession_selection_policy.md) §§19, 22, and 29, and operationalizes
[Decision 013](decision_013_pilot_selection_mechanics.md) §6 and
[Decision 016](decision_016_m23_schema_and_artifact_architecture.md) §7 for Stage S5.4. It redesigns
no accepted selection policy, no objective, and no quota definition.
**Governs:** Milestone 2.3, Stage S5.4 onward.
**Related:** [Decision 013](decision_013_pilot_selection_mechanics.md) §§5–7,
[Decision 014](decision_014_pilot_evidence_and_classification_policy.md) §1,
[Decision 016](decision_016_m23_schema_and_artifact_architecture.md) §§1, 3, 5, 6, 7, 8,
[Decision 017](decision_017_s4_quota_policy_and_control_evidence.md),
[Decision 018](decision_018_m23_s5_accession_selection_policy.md),
[Decision 019](decision_019_m23_s5_storage_to_pure_input_mapping.md).

**Stage S5.4 is implemented, independently accepted, and checkpointed — see §19.** This record remains
approved and binding as the controlling architecture record for reserves at S5.4. The project owner's
rulings are recorded in §14 and bound the design. The architecture, methodology, identity boundary,
reason-code ruling, and the exact §8.2 SQL are unchanged by acceptance; §§16 and 18 carry only their
gate-status markers forward, and every other section below is preserved as written. The bounded S5.4
implementation prompt required by §16.3 was issued and executed, the implementation was reviewed
independently twice, and the project owner accepted it on 2026-07-30 on the final independent
recommendation `ACCEPT_M23_S5_4_FOR_CHECKPOINT`. **This record authorizes no further implementation:
any future S5.4 change requires a new explicit owner authorization.** Approval of a policy record is
never itself authorization to write code.

> **Owner clarification recorded 2026-07-29 — §8 is resolved.** The owner's no-compatible-reserve
> ruling requires a deterministic, durable, normalized record of a target-specific reserve absence,
> and migration `0009` has no lawful location for it. The owner has **authorized a future minimal
> additive migration `0012` in principle** (§8), and the durability requirement stands unchanged:
> dropping durable persistence, using an in-memory-only diagnostic, or repurposing an existing
> unrelated table is **rejected**. Its **complete DDL is frozen in §8.2** — the table and all four
> triggers — and **no migration other than `0012` is authorized.** No question in this record remains
> open. **Migration `0012` was subsequently created in the S5.4 implementation session, reproduces the
> §8.2 SQL byte-for-byte, and is accepted (§19); statements below that it "has not been created"
> describe the position at approval and are historical.**
>
> **Correction applied 2026-07-29 after independent governance review.** That review found one
> approval-blocking defect: specifying the lifecycle guards as "mirroring migration `0009`" inherited
> that migration's OLD-only UPDATE predicate, so a disposition row could be moved from a `running` run
> onto an already-`feasible` run and leave a sealed run holding both a reserve and a
> no-compatible-reserve row for the same target. §8.2 now freezes exact SQL for all four triggers: the
> UPDATE guard checks **both** the OLD and the NEW associated run, and `selection_run_id`,
> `snapshot_id`, and `cik_numeric` are **immutable**. All guards use an explicit `NOT EXISTS` predicate
> and therefore **fail closed when the associated run does not exist**. Migrations `0009`–`0011` are
> **not** modified.
>
> **Focused independent governance re-review completed 2026-07-30 — recommendation
> `ACCEPT_DECISION_020_FOR_OWNER_APPROVAL`.** The re-review covered the exact §8.2 DDL — the table and
> all four triggers — and established that the corrected lifecycle SQL is valid and load-bearing; that
> the original cross-run `UPDATE` bypass reproduces when the correction is absent and is blocked by the
> frozen corrected SQL; that the INSERT, UPDATE, and DELETE guards fail closed for a missing or
> non-`running` run; that `selection_run_id`, `snapshot_id`, and `cik_numeric` are immutable; that all
> feasible-transition regression cases pass and non-feasible cleanliness remains correct; that
> migration `0012` creates exactly one table and four new triggers; that migrations `0009`–`0011`
> remain unchanged; and that **no governance defect or approval blocker remains**. The 2026-07-29
> lifecycle defect is **closed**. See §18.

---

## 1. Why this record exists

Stage S5.4 (reserve packages, reserve accession rows, replacement/substitution signatures) was
deferred by Decision 018 §§22 and 31 and is assigned no ruling by §29. Two facts make it
unimplementable under the existing records without a new decision.

**Fact 1 — the schema requires member-level quota-contribution data that no accepted artifact
produces.** Migration `0009` enforces, on the `running -> feasible` transition, that each reserve
package's `pilot_reserve_quota_contributions` set equals the target entity's
`pilot_selected_entity_quota_contributions` set exactly. The accepted Stage S5.1 core publishes quota
state as **integers only**. Stage S5.2 consequently left the contribution and quota-member tables
empty, which S5.3 accepted as a recorded forward dependency.

**Fact 2 — an accepted `feasible` selection run is permanently sealed.** Every write guard on the
reserve, contribution, and quota-member tables requires `run_state = 'running'`, and
`pilot_selection_run_transition_guard` does not permit `feasible -> running`.

Fact 2 is decisive: **Stage S5.4 cannot be a persistence pass over an already accepted selection
run.** Reserves, contributions, and quota members must be written inside the same single `running`
window, and the same transaction, as the selection itself. §3 records the evidence.

## 2. Scope

**In scope:** the architecture by which quota-contribution membership becomes available; reserve
construction and signature rules; the identity and hashing boundary; the schema ruling; and the
bounded governance consequences for the accepted S5.1 and S5.2 artifacts.

**Out of scope:** Stage S6 manifest construction, publication, and root-manifest hashing; the M2.5
replacement *event*; manual recovery orchestration; and any change to the Decision 013 §5 objective,
the Decision 018 quota set, role assignment, caps, floors, amendment families, the evidence-penalty
rule, or the selection tie-break formula.

## 3. Evidence of record

Observed directly against migrated scratch catalogs built by the accepted migration chain and driven
by the accepted S5.2 entry point.

| Observation | Result |
|---|---|
| Accepted S5.2 run terminal state | `feasible`, with 24 selected entities, 38 selected accessions, 35 quota results, and **0** contribution, member, and reserve rows |
| `INSERT` into `pilot_selected_entity_quota_contributions` on that run | refused — requires a running selection run |
| `INSERT` into `pilot_quota_result_members` on that run | refused — requires a running selection run |
| `INSERT` into `pilot_reserves` on that run | refused — requires a running selection run |
| `UPDATE run_state` from `feasible` to `running` | refused — illegal pilot selection run state transition |
| `running -> feasible` with contributions and **no** reserve | accepted |
| `running -> feasible` with a reserve whose contribution set **exactly** matches its target | accepted |
| the same, with a strict **subset** / **superset** / **empty** set | each refused — reserve/target signature mismatch |

Two further facts bound the cost of every ruling below:

- **No production catalog database exists.** The pilot has never been executed against real data.
  Every consequence here is code-only: no data migration, no reprocessing.
- **No accepted S5 test pins a literal digest value.** The S5.1 and S5.2 suites assert determinism,
  sensitivity, permutation-invariance, and exclusion properties, never a specific hash constant.

## 4. Architecture alternatives considered

### Alternative A — extend the accepted pure S5.1 public output — **adopted for membership**

`_build_witnesses` already computes, for every cross-cutting quota, the contribution units and the
accession members whose joint selection achieves each unit, and the published `achieved_count` is
computed *from* those witnesses (`_count_units(strict[key], chosen_present)`). Exposing them is a
projection of a value the accepted core already derives, not a second derivation. Consistency with the
published integers therefore holds **by construction**. Selection results, objective behavior, and run
identity are unchanged: the change is a purely additive output. Historical reconstruction remains
valid — the additional deterministic output is re-derived identically and gains its own validation.

### Alternative B — a new pure S5.4 module — **adopted for reserve methodology only**

- **For contribution membership: rejected.** It would re-derive the witness rules, i.e. the "second
  methodological implementation" Decision 018 §19 prohibits. Importing the private helpers instead is
  Alternative A reached indirectly with worse encapsulation. The only available equality invariant
  (recompute counts from members, compare to the diagnostics) *detects* divergence in tested cases and
  cannot *prevent* it; Alternative A makes divergence unrepresentable.
- **For reserve ranking, package assembly, and signature computation: adopted.** Those are genuinely
  separate methodology (Decision 013 §6, Decision 016 §7), not selection. The module consumes public
  accepted helpers (`selection_rank`, `accession_selection_rank`, `assign_accession_role`,
  `accession_evidence_penalty`, `derive_amendment_families`) without reproducing any of them, and is
  therefore not a disguised second selector. **It may not reproduce any quota-contribution rule.**

### Alternative C — bounded S5.1/S5.2 amendment — **its persistence half is mandatory**

§3 shows contributions, members, and reserves can only be written while the run is `running`, so
`execute_and_persist_joint_selection` is the only place that can write them. Any design deferring
reserve persistence to a later pass over an existing feasible run is unimplementable. Migration `0009`
compatibility is complete for the reserve, contribution, and member families. Reconstruction gains
fail-closed validation in the accepted `_validate_persisted_*` style. Risk is bounded: S5.1 gains
exactly one additive output; S5.2 gains contribution, member, and reserve persistence plus validation.

### Alternative D — signatures from integer quota outcomes only — **rejected, and remains rejected**

- `pilot_selected_entity_quota_contributions` is keyed `(selection_run_id, snapshot_id, cik_numeric,
  quota_dimension, quota_key)`. An integer count carries no CIK and no key, so the table cannot be
  populated from counts at all.
- The feasible-transition trigger compares `(quota_dimension, quota_key)` **sets** bidirectionally;
  §3 shows subset, superset, and empty sets each abort. No arithmetic over counts satisfies a set
  comparison.
- Decision 013 §6 as amended requires the **complete** signature and names this exact failure: a
  reserve "that matches on size or industry but would silently drop or alter a cross-cutting
  contribution is not compatible."
- Leaving the contribution tables empty so the trigger's `EXISTS` clauses never fire would make every
  reserve vacuously valid. That is disabling the integrity check, not satisfying it.

## 5. Frozen ruling — recommended architecture

**Single-window reserve materialization with S5.1-sourced contribution membership.**

1. **Stage S5.1 gains one additive public output** carrying deterministic, immutable
   quota-contribution membership, sourced directly from the existing witness derivation. It is the
   **sole** source of membership for every consumer.
2. **Stage S5.2's single transaction is extended** to persist, inside the same `running` window, the
   contribution and quota-member rows of §6 and the reserve rows of §7. The transition to `feasible`
   remains the last statement in that transaction.
3. **A new pure S5.4 reserve module** ranks candidates, assembles packages, and computes signatures.
   It implements no selection policy and no quota-contribution rule of its own.
4. **Reconstruction re-derives and validates every emitted row**, failing closed on any difference.
5. **No reserve, contribution, or member row is ever added to an already-feasible run.**

## 6. Frozen ruling — quota-contribution membership and the three row families

**One S5.1 output supplies all three families.** The witness derivation already produces, per quota
unit, the unit identity and its accession members; the entity-level and accession-level projections
are transposes of that single artifact. **No S5.2 or reserve-module re-derivation occurs anywhere**:
S5.2 projects and writes rows, and the reserve module reads them; neither computes a contribution rule
(Decision 018 §19). **The public output is not widened beyond what these three families, the accepted
diagnostics, and deterministic reconstruction require.**

| Row family | Required by `0009` for reserve integrity? | Required to reconstruct the accepted diagnostics? | Provenance only? |
|---|---|---|---|
| `pilot_selected_entity_quota_contributions` | **Yes — load-bearing.** The feasible-transition trigger compares each reserve package's contribution set against *this table* for the target CIK. Without it every reserve is vacuously valid. | No — diagnostics are re-derived from the pure solve | No |
| `pilot_selected_accession_quota_contributions` | No — no trigger consults it for reserve integrity; it appears only in the "zero rows before a non-feasible terminal transition" check | No | **Yes** |
| `pilot_quota_result_members` | No — same as above | No | **Yes** — the normalized member-level evidence for each persisted `achieved_count` |

**All three are emitted and persisted.** The two provenance families are produced by the same single
output at no additional cost, and persisting only the trigger-required family would leave an
asymmetric record whose achieved counts have no durable member-level basis — contrary to the
normalized evidence design of Decision 016 §§3 and 4. Their emission adds nothing to the public
output that the entity family does not already require.

Further membership rules:

- **Derived, not stored-then-trusted.** Reconstruction re-derives membership from the frozen snapshot
  and validates every persisted row against the re-derivation, failing closed.
- **Deterministic and order-independent**: emitted in a fixed canonical order and compared as a set,
  so SQLite retrieval order can never affect a result.
- **Exactly consistent with the published integers by construction.** A required invariant test
  recomputes each quota's achieved count from the emitted membership and asserts equality with the
  corresponding `AccessionQuotaDiagnostic` / `QuotaDiagnostic` value — a regression guard, not the
  mechanism of correctness.
- Only **`provisional`** evidence produces an affirmative contribution (Decision 014 §1).
- The Decision 018 §14 deferred quota contributes **no** membership and is never reported as satisfied.

## 7. Frozen ruling — reserve methodology

- **Purpose.** A reserve is a complete deterministic replacement package for one selected entity,
  usable only when objective verification or safe retrieval fails for that entity (Decision 013 §6).
  Constructing a reserve never substitutes anything; substitution is an M2.5 event.
- **Target coverage — every selected entity, including controls.** All 24 selected entities are
  reserve targets. Whether a valid reserve exists is decided by *compatibility*, never by entity role.
- **Exactly one reserve package per target.** Where a compatible reserve exists, exactly one package
  is constructed, at **`reserve_rank = 1`**. **Multiple reserve ranks are not authorized at M2.3.**
- **Eligible pool.** Candidate entities in the same frozen snapshot that are (a) not the target, (b)
  not themselves selected in the same run, (c) able to supply the target's exact quota-contribution
  set, and (d) able to satisfy the Decision 018 §9 accession floors from their own candidate
  accessions without breaching the §8 caps.
- **Rank and tie-breaking.** Ordering reuses the accepted initial-selection tie-break — Decision 013
  §6 requires "the same tie-breaker and ordering rules used for initial selection" — i.e.
  `selection_rank` over the padded CIK under the frozen seed, with the canonical identity fallback.
  `reserve_tie_break_sha256` records it. **No new ordering rule is introduced.**
- **Replacement reuse across targets is permitted.** One replacement CIK may be the rank-1 reserve for
  more than one target. Reserve packages are **independent contingencies** and are never simultaneously
  applied. Within a single target, a replacement CIK appears **at most once**, and only rank 1 exists.
  Explicitly **not** introduced: global replacement uniqueness; any cross-target assignment problem;
  greedy pool consumption; target-order-dependent allocation; or any pool-exhaustion state arising
  from another target's reservation. Each target's reserve is computed independently of every other
  target's, so the result cannot depend on the order targets are processed.
- **Signature.** Exactly Decision 016 §7's frozen input list: signature and quota policy versions;
  entity role; control kind; size stratum; industry family; industry-quota eligibility; history class;
  the eventful-and-currently-inactive contribution; primary-universe eligibility; the name-change,
  support-pair, multi-registrant, XBRL-era, year/cohort, and amendment-purpose contributions; the
  accession counts and roles the package supplies; and the evidence floor. Computed with
  `release/hashing.py` (Decision 013 §7).
- **Independent recomputation.** `replaces_signature_sha256` is computed from the **target's** own rows
  and `reserve_signature_sha256` from the **replacement's** own rows; they must be equal. The DDL
  `CHECK` proving the two stored columns match is necessary but **not sufficient** (Decision 016 §7),
  so acceptance tests recompute both from normalized content.
- **Permitted symmetric difference: none.** Schema-enforced, not a tunable tolerance.
- **Cap and floor preservation**, **amendment-family and linked-amendment coverage**, and **role
  compatibility from frozen attributes** (never re-labelled to manufacture a match) all hold, evaluated
  by the accepted S5.1 helpers.
- **Disjointness and duplicates.** `target <> replacement` is DDL-enforced. That the replacement is not
  itself a selected entity, and that one replacement CIK appears at most once per target, are **not**
  DDL-enforced and become required S5.4 invariants with adversarial tests.
- **Lifecycle and publication.** Reserves are written inside the S5 run's `running` window, are never
  published, and are not a manifest input before Stage S6.

### 7.1 No compatible reserve — frozen ruling

Where no candidate preserves a target's complete quota-contribution signature, the outcome is:

- **target-specific** — recorded against that selected entity, never as a run-level state;
- **review-required** — carrying `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` (§13);
- **nonblocking** — the run still reaches `feasible`; §3 confirms a run with zero reserves transitions
  successfully;
- **not selection infeasibility** and **not node-limit exhaustion** — reserve construction runs no
  search, discards no incumbent, and introduces no new run state;
- **never permission to substitute an approximate reserve** — Decision 013 §6 forbids discretionary
  substitution outright, and the Decision 013 §6 consequence (complete deterministic reselection or
  fail-closed) belongs to the M2.5 replacement event, not to S5.4 construction;
- **represented deterministically and durably** — in `pilot_selection_entity_reasons`, the table
  authorized by §8.2, with `reason_scope = 'reserve'` and
  `reason_code = 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE'`. Exactly one such row per target, and never
  alongside a reserve package for the same target.

## 8. Frozen ruling — schema and migration

**For reserves, contributions, and quota members: no DDL and no migration.** Every table, column,
constraint, index, and trigger those families need already exists in migration `0009` (Decision 016
§§3, 7). `PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION = "quota-contribution/1.0"` already exists in
`pilot_policy.py` **and** its `pilot_replacement_signature` row is already seeded in
`reference_policy_versions`, so no policy-reference migration is needed. Registering
`REVIEW_PILOT_NO_COMPATIBLE_RESERVE` also needs no migration: `reference_reason_codes` is seeded at
runtime from `reasons.py` (`storage/catalog.py`), which is how the five Decision 018 §21 codes entered
without one.

**For the §7.1 durable no-compatible-reserve record: exactly one future additive migration `0012` is
authorized in principle.** Migration `0009` has no lawful location for it — §8.1 records the audit that
established this — so the owner authorized `0012` rather than weakening the durability requirement.
**It is not created by this record**, and **no migration other than `0012` is authorized.**

### 8.1 Why migration `0009` cannot hold this record

A lawful location must carry all four of: the **target selected entity**, the **selection run
identity**, a **reason code** (a `reference_reason_codes` foreign key), and the meaning **"no reserve
package exists"**. Every candidate in the schema was audited and probed directly:

| Candidate location | run identity | target selected entity | reason-code FK | Verdict |
|---|---|---|---|---|
| `pilot_selected_entities` | yes | yes | **no** | **No `reason_code` column** — probe: "no such column: reason_code" |
| `pilot_candidate_entity_reasons` | **no** | candidate entity, not selected | yes | **No `selection_run_id` column**; snapshot-scoped frozen candidate content — probe: insert "requires a building snapshot", so it is unwritable once the snapshot is frozen. Its `reason_scope` CHECK admits no reserve scope |
| `pilot_candidate_accession_reasons` | no | accession, not entity | yes | wrong grain entirely |
| `pilot_selection_run_events.reason_code` | yes | **no** | yes | No entity column, and `UNIQUE (selection_run_id, attempt_number)` permits **one event per attempt**, so N per-target rows are structurally impossible — probe: UNIQUE constraint failed. Also a mutable operational log |
| `pilot_selection_runs.failure_reason_code` | yes | **no** | yes | The only writable candidate — a single run-level column that cannot name a target and would be a *failure* reason on a `feasible` run. Repurposing it is rejected |
| `pilot_reserves` | yes | yes | **no** | Cannot represent absence: `replacement_cik_numeric`, `replaces_signature_sha256`, and `reserve_signature_sha256` are all `NOT NULL`, `reserve_rank` is `CHECK (>= 1)`, and `CHECK (target <> replacement)` applies. No `reason_code` column |
| `pilot_quota_results` | yes | via members | **no** | **No `reason_code` column** — probe: "no such column: reason_code". A synthetic reserve quota would be a repurposed table |

**The gap, exactly: no table in the schema carries all three of `selection_run_id`, a selected entity,
and a `reference_reason_codes` foreign key.** The reason-bearing tables are snapshot- or
candidate-scoped, or run-level singletons; the run-and-entity-scoped tables carry no reason code.

### 8.2 Frozen ruling — migration `0012`

**Filename (frozen):** `src/disclosure_drift/storage/migrations/0012_m23_selection_entity_reasons.sql`

**Purpose:** provide one normalized, durable, target-specific location recording that a selected
entity's S5.4 reserve construction produced no compatible reserve.

**Exactly one new `STRICT` table is created**, `pilot_selection_entity_reasons`, with the columns and
constraints below. They follow the established conventions of the closest structural sibling,
`pilot_selected_entity_quota_contributions` — a run-scoped child of `pilot_selected_entities`.

```sql
CREATE TABLE IF NOT EXISTS pilot_selection_entity_reasons (
    selection_run_id  TEXT NOT NULL,
    snapshot_id       TEXT NOT NULL,
    cik_numeric       INTEGER NOT NULL,
    reason_scope      TEXT NOT NULL CHECK (reason_scope IN ('reserve')),
    reason_code       TEXT NOT NULL REFERENCES reference_reason_codes(reason_code),
    recorded_at_utc   TEXT NOT NULL,
    -- One disposition per (run, snapshot, target, scope): reason_code is deliberately
    -- NOT part of the key, so a target can never carry two reserve dispositions.
    PRIMARY KEY (selection_run_id, snapshot_id, cik_numeric, reason_scope),
    FOREIGN KEY (selection_run_id, snapshot_id, cik_numeric)
        REFERENCES pilot_selected_entities (selection_run_id, snapshot_id, cik_numeric),
    -- Only the one authorized reserve-scope code may ever be stored (section 13).
    CHECK (reason_scope <> 'reserve'
           OR reason_code = 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE')
) STRICT;
```

Column and constraint rulings:

- **`cik_numeric`, not `anchor_cik_numeric`.** In this schema a qualified CIK name marks a row that is
  *about something else*: `pilot_selected_accessions.anchor_cik_numeric` is the entity an **accession**
  is anchored to, and `pilot_reserves.target_cik_numeric` / `replacement_cik_numeric` name the two ends
  of a **package**. A row here is about the selected entity itself, exactly like
  `pilot_selected_entity_quota_contributions.cik_numeric` and `pilot_quota_result_members.cik_numeric`,
  both of which carry the same composite foreign key. **This is the one point where the frozen column
  name differs from the owner's minimum-identification wording**, resolved under the owner's own
  instruction to follow existing repository naming conventions; the identified value — the target
  selected entity's CIK — is unchanged. Flagged for confirmation at independent review.
- **Composite foreign key** to `pilot_selected_entities (selection_run_id, snapshot_id, cik_numeric)`,
  per Decision 016 §6: every result table proves its run and snapshot refer to the same pair.
- **`reason_code` foreign key** to `reference_reason_codes`, matching every other reason column.
- **Primary key excludes `reason_code`**, deliberately departing from the candidate reason tables'
  shape (which include it). Including it would permit two different codes for one target and scope;
  excluding it makes a duplicate disposition row **structurally impossible**, which is what the
  one-disposition-per-target requirement demands.
- **`recorded_at_utc TEXT NOT NULL`** is included solely because it is the established convention on
  every reason and result-child table. It is **excluded from every deterministic identity and hash**
  (Decision 016 §8) and **never defines the outcome**.
- **No `detail` column.** The candidate reason tables carry `detail TEXT NOT NULL DEFAULT ''`; it is
  deliberately omitted here so no free-text value can form part of the deterministic disposition.
- **`STRICT`**, matching every migration-`0009` table.

**Lifecycle guards (required) — exact frozen SQL.** The independent governance review of 2026-07-29
found that specifying these as "mirroring migration `0009`" inherits that migration's OLD-only UPDATE
predicate, and demonstrated the consequence: a disposition row could be moved from a `running` run
onto an already-`feasible` run by updating `selection_run_id`, leaving the sealed run with one target
holding **both** a rank-1 reserve package and a no-compatible-reserve row, after the disposition
trigger had already executed. The guards are therefore frozen as exact SQL, and they are **not**
mirrors of `0009`:

```sql
CREATE TRIGGER pilot_selection_entity_reasons_insert_guard
BEFORE INSERT ON pilot_selection_entity_reasons
WHEN NOT EXISTS (
    SELECT 1 FROM pilot_selection_runs
    WHERE selection_run_id = NEW.selection_run_id AND run_state = 'running')
BEGIN
    SELECT RAISE(ABORT,
        'pilot selection entity reason insert requires an existing running selection run');
END;

CREATE TRIGGER pilot_selection_entity_reasons_update_guard
BEFORE UPDATE ON pilot_selection_entity_reasons
BEGIN
    -- Both the run being written from and the run being written to must exist and be
    -- running, so a row can never be moved onto a terminal run.
    SELECT RAISE(ABORT,
        'pilot selection entity reason update requires an existing running selection run')
    WHERE NOT EXISTS (
            SELECT 1 FROM pilot_selection_runs
            WHERE selection_run_id = OLD.selection_run_id AND run_state = 'running')
       OR NOT EXISTS (
            SELECT 1 FROM pilot_selection_runs
            WHERE selection_run_id = NEW.selection_run_id AND run_state = 'running');
    -- Target identity is immutable: a disposition row is never reassigned between runs,
    -- snapshots, or selected entities. All three columns are NOT NULL, so no comparison
    -- can yield NULL and silently skip this check.
    SELECT RAISE(ABORT,
        'pilot selection entity reason target identity is immutable')
    WHERE NEW.selection_run_id <> OLD.selection_run_id
       OR NEW.snapshot_id      <> OLD.snapshot_id
       OR NEW.cik_numeric      <> OLD.cik_numeric;
END;

CREATE TRIGGER pilot_selection_entity_reasons_delete_guard
BEFORE DELETE ON pilot_selection_entity_reasons
WHEN NOT EXISTS (
    SELECT 1 FROM pilot_selection_runs
    WHERE selection_run_id = OLD.selection_run_id AND run_state = 'running')
BEGIN
    SELECT RAISE(ABORT,
        'pilot selection entity reason delete requires an existing running selection run');
END;
```

Rulings these guards freeze:

- **Every guard fails closed when the associated run does not exist.** The predicate is an explicit
  `NOT EXISTS (… AND run_state = 'running')`, which is true — and therefore aborts — both when the run
  is not `running` and when no such run row exists. `0009`'s
  `(SELECT run_state …) <> 'running'` form yields SQL `NULL` for a missing run, so its `WHEN` never
  fires; that three-valued-logic path does not exist here. Foreign keys remain enabled and required —
  this makes the triggers correct when reasoned about independently, not a substitute for them.
- **`selection_run_id`, `snapshot_id`, and `cik_numeric` are immutable.** A disposition row cannot be
  moved between runs, between snapshots, between selected target entities, or from a `running` run
  onto a `feasible` or any other terminal run. Both the OLD and the NEW run are checked explicitly;
  neither foreign keys nor the OLD check alone is relied on.
- **`recorded_at_utc` may be updated while the same associated run remains `running`.** It is
  operational provenance only (§9) and never defines the outcome. `reason_scope` and `reason_code` are
  already pinned to single values by the table's CHECK constraints, so neither can be changed to any
  other value.
- **Rows are immutable once the run leaves `running`** — every update and delete then aborts.

**This ruling applies only to the new migration-`0012` objects.** Migrations `0009`–`0011` are **not**
modified to repair their inherited OLD-only or NULL-comparison behaviour; that is out of scope here.

**Feasible-transition completeness (required, additive) — exact frozen SQL.**

```sql
CREATE TRIGGER pilot_selection_run_feasible_requires_reserve_disposition
BEFORE UPDATE OF run_state ON pilot_selection_runs
WHEN NEW.run_state = 'feasible' AND OLD.run_state = 'running'
BEGIN
    SELECT RAISE(ABORT,
        'pilot selection feasible transition requires exactly one reserve disposition per selected entity')
    WHERE EXISTS (
        SELECT 1 FROM pilot_selected_entities AS se
        WHERE se.selection_run_id = NEW.selection_run_id
          AND se.snapshot_id = NEW.snapshot_id
          AND ( (SELECT COUNT(*) FROM pilot_reserves AS r
                  WHERE r.selection_run_id = se.selection_run_id
                    AND r.snapshot_id = se.snapshot_id
                    AND r.target_cik_numeric = se.cik_numeric)
              + (SELECT COUNT(*) FROM pilot_selection_entity_reasons AS pr
                  WHERE pr.selection_run_id = se.selection_run_id
                    AND pr.snapshot_id = se.snapshot_id
                    AND pr.cik_numeric = se.cik_numeric
                    AND pr.reason_scope = 'reserve')
              ) <> 1
    );
    SELECT RAISE(ABORT,
        'pilot selection feasible transition requires every reserve package to be reserve_rank 1')
    WHERE EXISTS (
        SELECT 1 FROM pilot_reserves AS r
        WHERE r.selection_run_id = NEW.selection_run_id
          AND r.snapshot_id = NEW.snapshot_id
          AND r.reserve_rank <> 1
    );
    SELECT RAISE(ABORT,
        'pilot selection reserve-scope disposition admits only REVIEW_PILOT_NO_COMPATIBLE_RESERVE')
    WHERE EXISTS (
        SELECT 1 FROM pilot_selection_entity_reasons AS pr
        WHERE pr.selection_run_id = NEW.selection_run_id
          AND pr.snapshot_id = NEW.snapshot_id
          AND pr.reason_scope = 'reserve'
          AND pr.reason_code <> 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE'
    );
END;
```

The invariant is unchanged: **every selected entity, including controls, must have exactly one reserve
disposition** — either exactly one `pilot_reserves` row at `reserve_rank = 1`, or exactly one
`pilot_selection_entity_reasons` row with `reason_scope = 'reserve'` and
`reason_code = 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE'`. The two are mutually exclusive.

What each condition catches, and what it deliberately does not:

- the per-target sum condition rejects **neither** disposition (0), **both** (2), **multiple reserve
  packages** for one target, and **duplicate disposition rows**;
- the rank condition rejects **any reserve at a rank other than 1** — load-bearing on its own, because
  a rank-2-only target still sums to exactly 1 and would otherwise pass;
- the code condition rejects an **unauthorized reserve-scope reason**; a wrong `reason_scope` and an
  unauthorized `reason_code` are additionally refused at write time by the table's CHECK constraints;
- **two rank-1 reserve rows for one target are already rejected at insertion time** by migration
  `0009`'s existing `UNIQUE (selection_run_id, snapshot_id, target_cik_numeric, reserve_rank)`.
  Migration `0012` **neither duplicates nor replaces that constraint**, and **no test may require the
  transition trigger to catch a second identical rank-1 row** — that row cannot be written in the
  first place, so such a test would be unreachable.

On an empty selected set this trigger is vacuously satisfied; the accepted migration-`0009` trigger
`pilot_selection_run_feasible_requires_actual_results` independently requires exactly 24 selected
entities, so no feasible run can pass through the gap.

**Trigger names.** All four — `pilot_selection_entity_reasons_insert_guard`,
`pilot_selection_entity_reasons_update_guard`, `pilot_selection_entity_reasons_delete_guard`, and
`pilot_selection_run_feasible_requires_reserve_disposition` — are new and collision-free against every
object in migrations `0009`–`0011`.

**Existing migrations are untouched.** Migration `0012` does not edit, replace, or reinterpret
migrations `0009`, `0010`, or `0011`, modifies no existing table definition, and **replaces no existing
trigger** — every trigger it adds is new. No modification of
`pilot_selection_run_requires_clean_non_feasible_result` is required: the new table's composite foreign
key requires a parent `pilot_selected_entities` row, and that trigger already requires zero selected
entities before a non-feasible terminal transition, so with zero parents there can be zero children and
the clean-non-feasible-run invariant holds transitively.

**No policy-reference row is seeded.** `PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION =
"quota-contribution/1.0"` remains controlling, and `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` continues to be
registered through the existing `reasons.py` runtime registry and tested through the existing
reason-registry conventions. Migration `0012` is therefore **DDL-only**: one table and its triggers.

**Standing rule, unchanged:** a schema gap discovered *during implementation* — anything beyond this
authorized `0012` — remains an owner-level conflict and a stop condition, never a migration a session
may write on its own (Decision 018 §25).

### 8.3 Owner test-scoping clarification — binding, recorded 2026-07-30

Recorded with final approval. **It changes no invariant, no CHECK, no key, no foreign key, no trigger,
and no line of the §8.2 SQL, and it weakens neither the schema nor the required test suite.** It states
which enforcement layer owns each invariant, so that each is tested where it is actually enforced
rather than at a layer that can never observe it.

1. **Unauthorized reserve scope or reason code** is enforced and tested at the
   `pilot_selection_entity_reasons` **CHECK-constraint** boundary —
   `CHECK (reason_scope IN ('reserve'))` and
   `CHECK (reason_scope <> 'reserve' OR reason_code = 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE')`.
2. **Duplicate no-compatible-reserve disposition rows** for one target are enforced and tested at that
   table's **primary-key** boundary,
   `PRIMARY KEY (selection_run_id, snapshot_id, cik_numeric, reason_scope)`.
3. **Duplicate rank-1 reserve packages** for one target are enforced and tested by migration `0009`'s
   existing `UNIQUE (selection_run_id, snapshot_id, target_cik_numeric, reserve_rank)`. Migration
   `0012` neither duplicates nor replaces it.
4. **The migration-`0012` feasible-transition trigger is not required to catch states that existing
   CHECK, primary-key, foreign-key, or unique constraints make impossible to construct.** Its
   corresponding trigger conditions remain in the frozen §8.2 SQL as defence in depth and are **not**
   removed; they simply are not the boundary at which those invariants are tested, because a test
   reaching the transition through an unconstructible state is unreachable.
5. **Feasible-transition tests must still cover every constructible invalid state**, including:
   - neither disposition;
   - both disposition types;
   - rank-2 only;
   - rank-1 plus rank-2;
   - a control target with no disposition;
   - one missing disposition among many selected entities.

This clarification is binding on the S5.4 implementation session and is mirrored in
[`Milestones/contracts/m23_s5_4.md`](../../Milestones/contracts/m23_s5_4.md) under "Required tests".

## 9. Frozen ruling — hashing and identity

| Identity | Material content | Excluded |
|---|---|---|
| **S5 selection run** (`selection_run_id`) | unchanged: input-schema version, snapshot identity and content digests, seed, selector and quota policy versions, node limit, objective term order | outputs of any kind, including contribution membership and reserves |
| **Quota-contribution content** | no separate digest — a re-derived output validated against re-derivation | — |
| **Reserve-set** | no set-level digest and **no reserve-set root hash** — the schema defines none | — |
| **Reserve package** (`reserve_package_id`) | content-derived 64-hex SHA-256 (Decision 016 §1) over the package's own normalized content, with `reserve_rank` as an explicit hashed column (Decision 016 §8) | timestamps, event IDs, `detail`, paths, SEC identity, outcomes, filing text |
| **Manifest** (Stage S6) | not computed at S5.4; `pilot_manifest_versions.reserves_sha256` is the S6 consumer | — |

- **`ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` remains exactly `"pilot-joint-selection-input/1.0"`.
  It is not bumped.** Contribution membership is an additive deterministic **output**; it alters no
  frozen selection input and does not change the S5 selection run identity.
- **No second S5 selection run ID is created.** Reserves are **subordinate content under the accepted
  S5 run ID**, each package carrying its own content-derived `reserve_package_id`; the schema has no
  reserve run table and scopes reserves by `(selection_run_id, snapshot_id)`.
- **`selection_result_sha256` remains `NULL` through Stage S5.4.**
- Reserve-signature policy uses the existing `PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION =
  "quota-contribution/1.0"`. **No new policy constant and no policy-reference migration** are created.
- **Mutable lifecycle timestamps remain excluded** from every hash, without exception.
- **No manifest hash, partial or whole, is computed at S5.4.**

## 10. Frozen ruling — failure and reconstruction

Every condition below is fail-closed; none may be worked around, relaxed, or resolved by dropping rows
(CLAUDE.md rule 12).

**Gate failure** — `GateFailureError`, no write, no partial state: contribution rows missing for a
feasible reconstructed run; contribution rows inconsistent with the re-derived S5.1 membership; extra
or missing quota members; a malformed signature or one that does not recompute from normalized
content; selected/reserve overlap or a replacement that is itself selected; a duplicate replacement
within one target; a reserve at any rank other than 1; a reserve violating role compatibility, an
accession cap, or an entity/accession floor; any difference between a reserve's contribution set and
its target's; a partial persisted reserve package (a package without its accessions or contributions);
a same-ID run in `planned`, `running`, or `failed`; a conflicting replay; corrupted completed reserve
rows; and a candidate snapshot unavailable or not `frozen` during reconstruction.

**Review-required, nonblocking:** no compatible reserve exists for a target (§7.1), recorded with
`REVIEW_PILOT_NO_COMPATIBLE_RESERVE`. **There is no pool-exhaustion state** — §7 makes each target's
reserve independent of every other target's, so no target can exhaust another's pool.

**Infeasible / unproven:** unchanged from Decision 018 §§17 and 28. Reserve construction adds no
search, no new infeasibility state, and never alters an incumbent selection.

**Reconstruction** re-derives the pure result, the membership, and the reserve packages from the frozen
snapshot under the run's own recorded seed, policy versions, and node limit, then validates every
persisted row against the re-derivation. It never trusts a stored value it did not re-derive.

## 11. What this record does not change

Unchanged and not reopened: the Decision 013 §5 objective and its term order; the Decision 018 quota
set, caps, floors, role assignment, amendment families, evidence penalties, fiscal-year-end and
name-change derivation, 2009/2010 pairing, node-limit and failure semantics, and retry prohibition; the
Decision 019 mappings; every accepted policy constant; every existing reason code; migrations
`0009`–`0011`; the S4 entity-only draft, which remains `running`, non-publishable, and excluded from S5
identity and every manifest input; and the `m2.3-s5-complete` checkpoint (§14.9).

## 12. Policy constants

**None new.** Reuses `PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION`, `PILOT_QUOTA_POLICY_VERSION`,
`PILOT_JOINT_SELECTOR_POLICY_VERSION`, `PILOT_SELECTION_SEED`, and
`ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` — all unchanged.

## 13. Frozen ruling — reason codes

**Exactly one new reason code is authorized**, registered through the existing `reasons.py` registry
and its `ReasonCategory` / `ReasonCode` conventions.

| Code | Category | Metadata | Purpose |
|---|---|---|---|
| `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` | `review` | requires manual review; **nonblocking** (does not block release); target-specific reserve-construction outcome | No candidate preserves the target selected entity's complete quota-contribution signature, so that target has no reserve package (Decision 013 §6; §7.1). |

**`REVIEW_PILOT_RESERVE_POOL_EXHAUSTED` is not authorized and must not be added** — §7 makes each
target's reserve independent, so no pool-exhaustion state exists. **No integrity, retry, approximation,
or substitution reason code may be added**: every reserve integrity violation in §10 is a gate failure,
and Decision 013 §6 forbids discretionary substitution outright.

## 14. Owner rulings recorded

The project owner ruled on 2026-07-29. These are binding on the design and are reflected throughout
this record and in [`Milestones/contracts/m23_s5_4.md`](../../Milestones/contracts/m23_s5_4.md).

1. **Reserve count.** Exactly one rank-1 reserve package per selected entity where a compatible
   reserve exists. Multiple ranks are **not** authorized at M2.3. → §7.
2. **No-compatible-reserve behavior.** Target-specific, review-required, nonblocking; not selection
   infeasibility; not node-limit exhaustion; not permission to substitute an approximate reserve; and
   deterministically and durably represented. → §7.1. **Its persistence location is settled by the
   owner's 2026-07-29 clarification: migration `0012` is authorized in principle — see §8.2.**
3. **Input schema version.** `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` stays exactly
   `"pilot-joint-selection-input/1.0"`; it is **not** bumped. Contribution membership is an additive
   deterministic output and alters neither the frozen selection inputs nor the S5 run identity. → §9.
4. **Selection-result hash.** `selection_result_sha256` remains `NULL` through S5.4. → §9.
5. **S5.1 public output.** One additive immutable contribution-membership output, sourced directly
   from the existing witness derivation, is approved. It must not alter selected entities, selected
   accessions, roles, ordering, the objective, evidence penalties, quota definitions or counts, caps
   or floors, amendment families, or run identity. The implementation delta requires **bounded renewed
   acceptance**. → §§5, 6.
6. **Reserve targets.** Every selected entity is a reserve target, **including controls**;
   compatibility alone determines whether a valid reserve exists. → §7.
7. **Replacement reuse.** A replacement CIK may serve different target entities; packages are
   independent contingencies, never simultaneously applied. Within one target the replacement CIK
   appears at most once and only rank 1 exists. No global replacement uniqueness, cross-target
   assignment problem, greedy pool consumption, target-order-dependent allocation, or
   pool-exhaustion-from-another-target's-reservation is introduced. → §7.
8. **Reason codes.** Exactly `REVIEW_PILOT_NO_COMPATIBLE_RESERVE`;
   `REVIEW_PILOT_RESERVE_POOL_EXHAUSTED` is **not** authorized; no integrity, retry, approximation, or
   substitution code. → §13.
9. **Checkpoint boundary.** `m2.3-s5-complete` is **immutable**. The eventual S5.4 checkpoint is a new
   annotated tag **`m2.3-s5.4-complete`** that **supplements** rather than replaces or restates the
   accepted S5 checkpoint. → §15.

Two further owner rulings were recorded after that list and are equally binding: the **authorization in
principle of migration `0012`** (2026-07-29, recorded in §8 and frozen in §8.2), and the **test-scoping
clarification** (2026-07-30, recorded in §8.3). Neither reopens any of the nine rulings above.

## 15. Checkpoint boundary

The accepted `m2.3-s5-complete` tag is immutable and is never moved, replaced, re-pointed, or
restated. The eventual S5.4 checkpoint is a **new annotated tag `m2.3-s5.4-complete`**, supplementing
it. No commit, push, or tag is authorized before S5.4 acceptance and an explicit owner instruction.

## 16. Implementation authorization

**This record authorizes no implementation by itself; Stage S5.4 authorization was carried by the
contract, which read `IMPLEMENTATION_AUTHORIZATION: YES` while the stage was open and now reads
`IMPLEMENTATION_AUTHORIZATION: NO` with `STATUS: ACCEPTED_AND_COMPLETE`.** Stage S5.4 implementation
required all of:

1. **focused independent governance re-review** of this record and of the S5.4 contract, covering the
   exact migration `0012` DDL frozen in §8.2 — the table and all four triggers — and confirming that
   the lifecycle defect the 2026-07-29 review found is closed — **SATISFIED 2026-07-30**, recommendation
   `ACCEPT_DECISION_020_FOR_OWNER_APPROVAL`;
2. **final owner approval** of this record, recorded in
   [`Docs/Decisions/decision_registry.md`](decision_registry.md) — **SATISFIED 2026-07-30**,
   `APPROVED — OWNER APPROVED 2026-07-30`;
3. a **separately issued bounded S5.4 implementation prompt** that does not widen the contract's
   authorized paths — **SATISFIED 2026-07-30**; issued, executed within the twelve authorized
   implementation paths, and independently reviewed.

All three requirements are satisfied and Stage S5.4 is accepted and checkpointed (§19). **No further
S5.4 implementation is authorized by this record**: a new explicit owner authorization is required for
any future S5.4 change, and no session may treat this approval, the contract, or
`Milestones/STATUS.md` as a substitute for it. Approval of a policy record is never itself
authorization to write code.

## 17. Reason

Stage S5.4 is the first stage whose requirements are set by the *schema* rather than by a policy
record: migration `0009` already encodes, in triggers written under Decision 016 §7 and Decision 013
§6, exactly what a reserve must be. Two of those encodings — the member-level symmetric-difference
check and the `running`-window write guard — are unsatisfiable by the accepted artifacts as they stand.
A third requirement, the owner's durable target-specific reserve-absence record, has no lawful home in
the schema at all, and the owner resolved that by authorizing one minimal additive migration rather
than by weakening the durability requirement. This record exists so those facts are settled
deliberately, on evidence, before any code is written, rather than being discovered mid-implementation
and resolved under pressure.

## 18. Approval statement

**APPROVED — OWNER APPROVED 2026-07-30.** The project owner approved this record on 2026-07-30, after
the focused independent governance re-review required by §16.1, and approved it **as written**: no
architecture, methodology, table definition, key, CHECK, trigger SQL, reason code, identity rule, or
checkpoint ruling was revised at approval.

The re-review's recommendation was `ACCEPT_DECISION_020_FOR_OWNER_APPROVAL`. It established that:

- the corrected migration-`0012` lifecycle SQL is **valid and load-bearing**;
- the original cross-run `UPDATE` bypass **reproduces** when the correction is absent;
- the frozen corrected SQL **blocks** that bypass;
- the INSERT, UPDATE, and DELETE guards **fail closed** for a missing or non-`running` run;
- `selection_run_id`, `snapshot_id`, and `cik_numeric` are **immutable**;
- all feasible-transition regression cases **pass**;
- non-feasible cleanliness **remains correct**;
- migration `0012` creates **exactly one table and four new triggers**;
- migrations `0009`–`0011` **remain unchanged**;
- **no governance defect and no approval blocker remains.**

The 2026-07-29 lifecycle defect is closed. The exact table and four-trigger SQL in §8.2 is **frozen**
and is reproduced verbatim in migration `0012`; no implementation-time reinterpretation of it is
permitted. Migration `0012` was created only in the S5.4 implementation session, after this approval.
The owner's test-scoping clarification (§8.3) is **binding**.

What approval, on its own, did **not** do (the position on 2026-07-30 before implementation):

- **It did not implement anything.** No code, test, migration `0012`, reserve behavior, persistence
  behavior, CLI behavior, manifest behavior, release behavior, or publication behavior was created by
  it (§16).
- **It did not become self-executing.** Approval cleared the S5.4 approval blocker —
  [`Milestones/contracts/m23_s5_4.md`](../../Milestones/contracts/m23_s5_4.md) became
  `READY_FOR_IMPLEMENTATION` with implementation authorization **YES** — but implementation could begin
  only under a **separately issued bounded S5.4 implementation prompt**, confined to that contract's
  exact authorized paths. Approval did not widen them.
- **It did not modify any accepted artifact.** Migrations `0009`–`0011` and the `m2.3-s5-complete`
  checkpoint are untouched and immutable (§§11, 15), and remain so after acceptance.
- **It did not begin Stage S6.** No manifest, publication, or release work is authorized, and no S5
  selection or reserve is a manifest or publication input (§2). **S6 has still not begun.**

No deviation from Decisions 013–019 is made or implied. No transition metric and no final-test metric
has been viewed in connection with this record.

## 19. Final acceptance and checkpoint

**Stage S5.4 is complete and accepted.** The project owner accepted it on **2026-07-30** on the final
independent acceptance review's recommendation **`ACCEPT_M23_S5_4_FOR_CHECKPOINT`**. This section
records the acceptance; it changes no architecture, methodology, table definition, key, CHECK, trigger
SQL, reason code, identity rule, or ruling above.

| Item | Accepted state |
|---|---|
| Final independent recommendation | `ACCEPT_M23_S5_4_FOR_CHECKPOINT` |
| Acceptance date | 2026-07-30 |
| Accepted full suite | **1899 passed, 1 skipped** (the one skip is pre-existing and unrelated: the optional `[sec]` extra is not installed) |
| Migration `0012` | **created and accepted** — `0012_m23_selection_entity_reasons.sql`, DDL-only, one `STRICT` table plus four new triggers, reproducing the §8.2 SQL byte-for-byte |
| Bounded corrections D1, T1, T2, T3 | **accepted** — the accepted-core filing-year helper owns the derivation and the reserve module holds no parser of its own; malformed non-null stored filing dates raise `GateFailureError`; persisted signatures are independently recomputed from normalized content in repository tests; multi-witness load-bearing entity contributions are tested non-vacuously |
| Checkpoint tag | `m2.3-s5.4-complete`, **supplementing** the immutable `m2.3-s5-complete` (§§14.9, 15) |
| Manifest and publication | **no S5 selection and no reserve is yet a manifest or publication input** |
| Stage S6 | **not begun**; no manifest, release, or publication work is authorized |

The acceptance review verified independently, outside the repository, that: the exact §8.2 SQL
reproduces all four frozen digests and migration `0012`'s statement region is byte-identical to it;
migration `0012` adds exactly one table and four triggers and alters nothing existing; migrations
`0009`–`0011` remain byte-identical; the accepted S5 selection, objective, quota results, amendment
families, `selection_input_sha256`, and `selection_run_id` are unchanged from the pre-S5.4 code on the
same frozen snapshot; membership is emitted as the union over every satisfying witness and is invariant
under input permutation; both reserve signatures reproduce from persisted normalized rows over disjoint
input sets with every input material; the whole run commits in one transaction with the
`running -> feasible` transition as its last statement; an injected fault at any new row family rolls
the entire run back; every new row family fails closed on corruption under both reconstruction and
same-ID replay; and a valid replay is byte-identical and writes nothing.

### 19.1 Accepted methodological limitations

Recorded for future monitoring. Each is an accepted consequence of a frozen ruling above, **not** a
defect, and none requires an implementation change.

1. **Cross-anchor amendment-family resolution.** Amendment families resolve through the accepted
   resolved-root accession identity with **no added anchor-equality condition**, so an entity can be
   credited with a linked-amendment contribution for a unit named after a different anchor. Behavior is
   deterministic, conservative, and fail-closed for reserve construction — the extra credit makes
   contribution-set matching harder, never easier — and it neither weakens contribution-set equality nor
   alters run identity. S5.1 methodology and migration `0012` are unchanged.
2. **Provenance-oriented union member sets.** `pilot_selected_accession_quota_contributions` and
   `pilot_quota_result_members` carry every member participating in at least one satisfying witness, so
   they may contain **more** members than a minimal witness would require. This is the accepted semantic
   consequence of the witness-union ruling (§6); no minimal-witness optimization is authorized.
3. **Exact bundle comparison may reduce reserve availability.** The target side uses the target's actual
   selected accession bundle and the replacement side the replacement's complete deterministic
   role-assignable bundle from the frozen snapshot. No discretionary trimming, subset search, or package
   optimization is authorized merely to obtain compatibility (§7), so fewer targets may carry a package
   and more may carry a `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition. That is intended.
4. **Signature contribution values are counts.** The seven named contribution fields in the reserve
   signature are integer counts of distinct achieved units the package supplies, not Boolean presence
   values (Decision 016 §7). This is intentionally conservative and further reduces reserve
   availability.
5. **Schema-layer transition-test observation — nonblocking.** No repository test drives a strict
   subset, a strict superset, or an empty reserve contribution set through migration `0009`'s
   symmetric-difference check at the `running -> feasible` transition; that trigger is unchanged accepted
   `0009` DDL, the three cases are recorded as directly observed in §3, and the pure module and the
   persistence layer each test the equivalent behavior non-vacuously. The final acceptance review
   validated all three cases independently — exact accepted; subset, superset, and empty each refused —
   so nothing is untested in substance. Adding repository coverage at that layer is optional and at the
   owner's discretion; it is **not** required for acceptance and implies no implementation change.

### 19.2 What acceptance does not do

- **It authorizes no further implementation.** Any future S5.4 change requires a new explicit owner
  authorization and its own bounded contract; this record and the closed S5.4 contract authorize none.
- **It changes nothing frozen.** The §8.2 SQL, membership-union semantics, contribution-count
  semantics, target/replacement bundle semantics, cross-anchor amendment behavior, the filing-date
  helper, reserve selection, ranking, signatures, package identities, persistence order, reconstruction,
  migrations `0009`–`0012`, the reason registry, every policy version,
  `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION`, the S5 run identity, and `selection_result_sha256`
  (still `NULL`) are all unchanged.
- **It does not touch S4.** The entity-only draft stays `running`, non-publishable, and excluded from S5
  identity and every manifest input (§11).
- **It does not begin S6.** Stage S6 remains separately gated and unauthorized, and the S6 handoff
  conditions in the S5.4 contract still apply.
- **It does not move `m2.3-s5-complete`.** That tag is immutable; `m2.3-s5.4-complete` supplements it.
