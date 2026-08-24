# Decision 146 — Final Independent Post-D145 Pre-Canary Review

```text
STATUS: PUBLISHED — INDEPENDENT REVIEW RECORD
RECORD_TYPE: INDEPENDENT REVIEW — NO SOURCE CHANGE, NO TEST CHANGE, NO REPAIR
DATE: 2026-08-23
OWNER: Joey authorization; independent review performed by Claude Opus 5 at maximum effort
CLASSIFICATION: ADVERSARIAL REVIEW OF DECISION 145 — FINDINGS RECORDED, DELIBERATELY NOT REPAIRED
AUTHORIZATION:
  M3_3_D146_FINAL_INDEPENDENT_POST_D145_PRECANARY_REVIEW_AUTHORIZED — spent by the publication of
  this record
REVIEWED_PREDECESSOR: M3_3_D145_GOVERNED_MAJOR_PHASE_RAM_RECLAMATION_COMPLETE_READY_FOR_OWNER

REVIEWED_HEAD: 69a73d99a2aa5aafeb905d3fcfd40dba6f88e68d
REVIEWED_TREE: 1ab21d76913e367d972b024c5c1fb006160d52b6

VERDICT: D146_FINAL_INDEPENDENT_POST_D145_PRECANARY_REVIEW_FAIL
FINDINGS: 0 BLOCKER / 1 MAJOR / 2 MINOR / 7 OBSERVATION

MAJOR_PHASE_COUNT: 3 — F0, F1, F2 (independently reconstructed, not inherited)
QUALIFYING_BOUNDARIES: 2 of 2 — F0→F1, F1→F2; post-F2 is TERMINAL_PROCESS_EXIT_EXPECTED
PROCESS_REPLACEMENT: SUBSTANTIATED — three real OS processes, distinct pids, predecessor proved gone
CHECKPOINT_DURABILITY: SUBSTANTIATED — terminal-only, create-once, written last
CODE_CONTINUITY: NOT SUBSTANTIATED — see MAJOR-1
HOST_LOCK_GAP: ACCEPTABLE_LIMITATION
PARSE_BULK_REACHABILITY: PROVABLY CANARY-UNREACHABLE — independently re-traced
AUTHORITY_BYPASS: NONE FOUND
NETWORK_BYPASS: NONE FOUND
EQUIVALENCE: SUBSTANTIATED — 6 variable fields, 55 identical, measured rather than asserted

CANARY_AUTHORIZED: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_HEAD: 0015 — 0016 ABSENT
ALL_THREE_ACTIVATION_CONSTANTS: None
NETWORK: enabled=false, m3_acquire_enabled=false
GOVERNED_PAUSE_RESUME: NOT_IMPLEMENTED
SAFE_TO_EJECT: NOT_IMPLEMENTED
SOURCE_AND_TEST_CHANGE: NONE
```

## 1. What this record is, and what it is not

It is the independent adversarial review of
[Decision 145](decision_145_m3_3_governed_major_phase_restart.md) that Decision 145 §26 required and
that the session which wrote Decision 145 was forbidden to perform. It was performed from a
genuinely fresh session context, with no subagents, no delegated reasoning and no parallel sessions,
and **Decision 145's conclusions were not inherited** — the phase inventory, the boundary
classification, the reachability of `_parse_bulk` and the D140 acceptance lineage were each
reconstructed from the repository before Decision 145's own account of them was read.

**It repairs nothing.** The authorization classifies defects and forbids fixing them. No file under
`src/`, `tests/`, `scripts/`, `configs/` or `src/disclosure_drift/storage/migrations/` is changed by
this publication.

**It accepts nothing.** A `PASS` would not have owner-accepted Decision 145, and this `FAIL`
accepts neither Decision 137, 138, 141, 142, 143, 144 nor 145. Decisions 137 and 138 remain
`IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER ACCEPTANCE`.

**Bounded falsification was performed and completely restored.** Four temporary source mutations
were applied to resolve material review questions, each proved restored byte-identical by SHA-256
and by an empty `git diff`, before this record was written. No accepted evidence was touched, no
world was created, and **no real canary was executed**.

## 2. Entry state

Verified live through `make context` and `git`, not taken from a document:

| Fact | Expected | Observed |
|---|---|---|
| Branch / HEAD | `main` / `69a73d99…8e68d` | **match** |
| Tree | `1ab21d76…d52b6` | **match** |
| `origin/main` vs HEAD | equal, `0/0` | **match**, worktree clean, nothing staged, no untracked residue |
| Tag at HEAD | none | **match** |
| Migration head | `0015`; `0016` absent | **match** — 15 migrations, `0015_m33_verified_document_evidence.sql` |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` | **match** — `m3/e0.py:179` |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` | **match** — `m3/e0.py:201` |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` | **match** — `m3/e0.py:446` |
| `network.enabled` / `network.m3_acquire_enabled` | `false` / `false` | **match** — tracked `configs/project.yaml` |
| `canary_authorized` | `false` | **match** — `m3/external_working_root.py:1224` |
| D145 CI | run `32681301791`, both mandatory jobs success | **match** — `success` at exactly `69a73d99…8e68d`; it is the only run at that SHA |

No controlling entry predicate differs. `ENTRY_STATE_MISMATCH` is **not** raised.

## 3. The independently reconstructed major-phase inventory

Derived by reading `single_source_canary.py` before reading Decision 145 §§3–4.

**Three major execution phases, and exactly three.** The whole-run driver `_materialize`
(`single_source_canary.py:1478`) calls precisely three phase primitives — `_f0` (`:1395`), `_f1`
(`:1440`) and `_f2` (`:1461`). There is no fourth.

| Phase | What it is | Production entry point |
|---|---|---|
| `F0` | the one-source parse | `run_single_source_canary_phase(phase="f0", …)` → `_phase_f0_body` → `_f0` |
| `F1` | the Decision 012 resolution pass over every persisted accession | → `_phase_f1_body` → `_f1` |
| `F2` | the Decision 094 §6.4 association projection | → `_phase_f2_body` → `_f2` |

**The names are not invented by Decision 145.** `F0`/`F1`/`F2` are the accepted Decision 135 §11
capacity vocabulary already carried by `external_working_root.CAPACITY_PHASES` and by the accepted
boundary labels `POST_F0`, `PRE_F1`, `POST_F1_PRE_F2`, `POST_F2`.

**World creation is not a fourth phase.** `create_world` is a `mkdir` inside F0's own process, before
`_f0` runs; it emits no checkpoint and admits no successor. **Result publication is not a fifth.**
`_write_once(world.result, …)` runs inside F2's own process, between F2's last durable write and F2's
terminal checkpoint. Neither is a boundary at which a process could end and another begin.

**Every inter-phase boundary, classified independently:**

| Boundary | Classification | Why |
|---|---|---|
| `F0 → F1` | **`QUALIFIED_MAJOR_RESTART_BOUNDARY`** | F0's evidence is durable in the compact sidecar plus the checkpoint payload; `persist_streamed`'s create-once short-circuit is untouched. D140 §17 (A1-R23.1) proved it sound |
| `F1 → F2` | **`QUALIFIED_MAJOR_RESTART_BOUNDARY`** | F1 is idempotent by construction; the D126 §7 pre-F2 gate stays inside the process that opens F2's transaction. D140 §17 (A1-R23.2) proved it sound |
| post-`F2` | **`TERMINAL_PROCESS_EXIT_EXPECTED`** | `PHASE_SUCCESSOR[PHASE_F2] is None`; the next stage is E0, and no continuation was invented to manufacture a third restart |

**2 of 2 qualifying boundaries.** The reconstruction agrees with Decision 145 §§3–5 on every point,
having been derived without reference to it.

## 4. Core verdict on Decision 145

**The restart architecture is sound, and one claim it makes about itself is not.**

Decision 145 establishes a genuine, durable, governed OS-process boundary after every qualifying
major phase. RAM belonging to a completed phase is reclaimed by the only mechanism that reclaims
it — the process ending — and it is reclaimed before the successor may begin. Durability, topology,
capacity, identity, exactly-once, interruption, authority, network, evidence and working-catalog
contracts were each examined and **none is weakened**. Nine of the ten review axes are substantiated.

The tenth is not. Decision 145 §12 asserts that `phase_execution_identity()` mechanically prevents
"a process continuing **from a revision whose governing semantics moved**", and labels it "**code**
and configuration identity". It binds eleven frozen constants and a package version string that has
never changed in the project's history. Executable governing semantics can move arbitrarily while
the admitted identity is bit-identical, and this review proved it by mutation rather than argued it.
No other accepted mechanism closes the gap.

That is `MAJOR-1`, and it is why the verdict is `FAIL`.

## 5. D146-R1 — code, configuration and executable-semantics continuity

**Answered separately, as the authorization required.**

`phase_execution_identity()` (`single_source_canary.py:2139`) folds exactly eleven values through
`canary_phases.execution_identity()`, a pure SHA-256 over canonical JSON:

`canary_contract`, `restart_contract`, `evidence_contract`, `resolution_scope`,
`required_transport`, `qualified_volume_uuid`, `batch_size`, `launch_minimum_free_bytes`,
`pre_f1_minimum_free_bytes`, `pre_f2_minimum_free_bytes`, `package_version`.

**A. Does it bind configuration?** **Partly, and honestly.** This path reads no configuration file —
verified: no phase-path module names a configuration key, and the composed envelope takes its values
from module constants. For that path, those constants *are* the configuration, so the digest is a
faithful configuration identity **for the ten constants it folds**. It binds neither network switch
and no activation constant, which is correct — those are refused elsewhere and are not continuation
parameters.

**B. Does it bind executable governing code?** **No.** Not one input is derived from the content of
any source file.

**C. Does it bind repository revision, source digests, or an equivalent semantic code identity?**
**No.** `package_version` is `disclosure_drift.__version__`, which is the literal `"0.1.0"` at
`src/disclosure_drift/__init__.py:13` and has held that value since commit
`fa16668b98d21c35f687944c7428c1965cbca2d7` — the Milestone 1 foundation commit, and the only commit
in the entire history that has ever touched it. Across one hundred and forty-five decision records it
has never moved. As a code identity it has zero discriminating power.

**D. Can implementation behavior change while all hashed constants remain unchanged?** **Yes, and it
was proved rather than asserted.** Two bounded mutations were applied simultaneously:

* `POST_F0_MINIMUM_FREE_BYTES` relaxed from `60 * 1024**3` to `1 * 1024**3` — an accepted, enforced,
  execution-governing capacity floor;
* the predecessor terminal-status guard deleted outright from `require_phase_admission`.

```text
execution_identity @ HEAD          ef0b492c03ccd5b154eca8c0c3cd27463cab0686ac69b34a89b0fc66a339a69b
execution_identity @ mutated       ef0b492c03ccd5b154eca8c0c3cd27463cab0686ac69b34a89b0fc66a339a69b
```

Bit-identical. Both files were restored and the restoration proved by SHA-256
(`90f96a35…fe9a01` for `external_working_root.py`, `2e237be9…de25a` for `canary_phases.py`) and by an
empty `git diff`.

**E. Can F1/F2 then accept an F0/F1 checkpoint produced by the prior implementation?** **Yes.** The
only code-identity gate in the admission path is
`_require_identity(predecessor, "execution_identity", …)` (`canary_phases.py`), a string comparison
against the recorded digest. Equal digests admit.

**F. Does another accepted mechanism independently close that gap?** **No.** An exhaustive search of
`src/` for a git SHA, source digest, build identity, module checksum or any equivalent semantic code
identity returns nothing. The four continuity mechanisms Decision 145 §12 names are run identity,
plan fingerprint, catalog digest and this digest; the first three are **data** identities and none of
them moves when code moves. The migration head binds schema, not semantics.

**The exception in the owner's ruling cannot be discharged.** The property is not merely absent from
the accepted contract — Decision 145 §12 **asserts** it, mechanically, as one of four load-bearing
continuity guarantees, in the record now before the owner for acceptance. An asserted-but-false
mechanical guarantee in the record being adjudicated is exactly what requires correction before
acceptance. Accordingly the finding is `MAJOR`.

**What is *not* claimed here.** The digest is sound for what it folds, and folding constants was a
reasonable design choice. The realistic exposure is bounded: one operator, one machine, one governed
checkout, a window of hours, and a repository in which source changes are decision-gated. This is a
correctness-of-claim defect with a real but narrow exploitation surface, not a live corruption
channel. The remedy is the owner's choice between binding a genuine code identity and narrowing the
claim in §12 to what the digest actually does.

## 6. D146-R2 — true process replacement and RAM reclamation

**Substantiated.** The production mechanism is genuinely one OS process per phase.

`tests/unit/test_d145_phase_restart.py::test_the_three_phases_run_in_three_different_processes_and_each_one_ends`
drives the sequence with `subprocess.Popen([sys.executable, "-m", "disclosure_drift", "m3",
"canary-source", "--mode", f"phase-{phase}", …])` — the **real operator command**, not an in-process
call — and `child.communicate()` waits for each process to actually exit with return code `0`.

Every rejected interpretation was checked and none applies. There is no `gc.collect()`, no cache
clearing and no same-process continuation on the phase path. The parent is the test runner, which
never holds the phase's working set: the entire phase executes in the child, so this is not "a
subprocess whose large parent remains resident". No RSS percentage threshold exists anywhere.

Verified specifically:

* **genuinely distinct OS PIDs** — three, asserted as a set of size three, and each phase's
  self-reported `pid` is asserted **equal to `child.pid` observed by the parent**, so the proof does
  not rest on self-report;
* **terminal state durable before successor admission** — the checkpoint is written last, after the
  working catalog's context has closed, through a short-lived ledger handle in `synchronous = FULL`
  WAL autocommit;
* **successor refuses a live predecessor** — `_run_phase_locked` raises when
  `process_is_live_canary(predecessor.pid, run_id=run_id)`, before any work begins;
* **PID reuse matches D140-R18** — `process_is_live_canary` never asks whether the number is in use.
  A recycled id running something else reads *gone*; only a process carrying `m3 canary-source`
  adjacently **and** `--run-id` with exactly this identity reads *alive*. `--run-id` is a required
  CLI argument, so a real predecessor always matches;
* **predecessor identity comes from durable state** — `predecessor.pid` is read from the
  predecessor's own checkpoint and from no operator input and no scan;
* **process exit is the reclamation property** — asserted as such, with all three ids proved not live
  afterwards;
* **`ru_maxrss` is reported only as peak evidence** — `process_peak_resident_bytes()` is documented
  and named as a peak, platform-normalized, and no test or guard compares it against a floor.

No real complete-source canary was executed by this review.

## 7. D146-R3 — checkpoint durability and atomicity

**Substantiated.**

* **terminal-only** — `PHASE_STATUS_COMPLETE` is the only status the writer accepts; there is no
  `in_progress` and no `failed` value in the vocabulary;
* **no in-progress or failed state can masquerade as completion** — `write_phase_checkpoint` refuses
  any other status, and `require_phase_admission` independently requires the predecessor's status to
  be `complete`;
* **written only after durable completion** — `_write_terminal_checkpoint` is reached only when the
  phase body returned without raising and the `WorkingCatalog` context has exited;
* **create-once** — a checkpoint already present for that phase is refused, never overwritten;
* **commit semantics** — `RunProgressLedger` opens with `isolation_level=None` (autocommit),
  `PRAGMA journal_mode = WAL` and `PRAGMA synchronous = FULL`, so each write is its own committed,
  fsynced transaction. The pragmas are set on the connection that performs the write, so they do
  apply to this path;
* **ledger handle closure** — `_write_terminal_checkpoint` closes its handle in a `finally`, and
  `WorkingCatalog.__exit__` closes its own;
* **writer closed before the terminal checkpoint** — verified structurally: the checkpoint is written
  outside the `with WorkingCatalog(...)` block;
* **identity binding** — run, source, execution, catalog digest, migration head and plan fingerprint
  are all recorded and all compared;
* **existence is never completion** — a populated world, a working catalog holding every row F0
  wrote, and a ledger reading `parsed` are each insufficient without the checkpoint, and that exact
  case is tested by deleting the checkpoint and leaving every durable row behind.

**The F2 interval was analysed specifically.** The result document is written **before** F2's terminal
checkpoint. In the window where the result exists and the checkpoint does not:

* `attach_world` refuses any world that already carries its result document — *"a finished run is
  never re-entered"* — so `phase-f1` and `phase-f2` both refuse;
* `create_world` refuses the existing world, so `phase-f0`, `--mode run` and `--mode profile-prefix`
  refuse on that identity too.

The semantics are therefore **REFUSE continuation, do not rerun, treat the run as interrupted**, with
the deliverable intact. That is deliberate, is compatible with the create-once world contract, and is
**not** resumability. This review does not relabel it as such.

## 8. D146-R4 — the host execution lock gap

`acquire_canary_execution_lock` takes a non-blocking exclusive `flock` on a file in the private root,
keyed to the host rather than to `run_id`, and releases it in a `finally` when each phase process
ends. Between phases, no canary holds it.

Five interleavings were constructed and each was traced through the code:

| Intruder in the gap | Capacity | Data | Exactly-once | Original run |
|---|---|---|---|---|
| another canary run starts (new `run_id`) | **safe** — every phase re-measures free space live and enforces its accepted floor | **safe** — it builds its own world; `create_world` cannot reach this one | **safe** | **fail-closed** — refuses if the lock is held, or if the floor no longer clears |
| another process targets this run/world | **safe** | **safe** — `create_world` refuses the existing world | **safe** — the phase's own checkpoint refuses re-entry | **fail-closed** |
| another phase invocation of this run | **safe** | **safe** | **safe** — completed phase refused; absent predecessor refused | **fail-closed** |
| another run's phase takes the lock | **safe** | **safe** | **safe** | **fail-closed** — this run's next phase refuses to start |
| an unintended process runs first (`--mode run`, `profile-prefix`, E0, acquisition) | **safe** | **safe** — every world-creating mode is create-once; E0 and acquisition refuse at `None` authorities and `false` gates | **safe** | **fail-closed** |

**Decision 145's claim is proved.** An intruder in the gap can cause the original run's successor to
**refuse**; it cannot silently corrupt, duplicate or advance it. The three properties that make this
hold are that the world directory is named by `run_id` and is create-once, that capacity is
re-measured inside the lock at every phase, and that phase advancement is gated on a durable
checkpoint rather than on anything that merely exists.

What genuinely changed is that a *sequence* no longer holds the lock end to end. The accepted D140-R16
requirement is that two canaries never each measure the same free space as though alone, and that
still holds exactly: at most one canary **process** runs at any moment. The residual is
operator-governance — an operator can waste a run by starting another canary between phases — which is
a runbook matter, and Decision 145 §24 item 1 states it rather than smoothing it.

**Classification: `ACCEPTABLE_LIMITATION`.** Not repaired here.

## 9. D146-R5 — `--mode run` still exists

**A. Is the new three-process mechanism itself safe?** Yes, subject to `MAJOR-1`.

**B. Was Decision 145 required to remove `--mode run`?** **No.** Removing it was outside the
authorization, would have deleted the accepted Decision 116 whole-run path, and would have destroyed
the very baseline the equivalence proof measures against. Decision 145 was right not to.

**C. Can the future owner authorization safely make mode selection a governance boundary?** **Yes.**
Typing `--mode run` cannot damage an in-flight phased run: on that run's identity every world-creating
mode refuses at `create_world`, and on a fresh identity it is simply a different run. The failure mode
is wasted time, not corruption. The real canary already requires a future owner instrument that does
not yet exist, and naming the permitted modes inside it is the same governance mechanism that gates
every other real-execution surface in this repository.

**D. Is an authorization limited exactly to the six steps sufficient?** **Yes.**

**E. Or must code mechanically refuse `--mode run`?** **Not required.** It remains available to the
owner as a hardening if they prefer a mechanical bar to a governance one.

**Accordingly, and as the authorization directs, this record states the requirement:**

> **The future real-canary authorization MUST authorize only `--mode phase-f0`, `--mode phase-f1` and
> `--mode phase-f2`, each in its own process with a clean exit between them; it MUST forbid
> `--mode run` for the authorized real canary; and any `--mode run` invocation against the authorized
> real canary is OUTSIDE AUTHORITY.**

`--mode run` is not removed by this record.

## 10. D146-R6 — fresh-process reauthentication

**Substantiated for F1 and F2 independently.** `run_single_source_canary_phase` re-establishes every
predicate in the successor's own process, before anything is measured, opened, created or attached to:

| Predicate | Where |
|---|---|
| external work-root boundary | `require_canary_work_root` |
| accepted D137/D142 envelope | `require_external_envelope`, guards 1–8 |
| Volume UUID `397A4D4A-9508-391E-814E-3B533C7BD049` | `require_qualified_volume`, exact match, mandatory assertion |
| required transport | `require_qualified_transport(required=FIRST_CANARY_REQUIRED_TRANSPORT)` |
| AC power and open lid | `require_launch_power_conditions` |
| D130 isolation | `require_outside_d130_archive` |
| bounded archive precheck | `verify_d130_archive`, tar `stat`-ed and never opened |
| external `SQLITE_TMPDIR` | `require_external_sqlite_tmpdir` |
| host execution lock | `acquire_canary_execution_lock`, re-taken per phase |
| accepted-catalog digest | `_attach_existing`, compared against the digest recorded at copy time |
| working-catalog migration chain | `_verify_attached` |
| run / source / plan / migration / execution identity | `require_phase_admission` |
| predecessor terminal checkpoint | `read_phase_checkpoint` |
| predecessor process gone | `process_is_live_canary` |
| phase-specific free-space gate | `PHASE_ADMISSION_FLOOR[phase]`, then re-enforced by `record_phase` |

**The floors are the accepted ones and none is invented.** `PRE_F1_MINIMUM_FREE_BYTES = 55 * 1024**3`
and `PRE_F2_MINIMUM_FREE_BYTES = 50 * 1024**3` were read from source and match the accepted values
exactly. The launch floor stays `185` GiB for every non-continuation mode.

**The envelope tests are parameterized across all three phases** — `@pytest.mark.parametrize("phase",
["f0", "f1", "f2"])` on the UUID, transport, `USB_DIRECT`, power, lid, D130 and `SQLITE_TMPDIR`
refusals — so the coverage is not a single boundary generalized.

**The two deliberate omissions, adjudicated:**

1. **F1/F2 do not re-authenticate the source artifact or the shard-to-parent map.** **`ACCEPTABLE`.**
   Verified factually true rather than accepted on assertion: `preauthenticate_source` and `tree` are
   referenced only in the `PHASE_F0` branch and in `_phase_f0_body`; `_phase_f1_body` touches only the
   working catalog, and `_phase_f2_body` only the working-catalog connection and the earlier
   checkpoints. Re-digesting 1.5 GB to admit a phase that never opens it would buy nothing.
2. **`attach_world` does not repeat `PRAGMA integrity_check`.** **`ACCEPTABLE`.** The creating path
   runs `integrity_report` on the fresh copy, which is the moment a bad copy would be born and the
   only moment the check is affordable; at a boundary the file may be hundreds of gibibytes. The
   omission delays detection of corruption arising *after* creation; it does not admit known-bad data,
   and SQLite surfaces real corruption on access. Decision 145 §10 and §24 item 6 state it with its
   reason rather than smoothing it.

## 11. D146-R7 — working-catalog continuity

The accepted **source** catalog and the mutable **working** catalog were kept strictly separate in
this analysis.

What binds the working catalog to this run across process replacement: the world directory is
`work_root/<run_id>` and is create-once; `attach_world` refuses an absent world and a finished one;
`_attach_existing` refuses unless the run-local ledger records a working-catalog identity, the
accepted catalog is still byte-identical to the artifact this copy descends from (SHA-256 and byte
length), and the copy's applied migration chain still equals the recorded one.

**`create_world` and `attach_world` are true inverses in the sense Decision 145 claims.** Creation is
`mkdir` without `exist_ok` — atomic, so two callers cannot both believe they created the world — and
refuses an existing identity; attachment refuses an absent one; both refuse a world carrying its
result document. There is no path that creates a world for a continuation, so a successor cannot
manufacture the state it was supposed to inherit. Verified at every call site: `create_world` is
reached only from `_run_locked`, `run_single_source_prefix_profile` and the F0 branch;
`attach_world` only from the F1/F2 branch.

**One gap is recorded, and it is not a contract gap.** No digest of the working-catalog *file itself*
is recorded at creation or compared at attach, so a working catalog substituted from another run of
the same accepted catalog — same lineage, same migration chain — would pass admission, the phase
checkpoint living in the separate ledger file. Exercising this requires filesystem write access
inside the world directory on the qualified volume, and an actor with that access can equally rewrite
the ledger, the checkpoint and the result document. It is therefore outside the accepted threat model
rather than a defect within it, and this review declines to strengthen the threat model without
authority. Recorded as `OBSERVATION-1` so the owner may decide.

**Repeated `quick_check`/`integrity_check` is not contractually required** by any accepted record;
`quick_check` appears in the repository only in the shared `integrity_report` helper and on E0 and
recovery paths, never as a per-boundary obligation.

## 12. D146-R8 — idempotency and interruption

Verified through the production entry points — `run_single_source_canary_phase` for the library
surface and `run_canary_source_command` for the operator surface — rather than against internal
helpers:

| # | Condition | Result |
|---|---|---|
| 1 | current phase already checkpointed | **REFUSE** |
| 2 | predecessor checkpoint absent | **REFUSE** |
| 3 | predecessor not terminal/valid | **REFUSE** (write-side makes non-terminal unrecordable; admission refuses anyway) |
| 4 | wrong run | **REFUSE** |
| 5 | wrong source | **REFUSE** |
| 6 | wrong phase | **REFUSE** |
| 7 | wrong plan / catalog / migration / execution identity | **REFUSE** — see `OBSERVATION-3` for migration head |
| 8 | populated world, absent predecessor checkpoint | **REFUSE** |
| 9 | result document already present | **REFUSE**, at `attach_world` and at `create_world` |
| 10 | F1 reruns F0 | **DOES NOT HAPPEN** — proved by detonation, `materialize_one_planned_source` replaced by a raiser |
| 11 | F2 reruns F1 | **DOES NOT HAPPEN** — proved the same way |
| 12 | failed/mid-phase emits a valid terminal checkpoint | **IMPOSSIBLE** — the writer refuses any status but `complete`, and a raising phase body never reaches the writer |
| 13 | interrupted worlds resumed/repaired/overwritten | **NEVER** — no path resumes, repairs or overwrites a world |

```text
PHASE_BOUNDARY_RAM_RECLAMATION = IMPLEMENTED
GOVERNED_PAUSE_RESUME          = NOT_IMPLEMENTED
SAFE_TO_EJECT                  = NOT_IMPLEMENTED
```

**Decision 145 did not accidentally create generalized resume semantics.** The restart right is
conditioned on a durable terminal that only a successful phase can produce. There is no cursor, no
partial-progress marker, no repair path and no `SAFE_TO_EJECT` state.

## 13. D146-R9 — topology continuity

`FIRST_CANARY_REQUIRED_TRANSPORT = TRANSPORT_DOCK = "USB_VIA_THUNDERBOLT_DOCK"` is passed at exactly
**four** production seams, traced independently:

| Seam | Line |
|---|---|
| `run_single_source_canary` | `single_source_canary.py:1123` |
| `run_single_source_prefix_profile` | `:1996` |
| `run_single_source_canary_phase` | `:2358` |
| `run_canary_source_command` | `:2997` |

At every first-canary phase launch: the qualified docked topology is admitted; `USB_DIRECT` is
refused by `require_qualified_transport`'s `observed != required` branch; there is no automatic
fallback, no operator override and no "restart on direct" — the narrowing is a module constant with
no CLI flag, configuration key or environment variable behind it; and a changed BSD identifier cannot
override the accepted identity, because the identifier is only an IORegistry lookup key taken from a
volume that has already proved its UUID and is never compared against anything.

**`USB_DIRECT` remains valid outside the narrowing.** `required=None` still admits either qualified
class, so D141-R8 and Decision 142 §5 stand entire.

**The D144 seam-count tripwire update is legitimate.** The complete diff of
`test_d144_first_canary_transport_narrowing.py` between `2389dff` and `69a73d9` is the constant `3 →
4` plus a four-line explanatory comment. The substantive assertion — the loop requiring **every**
`require_external_envelope` call in the module to carry the pin — was not touched, and now covers four
seams instead of three. The tripwire was **strengthened by the change, not loosened to make a test
pass**.

## 14. D146-R10 — the Decision 126 interaction

Decision 126 was read directly rather than through Decision 145's account of it.

**The binding ruling is D126-R6**, in §7: a subsequent implementation stage containing only one frozen
constant, **one free-space guard placed after F1 returns and before F2 is called**, and three focused
tests. The requirement is that admission "must be made *inside* the path that is about to open the
transaction".

**The explanatory rationale** is the four independently sufficient reasons why an *external sampler*
cannot satisfy that predicate.

**Decision 145 does not violate the ruling.** `_phase_f2_body` calls `_require_pre_f2_free_space`
inside `write_containment`, immediately before `_f2`, in the same process that opens the transaction.
A restart between F1 and F2 does not move the gate and could not.

**Two sentences of nonbinding rationale became historically stale**, not one. Reason 2 — *"nothing
durable changes at the boundary"* — is now false, because F1's terminal checkpoint is durable. Reason
1 — *"F1 returns and F2 begins in consecutive statements… there is no window an outside process can
occupy"* — is also no longer a description of the phased shape. **Reasons 3 and 4 are untouched, and
they are the ones that carry the ruling**: a signal remains advisory where admission must be
dispositive, and a sampling race remains regardless of cadence.

**No formal note, correction or supersession of Decision 126 is required before Decision 145 can be
accepted**, and this record does not rewrite Decision 126. The ruling is honoured; only rationale
about a rejected alternative aged. Decision 145 §24 item 5 already records this, correctly, for the
decision record — but it names only reason 2, and the **source docstring** that restates both
sentences as present fact was left uncorrected. That is `MINOR-2`.

## 15. D146-R11 — the D140-R0 acceptance-lineage normalization

Reconstructed from repository history without assuming uniqueness.

Searching the working tree and **the entire git history** for acceptance-shaped D140 instruments
returns exactly three tokens, in three distinct roles and with no competition:

| Token | Role |
|---|---|
| `M3_3_D140_TOTAL_PRE_CANARY_HARDENING_AUTHORIZED` | correction authorization, spent |
| `M3_3_D140_TOTAL_PRE_CANARY_HARDENING_COMPLETE_READY_FOR_FABLE_REVIEW` | completion token |
| `M3_3_D140_CORRECTED_PUBLICATION_BASELINE_OWNER_ACCEPTED_FOR_CONTINUATION` | **the acceptance** |

* **First appearance:** commit `1b1517b` (Decision 141), as `decision_141_*.md` line 9,
  `ENTRY_BASELINE:`. `git log --all -S` returns exactly three commits — `1b1517b`, `a414682`,
  `69a73d9`.
* **No competing token exists**, in the tree or in history. Decision 145's uniqueness claim is
  confirmed independently rather than inherited.
* **No revocation or supersession conflict** touches it.
* **It predates Decision 141 as claimed.** It is the baseline Decision 141 *entered on*, and
  Decision 141's own header reads `ACCEPTANCE_TOKEN: NONE — THIS RECORD CLAIMS NO OWNER ACCEPTANCE`,
  so the acceptance demonstrably did not come *from* Decision 141.
* **It unambiguously accepts the corrected publication baseline.** Decision 141 §2 records entering
  on HEAD `cf9cd34c01e2ede295d562c8eb9f56344247b021`, which is *"Repair the Decision 140 BSD time
  portability defect, and record the CI failure"* — the corrected D140 baseline.
* **Registry, index and ledger now represent current state correctly**, and
* **leaving Decision 140's own header at `PENDING` correctly preserves historical state**: it claimed
  no acceptance when published, and its acceptance came separately and later. This follows the
  convention D144-R4 set for Decision 141 one commit earlier.
* **Decisions 137 and 138 remain unaccepted** — verified at both surfaces, their record headers and
  their registry rows.

**No governance ambiguity was found.** D145-R0 is confirmed accurate in full.

## 16. D146-R12 — authority, network and `_parse_bulk`

At the reviewed SHA: all three activation constants are `None`; both tracked network switches are
`false`; migration `0016` is absent; `canary_authorized` is `false`. Decision 145 created **no** real
canary world, **no** real execution namespace, **no** launch receipt, **no** E0 and **no** SEC
acquisition.

**`_parse_bulk` reachability was independently re-traced after the phase decomposition**, three ways:

1. **no phase-path module names it** — `census_orchestrator`, `CensusOrchestrator` and `_parse_bulk`
   appear zero times in `canary_phases.py`, `single_source_canary.py`, `working_catalog.py`,
   `canary_runtime.py`, `external_working_root.py` and `dock_transport.py`;
2. **a fresh interpreter that imports the whole phase path never loads it** — run in this review:
   `census_orchestrator` **not loaded**, `m3.e0` **not loaded**, `httpx` **not loaded**;
3. **no dynamic escape** — no `importlib`, `__import__`, `exec` or `eval` appears anywhere on the
   phase path, so the import-closure result is the whole answer.

`_parse_bulk` therefore remains **CANARY-UNREACHABLE**. It **remains an open PRE-NETWORK blocker**,
deliberately unrepaired here and by Decision 145, and must be repaired before any network or
live-retrieval authorization.

## 17. Test, falsification and equivalence assessment

**The test suite proves what it claims, with one named exception.** 68 tests, all passing in `13.07`
s. Refusal tests drive the production entry points rather than internal helpers. The envelope
refusals are parameterized across all three phases. The subprocess test creates genuinely separate OS
processes through the real CLI and compares the parent-observed pid against the self-reported one, so
it cannot pass on self-report alone. Predecessor-rerun is proved by **detonation** — replacing the
predecessor's entry point with a raiser and requiring the successor to complete — which is a positive
control that a mock could not fake.

**The exception is `test_a_successor_refuses_a_changed_code_revision`.** It proves the property by
`monkeypatch.setattr(disclosure_drift, "__version__", "99.99.99")`. Its docstring is careful and says
"a build whose *version* moved"; its **name** claims a changed *code revision*, and Decision 145 §18.G
carries it as such. Because `__version__` has never moved in the project's history, the test is a
correct positive control for a mechanism that is inert in practice. It is cited as evidence for
`MAJOR-1` rather than as a separate finding.

**The fifteen-mutation campaign was audited, and two of its claims were re-run rather than read.**

* **M2 is honest, and this review proved both halves.** Deleting the *admission-side* predecessor
  status guard **survived all 68 tests** — confirming Decision 145's statement that the guard is
  unreachable by construction, because no checkpoint with a non-`complete` status can ever exist.
  Disabling the *write-side* guard was **killed by exactly one test**
  (`test_a_checkpoint_is_never_written_with_any_status_but_complete`), matching the reported count.
  Decision 145 declined to count an unkillable mutation and said so; that is honest reporting, and
  the substitute is genuinely reachable.
* **M3–M7 and M1/M8/M10** are killed by tests that this review confirmed are parameterized across all
  three phases or exercise both boundaries, so the campaign cannot pass by testing one boundary.
* **M15** is corroborated by this review's own independent re-trace.

Every mutation applied by this review was restored, and restoration was proved by SHA-256 and by an
empty `git diff` **before** this record was written.

**The equivalence proof is stronger than a field list, and it was reproduced.** Rather than
hardcoding which fields may vary, the test **measures** the baseline — the fields that differ between
two *whole* runs — and requires the phased-versus-whole difference set to be **exactly** that
baseline. Reproduced independently in this review:

```text
TOTAL RESULT FIELDS        61
BASELINE (whole vs whole)  completed_at_utc, run_id, started_at_utc,
                           work_root_free_bytes_after, work_root_free_bytes_before,
                           working_catalog_sha256
OBSERVED (whole vs phased) identical to the baseline
SETS EQUAL                 True
```

Six variable fields — run identity, two timestamps, two free-space readings and the working catalog's
file digest — **exactly** the candidate set, with nothing unexpected. The remaining **55** fields are
identical, including all five accepted identities, the association totality, every count, the parser
states, the disposition, the plan and source identities and every evidence value. No normalization
removes a semantic difference: an equal-set assertion would fail in **both** directions.

**The structural basis for that result was verified too.** `_f0`, `_f1` and `_f2` are called by both
`_materialize` (the whole-run driver) and the three `_phase_*_body` functions. There is one
implementation of each phase and two drivers, not two implementations kept in step.

## 18. Findings

### MAJOR-1 — `phase_execution_identity()` binds no executable governing code

```text
ID          D146-MAJOR-1
SEVERITY    MAJOR
```

**DEFECT.** Decision 145 §12 claims that its continuity mechanism prevents, *mechanically*, "a process
continuing from a revision whose governing semantics moved", and labels `phase_execution_identity()`
"code and configuration identity". It binds ten frozen constants plus
`disclosure_drift.__version__`, which is the literal `"0.1.0"` and has not changed since the Milestone
1 foundation commit. Executable governing semantics can move arbitrarily while the admitted identity
is unchanged, and no other accepted mechanism closes the gap.

**RULE.** Decision 145 §12 ("What this prevents, mechanically: … a process continuing from a revision
whose governing semantics moved"); CLAUDE.md rule 12 (a stated invariant that does not hold is
reported, never worked around).

**EVIDENCE.**
* `src/disclosure_drift/m3/single_source_canary.py:2139-2175` — the complete input set.
* `src/disclosure_drift/m3/canary_phases.py` `execution_identity()` — a pure digest of what it is
  handed; nothing is derived from source content.
* `src/disclosure_drift/__init__.py:13` — `__version__ = "0.1.0"`; `git log --follow` shows exactly
  one commit, `fa16668`, has ever touched it.
* Empirical: with `POST_F0_MINIMUM_FREE_BYTES` relaxed `60 → 1` GiB **and** the admission-side
  predecessor-status guard deleted, the digest is bit-identical at
  `ef0b492c03ccd5b154eca8c0c3cd27463cab0686ac69b34a89b0fc66a339a69b`. Both files restored, SHA-256
  proved.
* Exhaustive search of `src/` returns no git SHA, source digest, build identity or equivalent.
* `tests/unit/test_d145_phase_restart.py:417` —
  `test_a_successor_refuses_a_changed_code_revision` establishes the property only for a version
  string that never moves.

**GENERALITY.** Every continuation admitted by `require_phase_admission`; both boundaries; every
future phase-restart consumer of this digest.

**EXPECTED.** Either the admitted identity binds a genuine semantic code identity, or Decision 145
§12 is narrowed to state what the digest actually does — that it binds the listed frozen constants
and the declared package version, and that governing-code continuity across a phase boundary rests on
operator and repository governance rather than on this mechanism.

**CONFLICTS.** With Decision 145 §12's own mechanical claim and with the `code` half of the label it
gives the digest.

**ON CONFLICT.** The implementation controls what is enforced. The record's claim is the part that is
wrong.

**CITE AS.** `D146-MAJOR-1`.

### MINOR-1 — the record says four capacity floors; three are bound

```text
ID          D146-MINOR-1
SEVERITY    MINOR
```

**DEFECT.** Decision 145 §12 states that the execution identity folds "the **four** capacity floors".
The implementation folds **three**: `LAUNCH_MINIMUM_FREE_BYTES`, `PRE_F1_MINIMUM_FREE_BYTES` and
`PRE_F2_MINIMUM_FREE_BYTES`. `POST_F0_MINIMUM_FREE_BYTES` (60 GiB) — an accepted floor enforced at
F0's own terminal — together with `F2_ALERT_FREE_BYTES` (20 GiB) and `F2_HARD_FLOOR_FREE_BYTES`
(10 GiB) are not folded.

**RULE.** Decision 145 §12; Decision 135 §11 / D138-R6, which make the phase floors accepted values.

**EVIDENCE.** `single_source_canary.py:2166-2172` folds three floors;
`external_working_root.py:202,213,223,230,242` defines five, and `single_source_canary.py:280` a
sixth. The 60 → 1 GiB `POST_F0` relaxation in `MAJOR-1` left the digest unchanged, which is this
finding made concrete on an accepted gate.

**GENERALITY.** The §12 statement and any reader who relies on it to reason about which floors a
continuation is protected against.

**EXPECTED.** Either the count is corrected to three with the unfolded floors named, or the missing
floors are folded in. Separable from `MAJOR-1`: fixing one does not necessarily fix the other.

**CONFLICTS.** Record text versus implementation.

**ON CONFLICT.** The implementation controls.

**CITE AS.** `D146-MINOR-1`.

### MINOR-2 — a source docstring restates two now-false D126 §7 rationale sentences as present fact

```text
ID          D146-MINOR-2
SEVERITY    MINOR
```

**DEFECT.** The `PRE_F2_MINIMUM_FREE_BYTES` docstring states, in the present tense, that *"F1 returns
and F2 begins in consecutive statements, so there is no window an outside process can occupy"* and
that *"nothing durable changes at the boundary, so an observer cannot tell 'F1 finished' from 'F2 is
about to open' by reading state"*. Decision 145 made both false on the phased path: there is now a
process boundary, and F1's terminal checkpoint is durable and readable. Decision 145 §24 item 5
records the staleness for the decision record but names only the second sentence, and the source copy
was not corrected.

**RULE.** CLAUDE.md's rule that a stale pointer is a bug in the pointer; Decision 126 §7.

**EVIDENCE.** `src/disclosure_drift/m3/single_source_canary.py:269-276`; Decision 145 §24 item 5;
Decision 126 §7 reasons 1 and 2.

**GENERALITY.** One docstring, on the canonical constant governing the pre-F2 admission gate — the
place a future reader is most likely to consult when reasoning about that boundary.

**EXPECTED.** The docstring marks both sentences as describing the pre-D145 whole-run shape, and
Decision 145 §24 item 5 names both rationale sentences rather than one. **No behavioural change**: the
guard is correctly placed and D126-R6 is honoured.

**CONFLICTS.** Source documentation versus the architecture the same commit introduced.

**ON CONFLICT.** The implementation controls; the prose is what is stale.

**CITE AS.** `D146-MINOR-2`.

### Observations

| ID | Observation |
|---|---|
| `D146-OBS-1` | **No digest of the working-catalog file itself is recorded or compared at attach.** A substituted copy of the same accepted-catalog lineage with the same migration chain would be admitted. Requires filesystem write access inside the world directory, which is outside the accepted threat model — an actor with it can equally rewrite the ledger and the checkpoint. Recorded, not classified as a contract gap |
| `D146-OBS-2` | **Checkpoint create-once is a lock-protected read-then-write** (`recorded_value` then an UPSERT `record_value`), not an atomic constraint like `_write_once`'s `O_EXCL`. Serialized by the host execution lock, so not exploitable; noted because it is weaker in shape than the neighbouring result-document primitive |
| `D146-OBS-3` | **`migration_head` is bound in `require_phase_admission` but has no tamper test.** The property is separately enforced by `_verify_attached`, which refuses before admission is reached, making the admission comparison defensive rather than load-bearing |
| `D146-OBS-4` | **The admission-side predecessor-status guard is unreachable defensive code**, verified by mutation in this review: deleting it survives all 68 tests. Decision 145 §19 disclosed exactly this rather than claiming a kill. Recorded as **confirmation of honest reporting**, not as a defect |
| `D146-OBS-5` | **D126 §7 rationale reason 1 also ceased to describe the phased shape**, not only reason 2. Reasons 3 and 4 — the ones that carry D126-R6 — are untouched |
| `D146-OBS-6` | **Mode selection is a governance boundary, not a mechanical one.** `--mode run` remains reachable and cannot damage an in-flight phased run. §9 of this record states the requirement the future authorization must carry |
| `D146-OBS-7` | **`process_is_live_canary` does not check `argv[0]`**, unlike `authenticate_canary_process`. A decoy shell that typed the canary command with this `--run-id` would read as *alive*, producing a spurious **refusal**. Fail-closed, and the safe direction of the asymmetry |

## 19. What holds

Recorded because a review that lists only findings misrepresents the tree.

Zero blockers. The phase inventory is exactly three phases and two qualifying boundaries, and no
fourth or fifth phase was invented. Process replacement is real, through the real operator command,
with the parent-observed pid checked against the self-reported one. The durable checkpoint is
terminal-only, create-once and written last, under `WAL` with `synchronous = FULL`. Every launch
predicate is re-established in the successor's own process, and the phase floors are the accepted
ones with none invented, moved or relaxed. The selected topology survives every restart at four
production seams, and the D144 tripwire fired and was strengthened rather than loosened. Exactly-once
phase advancement holds at all thirteen conditions tested, predecessor rerun is refuted by detonation,
and no generalized resume semantics were created. The D126-R6 ruling is honoured. The D140 acceptance
lineage is unambiguous. No authority is minted, no network gate moves, no migration appears, and
`_parse_bulk` is still unreachable from the canary. The phased and whole-run results differ in
exactly the six fields two whole runs differ in, measured rather than asserted.

## 20. Validation

Because the published CI run at exactly this SHA already succeeded, `make check-fast` was **not**
re-run for repetition. Targeted validation was used, and the documentation and governance gates
required for a review-only publication were run.

| Gate | Result |
|---|---|
| `pytest tests/unit/test_d145_phase_restart.py` | **68 passed** in `13.07` s |
| Phase-path import closure, fresh interpreter | `census_orchestrator`, `m3.e0`, `httpx` all **not loaded** |
| Equivalence reproduction | baseline `==` observed, 6 variable / 55 identical |
| Bounded falsification, 4 mutations | all restored; SHA-256 and `git diff` prove byte-identical |
| Post-restore re-run | **68 passed** in `12.05` s |
| Publication gates | recorded in the completion report |

## 21. What this record does not authorize

It does not start, authorize or enable the canary. It does not authorize `--mode run`, `phase-f0`,
`phase-f1` or `phase-f2` against the real canary. It does not authorize E0 or SEC acquisition, mint
any execution authority, enable either network gate, create migration `0016`, modify the accepted
catalog, or repair, resume or overwrite any real canary world. It accepts no predecessor record and
does not accept Decision 145.

```text
D146_FINAL_INDEPENDENT_POST_D145_PRECANARY_REVIEW_FAIL
0 BLOCKER / 1 MAJOR / 2 MINOR / 7 OBSERVATION
CANARY_AUTHORIZED = NO

M3_3_D146_FINAL_INDEPENDENT_POST_D145_PRECANARY_REVIEW_FAILED_READY_FOR_OWNER
```

**Next authorized action: STOP.** Return Decision 145 and this review to GPT-5.6 Sol for owner
adjudication of `D146-MAJOR-1`, `D146-MINOR-1` and `D146-MINOR-2`. **Do not start the canary.** **Do
not repair these findings in the session that found them.**
