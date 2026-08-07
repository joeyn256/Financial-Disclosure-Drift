# M3.2 T3 — Independent Rereview of the Corrected Combined T2.5–T2.6 Freeze Candidate

**Date:** 2026-08-07
**Reviewer role:** `M3_2_T3_CORRECTED_CANDIDATE_REREVIEWER`
**Model:** Claude Opus 5 — effort **Max**
**Verdict:** `M3_2_T3_CORRECTED_FREEZE_CANDIDATE_REREVIEW_PASS`

---

## 1. Independence and non-authorship

This review was performed in a single, genuinely fresh session whose first substantive project
instruction was the owner's rereview packet. The reviewing session did **not** author Decision 045,
did not perform the T2.5–T2.6 architecture discovery, did not implement the original freeze
candidate, did not perform the original T3 audit, did not author the T3 findings, did not implement
the correction, and did not author any corrected-candidate test.

No subagent, delegated agent, background agent, parallel session, Git worktree, dynamic workflow, or
second conversation was invoked. Every command was executed directly in the one active session.

The candidate was treated as **read-only** until the substantive verdict was complete. Every
destructive probe and every mutation was applied only inside a disposable reviewer-owned copy
outside the repository, which was deleted and verified deleted before this artifact was written
(§13).

Prior implementation and review reports were treated as evidence claims only. The correction
completion report was not accepted as proof; every material claim below was reproduced
independently from the source, the schema, and reviewer-owned fixtures.

## 2. Baseline and authority

Read directly before judging: `CLAUDE.md`; `Milestones/STATUS.md`; **Decision 045**; Decisions 041
and 040 where recovery semantics are relevant; the accepted `Milestones/contracts/m3_2.md`; the
historical T2 authorization packet; and the accepted recovery, receipt, snapshot, catalog,
request-ceiling, and transport primitives as needed.

Live baseline, verified from Git rather than assumed from any document:

| Fact | Verified value |
|---|---|
| Corrected candidate | `810d567ba7610b22e2ce7cd56b67b7f0e76d26fb` |
| Verified tree | `aa7a7d4a6117160a2a4b2d1165d9b82c318cf968` |
| Parent / published Decision-045 baseline | `f2bbbbf2a1b13e0780c3ea50d01797f78405e97b` |
| Subject | `Complete M3.2 T2.5-T2.6 integrated implementation` |
| Branch / remote | `main`; `origin/main == f2bbbbf2…`; ahead 1 / behind 0 |
| Working tree | clean; nothing staged; zero non-ignored untracked paths |
| Tag at candidate | none |
| Pre-correction candidate (reflog) | `d03fd93b27cb89d57bc0ab4e2fa9c833bee0af37`, parent `f2bbbbf2…` |

Protected state, verified live: `network.enabled = false`; `network.m3_acquire_enabled = false`;
CompanyFacts `enabled: false`; migrations exactly `0001`–`0013` (13 files, no `0014`); receipt schema
`m3-execution-receipt/2.0`; no operational catalog, real run, live receipt, raw acquisition object,
or SEC evidence artifact anywhere in the repository; ceiling **801** operationally unused.

No material mismatch was found, so the review proceeded.

## 3. Candidate identity and scope

**Candidate changed set**, derived independently against `f2bbbbf2…` — exactly eight paths, matching
the expected T2.5–T2.6 set with nothing added:

`src/disclosure_drift/cli.py`; `src/disclosure_drift/m3/__init__.py`;
`src/disclosure_drift/m3/acquisition.py`; `src/disclosure_drift/m3/request_plan.py`;
`tests/integration/test_m3_cli.py`; `tests/unit/test_m3_acquisition.py`;
`tests/unit/test_m3_dependent_plan.py` (added); `tests/unit/test_m3_request_plan.py`.
Totals: 7 707 insertions, 347 deletions.

**Correction envelope**, derived independently as `d03fd93 → 810d567` — exactly the four authorized
paths and no others: `src/disclosure_drift/m3/acquisition.py`, `src/disclosure_drift/cli.py`,
`tests/unit/test_m3_acquisition.py`, `tests/integration/test_m3_cli.py`. No correction escaped the
envelope.

**Prohibited-path nonchange proof.** Twenty-five paths compared by Git blob hash against the
published baseline and found byte-identical, including `m3/receipt.py`, `m3/recovery.py`,
`reasons.py`, `config.py`, `configs/project.yaml`, `sec/observation_catalog.py`,
`sec/http_client.py`, `sec/index_retrieval.py`, `sec/census_orchestrator.py`, `sec/raw_store.py`,
`sec/snapshots.py`, `sec/source_registry.py`, `sec/request_ceiling.py`, `storage/catalog.py`,
`tests/conftest.py`, `tests/integration/test_no_network.py`, `tests/unit/test_m3_receipt.py`,
`tests/unit/test_request_ceiling.py`, `tests/unit/test_httpx_transport.py`,
`tests/unit/test_migration_provenance.py`, `tests/unit/test_m3_recover.py`,
`tests/unit/test_m3_recovery.py`, `tests/unit/test_config.py`. `git diff` over `Docs`, `Literature`,
`Milestones`, `configs`, `scripts`, `src/disclosure_drift/storage`, `pyproject.toml`, and `Makefile`
is empty. No schema, receipt-vocabulary, reason-code, route, or configuration authority changed.

## 4. Prior finding disposition

| Prior finding | Disposition | Independent evidence |
|---|---|---|
| **MAJOR-1** — the live path could never emit `completion_status="interrupted"`, so real `m3 acquire --live --resume-from` could not become SAFE | **CLOSED** | `_RECEIPT_COMPLETION_STATUS` now maps `interrupted → interrupted` and the receipt carries `interruption_state`; the whole cycle reproduced for all three interruption points, in-process and across separate OS processes (§6, §7) |
| **MINOR-1** — the action/send pairing backstop lacked a direct load-bearing test | **CLOSED** | Reviewer-owned tests bind the diagnostic itself — the structural basis text, `status_code_totals == {}`, `classified_event_count == 0` — not generic `is_exact=False`; mutation M11 deleting the inner guard is KILLED by its dedicated killer (§9, §12) |
| **MINOR-2** — deterministic refusal paths created an empty operational catalog before refusing | **CLOSED** | `verify_window_bindings` now runs before `prepare_operational_catalog`; all eight refusal cases leave no catalog, no data root, no receipt, and zero transport constructions, with a positive control and a resume control (§10); mutation M12 is KILLED |
| **OPTIMIZATION-1** — wording only, no behavioural correction required | **CLOSED** | Every load-bearing wording claim in the correction was checked against the artefact it describes and found truthful (§4.1) |

### 4.1 Truthfulness of edited wording

Each verified against the thing it asserts, not against itself:

- "the two instants are the run's own … stamped after the last observation, by the same clock, at the
  same precision" — proved by a reviewer fixture comparing receipt instants against every committed
  `retrieved_at_utc` (§8);
- "the recorder commits each observation in its own transaction, and that transaction rolls back on
  any exception including a `KeyboardInterrupt`" — proved empirically: interrupting inside
  `ObservationRecorder.record` leaves zero committed rows for that retrieval (§6, I2);
- the `census_plan_sources` run→observation argument — verified against migration `0004`:
  `census_run_id TEXT NOT NULL REFERENCES ops_ingestion_jobs(job_id)` and
  `observation_id REFERENCES census_source_observations(observation_id)`;
- "All three are literals migration `0001`'s CHECK constraint already admits" — verified: the
  constraint admits `'pending','running','stopped','completed','failed','cooldown'`;
- "`_require_live_gate` … is observationally a no-op … a mutation campaign will correctly report
  that" — accurate and deliberately self-disclosing; `LiveOperatorGate` validates at construction.

## 5. Disposable review environment

A plain non-Git copy of the candidate tree (`git archive HEAD | tar -x`) outside the repository, with
imports resolved to the copy (verified: `disclosure_drift.__file__` inside the copy), run with
`PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`. All reviewer fixtures, all destructive probes,
and all mutations ran there. The primary repository was never modified during the review.

## 6. I1 / I2 / I3 — reconstructed from durable evidence

Reviewer-owned fixtures, built from the production API only; candidate test helpers were read for
orientation but are not the evidence. **59 reviewer fixtures, all passing.**

The only authorized states are `before_raw_store_write`,
`after_raw_store_write_before_catalog_commit`, and `after_catalog_commit`.
`ACQUISITION_INTERRUPTION_STATES` is a **strict subset** of the frozen receipt vocabulary:
`during_selection` and `during_manifest_write` are absent, `WindowOutcome.__post_init__` refuses
anything outside the tuple in both directions, and the frozen validator refuses an unaccepted value —
so production cannot emit a selection-phase state.

**I1 — before raw-store write.** Interrupted inside `SnapshotStore.record`. Proved from durable
state: no committed source observation for that retrieval (fresh read-only connection); no completed
promoted object of its own; the real `reconcile_requests` still owes the request and
`_classify_item` returns `retryable`, so a later SAFE resume may retry it; receipt state exactly
`before_raw_store_write`; reason exactly `SEC_ACQUISITION_INTERRUPTED`.

**I2 — after raw-store write, before catalog commit.** Interrupted inside
`ObservationRecorder.record`. Proved: the promoted object survives on disk with intact bytes; no
committed observation for that retrieval; `observe_recovery_state` reports exactly one orphan and
zero missing referents, which is the accepted recovery condition; receipt state exactly
`after_raw_store_write_before_catalog_commit`; the accepted `adopt-orphan` action reconciles the
evidence and the resume creates no duplicate substantive evidence.

**I3 — after catalog commit.** Interrupted after the recorder returned, and separately via a progress
sink raising `KeyboardInterrupt` between logical requests. Proved: the observation is visible on a
genuinely fresh durable read; no orphan classification applies; state exactly
`after_catalog_commit`; the request classifies as `satisfying`, so a resume does not request it
again.

**Falsification attempts.** The strongest available falsifier — one request committed cleanly, the
*next* interrupted before promotion — was constructed and correctly returns `before_raw_store_write`,
not the window's last commit. A `304`/byte-identical reuse was constructed and correctly returns
`before_raw_store_write`, because a reuse promotes nothing of its own. The very first retrieval
interrupted before anything returns `before_raw_store_write` with zero rows and zero objects. Where
durable evidence contradicts a transient marker, the implementation fails closed rather than
guessing.

## 7. Ambiguous interruption

Three independent durable ambiguities were constructed; each produces **no window at all** — the
`KeyboardInterrupt` propagates unchanged, no interrupted receipt is written, and no next request
begins:

1. interrupted *inside* the snapshot store **after** it promoted but before it returned — an orphan
   exists that no committed row references, and a completed promotion is indistinguishable from an
   interrupted one from inside that frame;
2. a promoted object that no longer verifies against its recorded hash;
3. a committed row whose object was removed (a missing referent).

Through the real CLI this is exit `4`, **zero receipt files anywhere below the evidence root**, the
promoted object preserved untouched, and the registered run row closed truthfully as `stopped`
rather than left indefinitely `running`.

## 8. Real CLI interruption → recovery → SAFE → resume

Driven through `disclosure_drift.cli.main` with the real argument vocabulary. `execute_live_acquisition`
was never called directly as the proof and no hand-built `ContinuationProposal` was injected. Exactly
two substitutions: the socket-owning transport implementation at `sec.httpx_transport.HttpxTransport`
— which is what the single production construction site imports at call time, so the production
factory, the `RecordingTransport` wrapper, run registration, and receipt assembly all really run — and
the canonical SEC identity validator, which returns a placeholder so no real contact value is ever
fabricated. No socket was opened; the placeholder appears in no artifact.

For each of I1, I2, I3, independently proved:

1. real `m3 acquire --live` → controlled `KeyboardInterrupt` → **exit 4**;
2. **exactly one** receipt written (`receipts/first.json`, and nothing else matching `*receipt*`);
3. it validates under the frozen schema as written on disk, and records
   `completion_status="interrupted"`, `reason_code="SEC_ACQUISITION_INTERRUPTED"`,
   `invocation_mode="live"`, and the **exact** interruption state for that scenario;
4. exactly one `ops_ingestion_jobs` row, `job_kind='m3_2_acquisition'`, `stage='M3.2A'`,
   `job_state='stopped'`;
5. `m3 recovery-state` **refuses** (exit 4) until the bounded recovery actions have run;
6. the exact accepted recovery actions are applied through `m3 recover --run` — `rebuild-projection`
   always, plus `adopt-orphan` then a second `rebuild-projection` for I2, with the orphan reconciled
   and never deleted;
7. a fresh `m3 recovery-state` returns **SAFE** (exit 0);
8. real `m3 acquire --live --resume-from receipts/first.json` → exit 0, `completion_status="complete"`,
   and no `interruption_state` on the resumed receipt;
9. a **new** run identity is registered (two rows: the predecessor still `stopped`, the resume
   `completed`), and the predecessor's run ID is never adopted;
10. predecessor receipt identity preserved via `recovery_predecessor_receipt_id`;
11. cumulative physical attempts carried forward **exactly**
    (`consumed_request_count_carried_forward == predecessor actual_physical_attempt_count`);
12. the approved ceiling is unchanged across the boundary and `carried + resumed_actual <= ceiling`;
13. only the remaining logical requests are placed — the scripted remainder is consumed exactly and
    the send counter advances by exactly that many;
14. already-completed requests are never replayed, and grouping committed observations by
    `(source_id, request_identity)` shows **one row per logical request** — no duplicate substantive
    write;
15. the final receipt validates under the frozen schema.

**Separate-OS-process proof.** The I2 cycle was additionally executed as **seven distinct operating-
system processes** over one shared evidence root — interrupt, inspect, recover, recover, recover,
inspect, resume — so no in-memory continuation state could satisfy the proof. Result: exit 4 →
interrupted receipt (`after_raw_store_write_before_catalog_commit`, 2 attempts, ceiling 53) → inspect
exit 4 → three recovery actions exit 0 → inspect exit 0 → resume exit 0, carrying 2 forward, placing
5, predecessor preserved, two run rows (`stopped`, `completed`), zero duplicate substantive writes,
both receipts valid, no identity leak.

## 9. Attempt accounting and the timestamp boundary

**Accounting (Challenge E).** Independently audited across the boundary:

- zero physical attempts (interrupted at the construction site) → **no receipt at all**, no
  observation, and the run row still closed truthfully as `stopped`;
- the first retrieval interrupted after its one response → exactly one attempt charged, one status
  entry, one classification entry;
- one completed physical response then interrupt → 2 sends, 2 attempts, `status_code_totals ==
  {"200": 2}`, and both totals equal to the recorded send count;
- a retry sequence then interrupt → every physical response accounted exactly once, the transient
  `503` retained rather than lost, both totals equal to the send count;
- interruption immediately between logical requests → nothing charged beyond the completed work;
- **an abandoned response is never silently omitted**: interrupting *inside* the transport send
  leaves a charged attempt whose response reached no bucket, and the receipt is **refused** rather
  than written under-counted;
- the final allowed attempt and a complete window stop at the ceiling and are never relabelled
  `interrupted`;
- a resume supplied ceiling `C−1` or `C+1` is refused before any transport construction, so the
  ceiling can never be reset or raised.

`cooldown_count == response_classification_totals["cooldown"]` held on every receipt inspected. The
`"0"` sentinel is reserved: a transport-level failure records `{"0": 1}` with one accepted policy
bucket and no invented `transport_error`, while a real HTTP response reported as status `0` is
refused as `UNDETERMINED` rather than recorded under `"0"`.

**Timestamp segmentation (Challenge F).** The defect the correction found is closed at its root. The
receipt's `started_at_utc` / `completed_at_utc` are now the run's **own** instants, taken from the one
governed clock the engine stamps observations with, and `elapsed_seconds` is derived from those same
two strings. Independently proved on a real CLI run: every committed `retrieved_at_utc` lies strictly
**after** `started_at_utc` and strictly **before** `completed_at_utc`, and the instants retain
sub-second precision rather than being truncated to whole seconds — the truncation that could place
the boundary before observations the run itself covered and re-charge them on every resume.

An adversarial boundary fixture confirms the remaining edge fails closed rather than double-charging:
an observation whose instant coincides **exactly** with the boundary is reported `UNDETERMINED`
("coincides exactly with the terminating receipt boundary"), never assigned to a side, while
observations one microsecond either side segment correctly (pre 2, post 5). Mutation M14, which
restores the separately-sampled truncated instants, is KILLED.

## 10. Completion-state separation and run state

All five frozen receipt completion states remain semantically distinct.
`_RECEIPT_COMPLETION_STATUS` maps `interrupted → interrupted` **and nothing else to it**. A governed
transport failure, a ceiling stop, and a gate stop each keep their own status and carry no
interruption state. `completed_with_absences` has no producer — the engine's `incomplete` maps to
`failed` — and an unknown completion status is refused. `WindowOutcome.__post_init__` refuses an
interrupted window with no established state (including `during_selection` and
`during_manifest_write`) and refuses any non-interrupted window that carries one; the frozen
validator refuses the same at the document layer.

**Run state (Challenge H).** Inspected on the durable row: `stopped` for an interrupted invocation,
`completed` for a successful one, and `failed` for an ordinary failure — including on the
no-window path, where the run is still closed `stopped` before the interrupt propagates.
`ACQUISITION_RUN_JOB_STATES == ("completed","failed","stopped")` and `finish_acquisition_run` raises
on anything else, so `job_state="interrupted"` cannot be inserted; every literal is one migration
`0001`'s CHECK already admits. No new DB literal and no migration was introduced. The transition
occurs after lawful registration and fabricates no second run.

## 11. Pairing diagnostic and pre-catalog ordering

**Pairing (Challenge I).** Mispairings in both directions were constructed. The outer equality
invariant would independently refuse the receipt, so it is a poor witness for the inner guard; the
reviewer tests therefore bind the **structural diagnostic itself** — the basis text `"physical
response(s) were observed but … accounted exactly once"`, `status_code_totals == {}`, and
`classified_event_count == 0` — plus a followed redirect proving the hop participates in the pairing
arithmetic and a correctly-paired positive control. Deleting the inner guard in the disposable clone
changes behaviour (probe: the basis text disappears) and the dedicated killer **fails** — mutation
M11 is KILLED.

**Pre-catalog ordering (Challenge J).** Against previously nonexistent catalog and data-root paths,
all eight cases — wrong window, unaccepted window, ceiling `C−1`, ceiling `C+1`, plan-hash mismatch,
live gate disabled, invalid identity, missing explicit `--live` — produce the correct exit
(`4`/`4`/`4`/`4`/`4`/`3`/`3`/`2`), **zero transport constructions**, no receipt, no M3.2 run row, an
absent catalog file, and an absent data root. A lawful positive control then creates the catalog and
writes exactly one receipt. A control with `--resume-from` confirms the catalog-dependent continuation
proposal was **not** incorrectly moved ahead of catalog construction: it still refuses, still builds
no transport, and the catalog is built because deciding a resume requires reading it.

## 12. Regression of previously passed high-risk areas

Spot-checked independently rather than blindly rerun: exactly one transport-construction site inside
the M3 layer (`m3/acquisition.py` → `default_live_transport_factory`; the only other
`HttpxTransport()` in the repository is the untouched M2.2 census orchestrator); the full live-gate
conjunction before construction; exact run registration and fresh-connection validation;
`census_plan_sources` run→observation lineage (one attribution row per planned request, per run,
observed across two runs in one catalog); run-scoped drift isolation, with an unknown run failing
closed at exit 4 and no global fallback and no receipt; response-event accounting for redirects, a
lawful `304`, the transport-failure `"0"` sentinel and cooldown; receipt count bindings keeping cache
/ `304` / duplicate distinct; `--show-scope` constructing no transport, emitting no receipt, and
creating no data root; progress-sink sanitization excluding an absolute path and an email address
from retained state; no receipt on refusal; and no route, source, configuration, or schema authority
drift. The accepted M3.2A plan hash reproduces byte-identically:
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, ceiling **801**, 75 planned
unique logical requests, via both `request_plan_sha256` and `sha256(canonical_plan_bytes(plan))`.

## 13. Independent mutation campaign

Run against the disposable clone only, independently of the correction session's own campaign. For
every mutation: the source bytes were proved changed (SHA-256 before/after), `__pycache__` was purged,
`PYTHONDONTWRITEBYTECODE=1` was set and the pytest cache disabled, a probe proved the mutated path
executes and what it now does, the dedicated killer was run, the exact bytes were restored, and the
restoration hash was verified.

| # | Mutation | Result |
|---|---|---|
| M01 | remove the interrupted completion mapping | **KILLED** |
| M02 | treat `KeyboardInterrupt` as an ordinary failure | **KILLED** |
| M03 | close an interrupted run as `completed` instead of `stopped` | **KILLED** |
| M04 | swap the I1 classification to `after_catalog_commit` | **KILLED** |
| M05 | swap the I2 classification to `before_raw_store_write` | **KILLED** |
| M06 | swap the I3 classification to `before_raw_store_write` | **KILLED** |
| M07 | suppress the interrupted receipt | **KILLED** |
| M08 | bypass the real continuation proposal on CLI resume | **KILLED** |
| M09 | reintroduce a completed request into the resume remainder | **KILLED** |
| M10 | remove the exact interruption-state/durable-evidence reconciliation (fail open) | **KILLED** |
| M11 | weaken the pairing diagnostic | **KILLED** |
| M12 | move catalog creation ahead of the window/ceiling/plan-hash proof | **KILLED** |
| M13 | (same site as M12; the killer parametrizes over window *and* ceiling `C∓1`) | **KILLED** |
| M14 | decouple the receipt completion instant from the governed run timing | **KILLED** |

**14 mutations, 14 `KILLED`, 0 `SURVIVED_EFFECTIVE`, 0 `SURVIVED_NO_OP`.** After restoration, the
clone's `acquisition.py`, `cli.py`, `m3/__init__.py`, and `request_plan.py` hash **exactly** to the
candidate's Git blobs.

The disposable environment (`rev/`, the separate-process evidence root, the mutation and process
drivers) was then deleted and its deletion verified.

## 14. Static and full-suite validation

Run against the primary candidate, read-only:

| Gate | Result |
|---|---|
| Targeted corrected-path + unchanged-primitive tests | **754 passed** |
| Ruff lint | `All checks passed!` |
| Ruff format check | `145 files already formatted` |
| mypy (`src`) | `Success: no issues found in 76 source files` |
| SQLite | Python 3.12.13 / SQLite 3.53.4 |
| Secret scan | `287 file(s) scanned, 0 findings` |
| Repository hygiene | `289 path(s) checked, 0 findings` |
| `validate-config` | cohorts validated 5 (frozen definitions match); seed `20260725` |
| `show-cohorts`, `sec --help`, `make context` | pass |

**One complete full pytest suite, run exactly once:** **3 222 passed, 1 skipped** (3 223 collected),
120.61 s.

**Exact skip inventory — one skip, and it is pre-existing and unrelated:**
`tests/unit/test_m23_pilot_manifest.py:429 — snapshot_state is a fixed literal asserted before
hashing`.

**`tests/unit/test_httpx_transport.py`: 30 passed, 0 skipped — it executed rather than skipped.**
The `[sec]` extra is genuinely available: `httpx 0.28.1`, `httpx_is_available() is True`.

## 15. Protected state and no-live proof

At completion, verified live:

- the primary corrected candidate is byte-identical to review start — `HEAD` `810d567b…`, tree
  `aa7a7d4a…`;
- no primary repository modification; clean working tree; nothing staged; zero non-ignored untracked
  paths;
- no push; no tag at the candidate; `origin/main` unchanged at `f2bbbbf2…` (Decision 045); the
  candidate remains local and unpushed, ahead 1 / behind 0;
- both tracked network switches `false`; CompanyFacts `false`;
- migrations exactly `0001`–`0013`; receipt schema `m3-execution-receipt/2.0`;
- no real SEC identity used; no DNS lookup; no connectivity test; no live request; no real
  operational catalog, real M3.2 run, live receipt, raw operational object, or SEC evidence artifact;
- ceiling **801** operationally unused.

## 16. Findings

**BLOCKER: 0. MAJOR: 0. MINOR: 1. OPTIMIZATION: 1.**

### MINOR-A (new) — post-commit marker ordering in `AcquisitionEngine._execute`

`src/disclosure_drift/m3/acquisition.py`: `_execute` stores `self._in_flight = None` **before**
`self._committed_any = True`. A real `SIGINT` delivered between those two stores leaves the engine in
a state where `_interruption_state_from_evidence` takes its final branch and returns
`before_raw_store_write`, even though that retrieval's observation is durably committed.
Demonstrated directly: with one retrieval committed and one row durable, the same engine returns
`after_catalog_commit` with the normal post-state and `before_raw_store_write` when only
`_committed_any` differs.

**This is not a fail-open and not a resume-accounting defect**, which was checked rather than
assumed: every production consumer of `interruption_state` is either display, the presence-only
recovery condition `8.2`, or pass-through. The resume remainder is derived from `reconcile_requests`
over durable catalog state, and the attempt accounting from `_segment_after_receipt` over committed
instants — neither branches on the state string. So no duplicate substantive write and no ceiling
breach can follow. The consequence is an inaccurate diagnostic value in the one field the correction
exists to make truthful, in a window of roughly one bytecode.

Suggested closure (not required for this stage): store `self._committed_any = True` before
`self._in_flight = None`. That closes the window entirely — a signal in the reordered gap leaves
`_in_flight` set with a committed observation, which the evidence path already classifies
`after_catalog_commit`.

### OPTIMIZATION-A (pre-existing at `d03fd93`, not introduced by the correction)

`src/disclosure_drift/cli.py`: `_window_reason_code`'s fallback `_ACQUISITION_FALLBACK_REASON` is
`SEC_ACQUISITION_INTERRUPTED`, so a `failed`, `stopped_by_gate`, or `incomplete` window carrying no
narrower registered blocking code produces a **non-interrupted** receipt whose `reason_code` is the
interruption code (verified for all three). No safety consequence: resumability is decided by
`completion_status` and `interruption_state`, both of which correctly exclude these, and the registry
entry's own text is "Acquisition was interrupted **and no narrower registered reason applies**".
Now that a genuine `interrupted` completion status exists, the shared code makes the reason field
ambiguous between the two cases. No behavioural correction is required, and closing it would need a
reason-code decision outside this stage's envelope.

Neither finding is a BLOCKER or a MAJOR, so neither affects the verdict.

## 17. Verdict

```text
M3_2_T3_CORRECTED_FREEZE_CANDIDATE_REREVIEW_PASS
```

Every PASS condition is met: no BLOCKER; no unresolved MAJOR; prior MAJOR-1 closed; prior MINOR-1 and
MINOR-2 closed; all three interruption states independently reproduced correctly; ambiguous
interruption fails closed; real CLI interruption/recovery/resume succeeds, including across separate
OS processes; restart and resume depend only on accepted durable evidence; attempt accounting across
the interruption boundary is exact, and refuses rather than under-counts when it cannot be;
timestamp segmentation cannot double-charge; no effective safety mutation survives; full validation
green; and the candidate remains local, unpushed, and untagged.

## 18. Recommended owner disposition

```text
RETURN_FOR_CHATGPT_OWNER_M3_2_T3_ACCEPTANCE_AND_PUBLICATION_DECISION
```

The corrected combined T2.5–T2.6 implementation-freeze candidate passes fresh independent T3
rereview. Bind acceptance to corrected candidate
`810d567ba7610b22e2ce7cd56b67b7f0e76d26fb`, its verified tree
`aa7a7d4a6117160a2a4b2d1165d9b82c318cf968`, and this durable PASS review artifact and its commit.
**Do not push or tag until the owner records the separate T3 acceptance and publication decision.**

---

**Reviewer:** independent non-author session, Claude Opus 5, effort Max, no subagents.
**Scope of this artifact:** a review record only. It changes no implementation, test, migration,
configuration, decision, or contract byte, and grants no authority.
