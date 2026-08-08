# Decision 052 — M3.2 Post-T5 Remediation Acceptance and Publication

**Date:** 2026-08-08
**Status:** ACCEPTED — OWNER APPROVED 2026-08-08
**Authority classification:** `M3_2_POST_T5_REMEDIATION_ACCEPTED_AND_PUBLISHED`
**Type:** Bounded governance record accepting the corrected **M3.2 post-T5 remediation** candidate
and its fresh independent PASS rereview, recording the owner's disposition of the two carried MINOR
findings and the clean-run carry-in obligation, exhausting
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) §10 implementation authority, and
publishing the complete local lineage by one normal fast-forward push. **Not** a preregistration
deviation. It changes no hypothesis, cohort window, maturity gate, outcome definition, threshold,
seed, selection methodology, governed identity, hash preimage, migration byte, implementation byte,
test byte, receipt byte, reason code, or configuration byte — **no executable byte changes with this
record**.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–051 are byte-unchanged.
The accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md),
[`Docs/m3/templates/interrupted_run_recovery.md`](../m3/templates/interrupted_run_recovery.md),
[`Docs/sec_data_dictionary.md`](../sec_data_dictionary.md), and the durable review artifact are all
byte-unchanged by this record. Stage progress is recorded here, in the registry, and in the ledger —
never in the contract.
**Narrowly supersedes:** nothing. Decision 051's own narrow supersession of Decision 032 F3 and
Decision 040 §7 — exact durable evidence controls over an automatic full-per-route `A_reachable`
charge, with the full-bound fallback still controlling on genuine ambiguity — is accepted as
implemented and is **not** widened here.
**Preserves unchanged:** accepted
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) §8's predecessor-receipt
requirement for every continuation, its no-automatic-resume rule, and ceiling **801**; Decision 051
§9's permanent old-run no-resume ruling and its `CURRENT_STATE_MUTATION: NOT_AUTHORIZED` boundary;
Decision 051 §8's receiptless-inspection boundary; the frozen `m3-execution-receipt/2.0` schema;
migrations `0001`–`0013`; and every route, host, method, spacing, content, provenance, leakage, and
stop condition not expressly addressed here.
**Related:**
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) (the authorizing record whose §10
implementation authority this record exhausts, and whose §11 item 10 required the fresh independent
rereview this record accepts);
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md);
[Decision 040](decision_040_m3_2_t2_4_implementation_authorization.md);
[Decision 042](decision_042_m3_2_t2_4_acceptance_and_publication.md);
[Decision 046](decision_046_m3_2_t3_acceptance_and_publication.md);
[Decision 048](decision_048_m3_2_pre_t4_rawstore_acceptance_and_publication.md);
[Decision 049](decision_049_m3_2_t4_operational_preflight_acceptance.md);
the durable review artifact
[`Docs/m3/reviews/m3_2_post_t5_remediation_independent_rereview.md`](../m3/reviews/m3_2_post_t5_remediation_independent_rereview.md);
the limitations register [`Docs/m3/limitations_register.md`](../m3/limitations_register.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's acceptance of the corrected post-T5 remediation candidate at the exact
commits, trees, and file hashes named in §3; the owner's acceptance of the fresh independent PASS
rereview and its durable artifact named in §4; the acceptance of the four Decision 051 §7 production
changes as implemented (§5); the accepted attempt-accounting determinations (§6); the dispositions of
**F1** (§7), **F2** (§8), **O1** (§9), and **O2**–**O4** (§10); the recorded status of the not-re-run
real-archive evidence (§11); the exhaustion of Decision 051 implementation authority and the
completion of the remediation (§12); the preserved interrupted-run disposition (§13); the withheld
authority (§14); and the publication of the complete three-commit lineage by one normal fast-forward
push (§15).

---

## 1. What this record accepts, and what it does not

Eight determinations, which must not be collapsed:

1. **Implementation acceptance.** The corrected post-T5 remediation candidate is accepted at the exact
   commits, tree, and file hashes named in §3. The acceptance is **SHA-, tree-, and hash-specific**
   and does not transfer automatically to a later changed tree.
2. **Review acceptance.** The fresh independent no-subagent non-author rereview, its verdict
   `M3_2_POST_T5_REMEDIATION_INDEPENDENT_REREVIEW_PASS` (**BLOCKER 0 · MAJOR 0 · MINOR 2**), and its
   durable repository artifact are accepted (§4).
3. **Architecture acceptance.** All four Decision 051 §7 production changes are accepted as correctly
   implemented (§5).
4. **Accounting acceptance.** The counterexample resolutions and the unchanged historical incident
   accounting are accepted (§6).
5. **Explicit limitation acceptance.** **F1** and **F2** are accepted as documented nonblocking
   limitations under the bounded review protocol (§§7–8). **This is a deliberate owner acceptance of
   known, characterized limitations, not an assertion that they do not exist**, and it expressly
   forecloses a third correction loop for this stage.
6. **Obligation recording.** **O1** — the absent clean-run carry-in interface for the consumed
   baseline of **1** — is recorded as a **mandatory later live-readiness obligation** that **blocks**
   any later clean-run authorization (§9).
7. **Publication.** The correction commit, the review-artifact commit, and this acceptance commit are
   published above the published Decision 051 baseline by **one normal fast-forward push** (§15).
   **No tag.**
8. **What this record is not.** It is **not** operational-state authority, **not** lease, receipt, or
   ledger authority, **not** network or SEC authority, **not** resume, retry, replacement, or
   clean-run authority, **not** T6, M3.2B, or Gate H authority, and **not** a live-readiness claim.
   **The project is not ready for live operation**, and O1 blocks that readiness until it is
   discharged.

## 2. The owner determination, recorded without alteration

The owner's determination for this acceptance was issued as the Decision 052 recording packet itself.
It carries **no separately named `OWNER_DECISION_052_…` instrument token**, and none is invented here
— the same convention accepted Decisions 046, 047, 048, and 049 record. Its operative terms are:

```text
M3.2 — DECISION 052
POST-T5 REMEDIATION ACCEPTANCE AND PUBLICATION

The owner accepts the frozen corrected post-T5 remediation candidate and its
fresh independent PASS rereview; accepts MINOR findings F1 and F2 as documented
nonblocking limitations without launching a third correction loop; records the
clean-run carry-in obligation O1 as a mandatory later live-readiness condition;
exhausts Decision 051 implementation authority; and authorizes one normal
fast-forward publication push. No operational-state, network, live-run, T6,
M3.2B, or Gate H authority is granted, and no live readiness is claimed.
```

Where this record summarizes for navigation, the owner's own terms control.

## 3. Ruling 052-A — accepted corrected remediation candidate

The accepted candidate is the Decision 051 implementation commit **plus** the separate accounting
correction commit, bound to these exact identities:

| Fact | Accepted value |
|---|---|
| Published Decision 051 baseline | `1e36a41c6fa67e552f8687414f8f33898ed1aca2` |
| Implementation commit | `47de0738f836958e86e31557b24834fd4f1a3436` |
| Implementation tree | `042d1efdd5bb2dee3687e7770f08405b974ebe78` |
| Implementation subject | `Remediate M3.2 post-T5 archive and recovery controls` |
| **Correction commit** | **`7dad4231650f5699ded3e8a550d14633d0372f82`** |
| **Correction tree** | **`53d5342e753c7c33fdca9222a2e70115ff3234c5`** |
| Correction subject | `Correct M3.2 post-T5 attempt accounting` |
| Correction parent | `47de0738f836958e86e31557b24834fd4f1a3436` |
| Full accepted diff from `1e36a41`, SHA-256 | `a2ad82c8e4e440398fcd62a01c8ea6a95a9f9b458d6ce8f7d05bc6f07bbb3d9b` |
| Correction delta from `47de073`, SHA-256 | `5ccc37ee9c186ef295bcb9d75da9205dcada93d186ca105b78d6e0d69df4899c` |

Accepted file identities (SHA-256), unchanged by the correction commit, which staged the reviewed
bytes without editing one of them:

| Path | SHA-256 |
|---|---|
| `src/disclosure_drift/m3/acquisition.py` | `a108c18c9e8702a07806c0b933bf5f11adbe2037f4198ca8e1e6c31a9e0e2190` |
| `src/disclosure_drift/m3/recovery.py` | `1f7a8fce4ab166fcd3f828092abc8425424b20862e10421a887601522f4ca309` |
| `tests/unit/test_m3_acquisition.py` | `44c017e68da6ea40451c183825b62e4faa66e9406b7ebaf2dbe6041b0ede82f0` |
| `tests/unit/test_m3_recovery.py` | `bd17a6fafe174628fbc4c72cc697b6e753f971d68cb0f5300ca3c8a15f42d029` |

**Why the correction is a separate commit.** The accounting correction is the transparent result of
the **two owner-authorized bounded remediation passes** performed after the original implementation
commit. Decision 051 §10.4 contemplated at most one implementation commit; the owner records here
that a **separate correction commit** is the accepted publication mechanism, expressly **instead of**
an amend, rebase, squash, or any other history rewrite, so the remediation's real sequence stays
visible in published history. No history was rewritten.

**Path envelope.** The complete accepted delta `1e36a41` → acceptance baseline is exactly **eight**
paths, inside the Decision 051 §10.2–§10.3 maximum of four production plus five test paths, with **no
ninth path**: `src/disclosure_drift/sec/archive.py`, `src/disclosure_drift/m3/acquisition.py`,
`src/disclosure_drift/m3/recovery.py`, `src/disclosure_drift/cli.py`,
`tests/unit/test_sec_archive.py`, `tests/unit/test_m3_acquisition.py`,
`tests/unit/test_m3_recovery.py`, and `tests/integration/test_m3_cli.py`. The fifth authorized test
path `tests/unit/test_m3_recover.py` was not needed and is unchanged.
`tests/integration/test_no_network.py` is byte-identical and passes.

**This acceptance is SHA-, tree-, and hash-specific. It does not transfer automatically to a later
changed tree.**

## 4. Ruling 052-B — accepted independent rereview

The fresh independent rereview required by Decision 051 §11 item 10 is accepted:

| Fact | Accepted value |
|---|---|
| Artifact | [`Docs/m3/reviews/m3_2_post_t5_remediation_independent_rereview.md`](../m3/reviews/m3_2_post_t5_remediation_independent_rereview.md) |
| Artifact SHA-256 | `7234ef37a1b8be8e1f8f23ba7debcfcd0373b6123cfafc723723feb0b2990bff` |
| Review commit | `e91b8fecfe7d1ac586b4a9da0e502e65571217c8` |
| Review tree | `bc38100c40f0bd5e193062d85b9c8304e9cfafd9` |
| Review subject | `Record independent rereview of M3.2 post-T5 remediation` |
| Review parent | `7dad4231650f5699ded3e8a550d14633d0372f82` |
| Verdict | `M3_2_POST_T5_REMEDIATION_INDEPENDENT_REREVIEW_PASS` |
| Findings | **BLOCKER 0 · MAJOR 0 · MINOR 2** |

The rereview was performed by a fresh Claude Opus 5 session at **Max** effort that authored none of
the remediation work and used no subagent, delegated agent, background agent, parallel session, Git
worktree, or dynamic workflow — the Decision 051 §11 item 10 conditions.

**The substantive acceptance threshold is satisfied: BLOCKER = 0 and MAJOR = 0.**

**The artifact is advisory.** It records findings and a recommendation. It accepts nothing. This
record, not the artifact, is the acceptance.

## 5. Ruling 052-C — the four Decision 051 §7 production changes are accepted as implemented

All four accepted architecture changes are correctly implemented:

1. **§7.1 archive-path correction.** The strict-ancestor-prefix set replaces the quadratic
   descendant scan, with constant-time membership for the reverse-order file-versus-directory
   collision. Semantics, refusals, member ordering, limits, suffix filtering, and malformed-input
   behavior are unchanged, and the required reverse-order positive controls are present.
   **Accepted semantic-equivalence evidence: 20,192 randomized differential cases with zero
   divergence, across 296 end-to-end archives, with ordered lineage preserved.**
2. **§7.2 pre-send durable attempt ledger.** One `ops_retrieval_attempts` `started` row commits at
   the accepted transport seam before every physical send, including each retry and redirect. A
   failed commit prevents the send; a stranded row remains consumed; terminal state is settled only
   when deterministically known. No header, body, contact identity, credential, or private path is
   recorded. `sec/http_client.py`, the ceiling, the response policy, the raw store, the migrations,
   and the receipt schema are untouched, and the ceiling remains the hard pre-attempt guard.
3. **§7.3 scoped SIGTERM handling.** Installed only around the governed live-acquisition lifecycle,
   only on the main thread, after the live gates pass, and always restored in `finally`. The first
   SIGTERM routes through the same interruption mechanism SIGINT uses; the handler performs no
   catalog, file, or receipt write; SIGINT behavior is preserved; and no claim is made that SIGKILL,
   power loss, OOM, or kernel termination can emit a receipt.
4. **§7.4 explicit receiptless inspection.** Reachable only through the explicit run-bound flag pair,
   mutually exclusive with the ordinary receipt-chain mode, refusing a missing or mistyped receipt
   path rather than silently degrading into receiptless mode, and additionally bound to the governed
   acquisition job kind and the inspected plan's window. It returns only `UNSAFE` or `UNDETERMINED`;
   **`SAFE` is unreachable by construction**; and it proposes, authorizes, and executes no
   continuation or mutation.

**Accepted mutation evidence: 20 mutations, 18 killed, one provably equivalent (§10, O4), and one
genuine narrow test gap (§8, F2).**

**Accepted validation, executed by the independent reviewer against these exact frozen hashes:**
targeted tests **601 passed**; SEC transport tests **123 passed**; full `pytest` suite **3315 passed,
1 skipped** (the known pre-existing intentional skip); `ruff check` and `ruff format --check` pass;
`mypy` passes; `make sqlite-check`, `make secrets`, `make hygiene`, and `make context` pass. No
correctness test depends on the clock. Tracked network configuration is **false / false**, no SEC or
network use occurred, and the real operational state is unchanged.

**The full code suite is deliberately not re-run at this recording**: the fresh independent reviewer
already ran it against these exact frozen hashes, and no code or test byte changes with this record.

## 6. Ruling 052-D — accepted attempt-accounting determinations

The owner accepts the following as the exact accounting position:

```text
COUNTEREXAMPLE_A_RESOLUTION:          2
COUNTEREXAMPLE_B_RESOLUTION:          1        (never 6)
HISTORICAL_INCIDENT_CONSUMED:         1_OF_801
HISTORICAL_INCIDENT_CLASSIFICATION:   UNDETERMINED
HISTORICAL_INCIDENT_RESUMABLE:        NEVER
APPROVED_HARD_CEILING:                801
REMAINING_TOTAL_HEADROOM:             800
BULK_ROUTE_REMAINING_HEADROOM:        5
```

Counterexample A resolves to **2** and counterexample B resolves to **1, never 6**. Decision 051
§2.4's narrow rule behaves as accepted: exact durable evidence controls, and the full per-route
`A_reachable` bound remains the fallback only where the count is genuinely unrecorded, unattributable,
or ambiguous.

Attribution rests on **durable run and event identity** — recorded run boundary instants, later
governed acquisition runs' starts, and the pre-send commit order of matching reservations — never on
URL equality alone. A segment already accounted for by strictly preceding reservations is never
counted twice; a strictly later same-URL reservation never erases an earlier lineage attempt; and
out-of-scope lineage never changes the count. Evidence that cannot be reconciled exactly fails closed
as `UNDETERMINED`, with the provable total standing as a **durable floor**, never an invented exact
value.

**The historical empty-ledger interrupted incident is unchanged: exactly 1 of 801, `UNDETERMINED`,
and non-resumable.** No historical `ops_retrieval_attempts` row is backfilled by this record.

## 7. Ruling 052-E — F1 accepted as a nonblocking limitation, with a hard standing condition

**Finding (MINOR).** Receiptless lineage attribution evaluates ledger-coverage cardinality
**independently per manifest**, so one reservation can cover multiple owned same-URL manifests.
Measured: **1 reservation + 2 owned segments** reports **1 / `UNSAFE`** rather than the durable floor
**2 / `UNDETERMINED`**.

**Disposition — `ACCEPTED_NONBLOCKING_LIMITATION`.** The owner accepts it without a third correction
loop, on these exact grounds:

- it is **absent from the real incident** — the interrupted run's ledger is empty, so no reservation
  exists to over-apply, and the accepted count of **1 of 801** is unaffected;
- it is **unreachable on the governed reserve-before-send path as currently constructed**;
- it **cannot authorize continuation**, because receiptless mode never returns `SAFE`.

**Hard standing condition, recorded as a limitation.** Before receiptless accounting with a
**non-empty** ledger is ever relied on as an owner baseline, **either** correct reservation
consumption to one-reservation-per-segment, **or** fail such unmatched cardinality to
`UNDETERMINED`. Until one of those is implemented and validated, receiptless accounting over a
non-empty ledger is **not** an acceptable owner baseline. This condition is carried in
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md) as **M3-L14**.

## 8. Ruling 052-F — F2 accepted as a deferred one-test gap

**Finding (MINOR).** Second-SIGTERM suppression is implemented and was **directly verified** by the
independent reviewer through process-level fault injection, but **no regression test guards it**.

**Disposition — `ACCEPTED_NONBLOCKING_TEST_STRENGTH_OBSERVATION — DEFERRED`.** The production
behavior is correct today and independently confirmed. This is a one-test coverage gap, not a
production defect. **This accepted stage is not reopened to add the test.** The gap is carried in the
limitations register as **M3-L15** and may be discharged by a later separately authorized packet.

## 9. Ruling 052-G — O1 is a mandatory later live-readiness obligation

**Observation.** The accepted candidate provides **no non-resume clean-run carry-in interface** for
the historical consumed baseline of **1**.

**Disposition.** This is **outside** Decision 051's four-change scope and is therefore correctly
absent from the accepted candidate — it is **not** a defect in the candidate and does not reduce this
acceptance. It is nonetheless a **mandatory later live-readiness obligation**:

```text
CLEAN_RUN_CARRY_IN_INTERFACE:   ABSENT
OBLIGATION_STATUS:              OPEN — BLOCKS LATER LIVE AUTHORIZATION
```

**No clean new run may be authorized until an exact owner-approved carry-in mechanism is available
and validated.** Decision 051 §12 already fixes that a clean run starts from cumulative consumption
**1**, with 5 bulk-route and 800 total attempts remaining, and never resets the count; O1 records that
no interface yet exists to carry that baseline in. It is carried in the limitations register as
**M3-L16**.

**No session may read this record as a live-readiness claim.** The project is **not** ready for live
operation.

## 10. Ruling 052-H — O2, O3, and O4 recorded as nonblocking reviewer observations

Recorded concisely, per repository convention, and creating **no** limitations-register entry:

- **O2 — transaction-enclosure assumption.** The reservation write assumes the accepted single-writer
  boundary's enclosure semantics. Recorded as an assumption made explicit, not a defect.
- **O3 — SIGTERM scope ends before the receipt write.** That is what the accepted §7.3 specification
  requires. Recorded so a later reader does not mistake it for a gap.
- **O4 — the strict-ancestor full-path mutant is equivalent.** One mutation of the prefix helper that
  also emits the full path is provably semantically equivalent on all reachable inputs. It survives
  for a sound reason and is not a coverage defect.

## 11. Ruling 052-I — the real-archive two-run evidence was NOT re-run

Decision 051 §11 item 4's two-run real-archive evidence was **not re-executed** by this reviewer,
because the private archive path was not disclosed to that session. The owner accepts that
disposition and records it explicitly rather than letting silence imply fresh evidence.

- **The previously accepted measurements of approximately 43.1 and 45.2 seconds stand** as the
  performance evidence of record, exactly as accepted at Decision 051 §4.1 — as evidence, **not** as a
  timeless contractual constant.
- The reviewer supplied **equivalent-scale synthetic** evidence, reported it **as synthetic**, and did
  **not** overclaim it as real-archive evidence. The owner accepts it on those terms.
- **No repository path, decision, or session may hereafter cite the synthetic evidence as
  real-archive evidence.**

## 12. Ruling 052-J — the remediation is accepted and complete; Decision 051 authority is exhausted

```text
M3_2_POST_T5_REMEDIATION:            ACCEPTED_AND_COMPLETE
POST_T5_INDEPENDENT_REREVIEW:        ACCEPTED_AND_COMPLETE
DECISION_051_IMPLEMENTATION_AUTHORITY: EXHAUSTED
THIRD_CORRECTION_LOOP:               NOT_AUTHORIZED
```

Decision 051 §10's implementation authority is **fully consumed** by the accepted candidate. No
further source or test change to the remediation is authorized by Decision 051 or by this record.
Any later change — including discharging **F1**, **F2**, or **O1** — requires a **new** explicit
owner packet.

## 13. Ruling 052-K — the interrupted-run disposition is preserved exactly

Nothing in this record changes the interrupted invocation's state or its disposition:

```text
OLD_RUN_RESUME:                 PROHIBITED
OLD_RUN_CLASSIFICATION:         UNDETERMINED
OLD_RUN_EVENTUAL_STATE:         stopped   (requires separate authority; not performed)
CURRENT_STATE_MUTATION:         NOT_AUTHORIZED
RECEIPT_CREATION:               PROHIBITED
HISTORICAL_LEDGER_BACKFILL:     PROHIBITED
ACCEPTED_CONSUMED_ATTEMPTS:     1_OF_801
```

The real catalog, raw object, lineage, staging tree, writer lease, recovery state, job state, and
private evidence remain **untouched**. Decision 050 §8's predecessor-receipt requirement remains
fully binding for every continuation, and Decision 051 §8's receiptless-inspection boundary is
unchanged: receiptless inspection can never report `SAFE`, propose continuation, enable
`--resume-from`, or mutate any artifact.

## 14. Ruling 052-L — negative authority

Decision 052 authorizes none of the following:

- any further remediation, correction, or implementation edit;
- mutation of the real interrupted catalog, raw object, lineage, staging tree, recovery state, writer
  lease, job state, or private evidence;
- clearing, deleting, or manually taking over the stale lease;
- creating, reconstructing, back-dating, sealing, or emitting a receipt;
- inserting a historical `ops_retrieval_attempts` row, or any attempt backfill;
- adopting, quarantining, reconciling, or otherwise resolving the real orphan;
- marking the old run `stopped`, `failed`, or `completed`;
- run closure, resume, retry, `--resume-from`, replacement run, or clean new run;
- tracked or private network enablement; DNS, connectivity tests, `curl`, `wget`, `ping`, an SEC
  request, or any remote contact;
- plan, route, host, method, ceiling, spacing, content, parser, schema, migration, reason-code, or
  receipt-schema change;
- T6, M3.2B, dependent-plan derivation, Gate H, M3.3+, publication of research output, a
  live-readiness or live-authorization claim, a commit tag, force push, rebase, amend, or history
  rewrite.

Tracked network configuration remains **false / false**. CompanyFacts remains disabled and
prohibited. The approved ceiling **801** is never increased, reset, shadowed, or reinterpreted.

## 15. Publication

The owner authorizes **one normal fast-forward push** of the complete local lineage, in this order:

```text
1e36a41c6fa67e552f8687414f8f33898ed1aca2   published Decision 051 baseline
  ↓
47de0738f836958e86e31557b24834fd4f1a3436   Decision 051 implementation commit
  ↓
7dad4231650f5699ded3e8a550d14633d0372f82   accepted accounting correction
  ↓
e91b8fecfe7d1ac586b4a9da0e502e65571217c8   accepted independent PASS rereview
  ↓
<this Decision 052 commit>                 owner acceptance and publication
```

Push only `main → origin/main`. **Normal fast-forward only**: no force, no `--force-with-lease`, no
rebase, no squash, no amend, no cherry-pick, no replacement branch, and **no history rewrite**. The
accepted candidate and the accepted review commit are published **exactly as they stand**.

**NO TAG.** No `m3.2-complete`, no remediation tag, and no other tag. Existing tags are unchanged.
**M3.2 is not complete.**

## 16. Authorized paths and acts for this recording

Exactly **four** paths, with **no fifth**:

1. `Docs/Decisions/decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md` (this record)
2. `Docs/Decisions/decision_registry.md`
3. `Milestones/STATUS.md`
4. `Docs/m3/limitations_register.md`

Expressly **not** edited: Decision 051 or any other accepted decision; the review artifact; the
accepted contract; `Docs/m3/templates/interrupted_run_recovery.md`; `Docs/sec_data_dictionary.md`;
`Docs/decision_index.md`; `Docs/m3/templates/evidence_index.md`; any production source beyond staging
the four already-reviewed frozen files in their own separate correction commit; any test; any
configuration; any migration; the receipt schema; the operator runbook; the master plan; the
`Makefile`; `pyproject.toml`; every script; and every other `Docs/` and `Milestones/` path.

One governance commit containing exactly those four paths, subject
`Accept M3.2 post-T5 remediation and independent rereview`, followed by one normal fast-forward push.
No amend, no squash, no rebase, no cherry-pick, no history rewrite.

## 17. Recorded acceptance status

```text
M3_2_POST_T5_REMEDIATION:               ACCEPTED_AND_COMPLETE
POST_T5_INDEPENDENT_REREVIEW:           ACCEPTED_AND_COMPLETE — BLOCKER 0, MAJOR 0, MINOR 2
DECISION_051_IMPLEMENTATION_AUTHORITY:  EXHAUSTED
F1_RECEIPTLESS_COVERAGE_CARDINALITY:    ACCEPTED_NONBLOCKING_LIMITATION — M3-L14 ACTIVE
F2_SECOND_SIGTERM_REGRESSION_TEST:      ACCEPTED_NONBLOCKING — DEFERRED — M3-L15 ACTIVE
O1_CLEAN_RUN_CARRY_IN_INTERFACE:        OPEN OBLIGATION — M3-L16 ACTIVE — BLOCKS LIVE AUTHORIZATION
REAL_ARCHIVE_TWO_RUN_EVIDENCE:          NOT_RE_RUN — ACCEPTED 43.1 / 45.2 SECOND EVIDENCE STANDS
ACCEPTED_CONSUMED_PHYSICAL_ATTEMPTS:    1_OF_801
OLD_RUN_CLASSIFICATION:                 UNDETERMINED
OLD_RUN_RESUME:                         NEVER
CURRENT_OPERATIONAL_STATE_MUTATION:     NOT_AUTHORIZED
NETWORK_AUTHORITY:                      NONE
NEW_LIVE_INVOCATION_AUTHORITY:          NONE
LIVE_READINESS:                         NOT_CLAIMED — BLOCKED BY O1
T6:                                     NOT_AUTHORIZED
M3_2B:                                  NOT_AUTHORIZED
GATE_H:                                 NOT_AUTHORIZED
TAG:                                    NONE
```

## 18. Formal outcome

```text
M3_2_POST_T5_REMEDIATION_ACCEPTED_AND_PUBLISHED
```

**Next authorized action:**
`CHATGPT_OWNER_M3_2_INTERRUPTED_RUN_CLOSURE_PACKET`

Control returns to the ChatGPT owner for the separate exact interrupted-run closure packet. This
record authorizes **no** operational-state mutation, **no** run closure, **no** lease or receipt act,
**no** network enablement, **no** SEC contact, **no** new or clean run, and **no** T6, M3.2B, or
Gate H work until that packet is issued, and no session may read this record as any of those.

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.
