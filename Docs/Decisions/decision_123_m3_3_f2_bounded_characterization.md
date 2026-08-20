# Decision 123 — The Bounded F2 Association-Finalization Characterization

```text
STATUS: ACCEPTED — OWNER FINDING, CLOSED
RECORD_TYPE: OWNER ACCEPTANCE OF A BOUNDED CHARACTERIZATION — NOT A FULL-POPULATION RUN
DATE: 2026-08-20
OWNER: Joey authorization; Sol/GPT-5.6 owner findings
OUTCOME: M3_3_D123_F2_BOUNDED_CHARACTERIZATION_OWNER_ACCEPTED
CLASSIFICATION: F2_MATERIAL_BUT_ACCEPTABLE
SCOPE: FIRST-SOURCE-CANARY ASSOCIATION-FINALIZATION SHAPE ONLY
FULL_POPULATION_F2_EXECUTION: DID NOT RUN — REFUSED AT THE STORAGE PREFLIGHT
SUPERSEDES: nothing
F2_FULL_POPULATION_AUTHORIZATION: NO
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_V3_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

The F2 half of the bounded finalization measurement
[Decision 118](decision_118_m3_3_read_only_performance_diagnosis.md) §4 (R23) required,
[Decision 121](decision_121_m3_3_finalization_feasibility_preflight.md) §4 split out as its own
separately-authorized shape, and
[Decision 122](decision_122_m3_3_d120_f1_finalization_characterization.md) §6 left as the single
remaining unmeasured half.

## 1. The one thing this record must not be misread as

**The full-population F2 execution against the preserved D122 F1 world did not run.** It was
**refused at the storage preflight**. No F2 transaction was opened against that world, no
association projection was written into it, no §9.5 totality check ran against it, and no
completion artifact exists anywhere.

**What did happen is narrower, and is what this record accepts:** a **bounded real F2
characterization**, executed against **production-schema disposable projections** at six sizes,
plus **read-only and probe measurements** taken against the full preserved D122 world.

Every wall-time statement about the complete first source in §6 below is therefore
**extrapolation**, not evidence. Nothing here may be cited as a completed full-population F2 run,
and nothing here is one.

## 2. Entry state

Branch `main` at published `207f9a5de2b35b72a719b44b1c84c5565e050576`, tree
`3e6efc500ae6bc8e65bf62af13bb78ff818355d7`, `origin/main` identical and the worktree clean, with
governance published through
[Decision 122](decision_122_m3_3_d120_f1_finalization_characterization.md). Migration head `0015`;
migration `0016` absent; no E0-v3 namespace; all three activation constants —
`M3_3_E0_EXECUTION_AUTHORITY`, `PRE_E0_CATALOG_TRANSITION_AUTHORITY`, and
`STALE_WRITER_LEASE_RECOVERY_AUTHORITY` — `None`; both tracked network switches `false` at request
ceiling `0`.

The preserved worlds at entry were the D117 world, the D120 world, and the D122 F1 working catalog,
all immutable per Decision 122 §7. They remain so; see Decision 123 R76 and R77 in §10.

## 3. What F2 is, and the structural property being characterized

**F2 is `materialize_census_associations(..., compact_evidence=True)`** in
`src/disclosure_drift/m3/offline_parse.py`.

**Its structural property is the one Decision 121 §4 identified and this record does not touch:
one transaction spans both association traversals and the totality check.** That single transaction
is the [Decision 094](decision_094_m3_3_pre_e0_executability_redesign.md) §§6.2–6.4 and §9.5
all-or-nothing **correctness property** — SQLite cannot checkpoint an uncommitted write-ahead log,
so an interruption loses the entire F2 transaction, by design. This characterization measures the
cost of that shape. It does not propose batching it away, and no such change is authorized here.

## 4. What actually executed

Three things, and only these three.

1. **Real F2 against production-schema disposable projections**, at six sizes: **25,000**,
   **50,000**, **100,000**, **200,000**, **400,000**, and **800,000** accessions. These are
   production-schema projections created for the measurement, not the governed worlds.
2. **Read-only and probe measurement against the preserved D122 F1 world** — the full catalog of
   about **23.5 GB**. Reading it mutated nothing.
3. **An attempted full-population F2 against that same world, which was refused at the storage
   preflight and therefore never began.** The refusal is the reason this record is bounded.

The `23.5 GB` figure is arithmetic over two already-accepted values, stated as arithmetic rather
than as an independent measurement: the Decision 120 §4 working database of `19,922,350,080 B`
plus the Decision 122 §5 F1 database growth of `3.360 GiB` is about `23.53 GB`, which is about
`21.91 GiB`.

## 5. The bounded scaling measurement

**Scaling across the six projections.**

| Quantity | Fitted exponent |
|---|---|
| wall time | **`b = 1.0053`** |
| write-ahead log | `0.9748` |
| durable database growth | `0.9996` |

The wall fit's coefficient of determination is **`R^2 = 0.99986`**.

**The finding this establishes is a negative one, and it is the important one: no `N x M` and no
quadratic mechanism was found.** All three exponents sit at or just below linear. Repeated probes
were confirmed to use the accepted indexes rather than falling back to scans.

**Repeatability, at the `200,000` rung.** Three runs spread about **`1.40%`** in wall time, and
their **write-ahead-log and database-growth byte counts were identical across all three runs**.
Byte-identical durable output across repeated runs is a determinism observation, not a timing one,
and it is recorded as its own fact.

**Memory.** Peak resident set plateaus at approximately **`0.68 GiB`** and does not climb with
projection size — the same bounded regime Decision 122 §5 measured for F1 at `0.666 GiB`.

## 6. The full-world read characterization

Measured against the preserved D122 F1 catalog of about `23.5 GB`, read-only:

| Quantity | Measured |
|---|---|
| real groups measured | **`600,000`** |
| read cost | **`136.32 us` per group** |
| database-size cost, full world versus the about-`2 GB` projections | **bounded constant, about `1.36x`** |

`600,000` groups at `136.32 us` is about `81.79 s` of read time; that product is arithmetic over
the table above and not a separately measured elapsed figure.

**The `1.36x` is the load-bearing result.** Moving from an about-`2 GB` projection to the full
about-`23.5 GB` world — roughly a twelvefold increase in database size — costs a **bounded
constant factor**, not a scaling exponent. That is what rules out the database-size-dependent
collapse mechanism for this shape, and it is the evidence behind the classification in §7.

## 7. The D120-scale projection, and the accepted classification

**Projected** — not measured — for F2 at the full D120/D122 first-source scale:

| Quantity | Projection |
|---|---|
| wall time, central | **about `0.78 h`** |
| wall time, primary range | about `0.74`–`0.82 h` |
| wall time, outer range | about `0.63`–`0.94 h` |
| pre-commit write-ahead log | **about `3.487 GiB`** |
| durable database growth | about `2.358 GiB` |
| peak resident set | about `0.68 GiB` |

**Accepted classification: `F2_MATERIAL_BUT_ACCEPTABLE`.**

**The owner's conclusion follows from it: no F2 architecture remediation is required for the
first-source-canary shape.** F2 costs real time and a real multi-gibibyte uncommitted log, which is
why it is *material*; it does not exhibit the collapse mechanism
[Decision 118](decision_118_m3_3_read_only_performance_diagnosis.md) §1 diagnosed, which is why it
is *acceptable*. The existing single-transaction architecture is retained unchanged — see
Decision 123 R70 and R72 in §10.

Against the Decision 118 §2 `>= 169.61 GiB` write-ahead-log lower bound observed from D117, a
projected pre-commit log of about `3.487 GiB` is not in the same regime. It is nonetheless about
`3,113x` the `1.12 MiB` F1 peak Decision 122 §5 measured, which is exactly the F1/F2 asymmetry
Decision 121 §4 predicted from the transaction structure: F1 checkpoints at every batch boundary
and F2 cannot checkpoint at all before commit.

## 8. Scope limits — recorded prominently, because they are easy to lose

These are limits on the record itself, not caveats about the measurements.

- **Full-population F2 was not executed.** It was refused at the storage preflight. §1 states this
  first for a reason.
- **About `92.7%` of the D120 population remains extrapolated for wall time.** This is the owner's
  accepted figure. It is consistent with the `600,000` groups §6 records against the `8,258,521`
  accepted D120 accession count — about `7.3%` measured — and this record neither recomputes nor
  adjudicates it.
- **Every complete-first-source number in §7 is extrapolation, not evidence.** The measured ladder
  tops out at `800,000` accessions, which is about `9.7%` of the `8,258,521` accepted D120
  accession count.
- **This does not characterize the full 76-source E0 finalization shape.** Decision 121 §5's limit
  carries unchanged: a D120-shaped world is performance-representative of the **first-source
  canary** *because full-index evidence is absent in both*, and of nothing beyond it.
- **Established / completeness-write behaviour was not exercised at all.** The first-source shape
  **lacks full-index evidence**, so the code paths that write `established` completeness were never
  reached. Their cost is unmeasured, and this record says nothing about them.
- **No complete-source authority and no E0 authority follows.** See Decision 123 R78 in §10.

## 9. Two capacity conflicts this record exposes and deliberately does not resolve

D123 surfaced unresolved conflicts in the capacity and population model. They are recorded here as
findings. **Neither is resolved by this record, and neither may be resolved by inference from it.**

### 9.1 Conflict A — the governed member count

| Basis | Count |
|---|---|
| D117 / D120 real enumeration, and [Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md) §7 | **`985,834`** |
| the older D111 / D112 basis this report cited — [Decision 111](decision_111_m3_3_e0_bounded_persistence_and_working_catalog.md) §5 and [Decision 112](decision_112_m3_3_compact_e0_evidence_contract.md) §6 | `985,479` |

The D123 report cited `985,479`, which came from the older basis, while real enumeration
established `985,834`.

**Owner ruling: `985,834` is the provisional controlling real count. `985,479` is stale and
unresolved, pending a D124 trace of where the difference arose.** "Provisional controlling" means
it governs now and is still expected to be traced — it is not yet a closed finding.

### 9.2 Conflict B — complete-source storage

D123 cited the older Decision 112 §6 figure of about **`132.5 GB`** of working state for source 1.
Later accepted work contains **materially different compact-capacity figures** — see
[Decision 113](decision_113_m3_3_compact_derived_e0_evidence.md) §15 and §19, and the
Decision 118 §5 (R24) finding that the capacity density is **strained but not invalidated**.

**This publication does not choose between them.** Doing so would be a capacity ruling, and no
capacity ruling is authorized here.

**Owner ruling: the prior `>= 85 GiB` complete-source free-space planning floor — Decision 121 §7 —
is SUSPENDED PENDING D124 CAPACITY RECONCILIATION.** Suspended means it may not be relied on in
either direction: it is neither a floor that has been met nor one that has been lowered.

**No complete-source run may be authorized using the unresolved figures.** A complete-source
authorization requires the D124 reconciliation first.

## 10. Owner rulings R70–R78

**A stated numbering condition, first.** Decision 094 §§6–9 already carries rulings numbered
R70–R78 with entirely different content. These numbers were issued by the owner for this record and
are recorded exactly as issued; this record does not renumber an owner ruling. The consequence is
that a bare `R72` is ambiguous repository-wide, so **every citation of a ruling in this range must
name its decision** — "Decision 123 R72", never "R72" alone. Resolving the numbering itself is a
governance question for D124, not something this publication may settle.

| Ruling | Content |
|---|---|
| **Decision 123 R70** | **`F2_MATERIAL_BUT_ACCEPTABLE` is accepted** for the first-source-canary shape. |
| **Decision 123 R71** | **No full-population D120 F2 rerun.** |
| **Decision 123 R72** | **Retain the existing single-transaction F2 architecture.** No remediation is required from the current evidence. |
| **Decision 123 R73** | **The measured F2 write-ahead-log cost becomes an input to future capacity planning.** It is an input to that planning, not a capacity ruling on its own. |
| **Decision 123 R74** | **The `>= 85 GiB` complete-source free-space floor is suspended pending D124.** |
| **Decision 123 R75** | **`985,834` is the provisional controlling real member count; `985,479` is unresolved and stale.** |
| **Decision 123 R76** | **The D117, D120, and D122 worlds remain preserved pending D124.** |
| **Decision 123 R77** | **The D123 disposable characterization residue remains preserved through D124.** |
| **Decision 123 R78** | **No complete-source authority and no E0 authority.** |

## 11. What this record does not do

It authorizes no full-population F2 execution, no complete-source canary, no D117 retry, no
three-source canary, no real replay proof, no E0-v3, no migration `0016`, no network, and no
acquisition. It authorizes **no deletion of any kind**: the D117, D120, and D122 worlds and the
D123 disposable residue are all preserved through D124 (Decision 123 R76 and R77).

It supersedes nothing. It changes no evidence contract, no digest, no schema, and no capacity
constant — including every Decision 113 constant, which is unchanged, and
`src/disclosure_drift/m3/capacity_plan.py`, which is untouched. It reopens no deferral, and it
resolves neither §9 conflict.

All three activation constants remain `None`, the operational catalog remains at migration head
`0015`, migration `0016` remains absent, no E0-v3 namespace exists, and both tracked network
switches remain `false` at request ceiling `0`.

**The next technical stage is D124 — capacity and model reconciliation.** It is not executed, not
started, and not authorized by anything written here.
