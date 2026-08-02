# Decision 029 — Milestone 3.1 Rehearsal Completeness and Reason Semantics

**Date:** 2026-08-02  
**Status:** ACCEPTED — OWNER APPROVED 2026-08-02
**Type:** Bounded Milestone 3.1 remediation record. **Not** a preregistration deviation. It changes
no hypothesis, cohort window, maturity gate, outcome definition, threshold, seed, selection
methodology, S4/S5/S6 identity, hash preimage, migration byte, or publication boundary. It
authorizes no network access and no live SEC retrieval.  
**Narrowly supersedes:** only two clauses of
[Decision 028](decision_028_m3_1_readiness_corrections.md) — §5's A6 scenario language, solely to
permit the rehearsal-only manifest-resolution fixture described in §4 below, and §6's word
"exactly" together with §12's closed-delta wording, solely to admit the single new reason code named
in §5. Every other clause of Decision 028 remains unchanged and controlling.  
**Amends:** nothing. Decisions 011, 013, 024, 026, and 027 remain unchanged and controlling for the
operating-calendar provenance, the pilot-selection mechanics, the M2 → M3 boundary, the Milestones
0–2 closeout, and the Milestone 3 master plan respectively.  
**Related:** Decisions 011, 024, 026, 027, and 028;
[`Milestones/contracts/m3_1.md`](../../Milestones/contracts/m3_1.md);
[`Docs/m3/offline_rehearsal_spec.md`](../m3/offline_rehearsal_spec.md);
[`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md).  
**Governs:** the completeness of the independently tested per-route `A_reachable` evidence M3.1A must
produce, the single new reason code that evidence requires, the M3.1A phase-token predicate, and the
first durable §17 review artifact.

---

## 1. Why this record is required

`Milestones/contracts/m3_1.md` is `ACCEPTED_READY_FOR_IMPLEMENTATION` and the M3.1 implementation
exists in the working tree. It is **not accepted**. Three defects block it, and two of the three
cannot be corrected by code alone because the correction would otherwise contradict an accepted
Decision 028 clause.

**F5 — the announcement route's `A_reachable` is not independently tested.**
`sec_edgar_calendar_announcement` is manifest-resolved: `SecClient._resolve_url` obtains its URL only
through `require_evidence(evidence_id)`, which reads the source-controlled
`CALENDAR_EVIDENCE_MANIFEST`. That manifest is provably empty and is asserted empty by
`tests/unit/test_operating_calendar_evidence.py`. The rehearsal therefore cannot place a single
attempt on the route, records it in `unmeasured_routes`, and produces **no** independently tested
bound for it. Master plan §§15–16, §§23–24, contract §4, contract §18, and Gate F items 3.10 and
9.3a each require an independently tested bound for **every** route, and Gate F item 9.3a says so
without exception for routes planning zero requests.

**N5 — a scenario mismatch has no registered terminal reason code.** A rehearsal whose scripted
scenario does not reach the state the specification names is an integrity failure of the evidence,
not an acquisition interruption. Recording it as `SEC_ACQUISITION_INTERRUPTED` would misreport a
defective witness as a network event and would corrupt the meaning of the only code Decision 028 §6
provides for interruption.

**R3 — the M3.1A phase token is gated on the wrong predicate.**
`cli.py::_m3_rehearse_command` emits the token when `report.a_reachable_agrees` holds.
`a_reachable_agrees` quantifies only over routes that **were** measured, so a route excluded into
`unmeasured_routes` is silently excluded from the predicate rather than failing it.
`report.a_reachable_fully_tested` is computed and serialized and is read by no consumer. The
stored-report path `cli.py::_m3_rehearse_report_command` has the same defect, and `_bounds_agree()`
is vacuously true for a matching subset.

R3 requires no supersession: the contract already requires every worst path to be exercised, so
correcting the gate is conformance work. F5 and N5 do require this record.

## 2. Verified baseline

Verified live before this record was drafted, and again before it was committed:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| Baseline commit (`HEAD`) | `458a741c01cb4bc33b51184570b05cc54beb17f8` |
| Live `refs/heads/main` (`git ls-remote --heads origin`) | `458a741c01cb4bc33b51184570b05cc54beb17f8` |
| Commits ahead of the live remote | **zero**; nothing is unpushed |
| Cached local `origin/main` | `1dbba3d…` — **stale**; `[ahead 17]` is an artifact of the stale ref and is not a real divergence |
| Working tree at draft start | clean |
| Migration chain | contiguous through `0013`; **no migration is proposed or authorized here** |
| Active implementation contract | `Milestones/contracts/m3_1.md`, `ACCEPTED_READY_FOR_IMPLEMENTATION` |
| Tags | latest is `m2.3-s6-complete`; **no `m3-complete`, no `m3.1-complete`** |
| Suite at baseline | 2675 passed, 2 skipped — one skip is `tests/unit/test_httpx_transport.py`, *"the `[sec]` extra is not installed"* |

The cached-ref correction is recorded because an earlier state assessment reported seventeen
unpushed commits. That was false. **Do not `git fetch` merely to repair the cached ref**; the live
remote was read directly and agrees with `HEAD`.

## 3. Prior review status — no durable artifact exists

There is **no** §17 review artifact anywhere in tracked history, in any ref, in any reflog, or among
unreachable objects. Commit prose describes at least four review rounds — a contract review, an
initial implementation review, a second review, and two independent blind audits against
`af56743…` — and states `FAIL` for several. None of those events produced a durable record joining
reviewer identity, UTC date, the exact reviewed commit and tree SHA, the commands run, the findings,
and a verdict.

Two consequences are recorded as fact rather than as opinion:

1. **No review covers `458a741`.** Every evidenced review is pinned to `af56743` or earlier.
2. **A fix commit does not convert a FAIL into a PASS.** The prior FAIL verdicts remain open process
   facts, and the tree they examined no longer exists.

The review required after this record's remediation is therefore the **first durable §17 review**,
not "the fourth". It must assess the new tree on its own evidence and may not inherit a
reconstructed finding count from records that do not exist.

## 4. Ruling F5 — the rehearsal-only manifest-resolution fixture

**Decision 028 §5's A6 language is narrowly superseded** solely to permit an in-memory,
rehearsal-only manifest-resolution fixture for `sec_edgar_calendar_announcement`. The supersession
is limited to that route, that fixture, and the offline rehearsal context. It grants **no** retrieval
authority of any kind.

The fixture must:

- exist only inside the offline rehearsal context, and never in a production code path;
- resolve exactly one fixed synthetic evidence identifier to exactly one fixed approved-host URL of
  the route's registered family;
- drive the real `SecClient.fetch()` and the real response-policy loop, over the existing scripted
  transport seam;
- never enter `CALENDAR_EVIDENCE_MANIFEST`, and never mutate it;
- never read, write, or require the operator's private calendar-evidence manifest;
- never assert a real date, a real announcement, or any provenance fact outside the fixture itself;
- never be serialized into a report, receipt, plan, catalog, snapshot, or raw object;
- restore the production resolver on normal **and** exceptional exit;
- open no socket, and grant no live retrieval and no arbitrary-URL retrieval authority.

It must be implemented as a tightly scoped, context-managed substitution of the binding
`SecClient._resolve_url` uses — that is, of `disclosure_drift.sec.http_client.require_evidence` — and
**not** by adding a resolver parameter, a URL override, or any arbitrary-URL API to the production
`SecClient`.

### 4.1 The fixture survives in both manifest branches

The question put to this record was whether an empty approved operator manifest, which makes
`U(sec_edgar_calendar_announcement) = 0`, removes the need for the fixture. **It does not.** Gate F
§9.3's arithmetic and Gate F §3.10's evidence obligation are separate requirements:

| Operator manifest state | `U(announcement)` | Ceiling contribution | Fixture required |
|---|---|---|---|
| Valid and explicitly empty | 0 | zero | **yes — unchanged** |
| Valid and non-empty | *m* > 0 | `m × A_reachable` | **yes — unchanged** |
| Missing or unconfirmed | **undefined** | planning cannot run | **yes**, and planning is refused |

The authorities that impose the obligation independently of the arithmetic are Gate F §3.10
("`A_reachable` derived per route **and independently tested**"), Gate F §9.3a, master plan §15
lines 576–580, master plan §§16, 23, and 24, contract §4 lines 121–122, contract §18 line 512 (which
stops on an `A_reachable` that is underived **or untested**), and offline-rehearsal pass criterion 9.

**A zero `U(route)` never waives the independent `A_reachable` witness.** This sentence is the
operative ruling and is restated in the contract, the master plan, the rehearsal spec, and the Gate F
checklist.

### 4.2 Operator-manifest state at this record's date

The in-repository `CALENDAR_EVIDENCE_MANIFEST` is provably empty, but the planner does not read it —
`cli.py` reads the explicitly named private JSON artifact through `_read_json_artifact()`. The owner
has declared an external evidence root and has placed an explicit, valid, empty operator manifest
(`{"entries": []}`) at a path relative to that root. That artifact is **owner-supplied external
evidence** and is not provable from Git; it is recorded here as a declared fact, not as a verified
repository state.

Accordingly `U(sec_edgar_calendar_announcement) = 0` is a **deliberate, inspectable Gate F input**
with a definite provenance, not an undefined term and not an inference. The distinction matters: a
*missing* manifest makes `U` unknown and stops Gate F, whereas an *explicitly empty* one makes it
zero lawfully.

## 5. Ruling N5 — one new reason code

**Decision 028 §6's word "exactly" and §12's closed-delta wording are narrowly superseded** solely to
admit one additional code. The delta is otherwise closed; no second code is authorized by this
record.

| Field | Value |
|---|---|
| Code | `OFFLINE_REHEARSAL_SCENARIO_MISMATCH` |
| Category | `integrity` |
| `blocks_release` | `true` |
| `requires_manual_review` | **`false`** |
| Decision reference | this record |

**Semantics.** The code is recorded when a rehearsal scenario does not reach the state its
specification names — a scripted path that ends in the wrong terminal condition, a witness whose
observed attempt count disagrees with the state machine, or a report whose tested key set omits a
derived route. It is an integrity failure of the **evidence**, and it blocks release.

**`requires_manual_review = false` is an owner ruling of this record.** No accepted document compels
either value: category `integrity` does not imply it, Decision 028 §6 does not assign it, and the
receipt specification treats it as independent metadata. The drafting recommendation carried `true`
as a conservative default and explicitly flagged it as the recommender's own judgment rather than an
inherited requirement. The owner ruled `false` on 2026-08-02. `blocks_release = true` is retained
and is what actually stops a release; the manual-review flag adds a separate workflow obligation
that the owner declined to impose for this code.

**Receipt schema is unchanged.** `m3-execution-receipt/2.0` is preserved in full — every field, every
type, the status vocabulary, the canonicalization rule, and the digest preimage. Registering a
reason code adds a permitted **value**, not a schema element. **No migration is created, and none is
authorized.**

## 6. Ruling R3 — the M3.1A phase-token predicate

Recorded as contract-conformance code work requiring **no** supersession, and stated here so the
requirement is unambiguous.

`m3 rehearse` may emit `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED` only when **all four** hold:

```text
report.passed and report.complete and report.a_reachable_agrees and report.a_reachable_fully_tested
```

`m3 rehearse-report` must **recompute** rather than trust a stored report: the authoritative derived
route key set, exact tested-key equality against it, an empty `unmeasured_routes`, and numeric
agreement. `_bounds_agree()` must not accept a subset. A diagnostic subset run may complete as a
command but must never emit the phase token.

A failing scenario records `completion_status = "failed"` with
`reason_code = "OFFLINE_REHEARSAL_SCENARIO_MISMATCH"`. `SEC_ACQUISITION_INTERRUPTED` is preserved for
genuine acquisition interruption only.

## 7. The `A_reachable` witness must be one realizable path

The rehearsal's present measurement adds three separately measured terms — retry attempts, cooldown
continues, and redirect hops — and compares the sum against the derivation. That is not a witness:
it proves each term separately reachable and never proves the composite path realizable. It is
replaced by **one black-box `SecClient.fetch()` execution per route**, whose observed transport
attempt count is the tested bound.

The scripted paths, and the counts they must produce with the state machine unchanged:

| Routes | Scripted path | Attempts |
|---|---|---|
| The four exact singleton routes, and `sec_edgar_calendar_announcement` | `503 × 4` → unqualified `429` → **active** same-path/only-path redirect refusal | **6**, with zero accepted redirect hops |
| `sec_edgar_filing_calendar` | `503 × 4` → `429` → one accepted in-family redirect → terminal response | **7** |
| `sec_full_index_company` | `503 × 4` → `429` → five accepted unique in-family redirects → terminal response | **11** |

The four singleton routes must **actively receive and reject** a redirect response. Returning zero
hops without exercising the resolver is a test failure, because it would prove only that the
measurement never asked.

## 8. The ceiling formula is per-route and is not a single multiplier

Restated because a fixed multiplier was withdrawn by Decision 027 §0 items 5–6 and asserting one is
a Gate F blocker. `U` is a **per-route** planned unique-logical-request count, not a scalar, and
`A_reachable` is likewise per-route:

```text
hard_request_ceiling = Σ over M3.2A routes of ( U(route) × A_reachable(route) )
```

With the state machine unchanged, and writing *m* for the approved-entry count in the operator
manifest and *q* for the actual planned full-index count:

```text
A(each exact singleton route) =  6
A(sec_edgar_filing_calendar)  =  7
A(sec_edgar_calendar_announcement) = 6
A(sec_full_index_company)     = 11

hard_request_ceiling = 31 + 6m + 11q
```

For a valid, explicitly empty operator manifest this is `31 + 11q`.

One refinement is required and is recorded here because the earlier statement was incomplete: *q* is
**not** `|required_closed_quarters(coverage, as_of, include_open_quarter)|`. Contract §4 and master
plan §15 exclude catalog-satisfied instances **before** plan formation, so

```text
q = | required_index_keys − already_satisfied_index_keys |
```

The owner signs the exact integer stored as both `maximum_physical_attempts` and
`hard_request_ceiling` in the two byte-identical plans. `m3 plan-requests` emits it and
`m3 show-budget` re-renders it; **neither command approves it**.

## 9. Decision 011 consequence — the fail-closed statement, corrected

The proposal that an absent precedence-1 announcement forces every potentially affected date to
`unknown` is **too broad and is refused in that form**. Decision 011 §7 permits fallback through
lower-precedence evidence:

- a weekend resolves `non_operating`;
- a preserved annual snapshot plus the general rule can establish holidays and ordinary weekdays;
- positive EDGAR activity can establish `operating`;
- only a date with insufficient evidence resolves `unknown`.

No date-specific announcement status is ever manufactured. Where evidence is insufficient, rollover
fails closed with `OPERATING_CALENDAR_UNAVAILABLE`.

**No currently known announcement or rollover evidence is lost.** The source-controlled manifest
holds no approved entry and the operator manifest is explicitly empty, so **there are no affected
dates to name.** If a real approved announcement were later omitted, the failure mechanism would be:
`EvidenceCalendar.status_for()` falls through to snapshot/general-rule/activity evidence; an
exceptional weekday closure could then be classified `operating`, or an exceptional operation on a
listed holiday `non_operating`; and `next_operating_day()` and the temporal classifier could shift or
refuse a rollover. The affected dates would be exactly that omitted entry's `affected_dates`. None
are presently recorded.

## 10. What this record does not do

It grants no network authority, authorizes no live SEC request, creates no migration, changes no
receipt schema field or digest preimage, changes no cohort window, cutoff, seed, selection rule,
reserve rule, manifest rule, hash preimage, or S4/S5/S6 behaviour, closes no limitations-register
entry, and creates no tag. It does not accept M3.1, and it does not authorize the `m3.1-complete`
tag.

## 11. Authorized paths

Governance amendment, before any code edit:

- `Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md` (this record)
- `Docs/Decisions/decision_registry.md`
- `Docs/Decisions/decision_028_m3_1_readiness_corrections.md` — **append-only** supersession note and
  clearly historical "next action" wording only
- `Milestones/contracts/m3_1.md`
- `Docs/m3/offline_rehearsal_spec.md`
- `Milestones/milestone_03_master_plan.md`
- `Docs/m3/templates/gate_f_checklist.md`
- `Docs/m3/templates/request_budget.md`
- `Docs/m3/execution_receipt_spec.md` — **controlling-record/status header only**
- `Milestones/STATUS.md`, `Milestones/contracts/README.md`, `Docs/architecture_map.md`,
  `Docs/decision_index.md`, `Docs/change_impact_map.md`, `README.md`

The current-state files are corrected **only** to say what is true: the M3.1 implementation exists,
is not accepted, Decision 029 remediation is next, and the first durable §17 review and Gate F both
remain outstanding. **No file may claim completion**, and the final "complete / accepted / next
action" wording lands only in the master-plan §33 governance acceptance commit of §12 step 15.

Code remediation, after the governance amendment:

- `src/disclosure_drift/m3/rehearsal.py`
- `src/disclosure_drift/cli.py`
- `src/disclosure_drift/reasons.py`
- `tests/unit/test_m3_rehearsal.py`, `tests/integration/test_m3_cli.py`,
  `tests/unit/test_reasons.py`, `tests/unit/test_m3_receipt.py`,
  `tests/unit/test_sec_http_client.py`

Prohibited and unchanged: `pyproject.toml`, production calendar evidence, every migration, every
configuration, accepted S4/S5/S6 code, and the protected no-network test.

Installing the already-declared `[sec]` extra into the virtual environment is **permitted** and is
not a `pyproject.toml` edit. It grants no retrieval authority. `pyproject.toml` must be proven
byte-identical to the baseline before and after.

## 12. Required end-state sequence

The placement of `m3.1-complete` before Gate F is **prohibited**: contract §20 requires the
owner-approved M3.2A budget and ceiling before the overall token, and master plan §34 permits the tag
only after independent acceptance. The valid sequence is:

1. Verify the `458a741` baseline and the live remote; no fetch.
2. Draft and owner-accept this record.
3. Make the pre-code governance amendment, including the interim current-state correction.
4. Implement the bounded code and test remediation.
5. Install `[sec]`; run targeted and full validation; prove protected paths unchanged.
6. Freeze the implementation SHA.
7. Obtain the **first durable §17 review** from a non-author session and retain its artifact.
8. Owner supplies a backed-up external evidence root, a valid explicit operator manifest, and the
   remaining plan inputs.
9. Run the full M3.1A rehearsal; record the token only if all four predicates pass.
10. Run `m3 plan-requests` twice to different immutable output names; require byte-identical plans.
11. Run `m3 show-budget`; the owner signs the exact emitted `hard_request_ceiling`.
12. Complete and sign Gate F.
13. Record `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION`.
14. Perform the separate independent M3.1 acceptance review.
15. Create the master-plan §33 governance-only acceptance commit, where the final "complete /
    accepted / next action" status and navigation corrections land.
16. With explicit tag authorization, create the annotated `m3.1-complete` at that commit.
17. Only then draft the bounded M3.2 contract.

No M3.1A token, Gate F, numeric owner signature, overall token, acceptance commit, or tag may be
produced before step 7 completes.

## 13. The first durable §17 review artifact

A non-author session must create, at the frozen implementation SHA:

```text
Docs/m3/reviews/m3_1_section_17_review_<FULL_REVIEWED_SHA>.md
```

It must contain the reviewer session and model identifier with a non-authorship attestation, the UTC
review date, the exact reviewed commit and tree SHA, the live remote SHA and clean-status evidence,
the reviewed diff boundaries, every validation command and its result, a finding table with
dispositions, the master-plan §26 answer, the exact verdict
`M3_1_SECTION_17_REVIEW: PASS` or `M3_1_SECTION_17_REVIEW: FAIL`, and a reviewer signature.

It is committed governance-only, identifying the reviewed implementation SHA and proving the
implementation bytes did not change. **A FAIL artifact is retained and blocks the tokens. It is
never rewritten into a PASS.**

## 14. Formal outcome

```text
M3_1_REHEARSAL_COMPLETENESS_AND_REASON_SEMANTICS_ACCEPTED
```

**Next authorized action:** the pre-code governance amendment of §11, then the bounded code
remediation, then the first durable §17 review.
