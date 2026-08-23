# Decision 142 — Pre-Canary Architecture Freeze, First-Canary Topology Selection, and the §28d Runbook Correction

```text
STATUS: PUBLISHED — OWNER RULINGS D142-R1 – D142-R6
RECORD_TYPE: GOVERNANCE PUBLICATION — SELECTION, DEFERRAL, FREEZE, AND ONE DOCUMENTATION CORRECTION
DATE: 2026-08-23
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings D142-R1 – D142-R6
CLASSIFICATION: GOVERNANCE AND DOCUMENTATION ONLY — NO SOURCE CHANGE, NO TEST CHANGE
AUTHORIZATION:
  M3_3_D142_PRECANARY_ARCHITECTURE_FREEZE_AND_RUNBOOK_CORRECTION_AUTHORIZED — spent by the
  publication of this record
ACCEPTED_PREDECESSOR: M3_3_D141_OWNER_ACCEPTED_FOR_CONTINUATION
COMPLETION_TOKEN: M3_3_D142_PRECANARY_ARCHITECTURE_FREEZE_COMPLETE_READY_FOR_OWNER
CANARY_AUTHORIZED: NO
E0_EXECUTION_AUTHORIZATION: NO
SELECTED_FIRST_CANARY_TRANSPORT: USB_VIA_THUNDERBOLT_DOCK
USB_DIRECT: QUALIFIED, NOT REVOKED, NOT SELECTED — NO FALLBACK EITHER WAY
QUALIFIED_VOLUME_UUID: 397A4D4A-9508-391E-814E-3B533C7BD049 — UNCHANGED, STILL PRIMARY IDENTITY
REQUIRE_VOLUME_UUID: MANDATORY — OMISSION IS A REFUSAL (D140-R2)
GOVERNED_PAUSE_RESUME: NOT_IMPLEMENTED — DEFERRED BEYOND THE FIRST CANARY
MIGRATION_HEAD: 0015 — 0016 ABSENT
ALL_THREE_ACTIVATION_CONSTANTS: None
NETWORK: enabled=false, m3_acquire_enabled=false
SOURCE_AND_TEST_CHANGE: NONE
```

## 1. What this record is, and what it is not

It is four owner decisions and one documentation repair, published together because they close the
pre-canary phase as a unit: **Decision 141 is accepted for continuation**, **one topology is
selected for the first complete-source canary**, **governed pause/resume is deferred beyond that
canary**, **the pre-canary architecture is frozen**, and **one false sentence in the operator
runbook is corrected**.

It is **not** a canary, a canary world, an execution namespace, a launch receipt, an E0
authorization, a migration, a network enablement, a pause/resume implementation, or any change to
executable behaviour. **No file under `src/` or `tests/` is touched by this record.** Every guard
the repository ships behaves after this publication exactly as it behaved before it; what changes
is which of two already-qualified configurations the owner has chosen, what the runbook says about
a flag the code already enforces, and whether further pre-canary architecture work is planned.

**Decision 141 asked how the volume is attached. Decision 142 answers the question Decision 141 §16
deliberately left to the owner** — *is the dock the intended canary topology?* — and then stops.

## 2. Entry state

Verified live before any edit, not taken from a document:

| Fact | Value |
|---|---|
| Branch / HEAD | `main` / `1b1517b9428982e6faf8bd0472dc4b6e44047d4d` |
| Tree | `1912a9c8cab53755a3e527ecdd7dfaf434ddfb42` |
| `origin/main` vs HEAD | equal, `0/0` ahead/behind |
| Worktree | clean; nothing staged; no untracked residue (`--untracked-files=all` empty) |
| Tag at HEAD | none |
| Migration head | `0015`; `0016` absent from `src/disclosure_drift/storage/migrations/` |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` — `m3/e0.py:179` |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` — `m3/e0.py:201` |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` — `m3/e0.py:446` |
| `network.enabled` | `false` — `configs/project.yaml:44` |
| `network.m3_acquire_enabled` | `false` — `configs/project.yaml:50` |
| D141 CI | run `32663574416`, head SHA `1b1517b9…`, conclusion **success**; both required jobs **success** |

No material predicate differed from the authorizing packet, so no repair and no reinterpretation
was performed on any of them.

## 3. D142-R1 — Decision 141 is owner accepted for continuation

**[Decision 141](decision_141_m3_3_thunderbolt_dock_qualification.md) is `OWNER ACCEPTED FOR
CONTINUATION`** under `M3_3_D141_OWNER_ACCEPTED_FOR_CONTINUATION`.

The measured and integrated transport class remains exactly:

```text
USB_VIA_THUNDERBOLT_DOCK
```

**The acceptance is of a bounded qualification, and it does not widen it.** Every limitation
Decision 141 §12 states remains intact and is carried forward verbatim in §12 below. Acceptance
for continuation means the record may be relied on as it is written — not that anything it
measured under bounded conditions may be restated as a general property of the hardware.

**Decision 141 is not rewritten by this record**, and neither is Decision 140.

## 4. D142-R2 — the first-canary topology, selected

The **one** topology selected for the first complete-source canary is:

```text
USB_VIA_THUNDERBOLT_DOCK
```

**The selected storage identity is exact and unchanged:**

| Element | Value |
|---|---|
| Volume UUID | `397A4D4A-9508-391E-814E-3B533C7BD049` |
| USB vendor | `0x090C` |
| USB product | `0x2320` |
| USB serial | `SSKPSSD0000000000071` |

**The required dock cascade is ordered and exact:**

```text
0x8087:0x0B40  ->  0x17EF:0x30B6  ->  0x17EF:0x30B8
```

**The physical dock port and profile qualified by Decision 141 must be used.** A different dock
port yields a different cascade, which is a topology this repository has not qualified and which
refuses — Decision 141 §5 and §12 item 3, unchanged.

**A changed BSD disk identifier is not a refusal.** `disk4`, `disk4s2`, or any successor is
attach-time state and is never identity; the exact Volume UUID and the frozen stable
transport/profile identity remain authoritative. Decision 141 §5 (D141-R4, D141-R7) is preserved
in every word.

## 5. D142-R2 continued — the direct path is compatible, and is not selected

`USB_DIRECT` — the topology accepted [Decision 136](decision_136_m3_3_external_ssd_active_volume_qualification.md)
§4 qualified — **remains a separately qualified topology and this record does not revoke it.**
Decision 141 §16 (D141-R8) stands entire.

**It is not selected for the first canary.**

Both facts are true at once and neither weakens the other: the repository continues to recognize
two qualified topologies and to refuse a third, while the owner has selected exactly one of the
two for the first run.

## 6. D142-R2 continued — the no-fallback rule

**There is no automatic fallback and no operator fallback between the two topologies for the
authorized first-canary configuration.**

If the selected dock topology fails or refuses its preflight:

* **STOP.**
* **Do not** switch that same canary to `USB_DIRECT`, silently or manually.
* **Do not** relax the profile, and do not work around the refusal.
* **Return to the owner.**

The correct repair for a transport refusal is restoring the qualified attachment — the same dock,
the same Mac-facing cable in the same Mac port, the same SSD cable in the same dock port. A
refusal is a statement that the physical configuration is not the one that was qualified; it is
never a prompt to select a different qualified configuration mid-run.

## 7. D142-R3 — governed pause/resume is deferred beyond the first canary

**Governed pause/resume is intentionally DEFERRED.** For the first canary:

```text
GOVERNED_PAUSE_RESUME = NOT_IMPLEMENTED
```

There is no `SAFE_TO_EJECT` state, no governed detach, no governed reconnect, no topology switch,
no storage migration, and no pause-and-move workflow.

* **`kill -STOP` is not a governed pause.** Suspending the process does not quiesce SQLite, does
  not close handles, and does not make the volume safe to eject.
* **Closing the lid is not a governed pause.**
* **Qualifying the dock does not create permission to detach it.** Decision 141 §17 already said
  this; this record does not soften it.

The first canary therefore runs under the **existing continuous-attachment operating model**. At
launch, every existing mechanical launch predicate still applies — none is replaced, relaxed, or
substituted by this ruling.

**During operation the operator must not intentionally:** eject the SSD; unplug the SSD; unplug or
reconfigure the dock storage path; move the SSD to another dock port; substitute the direct path;
substitute another volume; or treat a sleeping or stopped process as safely detachable.

**Decision 142 authorizes no pause/resume implementation and no new state machine.** The
architectural finding remains exactly where
[Decision 140](decision_140_m3_3_total_pre_canary_hardening.md) §17 left it, returned for owner
redesign and unresolved.

**This is a deliberate pre-canary architecture freeze, not an assertion that pause/resume would
never be useful later.**

## 8. D142-R3 continued — interruption is not pause

**If continued operation would require any of the actions §7 forbids, the run is INTERRUPTED, not
PAUSED.**

An interrupted run is lost and requires a new run identity; worlds are create-once and are never
resumed (D129-R8). There is no recovery procedure that converts a physical disconnection into a
resumable state, and **no operator procedure pretending to do so may be written** — a documented
recovery that does not exist is worse than an honest statement that none does.

## 9. D142-R4 — the §28d runbook correction

**The defect.** Accepted operator runbook §28d carried a D140-era statement that
`--require-volume-uuid` is **optional**, in two places:

> The `--require-volume-uuid` line is an explicit assertion and is **optional**; dropping it changes
> nothing about which guards run.

> - **omit it on the SSD** → the full envelope still runs, and every guard still refuses;

**Both are FALSE under accepted [Decision 140](decision_140_m3_3_total_pre_canary_hardening.md) §4
(D140-R2)**, which makes the assertion mandatory on every external route — by intent, by residence,
or by assertion — and makes omission the refusal. The second bullet is the same false claim in
different words, so the correction reaches the **meaning** in both places rather than the one
sentence that names the word *optional*.

**This is a documentation defect only.** The shipped code has enforced the mandatory rule since
Decision 140: `require_external_working_root_envelope` refuses with an explicit `D140-R2` message
when an external requirement exists and `asserted_uuid` is `None`, before the volume is consulted.
The runbook described a behaviour the repository does not have.

**The corrected meaning, now published in §28d:**

> `--require-volume-uuid` is **mandatory** for the external-SSD canary envelope. **Omitting it is a
> refusal.** Supplying it does not disable or weaken any other launch guard.

**The exact UUID requirement is preserved.** The assertion must be exactly
`397A4D4A-9508-391E-814E-3B533C7BD049`; any other value is refused before anything is measured
(D138-R12, unchanged), and an assertion supplied for an internal root still refuses. **It is not
weakened into a mount-name check** — `/Volumes/SSK SSD` is whatever volume happens to be mounted
there, and the mount path has never been identity. **It is not made optional through any other CLI,
configuration, or API path**, and no such path is created here.

**Decision 140 is not rewritten to repair this runbook sentence.** D140-R2 was already correct; the
runbook was wrong about it.

## 10. D142-R5 — the pre-canary architecture freeze

**After the publication of this record, no additional pre-canary architecture changes are planned
by the owner.**

The intended next phase is a **FINAL INDEPENDENT PRE-CANARY REVIEW**. That review is **not part of
this session and is not authorized by this record**. It must later be performed from a genuinely
fresh session context, against the exact published Decision 142 commit.

This freeze is what the Decision 141 §19 next-authorized-action was waiting on: it recorded that a
final review should not be commissioned until the owner confirmed no further pre-canary
architecture changes were planned. §10 is that confirmation.

## 11. D142-R6 — what this record does not authorize

**No canary. No canary-world construction. No execution namespace creation. No launch receipt
creation. No complete-source execution. No E0. No migration `0016`. No network activity. No SEC
acquisition. No deletion or modification of [Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md).
No use of a real canary `SQLITE_TMPDIR`. No pause/resume implementation.**

**Any existing `canary_authorized` value remains `false`.** A passing preflight still prints
`canary_authorized: false`, and holding one is not an authorization to launch.

Selecting a topology is not authorizing a run on it. Accepting Decision 141 for continuation is not
accepting Decisions 137, 138 or 140, none of which this record accepts, and is not a canary
authority. The three activation constants remain `None`, both tracked network switches remain
`false`, and migration head remains `0015` with `0016` absent.

## 12. Limitations carried forward, stated rather than smoothed

Carried forward **explicitly and without upgrade**. No bounded Decision 141 observation is restated
here as a general reliability claim, and **no physical evidence beyond Decision 141 is invented**:

1. **`F_FULLFSYNC` returning success is OS-visible only.** It is not proof that the dock, its
   bridge, or the SSD physically honoured a flush.
2. **No physical disconnect or power-loss qualification occurred.** Decision 141 established
   process-crash recovery only, by `SIGKILL`; no surprise removal, no power-loss test, and no
   physical disconnection was performed or is authorized. A matching transport does not prove the
   dock, cables, or enclosure cannot fail.
3. **ExFAT remains non-journaled.** Decision 137 §14 (D137-R11) and Decision 136 §9 (D136-R6) are
   unchanged in every word; nothing here converts them.
4. **The dock qualification is port- and profile-specific.** Moving the SSD to a different dock
   port refuses and requires re-qualification.
5. **macOS-specific mechanisms remain.** `ioreg`, `pmset`, and `diskutil` are the readers, and the
   guards fail closed elsewhere.
6. **No complete-source runtime has yet been measured.** Nothing in Decision 141 or in this record
   extrapolates one, and no bounded I/O reading is a rehearsal of one.
7. **Pause/resume remains unimplemented**, per §7 above.
8. **The Decision 140 §18 residual limitations are carried unchanged**, including unmeasured
   `SQLITE_TMPDIR` peak spill, unmeasured full-scale peak RSS, `8` GB of host RAM, and the
   requirement that the lid physically remain open.
9. **Host battery health is degraded** — `73%` maximum capacity, `859` cycles, macOS reporting
   `Check Battery`. This makes the AC requirement more important, not less, and is not a
   mitigation.
10. **`CensusOrchestrator._parse_bulk` remains an open pre-network blocker, deliberately
    unrepaired**, and its repair must not be performed as a side effect of unrelated work.

## 13. What did not change

The Volume UUID and every capacity floor; the transport profile and its classification rule; the
D131 parser and runtime semantics; the D130 archive; migration head `0015`; all three activation
constants at `None`; both network switches at `false`; the width of the D136-R8 one-canary
exception; `cli.py` and every other file under `src/`; every file under `tests/`; and
`GOVERNED_PAUSE_RESUME = NOT_IMPLEMENTED`.

## 14. The next-stage boundary

**STOP.** Return this publication report to the owner.

The next phase is one final independent pre-canary review, performed from a genuinely fresh
session context against the exact published Decision 142 commit. **That review is not authorized by
this record**, must not be performed in the session that published it, and does not itself
authorize a canary. A canary authority remains a separate owner instrument that has not been
issued.

## 15. Result

```text
M3_3_D142_PRECANARY_ARCHITECTURE_FREEZE_COMPLETE_READY_FOR_OWNER
```
