# Decision 082 — D081 Owner Adjudication and Pre-E0 Correction / Evidence Protocol Contracts

```text
STATUS: ACCEPTED — OWNER D081 ADJUDICATION AND PRE-E0 CONTRACT FREEZE
DATE: 2026-08-14
OWNER: Sol/GPT
OUTCOME: M3_3_DECISION_081_SOURCE_VERIFICATION_OWNER_ACCEPTED
IMPLEMENTATION_AUTHORIZATION: NONE — GOVERNANCE RECORDING AND CONTRACT DESIGN ONLY
R46_MULTI_REGISTRANT_IMPLEMENTATION_AUTHORIZATION: NO — REQUIRED BEFORE E0, CONTRACT PENDING OWNER ACCEPTANCE
VERIFIED_EVIDENCE_SCHEMA_AUTHORIZATION: NO — CONTRACT PENDING OWNER ACCEPTANCE
DOCUMENT_ADJUDICATION_EXECUTION_AUTHORIZATION: NO — PROTOCOL PENDING OWNER ACCEPTANCE
M3_3_E0_DURABLE_PARSE_AUTHORIZATION: NO
E0_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: none
REQUEST_CEILING: 0
```

**This record does five things and nothing else.** It records Sol/GPT's owner acceptance of the
executed [Decision 081](decision_081_m3_3_fixed_complete_submission_source_verification.md)
source-verification sample and the disposition of that session's model deviation (§2); it freezes
seven owner rulings — **R51** (§3), **R52** (§4), **R53** (§5), **R54** (§6), **R55** (§7), **R56**
(§8), **R57** (§9); and it records three design contracts as **PENDING OWNER ACCEPTANCE** — the
**R46** multi-registrant implementation contract (§10), the verified-evidence schema contract (§11),
and the future document-adjudication protocol contract (§12).

**It implements nothing.** No source, test, migration, schema, or configuration file is touched by
the governance commit that records it. **It closes neither real-path gate**, classifies **zero** real
filings, resolves **zero** real amendment parentage, and grants **no** quota credit. **It makes no
network request** and authorizes none.

**Where this record and an earlier governing record disagree**, it controls only on the points it
names. Decisions 001–081 remain accepted and byte-unchanged.

---

## 1. Entry state — verified

Verified live by `scripts/verify_target.py` plus direct Git corroboration, with no fetch, pull,
reset, clean, or stash:

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD == `origin/main` | `8b61a068d916c5b59b02c634a24244c5b0f8e661` |
| HEAD tree | `1ce1baf9cac57a96f0c6d4b15896a1a56e1c5429` |
| HEAD parent | `817ec53089dfcd356a6cade044cc5120d81c4344` |
| `m3.2-complete` annotated tag object | `2865a1479e4576dc18a4098c928b278812f38d00` |
| Working tree at entry | clean |
| Migration chain | `0001`–`0013` |
| Tracked network switches | `network.enabled` `false`; `network.m3_acquire_enabled` `false` |

## 2. Decision 081 — owner accepted

```text
M3_3_DECISION_081_SOURCE_VERIFICATION_OWNER_ACCEPTED
```

Sol/GPT accepts the executed Decision-081 fixed Complete-Submission-Text source verification. Its
rulings **R46**–**R50** stand unchanged.

### 2.1 The frozen sample result

| Fact | Value |
|---|---|
| `SAMPLE_N` | **108** |
| Logical requests | **108** |
| Physical attempts | **109** |
| Successful artifacts | **108** |
| Terminal absences | **0** |
| `SAMPLE_TOTALITY` | **PASS** |
| `NETWORK_AUTHORIZATION` | **SPENT / CLOSED** |

The sample returned **108** rather than the 125 maximum. Under Decision 081 §8.4 that is a **correct
outcome, not a defect**: undersized strata take all available members and cross-stratum backfill is
prohibited.

Complete Submission Text measurements, as returned:

| Measurement | Result |
|---|---|
| Native 14-digit acceptance present and accession-bound | **108 / 108** |
| Header accession matches the expected accession | **108 / 108** |
| Header form matches the expected amendment form | **108 / 108** |
| `AmendmentDescription` present and nonempty | **38 / 108** |
| Explicit issuer-authored amendment statement | **98 / 108** |
| At least one purpose-evidence source | **101 / 108** |
| Explicit original **form** stated | **98 / 108** |
| Explicit original **filing date** stated | **98 / 108** |
| Explicit original **accession** stated | **0 / 108** |

The frozen mechanical **M9** lookup returned `EXACTLY_ONE` **50**, `ZERO` **38**, `MULTIPLE` **10**,
`N/A` **10** — summing to 108.

**The M9 result is an INSTRUMENT result.** It is **not** accepted as the final document-evidence
linkage capability rate, and it is superseded for that purpose by **R53** (§5). No purpose category
was assigned, no `amendment_relationship` was written, and no quota witness was created.

### 2.2 Model deviation — accepted, no rerun

Decision 081 requested Claude Opus 5 at maximum effort. The returned execution report records Claude
Fable 5 at maximum effort.

```text
D081_MODEL_DEVIATION_ACCEPTED_NO_RERUN
```

**Owner disposition: NONBLOCKING PROCESS DEVIATION.** Decision 081 is **not** rerun. The
deterministic sample, the frozen hashes, the request ledger, the stored artifacts, and every
measurement above remain accepted. The deviation is recorded here because the executing model is a
process fact worth preserving, not because any measurement is in doubt: the sample was deterministic
and hash-frozen before the first request, so its identity does not depend on which model executed it.

## 3. Ruling R51 — Decision 079 compatible-original diagnostic supersession

The Decision-079 audit historically reported a compatible-original diagnostic of `ZERO` **4677**,
`EXACTLY_ONE` **42159**, `MULTIPLE` **75**, `NO_DATE` **1**.

Decision 081 established that **no accepted computation rule for that split was preserved**, and that
four plausible reconstructions of the rule do not reproduce it.

**Owner ruling.** Those four numbers remain **historically truthful** as the output of that audit
session, and they are **DEMOTED from frozen binding facts** to:

```text
HISTORICAL NON-GOVERNING AUDIT OBSERVATION
```

They **must not** be used as: an E0 reconciliation gate; candidate identity; selection identity;
quota evidence; linkage evidence; or a stop condition for any future stage.

**Decision 079 and Decision 080 are not rewritten**, and neither is amended. Their text stands exactly
as the owner wrote it. Later references are marked superseded **for current operation** only.

**This demotion is narrow.** It reaches the compatible-original diagnostic split and nothing else.
The rest of the Decision-080 §2 frozen fact set — including
`REAL_RAW_TOTAL_AMENDMENT_CANDIDATES` **46912** and `FROZEN_COHORT_AMENDMENT_CANDIDATES` **20258** —
is untouched and remains frozen under Decision 079 R41.

**Cite as:** *Decision 082 R51 — D079 Compatible-Original Diagnostic Supersession.*

## 4. Ruling R52 — the canonical association-set diagnostic

**For FUTURE DIAGNOSTIC USE ONLY.** For one amendment accession `A`:

1. determine the complete set `S` of substantive registrant CIK associations for `A`;
2. for each CIK in `S`, identify compatible original accession records whose form is exactly **`10-K`**
   or **`10-KT`** and whose `report_date` **exactly equals** `A.report_date`;
3. **UNION** the results across every CIK in `S`;
4. deduplicate by canonical accession identity;
5. classify the size of that unique original-accession set — `0` ⇒ **ZERO**; `1` ⇒ **EXACTLY_ONE**;
   `>1` ⇒ **MULTIPLE**.

If the amendment `report_date` is absent, the classification is **NO_DATE**.

**This diagnostic gives ZERO linkage credit.** It does **not** establish `amends_original`,
`possible_amendment_of`, family identity, parentage, or quota contribution.

Decision 081 measured this **R46**-consistent diagnostic over the same reproduced population as:

| Class | Count |
|---|---|
| `ZERO` | **4286** |
| `EXACTLY_ONE` | **42391** |
| `MULTIPLE` | **234** |
| `NO_DATE` | **1** |

These four counts are frozen **only** as a Decision-079-population audit reconciliation fact. They
sum to **46912**, reconciling exactly against the frozen
`REAL_RAW_TOTAL_AMENDMENT_CANDIDATES`. **They are not real linkage evidence.**

The difference from the §3 historical split is the expected direction and is itself informative: a
union across the complete substantive association set resolves **more** amendments to at least one
compatible original (`ZERO` falls 4677 → 4286) while exposing **more** genuine ambiguity
(`MULTIPLE` rises 75 → 234). That is what correcting a false singleton should do. It is recorded as
an observation, not as a linkage result.

**Cite as:** *Decision 082 R52 — Canonical Association-Set Diagnostic.*

## 5. Ruling R53 — document assertion extraction is adjudicated

**A regex or otherwise mechanical date extractor is not adopted as governed evidence.**

For a Complete Submission Text artifact, the following document-evidence facts are extracted **only**
under the frozen human/adjudicated evidence protocol (§12):

| Field | Requirement |
|---|---|
| `PURPOSE_SUPPORTING_SPAN` | Verbatim, with location |
| `ORIGINAL_FORM_ASSERTED` | As stated by the filing |
| `ORIGINAL_FILING_DATE_ASSERTED` | As stated by the filing |
| `ORIGINAL_ACCESSION_ASSERTED` | As stated by the filing, if any |
| `SOURCE_LOCATION` | Stable location inside the frozen artifact |
| `ARTIFACT_SHA256` | The frozen artifact hash |

**A fiscal-period end date must never be substituted for an explicitly stated filing date.** The two
are different propositions, and conflating them manufactures an assertion the filing never made.

The Decision-081 frozen mechanical extractor remains **historical verification instrument evidence
only**. It is **not** corrected, and the Decision-081 **M9** measurement is **not** rerun.

**Cite as:** *Decision 082 R53 — Adjudicated Document Assertion Extraction.*

## 6. Ruling R54 — purpose-feasibility closure standard

The real amendment-purpose feasibility gate may close **only** after a **pre-registered independent
document-evidence adjudication** establishes at least one qualifying real amendment for **each** of
the three frozen categories:

1. administrative / certification / signature / exhibit-only;
2. financial-statement / accounting / restatement / XBRL correction;
3. narrative / business / risk / control / governance disclosure.

Each witness must: come from the frozen Decision-081 sample or a later owner-authorized deterministic
sample; carry an accepted Complete Submission Text artifact SHA-256; carry an exact supporting
span/location; pass the frozen independent-review/adjudication protocol (§12); and have **no
unresolved category conflict**.

**This stage produces none of those witnesses.** Therefore:

```text
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
```

remains **OPEN** (Decision 073 R30).

**Cite as:** *Decision 082 R54 — Purpose-Feasibility Closure Standard.*

## 7. Ruling R55 — linked-feasibility closure standard

The real linked-amendment feasibility gate may close **only** after pre-registered independent
document-evidence adjudication establishes at least **8 DISTINCT substantive entities** with
amendments whose source statement:

1. explicitly identifies a compatible original **form**;
2. explicitly identifies the exact original **filing date** or **accession**;
3. resolves to **exactly one** compatible original accession under the **complete substantive
   registrant association set**;
4. has **no conflicting explicit statement**;
5. can satisfy the strict-later acceptance requirement using the accepted **R43** accession-level
   acceptance source.

**The 8 feasibility witnesses do not have to become the final selected pilot witnesses.** They prove
source and method feasibility. **No quota credit is persisted during feasibility adjudication.**

Therefore:

```text
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
```

remains **OPEN** (Decision 074 R32) pending that proof.

**Cite as:** *Decision 082 R55 — Linked-Feasibility Closure Standard.*

## 8. Ruling R56 — Decision 081 source sufficiency

Sol/GPT accepts:

```text
COMPLETE_SUBMISSION_TEXT_SOURCE_FEASIBILITY = PROVED
NATIVE_ACCEPTANCE_SOURCE_FEASIBILITY        = PROVED
```

The Complete Submission Text is the **preferred single-artifact source** for native acceptance time,
document-level purpose evidence, and explicit-original linkage evidence. Structured XBRL is
**supplementary only**, and an **XBRL-only architecture is rejected** — the 38/108
`AmendmentDescription` rate against the 98/108 issuer-authored statement rate is the measured reason.

**No further network acquisition is authorized by this ruling.**

**Cite as:** *Decision 082 R56 — Decision 081 Source Sufficiency.*

## 9. Ruling R57 — future sampling

The class **X1** — `has_xbrl = true` **AND** `has_inline_xbrl = false` — is **not** required as a
mandatory recent-cohort sampling cell in future acquisition waves. Decision 081 showed that class is
**absent** in `prospective` and `monitoring` and has **one** member in `primary_test`.

Future sampling **may** still record XBRL state as a covariate. **X1 is not a mandatory
quota/stratum.** The Decision-081 sample remains valid and unchanged.

**Cite as:** *Decision 082 R57 — Future Sampling XBRL Stratification.*

## 10. The R46 multi-registrant implementation contract — PENDING OWNER ACCEPTANCE

**Nothing in this section is implemented.** It converts Decision 081 **R46** into an exact
implementation contract and returns it for owner adjudication.

### 10.1 What was inspected

`census_accessions`; `census_accession_observations`; `census_registrants`;
`census_registrant_observations`; `census_accession_field_resolutions`;
`pilot_candidate_accessions`; `pilot_candidate_accession_registrants`; `pilot_selected_accessions`;
migrations `0001`, `0003`, `0006`, `0009`, `0013`; the candidate snapshot builder
(`src/disclosure_drift/m3/candidate_snapshot.py`); the candidate identity graph
(`src/disclosure_drift/m3/candidate_identity.py`); the accession selector and its tie-break
(`src/disclosure_drift/sec/accession_selector.py`); the selection store and its replay path
(`src/disclosure_drift/sec/accession_selection_store.py`); the reserve selector; the release hashing
primitive (`src/disclosure_drift/release/hashing.py`); the pilot manifest crosswalk
(`src/disclosure_drift/release/pilot_manifest.py`); the manifest store; and the rehearsal layer.

### 10.2 A. The canonical representation of a multi-registrant accession

The accession remains an **accession-level object**. Its substantive registrant set is a **relation**,
never a scalar. The canonical representation is the **complete set of substantive registrant
associations**, each one row, with a role vocabulary that no longer implies primacy where none exists:

| Case | Representation |
|---|---|
| Exactly one **established** substantive registrant | One row, `role = 'anchor'`, `is_anchor = 1`. The scalar registrant remains factual (**R46** §3.1) |
| Two or more substantive registrants | Every substantive row `role = 'associated'`, `is_anchor = 0`. **No anchor row exists**, and the scalar is `NULL` |
| Association set **not established** | Every observed substantive row `role = 'associated'`, `is_anchor = 0`, scalar `NULL`, and the accession carries an explicit unestablished-completeness state |
| Submitter that is not substantive | `role = 'submitter_only'`, `is_anchor = 0`, noncontributing — **unchanged** |

The existing `role` CHECK vocabulary (`'anchor'`, `'associated'`, `'submitter_only'`) is **not
widened**. What changes is when `'anchor'` may be used, not what the words mean.

**A third state is required and does not exist today, and this is a finding rather than a
restatement.** Under Decision 072 R23 §5.2 the associated set is every *other* distinct CIK observed
in accepted `company.idx` rows for that accession. If no accepted full-index rows exist for an
accession — the R22 category-B case — the associated set is **empty**, and the accession is currently
indistinguishable from a genuine single-registrant filing. Under **R46** that silence must not read as
proof of a sole registrant. The contract therefore requires an explicit
`registrant_set_completeness` state (`established` / `unestablished`), and `anchor` is permissible
**only** under `established` with cardinality exactly 1.

### 10.3 B. Which scalar registrant fields remain factual, and when they are NULL

| Field | Disposition |
|---|---|
| `census_accessions.registrant_cik_numeric` | Factual **only** when the substantive association set is `established` with cardinality 1. Otherwise **`NULL`**. Currently `INTEGER NOT NULL REFERENCES census_registrants(cik_numeric)` |
| `census_accessions.submitter_cik_numeric` | **Remains factual and unchanged.** The submitter is a real per-submission fact. It is **never** promoted to registrant identity — **R46** §3.2(7) prohibits exactly that, and the rejected MR-3(a) recommendation was that promotion |
| `pilot_candidate_accessions.anchor_cik_numeric` | **`NULL`** whenever the accession does not have exactly one established substantive registrant. Currently `INTEGER NOT NULL` |
| `pilot_selected_accessions.anchor_cik_numeric` | **`NULL`** on the same condition. Currently `INTEGER NOT NULL` with a composite FK to `pilot_selected_entities` |

**No provenance is lost when the census scalar goes `NULL`.** The observation that produced each
registrant value already lives in `census_accession_observations` with its own
`source_observation_id` and `parsed_record_id`, and Decision 012 field resolution already records
winning and competing observations. The scalar was a convenience projection, not the evidence.

### 10.4 C. The relation that stores the full substantive association set

**Candidate layer — exists.** `pilot_candidate_accession_registrants` is already relational, already
snapshot-scoped, already carries the full set, and already collapses duplicate rows to distinct
canonical CIKs. It needs a completeness/evidence extension, not a redesign.

**Census layer — does not exist, and is required.** There is **no** durable census-level
accession→registrant relation today. The association set is recomputed at snapshot-build time by
grouping `census_accession_observations` rows with `field_name = 'cik_padded'` and
`source_id = 'sec_full_index_company'`. The only durable census-level registrant attribution is the
scalar this contract sets to `NULL`. Once that scalar is `NULL`, census-layer attribution has no
stored representation at all.

The contract therefore proposes a new relation:

```text
census_accession_registrants (
    accession_plain, registrant_cik_numeric, registrant_cik_padded,
    association_class, evidence_level,
    source_observation_id, parsed_record_id,
    first_observed_at_utc, latest_observed_at_utc
)
PRIMARY KEY (accession_plain, registrant_cik_numeric)
```

plus a per-accession `registrant_set_completeness` fact. `inventory_accession_registrants`
(migration `0001`) is the right *shape* precedent but is the M2.1 inventory layer and is not consumed
by the census or pilot path; it is **not** reused.

**A cheaper alternative exists and is stated rather than hidden.** The census relation could be
omitted, leaving the association set derived-at-build-time exactly as today and simply letting the
census scalar go `NULL`. That satisfies **R46**'s literal words at the candidate layer while leaving
the census layer with no registrant attribution whatever, and it leaves E0 — the first durable real
parse — writing a census row that asserts nothing about who filed. **The contract recommends the new
relation and marks the choice as an owner adjudication item (§10.15, item 1).**

### 10.5 D. Is a migration required?

**Yes.** SQLite cannot alter a column's `NOT NULL` constraint in place, and every affected table is
`STRICT`, so each change is a table rebuild (create, copy, drop, rename) or a new object. The exact
required set:

| # | Change | Mechanism |
|---|---|---|
| 1 | `census_accessions.registrant_cik_numeric` `NOT NULL` → nullable | Table rebuild |
| 2 | New `census_accession_registrants` relation and indexes | `CREATE TABLE` |
| 3 | New per-accession `registrant_set_completeness` fact | Column on the rebuilt `census_accessions`, or a column on the new relation's parent |
| 4 | `pilot_candidate_accessions.anchor_cik_numeric` `NOT NULL` → nullable | Table rebuild |
| 5 | `pilot_candidate_accession_registrants` completeness/evidence extension | Table rebuild |
| 6 | `pilot_selected_accessions.anchor_cik_numeric` `NOT NULL` → nullable | Table rebuild |
| 7 | Replace the `pilot_snapshot_freeze_requires_valid_state` anchor clause | `DROP TRIGGER` + `CREATE TRIGGER` |
| 8 | New freeze invariant: `anchor_cik_numeric IS NOT NULL` **iff** exactly one established substantive association | Trigger clause |

**The composite foreign key needs no trigger.** `pilot_selected_accessions`'s
`FOREIGN KEY (selection_run_id, snapshot_id, anchor_cik_numeric) REFERENCES pilot_selected_entities`
uses SQLite's default `MATCH SIMPLE` semantics: **if any column of a composite foreign key is `NULL`,
the constraint is not enforced for that row.** A `NULL` anchor therefore satisfies it vacuously and
correctly, with no schema gymnastics. What that FK stops enforcing must be replaced by the §10.11
attachment rule, stated as a trigger.

**The partial unique index is already correct.** `uq_pilot_candidate_accession_single_anchor` enforces
*at most one* anchor per accession. Zero anchors already satisfy it. It is **unchanged**.

**Every table rebuild copies zero rows.** `census_accessions`, `census_parsed_records`,
`census_parser_runs`, every `pilot_candidate_*` table, and every `pilot_selected_*` table are empty
(Decision 081 §9), so the rebuild is a schema operation with no data migration and no data risk.

**Proposed migration number: `0014`.** See §10.14.

### 10.6 E. Which existing hashes and preimages consume the false singleton

**Five, three directly and two transitively.** This is the complete list; nothing else in the identity
graph reads a registrant scalar.

| # | Identity | How it consumes the anchor | Location |
|---|---|---|---|
| **E1** | `accession_tie_break_sha256` | `SHA256(seed \| anchor_cik_padded \| accession_number_dashed)` | `accession_selector.py` `accession_selection_rank`; called from `candidate_snapshot.py` |
| **E2** | `candidate_accession_table_sha256` | `ACCESSION_TABLE_COLUMNS` carries **both** `anchor_cik_numeric` and `accession_tie_break_sha256` | `candidate_identity.py` |
| **E3** | `candidate_registrant_table_sha256` | `REGISTRANT_TABLE_COLUMNS` carries `role` and `is_anchor` | `candidate_identity.py` |
| **E4** | `candidate_snapshot_sha256` | `SNAPSHOT_CONTENT_FIELDS` carries E2 and E3 | `candidate_identity.py` — **transitive** |
| **E5** | `selection_input_sha256` → `selection_run_id` → the pilot manifest component hashes and root | The selection input digest carries `candidate_snapshot_sha256`, `entity_content_sha256`, and `accession_content_sha256`; the manifest carries `anchor_cik_numeric` (item 48) and `is_anchor` (item 49) | `accession_selection_store.py`; `pilot_manifest.py` — **transitive** |

**Explicitly not affected**, verified rather than assumed:

- **`snapshot_id`.** `SNAPSHOT_IDENTITY_FIELDS` is `candidate_policy_version`,
  `coverage_window_sha256`, `evidence_policy_version`, `input_observation_set_sha256`,
  `sic_family_mapping_version`. No content digest and no registrant value enters it.
- **`entity_tie_break_sha256`.** Derived from the padded CIK and the selection seed only.
- **`evidence_sha256` (R15) and `resolution_sha256` (R16).** Neither eight-field preimage nor the
  resolution preimage carries any registrant field.

**One consequence must be stated plainly.** E5 means the **manifest root itself** transitively depends
on the anchor. Decision 021's manifest crosswalk binds **item 48 = "anchor CIK"** to
`pilot_selected_accessions.anchor_cik_numeric` as a per-accession record. Making that value `NULL`
for multi-registrant accessions changes what item 48 asserts. That is a change to an **accepted M2.3
manifest item**, and it is returned as an owner adjudication item (§10.15, item 3) rather than
decided here.

### 10.7 F. Which identities must change prospectively before any real E0 identity exists

**All five in §10.6 — and all of them are free to change, because none of them exists for any real
accession.** `census_parser_runs`, `census_parsed_records`, and `census_accessions` are all **0**;
`parser_state` is `not_started` for all **76** accepted M3.2 plan sources; no candidate snapshot, no
selection run, and no manifest version exists (Decision 081 §9).

**There is therefore no historical real identity to rewrite, and none is rewritten.** The correction
is purely prospective, which is exactly the condition Decision 081 **R49** sequences E0 behind. The
only existing identities are **synthetic rehearsal** ones (§10.8).

**No replacement singleton is invented anywhere in this contract**, as **R46** §3.4 requires.

### 10.8 G. Which accepted synthetic rehearsal expectations and tests must change

Only fixtures and expectations that construct **multi-registrant** accessions, or that assert the
"exactly one anchor" invariant unconditionally. Single-registrant fixtures should be **byte-unchanged**
under the §10.9 recommendation.

| Surface | Nature of the change |
|---|---|
| `src/disclosure_drift/m3/rehearsal_world.py` | Multi-registrant world construction stops minting an anchor for the multi case |
| `src/disclosure_drift/m3/execution_rehearsal.py` | The rehearsal tie-break and anchor plumbing follow §10.9 |
| `tests/unit/test_m23_pilot_schema.py` | The freeze-trigger anchor expectations become conditional |
| `tests/unit/test_m23_accession_selector.py` | Multi-registrant selector fixtures lose their anchor |
| `tests/unit/test_m23_accession_selection_store.py` | The "expected exactly one anchor registrant row" store validation expectations |
| `tests/unit/test_m23_reserve_selector.py` | Multi-registrant reserve fixtures |
| `tests/unit/test_m3_candidate_snapshot.py` | Builder expectations for the multi case |
| `tests/unit/test_m3_support_target_pairs.py` | Pair aggregation keyed on the anchor |
| `tests/unit/test_m3_offline_parse.py`, `tests/unit/test_m3_3_execution.py` | Rehearsal plumbing |
| `tests/unit/test_audit_tooling.py`, `tests/unit/test_governance_reference_gates.py` | Incidental references |

**No accepted synthetic I/R identity is expected to change for a single-registrant fixture.** Any that
does is a defect in the implementation, not an accepted consequence, and the §10.13 mutation set is
what proves it.

### 10.9 H. How single-registrant behaviour is preserved byte-for-byte

**The recommendation is to leave the single-registrant preimage exactly as it is today.** Where an
accession has exactly one established substantive registrant, `accession_selection_rank` is called
with that CIK, unchanged, and every downstream digest is byte-identical to the current
implementation.

The open question is only what occupies the registrant slot when **no** anchor exists. Three
candidates, with their exact costs:

| Option | Definition | Cost |
|---|---|---|
| **H-a** *(recommended)* | A fixed non-CIK sentinel literal in the anchor slot for every accession with ≠1 established registrant | Preserves single-registrant bytes exactly. Chooses **no** registrant, so it is not an anchor-selection heuristic under **R46** §3.2. Stable if the association set is later corrected. A non-digit literal cannot collide with any 10-digit padded CIK |
| **H-b** | A digest of the ordered substantive association set | Truthful and anchor-free, but the tie-break **drifts** whenever the association set is later corrected — the precise hazard `accession_selection_rank`'s own docstring was written to avoid |
| **H-c** | Drop the registrant slot: `SHA256(seed \| accession_number_dashed)` | Conceptually cleanest and most faithful to "the accession is an accession-level object", but changes **every** accession's tie-break, including every single-registrant one, so it forfeits byte-for-byte preservation entirely |

**H-a is recommended.** It is worth being explicit about why it does not violate **R46** §3.2(5),
which prohibits choosing a primary CIK **by hash**: H-a does not choose a CIK at all. It records that
no anchor exists. Selecting nothing is not selecting by hash.

**This is an owner adjudication item (§10.15, item 2), not a decided point.**

### 10.10 I. How Decision 072 multi-registrant semantics are preserved

**Decision 072 R24 is preserved exactly.** The multi-registrant quota stays measurable, hard, not
deferred, not optional, and outside `APPROVED_DEFERRED_QUOTA_KEYS`. Nothing in this contract lowers,
proxies, or defers it.

**Decision 072 R23 §5.3 is restated with identical extension.** Its predicate reads "exactly one valid
anchor **and** at least one distinct valid associated registrant". Under **R46** no anchor exists in
that case, so the predicate is restated anchor-free as:

```text
multi_registrant = 1  iff  the substantive association set is `established`
                          and its distinct canonical CIK cardinality is >= 2
```

**The set of accessions flagged is unchanged.** "One anchor plus at least one associated" and "at least
two distinct substantive associations" have the same extension; only the phrasing loses the false
primacy. Submitter-only rows still never make it true, repeated rows for one CIK still never create a
second registrant, and the flag is still never a raw row count.

**Decision 072 R23 §5.2 is partially superseded, and only for the multi case.** Its rule that "the
authoritative anchor remains the already resolved census accession anchor" is exactly the false
singleton **R46** prohibits, where more than one substantive registrant exists. For a genuine
single-registrant accession, R23 §5.2 stands unchanged.

### 10.11 J. How the hard multi-registrant quota works without a fabricated primary CIK

**The quota mechanism already needs no anchor, and this is the most important finding in this
section.** The witness the selector records for `multi_registrant_accessions` is keyed on the
**accession dashed number**, never on a registrant. Decision 013 already fixes that an accession
satisfies the multi-registrant quota **once, regardless of how many registrant CIKs it carries**. The
required count is **2 accessions**, hard, and it is unchanged.

Two things must nevertheless change, and neither invents a CIK:

1. **The store validation.** `accession_selection_store.py`'s multi-registrant mapping currently
   requires "exactly one anchor registrant row", requires that anchor to equal
   `anchor_cik_numeric`, and rejects `multi_registrant = 1` "without a qualifying registrant set (one
   anchor plus at least one associated row)". All three checks are restated on the §10.10 predicate.
   The aggregate evidence level continues to be computed over the **substantive** rows — which, for a
   multi-registrant accession, is simply all of them.

2. **Selection attachment.** The composite FK from `pilot_selected_accessions.anchor_cik_numeric` to
   `pilot_selected_entities` is what currently binds a selected accession to a selected entity. With a
   `NULL` anchor it stops enforcing (§10.5). It is replaced by an explicit rule, enforced by trigger:

   ```text
   A selected accession must have at least one substantive registrant association
   that is a selected entity in the same selection run.
   ```

   For a single-registrant accession this is byte-equivalent to the current FK. For a multi-registrant
   accession it is satisfied by **any** co-selected substantive registrant, without designating one.
   **Attachment is not primacy**, and this rule never writes a CIK into an anchor column.

**History and event aggregation is the remaining consumer, and it is a genuine open question.** The
builder currently groups accessions by anchor to derive per-entity `eligible_forms`,
`original_annual_report_dates`, `original_annual_report_count`, `multi_registrant_annual_filing`, and
`non_ordinary_amendment_lineage`. With no anchor there are exactly two defensible rules —
**attribute the accession to every substantive registrant**, or **attribute it to none and record the
entity's history as unestablished for that accession**. They differ in what `history_class` means for a
joint filer, which is a research-facing semantic, not an engineering convenience. **It is returned as
an owner adjudication item (§10.15, item 4) and is not decided here.**

### 10.12 K. The rollback and recovery rule

**Migrations in this repository are forward-only.** Each is applied with an immutable name and
checksum provenance row, and the applied chain is verified before and after. There is no
down-migration mechanism, and none is proposed.

**Hard precondition.** The correction may be applied **only** while every affected table is empty:
`census_parser_runs`, `census_parsed_records`, `census_accessions`, `census_accession_observations`,
every `pilot_candidate_*` table, every `pilot_selected_*` table, `pilot_selection_runs`, and
`pilot_manifest_versions`. **If any is non-empty, STOP and return to the owner.** A non-empty table
means a real identity exists, which would make this a data migration rather than a prospective
schema correction — a materially different act requiring its own authorization.

**Rollback rule.** Because the precondition guarantees zero rows, rollback is: revert the migration
and code commits together, discard the operational catalog, and rebuild it from migrations
`0001`–`0013`. **No accepted data is lost, because none exists.** No accepted M3.2 raw object, receipt,
or evidence artifact is touched by either the correction or its rollback — rule 6 (never delete raw
data) is not engaged at any point.

**Recovery rule.** If the correction is applied and then found defective *after* real E0 state exists,
rollback is **no longer available** and the defect is escalated to the owner as a blocker. That is the
reason **R49** sequences the correction **before** E0 rather than after.

### 10.13 L. The exact mutation tests that prove first-write and order invariance

A mutation is only useful if the *unmutated* suite fails when the mutation is applied. Each entry
below names the mutation and the assertion that must kill it. Digest equality alone is insufficient
for several of them — `hash_table` sorts rendered rows, so a row-order mutation is invisible to the
digest and must be caught by a positive assertion on persisted content.

| # | Mutation | Killing assertion |
|---|---|---|
| **MR-M1** | Permute the insertion order of substantive registrant rows | Snapshot digests, tie-break, `multi_registrant`, and quota results all identical |
| **MR-M2** | Remove the `ORDER BY` from the full-index observation read | Identical association set and identical digests |
| **MR-M3** | Reverse the `sorted()` ordering in the registrant-row builder | Persisted row **set** identical; anchor state identical |
| **MR-M4** | Set the anchor to `min(CIK)` for a multi-registrant accession | `anchor_cik_numeric IS NULL` fails |
| **MR-M5** | Set the anchor to `max(CIK)` | Same |
| **MR-M6** | Set the anchor from first-write / first observation order | Same |
| **MR-M7** | Set the anchor to `submitter_cik_numeric` | Same — this is the rejected MR-3(a) route |
| **MR-M8** | Set the anchor to the CIK whose hash sorts first | Same — **R46** §3.2(5) |
| **MR-M9** | Set the anchor to the census scalar (status-quo regression) | Same |
| **MR-M10** | Derive the association set from a source with rows omitted | `registrant_set_completeness` must be `unestablished`; a silent single-registrant result fails |
| **MR-M11** | Compute `multi_registrant` from a raw row count instead of distinct CIK cardinality | Duplicate-row fixture must not flip the flag |
| **MR-M12** | Count a `submitter_only` row as substantive | Flag must not flip |
| **MR-M13** | Alter the single-registrant tie-break preimage | The byte-identity assertion against the pre-correction digest fails |
| **MR-M14** | Make the multi-registrant tie-break depend on a specific member CIK | Association-set permutation must leave the tie-break unchanged |

**MR-M13 is the one that proves §10.9's guarantee is real** rather than asserted, and it must compare
against digests computed before the correction, pinned as literals in the test.

These continue the existing campaign numbering convention without renumbering it: the accepted
M1–M38 campaign is closed and is **not** reopened, extended, or re-executed by this contract.

### 10.14 Proposed migration number and authorized paths

**Proposed migration: `0014_m33_multi_registrant_relational_correction.sql`.**

Paths a future authorized implementation stage would be permitted to touch:

```text
src/disclosure_drift/storage/migrations/0014_m33_multi_registrant_relational_correction.sql   (new)
src/disclosure_drift/m3/candidate_snapshot.py
src/disclosure_drift/m3/candidate_identity.py
src/disclosure_drift/m3/rehearsal_world.py
src/disclosure_drift/m3/execution_rehearsal.py
src/disclosure_drift/m3/support_target_pairs.py
src/disclosure_drift/sec/accession_selector.py
src/disclosure_drift/sec/accession_selection_store.py
src/disclosure_drift/sec/reserve_selector.py
src/disclosure_drift/sec/pilot_manifest_store.py
src/disclosure_drift/release/pilot_manifest.py
src/disclosure_drift/reasons.py
Docs/sec_data_dictionary.md
tests/unit/*        (the §10.8 set)
tests/integration/*  (only where the §10.8 set requires it)
```

**Explicitly prohibited paths for that stage**, listed so the boundary is not inferred:
`src/disclosure_drift/cohorts.py`; `src/disclosure_drift/pilot_policy.py`; every migration
`0001`–`0013`; `Docs/preregistration.md`; every existing record in `Docs/Decisions/`; and any network,
acquisition, or transport module.

**No migration is written by this record**, and no path above is touched by the governance commit that
records it.

### 10.15 Open owner adjudication items — R46 contract

| # | Item | Recommendation |
|---|---|---|
| **1** | New `census_accession_registrants` relation, or leave census-layer attribution derived-only | **New relation** (§10.4) |
| **2** | The §10.9 filler for the anchor slot: **H-a**, **H-b**, or **H-c** | **H-a**, the non-CIK sentinel |
| **3** | Decision 021 manifest **item 48 "anchor CIK"** becoming nullable — an accepted M2.3 manifest item | Owner decision; no recommendation offered, because it changes what an accepted manifest asserts |
| **4** | History/event attribution for a multi-registrant accession: **every** substantive registrant, or **none** | Owner decision; this is a research-facing semantic, not an engineering choice |
| **5** | Whether `registrant_set_completeness = unestablished` blocks candidacy or only blocks the anchor | Owner decision |

```text
R46_MULTI_REGISTRANT_IMPLEMENTATION_CONTRACT = PENDING OWNER ACCEPTANCE
```

## 11. The verified-evidence schema contract — PENDING OWNER ACCEPTANCE

**Nothing in this section is implemented.** It designs the minimum schema needed to persist verified
document evidence, and returns the exact identity implications.

### 11.1 What must be persisted

Verified amendment-purpose evidence; verified explicit-original/linkage evidence; document artifact
provenance; supporting span/location; independent reviewer decisions; the adjudicated final result;
the artifact SHA-256; and `evidence_level = verified`.

### 11.2 The proposed tables

Four new relations, each append-only and immutable once frozen:

```text
document_artifacts (
    artifact_sha256 PRIMARY KEY, accession_plain, source_class,
    byte_length, retrieved_at_utc, source_url, retrieval_receipt_id
)

document_review_records (
    review_id PRIMARY KEY, artifact_sha256, accession_plain,
    review_pass,            -- 'A' | 'B' | 'ADJUDICATION'
    protocol_version, reviewer_identifier, decided_at_utc,
    purpose_category,       -- nullable; abstention is NULL
    abstained, abstention_reason,
    original_form_asserted, original_filing_date_asserted,
    original_accession_asserted,
    review_record_sha256
)

document_review_spans (
    review_id, span_ordinal, span_role,
    span_text_verbatim, span_location, span_sha256
)

document_adjudicated_evidence (
    accession_plain, evidence_kind,        -- 'amendment_purpose' | 'explicit_original'
    artifact_sha256, adjudicated_value,
    agreement_state,        -- 'agreed' | 'resolved' | 'conflicting' | 'abstained'
    contributing_review_ids_json,
    evidence_level,         -- 'verified' where and only where agreement permits
    adjudication_sha256, frozen_at_utc
)
```

Plus the widening required by Decision 080 §9.3: the migration `0009` evidence-level CHECK
constraints exclude `'verified'` **by design**, stated in that migration's own header, and
`amendment_purpose_quota_eligible` currently requires
`amendment_purpose_evidence_level = 'provisional'`. Both must widen before any verified value can be
persisted or can satisfy a quota.

### 11.3 The identity implications — exact

**The governing mechanic is `hash_table`.** It hashes the table name, then the column tuple, then the
sorted rendered rows, where a `NULL` renders as a fixed sentinel. Two consequences follow, and both
were verified against the implementation rather than assumed:

1. **Adding a column to an existing digest's column tuple changes that digest for every row, even if
   the new column is `NULL` everywhere.** The sentinel is appended to each rendered row and the column
   header changes. Widening `ACCESSION_TABLE_COLUMNS`, `REGISTRANT_TABLE_COLUMNS`, or
   `SNAPSHOT_CONTENT_FIELDS` therefore **breaks every accepted synthetic I/R identity**.

2. **A new domain — a new table name — leaves every existing digest byte-unchanged.**

**Therefore: the evidence layer can be added with zero disturbance to accepted synthetic I/R
identities if and only if it lives entirely in NEW hashing domains and no existing column tuple is
widened.** The four §11.2 relations do exactly that, under new domains such as
`document_review_record`, `document_review_span`, and `document_adjudicated_evidence`.

**The unavoidable exception.** The moment a verified purpose category or a verified `amends_original`
actually *reaches* `pilot_candidate_accessions` — populating `amendment_purpose_category` or
`amendment_linkage_state` where the metadata path left them `NULL` — `candidate_accession_table_sha256`
changes because a **value** changed. That is correct and unavoidable: a different candidate row is a
different candidate row. It is a **content** change under an unchanged column tuple, not a schema
change, and it affects only future real snapshots. **No accepted synthetic identity changes**, because
no synthetic fixture will carry verified evidence.

**No second hash implementation is introduced.** Every new digest goes through
`src/disclosure_drift/release/hashing.py`, preserving the Decision 067 §9 / R16 discipline.

### 11.4 Separation from the R46 correction

**Separate migrations are recommended, and separation is technically available.** The two changes
share no table: **R46** touches `census_accessions`, `pilot_candidate_accessions`,
`pilot_candidate_accession_registrants`, and `pilot_selected_accessions`; the evidence layer creates
four new tables and widens evidence-level CHECKs. The one overlap — the
`amendment_purpose_evidence_level` CHECK on `pilot_candidate_accessions`, whose table **R46** rebuilds
anyway — is a sequencing convenience, not a coupling.

**Proposed: migration `0014` for R46 (§10.14), migration `0015` for the evidence layer.** Auditability
is materially better with two records: **R46** is a truthfulness correction to an existing model, the
evidence layer is a new capability, and an independent reviewer should be able to accept or reject
them separately.

**Ordering constraint.** If both are applied, `0014` must precede `0015`, so the evidence layer is
never built on top of a schema that still asserts a false singleton.

### 11.5 Open owner adjudication items — evidence schema

| # | Item |
|---|---|
| **1** | Whether `document_artifacts` is a catalog table or stays private-evidence-root metadata only |
| **2** | Whether a `verified` linkage state reuses `amendment_linkage_state = 'amends_original'` or introduces a distinct verified state |
| **3** | Whether `verified` becomes eligible for **every** evidence dimension or only for `amendment_purpose` and linkage |
| **4** | Whether reviewer identifiers are recorded as durable values or as salted opaque identifiers |

```text
VERIFIED_EVIDENCE_SCHEMA_CONTRACT = PENDING OWNER ACCEPTANCE
```

## 12. The future document-adjudication protocol contract — PENDING OWNER ACCEPTANCE

**Nothing in this section is executed.** No real filing is classified. The protocol below runs later,
against the **already stored** Decision-081 artifacts. **ZERO new SEC requests are required.**

### 12.1 Sequencing — sequential, not parallel

| Pass | Conditions |
|---|---|
| **REVIEW A** | Fresh epoch/session. Artifact set frozen. Does **not** see Review B or any adjudication output |
| **REVIEW B** | A **different** fresh epoch/session. The same frozen artifact set. Does **not** see Review A |
| **ADJUDICATION** | A fresh epoch. Sees A and B **only after both are frozen**. Resolves **only** predefined disagreements |

**No parallel sessions are required, and none is used.** Independence here is a property of *what each
pass can see*, not of when it runs; sequential passes in separate epochs give the same blindness with
strictly better auditability. Every pass is blind to selection state and to every outcome value
(Decision 015; leakage register L15/L19 unchanged).

### 12.2 Review fields

Each review pass records, per accession: `artifact_sha256`; `accession_plain`; `protocol_version`;
`reviewer_identifier`; `decided_at_utc`; `purpose_category` **or** an abstention; every supporting
span verbatim with its location; `original_form_asserted`; `original_filing_date_asserted`;
`original_accession_asserted`; and a per-record hash.

**Allowed abstentions.** Insufficient text; ambiguous text; text present but not issuer-authored;
artifact unreadable at the stated location. An abstention is a **recorded outcome**, never a skipped
row — Decision 080 **AP-1** totality applies, so every artifact in the frozen set is adjudicated.

### 12.3 Category definitions

The three frozen categories, **verbatim and unchanged**:

1. administrative / certification / signature / exhibit-only;
2. financial-statement / accounting / restatement / XBRL correction;
3. narrative / business / risk / control / governance disclosure.

**Prohibited, without exception:** keyword classifier; substring classifier; regex classifier;
LLM-only classifier; filename heuristic; `primaryDocDescription` classifier; operator intuition; form
suffix inference.

### 12.4 Original form, date, and accession extraction rules

| Rule | Statement |
|---|---|
| **X-1** | Only an **issuer-authored** statement in the amendment's own artifact qualifies |
| **X-2** | The original **form** must be stated explicitly and must be exactly `10-K` or `10-KT` (**R44**) |
| **X-3** | The original **filing date** must be stated explicitly as a filing date. **A fiscal-period end date is never substituted for it** (**R53**) |
| **X-4** | The original **accession** is recorded only where the filing states it. Decision 081 measured this at **0/108**, so the protocol must not depend on it |
| **X-5** | Where form, date, and accession are stated inconsistently **within** the artifact, the record is `conflicting` and no value is extracted |
| **X-6** | Extraction records what the filing **asserts**. Resolution against the catalog is a separate later step and never feeds back into extraction |

### 12.5 Span-citation requirements

Every non-abstaining record carries at least one span: **verbatim text**, a **stable location** inside
the frozen artifact, and a **span hash**. A record whose spans cannot be mechanically located in the
artifact at the stated location **fails closed** and is `conflicting`, never silently accepted
(Decision 080 **AP-9**).

### 12.6 Agreement, third adjudication, and fail-closed states

| Condition | Result |
|---|---|
| A and B agree exactly on category **and** on every extracted assertion | `agreed` ⇒ eligible for `verified` |
| A and B both abstain | `abstained` ⇒ no category, no linkage, no quota credit |
| One abstains, one asserts | **Third adjudication** |
| A and B assert different categories | **Third adjudication** |
| A and B assert different original form/date/accession | **Third adjudication** |
| Third adjudication resolves, citing exact text from the frozen artifact | `resolved` ⇒ eligible for `verified` |
| Third adjudication cannot resolve | `conflicting` ⇒ **no quota credit**, fail closed |
| A span fails mechanical location | `conflicting` ⇒ fail closed |

**Never averaged. Never majority-by-silence. Never repaired.** An adjudicated category **never**
overwrites a structured metadata fact; a structured/narrative contradiction — an `AmendmentFlag`
disagreement, for instance — is a **recorded review condition** under the Decision 008 non-conflation
rule (Decision 080 **AP-10**).

### 12.7 Hashes

| Artefact | Hash |
|---|---|
| Review A | `REVIEW_A_TABLE_SHA256` over the complete frozen Review-A record set |
| Review B | `REVIEW_B_TABLE_SHA256` over the complete frozen Review-B record set |
| Adjudication | `ADJUDICATION_TABLE_SHA256` over the complete final table |
| Each record | Its own `review_record_sha256` |
| Each span | Its own `span_sha256` |

All five go through `src/disclosure_drift/release/hashing.py` under **new domains** (§11.3). Review A
is frozen and hashed **before** Review B begins; Review B is frozen and hashed **before** adjudication
begins. **A pass whose hash is not frozen cannot be consumed by the next pass** — that is the
mechanical enforcement of independence.

### 12.8 Feasibility-witness calculation

**Purpose feasibility (R54).** Count distinct categories having **at least one** accession whose final
`agreement_state` is `agreed` or `resolved` with a non-null category. **All three** categories must be
represented. `conflicting` and `abstained` contribute nothing.

**Linked feasibility (R55).** For each accession whose final state is `agreed` or `resolved` with an
explicit original assertion, resolve that assertion under **R52**'s association-set union against the
accepted catalog. Retain only `EXACTLY_ONE` resolutions with no conflicting statement that also pass
the strict-later acceptance rule on the **R43** accession-level source. Count **distinct substantive
entities** across the retained set. The gate closes at **8 or more**.

**No quota credit is persisted by either calculation.** They are feasibility proofs, and Decision 081
§8.10 continues to prohibit writing `amends_original` into any accepted structure until a separately
authorized stage does so.

### 12.9 Open owner adjudication items — adjudication protocol

| # | Item |
|---|---|
| **1** | Whether the third adjudication may be performed by the same operator in a fresh epoch, or requires a distinct one |
| **2** | Whether the protocol runs over all **108** artifacts or a precommitted deterministic subset |
| **3** | The exact `protocol_version` string to freeze |
| **4** | Whether a `conflicting` outcome is re-adjudicable later, or is permanently terminal |

```text
FUTURE_ADJUDICATION_PROTOCOL_CONTRACT = PENDING OWNER ACCEPTANCE
```

## 13. What is unchanged

No research definition, hypothesis, threshold, cohort window, outcome, or seed. No selector, reserve
selector, candidate behaviour, offline-parsing behaviour, selection store, manifest or release
hashing, migration, or configuration. No evidence, receipt, snapshot, or selection identity. No source
file, no test, and no config is touched by the governance commit that records this decision. The
preregistration is untouched, every accepted review artifact remains immutable, `m3.2-complete` is
unmoved, migrations remain `0001`–`0013`, and tracked network switches remain `false` / `false`.

Decisions 079 and 080 are **not rewritten**. Decision 081 is **not rerun**. The frozen Decision-080 §2
inventory facts are unchanged except for the narrow **R51** demotion of the compatible-original
diagnostic split. Both real-path gates remain **OPEN**, and `REAL_ACCEPTANCE_ORDERING_ADEQUACY`
remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION**.

## 14. What this record does not authorize

It does **not**: implement the **R46** multi-registrant correction; write migration `0014`, `0015`, or
any migration; implement the verified-evidence schema; execute Review A, Review B, or the
adjudication; classify any real filing; resolve any real amendment parentage; grant any quota credit;
close either real-path feasibility gate; resolve real acceptance-ordering adequacy; authorize the real
durable offline parse (**M3.3-E0**) or progression to **M3.3-E1** or **M3.3-E2**; authorize a real
snapshot, selection, manifest, or root; approve a root or begin **M3.4**; make any network, SEC, or
HTTP request; authorize any acquisition, reacquisition, or enrichment; write to the accepted M3.2
private evidence, the accepted real private catalog, or any accepted catalog; reopen the consumed
Decision-079 ephemeral-audit authorization or the spent Decision-081 network authority; reverse
Decision 071's **IN-2**; lower, defer, or proxy any quota; move `m3.2-complete`; or create any tag.

## 15. Next authorized action

**Owner adjudication of the three contracts recorded here** — §10 (**R46** multi-registrant
implementation), §11 (verified-evidence schema), and §12 (document-adjudication protocol) — each
returned as `PENDING OWNER ACCEPTANCE` with its own open items. **Nothing else.**

No session may begin the **R46** implementation, write any migration, execute any document review, or
begin **M3.3-E0** on the strength of this record.

```text
M3_3_DECISION_081_SOURCE_VERIFICATION_OWNER_ACCEPTED
D081_MODEL_DEVIATION_ACCEPTED_NO_RERUN
R46_MULTI_REGISTRANT_IMPLEMENTATION_CONTRACT = PENDING OWNER ACCEPTANCE
VERIFIED_EVIDENCE_SCHEMA_CONTRACT            = PENDING OWNER ACCEPTANCE
FUTURE_ADJUDICATION_PROTOCOL_CONTRACT        = PENDING OWNER ACCEPTANCE
MULTI_REGISTRANT_CORRECTION = REQUIRED BEFORE E0 / NOT YET IMPLEMENTED
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY = PENDING FUTURE AUTHORIZED E0 VERIFICATION
```
