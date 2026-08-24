# Decision 144 — The Decision 143 Pre-Canary Finding Correction

```text
STATUS: PUBLISHED — CORRECTION RECORD, ALL D143 FINDINGS CLOSED
RECORD_TYPE: CORRECTION OF A FAILED INDEPENDENT REVIEW — SOURCE, TEST, RUNBOOK AND GOVERNANCE
DATE: 2026-08-23
OWNER: Joey authorization; correction performed by Claude Opus 5 at maximum effort
CLASSIFICATION: TRUTH CORRECTION, NOT ARCHITECTURE EXPANSION
AUTHORIZATION:
  M3_3_D144_D143_FINDING_CORRECTION_AUTHORIZED — spent by the publication of this record
ACCEPTED_REVIEW_BASELINE: D143_FINAL_INDEPENDENT_PRECANARY_REVIEW_FAIL

D143_PUBLICATION_HEAD: 81782ca2b82510b65e01d5390dd2487054809bb2
D143_REVIEWED_HEAD:    a41468203e69c71c9741f3e4fab2d73cf2f7aef1
D143_REVIEWED_TREE:    8614cfc8421bbb93375066631e0616e72d074fd3

FINDINGS_CONSUMED: 0 BLOCKER / 2 MAJOR / 3 MINOR / 2 OBSERVATION
FINDINGS_CLOSED:   2 MAJOR / 3 MINOR / 2 OBSERVATION — none omitted, none deferred
FALSIFICATION: 5 mutations, 5 KILLED, every mutated file restored byte-identical by SHA-256
VALIDATION: PASS — make check-fast exit 0, 5167 passed / 1 skipped / 0 failed

PARSE_BULK_REACHABILITY: PROVABLY CANARY-UNREACHABLE (case B) — UNCHANGED, UNREPAIRED
CANARY_AUTHORIZED: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_HEAD: 0015 — 0016 ABSENT
ALL_THREE_ACTIVATION_CONSTANTS: None
NETWORK: enabled=false, m3_acquire_enabled=false
GOVERNED_PAUSE_RESUME: NOT_IMPLEMENTED — UNCHANGED
```

## 1. What this record is, and what it is not

It is the **correction of every finding** [Decision 143](decision_143_m3_3_final_independent_precanary_review.md)
recorded against the frozen Decision 142 tree. Decision 143 deliberately repaired nothing — Decision 142
§10 had frozen the pre-canary architecture, and a review that repairs its own findings is not an
independent review. The owner adjudicated those findings and authorized exactly this: close them.

**It is a truth correction, not an architecture expansion.** Two of the five findings say the
repository does something it does not do; one says the same of the CLI; two say a document
describes a repository that no longer exists. The corrections make the claims true — one by
changing the code to match the ruling, four by changing the words to match the code. **No new
mechanism was invented.** The `required_transport` narrowing that closes MAJOR-1 was built by
Decision 141 and has been correct and tested since; what was missing was a caller.

**What it is not.** It is not a canary authorization, a canary world, an execution namespace, a
launch receipt, an E0 authorization, a migration, a network enablement, a pause/resume
implementation, a physical-detach qualification, or a `_parse_bulk` repair. It is also **not a
rewrite of Decision 143**: that record stands byte-unchanged, including its FAIL verdict, which
remains true of the tree it was made against.

**Independence.** One active session from a fresh context, no subagents, no delegated reasoning,
no parallel sessions, no workflow delegation. Every gate below was executed in the foreground.

## 2. Entry state — verified live before any mutation

| Predicate | Required | Observed |
|---|---|---|
| branch | `main` | `main` |
| `HEAD` | `81782ca2b82510b65e01d5390dd2487054809bb2` | identical |
| `origin/main` | equal to `HEAD` | equal, 0 ahead / 0 behind |
| worktree | clean | clean |
| staged / untracked | none | none |
| tag at `HEAD` | none | none |
| D143 reviewed tree | `a414682` → `8614cfc8421bbb93375066631e0616e72d074fd3` | confirmed by `git rev-parse` |
| migration head | `0015` | `0015` |
| migration `0016` | absent | absent |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` | `None` (`m3/e0.py`) |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` | `None` (`m3/e0.py`) |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` | `None` (`m3/e0.py`) |
| `network.enabled` | `false` | `false` (`configs/project.yaml`) |
| `network.m3_acquire_enabled` | `false` | `false` (`configs/project.yaml`) |
| D143 CI run `32672962460` | success | `conclusion: success`, both mandatory jobs `success` |

No material predicate differed.

## 3. The findings consumed

Read from the published Decision 143 §18, not from a summary of it: **MAJOR-1** and **MAJOR-2**,
**MINOR-1**, **MINOR-2** and **MINOR-3**, and **OBSERVATION-1** and **OBSERVATION-2**. All seven
are closed below and every one of them appears in this record; **no observation was dropped for
being non-blocking.**

## 4. D144-R1 — MAJOR-1 closed: the selected topology is mechanically enforced

### The defect, restated exactly

Accepted [Decision 142](decision_142_m3_3_precanary_architecture_freeze.md) §4 selected
`USB_VIA_THUNDERBOLT_DOCK` as the one topology for the first complete-source canary, and §6 ruled
out **automatic and operator** fallback. [Decision 141](decision_141_m3_3_thunderbolt_dock_qualification.md)
§11 had already built the mechanism that expresses such a selection — the `required_transport`
narrowing — and it was correct, was fully unit-tested, and **narrowed nothing in production**: all
three seams into `require_external_envelope` left it at its `None` default, which
`require_qualified_transport` documents as *"omitting it admits either qualified topology"*. A
directly attached qualified SSD passed the entire envelope.

**It is the same shape as the defect Decision 141 §3 found**, one level down: there, a correct
guard that no production path called; here, a correct narrowing that no production path supplied.

### The correction

One constant, and three call sites.

```text
src/disclosure_drift/m3/single_source_canary.py

  FIRST_CANARY_REQUIRED_TRANSPORT: Final = TRANSPORT_DOCK

  run_single_source_canary        -> require_external_envelope(..., required_transport=FIRST_CANARY_REQUIRED_TRANSPORT)
  run_single_source_prefix_profile-> require_external_envelope(..., required_transport=FIRST_CANARY_REQUIRED_TRANSPORT)
  run_canary_source_command       -> require_external_envelope(..., required_transport=FIRST_CANARY_REQUIRED_TRANSPORT)
```

**All three, not one.** `--mode run` is the first complete-source canary itself. `--mode
profile-prefix` is the diagnostic *of that configuration*, and a prefix measured over an
unselected topology describes a run nobody authorized. `--mode preflight` is the operator surface,
and it is the one that matters most for D142 §6: the failure mode that ruling names is *a dock
preflight refusal answered by re-plugging the SSD directly*, and a preflight that then went green
would be that fallback with a receipt.

**It is a module constant and deliberately not an operator input.** There is no CLI flag, no
configuration key, and no environment variable that supplies, widens, or disables it, and none may
be added — a selection an operator can retype under a refusal *is* the operator fallback. Changing
it is a reviewed source change against a later owner decision.

### What was deliberately not done

* **No fallback of any kind** — not automatic, not operator-driven, not a "try dock then direct"
  path, and no switch that disables transport enforcement. A dock refusal is a **stop**.
* **`USB_DIRECT` is not revoked.** See §5.
* **No new guard, no new state, no new flag, and no reordering** of the composed preflight.

## 5. D144-R2 — MAJOR-2 closed: the runbook now distinguishes machine from operator

Runbook §28f.C presented **eight** rows under one categorical header — *"each is checked by the
application rather than by reading this page"* — and two of them were not.

The section is now split, and nothing is claimed for one category that belongs to the other:

* **§28f.C.1 — mechanically enforced launch predicates.** Transport, identity, power and lid,
  isolation, archive precheck, capacity, temporary root, and the one-canary host lock, each with
  the ruling that enforces it. **Transport appears here only because §4 made it true**, and the
  section says so in terms rather than quietly promoting the row.
* **§28f.C.2 — operator rules the application checks none of.** Co-tenancy leads it, stated as
  what it is: nothing in the application inspects other processes, and nothing there kills a user
  application. §28f.E already said this, and the table now agrees with it.

**No new co-tenancy enforcement mechanism was invented.** D143 recorded that §28f.E does not
overstate its coverage, and it does not; the defect was the *table*, and the table is what changed.

## 6. D144-R3 — MINOR-2 closed: runbook §28d is brought current

§28d's Decision 137-era table recorded external power as verified by the **operator**, carried no
lid row and no transport row, and counted *"five of the twelve"* as mechanical. After D141-R9 that
understated enforcement, and after §4 it understated it further.

It is **corrected rather than deleted**, and **conditions 1–12 keep their original numbers** so
that citations of them do not silently repoint. Condition 1 is now automatic at launch; conditions
13 (lid) and 14 (transport) are added; the count reads eight mechanical, four operator, two held
by the launch command. A currency banner now names **§28f.C as the table that governs today** and
states that §28f.C controls where the two could be read as disagreeing.

**"At launch" is stated as the whole of the guarantee** for power, lid and transport: they are read
once, immediately before admission, and nothing re-reads them for the following thirty hours.

## 7. D144-R4 — MINOR-3 closed: the registry records D141's acceptance

`Docs/Decisions/decision_registry.md` recorded Decision 141 as `IMPLEMENTED — PENDING INDEPENDENT
REVIEW AND OWNER ACCEPTANCE` with **no acceptance token**, for the whole life of Decisions 142 and
143, while Decision 142 §3, the decision index and the status ledger all recorded it as accepted
for continuation. `CLAUDE.md` names the registry as the source of truth for current status, so a
reader who consulted it alone reached the wrong conclusion about whether D141's rulings bind.

The row now reads `ACCEPTED — OWNER ACCEPTED FOR CONTINUATION 2026-08-23`, cites Decision 142 §3
(D142-R1) as the accepting record, and carries `M3_3_D141_OWNER_ACCEPTED_FOR_CONTINUATION` in the
repository's own `acceptance token` convention. Its `Binding, once accepted, for …` clause becomes
`Binding for …`, and its statement that D141 claimed no acceptance is kept as **history** — it did
not, and its acceptance came later from Decision 142.

**Decisions 137, 138 and 140 are untouched.** They remain `IMPLEMENTED — PENDING INDEPENDENT
REVIEW AND OWNER ACCEPTANCE`, and the row says explicitly that **their safety predicates are
enforced in the tree and are not weakened by any later record**. Nothing here implies a superseded
record's guards disappeared.

## 8. OBSERVATION-1 — disposition: DOCUMENTATION PRECISION, NO CODE CHANGE

**The concern, as D143 stated it.** The host execution lock covers `--mode run` only. A concurrent
`--mode profile-prefix` run is not mechanically excluded while a complete-source canary holds the
lock, and it would consume volume space the running canary's capacity model assumes it alone
consumes. D143 recorded it as an observation because D140-R16 speaks only of complete-source
canaries and the runbook does not overstate the coverage.

**Verified independently rather than accepted.** `acquire_canary_execution_lock` has exactly one
call site in `src/` — `single_source_canary.py`, inside `run_single_source_canary` — so the scope
is exactly as described.

**Disposition: NO CODE CORRECTION. DOCUMENTATION PRECISION, absorbed into §5.** Splitting the
§28f.C table required stating what the "one canary" row does and does not cover, so the lock's
exact scope is now written where an operator reads it, and the prohibition on a concurrent
diagnostic prefix is listed in §28f.C.2 as the operator rule it is.

**No new lock, no widened lock, and no new state machine was built.** Extending the lock to
diagnostic modes would change canary execution semantics, which this authorization excludes; it
is recorded here as available future owner work, not taken.

## 9. OBSERVATION-2 — disposition: NO MUTATION REQUIRED, CLOSED BY PROOF

**The concern, as D143 stated it.** Transport, power and lid are read only where an external
requirement exists. That is deliberate — D141-R10 keeps the accepted Decision 116 internal path
free of `ioreg` and `pmset` — and the selected first canary is external, so every guard applies to
it. It was recorded so that a future internal-root canary is not assumed to inherit them.

**Why it needs no correction.** The behaviour is correct, is intended by an accepted ruling, and
is already stated. Manufacturing a code change here would be inventing a defect.

**Why it nonetheless earned a test.** §4 added an argument to all three production callers, which
raises a fair question the old proof did not answer: does the internal path now pay for the
narrowing? It does not —`require_external_envelope` returns `None` for a root with no external
requirement **before** the transport is consulted, and the narrowing is a module constant rather
than a reading. That is now proved **through the production operator command** rather than against
the envelope helper, by making `transport_of` and `host_power_state` fatal and running
`--mode preflight` on an internal root to completion.

**Disposition: NO MUTATION — VERIFIED INFORMATIONAL ONLY, with one added test proving the D144
change did not disturb it.**

## 10. MINOR-1 closed: the CLI help states the mandatory rule

`cli.py` described `--require-volume-uuid` as protection that applies *"whether or not this is
supplied"*, and said *"omitting it cannot disable a single guard"* — true, and beside the point,
because since D140-R2 **omitting it on an external route is itself the refusal**. Decision 142 §9
corrected exactly this meaning in two runbook places and could not reach this one, because the text
lives in `src/`.

The help now states that the assertion is **mandatory on any external route** — by `/Volumes`
intent, by residence, or by assertion — that **omitting it is itself a refusal** raised before the
volume is consulted, and that it cites `D140-R2`. It keeps the true half (protection is owed by the
path, not switched on by the flag) and reframes it as *what omitting it does is refuse the run,
rather than disable a guard*.

**The internal path was not weakened by accident.** The flag stays optional at the parser, because
the accepted Decision 116 internal path needs no assertion and never did; the refusal belongs where
externality is known, which is the envelope. The help says so, and a test asserts both — that the
mandatory language is present, and that `parse_args` without the flag still yields `None`.

## 11. Production reachability — proved, not assumed

This is the property whose absence *was* MAJOR-1, so it is proved the way MAJOR-1 would have been
caught: **through production entry points**, never against `require_external_envelope` with the
argument supplied by the test.

| Proof | Through | Result |
|---|---|---|
| the narrowing arrives at the composed envelope | `run_canary_source_command` | `require_qualified_transport` receives `required=USB_VIA_THUNDERBOLT_DOCK`, exactly once |
| a qualified **dock** attachment passes | `run_canary_source_command` | exit `0`; record carries `"transport_class": "USB_VIA_THUNDERBOLT_DOCK"` and `"canary_authorized": false` |
| a qualified **direct** attachment refuses | `run_canary_source_command` | `DockTransportError`, no world created |
| a qualified **direct** attachment refuses | `run_single_source_canary` | `DockTransportError`, no world created |
| a qualified **direct** attachment refuses | `run_single_source_prefix_profile` | `DockTransportError`, no world created |
| an **unqualified** topology refuses | `run_canary_source_command` | `DockTransportError`, *"did not qualify"* |
| **no fallback** occurs after a refusal | `run_canary_source_command` | exactly one attempt, demanding exactly the dock; work root empty |
| a **changed BSD identifier** still admits | `run_canary_source_command` | exit `0` for `disk4s2`, `disk31s7`, `disk99s1` |
| **no seam omits the narrowing** | AST of `single_source_canary.py` | exactly 3 envelope calls, each pinned to the constant |

The last row is the recurrence killer that behaviour alone cannot supply: MAJOR-1 was an **absent**
argument at every call site at once, and a fourth seam added later without it would reintroduce the
defect where the behavioural tests cannot see it.

## 12. The direct path remains qualified — D141-R8 and D142 §5 preserved

**Nothing was globally revoked.** Proved separately from the narrowing:

* `QUALIFIED_TRANSPORT_CLASSES` still holds **both** classes, and an unqualified third still
  refuses;
* `classify_transport` still returns `USB_DIRECT` for a direct attachment and never reclassifies it;
* `require_qualified_transport(..., required=None)` still admits a direct attachment;
* `require_external_envelope` **still admits a direct attachment** when nothing narrows it — the
  library property D141 §16 established and D142 §5 preserved;
* the mechanism is **symmetric**: demanding `USB_DIRECT` refuses a dock attachment in the same
  shape, so neither class is privileged by the code and only the caller chose one.

What D144 narrows is **this repository's first-canary production envelope**. A later owner decision
selecting the direct topology needs a one-constant source change and nothing else.

## 13. Falsification — 5 mutations, 5 killed

Reversible, source-isolated, and byte-verified: every mutated file was restored from its exact
original bytes and re-hashed against its SHA-256 baseline after **every** mutation. No mutation
survived, and **no mutation survived into the published tree** — the final check confirmed all three
candidate files byte-identical to baseline.

| # | Mutation | Result | Killed by |
|---|---|---|---|
| M1 | the first-canary caller stops passing the dock requirement (the `--mode run` seam) | **KILLED** | `test_no_production_envelope_call_omits_the_transport_narrowing`; `test_the_direct_topology_refuses_through_the_complete_source_run` |
| M2 | the dock requirement is replaced with `None` at every production seam | **KILLED** | 8 tests, including all three per-seam refusals and the argument-arrival proof |
| M3 | the selected first-canary path accepts the direct topology instead | **KILLED** | 14 tests, including the positive dock admission and all three BSD-identifier cases |
| M4 | `required_transport` is ignored **inside** the composed envelope | **KILLED** | 7 tests, including the argument-arrival proof and all three per-seam refusals |
| M5 | the CLI help regresses to pre-D140 external-UUID optionality | **KILLED** | `test_the_cli_help_states_the_uuid_assertion_is_mandatory`; `test_the_cli_help_no_longer_frames_omission_as_harmless` |

M3 is worth reading twice: setting the constant to `USB_DIRECT` kills **the positive dock test and
the changed-BSD-identifier tests as well as the refusals**, which is what proves the suite pins the
*selected* class rather than merely pinning that *some* class is demanded.

**No broad mutation framework was run**, and no source-mutating framework was installed.

## 14. `_parse_bulk` — classification unchanged

`CensusOrchestrator._parse_bulk` remains **PROVABLY CANARY-UNREACHABLE (case B)** and an **open
pre-network blocker, deliberately unrepaired**. Nothing in this correction touches the census
orchestrator, its call graph, `network.enabled`, or the canary module's import graph: the change is
one constant and three keyword arguments inside `single_source_canary.py`, plus documentation. The
standing gate test `test_the_orchestrator_bulk_parse_stays_unreachable_without_network` passes
unchanged.

**The corrections did not make it reachable**, so no new blocker arises and none was repaired here.

## 15. Files changed

| Path | Purpose |
|---|---|
| `src/disclosure_drift/m3/single_source_canary.py` | MAJOR-1 — `FIRST_CANARY_REQUIRED_TRANSPORT`, and the narrowing at all three production seams |
| `src/disclosure_drift/cli.py` | MINOR-1 — the `--require-volume-uuid` help states the mandatory rule |
| `tests/unit/test_d144_first_canary_transport_narrowing.py` | new — 27 tests covering narrowing, direct compatibility, UUID, CLI help, and the internal path |
| `tests/unit/test_d141_dock_transport_qualification.py` | comment only — the direct-admission assertion is no longer the production argument set |
| `Docs/m3/operator_runbook.md` | MAJOR-2 (§28f.C) and MINOR-2 (§28d) |
| `Docs/Decisions/decision_registry.md` | MINOR-3 (the D141 row) and this record's own row |
| `Docs/decision_index.md` | the navigation answers this correction changes |
| `Milestones/STATUS.md` | the controlling current position |
| `Docs/Decisions/decision_144_m3_3_d143_finding_correction.md` | this record |

**`src/disclosure_drift/m3/external_working_root.py` and `m3/dock_transport.py` are unchanged.**
The mechanism they hold needed a caller, not a repair.

## 16. Validation

Every command was run in the foreground by this session.

| Gate | Result | Elapsed |
|---|---|---|
| focused D116/D119/D127/D131/D137/D138/D140/D141/D144 tests | **409 passed** | 19 s |
| new D144 suite alone | **27 passed** | 2 s |
| falsification campaign (5 mutations, restore + rehash each) | **5 KILLED**, all files byte-identical | 15 s |
| `ruff check .` | clean | < 1 s |
| `ruff format --check .` | all files formatted | < 1 s |
| `mypy src` | no issues, 96 source files | 1 s |
| decision section references | 0 unallowed | 1 s |
| Markdown links | 0 unallowed broken | 1 s |
| secret scan | 0 findings | 2 s |
| repository hygiene | 0 findings | < 1 s |
| `validate-config` / `show-cohorts` | frozen definitions match, 5 cohorts | < 1 s |
| **`make check-fast`** | **exit 0 — 5167 passed / 1 skipped / 0 failed** | 250 s wall, 243.94 s suite |

`make check-fast` was run **once**. **Not run, deliberately:** no canary, no canary world, no E0,
no network, no migration `0016`, no D130 open, no physical detach, and no storage requalification.

## 17. What did not change

`CANARY_AUTHORIZED = NO`. All three activation constants remain `None`. Both tracked network
switches remain `false`. Migration head remains `0015` with `0016` absent. `GOVERNED_PAUSE_RESUME`
remains `NOT_IMPLEMENTED`, with no `SAFE_TO_EJECT` token anywhere in `src/` or `tests/`. Every
D137, D138, D140 and D141 safety predicate is enforced exactly as before — **this record weakened
none of them and revoked none of them.** Decision 143 is not rewritten. No predecessor record is
accepted by this one.

## 18. Limitations carried forward

Every limitation in Decision 143 §19 stands, unchanged and unupgraded: `F_FULLFSYNC` visibility,
no physical-disconnect qualification, no power-loss qualification, non-journaled ExFAT, the
port- and profile-specific dock qualification, macOS-specific mechanisms, unmeasured complete-source
runtime, unimplemented pause/resume, unmeasured full-scale peak RSS and `SQLITE_TMPDIR` spill, the
lid requirement, degraded host battery health, and `_parse_bulk` as a pre-network blocker.

Two are added by this record, and both are stated rather than smoothed:

1. **The dock requirement is enforced at launch and is not re-checked.** A transport that changes
   mid-run is an interruption, not a refusal, exactly as power and lid already were.
2. **A concurrent `--mode profile-prefix` run remains mechanically unexcluded** (§8). It is now an
   explicit operator rule; making it a mechanical one is available future owner work.

## 19. The next owner boundary

**STOP.** Return this correction to the owner.

This record authorizes nothing operational. It does not authorize the canary, canary-world
construction, an execution namespace, a launch receipt, complete-source execution, E0, migration
`0016`, network acquisition, SEC traffic, pause/resume implementation, physical disconnect testing,
or any modification of the D130 archive. **Correcting the findings of a failed review is not
passing it**, and the independent rereview those corrections now invite is a separate act that must
be performed from a genuinely fresh session context — **not by the session that made them.**

## 20. Result

```text
M3_3_D144_D143_FINDING_CORRECTION_COMPLETE_READY_FOR_OWNER
```
