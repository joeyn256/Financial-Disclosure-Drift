# Decision 050 — M3.2 T5 Initial Live Invocation Authorization

**Date:** 2026-08-07
**Status:** ACCEPTED — OWNER AUTHORIZATION RECORDED
**Authority classification:** `T5_INITIAL_LIVE_INVOCATION_AUTHORIZED_FOR_SEPARATE_EXECUTION_PACKET`
**Type:** Bounded governance record accepting Decision 049 and the completed T4 operational preflight,
and authorizing **exactly one initial M3.2A live acquisition invocation** — to be performed later,
under a **separate owner execution packet**. **Not** a preregistration deviation. It changes no
hypothesis, cohort window, maturity gate, outcome definition, threshold, seed, selection methodology,
S4/S5/S6 identity, hash preimage, migration byte, implementation byte, test byte, receipt byte, reason
code, or configuration byte — **no executable byte changes with this record**.
**Amends:** nothing in place. No accepted decision is edited; Decisions 001–049 are byte-unchanged.
The accepted M3.2 contract, `Docs/m3/templates/evidence_index.md`, the limitations register, and every
durable review artifact are byte-unchanged by this record. Stage progress is recorded here, in the
registry, and in the ledger — never in the contract.
**Related:**
[Decision 049](decision_049_m3_2_t4_operational_preflight_acceptance.md) (the accepted T4 state this
record builds on, and whose evidence binding it carries forward);
[Decision 047](decision_047_m3_2_t4_operational_preflight_authorization.md) (whose ruling **047-A**
fixes that the operational catalog is first created inside the first lawfully authorized M3.2A live
invocation — preserved unchanged here);
[Decision 048](decision_048_m3_2_pre_t4_rawstore_acceptance_and_publication.md) (pre-T4 RawStore
acceptance, M3-L13 closure, F4 completion — unchanged);
[Decision 046](decision_046_m3_2_t3_acceptance_and_publication.md) (T3 acceptance, unchanged);
the accepted contract [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's acceptance of Decision 049 and T4 (§3), the evidence binding (§4), the frozen
M3.2A live scope (§5), the exact authority granted (§6), the authority expressly withheld (§7), the
interruption and no-resume rule (§8), the pre-live conditions the later execution packet must
reverify (§9), the network authority model (§10), the real-operational-catalog boundary (§11), and the
edit envelope and publication (§12).

---

## 1. What this record does, and what it does not

Five determinations, which must not be collapsed:

1. **T4 acceptance carried forward.** The owner accepts Decision 049 and the completed T4 operational
   preflight — `M3_2_T4_OPERATIONAL_PREFLIGHT_ACCEPTED`.
2. **One invocation authorized.** Exactly **`ONE_INITIAL_M3_2A_LIVE_INVOCATION`** is authorized, and
   nothing more.
3. **Execution is deferred.** **This record does not execute the live invocation.** The live execution
   remains deferred until the ChatGPT owner issues the separate T5 execution packet. The recorder of
   this decision **must not** execute it.
4. **No resume.** No resume, retry, recovery, second, or replacement invocation is authorized.
5. **What this record is not.** It is **not** M3.2B authority, **not** T6 authority, **not** Gate H
   authority, and **not** itself network enablement. Both tracked network switches remain `false` and
   CompanyFacts remains `false` at this record.

## 2. The owner determination, recorded without alteration

The owner's determination for this stage was issued as the Decision 050 authorization packet itself.
It carries **no separately named `OWNER_DECISION_050_…` instrument token**, and none is invented here
— the same convention Decisions 046 through 049 record for their own determinations. Where this record
summarizes for navigation, the owner's own terms control.

## 3. Ruling 050-A — acceptance of Decision 049 and T4

The owner accepts Decision 049 and the completed T4 operational preflight.

```text
M3_2_T4_OPERATIONAL_PREFLIGHT_ACCEPTED
T4: COMPLETE_AND_ACCEPTED
```

| Field | Value |
|---|---|
| Decision 049 commit | `82fe3881815cdf02435b9d0a07c13e11edb212ac` |
| Decision 049 subject | `Accept M3.2 T4 operational preflight` |
| Decision 049 parent (published T4 baseline) | `b7d83d389a92685bac776759b2af9762dc5301eb` |

## 4. Ruling 050-B — the bound T4 evidence

| Artifact | Relative private path | SHA-256 | Mode |
|---|---|---|---|
| T4 attestation | `runs/m3_2_t4_preflight/t4_preflight_attestation.md` | `8483a549cf894f1d186750ec13c24b41e5279134e782ca6e28ff4514e75d10c8` | `600` |
| Backup manifest | `backups/m3_2_t4_pre_window/manifest.sha256` | `0bb2b1d96bcefe7885d538fa054c93e4887a8a5233529538f9de39f059b84c8d` | `600`, **17** covered files |

Both hashes were **recomputed and matched exactly** at this record. The private evidence remains
**outside Git**; neither artifact is copied into the repository, and neither was rewritten by this
recording — they were read and re-hashed only.

**Accepted T4 resource state, carried forward unchanged:**

* **`FREE_DISK_50_GIB_GATE: PASS`** on the accepted measurement **74,481,328,128 bytes / 69.3661 GiB**;
* the **50.00 GiB** entry floor is **unchanged**;
* physical RAM **8.00 GiB** is an **observation only** — no object-size RAM floor is imposed;
* qualifying **off-device, device-distinct** backup **PASS**;
* backup destination hash verification **17/17 PASS**;
* scratch restore **17/17 PASS**;
* **`.env` excluded**;
* the attestation **copied separately** and **SHA-verified**;
* the external USB was **stable throughout the successful T4 execution**;
* the **prior unstable attempt is retained only as historical context** — it is not erased or
  rewritten, and it does not invalidate the successful run.

**Corrected policy count, carried forward frozen:** `reference_policy_versions = 25` — **21** distinct
policy keys from accepted migrations `0002`–`0011` plus **4** from `seed_reference_data()`, with zero
overlap. No code, migration, seed data, or governance record may be changed to obtain another value.

## 5. Ruling 050-C — the frozen M3.2A live scope

The future T5 invocation is frozen to exactly this scope:

| Field | Frozen value |
|---|---|
| **Window** | **M3.2A** |
| **Plan SHA-256** | **`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`** |
| **Planned unique logical requests** | **75** |
| **Quarterly index instances** | **70** |
| **Hard physical-attempt ceiling** | **801** |
| **Consumed before initial T5** | **0** |
| **Request method** | **GET** |
| **Request spacing floor** | **200.0 seconds** |

**No contingency requests. No ceiling increase. No substitution of another request plan. No alternate
plan hash. No stale-plan fallback.**

**Approved M3.2A source scope remains the accepted seven bootstrap route families only:**

`sec_bulk_submissions`, `sec_company_tickers`, `sec_company_tickers_exchange`,
`sec_edgar_calendar_announcement`, `sec_edgar_filing_calendar`, `sec_full_index_company`,
`sec_sic_code_list`.

**Prohibited route families:** `sec_submissions_entity`, `sec_submissions_historical`.

**Approved hosts remain limited to the accepted SEC hosts represented by the plan:**

* `www.sec.gov`
* `data.sec.gov`

The **zero-request compound calendar/announcement host representation remains accepted as
nonblocking** — it is a display artifact of a route family that places no requests in this window, and
no new evidence changes its meaning.

**CompanyFacts and Frames remain prohibited and unreachable. Filing-body and accession-content
acquisition remain prohibited in every window. M3.2B remains prohibited.**

## 6. Ruling 050-D — the exact authority granted

Decision 050 authorizes the owner to issue a **later execution packet** permitting exactly:

```text
ONE_INITIAL_M3_2A_LIVE_INVOCATION
```

That future execution — **and only that execution, under that later packet** — may:

1. re-establish the accepted baseline;
2. revalidate the T4-critical conditions immediately before live entry;
3. create a **private window-local configuration**;
4. set **within that window-local configuration only**:
   `network.enabled: true` and `network.m3_acquire_enabled: true`;
5. leave tracked `configs/project.yaml` at **false / false**;
6. load the accepted SEC contact identity **without displaying or retaining its value**;
7. execute exactly one accepted
   `python -m disclosure_drift m3 acquire … --window M3.2A --live …`;
8. **create the real governed M3.2A operational catalog** as part of the lawful live invocation;
9. create the initial M3.2A run;
10. perform **only** requests described by the frozen M3.2A plan;
11. enforce the **801** total physical-attempt ceiling;
12. enforce the **200.0-second** spacing floor;
13. write the immutable execution receipt and evidence required by the accepted implementation;
14. **disable and withdraw live network authorization immediately after termination**;
15. verify the safe **false / false** network state after the invocation.

**The live execution itself remains deferred until the ChatGPT owner issues the separate T5 execution
packet.** Nothing in this list may be performed under the authority of this record alone.

## 7. Ruling 050-E — the authority expressly withheld

This record does **NOT** authorize:

* executing the live invocation during Decision 050 recording;
* more than one initial invocation;
* automatic retry;
* automatic resume;
* `--resume-from`;
* recovery execution;
* a second run;
* a replacement run;
* **M3.2B**;
* dependent-plan derivation;
* reconciliation;
* **Gate H**;
* **T6**;
* CompanyFacts;
* Frames;
* filing-body retrieval;
* accession-content retrieval;
* plan changes;
* ceiling changes;
* spacing-floor reductions;
* adding request routes;
* expanding allowed hosts;
* changing the accepted contract;
* changing the accepted implementation;
* changing migrations;
* changing the receipt schema.

## 8. Ruling 050-F — interruption, termination, and the no-resume rule

**The authorization is for one initial invocation only.**

If that invocation ends in an **interrupted, failed, ceiling-stop, gate-stop, uncertain, or otherwise
non-successfully-completed** state:

```text
DO NOT RESUME AUTOMATICALLY.
```

Before any subsequent invocation, all of the following are required:

1. **network must be disabled**;
2. perform a **read-only** recovery inspection;
3. **classify** the recovery state;
4. continuation may proceed **only if** the classification is **SAFE**;
5. **UNSAFE** ⇒ **no continuation**;
6. **UNDETERMINED** ⇒ **STOP**;
7. the **predecessor receipt must be identified**;
8. the **consumed attempt count must be carried forward**;
9. the **same ceiling 801 remains binding**;
10. a **new run ID must be used** if continuation is later authorized;
11. the **ChatGPT owner must issue a separate explicit resume or new-run ruling**.

**No wording anywhere in this record may be interpreted as pre-authorizing that later continuation.**

## 9. Ruling 050-G — pre-live conditions for the future execution packet

The later T5 execution packet must **reverify, immediately before live entry**:

* Decision 050 is published and current;
* the repository is clean and synchronized;
* **no tag is required**;
* the accepted T4 attestation hash still matches;
* the plan hash still exactly matches;
* the window is **M3.2A**;
* logical requests **75**;
* quarterly indexes **70**;
* ceiling **801**;
* consumed count **0**;
* the real operational catalog **remains absent** before the first lawful invocation;
* **no prior M3.2 live run** exists;
* **no prior live receipt** exists;
* **no prior raw or live object** exists;
* sufficient operational disk remains available against the accepted **50 GiB** entry floor;
* the accepted private backup **remains recoverable**;
* the SEC identity is **locally valid and undisclosed**;
* tracked network configuration remains **false / false**;
* CompanyFacts remains **false**;
* the operator understands the stop and recovery rules.

**If any pre-live condition materially fails: NO LIVE ENTRY.**

## 10. Ruling 050-H — the network authority model

Two states must not be confused.

**Tracked / default state — unchanged by this record:**

```yaml
network:
  enabled: false
  m3_acquire_enabled: false
```

**Future window-local T5 state:** may be created **only** by the later execution packet, and **only**
for the authorized M3.2A invocation. It must set both values `true`, and it is withdrawn immediately
after termination.

**The live gate remains a conjunction.** Every one of the following is required, and no subset
suffices:

* explicit owner **T5 execution authority**;
* explicit **`--live`**;
* accepted window **M3.2A**;
* the accepted plan;
* the accepted **plan hash**;
* the accepted **ceiling 801**;
* a valid **SEC identity**;
* the accepted **contract**;
* the accepted **implementation**;
* accepted **T4**;
* **Decision 050**;
* all **implementation-level live gates**.

**Decision 050 itself leaves the network `false` / `false`.**

## 11. Ruling 050-I — the real operational catalog boundary

Decision 047's ruling is preserved unchanged:

```text
T4_DOES_NOT_CREATE_THE_OPERATIONAL_CATALOG
```

and this record establishes:

The real governed catalog **`catalogs/m3_2a_operational.sqlite3`** may first be created **only during
the separately authorized lawful T5 live invocation**.

**The Decision 050 recording must not create it.** Before that invocation, its **absence is
required** — and it is verified absent at this record.

## 12. Ruling 050-J — the edit envelope and publication

Exactly **three** repository paths are authorized for this record, **with no fourth**:

1. `Docs/Decisions/decision_050_m3_2_t5_initial_live_invocation_authorization.md` — this record;
2. `Docs/Decisions/decision_registry.md`;
3. `Milestones/STATUS.md`.

No executable code, test, migration, tracked configuration, evidence vocabulary or index, or
limitations-register edit is authorized. Had a fourth path appeared objectively necessary, the session
was required to stop and report before editing it.

One governance commit with subject `Authorize M3.2 T5 initial live invocation`, followed by **one
normal fast-forward push** to `origin/main`. No force, no force-with-lease, no rebase, no squash, no
amend after publication, no cherry-pick or replacement history. **NO TAG** — **M3.2 remains
incomplete**.

## 13. Recorded authorization status

```text
T5_INITIAL_LIVE_INVOCATION:      AUTHORIZED_FOR_SEPARATE_EXECUTION_PACKET
T5_EXECUTION:                    NOT_PERFORMED_BY_THIS_RECORD
AUTHORIZED_INVOCATION_COUNT:     1
RESUME_AUTHORITY:                NONE
RETRY_AUTHORITY:                 NONE
RECOVERY_AUTHORITY:              NONE
WINDOW:                          M3.2A
PLAN_SHA256:                     19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68
LOGICAL_REQUESTS:                75
QUARTERLY_INDEXES:               70
CEILING:                         801
CONSUMED_BEFORE_INITIAL_T5:      0
METHOD:                          GET
SPACING_FLOOR_SECONDS:           200.0
M3_2B:                           NOT_AUTHORIZED
T6:                              NOT_AUTHORIZED
GATE_H:                          NOT_AUTHORIZED
NETWORK_TRACKED:                 false / false
COMPANYFACTS:                    false
REAL_OPERATIONAL_CATALOG:        ABSENT
LIVE_M3_2_RUN:                   ABSENT
LIVE_RECEIPT:                    ABSENT
RAW_LIVE_SEC_OBJECT:             ABSENT
TAG:                             NONE
M3_2:                            NOT_COMPLETE
```

## 14. Formal outcome

```text
M3_2_T5_INITIAL_LIVE_INVOCATION_AUTHORIZATION_RECORDED_AND_PUBLISHED
```

**Next authorized action:** `CHATGPT_OWNER_M3_2_T5_INITIAL_LIVE_INVOCATION_EXECUTION_PACKET`
