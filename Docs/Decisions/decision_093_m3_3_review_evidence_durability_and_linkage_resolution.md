# Decision 093 — D091 Review-Evidence Durability and the Pre-E0 Linkage-Resolution Ruling

```text
STATUS: ACCEPTED — OWNER D091 REVIEW-EVIDENCE DURABILITY CLOSURE AND PRE-E0 LINKAGE-RESOLUTION RULING
DATE: 2026-08-15
OWNER: Sol/GPT
OUTCOME: M3_3_DECISION_093_D091_EVIDENCE_DURABLE_E0_READY
M3_3_D091_REVIEW_EVIDENCE_DURABILITY_HOLD_CLOSED: YES
M3_3_R52_LINKAGE_RESOLVER_USES_ASSOCIATION_SET_PLUS_STATED_FILING_DATE: YES
E0_ORIGINAL_ACCEPTANCE_TIMESTAMP_SOURCE: UNAVAILABLE
M3_3_E0_OWNER_AUTHORIZED: UNCHANGED — remains authorized and is now executable in a new session
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
MIGRATION_AUTHORIZED: NONE
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

**This record does three things.** It closes the durability gap that made the accepted D091 review
evidence unreproducible from the repository; it fixes the exact linkage-resolution predicate
prospectively, before E0 runs; and it records two read-only E0 preflight findings.

**It executes nothing.** No document is re-reviewed, no judgment changes, no schema byte changes, E0
is **not** started, and no network, SEC, or HTTP request is made.

---

## 1. Entry state — verified

| Fact | Value |
|---|---|
| Branch | `main`, `HEAD` == `origin/main` |
| `HEAD` | `632477923e498a3da7cd01379d7e4d319d1a0ecb` — the Decision 092 authority commit |
| Tree | `e27f0dec2822031394092a583f393ec2f69573dd` |
| Parent | `9855ceeeebc6bfd1f0e3bc7de98a7a719cc205e9` — the D091 evidence-publication commit |
| Accepted Review-A digest | `d9c9d9c79a75d7808e09094fdafa189128ae522d884bb88c8fb28f0e40d89c4f` |
| Accepted artifact-table digest | `b84495a40b23fdc77c70c537b8cf6c9bd7675b90493fc73d55841a2ac425174e` |
| Frozen counts | artifacts 108, review records 108, spans 302, adjudicated 0 |
| `m3.2-complete` | `2865a1479e4576dc18a4098c928b278812f38d00`, unmoved |
| Working tree | CLEAN |
| Migrations | `0001`–`0015` contiguous; `0016` ABSENT |

Verified read-only by Git; no fetch, pull, reset, clean, or stash.

## 2. Decision 092 remains accepted

Unchanged and not reopened:

```text
M3_3_DECISION_091_SINGLE_OPUS_EVIDENCE_REVIEW_OWNER_ACCEPTED
M3_3_REVIEW_A_DIGEST_D9C9D9C7_OWNER_ACCEPTED
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_CLOSED
M3_3_E0_OWNER_AUTHORIZED
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN_PENDING_E0_R52_RESOLUTION
```

**Decision 093 does not revoke E0 authority.** It placed a pre-execution durability hold on
*consuming* that authority until the accepted evidence could be reproduced from durable state. §7
closes that hold.

## 3. The durability gap — accepted as a fact, not a defect

The committed prose review artifact carries all 108 rows and 123 of the 302 span locations, which is
**not enough machine-readable state to independently reconstruct the accepted Review-A rows and
reproduce the accepted digests**. The complete frozen state existed only in the execution epoch's
built catalog and judgment export.

This is **not** a judgment defect, **not** a digest defect, and **not** a reopening of the D091
review. It is a **durability / reproducibility gap**, and it was closed before E0/R52 consumes the
evidence.

```text
M3_3_D091_REVIEW_EVIDENCE_DURABILITY_HOLD_OPEN   (opened and closed by this record)
```

## 4. The canonical durable export

Created under the authorized directory
[`Docs/m3/evidence/d091_review_a_d9c9d9c7/`](../m3/evidence/d091_review_a_d9c9d9c7/):

| File | Rows | Bytes | SHA-256 |
|---|---:|---:|---|
| [`document_artifacts.jsonl`](../m3/evidence/d091_review_a_d9c9d9c7/document_artifacts.jsonl) | 108 | 45,056 | `0fdd6d022cbaf53807fb950d8b3aba15c6274dc6945aa864faec87ad34a05291` |
| [`document_review_records.jsonl`](../m3/evidence/d091_review_a_d9c9d9c7/document_review_records.jsonl) | 108 | 80,106 | `f66135b0bcf16e69c589db1744eeca1f2272552e7527070e86b1e82ef4dbd007` |
| [`document_review_spans.jsonl`](../m3/evidence/d091_review_a_d9c9d9c7/document_review_spans.jsonl) | 302 | 128,014 | `18b8fc6b7b2e4c728c2f0566a3092d5fe4b377a7784bb0de5412be3727dba5da` |
| [`manifest.json`](../m3/evidence/d091_review_a_d9c9d9c7/manifest.json) | — | 3,015 | `599d9ff067a8bde721ded1d28a417c4356e877215660ef9595d257abbdfe9ae3` |

**This is an export of already-frozen accepted state.** No document was re-reviewed and no judgment,
category, abstention, asserted form, asserted date, source span, span text, or `review_epoch_id`
changed. No replacement review row was minted, and no Review-B or adjudication row was created.

**Canonicalization.** Deterministic UTF-8 JSON Lines; one logical row per line; newline-terminated;
`json.dumps(obj, ensure_ascii=False, separators=(',',':'))` with no spaces and no ASCII escaping;
field order is migration `0015`'s own column order per relation, preserved as JSON key order; row
order is each relation's declared UNIQUE business key — `document_artifacts` by
`(accession_plain, source_class)`, `document_review_records` by `(accession_plain, reviewer_role)`,
`document_review_spans` by the parent record's `accession_plain` then `span_ordinal`. Values are the
exact persisted governed values: `NULL` renders as JSON `null` and INTEGER columns render as JSON
numbers. **No value was invented and no timestamp was generated for the export.**

**Boundary.** The export carries only the governed span-level verbatim evidence needed to reproduce
`document_review_spans`. It contains no Complete Submission Text body, no absolute path, no
evidence-root name, no scratch or temporary path, no raw session identifier, and no personal
reviewer name — each mechanically asserted in §5 below. No D081 artifact or receipt was altered.

## 5. Reproducibility proof

From **only** the four exported files plus the accepted repository hashing implementation
(`disclosure_drift.m3.document_evidence`, itself over `release/hashing.py`), with the built catalog
deliberately not opened, **27 checks pass**:

```text
ARTIFACT_TABLE_SHA256 = b84495a40b23fdc77c70c537b8cf6c9bd7675b90493fc73d55841a2ac425174e   REPRODUCED
REVIEW_A_TABLE_SHA256 = d9c9d9c79a75d7808e09094fdafa189128ae522d884bb88c8fb28f0e40d89c4f   REPRODUCED
artifact rows 108   review rows 108   span rows 302   Review-B rows 0   adjudicated rows 0
```

Also reproduced from the export alone: every `review_record_sha256`; every `span_sha256`; every
`review_id` from `sha256(review_epoch_id | accession_plain)`. Also re-verified: no cross-accession
artifact binding; every span has a parent record; a single review epoch; the protocol version pinned
on every row; every span supports an assertion its record makes; every positive assertion carries its
span; abstained records assert nothing; the manifest's file digests match the files; and the accepted
content counts recompute exactly — purpose 99 asserted / 9 abstained, and original form 102, date 96,
accession 0, form+date 96.

## 6. Owner ruling — the linkage-resolution predicate

The R48 / R52 date-field ambiguity is resolved **prospectively, before E0**.

```text
M3_3_R52_LINKAGE_RESOLVER_USES_ASSOCIATION_SET_PLUS_STATED_FILING_DATE
```

**Input assertion set.** Exactly the **96** owner-accepted Review-A records carrying **both** an
accepted original form and an issuer-stated original filing date. The **6** form-only partial records
remain in the reconciliation waterfall as `NO_DATE / INELIGIBLE_FOR_LINKAGE_RESOLUTION`, receive **no**
linkage credit, and sit **outside the 96-match denominator**.

**A — registrant scope.** Use the **complete established amendment registrant association set**,
unioning over `pilot_candidate_accession_registrants` or the exact accepted relational successor.
**The nullable `anchor_cik_numeric` is never the registrant scope for a multi-registrant accession.**
Where `registrant_set_completeness` is unestablished, fail closed and report
`UNESTABLISHED_ASSOCIATION_SET`.

**B — form predicate.** The candidate original must be an **original** compatible annual filing whose
form **exactly** matches the owner-accepted asserted original form: `10-K` or `10-KT`. Not `10-K/A`,
not `10-KT/A`, not `10-KSB`. **No fuzzy form inference.**

**C — date predicate.** The candidate original's **`filing_date` must exactly equal the
issuer-stated `original_filing_date`** accepted from the D091 review. **This filing-date predicate is
controlling for this stage. `report_date` is NOT the linkage matching field** — it may be reported
diagnostically but may **not** create or destroy a match.

**D — set operation.** For every substantive registrant in the complete association set, collect all
E0 original rows satisfying **B + C**; **UNION**; **dedupe by canonical original accession**; then
classify the assertion as `ZERO`, `EXACTLY_ONE`, `MULTIPLE`, or `UNESTABLISHED_ASSOCIATION_SET`.

This combined rule is the **controlling M3.3 association-set linkage resolver**.

## 7. Acceptance ordering

For an `EXACTLY_ONE` resolved original, evaluate strict temporal ordering **separately**, using the
accepted native acceptance-timestamp authority (Decision 080 **R43**):

| Condition | State |
|---|---|
| original acceptance **<** amendment acceptance | `ORDERING_PASS` |
| original acceptance **>=** amendment acceptance | `ORDERING_FAIL` |
| either accepted native timestamp unavailable | `ORDERING_UNAVAILABLE` |

`filing_date`, `report_date`, retrieval time, filesystem time, and row-insertion time are **never**
substituted. An `ORDERING_UNAVAILABLE` case keeps its `EXACTLY_ONE` identity resolution but **cannot
receive final linkage or quota credit** until owner disposition. **Missing ordering evidence is never
treated as `ORDERING_PASS`.**

## 8. E0 source-adequacy preflight — read-only finding

```text
E0_ORIGINAL_ACCEPTANCE_TIMESTAMP_SOURCE = UNAVAILABLE
```

E0 **is not blocked** by this finding.

Read-only inspection of the accepted E0 contract and the reusable parser establishes the precise
position. `census_accessions` carries `acceptance_datetime_sec_raw` and `acceptance_date_sec`, and
the accepted parser populates them from the **entity-submissions `acceptanceDateTime`** field. Under
Decision 080 **R43** that is the **lower-authority** observation: the native accession-level
`<ACCEPTANCE-DATETIME>` EDGAR header is the intended higher authority, submissions values "never
override the native accession-level header," and R43 additionally **prohibits** the four remedies
(14-digit truncation of submissions values, timezone arithmetic, choosing among duplicates,
registrant-based precedence) that the Decision-079 **MAJOR-1/MAJOR-2** source findings would
otherwise invite.

**For the ORIGINAL candidate filings the native header is not present in any accepted stored M3.2
source object.** The only accepted stored artifacts carrying a validated native
`<ACCEPTANCE-DATETIME>` are the **108 D081 Complete Submission Text artifacts**, and those are the
**amendments**, not their originals. Acquiring originals' headers would require new SEC retrieval,
and network, SEC, and HTTP authority is **NONE** at `REQUEST_CEILING = 0`.

Consequently `REAL_ACCEPTANCE_ORDERING_ADEQUACY` **remains PENDING after E0**, and the §7 ordering
state for resolved originals is expected to be `ORDERING_UNAVAILABLE` unless a later owner authority
activates the level-1 `filing_level_metadata` class R43 describes as "defined and deliberately
deferred" — which R43 notes is a data change plus the bounded source-registration the resolver
requires, not a policy change. **This record does not grant that authority.**

## 9. E0 durable output path preflight — read-only finding

The accepted authority **does** name the durable locations with sufficient exactness. No path is
invented by this record.

| Output | Governed location | Authority |
|---|---|---|
| E0 catalog state | `<accepted private evidence root>/catalogs/m3_2a_operational.sqlite3` | `OPERATIONAL_CATALOG_RELATIVE_PATH`, a `Final` constant in accepted source `src/disclosure_drift/m3/acquisition.py`; the contract's "accepted real private catalog" |
| E0 write footprint inside it | **exactly** the fifteen tables of the M3.3 contract §10.2 item 2 plus the `census_plan_sources.parser_state` transition for category-A sources | contract **R17** (Decision 068 §3) |
| E0 receipt | `<accepted private evidence root>/runs/<E0 namespace>/execution_receipt.json` | `OPERATOR_RECEIPT_FILENAME`, a `Final` constant in accepted source `src/disclosure_drift/m3/receipt.py`; the accepted execution-receipt spec's operator-selected, create-once `runs/<namespace>/execution_receipt.json` pattern in the owner-controlled private evidence root |

**The receipt namespace is operator-selected by accepted design, not by omission** — the receipt spec
states receipts are "operator-selected, create-once," never overwritten, and **addressed by recorded
identity rather than by an assumed path**. No separate private real-state database or export is
required by E0 beyond these.

**Recommendation carried to the E0 packet, not a ruling:** the E0 execution packet should name its
run namespace explicitly rather than leaving the executor to choose it, on the same reasoning that
produced this record's durability gap.

## 10. E0 execution invariants — mandatory for the later E0 packet

| # | Invariant |
|---|---|
| **1** | **Python.** Use the project Python 3.12 environment, specifically the accepted `.venv` interpreter where available. **Do not use system `python3` where it resolves to Python 3.9** — the package fails to import there |
| **2** | **SQLite.** `storage.sqlite.connect()` is a **context manager**; use it through its accepted context-manager API, never as a bare connection |
| **3** | **Private root.** Resolve the accepted private root **once per process** and cache the resolved reference. **Do not recursively `rglob` all of `$HOME`** |
| **4** | **Validation order.** compute → validate → **independently recompute every identity and digest from the persisted rows** → verify foreign keys, integrity, and content bindings → **then** freeze. **Never freeze before identity validation** |
| **5** | **Self-reference rule.** **No** persisted digest, identifier, seal, or content address may be computed from a preimage containing that same field's own value |
| **6** | **Private-path validation.** Apply the accepted **per-column** schema and shape rules. **Do not blindly apply `require_no_private_path`** to text columns whose accepted syntax legitimately contains `/` or `:`. **Do not weaken nonleakage checks to suppress false positives** |

## 11. Durability-hold closure

§5 reproduced **both** accepted D091 digests exactly from the committed durable exports alone.
Therefore:

```text
M3_3_D091_REVIEW_EVIDENCE_DURABILITY_HOLD_CLOSED
```

**M3.3-E0 remains OWNER AUTHORIZED and is executable in a NEW session.**

## 12. What is unchanged

No research definition, hypothesis, threshold, cohort window, outcome, or seed. No source, test,
migration, script, or configuration byte. No frozen evidence row, no accepted digest, no review
artifact. Migrations remain `0001`–`0015` with `0016` absent, tracked network switches remain
`false` / `false`, `m3.2-complete` is unmoved, and no tag is created. Historical Decisions 001–092
are **not rewritten**.

## 13. What this record does not authorize

It does **not**: start E0; authorize **M3.3-E1**, **M3.3-E2**, or **M3.4**; broaden E0 methodology or
scope; authorize any network, SEC, or HTTP request; authorize migration `0016` or any migration;
modify migration `0015`; activate the level-1 `filing_level_metadata` native-header source class;
persist final verified linkage evidence; grant linkage quota credit; close the linked-amendment
feasibility gate; re-review any document; change any frozen judgment; move `m3.2-complete`; or create
any tag.

## 14. Next authorized action

**Return to Sol/GPT.** M3.3-E0 runs in a **new session** under its accepted frozen scope and the §10
invariants, followed by the read-only linkage resolution of §6–§7 returned to the owner.

```text
M3_3_DECISION_093_D091_EVIDENCE_DURABLE_E0_READY
M3_3_D091_REVIEW_EVIDENCE_DURABILITY_HOLD_CLOSED
M3_3_R52_LINKAGE_RESOLVER_USES_ASSOCIATION_SET_PLUS_STATED_FILING_DATE
E0_ORIGINAL_ACCEPTANCE_TIMESTAMP_SOURCE = UNAVAILABLE
REAL_ACCEPTANCE_ORDERING_ADEQUACY = REMAINS PENDING AFTER E0
M3_3_E0_OWNER_AUTHORIZED = UNCHANGED, EXECUTABLE IN A NEW SESSION
E1 / E2 / M3.4 = NOT AUTHORIZED
MIGRATION_AUTHORIZED = NONE; MIGRATION 0016 = NO
NETWORK / SEC / HTTP = NONE; REQUEST_CEILING = 0
```
