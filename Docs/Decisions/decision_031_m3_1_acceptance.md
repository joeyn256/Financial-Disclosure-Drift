# Decision 031 — Milestone 3.1 Acceptance

**Date:** 2026-08-03
**Status:** ACCEPTED — OWNER APPROVED 2026-08-03
**Type:** Governance-only acceptance record — the master-plan §33 acceptance decision record,
created at Decision 029 §12 step 15 under the owner's explicit step-15 authorization. **Not** a
preregistration deviation. It changes no hypothesis, cohort window, maturity gate, outcome
definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash preimage, migration
byte, implementation byte, test byte, script byte, or configuration byte. It authorizes no network
access, no live SEC retrieval, no CompanyFacts, no acquisition, no operational catalog, no
`m3.1-complete` tag, no Decision 029 §12 step 16, and no M3.2 contract or work.
**Supersedes:** nothing. **Amends:** nothing. Decisions 013, 023, 024, and 027–030 remain unchanged
and controlling for everything they govern; the Decision 029 §12 step sequence is unchanged.
**Related:** Decisions 024 §8, 027 v0.2, 028, 029 (§12 steps 14–17; §13), 030;
[`Milestones/contracts/m3_1.md`](../../Milestones/contracts/m3_1.md) (§§16–17, 20);
[`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md) (M3.1
§§26, 33–35);
[`Docs/m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md`](../m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the durable recording of the owner's final acceptance of Milestone 3.1; the binding of
that acceptance to the independent step-14 review and the accepted M3.1 evidence identities; and
the pre-tag dispositions of M3-L11 and M3-L12.

---

## 1. Why this record is required

Decision 029 §12 step 14 — the independent M3.1 acceptance review by a session that authored none
of the M3.1 work — completed on 2026-08-03 with verdict
`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS` and classification
`STEP_14_INDEPENDENT_M3_1_REVIEW_PASS`. The owner then issued the M3.1 acceptance instrument
recorded verbatim in §4. Master plan §33 requires M3.1 acceptance to be recorded in a separate
bounded governance commit "carrying the acceptance decision record and the status and navigation
updates it requires"; Decision 029 §12 step 15 is that act. This record is that acceptance
decision record. The owner's step-15 authorization authorizes this recording only.

## 2. Verified baseline

Verified live immediately before this record was written:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| Baseline commit (`HEAD`) | `24fba32413bb6c5dade60a64182e42510afe6f88` ("Record independent M3.1 acceptance review") |
| Parent | `04ce708fd46dbcf1c2fc355f16325ecea9e1f47a` ("Record M3.1 Gate F readiness token") |
| `origin/main` at recording start | `04ce708fd46dbcf1c2fc355f16325ecea9e1f47a` — local `main` ahead by exactly the one independent-review commit, behind zero, no divergence |
| Working tree | clean; nothing staged; no non-ignored untracked path; no tag at HEAD; `.env` ignored and invisible to status |
| Frozen accepted implementation SHA | `970e050deb06910adcde8588101564beb7d19c74` (tree `d0c3c94cbf9128eaf0fdb1ef58179d9977d718d3`) |
| Implementation and test bytes | byte-identical from the frozen SHA through the baseline commit (empty diff over `src`, `tests`, `scripts`, `Makefile`, `pyproject.toml`, `configs`, `.github`) |
| Decision numbering | directory and registry both end at Decision 030; 031 is the next genuinely unused number |

## 3. The accepted independent step-14 review

| Field | Value |
|---|---|
| Artifact | `Docs/m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md` |
| Artifact SHA-256 | `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e` (recomputed at this recording) |
| Review commit | `24fba32413bb6c5dade60a64182e42510afe6f88` |
| Reviewed baseline | `04ce708fd46dbcf1c2fc355f16325ecea9e1f47a` (tree `5c4208c7e1debae1086fa2b9a38ee9f816b874e4`) |
| Verdict | `M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS` |
| Independence | fresh non-author session; non-authorship attested in the artifact |
| Validation record | Python 3.12.13; SQLite 3.53.4; ruff pass; ruff format pass; mypy pass over 75 source files; full suite 2739 passed / 1 pre-existing skip; secrets pass; hygiene pass; `[sec]` installed with the transport test run rather than skipped; zero live SEC access |
| Findings | zero BLOCKER; zero MAJOR; three MINOR (accepted in §5); zero OPTIMIZATION |
| Forty-question adversarial matrix | all forty answered in the accepting direction, including the token-mechanism (E19–E27) and evidence-index (F28–F34) authority questions |

## 4. The owner acceptance instrument (verbatim, received 2026-08-03)

```text
OWNER_M3_1_ACCEPTANCE_DECISION: APPROVED
The project owner accepts Financial Disclosure Drift Milestone 3.1.
Date:
2026-08-03
Accepted repository baseline reviewed by the independent session:
04ce708fd46dbcf1c2fc355f16325ecea9e1f47a
Independent M3.1 acceptance-review commit:
24fba32413bb6c5dade60a64182e42510afe6f88
Independent M3.1 acceptance-review artifact SHA-256:
caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e
Independent-review verdict:
M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS
Frozen accepted implementation SHA:
970e050deb06910adcde8588101564beb7d19c74
Frozen implementation tree:
d0c3c94cbf9128eaf0fdb1ef58179d9977d718d3
Signed Gate F checklist SHA-256:
34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc
Gate F readiness-token record SHA-256:
b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e
Request-plan SHA-256:
19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68
Request-budget SHA-256:
2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f
Approved hard request ceiling:
801
The owner accepts the independent review's three MINOR findings as
nonblocking:

1. The invalid first test-suite run caused by machine-wide temporary-storage
exhaustion was discarded, temporary regenerable files were removed, and
the complete suite was rerun successfully without changing repository,
evidence, or user data.
2. Existing evidence backups are same-device accidental-deletion protection,
not off-device disaster-recovery copies.
3. The older M3-L12 limitations-register wording is controlled and superseded
for Gate-F purposes by accepted Decision 030 Ruling D.

The owner finds that:

1. The accepted M3.1 implementation satisfies its governing contract.
2. Decision 029 §12 steps 1–14 were completed in the required order.
3. The offline rehearsal, deterministic planning, request budget, signed Gate F
checklist, and readiness-token records are internally consistent.
4. The readiness token records readiness only.
5. No live SEC acquisition, operational catalog creation, Gate F execution, or
M3.2 implementation has begun.
6. M3-L11 and M3-L12 may be closed only according to their exact accepted
checkpoint criteria. This owner decision does not prematurely claim any
tag-dependent closure.
7. D023-O1 remains a latent fail-closed owner-referral condition and is
nonblocking unless triggered by a lawful later run.

Recorded acceptance reference:
ChatGPT owner M3.1 acceptance dated 2026-08-03, bound to independent-review
commit 24fba32413bb6c5dade60a64182e42510afe6f88 and independent-review artifact
SHA-256 caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e.
This is a transparent recorded owner acceptance reference, not a handwritten,
cryptographic, or third-party digital signature.
This decision authorizes Decision 029 §12 step 15 only: faithful durable
recording of the M3.1 acceptance in a governance-only acceptance commit.
It does not authorize the `m3.1-complete` tag, Decision 029 §12 step 16,
creation of the bounded M3.2 contract, live SEC access, controlled acquisition,
or any M3.2 execution.
```

Owner: **Joseph Nihill, project owner acting through the ChatGPT owner decision.** The recorded
acceptance reference above is a transparent recorded owner acceptance reference; it is not a
handwritten, cryptographic, or third-party digital signature.

## 5. What is accepted

The owner accepts **Milestone 3.1 in full**, comprising:

- the frozen implementation at `970e050deb06910adcde8588101564beb7d19c74`
  (tree `d0c3c94cbf9128eaf0fdb1ef58179d9977d718d3`), byte-identical through the accepted baseline,
  independently reviewed by the first durable §17 review (`M3_1_SECTION_17_REVIEW: PASS`;
  sanitized identity `9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3`;
  historical pre-redaction identity
  `73cb1eacf0fb5e29a8a1c2ea871692068caf3ebdc48cae161d6aef677ba8f3a3` per Decision 030);
- the M3.1A operational rehearsal (all twelve A1–A12 PASS; nine-route `A_reachable` witness
  complete; `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED` emitted by the canonical command; zero
  actual requests);
- the two byte-identical zero-request M3.2A plans
  (`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; q = 70; 75 planned unique
  logical requests) and their validating dry-run receipts;
- the owner-approved M3.2A request budget
  (`2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f`) with the exact hard request
  ceiling **801** and the three response-outcome markers Decision 030 Ruling C permits;
- the owner-signed Gate F checklist
  (`34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc`; result `PASS`);
- the step-13 Gate F readiness-token record
  (`b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e`; the token
  `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION` recorded exactly once; readiness only);
- the public evidence index rows `EV-M31A-001`–`EV-M31B-006` with the recorded owner attestation;
- and the independent step-14 acceptance review of §3, whose three MINOR findings the owner
  accepts as nonblocking exactly as stated in the §4 instrument.

## 6. Limitation dispositions at step 15

- **M3-L11 — `CLOSURE-READY PENDING STEP 16`.** Every closure-evidence item exists — the exact
  `.gitignore` entry, the hygiene refusal for a file/directory/symlink at the reserved path, the
  resolved-path CLI tests including ancestor and symlink bypasses, full validation, and
  independent M3.1 acceptance with the owner acceptance recorded by this decision — except the
  **committed checkpoint**, which is the step-16 `m3.1-complete` tag. The entry is **not closed**
  by this record.
- **M3-L12 — `CLOSURE-READY PENDING STEP 16`.** Decision 030 Ruling D's controlling distinction is
  preserved exactly: *Gate-F-facing requirement satisfied; administrative closure deferred to the
  later M3.1 acceptance and checkpoint sequence.* The acceptance half of that sequence is now
  recorded; the **committed checkpoint** (the step-16 tag) is the sole remaining closure
  criterion. The entry is **not closed** by this record, and Decision 013 remains byte-for-byte
  unchanged.
- **D023-O1 — `LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED`** (Decision
  030 Ruling E, unchanged). If a lawful real run ever reaches the empty sole-carrier condition,
  the phase stops and refers it to the owner.

## 7. What this record does not do

It does not create or authorize the `m3.1-complete` tag; does not begin or authorize Decision 029
§12 step 16 or 17; does not create, draft, or authorize the bounded M3.2 contract; does not
authorize live SEC access, network or CompanyFacts enablement, connectivity testing, controlled
acquisition, or the operational catalog; does not close M3-L11, M3-L12, or any limitations-register
entry; does not alter the independent review artifact, the signed checklist, the token record, or
any private evidence; and does not change any implementation, test, script, configuration, or
migration byte. The Decision 029 §12 sequence remains frozen; steps 16 and 17 remain separately
owner-gated.

## 8. Acceptance criteria for this record

All verified before the step-15 commit: (1) the step-14 review artifact re-hashes to
`caf9f26e…c5ae4e` and its commit is the baseline `HEAD`; (2) implementation and test bytes remain
byte-identical to the frozen SHA; (3) Decision 031 is unique — no other decision file or registry
row carries the number; (4) the registry, status ledger, and limitations register updates match
this record exactly; (5) `git diff --check`, `make context`, `make secrets`, and `make hygiene`
pass over the updated tree; (6) the acceptance commit carries only the authorized governance
records; (7) no tag is created; (8) no private path, SEC identity, or private evidence content
appears in any changed file.

## 9. Formal outcome

```text
M3_1_ACCEPTED_AND_COMPLETE
```

Milestone 3.1 is owner-accepted and complete. The `m3.1-complete` annotated tag is **not** created
by this record: master plan §34 places it at the accepted commit only under a separate explicit
owner authorization (Decision 029 §12 step 16).

**Next authorized action:**
`OWNER_AUTHORIZATION_OF_DECISION_029_SECTION_12_STEP_16_M3_1_COMPLETE_TAG` — the owner authorizes
(or declines) the annotated `m3.1-complete` tag at the accepted step-15 commit. Step 17 (the
bounded M3.2 contract) follows only after step 16, under its own explicit owner authorization. No
live SEC access and no M3.2 work is authorized.
