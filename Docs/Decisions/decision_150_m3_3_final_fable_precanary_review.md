# Decision 150 — Final Fable Pre-Canary Independent Whole-System Review

```text
STATUS: PUBLISHED — INDEPENDENT REVIEW RECORD
RECORD_TYPE: FINAL INDEPENDENT WHOLE-SYSTEM PRE-CANARY REVIEW — NO SOURCE CHANGE, NO TEST CHANGE, NO REPAIR
DATE: 2026-08-24
OWNER: Joey authorization; independent review performed by Claude Fable 5 at maximum effort, fresh /clear
CLASSIFICATION: FINAL ADVERSARIAL WHOLE-SYSTEM REVIEW OF THE DECISION 149 TREE — FINDINGS RECORDED, NONE FOUND
AUTHORIZATION:
  M3_3_D150_FINAL_FABLE_PRECANARY_INDEPENDENT_REVIEW_AUTHORIZED — spent by the publication of this record
ACCEPTED_PREDECESSOR: M3_3_D149_FINAL_PRECANARY_LIMITATION_CLEANUP_OWNER_ACCEPTED

REVIEWED_HEAD: 28a0ad92406077f8e4cf55ad2261d5db96c2c308
REVIEWED_TREE: a5fd9cae77165936db9f076ff8a8188f1b9c0a22

VERDICT: D150_FINAL_FABLE_PRECANARY_REVIEW_PASS
FINDINGS: 0 BLOCKER / 0 MAJOR / 0 MINOR / 0 ACTIONABLE INFO / 0 ACTIONABLE PRE-CANARY LIMITATION

PHASE_BOUNDARY_RAM_RECLAMATION: IMPLEMENTED — proved in three real OS processes
GOVERNED_MODE_RUN: REFUSED on every externally governed root — production, AST-pinned above the call
PHASE_CONTRACT: phase-f0 -> phase-f1 -> phase-f2 — each VALIDATED to admission on the qualified live-equivalent config
PREDECESSOR_PROCESS_DEATH: F0->F1 and F1->F2 VALIDATED — a live predecessor refuses the successor
SAME_GOVERNED_WORLD: VALIDATED — successor attaches, never copies; no hidden full-size duplication
REPOSITORY_IDENTITY: GENUINE — measured from Git at the module's own location, reproduced live; HEAD and TREE both bound
DIRTY/DELETED/RENAMED/UNTRACKED: fail-closed, no override, no repair
DOCK_TOPOLOGY: VALIDATED live — USB_VIA_THUNDERBOLT_DOCK present now, direct/unqualified refuse
EXACT_VOLUME_UUID: 397A4D4A-9508-391E-814E-3B533C7BD049 — matched live
D130_ARCHIVE: intact and isolated — giant tar 103,966,696,960 B stat-only, compact proofs matched, no writable route
SOURCE_IDENTITY: VALIDATED against the real artifact — 1,556,847,020 B / SHA-256 c85744be… / 985,834 members / 5,337 shards
STRUCTURAL_PARENT_CENSUS: sound — 0 orphan, 0 duplicate, 0 conflict; shard-before-parent supported; digest e58b9100…
D129/D131_SEMANTICS: intact — shards resolved by authoritative parent, filename corroborative only
OPERATIONAL_CATALOG: unchanged and read-only — SHA-256 57e36a78… / 359,378,944 B / logical 5c823d21… / observation b1122bb9…
CAPACITY_GATES: 185 / 60 / 55 / 50 GiB and 20 / 10 GiB F2 — exact; F2 rollback proved on a fresh fixture
NETWORK_ISOLATION: zero sockets at import, no transport constructed on the canary path, both gates false
PARSE_BULK_REACHABILITY: PROVABLY CANARY-UNREACHABLE — re-traced independently, unrepaired
FALSIFICATION: 19 load-bearing mutations, 19 KILLED, every file restored byte-identical by SHA-256
MAKE_CHECK_FAST: PASS — 5315 passed, 1 skipped

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

This is the **final independent whole-system pre-canary review** of the
[Decision 149](decision_149_m3_3_final_precanary_limitation_cleanup.md) implementation tree,
performed from a fresh `/clear` context by a **Claude Fable 5** session at maximum effort that wrote
none of Decisions 145 through 149 and **inherited none of their conclusions**. Every property below
was reconstructed independently from the published repository, verified live against the running
host and the real frozen artifacts where the review boundary permits, and falsified by an
independent mutation campaign.

**The verdict applies to the technical tree, not to the commit that publishes this record.**

```text
REVIEWED_HEAD  28a0ad92406077f8e4cf55ad2261d5db96c2c308
REVIEWED_TREE  a5fd9cae77165936db9f076ff8a8188f1b9c0a22
```

The later documentation-only commit that adds this file, the registry row, the index rows and the
`STATUS` block is **not** the reviewed artifact. The implementation diff
`git diff 28a0ad92406077f8e4cf55ad2261d5db96c2c308 HEAD -- src tests scripts configs` was **empty**
before publication and remains empty after it.

**A review records; it does not repair.** Nineteen bounded falsification mutations were applied and
every one was restored byte-identical by SHA-256, with an empty `git diff` afterward. No production
defect was corrected in this session, because none was found.

**It accepts nothing and authorizes nothing.** Not Decision 149, not Decision 147, and not
Decisions 137, 138, 140, 141, 142, 143, 144 or 145.
[Decision 146](decision_146_m3_3_final_independent_post_d145_precanary_review.md)'s `FAIL` verdict
remains historically valid for the tree it reviewed, and
[Decision 143](decision_143_m3_3_final_independent_precanary_review.md)'s does for its own. **A
`PASS` here is not permission to run anything.** `CANARY_AUTHORIZED = NO`.

## 2. Entry state

Every material entry predicate the authorization named was verified live and matched exactly.
**Nothing was repaired or normalized to make it match.**

| Predicate | Expected | Observed |
|---|---|---|
| Branch | `main` | `main` |
| `HEAD` | `28a0ad92…` | `28a0ad92406077f8e4cf55ad2261d5db96c2c308` |
| Tree | `a5fd9cae…` | `a5fd9cae77165936db9f076ff8a8188f1b9c0a22` |
| `origin/main` | equal to `HEAD` | equal — 0 ahead, 0 behind |
| Worktree | clean, nothing staged, no untracked residue | clean |
| Tag at `HEAD` | none | none |
| Latest governance | Decision 149 | `decision_149_m3_3_final_precanary_limitation_cleanup.md` |
| D149 CI run `32733076923` | `SUCCESS`, both mandatory jobs | matches the accepted lineage; the reviewer additionally ran one full `make check-fast` green (§17) |
| Migration head | `0015`, `0016` absent | `0015`; `0016` absent |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` | `None` |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` | `None` |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` | `None` |
| `network.enabled` | `false` | `false` |
| `network.m3_acquire_enabled` | `false` | `false` |

The three load-bearing source files carry the exact SHA-256 Decision 149 §9 recorded on
restoration, which independently confirms the tree is the D149-restored state:
`repository_identity.py 9fd79607…`, `canary_phases.py 53bb8452…`,
`single_source_canary.py 8d6b3b96…` (and `external_working_root.py 90f96a35…`).

## 3. The reconstructed final governed call graph

Reconstructed from the source, not from the authorization packet. The only governed real-canary
route is:

```text
operator/runbook §28h  ->  scripts/m3/canary_launch.py (tmux -d, caffeinate, exec, durable logs)
  ->  disclosure-drift m3 canary-source --mode phase-fN   [cli._m3_canary_source_command]
  ->  single_source_canary.run_canary_source_command
        - resolve private root, disposable work-root boundary
        - require_external_envelope(...)  ->  external is not None on the governed root
        - GUARD: if mode == "run" and external is not None:  REFUSE      (D149-R3)
        - phase = CANARY_PHASE_MODES[mode]  ->  run_single_source_canary_phase
  ->  run_single_source_canary_phase(phase)
        0a require_clean_running_repository()        (repository identity, FIRST)
        0b require_canary_work_root + require_external_envelope(minimum=PHASE_ADMISSION_FLOOR[phase])
        1  acquire_canary_execution_lock (host flock)
        2  select source (read-only) + plan_fingerprint + planned_source_observation
        3  F0: preauthenticate_source, reauthenticate volume, create_world
           F1/F2: attach_world (never create)
        4  WorkingCatalog(attach = phase != f0)  -> require_phase_admission
           (already-ran? predecessor complete? same run/source/code/catalog/plan? predecessor gone?)
        5  _phase_f0_body | _phase_f1_body | _phase_f2_body   (inside write_containment)
        6  F2 only: create-once result document, then durable terminal checkpoint (LAST)
        7  clean process exit  ->  next phase in a NEW process
  ->  after phase-f2: terminal process exit; no successor execution
```

Every production route capable of reaching the governed real source was enumerated. There is **no
hidden whole-run bypass** (`--mode run` on an external root is refused before entry), **no alternate
direct-API route** (`cli.py` reaches the canary through exactly one function; the whole-run entry
point `run_single_source_canary` has exactly one caller, the guarded operator surface — both
AST-pinned), **no phase-order bypass** (`require_phase_admission` refuses out-of-order), **no
multi-source continuation** (one source, no loop, no next-source callback), and **no E0
continuation** (the phase path imports no E0 module).

## 4. The phase contract, and the `--mode run` refusal

Independently proved the only governed real-canary contract is `phase-f0 -> phase-f1 -> phase-f2`:

1. **`--mode run` refuses before the run enters** on any externally governed root — reproduced by
   mutation `M11` (removing the guard is KILLED by
   `test_the_governed_external_route_refuses_mode_run`) and pinned by the AST test
   `test_the_refusal_is_taken_before_the_run_is_entered`, which asserts the guard is envelope-keyed,
   raises, and precedes the whole-run call by line number;
2. `phase-f0` remains reachable and reaches admission on the qualified external configuration;
3. `phase-f1` is reachable **only** from a valid F0 checkpoint — an absent F0 checkpoint refuses,
   even with the world, working catalog and committed rows all present
   (`test_committed_rows_and_a_populated_world_are_not_phase_completion`);
4. `phase-f2` is reachable only from a valid F1 checkpoint;
5. phases cannot execute out of order (`require_phase_admission` predecessor requirement, mutation
   `M8` KILLED);
6. a completed phase cannot be ambiguously replayed (create-once checkpoint; a phase carrying its
   own checkpoint refuses);
7. a checkpoint **version** mismatch fails closed (`PHASE_RESTART_CONTRACT = m3.3-canary-phase-restart/2`;
   a `/1` label refuses "does not continue from");
8. a checkpoint **identity** mismatch fails closed (run id, source, HEAD, tree, catalog digest,
   migration head, plan fingerprint, aggregate execution identity — mutations `M4`–`M8` KILLED);
9. a terminal completed run cannot be continued (`attach_world` refuses a world that already carries
   its result document);
10. no alternate CLI/API surface silently reaches the old full-run path (proof 5 above).

**The refusal is narrow, and that was proved as hard as its presence.** Mutation `M12` — dropping
the `mode == "run"` condition so the guard catches *every* mode — is KILLED by
`test_every_phase_mode_remains_admitted_on_the_same_governed_route`. On an **internal** root
`--mode run` remains exactly the accepted Decision 116 path, untouched, and cannot be mistaken for
the governed route, which is external by construction.

**No governed `--mode run` bypass exists.**

## 5. RAM reclamation is a real process exit

`PHASE_BOUNDARY_RAM_RECLAMATION = IMPLEMENTED`, and it is process replacement rather than any
in-process reset. Verified:

* the operator surface exposes one mode per phase (`phase-f0`, `phase-f1`, `phase-f2`), each routing
  to `run_single_source_canary_phase` in its own process;
* the successor refuses if the predecessor's process is still alive —
  `process_is_live_canary(predecessor.pid, run_id=run_id)` reads the pid from the predecessor's own
  durable checkpoint and from nowhere else, authenticates it by the canary subcommand and exact
  `--run-id`, and treats a recycled id as *gone* (mutation `M9` KILLED by
  `test_a_live_predecessor_process_refuses_the_successor`);
* the three-process demonstration
  (`test_the_three_phases_run_in_three_different_processes_and_each_one_ends`) runs each phase as a
  real child of the test process, observes three distinct operating-system pids, confirms each
  predecessor gone before its successor is admitted, and confirms none is alive afterward;
* there is **no** `gc.collect()` substitute, **no** `SIGSTOP`/suspend substitute, **no** sleeping or
  resident phase worker, and **no** in-process recursive phase invocation — asserted by source scan
  and by the absence of any same-process continuation path;
* `process_peak_resident_bytes()` reports `ru_maxrss` as the **peak**, normalized across Darwin/Linux
  units, and is named as the peak everywhere it appears.

## 6. Repository identity is a measurement

`src/disclosure_drift/m3/repository_identity.py` was reconstructed directly.

* **Derived from the executing source**, `Path(__file__).resolve()`, never the working directory; no
  parameter, CLI flag or environment variable on any surface can declare a revision
  (`test_no_operator_surface_accepts_a_revision`, and the phase entry point signatures carry no
  repository parameter).
* **Both identities recorded** — `rev-parse HEAD` and `rev-parse HEAD^{tree}` — each validated
  against a Git object-name pattern. Both are load-bearing: neutering the HEAD measurement is KILLED
  by `test_the_commit_identity_moves_even_when_the_tree_stands` (mutation `M1`), and neutering the
  TREE measurement is KILLED by `test_the_running_identity_is_the_one_git_reports_for_this_checkout`
  (mutation `M2`).
* **The repository is authenticated, not merely found**: the governing modules must be tracked files
  of the repository Git reports, which closes the enclosure and the in-repository virtual-environment
  cases together.
* **Every Git operation is a read** — `rev-parse`, `status`, `ls-files` — with no `checkout`,
  `reset`, `clean`, `stash`, `fetch`, `pull`, or index mutation.
* **Reproduced live**: the production derivation against this checkout returns
  `head_sha 28a0ad92406077f8e4cf55ad2261d5db96c2c308` and
  `tree_sha a5fd9cae77165936db9f076ff8a8188f1b9c0a22`, matching `git rev-parse` invoked
  independently.

**The dirty-tree contract is fail-closed and repairs nothing.** `require_clean_running_repository()`
runs **first** in the phase entry point, before the work root, the volume, the dock, the power state
or the lock. Admitting an ambiguous tree is KILLED by
`test_the_clean_contract_refuses_an_ambiguous_tree_and_repairs_nothing` (mutation `M3`), and the
positive control `test_the_clean_contract_admits_a_clean_tree` proves the gate can still be passed.
Deleted, staged-deleted, renamed (reporting the new path) and unstaged-rename states are all refused
(Decision 149 §4, re-verified). **The successor re-measures in its own process and compares the
freshly measured value as *observed* against the predecessor's checkpoint as *expected*** — the
named HEAD and TREE comparisons run before the aggregate digest so a refusal names both values
(mutations `M4`, `M5` KILLED at `[head-f1]` and `[tree-f1]`).

## 7. Dock transport, volume identity, and D130 isolation — verified live

The live host was inspected read-only. The **selected dock topology is physically present now** and
the production path classifies it exactly:

| Fact | Value | Result |
|---|---|---|
| Volume UUID | `397A4D4A-9508-391E-814E-3B533C7BD049` | matched |
| Filesystem | `exfat`, `BusProtocol USB`, mounted at `/Volumes/SSK SSD` | as qualified |
| Storage device | `0x090C:0x2320`, serial `SSKPSSD0000000000071` | exactly the qualified device |
| Dock cascade (host-first) | `0x8087:0x0B40 -> 0x17EF:0x30B6 -> 0x17EF:0x30B8` | exactly the frozen chain |
| `classify_transport` | `USB_VIA_THUNDERBOLT_DOCK` | the selected topology |
| `require_qualified_transport(required=DOCK)` | admits | pass |
| `require_qualified_transport(required=DIRECT)` | refuses (`DockTransportError`) | wrong-topology refusal |
| Power / lid | AC power, lid open (`AppleClamshellState = No`) | launch conditions hold |
| Free space | 310,498,426,880 B (~289 GiB) | above the 185 GiB launch floor |

`FIRST_CANARY_REQUIRED_TRANSPORT = USB_VIA_THUNDERBOLT_DOCK` is passed at **all four** production
envelope seams; removing the pin is KILLED by
`test_the_direct_topology_refuses_through_the_operator_path` (mutation `M13`). The exact volume UUID
is the primary identity and the volatile BSD identifier `disk4s2` governs nothing. A wrong asserted
UUID is refused before the transport is read (mutation `M14` KILLED). A stale mount, a missing
volume, and a replacement `st_dev` are each refused by `require_mounted_qualified_volume` /
`AdmittedVolume.require_present` (source-verified).

**D130 archive** verified through the production `verify_d130_archive` against the live volume: the
giant tar is `103,966,696,960` bytes **stat-only, never opened, never hashed**; the four compact
proofs match their accepted digests; the verifier returns an empty difference tuple (intact). A work
root that is, is inside, or contains the archive is refused (mutation `M15` KILLED by
`test_every_phase_refuses_a_work_root_inside_the_d130_archive`); `SQLITE_TMPDIR` inside the archive
is refused; and no runtime/log/pid path can be written into it. **No reachable archive-write route
exists.**

## 8. Source identity, structural parent census, and D129/D131 semantics — verified against the real artifact

The frozen governed source was verified against the real 1.56 GB artifact under the private evidence
root, read-only:

| Property | Expected | Observed |
|---|---|---|
| Byte length | 1,556,847,020 | matched |
| SHA-256 | `c85744be921b0dc5be4e3c7dd44552fc0f57d354d61df38cd92a13926982b82f` | matched |
| Governed `.json` members | 985,834 | matched |
| Historical shards | 5,337 | matched |
| Structural-preflight digest | `e58b910022aca9c88a2833e50f84efbf0719a86d11c09a5ab99c9e530a7f17eb` | matched |
| Parent map | sound | 0 orphan, 0 duplicate, 0 conflict |
| Shard-before-parent ordering | supported | observed `True` |

`preauthenticate_source` authenticates byte length, cryptographic hash, member count and shard count
**before a world exists** (Decision 140 §MINOR-7/INFO-9/10), and `require_sound_parent_map` refuses a
broken parent map before F0. The D129/D131 semantics are intact: shards are resolved by their
primary document's authoritative `filings.files[].name`, the filename CIK is corroboration only, and
a missing/duplicate/conflicting parent fails closed. A source hash mismatch and a shard-parent
failure both fail before expensive F0 work.

## 9. Exact-one-source, network isolation, operational-catalog nonmutation

**Exact one source.** The phase and whole-run paths select exactly one source by
`census_plan_sources.source_instance_id`, refuse an ambiguous or absent identifier, and return after
the one source — there is no source-plan loop, no next-source callback, no three-source campaign, and
no E0 orchestration.

**Network isolation.** Importing the complete canary phase path in a guarded interpreter made **zero
`socket.connect` calls**; both network switches are `false`; and the whole test suite runs under a
`conftest` socket block (`socket.socket`, `create_connection`, `getaddrinfo` all raise). The
transitive presence of `sec.http_client` / `sec.transport` / `m3.acquisition` in the import graph is
**module definition only** — it constructs no transport and opens no socket — and is explicitly
disclosed by the accepted test `test_the_phase_path_imports_no_e0_and_no_transport`, whose checked
property is *no `.e0` module and no `httpx` is loaded, and nothing constructs a transport*. The
`census_orchestrator.py::_parse_bulk` pre-network blocker is **provably canary-unreachable**: no
phase-path module names it, a fresh interpreter that imports the phase path never loads the
orchestrator, and adding such a reference is KILLED by
`test_parse_bulk_remains_canary_unreachable_after_the_phase_decomposition` (mutation `M19`).

**Operational-catalog nonmutation.** The accepted catalog is opened through `SQLITE_OPEN_READONLY`
on every path and copied only through the WAL-safe online-backup interface into a disposable
run-local working catalog; the run compares the catalog SHA-256 before and after. Verified live:
SHA-256 `57e36a788dc8e03ea4d1a4c722418de4c4244d73590c6643feace93c80af2ded`, byte length
`359,378,944`, logical digest `5c823d216957c0035babd4956f9d9e0c3c0b8ea54455231436a514191c6ad306`,
observation digest `b1122bb9fbb084411ce3cb3b7d192c7874c8969aadbb29f6ca313543b8e533be`. No writable
operational-catalog route exists.

## 10. Capacity model, F2 behaviour, and rollback

The frozen capacity constants match the accepted D135/D140 values exactly:

```text
LAUNCH (PRE_LAUNCH / F0 admission)  185 GiB = 198,642,237,440 B
POST_F0                              60 GiB =  64,424,509,440 B
PRE_F1                               55 GiB =  59,055,800,320 B
PRE_F2                               50 GiB =  53,687,091,200 B
F2 ALERT                             20 GiB =  21,474,836,480 B
F2 HARD FLOOR                        10 GiB =  10,737,418,240 B
PHASE_ADMISSION_FLOOR  {f0:185, f1:55, f2:50} GiB
```

The stale 30 GiB pre-F2 gate is unreachable (`test_the_superseded_thirty_gibibyte_floor_is_gone`).
F2 above 20 GiB is normal, 10 GiB < free ≤ 20 GiB alerts and continues, and free ≤ 10 GiB hard-stops
**from inside the open F2 transaction, which rolls back** — the in-flight association projection is
discarded, not truncated, `f2_transaction_rolled_back = True`, `f2_committed = False`. A measurement
failure takes the identical hard-stop path. Neutering the hard-stop classification is KILLED by
`test_the_hard_floor_is_inclusive_and_raises_the_dedicated_condition` (mutation `M16`); the
positive control `test_f2_commits_its_association_rows_when_capacity_holds` proves the normal
> 20 GiB path still commits. Free space is measured on the actual governed working filesystem, the
guard samples at ~5 s (ceiling 60 s) on a monotonic clock with the volume identity re-established
before any free-space number is trusted and the exact UUID re-read on a bounded 300 s interval, and
no gate performs destructive cleanup.

## 11. Watchdog, launch persistence, power/lid

**Watchdog** reads the exact canonical pid, authenticates the exact phase/run identity, scans no
process list, refuses a decoy shell on `argv[0]`, refuses a non-positive pid, sends one `SIGINT`
with **no** escalation and no automatic `SIGKILL`, and correctly treats a dead predecessor phase pid
as expected-dead rather than as a stall. **Launch** is `tmux -d` with `-e SQLITE_TMPDIR`,
`caffeinate -dims`, `time -l` durable resource log, `canary_launch.py` recording the pid before
`exec` and refusing an ignored `SIGINT` or a runtime path under the work root, durable stdout/stderr
on internal storage, the exact UUID and source, a **phase** mode (never `--mode run`), no member
limit, the host execution lock, and the unissued owner-authority placeholder. Each phase is
independently launchable from its validated predecessor checkpoint and **does not depend on
Claude/chat/session continuity** — the detached process survives shell exit and terminal
disconnect. **Power/lid**: AC required, closed lid refused, unknown fails closed unless asserted;
software does not claim to prevent physical lid-close sleep. Live readings: AC power, lid open.

## 12. Hidden-copy, runtime-waste, false-success, evidence completeness

**No hidden full-size copy.** The only `backup(`/copy on the phase path is F0's WAL-safe online
backup of the ~359 MB operational catalog into the disposable working catalog; F1 and F2 **attach**
the same world and copy nothing. Forcing a phase to create rather than attach is KILLED by
`test_the_three_phase_sequence_completes_and_writes_one_result_document` (mutation `M10`). No
`copytree`, `VACUUM INTO`, `rsync`, or per-phase duplication exists.

**No stale long-run timeout.** No timeout guards the ~30-hour in-process parse; the only subprocess
timeouts (git 30 s, ioreg 60 s, diskutil 30 s, pmset/ps 15 s) bound short read-only host queries.
The watchdog disables member-stall alerting at traversal completion and invents no wall-clock kill
for F1/F2.

**False-success prevention.** `require_f0_success` stops the run before F1 on a blocking F0 terminal
(mutation `M17` KILLED by `test_a_failed_predecessor_leaves_no_checkpoint_and_refuses_its_successor`);
`phase-f0` and `phase-f1` write **no** result document — only F2's terminal path does; a repository,
topology, volume, capacity, F1, F2-rollback, checkpoint, or integrity failure each prevents a normal
success.

**Evidence completeness across restarts.** The run's result document is assembled from the durable
per-phase checkpoints plus F2's own measurements — nothing is estimated and no phase is re-run to
recover it. The capacity observations are carried forward so the run holds one chronological record
across all three processes. Pause/resume and safe-to-eject evidence is correctly absent because both
are `NOT_IMPLEMENTED`.

## 13. The full adversarial matrix (§31)

All fifty-six attacks were exercised — by mutation where a single point exists, by production test
otherwise, and by live read-only observation for the topology and archive. **Every one holds.**

| # | Attack | Result | Evidence |
|---|---|---|---|
| 1 | governed `--mode run` bypass | REFUSED | `M11` KILLED; AST guard-before-call |
| 2 | phase order bypass | REFUSED | `M8` KILLED; predecessor requirement |
| 3–4 | F0→F1 / F1→F2 same-process continuation | REFUSED | `M9` KILLED; 3-process demo |
| 5 | predecessor pid still alive | REFUSED | `M9` KILLED |
| 6–7 | HEAD / TREE mismatch | REFUSED | `M4`, `M5` KILLED |
| 8 | dirty repository | REFUSED | `M3` KILLED |
| 9–10 | deleted / renamed tracked path | REFUSED | D149 §4 tests, re-verified |
| 11 | wrong dock topology | REFUSED | `M13` KILLED; live DIRECT-refusal |
| 12 | direct-qualified SSD instead of dock | REFUSED | D144 tests; live `require(DIRECT)` refuses |
| 13 | wrong UUID | REFUSED | `M14` KILLED |
| 14–16 | stale mount / missing SSD / replacement st_dev | REFUSED | `require_mounted_qualified_volume`, `require_present` |
| 17–18 | D130 child work / temp root | REFUSED | `M15` KILLED; tmpdir isolation |
| 19 | absent `SQLITE_TMPDIR` | REFUSED | `require_external_sqlite_tmpdir` |
| 20–23 | insufficient launch / POST_F0 / PRE_F1 / PRE_F2 capacity | REFUSED | D138/D127 floor tests |
| 24 | F2 alert band | ALERT, CONTINUES | D138 alert test |
| 25 | F2 hard floor | ROLLBACK | `M16` KILLED |
| 26 | F2 capacity measurement failure | ROLLBACK | D138 measurement-failure test |
| 27 | `SQLITE_FULL` | ROLLBACK | `transaction()` rolls back on any exception in-flight |
| 28 | F0 blocking failure | STOP before F1 | `M17` KILLED |
| 29 | source hash mismatch | REFUSED pre-world | `preauthenticate_source`; live hash matched |
| 30 | shard-parent failure | REFUSED pre-world | `require_sound_parent_map`; live map sound |
| 31 | second-source continuation | NONE | no loop; structural |
| 32 | network construction/use | NONE | zero-socket probe; conftest block |
| 33 | operational-catalog write | NONE | read-only everywhere; digest unchanged |
| 34 | duplicate concurrent canary | REFUSED | host `flock` execution lock |
| 35 | decoy watchdog target | REFUSED | `argv[0]` authentication |
| 36 | stale long-run timeout | NONE | timeout audit |
| 37 | false-success result | PREVENTED | `M17` KILLED; f0/f1 write no result |
| 38 | checkpoint version mismatch | REFUSED | `/1` label refused |
| 39 | checkpoint identity mismatch | REFUSED | `M4`–`M7` KILLED |
| 40 | completed-world continuation | REFUSED | `attach_world` refuses a world with a result |
| 41–42 | predecessor alive at F1 / F2 admission | REFUSED | `M9` KILLED |
| 43–44 | F1 / F2 different world than predecessor | REFUSED | `M10` KILLED (attach, not create) |
| 45 | successor uses stale predecessor pid metadata | REFUSED | pid from checkpoint; recycled-id test |
| 46 | phase restart loses repository identity evidence | PRESERVED | checkpoint records HEAD/tree |
| 47 | phase restart loses topology/volume identity | PRESERVED | envelope re-established each phase |
| 48 | phase restart loses capacity-policy identity | PRESERVED | folded into execution identity (`M18`) |
| 49 | phase restart duplicates world/catalog | NONE | `M10` KILLED; no copy |
| 50–51 | phase-f0 / phase-f1 writes final success | NONE | only F2 handoff writes the result |
| 52 | successor checkpoint missing | REFUSED | `M8` KILLED |
| 53 | successor checkpoint partial/corrupt | REFUSED | fail-closed decode; legacy-contract test |
| 54 | execution-identity digest mismatch | REFUSED | `M6` KILLED |
| 55 | capacity-policy constant mismatch | REFUSED | `M18` KILLED |
| 56 | transport-profile mismatch after predecessor completion | REFUSED | `M13` KILLED; every-phase topology test |

## 14. Independent falsification campaign

Nineteen reversible, source-isolated mutations, each aimed at a distinct load-bearing property and
each mapped to an exact killing node. **19 applied, 19 KILLED, 0 survivors.** Every mutated file was
restored and its restoration proved byte-identical by SHA-256 against a pre-campaign baseline.

| # | Mutation | Killed by |
|---|---|---|
| `M1` | repository HEAD reads the tree | `test_the_commit_identity_moves_even_when_the_tree_stands` |
| `M2` | repository TREE reads the commit | `test_the_running_identity_is_the_one_git_reports_for_this_checkout` |
| `M3` | dirty tree admitted | `test_the_clean_contract_refuses_an_ambiguous_tree_and_repairs_nothing` |
| `M4` | successor reuses predecessor HEAD as observed | `…refuses_a_predecessor_from_another_revision[head-f1]` |
| `M5` | successor reuses predecessor TREE as observed | `…refuses_a_predecessor_from_another_revision[tree-f1]` |
| `M6` | execution-identity digest not compared | `test_a_successor_refuses_a_changed_governing_configuration` |
| `M7` | run-id continuity not compared | `test_a_successor_refuses_another_runs_checkpoint` |
| `M8` | F1 requires no predecessor checkpoint | `test_committed_rows_and_a_populated_world_are_not_phase_completion` |
| `M9` | live-predecessor death not required | `test_a_live_predecessor_process_refuses_the_successor` |
| `M10` | F1/F2 create rather than attach the world | `test_the_three_phase_sequence_completes_and_writes_one_result_document` |
| `M11` | governed `--mode run` admitted | `test_the_governed_external_route_refuses_mode_run` |
| `M12` | `--mode run` refusal made over-broad | `test_every_phase_mode_remains_admitted_on_the_same_governed_route[f0]` |
| `M13` | first-canary transport pin removed | `test_the_direct_topology_refuses_through_the_operator_path` |
| `M14` | asserted-UUID gate disabled | `test_c1_cases_3_and_4_a_wrong_or_arbitrary_asserted_uuid_refuses` |
| `M15` | D130 "inside archive" isolation disabled | `test_every_phase_refuses_a_work_root_inside_the_d130_archive[f0]` |
| `M16` | F2 hard floor classified normal | `test_the_hard_floor_is_inclusive_and_raises_the_dedicated_condition` |
| `M17` | F0 blocking-terminal gate disabled | `test_a_failed_predecessor_leaves_no_checkpoint_and_refuses_its_successor` |
| `M18` | a capacity value dropped from the identity fold | `test_the_execution_identity_folds_exactly_the_recorded_inputs` |
| `M19` | orchestrator import added to a phase module | `test_parse_bulk_remains_canary_unreachable_after_the_phase_decomposition` |

`M12` matters as much as `M11`: it proves the `--mode run` refusal is **narrow** rather than merely
present.

**Positive controls** (the review's §32 requirement) were run explicitly and all pass:
`test_the_same_revision_admits_the_whole_sequence`, `test_the_clean_contract_admits_a_clean_tree`,
`test_a_qualified_dock_still_passes_every_phase`,
`test_the_three_phase_sequence_completes_and_writes_one_result_document`,
`test_a_recycled_process_id_is_not_mistaken_for_a_live_predecessor`,
`test_the_qualified_dock_still_passes_the_production_operator_path`,
`test_f2_commits_its_association_rows_when_capacity_holds`, and
`test_every_phase_mode_remains_admitted_on_the_same_governed_route`. Byte-identical restoration:

```text
repository_identity.py    9fd79607f65eceb3f7529fe4ac3b2b70ab4728b3f717e677942f2ce07e6f1ef3
canary_phases.py          53bb84523410fc4fb8c6722c332b0103a53f650e3da5657405d22fe700ac6620
single_source_canary.py   8d6b3b964fd1d38cbe981b812518d73d5fa6a58b4042a7560b01925d457666df
external_working_root.py  90f96a35633438949f7293fe117ef245a294443199b1f9fbce35b17204fe9a01
```

## 15. Validation

Run against the reviewed technical tree, after every falsification mutation had been restored and the
worktree confirmed clean. Nothing was mutated to make a failure pass.

| Gate | Result | Elapsed |
|---|---|---|
| Focused suites: D116, D127, D131, D137, D138, D140, D141, D144, D145, D147, D149, no-network | **567 passed** | 55 s |
| Mutation campaign | **19 mutations, 19 killed, 0 survivors**, all files restored byte-identical | ~15 s |
| Positive controls | **10 passed** | 2 s |
| Live artifact verification | source, structural digest, catalog logical/observation, D130 — **all matched** | ~110 s |
| Live topology / volume / power / lid | **dock present, UUID matched, AC, lid open** | <1 s |
| `make lint` / `make format-check` / `make typecheck` | clean; 204 files formatted; no issues in 98 source files | — |
| `make secrets` / `make hygiene` | 470 files, 0 findings; 472 paths, 0 findings | — |
| `make links` / `make decision-refs` | 225 documents, 0 unallowed broken; 4911 citations, 145 records | — |
| `make validate` / `make cohorts` | 5 cohorts validated, frozen definitions match | — |
| **`make check-fast`** | **exit 0 — 5315 passed, 1 skipped** | **245 s** |

The final `make check-fast` was run once against the reviewed tree even though D149's CI was already
green, because this is the last independent pre-canary review.

## 16. Findings

**0 BLOCKER. 0 MAJOR. 0 MINOR. 0 ACTIONABLE INFORMATIONAL. 0 ACTIONABLE PRE-CANARY LIMITATION.**

One non-actionable nuance is recorded for completeness rather than as a finding: the phase-path
import graph transitively **defines** the `sec.http_client`, `sec.transport` and `m3.acquisition`
modules. This is not a defect and does not weaken the network-bomb property — it constructs no
transport, opens no socket, and is explicitly disclosed and scoped by the accepted test
`test_the_phase_path_imports_no_e0_and_no_transport`. The property that governs authorization (no
request, no transport construction on the canary path, both gates false, `_parse_bulk` unreachable)
was independently verified and holds.

### Accepted residual limitations (§30), each verified to remain within its owner-adjudicated boundary

* **A. `D149-R4` local-checkout-write threat-model limitation** — an `UNCHECKED_HASH` byte-code file
  beneath an ignored `__pycache__` can execute without moving the repository identity. Verified that
  Decision 149 did **not** widen this: ordinary stale-`.pyc` behaviour remains safe (CPython rejects
  a timestamp-invalidated cache), no new ignored-file execution dependency was introduced, and no new
  environment override exists. The canary cannot be subverted **without** write access inside the
  checkout — the identity, transport, UUID and capacity policy are all derived from the module's own
  location or module constants with no operator/flag/env override. Non-actionable.
* **B.** ExFAT has no metadata journal. **C.** No software guarantee against physical surprise
  removal. **D.** The lid must physically stay open. **E.** Real corrected-scale peak RSS is
  observable only during the real run. **F.** Capacity sampling is bounded, not instantaneous.
  **G.** Hardware/dock/cable failure remains physically possible. **H.** `GOVERNED_PAUSE_RESUME` is
  not implemented. **I.** `SAFE_TO_EJECT` is not implemented. **J.** `_parse_bulk` remains a
  pre-network blocker, provably unreachable from this offline canary.

None has broadened beyond its accepted boundary.

## 17. What this record does not authorize

**It authorizes no canary.** A `PASS` verdict on a whole-system review is not permission to run
anything. `CANARY_AUTHORIZED = NO`.

No canary-world construction, no execution namespace, no run identity, no launch receipt, no phase
checkpoint, no complete-source execution, no E0, no pre-E0 catalog transition, no stale-writer-lease
recovery, no migration `0016`, no network activity, no SEC acquisition, no D130 modification or
archive opening, no physical detach, no re-run of the D141 qualification, and no pause/resume
implementation.

**It accepts no record.** Not Decision 149, not Decision 147, and not Decisions 137, 138, 140, 141,
142, 143, 144 or 145. Decision 146's `FAIL` verdict stands for the tree it reviewed, and Decision
143's for its own. Decisions 137 and 138 remain `IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER
ACCEPTANCE`; Decisions 140 and 141 remain accepted **for continuation only**.

**It repairs nothing.** No file under `src/`, `tests/`, `scripts/`, `configs/` or `migrations/` is
changed by this record, and the operator runbook is not corrected by it.

All three activation constants remain `None`, both network switches remain `false`, migration head
remains `0015` with `0016` absent, and a passing preflight still prints `canary_authorized: false`.

## 18. What holds, and the next owner action

Every condition the PASS standard (§35) requires is met: `PHASE_BOUNDARY_RAM_RECLAMATION` implemented
and proved in three real processes; governed `--mode run` refused; the three phases validated to
admission with the two predecessor-death boundaries; same governed world across restarts; genuine
repository identity with fresh successor re-measurement and fail-closed dirty/deleted/renamed
refusal; the dock topology, exact UUID and D130 isolation validated live; source identity, structural
parent census and D129 semantics validated against the real artifact; exact-one-source, network
isolation and operational-catalog nonmutation; the 185/60/55/50 and 20/10 GiB gates with F2 rollback;
watchdog exact-process identity and detached phase persistence; no hidden full-size copy, no stale
long-run timeout, false-success prevention and evidence completeness; a 19-mutation campaign with no
survivor; and `make check-fast` green.

```text
D150_FINAL_FABLE_PRECANARY_REVIEW_PASS

M3_3_D150_FINAL_FABLE_PRECANARY_REVIEW_PASS_READY_FOR_OWNER
```

**Next authorized action: STOP.** Return to GPT-5.6 Sol for D150 owner acceptance and the separate
controlled complete-source canary authorization decision. **Do not start the canary.** Do not mint a
canary authority. Do not pre-create a run id, a canary world, a SQLite temp root, a launch receipt,
or a phase checkpoint. Do not begin F0.
