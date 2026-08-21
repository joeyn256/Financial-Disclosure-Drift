# Decision 124 — Capacity Reconciliation, and the 105 GiB Complete-First-Source Floor

```text
STATUS: ACCEPTED — OWNER RULING, CLOSED
RECORD_TYPE: OWNER ACCEPTANCE OF A CAPACITY RECONCILIATION — WITH ONE PUBLISHED CORRECTION
DATE: 2026-08-20
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
OUTCOME: M3_3_D124_CAPACITY_RECONCILIATION_OWNER_ACCEPTED_WITH_CORRECTION
SCOPE: COMPLETE FIRST SOURCE ONLY — NOT 76-SOURCE E0 CAPACITY EVIDENCE
SUPERSEDES: the Decision 121 §7 `>= 85 GiB` floor — RETIRED, not suspended; and the
  Decision 112 §6 about-`132.5 GB` figure AS CURRENT PLANNING CAPACITY ONLY
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_V3_EXECUTION_AUTHORIZATION: NO
F1_EXECUTION_AUTHORIZATION: NO
F2_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
ARCHIVAL_EXECUTION_AUTHORIZATION: NO — A SEPARATE D125 INSTRUMENT IS REQUIRED
DELETION_AUTHORIZATION: NONE
EXTERNAL_VOLUME_ACTIVE_SQLITE_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The capacity and model reconciliation
[Decision 123](decision_123_m3_3_f2_bounded_characterization.md) §9 deliberately left open, and
which its R74 and R75 named as the D124 obligation.

## 1. What this record is, and what it is not

**It is a capacity reconciliation.** It closes both Decision 123 §9 conflicts, retires two figures
from current planning, sets the complete-first-source free-space gate, and approves an external
volume in principle for archival use.

**It is not an execution authorization of any kind.** No complete source, no E0, no F1, no F2, no
canary, no archival copy, no deletion, no migration `0016`, no network. **A record that resolves a
capacity question is not a grant to spend the capacity.** The next technical stage — D125, archival
plus verified internal reclamation — is sequencing, not authorization, and is not started here.

**Every figure in §8 is a planning estimate, not a complete-source observation.** The complete first
source has never been run. Nothing below may be cited as measurement of one.

## 2. Entry state

Branch `main` at published `b1200fae377abea3f90c1f6c4456aa9e356295b8`, tree
`02fbd4212f99fa07f3ee8759db54a22dd8fc672d`, `origin/main` identical at `0`/`0` and the worktree
clean, with governance published through Decision 123. Migration head `0015`; migration `0016`
absent; no E0-v3 namespace; all three activation constants — `M3_3_E0_EXECUTION_AUTHORITY`,
`PRE_E0_CATALOG_TRANSITION_AUTHORITY`, and `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` — `None` in
`src/disclosure_drift/m3/e0.py`; both tracked network switches `false` in `configs/project.yaml` at
request ceiling `0`.

The preserved worlds at entry were the D117 world, the D120 world, the D122 F1 working catalog, and
the D123 disposable characterization residue, all immutable per Decision 123 R76 and R77. **They
remain so. This record deletes nothing and authorizes no deletion** — see §11 and §16.

## 3. The governance namespace

Decision 123 §10 published a numbering condition rather than silently fixing it, and named its
resolution a D124 governance question. This section resolves it prospectively.

| ID | Ruling |
|---|---|
| **D124-G1** | **[Decision 094](decision_094_m3_3_pre_e0_executability_redesign.md) R70–R78 and Decision 123 R70–R78 are both historically immutable.** Neither is renumbered, rewritten, or withdrawn. |
| **D124-G2** | **Every future reference to a colliding ID must be decision-qualified** — "Decision 094 R72" or "Decision 123 R72", never a bare `R72`. |
| **D124-G3** | **From Decision 124 onward, new owner rulings use decision-scoped IDs**: `D124-R1`, `D124-R2`, and so on. The collision class is closed going forward rather than repaired backward. |

**Decision 094 and Decision 123 are not renumbered.** The collision is a permanent historical fact
of those two records, and D124-G2 is how it is navigated rather than erased.

## 4. Conflict A — closed: the governed member count

Decision 123 §9.1 recorded two counts and ruled `985,834` **provisional** pending a D124 trace. The
trace is complete, and it is a physical-object trace rather than a code defect.

| Physical archive | Raw entries | Governed JSON members | Non-JSON |
|---|---|---|---|
| older — `sec_bulk_submissions-9ca4642200dbcc45.zip` | `985,480` | **`985,479`** | one `placeholder.txt` |
| current controlling — `sec_bulk_submissions-c85744be921b0dc5.zip` | `985,835` | **`985,834`** | one `placeholder.txt` |

**The difference of `355` members is caused by two different SEC snapshot objects — not by a filter,
a parser, or a code discrepancy.** Both archives carry exactly one non-JSON `placeholder.txt`, so
the governed-member rule is identical across them and the raw-entry difference of `355` is the same
`355`. The older `985,479` basis is [Decision 111](decision_111_m3_3_e0_bounded_persistence_and_working_catalog.md)
§5 and [Decision 112](decision_112_m3_3_compact_e0_evidence_contract.md) §6; the current `985,834`
basis is real D117/D120 enumeration and
[Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md) §7.

**Owner ruling D124-R1: `985,834` is the FINAL controlling governed deterministic member count for
the frozen current source. `985,479` is `SUPERSEDED-BY-OBJECT`, not erroneous.** It was a correct
count of a different object. Decision 111 and Decision 112 are not rewritten, and neither is wrong
about what it measured.

**One navigation condition is published rather than silently fixed.** The identifier
`c85744be921b0dc5` appears in **no tracked repository record before this one**, while
[Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md)
§3 names `sec_bulk_submissions-9ca4642200dbcc45.zip` as the stored raw object. Decision 110 §7 does
not name an archive by hash — it records "the real first planned source", a 1.56 GB ZIP holding
`985,834` JSON members, which is the count D124-R1 makes final. **Reconciling the stored-object
naming in the tracked records is not something this publication does**; it is an obligation the
D125 archival instrument carries, alongside D124-R8.

## 5. Conflict B — closed: the storage contract

Decision 123 §9.2 recorded two storage bases and chose neither. They are not contradictory
predictions of one implementation — **they are successive evidence contracts**, and reading them as
rival estimates of the same thing was the error.

| Record | Contract | What it compacts |
|---|---|---|
| Decision 112 §6 — about **`132.5 GB`** | `e0-compact-evidence/1` | the observation layer; **the resolution layer is still uncompacted** |
| [Decision 113](decision_113_m3_3_compact_derived_e0_evidence.md) §15 and §19 | **`e0-compact-evidence/2`** | `/1` **plus** the resolution and derived evidence layers |

The about-`132.5 GB` figure is Decision 112 §6's `21,500,264 x 6,160.9 B` projection for source 1
under `/1`. Decision 113 §4 is what changed the shape: a resolution whose complete governed content
is a deterministic pure function of already-persisted canonical evidence is **not written**. The
later figure is smaller because the contract writes less, not because the estimate was revised.

**Owner ruling D124-R2: retire the Decision 112 §6 about-`132.5 GB` figure from future capacity
planning. `e0-compact-evidence/2` — Decision 113, as calibrated by
[Decision 118](decision_118_m3_3_read_only_performance_diagnosis.md) and by the later real D120,
D122, and D123 evidence — is the controlling storage contract.**

**Decision 112 is not retired as historical evidence.** Only its use as *current planning capacity*
is retired; the record, its measurements, and its `/1` verdict stand as what they were. The
Decision 118 §5 (R24) `STRAINED BUT NOT INVALIDATED` finding — real prefix density about `+28.2%`
above the accepted submissions density — remains a calibration input to `/2`, not a refutation of
it, and Decision 118 §5's statement that no Decision 113 capacity constant changes still holds:
**`src/disclosure_drift/m3/capacity_plan.py` is untouched by this record.**

## 6. The accession population

**Owner ruling D124-R3: the central planning value is `21,508,823` distinct accessions, within a
planning band of `21.50 M` – `21.55 M`.**

**This is a capacity/model input, not a completed-source observation.** No complete source has been
run, and no enumeration of `21,508,823` distinct accessions exists. Decision 112 §6's `21,500,264`
— derived from the `985,479` object's totals at a measured distinct-accession ratio of `0.97759` —
sits inside the band, which is why the band rather than a point value is what governs.

## 7. The F1 interpretation correction — the one error published rather than inherited

**The D124 technical review contained one arithmetic/interpretive error. It is corrected here, and
the incorrect claim is not published as a finding.** This section exists because a durable record
that quietly adopted the reviewer's reading would have carried a `61.8%` figure that means something
entirely different from what it appeared to mean.

[Decision 122](decision_122_m3_3_d120_f1_finalization_characterization.md) §5 measured, over one F1
pass on the D120 clone:

| Term | Measured |
|---|---|
| accessions | `8,258,521` |
| field-resolution rows | `5,104,568` |
| cohort-resolution rows | `638,071` |

**The correct quotients:**

- `638,071 / 8,258,521 = 0.077262` — **approximately `7.73%`**. This is the explicit-accession
  fraction.
- `5,104,568 / 8,258,521 = 0.618097` — **approximately `0.618`**. This is **field-resolution *rows*
  per accession**, because one explicit accession can emit **multiple** field rows. It is a
  rows-per-accession ratio and **not a percentage of accessions**.

**The reviewer read the second quotient as the first**, and concluded that `61.8%` of accessions
were explicit. **That claim is wrong by roughly a factor of eight and is not published.** Three
consequences follow, each stated as a prohibition:

1. **Do not publish the claim that `61.8%` of accessions were explicit.** The measured
   explicit-accession fraction is about `7.73%`.
2. **Do not claim the tail is proven to become more implicit.** That inference rested entirely on
   the mistaken `61.8%` reading; nothing in the D122 measurement establishes it.
3. **Do not characterize linear F1 byte extrapolation as necessarily "conservative-high" on that
   basis.** The basis does not exist. The extrapolation may or may not be conservative; this
   evidence does not say which.

**What survives the correction.** The measured linear F1 central projection remains useful, because
it rests on **actual measured bytes per accession** rather than on the resolution-mix inference the
error contaminated. Its usefulness was never derived from the `61.8%` reading.

**A term-label condition, recorded rather than resolved.** Decision 122 §5's table labels `638,071`
as **cohort-resolution rows**; the D124 owner instruction reads the same figure as
**explicit-resolution accessions**. **This record does not resolve which term is correct**, and the
correction does not depend on it: the numerator and denominator are unchanged under either reading,
so both quotients above hold as stated. A future record that needs the accession-versus-row
distinction at this layer must establish it rather than infer it from either label.

**Owner ruling D124-R4: the D124 phase model is accepted with this F1 interpretation corrected.**

## 8. The accepted current capacity model

**Recorded as planning estimates, not as complete-source observations.**

| Component | Central estimate |
|---|---|
| materialization durable state | about **`54.62 GB`** |
| compact sidecar | about **`0.27 GB`** |
| F1 durable growth | about **`9.40 GB`** |
| F1 wall | about **`1.33 h`**, bounded write-ahead log and resident set |
| F2 durable growth | about **`6.59 GB`** |
| F2 pre-checkpoint / pre-truncation write-ahead log | about **`9.52 GB`** |
| F2 wall | about **`2.04 h`**, resident set about `0.68 GiB` |
| **D124 technical review — central peak** | about **`75.27 GiB`** |
| **D124 technical review — conservative modeled peak** | about **`89.27 GiB`** |

**Scope: the complete FIRST SOURCE only. This is not 76-source E0 capacity evidence.** The
Decision 121 §5 limit carries unchanged: a first-source-shaped measurement is representative of the
first-source canary and of nothing larger, because full-index evidence is absent in both.

**A unit condition, stated rather than converted.** The component rows are stated in **`GB`** and
the peak rows in **`GiB`**, exactly as issued. **This record performs no conversion between them**,
because reconciling the units would itself be a capacity ruling. One consistency check is recorded
as arithmetic over the owner's own figures and nothing more: the four durable components sum to
`70.88 GB`, plus the F2 pre-checkpoint log gives `80.40 GB`, which is `74.88 GiB` — about `0.39 GiB`
below the stated `75.27 GiB` central peak. **The model is internally coherent at that resolution**;
the residual is not attributed to any named component here.

**Derived from the owner's figures, and labelled as derived:** F1 plus F2 wall time is about
`3.37 h` at the central estimates.

## 9. The capacity gates

**Owner ruling D124-R5 supersedes the reviewer's recommended `100 GiB` minimum.** The reviewer
recommended `100 GiB`; the owner ruled higher. The rulings below are the owner's, not the
reviewer's.

**HARD STARTING INTERNAL FREE-SPACE GATE: `>= 105 GiB` = `112,742,891,520` bytes.** The byte value
is exact: `105 x 1024^3 = 112,742,891,520`.

The additional margin over the reviewer's recommendation covers, in the owner's terms:

- corrected F1 uncertainty — §7 removed a claimed source of conservatism rather than adding one;
- the F2 `26x` extrapolation;
- APFS and background drift;
- unmeasured SQLite temporary-space behaviour.

**Derived from the owner's own figures:** `105 GiB` sits about `15.73 GiB` above the conservative
modeled peak and about `29.73 GiB` above the central peak.

**If about `110 GiB` can easily be staged, that is preferable additional headroom. It is not a
separate authorization predicate** — `105 GiB` is the gate, and `110 GiB` is neither a second gate
nor a condition.

**In-flight gates:**

| Gate | Value |
|---|---|
| continuous hard-stop floor, throughout the run | **`10 GiB`** |
| measured immediately before opening F2 | **`>= 30 GiB` free** |

**If less than `30 GiB` is free at that check, F2 must not begin.** The check is taken immediately
before opening F2, not inherited from the starting gate.

**Two further requirements:**

- **NO `VACUUM`.**
- **SQLite temporary storage must be explicitly placed and explicitly accounted for on the internal
  run volume** for the future complete-source run. It is not left to default placement, and its
  space is not assumed to be free.

**The Decision 121 §7 `>= 85 GiB` floor is SUPERSEDED, not merely suspended.** Decision 123 R74
suspended it pending this reconciliation; D124-R5 replaces it. It is retired as a planning floor and
may not be cited as one in either direction.

## 10. The external SSD

**Recorded as a D124 read-only discovery.** Nothing was written to it, and nothing was copied to it.

| Property | Observed |
|---|---|
| volume | `SSK SSD` |
| nominal capacity | `500 GB` |
| free at D124 observation | about `499.94 GB` / `465.61 GiB` |
| bus | USB SuperSpeed+, about `10 Gbps` visible |
| filesystem | **exFAT** |
| user-reported sequential capability | about `1050 MB/s` |

**The about-`1050 MB/s` figure is user-reported. It was not independently benchmarked, and this
record does not claim it was.**

**Owner ruling D124-R6: the SSD is approved IN PRINCIPLE as archival / cold-preservation storage.
Active SQLite use is NOT approved. Reformatting is NOT approved and is NOT required.**

**The next archival instrument must account explicitly for exFAT metadata limitations** — see
D124-R9.

## 11. Archival and retention requirements

**Owner ruling D124-R7 — what becomes eligible, and under what.** Eligible **under a later archival
instrument**, and not under this record:

- the **D117** world;
- the **D120** world;
- the **D122** post-F1 working catalog;
- the **D123** characterization residue;
- disposable performance experiment material.

**Only after external verification may their authorized internal copies be removed.** Verification
precedes removal; the ordering is the ruling, not a recommendation. **C3's retained about-`10 MiB`
evidence and its tiny diagnostics remain internally** and are not archival candidates.

**Owner ruling D124-R8 — the D122 catalog identity is not yet accepted.** The D122 post-F1 working
catalog **requires a fresh SHA-256 in the archival instrument.** The historical candidate carried in
the D123 completion report —

```text
fa4a635d36a487774e02670bb0fab1ded1c696b5e25faf54fb6f55b69799f413
```

— **is NOT yet to be treated as accepted durable identity.** The next archival instrument must:

1. **hash the actual preserved D122 catalog;**
2. **compare the result to the historical candidate above;**
3. **stop on mismatch** — this is a stop, not a discrepancy to record and continue past;
4. **record the resulting identity before any deletion.**

**Owner ruling D124-R9 — exFAT does not preserve all relevant POSIX metadata**, so the external
archive must carry an explicit cryptographic/metadata manifest, a metadata-preserving archive
container, or both. **At minimum, preserve:**

- relative paths;
- file types;
- exact bytes;
- SHA-256;
- original mode;
- original uid/gid, or owner/group names where meaningful;
- run / world ID;
- repository HEAD and tree;
- external archive destination;
- verification result.

## 12. Plan A arithmetic

Recorded as the clone-aware internal reclaim estimate, and as arithmetic rather than as a plan that
is authorized to execute.

| Quantity | Value |
|---|---|
| clone-aware internal reclaim estimate | about **`61.77 GiB`** |
| current D124 internal free | about **`36.70 GiB`** |
| projected after archival plus authorized internal cleanup | about **`98.46 GiB`** |
| **owner gate (§9)** | **`105 GiB`** |
| **gap** | about **`6.54 GiB` short** |

**Plan A does not satisfy the `105 GiB` gate.** That is the finding, and it is why archival alone
does not open a complete-source run.

**A rounding note, stated because capacity arithmetic is where rounding hides.** Summing the two
published rounded inputs gives about `98.47 GiB` against the stated `98.46 GiB` — a difference of
about `0.01 GiB` that changes no conclusion, since both fall about `6.5 GiB` short of the gate. The
owner's `98.46 GiB` is the recorded projection.

**Owner preference, recorded as preference:** free or move ordinary non-project data later, rather
than alter append-only project raw evidence merely to close a gap this small. **No non-project
deletion is authorized or performed by this publication**, and CLAUDE.md rule 6 — raw filings and
downloaded artifacts are append-only — is untouched by it.

## 13. The active governed volume

**Plan B is unnecessary on the current arithmetic and remains NOT APPROVED.**

**No categorical claim is made about whether SQLite can technically operate on exFAT.** The evidence
here does not support one in either direction, and the governance fact does not require one:

> **We do not need, and do not approve, the external SSD as the active governed SQLite volume.**

**The internal APFS Apple SSD remains the intended active working volume.**

## 14. Complete source and E0

**Owner ruling D124-R10: no complete-source authority arises from D124 alone.**

Before any complete-source authorization:

1. **archival must complete;**
2. **authorized internal copies must be reclaimed;**
3. **internal free space must be *measured* at `>= 105 GiB`** — measured, not projected;
4. **all other future-run preflight predicates must pass.**

**E0 remains NOT AUTHORIZED.** The D124 observations about possible 76-source storage are
**NON-GOVERNING** and may not be cited as a capacity basis for E0.

## 15. Owner rulings D124-R1 – D124-R10

| Ruling | Content |
|---|---|
| **D124-R1** | **`985,834` is the FINAL controlling governed deterministic member count** for the frozen current source; **`985,479` is `SUPERSEDED-BY-OBJECT`, not erroneous.** |
| **D124-R2** | **Retire the Decision 112 §6 about-`132.5 GB` figure from future capacity planning.** `e0-compact-evidence/2` — Decision 113, calibrated by D118 and the later D120/D122/D123 evidence — **is the controlling storage contract.** Decision 112 is **not** retired as historical evidence. |
| **D124-R3** | **Central planning value `21,508,823` distinct accessions, band `21.50 M` – `21.55 M`** — a capacity/model input, **not** a completed-source observation. |
| **D124-R4** | **Accept the D124 phase model with the §7 F1 interpretation corrected**: the explicit-accession fraction is about **`7.73%`**, not `61.8%`. |
| **D124-R5** | **Hard starting internal free-space gate `>= 105 GiB` = `112,742,891,520` bytes**, superseding the reviewer's recommended `100 GiB`. In-flight: continuous hard-stop floor `10 GiB`; **`>= 30 GiB` required immediately before opening F2**, and **F2 must not begin below it**. **No `VACUUM`.** SQLite temporary storage explicitly placed and accounted on the internal run volume. **The Decision 121 §7 `>= 85 GiB` floor is SUPERSEDED, not suspended.** |
| **D124-R6** | **The external SSD is approved IN PRINCIPLE as archival / cold-preservation storage. Active SQLite use is NOT approved. Reformatting is NOT approved or required.** |
| **D124-R7** | **D117, D120, D122, the D123 characterization residue, and disposable performance material are eligible under a later archival instrument.** **Only after external verification may authorized internal copies be removed.** C3's retained about-`10 MiB` evidence and tiny diagnostics stay internal. |
| **D124-R8** | **The D122 post-F1 working catalog requires a fresh SHA-256 in the archival instrument.** The historical candidate `fa4a635d…9413` is **not** yet accepted durable identity: hash the actual catalog, compare, **stop on mismatch**, and record the resulting identity **before** deletion. |
| **D124-R9** | **The external archive must carry an explicit cryptographic/metadata manifest and/or a metadata-preserving container**, because exFAT does not preserve all relevant POSIX metadata. The §11 minimum field list is mandatory. |
| **D124-R10** | **No complete-source authority from D124 alone.** Archival complete, copies reclaimed, **measured** `>= 105 GiB` free, and all other preflight predicates passing come first. **E0 remains NOT AUTHORIZED**, and the D124 76-source storage observations are **non-governing**. |

Governance-namespace rulings **D124-G1**, **D124-G2**, and **D124-G3** are in §3.

## 16. What this record does not do

**It authorizes no execution.** No complete-source run, no E0-v3, no F1, no F2, no full-population
F2 rerun, no D117 retry, no three-source canary, no real replay proof, no canary of any kind, no
migration `0016`, no network, and no acquisition.

**It authorizes no archival, no copy, and no deletion.** §11 makes worlds *eligible under a later
instrument*; **eligibility is not authorization**, and no such instrument exists yet. **Nothing was
archived, copied, moved, or deleted by this publication**, nothing was written to the external SSD,
and the D117, D120, and D122 worlds and the D123 residue all remain preserved. The single C3
working-catalog deletion recorded at Decision 122 §3 stays spent.

**It changes no code and no schema.** No source, test, migration, configuration, or capacity
constant changed; `src/disclosure_drift/m3/capacity_plan.py` is untouched; no database was opened;
and no governed SQLite writer was opened.

**It supersedes exactly two things, both narrowly.** The Decision 121 §7 `>= 85 GiB` floor is
retired (D124-R5), and the Decision 112 §6 about-`132.5 GB` figure is retired **as current planning
capacity only** (D124-R2). Decisions 111, 112, 121, and 123 are otherwise unrewritten, and
Decision 094 and Decision 123 are not renumbered (D124-G1).

**All three activation constants remain `None`**, the operational catalog remains at migration head
`0015`, migration `0016` remains absent, no E0-v3 namespace exists, and both tracked network
switches remain `false` at request ceiling `0`.

**The next technical and operational stage is D125 — archival plus verified internal reclamation.**
It is not executed, not started, and not authorized by anything written here.
