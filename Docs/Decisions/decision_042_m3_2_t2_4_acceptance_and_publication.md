# Decision 042 — M3.2 Stage T2.4 Acceptance and Publication

**Date:** 2026-08-06
**Status:** ACCEPTED — OWNER APPROVED 2026-08-06
**Type:** Bounded governance record accepting one implementation stage and publishing it by one
normal fast-forward push. **Not** a preregistration deviation. It changes no hypothesis, cohort
window, maturity gate, outcome definition, threshold, seed, selection methodology, S4/S5/S6
identity, hash preimage, migration byte, implementation byte, test byte, script byte, or
configuration byte — **no executable byte changes with this record**.
**Amends:** nothing. No accepted decision is edited in place; Decisions 032–041 are byte-unchanged;
the historical T2 authorization packet is preserved byte-identical (SHA-256 `62120146…`); the
accepted M3.2 contract is not edited (SHA-256 `c526335b…`). Stage progress is recorded here and in
the ledger, never in the contract.
**Related:** Decisions 024 §8, 034, 035, 036, 037, 039, 040, 041; the T2 packet
[revision v2](../m3/m3_2_t2_implementation_authorization_packet.md); the accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's acceptance of Milestone 3.2 implementation stage T2.4 at the corrected
candidate named in §3, the owner's acceptance of the fresh independent corrected-candidate
rereview, and the publication of that candidate by one normal fast-forward push.

---

## 1. What this record accepts, and what it does not

This record makes **three distinct determinations**, which must not be collapsed:

1. **Stage acceptance.** Milestone 3.2 implementation stage **T2.4 — Recovery, Reconciliation,
   Resume Boundaries, and Drift Control** is accepted at the exact corrected candidate named in §3.
   Formal classification: **`M3_2_T2_4_ACCEPTED_AND_COMPLETE`**.
2. **Publication of that stage.** One normal fast-forward push of `main` is authorized, publishing
   the corrected candidate and this acceptance commit. Publication makes the accepted stage visible
   on the remote; it is not a further acceptance and it confers no new authority.
3. **What remains outstanding.** **Overall Milestone 3.2 implementation acceptance is the separate
   later T3 act and has NOT occurred.** Accepting one stage of the four-stage cadence does not
   accept the milestone's implementation. Combined stage **T2.5–T2.6** remains owner-gated and
   **has not begun**; the T2.5–T2.6 commit remains the implementation-freeze candidate for the
   independent T3 review (Decision 037). **Nothing in this record may be read as T3, T4, T5, or
   Gate H satisfaction.**

## 2. Accepted review result

The owner accepts the verdict of the fresh independent rereview of the corrected T2.4 candidate:

```text
M3_2_T2_4_CORRECTED_CANDIDATE_REREVIEW_PASS
```

Recorded review execution, exactly as the owner supplied it:

| Property | Value |
|---|---|
| Model | Claude Opus 5 |
| Effort | Max |
| Session | fresh independent session |
| BLOCKER findings | 0 |
| MAJOR findings | 0 |
| MINOR findings | 0 |
| Mandatory separate-OS-process durability challenge | PASS |
| Independent mutation campaign | 18/18 killed |
| Targeted validation | 333 passed |
| Full suite | 3053 passed / 1 pre-existing intentional skip |
| Static gates | clean |

**Artifact status, stated exactly.** The rereview reached this repository through the owner's
supplied acceptance evidence. **No rereview artifact file was previously recorded in this
repository, and none is created, reconstructed, or back-dated by this record.** No artifact path
and no artifact SHA-256 is asserted here, because none exists to assert. The owner's acceptance,
recorded in §4, is the authority for this governance operation. The one pre-existing intentional
skip is the long-standing `[sec]`-extra skip carried unchanged since Stage S5.3.

## 3. Accepted identities

| Item | Value |
|---|---|
| Accepted implementation candidate | `625c03d6931e01acc99946ca3924f1cda4da6b76` |
| Accepted implementation tree | `816fd392df859106b9ba21b684f9b4a8061461fc` |
| Candidate parent / Decision 041 governance baseline | `4897bb1d8fc5be5cd6d12be941204e377bbfa5a4` |
| Stage commit subject | `Implement M3.2 T2.4 recovery and reconciliation` |
| Accepted contract (unchanged) | SHA-256 `c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7` |
| Historical T2 packet (byte-identical) | SHA-256 `621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599` |

The accepted candidate changes exactly **eight** tracked paths, all of them inside the ten-path
maximum Decision 041 §4 fixed, with **no eleventh path**:

1. `src/disclosure_drift/m3/acquisition.py`
2. `src/disclosure_drift/m3/__init__.py`
3. `src/disclosure_drift/reasons.py`
4. `src/disclosure_drift/sec/observation_catalog.py`
5. `tests/unit/test_m3_acquisition.py`
6. `tests/unit/test_m3_recover.py`
7. `tests/unit/test_observation_catalog.py`
8. `tests/unit/test_reasons.py`

Two authorized paths — `src/disclosure_drift/m3/recovery.py` and
`tests/unit/test_m3_recovery.py` — were **not** edited. That is correct and expected: Decision 041
§4 fixes the ten paths as a **maximum, not a requirement to edit every path**.

The candidate changes **no** migration, receipt-schema, configuration, contract, packet, decision,
script, template, CI, or documentation byte. The migration chain remains exactly `0001`–`0013`, the
receipt remains `m3-execution-receipt/2.0`, and both tracked network switches remain `false`.

## 4. The owner ruling

The ChatGPT owner reviewed the completion report and the fresh independent corrected-candidate
rereview, and issued the acceptance-and-publication instruction recorded here. The authority for
this governance operation is that owner acceptance; there is no separately supplied signed
instrument block for Decision 042, and none is invented. The operative text of the owner's
acceptance is reproduced below without alteration.

```text
The owner ACCEPTS the independent rereview verdict:

M3_2_T2_4_CORRECTED_CANDIDATE_REREVIEW_PASS

The owner therefore ACCEPTS corrected T2.4 candidate:

625c03d6931e01acc99946ca3924f1cda4da6b76

Expected tree:

816fd392df859106b9ba21b684f9b4a8061461fc

Expected parent:

4897bb1d8fc5be5cd6d12be941204e377bbfa5a4

Expected subject:

Implement M3.2 T2.4 recovery and reconciliation

This acceptance is limited to M3.2 stage T2.4.

It does NOT authorize:

* T2.5 implementation;
* T2.6 implementation;
* network enablement;
* network.enabled=true;
* network.m3_acquire_enabled=true;
* CompanyFacts enablement;
* creation or use of the real operational catalog;
* live SEC acquisition;
* live SEC requests;
* use of the 801-request ceiling;
* operational execution of m3 acquire;
* any T3/T4/T5 authority not already separately granted;
* any M3.2B activity.

Record that the ChatGPT owner accepts:

1. the corrected T2.4 candidate;
2. the independent corrected-candidate rereview;
3. Decision 041's recovery-state primitive implementation as satisfying the
    authorized corrective design;
4. T2.4 as complete and accepted.
```

The owner's four acceptances, restated once for the record and neither broadened nor narrowed:

1. **The corrected T2.4 candidate** `625c03d6…` is accepted.
2. **The independent corrected-candidate rereview** and its verdict
   `M3_2_T2_4_CORRECTED_CANDIDATE_REREVIEW_PASS` are accepted.
3. **Decision 041's recovery-state primitive implementation satisfies the authorized corrective
   design** — the additive public pair `open_recovery_state` and `resolve_recovery_state` in
   `src/disclosure_drift/sec/observation_catalog.py`, the generic `t2_4_recovery_action` state
   vocabulary, the caller-supplied already-registered `ops_ingestion_jobs.job_id` run-identity
   ruling, the corrected thirteen-step write-ahead sequence, and the eight fixed failure outcomes.
4. **T2.4 is complete and accepted.**

**T2.4 acceptance does not itself grant T2.5, T2.6, network, operational-catalog, live-SEC, or
801-ceiling execution authority.** Each of those remains a separate later owner act.

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.

## 5. Publication

The owner authorizes **one normal fast-forward push** of branch `main`, publishing in this order:

1. accepted implementation candidate `625c03d6931e01acc99946ca3924f1cda4da6b76`;
2. the Decision 042 acceptance-and-publication governance commit created from this record, whose
   exact subject is `Accept and publish M3.2 T2.4`.

The corrected candidate is **not** rewritten, amended, squashed, rebased, reset, or cherry-picked;
the governance change is created **on top of** it. The push may occur only after Decision 042 is
durably recorded, the registry and `Milestones/STATUS.md` agree, candidate bytes are unchanged,
the contract and packet hashes are unchanged, the staged path set is exactly the three §7 paths,
and governance validation passes.

**No tag.** No release. No force push, no `--force-with-lease`, no history rewrite, no rebase, no
squash, no amend, and no refspec that bypasses normal branch protection.

## 6. Deferred obligations remaining open

Acceptance of this stage closes none of the following. Each is carried forward unchanged from
Decision 040 §19:

1. **The accepted `RawStore` resource limitation** as a **T4** concern.
2. **Sanitization or exclusion of untrusted progress-sink messages** before any later receipt or
   indexed-artifact use.
3. **F4 evidence-index vocabulary resolution**, no later than T4 and before the first affected
   artifact is publicly indexed.
4. **D023-O1**, which remains a latent fail-closed referral condition, **unmodified**.
5. **Operator wiring and receipt assembly**, during T2.5–T2.6.
6. **Overall independent T3 implementation acceptance**, after the combined T2.5–T2.6 freeze
   candidate.

## 7. Authorized paths and acts for this recording

Exactly, and nothing further:

- `Docs/Decisions/decision_042_m3_2_t2_4_acceptance_and_publication.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 042 row and quick-lookup entry;
- `Milestones/STATUS.md` — current-state, blocker, authority-state, and next-action updates, with
  the machine marker set exactly to
  `NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_M3_2_T2_5_STAGE_AUTHORIZATION_DECISION`;
- **one** governance-only commit with the exact subject `Accept and publish M3.2 T2.4`, and **one**
  normal fast-forward push of `main`. **No tag.**

`Docs/decision_index.md` is deliberately **not** edited — the established navigation ruling stands
and the decision registry remains the discovery route. No implementation, test, script, migration,
receipt, template, packet, contract, review-artifact, configuration, or private-evidence byte
changes.

## 8. Negative authority

This acceptance and publication does **not**:

- constitute overall M3.2 **T3 implementation acceptance**;
- authorize **T2.5** or **T2.6** implementation;
- begin T2.5 merely because T2.4 is accepted and published;
- enable `network.enabled` or `network.m3_acquire_enabled`, or enable CompanyFacts;
- authorize SEC contact, connectivity testing, live SEC requests, or live acquisition;
- authorize creation or use of the real operational catalog;
- authorize operational execution of `m3 acquire`;
- authorize receipt emission, private reconciliation-report creation, or evidence indexing;
- authorize any use of the 801-request ceiling;
- authorize any M3.2B activity;
- grant any T3, T4, or T5 authority not already separately granted;
- authorize Gate H or M3.3 work;
- authorize a migration, a receipt-schema change, another reason code, or an eleventh path;
- authorize a tag, release, force push, history rewrite, rebase, squash, or amend.

## 9. Acceptance criteria for this record's commit

All verified before the commit: (1) the owner's acceptance is recorded without change of substance
and neither broadened nor reinterpreted, and no rereview artifact is invented; (2) `src`, `tests`,
`configs`, migrations, the receipt module, the contract, and the T2 packet are byte-identical to
the accepted candidate, with the contract and packet SHA-256 values unchanged; (3) Decisions
032–041 are byte-unchanged; (4) Decision 042 is unique — no other decision file or registry row
carries the number, and directory and registry agree; (5) the registry and status ledger match this
record exactly, with the next-action marker line occurring exactly once and carrying no suffix;
(6) `git diff --check` and `git diff --cached --check` pass over the updated tree; (7) the commit
carries exactly the three §7 paths; (8) no tag is created; (9) no private path, SEC identity, or
private-evidence content appears in any changed file; (10) `Docs/decision_index.md` is unchanged;
(11) both tracked network switches remain `false`, the migration chain remains `0001`–`0013`, and
the receipt remains `m3-execution-receipt/2.0`.

## 10. Formal outcome

```text
M3_2_T2_4_ACCEPTED_AND_PUBLISHED
```

Publication of the accepted stage is authorized under §5 by one normal fast-forward push, with
**no tag**. Overall Milestone 3.2 implementation acceptance remains the separate later **T3** act.

**Next authorized action:** `CHATGPT_OWNER_M3_2_T2_5_STAGE_AUTHORIZATION_DECISION` — control
returns to the ChatGPT owner for the next stage decision. **T2.5 has not begun and is not
authorized by this record**; network enablement, live SEC access, acquisition, real
operational-catalog creation, receipt emission, and ceiling-801 use all remain unauthorized.

---

**Owner:** Joseph Nihill, acting through the ChatGPT project-owner role.
**Date:** 2026-08-06.
This is a transparent recorded owner decision, not a handwritten, cryptographic, or third-party
digital signature.
