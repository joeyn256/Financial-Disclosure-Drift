# Decision 067 — M3.3 Snapshot Authority, Offline Parse Prerequisite, and Source-to-Candidate Identity

```text
STATUS: ACCEPTED — OWNER M3.3 GOVERNANCE RULINGS
        CONTRACT ACCEPTANCE PENDING INDEPENDENT REVIEW
DATE: 2026-08-13
OWNER: Sol/GPT
OUTCOME: M3_3_SNAPSHOT_AUTHORITY_AND_OFFLINE_PARSE_OWNER_RULED
IMPLEMENTATION_AUTHORIZATION: NO
REAL_PRIVATE_PARSE_AUTHORIZATION: NO
REAL_SNAPSHOT_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: none
```

**This is a governance authority record. It is not implementation authorization.** It rules on
methodology and identity questions that were open; it starts no work, enables no network, opens no
catalog, parses nothing, freezes nothing, and accepts no contract. The corrected
[M3.3 contract](../../Milestones/contracts/m3_3.md) remains **unaccepted** and must first pass a
**fresh independent contract review** by a session that authored neither this record nor that
contract.

**Where this record and an earlier governing record disagree**, this record controls only on the
points it names. Decisions 001–066 remain byte-unchanged, and every M3.2 accepted fact stands.

---

## 1. Entry state

Verified live before this record was written.

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD / `origin/main` | `0401bfdc4669db9237e78548fbd572a0aa14a255` |
| Working tree | clean |
| Latest accepted decision at entry | **Decision 066** |
| M3.3 contract | `DRAFT` — **not owner-accepted** |
| M3.3 implementation | **not authorized** |
| M3.3-G governance foundation | **owner-accepted** |
| M3.3-GR proposal | present at [`Docs/m3/m3_3_snapshot_authority_adjudication_proposal.md`](../m3/m3_3_snapshot_authority_adjudication_proposal.md) |
| M3.3-GV2 evidence result | `M3_3_GV2_PARSE_AND_IDENTITY_VERIFIED_READY_FOR_OWNER_ADJUDICATION` |
| `m3.2-complete` | unchanged, immutable historical tag |
| Migration chain | `0001`–`0013` |
| Tracked network switches | `network.enabled` `false`; `network.m3_acquire_enabled` `false` |

Three commits remain distinct and are never conflated: the accepted M3.2 implementation baseline
`5c4c875e89ea588acd7c04414a05e566c647b39c`; the Decision 065 closeout commit
`2185f5835a711963659cf7c4067ff5a8b88349b9`, which carries the tag; and the Decision 066 post-closeout
correction `e3e58f93efb868263ce8cc501f506528fcbc6fae`, the accepted M3.3 entry software baseline
(Decision 066 R3).

## 2. M3.3-GV2 owner acceptance

```text
M3_3_GV2_PARSE_AND_IDENTITY_VERIFICATION_OWNER_ACCEPTED
```

The owner accepts the M3.3-GV2 read-only evidence verification and its factual findings. **M3.2
acceptance is not reinterpreted by this record**, and nothing here reopens a closed M3.2 fact.

### 2.1 Accepted factual findings

| # | Finding |
|---|---|
| GV2-1 | The accepted private M3.2 catalog was inspected **strictly read-only** |
| GV2-2 | The main database's durable SHA-256 was **unchanged before and after** |
| GV2-3 | The repository was unchanged |
| GV2-4 | **No network**, **no parser execution**, **no private mutation** |
| GV2-5 | The census **parse layer is EMPTY** |
| GV2-6 | `parser_state = 'not_started'` for **all 76 plan sources** |
| GV2-7 | **76 accepted stored objects** are present |
| GV2-8 | The existing parser functions are **pure over materialized content** |
| GV2-9 | The existing loader and persistence machinery is **offline-capable** |
| GV2-10 | **No offline entry point currently exists** |
| GV2-11 | The minimum offline seam is a **SMALL_EXTENSION** |
| GV2-12 | `source_observation_id` is a **uuid4** |
| GV2-13 | An offline **REPARSE of the same accepted observation deterministically reproduces** `parser_run_id` / `parsed_record_id` |
| GV2-14 | Only **RE-RETRIEVAL** creates a new uuid root |
| GV2-15 | M3.2 is closed and **reacquisition is prohibited** |
| GV2-16 | `evidence_sha256` has a Decision-016 field set but **no governed call shape** |
| GV2-17 | All **eight** candidate `*_resolution_sha256` derivations were previously **ungoverned** |
| GV2-18 | **Five** candidate resolution dimensions have **no equivalent census-layer resolution digest** |
| GV2-19 | Historical per-registrant documents were **never acquired** |
| GV2-20 | SIC-dependent fields **must fail closed** if accepted evidence cannot establish them |

**GV2-5 through GV2-7 are the findings that condition everything below.** The candidate mapping the
M3.3-GR proposal traced depends in the majority on a parse layer that exists in schema and is empty
in fact.

## 3. Corrections to the M3.3-GR proposal — GR-C1 and GR-C2

The M3.3-GR proposal is **historical proposal evidence**. It is not rewritten as though it had always
been authority. Two of its propositions were overstated, and are corrected here for every **current
operative surface**; the proposal's own body keeps its original text, annotated.

### 3.1 GR-C1 — retrieval/parse coupling

**Superseded proposition** (proposal §G.1, executive finding): *parsing is coupled to retrieval and
cannot run offline over stored objects.*

**Correct proposition, binding from this record:**

> Retrieval and parsing are coupled **only at the orchestration entry points**. Parsers operate on
> **already-materialized stored content**; payload loading, archive traversal, and `CensusCatalog`
> persistence are **already offline-capable**. The missing capability is an **offline entry point /
> driver**.

### 3.2 GR-C2 — what changes candidate evidence identity

**Superseded proposition** (proposal §B.3, §B.4 item 3, OQ-5): *an identical re-retrieval **or**
reparse changes candidate evidence identities.*

**Correct proposition, binding from this record:**

> - **REPARSE of the SAME accepted `census_source_observations` row is deterministic** — it
>   reproduces `parser_run_id` and `parsed_record_id` exactly (GV2-13).
> - **RE-RETRIEVAL creates a new uuid4 `source_observation_id`** and therefore *can* alter downstream
>   evidence identities (GV2-12, GV2-14).
>
> **M3.3 forbids reacquisition and re-retrieval**, so only the deterministic branch is reachable
> inside M3.3.

## 4. Ruling R13 — Offline Parse Prerequisite and Source Binding (OQ-1)

```text
M3_3_OQ_1_OFFLINE_PARSE_PREREQUISITE_OWNER_RULED
```

**Status: RESOLVED — OWNER RULED.**

**M3.3 requires a bounded OFFLINE METADATA PARSE before an authoritative real candidate snapshot may
be constructed.**

### 4.1 What the offline parse is

The offline parse:

- consumes **only** already-accepted M3.2 stored objects;
- binds each planned source to **`census_plan_sources.observation_id`**;
- treats that plan-row `observation_id` as the **authoritative source disambiguator**;
- specifically uses that binding for the **two bulk-submissions objects**;
- does **not** choose an object by `source_id`, timestamp, or recency;
- creates **no HTTP client**;
- creates **no transport**;
- performs **no network access**;
- performs **no SEC request**;
- performs **no reacquisition**;
- performs **no re-retrieval**;
- performs **no filing-body retrieval or parsing**;
- uses **no CompanyFacts**;
- uses **no Frames**;
- adds **no new source evidence**;
- **preserves a failed or unavailable accepted source as failed or unavailable**;
- **never fabricates** a missing object or observation.

### 4.2 What it may reuse

`SnapshotStore` local loading and verification; the existing **pure** parsers; archive iteration;
`CensusCatalog` persistence; and the existing deterministic resolution machinery where applicable.

### 4.3 What is permitted, and what is not

A **new bounded offline driver / entry point is permitted in the corrected M3.3 contract scope**.

**This ruling does not authorize implementing or executing it.** Implementation authorization remains
**NO**, pending independent contract review and subsequent owner acceptance. Real execution is
separately gated at **M3.3-E0** (§11).

**Cite as:** *M3.3 Owner Ruling R13 — Offline Parse Prerequisite and Source Binding.*

## 5. Ruling R14 — Structural Fingerprint Non-Vacuity (OQ-2)

```text
M3_3_OQ_2_STRUCTURAL_FINGERPRINT_OWNER_RULED
```

**Status: RESOLVED — OWNER RULED.**

**A uniformly empty `schema_fingerprint_sha256` across the real source corpus may NOT be used merely
because the accepted parse layer had never been run.** The governed offline parse (R13) **must
precede** authoritative real candidate snapshot construction.

After parsing:

1. a source whose accepted parser **legitimately emits zero structural rows** may use the accepted
   empty-row-set structural digest **for that source**;
2. a **failed or unavailable** source is **not** converted into a fabricated successfully-parsed
   empty structural set;
3. structural fingerprints must be **recomputable from the actual authorized offline parse result**;
4. candidate snapshot construction **refuses** if required structural evidence is unavailable at its
   accepted evidence floor.

Decision 021 §8.1's permission for the empty-row-set case is retained exactly and is **not** widened
into a licence to skip the parse.

**Cite as:** *M3.3 Owner Ruling R14 — Structural Fingerprint Non-Vacuity.*

## 6. Ruling R15 — Evidence Provenance Identity Retained (OQ-5)

```text
M3_3_OQ_5_EVIDENCE_IDENTITY_ALT_3_OWNER_RULED
```

**Status: RESOLVED — OWNER RULED. The owner chooses ALT-3: retain Decision 016 §4 exactly.**

`evidence_sha256` continues to bind all eight Decision 016 §4 fields:

1. `classification_dimension`
2. `evidence_role`
3. `source_observation_id`
4. `parsed_record_id`
5. `source_field`
6. `canonical_observed_value`
7. `policy_version`
8. `precedence`

**Do not remove `source_observation_id`. Do not remove `parsed_record_id`. Do not substitute a
surrogate identifier.**

### 6.1 Reason

GV2 proved the relevant M3.3 operation is **deterministic over the frozen accepted observation rows**.
For the **same** accepted source observation, an offline reparse reproduces `parser_run_id` and
`parsed_record_id` deterministically (GV2-13). Only reacquisition or re-retrieval creates a new
random `source_observation_id` (GV2-12, GV2-14), and **M3.3 reacquisition is prohibited**.

Therefore the accepted M3.2 `source_observation_id` values are **frozen provenance constants for
M3.3**.

### 6.2 The bounded limitation this ruling records

> Candidate evidence and family digests are **deterministic for the accepted frozen observation
> set**, but Decision-016 candidate evidence identity is **not cross-reacquisition invariant**.

That hypothetical cross-reacquisition asymmetry **grants no acquisition authority** and is **not
repaired in M3.3**. It is registered as limitation **D067-L1** in
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md).

**Cite as:** *M3.3 Owner Ruling R15 — Evidence Provenance Identity Retained.*

## 7. Ruling R16 — Candidate Evidence and Resolution Identity (OQ-7 / OR-1 expansion)

```text
M3_3_OQ_7_OR_1_EXPANSION_OWNER_RULED
```

**Status: RESOLVED — OWNER RULED.**

**OR-1 is expanded.** It now covers:

- **A.** the **eleven** snapshot-level digest/identity definitions from the M3.3-GR proposal; **plus**
- **B.** `evidence_sha256`; **plus**
- **C.** all **eight** candidate `*_resolution_sha256` derivations.

**Entity and accession tie-break hashes require no new methodology ruling** — `entity_tie_break_sha256`
(Decision 013 §6; Decision 016 §7) and `accession_tie_break_sha256` (Decision 018 §5.2) **retain
their already accepted definitions**.

### 7.1 `evidence_sha256`

Use the **accepted `release/hashing.py` `hash_table`**. **No second hashing implementation.**

**Governed row-content call shape:**

| Aspect | Value |
|---|---|
| table / domain | `pilot_candidate_evidence_row` |
| logical fields | `classification_dimension`, `evidence_role`, `source_observation_id`, `parsed_record_id`, `source_field`, `canonical_observed_value`, `policy_version`, `precedence` |

The field set is **exactly Decision 016 §4's list** (R15).

`canonical_observed_value` is hashed **in the governed canonical representation already produced for
persistence**. The hash layer introduces **no second substantive normalization**. Canonical `NULL`
remains canonical `NULL` where the accepted schema permits it.

**Excluded from `evidence_sha256`:**

`evidence_id`; `snapshot_id`; the parent candidate key; `recorded_at_utc`; `detail` / free text;
`census_run_id`; paths; physical SQLite bytes; approval and publication state.

**`evidence_sha256` is content identity, not row uniqueness.**

### 7.2 Candidate `*_resolution_sha256`

The candidate `*_resolution_sha256` fields use a **candidate-layer digest**. They **do not reuse** the
census accession `resolution_sha256`.

**Step 1 — contributing evidence digest:**

```text
contributing_evidence_sha256 = hash_table(
    domain/table  = "pilot_candidate_resolution_evidence",
    logical fields = ( evidence_role, precedence, evidence_sha256 ),
    rows          = EXACT candidate evidence rows substantively used to establish this resolution,
    deterministically ordered
)
```

**Step 2 — the resolution digest:**

```text
<dimension>_resolution_sha256 = hash_table(
    domain/table   = "pilot_candidate_resolution",
    logical fields = ( classification_dimension,
                       contributing_evidence_sha256,
                       evidence_policy_version,
                       resolved_value ),
    rows           = one canonical logical row
)
```

`resolved_value` is the **exact canonical persisted candidate classification value**. **No
census-layer resolution digest is substituted for this candidate digest.**

### 7.3 The eight columns this construction governs

| Parent | Columns |
|---|---|
| **Entity** (`pilot_candidate_entities`) | `size_resolution_sha256`, `industry_resolution_sha256`, `history_resolution_sha256`, `primary_universe_resolution_sha256` |
| **Accession** (`pilot_candidate_accessions`) | `filing_date_resolution_sha256`, `cohort_resolution_sha256`, `xbrl_resolution_sha256`, `amendment_purpose_resolution_sha256` |

### 7.4 Absence and failure semantics

If the resolved value is **legitimately absent** under accepted methodology, the resolution SHA is
`NULL` **only where migration, schema, and methodology permit**.

If a **required** resolved value cannot be established from accepted evidence: **FAIL CLOSED.**

**No best-effort resolution. No manual resolution. No network fallback. No new evidence.**

The **five dimensions lacking a census-layer resolution analogue (GV2-18) are not exempt.** They use
candidate evidence under accepted classification rules, or they fail closed.

**Cite as:** *M3.3 Owner Ruling R16 — Candidate Evidence and Resolution Identity.*

## 8. Previously frozen owner rulings, recorded here for the first time

The owner froze four further dispositions before this record. **They had no repository record until
now**; this section is where they become recorded repository authority.

| Question | Owner disposition |
|---|---|
| **OQ-3** — rebuild colliding on `snapshot_id` in the same catalog | **FAIL CLOSED.** Never `INSERT OR REPLACE`, never `INSERT OR IGNORE`, never a silent no-op that returns the existing snapshot as though newly built |
| **OQ-4** — parent-key convention | **`snapshot_id` is EXCLUDED from the seven candidate-family digests**, following Decision 021 §8.1 and Decision 019 §6.6.1, and is bound once in `candidate_snapshot_sha256` |
| **OQ-6** — `coverage_policy_version` | **`pilot-coverage/1.0`** |
| **OQ-8** — persisted evidence roles | **`winning` / `competing` / `supporting`** — migration `0009`'s vocabulary, which governs the persisted contract. Decision 016 §4's illustrative `primary` / `corroborating` / `conflicting` wording is **illustrative and historical**, and the divergence is recorded rather than left silent |

### 8.1 An implementation-packet consequence of OQ-6, recorded and not resolved here

`coverage_policy_version` is `NOT NULL` in migration `0009`, sits inside `coverage_window_sha256`, and
therefore inside `snapshot_id`. **The value `pilot-coverage/1.0` has no current home in the
repository**: there is no `pilot_policy.py` constant for it, and no `reference_policy_versions` seed
row for it — verified read-only against `src/disclosure_drift/pilot_policy.py` and migration `0009`.

Two facts follow, and **neither is resolved by this record**:

- adding a `reference_policy_versions` seed row would need a **migration**, which the M3.3 contract
  prohibits and which is one of its stop conditions;
- adding the constant to `src/disclosure_drift/pilot_policy.py` is **prohibited by M3.3 contract
  §20**.

**This is therefore an open path question for the M3.3-I/R implementation packet**, requiring its own
owner authorization at that gate. Until then the value is fixed as **methodology** by this record and
has **no authorized executable home**. A session that reaches it **stops and refers**; it does not
choose a home for the constant, and it does not widen §20 to make one.

## 9. OR-1 — final owner disposition

```text
M3_3_OR_1_CANDIDATE_SNAPSHOT_IDENTITY_OWNER_RULED
```

**Status: RESOLVED — OWNER RULED.**

The **M3.3-GR eleven-digest proposal is ACCEPTED as the normative OR-1 basis**, subject to **all**
owner corrections and rulings already issued:

| Applied correction | Effect |
|---|---|
| **OQ-3** | Duplicate `snapshot_id` ⇒ **fail closed** |
| **OQ-4** | `snapshot_id` **excluded** from the seven family digests |
| **OQ-5 / R15** | **ALT-3** — the Decision 016 §4 evidence identity fields are **retained** |
| **OQ-6** | `coverage_policy_version` = **`pilot-coverage/1.0`** |
| **OQ-7 / R16** | The §7 expansion — `evidence_sha256` and the eight resolution digests |
| **OQ-8** | Persisted evidence roles = `winning` / `competing` / `supporting` |

### 9.1 `input_observation_set_sha256`

**`input_observation_set_sha256` is DEFINITIONALLY IDENTICAL to Decision 021 §8.1's
`source_observation_set_sha256`.**

It is computed **twice**, and both computations must agree:

1. from the **exact cited in-memory observation set** *before* the candidate snapshot `INSERT`; and
2. **independently recomputed from the persisted candidate evidence** within the **same authoritative
   snapshot transaction**.

**Mismatch ⇒ FAIL CLOSED / ROLL BACK.**

### 9.2 Retained without change

- the accepted `hash_table` implementation — **no second hashing implementation**;
- Decision 016 §8's exclusions;
- **no physical SQLite bytes or SQLite version** in any identity;
- **no `census_run_id`** in snapshot identity;
- **no timestamp, path, approval, or publication state** in any identity;
- **no circular digest dependency** — the dependency graph stays acyclic.

## 10. OR-2 — final owner disposition

```text
M3_3_OR_2_SOURCE_TO_CANDIDATE_MAPPING_OWNER_RULED
```

**Status: RESOLVED — OWNER RULED.**

The **M3.3-GR 135-column source→candidate mapping is ACCEPTED as the normative OR-2 basis**, with the
mandatory GV2 corrections below.

### 10.1 Parse prerequisite

Columns whose source chain terminates in the census parse layer are **not permanently UNAVAILABLE**
merely because M3.2 never parsed them. **They become available only after the governed R13 offline
parse succeeds.**

This is the single largest correction to the proposal: its §F conclusion that 71 of 135 columns are
unreachable was correct **as at M3.2's accepted state**, and is **not** a permanent property.

### 10.2 Authoritative source observation

For **every** planned source, the offline parse binds to **`census_plan_sources.observation_id`**.

**Do not** choose among multiple observations using recency, largest object, path, `source_id` alone,
retrieval time, or operator discretion. **This specifically resolves the two bulk-submissions
objects.**

### 10.3 Failed / unavailable sources

A source accepted as **failed or unavailable remains failed or unavailable**. No replacement, no
reacquisition, no alternate URL, no source substitution, no fabricated parse result.

Any candidate field that **actually requires** unavailable source content **FAILS CLOSED at the
applicable accepted evidence floor**.

### 10.4 Historical documents

Per-registrant historical documents were **never acquired** (GV2-19). **Offline parsing may not
retrieve them.** Any candidate derivation that genuinely requires those documents, and cannot be
established from another already-accepted authorized source, **FAILS CLOSED**.

**Decision 023 O1 remains unchanged.**

### 10.5 SIC

If the accepted source corpus cannot establish the required SIC authority **after** offline parsing,
**SIC-dependent candidate classifications fail closed**. **No alternate external SIC source.**

This applies in particular to any quota or eligibility field whose accepted derivation requires SIC,
including **`industry_family`** and **`primary_universe_eligible`**.

### 10.6 `census_index_instances`

`census_index_instances` remains **AVAILABLE-AS-NONE / DELIBERATELY NOT USED**. Its emptiness:

- does **not** authorize acquisition;
- does **not** block by itself;
- may **not** be artificially populated.

### 10.7 Candidate resolutions

Candidate `*_resolution_sha256` fields use **R16's candidate-evidence digest** (§7.2). **Do not map a
census resolution digest directly into a candidate resolution column merely because the names are
similar.**

### 10.8 The NULL / fail-closed rule

**There is no blanket nullable fallback.** A candidate field may be `NULL` **only** where the existing
accepted **schema**, **applicability rule**, **and** substantive **methodology** all permit that
absence.

If a field is necessary to establish **hard eligibility**, a **hard quota**, a **required
classification**, **required provenance**, a **required manifest fact**, or another accepted hard
constraint — and accepted evidence cannot establish it — then:

> **REFUSE THE AUTHORITATIVE SNAPSHOT.**

**No best effort. No discretionary imputation. No manual fill. No methodology adjustment.**

## 11. M3.3-E0 — the real offline metadata parse execution boundary

**This record permits the corrected contract to contain the offline parse capability. It does not
authorize real execution.**

### 11.1 The gate

```text
M3.3-E0 — REAL OFFLINE METADATA PARSE
```

- **M3.3-I/R may later**, and **only after contract owner acceptance**, implement the offline parser
  and rehearse it on **fixtures or disposable isolated copies**.
- **M3.3-I/R may not mutate the accepted real private catalog.**
- The **real** private offline parse is a **separate owner gate**, occurring only after a fresh
  independent M3.3 rehearsal acceptance.
- **E0 requires separate Sol/GPT authorization.**
- **E0 must complete and be independently, read-only verified before M3.3-E1** — real candidate
  snapshot construction and selection execution.
- **There is no automatic E0 → E1 progression.**

### 11.2 What the corrected contract must define, at minimum

1. the exact **E0 input set**;
2. the exact **permitted target tables**;
3. the **source-observation binding**;
4. **interruption / partial-state behaviour**;
5. **deterministic rerun / recovery behaviour**;
6. a **completeness proof**;
7. a **non-acquisition proof**;
8. the **network-construction prohibition**;
9. **pre/post catalog integrity**;
10. **parser provenance**;
11. a **result token**;
12. **STOP conditions**;
13. the **owner gate between E0 and E1**.

**Unsafe automatic recovery semantics must not be chosen for convenience. A partial or interrupted
real E0 must never silently authorize E1.**

## 12. What this record does not authorize

It does **not**: authorize implementation; accept the M3.3 contract; enable network access; authorize
an SEC request; authorize reacquisition or re-retrieval; authorize executing the offline parse
against real private evidence; authorize mutating the accepted private catalog; authorize freezing a
real candidate snapshot; authorize a real selection; authorize constructing a real manifest or root;
approve a root; publish anything; authorize a migration; authorize editing an accepted S4, S5, or S6
module; authorize moving, retargeting, deleting, or recreating `m3.2-complete`; reopen Milestone 3.2;
close any limitation; or begin M3.4.

**Milestone 3.2 remains historically closed**, `m3.2-complete` **never moves**, and **no reacquisition
authority exists or is created**.

## 13. Deferred inputs that stay deferred

**OR-6**, **OR-7**, **OR-9**, and **OR-11** remain deferred to their named owner gates, exactly as
M3.3 contract §1.2 states. This record supplies none of them, and reaching one remains a
stop-and-refer condition.

## 14. Governance surfaces this record touches

| Surface | Effect |
|---|---|
| [`Milestones/contracts/m3_3.md`](../../Milestones/contracts/m3_3.md) | Corrected to carry R13–R16, GR-C1/GR-C2, the resolved OR-1/OR-2, the offline parse driver in future I/R scope, and the M3.3-E0 boundary. **Still not accepted** |
| [`Docs/m3/m3_3_snapshot_authority_adjudication_proposal.md`](../m3/m3_3_snapshot_authority_adjudication_proposal.md) | Annotated with its owner disposition. **Remains historical proposal evidence**; its body is not rewritten as authority |
| [`Docs/m3/m3_3_governance_foundation_inventory.md`](../m3/m3_3_governance_foundation_inventory.md) | §G dispositions updated. Still a navigation index |
| [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) | **D067-L1** added (§6.2). **No limitation is closed** |
| [`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md) | §29 gains the E0 prerequisite and the E0/E1 separation |
| `Milestones/STATUS.md`, `Milestones/milestone_03_master_plan.md`, `Milestones/contracts/README.md`, `Docs/Decisions/decision_registry.md`, `Docs/decision_index.md`, `Docs/architecture_map.md`, `Docs/change_impact_map.md` | Current-state synchronization only |

**No executable source, test, migration, configuration, or CI file is changed by this record, and no
private evidence is read or mutated.**

## 15. Next authorized action

**A fresh independent M3.3 contract review**, by a session that authored neither this record nor the
corrected contract. That session must `/clear` first, independently reread authority, perform **both**
a residue scan and a semantic current-state review, inspect the offline-parse boundary, inspect every
OR-1 and OR-2 preimage, inspect fail-closed source handling, inspect the E0/E1 separation, and verify
that **no implementation or network authority leaked**.

**No M3.3-I/R until that review passes and Sol/GPT explicitly accepts the corrected contract.**

```text
M3_3_DECISION_067_RECORDED_CONTRACT_READY_FOR_FRESH_INDEPENDENT_REVIEW
```
