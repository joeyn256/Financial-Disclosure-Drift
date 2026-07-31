# Decision 021 — M2.3 Stage S6 Manifest Construction, Terminal Result Identity, and the Publication Boundary

**Date:** 2026-07-30
**Status:** ACCEPTED
**Approved:** 2026-07-30 by the project owner, on the focused independent governance review of v0.5,
whose recommendation was `ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL`. **This record is binding.**
**Revision:** v0.5, 2026-07-30 — the accepted revision. v0.5 supersedes all four earlier proposed
drafts **within this record only**, so nothing downstream is invalidated by any supersession.

| Draft | Independently reviewed? | Approved? | Outcome |
|---|---|---|---|
| v0.1 | yes | **no** | `REQUIRES_OWNER_CLARIFICATION`; produced owner corrections A–F, applied at v0.2 |
| v0.2 | **no** | **no** | never independently reviewed; changed the normative SQL, its digests, the `selector_policy_sha256` preimage, and the document contract |
| v0.3 | yes | **no** | `REQUIRES_OWNER_CLARIFICATION`; produced the §10 crosswalk and manifest-replacement corrections, applied at v0.4 |
| v0.4 | yes | **no** | **not ready** — it applied the exhaustive §10 crosswalk and the manifest replacement guard, but the **selection-run replacement, deletion, and identity bypasses remained open** (§19.11, now closed) |
| **v0.5** | **yes** | **YES — owner approved 2026-07-30** | `ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL`; adds triggers 6, 7, and 8 and the §15.5 guarantee |

**The v0.5 review reproduced every governance invariant independently** — all nine §15.3 digests from
the record bytes, the 10939-byte and 186-line region, blocks 1–5 byte-identical to v0.4, exactly
eight triggers added to a scratch `0001`–`0012` catalog with nothing removed or altered, 318
adversarial assertions passing across all four `recursive_triggers` × `foreign_keys` combinations,
the twelve structural-fingerprint probe classes, the acyclic digest graph, and the 81-item crosswalk
mapped row by row back to the milestone-plan source. It returned **no governance blockers and no
owner clarifications required**, with one editorial correction to explanatory arithmetic (§13.2.1)
and two non-blocking observations carried into §19.

**Approval is not implementation.** [`Milestones/contracts/m23_s6.md`](../../Milestones/contracts/m23_s6.md)
moves to `READY_FOR_IMPLEMENTATION` with `IMPLEMENTATION_AUTHORIZATION: YES`, which records only that
nothing external blocks the stage. A **separately issued bounded S6 implementation authorization** is
still required before any code, test, or migration is written (§23 condition 3;
[`contracts/README.md`](../../Milestones/contracts/README.md)).

- **v0.2** applied six bounded owner corrections issued after the focused independent governance
  review of v0.1: (A) six-field manifest-identity immutability (§9.2); (B) migration `0013` grows
  from three triggers to four, with completely restated normative SQL and digests (§15);
  (C) the complete pilot-manifest document schema, citing
  [`Milestones/milestone_2_3_pilot_selection_plan.md`](../../Milestones/milestone_2_3_pilot_selection_plan.md)
  §10 explicitly (§13), with the consequent extension of `selector_policy_sha256` (§8.4);
  (D) the structural-fingerprint partition rule (§8.1); (E) explicit classification of six residual
  schema columns (§8.1, §8.4); (F) the CLI narrowing and the complete S7–S10 boundary (§16, §17).
- **v0.3** applied one further bounded owner correction, to correction D only: the structural
  fingerprint binds **five** columns, not three — `region`, `state`, `member_name`, `observed_type`,
  and `record_path` (§8.1) — and the v0.2 accepted limitation that claimed `observed_type` and
  `record_path` were unbound was **withdrawn and replaced** (§19.8).
- **v0.5** applies one bounded owner correction issued after the focused independent governance
  review of v0.4. That review accepted the §10 crosswalk and the five-trigger manifest design, and
  proved by direct probe that `pilot_selection_runs` was still open on three fronts the manifest
  table had just been closed on: **row replacement**, **deletion**, and **identity mutation**.
  Migration `0013` therefore grows from five triggers to **eight** (§15): trigger 6
  `pilot_selection_run_replacement_guard`, trigger 7 `pilot_selection_run_delete_guard`, and trigger
  8 `pilot_selection_run_identity_guard`. **The five v0.4 blocks are retained byte-for-byte and keep
  their per-block digests; trigger 2 is neither widened nor renamed.** The v0.4 five-block region,
  its 7436-byte and 129-line counts, and its concatenation digest `6bfb897c…` are **withdrawn as a
  composition** (§15.3). §15.5 now states the append-once and identity guarantee without
  qualification, and §19.11 — the open finding v0.4 could not resolve — is **closed**.
  **Nothing else moves:** not the 81-item §10 crosswalk or any classification, the five-column
  structural fingerprint, the eleven-field `selector_policy_sha256`, any component, selection-result,
  root, or `manifest_id` preimage, six-field manifest-identity immutability, the complete document
  contract, the proposed-only lifecycle, the S4/S5 or S7–S10 boundaries, the CLI deferral, the
  serialization location, the seven implementation and test paths, the record status, the contract
  status, or the implementation authorization.
- **v0.4** applied two bounded owner corrections issued after the focused independent governance
  review of v0.3, which found three defects and returned `REQUIRES_OWNER_CLARIFICATION`:
  - **Correction A — the exhaustive milestone-plan §10 crosswalk (§13.2.1).** The review found that
    §13.1 claimed milestone plan §10 was "neither superseded nor narrowed" and §13.2 named exactly
    two deliberate omissions, while **nineteen §10 items and four partially covered items were
    neither serialized nor classified**. §10 is now enumerated **item by item, atomically**, and
    every one of the **81** atomic items is classified into exactly one of four categories, with
    zero unclassified. The review's third finding — §13.2's heading reading "twelve blocks" over a
    thirteen-row table — is corrected in the same pass.
  - **Correction B — migration `0013` grows from four triggers to five (§15).** The review
    demonstrated that six-field manifest-identity immutability held on the `UPDATE` path only:
    `INSERT OR REPLACE` rewrote a manifest row wholesale — `manifest_id`, the root, all eight
    component digests, `ordinal_version` and `manifest_state` alike — without firing trigger 4,
    migration `0009`'s hashes-immutable guard, its transition guard, or its no-delete guard. A fifth
    trigger closes every uniqueness route on `pilot_manifest_versions`. **The four v0.3 triggers keep
    their responsibilities and their exact bytes;** the statement region grows from four blocks to
    five, so **the v0.3 four-block region, its 4990-byte and 88-line counts, and its concatenation
    digest `51151767…` are withdrawn** (§15.3).

  **Nothing else moves:** not the five-column structural fingerprint, the eleven-field
  `selector_policy_sha256`, the `selection_result_sha256` preimage, any other component preimage,
  the root preimage, the `manifest_id` derivation, six-field identity immutability, the proposed-only
  lifecycle, the S4/S5 or S7–S10 boundaries, the CLI deferral, the serialization location, the seven
  authorized implementation paths, the record status, the contract status, or the implementation
  authorization. **The exhaustive crosswalk required no preimage change**: every §10 item that has a
  persisted column was already committed, directly or transitively, by `root_manifest_sha256` (§13.3).

**The corrections are the project owner's, not this record's.** **The forthcoming focused
independent review must assess v0.5 on its own terms and may not inherit the v0.1, v0.3, or v0.4
recommendation, or any conclusion reached about the never-reviewed v0.2** — v0.5 changed the
normative SQL again, and a changed statement region is a new object of review (§23).
**Type:** Implementation and provenance decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged by this record. No hypothesis, cohort window, maturity gate,
outcome definition, threshold, or seed is altered.
**Supersedes:** nothing. **Interprets and extends** the Stage-S6 boundary fixed by
[Decision 018](decision_018_m23_s5_accession_selection_policy.md) §22, and operationalizes
[Decision 013](decision_013_pilot_selection_mechanics.md) §§7–8 and
[Decision 016](decision_016_m23_schema_and_artifact_architecture.md) §§5, 8 for Stage S6. It
redesigns no accepted selection policy, no objective, no quota definition, and no reserve rule, and
it reopens nothing in [Decision 020](decision_020_m23_s5_4_reserve_architecture.md).
**Governs:** Milestone 2.3, Stage S6 onward.
**Related:** [Decision 009](decision_009_raw_data_governance.md) §10 (release hashing precedent),
[Decision 013](decision_013_pilot_selection_mechanics.md) §§6, 7, 8,
[Decision 016](decision_016_m23_schema_and_artifact_architecture.md) §§1, 3, 5, 6, 7, 8,
[Decision 017](decision_017_s4_quota_policy_and_control_evidence.md),
[Decision 018](decision_018_m23_s5_accession_selection_policy.md) §§6, 22, 25, 26, 27,
[Decision 019](decision_019_m23_s5_storage_to_pure_input_mapping.md),
[Decision 020](decision_020_m23_s5_4_reserve_architecture.md) §§9, 11, 14.4, 19.

**This record is accepted and binding, and still authorizes no implementation by itself.** It
records the project owner's Stage-S6 rulings and freezes the resulting architecture so that a bounded
implementation can be authorized against a fixed target. Two of the three gates are now closed: the
focused independent governance review of v0.5 (2026-07-30,
`ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL`) and final owner approval recorded in
[`decision_registry.md`](decision_registry.md). **The third remains open** — a **separately issued
bounded S6 implementation prompt** that does not widen the contract's authorized paths. Approval of a
policy record is never itself authorization to write code.

---

## 1. Why this record exists

Stage S6 was deferred by [Decision 018](decision_018_m23_s5_accession_selection_policy.md) §§22 and
31 and excluded from Stage S5.4 by [Decision 020](decision_020_m23_s5_4_reserve_architecture.md) §2.
**Six** facts make it unimplementable under the existing records without a new decision.

**Fact 1 — the nine manifest hash layers are named but undefined.** Decision 013 §7 names the layers
and migration `0009` gives `pilot_manifest_versions` nine `NOT NULL` 64-hex columns for them, but no
record states which rows or which columns feed any one of them. A hash contract cannot be
implemented from a list of layer names.

**Fact 2 — `selection_result_sha256` is defined by nothing.** The column exists on
`pilot_selection_runs` with a 64-hex `CHECK`, has been `NULL` since Stage S3, is written and read by
no module, and Decision 020 §14.4 explicitly reserved the question of whether it stays `NULL` beyond
S5.4 for Stage S6.

**Fact 3 — the schema does not enforce manifest eligibility.** §3 records the evidence: a
`pilot_manifest_versions` row can today be inserted, and driven to `owner_approved`, over a run that
is `running`, `infeasible`, or otherwise ineligible — including the permanently-`running` Stage-S4
entity-only draft that Decision 018 §§6 and 27 and Decision 020 §11 exclude from every manifest
input. That exclusion is **policy-only**, and a policy-only exclusion of a publication input is
exactly the kind of gap this project closes deliberately rather than discovers late.

**Fact 4 (added at v0.2) — manifest identity is mutable after insertion.** §3.3 records the
evidence. `manifest_id`, `manifest_schema_version`, `ordinal_version`, and `supersedes_manifest_id`
can all be rewritten after a manifest row exists. Two of those four are inputs to the `manifest_id`
preimage and one is an input to the `root_manifest_sha256` preimage, so a content-derived identity
can be silently invalidated, and a row can be driven into disagreement with its own immutable root.
A content-derived ID that its own schema lets you edit is not a content-derived ID.

**Fact 5 (added at v0.4) — a manifest row can be replaced wholesale, past every guard.** §3.5
records the evidence. `INSERT OR REPLACE` deletes and reinserts, and SQLite does not fire a
`BEFORE DELETE` trigger for that delete unless `PRAGMA recursive_triggers` is on, which this project
never sets. Every existing manifest guard is either a `BEFORE UPDATE` or a `BEFORE DELETE` trigger,
so a single statement rewrites identity, lineage, all eight component digests, the root, and the
manifest state — including over an **`owner_approved`** manifest. An immutability rule that a
default-pragma connection can step around is not an immutability rule.

**Fact 6 (added at v0.5) — the selection run itself can be replaced, deleted, and re-identified.**
§3.6 records the evidence. The same replacement mechanics apply to `pilot_selection_runs`, which is
**worse off than the manifest table** because it has **no delete guard at all** — so neither
`recursive_triggers` setting helps. A sealed terminal digest can be cleared by an `INSERT OR REPLACE`
that simply omits the column, the whole run can be removed by a plain `DELETE`, and
`selection_run_id`, `snapshot_id`, and `selection_input_sha256` can each be rewritten by direct
`UPDATE` — the last of these in **every** shape and under **every** pragma setting. Because
`selection_input_sha256` is an input to §6.1's preimage, rewriting it leaves a sealed
`selection_result_sha256` that no longer recomputes from its own row, which §11.2(3) requires. A seal
that survives every write path but stops matching its own preimage is not a terminal identity.

## 2. Scope

**In scope:** the deterministic pilot-manifest and terminal-result hashing architecture; the exact
canonical preimage of every digest; the circularity exclusions; the manifest write contract and its
fail-closed eligibility preconditions; the lifecycle and transaction rules; reconstruction and replay;
the serialization contract; the proposed-only boundary; and the schema ruling, including the complete
normative SQL of migration `0013`.

**Out of scope, and explicitly not authorized by this record:** live SEC metadata execution; a real
candidate snapshot; the exact real-data manifest instance; owner approval of a manifest; publication
of any artifact; projection-recovery writing; a CLI surface (§16); forecasts and outcomes; the M2.5
replacement event; and every Stage S7, S8, S9, and S10 activity (§17). Also out of scope: any change to the Decision 013 §5 objective,
the Decision 018 quota set, roles, caps, floors, amendment families, the evidence-penalty rule, the
selection tie-break formula, the Decision 020 reserve architecture, or any accepted S4 or S5
artifact.

## 3. Evidence of record

Observed directly against migrated scratch catalogs built by the accepted migration chain
(`0001`–`0012`), on SQLite 3.53.3. No repository file and no production catalog was written; every
catalog was a temporary directory discarded on exit.

### 3.1 Gap 1 — `selection_result_sha256` is entirely unguarded

Every trigger on `pilot_selection_runs` is declared `BEFORE UPDATE OF run_state` or
`BEFORE UPDATE OF run_state, current_attempt`. No trigger names `selection_result_sha256`, so an
`UPDATE` touching only that column fires none of them.

| Probe | Result |
|---|---|
| `UPDATE … SET selection_result_sha256 = <hex>` on a **terminal** run | **accepted** — no guard |
| overwrite an already-non-`NULL` `selection_result_sha256` with a different value | **accepted** — not immutable |
| reset a non-`NULL` `selection_result_sha256` back to `NULL` | **accepted** — clearable |
| **`INSERT` a run row already carrying a `selection_result_sha256`** (v0.2) | **accepted** — no `INSERT` guard |
| **`INSERT` a run row directly in `run_state = 'feasible'` and already sealed** (v0.2) | **accepted** |

Consequence: populating the column in a separate Stage-S6 transaction is schema-permitted today, but
so are silent mutation and silent erasure of a sealed digest. The two v0.2 rows matter because
`pilot_selection_runs` has **no `INSERT` guard of any kind**: an append-once rule enforced only on
the `UPDATE` path is not append-once, because a row can be created already sealed and so present a
terminal identity that no transition ever produced. Migration `0013`'s trigger 1 (§15.1) closes it.

### 3.2 Gap 2 — manifest eligibility is unenforced

`pilot_manifest_versions` carries four triggers (transition guard, supersession-requires-successor,
hashes-immutable, no-delete). **None is an `INSERT` guard, and none consults the referenced run.**

| Probe | Result |
|---|---|
| `INSERT` a manifest whose run is `infeasible` | **accepted** |
| `INSERT` a manifest whose run is `running` (the Stage-S4 draft shape) | **accepted** |
| drive either to `manifest_state = 'owner_approved'` | **accepted** |

Consequence: the composite foreign key to `pilot_selection_runs (selection_run_id, snapshot_id)`
constrains *identity*, not *state*. Nothing in the schema prevents an approved manifest over the S4
entity-only draft.

### 3.3 Gap 3 (added at v0.2) — manifest identity is mutable after insertion

`pilot_manifest_hashes_immutable` covers the eight component digests and the root. **It covers no
identity column.** `manifest_id` is a `TEXT PRIMARY KEY`, which SQLite does not make immutable.

| Probe | Result |
|---|---|
| `UPDATE … SET manifest_id = <other 64-hex>` | **accepted** — the content-derived ID is editable |
| `UPDATE … SET ordinal_version = 9` | **accepted** — a `manifest_id` preimage input (§9.1) |
| `UPDATE … SET supersedes_manifest_id = …` | **accepted** — a `manifest_id` preimage input (§9.1) |
| `UPDATE … SET manifest_schema_version = 'x/9'` | **accepted** — a `root_manifest_sha256` preimage input (§9) |

Consequence, and why this is not cosmetic: `root_manifest_sha256` **is** immutable, so mutating
`manifest_schema_version` drives a row into permanent disagreement with its own frozen root, and
mutating `ordinal_version` or `supersedes_manifest_id` silently falsifies `manifest_id` against its
own preimage — with no recompute obligation anywhere in the schema. Migration `0013`'s trigger 4
(§15.1) holds all six identity fields immutable together.

### 3.4 Facts that bound the cost of every ruling below

- **No production catalog database exists, and no candidate-snapshot builder exists.** No module
  writes any `pilot_candidate_*` table (Decision 020 §3; `Docs/architecture_map.md` §4). Every
  accepted S5 artifact was produced against in-test fixtures. Every consequence here is code-only:
  no data migration, no reprocessing, and no real pilot sample is affected.
- **`selection_result_sha256` has never been written**, so sealing it introduces no migration of
  existing values and invalidates no accepted artifact.
- **No accepted S5 or S4 statement names `selection_result_sha256`, `selection_run_id`, or
  `snapshot_id` in an `UPDATE … SET` list.** Verified across
  `sec/accession_selection_store.py` and `sec/entity_selection_store.py`: the only
  `UPDATE pilot_selection_runs SET …` statements set `run_state`, the two selected counts,
  `expanded_node_count`, `node_limit_exhausted`, `failure_reason_code`, and `finished_at_utc`.
- **No accepted S5 or S4 statement names `selection_result_sha256` in an `INSERT` column list
  either** (v0.2, for trigger 1). Both stores insert
  `(selection_run_id, snapshot_id, selection_seed, selector_policy_version, quota_policy_version,
  search_node_limit, run_state, selection_input_sha256, started_at_utc)` with
  `run_state = 'planned'`, so the column takes its `NULL` default and trigger 1's `WHEN` clause is
  false. **No accepted statement writes `pilot_manifest_versions` at all**, so trigger 4 cannot fire
  on an accepted path.
- **No accepted statement replaces, deletes, or re-identifies a run** (v0.5, for triggers 6–8). A
  repository-wide check finds no `INSERT OR REPLACE`, `REPLACE INTO`, `INSERT OR IGNORE`, or `DELETE`
  issued against `pilot_selection_runs` or `pilot_manifest_versions` anywhere in `src/`; every such
  statement in the codebase targets a different table. The accepted replay path in
  `accession_selection_store.py` **`SELECT`s the run first and reconstructs and returns when it
  exists**, inserting only when it does not, so trigger 6 is unreachable from an accepted path.
- **Migration `0013` is therefore behaviour-neutral for every accepted code path** — none of its
  **eight** triggers can fire on any statement the accepted stores issue.
- **No accepted test pins a literal manifest or result digest value.** Nothing downstream is
  invalidated by fixing these preimages now.

### 3.5 Gap 4 (added at v0.4) — `INSERT OR REPLACE` rewrites a manifest row past every guard

The focused independent governance review of v0.3 probed the replacement path directly. SQLite
resolves an `INSERT OR REPLACE` (equivalently `REPLACE INTO`) conflict by **deleting** the
conflicting row and inserting the new one. That implicit delete does **not** fire a `BEFORE DELETE`
trigger unless `PRAGMA recursive_triggers` is on, and this project never enables it —
`storage/sqlite.py` sets `foreign_keys`, `busy_timeout`, `journal_mode`, and `synchronous`, and
never `recursive_triggers`, which therefore reads `0` on every connection the repository opens.

| Probe (four v0.3 triggers applied, default pragmas) | Result |
|---|---|
| `INSERT OR REPLACE` on the `manifest_id` primary key, carrying a forged `root_manifest_sha256` | **accepted** — row rewritten |
| `INSERT OR REPLACE` conflicting on `UNIQUE (selection_run_id, snapshot_id, ordinal_version)` under a **different** `manifest_id` | **accepted** — identity swapped |
| `INSERT OR REPLACE` conflicting on the partial unique index `uq_pilot_manifest_single_active_approval`, replacing an **`owner_approved`** manifest with a different root under a different `manifest_id` and `ordinal_version` | **accepted** — an approved manifest silently displaced |
| the same three probes with `PRAGMA recursive_triggers = 1` | refused, by migration `0009`'s no-delete trigger |

Consequence: trigger 4 is a `BEFORE UPDATE` trigger, so it never runs on this path; migration
`0009`'s `pilot_manifest_hashes_immutable`, `pilot_manifest_transition_guard`, and
`pilot_manifest_versions_no_delete` are likewise bypassed. Foreign keys do not help — the replaced
row's key values are reinstated within the same statement, so no reference is ever left dangling. A
content-derived identity that a single `INSERT OR REPLACE` can overwrite is not immutable, and
**correctness must not depend on a pragma that nothing sets**. Migration `0013`'s trigger 5 (§15.1)
closes all three routes with `BEFORE INSERT` predicates that fire before conflict resolution can
delete anything.

### 3.6 Gaps 5, 6, and 7 (added at v0.5) — the selection run is replaceable, deletable, and re-identifiable

The focused independent governance review of v0.4 audited `pilot_selection_runs` directly, against a
scratch catalog carrying the accepted `0001`–`0012` chain and all five v0.4 triggers. Three findings.

**Schema facts, measured rather than asserted.** The table has **18 columns** and **two** unique
routes — the `selection_run_id` `TEXT PRIMARY KEY` and `UNIQUE (selection_run_id, snapshot_id)`;
both require a matching `selection_run_id`, so a single predicate on that column covers every
constructible replacement conflict. `idx_pilot_selection_runs_state` is non-unique and cannot drive
conflict resolution. Twelve tables hold incoming foreign keys, all `ON DELETE NO ACTION`. **Ten**
triggers exist on the table, and their events are exhaustively seven `BEFORE UPDATE OF run_state`,
one `BEFORE UPDATE OF run_state, current_attempt`, one `BEFORE UPDATE OF selection_result_sha256`,
and one `BEFORE INSERT`. **There is no `BEFORE DELETE` trigger at all**, and **no trigger names any
identity column in any `UPDATE OF` list.**

**Gap 5 — replacement clears a sealed digest.** On a `feasible`, sealed run:

| Probe (five v0.4 triggers applied) | `recursive_triggers = 0` | `= 1` |
|---|---|---|
| `INSERT OR REPLACE` omitting `selection_result_sha256` | **accepted — the seal is cleared to `NULL`** | **accepted** |

Trigger 1 cannot reach it: its `WHEN NEW.selection_result_sha256 IS NOT NULL` clause is false
precisely when the replacement omits the seal. Trigger 2 is a `BEFORE UPDATE` trigger. Foreign keys
do not help — the replacement reinstates the same key values inside the statement, verified with a
populated child table under `foreign_keys = 1`, so no reference is ever left dangling.

**Gap 6 — the run can simply be deleted.** `DELETE FROM pilot_selection_runs` on a `feasible`, sealed
run was **accepted under both `recursive_triggers` settings**, because the table has no delete guard
of any kind. This is strictly worse than the manifest case of §3.5, where migration `0009`'s
`pilot_manifest_versions_no_delete` at least closes the path when `recursive_triggers` is on.

**Gap 7 — run identity is mutable by direct `UPDATE`.** Probed per field, in a sparse shape
(`feasible`, sealed, no child rows) and a populated shape (`running`, one child row):

| Field | sparse | populated |
|---|---|---|
| `selection_run_id` | **accepted**, `foreign_keys` 1 and 0 | refused at `foreign_keys = 1` (foreign key only); **accepted** at 0 |
| `snapshot_id` | **accepted**, `foreign_keys` 1 and 0 | refused at `foreign_keys = 1` (foreign key only); **accepted** at 0 |
| `selection_input_sha256` | **accepted**, `foreign_keys` 1 and 0 | **accepted**, `foreign_keys` 1 and 0 |

The row was confirmed changed on every acceptance. `selection_input_sha256` is unguarded in every
shape under every pragma setting; the other two are protected only by foreign keys, only on a run
that already has child rows, and only while `PRAGMA foreign_keys` is on — the same
circumstance-and-pragma-dependent protection §3.2 and §3.5 already rejected. Because §6.1's preimage
reads `selection_input_sha256`, rewriting it makes a sealed digest stop recomputing from its own
row, which §11.2(3) requires: the seal survives, and silently stops meaning anything.

**`selection_input_schema_version` is not a column on this table, and needs no guard.** The 18
columns do not include it. It is **immutable by absence** — no `UPDATE` can reach it — and it enters
§6.1 and §8.4 as the accepted code-level constant `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION`
(`"pilot-joint-selection-input/1.0"`) in
[`sec/accession_selection_store.py`](../../src/disclosure_drift/sec/accession_selection_store.py).
Trigger 8 therefore names **three** columns, not four. This is recorded so that no later session
reads the three-column list as an omission.

Migration `0013`'s triggers 6, 7, and 8 (§15.1) close gaps 5, 6, and 7 respectively, and §15.5 states
the resulting guarantee.

## 4. Frozen ruling — Stage S6 scope

**Stage S6 implements deterministic manifest and terminal-result machinery only.** It delivers:

1. the eight component hashes and the root manifest hash (§7–§10);
2. `selection_result_sha256` (§6);
3. **the complete deterministic pilot-manifest document schema, and canonical JSON rendering of it,
   defined and fixture-tested here** (§13), including the **exhaustive milestone-plan §10 crosswalk**
   over all 81 atomic §10 items (§13.2.1) — Stage S9 later supplies its exact real-data instance;
4. persistence of a **`proposed`** manifest record (§11);
5. reconstruction and verification of both (§12);
6. the **eight** lifecycle, identity, replacement, and deletion guards of migration `0013` (§15), and
   the append-once and recomputability guarantee they establish (§15.5).

**Stage S6 does not authorize:** live SEC metadata execution; a real candidate snapshot; the exact
real-data manifest; owner approval; publication; projection recovery; forecasts or outcomes; a CLI
surface (§16); or any Stage S7, S8, S9, or S10 work (§17).

## 5. Frozen ruling — hashing infrastructure

Every digest in this record is computed with the existing primitives in
[`src/disclosure_drift/release/hashing.py`](../../src/disclosure_drift/release/hashing.py), reused
exactly as Decision 013 §7 requires. **No second hashing implementation, no parallel normalization,
and no alternative canonical-JSON encoder may be created.**

Two call shapes are used, both already established by the accepted S5 code:

- **Multi-row family digest** —
  `hash_table(<table_name>, <frozen column tuple>, <rows>).normalized_content_sha256`.
  `hash_table` binds the table name and the **declared column order**, renders each cell through
  `normalize_value`, and **sorts the rendered rows before digesting**, so SQLite retrieval order can
  never affect a result and row order need not be controlled by the caller. The column tuple's order
  is itself normative: reordering it changes the digest.
- **Single-row combination or scalar-field digest** —
  `hash_table(<name>, tuple(sorted(fields)), [fields]).normalized_content_sha256` over a mapping of
  named scalar fields. This is the shape
  `build_joint_selection_run_identity`, `_package_id`, and `_entity_content_sha256` already use.

`normalize_value`'s `NULL_SENTINEL` distinguishes SQL `NULL` from the empty string, so a nullable
column carries meaning rather than collapsing. Booleans render as `1`/`0`; integers as decimal text.
Naive datetimes are refused outright.

**Decision 016 §8's exclusions apply to every digest below without exception:** absolute local paths;
SEC identity (user-agent, contact address); secrets; any outcome value; any filing text; every
free-text `detail` column; every operational event ID; and **every timestamp column**. Where a
frozen column tuple below omits `recorded_at_utc`, `generated_at_utc`, `retrieved_at_utc`,
`applied_at_utc`, `started_at_utc`, `finished_at_utc`, `frozen_at_utc`, `created_at_utc`,
`invalidated_at_utc`, `approved_at_utc`, `rejected_at_utc`, `superseded_at_utc`, or `detail`, that
omission is normative, not incidental.

## 6. Frozen ruling — `selection_result_sha256`

**`selection_result_sha256` is populated at Stage S6**, under the existing
`PILOT_MANIFEST_HASH_POLICY_VERSION = "pilot-manifest/1.0"` policy. No new policy constant and no
policy-reference migration is created: that constant already exists in
[`pilot_policy.py`](../../src/disclosure_drift/pilot_policy.py) and its `pilot_manifest_hash` row is
already seeded in `reference_policy_versions` by migration `0009`.

### 6.1 Canonical preimage — frozen

A single-row `hash_table` digest named `pilot_selection_result` over exactly these fourteen fields,
sorted by key:

| Field | Source |
|---|---|
| `manifest_hash_policy_version` | `PILOT_MANIFEST_HASH_POLICY_VERSION` (`"pilot-manifest/1.0"`) |
| `selection_run_id` | `pilot_selection_runs.selection_run_id` |
| `snapshot_id` | `pilot_selection_runs.snapshot_id` |
| `selection_input_sha256` | `pilot_selection_runs.selection_input_sha256` |
| `selection_input_schema_version` | `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` (`"pilot-joint-selection-input/1.0"`) |
| `run_state` | the **literal constant** `"feasible"` (§6.2) |
| `selected_entity_count` | `pilot_selection_runs.selected_entity_count` |
| `selected_accession_count` | `pilot_selection_runs.selected_accession_count` |
| `expanded_node_count` | `pilot_selection_runs.expanded_node_count` |
| `node_limit_exhausted` | `pilot_selection_runs.node_limit_exhausted` |
| `selected_entities_sha256` | §7.1 |
| `selected_accessions_sha256` | §7.2 |
| `quota_report_sha256` | §7.3 |
| `reserves_sha256` | §7.4 |

### 6.2 Rulings these fields freeze

- **`run_state` is a fixed literal, not a read value.** The digest is defined only for a `feasible`
  run; the implementation asserts `run_state = 'feasible'` and fails closed with `GateFailureError`
  otherwise, then contributes the constant. A non-`feasible` run therefore has no result digest at
  all, rather than a differently-valued one.
- **`node_limit_exhausted` is always `0` on a feasible run** — migration `0009`'s
  `CHECK (node_limit_exhausted = 0 OR run_state = 'infeasible_or_unproven')` forces it. It is
  retained in the preimage as a deliberate, defensive constant so that a corrupted flag on a
  `feasible` row cannot pass unnoticed.
- **`search_node_limit`, `selection_seed`, and both selector policy versions are not listed
  directly** because they are already bound, exactly and without duplication, through
  `selection_input_sha256`. Nothing is left unbound by their absence.

### 6.3 Excluded from the preimage — frozen

`selection_result_sha256` itself (§9); every timestamp; `detail`; every `pilot_selection_run_events`
row and every lifecycle event ID; every path; every manifest approval field
(`manifest_state`, `approval_reference`, `approved_root_sha256`, `approved_at_utc`,
`rejected_at_utc`, `superseded_at_utc`); and every operational attempt value (`current_attempt`,
`failure_reason_code`).

## 7. Frozen ruling — terminal component boundaries

Four component digests are computed from the persisted terminal rows of one `feasible` S5 joint run.
Each column tuple below is **frozen in the order shown**. `recorded_at_utc` and `detail` are excluded
from every family.

### 7.1 `selected_entities_sha256`

`hash_table("pilot_selected_entities", COLUMNS, rows)` over every row of that table for the run,
with

```
("selection_run_id", "snapshot_id", "cik_numeric", "selected_order", "entity_hash_sha256",
 "entity_role", "candidate_category", "size_stratum", "industry_family", "history_class",
 "control_kind")
```

`selected_order` is a materialized hashed column, per Decision 016 §8.

### 7.2 `selected_accessions_sha256`

`hash_table("pilot_selected_accessions", COLUMNS, rows)`, with

```
("selection_run_id", "snapshot_id", "accession_plain", "anchor_cik_numeric", "selected_order",
 "accession_hash_sha256", "accession_role")
```

### 7.3 `quota_report_sha256`

Four sub-digests, combined by a single-row `hash_table` named `pilot_quota_report` over the mapping
`{"quota_results": …, "entity_contributions": …, "accession_contributions": …, "quota_members": …}`.

| Sub-digest | `hash_table` name | Frozen column tuple |
|---|---|---|
| `quota_results` | `pilot_quota_results` | `("quota_result_id", "selection_run_id", "snapshot_id", "quota_dimension", "quota_key", "comparison_operator", "required_count", "achieved_count", "eligible_pool_count", "excluded_pool_count", "evidence_state", "quota_result", "binding_constraint", "binding_evidence_sha256")` |
| `entity_contributions` | `pilot_selected_entity_quota_contributions` | `("selection_run_id", "snapshot_id", "cik_numeric", "quota_dimension", "quota_key")` |
| `accession_contributions` | `pilot_selected_accession_quota_contributions` | `("selection_run_id", "snapshot_id", "accession_plain", "quota_dimension", "quota_key")` |
| `quota_members` | `pilot_quota_result_members` | `("quota_result_id", "selection_run_id", "snapshot_id", "member_order", "member_kind", "cik_numeric", "accession_plain")` |

`binding_evidence_sha256`, `cik_numeric`, and `accession_plain` are nullable; `NULL_SENTINEL`
distinguishes a null from any stored value, so no null collapses into an empty string.

### 7.4 `reserves_sha256`

Four sub-digests, combined by a single-row `hash_table` named `pilot_reserve_report` over the mapping
`{"reserves": …, "reserve_accessions": …, "reserve_contributions": …, "reserve_dispositions": …}`.

| Sub-digest | `hash_table` name | Frozen column tuple |
|---|---|---|
| `reserves` | `pilot_reserves` | `("reserve_package_id", "selection_run_id", "snapshot_id", "target_cik_numeric", "replacement_cik_numeric", "reserve_rank", "replaces_signature_sha256", "reserve_signature_sha256", "signature_policy_version", "quota_policy_version", "reserve_tie_break_sha256", "evidence_floor")` |
| `reserve_accessions` | `pilot_reserve_accessions` | `("reserve_package_id", "selection_run_id", "snapshot_id", "accession_plain", "accession_role", "accession_order", "accession_hash_sha256")` |
| `reserve_contributions` | `pilot_reserve_quota_contributions` | `("reserve_package_id", "selection_run_id", "snapshot_id", "quota_dimension", "quota_key")` |
| `reserve_dispositions` | `pilot_selection_entity_reasons` | `("selection_run_id", "snapshot_id", "cik_numeric", "reason_scope", "reason_code")` |

Two rulings this freezes:

- **Reserve child rows are hashed directly**, even though `reserve_package_id` already binds them
  through its own content-derived preimage (Decision 020 §9). The redundancy is deliberate: it
  localizes a corruption to the child family that carries it, and it means `reserves_sha256` remains
  correct even if a package identity were ever recomputed under a different rule. It introduces no
  second derivation, because the child rows are read as persisted and no reserve methodology is
  re-implemented.
- **The migration-`0012` dispositions are inside `reserves_sha256`.** Decision 020 §7.1 makes each
  selected entity's reserve position total and mutually exclusive — exactly one rank-1 package or
  exactly one `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` row. Binding only the packages would leave "which
  targets have no reserve" as an inference rather than an approved fact. It is bound explicitly.

## 8. Frozen ruling — the remaining four component preimages

### 8.1 `source_observation_set_sha256`

The **cited observation set** for a snapshot is the distinct union of `source_observation_id` over
`pilot_candidate_entity_evidence` and `pilot_candidate_accession_evidence` scoped to that
`snapshot_id`. It is derived from persisted evidence rows, never supplied by a caller.

For each cited observation, the row contributed is exactly Decision 016 §8's **source-content hash**
input list, and nothing else:

`hash_table("census_source_observation_content", COLUMNS, rows)`, with

```
("source_id", "request_identity", "logical_sha256", "parser_version",
 "schema_fingerprint_sha256", "outcome")
```

#### The structural fingerprint — frozen partition rule (owner correction D, v0.2; **five-column tuple frozen at v0.3**)

`schema_fingerprint_sha256` is a stable identifier for the structural shape the parser observed, so
that a schema-drift event changes the fingerprint (Decision 016 §8). `census_structural_observations`
carries `UNIQUE (source_observation_id, parser_run_id, region, member_name)`, so **one source
observation may legitimately carry rows from several parser runs**, and `hash_table` does not
deduplicate rendered rows. A naive "hash that observation's rows" rule would therefore let an
*identical reparse* change the fingerprint — and with it `source_observation_set_sha256` and the root
— purely by adding duplicate rows.

**The frozen tuple is exactly these five columns, in this order:**

```
("region", "state", "observed_type", "member_name", "record_path")
```

**This is the only structural-fingerprint tuple.** The v0.2 three-column form
`("region", "state", "member_name")` is **withdrawn**: it must not appear in the migration, in a
module, in a test, or in any status file, and **no three-column fallback and no second fingerprint
methodology may exist** (§20, §21). All five columns are substantive structural facts, and §19.8
records what the rule does and does not exclude.

The following rule is frozen:

1. **Partition** that source observation's `census_structural_observations` rows **by
   `parser_run_id`**.
2. **Normalize every value** under the existing canonical normalization rules — `normalize_value`
   from [`release/hashing.py`](../../src/disclosure_drift/release/hashing.py), unchanged and not
   reimplemented (§5). `member_name` and `record_path` are nullable, so `NULL_SENTINEL` keeps a SQL
   `NULL` distinct from the empty string in both the set comparison and the digest.
3. **Reduce each parser run** to the **distinct set of normalized five-column tuples**. Reduction to
   a set is what makes a duplicate identical row and any retrieval ordering a no-op.
4. **Require every parser run's set for that source observation to be exactly equal.**
5. **Raise `GateFailureError` when they differ.** A disagreement between two parser runs is a genuine
   structural divergence, not a rendering artifact. It is **never** unioned, intersected, averaged,
   majority-voted, resolved by preferring a parser run, or silently discarded.
6. **Hash the common distinct set exactly once**, with the existing primitive:
   `hash_table("census_structural_observation_shape", ("region", "state", "observed_type", "member_name", "record_path"), rows)`.
   `hash_table` sorts rendered rows before digesting, so set order need not be controlled by the
   caller; the **column order above is normative**, and reordering it changes the digest.
7. **`parser_run_id` is excluded from the digest.** It is the partition key for the consistency check
   in steps 1, 4, and 5 — *how many times* and *under which run* the shape was observed is
   operational; *what* shape was observed is content.

Four properties this guarantees, each of which §20 requires a test for:

- **An identical reparse is a digest no-op.** A second `parser_run_id` producing the same five-column
  set leaves the fingerprint, `source_observation_set_sha256`, and the root byte-identical.
- **A duplicate identical row is a digest no-op**, by step 3. (Within one parser run the table's
  `UNIQUE (source_observation_id, parser_run_id, region, member_name)` already prevents most such
  duplicates; step 3 makes the property hold regardless of that constraint rather than depending on
  it.)
- **Parser-run order and row order are irrelevant** — step 3 reduces to a set and step 6's
  `hash_table` sorts.
- **Each of the five fields is load-bearing:** changing `region`, `state`, `member_name`,
  `observed_type`, or `record_path` on any row changes the set, therefore the fingerprint, therefore
  `source_observation_set_sha256`, therefore `root_manifest_sha256`.

An observation with no structural rows contributes the digest of the empty row set — deterministic,
and distinct from any populated shape.

**The v0.3 widening also strengthens step 4.** Under the withdrawn v0.2 form, two parser runs
agreeing on the first three columns but disagreeing on `observed_type` or `record_path` would have
compared equal and been silently accepted. Under the frozen five-column form they compare unequal and
fail closed. The wider tuple therefore both binds more and detects more; it costs nothing, because
the two added columns were already being read.

#### Complete column classification — `census_source_observations` (owner correction E, v0.2)

All 34 columns are classified; none is left to inference, and none is classified only by the
"and nothing else" closure above.

| Disposition | Columns |
|---|---|
| **Hashed** (6, incl. the derived fingerprint) | `source_id`, `request_identity`, `logical_sha256`, `parser_version`, `outcome`, `schema_fingerprint_sha256` (derived) |
| Excluded — per-retrieval identity | `observation_id` (two retrievals of identical content under the same request identity must hash identically), `supersedes_observation_id`, `reused_observation_id`, `attempts` |
| Excluded — timestamps | `retrieved_at_utc` (Decision 016 §8 corrects the S3 review specifically here), `recorded_at_utc` |
| Excluded — URL and redirect trace | `requested_url`, `final_url`, `redirects_json`, `redirect_hops_json` |
| Excluded — headers and validators | `etag`, `last_modified`, `validators_sent_json`, `headers_json` |
| Excluded — transport and storage digests, sizes, representation, path | `transport_sha256`, `stored_sha256`, `content_sha256`, `transport_size_bytes`, `content_size_bytes`, `stored_size_bytes`, `storage_representation`, `relative_storage_path` |
| Excluded — free text and operational flags | `detail`, `projected_to_audit` |
| **Excluded — the six residuals named explicitly by owner correction E** | `purpose`, `http_status`, `declared_content_type`, `observed_content_kind`, `content_encoding` (the sixth, `reference_policy_versions.decision_record`, is in §8.4) |

Rationale for the five residuals on this table, recorded so no implementation session has to infer
it and none may re-open it:

- **`purpose`** — a retrieval-intent routing label. Two retrievals of byte-identical content under
  the same request identity are the same content whatever the declared purpose was.
- **`http_status`** — transport-layer response metadata whose content-relevant consequence is
  already carried, in normalized form, by `outcome`.
- **`declared_content_type`** — a server-declared header value, and headers are excluded as a class.
- **`observed_content_kind`** — a parser-side transport classification, superseded for content
  purposes by `parser_version` together with the schema fingerprint.
- **`content_encoding`** — transport encoding, not logical content; `logical_sha256` is by
  definition the *decoded* content digest, so encoding cannot change it.

#### Complete column classification — `census_structural_observations` (owner correction E, v0.2)

| Disposition | Columns |
|---|---|
| **Hashed** (5, frozen at v0.3) | `region`, `state`, `observed_type`, `member_name`, `record_path` |
| Excluded — partition key, **used but not hashed** | `parser_run_id` (rule steps 1, 4, 5, and 7 above) |
| Excluded — per-row identity and parent pointer | `structural_observation_id`, `source_observation_id` (the parent is the scoping key, not content) |
| Excluded — counts and count-quality flags | `row_count`, `count_is_trustworthy`, `is_genuine_zero` (volume, not shape) |
| Excluded — free text and timestamps | `reason_codes_json`, `detail`, `raw_excerpt`, `recorded_at_utc` |

**Every substantive structural field is now bound.** The v0.2 classification excluded `observed_type`
and `record_path` as "finer shape detail"; owner correction D at v0.3 rules that they are structural
content, not detail, and moves them into the hashed tuple. See §19.8.

### 8.2 `candidate_tables_sha256`

A single-row `hash_table` named `pilot_candidate_tables` over the frozen snapshot's own identity,
policy versions, declared content digests, and counts:

```
snapshot_id, snapshot_state, coverage_start, coverage_end, as_of_date, include_open_quarter,
coverage_policy_version, candidate_policy_version, sic_family_mapping_version,
evidence_policy_version, coverage_window_sha256, input_observation_set_sha256,
candidate_entity_table_sha256, candidate_accession_table_sha256,
candidate_registrant_table_sha256, candidate_entity_evidence_sha256,
candidate_accession_evidence_sha256, candidate_entity_reasons_sha256,
candidate_accession_reasons_sha256, candidate_snapshot_sha256, entity_count, accession_count
```

Rulings this freezes:

- **`snapshot_state` is the fixed literal `"frozen"`.** As with `run_state` in §6.2, the
  implementation asserts the snapshot is `frozen` and fails closed otherwise, then contributes the
  constant. A later invalidation is a fact about the snapshot's *disposition* (Decision 016 §5) and
  must not retroactively change a manifest's candidate digest.
- **`census_run_id` is excluded**, exactly as Decision 016 §1 excludes it from `snapshot_id`: two
  snapshots built from the same observations under the same policy versions are the same snapshot.
- **The snapshot's declared component digests are the accepted representation of the candidate
  tables, and are bound as such rather than recomputed here.** Recomputing them would be a second
  implementation of a snapshot-freeze derivation that does not yet exist (Decision 018 §19 prohibits
  a second methodological implementation). The candidate *row content* is independently bound
  through `selection_input_sha256`, which S5.2 derives from the actual frozen rows and which Stage S6
  re-derives during reconstruction (§12) — so the row content is proven, not trusted, by a path that
  already exists.
- Excluded: `invalidated_reason_code`, `created_at_utc`, `frozen_at_utc`, `invalidated_at_utc`,
  `detail`.

### 8.3 `quota_definitions_sha256`

Decision 013 §7 makes the quota-*definition* hash (layer 3) and the quota-*report* hash (layer 8)
distinct layers, so a manifest binds what was **required** independently of what was **achieved**.

A single-row `hash_table` named `pilot_quota_definitions` over:

| Field | Source |
|---|---|
| `quota_policy_version` | `PILOT_QUOTA_POLICY_VERSION` (`"m23-pilot-quota-policy-v1"`), cross-checked against the run's recorded `quota_policy_version` |
| `quota_definitions_content_sha256` | `hash_table("pilot_quota_definition_rows", ("quota_dimension", "quota_key", "comparison_operator", "required_count"), rows)` over `pilot_quota_results` for the run |

**Excluded, normatively:** `quota_result_id`, `achieved_count`, `eligible_pool_count`,
`excluded_pool_count`, `evidence_state`, `quota_result`, `binding_constraint`,
`binding_evidence_sha256`, `recorded_at_utc`, `detail` — every one of which is an outcome of the
solve, not a definition, and every one of which is already bound by `quota_report_sha256` (§7.3).

### 8.4 `selector_policy_sha256`

A single-row `hash_table` named `pilot_selector_policy`. **Owner correction C (v0.2) extends this
layer from the original five categories to eleven fields**, because correction C also requires the
manifest *document* to carry the environment, authority, and source-plan identity that milestone plan
§10 specifies, and §13.3 forbids any substantive serialized field that no digest commits. This layer
is where that identity belongs: it is the manifest's "policy and environment identity" layer. Nothing
already frozen at v0.1 is removed or reinterpreted; five fields are added.

| Field | Source | New at v0.2 |
|---|---|---|
| `policy_versions_sha256` | `hash_table("reference_policy_versions_content", ("policy_key", "policy_version"), rows)` over the nine consumed keys below | |
| `selection_input_schema_version` | `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` | |
| `manifest_schema_version` | `PILOT_MANIFEST_HASH_POLICY_VERSION` | |
| `migration_chain_sha256` | `hash_table("ops_schema_migrations_content", ("version", "name", "checksum_sha256"), rows)` over every applied migration | |
| `dependency_lock_sha256` | **required explicit argument** | |
| `code_commit_identifier` | **required explicit argument** | |
| `runtime_python_version` | **required explicit argument** — milestone plan §10 "Python version" | ✔ |
| `configuration_sha256` | **required explicit argument** — milestone plan §10 "configuration hash" | ✔ |
| `decision_authority_sha256` | **required explicit argument** — milestone plan §10 "active decision-record hashes": a digest over the enumerated `(decision record identifier, content sha256)` pairs the caller asserts were in force | ✔ |
| `source_plan_sha256` | **required explicit argument** — milestone plan §10 "source-plan hash". It is a caller-supplied assertion and **not** read from the catalog, because no plan hash is persisted: `IndexPlan.plan_hash()` is computed in memory and no migration stores it | ✔ |
| `leakage_attestation` | the **fixed literal** `"no-outcome-no-filing-text-no-companyfacts/1.0"` (§13.2 block 12, §8.4.1) | ✔ |

The nine consumed policy keys, frozen: `pilot_candidate`, `pilot_evidence`,
`pilot_sic_family_mapping`, `pilot_selector`, `pilot_joint_selector`, `pilot_quota`,
`pilot_replacement_signature`, `pilot_manifest_hash`, `pilot_primary_universe_boundary`. Each value
is read from `reference_policy_versions` and must equal the corresponding `pilot_policy.py` constant;
a disagreement is a `GateFailureError`, never a value the manifest silently prefers.
**`reference_policy_versions.decision_record` is excluded** (owner correction E, v0.2, the sixth
residual): it is a repository-relative documentation pointer, not a policy value. The binding fact is
the `(policy_key, policy_version)` pair; where that pair is *written down* is navigation, and
navigation is never an authority (CLAUDE.md). `recorded_at_utc` is excluded as a timestamp, so all
four columns of that table are now classified.

**All six explicit arguments are frozen inputs supplied by the caller.** The implementation **must
not** invoke Git, read `.git`, shell out, consult environment variables, read `sys.version`, inspect
the working tree, or otherwise infer build, runtime, configuration, authority, or plan identity. A
missing or malformed value is a `GateFailureError`. This keeps every one of them an auditable,
deliberately-supplied assertion rather than a property of whatever tree, interpreter, or shell
happened to be present. `applied_at_utc` is excluded from `migration_chain_sha256`, like every other
timestamp.

**This layer is accepted and unchanged at v0.3 and again at v0.4.** The eleven-field expansion stands
exactly as v0.2 froze it: the pilot-manifest document carries substantive environment, authority,
source-plan, migration-chain, dependency-lock, code-identity, policy-version, and schema-version
values, and §13.3 requires every one of them to be committed — directly or transitively — by
`selector_policy_sha256` and therefore by `root_manifest_sha256`. Shrinking this layer would leave
those document fields unbound and violate §13.3.

**Correction A relies on this layer and does not change it (v0.4).** Two §13.2.1 items are committed
here and nowhere else: item 14, the as-of **time zone**, and item 58, the **after-hours state**. Both
are values fixed by [Decision 010](decision_010_temporal_availability_and_cohort_assignment.md) §5.2
— the EDGAR operating calendar's `America/New_York` zone and its 17:30 cutoff — rather than by any
persisted column. `decision_authority_sha256` binds the enumerated
`(decision record identifier, content sha256)` pairs, so **Decision 010's ruling cannot change
without changing `selector_policy_sha256` and the root.** That is what "active decision-record
hashes" is for, and it is why the exhaustive crosswalk needed no new preimage field.

The v0.1 review examined a five-category form of this layer and the v0.3 review examined a different
`schema_fingerprint_sha256`; §23 records why **no earlier conclusion carries forward to v0.5** for
this layer, for §8.1, for the §13 document contract, or for the §15 statement region.

### 8.4.1 `leakage_attestation` — what the constant does and does not claim

The literal commits **which** attestation was made, so it cannot be silently changed later without
changing `selector_policy_sha256` and the root. It does **not** by itself make the attestation true.
Its truth is a property of the code path and is enforced where such things are enforceable: Stage S6
reads only the tables enumerated in §§6–8, and §20 requires a test asserting that no S6 module opens
any outcome, filing-text, or CompanyFacts source. CLAUDE.md rule 4, Decision 015, and
`Docs/leakage_register.md` L15 and L19 continue to govern; this field records the claim in the
artifact, it does not replace the controls.

## 9. Frozen ruling — the root manifest hash

`root_manifest_sha256` is a single-row `hash_table` named `pilot_root_manifest` over exactly these
twelve fields, sorted by key:

```
manifest_schema_version, selection_run_id, snapshot_id, selection_result_sha256,
source_observation_set_sha256, candidate_tables_sha256, quota_definitions_sha256,
selector_policy_sha256, selected_entities_sha256, selected_accessions_sha256,
reserves_sha256, quota_report_sha256
```

**Excluded, normatively:** `ordinal_version`; `manifest_state`; `approval_reference`;
`approved_root_sha256`; `approved_at_utc`; `rejected_at_utc`; `superseded_at_utc`;
`supersedes_manifest_id`; `relative_manifest_path`; `generated_at_utc`; `detail`; `manifest_id`; and
every event ID.

**`approved_root_sha256` is a direct byte copy of `root_manifest_sha256`, recorded at a later owner
approval. It is never a second hash, never a hash of the root, and never computed by S6 code** —
migration `0009` already enforces the equality with
`CHECK (manifest_state NOT IN ('owner_approved','superseded') OR approved_root_sha256 = root_manifest_sha256)`.

### 9.1 `manifest_id` — derivation, confirmed at independent review

Decision 016 §1 requires `manifest_id` to be a content-derived 64-hex SHA-256. The derivation is a
single-row `hash_table` named `pilot_manifest_identity` over exactly
`{"root_manifest_sha256", "ordinal_version", "supersedes_manifest_id"}`, with `NULL_SENTINEL` for an
absent predecessor.

This keeps `manifest_id` content-derived, keeps it out of `root_manifest_sha256` (so no cycle
forms), and lets two ordinal versions over one run be distinct rows even when their root content
matches. It was the one point in v0.1 derived rather than directly ruled, and it was flagged for
confirmation at independent governance review. **That review confirmed it, and the project owner
ruled it unchanged at v0.2** — the derivation is preserved exactly. Manifest state, approval fields,
timestamps, relative paths, and every operational field stay out of it.

### 9.2 Manifest identity is immutable after insertion (owner correction A, v0.2)

**Six fields are immutable from the moment a `pilot_manifest_versions` row exists:**

| Field | Why it must not move |
|---|---|
| `manifest_id` | the content-derived identity itself (Decision 016 §1); an editable content-derived ID is not one |
| `manifest_schema_version` | a `root_manifest_sha256` preimage input (§9); the root is already immutable, so a mutable copy on the row can only ever create disagreement |
| `selection_run_id` | a `root_manifest_sha256` preimage input, and the run the manifest speaks for |
| `snapshot_id` | a `root_manifest_sha256` preimage input, and the frozen snapshot the run consumed |
| `ordinal_version` | a `manifest_id` preimage input (§9.1) |
| `supersedes_manifest_id` | a `manifest_id` preimage input (§9.1) |

**Enforced twice.** In application code, by the S6 store, which never issues an `UPDATE` naming any
of the six. In the schema, for the first time, by migration `0013` trigger 4 (§15.1), which holds all
six with NULL-safe `IS NOT` comparisons and additionally re-checks the referenced run on both the OLD
and the NEW side. §3.3 records why the policy-only form was insufficient.

**Consequence, frozen: a successor manifest declares its predecessor at `INSERT`, never by a later
`UPDATE`.** Because `supersedes_manifest_id` feeds `manifest_id`, the predecessor must be known when
the ID is fixed — exactly as migration `0009` already requires `input_observation_set_sha256` to be
known at snapshot `INSERT` because `snapshot_id` depends on it. Migration `0009`'s
`pilot_manifest_supersession_requires_successor` trigger is unaffected: it asks only that, at the
moment of supersession, some other row already references this one, and an insert-time declaration
satisfies that. **None of this is Stage-S6 work** — S6 creates only a first `proposed` manifest and
is forbidden to populate `supersedes_manifest_id` at all (§11.1).

**What stays mutable, deliberately.** `manifest_state` and the approval fields move under migration
`0009`'s existing transition guard; `relative_manifest_path` and `detail` are operational, excluded
from every digest (§9, §13.4), and may be corrected without touching identity. `generated_at_utc` is
a timestamp and is excluded everywhere.

## 10. Frozen ruling — circularity exclusions

The digest graph is a **directed acyclic graph**, and no digest is ever an input to itself, directly
or transitively:

```
source observations ─┐
candidate snapshot  ─┤
quota definitions   ─┼─────────────────────────────────────┐
selector policy     ─┘                                     │
                                                           ▼
selected_entities ─┐                                root_manifest_sha256 ──▶ manifest_id
selected_accessions ┼──▶ selection_result_sha256 ──▶      │                       │
quota_report       ─┤            │                        │                       ▼
reserves           ─┘            └────────────────────────┘            approved_root_sha256
                                  (also feed the root directly)          (later owner copy)
```

Eight exclusions are frozen:

1. **`selection_result_sha256` is excluded from its own preimage** (§6.3).
2. **No component digest reads `pilot_selection_runs` as a table.** The four terminal components
   (§7) read only their own result tables; the six named scalar run fields enter `selection_result_sha256`
   individually (§6.1). A table-level digest of `pilot_selection_runs` would contain
   `selection_result_sha256` and is therefore prohibited outright.
3. **`root_manifest_sha256` is excluded from every component and from `selection_result_sha256`.**
4. **`pilot_manifest_versions` is never hashed into any digest.** A manifest never hashes itself.
5. **`pilot_projection_recovery_events` is never hashed into any digest** — it is operational, and
   S6 writes it not at all (§16).
6. **`manifest_id` is excluded from `root_manifest_sha256`** and is derived from it (§9.1), never the
   reverse.
7. **`approved_root_sha256` is a copy, not a hash** (§9).
8. **The four terminal component digests deliberately appear at two layers** — inside
   `selection_result_sha256` and again inside `root_manifest_sha256`. This is a **diamond, not a
   cycle**: both consumers are downstream of the four producers, and neither producer reads either
   consumer. It is retained because it makes the root bind the terminal content directly, so a root
   remains verifiable even if the result-digest layer were ever re-examined.

**No proposal in this record hashes a digest into itself.**

### 10.1 Commitment closure (v0.2)

Owner correction C requires that no substantive serialized field be left unbound. Stating precisely
what commits what, because the two commitments are not the same set:

- **`root_manifest_sha256` commits every substantive value in the document** — all nine hash layers,
  the terminal result, the run and snapshot identity, the schema version, and, transitively through
  the eight components, every source observation, candidate-snapshot declaration, quota definition,
  policy and environment identity, selected entity and accession, contribution, member, reserve, and
  disposition that the document serializes (§13.3).
- **`manifest_id` commits the root plus the two version-ordering fields** — `ordinal_version` and
  `supersedes_manifest_id` (§9.1). Those two are manifest-*version* metadata, not manifest *content*:
  they order successive manifests over one run, they do not describe the pilot sample. They are
  deliberately outside the root, because putting them inside it would make two ordinal versions of
  identical content produce different roots — defeating the point of a content-addressed root.
- **`manifest_id` is therefore the total commitment over the whole document**, and the root is the
  total commitment over its substantive content. Both are recorded; §13.3 states the completeness
  obligation in terms of both. The relation stays acyclic: root → `manifest_id`, never the reverse.

## 11. Frozen ruling — manifest lifecycle, eligibility, and transactions

### 11.1 Proposed-only boundary

**S6 code may create a manifest only in `manifest_state = 'proposed'`.** It must not:

- transition a manifest to `owner_approved`;
- populate `approval_reference`, `approved_root_sha256`, or `approved_at_utc`;
- supersede or reject any manifest, or populate `supersedes_manifest_id` at all — at S6 it is always
  the canonical `NULL`, so §9.1's `NULL_SENTINEL` branch is the only one S6 exercises (§9.2);
- issue any `UPDATE` naming one of the six immutable identity columns (§9.2), including an identical
  restatement that migration `0013` would tolerate;
- publish any artifact;
- create a real-data manifest instance.

The `proposed → owner_approved` transition is an **owner act outside the S6 implementation
contract** and outside this record's authorization. Decision 013 §8's requirement — that M2.3
completion is owner approval of the exact final manifest hash — is unchanged and is satisfied at
Stage S10 (§17), not here.

### 11.2 Eligibility — application code must fail closed unless all of

1. the referenced `pilot_selection_runs` row **exists**;
2. its `run_state` is **`feasible`**;
3. its `selection_result_sha256` is **non-`NULL` and independently recomputes** from §6.1;
4. the run uses the accepted S5 joint-selection input schema —
   `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION == "pilot-joint-selection-input/1.0"` — and its recorded
   selector and quota policy versions equal the accepted constants;
5. the run's `snapshot_id` and the manifest's `snapshot_id` **agree**, and the snapshot is `frozen`;
6. the run is **not the Stage-S4 entity-only draft** (§14);
7. **every manifest component hash independently recomputes** from persisted rows (§7–§9).

Each failure raises `GateFailureError`, writes nothing, and leaves no partial state. None may be
worked around, relaxed, or resolved by dropping rows (CLAUDE.md rule 12).

`REVIEW_PILOT_NO_COMPATIBLE_RESERVE` **remains nonblocking** — it is registered in `reasons.py` with
`blocks_release=False, requires_manual_review=True` (Decision 020 §13). A run carrying
no-compatible-reserve dispositions is manifest-eligible; its dispositions are bound into
`reserves_sha256` (§7.4) so the owner sees them in the artifact they later approve.

### 11.3 Transactions and concurrency

- **One explicit transaction per manifest write.** The `pilot_manifest_versions` row and the
  serialized JSON file commit together or not at all; a partial manifest never exists.
- **Sealing `selection_result_sha256` happens in its own transaction, before the manifest write**,
  and is idempotent by content: the implementation recomputes, compares, and either writes the seal,
  accepts an identical existing seal, or fails closed on a differing one. It never overwrites.
- **This does not weaken accepted terminal-row immutability.** Every result row family
  (`pilot_selected_*`, `pilot_quota_*`, `pilot_reserve*`, `pilot_selection_entity_reasons`) stays
  untouched and stays sealed by migration `0009`'s and `0012`'s `running`-window guards. Only
  `pilot_selection_runs.selection_result_sha256` — a column no accepted statement writes, and which
  migration `0013` makes append-once — changes.
- **No new run state and no new run transition is created.** `feasible` remains terminal; manifest
  state lives on `pilot_manifest_versions` and is unchanged from Decision 016 §5.
- **Repeated execution is safe.** An identical re-run recomputes the same seal and the same root; a
  second `proposed` manifest for the same run is refused by the implementation unless the owner has
  authorized a new `ordinal_version`, and migration `0009`'s
  `UNIQUE (selection_run_id, snapshot_id, ordinal_version)` plus
  `uq_pilot_manifest_single_active_approval` bound the rest.
- **Idempotent replay reads, reconstructs, compares, and returns — it never replaces (v0.4).** When a
  manifest already exists for the run, snapshot, and ordinal version, the implementation **reads the
  persisted row, re-derives the document and every digest from persisted state (§12), compares, and
  returns the existing manifest unchanged**. It writes nothing. A mismatch is a `GateFailureError`,
  never a rewrite.
- **`INSERT OR REPLACE` is prohibited against `pilot_manifest_versions` and `pilot_selection_runs`,
  without exception (v0.4; extended to the run table at v0.5).** So is `REPLACE INTO`, and so is any
  other conflict-resolution clause that could delete a row — `INSERT OR IGNORE` included, because
  silently doing nothing is as wrong as silently overwriting. **`DELETE` against either table is
  prohibited outright**, and **no `UPDATE` may name `selection_run_id`, `snapshot_id`, or
  `selection_input_sha256`.** The S6 store issues plain `INSERT` and plain `UPDATE` only. Migration
  `0013`'s triggers 5, 6, 7, and 8 (§15.1) enforce all of this at the schema layer so no part of it
  rests on code review; §3.5 and §3.6 record why the schema-layer form was necessary, and §15.5
  states the resulting guarantee.

## 12. Frozen ruling — reconstruction and replay

- **Nothing stored is trusted that was not re-derived.** Manifest verification re-derives the S5 run
  through the accepted `reconstruct_persisted_joint_selection` entry point, recomputes all eight
  component digests, the result digest, and the root from persisted rows, and compares. Any
  difference is a `GateFailureError`.
- **S6 owns its own verification.** The accepted S5.2 reconstruction path does not read
  `selection_result_sha256`, and `JointSelectionRunIdentity` has no such field, so a sealed digest is
  invisible to it. **`accession_selection_store.py` is not modified to close that gap** — it is a
  closed, accepted stage. S6 supplies a public verification entry point instead, and its tests prove
  that a corrupted seal, a corrupted component, and a corrupted root each fail closed.
- **Same-ID replay is unaffected and remains safe.** `execute_and_persist_joint_selection` on an
  existing terminal run reconstructs and returns without writing, and its `UPDATE` statements never
  name `selection_result_sha256`, so a replay after sealing neither clears nor mutates the digest
  (§3.4). It also does not verify it — which is exactly why S6's verification path is required rather
  than optional.
- **Historical reconstruction proves the terminal digest** by re-deriving the pure result from the
  frozen snapshot under the run's own recorded seed, policy versions, and node limit, recomputing the
  four terminal component digests from the validated rows, recomputing §6.1, and comparing to the
  stored seal.
- **The document is verified as well as the row** (v0.2). Verification re-renders the §13.2 document
  from persisted rows and the recorded explicit arguments, recomputes `root_manifest_sha256` from its
  substantive content and `manifest_id` from §9.1, and compares both to the stored row. A document
  that does not reproduce its own root, a root that does not reproduce its own `manifest_id`, or a
  rendered value that disagrees with the row it came from is a `GateFailureError`.
- **Verification is item-by-item over the §13.2.1 crosswalk (v0.4).** For every one of the 81 atomic
  §10 items classified **D** or **T**, verification re-reads the value from its recorded
  reconstruction source and compares it to the rendered document, and confirms the covering digest
  recomputes. This is the "document → row" half of §13.3's two-step audit; the "row → digest" half is
  the component recomputation above. An item present in the document but absent from the crosswalk,
  or absent from the document but classified **D** or **T**, is a `GateFailureError`.
- **Replay never writes (v0.4).** Where an existing manifest matches, verification is the whole
  operation: read, reconstruct, compare, return (§11.3). No replacement statement is issued, and
  migration `0013`'s triggers 5 and 6 refuse one if it ever were.
- **The seal stays recomputable, not merely unchanged (v0.5).** §11.2(3) requires
  `selection_result_sha256` to independently recompute from §6.1's preimage before a manifest may be
  built, and that preimage reads `selection_run_id`, `snapshot_id`, and `selection_input_sha256` from
  the run row. Triggers 6, 7, and 8 make all three immutable, so the row a sealed digest was computed
  from cannot be rewritten underneath it. **Verification therefore proves recomputability rather than
  assuming it**, and §15.5 records the full guarantee.

## 13. Frozen ruling — the pilot-manifest document (owner correction C, v0.2)

### 13.1 What Stage S6 owes, and what it does not

[`Milestones/milestone_2_3_pilot_selection_plan.md`](../../Milestones/milestone_2_3_pilot_selection_plan.md)
**§10, "Required pilot-manifest contents", is the specification this section operationalizes.** v0.1
did not cite it and defined the document as no more than "a rendering of the values the row carries",
which is materially narrower than §10 requires; the focused independent governance review raised it
and the project owner corrected it. **Milestone plan §10 is neither superseded nor narrowed.** It is
implemented in two parts, and both parts are now stated so that neither can be lost between stages:

- **Stage S6 defines and fixture-tests the complete deterministic pilot-manifest document schema** —
  every block in §13.2, **every one of the 81 atomic §10 items in the §13.2.1 crosswalk**, every
  binding in §13.3, and the encoding in §13.5 — against synthetic fixtures. This is a *schema and a
  proof*, not a pilot sample.
- **Stage S9 supplies the exact real-data instance** of that schema, over the real frozen candidate
  snapshot. Stage S10 is the owner's approval of its root hash (Decision 013 §8).

A document produced at S6 over fixture data is structurally complete and is **not** a research
result: there is no real snapshot to describe and no code path that approves one (§17).

**Correction A (v0.4) — the crosswalk is exhaustive and item-by-item.** v0.2 asserted that §10 was
"neither superseded nor narrowed" and named exactly two deliberate omissions. The focused
independent governance review of v0.3 showed that claim was inaccurate: nineteen §10 items and four
partially covered items were neither serialized in a §13.2 block nor classified anywhere. **A
summary is not a crosswalk.** §13.2.1 therefore enumerates §10 **atomically** — every compound
bullet split into its separate requirements — and assigns each of the resulting **81** items to
exactly one of four categories, with a machine-checkable count and **zero unclassified items**.
§20 requires the implementation to assert the table row by row, so a §10 item that silently loses
its home fails the suite rather than reaching an owner.

### 13.2 Required contents — thirteen blocks, each bound

Every block below is mandatory. The right-hand column names the digest that commits it, so that
§13.3's completeness rule is checkable block by block rather than asserted. **There are thirteen
blocks** — v0.3's heading said "twelve" over this same thirteen-row table, which the v0.3 review
flagged; the count is corrected here and is thirteen everywhere in this record, in
[`m23_s6.md`](../../Milestones/contracts/m23_s6.md), and in the registry.

The **Serialized contents** column below states each block's *minimum* content. §13.2.1 is the
authority on the complete per-item obligation: where the crosswalk assigns a §10 item to a block,
that item is part of the block whether or not the summary line below repeats it.

| # | Block | Serialized contents | Committed by |
|---|---|---|---|
| 1 | **Manifest identity** | `manifest_id`; `manifest_schema_version`; `selection_run_id`; `snapshot_id`; `ordinal_version`; `supersedes_manifest_id`; `manifest_state` as the fixed literal `proposed` at S6 | `manifest_id` (§9.1); the root binds the schema version and both identity fields (§9); `manifest_state` per §13.2.2 |
| 2 | **Hash layers** | all eight component digests, `root_manifest_sha256`, and `selection_result_sha256` | `root_manifest_sha256` (§9); each component by its own §7–§8 preimage |
| 3 | **Environment and reproducibility identity** | `runtime_python_version`; `dependency_lock_sha256`; `code_commit_identifier`; `configuration_sha256` | `selector_policy_sha256` (§8.4) |
| 4 | **Active authority** | `decision_authority_sha256` and the enumerated `(decision record, content sha256)` pairs it covers; the nine `(policy_key, policy_version)` pairs | `selector_policy_sha256` (§8.4) |
| 5 | **Migration chain** | `(version, name, checksum_sha256)` for every applied migration, in version order | `migration_chain_sha256` → `selector_policy_sha256` (§8.4) |
| 6 | **Source plan and per-source provenance** | `source_plan_sha256`; per cited observation the six §8.1 fields — `source_id`, `request_identity`, `logical_sha256`, `parser_version`, `schema_fingerprint_sha256`, `outcome` | `source_plan_sha256` → `selector_policy_sha256`; the observation set → `source_observation_set_sha256` (§8.1) |
| 7 | **Candidate snapshot and candidate pool** | the twenty-two §8.2 fields, including all nine declared component digests and both counts | `candidate_tables_sha256` (§8.2) |
| 8 | **Selected entity records** | every selected entity at the eleven §7.1 columns, ordered by `selected_order`, **plus the §13.2.1 entity-record items**: `cik_padded`; the size, industry, history, and primary-universe evidence levels and their classification-dimension evidence records; `currently_inactive`; `engineering_only_stress`; `eligible_original_annual_report_count`; the Decision 019 §8 identity/name-change evidence records and derived flags; and the entity's `pilot_candidate_entity_reasons` rows | `selected_entities_sha256` (§7.1); `selection_input_sha256` via `entity_content_sha256` (§6.1); `candidate_tables_sha256` (§8.2) |
| 9 | **Selected accession records** | every selected accession at the seven §7.2 columns, ordered by `selected_order`, **plus the §13.2.1 accession-record items**: `accession_number_dashed`; `form_type`; `is_amendment` and `amendment_purpose_category`; `official_filing_date`; `report_date`; `acceptance_audit_date`; `provisional_official_cohort`; `acceptance_audit_cohort`; `cohort_ambiguous`; `filing_date_precedence`; the amendment linkage state, provisional parent (plain and dashed), and the eight `*_evidence_level` values; `multi_registrant` and the per-accession registrant records; `has_xbrl` and `has_inline_xbrl` | `selected_accessions_sha256` (§7.2); `selection_input_sha256` via `accession_content_sha256` (§6.1); `candidate_tables_sha256` (§8.2) |
| 10 | **Quota definitions and results** | definitions at the four §8.3 columns; results at the fourteen §7.3 columns | `quota_definitions_sha256` (§8.3) and `quota_report_sha256` (§7.3) |
| 11 | **Contribution and member records** | entity contributions, accession contributions, and quota-result members, at their §7.3 columns | `quota_report_sha256` (§7.3) |
| 12 | **Reserve packages, child rows, and dispositions** | packages, reserve accessions, reserve contributions, and the migration-`0012` `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` dispositions, at their §7.4 columns | `reserves_sha256` (§7.4) |
| 13 | **Historical reconstruction** | `selection_seed`; `selection_input_sha256`; `selection_input_schema_version`; candidate-table row counts; selected-table row counts; per-quota `excluded_pool_count` and `eligible_pool_count`; **exclusion counts by `reason_code`** over `pilot_candidate_entity_reasons` and `pilot_candidate_accession_reasons`; unresolved counts (rows whose `evidence_state` is not `provisional`) and the complementary **provisional count**; the `leakage_attestation` literal | `selection_result_sha256` (§6.1), `candidate_tables_sha256` (§8.2), `quota_report_sha256` (§7.3), `selector_policy_sha256` (§8.4) |

### 13.2.1 The exhaustive milestone-plan §10 crosswalk (owner correction A, v0.4)

**This table is normative and complete.** It enumerates
[`milestone_2_3_pilot_selection_plan.md`](../../Milestones/milestone_2_3_pilot_selection_plan.md)
§10 **atomically**: every compound bullet is split into its separate requirements.

**The arithmetic, stated exactly (editorial correction, owner-accepted 2026-07-30).** Milestone plan
§10 contains **74 original bullets** — Manifest identity 15, Source provenance 14, Entity records 13,
Accession records 16, Quota report 8, Reconstruction fields 8. **Seven** of them are compound and are
split into two requirements each:

| # | Compound bullet | §10 group | Atomic items |
|---|---|---|---|
| 1 | "as-of date and time zone" | Manifest identity | 13, 14 |
| 2 | "padded and numeric CIK" | Entity records | 31, 32 |
| 3 | "industry family and evidence basis" | Entity records | 35, 36 |
| 4 | "filer-size category and evidence basis" | Entity records | 37, 38 |
| 5 | "CIK and registrant CIK relationships" | Accession records | 48, 49 |
| 6 | "amendment parent and evidence state" | Accession records | 59, 60 |
| 7 | "input and output hashes" | Reconstruction fields | 78, 79 |

**74 original bullets producing 81 atomic requirements** (74 + 7 = 81), distributed 16, 14, 16, 18,
8, 9 across the six §10 groups — exactly the per-group counts the subsection headings below declare.
"migration versions and checksums" is deliberately **not** split, because block 5 serializes both
halves of it together.

This paragraph corrects explanatory arithmetic only. It was recorded after the focused independent
governance review of v0.5 demonstrated the bullet count mechanically from the plan source. **No
crosswalk row, item number, classification, category total, digest preimage, or SQL byte changes**,
and the review confirmed every one of the 74 bullets maps to at least one crosswalk row with none
duplicated or omitted.

Every item carries exactly one classification:

- **D — included directly.** The value is a **named field of a §§6–9 preimage** (or of a §7 frozen
  column tuple), and the document serializes it.
- **T — included transitively.** The value is committed through a **named component digest that
  covers a set containing it** — `selection_input_sha256`, `candidate_*_sha256`,
  `decision_authority_sha256`, `policy_versions_sha256`, `migration_chain_sha256`,
  `quota_report_sha256` — **and the document serializes it at the granularity §10 requires.**
- **X — operationally excluded** by [Decision 016](decision_016_m23_schema_and_artifact_architecture.md)
  §8 and §8.1, with the specific rationale given in the row. Not serialized.
- **S9 — deferred to Stage S9** under an existing owner ruling, cited in the row.

**A digest alone never discharges a requirement.** Where §10 asks for full records, provenance
entries, configuration values, authority records, or reconstruction content, category T requires the
values themselves in the document; the digest supplies the binding, not the content. **No fifth
category exists and no item is unclassified.**

Throughout, "reconstruction source" names where a verifier re-reads the value to check the document
against the persisted state (§12).

#### §10 "Manifest identity" — 16 atomic items

| # | §10 item | Block | Committing digest | Class | Reconstruction source |
|---|---|---|---|---|---|
| 1 | manifest schema version | 1 | `root_manifest_sha256` (§9) names it; `selector_policy_sha256` (§8.4) binds the constant | **D** | `PILOT_MANIFEST_HASH_POLICY_VERSION`; `pilot_manifest_versions.manifest_schema_version` |
| 2 | manifest version (`ordinal_version`) | 1 | `manifest_id` (§9.1) names it | **D** | `pilot_manifest_versions.ordinal_version` |
| 3 | status (proposed / owner-approved / rejected / superseded) | 1 | the **fixed literal** `proposed`, committed through `manifest_schema_version` → `root_manifest_sha256` (§13.2.2) | **T** | `pilot_manifest_versions.manifest_state` |
| 4 | selection seed | 13 | `selection_input_sha256` (a `selection_seed` field of its preimage) → §6.1 → §9 | **T** | `pilot_selection_runs.selection_seed` |
| 5 | selection-policy version | 4 | `policy_versions_sha256` → `selector_policy_sha256` (§8.4), keys `pilot_selector` and `pilot_joint_selector`; independently inside `selection_input_sha256` | **T** | `reference_policy_versions`; `pilot_selection_runs.selector_policy_version` |
| 6 | quota-policy version | 4 | `quota_definitions_sha256` (§8.3) names `quota_policy_version` | **D** | `reference_policy_versions`; `pilot_selection_runs.quota_policy_version` |
| 7 | selector code commit | 3 | `selector_policy_sha256` (§8.4) names `code_commit_identifier` | **D** | the §8.4 explicit argument recorded in the document |
| 8 | Python version | 3 | `selector_policy_sha256` names `runtime_python_version` | **D** | the §8.4 explicit argument |
| 9 | dependency-lock hash | 3 | `selector_policy_sha256` names `dependency_lock_sha256` | **D** | the §8.4 explicit argument |
| 10 | migration versions and checksums | 5 | `migration_chain_sha256` → `selector_policy_sha256` (§8.4) | **T** | `ops_schema_migrations (version, name, checksum_sha256)` |
| 11 | active decision-record hashes | 4 | `decision_authority_sha256` → `selector_policy_sha256` (§8.4) | **T** | the enumerated `(decision record, content sha256)` pairs in the document |
| 12 | configuration hash | 3 | `selector_policy_sha256` names `configuration_sha256` | **D** | the §8.4 explicit argument |
| 13 | as-of **date** | 7 | `candidate_tables_sha256` (§8.2) names `as_of_date` | **D** | `pilot_candidate_snapshots.as_of_date` |
| 14 | as-of **time zone** | 7 | `decision_authority_sha256` → `selector_policy_sha256` (§8.4). The EDGAR operating-calendar zone is **`America/New_York`**, frozen by [Decision 010](decision_010_temporal_availability_and_cohort_assignment.md) §5.2; that record's content hash is in the enumerated authority set, so the zone cannot change without changing the root | **T** | Decision 010 §5.2; `sec/calendar.py` |
| 15 | source-plan hash | 6 | `selector_policy_sha256` names `source_plan_sha256` | **D** | the §8.4 explicit argument |
| 16 | candidate-pool hash | 7 | `candidate_tables_sha256` (§8.2) names `candidate_snapshot_sha256` | **D** | `pilot_candidate_snapshots.candidate_snapshot_sha256` |

**Subtotal: D 10, T 6, X 0, S9 0.**

#### §10 "Source provenance" — 14 atomic items, per cited observation

| # | §10 item | Block | Committing digest | Class | Reconstruction source |
|---|---|---|---|---|---|
| 17 | source ID | 6 | `source_observation_set_sha256` (§8.1) names `source_id` | **D** | `census_source_observations.source_id` |
| 18 | source URL identity or approved source key | 6 | §8.1 names `request_identity` — the approved source key. The raw `requested_url`/`final_url` are excluded as URL-trace data | **D** | `census_source_observations.request_identity` |
| 19 | source observation ID | — | — | **X** | per-retrieval identity (§8.1): `observation_id` is excluded **so that two retrievals of identical content under the same request identity hash identically**. The observation is named in the document by the bound `(source_id, request_identity)` pair, from which the row is recoverable |
| 20 | retrieval attempt ID | — | — | **X** | per-retrieval identity: `attempts` (Decision 016 §8) |
| 21 | retrieved-at UTC | — | — | **X** | timestamp; Decision 016 §8 corrects the S3 design specifically here |
| 22 | HTTP validator metadata | — | — | **X** | headers and validators are excluded as a class (§8.1): `etag`, `last_modified`, `validators_sent_json`, `headers_json` |
| 23 | transport hash | — | — | **X** | transport digest (§8.1): `transport_sha256`; the *decoded* content is bound instead |
| 24 | decoded-content hash | 6 | §8.1 names `logical_sha256` | **D** | `census_source_observations.logical_sha256` |
| 25 | stored-object hash | — | — | **X** | storage digest (§8.1): `stored_sha256` |
| 26 | relative storage path | — | — | **X** | path; excluded from every digest by Decision 016 §8 and from the document by §13.4 |
| 27 | parser version | 6 | §8.1 names `parser_version` | **D** | `census_source_observations.parser_version` |
| 28 | parser status | 6 | §8.1 names `outcome` | **D** | `census_source_observations.outcome` |
| 29 | schema fingerprint | 6 | §8.1 names `schema_fingerprint_sha256`, derived by the five-column partition rule | **D** | `census_structural_observations`, five-column rule (§8.1) |
| 30 | supersession lineage | — | — | **X** | per-retrieval identity (§8.1): `supersedes_observation_id`, `reused_observation_id` |

**Subtotal: D 6, T 0, X 8, S9 0.** The eight **X** items are the retrieval envelope. They are
recoverable in full from `census_source_observations` by the bound `(source_id, request_identity)`
pair; serializing an unbound copy would violate §13.3, so the document binds the content record and
points at the envelope rather than duplicating it.

#### §10 "Entity records" — 16 atomic items, per selected entity

| # | §10 item | Block | Committing digest | Class | Reconstruction source |
|---|---|---|---|---|---|
| 31 | **padded** CIK | 8 | `selection_input_sha256` via `entity_content_sha256` (`cik_padded`) | **T** | `pilot_candidate_entities.cik_padded` |
| 32 | **numeric** CIK | 8 | `selected_entities_sha256` (§7.1) names `cik_numeric` | **D** | `pilot_selected_entities.cik_numeric` |
| 33 | entity role | 8 | §7.1 names `entity_role` | **D** | `pilot_selected_entities.entity_role` |
| 34 | operating or control classification | 8 | §7.1 names `candidate_category` and `control_kind` | **D** | `pilot_selected_entities` |
| 35 | industry **family** | 8 | §7.1 names `industry_family` | **D** | `pilot_selected_entities.industry_family` |
| 36 | industry **evidence basis** | 8 | `entity_content_sha256` (`industry_evidence_level`, `industry_quota_eligible`, and the `industry`-dimension evidence records) → `selection_input_sha256`; also `candidate_entity_evidence_sha256` (§8.2) | **T** | `pilot_candidate_entities`; `pilot_candidate_entity_evidence` |
| 37 | filer-size **category** | 8 | §7.1 names `size_stratum` | **D** | `pilot_selected_entities.size_stratum` |
| 38 | filer-size **evidence basis** | 8 | `entity_content_sha256` (`size_evidence_level` and the `size`-dimension evidence records) → `selection_input_sha256`; also `candidate_entity_evidence_sha256` | **T** | `pilot_candidate_entities`; `pilot_candidate_entity_evidence` |
| 39 | history category | 8 | §7.1 names `history_class` | **D** | `pilot_selected_entities.history_class` |
| 40 | event flags | 8, 11 | `entity_content_sha256` (`history_class`, `currently_inactive`, `engineering_only_stress`), `candidate_tables_sha256` (`eligible_original_annual_report_count`), and `quota_report_sha256` for the entity's event-bearing quota contributions | **T** | `pilot_candidate_entities`; `pilot_selected_entity_quota_contributions` |
| 41 | current-status evidence | 8 | `entity_content_sha256` (`currently_inactive`) and the entity's status evidence records → `selection_input_sha256`; also `candidate_entity_evidence_sha256` | **T** | `pilot_candidate_entities.currently_inactive`; `pilot_candidate_entity_evidence` |
| 42 | alias evidence | 8 | `entity_content_sha256` — the six Decision 019 §8 `name_change_*` derived flags and the `identity`-dimension evidence records → `selection_input_sha256`; also `candidate_entity_evidence_sha256`. `filing_time_name` itself is **not** serialized: names never enter a hash or an ordering decision (accepted S4.2 precedent, restated in `_entity_content_sha256`) | **T** | `pilot_candidate_entity_evidence` (`classification_dimension = 'identity'`) |
| 43 | provisional flags | 8 | `entity_content_sha256` — `size_evidence_level`, `industry_evidence_level`, `history_evidence_level`, `primary_universe_evidence_level` → `selection_input_sha256` | **T** | `pilot_candidate_entities` |
| 44 | review reasons | 8, 12 | `entity_content_sha256`'s reasons component and `candidate_entity_reasons_sha256` (§8.2) for candidate-scope reasons; `reserves_sha256` (§7.4) for the reserve-scope dispositions | **T** | `pilot_candidate_entity_reasons`; `pilot_selection_entity_reasons` |
| 45 | deterministic entity hash | 8 | §7.1 names `entity_hash_sha256` | **D** | `pilot_selected_entities.entity_hash_sha256` |
| 46 | reserve rank | 12 | `reserves_sha256` (§7.4) names `reserve_rank` | **D** | `pilot_reserves.reserve_rank` |

**Subtotal: D 8, T 8, X 0, S9 0.**

#### §10 "Accession records" — 18 atomic items, per selected accession

| # | §10 item | Block | Committing digest | Class | Reconstruction source |
|---|---|---|---|---|---|
| 47 | canonical accession number | 9 | `selected_accessions_sha256` (§7.2) names `accession_plain`; `accession_content_sha256` binds `accession_number_dashed` | **D** | `pilot_selected_accessions`; `pilot_candidate_accessions` |
| 48 | **anchor** CIK | 9 | §7.2 names `anchor_cik_numeric` | **D** | `pilot_selected_accessions.anchor_cik_numeric` |
| 49 | **registrant** CIK relationships | 9 | `accession_content_sha256` (`multi_registrant`, `registrant_content_sha256`) → `selection_input_sha256`; also `candidate_registrant_table_sha256` (§8.2) | **T** | `pilot_candidate_accession_registrants` |
| 50 | form | 9 | `accession_content_sha256` (`form_type`) → `selection_input_sha256` | **T** | `pilot_candidate_accessions.form_type` |
| 51 | original or amendment role | 9 | `accession_content_sha256` (`is_amendment`, `amendment_purpose_category`, `amendment_purpose_quota_eligible`) | **T** | `pilot_candidate_accessions` |
| 52 | official filing date | 9 | `accession_content_sha256` (`official_filing_date`) | **T** | `pilot_candidate_accessions.official_filing_date` |
| 53 | acceptance timestamps | 9 | `accession_content_sha256` (`acceptance_audit_date`) — the M2.3 metadata-only acceptance value. The raw SEC acceptance datetime is not a pilot-candidate column and is a timestamp excluded by Decision 016 §8 | **T** | `pilot_candidate_accessions.acceptance_audit_date` |
| 54 | report date | 9 | `accession_content_sha256` (`report_date`) | **T** | `pilot_candidate_accessions.report_date` |
| 55 | fiscal year end | 9, 11 | `accession_content_sha256` (`report_date`, the fiscal-year-end basis under Decision 018 §12) and `quota_report_sha256` for the `fiscal_year_end_change_entities` quota contribution | **T** | `pilot_candidate_accessions.report_date`; `pilot_selected_entity_quota_contributions` |
| 56 | official cohort | 9 | `accession_content_sha256` (`provisional_official_cohort`, `cohort_applicability`, `cohort_ambiguous`) | **T** | `pilot_candidate_accessions` |
| 57 | acceptance audit cohort | 9 | `candidate_tables_sha256` via `candidate_accession_table_sha256` (§8.2) | **T** | `pilot_candidate_accessions.acceptance_audit_cohort` |
| 58 | after-hours state | 9 | represented by the bound `official_filing_date` / `acceptance_audit_date` pair, `filing_date_precedence`, and both cohorts, under the **17:30 `America/New_York`** cutoff frozen by Decision 010 §5.2 and bound through `decision_authority_sha256` | **T** | `pilot_candidate_accessions`; Decision 010 §5.2 |
| 59 | amendment **parent** | 9 | `accession_content_sha256` (`stored_amendment_linkage_state`, `stored_provisional_parent_accession`, `provisional_parent_accession_dashed`) | **T** | `pilot_candidate_accessions` |
| 60 | amendment **evidence state** | 9 | `accession_content_sha256` (`amendment_purpose_evidence_level`, `stored_amendment_purpose_evidence_level`, `amendment_linkage_evidence_level`) | **T** | `pilot_candidate_accessions` |
| 61 | base, stress, support, or control role | 9 | §7.2 names `accession_role` | **D** | `pilot_selected_accessions.accession_role` |
| 62 | cross-cutting quotas satisfied | 11 | `quota_report_sha256` (§7.3) names the `pilot_selected_accession_quota_contributions` tuple | **D** | `pilot_selected_accession_quota_contributions` |
| 63 | provisional-verification requirements | 9 | `accession_content_sha256` — the eight `*_evidence_level` values on the accession (filing date, cohort, stored cohort, XBRL, amendment purpose, stored amendment purpose, amendment linkage, multi-registrant) | **T** | `pilot_candidate_accessions` |
| 64 | deterministic accession hash | 9 | §7.2 names `accession_hash_sha256` | **D** | `pilot_selected_accessions.accession_hash_sha256` |

**Subtotal: D 5, T 13, X 0, S9 0.**

#### §10 "Quota report" — 8 atomic items, per quota

| # | §10 item | Block | Committing digest | Class | Reconstruction source |
|---|---|---|---|---|---|
| 65 | required value | 10 | `quota_report_sha256` (§7.3) and `quota_definitions_sha256` (§8.3) name `required_count` | **D** | `pilot_quota_results.required_count` |
| 66 | achieved value | 10 | §7.3 names `achieved_count` | **D** | `pilot_quota_results.achieved_count` |
| 67 | selected members | 11 | §7.3 names the `pilot_quota_result_members` tuple | **D** | `pilot_quota_result_members` |
| 68 | evidence level | 10 | §7.3 names `evidence_state` | **D** | `pilot_quota_results.evidence_state` |
| 69 | provisional count | 13 | `quota_report_sha256` over the rows it aggregates — the count of results whose `evidence_state` **is** `provisional`, complementary to the unresolved count | **T** | `pilot_quota_results.evidence_state` |
| 70 | reserve coverage | 12 | `reserves_sha256` (§7.4) — the target's rank-1 package or its `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition | **D** | `pilot_reserves`; `pilot_selection_entity_reasons` |
| 71 | pass, fail, or unproven | 10 | §7.3 names `quota_result` | **D** | `pilot_quota_results.quota_result` |
| 72 | reason for failure | 10 | §7.3 names `binding_constraint` and `binding_evidence_sha256` | **D** | `pilot_quota_results` |

**Subtotal: D 7, T 1, X 0, S9 0.**

#### §10 "Reconstruction fields" — 9 atomic items

| # | §10 item | Block | Committing digest | Class | Reconstruction source |
|---|---|---|---|---|---|
| 73 | canonical SQL/query or selector-input version | 13 | `selection_result_sha256` (§6.1) and `selector_policy_sha256` (§8.4) name `selection_input_schema_version` | **D** | `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` |
| 74 | candidate-table row counts | 13 | `candidate_tables_sha256` (§8.2) names `entity_count` and `accession_count` | **D** | `pilot_candidate_snapshots` |
| 75 | selected-table row counts | 13 | `selection_result_sha256` (§6.1) names `selected_entity_count` and `selected_accession_count` | **D** | `pilot_selection_runs` |
| 76 | exclusion counts by reason | 13 | `candidate_entity_reasons_sha256` and `candidate_accession_reasons_sha256` → `candidate_tables_sha256` (§8.2); also the reasons component of `entity_content_sha256` / `accession_content_sha256` | **T** | `pilot_candidate_entity_reasons`; `pilot_candidate_accession_reasons`, grouped by `reason_code` |
| 77 | unresolved counts | 13 | `quota_report_sha256` (§7.3) over the rows it aggregates | **T** | `pilot_quota_results` where `evidence_state` is not `provisional` |
| 78 | **input** hashes | 2, 13 | §6.1 names `selection_input_sha256`; §9 names all eight component digests | **D** | `pilot_selection_runs`; recomputed at §12 |
| 79 | **output** hashes | 2 | `root_manifest_sha256` (§9) and `manifest_id` (§9.1); `selection_result_sha256` (§6.1) | **D** | `pilot_manifest_versions`; recomputed at §12 |
| 80 | command invocation with no personal path or SEC identity | — | — | **S9** | Stage S6 has no CLI (§16, owner correction F, v0.2), so there is no invocation to record. Deferred to **Stage S9** with the CLI (§17), where it is added to the document. **Not dropped** |
| 81 | confirmation that no prohibited data source was read | 13 | `selector_policy_sha256` (§8.4) names the `leakage_attestation` literal | **D** | the fixed literal, plus the §20 read-set test (§8.4.1) |

**Subtotal: D 6, T 2, X 0, S9 1.**

#### Machine-checkable count — frozen

```
total_section_10_items      = 81
directly_included    (D)    = 42
transitively_included(T)    = 30
operationally_excluded(X)   =  8
deferred_to_s9       (S9)   =  1
deferred_to_s10      (S10)  =  0
unclassified                =  0
```

`D + T + X + S9 + S10 == total`, and `unclassified == 0`. §20 requires a test asserting these six
numbers and the per-item classification, so neither the table nor the totals can drift silently.

**`deferred_to_s10 = 0` is deliberate and correct.** Stage S10 is the owner's approval act on the
exact `root_manifest_sha256` (Decision 013 §8; §17), not a manifest-*content* requirement. §10 asks
the manifest to carry a status, which item 3 supplies; it does not ask the manifest to carry its own
approval.

**Exact real-data values remain Stage S9 for every item.** §13.1's split is unchanged: S6 defines and
fixture-tests the schema for all 81 items; S9 instantiates it over the real frozen snapshot. That is
a stage split, not a per-item deferral, and item 80 is the only item deferred as an *item*.

### 13.2.2 `manifest_state` — a fixed literal, committed through the schema version

`manifest_state` is serialized in block 1 and is **excluded from `root_manifest_sha256`** (§9), for a
reason that is not an oversight: the root must survive the lifecycle transition unchanged, because
Decision 013 §8 makes M2.3 completion the owner's approval of *the exact final manifest hash* and
migration `0009` already enforces
`CHECK (manifest_state NOT IN ('owner_approved','superseded') OR approved_root_sha256 = root_manifest_sha256)`.
A root that changed on approval would defeat both.

It is nonetheless bound, by exactly the construction §6.2 uses for `run_state` and §8.2 for
`snapshot_state`: **at Stage S6 `manifest_state` is a fixed literal, not a read value.** The S6
document schema is the *proposed*-manifest schema; the implementation asserts
`manifest_state = 'proposed'` and fails closed with `GateFailureError` otherwise, then serializes the
constant. `manifest_schema_version` — which identifies that schema and therefore that literal — **is**
a named field of the root preimage. A later lawful transition to `owner_approved` or `superseded`
moves the row under migration `0009`'s transition guard and leaves both the root and the S6 document
untouched.

### 13.3 The completeness rule — no unbound substantive field

**Every substantive value the document serializes must be committed, directly or transitively, by
`root_manifest_sha256`; the two version-ordering fields `ordinal_version` and
`supersedes_manifest_id` are committed by `manifest_id`, which itself commits the root (§10.1).
Taken together, `manifest_id` commits the entire document. No substantive serialized field may be
unbound by both.**

Three consequences, frozen:

- **Adding a field to the document requires adding it to a preimage.** A field that no digest commits
  may not be serialized. This is why owner correction C extended §8.4 rather than letting the
  document carry loose environment and authority values.
- **The serialized document is a rendering, never a second source of truth.** Every value is either
  read from the persisted rows the digests were computed over, or is one of the explicit arguments
  §8.4 requires. A rendering that disagrees with the persisted row, or that fails to reproduce the
  root when re-derived, is a `GateFailureError`.
- **The obligation is testable, and §20 requires the test:** a completeness assertion enumerating
  every serialized leaf and mapping it to the digest that binds it, so a later field added without a
  binding fails the suite rather than reaching an owner.

**How a transitively committed value is audited (v0.4).** Thirty of the 81 §10 items are class **T**:
committed through a component digest that covers a *set* containing the value, rather than by a
preimage that names the field. That is a complete binding, in two steps, and §12 checks both:

1. **Row → digest.** Changing the persisted value changes the covering digest — `entity_content_sha256`
   or `accession_content_sha256` inside `selection_input_sha256`, a `candidate_*_sha256` declared
   digest inside `candidate_tables_sha256`, `decision_authority_sha256` or `policy_versions_sha256`
   or `migration_chain_sha256` inside `selector_policy_sha256`, or `quota_report_sha256` — and
   therefore changes `root_manifest_sha256`.
2. **Document → row.** §13.3's second consequence already requires the rendering to agree with the
   persisted row it came from. Verification re-reads the row and compares; a document value that
   disagrees is a `GateFailureError`.

Tampering with the row is caught by step 1, tampering with the document alone by step 2. **Neither
step is optional**, which is why §20 requires the per-item crosswalk assertion and the
rendering-versus-row assertion as separate tests.

**Adding, moving, or reclassifying a §10 item is an owner-level act.** §13.2.1 is frozen. An
implementation session that finds an item it cannot place stops under §21 rather than choosing a
category.

### 13.4 The operational envelope — excluded, and excluded from the document too

`relative_manifest_path`, `generated_at_utc`, `approved_at_utc`, `rejected_at_utc`,
`superseded_at_utc`, `approval_reference`, `detail`, and every event ID are **operational**. They are
excluded from every digest (§5, §9) and, because §13.3 forbids unbound substantive fields, they are
excluded from the document's substantive body as well. `relative_manifest_path` is persisted on the
row for retrieval and is never identity. No absolute path and no SEC identity appears anywhere in the
document, at any nesting depth.

### 13.5 Encoding and location

- The canonical pilot-manifest JSON is written under **`DataTree.releases / "pilot"`**. No new
  top-level data directory is introduced, consistent with Decision 016 §8; the writer creates the
  subdirectory with `mkdir(parents=True, exist_ok=True)`, exactly as `ReleaseManifest.write` already
  does. **`paths.py` is not modified**, and `SEC_SUBTREES` is unchanged.
- The filename is **content-derived from the root**: `pilot_manifest_<root_manifest_sha256>.json`.
- Encoding follows Decision 013 §7 exactly: UTF-8, LF line endings, sorted object keys, arrays in
  deterministic order, no nonfinite numbers, canonical accession and CIK formatting, UTC timestamps
  written with `Z`, **relative paths only**.
- Re-serializing the same manifest is byte-identical.

### 13.6 Distinct from the SEC-inventory release manifest

**The pilot manifest is a distinct artifact.** It uses
`manifest_schema_version = "pilot-manifest/1.0"` and must not reuse `ReleaseManifest`,
`build_manifest`, or `RELEASE_SCHEMA_VERSION = "sec_inventory/0.1"` from
[`release/manifest.py`](../../src/disclosure_drift/release/manifest.py). Only the hashing primitives
in `release/hashing.py` are shared.

## 14. Frozen ruling — the S4 exclusion and S5 authority

- **The Stage-S4 entity-only draft is excluded from manifest authority, permanently.** It stays
  `running`, non-publishable, and is never mutated, deleted, promoted, or used as a manifest source
  (Decision 018 §§6, 27; Decision 020 §11). S6 reads it not at all.
- **The exclusion is enforced twice**: by the eligibility precondition §11.2(6), and — for the first
  time — at the schema layer, because migration `0013` refuses a manifest over any run that is not
  `feasible` (§15), and the S4 draft is permanently `running`. §3.2 shows why the policy-only form
  was insufficient.
- **Stage S5 remains the sole accepted joint-selection authority.** S6 consumes only accepted S5
  terminal state and its frozen historical inputs. It runs **no second selection**, applies **no
  reserve substitution**, re-derives **no** selection, quota-contribution, reserve, role, penalty,
  family, or tie-break rule, and adds no policy function. Reserve packages remain contingencies,
  never simultaneous replacements. `sec/accession_selector.py`, `sec/accession_selection_store.py`,
  `sec/reserve_selector.py`, `sec/entity_selector.py`, and `sec/entity_selection_store.py` are
  **unchanged** by Stage S6.

## 15. Frozen ruling — schema and migration `0013`

**Exactly one additive, DDL-only migration is authorized in principle:**

**Filename (frozen):**
`src/disclosure_drift/storage/migrations/0013_m23_manifest_lifecycle_guards.sql`

**It is not created by this record**, and **no migration other than `0013` is authorized.** It
creates **no table, no column, and no index** — only **eight new triggers** (owner ruling, v0.5;
v0.4 proposed five, v0.2 four, v0.1 three). It does not edit, replace, drop, alter, or reinterpret any
existing table, column, index, trigger, or migration; migrations `0009`–`0012` are untouched,
including their inherited OLD-only and NULL-comparison behaviour, which is deliberately left alone.

**Why existing schema cannot satisfy the requirement:** §§3.1–3.3, §3.5, and §3.6 record the direct
probes.
No trigger on `pilot_selection_runs` names `selection_result_sha256`, so the column is writable on any
run in any state, overwritable, and clearable — and the table has **no `INSERT` guard at all**, so a
run can be created already `feasible` and already sealed. `pilot_manifest_versions` has no `INSERT`
guard either, its composite foreign key constrains identity rather than run state, none of its four
existing triggers protects any identity column, and **every one of those four is a `BEFORE UPDATE` or
`BEFORE DELETE` trigger, so a single `INSERT OR REPLACE` steps around all of them** (§3.5). The same
mechanics reach `pilot_selection_runs`, which is worse off still: it has **no delete guard of any
kind** and **no trigger naming any identity column**, so its run can be replaced, deleted, or
re-identified outright (§3.6). Per Decision 018 §25 and Decision 020 §8.2's standing rule, a schema
gap is an owner-level conflict resolved by an authorized migration or not at all — never a widening a
session performs on its own. **Triggers 6, 7, and 8 were designed and scratch-validated at the v0.4
review and authorized by the project owner before being frozen here.**

**The eight triggers, and what each closes:**

| # | Trigger | Event | Closes |
|---|---|---|---|
| 1 | `pilot_selection_run_insert_unsealed_guard` | `BEFORE INSERT ON pilot_selection_runs` | §3.1 — a run created already sealed (**new at v0.2**) |
| 2 | `pilot_selection_run_result_hash_guard` | `BEFORE UPDATE OF selection_result_sha256` | §3.1 — sealing a non-`feasible` run; changing or clearing a seal |
| 3 | `pilot_manifest_versions_insert_guard` | `BEFORE INSERT ON pilot_manifest_versions` | §3.2 — a manifest over a missing, mismatched, non-`feasible`, or unsealed run |
| 4 | `pilot_manifest_versions_identity_guard` | `BEFORE UPDATE OF` the six identity columns | §3.3 — mutable manifest identity; a manifest moved onto an ineligible run (**restated and widened at v0.2**) |
| 5 | `pilot_manifest_versions_replacement_guard` | `BEFORE INSERT ON pilot_manifest_versions` | §3.5 — `INSERT OR REPLACE` displacing or impersonating an existing manifest on any of the table's three uniqueness routes (**new at v0.4**) |
| 6 | `pilot_selection_run_replacement_guard` | `BEFORE INSERT ON pilot_selection_runs` | §3.6 gap 5 — a duplicate, ignored, or replacing `INSERT` displacing an existing run and clearing or rewriting its seal (**new at v0.5**) |
| 7 | `pilot_selection_run_delete_guard` | `BEFORE DELETE ON pilot_selection_runs` | §3.6 gap 6 — deletion of a run in any state (**new at v0.5**) |
| 8 | `pilot_selection_run_identity_guard` | `BEFORE UPDATE OF selection_run_id, snapshot_id, selection_input_sha256` | §3.6 gap 7 — direct mutation of persisted run identity, which silently falsifies a sealed digest against its own preimage (**new at v0.5**) |

Triggers 1 and 2 make the seal append-once on the `INSERT` and `UPDATE` paths, so trigger 3's
precondition — an existing `feasible` run carrying a non-`NULL` seal — cannot be manufactured by
either. Trigger 4 then holds the manifest row that precondition admits permanently bound to it on the
`UPDATE` path, and **trigger 5 closes the replacement path that would otherwise route around trigger
4 entirely.** Triggers 6, 7, and 8 do for the run row what 5 and 4 do for the manifest row: **6**
closes replacement, **7** closes deletion, and **8** closes identity mutation — so the run the seal
belongs to is as immovable as the manifest built over it. **Trigger 2 is neither widened nor
renamed**: the seal lifecycle and run identity stay separate invariants in separate triggers, each
independently testable, matching the one-responsibility-per-trigger shape of the table above.

**The two uniqueness routes trigger 6 covers are the complete set**, enumerated from the live schema:
`PRAGMA index_list(pilot_selection_runs)` reports the `selection_run_id` primary-key autoindex, the
`UNIQUE (selection_run_id, snapshot_id)` autoindex, and the non-unique
`idx_pilot_selection_runs_state`. **Both unique routes require a matching `selection_run_id`**, so
trigger 6's single `EXISTS` on that column covers every constructible replacement conflict —
including one that would arrive with a different `snapshot_id` or a different
`selection_input_sha256` — and it refuses a plain duplicate `INSERT` and an `INSERT OR IGNORE` as
well, rather than letting either pass silently.

**The three uniqueness routes trigger 5 covers are the complete set**, enumerated from the live
schema rather than from prose. `PRAGMA index_list(pilot_manifest_versions)` reports exactly four
indexes:

| Index | Unique | Origin | Replacement route? |
|---|---|---|---|
| `sqlite_autoindex_pilot_manifest_versions_1` (`manifest_id`) | yes | `TEXT PRIMARY KEY` | **yes — route 1** |
| `sqlite_autoindex_pilot_manifest_versions_2` (`selection_run_id`, `snapshot_id`, `ordinal_version`) | yes | `UNIQUE` | **yes — route 2** |
| `uq_pilot_manifest_single_active_approval` (`selection_run_id`, `snapshot_id`) `WHERE manifest_state = 'owner_approved'` | yes | partial index | **yes — route 3** |
| `idx_pilot_manifest_versions_state` (`manifest_state`, `generated_at_utc`) | no | index | no — non-unique indexes cannot drive conflict resolution |

Route 3 is the most consequential and the least obvious: a replacement conflicting only on the
partial index displaces an **already `owner_approved`** manifest under a *different* `manifest_id`
and `ordinal_version`, which routes 1 and 2 do not catch.

**Behaviour-neutrality:** §3.4 records the verification. No accepted S4 or S5 statement names
`selection_result_sha256`, `selection_run_id`, or `snapshot_id` in an `UPDATE … SET` list — so
trigger 8 cannot fire on an accepted path either; no accepted statement names
`selection_result_sha256` in an `INSERT` column list; no accepted statement writes
`pilot_manifest_versions` at all; and no accepted statement anywhere in `src/` issues
`INSERT OR REPLACE`, `REPLACE INTO`, `INSERT OR IGNORE`, or `DELETE` against either table, so
triggers 5, 6, and 7 are unreachable as well. The accepted replay path `SELECT`s the run first and
reconstructs and returns when it exists, inserting only when it does not. **None of the eight
triggers can fire on any accepted code path, and migration `0013` changes no accepted behaviour.**

**Trigger names**, all new and collision-free against every object in migrations `0009`–`0012`:
`pilot_selection_run_insert_unsealed_guard`, `pilot_selection_run_result_hash_guard`,
`pilot_manifest_versions_insert_guard`, `pilot_manifest_versions_identity_guard`,
`pilot_manifest_versions_replacement_guard`, `pilot_selection_run_replacement_guard`,
`pilot_selection_run_delete_guard`, `pilot_selection_run_identity_guard`.

**Triggers 3 and 5 are both `BEFORE INSERT` on `pilot_manifest_versions`, and triggers 1 and 6 are
both `BEFORE INSERT` on `pilot_selection_runs`; SQLite does not define firing order within either
pair.** Both members of each pair abort, so either order refuses the same statements and only the
message differs. A test asserting a specific message must therefore construct a case that violates
exactly one of the pair.

### 15.1 Normative SQL — frozen, byte-for-byte

The **eight** blocks below are the **complete normative statement region** of migration `0013`, in
the order shown. They **replace the five-block v0.4 region, the four-block v0.3 region, and the
three-block v0.1 region in their entirety**; all three earlier statement regions and their
concatenation digests are withdrawn and must not be reproduced. An implementation session **reproduces the blocks below verbatim**; trigger behaviour
is not defined by prose anywhere in this record or in the stage contract, and **no
implementation-time reinterpretation, reformulation, optimization, or "equivalent" rewriting is
permitted.** A difference between the migration file's statement region and the SQL below is a defect
in the migration, never a correction to this record.

**Blocks 1 through 5 are byte-identical to v0.4's five blocks and retain their per-block digests
exactly** — the v0.5 ruling adds three triggers, it does not restate the existing five, and it
neither widens nor renames trigger 2. **Blocks 6, 7, and 8 are new at v0.5**, and because the
region's composition changed, the **region-level** digest, byte count, and line count are all new
(§15.3).

The migration file additionally carries a leading `--` header comment block, following the migration
`0012` convention. **The header is not part of the normative statement region** and is not covered by
the digests in §15.3.

**Block 1 — `pilot_selection_run_insert_unsealed_guard`** (new at v0.2)

```sql
CREATE TRIGGER pilot_selection_run_insert_unsealed_guard
BEFORE INSERT ON pilot_selection_runs
WHEN NEW.selection_result_sha256 IS NOT NULL
BEGIN
    -- Every selection run begins unsealed. The terminal result digest is established
    -- only by the append-once UPDATE guard below, on a run that is already feasible, so
    -- a row can never be created pre-sealed and present a forged terminal identity to
    -- the manifest insert guard. Without this, append-once would hold on the UPDATE
    -- path only, and a direct INSERT could manufacture a feasible, sealed run.
    SELECT RAISE(ABORT,
        'pilot selection run must be inserted unsealed; selection_result_sha256 is set only by a later append-once seal on a feasible run');
END;
```

**Block 2 — `pilot_selection_run_result_hash_guard`**

```sql
CREATE TRIGGER pilot_selection_run_result_hash_guard
BEFORE UPDATE OF selection_result_sha256 ON pilot_selection_runs
BEGIN
    -- Sealing is permitted only on a run that is feasible both before and after the
    -- write. run_state is NOT NULL, so neither comparison can yield NULL and silently
    -- skip this check.
    SELECT RAISE(ABORT,
        'pilot selection result hash may be set only on a feasible selection run')
    WHERE OLD.selection_result_sha256 IS NULL
      AND NEW.selection_result_sha256 IS NOT NULL
      AND (OLD.run_state <> 'feasible' OR NEW.run_state <> 'feasible');
    -- Once sealed the digest is immutable: it may neither change nor be cleared. IS NOT
    -- is NULL-safe, so clearing to NULL is caught by the same predicate that catches a
    -- changed value. Rewriting the identical value stays permitted, so a replay that
    -- recomputes the same digest is idempotent rather than a failure.
    SELECT RAISE(ABORT,
        'pilot selection result hash is immutable once set')
    WHERE OLD.selection_result_sha256 IS NOT NULL
      AND NEW.selection_result_sha256 IS NOT OLD.selection_result_sha256;
END;
```

**Block 3 — `pilot_manifest_versions_insert_guard`**

```sql
CREATE TRIGGER pilot_manifest_versions_insert_guard
BEFORE INSERT ON pilot_manifest_versions
WHEN NOT EXISTS (
    SELECT 1 FROM pilot_selection_runs
    WHERE selection_run_id = NEW.selection_run_id
      AND snapshot_id = NEW.snapshot_id
      AND run_state = 'feasible'
      AND selection_result_sha256 IS NOT NULL)
BEGIN
    SELECT RAISE(ABORT,
        'pilot manifest insert requires an existing feasible selection run whose snapshot matches and whose selection_result_sha256 is sealed');
END;
```

**Block 4 — `pilot_manifest_versions_identity_guard`** (replaces v0.1's block 3)

```sql
CREATE TRIGGER pilot_manifest_versions_identity_guard
BEFORE UPDATE OF manifest_id, manifest_schema_version, selection_run_id, snapshot_id,
                 ordinal_version, supersedes_manifest_id
ON pilot_manifest_versions
BEGIN
    -- Both the run being written from and the run being written to must exist, be
    -- feasible, carry this manifest's snapshot, and be sealed, so a manifest row can
    -- never be moved onto an ineligible run. This is the Decision 020 section 8.2
    -- OLD-and-NEW correction, applied here from the start rather than inherited. The
    -- explicit NOT EXISTS form fails closed on a missing run, where migration 0009's
    -- (SELECT run_state ...) <> 'running' form would yield NULL and never fire.
    SELECT RAISE(ABORT,
        'pilot manifest update requires an existing feasible selection run whose snapshot matches and whose selection_result_sha256 is sealed')
    WHERE NOT EXISTS (
            SELECT 1 FROM pilot_selection_runs
            WHERE selection_run_id = OLD.selection_run_id
              AND snapshot_id = OLD.snapshot_id
              AND run_state = 'feasible'
              AND selection_result_sha256 IS NOT NULL)
       OR NOT EXISTS (
            SELECT 1 FROM pilot_selection_runs
            WHERE selection_run_id = NEW.selection_run_id
              AND snapshot_id = NEW.snapshot_id
              AND run_state = 'feasible'
              AND selection_result_sha256 IS NOT NULL);
    -- Manifest identity is immutable in all six of its fields: the content-derived
    -- manifest_id, the manifest_schema_version and run identity that root_manifest_sha256
    -- binds, and the ordinal_version and supersedes_manifest_id that the manifest_id
    -- preimage binds. IS NOT is NULL-safe throughout, so a nullable
    -- supersedes_manifest_id cannot yield NULL and silently skip this check. Rewriting
    -- all six identically stays permitted, so an idempotent restatement is a no-op
    -- rather than a failure.
    SELECT RAISE(ABORT,
        'pilot manifest identity is immutable: manifest_id, manifest_schema_version, selection_run_id, snapshot_id, ordinal_version, and supersedes_manifest_id may never change once inserted')
    WHERE NEW.manifest_id             IS NOT OLD.manifest_id
       OR NEW.manifest_schema_version IS NOT OLD.manifest_schema_version
       OR NEW.selection_run_id        IS NOT OLD.selection_run_id
       OR NEW.snapshot_id             IS NOT OLD.snapshot_id
       OR NEW.ordinal_version         IS NOT OLD.ordinal_version
       OR NEW.supersedes_manifest_id  IS NOT OLD.supersedes_manifest_id;
END;
```

**Block 5 — `pilot_manifest_versions_replacement_guard`** (new at v0.4)

```sql
CREATE TRIGGER pilot_manifest_versions_replacement_guard
BEFORE INSERT ON pilot_manifest_versions
BEGIN
    -- SQLite resolves an INSERT OR REPLACE conflict by deleting the conflicting row
    -- and inserting the new one. That implicit delete does not fire migration 0009's
    -- pilot_manifest_versions_no_delete trigger unless PRAGMA recursive_triggers is
    -- on, and this project never enables it, so replacement semantics would rewrite a
    -- manifest row wholesale -- identity, lineage, every component hash and the root
    -- alike -- while the BEFORE UPDATE identity guard never runs at all. A BEFORE
    -- INSERT trigger fires before conflict resolution can delete anything, so each
    -- predicate below holds on every connection whatever the pragma settings are.
    --
    -- Route 1 -- the TEXT PRIMARY KEY.
    SELECT RAISE(ABORT,
        'pilot manifest insert conflicts with an existing manifest_id; a manifest row is never replaced, and an identical replay must reconstruct and compare instead')
    WHERE EXISTS (
        SELECT 1 FROM pilot_manifest_versions
        WHERE manifest_id = NEW.manifest_id);
    -- Route 2 -- UNIQUE (selection_run_id, snapshot_id, ordinal_version).
    SELECT RAISE(ABORT,
        'pilot manifest insert conflicts with an existing ordinal version for this selection run and snapshot; a manifest row is never replaced')
    WHERE EXISTS (
        SELECT 1 FROM pilot_manifest_versions
        WHERE selection_run_id = NEW.selection_run_id
          AND snapshot_id = NEW.snapshot_id
          AND ordinal_version = NEW.ordinal_version);
    -- Route 3 -- the partial unique index uq_pilot_manifest_single_active_approval,
    -- which admits one owner_approved manifest per run and snapshot. Without this
    -- predicate an INSERT OR REPLACE carrying manifest_state 'owner_approved' would
    -- delete an already approved manifest and stand in its place under a different
    -- manifest_id, ordinal_version and root_manifest_sha256.
    SELECT RAISE(ABORT,
        'pilot manifest insert conflicts with the existing owner-approved manifest for this selection run and snapshot; an approved manifest is never replaced')
    WHERE NEW.manifest_state = 'owner_approved'
      AND EXISTS (
        SELECT 1 FROM pilot_manifest_versions
        WHERE selection_run_id = NEW.selection_run_id
          AND snapshot_id = NEW.snapshot_id
          AND manifest_state = 'owner_approved');
END;
```

**Block 6 — `pilot_selection_run_replacement_guard`** (new at v0.5)

```sql
CREATE TRIGGER pilot_selection_run_replacement_guard
BEFORE INSERT ON pilot_selection_runs
BEGIN
    -- A selection run is created once and never re-created. SQLite resolves an
    -- INSERT OR REPLACE conflict by deleting the conflicting row and inserting the
    -- new one, and that implicit delete fires no BEFORE DELETE trigger unless PRAGMA
    -- recursive_triggers is on, which this project never sets -- so without this
    -- predicate a replacement would silently clear a sealed selection_result_sha256,
    -- or repoint the run at another snapshot or input digest, while trigger 2 never
    -- ran. Both unique routes on this table (the selection_run_id PRIMARY KEY and
    -- UNIQUE (selection_run_id, snapshot_id)) require a matching selection_run_id, so
    -- this single EXISTS covers every constructible replacement conflict, and it
    -- refuses an ordinary duplicate INSERT and an INSERT OR IGNORE too rather than
    -- letting either pass silently. A genuinely new run is unaffected.
    SELECT RAISE(ABORT,
        'pilot selection run already exists for this selection_run_id; a run row is never replaced or re-inserted, and an identical replay must look up, reconstruct, and compare instead')
    WHERE EXISTS (
        SELECT 1 FROM pilot_selection_runs
        WHERE selection_run_id = NEW.selection_run_id);
END;
```

**Block 7 — `pilot_selection_run_delete_guard`** (new at v0.5)

```sql
CREATE TRIGGER pilot_selection_run_delete_guard
BEFORE DELETE ON pilot_selection_runs
BEGIN
    -- Selection runs are permanent in every state. There is no S6-authorized deletion
    -- lifecycle: a planned, running, failed, infeasible, infeasible_or_unproven, or
    -- feasible run is history, and a feasible sealed run additionally carries the
    -- terminal result digest a manifest is built over. This mirrors migration 0009's
    -- pilot_manifest_versions_no_delete and is unconditional -- no child-row or
    -- foreign-key test is involved -- so it holds on every connection whatever the
    -- pragma settings are, and it closes replacement-driven deletion as well as a
    -- direct DELETE.
    SELECT RAISE(ABORT,
        'pilot selection runs are undeletable in every run state; there is no authorized deletion lifecycle');
END;
```

**Block 8 — `pilot_selection_run_identity_guard`** (new at v0.5)

```sql
CREATE TRIGGER pilot_selection_run_identity_guard
BEFORE UPDATE OF selection_run_id, snapshot_id, selection_input_sha256
ON pilot_selection_runs
BEGIN
    -- Run identity is immutable from the moment the row exists. selection_run_id is
    -- content-derived (Decision 018 section 26), snapshot_id names the frozen snapshot
    -- the run consumed, and selection_input_sha256 is an input to the section 6.1
    -- selection_result_sha256 preimage -- so a mutable copy of any of the three can
    -- silently falsify a sealed terminal digest against its own preimage. Migrations
    -- 0009 to 0012 name none of these columns in any trigger, and foreign keys guard
    -- only the first two, only on a run that already has child rows, and only while
    -- PRAGMA foreign_keys is on. IS NOT is NULL-safe throughout, and rewriting all
    -- three identically stays permitted, so an idempotent restatement is a no-op
    -- rather than a failure.
    SELECT RAISE(ABORT,
        'pilot selection run identity is immutable: selection_run_id, snapshot_id, and selection_input_sha256 may never change once inserted')
    WHERE NEW.selection_run_id       IS NOT OLD.selection_run_id
       OR NEW.snapshot_id            IS NOT OLD.snapshot_id
       OR NEW.selection_input_sha256 IS NOT OLD.selection_input_sha256;
END;
```

### 15.2 Rulings these guards freeze

- **Every guard that references another table fails closed when the referenced run does not exist.**
  Blocks 3 and 4 use an explicit `NOT EXISTS (… AND run_state = 'feasible' AND selection_result_sha256 IS NOT NULL)`
  predicate, which is true — and therefore aborts — when the run is missing, when the snapshot does
  not match, when the state is not `feasible`, and when the seal is absent. Migration `0009`'s
  `(SELECT run_state …) <> 'running'` form yields SQL `NULL` for a missing run and never fires; that
  three-valued-logic path does not exist here. Foreign keys remain enabled and required — this makes
  the triggers correct when reasoned about independently, not a substitute for them.
- **The result digest is append-once on the `INSERT` and `UPDATE` paths** (widened at v0.2;
  **claim narrowed and made accurate at v0.4** — see the residual below). Block 1 refuses any
  `INSERT` carrying a non-`NULL` `selection_result_sha256`, so a run cannot be created already
  sealed and a sealed run can only ever be one that transitioned to `feasible` under migration
  `0009`'s and `0012`'s guards. Block 2 then permits `NULL → non-NULL` only while the run is
  `feasible` both before and after the write; a sealed value may neither change nor return to
  `NULL`; and rewriting the **identical** value stays permitted, so a recompute-and-reseal replay is
  idempotent rather than a failure. `IS` / `IS NOT` are used throughout so no NULL comparison can
  silently skip a check. **v0.1's "append-once" claim held on the `UPDATE` path only; that is the
  gap block 1 closes.**
- **v0.5 closes the residual v0.4 could not.** v0.2 and v0.3 claimed the seal was append-once on
  every write path while a row-replacement path on `pilot_selection_runs` that blocks 1 and 2 cannot
  reach was still open; v0.4 narrowed the claim and recorded the residual at §19.11. **Triggers 6, 7,
  and 8 close it**, so §15.5 now states the unqualified guarantee and §19.11 is marked **CLOSED**.
- **Trigger 6 closes run replacement on every route.** Like trigger 5, it is a `BEFORE INSERT`
  trigger, so `RAISE(ABORT)` fires **before** SQLite performs conflict resolution and no implicit
  delete ever happens. One `EXISTS` on `selection_run_id` suffices because both unique routes on the
  table require a matching value there — so a replacement arriving with a different `snapshot_id` or
  `selection_input_sha256` is refused by the same predicate. It also refuses a plain duplicate
  `INSERT` and an `INSERT OR IGNORE`, because silently doing nothing would let a caller believe it
  had created a run it had not. **A genuinely new unsealed run is untouched**, and trigger 1's
  pre-sealed-`INSERT` rule is unaffected: the two triggers are independent and both must pass.
- **Trigger 7 closes deletion unconditionally.** It mirrors migration `0009`'s
  `pilot_manifest_versions_no_delete` and tests nothing at all — no child row, no foreign key, no run
  state — so it holds in `planned`, `running`, `feasible` unsealed, `feasible` sealed, `failed`,
  `infeasible`, and `infeasible_or_unproven` alike, and on every connection regardless of pragmas.
  There is no S6-authorized deletion lifecycle for a selection run; a run is history in every state.
- **Trigger 8 closes identity mutation, and stays a separate trigger deliberately.** It names the
  **three persisted** identity columns and holds them with NULL-safe `IS NOT`, permitting an
  identical three-field restatement as an idempotent no-op exactly as trigger 4 does on the manifest
  side. **Trigger 2 was deliberately not widened to carry this rule**: the seal lifecycle and run
  identity are independent invariants, and folding them together would have left a trigger named for
  the result hash silently enforcing identity, breaking the one-responsibility-per-trigger shape that
  makes §15's table, §20's obligations, and the trigger names readable. `selection_input_schema_version`
  is **not** in the column list because it is not a column on this table at all (§3.6); it is
  immutable by absence and enters §6.1 and §8.4 as the accepted code constant
  `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION`.
- **None of the three depends on a pragma.** Refusal was verified under all four combinations of
  `recursive_triggers` ∈ {0, 1} and `foreign_keys` ∈ {0, 1} (§15.4). This matters because the run
  table has **no** delete guard of its own, so unlike the manifest table it was not even protected
  when `recursive_triggers` was on.
- **Trigger 5 closes the manifest replacement path on all three uniqueness routes** (new at v0.4).
  A `BEFORE INSERT` trigger fires **before** SQLite performs conflict resolution, so
  `RAISE(ABORT)` prevents the implicit delete rather than reacting to it. Each route is a separate
  explicit `EXISTS` predicate with its own message, and **none depends on a pragma**: refusal was
  verified under all four combinations of `recursive_triggers` ∈ {0, 1} and `foreign_keys` ∈ {0, 1}
  (§15.4). This matters because the pre-existing `pilot_manifest_versions_no_delete` trigger only
  covers the replacement path when `recursive_triggers` is on, and nothing in this repository ever
  turns it on.
- **Trigger 5 preserves every legitimate write.** A genuinely new `proposed` manifest has a fresh
  content-derived `manifest_id` and a fresh `(selection_run_id, snapshot_id, ordinal_version)`
  triple, so all three predicates are false. An ordinal-2 successor declaring its predecessor at
  `INSERT` (§9.2) inserts normally. `proposed → owner_approved` and `owner_approved → superseded` are
  `UPDATE`s and never reach a `BEFORE INSERT` trigger. Route 3's predicate is additionally guarded by
  `NEW.manifest_state = 'owner_approved'`, so it cannot fire on the only state S6 ever writes.
- **Trigger 5 makes an identical-content replay fail closed rather than silently rewrite.** Re-running
  S6 over a run that already has its manifest is refused at the schema layer, which is why §11.3 and
  §12 require replay to **read, reconstruct, compare, and return** instead. `INSERT OR IGNORE` is
  refused for the same reason: silently doing nothing would let a caller believe it had written a
  manifest it had not. Verified in §15.4.
- **The pre-existing row survives every refused attempt byte-for-byte.** Because the abort happens
  before conflict resolution, no delete is ever performed and no column of the existing row — least
  of all an `owner_approved` row's `root_manifest_sha256` and `approved_root_sha256` — is touched.
  §15.4 asserts full-row equality after each of the twelve refused replacement probes.
- **Sealing cannot ride along with the terminal transition.** A single statement setting both
  `run_state = 'feasible'` and `selection_result_sha256` fires block 2 with `OLD.run_state` still
  `running`, and aborts. The seal is therefore always a separate, later write over an already-terminal
  run — which is what makes §11.3's separate sealing transaction the only lawful shape.
- **Block 4 checks both the OLD and the NEW referenced run**, and additionally holds all six identity
  columns immutable with NULL-safe `IS NOT`. This applies the Decision 020 §8.2 correction from the
  outset rather than repeating the 2026-07-29 defect: an OLD-only predicate would let a manifest row
  be moved onto an ineligible run after the insert guard had already passed. Rewriting all six
  identically is permitted, so an idempotent restatement is a no-op.
- **The legitimate manifest lifecycle is untouched.** `proposed → owner_approved` and
  `owner_approved → superseded` name none of the six identity columns in their `SET` lists, so block 4
  does not fire on them; migration `0009`'s existing four manifest triggers continue to govern state
  transitions, hash immutability, supersession, and deletion. The one behavioural consequence is
  §9.2's: a successor declares `supersedes_manifest_id` at `INSERT`, which
  `pilot_manifest_supersession_requires_successor` accepts unchanged.

### 15.3 Normative digests

Lowercase SHA-256 over the exact UTF-8 bytes of each block, LF line endings, **including each
block's trailing newline**.

**Concatenation rule, stated exactly and unchanged since v0.3:** the statement region is the
**eight** blocks in the order above, each block already ending in a newline, **joined by exactly one
blank line** — that is, `"\n".join(blocks)`, which inserts a single `\n` between consecutive blocks
and adds nothing before the first or after the last. The region is **10939 bytes over 186 lines**.

| Block | Object | Bytes | Lines | SHA-256 |
|---|---|---:|---:|---|
| 1 | `pilot_selection_run_insert_unsealed_guard` | 743 | 12 | `f805f666be223cdaf7d5b29fdbd1bec8709f9ba3c71fd8e46f419ca35ab3b850` |
| 2 | `pilot_selection_run_result_hash_guard` | 1143 | 20 | `e2e44785a6b123e3eef87314c8e8d4d24b75fb3b3ffef3c6adde763dcfd940f2` |
| 3 | `pilot_manifest_versions_insert_guard` | 500 | 12 | `495a1c43e7a1e542f9464c86e18900a5a161aa84dc85bee55fb7d7e5f86394fb` |
| 4 | `pilot_manifest_versions_identity_guard` | 2601 | 41 | `1a376c1b37317ec0fc9dc697a69370f54a09cf0124942c742ea9a984c838cb98` |
| 5 | `pilot_manifest_versions_replacement_guard` | 2445 | 40 | `21d8cc57090c35ac3624e908a98759112623f7be4347df15ea0a5bce20b5c97e` |
| 6 | `pilot_selection_run_replacement_guard` | 1343 | 20 | `fb43032dd3c2c868428539ac5eb7fed98bef8bad39318014ddd34f0eec26b424` |
| 7 | `pilot_selection_run_delete_guard` | 843 | 14 | `879459ec7dbde300ce586c9d51c3aa32208e5c44719c8fce177465f942536448` |
| 8 | `pilot_selection_run_identity_guard` | 1314 | 20 | `167f7a891728250b04f3637562fe5526d0cf997ea9ae098e97be71e8611b7eef` |
| — | **exact concatenation (statement region)** | **10939** | **186** | `7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595` |

**Withdrawn as compositions, and not to be reproduced in the migration, in a test, or in any status
file:**

- **the whole v0.4 five-block statement region** — its five-block composition, its **7436**-byte and
  **129**-line counts, and its concatenation digest
  `6bfb897cc0db1b870d67546dc8ce5937741fbef542d6c2f940f2928c0c9a6c40`;
- **the whole v0.3 four-block statement region** — its four-block composition, its **4990**-byte and
  **88**-line counts, and its concatenation digest
  `51151767895eee673997331d4e8a3153836a31738c094c152340320021449edc`;
- **the whole v0.1 three-block statement region**, its concatenation digest `19cd847b…`, and its
  block-3 digest `68192eff…`.

A statement region containing three, four, or five `CREATE TRIGGER` blocks is by itself a defect,
whatever its digest.

**Blocks 1–5 carry forward the per-block digests they carried at v0.4, because the v0.5 ruling
changed none of their bytes** — it appends three triggers, it does not restate the existing five, and
it neither widens nor renames trigger 2. **Their individual digests are not withdrawn**; only the
five-block *composition* is. The eight per-block digests above are the complete set of valid block
digests, and `7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595` is the only valid
region digest. An implementation reproduces all nine values; reproducing the withdrawn 7436/129
region means blocks 6, 7, and 8 are missing.

### 15.4 Verification already performed on this SQL

Executed against scratch catalogs built by the accepted `0001`–`0012` chain on SQLite 3.53.3, using
the bytes **extracted from this record**, never a rewrite. No repository file and no production
catalog was written; every catalog was a temporary directory discarded on exit.

- **DDL effect:** the statement region added exactly the **eight** named triggers and **removed or
  altered nothing** — `objects removed: []`, **no existing object's `sql` text changed**,
  `sqlite_master` **320 → 328**, and every added object is of type `trigger`. No table, index, or
  column created; migrations `0009`–`0012` byte-unchanged; no data statement, and
  `ops_schema_migrations` unchanged at 12 rows.
- **67 behavioural assertions, 67 as frozen.** Composition: 9 for block 1 (a pre-sealed `INSERT`
  refused in all six run states, an unsealed `INSERT` accepted in `planned`, `running`, and
  `feasible`); 10 for block 2 (sealing refused on all five non-`feasible` states individually,
  `NULL → value` accepted on `feasible`, an identical reseal accepted, a changed seal and a cleared
  seal refused, and a seal riding along with the `running → feasible` transition refused); 9 for
  block 3 (refused over a `feasible` but **unsealed** run, accepted over a `feasible` sealed run,
  refused over each of the five other run states, refused on a mismatched `snapshot_id`, refused on a
  missing run); 7 for block 4 (each of the six identity columns refused individually — including
  moving the manifest onto a *different but otherwise eligible* sealed `feasible` run, which proves
  the OLD-and-NEW check is load-bearing — plus an idempotent six-field restatement accepted and an
  operational `relative_manifest_path` update accepted); 3 lifecycle
  (`proposed → owner_approved`, a successor declaring its predecessor at `INSERT`, and
  `owner_approved → superseded`, all accepted); 2 pre-existing bypass checks (plain `DELETE` refused,
  a component-hash `UPDATE` refused); and **27 for block 5** (see below).
- **Block 5, adversarially — 27 assertions.** All three replacement routes refused under **all four**
  pragma combinations of `recursive_triggers` ∈ {0, 1} × `foreign_keys` ∈ {0, 1} (12 assertions), and
  after **each** refusal the pre-existing manifest row compared **byte-identical across every column**
  (12 assertions). Plus: a plain `INSERT` duplicating `manifest_id` refused; an identical-content
  `INSERT OR REPLACE` replay refused, so replay must reconstruct and compare (§11.3, §12); and
  `INSERT OR IGNORE` on a duplicate **refused rather than silently ignored**, which is the fail-closed
  behaviour this record wants. Route 3's probe replaced an `owner_approved` manifest with a different
  root under a different `manifest_id` and `ordinal_version` — accepted under the four-trigger v0.3
  region, refused under the five-trigger v0.4 region, with the approved row unchanged.
- **Blocks 6, 7, and 8, adversarially — 223 assertions in total, all as frozen (v0.5).** The whole
  battery was re-run against the bytes **extracted from §15.1 of this record**, not a rewrite, and
  every prior block 1–5 assertion still passes. Added at v0.5, each under **all four** combinations
  of `recursive_triggers` ∈ {0, 1} × `foreign_keys` ∈ {0, 1}:
  - **Replacement (block 6), refused in every form** — a plain duplicate `INSERT`; an
    `INSERT OR IGNORE` on a duplicate; and an `INSERT OR REPLACE` carrying the **same** sealed
    digest, a **changed** digest, and **omitting** the digest, as well as one changing `snapshot_id`
    and one changing `selection_input_sha256`. Also refused over a run in **each of the six run
    states**. Insertion of a genuinely new unsealed run stays accepted in `planned`, `running`, and
    `feasible`, and block 1's pre-sealed-`INSERT` refusal still holds in all six states.
  - **Deletion (block 7), refused in every state** — `planned`, `running`, `feasible` unsealed,
    `feasible` sealed, `failed`, `infeasible`, and `infeasible_or_unproven`.
  - **Identity (block 8), refused per field** — `selection_run_id`, `snapshot_id`, and
    `selection_input_sha256` each rejected individually on a `feasible`, sealed run, while an
    identical three-field restatement is accepted as an idempotent no-op.
  - **Byte preservation** — after **every** refused replacement, deletion, and identity update, the
    full run row compared **byte-identical across all 18 columns**, asserted per route, per state,
    per field, and per pragma combination.
  - **Manifest regression** — blocks 3, 4, and 5 behave exactly as at v0.4 with blocks 6–8 present,
    including the manifest replacement route refused under all four pragma combinations with the
    manifest row byte-identical after each, and `proposed → owner_approved`, an ordinal-2 successor
    declaring its predecessor at `INSERT`, and `owner_approved → superseded` all still accepted.
  - **Accepted-path neutrality** — `planned → running` and the accepted count and node-count `UPDATE`
    both still accepted (§3.4).
- **The Stage-S4 draft, end to end.** A permanently-`running` entity-only draft with 24 selected
  entities was built through the real lifecycle and probed: promotion to `feasible` refused by
  migration `0012`'s disposition-completeness trigger, sealing refused by block 2, and a manifest over
  it refused by block 3. The exclusion holds at **three** independent layers.

### 15.5 The append-once and identity guarantee (v0.5)

With triggers 1, 2, 6, 7, and 8 applied, the following holds **without qualification** for
`pilot_selection_runs`. Every clause is probe-supported under all four combinations of
`recursive_triggers` ∈ {0, 1} × `foreign_keys` ∈ {0, 1} (§15.4); **no clause rests on a pragma, on a
foreign key, on the presence of child rows, or on application discipline.**

1. **Every new run begins unsealed.** Block 1 refuses any `INSERT` carrying a non-`NULL`
   `selection_result_sha256`, in every run state.
2. **An existing run cannot be replaced.** Block 6 refuses a duplicate `INSERT`, an
   `INSERT OR IGNORE`, and an `INSERT OR REPLACE` — whether the incoming row carries an identical
   digest, a changed digest, or none — and whether or not it also changes `snapshot_id` or
   `selection_input_sha256`.
3. **A run cannot be deleted.** Block 7 aborts every `DELETE`, in every run state, unconditionally.
4. **The persisted run identity cannot change.** Block 8 holds `selection_run_id`, `snapshot_id`, and
   `selection_input_sha256` immutable from the moment the row exists.
5. **`NULL` → non-`NULL` sealing occurs only through the guarded update on an already-`feasible`
   run.** Block 2 permits it only when the run is `feasible` both before and after the write, so a
   seal can never ride along with the terminal transition.
6. **A sealed digest cannot change or clear.** Block 2's NULL-safe `IS NOT` predicate catches both.
7. **Identical digest restatement remains idempotent**, so a recompute-and-reseal replay is a no-op
   rather than a failure.
8. **The stored `selection_input_sha256` cannot be changed — before sealing or after.** Block 8
   guards the `UPDATE` path and block 6 the replacement path, so neither ordering evades it.
9. **`selection_result_sha256` is therefore append-once and remains recomputable from its persisted
   preimage across every direct SQLite write path** — `INSERT`, `UPDATE`, `INSERT OR REPLACE` /
   `REPLACE INTO`, `INSERT OR IGNORE`, and `DELETE`.

Clause 9 is the one that needed clauses 2, 3, 4, and 8 to be true first, and is why v0.4 could not
state it. §6.1's preimage reads `selection_input_sha256`, `snapshot_id`, and `selection_run_id` among
its fourteen fields. Making the seal merely unchangeable would have left it **append-once but
detached**: the row it was computed from could still be rewritten underneath it, so the digest would
survive while silently ceasing to recompute — and §11.2(3) requires exactly that recomputation before
a manifest may be built. Freezing the identity fields is what turns an immutable digest into a
**terminal identity**.

**`selection_input_schema_version` is covered by absence, not by a guard.** It is not a column on
`pilot_selection_runs` (§3.6), so no write path can reach it; it enters §6.1 and §8.4 as the accepted
code constant `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION`, and §11.2(4) already requires the run's
recorded policy versions to equal the accepted constants.

**What this guarantee does not claim.** It is a statement about direct SQLite write paths against the
persisted row. It does not speak to file-level tampering with the catalog, to a restore from a
different database, or to anything outside the schema — those remain the province of
`Docs/leakage_register.md`, the writer-exclusivity lease, and migration provenance.

## 16. Frozen ruling — no new surfaces

- **No new reason code.** `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` remains the only reserve code, and no
  manifest, integrity, retry, approximation, or substitution code may be added. Every manifest
  integrity violation is a `GateFailureError` (§11.2).
- **No new policy constant and no policy-reference migration.**
  `PILOT_MANIFEST_HASH_POLICY_VERSION` and its seeded `pilot_manifest_hash` row already exist.
- **No CLI, and this deliberately narrows the milestone plan** (owner correction F, v0.2). `cli.py`
  is unchanged and no S6 subcommand is authorized.
  [`Milestones/milestone_2_3_pilot_selection_plan.md`](../../Milestones/milestone_2_3_pilot_selection_plan.md)
  §16 scopes stage M2.3A-6 as "Manifest serialization, hashing, **and CLI output**". This record
  narrows that stage: **serialization, hashing, persistence, and verification stay at S6 exactly as
  §§6–13 fix them; CLI output is deferred to Stage S9**, where it lands together with the exact
  real-data manifest and the milestone plan §10 "command invocation" field that §13.2 defers with it.
  Nothing is dropped — a CLI over a fixture-only manifest would print a machine-generated example and
  invite it to be mistaken for a pilot sample, which is precisely the confusion §17 exists to
  prevent. The narrowing is recorded here rather than left implicit so that no later session reads
  the plan's stage table as authorizing an S6 CLI.
- **No projection-recovery writer.** `pilot_projection_recovery_events` stays unwritten.
- **No replacement, deletion, or identity SQL, anywhere in S6 (v0.4; extended at v0.5).** No S6
  module may issue `INSERT OR REPLACE`, `REPLACE INTO`, `INSERT OR IGNORE`, or any other
  conflict-resolution clause against `pilot_manifest_versions` or `pilot_selection_runs`; none may
  issue `DELETE` against either; and **none may name `selection_run_id`, `snapshot_id`, or
  `selection_input_sha256` in an `UPDATE … SET` list**. The store writes plain `INSERT` and plain
  `UPDATE` only, and the only run column it ever updates is `selection_result_sha256`. Idempotent
  replay reads, reconstructs, compares, and returns (§11.3, §12). §20 requires a test asserting the
  absence of every one of those statement forms in the S6 modules.
- **No change to S4 or S5**, no second selection, no reserve substitution, and no manifest transition
  beyond `proposed`.
- **No change to `paths.py`**, `cohorts.py`, `pilot_policy.py`, `reasons.py`, `release/hashing.py`,
  or `release/manifest.py`.

## 17. Frozen ruling — the Stage S7–S10 boundary

Stage S6 delivers **machinery and a document schema**, not a published pilot sample. **All four
later stages, in order** (owner correction F, v0.2 — v0.1 listed only three and omitted S7):

| Stage | Scope | Where the milestone plan defines it |
|---|---|---|
| **S7** | Gate F — live-metadata safety and allowlist: SEC identity configured and never echoed, metadata-only URL allowlist, accession-archive and filing-document routes denied, CompanyFacts disabled, network off by default, explicit live flag, printed request budget, zero-request dry run, two dry runs producing an identical plan hash | §11, Gate F ("Status: not started (Stage S7)") |
| **S8** | Real candidate metadata and the first live metadata run; Gate H pre-run recovery state | §16; §11, Gate H |
| **S9** | The exact frozen candidate snapshot, the real-data pilot manifest instance of the §13 schema, **and the CLI output deferred from S6 by §16** | §16 |
| **S10** | Owner approval of the exact `root_manifest_sha256`, which Decision 013 §8 makes the M2.3 completion condition | §16; §14 items 17–18 |

**None of the four is authorized by this record**, and none is reachable from the current state: no
candidate-snapshot builder exists and no production catalog exists (§3.4). A complete, correct Stage
S6 therefore produces a verifiable hash contract, a complete document schema proven against
fixtures, and at most a `proposed` manifest over fixture data. **Milestone 2 cannot accidentally
publish a research result**, because there is no real snapshot to manifest and no code path that
approves one.

**The full Milestone 2 integrated Opus Max review occurs only after Stage S10** — after the final
M2.3 stage and the exact owner-approved manifest — **not after S6**, and not after S7, S8, or S9.

## 18. What this record does not change

Unchanged and not reopened: the Decision 013 §5 objective and its term order; the Decision 018 quota
set, roles, caps, floors, amendment families, evidence penalties, node-limit and failure semantics,
and retry prohibition; the Decision 019 mappings; the Decision 020 reserve architecture, membership
semantics, signature model, `0012` SQL, and five accepted limitations; every policy constant;
`ACCESSION_SELECTION_INPUT_SCHEMA_VERSION`; every existing reason code; migrations `0009`–`0012`; the
S4 entity-only draft; and the immutable `m2.3-s5-complete` and `m2.3-s5.4-complete` checkpoints.

## 19. Accepted limitations

Recorded for monitoring. Each is a consequence of a ruling above, not a defect, and none requires an
implementation change.

1. **The six S5-era limitations carry forward unchanged** — the five in Decision 020 §19.1
   (cross-anchor amendment-family attribution; provenance-oriented union member sets; exact
   target-selected versus complete-replacement bundle comparison; count-based signature contribution
   values; the nonblocking schema-layer subset/superset/empty transition-test observation) plus the
   nonblocking redundant vacuous assertion. **None affects terminal hashing or release eligibility:**
   each changes which rows exist, and Stage S6 hashes the rows as persisted.
2. **`candidate_tables_sha256` binds the snapshot's declared component digests, not recomputed
   candidate tables** (§8.2). Until a snapshot builder exists there is no accepted derivation to
   recompute against, and recomputing would be a second implementation. Candidate row content is
   independently bound through `selection_input_sha256`.
3. **`node_limit_exhausted` is a constant `0` in the result preimage** on any `feasible` run (§6.2).
   It is retained deliberately as a defensive field.
4. **The four terminal component digests appear at two layers** (§10, exclusion 8). This is an
   intentional diamond, not redundancy to be optimized away.
5. **Reserve child rows are hashed both directly and, transitively, through `reserve_package_id`**
   (§7.4). Deliberate, for corruption localization.
6. **A `feasible` run that never receives a manifest still carries a sealed
   `selection_result_sha256`.** The seal is a deterministic checkpoint of terminal content; it is
   **not** a publication, not an approval, and not a release artifact.

Added at v0.2:

7. **The six explicit §8.4 arguments are asserted, not verified.** `dependency_lock_sha256`,
   `code_commit_identifier`, `runtime_python_version`, `configuration_sha256`,
   `decision_authority_sha256`, and `source_plan_sha256` are caller-supplied. S6 binds them
   immutably into `selector_policy_sha256` and therefore into the root, so a wrong value is
   permanently attributable — but S6 cannot detect one, because detecting it would mean reading the
   Git tree, the interpreter, the config, the decision directory, or the plan, which §8.4 prohibits
   outright. This is the deliberate trade: an auditable assertion beats a value silently inherited
   from whatever environment happened to run the code.
8. **What the structural fingerprint excludes, stated accurately** (§8.1). *This replaces the v0.2
   limitation, which claimed `observed_type` and `record_path` were unbound. That claim is
   **withdrawn**: owner correction D at v0.3 binds both, and **all five substantive structural fields
   — `region`, `state`, `observed_type`, `member_name`, `record_path` — are bound.*** What the rule
   genuinely excludes, and why each exclusion is intended rather than a gap:
   - **`parser_run_id` is used only for cross-run consistency checking and is excluded from
     identity.** It partitions the rows (step 1) and drives the equality requirement and its
     fail-closed branch (steps 4–5), but it never enters the digest (step 7). Which run observed the
     shape, and how many runs did, are operational facts.
   - **Duplicate identical structural rows are collapsed**, because step 3 reduces each parser run to
     a *set*. Observing the same shape twice is the same shape.
   - **Row order is excluded**, both by the set reduction and by `hash_table` sorting rendered rows.
   - **The per-row identity, count, count-quality, free-text, and timestamp columns are excluded** as
     the §8.1 classification table records: `structural_observation_id`, `source_observation_id`,
     `row_count`, `count_is_trustworthy`, `is_genuine_zero`, `reason_codes_json`, `detail`,
     `raw_excerpt`, `recorded_at_utc`. These are volume, provenance, and prose, not shape.

   Recorded for monitoring, not for change. Nothing here weakens drift detection: a change to any of
   the five bound fields changes the fingerprint, and a disagreement between parser runs on any of
   the five fails closed.
9. **The `leakage_attestation` literal records a claim; it does not prove one** (§8.4.1). Its truth
   rests on the S6 read set and the §20 test, not on the constant.
10. **The v0.2 identity guard makes the existing `test_m23_pilot_schema.py` manifest fixtures
    materially heavier**, not merely adjusted — see §20's foreseeable bounded consequence. This is
    expected and is not grounds for weakening any guard.

Added at v0.4:

11. **CLOSED at v0.5 — `pilot_selection_runs` replacement, deletion, and identity mutation.**
    Recorded at v0.4 as an open owner-facing finding, and **resolved by owner ruling** with triggers
    6, 7, and 8. Retained here as the audit trail rather than as a live limitation.

    v0.4 scoped trigger 5 to `pilot_manifest_versions` and left the structurally identical routes on
    `pilot_selection_runs` open — worse than the manifest case, because that table had **no delete
    guard at all** and so was not even protected when `recursive_triggers` was on. §3.6 records the
    probes: `INSERT OR REPLACE` omitting the seal cleared it, a plain `DELETE` removed the run, and
    `selection_run_id`, `snapshot_id`, and `selection_input_sha256` were each rewritable by direct
    `UPDATE` — the last in every shape under every pragma setting. Foreign keys did not help, since
    a replacement reinstates the same key values inside the statement.

    Closing it required a count the v0.4 correction had fixed at five, so the v0.4 review stopped and
    referred it rather than widening an owner-frozen ruling (Decision 018 §25; Decision 020 §8.2).
    The project owner then authorized three further triggers. **Trigger 2 was deliberately not
    widened**, so the seal lifecycle and run identity remain separate, independently testable
    invariants. §15.5 states the resulting unqualified guarantee, and §15.4 records the 223
    assertions supporting it.

## 20. Test obligations

Required once Stage S6 is separately authorized. These extend, and do not replace, the accepted
suites.

- **Determinism and permutation invariance:** every digest is stable across repeated computation and
  invariant under SQLite retrieval order and row-insertion order.
- **Sensitivity, per component:** changing any single hashed column in any family changes exactly the
  digests that column feeds, and changes the root.
- **Exclusion proofs:** mutating `recorded_at_utc`, `generated_at_utc`, `detail`, `relative_manifest_path`,
  `ordinal_version`, `manifest_state`, an approval field, or an event ID changes **no** digest.
- **Column-order normativity:** the frozen column tuples are asserted literally, so a silent
  reordering is caught.
- **Circularity:** `selection_result_sha256` is provably absent from its own preimage and from every
  component; no digest reads `pilot_manifest_versions`; the diamond in §10 is asserted explicitly.
- **Eligibility, adversarially:** each of the seven §11.2 conditions refused independently — missing
  run; `running`, `failed`, `infeasible`, and `infeasible_or_unproven` runs; `NULL` seal; a seal that
  does not recompute; a wrong input-schema or policy version; a mismatched or non-`frozen` snapshot;
  the S4 draft specifically; and each component hash failing to recompute.
- **Nonblocking dispositions:** a run whose reserve position includes
  `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` is manifest-eligible, and its dispositions are inside
  `reserves_sha256`.
- **Proposed-only:** no code path produces `owner_approved`, populates `approved_root_sha256`, sets
  `supersedes_manifest_id`, rejects a manifest, or issues any `UPDATE` naming one of the six
  immutable identity columns (§9.2).
- **Manifest identity immutability (v0.2):** each of the six §9.2 fields refused independently at the
  schema layer; an identical six-field restatement accepted as an idempotent no-op; a successor
  declaring `supersedes_manifest_id` at `INSERT` accepted; `proposed → owner_approved` and
  `owner_approved → superseded` provably unaffected by trigger 4.
- **Append-once on every write path (v0.2):** a pre-sealed `INSERT` refused in the `planned`,
  `running`, and `feasible` shapes; an unsealed `INSERT` accepted; a seal riding along with the
  `running → feasible` transition refused; the accepted S4 and S5 `INSERT` column lists provably
  unaffected.
- **Document completeness (v0.2, §13.3):** an assertion enumerating **every** serialized leaf of the
  §13.2 document and mapping it to the digest that binds it, so a field added later without a binding
  fails the suite; plus a proof that `manifest_id` recomputes from the rendered document and that
  `root_manifest_sha256` recomputes from its substantive content.
- **Document schema, per block (v0.2):** all **thirteen** §13.2 blocks present and populated over
  fixtures.
- **The exhaustive §10 crosswalk, item by item (v0.4, §13.2.1).** Five proofs, each required:
  1. **the item table is asserted literally** — all **81** atomic items, each with its §10 wording,
     block, committing digest, and classification, so a silent reclassification, renumbering, or
     deletion fails the suite;
  2. **the six counts are asserted** — `total = 81`, `D = 42`, `T = 30`, `X = 8`, `S9 = 1`,
     `S10 = 0`, together with `D + T + X + S9 + S10 == total` and **`unclassified == 0`**;
  3. **every D and T item is present in the rendered document** at the granularity §10 requires, and
     every X item is **provably absent** from the document's substantive body;
  4. **every T item's covering digest is sensitive to it** — changing the persisted value changes the
     named component digest and the root (§13.3 step 1) — and **every D and T item's rendered value
     is compared against its recorded reconstruction source** (§13.3 step 2), the two halves asserted
     separately;
  5. **the single S9 deferral is exactly item 80** (command invocation), and the retrieval envelope
     is recoverable from `census_source_observations` by the bound `source_id` and `request_identity`.
- **`manifest_state` as a fixed literal (v0.4, §13.2.2):** the implementation refuses to build an S6
  document for any state other than `proposed` with `GateFailureError`, and the literal is serialized
  rather than read.
- **Blocks 6, 7, and 8 — the selection-run guarantee, adversarially (v0.5, §15, §15.5).** Six proofs,
  each required, and each asserted under **all four** combinations of `recursive_triggers` ∈ {0, 1}
  and `foreign_keys` ∈ {0, 1} so that **no pragma is required for correctness**:
  1. **replacement refused in every form** — a plain duplicate `INSERT`; an `INSERT OR IGNORE`; and
     an `INSERT OR REPLACE` carrying an identical digest, a changed digest, and omitting the digest,
     plus one changing `snapshot_id` and one changing `selection_input_sha256`; and refused over a
     run in **each of the six run states**;
  2. **deletion refused in every run state** — `planned`, `running`, `feasible` unsealed, `feasible`
     sealed, `failed`, `infeasible`, `infeasible_or_unproven` — with no child row present, proving
     the guard is unconditional rather than foreign-key-derived;
  3. **each of the three persisted identity fields refused independently**, and an identical
     three-field restatement accepted as an idempotent no-op;
  4. **the run row byte-identical across all 18 columns after every refused replacement, deletion,
     and identity update**, asserted per route, per state, per field, and per pragma combination;
  5. **the nine §15.5 clauses proven as a set**, including that a sealed `selection_result_sha256`
     still recomputes from its persisted §6.1 preimage after every refused write — recomputability,
     not merely immutability;
  6. **valid behaviour preserved** — a genuinely new unsealed run still inserts in `planned`,
     `running`, and `feasible`; block 1 still refuses a pre-sealed `INSERT` in all six states;
     sealing an already-`feasible` unsealed run and identical resealing both still succeed; and the
     accepted S4 and S5 `INSERT` and `UPDATE` patterns, including `planned → running` and the
     count/node-count update, are provably unaffected.
- **`selection_input_schema_version` is not a run column (v0.5):** asserted literally, so a later
  session cannot read trigger 8's three-column list as an omission, together with a proof that the
  accepted constant `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` is what §6.1 and §8.4 bind.
- **Block 5 and the manifest replacement path, adversarially (v0.4, §15).** Seven proofs, each
  required:
  1. each of the three uniqueness routes refused independently — the `manifest_id` primary key;
     `UNIQUE (selection_run_id, snapshot_id, ordinal_version)` under a different `manifest_id`; and
     the partial index `uq_pilot_manifest_single_active_approval`, replacing an **`owner_approved`**
     manifest under a different `manifest_id` and `ordinal_version`;
  2. all three refused under **all four** combinations of `recursive_triggers` ∈ {0, 1} and
     `foreign_keys` ∈ {0, 1}, so **no pragma is required for correctness**;
  3. after **every** refused attempt the pre-existing manifest row is **byte-identical across every
     column**, asserted per route and per pragma combination;
  4. a genuinely new `proposed` manifest still inserts, and an ordinal-2 successor declaring its
     predecessor at `INSERT` still inserts;
  5. `proposed → owner_approved` and `owner_approved → superseded` are provably unaffected;
  6. an identical-content `INSERT OR REPLACE` replay is refused, and the supported replay path
     instead reads, reconstructs, compares, and returns the existing manifest **without writing**
     (§11.3, §12); `INSERT OR IGNORE` on a duplicate is refused, not silently ignored;
  7. **no S6 module contains `INSERT OR REPLACE`, `REPLACE INTO`, `INSERT OR IGNORE`, or `DELETE`**
     against `pilot_manifest_versions` or `pilot_selection_runs`, and **no S6 module names
     `selection_run_id`, `snapshot_id`, or `selection_input_sha256` in an `UPDATE … SET` list**
     (§16).
- **Structural fingerprint (§8.1; five-column tuple frozen at v0.3).** Six proofs, each required:
  1. **an identical reparse is a digest no-op** — a second `parser_run_id` producing the same
     five-column set leaves the fingerprint, `source_observation_set_sha256`, and the root
     **byte-identical**;
  2. **a duplicate identical structural row is a digest no-op**;
  3. **parser-run order and row order are irrelevant** — permuting either, and permuting SQLite
     retrieval order, leaves every digest unchanged;
  4. **disagreement between parser-run sets fails closed** with `GateFailureError`, and is never
     unioned, intersected, averaged, majority-voted, resolved by preferring a run, or discarded —
     asserted for a divergence in **each** of the five columns independently;
  5. **each of the five tuple fields is load-bearing** — changing `region`, `state`, `observed_type`,
     `member_name`, or `record_path` alone changes the fingerprint and the root, asserted per field;
  6. **no three-column fallback and no second fingerprint methodology exists** — the frozen
     five-column tuple is asserted literally, so a silent reversion to the withdrawn v0.2 form or a
     parallel shape derivation fails the suite.

  Plus: an observation with no structural rows yields the empty-set digest, distinct from any
  populated shape; and `NULL` versus empty-string `member_name` and `record_path` are distinguished.
- **No leakage surface (v0.2, §8.4.1):** no S6 module opens an outcome, filing-text, or CompanyFacts
  source, and the `leakage_attestation` literal is bound into `selector_policy_sha256`.
- **Explicit-argument discipline (v0.2, §8.4):** each of the six explicit arguments missing or
  malformed raises `GateFailureError`; no S6 module invokes Git, reads `.git`, shells out, reads
  `sys.version`, or consults an environment variable.
- **Atomicity:** an injected fault at any point rolls the whole manifest write back, leaving no row
  and no file; a partial manifest is unconstructible.
- **Serialization:** byte-identical re-serialization; sorted keys; LF; no absolute path anywhere in
  the document; the content-derived filename equals `root_manifest_sha256`; the rendered document and
  the persisted row agree.
- **Reconstruction and replay:** a corrupted seal, a corrupted component digest, and a corrupted root
  each raise `GateFailureError`; a same-ID S5 replay after sealing is byte-identical, writes nothing,
  and neither clears nor mutates the seal.
- **Migration `0013`, adversarially:** the **223** §15.4 assertions as repository tests; the
  statement region is **byte-faithful to §15.1** and reproduces the **nine** §15.3 digests — eight
  per-block plus the concatenation — together with the **10939**-byte count and the **186**-line
  count under the stated concatenation rule; the withdrawn v0.4 region digest `6bfb897c…`, the
  withdrawn v0.3 region digest `51151767…`, and the withdrawn v0.1 digests `19cd847b…` and
  `68192eff…` appear **nowhere**; the migration adds exactly **eight** triggers, creates no table,
  index, or column, and alters nothing existing — asserted as `objects removed: []`, no existing
  object's `sql` text changed, and `sqlite_master` 320 → 328; migrations `0009`–`0012` remain
  byte-identical; and the chain is contiguous, provenance-recorded, byte-immutable, and idempotent
  under rerun per repository convention.
- **The S4 draft at three layers (v0.2):** promotion refused by migration `0012`, sealing refused by
  block 2, and a manifest over it refused by block 3, each asserted independently.
- **Regression without editing:** the S5.1, S5.2, S5.4, S4, reserve, reason, catalog, release, and
  migration-provenance suites.

**Foreseeable bounded consequence, restated and enlarged at v0.2.**
`tests/unit/test_m23_pilot_schema.py` currently inserts `pilot_manifest_versions` rows through its
`_insert_manifest` helper against runs built by `_running_selection_run`. Under migration `0013`
those fixtures need three changes, and the third is the substantial one:

1. the referenced run must be `feasible` and sealed, not `running`;
2. the seal must be established by a **later `UPDATE`** on the already-`feasible` run, because
   trigger 1 refuses a pre-sealed `INSERT` and trigger 2 refuses a seal that rides along with the
   terminal transition;
3. reaching `feasible` through the real lifecycle requires what migrations `0009` and `0012` already
   demand of any feasible run — 24 selected entities with contiguous `selected_order`, matching
   declared counts, and exactly one reserve disposition per selected entity.

Tests that only need a manifest row over an eligible run may instead insert the run directly in
`run_state = 'feasible'` with `selection_result_sha256` left `NULL` and seal it by `UPDATE`, which
migration `0013` permits and which is how §15.4's probes were built. Either route is legitimate.
This is expected, is why that module is an authorized bounded-edit path in the stage contract, and is
**not** grounds for weakening any guard.

## 21. Implementation stop conditions

An implementation session must stop and report, without writing code, if any of the following is
true.

- **A live check finds this record not approved** in `Docs/Decisions/decision_registry.md`.
- **No separately issued bounded S6 implementation prompt has authorized the work.** This record,
  the stage contract, and `Milestones/STATUS.md` are not substitutes for it.
- **Migration `0013` as written differs in any way from the §15.1 SQL**, or a reinterpretation of it
  appears necessary, or its digests do not reproduce §15.3.
- **Any migration or DDL beyond `0013` appears genuinely necessary** — an owner-level schema
  conflict, never a widening.
- **A path outside the contract's authorized paths is genuinely required** — including
  `paths.py`, `pilot_policy.py`, `reasons.py`, `cli.py`, `release/hashing.py`, `release/manifest.py`,
  and every accepted S4/S5 module.
- **A digest preimage in §§6–9 appears wrong, incomplete, or unimplementable**, or a column exists
  that no frozen tuple classifies. Every column of every table §§6–9 read is now classified
  explicitly — `census_source_observations` and `census_structural_observations` in §8.1,
  `reference_policy_versions` in §8.4 — so this condition fires only on a genuine schema change.
- **A §13.2 document block cannot be populated from bound values**, or a serialized field would have
  to be carried that no digest commits (§13.3). Widening the document is an owner-level act, exactly
  as widening a preimage is.
- **A §13.2.1 crosswalk item cannot be placed as classified** — an item marked **D** or **T** whose
  value cannot be rendered from bound state, an item marked **X** that would have to be serialized,
  or any §10 requirement that appears to need a category the table does not give it. **A session may
  not reclassify an item, add a category, or change a count** (§13.3). Zero unclassified is a frozen
  property, not a target to be met by moving an item somewhere convenient.
- **Any of the nine §15.5 clauses cannot be reproduced** against the migration as written — in
  particular if a sealed `selection_result_sha256` does not still recompute from its persisted §6.1
  preimage after every refused write. §15.5 is stated without qualification, so a failure to
  reproduce it is a defect in the migration or in the schema, never a reason to soften the claim.
- **Any S6 module would need `INSERT OR REPLACE`, `REPLACE INTO`, `INSERT OR IGNORE`, or `DELETE`**
  against `pilot_manifest_versions` or `pilot_selection_runs`, **or would need to name
  `selection_run_id`, `snapshot_id`, or `selection_input_sha256` in an `UPDATE … SET` list** (§16).
  Idempotent replay reads, reconstructs, compares, and returns; it never replaces.
- **A ninth trigger or any further DDL appears necessary.** Migration `0013` is exactly eight
  triggers. Growing it again is an owner-level act (Decision 018 §25; Decision 020 §8.2), never a
  session's — as the v0.3, v0.4, and v0.5 rounds each demonstrated.
- **The structural fingerprint rule cannot be satisfied** — two parser runs over one cited
  observation disagree on their distinct
  `(region, state, observed_type, member_name, record_path)` sets (§8.1). That is a
  `GateFailureError` at run time and a stop condition at design time; it is never resolved by
  unioning, intersecting, averaging, preferring a run, dropping an observation, or **narrowing the
  tuple back toward the withdrawn v0.2 three-column form**.
- **Any of the six §8.4 explicit arguments is unavailable**, so that build, runtime, configuration,
  authority, or plan identity would have to be inferred instead of supplied.
- **Producing a manifest would require reading the S4 draft**, running a second selection, applying a
  reserve substitution, re-deriving any S5 rule, or relaxing an accepted S5 expected output.
- **Any instruction asks to** advance a manifest past `proposed`, populate an approval field, mutate
  one of the six immutable identity columns (§9.2), perform owner approval, publish an artifact, add
  a CLI surface (§16), begin live metadata retrieval, build a real candidate snapshot, begin Stage
  S7/S8/S9/S10, write `pilot_projection_recovery_events`, amend Decision 018 or 020, or commit before
  S6 acceptance.
- **Build identity would have to be inferred** from Git, the environment, or the working tree rather
  than supplied explicitly (§8.4).

## 22. Checkpoint boundary

The accepted `m2.3-s5-complete` and `m2.3-s5.4-complete` tags are **immutable** and are never moved,
replaced, re-pointed, or restated. The eventual Stage-S6 checkpoint is a **new annotated tag
`m2.3-s6-complete`** that **supplements** both. No commit, push, or tag is authorized before S6
acceptance and an explicit owner instruction. CLAUDE.md rule 13 applies independently.

## 23. Implementation authorization

**This record, though now accepted and binding, still authorizes no implementation by itself.**
Stage S6 implementation requires all of:

1. a **focused independent governance review of v0.5** of this record and of
   [`Milestones/contracts/m23_s6.md`](../../Milestones/contracts/m23_s6.md), covering the exact
   **eight-block** §15.1 SQL and its **nine** §15.3 digests, the **§15.5 append-once and identity
   guarantee** and its nine clauses, the **exhaustive 81-item milestone-plan §10 crosswalk in
   §13.2.1** and its frozen counts, every preimage in §§6–9 including the eleven-field §8.4
   selector-policy layer and the five-column §8.1 structural fingerprint, the §10 circularity
   exclusions and the §10.1 commitment closure, the §9.2 identity-immutability ruling, and the §13
   document contract — **NOT YET SATISFIED**.

   **The review must reach its own conclusion and may not inherit an earlier one.** Each earlier
   draft was a different object:

   | Draft | Reviewed? | Approved? | What changed after it |
   |---|---|---|---|
   | v0.1 | yes — returned `REQUIRES_OWNER_CLARIFICATION` | **no** | produced owner corrections A–F, applied at v0.2 |
   | v0.2 | **no** | **no** | changed the normative SQL, its digests, the `selector_policy_sha256` preimage, and the document contract |
   | v0.3 | yes — returned `REQUIRES_OWNER_CLARIFICATION` | **no** | changed the `schema_fingerprint_sha256` preimage; its review produced owner corrections A and B, applied at v0.4 |
   | v0.4 | yes — returned `REQUIRES_OWNER_CLARIFICATION` | **no** | applied the §10 crosswalk and the manifest replacement guard, but the selection-run replacement, deletion, and identity bypasses remained; its review produced the v0.5 ruling |
   | v0.5 | **not yet** | **no** | — |

   **SATISFIED — 2026-07-30.** The review ran against v0.5, reached its own conclusion, inherited
   no earlier recommendation, and returned `ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL` with no
   governance blockers and no owner clarifications required;
2. **final owner approval of v0.5** of this record, recorded in
   [`decision_registry.md`](decision_registry.md) — **SATISFIED — owner approved 2026-07-30**;
3. a **separately issued bounded S6 implementation prompt** that does not widen the contract's
   authorized paths — **NOT YET SATISFIED**. This is the only remaining gate. Approval of this
   record moved [`m23_s6.md`](../../Milestones/contracts/m23_s6.md) to `READY_FOR_IMPLEMENTATION`
   with `IMPLEMENTATION_AUTHORIZATION: YES`, which records that nothing external blocks the stage
   and **does not start the work** ([`contracts/README.md`](../../Milestones/contracts/README.md)).

## 24. Reason

Stage S6 is where a chain of content-derived identities that has been extended one accepted stage at
a time finally has to close: into a digest of the terminal result, into a manifest the project owner
can approve by hash, and into a boundary that keeps deterministic machinery from being mistaken for a
published research result. Two of the three things it needs were named but never defined — the nine
hash layers, and `selection_result_sha256` — and the third, manifest eligibility, turned out on
direct probing not to be enforced at all: the schema will today accept, and approve, a manifest over
the permanently-`running` Stage-S4 draft that three separate records exclude. This record settles all
three deliberately, on evidence, before any code is written, rather than leaving them to be
discovered mid-implementation and resolved under pressure.

No deviation from Decisions 013–020 is made or implied. No transition metric and no final-test metric
has been viewed in connection with this record.
