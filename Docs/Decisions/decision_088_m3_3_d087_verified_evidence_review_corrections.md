# Decision 088 — D087 Verified-Evidence Schema: Owner Adjudication of the Independent-Review Findings and Bounded Correction Authorization

```text
STATUS: ACCEPTED — OWNER ADJUDICATION OF THE D087 INDEPENDENT REVIEW AND BOUNDED CORRECTION AUTHORIZATION
DATE: 2026-08-15
OWNER: Sol/GPT
OUTCOME: M3_3_D087_REVIEW_FINDINGS_OWNER_ACCEPTED_FOR_BOUNDED_CORRECTION
D087_INDEPENDENT_REVIEW_VERDICT: FAIL — BLOCKER 0 / MAJOR 1 / MINOR 3 / OBSERVATION 3
D087_VERIFIED_EVIDENCE_SCHEMA: NOT YET OWNER ACCEPTED
M_1_DISPOSITION: ACCEPTED / CORRECTION REQUIRED / ACCEPTANCE-GATING
MIN_1_DISPOSITION: ACCEPTED / CORRECT NOW
MIN_2_DISPOSITION: ACCEPTED / CORRECT NOW
MIN_3_DISPOSITION: ACCEPTED / CORRECT NOW
OBS_2_DISPOSITION: ACCEPTED / CORRECT COMMENT NOW
OBS_3_DISPOSITION: ACCEPTED / STRENGTHEN VALIDATION NOW
OBS_1_DISPOSITION: ACCEPTED AS NON-GATING OBSERVATION / DEFERRED
MIGRATION_AUTHORIZED: 0015 only (correction in place; NOT a new migration)
MIGRATION_0016_AUTHORIZATION: NO
DOCUMENT_REVIEW_A_AUTHORIZATION: NO
DOCUMENT_REVIEW_B_AUTHORIZATION: NO
DOCUMENT_ADJUDICATION_AUTHORIZATION: NO
E0_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
D081_PRIVATE_EVIDENCE_ACCESS: NO
```

**This record does two things and nothing else.** It records Sol/GPT's **owner adjudication** of the
fresh independent review of the Decision 087 verified-evidence implementation, and it authorizes a
**bounded correction** of the six findings it accepts for correction.

**It grants no execution authority and no acceptance.** The verified-evidence schema is **not**
owner-accepted by this record, no document review runs, no filing is classified, no real evidence is
created, and no network, SEC, or HTTP request is made.

---

## 1. The independent review, and its frozen verdict

The Decision 087 §18 fresh independent review ran at **Claude Fable 5, maximum effort**, in a fresh
`/clear` epoch, against the frozen implementation target `8c13fc79aee649df4956643f0b24504c8cdfd2c7`
(tree `80dc6c051641551e6b53ffd02a41f94db4d8a6d6`). It returned:

```text
VERDICT: FAIL
BLOCKER 0   MAJOR 1   MINOR 3   OPTIMIZATION 0   OBSERVATION 3
M3_3_DECISION_087_VERIFIED_EVIDENCE_SCHEMA_INDEPENDENT_REVIEW_FAIL
```

**That verdict is frozen and immutable.** It was reached and reported **before** any correction
authority existed, and nothing in this record revises, softens, or reinterprets it. The review
corrected nothing and accepted nothing on the owner's behalf.

The review confirmed, independently and by execution, that the accepted architecture is sound: the
verified-applicability boundary is enforced at both the schema and the module layer, no
`verified_amends_original` state exists, reviewer-epoch independence holds in both the restrictive
and the permissive direction, private-evidence-root nonleakage holds with no locator column at all,
the seven new hash domains reuse `release/hashing.py` with no frozen tuple widened, and the only
identity movement is the accepted **R68** migration-chain policy binding — reproduced to the byte,
with `candidate_tables_sha256` and `selection_result_sha256` byte-identical. **No redesign is
warranted, and none is authorized.**

## 2. Owner adjudication of the findings

| Finding | What it is | Owner disposition |
|---|---|---|
| **M-1** | `INSERT OR REPLACE` rewrites rows in all four evidence relations by implicit delete-and-insert, bypassing the `BEFORE UPDATE` / `BEFORE DELETE` protections under this repository's governed connection settings | **ACCEPTED / CORRECTION REQUIRED / ACCEPTANCE-GATING** |
| **MIN-1** | A review or adjudication for accession *X* may uniformly bind an artifact registered to accession *Y* | **ACCEPTED / CORRECT NOW** |
| **MIN-2** | `agreement_state = 'agreed'` with `evidence_level = 'verified'` is representable over two abstaining reviews with zero spans; and the `verified` ⇒ `agreed`/`resolved` CHECK has no protecting test | **ACCEPTED / CORRECT NOW** |
| **MIN-3** | The verified-candidate guard does not fire when `accession_plain` changes while the level stays `verified` | **ACCEPTED / CORRECT NOW** |
| **OBS-2** | Migration `0015` §1's comment misdescribes the enforced precondition list | **ACCEPTED / CORRECT COMMENT NOW** |
| **OBS-3** | `span_location` admits malformed byte ranges such as `bytes:1a-2b` | **ACCEPTED / STRENGTHEN VALIDATION NOW** |
| **OBS-1** | The contributor-JSON arithmetic admits non-canonical encodings | **ACCEPTED AS NON-GATING OBSERVATION / DEFERRED** |

```text
M3_3_D087_REVIEW_FINDINGS_OWNER_ACCEPTED_FOR_BOUNDED_CORRECTION
```

## 3. M-1 — the replacement-rewrite door is acceptance-gating

The review proved on disposable catalogs, through the repository's own connection machinery, that
SQLite resolves an `INSERT OR REPLACE` conflict by deleting the conflicting row and inserting the
new one, and that the implicit delete fires no `BEFORE DELETE` trigger unless `PRAGMA
recursive_triggers` is on — **which this project never sets**. A frozen adjudicated result, a review
record's role and epoch, span provenance, and artifact metadata were each rewritten that way while
every existing protection stayed silent.

**This is the same defect class accepted migration `0013` already anticipated** for
`pilot_manifest_versions` and `pilot_selection_runs`, and it is corrected the same way: a
`BEFORE INSERT` guard, which fires **before** conflict resolution can delete anything and therefore
holds on every connection whatever the pragma settings are.

**Required semantic outcome.** Once a governed key or unique identity already exists, no
conflict-resolution write idiom may silently rewrite it or silently pass. The correction covers
`INSERT OR REPLACE`, an ordinary duplicate `INSERT`, and `INSERT OR IGNORE` — which the accepted
`0013` pattern refuses rather than letting it no-op — across **every** unique route of **all four**
relations. `BEFORE UPDATE` and `BEFORE DELETE` protections are **kept**; the review proved them
necessary but not sufficient, and neither is removed.

```text
D087_M1_REPLACEMENT_REWRITE_DOOR = MUST BE CLOSED AND PROVEN CLOSED
```

## 4. MIN-1 — cross-accession artifact binding

Every `document_review_records` row must bind an artifact whose **registered** accession equals the
review's own `accession_plain`, and every `document_adjudicated_evidence` row must do the same. The
existing bound-artifact trigger enforces only that the reviews of one accession agree with each
other, which a uniformly cross-bound set satisfies.

**No new accession identity is invented.** `document_artifacts.accession_plain` is already the
registered fact; the correction requires the other two relations to agree with it.

## 5. MIN-2 — `agreed` means both passes substantively asserted the adjudicated evidence

Decision 082 §12.6 defines `agreed` as A and B agreeing **exactly** on the category and on every
extracted assertion. An `agreed` adjudication therefore requires **both** required contributing
review records to be **non-abstaining** and to carry the assertion the adjudicated value states, per
evidence kind.

**Abstention is not turned into a negative assertion, and no evidence is fabricated from absence.**
An abstention remains a recorded outcome (Decision 080 **AP-1** totality) that earns nothing; the
`abstained` and `conflicting` routes are unchanged and remain unable to carry `verified`.

The existing `verified` ⇒ `agreed`/`resolved` CHECK additionally receives a **dedicated negative
test**: the review demonstrated that removing that CHECK survived every existing test, which makes
it an unprotected guard rather than a proven one.

## 6. MIN-3 — the verified candidate level follows its accession

The verified-candidate guard fires on `INSERT` and on `UPDATE OF amendment_purpose_evidence_level`.
It must also fire when the **accession identity the evidence depends on** is changed while the level
remains `verified`. This is the same genus as the accepted Decision 085 **MIN-2** door, and it is
closed the same narrow way: by naming the additional column, not by redesigning candidate identity.

**Verified applicability is not widened.** `verified` remains authorized for amendment purpose and
amendment linkage / explicit-original only.

## 7. OBS-2 and OBS-3 — truthful comment, strict validation

**OBS-2 is a comment correction only.** Migration `0015` §1 claims its guard list is migration
`0014`'s precondition set plus three children; the enforced list in fact **omits**
`census_parsed_records` and `census_parser_runs`, because `0015` rebuilds no census relation. The
comment is corrected to describe the enforced list truthfully and to say why those two entries are
not needed here. **No executable change is authorized for OBS-2 alone.**

**OBS-3 strengthens `span_location` validation now.** The canonical form is
`bytes:<decimal_start>-<decimal_end>` with ASCII decimal digits only, rejecting letters, spaces,
signs, decimal points, path characters, alternate prefixes, and empty endpoints, while preserving
the existing non-empty requirement. **No fuzzy source-location semantics are introduced**, and
nothing beyond strict decimal validation is authorized — Decision 080 **AP-9** continues to fail a
non-locatable span closed at consumption.

## 8. OBS-1 — deferred, and recorded as open

The contributor-JSON arithmetic (`1 + 67n` characters, `2n` quotes, containment of every identity)
admits non-canonical encodings. It is **not** corrected in this stage, for reasons the owner
records rather than assumes:

* the authoritative membership set remains `document_review_records`, not the JSON string;
* the module emits canonically sorted, deduplicated, hex-validated identities;
* a malformed non-canonical representation creates **no false hash-derived membership**;
* a clean fix without JSON1, under the declared SQLite 3.37 floor, may cost complexity
  disproportionate to the current risk.

```text
OBS-1 = NON-GATING / DEFERRED / OPEN
```

**OBS-1 must not be reported as fixed, closed, or resolved.** A future record may take it up.

## 9. Role: the same epoch corrects, and may not accept

The Fable 5 epoch that produced the failed independent review is reused **only** as the
owner-authorized correction executor, under this record's authority and no other.

| Fact | Value |
|---|---|
| The independent FAIL verdict | Reached and reported **before** any correction authority existed |
| Corrections before the verdict | **None** |
| The session's role now | **Correction executor**, by this record |
| That session's eligibility to accept its own corrected target | **NONE** |

**The acceptance rereview must be a fresh `/clear` epoch** that inherits none of the correction
session's conclusions. **Successful correction is not acceptance.**

## 10. Authorized implementation paths

```text
src/disclosure_drift/storage/migrations/0015_m33_verified_document_evidence.sql   (corrected in place)
tests/unit/test_m3_3_verified_document_evidence.py
tests/unit/test_m23_pilot_manifest_store.py   (policy-chain re-baseline, only if the bytes move it)
Docs/sec_data_dictionary.md
Docs/architecture_map.md
Docs/change_impact_map.md
Docs/decision_index.md
Docs/Decisions/decision_registry.md
Milestones/STATUS.md
```

Migration `0015` is **corrected in place**. It is not owner-accepted, no real state was ever created
from it, and every catalog it has ever touched is disposable — so amending the unaccepted record is
correct, and **no migration `0016` is authorized**.

**Explicitly prohibited:** `cohorts.py`; `pilot_policy.py`; `candidate_identity.py`;
`candidate_snapshot.py`; `offline_execution.py` beyond the accepted **R66** caller;
`acquisition.py` beyond the current migration-head truth; `release/hashing.py`; migrations
`0001`–`0014`; `Docs/preregistration.md`; Decisions 001–087; every prior independent-review
artifact; the accepted Decision-081 evidence; the accepted M3.2 private evidence; every network,
acquisition, and transport module; candidate-selection methodology; document-classification logic;
real review execution; and **E0**.

**If an additional executable path proves technically required: STOP** and return to Sol/GPT.

## 11. Identity and the migration chain

Correcting migration `0015` changes its bytes, so the already-accepted **R68** policy-binding path
may move again:

```text
0015 checksum -> migration_chain_sha256 -> selector_policy_sha256
              -> root_manifest_sha256 / manifest_id
```

That movement is **expected and accepted** where it is caused **solely** by the final `0015` bytes.
It must be enumerated explicitly, and these eight components must be **byte-identical**:
`candidate_tables_sha256`, `selection_result_sha256`, `source_observation_set_sha256`,
`quota_definitions_sha256`, `selected_entities_sha256`, `selected_accessions_sha256`,
`reserves_sha256`, and `quota_report_sha256`.

**If any other component moves: STOP and report.** `ACCESSION_TABLE_COLUMNS`,
`REGISTRANT_TABLE_COLUMNS`, and `SNAPSHOT_CONTENT_FIELDS` are not widened (accepted **R67**).

## 12. Required adversarial effectiveness — VE-R1 … VE-R10

**VE-M1 … VE-M14 are re-run**, and the newly discovered doors receive their own matrix.
**Effectiveness is demonstrated, not named**: each protection is shown to refuse the exact defect,
and the guards are shown to be load-bearing rather than nominal.

| # | The mutation that must be rejected |
|---|---|
| **VE-R1** | `INSERT OR REPLACE` against a frozen adjudicated row |
| **VE-R2** | `INSERT OR REPLACE` against a review record |
| **VE-R3** | `INSERT OR REPLACE` against a review span |
| **VE-R4** | `INSERT OR REPLACE` against artifact metadata |
| **VE-R5** | Cross-accession review / artifact binding |
| **VE-R6** | Cross-accession adjudication / artifact binding |
| **VE-R7** | `agreed` + `verified` over one or both abstaining reviews |
| **VE-R8** | Removing the `verified` ⇒ `agreed`/`resolved` guard must kill a targeted negative test |
| **VE-R9** | Re-pointing a verified candidate to an accession without frozen evidence |
| **VE-R10** | Malformed byte-range locations carrying alphabetic or other non-decimal characters |

The lawful lifecycle must remain representable throughout: artifact → Review A and its spans →
Review B and its spans → `agreed` adjudication → verified purpose and linkage evidence → verified
candidate consumption, plus the `resolved` route with its third adjudication epoch.

## 13. Stop conditions

The session **STOPS** and returns to Sol/GPT if closing the replacement door requires redesigning the
evidence lifecycle; if cross-accession integrity cannot be enforced without changing the
four-relation contract; if `agreed`-state consistency requires new methodology; if the candidate
re-point protection requires candidate-identity redesign; if OBS-3 requires source-location
semantics beyond strict decimal validation; if the `0015` correction moves a non-policy manifest
component; if a frozen candidate identity tuple must widen; if real evidence, network, or **E0**
becomes necessary; if migration `0016` becomes necessary; or if a new BLOCKER or MAJOR remains
unresolved.

**A stop condition is never worked around.**

## 14. What this record does not authorize

It does **not** accept the verified-evidence schema; execute Review A, Review B, or the
adjudication; classify any real filing; populate or access any real Decision-081 evidence; resolve
real amendment parentage; grant quota credit; close either real-path feasibility gate; authorize
**M3.3-E0**, **E1**, **E2**, or **M3.4**; authorize any network, SEC, or HTTP request; write
migration `0016`; reverse Decision 071's **IN-2**; move `m3.2-complete`; or create any tag.

Both real-path feasibility gates — `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
`M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` — remain **OPEN** and are never merged into one
flag, and `REAL_ACCEPTANCE_ORDERING_ADEQUACY` remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION**.

## 15. Next authorized action

**Correct M-1, MIN-1, MIN-2, MIN-3, OBS-2, and OBS-3 under §10, then return to Sol/GPT.** The
correcting session does **not** self-review, does **not** accept its own target, and does **not**
start Review A, Review B, the adjudication, or **E0**.

```text
M3_3_D087_REVIEW_FINDINGS_OWNER_ACCEPTED_FOR_BOUNDED_CORRECTION
D087_VERIFIED_EVIDENCE_SCHEMA = NOT YET OWNER ACCEPTED
OBS-1 = NON-GATING / DEFERRED / OPEN
MIGRATION_AUTHORIZED = 0015 only (corrected in place); MIGRATION 0016 = NO
M3_3_E0_AUTHORIZATION = NO
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY = PENDING FUTURE AUTHORIZED E0 VERIFICATION
```
