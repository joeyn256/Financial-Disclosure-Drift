# Decision 098 — D094 Implementation Independent-Review Rejection and PRE-E0 Hold

```text
STATUS: ACCEPTED — OWNER REVIEW ADJUDICATION AND HOLD
DATE: 2026-08-16
OWNER: Sol/GPT
OUTCOME: M3_3_D094_PRE_E0_IMPLEMENTATION_REJECTED_PENDING_CORRECTION_AUTHORITY
REVIEW_RESULT: M3_3_D094_PRE_E0_IMPLEMENTATION_INDEPENDENT_REVIEW_FAIL
REVIEW_FINDINGS: BLOCKER 0 / MAJOR 2 / MINOR 4 / OPTIMIZATION 1 / OBSERVATION 4
PRE_E0_IMPLEMENTATION_ACCEPTANCE: NO
M3_3_E0_OPERATIONAL_STATE: HELD
FURTHER_CORRECTION_AUTHORIZATION: NO — REQUIRES A NEW JOEY RULING
ACCEPTED_CATALOG_MIGRATION_EXECUTION_AUTHORIZATION: NO
M3_3_E0_EXECUTION_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

This is the owner ruling required by Decision 094 §12.4 after the one fresh independent review.
It rejects the current implementation candidate, not the Decision-094 architecture. It records the
review evidence durably, adopts two reproducible MAJOR findings, preserves the otherwise-strong
candidate unchanged, and stops at the explicit post-Decision-097 authority boundary.

No statement in this record activates either execute constant, accepts the candidate, authorizes a
new correction executor, permits private-root access, or turns a passing test suite into transition
or E0 authority.

## 1. Frozen candidate and completed implementation evidence

The Decision-097 executor produced this clean, local, unpushed candidate:

| Fact | Value |
|---|---|
| Branch | `main` |
| Candidate HEAD | `1e200218be82702e55396a5afab579203a1545a9` |
| Candidate tree | `7d5f3aa9ba9b84c8fe041d0e9f8c8cd12f0133cd` |
| Parent | `0920bc29e2a1c28a692105416a8f5d605507b9b0` |
| Subject | `feat: implement Decision 094 pre-E0 execution surfaces` |
| Recorded `origin/main` | `4ed0fc7f67c3f9b4f5750e7c24432269aed9ffc4` |
| Relation at review | ahead 5 / behind 0 |
| Candidate paths | exactly 23, the Decision-097 R89 set |
| Worktree and index at review | clean |
| Tags at HEAD | none |

The implementation epoch attested actual `claude-opus-5`; Maximum was requested under the accepted
Decision-096 R85 observability ruling. Every Decision-097 §2 preserved-WIP hash matched, the sole
new edit was `tests/unit/test_audit_tooling.py`, and the M19 correction proved exactly 38 historical
definitions, 37 current live anchors, `[M19]` solely superseded, and zero unexpected missing anchors.

The one permitted post-correction `make check-fast` passed once:

```text
4351 passed / 1 skipped / 0 failed in 79.40 seconds
```

The preserved log `/tmp/d097_checkfast.log` had SHA-256
`9e0a3a6ae299f008d3e47001e28f7cc4e7f1f0dcdebd02e5bf5a982a7aa31865` at review. The reviewer did
not rerun the unchanged full gate. A passing gate is evidence, not owner acceptance.

## 2. Ruling R90 — independent review evidence is accepted as authentic

The Decision-094 §12.4 review used one genuinely fresh, read-only Claude Opus 5 session:

| Fact | Value |
|---|---|
| Actual model attestation | first output line exactly `ACTUAL_MODEL: claude-opus-5` |
| Effort | Maximum requested; CLI visibility limitation disclosed under Decision 096 R85 |
| ACPX record | `13242828-7cab-4a70-8764-429ffd3c13d4` |
| Actual ACP session | `30ea6bfd-9acd-4adc-a1bb-aea58a806f80` |
| Review target | candidate HEAD/tree in §1 |
| Delegation | none; one model, no subagent, workflow, second reviewer, branch, or worktree |
| Repository writes | none during substantive review |

The exact reconstructed reviewer report is the immutable candidate-review artifact
[`Docs/m3/reviews/m3_3_d094_pre_e0_implementation_independent_review_1e20021.md`](../m3/reviews/m3_3_d094_pre_e0_implementation_independent_review_1e20021.md), SHA-256
`07feb1608f85ae30b61ff3ec4cdc1fb67ad6b17da03fa6cebd97295174cf1beb`. It was reconstructed by
concatenating the final ACP `agent_message_chunk` values for message
`msg_011Ce6fZxfsKt3PGHeZR5mDD`; its SHA-256 equals the same concatenated stream bytes. The reviewer
did not create the artifact and did not claim owner authority.

Independent evidence included:

- 727 targeted tests passed, 0 failed, in 147.36 seconds;
- a disposable mutation battery whose true guard mutants were killed, including the Decision-096
  R83 `invalid_cik_rendering_count` successor proof and the R79 unbindable-member negative controls;
- exact verification of the sixteen-table write set, canonical relation consumer, no scalar or
  observation fallback, receipt-v4 isolation, non-self-referential identities, and disabled execute
  constants; and
- two bounded failure-window experiments that reproduced MAJOR-1 independently of the full suite.

The authoritative repository remained byte-identical throughout the review. No accepted private
root or catalog was located or opened, and no network, SEC, HTTP, DNS, migration, transition, E0,
linkage, activation, push, or tag action occurred.

## 3. Ruling R91 — MAJOR-1 is owner-confirmed

**Finding:** a failure between assigning an event-conditioned terminal field and durably appending
its conditioning event can leave a create-once terminal that its own closed validator refuses.

The governing schemas are exact:

- Decision 094 §8.1 permits `post_preexisting_content_sha256` on a failed/interrupted transition
  only if `POSTCHECK_PASSED` is durable; and
- Decision 094 §9.2 permits `post_integrity`, `table_hashes`,
  `plan_parser_state_hash`, and `e0_catalog_state_sha256` on a failed/interrupted E0 terminal only
  if `VALIDATION_PASSED` is durable.

The candidate assigns these values before the corresponding `ledger.append()`. On failure,
`_disclose_failure()` does not derive the permitted field set from the durable event ledger. It then
suppresses the validation error raised by `_freeze()`, after the malformed terminal has been written
create-once.

The independent transition experiment forced `POSTCHECK_PASSED` append failure and measured:

```text
POSTCHECK_PASSED durable: False
post_preexisting_content_sha256 present: True
terminal validator: REFUSED
transition_verify: determined=True passed=False
```

The independent E0 experiment used the genuine input-observation digest reproduction gate and
measured:

```text
VALIDATION_PASSED durable: False
post_integrity present: True
terminal validator: REFUSED
e0_verify: determined=True passed=False
```

This fails closed and does not create a false success, so it is not a BLOCKER. It is MAJOR because
Decision 094 conflict C4 and §12.3 item 8 require every failed/interrupted state and crash boundary
to be durably representable. The current candidate does not satisfy that acceptance condition.

## 4. Ruling R92 — MAJOR-2 is owner-confirmed; predicate 3 remains mandatory

Decision 094 §5.2 is headed **“Preflight — all predicates required.”** Predicate 3 requires:

> the accepted M3.2 acquisition completion receipt and catalog binding validate

Decision 094 §5.3 item 2 repeats predicates 1–8 and 10–13 under the continuous writer lease before
creating a namespace or backup. Predicate 3 is therefore required both by transition preflight and
by the under-lease recheck.

The candidate implements twelve of the thirteen §5.2 predicates. It contains no validation of the
accepted M3.2 completion receipt or its binding to the catalog, while
`transition_preflight()` claims to evaluate every §5.2 predicate. No later accepted Decision
supersedes predicate 3. The omission is not a permissible implementation interpretation and is not
discharged by validating the catalog chain alone.

The accepted M3.2 evidence already provides a concrete completion chain: the T7 head receipt at the
Decision-063 accepted per-run path, its predecessor T6 receipt, validated receipt identities, and
the accepted receipt-chain/catalog/run-state cross-check semantics finalized by Decisions 063–065.
Exactly how the bounded PRE-E0 surface invokes or narrowly reuses those accepted mechanics must be
stated in any future correction instrument; an executor may not silently invent a weaker binding or
import the acquisition orchestrator in conflict with Decision 094 §7.3.

This is MAJOR because a transition preflight can otherwise report PASS for a catalog whose accepted
M3.2 completion provenance is missing, invalid, or bound elsewhere. It is not a BLOCKER only because
the transition execute constant remains `None` and no accepted catalog write is reachable.

## 5. Ruling R93 — remaining findings are recorded, not correction authority

The owner adopts the review's remaining classifications:

| ID | Classification | Disposition |
|---|---|---|
| MINOR-1 | `transition_preflight()` overclaims complete §5.2 coverage | Confirmed; substantively coupled to MAJOR-2 |
| MINOR-2 | `verify` does not validate catalog state despite Decision 094 §7.2 | Confirmed; fail-closed downstream remeasurement limits exposure, but the accepted row remains unsatisfied |
| MINOR-3 | under-lease lease-refusal removal depends on an English substring | Confirmed; fail-closed but brittle |
| MINOR-4 | namespace parent existence and operator ownership are not fully checked | Confirmed; Decision 094 §5.2 predicate 10 is only partially implemented |
| OPTIMIZATION-1 | duplicate equivalent unbindable-establishment conditions | Recorded and deferred; harmless defensive redundancy |
| OBSERVATION-1 | package-level imports transitively reach acquisition/network modules | Recorded; `e0.py` and `offline_parse.py` add no new edge and construct no client |
| OBSERVATION-2 | the review packet named a repository `AGENTS.md` that is absent | Recorded as a packet-description error; repository `CLAUDE.md` was applied |
| OBSERVATION-3 | `Docs/change_impact_map.md` does not name Decision 097/audit path | Recorded; D097's one-file limit made that omission expected during implementation |
| OBSERVATION-4 | the disclosed legacy nullable-scalar conversion remains | Recorded exactly as Decision 094 §6.5's unreachable residual |

These findings neither authorize opportunistic cleanup nor weaken the two MAJOR findings. A future
owner instrument may combine small corrections only when they remain bounded, materially useful,
and do not reopen accepted production semantics.

## 6. Ruling R94 — candidate rejected; operational hold continues

The candidate at `1e200218be82702e55396a5afab579203a1545a9` is **not owner-accepted**. It remains a
valuable, clean, unpushed correction baseline and is preserved rather than reset, amended, rebased,
or concealed. Its passing full gate and independently verified correct surfaces remain evidence;
they do not cure the two MAJOR gaps.

No Decision-094/095/096/097 production semantic is broadened. In particular:

- the canonical relation and complete association-set consumer remain controlling;
- no observation or scalar fallback is restored;
- missing/unbindable entities fail closed and no entity is invented;
- the R28 bridge remains attributed to canonical-relation/evidence-digest behavior;
- historical M19 evidence remains truthful and only its current live applicability is superseded;
- both execute constants remain exactly `None`; and
- E0 remains operationally HELD.

The one Decision-097 implementation commit authority has been consumed. Decision 096 prohibited
another automatic remediation, and Decision 097 granted only its exact one-file exception. This
record therefore grants **no** new source, test, documentation, validation, commit, or reviewer
authority.

## 7. Owner ruling required for any correction

The exact next consequential action requires Joey's new ruling. The recommended ruling is one
exceptional bounded correction instrument that:

1. preserves candidate `1e200218…` as the correction baseline;
2. corrects MAJOR-1 in `src/disclosure_drift/m3/e0.py` with load-bearing transition and E0
   failure-window tests in `tests/unit/test_m3_e0.py`;
3. freezes and implements the exact accepted M3.2 completion-receipt/catalog binding required by
   Decision 094 §5.2 predicate 3 in both preflight and the under-lease recheck, using existing
   accepted receipt/recovery semantics rather than a new provenance method;
4. explicitly dispositions MINOR-1 through MINOR-4, correcting them only where the bounded change
   is mechanically compatible with the same authority;
5. uses one fresh actual-model-attested Claude Opus 5 Maximum executor, targeted tests and mutation
   proofs, touched-file checks, and one final `make check-fast` on the corrected tree;
6. permits one new local correction commit only after every required proof passes, with no push,
   tag, amend, rebase, force operation, migration, activation, private-root access, or network; and
7. states the corrected-target review boundary explicitly. Decision 094's independent review has
   failed; accepting changed code requires bounded review evidence against the corrected target,
   but no reviewer-of-reviewer chain or extra-opinion loop.

Until that ruling is explicit, the only authorized work is read-only analysis and this governance
record. No correction executor is launched.

## 8. Governance recording

Sol/GPT may commit this Decision, the exact independent-review artifact, and current-state
navigation overlays in one local governance commit with subject:

```text
docs: record Decision 098 PRE-E0 review hold
```

The commit changes no source, test, configuration, migration, accepted evidence, or historical
Decision byte. It does not accept or rewrite candidate `1e200218…`, and it grants no push or tag.

## 9. Acts still prohibited

No accepted private-root discovery or access; no accepted-catalog open; no migration `0014`, `0015`,
or `0016`; no transition; no E0; no linkage diagnostic; no persistence bridge; no E1, E2, or M3.4;
no activation-constant change; no network, SEC, HTTP, DNS, socket, acquisition, package installation,
fetch, pull, or push; no tag, release, publication, or history rewrite.

```text
RESULT_TOKEN: M3_3_D094_PRE_E0_IMPLEMENTATION_REJECTED_PENDING_CORRECTION_AUTHORITY
NEXT_ACTION: JOEY RULING ON ONE BOUNDED CORRECTION AND CORRECTED-TARGET REVIEW BOUNDARY
M3_3_E0_OPERATIONAL_STATE: HELD
```
