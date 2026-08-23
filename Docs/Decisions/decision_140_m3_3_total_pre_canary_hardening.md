# Decision 140 — Total Pre-Canary Hardening

```text
STATUS: IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER ACCEPTANCE
RECORD_TYPE: CLOSURE OF EVERY ACTIONABLE FINDING THE ACCEPTED D139 INDEPENDENT REVIEW RAISED —
  ZERO BLOCKERS, TWO MAJORS, SEVEN MINORS, TEN INFORMATIONAL
DATE: 2026-08-23
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings D140-R1 – D140-R23
CLASSIFICATION: BOUNDED CORRECTION AND HARDENING — NOT A REDESIGN OF DECISIONS 137 OR 138
REVIEW_VERDICT_ACCEPTED: D139_FABLE_REVIEW_CORRECTION_REQUIRED — 0 BLOCKER / 2 MAJOR / 7 MINOR /
  10 INFORMATIONAL
REVIEW_ACCEPTANCE: M3_3_D139_FABLE_REVIEW_FINDINGS_OWNER_ACCEPTED
CORRECTION_AUTHORIZATION:
  M3_3_D140_TOTAL_PRE_CANARY_HARDENING_AUTHORIZED — issued outside this repository and now spent
PRIOR_CANARY_AUTHORITY: M3_3_D139_PRIOR_CANARY_AUTHORIZATION_SUPERSEDED_AND_WITHDRAWN
ACCEPTANCE_TOKEN: NONE — THIS RECORD CLAIMS NO OWNER ACCEPTANCE
COMPLETION_TOKEN: M3_3_D140_TOTAL_PRE_CANARY_HARDENING_COMPLETE_READY_FOR_FABLE_REVIEW
CANARY_AUTHORIZED: NO
E0_EXECUTION_AUTHORIZATION: NO
QUALIFIED_VOLUME_UUID: 397A4D4A-9508-391E-814E-3B533C7BD049 — MANDATORY, NOT OPTIONAL
EXTERNAL_INTENT_RULE: A /Volumes PATH IS AN EXTERNAL INTENT WHETHER OR NOT ANYTHING IS MOUNTED
LAUNCH_FLOOR: 185 GiB — 198,642,237,440 BYTES — UNCHANGED
POST_F0_FLOOR: 60 GiB — 64,424,509,440 BYTES — UNCHANGED
PRE_F1_FLOOR: 55 GiB — 59,055,800,320 BYTES — UNCHANGED
PRE_F2_FLOOR: 50 GiB — 53,687,091,200 BYTES — UNCHANGED
DURING_F2_ALERT: 20 GiB — UNCHANGED. DURING_F2_HARD_FLOOR: 10 GiB — UNCHANGED
CAPACITY_COVERAGE: F0 PER PART, F0 FINALIZATION, F1 PER ACCESSION, F2 BOTH TRAVERSALS, F2 TAIL
TEMP_MEASUREMENT: temp_bytes IS ALWAYS null — UNMEASURED_UNLINKED_SQLITE_TEMP
EXECUTION_LOCK: ONE PER HOST, RUN-ID INDEPENDENT, fcntl.flock, INTERNAL PATH
STRUCTURAL_PREFLIGHT: RUN ON THE REAL SOURCE — 985,834 MEMBERS / 5,337 SHARDS / PARENT MAP SOUND
FOCUSED_BASELINE_BEFORE: 270 PASSED
FULL_SUITE_AFTER: 5107 PASSED, 1 PRE-EXISTING SKIPPED, 0 FAILED
FALSIFICATION: 22 REVERSIBLE MUTATIONS, ALL 22 KILLED, EVERY FILE RESTORED BYTE-IDENTICAL
LIVE_PREFLIGHT: RUN — READ-ONLY, NOTHING CREATED, WRITTEN OR DELETED ON THE VOLUME
GOVERNED_PAUSE_RESUME: NOT IMPLEMENTED —
  D140_PAUSE_RESUME_ARCHITECTURE_REQUIRES_OWNER_REDESIGN (§17)
MIGRATION_HEAD: 0015 — 0016 ABSENT, UNAPPLIED, NOT AUTHORIZED
ACTIVATION_CONSTANTS: ALL THREE REMAIN None
NETWORK_AUTHORIZATION: NONE — REQUEST CEILING 0
PRE_NETWORK_BLOCKER: CensusOrchestrator._parse_bulk — OPEN, DELIBERATELY UNREPAIRED
NEXT_STAGE: ONE FRESH INDEPENDENT REREVIEW REQUIRING 0 BLOCKER / 0 MAJOR / 0 MINOR / 0 ACTIONABLE
  INFORMATIONAL, THEN AN OWNER DECISION ON WHETHER TO ISSUE A CANARY AUTHORITY
```

Decision 138 corrected what the D137 review found. The **D139** review then asked a harder question
of the corrected surface — *what does it do when the volume is not there?* — and the answer was
worse than the question. This record closes every actionable finding it raised.

**The owner chose a stronger correction than the review's minimum.** MAJOR-1 could have been closed
by editing the runbook. It is closed in production code instead.

## 1. What this record is, and what it is not

It **is** the closure of the D139 findings, the tests that kill each closure, and the evidence from
one live read-only preflight and one real structural census.

It is **not** an acceptance of Decision 137, 138 or itself; not a canary authorization — the prior
one is **superseded and withdrawn**; not an E0 authorization; not a migration; not a change to any
research definition, parser version, or D131 semantic; and not a redesign of anything.

## 2. Entry state

Branch `main`, HEAD `4fda557bca272965b89bc27cd6d88b2df7646350`, tree
`bf710df3de61cb22ad2108fcd1a1319e1935b3d4`, `origin/main == HEAD`, ahead/behind `0/0`, clean tree,
nothing staged, no untracked files, no tag at HEAD. Latest governance **Decision 138**. Migration
head `0015`, `0016` absent. All three activation constants `None`. `network.enabled=false`,
`network.m3_acquire_enabled=false`. No corrected complete-source canary world exists.

**One environmental fact is recorded rather than smoothed.** At session entry `/Volumes` held only
the `Macintosh HD` symlink and `diskutil list external` reported nothing: **the qualified SSD was
not attached.** It was attached partway through the session and every live check in §16 ran against
it. Both states are reported because both were real, and because the absent state is precisely the
condition MAJOR-1 is about.

## 3. The accepted verdict, and the owner's adjudication

`D139_FABLE_REVIEW_CORRECTION_REQUIRED` — **0 blocker, 2 major, 7 minor, 10 informational**, all
accepted, all authorized for correction. The owner made one **upgrade**: the blocking-F0
progression defect (the review's MINOR-2) is treated as **canary-critical**, because a canary that
reports success after a failed parse is the single most consequential way this instrument could
mislead.

## 4. MAJOR-1 — the absent and stale mount can no longer reach an internal fallback

**What was wrong.** Decision 138 decided *external or internal* by asking which device the resolved
root sits on, measured on its **nearest existing ancestor**. That question has a wrong answer
whenever the volume is not there. With the SSD unplugged, `/Volumes/SSK SSD/world` has nearest
existing ancestor `/Volumes`; with an ordinary directory left at the mount point, it has the
directory itself. Both are on internal storage, both classify **internal**, and an internal root
with no assertion returns `None` — **no guard runs at all**. The stale-directory case is worse than
the absent one, because the directory is writable and a complete run lands on the internal disk.

**What is now true** (`src/disclosure_drift/m3/external_working_root.py`):

| Rule | Correction |
|---|---|
| **D140-R1** | `external_volume_intent()` reads intent from the **name**. A path under `/Volumes/<name>/` is an external-volume intent whether or not anything is mounted there, and **an intent never degrades to internal**. |
| **D140-R2** | `--require-volume-uuid` is **mandatory** on every external route — by intent, by residence, or by assertion. Omission is the refusal. It must be `397A4D4A-9508-391E-814E-3B533C7BD049`; an arbitrary UUID is refused before anything is measured (D138-R12, preserved). |
| **D140-R3** | `require_mounted_volume_directory()` requires the `/Volumes/<name>` directory to **exist**, to be **currently a mount point**, and to report **exactly** the accepted UUID — and `require_mounted_qualified_volume()` then requires the work root to resolve **onto that volume**. The mount-point predicate is what kills the writable stale directory. `diskutil` is not consulted for a path with nothing mounted at it. |
| **D140-R4** | The volume is **re-authenticated at the last safe point before `mkdir`**, so the gap between *the envelope held* and *the world exists* carries a check rather than an assumption. |
| **D140-R5** | `create_world(..., require_existing_root=True)` on every external run. **No parent is created.** The accepted `mkdir(parents=True)` would have **recreated the mount point** as an ordinary directory on the internal disk and built the world inside it; only `/Volumes` being root-owned stood in the way, which is a permission accident and not a guard. |
| **D140-R15** | `AdmittedVolume` pins the mount point and the **device number** at admission. Every later reading re-establishes both first. |

**Preserved unchanged:** an internal root with no assertion returns `None` and is byte-for-byte the
accepted Decision 116 path; an internal root with the external UUID still refuses at the identity
guard; archive exclusion remains unconditional and byte-unchanged.

## 5. MAJOR-2 — one canonical durable launch envelope

Runbook **§28e** is now the single canonical command, and every other launch snippet is marked
superseded in place. `scripts/m3/canary_launch.py` enforces what the shape assumes.

| Component | Finding closed |
|---|---|
| `tmux -e SQLITE_TMPDIR=…` | An **exported** value reaches a pane only when tmux starts a **new server**. Attaching to a running one gives that server's environment, so SQLite spills to the internal volume for thirty hours while the operator's shell shows the right value. `--require-sqlite-tmpdir` turns that silent misconfiguration into a first-second refusal. |
| Durable stdout / stderr | `dup2` **before `exec`**, so the exec'd image inherits the descriptors. No required failure diagnosis lives only in a pane's scrollback. |
| `caffeinate -dims` | Assertions held for the child's whole lifetime, proved by `pmset -g assertions` while a child runs. **It does not prevent lid-close sleep**, and this record does not claim it does. |
| `/usr/bin/time -l -o` | Peak resident set size, captured durably — closing **INFO-4**. It is not a threshold, and the obsolete D115 `2.5` GiB acceptance is not revived. |
| Internal pid record | **D140-R10.** Never derived from `WORK_ROOT`, never on the SSD, never under D130. |

`caffeinate` and `time` are **ancestors** of the canary, not things the launcher `exec`s: if the
launcher `exec`'d `caffeinate`, the pid file would name `caffeinate` and the stop path would signal
a process that is not the canary — D128's defect by another route.

## 6. MINOR-1 — the temporary/spill measurement is truthful (D140-R7)

SQLite creates `etilqs_*` and **unlinks them immediately**, so a directory walk returns zero *while
a spill is in progress*. Decision 137 recorded that zero as `temp_bytes`.

`temp_bytes` is now **always `null`**, beside `temp_measurement_status:
UNMEASURED_UNLINKED_SQLITE_TEMP`. The visible-file walk survives under the truthful name
`temp_visible_bytes`. **Filesystem free space remains the authoritative capacity signal**, and it
already counts allocated unlinked blocks.

## 7. MINOR-2 — a blocking F0 stops the run (D140-R12, owner-upgraded)

`require_f0_success()` sits between F0's return and anything that reads its output. On a blocking
terminal — `parser_state_after == "failed"`, or disposition
`E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE` — **F1 runs zero times, F2 runs zero times, no result
document is written, the operator exit is a gate failure, the world is left exactly as it is, and
nothing is retried or cleaned.** The blocking set is read from the **existing** accepted terminals;
`quarantined` is deliberately absent, because the accepted rules already permit a quarantined parse
to proceed and D140 widens nothing.

## 8. MINOR-3 — the vacuous post-F0 test (D140-R13)

The accepted test read:

```python
calls: list[str] = []
with pytest.raises(...):
    calls, _ = _gated_run(...)     # raises — the assignment NEVER executes
assert calls == []                 # re-asserts the literal two lines above
```

It passed identically whether F1 ran once, never, or a thousand times. The harness now takes a
caller-owned counter that survives the exception. It is **strengthened, not deleted**, and the
falsification run in §15 kills it by deliberately invoking F1.

## 9. MINOR-4, MINOR-5, MINOR-6, MINOR-7

* **MINOR-4 (D140-R10).** `require_internal_runtime_path()` refuses a pid, log, status or resource
  path inside the work root or the D130 archive, on resolved case-folded components so `..`, a
  symlink and a case variant cannot launder it. The launcher enforces the same rule at the process
  boundary and refuses with `LAUNCH_REFUSED_RUNTIME_PATH_NOT_INTERNAL` **before creating anything**.
* **MINOR-5 (D140-R11).** An invalid `SQLITE_TMPDIR` now says the **temporary root** is wrong.
  Decision 137 said *"the selected working root is on volume …"* while rejecting a different path
  entirely. No private path is printed.
* **MINOR-6 (D140-R16).** One host-level `fcntl.flock` at a fixed internal path, **independent of
  `run_id`**, taken before anything is measured or created and held for the whole run. Two
  concurrent canaries would each measure the same volume's free space as though alone on it, making
  every floor wrong in the one direction that matters. Stale metadata in the file cannot block —
  only a **held** `flock` does — and the kernel releases it on process death. It is **not** a second
  writer-lease architecture: it holds no state, adopts nothing, recovers nothing, grants nothing. It
  binds in `run_single_source_canary`, so every production route is covered rather than the CLI.
* **MINOR-7 (D140-R20).** `preauthenticate_source()` runs **before `create_world`**: byte length and
  SHA-256 against the plan-bound observation, and — when the digest is the governed artifact's —
  the frozen byte length, member count and shard count. A mismatch now costs nothing; discovered
  during F0 it cost a create-once run identity. **F0's own verification is not weakened**: the
  parser re-reads and re-verifies through the same integrity-checking reader, deliberately not
  skipped because a first check passed.

## 10. INFO-1 / INFO-2 — the long unsampled windows are closed (D140-R14)

Between `PRE_LAUNCH` and `POST_F0` the accepted run took **no capacity reading at all**, across
roughly 985,000 parts and the great majority of a thirty-hour run. F1 was the same.

`capacity_guard` is now threaded into F0's **per-part** boundary and its finalization block, F1's
**per-accession** boundary, and around F2's totality tail — which cannot be sampled internally,
because nothing can be sampled inside one aggregate SQL statement, so it is bracketed instead. The
guard decides for itself whether enough wall-clock time has elapsed, so a per-unit call stays
affordable; the accepted 5 s cadence and 60 s ceiling are unchanged, `diskutil` is **not** run at
that cadence, and the 20 GiB alert and 10 GiB hard-stop semantics are untouched. Each transactional
stage keeps its rollback semantics, and a batch-boundary failure cannot fabricate completion.

## 11. INFO-3 — volume disappearance during the run (D140-R15)

**Free space measured after the volume has gone describes the internal disk, and the internal disk
always looks healthy.** Every sample now re-establishes identity *before* any free-space number is
trusted: the cheap check (containment plus pinned `st_dev`) runs at the sampling cadence, and the
exact `diskutil` UUID re-read runs on a bounded 300 s interval. A vanished root, a failed `stat`, an
escape from the mount point, or a changed device identity raises
`F2_VOLUME_IDENTITY_LOST` — fail-closed, through the same rollback-safe abort path, with
`free_bytes: null` rather than an internal reading.

## 12. INFO-5, INFO-6, INFO-7, INFO-8

* **INFO-5 (D140-R17).** Alert evidence is bounded in **memory**, not merely in cadence: the first
  entry is always recorded, then at most one per 60 s, capped at 240 retained records, with
  `alert_count`, `first_alert` and `latest_alert` kept exactly. Safety sampling is unchanged and the
  hard stop still fires immediately at a sample. A 21,600-sample thirty-hour simulation retains ≤ 240.
* **INFO-6 (D140-R18).** `stop-canary` reads the exact PID from the canonical record and **scans
  nothing**. Authentication requires `argv[0]` to be a canary executable, the `m3 canary-source`
  tokens to be adjacent, and `--run-id` to be exactly this run. A shell that has merely *typed* the
  canary's command carries the substring the accepted `--expect-command` matched; it is refused on
  `argv[0]` whatever the rest of its command line says — proved live in §16. One `SIGINT`, bounded
  wait, **no escalation**. The generic `stop` remains, explicitly outside the governed path.
* **INFO-7 (D140-R19) — `RESOLVED_BY_RECOVERY_CONTROL`.** A late failure can leave a ~120 GiB world
  behind, and 185 GiB is then not available for a fresh attempt without reclaiming it. **That
  physical fact is not removed and is not claimed to be.** What is removed is the ambiguity:
  `failed_world_reclaim_readiness()` reports the run identity, whether a normal success result
  exists, world/database/WAL sizes, the durable runtime evidence, and `FAILED_WORLD_RECLAIM_READY` —
  naming **only** the exact world for that exact run as eligible, never the work root, a sibling
  world, the D130 archive, or the source. **It deletes nothing and authorizes nothing.** A world
  carrying a success result is never reclaim-ready.
* **INFO-8 (D140-R20) — `RESOLVED_BY_CONTROL`.** `caffeinate` cannot defeat lid-close sleep, and
  nothing in software can. Resolved as an explicit launch condition with a real bounded preflight:
  `pmset -g ps` for AC power and `ioreg -k AppleClamshellState` for the lid. Battery refuses; a
  closed lid refuses; an **unreadable** state refuses unless the operator explicitly asserts the
  conditions. Both readings are available on this host (§16).

## 13. INFO-9 / INFO-10 — the shard-to-parent structure is proved before F0 (D140-R21)

The highest-value hardening in this record. The D129 parent rule binds every historical shard to the
registrant its primary document **explicitly declares** under `filings.files`, and that binding is
resolved during F0 — roughly twenty-seven hours into a complete-source run, with a ~120 GiB world
already built.

`structural_source_preflight()` asks the same question first, from the archive alone, read-only. It
traverses once with the **same filters F0 uses** (`name_suffix=".json"`, the same shard predicate),
folds each primary document's explicit declarations into the parent map, observes shard-before-parent
ordering, and then resolves every governed shard through **`_resolve_shard_parent` itself** — the
accepted function, not a copy. **No competing parent algorithm is introduced, and the filename
remains corroboration and never a binding.** It populates no SQLite, creates no world, and runs no F0.
`require_sound_parent_map()` refuses on any orphan, duplicate or conflicting binding.

## 14. Change set

| Path | Purpose |
|---|---|
| `src/disclosure_drift/m3/external_working_root.py` | MAJOR-1 intent rule, mandatory UUID, mount-point authentication, `AdmittedVolume` pinning, MINOR-1 temp truthfulness, MINOR-5 error text, INFO-3 identity guard, INFO-5 bounded alerts |
| `src/disclosure_drift/m3/canary_runtime.py` | **New.** Internal runtime directory, host execution lock, exact-PID authentication, power/lid preflight, reclaim readiness |
| `src/disclosure_drift/m3/single_source_canary.py` | Pre-`mkdir` re-authentication, `require_existing_root`, MINOR-2 blocking-F0 gate, MINOR-7 pre-world source authentication, execution-lock binding, guard threading |
| `src/disclosure_drift/m3/offline_parse.py` | Structural source preflight, `planned_source_observation`, F2 tail bracketing, F0 guard threading |
| `src/disclosure_drift/sec/census.py` | `capacity_guard` at F0's per-part and finalization boundaries and F1's per-accession boundary |
| `scripts/m3/canary_launch.py` | Runtime-path refusal, `--require-sqlite-tmpdir`, durable stdout/stderr, canonical shape |
| `scripts/m3/canary_watchdog.py` | `stop-canary` governed exact-PID stop path |
| `tests/unit/test_d140_total_pre_canary_hardening.py` | **New.** The falsification matrix |
| `tests/unit/test_d137_external_working_root.py`, `tests/unit/test_d138_safety_envelope_correction.py` | Updated to the corrected semantics — strengthened, never weakened |
| `Docs/m3/operator_runbook.md` | §28e canonical command; §28b/§28d marked superseded |

## 15. Validation

* **Focused baseline before any edit:** `270` passed (`19.98` s).
* **Full suite after:** **`5107` passed, `1` pre-existing skipped, `0` failed** in `245.00` s —
  exactly `+75` over the D139 baseline of `5033` collected / `5032` passed / `1` skipped, which is
  the new D140 file exactly.
* **Falsification:** **22 reversible source mutations, all 22 killed by named tests**, every mutated
  file verified byte-identical by SHA-256 afterwards. **No source-mutating framework was used.**
* **One test weakness was found by falsification rather than by design and is recorded.** The
  INFO-1 sampling test first asserted only that *a* reading happened before `POST_F0`, which is
  satisfied by the two fixed readings bracketing F0's finalization — so it **survived deleting the
  per-part call entirely**, the one thing INFO-1 is about. It now asserts that the reading count
  **scales with the number of parts**, and it dies.
* Ruff and `ruff format --check` clean; mypy strict clean over `src`.

**A CI failure on the first push, recorded rather than tidied away.** `make check-fast` is green on
macOS, and the first push of this record was nevertheless **red**: CI run `32658404416` failed its
required SEC-enabled job with `1 failed, 5105 passed, 2 skipped`. The single failure was
`test_m2_the_resource_report_is_captured_durably`, which invoked `/usr/bin/time -l` — a **BSD**
flag that GNU `time` on a Linux runner rejects with exit `125`. **The defect was in the test, not
in production code**: nothing under `src/` invokes `/usr/bin/time`, and the flag lives in the
runbook's canonical command, which is macOS-operator-only in every other respect too
(`caffeinate`, `diskutil`, `pmset`, `ioreg`).

The repair follows the [Decision 133](decision_133_m3_3_watchdog_linux_portability_repair.md)
precedent exactly: **guard on the capability, never delete the coverage and never hard-code
`sys.platform`.** A probe runs `/usr/bin/time -l` once at import and the test skips where the flag
is unsupported. The guard is itself proved — forcing the capability off makes the test **skip**
rather than pass vacuously or fail. The tmux and `caffeinate` tests already carried such guards,
which is why they skipped cleanly on the runner and account for the second of the two skips.

**This is recorded because a green local gate is not a green CI, and a record that implied
otherwise would be false.** The corrected state is the second commit on this record.

## 16. The live read-only preflight and the real structural census

Run against the genuinely mounted qualified volume. **Nothing was created, written, deleted or
benchmarked on it, and no canary world exists.**

| Check | Result |
|---|---|
| Volume UUID | `397A4D4A-9508-391E-814E-3B533C7BD049` — **exact match** |
| Filesystem / device / mount | ExFAT, `disk4s2`, `/Volumes/SSK SSD`, a real mount point |
| D130 archive | **24 entries, no differences**, `0.002` s; the `103,966,696,960`-byte tar `stat`-ed and **never opened** |
| Free space | `310,498,426,880` B = `289.1742` GiB — clears 185 / 60 / 55 GiB |
| Power / lid | `on_ac_power: true`, `clamshell_closed: false` — both readable |
| Source artifact | `1,556,847,020` B and SHA-256 `c85744be…82b82f`, both **exact**, in `1.323` s |
| **Structural census** | **`985,834` governed members, `5,337` shards, `5,337` declared, `0` orphan, `0` duplicate-parent, `0` conflicting-parent, parent map SOUND, shard-before-parent TRUE**, digest `e58b910022aca9c88a2833e50f84efbf0719a86d11c09a5ab99c9e530a7f17eb`, in **`108.432` s** |

**Five live refusal controls, all refused, nothing created:** external root with the UUID omitted;
an arbitrary asserted UUID; a D130 archive child with the correct UUID; the volume root itself; and
the correct UUID with `SQLITE_TMPDIR` unset. An internal root with no flag returned `None`. The work
root was not created, the archive child was not created, and the archive still holds 24 entries.
A live decoy — a process whose command line contains `m3 canary-source --run-id d140` — was
**refused and not signalled**, and remained alive.

**A measurement condition, published rather than smoothed.** Free space reads `310,498,426,880` B
here against D138's `310,498,951,168` B — `524,288` B lower. Nothing in this session wrote to the
volume; the difference is ExFAT free-space accounting across a remount. **All floors clear under
either reading, so the conclusion is identical.**

## 17. Governed pause/resume — `D140_PAUSE_RESUME_ARCHITECTURE_REQUIRES_OWNER_REDESIGN`

The owner amended this decision to require a governed quiescent pause and deterministic resume
(A1), process-RAM release on pause (A1-R22), and mandatory phase-boundary process recycling
(A1-R23). **A1-R20 requires a stop, rather than a compromised implementation, if exact
deterministic F0/F1 resume would need any of a named set of changes. Inspection shows it does.**

**What blocks mid-F0 resume**, each independently sufficient:

1. **`persist_streamed` short-circuits on an existing `parser_run_id`.** That short-circuit *is* the
   create-once guarantee for a parser run. Making it continue a partially written run weakens a
   create-once guarantee — an A1-R20 stop trigger.
2. **`_StreamedRunAccumulator` applies duplicate identities and historical references at the end of
   the run.** On resume the pre-pause contributions are gone. It is bounded and could be
   serialized, but it has **no durable home** at migration head `0015`, and creating one is
   migration `0016` — an A1-R20 stop trigger.
3. **The sidecar and the batch transaction are written to different places.** A pause between a
   committed batch and its sidecar member rows leaves a skew that no existing protocol reconciles;
   resuming across it would double-count or mis-hash. Closing that needs a three-way
   cursor/DB/sidecar consistency protocol that does not exist.

**What is NOT blocked, and is offered as the smallest technically sound architecture** A1-R20 asks
for. The load-bearing fact is favourable and was verified: the source completeness digest absorbs
**only** `("member-digest", record_count, member_digest)` per member — not raw records — and the
sidecar durably stores exactly those per member in ordinal order. **F0's evidence is therefore
exactly reconstructible from durable state without re-parsing.** Given that:

* **F0 → F1 boundary recycle (A1-R23.1) is sound.** F0 is complete, `persist_streamed` already
  short-circuits correctly, and `CompactSourceEvidence` can be replayed from the sidecar. It needs
  no schema change, no create-once weakening, and no parser-semantics change.
* **F1 → F2 boundary recycle (A1-R23.2) is sound.** F1 is idempotent — `INSERT … ON CONFLICT … DO
  UPDATE` plus a plain `UPDATE` — so it is re-runnable from scratch.
* **Mid-F1 pause is sound** by the same rollback-and-re-run shape A1-R6 already accepts for F2.
* **Mid/pre-F2 pause is sound**: F2 is one transaction and is documented re-enterable.

**Why none of it is implemented here.** A pause subsystem that silently does not work during F0 —
the ~27-hour phase, and the phase in which an operator is overwhelmingly most likely to want a
pause — is exactly the "fake or best-effort resume" A1-R20 forbids. The sound subset is a **new
subsystem** requiring its own review, not a bounded correction of a D139 finding. It is returned for
owner redesign.

**Consequences now recorded in the runbook §28e:** there is no `SAFE_TO_EJECT` state, `kill -STOP`
is **not** a governed pause and does not make the volume safe to eject, and the SSD must not be
disconnected while a canary runs.

Accordingly: `GOVERNED_PAUSE_RESUME = NOT_IMPLEMENTED`, and `SAFE_TO_EJECT_PROOF`,
`SAME_RUN_RESUME`, `F2_ROLLBACK_RESUME`, `PAUSE_RESUME_DETERMINISM` and
`PAUSE_RELEASES_PROCESS_RAM` are **NOT ASSERTED** rather than claimed.

## 18. Limitations, stated rather than smoothed

1. `macos_volume_identity` is macOS-only and fails closed elsewhere.
2. The residence classifier is a mount-point test, not a device-class test: a disk image or network
   mount classifies external and must then authenticate as the D136 volume. Fail-closed, but a
   broader net than "USB disk".
3. `DURING_F2` sampling is bounded, not instantaneous: free space can fall below a floor and be
   observed up to one interval later. The 20 GiB alert band sits above the floor for that reason.
4. The exact-UUID re-read during F2 runs on a 300 s interval; between re-reads a swap that preserved
   the device number would be invisible. The cheap check catches every disappearance and every
   replacement that changes it.
5. **`SQLITE_TMPDIR` peak spill remains unmeasured** — D136-R5 unchanged. D140 makes the *reporting*
   truthful (§6); it does not make the quantity measurable.
6. **No live end-to-end rehearsal was performed**, because that would require creating a world on the
   volume. The accepting path is proved synthetically and by live refusals.
7. **Full-scale peak RSS cannot be measured until a real run.** The launcher captures it; the number
   does not exist yet.
8. **The lid must physically remain open.** ExFAT still has no journal, and D136-R6's
   process-crash-recovery-only boundary is unchanged in every word.
9. A failed late world still cannot be disposed of without its own owner authorization (§12).

## 19. What did not change

D129/D131 shard semantics and parser versions `submissions-json/1.2` and
`submissions-historical/1.1`; archive isolation and D130 immutability; the 185 / 60 / 55 / 50 GiB
floors and the 20 / 10 GiB bands; F2 rollback and measurement-failure rollback; exact-one-source
behaviour; `mode=ro` on the operational catalog; zero network construction or use; the absence of
any runtime ceiling; WAL/FULL/cache settings; **no `mmap`**; **no relaxed checkpoint**; create-once
worlds; and no automatic retry. `CensusOrchestrator._parse_bulk` **remains an open pre-network
blocker, deliberately unrepaired**.

## 20. What this record does not authorize — D140-R23

No canary. No canary world, run identity, execution namespace, launch receipt or terminal state. No
E0, E1, E2. No SEC or network access. No migration `0016`. No D130 modification and no large-tar
read. No destructive cleanup and no failed-world deletion. No operational-catalog write. **The
prior canary authorization is superseded and withdrawn, and this record issues no replacement.**

## 21. The next authorized action

One fresh independent rereview of the D140 corrected target, requiring **0 blocker / 0 major /
0 minor / 0 actionable informational**, followed by an owner decision on whether to issue a canary
authority — and, separately, on the §17 pause/resume redesign.
