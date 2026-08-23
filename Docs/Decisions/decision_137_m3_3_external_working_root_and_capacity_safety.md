# Decision 137 — The External Working-Root Guards and the Capacity-Safety Implementation

```text
STATUS: IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER ACCEPTANCE
RECORD_TYPE: IMPLEMENTATION RECORD OF THE NINE D136-R11 ITEMS — THE FAIL-CLOSED EXTERNAL
  WORKING-ROOT, VOLUME-IDENTITY, ARCHIVE-ISOLATION, CAPACITY, AND MONITORING MACHINERY REQUIRED
  BEFORE A CORRECTED COMPLETE-SOURCE CANARY MAY BE AUTHORIZED
DATE: 2026-08-23
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings D137-R1 – D137-R12
CLASSIFICATION: BOUNDED_SAFETY_IMPLEMENTATION_ONLY
IMPLEMENTATION_AUTHORIZATION:
  M3_3_D137_EXTERNAL_WORKING_ROOT_AND_CAPACITY_SAFETY_IMPLEMENTATION_AUTHORIZED — issued outside
  this repository and now spent
ACCEPTANCE_TOKEN: NONE — THIS RECORD CLAIMS NO OWNER ACCEPTANCE
COMPLETION_TOKEN: M3_3_D137_IMPLEMENTATION_COMPLETE_READY_FOR_OWNER_REVIEW
QUALIFIED_VOLUME_UUID: 397A4D4A-9508-391E-814E-3B533C7BD049 — THE ONLY AUTHORIZED CANDIDATE
BSD_IDENTIFIER_DISPOSITION: disk4 / disk4s2 ARE ATTACH-TIME AND ARE NEVER IDENTITY
ROOT_SELECTION_SURFACE: EXISTING --work-root, REUSED UNCHANGED. NO SECOND MECHANISM CREATED
NEW_OPERATOR_SURFACE: ONE OPTIONAL FLAG — m3 canary-source --require-volume-uuid
LAUNCH_FLOOR: 185 GiB — 198,642,237,440 BYTES — IMPLEMENTED, FAIL-CLOSED
PRE_F2_FLOOR: 50 GiB — 53,687,091,200 BYTES — REPLACES THE 30 GiB CONSTANT IN CODE
SUPERSEDED_CONSTANT: PRE_F2_MINIMUM_FREE_BYTES 30 * 1024**3 → 50 * 1024**3. NO REACHABLE 30 GiB PATH
CONTINUOUS_F2_HARD_FLOOR: 10 GiB — 10,737,418,240 BYTES — UNCHANGED (D124-R5)
CONTINUOUS_F2_ALERT: 20 GiB — 21,474,836,480 BYTES
SQLITE_TMPDIR_DISPOSITION: REQUIRED EXPLICITLY, VALIDATED, NEVER SET BY LIBRARY CODE
POWER_LOSS_CLAIM: NONE — PROCESS-CRASH RECOVERY ONLY, UNCHANGED FROM D136-R6
FOCUSED_BASELINE_BEFORE: 317 PASSED
FOCUSED_AFTER: 384 PASSED
FALSIFICATION: 17 REVERSIBLE MUTATIONS, EVERY ONE CAUGHT BY NAMED TESTS
LIVE_PREFLIGHT: RUN — READ-ONLY, NOTHING CREATED ON THE VOLUME
MIGRATION_HEAD: 0015 — 0016 ABSENT, UNAPPLIED, NOT AUTHORIZED
ACTIVATION_CONSTANTS: ALL THREE REMAIN None
NETWORK_AUTHORIZATION: NONE — REQUEST CEILING 0
CORRECTED_CANARY_AUTHORIZATION: NO
E0_EXECUTION_AUTHORIZATION: NO
PRE_NETWORK_BLOCKER: CensusOrchestrator._parse_bulk — OPEN, DELIBERATELY UNREPAIRED
NEXT_STAGE: INDEPENDENT REVIEW, THEN AN OWNER DECISION ON CANARY AUTHORIZATION
```

The implementation of the nine items accepted
[Decision 136](decision_136_m3_3_external_ssd_active_volume_qualification.md) §11 (**D136-R11**)
assigned to this stage. **Decision 136 qualified a volume; this record makes it safe to use one.**
Neither adopts it, and **neither starts a run**.

## 1. What this record is, and what it is not

**It is an implementation record.** Decision 136 shipped an empty executable change set on purpose:
it proved the external SSD mechanically sound and created a **narrow one-canary exception**
(D136-R8) to the standing D125-R4 cold/archive-only rule, and then stopped — because
*qualification is not adoption*, and the exception **grants no authority now**. This record
implements the machinery that exception depends on and validates it.

**It is not an acceptance, and it is not an authorization.** It carries no acceptance token. It
does not adopt the external volume, does not create a world, a run identity, an execution
namespace, or a launch receipt, and does not authorize a corrected complete-source canary. The
guards below decide whether a launch *may be attempted*; **D137-R12 reserves the decision that one
*is* attempted to a separate owner instrument.**

Three steps were named in [Decision 135](decision_135_m3_3_corrected_run_capacity_reconciliation.md)
§10 (**D135-R5**) — *selecting a path is not qualifying a volume, and qualifying a volume is not
adopting it*. Decision 136 completed the second. **This record completes neither the third nor any
part of it; it builds what the third will need.**

## 2. Entry state

Branch `main` at `8d25d954f1025dc2ac67bd87ec6fc4ee0c9c2de8`, tree
`d1315c9872b1b9cbf0fe931404ea78f69064d658`, `origin/main` identical, `0/0` ahead/behind, working
tree clean, nothing staged. Latest governance record Decision 136. Migration head `0015`; `0016`
absent. `PRE_E0_CATALOG_TRANSITION_AUTHORITY`, `M3_3_E0_EXECUTION_AUTHORITY`, and
`STALE_WRITER_LEASE_RECOVERY_AUTHORITY` all `None`. `network.enabled=false`,
`network.m3_acquire_enabled=false`. `PRE_F2_MINIMUM_FREE_BYTES` live at `30 * 1024**3`.

The qualified volume was attached: `/Volumes/SSK SSD`, `/dev/disk4s2`, ExFAT via FSKit.

## 3. The architecture found — and why no second root-selection mechanism exists

**D137-R2 says to use an existing configurable working-root surface if one exists and is
sufficient. One does, and it is.** The canary already takes an operator-supplied absolute
`--work-root`, and already establishes the invariant **twice** — once at the operator surface for a
fast, stack-trace-free refusal, and once inside `run_single_source_canary` itself, so a direct
library caller cannot reach a location the operator surface would have refused:

| Layer | Symbol |
|---|---|
| CLI | `m3 canary-source --work-root` |
| Operator function | `run_canary_source_command(work_root=...)` |
| Run boundary | `require_canary_work_root(work_root, tree=...)` |
| Primitive | `require_disposable_work_root(...)` → `require_external_evidence_root(...)` |
| World | `create_world(work_root, run_id)` — create-once `mkdir`, symlink-refusing |

**What was missing was never a way to *name* an external root. It was a way to *authenticate*
one.** Nothing in the repository could answer "is this path on the volume the owner qualified?",
"is it clear of the D130 archive?", "is there `185` GiB on *that* filesystem?", or "where will
SQLite spill?" — `SQLITE_TMPDIR` returned **zero** matches repository-wide before this stage.

So this record adds authentication and adds nothing else. The new guards live in one new module,
`src/disclosure_drift/m3/external_working_root.py`, and reach the run through **one optional
parameter**. Omitted, every path behaves exactly as accepted Decision 116 left it. Supplied, every
guard becomes a precondition of the run rather than of whoever launched it.

## 4. The volume-identity guard — D137-R1

`require_qualified_volume()` authenticates the volume hosting the selected root against the exact
accepted **Volume UUID `397A4D4A-9508-391E-814E-3B533C7BD049`**.

**Neither the BSD identifier nor the mount path is identity.** `disk4` and `disk4s2` are assigned
at attach time and will differ across reboots and re-plugs. `/Volumes/SSK SSD` is whatever volume
happens to be mounted there — which is precisely the substitution a mount-path check cannot see.

Four outcomes, one of which is a pass:

| Condition | Outcome |
|---|---|
| the volume reports the expected UUID | **PASS**, and its identity is returned |
| it reports a different UUID | **REFUSED** |
| nothing is mounted where the root points | **REFUSED** |
| the lookup fails, for any reason | **REFUSED** |

**There is no fallback to internal storage in any of the three refusals.**

The identity is read from `diskutil info -plist` and parsed as a **property list** — a structured
form exists, so the fragile human-oriented table is not parsed. `diskutil` will not answer for an
arbitrary subdirectory, so the mount point is **derived** first by `mount_point_of()`, which walks
upward while `st_dev` is unchanged. That is the definition of a mount point rather than a guess at
one, and it means an operator cannot *assert* that a path is external.

**No test depends on the operator's SSD.** Every guard takes `provider=None` and resolves
`macos_volume_identity` from module globals **at call time** rather than binding it as a default
argument, so a substituted provider reaches the composed preflight and the run path too — not only
a directly-called guard.

## 5. The working root — D137-R2

The future canary working world must reside on the accepted external volume, and the existing
`--work-root` surface carries it. **No global repository relocation, no movement of the operational
catalog, and no movement of accepted source evidence** was performed or is required. The future
world remains **create-once under a new run identity** — [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
**D129-R8**, unchanged.

The accepted shape is a **sibling tree at the volume root**, beside the D130 archive rather than
beneath it, which is the same shape Decision 136's own scratch tree used.

## 6. Archive isolation — D137-R3

`require_outside_d130_archive()` refuses three states, all decided on **`realpath`-resolved,
case-folded path components**:

- the root **is** the archive directory;
- the root lies **inside** it — the case a `..` path or a symlink would otherwise launder;
- the archive lies **inside the root** — which the sibling shape excludes, and which would place
  the only surviving copy of the D128 evidence inside a disposable tree. This third refusal mirrors
  the rule `require_disposable_work_root` already states for the private evidence root.

**Comparing components rather than strings is load-bearing in both directions.** `realpath`
collapses `..` and follows symlinks *before* anything is compared, so aliasing cannot get in; and a
component-wise prefix cannot mistake `FDD_M3_3_D130_D128_ARCHIVE_WORKING` for a child of
`FDD_M3_3_D130_D128_ARCHIVE`, so a lawful sibling is not falsely refused. A naive `startswith`
would fail the second case, and refusing a lawful root is still a defect even though it errs safe.

## 7. The `185` GiB launch floor — D137-R4

`require_launch_free_space()` requires **`>= 198,642,237,440` bytes** free — accepted
[Decision 135](decision_135_m3_3_corrected_run_capacity_reconciliation.md) §7 (**D135-R2**), placed
at `PRE_LAUNCH` by §11 (D135-R7) and confirmed unchanged by
[Decision 136](decision_136_m3_3_external_ssd_active_volume_qualification.md) §5 (D136-R2).

It is measured on **the filesystem hosting the selected working root**, on that root's nearest
existing ancestor so a root that does not exist yet is still measured on the volume it would be
created on. Measuring the internal Data volume while writing to an external one would satisfy the
arithmetic and none of the intent.

`>=` is the rule, so the floor itself admits. **A shortfall refuses the launch. Nothing is deleted,
moved, or cleaned to reach it**, and an unmeasurable volume refuses rather than admitting on a
missing value.

## 8. The `50` GiB pre-F2 replacement — D137-R5

`PRE_F2_MINIMUM_FREE_BYTES` is now **`50 * 1024**3` = `53,687,091,200` bytes**, replacing the
`30 * 1024**3` = `32,212,254,720` value [Decision 127](decision_127_m3_3_pre_f2_admission_guard.md)
introduced from the D124-R5 figure of the time. Accepted Decision 135 §8 (**D135-R3**) found `30`
GiB **inadequate** for the corrected run; Decision 136 §11 (D136-R11 item 6) made replacing that
behaviour this stage's work.

**The constant moved. The mechanism did not.** The strict `<` comparison, the call site between
F1's return and F2's call ([Decision 126](decision_126_m3_3_complete_first_source_final_preflight.md)
§7, D126-R6), the refusal's shape, and the Decision 094 §6.4 resolution-before-projection ordering
are all byte-unchanged.

**The old behaviour has no reachable path.** It was one constant read from one comparison, so
raising the constant retires it entirely rather than leaving a second branch, a fallback, or a
caller-supplied override that could still select it. This is proved directly rather than asserted:
`test_the_superseded_thirty_gibibyte_amount_no_longer_admits` pins free space at *exactly*
`32,212,254,720` and requires a refusal.

Accepted Decision 127's own test file is **updated in place, not deleted and not skipped**: every
claim it made is re-proved at the floor that now controls, and the superseded amount is kept as a
named constant precisely so "the old value no longer admits" can be tested against the exact number
that used to.

**Three floors, three questions, and none replaces another:**

| Where | Floor | Behaviour on breach |
|---|---|---|
| `PRE_LAUNCH` | `185` GiB / `198,642,237,440` B | **refuse to launch** |
| `POST_F1_PRE_F2` | `50` GiB / `53,687,091,200` B | **refuse F2** before its transaction opens |
| `DURING_F2` continuous | `10` GiB / `10,737,418,240` B | **hard stop**, alerting from `20` GiB |

## 9. Continuous F2 monitoring — D137-R6

`f2_capacity_state()` classifies a continuous reading, and `scripts/m3/canary_watchdog.py capacity`
samples it from outside the run. Both thresholds are **inclusive**, as Decision 135 §11 states them.

| Free space | State | Watchdog exit |
|---|---|---|
| `> 20` GiB | `F2_CAPACITY_NORMAL` | `0` |
| `<= 20` GiB | `F2_CAPACITY_ALERT` | `2` |
| `<= 10` GiB | `F2_CAPACITY_HARD_STOP` | `6` |
| unmeasurable | `CAPACITY_REFUSED_UNMEASURABLE` | `3` |

**The `10` GiB emergency floor did not move.** Raising the admission gate to `50` GiB says what must
be true *before* the transaction opens; it says nothing about the emergency floor *during* it, and
the two are deliberately different numbers.

**A hard stop during F2 is a rollback, not a truncation**, and the operator is told so in the
message itself rather than left to infer it: F2 is a **single transaction**, so stopping inside it
discards the in-flight projection entirely.

**The subcommand reports and never acts.** It sends no signal, deletes nothing, and cleans nothing
at any threshold — acting stays the operator's decision through the existing `stop` subcommand, and
the accepted D131 no-escalation invariant is untouched. The three thresholds are **imported** from
the package rather than restated in the script: a watchdog carrying its own copy of a frozen floor
is a second definition that can drift, and a monitor that disagrees with the gate it monitors is
worse than none.

## 10. Phase-boundary observability — D137-R7

`observe_capacity()` records one `CapacityObservation` per accepted boundary, and the accepted
Decision 135 §11 labels are the **whole** set — an invented label is refused rather than recorded.

A run held to the external requirement records `PRE_LAUNCH`, `POST_F0`, `PRE_F1`,
`POST_F1_PRE_F2`, and `POST_F2` into its result document, each carrying free bytes, total bytes,
database bytes, WAL bytes, temporary-directory allocation, the volume's identity, and a timestamp.

**`DURING_F2` is deliberately not among them.** F2 is one blocking call inside one transaction, so
nothing inside that process can sample it; that boundary belongs to the watchdog, which samples from
outside. Claiming it in-process would be inventing a measurement that was never taken.

**An unknown measurement stays `None`, never `0`.** Reporting a missing WAL as zero would be
indistinguishable from a checkpointed one — exactly the confusion D128's evidence left behind.

**A run with no external requirement records nothing and renders no key.** Emitting an empty list
would change the result document every previous canary produced, including the byte-level
evidence-equivalence the accepted [Decision 119](decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md)
cache-budget proof rests on. An absent key and an empty list say the same thing, and only one of
them is free.

## 11. `SQLITE_TMPDIR` — D137-R8

Accepted Decision 124 §9 (D124-R5) has required explicit `SQLITE_TMPDIR` placement since it was
written; D128 left its peak unmeasured, and Decision 136 §8 (D136-R5) carried the gap forward.
`require_external_sqlite_tmpdir()` closes it with four fail-closed conditions: the variable is
**set** and non-blank; it is an **absolute** path to an **existing directory**; it is **outside the
D130 archive**; and it is on the **same qualified external volume** as the working world.

**It is validated, never set.** Assigning the variable from inside library code would put a
process-wide side effect in a path whose whole purpose is to refuse unsafe states, and would hide
the very setting the operator must be able to see. The launcher exports it, the runbook says to, and
the guard refuses if it is absent or wrong.

Unset, SQLite spills to the operating system's temporary directory **on the internal volume**,
silently — which the capacity model does not cover. That is the exact failure this guard exists to
prevent, and it is proved by counterexample rather than asserted.

## 12. Operator and physical conditions — D137-R9

`Docs/m3/operator_runbook.md` §28d states twelve conditions for a future launch: external power; the
exact qualified SSD connected; the SSD physically stationary; no eject or unplug; no reformat or
repartition; no unrelated write-heavy activity on it; system sleep prevented; a `caffeinate`/no-sleep
launcher; the D130 archive precheck; the authenticated Volume UUID; `>= 185` GiB free; and the
working root outside the archive.

**Four of the twelve are mechanically verified and eight are not.** The runbook says which are
which, and says explicitly that the preflight's silence about the physical ones is not evidence they
hold. **No attempt is made to programmatically infer "the Mac is physically stationary."** A fake
automated proof of an unverifiable condition is worse than an honest checklist.

## 13. The bounded D130 archive pre/postcheck — D137-R10

`verify_d130_archive()` compares the archive against the compact governed proofs
[Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md) §6 (D130-R2) records — the same
bounded check Decision 136 §10 (D136-R7) ran in `0.040` s. **Four small files are hashed. The
`103,966,696,960`-byte tar is `stat`-ed and never opened.**

A future launch **refuses** if the precheck differs. A post-run difference is a **blocker**, not a
note: it would mean the corrected canary disturbed the only surviving copy of the D128 evidence.

That the tar is never read is proved by a **tripwire over `Path.read_bytes`** rather than by reading
the source: the check still reports no differences with the tripwire armed, so the bytes were never
touched.

## 14. Claim boundaries — D137-R11

**Nothing implemented here claims journaled filesystem semantics, power-loss safety,
surprise-removal safety, or USB-bridge cache-flush correctness.** Decision 136 §9 (D136-R6)
established **process-crash recovery only**; ExFAT has no metadata journal, and D136 could not
distinguish a satisfied `F_FULLFSYNC` from a bridge that ignored one. The guards here reduce
**capacity and path** risk. They do not convert the volume into a journaled one, and the module's
own documentation says so where a reader would otherwise infer more.

## 15. What this record does not authorize — D137-R12

**No canary. No run identity. No production world. No launch receipt. No execution namespace. No
terminal state.** A passing preflight prints `canary_authorized: false`, and that is a fact rather
than a formality. Nothing here discharges D129-R2, D129-R8, or D129-R12; nothing enables E0, network,
SEC, or HTTP at request ceiling `0`; nothing creates or authorizes migration `0016`; and
`CensusOrchestrator._parse_bulk` remains an open PRE-NETWORK blocker, deliberately unrepaired.

## 16. The change set

| Path | What changed |
|---|---|
| `src/disclosure_drift/m3/external_working_root.py` | **new** — every D137 guard: the frozen UUID, the `185`/`50`/`20`/`10` GiB constants, `mount_point_of`, `macos_volume_identity`, `require_qualified_volume`, `require_outside_d130_archive`, `require_launch_free_space`, `f2_capacity_state`, `CapacityObservation`/`observe_capacity`, `require_external_sqlite_tmpdir`, the D130 compact proofs and `verify_d130_archive`, and the composed `external_canary_preflight` |
| `src/disclosure_drift/m3/single_source_canary.py` | `PRE_F2_MINIMUM_FREE_BYTES` `30` → `50` GiB; one optional `require_volume_uuid` (plus `environ`) on the run, the prefix profile, and the operator surface; the `_PhaseObserver` seam and five in-process phase observations; `CanaryResult.capacity_observations`, rendered only when non-empty |
| `src/disclosure_drift/cli.py` | one optional flag, `m3 canary-source --require-volume-uuid` |
| `scripts/m3/canary_watchdog.py` | the `capacity` subcommand, exit `6`, thresholds imported from the package; no signal, no deletion, no escalation change |
| `tests/unit/test_d137_external_working_root.py` | **new** — `65` tests, every guard proved at its boundary and against the state it refuses |
| `tests/unit/test_d127_pre_f2_admission_guard.py` | updated in place to the `50` GiB floor; `2` tests added proving the superseded amount no longer admits |
| `Docs/m3/operator_runbook.md` | §28d — the external-volume preflight, the twelve operator conditions, the monitoring table, the archive postcheck, and the launch command marked **not authorized** |

**No migration. No schema change. No parser or runtime-semantics change. No `mmap`. No checkpoint-cadence change. No `_parse_bulk` repair.**

## 17. Validation

**Focused baseline before any edit: `317` passed** across `test_d116_single_source_canary.py`,
`test_d119_cache_and_prefix.py`, `test_d127_pre_f2_admission_guard.py`,
`test_d131_signal_and_monitor.py`, and `tests/integration/test_m3_cli.py`, in `158.76` s.
**After: `384` passed** in `162.62` s over the same set plus
`test_d137_external_working_root.py` — `317 + 65 + 2`, with **no regression**.

**Falsification: `17` reversible source mutations, every one caught.** Each protection was broken
or inverted in place, the targeted tests were run, and the file was restored; the tree was verified
byte-identical afterwards. No source-mutating automated framework was used.

| Mutation | Caught by |
|---|---|
| UUID comparison removed | `test_a_wrong_uuid_is_refused`, `test_the_uuid_comparison_is_case_insensitive_and_otherwise_exact`, `test_an_internal_temporary_root_is_refused`, `test_the_composed_preflight_refuses_when_any_single_guard_fails[uuid…]`, `test_a_run_on_a_wrong_volume_is_refused_before_a_world_exists` |
| qualified-UUID constant changed | `test_the_frozen_uuid_is_the_decision_136_volume` |
| archive child-containment refusal removed | `test_a_child_of_the_archive_is_refused`, `test_a_dot_dot_path_that_normalizes_into_the_archive_is_refused`, `test_a_symlink_resolving_into_the_archive_is_refused`, `test_a_temporary_root_inside_the_archive_is_refused`, `test_the_composed_preflight_refuses_when_any_single_guard_fails[archive…]` |
| `realpath` dropped from containment | `test_a_dot_dot_path_that_normalizes_into_the_archive_is_refused`, `test_a_symlink_resolving_into_the_archive_is_refused` |
| launch floor lowered one byte | `test_the_launch_floor_is_exactly_one_hundred_and_eighty_five_gibibytes`, `test_one_byte_below_the_launch_floor_refuses`, `test_the_composed_preflight_refuses_when_any_single_guard_fails[capacity…]` |
| launch comparison off-by-one | `test_one_byte_below_the_launch_floor_refuses`, `test_the_composed_preflight_refuses_when_any_single_guard_fails[capacity…]` |
| launch measurement redirected off the selected root | `test_the_launch_floor_measures_the_selected_root_not_the_process_volume` |
| unmeasurable volume admitted | `test_an_unmeasurable_volume_refuses` |
| pre-F2 floor reverted to `30` GiB | `test_the_floor_is_exactly_fifty_gibibytes`, `test_the_superseded_thirty_gibibyte_floor_is_gone`, `test_one_byte_below_the_floor_refuses`, `test_the_superseded_thirty_gibibyte_amount_no_longer_admits`, `test_below_the_floor_the_f2_tripwire_is_never_reached`, `test_the_pre_f2_floor_matches_the_decision_137_value` |
| hard floor made exclusive at the boundary | `test_the_continuous_states_are_classified_at_their_boundaries[10737418240…]`, `test_the_watchdog_classifies_and_exits_at_each_threshold[10737418240…]`, `test_the_watchdog_hard_stop_states_that_f2_rolls_back` |
| hard floor raised to `20` GiB | `test_the_continuous_thresholds_are_twenty_and_ten_gibibytes` and four threshold cases |
| alert threshold made exclusive | `test_the_continuous_states_are_classified_at_their_boundaries[21474836480…]`, `test_the_watchdog_classifies_and_exits_at_each_threshold[21474836480…]` |
| `SQLITE_TMPDIR` same-volume requirement removed | `test_an_internal_temporary_root_is_refused` |
| unset `SQLITE_TMPDIR` allowed to fall back | `test_an_unset_temporary_root_is_refused`, `test_the_composed_preflight_refuses_when_any_single_guard_fails[tmpdir…]` |
| phase-label validation removed | `test_an_invented_phase_label_is_refused` |
| the `104` GB tar given a digest | `test_the_archive_proofs_are_the_decision_130_identities`, `test_the_large_tar_is_never_read` |
| archive precheck no longer blocks | `test_the_preflight_refuses_when_the_archive_precheck_differs` |

## 18. The live read-only preflight

Run once against the attached qualified volume. **Read-only: nothing was created, written,
deleted, ejected, or benchmarked, and the `104` GB tar was not opened.**

| Check | Result |
|---|---|
| mount present | `/Volumes/SSK SSD` |
| **Volume UUID** | `397A4D4A-9508-391E-814E-3B533C7BD049` — **exact match** |
| filesystem / device | `exfat` / `disk4s2` (recorded, **not** used as identity) |
| D130 archive present | yes, **`24` entries** |
| archive compact precheck | **no differences**, `0.171` s; tar `103,966,696,960` B by `stat`, **not hashed** |
| free on that volume | **`310,498,951,168` B / `289.1747` GiB** |
| against the `185` GiB floor | **PASS**, surplus `111,856,713,728` B / `104.1747` GiB |
| archive-child control root | **refused** |
| volume-root control root | **refused** |
| `SQLITE_TMPDIR` unset | **refused** |
| `SQLITE_TMPDIR=/tmp` (internal) | **refused** — internal volume UUID reported, not the qualified one |
| proposed work root / temp root created | **no** — both absent afterwards |

**One honest discrepancy.** Free space reads `310,498,951,168` B, which is `393,216` B — exactly
three `131,072`-byte ExFAT allocation blocks — **higher** than the `310,498,557,952` B Decision 136
§5 recorded. It is recorded rather than rounded away. It moves no floor and no verdict; free space
rose, and both independent reads in this session agree with each other.

**The live `SQLITE_TMPDIR` directory was not created**, because creating it is a write to the
volume and this stage authorizes none. The guard's accepting path is therefore proved
**synthetically**; only its refusing paths were exercised live.

## 19. Limitations, stated rather than smoothed

- **`DURING_F2` is not sampled in-process**, and cannot be. It depends on the operator running the
  watchdog's `capacity` subcommand alongside the run; nothing forces that.
- **The external requirement is opt-in.** Omitting `--require-volume-uuid` restores the pre-D137
  behaviour exactly. That is deliberate — every existing internal-volume canary path must keep
  working — but it means the guards protect a run that *asks* to be protected.
- **`macos_volume_identity` is macOS-only.** It shells to `diskutil`. On another platform the
  lookup fails, and failing closed means the external mode refuses rather than degrading.
- **The `SQLITE_TMPDIR` guard validates placement, not peak.** Peak spill is recorded at phase
  boundaries when a run takes them; it is not bounded in advance, and D136-R5 left it unmeasured.
- **No live end-to-end rehearsal was performed**, because that would require creating a world on
  the volume. The composed preflight's accepting path is proved synthetically and by its live
  refusals, not by a live pass.

## 20. What did not change

- **D129-R2** — every D128 semantic count remains rejected. **D129-R8** — from scratch, new world,
  new run identity.
- **The D131 runtime configuration**, the parser, and the shard-dispatch semantics.
- **D134's `mmap` and relaxed-checkpoint candidates remain rejected.**
- **The `10` GiB continuous floor and the no-`VACUUM` rule** (D124-R5).
- **D125-R3** stands; **D125-R4 stands as the general rule**, narrowed only by D136-R8.
- **E0, network, SEC, and HTTP remain unauthorized**; all three activation constants remain `None`;
  request ceiling `0`; migration head `0015` with `0016` absent.
- **`CensusOrchestrator._parse_bulk` remains an open PRE-NETWORK blocker**, deliberately unrepaired.

## 21. The next authorized action

**Independent review of this implementation, and nothing else.** The D136-R8 exception takes effect
only after D137 implementation **and acceptance**; this record is the implementation and claims
neither. A session that creates a canary world, a run identity, or a launch receipt on the strength
of this record is acting outside it.
