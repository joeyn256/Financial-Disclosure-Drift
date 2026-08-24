# Decision 149 — Final Pre-Canary Limitation Cleanup

```text
STATUS: PUBLISHED — CORRECTION RECORD
RECORD_TYPE: BOUNDED CLEANUP — TWO PROSE/BEHAVIOUR CORRECTIONS, ONE TEST CLOSURE
DATE: 2026-08-24
OWNER: Joey adjudication; implementation by Claude Opus 5 at maximum effort
CLASSIFICATION: FINAL PRE-CANARY CLEANUP — NO ARCHITECTURE REDESIGN, NO NEW AUTHORITY
AUTHORIZATION:
  M3_3_D149_FINAL_PRE_CANARY_LIMITATION_CLEANUP_AUTHORIZED — spent by this publication
ACCEPTED_PREDECESSOR: M3_3_D148_FINAL_INDEPENDENT_REREVIEW_OWNER_ACCEPTED

ENTRY_HEAD: 1e03b44a2d97da0e428afcd179c13bd9aacf58e7
ENTRY_TREE: 153e4ef1eedac2bbb7a0b9f87d5e5111777f7b2d
ENTRY_CI:   32726543966 — SUCCESS, both mandatory jobs

D148-MINOR-1: CLOSED — D149-R1
D148-L3:      CLOSED — D149-R2
D148-L2:      CLOSED — D149-R3
D148-L1:      ACCEPTED_THREAT_MODEL_LIMITATION — D149-R4, not actionable for canary acceptance
_parse_bulk:  DEFERRED_PRE_NETWORK_BLOCKER_NONBLOCKING_FOR_OFFLINE_CANARY — D149-R5

FALSIFICATION: 7 mutations, 7 KILLED, every file restored byte-identical by SHA-256
ACCEPTED_TESTS_CHANGED: NONE — measured, not assumed
MAJOR_PHASE_COUNT: 3 — F0, F1, F2, unchanged
PHASE_BOUNDARY_RAM_RECLAMATION: IMPLEMENTED
GOVERNED_PAUSE_RESUME: NOT_IMPLEMENTED
SAFE_TO_EJECT: NOT_IMPLEMENTED
MIGRATION_HEAD: 0015 — 0016 ABSENT
ALL_THREE_ACTIVATION_CONSTANTS: None
NETWORK: enabled=false, m3_acquire_enabled=false
CANARY_AUTHORIZED: NO
```

## 1. What this record is, and what it is not

The owner accepted
[Decision 148](decision_148_m3_3_final_independent_d147_rereview.md) as a
`PASS WITH NON-BLOCKING LIMITATIONS` and authorized a deliberately **small** cleanup of its
actionable residue before the final independent pre-canary review.

**It is three narrow corrections and nothing else.** Two production files are touched — one
docstring, and one refusal at the operator surface — plus one new test module, plus the runbook
section the refusal makes untrue. **No accepted test was changed, deleted, or skipped**, and that
is a measured fact rather than an intention: the blast radius of the only behavioural change was
measured before it was designed.

**It is not a redesign.** The phase architecture, the checkpoint contract, the repository-identity
mechanism, the topology envelope and the parser are untouched. **It creates no authority**, enables
no switch, and writes no migration. `CANARY_AUTHORIZED = NO`.

## 2. Entry state

Every predicate required by the authorization was verified live and matched. Nothing was repaired
to make it match.

| Predicate | Observed |
|---|---|
| Branch / `HEAD` / tree | `main` / `1e03b44a…` / `153e4ef1…` |
| `origin/main` | equal — 0 ahead, 0 behind; clean; nothing staged; no untracked residue; no tag |
| Latest governance | Decision 148 |
| Reviewed implementation beneath it | `ad3bb14d…`, tree `2f4b98f7…`; D148's publication changed no `src`, `tests`, `scripts` or `configs` |
| CI `32726543966` | `SUCCESS`, both mandatory jobs |
| Migration head | `0015`; `0016` absent |
| Three activation constants | all `None` |
| Network | `enabled=false`, `m3_acquire_enabled=false` |

## 3. `D149-R1` — the `PATH` claim, corrected to what is true

**The defect, accepted.** The `_git` docstring in
`src/disclosure_drift/m3/repository_identity.py` said:

> *"the executable is resolved to an absolute path, so ``PATH`` order decides nothing either."*

That is false. `shutil.which("git")` **searches `PATH` in order** and returns the first match, so
`PATH` decides *which* `git` is resolved. What absolute resolution actually buys is narrower and
worth stating: the resolved executable is the one that runs, because `subprocess` performs no
second, exec-time lookup that could resolve a different `git` between this call and the next.

**The correction states the real property, and it states the boundary too.** Which `git` exists on
the host is **host trust** — not something this module establishes, and not something it ever did.
An actor who can order `PATH` can equally write inside the checkout, which the accepted threat
model excludes (`D149-R4`). Saying so is the honest form of the claim.

**No production behaviour changed**, and that is asserted rather than promised: a test re-derives
from the module's own AST that the resolution is still exactly one `shutil.which("git")` and that
the complete set of Git subcommands is still `rev-parse`, `status`, `ls-files`.

**The false claim cannot come back.** A machine-checkable test scans every file under `src/` and
the operator runbook for the assertion in any wording and fails if it reappears. The decision
records are deliberately out of that scan: Decision 148 **recorded** the false claim as a finding
and this record quotes it while correcting it, and a record of a defect is not a repetition of it.

**Decision 147's true claim is unaffected and was re-verified**: every Git invocation is a read,
enumerated mechanically from the module's own AST.

**`D148-MINOR-1` is CLOSED.**

## 4. `D149-R2` — deleted and renamed tracked paths, now covered directly

Decision 148 verified by hand that a deleted or renamed tracked path is refused, and recorded that
Decision 147 had no test saying so. This is that coverage, on the same **real Git** fixtures the
Decision 147 suite uses — real repositories, real commits, real index operations.

| State | Behaviour | Reported as |
|---|---|---|
| Tracked file deleted in the worktree | **refused** | `dirty_tracked_paths` |
| Tracked file staged for deletion (`git rm`) | **refused**, and `HEAD^{tree}` is asserted **not** to have moved | `dirty_tracked_paths` |
| Tracked file renamed (`git mv`) | **refused** | `dirty_tracked_paths`, the **new** path |
| Tracked file renamed unstaged in the worktree | **refused twice over** | old path dirty **and** new path untracked |
| Clean | **admitted** | — |

**Non-vacuous, and fail-closed rather than merely reported.** Each state asserts the exact path
reported, and every one of the four is then driven through
`require_clean_running_repository()` — the production contract — to prove it **refuses**, that the
refusal says it is not a resumable pause, and that the repository is left exactly as it was found.
A positive control admits a clean repository, because four refusals prove nothing without it.

The rename case documents the reason the **new** path is the one recorded: it is the file now on
disk, and therefore the one that could execute.

**No redesign of repository identity.** Behaviour was already correct; only the evidence was
missing.

**`D148-L3` is CLOSED.**

## 5. `D149-R3` — `--mode run` is refused where the external envelope governs

**What was ambiguous.** Accepted [Decision 145](decision_145_m3_3_governed_major_phase_restart.md)
split the governed canary into three processes so that a finished phase's memory is reclaimed by
the only mechanism that reclaims it, and
[Decision 147](decision_147_m3_3_d146_finding_correction.md) then bound each phase to the
repository revision it executed under. `--mode run` provides **neither** property: it is one
process for the whole run, and it derives no repository identity. Decision 148 proved it could not
seed or continue a phase sequence — so it was not a correctness vulnerability — and recorded the
ambiguity as `D148-L2`.

**The smallest mechanically sound hardening.** One refusal, at the operator surface, taken
immediately after the external envelope is established and **before** the run is entered:

```text
if mode == "run" and external is not None:  ->  refuse
```

**Why it is keyed on the envelope.** Accepted [Decision 138](decision_138_m3_3_d137_safety_envelope_correction.md)
(D138-R1) already makes **the resolved root** the single thing that decides whether a run is
governed and external. A second externality rule here would be a second source of truth for one
question — the exact shape this repository has repeatedly refused.

**What is preserved, deliberately.** On an **internal** root `--mode run` is untouched and remains
exactly the accepted [Decision 116](decision_116_m3_3_disposable_single_source_canary_path.md)
path. That is the bounded library and development exercise the authorization explicitly permits
keeping, and it **cannot be mistaken for the governed real-canary route**, because the governed
route is external by construction. Ten accepted tests exercise capacity-boundary sequencing on the
whole-run path over a *synthetic* external volume; those drive the library entry point directly,
not the operator surface, and none of them changed.

**Six proofs, each direct:**

1. a fully qualified external launch — the exact configuration the real canary runs in — is
   **refused** for `--mode run`, and no world is created;
2. – 4. `phase-f0`, `phase-f1` and `phase-f2` are each driven to **admission** through the same
   operator surface, in sequence, on that same qualified external configuration;
5. **no alternate route.** `cli.py` reaches the canary through exactly one function, and inside the
   module the whole-run entry point has exactly one caller — the guarded operator surface. Both are
   asserted, so a future refactor that added a second route fails rather than quietly reopening the
   legacy path. A further AST assertion pins the guard **above** the whole-run call, so a
   correctly-behaving but wrongly-ordered future edit fails too;
6. **no new authority.** All three activation constants are `None`, and neither touched module
   names an authority constant, a network switch or a transport.

**Not a runbook-only prohibition.** Production enforces it; the runbook was corrected because
production made its command untrue, which is the correct order of those two things.

**`D148-L2` is CLOSED.** The `D149-R3` stop condition was **not** reached: no material architecture
redesign was required.

## 6. `D149-R4` — `D148-L1` remains an accepted limitation

An `UNCHECKED_HASH` byte-code file beneath an ignored `__pycache__` can execute without moving the
repository identity. **No attempt is made to solve it here**, on the owner's adjudication:

* it requires write capability inside the checkout;
* the accepted canary threat model excludes such an actor;
* an actor with that capability can attack equivalent execution surfaces — `PATH` and tool
  selection among them, as `D149-R1` now says plainly;
* solving arbitrary hostile-local-checkout execution is outside the canary integrity model;
* broad Python import or runtime changes immediately before the canary would add more risk than
  they remove.

**Verified only that this record does not broaden the threat model or make the condition easier to
reach.** It does neither: `D149-R1` is prose, and `D149-R3` only *removes* a route.

**Cite as `D149-R4_ACCEPTED_LOCAL_CHECKOUT_WRITE_THREAT_MODEL_LIMITATION`. Non-actionable for
canary acceptance.**

## 7. `D149-R5` — `_parse_bulk` remains deferred and unreachable

`census_orchestrator.py::_parse_bulk` remains an open **pre-network** blocker and was **not**
repaired. Re-confirmed statically across the surfaces this record touched:

* no phase-path module names `census_orchestrator`, `CensusOrchestrator` or `_parse_bulk`;
* a fresh interpreter that imports the whole canary phase path never loads the orchestrator;
* the only construction of `CensusOrchestrator` in `src/` is a function-local import in the census
  CLI command, behind the network gate;
* both network switches remain `false`.

**Classified `DEFERRED_PRE_NETWORK_BLOCKER` / `NONBLOCKING_FOR_OFFLINE_CANARY`.** No newly
reachable route exists.

## 8. `D149-R6`, `R7` and topology — what did not change

**The phase architecture is preserved exactly**: `F0 → F1 → F2`, two qualified major process
restarts, terminal process exit after F2, one operating-system process per phase.
`PHASE_BOUNDARY_RAM_RECLAMATION` remains `IMPLEMENTED`; no same-process continuation, `gc.collect()`
substitute, `SIGSTOP`, sleeping worker or retained resident worker is introduced.
`GOVERNED_PAUSE_RESUME` and `SAFE_TO_EJECT` remain `NOT_IMPLEMENTED` and nothing here implies
otherwise.

**No accepted physical truth was "fixed"** — ExFAT's absent journal, surprise-removal risk, the lid
that must stay open, corrected-scale RSS being measurable only during the real run, bounded rather
than instantaneous capacity observation, and the physical possibility of hardware or dock failure
all stand, with the Decision 140 and Decision 141 controls preserved.

**The selected topology is preserved.** All four production envelope seams still pin
`USB_VIA_THUNDERBOLT_DOCK`, asserted by an AST tripwire re-run against the module this record
edited; qualified direct attachment remains refused on the phase path; Decision 141 is not relaxed.

**The repository identity contract is preserved**: derived from the module's own location and never
the working directory, tracked-file authentication, `HEAD` and tree both captured, dirty-tree
refusal, successor fresh re-measurement, the exact seventeen-input execution-identity fold, no
override on any surface, and no Git mutation added.

## 9. Falsification

Seven mutations, each aimed at a property this record either created or must not have weakened.

| # | Mutation | Result | Killed by |
|---|---|---|---|
| `M1` | revive the false `PATH`-order assertion | **KILLED** | the documentation scan and the docstring assertion |
| `M2` | admit a deleted tracked path | **KILLED** | 5 tests, including both fail-closed drives |
| `M3` | admit a renamed tracked path | **KILLED** | 2 tests |
| `M4` | admit governed `--mode run` | **KILLED** | the `D149-R3` refusal proof |
| `M5` | over-refuse — drop the `mode == "run"` condition so the guard catches every mode | **KILLED** | 9 tests, including all three phase-mode positive controls and D144's admissions |
| `M6` | remove the phase transport pin | **KILLED** | 9 tests across three files |
| `M7` | reuse the predecessor's repository identity at the successor | **KILLED** | 4 tests, including D147's real-process refusal |

**7 killed, no survivor.** `M5` matters as much as `M4`: it proves the refusal is *narrow*, not
merely present. Every mutated file was restored byte-identical by SHA-256:

```text
repository_identity.py    9fd79607f65eceb3f7529fe4ac3b2b70ab4728b3f717e677942f2ce07e6f1ef3
canary_phases.py          53bb84523410fc4fb8c6722c332b0103a53f650e3da5657405d22fe700ac6620
single_source_canary.py   8d6b3b964fd1d38cbe981b812518d73d5fa6a58b4042a7560b01925d457666df
```

## 10. Validation

| Gate | Result |
|---|---|
| `test_d149_precanary_limitation_cleanup.py` | **25 passed** |
| D116, D119, D127, D137, D138, D140, D141, D144, D145, D147 + D149 | **511 passed** — **no accepted test changed** |
| `ruff` / `ruff format` / `mypy src` | clean; 98 source files, no issues |
| Governance gates | secrets, hygiene, Markdown links, decision references, config validation, cohorts — all pass |
| **`make check-fast`** | **exit 0** |

## 11. What this record does not authorize

**It authorizes no canary.** No canary-world construction, no execution namespace, no launch
receipt, no complete-source execution, no E0, no pre-E0 catalog transition, no stale-writer-lease
recovery, no migration `0016`, no network activity, no SEC acquisition, no D130 modification, no
physical detach, no re-run of the D141 qualification, and no pause/resume implementation.

**It accepts no record.** Decisions 145, 146, 147 and 148 stand exactly as written, including
Decision 146's `FAIL` verdict for the tree it reviewed and Decision 143's for its own. Decisions
137 and 138 remain `IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER ACCEPTANCE`; Decisions 140
and 141 remain accepted **for continuation only**.

**It creates no authority.** All three activation constants remain `None`, both network switches
remain `false`, migration head remains `0015` with `0016` absent, and a passing preflight still
prints `canary_authorized: false`.

**Next required action: return this record to the owner.** The next intended step is one fresh
independent pre-canary review of this implementation tree, by a session that did not write it.
**Do not start the canary.**
