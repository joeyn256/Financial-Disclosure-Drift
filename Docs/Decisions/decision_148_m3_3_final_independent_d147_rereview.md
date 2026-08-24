# Decision 148 — Final Independent D146/D147 Correction and RAM-Restart Re-Review

```text
STATUS: PUBLISHED — INDEPENDENT REVIEW RECORD
RECORD_TYPE: INDEPENDENT RE-REVIEW — NO SOURCE CHANGE, NO TEST CHANGE, NO REPAIR
DATE: 2026-08-24
OWNER: Joey authorization; independent review performed by Claude Opus 5 at maximum effort
CLASSIFICATION: ADVERSARIAL RE-REVIEW OF DECISION 147 — FINDINGS RECORDED, DELIBERATELY NOT REPAIRED
AUTHORIZATION:
  M3_3_D148_FINAL_INDEPENDENT_D147_REREVIEW_AUTHORIZED — spent by the publication of this record
ACCEPTED_CORRECTIVE_PREDECESSOR: M3_3_D147_OWNER_ACCEPTED_FOR_D148_FINAL_INDEPENDENT_REREVIEW

REVIEWED_HEAD: ad3bb14d128da5eaf6c0fed9f234fcadf2d7a4fe
REVIEWED_TREE: 2f4b98f729cd108e7c6b6777d15877ab307c29f7

VERDICT: D148_FINAL_INDEPENDENT_D147_REREVIEW_PASS_WITH_NONBLOCKING_LIMITATIONS
FINDINGS: 0 BLOCKER / 0 MAJOR / 1 MINOR / 3 LIMITATION

REPOSITORY_CODE_IDENTITY: GENUINE — measured from Git, reproduced live against this exact tree
REPOSITORY_ROOT_AUTHENTICATION: SUBSTANTIATED — tracked-membership required, enclosure refused
REAL_POSITIVE_CONTROL: VALID — real repositories, real commits, real amend, real child processes
DIRTY_TREE_CONTRACT: FAIL-CLOSED across all seven working-tree states, no override, no repair
F1_FRESH_RECOMPUTATION: SUBSTANTIATED — production-reachable, proved in a real second OS process
F2_FRESH_RECOMPUTATION: SUBSTANTIATED — same single derivation point, proved by mutation kill
EXECUTION_IDENTITY_INPUTS: 17 — independently enumerated from source, documentation agrees
CAPACITY_POLICY: 6 folded / 2 excluded with stated reasons — classification is truthful
DECISION_126_INVARIANT: PRESERVED — 50 GiB, dispositive, inside the F2 process, D126 not rewritten
MAJOR_PHASE_COUNT: 3 — F0, F1, F2 (independently reconstructed, not inherited)
QUALIFYING_BOUNDARIES: 2 of 2 — F0→F1, F1→F2; post-F2 is TERMINAL_PROCESS_EXIT_EXPECTED
PHASE_BOUNDARY_RAM_RECLAMATION: IMPLEMENTED
CHECKPOINT_EXACTLY_ONCE: PRESERVED — a repository refusal modifies no predecessor checkpoint
TOPOLOGY_NARROWING: PRESERVED — 4 of 4 production envelope seams, all three phases
PARSE_BULK_REACHABILITY: PROVABLY CANARY-UNREACHABLE — independently re-traced, unrepaired
AUTHORITY_BYPASS: NONE FOUND
NETWORK_BYPASS: NONE FOUND
FALSIFICATION: 7 load-bearing mutations, 7 KILLED, every file restored byte-identical

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

This is the independent re-review of
[Decision 147](decision_147_m3_3_d146_finding_correction.md), performed from a fresh context by a
session that wrote neither Decision 145, Decision 146, nor Decision 147, and that did **not** inherit
their conclusions. Every property below was reconstructed from the published repository.

**The verdict applies to the technical tree, not to the commit that publishes this record.**

```text
REVIEWED_HEAD  ad3bb14d128da5eaf6c0fed9f234fcadf2d7a4fe
REVIEWED_TREE  2f4b98f729cd108e7c6b6777d15877ab307c29f7
```

The later documentation-only commit that adds this file, the registry row, the index rows and the
`STATUS` block is **not** the reviewed artifact. Nothing under `src/`, `tests/`, `scripts/`,
`configs/` or `migrations/` differs between the reviewed tree and the publication commit.

**A review records; it does not repair.** Seven bounded falsification mutations were applied and
every one was restored byte-identical by SHA-256, with an empty `git diff` before publication. The
one MINOR and the three limitations below are **deliberately not fixed** in this session.

**It accepts nothing.** Not Decision 145, not Decision 147, and not Decisions 137, 138, 140, 141,
142, 143 or 144. [Decision 146](decision_146_m3_3_final_independent_post_d145_precanary_review.md)'s
`FAIL` verdict remains historically valid for the tree it reviewed, and
[Decision 143](decision_143_m3_3_final_independent_precanary_review.md)'s does for its own.

**A `PASS` here does not authorize the canary.**

## 2. Entry state

Every material entry predicate was verified live and matched. Nothing was repaired or normalized to
make it match.

| Predicate | Expected | Observed |
|---|---|---|
| Branch | `main` | `main` |
| `HEAD` | `ad3bb14d…` | `ad3bb14d128da5eaf6c0fed9f234fcadf2d7a4fe` |
| Tree | `2f4b98f7…` | `2f4b98f729cd108e7c6b6777d15877ab307c29f7` |
| `origin/main` | equal to `HEAD` | equal — 0 ahead, 0 behind |
| Worktree | clean, nothing staged, no untracked residue | clean |
| Tag at `HEAD` | none | none |
| D147 CI run `32691646553` | `SUCCESS`, both mandatory jobs | `SUCCESS`; *SEC-enabled environment* and *Core environment* both `success`, head SHA `ad3bb14d…` |
| Migration head | `0015`, `0016` absent | `0015`; `0016` absent |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` | `None` |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` | `None` |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` | `None` |
| `network.enabled` | `false` | `false` |
| `network.m3_acquire_enabled` | `false` | `false` |
| `canary_authorized` | `false` | `False`, a literal in the preflight record with no path that sets it |

## 3. `R1` — the repository code identity is a measurement

`src/disclosure_drift/m3/repository_identity.py` was reconstructed directly rather than read through
Decision 147's description of it.

**It is derived from the executing source.** `running_repository_identity()` starts from
`Path(__file__).resolve()` — this module's own location. It never reads the current working
directory, and no parameter, CLI flag or environment variable on any surface can supply a revision.

**It records both identities.** `rev-parse HEAD` and `rev-parse HEAD^{tree}`, each validated against
a Git object-name pattern before it can be folded into anything. Both are needed and the reason is
demonstrable rather than asserted: an amend moves the commit and leaves the tree, so a tree
comparison alone admits a history that moved.

**The repository is authenticated, not merely found.** Git walks upward, so an installed copy of the
package sitting inside an unrelated repository would otherwise yield a *real* identity of the *wrong*
code. `_require_tracked_governing_source` requires `canary_phases.py` and `single_source_canary.py`
to be **tracked files** of the repository Git reported, via `ls-files --error-unmatch`. This closes
the enclosure case, and it also closes the in-repository virtual-environment case as a side effect:
an installed copy under an ignored `.venv/` is not a tracked path, so it refuses.

**Every Git operation is a read.** Re-derived from the module's own AST in this review, independently
of the D147 test that makes the same claim: every `_git` call site takes a literal argument list, and
the complete set of subcommands issued is

```text
rev-parse   status   ls-files
```

No `reset`, `checkout`, `clean`, `stash`, `fetch`, `pull`, `write-tree`, `commit` or index mutation
appears, and none is required. The single string `clean` present in the module is the
`RepositoryIdentity.clean` property, not a Git verb.

**Reproduced live.** Running the production derivation against this checkout returns
`head_sha = ad3bb14d128da5eaf6c0fed9f234fcadf2d7a4fe` and
`tree_sha = 2f4b98f729cd108e7c6b6777d15877ab307c29f7` — the reviewed identity, matching `git
rev-parse` run independently. The mechanism measures; it does not declare.

## 4. `R2` — the dirty-worktree contract, and the ignored-path threat model

`require_clean_running_repository()` refuses an ambiguous working tree **before** any identity is
folded, and the phase entry point calls it **first**, before the work root, the volume, the dock, the
power state or the host execution lock.

**All seven states were verified against real repositories by this review**, including the two
Decision 147's own tests do not cover:

| Working-tree state | Result | Reported as |
|---|---|---|
| Clean | **admitted** | — |
| Modified tracked | **refused** | `dirty_tracked_paths` |
| Staged but uncommitted | **refused** | `dirty_tracked_paths` |
| Deleted tracked, worktree | **refused** | `dirty_tracked_paths` |
| Deleted tracked, staged (`git rm`) | **refused** | `dirty_tracked_paths` |
| Renamed tracked, staged (`git mv`) | **refused** | `dirty_tracked_paths`, the **new** path |
| Renamed tracked, unstaged | **refused** twice over | old path dirty **and** new path untracked |
| Untracked, non-ignored | **refused** | `untracked_paths` |
| Ignored | **admitted** | — |

A refusal is terminal. Nothing is checked out, stashed, reset, cleaned, fetched or repaired, and
there is no flag, environment variable or configuration key that makes a phase proceed anyway.

**The ignored-path question, answered from `.gitignore` rather than from Decision 147's statement.**
The tracked `.gitignore` is the only ignore file in the repository. Its entries are secrets and
environment files, virtual environments, byte-code and tool caches, coverage output, the governed
`data/` tree, database and release artifacts, logs, build output, editor directories, and the
reserved M3 private-evidence path. One class is genuinely code: `__pycache__/` and `*.py[cod]`.

This review tested it rather than reasoning about it. Against a disposable repository with the same
ignore policy:

* a **timestamp-invalidated** forged `.pyc` — the ordinary stale-cache case — is **rejected by
  CPython** and the committed source runs. The failure mode the mechanism exists to catch, a
  governing revision moving, therefore cannot be laundered through a stale cache;
* an **`UNCHECKED_HASH`** `.pyc` **is** executed without validation against its source, and the
  repository identity stays byte-identical and `clean`.

**This is recorded as a limitation, not a defect** — see `D148-L1` in §17. It requires an actor with
write access inside the checkout, which is the same threat model
[Decision 146](decision_146_m3_3_final_independent_post_d145_precanary_review.md) `OBS-1` already
excluded on the owner-adjudicated reasoning that such an actor can equally rewrite the ledger and the
checkpoint. The threat model is **not broadened here without evidence**, and the review notes for
completeness that an actor at that level can also place a `git` earlier on `PATH` and defeat the
measurement outright — which is a property of trusting the host, not a property Decision 147
introduced.

## 5. `R3` — the real positive control is real

The control Decision 146 found missing is present and is not a fake seam.

* `test_a_tracked_content_change_and_a_new_commit_move_both_identities` builds a **real** repository
  with `git init` and a real commit, reads identity A, changes a governing tracked file, commits B,
  and asserts both the commit and the tree moved;
* `test_the_commit_identity_moves_even_when_the_tree_stands` performs a real `--amend`: same tree,
  different commit, identity still moves — the case a tree-only check would admit;
* `test_the_running_identity_is_the_one_git_reports_for_this_checkout` compares the package's own
  derivation against `git` invoked independently by the test on the live checkout. A helper that
  returned a constant, a version string, or anything not read from Git fails here.

The last of these is the decisive one: it makes a passing production path and an inert one
distinguishable. This review confirmed that independently by mutation — see `M1` in §18.

## 6. `R4` — the successor recomputes in its own process

This was the highest-priority domain, and the specific defect looked for was the recurrence pattern
*helper correct, helper tested, production continuation never calls it*.

**There is exactly one derivation point, and it is unconditional.** In
`run_single_source_canary_phase`, after `validate_phase(phase)` and before anything else,
`repository = require_clean_running_repository()`. One function serves all three phases; there is no
per-phase branch that could skip it, and the value is threaded into `_run_phase_locked` from there.

**The comparison direction is correct.** `require_phase_admission` receives the **freshly measured**
identity as the *observed* value and reads the *expected* value out of the predecessor's checkpoint.
The successor cannot say *"the previous process already checked this"*; it recomputes and compares
every time.

**Both halves are compared, twice, deliberately.** The named `repository_head_sha` and
`repository_tree_sha` comparisons run **before** the aggregate `execution_identity` digest, so a
refusal names the expected and observed values instead of reporting an undiagnosable digest
mismatch — and the digest, which folds both, remains the catch-all behind them.

**F1 is proved in a real second OS process.** `test_a_governing_repository_change_between_phases_
refuses_the_successor` runs F0 through the real operator command in a child process from a real
published checkout at commit A, commits a genuine change to a governing tracked source file as
commit B, and runs F1 in its own child process. F1 refuses, names both SHAs, and the world is left
exactly as F0 left it — F0's checkpoint present, F1's absent. Nothing is pinned and nothing is faked:
the module-level identity pin used by the in-process tests cannot reach a child process.

**F2 is proved by the same production path plus mutation.** F2 shares the single derivation point,
and `test_a_successor_refuses_a_predecessor_from_another_revision` is parameterized over `f1`/`f2`
and over `head`/`tree`, driving the real production entry point. This review confirmed the coverage
is load-bearing rather than incidental: neutering the head comparison kills `[head-f1]` **and**
`[head-f2]`; neutering the tree comparison kills `[tree-f1]` **and** `[tree-f2]` (`M2`, `M3` in §18).
A production path that reused the predecessor's recorded value as the observed value would pass its
own comparison and is killed at both boundaries.

**And all three processes measure.** In the three-real-process demonstration every phase reports the
published checkout's real commit, and the three tree values are identical — a measured Git identity,
not a shared default.

## 7. `R5` — the execution identity, enumerated from source

`phase_execution_identity()` was reconstructed and its canonical key set counted independently of
Decision 147's claim. It folds **seventeen** inputs:

```text
 1 canary_contract                 10 pre_f1_minimum_free_bytes
 2 restart_contract                11 pre_f2_minimum_free_bytes
 3 evidence_contract               12 f2_alert_free_bytes
 4 resolution_scope                13 f2_hard_floor_free_bytes
 5 required_transport              14 package_version
 6 qualified_volume_uuid           15 repository_identity_contract
 7 batch_size                      16 repository_head_sha
 8 launch_minimum_free_bytes       17 repository_tree_sha
 9 post_f0_minimum_free_bytes
```

Every item the review was asked to check for is bound: the existing canary contract identity, the
restart contract identity, the evidence contract identity, the resolution scope, the required
transport, the qualified volume UUID, the batch size, the repository `HEAD` commit, the repository
tree, and the declared package version. **The count matches the documentation**, and it is pinned
against the source's own AST rather than described in prose — which is the correct closure of
`D146-MINOR-1`, since that finding was a prose count that had rotted.

**Capacity-policy classification**, cross-checked against every capacity constant the F0/F1/F2 path
actually uses:

| Constant | Value | Classification | Folded |
|---|---|---|---|
| `LAUNCH_MINIMUM_FREE_BYTES` | 185 GiB | load-bearing execution policy — F0 admission floor | **yes** |
| `POST_F0_MINIMUM_FREE_BYTES` | 60 GiB | load-bearing — post-F0 invariant at the `POST_F0` boundary | **yes** |
| `PRE_F1_MINIMUM_FREE_BYTES` | 55 GiB | load-bearing — F1 admission floor | **yes** |
| `PRE_F2_MINIMUM_FREE_BYTES` | 50 GiB | load-bearing — F2 admission floor, dispositive in the F2 process | **yes** |
| `F2_ALERT_FREE_BYTES` | 20 GiB | warning-only in effect, but decides what a capacity observation **records** | **yes** |
| `F2_HARD_FLOOR_FREE_BYTES` | 10 GiB | load-bearing — rolls F2's single transaction back | **yes** |
| `PHASE_MINIMUM_FREE_BYTES` | `{POST_F0, PRE_F1}` | **derived duplicate** — a label-to-floor mapping over values already folded | no, correctly |
| `WORKING_CATALOG_CACHE_BYTES` | 512 MiB | **evidence-neutral implementation tuning** — Decision 119's equivalence proof | no, correctly |

The exclusions carry stated reasons and are themselves tested, and a test fails if a seventh capacity
constant is ever added unclassified. **Documentation and implementation agree.**

## 8. `R6` — Decision 126 and the pre-F2 invariant

[Decision 126](decision_126_m3_3_complete_first_source_final_preflight.md) was read directly. Its §7
gives four reasons an external sampler cannot satisfy the owner predicate. Decision 147 splits them,
and this review confirms the split is faithful:

* reasons **1** and **2** — *"F1 returns and F2 begins in consecutive statements … no window"* and
  *"nothing durable changes at the boundary"* — **stopped describing this architecture** when the run
  was split into three processes. They remain true of the surviving whole-run path;
* reasons **3** and **4** — *a signal from outside is advisory where admission must be dispositive*,
  and *free space sampled at any instant before the call describes a different instant* — are
  **untouched**, and they are the reasons that carry `D126-R6`.

The `PRE_F2_MINIMUM_FREE_BYTES` docstring marks exactly those two as `HISTORICAL` and exactly those
two as `CURRENT AND BINDING`, quoting them. That is the correct separation.

**The invariant itself is intact, verified structurally from production code.** In `_phase_f2_body`,
inside F2's own `write_containment`, `_require_pre_f2_free_space(...)` is the statement **immediately
before** `_f2(...)`. The gate has not moved to an external sampler, has not become advisory, and the
value is unchanged at 50 GiB. **Decision 126 itself is byte-unchanged** since its own publication
commit `298ad7f`.

## 9. `R7` — three phases, two boundaries, and RAM reclamation

The inventory was reconstructed rather than assumed, and it is exactly:

```text
F0 ──QUALIFIED_MAJOR_RESTART_BOUNDARY──▶ F1 ──QUALIFIED_MAJOR_RESTART_BOUNDARY──▶ F2
                                                                                  │
                                                                TERMINAL_PROCESS_EXIT_EXPECTED
```

`CANARY_PHASE_SEQUENCE = ('f0', 'f1', 'f2')`; `PHASE_PREDECESSOR` and `PHASE_SUCCESSOR` agree; F2 has
no successor; the operator surface exposes one mode per phase.

**Proved through the real operator CLI path.** The three-process demonstration runs each phase as a
separate child of the test process, so the operating system's own process id is observed by the
parent and compared against the id the phase reported for itself — a self-report compared only
against itself would prove nothing. Three distinct pids; each predecessor's process proved **gone**
before its successor was admitted (`predecessor_process_gone = [None, True, True]`); all three
confirmed not live afterwards.

There is **no** same-process continuation substitution, **no** `gc.collect()` stand-in, **no**
suspended-process continuation, and **no** resident phase worker holding an old working set: the
successor refuses outright if the predecessor's process is still alive, and this review confirmed
that guard is load-bearing by deleting it (`M6`, §18).

```text
PHASE_BOUNDARY_RAM_RECLAMATION  IMPLEMENTED
GOVERNED_PAUSE_RESUME           NOT_IMPLEMENTED
SAFE_TO_EJECT                   NOT_IMPLEMENTED
```

No physical-detach right is created, and the volume must stay attached to the selected topology for
the whole sequence.

## 10. `R8` — checkpoint and exactly-once semantics survive

Decision 147's additions widened the checkpoint; they did not weaken it.

* the checkpoint is written **only** at durable terminal success, with the single status `complete`,
  **last**, after the working-catalog context has closed, through a short-lived handle of its own;
* it is **create-once**: a phase already carrying one is refused rather than overwritten;
* a phase carrying its own checkpoint is never re-entered, and an absent predecessor checkpoint is
  never read as completion — not a world directory, not a working catalog, not committed rows;
* the successor requires run identity, source identity, repository `HEAD`, repository tree, the
  accepted catalog digest, the migration head, the plan fingerprint **and** the aggregate execution
  identity to match exactly, plus the predecessor's process to be gone;
* `PHASE_RESTART_CONTRACT` moved `/1 → /2`, so a version-1 checkpoint — one describing a phase that
  ran without recording which revision it ran under — is refused rather than half-read;
* **a repository-identity refusal repairs nothing.** The real-process test confirms F0's checkpoint
  is still present and F1's still absent after the refusal.

## 11. `R9` — topology and external-root safety

All **four** production `require_external_envelope` call sites pass
`required_transport=FIRST_CANARY_REQUIRED_TRANSPORT`, whose value is `USB_VIA_THUNDERBOLT_DOCK`. The
parameter's default is `None`, so a future seam that forgot it would fall open — which is why the
every-call-site AST tripwire matters, and it is intact.

A qualified dock is admitted when all other predicates pass; a **qualified direct attachment is
refused on the phase path**, at every phase; an unqualified topology is refused. There is no
fallback, no operator override, no environment override and no configuration override. The exact
volume UUID, storage identity, ordered dock profile, AC power, lid state, D130 exclusion,
`SQLITE_TMPDIR` requirement, phase capacity floors and host execution lock are all re-established in
each successor's own process. A changing BSD disk number alone remains non-authoritative.

Removing the narrowing from the phase path is killed by eight tests across three files, covering all
three phases (`M7`, §18).

## 12. `R10` — the seven Decision 146 observations

Each disposition was re-judged independently. **None is reclassified.**

| Observation | D147 disposition | This review |
|---|---|---|
| `OBS-1` — no working-catalog **file** digest at attach | accepted, boundary now asserted by a test | **Still reasonable.** Requires write access inside the world directory, outside the accepted threat model. D147 changed no fact material to it |
| `OBS-2` — lock-serialized create-once rather than `O_EXCL` | accepted, boundary now asserted by a test | **Still reasonable.** Serialized by the host execution lock; the shape is unchanged by D147 |
| `OBS-3` — `migration_head` bound but untested | closed with a focused test, no architecture change | **Correctly closed.** The comparison is defensive because `_verify_attached` refuses first; what was missing was a test that the defensive comparison is real, and that is what was added |
| `OBS-4` — unreachable defensive predecessor-status guard | kept and pinned | **Correct.** Removing defensive redundancy because it is unreachable is the wrong direction; D146 recorded it as confirmation of honest reporting, and pinning it preserves that |
| `OBS-5` — stale Decision 126 rationale wording | closed together with MINOR-2 | **Closed.** Verified against D126 §7 sentence by sentence in §8 above |
| `OBS-6` — `--mode run` remains reachable | carried forward as a future authorization boundary | **Still correct.** See §13 |
| `OBS-7` — `process_is_live_canary` fail-closed asymmetry | correction **refused on evidence** | **Agreed, and the refusal is the right call.** An `argv[0]` condition would make *alive* harder to detect and could admit a successor while its predecessor was still writing the working catalog — the dangerous direction. A spurious refusal is the safe one |

## 13. `R11` — the `--mode run` authorization boundary

`--mode run` remains technically present. That is **not** a failure, and Decision 147 did not make it
necessary for the phase sequence: `--mode phase-f0|phase-f1|phase-f2` route to
`run_single_source_canary_phase` on their own, and `--mode run` routes elsewhere entirely.

The future real-canary authorization is therefore fully capable of restricting authority to exactly

```text
--mode phase-f0     --mode phase-f1     --mode phase-f2
```

with a clean process exit between each, and **an invocation of `--mode run` against the future
authorized real canary is OUTSIDE AUTHORITY.** The requirement Decision 146 §9 recorded is carried
forward unchanged.

For completeness, this review notes an asymmetry Decision 147 introduced and did not state: the
clean-tree contract gates the **phase** path only. It is recorded as `D148-L2` in §17 and it does not
weaken the phase path.

## 14. `R12` — authority, network, and `_parse_bulk`

`canary_authorized` remains `false` and is a literal with no path that sets it. No canary authority
bypass, no E0 authority, and no stale-writer-lease recovery authority exists — all three activation
constants are `None`. Both network gates are `false` in the tracked configuration. Migration head is
`0015` and `0016` is absent. The module Decision 147 added mints nothing and reaches nothing: it
names no activation constant, no network switch and no transport.

**`census_orchestrator.py::_parse_bulk` is `PROVABLY CANARY-UNREACHABLE`**, re-traced independently
after `repository_identity.py` was added, three ways:

1. **Call graph.** `_parse_bulk` has exactly one caller, inside `CensusOrchestrator`; the only
   construction of `CensusOrchestrator` anywhere in `src/` is a **function-local** import in the
   census CLI command, behind the network gate;
2. **Import closure, measured live in this review.** Importing the complete canary phase path in a
   fresh interpreter does **not** load `disclosure_drift.sec.census_orchestrator` at all;
3. **Source.** No phase-path module names the orchestrator, its class, or the function.

**It remains an open PRE-NETWORK blocker and was deliberately not repaired.**

## 15. Test-quality assessment

The tests were inspected, not counted. The organising question was whether any property is proved
*only* by monkeypatching an expected return value.

**It is not.** The pattern used is sound and is the one the situation calls for: the upstream
**measurement** is proved against real Git — real repositories, real commits, a real amend, real
dirty and untracked states, and the live checkout cross-checked against independently invoked `git` —
while the pinned identity is used downstream to drive **refusal** paths deterministically. A pin used
that way tests the consumer; it is legitimate precisely because the producer is separately proved.
The end-to-end refusals then run in real child processes from real published checkouts through the
real operator command, where no pin can reach.

Coverage against the properties this review was required to check:

| Property | Proved | How |
|---|---|---|
| Real Git identity | **yes** | real repositories; live checkout cross-checked against independent `git` |
| Dirty-tree refusal | **yes** | real dirty tree, in-process and in a real child process |
| Staged change refusal | **yes** | real staged change |
| Untracked refusal | **yes** | real untracked module, in a real child process |
| Ignored-file intended behaviour | **yes** | real `.gitignore`, real `__pycache__` |
| F1 fresh recomputation | **yes** | real second OS process, real commit moved between phases |
| F2 fresh recomputation | **yes** | production path, both identity halves, killed by mutation |
| Actual production admission | **yes** | driven through `run_single_source_canary_phase` |
| Real three-process sequence | **yes** | parent-observed pids, predecessors proved gone |
| Capacity identity inventory | **yes** | AST-pinned set, plus an unclassified-constant tripwire |
| Pre-F2 gate placement | **yes** | AST-pinned to the statement before `_f2` |
| Dock narrowing | **yes** | every phase, plus an every-call-site AST tripwire |
| `_parse_bulk` non-reachability | **yes** | source, live import closure, call graph |
| Deleted / renamed tracked paths | **no** | correct in implementation; verified by **this** review (`D148-L3`) |

## 16. Validation

Run against the reviewed technical tree, after every falsification mutation had been restored and the
worktree confirmed clean. Nothing was mutated to make a failure pass.

| Gate | Result | Elapsed |
|---|---|---|
| `test_d147_repository_code_identity.py` + `test_d145_phase_restart.py` | **123 passed** | 24s |
| D144 transport narrowing, D137/D138/D140/D141 envelope, D127 pre-F2 guard | **274 passed** | 8s |
| `make lint` | **All checks passed** | <1s |
| `make format-check` | **203 files already formatted** | <1s |
| `make typecheck` | **no issues in 98 source files** | 1s |
| `make secrets` | **467 files, 0 findings** | 2s |
| `make hygiene` | **469 paths, 0 findings** | <1s |
| `make links` | **223 documents, 2612 links, 0 unallowed broken** | 1s |
| `make decision-refs` | **4912 citations against 143 records** | 1s |
| `make validate` / `make cohorts` | **5 cohorts validated, frozen definitions match** | 1s |
| **`make check-fast`** | **exit 0 — 5290 passed, 1 skipped** | **250s** |

The final `make check-fast` was run once against the reviewed tree even though D147's CI was already
green, because this is the last independent pre-canary review.

## 17. Findings

**0 BLOCKER. 0 MAJOR.**

### `D148-MINOR-1` — one docstring sentence overstates a `PATH` property

```text
ID          D148-MINOR-1
SEVERITY    MINOR
LOCATION    src/disclosure_drift/m3/repository_identity.py, the _git docstring
```

The docstring states *"the executable is resolved to an absolute path, so `PATH` order decides
nothing either."* Resolution is by `shutil.which("git")`, which **selects by `PATH` order**. What
absolute resolution buys is that the subprocess performs no second, independent lookup between
resolution and exec — not that `PATH` order is irrelevant to which `git` is chosen.

**Why it is MINOR and not an observation.** The sentence concerns a security-relevant property, and
an owner reading it could infer robustness against a hostile `PATH` that the code does not provide.

**Why it is non-blocking.** The overstatement appears **only** in that internal docstring. It is not
in Decision 147's record, not in the operator runbook, and not in `STATUS`. Decision 147's own
published claim — *every Git invocation is a read, proved from the module's own AST* — is true, and
this review re-derived it independently. Host integrity is assumed throughout this subsystem and
always has been.

**Not fixed here.** A review records; it does not repair.

**CITE AS.** `D148-MINOR-1`.

### Limitations

| ID | Limitation |
|---|---|
| `D148-L1` | **An `UNCHECKED_HASH` byte-code file under an ignored `__pycache__` executes without validation and does not move the repository identity** — demonstrated empirically in §4. The ordinary stale-cache case is **provably closed**: a timestamp-invalidated forged `.pyc` is rejected and the committed source runs. Exploiting this needs write access inside the checkout, which the accepted threat model excludes on the same reasoning the owner adjudicated for `OBS-1`, and an actor at that level can equally place a `git` earlier on `PATH`. Recorded so the boundary is **stated rather than inferred**; the threat model is not broadened |
| `D148-L2` | **The clean-tree contract gates the phase path only.** `--mode run` derives no repository identity and is not refused for a dirty checkout. It cannot seed or continue a phase sequence — it writes no phase checkpoint, and `create_world` refuses a world that already exists — so the phase path is not weakened. The future authorization must forbid `--mode run` for the real canary regardless, which `OBS-6` and §13 already require |
| `D148-L3` | **Decision 147's tests do not cover deleted or renamed tracked paths.** Both were verified correct by this review against real repositories (§4), including that a staged rename reports the **new** path. This is a test-coverage observation, not a defect |

## 18. Independent falsification

A small adversarial campaign, deliberately **not** a mechanical repeat of Decision 147's. Each
mutation targets the load-bearing `D146-MAJOR-1` correction or a property it must not have weakened.
Every mutated file was restored and its SHA-256 verified against a pre-campaign baseline.

| # | Mutation | Result | Killed by |
|---|---|---|---|
| `M1` | repository identity returns a constant | **KILLED** | 6 tests, including three real-process refusals and the three-process demonstration |
| `M2` | successor compares the **predecessor's** head identity instead of its fresh measurement | **KILLED** | `[head-f1]`, `[head-f2]`, and the real-process cross-phase refusal |
| `M3` | successor compares the **predecessor's** tree identity instead of its fresh measurement | **KILLED** | `[tree-f1]`, `[tree-f2]` |
| `M4` | a dirty repository is admitted | **KILLED** | 3 tests, including both real-process refusals |
| `M5` | successor stops comparing repository identity entirely — both named comparisons **and** all three digest inputs removed | **KILLED** | 9 tests, including the end-to-end real-process refusal |
| `M6` | phase decomposition collapses to same-process continuation — the live-predecessor refusal removed | **KILLED** | `test_a_live_predecessor_process_refuses_the_successor` |
| `M7` | the first-canary transport pin removed from the phase path | **KILLED** | 8 tests across three files, all three phases |

**7 load-bearing mutations, 7 killed. No survivor.** `M3` additionally demonstrated that the
belt-and-braces is real rather than decorative: with the named tree comparison neutered the run was
still refused by the aggregate digest, only less diagnosably — which is exactly the relationship
Decision 147 describes between the named fields and the digest.

Restoration was verified byte-for-byte:

```text
repository_identity.py    85bd13c001b045cce212883bfbc3abc0e3203bd6a94e2c164fe1b6e78d952b25
canary_phases.py          53bb84523410fc4fb8c6722c332b0103a53f650e3da5657405d22fe700ac6620
single_source_canary.py   ba08079e8ff53f6a9d3bf311480d54494c4d481ca773ed9d08b59b4c33aebbef
external_working_root.py  90f96a35633438949f7293fe117ef245a294443199b1f9fbce35b17204fe9a01
```

## 19. What holds

Every condition the verdict rules require for a `PASS`:

* genuine repository identity, **independently substantiated** and reproduced live against this tree;
* repository identity **production-reachable in F1 and F2**, from one unconditional derivation point;
* a **real** commit and tree positive control, including the amend case;
* dirty execution state **fail-closed** across all seven working-tree states, with no override;
* execution-identity documentation **truthful** — seventeen inputs, six capacity values, two reasoned
  exclusions;
* `D146-MINOR-1` **closed** by inventory, `D146-MINOR-2` **closed** with `OBS-5`;
* the **three-phase inventory** preserved, with **two** qualified restart boundaries;
* **RAM reclamation** preserved, proved in three real OS processes;
* **checkpoint exactly-once** semantics preserved, and a repository refusal repairs nothing;
* **dock-only first-canary narrowing** preserved at four seams and all three phases;
* `_parse_bulk` **canary-unreachable**;
* **no authority or network bypass**;
* required validation **green**, including one full `make check-fast`.

`D148-MINOR-1` and the three limitations undermine none of these.

## 20. What this record does not authorize

**It authorizes no canary.** A `PASS` verdict on a mechanism re-review is not permission to run
anything. `CANARY_AUTHORIZED = NO`.

No canary-world construction, no execution namespace, no launch receipt, no complete-source
execution, no E0, no pre-E0 catalog transition, no stale-writer-lease recovery, no migration `0016`,
no network activity, no SEC acquisition, no D130 modification or archive opening, no physical detach,
no re-run of the D141 multi-gibibyte qualification, and no pause/resume implementation.

**It accepts no record.** Not Decision 145, not Decision 147, not Decisions 137, 138, 140, 141, 142,
143 or 144. Decision 146's `FAIL` verdict stands for the tree it reviewed, and Decision 143's for
its own. Decisions 137 and 138 remain `IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER
ACCEPTANCE`; Decisions 140 and 141 remain accepted **for continuation only**.

**It repairs nothing.** No file under `src/`, `tests/`, `scripts/`, `configs/` or `migrations/` is
changed by this record, and the runbook is not corrected by it.

`GOVERNED_PAUSE_RESUME` and `SAFE_TO_EJECT` both remain `NOT_IMPLEMENTED`, and no physical-detach
right is created.

**Next required action: return this record, with Decisions 145, 146 and 147, to the owner. Do not
start the canary. Do not repair `D148-MINOR-1` or any limitation in the session that wrote this
record.**
