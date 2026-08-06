# Decision 039 — M3.2 Stage T2.2–T2.3 Acceptance and Publication Authorization

**Date:** 2026-08-06
**Status:** ACCEPTED — OWNER APPROVED 2026-08-06
**Type:** Bounded governance record accepting one implementation stage and authorizing its normal
publication.
**Not** a preregistration deviation. It changes no hypothesis, cohort window, maturity gate, outcome
definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash preimage, migration
byte, implementation byte, test byte, script byte, or configuration byte — **no executable byte
changes with this record**.
**Amends:** nothing. No accepted decision is edited in place; the T2 authorization packet is
preserved byte-identical; the accepted M3.2 contract is not edited; both M3.2 review artifacts and
[Decision 038](decision_038_m3_2_t2_2_t2_3_path_envelope_amendment.md) are preserved unchanged.
Stage progress is recorded here and in the ledger rather than in the contract.
**Related:** Decisions 024 §8, 034, 035, 036, 037, 038; the T2 packet
[revision v2](../m3/m3_2_t2_implementation_authorization_packet.md); the accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's acceptance of the combined Milestone 3.2 implementation stage T2.2–T2.3
and the authorization to publish it by one normal fast-forward push.

---

## 1. What this record accepts, and what it does not

This record makes **three distinct determinations**, which must not be collapsed:

1. **Stage acceptance.** The combined Milestone 3.2 implementation stage **T2.2–T2.3 — Catalog,
   Immutable Storage, and Acquisition Engine** is accepted, at the exact candidate named in §3.
   Formal classification: **`M3_2_T2_2_T2_3_ACCEPTED_AND_COMPLETE`**.
2. **Publication of that stage.** One normal fast-forward push of `main` is authorized, publishing
   the exact three-commit sequence in §5. Publication is the act of making the accepted stage
   visible on the remote; it is not a further acceptance and it confers no new authority.
3. **What remains outstanding.** **Overall Milestone 3.2 implementation acceptance is the separate
   later T3 act and has NOT occurred.** Accepting one stage of a four-stage cadence does not accept
   the milestone's implementation. Stage **T2.4** and combined stage **T2.5–T2.6** remain
   owner-gated, unauthorized, and not begun; the T2.5–T2.6 commit remains the implementation-freeze
   candidate for the independent T3 review (Decision 037). **Nothing in this record may be read as
   T3, T4, T5, or Gate H satisfaction.**

## 2. Adopted technical findings

The owner adopts the findings of the final independent, adversarial, no-subagent technical rereview
of the second-corrected candidate, conducted by a session that authored none of the candidates,
corrections, tests, prior reviews, the M3.2 contract, Decisions 034–037, or the T2 packet:

1. Every technical PASS condition for the combined T2.2–T2.3 stage was met.
2. Archive transport and candidate-owned archive-member lineage are **memory-bounded**.
3. Archive-member persistence is **single-pass, deterministic, and transactional**.
4. Failed member enumeration or insertion leaves **no partial catalog transaction**.
5. Archive reuse, supersession, immutable-object preservation, and lineage reconciliation are
   correct.
6. ZIP fixtures are deterministic and independent of the wall clock, locale, timezone, and building
   platform.
7. Bounded operational-error outputs do not disclose private paths or payloads.
8. Request-plan, route, ceiling, completion, recovery-observability, and no-network boundaries
   remain **fail-closed**.
9. Required static, targeted, mutation, determinism, and full-suite validation passed.
10. **No live SEC access, operational catalog, receipt, evidence artifact, or ceiling usage
    occurred.**

The rereview's verdict was
`M3_2_T2_2_T2_3_SECOND_CORRECTED_INDEPENDENT_REREVIEW: PASS_WITH_REQUIRED_CORRECTIONS`, with **zero
BLOCKER**. It withheld a clean PASS **solely** because two implementation paths were not covered by
the last durably recorded authorization envelope — a governance-record defect that required no code
change.

## 3. Accepted identities

| Item | Value |
|---|---|
| Accepted implementation candidate | `6b189df1651ec3674ec7f96a1f5d66f488c654a9` |
| Accepted implementation tree | `8850e1e45e9471bbb8b94612da67715e932a496f` |
| Published baseline and candidate parent | `feb9e134307a9551475f243dc0c1ddcecc89ffde` |
| Stage commit subject | `Implement M3.2 T2.2-T2.3 acquisition foundation` |
| Decision 038 governance commit | `27842965ed5a8fcccbf5fbb3c3c63ff2c2e798ba` |
| Decision 038 governance tree | `6bead61920ad947d35b300e9d81634ca5c767358` |
| Accepted contract (unchanged) | SHA-256 `c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7` |
| Historical T2 packet (byte-identical) | SHA-256 `621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599` |

The accepted candidate changes exactly six paths:
`src/disclosure_drift/m3/__init__.py`, `src/disclosure_drift/m3/acquisition.py`,
`src/disclosure_drift/sec/observation_catalog.py`, `tests/integration/test_m3_cli.py`,
`tests/unit/test_m3_acquisition.py`, and `tests/unit/test_observation_catalog.py`.

## 4. Decision 038 dependency

Two of those six paths — `src/disclosure_drift/sec/observation_catalog.py` and
`tests/unit/test_observation_catalog.py` — lay outside the Decision 035 §6 fifteen-path maximum
envelope. Accepted [Decision 038](decision_038_m3_2_t2_2_t2_3_path_envelope_amendment.md)
(2026-08-05, outcome `M3_2_T2_2_T2_3_PATH_ENVELOPE_AMENDMENT_RECORDED`) resolved that
governance-record defect by narrowly authorizing exactly those two paths, for the combined T2.2–T2.3
stage only, bound to and limited by the exact changes in candidate `6b189df1…` / tree `8850e1e4…`.

**Decision 038 is accepted as the controlling higher-authority amendment for those paths and
purposes.** This record depends on it: without Decision 038 the candidate would exceed its recorded
envelope, and stage acceptance would not be available. Decision 038's own limits carry forward
unchanged — in particular, it authorizes **no further edit** to either path beyond tree `8850e1e4…`,
and it does **not** carry the path expansion into T2.4 or T2.5–T2.6 (§7).

## 5. Publication authorization

The owner authorizes **one normal fast-forward push** of branch `main`, publishing in this order:

1. implementation candidate `6b189df1651ec3674ec7f96a1f5d66f488c654a9`;
2. Decision 038 governance commit `27842965ed5a8fcccbf5fbb3c3c63ff2c2e798ba`;
3. the Decision 039 stage-acceptance governance commit created from this instrument.

The push may occur **only after** every one of the following holds:

- Decision 039 is durably recorded;
- the registry and `Milestones/STATUS.md` records agree;
- candidate bytes remain unchanged;
- the contract and authorization-packet hashes remain unchanged;
- `origin/main` is verified as an **ancestor** of local `HEAD`;
- the branch is **behind by zero** and has **no divergence**;
- repository governance validation passes.

**No tag is authorized for this stage.** No force push, no history rewrite, no rebase, no squash,
no amend, and no refspec that bypasses normal branch protection.

## 6. Deferred obligations remaining open

Acceptance of this stage closes none of the following. Each remains open for a later authorized
stage:

1. **Owner adjudication of singleton bootstrap-absence reason authority**, required *before* the
   T2.4 absence enumeration is implemented.
2. **Catalog-authoritative adoption after quarantine**, during T2.4.
3. **Conditional-request and 304 / cache-resume handling**, during T2.4.
4. **The accepted `RawStore` resource limitation** — full-object buffering in the store layer,
   outside the candidate-owned lineage phase — as a **T4 preflight and integrated-candidate review**
   concern.
5. **Sanitization or exclusion of untrusted progress-sink messages** before any later receipt or
   indexed-artifact use.
6. **F4 evidence-index vocabulary resolution**, no later than T4 and before the first affected
   artifact is publicly indexed.
7. **D023-O1**, which remains a latent fail-closed referral condition, **unmodified**.

## 7. Negative authority

This acceptance and publication authorization does **not**:

- constitute overall M3.2 **T3 implementation acceptance**;
- authorize **T2.4**;
- carry the Decision 038 path expansion into T2.4 or T2.5–T2.6;
- authorize repair, reconciliation, drift inspection, or resume;
- authorize operator CLI wiring;
- authorize conditional requests, 304 handling, or cache resume;
- resolve singleton bootstrap-absence reason-code authority;
- resolve the F4 evidence-index vocabulary requirement;
- modify D023-O1;
- enable network or CompanyFacts;
- authorize SEC contact or connectivity testing;
- authorize creation of the real operational catalog;
- authorize receipts, private evidence, acquisition, or use of ceiling 801;
- authorize a tag, force push, history rewrite, rebase, squash, or amend.

## 8. Owner instrument (verbatim)

```
OWNER_DECISION_039_M3_2_T2_2_T2_3_STAGE_ACCEPTANCE_AND_PUBLICATION_AUTHORIZATION: APPROVED

The project owner accepts the combined Milestone 3.2 T2.2–T2.3 implementation
stage:

CATALOG, IMMUTABLE STORAGE, AND ACQUISITION ENGINE

Accepted implementation candidate:

6b189df1651ec3674ec7f96a1f5d66f488c654a9

Accepted implementation tree:

8850e1e45e9471bbb8b94612da67715e932a496f

Published baseline and candidate parent:

feb9e134307a9551475f243dc0c1ddcecc89ffde

Decision 038 governance commit:

27842965ed5a8fcccbf5fbb3c3c63ff2c2e798ba

Decision 038 governance tree:

6bead61920ad947d35b300e9d81634ca5c767358

The owner adopts the final independent technical rereview findings:

1. Every technical PASS condition for the combined T2.2–T2.3 stage was met.
2. Archive transport and candidate-owned archive-member lineage are
    memory-bounded.
3. Archive-member persistence is single-pass, deterministic, and transactional.
4. Failed member enumeration or insertion leaves no partial catalog transaction.
5. Archive reuse, supersession, immutable-object preservation, and lineage
    reconciliation are correct.
6. ZIP fixtures are deterministic and independent of the wall clock, locale,
    timezone, and building platform.
7. Bounded operational-error outputs do not disclose private paths or payloads.
8. Request-plan, route, ceiling, completion, recovery-observability, and
    no-network boundaries remain fail-closed.
9. Required static, targeted, mutation, determinism, and full-suite validation
    passed.
10. No live SEC access, operational catalog, receipt, evidence artifact, or
    ceiling usage occurred.

The final rereview withheld a clean PASS solely because two implementation
paths were not covered by the last durably recorded authorization envelope.
Decision 038 has now resolved that governance-record defect by narrowly
authorizing:

* src/disclosure_drift/sec/observation_catalog.py
* tests/unit/test_observation_catalog.py

Decision 038 is accepted as the controlling higher-authority amendment for
those paths and purposes.

The project owner therefore classifies the combined stage as:

M3_2_T2_2_T2_3_ACCEPTED_AND_COMPLETE

Publication authorization:

The owner authorizes one normal fast-forward push of branch main containing,
in order:

1. implementation candidate
    6b189df1651ec3674ec7f96a1f5d66f488c654a9;
2. Decision 038 governance commit
    27842965ed5a8fcccbf5fbb3c3c63ff2c2e798ba;
3. the Decision 039 stage-acceptance governance commit created from this
    instrument.

The push must occur only after:

* Decision 039 is durably recorded;
* registry and STATUS records agree;
* candidate bytes remain unchanged;
* the contract and authorization-packet hashes remain unchanged;
* origin/main is verified as an ancestor of local HEAD;
* the branch is behind by zero and has no divergence;
* repository governance validation passes.

No tag is authorized for this stage.

This acceptance and publication authorization does not:

* constitute overall M3.2 T3 implementation acceptance;
* authorize T2.4;
* carry the Decision 038 path expansion into T2.4 or T2.5–T2.6;
* authorize repair, reconciliation, drift inspection, or resume;
* authorize operator CLI wiring;
* authorize conditional requests, 304 handling, or cache resume;
* resolve singleton bootstrap-absence reason-code authority;
* resolve the F4 evidence-index vocabulary requirement;
* modify D023-O1;
* enable network or CompanyFacts;
* authorize SEC contact or connectivity testing;
* authorize creation of the real operational catalog;
* authorize receipts, private evidence, acquisition, or use of ceiling 801;
* authorize a tag, force push, history rewrite, rebase, squash, or amend.

The following obligations remain open for later authorized stages:

* owner adjudication of singleton bootstrap-absence reason authority before the
    T2.4 absence enumeration is implemented;
* catalog-authoritative adoption after quarantine during T2.4;
* conditional-request and 304/cache-resume handling during T2.4;
* the accepted RawStore resource limitation as a T4 preflight and integrated
    candidate review concern;
* sanitization or exclusion of untrusted progress-sink messages before any later
    receipt or indexed-artifact use;
* F4 evidence-index vocabulary resolution no later than T4;
* D023-O1 as a latent fail-closed referral condition.

After successful publication, set:

NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_M3_2_T2_4_IMPLEMENTATION_AUTHORIZATION_AFTER_T2_2_T2_3_PUBLICATION

Owner:
Joseph Nihill, acting through the ChatGPT project-owner role

Date:
2026-08-06

This is a transparent recorded owner decision, not a handwritten,
cryptographic, or third-party digital signature.
```

## 9. Formal outcome

**`M3_2_T2_2_T2_3_ACCEPTED_AND_COMPLETE`**

Publication of the accepted stage is authorized under §5 by one normal fast-forward push, with
**no tag**. Overall Milestone 3.2 implementation acceptance remains the separate later **T3** act.

`NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_M3_2_T2_4_IMPLEMENTATION_AUTHORIZATION_AFTER_T2_2_T2_3_PUBLICATION`

---

**Owner:** Joseph Nihill, acting through the ChatGPT project-owner role.
**Date:** 2026-08-06.
This is a transparent recorded owner decision, not a handwritten, cryptographic, or third-party
digital signature.
