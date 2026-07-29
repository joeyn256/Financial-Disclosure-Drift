# Decision 019 — M2.3 Stage S5 Frozen-Storage-to-Pure-Input Mapping Policy

**Date:** 2026-07-28
**Status:** APPROVED — OWNER APPROVED 2026-07-28
**Type:** Implementation and provenance decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged by this record. No hypothesis, cohort window, maturity gate,
outcome definition, threshold, or seed is altered.
**Supersedes:** nothing. **Clarifies** the storage-to-pure-input boundary required by
[Decision 018](decision_018_m23_s5_accession_selection_policy.md) §§5.3, 13, 15, 19, and 25. It does
**not** redesign the accepted Stage S5.1 policy, objective, or core.
**Governs:** Milestone 2.3, Stage S5.2 onward.
**Related:** [Decision 007](decision_007_sec_universe.md) (canonical CIK identity),
[Decision 008](decision_008_filing_inventory.md) §2 (amendment relationship states and
`REVIEW_AMENDMENT_PARENT_UNRESOLVED`), [Decision 010](decision_010_temporal_availability_and_cohort_assignment.md)
(cohort date-source rule), [Decision 013](decision_013_pilot_selection_mechanics.md) §§3–5 (counting
units, multi-registrant accounting, selector policy),
[Decision 014](decision_014_pilot_evidence_and_classification_policy.md) §§1, 6, 7 (evidence levels,
amendment-purpose `unproven`, provisional cohort),
[Decision 016](decision_016_m23_schema_and_artifact_architecture.md) §§4, 6, 8, 9 (normalized
evidence and reasons, integrity, hash boundaries, multi-registrant rule),
[Decision 017](decision_017_s4_quota_policy_and_control_evidence.md) (quota-policy version,
`excluded_pool_count`, boundary-control evidence interpretation),
[Decision 018](decision_018_m23_s5_accession_selection_policy.md) (Stage S5 accession selection
policy).

**This record authorizes no implementation.** No code, test, migration, reason-code registration, or
policy constant is created by it. Its approval on 2026-07-28 cleared the
`BLOCKED_PENDING_DECISION_019` blocker on Stage S5.2 — the stage is now
`READY_FOR_IMPLEMENTATION` — but approval of a policy record is never itself authorization to write
code: **a separate bounded S5.2 implementation prompt is required** before any S5.2 code, test,
migration `0011`, reason-code registration, or policy constant is written. See §19.

## 1. Why this record exists

Decision 018 §19 divides Stage S5 into a pure methodological core (S5.1, accepted) and a persistence
adapter (S5.2). Decision 018 §5.3 obliges the adapter to "construct the pure S5.1 inputs" and to fail
closed on inconsistency, and §25 rules that the frozen Stage S3 schema requires no change to support
Stage S5.

Four of the accepted S5.1 input fields have **no corresponding stored column** in migration `0009`:

| Accepted S5.1 pure input | Stored representation in migration `0009` |
|---|---|
| `AccessionCandidate.amendment_linkage_evidence_level` | none — only `amendment_linkage_state` and `provisional_parent_accession` exist |
| `AccessionCandidate.multi_registrant_evidence_level` | none — N per-registrant `evidence_level` rows exist in `pilot_candidate_accession_registrants` |
| `AccessionCandidate.cohort_applicability` | none — `cohort_evidence_level` is `NOT NULL` over four levels with no `not_applicable` member |
| `EntityCandidate.name_change` (`NameChangeEvidence`) | none — `pilot_candidate_entity_evidence` identity rows with unconstrained `source_field` and free-text `canonical_observed_value` |

Each gap is a **representation and conversion** question, not a methodological one: the underlying
facts are already stored, but no approved record states which stored rows carry them or how the
adapter reads them. Without those rulings the adapter would have to invent a mapping, which
Decision 018 §19 prohibits outright — an invented mapping is a second methodological implementation.

This record closes exactly those four gaps and nothing else.

## 2. Scope

This record freezes, for Stage S5 only:

- the candidate-snapshot **representation requirements** for amendment linkage, multi-registrant
  structure, pre-study support provenance, and former-name identity evidence (§§5–8);
- the **loader-conversion rules** mapping those representations onto the accepted, unmodified S5.1
  immutable input types (§§5–8);
- the **snapshot-freeze obligations** a candidate snapshot must satisfy to be valid for Stage S5 (§9);
- the **run-identity content** these mappings contribute (§10).

## 3. Non-scope

This record does **not**:

- redesign, reopen, or amend the accepted Stage S5.1 policy, objective, core module, or tests;
- change Decision 018's pure-versus-persistence boundary (§19) or its no-DDL ruling (§25);
- reorder, split, merge, or reweight any objective term;
- create, rename, or retire any table, column, constraint, index, trigger, migration, reason code,
  policy constant, module, or test;
- authorize migration `0011`, reason-code registration, S5.2 implementation, reserve work (S5.4), or
  manifest work (S6);
- relax, remove, defer, or declare satisfied any quota. **No measurable quota is deferred by this
  record**; the difficult-or-nonstandard filing-package quota (Decision 018 §14) remains the only
  approved M2.3 deferral, unchanged.

## 4. General principles (frozen)

1. **No DDL is required or authorized.** Every ruling below is expressible over the tables migration
   `0009` already defines.
2. **Migrations `0009` and `0010` remain unchanged.** Migration `0011` remains INSERT-only
   policy-reference seeding (Decision 018 §20) and is not created, extended, or repurposed here.
3. **The existing normalized evidence, registrant, and reason rows are the authoritative
   representation** (Decision 016 §4). A resolved value with no supporting evidence row is not a
   valid candidate row, and the normalized reason tables are the source of truth.
4. **The candidate-snapshot builder must materialize the required representation before freezing a
   snapshot.** Every representation this record requires is a build-time obligation.
5. **Stage S5.2 validates and maps that representation into the accepted immutable S5.1 inputs.** It
   reads; it does not write candidate rows.
6. **Stage S5.2 must never manufacture missing evidence, provenance, relationships, or evidence
   levels.** No default, no proxy, no inference beyond the mechanical conversions below.
7. **Unknown, incomplete, contradictory, duplicated, or ambiguous representations fail closed before
   the solver is invoked** (Decision 018 §§5.3, 17; CLAUDE.md rule 12). Failing closed means raising
   before any search node is expanded — never dropping the offending row, never substituting a
   default, never relaxing a check.
8. **These mappings, and every normalized row that affects them, enter the S5 run-identity content**
   (§10).
9. **A snapshot that predates these representation requirements is not silently upgraded.** It must
   satisfy this record **as stored** or be rejected. No production snapshot is rewritten, migrated,
   backfilled, or repaired by Stage S5.
10. **Evidence levels are read, never graded.** Where a stored `evidence_level` exists, S5.2 carries
    it; where a pure-input level must be derived (§§5–8), this record states the derivation
    exhaustively and the adapter implements exactly that.

## 5. Ruling 1 — amendment-linkage evidence

### 5.1 The exact stored vocabulary

Migration `0009` constrains `pilot_candidate_accessions.amendment_linkage_state` to exactly:

```sql
CHECK (amendment_linkage_state IS NULL OR amendment_linkage_state IN (
    'amends_original', 'amends_prior_amendment', 'supplements_original',
    'possible_amendment_of', 'unresolved_amendment'))
```

with two further constraints on the same table:

```sql
CHECK (is_amendment = 1 OR (amendment_linkage_state IS NULL AND provisional_parent_accession IS NULL))
CHECK (is_amendment = 0 OR amendment_linkage_state IS NOT NULL)
```

**The schema's non-amendment linkage state is `NULL`**, not a named vocabulary value. There is no
stored amendment-linkage evidence-level column, and `pilot_candidate_accession_evidence
.classification_dimension` has no `amendment_linkage` member — the freeze trigger backs a non-`NULL`
linkage state with an `amendment_purpose`-dimension evidence row.

The meanings below are Decision 008 §2.1's, quoted, not paraphrased:

| Stored state | Decision 008 §2.1 meaning |
|---|---|
| `amends_original` | "Evidence links the amendment to a specific original accession" |
| `amends_prior_amendment` | "Evidence links the amendment to an earlier amendment" |
| `supplements_original` | "Evidence shows a supplemental relationship, not a replacement" |
| `possible_amendment_of` | "Candidate parentage with insufficient evidence to resolve" |
| `unresolved_amendment` | "Parentage cannot be established" |

Decision 008 §2.1 additionally states that `possible_amendment_of` and `unresolved_amendment` "both
carry `REVIEW_AMENDMENT_PARENT_UNRESOLVED`".

### 5.2 Frozen mapping

| Stored `amendment_linkage_state` | `amendment_linkage_evidence_level` on the pure input |
|---|---|
| `NULL` (required on every original) | `not_applicable` |
| `amends_original` | `provisional` when every §5.4 condition holds; `review_required` in exactly the §5.6 case; otherwise fail closed under §5.8 |
| `amends_prior_amendment` | `provisional` when every §5.4 condition holds; `review_required` in exactly the §5.6 case; otherwise fail closed under §5.8 |
| `supplements_original` | `provisional` when every §5.4 condition holds; `review_required` in exactly the §5.6 case; otherwise fail closed under §5.8 |
| `possible_amendment_of` | `review_required` |
| `unresolved_amendment` | `unavailable` |

The three resolved rows are **total**. §5.6 names the single non-corrupt way a resolved state can fail
§5.4 — an otherwise well-formed, type-consistent parent identity that is absent from the frozen
snapshot. §5.8 enumerates every other §5.4 failure as a fail-closed condition, **including the two
chain dead-ends §5.4.2 names**: a walk that reaches an intermediate amendment in `unresolved_amendment`,
and one that reaches an intermediate amendment in `possible_amendment_of` with a `NULL` stored
candidate parent. §5.4.2 also states the one intermediate condition that is **not** a §5.4 failure at
all — a hop in `possible_amendment_of` carrying a valid stored candidate-parent identity, through
which the walk continues — and states what each accession maps to in that case. There is no residual
"otherwise" branch and no implementation latitude between the three outcomes.

`unproven` is **not** an admissible value for this dimension. The accepted S5.1 core admits
`unproven` only for `amendment_purpose_evidence_level` (Decision 014 §6) and
`pilot_quota_results.evidence_state`; `accession_selector.ACCESSION_EVIDENCE_LEVELS` is exactly
`{provisional, review_required, conflicting, unavailable}`, and the accepted validator rejects any
other value on this dimension. Freezing `unproven` here would make every unresolved amendment a hard
load failure, contradicting Decision 018 §10.2, which requires such an accession to survive as a
singleton diagnostic family.

`conflicting` is unreachable for this dimension: a contradiction between the stored linkage
representations is a fail-closed condition (§5.5), not a gradeable evidence state.

### 5.3 Original accession

When `is_amendment = 0`:

- `amendment_linkage_state` **must** be `NULL` (the schema's non-amendment state);
- `provisional_parent_accession` **must** be `NULL`;
- the pure input carries `amendment_linkage_state = None`,
  `provisional_parent_accession_dashed = None`, and
  `amendment_linkage_evidence_level = not_applicable`.

Any contradictory combination fails closed (§5.5). Structural inapplicability is not a penalty
(Decision 018 §3.4): an original contributes zero on this dimension.

### 5.4 Amendment with resolved parentage

An amendment maps to `amendment_linkage_evidence_level = provisional` **only when all of the
following hold**:

1. its stored `amendment_linkage_state` is exactly one of `amends_original`,
   `amends_prior_amendment`, or `supplements_original` — the three states Decision 008 §2.1 defines
   as evidence-linked parentage;
2. `provisional_parent_accession` is non-`NULL` and is in the **required canonical stored form**
   (§5.7);
3. the parent identity is internally consistent — it is a well-formed accession identity, and it is
   not the amending accession's own identity;
4. the **direct** parent exists in the **same frozen candidate snapshot**, matched on
   `pilot_candidate_accessions.accession_plain` under the same `snapshot_id`;
5. the **direct parent's type matches the stored state exactly**, per the table below;
6. the **resolved chain terminates at an original accession**, per §5.4.2;
7. the **strict acceptance ordering** of §5.9 holds against the resolved root original — the
   amendment's stored `acceptance_audit_date` and that of its resolved root original are both
   present and well formed, and the amendment's is **strictly later**;
8. **no** normalized unresolved-parent reason applies to that accession — that is, no
   `pilot_candidate_accession_reasons` row with `reason_code = 'REVIEW_AMENDMENT_PARENT_UNRESOLVED'`
   exists for it, at any `reason_scope`.

When all eight hold, the pure input additionally carries the parent's **canonical dashed** identity in
`provisional_parent_accession_dashed`, derived per §5.7.

#### 5.4.1 State-specific direct-parent type (frozen)

Decision 008 §2.1 defines each resolved state **by the type of the accession it points at**. That
definition is a validation obligation, not a description:

| Stored `amendment_linkage_state` | Required `is_amendment` on the direct parent row | Decision 008 §2.1 wording this enforces |
|---|---|---|
| `amends_original` | `0` — the direct parent must be an **original** | "links the amendment to a specific **original** accession" |
| `supplements_original` | `0` — the direct parent must be an **original** | "a supplemental relationship" to an original, "not a replacement" |
| `amends_prior_amendment` | `1` — the direct parent must be an **amendment** | "links the amendment to an **earlier amendment**" |

A state/parent-type mismatch is a **structural contradiction and fails closed** (§5.8). It is not
graded, not downgraded to `review_required`, and not repaired.

**Stage S5.2 must not pass a contradictory parent pointer into Stage S5.1 and rely on transitive
resolution to repair it.** The accepted S5.1 `derive_amendment_families` walks the parent chain until
it reaches a non-amendment and therefore *would* silently resolve `amends_original` pointing at an
amendment into the chain's root original, producing a resolved family and affirmative
linked-amendment coverage (Decision 018 §10.4) that the stored evidence does not support. Migration
`0009` places neither a foreign key nor a `CHECK` on `provisional_parent_accession`, so the loader is
the only place this contradiction can be caught, and catching it there is mandatory.

#### 5.4.2 Chain termination (frozen)

Starting from the amendment and following `provisional_parent_accession` row by row within the same
`snapshot_id`:

- every hop in a **resolved** linkage state must satisfy conditions 2 and 3 for its own stored parent
  identity;
- every hop whose parent row is present must satisfy condition 5 for **that hop's own** stored
  `amendment_linkage_state`. §5.4.1 constrains exactly the three resolved states; a hop in
  `possible_amendment_of` imposes no parent-type requirement of its own, and is governed instead by
  the intermediate-state rules below;
- a hop in an **unresolved** linkage state (`possible_amendment_of`, `unresolved_amendment`) is
  governed by the intermediate-state rules below, not by conditions 2, 3, and 5;
- no accession identity may repeat — a chain that revisits an accession is a cycle;
- the walk must terminate at a row with `is_amendment = 0`, which is the **resolved root original**.

**Intermediate `unresolved_amendment` (frozen).** A walk that reaches an intermediate amendment whose
stored `amendment_linkage_state` is `unresolved_amendment` is a **dead end**. That row necessarily
carries a `NULL` `provisional_parent_accession` — a snapshot in which it carries a stored parent is
already rejected by §5.8's parent-identity rule, on that row's own account — so the chain terminates
at no original and §5.4 condition 6 cannot be satisfied. The **outer** resolved representation
therefore **fails closed** (§5.8). Stage S5.2 must not treat the intermediate amendment as a root,
must not repair, re-point, or bypass the dead end, and must not pass the outer candidate into
Stage S5.1 as a valid resolved chain.

**Intermediate `possible_amendment_of` with no stored candidate parent (frozen).** A walk that
reaches an intermediate amendment whose stored state is `possible_amendment_of` and whose
`provisional_parent_accession` is `NULL` is the same dead end: the chain terminates at no original,
§5.4 condition 6 cannot be satisfied, and the outer resolved representation **fails closed** (§5.8).
No repair, substitution, or inference is permitted.

**Intermediate `possible_amendment_of` carrying a valid stored candidate parent (frozen).** Where the
intermediate's stored candidate-parent identity is present and well formed (§5.4 conditions 2 and 3),
the walk **continues through it**, and:

- this record uses that stored identity **only** for candidate-storage consistency and chain
  diagnostics — never as evidence that the intermediate's own parentage is resolved;
- the **intermediate accession itself** maps, unchanged from §5.5, to
  `amendment_linkage_evidence_level = review_required` with
  `provisional_parent_accession_dashed = None` on the accepted S5.1 pure input;
- the accepted S5.1 `derive_amendment_families` therefore **stops family traversal at that
  intermediate accession**, because the pure input it receives carries no parent pointer there;
- the **family remains unresolved**, and **no linked-amendment quota contribution is possible** for
  any member of it (Decision 018 §§10.2, 10.4);
- the **outer accession's own direct linkage mapping remains governed by its existing §5.4
  conditions** — conditions 1–5 against its own direct parent, condition 6 against this walk,
  and conditions 7–8 unchanged.

**Nothing in that paragraph makes the chain resolved for Stage S5.1.** Continuing the walk is a
loader-side storage-consistency and diagnostic operation; it never creates a resolved S5.1 family, a
resolved root original for S5.1 purposes, or any affirmative linked-amendment credit. It documents
existing fail-safe behaviour and introduces no second family methodology (§5.10).

Outcomes, exhaustively — every way the walk can end, and the one way it legitimately continues:

| Chain condition | Outcome |
|---|---|
| Terminates at an `is_amendment = 0` row; every hop type-consistent for its own state | conditions 4–6 satisfied; continue to conditions 7–8 |
| A hop's parent row is **present but type-inconsistent** with that hop's state (§5.4.1) | fail closed (§5.8) |
| The walk **cycles** | fail closed (§5.8) |
| A hop's parent identity is well formed and type-consistent but the parent row is **absent from the snapshot** | §5.6 — `review_required`, no parent passed |
| A hop in a **resolved** state carries a malformed, self-referential, or `NULL` `provisional_parent_accession` | fail closed (§5.8) |
| The walk reaches an intermediate amendment in **`unresolved_amendment`** | fail closed (§5.8) — necessarily a `NULL` parent, so the chain terminates at no original |
| The walk reaches an intermediate amendment in **`possible_amendment_of` with a `NULL` parent** | fail closed (§5.8) — the same dead end |
| The walk reaches an intermediate amendment in **`possible_amendment_of` carrying a valid stored candidate parent** | the walk **continues** through that identity for storage-consistency and diagnostics only; the outer accession stays governed by its own §5.4 conditions; the intermediate maps to `review_required` with no parent pointer (§5.5), so S5.1's family stays **unresolved** and earns **no** linked-amendment contribution |
| The chain terminates at a root original but the §5.9 **strict acceptance ordering** fails — earlier, equal, `NULL`, malformed, or otherwise incomparable | fail closed (§5.8, §5.9.3); evaluated after conditions 4–6 resolve |

Classified by where each outcome takes effect:

- **Fail closed at the loader, before any search node is expanded:** type-inconsistent hop; cycle;
  malformed, self-referential, or `NULL` parent on a resolved hop; intermediate `unresolved_amendment`;
  intermediate `possible_amendment_of` with a `NULL` parent; acceptance-ordering failure.
- **Mapped onto a weaker pure input rather than rejected:** an absent parent row → `review_required`
  with no parent pointer (§5.6); an accession stored in `possible_amendment_of` → `review_required`,
  and one stored in `unresolved_amendment` → `unavailable`, each with no parent pointer (§§5.2, 5.5).
- **Left unresolved only inside the accepted S5.1 family computation:** a chain that the loader admits
  but whose traversal S5.1 halts because an intermediate member's pure input carries no parent pointer.
  That is S5.1's singleton-diagnostic behaviour under Decision 018 §10.2, computed by S5.1 alone; this
  record neither reproduces nor overrides it.

This is stricter than the accepted S5.1 core, which degrades a cycle or an out-of-pool parent to an
unresolved singleton family rather than raising. The stricter loader gate is deliberate: S5.1's
degradation is the correct behaviour for a *pure* input that has already been validated, and is not a
licence for the adapter to hand it an input known to be corrupt (Decision 018 §§5.3, 19).

### 5.5 Amendment with unresolved parentage

`possible_amendment_of` maps to `review_required`; `unresolved_amendment` maps to `unavailable`. The
distinction follows Decision 008 §2.1 exactly: the first names a candidate parent whose evidence is
insufficient to resolve, the second states that parentage cannot be established at all. Both states
produce identical selector behaviour, and the distinction is diagnostic and provenance-bearing
rather than methodological.

For **both** unresolved states:

- the pure input carries `provisional_parent_accession_dashed = None`, **even when the stored
  `provisional_parent_accession` column is non-`NULL`**. This is required, not optional: the accepted
  S5.1 `derive_amendment_families` resolves parentage from the pure input's parent pointer alone, so
  carrying an unresolved candidate parent through would produce a *resolved* family and contradict
  Decision 018 §10.2;
- the accession therefore takes **unresolved singleton-family behaviour** in the accepted S5.1 core:
  a singleton diagnostic family that can never satisfy linked-amendment coverage;
- there is **no linked-amendment quota contribution**, affirmative or otherwise (Decision 018 §10.2,
  §10.4);
- the existing `REVIEW_AMENDMENT_PARENT_UNRESOLVED` reason semantics are **reused, never
  duplicated**: the snapshot must carry that reason row for the accession, and no new unresolved-
  parent code is created.

### 5.6 Resolved state whose parent is absent from the snapshot

A stored state in the resolved set that satisfies §5.4 conditions 1, 2, and 3, and whose only
unsatisfied condition is condition 4 at some hop of the §5.4.2 walk — the parent identity is well
formed, type-consistent for its state, and not self-referential, but **no accession with that
identity exists in the same frozen snapshot** — maps to
`amendment_linkage_evidence_level = review_required`, carries
`provisional_parent_accession_dashed = None`, takes singleton-family behaviour, and makes no
linked-amendment contribution.

This is not a corruption: an amendment's original may legitimately fall outside the candidate pool.
It is an affirmative claim the snapshot cannot corroborate, which is exactly what `review_required`
names.

**This subsection covers absence and nothing else.** A present-but-type-inconsistent parent (§5.4.1),
a cycle (§5.4.2), an acceptance-ordering failure (§5.9) — which includes equal, missing, malformed,
and otherwise incomparable dates, not only a strictly-earlier one — a malformed or self-referential
parent identity, and a contradictory reason row are **not** §5.6 cases: each is a fail-closed
condition under §5.8. Where the absent-parent condition and any fail-closed condition both hold, the
fail-closed condition governs — gates are evaluated before mappings (§4 principle 7, §14).

**The §5.9 ordering gate cannot be one of those coincident conditions.** It applies only when the
§5.4.2 walk terminates at a resolved root original **present** in the same snapshot; when the walk
ends in absence there is no root original and therefore no comparison to make, so the ordering gate
is **inapplicable rather than failed** and this subsection's `review_required` governs (§5.9.3).
An absent parent is never reported as an ordering failure, and an ordering failure is never reported
as an absent parent.

### 5.7 Canonical stored form of the parent identity

`pilot_candidate_accessions.provisional_parent_accession` carries the **plain 18-character** accession
form — exactly eighteen decimal digits, no dashes — matching `accession_plain`, the column it
references in the same table.

This follows Decision 018 §5.1 mechanically: the plain form "remains the persisted database and
foreign-key column (`pilot_candidate_accessions.accession_plain` and every table referencing it)",
while the dashed form is canonical for hashing, ordering, identity fallback, and presentation.
Migration `0009` places no format `CHECK` and no foreign key on this column, so this record freezes
the form; no DDL is added to enforce it, and validation is the loader's obligation (Decision 018
§5.3).

Stage S5.2 derives the canonical dashed form `NNNNNNNNNN-NN-NNNNNN` from the stored plain value for
`AccessionCandidate.provisional_parent_accession_dashed`, and fails closed when the stored value is
not exactly eighteen decimal digits.

### 5.8 Contradictions that fail closed

Every one of the following is a fail-closed condition, rejected before the solver is invoked. Each
names an exact stored condition; none is a judgement call.

**Linkage state versus amendment flag**

- a linkage state outside the migration-`0009` vocabulary enumerated in §5.1;
- the non-amendment state (`NULL`) on an accession with `is_amendment = 1`;
- any non-`NULL` linkage state, or any non-`NULL` `provisional_parent_accession`, on an accession
  with `is_amendment = 0`.

**Parent identity**

- a resolved linkage state (`amends_original`, `amends_prior_amendment`, `supplements_original`)
  with a `NULL` `provisional_parent_accession`;
- `unresolved_amendment` carrying a non-`NULL` `provisional_parent_accession` — "parentage cannot be
  established" and a stored parent identity cannot both be true;
- a malformed parent identity at any hop of the §5.4.2 walk — `provisional_parent_accession` that is
  not exactly eighteen decimal digits, or that equals that hop's own `accession_plain`;
- a parent row that **is** present in the snapshot but whose stored `accession_number_dashed` is not
  the canonical dashed rendering of its own `accession_plain` (Decision 018 §5.3 requires plain and
  dashed to agree on every candidate accession; a parent row that fails it cannot be used to derive
  `provisional_parent_accession_dashed`).

**Parent type and chain shape (§5.4.1, §5.4.2)**

- `amends_original` whose direct parent row carries `is_amendment = 1`;
- `supplements_original` whose direct parent row carries `is_amendment = 1`;
- `amends_prior_amendment` whose direct parent row carries `is_amendment = 0`;
- any hop of the §5.4.2 walk whose present parent row violates that hop's own state-specific type
  requirement;
- a parent chain that revisits an accession identity (a cycle), and therefore terminates at no
  original;
- a parent chain that reaches an intermediate amendment whose stored `amendment_linkage_state` is
  `unresolved_amendment`. That row necessarily carries a `NULL` `provisional_parent_accession` — the
  parent-identity rule above already rejects one that does not — so the walk dead-ends and the chain
  terminates at no original (§5.4.2);
- a parent chain that reaches an intermediate amendment whose stored `amendment_linkage_state` is
  `possible_amendment_of` and whose `provisional_parent_accession` is `NULL` — the same dead end,
  terminating at no original (§5.4.2).

An intermediate amendment in `possible_amendment_of` that carries a **valid** stored candidate-parent
identity is deliberately **not** in this list. The §5.4.2 walk continues through it for
storage-consistency and diagnostic purposes, the intermediate itself maps to `review_required` with
no parent pointer, and the resulting S5.1 family is unresolved and earns no linked-amendment
contribution. §5.4.2 states that disposition in full; it is not a fail-closed condition.

**Acceptance ordering (§5.9)** — a resolved state whose chain terminates at a root original inside
the snapshot is admitted **only** when the amendment's `acceptance_audit_date` is **strictly later**
than that root original's. Every other stored condition fails closed:

- a resolved state whose `acceptance_audit_date` is strictly **earlier** than the resolved root
  original's `acceptance_audit_date`;
- a resolved state whose `acceptance_audit_date` is **equal** to the resolved root original's —
  the field carries day granularity, so equality proves no ordering and cannot support a resolved
  linkage claim (§5.9.4);
- a resolved state where `acceptance_audit_date` is `NULL` on the amendment or on its resolved root
  original;
- a resolved state where `acceptance_audit_date` is not an exact, real `YYYY-MM-DD` calendar date on
  the amendment or on its resolved root original;
- a resolved state whose two `acceptance_audit_date` values are otherwise incomparable (§5.9.3).

**Reason-row agreement**

- a resolved linkage state on an accession that also carries a
  `REVIEW_AMENDMENT_PARENT_UNRESOLVED` reason row at any `reason_scope` — two normalized
  representations of the same fact in direct contradiction;
- an unresolved linkage state (`possible_amendment_of`, `unresolved_amendment`) with **no**
  `REVIEW_AMENDMENT_PARENT_UNRESOLVED` reason row, which Decision 008 §2.1 requires.

`pilot_candidate_accessions.provisional_parent_accession` is a single column on a row keyed
`(snapshot_id, accession_plain)`, so "more than one stored parent identity for one accession" is not
a reachable state and no rule is stated for it.

### 5.9 Amendment acceptance ordering

Decision 008 §2.2 rules that "an amendment accepted before its alleged original is
`unresolved_amendment` plus review, never a silent reassignment". This subsection states which stored
field expresses that rule for Stage S5, and what each side of the boundary must do with it.

**The frozen rule, stated once.** The only acceptance-order field available to Stage S5 is a
**calendar date**, not a timestamp (§5.9.1). For every amendment represented as having resolved
parentage, its stored `acceptance_audit_date` is compared with the stored `acceptance_audit_date` of
its **transitive root original** (§5.4.2), and **only a strictly later amendment date permits a
resolved linkage state**. Strictly earlier, equal, missing, malformed, and otherwise incomparable
dates are all **unresolved**. This record **does not infer sub-day ordering** in either direction
from a day-granularity field (§5.9.4).

#### 5.9.1 The exact stored field

Migration `0009` gives `pilot_candidate_accessions` **two** acceptance-derived columns, and only one
of them can express ordering:

```sql
-- pilot_candidate_accessions, migration 0009
acceptance_audit_date              TEXT,
acceptance_audit_cohort            TEXT
    CHECK (acceptance_audit_cohort IS NULL OR acceptance_audit_cohort IN (
        'development', 'transition', 'primary_test', 'prospective', 'monitoring')),
```

`acceptance_audit_date` is the **only stored acceptance date** in the frozen candidate-accession
representation, and the **only frozen candidate field capable of expressing relative accession
acceptance ordering**. It is therefore the only field §§5.9.2–5.9.3 read, and the only one this
subsection's properties describe.

`acceptance_audit_cohort` is a **categorical, audit-only cohort label** over the five frozen cohort
names above — not a date, not a timestamp, and not an ordering source. It **must not** be used to
infer accession ordering, sub-day timing, or amendment-parent chronology. Two accessions sharing a
label are not ordered by it, and two carrying different labels are not thereby ordered either: the
label is a cohort classification derived from the acceptance date, which Decision 010 and §13 keep
audit-only for cohort purposes. **No rule in this record reads it**, and naming it here is what keeps
the paragraph below from being read as a claim that no other acceptance-derived column exists.

`acceptance_audit_date`'s properties, as migration `0009` actually defines them, are load-bearing
here and are not restated loosely:

- it is a **calendar date, not a timestamp** — day granularity, canonical form exactly `YYYY-MM-DD`;
- it therefore **cannot order two accessions accepted on the same calendar day**, and no sub-day
  ordering may be derived, inferred, or assumed from it (§5.9.4);
- it is **nullable**, and migration `0009` places no `CHECK` on its format;
- it is **audit-only for cohort purposes** — official filing date remains authoritative for cohort
  assignment (Decision 010; Decision 018 §23; §13 of this record). Using it to order two accessions
  within one amendment family is not a cohort use and does not disturb that rule.

**No acceptance timestamp is available to Stage S5.2, and no acceptance field outside the frozen
candidate snapshot may be read.** `inventory_accessions.acceptance_datetime_utc`,
`.acceptance_datetime_et`, `.acceptance_date_sec`, and `.acceptance_datetime_sec_raw` (migration
`0001`) are post-retrieval and prohibited before M2.5 (Decision 013 §2; the Stage S5.2 contract's
prohibited paths). `census_accessions.acceptance_datetime_sec_raw` and `.acceptance_date_sec`
(migration `0003`) are census-side observation columns and are not part of the frozen candidate
snapshot the adapter reads. **Both families remain outside the M2.3 frozen-input boundary**, whatever
their resolution. Inside that boundary the two columns above are the whole of it: one usable
acceptance date and one audit-only cohort label. **No new field is invented, and none is added.**

#### 5.9.2 Candidate-snapshot construction obligation

Candidate-snapshot construction **must not represent an amendment as having resolved parentage
unless the strict ordering of §5.9 is affirmatively established from the stored dates.** For an
amendment whose parentage would otherwise resolve to a root original inside the snapshot, the
builder compares the amendment's own `acceptance_audit_date` with that of its alleged **resolved
root original** (§5.4.2) and classifies as follows. The table is total:

| Stored condition | Required candidate-snapshot classification |
|---|---|
| amendment date **strictly later** than the root original's | a resolved state is permitted, subject to every other §5.4 condition |
| amendment date **strictly earlier** than the root original's | `unresolved_amendment` + `REVIEW_AMENDMENT_PARENT_UNRESOLVED` |
| amendment date **equal to** the root original's | `unresolved_amendment` + `REVIEW_AMENDMENT_PARENT_UNRESOLVED` |
| amendment's `acceptance_audit_date` **missing** (`NULL`) | `unresolved_amendment` + `REVIEW_AMENDMENT_PARENT_UNRESOLVED` |
| root original's `acceptance_audit_date` **missing** (`NULL`) | `unresolved_amendment` + `REVIEW_AMENDMENT_PARENT_UNRESOLVED` |
| either date **malformed** — not an exact, real `YYYY-MM-DD` calendar date | `unresolved_amendment` + `REVIEW_AMENDMENT_PARENT_UNRESOLVED` |
| either date **otherwise incomparable** (§5.9.3) | `unresolved_amendment` + `REVIEW_AMENDMENT_PARENT_UNRESOLVED` |

Every accession classified `unresolved_amendment` by that table:

- **must not** be represented using any resolved linkage state — not `amends_original`, not
  `amends_prior_amendment`, not `supplements_original`;
- **must not** claim provisional amendment-linkage evidence: its pure-input
  `amendment_linkage_evidence_level` is `unavailable` (§5.2), it carries
  `provisional_parent_accession_dashed = None`, it takes unresolved singleton-family behaviour
  (§5.5), and it makes no linked-amendment contribution (Decision 018 §§10.2, 10.4);
- **must** carry `provisional_parent_accession = NULL`, because §5.8 already makes
  `unresolved_amendment` with a stored parent identity a fail-closed contradiction. This is the
  intersection of two rules this record already states, not an additional requirement.

The strictly-earlier row is Decision 008 §2.2 expressed over the stored field. The equal, missing,
malformed, and incomparable rows are the **evidence boundary of a day-granularity column**: none of
them establishes that the amendment followed the original, and an ordering that is not established
may not be represented as a resolved one (§5.9.4). Every row is a build-time obligation
(§4 principle 4).

**For an `amends_prior_amendment` chain the comparison is against the transitive root original, not
merely the immediate amendment parent.** An amendment may legitimately be accepted before an earlier
amendment in the same family; it may never be accepted before the original it ultimately amends, and
a same-day pair does not establish that it was accepted after it.

**Future higher-resolution data is out of scope here.** The separately authorized future candidate
builder (§9.1) may, under a future stage or decision, establish sub-day ordering from a frozen
higher-resolution SEC acceptance source. **M2.3 neither uses nor infers that data** (§5.9.1), and
nothing in this record authorizes acquiring, storing, or reading it.

#### 5.9.3 Read-time revalidation

Stage S5.2 **revalidates** this relationship from the stored authoritative dates on every **stored
resolved state**, and admits that state **only** when the amendment's `acceptance_audit_date` is
strictly later than its resolved root original's. A stored resolved state is valid at read time only
when all of the following hold together:

- every §5.4 parent-identity, parent-type, and chain condition passes (§§5.4, 5.4.1, 5.4.2);
- every required `acceptance_audit_date` — the amendment's and its transitive root original's — is
  present and valid;
- the amendment's date is **strictly later** than the transitive root original's.

The gate is total (§5.8):

| Stored condition on a resolved state | Outcome |
|---|---|
| amendment date **strictly later than** the root original's | ordering satisfied — resolved state admitted, subject to every other §5.4 condition |
| amendment date **strictly earlier than** the root original's | **fail closed** — corrupted representation |
| amendment date **equal to** the root original's | **fail closed** — corrupted representation; equality establishes no ordering (§5.9.4) |
| amendment's `acceptance_audit_date` **`NULL`** | **fail closed** |
| root original's `acceptance_audit_date` **`NULL`** | **fail closed** |
| amendment's `acceptance_audit_date` **malformed** — not an exact, real `YYYY-MM-DD` calendar date | **fail closed** |
| root original's `acceptance_audit_date` **malformed** | **fail closed** |
| the two values **otherwise incomparable** | **fail closed** |

"Otherwise incomparable" is a **residual safety category, not a judgement call**: two values that are
each an exact, real `YYYY-MM-DD` calendar date are always totally ordered by exact string comparison,
which is the comparison Stage S5.2 performs. The row exists so that any condition this table did not
anticipate falls to fail-closed rather than to a permissive default.

**Applicability.** This gate applies exactly when the §5.4.2 walk terminates at a resolved root
original present in the same frozen snapshot. When the walk instead ends at a well-formed,
type-consistent parent that is **absent** from the snapshot, there is no resolved root original and
therefore no comparison to make: §5.6 governs, and the accession maps to `review_required` with no
parent pointer and no linked-amendment contribution. Absence is never converted into an ordering
failure, and an ordering failure is never converted into absence.

Every fail-closed row above is **corrupted representation**: the snapshot asserts a resolved
parentage its own stored dates do not support. On any of them Stage S5.2 **must not**:

- silently downgrade the state to `possible_amendment_of`, to `unresolved_amendment`, or to
  `review_required`;
- rewrite, repair, re-point, or drop the row, or rewrite the parent;
- create, insert, or synthesize a `REVIEW_AMENDMENT_PARENT_UNRESOLVED` reason row;
- substitute an `inventory_*` or `census_*` acceptance field for the missing or unusable value
  (§5.9.1);
- retrieve live SEC metadata;
- manufacture, widen, or infer a timestamp, a time of day, or a time zone;
- accept equality — or any other condition that is not strictly later — as sufficient.

The downgrade those rows describe is exactly the build-time classification §5.9.2 requires;
performing it at load would move a classification rule into the adapter, which Decision 018 §19
prohibits.

#### 5.9.4 Granularity boundary, stated rather than assumed

`acceptance_audit_date` carries day granularity, so it **cannot order two accessions accepted on the
same calendar day**. This record therefore **does not infer sub-day ordering from it, in either
direction**:

- equal dates do **not** establish that the amendment followed its original;
- equal dates are therefore **not** valid resolved ordering, and a same-day pair may neither be
  represented as (§5.9.2) nor admitted as (§5.9.3) a resolved linkage state;
- the absence of a visible strictly-earlier relationship is **not** a substitute for the affirmative
  strictly-later evidence a resolved state claims.

**This is a fail-closed evidence boundary, not a deferral.** No quota is relaxed, deferred, or
declared satisfied by it, and the difficult-or-nonstandard-package quota (Decision 018 §14) remains
the only approved M2.3 deferral (§3). A same-day amendment is neither excluded from the pool nor
discarded: it is carried as an unresolved singleton diagnostic family (§5.5) with its provenance
intact, earning no linked-amendment coverage (Decision 018 §§10.2, 10.4). Where that leaves a hard,
measurable quota unsatisfiable, Decision 018 §16's third disposition governs — the quota binds and is
reported as `fail` with its true `eligible_pool_count` — and it is **never** converted into a
deferred quota.

**M2.5 and future-stage boundary.** Sub-day acceptance ordering **cannot be proven from migration
`0009`**, which stores no acceptance timestamp for candidate accessions. A future authorized stage
may establish it from a **frozen higher-resolution acceptance source**; **no such source is
authorized for M2.3** (§5.9.1), and Stage S5 neither reads nor approximates one. Until such a stage
exists, same-day ordering is **unresolved** and cannot earn resolved linkage credit. This is a
deliberate limit of the frozen schema, recorded here rather than worked around.

### 5.10 Boundaries

- **Amendment-purpose evidence is never a substitute for amendment-linkage evidence.** The two are
  separate applicable dimensions under Decision 018 §3.4, and the fact that migration `0009` backs a
  non-`NULL` linkage state with an `amendment_purpose`-dimension evidence row does not merge them. A
  `provisional` amendment purpose never raises the linkage level, and a weak amendment purpose never
  lowers it.
- **The accepted S5.1 family logic remains authoritative** for transitive chain resolution, root
  co-selection under Decision 018 §10.4, and singleton diagnostics. This record determines only what
  the adapter puts on the pure input; it re-implements none of that logic.
- **The §5.4.1/§5.4.2/§5.9 walks are validation, not a second family implementation.** They compute
  no family identity, no membership, and no coverage; they decide only whether a stored parent
  pointer may be placed on the pure input at all. Every family, chain, and coverage decision remains
  S5.1's, computed from the pointers this record admits.

## 6. Ruling 2 — multi-registrant evidence

### 6.1 Authoritative representation and exact vocabulary

`pilot_candidate_accession_registrants` is the authoritative normalized representation of an
accession's registrant set (Decision 013 §4; Decision 016 §9). Migration `0009` constrains it to:

```sql
role           TEXT NOT NULL CHECK (role IN ('anchor', 'associated', 'submitter_only')),
is_anchor      INTEGER NOT NULL CHECK (is_anchor IN (0, 1)),
evidence_level TEXT NOT NULL
    CHECK (evidence_level IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
PRIMARY KEY (snapshot_id, accession_plain, registrant_cik_numeric),
CHECK ((role = 'anchor') = (is_anchor = 1))
```

with a partial unique index enforcing at most one anchor per accession, and a freeze trigger
requiring exactly one anchor and at least one registrant row per candidate accession.

### 6.2 Structural registrant set

For every candidate accession:

- **exactly one** `anchor` row is required;
- the anchor row's `registrant_cik_numeric` must equal
  `pilot_candidate_accessions.anchor_cik_numeric`;
- on every row, `registrant_cik_padded` must be the canonical ten-digit zero-padded rendering of
  `registrant_cik_numeric` (Decision 007);
- duplicate registrant identities fail closed — including an `associated` or `submitter_only` row
  whose CIK equals the anchor's, and any two rows whose padded CIKs coincide.

For multi-registrant coverage:

- **only `anchor` and `associated` rows establish the registrant set.** A `submitter_only` row
  creates **no** registrant contribution: it records who transmitted the filing, not who is a
  registrant on it;
- a **qualifying** multi-registrant accession requires one `anchor` row and **at least one distinct
  `associated`** row;
- the candidate's stored `multi_registrant` flag must agree with the normalized registrant set,
  subject to §6.3.

### 6.3 The one permitted divergence

Migration `0009`'s freeze trigger admits `multi_registrant = 0` on an accession carrying more than one
registrant row whenever **any** `pilot_candidate_accession_reasons` row with
`reason_scope = 'multi_registrant'` exists for it. The trigger tests the scope only. **This record
does not adopt the scope-only test**, because a scope is not a fact: the divergence is authorized by
one specific recorded condition — "authorized metadata does not fully establish the accession's
registrant set" — and that condition has exactly one registered code.

**The exact permitted case, frozen.** The single case in which `multi_registrant = 0` may stand on an
accession that carries one or more `associated` registrant rows is when **exactly one**
`pilot_candidate_accession_reasons` row exists for that accession at `reason_scope = 'multi_registrant'`,
and that row's `reason_code` is exactly:

```text
REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE
```

(registered in `src/disclosure_drift/reasons.py` under Decision 013). In that case the stored flag
governs, the accession is **not** a qualifying multi-registrant accession, and the dimension is not
applicable (§6.4).

Every other shape of that divergence **fails closed**:

- **no** `multi_registrant`-scope reason row (already unfreezable under the trigger, and rejected
  here independently of it);
- a `multi_registrant`-scope reason row carrying **any other** code — no other reason code at that
  scope authorizes the divergence, however plausible its name;
- **more than one** `multi_registrant`-scope reason row on the accession, whether or not one of them
  is the exact code — contradictory recorded reasons for a single fact.

This is **stricter than migration `0009`'s trigger**, deliberately and in the same direction as the
rule below: the trigger can only count rows and test a scope, while the divergence it admits is
meaningful only for one recorded condition.

`multi_registrant = 1` without a qualifying normalized registrant set — for example an anchor plus
only `submitter_only` rows, which the freeze trigger's row count alone cannot detect and which
therefore freezes cleanly — **always** fails closed. This too is stricter than the freeze trigger by
design: the trigger counts rows, while the quota requires registrants.

`multi_registrant = 0` on an accession with **no** `associated` rows is not a divergence at all — the
flag agrees with the registrant set — and is consistent under §6.4 regardless of any reason row
present. Such a reason row authorizes nothing and is carried into run identity (§10) like any other
normalized row.

Nothing here silently defers the multi-registrant quota. It is measurable from authorized candidate
metadata, stays hard, and is reported with its true `eligible_pool_count` when it binds
(Decision 016 §9; Decision 018 §14).

### 6.4 Mapping to the accepted S5.1 input

**"The normalized structure is consistent"** means, exactly and exhaustively, that every one of the
following holds for the accession: exactly one `anchor` row exists; the anchor row's
`registrant_cik_numeric` equals `pilot_candidate_accessions.anchor_cik_numeric`; every row's
`registrant_cik_padded` is the canonical ten-digit zero-padded rendering of its own
`registrant_cik_numeric`; no two rows carry the same `registrant_cik_padded`; and the stored
`multi_registrant` flag agrees with the normalized registrant set under §6.2, or diverges in exactly
the one case §6.3 permits. Any failure of any of these is a fail-closed condition, not a weaker
level.

When `multi_registrant = 0` and the normalized structure is consistent:

- `multi_registrant_evidence_level = not_applicable`.

When `multi_registrant = 1` and the normalized structure is consistent:

- the dimension is applicable;
- it is `provisional` **only when every** `anchor` **or** `associated` row that establishes the
  registrant set carries `evidence_level = 'provisional'`;
- when any set-establishing row carries an `evidence_level` other than `provisional`, the aggregate
  is the exact level §6.5's precedence selects — `conflicting`, `review_required`, or `unavailable`,
  never an unnamed "weaker" state — and the accession therefore cannot contribute to the
  multi-registrant quota (Decision 014 §1).

`submitter_only` rows do not affect the aggregate level, because they do not establish the registrant
set.

### 6.5 Deterministic weaker-state precedence

When at least one set-establishing row carries an `evidence_level` other than `provisional`, the
aggregate is the **first present** state in this frozen precedence:

1. `conflicting`;
2. `review_required`;
3. `unavailable`.

This is the conceptual precedence narrowed to the exact migration-`0009` registrant vocabulary:
`unproven` is not an admissible `pilot_candidate_accession_registrants.evidence_level` value and is
not admissible on this pure-input dimension, so it is omitted rather than mapped.

The precedence is evaluated by membership, in the stated order. **No numeric score, ordinal
arithmetic, or floating-point value is introduced** — Decision 013 §5 permits integer and categorical
comparisons only, and this is a categorical comparison.

### 6.6 Resolution provenance without DDL

Decision 014 §1 requires a provisional classification's evidence basis to be stored on the candidate
record, and Decision 016 §4 ties resolved values to a `*_resolution_sha256`. `pilot_candidate_accessions`
has no `multi_registrant_resolution_sha256` column. This record clarifies how Decision 014's
requirement is met for this dimension:

- **the complete canonical sorted registrant-row set is the authoritative resolved representation.**
  The child rows *are* the resolution: unlike size or industry, where a single resolved scalar needs
  a hash pointing back at the evidence that produced it, the multi-registrant classification is
  nothing more than its normalized rows;
- **each row retains its own stable evidence provenance** — its role, anchor flag, canonical CIK
  pair, and `evidence_level` — and each is individually inspectable;
- **Stage S5.2 computes a deterministic registrant-content digest** over the canonical registrant-row
  set for validation and run identity (§10), using the repository's accepted canonical row
  serialization and `hash_table` mechanism (`src/disclosure_drift/release/hashing.py`);
- **no new stored `multi_registrant_resolution_sha256` column is required**, and none is authorized;
- **the computed digest is never written back** into the frozen candidate tables.

#### 6.6.1 The digest, frozen exactly

**One digest per candidate accession.** The digest is computed over the registrant rows of a single
accession and identifies that accession's registrant content only.

- **Table-name / domain label:** the literal string `pilot_candidate_accession_registrants`.
- **Columns, in exactly this order** — the exact migration-`0009` column names of
  `pilot_candidate_accession_registrants`:

  1. `registrant_cik_padded`
  2. `role`
  3. `is_anchor`
  4. `evidence_level`

- **Rows:** **every** registrant row for that accession under that `snapshot_id`, including every
  `submitter_only` row. They are material normalized content even though they establish no
  contribution (§6.2).
- **Serialization and digest mechanism:** the repository's accepted canonical row serialization and
  `hash_table` from `src/disclosure_drift/release/hashing.py`, unmodified. `hash_table` sorts its
  rendered rows before digesting, so the digest is **row-order independent** by construction; no
  additional ordering step is specified, and none is needed.
- **Excluded:** `recorded_at_utc` — every timestamp is excluded from every deterministic hash
  (Decision 016 §8). `snapshot_id` and `accession_plain` are excluded from the digested rows because
  they are constant within one accession's row set and would add nothing.
- **Accession identity is carried in the surrounding run-identity record, not inside the digest**
  (§10). Two accessions with identical registrant content therefore produce identical digests; the
  run-identity record pairs each digest with its accession identity, so the pairing — not the digest
  alone — is what distinguishes them. A digest is never used as an accession identifier.
- **Computed at read time; used for validation and S5 run identity; never written back** into
  `pilot_candidate_accessions` or any other frozen table.

`registrant_cik_numeric` is omitted from the digested columns because §6.2 requires
`registrant_cik_padded` to be the canonical rendering of it on every row, so the two are in
bijection and including both would restate one fact twice.

**This is a controlled clarification of the existing normalized-child-row architecture, not
permission to omit provenance.** Provenance is preserved in full; only the redundant scalar hash
column is declined.

## 7. Ruling 3 — explicit pre-study support provenance

### 7.1 The required marker

`PILOT_ACCESSION_PRE_STUDY_SUPPORT` (Decision 018 §21) is the **required normalized provenance
marker** distinguishing a pre-study accession from one whose cohort evidence is merely absent or
unresolved. Decision 018 §15 requires that distinction to be recorded and does not name the marker;
this record names it.

**Ordering dependency, stated and not waived:** `pilot_candidate_accession_reasons.reason_code` is
foreign-key-constrained to `reference_reason_codes`, which is seeded from
`src/disclosure_drift/reasons.py`. No snapshot can carry this provenance row until the code is
registered. Registration belongs to Stage S5.2 (Decision 018 §21; the S5.2 stage contract's
"Authorized paths") and **is not authorized by this record**.

### 7.2 Frozen mapping

A candidate maps to:

- `cohort_applicability = pre_study`;
- `cohort_evidence_level = not_applicable`;

**only when all of the following are true:**

- original 10-K — `form_type = '10-K'` and `is_amendment = 0`;
- `official_filing_date` falls in calendar year 2009;
- `support_eligible = 1`;
- `base_eligible = 0`;
- `provisional_official_cohort IS NULL`;
- `cohort_ambiguous = 0`;
- **exactly one** normalized `pilot_candidate_accession_reasons` row exists for the accession with
  `reason_code = 'PILOT_ACCESSION_PRE_STUDY_SUPPORT'` and `reason_scope = 'cohort'`;
- no contradictory cohort evidence and no contradictory cohort reason exists.

**A null cohort without that exact provenance row never establishes pre-study applicability.** It is
an unresolved cohort on an accession the study windows still apply to, which is a materially
different condition and is treated as such.

The stored `cohort_evidence_level` of a valid pre-study candidate is **not** carried onto the pure
input: the column is `NOT NULL` over four levels with no `not_applicable` member, so `not_applicable`
is derived, not read. A stored `cohort_evidence_level = 'provisional'` alongside a `NULL`
`provisional_official_cohort` is contradictory cohort evidence and fails closed.

### 7.3 Build-time obligation

Candidate-snapshot construction **must insert the provenance row before snapshot freeze**. Stage S5.2
may validate and consume the row; it **may not create it**, and it may not infer pre-study
applicability from the absence of a cohort.

### 7.4 In-window filings

For an accession whose `official_filing_date` falls inside a study cohort window:

- `cohort_applicability = applies`;
- the stored `provisional_official_cohort` and `cohort_evidence_level` govern, carried through
  unchanged;
- a `NULL`, unresolved cohort **remains applicable** but weak or unavailable — it never becomes
  pre-study.

An accession with an official filing date outside 2009 and outside every study window, and without
the §7.2 provenance, is likewise `applies` with whatever cohort evidence it carries. It simply cannot
take the support or base role.

### 7.5 Fail-closed conditions

The `PILOT_ACCESSION_PRE_STUDY_SUPPORT` reason row fails closed when it appears on:

- an accession whose official filing date is inside a study cohort window;
- an amendment (`is_amendment = 1`);
- an accession whose official filing date is not in calendar year 2009, or is `NULL`;
- a `base_eligible = 1` accession;
- an accession with a non-`NULL` `provisional_official_cohort`, or with `cohort_ambiguous = 1`, or
  with `support_eligible = 0`.

### 7.6 The marker is provenance, not eligibility

The reason row **does not itself make the accession support-role eligible**. The accepted S5.1
`assign_accession_role` remains authoritative for role assignment (Decision 018 §7, §29), including
its requirement that a support accession be an original 10-K filed in 2009 with `support_eligible`
and `cohort_applicability = pre_study` under an operating anchor. This record supplies the
`cohort_applicability` value that function reads; it does not decide roles.

## 8. Ruling 4 — former-name identity evidence

### 8.1 The required representation

Former-name identity evidence is carried by `pilot_candidate_entity_evidence` rows with:

- `classification_dimension = 'identity'`;
- `source_field` exactly `former_name_relationship`;
- an `evidence_role` from the existing vocabulary `('winning', 'competing', 'supporting')`;
- a **non-null `parsed_record_id`** — the parsed-record provenance reference;
- a **strict canonical JSON object** in `canonical_observed_value`.

Migration `0009` leaves `source_field` as unconstrained `TEXT` and `canonical_observed_value` and
`parsed_record_id` nullable, and `pilot_candidate_entity_evidence` carries **no `evidence_level`
column at all**. The `source_field` values, the payload schema, and the derived
`NameChangeEvidence.evidence_level` are therefore all frozen by this record. No DDL is added;
validation is the loader's obligation (§4 principle 10).

#### 8.1.1 Identity storage scope (frozen)

Migration `0009` admits `identity` in more places than Stage S5 supports. The supported boundary is
exactly:

| Stored location | M2.3 Stage S5 treatment |
|---|---|
| `pilot_candidate_entity_evidence` with `classification_dimension = 'identity'` | **The only supported representation.** Consumed by §§8.2–8.5. |
| `pilot_candidate_accession_evidence` with `classification_dimension = 'identity'` | **Unsupported — fails closed.** |
| `pilot_candidate_entity_reasons` with `reason_scope = 'identity'` | **Unsupported — fails closed.** |
| `pilot_candidate_accession_reasons` with `reason_scope = 'identity'` | **Unsupported — fails closed.** |
| Any `identity`-dimension entity-evidence row whose `source_field` is outside `{former_name_relationship, ticker_change}` | **Unsupported — fails closed.** |

**This is a loader validation boundary, not a new deferral.** No quota is relaxed, deferred, or
declared satisfied by it, and the difficult-or-nonstandard-package quota remains the only approved
M2.3 deferral (§3). It is equally **not permission to discard rows silently**: an unsupported row
invalidates the snapshot for Stage S5 under §9 and is reported, never skipped, filtered, or ignored.
A future record may extend the supported set; until one does, Stage S5 has no defined meaning for
these rows and §11's stop-and-request-owner-decision rule would otherwise apply to every one of them.

#### 8.1.2 Structural validation of every permitted identity row

For **every** `pilot_candidate_entity_evidence` row with `classification_dimension = 'identity'`:

- `parsed_record_id` must be **non-null** — on every row, whatever its `evidence_role`;
- `evidence_role` must be in the stored vocabulary `('winning', 'competing', 'supporting')` — which
  migration `0009` already enforces by `CHECK`, restated here because the mapping reads it;
- `source_field` must be exactly `former_name_relationship` or exactly `ticker_change`;
- two rows for the same entity, dimension, and `source_field` carrying **byte-identical**
  `canonical_observed_value` are a duplicated representation of one fact and **fail closed**; they
  are never deduplicated, collapsed, or counted once.

Any failure is a fail-closed condition (§8.4).

### 8.2 Canonical JSON forms

Exactly one of these two structures is permitted, serialized canonically with sorted keys and no
extra keys.

Prior/current form:

```json
{
  "current_name": "<nonempty normalized name>",
  "prior_name": "<nonempty normalized name>",
  "relationship": "prior_current"
}
```

From/to form:

```json
{
  "from_name": "<nonempty normalized name>",
  "relationship": "from_to",
  "to_name": "<nonempty normalized name>"
}
```

Requirements:

- the payload parses under strict JSON and is a JSON object;
- no extra keys, and no missing keys — the key set is exactly one of the two above;
- no null name values, and every value is a JSON string;
- `relationship` is exactly the literal its key set requires;
- **every stored name is already normalized** — each name value is byte-identical to its own
  §8.2.1 normalized form;
- the canonical reserialization equals the stored value byte for byte;
- **malformed free text is never accepted as a former-name record.**

The **content** requirements — names nonempty after normalization, and the two names differing — are
stated separately in §8.4, because they produce `review_required` rather than a gate failure.

**Canonical serialization** is `json.dumps(payload, sort_keys=True, ensure_ascii=False,
separators=(",", ":"))`, encoded UTF-8:

- UTF-8;
- `ensure_ascii = false`;
- sorted keys;
- separators `(",", ":")`;
- no extra keys;
- stored bytes equal the canonical reserialization.

Compact separators and `ensure_ascii=False` are chosen because `canonical_observed_value` is a stored
value compared byte for byte, not a hash payload: a single rendering of a non-ASCII issuer name must
exist, rather than two that differ only by escaping. This introduces no change to
`src/disclosure_drift/release/hashing.py` or to any existing hash contract.

#### 8.2.1 Name normalization (frozen, exactly)

A stored name value is normalized by applying, in this order:

1. decode as valid Unicode — an undecodable value fails closed;
2. normalize to Unicode **NFC**;
3. trim leading and trailing code points for which the implementation language's Unicode whitespace
   predicate is true (in Python, `str.isspace()`);
4. collapse each internal run of one or more Unicode whitespace code points to exactly one `U+0020`
   ASCII space;
5. preserve case and **all** other Unicode characters unchanged.

Steps 3 and 4 together are exactly Python's `" ".join(value.split())`, whose whitespace predicate is
`str.isspace()` and therefore includes non-ASCII whitespace such as `U+00A0`. This is stated rather
than left to inference: an ASCII-only reading would accept `U+00A0` inside a name and a Unicode
reading would not, and the two readings must not both be available.

**Normalization is a validation test, not a rewrite.** Stage S5.2 never normalizes a stored value and
proceeds on the result. It computes the normalized form, compares it byte for byte with the stored
name, and **fails closed on any difference** (§8.4). Canonical reserialization alone cannot detect a
non-normalized name — `json.dumps` preserves a string's contents exactly, so `"  ACME  "`
reserializes to itself — which is why this is an explicit, separate test rather than a consequence of
the byte-equality requirement.

Step 5 preserves non-whitespace control code points rather than stripping them. A name containing one
is therefore canonical if it is otherwise well formed; rejecting such names would be a content rule
this record does not make, and is available to a future record if the project wants it.

### 8.3 Mapping to `NameChangeEvidence`

The evidence is entity-level: it populates `EntityCandidate.name_change` for the anchor entity's CIK
within the same frozen snapshot.

#### 8.3.1 Deterministic procedure

Let **R** be the set of `pilot_candidate_entity_evidence` rows for that CIK under that `snapshot_id`
with `classification_dimension = 'identity'`. Apply, in this order:

1. **Gate.** Apply §8.1.1 (storage scope) and §8.1.2 (structural validation) to every row of R, and
   §8.2 to every `former_name_relationship` row. Any failure fails closed; nothing below runs.
2. **Partition.** Let **F** be the rows of R with `source_field = former_name_relationship`, and
   **T** the rows with `source_field = ticker_change`.
3. **Ticker flag.** Derive `ticker_change_claimed` from T alone, per §8.5. It is derived
   **independently** in every case below and never affects any other field.
4. **Branch.** Let **W** be the rows of F with `evidence_role = 'winning'`, and **N** = F \ W. Select
   exactly one branch by the size of F, W, and N, in the order given by the table.

Branch selection is total and mutually exclusive: F is either empty or not; when it is not, `|W|` is
0, 1, or ≥ 2; when `|W|` is 1 its payload either passes the §8.4 content tests or does not.
`|W| ≥ 2` reaches its branch only with distinct payloads, because byte-identical winning duplicates
already failed closed at step 1.

#### 8.3.2 Frozen output table

| # | Branch condition | `has_identity_evidence` | `evidence_role` | `evidence_level` | `former_name_record_parseable` | `has_prior_current_or_from_to` | `ticker_change_claimed` |
|---|---|---|---|---|---|---|---|
| 1 | `F` empty and `T` empty — no identity rows | `false` | `supporting` | `unavailable` | `false` | `false` | `false` |
| 2 | `F` empty, one valid ticker row — ticker-only | `true` | `supporting` | `unavailable` | `false` | `false` | `true` |
| 3 | `\|W\| = 1`, its payload passes the §8.4 content tests | `true` | `winning` | `provisional` | `true` | `true` | §8.5 |
| 4 | `\|W\| = 1`, row structurally valid but its payload fails a §8.4 content test | `true` | `winning` | `review_required` | `false` | `false` | §8.5 |
| 5 | `\|W\| = 0` and `\|N\| ≥ 1` | `true` | `competing` if any row of `N` has `evidence_role = 'competing'`, otherwise `supporting` | `review_required` | `true` iff at least one row of `N` has a payload passing the §8.4 content tests, else `false` | equals `former_name_record_parseable` | §8.5 |
| 6 | `\|W\| ≥ 2` with distinct canonical payloads | `true` | `winning` | `conflicting` | `true` iff **every** row of `W` has a payload passing the §8.4 content tests, else `false` | equals `former_name_record_parseable` | §8.5 |

Every cell is a value, not a range. No branch leaves a field to the implementation, and no branch
admits `None` for `evidence_role`.

#### 8.3.3 Rules the table encodes

- **Branch 5 is `review_required`, never `unavailable`.** Non-winning former-name rows are evidence
  that exists and requires review; `unavailable` means "no approved M2.3 source carries this field
  for this candidate" (Decision 014 §1), which is false whenever a former-name row is present.
- **Competing or supporting rows never override a single valid winning row.** Branch 3 is selected on
  `|W| = 1` regardless of how many rows `N` holds. Those rows remain material normalized content and
  are carried into run identity (§10) in full.
- **One payload is never picked silently.** Branch 6 reports `conflicting`; it does not choose a
  winner, and the entity does not contribute to the name-change quota.
- **Byte-identical duplicate winning rows never reach branch 6.** They are structural corruption and
  fail closed at step 1 (§8.1.2, §8.4); they are never deduplicated into a single winner.
- **Only branch 3 contributes** to the M2.3 name-change quota, because the accepted S5.1
  `_name_change_contributes` requires `has_identity_evidence`, `evidence_role = winning`,
  `evidence_level = provisional`, `former_name_record_parseable`, and `has_prior_current_or_from_to`
  together. Branches 4, 5, and 6 each fail at least one of those and contribute nothing.
- **`former_name_record_parseable` in branches 5 and 6 records structure, not contribution.** The
  accepted S5.1 core reads that field together with `has_prior_current_or_from_to` to count the
  *structural* name-change pool behind Decision 017's `excluded_pool_count`. Reporting `true` there
  is what makes such an entity visible as a candidate excluded by its evidence gate, rather than
  invisible; it grants no contribution, which remains gated on branch 3 alone.
- **The ticker flag is orthogonal.** In branches 3–6 it is whatever §8.5 derives from T, and it
  changes no other cell.

### 8.4 The strict fail-closed versus `review_required` distinction

**Fail closed — structural corruption.** The stored row is not an instance of the required
representation, and the snapshot is invalid for Stage S5:

- an `identity` evidence or reason row in an unsupported location, per §8.1.1;
- the `identity`-dimension `source_field` is outside `{former_name_relationship, ticker_change}`;
- `parsed_record_id` is `NULL` on **any** `identity`-dimension entity-evidence row;
- `evidence_role` outside `('winning', 'competing', 'supporting')`;
- two rows for one entity, dimension, and `source_field` carry byte-identical
  `canonical_observed_value` — including two `winning` former-name rows;
- on a `former_name_relationship` row: `canonical_observed_value` is `NULL` or empty;
- the payload does not parse under strict JSON, or is not a JSON object;
- the key set is not exactly one of the two permitted key sets;
- any value is not a JSON string, including `null`;
- `relationship` is not exactly the value its key set requires (`prior_current` for the
  prior/current form, `from_to` for the from/to form);
- a stored name value is not byte-identical to its own §8.2.1 normalized form;
- a stored name value is not decodable as valid Unicode;
- the canonical reserialization does not equal the stored value;
- any §8.5 ticker-row condition is violated.

**`review_required` — content tests.** A structurally well-formed, canonical `former_name_relationship`
row whose **content** cannot support the required relationship. The content tests are exactly:

- a required name is empty after §8.2.1 normalization;
- the two names are equal, or equal ignoring ASCII case — a re-rendering of one name is not a name
  change.

A row failing either test is a row whose payload "fails a §8.4 content test" in §8.3.2. It never
contributes and never raises the level above `review_required`.

The distinction is exact: **structure decides whether the snapshot is valid at all; content decides
what the valid row is worth.** Every condition above is a stored-state test; none is a judgement.

### 8.5 Ticker evidence

A separate `identity`-dimension entity-evidence row may use the exact `source_field`:

```text
ticker_change
```

**Required representation, frozen.** For a `ticker_change` row:

- **at most one** such row may exist per entity within the snapshot;
- `parsed_record_id` must be **non-null**;
- `canonical_observed_value` must be **`NULL`** — M2.3 freezes no ticker payload interpretation, so
  there is no permitted ticker payload schema and a non-null value is an interpretation this record
  does not define;
- its stored `evidence_role` is recorded in run identity (§10) but **never** determines the derived
  former-name `evidence_role`, which is fixed by the §8.3.2 branch alone.

**Frozen derivation of `ticker_change_claimed`:**

| Stored condition | `ticker_change_claimed` |
|---|---|
| No `ticker_change` row for the entity | `false` |
| Exactly one `ticker_change` row, `parsed_record_id` non-null, `canonical_observed_value` `NULL` | `true` |
| Two or more `ticker_change` rows for the entity | **fail closed** |
| One `ticker_change` row with `canonical_observed_value` non-null | **fail closed** |
| One `ticker_change` row with `parsed_record_id` `NULL` | **fail closed** |

The derivation is total: the flag is `true`, `false`, or the snapshot is rejected. Nothing here is
optional.

Beyond that:

- a ticker row **never** satisfies the M2.3 name-change quota;
- it **never** substitutes for a former-name row;
- its **absence produces no warning** — absence of ticker evidence is the expected M2.3 condition
  (Decision 018 §13) and sets the flag to `false` rather than raising anything;
- **no ticker-verification methodology is introduced**, and no ticker-warning reason code is created
  (Decision 018 §21).

### 8.6 Why a valid winning row is `provisional` and not `verified`

- **M2.3 admits provisional evidence only.** Every M2.3 source is metadata-only; `verified` requires
  retrieval-verified, document-level evidence (Decision 014 §1), which is an M2.5 obligation. The
  Stage S3 schema encodes this: no candidate evidence-level column admits `verified` at all.
- **The evidence row and its stable provenance establish the winning candidate-level identity
  record** — `parsed_record_id`, `source_observation_id`, `policy_version`, `precedence`, and
  `evidence_sha256` together satisfy Decision 014 §1's requirement that a provisional
  classification's evidence basis be stored on the candidate record.
- **No outcome, filing text, or future verification is used** to reach this level (Decision 018 §23;
  Decision 015).

## 9. Snapshot-freeze obligations

**A candidate snapshot is not valid for Stage S5 when any applicable candidate cannot be mapped
losslessly into the accepted S5.1 inputs under §§5–8.**

At freeze time — and again at Stage S5.2 read time, because a frozen snapshot may predate these
requirements — the following must be validated:

- **linkage-state and parent consistency** (§5): vocabulary membership, the amendment/original
  invariants, canonical parent form, direct-parent presence in the same snapshot, and agreement
  between the linkage state and the `REVIEW_AMENDMENT_PARENT_UNRESOLVED` reason row;
- **state-specific parent type and chain termination** (§5.4.1, §5.4.2): every resolved state's
  direct parent carries the `is_amendment` value its state requires, no chain revisits an accession,
  and every resolved chain terminates at an original;
- **amendment acceptance ordering** (§5.9): every resolved state whose chain terminates at a root
  original inside the snapshot carries an `acceptance_audit_date`, as does that root original; both
  are exact, real `YYYY-MM-DD` calendar dates; and the amendment's is **strictly later** than the
  root original's. Earlier, equal, missing, malformed, and otherwise incomparable dates each
  invalidate the snapshot for Stage S5, because the conforming representation of every one of them
  is `unresolved_amendment` (§5.9.2), not a resolved state;
- **normalized registrant aggregation** (§6): exactly one anchor, anchor/CIK agreement, canonical
  padded CIKs, no duplicate registrant identities, and `multi_registrant`-flag agreement subject to
  the single exact-code exception of §6.3;
- **the pre-study provenance row** (§7): present with the exact code and scope where pre-study
  applicability is claimed, and absent everywhere it would be contradictory;
- **identity storage scope** (§8.1.1): no `identity`-dimension accession-evidence row, no
  `identity`-scope entity or accession reason row, and no `identity` `source_field` outside
  `{former_name_relationship, ticker_change}`;
- **identity row structure** (§8.1.2): non-null `parsed_record_id` on every identity row, a stored
  `evidence_role`, and no byte-identical duplicate rows for one entity, dimension, and
  `source_field`;
- **former-name canonical payloads** (§8.2): strict parse, permitted key set, string-only values,
  the exact `relationship` literal, stored names already normalized under §8.2.1, and canonical
  reserialization equality;
- **ticker-row representation** (§8.5): at most one per entity, non-null `parsed_record_id`, `NULL`
  `canonical_observed_value`;
- **duplicate and contradictory reason and evidence rows**: no reason row contradicting the stored
  state it describes, and no duplicated normalized representation of a single fact.

**No production snapshot is silently rewritten, backfilled, migrated, or repaired**; a non-conforming
snapshot is rejected (§4 principle 9).

### 9.1 Candidate-builder boundary

Every representation requirement in §§5–8 is an obligation on a **future production
candidate-snapshot builder**. That component does not exist: no candidate-snapshot builder exists
anywhere in `src/disclosure_drift/` today, and no approved record authorizes writing one. The
boundary is therefore stated explicitly so that no session mistakes either side of it:

- **This record freezes the obligations that builder must satisfy.** It does not authorize building
  it, and nothing here is a builder specification, plan, or schedule.
- **Stage S5.2 may be implemented, tested, and completed against conforming temporary snapshots.**
  Its required tests construct temporary SQLite databases; that is sufficient for the whole of the
  Stage S5.2 contract, and the absence of a production builder blocks none of it.
- **Stage S5.2 never creates or repairs candidate evidence or reason rows.** It reads, validates, and
  converts (§4 principles 5–6). It may not insert the §7 pre-study provenance row, may not
  synthesize an identity or registrant row, and may not normalize a non-conforming snapshot into a
  conforming one.
- **Production use of Stage S5 remains blocked** until a separately authorized builder can
  materialize snapshots conforming to this record. A conforming production snapshot is a
  precondition of a production S5 run, not of S5.2's completion.
- **This future dependency does not alter Stage S5.2's persistence scope**, does not widen the S5.2
  stage contract, and does not authorize builder implementation now. Authorizing it requires its own
  owner instruction and, if it needs rules this record does not state, its own decision record
  (§11).

## 10. Run identity

The Stage S5 candidate-content and selection-input identity must include **all material normalized
content used by these mappings**:

- `amendment_linkage_state` and the stored plain parent identity, per candidate accession;
- **`acceptance_audit_date` for every frozen candidate accession** in the snapshot, whether or not
  any §5.9 check reads that particular row. The simpler complete rule is deliberate: it necessarily
  includes the amendment candidate's own stored `acceptance_audit_date`, that of **every** accession
  on its parent chain, and that of its **transitive root original** (§§5.4.2, 5.9), and it removes
  any question of which rows a given snapshot's checks happened to touch;
- the normalized unresolved-parent reason rows (`REVIEW_AMENDMENT_PARENT_UNRESOLVED`);
- **every** registrant row and its `evidence_level` — including `submitter_only` rows — and the
  derived per-accession registrant-content digest (§6.6.1), each digest paired in the identity
  record with the `accession_plain` whose rows it covers, so that two accessions with identical
  registrant content remain distinguishable;
- the `multi_registrant`-scope reason rows §6.3 reads, whether or not they authorize a divergence;
- the pre-study provenance reason row (`PILOT_ACCESSION_PRE_STUDY_SUPPORT`, scope `cohort`);
- identity evidence `evidence_role`, `source_field`, `canonical_observed_value`, `policy_version`,
  `precedence`, `parsed_record_id`, and `evidence_sha256` — for **every** identity row, including
  `competing` and `supporting` former-name rows that no branch of §8.3.2 selects, and including the
  `ticker_change` row;
- all other relevant evidence and reason identities that any mapping above consults.

**Excluded**, per Decision 016 §8 and Decision 018 §26: every timestamp column and wall-clock read,
every free-text `detail` column, operational event IDs, process identity, filesystem paths, database
and insertion row order, Python object representations, mutable lifecycle state, the S4 entity-only
result and its `selection_run_id`, and any outcome or future information. Timestamp columns and
free-text detail remain excluded unless a governing hash contract already requires them; none does.

**`acceptance_audit_date` is not reached by that exclusion, and its inclusion is not an exception to
it.** Decision 016 §8 excludes every *timestamp* column — `retrieved_at_utc`, the operational
`recorded_at_utc` family, and event times — as provenance-envelope and wall-clock data.
`acceptance_audit_date` is not such a column:

- it is a **frozen candidate classification input** on `pilot_candidate_accessions`, stored as a
  **calendar date, not a timestamp** (§5.9.1), alongside the other candidate date columns;
- it **affects loader validation and linkage applicability** — it determines whether an accession may
  be mapped to provisional amendment-linkage evidence at all, or must be represented and read as
  unresolved (§§5.9.2–5.9.3);
- it is therefore **material candidate content** in exactly the sense this section's opening sentence
  requires, and is **included**.

Mutable lifecycle timestamps, operational event timestamps, wall-clock reads, and `recorded_at_utc`
remain excluded without exception, including from the §6.6.1 registrant digest. Nothing here
redefines Decision 016 §8; it states which side of that rule an existing date column falls on.

**Row order must not matter.** A permutation of semantically identical rows must produce the same run
identity — `release/hashing.py`'s `hash_table` sorts rendered rows before digesting, which is the
mechanism Decision 016 §8 already relies on.

Any material change to the content above changes the S5 `selection_run_id`, exactly as Decision 018
§26 requires of every other identity input. In particular, **a material change to any frozen
candidate accession's stored `acceptance_audit_date` must change the accession-candidate content
hash and the S5 `selection_run_id`.**

## 11. Decision relationships

- **This record clarifies Decision 018 §§5.3, 13, 15, 19, and 25.** It resolves what those sections
  require the loader to read and validate; it changes none of them.
- **Decision 018's pure-versus-persistence boundary (§19) remains unchanged.** Every methodological
  rule still lives in the accepted pure core; the adapter converts and calls.
- **Decision 018's no-DDL ruling (§25) remains unchanged.** Schema impact is **none** (§12).
- **Decision 008 §2 is implemented, not extended.** §5.4.1 states which parent type each of
  Decision 008 §2.1's three resolved states already means, and §5.9 states which stored field
  expresses Decision 008 §2.2's acceptance-ordering rule at M2.3. Neither adds a relationship state,
  changes a state's meaning, nor creates a new reason code; both make an existing definition
  checkable against the frozen schema. §5.9's refusal to admit equal, missing, malformed, or
  incomparable dates as resolved ordering reaches beyond Decision 008 §2.2's literal
  strictly-earlier wording; it is the evidence boundary of a day-granularity column rather than a new
  methodological rule, and it is recorded as such in §18.
- **Decision 014's evidence requirements remain in force**, with the §6.6 clarification that for the
  multi-registrant dimension the normalized child rows are themselves the resolved representation and
  their provenance, so no additional resolution-hash column is required.
- **Decision 016's normalized evidence and reason architecture remains unchanged** (§§4, 9). This
  record names specific `source_field` values, a payload schema, and a reason marker within that
  architecture; it adds no new architectural layer.
- **Decision 017's excluded-pool semantics remain unchanged.**
- **Decision 013 §5's objective, and Decision 018 §3's reading of it, are untouched.**
- **The accepted Stage S5.1 code and tests are not modified**, and no accepted S5.1 expected output
  is relaxed to accommodate persistence.
- **The Stage S5.2 adapter implements these mappings mechanically** once separately authorized.
- **Any mapping not addressed here remains a stop-and-request-owner-decision condition.** A rule this
  record does not answer is never inferred.

## 12. Schema impact

**None.** No table, column, constraint, index, or trigger is created, altered, or dropped, and no
existing migration is edited. Migrations `0009` and `0010` are unchanged; migration `0011` remains
the INSERT-only policy-reference seeding approved by Decision 018 §20 and is not created, widened, or
repurposed by this record.

Specifically **not** added, and not authorized: a `multi_registrant_resolution_sha256` column, a
`cohort_applicability` column, an `amendment_linkage_evidence_level` column, an `amendment_linkage`
member of `classification_dimension`, a format `CHECK` or foreign key on
`provisional_parent_accession`, any `CHECK` restricting `amendment_linkage_state` against the
parent row's `is_amendment`, any acceptance-**timestamp** column, any `NOT NULL` or format `CHECK` on
the existing `acceptance_audit_date`, any narrowing of the freeze trigger's `multi_registrant`
reason-scope test, and any constraint over `source_field` or `canonical_observed_value`. Each is a
loader-computed value or a loader-validated invariant.

`pilot_candidate_accessions.acceptance_audit_date` (§5.9.1) is an **existing** migration-`0009`
column, used as stored and as typed. Nothing in §5.9 adds, alters, or constrains it, and nothing in
this record reads an `inventory_*` or `census_*` acceptance column.

If the frozen schema is ever found genuinely insufficient for one of these mappings, that is an
owner-level schema conflict — stop and report (CLAUDE.md rule 12). It is never a licence to add DDL.

## 13. Leakage controls

Every ruling in this record is a mechanical representation or conversion choice over frozen,
authorized SEC metadata and candidate evidence. None reads, fits on, or is informed by any 2022–2026
outcome. Stage S5 continues to use no outcome value, no pilot membership as a methodological input,
no post-boundary information, no filing text, no CompanyFacts value, no Frames data, and no
later-resolved classification unavailable at the snapshot boundary (Decision 018 §23).

Acceptance date remains audit-only for cohort purposes; official filing date remains authoritative
for cohort assignment (Decision 010). §7's pre-study rule reads `official_filing_date` only.

Decision 015's prohibitions and `Docs/leakage_register.md` L15/L19 apply in full and are unaffected.

## 14. Failure behavior

Every fail-closed condition in §§5.8, 6.3, 7.5, 8.4, and 9 is a stop-and-report condition in the
sense of CLAUDE.md rule 12. None may be worked around, relaxed, defaulted, or resolved by dropping
the offending rows. Malformed input fails before search begins (Decision 018 §17), and a candidate
that cannot be mapped losslessly invalidates the snapshot for Stage S5 rather than being silently
excluded from the pool.

## 15. Rationale

- **Naming the representation, rather than inferring it, is what keeps the adapter from becoming a
  second methodological implementation.** Decision 018 §19 forbids a rule living in two places. Four
  pure-input fields had no stored counterpart, so an unblocked S5.2 session would have had to invent
  one — precisely the duplicate that §19 exists to prevent.
- **`review_required` and `unavailable` for the two unresolved linkage states** preserve
  Decision 008 §2.1's own distinction between named-but-unproven parentage and unestablishable
  parentage, while staying inside the evidence vocabulary the accepted S5.1 core admits. Both behave
  identically in selection, so the distinction costs nothing methodologically and preserves
  provenance.
- **Dropping the parent pointer for unresolved states** is what actually delivers Decision 018
  §10.2's singleton diagnostic family. Carrying an unresolved candidate parent onto the pure input
  would silently resolve the family, and the resulting selection would claim linkage coverage the
  evidence does not support.
- **Registrant child rows as their own resolution** avoids a schema change that would buy nothing:
  the classification *is* its rows, each already carrying evidence provenance, so a scalar hash
  column would restate rather than add. Computing the digest at read time keeps provenance complete
  and the frozen tables untouched.
- **An explicit pre-study marker** is the only way to satisfy Decision 018 §15's requirement that the
  record "be able to tell the two apart". A `NULL` cohort is ambiguous between "outside the frozen
  windows by design" and "cohort evidence absent"; the first must receive no cohort penalty under
  Decision 018 §3.4 and the second must, so the distinction has to be stored, not derived.
- **A strict canonical payload for former names** is what makes `former_name_record_parseable`
  meaningful. Decision 018 §13 makes the name-change quota hard *because* name evidence is measurable;
  that only holds if "parseable" has one frozen definition rather than a per-implementation guess.
- **Fail-closed for structure, `review_required` for content** keeps two genuinely different failures
  apart: a corrupt row means the snapshot is not what it claims to be and nothing downstream can be
  trusted, whereas a well-formed row that cannot prove a name change is ordinary weak evidence the
  selector is designed to rank.
- **State-specific parent types (§5.4.1) exist because the accepted core would otherwise repair the
  contradiction silently.** `derive_amendment_families` walks to the first non-amendment ancestor, so
  `amends_original` pointing at an amendment resolves to that chain's root and earns affirmative
  linked-amendment coverage the stored evidence never asserted. The schema cannot catch it — no
  foreign key, no `CHECK` — so either the loader rejects it or nothing does.
- **Acceptance ordering (§5.9) is checked against the root original, not the immediate parent**,
  because an amendment may legitimately precede an earlier amendment of the same filing but can never
  precede the original it amends.
- **Only a strictly later date admits a resolved state**, because a resolved linkage state is an
  affirmative claim and `acceptance_audit_date` has day granularity. Treating equal dates as
  satisfying the ordering would read a precision into the column that it does not have, and would let
  a same-day pair earn affirmative linked-amendment coverage (Decision 018 §10.4) on evidence that
  establishes nothing about order. The same holds for a missing, malformed, or incomparable date:
  "not observed to be earlier" is not "observed to be later", and only the second is what a resolved
  state asserts. Naming that limit and failing closed on it (§5.9.4) keeps the boundary visible
  rather than silently converting absent evidence into affirmative evidence.
- **The exact-code multi-registrant exception (§6.3)** matters because a scope is not a fact. The
  freeze trigger can only test `reason_scope`; the divergence it admits is meaningful for exactly one
  recorded condition, and reading the trigger's mechanism as the policy would let any future
  `multi_registrant`-scope code silently authorize a flag that contradicts the registrant rows.
- **A complete six-field output table (§8.3.2)** replaces per-field prose because `NameChangeEvidence`
  is an immutable pure input: every field must have exactly one value for a given stored state.
  Prose that names a direction instead of a level, or that makes a field conditional on the reader's
  judgement, leaves the adapter choosing — precisely the second methodological implementation
  Decision 018 §19 forbids. Every cell of the table is a literal.
- **Non-winning former-name rows are `review_required`, not `unavailable`**, because `unavailable`
  asserts that no approved source carries the field (Decision 014 §1) — false whenever a former-name
  row exists. Reporting their structural parseability is what lets Decision 017's
  `excluded_pool_count` see them as candidates excluded by an evidence gate rather than as candidates
  that never existed.

## 16. Required tests

Required once Stage S5.2 is separately authorized; they extend, and do not replace, the categories
already named in [`Milestones/contracts/m23_s5_2.md`](../../Milestones/contracts/m23_s5_2.md).

- each of the five `amendment_linkage_state` values maps to its frozen level, and the `NULL`
  non-amendment state maps to `not_applicable` (§5.2);
- an unresolved state with a stored parent yields a singleton family and no linked-amendment
  contribution (§5.5);
- a resolved state whose parent is absent from the snapshot maps to `review_required` (§5.6);
- **each §5.4.1 parent-type mismatch fails closed** — `amends_original` and `supplements_original`
  pointing at an `is_amendment = 1` row, and `amends_prior_amendment` pointing at an
  `is_amendment = 0` row — and none of them reaches S5.1 to be resolved transitively;
- **a valid `amends_prior_amendment` chain** whose direct parent is an amendment and whose chain
  terminates at an original maps to `provisional`, and a **cycle** fails closed (§5.4.2);
- **acceptance ordering at read time** (§5.9.3), one case per row of that table: a resolved state
  whose amendment date is **strictly later** than its resolved root original's is admitted, and each
  of strictly earlier, **equal**, `NULL` on either endpoint, malformed on either endpoint, and
  otherwise incomparable **fails closed**; in every failing case the loader neither downgrades the
  state, nor rewrites or re-points the parent, nor creates a `REVIEW_AMENDMENT_PARENT_UNRESOLVED`
  row, nor reads any `inventory_*` or `census_*` acceptance column, nor manufactures a timestamp; the
  comparison for an `amends_prior_amendment` chain is against the transitive root original, not the
  immediate parent; and a resolved state whose parent is **absent** from the snapshot takes §5.6's
  `review_required` rather than an ordering failure;
- **acceptance-ordering classification at candidate-snapshot construction** (§5.9.2), exercised over
  constructed fixtures as a representation requirement: a snapshot in which a same-day, earlier,
  missing-date, malformed-date, or incomparable-date amendment carries a resolved linkage state is
  rejected, and the conforming representation of each of those cases is `unresolved_amendment` with
  `provisional_parent_accession = NULL` and a `REVIEW_AMENDMENT_PARENT_UNRESOLVED` row, which maps to
  `unavailable`, a singleton family, and no linked-amendment contribution;
- registrant aggregation: `submitter_only` establishes nothing; one anchor plus one associated with
  all-`provisional` rows yields `provisional`; each weaker state wins by the §6.5 precedence;
- the §6.3 divergence is admitted **only** with exactly one `multi_registrant`-scope reason row whose
  code is exactly `REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE`; any other code at that scope, more than
  one such row, or none fails closed; and `multi_registrant = 1` without a qualifying set always
  fails closed even though migration `0009` freezes it;
- the per-accession registrant-content digest (§6.6.1) uses the frozen label and column order, is
  permutation-invariant, includes `submitter_only` rows, excludes timestamps, and is never written
  back;
- pre-study mapping requires the exact reason code and scope; a `NULL` cohort without it stays
  `applies`; each §7.5 misplacement fails closed;
- **identity storage scope** (§8.1.1): an `identity`-dimension accession-evidence row, an
  `identity`-scope entity or accession reason row, and an unknown identity `source_field` each fail
  closed;
- both §8.2 canonical JSON forms parse, reserialize identically, and map to branch 3 of §8.3.2; a
  stored name that is not already normalized under §8.2.1 fails closed, including one differing only
  by `U+00A0` or by NFC form;
- **every branch of the §8.3.2 table is exercised and produces exactly its frozen six-field output**,
  including branch 1 (`supporting`/`unavailable`), branch 2 (ticker-only), branch 4
  (`winning`/`review_required`), branch 5 (`competing` when any competing row exists, otherwise
  `supporting`, always `review_required`, never `unavailable`), and branch 6
  (`winning`/`conflicting`);
- competing and supporting rows alongside a single valid winning row do not change branch 3's output,
  and remain in run identity;
- byte-identical duplicate `winning` rows fail closed rather than being deduplicated;
- two distinct winning payloads yield `conflicting` with no contribution and no silent pick;
- a `ticker_change` row sets only `ticker_change_claimed`, satisfies no quota, never determines the
  former-name `evidence_role`, and its absence produces no warning; two ticker rows, a non-null
  ticker payload, and a `NULL` `parsed_record_id` each fail closed (§8.5);
- **`acceptance_audit_date` is in run identity** (§10): changing the stored value on any frozen
  candidate accession — including an accession no §5.9 check reads — changes the accession-candidate
  content hash and the S5 `selection_run_id`, while a row permutation does not;
- every §10 input changes the run identity when it changes, row permutation does not, and two
  accessions with identical registrant content remain distinguishable through the digest/accession
  pairing.

## 17. Deferred work

- **Stage S5.2 implementation**, migration `0011`, reason-code registration, and the joint policy
  constant — approved by Decision 018 §§20–21, authorized by neither that record nor this one.
- **Stage S5.4 (reserves)** and **Stage S6 (manifest)** — unchanged and unauthorized.
- **The production candidate-snapshot builder** that must materialize the representations §§5–8
  require (§9.1) — no record authorizes it, and this one does not.
- **M2.5 verification obligations** carried forward unchanged: document-level verification of every
  provisional classification (Decision 014 §1), ticker-change contributions (Decision 018 §13),
  amendment parentage, and the difficult-or-nonstandard-package quota (Decision 018 §14).
- **Higher-resolution acceptance ordering is a future-stage capability, not a deferred M2.3
  obligation.** M2.3 has no unmet ordering gate: §5.9 disposes of every same-day, earlier, missing,
  malformed, and incomparable case now, by refusing to treat any of them as resolved (§5.9.4). A
  future authorized stage may establish sub-day ordering from a frozen higher-resolution acceptance
  source, which would allow some presently-unresolved same-day amendments to become resolvable; no
  such source is authorized here, and **no quota, count, or verification requirement is deferred,
  relaxed, or declared satisfied** by this record (§3).

## 18. Controlled deviations

**None beyond the two clarifications stated explicitly above**, neither of which relaxes a
requirement:

1. **§6.6** — the multi-registrant dimension satisfies Decision 014's provenance requirement through
   its complete normalized child-row set and a read-time digest, rather than through a stored
   resolution-hash column. Provenance is preserved in full; only a redundant column is declined.
2. **§6.3** — the stored `multi_registrant` flag may diverge from the normalized registrant set only
   in a narrowing of the single case migration `0009`'s freeze trigger admits: the trigger tests only
   `reason_scope = 'multi_registrant'`, while this record additionally requires exactly one such row
   carrying exactly `REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE`. Every other divergence fails closed,
   which is stricter than the trigger alone.

**Validation stricter than the frozen schema, recorded so it is not mistaken for drift.** Three
rulings reject stored states that migration `0009` can freeze, because the schema cannot express the
constraint and the loader is the only place it can be checked (Decision 018 §5.3 assigns exactly that
role):

- §5.4.1 and §5.4.2 — state-specific parent type and chain termination. Migration `0009` places
  neither a foreign key nor a `CHECK` on `provisional_parent_accession`.
- §5.9 — amendment acceptance ordering, admitted only on a **strictly later** stored date.
  `acceptance_audit_date` is nullable and unconstrained, so migration `0009` can freeze an amendment
  that is same-day with, earlier than, or undated relative to its root original while still carrying
  a resolved linkage state; only the loader can reject it.
- §6.3 and §8.1.1 — the exact-code multi-registrant exception, and the identity storage scope.

Each **tightens** validation; none relaxes a requirement, defers a quota, or admits a state the
schema forbids. Each restates an obligation an approved record already carries — Decision 008 §2.1
and §2.2 for parentage and acceptance ordering, Decision 013 for the recorded multi-registrant
condition — rather than creating a new methodological rule.

**One point reaches further than the literal text it implements, and is recorded as such.**
Decision 008 §2.2 names the strictly-earlier case: "an amendment accepted before its alleged original
is `unresolved_amendment` plus review". §5.9 additionally refuses resolved status to equal, missing,
malformed, and incomparable dates. That is neither a new methodological rule nor a deferral: it is
the evidence boundary of a day-granularity column (§5.9.4). A resolved linkage state is an
affirmative claim, and Decision 018 §§10.2 and 10.4 already require affirmative linkage to be
evidenced rather than assumed, so declining to infer an ordering the stored field cannot express
applies an existing requirement instead of adding one. The disposition of every affected accession
— unresolved singleton family, no linked-amendment contribution, provenance retained — is exactly
the one Decision 018 §10.2 already specifies for unresolved parentage.

No deviation from Decisions 013–018 is made or implied. No transition metric and no final-test metric
has been viewed in connection with this record.

## 19. Approval statement

**APPROVED — OWNER APPROVED 2026-07-28.** The project owner approved this record on 2026-07-28,
after the final independent audit of it, and approved it **as written**. The audit's recommendation
was `ACCEPT_DECISION_019_FOR_OWNER_APPROVAL`; it found no ambiguities, no implementation blockers, no
scope violations, total and deterministic mappings, compatibility with the accepted Stage S5.1 core,
no required DDL, no new quota deferral, and governance consistency across the active records. The
audit's four documentation-precision notes were **nonblocking** and do not alter the approved
mappings; no substantive text of this record was revised at approval, and the optional §5.4.2 wording
refinement was **not** applied.

This record is now binding and is the **controlling record** for the four frozen
storage-to-pure-input mappings it freezes: amendment-linkage evidence conversion (§5),
multi-registrant evidence aggregation (§6), explicit pre-study support provenance (§7), and
former-name identity-evidence conversion (§8), together with the snapshot-freeze obligations (§9)
and the run-identity content those mappings contribute (§10).

What approval does **not** do:

- **It does not modify the accepted Stage S5.1 core.** No S5.1 code, test, or expected output changes
  (§11), and none may be relaxed to accommodate persistence.
- **It does not itself implement Stage S5.2.** No code, test, migration `0011`, reason-code
  registration, or policy constant is created by this approval (§§3, 17).
- **It does not become self-executing.** Approval cleared the `BLOCKED_PENDING_DECISION_019` blocker
  — Stage S5.2 is `READY_FOR_IMPLEMENTATION` with implementation authorization **YES** — but
  implementation may begin only under a **separately issued, revised bounded Stage S5.2
  implementation prompt**, within the exact authorized paths of
  [`Milestones/contracts/m23_s5_2.md`](../../Milestones/contracts/m23_s5_2.md). That contract's
  scope is unchanged and is not widened by this approval.

Any later **substantive** change to the mappings frozen here requires a new decision amendment and a
fresh independent review; it is never made by editing this record in place. The combined S5.1–S5.3
commit boundary (Decision 018 §22) is unchanged: no commit, push, or tag is authorized before S5.3
acceptance.
