# TEMPLATE — Gate H Checklist (post-acquisition verification)

**This file is a blank template. Gate H has not been run and has not passed. No live acquisition has
occurred.**
Copy it, fill every field, and retain the completed copy as evidence. Do not edit this template in
place.

**Purpose:** to prove, after the controlled metadata acquisition, that the run stayed inside every
boundary it was given — routes, budget, ceiling, response policy, provenance, drift, and secrecy —
and that nothing beyond acquisition has happened yet.
**Phase:** M3.2
**Controlling records:** [Decision 027](../../Decisions/decision_027_m3_master_plan_and_operational_readiness.md),
as narrowly corrected by proposed
[Decision 028](../../Decisions/decision_028_m3_1_readiness_corrections.md) §§7, 9–10;
[Decision 024](../../Decisions/decision_024_m2_m3_boundary_governance.md) §5.2 (the S8 row);
[Decision 009](../../Decisions/decision_009_raw_data_governance.md);
[`milestone_2_3_pilot_selection_plan.md`](../../../Milestones/milestone_2_3_pilot_selection_plan.md)
§§11 Gate H, 12, 13;
[`milestone_03_master_plan.md`](../../../Milestones/milestone_03_master_plan.md) phase M3.2.
**Completion token:** on a full pass,
`M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED`.

---

## 0. Handling

- **The completed copy is PRIVATE evidence.** It lives in the owner-controlled private evidence root,
  never in the repository. Only its type, phase, status, SHA-256, and reference identifier go into
  [`evidence_index.md`](evidence_index.md).
- **Non-secret content even so.** Counts, route names, hashes, reason codes, and outcomes only.
- **Never record** the SEC identity, any credential, any absolute personal path, or any response
  body. Cite a `receipt_id` and a reason code, not a payload.
- **Every item is `PASS`, `FAIL`, or `N/A` with a reason.**
- **Immutable once signed.**

## 1. Identification

| Field | Value |
|---|---|
| Phase | M3.2 |
| Owner | `_______` |
| Date (UTC) | `_______` |
| Operator | `_______` |
| Repository baseline commit | `_______` |
| Baseline tag | `_______` |
| Governing contract | `_______` |
| M3.2A acquisition run identifier | `_______` |
| M3.2B acquisition run identifier | `_______` |
| **M3.2A approved request-plan hash** | `_______` |
| **M3.2A approved hard ceiling** | `____` |
| **M3.2B approved request-plan hash** | `_______` |
| **M3.2B approved hard ceiling** | `____` |
| M3.2A request-budget reference | `_______` |
| M3.2B request-budget reference | `_______` |
| Gate F checklist reference | `_______` |
| Execution receipt identifiers (all) | `_______` |

## 2. Gate H pre-run state — recorded before the first request

| # | Item | Result | Evidence |
|---|---|---|---|
| 2.1 | An isolated M3.2 data root was used | `PASS`/`FAIL` | relative path only |
| 2.2 | A consistent SQLite backup of any accepted prior state was made | `PASS`/`FAIL` | `_______` |
| 2.3 | Available storage recorded | `PASS`/`FAIL` | `_______` |
| 2.4 | Quarantine and staging paths confirmed | `PASS`/`FAIL` | `_______` |
| 2.5 | Single-writer lock confirmed | `PASS`/`FAIL` | lease identifier |
| 2.6 | **No stale `.part` files** | `PASS`/`FAIL` | `_______` |
| 2.7 | **No unresolved recovery events** | `PASS`/`FAIL` | `_______` |
| 2.8 | Approved plan hash saved | `PASS`/`FAIL` | hash |
| 2.9 | Pre-run state re-established **before each window**, not once for both | `PASS`/`FAIL` | `_______` |

## 2.1 Between-windows freeze and derivation

| # | Item | Result | Evidence |
|---|---|---|---|
| 2.1a | **Transport disabled after M3.2A**, before any derivation | `PASS`/`FAIL` | `_______` |
| 2.1b | Bootstrap raw objects **frozen and identified** by content-addressed identity | `PASS`/`FAIL` | `_______` |
| 2.1c | Historical-submission references **derived from the frozen bulk-submissions object** | `PASS`/`FAIL` | `_______` |
| 2.1d | Entity reconciliation set derived from the frozen objects | `PASS`/`FAIL` | `_______` |
| 2.1e | **Second zero-request plan produced**, with its own hash | `PASS`/`FAIL` | `_______` |
| 2.1f | **Second exact owner approval recorded** before M3.2B opened | `PASS`/`FAIL` | `_______` |
| 2.1g | The derived set matches what the frozen objects actually name | `PASS`/`FAIL` | `_______` |

## 3. Actual versus planned requests

| `source_id` | Planned logical | Actual logical | Planned max physical | Actual physical | Divergence | Explained by |
|---|---:|---:|---:|---:|---:|---|
| `sec_bulk_submissions` | `____` | `____` | `____` | `____` | `____` | `_______` |
| `sec_company_tickers_exchange` | `____` | `____` | `____` | `____` | `____` | `_______` |
| `sec_company_tickers` | `____` | `____` | `____` | `____` | `____` | `_______` |
| `sec_sic_code_list` | `____` | `____` | `____` | `____` | `____` | `_______` |
| `sec_edgar_filing_calendar` | `____` | `____` | `____` | `____` | `____` | `_______` |
| `sec_edgar_calendar_announcement` | `____` | `____` | `____` | `____` | `____` | `_______` |
| `sec_full_index_company` | `____` | `____` | `____` | `____` | `____` | `_______` |
| `sec_submissions_historical` | `____` | `____` | `____` | `____` | `____` | `_______` |
| `sec_submissions_entity` | `____` | `____` | `____` | `____` | `____` | `_______` |
| **TOTAL** | `____` | `____` | `____` | `____` | `____` | |

| # | Item | Result |
|---|---|---|
| 3.1 | Every divergence is explained by a plan rule (retry, redirect, cooldown, cache hit, not-modified) | `PASS`/`FAIL` |
| 3.2 | **Actual physical attempts less than or equal to each window's approved ceiling** | `PASS`/`FAIL` |
| 3.3 | Each window completed its whole approved plan; equality with unfinished work is a ceiling stop and fails Gate H | `PASS`/`FAIL` |
| 3.4 | **No unexplained request was placed** in either window | `PASS`/`FAIL` |
| 3.5 | Each window consumed its own approved plan hash | `PASS`/`FAIL` |
| 3.6 | **No dependent request in M3.2A, and no bootstrap request in M3.2B** | `PASS`/`FAIL` |
| 3.7 | **No M3.2B request was issued under the M3.2A approval** | `PASS`/`FAIL` |

## 4. Route compliance

| # | Item | Result | Evidence |
|---|---|---|---|
| 4.1 | Every request went to `www.sec.gov` or `data.sec.gov` | `PASS`/`FAIL` | `_______` |
| 4.2 | Every request used `GET` | `PASS`/`FAIL` | `_______` |
| 4.3 | Every URL matched its source's exact path or pattern | `PASS`/`FAIL` | `_______` |
| 4.4 | **Zero prohibited-route attempts**, constructed or placed | `PASS`/`FAIL` | `_______` |
| 4.5 | **Zero filing-body URLs** | `PASS`/`FAIL` | `_______` |
| 4.6 | **Zero CompanyFacts requests** | `PASS`/`FAIL` | `_______` |
| 4.7 | **Zero Frames API requests** | `PASS`/`FAIL` | `_______` |
| 4.8 | **Zero outcome-data access** | `PASS`/`FAIL` | `_______` |
| 4.9 | Every redirect hop and every final URL was validated | `PASS`/`FAIL` | `_______` |
| 4.10 | No redirect loop, over-depth chain, or identity-bound path change | `PASS`/`FAIL` | `_______` |

## 5. Response totals

| Classification | Count |
|---|---:|
| `proceed` | `____` |
| `retry` | `____` |
| `retry_after` | `____` |
| `cooldown` | `____` |
| `fail` | `____` |
| `quarantine` | `____` |
| **Total, equal to actual physical attempts** | `____` |

| Status code | Count |
|---|---:|
| `200` | `____` |
| `304` | `____` |
| `403` | `____` |
| `404` | `____` |
| `408` / `429` / `5xx` | `____` |
| other | `____` |

| # | Item | Result |
|---|---|---|
| 5.1 | **Every response is in exactly one classification bucket; none unclassified** | `PASS`/`FAIL` |
| 5.2 | **No failure was recorded as a valid empty result** | `PASS`/`FAIL` |
| 5.3 | Every terminal failure names a registered reason code | `PASS`/`FAIL` |

## 6. Raw-store completeness

| Field | Value |
|---|---:|
| Maximum new raw objects (from the budget) | `____` |
| Actual new raw objects | `____` |
| Duplicate bodies reconciled | `____` |
| Not-modified responses | `____` |
| Cache hits (already satisfied) | `____` |
| Quarantined objects | `____` |

| # | Item | Result | Evidence |
|---|---|---|---|
| 6.1 | Object count reconciles with the budget | `PASS`/`FAIL` | `_______` |
| 6.2 | Every object verifies against its `content_sha256` | `PASS`/`FAIL` | `_______` |
| 6.3 | **Zero `.part` files remain** | `PASS`/`FAIL` | `_______` |
| 6.4 | Every orphan was adopted or quarantined; none deleted | `PASS`/`FAIL` | `_______` |
| 6.5 | **No raw object was overwritten** — a differing body became a new observation | `PASS`/`FAIL` | `_______` |
| 6.6 | Quarantined evidence is preserved and excluded from the candidate pool | `PASS`/`FAIL` | `_______` |

## 7. Provenance completeness

| # | Item | Result |
|---|---|---|
| 7.1 | Every object carries `content_sha256`, transport hash, stored-object hash, and relative path | `PASS`/`FAIL` |
| 7.2 | Every observation carries retrieval-attempt identity and `retrieved_at` UTC | `PASS`/`FAIL` |
| 7.3 | Every observation carries HTTP validator metadata | `PASS`/`FAIL` |
| 7.4 | Every observation carries its complete validated redirect chain | `PASS`/`FAIL` |
| 7.5 | Every parsed record carries parser identifier, version, and status | `PASS`/`FAIL` |
| 7.6 | Every observation carries its schema fingerprint | `PASS`/`FAIL` |
| 7.7 | Supersession lineage is complete and non-cyclic | `PASS`/`FAIL` |
| 7.8 | Accession, CIK, form type, filing date, acceptance timestamp, fiscal period end, and source offsets carried through every derived row | `PASS`/`FAIL` |
| 7.9 | **No absolute path is stored anywhere** | `PASS`/`FAIL` |

## 8. Retry compliance

| Field | Value |
|---|---:|
| Total retries | `____` |
| Maximum retries on any one logical request | `____` |
| Retry budget in force | `____` |
| Cooldowns | `____` |
| Controlled post-cooldown requests | `____` |
| Redirect hops | `____` |

| # | Item | Result |
|---|---|---|
| 8.1 | No logical request exceeded the retry budget | `PASS`/`FAIL` |
| 8.2 | Backoff followed the accepted schedule and never exceeded the ceiling | `PASS`/`FAIL` |
| 8.3 | `Retry-After` honoured where usable | `PASS`/`FAIL` |
| 8.4 | Each cooldown halted **aggregate** traffic, not one worker | `PASS`/`FAIL` |
| 8.5 | At most one cooldown; a second would have been terminal | `PASS`/`FAIL` |
| 8.6 | Redirect hops within `MAX_REDIRECT_DEPTH` | `PASS`/`FAIL` |

## 9. Budget compliance

| # | Item | Result |
|---|---|---|
| 9.1 | **No budget overflow** — actual attempts are `<=` the approved ceiling | `PASS`/`FAIL` |
| 9.2 | The ceiling was **not raised** at any point during the run | `PASS`/`FAIL` |
| 9.3 | If a run reached the ceiling, it either completed exactly there or stopped with `SEC_REQUEST_CEILING_EXHAUSTED` before `C+1` | `PASS`/`N/A` |
| 9.4 | A resumed run carried its consumed count forward against the same ceiling | `PASS`/`N/A` |

## 10. Schema drift

| Field | Value |
|---|---:|
| Total drift events | `____` |
| Unknown fields retained (non-blocking) | `____` |
| **Blocking events** | `____` |
| New historical-file references observed | `____` |

| # | Item | Result | Evidence |
|---|---|---|---|
| 10.1 | **No unresolved blocking drift** | `PASS`/`FAIL` | `_______` |
| 10.2 | Every blocking event has a schema-drift incident record and an owner ruling | `PASS`/`N/A` | `_______` |
| 10.3 | **No drift was resolved by a default, a coercion, or a dropped row** | `PASS`/`FAIL` | `_______` |
| 10.4 | Unknown fields were retained and logged, not discarded | `PASS`/`FAIL` | `_______` |

## 11. Secret and identity containment

| # | Item | Result |
|---|---|---|
| 11.1 | **No SEC identity in any log, artifact, receipt, or this document** | `PASS`/`FAIL` |
| 11.2 | **No credential, token, cookie, or authorization header anywhere** | `PASS`/`FAIL` |
| 11.3 | **No absolute personal path anywhere** | `PASS`/`FAIL` |
| 11.4 | No raw response body quoted into evidence | `PASS`/`FAIL` |
| 11.5 | `make secrets` and `make hygiene` pass | `PASS`/`FAIL` |
| 11.6 | Every receipt passes the prohibited-field scan | `PASS`/`FAIL` |

## 12. Execution receipts

| # | Item | Result |
|---|---|---|
| 12.1 | **One receipt per live command**, none missing | `PASS`/`FAIL` |
| 12.2 | Every receipt validates against `m3-execution-receipt/2.0` | `PASS`/`FAIL` |
| 12.3 | Actual counts in the receipts reconcile with §3 | `PASS`/`FAIL` |
| 12.4 | Any recovery chain resolves completely to its first attempt | `PASS`/`N/A` |
| 12.5 | **No receipt appears in any governed identity** | `PASS`/`FAIL` |

## 13. Nothing beyond acquisition has happened

| # | Item | Result |
|---|---|---|
| 13.1 | **No real candidate snapshot exists** | `PASS`/`FAIL` |
| 13.2 | **No real selection run exists** | `PASS`/`FAIL` |
| 13.3 | **No real manifest exists** | `PASS`/`FAIL` |
| 13.4 | **No root has been approved**; `approved_root_sha256` is unwritten | `PASS`/`FAIL` |
| 13.5 | **Nothing has been published** | `PASS`/`FAIL` |
| 13.6 | The S4 draft is unchanged, still `running`, never promoted | `PASS`/`FAIL` |

## 14. Network disabled afterward

| # | Item | Result | Evidence |
|---|---|---|---|
| 14.1 | **Network is disabled again** in the effective configuration | `PASS`/`FAIL` | `network: disabled (safe default)` |
| 14.2 | The live flag is not set in any persisted configuration | `PASS`/`FAIL` | `_______` |
| 14.3 | Verified **after each window's last request**, and again before this checklist was signed | `PASS`/`FAIL` | `_______` |

## 15. Catalog integrity

| # | Item | Result | Value |
|---|---|---|---|
| 15.1 | `quick_check` | `PASS`/`FAIL` | `_______` |
| 15.2 | `integrity_check` | `PASS`/`FAIL` | `_______` |
| 15.3 | `foreign_key_check` violations | `PASS`/`FAIL` | `____` |
| 15.4 | Migration checksums verified before further writes | `PASS`/`FAIL` | `_______` |
| 15.5 | Audit projection reconstructed and matching SQLite | `PASS`/`FAIL` | `_______` |

## 16. Blockers

| # | Blocker | Severity | Resolution required | Resolved |
|---|---|---|---|---|
| 1 | `_______` | `_______` | `_______` | `_______` |

**Any `FAIL`, any `UNKNOWN`, or any unresolved blocker means Gate H does not pass, and no snapshot
may be frozen.**

## 17. Owner sign-off

> I confirm that the acquisition stayed inside its approved routes, budget, and ceiling; that every
> stored object is complete and fully provenanced; that no unresolved schema drift remains; that no
> secret or identity leaked; that the network is disabled again; and that no snapshot, selection,
> manifest, approval, or publication exists.
>
> **This sign-off authorizes freezing a real candidate snapshot under a bounded M3.3 contract. It
> authorizes nothing else.**

| Field | Value |
|---|---|
| Owner | `_______` |
| Date (UTC) | `_______` |
| Gate H result | `PASS` / `FAIL` |
| Completion token recorded | `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED` / not recorded |
| Signature or recorded acceptance reference | `_______` |
