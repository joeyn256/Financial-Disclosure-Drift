# Decision 135 — The Corrected-Run Capacity Reconciliation, and the Turn to an External Working Volume

```text
STATUS: ACCEPTED — OWNER RULING / CAPACITY PLANNING MODEL
RECORD_TYPE: OWNER GOVERNANCE PUBLICATION OF A COMPLETED CAPACITY RECONCILIATION, TOGETHER WITH THE
  OWNER'S CAPACITY-ARCHITECTURE DIRECTION
DATE: 2026-08-23 (record). The reconciliation itself ran 2026-08-22 local time; its
  free-space observations are stamped 2026-08-23T03:44Z UTC, which is the same evening
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
CLASSIFICATION: CAPACITY_PLANNING_MODEL_ONLY
ACCEPTANCE_TOKEN: M3_3_D135_CORRECTED_RUN_CAPACITY_MODEL_OWNER_ACCEPTED
ARCHITECTURE_RULING_TOKEN: M3_3_D135_EXTERNAL_WORKING_VOLUME_PATH_SELECTED
ANALYSIS_AUTHORIZATION: M3_3_D135_CORRECTED_RUN_CAPACITY_RECONCILIATION_AUTHORIZED — issued outside
  this repository and now spent; this record authorized none of the analysis it publishes
VERDICT: D135_CORRECTED_RUN_CAPACITY_MODEL_INSUFFICIENT
D129_R12_DISPOSITION: THE CAPACITY MODEL D129-R12 REQUIRED NOW EXISTS. D129-R12 IS ANSWERED AS A
  MODELLING OBLIGATION AND IS NOT DISCHARGED AS AN AUTHORIZATION
ACCEPTED_START_FREE_FLOOR: 185 GiB — 198,642,237,440 BYTES
ACCEPTED_PRE_F2_FREE_FLOOR: 50 GiB — 53,687,091,200 BYTES
SUPERSEDED_FOR_PLANNING: THE 105 GiB LAUNCH GATE AND THE 30 GiB PRE-F2 GATE
CODE_CONSTANT_DISPOSITION: PRE_F2_MINIMUM_FREE_BYTES REMAINS 30 * 1024**3 IN CODE — NOT EDITED HERE
  AND NOT AUTHORIZED TO BE EDITED HERE
INTERNAL_VOLUME_DISPOSITION: INSUFFICIENT — 126,846,775,296 BYTES OBSERVED MINIMUM FREE AGAINST A
  198,642,237,440 BYTE FLOOR; SHORTFALL 71,795,462,144 BYTES / 66.8647 GiB
INTERNAL_CLEANUP_CAMPAIGN: NOT REQUIRED AND NOT AUTHORIZED
CAPACITY_ARCHITECTURE_PATH: ACTIVE EXTERNAL WORKING VOLUME — QUALIFICATION ONLY, UNDER A FUTURE D136
EXECUTABLE_CHANGE_SET: NONE — NO SOURCE, TEST, SCRIPT, CONFIGURATION, SCHEMA, OR MIGRATION BYTE
D131_CONFIGURATION_DISPOSITION: UNCHANGED. NO D134 CANDIDATE ADOPTED
D134_DISPOSITION: UNAFFECTED AND UNCHANGED — mmap AND CHECKPOINT CANDIDATES REMAIN REJECTED
D128_SEMANTIC_DISPOSITION: UNCHANGED. D129-R2'S REJECTION OF EVERY D128 COUNT STANDS ENTIRELY
CARDINALITY_LABEL: CAPACITY_PLANNING_CARDINALITIES_ONLY
SOURCE_WIDE_SEMANTIC_CLAIM: NONE
COMPLETE_SOURCE_AUTHORIZATION: NO
CORRECTED_CANARY_AUTHORIZATION: NO
EXTERNAL_VOLUME_ADOPTION_AUTHORIZATION: NO — QUALIFICATION IS NOT ADOPTION
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
PRE_NETWORK_BLOCKER: CensusOrchestrator._parse_bulk — OPEN, DELIBERATELY UNREPAIRED
```

The owner's governance publication of the corrected-run capacity reconciliation required by
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (**D129-R12**), together with
the owner's ruling that the model is accepted, that the internal working volume does not meet it,
and that the next capacity-architecture step is **qualification of an external active working
volume**.

## 1. What this record is, and what it is not

**It is a capacity model and a verdict about a machine.** D129-R12 ruled that the old
[Decision 124](decision_124_m3_3_capacity_reconciliation.md) launch-capacity model was not sufficient
by itself to authorize a corrected rerun, and stated plainly that D129 **does not construct** the
replacement. This record publishes the replacement. It answers D129-R12 as a **modelling
obligation**.

**It is not an authorization, and answering D129-R12 does not discharge it as a gate.** A capacity
model tells the project what a corrected run would need. It does not say the run may happen, and in
this case the model's own verdict is that the machine as it stands **cannot host the run at all**.
The formal outcome is `D135_CORRECTED_RUN_CAPACITY_MODEL_INSUFFICIENT`, and the word *insufficient*
attaches to the **capacity**, not to the model:

> INSUFFICIENT is a statement about CAPACITY, not about the model. The model is defensible; the
> machine does not currently hold what it asks for.

**It certifies no count.** Every cardinality it uses is labelled `CAPACITY_PLANNING_CARDINALITIES_ONLY`.
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §4 (**D129-R2**) still rejects every
D128 semantic count, and this record does not revisit that by a single figure. A number good enough
to size a disk is not thereby a number good enough to publish as a research result, and the two uses
are kept apart throughout.

**Its executable change set is empty.** No source, test, script, configuration, schema, or migration
byte moves with it. In particular `PRE_F2_MINIMUM_FREE_BYTES` in
`src/disclosure_drift/m3/single_source_canary.py` **remains `30 * 1024**3`**, and this record's
finding that the constant is inadequate is explicitly **not** an authorization to edit it.

## 2. Entry state

Accepted [Decision 134](decision_134_m3_3_bounded_performance_ab.md) closed the performance half of
the pre-complete-source gate with a decision to **adopt nothing**, leaving the capacity half
untouched and naming it the next substantive stage. At the point the reconciliation ran:

- **HEAD** was the D134 publication; the working tree was clean.
- The **accepted D131 runtime configuration** and the **D119 pragma surface** were byte-unchanged,
  since no D134 candidate was adopted. The model is therefore built for **the configuration that
  would actually run**.
- **Migration head `0015`**; `0016` absent, unapplied and unauthorized.
- **All three activation constants `None`.** Network disabled at both tracked switches, request
  ceiling `0`.
- `CensusOrchestrator._parse_bulk` **open as a PRE-NETWORK blocker**
  ([Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §12, D131-R4).

## 3. What the model was built from, and how each input is classified

The reconciliation reads **measured** values only, and every component carries an explicit
classification — `MEASURED_LIVE`, `DERIVED`, `ARCHIVE_ONLY` or `UNKNOWN` — so that no archive figure
is ever silently used as a live one.

**Repository records read:** Decisions 124, 126, 127, 129, 130, 131, 132 and 134;
`src/disclosure_drift/m3/single_source_canary.py` for the live pre-F2 constant;
`src/disclosure_drift/storage/migrations/0003_census_catalog.sql` for the key structure that
justifies the two uplift factors; and `Milestones/STATUS.md` for entry state.

**External evidence read:** the D134 preserved arm documents and consolidated results, entry-gated
against `evidence/d134_preservation_manifest.json`, SHA-256
`68ed5537af2be388b7ebdf7bff6545f71be3c586649104bb3523731aee6d60b3` — the manifest
[Decision 134](decision_134_m3_3_bounded_performance_ab.md) §9 (D134-R8) created for exactly this
purpose. **The D134 preservation ruling paid for itself here**: without it, this model's only
independent scaling evidence would have been deleted.

**What was deliberately not opened.** The D130 external pax archive was **not consulted** — every
figure required was available from the D130 record's own durable internal index — so the `~104 GB`
archive was **not opened, not re-hashed, not extracted, and no member was read**. The accepted bulk
source archive's size was read from **directory metadata only**; the archive was not opened or
hashed. **`0` databases were opened**, the operational catalog was **not touched**, and **no network
was used**.

**The honest gaps.** D128 recorded **no launch free space**, **no F0 or F1 interior free-space
breakpoint**, **no SHM size at any stage**, and **no peak temporary/spill usage** — its
`SQLITE_TMPDIR` was *present and empty at the end of the run*, which proves nothing about its peak.
These are listed as `UNKNOWN` and are the single largest source of uncertainty in the model. They are
also the reason §9's monitoring recommendations exist.

## 4. Model A — D128's measured state, scaled by the corrected workload

**Basis: what a real complete-source run actually consumed, scaled up by how much more a corrected
run must store.**

D128 is a **defective** run, and §11 of D129 reports what a defective run consumed — systematically
**less** than a corrected one will. The correction is a workload uplift, derived from the D129 §5
cardinalities:

| Quantity | Value | Label |
|---|---|---|
| D128 accessions | `15,996,591` | planning cardinality |
| Corrected accession universe | `19,034,205` | planning cardinality |
| Shard accessions | `5,102,087` | planning cardinality |
| Shard accessions recovered | `2,064,473` | planning cardinality |
| Genuinely missing from D128 | `3,037,614` | planning cardinality |
| Historical shards | `5,337` | planning cardinality |
| Governed JSON members | `985,834` | planning cardinality |

Two uplift factors follow, and they differ because the schema keys differ:

- **`U_acc` = `6,344,735 / 5,332,197` ≈ `1.1899`** — applies to `census_accessions`, whose
  `accession_plain` **primary key** collapses duplicates.
- **`U_rows` = `21,098,678 / 15,996,591` ≈ `1.31895`** — applies to `census_parsed_records` and
  `census_accession_observations`, which carry **their own surrogate keys**, so duplicate shard
  accessions **do** add rows.

**`U_rows` governs.** The catalog cannot be decomposed into accession-keyed and row-keyed families
from the available evidence, so the **conservative supported proxy governs the whole catalog**.
`U_acc` is retained as a sensitivity, not as the model.

**What is deliberately not scaled.** The accepted source archive (`1,556,847,020` bytes) is already
resident on the run volume and is **not duplicated into the run world** — D128's world held `26`
files, all catalog and evidence — so its **incremental capacity cost is `0`**. Run logs and results
(`758,142` bytes) are fixed, not scaled.

**Model A's projection, at the governing uplift:**

| Component | Bytes | GiB |
|---|---|---|
| Working catalog | `136,767,758,802` | `127.3720` |
| Compact-evidence sidecar | `357,877,422` | `0.3333` |
| Fixed other | `758,142` | `0.0007` |
| **Durable, allocated** | **`137,164,199,880`** | **`127.7441`** |
| Governing WAL (pre-F2 peak) | `21,483,906,517` | `20.0084` |
| Temp / spill | `0` | `0` |
| Incremental source payload | `0` | `0` |
| **Pre-F2 consumption** | **`129,062,324,047`** | **`120.1987`** |
| **Projected peak live** | **`158,648,106,397`** | **`147.7526`** |

**The D128 timeline closes internally**, which is what makes the reconstruction trustworthy rather
than merely arithmetic: the gate-to-minimum drawdown (`15,486,956,011` B) minus the
minimum-to-final recovery (`9,344,094,208` B) yields F2 durable growth of `6,142,861,803` B, and the
recovery matches F2's published `~8.67 GiB` WAL peak to within `34,752,593` B — `0.032` GiB.

## 5. Model B — D134's baseline arms, scaled — and why it never governs

**Basis: the corrected code path's own measured densities, from D134's baseline arms only.** The
mmap arms (D134-R2) and relaxed-checkpoint arms (D134-R3) are **excluded**, because neither was
adopted.

Model B projects a peak of `51,203,670,855` bytes (`47.6871` GiB) at its governing `ab3000` point —
roughly **a third** of Model A. That gap is not a disagreement to be split. Model B is
**structurally an understatement**, for four stated reasons:

1. **No pre-F2 WAL term exists at all.** D134's global WAL high-water **is** F2's (D134-R3), so the
   `~15.17 GiB` pre-F2 WAL phenomenon D128 measured is **unrepresented, not absent**.
2. **No pre-F2 stage breakpoint.** D134 recorded no interior free-space observation.
3. **The fixture is a low-ordinal prefix** carrying `~317` accessions per member against a corrected
   source-wide `~19.3` — a **`~16×` structural difference** — and its bytes-per-accession understates
   D128's measured value by **`~3×`**.
4. **`1 Hz` sampling can understate true WAL and free-space extrema.**

**And its density rises with scale**: catalog bytes per accession grew `2,086.81` → `2,171.55`
(`+4.06%`) between `ab3000` and `ab6000`, so **linear extrapolation from either point is an
understatement, not a conservative bound**.

Model B is retained as an **independent projection** and is demonstrably an understatement for every
component it covers. **It never governs the reconciliation.** It is kept because a model with only
one input is a guess with a table around it.

## 6. The reconciled model — component-wise `max`, and the stage envelope

The reconciliation takes **component-wise `max(Model A, Model B)`**. Model A governs **every**
component; Model B is **inapplicable** for pre-F2 consumption, since D134 recorded no pre-F2
breakpoint at all.

| Stage | Projected total live | GiB | Uncertainty |
|---|---|---|---|
| `START` | `0` | `0` | MEASURED — a new create-once world starts empty (D129-R8) |
| `F0_PARSE_PEAK` | *unknown* | — | **UNKNOWN** — D128 recorded no F0/F1 interior breakpoint |
| `F0_F1_PEAK_BOUND` | `150,546,230,564` | `140.2071` | DERIVED-CONSERVATIVE — deliberately double-counts checkpointed pages |
| `PRE_F2_ADMISSION` | `129,062,324,047` | `120.1987` | DERIVED from a measured D128 gate observation |
| `F2_PEAK` | `158,648,106,397` | `147.7526` | DERIVED-CONSERVATIVE — full durable state plus the largest observed WAL |
| `FINALIZATION` | `137,164,199,880` | `127.7441` | DERIVED — WAL checkpointed to `0`, as D128 measured at close |

For reference, D128 itself peaked at a **derived** `113,339,400,192` bytes (`105.5555` GiB) and
finished at `103,995,305,984` (`96.8532` GiB). The corrected projection is larger because a corrected
run **stores what D128 never stored**.

**The safety-reserve rule, fixed before either gate was computed:**
`max(20 GiB, 25% of remaining projected peak growth)`, then **round up to the next `5` GiB**.

**Two independent arithmetic paths.** Every derived value is reproduced by two independently written
exact-integer implementations — Python `fractions.Fraction` with `math.ceil`, and BSD `bc` at
`scale=0` — with the second written from the **raw measured inputs only**, sharing no computed value,
intermediate, or line of code with the first. They **agree exactly on all `21` integer-byte totals**.

## 7. The accepted START floor — D135-R2

| | Bytes | GiB |
|---|---|---|
| Remaining projected peak growth | `158,648,106,397` | `147.7526` |
| Safety reserve (`25%` branch binds) | `39,662,026,600` | `36.9381` |
| Required free | `198,310,132,997` | `184.6907` |
| **Accepted floor** | **`198,642,237,440`** | **`185`** |

The `25%` branch binds because `25%` of `147.7526` GiB exceeds the `20` GiB floor.

**This supersedes the `105 GiB` launch gate for planning purposes.** The old gate was built against
D124's projections, which D129 §11.4 measured as underpredicting F1+F2 by about `1.8×`–`1.9×`.

## 8. The accepted PRE-F2 floor, and why `30 GiB` is not adequate — D135-R3

| | Bytes | GiB |
|---|---|---|
| Remaining projected peak growth after the gate | `29,585,782,350` | `27.5539` |
| Safety reserve (**`20` GiB floor** binds; the `25%` branch yields only `7,396,445,588`) | `21,474,836,480` | `20` |
| Required free | `51,060,618,830` | `47.5539` |
| **Accepted floor** | **`53,687,091,200`** | **`50`** |
| Old floor, still live in code | `32,212,254,720` | `30` |
| Delta | `21,474,836,480` | `20` |

**The proof that the old gate is not adequate is arithmetic, not preference.** The corrected
projection consumes **`27.5539` GiB of the old `30` GiB gate outright**, leaving **`2.4461` GiB** —
almost exactly the `~2 GiB` margin D129 §11.3 found D128 *actually* experienced — and with **zero
safety reserve**. The old gate is not a comfortable threshold that happens to be low; it is **a
near-miss restated at a larger workload**.

**The exact reason for the delta:** the pre-F2 gate must cover the run's later live-storage peak,
which the corrected workload raises by the `1.3189` row uplift, **plus** a precommitted reserve the
old gate never carried at all.

**A sensitivity was computed and deliberately NOT adopted.** Using F2's *own* WAL peak
(`12,278,541,168` B scaled) instead of the global maximum WAL — on the D128 finding that the largest
WAL sat *before* the gate — gives remaining growth of `20,380,417,001` B (`18.9807` GiB) and would
support a **`40` GiB** floor. It is not adopted because **the WAL phase attribution rests on one
defective run at a different workload**, and because
[Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) inserts a **new deferred-shard
reopen phase whose transient behaviour has never been measured at full scale**. The locked floor
keeps the conservative form. **The variant changes neither the START floor nor the verdict.**

**The code constant is not edited by this record.** `PRE_F2_MINIMUM_FREE_BYTES` stays at
`30 * 1024**3`. Implementing the corrected constant is a **separate, separately authorized** change,
and it is safe to defer precisely because **no run is authorized**: a gate that is never reached
cannot be reached at the wrong value.

## 9. The internal-volume verdict — D135-R4

**The model was locked and hashed BEFORE any current free-space measurement was taken.** That
ordering is the record's own integrity guarantee: `capacity_model_locked.json`, SHA-256
`cba5ba2bf117286ddfee27f5582b9fdcd135b9a193f79ad73207f7dc5b69a982`, carries the attestation
`WRITTEN BEFORE ANY CURRENT FREE-SPACE OBSERVATION`, and the observation document records the same
hash as the model it was compared against. **No threshold was altered in response to the
measurement.**

Three observations were then taken on `/dev/disk3s5` (`APFS`, `/System/Volumes/Data`) at
`2026-08-23T03:44:15Z`, `:24Z` and `:33Z`, spanning `1,298,432` bytes:

| | Bytes | GiB |
|---|---|---|
| Container capacity | `245,107,195,904` | `228.2739` |
| Used | `118,260,420,608` | `110.1386` |
| **Minimum observed free** | **`126,846,775,296`** | **`118.1353`** |
| Accepted START floor | `198,642,237,440` | `185` |
| **Shortfall** | **`71,795,462,144`** | **`66.8647`** |

`CAPACITY_NOW_MEETS_PROPOSED_START_FLOOR: false`.

**Nothing is withholding reclaimable space** — `0` APFS snapshots on the Data volume and `0` Time
Machine local snapshots — so the shortfall is real rather than an artifact of retained snapshots.
**Free space is container-wide** and shared with the System, Preboot and VM volumes; **VM swap growth
draws on the same pool a run would**.

**Three structural findings make this more than a subtraction:**

1. The accepted START floor is **`81.04%` of the entire container capacity**. Meeting it would leave
   `43.2739` GiB for the operating system and all other data combined.
2. **The projected FINAL durable state alone** (`127.7441` GiB) already **exceeds the minimum
   observed free space** (`118.1353` GiB) by `9.6089` GiB — before any transient, any WAL, and any
   safety reserve. The finished catalog does not fit, never mind the run that builds it.
3. Current free space **does** clear the obsolete `105` GiB D124 start gate, by `13.1353` GiB. That
   is precisely the trap [Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md) §10
   (**D130-R6**) named: **clearing a superseded gate is not readiness**.

The measurement is **descriptive only**. Nothing was cleaned, deleted, moved, or reclaimed to produce
it, and free space remains an **input** to a capacity model and never a substitute for one.

## 10. The capacity-architecture direction — D135-R5

**The owner cannot practically free enough internal storage**, and finding 2 above explains why no
plausible cleanup closes the gap: the *final* state alone already exceeds current free space. A
`66.8647` GiB campaign against a container where the target floor is `81.04%` of total capacity is
not a tidying exercise; it is a request to run the machine with `43` GiB for everything else.

**The owner therefore selects the ACTIVE EXTERNAL WORKING VOLUME path for qualification.**

**This selection means, exactly:**

- proceed next to a **bounded external-volume qualification**;
- **do not** attempt to free `~67` GiB on the internal volume — no internal cleanup campaign is
  required or authorized;
- **do not** authorize a complete-source canary yet;
- **do not** assume the currently attached SSD is suitable until a future **D136** proves it.

**It reverses no prior implementation automatically**, and it authorizes **only a subsequent D136
qualification instrument**. It does **not** authorize using any SSD as the production working root,
modifying path configuration, or running the complete-source canary.

**A future candidate external volume must independently satisfy** — every item, not a majority:

1. **filesystem suitability**;
2. **SQLite WAL and locking correctness**;
3. **durability and recovery requirements**;
4. **sufficient free capacity against the D135 floors** in §§7–8;
5. **sustained-write practicality**;
6. **safe separation from retained D130 evidence**.

**Selecting a path is not qualifying a volume, and qualifying a volume is not adopting it.** Those
are three distinct steps and each needs its own instrument.

## 11. Monitoring recommendations — accepted as planning inputs — D135-R7

**Planning only. Nothing is implemented by this record, and no signal-escalation policy changes.**
**No automatic destructive cleanup is proposed at any point.**

| Point | Threshold | Behaviour on breach |
|---|---|---|
| `PRE_LAUNCH` | free `>= 198,642,237,440` B (`185` GiB); snapshots `== 0` | **REFUSE TO LAUNCH.** No partial start, no "proceed and watch" |
| `POST_F0` | free `>= 60` GiB; catalog within `+25%` of projected F0 share | **STOP AND REPORT** before F1. Do not relax and continue |
| `PRE_F1` | free `>= 55` GiB | **STOP AND REPORT** before opening F1 |
| `POST_F1_PRE_F2` | free `>= 53,687,091,200` B (`50` GiB) | **REFUSE F2** — the existing D127 guard shape with a corrected constant; it already fails closed |
| `DURING_F2` | continuous hard floor `>= 10` GiB (**D124-R5, unchanged**); alert at `20` GiB | **ALERT** at `20` GiB, **HARD STOP** at `10` GiB. F2 is a single transaction, so a stop is a **rollback** — the operator must be told that explicitly |
| `POST_F2` | WAL checkpoints to `0`; world bytes within `+25%` of projection | **REPORT ONLY.** Record the actuals as the next model's anchors |

Four supporting recommendations, each traceable to a gap this model had to work around:

- **Sample at `<= 60` s.** D134's `1 Hz` sampler is the reference. **D128's evidence carries no
  interior F0/F1 breakpoint at all, which is the single largest gap in this model.**
- **Record free space at every phase boundary.** Had D128 done so, Model A would rest on
  measurements rather than on a two-point derivation.
- **Watch the APFS container, not just the Data volume** — VM swap draws on the same pool.
- **`SQLITE_TMPDIR` must be explicitly placed and its peak sampled** (D124-R5). D128 left its sibling
  temp directory **empty at close**, which proves nothing about its peak.

## 12. Claim boundaries — D135-R8 and D135-R9

**What this record establishes:** a capacity-planning model; proposed and accepted capacity floors;
and whether **current** free disk meets the accepted START floor.

**What it does NOT establish — none of these, in any degree:** certified corrected semantic counts;
corrected complete-source runtime; complete-source semantic correctness; complete-source canary
acceptance; E0 readiness; network readiness; **or permission to execute anything**.

**D129-R2 remains controlling.** The `19,034,205` planning accession universe, the `3,037,614`
genuinely-missing figure, and every related quantity in this record are
**`CAPACITY_PLANNING_CARDINALITIES_ONLY`** — sized to plan a disk, **not certified semantic counts**.
Every D128 semantic count remains **rejected**.

**D129-R8 remains controlling.** No corrected complete-source canary is authorized by this record,
and any later canary remains subject to its four requirements: **from scratch, in a new world, under
a new run identity**, with a full source rerun from the beginning. D128 is not resumable and not
repairable in place.

## 13. What did not change

**D131's runtime configuration is unchanged** — SQLite cache, batching, checkpoint cadence, WAL
mode, synchronous durability, index architecture, multiprocessing and writers, and the D127 pre-F2
guard shape all stand exactly as before. **D134's mmap and checkpoint candidates remain rejected**
and neither is implemented; the accepted **D119** pragma surface is byte-unchanged.

**Every D124-R5 gate carries forward.** The continuous `10` GiB floor, the no-`VACUUM` rule, and
explicit `SQLITE_TMPDIR` placement are untouched; the `105` GiB and `30` GiB gates are **superseded
for planning purposes only**, and the `30` GiB constant **remains live in code exactly as written**.

**Every prior decision stands as written.** This record supersedes nothing. Decisions 121 through 134
are unaffected, and **D125-R3** (no further Disclosure Drift evidence may be deleted for capacity)
and **D125-R4** (the SSK SSD remains cold/archive only, with no reformat) both stand.

**Other safety state — D135-R10.** **E0 remains unauthorized.** **Network remains disabled** at both
tracked switches with request ceiling `0`. **`census_orchestrator.py::_parse_bulk` remains the
independent PRE-NETWORK blocker**, deliberately unrepaired, and its repair must not be performed as
a side effect of unrelated work.

## 14. Where the evidence lives

The reconciliation's evidence is held in a **private disposable root outside the repository**, and
**this record is the durable governance pointer** — the architecture
[Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md) §6 (D130-R2) adopted and
[Decision 132](decision_132_m3_3_bounded_real_semantic_proof.md) §12 (D132-R10) reused.

Root: `~/m3-d135-capacity` (`88` KB). Eleven artifacts are authenticated by `evidence_sha256.txt`:

| Artifact | SHA-256 |
|---|---|
| `capacity_model_locked.json` | `cba5ba2bf117286ddfee27f5582b9fdcd135b9a193f79ad73207f7dc5b69a982` |
| `capacity_reconciliation_result.json` | `e5ca0b1f14b41615d1181738205770916f4fa7bf67e4e0f5708333123e0d8272` |
| `reconciled_capacity_model.json` | `bfe2af8ddc27c297e0559d79bdd7864b244f0a335bb9c7c461c28b1d7622b962` |
| `model_a_d128_uplift.json` | `0687ca154637624f30f69e9a958eb5b1b7239b00075b3c5dd5c51b5deadc2990` |
| `model_b_d134_scaling.json` | `ea45c6768c310b0617f275d1dcd7a7a2a4b51865b509b4835a9901f251c645f9` |
| `d128_capacity_timeline.json` | `db978684daa4bba93c557da5d76e393965b08a4f8c08da5b1aa262dfbb24f356` |
| `d134_capacity_anchors.json` | `c671027f3ee6d895035fa871c3bae1a0bd29f88017f4afea992be1617efcee8f` |
| `live_free_space_observation.json` | `9d19e746f05481a7c1caddafd943bd4a6708d1f55113bfd3c2fe12f15f808973` |
| `arithmetic_crosscheck.json` | `19312e95d71eb85bb89a1293320e23d8e1ea13e574cf6b5f3f14a77649ec2917` |
| `source_inventory.json` | `47273cdcbc3b431f5ff255157c1737718453c29efc6b42503d4cc457bbcb1aa4` |
| `crosscheck_bc_output.txt` | `29fc24a2b1c42fe1f51fab0a42cce593835bf05873082279317b9173ea174757` |

The two independent model programs are `model/d135_model_primary.py` (`26,221` bytes, SHA-256
`8eb91655a7f01b2762c3d8b4aa8564102026f1f2adf0dbe67c03d5c60010d314`) and `model/d135_crosscheck.bc`
(`3,817` bytes, SHA-256 `93c2c877fe94f208b37ceb7757ef51c3260926e565a2f756173be21635bf3c3f`).

**All eleven digests were re-verified at publication time and all matched.** The publishing session
also re-derived the START floor, the PRE-F2 floor, the reserve branches, the old-gate margin, and the
shortfall from the published component values by a third, independent computation, and each agreed.

## 15. Limitations, stated rather than smoothed

1. **The model rests on one complete-source run, and that run was defective.** Model A scales D128;
   Model B, the only independent anchor, is a **`<0.7%` prefix** and a demonstrated understatement.
   Two disagreeing models where one is known-low is a reason for conservatism, not a reason for
   confidence.
2. **No F0 or F1 interior breakpoint exists anywhere in the evidence.** The `F0_PARSE_PEAK` stage is
   `UNKNOWN` and is bounded only from above.
3. **Peak temporary and spill usage was never measured** on any run at scale; the model carries `0`
   for it because `0` is what the evidence supports, not because `0` is known to be right.
4. **The D131 deferred-shard reopen phase has never been measured at full scale.** It is new since
   D128 and its transient behaviour is genuinely unknown.
5. **`1 Hz` sampling can understate true extrema**, so D134-derived anchors are lower bounds.
6. **The floors are planning values, not measured requirements.** They will be right or wrong only
   when a corrected run is actually observed against them — which is exactly why §11's monitoring
   recommendation is to record the actuals as the next model's anchors.

## 16. Owner rulings D135-R1 – D135-R10

| Ruling | Content |
|---|---|
| **D135-R1** | **MODEL ACCEPTANCE.** The corrected-run capacity model is accepted as the **controlling capacity planning model**. It does **not** certify corrected semantic counts or complete-source correctness. |
| **D135-R2** | **START FLOOR.** The corrected START free-space floor is accepted at **`185` GiB / `198,642,237,440` bytes**. |
| **D135-R3** | **PRE-F2 FLOOR.** The corrected PRE-F2 free-space floor is accepted at **`50` GiB / `53,687,091,200` bytes**. The existing `30` GiB code constant is **insufficient** under the corrected model. **That constant is NOT edited by this publication.** |
| **D135-R4** | **INTERNAL CAPACITY.** The internal working volume is **currently insufficient**: observed minimum free `126,846,775,296` B (`118.1353` GiB); shortfall `71,795,462,144` B (`66.8647` GiB). **No internal-space cleanup campaign is required or authorized.** |
| **D135-R5** | **EXTERNAL-VOLUME PATH.** The owner selects **external active-volume qualification** as the next capacity-architecture path. It reverses **no** prior implementation automatically and authorizes **only** a subsequent **D136 qualification instrument**. It does **not** authorize using the SSD as the production working root, modifying path configuration, or running the complete-source canary. |
| **D135-R6** | **D131 CONFIGURATION.** The D131 runtime configuration **remains unchanged**. The D134 mmap and checkpoint candidates **remain rejected**. |
| **D135-R7** | **MONITORING.** The D135 monitoring recommendations are accepted as **planning inputs**. **No monitoring or code change is implemented by this publication.** |
| **D135-R8** | **CLAIM BOUNDARY.** **D129-R2 remains controlling.** The `19,034,205` planning accession universe and related quantities remain **`CAPACITY_PLANNING_CARDINALITIES_ONLY`**, not certified semantic counts. |
| **D135-R9** | **COMPLETE-SOURCE AUTHORITY.** **No corrected complete-source canary is authorized.** Any later canary remains subject to **D129-R8**: **from scratch, new world, new run id**. |
| **D135-R10** | **OTHER SAFETY STATE.** **E0 remains unauthorized.** **Network remains disabled.** **`census_orchestrator.py::_parse_bulk` remains the independent PRE-NETWORK blocker.** |

## 17. What this record does not do

It does **not** authorize an execution of any kind. It does **not** create, modify, or delete any
world, catalog, database, or archive. It does **not** touch the external SSD — the attached volume
was **not benchmarked, not written to, not deleted from, not moved on, not reformatted, not
repartitioned**, its D130 archive evidence was **not modified**, and **no inference about its
filesystem suitability is made here**; a future **D136** governs all of that separately. It does
**not** edit `PRE_F2_MINIMUM_FREE_BYTES` or any other constant. It does **not** change path
configuration. It does **not** enable any activation constant, create an E0-v3 namespace, apply
migration `0016`, or alter either network switch. It does **not** relax a single D124-R5 gate. It
does **not** revisit any D128 semantic count, and it does **not** make any source-wide semantic
claim.

## 18. The next authorized action

**An owner-prepared D136 external SSD active-volume qualification instrument — and nothing else.**
It is not started, and nothing written here authorizes it.

The controlling sequence after it, **each step requiring its own owner instrument**: adoption of the
resulting capacity and path architecture, if and only if qualification succeeds; **then and only
then** an owner decision on another complete-source canary, which
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §14 (D129-R8) still requires to be a
**full rerun from scratch, in a new world, under a new run identity**. **E0 remains unauthorized
throughout that sequence**, and reaching its last step is not reaching E0.

**Separately and independently of that sequence**, `census_orchestrator.py::_parse_bulk` must be
repaired before any network or live-retrieval authorization may reach it (D131-R4, D134-R7). That
repair is **not authorized now** and **must not be performed as a side effect of unrelated work**.

**Nothing in this repository is an execution authorization**: not this record, not a passing gate,
not a commit, not a push, not a green CI run. **Modelling what a run would need is not authorizing
the run.** **Complete source is NOT authorized. E0 is NOT authorized.**
