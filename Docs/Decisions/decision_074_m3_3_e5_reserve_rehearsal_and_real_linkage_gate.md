# Decision 074 — M3.3 E5 Reserve-Rehearsal Correction, Real Linkage Gate, and Temporal Derivation Correction

```text
STATUS: ACCEPTED — OWNER M3.3 E5 REHEARSAL CORRECTION AND REAL-LINKAGE GATE
DATE: 2026-08-14
OWNER: Sol/GPT
OUTCOME: M3_3_I_R_E5_RESERVE_REHEARSAL_ARCHITECTURE_OWNER_RESOLVED
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

**This record resolves the M3.3-I/R stop and permits the same bounded stage to complete.**
It creates no new stage and no new authority:
[Decision 070](decision_070_m3_3_i_r_implementation_authorization.md) remains the accepted,
still-unconsumed I/R implementation authority, and Decisions 071–073 remain accepted.

**It authorizes no real execution.** M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 all remain
unauthorized; network, SEC, reacquisition, and private-evidence access remain **NONE**;
`EV_ROOT` remains prohibited; migration remains `none`; and `m3.2-complete` remains
immutable.

**Where this record and an earlier governing record disagree**, it controls only on the
points it names. Decisions 001–073 remain accepted and byte-unchanged. Decision 020's
reserve methodology is **unchanged**, and Decision 073's dual-track rehearsal
architecture is **unchanged**.

---

## 1. Owner acceptance of the stop

```text
M3_3_I_R_E5_ARCHITECTURE_STOP_OWNER_ACCEPTED
```

The stop was **correct**. The implementer reached a condition
`Docs/m3/offline_rehearsal_spec.md` §10 item 4 reserves — an architecture finding, which
is *referred, never resolved by adjusting the scenario until it passes* — and returned
rather than tuning the fixture.

Accepted as complete at the stop: Track A; Track B; the **R28** bridge (48 expected
differences, 0 violations); the unchanged joint selector; 2009/2010 pair wiring;
persistence and reconstruction; write-free replay; the selection seal; Decision 023
**O1** fail-closed referral; and scenarios E1, E2, E3, E4, E6, E7, E8. E5 was partial:
(b) and (c) passed, (a) stopped.

`BUILDER_DERIVED_SELECTION_DISPOSITION = INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE` and
Track-B selector feasibility are both accepted as reported. No commit existed, and
Decision 070 remained unconsumed.

## 2. Ruling R31 — Reserve Rehearsal Totality Semantics

```text
M3_3_I_R_E5_RESERVE_REHEARSAL_ARCHITECTURE_OWNER_RESOLVED
```

**BLK-2 is RESOLVED.** The defect was in the **E5(a) rehearsal requirement**, not in
Decision-020 production reserve compatibility.

**Production authority is unchanged.** For each selected target, exactly one of:

| # | Outcome |
|---|---|
| **A** | a compatible reserve exists ⇒ persist exactly one `reserve_rank = 1` package |
| **B** | none exists ⇒ persist exactly one deterministic `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition |

The two are mutually exclusive. A no-compatible-reserve disposition is target-specific,
deterministic, durable, review-required, and **nonblocking**: it is **not** selection
infeasibility, **not** node exhaustion, and **not** a licence to approximate.

**Unchanged, and not to be changed:** whole-bundle replacement semantics; exact
contribution-set equality; exact reserve signature equality; role compatibility; floor
preservation; cap preservation; amendment-family behaviour; evidence floors; ranking;
rank count; the selector objective; the selected bundle.

**Specifically prohibited:** dropping a replacement's stress accession to match a target;
forcing the initial selector to choose an amendment; tuning the fixture until every
selected bundle happens to be twinned; raising the production `node_limit`; approximate
reserve signatures.

### 2.1 Corrected E5(a)

The former requirement — *"every selected target has a compatible rank-1 reserve
package"* — is **SUPERSEDED for M3.3 rehearsal**. It imposed a production-invalid
condition: outcome **B** is lawful, so universal coverage was never required.

E5(a)'s purpose is now to **prove the positive compatible-reserve path directly and
completely**, using a small, bounded, **pure** reserve-selector fixture that does **not**
invoke the pilot-scale joint selector. It constructs a lawful selected target and at
least one lawful unselected replacement from the accepted candidate model, gives them
exactly compatible bundles and exact contribution signatures, and proves: one rank-1
package is produced; ranking is deterministic where two or more compatible replacements
exist; target and replacement are disjoint; whole-bundle compatibility is exact; a
subset or superset bundle is rejected; and no arbitrary accession subset can be chosen to
manufacture compatibility.

This is a **reserve-layer** positive-path rehearsal, not a second selection methodology.
A minimal synthetic selected-result fixture is permitted because the pure reserve layer
is explicitly downstream of, and does not determine, the initial joint selection.

### 2.2 E5(b) and E5(c)

**E5(b)** retains the existing end-to-end feasible Track-B run in which **zero** selected
targets have compatible reserve packages: every selected target receives exactly one
durable disposition, `running -> feasible` succeeds, no target has neither and none has
both, and reconstruction reproduces the dispositions exactly.

**E5(c)** retains the existing end-to-end feasible **mixed** Track-B run: at least one
target with a compatible rank-1 reserve, at least one with a disposition, exactly one
outcome per selected entity, both persisted inside the accepted transaction, and both
reproduced by reconstruction. The observed 23/1 split is an acceptable fixture while it
stays deterministic; **the requirement is MIXED + TOTAL, never that exact count**.

### 2.3 E5 pass standard

E5 passes when (a) the pure compatible-positive reserve path passes, (b) end-to-end
zero-compatible disposition totality passes, and (c) end-to-end mixed disposition
totality passes. Together these cover the whole production state space without imposing
a production-invalid requirement.

**Cite as:** *M3.3 Owner Ruling R31 — Reserve Rehearsal Totality Semantics.*

## 3. Ruling R32 — Real Linked-Amendment Feasibility Gate

```text
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
```

**FND-1 is ACCEPTED.** Accepted candidate and selector methodology requires
evidence-supported amendment parentage for linked-amendment quota contribution;
`possible_amendment_of` and `unresolved_amendment` satisfy nothing; the real M3.3-E0
source-to-canonical mapping currently feeds no accepted field into the Decision 012
canonical field `amendment_relationship`; and absent filing-header relationship evidence
the Decision 008 linkage machinery reaches at best a possible or unresolved state.
**The current real metadata path therefore has no demonstrated way to produce the eight
affirmative linked-amendment entity witnesses.**

This is **not** an I/R software defect while production remains fail-closed, synthetic
rehearsal facts are explicitly stipulated, and no real-feasibility claim is made.

A new current status fact is recorded, analogous to and **independent of**
[Decision 073](decision_073_m3_3_rehearsal_snapshot_bifurcation_and_amendment_purpose_blocker.md)
§6's amendment-purpose gate. Both remain visible and separately auditable.

This record does **not**: invent parentage; treat `/A` as sufficient evidence by itself;
assign `amends_original` from accession order; use a company name, filing-date proximity,
or an amendment sequence number as proof; authorize filing headers, filing-body
retrieval, or network; or lower the linked-amendment quota.

Track A and Track B may continue to use explicit synthetic, accepted-shaped linkage facts
for rehearsal only, identical across the **R28** bridge except where an existing decision
says otherwise. The I/R evidence must state
`REAL_LINKED_AMENDMENT_FEASIBILITY_PROVED = NO` and
`REAL_LINKED_AMENDMENT_FEASIBILITY_GATE = OPEN`.

**Cite as:** *M3.3 Owner Ruling R32 — Real Linked-Amendment Feasibility Gate.*

## 4. The two real-path gates

After this record **two** known real-path gates are open:

1. `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` (Decision 073 **R30**);
2. `M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` (**R32**).

I/R may still reach BLOCKER 0 / MAJOR 0 / MINOR 0, because these are truthfully governed
**real-execution limitations**, not unfixed I/R defects.

**No owner authorization for real E0 may be issued merely from I/R success, an
ultrareview pass, or a fresh independent A1 acceptance.** A separate Sol/GPT owner
architecture disposition must first address **both** gates. **They are never merged into
one vague "real feasibility" flag.**

## 5. Ruling R33 — Same-Build Cohort-Boundary Derivation

**FND-2 is NOT a real-path feasibility gate.** It revealed a bounded I/R
implementation-order defect, and
[Decision 010](decision_010_temporal_availability_and_cohort_assignment.md) already fixes
the necessary semantics: the official filing date determines the authoritative temporal
cohort, `acceptance_date_sec` determines the audit-only acceptance cohort, both use the
same frozen `cohort_for()` windows, a crossing is reportable when those two resolved
assignments occupy different frozen cohorts, and ambiguity is never silently `false`.

`cohort_boundary_crossed` **must** therefore be derived from the current authoritative
resolved candidate facts **during the same candidate-snapshot derivation**. It **must
not** require an earlier M3.3 snapshot, a previous E0 pass, a prior candidate resolution,
or a second real execution cycle. One pure derivation, using the existing `cohort_for()`
definitions.

| Condition | Result |
|---|---|
| both cohorts known and **different** | `TRUE` |
| both known and equal | `FALSE` |
| either unavailable, malformed, or unresolved | **UNKNOWN / review-required** in the existing candidate vocabulary — **never a silent `FALSE`** |

No new cohort-boundary table, no altered cohort window, no altered selection cohort. The
rehearsal-only stipulation for this fact is removed once the production derivation
exists, and Track A and Track B receive the **same** mechanically derived value.

Required tests: same cohort; every adjacent frozen-boundary crossing; a non-adjacent
crossing; a missing official date; a missing acceptance date; a malformed acceptance
value; input-order invariance; and A/B bridge equality.

**Cite as:** *M3.3 Owner Ruling R33 — Same-Build Cohort-Boundary Derivation.*

## 6. Ruling R34 — Acceptance-Date Ordering Verification

**FND-3 requires no new methodology rule.** Decision 010 already defines the raw SEC
acceptance format `YYYYMMDDHHMMSS` and derives `acceptance_date_sec` from the first eight
characters, and Decision 019's strict-later ordering remains **fail-closed** when a
required acceptance audit date is `NULL`, malformed, incomparable, equal, or earlier.
**That is not weakened.**

For I/R: retain strict parsing, retain fail-closed ordering, and retain synthetic tests
for the valid fourteen-digit, `NULL`, malformed, equal, earlier, and later cases.

For a **future authorized real E0 verification**, require a report carrying:

```text
TOTAL_AMENDMENT_CANDIDATES:
ACCEPTANCE_RAW_PRESENT:
ACCEPTANCE_RAW_VALID_14_DIGIT:
ACCEPTANCE_RAW_MISSING:
ACCEPTANCE_RAW_MALFORMED:
RESOLVED_LINKAGE_WITH_ORDERING_PROOF:
RESOLVED_LINKAGE_BLOCKED_BY_ACCEPTANCE_ORDERING:
```

No result is assumed today, because private evidence may not be inspected. If real data
later carries insufficient valid acceptance evidence, affected resolved linkage fails
closed under existing authority. **This is an E0/E1 verification condition, not a third
pre-E0 methodology gate.**

**Cite as:** *M3.3 Owner Ruling R34 — Acceptance-Date Ordering Verification.*

## 7. IMP-1, IMP-2, IMP-3

Accepted as legitimate **bounded** implementation corrections, subject to independent
review, and **not to be broadened**:

| ID | Correction |
|---|---|
| **IMP-1** | `industry_quota_eligible` and primary-universe eligibility remain **independent**, as Decision 016 §2 governs |
| **IMP-2** | **R19** receives the raw accepted lineage edge kinds; no unauthorized name-transition inference |
| **IMP-3** | Candidate accessions are bounded by the accepted candidate `reference_form_types` family; an unrelated `10-D` or `8-K` census row must not fail the candidate builder merely by existing |

Each is added to the independent-review checklist and to the implementer evidence.

## 8. Mutation-campaign additions

The authorized campaign extends from M1–M32 to **M1–M38**:

| ID | Mutation |
|---|---|
| **M33** | E5 incorrectly requires every selected target to hold a reserve package |
| **M34** | a no-compatible-reserve disposition incorrectly makes a feasible selection infeasible |
| **M35** | the reserve layer may drop an accession from a replacement's whole bundle to manufacture compatibility |
| **M36** | `cohort_boundary_crossed` depends on a previously persisted M3.3 resolution rather than the current same-build resolved facts |
| **M37** | a missing or malformed acceptance date silently becomes "no boundary crossed" |
| **M38** | `possible_amendment_of` or `unresolved_amendment` is allowed to satisfy `linked_amendment_entities` |

All must be killed, with positive-control proof.

## 9. Governance synchronization

Decisions **070, 071, 072, 073, and 074** are registered. On success the recorded status
becomes `M3.3-I/R: IMPLEMENTED + REHEARSED — PENDING INDEPENDENT REVIEW`, and current
surfaces record **both** real-path gates plus
`REAL ACCEPTANCE-ORDERING ADEQUACY: PENDING FUTURE AUTHORIZED E0 VERIFICATION`.

**No real-feasibility claim is made, and E0 is not next automatically.** The truthful
next path after independent I/R acceptance is **return to Sol/GPT for real-path
architecture resolution**, before any real E0 authorization.

## 10. Pre-commit standard

I/R may reach BLOCKER 0 / MAJOR 0 / MINOR 0 with **both** real-path gates OPEN, provided
production behaviour remains fail-closed, fixtures are explicit, **R28** remains clean, no
real-feasibility claim is made, and governance records the gates truthfully. The
real-path gates are not implementation defects; every actual I/R defect must still be
zero before any commit.

## 11. What this record does not authorize

It does **not**: authorize the real offline parse (**M3.3-E0**) or progression to
**M3.3-E1** or **M3.3-E2**; authorize a real snapshot, selection, manifest, or root;
approve a root or begin **M3.4**; enable network access; authorize an SEC request,
reacquisition, or re-retrieval; authorize a migration; authorize reading, resolving, or
mutating `EV_ROOT`, the accepted real private catalog, or any M3.2 private evidence;
change Decision 020's reserve methodology; change Decision 073's dual-track architecture;
relax any quota; supply **OR-6**, **OR-7**, **OR-9**, or **OR-11**; pre-resolve Decision
023 **O1**; close any limitation; move `m3.2-complete`; or create any tag.

**No real candidate distribution has been inspected.** R31–R34 were frozen from accepted
records and synthetic fixtures only.

## 12. Next authorized action

**Complete the same bounded M3.3-I/R stage under Decision 070's unconsumed authority**,
then return to Sol/GPT for a frozen-target read-only review, a fresh independent I/R
acceptance, and a separate owner resolution of **both** real-path feasibility gates.

```text
M3_3_I_R_E5_RESERVE_REHEARSAL_ARCHITECTURE_OWNER_RESOLVED
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
```
