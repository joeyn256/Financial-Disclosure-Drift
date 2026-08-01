# Milestone 3 — Limitations Register

**Status:** seeded at Milestone 3 master planning. **No inherited limitation is closed by this
document.**
**Controlling record:** [Decision 027](../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§11.
**Plan:** [`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md)
§14.

---

## How to use this register

**Closing a milestone does not close its limitations** ([Decision 026](../Decisions/decision_026_milestones_0_1_2_final_closeout.md)
§12). Every accepted limitation from Milestones 0, 1, and 2 is live and inherited here, and none may
be treated as discharged merely because the milestone that recorded it is closed.

Every Milestone 3 phase:

1. **reads this register before starting**, to know which conditions are live;
2. **records any new limitation it discovers**, with the complete field set below;
3. **never closes an inherited limitation** — closure requires the evidence the entry names and,
   where the entry says so, an explicit owner ruling;
4. **refers rather than resolves** any future owner-ruling condition. **D023-O1** is the live example.

### Field definitions

| Field | Meaning |
|---|---|
| **ID** | Stable identifier. Origin-prefixed; never renumbered |
| **Origin** | The accepted record or the Milestone 3 phase that established it |
| **Description** | What the limitation actually is |
| **Affected M3 phase** | Which phases it bears on |
| **Status** | `ACTIVE`, `ACTIVE — OWNER RULING PENDING`, or `CLOSED` with its closing record |
| **Methodology impact** | Effect on the research design, selection, or outcome |
| **Reproducibility impact** | Effect on whether a result re-derives identically |
| **Security impact** | Effect on secrets, identity, or leakage exposure |
| **Operational impact** | Effect on running the phase |
| **Publication impact** | Effect on what may be claimed or released |
| **Mitigation** | What is already done about it |
| **Stop condition** | What must halt the phase if it occurs |
| **Required owner action** | What only the owner can decide, or `none` |
| **Closure evidence** | Exactly what would justify closing it |
| **Closable before M3.5** | `yes` / `no` |

### Register summary

| Group | Entries | Status |
|---|---:|---|
| Decision 020 §19.1 — S5.4 methodological | 5 | all `ACTIVE` |
| Decision 021 §19 — S6 architecture | 10 active, 1 closed | 10 `ACTIVE`, `D021-L11` `CLOSED` |
| Decision 022 — item-46 applicability | 1 | `ACTIVE` |
| Decision 023 §7 — S6 acceptance | 4 | 3 `ACTIVE`, **O1** `ACTIVE — OWNER RULING PENDING` |
| Decision 024 — boundary consequences | 2 | all `ACTIVE` |
| Decision 026 — standing obligations | 3 | all `ACTIVE` |
| Milestone 3 — new at planning | 10 | all `ACTIVE` |
| **Total** | **35 active, 1 closed** | |

---

# Group 1 — Decision 020 §19.1, inherited S5.4 methodological limitations

## D020-L1 — Cross-anchor amendment-family resolution

| Field | Value |
|---|---|
| **Origin** | [Decision 020](../Decisions/decision_020_m23_s5_4_reserve_architecture.md) §19.1 item 1 |
| **Description** | Amendment-family resolution follows the accepted resolved-root accession identity with no added anchor-equality condition, so an entity can be credited with a linked-amendment contribution for a unit named after a different anchor |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | Deterministic, conservative, and fail-closed for reserve construction; it neither weakens contribution-set equality nor alters run identity |
| **Reproducibility impact** | None — the rule is deterministic and reproduces identically |
| **Security impact** | None |
| **Operational impact** | None |
| **Publication impact** | Must be disclosed with any description of the reserve construction |
| **Mitigation** | Recorded and accepted; contribution-set equality is still exact |
| **Stop condition** | A real run where the credited contribution and the anchor disagree in a way that changes selected membership — refer, do not adjust |
| **Required owner action** | none unless the stop condition occurs |
| **Closure evidence** | An accepted decision adding an anchor-equality condition, plus a reviewed code change |
| **Closable before M3.5** | no |

## D020-L2 — Provenance-oriented union member sets

| Field | Value |
|---|---|
| **Origin** | Decision 020 §19.1 item 2 |
| **Description** | Union member sets may contain more members than a minimal witness would require — the accepted consequence of the witness-union ruling |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None on selection; membership is provenance-oriented by design |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | Slightly larger persisted member sets |
| **Publication impact** | Disclose that membership is provenance-complete, not minimal |
| **Mitigation** | **No minimal-witness optimization is authorized** |
| **Stop condition** | Any attempt to trim membership to a minimal witness |
| **Required owner action** | none |
| **Closure evidence** | An accepted decision authorizing a minimal-witness derivation |
| **Closable before M3.5** | no |

## D020-L3 — Exact bundle comparison may reduce reserve availability

| Field | Value |
|---|---|
| **Origin** | Decision 020 §19.1 item 3 |
| **Description** | Exact target-selected versus complete-replacement bundle comparison may reduce the number of compatible reserves found |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | Conservative by design; fewer reserves, never a wrong one |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | A real run may produce more `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` dispositions than an optimizing comparison would |
| **Publication impact** | Disclose the exact-equality rule with any reserve-coverage figure |
| **Mitigation** | **No discretionary trimming, subset search, or package optimization is authorized to obtain compatibility** |
| **Stop condition** | Any subset search or trimming introduced to raise reserve availability |
| **Required owner action** | none |
| **Closure evidence** | An accepted decision changing the comparison rule |
| **Closable before M3.5** | no |

## D020-L4 — Signature contribution values are counts, not Boolean presence

| Field | Value |
|---|---|
| **Origin** | Decision 020 §19.1 item 4 |
| **Description** | The seven named signature contribution values are counts of achieved units, not Boolean presence |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | Intentionally conservative; it further reduces reserve availability |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | Interacts with **D020-L3** — both reduce availability in the same direction |
| **Publication impact** | Disclose alongside D020-L3 |
| **Mitigation** | Recorded and accepted |
| **Stop condition** | Any relaxation to Boolean presence to obtain compatibility |
| **Required owner action** | none |
| **Closure evidence** | An accepted decision changing the signature semantics |
| **Closable before M3.5** | no |

## D020-L5 — Schema-layer transition-test observation

| Field | Value |
|---|---|
| **Origin** | Decision 020 §19.1 item 5 |
| **Description** | The schema-layer subset/superset/empty transition-test observation is nonblocking and was independently validated at acceptance — exact accepted; subset, superset, and empty each refused |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | None |
| **Publication impact** | None |
| **Mitigation** | Independently validated; additional repository coverage at that layer is optional and at the owner's discretion |
| **Stop condition** | A transition the schema layer accepts that the enforcement layer should have refused |
| **Required owner action** | none |
| **Closure evidence** | Owner election to add the optional coverage, plus that coverage passing |
| **Closable before M3.5** | yes, at the owner's discretion |

---

# Group 2 — Decision 021 §19, inherited S6 architecture limitations

## D021-L1 — The six S5-era limitations carry forward unchanged

| Field | Value |
|---|---|
| **Origin** | [Decision 021](../Decisions/decision_021_m23_s6_manifest_construction.md) §19 item 1 |
| **Description** | The five Decision 020 §19.1 limitations (**D020-L1**–**D020-L5**) plus the nonblocking redundant vacuous assertion carry forward into S6 unchanged |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | **None affects terminal hashing or release eligibility** — each changes which rows exist, and S6 hashes the rows as persisted |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | None |
| **Publication impact** | Disclose the S5-era set with any manifest description |
| **Mitigation** | Explicitly reasoned through at S6 acceptance |
| **Stop condition** | Evidence that any of the six does affect terminal hashing |
| **Required owner action** | none |
| **Closure evidence** | Closure of all six underlying entries |
| **Closable before M3.5** | no |

## D021-L2 — `candidate_tables_sha256` binds declared digests, not recomputed tables

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 2 (see §8.2) |
| **Description** | `candidate_tables_sha256` binds the snapshot's **declared** component digests, not independently recomputed candidate tables |
| **Affected M3 phase** | **M3.3 — this is the phase where a real snapshot first exists** |
| **Status** | `ACTIVE` |
| **Methodology impact** | Candidate row content is independently bound through `selection_input_sha256`, so the content is committed by another route |
| **Reproducibility impact** | A wrong declared digest would be permanently attributable but is not detected by recomputation at this layer |
| **Security impact** | None |
| **Operational impact** | **Rises at M3.3**: until now no snapshot builder existed, so there was no accepted derivation to recompute against. When a real builder exists, the declaration and the rows must be checked to agree |
| **Publication impact** | Disclose what the digest binds |
| **Mitigation** | `selection_input_sha256` binds candidate content independently; the M3.3 snapshot-freeze validation must assert declaration/row agreement |
| **Stop condition** | A declared component digest that disagrees with the rows the snapshot actually contains |
| **Required owner action** | Consider, at M3.3 contract time, whether the builder must recompute and compare |
| **Closure evidence** | An accepted decision plus an implemented recomputation-and-comparison step, reviewed |
| **Closable before M3.5** | no |

## D021-L3 — `node_limit_exhausted` is a constant `0` on a feasible run

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 3 (see §6.2) |
| **Description** | `node_limit_exhausted` is a constant `0` in the result preimage on any `feasible` run, retained deliberately as a defensive field |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None — a feasible run by definition did not exhaust the node limit |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | None |
| **Publication impact** | None |
| **Mitigation** | Recorded; the field is defensive, not informational |
| **Stop condition** | A `feasible` run reporting a non-zero value |
| **Required owner action** | none |
| **Closure evidence** | An accepted decision removing or repurposing the field |
| **Closable before M3.5** | no |

## D021-L4 — The four terminal component digests appear at two layers

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 4 (see §10, exclusion 8) |
| **Description** | The four terminal component digests appear at two layers — an intentional diamond, not redundancy to be optimized away |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | None; the graph stays acyclic |
| **Security impact** | None |
| **Operational impact** | None |
| **Publication impact** | None |
| **Mitigation** | Recorded and deliberate |
| **Stop condition** | Any attempt to "simplify" the diamond |
| **Required owner action** | none |
| **Closure evidence** | An accepted decision restructuring the digest graph |
| **Closable before M3.5** | no |

## D021-L5 — Reserve child rows are hashed twice

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 5 (see §7.4) |
| **Description** | Reserve child rows are hashed both directly and, transitively, through `reserve_package_id` — deliberate, for corruption localization |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | None |
| **Publication impact** | None |
| **Mitigation** | Recorded and deliberate |
| **Stop condition** | Any attempt to remove one of the two bindings |
| **Required owner action** | none |
| **Closure evidence** | An accepted decision changing the reserve preimage |
| **Closable before M3.5** | no |

## D021-L6 — A sealed run without a manifest is not a publication

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 6 |
| **Description** | A `feasible` run that never receives a manifest still carries a sealed `selection_result_sha256`. The seal is a deterministic checkpoint of terminal content — **not** a publication, **not** an approval, **not** a release artifact |
| **Affected M3 phase** | M3.3, M3.4 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | A real run could leave a sealed but unmanifested result, which must not be read as a result |
| **Publication impact** | **Material.** A sealed digest must never be presented as an approved or published artifact |
| **Mitigation** | Recorded; the approval packet states the publication status explicitly |
| **Stop condition** | Any presentation of a sealed digest as an approval or a release |
| **Required owner action** | none |
| **Closure evidence** | Not closable — it is a property of the design |
| **Closable before M3.5** | no |

## D021-L7 — The six explicit §8.4 arguments are asserted, not verified

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 7 (see §8.4) |
| **Description** | `dependency_lock_sha256`, `code_commit_identifier`, `runtime_python_version`, `configuration_sha256`, `decision_authority_sha256`, and `source_plan_sha256` are caller-supplied. S6 binds them immutably into `selector_policy_sha256` and therefore into the root, so a wrong value is permanently attributable — **but S6 cannot detect one**, because detecting it would mean reading the Git tree, the interpreter, the config, the decision directory, or the plan, which §8.4 prohibits outright |
| **Affected M3 phase** | **M3.3 — the first time these are supplied for a real artifact** |
| **Status** | `ACTIVE` |
| **Methodology impact** | None if the values are correct |
| **Reproducibility impact** | **Material.** A wrong value produces a root that binds a false claim about the environment that produced it |
| **Security impact** | None directly |
| **Operational impact** | **High at M3.3.** The operator must derive each of the six correctly and record how |
| **Publication impact** | The manifest's environment claims are only as good as these six |
| **Mitigation** | The deliberate trade: an auditable assertion beats a value silently inherited from whatever environment happened to run the code. The M3.3 evidence packet must record **how each of the six was derived**, so the assertion is checkable by a reviewer even though it is not checkable by the code |
| **Stop condition** | Any of the six being unavailable, ambiguous, or derived from an unclean tree |
| **Required owner action** | Confirm, at M3.3, the exact derivation method for each of the six |
| **Closure evidence** | Not closable without reversing the §8.4 prohibition, which is deliberate |
| **Closable before M3.5** | no |

## D021-L8 — What the structural fingerprint excludes

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 8 (see §8.1) |
| **Description** | `parser_run_id` is used only for cross-run consistency checking and is excluded from identity; duplicate identical structural rows are collapsed; row order is excluded; and the per-row identity, count, count-quality, free-text, and timestamp columns are excluded. **All five substantive structural fields — `region`, `state`, `observed_type`, `member_name`, `record_path` — are bound** |
| **Affected M3 phase** | M3.2, M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None — the excluded items are volume, provenance, and prose, not shape |
| **Reproducibility impact** | Positive: an identical reparse, a duplicate identical row, and any ordering change are provable digest no-ops |
| **Security impact** | None |
| **Operational impact** | A disagreement between parser runs on any of the five **fails closed** |
| **Publication impact** | Disclose what the fingerprint binds |
| **Mitigation** | Recorded for monitoring, not for change |
| **Stop condition** | A cross-run disagreement on any of the five fields |
| **Required owner action** | none |
| **Closure evidence** | An accepted decision changing the partition rule |
| **Closable before M3.5** | no |

## D021-L9 — The `leakage_attestation` literal records a claim

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 9 (see §8.4.1) |
| **Description** | The `leakage_attestation` literal **records** a claim; it does not **prove** one. Its truth rests on the S6 read set and the §20 test, not on the constant |
| **Affected M3 phase** | M3.3, M3.5 |
| **Status** | `ACTIVE` |
| **Methodology impact** | The attestation is only as true as the read set it describes |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | **The M3.3 evidence packet must name the exact read set** that makes the attestation true, so a reviewer checks the claim rather than the constant |
| **Publication impact** | **Material.** A leakage claim in a publication must rest on the read set, never on the literal |
| **Mitigation** | Recorded; the evidence packet carries the read set; M3.5 re-verifies it |
| **Stop condition** | The read set including anything the attestation denies |
| **Required owner action** | none |
| **Closure evidence** | Not closable — a literal cannot become a proof |
| **Closable before M3.5** | no |

## D021-L10 — The identity guard makes manifest fixtures heavier

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 10 (see §20) |
| **Description** | The v0.2 identity guard makes the existing `test_m23_pilot_schema.py` manifest fixtures materially heavier, not merely adjusted |
| **Affected M3 phase** | M3.1, M3.3 — any phase adding a lifecycle-adjacent fixture |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | New fixtures must construct a `feasible` run sealed by a **later** `UPDATE`; a pre-sealed `INSERT` is refused |
| **Publication impact** | None |
| **Mitigation** | Expected, and **not grounds for weakening any guard**. The generalizable lesson: when adding a lifecycle trigger, search the suite for fixtures that construct the state the trigger now forbids |
| **Stop condition** | Any proposal to weaken a guard to simplify a fixture |
| **Required owner action** | none |
| **Closure evidence** | Not closable — it is a consequence of the guards |
| **Closable before M3.5** | no |

## D021-L11 — Selection-run replacement, deletion, and identity mutation — **CLOSED**

| Field | Value |
|---|---|
| **Origin** | Decision 021 §19 item 11 |
| **Description** | Recorded at v0.4 as an open owner-facing finding that `pilot_selection_runs` was open to row replacement, deletion, and identity mutation |
| **Affected M3 phase** | — |
| **Status** | **`CLOSED`** at Decision 021 v0.5, by migration `0013` triggers 6, 7, and 8 |
| **Methodology impact** | — |
| **Reproducibility impact** | — |
| **Security impact** | — |
| **Operational impact** | — |
| **Publication impact** | — |
| **Mitigation** | Closed by the eight-trigger migration; §15.5 states the resulting append-once and identity guarantee without qualification |
| **Stop condition** | — |
| **Required owner action** | none |
| **Closure evidence** | Recorded in Decision 021 §19.11 and confirmed at Decision 023 acceptance |
| **Closable before M3.5** | already closed; **retained here as the audit trail, and never reopened silently** |

---

# Group 3 — Decision 022, item-46 applicability boundary

## D022-L1 — Reserve-rank applicability is per persisted package

| Field | Value |
|---|---|
| **Origin** | [Decision 022](../Decisions/decision_022_m23_s6_reserve_rank_applicability.md) |
| **Description** | Crosswalk item 46's reserve rank is applicable **once per persisted compatible reserve package** and is **structurally not applicable** for a selected target that instead carries the persisted `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition. Structural non-applicability never makes a feasible S5 run manifest-ineligible, and item 70 remains the total per-target coverage requirement |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None — it clarifies applicability and changes no crosswalk row, count, preimage, or identity |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | A zero-package run is a **first-class case, not an edge case**, in any M3.3 test or review |
| **Publication impact** | Disclose the applicability rule with any reserve-coverage figure |
| **Mitigation** | Accepted and implemented; **D023-O4** records that enforcement is consistent defence in depth |
| **Stop condition** | Any synthetic package, `reserve_rank = 0`, `null`, `"N/A"`, placeholder, or invented rank being created or serialized |
| **Required owner action** | none |
| **Closure evidence** | Not closable — it is a standing applicability rule |
| **Closable before M3.5** | no |

---

# Group 4 — Decision 023 §7, accepted S6 limitations

## D023-O1 — An empty sole-carrier crosswalk family fails closed

| Field | Value |
|---|---|
| **Origin** | [Decision 023](../Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md) §7 **O1** |
| **Description** | Where a milestone-plan §10 item is discharged by more than one serialized family, emptying one is accepted. Where a family is an item's **sole** carrier, an empty family makes the item unplaceable and raises `GateFailureError` |
| **Affected M3 phase** | **M3.3** |
| **Status** | **`ACTIVE — OWNER RULING PENDING`** — the live future owner-ruling condition Milestone 3 inherits unresolved |
| **Methodology impact** | Potentially material: a lawful real run could be refused at document verification |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | **The most likely M3.3 stop.** No accepted current S5 plan reaches this condition, but a real candidate universe is not an accepted plan |
| **Publication impact** | A refused document is not publishable, by construction |
| **Mitigation** | Fails closed by design (Decision 021 §21). Decision 022 is **not** broadened to pre-resolve it |
| **Stop condition** | **A lawful real run reaching an empty sole-carrier family. Stop and refer** |
| **Required owner action** | **An explicit owner ruling, if and only if a real run reaches it** — never resolved by a session reclassifying an item, adding a category, or changing a count |
| **Closure evidence** | Either an accepted owner ruling resolving the condition, or M3.5 acceptance recording that no real run reached it — the latter closes the *occurrence*, not the *rule* |
| **Closable before M3.5** | **no** |

## D023-O2 — The release root is assumed owner-controlled

| Field | Value |
|---|---|
| **Origin** | Decision 023 §7 **O2** |
| **Description** | `Path.write_text` follows a symlink pre-positioned at the content-derived output path. Symlink-resistant publication was never an accepted S6 requirement |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | None |
| **Security impact** | **The only security-relevant inherited limitation.** It assumes the release root is under the owner's control and not writable by another party |
| **Operational impact** | The M3.3 operator must confirm the release root is owner-controlled before writing a real manifest |
| **Publication impact** | A manifest written through a hostile symlink would fail verification, so a wrong artifact is detectable |
| **Mitigation** | Verification fails closed on wrong bytes, and no database row survives a failed write. The assumption is explicit rather than implicit |
| **Stop condition** | Evidence that the release root is writable by anything other than the owner |
| **Required owner action** | Confirm release-root control at M3.3 |
| **Closure evidence** | An accepted decision requiring symlink-resistant publication, plus a reviewed implementation |
| **Closable before M3.5** | no |

## D023-O3 — Atomicity governs newly created artifacts only

| Field | Value |
|---|---|
| **Origin** | Decision 023 §7 **O3** |
| **Description** | S6 atomicity governs artifacts **the current operation created**: a fault removes a newly created file and rolls back the row, leaving neither. A file that already existed at that exact content-derived name is **not** deleted |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | A pre-existing artifact at the content-derived path is possible on a retry; partial or wrong bytes fail verification and an authorized retry repairs the artifact through the normal construction path |
| **Publication impact** | None — wrong bytes are detected |
| **Mitigation** | Recorded; deleting another writer's artifact is deliberately not this operation's act |
| **Stop condition** | An unexplained pre-existing artifact at the content-derived path |
| **Required owner action** | none |
| **Closure evidence** | An accepted decision extending atomicity to pre-existing artifacts |
| **Closable before M3.5** | no |

## D023-O4 — Item-46 enforcement is consistent defence in depth

| Field | Value |
|---|---|
| **Origin** | Decision 023 §7 **O4** |
| **Description** | The Decision 022 applicability check and the per-record document-completeness check agree on every document; neither is vacuous and neither weakens the other |
| **Affected M3 phase** | M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None — reserve rank remains substantively enforced for every real package |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | None |
| **Publication impact** | None |
| **Mitigation** | Both checks were proven non-vacuous at acceptance across eight failure shapes |
| **Stop condition** | Either check becoming vacuous, or the two disagreeing on any document |
| **Required owner action** | none |
| **Closure evidence** | Not closable — it is a design property, recorded for monitoring |
| **Closable before M3.5** | no |

---

# Group 5 — Decision 024, boundary consequences

## D024-L1 — Assignment to Milestone 3 is not authorization

| Field | Value |
|---|---|
| **Origin** | [Decision 024](../Decisions/decision_024_m2_m3_boundary_governance.md) §8 |
| **Description** | Assigning an obligation to Milestone 3 is a governance relabelling; it starts nothing. Every phase requires all five entry conditions |
| **Affected M3 phase** | all |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | None |
| **Security impact** | Prevents an unauthorized live run |
| **Operational impact** | **Every phase must satisfy all five entry conditions before beginning** |
| **Publication impact** | None |
| **Mitigation** | Restated in Decision 026 §21, Decision 027 §20, and the master plan §6 |
| **Stop condition** | Any phase beginning with an unsatisfied entry condition |
| **Required owner action** | Explicit authorization, per phase |
| **Closure evidence** | Not closable — it is the standing rule |
| **Closable before M3.5** | no |

## D024-L2 — Every inherited control transfers unchanged

| Field | Value |
|---|---|
| **Origin** | Decision 024 §§5.3, 6 |
| **Description** | No gate, prohibition, owner ruling, validation requirement, identity, methodology, or accepted limitation was removed, weakened, renumbered, deferred, or rewritten by the M2 → M3 transfer |
| **Affected M3 phase** | all |
| **Status** | `ACTIVE` |
| **Methodology impact** | Every frozen definition, temporal rule, identifier rule, and leakage control still binds |
| **Reproducibility impact** | The bootstrap seed, cohort rules, and policy versions are unchanged |
| **Security impact** | The SEC identity, rate-limit, response-policy, and raw-store controls are unchanged |
| **Operational impact** | A phase may not simplify an inherited control because it is now under a new phase name |
| **Publication impact** | The Decision 006 prohibited-claims list still binds |
| **Mitigation** | The §5.2 traceability table maps each obligation to exactly one phase |
| **Stop condition** | Any inherited control found weakened in a Milestone 3 contract |
| **Required owner action** | none |
| **Closure evidence** | Not closable — it is the standing rule |
| **Closable before M3.5** | no |

---

# Group 6 — Decision 026, standing obligations

## D026-L1 — The final literature refresh before publication

| Field | Value |
|---|---|
| **Origin** | [Decision 026](../Decisions/decision_026_milestones_0_1_2_final_closeout.md) §12; [Decision 001](../Decisions/decision_001_novelty_boundary.md) |
| **Description** | The final literature refresh before publication remains **required** and was not discharged by Milestone 0 closure |
| **Affected M3 phase** | M3.5 and any later publication work |
| **Status** | `ACTIVE` |
| **Methodology impact** | The novelty boundary is not final until the refresh runs |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | None during M3.1–M3.4 |
| **Publication impact** | **Blocking.** No publication may proceed before the refresh, and Decision 001's six prohibited first-in-field claims and Decision 006's wider list both bind |
| **Mitigation** | Recorded in Decision 001, restated at closeout, restated here |
| **Stop condition** | Any publication proposal before the refresh |
| **Required owner action** | Commission the refresh before publication |
| **Closure evidence** | A completed literature refresh, reviewed and recorded |
| **Closable before M3.5** | no — and **Milestone 3 acceptance does not close it** |

## D026-L2 — The difficult-or-nonstandard-package quota

| Field | Value |
|---|---|
| **Origin** | Decision 026 §12; [Decision 018](../Decisions/decision_018_m23_s5_accession_selection_policy.md) §14 |
| **Description** | The difficult-or-nonstandard-package quota remains an **M2.5 verification obligation**, excluded from hard feasibility, never proxied, and never reported as satisfied |
| **Affected M3 phase** | M3.3, M3.5 |
| **Status** | `ACTIVE` |
| **Methodology impact** | One frozen cross-cutting quota is not measurable from authorized M2.3/M3.2 metadata |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | The M3.3 quota report must mark it deferred, never passed |
| **Publication impact** | **Material.** Any pilot-coverage claim must state that this quota is deferred to M2.5 |
| **Mitigation** | Excluded from hard feasibility by accepted policy; `REVIEW_PILOT_QUOTA_UNMEASURABLE_AT_M23` records it |
| **Stop condition** | Any report presenting it as satisfied, or any proxy substituted for it |
| **Required owner action** | none until M2.5 |
| **Closure evidence** | M2.5 retrieval-verified evidence, reviewed |
| **Closable before M3.5** | **no** |

## D026-L3 — Milestone 0's standing limitations

| Field | Value |
|---|---|
| **Origin** | Decision 026 §12 |
| **Description** | Milestone 0's standing limitations remain open: the Lin (2026) full-text recheck, and the Stage 2A/2B items still to freeze |
| **Affected M3 phase** | M3.5 and later |
| **Status** | `ACTIVE` |
| **Methodology impact** | Bears on the novelty boundary and on later stage design |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | None during M3.1–M3.4 |
| **Publication impact** | **Blocking alongside D026-L1** |
| **Mitigation** | Recorded and carried forward explicitly rather than dropped at closure |
| **Stop condition** | Any claim resting on an unfrozen Stage 2A/2B item |
| **Required owner action** | Complete the recheck and the freezes before the work that depends on them |
| **Closable before M3.5** | no |

---

# Group 7 — New at Milestone 3 master planning

## M3-L01 — Platform and filesystem assumptions

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning, 2026-07-31 |
| **Description** | The accepted atomicity guarantees assume a POSIX filesystem where a same-directory rename is atomic, a hard link is atomic and refuses to overwrite, and a directory `fsync` is meaningful. The operator platform is macOS on a local APFS volume |
| **Affected M3 phase** | M3.1, M3.2, M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | A network volume, a case-insensitive volume with unexpected collision behaviour, or a filesystem without durable `fsync` could break the atomicity properties the rehearsal proves |
| **Security impact** | A world-writable data root would defeat **D023-O2** |
| **Operational impact** | **Run every phase on a local volume**, never on a network share, an external volume mounted with unusual semantics, or a synchronized cloud folder |
| **Publication impact** | None |
| **Mitigation** | The operator runbook keeps the data root local; the rehearsal exercises the atomicity boundaries on the actual platform |
| **Stop condition** | Any evidence of a non-atomic rename, a silently overwritten hard link, or a lost `fsync` |
| **Required owner action** | Confirm the data root is a local, owner-controlled volume before M3.2 |
| **Closure evidence** | Not closable — it is an environmental assumption, restated per run |
| **Closable before M3.5** | no |

## M3-L02 — Synthetic-fixture limitations

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning |
| **Description** | The offline rehearsal proves the **workflow** against synthetic fixtures and scripted responses. It does not prove that real SEC payloads have the shapes the fixtures assume |
| **Affected M3 phase** | M3.1A, and it is what M3.2 tests against reality |
| **Status** | `ACTIVE` |
| **Methodology impact** | None — fixtures inform no research artifact |
| **Reproducibility impact** | A fixture that is unlike a real payload could leave a real failure mode unrehearsed |
| **Security impact** | None |
| **Operational impact** | **A passing rehearsal is not a guarantee about live data.** It is a guarantee about the workflow |
| **Publication impact** | None |
| **Mitigation** | Fixtures are built to the shape the accepted parsers already declare; the drift scenarios exist precisely because the real shape may differ |
| **Stop condition** | A real payload shape the rehearsal did not model, producing an unrehearsed code path |
| **Required owner action** | none |
| **Closure evidence** | M3.2 completing without an unrehearsed failure mode, recorded at Gate H |
| **Closable before M3.5** | **no** — but its residual risk narrows once Gate H passes |

## M3-L03 — First-real-instance uncertainty

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning |
| **Description** | Every Milestone 3 artifact — the real snapshot, the real selection, the real manifest, the real root — is a **first instance**. No prior real instance exists to compare against |
| **Affected M3 phase** | M3.2, M3.3, M3.4 |
| **Status** | `ACTIVE` |
| **Methodology impact** | An error in a first instance has no baseline to reveal it |
| **Reproducibility impact** | Internal reproducibility is provable (two clean rebuilds must agree); external comparison is not available |
| **Security impact** | None |
| **Operational impact** | **Two clean rebuilds are the substitute for a baseline**, and are mandatory |
| **Publication impact** | Any claim about the pilot rests on a single real construction |
| **Mitigation** | Two clean rebuilds producing identical selections, ordering, quota results, and root; full reconstruction and replay proofs; independent review at every consequential boundary |
| **Stop condition** | Two rebuilds disagreeing on any output |
| **Required owner action** | none |
| **Closure evidence** | M3.5 acceptance recording the reproducibility proofs |
| **Closable before M3.5** | no |

## M3-L04 — Live SEC availability

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning |
| **Description** | SEC source availability, content, and structure are outside this project's control. A source may be unavailable, moved, restructured, or temporarily degraded at the moment of the run |
| **Affected M3 phase** | M3.2 |
| **Status** | `ACTIVE` |
| **Methodology impact** | An unavailable required source blocks the census rather than degrading it |
| **Reproducibility impact** | A `living` source retrieved on a different day may return different content — which is why the raw store is append-only and supersession lineage is recorded |
| **Security impact** | None |
| **Operational impact** | `INDEX_INSTANCE_UNAVAILABLE`, `INDEX_REQUIRED_INSTANCE_MISSING`, and `OPERATING_CALENDAR_UNAVAILABLE` are the recorded outcomes |
| **Publication impact** | The manifest records the exact source observations retrieved, so the artifact is dated by construction |
| **Mitigation** | Required closed quarters block completion when missing; a differing later response is a new observation; the retrieval is restartable |
| **Stop condition** | A required source unavailable after the retry budget, or a closed-quarter artifact changed without an official explanation |
| **Required owner action** | A ruling if a required source is durably unavailable |
| **Closure evidence** | Gate H recording every required instance satisfied |
| **Closable before M3.5** | **no** — the underlying uncertainty is permanent even after one successful run |

## M3-L05 — Rate-limit behaviour under real conditions

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning |
| **Description** | The aggregate limiter's behaviour against the real service — whether 4 requests per second with burst 1 is accepted, and whether a `403` or an unqualified `429` occurs — has never been observed |
| **Affected M3 phase** | M3.2 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | Cooldowns lengthen the elapsed window; they change no identity |
| **Security impact** | A block-page response is a signal that the traffic profile was unacceptable |
| **Operational impact** | The **expected elapsed acquisition window is a floor, not a prediction.** One cooldown adds 600 seconds |
| **Publication impact** | None |
| **Mitigation** | The project rate is 4/s against a published ceiling of 10/s; aggregate halt on `403` or unqualified `429`; exactly one controlled post-cooldown request; a second cooldown is terminal |
| **Stop condition** | A second cooldown, or a `403` after one controlled retry |
| **Required owner action** | A ruling if the traffic profile must change |
| **Closure evidence** | Gate H recording zero cooldowns, or recording one and explaining it |
| **Closable before M3.5** | no |

## M3-L06 — Schema-drift uncertainty

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning |
| **Description** | Whether real SEC payloads currently match the shapes the accepted parsers expect is unknown until the first live run |
| **Affected M3 phase** | M3.2 |
| **Status** | `ACTIVE` |
| **Methodology impact** | Blocking drift stops the phase rather than producing degraded data |
| **Reproducibility impact** | None — drift is recorded, not absorbed |
| **Security impact** | None |
| **Operational impact** | **The most likely M3.2 stop.** An unknown extra field is retained and logged; a missing required field, an unexpected null, a changed type, or a malformed nested array is blocking |
| **Publication impact** | None |
| **Mitigation** | Fail-closed by design; the rehearsal proves the refusal; [`templates/schema_drift_incident.md`](templates/schema_drift_incident.md) is the record |
| **Stop condition** | **Any blocking drift event.** Never resolved by supplying a default, coercing a type, or dropping a row |
| **Required owner action** | **An explicit ruling on every drift incident** |
| **Closure evidence** | Gate H recording no unresolved drift |
| **Closable before M3.5** | no |

## M3-L07 — Interrupted-run uncertainty

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning |
| **Description** | A real acquisition may be interrupted by a signal, a crash, a power loss, or a network drop at a point the rehearsal modelled only synthetically |
| **Affected M3 phase** | M3.2, M3.3 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | A correctly recovered run must produce the identical final state; that identity is asserted, not assumed |
| **Security impact** | None |
| **Operational impact** | Recovery requires the receipt chain, the raw-store state, and the catalog state to agree |
| **Publication impact** | None |
| **Mitigation** | Rehearsal scenarios R6–R8 and R10 model interruption at each boundary and prove duplicate prevention; the recovery template is mandatory |
| **Stop condition** | **A safe-resume determination of `UNDETERMINED`.** Recovery uncertainty is a stop condition, not a judgement call |
| **Required owner action** | A ruling on any `UNDETERMINED` state |
| **Closure evidence** | A recovery record showing a clean resume with duplicate prevention proven, or a run that was never interrupted |
| **Closable before M3.5** | no |

## M3-L08 — Operator-error risk

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning |
| **Description** | Milestone 3 depends on a human operator performing steps in order, on the right machine, with the right approvals recorded. A live request cannot be un-sent, and an approval cannot be un-given |
| **Affected M3 phase** | all |
| **Status** | `ACTIVE` |
| **Methodology impact** | A mis-ordered step could produce an artifact under conditions the evidence does not describe |
| **Reproducibility impact** | An undocumented manual step is not reproducible |
| **Security impact** | The realistic path to a leaked SEC identity is a person pasting it, not code printing it |
| **Operational impact** | **The primary residual risk of the whole milestone** |
| **Publication impact** | An artifact produced out of order is not defensible |
| **Mitigation** | The sequential operator runbook; explicit command-status labels so a planned command is never typed; the "never print" list; the stop rule; mandatory receipts making each step's occurrence durable; gate checklists requiring a signature |
| **Stop condition** | Any step performed out of order, or any output not matching what the runbook says it should be |
| **Required owner action** | Follow the runbook in order; stop on the first mismatch |
| **Closure evidence** | Not closable — it is inherent to a human-operated milestone |
| **Closable before M3.5** | no |

## M3-L09 — Receipt-schema evolution

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning; [`execution_receipt_spec.md`](execution_receipt_spec.md) §12 |
| **Description** | The execution-receipt schema is versioned `m3-execution-receipt/1.0`. A version change **during** Milestone 3 would make receipts from different phases non-comparable |
| **Affected M3 phase** | all |
| **Status** | `ACTIVE` |
| **Methodology impact** | **None — receipts enter no governed identity**, so a schema change cannot alter any result |
| **Reproducibility impact** | None on artifacts; comparability of operational evidence across phases would suffer |
| **Security impact** | A schema change is a chance to introduce a prohibited field, which the fail-closed scan must catch |
| **Operational impact** | Reconciliation and recovery tooling would need to dispatch on version |
| **Publication impact** | None |
| **Mitigation** | The field set is frozen by Decision 027 §10; a **major** version change requires a new accepted decision; old receipts are never rewritten; every receipt carries its version |
| **Stop condition** | A receipt whose schema version the reader does not recognize |
| **Required owner action** | Accept a new decision before any major version change |
| **Closure evidence** | M3.5 confirming one schema version across the whole milestone |
| **Closable before M3.5** | no |

## M3-L10 — Request-budget estimation uncertainty

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning; master plan §15 |
| **Description** | Two M3.2 routes cannot be counted offline — `sec_submissions_historical`, whose count depends on the historical-file references named inside the retrieved bulk archive, and `sec_submissions_entity`, whose count depends on the reconciliation set actually needed. Both are marked `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN`. Additionally, the bulk submissions archive is a `living` source, so references may appear between the dry run and the live run |
| **Affected M3 phase** | M3.1B, M3.2 |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | The derivable component reproduces exactly — 69 required closed quarterly instances plus five one-shot routes, plan hash `25257d75…` at the accepted as-of. The deferred component does not, by construction |
| **Security impact** | None |
| **Operational impact** | **The budget is only exact once the Gate F dry run resolves both routes.** The 10% contingency covers exactly one nameable cause: newly appearing historical-file references |
| **Publication impact** | None |
| **Mitigation** | **No integer is invented.** The formula, every count input, and the deferral marker are stated; the hard ceiling binds regardless of what the formula resolves to; the run stops **before** the attempt that would exceed it |
| **Stop condition** | Reaching the hard ceiling; or a resolved count exceeding the approved budget without owner re-approval |
| **Required owner action** | **Approve the exact budget and the exact ceiling before network enablement** |
| **Closure evidence** | A Gate F plan resolving both routes, owner-approved, and a Gate H reconciliation showing actual within plan |
| **Closable before M3.5** | **no** — the estimation method's uncertainty outlives one successful run |

---

## What this register does not do

It closes nothing. It changes no accepted decision, methodology, identity, or limitation. It adds no
authority. **Every entry marked `ACTIVE` is live and binds the phases it names**, and **D023-O1**
remains an unresolved future owner-ruling condition that Milestone 3 inherits and must refer if a real
run reaches it.
