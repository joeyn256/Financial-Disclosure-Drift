# TEMPLATE — Schema-Drift Incident Record

**This file is a blank template. No schema-drift incident has occurred.**
Copy it, fill every field, and retain the completed copy as evidence. Do not edit this template in
place.

**Purpose:** to record a fail-closed schema-drift stop completely enough that the owner can rule on
it without re-running anything — what was observed, what was expected, what stopped, what did not
progress, and what would close it.
**Phase:** M3.2 primarily; M3.3 where a stored payload no longer matches its expected shape.
**Controlling records:** [Decision 027](../../Decisions/decision_027_m3_master_plan_and_operational_readiness.md);
[Decision 009](../../Decisions/decision_009_raw_data_governance.md);
[Decision 012](../../Decisions/decision_012_accession_observation_resolution.md);
[`milestone_2_3_pilot_selection_plan.md`](../../../Milestones/milestone_2_3_pilot_selection_plan.md)
§12 (quarantine, rollback);
[`milestone_03_master_plan.md`](../../../Milestones/milestone_03_master_plan.md) phase M3.2 §19.

---

## 0. Handling

- **Non-secret document.** Field paths, types, counts, identities, and reason codes only.
- **Never record** the raw response body, an excerpt of it, the SEC identity, any credential, or any
  absolute personal path. Describe the **shape**, not the payload.
- **The incident stops the phase.** It is not a warning to be noted and passed.
- **Immutable once closed.** A later development is a new dated entry.

## 1. Incident identification

| Field | Value |
|---|---|
| Incident ID | `_______` |
| Phase | `_______` |
| Owner | `_______` |
| Date opened (UTC) | `_______` |
| Opened by (operator / session) | `_______` |
| Acquisition run identifier | `_______` |
| Execution receipt ID at the stop | `_______` |
| Repository baseline commit | `_______` |
| Governing contract | `_______` |

## 2. Observed schema

Describe the **shape** encountered. Field paths and types only.

| Field | Value |
|---|---|
| Source class | `_______` |
| Parser identifier | `_______` |
| Parser version | `_______` |
| Schema fingerprint observed | `_______` |
| Drift kind | `unknown_field_retained` / `required_field_missing` / `type_changed` / `unexpected_null` / `malformed_nested_array` / `new_historical_file_reference` |
| Field path(s) | `_______` |
| Observed type or structure | `_______` |
| Number of records exhibiting it | `____` |
| Number of records unaffected | `____` |

## 3. Expected schema

| Field | Value |
|---|---|
| Expected field path(s) | `_______` |
| Expected type or structure | `_______` |
| Expected schema fingerprint | `_______` |
| Where the expectation is declared | `_______` |
| When the expectation was last confirmed | `_______` |

## 4. Affected route

| Field | Value |
|---|---|
| `source_id` | `_______` |
| Host | `_______` |
| Path or path family | `_______` |
| Source mutability class | `living` / `dated_snapshot` / `immutable` |
| Retrieval method | `_______` |
| Expected content kind | `_______` |
| Is the route required for census completion? | `YES` / `NO` |

## 5. Affected raw-object identities

Identities only. **No bodies.**

| # | Object identity (`content_sha256`) | Source observation ID | Retrieval attempt ID | Relative stored path | Quarantined? |
|---|---|---|---|---|---|
| 1 | `_______` | `_______` | `_______` | `_______` | `YES`/`NO` |
| 2 | `_______` | `_______` | `_______` | `_______` | `YES`/`NO` |

## 6. Stop record

| Field | Value |
|---|---|
| **Stop timestamp (UTC)** | `_______` |
| Reason code recorded | `_______` |
| Was the stop automatic (fail-closed) or operator-initiated? | `_______` |
| Physical attempts placed before the stop | `____` |
| Approved ceiling in force | `____` |
| Remaining planned logical requests, unattempted | `____` |

## 7. No-progress confirmation

Confirm, item by item, that **nothing advanced past the stop**.

| # | Item | Result |
|---|---|---|
| 7.1 | **No parsed record was admitted from the drifted payload** | `CONFIRMED` / `NOT CONFIRMED` |
| 7.2 | **No default was supplied for a missing field** | `CONFIRMED` / `NOT CONFIRMED` |
| 7.3 | **No type was coerced** | `CONFIRMED` / `NOT CONFIRMED` |
| 7.4 | **No row was dropped** to make the parse succeed | `CONFIRMED` / `NOT CONFIRMED` |
| 7.5 | **No threshold or expectation was relaxed** | `CONFIRMED` / `NOT CONFIRMED` |
| 7.6 | The uncommitted transaction rolled back | `CONFIRMED` / `NOT CONFIRMED` |
| 7.7 | **The raw object was preserved, not deleted** | `CONFIRMED` / `NOT CONFIRMED` |
| 7.8 | No further request was issued after the stop | `CONFIRMED` / `NOT CONFIRMED` |
| 7.9 | No snapshot, selection, or manifest was produced | `CONFIRMED` / `NOT CONFIRMED` |
| 7.10 | The terminating execution receipt was written | `CONFIRMED` / `NOT CONFIRMED` |

**Any `NOT CONFIRMED` is itself a finding and is escalated before anything else proceeds.**

## 8. Analysis

| Question | Answer |
|---|---|
| What most likely changed at the source? | `_______` |
| Is the change plausibly an official SEC correction or format update? | `_______` |
| Is the change consistent across records, or isolated? | `_______` |
| Does it affect a field the selection or a governed identity consumes? | `_______` |
| Would ignoring it change any candidate attribute, quota, or identity? | `_______` |
| Does the accepted parser have a defensible reading of the new shape? | `_______` |
| Does any accepted decision already govern this field's interpretation? | `_______` |
| Is a source-registry or parser-version change implied? | `_______` |
| **Is there any interpretation under which this is not drift?** | `_______` |

## 9. Owner ruling needed

State the exact question, with the options, and **do not choose one.**

> **Question for the owner:** `_______`

| Option | What it would mean | What it would require |
|---|---|---|
| A — accept the new shape | `_______` | `_______` |
| B — treat it as an anomaly and stop the phase | `_______` | `_______` |
| C — quarantine the affected records and continue with reduced coverage | `_______` | `_______` |
| D — other | `_______` | `_______` |

**No option may be exercised before the ruling.** A session that resolves drift by choosing an option
has violated the fail-closed rule.

| Field | Value |
|---|---|
| **Owner ruling** | `_______` |
| Ruling date (UTC) | `_______` |
| Does the ruling require a new accepted decision record? | `YES` / `NO` |
| If yes, decision reference | `_______` |
| Does the ruling change a parser version or the source registry? | `YES` / `NO` |
| Does the ruling change any governed identity or preimage? | `YES` / `NO` — **if yes, it needs its own methodology review** |

## 10. Correction and replay plan

| Field | Value |
|---|---|
| Correction required | `_______` |
| Authorized paths for the correction | `_______` |
| Governing contract for the correction | `_______` |
| Tests the correction must ship with | `_______` |
| Must the offline rehearsal be re-run? | `YES` / `NO` |
| Must the acquisition be re-planned? | `YES` / `NO` |
| **Is a new request budget and ceiling approval required?** | `YES` / `NO` |
| Does replay resume from the predecessor receipt, or start fresh? | `_______` |
| Predecessor receipt ID for the resume | `_______` |
| Duplicate-prevention proof for the resume | `_______` |

## 11. Closure evidence

The incident closes only when **all** of these are recorded.

| # | Evidence | Recorded |
|---|---|---|
| 11.1 | The owner ruling, with its date | `_______` |
| 11.2 | The correction, applied under an authorized contract | `_______` |
| 11.3 | Tests covering the new shape, passing | `_______` |
| 11.4 | The re-run or resumed acquisition completing | `_______` |
| 11.5 | The affected records parsed or durably quarantined | `_______` |
| 11.6 | The resumed execution receipt, naming its predecessor | `_______` |
| 11.7 | Gate H reflecting the final state | `_______` |
| 11.8 | The limitations register updated if the ruling created a limitation | `_______` |

## 12. Sign-off

| Field | Value |
|---|---|
| Owner | `_______` |
| Date closed (UTC) | `_______` |
| Incident status | `OPEN` / `RULED` / `CLOSED` |
| Resulting limitation ID, if any | `_______` |
| Signature or recorded acceptance reference | `_______` |
