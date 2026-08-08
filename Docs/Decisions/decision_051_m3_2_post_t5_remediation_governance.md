# Decision 051 — M3.2 Post-T5 Remediation Governance

**Date:** 2026-08-08
**Status:** ACCEPTED — OWNER APPROVED 2026-08-08
**Authority classification:** `M3_2_POST_T5_REMEDIATION_GOVERNANCE_RECORDED`
**Type:** Governance-only record of the interrupted first M3.2A T5 invocation, the owner's
attempt-accounting adjudication, and the architecture and maximum path envelope for a later bounded
offline remediation implementation stage. **Not** a preregistration deviation. This record changes
no hypothesis, cohort window, maturity gate, outcome definition, threshold, seed, selection
methodology, governed identity, migration, implementation, test, receipt, reason code, or tracked
configuration byte.
**Amends:** the accepted
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §12 interruption, recovery, and
attempt-accounting rules and their directly consequent status metadata only.
**Narrowly supersedes:** accepted
[Decision 032](decision_032_m3_2_contract_corrections.md) F3 and accepted
[Decision 040](decision_040_m3_2_t2_4_implementation_authorization.md) §7 only to the extent they
require an automatic full-per-route `A_reachable` charge despite exact, independently verifiable
durable evidence of the physical-attempt count. Their full-bound fallback remains controlling where
the exact count is genuinely unrecorded or ambiguous.
**Preserves unchanged:** accepted
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) §8's predecessor-
receipt requirement for continuation, its no-automatic-resume rule, ceiling 801, and all withheld
authority; the frozen `m3-execution-receipt/2.0` schema; migrations `0001`–`0013`; every route,
host, method, spacing, content, provenance, leakage, and stop condition not expressly narrowed here.
**Related:** [Decision 040](decision_040_m3_2_t2_4_implementation_authorization.md);
[Decision 041](decision_041_m3_2_t2_4_recovery_state_primitive_authority.md);
[Decision 042](decision_042_m3_2_t2_4_acceptance_and_publication.md);
[Decision 046](decision_046_m3_2_t3_acceptance_and_publication.md);
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md);
[`Docs/m3/templates/interrupted_run_recovery.md`](../m3/templates/interrupted_run_recovery.md);
[`Docs/sec_data_dictionary.md`](../sec_data_dictionary.md).
**Governs:** the accepted facts from the interrupted initial T5 invocation (§3), the owner
performance and lineage rulings (§4), the accepted consumed-attempt count (§5), future attempt-
reservation and reconciliation semantics (§6), the exact remediation architecture (§7), the
receiptless-inspection boundary (§8), the old-run disposition (§9), the later remediation-stage
authority and maximum path envelope (§10), validation and independent rereview (§11), future-run
boundary (§12), withheld authority (§13), and this recording's publication boundary (§14).

---

## 1. What this record does

This record makes nine determinations that must remain separate:

1. It records the durable facts of the interrupted first M3.2A T5 invocation without changing the
   real operational catalog, raw object, lineage, lease, or receipt state.
2. It accepts **exactly one consumed physical attempt**, not six.
3. It narrows the prior conservative-accounting language only where exact durable evidence exists.
4. It accepts `ops_retrieval_attempts` as the future primary durable consumed-count surface under
   the write-ahead semantics in §6.
5. It accepts a four-part remediation architecture: the archive-path complexity correction,
   pre-send attempt reservation, scoped SIGTERM handling, and explicit receiptless inspection.
6. It authorizes that bounded remediation architecture **for a later separate implementation
   packet**. This recording does not start implementation.
7. It permanently prohibits resume of the interrupted invocation.
8. It records `stopped` as the eventual truthful terminal state, while authorizing no state
   mutation now.
9. It withholds every live, network, recovery-mutation, T6, M3.2B, and Gate H authority.

The Claude Opus discovery report is specialist evidence and recommendation only. It is not an
authority source, does not approve its own architecture, and is binding here only where this owner
record expressly accepts or modifies a finding.

## 2. Authority verification and narrow precedence ruling

The owner re-read the exact accepted authority before this record was written.

Authority identities verified before amendment:

- pre-Decision-051 `Milestones/contracts/m3_2.md` SHA-256
  `c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7`;
- Decision 032 SHA-256
  `1aa468cb4f007e919e60ba94513fdb895bb2618a483a8ad77733efd68f946974`;
- Decision 040 SHA-256
  `51c949df42d65811b2c4f220056b066fb0be9cdbcf9f1d7804e01ecfd0a539c2`;
- Decision 050 SHA-256
  `16d2445676db0c80d4e356bc3db01a2c2e667864e9f03de3a9c1cf500e0ea13e`.

### 2.1 Contract §12

The accepted contract says the full per-route `A_reachable` charge applies when a hard
interruption without a terminating receipt leaves the in-flight request's physical attempts
**unrecorded**. It also makes recovery uncertainty a stop condition.

### 2.2 Decision 040 §7

Decision 040 states a broader three-part formula whose third part charges the full registered
`A_reachable` for at most one identifiable receiptless in-flight request, and classifies a missing
predecessor chain as `UNDETERMINED`.

### 2.3 Decision 050 §8

Decision 050 requires a predecessor receipt before continuation, permits continuation only after a
`SAFE` determination, and requires a separate owner resume-or-new-run ruling.

### 2.4 Resolution

There is no unresolved authority conflict after this record:

- The word **unrecorded** in contract §12 remains load-bearing.
- Exact, accepted, independently verifiable durable evidence controls when it establishes the
  physical-attempt count without inference.
- Full `A_reachable` charging remains the conservative fallback when the exact count is genuinely
  unrecorded, unattributable, or ambiguous.
- Receiptless inspection may determine facts and consumed count, but it can never establish
  continuation eligibility.
- Decision 050's predecessor-receipt requirement remains fully binding for continuation.
- No accepted historical decision is edited in place. This later accepted record supplies the
  precise, partial supersession recorded in the decision registry.

## 3. Accepted factual findings from the interrupted T5 invocation

The following are accepted facts, not architecture recommendations:

1. Exactly one initial M3.2A live invocation occurred under Decision 050.
2. Exactly one physical SEC retrieval attempt occurred.
3. That attempt returned the bulk submissions archive successfully. The immutable raw object and its
   raw-object lineage are complete and hash-consistent.
4. The durable lineage records `attempts = 1`, HTTP 200, zero redirect hops, and a successful
   `stored_new` outcome.
5. The archive contains 985,480 entries. M3.2A's accepted lineage workload consists of 985,479 JSON
   members; the one non-JSON member is validated but is not a JSON-lineage row.
6. M3.2A was not JSON-parsing those members. It was validating the archive directory and preparing
   complete archive-member lineage.
7. No second logical request or physical request began. The sequential engine remained inside the
   first request's local archive-validation path.
8. The archive-member transaction did not commit. The real catalog contains no committed source
   observation or archive-member row for the object.
9. No terminating execution receipt was emitted. None is reconstructed by this record.
10. The ingestion-job row remained non-terminal, and the stale lease metadata remained on disk after
    the process ended.
11. The real `ops_retrieval_attempts` table contains no row for this historical attempt.
12. The preserved raw-store evidence and the catalog/receipt accounting surfaces therefore disagree,
    and the previously accepted recovery classification remains `UNDETERMINED` until a later
    separately authorized disposition.
13. Network was disabled after termination. No resume, retry, replacement invocation, T6, M3.2B, or
    Gate H operation followed.

Private evidence remains outside Git. This record contains no SEC identity, credential, response
body, private absolute path, or authorization header.

## 4. Performance and lineage rulings

### 4.1 Archive-path root cause

The apparent roughly 46-minute parser stall was an accidental quadratic descendant-collision scan
in `src/disclosure_drift/sec/archive.py`. It repeatedly scanned the growing admitted-path set for
each archive entry before yielding any member. This is an acceptance-blocking implementation defect.

The owner accepts the measured replacement: maintain the set of strict ancestor prefixes of admitted
paths and use a constant-time membership test for the reverse-order file-versus-directory collision.
The semantics, refusals, member ordering, limits, suffix filtering, and malformed-input behavior
remain unchanged. The specialist's two full real-archive lineage measurements of approximately
43.1 and 45.2 seconds are accepted as performance evidence, not as a timeless contractual constant.

### 4.2 Complete lineage retained

The full accepted JSON-member lineage remains required. No CIK, cohort, date, sample, or downstream-
use prefilter is authorized. No faster JSON decoder is relevant because M3.2A does not decode the
member JSON. No concurrency, archive extraction, checkpointing, parser-version change, schema change,
limit relaxation, or new dependency is authorized.

### 4.3 No command split

Network acquisition and archive-lineage materialization remain one governed live command. Splitting
them now would redesign invocation, receipt, recovery, and Gate H semantics to address a local stage
that completes in under a minute after the bounded defect repair. That redesign is rejected for this
remediation.

## 5. Accepted consumed-attempt ruling

~~~text
ACCEPTED_PHYSICAL_ATTEMPTS_CONSUMED: 1
APPROVED_HARD_CEILING:               801
REMAINING_CEILING_HEADROOM:          800
BULK_ROUTE_A_REACHABLE:              6
BULK_ROUTE_REMAINING_HEADROOM:       5
COMMITTED_LOGICAL_REQUESTS:          0
~~~

The correct charge is **1**, not 6:

- the raw lineage durably records exactly one attempt;
- it records no redirect and no retry;
- the sequential call path proves the process remained in local archive validation before another
  request could begin;
- the accepted preserved facts already state that exactly one physical request occurred.

Charging six would replace an established fact with five requests that did not occur. That is not
conservative uncertainty accounting; it is contrary to the accepted evidence hierarchy.

The historical attempt is **not** backfilled into `ops_retrieval_attempts`. Decision 051 plus the
verified immutable raw lineage is the accepted one-time baseline for this interrupted invocation.
A later authorized physical send would increase cumulative consumption from 1 to 2; no future run
may reset the count.

## 6. Future physical-attempt reservation and accounting

Decision 051 accepts `ops_retrieval_attempts`, already present in migration `0001`, as the future
primary durable consumed-count surface under all of these semantics:

1. Immediately before each physical transport send, commit one row in state `started` through the
   accepted single-writer catalog boundary.
2. If the `started` commit fails, no transport send may occur.
3. Every committed `started` row consumes one attempt, even if the process ends between the commit
   and the transport call. This is a one-attempt conservative reservation, not an assertion that a
   remote server necessarily received bytes.
4. Each retry and redirect send receives its own row.
5. When deterministically possible, update the row to `succeeded`, `failed`, `quarantined`, or
   `abandoned`. A stranded `started` row remains consumed.
6. Receipts, committed observations, raw lineage, and transport-response accounting reconcile with
   the ledger. No segment may be counted twice.
7. A mismatch that cannot be resolved deterministically produces `UNDETERMINED` and prohibits
   continuation and live entry.
8. If no exact durable count can be established for at most one identifiable in-flight logical
   request, charge its full registered `A_reachable`.
9. If the logical request, route bound, number of possible in-flight requests, or evidence
   attribution cannot be established, classify `UNDETERMINED`.
10. The approved ceiling is never increased, reset, shadowed, or reinterpreted.
11. No attempt row may contain the SEC identity, credentials, private paths, headers, cookies,
    authorization material, or response bodies.

## 7. Exact remediation architecture

The later bounded implementation stage is limited to four production changes.

### 7.1 O(n²) archive-path correction

Replace the growing-set descendant scan with the strict-ancestor-prefix-set algorithm. Preserve all
accepted archive defenses and output semantics. Add the missing reverse-order positive control,
including `["nested/x.json", "nested"]`, deep variants, and non-boundary sibling prefixes.

### 7.2 Pre-send durable attempt ledger

Instrument the accepted transport seam so every physical send first commits the §6 `started` row.
Do not modify `sec/http_client.py`, the request ceiling, response policy, raw store, migration, or
receipt schema.

### 7.3 Scoped SIGTERM handling

Install SIGTERM handling only around the governed live-acquisition lifecycle on the main thread,
after live gates pass; restore the prior handler in `finally`; route the first SIGTERM through the
same interruption mechanism as SIGINT without performing catalog or receipt writes inside the
signal handler. The existing lifecycle owns truthful closure, and the ordinary CLI may attempt at
most one terminating receipt only when an exact terminal outcome is available; otherwise it must
not fabricate one. Preserve SIGINT behavior. Do not claim that SIGKILL, power loss, OOM, or kernel
termination can emit a receipt.

### 7.4 Explicit receiptless inspection

Add an explicit first-invocation receiptless inspection mode, mutually exclusive with
`--receipt-chain-head`, and require the exact interrupted `census_run_id`. A missing or mistyped
receipt path remains an error. The receiptless mode may inspect and classify facts but may not
propose, authorize, or execute continuation or mutation.

## 8. Receiptless-inspection boundary

Receiptless inspection is read-only and non-continuable:

- it may validate the catalog, immutable object, lineage, attempt evidence, run state, projections,
  and recovery findings;
- it may calculate the accepted consumed count;
- it may support a later owner closure decision;
- it may return `UNSAFE` or `UNDETERMINED`, but never `SAFE` or continuation-eligible;
- it may not create a predecessor receipt or a substitute identity;
- it may not call `propose_continuation` or `apply_recovery_action`;
- it may not enable `--resume-from`;
- it may not adopt, quarantine, reconcile, clear a lease, close a job, or mutate any artifact;
- it may not authorize a clean or replacement run.

The ordinary receipt-chain mode remains unchanged. A missing receipt is never silently treated as
receiptless-first-invocation mode.

## 9. Interrupted-run disposition

The interrupted invocation is permanently non-resumable:

~~~text
OLD_RUN_RESUME:             PROHIBITED
OLD_RUN_EVENTUAL_STATE:     stopped
CURRENT_STATE_MUTATION:     NOT_AUTHORIZED
RECEIPT_CREATION:           PROHIBITED
HISTORICAL_LEDGER_BACKFILL: PROHIBITED
~~~

The eventual one-time transition to `stopped` requires a separate explicit offline state-
disposition authorization after the remediation implementation and its independent rereview are
accepted. That later operation must use the normal OS-lock and writer lifecycle. It must not
manually delete or clear the lease file, fabricate a receipt, alter the raw object or lineage,
manufacture an attempt row, or mark the run complete.

Until that later authority exists, the real catalog, raw object, lineage, and stale lease remain
untouched.

## 10. Later bounded remediation implementation stage

### 10.1 Authority state

~~~text
REMEDIATION_ARCHITECTURE:       OWNER_APPROVED
MAXIMUM_PATH_ENVELOPE:          OWNER_APPROVED
IMPLEMENTATION_EXECUTION:       REQUIRES_SEPARATE_OWNER_PACKET
NETWORK_DURING_IMPLEMENTATION:  FORBIDDEN
REAL_OPERATIONAL_STATE_WRITES:  FORBIDDEN
COMMIT_OR_PUSH_NOW:             FORBIDDEN
~~~

Publication of Decision 051 makes the architecture and maximum envelope durable. It does **not**
start an implementation session. The next owner act is the exact bounded implementation packet.

### 10.2 Maximum production envelope

Exactly four production paths:

1. `src/disclosure_drift/sec/archive.py`
2. `src/disclosure_drift/m3/acquisition.py`
3. `src/disclosure_drift/m3/recovery.py`
4. `src/disclosure_drift/cli.py`

### 10.3 Maximum test envelope

Exactly five test paths:

1. `tests/unit/test_sec_archive.py`
2. `tests/unit/test_m3_acquisition.py`
3. `tests/unit/test_m3_recovery.py`
4. `tests/unit/test_m3_recover.py`
5. `tests/integration/test_m3_cli.py`

`tests/integration/test_no_network.py` remains byte-identical and must pass.

No tenth path is authorized. In particular: no migration, `m3/receipt.py`, raw-store,
observation-catalog, storage-catalog, HTTP-client, response-policy, configuration, reason-code,
parser-version, dependency, CI, script, evidence-index, or governance edit belongs to the
implementation stage. Any objectively necessary out-of-envelope path is an immediate stop before
that path is touched and returns to the owner.

### 10.4 Model and commit boundary

The later implementation packet should assign one fresh Claude Code Opus 5 session at **Max**
effort, with write authority only for §10.2–§10.3, network forbidden, real operational evidence
read-only, and disposable scratch outputs outside the governed original.

At most one local implementation commit may later be created, with exact subject:

~~~text
Remediate M3.2 post-T5 archive and recovery controls
~~~

It remains local and unpushed until owner review, fresh independent rereview, correction if
required under the bounded challenge protocol, and separate owner acceptance/publication.
No tag.

## 11. Validation and independent rereview

Before any later live authorization:

1. targeted archive, acquisition, recovery, recover, and CLI tests pass;
2. deterministic differential tests prove the archive-path replacement preserves accepted
   behavior, including reverse-order and boundary positive controls;
3. no correctness test depends on the clock;
4. the real archive is read only through an explicit private path and processed twice into
   disposable scratch outputs, with identical ordered-lineage digest and count evidence;
5. performance and resource measurements are reported separately as benchmark evidence, not as a
   clock-dependent unit test;
6. process-level SIGTERM and hard-termination fault injection proves terminal-receipt behavior where
   possible, durable attempt reservation where a receipt is impossible, and receiptless inspection
   that remains non-continuable;
7. ceiling accounting proves the accepted carry-in of 1, one-row-per-send reservation, no reset,
   no double count, full-bound fallback only on genuine ambiguity, and fail-closed disagreement;
8. `ruff check .`, `ruff format --check .`, `mypy src`, the full pytest suite with the SEC
   transport test running, `make sqlite-check`, `make secrets`, `make hygiene`, and
   `make context` pass once at the stage boundary;
9. the prohibited-path nonchange proof is empty and tracked network configuration remains false /
   false;
10. one different fresh Claude Code Opus 5 session at **Max** effort performs a read-only,
    no-subagent independent rereview and records a durable review artifact under
    `Docs/m3/reviews/`;
11. the owner separately accepts the candidate and rereview before any operational-state mutation
    or live authorization.

## 12. Future clean-run boundary

No new run is authorized here. If a later owner instrument prefers a clean new invocation:

- it uses a new run ID and never `--resume-from`;
- cumulative consumption starts at 1, with five bulk-route attempts and 800 total attempts
  remaining;
- it may re-request `submissions.zip`, but byte-identical deduplication is an optimization, not an
  assumption;
- identical bytes use the accepted content-addressed deduplication path;
- differing bytes are preserved as a new object, never an overwrite, and require an immediate stop
  and owner adjudication before the earlier recovery condition is called resolved;
- no receipt-sealing, synthetic-receipt, or archive-adoption mechanism is authorized by this
  remediation.

## 13. Authority expressly withheld

Decision 051 authorizes none of the following:

- remediation implementation during this recording;
- mutation of the real interrupted catalog, raw object, lineage, staging tree, recovery state,
  writer lease, or private evidence;
- clearing, deleting, or manually taking over the stale lease;
- creating, reconstructing, back-dating, sealing, or emitting a receipt;
- inserting a historical `ops_retrieval_attempts` row;
- adopting, quarantining, reconciling, or otherwise resolving the real orphan;
- marking the old run `stopped`, `failed`, or `completed` now;
- resume, retry, `--resume-from`, replacement run, or clean new run;
- tracked or private network enablement;
- DNS, connectivity tests, curl, wget, ping, SEC request, or any remote contact;
- plan, route, host, method, ceiling, spacing, content, parser, schema, migration, reason-code, or
  receipt-schema change;
- T6, M3.2B, dependent-plan derivation, Gate H, M3.3+, publication of research output, commit tag,
  force push, rebase, amend, or history rewrite.

Tracked network configuration remains false / false. CompanyFacts and Frames remain disabled and
prohibited.

## 14. Governance edit envelope and publication

Exactly six repository paths are authorized for this governance recording, with no seventh:

1. `Docs/Decisions/decision_051_m3_2_post_t5_remediation_governance.md`
2. `Docs/Decisions/decision_registry.md`
3. `Milestones/STATUS.md`
4. `Milestones/contracts/m3_2.md`
5. `Docs/m3/templates/interrupted_run_recovery.md`
6. `Docs/sec_data_dictionary.md`

`Docs/decision_index.md` and every executable, test, migration, configuration, review-artifact,
evidence-index, and limitations-register path remain unchanged.

Post-amendment `Milestones/contracts/m3_2.md` SHA-256:
`c557b1090e416f173354de183acccaf85e7ba5a36b7b6184a9353b943ada56a7`.

One governance-only commit with exact subject:

~~~text
Record M3.2 Decision 051 remediation governance
~~~

followed by one normal fast-forward push to `origin/main`. No force, force-with-lease, rebase,
squash, amend after publication, cherry-pick, replacement history, or tag.

## 15. Recorded status

~~~text
DECISION_051:                         ACCEPTED_AND_PUBLISHED
INTERRUPTED_INITIAL_T5:              NON_SUCCESSFUL
CURRENT_RECOVERY_CLASSIFICATION:     UNDETERMINED
ACCEPTED_CONSUMED_PHYSICAL_ATTEMPTS: 1_OF_801
OLD_RUN_RESUME:                      NEVER
OLD_RUN_EVENTUAL_STATE:              stopped
CURRENT_OPERATIONAL_STATE_MUTATION:  NOT_AUTHORIZED
REMEDIATION_ARCHITECTURE:            OWNER_APPROVED
REMEDIATION_IMPLEMENTATION:          REQUIRES_SEPARATE_OWNER_PACKET
NETWORK_AUTHORITY:                   NONE
NEW_LIVE_INVOCATION_AUTHORITY:       NONE
T6:                                  NOT_AUTHORIZED
M3_2B:                               NOT_AUTHORIZED
GATE_H:                              NOT_AUTHORIZED
TAG:                                 NONE
~~~

## 16. Formal outcome

~~~text
M3_2_DECISION_051_REMEDIATION_GOVERNANCE_RECORDED
~~~

**Next authorized action:**
`CHATGPT_OWNER_M3_2_REMEDIATION_IMPLEMENTATION_PACKET`

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.
