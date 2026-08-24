# Decision 145 — Governed Major-Phase Restart and RAM Reclamation

```text
STATUS: IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER ACCEPTANCE
RECORD_TYPE: EXECUTION-ARCHITECTURE IMPLEMENTATION, PLUS ONE GOVERNANCE NORMALIZATION
DATE: 2026-08-23
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings D145-R0 – D145-R12
CLASSIFICATION: BOUNDED IMPLEMENTATION OF THE SOUND SUBSET DECISION 140 §17 RETURNED FOR REDESIGN
ACCEPTED_PREDECESSOR: M3_3_D144_D143_FINDING_CORRECTION_COMPLETE_READY_FOR_OWNER, owner-accepted
  for continuation; entry HEAD 2389dffe85b242bbb1e13724dc9f444e777bb634
AUTHORIZATION:
  M3_3_D145_GOVERNED_MAJOR_PHASE_RESTART_AND_RAM_RECLAMATION_AUTHORIZED — issued outside this
  repository and now spent, together with its D145-R0 addendum
ACCEPTANCE_TOKEN: NONE — THIS RECORD CLAIMS NO OWNER ACCEPTANCE
COMPLETION_TOKEN: M3_3_D145_GOVERNED_MAJOR_PHASE_RAM_RECLAMATION_COMPLETE_READY_FOR_OWNER
PHASE_BOUNDARY_RAM_RECLAMATION: IMPLEMENTED
GOVERNED_PAUSE_RESUME: NOT_IMPLEMENTED
SAFE_TO_EJECT: NOT_IMPLEMENTED
CANARY_AUTHORIZED: NO
E0_EXECUTION_AUTHORIZATION: NO
MAJOR_EXECUTION_PHASES: 3 — F0, F1, F2
QUALIFIED_MAJOR_RESTART_BOUNDARIES: 2 of 2 — F0→F1, F1→F2
FINAL_PHASE_BOUNDARY: TERMINAL_PROCESS_EXIT_EXPECTED
SELECTED_TRANSPORT: USB_VIA_THUNDERBOLT_DOCK — UNCHANGED, ENFORCED AT EVERY BOUNDARY
QUALIFIED_VOLUME_UUID: 397A4D4A-9508-391E-814E-3B533C7BD049 — UNCHANGED
MIGRATION_HEAD: 0015 — 0016 ABSENT
ALL_THREE_ACTIVATION_CONSTANTS: None
NETWORK: enabled=false, m3_acquire_enabled=false
PARSE_BULK: CANARY-UNREACHABLE — RE-TRACED, UNCHANGED, DELIBERATELY UNREPAIRED
```

## 1. What this record is, and what it is not

It is the implementation of **exactly the sound subset accepted
[Decision 140](decision_140_m3_3_total_pre_canary_hardening.md) §17 identified and returned for
owner redesign**, and nothing wider.

Decision 140 was asked for a governed quiescent pause with deterministic resume. It inspected the
corrected complete-source canary, **refused to build one**, and named three independently
sufficient blockers to mid-F0 resume. In the same breath it named what was *not* blocked and
offered it as "the smallest technically sound architecture": the **`F0 → F1` and `F1 → F2`
boundary recycles**. The load-bearing fact was verified there rather than assumed — F0's source
completeness digest absorbs **only** `("member-digest", record_count, member_digest)` per member,
and the sidecar durably stores exactly those in ordinal order, so **F0's evidence is exactly
reconstructible from durable state without re-parsing**. F1 writes through `INSERT … ON CONFLICT …
DO UPDATE` plus a plain `UPDATE`.

The owner has now authorized that subset. **This record builds it and stops there.**

**It is not pause/resume, and no sentence here may be read as creating one.** The authorized
behaviour is a phase that reaches durable terminal success, a process that then **exits**, and a
**different** process that starts and continues. It is not process suspension, not `kill -STOP`,
not sleep, not lid closure, not unmount, not eject, not disconnect, and not topology switching.
`GOVERNED_PAUSE_RESUME` remains `NOT_IMPLEMENTED` and `SAFE_TO_EJECT` remains `NOT_IMPLEMENTED`.

**It authorizes nothing.** No activation constant is minted, no network switch moves, no migration
is created, no world is built, and the complete-source canary remains unauthorized exactly as
Decision 144 left it. A passing preflight still prints `canary_authorized: false`.

**One governance normalization was performed first, and is recorded separately.** The owner's
D145-R0 addendum required the Decision 140 acceptance lineage to be normalized **before** any
D145 architecture or source mutation. It was, it passed, and only then did implementation begin.
It touched two documentation surfaces and **no** source, test, configuration, or migration path.
See **§22**.

## 2. Entry state

Verified live, not taken from a document:

| Fact | Value |
|---|---|
| Branch / HEAD | `main` / `2389dffe85b242bbb1e13724dc9f444e777bb634` |
| `origin/main` vs HEAD | equal, `0/0` ahead/behind, worktree clean, nothing staged, no untracked residue |
| Tag at HEAD | none |
| Migration head | `0015`; `0016` absent |
| Activation constants | all three `None`, read from `m3/e0.py` |
| Network | `enabled=false`, `m3_acquire_enabled=false` |
| D144 CI | run `32675430616` at this exact SHA — terminal `success`, **both** mandatory jobs `success` |

## 3. The reconstructed major-phase inventory

**Reconstructed from the controlling implementation, not from the authorization packet and not
from a phase count assumed in advance.** The packet explicitly forbade assuming two phases, three
phases, or any particular naming; the inventory below was derived by reading
`m3/single_source_canary.py`, `m3/offline_parse.py`, `m3/working_catalog.py`,
`m3/compact_evidence.py`, `sec/census.py` and the accepted capacity vocabulary.

The first complete-source canary is `disclosure-drift m3 canary-source --mode run`. Before this
record it was **one process** holding one `WorkingCatalog`, one SQLite connection, one
`CensusCatalog` and one open sidecar across its entire ~30-hour life.

| # | `PHASE_ID` | Production entry point | Predecessor | Successor | Terminal success state |
|---|---|---|---|---|---|
| 1 | `F0` | `offline_parse.materialize_one_planned_source` | — | `F1` | `require_f0_success` passes; ledger `parsed`; sidecar source row + member manifest |
| 2 | `F1` | `census.CensusCatalog.count_persisted_accession_resolutions` | `F0` | `F2` | every persisted accession resolved; resolution rows durable |
| 3 | `F2` | `offline_parse.materialize_census_associations` | `F1` | — | one transaction committed; `AssociationTotality` invariants hold |

**Durable state written, in-memory state remaining, and what the next phase consumes:**

| Phase | Durable at terminal | In memory at terminal | Next phase consumes |
|---|---|---|---|
| `F0` | every census row the source implies; `compact_source_evidence` (members, records, omitted/materialized field observations, completeness digest); the per-member manifest; ledger `parsed` with parts and batches | `SingleSourceOutcome` — the parse disposition, `parser_state_before/after`, `parser_run_id`, `parsed_records`, `quarantined_records`, the bound `SourceObservation`, and a `FullIndexCorroboration` for a full-index quarter | the **working catalog only** |
| `F1` | every resolution row | `ResolutionEvidence` — a rolling digest and seven counts, accumulated on the `CensusCatalog` object | the **working catalog only** |
| `F2` | the canonical association relation | `AssociationTotality` and the row counts | — (the result document) |

**The one thing that had no durable home.** Neither F0's `SingleSourceOutcome` scalars nor F1's
`ResolutionEvidence` were written down when the phase produced them: the whole-run path reads both
at the very end, because the same process is still holding them. A process that exits at a phase
terminal takes them with it, and the only way to recover them would be to **re-run the phase that
produced them** — which is precisely the duplicate execution §13 prohibits. That gap, and only
that gap, is what this record persists.

## 4. The phases: exact number and names

**Three major execution phases: `F0`, `F1`, `F2`.**

The names are **not invented by this record**. They are the accepted
[Decision 135](decision_135_m3_3_corrected_run_capacity_reconciliation.md) §11 capacity
vocabulary, already carried in code by `external_working_root.CAPACITY_PHASES` — `PRE_LAUNCH`,
`POST_F0`, `PRE_F1`, `POST_F1_PRE_F2`, `DURING_F2`, `POST_F2` — and used by every ruling from
[Decision 124](decision_124_m3_3_capacity_reconciliation.md) onward.

**World creation is not a fourth phase**, and the result document is not a fifth. Creating the
disposable world, copying the accepted catalog into the D111 working catalog, and opening the
sidecar are F0's own setup, inside F0's process; writing the create-once `canary_result.json` is
F2's own terminal, inside F2's process. Neither is a boundary the accepted capacity model names,
and inventing one would have been exactly the "invent a continuation merely to create another
restart" the authorization forbids.

## 5. Every inter-phase boundary, classified

Three phases give **two** inter-phase boundaries, and the owner rule was that **every** boundary
proven terminal, durable, reconstructable, idempotently continuable and safe for clean termination
must support restart — not a hard-coded "after phase 1 and phase 2".

| Boundary | Classification | Why |
|---|---|---|
| `F0 → F1` | **`QUALIFIED_MAJOR_RESTART_BOUNDARY`** | F0 is complete and its rows are committed; `persist_streamed` already short-circuits on an existing `parser_run_id`, so the create-once guarantee is untouched; F1 consumes the working catalog and nothing else. D140 §17 (A1-R23.1) proved it sound. |
| `F1 → F2` | **`QUALIFIED_MAJOR_RESTART_BOUNDARY`** | F1 is idempotent by construction; F2 consumes the working catalog and nothing else; the Decision 126 §7 admission gate stays inside the process that opens F2's transaction. D140 §17 (A1-R23.2) proved it sound. |

**Both boundaries qualify. Neither is `UNDETERMINED`, `NOT_DURABLE`, or
`REQUIRES_IN_MEMORY_CONTINUITY`** — the last only because the bounded persistence in §7 closes the
gap §3 names. Without that persistence, both boundaries would have been
`REQUIRES_IN_MEMORY_CONTINUITY` and this record would have had to **fail**.

**The final phase.** After F2 reaches its terminal, the run's create-once result document is
written and the canary stops. The next stage is E0, which is unauthorized and is a separate owner
instrument, so there is **no successor execution to admit**. The post-final boundary is classified
`TERMINAL_PROCESS_EXIT_EXPECTED`: the process exits cleanly, and no continuation is invented for it.

Accordingly `PHASE_BOUNDARY_RAM_RECLAMATION = IMPLEMENTED` is stated because **every** inter-phase
boundary the first canary requires is a qualified major restart boundary — two of two — and the
only remaining boundary conclusively requires no successor execution.

## 6. What a restart is, and the rights it does not confer

A restart is: **durable terminal success → clean process exit → fresh process → full
reauthentication → next phase.** It is not, and this list is exhaustive rather than illustrative:

* not process suspension; `kill -STOP` is **not** a governed pause and never was;
* not storage eject, unmount, detach, or dock disconnect;
* not SSD movement, topology change, or a switch to `USB_DIRECT`;
* not laptop sleep, lid closure, or reconnect;
* not process resurrection, and not crash recovery.

**The external SSD must remain continuously attached to the selected qualified dock topology for
the whole sequence, restarts included.** A major-phase restart grants **zero** physical-detach
rights. `SAFE_TO_EJECT` does not exist in `src/` or `tests/`, which is asserted by a test that
reads every Python file in both trees as a syntax tree and requires the identifier to appear in
neither.

## 7. The durable checkpoint contract

A boundary is a restart boundary only once the completed phase is **mechanically proved** durable.

**Where the checkpoint lives, and why no migration was needed.** In the accepted
[Decision 111](decision_111_m3_3_e0_bounded_persistence_and_working_catalog.md) run-local progress ledger
(`run_progress.sqlite3`), which already sits beside the working catalog, already runs `WAL` with
`synchronous = FULL`, and already exists to record *the attempt* rather than the census. Its
`run_working_catalog` key/value table is the durable home the checkpoint needed. **Migration head
remains `0015` and `0016` remains absent**, and the working catalog stays the byte-for-byte schema
twin of the accepted operational catalog that Decision 111 requires it to be.

**Existing canonical artifacts were preferred, and duplicates were refused.** F0's member manifest,
per-member digests and source completeness digest are **not** copied into the checkpoint — they are
already durable in the compact-evidence sidecar, and the sidecar remains the evidence contract. The
checkpoint carries execution state and the §3 gap, and no more.

Each checkpoint records:

| Field | What it is for |
|---|---|
| `contract`, `phase`, `status` | this build's shape, the phase named, and `complete` — the **only** status ever written |
| `run_id`, `source_instance_id` | the governed run and the one source |
| `execution_identity` | the digest of the frozen values that govern a phase (§12) |
| `catalog_source_sha256`, `migration_head`, `plan_fingerprint` | the accepted catalog, its schema, and the plan |
| `completed_at_utc`, `pid`, `rss_peak_bytes_at_start`, `rss_peak_bytes_at_terminal` | the §9 evidence |
| `payload` | the phase's own cross-boundary values, and the accumulated capacity observations |

**There is deliberately no `in_progress` and no `failed` status.** A checkpoint is written only
after the phase reached durable terminal success, so **its presence is the completion proof and
its absence is the refusal**. A phase that died part-way leaves none, which is exactly right.

**It is written last, and exactly once.** Every durable write of the phase is committed and every
handle on the working catalog is closed before the checkpoint is written, through a short-lived
ledger handle opened only for it. A checkpoint already present for that phase is **refused, not
overwritten**. In F2's process the create-once result document is written **before** the
checkpoint, so a death between the two leaves the run's deliverable intact and leaves F2 unable to
run again — `attach_world` refuses a world that already carries its result document.

## 8. The clean-exit contract

Normal reclamation is **intentional process termination**: the phase entry point returns, the
process ends, and the operating system reclaims its address space. `SIGKILL`, `kill -9`, crash
simulation and forced termination are **not** the mechanism, and neither are `gc.collect()`,
deleting variables, or clearing caches — none of which returns memory to the operating system in
the way process replacement does.

Before the process ends, in this order: the phase's durable writes complete; the containment
authorizer is cleared; the sidecar connection is closed; the working catalog's context closes the
writing connection and the ledger; F2 additionally truncates the write-ahead log; the result
document is written; the terminal checkpoint is written and its handle closed; and the host
execution lock is released in a `finally`.

**No stronger physical-durability claim is made than the existing D141 evidence supports.**
`F_FULLFSYNC` remains OS-visible evidence only, and this record does not upgrade it.

## 9. The RAM-reclamation property, and its evidence

The mechanical requirement is **process replacement**: the old phase's process terminates, and the
next phase runs in a different process. That is strictly stronger than any in-process reset.

Every governed continuation records: the old process's id and peak resident size at its terminal;
the terminal checkpoint identity it produced; the new process's id and peak resident size at its
start; the successor phase; and **the proof that the old process is gone**.

**"Gone" is enforced, not observed.** The checkpoint is written *before* the process exits, so
"the predecessor finished its phase" and "the predecessor is no longer running" are two different
claims. A successor that finds the predecessor's process still running this canary **refuses** —
two writers on one working catalog is not a restart. The predecessor's id comes from its own
durable checkpoint and from nowhere else, and it is authenticated the way
[Decision 140](decision_140_m3_3_total_pre_canary_hardening.md) (D140-R18) authenticates the stop
path: a recycled id running something else reads as *gone*, and only a process carrying the canary
subcommand adjacently **and** `--run-id` with exactly this identity reads as *alive*.

**The resident-size figure is named for what it is.** `ru_maxrss` is a **peak**, not an
instantaneous sample; the unit is normalized (Darwin reports bytes, Linux kibibytes). It is
reported as the peak rather than described as something narrower. **No arbitrary percentage drop
is enforced** — the requirement is process replacement, and the resident-size figures are evidence
of the benefit rather than a threshold to pass.

## 10. Fresh-process world reauthentication

**A successor process may not say "the previous process already checked this."** Every predicate
is re-established in the successor, in the successor's own process, before any work begins:

* the disposable work-root boundary (`require_canary_work_root`);
* the **complete** Decision 137 external envelope, narrowed to the Decision 142 §4 topology —
  volume identity by exact UUID, the mandatory `--require-volume-uuid` assertion, mounted-volume
  authentication, qualified transport, AC power and open lid, D130 isolation, the bounded archive
  precheck, the free-space floor for the phase being admitted, and an explicit external
  `SQLITE_TMPDIR`;
* the host execution lock, re-taken by this process;
* the accepted operational catalog's own digest, compared against the digest recorded when the
  working catalog was copied from it;
* the working catalog's applied migration chain;
* run identity, source identity, plan fingerprint, migration head and execution identity;
* the predecessor's durable terminal checkpoint, and the proof its process is gone.

**Two things are deliberately not re-done, and both are stated rather than smoothed.** F1 and F2
do **not** re-authenticate the source artifact or re-prove its shard-to-parent map: neither phase
opens the artifact, and re-digesting 1.5 GB to admit a phase that never reads it would be theatre.
And the attach path does **not** repeat `PRAGMA integrity_check` on the working catalog: it is
O(database), the creating path runs it when the copy is fresh — which is the moment it can be
afforded and the moment a bad copy would be born — and repeating it at every boundary of a
multi-hundred-gibibyte file would cost hours per boundary to answer a question the boundary is not
asking.

**The free-space floor a continuation is admitted under is the accepted floor for the phase it is
about to begin, not the launch floor.** The 185 GiB launch floor asks *"is there room to run the
whole canary from nothing?"*, which is false by construction once F0 has written; refusing a
continuation with it would be refusing the run for passing. The floors used are already-accepted
constants at their already-accepted meanings — `PRE_F1_MINIMUM_FREE_BYTES` (55 GiB, D138-R6) before
F1 and `PRE_F2_MINIMUM_FREE_BYTES` (50 GiB, D126-R6/D137-R5) before F2 — and **not one floor is
invented, moved, or relaxed.** Each phase then records and enforces its accepted boundary gate
again inside the run, which is the same deliberate redundancy through one primitive the work root
already uses.

## 11. Topology enforcement survives every restart

**The Decision 144 correction is intact and is now enforced at four production seams rather than
three.** `FIRST_CANARY_REQUIRED_TRANSPORT` is passed by `run_single_source_canary`,
`run_single_source_prefix_profile`, `run_canary_source_command` **and**
`run_single_source_canary_phase`.

**A qualified `USB_DIRECT` attachment does not become admissible because the canary restarted.**
That matters more at a phase boundary than anywhere else: the D142 §6 failure mode is a dock
refusal answered by re-plugging directly, and a phase boundary is exactly where an operator part-way
through a thirty-hour run would try it. There is no fallback, no operator override, and no
"restart on direct if the dock preflight fails". A changed BSD disk identifier remains
non-authoritative.

`USB_DIRECT` is **not** revoked: D141-R8 and Decision 142 §5 stand entire, both classes remain
qualified, and `require_external_envelope` still admits direct when nothing narrows it.

**The D144 recurrence killer did its job here, and that is worth recording.** The D144 test that
pins the production seam count to an exact number **failed** when the fourth seam was added. The
seam was then reviewed for the narrowing, found to carry it, and the count was raised to four with
the reason written beside it. A tripwire that fires and is understood is a tripwire working.

## 12. Run, code and configuration continuity

A successor process is a continuation of the **same** governed run, and it fails closed when any
governing identity has moved. The mechanisms are the repository's own; **no parallel identity
system was invented**:

* **run identity** — the create-once `run_id` that names the disposable world;
* **input/plan identity** — `capacity_plan.plan_fingerprint`, re-derived live in each process from
  the accepted catalog and compared, never carried;
* **catalog identity** — the accepted catalog's SHA-256, recorded by D111 at copy time and
  re-measured on every attach;
* **code and configuration identity** — `phase_execution_identity()`, a SHA-256 over the frozen
  values that govern a phase: this path's contract, the restart contract, the evidence contract,
  the resolution scope, the required transport, the qualified volume UUID, the batch size, the
  four capacity floors, and the package version. **This path reads no configuration file — its
  configuration *is* those frozen constants** — so one digest is honestly both identities.

**`cache_bytes` is deliberately excluded, and the reason is an accepted decision rather than
convenience.** [Decision 119](decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md)'s equivalence
proof establishes that the page-cache budget moves no row, no ordering, no digest and no identity;
folding a provably evidence-neutral execution parameter into a continuity check would refuse
continuations that are provably fine. `batch_size` **is** folded in, because it decides when rows
become durable and no accepted record blesses changing it mid-run.

What this prevents, mechanically: a process continuing another run's checkpoint; a process
continuing under an incompatible configuration; a process continuing from a revision whose
governing semantics moved; and a checkpoint of one phase being read as another's.

## 13. Idempotency and exactly-once phase advancement

Three questions are asked before any phase begins, in order, each dispositive:

1. **has this phase already run?** A phase carrying its own durable checkpoint is refused.
2. **did the predecessor finish?** F0 has none and needs none. Every other phase requires its
   predecessor's checkpoint to be present and `complete`.
3. **is it the same run?** Every identity in §12 must match exactly.

**The existence of a directory is never phase-completion proof, and neither is anything else that
merely exists.** A populated world, a working catalog holding every row F0 wrote, and a run-local
ledger reading `parsed` are all insufficient: without the terminal checkpoint the successor
refuses. That case is tested directly — a completed F0 has its checkpoint deleted, leaving every
durable row behind, and F1 refuses.

**`create_world` and `attach_world` are exact inverses**, so no path can manufacture the state a
continuation was supposed to inherit: creation refuses an identity whose world exists, attachment
refuses one whose world does not, and a world already carrying its result document is refused by
both.

**A predecessor is never re-run**, proved by detonation rather than by reading: F1 runs with
`materialize_one_planned_source` replaced by a function that raises, and F2 runs with F1's entry
point replaced the same way. Both complete.

## 14. Interruption semantics

**The restart right exists only after successful terminal phase completion.** Unexpected process
death mid-phase is not a RAM-reclamation checkpoint, and this record does not broaden into
arbitrary crash recovery.

A crash, a `kill`, an out-of-memory termination, a physical disconnect, or a closed lid part-way
through a phase leaves **no checkpoint**, and an absent checkpoint refuses the successor. Such a
run is **interrupted**, governed exactly as accepted
[Decision 142](decision_142_m3_3_precanary_architecture_freeze.md) §8 already governs it: an
interrupted run is lost and requires a new run identity; worlds are create-once and are never
resumed, repaired or overwritten. **No existing interruption governance is reinterpreted, relaxed,
or silently absorbed into this mechanism.**

## 15. Authority semantics — what this record does not authorize

D145 creates architecture and implementation only. It **does not** authorize the real canary, and
it **mints no execution authority**.

It does not activate `PRE_E0_CATALOG_TRANSITION_AUTHORITY`, `M3_3_E0_EXECUTION_AUTHORITY`, or
`STALE_WRITER_LEASE_RECOVERY_AUTHORITY` — all three remain `None`. It does not enable
`network.enabled` or `network.m3_acquire_enabled` — both remain `false`. It creates no migration
`0016`. It accepts neither Decision 137, 138, 141, 142, 143 nor itself.

**The future canary authorization must explicitly authorize the multi-process sequence.** Building
the mechanism is not permission to use it.

The phase-path modules are asserted to name **no** activation constant, **no** network switch and
**no** transport symbol at all, and a fresh interpreter that imports the whole phase path loads no
E0 module and no transport library.

## 16. `_parse_bulk` remains canary-unreachable

[Decision 143](decision_143_m3_3_final_independent_precanary_review.md) proved
`census_orchestrator.py::_parse_bulk` canary-unreachable under the frozen first-canary production
path. **This record does not change that, and the reachability was independently re-traced after
the phase decomposition rather than assumed to have survived it.**

Three ways, because one alone would be an argument rather than a proof: no phase-path module names
`census_orchestrator`, `CensusOrchestrator` or `_parse_bulk`; a fresh interpreter that imports the
whole phase path never loads the orchestrator module; and the phase entry points reach it through
no call. Process decomposition, the new entry points and the continuation logic leave it exactly
where D143 found it.

**It remains an open pre-network blocker and is deliberately unrepaired here.** It must be repaired
before any network or live-retrieval authorization.

## 17. Implementation shape and the change set

**One OS process per major execution phase**, using the existing canonical phase entry points.

The three phases were **extracted** from the whole-run path into `_f0`, `_f1` and `_f2` and are
called by both paths, so the phase sequence and `--mode run` execute the *same* F0, F1 and F2
rather than two implementations that must be kept in step. Evidence recording was likewise
refactored to one implementation given plain values, so the sidecar receives the same rows by the
same rule whether they were produced a microsecond ago or read back from a checkpoint.

| Path | Change |
|---|---|
| `m3/canary_phases.py` | **new.** The phase vocabulary, the durable checkpoint, its create-once write, and the admission that refuses. |
| `m3/single_source_canary.py` | `run_single_source_canary_phase`, `attach_world`, `CanaryPhaseResult`, `phase_execution_identity`, `PHASE_ADMISSION_FLOOR`, `CANARY_PHASE_MODES`, the three extracted phase primitives, and the operator routing. |
| `m3/working_catalog.py` | `RunProgressLedger.record_value` / `recorded_value`; `WorkingCatalog(attach=True)`, the exact inverse of creation. |
| `m3/canary_runtime.py` | `process_is_live_canary`, `process_peak_resident_bytes`. |
| `m3/external_working_root.py` | `minimum_free_bytes` threaded through the envelope, defaulting to the launch floor so every existing caller is unchanged. |
| `cli.py` | the three phase modes and their help. |

**The CLI change is explicit, fail-closed, testable and non-bypassable.** One mode per phase —
`--mode phase-f0|phase-f1|phase-f2` — rather than a mode/phase pair that could disagree, so the
phase a governed run was launched under is legible in `ps` output and in the host lock's own
detail record. **There is no environment-variable backdoor and no debug-only bypass**: a
continuation consumes the durable canonical phase state or it refuses.

**`--mode run` is not removed and is not weakened.** The accepted Decision 116 whole-run path
behaves exactly as before. See the limitation in §24 item 2.

## 18. The test matrix

`tests/unit/test_d145_phase_restart.py` — **68 tests**, every refusal asserted through a production
entry point, every topology, volume, power state and lid state synthesised through the provider
seams Decisions 137–144 already use. Nothing depends on the operator's SSD being attached.

| Item | Covered by |
|---|---|
| A complete predecessor admits successor | the three-phase sequence completes; each phase records its terminal; the equivalence proof |
| B incomplete predecessor refuses | an absent world; **committed rows with the checkpoint deleted** |
| C failed predecessor refuses | a blocking F0 leaves no checkpoint, and F1 refuses |
| D wrong run id refuses | a checkpoint rewritten to another run |
| E wrong checkpoint identity refuses | a checkpoint naming another phase; another contract; another source |
| F wrong configuration refuses | a governing constant moved |
| G wrong code/revision refuses | the package version moved |
| H / I wrong and missing UUID refuse | parameterized over **all three** phases |
| J / L wrong and unqualified transport refuse | parameterized over all three phases |
| K qualified `USB_DIRECT` refuses | parameterized over all three phases, plus every operator phase mode |
| M / N battery and closed lid refuse | parameterized over all three phases |
| O D130 violation refuses | parameterized over all three phases |
| P bad `SQLITE_TMPDIR` refuses | parameterized over all three phases |
| Q host lock conflict refuses | parameterized over all three phases |
| R network remains disabled | no network switch named; no transport library loaded |
| S authority bypass refuses | no activation constant named; all three remain `None` |
| T predecessor is not rerun | detonation on F0's and F1's entry points |
| U successor is not duplicated | a completed phase and a finished run both refuse |
| V old PID ≠ new PID | the three-process demonstration |
| W old process is gone | a live predecessor refuses; a recycled id is not a live predecessor |
| X `_parse_bulk` unreachable | three independent re-traces |

Generic parameterization is used where a boundary-specific difference does not exist, and **the
per-phase parameterization is what stops the matrix passing by testing one boundary only**.

**The equivalence proof deserves its own sentence.** The phased result document is compared against
a whole run, and the set of fields that differ is required to be *exactly* the set that differs
between **two whole runs** of the same source into two worlds — a baseline measured in the test
rather than assumed. That baseline is `run_id`, the two timestamps, the two free-space
measurements, and the working catalog's file digest. Every identity, every count, the association
totality, the resolution evidence, the disposition and the parser states are **identical**.

## 19. The bounded falsification campaign

Fifteen reversible, source-isolated mutations. **15 applied, 15 killed, 0 survivors.** Every
mutated file was restored and the restoration proved by SHA-256 comparison against the pre-mutation
digest.

| # | Mutation | Killed by |
|---|---|---|
| M1 | a qualified boundary accepts an incomplete predecessor | 2 failures |
| M2 | a failed phase can record itself as a terminal | 1 |
| M3 | the successor skips volume UUID reauthentication | 6 |
| M4 | the successor skips transport reauthentication | 4 |
| M5 | the successor admits `USB_DIRECT` for the first canary | 4 |
| M6 | the successor skips AC-power reauthentication | 3 |
| M7 | the successor skips lid reauthentication | 3 |
| M8 | the successor accepts a wrong run/checkpoint identity | 4 |
| M9 | the predecessor phase is rerun after the restart | 1 |
| M10 | a successor phase can execute twice | 1 |
| M11 | an activation constant is minted on this path | 1 |
| M12 | the tracked network gate is bypassed | 1 |
| M13 | the continuation trusts stale in-memory state | 1 |
| M14 | same-process continuation replaces process replacement | 1 |
| M15 | `_parse_bulk` becomes reachable | 1 |

**M2 is recorded honestly rather than counted quietly.** The *admission-side* status guard is
unreachable by construction — no checkpoint is ever written with a status other than `complete` —
so mutating it would have survived for a reason that proves nothing. The reachable expression of
"a failed predecessor is accepted" is the **write-side** guard that makes failed state
unrecordable, and that is what was mutated and killed.

**The campaign cannot pass by testing one boundary.** M3–M7 are killed by tests parameterized
across all three phases; M1, M8 and M10 by tests that exercise both boundaries.

## 20. The bounded memory-reclamation demonstration

Disposable bounded fixtures only — the hostile Decision 112 synthetic world. **The real
complete-source canary was not run, no real world was created, and this is not a performance
benchmark.**

Three phases, three genuinely separate operating-system processes, launched through the real
operator command with `subprocess.Popen` so that the operating system's own process id is observed
independently of what each phase reports about itself:

```text
process A  --mode phase-f0  ->  POST_F0 terminal, checkpoint written, clean exit
                                pid and peak RSS recorded
   old PID proved gone
process B  --mode phase-f1  ->  fresh process, initial peak RSS recorded,
                                predecessor checkpoint and world reauthenticated,
                                PRE_F1 and POST_F1_PRE_F2 recorded, clean exit
   old PID proved gone
process C  --mode phase-f2  ->  fresh process, reauthenticated, pre-F2 gate,
                                F2, evidence, create-once result document, clean exit
```

The demonstration asserts: **three distinct process ids**; that each reported id **is** the
operating system's id for that child; that each successor recorded its predecessor's id and
`predecessor_process_gone = True`; that none of the three is alive afterwards; that the accepted
catalog is byte-identical after every phase; that a peak resident size was measured at every
terminal; and that the five accepted identities in the resulting document equal those of a whole
run over the same source. **No phase executed twice and no committed state was lost.**

## 21. The RAM policy for the future real canary

At **every** D145-qualified major phase boundary — which is every inter-phase boundary the first
canary has:

1. the phase reaches durable terminal success;
2. the terminal checkpoint is verified;
3. the current process **exits cleanly**;
4. the old process id is confirmed terminated;
5. the successor starts as a **fresh process**;
6. the successor reauthenticates the full relevant world;
7. the successor continues **only** if every predicate passes.

**There is no operator discretion to skip the restart because resident size "looks fine."** The
restart is part of the governed canary execution procedure unless a future canary authorization
explicitly changes this rule.

**The volume stays attached throughout.** Steps 3 to 5 are a process ending and another starting;
they are not a window in which anything may be unplugged, unmounted, ejected, slept, or re-plugged
into a different topology.

## 22. D145-R0 — the Decision 140 acceptance-lineage normalization

**Performed before any D145 architecture or source mutation, and validated before implementation
began.** It is governance normalization only.

**The defect.** The registry recorded Decision 140 as `IMPLEMENTED — PENDING INDEPENDENT REVIEW AND
OWNER ACCEPTANCE` with **no acceptance token**, while the controlling owner lineage already carried
one.

**The evidence, traced rather than assumed.** Exactly one D140 acceptance-shaped owner instrument
exists in the repository and in its entire git history — `M3_3_D140_CORRECTED_PUBLICATION_BASELINE_OWNER_ACCEPTED_FOR_CONTINUATION`
— published as [Decision 141](decision_141_m3_3_thunderbolt_dock_qualification.md)'s
`ENTRY_BASELINE`, carried forward by the registry's D141 row and by the status ledger. There is **no
competing candidate**, so the token is unambiguous. Its `_OWNER_ACCEPTED_FOR_CONTINUATION` form is
the repository's own convention, identical in shape to `M3_3_D141_OWNER_ACCEPTED_FOR_CONTINUATION`.
Its timing matches the owner's ruling exactly: it is the baseline D141 *entered on*, so it was
issued **before** Decision 141. It accepts the **corrected** publication baseline — Decision 140 as
repaired at `cf9cd34c01e2ede295d562c8eb9f56344247b021`, which is the HEAD Decision 141 §2 records
entering on. The same status-ledger line that carried the token also asserted that D140 was not
owner accepted, which is the contradiction itself.

**The inconsistency is metadata only, verified rather than asserted.** No file under `src/`,
`tests/` or `scripts/` contains any of the strings `PENDING INDEPENDENT REVIEW`, `OWNER
ACCEPTANCE` or `OWNER_ACCEPTED`; no executable semantics depend on D140 being marked pending; and
correcting it required no reinterpretation of any technical ruling.

**What was corrected.** Two surfaces: the registry's Decision 140 row now reads
`ACCEPTED — OWNER ACCEPTED FOR CONTINUATION 2026-08-23`, cites the accepting owner instrument,
carries the token, and its `Binding, once accepted, for …` clause becomes `Binding for …`; and the
decision index gains a `Whether Decision 140 is owner accepted` row. **The convention followed is
the one D144-R4 set one commit earlier for Decision 141**: the decision record's own header is
left as **history** — it claimed no acceptance when it was published, and its acceptance came
separately and later — while the registry, index and ledger carry the current state.

**What was not touched.** No D140 technical ruling; no D140-R1 – D140-R23 safety predicate; no
Decision 141, 142, 143 or 144 content; no source, test, configuration or migration path. **Decisions
137 and 138 are NOT accepted by this** and remain `IMPLEMENTED — PENDING INDEPENDENT REVIEW AND
OWNER ACCEPTANCE`. Decision 143 is **not rewritten**: its `FAIL` verdict stands, and the D143-R1
interpretation that matters — that a superseded record's unreplaced safety predicates remain
inherited and enforced — is preserved entire. **`ACCEPTED` is not `LATEST CONTROLLING RECORD`, and
`SUPERSEDED` is not `REVOKED`.**

**Validated before implementation began**: decision section references, markdown links, secret
scan and repository hygiene all passed; the worktree carried exactly the two authorized
documentation surfaces and no source, test, configuration or migration change; migration head
`0015` with `0016` absent; all three activation constants `None`; both network gates `false`; the
canary unauthorized.

## 23. Validation

| Gate | Result |
|---|---|
| `tests/unit/test_d145_phase_restart.py` | `68` passed |
| Falsification campaign | `15` mutations, `15` killed, `0` survivors, all files restored byte-identical |
| Bounded memory demonstration | three distinct processes, each proved gone before its successor ran |
| Ruff lint and format | clean across `src/` and `tests/` |
| mypy strict over `src` | clean, `97` source files |
| Full acceptance gate | `make check-fast` — see the completion report |

The real canary was not run, E0 was not run, no network was enabled, no physical detach was
performed, the D130 archive was never opened, migration `0016` was not created, and the multi-GiB
D141 storage qualification was not repeated.

## 24. Limitations, stated rather than smoothed

| # | Limitation | Classification |
|---|---|---|
| 1 | **The host execution lock is released between phases and re-taken by the next process.** At most one canary *process* executes on this host at any moment, which is what the capacity model needs — but a *sequence* no longer holds the lock end to end, so another canary could start in the gap. If one does, this sequence's next phase refuses on the lock conflict, which is fail-closed for this run and is not a mechanical bar on the intruder | **NON-BLOCKING BOUNDED LIMITATION.** It is an operator rule, and it is now written in the runbook |
| 2 | **`--mode run` still exists, and choosing the phase sequence is an operator act.** Every predicate *within* the sequence is mechanical and non-bypassable; which mode is typed is governed by the runbook and by the future canary authorization, not by a refusal in code | **NON-BLOCKING BOUNDED LIMITATION**, and deliberate: removing the accepted D116 whole-run path is a redesign this record was not authorized to make |
| 3 | **`ru_maxrss` is a peak, not an instantaneous sample** | **NON-BLOCKING.** Named as a peak everywhere it appears |
| 4 | **The launch predicates are read at launch of each phase and are not re-checked during it** — exactly as D144 records for power, lid and transport. A restart makes the check *more* frequent, not continuous | **NON-BLOCKING BOUNDED LIMITATION**, unchanged in kind |
| 5 | **The F1→F2 boundary is now durably observable.** Decision 126 §7's *rationale* said nothing durable changes at that boundary, as an argument for why an external sampler cannot admit F2. The **ruling** is untouched: the pre-F2 gate is still taken by the process that opens the transaction, immediately before it opens, in the same process. Only that one sentence of rationale ceases to describe the phase-restart shape | **NON-BLOCKING.** Recorded rather than left for a reader to discover |
| 6 | **The attach path does not repeat `PRAGMA integrity_check`** — see §10 | **NON-BLOCKING BOUNDED LIMITATION**, stated with its reason |
| 7 | **`F_FULLFSYNC` remains OS-visible evidence only**, and no physical power-loss or disconnect qualification exists | **NON-BLOCKING BOUNDED LIMITATION**, inherited unchanged from D141 and D143 |

## 25. What did not change

The frozen research definitions; the preregistration; every cohort window, maturity gate,
threshold and the bootstrap seed; the parser; the evidence contract `e0-compact-evidence/2`; the
five accepted identities; the association-totality invariants; every capacity floor; the qualified
volume; the selected topology; the D130 archive; migration head `0015`; all three activation
constants; both network switches; and the unrepaired `_parse_bulk` blocker.

## 26. Result token and the next owner boundary

```text
PHASE_BOUNDARY_RAM_RECLAMATION = IMPLEMENTED
GOVERNED_PAUSE_RESUME = NOT_IMPLEMENTED
SAFE_TO_EJECT = NOT_IMPLEMENTED
CANARY_AUTHORIZED = NO

M3_3_D145_GOVERNED_MAJOR_PHASE_RAM_RECLAMATION_COMPLETE_READY_FOR_OWNER
```

**Next authorized action: STOP.** Return Decision 145 to GPT-5.6 Sol. **Do not start the canary**,
which remains unauthorized and needs a separate owner instrument that has not been issued. **Do not
perform the independent re-review in the session that made these changes.**
