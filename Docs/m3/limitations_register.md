# Milestone 3 — Limitations Register

**Status:** seeded at Milestone 3 master planning. **No inherited limitation is closed by this
document.**
**Controlling records:** [Decision 027](../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§11 and proposed [Decision 028](../Decisions/decision_028_m3_1_readiness_corrections.md) §§4, 9–11
(controlling once accepted).
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
| Milestone 3 — new at planning, **M3-L13** new at the T4 preflight, and **M3-L14**–**M3-L16** new at the post-T5 remediation acceptance | 16 | 12 `ACTIVE`; **M3-L11** and **M3-L12** **`CLOSED` 2026-08-03**; **M3-L13** **`CLOSED` — DECISION 048**; **M3-L14** **`CLOSED` — DECISION 056** (2026-08-09; accepted candidate `2c18e89…` at tree `6f77deaf…`) |
| **Total** | **37 open (all `ACTIVE`), 5 closed** | |

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
| **Description** | The offline rehearsals prove the **workflow** against synthetic fixtures and scripted responses. They do not prove that real SEC payloads have the shapes the fixtures assume, or that a real candidate universe behaves like a real-shaped one |
| **Affected M3 phase** | M3.1A (acquisition, A1–A12) and M3.3A (execution, E1–E8); M3.2 and M3.3B test them against reality |
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
| **Mitigation** | Rehearsal scenario A11's four abort/recovery variants (a)–(d) model interruption at each boundary and prove duplicate prevention; the recovery template is mandatory |
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
| **Description** | The execution-receipt schema is versioned `m3-execution-receipt/2.0` before the first receipt exists. A later version change **during** Milestone 3 would make receipts from different phases non-comparable |
| **Affected M3 phase** | all |
| **Status** | `ACTIVE` |
| **Methodology impact** | **None — receipts enter no governed identity**, so a schema change cannot alter any result |
| **Reproducibility impact** | None on artifacts; comparability of operational evidence across phases would suffer |
| **Security impact** | A schema change is a chance to introduce a prohibited field, which the fail-closed scan must catch |
| **Operational impact** | Reconciliation and recovery tooling would need to dispatch on version |
| **Publication impact** | None |
| **Mitigation** | Decision 028 corrects field timing and freezes v2 before any receipt exists; a later **major** version change requires a new accepted decision; old receipts are never rewritten; every receipt carries its version |
| **Stop condition** | A receipt whose schema version the reader does not recognize |
| **Required owner action** | Accept a new decision before any major version change |
| **Closure evidence** | M3.5 confirming one schema version across the whole milestone |
| **pre-first-receipt note** | The Decision 027 v0.2 and Decision 028 corrections were made **before any receipt was ever produced**. No v1 receipt exists, cross-phase comparability has not yet arisen, and no migration or compatibility shim is required |
| **Closable before M3.5** | no |

## M3-L10 — Request-budget derivation dependency

| Field | Value |
|---|---|
| **Origin** | Milestone 3 master planning; revised at Decision 027 v0.2 |
| **Description** | Two M3.2 routes cannot be counted before access — `sec_submissions_historical`, whose count depends on the historical-file references named inside the bulk-submissions object, and `sec_submissions_entity`, whose count depends on the reconciliation set actually needed. **v0.2 resolves this by derivation rather than estimation:** M3.2A acquires only sources whose count is derivable beforehand; transport is then disabled, the bootstrap objects are frozen, the dependent references are **derived from them**, and a **second** plan and ceiling are separately owner-approved before M3.2B |
| **Affected M3 phase** | M3.1B, M3.2A, M3.2B |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | The M3.2B count is reproducible **given the frozen M3.2A objects**, and not before. That dependency is structural, not an estimate |
| **Security impact** | None |
| **Operational impact** | **Two owner approvals, not one.** M3.2A's approval never covers M3.2B. The bulk-submissions archive is a `living` source, so a re-run of M3.2A may name a different reference set — which is why the derivation happens after the freeze, over fixed bytes |
| **Publication impact** | None |
| **Mitigation** | **No integer is invented and no contingency exists.** The v0.1 10% allowance is withdrawn: it padded for exactly this dependency instead of removing it. Each window's count is derived from explicit inputs or frozen objects; the hard ceiling binds regardless; the run stops **before** the attempt that would exceed it |
| **Stop condition** | Equality with a window's ceiling while planned work remains; M3.2B beginning without its own derived plan and recorded approval; or the derived set disagreeing with what the frozen objects name |
| **Required owner action** | **Approve an exact budget and ceiling per window, before that window's network enablement** |
| **Closure evidence** | Both windows planned, approved, executed, and reconciled at Gate H with no divergence the plans do not explain |
| **Closable before M3.5** | **no** — the derivation dependency is permanent even after one successful run |

## M3-L11 — The private evidence root is not yet git-ignored

| Field | Value |
|---|---|
| **Origin** | Decision 027 v0.2 §10.1; owner ruling recorded by accepted Decision 028 §11 |
| **Description** | The two-layer evidence model requires completed operational evidence to live in an owner-controlled private evidence root **outside the repository**. `.gitignore` has **not** been updated to defend against an accidental in-tree private root, because `.gitignore` is a configuration file and the planning sessions are documentation-only |
| **Affected M3 phase** | M3.1 onward — every phase that produces evidence |
| **Status** | **`CLOSED` — 2026-08-03**, under the owner's explicit Decision 029 §12 step-17 closure authorization, on the register's own closure-evidence list, every item satisfied: the exact `.gitignore` entry (`/.m3-private-evidence`, in the frozen accepted tree); the hygiene refusal for a file, directory, or symlink at the reserved path (`scripts/check_repo_hygiene.py` + `tests/unit/test_repo_hygiene.py`); the resolved-path CLI protection with equal/inside/ancestor and bidirectional symlink-bypass tests (`m3/evidence_paths.py` + `tests/unit/test_m3_evidence_paths.py`); full validation (first durable §17 review `M3_1_SECTION_17_REVIEW: PASS` and the step-14 independent acceptance review, both green over the full gate sequence); independent M3.1 acceptance (`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`, artifact SHA-256 `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`, commit `24fba32413bb6c5dade60a64182e42510afe6f88`) with owner acceptance recorded by accepted Decision 031; and the committed checkpoint — annotated tag `m3.1-complete` (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled target `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`), verified locally and remotely. Residual nonblocking note, disclosed and owner-accepted (Decision 031): private-evidence backups remain same-device accidental-deletion snapshots only; an off-device backup remains an owner matter and is a pre-live-operation decision under the M3.2 contract |
| **Methodology impact** | None |
| **Reproducibility impact** | None |
| **Security impact** | **Material.** The repository is public. Without the ignore entry, an evidence root created inside the checkout could be staged by a careless `git add`, publishing completed packets — including an unpublished root — irreversibly |
| **Operational impact** | Until it is closed, the defence is procedural: the private root lives **outside** the checkout, and `make hygiene` plus explicit-path staging catch the rest |
| **Publication impact** | An accidental commit of a root-approval packet **is** a publication, and cannot be retracted from public history |
| **Mitigation** | The private root is outside the repository by policy; staging is by exact path, never `git add -A`; Decision 028 requires the root `.gitignore` rule `/.m3-private-evidence`, an explicit hygiene refusal for any object at that reserved path, and resolved-path refusal in every M3 evidence-output CLI |
| **Stop condition** | A completed evidence artifact found tracked, or an evidence root found inside the checkout |
| **Required owner action** | Accept the bounded M3.1 contract after independent review, then issue exact-path implementation authorization |
| **Closure evidence** | The exact `.gitignore` entry, hygiene refusal for a file/directory/symlink at the reserved path, resolved-path CLI tests including ancestor and symlink bypasses, full validation, independent M3.1 acceptance, and a committed checkpoint |
| **Closable before M3.5** | **yes**, once the authorized configuration change lands |

## M3-L12 — Inherited exact-quarter-end planner defect

| Field | Value |
|---|---|
| **Origin** | Decision 027 v0.2 §15.1; owner ruling recorded by accepted Decision 028 §4 |
| **Description** | [Decision 013](../Decisions/decision_013_pilot_selection_mechanics.md) §1 requires closed 2026 Q2 at as-of `2026-06-30`. The planner checks “containing quarter” before `quarter_end <= as_of_date`, contrary to its own module contract, and misclassifies an exact quarter end as provisional. Decision 028 preserves Decision 013 and requires the total order `start > as_of` → unplanned; else `end <= as_of` → closed; else open, under `quarterly-index-instances/2.0` |
| **Affected M3 phase** | **M3.1B (Gate F)**, then M3.2A |
| **Status** | **`CLOSED` — 2026-08-03**, under the owner's explicit Decision 029 §12 step-17 closure authorization, on the register's own closure-evidence list, every item satisfied: planner-v2 implementation (`quarterly-index-instances/2.0`) with the exact-quarter-end, interior-date, future-quarter, open-quarter, and version-mismatch boundary tests, in the frozen accepted tree; full validation (the §17 review and the step-14 independent acceptance review, both green); independent M3.1 acceptance (artifact SHA-256 `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`, commit `24fba32413bb6c5dade60a64182e42510afe6f88`) with owner acceptance recorded by accepted Decision 031; the committed checkpoint — annotated tag `m3.1-complete` (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled target `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`), verified locally and remotely; and a Gate F plan whose required-quarter set matches accepted authority (request-plan SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, 70 quarters `2009QTR1`–`2026QTR2` including the closed 2026 Q2 that Decision 013 §1 requires at as-of `2026-06-30`). Sequencing distinction preserved exactly per Decision 030 Ruling D: the **Gate-F-facing requirement was satisfied on 2026-08-03, before the Gate F checklist was signed** (`M3-L12 GATE-F-FACING REQUIREMENT: SATISFIED`), and only the **administrative closure** was deferred to the M3.1 acceptance and checkpoint sequence now complete — M3-L12 was not a Gate F blocker after Decision 030. Decision 013 remains byte-for-byte unchanged |
| **Methodology impact** | **Material.** One quarter of accepted coverage is either included or excluded, changing the candidate universe the pilot is drawn from |
| **Reproducibility impact** | Both behaviours are deterministic. The problem is not nondeterminism — it is that the deterministic answer disagrees with the accepted record |
| **Security impact** | None |
| **Operational impact** | **Gate F cannot pass while they disagree.** A request plan that disagrees with the accepted coverage cutoff is not a plan a budget can be approved against |
| **Publication impact** | Any coverage claim must rest on the resolved position, not on whichever component happened to be consulted |
| **Mitigation** | Decision 028 records the correction and policy-version boundary without editing Decision 013. **v0.1's derived counts, which were faithful to the defective planner and not to Decision 013 §1, remain withdrawn** |
| **Stop condition** | Gate F attempting to pass with the discrepancy open; or **any change to Decision 013 made to accommodate the planner** |
| **Required owner action** | Accept the bounded M3.1 contract after independent review, then authorize implementation. **Decision 013 remains byte-for-byte unchanged** |
| **Closure evidence** | Planner v2 implementation; exact-quarter-end, interior-date, future-quarter, open-quarter, and version-mismatch tests; full validation; independent M3.1 acceptance; committed checkpoint; and a Gate F plan whose required-quarter set matches accepted authority |
| **Closable before M3.5** | **yes — and it must close before Gate F passes** |

## M3-L13 — `RawStore.store()` buffered the whole object in memory

| Field | Value |
|---|---|
| **Origin** | Accepted [Decision 039](../Decisions/decision_039_m3_2_t2_2_t2_3_stage_acceptance.md) §6.4, which recorded the `RawStore` resource limitation as an accepted deferral and carried it to T4; restated by accepted [Decision 040](../Decisions/decision_040_m3_2_t2_4_implementation_authorization.md) §19 and accepted [Decision 042](../Decisions/decision_042_m3_2_t2_4_acceptance_and_publication.md) §1; located exactly and dispositioned by accepted [Decision 047](../Decisions/decision_047_m3_2_t4_operational_preflight_authorization.md) §§3 (ruling 047-B), 5, 6 |
| **Description** | `src/disclosure_drift/sec/raw_store.py`, `RawStore.store()`, accumulated the **complete decoded object body** in one Python `bytearray` (`buffer.extend(chunk)`) on **every** call — including `compress=False`, where the buffer was never read — and then read the **entire promoted file back** with `Path.read_bytes()` to compute `stored_sha256` and `stored_size_bytes`. On the `compress=True` path it additionally materialized a `bytes(buffer)` copy, the whole compressed output, and a whole decompressed copy for the round-trip check. The upstream retrieval already streams to a spool file deliberately (`SnapshotStore._spool_stream` / `_file_chunks`, "yield a spooled response without reading it all into memory"); the store layer negated that intent immediately downstream. Measured directly on an 8 MiB payload in 512 KiB chunks with `tracemalloc`: **peak traced allocation 2.12× object size for `compress=False` and 3.80× for `compress=True`**. `RawStore.verify()` and the existing-object deduplication branch performed the same whole-file reads |
| **Affected M3 phase** | **M3.2A**, and every later phase that stores or verifies a raw object |
| **Status** | **`CLOSED` — DECISION 048** (2026-08-07), under accepted [Decision 048](../Decisions/decision_048_m3_2_pre_t4_rawstore_acceptance_and_publication.md) §7 (ruling 048-H), on this entry's own closure-evidence list, every item satisfied: the **Decision 047 authorization** (`bc3d170a155aaa6c196536109ef57dd841226675`); the **accepted corrected implementation** (`833a192839e888720389c4757250234b5cb219b7`) at its **accepted tree** (`c2d95badd8d137ebbb00a642d087fb03e1ec7353`), across its exact two-path envelope; the **independent PASS artifact** [`Docs/m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md`](reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md), **SHA-256 `7bd5a5441fc4a0218e18a5a5daddf5a53c4436a938ea942fc6f84835d265fc42`**, verdict `M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEW_PASS` with **BLOCKER 0 · MAJOR 0**, at **review commit `9406afbe88e83f7a0f0a52db290f9a220d01e6bc`**; and the **owner's separate acceptance recorded in Decision 048**. The rereview independently established bounded memory for valid objects (object size grown 8× at 1.00×–1.40× peak growth), **108/108** deterministic-gzip cases byte-exact, **12/12** independent mutations `KILLED`, and preserved durability, deduplication, and API. **Two nonblocking observations are carried forward without reopening the accepted candidate** and expressly **create no register entry** (Decision 048 §§6.1–6.2): MINOR-1 `ACCEPTED_NONBLOCKING_TEST_STRENGTH_OBSERVATION — DEFERRED` (the committed suite contains no isolated mutation killer for the `content_sha256` comparison; production enforcement is independently demonstrated correct and no production defect exists) and MINOR-2 `ACCEPTED_NONBLOCKING_CORRUPT_PATH_RESOURCE_OBSERVATION — DEFERRED` (`zlib` may retain a large trailing-garbage tail in `unused_data` while verifying an **already-corrupt** object; invalid objects stay correctly refused, lawful verification stays bounded-memory, and `RawStore.verify()` has zero production callers). The historical description above is **preserved and never erased** (Decision 047 ruling 047-C) |
| **Methodology impact** | **None.** No research definition, identity, hash preimage, or stored byte changes. `content_sha256`, `stored_sha256`, the deterministic-gzip output, and every content-addressed identity are byte-identical before and after |
| **Reproducibility impact** | **None** — and this is load-bearing. The correction is only sound because streaming deterministic gzip is byte-identical to the frozen one-shot `compress_deterministically`; that equality is asserted directly by the accepted tests rather than assumed |
| **Security impact** | None. No identity, credential, path, or payload reaches an artifact by either implementation |
| **Operational impact** | **Material, and the reason this was a T4 concern.** The M3.2A plan's `sec_bulk_submissions` route retrieves a full EDGAR bulk archive whose size is **not recorded in any repository evidence** and cannot be established without a live request. Under the pre-correction implementation a machine unable to hold roughly twice that archive resident would fail with `MemoryError`, swap thrash, or an OS kill **mid-window, on the single largest retrieval** — an interruption inside a live window, with attempts already consumed, recovery required before any resume, and a possible `.part` or orphan. Data integrity was never at risk: the atomic protocol preserves evidence and overwrites nothing. **Availability was.** Decision 047 ruling 047-H separately imposes a conservative `FREE DISK >= 50 GiB` T5 entry floor, which the correction does not replace |
| **Publication impact** | None |
| **Mitigation** | The Decision 047 §6 substage makes hashing, sizing, compression, decompression, and verification incremental over bounded blocks in `store()`, `verify()`, and the deduplication branch, so storage memory no longer scales with object size. Every accepted durability semantic is preserved: `.part` staging, content-addressed identity, no-overwrite atomic create-once hard-link promotion, file and directory `fsync`, evidence preservation after failure, exact deduplication, and unchanged fail-closed failure handling. **The public `RawStore` API is unchanged.** A non-vacuous instrumentation-based positive control and a threshold-free incremental-write control both fail against the pre-correction implementation |
| **Stop condition** | Any evidence that the streaming compressor does not reproduce `compress_deterministically` byte-for-byte; any stored-object hash, size, or round-trip verification becoming inexact; any previously fail-closed condition becoming acceptance; or an out-of-memory or resource failure during a live window notwithstanding the correction |
| **Required owner action** | **Accept or refuse the Decision 047 §6 substage** after its fresh independent review. Until that acceptance, this entry stays `ACTIVE` and the substage remains local and unpublished |
| **Closure evidence** | The accepted two-path correction; its non-vacuous streaming and memory positive controls; byte-identical deterministic-gzip, `content_sha256`, `stored_sha256`, and stored-size proofs across both compression modes; the preserved durability, deduplication, quarantine, reconciliation, and failure-preservation tests; full validation green; a fresh independent implementation review by a non-author session; and the owner's separate acceptance recorded in a Decision and this register |
| **Closable before M3.5** | **yes — and it should close before T5 opens a live window** |

## M3-L14 — Receiptless ledger-coverage cardinality is evaluated per manifest

| Field | Value |
|---|---|
| **Origin** | Post-T5 remediation independent rereview finding **F1**, accepted as a nonblocking limitation by accepted [Decision 052](../Decisions/decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) §7 (ruling 052-E) |
| **Description** | In the explicit receiptless first-invocation inspection, ledger coverage is decided **independently for each raw-lineage manifest**. Reservations are not consumed across manifests, so one `ops_retrieval_attempts` reservation can satisfy the coverage test for more than one owned same-URL segment. Measured directly by the independent reviewer: **1 reservation + 2 owned segments** reports a consumed count of **1** with determination `UNSAFE`, where the durable floor is **2** and the correct fail-closed outcome is `UNDETERMINED` |
| **Affected M3 phase** | M3.2 — any future receiptless inspection performed over a **non-empty** attempt ledger |
| **Status** | **`CLOSED — DECISION 056`** (2026-08-09) |
| **Owner-selected correction** | Accepted [Decision 055](../Decisions/decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md) §8 (ruling 055-D) **resolves this entry's two-way owner choice in favour of the fail-closed option**: a **global one-to-one reservation-consumption rule across all owned receiptless lineage segments**, in which a durable reservation may satisfy **at most one** segment. **`UNDETERMINED`** is returned on unmatched cardinality, multiply matchable cardinality, duplicate reservation reuse, source/URL/run mismatch, a leftover contradiction, or **any inability to establish an exact bijection**. The measured counterexample — **1 reservation + 2 owned same-URL segments** — **must produce `UNDETERMINED`**, never consumed count **1** with `UNSAFE`. Receiptless inspection remains inspection-only and can never return `SAFE` or authorize continuation. **Selecting the correction is not closing the entry** |
| **Methodology impact** | None. No research definition, cohort rule, outcome, identity, or hash preimage is involved |
| **Reproducibility impact** | None — the behaviour is deterministic. The defect is that the deterministic answer can under-report a durable floor, not that it varies |
| **Security impact** | None |
| **Operational impact** | **Bounded, and absent from the real incident.** The interrupted initial T5 invocation's `ops_retrieval_attempts` table is **empty**, so no reservation exists to over-apply and the accepted count of **1 of 801** is unaffected. The condition is unreachable on the governed reserve-before-send path as currently constructed, which commits one reservation per physical send before that send occurs. It **cannot authorize continuation** under any value, because receiptless mode never returns `SAFE` (Decision 051 §8) |
| **Publication impact** | Disclose the per-manifest cardinality rule with any consumed-count figure derived from receiptless inspection over a non-empty ledger |
| **Mitigation** | **Implemented and accepted.** Decision 055 §8 selected the global one-to-one rule. Decision 056 accepts candidate `2c18e89…`, its non-vacuous counterexample test, full validation, independent review, bounded MAJOR remediation, and final owner verification. Receiptless mode remains structurally unable to return `SAFE` or authorize continuation |
| **Stop condition** | Any regression to per-manifest reservation reuse, any non-bijective match reported as determinate, or any observed consumed count that disagrees with the durable reservation-plus-lineage floor |
| **Required owner action** | none — completed by Decision 056 |
| **Closure evidence** | **Complete.** Decision 055 §8 selected the correction; accepted candidate `2c18e89b73048a6cf7ce8cd528325f2a0c50a9ac` at tree `6f77deaf0aaf4be3e365d3d0be8c22a89c737802` implements it; the required non-vacuous old-behaviour counterexample fails before the correction and passes after it; full validation is green; fresh Opus 5 Max non-author review completed; its owner-adjudicated MAJOR was remediated in one bounded pass; and Decision 056 separately accepts and closes the entry |
| **Closable before M3.5** | **closed — Decision 056** |

## M3-L15 — Second-SIGTERM suppression has no regression test

| Field | Value |
|---|---|
| **Origin** | Post-T5 remediation independent rereview finding **F2**, accepted as a deferred one-test gap by accepted [Decision 052](../Decisions/decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) §8 (ruling 052-F) |
| **Description** | The `delivered` latch that suppresses a **second** SIGTERM during live-acquisition cleanup — so cleanup and any single terminating-receipt attempt are never duplicated — is implemented and was **directly verified** by the independent reviewer through process-level fault injection. **No committed test guards it**, so a future edit could remove the latch without failing the suite |
| **Affected M3 phase** | M3.2, and every later phase that runs the governed live-acquisition lifecycle |
| **Status** | `ACTIVE` |
| **Methodology impact** | None |
| **Reproducibility impact** | None — the production behaviour is correct today and was independently confirmed |
| **Security impact** | None |
| **Operational impact** | **A test-strength gap, not a production defect.** A regression would only surface under a second SIGTERM delivered during cleanup of a live acquisition |
| **Publication impact** | None |
| **Mitigation** | The behaviour was directly verified once by fault injection at rereview. Decision 052 §8 expressly **does not reopen** the accepted stage to add the test |
| **Stop condition** | Any edit to the scoped SIGTERM handling that is not accompanied by a test covering second-signal suppression |
| **Required owner action** | none unless the stop condition occurs; the gap may be discharged by a later separately authorized packet |
| **Closure evidence** | A committed regression test that fails when the `delivered` latch is removed, inside a later authorized envelope, with full validation green |
| **Closable before M3.5** | yes, under a later separately authorized packet |

## M3-L16 — No clean-run carry-in interface for the consumed baseline of 1

| Field | Value |
|---|---|
| **Origin** | Post-T5 remediation independent rereview observation **O1**, recorded as a mandatory live-readiness obligation by accepted [Decision 052](../Decisions/decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md) §9 (ruling 052-G) |
| **Description** | Accepted [Decision 051](../Decisions/decision_051_m3_2_post_t5_remediation_governance.md) §§5, 12 fix that cumulative consumption starts at **1**, with **5** bulk-route and **800** total attempts remaining, and that no future run may reset the count. The accepted remediation candidate provides **no non-resume mechanism for carrying that historical baseline of 1 into a clean new run**. The gap is **outside** Decision 051's four-change scope and is correctly absent from the accepted candidate — it is not a defect in that candidate |
| **Affected M3 phase** | **M3.2A** — any future clean new invocation; and every later phase that depends on one |
| **Status** | **`ACTIVE — BLOCKS LATER LIVE AUTHORIZATION; IMPLEMENTATION ACCEPTED; ORPHAN ADOPTION AND OWNER CLOSURE OUTSTANDING`** |
| **Owner-selected architecture** | Accepted [Decision 055](../Decisions/decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md) §§5–7, 9 (rulings **055-A**, **055-B**, **055-C**, **055-E**) fixes the exact carry-in mechanism this entry demanded. **055-A**: the cumulative ceiling stays exactly **801**, historical seed **`H` = 1**, future cumulative consumption is `H` plus new durable reservations, the frozen plan and its 75 logical requests are unchanged, the global `PhysicalAttemptCeiling` is constructed with `approved_ceiling` 801 and `consumed` 1, and **no `802`, additive, shadow, reset, or reinterpreted ceiling** is permitted; route attribution to `sec_bulk_submissions` is **evidence and reporting only**, with **no per-route runtime refusal**. **055-B**: **one explicit clean-root carry-in interface that is never resume** and refuses coexistence with `--resume-from`, carried by a canonical-JSON artifact under schema **`m3-carry-in-authority/1.0`**, identified by the SHA-256 of its exact canonical bytes, validated before transport construction, and **consumed exactly once** by a deterministic `ops_checkpoints` primary key inside the **same existing `BEGIN IMMEDIATE`** run-registration transaction — **no migration** — with an all-or-nothing commit and **no automatic reissue if the authority burns before the wire**. **055-C**: writer schema **`m3-execution-receipt/3.0`** with version dispatch, existing `2.0` receipts byte-unchanged and mixed-chain usable, a required `carry_in_authority_sha256` on a clean carry-in root only, and a chain walker that adds the root carry-in **exactly once**. **055-E**: **Path B** — a separately authorized, offline, one-time, **verified orphan adoption must precede any clean carry-in run**, and Decision 055 neither designs it in executable detail nor performs it |
| **Methodology impact** | None directly; but a run that silently restarted the count at zero would breach the accepted ceiling accounting |
| **Reproducibility impact** | None |
| **Security impact** | None |
| **Operational impact** | **Material and blocking.** **No clean new run may be authorized until an exact owner-approved carry-in mechanism is available and validated.** Until then the project is **not** ready for live operation, and no record, status marker, or session may claim live readiness |
| **Publication impact** | Any statement of remaining request headroom must rest on the accepted baseline of 1 of 801, never on a fresh run's internal counter |
| **Mitigation** | The exact Decision 055 mechanism is implemented, independently reviewed, corrected once, owner-verified, and accepted by Decision 056 at candidate `2c18e89…`. `LIVE_READINESS: NOT_CLAIMED` still stands because the historical orphan remains unadopted and M3-L16 remains open |
| **Stop condition** | **Any proposed clean new run, live authorization, or live-readiness claim while this entry is open.** Also: any run observed starting its consumed count at zero. **Additionally, per Decision 055 §9: any clean run, transport construction, network use, or SEC contact before the separately authorized offline orphan adoption is executed, independently verified, and accepted with zero unresolved historical orphan mismatch** — the accepted recovery classification is `UNDETERMINED` because of a raw-store/catalog **orphan mismatch**, not because attempt evidence is ambiguous, so carry-in accounting alone can never clear it |
| **Required owner action** | The architecture and implementation limbs are discharged by Decisions 055 and 056. What remains is the separately authorized, offline, one-time verified orphan adoption of Decision 055 §9, its independent verification and owner acceptance with zero unresolved orphan mismatch, and a separate M3-L16 closure act |
| **Closure evidence** | **Partially complete.** Decision 055 fixes the mechanism; Decision 056 accepts candidate `2c18e89…`, all mandatory tests, full validation, independent review, bounded MAJOR remediation, and final owner verification. Still required: accepted orphan adoption under Decision 055 §9 leaving zero unresolved historical orphan mismatch, followed by the owner's separate closure act |
| **Closable before M3.5** | **yes — and it must close before any clean new M3.2A run is authorized** |

## What this register does not do

This register does not close a limitation on its own; it records closures made by accepted owner
decisions. It changes no accepted decision, methodology, or identity and adds no authority. **Every
entry marked `ACTIVE` is live and binds the phases it names.**

**D023-O1 is the sole unresolved owner-ruling condition** and is referred only if a real run reaches
it — `LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED` (Decision 030 Ruling E).
Every future Milestone 3 phase carries it forward as a mandatory stop-and-refer condition.
**M3-L11 and M3-L12 are `CLOSED` (2026-08-03)** under the owner's explicit Decision 029 §12 step-17
closure authorization, each on its own complete closure-evidence list: bounded implementation and
tests in the frozen accepted tree, full validation, independent M3.1 acceptance
(`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`), owner acceptance recorded by accepted Decision 031,
and the committed checkpoint — the annotated `m3.1-complete` tag (object `638a02b7…`, peeled
`4cd2c72…`), verified locally and remotely. The former "Gate F cannot pass while M3-L12 remains
active" sentence is historical: Decision 030 Ruling D recorded
`M3-L12 GATE-F-FACING REQUIREMENT: SATISFIED` before the Gate F checklist was signed, with only the
administrative closure deferred to the acceptance and checkpoint sequence now complete.
**M3-L13 is `CLOSED` — DECISION 048 (2026-08-07)**, on its own complete closure-evidence list: the
Decision 047 authorization (`bc3d170…`), the accepted corrected implementation (`833a192…`) at tree
`c2d95bad…`, the independent PASS artifact
`Docs/m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md`
(SHA-256 `7bd5a544…`, verdict `M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEW_PASS`,
**BLOCKER 0 · MAJOR 0**) at review commit `9406afb…`, and the owner's separate acceptance in
Decision 048. Its two accepted nonblocking observations (Decision 048 §§6.1–6.2) are carried on that
entry and **create no register entry of their own**. The historical description is preserved.
**M3-L14, M3-L15, and M3-L16 were new and `ACTIVE`** at the post-T5 remediation acceptance (accepted
[Decision 052](../Decisions/decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md),
2026-08-08), carrying rereview findings **F1** and **F2** and observation **O1**. They are owner-
accepted as nonblocking **for that accepted stage only**. **M3-L14 is now `CLOSED — DECISION 056`; M3-L15 and M3-L16 remain active, and M3-L16 blocks any
later clean-run or live authorization until it closes**. Decision 052's remaining nonblocking
observations **O2**, **O3**, and **O4** are recorded at Decision 052 §10 and **create no register
entry of their own**.
