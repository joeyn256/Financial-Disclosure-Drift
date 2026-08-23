# Decision 141 — ThinkPad Thunderbolt Dock Qualification and Pre-Canary Transport Integration

```text
STATUS: IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER ACCEPTANCE
RECORD_TYPE: HARDWARE-TRANSPORT QUALIFICATION AND MINIMAL INTEGRATION
DATE: 2026-08-23
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings D141-R1 – D141-R12
CLASSIFICATION: BOUNDED QUALIFICATION AND INTEGRATION — NOT A REDESIGN OF DECISIONS 136–140
ENTRY_BASELINE: M3_3_D140_CORRECTED_PUBLICATION_BASELINE_OWNER_ACCEPTED_FOR_CONTINUATION
AUTHORIZATION:
  M3_3_D141_THUNDERBOLT_DOCK_QUALIFICATION_AND_INTEGRATION_AUTHORIZED — issued outside this
  repository and now spent
ACCEPTANCE_TOKEN: NONE — THIS RECORD CLAIMS NO OWNER ACCEPTANCE
COMPLETION_TOKEN: M3_3_D141_THUNDERBOLT_DOCK_QUALIFICATION_COMPLETE_READY_FOR_OWNER
CANARY_AUTHORIZED: NO
E0_EXECUTION_AUTHORIZATION: NO
QUALIFIED_VOLUME_UUID: 397A4D4A-9508-391E-814E-3B533C7BD049 — UNCHANGED, STILL PRIMARY IDENTITY
DOCK_TRANSPORT_CLASS: USB_VIA_THUNDERBOLT_DOCK
DOCK_IDENTITY: ThinkPad Thunderbolt 4 Dock — Lenovo 0x17EF:0x30B3, firmware 38.6, USB4 mode
DOCK_LINK: Thunderbolt/USB4 Bus 1, upstream connected at 40 Gb/s
STORAGE_ATTACHMENT: USB mass storage, three dock hub tiers, 0x090C:0x2320
GOVERNED_PAUSE_RESUME: NOT_IMPLEMENTED — UNCHANGED BY THIS RECORD
MIGRATION_HEAD: 0015 — 0016 ABSENT
ALL_THREE_ACTIVATION_CONSTANTS: None
NETWORK: enabled=false, m3_acquire_enabled=false
D130_ARCHIVE: UNCHANGED — 24 ENTRIES, COMPACT PROOFS IDENTICAL, TAR NEVER OPENED
```

## 1. What this record is, and what it is not

It is the qualification of **how** the accepted external volume is attached, and the minimal
integration of that qualification into the pre-canary system.

It is **not** a canary, a canary world, an E0 authorization, a migration, a change to the D131
parser, an adoption of any D134 candidate, a widening of the D136-R8 one-canary exception, or an
implementation of governed pause/resume. It **authorizes nothing**, and the corrected
complete-source canary remains unauthorized exactly as accepted Decision 140 left it.

Decision 136 qualified **which** volume. Decisions 137, 138 and 140 built the fail-closed
envelope **around** that volume. None of them asked what sits on the wire between the host and
the disk — and the operator runbook filled that gap with a sentence that turned out to be false.

## 2. Entry state

Verified live, not taken from a document:

| Fact | Value |
|---|---|
| Branch / HEAD | `main` / `cf9cd34c01e2ede295d562c8eb9f56344247b021` |
| Tree | `e92673586c0bf3e07c07d39910c6e32eccd21744` |
| `origin/main` vs HEAD | equal, `0/0` ahead/behind, worktree clean, no tag |
| Migration head | `0015`; `0016` absent |
| Activation constants | all three `None` |
| Network | `enabled=false`, `m3_acquire_enabled=false` |
| D140 CI | run `32659453128` — both required jobs **success** |
| Focused baseline | `206` passed in `5.06` s |

## 3. The governing finding — the runbook asserted a topology that was not true

Accepted runbook §28e condition 3 read, verbatim:

> | 3 | The SSD is **directly connected** — no hub | D136 established process-crash recovery only. |

The operator's actual topology, measured rather than assumed, is **three USB hub tiers deep
inside a ThinkPad Thunderbolt 4 Dock**. The condition was not merely unenforced; it was false.

**A second, independent finding.** `require_launch_power_conditions` — the AC-power and lid
guard accepted Decision 140 wrote under D140-R20 — was fully implemented, fully unit-tested, and
named by that same runbook table as *"Checked at launch by `pmset -g ps`"*. **No production path
called it.** The guard existed and was unreachable. The Decision 141 authorization requires
the corrected canary to require AC power and lid state, so this record puts it on the launch
path.

## 4. D141-R1 — the topology, discovered rather than inferred

The dock's commercial name was misleading twice over, and neither assumption survived
measurement. The authorizing instruction was explicit that a Thunderbolt connection must not be
inferred from a product name; it must not be inferred from this one.

| Question | Answer | Evidence |
|---|---|---|
| Which dock? | **Thunderbolt 4**, not the Thunderbolt 3 the topology change was described as | `SPThunderboltDataType`: `device_name_key = "ThinkPad Thunderbolt 4 Dock"` |
| Dock identity | Lenovo `vendor_id_key 0x17EF`, `device_id_key 0x30B3`, `switch_version_key 38.6` | same |
| How did the dock link negotiate? | **`mode_key = "usb_four"`** — USB4, not native Thunderbolt | same |
| Dock upstream link | connected, **`40` Gb/s**, `link_status 0x2`, TB/USB4 Bus 1 | same |
| Dock's downstream Thunderbolt port | **empty** — `receptacle_no_devices_connected` | same |
| Is the volume Thunderbolt storage? | **No.** `diskutil` reports `BusProtocol = USB` | `diskutil info -plist` |
| How is it attached? | USB mass storage, three dock hub tiers | IOService-plane walk |

```text
DOCK_TRANSPORT_CLASS = USB_VIA_THUNDERBOLT_DOCK
```

The cascade, host-side first, walked **from the mounted volume's own media upward** rather than
guessed from proximity in a device list:

```
AppleT8103USBXHCI              the Mac's own USB host controller
└── USB3.0 Hub   0x8087:0x0B40     Intel — the dock's USB4-side hub
    └── USB3.1 Hub 0x17EF:0x30B6   Lenovo
        └── USB3.1 Hub 0x17EF:0x30B8  Lenovo
            └── SSK SSD 0x090C:0x2320, serial SSKPSSD0000000000071
```

Host: MacBook Pro `MacBookPro17,1`, Apple M1, 8 GB. Volume: `397A4D4A-9508-391E-814E-3B533C7BD049`,
ExFAT, `499,955,924,992` B total.

## 5. D141-R4 — the profile, and stable-versus-volatile identity

The **Volume UUID remains the primary identity and is unweakened.** The transport profile is a
second, narrower launch condition answering a different question: *is that volume attached the
way it was qualified?*

**Frozen** (stable hardware properties): the storage device's USB vendor, product and serial;
the ordered dock hub cascade `0x8087:0x0B40 → 0x17EF:0x30B6 → 0x17EF:0x30B8`.

**Recorded as evidence, decided on by nothing**: the dock's Thunderbolt vendor/device ids, its
`switch_uid`, firmware version, route string, negotiated speed, product-name strings, IORegistry
entry ids, and `locationID` values.

**Never frozen, and explicitly never compared**: `disk4`, `disk4s2`, or any BSD identifier. The
current identifier is used only as a momentary lookup key into the IORegistry, obtained from the
volume that has *already* proved its UUID. **A changed disk number does not refuse**, and that
non-refusal has its own tests at both the unit and the production-envelope level.

The cascade comparison is **exact and ordered**. That is a deliberate constraint: Decision 141
qualified the SSD on one dock port, and a different port yields a different cascade — a topology
this repository has not qualified. A refusal is repaired by restoring the qualified port, never
by relaxing the tuple. The limitation is stated in §12 rather than hidden.

## 6. D141-R2 / D141-R3 — how it is read and classified

`ioreg -a -p IOService -r -c IOUSBHostDevice -l -w0` emits a **property list**, and it is parsed
as one — the same rule `macos_volume_identity` already follows in refusing to parse the
human-oriented `diskutil info` table. Only nodes whose registry class is exactly
`IOUSBHostDevice` count: the interface and mass-storage nubs beneath a device inherit its
vendor/product ids, so counting them would turn a three-hub cascade into a six-entry chain and
the comparison could never match. That filter has its own killer test.

Three classes: `USB_VIA_THUNDERBOLT_DOCK`, `USB_DIRECT` (Decision 136's topology, **not
revoked** — D141-R8), and `UNQUALIFIED`. Qualified is the only answer that admits. Direct is
never reclassified as the dock and the dock is never reclassified as direct.

Measured cost: `0.058`–`0.060` s. Cheap enough to be a launch precondition.

## 7. Bounded file I/O — and one reading that had to be re-measured

Every run was non-sparse, deterministic, `fsync`-ed, `F_FULLFSYNC`-ed, and read back with
`F_NOCACHE` so the readback came from the device rather than the page cache. **Every run's
SHA-256 written and read back were identical.**

| Run | fsync-complete write | Uncached read | Hash |
|---|---|---|---|
| 3 GiB — the first write ever made into the new directory | `110.435` MiB/s | `458.813` MiB/s | identical |
| 2 GiB — the size Decision 136 used | `352.763` MiB/s | `560.359` MiB/s | identical |
| 3 GiB re-run | `404.909` MiB/s | `480.964` MiB/s | identical |
| 6 GiB | `388.493` MiB/s | `436.747` MiB/s | identical |
| 4 GiB, under concurrent power sampling | `530.080` MiB/s | — | — |

`F_FULLFSYNC` returned success and cost `0.0002` s beyond `fsync` on the 2 GiB run.

**The first reading is reported because it was observed, and its cause is not claimed.** At
`110.435` MiB/s it would have read as a ~56% regression against Decision 136's direct-connection
`250.438` MiB/s. It was not reproduced: three later runs at 2, 3 and 6 GiB measured `352.8`,
`404.9` and `388.5` MiB/s, with 512 MiB segment sampling showing a steady `~420`–`435` MiB/s
plateau and **no cliff out to 6 GiB**. Sustained write through the dock therefore **exceeds**
the direct-connection baseline rather than falling below it, and every run clears the accepted
`50` MiB/s D136 qualification floor by at least `2.2×`. The first run's cause was not isolated
and **no explanation is asserted**.

## 8. SQLite WAL, locking, and process-crash recovery

Run under the project's accepted profile, read back from the connection rather than assumed:
`journal_mode=wal`, `synchronous=2` (FULL), `foreign_keys=1`, `mmap_size=0`, `cache_size=-524288`
(512 MiB), `busy_timeout=10000`, `page_size=4096`.

| Measure | Result |
|---|---|
| Transactions / rows | `240` × `500` = `120,000` |
| Database | `553,132,032` B |
| WAL high-water | `4,688,592` B; `0` after `wal_checkpoint(TRUNCATE)` |
| Commit latency | min `7.635` ms, p50 `19.358` ms, p95 `24.676` ms, max `55.883` ms |
| `integrity_check` | **`ok`** |
| `foreign_key_check` | **`0`** violations |
| Busy / I/O errors | **none** |

**Locking**, in separate OS processes — never threads: a second writer attempting
`BEGIN IMMEDIATE` while a holder held one was **excluded** (`database is locked`); a reader saw
`0` of the holder's uncommitted rows; after the holder exited the second writer **acquired**;
`integrity_check` after contention `ok`. No `ENOTSUP` or locking anomaly.

**Process-crash recovery**, by `SIGKILL` — no physical interruption of any kind:

* **A, uncommitted:** child killed mid-transaction (`rc = -9`). Uncommitted rows present:
  **`0`**. `integrity_check` **`ok`**.
* **B, committed:** child committed then was killed before any graceful close (`rc = -9`). A
  **hot WAL of `28,872` B** was present at reopen, so recovery genuinely occurred. Committed rows
  present: **`1000`**. `integrity_check` **`ok`**, `wal_checkpoint(TRUNCATE)` succeeded with
  `busy = 0`, `integrity_check` after checkpoint **`ok`**, `0` foreign-key violations.

## 9. Link stability, and charging coexistence

```text
DOCK_LINK_FLAPS   = 0
SSD_DETACH_EVENTS = 0
IO_ERRORS         = 0
```

`63,970` kernel log lines across the 45-minute window containing the whole qualification were
scanned: **zero** matches for any `disk4`, `SSK`, `IOUSB`, `AppleUSB`, `Thunderbolt`, `exfat`,
`IOStorage`, I/O-error or I/O-timeout event. A broader scan returned 25 candidate lines, **all**
of which were `runningboardd` process-lifecycle records matching the substring
`terminateprocess`; none is a storage, USB or Thunderbolt event, and none is interpreted as one.

In-band, across every phase boundary: mount present, Volume UUID exact, `st_dev = 16777238`
constant, transport class constant.

```text
DOCK_POWER_AND_STORAGE_COEXIST = PASS
```

Because charging while the SSD is attached is the entire reason for the topology, this was
measured **during** the load rather than inferred from before-and-after readings: `13` samples
across `7.7` s of sustained 4 GiB writing at `530.08` MiB/s. `ac_power` **`True`** on every
sample, `mounted` **`True`** on every sample, `st_dev` constant, adapter connected and reporting
**`92` W** before, during and after. The `92` W supply is not the Mac's own `61` W brick, which
is consistent with power arriving through the dock.

No repeated disconnects under sustained load, no thermal or power device errors, and charging
never lapsed. **No temperature threshold is invented and no third-party monitoring was
installed.**

## 10. D140 safety revalidated on the docked path

Seventeen live controls, each asserting the **reason** for its outcome rather than merely that
something was raised — a control that refuses for the wrong reason proves nothing. **17/17**
behaved exactly as required.

Refused, each for its own stated reason: the UUID assertion omitted; a wrong UUID; the D130
archive root as work root; a child of the archive; the volume root; `SQLITE_TMPDIR` absent, on
the internal volume, and inside the archive; and a named volume that is not mounted.

Admitted, correctly: a **substring-decoy sibling** of the archive directory name — the
component-wise containment rule does not over-refuse a sibling whose name merely begins with the
archive's; the accepted **internal historical root**, which returns `None` and is byte-for-byte
the Decision 116 path; and **the real docked path with everything correct**, which was asserted
to have created nothing.

`§19`, by synthetic and provider-based substitution with **no physical removal**: a vanished work
root escaping the mount point, a changed `st_dev`, a replacement mount reporting a different
UUID, and a mount point replaced by an internal directory — **all four refused**, and the live
pinned volume re-authenticated.

```text
D140_SAFETY_ON_DOCK_PATH = PASS
```

## 11. The integration

One new module, `src/disclosure_drift/m3/dock_transport.py`, and two calls added to the composed
external preflight in `external_working_root.py`. The composed preflight is the single point all
three canary modes — `preflight`, `run` and `profile-prefix` — already flow through, so the
checks reach production by construction rather than by a second rule.

Guard order is now: identity → **transport** → **host launch conditions** → isolation → archive
→ capacity → temporary placement → observation. Transport runs second because it is the only
guard needing the authenticated volume's own BSD identifier as a lookup key, and because an
unqualified attachment should be refused before a `~104` GB archive is stat-ed.

Both new readers are substituted through **module-global seams** (`transport_of`,
`host_power_state`), exactly as `macos_volume_identity` already is. **There is no switch that
disables either check** — that shape was the D137 review's MAJOR-1, and it is not reintroduced.
The `required_transport` argument, like `--require-volume-uuid`, can only **narrow**.

**No CLI flag was added.** The authorizing instruction leaves selecting one topology for the
real canary to the owner (§16 below), so the repository recognizes both qualified topologies and
refuses a third; the pin is a library parameter. `cli.py` is unchanged.

**The internal historical path costs no `ioreg` and no `pmset`**, proved by making both fatal in
a test — the same care Decision 140 took to keep an internal root free of a `diskutil` call.

## 12. Limitations, stated rather than smoothed

1. **`F_FULLFSYNC` returning success is an OS-visible result only.** It is **not** proof that the
   dock, its bridge, or the SSD physically honoured a flush. Decision 136's D137-R11 position is
   unchanged: ExFAT has no metadata journal, and this record converts nothing.
2. **Process-crash recovery only.** No surprise removal, no power-loss test, no physical
   disconnection was performed or is authorized. A matching transport does **not** prove the
   dock, cables or enclosure cannot fail.
3. **The cascade match is port-specific.** Moving the SSD to a different dock port refuses and
   requires re-qualification. This is deliberate and is stated in runbook §28f.B.
4. **macOS-only**, like `macos_volume_identity` before it. `ioreg` and `pmset` are the readers.
5. **The 110 MiB/s first reading is unexplained.** It was not reproduced across three later runs;
   no cause is claimed.
6. **No dock-specific serial is used as a launch predicate.** The Thunderbolt `switch_uid` is
   recorded as evidence only; the USB cascade is what the check decides on.
7. **Host battery health is degraded** — `73%` maximum capacity, `859` cycles, macOS reporting
   `Check Battery`. AC is a launch requirement, and this makes the AC requirement more, not less,
   important; it is not a mitigation.
8. **8 GB of host RAM.** Unchanged by this record and unmeasured at full canary scale, exactly as
   Decision 140 §18 already carried.
9. **Bounded qualification.** Nothing here extrapolates complete-source runtime, and nothing here
   is a rehearsal of one.

## 13. D130 protection

**Precheck:** `24` entries; the four compact proofs identical in `0.0016` s; the tar `stat`-ed at
exactly `103,966,696,960` B and **never opened**; free `310,498,426,880` B.

**Postcheck:** `24` entries unchanged; compact proofs identical in `0.0005` s; tar size, inode,
mtime and ctime **byte-identical** to the precheck.

The tar-open tripwire is a real one, not an assertion: `open`, `Path.open` and `Path.read_bytes`
were wrapped to raise on the tar path, the accepted compact precheck was run through them
recording **`0`** opens, and **the tripwire was then proved armed by making it fire on a genuine
open.** A tripwire that cannot fire proves nothing.

**An honest negative result:** `atime` does **not** advance on read on this ExFAT volume —
calibrated on a disposable D141 file, never on the archive. `atime` is therefore *not* evidence
that the tar was never opened, and it is not offered as any. The tripwire and the code path are.

**Free space is fully reconciled.** Scratch held `553,164,800` B in 2 files; after deletion free
returned to **`310,498,426,880` B — byte-identical to the pre-qualification reading**. The
qualification root was created outside the archive, used only for D141, and removed. No other
deletion occurred anywhere on the volume.

## 14. Validation and falsification

| Gate | Result |
|---|---|
| Focused baseline, before any edit | `206` passed |
| Focused suites, after integration | `206` passed — unchanged |
| New `test_d141_dock_transport_qualification.py` | `33` passed |
| Full suite | see §14.1 |
| `ruff check` / `ruff format --check` | clean |
| `mypy src` (the acceptance gate) | `Success: no issues found in 96 source files` |
| Governance section-reference gate | `59` passed |

**Falsification — `11` reversible source mutations, `11` killed, `0` survived.** Every file was
proved **byte-identical by SHA-256** after each mutation and after the run as a whole. No
source-mutating framework was used.

| # | Mutation | Killed at |
|---|---|---|
| M1 | transport classifier always returns `DOCK` | `test_a_direct_connection_is_recognised_and_is_not_the_dock` |
| M2 | qualification aggregator admits anything | `test_an_unqualified_cascade_is_never_admitted[an-unrelated-third-party-hub]` |
| M3 | topology-profile comparison always matches | `test_an_unqualified_cascade_is_never_admitted[an-unrelated-third-party-hub]` |
| M4 | storage-identity check removed | `test_the_right_volume_behind_the_wrong_enclosure_is_refused[wrong-serial]` |
| M5 | narrowing assertion ignored | `test_a_supplied_assertion_can_only_narrow` |
| M6 | Volume UUID comparison always matches | `test_d137…::test_a_wrong_uuid_is_refused` |
| M7 | AC-power predicate removed | `test_battery_power_refuses_through_the_production_envelope` |
| M8 | lid predicate removed | `test_a_closed_lid_refuses_through_the_production_envelope` |
| M9 | D130 exclusion neutered | `test_d137…::test_the_archive_directory_itself_is_refused` |
| M10 | **transport guard never called from the preflight** | `test_the_transport_check_actually_reaches_the_production_envelope` |
| M11 | **host power conditions never applied in the preflight** | `test_battery_power_refuses_through_the_production_envelope` |

**M10 and M11 are the two that matter most.** They are the reachability mutations: they leave
every guard implemented and correct and merely stop the preflight from calling it — which is
precisely the state `require_launch_power_conditions` was actually in before this record. Both
are killed, so the same defect cannot recur silently.


## 15. Acceptance thresholds

```text
DOCK_TOPOLOGY_IDENTIFIED       = PASS      DOCK_SQLITE_INTEGRITY         = PASS
DOCK_POWER_STABLE              = PASS      DOCK_LOCKING                  = PASS
DOCK_POWER_AND_STORAGE_COEXIST = PASS      DOCK_PROCESS_CRASH_RECOVERY   = PASS
DOCK_STORAGE_IO                = PASS      DOCK_VOLUME_UUID_STABLE       = PASS
DOCK_READBACK_HASH             = PASS      DOCK_LINK_FLAPS               = 0
DOCK_SQLITE_WAL                = PASS      SSD_DETACH_EVENTS             = 0
D130_PRECHECK                  = PASS      IO_ERRORS                     = 0
D130_POSTCHECK                 = PASS      D140_SAFETY_ON_DOCK_PATH      = PASS
```

## 16. Is the dock the intended canary topology?

**That is the owner's call, and this record does not make it.** Decision 141 qualifies the docked
topology and **does not revoke** the Decision 136 direct one; both are recognized and a third
refuses. The authorizing instruction reserves selecting one for the owner, and the
`required_transport` pin exists so that selection can be expressed when it is made.

## 17. What did not change

The Volume UUID and every capacity floor; the D131 parser and runtime semantics; the D130
archive; migration head `0015`; all three activation constants at `None`; both network switches
at `false`; the D136-R8 one-canary exception's width; `census_orchestrator.py::_parse_bulk`,
which **remains an open pre-network blocker deliberately unrepaired**; `cli.py`; and governed
pause/resume, which remains `NOT_IMPLEMENTED` with no `SAFE_TO_EJECT` state.

## 18. What this record does not authorize — D141-R12

No canary. No canary world, run identity, execution namespace or launch receipt. No E0. No
migration `0016`. No network. No D130 mutation. No pause/resume. **A passing preflight still
prints `canary_authorized: false`, and holding one is not an authorization to launch.**

## 19. The next authorized action

Return to the owner. The corrected complete-source canary remains unauthorized, Decisions 137,
138, 140 and this record remain un-accepted, and the governed pause/resume redesign remains open
owner work that may still change the tree — so the final independent review should not be
commissioned until the owner confirms no further pre-canary architecture changes are planned.
