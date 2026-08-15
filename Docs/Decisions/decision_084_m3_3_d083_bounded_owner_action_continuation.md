# Decision 084 — Bounded Owner-Action Continuation of the Decision 083 Correction

```text
STATUS: ACCEPTED — OWNER BOUNDED CONTINUATION OF THE D083 IMPLEMENTATION
DATE: 2026-08-15
OWNER: Sol/GPT
OUTCOME: D083_OWNER_ACTION_CONTINUATION_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION: TWO BOUNDED PATHS ADDED TO THE ACCEPTED DECISION-083 SET
R65_MIGRATION_CHAIN_HEAD: AUTHORIZED — acquisition.py constant only
R66_JOINT_SUPPORT_PAIR_CALLER: AUTHORIZED — offline_execution.py caller only
R67_NARROWER_IDENTITY_IMPLEMENTATION: ACCEPTED — candidate_identity.py unchanged
M3_3_E0_DURABLE_PARSE_AUTHORIZATION: NO
E0_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: 0014 only
MIGRATION_0015_AUTHORIZATION: NO
REVIEW_A_AUTHORIZATION: NO
REVIEW_B_AUTHORIZATION: NO
DOCUMENT_ADJUDICATION_AUTHORIZATION: NO
REQUEST_CEILING: 0
```

**This record resolves one narrow stop and nothing else.** The Decision 083 implementation is
complete and proved; it stopped at final validation because making the suite green required editing
a path Decision 083 §11 prohibited. This record disposes of that stop by authorizing **two exactly
bounded paths** (§2 **R65**, §3 **R66**) and by **accepting** the implementation's conservative
identity narrowing (§4 **R67**).

**It reopens nothing.** Decision 083 is **not modified**. The Decision-083 implementation is not
redone, reverted, or re-derived — the existing uncommitted working tree is the continuation
baseline and is preserved. **M3.3-E0, migration `0015`, and every document-review stage remain
unauthorized**, and network, SEC, and HTTP authority remains **NONE** at `REQUEST_CEILING = 0`.

---

## 1. Continuation baseline — verified

| Fact | Value |
|---|---|
| `HEAD` == `origin/main` | `8da08e48dfa2c3c04f6cb213fefb5f1dcc543df2` (the Decision-083 governance commit) |
| Tree at `HEAD` | `e81e7a365c2f82ebedc9f64cd0b46ac7807e88fb` |
| Parent | `5231359fcce3764257dcc54d29c151b1021e51d6` |
| `m3.2-complete` | `2865a1479e4576dc18a4098c928b278812f38d00`, unmoved |
| Working tree | **DIRTY by design** — it carries the complete uncommitted Decision-083 implementation |
| Staged | nothing |
| Migrations | `0001`–`0014` (`0014` present as an untracked new file) |

The Decision-083 implementation is **preserved**, never reset, restored, checked out, stashed,
cleaned, discarded, or recreated.

## 2. Ruling R65 — the migration chain head

`src/disclosure_drift/m3/acquisition.py` carries
`FINAL_MIGRATION_VERSION`, the constant recording the repository's current schema-chain head.
Migration `0014` moved that head, so the constant became false and
`prepare_operational_catalog` began refusing every catalog it creates.

**Authorized edit — exactly one constant, and nothing else in that file** unless formatting
mechanically requires it:

```text
FINAL_MIGRATION_VERSION: Final = 13   ->   FINAL_MIGRATION_VERSION: Final = 14
```

**Owner interpretation.** This constant records a schema fact. It does **not** reopen M3.2, authorize
acquisition, authorize network access, authorize applying migration `0014` to the accepted private
M3.2 operational catalog, authorize writing any accepted M3.2 evidence, move `m3.2-complete`, or
grant **M3.3-E0** authority. Migration `0014` remains **prospective and pre-E0**, the accepted
private M3.2 operational catalog remains **untouched**, and **no invocation against that private
catalog is authorized**.

**Required proof:** the disposable and test catalog machinery recognizes migration head `0014`.

## 3. Ruling R66 — the joint support-pair caller

Decision 083 reported **MINOR-1**: `support_target_pairs.paired_accessions_from_rows` was made
NULL-safe and association-aware, but its only caller —
`src/disclosure_drift/m3/offline_execution.py` — was outside the Decision-083 path set and could not
supply the association set, so a **jointly filed** 2009/2010 pair leg contributed no pair credit.
That is fail-closed, but it is an under-attribution and therefore a correction-stage defect.

**Authorized path: `src/disclosure_drift/m3/offline_execution.py`, strictly limited to the caller
around the existing `paired_accessions_from_rows` path.**

Required semantics:

| Case | Behaviour |
|---|---|
| **Established multi-registrant** | Evaluate the truthful substantive registrant associations; a valid 2009/2010 support/base pair may contribute to the appropriate substantive entity under the frozen pair rule. **No arbitrary scalar anchor is used** |
| **Established single-registrant** | Byte-for-byte and semantically identical to the accepted behaviour |
| **Unestablished set** | **Fail closed**; zero pair credit |

**No pair may be fabricated** by minimum or maximum CIK, first-write CIK, submitter, row order, date
proximity, name, ticker, or hash order. Accession-domain deduplication remains by canonical
accession.

**Unchanged:** the pair quota, the frozen eligible forms, the 2009/2010 rule, and the research
methodology.

Required focused tests: **(A)** a joint pair receives truthful entity-domain attribution; **(B)** no
duplicate accession-domain credit; **(C)** insertion and order invariance; **(D)** an unestablished
association set grants zero pair credit; **(E)** established single-registrant behaviour does not
change.

## 4. Ruling R67 — the narrower identity implementation is accepted

Decision 082 §10.14 anticipated changes to `src/disclosure_drift/m3/candidate_identity.py`. The
Decision-083 implementation deliberately did **not** widen `ACCESSION_TABLE_COLUMNS`,
`REGISTRANT_TABLE_COLUMNS`, or `SNAPSHOT_CONTENT_FIELDS`, on the grounds that the relational
association set is already bound through the existing candidate registrant table semantics.

**The owner accepts that deviation.** Widening those tuples would create identity deltas for **pure
single-registrant snapshots** even though no semantic change occurred. `candidate_identity.py` is
**not** modified solely to widen them.

The accepted, stronger requirement is:

```text
PURE SINGLE-REGISTRANT SNAPSHOT : E1-E5 remain BYTE-IDENTICAL
MULTI-REGISTRANT SNAPSHOT       : only the prospective identity effects R58-R62 require may move
```

**The fresh independent acceptance review must specifically verify that the relational set is
genuinely governed and bound** — that no association can be removed or altered without changing the
appropriate governed digest. **If that claim is false, the session STOPS** rather than modifying
`candidate_identity.py` without new owner action.

## 5. What this record does not authorize

It does **not**: modify Decision 083; redo, revert, or re-derive the Decision-083 implementation;
broaden either authorized path beyond the exact scope in §2 and §3; write migration `0015`;
implement the verified-evidence schema; execute Review A, Review B, or the adjudication; classify any
real filing; resolve any real amendment parentage; grant any quota credit; close either real-path
feasibility gate; authorize **M3.3-E0**, **M3.3-E1**, **M3.3-E2**, or **M3.4**; make any network,
SEC, or HTTP request; apply migration `0014` to the accepted private M3.2 operational catalog; write
to the accepted M3.2 private evidence; move `m3.2-complete`; or create any tag.

**Successful implementation is still not acceptance.** **R49** condition B is satisfied only after a
**fresh independent Claude Fable 5 maximum review** and Sol/GPT owner acceptance.

## 6. Next authorized action

Apply **R65** and **R66**, run targeted validation, run exactly one `make check-fast`, commit the
complete Decision-083 implementation as **one** implementation commit whose parent is this
governance commit, push once, and **return to Sol/GPT**. The implementing session does not
self-review for formal acceptance.

```text
D083_OWNER_ACTION_CONTINUATION_AUTHORIZED
R65_MIGRATION_CHAIN_HEAD             = AUTHORIZED (acquisition.py constant only)
R66_JOINT_SUPPORT_PAIR_CALLER        = AUTHORIZED (offline_execution.py caller only)
R67_NARROWER_IDENTITY_IMPLEMENTATION = ACCEPTED (candidate_identity.py unchanged)
MIGRATION_AUTHORIZED                 = 0014 only
M3_3_E0_AUTHORIZATION                = NO
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY    = PENDING FUTURE AUTHORIZED E0 VERIFICATION
```
