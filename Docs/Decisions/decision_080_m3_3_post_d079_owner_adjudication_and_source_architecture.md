# Decision 080 — Post-D079 Owner Adjudication and Single-Artifact Source Architecture

```text
STATUS: ACCEPTED — OWNER POST-D079 ADJUDICATION AND SOURCE-ARCHITECTURE RULINGS
DATE: 2026-08-14
OWNER: Sol/GPT
OUTCOME: M3_3_DECISION_079_REAL_AMENDMENT_INVENTORY_OWNER_ACCEPTED
IMPLEMENTATION_AUTHORIZATION: NONE — GOVERNANCE RECORDING ONLY
REAL_PRIVATE_EPHEMERAL_PARSE_AUDIT_AUTHORIZATION: CLOSED — THE SINGLE DECISION-079 AUDIT IS CONSUMED
M3_3_E0_DURABLE_PARSE_AUTHORIZATION: NO
REAL_SNAPSHOT_AUTHORIZATION: NO
REAL_SELECTION_AUTHORIZATION: NO
MANIFEST_ROOT_CONSTRUCTION_AUTHORIZATION: NO
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

**This record does three things and nothing else.** It records Sol/GPT's owner acceptance of the
Decision-079 ephemeral audit's findings as a frozen source-inventory fact set (§2); it freezes four
owner rulings — **R42** (§3), **R43** (§4), **R44** (§5), **R45** (§6) — plus the R39/R42 collision
disposition (§7); and it records the six architecture investigations the owner ordered — the
multi-registrant representation (§8), the verified amendment-purpose evidence protocol (§9), the
explicit original/linkage evidence rule (§10), the fixed source-verification sample (§11), the
request economics (§12), and the E0 ordering verdict (§13) — **each as a finding or proposal
PENDING OWNER ACCEPTANCE, not as accepted methodology.**

**It closes neither real-path gate.** `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` (Decision
073 R30) and `M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` (Decision 074 R32) both remain
**OPEN / ACTIVE**, separately auditable, and never merged. **It authorizes no real execution and no
acquisition**: M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 each remain a separate, unissued owner gate;
network, SEC, and HTTP remain **NONE**; the request ceiling remains **0**.

**Where this record and an earlier governing record disagree**, it controls only on the points it
names. Decisions 001–079 remain accepted and byte-unchanged.

---

## 1. Entry state — verified

Verified live by `scripts/verify_target.py` (9 / 9 checks passed) plus direct Git corroboration, with
no fetch, pull, reset, clean, or stash:

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD == `origin/main` | `3c0b7592e94e3c5c1c65201643aa848c664062c7` |
| HEAD tree | `93b396c4bdbcebcc767741cba202640c26be509a` |
| HEAD parent | `3f8c754fc7e12b10e5015c33fc76b2fc2c3996b3` |
| Accepted M3.3-I/R executable target | `feaeaa4163587730d6b12ebb87aabf2fc215c8f3` (ancestor of HEAD) |
| `m3.2-complete` tag object | `2865a1479e4576dc18a4098c928b278812f38d00` |
| Working tree at entry | clean |
| Migration chain | `0001`–`0013` |
| Tracked network switches | `network.enabled` `false`; `network.m3_acquire_enabled` `false` |

## 2. The Decision-079 audit findings — owner accepted

```text
M3_3_DECISION_079_REAL_AMENDMENT_INVENTORY_OWNER_ACCEPTED
```

The single audit Decision 079 §7 authorized was executed once, ephemerally, with **zero network
requests and zero durable parse state**, and its §8 nonmutation postconditions held. Sol/GPT
**accepts its findings as a frozen source-inventory fact set**:

| Fact | Value |
|---|---|
| `REAL_RAW_TOTAL_AMENDMENT_CANDIDATES` | **46912** |
| `FROZEN_COHORT_AMENDMENT_CANDIDATES` | **20258** |
| — `development` | 16401 |
| — `transition` | 1750 |
| — `primary_test` | 861 |
| — `prospective` | 711 |
| — `monitoring` | 535 |
| By form — `10-K/A` | 46775 |
| By form — `10-KT/A` | 137 |
| Raw rows before deduplication | 48199 |
| Multi-registrant amendment accessions | **568** (each appearing under 2–65 registrant CIKs; every duplicate conflict includes differing CIKs) |
| Same-CIK / report-date compatible-original diagnostic — zero matches | 4677 |
| — exactly one match | 42159 |
| — multiple matches | 75 |
| — missing report date | 1 |
| `has_xbrl` true / false | 8424 / 38488 |
| `has_inline_xbrl` true / false | 4199 / 42713 |

**Decision 079 R41 is unchanged and controls the status of these values**: they are owner-accepted
**audit facts about the accepted raw sources**, not census state, candidate state, evidence,
resolution, selection eligibility, purpose classification, amendment relationships, or manifest
inputs. **No ephemeral row is ever represented as durable E0 candidate evidence.** A later
authorized durable stage that recomputes them must reconcile against these frozen totals and stop on
mismatch (§11.4).

`REAL_PRIVATE_EPHEMERAL_PARSE_AUDIT_AUTHORIZATION` is now **CLOSED**: the one authorized audit is
consumed, exactly as Decision 079 §13 provided.

## 3. Ruling R42 — artifact-hash / validator-conflict rule (operative alias)

Adopted **prospectively** as the live citation for the validator-conflict rule, with the same
substantive meaning as Decision 079 §3's ruling:

When a byte-exact, owner-frozen artifact SHA-256 matches but a weaker ad-hoc checker contradicts it:

1. classify **`VALIDATOR_CONFLICT`**, never `ARTIFACT_IDENTITY_MISMATCH`;
2. inspect the checker;
3. structured-parse the artifact correctly;
4. require independent confirmation before rejecting the artifact.

**Hash equality does not prove every semantic field. But a weaker checker may not silently overrule
exact artifact identity.** A false `NO_IDENTITY_MATCH` is prohibited.

**Future operative citations MUST use `Decision 080 R42`**, never a bare "R39". Historical
decision-qualified citations remain valid and untouched (§7).

**Cite as:** *Decision 080 R42 — Artifact-Hash / Validator-Conflict Rule.*

## 4. Ruling R43 — acceptance-datetime source authority

Decision-079 findings **MAJOR-1** and **MAJOR-2** are accepted as **SOURCE findings** about the
entity-submissions acceptance values. The following remedies are **REJECTED and prohibited**:

- taking the first 14 significant digits of a submissions `acceptanceDateTime` value;
- timezone arithmetic over the submissions ISO values;
- choosing among duplicate submissions values;
- registrant-based timestamp precedence.

**The frozen strict 14-digit rule is unchanged** (Decision 010: raw SEC acceptance format
`YYYYMMDDHHMMSS`; `acceptance_date_sec` from the first eight characters), and Decision 019's
strict-later ordering remains **fail-closed** exactly as Decision 074 R34 restated it.

**Owner finding from primary SEC documentation.** The SEC Complete Submission Text / EDGAR header
carries `<ACCEPTANCE-DATETIME>YYYYMMDDHHMMSS`, which the SEC identifies as the EDGAR-assigned
acceptance date/time. Therefore:

**When a future owner-authorized source stage acquires and validates a Complete Submission
Text/header for an accession, its native `<ACCEPTANCE-DATETIME>` is the intended higher-authority
source for the frozen 14-digit acceptance value.** Entity-submissions `acceptanceDateTime` values
remain lower-authority observations/corroboration: they may surface conflicts, but they never
override the native accession-level header. This is exactly the authority relation Decision 012 §4
already defines — the native header is the level-1 `filing_level_metadata` class, defined and
deliberately deferred, whose later activation is a data change rather than a policy change (plus the
bounded source-registration the resolver requires for a new source identifier).

**Until the native source exists for a required accession, current fail-closed behavior remains.**
This ruling does **not** resolve `REAL_ACCEPTANCE_ORDERING_ADEQUACY`, which remains **PENDING FUTURE
AUTHORIZED E0 VERIFICATION** (Decision 074 R34).

**Cite as:** *Decision 080 R43 — Native Accession-Level Acceptance Authority.*

## 5. Ruling R44 — legacy original forms

The original-compatible forms remain frozen as exactly **`10-K`** and **`10-KT`**, and the
amendment-eligible forms remain exactly **`10-K/A`** and **`10-KT/A`** (Decision 079 §7.5).
**`10-K405`, `10KSB`, `NT 10-K`, and every other historical form are NOT added.**

An amendment without an accepted compatible original simply cannot satisfy linked-amendment
coverage. **No quota is weakened, and no historical form is promoted into the pilot universe merely
to increase coverage.** The 4677 zero-match rows in the §2 diagnostic are in part a consequence of
this frozen boundary, and that consequence is accepted rather than engineered around.

**Cite as:** *Decision 080 R44 — Legacy Original Forms Excluded.*

## 6. Ruling R45 — Complete Submission Text as preferred source candidate

Owner external-source research establishes that a **single SEC accession-level Complete Submission
Text artifact** can contain:

1. the native `<ACCEPTANCE-DATETIME>` header (§4);
2. the amendment's primary filing body;
3. Inline/XBRL facts where supplied, including `dei:AmendmentDescription` when
   `AmendmentFlag = true`;
4. an Explanatory Note that may explicitly state the original filing and the purpose of the
   amendment.

**This is a SOURCE-CANDIDATE ruling, not acquisition authority.** Future source design **prefers
evaluating the Complete Submission Text as the single-artifact source** serving the acceptance
authority (§4), the purpose-evidence path (§9), and the linkage-evidence path (§10) at once — the
one-shared-source preference Decision 078 §5 states.

**Important qualification, frozen with the ruling:** `has_xbrl = true` or `has_inline_xbrl = true`
does **not** imply `AmendmentDescription` exists. A verified current `10-K/A` example carries inline
XBRL with `AmendmentFlag = false` and no `AmendmentDescription`, yet **does** have a filing-body
Explanatory Note stating its original filing and amendment purpose. **No XBRL-only route may be
designed as though it covers every amendment.**

**Cite as:** *Decision 080 R45 — Complete Submission Text Preferred Source Candidate.*

## 7. R39 / R42 collision disposition

The accepted historical numbering collision (Decision 079 §1, OBS-1) is disposed **without
rewriting either accepted record**:

| Citation | Status |
|---|---|
| **Decision 078 R39** | Historical / read-only — the pre-E0 feasibility-audit ruling, as issued (Decision 078 §3) |
| **Decision 079 R39** | Historical — the validator-conflict ruling, as issued (Decision 079 §3) |
| **Decision 080 R42** | **Operative** — the prospective alias of the validator-conflict rule (§3 above) |

Future live citations use **Decision 080 R42**. Historical decision-qualified citations remain
valid. **A bare "R39" remains prohibited.** OBS-1 is **CLOSED**.

## 8. Multi-registrant architecture — findings and recommendation — PENDING OWNER ACCEPTANCE

The owner question: 568 accessions appear under 2–65 registrant CIKs, and every duplicate conflict
includes differing CIKs. The accepted schema, code, and rulings were inspected before proposing
anything: migrations `0003` and `0009`; `sec/accession_resolution.py`; `sec/census.py`;
`m3/candidate_snapshot.py`; Decision 008 §§1, 6; Decision 012 §§2–4, 8; Decision 019 §§6.2–6.3;
Decision 067 §9 (OR-1); Decision 068 §8 (R16-C1); Decision 072 §§2–4 (R22–R24).

### 8.1 What the accepted architecture actually does — findings of fact

| # | Finding |
|---|---|
| **F-MR-1** | `census_accessions` (migration `0003`) keys on `accession_plain` and carries exactly one `NOT NULL` `registrant_cik_numeric` plus one `submitter_cik_numeric`. Accession identity is **already accession-level** — the canonical accession number — exactly as Decision 072 §1 stated |
| **F-MR-2** | The accepted ingest path (`sec/census.py`) inserts the accession row with `ON CONFLICT(accession_plain) DO UPDATE SET latest_observed_at_utc` only. For a multi-registrant accession the **anchor column therefore holds the first-parsed file's CIK** — a parse-order artifact — while every later file's fields land append-only in `census_accession_observations` |
| **F-MR-3** | The Decision 012 resolver (`sec/accession_resolution.py`) treats `registrant_cik` as **material**; N differing equal-authority `entity_submissions` observations resolve **`unresolved`** with `ACCESSION_FIELD_UNRESOLVED_EQUAL_AUTHORITY`, `ACCESSION_FIELD_CONFLICT_MATERIAL`, and the release-blocking `ACCESSION_REGISTRANT_CONFLICT_PRESERVED` (Decision 012 §8). The canonical projection deliberately never rewrites `registrant_cik_numeric`, so **the first-write value persists in the anchor column while the resolution truthfully records `unresolved`** |
| **F-MR-4** | The accepted candidate builder (`m3/candidate_snapshot.py`) reads `anchor_cik_numeric` **directly from that column**, feeds it into `accession_tie_break_sha256`, attributes the accession to that entity, and — via the R19 §4.12 path — maps every material-unresolved accession onto its anchor entity as `material_source_or_identity_conflict` |
| **F-MR-5** | Per-entity submissions-history aggregation groups `census_accessions` rows **by the single anchor column**, so a joint filing appears in **only the first-parsed registrant's history** — although every co-registrant's own accepted submissions file lists it. On real data this under-populates co-registrant histories for the R19 event predicates and R20 control predicates |
| **F-MR-6** | `pilot_candidate_accession_registrants` (migration `0009`) already represents the full registrant set — `role ∈ {anchor, associated, submitter_only}` with exactly one anchor enforced at freeze — and Decision 072 R23 populates `associated` from `company.idx`. Decision 008 §1 anticipated exactly this edge entity (`inventory_accession_registrants`, "supports multiple registrants"), and Decision 008 §6 names "multi-registrant representation cannot be preserved without collapsing filings" as an explicit revisit trigger |

**F-MR-2 through F-MR-5 together constitute a newly discovered material-defect class on real
multi-registrant data** — the accepted I/R passed on synthetic fixtures that never exercised the
568-row real shape — and are returned to the owner as the ground for a bounded correction under
Decision 078 §1's reopen standard. Nothing here is a claim that any real row was durably written:
no parse has run, and the structural zeros stand.

### 8.2 Answers to the owner's four questions

| Q | Answer |
|---|---|
| **A** — does an existing accepted rule supply a lawful canonical accession anchor? | **NO.** The accepted resolver's lawful output for the 568 is `unresolved` (fail-closed); the only single value the implementation produces is the first-write CIK — the ingestion-order precedence Decision 012 §2 exists to reject, and which the owner's prohibited list ("first appearance", "record order") covers. Decision 072 R23's "already resolved census accession anchor" **presupposes** a resolved anchor and does not itself resolve one. Deeper: for a genuinely joint filing, a single "the registrant" is **not a fact that exists in the evidence** — the resolver is being asked a single-valued question whose truthful answer is a set |
| **B** — can every substantive registrant association be preserved without changing an existing governed identity? | **YES.** `census_accession_observations` already preserves every per-file observation append-only, and `pilot_candidate_accession_registrants` already represents the role-tagged set. **No real governed identity exists yet** — the catalog zeros are structural, no E0/E1 has run — so correcting the anchor/association semantics **before** E0 changes no frozen identity. It does require a bounded owner-authorized correction of the accepted I/R architecture (decision + code + tests), justified by the F-MR findings |
| **C** — are the submissions-source duplicates corroborating associations, conflicting observations, or a new representation? | **They are substantive registrant associations forced through a single-valued observation model.** Each per-file listing truthfully asserts "this CIK is a registrant of this accession"; flattening those assertions into competing sole-registrant claims **manufactures** a conflict. Where per-file core fields (form, dates, flags) agree, the duplicates **corroborate** the accession facts and **jointly constitute the association set** — the same semantic content `company.idx` supplies at lower authority. A **genuine** conflict exists only where core fields disagree across sources, and the existing conflict machinery is correct for that case. What is required is a new explicit **representation rule** (association-set semantics), not a new table |
| **D** — is a migration actually required? | **NO for multi-registrant representation** — migration `0003`'s observations plus migration `0009`'s registrant-role table suffice, and the fix is rule/code-level. **YES, separately, for the future verified-evidence layer** (§9.3, §10.3): migration `0009` deliberately excludes `verified` from every candidate evidence-level CHECK, so document-level verified evidence cannot be persisted under the current schema at all |

### 8.3 Recommendation — PENDING OWNER ACCEPTANCE

Preferred principle honored: accession identity stays accession-level; truthful substantive
registrant associations are preserved; no arbitrary one-CIK precedence is invented.

| # | Proposal |
|---|---|
| **MR-1** | **Association-set semantics.** Rule that an entity-submissions per-file accession listing is an **association-membership observation** — never a competing sole-registrant claim. The submissions-derived association set is the union of distinct canonical CIKs across the accepted files listing the accession; the `company.idx` set corroborates it at its lower authority (Decision 072 R23 unchanged). A registrant-identity **conflict** exists only on per-source core-field disagreement — set-membership union alone never raises one |
| **MR-2** | **Accession identity unchanged.** The canonical accession number remains the sole accession identity everywhere (already true — F-MR-1) |
| **MR-3** | **Anchor disposition — owner must choose one.** **(a) Recommended:** keep the single-anchor schema; for a multi-registrant accession the anchor is the registrant association whose CIK equals the accession's **intrinsic submitter CIK** (embedded in the accession number itself) when the submitter is a member of the association set; otherwise the anchor is **review-required and the accession is excluded from candidate rows with a counted, reported reason** — fail-closed, never guessed. This designation is evidence-grounded in EDGAR's own accession identity, but it is adjacent to the prohibited "filing agent" precedence and therefore **requires explicit owner acceptance**, plus an E0-time measurement of the submitter-∈-set rate over the 568 (zero new requests). **(b) Higher-fidelity alternative:** relational anchor — per-entity candidate accession rows — which is a migration plus an OR-1 preimage revision (lawful pre-E0, since no real identity exists, but a substantially wider reopening). **(c) REJECTED:** fail-closed exclusion of every multi-registrant accession — it structurally defeats the Decision 072 R24 hard multi-registrant quota |
| **MR-4** | **History-aggregation correction.** Per-entity submissions history (R19 events, R20 controls) must include a joint accession in **every substantive co-registrant's** history, because each co-registrant's own accepted file lists it (fixes F-MR-5) |
| **MR-5** | **Conflict-flag correction.** Once MR-1 is accepted, association multiplicity alone is no longer a `material_source_or_identity_conflict`; genuine core-field conflicts keep the flag and all existing fail-closed behavior (fixes the false-positive limb of F-MR-4) |

**None of MR-1–MR-5 is implemented, and none is accepted methodology, until a separate owner
ruling adopts it.**

## 9. Verified amendment-purpose evidence — architecture answer — PENDING OWNER ACCEPTANCE

Inspected: Decision 014 §§1, 6; Decision 071 §6 (IN-2); Decision 073 §§2, 6–7; migration `0009`.

**Answer: YES — a bounded, pre-registered, adjudicated document-evidence protocol is compatible
with the accepted governance architecture, and it requires a new owner ruling to exist.** Decision
014 §1 already defines the `verified` level as "retrieval-verified, document-level evidence" and
Decision 014 §6 already places definitive purpose classification at exactly that level; what has
never existed is the accepted protocol, the accepted source, and the schema to persist it. **IN-2
is not reversed and no classifier is invented**: the production builder continues to infer nothing —
under this design it would **consume a frozen, owner-accepted adjudication table** as evidence, and
keyword/substring/regex/filename/LLM/operator-intuition classification all remain prohibited.

### 9.1 The protocol design (for owner acceptance, not for use)

| # | Element |
|---|---|
| **AP-1** | **Population totality.** Every accession in the precommitted deterministic population (§11 sample; any later enrichment wave) is adjudicated. No post-hoc subset, no skipping after reading, every outcome recorded — including "insufficient text" |
| **AP-2** | **Protocol frozen before the first document is read**: the three frozen Decision 014 §6 categories verbatim; written decision rules; an explicit abstention rule (insufficient or ambiguous text ⇒ no category); the record form; a version identifier (`amendment-purpose-adjudication/1.0`) |
| **AP-3** | **Artifact binding.** Adjudication reads only the accepted stored Complete Submission Text artifact, identified by accession number and frozen SHA-256. No live browsing, no substitute copy |
| **AP-4** | **Dual independent adjudication**, blind to each other, blind to selection state, and blind to every outcome value (Decision 015; leakage register L15/L19 unchanged) |
| **AP-5** | **Evidence record per accession**: category or abstention; verbatim quoted supporting span(s) with location in the frozen artifact; artifact SHA-256; adjudicator identifier; protocol version; UTC timestamp |
| **AP-6** | **Agreement rule.** Exact category agreement ⇒ `verified`. Disagreement ⇒ one documented joint resolution citing exact text; irreconcilable ⇒ `conflicting`, no quota credit. Never averaged, never majority-by-silence |
| **AP-7** | **Freeze and seal.** The complete adjudication table is canonically serialized and hashed through the existing accepted `release/hashing.py` machinery under a new domain (no second hash implementation — the Decision 067 §9 / R16 discipline), owner-accepted, then immutable. The deterministic pipeline consumes only the frozen table |
| **AP-8** | **Category determinism after freeze.** Identical frozen table + identical catalog ⇒ identical candidate rows, independent of adjudication order |
| **AP-9** | **Independent review.** A separate epoch verifies 100% of quoted spans mechanically against the frozen artifacts (byte-existence at the stated locations) and re-adjudicates a deterministic subsample |
| **AP-10** | **No metadata overwrite.** An adjudicated category never overwrites a structured fact; a structured/narrative contradiction (e.g. `AmendmentFlag` disagreement) is a recorded review condition under the Decision 008 §2.2 non-conflation rule |

### 9.2 What acceptance of this protocol would and would not do

It would create the accepted evidence route Decision 073 §6 said "a later owner decision may
address"; a `verified` category could then satisfy the three-category hard quota under Decision 014
§1's own rules. It would **not** lower the quota (three distinct categories, hard), reverse IN-2,
create any production classifier, or make any classification now. **Zero classifications are
performed by this record.**

### 9.3 Schema consequence

Migration `0009` excludes `verified` from every candidate evidence-level CHECK by design (its
metadata-only M2.3 scope), and `amendment_purpose_quota_eligible` requires
`amendment_purpose_evidence_level = 'provisional'`. Persisting verified purpose evidence therefore
**requires a future migration** (widened CHECKs plus adjudication-evidence storage) — designed and
authorized only by a later owner ruling. **No migration is authorized here.**

## 10. Explicit original / linkage evidence — architecture answer — PENDING OWNER ACCEPTANCE

Inspected: Decision 008 §§2, 2.1, 2.2, 6; Decision 018 §§10, 10.1–10.4; Decision 074 §3 (R32);
Decision 078 §4; `sec/amendments.py`; migration `0009`.

**Verdict: `REQUIRES_NEW_OWNER_RULING`.**

**Exact rationale.** The proposed mechanism — an explicit statement in the amendment's own stored
primary document ("this Amendment amends the Annual Report on Form 10-K … filed on YYYY-MM-DD"),
resolved against the accepted E0 catalog to **exactly one** same-registrant, compatible-form,
exact-stated-date original — is **not prohibited in principle**. It is precisely Decision 008
§2.1's standard ("evidence links the amendment to a specific original accession"): the date/form
proposition is **asserted by the amendment itself**, and the catalog lookup merely resolves that
explicit assertion to an accession. It is not date proximity, not same-report-date inference, not
accession ordering, and not guessing — none of Decision 078 §4's prohibited inference routes is
used. Decision 078 §4's own carve-out shape ("… unless that text is already inside an accepted
stored source **and** is itself authorized evidence") states the two conditions that **do not
currently hold**:

1. **the Complete Submission Text is not yet an accepted stored source** — no acquisition, storage,
   or provenance authority exists for it (Decision 074 R32 explicitly declined to authorize filing
   bodies); and
2. **no accepted rule defines explicit-statement resolution as an authorized evidence class**, and
   migration `0009` cannot persist `verified` linkage evidence at all (§9.3).

### 10.1 What the new owner ruling must fix (proposal)

| # | Required content |
|---|---|
| **L-1** | Admit the accession-level Complete Submission Text as an accepted stored source class, acquired and stored under the same raw-object governance as the accepted M3.2 objects, and registered in the Decision 012 §4 authority map at level 1 (`filing_level_metadata`) |
| **L-2** | Define the **explicit-statement linkage evidence class**: an explicit statement in the amendment's own accepted stored document identifying its original by form and exact filing date (or by accession number), extracted verbatim with location and adjudicated under the §9 protocol discipline — mechanical verification where the statement carries a machine-checkable accession number |
| **L-3** | **Uniqueness rule.** Registrant identity plus compatible original form plus exact stated filing date must resolve to **exactly one** accepted catalog accession. Zero or multiple ⇒ `possible_amendment_of` / `unresolved_amendment`, fail-closed — never nearest-date, never proximity |
| **L-4** | **Conflict rule.** A statement/catalog disagreement (form or date mismatch, absent original) stays unresolved with review; it is never repaired |
| **L-5** | **Ordering unchanged.** Decision 019's strict-later acceptance ordering and the Decision 074 R34 report stand; an amendment accepted before its resolved original stays unresolved-plus-review under Decision 008 §2.2 |
| **L-6** | **Joint-filing identity.** "Same canonical CIK" is evaluated over registrant-association sets under whichever §8.3 disposition the owner accepts; until then, resolution is defined only for the single-registrant case |
| **L-7** | **Evidence level and schema.** The resolved state satisfies Decision 018 §10.4's evidence requirement at `verified`, persisted only after the §9.3 migration exists |
| **L-8** | **Quota mechanics unchanged.** `amends_original` still contributes only when the resolved root original is co-selected in the same joint run (Decision 018 §10.4), and `linked_amendment_entities` remains **8**, hard |

**No real accession is resolved by this record**, and the §2 diagnostic (42159 exactly-one rows) is
context, never linkage evidence.

## 11. Fixed bounded source-verification stage — design only — PENDING OWNER ACCEPTANCE

A small public-SEC verification stage, **fixed before retrieval, designed here and NOT executed**.
Artifact class: `sec_accession_complete_submission_text` — one Complete Submission Text per sampled
accession, constructed from the accession's own identity. Body text is involved, which is exactly
why execution requires the L-1 owner ruling first.

### 11.1 Sample frame and strata

Selection uses **only** structural metadata frozen in §2 — never amendment purpose, never
filing-body knowledge, never convenience. Rare, decision-relevant strata are deliberately
oversampled, precommitted here transparently.

| Stratum block | Frame | Cells | Per cell | Subtotal |
|---|---|---|---|---|
| **Core** | the 20258 frozen-cohort `10-K/A` candidates | 5 cohorts × 3 XBRL classes (`no XBRL`, `XBRL without inline`, `inline`) = 15 | 6 | 90 |
| **S-KT** | all 137 `10-KT/A` | 1 | 10 | 10 |
| **S-MR** | the 568 multi-registrant accessions | 1 | 8 | 8 |
| **S-MULTI** | the 75 multiple-compatible-original rows | 1 | 8 | 8 |
| **S-ZERO** | the 4677 zero-compatible-original rows | 1 | 8 | 8 |
| **S-MISS** | the 1 missing-report-date row | 1 | 1 | 1 |

```text
SAMPLE_N = 125 (maximum; short cells report exact counts)
MAX_PHYSICAL_REQUESTS = 250 (at most 2 physical attempts per logical request)
```

### 11.2 Selection algorithm — deterministic, order-free, precommitted

Rank every frame member by ascending
`sha256("d080-source-verification/1.0:" + accession_plain)` and take cells in the fixed block order
above, skipping any accession already selected (blocks are disjoint). A cell with fewer members
than its target takes all and reports the shortfall; a Core shortfall reallocates within the same
cohort's other XBRL cells and is reported. **No stochastic step exists, so no seed is consumed; the
ranking is a fixed pure function of the frozen population.**

### 11.3 Measurements (every retrieved artifact, mechanical, no classification)

m1 native `<ACCEPTANCE-DATETIME>` present and strict-14-digit valid; m2 `AmendmentFlag`
present/value where XBRL exists; m3 `AmendmentDescription` present/nonempty; m4 explicit amendment
statement present (Explanatory Note or equivalent); m5 explicit original form named; m6 explicit
original filing date stated; m7 the stated original maps **uniquely** into the recomputed catalog
diagnostic; m8 document text sufficient for the §9 protocol — **recorded as present/absent only;
no category is assigned**. Acceptance counts are reported in the Decision 074 R34 field layout.

### 11.4 Stop conditions and success criteria

**Stop**: more than 6 cumulative hard retrieval failures (5%); any response outside the accepted
response policy; any request outside the frozen 125-accession list; a third physical attempt for
any logical request; recomputed population totals failing to reconcile with the §2 frozen totals;
any measurement that would require judgment beyond the precommitted mechanical definitions (the item
is recorded `UNDETERMINED`, never improvised). A failed accession is reported, **never substituted
after the fact**.

**Success**: ≥ 95% retrieval success; 100% of retrieved artifacts fully measured; reconciliation
clean; per-stratum rates for m1–m8 returned to Sol/GPT for the gate adjudications. **This stage
closes neither gate by itself** — it measures whether the R45 source can.

## 12. Future request economics — PENDING OWNER ACCEPTANCE

One Complete Submission Text fetch per sampled amendment accession; artifacts are immutable and
fully reusable across stages (verification-sample artifacts count toward enrichment; nothing is
refetched). Assumed artifact size ~2–50 MB.

| Option | Logical requests | Worst-case physical | Volume (est.) | Cache/reuse | Governance burden |
|---|---|---|---|---|---|
| **A — fixed verification sample (§11)** | 125 | 250 | ~1–4 GB | artifacts reused by B | one bounded acquisition ruling (L-1) + contract addendum; smallest |
| **B — deterministic bounded enrichment** | expected ~100–300; **precommitted ceiling 400** | 800 | ~3–12 GB | reuses A's artifacts and the E0 catalog | protocol (§9) + linkage ruling (§10) + migration (§9.3) + adjudication governance; moderate |
| **C — full population** | 46912 | 93824 | ~0.4–2.3 TB | total, but unnecessary | maximal — **REJECTED unless technically unavoidable, and it is not**: the hard quotas need 8 linked entities + 3 categories + reserves, orders of magnitude below the population |

**Option B's shape** (design only): deterministic hash-order waves of fixed size over the
frozen-cohort amendment population under the §11.2 ranking, each wave's membership fixed before any
document is read, adjudicated to totality (AP-1), with a precommitted stopping rule on **aggregate
sufficiency counts** (verified categories ≥ 3 distinct; linked-amendment entity witnesses ≥ 8 plus
reserve headroom), never on the content of any individual filing. Only amendment-side artifacts are
needed: the linkage mechanism (§10) reads the amendment's own statement and the catalog, not the
original's body. The true Option-B size depends on the §11 measured rates — which is exactly why A
precedes B. **Minimum acquisition consistent with non-cherry-picked evidence: A, then bounded B.
Never C.**

## 13. E0 ordering — verdict — PENDING OWNER ACCEPTANCE

Read: the accepted contract's M3.3-E0 definition (`Milestones/contracts/m3_3.md` §10.2, items 1–14,
R17/R18) and the accepted implementation (`m3/offline_parse.py`, `sec/census.py`,
`sec/accession_resolution.py`).

```text
E0_CAN_RUN_FAIL_CLOSED_BEFORE_ENRICHMENT
```

**Why.** E0's completeness, atomicity, and coverage conditions are **per-source**, not per-field:
every planned source receives exactly one R18 disposition, category-A sources must parse, and the
write set is the fixed R17 fifteen-table footprint. None of those conditions depends on acceptance
validity, amendment purpose, or amendment parentage. The fields at issue persist lawfully
unresolved:

| Field | E0 persisted state before enrichment | Basis |
|---|---|---|
| `acceptance_datetime_sec_raw` / `acceptance_date_sec` | raw preserved; derived value NULL wherever the strict 14-digit rule fails; `accepted_temporal_cohort = 'unresolved'` | R43; Decision 012 §3 — acceptance is **non-material**, audit-only |
| `amendment_relationship` | absent/unresolved for every accession (no accepted source field maps to it) | Decision 074 R32; material, but Decision 012 §2's blocking is scoped to dependents — the linked-amendment quota at E1, not E0 completion |
| `registrant_cik` (the 568) | resolution `unresolved` + `ACCESSION_REGISTRANT_CONFLICT_PRESERVED` recorded | Decision 012 §8; see the §8 caveat below |
| `report_date` conflicts | unresolved, reviewed | non-material |
| `amendment_purpose_category` | not an E0 field at all — candidate-layer (E1) | R17 write set |

No §10.2 item-12 stop condition is triggered by any of these states, and the R34 acceptance report
falls out of E0 as measured fact.

**Three binding caveats, stated with the verdict:**

1. **The enrichment ingest is NOT E0.** The accepted E0 input set is the M3.2 stored objects "and
   nothing else"; parsing later-acquired Complete Submission Texts is a **separate, new
   owner-gated stage** requiring its own definition (contract addendum), the L-1 source admission,
   and the §9.3 migration. Running E0 first does not change that, and a rerun of E0 over the same
   set remains an explicit owner authorization, never automatic (§10.2 item 5).
2. **Sequencing recommendation:** rule on the §8 multi-registrant disposition **before** E0.
   Otherwise E0 durably persists a first-write anchor for the 568 plus false §4.12 conflict
   classifications, recoverable afterwards only by an owner-authorized resolution-policy revision
   (`accession-resolution/2.0`-style re-resolution over the preserved observations — no
   reacquisition, but avoidable governance debt).
3. **E1 remains expected-infeasible before enrichment** on both open gates, and E1 is separately
   gated regardless — E0 completing never authorizes it (§10.2 items 11, 13).

**This verdict does not authorize E0.** M3.3-E0 remains a separate, unissued owner gate.

## 14. What is unchanged

No research definition, hypothesis, threshold, cohort window, outcome, or seed. No selector,
reserve selector, candidate behavior, offline-parsing behavior, selection store, manifest or release
hashing, migration, or configuration. No evidence, receipt, snapshot, or selection identity. No
source file, no test, and no config is touched by this governance commit. The preregistration is
untouched, every accepted review artifact remains immutable, `m3.2-complete` is unmoved, migrations
remain `0001`–`0013`, and tracked network switches remain `false` / `false`. Both real-path gates
remain **OPEN**, and `REAL_ACCEPTANCE_ORDERING_ADEQUACY` remains **PENDING FUTURE AUTHORIZED E0
VERIFICATION**.

## 15. What this record does not authorize

It does **not**: authorize the real durable offline parse (**M3.3-E0**) or progression to
**M3.3-E1** or **M3.3-E2**; authorize a real snapshot, selection, manifest, or root; approve a root
or begin **M3.4**; enable network access; authorize any SEC request, HTTP request, acquisition,
reacquisition, or Complete Submission Text retrieval; execute the §11 verification stage or the §12
enrichment; authorize a migration; adopt MR-1–MR-5, AP-1–AP-10, or L-1–L-8 as accepted methodology;
perform or authorize any amendment-purpose classification; resolve any real amendment parentage;
close either real-path feasibility gate; resolve real acceptance-ordering adequacy; lower, defer, or
proxy any quota; reverse Decision 071's IN-2; write to `EV_ROOT` or any accepted private evidence;
reopen the single consumed Decision-079 audit authorization; move `m3.2-complete`; or create any
tag.

## 16. Next authorized action

**Return to Sol/GPT for owner adjudication of the six PENDING items recorded here** — the §8
multi-registrant disposition (including the MR-3 anchor choice), the §9 purpose-evidence protocol,
the §10 linkage ruling (L-1–L-8), the §11 verification-sample design, the §12 request-economics
plan, and the §13 E0-ordering disposition. **No session may begin E0, any acquisition, or any
implementation on the strength of this record.**

```text
M3_3_DECISION_079_REAL_AMENDMENT_INVENTORY_OWNER_ACCEPTED
M3_3_DECISION_080_SOURCE_ARCHITECTURE_READY_FOR_OWNER_ADJUDICATION
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY = PENDING FUTURE AUTHORIZED E0 VERIFICATION
```
