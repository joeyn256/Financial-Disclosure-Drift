# Decision 068 — M3.3 E0 Write-Set, Source-Disposition, and Contract Consistency Correction

```text
STATUS: ACCEPTED — OWNER BOUNDED CONTRACT CORRECTION
        CONTRACT ACCEPTANCE STILL PENDING FRESH REREVIEW
DATE: 2026-08-13
OWNER: Sol/GPT
OUTCOME: M3_3_FRESH_REVIEW_FINDINGS_OWNER_ADOPTED_FOR_BOUNDED_CORRECTION
IMPLEMENTATION_AUTHORIZATION: NO
REAL_PRIVATE_PARSE_AUTHORIZATION: NO
REAL_SNAPSHOT_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: none
```

**This is a narrow owner contract-correction record.** It adopts the findings of the fresh
independent review of the Decision-067-corrected M3.3 contract, corrects the contract's M3.3-E0
mechanics and consistency defects, and synchronizes the current governance surfaces. It alters **no
substantive methodology** of Decisions 067, 016, 021, 023, or any earlier accepted decision; it
authorizes **no** implementation, **no** E0 execution, **no** network, and **no** reacquisition.
Decision 067 remains accepted historical governance authority except where this record expressly
corrects the E0 contract mechanics below. Decisions 001–067 remain byte-unchanged.

**Where this record and an earlier governing record disagree**, this record controls only on the
points it names.

---

## 1. Entry state

Verified live before this record was written.

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD / `origin/main` | `8cbb77ec127cc7887e71d7fcea0c42a9b7aa41da` |
| Working tree | clean |
| HEAD subject | `Record independent review of corrected M3.3 contract` |
| Review artifact | [`Docs/m3/reviews/m3_3_corrected_contract_independent_review_c8acfef.md`](../m3/reviews/m3_3_corrected_contract_independent_review_c8acfef.md) — **immutable evidence, not edited by this record** |
| Reviewed frozen target | `c8acfef59006f8812eb5678d3f61d852d6789f07` |
| Review verdict | `M3_3_CORRECTED_CONTRACT_FRESH_INDEPENDENT_REVIEW_FAILED` — BLOCKER 0 / **MAJOR 1** / **MINOR 1** / OPTIMIZATION 0 / OBSERVATION 5 |
| `m3.2-complete` | unchanged, immutable |
| Migration chain | `0001`–`0013` |
| Tracked network switches | `false` / `false` |

## 2. Owner adoption of the review findings

```text
M3_3_FRESH_REVIEW_FINDINGS_OWNER_ADOPTED_FOR_BOUNDED_CORRECTION
```

The owner accepts the fresh independent review as **valid** and adopts **MAJ-1** (the E0
permitted-table list is incomplete and makes the accepted offline-parse design non-executable in
principle), **MIN-1** (contract §1.1 R12 pointed at architecture-map §10.2 where the applied
correction lives in §10.1), and **OBS-A through OBS-E** for bounded correction as ruled below.
**The review verdict remains `FAIL` historically**; the review artifact is preserved byte-unchanged
as evidence.

## 3. Ruling R17 — E0 Exact Permitted Persistence Footprint (adopts MAJ-1)

```text
M3_3_MAJ_1_E0_WRITE_SET_OWNER_RULED
```

**The Decision-067-era nine-table E0 list was incomplete.** M3.3-E0 is designed to reuse the already
accepted pure parsers and `CensusCatalog` persistence machinery for the source families that
actually require a candidate-substantive offline parse; the permitted durable E0 write set is
therefore the **complete legitimate write footprint of that reusable persistence path** for those
authorized source families — no less (which made E0 impossible) and no more (which would widen
authority).

**The permitted E0 durable write set is exactly these fifteen tables**, plus the
`census_plan_sources.parser_state` transition for category-A sources (§4):

| # | Table | Written by (verified) |
|---|---|---|
| 1 | `census_parser_runs` | `sec/census.py:174` (INSERT), `:206` (UPDATE) |
| 2 | `census_parsed_records` | `:441` |
| 3 | `census_structural_observations` | `:1152` |
| 4 | `census_accessions` | `:667` (+ upsert `:677`), `:912` (canonical projection UPDATE) |
| 5 | `census_accession_observations` | `:683`, `:1237` (conflict-flag UPDATE) |
| 6 | `census_registrants` | `:994` (+ upsert `:996`) |
| 7 | `census_registrant_observations` | `:1028` |
| 8 | `census_accession_field_resolutions` | `:833` (+ upsert `:840`) |
| 9 | `census_accession_cohort_resolutions` | `:870` (+ upsert `:876`) |
| 10 | `census_quarantined_records` | `:483` |
| 11 | `census_historical_references` | `:1123` |
| 12 | `census_malformed_historical_references` | `:1096` |
| 13 | `census_candidate_lineage_edges` | `:1202` |
| 14 | `census_calendar_days` | `:972` |
| 15 | `reference_sic_codes` | `:951` (the accepted `INSERT OR REPLACE` upsert) |

### 3.1 The mechanical re-verification this ruling required, performed before any edit

Every durable-write statement in the reusable path was enumerated and classified before the contract
was corrected:

- **`sec/census.py` contains exactly twenty-four durable-write statements**, resolving to exactly
  **sixteen distinct tables**: the fifteen above plus `census_qa_metrics` (`:376`).
- **`census_qa_metrics` is excluded**: its sole writer is the separate `CensusCatalog.qa_metrics()`
  entry point, called only by the network-gated orchestrator
  (`sec/census_orchestrator.py:425`) — it is not reachable from `persist()` or
  `resolve_persisted_accessions()`, and **E0 does not invoke it**; E0's own completeness proof
  substitutes.
- **`sec/accession_resolution.py`, `sec/raw_store.py` (`SnapshotStore` loading and verification),
  `sec/snapshots.py`, `sec/archive.py`, and every module under `sec/parsers/` contain zero durable
  write statements** — loading, verification, archive iteration, and parsing are pure/read-only.
- **`census.py` contains zero references** to `census_plan_sources`, `census_index_*`,
  `record_reasons`, or `record_event`; the four index-side tables (`census_index_instances`,
  `census_index_reconciliation`, `census_index_instance_events`,
  `census_index_retrieval_accounting`) are written **only** by `sec/census_orchestrator.py`, which
  E0 does not use.
- **No additional durable table is transitively or unavoidably written** by the reusable E0
  persistence path. The stop-and-report branch this ruling reserved for that case was therefore not
  taken.

### 3.2 What R17 does not permit

- **The four index-side tables remain outside candidate-substantive E0**:
  `census_index_instances`, `census_index_reconciliation`, `census_index_instance_events`, and
  `census_index_retrieval_accounting` are **not** authorized, and may not be populated solely to
  make full-index sources appear "parsed" (§4). `census_index_instances` remains
  AVAILABLE-AS-NONE (Decision 067 §10.6).
- **`census_qa_metrics` is not written at E0.**
- **No second writer implementation** may be created to avoid the corrected write set (the
  M3.3 contract §20 prohibition stands unchanged).
- **Nothing else changes**: no `pilot_candidate_*` write (that is M3.3-E1), no
  `census_source_observations` mutation, no raw-object mutation, no receipt mutation.

**Cite as:** *M3.3 Owner Ruling R17 — E0 Exact Permitted Persistence Footprint.*

## 4. Ruling R18 — E0 Planned-Source Disposition (adopts MAJ-1's secondary facet)

```text
M3_3_MAJ_1_SOURCE_DISPOSITION_OWNER_RULED
```

**E0 completeness is not defined as "mutate `parser_state` for every M3.2 planned source."**
Instead, every accepted M3.2 planned source receives exactly one **report-level** E0 disposition:

| Category | Name | Meaning |
|---|---|---|
| **A** | `E0_REQUIRED_PARSE` | Source content is substantively required for M3.3 candidate construction and must successfully traverse the authorized offline parse path — unless the accepted source is already failed/unavailable |
| **B** | `E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE` | A candidate-substantive source already accepted as failed or unavailable. No parser execution is fabricated, no substitute observation is used, and the existing fail-closed rules (Decision 067 §10.3; R14) govern every downstream use |
| **C** | `E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY` | Accepted M3.2 evidence whose parser output is not used by the authoritative M3.3 candidate builder |

**The 70 quarterly full-index sources are category C** unless an already accepted field-level OR-2
mapping proves otherwise — under the adopted normative mapping they are provenance-only, and their
index-side parse destinations are excluded (§3.2). For category-C sources: excluded index tables
are **not** populated to satisfy a completion metric; **no parser run is fabricated**;
**`census_plan_sources.parser_state` is not altered** merely to make the ledger appear complete;
the accepted acquisition evidence is preserved; and each is **enumerated explicitly** in the E0
completion report as `NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY`.

**The E0 completeness proof must show:** every planned source enumerated; **exactly one**
disposition per planned source; every category-A source parsed successfully; every category-B
source preserved truthfully as failed/unavailable; every category-C source deliberately untouched;
and **no unclassified source**.

**This is a report/contract disposition vocabulary only.** No database enum value, no schema
change, and no migration is created or authorized by it.

**Cite as:** *M3.3 Owner Ruling R18 — E0 Planned-Source Disposition.*

## 5. Auxiliary-output semantics — inclusion is not licence

Adding a table to the permitted E0 write set does **not** make arbitrary content acceptable:

- `census_quarantined_records` remains governed by the existing accepted parser and QA rules;
- the historical-reference tables may remain empty where the accepted input contains no authorized
  historical material, and **no missing per-registrant historical document may be retrieved**
  (Decision 067 §10.4 unchanged);
- `census_candidate_lineage_edges` may contain only lineage derived from accepted stored metadata;
- `census_calendar_days` may contain only authorized calendar parse output;
- `reference_sic_codes` may contain only output derived from the authoritative, plan-bound accepted
  SIC source (`census_plan_sources.observation_id` binding, R13);
- any parser or QA condition that existing accepted rules classify as blocking **continues to block
  E0 success**;
- **no table's inclusion in the write set lowers an evidence floor.**

## 6. MIN-1 — the R12 pointer correction

The current contract wording "architecture-map §10.2 `Status` bullet" is corrected to
"architecture-map **§10.1** `Status` bullet". The underlying accepted R12 rule is unchanged, and
historical records that quote the earlier pointer (the failed review artifact included) are **not**
rewritten.

## 7. OBS dispositions

| ID | Disposition |
|---|---|
| **OBS-A** | **Adopted and fixed.** Current operative "Both reviews" wording, where three reviews are enumerated, is replaced with wording stating the exact count — "all three §30 reviews" — in the corrected contract |
| **OBS-B** | **Adopted as clarification R16-C1 (§8 below).** No new role filter, no new resolution methodology |
| **OBS-C** | **Adopted and fixed.** `M3.3-E0` / `M3.3-E1` / `M3.3-E2` are reserved for the real owner-gated execution stages; current operative documentation qualifies rehearsal labels explicitly ("rehearsal scenario E1", "rehearsal scenarios E1–E8"). Historical artifact labels are preserved. **No gate semantics change** |
| **OBS-D** | **Adopted and fixed.** The current master-plan M3.3 implementation-category list gains the bounded offline metadata-parse driver / entry point — descriptive only; it grants no implementation, E0, private-mutation, or network authority |
| **OBS-E** | **Adopted as a historical erratum.** The GR proposal §B.2's "four snapshot timestamps" should read "three snapshot timestamps"; a narrow visible erratum note is added to the proposal without rewriting its historical text, and the underlying inclusion/exclusion tally is unchanged |

## 8. Clarification R16-C1 — Resolution Contributor Membership (adopts OBS-B)

```text
M3_3_OBS_B_R16_MEMBERSHIP_OWNER_CLARIFIED
```

Ruling R16 (Decision 067 §7) already governs the digest fields and deterministic ordering. The
membership rule is clarified, not changed:

**`contributing_evidence_sha256` includes exactly the persisted candidate evidence rows that the
accepted deterministic classification/resolution procedure actually uses to establish the
corresponding resolved value.** Membership is **substantive, not discretionary**; it may **not** be
inferred merely from `evidence_role`; it may **not** include unrelated evidence rows merely because
they share the same candidate or dimension; it must be **independently recomputable**; it must be
**deterministic** for identical candidate evidence; and M3.3-I/R must expose it through **one
explicit deterministic membership selection/query or equivalent pure function**, and must **test**
it. If existing accepted methodology or code cannot mechanically determine the contributor set for
a dimension, the session **stops and returns to the owner** — no new role filter and no new
resolution methodology may be invented.

**Cite as:** *M3.3 Owner Clarification R16-C1 — Resolution Contributor Membership.*

## 9. Governance surfaces this record touches

| Surface | Effect |
|---|---|
| [`Milestones/contracts/m3_3.md`](../../Milestones/contracts/m3_3.md) | Corrected to carry R17, R18, R16-C1, the §10.1 pointer fix, the R18 completeness language, and the OBS-A/OBS-C wording fixes; status now `CORRECTED — DECISIONS 067–068 OWNER RULINGS RECORDED — PENDING FRESH INDEPENDENT REREVIEW AND OWNER ACCEPTANCE`. **Still not accepted** |
| [`Docs/m3/m3_3_snapshot_authority_adjudication_proposal.md`](../m3/m3_3_snapshot_authority_adjudication_proposal.md) | OBS-E erratum note only; body preserved as historical proposal evidence |
| [`Docs/m3/m3_3_governance_foundation_inventory.md`](../m3/m3_3_governance_foundation_inventory.md) | Current-state banner and §G dispositions updated. Still a navigation index |
| [`Docs/m3/operator_runbook.md`](../m3/operator_runbook.md) | §28a gains the R17 write-footprint and R18 disposition statements |
| `Milestones/STATUS.md`, `Milestones/milestone_03_master_plan.md`, `Milestones/contracts/README.md`, `Docs/Decisions/decision_registry.md`, `Docs/decision_index.md`, `Docs/architecture_map.md`, `Docs/change_impact_map.md` | Current-state synchronization only |
| [`Docs/m3/reviews/m3_3_corrected_contract_independent_review_c8acfef.md`](../m3/reviews/m3_3_corrected_contract_independent_review_c8acfef.md) | **Not modified.** Immutable evidence of the failed review |

**No executable source, test, migration, configuration, or CI file is changed by this record, and
no private evidence is read or mutated.**

## 10. What this record does not authorize

It does **not**: authorize implementation; accept the M3.3 contract; authorize M3.3-I/R; authorize
executing the offline parse (M3.3-E0) or progressing to M3.3-E1; enable network access; authorize
an SEC request, reacquisition, or re-retrieval; authorize a migration; authorize populating any
index-side table or `census_qa_metrics` at E0; authorize mutating the accepted real private catalog
or any M3.2 private evidence; authorize a real snapshot, selection, manifest, or root; approve
anything; close any limitation; move `m3.2-complete`; or begin M3.4.

## 11. Next authorized action

**A fresh independent M3.3 contract rereview** of the Decisions-067–068-corrected contract, in a
**new epoch** (`/clear` first) — the session that authored this correction is an author of the
corrected contract and is **disqualified from rereviewing it**. After that rereview passes, a
separate owner acceptance act is still required. **No M3.3-I/R, no E0, and no E1 until then.**

```text
M3_3_DECISION_068_BOUNDED_CONTRACT_CORRECTION_READY_FOR_FRESH_REREVIEW
```
