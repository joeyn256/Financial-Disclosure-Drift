# Decision 018 — M2.3 Stage S5 Accession Selection Policy

**Date:** 2026-07-28
**Status:** Approved by project owner
**Type:** Implementation and provenance decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged by this record. No hypothesis, cohort window, maturity gate,
outcome definition, threshold, or seed is altered.
**Supersedes:** nothing. Freezes the accession-specific interpretation of policy left open by
[Decision 013](decision_013_pilot_selection_mechanics.md) §5 (D10) and enumerated as open in
[`Milestones/contracts/m23_s5_1.md`](../../Milestones/contracts/m23_s5_1.md) ("Not frozen by this
contract") and [`Docs/decision_index.md`](../decision_index.md) ("Decision 018 — pending").
**Governs:** Milestone 2.3, Stage S5 onward.
**Related:** [Decision 002](decision_002_primary_outcome.md) (primary-universe boundary),
[Decision 007](decision_007_sec_universe.md) (canonical CIK identity),
[Decision 008](decision_008_filing_inventory.md) §2 (amendment policy),
[Decision 010](decision_010_temporal_availability_and_cohort_assignment.md) (cohort date-source
rule), [Decision 013](decision_013_pilot_selection_mechanics.md) (selection mechanics — counting
units, multi-registrant accounting, selector policy, reserves, manifest hashing),
[Decision 014](decision_014_pilot_evidence_and_classification_policy.md) (evidence levels,
classification, provisional cohort), [Decision 015](decision_015_pilot_use_prohibition.md)
(pilot-use prohibition), [Decision 016](decision_016_m23_schema_and_artifact_architecture.md)
(schema and artifact architecture), [Decision 017](decision_017_s4_quota_policy_and_control_evidence.md)
(S4 quota-policy version, `excluded_pool_count`, boundary-control evidence).

This record **operationalizes** accession-specific meaning for Stage S5. It does not supersede
Decisions 013–017 except where it explicitly resolves a question those records left open. Decision
013 §5's lexicographic objective order is preserved exactly and is neither reordered nor split.

**This record authorizes no implementation.** No code, test, migration, reason code, or policy
constant is created by it. The active stage contract
([`Milestones/contracts/m23_s5_1.md`](../../Milestones/contracts/m23_s5_1.md)) governs the next
bounded implementation, and implementation begins only on a separate, explicit instruction.

## 1. Scope

This record freezes, for Stage S5 only:

- the accession-specific reading of Decision 013 §5's objective terms (§2–§3 below);
- accession role assignment, caps, and floors (§7–§9, §11);
- canonical accession representation, the tie-break hash, and identity fallback (§4);
- the disposition of the accepted S4 entity-only draft and the identity of the S5 joint run (§5);
- accession-family and amendment-linkage semantics (§10);
- cross-cutting quota operationalization, including the controlled deferral of one genuinely
  unmeasurable quota (§12–§16);
- search-completeness, failure, and retry semantics (§17–§18);
- the S5.1/S5.2 methodological boundary (§19);
- the future joint-selector policy version, future additive migration `0011`, and the future reason
  codes S5 will require (§20–§21);
- the S5.1–S6 stage boundaries (§22) and S5's leakage controls (§23).

## 2. Non-scope

This record does **not**:

- reorder, split, merge, or reweight Decision 013 §5's objective terms;
- alter the accepted Stage S4 entity selector, its persisted artifacts, or its entity-side evidence
  behavior (§3 states this explicitly);
- alter any frozen research definition — cohort windows, maturity gates, the primary outcome,
  thresholds, or the bootstrap seed remain owned by `src/disclosure_drift/cohorts.py` and Decisions
  002/003/005/010;
- alter migrations `0009` or `0010`, or any table, column, constraint, index, or trigger they define;
- create, rename, or retire any reason code, policy constant, module, or test;
- authorize reserve-package work (Stage S5.4) or any manifest work (Stage S6);
- relax, remove, or declare satisfied any frozen quota. §16's treatment of the
  difficult-or-nonstandard-package quota is a **controlled stage deferral**, not satisfaction.

## 3. Frozen ruling — the joint objective and its evidence term

### 3.1 Objective order (unchanged from Decision 013 §5)

The S5 joint entity-accession selection uses exactly this lexicographic order:

1. satisfy all hard quotas;
2. minimize the single integer unresolved/provisional-evidence penalty;
3. minimize base-accession count;
4. minimize stress-accession count;
5. minimize the complete sorted entity-hash vector;
6. minimize the complete sorted accession-hash vector;
7. canonical identity fallbacks after hash equality.

Decision 018 clarifies the meaning of individual terms. It does not reorder or split them. Decision
013 §5's accompanying requirements — integer and categorical comparisons only, no floating-point
objective, explicit input ordering fixed before search, deterministic branch ordering, a
deterministic search-node limit, `infeasible_or_unproven` on exhaustion, and identical results from
an identical input snapshot — remain in force unchanged.

### 3.2 Term 2 is one integer

Objective term 2 is a single non-negative integer:

```text
term_2 = sum(selected entity penalties) + sum(selected accession penalties)
```

There is no separate entity sub-term and no separate accession sub-term; introducing either would
split a frozen term. **No floating-point penalty is permitted** at any point in its computation,
accumulation, or comparison.

### 3.3 Accepted S4 entity behavior is preserved

**This record does not define, redefine, or retrofit the entity-side penalty.** The accepted Stage
S4 entity selector and every S4 persisted artifact remain exactly as checkpointed at
`m2.3-s4-complete` (`e7157aa`). Decision 017 §4's statement of the entity objective is unchanged.
Any change to entity-side penalty behavior would require its own decision record and is out of scope
here.

### 3.4 Applicability-aware accession penalty

Each **applicable** evidence dimension on a selected accession contributes:

| Evidence condition | Contribution |
|---|---|
| `provisional` | 0 |
| weaker than `provisional` | 1 |
| structurally not applicable | 0 |

The applicable dimensions are:

- **filing-date evidence** — always applicable;
- **cohort evidence** — applicable only where a study cohort applies to the accession;
- **XBRL evidence** — always applicable;
- **amendment-purpose evidence** — applicable only when the accession is an amendment;
- **amendment-linkage evidence** — applicable only when the accession is an amendment.

**Structural inapplicability is not a penalty.** A valid pre-study 2009 support accession (§15) has
no applicable study cohort, and therefore receives **no cohort penalty** merely because its cohort
columns are unavailable or `NULL`. The same principle applies to amendment-purpose and
amendment-linkage evidence on an original accession: those dimensions do not apply, so they
contribute zero rather than one.

This is the substantive difference between the entity and accession sides of term 2. An entity that
fails an evidence gate is excluded from selection outright; an accession may be legitimately
selected while carrying weaker-than-`provisional` evidence on a dimension it is not being used to
affirm. The penalty exists to rank such accessions, and applicability-awareness keeps it from
punishing an accession for a dimension that structurally does not exist for it.

## 4. Frozen ruling — deterministic selected accession order

Selected accessions are persisted in ascending order by, in this exact precedence:

1. `accession_tie_break_sha256`;
2. `anchor_cik_padded`;
3. `accession_number_dashed`.

`selected_order` is assigned as **contiguous integers 1..N** over that ordering, where N is the
count of selected accessions in the run.

**Accession role and entity `selected_order` do not enter this key.** The ordering is therefore a
pure function of accession identity, independent of role assignment and independent of how entities
were ordered. Because the tie-break hash is unique per accession under §5's formula, and because
`accession_number_dashed` is unique within a snapshot, the key is total and the resulting order is
deterministic.

Per [Decision 016](decision_016_m23_schema_and_artifact_architecture.md) §8, `selected_order` is a
materialized integer inside the hashed column list. This ordering rule is therefore part of the
frozen identity contract and cannot be revised without invalidating every hash computed under it.

## 5. Frozen ruling — canonical accession representation and identity

### 5.1 Canonical form

The **dashed** SEC accession form

```text
NNNNNNNNNN-NN-NNNNNN
```

is canonical for:

- accession tie-break hashing;
- canonical identity fallback (objective term 7);
- deterministic presentation;
- future manifest representation (Stage S6).

The **plain** 18-character form remains the persisted database and foreign-key column
(`pilot_candidate_accessions.accession_plain` and every table referencing it). This is a storage
convention, not a competing identity: the two forms denote the same accession and must agree.

### 5.2 Tie-break formula

```text
SHA256(
  selection_seed
  + "|"
  + anchor_cik_padded
  + "|"
  + accession_number_dashed
)
```

rendered as lowercase 64-character hexadecimal SHA-256.

**Associated registrant CIKs do not enter this identity hash.** Only the anchor CIK does. A
multi-registrant accession's identity therefore cannot drift when its associated-registrant set is
later corrected or extended — the accession satisfies the multi-registrant quota once regardless of
registrant count ([Decision 013](decision_013_pilot_selection_mechanics.md) §4), and its identity is
equally independent of that count.

### 5.3 Fail-closed loader obligations

A future loader must fail closed unless both hold:

- the plain and dashed forms of every candidate accession are mutually consistent;
- the stored accession tie-break hash matches the §5.2 formula exactly.

This mirrors the accepted entity-side precedent, where the S4.2 loader verifies both the canonical
CIK rendering and the stored entity tie-break hash before admitting a candidate.

## 6. Frozen ruling — the S4 draft and the S5 joint run

The accepted Stage S4 entity-only running draft:

- **remains unchanged**;
- **remains in `running` state**;
- is **non-publishable**;
- is **never** mutated, deleted, promoted, or used as a manifest source.

The S5 joint entity-accession result receives a **new deterministic content-derived
`selection_run_id`**. Only the S5 joint run may advance toward publication.

Decision 018 **freezes** this rule. It was previously recorded only as an S5 preflight proposal and
as an open question in the stage contract and in `Docs/architecture_map.md`; it is now accepted
policy and those documents are updated accordingly.

Nothing in this section changes Decision 016 §5's `pilot_selection_runs` lifecycle, which continues
to govern whatever run row S5 produces.

## 7. Frozen ruling — accession roles

Every selected accession receives **exactly one** mutually exclusive role:

| Role | Definition |
|---|---|
| **Control** | An original annual report selected for a boundary-control entity. |
| **Support** | An original 10-K filed in calendar year 2009, anchored to a selected operating entity, with `support_eligible = 1`, outside the study cohorts. |
| **Base** | An original 10-K, anchored to a selected operating entity, with `base_eligible = 1`. |
| **Stress** | An eligible 10-KT, 10-K/A, or 10-KT/A, anchored to a selected operating entity. |

**Anything else fails role classification** and is not selectable.

Counting consequences:

- **Support and control accessions count toward the total-accession cap only** (§8's 120 limit).
- **Control accessions do not count toward base or stress totals**, and therefore never enter
  objective terms 3 or 4 through the base or stress counts.

Because role is a function of the accession's own frozen attributes and its anchor entity's role —
never of which quota it happens to serve — role assignment cannot be used to move an accession
between objective terms 3 and 4.

## 8. Frozen ruling — accession caps

Restated here as accepted Decision 018 rules (previously stated only in
`Milestones/milestone_2_3_pilot_selection_plan.md` §4.2):

- no more than **4** base accessions per selected operating CIK;
- no more than **96** base accessions total;
- no more than **24** stress accessions total;
- no more than **120** selected accessions across all roles.

These are **hard constraints, not penalty terms**. A candidate solution violating any of them is
infeasible; it is never merely disfavored by the objective.

## 9. Frozen ruling — entity accession floors

Hard requirements on any feasible S5 result:

- every selected **operating** entity has at least one selected **base** accession;
- every selected **control** entity has at least one selected **control-role** accession;
- every selected entity anchors at least one selected accession.

A zero-accession or partially anchored entity result **can never be feasible or publishable**. This
closes the failure mode in which objective term 3 (minimize base-accession count) would otherwise
drive a selected entity to zero accessions, producing a manifest that claims entity coverage the
selection does not actually supply.

## 10. Frozen ruling — accession families and amendments

### 10.1 Family definition and identity

An **accession family** is the transitive amendment chain rooted at an original accession. Family
identity is the **canonical dashed accession number of the resolved root original**.

### 10.2 Unresolved parentage

Unresolved parentage:

- creates a **singleton diagnostic family**;
- **cannot** satisfy linked-amendment coverage;
- **fails closed** for affirmative linkage contribution.

### 10.3 Family identity is diagnostic, not identifying

Family identity:

- does **not** enter the accession tie-break hash;
- does **not** enter `selected_order`;
- does **not** create a separate cap.

Parentage, linkage state, and related provenance **do** remain part of candidate content hashing and
quota evidence. The distinction is deliberate: parentage is provisional metadata at M2.3 and may be
corrected by M2.5 verification. Keeping it inside candidate content hashing preserves its provenance;
keeping it out of the tie-break hash and out of `selected_order` prevents a later verification
correction from altering a selection identity or a frozen manifest hash.

### 10.4 Linked-amendment coverage

An amendment contributes to linked-amendment coverage **only when all three hold**:

- its parentage resolves to an original accession;
- the resolved root original is **also selected in the same joint run**;
- the accepted evidence requirements are met.

### 10.5 Amendment invariants

An amendment **never** replaces, re-dates, or re-cohorts its original. This restates, and does not
extend, `Milestones/milestone_2_3_pilot_selection_plan.md` §6 and
[Decision 008](decision_008_filing_inventory.md) §2.

## 11. Frozen ruling — controls in cross-cutting quotas

A selected control may contribute to a cross-cutting quota when **both** hold:

- the accepted quota definition uses *distinct entities* or *distinct accessions* without explicitly
  restricting contribution to operating or primary-universe entities;
- the control carries the same required evidence as any other contributor.

Control accessions never count toward base or stress totals (§7).

## 12. Frozen ruling — fiscal-year-end changes

An entity contributes to fiscal-year-end-change coverage when **either**:

- it has a selected 10-KT or 10-KT/A; **or**
- consecutive selected original annual reports have a **circular calendar month-day distance greater
  than seven days** between their `report_date` values.

**Circular calendar distance is required** so that a year boundary is handled correctly — a shift
from late December to early January is a small distance, not a large one, and a non-circular
comparison would misclassify it.

The seven-day tolerance exists so that 52/53-week fiscal calendars, whose year-end date legitimately
drifts by a few days without any change of fiscal year end, do not register as changes.

**Missing required `report_date` values fail closed and do not contribute.**

## 13. Frozen ruling — name and ticker changes

M2.3 remains **name-only** for this quota, consistent with
[Decision 013](decision_013_pilot_selection_mechanics.md) §3.

- An entity contributes **only** through provisional winning identity evidence derived from a
  parseable former-name record.
- **Ticker-only claims do not contribute until M2.5.**
- **No warning is created merely because ticker evidence is absent.** Absence of ticker evidence is
  the expected M2.3 condition, not an anomaly. A warning is appropriate only when code actually
  attempts to use a ticker-change claim that lacks the required evidence.
- **This quota remains hard**, because name-change evidence is measurable from authorized candidate
  evidence.

## 14. Frozen ruling — the difficult-or-nonstandard filing-package quota

The frozen required count **remains six**. The property is **not measurable** from authorized M2.3
metadata, because it is a document-level characteristic and every M2.3 evidence source is
metadata-only.

Therefore, for Stage S5:

- it is **excluded from hard-feasibility calculations**;
- **no proxy or manufactured evidence is permitted**;
- it is persisted as **`unproven`** with evidence state **`unavailable`**;
- `achieved_count = 0`;
- `eligible_pool_count = 0`;
- it is **non-binding** for S5;
- it remains a **mandatory M2.5 verification obligation**.

**This is a controlled stage deferral, not satisfaction or removal of the requirement.** The project
may **not** claim full quota verification until M2.5 resolves it.

**This ruling applies only to genuinely unmeasurable quotas.** Measurable quotas — including
multi-registrant coverage, which is directly observable from authorized candidate metadata — remain
hard. Decision 016 §9's rule against silently deferring the multi-registrant quota is unaffected:
that quota is measurable, stays hard, and is reported with its true `eligible_pool_count` when it
binds.

## 15. Frozen ruling — 2009 support and 2010 target pairs

**2009 support accession:**

- original 10-K;
- official filing date in calendar year 2009;
- no applicable study cohort;
- `support_eligible = 1`;
- **distinguished from missing cohort evidence by explicit provenance** — a pre-study accession is
  outside the frozen windows by design, which is not the same condition as cohort evidence being
  absent or unresolved, and the record must be able to tell the two apart.

**2010 target accession:**

- original 10-K;
- official filing date in calendar year 2010;
- provisional official cohort = `development`;
- role = base.

**A valid pair:**

- shares one anchor CIK;
- contains one support and one target accession;
- counts once per distinct entity.

The frozen requirement remains **six distinct entities**
([Decision 013](decision_013_pilot_selection_mechanics.md) §3).

## 16. Frozen ruling — hard, deferred, and measurable quotas

For clarity across §§8–15, a quota falls into exactly one of three dispositions at Stage S5:

| Disposition | Effect on objective term 1 | Persisted result |
|---|---|---|
| **Hard and measurable** | Binding — must be satisfied for feasibility | `pass` or `fail` per its `comparison_operator` |
| **Deferred as unmeasurable** (§14 only, at present) | Excluded from feasibility | `unproven` / `unavailable`, non-binding, M2.5 obligation |
| **Hard but unsatisfiable in the pool** | Binding — the run is infeasible | `fail`, reported as a binding constraint with its true `eligible_pool_count` |

A hard quota is never converted to a deferred quota because the pool cannot satisfy it. The third
row is the correct outcome in that case.

## 17. Frozen ruling — node limit and failure semantics

The node limit is:

- an **explicit positive integer run input**;
- **included in deterministic run identity**;
- **shared through one counter across every search phase**.

**No arbitrary numeric production default is frozen by this record.** The value is a run input;
selecting a production default is an implementation and operations matter, and because the limit
enters run identity, changing it visibly changes the run.

Exhaustion in **any** phase:

- **discards every feasible incumbent**;
- returns `infeasible_or_unproven`;
- records `node_limit_exhausted`;
- returns **no approved selection**.

Additionally:

- **malformed input fails before search begins**;
- a proven infeasible result **contains no selected result**;
- **no partial accession selection may ever be represented as approved.**

## 18. Frozen ruling — retry behavior

- **No automatic retry is authorized.**
- **No S5 retry entry point is authorized.**
- A same-ID row in `failed`, `planned`, or incomplete-`running` state **causes a gate failure**.
- Manual recovery orchestration is **deferred to a later operational stage** and requires separate
  authorization.

Automatic retry over a deterministic solver would be meaningless — identical input yields identical
output — so a retry can only ever recover from an environment fault, which is an operator decision
rather than a selector behavior. Decision 016 §5's `failed → running` transition remains defined in
the schema and is simply not exercised by any S5 module.

## 19. Frozen ruling — pure core versus persistence

**Stage S5.1 (pure core) owns the deterministic policy functions for:**

- accession role assignment;
- applicability-aware evidence penalties;
- amendment-family derivation;
- fiscal-year-end-change derivation;
- name-change contribution;
- quota contribution and diagnostics;
- joint entity-accession optimization.

**Stage S5.2 (persistence adapter):**

- reads frozen rows;
- validates canonical forms and stored hashes;
- constructs the pure S5.1 inputs;
- invokes the pure functions;
- derives deterministic run identity;
- persists and reconstructs results.

**The SQLite adapter must not become a second methodological implementation.** Every methodological
rule in this record lives in exactly one place — the pure core — and the adapter calls it. A rule
re-expressed in SQL, in a query predicate, or in adapter-local Python is a duplicate implementation
that can silently diverge, and is prohibited.

## 20. Frozen ruling — joint-selector policy version and migration `0011`

The following executable constant is **approved for future creation**:

```python
PILOT_JOINT_SELECTOR_POLICY_VERSION = "m23-joint-selector-policy-v1"
```

A future **additive migration `0011`** is approved to seed this exact policy value using the accepted
migration `0010` pattern.

Rules:

- migration `0011` is **INSERT-only**;
- **no DDL**;
- **migrations `0009` and `0010` are not edited**;
- the accepted S4 selector-policy version (`PILOT_SELECTOR_POLICY_VERSION`) is **unchanged**, so the
  checkpointed S4 artifact stays byte-stable;
- S5 joint runs store the new version as `selector_policy_version`;
- implementation of the constant and the migration belongs to **Stage S5.2**, not to this
  decision-drafting phase.

**Neither the constant nor the migration is created by this record.** `src/disclosure_drift/pilot_policy.py`
and `src/disclosure_drift/storage/migrations/` are untouched by this decision.

## 21. Frozen ruling — reason codes

Exactly these **five** new reason codes are approved for future creation:

| Code | Purpose |
|---|---|
| `PILOT_ACCESSION_CAP_EXCEEDED` | A per-CIK or global accession cap (§8) would be exceeded. |
| `PILOT_ENTITY_ACCESSION_FLOOR_UNMET` | A selected entity fails an accession floor (§9). |
| `PILOT_ACCESSION_PRE_STUDY_SUPPORT` | The accession precedes the frozen study windows and is eligible only as a support accession (§15). |
| `REVIEW_PILOT_QUOTA_UNMEASURABLE_AT_M23` | The quota is not measurable from authorized M2.3 metadata and is deferred under §14. |
| `REVIEW_PILOT_ACCESSION_ROLE_UNCLASSIFIED` | The accession's frozen attributes do not map to exactly one role (§7). |

**Existing codes are reused, not duplicated,** for:

- **unresolved amendment parentage** — `REVIEW_AMENDMENT_PARENT_UNRESOLVED`
  ([Decision 008](decision_008_filing_inventory.md));
- **run-level infeasibility** — `PILOT_SELECTION_INFEASIBLE`;
- **infeasible-or-unproven node exhaustion** — `PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN`.

**No retry code and no ticker-warning code is added.** §13 explains why an absent ticker claim is
the expected condition rather than a warnable one, and §18 explains why no retry entry point exists
to emit a retry code.

**`src/disclosure_drift/reasons.py` is not modified by this record.** These codes are approved for a
future implementation stage.

## 22. Frozen ruling — stage boundaries

**S5.1**

- pure accession-candidate and joint-selection core;
- the pure methodological functions listed in §19;
- adversarial in-memory tests;
- **no** SQLite, persistence, reconstruction, reserves, manifests, or migration work.

**S5.2**

- frozen reader;
- canonical validation;
- the joint policy constant (§20);
- additive migration `0011` (§20);
- deterministic run identity;
- transactionality;
- persistence;
- reconstruction;
- idempotence.

**S5.3**

- independent adversarial review;
- combined S5.1–S5.3 acceptance checkpoint;
- **one commit boundary**, unless later explicitly changed by the project owner.

**S5.4**

- reserve packages;
- reserve accession rows;
- replacement and substitution signatures.

**S6**

- final manifest construction;
- publication;
- final root-manifest hashing.

**No manifest work is authorized before S6.**

## 23. Leakage controls

Stage S5 uses only frozen, authorized SEC metadata and candidate evidence. It **must not** use:

- outcome values;
- pilot membership as an input to methodological choices;
- post-boundary information;
- filing text;
- CompanyFacts values;
- Frames data;
- later-resolved classifications unavailable at the snapshot boundary.

**Acceptance date remains audit-only for cohort purposes. Official filing date remains authoritative
for cohort assignment** ([Decision 010](decision_010_temporal_availability_and_cohort_assignment.md)).

Every rule in this record is a mechanical or provenance choice about how metadata-only candidates are
classified, ranked, and selected. None reads, fits on, or is informed by any 2022–2026 outcome. The
prohibitions in [Decision 015](decision_015_pilot_use_prohibition.md) and
`Docs/leakage_register.md` L15/L19 apply to Stage S5 in full and are unaffected by this record.

## 24. Rationale

Each ruling above closes a specific gap that made Stage S5.1 unimplementable from Decision 013 §5
alone, without changing anything Decision 013 already froze.

- **Applicability-aware penalties (§3.4)** exist because accessions and entities differ in kind: an
  entity failing an evidence gate is excluded outright, so its penalty is uniform among admissible
  candidates, whereas an accession may be legitimately selected while carrying weaker evidence on a
  dimension it is not affirming. A flat "count the non-provisional dimensions" rule would have
  penalized a valid 2009 support accession for lacking a cohort it structurally cannot have.
- **Identity-only ordering (§4) and dashed canonicalization (§5)** keep selection identity a pure
  function of accession identity. Excluding role, entity order, associated registrants, and family
  identity from the hashed identity means later corrections to any of those — all of which are
  provisional at M2.3 — cannot alter a frozen selection or manifest hash.
- **A distinct S5 run with the S4 draft preserved (§6)** keeps the accepted S4 artifact immutable
  while allowing the joint optimum to differ from it, which it legitimately may once accession-level
  terms and cross-cutting quotas enter the problem.
- **Role assignment from frozen attributes (§7)** prevents role from becoming a selector choice,
  which would let a solution move accessions between objective terms 3 and 4 to improve its own
  score.
- **Caps as hard constraints and floors as hard requirements (§8–§9)** together bound the accession
  set from both directions. Without the floors, term 3 would drive selected entities toward zero
  accessions and produce a manifest claiming coverage it does not supply.
- **Family identity as diagnostic rather than identifying (§10.3)**, combined with the requirement
  that a linked amendment's root original be co-selected (§10.4), makes linked-amendment coverage
  mean what the pilot needs it to mean — an actually retrievable original/amendment pair — without
  letting provisional parentage into an identity hash.
- **The controlled deferral (§14)** is the only disposition that is simultaneously honest (no proxy,
  no manufactured evidence, count unchanged at six), visible (persisted every run as `unproven` with
  a dedicated reason code), and finishable (excluded from feasibility so a genuinely unmeasurable
  property cannot deadlock M2.3). Silently dropping it, inventing a metadata proxy, or leaving it
  binding were all rejected.
- **Circular month-day distance (§12)** is required for correctness at the year boundary; the
  seven-day tolerance exists so that 52/53-week filers are not misread as changing their fiscal year
  end.
- **No frozen node-limit default (§17)** keeps an operations parameter out of a methodology record
  while still making it visible: because the limit enters run identity, any change to it changes the
  run's hash.
- **One methodological implementation (§19)** prevents the persistence adapter from becoming a second
  place where a rule lives and can silently drift.

## 25. Schema impact

**None.** No table, column, constraint, index, or trigger is created, altered, or dropped by this
record, and no existing migration is edited.

Every ruling above is expressible within the Stage S3 table family already approved by Decision 016
§3 and implemented by migration `0009`, together with migration `0010`:

- accession roles (§7) fit `pilot_selected_accessions.accession_role`, whose approved value set is
  already `base`/`stress`/`support`/`control`;
- accession quota results and members (§§8–16) fit `pilot_quota_results` and
  `pilot_quota_result_members`, whose `member_kind` already admits `accession` and whose
  `quota_dimension`/`quota_key` are unconstrained text;
- the §14 deferred-quota row is expressible as `quota_result = 'unproven'` with
  `evidence_state = 'unavailable'`, which the approved constraints permit;
- a pre-study 2009 support accession (§15) is expressible with a `NULL`
  `provisional_official_cohort` and `base_eligible = 0`, which the approved constraints already
  require of such a row;
- two selection runs over one snapshot (§6) are already permitted — nothing constrains a snapshot to
  a single run.

The **only** approved future schema-adjacent change is additive migration `0011` (§20), which is
INSERT-only, adds no DDL, and belongs to Stage S5.2. **It is not created by this record.**

## 26. Hashing and identity impact

- The accession tie-break hash is frozen at §5.2, lowercase 64-hex SHA-256, over
  `selection_seed | anchor_cik_padded | accession_number_dashed`.
- Associated registrant CIKs, accession role, entity `selected_order`, and family identity are all
  **excluded** from that hash.
- `selected_order` (§4) is a materialized hashed column per Decision 016 §8; its assignment rule is
  therefore part of the frozen identity contract.
- The S5 joint run's `selection_run_id` is **content-derived and distinct** from the S4 draft's
  (§6).
- The node limit enters deterministic run identity (§17).
- Decision 016 §8's exclusions remain in force without exception: absolute paths, SEC identity,
  secrets, outcome values, filing text, free-text `detail` columns, operational event IDs, and
  **every timestamp** are excluded from every deterministic hash.
- No existing hash contract is redefined. Nothing in this record changes any hash already computed
  under Stage S3 or Stage S4.

## 27. Lifecycle impact

- Decision 016 §5's `pilot_selection_runs` lifecycle is **unchanged**.
- The S4 entity-only draft stays `running` permanently and is never promoted, mutated, deleted, or
  published (§6). A permanently-`running` S4 draft is expected residue, not an abandoned run.
- Only the S5 joint run may reach `feasible` and advance toward publication.
- `failed → running` remains defined in the schema but is **exercised by no S5 module** (§18).
- Snapshot and manifest lifecycles are untouched by this record.

## 28. Failure behavior

- **Malformed input fails before search begins** (§17).
- **Role classification failure** is a candidate-level failure; an accession whose frozen attributes
  do not map to exactly one role (§7) is not selectable.
- **Cap violation** (§8) and **floor violation** (§9) are infeasibility conditions, never penalties
  and never warnings.
- **Node-limit exhaustion** in any phase discards every incumbent and yields `infeasible_or_unproven`
  with `node_limit_exhausted` recorded and no approved selection (§17).
- **A proven infeasible result contains no selected result**, and **no partial accession selection
  may ever be represented as approved** (§17).
- **A same-ID run row in `failed`, `planned`, or incomplete-`running` state causes a gate failure**
  (§18).
- Unresolved amendment parentage **fails closed** for affirmative linkage contribution (§10.2), and
  missing `report_date` values **fail closed** for fiscal-year-end contribution (§12).

Every one of these is a stop-and-report condition in the sense of CLAUDE.md rule 12. None may be
worked around, relaxed, or resolved by dropping the offending rows.

## 29. Implementation ownership by sub-stage

| Ruling | Owning sub-stage |
|---|---|
| §3 objective and applicability-aware penalty | S5.1 |
| §4 selected-order rule | S5.1 computes the ordering; S5.2 persists `selected_order` |
| §5.1–§5.2 canonical form and tie-break formula | S5.1 |
| §5.3 loader fail-closed obligations | S5.2 |
| §6 S4-draft disposition and distinct S5 run identity | S5.2 |
| §7 role assignment | S5.1 |
| §8 caps, §9 floors | S5.1 |
| §10 families and linked-amendment coverage | S5.1 |
| §11 control contribution | S5.1 |
| §12 fiscal-year-end derivation | S5.1 |
| §13 name-change contribution | S5.1 |
| §14 deferred-quota result | S5.1 produces the diagnostic; S5.2 persists it |
| §15 2009/2010 pairing | S5.1 |
| §17 node limit and failure semantics | S5.1 (search); S5.2 (recorded run fields) |
| §18 retry prohibition and gate failure | S5.2 |
| §20 policy constant and migration `0011` | S5.2 |
| §21 reason codes | S5.1/S5.2 as each code's emission point requires |

Nothing in this table authorizes work. It states which sub-stage owns each ruling once that
sub-stage is separately authorized.

## 30. Required tests

Required once the corresponding sub-stage is authorized. These extend, and do not replace, the
adversarial test categories already named in
[`Milestones/contracts/m23_s5_1.md`](../../Milestones/contracts/m23_s5_1.md).

**S5.1 (pure, in-memory):**

- role assignment is total and mutually exclusive; an unclassifiable accession is rejected (§7);
- 10-KT and 10-KT/A classify as stress, never base (§7);
- applicability-aware penalty: `provisional` scores 0, weaker scores 1, structurally inapplicable
  scores 0; a valid 2009 support accession receives **no** cohort penalty (§3.4);
- term 2 is a single integer over entities plus accessions, with no floating-point value anywhere in
  its computation (§3.2);
- the objective is solved **jointly** — a case where the entity-optimal choice is not
  accession-optimal;
- caps enforced per-CIK and globally; floors enforced for operating, control, and anchor coverage
  (§8–§9);
- family derivation over transitive chains, including cycle rejection and singleton isolation
  (§10.1–§10.2);
- linked-amendment coverage requires the resolved root original to be co-selected (§10.4);
- fiscal-year-end derivation uses **circular** month-day distance and handles the year boundary;
  52/53-week drift within seven days does **not** contribute; missing `report_date` fails closed
  (§12);
- name-change contribution requires provisional winning identity evidence; ticker-only does not
  contribute and produces **no** warning by its absence alone (§13);
- 2009/2010 pairing requires one anchor CIK, one support and one target, counted once per distinct
  entity (§15);
- the deferred quota is excluded from feasibility and reported as `unproven`/`unavailable` with
  `achieved_count = 0` and `eligible_pool_count = 0`, and a feasible run is still reachable with it
  outstanding (§14);
- node-limit exhaustion discards a feasible incumbent and returns `infeasible_or_unproven` with an
  empty selection (§17);
- malformed and duplicate accession inputs are rejected before search begins (§17);
- deterministic reproducibility across repeated runs and across input orderings;
- canonical hashing determinism across process runs (§5.2).

**S5.2 (persistence):**

- the loader fails closed on plain/dashed inconsistency and on a stored tie-break hash that does not
  match the §5.2 formula (§5.3);
- `selected_order` is contiguous 1..N over the §4 key, and role and entity order do not affect it;
- the S5 joint `selection_run_id` is content-derived and distinct from the S4 draft's, and the S4
  draft is byte-unchanged after a joint run executes (§6);
- a same-ID row in `failed`, `planned`, or incomplete-`running` state raises a gate failure (§18);
- the deferred-quota row satisfies every `pilot_quota_results` constraint as persisted (§14);
- idempotence and exact reconstruction from persisted rows;
- `comparison_operator`-aware quota evaluation and composite `(selection_run_id, snapshot_id)`
  foreign-key integrity (Decision 016 §6);
- migration `0011` seeds exactly `m23-joint-selector-policy-v1`, adds no DDL, and leaves
  `PILOT_SELECTOR_POLICY_VERSION` unchanged (§20).

## 31. Deferred work

- **Stage S5.4 — reserves.** Reserve packages, reserve accession rows, and replacement/substitution
  signatures (Decision 013 §6, Decision 016 §7). Not authorized here.
- **Stage S6 — manifest.** Construction, publication, and final root-manifest hashing. Not
  authorized here; no manifest work before S6.
- **Manual recovery orchestration.** Deferred to a later operational stage, requiring separate
  authorization (§18).
- **M2.5 verification obligations** carried forward: the difficult-or-nonstandard-package quota
  (§14); ticker-change contributions (§13); document-level verification of every provisional
  classification (Decision 014 §1).
- **Production node-limit default.** An operations decision, deliberately not frozen here (§17).

## 32. Controlled deviations

Two rulings are recorded explicitly as controlled deviations so that neither is mistaken for silent
drift:

1. **§14, the difficult-or-nonstandard-package quota.** Excluding a frozen quota from S5 feasibility
   is a deliberate, recorded stage deferral approved by the project owner. The required count is
   unchanged at six, no proxy is permitted, the quota is persisted and visible on every run, and it
   remains a mandatory M2.5 obligation. The project may not claim full quota verification until M2.5
   resolves it. This is scoped to genuinely unmeasurable quotas only.
2. **§8, caps restated from the milestone plan.** The four accession caps previously had authority
   only through `Milestones/milestone_2_3_pilot_selection_plan.md` §4.2. They are restated verbatim
   here so the selector cites a decision record rather than a milestone plan. The values are
   unchanged; only their authority is clarified.

No other deviation from Decisions 013–017 is made or implied. No transition metric and no final-test
metric has been viewed in connection with this record.

## 33. Approval statement

The project owner approved every ruling in §§3–23 of this record on 2026-07-28.

This record freezes accession-selection policy for Stage S5. It **authorizes no implementation**: no
code, test, migration, reason code, or policy constant is created by it. Stage S5.1 implementation
begins only on a separate, explicit instruction, and is bounded by
[`Milestones/contracts/m23_s5_1.md`](../../Milestones/contracts/m23_s5_1.md), which remains the
governing stage contract. The combined S5.1–S5.3 commit boundary is unchanged.
