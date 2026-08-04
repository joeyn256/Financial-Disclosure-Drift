# Decision 030 — Gate F Step-12 Owner Rulings and Hygiene Remediation

**Date:** 2026-08-03
**Status:** ACCEPTED — OWNER APPROVED 2026-08-03
**Type:** Bounded governance-remediation and owner-interpretation record. **Not** a preregistration
deviation. It changes no hypothesis, cohort window, maturity gate, outcome definition, threshold,
seed, selection methodology, S4/S5/S6 identity, hash preimage, migration byte, implementation byte,
test byte, script byte, or configuration byte. It authorizes no network access, no live SEC
retrieval, no SEC-identity configuration, no push, no tag, no checklist signature, no readiness
token, and no Gate F, M3.2, or later work.
**Supersedes:** nothing. **Amends:** nothing. Decisions 013, 023, 027, 028, and 029 remain
unchanged and controlling for everything they govern; the Decision 029 §12 step sequence is
unchanged.
**Related:** Decisions 023, 027, 028, and 029;
[`Milestones/contracts/m3_1.md`](../../Milestones/contracts/m3_1.md);
[`Docs/m3/templates/gate_f_checklist.md`](../m3/templates/gate_f_checklist.md);
[`Docs/m3/templates/request_budget.md`](../m3/templates/request_budget.md);
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md);
[`Docs/m3/reviews/m3_1_section_17_review_970e050deb06910adcde8588101564beb7d19c74.md`](../m3/reviews/m3_1_section_17_review_970e050deb06910adcde8588101564beb7d19c74.md).
**Governs:** the Decision 029 §12 step-12 repository-hygiene remediation of the first durable §17
review artifact; the treatment of that artifact's pre-redaction and sanitized identities; and the
owner's Gate F interpretation rulings for the three unresolved request-budget markers, for
M3-L12's Gate-F-facing requirement, and for D023-O1.

---

## 1. Why this record is required

Decision 029 §12 step-12 preparation completed on 2026-08-03 (status commit
`33bf0a35a025b6fd7ab282d6acd24c4ef6acb286`) and classified `STEP_12_BLOCKED` on exactly one
finding: the committed first durable §17 review artifact carried one machine-local absolute path
in its clone-provenance sentence, which `scripts/check_repo_hygiene.py` refuses ("absolute home
path") and which master plan M3.1 §17 stop condition 12 names as a class. The accepted review
artifact may not be altered by a session on its own authority, and the preparation task was
authorized to touch no path that could remediate it. This record supplies the owner authority for
a bounded, provably non-substantive redaction and records the interpretation rulings the owner's
step-12 signature decision requires. The ChatGPT owner issued rulings A–E on 2026-08-03; this
record is their durable form.

## 2. Verified baseline

Verified live immediately before the remediation:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| Baseline commit (`HEAD`) | `33bf0a35a025b6fd7ab282d6acd24c4ef6acb286` (`Record M3.1B plan and ceiling approval`) |
| Working tree | clean; nothing staged; no untracked path; `git diff --check` clean |
| Tags at HEAD | none; latest repository tag `m2.3-s6-complete` |
| Frozen reviewed implementation SHA | `970e050deb06910adcde8588101564beb7d19c74` |
| Protected bytes | `src`, `tests`, `scripts`, `pyproject.toml`, `Makefile`, and `configs` byte-identical from the frozen SHA through the baseline commit (empty diff) |
| Hygiene at baseline | FAILED — exactly one finding: the §17 review artifact, one absolute home path in its clone-provenance sentence; no second finding anywhere in the tracked tree |
| Secret scan at baseline | passed, 0 findings |
| Accepted step-12-preparation evidence | private M3.2A request-budget document `sha256:2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f`; request-plan `sha256:19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; owner-approved hard request ceiling `801` (2026-08-03) |

## 3. Ruling A — bounded hygiene remediation

**The owner authorizes exactly one redaction** in
`Docs/m3/reviews/m3_1_section_17_review_970e050deb06910adcde8588101564beb7d19c74.md`: the
machine-local absolute path material in the §5 clone-provenance sentence — the disposable clone's
own machine-local absolute path and the machine-local `file://` clone-source token that the
hygiene gate flagged — is replaced with the owner's neutral wording, grammar minimally adapted:

> an external independent clone whose machine-local absolute path is redacted for repository
> hygiene, cloned from the local primary repository checkout

Every provenance claim of the sentence is preserved: a fresh disposable clone; the author
session's clone not reused; the clone external and independent; cloned from the local primary
repository checkout; checked out detached-HEAD at the frozen implementation SHA; and the in-clone
verification values (`HEAD`, `HEAD^{tree}`, clean status) byte-unchanged.

This ruling does **not**: weaken or modify the hygiene scanner; create an allowlist; exempt
`Docs/m3/reviews` or any other path; waive the hygiene gate; delete the review artifact; replace
the review with a different analysis; rerun or rewrite any review finding; or change the review
verdict. No other review statement is changed.

## 4. Ruling B — review validity and the two artifact identities

**The redaction is non-substantive**, and the accepted §17 review remains valid **only because** a
normalized before/after comparison proved that the sole change is the single approved
substitution: the pre-redaction text with that one substitution applied is byte-identical to the
sanitized artifact, and the reverse substitution reproduces the pre-redaction bytes exactly.

| Identity | Value |
|---|---|
| Pre-redaction artifact SHA-256 — **the historical artifact identity** | `73cb1eacf0fb5e29a8a1c2ea871692068caf3ebdc48cae161d6aef677ba8f3a3` |
| Sanitized artifact SHA-256 — the current tracked identity | `9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3` |
| Relationship | The sanitized artifact is the pre-redaction artifact with exactly one approved provenance-wording substitution; every finding, table, command result, SHA claim, classification, adjudication, limitation, and acceptance statement is byte-unchanged |
| Verdict | `M3_1_SECTION_17_REVIEW: PASS` — unchanged, occurring exactly once before and after |
| Completion-token literals in the artifact | zero before, zero after; none added |

**Git history is not rewritten.** The commit that introduced the pre-redaction artifact
(`66e4c5433a393815c74f9e3087300613a516e2fb`) remains part of the local audit trail, and the
pre-redaction bytes remain recoverable from it. The pre-redaction SHA-256 above remains the
historical identity of the review as owner-accepted; the sanitized SHA-256 identifies the tracked
artifact from this record forward. Any future reference to the review should cite the sanitized
identity, and may cite the pre-redaction identity for the historical acceptance event.

## 5. Ruling C — the three unresolved request-budget quantities

The three `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` markers in the accepted private
M3.2A request-budget document are **permitted and nonblocking**. They apply **only** to:

- expected successful responses;
- expected not-modified responses;
- expected governed non-success responses.

Every budget §3 route count is resolved by the accepted deterministic zero-request plan
(request-plan `sha256:19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`); **no
route-count sentinel remains**, so Gate F item 9.2 is satisfied on its stated §3 scope. The three
response-outcome expectations are **intentionally resolved during controlled acquisition**, not
before it, and **no integer may be guessed** for any of them. This ruling makes the markers no
obstacle to checklist preparation, the owner's step-12 signature, the step-13 readiness token, or
Gate F.

## 6. Ruling D — M3-L12

For Decision 029 §12 steps 12 and 13 the owner records:

```text
M3-L12 GATE-F-FACING REQUIREMENT: SATISFIED
```

Supporting evidence: the accepted Decision 028 owner ruling (§4); planner policy
`quarterly-index-instances/2.0` implemented in the frozen reviewed tree; the accepted boundary
tests (exact quarter end, interior date, future quarter, open quarter, caller-version refusal);
Decision 013 byte-for-byte unchanged; and the accepted deterministic request plan whose
required-quarter set includes the closed `2026QTR2` and excludes `2026QTR3` and `2026QTR4`.

The limitations-register entry may remain administratively `ACTIVE` until the later independent
M3.1 acceptance and checkpoint sequence. The controlling distinction is exactly:

> Gate-F-facing requirement satisfied; administrative closure deferred to the later M3.1
> acceptance and checkpoint sequence.

The deferred administrative closure does **not** block: checklist preparation; the owner's step-12
signature; the step-13 readiness token; or beginning Gate F after valid step-13 authorization.
**The register entry is not finally closed by this record**, and no session may close it; closure
follows the register's own closure-evidence list at the later acceptance and checkpoint sequence.

## 7. Ruling E — D023-O1

The owner records:

```text
D023-O1: LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED
```

D023-O1 remains unresolved because no real run has reached the empty sole-carrier crosswalk
condition it describes. It does **not** block step 12, step 13, or Gate F unless a lawful real run
reaches that condition. If a lawful real run ever reaches it, the phase **stops and refers it to
the owner** — it is never resolved by a session reclassifying an item, adding a category, or
changing a count (Decision 023 §7 O1; Decision 021 §§13.3, 21). This ruling restates and applies
the accepted rule; it does not resolve, close, or pre-resolve the condition.

## 8. What this record does not do

It does not sign, complete, or instantiate the Gate F checklist; does not emit or authorize
`M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION`; does not authorize live SEC access,
network enablement, SEC-identity configuration, branch synchronization or any push, the
operational catalog, M3.1 final acceptance, the `m3.1-complete` tag, or any M3.2 or later work. It
closes no limitations-register entry, rewrites no history, alters no implementation, test, script,
configuration, template, or private-evidence byte, and changes no accepted decision. The Decision
029 §12 sequence remains frozen; steps 12 and 13 remain owner acts.

## 9. Acceptance criteria

All of the following, verified before this record's commit:

1. the flagged machine-local absolute path is absent from the entire tracked tree;
2. the normalized comparison proves the sole change is the single approved substitution, in both
   directions;
3. `M3_1_SECTION_17_REVIEW: PASS` occurs exactly once in the sanitized artifact, and no
   completion-token literal was added;
4. `make hygiene` passes with zero findings; `make secrets` passes; `make context` succeeds;
5. `src`, `tests`, `scripts`, `pyproject.toml`, `Makefile`, and `configs` remain byte-identical to
   the frozen reviewed implementation SHA;
6. Decision 030 is unique in the registry and this file is the only decision numbered 030;
7. `Milestones/STATUS.md` records the resolved blocker and the exact remaining owner-side step-12
   actions truthfully, claiming no signature, no token, and no Gate F;
8. one bounded governance commit carries exactly the authorized paths.

## 10. Stop and rollback conditions

**Stop before commit** if: the normalized equivalence cannot be proven; the verdict count changes;
any completion-token literal appears; a second hygiene finding exists; an unauthorized path
changes; or the registry becomes inconsistent. **Rollback before commit** is a reviewable discard
of only the working changes under explicit owner instruction. **After commit**, a correction is a
new dated decision record — never a history rewrite and never an in-place edit of an accepted
record.

## 11. Formal outcome

```text
GATE_F_STEP_12_OWNER_RULINGS_AND_HYGIENE_REMEDIATION_ACCEPTED
```

**Next authorized action:**
`OWNER_PROVISION_SEC_CONTACT_IDENTITY_AND_AUTHORIZE_BRANCH_SYNCHRONIZATION_AND_FINAL_STEP_12_SIGNING_PREFLIGHT`
— the owner provisions and validates the SEC contact identity, decides branch synchronization or
live `HEAD == origin/main` verification, records the operator acknowledgement, and then reviews
and signs (or declines) the Decision 029 §12 step-12 Gate F checklist. No session may perform any
of those acts for the owner.
