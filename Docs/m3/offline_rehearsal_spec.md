# Milestone 3 — Offline Rehearsal Specification

**Status:** specification only. **Neither rehearsal has been implemented and neither has been run.**
**Phases:** **M3.1A** — acquisition rehearsal, scenarios **A1–A12**. **M3.3A** — execution rehearsal,
scenarios **E1–E8**.
**Network permission:** `NONE` for both — no socket is opened.
**Controlling records:** [Decision 027](../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§§6.1, 6.3, 8, as narrowly corrected by proposed
[Decision 028](../Decisions/decision_028_m3_1_readiness_corrections.md) §§5–8, as narrowly
superseded in two clauses by
[Decision 029](../Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md), which
is controlling for the manifest-resolution injection (§3), the one new reason code (§2 constraint 7),
and the per-route `A_reachable` witness (§6.9). **A1–A12 remain exactly twelve scenarios with
unchanged identities; no A13 is introduced.**
**Plan:** [`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md).
**Completion tokens (future):** `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED` (A1–A12); the E1–E8 result
is recorded inside M3.3A and gates M3.3B.

---

## 1. Why there are two rehearsals, in two phases

The first live SEC run is the worst possible place to discover that an interruption between a
raw-store write and a catalog commit leaves an orphan, that a duplicate body creates a second object,
or that a schema change silently defaults a field. The first *real* snapshot is the worst possible
place to discover that reconstruction disagrees with persistence. Both classes of failure are cheap
to produce on demand offline and nearly impossible to produce on demand live.

**But a rehearsal can only exercise a production path that exists.** At M3.1 there is no
candidate-snapshot builder anywhere in the repository, so a scenario claiming to rehearse a snapshot
freeze at M3.1 would be exercising nothing.

**The governing rule, frozen by Decision 027 §6.1: no scenario may be placed in a phase that lacks
the production path it exercises.** Hence two rehearsals:

| Rehearsal | Phase | Scenarios | Gates | Must pass before |
|---|---|---|---|---|
| **Acquisition** | **M3.1A** | **A1–A12** | Gate F | the first SEC request |
| **Execution** | **M3.3A** | **E1–E8** | M3.3A review | the real snapshot freeze |

## 2. Global constraints — both rehearsals

1. **No socket is opened.** Asserted, not assumed.
2. **No live SEC data.** Every response is scripted; every fixture is synthetic or real-shaped.
3. **Deterministic clock inputs.** Wherever an operational timestamp is required, it is supplied
   explicitly. **Nothing reads the system clock into a recorded identity.**
4. **Deterministic ordering.** Planned order is a property of the plan, not of iteration order,
   dictionary order, or arrival order, and is asserted stable across runs.
5. **An isolated synthetic data root.** Never the machine's default data root, never a personal path.
6. **Every scenario is implemented and runs.** None may be skipped, `xfail`ed, or conditionally
   disabled. An unimplemented scenario is a phase failure.
7. **Reason codes come from the registered registry.** A scenario needing a code the registry does
   not contain — and which the future M3.1 contract has not already registered under Decision 028
   §6, or Decision 029 §5 — is a stop-and-report condition, not licence to add one.
   [Decision 029](../Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md) §5
   registers exactly one further code, `OFFLINE_REHEARSAL_SCENARIO_MISMATCH` (category `integrity`,
   `blocks_release=true`, `requires_manual_review=false`), recorded when a scenario does not reach
   the state this specification names. `SEC_ACQUISITION_INTERRUPTED` remains reserved for genuine
   acquisition interruption and may never stand in for a defective witness.
8. **Receipts are produced for every rehearsal command.** Acquisition scenarios A1–A12 use
   `invocation_mode = "rehearsal"`; execution scenarios E1–E8 use
   `invocation_mode = "offline_execution"`. In both modes the **actual network counts are `0`**.
   Simulated request, response, and object-accounting totals belong to the rehearsal evidence
   report, never to receipt fields classified for `live` mode
   ([`execution_receipt_spec.md`](execution_receipt_spec.md) §§4.5, 14).
9. **No uncontracted module is modified** to make a scenario pass. The future M3.1 contract may make
   only the bounded Decision 028 corrections it names; the rehearsal must exercise the resulting
   production path rather than substituting test-only behaviour.
10. **All rehearsal evidence is private evidence.** Completed records live in the owner-controlled
    private evidence root; only type, phase, status, SHA-256, and a reference identifier reach the
    public [`evidence_index.md`](templates/evidence_index.md).

## 3. Fixture and injection design

**Scripted responses.** A response script is a deterministic, ordered mapping from
`request_identity(source_id, normalized_url, parameters)` and attempt ordinal to a synthetic
`(status, headers, body)` triple. The same script always produces the same sequence.

**Synthetic and real-shaped fixtures.** Candidate, entity, accession, evidence, reserve, and
disposition fixtures are constructed in the shape the accepted loaders expect, with explicit values
for every field the accepted identity functions consume. **No fixture is derived from a real filing,
a real registrant, or any real SEC payload.**

**Injection points** — six, all at boundaries the accepted architecture already exposes, or that the
bounded M3.1 corrections introduce as explicit arguments:

| Injection | Where |
|---|---|
| Response substitution | The transport boundary — the harness supplies responses instead of a client |
| Clock substitution | The explicit clock argument the rate limiter and any timestamped output already take |
| Interruption | A named abort point, raised between two identified statements |
| Filesystem fault | A write that raises after `n` bytes, or a file removed between write and verification |
| Payload mutation | A field added, removed, nulled, or retyped in a scripted body, to produce drift |
| Ceiling substitution | The explicit cumulative physical-attempt ceiling argument the acquisition driver takes, per Decision 028 §7 |
| Manifest resolution (rehearsal only) | A context-managed substitution of the binding `SecClient._resolve_url` consults for a manifest-resolved route — that is, of `disclosure_drift.sec.http_client.require_evidence` — authorized narrowly by Decision 029 §4 |

**No injection modifies production code.** Each is a test-time substitution at a seam that exists
when the rehearsal runs.

**The manifest-resolution injection is narrowly bounded** (Decision 029 §4). It exists so
`sec_edgar_calendar_announcement` — whose URL comes only from a reviewed manifest, and whose
source-controlled manifest is provably empty — can be driven through the **real** `SecClient.fetch()`
policy loop and yield an independently tested `A_reachable`. It must:

- exist only inside the offline rehearsal context, never in a production code path;
- resolve exactly one fixed synthetic evidence identifier to exactly one fixed approved-host URL of
  the route's registered family;
- never enter or mutate `CALENDAR_EVIDENCE_MANIFEST`;
- never read, write, or require the operator's private calendar-evidence manifest;
- never assert a real date, announcement, or provenance fact outside the fixture;
- never be serialized into a report, receipt, plan, catalog, snapshot, or raw object;
- restore the production resolver on normal **and** exceptional exit; and
- open no socket, and grant no live and no arbitrary-URL retrieval authority.

It is implemented as a scoped substitution, **never** by adding a resolver parameter, URL override,
or arbitrary-URL API to the production `SecClient`.

---

# Part I — M3.1A acquisition rehearsal (A1–A12)

## 4. What the acquisition rehearsal must cover

| # | Capability | Scenario |
|---|---|---|
| 1 | Request planning and deterministic ordering | A1 |
| 2 | Request-budget enforcement | A5 |
| 3 | Rate limiting | A1, A2 |
| 4 | Retries and retry scheduling | A2 |
| 5 | `Retry-After` | A3 |
| 6 | Cooldowns, block pages, terminal responses | A4 |
| 7 | Redirect handling within the accepted depth | A6 |
| 8 | Route allowlist and denylist enforcement | A6 |
| 9 | Content-addressed raw storage and provenance | A1, A9, A11 |
| 10 | Duplicate and changed-body handling | A9, A10 |
| 11 | Parser behaviour and unknown-field retention | A7 |
| 12 | Blocking schema drift | A8 |
| 13 | Catalog transactionality | A11 |
| 14 | Interruption and recovery | A11 |
| 15 | Execution receipts and prohibited-field scanning | A12 |
| 16 | Receipt non-contamination | A12 |

**Explicitly out of scope for A1–A12:** candidate-snapshot construction, snapshot freeze, S5
selection, reserves, dispositions, selection-result sealing, S6 manifest construction, and root
computation. Those are E1–E8.

## 5. Acquisition scenario matrix

Each scenario specifies setup, expected command, expected response, expected reason code, expected
persisted state, expected files, expected receipt, expected rollback, expected recovery, and expected
validation. "No rollback" means none is expected, and an observed rollback is a failure.

---

### A1 — All-success acquisition

| Field | Specification |
|---|---|
| **Setup** | Full synthetic plan across every bootstrap route; every scripted response `200` with a well-formed body of that route's expected content kind; empty data root; empty catalog at migration `0013` |
| **Expected command** | `m3 plan-requests`, then `m3 rehearse --scenarios A1` |
| **Expected response** | Every logical request classified `proceed`; physical attempts equal logical requests |
| **Expected reason code** | none. First storage is `stored_new`; `SOURCE_CONTENT_UPDATED` applies only to a later changed living source |
| **Expected persisted state** | One source-observation row per logical request, each with its validated single-hop chain; parsed source records with parser version and complete `parser_state`; no quarantine row |
| **Expected files** | One content-addressed raw object per logical request, each with its `.lineage.json` sibling; **zero** `.part` files |
| **Expected receipt** | `completion_status = "complete"`; **`actual_logical_request_count = 0` and `actual_physical_attempt_count = 0`** (rehearsal mode); simulated totals recorded in the rehearsal evidence report; `schema_drift_outcome = "none"` |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | Simulated planned equals simulated actual per route; every object verifies against its `content_sha256`; every observation has complete provenance; the plan hash is unchanged from the dry run; **the request order is identical across two runs**. The announcement route lawfully contributes zero requests when its evidence manifest is empty |

---

### A2 — Retry then success

| Field | Specification |
|---|---|
| **Setup** | One route scripted `503, 503, 200`; all others `200` |
| **Expected command** | `m3 rehearse --scenarios A2` |
| **Expected response** | Attempts 1 and 2 classify `retry` with exponential backoff from the accepted base; attempt 3 classifies `proceed` |
| **Expected reason code** | none terminal — a retryable action carries no reason code while it is still retryable |
| **Expected persisted state** | **One** source observation for the route, not three; retry ordinals recorded on the attempt record |
| **Expected files** | **One** raw object for that route; no partial file left behind |
| **Expected receipt** | Rehearsal-mode network counts `0`; the simulated logical/physical split and the two `retry` classifications recorded in the evidence report |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | A retry consumes **no** additional logical request and **exactly one** additional physical attempt; backoff is exponential from the accepted base and never exceeds the accepted ceiling. This scenario no longer supplies a term of `A_reachable`: that bound is established by the single full-path witness of §6.9, not by adding separately measured retry, cooldown, and redirect terms |

---

### A3 — `Retry-After`

| Field | Specification |
|---|---|
| **Setup** | `429` **with** a usable `Retry-After: 3`, then `200`; plus a variant with an unusable HTTP-date `Retry-After` |
| **Expected command** | `m3 rehearse --scenarios A3` |
| **Expected response** | Usable value → `retry_after`, delay `3.0 s`, aggregate traffic **not** halted. Unusable value → falls back to the aggregate cooldown path |
| **Expected reason code** | none while retryable |
| **Expected persisted state** | One source observation; the honoured delay recorded on the attempt |
| **Expected files** | One raw object once the retry succeeds |
| **Expected receipt** | Rehearsal-mode network counts `0`; the `retry_after` classification recorded in the evidence report |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | A usable delta-seconds `Retry-After` is honoured exactly and **does not** halt aggregate traffic; an unusable one **does** fall through to the cooldown path rather than being silently ignored |

---

### A4 — Cooldown and block-page termination

| Field | Specification |
|---|---|
| **Setup** | Three variants: (a) `429` **without** `Retry-After`; (b) `403`; (c) `200` whose body carries a block-page signature. Each followed by a second cooldown-triggering response |
| **Expected command** | `m3 rehearse --scenarios A4` |
| **Expected response** | Each first occurrence → `cooldown`, aggregate traffic **halted**, exactly **one** controlled further request permitted. Each second occurrence → **terminal** |
| **Expected reason code** | `SEC_RETRIES_EXHAUSTED` for a second unqualified `429`; `SEC_BLOCK_PAGE` for a second `403` or block-page response |
| **Expected persisted state** | The attempt and its classification recorded; **no** partial or empty observation promoted to usable; the retrieval marked failed on the second cooldown |
| **Expected files** | No raw object for a non-`proceed` outcome; nothing empty stored |
| **Expected receipt** | Rehearsal-mode network counts `0`; `completion_status = "failed"`; `reason_code` set; the cooldown count recorded in the evidence report |
| **Expected rollback** | Per the accepted order: stop new requests, mark failed, preserve attempts, roll back the uncommitted transaction |
| **Expected recovery** | An **explicit** resume decision is required; no automatic resume |
| **Expected validation** | **A failure never becomes a valid empty result**; the halt is **aggregate**, not per-worker; exactly one controlled post-cooldown request is permitted and a second cooldown is terminal |

---

### A5 — Stop before budget overflow

| Field | Specification |
|---|---|
| **Setup** | Two variants. **(a) Overflow:** a plan whose derived maximum physical attempts exceed a deliberately low injected hard ceiling. **(b) Exactly at `C`:** a plan whose attempts total exactly the injected ceiling. Every response `200` in both |
| **Expected command** | `m3 rehearse --scenarios A5` |
| **Expected response** | The run **refuses to place the attempt that would exceed the ceiling** and stops |
| **Expected reason code** | `SEC_REQUEST_CEILING_EXHAUSTED` |
| **Expected persisted state** | Every object retrieved before the stop is committed and provenanced; the run marked `stopped_at_ceiling` — a status distinct from `failed` — with the remaining plan recorded unattempted |
| **Expected files** | Raw objects for the completed retrievals only; no partial file |
| **Expected receipt** | `completion_status = "stopped_at_ceiling"`. Actual network counts remain `0` in the rehearsal receipt |
| **Expected rollback** | Stop-and-preserve, never delete |
| **Expected recovery** | A real resume would carry consumed attempts forward. If the proven remainder does not fit the original headroom, stop for re-planning and a new exact owner approval; never enlarge the active window silently |
| **Expected validation** | **Stop-before-overflow, never stop-after.** Exactly `C` attempts are allowed; `C+1` is refused and the counter remains `C`. Variant (b), completing exactly at `C`, succeeds. The simulated attempt total equalling `C`, the fact that `C+1` was not placed, and the remaining planned count are recorded in the **rehearsal evidence report**, never in a receipt's `live`-classified fields |

---

### A6 — Route allowlist and denylist enforcement

| Field | Specification |
|---|---|
| **Setup** | A scripted plan and scripted redirect chains that attempt, per denied family: `/Archives/edgar/data/…`; an `-index.htm` path; `.txt`, `.htm`, `.xml`, `.xsd` suffixes; a CompanyFacts path; a Frames path; a non-SEC host; a scheme downgrade; a user-info authority; an unexpected port; a fragment; a relative `..` segment; a redirect leaving the source's URL family; a redirect loop; and an over-depth chain |
| **Expected command** | `m3 rehearse --scenarios A6` |
| **Expected response** | Invalid initial routes are refused before transport. A redirect violation occurs only after the preceding scripted response; its proposed next hop is refused before being followed and before any write |
| **Expected reason code** | `SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY` for boundary violations; `SEC_REDIRECT_DEPTH_EXCEEDED` for loops and over-depth chains |
| **Expected persisted state** | No observation, parsed record, or catalog row for an invalid initial route. A redirect refusal records only the already-observed attempt evidence required by policy and promotes no payload to a usable observation |
| **Expected files** | No raw object and no `.part` file for any refused route |
| **Expected receipt** | `completion_status = "failed"` on the refusal variants; the refusal reason recorded |
| **Expected rollback** | Initial-route refusal has nothing to roll back. Redirect refusal preserves the preceding attempt evidence and performs no substantive write for the refused hop |
| **Expected recovery** | none |
| **Expected validation** | Every one of the nine registered families is asserted **reachable** at its exact path or pattern; a manifest-resolved announcement source with an empty accepted manifest is lawful and yields zero instances, **but still requires the §6.9 witness — a zero `U(route)` never waives it**; every denied family is asserted **refused** by at least one representative probe; **only `GET` and only `www.sec.gov` / `data.sec.gov` are permitted**. This scenario no longer supplies a redirect term of `A_reachable`: that bound is established by the single full-path witness of §6.9 |

---

### A7 — Unknown-field retention

| Field | Specification |
|---|---|
| **Setup** | A scripted body carrying one or more **extra unknown** fields at several nesting depths |
| **Expected command** | `m3 rehearse --scenarios A7` |
| **Expected response** | `proceed`; the unknown fields are **retained and logged**; processing continues |
| **Expected reason code** | `PARSER_SCHEMA_DRIFT_OBSERVED` |
| **Expected persisted state** | The drift event recorded as **non-blocking**; the record parsed and admitted; the retained field names recorded |
| **Expected files** | The raw object stored normally |
| **Expected receipt** | `schema_drift_outcome = "unknown_fields_retained"`; `schema_drift_event_count` set |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | **Unknown fields are never discarded silently**, and their presence never blocks a lawful parse |

---

### A8 — Blocking schema drift

| Field | Specification |
|---|---|
| **Setup** | Four variants: a **required field missing**; an **unexpected null**; a **changed type**; a **malformed nested array**. Plus a **new historical-file reference** variant |
| **Expected command** | `m3 rehearse --scenarios A8` |
| **Expected response** | Processing **stops** and evidence is preserved on all four blocking variants |
| **Expected reason code** | `SEC_SCHEMA_REQUIRED_FIELD_MISSING`; `PARSER_STRUCTURE_NULL`; `PARSER_STRUCTURE_WRONG_TYPE`; `PARSER_STRUCTURE_MALFORMED`. The reference variant records `PARSER_HISTORICAL_REFERENCE_MALFORMED` where malformed, or a recorded drift event where merely new |
| **Expected persisted state** | The source observation and raw object are preserved. Parser failure, structural failure, quarantine, and drift evidence are committed atomically; **no invalid/defaulted/coerced normalized row** is admitted. Valid siblings may remain recorded, but the parser run is failed/incomplete |
| **Expected files** | The raw object is retained in every variant — evidence is never deleted |
| **Expected receipt** | `schema_drift_outcome = "blocked"`; `completion_status = "failed"` |
| **Expected rollback** | Policy-failure evidence is retained. Rollback occurs only if the evidence transaction itself faults; that fault may not promote any invalid normalized row |
| **Expected recovery** | Requires a [`schema_drift_incident.md`](templates/schema_drift_incident.md) record and an **owner ruling**; no resume until ruled |
| **Expected validation** | **No default supplied, no type coerced, no row dropped.** A new historical-file reference is a recorded drift event and **does not silently expand the plan** — it is inside the approved budget or it stops the run |

---

### A9 — Byte-identical duplicate and valid-304 reconciliation

| Field | Specification |
|---|---|
| **Setup** | Two variants across two runs against the same data root: **(a)** the same logical request returns a byte-identical `200`; **(b)** a conditional request receives a valid `304` and reuses the preserved snapshot |
| **Expected command** | `m3 rehearse --scenarios A9` |
| **Expected response** | **(a)** both responses classify `proceed`; **(b)** the second response classifies `not_modified` and reuses the preserved object |
| **Expected reason code** | **(a)** second observation `SOURCE_CONTENT_UNCHANGED`; **(b)** second observation `SOURCE_SNAPSHOT_REUSED` |
| **Expected persisted state** | **One** object and **two immutable observations** in each variant. The second is `unchanged_content` for (a) and `reused_snapshot` for (b); neither claims new content |
| **Expected files** | Exactly one raw object and one lineage sibling |
| **Expected receipt** | `invocation_mode = "rehearsal"`; actual network counts `0`; the `C: live` fields `duplicate_object_count` and `raw_object_count` are **absent**. The simulated duplicate/new-object accounting is recorded in the rehearsal evidence report |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | Content-addressing collapses identical bodies by identity, not filename or timestamp; a lawful `304` never suppresses its immutable reuse observation |

---

### A10 — Changed-body new-observation behaviour

| Field | Specification |
|---|---|
| **Setup** | The same logical request returning a **different** body on the second retrieval, in four variants: a `living` source, a **closed-quarter** `dated_snapshot`, an `immutable` identity, and an officially explained dated correction |
| **Expected command** | `m3 rehearse --scenarios A10` |
| **Expected response** | `proceed`, with the change recorded rather than absorbed |
| **Expected reason code** | `SOURCE_CONTENT_UPDATED` for the living source; `SOURCE_DATED_ARTIFACT_CHANGED` for the closed-quarter snapshot; `SOURCE_IMMUTABLE_IDENTITY_MUTATED` for the immutable identity; `SOURCE_CONTENT_UPDATED` plus `SOURCE_CORRECTION_EXPLAINED` for an official explained correction. `REMOTE_CONTENT_CHANGED` may exist only as lower-layer observation evidence, not the final SnapshotStore verdict |
| **Expected persisted state** | A **new observation**, with the earlier observation retained and the supersession lineage recorded and non-cyclic |
| **Expected files** | **Two** raw objects — **the first is never overwritten** |
| **Expected receipt** | `invocation_mode = "rehearsal"`; actual network counts `0`; the `C: live` field `raw_object_count` is **absent**. The simulated new-object accounting and changed-body observation are recorded in the rehearsal evidence report |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | **A differing later response is always a new observation and never an overwrite** (CLAUDE.md rule 6); a change at an immutable identity or a closed dated snapshot is an **anomaly requiring review**, not an ordinary update |

---

### A11 — Raw-store and catalog interruption recovery

| Field | Specification |
|---|---|
| **Setup** | Four injected abort points, exercised in sequence and then recovered from: **(a)** before any byte reaches the raw store; **(b)** after the object is promoted and fsynced but **before** the catalog transaction commits; **(c)** immediately **after** the catalog commit; **(d)** a restart-and-resume pass over all three |
| **Expected command** | `m3 recovery-state`, then `m3 rehearse --scenarios A11` resuming from the predecessor receipt |
| **Expected response** | Each abort terminates the retrieval as interrupted. Read-only inspection reports `UNSAFE` while deterministic repair is required; the isolated rehearsal applies that repair, a second inspection reports `SAFE`, and the resumed synthetic run completes the remainder |
| **Expected reason code** | `SEC_ACQUISITION_INTERRUPTED` where no narrower code applies; `RAW_PARTIAL_DOWNLOAD` only where a stream was actually partial; `RAW_FILE_CHECKSUM_MISMATCH` for an unproven orphan quarantined rather than adopted; `AUDIT_PROJECTION_INCOMPLETE` where a projection rebuild is required |
| **Expected persisted state** | **(a)** catalog byte-identical to the pre-retrieval state, no observation row. **(b)** **no** committed row — the transaction rolled back. **(c)** the committed row present and complete. **(d)** exactly the state one uninterrupted run would have produced — no more rows and no fewer |
| **Expected files** | **(a)** no object, no `.part`. **(b)** the object **exists** as an **orphan**, with its lineage sibling — repair records `RecoveryEvent(action_taken="adopted_verified")` if it verifies against `content_sha256` and lineage intent, otherwise quarantines it with `RAW_FILE_CHECKSUM_MISMATCH`. **It is never deleted.** **(c)** object and lineage present, matching the row. **(d)** zero `.part` files; every orphan adopted or quarantined |
| **Expected receipt** | `completion_status = "interrupted"` with `interruption_state` set to `before_raw_store_write`, `after_raw_store_write_before_catalog_commit`, and `after_catalog_commit` respectively; the resumed rehearsal receipt names its `recovery_predecessor_receipt_id`, reports actual network counts `0`, and omits the live-only `consumed_request_count_carried_forward`; the simulated consumed count is carried forward and proved in the rehearsal evidence report |
| **Expected rollback** | The uncommitted transaction rolls back in every variant; **no file is deleted in any variant** |
| **Expected recovery** | The `m3 recovery-state` inspector is provably read-only and never invokes `observation_catalog.reconcile()` or an equivalent writer. M3.1 rehearses repair only in its isolated synthetic harness; M3.2 owns real repair application and resume. The committed retrieval in (c) is **not** re-attempted |
| **Expected validation** | **This is the scenario the acquisition rehearsal exists for.** Variant (b) produces exactly one orphan, exactly one adoption or quarantine, and **no** duplicate object or row after repair. Inspection alone changes no byte. **Duplicate-prevention proof:** the resumed run issues **zero** requests for an already-committed retrieval, and the final state equals the uninterrupted-run state exactly |

---

### A12 — Receipt non-contamination and non-vacuous prohibited-field scanning

| Field | Specification |
|---|---|
| **Setup** | Two parts. **(a) Redaction:** an environment deliberately loaded with a synthetic SEC identity on a reserved example domain, a synthetic credential, and an absolute path; responses carrying `Set-Cookie` and `Authorization` echo headers; bodies containing recognizable payload text. **(b) Non-contamination:** two otherwise identical complete runs over the same synthetic inputs — run A with receipt emission **disabled**, run B **enabled** — plus run C with receipts enabled and deliberately different operational values (different injected clock, different receipt IDs, different paths, different simulated counts) |
| **Expected command** | `m3 rehearse --scenarios A12`, then `m3 show-receipt` |
| **Expected response** | Every receipt produced; every receipt passes the prohibited-field scan; all three runs complete |
| **Expected reason code** | none on success; `m3 show-receipt` exits `4` if any prohibited field is present |
| **Expected persisted state** | Identical across A, B, and C |
| **Expected files** | Receipt files only; identical acquisition outputs across A, B, and C |
| **Expected receipt** | Contains **none** of: full SEC identity, email address, credential, API token, cookie, authorization header, raw response body, absolute personal path, candidate row, selected row, reserve row, filing text, outcome value. B and C **differ from each other**, which is the point. **Exactly one integrity identity — `receipt_id`** — and no second digest field |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | **Non-vacuous scan:** the harness constructs a receipt that *does* contain a prohibited field and asserts the scan **rejects** it. **Non-contamination:** every acquisition-layer identity — every stored `content_sha256`, every observation identity, every parser fingerprint — is **byte-identical** across A, B, and C. Varying every operational value changes **no** governed value. A single difference is a phase-stopping failure |

---

## 6. Acquisition pass criteria

The M3.1A rehearsal passes when **all** hold:

1. all twelve scenarios A1–A12 implemented and executed — none skipped, `xfail`ed, or disabled;
2. every scenario's observed outcome equals its expected outcome, field by field, across all ten
   specified fields;
3. every observed reason code equals its expected code and is a **registered** code;
4. no socket was opened, asserted rather than assumed;
5. no uncontracted module, and no accepted S4, S5, or S6 module, was modified to make a scenario
   pass;
6. **every rehearsal receipt reports actual network counts of `0`**, with simulated totals in the
   evidence report;
7. every receipt passes the prohibited-field scan, and the positive control proves the scan is not
   vacuous;
8. **A12's non-contamination proof holds exactly**;
9. **`A_reachable` is independently tested per route by one realizable full-path witness** — see
   §6.9 — with `unmeasured_routes` empty and the tested key set exactly equal to the authoritative
   derived key set;
10. re-running the whole rehearsal from the same fixtures reproduces the same results.

### 6.9 The per-route `A_reachable` witness

Superseding the earlier description, which credited A2, A4, and A6 with separately measured retry,
cooldown, and redirect terms and **added** them. That arithmetic proved each term separately
reachable and never proved the composite path realizable, so it was not a witness. Decision 029 §7
replaces it with **one black-box `SecClient.fetch()` execution per route**, whose observed transport
attempt count *is* the tested bound.

| Routes | Scripted path | Attempts |
|---|---|---|
| The four exact singleton routes, and `sec_edgar_calendar_announcement` | `503 × 4` → unqualified `429` → **active** same-path/only-path redirect refusal | **6**, with zero accepted redirect hops |
| `sec_edgar_filing_calendar` | `503 × 4` → `429` → one accepted in-family redirect → terminal response | **7** |
| `sec_full_index_company` | `503 × 4` → `429` → five accepted unique in-family redirects → terminal response | **11** |

Three rules make the witness non-vacuous:

1. **The four singleton routes must actively receive and reject a redirect response.** Reporting zero
   hops without exercising the resolver is a failure, because it proves only that the measurement
   never asked.
2. **Removing or bypassing any segment of the combined path must make the witness fail.** A witness
   that still passes with a segment deleted is measuring something else.
3. **A zero `U(route)` never waives the witness.** The obligation holds whether the approved operator
   calendar-evidence manifest is empty (`U = 0`, the route contributing zero to the ceiling) or
   non-empty (`U = m > 0`). Gate F §9.3's arithmetic and Gate F §3.10's evidence obligation are
   separate requirements; satisfying the first does not discharge the second. A **missing** operator
   manifest is a third case: `U` is then undefined, planning is refused outright, and the witness is
   still required.

A witness that does not reach the state named above records `completion_status = "failed"` with
`reason_code = "OFFLINE_REHEARSAL_SCENARIO_MISMATCH"`.

Then, and only then:

```
M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED
```

**Recording the token is not acceptance of M3.1.** M3.1B — Gate F and zero-request readiness — must
still complete, and the M3.1 independent review must still pass.

---

# Part II — M3.3A execution rehearsal (E1–E8)

**These scenarios belong to M3.3A because that is the phase that builds the candidate-snapshot
builder.** They cannot run at M3.1: the production paths do not exist there.

## 7. What the execution rehearsal must cover

| # | Capability | Scenario |
|---|---|---|
| 1 | Deterministic snapshot construction and freeze | E1 |
| 2 | Every Decision 019 §9 snapshot-validation obligation | E2 |
| 3 | Plain/dashed accession disagreement | E2 |
| 4 | Feasible selection | E3 |
| 5 | Infeasible and node-limit fail-closed behaviour | E4 |
| 6 | Reserves, dispositions, and total coverage | E5 |
| 7 | Persistence and reconstruction, with mismatch refusal | E6 |
| 8 | Selection-result sealing and manifest atomicity | E7 |
| 9 | S6 manifest construction and file/database atomicity | E7 |
| 10 | Write-free replay and identical-root replay | E8 |
| 11 | Decision 023 **O1** behaviour | E8 |

## 8. Execution scenario matrix

---

### E1 — Deterministic snapshot freeze

| Field | Specification |
|---|---|
| **Setup** | A complete synthetic or real-shaped metadata set sufficient to freeze a snapshot; deterministic as-of inputs supplied explicitly; isolated data root |
| **Expected command** | `m3 rehearse-execution --scenarios E1` |
| **Expected response** | The snapshot freezes and receives its identity |
| **Expected reason code** | `PILOT_CANDIDATE_SNAPSHOT_FROZEN` |
| **Expected persisted state** | Candidate snapshot, entity, accession, registrant, and evidence rows written; the snapshot marked frozen and thereafter **immutable** |
| **Expected files** | none beyond the catalog |
| **Expected receipt** | `invocation_mode = "offline_execution"`; `resulting_snapshot_id` recorded; actual network counts `0` |
| **Expected rollback** | A failed freeze leaves **no** partial snapshot — the transaction is atomic |
| **Expected recovery** | Re-attempt from the same inputs; the identity must be identical |
| **Expected validation** | **Freezing twice from identical inputs yields an identical `snapshot_id`**; the frozen snapshot rejects mutation; the declared candidate-table component digests agree with the rows the snapshot actually contains (limitation **D021-L2**) |

---

### E2 — Snapshot-validation refusal

| Field | Specification |
|---|---|
| **Setup** | One fixture per Decision 019 §9 obligation, each violated in isolation — including the four storage-to-pure-input mappings (amendment-linkage evidence, multi-registrant aggregation, explicit pre-study support provenance, former-name identity evidence) — plus a fixture where the **plain and canonical dashed accession disagree** |
| **Expected command** | `m3 rehearse-execution --scenarios E2` |
| **Expected response** | The freeze **fails closed** on every variant |
| **Expected reason code** | `PILOT_CANDIDATE_SNAPSHOT_INVALIDATED`; plus `REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE`, `REVIEW_AMENDMENT_PARENT_UNRESOLVED`, and `REVIEW_REGISTRANT_CIK_UNRESOLVED` on the respective variants. Plain/dashed disagreement raises `GateFailureError` |
| **Expected persisted state** | **No** frozen snapshot in any variant; the catalog unchanged |
| **Expected files** | none |
| **Expected receipt** | `completion_status = "failed"` with the refusal reason |
| **Expected rollback** | The transaction rolls back; no partial snapshot survives |
| **Expected recovery** | **None is authorized.** A validation failure is a stop-and-report condition |
| **Expected validation** | **Every §9 obligation is exercised individually**, and none is vacuous — each fixture must fail for its own stated reason, not incidentally. **Plain-to-dashed consistency fails closed on disagreement**, per Decision 018 §5 |

---

### E3 — Feasible selection

| Field | Specification |
|---|---|
| **Setup** | A synthetic candidate set satisfying the frozen quotas, including the four boundary controls |
| **Expected command** | `m3 rehearse-execution --scenarios E3` |
| **Expected response** | The joint entity–accession selection succeeds and the run reaches `feasible` |
| **Expected reason code** | `ELIGIBLE_ORIGINAL_10K`, `ELIGIBLE_TRANSITION_10KT`, `SUPPORT_ONLY`, `PILOT_ACCESSION_PRE_STUDY_SUPPORT`, and `PILOT_ENGINEERING_ONLY_STRESS_CASE` on the respective records |
| **Expected persisted state** | Selected entities and accessions with roles and `selected_order`; quota contributions; quota results and members; the run transitioning `running -> feasible` as the **last** statement of one transaction |
| **Expected files** | none beyond the catalog |
| **Expected receipt** | `resulting_selection_run_id` recorded |
| **Expected rollback** | A fault anywhere in the window rolls back the **entire** selection — no partial selection is ever visible |
| **Expected recovery** | Re-run from the same frozen snapshot; the identity must be identical |
| **Expected validation** | Exactly the frozen pilot shape; `selected_order` deterministic; the Decision 013 §5 objective order unchanged; canonical dashed accession used for hashing and plain accession for foreign keys |

---

### E4 — Infeasible and node-limit fail-closed behaviour

| Field | Specification |
|---|---|
| **Setup** | (a) a candidate set that cannot satisfy the frozen quotas; (b) a set that exhausts the node limit; plus variants producing each governed review disposition |
| **Expected command** | `m3 rehearse-execution --scenarios E4` |
| **Expected response** | The selection **fails closed** and reports the binding constraints |
| **Expected reason code** | `PILOT_SELECTION_INFEASIBLE`; `PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN` on node-limit exhaustion; plus `PILOT_ENTITY_ACCESSION_FLOOR_UNMET`, `PILOT_ACCESSION_CAP_EXCEEDED`, `REVIEW_PILOT_QUOTA_UNMEASURABLE_AT_M23`, `REVIEW_PILOT_HISTORY_EVIDENCE_INSUFFICIENT`, and `REVIEW_PILOT_ACCESSION_ROLE_UNCLASSIFIED` on the respective variants |
| **Expected persisted state** | The run recorded in its terminal non-feasible state; **no** manifest; **no** seal |
| **Expected files** | none |
| **Expected receipt** | `completion_status = "failed"`; the reason code recorded; **no** `selection_result_sha256` and **no** root |
| **Expected rollback** | The run is preserved in its failed state and is **never deleted** |
| **Expected recovery** | **No automatic retry** (Decision 018 §18). Infeasibility is referred, never relaxed |
| **Expected validation** | **No quota relaxed, no row dropped, no discretionary substitution** to obtain feasibility; the binding constraints reported by name |

---

### E5 — Reserve and disposition totality

| Field | Specification |
|---|---|
| **Setup** | Three variants. ***(a) SUPERSEDED FOR M3.3 REHEARSAL by accepted [Decision 074](../Decisions/decision_074_m3_3_e5_reserve_rehearsal_and_real_linkage_gate.md) §2.1, Ruling R31**: requiring every selected target to hold a rank-1 package imposed a production-invalid condition, because Decision 020 §7 makes a target-specific no-compatible-reserve disposition lawful and nonblocking. (a) now proves the **positive** compatible-reserve path directly at the **pure** reserve layer, without invoking the pilot-scale joint selector. Variants (b) and (c) are unchanged.)* (a) the compatible rank-1 reserve path; (b) **no** target has one; (c) a mixed run |
| **Expected command** | `m3 rehearse-execution --scenarios E5` |
| **Expected response** | All three runs are lawful, feasible, and **manifest-eligible** |
| **Expected reason code** | (b) and (c) record `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` per uncovered target; `PILOT_RESERVE_UNAVAILABLE` and `PILOT_RESERVE_SIGNATURE_INCOMPATIBLE` on the eligibility variants |
| **Expected persisted state** | Exactly one rank-1 package **or** exactly one disposition per selected target — never both, never neither, never two |
| **Expected files** | none beyond the catalog |
| **Expected receipt** | `resulting_selection_run_id` recorded |
| **Expected rollback** | Reserves are written inside the same single `running` window; a fault rolls back the whole window |
| **Expected recovery** | Re-run from the same snapshot; reserve ordering must be identical |
| **Expected validation** | Item 70's total per-target coverage holds in all three; Decision 022's item-46 applicability holds — rank rendered **once per persisted package**, **structurally not applicable** for a disposition-only target; **no synthetic package, `reserve_rank = 0`, `null`, `"N/A"`, placeholder, or invented rank** is created or serialized |

---

### E6 — Reconstruction mismatch refusal

| Field | Specification |
|---|---|
| **Setup** | A persisted run whose stored identity is deliberately corrupted after sealing, one field at a time across every `JointSelectionRunIdentity` field |
| **Expected command** | `m3 rehearse-execution --scenarios E6` |
| **Expected response** | **Both** public reconstruction entry points **fail closed** on the same corruption |
| **Expected reason code** | A `GateFailureError` naming the disagreeing field |
| **Expected persisted state** | Unchanged — reconstruction is read-only and repairs nothing |
| **Expected files** | none |
| **Expected receipt** | `completion_status = "failed"` with the mismatch reason |
| **Expected rollback** | none — nothing was written |
| **Expected recovery** | **None is authorized.** Stored identity corruption is a stop-and-report condition |
| **Expected validation** | The single centralized identity comparison covers **every** field; neither entry point is more permissive than the other; no path silently repairs, coerces, or ignores a mismatch |

---

### E7 — Seal and manifest atomicity

| Field | Specification |
|---|---|
| **Setup** | A feasible run, with faults injected: **(a)** before the document is written; **(b)** part-way through the write; **(c)** after the write but before the row commits; **(d)** the written document then deleted; **(e)** truncated; **(f)** byte-modified |
| **Expected command** | `m3 rehearse-execution --scenarios E7`, then the verification entry point |
| **Expected response** | Every variant fails closed |
| **Expected reason code** | A `GateFailureError` naming the write fault or the document mismatch; `RAW_FILE_CHECKSUM_MISMATCH` where a stored-object check applies; `PILOT_MANIFEST_HASH_NOT_APPROVED` remains the manifest's approval state throughout |
| **Expected persisted state** | **No** `pilot_manifest_versions` row in (a)–(c). `selection_result_sha256` remains sealed and unchanged — sealing happens in its own prior transaction and is append-once. In (d)–(f) the manifest row is **unchanged**; verification repairs nothing and deletes nothing |
| **Expected files** | **No newly created document survives** a fault in (a)–(c); a **pre-existing** file at that exact content-derived path is **not** deleted — limitation **D023-O3**. In (d)–(f) files are left exactly as found |
| **Expected receipt** | `completion_status = "failed"`; **no** `resulting_root_manifest_sha256` and **no** `resulting_manifest_id` on the fault variants |
| **Expected rollback** | Row and file are atomic together: a fault leaves neither a new row nor a new file |
| **Expected recovery** | An authorized retry re-constructs through the normal path and must produce the **identical** root and **identical** document bytes |
| **Expected validation** | Atomicity governs artifacts **the operation created**; verification fails closed on wrong bytes and never trusts the file over the persisted rows; no partial manifest is ever visible |

---

### E8 — Identical replay and Decision 023 O1 handling

| Field | Specification |
|---|---|
| **Setup** | Two parts. **(a) Replay:** a complete successful run from E3/E5, replayed twice, plus two clean rebuilds from the same frozen snapshot. **(b) O1:** a fixture in which a milestone-plan §10 item's **sole** serialized carrier family is empty |
| **Expected command** | `m3 rehearse-execution --scenarios E8` |
| **Expected response** | **(a)** replay reads, reconstructs, compares, and returns. **(b)** the document **fails closed** |
| **Expected reason code** | **(a)** none. **(b)** a `GateFailureError` naming the unplaceable item |
| **Expected persisted state** | **(a)** **byte-identical** before and after each replay — **zero** writes: no `INSERT`, `UPDATE`, `DELETE`, or `INSERT OR REPLACE`. **(b)** no manifest row |
| **Expected files** | **(a)** unchanged; no file created, rewritten, or removed. **(b)** no document |
| **Expected receipt** | **(a)** a receipt **is** produced and records the same resulting identities; the receipt is the **only** thing differing between two replays. **(b)** `completion_status = "failed"` |
| **Expected rollback** | **(b)** the transaction rolls back; nothing partial survives |
| **Expected recovery** | **(b)** **none is authorized.** O1 is a **stop-and-refer** condition for an owner ruling — never resolved by reclassifying an item, adding a category, or changing a count |
| **Expected validation** | **Two clean rebuilds from the same frozen snapshot produce identical entity selections, accession selections, reserve ordering, quota results, and root manifest hash.** An identical re-seal is idempotent; a **differing** seal is refused. **Unchanged governed state plus byte-identical canonical serialization produces the same root** — regeneration alone never changes it. **(b)** confirms O1 fails closed as designed and is referred, not resolved |

---

## 9. Execution pass criteria

The M3.3A rehearsal passes when **all** hold:

1. all eight scenarios E1–E8 implemented and executed — none skipped, `xfail`ed, or disabled;
2. every scenario's observed outcome equals its expected outcome, field by field;
3. every observed reason code equals its expected code and is a **registered** code;
4. no socket was opened;
5. no accepted S4, S5, or S6 module was modified to make a scenario pass;
6. **E8 demonstrates that regenerating from unchanged state reproduces the identical root**;
7. **E8's O1 fixture fails closed and is referred, not resolved**;
8. re-running the whole rehearsal from the same fixtures reproduces the same results;
9. the M3.3A independent review passes.

**Only then may M3.3B freeze a real snapshot.**

## 10. Failure handling — both rehearsals

A failing scenario is a **finding**, not a retry target.

1. **Stop.** Do not re-run until it passes.
2. Record the scenario, the expected and observed values field by field, and the reason code.
3. Classify: a **specification** defect (this document is wrong), an **implementation** defect (the
   harness is wrong), or an **architecture** finding (the accepted code behaves differently than the
   plan assumed).
4. An architecture finding is **referred**, never resolved by adjusting the scenario until it passes.
5. Correct under the relevant bounded contract, then re-run the **whole** rehearsal for that phase —
   not just the failing scenario.

## 11. What this specification does not do

It does not implement either rehearsal, run either, authorize running either, or create a harness. It
changes no production code, test, migration, configuration, or accepted behaviour. **No scenario in
this document has been executed.**
