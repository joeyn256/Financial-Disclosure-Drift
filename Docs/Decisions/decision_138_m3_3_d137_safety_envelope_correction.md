# Decision 138 — The D137 Safety-Envelope Correction

```text
STATUS: IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER ACCEPTANCE
RECORD_TYPE: BOUNDED CORRECTION OF THE THREE MAJORS THE ACCEPTED D137 INDEPENDENT REVIEW RAISED —
  THE MANDATORY EXTERNAL ENVELOPE, THE IN-PROCESS DURING_F2 ENFORCEMENT, AND THE POST_F0 / PRE_F1
  PHASE GATES
DATE: 2026-08-23
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings D138-R1 – D138-R13
CLASSIFICATION: BOUNDED_CORRECTION_ONLY — NOT A REDESIGN OF DECISION 137
REVIEW_VERDICT_ACCEPTED: D137_INDEPENDENT_REVIEW_CORRECTION_REQUIRED — ZERO BLOCKERS, THREE MAJORS
REVIEW_ACCEPTANCE: M3_3_D137_INDEPENDENT_IMPLEMENTATION_REVIEW_OWNER_ACCEPTED
CORRECTION_AUTHORIZATION:
  M3_3_D138_D137_SAFETY_ENVELOPE_CORRECTION_AUTHORIZED — issued outside this repository and now
  spent
D137_ACCEPTANCE: NONE — DECISION 137 WAS NOT OWNER ACCEPTED BEFORE THIS CORRECTION AND IS NOT
  ACCEPTED BY IT
ACCEPTANCE_TOKEN: NONE — THIS RECORD CLAIMS NO OWNER ACCEPTANCE
COMPLETION_TOKEN: M3_3_D138_D137_SAFETY_ENVELOPE_CORRECTION_COMPLETE_READY_FOR_REVIEW
QUALIFIED_VOLUME_UUID: 397A4D4A-9508-391E-814E-3B533C7BD049 — THE ONLY AUTHORIZED IDENTITY
EXTERNAL_ENVELOPE: MANDATORY, DECIDED BY THE RESOLVED WORK ROOT. THE CLI FLAG IS AN ASSERTION AND
  CANNOT DISABLE A SINGLE GUARD
ROOT_SELECTION_SURFACE: EXISTING --work-root, UNCHANGED. NO SECOND MECHANISM CREATED
LAUNCH_FLOOR: 185 GiB — 198,642,237,440 BYTES — UNCHANGED
POST_F0_FLOOR: 60 GiB — 64,424,509,440 BYTES — NEW, EXECUTABLE
PRE_F1_FLOOR: 55 GiB — 59,055,800,320 BYTES — NEW, EXECUTABLE
PRE_F2_FLOOR: 50 GiB — 53,687,091,200 BYTES — UNCHANGED
DURING_F2_ALERT: 20 GiB — 21,474,836,480 BYTES — RECORD AND CONTINUE
DURING_F2_HARD_FLOOR: 10 GiB — 10,737,418,240 BYTES — IN-PROCESS ABORT AND ROLLBACK
DURING_F2_SAMPLING: SYNCHRONOUS, IN F2'S OWN LOOP, MONOTONIC CLOCK, 5 s SCHEDULED / 60 s CEILING
MEASUREMENT_FAILURE: FAILS CLOSED THROUGH THE SAME ROLLBACK-SAFE ABORT PATH
WATCHDOG_ROLE: SUPPLEMENTAL OPERATOR OBSERVABILITY ONLY — NOT THE ENFORCEMENT MECHANISM
FOCUSED_BASELINE_BEFORE: 384 PASSED — THE ACCEPTED D137 STATE, REPRODUCED
FOCUSED_AFTER: 450 PASSED — 384 + 66, NO REGRESSION
FALSIFICATION: 13 REVERSIBLE MUTATIONS, EVERY ONE KILLED BY NAMED TESTS
LIVE_PREFLIGHT: RUN — READ-ONLY, NOTHING CREATED ON THE VOLUME
MIGRATION_HEAD: 0015 — 0016 ABSENT, UNAPPLIED, NOT AUTHORIZED
ACTIVATION_CONSTANTS: ALL THREE REMAIN None
NETWORK_AUTHORIZATION: NONE — REQUEST CEILING 0
CORRECTED_CANARY_AUTHORIZATION: NO
E0_EXECUTION_AUTHORIZATION: NO
PRE_NETWORK_BLOCKER: CensusOrchestrator._parse_bulk — OPEN, DELIBERATELY UNREPAIRED
NEXT_STAGE: INDEPENDENT REVIEW OF THIS CORRECTION, THEN AN OWNER DECISION ON D137+D138 ACCEPTANCE
```

Decision 137 built the external safety envelope. Its independent review found that the envelope
could be **walked around**, that its most important floor was **advisory**, and that two accepted
stop-and-report gates were **never written**. This record corrects those three things and nothing
else.

## 1. What this record is, and what it is not

It is the bounded correction of the three majors the accepted D137 independent review raised. It
is **not** a redesign of Decision 137, and **not** an acceptance of it.

**Decision 137 remains historical and is not rewritten.** Its defects were real, its record says
what it said, and no byte of it is edited to pretend otherwise. What is corrected is the **code**,
the **tests**, and the **runbook** — the places where the defects actually lived.

**Decision 137 was never owner accepted.** Implementation is not acceptance, and this record does
not supply the acceptance D137 never had. It carries **no acceptance token of its own** either.

## 2. Entry state

| Fact | Value |
|---|---|
| Branch / `HEAD` | `main` / `358c45c7ccdac6253365edc53e8a9d59e50b55da` |
| Tree | `af4f53a1322334bb60cc27af461f6bea67afee7f` |
| `origin/main` | identical; ahead/behind `0`/`0`; worktree clean; nothing staged |
| Latest governance | Decision 137 — `IMPLEMENTED — PENDING INDEPENDENT REVIEW AND OWNER ACCEPTANCE` |
| Migration head | `0015`; `0016` absent |
| Activation constants | `PRE_E0_CATALOG_TRANSITION_AUTHORITY`, `M3_3_E0_EXECUTION_AUTHORITY`, `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` — all `None` |
| Network | `network.enabled=false`, `network.m3_acquire_enabled=false` |
| Canary world on the SSD | none |

Every entry condition matched. Nothing was started on a mismatch, because there was none.

## 3. The accepted review verdict, and the owner's adjudication

The verdict accepted is **`D137_INDEPENDENT_REVIEW_CORRECTION_REQUIRED`** — **zero blockers, three
majors**, all three accepted for correction.

| | The major, as accepted | The owner ruling that disposes of it |
|---|---|---|
| **MAJOR-1** | The external safety envelope can be **bypassed by omitting** the optional `--require-volume-uuid` path | **D138-R1, R2, R3, R12** — the envelope is mandatory, decided by the resolved root; archive exclusion is unconditional; `SQLITE_TMPDIR` is validated where SQLite reads it; only the one D136 identity is ever accepted |
| **MAJOR-2** | The `DURING_F2` `10` GiB hard floor is **classification and reporting only**, with no continuous mechanical enforcement | **D138-R8, R9, R10, R11** — enforcement moves **inside** the process running F2, sampled on a bounded interval, aborting from within the open transaction; the watchdog is demoted to observability |
| **MAJOR-3** | The D135 `POST_F0 >= 60` GiB and `PRE_F1 >= 55` GiB stop-and-report **phase gates are not enforced** | **D138-R5, R6** — both adopted as executable gates ahead of the phases they admit |

## 4. The baseline, reproduced before anything was edited

The accepted focused set ran unchanged first: **`384` passed** in `124.97` s across
`test_d116_single_source_canary.py`, `test_d119_cache_and_prefix.py`,
`test_d127_pre_f2_admission_guard.py`, `test_d131_signal_and_monitor.py`,
`test_d137_external_working_root.py`, and `tests/integration/test_m3_cli.py` — the exact count
Decision 137 §17 published.

Each review finding was then reproduced as an executable assertion of the **defective** behaviour,
in a temporary file that was deleted afterwards and never committed:

| | Reproduced as | Result before the correction |
|---|---|---|
| **A** | An unqualified external volume with the flag omitted | The run **completed** and built a world; the external preflight was invoked **zero** times |
| **B** | A work root inside the D130 archive with the flag omitted | A world was **created inside** the only surviving copy of the D128 evidence |
| **C** | Free space sampled during F2 | **Zero** readings taken while the transaction ran; `1` byte free changed nothing; `materialize_census_associations` accepted no capacity parameter |
| **D** | `52` GiB observed at `POST_F0` and `PRE_F1` | Below **both** D135 floors, and the run proceeded through F1 and F2 to completion; neither constant existed |

After the correction, A, C, and D flip: those assertions can no longer be made. B and the F2 case
flip only under external classification, which is the point — an internal `tmp_path` is genuinely
internal, and Decision 138 does not pretend otherwise.

## 5. Correction C1 — the external envelope is mandatory (D138-R1, R2, R3, R12)

**The defect was that protection was something a run had to ask for.** `require_volume_uuid` was
both the assertion *and* the switch: `None` meant "no external requirement", so an operator who
never typed the flag reached an unqualified disk, or the archive, with **no guard running at all**.

**The correction takes the decision away from the argument and gives it to the path.**

- `external_volume_candidate(path)` classifies the **resolved root** by device number, on its
  **nearest existing ancestor**, so the world is classified before it is created and **no
  `diskutil` call is made for an internal root**. A derived mount point equal to the system root's
  is internal; anything else is external.
- `require_external_envelope()` is the single decision point. External → the **complete** D137
  envelope runs. Internal, with no assertion → `None`, and the caller's path is exactly what
  accepted Decision 116 left it.
- **An unclassifiable root refuses.** Internal is the only answer that admits without proof, so it
  is never the fallback.

**The flag can now only ever add a requirement** (D138-R1). Supplied, it forces the envelope onto
a root that would classify as internal — so asserting the qualified volume for an internal root
refuses at the identity guard, which is the truth — and it must itself be
`397A4D4A-9508-391E-814E-3B533C7BD049`. **An arbitrary UUID is refused before anything is
measured** (D138-R12): the expected identity passed into the envelope is the frozen constant, never
the caller's string, so there is no generic external-volume authorization here and D125-R4 remains
the general rule outside the one-canary exception.

**Both enforcement layers route through the one primitive.** `run_canary_source_command`,
`run_single_source_canary`, and `run_single_source_prefix_profile` each call it, so a direct
library caller cannot bypass what the operator surface enforces, and a diagnostic prefix cannot
reach a volume the complete-source run would have refused.

**Archive exclusion is now unconditional on the qualified volume** (D138-R2). It was always inside
the envelope; the correction is that the envelope is always entered. The refusal itself is
byte-unchanged D137-R3 — `realpath`-resolved, case-folded components, so `..`, a symlink, and a
case variant cannot launder containment **and** a lawful sibling sharing the name prefix is still
not falsely refused.

**`SQLITE_TMPDIR` is validated where SQLite reads it** (D138-R3). The D137 review's MINOR was that
a guard could validate a caller-supplied mapping while SQLite went on to read `os.environ`. The
guard now resolves the value from the **process environment** — the only environment the spilling
process has — and an explicitly supplied mapping must carry the **identical** value. A
disagreement is a refusal, not a preference. The normal CLI path supplies no mapping and is
therefore deterministic.

## 6. Correction C2 — continuous F2 enforcement, in-process (D138-R8 – R11)

**The defect was that the `10` GiB floor was a printed opinion.** `f2_capacity_state()` classified
free space correctly and the watchdog's `capacity` subcommand printed exit `6` correctly, and
neither could stop a transaction: enforcement depended on a human starting a second process, which
nothing obliged them to do.

**`F2CapacityGuard` samples from inside the process executing F2 and raises from inside its open
transaction.** F2 is one transaction, so
[`transaction()`](../../src/disclosure_drift/storage/sqlite.py) rolls it back on the way out — the
in-flight projection is **discarded, not truncated**, and **no partial F2 association state
commits**.

| Free space | State | What happens |
|---|---|---|
| `> 20` GiB | `F2_CAPACITY_NORMAL` | nothing recorded, F2 continues |
| `<= 20` GiB | `F2_CAPACITY_ALERT` | a `DURING_F2` observation is recorded, F2 **continues** |
| `<= 10` GiB | `F2_CAPACITY_HARD_STOP` | `F2CapacityHardStopError` — abort and **roll back** |
| unmeasurable | `F2_CAPACITY_MEASUREMENT_FAILED` | the **same** abort path — fail-closed |

Both thresholds stay **inclusive** and neither moved: D124-R5's `10` GiB is untouched, and the
`20` GiB alert is D135-R7's.

**Sampling is bounded by wall clock, not by iteration count** (D138-R9). The guard is called from
F2's own per-accession loop in **both** traversals, and from the entry point before the transaction
opens. It decides for itself whether enough time has passed, on a **monotonic** clock that a
system time adjustment cannot walk backwards. The scheduled interval is `5` s against a `60` s
ceiling, so a long batch cannot buy hours of unobserved execution — and calling it per accession is
affordable precisely because most calls return immediately.

**No thread, no background process, no signal, no deletion, no escalation.** The check is
synchronous, the abort is an exception, and D131's no-escalation behaviour is untouched.

**The hard-stop evidence survives the rollback** (D138-R10). It is built **before** the exception
is raised and carried **on** it — phase `DURING_F2`, the reason, the measured free bytes or the
measurement-failure class, the threshold, the observation time, the authenticated volume identity,
and the explicit statements `f2_transaction_rolled_back: true` and `f2_committed: false`. Writing
it into the transaction being rolled back would have destroyed exactly the record the operator
needs. `ALERT` observations use the existing `CapacityObservation` mechanism and share the run's
own list, so they land chronologically among the phase boundaries; fields the guard deliberately
does not measure stay `None` rather than becoming zeros.

**The watchdog is demoted, in prose and in help text** (D138-R11). Its `capacity` subcommand
remains as operator observability. Its exit codes are no longer described as stopping anything:
**exit `6` does not stop F2**, and the module says so.

**Scope**: the guard is bound **only** on the protected external path. An internal run binds
`None` and F2 behaves exactly as accepted Decision 094 §6.4 left it.

## 7. Correction C3 — the POST_F0 and PRE_F1 gates (D138-R5, R6)

Decision 135 §11 (D135-R7) stated both rows as **stop-and-report**. Decision 137 recorded the
observations and enforced neither.

```text
POST_F0_MINIMUM_FREE_BYTES = 60 * 1024**3 = 64,424,509,440
PRE_F1_MINIMUM_FREE_BYTES  = 55 * 1024**3 = 59,055,800,320
```

`require_phase_free_space()` is applied to the observation the run has just taken, at both
boundaries, **before F1 begins**. `>=` admits at each floor and one byte below refuses. A
measurement that could not be taken never reaches the comparison at all — `observe_capacity()` has
already refused it — which is why an unmeasurable boundary refuses rather than being admitted by
default. **Nothing is deleted, moved, or cleaned to clear either floor.**

They remain **two separate named gates** even though they occur close together (D138-R6): they
answer *did F0 leave enough behind?* and *is there enough to start F1 with?*, and folding them
would lose the phase-boundary verification that is the point of having both.

**Three floors keep their own accepted call sites and are not moved into this mechanism.**
`PRE_LAUNCH`'s `185` GiB is enforced by `require_launch_free_space` before any world exists
(D138-R4, unchanged), and `POST_F1_PRE_F2`'s `50` GiB stays exactly where accepted Decision 126 §7
(D126-R6) put it — between F1's return and F2's call, the one point where the measurement and the
transaction it admits cannot be separated by a race (D138-R7, unchanged). **The `30` GiB behaviour
remains unreachable.**

Because the floors **descend** — `60`, then `55`, then `50` — no single free-space value can breach
a later gate without having breached every earlier one first. The tests therefore drop free space
*between* boundaries, which is both the only way to reach each gate in isolation and the real shape
of the failure being modelled.

## 8. The change set

| Path | What changed |
|---|---|
| `src/disclosure_drift/m3/external_working_root.py` | `external_volume_candidate`, `require_external_envelope`, `require_phase_free_space`, `F2CapacityGuard`, `F2CapacityHardStopError`, the two new floors and the phase-floor map, and the `SQLITE_TMPDIR` environment cross-check |
| `src/disclosure_drift/m3/single_source_canary.py` | The three entry points call the mandatory envelope; `record_phase` enforces its floor; the F2 guard is bound and passed down |
| `src/disclosure_drift/m3/offline_parse.py` | `materialize_census_associations` takes an optional `capacity_guard`, called at entry and in both membership traversals |
| `src/disclosure_drift/cli.py` | `--require-volume-uuid` help: an assertion, never a switch |
| `scripts/m3/canary_watchdog.py` | Prose, exit-code documentation, and subcommand help demoted to supplemental observability |
| `tests/unit/test_d137_external_working_root.py` | Updated **in place** for the D138-R3 environment contract and the `DURING_F2` rationale — not deleted, not skipped |
| `tests/unit/test_d138_safety_envelope_correction.py` | **New.** `66` tests across the classifier, the mandatory envelope, exact-UUID pinning, `SQLITE_TMPDIR`, the phase gates, and the F2 guard including the rollback proofs |
| `Docs/m3/operator_runbook.md` | §28d rewritten for the corrected contract |

**No migration, no schema, no configuration, and no authority constant moved.**

## 9. Validation

**Focused suite: `384` before, `450` after** — `384 + 66`, **no regression** — in `127.00` s over
the same set plus `test_d138_safety_envelope_correction.py`. Ruff clean, `ruff format --check`
clean, and **mypy strict clean over all `94` source files**.

**Falsification: `13` reversible source mutations, every one killed.** Each protection was broken
or inverted in place, the targeted nodes were run, the file was restored, and every mutated file
was verified byte-identical by SHA-256 afterwards. **No source-mutating framework was used.**

| Mutation | Killed by |
|---|---|
| automatic external-mode detection disabled | `test_c1_case_2_the_uuid_argument_omitted_still_protects_the_external_root`, `test_c1_case_5_an_unqualified_external_volume_refuses_with_no_flag`, `test_the_library_boundary_refuses_an_unqualified_volume_with_no_flag`, `test_the_library_boundary_refuses_the_archive_with_no_flag` |
| archive check bypassed | `test_c1_cases_6_and_7_a_root_inside_the_d130_archive_refuses_either_way[None]`, `…[397A4D4A-9508-391E-814E-3B533C7BD049]`, `test_c1_case_8_a_symlinked_or_normalized_alias_into_the_archive_refuses`, `test_the_library_boundary_refuses_the_archive_with_no_flag` |
| an arbitrary asserted UUID accepted | `test_c1_cases_3_and_4_a_wrong_or_arbitrary_asserted_uuid_refuses[0BADCAFE-…]`, `…[11111111-…]` |
| external `SQLITE_TMPDIR` same-volume check disabled | `test_c1_case_13_an_internal_temporary_root_refuses_in_automatic_mode`, `test_an_internal_temporary_root_is_refused` |
| `POST_F0` gate removed | `test_the_two_new_floors_are_exactly_sixty_and_fifty_five_gibibytes`, `test_each_phase_gate_refuses_one_byte_below_its_floor[POST_F0-64424509440]`, `test_a_breach_at_either_gate_stops_the_run_before_f1_begins[64424509439-POST_F0-None]`, `test_f1_is_never_called_when_the_post_f0_gate_refuses` |
| `PRE_F1` gate removed | `test_the_two_new_floors_are_exactly_sixty_and_fifty_five_gibibytes`, `test_each_phase_gate_refuses_one_byte_below_its_floor[PRE_F1-59055800320]`, `test_a_breach_at_either_gate_stops_the_run_before_f1_begins[59055800319-PRE_F1-POST_F0]` |
| hard stop turned into an alert | `test_the_hard_floor_is_inclusive_and_raises_the_dedicated_condition`, `test_a_hard_stop_mid_f2_rolls_the_association_mutation_back`, `test_a_hard_stop_during_a_real_run_leaves_no_result_document` |
| periodic `DURING_F2` call removed from the **writing** traversal | `test_f2_commits_its_association_rows_when_capacity_holds` |
| periodic `DURING_F2` call removed from the **completeness** traversal | `test_f2_commits_its_association_rows_when_capacity_holds` |
| the reading taken **before** F2 opens removed | `test_f2_is_sampled_before_its_transaction_opens` |
| capacity measurement error swallowed | `test_a_measurement_failure_takes_the_same_hard_stop_path`, `test_a_measurement_failure_mid_f2_rolls_back_the_same_way` |
| transaction committed despite the hard stop | `test_a_hard_stop_mid_f2_rolls_the_association_mutation_back`, `test_a_measurement_failure_mid_f2_rolls_back_the_same_way` |
| envelope forced onto internal roots too | `test_c1_case_9_an_internal_root_with_no_assertion_keeps_its_historical_behaviour`, `test_an_internal_run_binds_no_guard_at_all`, `test_the_classifier_never_shells_out_for_an_internal_root` |

**Two of these were found by falsification rather than by design**, and are recorded because that
is what falsification is for. The first version of the entry-reading test asserted on the reading
*count*, which cannot distinguish "sampled before F2 opens" from "sampled at F2's first accession"
— deleting the entry call simply promotes the first loop call into its place. The test now asserts
on `in_transaction`, which is `False` for the entry reading and `True` for every later one. The
first version of the sampling control likewise asserted only `samples > 1`, which survived removing
either traversal's call; it now asserts the **shape** of what the readings observe — zero rows
before the transaction, a partial count during the writing traversal, and the final total seen more
than once during the completeness traversal.

### The rollback proof

The proof is not that an exception was raised. It is that the association mutation **existed inside
the transaction and is absent after it**, observed on the **same connection**:

1. F0 is made durable and F2 is entered on a real catalog;
2. the capacity provider reads `SELECT COUNT(*) FROM census_accession_registrants` at each sampling
   point, from inside the open transaction, and the count is seen to **climb from zero**;
3. the moment it is non-zero the provider returns `<= 10` GiB;
4. `F2CapacityHardStopError` propagates out of `transaction()`;
5. afterwards `in_transaction` is `False` and the row count is **`0`**.

The control run — identical, with capacity holding — commits its rows, so the empty table proves a
rollback rather than a projection that never wrote anything. The measurement-failure case is proved
the same way, and the `ALERT` case is proved to record its observation and **complete normally**. At
the run level, a hard stop leaves **no result document** and no finalized world.

## 10. The live read-only preflight

Run once against the attached qualified volume. **Read-only: nothing was created, written, deleted,
ejected, or benchmarked, and the `104` GB tar was not opened** — proved by a tripwire over `open`.

| Check | Result |
|---|---|
| mount present | `/Volumes/SSK SSD` |
| **Volume UUID** | `397A4D4A-9508-391E-814E-3B533C7BD049` — **exact match** |
| filesystem / device | `exfat` / `disk4s2` (recorded, **not** used as identity) |
| mount point, derived by `st_dev` walk | `/Volumes/SSK SSD` |
| D130 archive present | yes, **`24` entries** |
| archive compact precheck | **no differences**, `0.133` s; tar `103,966,696,960` B by `stat`, **not opened** |
| free on that volume | **`310,498,951,168` B / `289.1747` GiB** |
| against `185` GiB / `60` GiB / `55` GiB | **PASS / PASS / PASS**; launch surplus `111,856,713,728` B |
| classification: proposed work root | **external** |
| classification: archive child | **external** |
| classification: home directory | **internal** |
| **external root, NO FLAG, `SQLITE_TMPDIR` unset** | **REFUSED** — the envelope activated without being asked |
| **archive child, NO FLAG** | **REFUSED** |
| **volume root (contains the archive), NO FLAG** | **REFUSED** |
| external root, arbitrary asserted UUID | **REFUSED** |
| external root, internal `SQLITE_TMPDIR=/tmp` | **REFUSED** — the internal volume's UUID reported, not the qualified one |
| internal root, no flag | **`None`** — no envelope, the accepted Decision 116 path |
| proposed work root / temp root created | **no** — both absent afterwards |
| canary world on the volume | **none** |

The four no-flag refusals are **MAJOR-1's correction, live**: under Decision 137 every one of them
was an admission. Free space is byte-identical to the reading Decision 137 §18 recorded.

**The live `SQLITE_TMPDIR` directory was still not created**, because creating it is a write to the
volume and this stage authorizes none. The envelope's **accepting** path therefore remains proved
**synthetically**; only its **refusing** paths ran live.

## 11. A recorded erratum, not corrected in place

Decision 137 §12 states that *"four of the twelve are mechanically verified and eight are not"*.
The runbook table it describes marks **five** conditions as preflight-verified — the volume UUID,
the archive precheck, the `185` GiB floor, archive isolation, and `SQLITE_TMPDIR` placement — and
**seven** as operator or launch-command responsibilities. **The correct counts are five and
seven.**

`Docs/m3/operator_runbook.md` §28d now states them explicitly and correctly. **Decision 137 §12 is
left byte-unchanged**, because this record does not rewrite D137's history; the erratum is recorded
here instead.

## 12. Limitations, stated rather than smoothed

- **`macos_volume_identity` is macOS-only**, unchanged from D137. It shells to `diskutil`; on any
  other platform the lookup fails, and failing closed means the external mode **refuses** rather
  than degrading.
- **The classifier is a mount-point test, not a device-class test.** A disk image, a network mount,
  or any other non-system volume classifies as **external** and must then authenticate as the D136
  volume — which it will not. That is fail-closed and intended, but it is a broader net than "USB
  disk", and a future internal-volume topology change would be classified on its device numbers
  rather than on what it is.
- **The `SQLITE_TMPDIR` guard validates placement, not peak.** Unchanged from D137: peak spill is
  recorded at phase boundaries when a run takes them, is not bounded in advance, and D136-R5 left
  it unmeasured.
- **`DURING_F2` sampling is bounded, not instantaneous.** A `5` s interval means free space can
  fall below the floor and be observed up to one interval later. The floor is an emergency floor
  with `20` GiB of alerting above it, so the gap is covered by design rather than by luck — but the
  guarantee is "sampled at least this often", never "detected the instant it happens".
- **No live end-to-end rehearsal was performed**, unchanged from D137, because that would require
  creating a world on the volume. The envelope's accepting path is proved synthetically and by its
  live refusals.
- **The rollback proof runs on a small synthetic catalog.** It proves the mechanism — mutation
  inside the transaction, absence after it — on tens of rows rather than tens of millions. Nothing
  about the mechanism scales differently, and nothing about the run time was measured or
  extrapolated.
- **`CensusOrchestrator._parse_bulk` remains an open PRE-NETWORK blocker**, deliberately unrepaired
  and not touched here.

## 13. What did not change

- **D129-R2** — every D128 semantic count remains rejected. **D129-R8** — from scratch, new world,
  new run identity. **D129-R12** is not discharged.
- **The `185` GiB launch floor, the `50` GiB `PRE_F2` floor, the `20` GiB alert, and the `10` GiB
  hard floor** — every one of them keeps its accepted value. **The `30` GiB behaviour has no
  reachable path.**
- **D137's independently verified behaviour is preserved and not opportunistically refactored**:
  `--work-root` as the sole root-selection surface, structured plist volume identity, exact UUID
  semantics, no `disk4`/`disk4s2` identity dependence, `realpath` archive comparisons, D127
  ordering, D131 runtime configuration, the D130 compact-proof precheck with the tar never opened,
  the ExFAT claim limitations, the operator physical-condition assertions, D134's `mmap` and
  relaxed-checkpoint rejections, and internal backward compatibility.
- **No migration** — head remains `0015`, `0016` absent, unapplied, not authorized.
- **All three activation constants remain `None`**; network, SEC, and HTTP remain unauthorized at
  request ceiling `0`.
- **D125-R3 stands; D125-R4 stands as the general rule**, narrowed only by D136-R8.

## 14. What this record does not authorize — D138-R13

It creates **no** canary world, run identity, execution namespace, launch receipt, or terminal
state; authorizes **no** corrected complete-source canary and **no** canary of any kind; authorizes
**no** E0, **no** migration `0016`, and **no** network at request ceiling `0`; adopts the external
volume **not at all**; and certifies **no** semantic count. **It claims no owner acceptance, for
itself or for Decision 137.**

## 15. The next authorized action

**Independent review of this correction, and nothing else.** After that, an owner decision on
whether to accept Decision 137 as corrected by Decision 138 — and, separately and only then,
whether to authorize the corrected canary.
