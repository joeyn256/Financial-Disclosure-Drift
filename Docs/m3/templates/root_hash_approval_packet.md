# TEMPLATE — Exact Root-Hash Approval Packet

**This file is a blank template. No root has been approved, and `approved_root_sha256` has never been
written.**
Copy it, fill every field, and retain the completed copy as evidence. Do not edit this template in
place.

**Purpose:** to present one exact `root_manifest_sha256` for an explicit owner decision, with every
identity re-derived at the moment of approval, and to record that decision in a form that cannot be
widened, inferred, or transferred.
**Phase:** M3.4
**Controlling records:** [Decision 013](../../Decisions/decision_013_pilot_selection_mechanics.md)
**§8 — completion requires owner approval of the exact final manifest hash**;
[Decision 021](../../Decisions/decision_021_m23_s6_manifest_construction.md) §9 (the copy-not-hash
rule), §9.2 (six-field identity immutability), §11 (the proposed-only boundary);
[Decision 024](../../Decisions/decision_024_m2_m3_boundary_governance.md) §5.2 (the S10 row);
[Decision 027](../../Decisions/decision_027_m3_master_plan_and_operational_readiness.md);
migration `0009`'s `approved_root_sha256 = root_manifest_sha256` check and migration `0013`'s eight
lifecycle guards;
[`milestone_03_master_plan.md`](../../../Milestones/milestone_03_master_plan.md) phase M3.4.
**Completion token:** on approval,
`M3_4_EXACT_ROOT_OWNER_APPROVED_READY_FOR_INTEGRATED_ACCEPTANCE`.

---

## 0. Handling

- **Non-secret document.** Identities, digests, versions, counts, and evidence references.
- **Never record** the SEC identity, any credential, any absolute personal path, any raw response
  body, any filing text, or any outcome value.
- **Never circulate an approved root outside this packet** before publication is separately
  authorized.
- **Immutable once decided.** A later development is a new dated packet.

## 1. Identification

| Field | Value |
|---|---|
| Packet ID | `_______` |
| Phase | M3.4 |
| Owner | `_______` |
| Date prepared (UTC) | `_______` |
| Prepared by | `_______` |
| Repository baseline commit | `_______` |
| Baseline tag | `_______` |
| Governing contract, if any | `_______` |
| Network state throughout | **NONE**, verified at `_______` |

## 2. The exact root

| Field | Value |
|---|---|
| **`root_manifest_sha256`** | `_______` |
| **`manifest_id`** | `_______` |
| **`selection_result_sha256`** | `_______` |
| `manifest_schema_version` | `_______` |
| `ordinal_version` | `_______` |
| `supersedes_manifest_id` | `_______` |
| `manifest_state` at presentation | `proposed` |
| `approved_root_sha256` at presentation | **unwritten** |

## 3. Component digest table

| Component | Digest |
|---|---|
| `source_content_sha256` | `_______` |
| `candidate_tables_sha256` | `_______` |
| `quota_definition_sha256` | `_______` |
| `selector_policy_sha256` | `_______` |
| `entities_sha256` | `_______` |
| `accessions_sha256` | `_______` |
| `quota_report_sha256` | `_______` |
| `reserves_sha256` | `_______` |
| **Root over the above** | `_______` |

## 4. Snapshot identity

| Field | Value |
|---|---|
| `snapshot_id` | `_______` |
| As-of date | `_______` |
| Coverage window | `_______` |
| `include_open_quarter` | `_______` |
| `selection_run_id` | `_______` |
| `selection_input_sha256` | `_______` |
| `run_state` | `feasible` |

## 5. Policy versions

| Version | Value |
|---|---|
| Source registry | `_______` |
| Quota policy | `_______` |
| Joint selector policy | `_______` |
| Replacement signature policy | `_______` |
| Manifest hash policy | `_______` |
| Selection input schema | `_______` |
| Migration chain head | `_______` |
| `dependency_lock_sha256` | `_______` |
| `code_commit_identifier` | `_______` |
| `runtime_python_version` | `_______` |
| `configuration_sha256` | `_______` |
| `decision_authority_sha256` | `_______` |
| `source_plan_sha256` | `_______` |

## 6. Cohort definitions

| Field | Value |
|---|---|
| Cohort windows | `_______` |
| Maturity gates | `_______` |
| Bootstrap seed | `_______` |
| Cohort assignment date source | official SEC filing date (Decision 010); acceptance date audit-only |
| Any deviation | Deviation D001 only, per `Docs/preregistration.md` §25 |

## 7. Request-plan identity

| Field | Value |
|---|---|
| `request_plan_sha256` | `_______` |
| Approved planned unique logical requests | `____` |
| Approved hard request ceiling | `____` |
| Request-budget document reference | `_______` |

## 8. Acquisition evidence

| Field | Value |
|---|---:|
| Actual logical requests | `____` |
| Actual physical attempts | `____` |
| Raw objects stored | `____` |
| Duplicate bodies reconciled | `____` |
| Quarantined objects | `____` |
| Cooldowns | `____` |
| Blocking drift events | `____` (**must be 0**) |
| Prohibited-route attempts | `____` (**must be 0**) |
| Execution receipt identifiers | `_______` |

## 9. Gate results

| Gate | Result | Reference |
|---|---|---|
| **Gate F** | `PASS` / `FAIL` | `_______` |
| **Gate H** | `PASS` / `FAIL` | `_______` |
| M3.1A offline rehearsal | `PASS` / `FAIL` | `_______` |
| Independent M3.1 review | `PASS` / `FAIL` | `_______` |
| Independent M3.2 review | `PASS` / `FAIL` | `_______` |
| Independent M3.3 review | `PASS` / `FAIL` | `_______` |

## 10. Reconstruction, replay, and verification

| # | Item | Result | Reference |
|---|---|---|---|
| 10.1 | Reconstruction through the accepted entry point | `PASS`/`FAIL` | `_______` |
| 10.2 | Write-free idempotent replay | `PASS`/`FAIL` | `_______` |
| 10.3 | Public document verification | `PASS`/`FAIL` | `_______` |
| 10.4 | Byte-identical re-serialization | `PASS`/`FAIL` | `_______` |
| 10.5 | Two clean rebuilds producing an identical root | `PASS`/`FAIL` | `_______` |

## 11. Re-derivation **at the moment of approval**

**This section is completed immediately before the owner decides, not when the packet was prepared.**

| # | Item | Result | Value observed |
|---|---|---|---|
| 11.1 | Every component digest recomputes from persisted rows | `PASS`/`FAIL` | `_______` |
| 11.2 | **`root_manifest_sha256` recomputes and equals §2** | `PASS`/`FAIL` | `_______` |
| 11.3 | **`manifest_id` recomputes and equals §2** | `PASS`/`FAIL` | `_______` |
| 11.4 | `selection_result_sha256` equals §2 and is still sealed append-once | `PASS`/`FAIL` | `_______` |
| 11.5 | The document verifies against the persisted rows | `PASS`/`FAIL` | `_______` |
| 11.6 | No governed byte or governed row changed since the packet was prepared | `PASS`/`FAIL` | `_______` |
| 11.7 | The six manifest identity fields are unchanged | `PASS`/`FAIL` | `_______` |
| 11.8 | Catalog integrity and foreign-key checks pass | `PASS`/`FAIL` | `_______` |

| Field | Value |
|---|---|
| Re-derivation timestamp (UTC) | `_______` |
| Re-derivation performed by | `_______` |
| Execution receipt for the re-derivation | `_______` |

**If any item is `FAIL`, STOP.** Do not approve. Do not adjust this packet to match the derived value.
Do not regenerate to match this packet. Record the mismatch under §14 and refer it as an M3.3 finding.

## 12. Limitations

| ID | Status | Relevance to this approval |
|---|---|---|
| `_______` | `_______` | `_______` |

| # | Item | Result |
|---|---|---|
| 12.1 | The complete limitations register is attached or referenced | `PASS`/`FAIL` |
| 12.2 | **No inherited limitation has been closed** | `PASS`/`FAIL` |
| 12.3 | **D023-O1** status stated explicitly | `PASS`/`FAIL` |
| 12.4 | **D023-O2** — release root confirmed owner-controlled | `PASS`/`FAIL` |
| 12.5 | **D021-L7** — the six explicit arguments' derivations recorded | `PASS`/`FAIL` |
| 12.6 | **D026-L2** — the deferred quota is reported as deferred, never satisfied | `PASS`/`FAIL` |

## 13. Unresolved warnings

**Every unresolved warning is disclosed here. An undisclosed warning invalidates the approval.**

| # | Warning | Severity | Bearing on the root | Disclosed |
|---|---|---|---|---|
| 1 | `_______` | `_______` | `_______` | `YES` |

| Field | Value |
|---|---|
| Total unresolved warnings | `____` |
| Any warning bearing on the root's correctness? | `YES` / `NO` |

## 14. Mismatch record

Complete only if §11 produced a `FAIL`.

| Field | Value |
|---|---|
| Item that failed | `_______` |
| Expected value (from this packet) | `_______` |
| Observed value (re-derived) | `_______` |
| Action taken | **STOPPED — no approval given** |
| Referred as | `_______` |
| Date (UTC) | `_______` |

## 15. Publication status

| Field | Value |
|---|---|
| Publication authority | **`NOT_AUTHORIZED`** |
| Basis | Milestone 3 acceptance creates no publication authority; publication requires a separate accepted record |
| Decision 001 final literature refresh | **required, not discharged** (**D026-L1**) |
| Decision 006 prohibited-claims list | binding |
| Milestone 0 standing limitations | open (**D026-L3**) |
| Future outcome-analysis authority | **`NOT_AUTHORIZED`** |

## 16. The owner decision

**Read §17 before signing.**

| Field | Value |
|---|---|
| **Decision** | `APPROVED` / `REJECTED` |
| **Exact hash decided upon** | `_______` |
| Owner | `_______` |
| Date (UTC) | `_______` |
| Signature or recorded acceptance reference | `_______` |
| If rejected, reason | `_______` |
| Completion token recorded | `M3_4_EXACT_ROOT_OWNER_APPROVED_READY_FOR_INTEGRATED_ACCEPTANCE` / not recorded |

### Approval statement — copied verbatim when approving

> I approve **exactly** the value `root_manifest_sha256 = ` `_______`, and nothing else.
>
> I have read the component digest table, the snapshot identity, the policy versions, the cohort
> definitions, the request-plan identity, the acquisition evidence, both gate results, the
> reconstruction, replay, and verification results, the re-derivation performed at this moment, the
> limitations register, and every disclosed unresolved warning.
>
> **This approval applies to this exact hash only.** It does not apply to any regenerated,
> recomputed, corrected, or superseded root. It is not inferable from silence, from a passing gate,
> from a green suite, from a created tag, from an execution receipt, or from the code having run.
>
> **This approval authorizes no publication and no outcome analysis.**

## 17. Approval semantics — binding

| Rule | Statement |
|---|---|
| **Explicit** | Approval exists only as this recorded decision, signed |
| **Owner-recorded** | Only the owner approves. No model, session, or reviewer approves on the owner's behalf |
| **Exact-hash specific** | Approval attaches to the single byte value in §16, and to no other |
| **Non-transferable to a regenerated root** | Any regeneration produces a new `root_manifest_sha256` and requires a new packet and a new decision. **A prior approval never carries over** |
| **Non-inferable from silence** | Not deciding is not approving |
| **Non-inferable from running code** | Construction, verification, replay, and a passing gate are not approval |
| **Invalidated by any governed change** | Any change to a governed byte or a governed row after approval invalidates it for the changed artifact |

### Rejection handling

A rejection is recorded with its reason. The manifest stays `proposed`. The correction is made under
a new bounded authorization, and the result is a **new** exact root requiring its own packet.

### Regeneration handling

Any regeneration produces a new root. A prior approval never carries over, and the new root requires
its own packet and its own explicit decision.

### Reapproval requirements

Reapproval requires the full packet again: re-derivation at the moment of approval, re-verification,
a current limitations register, every unresolved warning disclosed, and a fresh explicit decision
naming the new exact hash.

### Approved-root persistence — inherited from the accepted schema

| Rule | Enforcement |
|---|---|
| `approved_root_sha256` may only be written **equal to** `root_manifest_sha256` | migration `0009` check |
| The six manifest identity fields are immutable after insertion | migration `0013` trigger 4 |
| A manifest row cannot be replaced by `INSERT OR REPLACE` | migration `0013` trigger 5 |
| A selection run cannot be replaced, deleted, or re-identified | migration `0013` triggers 6, 7, 8 |
| `selection_result_sha256` is append-once and remains recomputable from its persisted preimage | Decision 021 §15.5 |

### Evidence retention

Every packet — approved or rejected — is retained permanently and is **never edited after the
decision**. A correction is a new dated packet that names what it supersedes.

## 18. Publication prohibition

> **This approval confers no publication authority.**
>
> Publication requires a separate accepted record, and additionally requires the Decision 001 final
> literature refresh (**D026-L1**), compliance with the Decision 006 prohibited-claims list, and
> resolution of Milestone 0's standing limitations (**D026-L3**). Any outcome analysis requires its
> own separate authorization and is not created by Milestone 3 acceptance.
