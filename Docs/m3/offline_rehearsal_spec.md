# Milestone 3.1A — Offline Operator-Workflow Rehearsal Specification

**Status:** specification only. **The rehearsal has not been implemented and has not been run.**
**Phase:** M3.1A. **Network permission:** `NONE` — no socket is opened.
**Controlling record:** [Decision 027](../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§8. **Plan:** [`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md),
phase M3.1.
**Completion token (future):** `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED`

---

## 1. Why the rehearsal exists

The first live SEC run is the worst possible place to discover that an interruption between a
raw-store write and a catalog commit leaves an orphan, that a duplicate body creates a second object,
or that a schema change silently defaults a field. Those failures are cheap to produce on demand
offline and nearly impossible to produce on demand live.

**The rehearsal is one end-to-end exercise of the whole operator workflow, against scripted responses
and synthetic fixtures, with every failure mode injected deliberately.** It proves the workflow, not
the data.

## 2. Global rehearsal constraints

1. **No socket is opened.** The rehearsal asserts this, rather than assuming it.
2. **No live SEC data is used.** Every response is scripted; every fixture is synthetic.
3. **Deterministic clock inputs.** Wherever an operational timestamp is required, it is supplied
   explicitly. **Nothing reads the system clock into a recorded identity.**
4. **Deterministic request ordering.** The planned order is a property of the plan, not of iteration
   order, dictionary order, or arrival order, and is asserted as stable across runs.
5. **An isolated synthetic data root.** Never the machine's default data root, never a personal path.
6. **Every scenario is implemented and runs.** None may be skipped, `xfail`ed, or conditionally
   disabled. An unimplemented scenario is a phase failure.
7. **Reason codes come from the registered registry.** A scenario that needs a code the registry does
   not contain is a stop-and-report condition, not licence to add one.
8. **Receipts are produced for every rehearsal command**, with `invocation_mode = "rehearsal"`.
9. **No accepted S4, S5, or S6 module is modified** to make a scenario pass. The rehearsal exercises
   the accepted code; it does not adapt it.

## 3. What the rehearsal must cover

Every item below appears in at least one scenario in §5, and the coverage map in §6 states where.

| # | Capability |
|---|---|
| 1 | Planned request generation |
| 2 | Deterministic request ordering |
| 3 | Request-budget construction |
| 4 | Deterministic rate limiting |
| 5 | Retry scheduling |
| 6 | Response classifications |
| 7 | Content-addressed raw storage |
| 8 | Raw-object provenance |
| 9 | Duplicate response handling |
| 10 | Schema-drift refusal |
| 11 | Snapshot freezing |
| 12 | Entity selection |
| 13 | Accession selection |
| 14 | Reserves |
| 15 | Dispositions |
| 16 | S5 persistence |
| 17 | S5 reconstruction |
| 18 | S5 replay |
| 19 | Selection-result sealing |
| 20 | S6 manifest construction |
| 21 | Canonical serialization |
| 22 | Manifest verification |
| 23 | Identical replay |
| 24 | Injected interruption |
| 25 | Transaction rollback |
| 26 | File and database atomicity |
| 27 | Interrupted-run recovery |
| 28 | Execution-receipt production |
| 29 | Proof that operational receipt content does not enter governed identities |

## 4. Fixture and injection design

**Scripted responses.** A response script is a deterministic, ordered mapping from
`request_identity(source_id, normalized_url, parameters)` and attempt ordinal to a synthetic
`(status, headers, body)` triple. The same script always produces the same sequence.

**Synthetic fixtures.** Candidate, entity, accession, evidence, reserve, and disposition fixtures are
constructed in the shape the accepted loaders expect, with explicit values for every field the
accepted identity functions consume. **No fixture is derived from a real filing, a real registrant,
or any real SEC payload.**

**Injection points.** The rehearsal harness injects at exactly five places, all of which the accepted
architecture already exposes as boundaries:

| Injection | Where |
|---|---|
| Response substitution | The transport boundary — the harness supplies responses instead of a client |
| Clock substitution | The explicit clock argument the rate limiter and any timestamped output already take |
| Interruption | A named abort point, raised as an exception between two identified statements |
| Filesystem fault | A write that raises after `n` bytes, or a file removed between write and verification |
| Payload mutation | A field added, removed, nulled, or retyped in a scripted body, to produce drift |

**No injection modifies production code.** Each is a test-time substitution at an existing seam.

## 5. Scenario matrix

Twenty scenarios. Each specifies setup, expected command, expected response, expected reason code,
expected persisted state, expected files, expected receipt, expected rollback, expected recovery, and
expected validation.

Throughout: `R#` denotes the scenario identifier; "no rollback" means the scenario is not expected to
roll back anything, and an observed rollback is a failure.

---

### R1 — All-success path

| Field | Specification |
|---|---|
| **Setup** | Full synthetic plan across every registered route; every scripted response `200` with a well-formed body of the route's expected content kind; empty data root; empty catalog at migration `0013` |
| **Expected command** | `m3 plan-requests` then `m3 rehearse --scenarios R1` |
| **Expected response** | Every logical request classified `proceed`; physical attempts equal logical requests |
| **Expected reason code** | none — success carries no failure code; `SOURCE_CONTENT_UPDATED` recorded per newly stored object |
| **Expected persisted state** | One source-observation row per logical request, each with its validated single-hop chain; parsed source records with parser version and `parser_state` complete; no quarantine row |
| **Expected files** | One content-addressed raw object per logical request, each with its `.lineage.json` sibling; **zero** `.part` files |
| **Expected receipt** | `completion_status = "complete"`; `actual_logical_request_count == planned_logical_request_count`; `actual_physical_attempt_count == actual_logical_request_count`; response-classification totals all in `proceed`; `schema_drift_outcome = "none"` |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | Planned equals actual per route; every object verifies against its `content_sha256`; every observation has complete provenance; the plan hash is unchanged from the dry run |

---

### R2 — Retry then success

| Field | Specification |
|---|---|
| **Setup** | One route scripted `503, 503, 200`; all others `200` |
| **Expected command** | `m3 rehearse --scenarios R2` |
| **Expected response** | Attempts 1 and 2 classify `retry` with backoff `1.0 s` then `2.0 s`; attempt 3 classifies `proceed` |
| **Expected reason code** | none terminal — a retryable action carries no reason code while it is still retryable |
| **Expected persisted state** | **One** source observation for the route, not three; the retry ordinals recorded on the attempt record |
| **Expected files** | **One** raw object for that route; no partial file left behind |
| **Expected receipt** | `actual_logical_request_count` unchanged by the retries; `actual_physical_attempt_count` exceeds it by exactly 2; classification totals show two `retry` and one `proceed` |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | A retry consumes **no** additional logical request and **exactly one** additional physical attempt; the backoff delays are exponential from a 1.0 s base and never exceed the 60 s ceiling |

---

### R3 — Governed non-success response

Four sub-cases, all required.

| Field | Specification |
|---|---|
| **Setup** | (a) `429` **with** `Retry-After: 3`; (b) `429` **without** `Retry-After`; (c) `403`; (d) `200` whose body carries a block-page signature |
| **Expected command** | `m3 rehearse --scenarios R3` |
| **Expected response** | (a) `retry_after`, delay `3.0 s`, aggregate traffic **not** halted; (b) `cooldown`, delay `600 s`, aggregate traffic halted; (c) `cooldown`, delay `600 s`, halted; (d) `cooldown`, delay `600 s`, halted |
| **Expected reason code** | (a) none while retryable; (b) none on the cooldown action itself, `SEC_RETRIES_EXHAUSTED` if terminal; (c) `SEC_BLOCK_PAGE`; (d) `SEC_BLOCK_PAGE` |
| **Expected persisted state** | The attempt and its classification recorded; **no** partial or empty observation promoted to usable; a second cooldown terminates the retrieval as failed |
| **Expected files** | No raw object for a non-`proceed` outcome; nothing empty stored |
| **Expected receipt** | Classification totals name each class explicitly; `completion_status = "failed"` where the retrieval terminated; `reason_code` set |
| **Expected rollback** | Per the accepted order: stop new requests, mark failed, preserve attempts, roll back the uncommitted transaction |
| **Expected recovery** | An explicit resume decision is required; **no automatic resume** |
| **Expected validation** | **A failure never becomes a valid empty result**; exactly one controlled post-cooldown request is permitted and a second cooldown is terminal; the aggregate halt stops **all** traffic, not just the observing worker |

---

### R4 — Request-budget exhaustion

| Field | Specification |
|---|---|
| **Setup** | A plan whose maximum physical attempts exceed a deliberately low injected hard ceiling; every response `200` |
| **Expected command** | `m3 rehearse --scenarios R4` |
| **Expected response** | The run **refuses to place the attempt that would exceed the ceiling** and stops |
| **Expected reason code** | A registered code naming budget exhaustion; if the registry contains none, **stop and report** — the rehearsal does not invent one, and the gap is referred for a decision before M3.2 |
| **Expected persisted state** | Every object retrieved before the stop is committed and provenanced; the run is marked failed with the remaining plan recorded as unattempted |
| **Expected files** | Raw objects for the completed retrievals only; no partial file |
| **Expected receipt** | `completion_status = "stopped_at_ceiling"`; `actual_physical_attempt_count` **strictly less than** `approved_request_ceiling`; the remaining planned count recorded |
| **Expected rollback** | Stop-and-preserve, never delete |
| **Expected recovery** | Resume is permitted **only** after a new owner-approved ceiling; the consumed count carries forward |
| **Expected validation** | **Stop-before-overflow, never stop-after.** The ceiling is never raised by the run itself |

---

### R5 — Schema-drift refusal

Two sub-cases, both required.

| Field | Specification |
|---|---|
| **Setup** | (a) a scripted body with one **extra unknown** field; (b) a scripted body with a **required field missing**, plus variants for an unexpected null, a changed type, and a malformed nested array |
| **Expected command** | `m3 rehearse --scenarios R5` |
| **Expected response** | (a) the unknown field is **retained and logged**, processing continues; (b) processing **stops** and evidence is preserved |
| **Expected reason code** | (a) `PARSER_SCHEMA_DRIFT_OBSERVED`; (b) `SEC_SCHEMA_REQUIRED_FIELD_MISSING`, with `PARSER_STRUCTURE_NULL`, `PARSER_STRUCTURE_WRONG_TYPE`, and `PARSER_STRUCTURE_MALFORMED` for the respective variants |
| **Expected persisted state** | (a) the drift event recorded, the record parsed; (b) **no** parsed record admitted, the raw object preserved, the drift event recorded as blocking |
| **Expected files** | The raw object is retained in both cases — evidence is never deleted |
| **Expected receipt** | `schema_drift_outcome = "unknown_fields_retained"` for (a) and `"blocked"` for (b); `completion_status = "failed"` for (b) |
| **Expected rollback** | (b) rolls back the uncommitted transaction and preserves the object |
| **Expected recovery** | (b) requires a [`schema_drift_incident.md`](templates/schema_drift_incident.md) record and an **owner ruling**; no resume until ruled |
| **Expected validation** | **No default is supplied, no type is coerced, and no row is dropped.** A new historical-file reference is a recorded drift event and does not silently expand the plan |

---

### R6 — Interruption before the raw-store write

| Field | Specification |
|---|---|
| **Setup** | Abort injected after the response is fully received and classified `proceed`, but **before** any byte reaches the raw store |
| **Expected command** | `m3 rehearse --scenarios R6` |
| **Expected response** | The retrieval terminates as interrupted |
| **Expected reason code** | `RAW_PARTIAL_DOWNLOAD` where a stream was in flight; otherwise the interruption reason recorded on the run |
| **Expected persisted state** | **No** source-observation row for that retrieval; the catalog is exactly as it was before the retrieval began |
| **Expected files** | **No** raw object and **no** `.part` file for that identity |
| **Expected receipt** | `completion_status = "interrupted"`; `interruption_state = "before_raw_store_write"`; the object count unchanged |
| **Expected rollback** | Nothing to roll back beyond the uncommitted transaction |
| **Expected recovery** | Safe-resume determination `SAFE`; the retrieval is simply re-planned and re-attempted |
| **Expected validation** | The catalog and the raw store are **byte-identical** to the pre-retrieval state |

---

### R7 — Interruption after the raw-store write but before the catalog commit

| Field | Specification |
|---|---|
| **Setup** | Abort injected after the raw object is promoted and fsynced, but **before** the catalog transaction commits |
| **Expected command** | `m3 rehearse --scenarios R7` |
| **Expected response** | The retrieval terminates as interrupted |
| **Expected reason code** | The interruption reason on the run; `SOURCE_SNAPSHOT_REUSE_UNRECONCILED` if a later pass finds the object without its row |
| **Expected persisted state** | **No** committed catalog row — the transaction rolled back |
| **Expected files** | The raw object **exists** on disk with its lineage sibling. It is an **orphan**, and orphan adoption is the only permitted resolution: recovery either adopts the valid orphan or quarantines it. **It is never deleted** |
| **Expected receipt** | `completion_status = "interrupted"`; `interruption_state = "after_raw_store_write_before_catalog_commit"` |
| **Expected rollback** | The uncommitted transaction rolls back; **the file is preserved** |
| **Expected recovery** | Safe-resume `SAFE`; recovery adopts the orphan if it verifies against its `content_sha256` and its lineage intent, otherwise quarantines it and records the reason |
| **Expected validation** | **This is the scenario the whole rehearsal exists for.** It must produce exactly one orphan, exactly one adoption or quarantine, and **no** duplicate object and **no** duplicate row after recovery |

---

### R8 — Interruption after the catalog commit

| Field | Specification |
|---|---|
| **Setup** | Abort injected immediately after the catalog transaction commits and before the next retrieval begins |
| **Expected command** | `m3 rehearse --scenarios R8` |
| **Expected response** | The run terminates as interrupted with that retrieval **complete** |
| **Expected reason code** | The interruption reason on the run |
| **Expected persisted state** | The committed row is present and complete; the JSONL audit projection may lag and is rebuilt from SQLite at recovery |
| **Expected files** | The raw object and its lineage present, matching the committed row |
| **Expected receipt** | `completion_status = "interrupted"`; `interruption_state = "after_catalog_commit"`; the completed retrieval counted |
| **Expected rollback** | None for the committed retrieval |
| **Expected recovery** | Safe-resume `SAFE`; the completed retrieval is **not** re-attempted, and the projection is reconstructed from the authoritative SQLite catalog |
| **Expected validation** | Resume issues **zero** requests for the already-committed retrieval; the rebuilt projection matches SQLite exactly |

---

### R9 — Duplicate raw object

Two sub-cases, both required.

| Field | Specification |
|---|---|
| **Setup** | (a) the same logical request returning a **byte-identical** body twice; (b) the same logical request returning a **different** body on the second retrieval |
| **Expected command** | `m3 rehearse --scenarios R9` |
| **Expected response** | Both classify `proceed` |
| **Expected reason code** | (a) `SOURCE_CONTENT_UNCHANGED` and `SOURCE_SNAPSHOT_REUSED`; (b) `REMOTE_CONTENT_CHANGED`, plus `SOURCE_DATED_ARTIFACT_CHANGED` for a closed-quarter dated snapshot and `SOURCE_IMMUTABLE_IDENTITY_MUTATED` for an immutable identity |
| **Expected persisted state** | (a) **one** object, a reuse recorded, no second object; (b) a **new observation**, with the earlier observation retained and the supersession lineage recorded |
| **Expected files** | (a) exactly one raw object; (b) two raw objects — **the first is never overwritten** |
| **Expected receipt** | `duplicate_object_count` incremented for (a); `raw_object_count` incremented for (b) |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | **A differing later response is always a new observation and never an overwrite** (CLAUDE.md rule 6); a changed body at an immutable identity or a closed dated snapshot is an **anomaly requiring review**, not an ordinary update |

---

### R10 — Restart and resume

| Field | Specification |
|---|---|
| **Setup** | Run R6, R7, and R8 in sequence, then restart from the recorded predecessor receipt |
| **Expected command** | `m3 recovery-state`, then `m3 rehearse --scenarios R10` resuming from the predecessor receipt |
| **Expected response** | Recovery reports `SAFE`; the resumed run completes the remaining plan |
| **Expected reason code** | Whatever each recovered retrieval carries; `AUDIT_PROJECTION_INCOMPLETE` if a projection rebuild was required |
| **Expected persisted state** | Exactly the state a single uninterrupted run would have produced — no more rows and no fewer |
| **Expected files** | Exactly the object set a single uninterrupted run would have produced; **zero** `.part` files; every orphan adopted or quarantined |
| **Expected receipt** | The resumed receipt names its `recovery_predecessor_receipt_id`; the consumed request count carries forward against the **same** ceiling |
| **Expected rollback** | none beyond what R6–R8 already performed |
| **Expected recovery** | This scenario **is** the recovery |
| **Expected validation** | **Duplicate-prevention proof**: the resumed run issues no request for an already-committed retrieval, and the final state equals the uninterrupted-run state exactly |

---

### R11 — Candidate-snapshot freeze

| Field | Specification |
|---|---|
| **Setup** | A complete synthetic metadata set sufficient to freeze a snapshot; deterministic as-of inputs supplied explicitly |
| **Expected command** | `m3 rehearse --scenarios R11` |
| **Expected response** | The snapshot freezes and receives its identity |
| **Expected reason code** | `PILOT_CANDIDATE_SNAPSHOT_FROZEN`; `PILOT_CANDIDATE_SNAPSHOT_INVALIDATED` on the negative variant |
| **Expected persisted state** | Candidate snapshot, entity, accession, registrant, and evidence rows written; the snapshot marked frozen and thereafter **immutable** |
| **Expected files** | none beyond the catalog |
| **Expected receipt** | `resulting_snapshot_id` recorded |
| **Expected rollback** | A failed freeze leaves **no** partial snapshot — the transaction is atomic |
| **Expected recovery** | A failed freeze is re-attempted from the same inputs and must produce the **same** identity |
| **Expected validation** | Every Decision 019 §9 snapshot-freeze obligation is exercised, including the four storage-to-pure-input mappings; freezing twice from identical inputs yields an identical `snapshot_id`; the frozen snapshot rejects mutation |

---

### R12 — No feasible selection, or a governed review path

| Field | Specification |
|---|---|
| **Setup** | A synthetic candidate set that cannot satisfy the frozen quotas; plus variants producing each governed review disposition |
| **Expected command** | `m3 rehearse --scenarios R12` |
| **Expected response** | The selection **fails closed** and reports the binding constraints |
| **Expected reason code** | `PILOT_SELECTION_INFEASIBLE` or `PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN`; plus `PILOT_ENTITY_ACCESSION_FLOOR_UNMET`, `PILOT_ACCESSION_CAP_EXCEEDED`, `REVIEW_PILOT_QUOTA_UNMEASURABLE_AT_M23`, `REVIEW_PILOT_HISTORY_EVIDENCE_INSUFFICIENT`, and `REVIEW_PILOT_ACCESSION_ROLE_UNCLASSIFIED` on the respective variants |
| **Expected persisted state** | The run recorded in its terminal non-feasible state; **no** manifest; **no** seal |
| **Expected files** | none |
| **Expected receipt** | `completion_status = "failed"`; the reason code recorded; **no** `selection_result_sha256` and **no** root |
| **Expected rollback** | The run is preserved in its failed state and is **never deleted** |
| **Expected recovery** | **No automatic retry** (Decision 018 §18). Infeasibility is referred, never relaxed |
| **Expected validation** | **No quota is relaxed, no row is dropped, and no discretionary substitution occurs to obtain feasibility**; the binding constraints are reported by name |

---

### R13 — Feasible selection

| Field | Specification |
|---|---|
| **Setup** | A synthetic candidate set that satisfies the frozen quotas, including the four boundary controls |
| **Expected command** | `m3 rehearse --scenarios R13` |
| **Expected response** | The joint entity–accession selection succeeds and the run reaches `feasible` |
| **Expected reason code** | `ELIGIBLE_ORIGINAL_10K`, `ELIGIBLE_TRANSITION_10KT`, `SUPPORT_ONLY`, `PILOT_ACCESSION_PRE_STUDY_SUPPORT`, and `PILOT_ENGINEERING_ONLY_STRESS_CASE` on the respective records |
| **Expected persisted state** | Selected entities and accessions with roles and `selected_order`; quota contributions; quota results and members; the run transitioning `running -> feasible` as the **last** statement of one transaction |
| **Expected files** | none beyond the catalog |
| **Expected receipt** | `resulting_selection_run_id` recorded |
| **Expected rollback** | A fault anywhere in the window rolls back the **entire** selection — no partial selection is ever visible |
| **Expected recovery** | Re-run from the same frozen snapshot; the identity must be identical |
| **Expected validation** | Exactly the frozen pilot shape; `selected_order` deterministic; the objective order unchanged from Decision 013 §5; canonical dashed accession used for hashing and plain accession for foreign keys, with a fail-closed check on disagreement |

---

### R14 — Reserve and disposition coverage

Three sub-cases, all required.

| Field | Specification |
|---|---|
| **Setup** | (a) every selected target has a compatible rank-1 reserve package; (b) **no** target has one; (c) a mixed run |
| **Expected command** | `m3 rehearse --scenarios R14` |
| **Expected response** | All three runs are lawful, feasible, and **manifest-eligible** |
| **Expected reason code** | (b) and (c) record `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` per uncovered target; `PILOT_RESERVE_UNAVAILABLE` and `PILOT_RESERVE_SIGNATURE_INCOMPATIBLE` on the eligibility variants |
| **Expected persisted state** | Exactly one rank-1 package **or** exactly one disposition per selected target — never both, never neither, never two |
| **Expected files** | none beyond the catalog |
| **Expected receipt** | `resulting_selection_run_id` recorded; reserves are **not** counted as objects |
| **Expected rollback** | Reserves are written inside the same single `running` window; a fault rolls back the whole window |
| **Expected recovery** | Re-run from the same snapshot; reserve ordering must be identical |
| **Expected validation** | Item 70's total per-target coverage holds in all three; Decision 022's item-46 applicability holds — rank is rendered **once per persisted package** and is **structurally not applicable** for a disposition-only target; **no synthetic package, `reserve_rank = 0`, `null`, `"N/A"`, placeholder, or invented rank is created or serialized** |

---

### R15 — Reconstruction mismatch

| Field | Specification |
|---|---|
| **Setup** | A persisted run whose stored identity is deliberately corrupted after sealing, one field at a time across every `JointSelectionRunIdentity` field |
| **Expected command** | `m3 rehearse --scenarios R15` |
| **Expected response** | **Both** public reconstruction entry points **fail closed** on the same corruption |
| **Expected reason code** | A `GateFailureError` naming the disagreeing field |
| **Expected persisted state** | Unchanged — reconstruction is read-only and repairs nothing |
| **Expected files** | none |
| **Expected receipt** | `completion_status = "failed"` with the mismatch reason |
| **Expected rollback** | none — nothing was written |
| **Expected recovery** | **None is authorized.** Stored identity corruption is a stop-and-report condition |
| **Expected validation** | The single centralized identity comparison covers **every** field; neither entry point is more permissive than the other; no path silently repairs, coerces, or ignores a mismatch |

---

### R16 — Manifest-write fault

| Field | Specification |
|---|---|
| **Setup** | A feasible sealed run; a filesystem fault injected (a) before the document is written, (b) part-way through the write, and (c) after the write but before the row commits |
| **Expected command** | `m3 rehearse --scenarios R16` |
| **Expected response** | Every variant fails closed |
| **Expected reason code** | A `GateFailureError` naming the write fault; `PILOT_MANIFEST_HASH_NOT_APPROVED` remains the manifest's approval state throughout |
| **Expected persisted state** | **No** `pilot_manifest_versions` row in any variant. `selection_result_sha256` remains sealed and unchanged — sealing happens in its own prior transaction and is append-once |
| **Expected files** | **No newly created document file survives.** A file the operation created is removed; a **pre-existing** file at that exact content-derived path is **not** deleted — limitation **O3** |
| **Expected receipt** | `completion_status = "failed"`; **no** `resulting_root_manifest_sha256` and **no** `resulting_manifest_id` |
| **Expected rollback** | Row and file are atomic together: a fault leaves neither a new row nor a new file |
| **Expected recovery** | An authorized retry re-constructs through the normal path and must produce the **identical** root |
| **Expected validation** | Atomicity governs artifacts **the operation created**; verification fails closed on wrong bytes; no partial manifest is ever visible |

---

### R17 — Manifest-file loss

| Field | Specification |
|---|---|
| **Setup** | A successfully written manifest whose document file is then (a) deleted, (b) truncated, and (c) byte-modified |
| **Expected command** | `m3 rehearse --scenarios R17` then the verification entry point |
| **Expected response** | Verification **fails closed** in all three variants |
| **Expected reason code** | A `GateFailureError` naming the document mismatch; `RAW_FILE_CHECKSUM_MISMATCH` for the byte-modified variant where a stored-object check applies |
| **Expected persisted state** | The manifest row is **unchanged** — verification repairs nothing and deletes nothing |
| **Expected files** | Left exactly as found; the rehearsal does not restore them |
| **Expected receipt** | `completion_status = "failed"` with the verification reason |
| **Expected rollback** | none |
| **Expected recovery** | An authorized re-serialization through the normal construction path restores the document and must reproduce the **identical** bytes and the identical root |
| **Expected validation** | The document is bound by the root, so wrong bytes are detectable; verification never trusts the file over the persisted rows |

---

### R18 — Identical replay

| Field | Specification |
|---|---|
| **Setup** | A complete successful run from R13/R14, then replay invoked twice more |
| **Expected command** | `m3 rehearse --scenarios R18` |
| **Expected response** | Replay reads, reconstructs, compares, and returns |
| **Expected reason code** | none |
| **Expected persisted state** | **Byte-identical** before and after each replay. **Zero** writes: no `INSERT`, no `UPDATE`, no `DELETE`, no `INSERT OR REPLACE` |
| **Expected files** | Unchanged; no file created, rewritten, or removed |
| **Expected receipt** | A receipt **is** produced (replay is a command) and records the same resulting identities; the receipt is the **only** thing that differs between two replays |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | Two clean rebuilds from the same frozen snapshot produce identical entity selections, accession selections, reserve ordering, quota results, and root manifest hash; an identical re-seal is idempotent; a **differing** seal is refused |

---

### R19 — Receipt redaction

| Field | Specification |
|---|---|
| **Setup** | An environment deliberately loaded with a synthetic SEC identity on a reserved example domain, a synthetic token, and an absolute path; responses carrying `Set-Cookie` and `Authorization` echo headers; bodies containing recognizable payload text |
| **Expected command** | `m3 rehearse --scenarios R19` then `m3 show-receipt` |
| **Expected response** | Every receipt is produced and passes the prohibited-field scan |
| **Expected reason code** | none on success; `4` from `m3 show-receipt` if any prohibited field is present |
| **Expected persisted state** | unchanged by the scan |
| **Expected files** | The receipt file only |
| **Expected receipt** | Contains **none** of: full SEC identity, email address, secret, API token, cookie, authorization header, raw response body, absolute personal path, candidate row, selected row, reserve row, filing text, outcome value |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | An automated scan over the serialized receipt for each prohibited class; a **positive control** — the harness constructs a receipt that *does* contain a prohibited field and asserts the scan **rejects** it, so the scan is proven non-vacuous |

---

### R20 — Receipts do not alter S5 or S6 identities

| Field | Specification |
|---|---|
| **Setup** | Two otherwise identical complete runs over the same frozen synthetic snapshot: run A with receipt emission **disabled**, run B with receipt emission **enabled**, and a third run C with receipts enabled and deliberately different operational values (different injected clock, different receipt IDs, different paths, different counts) |
| **Expected command** | `m3 rehearse --scenarios R20` |
| **Expected response** | All three runs complete |
| **Expected reason code** | none |
| **Expected persisted state** | The governed rows are identical across A, B, and C |
| **Expected files** | The manifest document bytes are identical across A, B, and C |
| **Expected receipt** | A has none; B and C have receipts that **differ from each other** — which is the point |
| **Expected rollback** | none |
| **Expected recovery** | none |
| **Expected validation** | **The non-contamination proof.** `snapshot_id`, candidate-table identities, `selection_input_sha256`, `selection_run_id`, `selection_result_sha256`, all eight component digests, `root_manifest_sha256`, and `manifest_id` are **byte-identical** across A, B, and C. Varying every operational value changes **no** governed identity and **no** document byte. A single differing identity is a phase-stopping failure |

---

## 6. Coverage map

Each capability from §3 mapped to the scenarios that exercise it. Every capability has at least one.

| Capability | Scenarios |
|---|---|
| Planned request generation | R1, R4 |
| Deterministic request ordering | R1, R10, R18 |
| Request-budget construction | R1, R4 |
| Deterministic rate limiting | R1, R2, R3 |
| Retry scheduling | R2, R3 |
| Response classifications | R1, R2, R3, R5 |
| Content-addressed raw storage | R1, R7, R9 |
| Raw-object provenance | R1, R7, R9 |
| Duplicate response handling | R9 |
| Schema-drift refusal | R5 |
| Snapshot freezing | R11 |
| Entity selection | R12, R13 |
| Accession selection | R12, R13 |
| Reserves | R14 |
| Dispositions | R14 |
| S5 persistence | R13, R14 |
| S5 reconstruction | R15, R18 |
| S5 replay | R18 |
| Selection-result sealing | R16, R18 |
| S6 manifest construction | R16, R17, R18 |
| Canonical serialization | R17, R18 |
| Manifest verification | R17 |
| Identical replay | R18, R20 |
| Injected interruption | R6, R7, R8 |
| Transaction rollback | R3, R7, R13, R16 |
| File and database atomicity | R7, R16 |
| Interrupted-run recovery | R7, R8, R10 |
| Execution-receipt production | R1–R20 |
| Receipt non-contamination | R19, R20 |

## 7. Pass criteria

The rehearsal passes when **all** of the following hold:

1. all twenty scenarios are implemented and executed — none skipped, `xfail`ed, or disabled;
2. every scenario's observed outcome equals its expected outcome, field by field, across all ten
   specified fields;
3. every observed reason code equals its expected reason code and is a **registered** code;
4. no socket was opened, asserted rather than assumed;
5. no accepted S4, S5, or S6 module was modified to make a scenario pass;
6. every receipt passes the prohibited-field scan, and the positive control proves the scan is not
   vacuous;
7. **R20's non-contamination proof holds exactly** — every governed identity byte-identical across
   all three runs;
8. re-running the whole rehearsal from the same fixtures reproduces the same results.

## 8. Failure handling

A failing scenario is a **finding**, not a retry target.

1. **Stop.** Do not re-run until it passes.
2. Record the scenario, the expected and observed values field by field, and the reason code.
3. Classify: a **specification** defect (this document is wrong), an **implementation** defect (the
   harness is wrong), or an **architecture** finding (the accepted code behaves differently than the
   plan assumed).
4. An architecture finding is **referred**, never resolved by adjusting the scenario until it passes.
5. Correct under the bounded M3.1 contract, then re-run the **whole** rehearsal — not just the failing
   scenario.

## 9. Completion token

On a full pass, and only then:

```
M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED
```

**Recording the token is not acceptance of M3.1.** M3.1B — Gate F and zero-request readiness — must
still complete, and the M3.1 independent review must still pass.

## 10. What this specification does not do

It does not implement the rehearsal, run it, authorize running it, or create the harness. It changes
no production code, test, migration, configuration, or accepted behaviour. **No scenario in this
document has been executed.**
