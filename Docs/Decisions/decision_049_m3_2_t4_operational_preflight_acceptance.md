# Decision 049 — M3.2 T4 Operational Preflight Acceptance and Publication

**Date:** 2026-08-07
**Status:** ACCEPTED — OWNER APPROVED 2026-08-07
**Type:** Bounded governance record accepting the completed **M3.2 T4 Operational Preflight
Execution**, binding that acceptance to two named private-evidence artifacts by SHA-256, and freezing
the corrected `reference_policy_versions` operational expectation at **25**. **Not** a preregistration
deviation. It changes no hypothesis, cohort window, maturity gate, outcome definition, threshold,
seed, selection methodology, S4/S5/S6 identity, hash preimage, migration byte, implementation byte,
test byte, receipt byte, reason code, or configuration byte — **no executable byte changes with this
record**.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–048 are byte-unchanged.
The accepted M3.2 contract, `Docs/m3/templates/evidence_index.md`, the limitations register, and every
durable review artifact are all byte-unchanged by this record. Stage progress is recorded here, in
the registry, and in the ledger — never in the contract.
**Related:**
[Decision 047](decision_047_m3_2_t4_operational_preflight_authorization.md) (the governing T4
authorization whose execution this record accepts, and whose ruling **047-A** keeps the operational
catalog uncreated until a later T5 instrument);
[Decision 048](decision_048_m3_2_pre_t4_rawstore_acceptance_and_publication.md) (pre-T4 RawStore
acceptance, M3-L13 closure, F4 completion — all unchanged);
[Decision 046](decision_046_m3_2_t3_acceptance_and_publication.md) (T3 acceptance, unchanged);
Decision 023 §7 **O1**; the accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's acceptance of the completed T4 operational preflight (§3), the private
evidence that acceptance is bound to (§4), the accepted T4 facts (§§5–10), the frozen
`reference_policy_versions = 25` expectation (§7), the accepted finding counts (§11), the governance
result (§12), the authorized repository edit envelope and publication (§13), and the negative
authority that survives all of it (§14).

---

## 1. What this record accepts, and what it does not

Six determinations, which must not be collapsed:

1. **T4 execution acceptance.** The completed M3.2 T4 Operational Preflight Execution
   (`M3_2_T4_OPERATIONAL_PREFLIGHT_EXECUTION_COMPLETE_READY_FOR_OWNER_ACCEPTANCE`) is **accepted**.
2. **Evidence binding.** The acceptance is bound to exactly two private artifacts, each named by
   relative path and SHA-256 in §4. The evidence itself stays outside Git.
3. **Corrected expectation.** `reference_policy_versions = 25` is frozen as the correct T4
   operational expectation, superseding the stale packet value of 6.
4. **No independent rereview.** None was required for this recording, and none is implied.
5. **T4 is closed.** T4 is `COMPLETE_AND_ACCEPTED`. Decision 047's T4 authorization is exhausted.
6. **What this record is not.** It is **not** T5, T6, or Gate H authority, **not** network authority,
   and **not** live-operation authority. Nothing here permits a live SEC operation, a real operational
   catalog, a real M3.2 run, a live receipt, a raw live object, or any use of the approved request
   ceiling **801**.

## 2. The owner determination, recorded without alteration

The owner's determination for this stage was issued as the Decision 049 recording packet itself. It
carries **no separately named `OWNER_DECISION_049_…` instrument token**, and none is invented here —
the same convention Decisions 046, 047, and 048 record for their own determinations. The sections
below reproduce the owner's rulings; where this record summarizes for navigation, the owner's own
terms control.

## 3. Ruling 049-A — the accepted T4 execution

The owner **accepts** the completed T4 Operational Preflight Execution at the published baseline
`b7d83d389a92685bac776759b2af9762dc5301eb`, tree `6f54cdbccfa77def555c27c61e6ad9dd178369a0`.

`M3_2_T4_OPERATIONAL_PREFLIGHT_ACCEPTED`

## 4. Ruling 049-B — the private evidence this acceptance is bound to

| Artifact | Relative private path | SHA-256 | Mode |
|---|---|---|---|
| T4 attestation | `runs/m3_2_t4_preflight/t4_preflight_attestation.md` | `8483a549cf894f1d186750ec13c24b41e5279134e782ca6e28ff4514e75d10c8` | `600` |
| Backup manifest | `backups/m3_2_t4_pre_window/manifest.sha256` | `0bb2b1d96bcefe7885d538fa054c93e4887a8a5233529538f9de39f059b84c8d` | `600` |

The backup manifest covers **17** files.

**The private evidence remains outside Git.** Neither artifact is copied into the repository. No
`operational_preflight_attestation` evidence type is added, and **no public evidence-index row is
added for the T4 attestation** — Decision 047 ruling **047-D** already settled that T4 preflight
evidence stays private, and this record does not disturb it.

## 5. Ruling 049-C — accepted repository and implementation facts

* Published baseline `b7d83d389a92685bac776759b2af9762dc5301eb`.
* **The repository remained byte-identical throughout T4.**
* No implementation, test, configuration, or migration change occurred.
* No commit, push, or tag occurred during T4 itself.

## 6. Ruling 049-D — accepted resource gate

| Field | Accepted value |
|---|---|
| Measured free storage | **74,481,328,128 bytes** |
| | **69.3661 GiB** |
| Required floor | **50.00 GiB** |
| Disposition | **`FREE_DISK_50_GIB_GATE: PASS`** |
| Measured physical RAM | **8,589,934,592 bytes** (**8.00 GiB**) |

**No invented object-size RAM floor is imposed.** The measured RAM is recorded as an observation, not
as a gate, and no later stage may read it as one.

## 7. Ruling 049-E — the frozen policy count

The T4 operational expectation is frozen as:

```text
reference_policy_versions = 25
```

**Accepted provenance:**

* **21** distinct policy keys seeded by accepted migrations `0002`–`0011`;
* **4** distinct keys seeded by `seed_reference_data()` — `universe`, `filing_inventory`,
  `raw_governance`, `temporal`;
* **zero** overlap between the two sets;
* total **25**.

This **resolves the stale earlier packet expectation of 6**, which was incorrect. It is **not** a
defect. **No code, migration, seed data, or governance record may be changed to obtain another
value.**

The complete accepted T4 reference-count expectation is:

| Reference table | Expected |
|---|---|
| `ops_schema_migrations` | 13 |
| `reference_form_types` | 8 |
| `reference_reason_codes` | 113 |
| `reference_cohort_definitions` | 5 |
| **`reference_policy_versions`** | **25** |
| `reference_sic_codes` | 0 |

## 8. Ruling 049-F — accepted external backup

The owner accepts that the successful T4 run established:

* a qualifying **local external USB** backup destination;
* **device-distinct PASS** — primary `st_dev` != backup `st_dev`;
* **writable PASS**;
* **stable throughout the complete successful T4 execution PASS**;
* **pre-existing USB contents unchanged**;
* a **non-overwriting new backup snapshot**;
* **destination hash verification 17/17 PASS**;
* **covered file-count equality PASS**;
* **scratch restore 17/17 PASS**, restored from the USB copy;
* the scratch restore **deleted, with deletion proven**;
* **`.env` excluded**, and no secret or identity source file covered;
* the final T4 attestation **copied separately** to the backup snapshot;
* the copied attestation SHA **exactly matched** its source.

**The earlier unsuccessful T4 attempt, in which the same USB disconnected, remains historical
operational context.** It **does not invalidate** the subsequent successful T4 run, because the device
was requalified and remained stable throughout the complete accepted execution. **The historical
failed attempt is not erased or rewritten.**

## 9. Ruling 049-G — accepted disposable catalog

The owner accepts:

* disposable, offline catalog preparation **PASS**;
* migrations **contiguous `0001`–`0013`**, head equal to the accepted `FINAL_MIGRATION_VERSION`;
* `PRAGMA quick_check` **PASS**;
* `PRAGMA integrity_check` **PASS**;
* foreign-key check **PASS**;
* **all six** reference counts **PASS**;
* **`reference_policy_versions = 25`**;
* **operational tables empty**;
* the disposable catalog and its root **removed**;
* **the real operational catalog remains ABSENT.**

## 10. Ruling 049-H — accepted operational and governance state

| Field | Accepted value |
|---|---|
| Approved plan SHA-256 | `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` |
| Planned unique logical requests | **75** |
| Quarterly full-index requests | **70** |
| Hard physical-attempt ceiling | **801** |
| Consumed | **0** |
| Approved scope | **GET-only** |
| Route / host / prohibition checks | **PASS** |
| SEC contact identity | locally validated, **value never retained** |
| **F4** | **COMPLETE** |
| **M3-L13** | **CLOSED — Decision 048** |
| Progress-sink obligation | **DISCHARGED** |
| **D023-O1** | **LATENT / NOT TRIGGERED / M3.3-scoped** |
| SEC contact | **`NO_SEC_CONTACT_OCCURRED`** |
| Real operational catalog | **ABSENT** |
| Live M3.2 run | **ABSENT** |
| Live receipt | **ABSENT** |
| Raw / live SEC object | **ABSENT** |

## 11. Ruling 049-I — accepted findings

| Class | Count |
|---|---|
| BLOCKER | **0** |
| MAJOR | **0** |
| MINOR | **0** |
| OPTIMIZATION | **0** |

The intermediate `backups/` permission issue was **corrected within authorized private-evidence
scope** from `0755` to `0700` and passed the final permissions gate. **It is not an open limitation**,
and it creates no limitations-register entry.

## 12. Ruling 049-J — the governance result

```text
M3_2_T4_OPERATIONAL_PREFLIGHT_ACCEPTED
T4:  COMPLETE_AND_ACCEPTED
T5:  NOT_AUTHORIZED
T6:  NOT_AUTHORIZED
```

**T4 enabled no network capability and consumed no request budget.** T4 acceptance is **not** combined
with T5 authorization, and no session may read it as such.

## 13. Ruling 049-K — the authorized edit envelope and publication

Exactly **three** repository paths are authorized for this record, **with no fourth**:

1. `Docs/Decisions/decision_049_m3_2_t4_operational_preflight_acceptance.md` — this record;
2. `Docs/Decisions/decision_registry.md`;
3. `Milestones/STATUS.md`.

No executable code, test, migration, tracked configuration, evidence vocabulary or index, or
limitations-register edit is authorized. Had a fourth path appeared necessary, the session was
required to stop and report before editing it.

One governance commit with subject `Accept M3.2 T4 operational preflight`, followed by **one normal
fast-forward push** to `origin/main`. No force, no force-with-lease, no rebase, no squash, no amend
after publication, no cherry-pick or replacement history. **NO TAG** — M3.2 is not complete.

## 14. Ruling 049-L — the negative authority that survives this record

This record does **not**:

* authorize **T5**, **T6**, or **Gate H**;
* enable the network — both tracked switches remain `false`;
* enable CompanyFacts — it remains `false`;
* authorize any SEC contact, DNS lookup, or live transport;
* authorize creation of the real operational catalog;
* authorize any live M3.2 run, live receipt, or raw live object;
* consume, reserve, or transfer any part of ceiling **801**, which remains **wholly unconsumed at 0**;
* confer resume authority, `--resume-from` authority, or receipt-chain continuation authority;
* change the migration chain, which remains `0001`–`0013` with no `0014`;
* change the receipt schema, which remains `m3-execution-receipt/2.0`;
* reopen any accepted decision, review artifact, contract, packet, or template.

Any future live operation requires its own separate, exact, owner-issued authorization. Neither this
record, nor Decision 047, nor Decision 048, nor any gate token or contract acceptance substitutes for
it.

## 15. Recorded acceptance status

```text
T4_OPERATIONAL_PREFLIGHT:        ACCEPTED_AND_PUBLISHED
T4:                              COMPLETE_AND_ACCEPTED
T4_FINDINGS:                     BLOCKER 0 · MAJOR 0 · MINOR 0 · OPTIMIZATION 0
FREE_DISK_50_GIB_GATE:           PASS
REFERENCE_POLICY_VERSIONS:       25
OFF_DEVICE_BACKUP:               VERIFIED (17/17 destination, 17/17 restore)
F4:                              COMPLETE
M3_L13:                          CLOSED_BY_DECISION_048
PROGRESS_SINK:                   DISCHARGED
D023_O1:                         LATENT_NOT_TRIGGERED_M3_3_SCOPED
T5:                              NOT_AUTHORIZED
T6:                              NOT_AUTHORIZED
NETWORK:                         DISABLED
COMPANYFACTS:                    DISABLED
M3_2A_CEILING_801:               UNUSED
REAL_OPERATIONAL_CATALOG:        ABSENT
LIVE_M3_2_RUN:                   ABSENT
LIVE_RECEIPT:                    ABSENT
RAW_LIVE_SEC_OBJECT:             ABSENT
```

## 16. Formal outcome

```text
M3_2_T4_OPERATIONAL_PREFLIGHT_ACCEPTED_AND_PUBLISHED
```

**Next authorized action:** `CHATGPT_OWNER_M3_2_T5_INITIAL_LIVE_INVOCATION_AUTHORIZATION_PACKET`
