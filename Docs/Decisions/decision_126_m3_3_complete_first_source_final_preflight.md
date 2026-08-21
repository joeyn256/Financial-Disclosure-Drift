# Decision 126 — The Complete First-Source Final Live Preflight

```text
STATUS: ACCEPTED — OWNER RULING, CLOSED
RECORD_TYPE: OWNER ACCEPTANCE OF A COMPLETED READ-ONLY PREFLIGHT —
  A RETROSPECTIVE DURABLE RECORD, PUBLISHED AFTER THE PREFLIGHT
DATE: 2026-08-20
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
OUTCOME: M3_3_D126_COMPLETE_SOURCE_PREFLIGHT_OWNER_ACCEPTED
VERDICT: NOT_READY_IMPLEMENTATION_GAP
SCOPE: THE FINAL LIVE COMPLETE-FIRST-SOURCE PREFLIGHT AND ITS VERDICT — NOT AN
  IMPLEMENTATION, NOT A CAPACITY MODEL, AND NOT AN EXECUTION AUTHORIZATION
DISCHARGES: the Decision 125 sections 11 and 13 (D125-R7) final-live-preflight requirement,
  the Decision 125 section 10 (D125-R8) residue-check requirement, and the Decision 124
  section 4 stored-object naming reconciliation that Decision 125 section 12 carried forward
AUTHORIZES: exactly one later D127 minimal pre-F2 admission-guard implementation stage
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_V3_EXECUTION_AUTHORIZATION: NO
F1_EXECUTION_AUTHORIZATION: NO
F2_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
DISPOSABLE_WORLD_CREATION_AUTHORIZATION: NO
FURTHER_DELETION_AUTHORIZATION: NONE
CATALOG_WRITE_AUTHORIZATION: NONE
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The final live M3.3 complete-first-source preflight that
[Decision 125](decision_125_m3_3_external_archival_and_reclamation.md) §13 (D125-R7) made a
precondition of any complete-source authorization, and whose §10 residue check D125-R8 required.

## 1. What this record is, and what it is not

**It is a retrospective durable record of a completed READ-ONLY preflight.** The preflight had
already run when this file was written. **This file did not exist before it and did not authorize
it**; the authorizing instrument was the GPT-5.6 Sol owner instrument issued at the time. Nothing in
this publication executed, created, wrote, moved, or deleted anything.

**The verdict is `NOT_READY_IMPLEMENTATION_GAP`, and the shape of that verdict matters more than the
word `NOT_READY`.** Four things must be read together, and none of them may be read alone:

1. **This is NOT a live-state failure.**
2. **Every live-state predicate PASSED.** Disk, source identity, catalog identity, migration head,
   plan state, residue — all of it. §§3–6 record the measurements.
3. **Complete-source execution did NOT occur.** No F1, no F2, no canary, no world, no E0.
4. **Complete-source execution remains UNAUTHORIZED**, and this record does not authorize it.

**The blocker is a missing guard in this repository's own source, not a condition of the machine.**
[Decision 124](decision_124_m3_3_capacity_reconciliation.md) §9 (D124-R5) requires a `>= 30 GiB`
free-space check taken *immediately before opening F2*. The complete-source path does not contain
one. §7 records why no external process can supply it, and D126-R6 authorizes the one later stage
that will.

**It is not an implementation.** No production source, test, schema, migration, configuration, or
authority constant changed in this publication. The guard §7 describes is **authorized, not
written**, and the record's own publication does not write it.

**It is not a capacity model.** The [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §8
model is unchanged. §4 reports *measured* live state against the D124-R5 gates rather than revising
them.

## 2. Entry state

Branch `main` at published `2bb05ff712030f825b7e7824211186a27b7fa3c8`, tree
`66cc009301b796dd5470adf51f7afd53f7f9e705`, `origin/main` identical at `0`/`0` and the worktree
clean, with governance published through Decision 125. Migration head `0015`; migration `0016`
absent and unapplied; no E0-v3 namespace; all three activation constants —
`M3_3_E0_EXECUTION_AUTHORITY`, `PRE_E0_CATALOG_TRANSITION_AUTHORITY`, and
`STALE_WRITER_LEASE_RECOVERY_AUTHORITY` — `None` in `src/disclosure_drift/m3/e0.py`; both tracked
network switches `false` in `configs/project.yaml` at request ceiling `0`.

Every one of those predicates was verified at publication and still holds. **This record changes
none of them.**

## 3. What the preflight was, and what it touched

**It was read-only throughout.** It opened no writer, created no run world, consumed no namespace,
applied no migration, made no request, and changed no byte of catalog, source, or evidence. It
measured, and it stopped.

**It answered the D125-R7 question in the only order that is sound**: measure live state first, then
measure the repository's ability to *honour* the gates that state has to be defended by. The first
half passed completely. The second half is where the verdict comes from.

## 4. Accepted live readiness

### 4.1 Free space

| Measurement | Bytes | GiB |
|---|---:|---:|
| entry free | `137,633,968,128` | `128.1816` |
| exit free | `136,576,831,488` | `127.1971` |
| consumed by the preflight itself | `1,057,136,640` | `0.9845` |

| Threshold | Bytes | Entry | Exit |
|---|---:|---|---|
| **formal gate `>= 105 GiB`** (D124-R5) | `112,742,891,520` | **PASS** | **PASS** |
| owner *preference* `>= 110 GiB` (D125-R6) | `118,111,600,640` | **PASS** | **PASS** |

**Both readings clear both levels, and the margin is not marginal**: exit free stands
`23,833,939,968` bytes = `22.1971 GiB` above the formal gate and `18,465,230,848` bytes =
`17.1971 GiB` above the preference. The `110 GiB` level is reported because the owner preferred it
and it was reached — **it remains a preference and is still not a second gate** (D125-R6).

**The Decision 125 §9 shortfall is closed by measurement.** D125 settled at `104,500,830,208` bytes
= `97.3240 GiB` and recorded a **remaining hard gap of `8,242,061,312` bytes = `7.6760 GiB`**. Entry
free is `33,133,137,920` bytes = `30.8576 GiB` above that settled figure. The gap was closed from
ordinary non-project storage, as D125-R3 required, and **no further Disclosure Drift evidence was
deleted for capacity**.

**`0 GiB` of material stale pytest scratch remained.** The known accumulation pattern — full
validation runs leaving multi-gigabyte scratch in the system temporary directory — was checked and
was not present.

**One measurement condition is published rather than smoothed**, following the Decision 125 §9
precedent. A publication-time re-read returned `136,511,447,040` bytes = `127.1362 GiB`, about
`65 MB` (`0.0609 GiB`) below the recorded exit figure — ordinary drift on a live APFS volume.
**All three readings clear both the gate and the preference, so the conclusion is identical under
any of them.**

### 4.2 The frozen source

```text
sec_bulk_submissions-c85744be921b0dc5.zip
```

| Property | Value |
|---|---|
| bytes | `1,556,847,020` |
| SHA-256 | `c85744be921b0dc5be4e3c7dd44552fc0f57d354d61df38cd92a13926982b82f` |
| raw ZIP entries | `985,835` |
| governed JSON members | `985,834` |
| non-JSON entries | exactly one — `placeholder.txt` |

The governed member count `985,834` is the [Decision 124](decision_124_m3_3_capacity_reconciliation.md)
§4 (D124-R1) **final controlling** count, and this preflight measured the same value against the
same physical object. The single non-JSON entry is the same `placeholder.txt` D124 §4 recorded, so
the governed-member rule is unchanged and the `985,835` / `985,834` difference is that one file and
nothing else.

### 4.3 The operational catalog

| Digest | Value |
|---|---|
| file SHA-256 | `57e36a788dc8e03ea4d1a4c722418de4c4244d73590c6643feace93c80af2ded` |
| logical digest | `5c823d216957c0035babd4956f9d9e0c3c0b8ea54455231436a514191c6ad306` |
| observation-set digest | `b1122bb9fbb084411ce3cb3b7d192c7874c8969aadbb29f6ca313543b8e533be` |

| Predicate | Measured |
|---|---|
| migration head | `15` |
| plan sources | `76` |
| parser states | **all `not_started`** |
| E0 parser / accession / record materialization residue | **zero** |

**The logical and observation-set digests are the same values the interrupted-E0 chain recorded**,
which is the point of measuring them: the catalog is in the state the governance record says it is
in, and no partial E0 work is sitting in it. `76` plan sources all `not_started` and zero
materialization residue together mean **the complete-source path would start from a clean state, not
resume into one**.

## 5. Source-pointer reconciliation — D126-R4

**This discharges the [Decision 124](decision_124_m3_3_capacity_reconciliation.md) §4 obligation that
[Decision 125](decision_125_m3_3_external_archival_and_reclamation.md) §12 explicitly carried forward
rather than closed.**

**The current plan selects exactly one source, and the selection is single-valued:**

| Field | Value |
|---|---|
| `census_plan_sources.observation_id` | `09fdacf651ba4d0a80f5d2ab4e36f4a3` |
| archive | `sec_bulk_submissions-c85744be921b0dc5.zip` |
| governed member rows | `985,834` |

**Decision 059's older August-07 object reference remains HISTORICALLY CORRECT, and Decision 059 is
not amended.** [Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md)
§3 named the object that was stored *then*. It was right about what it named. The later object is a
different SEC snapshot, which is exactly what D124-R1 already established when it ruled the older
`985,479` count `SUPERSEDED-BY-OBJECT` rather than erroneous. **A record that correctly describes an
earlier state is not corrected by a later state arriving.**

**The runtime authority is the pointer, not the prose.** What selects the source at execution time is
the single-valued `census_plan_sources.observation_id` together with its corresponding member rows —
not any narrative naming in a governance record. **There is exactly one such pointer, it resolves to
exactly one archive, and that archive carries exactly `985,834` governed member rows.** That is what
makes the current state runtime-unambiguous, and it is the substance of D126-R4.

**One confirming property is recorded because it makes the naming self-verifying.** The object name's
identifier `c85744be921b0dc5` is the **first sixteen hexadecimal characters of the object's own
SHA-256**, `c85744be921b0dc5be4e3c7dd44552fc0f57d354d61df38cd92a13926982b82f`. D124 §4 published,
correctly, that this identifier appeared in **no tracked record before Decision 124**. It is now also
recorded that the identifier is *derived from the content it names*, so the pointer and the bytes
verify each other without reference to any document.

**One nonblocking limitation is recorded rather than repaired.** The controlling August-11 observation
carries **no explicit `supersedes_observation_id` edge** to the August-07 observation. The
supersession is therefore true in substance and unrecorded as a link.

**That absence does not affect runtime correctness**, because selection reads the single-valued
pointer and never walks a supersession chain. **It authorizes no catalog write.** It is a
documentation-level limitation of the observation graph, carried as such — **not** grounds for
opening a writer against the operational catalog to add an edge.

## 6. Historical namespaces and the released lease — D126-R3

**This is the [Decision 125](decision_125_m3_3_external_archival_and_reclamation.md) §10 (D125-R8)
residue check, performed as required.**

**Both historical namespaces remain present and consumed:**

```text
m3_3_e0_offline_parse_v1
m3_3_e0_offline_parse_v2
```

**No `v3` exists.** Their presence is historical residue of consumed generations, **not a new E0
namespace and not an available one** — a consumed namespace is spent. **They are structurally
irrelevant to the canary path**, which neither reads nor writes them.

**The lease is `released`, and that is the finding:**

| Field | Value |
|---|---|
| `state` | **`released`** |
| `lease_id` | `3a37a7ee0e0c4496a4fba845d4d5d2a1` |
| `writer_pid` | `68482` — **dead** |
| `released_at_utc` | `2026-08-18T01:44:33.497032Z` |
| file SHA-256 | `8c0f251f03c3c113dea7ab59f7c542a02721d6246eefd9b35cf21227019db29b` |

**The advisory lock was available.**

**Owner ruling D126-R3: the former stale-*held* lease condition is ABSENT.** The condition that
Decisions 102 through 107 were built to reconcile — a persisted lease recording `state = held` for a
dead writer — **does not exist here**. This file records a *voluntary release* that already
completed, carries `released_at_utc`, and names a dead PID that is dead because its work finished and
released. It is **irrelevant historical residue for this canary**.

**No recovery authority and no recovery action is required**, and `STALE_WRITER_LEASE_RECOVERY_AUTHORITY`
stays `None`. **Do not modify the lease file.** A `released` lease is not a defect to clean up; it is
the correct terminal state of a writer that exited properly, and rewriting it would destroy evidence
to no purpose.

## 7. The implementation gap — the sole blocker

**This is the entire reason the verdict is not `READY`.**

**The current complete-source path is, in order:**

```text
F1   catalog.count_persisted_accession_resolutions(...)
F2   materialize_census_associations(...)
```

in `src/disclosure_drift/m3/single_source_canary.py`, where the F2 call is the **statement
immediately following** the F1 call. **There is no `>= 30 GiB` disk admission predicate between F1's
return and F2's transaction opening.** [Decision 124](decision_124_m3_3_capacity_reconciliation.md)
§9 (D124-R5) requires that check to be **taken immediately before opening F2**, explicitly *not*
inherited from the starting gate.

**An external sampler cannot satisfy the owner predicate.** This is not a matter of sampling often
enough. Four independent reasons, each sufficient on its own:

1. **No enforceable pause exists at the boundary.** F1 returns and F2 begins in consecutive
   statements. There is no window an outside process can occupy.
2. **Ledger state does not distinguish F1 from impending F2.** Nothing durable changes at the
   boundary, so an observer cannot tell "F1 finished" from "F2 is about to open" by reading state.
3. **An external process can signal but cannot decline admission atomically.** Admission is a
   decision that must be made *inside* the path that is about to open the transaction. A signal is
   advisory; the predicate must be dispositive.
4. **A sampling race remains regardless of cadence.** Free space measured at any instant before the
   call is a measurement of a different instant than the one that matters. Tightening the interval
   shrinks the race; it never closes it.

**Owner ruling D126-R6 authorizes a subsequent, separate D127 implementation stage containing ONLY:**

1. **one frozen `30 GiB` constant**;
2. **one free-space guard**, placed after F1 returns and before F2 is called;
3. **three focused tests** —
   - below the floor **refuses**,
   - at or above the floor **admits**,
   - ordering proves the **guard executes before F2**.

**No implementation occurs in this publication.** D127 is authorized; it is not performed here, and
this record's own publication writes no guard, no constant, and no test.

## 8. The other D124-R5 safety requirements — D126-R5

**Only one of the five requires a repository change.** Recording the other four as already-satisfied
is not a relaxation of D124-R5; it is the reason D127's scope is one guard rather than a programme.

| D124-R5 requirement | Disposition |
|---|---|
| start `>= 105 GiB` | **enforceable by the launch wrapper** — no production code change |
| continuous `10 GiB` floor during interruptible phases | **enforceable by monitor / wrapper** — no production code change |
| **`>= 30 GiB` measured immediately before F2** | **REPO CHANGE REQUIRED — the sole blocker** (§7) |
| **no `VACUUM`** | **already implemented by construction** — the path issues none |
| SQLite temporary placement, explicit | **wrapper-enforceable with `SQLITE_TMPDIR`** — no production code change |

**Owner ruling D126-R5 fixes the temporary directory, and fixes it as a sibling:**

```text
<work-root>/<run-id>__sqlite_tmp/
```

**and expressly NOT `<world>/tmp`.** The reason is a real constraint rather than a preference:
**precreating `<world>/tmp` violates the world's create-once semantics.** The disposable run world is
created once, whole, by the path that owns it; a wrapper that reaches in and materializes a directory
inside it beforehand has already written into a world that is supposed to be created rather than
found. A **sibling** directory places the temporary space on the same volume — which is what the
accounting requires — without touching the world at all.

**No code change is required for temporary placement.** `SQLITE_TMPDIR` is set by the wrapper.

## 9. Power, runtime, and monitoring — D126-R7

**AC power was confirmed before the preflight completed.**

**A future run requires an explicit per-process no-sleep assertion.** Current settings are
`sleep=1` and `disksleep=10`, which makes the assertion necessary rather than merely prudent — a
system sleep during a non-resumable run destroys the run.

**The accepted wrapper concept is:**

```text
caffeinate -i -m -s
```

**Persistent `pmset` settings must not be altered.** The assertion is scoped to the process that
needs it and expires with that process; changing the machine's standing power policy to serve one run
is a durable change made for a temporary reason.

**Owner ruling D126-R7: there is NO arbitrary wall-clock kill ceiling.**

**The planning envelope is a planning envelope, and is not a deadline:**

| Case | Envelope |
|---|---|
| optimistic | about `15 h` |
| central | about `24 h` |
| possible | about `34 h+` |

**Actual health, progress, and resource monitoring controls** — not the clock. **The run is not
resumable**, so **elapsed time alone is not a valid kill criterion**: killing a healthy run at an
arbitrary hour destroys all of its work and buys nothing, while a run that is genuinely unhealthy is
identifiable from progress and resource behaviour long before any clock threshold would fire.

## 10. The proposed command is not frozen — D126-R8

**The command the technical preflight proposed was NOT executed.**

**Owner ruling D126-R8: the proposed run ID**

```text
m3_3_d126_complete_first_source_v1
```

**and its command are NOT frozen for eventual execution**, because **D127 will change the published
code baseline**. A frozen command identifies a run against a specific tree; freezing one now would
name a tree that is about to stop existing.

**The final run identity and command must be regenerated after both:**

1. **D127 implementation acceptance**, and
2. **a new final live preflight.**

Neither has occurred. **Nothing in this record may be cited as a frozen command contract.**

## 11. Owner rulings D126-R1 – D126-R9

| Ruling | Content |
|---|---|
| **D126-R1** | **The verdict `NOT_READY_IMPLEMENTATION_GAP` is ACCEPTED.** It is **not** a live-state failure: every live-state predicate passed (§§4–6). Complete-source execution did not occur and remains unauthorized. |
| **D126-R2** | **Live disk and readiness state PASSES**, at `128.1816 GiB` entry and `127.1971 GiB` exit against the `105 GiB` gate and the `110 GiB` preference. **No additional storage cleanup is required now.** |
| **D126-R3** | **The released-lease residue is NONBLOCKING and requires no recovery action.** The former stale-*held* condition is **absent**; the current file is irrelevant historical released residue for this canary. Do not modify it. |
| **D126-R4** | **The current source pointer is runtime-unambiguous** — single-valued `census_plan_sources.observation_id` `09fdacf651ba4d0a80f5d2ab4e36f4a3` plus its `985,834` governed member rows. **[Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md) remains historically correct and is NOT amended.** The absent `supersedes_observation_id` edge is accepted as a **nonblocking documentation limitation** that authorizes no catalog write. |
| **D126-R5** | **`SQLITE_TMPDIR` uses a sibling run-temp directory** `<work-root>/<run-id>__sqlite_tmp/`, **not** `<world>/tmp`, because precreating `<world>/tmp` violates create-once world semantics. **Wrapper enforcement is sufficient**; no code change is required. |
| **D126-R6** | **A later D127 minimal pre-F2 admission-guard implementation is AUTHORIZED**, scoped to exactly one frozen `30 GiB` constant, one guard between F1's return and F2's call, and three focused tests. **No implementation occurs in this publication.** |
| **D126-R7** | **No arbitrary wall-clock kill ceiling.** The `15 h` / `24 h` / `34 h+` figures are a **planning envelope only**; resource and progress monitoring controls. The run is **not resumable**, so elapsed time alone is not a valid kill criterion. |
| **D126-R8** | **D126's proposed run identity `m3_3_d126_complete_first_source_v1` and its command are NOT final**, because D127 changes the code baseline. Both must be **regenerated** after D127 acceptance **and** a new final live preflight. |
| **D126-R9** | **Complete source is NOT authorized. E0 is NOT authorized.** |

## 12. What this record does not do

**It authorizes no execution** (D126-R9). No complete-source run, no E0, no E0-v3, no F1, no F2, no
full-population F2 rerun, no D117 retry, no three-source canary, no real replay proof, no canary of
any kind, no disposable run world, no migration `0016`, no network, and no acquisition. **Passing
every live-state predicate is not an authorization** — it is a measurement, and D125-R7 already said
that crossing a threshold authorizes nothing by itself.

**It implements nothing.** The §7 guard is **authorized for D127 and not written here**. No
production source, test, schema, migration, configuration, or authority constant changed in this
publication, and no capacity constant moved.

**It writes nothing to the catalog, the source, or the evidence root.** The §5 missing supersession
edge is recorded as a limitation precisely so that it is not repaired by a write; the §6 lease is
left exactly as found.

**It supersedes nothing.** Decisions 121 through 125 stand as written, and the D124-R5 gates carry
forward intact — **including** the `>= 30 GiB` pre-F2 gate, which §7 records as *unenforced by code*
rather than as relaxed. **The gate is not weakened by being unmet; that is what makes it the
blocker.**

**It freezes no command** (D126-R8).

**All three activation constants remain `None`**, the operational catalog remains at migration head
`0015`, migration `0016` remains absent and unapplied, no E0-v3 namespace exists, and both tracked
network switches remain `false` at request ceiling `0`.

**The next stage is D127** — the minimal pre-F2 admission-guard implementation authorized by D126-R6,
and nothing beyond it. **Complete source is NOT authorized. E0 is NOT authorized.**
