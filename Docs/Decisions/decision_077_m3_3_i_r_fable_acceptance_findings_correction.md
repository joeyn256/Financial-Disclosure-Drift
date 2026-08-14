# Decision 077 — M3.3-I/R Fable Acceptance Findings, Final Bounded Correction

```text
STATUS: ACCEPTED — OWNER M3.3-I/R FABLE ACCEPTANCE FINDINGS CORRECTION
DATE: 2026-08-14
OWNER: Sol/GPT
OUTCOME: M3_3_DECISION_077_FABLE_FINDINGS_CORRECTED_READY_FOR_FRESH_FORMAL_ACCEPTANCE
IMPLEMENTATION_AUTHORIZATION: BOUNDED — LIVE COMMENT/DOCSTRING AUTHORITY POINTERS,
  CURRENT-STATE NAVIGATION SURFACES, AND OPERATOR WORKFLOW DOCUMENTATION, AND NOTHING ELSE
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

**This record disposes the findings of the first formal Fable 5 Maximum M3.3-I/R acceptance
review and authorizes the final bounded correction before a fresh one.** It changes no research
definition, no methodology, no selector, no quota, no schema, no evidence identity, no receipt or
snapshot identity, and no authorization. It corrects documentation: where live code comments point,
what live navigation surfaces say the current stage is, and how the operator runs routine
validation.

**It is not an acceptance.** The review it disposes returned **BLOCKER 0 / MAJOR 0 / MINOR 2**,
which is a correction verdict, not a pass. A fresh formal Fable acceptance is still required, and
this record does not anticipate its result.

**It authorizes no real execution.** M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 all remain separate,
unissued owner gates. Both real-path feasibility gates remain **OPEN** and unmerged.

---

## 1. The reviewed target and the verdict

| Fact | Value |
|---|---|
| Reviewed target | `46b6742b776504dfc795174a5b36f2feaf3bb25d` (tree `e0d7eb3f8f93a343e70e0573c21c8891f1ad17e0`) |
| Reviewer | Fable 5, Maximum effort, first formal M3.3-I/R acceptance epoch |
| Verdict | **BLOCKER 0 / MAJOR 0 / MINOR 2 / OPTIONAL 1 / OBSERVATIONS 3** |
| Acceptance | **NOT GRANTED** — a MINOR-bearing review is not a pass |
| `m3.2-complete` | unchanged (tag object `2865a1479e4576dc18a4098c928b278812f38d00`) |

The review confirmed the substance of the stage: the M3.3A execution rehearsal E1–E8 runs and
passes, the **R28** bridge is clean, the M1–M38 mutation campaign is fully killed, the Decision 076
infrastructure is sound, and both real-path feasibility gates are truthfully carried as OPEN. No
finding touched methodology, selector behavior, evidence identity, or any authorization.

**The two MINOR findings and the one OPTIONAL finding are accepted for bounded correction.** The
three observations are disposed in §6 without code change.

## 2. Ruling R36 — Live Authority-Pointer Correction

```text
M3_3_LIVE_AUTHORITY_POINTER_SEMANTIC_CORRECTION_OWNER_RULED
```

**The defect (MIN-1).** Live comments and docstrings under `src/` and `tests/` carried section
pointers derived from the **superseded draft numbering** of Decisions 071, 072, and 074. Some named
sections that do not exist. Others named sections that *do* exist but govern something else
entirely — `R20 §7` resolving to Decision 071 §7, the calendar-source R18 recheck, is the clearest
case — so an existence-only checker cannot see them.

**The rule.** Every approval-relevant live authority pointer must identify the **actual accepted
section supporting the adjacent claim**. A structurally existing but semantically unrelated section
is **not acceptable**.

**Generality.** The rule applies to live M3.3-I/R `src/**` and `tests/**` authority comments and
docstrings. It is **not** satisfied by correcting only the sites a reviewer happened to list: every
live Decision 071–076 citation is semantically reviewed in this stage. Additional stale pointers the
sweep discovers are correctable under this ruling when, and only when, (a) the site is
comment/docstring authority text, (b) the accepted target is mechanically clear from the record, and
(c) behavior and assertions are untouched. A semantically ambiguous site is **returned to the owner
as a new MINOR**, never resolved by inventing an authority.

**Conflicts.** The existing `scripts/check_decision_section_refs.py` gate remains an **existence**
checker and is not broadened, weakened, or redesigned to force a result. Where structural existence
and human semantic review disagree, **semantic review controls**. **No semantic NLP checker is
built.**

**Internal rule-label numbering is not a defect.** Decision 071 §3's R19 predicate table keeps its
original `4.1`–`4.12` row labels, and Decision 072 §3's R23 table keeps its `§5.1`–`§5.6` aspect
labels. Those labels exist in the accepted records and identify the correct predicates, so citations
using them are correct. Because `R19 §4.N` can be misread as Decision 071 §4 — which is R20 — the
modules that use that form now state the convention explicitly.

**Cite as:** *M3.3 Owner Ruling R36 — Live Authority-Pointer Correction.*

## 3. Ruling R37 — Current-State Surface Synchronization

```text
M3_3_CURRENT_STATE_SURFACE_SYNCHRONIZATION_OWNER_RULED
```

**The defect (MIN-2).** Several live navigation and current-state surfaces still instructed the
operator to perform an **Opus corrected-target rereview that has already occurred and has since been
superseded**. A stale instruction on a current-state surface is not a harmless leftover: it is an
operative direction to do the wrong next thing.

**The rule.** Live current-state and navigation surfaces must describe the **actual** current stage:

| Fact | Current value |
|---|---|
| M3.3-I/R implementation and rehearsal | **COMPLETE** |
| Original and corrected Opus review work | **COMPLETE** |
| MIN-A | **CLOSED** |
| Decision 076 infrastructure | **COMPLETE / OWNER-ACCEPTED** |
| RET-1 | **CLOSED** |
| First formal Fable acceptance review | **COMPLETE — B0 / M0 / MIN2 — NOT ACCEPTED** |
| Decision 077 bounded correction | **APPLIED** |
| Next authorized action | **one fresh Fable 5 Maximum formal M3.3-I/R acceptance review** |
| A further Opus ultrareview | **NOT AUTHORIZED / NOT REQUIRED** |
| M3.3-E0, M3.3-E1, M3.3-E2, M3.4 | **NOT AUTHORIZED** |
| Both real feasibility gates | **OPEN / ACTIVE**, never merged |
| Real acceptance-ordering adequacy | **PENDING FUTURE AUTHORIZED E0 VERIFICATION** |

**Accepted historical decision records are not rewritten** merely because current state advanced.
Decision 075 §10 may keep saying a fresh read-only ultrareview-rereview was its next act; Decision
076 §13 may keep saying Decision 076 found and returned RET-1 as open defects. Both are historically
true, and current state is carried elsewhere. Historical passages on a navigation surface may remain
**when explicitly marked historical**; current operative instructions may not.

**This record does not itself constitute Fable acceptance, and no surface may imply that it does.**

**Cite as:** *M3.3 Owner Ruling R37 — Current-State Surface Synchronization.*

## 4. Ruling R38 — Operator Validation Workflow

```text
M3_3_OPERATOR_VALIDATION_WORKFLOW_OWNER_RULED
```

**The gap (OPT-1).** `Docs/m3/operator_runbook.md` documented no routine full-validation command,
so the Decision 076 R35 optimization was reachable only by reading the Makefile.

**The rule.** For routine local full development validation on the project owner's current Mac,
**`make check-fast` is the owner-recommended path**. Its pytest leg uses `WORKERS ?= 7` and
`DIST ?= worksteal`.

The conservative serial references remain **`make test`** and **`make check`**, neither removed nor
weakened. The governance gates are **`make links`** and **`make decision-refs`**.

`WORKERS` and `DIST` are overridable. Seven workers with `worksteal` is a value **measured on the
owner's machine**; it is **not** automatically the CI standard, and **CI was not switched to seven
workers** under Decision 076 §10. Serial validation is for when a concrete reason requires it — a
parallel/serial disagreement, a test-isolation symptom, or a reviewer wanting unscheduled execution
order.

**This is workflow documentation only.** It alters no real-operation command, grants no network
authority, and is **never** a precondition for, or a component of, an E0/E1/E2 authorization.

**Cite as:** *M3.3 Owner Ruling R38 — Operator Validation Workflow.*

## 5. What was corrected

**MIN-1 — live authority pointers.** The thirteen sites the review listed were corrected, and the
full sweep required by R36 found and corrected further sites the review had not listed:

| Class | Stale form | Corrected target |
|---|---|---|
| R19 event-flag ruling | `Decision 071 §4` | **Decision 071 §3** |
| R19 history stratum | `R19 §4.13` (does not exist; the table ends at `4.12`) | **Decision 071 §3.1** |
| R20 boundary controls | `Decision 071 §6`, `R20 §6`, `R20 §§6.1`–`6.4`, `R20 §7` | **Decision 071 §4** |
| R20 overlap and absence | `R20 §6.5` | **Decision 071 §4.1** |
| R21 XBRL composite | `Decision 071 §8` | **Decision 071 §5** |
| R22 full-index disposition | `Decision 072 §4` | **Decision 072 §2** |
| R23 registrant materialization | `Decision 072 §4`, `§10`, `§§5, 10` | **Decision 072 §3** |
| R32 linked-amendment gate | `Decision 074 §4` | **Decision 074 §3** |
| R33 cohort boundary | `Decision 074 §6` | **Decision 074 §5** |
| Mutation-campaign recovery | `Decision 076 §14` | **Decision 076 §9** |

Two sites gained a second pointer because the adjacent sentence independently relies on a second
accepted proposition: the `census_accessions` single-registrant fact (**Decision 072 §1**) beside the
R23 grouping rule, and the OBS-E project-facing control name (**Decision 072 §7**) beside Decision
071 §4's persisted vocabulary.

**Executable semantics were proved unchanged**, not asserted: every edit was pre-classified with
`tokenize` and `ast` as comment or docstring text, and every touched file was re-derived against the
committed entry tree under the project Python 3.12 interpreter. Comment-only files kept an identical
non-comment token stream, an identical full AST, and identical semantic code-object fields.
Docstring-edited files kept an identical docstring-normalized AST, identical assertion ASTs, and
identical semantic code-object fields. **Cross-process marshal-byte equality was deliberately not
used as a correctness requirement**, per the Decision 076 RET-1 finding; set and frozenset constants
were rendered order-independently for the same reason.

**MIN-2 — current-state surfaces.** The shared current-state banner in `Docs/architecture_map.md`,
`Docs/change_impact_map.md`, `Docs/m3/operator_runbook.md`,
`Milestones/milestone_03_master_plan.md`, and `Milestones/contracts/README.md`, the M3.3-I/R status
field in `Milestones/contracts/m3_3.md`, the current-state pointer in `Docs/decision_index.md`, and
the ledger in `Milestones/STATUS.md` were synchronized to the R37 posture.

**OPT-1 — operator runbook.** `Docs/m3/operator_runbook.md` documents the R38 workflow.

## 6. Observation dispositions

| ID | Disposition |
|---|---|
| **OBS-1** — per-run execution-rehearsal `evidence_reference` variability | **DEFERRED — REQUIRES SEPARATE OWNER ARCHITECTURE DECISION.** It remains part of the Decision 076 deferred architecture question. This record does **not** redefine `evidence_reference`, receipt identity, evidence identity, selection identity, manifest identity, or catalog-digest semantics, and no code change is made for it |
| **OBS-2** — `Milestones/STATUS.md` internal coherence | **NO CORRECTION REQUIRED.** STATUS remains internally coherent under its documented convention that the trailing machine-readable current-state markers control |
| **OBS-3** — E5(a) rehearsal proof shape | **NO CORRECTION REQUIRED.** The E5(a) strict-subset proof through the accepted entry point, together with the scenario superset proof, jointly satisfy the accepted rehearsal requirement. **No new methodology ruling is created by this record** |

## 7. Findings returned to the owner

**One new MINOR, discovered by the R36 sweep and not resolved here.**

```text
tests/unit/test_m3_support_target_pairs.py:1   "(Decision 071 §6; §17 item L)"
```

The `Decision 071 §6` half is **correct** — IN-3 is in Decision 071 §6. The `§17 item L` half names
no document. Decision 071 has §1–§9; Decision 070 has §1–§9; Decision 018 §17 is the node-limit
ruling; `Milestones/contracts/m3_3.md` §17 is Atomicity; and no accepted record in the repository
contains an "item L". The form matches the `packet §N item X` convention used elsewhere for an
**owner session packet**, which is not repository authority.

Because the accepted target is **not mechanically clear from any accepted record**, R36 forbids
resolving it here. It is left byte-unchanged and returned to Sol/GPT.

**One observation, recorded and not acted on.** `RIC_ETF_SIC_CODES` in
`src/disclosure_drift/m3/candidate_controls.py` cites Decision 014 §4 for the SIC family exclusion,
which is correct, but does not cite **R26** (Decision 072 §6) — the ruling that froze the set as
exactly `{6722, 6726}` and excluded `6798`. This is a **missing** citation, not a stale one, and R36
governs stale pointers. No edit was made.

## 8. What is unchanged

No research definition, hypothesis, threshold, cohort window, outcome, or seed. No selector, reserve
selector, candidate behavior, offline-parsing behavior, selection store, manifest or release
hashing, migration, or configuration. No evidence, receipt, snapshot, or selection identity. No
production executable AST and no test assertion AST. No CI standard. The preregistration is
untouched.

`Docs/m3/reviews/m3_3_i_r_rehearsal_06bb47a.md`,
`Docs/m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md`, and every earlier accepted review artifact
remain **immutable and unmodified**. Decisions 001–076 are not rewritten.

## 9. What this record does not authorize

It does **not**: authorize the real offline parse (**M3.3-E0**) or progression to **M3.3-E1** or
**M3.3-E2**; authorize a real snapshot, selection, manifest, or root; approve a root or begin
**M3.4**; enable network access; authorize an SEC request, reacquisition, or re-retrieval; authorize
a migration; authorize reading, resolving, or mutating `EV_ROOT`, the accepted real private catalog,
or any M3.2 private evidence; close either real-path feasibility gate; move `m3.2-complete`; or
create any tag.

`M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
`M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` both remain **ACTIVE**, separately auditable, and
never merged into one flag. `real_builder_feasibility_proved` remains **false**. Real
acceptance-ordering adequacy remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION**.

**It is not a Fable acceptance and claims none.**

## 10. Next authorized action

Return to Sol/GPT. The owner will issue **one fresh Fable 5 Maximum formal M3.3-I/R acceptance
packet** against the final post-Decision-077 target. **No further Opus ultrareview is authorized or
required**, no real-feasibility resolution begins here, and **E0 does not begin here**.

```text
M3_3_DECISION_077_FABLE_FINDINGS_CORRECTION_RECORDED
```
