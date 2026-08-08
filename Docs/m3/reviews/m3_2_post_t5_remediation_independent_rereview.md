# M3.2 Post-T5 Remediation — Independent Rereview of the Corrected Candidate

**Date:** 2026-08-08
**Reviewer role:** `M3_2_POST_T5_REMEDIATION_INDEPENDENT_REREVIEWER`
**Model:** Claude Opus 5 — effort **Max**
**Verdict:** `M3_2_POST_T5_REMEDIATION_INDEPENDENT_REREVIEW_PASS`
**Findings:** **BLOCKER 0 · MAJOR 0 · MINOR 2**

**This artifact is advisory.** It is the durable record required by accepted
[Decision 051](../../Decisions/decision_051_m3_2_post_t5_remediation_governance.md) §11 item 10. It
records one reviewer's independent findings and a recommendation. It accepts nothing, authorizes
nothing, and is not an owner determination — only a separate owner record can accept this candidate
or the findings below.

---

## 1. Independence and non-authorship

Performed in a single fresh session whose first substantive project instruction was the owner's
rereview packet. This session did **not** record Decision 051, did **not** implement the original
post-T5 remediation candidate, and did **not** implement either of the two bounded correction passes
that followed it.

No subagent, delegated agent, background agent, parallel session, Git worktree, or dynamic workflow
was used. Every command ran directly in the one active session.

The implementation completion reports were treated as **claims to falsify**, never as authority.
Committed fixtures were not relied on to establish any acceptance conclusion; they were run as a
separate corroborating signal only.

## 2. Reviewed identities

The reviewed candidate is the Decision 051 implementation commit **plus** the two bounded correction
passes, which at review time stood as an uncommitted delta on top of it. The composite was verified
from Git rather than assumed from any report.

| Fact | Verified value |
|---|---|
| Published baseline (`origin/main`) | `1e36a41c6fa67e552f8687414f8f33898ed1aca2` — "Record M3.2 Decision 051 remediation governance" |
| Implementation commit | `47de0738f836958e86e31557b24834fd4f1a3436` — "Remediate M3.2 post-T5 archive and recovery controls" |
| Full reviewed diff from `1e36a41`, SHA-256 | `a2ad82c8e4e440398fcd62a01c8ea6a95a9f9b458d6ce8f7d05bc6f07bbb3d9b` |
| Correction delta from `47de073`, SHA-256 | `5ccc37ee9c186ef295bcb9d75da9205dcada93d186ca105b78d6e0d69df4899c` |
| Branch / position | `main`; no stash; no tag at any reviewed commit |

Reviewed file identities (SHA-256), the exact bytes every conclusion below rests on:

| Path | SHA-256 |
|---|---|
| `src/disclosure_drift/m3/acquisition.py` | `a108c18c9e8702a07806c0b933bf5f11adbe2037f4198ca8e1e6c31a9e0e2190` |
| `src/disclosure_drift/m3/recovery.py` | `1f7a8fce4ab166fcd3f828092abc8425424b20862e10421a887601522f4ca309` |
| `tests/unit/test_m3_acquisition.py` | `44c017e68da6ea40451c183825b62e4faa66e9406b7ebaf2dbe6041b0ede82f0` |
| `tests/unit/test_m3_recovery.py` | `bd17a6fafe174628fbc4c72cc697b6e753f971d68cb0f5300ca3c8a15f42d029` |

**Recording note, added at publication and not a review finding:** the reviewed correction bytes were
subsequently committed unchanged as `7dad4231650f5699ded3e8a550d14633d0372f82`. The four hashes above
are unchanged by that commit, and the full reviewed diff from `1e36a41` still hashes to
`a2ad82c8…`.

## 3. Path-envelope proof

The complete delta `origin/main` → reviewed candidate is exactly **eight** paths, inside the
Decision 051 §10.2–§10.3 maximum of four production plus five test paths, **with no ninth path**:

| # | Path | Class |
|---|---|---|
| 1 | `src/disclosure_drift/sec/archive.py` | production |
| 2 | `src/disclosure_drift/m3/acquisition.py` | production |
| 3 | `src/disclosure_drift/m3/recovery.py` | production |
| 4 | `src/disclosure_drift/cli.py` | production |
| 5 | `tests/unit/test_sec_archive.py` | test |
| 6 | `tests/unit/test_m3_acquisition.py` | test |
| 7 | `tests/unit/test_m3_recovery.py` | test |
| 8 | `tests/integration/test_m3_cli.py` | test |

`tests/unit/test_m3_recover.py` — the fifth authorized test path — was not needed and is unchanged.
`tests/integration/test_no_network.py` is byte-identical and passes. No migration, receipt module,
raw store, observation catalog, storage catalog, HTTP client, response policy, configuration,
reason code, parser version, dependency, CI, script, evidence index, or governance byte changed.

## 4. Architecture rulings — all four Decision 051 changes

Each of the four §7 production changes is implemented as accepted.

### 4.1 §7.1 — O(n²) archive-path correction

`sec/archive.py` replaces the growing-set descendant scan with a maintained set of **strict ancestor
prefixes** of admitted paths, turning the reverse-order file-versus-directory collision check into a
constant-time membership test. `_strict_ancestor_prefixes("a/b/c")` yields `("a", "a/b")` and is
empty for a single-component key.

The replacement is semantically exact, not approximately equivalent. Keys reaching the test are
already portable (NFC-normalized, case-folded, `/`-joined), so `portable in strict_ancestors` is
precisely `any(existing.startswith(portable + "/"))` over the admitted set: the component boundary a
prefix split enforces is the same boundary the `+ "/"` concatenation enforced, so `a` never matches a
sibling `ab/…`. Refusals, member ordering, limits, suffix filtering, and malformed-input behavior are
unchanged, and the required reverse-order positive controls — including `["nested/x.json", "nested"]`,
deep variants, and non-boundary sibling prefixes — are present.

**Differential evidence: 20,192 randomized differential cases, zero divergence** between the accepted
prior algorithm and the replacement, across **296 end-to-end archives**, with **ordered member lineage
preserved** in every case.

### 4.2 §7.2 — pre-send durable attempt ledger

`PreSendAttemptLedger` commits one `ops_retrieval_attempts` `started` row at the accepted transport
seam immediately before every physical send, including each retry and redirect send. A failed
reservation commit aborts the send. A stranded row remains consumed. Terminal state is settled only
when deterministically known. No header, body, contact identity, credential, or private path is
recorded. `sec/http_client.py`, the request ceiling, the response policy, the raw store, the
migrations, and the receipt schema are untouched.

The correction pass additionally made the durable reservation count, rather than the in-memory
ceiling, the source of the window's consumed physical-attempt count: `AcquisitionEngine._durable_consumed()`
returns `self._baseline_consumed + self.ledger.reserved_count()` when a ledger is bound, where the
baseline is captured before the first request is placed so a carry-forward window stays cumulative.
Ledgerless callers — the accepted offline and fixture paths — fall through to `self.ceiling.consumed`
and are behaviourally unchanged. This is what keeps an interruption inside the pre-send window from
charging an attempt that left no durable trace: the ceiling may have incremented before the
reservation committed, but no row means no charge. The ceiling itself is untouched and remains the
hard pre-attempt guard.

### 4.3 §7.3 — scoped SIGTERM handling

`_scoped_sigterm_interruption()` installs a SIGTERM handler **only** around the governed
live-acquisition lifecycle, **only** on the main thread (a non-main caller keeps the default
disposition rather than pretending to have scoped it), **after** the live gates pass, and always
restores the prior handler in `finally`. The first SIGTERM raises `KeyboardInterrupt`, routing it
through the existing SIGINT reconciliation path. The handler performs no SQLite, file, receipt, or
catalog write. SIGINT behavior is untouched. The code explicitly disclaims any receipt guarantee for
SIGKILL, power loss, OOM kill, or kernel termination — none of which deliver a catchable signal.

Second-SIGTERM delivery during cleanup is suppressed by a `delivered` latch, so cleanup and any
single terminating-receipt attempt are never duplicated. That behavior was directly verified by
process-level fault injection (see **F2** for the test-coverage gap).

### 4.4 §7.4 — explicit receiptless inspection

`inspect_receiptless_first_invocation` is reachable only through the explicit
`--receiptless-first-invocation --run CENSUS_RUN_ID` pair. The two modes are mutually exclusive:
`--run` is rejected in ordinary receipt-chain mode, and a missing or mistyped receipt path remains an
error rather than a silent fall-through into receiptless mode.

Run binding was tightened by the correction pass beyond mere row existence: the run must be a
governed M3.2 acquisition job (`job_kind = ACQUISITION_JOB_KIND`) **and** its `stage` must equal the
inspected plan's acquisition window, so a mistyped id, a non-acquisition job sharing an id, or a run
for a different window cannot read as a genuine recovery finding.

`_determine_receiptless` returns only `UNSAFE` or `UNDETERMINED`. **`SAFE` is unreachable by
construction** — verified by exhaustive inspection of every return path. The mode creates no
predecessor receipt or substitute identity, never calls `propose_continuation` or
`apply_recovery_action`, never enables `--resume-from`, and adopts, quarantines, reconciles, clears,
closes, and mutates nothing.

## 5. Attempt-accounting counterexamples

Both counterexamples the first correction pass was directed at now resolve correctly.

- **Counterexample A resolves to 2.** The genuine two-attempt case is charged **2**. It is not
  collapsed to 1 by lineage that the ledger already covers, and it is not inflated.
- **Counterexample B resolves to 1, never 6.** The single-attempt case is charged **1**. The full
  per-route `A_reachable` bound of 6 is **not** applied where exact durable evidence establishes the
  count — the narrow Decision 051 §2.4 supersession of Decision 032 F3 and Decision 040 §7 behaves as
  accepted, and the full-bound fallback remains reachable only on genuine ambiguity.

The correction achieves this by attributing pre-ledger raw lineage on **durable run and event
identity** rather than URL equality alone: the run's recorded boundary instants, later governed
acquisition runs' start instants, and the pre-send commit order of matching reservations. A segment
whose strictly preceding reservations already account for its recorded `attempts` adds nothing (§5A
rule 4); a strictly **later** same-URL reservation is its own consumed event and never erases or
absorbs an earlier lineage attempt; lineage outside the interrupted run's plan scope, or that the
boundaries prove belongs to another run, never changes the count. Boundary instants are parsed
strictly, and an unparseable, naive, or exactly-simultaneous instant proves no order and is treated as
non-provable rather than guessed. **The current wall clock is consulted nowhere in this accounting**,
so no correctness test depends on it.

Evidence that cannot be reconciled exactly fails closed as `UNDETERMINED`, with the provable total
reported as a **durable floor** rather than an invented exact value.

**The historical incident is unchanged.** For the interrupted initial T5 invocation — whose
`ops_retrieval_attempts` table is empty and is never backfilled — the accepted consumed count remains
exactly **1 of 801**, the classification remains **`UNDETERMINED`**, and the run remains
**non-resumable**.

## 6. Mutation evidence

**20 independent mutations. 18 KILLED. 1 provably equivalent. 1 genuine narrow test gap.**

- The 18 killed mutations cover the archive strict-ancestor boundary, the ledger reservation and
  abort-on-failed-commit path, the durable-consumed baseline and ledgerless fall-through, the
  receiptless run-kind and window binding, the ordering and coverage predicates, and the
  never-`SAFE` guarantee.
- The one equivalent mutant is recorded as **O4** below; it is not a coverage defect.
- The one surviving genuine gap is recorded as **F2** below.

## 7. Real-archive two-run evidence — NOT RE-RUN

**Decision 051 §11 item 4's two-run real-archive evidence was not re-executed by this reviewer.** The
private path to the real archive was not disclosed to this session, and this session did not seek,
guess, or construct one. Nothing here should be read as fresh real-archive evidence.

The previously accepted measurements of approximately **43.1** and **45.2** seconds stand as the
performance evidence of record, exactly as accepted at Decision 051 §4.1 — as evidence, not as a
timeless contractual constant.

To bound the risk without overclaiming, this reviewer instead constructed **equivalent-scale
synthetic** archives and measured the replacement against them. That synthetic evidence is consistent
with the accepted real-archive measurements and is reported **as synthetic**. It is explicitly **not**
a substitute for the real-archive two-run requirement, and the requirement is not treated as
discharged by it.

## 8. Findings

**BLOCKER: none. MAJOR: none.**

### F1 — MINOR: receiptless lineage coverage cardinality is evaluated per manifest

**Finding.** In `_selected_run_lineage_contribution`, ledger coverage is decided independently for
each lineage manifest. Reservations are not consumed across manifests, so one reservation can satisfy
the coverage test for more than one owned same-URL segment. Measured directly: **1 reservation + 2
owned segments** reports a consumed count of **1** with determination `UNSAFE`, where the durable
floor is **2** and the correct fail-closed outcome is `UNDETERMINED`.

**Why it is MINOR and not MAJOR.**

- It is **absent from the real incident**. The interrupted initial T5 invocation's ledger is empty, so
  no reservation exists to over-apply; its accepted count of **1 of 801** is unaffected.
- It is **unreachable on the governed reserve-before-send path as currently constructed**, which
  commits one reservation per physical send before that send occurs.
- It **cannot authorize continuation** under any value. Receiptless mode never returns `SAFE`, so
  neither the wrong count nor the wrong determination can make a run resume-eligible.

**Recommended standing condition.** Before receiptless accounting with a **non-empty** ledger is ever
relied on as an owner baseline, either correct reservation consumption to one-reservation-per-segment,
or fail such unmatched cardinality to `UNDETERMINED`.

### F2 — MINOR: second-SIGTERM suppression has no regression test

**Finding.** The `delivered` latch that suppresses a second SIGTERM during cleanup is implemented and
was **directly verified** by this reviewer through process-level fault injection. No committed test
guards it, so a future edit could remove the latch without failing the suite.

**Why it is MINOR.** The production behavior is correct today and was independently confirmed. This is
a one-test coverage gap, not a defect.

## 9. Observations (nonblocking, not findings)

- **O1 — no clean-run carry-in interface for the consumed baseline of 1.** The candidate provides no
  non-resume mechanism for carrying the historical consumed baseline of **1** into a clean new run.
  This is **outside** Decision 051's four-change scope and is correctly absent from the candidate. It
  is nonetheless a **mandatory later live-readiness obligation**: no clean new run may be authorized
  until an exact owner-approved carry-in mechanism exists and is validated. **Nothing in this artifact
  claims live readiness.**
- **O2 — transaction-enclosure assumption.** The reservation write assumes the accepted single-writer
  boundary's enclosure semantics. Recorded as an assumption made explicit, not a defect.
- **O3 — SIGTERM scope ends before the receipt write.** The scoped handler's lifetime ends before any
  terminating-receipt write, which is what the accepted §7.3 specification requires. Recorded so a
  later reader does not mistake it for a gap.
- **O4 — the strict-ancestor full-path mutant is equivalent.** One mutation of
  `_strict_ancestor_prefixes` that also emits the full path is provably semantically equivalent on all
  reachable inputs, because a path is never its own strict ancestor in the collision test's operand
  set. It survives for a sound reason and is not a coverage defect.

## 10. Validation

Every gate below was executed by this reviewer against the exact reviewed bytes.

| Gate | Result |
|---|---|
| Targeted tests (archive, acquisition, recovery, recover, CLI) | **601 passed** |
| SEC transport tests | **123 passed** |
| Full `pytest` suite, SEC transport running | **3315 passed, 1 skipped** |
| `ruff check .` | pass |
| `ruff format --check .` | pass |
| `mypy src` | pass |
| `make sqlite-check` | pass |
| `make secrets` | pass |
| `make hygiene` | pass |
| `make context` | pass |

The single skip is the known pre-existing intentional skip; no other test was skipped. No correctness
test depends on the clock.

## 11. Nonchange and network proof

- **Prohibited-path nonchange proof is empty.** The eight-path delta in §3 is complete; no ninth path
  differs from `origin/main`.
- **Tracked network configuration remains `false` / `false`** (`network.enabled`,
  `network.m3_acquire_enabled`), and CompanyFacts remains disabled.
- **No network access was attempted or made at any point** — no SEC request, DNS lookup, connectivity
  test, `curl`, `wget`, or `ping`.
- **The real operational state is unchanged.** No catalog, raw object, lineage, staging tree, writer
  lease, recovery state, or private evidence was read for mutation or written. No lease was cleared or
  taken over, no receipt was created or reconstructed, no attempt row was backfilled, no run was
  closed, and no resume, retry, replacement, or clean run occurred.
- Migrations remain exactly `0001`–`0013`; the receipt schema remains `m3-execution-receipt/2.0`.
- No tag and no push was created by this rereview.

## 12. Verdict and recommendation

All four Decision 051 §7 production changes are implemented as accepted. The archive replacement is
semantically exact under 20,192 randomized differential cases with zero divergence. The attempt
accounting resolves both counterexamples correctly — A to 2, B to 1 and never 6 — while leaving the
historical incident at exactly 1 of 801, `UNDETERMINED`, and non-resumable. Receiptless inspection is
run-bound, read-only, and can never return `SAFE`. Two MINOR findings remain, each precisely
characterized and safely deferrable, and one of them (**F1**) carries a standing condition that must
be discharged before receiptless accounting over a non-empty ledger is ever used as an owner baseline.

> ### `M3_2_POST_T5_REMEDIATION_INDEPENDENT_REREVIEW_PASS`
>
> **BLOCKER 0 · MAJOR 0 · MINOR 2**

**Recommendation to the owner:** accept the candidate as reviewed, and carry **F1**, **F2**, and
**O1** forward as recorded nonblocking conditions rather than opening a third correction loop. **This
recommendation is advisory only.** It confers no acceptance, no operational-state authority, no
network or SEC authority, no live-run authority, and no T6, M3.2B, or Gate H authority — and it does
not assert live readiness, which **O1** expressly blocks until an exact owner-approved carry-in
mechanism exists and is validated.
