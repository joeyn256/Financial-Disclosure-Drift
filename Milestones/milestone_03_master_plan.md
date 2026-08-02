# Milestone 3 — Master Plan and Operational Readiness Roadmap

**Status:** `DECISION_028_ACCEPTED_M3_1_CONTRACT_DRAFT_PENDING_INDEPENDENT_REVIEW`
**Implementation authorization:** `NO` — for every phase, without exception
**Controlling records:** [Decision 027](../Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome
`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`), as narrowly corrected by accepted
[Decision 028](../Docs/Decisions/decision_028_m3_1_readiness_corrections.md).
**Next authorized action:** `INDEPENDENT_M3_1_CONTRACT_REVIEW`

**This document is a governance roadmap, not an authorization.** It plans five phases. It starts
none of them. The M3.1 contract exists only as an unaccepted draft; no Milestone 3 implementation exists, no SEC network
access has occurred, no real snapshot or manifest exists, no root has been approved, and nothing has
been published.

---

## 1. Purpose

To state, for each Milestone 3 phase, exactly what it does, what it must not do, what it consumes,
what it produces, whether it may touch the network, what stops it, how it is validated, how it
recovers, what evidence it must leave behind, what token completes it, and what may be committed and
tagged — so that a later bounded contract can be written against a plan rather than against an
inference.

Milestone 3 is the first part of this project whose actions cannot be undone. A request sent is sent;
a rate limit tripped is tripped; an approved root is approved. Everything in this plan follows from
that asymmetry.

## 2. Inherited authority

Milestone 3 inherits every applicable accepted control from Milestones 0, 1, and 2, unchanged
([Decision 024](../Docs/Decisions/decision_024_m2_m3_boundary_governance.md) §6):

- **Frozen research definitions** — cohort windows, maturity gates, outcome cutoffs, and bootstrap
  seed `20260725`. `src/disclosure_drift/cohorts.py` remains canonical (CLAUDE.md rule 3).
- **Temporal authority** — the official SEC filing date is authoritative for cohort assignment
  ([Decision 010](../Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md));
  the acceptance date remains audit-only where governed.
- **Identifier rules** — plain accession is database and foreign-key identity; canonical dashed
  accession is used for deterministic hashing and presentation
  ([Decision 018](../Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md) §5); loaders
  verify plain-to-dashed consistency and fail closed on disagreement.
- **SEC access controls** — required SEC user agent; deterministic bounded aggregate rate limiting;
  governed response policy and retry classification; raw-store and provenance rules; fail-closed
  schema-drift detection.
- **Data-source prohibitions** — CompanyFacts disabled; the Frames API prohibited; external corpora
  validation-only.
- **Leakage controls** — the whole of [`Docs/leakage_register.md`](../Docs/leakage_register.md)
  (L01–L19), including L01, L04, L10, and L18, plus L15, L19, and the
  [Decision 015](../Docs/Decisions/decision_015_pilot_use_prohibition.md) pilot-use prohibition.
- **Accepted S4 isolation** — the entity-only draft stays `running`, non-publishable, and is never
  mutated, deleted, promoted, or used as a manifest input.
- **Accepted S5** — identity, selection, roles, evidence, contributions, quota rules, reserves,
  dispositions, persistence, reconstruction, and replay.
- **Accepted S6** — every manifest identity and preimage, the lifecycle and its eight
  migration-`0013` guards, verification, and file/database atomicity.
- **The decision record** — Decisions 013, 015, 016, 017, 018, 019, 020, 021, 022, 023, 024, 025,
  026, and 027, plus Decision 028 once independently reviewed and owner-accepted.
- **All accepted limitations** — carried in
  [`Docs/m3/limitations_register.md`](../Docs/m3/limitations_register.md) and never closed by a
  phase passing.

## 3. Closeout baseline

Verified live, not assumed. Recorded in full in
[Decision 027](../Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md) §2.

| | |
|---|---|
| Branch | `main` |
| Closeout commit | `034bbc1fa62c353602291f7f863092eb595f3c51` — `Close Milestones 0 1 and 2` |
| Completion tags at it | `m0-complete`, `m1-complete`, `m2-complete` (all annotated) |
| Migration chain | contiguous `0001`–`0013`; nothing beyond `0013` |
| Migration `0013` normative region | 10939 bytes, 186 lines, `7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595` |
| Implementation authorization | `NO` |

**Every phase re-verifies this live** with `make context` before relying on it. A recorded hash is a
historical reference, never live state.

## 4. Definitions

Terms are defined once here and used with exactly these meanings throughout.

| Term | Definition |
|---|---|
| **Logical request** | One distinct approved retrieval identity — the `request_identity(source_id, normalized_url, parameters)` triple. Two retrievals share a logical request only when all three agree. |
| **Physical attempt** | One HTTP request actually placed on the wire. A redirect hop, a retry, and the single controlled post-cooldown request are each separate physical attempts. |
| **Request plan** | The complete, ordered, deterministic set of logical requests a command intends to issue, derived from explicit inputs and never from the clock. |
| **Request-plan hash** | The SHA-256 over the canonical serialization of the request plan. Two dry runs with identical inputs must produce identical plan hashes. |
| **Request budget** | The owner-approved statement of planned logical requests, maximum physical attempts, maximum new raw objects, expected response classes, and the rate-limiter spacing floor, per route and in total. |
| **Hard request ceiling** | An owner-approved integer above which no physical attempt may be placed. A complete run may finish exactly at it; equality with work remaining yields `stopped_at_ceiling`. It is never raised during a running window. |
| **Governed identity** | Any of: candidate identity, `selection_run_id`, `selection_input_sha256`, `selection_result_sha256`, the eight S6 component digests, `root_manifest_sha256`, `manifest_id`. |
| **Operational state** | Timestamps, counts, durations, paths, receipt identifiers, machine and operator identity, and log locations. Operational state never enters a governed identity. |
| **Execution receipt** | One machine-readable, non-secret record of one governed M3 command's operational facts, specified by [`Docs/m3/execution_receipt_spec.md`](../Docs/m3/execution_receipt_spec.md). |
| **Governed non-success response** | A non-2xx response the accepted response policy classifies (`retry`, `retry_after`, `cooldown`, `fail`, `quarantine`) rather than one that is silently absorbed. There is no unclassified response. |
| **Fail closed** | Stop, preserve evidence, record a registered reason code, and report. Never relax a threshold, drop a failing row, substitute a default, or work around the gate. |
| **Exact root** | The specific byte value of `root_manifest_sha256` presented for approval. Approval attaches to that value alone. |

## 5. Global prohibitions

These hold in **every** Milestone 3 phase, and no phase contract may weaken one.

1. **No filing body, primary document, accession index, complete submission, SGML header, exhibit,
   Inline XBRL document, standalone XBRL instance, or taxonomy is ever retrieved.**
2. **CompanyFacts is disabled. The Frames API is prohibited.**
3. **External corpora are validation-only** and are never the point-in-time source of truth (L18).
4. **No outcome value, operating-margin input, or outcome linkage is read, derived, or stored.**
5. **No filing text is retrieved, parsed, or featurized.** No section extraction, no Item 1A or
   Item 7 parsing, no textual feature construction, no DDI construction, no rewrites, no model
   training or evaluation.
6. **Raw data is append-only** (CLAUDE.md rule 6). A differing remote response becomes a new
   observation and never overwrites an earlier raw object. Nothing is deleted.
7. **No frozen research definition changes** — cohort windows, maturity gates, the primary outcome,
   hypotheses, thresholds, and seed `20260725` (CLAUDE.md rule 3).
8. **No pilot membership or stratification informs any research artifact** (Decision 015; L15, L19).
9. **The S4 entity-only draft is never mutated, deleted, promoted, or used as a manifest input.**
10. **No second selector, no reserve substitution, and no discretionary trimming** to obtain
    feasibility or compatibility.
11. **No operational state enters a governed identity** (§4; Decision 027 §18).
12. **No secret, full SEC identity, absolute personal path, raw response body, or restricted
    substantive payload is printed, logged, or persisted** in a receipt, evidence packet, log, or
    commit.
13. **Approval is never implied** — not by construction, not by a passing gate, not by silence, and
    not by code having run.
14. **Nothing is published.** Milestone 3 acceptance creates no publication authority.
15. **On any failed data-quality, leakage, reconciliation, budget, or drift gate, stop and report**
    (CLAUDE.md rule 12).

## 6. Sequencing rules

1. **Sequential execution only.** One phase at a time, one session at a time. No concurrent Claude
   sessions, no parallel worktrees, no overlapping implementation phases.
2. **Governance before implementation.** A phase begins only with all five Decision 024 §8 entry
   conditions satisfied: an accepted governing record where required, a bounded contract, explicit
   owner authorization, exact path authorization, and its inherited prerequisite gates.
3. **A phase may not begin until its predecessor's completion token is recorded and its independent
   review, where required, has passed.**
4. **A gate never passes retroactively.** Evidence is produced by the run it describes.
5. **Fail closed.** Unmet prerequisites, missing authority, schema drift, request-budget overflow,
   an unexpected response class, missing provenance, identity disagreement, or recovery uncertainty
   stops the phase.

## 7. Phase map

| Phase | Former stage | Scope | Network | Token | Future tag |
|---|---|---|---|---|---|
| **M3.1A** | part of S7 | Offline **acquisition-path and operator** rehearsal | **NONE** | `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED` | none |
| **M3.1B** | part of S7 | Gate F and zero-request controlled-live readiness | **ZERO LIVE REQUESTS** | `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION` | `m3.1-complete` |
| **M3.2A** | part of S8 | Bootstrap acquisition window — sources whose complete logical-request set is derivable before access | **CONTROLLED, EXPLICITLY AUTHORIZED** | — (internal) | none |
| **M3.2B** | part of S8 | Dependent acquisition window — the historical/entity requests derived from the frozen M3.2A objects; then Gate H over both | **CONTROLLED, EXPLICITLY AUTHORIZED** | `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED` | `m3.2-complete` |
| **M3.3A** | part of S9 | Candidate-snapshot **builder** plus the offline execution rehearsal | **OFF** | — (internal) | none |
| **M3.3B** | part of S9 | Real snapshot freeze, deterministic real execution, exact real manifest | **OFF** | `M3_3_REAL_PILOT_MANIFEST_CONSTRUCTED_READY_FOR_ROOT_APPROVAL` | `m3.3-complete` |
| **M3.4A** | part of S10 | Approval-recording entry point, validated against synthetic catalogs | **NONE** | — (internal) | none |
| **M3.4B** | part of S10 | Exact root-hash owner approval and the single governed write | **NONE** | `M3_4_EXACT_ROOT_OWNER_APPROVED_READY_FOR_INTEGRATED_ACCEPTANCE` | `m3.4-complete` |
| **M3.5** | new | Integrated real-pilot acceptance and the Milestone 3 checkpoint | **NONE** (see M3.5 field 11) | `M3_5_REAL_PILOT_ACCEPTED_MILESTONE_3_COMPLETE` | `m3-complete` |

**Every `A`/`B` pair above is two sequential internal parts of one phase. They create no new milestone
and no new phase, and the Decision 024 §5.1 map M3.1–M3.5 is unchanged** (Decision 027 §6). **Only a
phase takes a tag; an internal part never does.**

**The rule that produced these subdivisions, and that governs any future one:** the second part
depends on something the first part must build, freeze, or prove, and **no scenario may be placed in
a phase that lacks the production path it exercises.**

## 8. Decision and contract policy

**A phase needs a new accepted decision record when** it fixes methodology, an identity, a preimage,
a schema object, a policy constant, an approval semantic, or a value that later work must not
re-derive differently. It does **not** need one to implement something an accepted record already
fixes.

**Every phase needs its own bounded contract** under `Milestones/contracts/`, written to the shape
[`contracts/README.md`](contracts/README.md) requires and to the additional mandatory contents in
§16 below. **This plan creates no contract.**

Anticipated owner decisions, as proposals requiring separate acceptance:

| When | Decision |
|---|---|
| Before M3.1 implementation | Bounded M3.1 contract; acceptance of the rehearsal scenario matrix as the required coverage set |
| At Gate F, before M3.2 | **Approval of the exact request budget and the exact hard ceiling**; authorization to enable the network for one named command |
| Before M3.3 | Authorization to freeze a real candidate snapshot; a governance record for the candidate-snapshot builder if its construction fixes any identity not already frozen |
| At M3.4 | **Explicit approval of the exact `root_manifest_sha256`** |
| At M3.5 | Acceptance of the integrated result; separately, any publication or outcome-analysis authority |
| Any time | A ruling on Decision 023 **O1** if a lawful run reaches an empty sole-carrier crosswalk family |

## 9. Validation policy

| When | What runs |
|---|---|
| **During implementation** | Targeted tests and touched-file checks only — `make fast`, plus `make test PYTEST_ARGS="<paths>"` with paths chosen from [`Docs/change_impact_map.md`](../Docs/change_impact_map.md). Not an acceptance gate. |
| **At the end of every phase** | One full suite and every required repository gate, in this fixed order: `ruff check .`; `ruff format --check .`; `mypy src`; `pytest`; `make sqlite-check`; `make secrets`; `make hygiene`; `make context`. Plus the phase's own evidence packet and, where the phase touched schema, `tests/unit/test_migration_provenance.py` and the migration-integrity checks. |
| **At consequential phase boundaries** | One focused independent Opus review, scoped to that phase's acceptance question. |
| **At M3.5** | The final integrated Milestone 3 acceptance review. |

**When Milestone 3 introduces schema, [`Docs/sec_data_dictionary.md`](../Docs/sec_data_dictionary.md)
is extended in the same pass** — the standing lesson Decision 025 recorded.

## 10. Commit and tag policy

**Commit.**

- **One implementation commit per accepted phase, by default.**
- An **intermediate implementation checkpoint** is allowed only where that phase's own plan
  explicitly justifies it *and* the owner separately authorizes it.
- **Governance-only records may take a separate bounded governance commit.**
- **No noisy sequence of mechanical checkpoint commits.**
- Nothing is staged with `git add .`, `git add -A`, or `git add --all`; exact paths only.
- Nothing is committed or pushed without an explicit instruction (CLAUDE.md rule 13).

**Tag.**

- **Annotated tags only**, created only after independent phase acceptance.
- **No tag for an unreviewed implementation state**, and **no tag for M3.1A**.
- **Frozen future tag names**, confirmed against every existing tag as non-conflicting:

| Tag | Created after | Message |
|---|---|---|
| `m3.1-complete` | M3.1 acceptance | `Complete Milestone 3.1 Gate F and controlled-live readiness` |
| `m3.2-complete` | M3.2 acceptance | `Complete Milestone 3.2 controlled metadata acquisition` |
| `m3.3-complete` | M3.3 acceptance | `Complete Milestone 3.3 real pilot snapshot and manifest` |
| `m3.4-complete` | M3.4 acceptance | `Complete Milestone 3.4 exact root approval` |
| `m3-complete` | M3.5 acceptance | `Complete Milestone 3 real pilot execution` |

Existing tags — `m0-complete`, `m1-complete`, `m2-complete`, `m2.2-r3-complete`,
`m2.3-s3.2-complete`, `m2.3-s4-complete`, `m2.3-s5-complete`, `m2.3-s5.4-complete`,
`m2.3-s6-complete` — are **immutable**. The Milestone 3 tags supplement them and move, replace, or
re-point none of them.

## 11. Rollback philosophy

**Rollback never means deleting evidence** (milestone plan §12). On failure, in order:

1. stop issuing new requests;
2. mark the job failed with a registered reason code;
3. preserve every retrieval attempt;
4. preserve every committed immutable raw object;
5. quarantine partial or unverifiable objects — preserved, never replaced or deleted;
6. roll back uncommitted SQLite transactions;
7. reconstruct JSONL projections from the authoritative SQLite catalog;
8. rerun integrity and foreign-key checks;
9. require an **explicit** resume or new-run decision — never an automatic one;
10. write the terminating execution receipt, including the interruption state and reason code.

Git-level rollback is a separate matter: an unaccepted phase commit is reverted or reset only under
explicit owner instruction, and a pushed commit is corrected by a forward commit, never by a
history rewrite.

## 12. Evidence-storage and retention policy — the two-layer model

**The repository is public. Completed operational evidence is not committed to it.** Git history is
permanent: a completed root-approval packet pushed to a public remote publishes an unpublished
`root_manifest_sha256` irreversibly, while publication authority is `NOT_AUTHORIZED`. The two layers
exist to make that impossible rather than merely discouraged.

### 12.1 Tracked publicly

- **blank templates** under [`Docs/m3/templates/`](../Docs/m3/templates/request_budget.md);
- planning and governance records;
- the [limitations register](../Docs/m3/limitations_register.md);
- non-sensitive status and navigation;
- the **evidence index**
  ([`Docs/m3/templates/evidence_index.md`](../Docs/m3/templates/evidence_index.md)) — artifact type,
  phase, status, the completed artifact's own **SHA-256**, and a **non-sensitive reference
  identifier**.

### 12.2 Held privately, outside the repository

In an **owner-controlled private evidence root**, git-ignored and never tracked:

execution receipts; request budgets; Gate F and Gate H packets; interrupted-run records;
schema-drift records; real-snapshot evidence packets; root-approval packets; raw objects; catalogs;
candidate, selection, reserve, and manifest artifacts; and **every unpublished governed identity**.

### 12.3 The digest workflow

The operator computes a completed artifact's digest with:

```bash
shasum -a 256 <private-evidence-file>
```

and enters **only that digest and non-sensitive metadata** into the public evidence index. **No
absolute private path is ever recorded publicly.**

**A public acceptance decision may reference the SHA-256 of a private evidence artifact. It may not
expose an unpublished root or any substantive row.**

### 12.4 Retention

1. **Every phase produces its evidence packet from the template frozen for it**, and stores the
   completed copy privately.
2. **Evidence is retained for the life of the project** and is never edited after the phase is
   accepted; a correction is a new dated entry, not an overwrite.
3. **Execution receipts are retained indefinitely** and are the operational record of what ran.
4. **Raw objects and their provenance are append-only and are never deleted** (CLAUDE.md rule 6).
5. **Completed private evidence requires a separate owner-controlled backup.** A private root with
   no backup is a single point of loss for the only record of a run that cannot be re-run.
6. **Even privately, evidence never contains a secret, a full SEC identity, an absolute personal
   path, a raw response body, filing text, or an outcome value.** Privacy is defence in depth, not a
   licence to record prohibited content.
7. **Nothing under `data/` is committed** except `data/README.md`; `scripts/check_repo_hygiene.py`
   enforces this.

**`.gitignore` is not edited by the planning sessions.** Creating the private root's ignore entry is
a configuration change requiring its own authorization, and is carried as an open follow-up in the
limitations register (**M3-L11**).

## 13. Model assignment

| Model | Effort | Work |
|---|---|---|
| **Claude Opus** | **Max** | Architecture, phase contracts, owner decisions, consequential methodology, focused independent reviews, exact-root approval preparation, final integrated acceptance |
| **Claude Sonnet** | **High or Max** | Bounded implementation, tests, CLI work, separately authorized migrations, operator tooling, narrow corrections |
| **Haiku** | — | **Nowhere on the Milestone 3 critical path** |

**Sequential only.** One session at a time; no parallel worktrees; no overlapping phases.

## 14. Limitations management

[`Docs/m3/limitations_register.md`](../Docs/m3/limitations_register.md) is the register. Every phase:

1. **reads it before starting**, to know which conditions are live;
2. **records any new limitation it discovers**, with the full field set;
3. **never closes an inherited limitation** — closure requires the evidence the register names and,
   where the register says so, an owner ruling;
4. **refers rather than resolves** any future owner-ruling condition, of which Decision 023 **O1**
   is the live example.

---

# Phase M3.1 — Acquisition-path rehearsal and Gate F

Planned in two sequential internal parts: **M3.1A** offline acquisition-path and operator rehearsal,
then **M3.1B** Gate F and zero-request readiness. Where a field differs between them, both are
stated.

### 1. Objective

Prove, with no live request, that the **acquisition path and the operator workflow** work end to end,
and that the project is ready to place its first SEC request — then obtain the owner's approval of
the exact request budget and hard ceiling that will bind the first acquisition window.

### 2. Exact scope

**M3.1A.** Implement and run the **acquisition rehearsal** specified in
[`Docs/m3/offline_rehearsal_spec.md`](../Docs/m3/offline_rehearsal_spec.md) §5 — all twelve
acquisition scenarios A1–A12, using scripted responses and synthetic fixtures only, opening no
socket, with deterministic clock inputs wherever an operational timestamp is required. Produce the
rehearsal evidence, including the proof that receipt content enters no governed identity.

**M3.1A rehearses only acquisition and operator operations:** request planning and ordering;
request-budget enforcement; rate limiting; retries, redirects, `Retry-After`, cooldowns, block pages,
and terminal responses; route allowlist and denylist enforcement; raw storage and provenance;
duplicate and changed-body handling; parser and schema-drift behaviour; catalog transactionality;
interruption and recovery; execution receipts and prohibited-field scanning.

**M3.1 must not rehearse or implement candidate-snapshot construction, snapshot freeze, S5 selection,
reserves, dispositions, selection-result sealing, S6 manifest construction, or root computation.**
Those production paths do not exist at M3.1 — no candidate-snapshot builder exists anywhere in the
repository — and they are rehearsed at **M3.3A**, which builds them. **No scenario may be placed in a
phase that lacks the production path it exercises** (Decision 027 §6.1).

**M3.1B.** Verify the `[sec]` extra is installed; validate the SEC identity locally without printing
it; confirm network is disabled by default; define and assert the exact route allowlist and denylist;
implement the zero-request request-plan command; implement the Decision 028 planner-v2 correction
that resolves the `CURRENT_PLANNER_DISCREPANCY` (§15.1), with Decision 013 unchanged; produce a
deterministic request plan for the **M3.2A window** and its plan hash; run the dry run twice and
compare plan hashes; construct the proposed request budget and the hard ceiling from the **derived**
maximum-attempt bound (§16); record policy versions and the maximum-new-raw-object bound; obtain
operator acknowledgement; obtain **owner approval of the exact M3.2A budget and ceiling**; produce
the Gate F evidence packet.

**M3.1B approves the M3.2A window only.** The M3.2B budget and ceiling do not exist yet — they are
derived after M3.2A freezes its objects, and approved separately (§6.2 of Decision 027).

**The four acts M3.1B keeps separate, and never conflates:**

| Act | What it is | What it is not |
|---|---|---|
| **Validating identity locally** | Reading and format-checking `DISCLOSURE_DRIFT_SEC_USER_AGENT` at the boundary | Not contacting anything; not printing the value |
| **Constructing a request plan** | Deriving the ordered logical-request set and its hash from explicit inputs | Not building a transport; not resolving DNS |
| **Enabling transport** | Setting `network.enabled: true` and constructing the HTTP client | Not sending anything |
| **Sending the first request** | An M3.2 act, under an M3.2 contract, with an approved budget | Never an M3.1 act |

### 3. Explicit non-scope

No live request of any kind. No metadata acquisition. **No candidate-snapshot builder, in
implementation or in rehearsal. No snapshot freeze. No S5 selection. No reserves or dispositions. No
selection-result sealing. No S6 manifest construction. No root computation.** No real candidate
snapshot. No manifest. No approval. No publication. No change to any accepted S4, S5, or S6 module,
migration, identity, preimage, or methodology. No new selector. No schema change unless a separately
accepted decision authorizes one and the contract names it. **No M3.2B budget or ceiling** — that
window's plan does not exist until M3.2A freezes its objects.

### 4. Controlling decisions

[Decision 024](../Docs/Decisions/decision_024_m2_m3_boundary_governance.md) §§5.1, 5.2 (the S7 row),
6, 8; [Decision 026](../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md) §§19–21;
[Decision 027](../Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md);
[Decision 028](../Docs/Decisions/decision_028_m3_1_readiness_corrections.md), accepted;
[Decision 021](../Docs/Decisions/decision_021_m23_s6_manifest_construction.md) §17 (the S7 scope
definition Decision 024 renamed); [Decision 007](../Docs/Decisions/decision_007_sec_universe.md)
(approved sources); [Decision 009](../Docs/Decisions/decision_009_raw_data_governance.md) (raw-data
governance); [Decision 013](../Docs/Decisions/decision_013_pilot_selection_mechanics.md) §1 (the
as-of cutoff); [`milestone_2_3_pilot_selection_plan.md`](milestone_2_3_pilot_selection_plan.md) §11
Gate F, §12 (rate limiting, retry, quarantine, rollback, audit).

### 5. Required owner decisions

1. **The bounded M3.1 contract**, with its exact authorized paths.
2. **Acceptance of Decision 028's corrected acquisition-rehearsal scenario matrix** (A1–A12) as the
   required coverage set.
3. **Acceptance of Decision 028's M3-L12 ruling** — correct the planner to agree with Decision 013
   §1 under policy `quarterly-index-instances/2.0`; do not change Decision 013. Gate F cannot pass
   until that implementation and its tests are accepted.
4. **Approval of the exact M3.2A request budget and the exact hard request ceiling** — a Gate F exit
   condition, and the single most consequential decision in the phase.
5. **Authorization to proceed to M3.2A** — separate from 4, and not implied by it.

### 6. Prerequisites

- Decision 027 accepted at v0.2; Decision 028 accepted; the corrected
  `INDEPENDENT_M3_MASTER_PLAN_REREVIEW` passed.
- A bounded M3.1 contract exists, accepted, with exact paths.
- Explicit owner authorization to begin M3.1.
- Live baseline re-verified with `make context`: branch `main`, `HEAD == origin/main`, clean tree,
  migration chain contiguous through `0013`.
- The full suite green at the phase-entry baseline.
- `Docs/m3/` documentation pack present and unmodified since acceptance.
- **M3.1B additionally requires** `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED` recorded.

### 7. Exact inputs

- The accepted source registry `SOURCES` and its nine registrations, and the structured URL family
  policies that bound each one.
- The accepted response policy constants: `MAX_TRANSIENT_RETRIES = 5`,
  `RETRY_BACKOFF_CEILING_SECONDS = 60.0`, `COOLDOWN_SECONDS = 600.0`, `RETRYABLE_STATUSES`,
  the block-page signatures.
- The accepted rate-limit constants: `DEFAULT_REQUESTS_PER_SECOND = 4.0`,
  `MAX_REQUESTS_PER_SECOND = 8.0`, `DEFAULT_BURST = 1`.
- `MAX_REDIRECT_DEPTH = 5` and `REDIRECT_STATUSES`.
- The Decision 013 §1 as-of inputs: `coverage_start = 2009-01-01`, `coverage_end = 2026-06-30`,
  `as_of_date = 2026-06-30`, `include_open_quarter = false`.
- The explicit `--calendar-year` input for the annual EDGAR calendar instance.
- The calendar-evidence manifest (`edgar-calendar-evidence/1.0`).
- The frozen policy versions: `M22_SOURCE_REGISTRY_VERSION`, `PILOT_QUOTA_POLICY_VERSION`,
  `PILOT_JOINT_SELECTOR_POLICY_VERSION`, `PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION`,
  `PILOT_MANIFEST_HASH_POLICY_VERSION`, `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION`, and the parser
  versions.
- `INDEX_PLAN_POLICY_VERSION = "quarterly-index-instances/2.0"` and the request-plan schema version
  named by the M3.1 contract.
- Synthetic fixtures and scripted responses for M3.1A. **No live data, and no real SEC response.**

### 8. Exact outputs

**M3.1A.** A passing acquisition rehearsal across all twelve scenarios A1–A12; per-scenario recorded
reason codes, persisted state, files, receipts, rollback, recovery, and validation; the
identity-noncontamination proof; the **derived and independently tested per-route maximum reachable
physical-attempt bound** (§16); the rehearsal evidence record; the token
`M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED`.

**M3.1B.** A deterministic **M3.2A** request plan; its request-plan hash; two dry-run outputs with
identical plan hashes; proof that the M3-L12 planner correction agrees with Decision 013 §1; the completed
[`Docs/m3/templates/request_budget.md`](../Docs/m3/templates/request_budget.md) for the M3.2A window;
the owner-approved hard ceiling; the recorded policy versions; the maximum-new-raw-object bound; the
expected request-class totals where derivable; the completed
[`Docs/m3/templates/gate_f_checklist.md`](../Docs/m3/templates/gate_f_checklist.md); one execution
receipt per dry run; the token `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION`.

**Every completed artifact above is private evidence** (§12); the repository records only its type,
phase, status, SHA-256, and reference identifier in the public evidence index.

### 9. Authorized future path categories

Stated as **categories**; a contract names exact paths.

- A new offline rehearsal harness module and its tests.
- A new zero-request request-planning module and its tests, plus the CLI wiring for a dry-run-only
  subcommand.
- A new execution-receipt construction and serialization module and its tests.
- Bounded corrections to the inherited quarterly planner, terminal second-cooldown fallback, and
  central reason-code registry, with their nearest unit tests, exactly as Decision 028 authorizes.
- A bounded cumulative physical-attempt ceiling gate on the acquisition/retrieval surface, taking an
  explicit ceiling argument and refusing the attempt that would exceed it, with its unit tests. This
  is the production path scenario A5 exercises and the seam the rehearsal's ceiling substitution
  uses; without it A5 could only be satisfied by test-only behaviour, which §2.9 of the rehearsal
  spec forbids.
- The read-only recovery-state inspection surface and proof that it cannot invoke a writer.
- The M3-L11 root-level ignore entry, explicit hygiene refusal, evidence-root boundary validation,
  and adversarial path/symlink tests.
- Bounded edits to existing test modules that the new modules force.
- `Docs/m3/` evidence records for this phase.
- `Milestones/STATUS.md` and the navigation aids, under explicit instruction only.

### 10. Prohibited path categories

- Every accepted S4, S5, and S6 production module.
- Every migration, existing or new, unless a separately accepted decision authorizes one and the
  contract names it.
- `cohorts.py`, `pilot_policy.py`, `release/hashing.py`, `release/manifest.py`,
  `release/pilot_manifest.py`, `sec/pilot_manifest_store.py`, `paths.py`.
- `configs/`, `pyproject.toml`, `.github/`.
- `Docs/preregistration.md`, `Docs/sec_data_dictionary.md`, Decisions 001–028, every completed
  contract.
- Any code path that opens a socket during M3.1A.

### 11. Network permission

**M3.1A: NONE.** No socket is opened. The offline assertions in
`tests/integration/test_no_network.py` must continue to hold.

**M3.1B: ZERO LIVE REQUESTS.** Network stays disabled by default in configuration. The dry run makes
zero requests and constructs no transport. Identity validation reads a local environment variable and
contacts nothing.

### 12. Permitted SEC routes or source classes

**None are contacted.** The routes are *enumerated and asserted*, never requested. The enumeration is
the accepted registry:

| `source_id` | Host | Path family |
|---|---|---|
| `sec_bulk_submissions` | `www.sec.gov` | exact `/Archives/edgar/daily-index/bulkdata/submissions.zip` |
| `sec_company_tickers_exchange` | `www.sec.gov` | exact `/files/company_tickers_exchange.json` |
| `sec_company_tickers` | `www.sec.gov` | exact `/files/company_tickers.json` |
| `sec_sic_code_list` | `www.sec.gov` | exact `/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list` |
| `sec_edgar_filing_calendar` | `www.sec.gov` | exact `/submit-filings/filer-support-resources/edgar-calendar` and `/edgar/filer-information/calendar` |
| `sec_edgar_calendar_announcement` | `www.sec.gov`, `data.sec.gov` | manifest-exact only; no arbitrary URL |
| `sec_full_index_company` | `www.sec.gov` | pattern `^/Archives/edgar/full-index/(?:19[6-9][0-9]\|20[0-9]{2})/QTR[1-4]/company\.idx$` |
| `sec_submissions_entity` | `data.sec.gov` | pattern `^/submissions/CIK[0-9]{10}\.json$` |
| `sec_submissions_historical` | `data.sec.gov` | pattern `^/submissions/CIK[0-9]{10}-submissions-[0-9]{3}\.json$` |

### 13. Prohibited SEC routes or source classes

Every host other than `www.sec.gov` and `data.sec.gov`; every HTTP method other than `GET`; every
path the accepted filing-body guard refuses (`/Archives/edgar/data/`, `-index.htm`, and the `.txt`,
`.htm`, `.xml`, `.xsd` suffix families); accession archives; primary documents; complete submissions;
SGML headers; exhibits; Inline XBRL; standalone XBRL instances and taxonomies; **CompanyFacts**;
**the Frames API**; every third-party source (`PROHIBITED_SOURCE_HINTS`); and every financial-outcome
source.

### 14. Expected request volume

**M3.1A: exactly 0.** **M3.1B: exactly 0.** Both parts are zero-request by definition, and a
non-zero count is a Gate F failure, not a variance.

The volume M3.1B *plans* — for the **M3.2A window only** — is in §15.

### 15. Request-volume formula

**No count is frozen in this plan.** Every count below is produced by the accepted planner from
explicit inputs at the time the plan is produced, and approved by the owner as an exact integer for
that window. The v0.1 derived totals, subtotal, plan hash, and maximum-attempt product are
**withdrawn** (Decision 027 §0 items 5–6).

For the **M3.2A bootstrap window** M3.1B budgets:

```
planned_unique_logical_requests(M3.2A)
  = Σ_over_bootstrap_routes  U(route)

U(sec_bulk_submissions)          = 1
U(sec_company_tickers_exchange)  = 1
U(sec_company_tickers)           = 1
U(sec_sic_code_list)             = 1
U(sec_edgar_filing_calendar)     = 1                       # one instance per explicit --calendar-year
U(sec_edgar_calendar_announcement)
                                 = |approved entries in the explicitly named operator
                                    calendar-evidence manifest|          # 0 is lawful; see below
U(sec_full_index_company)        = |required_index_keys − already_satisfied_index_keys|
                                   # i.e. AFTER catalog-satisfied exclusion, per §4 of the M3.1
                                   # contract and the cache-hit rule below. The bare
                                   # |required_closed_quarters(coverage, as_of, include_open_quarter)|
                                   # is the pre-exclusion set and is NOT the planned count.

max_physical_attempts(window)
  = Σ_over_routes_in_window  U(route) × A_reachable(route)

A_reachable(route)
  = the maximum reachable physical attempts for that route, DERIVED from the implemented
    response-policy state machine and INDEPENDENTLY TESTED against its worst reachable path
    by ONE realizable full-path witness — a single SecClient.fetch() execution whose observed
    transport attempt count IS the tested bound. It is never asserted from constants, and it
    is never the SUM of separately measured retry, redirect, and cooldown terms: that sum
    proves each term separately reachable and never proves the composite path realizable.
    See §16 and offline_rehearsal_spec.md §6.9.

max_new_raw_objects(window)
  = planned_unique_logical_requests(window)

rate_limiter_spacing_floor_seconds
  = max(0, max_physical_attempts(window) − 1) ÷ requests_per_second
```

The **M3.2B dependent window** has its own plan, derived after M3.2A freezes its objects:

```
planned_unique_logical_requests(M3.2B)
  = U(sec_submissions_historical) + U(sec_submissions_entity)

U(sec_submissions_historical)
  = |historical-file references enumerated from the FROZEN M3.2A bulk-submissions object|
U(sec_submissions_entity)
  = |the explicit entity reconciliation set derived from the frozen M3.2A objects|
```

**Both M3.2B counts are `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` until M3.2A completes.**
They are then **derived, not estimated** — which is why no contingency allowance exists.

**Count inputs, by name:** the coverage window (`coverage_start`, `coverage_end`, `as_of_date`,
`include_open_quarter`); the explicit `--calendar-year`; the calendar-evidence manifest entry set;
the frozen M3.2A bulk-submissions object and the historical-file references it names; the explicit
entity reconciliation set; the catalog's already-satisfied instance set; `requests_per_second`; and
the response-policy state machine from which `A_reachable` is derived.

**Treatment rules, stated exactly:**

| Case | Treatment |
|---|---|
| **Deduplication** | Two retrievals collapse to one logical request only when `request_identity(source_id, normalized_url, parameters)` is identical. Nothing else deduplicates. |
| **Cache hit** | An instance already satisfied in the catalog is **not** planned and consumes no logical request. The dry run reports it as `already satisfied (reused)`. |
| **Conditional request** | A conditional re-validation is one logical request and at least one physical attempt. A `304 Not Modified` closes it, produces **no** new raw object, and records an immutable `reused_snapshot` observation with `SOURCE_SNAPSHOT_REUSED`. |
| **Retry** | A retry consumes **no** additional logical request and **one** additional physical attempt. Bounded by the accepted retry budget. |
| **Redirect** | Each validated hop is **one** additional physical attempt against the **same** logical request. Bounded by the accepted redirect depth; a loop or an over-depth chain fails closed. |
| **Cooldown** | A `403`, or a `429` without a usable `Retry-After`, halts **aggregate** traffic and permits exactly **one** controlled further request; a second cooldown is terminal. |
| **Already-present raw object** | A byte-identical body reconciles to the existing content-addressed object and creates **no** second object. A differing body at the same identity is a **new observation**, never an overwrite. |

### 15.1 `CURRENT_PLANNER_DISCREPANCY` — owner ruling recorded; implementation still blocks Gate F

**The accepted planner and accepted authority currently disagree about the 2026 Q2 quarter.**

[Decision 013](../Docs/Decisions/decision_013_pilot_selection_mechanics.md) §1 fixes the as-of date
at **2026-06-30** and states that **coverage extends through the closed 2026 Q2 quarter**, with
`include_open_quarter = false` and no open-2026-Q3 retrieval. The milestone plan's Gate G rule reads
"quarters ending on or before the as-of date are required."

The accepted planner, at exactly those inputs, classifies **2026 Q2 as the provisional open quarter**
— because 2026-06-30 falls *inside* 2026 Q2 — and with `include_open_quarter = false` **excludes it**,
ending its required set at 2026 QTR1.

2026 Q2 satisfies both conditions at once: it **ends on** the as-of date and it **contains** the
as-of date. The planner resolves that tie one way; Decision 013 §1 states the other.

Decision 028 classifies this as an inherited implementation defect and records the
controlling total order: a quarter beginning after `as_of_date` is unplanned; otherwise a quarter
ending on or before `as_of_date` is required and closed; otherwise it is provisional and open. The
corrected implementation uses `quarterly-index-instances/2.0`, refuses a caller-supplied mismatching
version, and leaves historical v1 hashes untouched. **Decision 013 remains unchanged and
controlling.**

Until Decision 028 is accepted and the bounded M3.1 implementation and tests make the planner agree
with that authority, **Gate F cannot pass** — a request plan that disagrees with the accepted
coverage cutoff is not a plan a budget can be approved against.

**How the M3.2B counts get resolved.** The separate M3.2 `m3 derive-dependent-plan` command
(**`PLANNED — NOT YET IMPLEMENTED`**, interface in the operator runbook) runs after M3.2A, over the
frozen bootstrap objects. It enumerates the historical-file references those objects actually name
and the explicit reconciliation set the operator supplies, prints the complete per-route table, and
emits the second request-plan hash — **while making zero requests**. Its output is the second budget
the owner approves. M3.1's `m3 plan-requests` command plans M3.2A only.

### 16. Hard request ceiling

**M3.1A and M3.1B: `0`.** One physical attempt is a phase failure.

The ceiling M3.1B *sets for the M3.2A window*:

```
HARD_REQUEST_CEILING(window)
  = Σ_over_routes_in_window ( U(route) × A_reachable(route) )
```

**No contingency multiplier is applied.** The v0.1 10% allowance is withdrawn: it existed only
because v0.1 tried to acquire, in one window, requests whose count depended on an object it had not
yet retrieved. The two-window split (M3.2A → freeze → derive → M3.2B) removes that cause, so each
window's count is derived rather than padded.

**`A_reachable(route)` is derived, never asserted.** The future implementation must:

1. **derive the maximum reachable physical attempts per route** from the implemented response-policy
   state machine as written — not from a formula that assumes retries, redirects, and cooldowns are
   simply additive;
2. **count every redirect hop, every retry, and every controlled post-cooldown request** as a
   physical attempt;
3. **test the worst reachable path independently**, rather than deriving the bound only by reading,
   using **one realizable full-path witness per route** (Decision 029 §7) rather than a sum of
   separately measured terms — and **a zero `U(route)` never waives that witness**: Gate F §9.3's
   arithmetic and Gate F §3.10's evidence obligation are separate requirements, so a route planning
   zero requests still needs an independently tested bound;
4. **produce an exact per-window integer**;
5. **obtain explicit owner approval** of that integer;
6. **refuse the request that would exceed the approved ceiling** — stop before, never after;
7. **never increase a ceiling during a running window.**

**The ceiling is a hard bound, not a target.** It is approved by the owner as an exact integer per
window before that window's network enablement, is recorded in that window's request budget and in
the Gate F record, and is **never raised mid-window**. A complete run may finish exactly at the
ceiling. Equality with work remaining yields `stopped_at_ceiling`, records
`SEC_REQUEST_CEILING_EXHAUSTED`, and refuses attempt `C+1`. More headroom requires stopping,
re-planning, and a new owner approval.

### 17. Stop conditions

Stop and report — do not work around — on any of:

1. any physical attempt occurring in either part;
2. the two dry runs producing **different** request-plan hashes;
3. the SEC identity being absent, malformed, or rejected by the boundary validator;
4. network being enabled in the effective configuration at any point in M3.1;
5. a route present in the plan that is not in the allowlist, or a denylisted route reachable;
6. any acquisition-rehearsal scenario failing, or any scenario being unimplemented, skipped, or
    `xfail`ed;
7. a receipt containing a prohibited field;
8. any evidence that receipt content reached a governed identity;
9. `A_reachable` being underivable, or the derived bound disagreeing with the independently tested
    worst reachable path — **including** a non-empty `unmeasured_routes`, a false
    `a_reachable_fully_tested`, or a tested key set that is not exactly equal to the authoritative
    derived key set. A route excluded from the agreement predicate is an untested bound, not a pass;
10. **the Decision 028 planner-v2 correction not being implemented and accepted** — Gate F cannot
    pass while the planner and Decision 013 §1 disagree about 2026 Q2;
11. the live baseline disagreeing with the contract's stated baseline;
12. a full SEC identity or an absolute personal path appearing in any output, log, or artifact;
13. the owner declining to approve the exact M3.2A budget or ceiling;
14. any attempt to rehearse or implement a snapshot, selection, reserve, sealing, manifest, or root
    path in this phase.

### 18. Retry and response-policy boundary

**No live retry occurs, because no live request occurs.** M3.1A exercises the accepted policy
against *scripted* responses only: the full matrix of `proceed`, `retry`, `retry_after`, `cooldown`,
`fail`, and `quarantine`, the `403` and unqualified-`429` aggregate halt, the single controlled
post-cooldown request, retry exhaustion at `max_transient_retries`, and the invariant that **a
failure never becomes a valid empty result**.

**M3.1 changes no response-policy constant and no response classification.** Under Decision 028 it
adds the two registered terminal codes `SEC_REQUEST_CEILING_EXHAUSTED` and
`SEC_ACQUISITION_INTERRUPTED`, and makes the narrow terminal fallback that assigns
`SEC_RETRIES_EXHAUSTED` to a second unqualified `429`. Under
[Decision 029](../Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md)
§5 it adds exactly one further code, `OFFLINE_REHEARSAL_SCENARIO_MISMATCH` (category `integrity`,
`blocks_release=true`, `requires_manual_review=false`), for a rehearsal scenario that does not reach
the state its specification names. **`SEC_ACQUISITION_INTERRUPTED` is preserved for genuine
acquisition interruption only** and may never stand in for a defective witness. No other reason-code
meaning changes, and the receipt schema is unchanged in every field, type, status value,
canonicalization rule, and digest preimage.

**M3.1A exit requirements, stated exactly** (Decision 029 §§6–7). The phase token requires all four
of `passed`, `complete`, `a_reachable_agrees`, and **`a_reachable_fully_tested`**; `unmeasured_routes`
must be **empty**; and the tested route key set must be **exactly equal** to the authoritative derived
key set. `m3 rehearse-report` recomputes these rather than trusting a stored report, and a
subset-matching bounds comparison is not agreement. A diagnostic subset run may complete as a command
but never emits the token.

### 19. Schema-drift boundary

M3.1A must prove the **fail-closed** behaviour against injected drift: an unknown extra field is
retained and logged; a missing required field, an unexpected null, a changed type, or a malformed
nested array **stops processing and preserves evidence**. A new historical-file reference is a
recorded drift event, not a silent expansion of the plan.

**No drift may be resolved by supplying a default, coercing a type, or dropping a row.** Real drift
in M3.2 is an incident, recorded on
[`Docs/m3/templates/schema_drift_incident.md`](../Docs/m3/templates/schema_drift_incident.md).

### 20. Leakage controls

- **L01, L03** — no future information: the rehearsal uses only synthetic data with explicit
  timestamps; no real filing, fact, or outcome is read.
- **L04** — the universe is never drawn from a current index; the plan enumerates SEC sources only.
- **L10** — every rehearsal failure is recorded, not dropped, so differential failure stays visible.
- **L15, L19; Decision 015** — no pilot membership or stratification informs anything.
- **L18** — no external corpus is consulted.
- **A leakage attestation** is recorded in the Gate F evidence packet, naming the exact read set.

### 21. Provenance requirements

Every rehearsal raw object carries the full lineage the accepted store requires: content-addressed
identity, `content_sha256` over decoded entity bytes, the stored path relative to the data root,
compression, the lineage intent record, and the source-observation linkage. Where a synthetic fixture
stands in for a filing-level artifact, it still carries accession, CIK, form type, filing date,
acceptance timestamp, fiscal period end, and source offsets (CLAUDE.md rule 9), so the rehearsal
proves the lineage path rather than bypassing it.

### 22. Execution-receipt requirements

**M3.1A** produces one receipt per rehearsal command, with `invocation_mode = "rehearsal"`, and must
demonstrate the receipt's redaction rules and its non-contamination of S5 and S6 identities.

**M3.1B** produces one receipt per dry run, with `invocation_mode = "dry_run"`,
`actual_logical_request_count = 0`, `actual_physical_attempt_count = 0`, the acquisition-window and
request-plan identities, the planner and request-plan schema versions, and the planned counts.
Because the two dry runs precede approval, they omit `approved_request_ceiling`. Gate F's later
outcome belongs only in its checklist.

Both must satisfy every prohibition in
[`Docs/m3/execution_receipt_spec.md`](../Docs/m3/execution_receipt_spec.md) §5.

### 23. Validation requirements

- Two dry runs, executed independently, producing **byte-identical plan output and identical plan
  hashes**.
- All twelve acquisition-rehearsal scenarios A1–A12 implemented and passing, none skipped or
  `xfail`ed.
- **The independently tested worst reachable path per route**, producing `A_reachable` and agreeing
  with the derived bound.
- Boundary tests proving the Decision 028 quarter total order and policy-version refusal.
- An assertion that no socket is opened during the rehearsal.
- An assertion that the receipt schema contains **no** prohibited field.
- An assertion that the S5 and S6 identity functions produce identical values with and without a
  receipt present — the non-contamination proof.
- Allowlist and denylist assertions over every registered source and a representative prohibited
  path per denied family.

### 24. Offline tests

The whole phase is offline. The minimum test categories: acquisition-rehearsal scenario tests (one
per scenario A1–A12); **worst-reachable-path tests deriving `A_reachable` per route from the
implemented state machine**; request-plan determinism and plan-hash stability tests;
allowlist/denylist boundary tests; receipt construction, serialization, mode-classification, and
redaction tests; the identity non-contamination test; and the existing
`tests/integration/test_no_network.py` assertions, unchanged and still passing.

### 25. Full phase-end validation

`ruff check .`; `ruff format --check .`; `mypy src`; `pytest`; `make sqlite-check`; `make secrets`;
`make hygiene`; `make context` — in that order, all green — plus the Gate F evidence packet, the
completed request budget, and the recorded owner approval.

### 26. Independent-review requirement

**Required, at the M3.1 boundary**, by a focused Opus Max review performed by a session that wrote
none of the M3.1 work. Its question: *does the rehearsal actually cover the workflow, is Gate F
genuinely zero-request, and is the approved budget derived rather than asserted?* It is not a
re-audit of Milestones 0–2.

**The review must produce a durable artifact** (Decision 029 §13). No §17/§26 review artifact exists
in tracked history, refs, reflogs, or unreachable objects; commit prose describing prior rounds is
not a review record, and a fix commit never converts a prior `FAIL` into a `PASS`. The required
artifact is written at the frozen implementation SHA to
`Docs/m3/reviews/m3_1_section_17_review_<FULL_REVIEWED_SHA>.md` and carries the reviewer session and
model identifier with a non-authorship attestation, the UTC review date, the exact reviewed commit
and tree SHA, the live remote SHA and clean-status evidence, the reviewed diff boundaries, every
validation command and its result, a finding table with dispositions, the §26 answer, the exact
verdict `M3_1_SECTION_17_REVIEW: PASS` or `M3_1_SECTION_17_REVIEW: FAIL`, and a reviewer signature.
**A FAIL artifact is retained and blocks the tokens; it is never rewritten into a PASS.**

### 27. Rollback procedure

No data is acquired, so rollback is code-level only: discard the working tree to the phase-entry
baseline, or revert the phase commit under explicit owner instruction. Rehearsal artifacts under the
data root are removable because they are synthetic — but the rehearsal **evidence record** is
retained. No raw object produced by a real retrieval exists to preserve, because none was retrieved.

### 28. Recovery procedure

An interrupted rehearsal is restarted from a clean synthetic data root; acquisition scenarios
A9–A11 prove duplicate reconciliation, changed-body preservation, and interruption recovery. An
interrupted dry run is simply re-run: it
holds no state and writes no catalog row. If two dry runs disagree, **do not re-run until they
agree** — the disagreement is the finding.

### 29. Idempotency or replay expectations

The dry run is **pure**: identical explicit inputs produce identical output bytes and an identical
plan hash, on any day, on any machine, with no clock dependency. The rehearsal is **replayable**:
re-running a scenario from the same fixtures reproduces the same persisted state, the same reason
codes, and the same identities, and re-running a completed scenario performs **no** further write.

### 30. Required evidence packet

**Every item below is private evidence** (§12). Only its type, phase, status, SHA-256, and reference
identifier are recorded publicly, in
[`Docs/m3/templates/evidence_index.md`](../Docs/m3/templates/evidence_index.md).

- [`Docs/m3/templates/gate_f_checklist.md`](../Docs/m3/templates/gate_f_checklist.md), completed and
  owner-signed.
- [`Docs/m3/templates/request_budget.md`](../Docs/m3/templates/request_budget.md), completed and
  owner-approved with the exact M3.2A ceiling.
- The acquisition-rehearsal evidence record: per-scenario outcomes for A1–A12, their reason-code
  results, the derived and tested `A_reachable` per route, the non-contamination proof, and the
  receipt sample set with prohibited fields shown absent.
- The M3-L12 implementation and boundary-test evidence.
- The two dry-run outputs and their identical plan hashes.
- One execution receipt per rehearsal command and per dry run.

### 31. Completion token

```
M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED          # M3.1A only
M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION   # M3.1 as a whole
```

### 32. Implementation commit policy

**One implementation commit for M3.1**, by default. Because M3.1A and M3.1B are separately
meaningful and M3.1A gates M3.1B, the phase plan **explicitly justifies** at most one intermediate
checkpoint at the M3.1A/M3.1B boundary — and that checkpoint is taken **only** if the owner
separately authorizes it. Otherwise, one commit.

### 33. Governance acceptance-commit policy

M3.1 acceptance is recorded in a separate bounded governance commit carrying the acceptance decision
record and the status and navigation updates it requires. That commit changes no implementation byte.

### 34. Annotated tag policy

**`m3.1-complete`**, annotated, created **only after** independent M3.1 acceptance and **only** at the
accepted commit. **No tag for M3.1A.** No tag for an unreviewed state.

### 35. Next authorized action

On success: record `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION`, then
`INDEPENDENT_M3_1_ACCEPTANCE_REVIEW`, then — separately — owner authorization to create the bounded
M3.2 contract.

### 36. Conditions preventing progression

M3.2A may not begin while **any** of these holds: the acquisition rehearsal has not passed; the two
dry runs disagree; **the Decision 028 planner-v2 correction is unaccepted or unimplemented**;
**the Decision 029 remediation is unimplemented**; `A_reachable` is underived or
untested **for any route, including a route planning zero requests**; `unmeasured_routes` is
non-empty; the M3.2A request budget is unapproved; the hard ceiling is unapproved; the allowlist or
denylist is unasserted; the SEC identity is unvalidated or has been printed; network is enabled
outside an authorized window; the independent M3.1 review has not passed **or has produced no
durable artifact**; the M3.2 contract does not exist; or any Gate F checklist item is `FAIL` or
`UNKNOWN`.

---

# Phase M3.2 — Controlled metadata-only SEC acquisition and Gate H

**One phase, two sequential acquisition windows.** M3.2A retrieves only sources whose complete
logical-request set is derivable before any network access; M3.2B retrieves only the dependent
requests **derived from the frozen M3.2A objects**. Gate H integrates both.

**Each window carries its own plan identity, budget, hard ceiling, owner approval, execution
receipts, and stop-before-overflow enforcement.** A window's approval never covers the other window.

### 1. Objective

Acquire, under a per-window approved budget and ceiling, exactly the already-approved SEC
**metadata** needed to build a real candidate snapshot — deriving the dependent requests from frozen
evidence rather than estimating them — and prove afterwards, at Gate H, that both windows stayed
inside every boundary they were given.

### 2. Exact scope

**M3.2A — bootstrap window.** Enable the network for one named, authorized command. Acquire **only**
the bootstrap sources whose complete logical-request set was derivable before access:
`sec_bulk_submissions`, `sec_company_tickers_exchange`, `sec_company_tickers`, `sec_sic_code_list`,
`sec_edgar_filing_calendar`, `sec_edgar_calendar_announcement` (manifest-resolved only), and
`sec_full_index_company`.

**Between the windows, in this exact order:**

1. **disable transport**;
2. **freeze and identify the exact bootstrap raw objects** by their content-addressed identities;
3. **derive** the historical-submission references **from the frozen bulk-submissions object**;
4. **derive** the explicit entity reconciliation set from the frozen objects;
5. **produce a second zero-request request plan** covering only those dependent requests;
6. **obtain a second exact owner approval** of that plan's budget and hard ceiling.

**M3.2B — dependent window.** Re-enable the network for one named, authorized command. Acquire
**only** the `sec_submissions_historical` and `sec_submissions_entity` requests enumerated by that
second plan — nothing the second plan does not name.

**In both windows:** store every retrieved object content-addressably with immutable provenance;
classify every response; enforce that window's budget and stop before that window's ceiling; detect
schema drift and fail closed; survive interruption and resume without duplicate substantive writes;
emit one execution receipt per live command; and **disable the network again** at the window's end.

**After M3.2B:** run Gate H over both windows together and produce its evidence.

### 3. Explicit non-scope

No filing body, primary document, accession index, complete submission, SGML header, exhibit, or
XBRL artifact. No CompanyFacts. No Frames API. No outcome data. **No candidate snapshot** — freezing
one is M3.3. **No selection run.** **No manifest.** **No approval.** **No publication.** No change to
any accepted S4, S5, or S6 identity, preimage, or methodology.

**No dependent request in M3.2A**, and **no bootstrap request in M3.2B**. Neither window may issue a
request the other window's plan owns. **No M3.2B request may be issued under the M3.2A approval** —
the second window requires its own owner-approved budget and ceiling, derived after the freeze.

**No contingency allowance in either window.** Counts are derived from explicit inputs and frozen
source objects, never padded.

### 4. Controlling decisions

Decision 024 §§5.1, 5.2 (the S8 row), 6, 8; Decision 027;
[Decision 007](../Docs/Decisions/decision_007_sec_universe.md) (approved sources, canonical CIK);
[Decision 008](../Docs/Decisions/decision_008_filing_inventory.md) (inventory, amendments);
[Decision 009](../Docs/Decisions/decision_009_raw_data_governance.md) (raw-data governance, §10
hashing); [Decision 010](../Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md)
(temporal availability, cohort date source);
[Decision 011](../Docs/Decisions/decision_011_edgar_operating_calendar_provenance.md) (calendar
provenance); [Decision 012](../Docs/Decisions/decision_012_accession_observation_resolution.md)
(observation resolution); Decision 013 §1 (as-of);
[`milestone_2_3_pilot_selection_plan.md`](milestone_2_3_pilot_selection_plan.md) §§2.1, 2.2, 11
Gate H, 12, 13.

### 5. Required owner decisions

1. **The bounded M3.2 contract**, with exact authorized paths and an explicit per-window network
   authorization.
2. **Confirmation of the exact M3.2A request budget and hard ceiling** approved at Gate F, restated
   at M3.2A entry — a stale budget is not an approved budget.
3. **A second exact owner approval, between the windows**, of the derived M3.2B plan, its budget, and
   its hard ceiling. **M3.2B may not begin without it**, and it cannot be given before M3.2A's
   objects are frozen.
4. **Authorization to freeze a real candidate snapshot** — taken at Gate H exit, not at entry, and
   not implied by either window succeeding.
5. **A ruling on any schema-drift incident** either window raises.

### 6. Prerequisites

- `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION` recorded; independent M3.1 review passed;
  `m3.1-complete` created.
- A bounded M3.2 contract, accepted, with explicit network authorization and exact paths.
- The Gate F checklist complete, every item `PASS`, owner-signed.
- **The Decision 028 planner-v2 correction accepted and implemented** — the planner agrees with
  Decision 013 §1 and records policy `quarterly-index-instances/2.0`.
- The **M3.2A** request budget and hard ceiling approved as exact integers.
- Gate H **pre-run** state established, before **each** window: an isolated M3.2 data root; a
  consistent SQLite backup of any accepted prior state; recorded available storage; confirmed
  quarantine and staging paths; the confirmed single-writer lock; **no** stale `.part` files and
  **no** unresolved recovery events; that window's approved plan hash saved.
- `[sec]` extra installed; SEC identity valid; live baseline re-verified with `make context`.
- **M3.2B additionally requires**: M3.2A complete; transport disabled; the bootstrap objects frozen
  and identified; the dependent references derived from them; the second zero-request plan produced;
  and the **second owner approval** recorded.

### 7. Exact inputs

**M3.2A:** the Gate F request plan and its hash; the approved M3.2A budget and ceiling; the approved
coverage window and as-of inputs; the explicit `--calendar-year`; the accepted source registry and
URL family policies; the accepted response, retry, cooldown, and rate-limit policy; the accepted
raw-store and provenance rules; the accepted schema-drift policy; the validated SEC user-agent,
resolved on demand and never printed; the isolated data root and its catalog at migration `0013`.

**M3.2B additionally:** the **frozen** M3.2A raw objects and their content-addressed identities; the
historical-submission references **derived from the frozen bulk-submissions object**; the explicit
entity reconciliation set; the second zero-request plan and its hash; and the **second** owner-approved
budget and ceiling.

### 8. Exact outputs

**Per window:** immutable raw objects for every successful logical retrieval, content-addressed with
full lineage; one source-observation row per retrieval with its validated redirect chain; parsed
source records with parser versions and QA state; quarantined objects where the policy quarantines;
that window's recorded actual logical-request count, actual physical-attempt count, and
response-classification totals; that window's drift outcome; and one execution receipt per live
command.

**Between the windows:** the frozen bootstrap object identities; the derived historical-submission
reference set; the derived entity reconciliation set; the second zero-request plan and its hash; and
the recorded second owner approval.

**After M3.2B:** the accession and registrant metadata the approved sources yield; the completed
[`Docs/m3/templates/gate_h_checklist.md`](../Docs/m3/templates/gate_h_checklist.md) integrating both
windows; and the token `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED`.

**Every completed artifact above is private evidence** (§12); the public repository records only its
type, phase, status, SHA-256, and reference identifier in the evidence index.

### 9. Authorized future path categories

- Bounded edits to the existing census orchestration and index-retrieval surface, where the contract
  names them.
- A new acquisition-driver module and its tests, if the contract creates one.
- The receipt-emission call sites for live commands.
- CLI wiring for the authorized acquisition subcommand and its explicit live flag.
- `Docs/m3/` evidence records; `Docs/sec_data_dictionary.md` **only if** the phase introduces schema,
  and then in the same pass.
- `Milestones/STATUS.md` and navigation aids, under explicit instruction only.

### 10. Prohibited path categories

Every accepted S4, S5, and S6 module; every existing migration; `cohorts.py`; `pilot_policy.py`;
`release/pilot_manifest.py`; `sec/pilot_manifest_store.py`; `configs/` beyond the explicitly
authorized network-enable change the contract names; `.github/`; `Docs/preregistration.md`;
Decisions 001–028; every completed contract; and any code path that would retrieve a prohibited
route.

### 11. Network permission

**CONTROLLED AND EXPLICITLY AUTHORIZED, per window.** Network is disabled by default and is enabled
**only** for the one named acquisition command, **only** for the duration of that window, and
**only** with that window's approved budget and ceiling in force.

**It is disabled again at the end of each window** — after M3.2A, before the freeze and derivation
step, and again after M3.2B, before Gate H concludes. **Transport is off while the dependent plan is
being derived**, which is what makes that derivation an offline act over frozen evidence.

**M3.2A's authorization does not extend to M3.2B.** Each window is separately enabled under its own
owner approval.

### 12. Permitted SEC routes or source classes

**M3.2A:** the seven bootstrap families only — `sec_bulk_submissions`,
`sec_company_tickers_exchange`, `sec_company_tickers`, `sec_sic_code_list`,
`sec_edgar_filing_calendar`, `sec_edgar_calendar_announcement` (manifest-resolved only), and
`sec_full_index_company`.

**M3.2B:** the two dependent families only — `sec_submissions_historical` and
`sec_submissions_entity` — and only the exact requests the second plan enumerates.

All from the nine registered families in the M3.1 §12 table, on hosts `www.sec.gov` and
`data.sec.gov`, method `GET` only. Expected content types by route: `zip` for
`sec_bulk_submissions`; `json` for `sec_company_tickers_exchange`, `sec_company_tickers`,
`sec_submissions_entity`, `sec_submissions_historical`; `html` for `sec_sic_code_list`,
`sec_edgar_filing_calendar`, `sec_edgar_calendar_announcement`; `text` for
`sec_full_index_company`.

**Permitted metadata fields** — the already-approved families only: canonical CIK; registrant name
and former names with their `from`/`to` ranges; tickers and exchanges (noncanonical aliases only);
SIC; fiscal year end; accession number; form type; official filing date; acceptance timestamp; report
date; per-filing XBRL and Inline-XBRL flags; the quarterly index's registrant-per-accession rows;
SIC reference codes and descriptions; and EDGAR operating-calendar evidence.

### 13. Prohibited SEC routes or source classes

As M3.1 §13, and binding at runtime rather than only in assertion: every non-SEC host; every method
other than `GET`; `/Archives/edgar/data/` and every accession-archive path; `-index.htm`; the `.txt`,
`.htm`, `.xml`, `.xsd` filing-document suffix families; primary documents; complete submissions; SGML
headers; exhibits; Inline XBRL documents; standalone XBRL instances and taxonomies; **CompanyFacts**;
**the Frames API**; filing bodies used to classify amendment purpose; and any financial-outcome
source. **External corpora remain validation-only and are not retrieved here at all.**

### 14. Expected request volume

**M3.2A:** exactly the Gate F approved plan for that window. **M3.2B:** exactly the second approved
plan, derived after the freeze. **No count is stated here**; each is produced by the accepted planner
from explicit inputs and approved as an exact integer for its window (Decision 027 §15).

**A deviation from a window's approved plan is a finding, not a variance.** Actual counts are
recorded per window and compared item by item at Gate H.

### 15. Request-volume formula

Identical to M3.1 §15. **Each window's plan is evaluated once, before that window opens, and is not
recomputed during the run.** The run consumes its approved plan; it does not re-derive one.

The M3.2B formula's inputs do not exist until M3.2A's objects are frozen — which is the whole reason
the phase has two windows.

### 16. Hard request ceiling

**One exact owner-approved integer per window**, in force for that window only. **The acquisition
refuses the attempt that would exceed it** — it stops before, never after. A complete run ending
exactly at the ceiling succeeds; equality with planned work remaining is `stopped_at_ceiling` and a
Gate H failure. The ceiling is **never raised mid-window**, and a re-plan requires a new owner
approval.

**M3.2A's ceiling does not bind or budget M3.2B, and M3.2B's does not extend M3.2A.** Consumed counts
are tracked per window and reconciled together at Gate H.

### 17. Stop conditions

Stop and report on any of:

1. reaching that window's hard request ceiling **with planned work remaining**;
2. any request to a prohibited host, method, or route, attempted or constructed — including a
   dependent request issued in M3.2A, or a bootstrap request issued in M3.2B;
3. any response the accepted policy cannot classify;
4. a second aggregate cooldown, or a `403`/block-page signature after one controlled retry;
5. unresolved schema drift of any blocking kind;
6. a raw object failing its `content_sha256` verification or its lineage check;
7. a changed body at an `immutable` source identity, or at a closed-quarter `dated_snapshot`, without
   an official explanation;
8. a redirect chain that loops, exceeds depth, leaves the source's URL family, or changes an
   identity-bound source path;
9. any `.part` file, orphan, or unresolved recovery event that recovery cannot resolve deterministically;
10. the SEC identity being invalid, or appearing in any log or artifact;
11. the catalog failing quick, integrity, or foreign-key checks;
12. actual counts diverging from that window's approved plan in a way the plan does not account for;
13. transport still enabled when the between-windows freeze and derivation step begins;
14. M3.2B beginning without its own derived plan and its own recorded owner approval;
15. the derived M3.2B reference set disagreeing with what the frozen bootstrap objects actually name.

### 18. Retry and response-policy boundary

The accepted policy applies unchanged and is not re-tuned for the live run:

- maximum **5** transient retries per logical request; exponential backoff with a **60 s** ceiling;
- `Retry-After` honoured for a `429` when it carries a usable delta-seconds value;
- a `403`, an unqualified `429`, or a block-page signature **halts aggregate traffic** for **600 s**
  and permits exactly **one** controlled further request; a second cooldown is terminal;
- retryable statuses `408, 500, 502, 503, 504`; a `404` on an archival path is recorded as absent
  evidence; a `404` on a recent target retries before failing;
- **a failure never becomes a valid empty result** — every terminal failure names a registered reason
  code;
- HTML where JSON was expected, a non-JSON body prefix, and a ZIP without a local-file signature are
  **quarantined**, not parsed.

### 19. Schema-drift boundary

Unknown extra fields are **retained and logged**. A missing required field, an unexpected null, a
changed type, or a malformed nested array is **blocking**: stop, preserve evidence, record the reason
code, and raise a schema-drift incident on
[`Docs/m3/templates/schema_drift_incident.md`](../Docs/m3/templates/schema_drift_incident.md). A new
historical-file reference is recorded as a drift event and **does not silently expand the plan** — it
is either inside the approved budget or it stops the run.

**Drift is never resolved by defaulting, coercing, or dropping.** It is referred for an owner ruling.

### 20. Leakage controls

- **L01** — only metadata available at retrieval is stored; no later fact is back-filled.
- **L04** — the universe comes from historical SEC submissions and the quarterly index; delisted and
  inactive registrants are retained.
- **L05** — filing date, fiscal period end, fiscal year, and form are stored separately.
- **L10** — every retrieval and parse failure is recorded with its reason code, and coverage is
  reported by year and source, so differential failure is visible rather than silent.
- **L18** — no external corpus is retrieved or consulted.
- **Decision 010** — the official filing date is the cohort-assignment source; the acceptance date is
  audit-only.
- **Decisions 002 and 015** — no outcome source is touched, and no pilot artifact yet exists to leak.

### 21. Provenance requirements

Every stored object carries: `content_sha256` over decoded entity bytes; the transport hash; the
stored-object hash; the relative storage path; compression; the retrieval attempt identity;
`retrieved_at` UTC; HTTP validator metadata; the complete validated redirect chain; the parser
identifier and version; parser status; the schema fingerprint; and supersession lineage. Accession,
CIK, form type, filing date, acceptance timestamp, fiscal period end, and source offsets are carried
through every derived row (CLAUDE.md rule 9). **A differing later response is a new observation and
never an overwrite** (CLAUDE.md rule 6).

### 22. Execution-receipt requirements

**One receipt per live command**, mandatory. It must record: the request-plan identity; the approved
ceiling; planned logical and maximum physical counts; **actual** logical and physical counts;
response-classification totals; raw-object, duplicate-object, and cache-hit counts; the schema-drift
outcome; the Gate H outcome once known; completion status; the reason code; and the interruption
state. A resumed run records its predecessor receipt.

**It must contain none of the prohibited fields** — no full SEC identity, no email address, no
secret, no token, no cookie, no authorization header, no raw response body, no absolute personal
path, and no substantive row content.

### 23. Validation requirements

Planned versus actual reconciliation **per window**, per route and in total; raw-store completeness
against each plan; provenance completeness on every stored object; response-policy compliance with no
unclassified response; zero prohibited-route attempts in either window; zero budget overflow in
either window; zero unresolved drift; zero secret or identity leakage in logs and artifacts; catalog
quick, integrity, and foreign-key checks passing; migration integrity verified before further writes;
**proof that the M3.2B plan was derived from the frozen M3.2A objects and matches what they name**;
**proof that transport was disabled between the windows**; and confirmation that **no snapshot, no
selection, and no manifest exists yet**.

### 24. Offline tests

Every new or edited code path ships with offline tests using scripted responses — never live ones:
per-window budget enforcement and the stop-before-ceiling boundary; ceiling derivation from the
implemented state machine; per-route allowlist and denylist enforcement, including window-scoped
route separation; resumability with no duplicate substantive write; duplicate-object reconciliation;
drift refusal; derivation of the dependent plan from a frozen object fixture; receipt field
completeness, mode classification, and redaction; and the unchanged
`tests/integration/test_no_network.py` assertions for every non-authorized path.

### 25. Full phase-end validation

`ruff check .`; `ruff format --check .`; `mypy src`; `pytest`; `make sqlite-check`; `make secrets`;
`make hygiene`; `make context` — all green — plus `tests/unit/test_migration_provenance.py`, the
catalog integrity report, the completed Gate H checklist, and the reconciled request accounting.

### 26. Independent-review requirement

**Required.** A focused Opus Max review by a session that ran none of the acquisition. Its question:
*did the run stay inside its approved routes, budget, ceiling, and policies, and is every stored
object fully provenanced?* Gate H evidence is its input; the raw store and catalog are its ground
truth.

### 27. Rollback procedure

Per §11 of this plan, in that exact order. Concretely for M3.2: stop new requests; mark the
acquisition run failed with its reason code; preserve every attempt and every committed raw object;
quarantine partial or unverifiable objects; roll back the uncommitted transaction; rebuild the JSONL
projection from SQLite; rerun integrity and foreign-key checks; write the terminating receipt;
**require an explicit resume-or-new-run decision.** **Nothing acquired is deleted.**

### 28. Recovery procedure

Follow
[`Docs/m3/templates/interrupted_run_recovery.md`](../Docs/m3/templates/interrupted_run_recovery.md):
locate the last successful receipt; establish the interruption point; inspect database state,
raw-store state, and partial-file state; reconcile the request count against the budget; determine
whether resume is safe; **prove duplicate prevention before resuming**; resume under the same
approved budget and ceiling with the consumed count carried forward; write the resumed receipt naming
its predecessor; reconcile finally at Gate H.

**Recovery uncertainty is a stop condition.** If it cannot be determined whether a write committed,
the run does not resume.

### 29. Idempotency or replay expectations

A resumed acquisition performs **no duplicate substantive write**: an already-satisfied instance is
reused, a byte-identical body reconciles to the existing object, and a differing body becomes a new
observation. Re-running a completed acquisition against an unchanged catalog issues **zero** new
logical requests. The acquisition is restartable at every boundary the rehearsal exercised.

### 30. Required evidence packet

**Every item below is private evidence** (§12); the public repository records only its type, phase,
status, SHA-256, and reference identifier in
[`Docs/m3/templates/evidence_index.md`](../Docs/m3/templates/evidence_index.md).

[`Docs/m3/templates/gate_h_checklist.md`](../Docs/m3/templates/gate_h_checklist.md), completed and
owner-signed, integrating **both** windows; the request-accounting reconciliation per window (planned
versus actual, per route); the **second** window's request budget and its recorded owner approval;
the frozen bootstrap object identities and the derived dependent reference set; the raw-store and
provenance completeness report; the response-classification totals; the drift outcome, with any
incident record; the recovery record if either window was interrupted; every execution receipt from
the phase; and the confirmation that network is disabled again after each window.

### 31. Completion token

```
M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED
```

### 32. Implementation commit policy

**One implementation commit**, by default. An intermediate checkpoint is allowed only if the M3.2
contract explicitly justifies one and the owner separately authorizes it. **No commit contains data,
a database, a raw object, or a `.part` file** — `make hygiene` enforces this.

### 33. Governance acceptance-commit policy

M3.2 acceptance is recorded in a separate bounded governance commit carrying the acceptance record
and its status and navigation updates, changing no implementation byte.

### 34. Annotated tag policy

**`m3.2-complete`**, annotated, only after independent M3.2 acceptance.

### 35. Next authorized action

On success: record `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED`, then
`INDEPENDENT_M3_2_ACCEPTANCE_REVIEW`, then — separately — owner authorization to freeze a real
candidate snapshot and to create the bounded M3.3 contract.

### 36. Conditions preventing progression

M3.3 may not begin while any of these holds: any Gate H item is `FAIL` or `UNKNOWN`; actual requests
diverge unexplained from either window's plan; any prohibited route was attempted; either budget
overflowed; **M3.2B ran without its own derived plan and recorded owner approval**; **the dependent
plan was not derived from the frozen bootstrap objects**; drift is unresolved; any response is
unclassified; any stored object lacks complete provenance; network is still enabled; a secret or
identity leaked; the independent M3.2 review has not passed; or the M3.3 contract does not exist.

---

# Phase M3.3 — Builder rehearsal, then frozen real snapshot and exact real manifest construction

Planned in two sequential internal parts: **M3.3A** builds the candidate-snapshot builder and
rehearses the whole execution path offline; **M3.3B** performs the real freeze and the real
deterministic execution. **M3.3B may not begin until M3.3A passes its independent review.**

### 1. Objective

Build and prove the candidate-snapshot builder and the execution path offline, then freeze the real
candidate snapshot from the acquired metadata, execute the accepted deterministic selection over it,
persist, reconstruct, and replay the result, and construct the **exact real-data pilot manifest** —
producing the exact `root_manifest_sha256` as an **output**, never as an approval.

### 2. Exact scope

**M3.3A — builder and execution rehearsal.** Implement the **candidate-snapshot builder** under this
phase's bounded contract. Then run the **execution rehearsal** specified in
[`Docs/m3/offline_rehearsal_spec.md`](../Docs/m3/offline_rehearsal_spec.md) §6 — scenarios E1–E8,
against synthetic or real-shaped fixtures, offline — covering snapshot construction and freeze; every
Decision 019 §9 snapshot-validation obligation; plain/dashed accession disagreement; feasible and
fail-closed selection; reserves and dispositions; persistence and reconstruction; write-free replay;
selection-result sealing; S6 manifest construction; file/database atomicity; identical-root replay;
and Decision 023 **O1** behaviour. **This is where those scenarios belong** — M3.3A is the first
phase in which the production paths they exercise exist.

**M3.3B — real freeze and deterministic real execution.** Only after M3.3A passes:

Disable transport. Freeze the real candidate snapshot and compute its identity. Execute the accepted
joint entity–accession selector, reserve construction, and disposition handling — unchanged. Persist
the S5 run inside its single `running` window, ending at `running -> feasible`. Reconstruct it
deterministically through the accepted entry point. Prove write-free idempotent replay. Seal
`selection_result_sha256` append-once. Compute the eight S6 component digests, `root_manifest_sha256`,
and `manifest_id`. Render the complete thirteen-block document with all 81 milestone-plan §10 items
bound. Serialize canonically. Verify. Deliver **the CLI output Decision 021 §16 deferred from S6**,
including milestone-plan §10's "command invocation" field (crosswalk item 80). Produce the
real-snapshot evidence packet and the limitations update.

### 3. Explicit non-scope

**No owner approval** — that is M3.4. **No publication.** No manifest state beyond `proposed`. No
second selector, no reserve substitution, no discretionary trimming, no relaxation of any accepted S5
output. No network. No outcome data, filing text, CompanyFacts, or Frames. **No S4 draft input.** No
operational timestamp in any substantive identity. No approval state and no publication state written
anywhere.

**No real snapshot in M3.3A** — it uses synthetic or real-shaped fixtures only, against an isolated
data root. **No further metadata acquisition in either part**; if the acquired set proves
insufficient, that is a stop-and-refer condition, not a licence to reopen the network.

### 4. Controlling decisions

Decision 024 §§5.1, 5.2 (the S9 row), 6, 8; Decision 027;
[Decision 013](../Docs/Decisions/decision_013_pilot_selection_mechanics.md) §§2, 5–7;
[Decision 016](../Docs/Decisions/decision_016_m23_schema_and_artifact_architecture.md) §§3–8;
[Decision 017](../Docs/Decisions/decision_017_s4_quota_policy_and_control_evidence.md);
[Decision 018](../Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md);
[Decision 019](../Docs/Decisions/decision_019_m23_s5_storage_to_pure_input_mapping.md), **§9 the
snapshot-freeze validation obligations**;
[Decision 020](../Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md);
[Decision 021](../Docs/Decisions/decision_021_m23_s6_manifest_construction.md) v0.5 §§6–13, 15, 16;
[Decision 022](../Docs/Decisions/decision_022_m23_s6_reserve_rank_applicability.md);
[Decision 023](../Docs/Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md) §7;
[Decision 010](../Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md);
[Decision 014](../Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md);
[`milestone_2_3_pilot_selection_plan.md`](milestone_2_3_pilot_selection_plan.md) §10.

### 5. Required owner decisions

1. **The bounded M3.3 contract**, with exact authorized paths, covering M3.3A and M3.3B.
2. **Authorization to proceed from M3.3A to M3.3B**, after the M3.3A independent review — separate
   from 1, and not implied by the builder working.
3. **A governance record for the candidate-snapshot builder** if its construction would fix any
   identity, mapping, or classification not already frozen by Decisions 013, 014, 016, or 019.
4. **A ruling on Decision 023 O1** if the M3.3A rehearsal or the real M3.3B run reaches an empty
   sole-carrier crosswalk family.
5. **A ruling on any infeasibility** — if the real candidate universe cannot satisfy the frozen
   design, M3.3B **fails closed** and reports the binding constraints; it does not relax a quota.

The owner decision on the root is **not** taken in this phase.

### 6. Prerequisites

- `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED` recorded; independent M3.2 review passed;
  `m3.2-complete` created.
- A bounded M3.3 contract, accepted, with exact paths and **network authorization `NONE`**.
- **Transport disabled again**, verified before snapshot construction begins.
- Gate H complete, every item `PASS`, owner-signed, integrating both M3.2 windows.
- The acquired raw-object set complete, verified, and fully provenanced.
- Catalog at migration `0013`, integrity and foreign-key checks passing.
- **M3.3B additionally requires:** the candidate-snapshot builder implemented; the M3.3A execution
  rehearsal passed across E1–E8; the M3.3A independent review passed; and explicit owner
  authorization to freeze a real candidate snapshot.

### 7. Exact inputs

Gate H acceptance; the exact acquired raw-object set; immutable provenance; the accepted
source-policy versions (`M22_SOURCE_REGISTRY_VERSION`, parser versions); the accepted quota policy
(`PILOT_QUOTA_POLICY_VERSION`); the accepted selector policy
(`PILOT_JOINT_SELECTOR_POLICY_VERSION`) and the replacement-signature policy; the manifest hash
policy (`PILOT_MANIFEST_HASH_POLICY_VERSION`); `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION`; the frozen
bootstrap seed `20260725`; the frozen cohort rules and the Decision 010 date-source rule; the leakage
controls; the accepted S4, S5, and S6 identities and their accepted limitations; and the six
Decision 021 §8.4 explicit arguments — dependency-lock hash, code-commit identifier, Python runtime
version, configuration hash, decision-authority hash, and source-plan hash — **supplied explicitly and
never inferred** from Git, the environment, the interpreter, or the working tree.

### 8. Exact outputs

**M3.3A:** the implemented candidate-snapshot builder and its tests; a passing execution rehearsal
across E1–E8; the per-scenario recorded reason codes, persisted state, files, receipts, rollback,
recovery, and validation; the M3.3A independent-review result.

**M3.3B:** the frozen real candidate snapshot and its `snapshot_id`; the candidate-table identities;
the selected entities; the selected accessions; roles; reserves; dispositions; the quota report; a
**feasible** persisted S5 run; the reconstructed S5 result; the replay proof; the terminal
`selection_result_sha256`; the exact eight S6 component digests; `root_manifest_sha256`;
`manifest_id`; the canonical serialized manifest document under the content-derived filename; the
verification result; the write-free replay result; the CLI output deferred from S6; the
[`real_snapshot_evidence_packet.md`](../Docs/m3/templates/real_snapshot_evidence_packet.md); the
limitations-register update; and one execution receipt per command.

**The completed evidence packet, the manifest document, and every governed identity are private
evidence** (§12). The public repository records only the packet's type, phase, status, SHA-256, and
reference identifier in the evidence index — **never the root, and never a substantive row**.

### 9. Authorized future path categories

- A new candidate-snapshot builder module and its tests (**M3.3A**).
- A new execution-rehearsal harness for E1–E8 and its fixtures (**M3.3A**).
- A new or extended CLI subcommand delivering the deferred S6 output, with its tests.
- Receipt emission for M3.3 commands.
- `Docs/m3/` evidence records; `Docs/sec_data_dictionary.md` in the same pass if schema is
  introduced.
- `Milestones/STATUS.md` and navigation aids, under explicit instruction only.

### 10. Prohibited path categories

`release/pilot_manifest.py`, `sec/pilot_manifest_store.py`, `sec/accession_selector.py`,
`sec/accession_selection_store.py`, `sec/reserve_selector.py`, `sec/entity_selector.py`,
`sec/entity_selection_store.py` — **reused, never edited**; `cohorts.py`; `pilot_policy.py`;
`reasons.py`; `release/hashing.py`; migrations `0001`–`0013`; `Docs/preregistration.md`; Decisions
001–028; every completed contract; and any transport, HTTP, or socket path.

### 11. Network permission

**OFF.** Transport is disabled again **before** snapshot construction begins, and the phase verifies
this rather than assuming it. Any network access in M3.3 is a stop condition.

### 12. Permitted SEC routes or source classes

**None.** M3.3 reads the raw store and the catalog. It contacts nothing.

### 13. Prohibited SEC routes or source classes

**All of them**, without exception, plus every prohibition in M3.2 §13.

### 14. Expected request volume

**Exactly 0.** Any non-zero count is a phase failure.

### 15. Request-volume formula

Not applicable — the phase issues no request. `planned = 0`, `maximum = 0`, `actual` must equal `0`.

### 16. Hard request ceiling

**`0`.**

### 17. Stop conditions

Stop and report on any of:

1. any network access;
2. **M3.3B beginning before M3.3A has passed its independent review**;
3. any execution-rehearsal scenario E1–E8 failing, or being unimplemented, skipped, or `xfail`ed;
4. snapshot-freeze validation failing any Decision 019 §9 obligation;
5. stored identity corruption detected during reconstruction;
6. the reconstructed result disagreeing with the persisted result on any field;
7. replay performing any write;
8. re-serialization not being byte-identical;
9. any digest not recomputing from persisted rows;
10. any of the seven Decision 021 §11.2 eligibility conditions failing;
11. an empty sole-carrier crosswalk family (**O1** — refer, never resolve);
12. infeasibility of the frozen design against the real candidate universe;
13. any attempt to use the S4 draft as an input, or to mutate, delete, or promote it;
14. any operational value reaching a governed identity;
15. a manifest state beyond `proposed` being written, or any approval or publication field being set;
16. any reserve substitution, discretionary trimming, or second selector appearing.

### 18. Retry and response-policy boundary

**Not applicable to the network** — nothing is retried because nothing is requested. Internally,
**no automatic retry of a selection is authorized** (Decision 018 §18): a failed run is recorded and
referred, never silently re-attempted.

### 19. Schema-drift boundary

Drift in the *acquired* data is an M3.2 concern, already closed at Gate H. In M3.3, a stored payload
that no longer matches its expected shape, or a catalog row that fails its structural expectation, is
**blocking**: stop, preserve, record, and refer. The structural fingerprint's cross-run equality
requirement fails closed on disagreement, and `parser_run_id` stays excluded from identity.

### 20. Leakage controls

- **L01, L03, L13** — every candidate attribute is derived only from metadata available at the
  frozen as-of; nothing later is used.
- **L02, L05** — every accession is retained separately, amendments are explicitly linked, and
  filing date, fiscal period end, fiscal year, and form are kept distinct.
- **L04, L10** — delisted and inactive registrants are retained, and exclusion counts by reason are
  reported in the manifest's reconstruction block.
- **L15, L19; Decision 015** — pilot membership and stratification inform nothing outside the pilot.
- **Decision 002** — the eight primary-universe-ineligible pilot entities are engineering-only and
  never enter primary outcome construction.
- The `leakage_attestation` literal is recorded, and the evidence packet names the exact read set
  that makes it true.

### 21. Provenance requirements

The manifest's source-provenance block carries, for every source snapshot: source ID; source URL
identity or approved source key; source-observation ID; retrieval-attempt ID; retrieved-at UTC; HTTP
validator metadata; transport hash; decoded-content hash; stored-object hash; relative storage path;
parser version; parser status; schema fingerprint; and supersession lineage. Every entity and
accession record carries its full lineage per milestone-plan §10. **Relative paths only — never an
absolute or personal path.**

### 22. Execution-receipt requirements

One receipt per M3.3 command, with `invocation_mode = "offline_execution"`, zero request counts, and
the resulting `snapshot_id`, `selection_run_id`, `selection_result_sha256`, `root_manifest_sha256`,
and `manifest_id` **recorded as references**. Recording an identity in a receipt is not the same as
the identity committing the receipt: the direction is one-way, and **the receipt is never an input to
any digest**.

### 23. Validation requirements

Full reconstruction and replay proofs over the real data; byte-identical re-serialization; every one
of the eight component digests, `selection_result_sha256`, `root_manifest_sha256`, and `manifest_id`
recomputed **from persisted rows** rather than from memory; all 81 crosswalk items bound and asserted
item by item at the frozen totals (42 direct / 30 transitive / 8 operationally excluded / 1 deferred
to S9 — **delivered here** / 0 deferred to S10 / 0 unclassified); reserve coverage complete per item
70; item-46 applicability per Decision 022; exactly one `proposed` manifest row, written atomically
with its document; public verification passing and failing closed on wrong bytes.

### 24. Offline tests

Candidate-snapshot builder tests against synthetic and real-shaped fixtures; snapshot-freeze
validation tests for every Decision 019 §9 obligation; reconstruction-mismatch fail-closed tests;
replay write-free tests; manifest-write fault and manifest-file-loss tests; CLI output tests
asserting **no personal path and no SEC identity** in the rendered command-invocation field; and the
unchanged S4, S5, and S6 regression suites.

### 25. Full phase-end validation

`ruff check .`; `ruff format --check .`; `mypy src`; `pytest`; `make sqlite-check`; `make secrets`;
`make hygiene`; `make context` — all green — plus `tests/unit/test_migration_provenance.py`, the
catalog integrity report, the manifest verification result, and the write-free replay result.

### 26. Independent-review requirement

**Two required reviews, both consequential, both by a session that constructed none of the artifacts.**

- **After M3.3A**, before any real freeze. Its question: *does the builder satisfy every Decision 019
  §9 obligation, and does the execution rehearsal actually exercise the production paths — not
  stubs — across E1–E8 including O1 behaviour?*
- **After M3.3B.** Its question: *does every identity recompute from persisted rows, does replay
  write nothing, is every crosswalk item bound, and is the root an output rather than an approval?*

### 27. Rollback procedure

A failed manifest write leaves **no** row and **no** new file (accepted S6 atomicity, with limitation
**O3**: a pre-existing artifact at the content-derived path is outside the transaction's ownership).
A failed selection leaves the run in its recorded failed state — **it is not deleted**, and no
automatic retry occurs. The snapshot, once frozen, is **immutable**: a wrong snapshot is superseded by
a new one under explicit authorization, never edited. **Nothing acquired in M3.2 is touched.**

### 28. Recovery procedure

Use
[`Docs/m3/templates/interrupted_run_recovery.md`](../Docs/m3/templates/interrupted_run_recovery.md).
The accepted lifecycle guards make the safe states enumerable: a run is inserted only unsealed, can
never be replaced or deleted, cannot have `selection_run_id`, `snapshot_id`, or
`selection_input_sha256` changed, seals only through the guarded update on an already-`feasible` run,
and cannot have that seal changed or cleared — so recovery determines **which** of those states the
catalog is in and resumes from it, or stops. Identical restatement is idempotent; anything else is a
stop condition.

### 29. Idempotency or replay expectations

Two clean rebuilds from the same frozen candidate snapshot must produce **identical** entity
selections, accession selections, reserve ordering, quota results, and root manifest hash
(milestone-plan §14 item 13). Replay is **write-free**: it reads, reconstructs, compares, and returns.
An identical re-seal is idempotent; a differing seal is refused.

### 30. Required evidence packet

**Private evidence** (§12); only its type, phase, status, SHA-256, and reference identifier appear in
the public evidence index.

The M3.3A execution-rehearsal record across E1–E8, with its independent-review result; and
[`Docs/m3/templates/real_snapshot_evidence_packet.md`](../Docs/m3/templates/real_snapshot_evidence_packet.md),
completed: the source-observation set; provenance; snapshot identity; candidate-table identities;
policy versions; cohort definitions; the leakage attestation; the selection result; reserves;
dispositions; reconstruction; replay; manifest identities; limitations; **and the explicit
no-approval statement.** Plus every execution receipt from the phase.

### 31. Completion token

```
M3_3_REAL_PILOT_MANIFEST_CONSTRUCTED_READY_FOR_ROOT_APPROVAL
```

### 32. Implementation commit policy

**One implementation commit per part**, by default — M3.3A's builder and rehearsal harness, then
M3.3B's execution work. The M3.3A/M3.3B boundary is an **explicitly justified** checkpoint, because
an independent review sits between them and a review needs a committed state to review; it is still
taken only if the owner separately authorizes it. **No data, database, raw object, manifest artifact,
release file, or completed evidence packet is committed.**

### 33. Governance acceptance-commit policy

M3.3 acceptance is recorded in a separate bounded governance commit with its status and navigation
updates, changing no implementation byte.

### 34. Annotated tag policy

**`m3.3-complete`**, annotated, only after independent M3.3 acceptance. **A tag here records that the
manifest was constructed and reviewed — it records no approval.**

### 35. Next authorized action

On success: record `M3_3_REAL_PILOT_MANIFEST_CONSTRUCTED_READY_FOR_ROOT_APPROVAL`, then
`INDEPENDENT_M3_3_ACCEPTANCE_REVIEW`, then — separately — owner authorization to prepare the M3.4
root-hash approval packet.

### 36. Conditions preventing progression

M3.4 may not begin while any of these holds: the M3.3A rehearsal has not passed; the M3.3A review has
not passed; any identity fails to recompute from persisted rows; the re-serialization is not
byte-identical; replay performed a write; any crosswalk item is unbound; the run is not
manifest-eligible; O1 is reached and unruled; the design is infeasible against the real universe; any
operational value reached a governed identity; the evidence packet is incomplete; or the independent
M3.3B review has not passed.

---

# Phase M3.4 — Accepted approval path and the exact root-hash decision

Planned in two sequential internal parts: **M3.4A** builds and independently validates the
approval-recording entry point against synthetic catalogs; **M3.4B** presents the exact real root and
invokes that accepted entry point once.

**M3.4 always requires a bounded contract. It is never purely documentary.**

### 1. Objective

Obtain an **explicit, exact-hash-specific, owner-recorded** approval of the precise
`root_manifest_sha256` produced by M3.3B — and record it through an **accepted, tested application
entry point**, in a way that no later session can widen, infer, or transfer.

### 2. Exact scope

**M3.4A — approval entry point.** Implement a **minimal approval-recording application entry point**
under this phase's bounded contract, and validate it **independently against synthetic catalogs**: it
must refuse a mismatched root, refuse a second differing approval, hold the six manifest identity
fields immutable, and be incapable of writing `approved_root_sha256` unequal to
`root_manifest_sha256`.

**M3.4B — the exact-root decision.** Assemble the root-hash approval packet. Re-derive the presented
root from persisted state **at the moment of approval**. Present the packet to the owner. Record the
owner's explicit decision — approval or rejection. On approval, invoke the accepted entry point
**once** to persist `approved_root_sha256 = root_manifest_sha256` under the accepted schema's
equality check. Retain the evidence.

### 3. Explicit non-scope

**No publication** — approval is not publication authority. No regeneration of the root to obtain a
convenient value. No partial, implied, conditional, or retroactive approval. No manifest edit. No
selection change. No new snapshot. No network. No outcome analysis.

**No manual SQL against the real catalog, in any part, for any reason.** The only write path is the
accepted entry point. **No real root is touched in M3.4A** — it runs against synthetic catalogs
only.

### 4. Controlling decisions

Decision 024 §§5.1, 5.2 (the S10 row), 8; Decision 027 §§10, 19;
[Decision 013](../Docs/Decisions/decision_013_pilot_selection_mechanics.md) **§8 — completion requires
owner approval of the exact final manifest hash**;
[Decision 016](../Docs/Decisions/decision_016_m23_schema_and_artifact_architecture.md) §5 (manifest
lifecycle); [Decision 021](../Docs/Decisions/decision_021_m23_s6_manifest_construction.md) §9 (the
copy-not-hash rule for `approved_root_sha256`), §9.2 (six-field identity immutability), §11 (the
proposed-only boundary S6 could not cross); migration `0009`'s
`approved_root_sha256 = root_manifest_sha256` check and migration `0013`'s eight lifecycle guards.

### 5. Required owner decisions

1. **The bounded M3.4 contract.** Always required — M3.4 is never documentary.
2. **Authorization to proceed from M3.4A to M3.4B**, after the entry point is independently validated
   against synthetic catalogs.
3. **The approval decision itself** — the phase's entire purpose.

### 6. Prerequisites

- `M3_3_REAL_PILOT_MANIFEST_CONSTRUCTED_READY_FOR_ROOT_APPROVAL` recorded; independent M3.3 review
  passed; `m3.3-complete` created.
- The real-snapshot evidence packet complete, including its explicit no-approval statement.
- The manifest in state `proposed`, verified, with every identity recomputing from persisted rows.
- The limitations register current, with every unresolved warning listed.
- Network verified disabled.
- **M3.4B additionally requires:** the approval-recording entry point implemented, independently
  validated against synthetic catalogs, and accepted.

### 7. Exact inputs

The exact `root_manifest_sha256`; the exact `manifest_id`; the exact `selection_result_sha256`; the
eight component digests; the snapshot identity; the policy versions; the cohort definitions; the
request-plan identity; the acquisition evidence; the Gate F result; the Gate H result; the
reconstruction result; the replay result; the verification result; the limitations register; the
unresolved warnings; and the publication status.

### 8. Exact outputs

**M3.4A:** the implemented approval-recording entry point, its tests against synthetic catalogs, and
its independent-validation result.

**M3.4B:** the completed
[`Docs/m3/templates/root_hash_approval_packet.md`](../Docs/m3/templates/root_hash_approval_packet.md);
the owner's explicit recorded decision; on approval, the **single** governed write through the
accepted entry point persisting `approved_root_sha256` equal to `root_manifest_sha256`, and the
manifest state transition the accepted lifecycle permits; the retained evidence; and the token.

**The approval packet is private evidence** (§12) and **contains the unpublished exact root**. Only
its type, phase, status, SHA-256, and reference identifier are recorded publicly. **The root itself is
never written into the repository.**

### 9. Authorized future path categories

- A **minimal approval-recording application entry point** and its tests (**M3.4A**). Always created;
  the phase is never documentary.
- `Docs/m3/` evidence records and the approval decision record under `Docs/Decisions/`.
- `Milestones/STATUS.md` and navigation aids, under explicit instruction only.

### 10. Prohibited path categories

Everything that could alter what is being approved: `release/pilot_manifest.py`;
`sec/pilot_manifest_store.py`; every selector and store module; every migration; `cohorts.py`;
`pilot_policy.py`; `Docs/preregistration.md`; Decisions 001–028; every completed contract; and any
publication or release path.

**Any ad-hoc SQL client, script, or console session against the real catalog is a prohibited path.**

### 11. Network permission

**NONE.**

### 12. Permitted SEC routes or source classes

**None.**

### 13. Prohibited SEC routes or source classes

**All.**

### 14. Expected request volume

**Exactly 0.**

### 15. Request-volume formula

Not applicable. `planned = 0`, `maximum = 0`, `actual` must equal `0`.

### 16. Hard request ceiling

**`0`.**

### 17. Stop conditions

Stop and report on any of:

1. the presented root **not** re-deriving from persisted state at the moment of approval;
2. any governed byte or governed row having changed since the packet was assembled;
3. `manifest_id`, `manifest_schema_version`, `ordinal_version`, `supersedes_manifest_id`,
   `root_manifest_sha256`, or `selection_result_sha256` differing from the packet;
4. any attempt to approve a root other than the exact presented value;
5. any attempt to regenerate the root in order to obtain a different value;
6. any suggestion that approval is implied, partial, conditional, or inferable;
7. an unresolved warning the packet does not disclose;
8. any publication step being proposed as part of approval.

### 18. Retry and response-policy boundary

Not applicable — no request, and **no retry of an approval**. A rejected root is not re-presented
unchanged; it is corrected under §"Rejection handling" below and re-presented as a **new** exact root.

### 19. Schema-drift boundary

Not applicable to acquisition. At the schema layer, migration `0009`'s equality check and migration
`0013`'s guards are the enforcement: `approved_root_sha256` may only equal `root_manifest_sha256`, the
six manifest identity fields are immutable after insertion, and neither the manifest row nor the
selection run can be replaced or deleted.

### 20. Leakage controls

The approval packet contains **identities and evidence references**, never substantive payload: no
filing text, no outcome value, no candidate or selected row content beyond what the manifest already
commits, no secret, no full SEC identity, and no absolute personal path. **Approval creates no
research artifact and informs no feature, threshold, vocabulary, transform, or model choice**
(Decision 015; L15, L19).

### 21. Provenance requirements

The packet cites, for every claim, the persisted artifact that proves it: the row, the digest, the
receipt, or the evidence packet section. **A claim with no citation is not evidence.**

### 22. Execution-receipt requirements

If any command runs — re-derivation, verification, or approval recording — it emits a receipt with
`invocation_mode = "approval"`, zero request counts, and the referenced identities. **The receipt is
not the approval**; the owner's recorded decision is. The receipt records that a command ran.

### 23. Validation requirements

The root re-derives from persisted rows **at the moment of approval**, not from the packet; the
manifest verifies; `manifest_id` recomputes; the component digests recompute; the accepted lifecycle
accepts the transition; the schema's equality check holds; and **the write occurs through the accepted
entry point, exactly once, with no manual SQL anywhere in the phase**.

### 24. Offline tests

**Required, against synthetic catalogs, before M3.4B:** a mismatched root is refused; a second,
different approval is refused; an identical re-derived root is handled per §29 without producing a
second, different approval; the six identity fields remain immutable; and **no path can write
`approved_root_sha256` unequal to `root_manifest_sha256`**.

### 25. Full phase-end validation

`ruff check .`; `ruff format --check .`; `mypy src`; `pytest`; `make sqlite-check`; `make secrets`;
`make hygiene`; `make context` — all green — plus the re-derivation proof and the completed approval
packet.

### 26. Independent-review requirement

**Two required reviews.** The **M3.4A entry point is independently validated against synthetic
catalogs** before it may touch a real root. **Packet preparation is Opus Max work** — assembling and
checking the packet before it reaches the owner. The **approval itself is the owner's act and is not
delegated, reviewed away, or performed by a model.** A separate independent review of the approval
record occurs at M3.5.

### 27. Rollback procedure

**An approval, once recorded, is not rolled back** — it is superseded by a later recorded decision
that names what it supersedes. If a packet is found defective **before** approval, the packet is
withdrawn and re-assembled. If a defect is found **after** approval, it is recorded as a new finding
and referred; the record of what was approved stands.

### 28. Recovery procedure

An interrupted approval is resumed only after re-deriving the root and re-verifying the manifest from
persisted state. **A partially recorded approval is not an approval.** If it cannot be determined
whether the approval was recorded, the phase stops and the state is inspected **through the accepted
entry point's read path**, never by ad-hoc SQL.

### 29. Idempotency or replay expectations

Re-running the re-derivation and verification is **write-free** and must reproduce the same
identities — that is the determinism, not a coincidence. Recording the same approval twice is either
idempotent under the accepted guards or refused; **it never produces a second, different approval.**

**An identical root re-derived from unchanged governed state is the same approved value**, not a new
one requiring re-approval.

### 30. Required evidence packet

[`Docs/m3/templates/root_hash_approval_packet.md`](../Docs/m3/templates/root_hash_approval_packet.md),
completed and owner-signed, containing the exact root, the exact manifest ID, the exact selection
result hash, the component digest table, the evidence references, the limitations, the owner decision,
the exact-hash-only clause, the reapproval condition, and the publication prohibition unless
separately authorized.

**Approval semantics, stated exactly.** Approval is: **explicit**; **owner-recorded**; **exact-hash
specific**; **non-inferable from silence**; **non-inferable from code having run**; and **invalidated
by any change to governed state that changes the root**.

**Deterministic re-derivation, frozen.** This replaces the v0.1 claim that any regeneration
necessarily creates a new root, which was false and contradicted the determinism the manifest exists
to provide:

1. **Unchanged governed state plus byte-identical canonical serialization produces the same
   `root_manifest_sha256`.**
2. **An independently re-derived identical root remains the same approved value.** Re-deriving does
   not invalidate the approval and requires no new packet.
3. **A differing root, changed governed state, or a superseding manifest requires a new packet and a
   new explicit owner decision.**

The distinction is between *regenerated* and *different*. Only the latter invalidates an approval.

**Mismatch handling.** If the presented root does not re-derive **to the same value**, **stop**. Do
not approve, do not adjust the packet to match the derived value, and do not recompute in search of
a convenient one. Record the mismatch, refer it, and treat it as an M3.3 finding.

**Rejection handling.** A rejection is recorded with its reason. The manifest stays `proposed`. The
correction is made under a new bounded authorization, and — because the correction changes governed
state — the result is a **new, different** exact root requiring its own packet.

**Reapproval requirements.** Reapproval is required only when the root **differs**. It requires the
full packet again — re-derivation, re-verification, current limitations, and a fresh explicit owner
decision naming the new exact hash.

**Evidence retention.** Every packet, approved or rejected, is retained permanently **in the private
evidence root** (§12), with a separate owner-controlled backup, and is never edited after the
decision; a correction is a new dated entry. Only its digest and non-sensitive metadata reach the
public evidence index.

**Approved-root persistence.** Inherited from the accepted schema: `approved_root_sha256` may only be
written equal to `root_manifest_sha256` (migration `0009`'s check); the six manifest identity fields
are immutable after insertion; the manifest row cannot be replaced or deleted; and the selection run
cannot be replaced, deleted, or re-identified (migration `0013` triggers 3–8).

### 31. Completion token

```
M3_4_EXACT_ROOT_OWNER_APPROVED_READY_FOR_INTEGRATED_ACCEPTANCE
```

### 32. Implementation commit policy

**One implementation commit for M3.4A**, carrying the approval-recording entry point and its
synthetic-catalog tests. **M3.4B adds no implementation commit** — it invokes the accepted entry
point and records a decision. The phase is **never** documentary, so there is always at least the
M3.4A commit.

### 33. Governance acceptance-commit policy

**One bounded governance commit** carrying the approval decision record — which references the
completed packet only by its SHA-256 and non-sensitive reference identifier, never the root — the
public evidence-index update, and the status and navigation updates. **The completed packet is
retained in the private evidence root (§12) and is never committed.**

### 34. Annotated tag policy

**`m3.4-complete`**, annotated, only after the approval is recorded and independently confirmed.
**The tag marks that an approval exists — it is not itself the approval.**

### 35. Next authorized action

On approval: record `M3_4_EXACT_ROOT_OWNER_APPROVED_READY_FOR_INTEGRATED_ACCEPTANCE`, then —
separately — owner authorization to begin M3.5 integrated acceptance.

### 36. Conditions preventing progression

M3.5 may not begin while any of these holds: no explicit owner decision is recorded; the recorded
decision does not name the exact hash; the root does not re-derive; a governed byte or row changed
after approval; the packet is incomplete; an undisclosed unresolved warning exists; or approval is
claimed by inference rather than by record.

---

# Phase M3.5 — Integrated real-pilot acceptance and the Milestone 3 checkpoint

### 1. Objective

Review the whole of Milestone 3 together — readiness, acquisition, construction, and approval — and
decide whether Milestone 3 is accepted, while keeping **implementation acceptance**, **real-data
execution acceptance**, **exact-root approval**, **publication eligibility**, and **future
outcome-analysis authority** as five separate findings.

### 2. Exact scope

Integrate and re-verify: Gate F; the M3.1A **acquisition** rehearsal; the zero-request dry runs; the
Decision 028's M3-L12 ruling and its accepted planner-v2 implementation; **both** M3.2 windows, each against its own plan, budget,
ceiling, and owner approval; the between-windows freeze and derivation; Gate H; raw-store provenance;
schema drift; the M3.3A **execution** rehearsal; the snapshot freeze; S5 selection; reserves and
dispositions; reconstruction; replay; selection-result sealing; the S6 manifest; root identity; the
M3.4A entry point and its synthetic-catalog validation; the exact owner approval and the single
governed write; limitations; leakage; reproducibility; the operator workflow; execution receipts; the
**public evidence index against the private evidence root**; recovery evidence; and Git and tag
state. Produce the integrated acceptance result and, on acceptance, the Milestone 3 closeout record
and checkpoint.

### 3. Explicit non-scope

**No publication.** **No outcome analysis.** No new acquisition, snapshot, selection, or manifest. No
approval of a different root. No relaxation of any accepted limitation. **Acceptance authorizes
nothing beyond Milestone 3.**

### 4. Controlling decisions

Decision 024 §§5.1, 5.2 (the M3.5 row), 8; Decision 026 §§12, 21; Decision 027;
the independence discipline of [Decision 022](../Docs/Decisions/decision_022_m23_s6_reserve_rank_applicability.md)
§9 and [Decision 023](../Docs/Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md) §2;
[Decision 001](../Docs/Decisions/decision_001_novelty_boundary.md) (the final literature refresh
before publication); [Decision 006](../Docs/Decisions/decision_006_final_contribution.md) (the
prohibited-claims list); [Decision 015](../Docs/Decisions/decision_015_pilot_use_prohibition.md).

### 5. Required owner decisions

1. **Acceptance of the integrated Milestone 3 result.**
2. **Separately: any publication authority** — which acceptance does not create.
3. **Separately: any future outcome-analysis authority** — which acceptance does not create.
4. **Authorization of the closeout commit and the `m3-complete` tag.**

### 6. Prerequisites

- `M3_4_EXACT_ROOT_OWNER_APPROVED_READY_FOR_INTEGRATED_ACCEPTANCE` recorded.
- All four prior phases accepted, with `m3.1-complete`, `m3.2-complete`, `m3.3-complete`, and
  `m3.4-complete` created.
- Every evidence packet complete, owner-signed where required, and retained.
- The limitations register current.
- Clean tree, `HEAD == origin/main`, live baseline re-verified.

### 7. Exact inputs

Every evidence packet; every execution receipt; the Gate F and Gate H checklists; the request budget
and the reconciled accounting; the rehearsal record; the recovery records; the real-snapshot evidence
packet; the root-hash approval packet; the limitations register; the raw store and the catalog; the
Git history and the tag set.

### 8. Exact outputs

The integrated acceptance review result; the five distinguished findings (§2 of this phase's
objective); the updated limitations register; the Milestone 3 closeout decision record; the token; the
checkpoint commit and the `m3-complete` tag on acceptance.

### 9. Authorized future path categories

- A Milestone 3 closeout decision record under `Docs/Decisions/`.
- `Docs/m3/` final evidence records and the limitations-register update.
- `Milestones/STATUS.md`, `Milestones/contracts/README.md`, `Docs/architecture_map.md`,
  `Docs/change_impact_map.md`, `Docs/decision_index.md`, `Docs/Decisions/decision_registry.md`,
  `README.md` — under explicit instruction only.
- **Bounded correction paths only if a separate correction contract authorizes them.**

### 10. Prohibited path categories

Every production module, test, migration, configuration file, and CI workflow — **unless a separate
bounded correction contract authorizes a specific path**; `Docs/preregistration.md`; every earlier
decision record; every completed contract; and every publication or release path.

### 11. Network permission

**NONE**, unless an explicit bounded correction contract separately authorizes otherwise — in which
case that contract carries its own budget, ceiling, allowlist, and Gate F/Gate H obligations, and
this phase does not inherit M3.2's.

### 12. Permitted SEC routes or source classes

**None**, subject to the same correction-contract exception.

### 13. Prohibited SEC routes or source classes

**All.**

### 14. Expected request volume

**Exactly 0**, unless a correction contract authorizes a bounded, separately approved number.

### 15. Request-volume formula

Not applicable. `planned = 0`, `maximum = 0`, `actual` must equal `0` absent a correction contract.

### 16. Hard request ceiling

**`0`**, absent a correction contract that sets and has approved its own.

### 17. Stop conditions

Stop and report on any of:

1. an evidence packet missing, incomplete, or unsigned where a signature is required;
2. an execution receipt missing for a live command;
3. **a completed evidence artifact found tracked in the public repository**, or an index entry whose
   digest does not match the private artifact it names;
4. a Gate F or Gate H item not `PASS`;
5. an identity that does not reproduce at review time;
6. an approval that is not exact-hash specific;
7. a limitation silently closed;
8. a leakage control unproven;
9. Git or tag state disagreeing with the record;
10. a reviewer who wrote the work being asked to review it;
11. publication or outcome analysis being proposed as part of acceptance.

### 18. Retry and response-policy boundary

Not applicable absent a correction contract. A failed acceptance is **not retried** — it produces
findings, which are corrected under a bounded contract and then re-reviewed by a fresh session.

### 19. Schema-drift boundary

Not applicable to acquisition. Any schema difference found at review between the recorded and the
actual catalog is a **finding**, resolved by correction and re-review, never by amending the record.

### 20. Leakage controls

The full register L01–L19 is re-verified as a review dimension, with particular attention to L15 and
L19 and the Decision 015 prohibition: acceptance must confirm that **no pilot artifact has informed
any research choice** and that no outcome value has been read anywhere in Milestone 3.

### 21. Provenance requirements

Every accepted claim traces to a persisted artifact. The review reproduces identities from persisted
rows rather than reading them from a document, exactly as the Milestones 1–2 integrated audit did.

### 22. Execution-receipt requirements

The review **consumes** receipts; it produces none of its own beyond any commands it runs. It must
confirm: one receipt per live command; **exactly one receipt integrity identity** (`receipt_id`), with
no second digest; **zero actual network counts in every `rehearsal` and `dry_run` receipt**; every
field correctly classified as required, conditionally required, or prohibited for its mode; no
prohibited field in any receipt; every recovery chain complete through its predecessor references;
and **no receipt appearing in any governed identity**.

### 23. Validation requirements

Every dimension in §2 of this phase's scope, reviewed together and independently reproduced where
reproducible. The five findings are recorded separately and are never merged:

| Finding | What it means | What it does **not** mean |
|---|---|---|
| **Implementation acceptance** | The Milestone 3 code is correct, tested, and accepted | Not that it was run on real data |
| **Real-data execution acceptance** | The live run stayed inside every boundary and produced complete, provenanced evidence | Not that its output is approved |
| **Exact-root approval** | The owner explicitly approved that exact root | Not that anything may be published |
| **Publication eligibility** | Recorded as a separate status, and **`NOT_AUTHORIZED`** unless a separate record grants it | Never implied by acceptance |
| **Future outcome-analysis authority** | Recorded as a separate status, and **`NOT_AUTHORIZED`** unless a separate record grants it | Never implied by acceptance |

### 24. Offline tests

The full suite, unchanged, plus any tests a bounded correction contract adds. **The review adds no
test of its own to the repository** unless it is correcting a proven gap under authorization.

### 25. Full phase-end validation

`ruff check .`; `ruff format --check .`; `mypy src`; `pytest`; `make sqlite-check`; `make secrets`;
`make hygiene`; `make context` — all green — plus the documentation and governance consistency checks
and the Git and tag state verification.

### 26. Independent-review requirement

**This phase is the review.** It is performed at Opus Max effort by a session that wrote none of the
Milestone 3 work it reviews. Where corrections are required, a **fresh** session re-reviews them —
the same discipline Decisions 022 §9, 023 §2, 025 §8, and 026 §3 established.

### 27. Rollback procedure

An unaccepted result produces findings, a bounded correction contract, corrections, and a fresh
re-review. **No acquired data, raw object, snapshot, selection, manifest, or approval is deleted or
rewritten by a failed acceptance.**

### 28. Recovery procedure

An interrupted review resumes from its recorded findings; it does not restart from zero. **A partial
review is never reported as an acceptance**, and no earlier review's recommendation is inherited.

### 29. Idempotency or replay expectations

Every identity the review reproduces must reproduce **identically** on any later day from the same
persisted state. That reproducibility is itself one of the acceptance criteria.

### 30. Required evidence packet

The integrated acceptance record, naming: every input reviewed; every dimension's classification; the
five distinguished findings; every unresolved limitation and its status; the exact Git and tag state;
and the recommendation. On acceptance, the Milestone 3 closeout decision record carries it.

### 31. Completion token

```
M3_5_REAL_PILOT_ACCEPTED_MILESTONE_3_COMPLETE
```

### 32. Implementation commit policy

**None by default** — M3.5 is a review. Any correction is a separate bounded implementation commit
under a separate correction contract.

### 33. Governance acceptance-commit policy

**One bounded governance commit** carrying the Milestone 3 closeout decision record and its status
and navigation updates.

### 34. Annotated tag policy

**`m3-complete`**, annotated, created at the closeout commit **only after** acceptance passes, with
the message `Complete Milestone 3 real pilot execution`. It supplements every existing tag and moves,
replaces, or re-points none of them.

### 35. Next authorized action

On acceptance: record `M3_5_REAL_PILOT_ACCEPTED_MILESTONE_3_COMPLETE` and stop. **Any subsequent
work — publication, the Decision 001 final literature refresh, M2.5 bounded pilot ingestion, or any
outcome analysis — requires its own separate owner authorization and is not authorized by Milestone 3
acceptance.**

### 36. Conditions preventing progression

Milestone 3 is not closed while any of these holds: any dimension is unaccepted; any identity fails to
reproduce; any receipt is missing or carries a prohibited field; any limitation was silently closed;
any leakage control is unproven; Git or tag state disagrees with the record; the reviewer is not
independent; or the owner has not accepted.

---

## 15. Request-volume policy, consolidated

Restated in one place so no phase has to re-derive it.

**No integer request count may be invented, and none is frozen in this plan.** A count is produced by
the accepted planner from explicit inputs at the time the plan is produced, and approved by the owner
as an exact integer **for one window**; or it is written
`EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` and resolved by a zero-request planning run before
that window's network enablement.

**Counts are per window.** M3.2A's plan and ceiling are approved at Gate F; M3.2B's are derived from
the frozen M3.2A objects and approved separately. **Neither approval covers the other window**, and
**no contingency allowance exists** — the two-window split makes each count derived rather than
estimated.

**The request budget template distinguishes eight quantities, and never conflates them:**

| Quantity | Meaning |
|---|---|
| **Planned unique logical requests** | Distinct approved retrieval identities that window's plan intends |
| **Maximum physical attempts** | Including every retry, every redirect hop, and every controlled post-cooldown request. **Derived per route from the implemented response-policy state machine and independently tested against its worst reachable path** — never asserted from constants, and never assumed to be the sum of the retry, redirect, and cooldown bounds |
| **Expected successful responses** | Logical requests expected to end in `proceed` |
| **Expected cache hits** | Instances already satisfied in the catalog and therefore excluded before the logical-request plan is formed; reported for reconciliation and never subtracted again |
| **Expected not-modified responses** | Conditional re-validations expected to return `304`, producing no new raw object |
| **Expected governed non-success responses** | Responses expected to classify as `retry`, `retry_after`, `cooldown`, `fail`, or `quarantine` — never "errors we will look at" |
| **Maximum new raw objects** | Equal to planned unique logical requests. A `304`, duplicate body, terminal failure, or quarantine may lower the actual count, but none is assumed in the maximum |
| **Rate-limiter spacing floor** | `max(0, maximum physical attempts − 1) ÷ requests_per_second`. A minimum spacing floor, not a maximum or prediction; transfers, timeouts, `Retry-After`, and cooldowns may lengthen the run |

**Stop-before-overflow is the rule, not stop-after.** The acquisition refuses to place the attempt
that would exceed that window's ceiling, and **a ceiling is never increased during a running
window**. A complete run may finish exactly at the ceiling; equality with work remaining is a
governed ceiling stop and Gate H failure.

**The M3-L12 owner ruling is recorded in accepted Decision 028** (M3.1 §15.1): exact-quarter-end
classification is an inherited planner defect; Decision 013 stays unchanged; corrected behaviour is
`quarterly-index-instances/2.0`. **Gate F cannot pass until the contracted correction and tests are
implemented and accepted.**

---

## 16. Mandatory contents of every future Milestone 3 phase contract

**This plan creates no contract.** It fixes what each future contract must contain, in addition to the
required sections in [`contracts/README.md`](contracts/README.md):

1. **Exact baseline commit and tag**, to be re-verified live before the contract is relied on.
2. **Governing decisions**, cited by ID and section — linked, never restated as contract prose.
3. **Exact authorized paths**, enumerated.
4. **Exact prohibited paths**, stated explicitly rather than left to inference.
5. **Implementation authorization** — `YES` or `NO`, on its own line.
6. **Network authorization** — `NONE`, `ZERO LIVE REQUESTS`, or `CONTROLLED AND EXPLICITLY
   AUTHORIZED`, with the exact authorized command named.
7. **Request ceiling**, where applicable, as an exact owner-approved integer.
8. **CLI interface** — every command the phase adds or changes, with arguments, exit codes, stdout
   contract, and network scope.
9. **Storage effects** — which tables and files are written, and under what transaction.
10. **Migration effects** — the exact migration authorized, or `none`. No migration is implied.
11. **Identity effects** — which governed identities the phase produces, and the explicit statement
    that no operational value enters any of them.
12. **Test requirements** — the minimum test categories, by name.
13. **Targeted-validation commands** — the exact `make test PYTEST_ARGS=...` set for the development
    loop.
14. **Phase-end full validation** — the fixed gate sequence from §9.
15. **Nonchange proof** — the exact path set that must remain byte-identical, and how it is proven.
16. **Failure and rollback behaviour** — the concrete procedure, per §11.
17. **Commit policy** — one commit by default; any intermediate checkpoint explicitly justified.
18. **Tag policy** — the exact annotated tag name and the acceptance that must precede it.
19. **Completion report format** — the exact field list the session must print.
20. **Exact completion token.**

---

## 17. What this plan does not do

It does not implement anything. It does not create a contract. It does not enable network access,
acquire metadata, create a snapshot, run a pilot, construct a manifest, approve a root, or publish.
It changes no production code, test, migration, configuration, CI workflow, methodology, identity,
preimage, or accepted limitation.

**Planning a phase is not authorization to begin it** (Decision 024 §8; Decision 026 §21;
Decision 027 §20). Implementation authorization is `NO` for every Milestone 3 phase.
