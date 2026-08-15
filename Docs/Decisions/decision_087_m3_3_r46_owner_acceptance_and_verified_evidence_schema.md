# Decision 087 — R46 Final Owner Acceptance and Verified-Evidence Schema Implementation Authorization

```text
STATUS: ACCEPTED — OWNER FINAL R46 ACCEPTANCE AND VERIFIED-EVIDENCE SCHEMA IMPLEMENTATION AUTHORIZATION
DATE: 2026-08-15
OWNER: Sol/GPT
OUTCOME: M3_3_D085_R46_CORRECTED_IMPLEMENTATION_OWNER_ACCEPTED
M3_3_D085_R46_CORRECTED_IMPLEMENTATION_OWNER_ACCEPTED: YES — frozen at 1c5b0150ecfc5e4695842e330d83f1ce2148c643
M3_3_R49_CONDITION_B_SATISFIED: YES
M3_3_PRE_E0_MULTI_REGISTRANT_HOLD_CLOSED: YES
VERIFIED_EVIDENCE_SCHEMA_CONTRACT: OWNER ACCEPTED / IMPLEMENTATION AUTHORIZED
MIGRATION_AUTHORIZED: 0015 only
MIGRATION_0015_AUTHORIZATION: YES
FUTURE_ADJUDICATION_PROTOCOL_CONTRACT: OWNER ACCEPTED / EXECUTION DEFERRED
DOCUMENT_REVIEW_A_AUTHORIZATION: NO
DOCUMENT_REVIEW_B_AUTHORIZATION: NO
DOCUMENT_ADJUDICATION_AUTHORIZATION: NO
M3_3_E0_DURABLE_PARSE_AUTHORIZATION: NO
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

**This record does two things and nothing else.** It records Sol/GPT's **final owner acceptance** of
the corrected **R46** multi-registrant implementation, and it **lifts the implementation deferral** on
the already-owner-accepted verified-evidence schema contract so that migration `0015` and the narrow
infrastructure it needs may be built.

**It grants no execution authority.** No document review runs, no filing is classified, no real
amendment parentage is resolved, no quota credit is granted, no feasibility gate closes, no real
offline parse begins, and no network, SEC, or HTTP request is made.

---

## 1. Acceptance baseline — verified

| Fact | Value |
|---|---|
| Branch | `main` |
| `HEAD` == `origin/main` | `3749b012c5a794d1c51aa6495f7f234806db6b49` — the genuine-Fable review-publication commit |
| Parent | `c6cd1dfdcae12453129b007c72503ea88d1f4660` — the Decision 086 authority commit |
| Frozen R46 implementation target | `1c5b0150ecfc5e4695842e330d83f1ce2148c643` |
| Frozen R46 implementation tree | `1994e8bfe54b8db03da765980f5df2d6dff822ba` |
| Genuine-Fable review artifact | [`Docs/m3/reviews/m3_3_d085_r46_genuine_fable_rereview_1c5b015.md`](../m3/reviews/m3_3_d085_r46_genuine_fable_rereview_1c5b015.md) |
| `m3.2-complete` | `2865a1479e4576dc18a4098c928b278812f38d00`, unmoved |
| Working tree | CLEAN |
| Migrations | `0001`–`0014` contiguous; `0015` absent |

Verified read-only by Git and by `scripts/verify_target.py` (10 of 10 checks passed). No fetch, pull,
reset, clean, or stash was performed.

## 2. Final owner acceptance of the corrected R46 implementation

The genuine **Claude Fable 5 maximum** formal independent rereview commissioned by
[Decision 086](decision_086_m3_3_d085_correction_owner_adjudication_and_fable_rereview.md) §5 ran in a
genuine fresh epoch, reported its harness identity before substantive review, and returned:

```text
VERDICT: PASS
BLOCKER 0   MAJOR 0   MINOR 0
M3_3_D085_R46_GENUINE_FABLE_REREVIEW_PASSED_READY_FOR_OWNER_ACCEPTANCE
```

Sol/GPT **accepts** the corrected R46 implementation frozen at
`1c5b0150ecfc5e4695842e330d83f1ce2148c643` (tree `1994e8bfe54b8db03da765980f5df2d6dff822ba`).

```text
M3_3_D085_R46_CORRECTED_IMPLEMENTATION_OWNER_ACCEPTED
```

**R49 condition B** — which [Decision 081](decision_081_m3_3_fixed_complete_submission_source_verification.md)
§6 made a precondition to **M3.3-E0**, and which
[Decision 083](decision_083_m3_3_pre_e0_multi_registrant_correction.md) §12 said is satisfied "only
after the implementation receives a fresh independent review **and** Sol/GPT owner acceptance" — now
has both halves:

```text
M3_3_R49_CONDITION_B_SATISFIED
```

The special pre-**E0** multi-registrant hold is **permanently closed**:

```text
M3_3_PRE_E0_MULTI_REGISTRANT_HOLD_CLOSED
```

No further R46 correction or review is required unless a later stage discovers a genuinely **new**
defect. Decisions 082–086 and every prior review artifact are **not rewritten**.

## 3. R49 condition B is not E0 authorization

Satisfying one precondition does not discharge the others, and this record grants no execution.

| State | Value |
|---|---|
| **R46** | **OWNER ACCEPTED** |
| Migration `0014` | **ACCEPTED SOFTWARE BASELINE** for future real M3.3 state |
| **M3.3-E0** | **NOT AUTHORIZED** |
| **M3.3-E1** | **NOT AUTHORIZED** |
| **M3.3-E2** | **NOT AUTHORIZED** |
| **M3.4** | **NOT AUTHORIZED** |
| Network / SEC / HTTP | **NONE**, `REQUEST_CEILING = 0` |

The next authorized implementation stage is the **verified-evidence schema / migration `0015`**, and
nothing beyond it.

## 4. The verified-evidence schema contract — implementation deferral lifted

[Decision 082](decision_082_m3_3_d081_owner_adjudication_and_pre_e0_contracts.md) §11 designed the
verified-evidence schema. [Decision 083](decision_083_m3_3_pre_e0_multi_registrant_correction.md) §8
(**R63**) accepted it, adjudicated its four open items, and deferred implementation with
`MIGRATION_0015_AUTHORIZATION = NO`.

**That deferral is lifted.** The contract's content is unchanged; only its implementation status moves.

```text
VERIFIED_EVIDENCE_SCHEMA_CONTRACT = OWNER ACCEPTED / IMPLEMENTATION AUTHORIZED
MIGRATION_AUTHORIZED              = 0015 only
```

Exactly one migration is authorized: the next number, `0015`. It stays **separate** from `0014`, and
`0014` is neither rewritten nor squashed — the Decision 082 §11.4 ordering constraint (`0014` precedes
`0015`) is preserved as an actual chain position.

## 5. The four required relations, and their controlling semantics

The four Decision 082 §11.2 relations are implemented at their contract semantics as adjudicated by
Decision 083 **R63**:

| Relation | What it holds |
|---|---|
| `document_artifacts` | Governed **catalog metadata** for one bound document artifact |
| `document_review_records` | One independent review pass's record for one artifact |
| `document_review_spans` | Exact verbatim source spans supporting a review record |
| `document_adjudicated_evidence` | The frozen final adjudication result for one accession and evidence kind |

These relations are **infrastructure for future reviewed document evidence**. They are created empty.
No real Decision-081 evidence is populated by this stage; only synthetic, disposable test fixtures
touch them.

### 5.1 `document_artifacts` — catalog metadata only (R63 item A)

`document_artifacts` is a governed **catalog-metadata** relation. The Complete Submission Text bytes
stay in the **private external evidence root** and **never enter SQLite**.

**No absolute `EV_ROOT` path, private filesystem path, local user path, or scratch path is persisted**,
and none may be. The relation stores artifact identity (`artifact_sha256`), public source identity, the
content hash, and the content/provenance metadata needed to bind the artifact. A content-addressed or
private-object locator is permitted **only if technically required** and must never expose `EV_ROOT` —
and it is **not** required here, because the SHA-256 is itself the content address, so **no locator
column exists at all**. That is the strongest available form of the rule, not a relaxation of it.

### 5.2 `document_review_records` — opaque review epochs (R63 item D)

The relation must **mechanically distinguish** Review A, Review B, and adjudication, using durable
**opaque review-epoch identifiers** plus reviewer **role** and **model**. **No personal reviewer name**
is persisted and **no raw Claude session ID** is required. The governed record must be sufficient to
prove the review epochs are distinct — a property this record requires to be *enforced*, not merely
recorded.

The frozen future protocol version is `m3.3-document-evidence/1.0`
([Decision 083](decision_083_m3_3_pre_e0_multi_registrant_correction.md) §9, **R64**). The schema may
store that version exactly as contracted. **That protocol is not executed by this stage.**

### 5.3 `document_review_spans` — exact source-span provenance

A future evidence judgment must be traceable to the bound document artifact, the review record, the
relevant source span(s), and the defined evidence question or category — **without fuzzy text search at
acceptance time**. Decision 082 §12.5's requirements (verbatim text, a stable location inside the
frozen artifact, a span hash) are preserved where they are more specific.

**No classifier and no automated evidence-inference system is invented.** Decision 071's **IN-2** is
not reversed, and every prohibited classification route in Decision 082 §12.3 remains prohibited.

### 5.4 `document_adjudicated_evidence` — where `verified` is authorized (R63 item C)

For **M3.3 v1**, `evidence_level = verified` is authorized **only** for:

* **A.** amendment **purpose**; and
* **B.** amendment **linkage / explicit-original** evidence.

It is **not** silently permitted for size, industry, history, universe, cohort, XBRL eligibility,
control predicates, name/ticker, or **any** other evidence dimension. **Schema and policy validation
must enforce that restriction**, not document it.

## 6. Linkage semantics (R63 item B)

**No new semantic relationship state is invented.** In particular `verified_amends_original` must not
exist anywhere in the schema, in policy validation, or in source.

When the relationship itself is established, the existing semantic is reused:

```text
amendment_linkage_state = amends_original
```

Verification **strength** is separate, and lives in `evidence_level = verified` together with its
document, review, and adjudication provenance. The schema must distinguish **what** the relationship is
from **how strongly, and by what process,** it was verified.

## 7. Evidence-level extension

The Decision 082 §11.2 / Decision 080 §9.3 extension is implemented: the candidate evidence-level
constraint that today excludes `'verified'` by design, and the `amendment_purpose_quota_eligible` rule
that today requires `'provisional'`, both widen — **only** for the authorized amendment-purpose
dimension.

Existing evidence-level validation for **every other dimension is not weakened**. Existing synthetic
and rehearsal rows are **not silently reinterpreted**: accepted synthetic identities and historical
artifacts remain unchanged.

## 8. Append-only / immutability model

The four evidence relations follow the accepted append-only, freeze-oriented provenance model, using
the exact Decision 082 §11.2 statement that each is "append-only and immutable once frozen".

At minimum, the schema must protect against unauthorized:

1. in-place mutation of a frozen review;
2. rewriting source-span provenance;
3. changing an artifact SHA after review;
4. changing reviewer role or epoch after freeze;
5. changing an adjudicated result after final freeze.

**No delete or update flexibility is invented for convenience.** Where Decision 082 specifies freeze
states, uniqueness, keys, or allowed lifecycle transitions, those exact specifications control.

## 9. Hash and identity discipline

Decision 082 §11.3's accepted rule stands: verified evidence uses **new** evidence-specific hash
domains. Every digest continues to go through
`src/disclosure_drift/release/hashing.py`; **no second hash implementation is introduced.**

* **No existing frozen column tuple is widened.** `ACCESSION_TABLE_COLUMNS`,
  `REGISTRANT_TABLE_COLUMNS`, and `SNAPSHOT_CONTENT_FIELDS` are untouched, exactly as accepted
  Decision 084 §4 (**R67**) requires.
* **No historical synthetic identity is altered.**
* **Candidate identity does not change merely because migration `0015` exists.**

**Required proof.** A database upgraded from `0014` to an **empty** `0015` evidence state must preserve
every pre-existing candidate and selection identity output, **except** the already-accepted
migration-chain policy binding where it applies. Any identity movement caused **solely** by the
migration chain must be enumerated explicitly and distinguished from evidence-content movement.

**The expected, accepted migration-chain movement.** Decision 086 §3 (**R68**) already classified this
exact path as an *expected governed policy-binding consequence*:

```text
migration checksum -> migration_chain_sha256 -> selector_policy_sha256
                   -> root_manifest_sha256 / manifest_id
```

Migration `0015` adds one row to `ops_schema_migrations`, so the reserve-bearing manifest fixture's
`selector_policy_sha256`, `root_manifest_sha256`, and `manifest_id` move, and the canonical manifest
document's block 5 gains one migration row. **Nothing else may move.** In particular
`candidate_tables_sha256`, `selection_result_sha256`, `source_observation_set_sha256`,
`quota_definitions_sha256`, `selected_entities_sha256`, `selected_accessions_sha256`, `reserves_sha256`,
and `quota_report_sha256` must all be **byte-identical**, and anything else that moves must be reported.

**If implementation requires widening an owner-frozen candidate identity tuple: STOP.**

Future **real** candidate identities may change by their **values** when verified purpose or linkage
evidence is later populated into already-governed candidate fields. That is the unavoidable
Decision 082 §11.3 content change, and it is a different thing from changing the identity schema.

## 10. No document review execution

This stage builds **infrastructure only**. It does **not** perform Review A, Review B, document
adjudication, purpose classification, linkage adjudication, or witness counting from real Decision-081
documents. **The 108 real Decision-081 review outcomes are not inserted, and the private Decision-081
evidence artifacts are not accessed.**

The future protocol, accepted by Decision 083 §9 (**R64**) and still **EXECUTION DEFERRED**, remains:

| Stage | Model | Effort | Epoch |
|---|---|---|---|
| **Review A** | Claude Opus 5 | maximum | fresh |
| **Review B** | Claude Fable 5 | maximum | a different fresh epoch |
| **Adjudication** | Claude Opus 5 | maximum | a third fresh epoch |

over **all 108** frozen Decision-081 artifacts, with **zero** new SEC requests.

## 11. No network, and no real E0

No SEC access, no HTTP, no network, no real **E0**, no mutation of the accepted private M3.2 catalog,
and no Decision-081 private-root access. Every migration and schema test runs against **test,
disposable, or accepted migration-test machinery** only.

## 12. Migration `0015` safety

Migration `0015` must be **prospective**, **non-destructive**, compatible with an empty
verified-evidence state, and safe on a disposable catalog migrated through `0014`. Required checks:

| # | Check |
|---|---|
| 1 | `0014` → `0015` upgrade succeeds on lawful empty-evidence state |
| 2 | A fresh build through `0015` succeeds |
| 3 | Fresh-build schema and upgrade schema are equivalent where required |
| 4 | `PRAGMA foreign_key_check` is clean |
| 5 | `PRAGMA integrity_check` is clean |
| 6 | Migration provenance/checksum recognizes the final bytes |
| 7 | `0015` cannot silently mutate historical accepted evidence |

**Any migration requirement to reinterpret accepted real evidence is a STOP.**

## 13. Authorized implementation paths

The implementation uses the paths Decision 082 §11 and Decision 083 §8 (**R63**) explicitly authorize
or necessarily imply. **Decision 082 §11 states no exact path list** — unlike §10.14, which does for
R46 — so the list below is this record's, bounded to what the accepted contract requires:

```text
src/disclosure_drift/storage/migrations/0015_m33_verified_document_evidence.sql   (new)
src/disclosure_drift/m3/document_evidence.py                                      (new)
src/disclosure_drift/m3/__init__.py            (re-export only)
src/disclosure_drift/m3/acquisition.py         (FINAL_MIGRATION_VERSION only)
tests/unit/test_m3_3_verified_document_evidence.py                                (new)
tests/unit/test_migration_provenance.py        (chain-head expectations)
tests/unit/test_storage_catalog.py             (chain-head expectations)
tests/unit/test_m3_3_multi_registrant_correction.py   (chain-head expectations)
tests/unit/test_m23_pilot_manifest_store.py    (the section 9 migration-chain re-baseline)
Docs/sec_data_dictionary.md
Docs/architecture_map.md
Docs/change_impact_map.md
Docs/decision_index.md
Docs/Decisions/decision_registry.md
Milestones/STATUS.md
```

`FINAL_MIGRATION_VERSION` in `src/disclosure_drift/m3/acquisition.py` moves **14 → 15** — **that
constant and nothing else in that file**. This is the exact, already-adjudicated situation of accepted
Decision 084 §2 (**R65**): the constant records the repository's schema-chain head, migration `0015`
moves that head, and without the constant every freshly prepared **disposable** catalog would refuse
itself. On the same owner interpretation as R65, it does **not** reopen M3.2, authorize acquisition,
authorize network access, authorize applying `0015` to the accepted private M3.2 operational catalog,
authorize writing accepted M3.2 evidence, move `m3.2-complete`, or grant **M3.3-E0**.

**Explicitly prohibited paths for this stage**, listed so the boundary is never inferred:
`src/disclosure_drift/cohorts.py`; `src/disclosure_drift/pilot_policy.py`; migrations `0001`–`0014`;
`Docs/preregistration.md`; every existing record in `Docs/Decisions/`; every network, acquisition, and
transport module; the R46 implementation; the Decision-081 private verification evidence; the accepted
M3.2 evidence root; candidate-selection methodology; document-classification logic; real review
execution; and **E0** execution.

**If implementation proves that an additional executable path outside the accepted contract is
technically required: STOP** and return to Sol/GPT with the minimal proposed expansion.

## 14. Required adversarial tests — VE-M1 … VE-M14

An explicit adversarial test matrix is required for the verified-evidence schema. **Effectiveness must
be demonstrated, not named.** Each mutation is applied and the exact condition that kills it is
asserted.

| # | The mutation that must be rejected |
|---|---|
| **VE-M1** | Absolute private `EV_ROOT` path persistence |
| **VE-M2** | Artifact SHA mutation after governed review binding |
| **VE-M3** | Review-record role or epoch mutation after freeze |
| **VE-M4** | Source span rewritten after a frozen review |
| **VE-M5** | Adjudicated evidence rewritten after finalization |
| **VE-M6** | `verified` evidence on an unauthorized dimension |
| **VE-M7** | An invented `verified_amends_original` semantic state |
| **VE-M8** | Adjudication lacking bound artifact provenance |
| **VE-M9** | Adjudication lacking review provenance |
| **VE-M10** | Review A and Review B sharing one governed epoch identifier |
| **VE-M11** | Artifact substitution under the same governed review identity |
| **VE-M12** | Candidate identity tuple widening, or unrelated identity movement, merely from empty `0015` evidence tables |
| **VE-M13** | Private-path leakage into governed rows or completion output |
| **VE-M14** | Real Decision-081 artifact or reference access during this infrastructure-only stage |

Where Decision 082's requirements are more specific, those exact requirements control.

## 15. Stop conditions

The session **STOPS** and returns to Sol/GPT if:

| # | Condition |
|---|---|
| **A** | Implementation requires widening an existing owner-frozen candidate identity tuple |
| **B** | Verified evidence cannot be restricted to amendment purpose and linkage in M3.3 v1 |
| **C** | Actual Complete Submission Text bytes must be stored in SQLite for the design to work |
| **D** | A private absolute filesystem path must become governed data |
| **E** | Review A, Review B, or adjudication must execute to implement the schema |
| **F** | Real Decision-081 evidence must be accessed |
| **G** | Network, SEC, or HTTP access becomes necessary |
| **H** | Real **E0** state must be created |
| **I** | Migration `0015` requires reinterpretation or destruction of accepted real state |
| **J** | The four-relation contract proves incomplete in a way that requires new methodology |
| **K** | A BLOCKER or MAJOR remains unresolved |

**A stop condition is never worked around.**

## 16. What is unchanged

No research definition, hypothesis, threshold, cohort window, outcome, or seed. No quota value, no
quota domain, and no selector policy. No candidate-selection methodology, offline-parsing behaviour,
selection store, or reserve selector. `snapshot_id`, `entity_tie_break_sha256`, the **R15** evidence
preimage, and the **R16** resolution preimage are unaffected. `cohorts.py` and `pilot_policy.py` are
untouched. Migrations `0001`–`0014` are byte-unchanged. The preregistration is untouched, every
accepted review artifact remains immutable, `m3.2-complete` is unmoved, and tracked network switches
remain `false` / `false`.

Decisions 079–086 are **not rewritten**, and Decision 081 is **not rerun**. Both real-path feasibility
gates — `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
`M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` — remain **OPEN** and are never merged into one
flag. `REAL_ACCEPTANCE_ORDERING_ADEQUACY` remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION**.

## 17. What this record does not authorize

It does **not**: execute Review A, Review B, or the adjudication; classify any real filing; populate any
real Decision-081 evidence; access the Decision-081 private evidence artifacts; resolve any real
amendment parentage; grant any quota credit; close either real-path feasibility gate; resolve real
acceptance-ordering adequacy; authorize the real durable offline parse (**M3.3-E0**) or progression to
**M3.3-E1** or **M3.3-E2**; authorize a real snapshot, selection, manifest, or root; approve a root or
begin **M3.4**; make any network, SEC, or HTTP request; authorize any acquisition, reacquisition, or
enrichment; write to the accepted M3.2 private evidence, the accepted real private catalog, or any
accepted catalog; write any migration other than `0015`; reverse Decision 071's **IN-2**; lower, defer,
or proxy any quota; move `m3.2-complete`; or create any tag.

**Successful implementation is not acceptance.** Migration `0015` and its infrastructure must receive a
**fresh independent review** *and* **Sol/GPT owner acceptance** before real document-review execution
begins.

## 18. Next authorized action

**Implement migration `0015` and the authorized verified-evidence infrastructure under §13, then return
to Sol/GPT.** The implementing session does **not** self-review, does **not** start Review A, Review B,
or the adjudication, and does **not** start **E0**.

```text
M3_3_D085_R46_CORRECTED_IMPLEMENTATION_OWNER_ACCEPTED
M3_3_R49_CONDITION_B_SATISFIED
M3_3_PRE_E0_MULTI_REGISTRANT_HOLD_CLOSED
VERIFIED_EVIDENCE_SCHEMA_CONTRACT = OWNER ACCEPTED / IMPLEMENTATION AUTHORIZED
FUTURE_ADJUDICATION_PROTOCOL_CONTRACT = OWNER ACCEPTED / EXECUTION DEFERRED
MIGRATION_AUTHORIZED = 0015 only
M3_3_E0_AUTHORIZATION = NO
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY = PENDING FUTURE AUTHORIZED E0 VERIFICATION
```
