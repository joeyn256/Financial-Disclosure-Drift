# Decision 038 — M3.2 T2.2–T2.3 Implementation-Path Envelope Amendment

**Date:** 2026-08-05
**Status:** ACCEPTED — OWNER APPROVED 2026-08-05
**Type:** Narrow bounded governance record amending the authorized implementation-path envelope for
the combined M3.2 stage T2.2–T2.3 **only**.
**Not** a preregistration deviation. It changes no hypothesis, cohort window, maturity gate, outcome
definition, threshold, seed, selection methodology, S4/S5/S6 identity, hash preimage, migration
byte, implementation byte, test byte, script byte, or configuration byte — **no executable byte
changes with this record**.
**Amends:** [Decision 035](decision_035_m3_2_t2_staged_implementation_authorization.md) §6 (the
fifteen-path maximum T2 envelope), the corresponding fifteen-path maximum recorded in
[`Docs/m3/m3_2_t2_implementation_authorization_packet.md`](../m3/m3_2_t2_implementation_authorization_packet.md)
§5, and the unchanged-envelope statements carried in
[Decision 036](decision_036_m3_2_t2_1_stage_completion.md) and
[Decision 037](decision_037_m3_2_remaining_stage_combination.md) — **for the combined T2.2–T2.3
stage only, and only to the extent §4 states**.
**Amends in place:** nothing. No accepted decision file is edited; the T2 authorization packet is
**preserved byte-identical**; the accepted M3.2 contract is **not edited**; both M3.2 review
artifacts are preserved unchanged (Decision 030 §10).
**Related:** Decisions 024 §8, 034, 035, 036, 037; the T2 packet
[revision v2](../m3/m3_2_t2_implementation_authorization_packet.md); the accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the exact set of implementation paths authorized for the combined M3.2 T2.2–T2.3
stage, and nothing else.

---

## 1. Why this record is required

The combined T2.2–T2.3 implementation candidate
`6b189df1651ec3674ec7f96a1f5d66f488c654a9` changed six paths. Four of them lie inside the
Decision 035 §6 fifteen-path maximum envelope. Two do not:

1. `src/disclosure_drift/sec/observation_catalog.py`
2. `tests/unit/test_observation_catalog.py`

The T2 packet §5 places `sec/observation_catalog.py` under **"Dispositioned and DECLINED (remain
prohibited) … accepted, injectable, consumed unchanged"**, adding that "A discovered need to edit
any of these is stop-and-return S1 (§7.8), never self-widening."
`tests/unit/test_observation_catalog.py` is not among T1–T7. Decision 035 §6 fixes that envelope as
"a ceiling and not a grant, with any out-of-subset need an immediate stop for new owner
adjudication **before the path is touched**", and Decisions 036 and 037 each re-affirm it unchanged.

The owner granted the required adjudication on 2026-08-05, **before those paths were edited**, after
the accepted architecture proved unsafe within the original envelope (§5). What did not yet exist
was the **durable record** of that grant. Under CLAUDE.md's authority rules, chat transcripts are not
repository authority and `Milestones/STATUS.md` records workflow state but never overrides a
decision; only a numbered accepted record in `Docs/Decisions/` binds a future session. Without this
record, a later reader applying the committed authority would find the accepted record prohibiting
exactly the edit that `main` contains, with nothing explaining it.

This record is that durable home. It ratifies the prior explicit owner adjudication and states its
exact, narrow limits.

## 2. The final independent rereview and its disposition

The second-corrected candidate received a fresh, independent, adversarial rereview by a session that
authored none of the candidates, corrections, tests, reviews, the M3.2 contract, Decisions 034–037,
or the T2 packet, conducted with no subagent, delegated agent, background agent, parallel session,
worktree, or other conversation.

**Verdict:** `M3_2_T2_2_T2_3_SECOND_CORRECTED_INDEPENDENT_REREVIEW: PASS_WITH_REQUIRED_CORRECTIONS`

**Technical disposition — the owner determines that every technical PASS condition is satisfied.**
The rereview confirmed, on independently written probes rather than on the candidate's own tests:

- all three prior MAJOR findings fully corrected — eager materialization replaced by a streamed
  single pass; unsanitized operational detail replaced by class-derived public descriptions;
  clock-stamped ZIP fixtures replaced by fully pinned member metadata;
- **zero BLOCKER**;
- the candidate-owned archive-lineage phase is **memory-bounded by measurement** — a 71,310,806-byte
  archive expanding to 71,303,168 bytes across 68 members (largest 1,048,576 bytes) drove a
  lineage-phase heap peak of 3,211,570 bytes: 3.06× the largest single member and **4.5 % of total
  expanded content**, with at most **2** members simultaneously live and all-payloads-live **false**;
- observation-member persistence is transactional and deterministic — 12 of 12 rollback and
  reuse-boundary probes left no partial observation, no member subset, and no residue, with the
  identity lawfully retryable afterwards;
- ZIP fixtures and tests are clock-independent — byte-identical across five timezones and five
  processes, and 15 consecutive runs of the previously flaky classes passed;
- bounded operational outputs expose no private path or payload — five injected operational failure
  classes carrying absolute-path, home-path, database-filename, response-body, member-payload, and
  credential canaries produced zero leaks into outcome details, window details, reason codes,
  progress failures, logs, returned exception text, or the catalog file;
- no plan, route, ceiling, completion, receipt, or no-network bypass;
- all validation green — ruff clean, format clean, mypy strict clean over 76 source files, targeted
  272 passed, and the full suite **2938 passed, 1 skipped, twice consecutively**;
- all twelve required mutation checks are **load-bearing**;
- the candidate was not modified.

**The sole PASS-blocking issue was the absence of a durable path-envelope amendment.** It was
classified MAJOR as a governance-record defect explicitly requiring **no code change**. This record
resolves it.

## 3. Owner instrument (verbatim)

```
OWNER_DECISION_038_M3_2_T2_2_T2_3_PATH_ENVELOPE_AMENDMENT: APPROVED

The project owner adopts the final independent rereview's technical findings for
the combined M3.2 T2.2–T2.3 implementation candidate:

6b189df1651ec3674ec7f96a1f5d66f488c654a9

Candidate tree:

8850e1e45e9471bbb8b94612da67715e932a496f

Published parent:

feb9e134307a9551475f243dc0c1ddcecc89ffde

Final independent rereview disposition:

M3_2_T2_2_T2_3_SECOND_CORRECTED_INDEPENDENT_REREVIEW:
PASS_WITH_REQUIRED_CORRECTIONS

The owner determines that every technical PASS condition has been satisfied.
The only remaining correction is the durable recording of a previously granted
owner path-envelope amendment.

Decision 038 therefore amends, for the combined T2.2–T2.3 stage only:

* Decision 035 §6;
* the fifteen-path maximum envelope recorded in
  `Docs/m3/m3_2_t2_implementation_authorization_packet.md`;
* the unchanged-envelope statements in Decisions 036 and 037.

The following two paths are added to the authorized T2.2–T2.3 implementation
envelope:

1. `src/disclosure_drift/sec/observation_catalog.py`
2. `tests/unit/test_observation_catalog.py`

The amendment is limited to the exact changes contained in candidate
`6b189df1651ec3674ec7f96a1f5d66f488c654a9`:

* widening `ObservationRecorder.record(..., members=...)` from an eager sequence
  boundary to a compatible single-pass iterable boundary;
* lazily and transactionally consuming archive-member lineage;
* preserving compatibility for existing sequence callers;
* preserving deterministic order, lineage validation, rollback, reuse, and
  supersession behavior;
* adding the direct tests necessary to prove those properties.

The owner ratifies the earlier correction authorization dated 2026-08-05 that
permitted these two paths after the accepted architecture proved unsafe within
the original path envelope.

This ratification is not a retrospective self-widening by an implementation
agent. It is the durable record of an explicit owner adjudication made before
the paths were edited.

This amendment does not:

* authorize any further edit to either added path;
* add either path to T2.4 or T2.5–T2.6 authority;
* broaden any other stage envelope;
* amend schema or migrations;
* amend reason-code authority;
* amend receipt vocabulary or schema;
* amend route or source authority;
* amend network configuration;
* authorize operator CLI wiring;
* authorize T2.4;
* accept or publish the implementation candidate;
* enable network or CompanyFacts;
* authorize SEC contact, acquisition, receipts, evidence, or operational use of
  the ceiling.

The historical T2 authorization packet remains byte-identical and retains its
recorded SHA-256:

621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599

Decision 038 is higher authority and provides the narrow amendment. The packet
must not be silently rewritten.

The implementation candidate remains unaccepted and unpushed until the owner
reviews the durable Decision 038 commit and separately grants acceptance and
normal push authorization.

Required next state:

`NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_ACCEPTANCE_AND_PUSH_DECISION_FOR_M3_2_T2_2_T2_3_AFTER_DECISION_038_RECORDING`

Owner:
Joseph Nihill, acting through the ChatGPT project-owner role

Date:
2026-08-05

This is a transparent recorded owner decision, not a handwritten,
cryptographic, or third-party digital signature.
```

## 4. The amendment

For the combined M3.2 stage **T2.2–T2.3 only**, the authorized implementation-path envelope is the
Decision 035 §6 fifteen-path maximum (T2 packet §5, production P1–P8 and tests T1–T7) **plus exactly
these two paths**:

| # | Path | Disposition | Exact limited purpose |
|---|---|---|---|
| A1 | `src/disclosure_drift/sec/observation_catalog.py` | bounded edit — **added to the envelope by this record** | Widen `ObservationRecorder.record(..., members=...)` from an eager `Sequence[ArchiveMember]` boundary to a compatible single-pass `Iterable[ArchiveMember]` boundary, and consume archive-member lineage **lazily and inside the observation's own transaction**, so each member's row is written and the member released before the next is read. Compatibility for existing sequence callers is preserved. Deterministic order, lineage validation, rollback, reuse, and supersession behaviour are preserved. |
| A2 | `tests/unit/test_observation_catalog.py` | bounded edit — **added to the envelope by this record** | Add the direct tests necessary to prove the A1 properties: single-pass consumption with no `len`, indexing, sorting, conversion, or second iteration; row-by-row persistence observable from inside the transaction; deterministic order; complete rollback on late member failure and on member-insert failure; payload bytes never persisted; and preserved-owner lineage on reuse. |

**No other path is added, at this stage or any other.** The four in-envelope paths the candidate also
changed — `src/disclosure_drift/m3/__init__.py` (P8), `src/disclosure_drift/m3/acquisition.py` (P3),
`tests/integration/test_m3_cli.py` (T4), and `tests/unit/test_m3_acquisition.py` (T1) — are
unaffected by this record and remain authorized exactly as before.

### 4.1 Binding to the exact candidate

The amendment is bound to, and limited by, the exact changes contained in:

- **candidate commit:** `6b189df1651ec3674ec7f96a1f5d66f488c654a9`
- **candidate tree:** `8850e1e45e9471bbb8b94612da67715e932a496f`
- **published parent:** `feb9e134307a9551475f243dc0c1ddcecc89ffde`
- **stage subject:** `Implement M3.2 T2.2-T2.3 acquisition foundation`

A change to either added path beyond what that tree already contains is **outside this amendment**
and requires a new owner adjudication before the path is touched.

## 5. The envelope conflict this record resolves

The accepted architecture required the acquisition driver to record archive-member lineage for the
bulk submissions object. The bulk archive expands to far more content than the archive itself, and
the accepted recorder's `members` parameter was an **eager sequence** boundary. A driver confined to
the original fifteen-path envelope could therefore satisfy that signature only by materializing
every member payload in memory at once — reintroducing precisely the unbounded-memory behaviour the
stage exists to avoid, and which the first candidate exhibited.

The safe implementation is not reachable inside the original envelope: the boundary that must widen
belongs to `sec/observation_catalog.py`, a path the packet declined. That is the "accepted
architecture cannot be implemented as written" condition Decision 037 names as an **immediate stop**.
The stop was taken and the owner adjudicated it. This record is the durable form of that
adjudication.

## 6. Ratification, and why this is not self-widening

The owner **ratifies the earlier correction authorization dated 2026-08-05** that permitted these two
paths after the accepted architecture proved unsafe within the original path envelope.

**This ratification is not a retrospective self-widening by an implementation agent.** It is the
durable record of an explicit owner adjudication made **before the paths were edited**. The sequence
was: the constraint was discovered; work stopped; the owner adjudicated and authorized the two
paths; the implementation then proceeded within the widened envelope. No implementation session
enlarged its own authority, and the packet's stop-and-return S1 discipline was honoured rather than
bypassed. The defect this record cures is that the adjudication lived only outside the repository —
a **recording** gap, not an authority gap.

## 7. Authority hierarchy and supersession

- **Decision 038 is higher authority** than Decision 035 §6, the T2 packet §5 fifteen-path maximum,
  and the unchanged-envelope statements in Decisions 036 and 037 — **for the combined T2.2–T2.3
  stage, and only for the two paths and purposes §4 names.**
- The supersession is **partial and narrow**. Every other provision of Decisions 035, 036, and 037
  remains in force verbatim, including: the envelope's character as a **ceiling and not a grant**;
  the requirement that any further out-of-subset need is an **immediate stop for new owner
  adjudication before the path is touched**; the stage cadence; the commit boundaries; the
  prohibition on stage and T3 tags; and every declined and prohibited surface not named in §4.
- **No accepted decision is edited in place.** Decisions 032–037 are byte-unchanged. This record
  amends by higher authority, not by rewriting.
- The accepted M3.2 contract is **not edited**; it retains SHA-256
  `c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7`.

## 8. Historical packet disposition

The T2 implementation-authorization packet remains **byte-identical** and retains its recorded
SHA-256:

```
621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599
```

**The packet must not be silently rewritten.** Its §5 fifteen-path table stands as the historical
record of what was authorized on 2026-08-04; this record is where a reader learns that the T2.2–T2.3
stage envelope was subsequently and narrowly extended by two paths. Every other packet requirement
remains controlling.

## 9. Negative authority

This record does **not**:

- authorize any further edit to `src/disclosure_drift/sec/observation_catalog.py` or
  `tests/unit/test_observation_catalog.py` beyond the exact candidate tree `8850e1e4…`;
- add either path to T2.4 or T2.5–T2.6 authority;
- broaden any other stage envelope;
- amend schema or migrations (no `0014`; migrations `0001`–`0013` unchanged);
- amend reason-code authority (`reasons.py` unchanged; no code invented);
- amend receipt vocabulary or schema (`m3/receipt.py` unchanged and frozen);
- amend route or source authority (`sec/source_registry.py` unchanged);
- amend network configuration (`network.enabled: false` and
  `network.m3_acquire_enabled: false` both unchanged);
- authorize operator CLI wiring;
- authorize T2.4;
- **accept or publish the implementation candidate**;
- enable network or CompanyFacts;
- authorize SEC contact, connectivity testing, acquisition, receipts, evidence, or operational use
  of the M3.2A ceiling 801;
- authorize any tag, push, branch, or history rewrite;
- resolve the open F4 evidence-index vocabulary decision, which remains due no later than T4;
- reopen any completed M3.1 limitation or alter D023-O1, which remains a latent fail-closed
  referral condition.

## 10. Candidate state

The implementation candidate remains **unaccepted and unpushed**. It exists locally only, at
`6b189df1651ec3674ec7f96a1f5d66f488c654a9`, one commit ahead of `origin/main`
(`feb9e134307a9551475f243dc0c1ddcecc89ffde`), with no tag. Recording this amendment accepts nothing,
publishes nothing, and completes no stage. Candidate acceptance and push authorization remain
**separate owner acts** taken after the owner reviews this durable record.

No transport, operational catalog, receipt, evidence artifact, raw object, token, request, attempt,
hostname lookup, socket operation, or SEC contact exists or has occurred. Ceiling 801 remains unused.

## 11. Formal outcome

**`M3_2_T2_2_T2_3_PATH_ENVELOPE_AMENDMENT_RECORDED`**

`NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_ACCEPTANCE_AND_PUSH_DECISION_FOR_M3_2_T2_2_T2_3_AFTER_DECISION_038_RECORDING`

---

**Owner:** Joseph Nihill, acting through the ChatGPT project-owner role.
**Date:** 2026-08-05.
This is a transparent recorded owner decision, not a handwritten, cryptographic, or third-party
digital signature.
