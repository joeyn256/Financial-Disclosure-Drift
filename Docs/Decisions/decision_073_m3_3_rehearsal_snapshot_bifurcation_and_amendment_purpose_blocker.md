# Decision 073 — M3.3 Rehearsal-Snapshot Bifurcation and the Amendment-Purpose Real-Path Blocker

```text
STATUS: ACCEPTED — OWNER M3.3 REHEARSAL-SNAPSHOT BIFURCATION AND REAL-PATH BLOCKER
DATE: 2026-08-13
OWNER: Sol/GPT
OUTCOME: M3_3_I_R_BLK_1_REHEARSAL_ARCHITECTURE_OWNER_RESOLVED
IMPLEMENTATION_AUTHORIZATION: YES — THE SAME BOUNDED M3.3-I/R STAGE, RESUMED
REAL_PRIVATE_PARSE_AUTHORIZATION: NO
REAL_SNAPSHOT_AUTHORIZATION: NO
REAL_SELECTION_AUTHORIZATION: NO
MANIFEST_ROOT_CONSTRUCTION_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
PRIVATE_EVIDENCE_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: none
REQUEST_CEILING: 0
```

**This record resolves BLK-1 for rehearsal only.** It does **not** reverse IN-2, define a
production amendment-purpose classifier, defer or lower any quota, authorize real data,
or authorize M3.3-E0, M3.3-E1, M3.3-E2, or M3.4.
[Decision 070](decision_070_m3_3_i_r_implementation_authorization.md) remains the
still-unconsumed I/R implementation authority; Decisions 071 and 072 remain accepted.

**Where this record and an earlier governing record disagree**, it controls only on the
points it names. Decisions 001–072 remain accepted and byte-unchanged.

---

## 1. Owner acceptance of BLK-1

```text
M3_3_AMENDMENT_PURPOSE_BUILDER_FEASIBILITY_BLOCKER_OWNER_ACCEPTED
```

BLK-1 is **valid**, and the mechanical chain is accepted as stated:

1. the accepted candidate builder assigns **no** affirmative
   `amendment_purpose_category` from the authorized metadata;
2. Decision 071 **IN-2** forbids inventing one from form suffix, timing, generic linkage,
   company name, or similar unsupported metadata;
3. the accepted selector requires **three distinct** `amendment_purpose_categories`;
4. a `NULL` category produces **no witness**, and that quota sits in the subproblem's
   hard requirements;
5. therefore a builder-derived candidate snapshot **cannot currently produce a feasible
   joint selection**.

**This is not a selector defect, and not a builder defect under current IN-2.** It is an
evidence-availability and stage-architecture consequence.

## 2. Decision 014 remains authoritative

The three frozen purpose categories are unchanged: administrative/certification/
signature/exhibit-only; financial-statement/accounting/restatement/XBRL correction; and
narrative/business/risk/control/governance disclosure.

Decision 014 permits `provisional` **or** `unproven` at the metadata stage, but
`provisional` may satisfy the quota **only** where an accepted metadata-safe evidence
basis actually establishes the category, and `unproven` **never** satisfies it.

**This record creates no new metadata-safe classifier.** The production builder stays
conservative, and classification from any of the following remains forbidden: the `/A`
suffix alone; XBRL presence alone; filing timing; a newly invented primary-document
filename heuristic; amendment count; linkage state; company name; filing size. A later
owner decision may address the real evidence path separately.

## 3. Ruling R27 — Dual-Track Rehearsal Architecture

M3.3-I/R uses **two explicitly different rehearsal tracks**, serving different proof
obligations. **They may never be conflated.**

### Track A — builder-integrity track

Uses the **actual M3.3 candidate builder** over synthetic source observations through the
production offline-parse and candidate-construction path. It proves: offline parse; R17;
R18 as corrected by R22–R25; full-index multi-registrant materialization; R19 event
classification; R20 controls; R21 XBRL identity; SIC authority; the former-name payload;
registrant representation; the 2009/2010 candidate facts; OR-1; OR-2; R16-C1; the
structural fingerprint; snapshot atomicity and freeze; and deterministic reconstruction
of candidate content.

**Track A must additionally prove the currently expected selector disposition** —
`AMENDMENT_PURPOSE_QUOTA_INFEASIBLE` where no provisional metadata-safe category exists.
That is a **required negative integration test**. **The builder is not modified to make
Track A feasible.**

### Track B — downstream-feasible rehearsal track

May use an **explicitly governed rehearsal snapshot** constructed directly through the
accepted candidate schema, store, and loader fixture machinery. It exists **only** to
exercise logic downstream of candidate construction that requires a feasible selector
result.

It may assign exactly the three frozen categories to synthetic amendment accessions at
`evidence_level = provisional`, **only because the test fixture explicitly stipulates
those synthetic facts**. Those facts are **not** inferred from metadata, **not** a
production classifier, **not** real candidate evidence, **not** evidence that the real
pool is feasible, and **not** a methodology rule for E0 or E1. The fixture identifies
them as `SYNTHETIC_REHEARSAL_ONLY` in its construction and evidence documentation — a
documentation label only, never a persisted evidence-vocabulary value, and the persisted
candidate rows still use the existing governed schema values.

**Cite as:** *M3.3 Owner Ruling R27 — Dual-Track Rehearsal Architecture.*

## 4. Ruling R28 — Rehearsal Snapshot Bridge Equivalence

**Track B may not become an unrelated hand-crafted easy fixture.** A **paired**
construction is required: `A` the builder-derived sibling snapshot and `B` the explicitly
governed feasible rehearsal snapshot, **both originating from the same synthetic base
case design**. Before selector execution the two are compared mechanically, and every
substantive fact **not** dependent on amendment-purpose evidence must be equivalent —
entity identity, size, industry, history stratum, event flags, control classification,
primary-universe state, evidence levels and tie-break content; accession identity, anchor
CIK, form, filing and report dates, cohort, roles and eligibility, XBRL flags, amendment
linkage and parentage, `multi_registrant`, registrant rows, name-transition contribution,
fiscal-year-end facts, support/base/stress/control eligibility, the 2009/2010
support-target facts, non-amendment evidence levels and reason rows; and the full-index
facts — associated registrants, submitter-only noncontribution, and corroboration or
conflict behaviour.

The **only** permitted substantive candidate-field difference is the explicitly injected
synthetic amendment-purpose classification and its evidence. **Transitive** identity
differences are also permitted where that purpose difference propagates:
`amendment_purpose_category`; its evidence level; `amendment_purpose_quota_eligible`; its
evidence and reason rows; `amendment_purpose_resolution_sha256`; the candidate
table/family digests containing those rows; `snapshot_id`; `candidate_snapshot_sha256`;
and the later selection, run, seal, and manifest identities.

**No unrelated fact may differ merely to make selection easier.** The permitted
differences are an **explicit allowlist**, and the bridge test **fails** on any difference
outside it. This is what preserves the Decision-072 proof through Track B.

**Cite as:** *M3.3 Owner Ruling R28 — Rehearsal Snapshot Bridge Equivalence.*

## 5. Ruling R29 — Downstream Feasible Rehearsal Scope

Rehearsal scenarios requiring a **feasible** joint selection may use Track B: the joint
selector, quota satisfaction, reserves, persistence, independent reconstruction,
write-free replay, the selection-result seal, manifest construction and verification,
identical-root replay, Decision 023 **O1**, and downstream fault and atomicity behaviour.

The affected scenarios were identified as rehearsal scenarios **E3, E5, E7, and E8(a)**.
**That mapping is verified against the accepted contract before implementation, and where
the contract assigns a scenario differently the contract controls.** Scenario meanings are
never silently reassigned.

Every Track-B report states `FEASIBILITY SOURCE:
EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT`, and must never state or imply
`BUILDER_DERIVED_REAL_FEASIBILITY_PROVED`.

**Cite as:** *M3.3 Owner Ruling R29 — Downstream Feasible Rehearsal Scope.*

## 6. Ruling R30 — Real Amendment-Purpose Feasibility Gate

```text
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
```

Track-B success proves the selector, store, replay, seal, and manifest system operates
correctly **on a conforming feasible candidate snapshot**. It does **not** prove that the
current accepted metadata-only production builder can produce one.

A new current limitation is therefore recorded: **M3.3 REAL AMENDMENT-PURPOSE
FEASIBILITY: OPEN — OWNER RESOLUTION REQUIRED BEFORE REAL EXECUTION.** The known
production condition is that the quota requires three categories, the production metadata
path has no accepted affirmative classifier, the builder therefore supplies no
affirmative purpose witnesses, and a real builder-derived selection would currently be
expected to return infeasible on that requirement.

**This is not a software failure, is not hidden after I/R passes, does not relax the
quota, and is not a claim about real feasibility.** No real candidate distribution has
been inspected.

**I/R passing does not authorize E0. A1 passing does not by itself authorize E0.** The
previously contemplated `A1 → owner E0 authorization` sequence is now **conditioned** on a
separate owner disposition of this real-path limitation, which may consider — in a
separate packet — whether an already accepted metadata-safe evidence route exists,
whether a new pre-selection evidence stage is required, whether an explicit methodology
revision is justified before any real candidate distribution is inspected, or whether real
infeasibility is intentionally accepted. **This record chooses none of those options.**

**Cite as:** *M3.3 Owner Ruling R30 — Real Amendment-Purpose Feasibility Gate.*

## 7. IN-2 is not reversed

The production rule stands: where accepted metadata does not establish a provisional
category, `amendment_purpose_category` is `NULL`, the evidence level is `unproven` in its
governed schema-compatible representation, and the accession makes **no** amendment-purpose
quota contribution.

**No production fallback, and no hidden fixture fallback in the builder.** The Track-B
constructor is test- and rehearsal-only and must be **mechanically unreachable** from real
E0/E1 operator paths, proved by a boundary test that the production candidate builder can
neither invoke nor import the synthetic-purpose injection path.

## 8. What this record does not authorize

It does **not**: authorize the real offline parse (**M3.3-E0**) or progression to
**M3.3-E1** or **M3.3-E2**; authorize a real snapshot, selection, manifest, or root;
approve a root or begin **M3.4**; enable network access; authorize an SEC request,
reacquisition, or re-retrieval; authorize a migration; authorize reading or mutating
`EV_ROOT`, the real private catalog, or any M3.2 private evidence; reverse IN-2; create a
production amendment-purpose classifier; defer or lower any quota; supply **OR-6**,
**OR-7**, **OR-9**, or **OR-11**; pre-resolve Decision 023 **O1**; close any limitation;
move `m3.2-complete`; or create any tag.

**Additionally**: real E0 may **not** be owner-authorized merely because I/R or A1 passes
while `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` remains unresolved.

## 9. Next authorized action

**Resume the same Decision-070 M3.3-I/R stage** under the governed dual-track rehearsal,
with every earlier obligation and stop condition still in force, then return to Sol/GPT
for a fresh read-only review of the frozen target and its rehearsal evidence.

```text
M3_3_I_R_BLK_1_REHEARSAL_ARCHITECTURE_OWNER_RESOLVED
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
```
