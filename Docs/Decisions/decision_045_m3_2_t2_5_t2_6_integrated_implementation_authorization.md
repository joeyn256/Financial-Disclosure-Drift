# Decision 045 — M3.2 T2.5–T2.6 Integrated Implementation and Freeze-Candidate Authorization

**Date:** 2026-08-07
**Status:** ACCEPTED — OWNER APPROVED 2026-08-07
**Type:** Bounded governance record authorizing one combined implementation stage. **Not** a
preregistration deviation. It changes no hypothesis, cohort window, maturity gate, outcome
definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash preimage, migration
byte, implementation byte, test byte, script byte, or configuration byte — **no executable byte
changes with this record**.
**Amends:** nothing. No accepted decision is edited in place; Decisions 032–044 are byte-unchanged;
the historical T2 authorization packet is preserved byte-identical (SHA-256 `62120146…`); the
accepted M3.2 contract is not edited (SHA-256 `c526335b…`). Where this record and the historical T2
packet's argument lists disagree, **this record controls** (§4); the packet's substantive
requirements are preserved.
**Related:** Decisions 024 §8, 034, 035, 036, 037, 038, 039, 040, 041, 042, 043, 044; the T2 packet
[revision v2](../m3/m3_2_t2_implementation_authorization_packet.md); the accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md) steps 16–28 and Appendix B;
[`Docs/m3/execution_receipt_spec.md`](../m3/execution_receipt_spec.md);
[`Docs/m3/review_execution_conventions.md`](../m3/review_execution_conventions.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's authorization of Milestone 3.2 combined implementation stage **T2.5–T2.6 —
Operator Surfaces and Integrated Implementation Candidate**, its exact operator interfaces, the
M3.2 acquisition-run identity, the response-event accounting universe, its fifteen-path envelope,
its validation and mutation requirements, and the governance sequence to T3.

---

## 0. What this record is, and the two rulings it carries

This is the **first and only durable version** of Decision 045. No earlier version of this Decision
was ever written to this repository, committed, published, or accepted, and none is referenced here
as authority.

Before any recording occurred, a read-only architecture-discovery session verified the draft
instrument against the accepted code and schema and raised **two findings**, both of which the owner
reviewed and accepted as genuine defects of the unrecorded draft. The owner ruled on both on
2026-08-07 and directed that the rulings be **incorporated into this first durable version** rather
than recorded as a later corrective decision. They are carried in **§4.6, §4.7, §6A, §9, §10, §14,
§22, §23, and §28**:

| Ruling token | Substance |
|---|---|
| `BLOCKER_1_RESOLUTION: A1_APPROVED` | M3.2 shall have a **durable acquisition-run identity**, registered by the authorized M3 acquisition driver in the existing `ops_ingestion_jobs` table, with durable run→observation attribution — so `m3 show-drift --run` and `m3 recover --run` are lawful and the accepted T2.4 write-ahead recovery state is reachable in a future authorized real operation (§6A) |
| `BLOCKER_2_RESOLUTION: EXHAUSTIVE_RESPONSE_EVENT_ACCOUNTING_WITH_STATUS_ZERO_SENTINEL` | The strong receipt-accounting equality invariant is **retained**, with an exhaustively defined response-event universe, an explicit ruling for followed redirects and transport-level failures, and one receipt-local `status_code_totals["0"]` sentinel meaning "no HTTP status — transport-level failure" (§9–§11) |

**Verified facts underlying the rulings** (recorded because they bound what implementation may
lawfully do, and because the alternative would be re-derivation later):

- `census_source_observations_r3` carries **no run column** (`storage/migrations/0008_r3_durability_and_lineage.sql`).
  Durable run→observation attribution exists today only through the run-scoped relations that
  already carry both identities.
- The only `INSERT INTO ops_ingestion_jobs` in the repository is the private M2.2 registration in
  `src/disclosure_drift/sec/census_orchestrator.py`, which hardcodes `job_kind = 'sec_census'` and
  `stage = 'M2.2'`. That module is a **prohibited path** for all of T2 and its implementation is
  **not** to be reused.
- `src/disclosure_drift/sec/observation_catalog.py` exposes **no** run registrar; its accepted
  `open_recovery_state` primitive only **validates** an existing `ops_ingestion_jobs.job_id`, and
  `src/disclosure_drift/m3/acquisition.py` likewise validates and never mints (Decision 041 §7).
- `ops_ingestion_jobs` carries **no CHECK constraint** on `job_kind` or `stage`
  (`storage/migrations/0001_initial.sql`), so an M3.2 row is schema-legal and **no migration is
  required or authorized**.
- In the accepted client, a **followed redirect** records a hop and continues **without** a
  response-policy bucket, and a **transport-level failure** produces a bucket with **no HTTP
  status**, so the equality invariant required the exhaustive definition §9 now gives it.
- `status_code_totals` is a receipt `count_map` whose keys are already unconstrained strings, so the
  `"0"` sentinel needs **no receipt-schema, field, mode, vocabulary, or validator change**.

**This record authorizes implementation and offline testing only.** It authorizes no network
enablement, no SEC contact, no acquisition, no real operational catalog, no real run row, no live
receipt, and no use of the approved ceiling **801** (§19).

## 1. Baseline

| Fact | Value |
|---|---|
| Published baseline | `37866d3de8207528b42b3a207187d02404582370` |
| Branch state at recording | `main`; `HEAD == origin/main`; clean; ahead 0 / behind 0; no tag at HEAD |
| G1 | accepted, complete, and published (Decision 044) |
| T2.5 / T2.6 | **not begun** |
| Tracked network switches | `network.enabled = false`; `network.m3_acquire_enabled = false` |
| CompanyFacts | disabled |
| Migration chain | `0001`–`0013`, contiguous; **no `0014`** |
| Receipt schema | `m3-execution-receipt/2.0`, frozen |
| Operational state | no operational catalog, raw acquisition object, live receipt, request attempt, or live SEC artifact exists; ceiling **801** operationally unused |

## 2. Combined-stage ruling

**M3.2 T2.5–T2.6 SHALL PROCEED AS ONE COMBINED IMPLEMENTATION STAGE**, following accepted
[Decision 037](decision_037_m3_2_remaining_stage_combination.md) and accepted contract §22.

No separate T2.5 implementation commit, T2.5 acceptance, or T2.6 authorization is required. The
combined stage produces **one implementation-freeze candidate** for the independent T3 review.

Exact implementation commit subject:

```text
Complete M3.2 T2.5-T2.6 integrated implementation
```

The candidate **remains local and unpushed** pending T3 review. **No tag is authorized.**

## 3. Internal subphases

The combined stage shall use two internal implementation subphases. These are **implementation
checkpoints only**; they create no separate governance stage and no separate commit.

**Subphase A — offline operator surfaces.** Complete `m3 acquire --show-scope`,
`m3 derive-dependent-plan`, `m3 reconcile-requests`, `m3 show-drift`, `m3 recover`, the associated
offline receipt and report behaviour, progress-sink sanitization and exclusion, and dependent-plan
derivation with plan-identity preservation. Run the §20 targeted self-check before beginning
Subphase B. **Do not commit at the Subphase-A boundary.**

**Subphase B — live-capable wiring, still offline in execution.** Complete `m3 acquire --live`, the
single transport-construction site, the complete operator-boundary authorization conjunction, the
M3.2 acquisition-run registration and attribution of §6A, physical-attempt ceiling and resume
integration, frozen receipt-field production and assembly, integrated CLI behaviour, and final
freeze-candidate validation. **No live invocation is authorized in Subphase B.**

## 4. Exact operator interfaces

This section resolves the interface inconsistencies discovered after T2.4. **These rulings supersede
conflicting or incomplete argument lists in the historical T2 execution packet while preserving its
substantive requirements**; the packet itself is not edited and remains byte-identical.

### 4.1 `m3 acquire --show-scope`

Required operator inputs: `--config`, `--evidence-root`, `--plan`, `--window`, `--show-scope`, and
optional `--receipt-chain-head`.

It must report deterministically: allowed hosts; method `GET`; the exact route allowlist for the
requested window; the prohibited route/family set; the approved plan hash; the approved request
ceiling; and the consumed-count baseline reconstructed from the supplied receipt chain, or zero for
a fresh chain.

It must perform zero network, construct no transport, create no operational catalog, emit no
receipt, and write no artifact. Malformed or mismatched governed inputs fail closed.

### 4.2 `m3 acquire --live`

Required operator inputs: `--config`, `--evidence-root`, `--plan`, `--window`, `--live`,
`--ceiling`, `--catalog`, `--data-root`, `--receipt-out`, and optional `--resume-from`.

`--resume-from`, when supplied, must identify an **exact predecessor receipt**; it may not be
inferred from ambient state.

This is the **only** operator surface permitted to contain a live transport-construction path.
**Implementation is authorized. Execution is not.**

### 4.3 `m3 derive-dependent-plan`

Required operator inputs: `--config`, `--evidence-root`, `--from-window`, `--catalog`,
`--data-root`, `--reconciliation-set`, `--plan-out`, `--receipt-out`.

`--from-window` must be exactly `M3.2A` for this M3.2B derivation. The additional `--data-root`
requirement is authorized so frozen source-object bytes can be verified without guessing a storage
root. The explicit `--receipt-out` requirement is authorized so the mandatory dry-run receipt
location is never inferred.

The command must be structurally zero-network; refuse when either network switch indicates
transport-capable configuration; verify that required frozen source objects are present; verify
`content_sha256`; verify required provenance; reconcile against the explicit reconciliation set;
deterministically derive only the authorized dependent-route instances; write the M3.2B plan; write
**exactly one `dry_run` receipt** on successful derivation; refuse disagreement between the frozen
objects and the reconciliation set; and refuse any attempt to invent the eventual exact M3.2B
request count.

**Successful derivation does not approve the resulting M3.2B exact count or ceiling.** That remains
a separate later owner action.

### 4.4 `m3 reconcile-requests`

Required operator inputs: `--config`, `--evidence-root`, `--plan`, `--catalog`, `--data-root`,
`--report-out`.

**`--receipt` is removed from this interface.** The accepted reconciliation primitive does not
consume a receipt, and this Decision prohibits adding an unused receipt argument merely to preserve
stale packet syntax. **`--data-root` is required** because accepted reconciliation consumes a
`StorageBinding`.

The command must deterministically evaluate the plan against catalog and storage state. **Exit `0`
only when** no blocking reconciliation defect exists, **and** the required-absence enumeration is
empty, **and** any remaining divergence is plan-explained and nonblocking. Otherwise **exit `4`**
after a successfully completed evaluation. Malformed input, IO, and other ordinary failures use the
established non-integrity failure class (§5) and **must not masquerade as a clean reconciliation**.

It emits **no receipt**.

### 4.5 Private reconciliation report

`m3 reconcile-requests --report-out` is authorized to write **one deterministic private
reconciliation report**. The report must live under the supplied evidence root; must use the
accepted canonical, write-once artifact conventions; may be written after a successfully completed
reconciliation evaluation **whether that evaluation exits `0` or `4`**; must record the evaluated
reconciliation result, including the absence enumeration and the blocking/nonblocking drift
necessary to explain the exit; and must contain **no raw progress-sink exception text** (§12).

It is **private**, is **not** entered into the public evidence index, and **does not extend the
current public evidence vocabulary** — so **F4 remains a T4 obligation**.

**No real operational reconciliation report may be produced during implementation**; tests use
temporary roots only.

### 4.6 `m3 show-drift`

Required operator inputs: `--config`, `--evidence-root`, `--catalog`, `--run <census_run_id>`.

`--run` means an **existing durable `ops_ingestion_jobs.job_id`**. The interface is **retained**;
run scoping is **not** re-scoped away, and the run-identity problem is **not** deferred — it is
resolved by §6A.

For this M3.2 operator surface the supplied run must: exist in `ops_ingestion_jobs`; be an M3.2
acquisition run; carry `job_kind = 'm3_2_acquisition'`; and carry stage `M3.2A` or `M3.2B`.

The command must list and evaluate **only drift attributable through durable observation lineage to
that exact run**. **No global-drift fallback is permitted.** An unknown, non-M3.2, unattributable,
or ambiguous run identity **fails closed with exit `4`**. Blocking drift causes exit `4`; the
absence of blocking drift permits exit `0`.

It emits **no receipt**.

### 4.7 `m3 recover`

Required operator inputs: `--config`, `--evidence-root`, `--plan`, `--receipt-chain-head`,
`--catalog`, `--data-root`, `--run <census_run_id>`, `--action`, `--event`.

`--run` is **mandatory** and satisfies the Decision 041 §7 requirement that every mutating T2.4
recovery action receive an **already-registered** ingestion-job identity. The CLI wrapper must
verify that the run already exists, is a valid M3.2 acquisition run, and **was not fabricated by the
recovery command**. The command **must never fabricate, substitute, create, or infer** that run
identity.

It exposes the accepted T2.4 recovery applier, which remains **unchanged**; recovery still may not
create a run identity. It emits **no receipt**; its durable evidence remains the accepted
recovery-state and recovery-event catalog family.

## 5. Operator exit-code boundary

Preserve the existing CLI conventions while enforcing these stage-specific meanings:

| Exit | Meaning |
|---|---|
| `0` | The requested offline/operator evaluation or authorized operation completed successfully |
| `1` | Configuration, input-reading, filesystem, or other ordinary execution failure **not** classified as a governed refusal |
| `2` | CLI usage or explicitness failure, including a live acquisition invocation lacking the required explicit `--live` |
| `3` | Live operator gate unavailable or disabled, including `network.m3_acquire_enabled = false` |
| `4` | Governed fail-closed refusal: integrity failure, plan/window/ceiling mismatch, prohibited route, accounting uncertainty, blocking drift, an absence or refusal condition, an unknown governed run, or a similar accepted safety condition |

Tests must bind the important operator cases rather than rely only on prose.

## 6. Live-acquire authorization conjunction

Before the single live transport-construction site can execute, **all** required conditions must be
proven together. At minimum:

1. explicit `--live`;
2. the `network.enabled` accepted prerequisite state;
3. `network.m3_acquire_enabled`;
4. the exact approved plan hash;
5. the exact window identity;
6. the operator ceiling equal to the plan/approved ceiling **exactly**;
7. accepted contract and stage authority;
8. a valid SEC identity through the canonical identity validator.

Any required later T4/T5/T6 condition not representable as static program state remains
**externally owner-gated** and prevents real invocation. T2.5–T2.6 **may implement** this
conjunction; it **may not** satisfy the live-only governance conditions with fabricated values.

Transport construction must occur at **one auditable site only**, after all in-process preconditions
pass **and** after the §6A run registration is verified. **Every refusal path must prove that site
was never invoked.**

## 6A. M3.2 acquisition-run identity — registration and attribution

**Owner ruling `BLOCKER_1_RESOLUTION: A1_APPROVED`.** M3.2 shall have a durable acquisition-run
identity. **No migration and no prohibited-path edit is authorized to achieve it.**

### 6A.1 Run registration

For every actual `m3 acquire --live` invocation that reaches the point of lawful execution, the M3
acquisition driver in `src/disclosure_drift/m3/acquisition.py` is authorized to register **exactly
one** durable row in the **existing** `ops_ingestion_jobs` table. This is an authorized **P3
responsibility**. It is **not** authority to modify the schema, any migration file,
`sec/census_orchestrator.py`, or `sec/observation_catalog.py`.

The row must use `job_kind = 'm3_2_acquisition'` and `stage` corresponding **exactly** to the
governed acquisition window — `M3.2A` or `M3.2B`. **Do not reuse the M2.2-only registration
implementation, and do not hardcode an M2.2 job kind or stage.**

### 6A.2 Registration ordering

For a new live acquisition invocation, in this order:

1. validate CLI, configuration, and governed inputs;
2. prove the full in-process live authorization conjunction (§6);
3. validate catalog and storage prerequisites;
4. generate or allocate exactly one invocation run identity through a **test-injectable** mechanism;
5. durably register the `ops_ingestion_jobs` row;
6. verify the registration succeeded;
7. **only then** may the single transport-construction site be reached.

If run registration or its verification fails: **no transport may be constructed; no physical
request may occur; and no acquired object may be durably attributed to that failed run.**

Tests must use deterministic, injected run identities. **No real live invocation is authorized by
this Decision.**

### 6A.3 One run per live invocation

A run identifies **one live command invocation**, not an entire multi-invocation window. A resumed
invocation therefore receives a **new** run identity; its predecessor lineage remains governed by
`--resume-from`, the predecessor receipt identity, and the accepted continuation and accounting
rules (§14). **Do not silently reuse the predecessor invocation's run ID as the new invocation ID.**

### 6A.4 Run-to-observation attribution

Every source observation durably created or adopted as belonging to a live M3.2 acquisition
invocation must be **durably attributable** to that invocation's `census_run_id`. P3 may write the
**existing** accepted catalog relations that already support durable run-to-observation attribution.

This does **not** authorize a new table, a new column, a migration, a new event or reason
vocabulary, or modification of the modules that own those tables.

**Before using an existing run/observation relation, implementation must prove from the existing
schema that** it durably carries the run identity, **and** durably carries the observation identity,
**and** that its existing semantics are compatible with the M3.2 observation being attributed. **Do
not overload an unrelated relation merely because it has convenient columns.** If no existing schema
relation can lawfully represent the required run→observation attribution, **STOP** under §28 rather
than inventing one.

### 6A.5 Recovery-state usability

This ruling exists in part so the Decision 041 / T2.4 durable write-ahead recovery state is
**reachable** in a future authorized real M3.2 operation. This Decision authorizes **implementation
and fixture testing of that path only**. It does not authorize a real M3.2 run, a real operational
catalog, a real recovery state, or live acquisition.

## 7. Frozen receipt authority

The receipt schema remains exactly `m3-execution-receipt/2.0`. **No receipt schema, field, mode,
status vocabulary, or validation rule may change**, and `src/disclosure_drift/m3/receipt.py` is
**prohibited from modification**.

Only these commands emit receipts:

1. **`m3 acquire --live`** — once a live invocation has lawfully passed all pre-execution gates and
   execution has begun, it must assemble **exactly one terminal receipt** for that invocation,
   including failed, interrupted, and stopped terminal outcomes as the frozen schema requires. **A
   refusal before lawful execution begins writes no receipt.**
2. **`m3 derive-dependent-plan`** — a successful deterministic derivation writes **exactly one
   `dry_run` receipt**. A refused or invalid derivation writes **no** success receipt.

`m3 acquire --show-scope`, `m3 reconcile-requests`, `m3 show-drift`, and `m3 recover` emit **none**.

## 8. Receipt count-vocabulary bindings

Decision 040 §6 remains binding. Request-level counts:

| Condition | Frozen receipt field |
|---|---|
| Request already satisfied and excluded from future continuation | `cache_hit_count` |
| Physical lawful `304` | `not_modified_count` |
| Physical byte-identical `200` | `duplicate_object_count` |

The legacy `WindowOutcome.cache_hits` alias **must not** be used to populate the frozen receipt's
`cache_hit_count`.

**Response-policy totals.** This Decision expressly authorizes **producer-side accumulation** for
the previously missing frozen fields `response_classification_totals`, `status_code_totals`, and
`cooldown_count`. This new logic belongs inside the authorized acquisition/operator implementation
surface. **It is not a receipt-schema change.**

## 9. Exact response accounting universe

**Owner ruling `BLOCKER_2_RESOLUTION: EXHAUSTIVE_RESPONSE_EVENT_ACCOUNTING_WITH_STATUS_ZERO_SENTINEL`.**
The strong equality invariant is **retained**, and the owner expressly defines one **receipt-local
sentinel**:

```text
status_code_totals["0"]  ==  no HTTP status — transport-level failure
```

This is an **M3.2 receipt-accounting convention, not an HTTP status code**. The frozen receipt
schema remains unchanged because the existing count-map keys are already strings and no schema field
or validator shape changes.

### 9.1 Response-event universe

For receipt accounting, a **response-policy event** is exactly one of:

1. a physical HTTP response observed by the accepted transport and response-policy path; or
2. a transport-level failure that reaches accepted response-policy classification before any HTTP
   status exists.

Each response-policy event contributes **exactly one** `response_classification_totals` bucket
**and exactly one** `status_code_totals` entry. Therefore the invariant is:

```text
sum(response_classification_totals.values()) == sum(status_code_totals.values())
```

**Pre-transport refusals are not response-policy events** and contribute to neither total —
including request-ceiling refusal before transport, operator-boundary authorization refusal,
prohibited-route refusal before request, and other pre-transport construction or preflight refusals.

### 9.2 Ordinary HTTP responses

Every physical HTTP response contributes its **actual** status code exactly once to
`status_code_totals` and exactly one accepted response-policy bucket. **Do not count only the
terminal response** — intermediate physical responses are part of the response universe.

### 9.3 Followed redirects

A followed physical redirect response, including governed `301`, `302`, `307`, and `308`,
contributes one count at its **actual 3xx code** in `status_code_totals`, one **`proceed`**
response-classification bucket, and the existing redirect-hop accounting the accepted
implementation requires.

**A followed redirect must not disappear merely because transport execution continues.** Redirect-hop
counting and response-policy counting are **different metrics** and may both increment for the same
physical response.

### 9.4 Transport-level failure

A connection or transport failure that reaches accepted response-policy classification but has no
HTTP response contributes `status_code_totals["0"] += 1` and exactly one response bucket according
to the accepted response-policy result — `retry`, `retry_after`, `fail`, or another already-frozen
bucket if legitimately produced.

**Do not invent a new response-classification bucket** such as `transport_error`. `"0"` is reserved
**exclusively** for "no HTTP status — transport-level failure", and **a real HTTP response must
never be recorded under `"0"`**.

### 9.5 Producer responsibility

The additional response accounting must be produced **inside the already-authorized M3 acquisition
layer**. Do **not** modify `src/disclosure_drift/sec/http_client.py` or
`src/disclosure_drift/m3/receipt.py` merely to make receipt accounting convenient.

If the accepted `FetchResult` and transport result surfaces do not expose enough information to
account **exactly** for followed redirect status codes, the terminal status, transport failures, and
response-policy decisions within this Decision's path envelope, **STOP** rather than infer or
silently undercount.

## 10. Lawful 304 ruling

A lawful HTTP `304 Not Modified` contributes:

- `status_code_totals["304"] += 1`;
- `response_classification_totals["proceed"] += 1`;
- `not_modified_count += 1` at the request/object disposition level.

It **does not** increment `duplicate_object_count`. This ruling resolves the accepted-client
early-return ambiguity identified before T2.5–T2.6: **a 304 must not silently disappear from
response-policy totals.**

## 11. Cooldown ruling

`cooldown_count` is exactly the number of physical-response policy decisions classified into the
`cooldown` bucket:

```text
cooldown_count == response_classification_totals["cooldown"]   (zero when that bucket is absent)
```

It does **not** count arbitrary sleep calls, redirect hops, retry attempts merely because they occur
later, or elapsed cooldown seconds.

## 12. Progress-sink sanitization and exclusion

The carried Decision 040 §19 progress-sink obligation is **DUE in this stage**.

Raw operator-controlled progress-sink exception text must **never** reach a receipt field, a
reconciliation report, another written M3 artifact, or an evidence-index record. Raw exception text
may be emitted **only** to the local stderr diagnostic channel.

Any structured progress-failure state retained for later processing must contain only **bounded,
sanitized structural information** — for example an allowlisted or fixed internal reason, and the
exception class or type where safe — and **never** raw `str(exc)` content. Receipt and report
builders must not serialize raw progress-sink failure text.

**Required positive control.** A progress sink raises an exception containing at least an absolute
local path **and** an email address. Neither string may appear in any receipt or written artifact,
and the test must demonstrate **exclusion** before relying on the receipt prohibited-content
validator as a backstop.

## 13. Dependent-plan authority

T2.5–T2.6 may implement **deterministic M3.2B dependent-plan derivation only**. The command must
read accepted frozen M3.2A inputs; verify object identity, hash, and provenance; use the explicit
reconciliation set; derive **only** the two authorized dependent routes; remain zero-network; and
produce deterministic canonical output.

The sentinel exact count is resolved only by (1) a successful **real** post-M3.2A derivation over
frozen objects, and then (2) separate owner review and approval. **Implementation tests use fixtures
and do not resolve the real sentinel.**

The accepted M3.2A plan hash
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` must remain **byte-reproducible**
after any `request_plan.py` change.

## 14. Resume semantics

T2.5–T2.6 shall wire the already-accepted conservative continuation and recovery architecture.
Resume must start from an **exact predecessor receipt**; reconstruct cumulative attempt consumption;
include deterministically attributable committed post-receipt attempts; conservatively charge the
one permitted identifiable receiptless in-flight request; refuse on `UNDETERMINED` attribution;
require accepted recovery inspection to be `SAFE`; refuse while unresolved write-ahead recovery
state exists; preserve the original approved ceiling; never reset or raise consumed accounting; and
never duplicate an already-satisfied substantive write.

A resumed live invocation must **re-prove the entire current operator authorization conjunction**
(§6) and, per §6A.3, **registers its own new run identity** while carrying predecessor lineage
through `--resume-from` and the predecessor receipt identity.

## 15. Path envelope

This Decision uses the accepted T2 packet's **fifteen-path maximum**. **No sixteenth implementation
path is authorized.**

**Production and configuration paths**

| # | Path |
|---|---|
| P1 | `configs/project.yaml` |
| P2 | `src/disclosure_drift/config.py` |
| P3 | `src/disclosure_drift/m3/acquisition.py` |
| P4 | `src/disclosure_drift/cli.py` |
| P5 | `src/disclosure_drift/m3/request_plan.py` |
| P6 | `src/disclosure_drift/m3/recovery.py` |
| P7 | `src/disclosure_drift/reasons.py` |
| P8 | `src/disclosure_drift/m3/__init__.py` |

**Test paths**

| # | Path |
|---|---|
| T1 | `tests/unit/test_m3_acquisition.py` |
| T2 | `tests/unit/test_m3_dependent_plan.py` |
| T3 | `tests/unit/test_m3_recover.py` |
| T4 | `tests/integration/test_m3_cli.py` |
| T5 | `tests/unit/test_m3_request_plan.py` |
| T6 | `tests/unit/test_m3_recovery.py` |
| T7 | `tests/unit/test_config.py` |

**The fifteen paths are a ceiling, not a requirement to edit each one.** Expected **REQUIRED**
production changes: **P3, P4, P5, P8**. Expected **REQUIRED** tests: **T1, T2, T4, T5**. **P6, P7,
T3, T6, and T7 are conditional.**

**P1 and P2** are historically inside the accepted maximum but are **expected to remain
byte-identical**, because T2.1 already delivered the required configuration surface. Any P1/P2
change must preserve both tracked network switches `false`, the existing fail-closed defaults, and
the existing configuration authority, and must be **justified explicitly in the completion report**.
**An attempt to use P1 or P2 to grant live authority is prohibited.**

## 16. Prohibited paths

The implementation commit may not modify: `src/disclosure_drift/m3/receipt.py`;
`src/disclosure_drift/sec/observation_catalog.py`; `src/disclosure_drift/sec/http_client.py`;
`src/disclosure_drift/sec/index_retrieval.py`; `src/disclosure_drift/sec/census_orchestrator.py`;
`src/disclosure_drift/sec/raw_store.py`; `src/disclosure_drift/sec/snapshots.py`;
`src/disclosure_drift/sec/source_registry.py`; `src/disclosure_drift/sec/request_ceiling.py`;
`src/disclosure_drift/storage/catalog.py`; **any migration**; `tests/conftest.py`;
`tests/integration/test_no_network.py`; `tests/unit/test_m3_receipt.py`;
`tests/unit/test_request_ceiling.py`; `tests/unit/test_httpx_transport.py`;
`tests/unit/test_migration_provenance.py`; any `Docs/`, `Literature/`, or `Milestones/` path; any
accepted Decision; any contract; any G1 review artifact; and any evidence-index vocabulary surface.

**The Decision 038 and Decision 041 path extensions do not carry forward automatically into this
stage.** If the exact `show-drift` or reconciliation requirements cannot be implemented without
`sec/observation_catalog.py`, **STOP. Do not self-widen.**

M3.2 run registration and attribution (§6A) are newly authorized responsibilities of **P3 within the
existing accepted schema**. If they cannot be achieved without a prohibited path or a schema change,
implementation must **STOP**.

## 17. Stale contract-header precedence ruling

The owner acknowledges that the accepted `Milestones/contracts/m3_2.md` header and status metadata
still reflect an earlier Decision-037-era authorization state. The contract **body** and the
accepted substantive contract remain binding.

Where the stale header metadata conflicts with later accepted governance, **Decisions 039, 042, 044,
and 045 control** the current stage-authorization state. **The stale header is historical metadata
and is NOT a stop condition** for execution of this Decision-045-authorized stage.

**Do not edit the accepted contract.** Its accepted SHA-256 remains unchanged.

## 18. Freeze-SHA recording ruling

The T2.5–T2.6 implementation session **shall not edit `Milestones/STATUS.md`**. The
implementation-freeze candidate SHA is **first reported in the completion handoff** and is **durably
bound later by the T3 acceptance governance Decision**. This resolves the older packet language
suggesting that the implementation session itself records the freeze SHA in the ledger.

## 19. Network and live-operation negative authority

This Decision authorizes **implementation and offline testing only**. It does **not** authorize:
setting either tracked network switch `true`; CompanyFacts enablement; use of a real SEC identity; a
DNS lookup; a connectivity test; a real HTTP request; real operational-catalog creation; real
raw-object acquisition; live receipt creation; real request-attempt consumption; use of ceiling
**801**; M3.2A execution; M3.2B execution; T4; T5; T6; or Gate H.

**All network-capable behaviour must be exercised only through injected or scripted in-process test
transports.**

## 20. Subphase-A self-check

Before beginning Subphase B, the implementation session must demonstrate at minimum: all five
offline surfaces wired; dependent-plan derivation deterministic; the accepted M3.2A plan hash
unchanged; `--show-scope` constructs no transport; the reconciliation report deterministic;
`show-drift` run scoping correct; `recover` requires an existing caller-supplied run ID;
progress-sink untrusted text excluded from artifacts and receipts; targeted Subphase-A tests green;
changed paths still inside the envelope; and no network or live action occurred.

This is a **self-check, not a commit or an owner gate**. **If a relevant MAJOR appears, stop before
Subphase B.**

## 21. Required validation

During implementation, use targeted tests and touched-file static checks. At freeze-candidate
completion, run the accepted complete stage gate **once**.

Also prove: `tests/unit/test_httpx_transport.py` **executes rather than skips**; the `[sec]` extra
is actually available; plan hash `19be7bdc…` reproduces; receipt validation succeeds over every
generated fixture receipt; ceiling C−1 / C / C+1 behaviour; the no-network regression remains
byte-identical and green; the migration-provenance regression remains green; changed paths are a
subset of this Decision's envelope; the prohibited-path nonchange proof; no S5/S6 identity
contamination; and no operational artifact.

**Enumerate the actual skip inventory from the final full run** rather than copying historical
wording.

## 22. Required high-risk test coverage

At minimum, include load-bearing tests for: every in-process live authorization-conjunction element;
the transport constructor never being called on a refusal; explicit `--live`; exact ceiling
equality; exact plan-hash equality; exact window binding; prohibited-route construction; prohibited
filing-body construction; `--show-scope` zero-network and zero-transport; deterministic
dependent-plan success and its complete refusal matrix; reconciliation byte determinism;
reconciliation absence and blocking exit behaviour; `show-drift` **run isolation**; `show-drift`
blocking exit behaviour; recovery invalid, unknown, and fabricated-run refusal; resume accounting
with no duplicate substantive write; response classification totals; status-code totals; lawful 304
accounting; cooldown accounting; the request-level cache / 304 / duplicate distinction; receipt mode
and completion-state correctness; **no receipt written on a pre-execution refusal**; progress-sink
content exclusion; `completed_with_absences` receipt rejection; unknown receipt-field rejection; and
a separate-process durability check where relevant to resumed recovery state.

**Run registration and attribution (§6A) additionally require:** registration failure preventing
transport construction and any physical request; exactly one run row per lawful live invocation; a
resumed invocation receiving a **new** run identity while preserving predecessor lineage; the
registered row carrying `job_kind = 'm3_2_acquisition'` and the exact window stage; and durable
run→observation attribution proving `show-drift --run` isolation between two distinct runs in one
catalog.

**Response-accounting tests (§9) must include at minimum:**

| Case | Required demonstration |
|---|---|
| Redirect | A followed 3xx produces its actual 3xx status count, one `proceed` bucket, one redirect hop, and preserves the equality invariant |
| 304 | A lawful 304 produces one `304` status, one `proceed`, one not-modified count, and **no** duplicate-200 count |
| Transport failure | A classified no-response transport failure produces one `"0"` status sentinel, exactly one accepted policy bucket, and **no fabricated HTTP status** |
| Pre-transport refusal | A refusal before any transport response contributes no status entry, no response-classification entry, and **no receipt** when the refusal occurs before lawful live execution begins |
| Mixed sequence | A deterministic scripted sequence containing at least a followed redirect, a normal HTTP response, a 304, and a transport failure demonstrates `sum(response_classification_totals.values()) == sum(status_code_totals.values())` with every event accounted **exactly once** |

## 23. Effective mutation campaign

Use the Decision 043 / G1 mutation hygiene
([`Docs/m3/review_execution_conventions.md`](../m3/review_execution_conventions.md) §5). At minimum
perform **effective** mutations against the highest-risk controls:

1. each live authorization-conjunction element;
2. ceiling equality;
3. exact plan-hash comparison;
4. explicit `--live`;
5. network-key selection;
6. cache-hit versus 304 binding;
7. duplicate-200 versus 304 binding;
8. the lawful 304 response bucket;
9. status-code accumulation;
10. cooldown accumulation;
11. reconciliation blocking/absence exit;
12. `show-drift` blocking exit;
13. dependent-plan transport-capable-configuration refusal;
14. dependent-plan reconciliation-set disagreement;
15. progress-sink exclusion;
16. run-identity fabrication and refusal;
17. resume ceiling preservation;
18. pre-execution refusal receipt suppression;
19. **run-registration ordering** — registration moved after transport construction, or its
    verification removed;
20. **run→observation attribution** — attribution omitted, or `show-drift --run` falling back to
    unscoped global drift;
21. **the transport-failure `"0"` sentinel** — omitted, or a real HTTP response recorded under
    `"0"`;
22. **the redirect response bucket** — a followed 3xx omitted from either total.

For every mutation: prove the source bytes changed; prove behaviour actually changed; run the
killer; classify as `KILLED`, `SURVIVED_EFFECTIVE`, or `SURVIVED_NO_OP`; restore the exact bytes;
and verify restoration. **No effective high-risk mutation may survive.**

## 24. Freeze-candidate acceptance conditions

The candidate exists only when **all** are true: combined T2.5–T2.6 behaviour complete; all six
operator surfaces complete; receipt assembly complete **without** a receipt-schema edit; exact
path-envelope compliance; no unresolved BLOCKER; no relevant unresolved MAJOR; targeted validation
green; stage gate green; the HTTPX transport suite executed; the mutation campaign green; the
no-network state preserved; no operational artifact; no live execution; **one** implementation
commit only; the exact subject; **no tag**; and the candidate remaining **local and unpushed**.

## 25. Commit structure

Create **at most one** T2.5–T2.6 implementation commit with the exact subject
`Complete M3.2 T2.5-T2.6 integrated implementation`. Its parent must be the published Decision 045
governance baseline. **Do not create a Subphase-A commit. Do not push. Do not tag. Do not record the
freeze SHA in `Milestones/STATUS.md`.**

After successful candidate creation, control returns for fresh independent T3 review authorization.

## 26. T3 review lifecycle

The freeze candidate must undergo a **genuinely fresh, non-author independent T3 review** —
**Claude Opus 5**, effort **Max** — using an isolated reviewer-owned environment and remaining
**read-only until its substantive verdict**. On `PASS`, the later review packet may authorize
exactly **one** durable review-artifact commit under `Docs/m3/reviews/`. **The candidate remains
unpushed through review.**

## 27. Governance sequence

1. Decision 045 authorization and publication;
2. combined T2.5–T2.6 implementation;
3. one local implementation-freeze candidate;
4. fresh independent T3 review;
5. durable T3 review artifact on `PASS`;
6. Decision 046 owner acceptance;
7. one normal fast-forward publication of candidate + review + Decision 046.

**No intermediate T2.5 acceptance is required.** A correction that remains inside this Decision's
envelope may be authorized by an **owner correction packet without a new Decision**. A correction
requiring authority outside the envelope requires a **new owner Decision**.

## 28. Stop conditions

Stop **before the act** if: a sixteenth implementation path is required; `sec/observation_catalog.py`
or another prohibited path becomes necessary; a migration is required; the receipt schema must
change; another reason code is required; source or route authority must change; tracked network
enablement must change; **run-scoped drift cannot be established lawfully within the envelope**;
**no existing schema relation can lawfully carry the required run→observation attribution**; **run
registration cannot be ordered before transport construction or cannot be verified**; **the accepted
transport result surfaces cannot account exactly for redirects, terminal status, transport failures,
or response-policy decisions**; dependent-plan derivation cannot verify frozen inputs within the
authorized interfaces; progress-sink exclusion cannot be guaranteed; a high-risk effective mutation
survives; a relevant BLOCKER or MAJOR remains; or live SEC activity appears necessary.

**Do not weaken a guard to finish.**

## 29. Model allocation

| Role | Model | Effort |
|---|---|---|
| Combined T2.5–T2.6 implementation | Claude Opus 5 | **Max** |
| Correction cycle | Claude Opus 5 | **High** by default; **Max** for architectural, durability, accounting, or BLOCKER-level corrections |
| Independent T3 review | Fresh Claude Opus 5 | **Max** |

## 30. The owner instrument

The operative owner text, reproduced without alteration of substance. §§1–29 above are that
instrument's content as issued, with the owner's 2026-08-07 pre-recording rulings incorporated at
§4.6, §4.7, §6A, §9, §10, §14, §22, §23, and §28 exactly as the owner directed.

```text
OWNER_DECISION_045_M3_2_T2_5_T2_6_INTEGRATED_IMPLEMENTATION_AUTHORIZATION: APPROVED

Decision title:
M3.2 T2.5-T2.6 Integrated Implementation and Freeze-Candidate Authorization

Date: 2026-08-07

M3.2 T2.5-T2.6 SHALL PROCEED AS ONE COMBINED IMPLEMENTATION STAGE.

This follows accepted Decision 037 and contract section 22. No separate T2.5
implementation commit, T2.5 acceptance, or T2.6 authorization is required. The
combined stage shall produce one implementation-freeze candidate for the
independent T3 review. Exact implementation commit subject:

Complete M3.2 T2.5-T2.6 integrated implementation

The candidate remains local and unpushed pending T3 review. No tag is
authorized.

The owner has reviewed the two pre-recording findings. Both findings are
accepted as genuine defects in the unrecorded Decision-045 draft. Because
Decision 045 has not yet been written, committed, or published, do NOT create a
corrective/amendment Decision. Instead, incorporate the following rulings
directly into the first durable Decision 045 so the repository never contains
the defective version. All other Decision-045 rulings remain unchanged.

BLOCKER_1_RESOLUTION: A1_APPROVED

M3.2 shall have a durable acquisition-run identity. Do not re-scope
m3 show-drift away from --run. Do not defer the run-identity problem. No
migration or prohibited-path edit is authorized. For every actual
m3 acquire --live invocation that reaches the point of lawful execution, the M3
acquisition driver in src/disclosure_drift/m3/acquisition.py is authorized to
register exactly one durable row in the existing ops_ingestion_jobs table, with
job_kind = 'm3_2_acquisition' and stage corresponding exactly to the governed
acquisition window M3.2A or M3.2B. Do not reuse the M2.2-only registration
implementation. Registration is ordered before transport construction and must
be verified; on failure no transport may be constructed, no physical request may
occur, and no acquired object may be durably attributed to that failed run. A
run identifies one live command invocation, not an entire window, so a resumed
invocation receives a new run identity. Every observation durably created or
adopted for a live M3.2 invocation must be durably attributable to that
invocation's census_run_id through existing accepted relations only, proven
compatible before use; if none can lawfully represent it, STOP. m3 show-drift
--run and m3 recover --run are retained, scoped to an existing M3.2 acquisition
run, failing closed with exit 4 on unknown, non-M3.2, unattributable, or
ambiguous identity, with no global-drift fallback and no fabricated identity.

BLOCKER_2_RESOLUTION: EXHAUSTIVE_RESPONSE_EVENT_ACCOUNTING_WITH_STATUS_ZERO_SENTINEL

The strong equality invariant is retained. The owner expressly defines one
receipt-local sentinel status_code_totals["0"] meaning "no HTTP status —
transport-level failure". This is an M3.2 receipt-accounting convention, not an
HTTP status code. The frozen receipt schema remains unchanged because the
existing count-map keys are already strings and no schema field or validator
shape changes. Each response-policy event contributes exactly one
response_classification_totals bucket and exactly one status_code_totals entry,
so sum(response_classification_totals.values()) ==
sum(status_code_totals.values()). Pre-transport refusals are not response-policy
events. A followed 3xx contributes its actual status and one proceed bucket. A
lawful 304 contributes status 304, proceed, and not_modified_count, and never
duplicate_object_count. A classified no-response transport failure contributes
status_code_totals["0"] and exactly one accepted policy bucket; no new bucket
may be invented, and a real HTTP response must never be recorded under "0".
cooldown_count == response_classification_totals["cooldown"]. The accounting is
produced inside the authorized M3 acquisition layer; sec/http_client.py and
m3/receipt.py may not be modified for convenience, and insufficient accepted
surfaces are a STOP rather than an inference.

These rulings do NOT widen the fifteen-path implementation ceiling. In
particular they do not authorize modification of sec/census_orchestrator.py,
sec/observation_catalog.py, sec/http_client.py, any migration, or
m3/receipt.py. M3.2 run registration and attribution are newly authorized
responsibilities of P3 within the existing accepted schema. If that cannot be
achieved without a prohibited path or schema change, implementation must STOP.

The final Decision 045 must be internally consistent and must not retain the
now-invalid claim that run scoping can exist without a durable M3.2
run-registration/attribution responsibility. It must also not retain an
accounting definition that excludes redirects or transport failures while
asserting the equality invariant. Do not describe the defective unrecorded draft
as an accepted historical Decision.

Recording and publication of this Decision are explicitly authorized on exactly
three governance paths — the Decision 045 record, the decision registry, and
Milestones/STATUS.md — with one governance commit whose subject is

Authorize M3.2 T2.5-T2.6 integrated implementation

and one normal fast-forward push of main. No fourth path. No amend, rebase,
squash, force push, or tag. Implementation remains NOT BEGUN and must not begin
in the governance session.

NEXT_AUTHORIZED_ACTION:
CHATGPT_OWNER_ISSUANCE_OF_M3_2_T2_5_T2_6_IMPLEMENTATION_PACKET_AFTER_DECISION_045_PUBLICATION

Owner:
Joseph Nihill, acting through the ChatGPT project-owner role

Date: 2026-08-07

This is a transparent recorded owner decision, not a handwritten,
cryptographic, or third-party digital signature.
```

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.

## 31. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_045_m3_2_t2_5_t2_6_integrated_implementation_authorization.md` (this
  record);
- `Docs/Decisions/decision_registry.md` — the 045 row and quick-lookup entry;
- `Milestones/STATUS.md` — current-state, blocker, authority-state, and next-action updates, with
  the machine marker set exactly to
  `NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_ISSUANCE_OF_M3_2_T2_5_T2_6_IMPLEMENTATION_PACKET_AFTER_DECISION_045_PUBLICATION`;
- **one** governance-only commit with the exact subject
  `Authorize M3.2 T2.5-T2.6 integrated implementation`, and **one** normal fast-forward push of
  `main`. **No tag.**

`Docs/decision_index.md` is deliberately **not** edited — the established navigation ruling stands
and the decision registry remains the discovery route. No implementation, test, script, migration,
receipt, template, packet, contract, review-artifact, configuration, or private-evidence byte
changes.

## 32. Acceptance criteria for this record's commit

All verified before the commit: (1) the owner's authorization and both pre-recording rulings are
recorded without change of substance and neither broadened nor narrowed, and no earlier draft is
described as an accepted historical Decision; (2) `src`, `tests`, `configs`, migrations, the receipt
module, the contract, and the T2 packet are byte-identical to the published baseline; (3) Decisions
001–044 are byte-unchanged; (4) Decision 045 is unique — no other decision file or registry row
carries the number, and directory and registry agree; (5) the registry and status ledger match this
record exactly, with the next-action marker line occurring exactly once and carrying no suffix;
(6) `git diff --check` and `git diff --cached --check` pass over the updated tree; (7) the commit
carries exactly the three §31 paths; (8) no tag is created; (9) no private path, SEC identity, or
private-evidence content appears in any changed file; (10) both tracked network switches remain
`false`, the migration chain remains `0001`–`0013`, and the receipt remains
`m3-execution-receipt/2.0`; (11) no operational catalog, run row, receipt, raw object, evidence
artifact, request, or SEC contact is created.

## 33. Formal outcome

```text
M3_2_T2_5_T2_6_INTEGRATED_IMPLEMENTATION_AUTHORIZED
```

**Combined stage T2.5–T2.6 is AUTHORIZED and has NOT BEGUN.** Implementation may not start from this
record alone: the separate owner-issued execution packet is a precondition to any executable work.
Network enablement, live SEC access, acquisition, real operational-catalog creation, real run-row
creation, receipt emission, and ceiling-801 use all remain unauthorized, and T3, T4, T5, T6, and
Gate H remain separate later owner acts.

**Next authorized action:**
`CHATGPT_OWNER_ISSUANCE_OF_M3_2_T2_5_T2_6_IMPLEMENTATION_PACKET_AFTER_DECISION_045_PUBLICATION`

---

**Owner:** Joseph Nihill, acting through the ChatGPT project-owner role.
**Date:** 2026-08-07.
This is a transparent recorded owner decision, not a handwritten, cryptographic, or third-party
digital signature.
