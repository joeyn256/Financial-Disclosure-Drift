# Decision 079 — Pre-E0 Ephemeral Real-Source Parse and Amendment-Inventory Audit

```text
STATUS: ACCEPTED — OWNER PRE-E0 EPHEMERAL REAL-SOURCE PARSE / AMENDMENT-INVENTORY AUDIT AUTHORIZATION
DATE: 2026-08-14
OWNER: Sol/GPT
OUTCOME: M3_3_PRE_E0_EPHEMERAL_REAL_SOURCE_INVENTORY_AUDIT_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION: NONE — GOVERNANCE RECORDING PLUS ONE BOUNDED EPHEMERAL READ-ONLY AUDIT
REAL_PRIVATE_EPHEMERAL_PARSE_AUDIT_AUTHORIZATION: YES — ONE AUDIT, EPHEMERAL OUTPUT ONLY
M3_3_E0_DURABLE_PARSE_AUTHORIZATION: NO
REAL_SNAPSHOT_AUTHORIZATION: NO
REAL_SELECTION_AUTHORIZATION: NO
MANIFEST_ROOT_CONSTRUCTION_AUTHORIZATION: NO
E0_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: none
REQUEST_CEILING: 0
```

**This record authorizes one bounded audit and records three rulings and one process rule. It does
nothing else.** It makes explicit a boundary that [Decision 078](decision_078_m3_3_i_r_owner_acceptance_and_real_feasibility_audit.md)
§3.2 already implied — in-memory parsing for audit purposes — and states exactly where the line
between an *ephemeral* parse and a *durable* M3.3-E0 parse falls.

**It closes neither real-path gate.** `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` (Decision
073 R30) and `M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` (Decision 074 R32) both remain
**OPEN / ACTIVE**, separately auditable, and never merged. **It authorizes no real execution**:
M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 each remain a separate, unissued owner gate.

**Where this record and an earlier governing record disagree**, it controls only on the points it
names. Decisions 001–078 remain accepted and byte-unchanged.

---

## 1. Ruling-number collision — read this before citing R39

**Decision 078 §3 already defines a ruling numbered R39** ("Pre-E0 Read-Only Real-Feasibility Source
Audit"). The owner's Decision 079 packet independently numbers this record's first ruling **R39**
("Hash / Validator Conflict") and instructs `CITE AS: Decision 079 R39`.

**Both numbers stand as the owner wrote them. Neither ruling amends, replaces, or narrows the
other**, and this record does not renumber Decision 078.

| Citation | Ruling |
|---|---|
| **Decision 078 R39** | Pre-E0 read-only real-feasibility source audit (Decision 078 §3) |
| **Decision 079 R39** | Artifact-hash / validator-conflict rule (§3 below) |

**Every citation of R39 must be decision-qualified.** A bare "R39" is ambiguous from 2026-08-14
forward and must not be written. R40, R41, and P8 are unambiguous: no earlier record uses them.

**Returned to the owner as OBS-1** (§10). Renumbering this record's R39 to **R42** would remove the
ambiguity permanently, and is the owner's call, not the auditor's. Nothing here is blocked on it.

## 2. Decision 078 facts accepted as frozen

The owner accepts the Decision 078 count audit **with the structural-zero interpretation**. The
durable catalog's zeros are a statement about the *catalog*, not about the *world*.

| Fact | Value |
|---|---|
| `M3_3_I_R_STATUS` | **OWNER ACCEPTED / COMPLETE** |
| `ACCEPTED_EXECUTABLE_TARGET` | `feaeaa4163587730d6b12ebb87aabf2fc215c8f3` |
| T7 receipt SHA-256 | `ae8ace5dc62155c9dca395af238290b0bb5b99dc4e3f1741e3d8ff1c9ab9c3dd` |
| T7 receipt ID | `7d72a5501f66d36af9024b80a64060668da315b8880fb5add028917d36ad12e1` |
| T7 run | `m3-2-acquisition-b6f8bc7f48b94e6080038db575b204e5` |
| Predecessor receipt SHA-256 | `0278c857d7816a79907068513fe09d5b78fc3973ba415149fbc9d73605b5359c` |
| Accepted observations | **77** |
| Accepted raw objects | **76** |
| Successor satisfaction | **75 / 75** |
| Cumulative physical attempts | **77 of 801** |
| `census_accessions` | **0** |
| `census_parser_runs` | **0** |
| `census_parsed_records` | **0** |
| `parser_state` | **`not_started` for all 76 plan sources** |

**The correct interpretation, and the only one this record permits:**

```text
DURABLE_PARSED_AMENDMENT_POPULATION = 0
REAL_RAW_SOURCE_AMENDMENT_POPULATION = NOT YET MEASURED
```

**Zero durable parsed records does not mean zero real amendments.** No parse has ever run. The
accepted raw source material is already in hand, and measuring it requires **no** new SEC request:
`NEW_SEC_REQUESTS_NEEDED_TO_MEASURE_POPULATION = 0`.

## 3. Ruling R39 (Decision 079) — artifact-hash / validator conflict

**Defect class.** A validator may incorrectly parse or search an artifact **even when the artifact's
exact frozen hash matches**. The hash is the stronger evidence; the ad-hoc checker is the weaker.

**Rule.** When both of the following hold:

1. the candidate artifact's SHA-256 **exactly equals** the owner-frozen SHA-256; and
2. a secondary ad-hoc field-level checker reports a **contradictory** identity failure,

the contradictory result is classified **`VALIDATOR_CONFLICT`**, **not**
`ARTIFACT_IDENTITY_MISMATCH`, until independently confirmed by a **correct structured parse**.

**What this does not say.** An artifact hash does not prove every semantic assertion made about that
artifact. It proves the bytes. The rule is narrower and one-directional: **an ad-hoc substring or
search checker may not overrule byte-exact artifact identity without independent evidence.**

**Required response:** inspect the validator; parse the structured content correctly; **do not**
emit a false `NO_IDENTITY_MATCH`.

**Cite as:** *Decision 079 R39 — Artifact-Hash / Validator Conflict.* (Never as a bare "R39" — see
§1.)

## 4. Ruling R40 — ephemeral real-source parse

Decision 078 §3.2 already permitted in-memory parsing for audit purposes. **This ruling makes the
boundary explicit and exhaustive.**

**Authorized.** Use **accepted, production parser functions** against **accepted M3.2 raw objects**
to derive **temporary** audit records. Temporary parsed objects may exist:

- in Python memory; or
- in a session scratch directory **outside** both the repository and `EV_ROOT`.

**Prohibited.** They may **not** be written into `census_parser_runs`, `census_parsed_records`,
`census_accessions`, `census_accession_observations`, any candidate table, any selection table, the
accepted evidence root, or **any** accepted catalog.

**No SQLite writer is authorized. No migration is authorized. No durable parser-state change is
authorized.**

```text
REAL_PRIVATE_EPHEMERAL_PARSE_AUDIT_AUTHORIZATION = YES
M3_3_E0_DURABLE_PARSE_AUTHORIZATION = NO
```

**Cite as:** *Decision 079 R40 — Ephemeral Real-Source Parse.*

## 5. Ruling R41 — audit output is not candidate state

The ephemeral parse may produce, **for audit and counting purposes only**: forms; accessions; CIKs;
filing dates; report dates; acceptance timestamps; XBRL flags; inline-XBRL flags; and
primary-document metadata.

**These audit values do not constitute** frozen E0 census state, candidate records, candidate
evidence, candidate resolutions, selection eligibility, amendment-purpose classifications,
amendment relationships, or manifest inputs.

**No ephemeral output may be cited later as durable real-pilot evidence** unless a separately
authorized stage persists and validates it under the accepted M3.3 architecture.

**Cite as:** *Decision 079 R41 — Audit Output Is Not Candidate State.*

## 6. Process rule P8 — validator conflict

Adopted for future review-packet design, extending [Decision 076](decision_076_m3_3_preacceptance_infrastructure_optimization.md)
§12's **P1–P7**. This is a **process** rule; it changes no methodology.

8. **P8 — artifact-hash / validator-conflict rule.** When a byte-exact frozen artifact SHA matches
   but a lower-level ad-hoc validator reports a contradiction: (1) do not declare identity mismatch
   immediately; (2) classify `VALIDATOR_CONFLICT`; (3) inspect the validator; (4) structured-parse
   the artifact; (5) require independent confirmation before rejecting the artifact. **Hash equality
   does not prove every semantic claim** — it means a weaker checker cannot silently overrule exact
   frozen artifact identity.

## 7. The exact audit boundary

**Purpose.** Measure the **real** amendment-candidate population and structured-data coverage from
**already acquired, accepted M3.2 raw source objects**, so the owner can design the next source
stage on measured facts rather than on an unmeasured catalog zero.

### 7.1 Authorized

- **Read-only** access to the accepted M3.2 private evidence root, using true OS-level read-only
  handles where SQLite is involved.
- **Pure / ephemeral** parsing of already-acquired raw SEC objects.
- **In-memory or session-scratch** analysis only, the scratch directory lying outside both the
  repository and `EV_ROOT`.

### 7.2 Prohibited

M3.3-E0 durable parsing; writes to the accepted catalog; candidate snapshot construction;
selection; persistence; seal; manifest; network; SEC retrieval; HTTP; reacquisition.
**`REQUEST_CEILING` is 0**, and `NETWORK_REQUESTS`, `SEC_REQUESTS`, and `HTTP_REQUESTS` must each
end at **0**.

### 7.3 Raw-source boundary

Use **only** raw objects already bound to accepted M3.2 plan sources. **Do not traverse every
plausible raw file.** Accepted `census_plan_sources` and `census_source_observations` provenance
establishes which local raw objects belong to the accepted M3.2 acquisition.

Relevant source classes: `sec_bulk_submissions`; `sec_submissions_entity` / historical
representation where materialized inside the bulk archive; and `sec_full_index_company`. Full-index
objects are a **corroboration and diagnostic** layer (§7.6). Unrelated ticker, SIC, and calendar
objects are **not** parsed for amendment population unless a specific governed field requires it.
**No network fallback. No alternate source URL.**

### 7.4 Parser discipline

Reuse the **accepted pure parser machinery** — preferring
`src/disclosure_drift/sec/parsers/submissions.py` and
`src/disclosure_drift/sec/parsers/full_index.py` with the accepted canonical normalization helpers
in `src/disclosure_drift/sec/identifiers.py`. **Do not write a new independent SEC parser** unless
the accepted parser genuinely cannot expose a required field. A small audit adapter is permitted
**only** in session scratch outside the repository, must call the accepted parsing and normalization
functions, and must not duplicate parser semantics.

**Machine-readable first** (Decision 076 §12, P6). **Do not OCR. Do not regex raw JSON as a
substitute for the parser.**

### 7.5 Frozen amendment forms

| Class | Forms |
|---|---|
| Amendment-eligible | **`10-K/A`**, **`10-KT/A`** |
| Original-compatible | **`10-K`**, **`10-KT`** |

**No other form is added** — not `20-F/A`, not `40-F/A`, not `10-D`, not `8-K`, not any other —
unless an accepted rule explicitly makes it part of the M3.3 amendment candidate universe.

### 7.6 What the audit reports

Deduplicated by accepted canonical accession identity, with plain ↔ dashed consistency verified and
**no new precedence policy invented**: population and distinct entities; by form, year, and cohort;
acceptance-timestamp source coverage under the frozen strict 14-digit SEC rule; XBRL and
inline-XBRL coverage; `primaryDocDescription` **presence and absence only**; the original-filing
lookup diagnostic; a full public accession inventory in **presentation order**; and full-index
corroboration. **A materially conflicting duplicate is reported, never silently resolved.**

### 7.7 What the audit may not conclude

It **may not** classify amendment purpose, keyword-search or infer purpose from
`primaryDocDescription`, select a parent, assign `amendment_relationship`, use date proximity or
accession order as linkage, or grant linkage credit. **Full index may corroborate or conflict; it
may never overwrite the higher-authority submissions facts, and no index-only accession becomes an
amendment candidate.** The prohibited inferences listed in Decision 078 §4 are unchanged, and
**neither quota is lowered, deferred, or proxied** — `linked_amendment_entities` remains **8**,
`amendment_purpose_categories` remains **3**.

## 8. Nonmutation

The audit runs **after** this record's governance-only commit and **does not mutate the repository
or the accepted evidence**. Before and after, the session records HEAD, working-tree state, receipt
identity, accepted raw-object count, `census_source_observations`, `census_plan_sources`,
`census_accessions`, `census_parser_runs`, `census_parsed_records`, and the catalog main-DB and WAL
size and mtime.

**Required after-state:** HEAD unchanged; working tree clean; raw-object count unchanged; receipt
identity unchanged; catalog logical counts unchanged; `census_parser_runs`, `census_parsed_records`,
and `census_accessions` all still **0**; `parser_state` still `not_started` for all **76** plan
sources; main DB and WAL size and mtime unchanged; no journal created, no WAL created, no
checkpoint, no catalog write, no repository write, no commit, no push, no tag.

**SHM is a non-governed reader artifact.** Its size or mtime may move under a genuine read-only WAL
connection. Movement is reported as **reader-side SHM activity**, never as durable catalog mutation,
provided the main DB and the WAL are unchanged. **No physical SQLite hash becomes governed
identity.**

## 9. Privacy

The audit reports **counts and public SEC identifiers**. It **never** prints `EV_ROOT`, the absolute
receipt path, any parent path, or any other private absolute pathname. Private-root recovery uses
the exact bounded mechanism already proven successful: a search of the current user's `HOME` for the
exact suffix `runs/m3_2_decision_062_sic_continuation/execution_receipt.json`, validated by the
frozen receipt SHA-256 and structured identity facts, requiring exactly one candidate, one SHA
match, and one identity match. **If session permission policy blocks that exact search, STOP** —
alternate formulations are not attempted and filesystem authority is not broadened.

## 10. Findings returned to the owner

**OBS-1 — R39 ruling-number collision.** Decision 078 §3 and this record both define a ruling
numbered R39. Recorded per §1 with a mandatory decision-qualified citation convention. **Not
corrected here**, because renumbering an owner-issued ruling is the owner's act. Renumbering this
record's R39 to **R42** is available and would close it permanently.

## 11. What is unchanged

No research definition, hypothesis, threshold, cohort window, outcome, or seed. No selector, reserve
selector, candidate behavior, offline-parsing behavior, selection store, manifest or release
hashing, migration, or configuration. No evidence, receipt, snapshot, or selection identity. No
source, no test, and no config is touched by the governance commit. The preregistration is
untouched, every accepted review artifact remains immutable, `m3.2-complete` is unmoved, and
migrations remain `0001`–`0013`. Tracked network switches remain `false` / `false`.

## 12. What this record does not authorize

It does **not**: authorize the real durable offline parse (**M3.3-E0**) or progression to
**M3.3-E1** or **M3.3-E2**; authorize a real snapshot, selection, manifest, or root; approve a root
or begin **M3.4**; enable network access; authorize an SEC request, reacquisition, or re-retrieval;
authorize a migration; authorize **writing to** `EV_ROOT`, the accepted real private catalog, or any
M3.2 private evidence; close either real-path feasibility gate; resolve real acceptance-ordering
adequacy; lower, defer, or proxy any quota; reverse Decision 071's **IN-2**; create a production
amendment-purpose classifier; move `m3.2-complete`; or create any tag.

**Acceptance ordering remains `PENDING FUTURE AUTHORIZED E0 VERIFICATION`** (Decision 074 R34). This
audit measures **source coverage** for it and does not resolve
`REAL_ACCEPTANCE_ORDERING_ADEQUACY`.

## 13. Next authorized action

The **Decision-079 pre-E0 ephemeral real-source parse and amendment-inventory audit**, executed
**once** under §7, then **return to Sol/GPT** for owner adjudication. Audit results are **not
committed** in this pass. **E0 does not begin**, no acquisition begins, and no implementation
begins. `REAL_PRIVATE_EPHEMERAL_PARSE_AUDIT_AUTHORIZATION` is **CLOSED after this audit**.

```text
M3_3_PRE_E0_EPHEMERAL_REAL_SOURCE_INVENTORY_AUDIT_AUTHORIZED
REAL_PRIVATE_EPHEMERAL_PARSE_AUDIT_AUTHORIZATION = YES — ONE AUDIT, CLOSED AFTER IT
M3_3_E0_DURABLE_PARSE_AUTHORIZATION = NO
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
```
