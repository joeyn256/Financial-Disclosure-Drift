# Decision 083 — Pre-E0 Multi-Registrant Relational Correction: Owner Acceptance and Implementation Authorization

```text
STATUS: ACCEPTED — OWNER ACCEPTANCE OF THE DECISION-082 CONTRACTS AND R46 IMPLEMENTATION AUTHORIZATION
DATE: 2026-08-14
OWNER: Sol/GPT
OUTCOME: M3_3_DECISION_082_PRE_E0_CONTRACTS_OWNER_ACCEPTED
IMPLEMENTATION_AUTHORIZATION: R46 MULTI-REGISTRANT RELATIONAL CORRECTION ONLY — MIGRATION 0014 ONLY
R46_MULTI_REGISTRANT_IMPLEMENTATION_CONTRACT: OWNER ACCEPTED / IMPLEMENTATION AUTHORIZED
VERIFIED_EVIDENCE_SCHEMA_CONTRACT: OWNER ACCEPTED / IMPLEMENTATION DEFERRED
FUTURE_ADJUDICATION_PROTOCOL_CONTRACT: OWNER ACCEPTED / EXECUTION DEFERRED
M3_3_E0_DURABLE_PARSE_AUTHORIZATION: NO
E0_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: 0014 only
MIGRATION_0015_AUTHORIZATION: NO
REVIEW_A_AUTHORIZATION: NO
REVIEW_B_AUTHORIZATION: NO
DOCUMENT_ADJUDICATION_AUTHORIZATION: NO
REQUEST_CEILING: 0
```

**This record does three things and nothing else.** It records Sol/GPT's owner acceptance of the
three contracts [Decision 082](decision_082_m3_3_d081_owner_adjudication_and_pre_e0_contracts.md)
returned as `PENDING OWNER ACCEPTANCE` (§2); it freezes seven owner rulings — **R58** (§3), **R59**
(§4), **R60** (§5), **R61** (§6), **R62** (§7), **R63** (§8), **R64** (§9) — which adjudicate every
open item those contracts left open; and it authorizes **exactly one** bounded implementation: the
**R46** multi-registrant relational correction and migration `0014` (§10).

**It authorizes nothing else.** Migration `0015`, the verified-evidence schema, Review A, Review B,
the document adjudication, **M3.3-E0**, **M3.3-E1**, **M3.3-E2**, and **M3.4** all remain
unauthorized. Network, SEC, and HTTP authority remains **NONE** at `REQUEST_CEILING = 0`.

**Where this record and an earlier governing record disagree**, it controls only on the points it
names. Decisions 001–082 remain accepted and byte-unchanged, and no historical evidence artifact is
rewritten.

---

## 1. Entry state — verified

Verified live by `scripts/verify_target.py` plus direct Git corroboration, with no fetch, pull,
reset, clean, or stash.

| Fact | Value |
|---|---|
| Branch | `main` |
| `HEAD` == `origin/main` | `5231359fcce3764257dcc54d29c151b1021e51d6` |
| Tree | `59b603a723ac1aa365504c8a789d6f3370c4ac2f` |
| Parent | `8b61a068d916c5b59b02c634a24244c5b0f8e661` |
| `m3.2-complete` annotated tag object | `2865a1479e4576dc18a4098c928b278812f38d00` |
| Working tree | clean |
| Migrations | `0001`–`0013` only |

## 2. Decision 082 — owner accepted

```text
M3_3_DECISION_082_PRE_E0_CONTRACTS_OWNER_ACCEPTED
```

The already-pushed Decision-082 governance commit `5231359f…` is accepted as the **sole** Decision-082
execution. It is not rerun, replaced, rolled back, or duplicated, and the prior duplicate-delivery
condition is **CLOSED**.

The three contract statuses become:

```text
R46_MULTI_REGISTRANT_IMPLEMENTATION_CONTRACT = OWNER ACCEPTED / IMPLEMENTATION AUTHORIZED
VERIFIED_EVIDENCE_SCHEMA_CONTRACT            = OWNER ACCEPTED / IMPLEMENTATION DEFERRED
FUTURE_ADJUDICATION_PROTOCOL_CONTRACT        = OWNER ACCEPTED / EXECUTION DEFERRED
```

Only the **R46** implementation is authorized (§10). Accepting a contract is not executing it.

## 3. Ruling R58 — the canonical multi-registrant representation

**Decision 082 §10.15 item 1 is adjudicated: the new relation is adopted.** A new census-layer
relation `census_accession_registrants` is created as the canonical relation between an accession and
**all** substantive registrants established for that accession. **The relation, not a scalar CIK, is
authoritative** for a genuinely multi-registrant accession.

For an accession whose substantive registrant set is **established**:

| Cardinality | Scalar registrant field |
|---|---|
| exactly 1 | may carry that canonical CIK |
| more than 1 | **`NULL`** — no arbitrary primary CIK exists |

**No anchor may be chosen** by first write, last write, minimum CIK, maximum CIK, archive order,
record order, hash order, a submissions occurrence, full-index row order, the submitter, a filing
agent, a transport URL, or a filename. The accession remains an accession-level identity.

## 4. Ruling R59 — completeness and candidacy

**Decision 082 §10.15 item 5 is adjudicated.** The implementation distinguishes at least
`established` and `unestablished` registrant-set completeness. An `established` set means the
accepted source architecture has established the **complete** substantive registrant association set
under the accepted rules. **`unestablished` must never be read as evidence of a sole registrant.**

```text
registrant_set_completeness = unestablished  BLOCKS ACCESSION CANDIDACY ENTIRELY
```

It does not merely block filling the scalar anchor. Candidate identity, history attribution,
multi-registrant status, and quota semantics all depend on the complete substantive association set,
so an incomplete set must never enter a candidate snapshot and become a later identity problem. The
block **fails closed with an explicit accepted reason**.

## 5. Ruling R60 — the non-CIK sentinel

**Decision 082 §10.15 item 2 is adjudicated: option H-a is adopted**, with this clarification.

The **persisted** representation for an established multi-registrant accession is
`registrant_cik_numeric = NULL`. The deterministic accession tie-break serializer may use the exact
domain-separated sentinel

```text
MULTI_REGISTRANT_NO_SINGLETON
```

**only** where the preimage required one registrant slot and the accession has an **established**
registrant set of cardinality > 1. This string is **not a CIK**: it is never parsed as one, never
persisted in a CIK column, never presented as an entity, never counted toward any entity or quota,
and never a transport locator.

For an **established single-registrant** accession the preimage remains the canonical CIK exactly as
before. For an **unestablished** set no fake value is hashed at all — the accession is ineligible for
candidacy under **R59**.

**Required protection:** every existing single-registrant tie-break preimage must remain
byte-for-byte identical. Known multi-registrant synthetic identities may change prospectively and
must be **explicitly re-baselined, never silently changed**.

## 6. Ruling R61 — manifest and identity semantics

**Decision 082 §10.15 item 3 is adjudicated.** [Decision 021](decision_021_m23_s6_manifest_construction.md)
is **not rewritten**, and no historical accepted manifest rule is altered. Prospectively for M3.3 real
state, Decision 021 manifest **item 48 "anchor CIK"** is interpreted as:

- the single factual registrant CIK when the established substantive set has cardinality exactly 1;
- **`NULL`** when the established substantive set has cardinality > 1.

For multi-registrant accessions the governed **relational registrant set is authoritative**, and
`candidate_registrant_table_sha256` must bind that relation under the accepted candidate identity
architecture. **No fabricated replacement anchor is added.**

The five affected identity consumers Decision 082 §10.6 named are accepted as **prospectively
changeable before real E0**:

```text
E1  accession_tie_break_sha256
E2  candidate_accession_table_sha256
E3  candidate_registrant_table_sha256
E4  candidate_snapshot_sha256
E5  selection_input_sha256 -> selection_run_id -> manifest components -> manifest root
```

Explicitly preserved as **unaffected** unless implementation proves otherwise: `snapshot_id`,
`entity_tie_break_sha256`, the **R15** `evidence_sha256` preimage, and the **R16** `resolution_sha256`
preimage. **If implementation proves this five-item inventory incomplete, the session STOPS and
returns to Sol/GPT.** The identity impact is never silently widened.

## 7. Ruling R62 — history and event attribution

**Decision 082 §10.15 item 4 is adjudicated: every substantive registrant.** For an **established**
multi-registrant accession the accession participates in the filing history of **every** substantive
registrant associated with it. It is attributed neither to only one CIK nor to none.

However:

- **Accession-domain** calculations continue to deduplicate by canonical accession identity — one
  joint filing remains one filing.
- Where a metric or quota is explicitly **entity-domain**, each truthful substantive entity may
  participate according to that metric's **existing** definition.
- **No existing quota changes its declared domain** merely because the association representation
  changed.

[Decision 072](decision_072_m3_3_full_index_multi_registrant_source_correction.md)'s multi-registrant
quota is unchanged: the hard multi-registrant quota remains **2**, and its accession-keyed witness
requires no arbitrary anchor.

## 8. Ruling R63 — verified-evidence schema contract acceptance

Decision 082 §11 is accepted, and its four open items (§11.5) are adjudicated below. **Migration
`0015` is NOT implemented in this stage** and remains ordered **after** `0014`.

| Item | Owner disposition |
|---|---|
| **A. `document_artifacts`** | A **catalog metadata relation**. The Complete Submission Text bytes stay in the private external evidence root; the relation stores only governed metadata and provenance needed to bind the artifact, including its SHA-256 and public source identity. **No absolute private filesystem path is persisted.** A content-addressed or private-object locator may be used only if technically required, and must not expose `EV_ROOT` |
| **B. verified linkage state** | **Reuse** `amendment_linkage_state = 'amends_original'` when the relationship is established. Verification strength belongs in `evidence_level = 'verified'` and its document/adjudication provenance. **No second semantic state** such as `verified_amends_original` is invented |
| **C. verified applicability** | For M3.3 v1, `verified` is authorized **only** for amendment purpose and amendment linkage / explicit-original evidence. It is **not** silently enabled for size, industry, history, universe, cohort, XBRL, control predicates, or any other dimension. The future migration and policy validation must **enforce** that applicability |
| **D. reviewer identity** | Persist durable **opaque review-epoch identifiers** plus reviewer role and model. **No personal name** is persisted, and raw Claude session IDs are **not** required in the governed evidence row. The evidence package must mechanically distinguish Review A, Review B, and adjudication epochs |

```text
VERIFIED_EVIDENCE_SCHEMA_CONTRACT = OWNER ACCEPTED / IMPLEMENTATION DEFERRED
MIGRATION_0015_AUTHORIZATION      = NO
```

## 9. Ruling R64 — document adjudication protocol acceptance

Decision 082 §12 is accepted, and its open items (§12.9) are adjudicated below.

```text
PROTOCOL_VERSION: m3.3-document-evidence/1.0
```

**Artifact population: all 108 frozen D081 Complete Submission Text artifacts.** No deterministic
subset, and **no further SEC request**.

Sequential independence, each in its own fresh `/clear` epoch:

| Stage | Model | Effort | Visibility |
|---|---|---|---|
| **Review A** | Claude Opus 5 | maximum | blind to Review B and to the adjudication output |
| **Review B** | Claude Fable 5 | maximum | blind to Review A and to the adjudication output |
| **Adjudication** | Claude Opus 5 | maximum | may see frozen A + B only after **both** are complete and hash-frozen; may resolve only the protocol's defined disagreement states |

The same human operator may launch all three: **the independence unit is the fresh review epoch plus
the frozen-input boundary**, not the operator. No parallel session is required or authorized.

**Conflict terminality.** If final adjudication cannot resolve a conflict under
`m3.3-document-evidence/1.0` using the frozen artifact set, that outcome is **TERMINAL** for that
protocol version and artifact set. The same evidence is **not** re-adjudicated until a desired result
appears. It may reopen only after a new owner-authorized protocol version **or** materially new source
evidence.

```text
FUTURE_ADJUDICATION_PROTOCOL_CONTRACT = OWNER ACCEPTED / EXECUTION DEFERRED
DOCUMENT REVIEW EXECUTION             = NOT AUTHORIZED BY THIS RECORD
```

## 10. What this record authorizes

**Exactly one bounded implementation**: the Decision 082 §10 contract as modified and finalized by
**R58**–**R62**, delivered as the next migration

```text
0014_m33_multi_registrant_relational_correction.sql
```

and the source and test changes Decision 082 §10.14 authorizes, plus only the current-state
documentation necessary to report implementation completion truthfully.

**Migration safety.** `0014` is a **prospective pre-E0 correction**. It is never applied to, and never
mutates, the accepted private M3.2 operational catalog. All real M3.3 parse and candidate tables
remain empty, and the migration is exercised only through test, disposable, and repository migration
machinery. If a test exposes non-empty state requiring destructive reinterpretation, the session
**STOPS**; no destructive migration of accepted real data is authorized.

**Identity and rehearsal rule.** Historical accepted Decision-070–077 rehearsal and evidence artifacts
are **immutable** and are not rewritten because corrected prospective hashes differ. Affected synthetic
scenarios receive **new** correction-stage expectations, every changed hash traceable exclusively to
**R46** / **R58**–**R62** semantics, and

```text
SINGLE_REGISTRANT_UNEXPECTED_IDENTITY_DELTAS = 0
```

**Mutation protection.** All fourteen Decision 082 §10.13 protections **MR-M1**–**MR-M14** are
implemented at their exact definitions, not reduced to representative coverage, and their
effectiveness is **demonstrated rather than assumed**.

**Prohibited for this implementation**: `src/disclosure_drift/cohorts.py`;
`src/disclosure_drift/pilot_policy.py`; migrations `0001`–`0013`; `Docs/preregistration.md`; every
existing record in `Docs/Decisions/`; every network, acquisition, and transport module; the D081
private verification evidence; the accepted M3.2 evidence root; migration `0015`; the verified-evidence
schema; and any document review or adjudication code.

## 11. What is unchanged

No research definition, hypothesis, threshold, cohort window, outcome, or seed. No quota value, no
quota domain, and no selector policy. `snapshot_id`, `entity_tie_break_sha256`, the **R15** evidence
preimage, and the **R16** resolution preimage are unaffected. Decision 021 is not rewritten; Decision
072's hard multi-registrant quota of **2** is unchanged; Decisions 079 and 080 are not rewritten and
Decision 081 is not rerun. Every accepted review artifact remains immutable, `m3.2-complete` is
unmoved, and tracked network switches remain `false` / `false`.

## 12. What this record does not authorize

It does **not**: write migration `0015` or any migration other than `0014`; implement the
verified-evidence schema; execute Review A, Review B, or the adjudication; classify any real filing;
resolve any real amendment parentage; grant any quota credit; close either real-path feasibility gate;
authorize the real durable offline parse (**M3.3-E0**) or progression to **M3.3-E1** or **M3.3-E2**;
authorize a real snapshot, selection, manifest, or root; approve a root or begin **M3.4**; make any
network, SEC, or HTTP request; write to the accepted M3.2 private evidence or any accepted catalog;
move `m3.2-complete`; or create any tag.

**Successful implementation is not acceptance.** **R49** condition B is satisfied only after the
implementation receives a fresh independent review **and** Sol/GPT owner acceptance.

## 13. Next authorized action

**Implement the R46 correction and migration `0014` under §10, then return to Sol/GPT.** A fresh
Claude Fable 5 maximum epoch performs the independent acceptance review under a separate owner packet.
The implementing session does not self-review for formal acceptance.

```text
M3_3_DECISION_082_PRE_E0_CONTRACTS_OWNER_ACCEPTED
R46_MULTI_REGISTRANT_IMPLEMENTATION_CONTRACT = OWNER ACCEPTED / IMPLEMENTATION AUTHORIZED
VERIFIED_EVIDENCE_SCHEMA_CONTRACT            = OWNER ACCEPTED / IMPLEMENTATION DEFERRED
FUTURE_ADJUDICATION_PROTOCOL_CONTRACT        = OWNER ACCEPTED / EXECUTION DEFERRED
MIGRATION_AUTHORIZED                         = 0014 only
M3_3_E0_AUTHORIZATION                        = NO
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY            = PENDING FUTURE AUTHORIZED E0 VERIFICATION
```
