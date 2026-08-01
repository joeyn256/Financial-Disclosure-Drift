# TEMPLATE — Real-Snapshot Evidence Packet

**This file is a blank template. No real snapshot, selection, or manifest exists.**
Copy it, fill every field, and retain the completed copy as evidence. Do not edit this template in
place.

**Purpose:** to present everything M3.3 produced — the frozen real snapshot, the deterministic
selection, the reserves and dispositions, the reconstruction and replay proofs, and the exact
manifest identities — in a form a reviewer can check against persisted rows.
**Phase:** M3.3
**Controlling records:** [Decision 027](../../Decisions/decision_027_m3_master_plan_and_operational_readiness.md);
[Decision 013](../../Decisions/decision_013_pilot_selection_mechanics.md) §§2, 5–7;
[Decision 018](../../Decisions/decision_018_m23_s5_accession_selection_policy.md);
[Decision 019](../../Decisions/decision_019_m23_s5_storage_to_pure_input_mapping.md) §9;
[Decision 020](../../Decisions/decision_020_m23_s5_4_reserve_architecture.md);
[Decision 021](../../Decisions/decision_021_m23_s6_manifest_construction.md) §§6–13;
[Decision 022](../../Decisions/decision_022_m23_s6_reserve_rank_applicability.md);
[`milestone_2_3_pilot_selection_plan.md`](../../../Milestones/milestone_2_3_pilot_selection_plan.md) §10;
[`milestone_03_master_plan.md`](../../../Milestones/milestone_03_master_plan.md) phase M3.3.
**Completion token:** on a complete packet,
`M3_3_REAL_PILOT_MANIFEST_CONSTRUCTED_READY_FOR_ROOT_APPROVAL`.

---

## 0. Handling

- **The completed copy is PRIVATE evidence.** It lives in the owner-controlled private evidence root,
  never in the repository. Only its type, phase, status, SHA-256, and reference identifier go into
  [`evidence_index.md`](evidence_index.md).
- **It contains unpublished governed identities** — the snapshot ID, every component digest, the
  root, and the manifest ID. **None of them is ever written into the repository.**
- **Never record** the SEC identity, any credential, any absolute personal path, any raw response
  body, any filing text, or any outcome value.
- **Relative paths only.**
- **This packet is not an approval.** See §16, which is mandatory.
- **Immutable once signed.**

## 1. Identification

| Field | Value |
|---|---|
| Phase | M3.3B (the real execution; M3.3A's rehearsal record is a separate artifact) |
| M3.3A execution-rehearsal reference | `_______` |
| M3.3A independent-review result | `_______` |
| Owner | `_______` |
| Date (UTC) | `_______` |
| Operator | `_______` |
| Repository baseline commit | `_______` |
| Baseline tag | `_______` |
| Governing contract | `_______` |
| Gate H checklist reference | `_______` |
| Execution receipt identifiers (all M3.3 commands) | `_______` |
| Network state throughout | **OFF**, verified at `_______` |

## 2. Source-observation set

| Field | Value |
|---|---:|
| Total source observations consumed | `____` |
| Distinct sources | `____` |
| Required closed quarterly instances satisfied | `____` |
| Provisional instances included | `____` |
| Observations superseded | `____` |
| Observations quarantined and excluded | `____` |

| `source_id` | Observations | Parser version | Parser status | Schema fingerprint |
|---|---:|---|---|---|
| `_______` | `____` | `_______` | `_______` | `_______` |

## 3. Provenance

| # | Item | Result |
|---|---|---|
| 3.1 | Every observation carries source ID, source URL identity or approved source key, source-observation ID, and retrieval-attempt ID | `PASS`/`FAIL` |
| 3.2 | Every observation carries `retrieved_at` UTC and HTTP validator metadata | `PASS`/`FAIL` |
| 3.3 | Every observation carries transport hash, decoded-content hash, and stored-object hash | `PASS`/`FAIL` |
| 3.4 | Every observation carries a **relative** storage path | `PASS`/`FAIL` |
| 3.5 | Every observation carries parser version, parser status, and schema fingerprint | `PASS`/`FAIL` |
| 3.6 | Supersession lineage is complete and non-cyclic | `PASS`/`FAIL` |
| 3.7 | Accession, CIK, form type, filing date, acceptance timestamp, fiscal period end, and source offsets carried through every derived row | `PASS`/`FAIL` |

## 4. Snapshot identity

| Field | Value |
|---|---|
| **`snapshot_id`** | `_______` |
| As-of date | `_______` |
| Coverage window | `_______` |
| `include_open_quarter` | `_______` |
| Snapshot frozen at (UTC, operational) | `_______` |
| Snapshot reason code recorded | `PILOT_CANDIDATE_SNAPSHOT_FROZEN` |
| **Freeze reproduced from identical inputs?** | `YES` / `NO` — second freeze `snapshot_id`: `_______` |

### Decision 019 §9 snapshot-freeze validation obligations

| # | Obligation | Result | Evidence |
|---|---|---|---|
| 4.1 | Amendment-linkage evidence conversion | `PASS`/`FAIL` | `_______` |
| 4.2 | Multi-registrant evidence aggregation | `PASS`/`FAIL` | `_______` |
| 4.3 | Explicit pre-study support provenance | `PASS`/`FAIL` | `_______` |
| 4.4 | Former-name identity-evidence conversion | `PASS`/`FAIL` | `_______` |
| 4.5 | Every further §9 obligation, enumerated and checked | `PASS`/`FAIL` | `_______` |
| 4.6 | Plain-to-dashed accession consistency verified, failing closed on disagreement | `PASS`/`FAIL` | `_______` |
| 4.7 | The frozen snapshot rejects mutation | `PASS`/`FAIL` | `_______` |

## 5. Candidate-table identities

| Table | Row count | Declared component digest |
|---|---:|---|
| `pilot_candidate_snapshots` | `____` | `_______` |
| `pilot_candidate_entities` | `____` | `_______` |
| `pilot_candidate_accessions` | `____` | `_______` |
| `pilot_candidate_accession_registrants` | `____` | `_______` |
| `pilot_candidate_entity_evidence` | `____` | `_______` |
| `pilot_candidate_accession_evidence` | `____` | `_______` |
| `pilot_candidate_entity_reasons` | `____` | `_______` |
| `pilot_candidate_accession_reasons` | `____` | `_______` |
| **`candidate_tables_sha256`** | — | `_______` |

**Limitation D021-L2 applies:** `candidate_tables_sha256` binds the snapshot's **declared**
component digests. Record here how declaration/row agreement was checked: `_______`

## 6. Policy versions

| Version | Value |
|---|---|
| Source registry | `_______` |
| Quota policy | `_______` |
| Joint selector policy | `_______` |
| Replacement signature policy | `_______` |
| Manifest hash policy | `_______` |
| Selection input schema | `_______` |
| Parser versions | `_______` |
| Migration chain head | `_______` |

### The six Decision 021 §8.4 explicit arguments

**Limitation D021-L7 applies: these are asserted, not verified.** Record the exact derivation of
each, so a reviewer can check the assertion.

| Argument | Value | **How it was derived** |
|---|---|---|
| `dependency_lock_sha256` | `_______` | `_______` |
| `code_commit_identifier` | `_______` | `_______` |
| `runtime_python_version` | `_______` | `_______` |
| `configuration_sha256` | `_______` | `_______` |
| `decision_authority_sha256` | `_______` | `_______` |
| `source_plan_sha256` | `_______` | `_______` |

## 7. Cohort definitions

| Cohort | Window | Assigned by |
|---|---|---|
| Development | `_______` | official SEC filing date (Decision 010) |
| Transition evaluation | `_______` | official SEC filing date |
| Final primary test | `_______` | official SEC filing date |
| Prospective secondary test | `_______` | official SEC filing date |
| Current monitoring | `_______` | official SEC filing date |
| Bootstrap seed | `_______` | frozen |
| Maturity gates | `_______` | frozen |
| Acceptance-date cohort | audit-only, never determines membership | Decision 010 |

## 8. Leakage attestation

**Limitation D021-L9 applies: the literal records a claim; the read set proves it.**

| # | Attestation | Result |
|---|---|---|
| 8.1 | No outcome value was read, derived, or stored | `PASS`/`FAIL` |
| 8.2 | No filing text was retrieved, parsed, or featurized | `PASS`/`FAIL` |
| 8.3 | No CompanyFacts and no Frames API access | `PASS`/`FAIL` |
| 8.4 | No external corpus influenced any value | `PASS`/`FAIL` |
| 8.5 | No S4 draft input was used | `PASS`/`FAIL` |
| 8.6 | No pilot membership or stratification informed anything | `PASS`/`FAIL` |
| 8.7 | Cohort assignment used the official filing date only | `PASS`/`FAIL` |
| 8.8 | No operational timestamp entered any substantive identity | `PASS`/`FAIL` |

**Exact read set that makes the attestation true:** `_______`

## 9. Selection result

| Field | Value |
|---|---|
| **`selection_run_id`** | `_______` |
| **`selection_input_sha256`** | `_______` |
| `run_state` | `_______` (must be `feasible`) |
| Selected entities | `____` (operating `____`, boundary controls `____`) |
| Selected accessions | `____` |
| Objective order | unchanged from Decision 013 §5 — `PASS`/`FAIL` |
| `selected_order` deterministic | `PASS`/`FAIL` |
| Node-limit exhausted | `____` |

### Roles and caps

| Role | Count | Cap | Within cap |
|---|---:|---:|---|
| control | `____` | `____` | `PASS`/`FAIL` |
| support | `____` | `____` | `PASS`/`FAIL` |
| base | `____` | `____` | `PASS`/`FAIL` |
| stress | `____` | `____` | `PASS`/`FAIL` |

### Quota report

| Quota | Required | Achieved | Members | Evidence level | Provisional | Result | Reason if not passed |
|---|---:|---:|---:|---|---:|---|---|
| `_______` | `____` | `____` | `____` | `_______` | `____` | `pass`/`fail`/`unproven` | `_______` |

**The difficult-or-nonstandard-package quota is deferred to M2.5 and is never reported as satisfied**
(limitation **D026-L2**): recorded as `_______`.

## 10. Reserves and dispositions

| Field | Value |
|---|---:|
| Selected targets | `____` |
| Targets with exactly one rank-1 reserve package | `____` |
| Targets with exactly one `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition | `____` |
| Targets with both | `____` (**must be 0**) |
| Targets with neither | `____` (**must be 0**) |
| Total reserve packages | `____` |
| Reserve child rows | `____` |
| **`reserves_sha256`** | `_______` |

| # | Item | Result |
|---|---|---|
| 10.1 | Item 70 total per-target coverage holds | `PASS`/`FAIL` |
| 10.2 | Item-46 applicability per Decision 022 — rank rendered once per persisted package, structurally not applicable for a disposition-only target | `PASS`/`FAIL` |
| 10.3 | **No synthetic package, `reserve_rank = 0`, `null`, `"N/A"`, placeholder, or invented rank** | `PASS`/`FAIL` |
| 10.4 | Contribution-set equality exact for every package | `PASS`/`FAIL` |
| 10.5 | A reserve was **constructed, never applied** | `PASS`/`FAIL` |

## 11. Reconstruction

| # | Item | Result | Evidence |
|---|---|---|---|
| 11.1 | Reconstruction through the accepted entry point succeeded | `PASS`/`FAIL` | `_______` |
| 11.2 | Every reconstructed field equals its persisted value | `PASS`/`FAIL` | `_______` |
| 11.3 | Both public entry points fail closed on the same stored identity corruption | `PASS`/`FAIL` | `_______` |
| 11.4 | **Every digest recomputed from persisted rows**, not from memory | `PASS`/`FAIL` | `_______` |

## 12. Replay

| # | Item | Result |
|---|---|---|
| 12.1 | Replay is **write-free** — no `INSERT`, `UPDATE`, `DELETE`, or `INSERT OR REPLACE` | `PASS`/`FAIL` |
| 12.2 | Replay returns identical identities | `PASS`/`FAIL` |
| 12.3 | An identical re-seal is idempotent; a differing seal is refused | `PASS`/`FAIL` |
| 12.4 | **Two clean rebuilds from the same snapshot produce identical** entity selections, accession selections, reserve ordering, quota results, and root | `PASS`/`FAIL` |

**Second rebuild root:** `_______` — **must equal §13's root exactly.**

**Unchanged governed state plus byte-identical canonical serialization produces the same root.** An
independently re-derived identical root is **not** a new root and does **not** require re-approval;
only a **differing** root does.

## 13. Manifest identities

| Digest | Value |
|---|---|
| **`selection_result_sha256`** | `_______` |
| `source_content_sha256` | `_______` |
| `candidate_tables_sha256` | `_______` |
| `quota_definition_sha256` | `_______` |
| `selector_policy_sha256` | `_______` |
| `entities_sha256` | `_______` |
| `accessions_sha256` | `_______` |
| `quota_report_sha256` | `_______` |
| `reserves_sha256` | `_______` |
| **`root_manifest_sha256`** | `_______` |
| **`manifest_id`** | `_______` |
| `manifest_schema_version` | `_______` |
| `ordinal_version` | `_______` |
| `supersedes_manifest_id` | `_______` |
| `manifest_state` | `proposed` |
| `approved_root_sha256` | **unwritten** |
| Canonical document, relative path | `_______` |
| Document byte length | `____` |

### Document contract

| # | Item | Result |
|---|---|---|
| 13.1 | All thirteen mandatory blocks present | `PASS`/`FAIL` |
| 13.2 | All **81** atomic milestone-plan §10 items bound and asserted item by item | `PASS`/`FAIL` |
| 13.3 | Totals: **42 direct / 30 transitive / 8 operationally excluded / 1 deferred to S9 — delivered here / 0 deferred to S10 / 0 unclassified** | `PASS`/`FAIL` |
| 13.4 | **Item 80, "command invocation", rendered with no personal path and no SEC identity** | `PASS`/`FAIL` |
| 13.5 | No substantive serialized field is unbound by the root | `PASS`/`FAIL` |
| 13.6 | Canonical JSON, content-derived filename | `PASS`/`FAIL` |
| 13.7 | Re-serialization is **byte-identical** | `PASS`/`FAIL` |
| 13.8 | Public verification passes and fails closed on wrong bytes | `PASS`/`FAIL` |
| 13.9 | Exactly one `proposed` manifest row, written atomically with its document | `PASS`/`FAIL` |
| 13.10 | **No empty sole-carrier crosswalk family was reached** (**D023-O1**) | `PASS`/`FAIL` — if `FAIL`, **stop and refer** |

## 14. CLI output deferred from S6

| # | Item | Result |
|---|---|---|
| 14.1 | The CLI output Decision 021 §16 deferred was delivered | `PASS`/`FAIL` |
| 14.2 | Its output contains **no personal path** | `PASS`/`FAIL` |
| 14.3 | Its output contains **no SEC identity** | `PASS`/`FAIL` |
| 14.4 | Its output contains no filing text and no outcome value | `PASS`/`FAIL` |

## 15. Limitations

| ID | Status at M3.3 | Note |
|---|---|---|
| `_______` | `ACTIVE` / `ACTIVE — OWNER RULING PENDING` | `_______` |

| # | Item | Result |
|---|---|---|
| 15.1 | The limitations register was read before the phase began | `PASS`/`FAIL` |
| 15.2 | Every new limitation discovered is recorded with the complete field set | `PASS`/`FAIL` |
| 15.3 | **No inherited limitation was closed** | `PASS`/`FAIL` |
| 15.4 | **D023-O1** was not reached, or was reached and **referred** | `PASS`/`FAIL` |

## 16. No-approval statement

**Mandatory. This section is never removed, softened, or marked `N/A`.**

> **Nothing in this packet is an approval.**
>
> The manifest is in state `proposed`. `approved_root_sha256` is unwritten. The exact
> `root_manifest_sha256` recorded in §13 is an **output of construction**, not an approved value, and
> its appearance here confers no approval, no release candidacy, and no publication eligibility.
>
> **Approval is a separate act**, taken by the owner in M3.4, recorded in
> [`root_hash_approval_packet.md`](root_hash_approval_packet.md), and specific to one exact hash. It
> is not implied by this packet, by verification passing, by replay succeeding, by a green suite, by
> a created tag, or by the code having run.
>
> **Nothing has been published, and Milestone 3 creates no publication authority.**

## 17. Sign-off

| Field | Value |
|---|---|
| Prepared by | `_______` |
| Date (UTC) | `_______` |
| Owner acknowledgement of receipt (**not approval**) | `_______` |
| Packet result | `COMPLETE` / `INCOMPLETE` |
| Completion token recorded | `M3_3_REAL_PILOT_MANIFEST_CONSTRUCTED_READY_FOR_ROOT_APPROVAL` / not recorded |
| Signature or recorded acceptance reference | `_______` |
