# Decision 085 — D083/D084 R46 Formal-Review Findings: Owner Acceptance and Correction Authorization

```text
STATUS: ACCEPTED — OWNER ACCEPTANCE OF THE FORMAL REVIEW FINDINGS AND CORRECTION AUTHORIZATION
DATE: 2026-08-15
OWNER: Sol/GPT
OUTCOME: M3_3_D083_D084_R46_FORMAL_REVIEW_FINDINGS_OWNER_ACCEPTED_FOR_CORRECTION
FORMAL_REVIEW_VERDICT: FAIL — BLOCKER 0 / MAJOR 1 / MINOR 4
M_1_MR_M10_BUILDER_PROTECTION: ACCEPTED — CORRECTION REQUIRED — ACCEPTANCE-GATING
MIN_1_MIGRATION_COMMENT_ACCURACY: ACCEPTED — CORRECT NOW
MIN_2_ESTABLISHED_ZERO_RELATION_INSERT_GUARD: ACCEPTED — CORRECT NOW
MIN_3_REBASELINE_DIGEST_PROVENANCE: ACCEPTED — CORRECT NOW
MIN_4_RESERVE_PER_CIK_JOINT_CAP: ACCEPTED — CORRECT NOW
ARCHITECTURE_REOPENED: NO
R58_R67_REDESIGN: NO
CANDIDATE_IDENTITY_PY: PROHIBITED — UNCHANGED
M3_3_E0_DURABLE_PARSE_AUTHORIZATION: NO
E0_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
MIGRATION_AUTHORIZED: 0014 correction only
MIGRATION_0015_AUTHORIZATION: NO
REVIEW_A_AUTHORIZATION: NO
REVIEW_B_AUTHORIZATION: NO
DOCUMENT_ADJUDICATION_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

**This record accepts a failed review as a truthful review result and authorizes exactly its
findings' correction.** The fresh formal independent acceptance review of the Decision-083 /
Decision-084 **R46** implementation returned **FAIL** at **BLOCKER 0 / MAJOR 1 / MINOR 4**. It
independently confirmed the implementation's **production behaviour** faithful to **R58**–**R62**
and **R65**–**R67**; the acceptance failure is primarily a **verification defect**, not a behaviour
defect. Sol/GPT accepts the verdict and all five findings, and authorizes their correction and
nothing else.

**It reopens nothing.** Decisions 083 and 084 are **not modified**, the **R58**–**R67**
architecture is **not** redesigned, migration `0015` is **not** started, no document-review stage
begins, and **M3.3-E0** remains unauthorized at `REQUEST_CEILING = 0`.

---

## 1. Correction baseline — verified

| Fact | Value |
|---|---|
| Branch | `main` |
| `HEAD` == `origin/main` | `2d4e2ea16111a38ce233dca94fee05f7aa09e3be` (the review publication commit) |
| Parent — the frozen implementation target reviewed | `09ee44223cfebf247f7ae32a59c3f95c4d06bb79` |
| Reviewed implementation tree | `e13c55ae13d8c5ae12ddd7891e92fd946ec799fd` |
| Genuine pre-correction parent (**MIN-3** reproduction source) | `6fdec2ed685c3c6248e392b04cdf184e8f3549e3` |
| `m3.2-complete` | `2865a1479e4576dc18a4098c928b278812f38d00`, unmoved |
| Working tree | CLEAN |
| Migrations | `0001`–`0014`; `0015` absent |

The frozen review artifact is
[`Docs/m3/reviews/m3_3_d083_d084_r46_formal_independent_acceptance_09ee442.md`](../m3/reviews/m3_3_d083_d084_r46_formal_independent_acceptance_09ee442.md).
It is **immutable** and is not edited, re-derived, or re-run by the correction.

## 2. The review verdict is accepted as a truthful review result

```text
M3_3_D083_D084_R46_INDEPENDENT_REVIEW_FAILED_READY_FOR_OWNER_CORRECTION
```

The reviewed target `09ee4422…` **stands as committed**. It is not reverted, amended, rebased,
squashed, or re-derived. The correction is a **forward** change parented on the review publication
commit.

## 3. Owner dispositions

| Finding | Severity | Owner disposition |
|---|---|---|
| **M-1** — MR-M10 does not kill its exact intended derivation-layer mutation | MAJOR | **ACCEPTED / CORRECTION REQUIRED / ACCEPTANCE-GATING** |
| **MIN-1** — migration `0014` comments misstate the R67 binding mechanism | MINOR | **ACCEPTED / CORRECT NOW** |
| **MIN-2** — `established` + zero substantive relation reachable by INSERT | MINOR | **ACCEPTED / CORRECT NOW** |
| **MIN-3** — an unverifiable second "before" digest in a re-baseline table | MINOR | **ACCEPTED / CORRECT NOW** |
| **MIN-4** — reserve per-CIK cap attributes a joint bundle accession to the replacement alone | MINOR | **ACCEPTED / CORRECT NOW** |

**No other implementation defect is authorized for correction** unless it is discovered while
fixing one of these five and is inseparable from it. A newly discovered unrelated defect is
**classified and reported**, and a material one is a **STOP** for owner action.

Observations **OBS-1** through **OBS-6** are recorded by the review and are **not** authorized for
correction by this record.

## 4. Ruling — M-1: the exact MR-M10 derivation-layer mutation must be killed

**MR-M10**'s accepted definition (Decision 082 §10.13) is: *mutation* — derive the association set
from a source with rows omitted; *killing assertion* — `registrant_set_completeness` must be
`unestablished`, and **a silent single-registrant result fails**.

The review demonstrated that the shipped MR-M10 test exercises only the **freeze/schema
persistence backstop**, and that the exact derivation-layer mutant — inside
`derive_candidate_snapshot` and its direct derivation path, **absent** establishment / registrant
evidence silently interpreted as evidence of **one substantive registrant** — produces
lawful-looking established sole-registrant state that **no schema or freeze guard can see**, and
**survived** every builder-invoking test.

**Required correction.** A dedicated **builder-level** test whose fixture includes an otherwise
candidate-eligible accession with **no** established substantive registrant relation or evidence
and **no** lawful complete registrant-set proof, verifying that the candidate builder:

- **excludes** it before candidate snapshot entry;
- records the accepted `PILOT_ACCESSION_REGISTRANT_SET_UNESTABLISHED` reason;
- grants **no** entity, history, or quota credit;
- **does not fabricate** a scalar registrant.

Effectiveness is then **demonstrated**, not assumed, by executing the exact intended mutant —
absent registrant-set evidence silently interpreted as a sole registrant. The new builder-level
test **must FAIL** under that mutant; the real implementation **must PASS**.

**MR-M10 becomes a two-layer protection**, and neither layer replaces the other:

```text
MR-M10A = builder / derivation rejection   (new)
MR-M10B = schema / freeze persistence backstop   (retained)
```

The dangling `test_group_r59` pointer the reviewer identified is corrected so the test group
truthfully names the implemented case.

**Required result:** `MR_M10_DERIVATION_MUTANT = KILLED`. A surviving mutant is a **STOP**.

## 5. Ruling — MIN-1: migration comment accuracy

Migration `0014` carries comments stating or implying that the new relational columns enter
`REGISTRANT_TABLE_COLUMNS` and therefore sit inside the governed digest. Under accepted
**Decision 084 R67** that is **false as to mechanism**: `candidate_identity.py` and its existing
digest tuples are deliberately **unchanged**, and the relational set is governed instead through
the existing candidate registrant **row representation** and its digest.

Only the stale comments are corrected, so that they describe the **actual accepted R67 binding
mechanism**. `REGISTRANT_TABLE_COLUMNS`, `ACCESSION_TABLE_COLUMNS`, and `SNAPSHOT_CONTENT_FIELDS`
are **not** widened, and **MIN-1 changes no executable semantics**.

## 6. Ruling — MIN-2: the established-with-zero-relation state must not persist

The review proved the census `established`-requires-relation guard covers **UPDATE** only, so a
direct **INSERT** can assert `registrant_set_completeness = 'established'` while zero substantive
relation rows exist. Downstream candidacy still fails closed, so the finding is **non-gating** —
but an accession must not be able to persist a semantically false **ESTABLISHED + ZERO
substantive registrants** state.

**Owner ruling: strengthen the schema anyway.** Because migration `0014` has **not** been
owner-accepted and has **not** been applied to any real E0 state, it may be corrected
**prospectively** in this stage. The preferred correction extends `0014`'s trigger/guard design so
the false state cannot survive the completed transactional operation.

**Insertion ordering must be respected.** If the legitimate ingest transaction must create the
accession row before its relation rows, **no impossible immediate trigger** may be created that
prevents the lawful transaction shape. The **actual writer transaction is inspected before** the
exact trigger shape is chosen, and the **narrowest** accepted mechanism is used.

Required disposable probes:

| Probe | Requirement |
|---|---|
| **A** | lawful established-single insert succeeds |
| **B** | lawful established-multi insert succeeds |
| **C** | unestablished insert succeeds where allowed |
| **D** | established + zero relation cannot reach an accepted/frozen persisted state |
| **E** | relation deletion that would leave an established set empty is refused |
| **F** | update to established without a relation is refused |
| **G** | existing migration empty-state safeguards still work |

**No fake registrant** may be introduced merely to satisfy a guard. A correction requiring
migration architecture changes **beyond** the **R58**/**R59** truth condition is a **STOP**.

## 7. Ruling — MIN-3: no unverifiable historical baseline

One re-baseline test contains a second purported pre-correction digest (`5f3f6a57…` for
`0000000018-18-000002`) that the independent reviewer could not reproduce as any genuine
pre-correction value, and the test asserts only `before != after` — insufficient provenance for a
historical identity baseline.

**Owner ruling: an unverifiable "before" literal is not retained.** Using a **disposable**
checkout or worktree of the genuine pre-correction parent `6fdec2ed…`, the intended exact
pre-correction input and state are independently reproduced. Then either:

- a genuine corresponding pre-correction digest exists — the unverifiable literal is **replaced by
  that exact reproduced value** and asserted exactly; **or**
- the scenario did not exist under the pre-correction representation — the **false
  historical-baseline framing is removed** and only the legitimate prospective corrected identity
  is tested, under a clearly named assertion.

**No predecessor hash is fabricated for symmetry.** For **every** retained before/after literal,
enough fixture and preimage provenance is recorded in the test or its comment that a fresh reviewer
can independently reproduce it from the parent commit.

**Required result:** `UNVERIFIABLE_PRECORRECTION_DIGESTS = 0`.

## 8. Ruling — MIN-4: the reserve per-CIK cap attaches to every substantive registrant

`reserve_selector._caps_preserved` attributes a joint bundle accession to the **replacement alone**
in the substituted-world simulation, which can undercount a co-registrant's per-CIK base cap in an
overlap case. It is synthetic reserve simulation only and fail-closed in the observed corner, but
it diverges from the **R62** entity-domain cap treatment used everywhere else — including this
module's own `_usage_from` for retained selections.

**Required semantics.** For an **established multi-registrant** accession in a reserve replacement
bundle, per-CIK / entity-domain cap accounting **attaches the accession to EVERY truthful
substantive registrant** represented by it. It is **never** attributed only to the replacement
entity, an anchor, the first registrant, the minimum or maximum CIK, or the submitter.
**Accession-domain accounting still counts the filing ONCE.** The existing base per-CIK cap value
and the research policy **do not change**.

Required focused coverage:

| Case | Requirement |
|---|---|
| **A** | joint replacement with two substantive registrants |
| **B** | one co-registrant already near or at the cap |
| **C** | replacement that would exceed that co-registrant cap is rejected / fails closed |
| **D** | the same joint accession is not double-counted in accession-domain totals |
| **E** | the order of associated registrants does not change the decision |
| **F** | single-registrant reserve behaviour unchanged |

A fix requiring a **research-policy constant** to change is a **STOP**.

## 9. Authorized correction paths

Authorized paths are limited to those necessary for the five accepted findings:

- `src/disclosure_drift/storage/migrations/0014_m33_multi_registrant_relational_correction.sql`
- `src/disclosure_drift/m3/candidate_snapshot.py`
- `src/disclosure_drift/sec/reserve_selector.py`
- existing and new unit tests covering the candidate snapshot / **R59** / **MR-M10**, migration
  `0014`, the identity re-baselines, the reserve selector and its caps, and audit or mutation
  tooling **only** where required to register the exact MR-M10 mutant
- truthful current-state documentation for the correction

`src/disclosure_drift/m3/candidate_identity.py` remains **PROHIBITED** unless a new owner stop is
raised. `acquisition.py` and `offline_execution.py` should need no further semantic change. Paths
are **not** broadened for cleanup, and an unexpected path that is not clearly required by
**M-1** or **MIN-1**–**MIN-4** is a **STOP** before editing.

## 10. Nonchange requirements

The correction preserves:

```text
SINGLE_REGISTRANT_UNEXPECTED_IDENTITY_DELTAS = 0
Affected governed identity inventory            = E1-E5 ONLY
snapshot_id                                     unchanged
entity_tie_break_sha256                         unchanged
R15 evidence_sha256 preimage                    unchanged
R16 resolution_sha256 preimage                  unchanged
candidate_identity.py                           unchanged
```

The **R67** relational digest-binding proof remains valid — **REMOVE** an association changes the
digest, **CHANGE** an association changes the digest, **ADD** an association changes the digest,
and **REORDER** leaves it unchanged.

No research quota value or declared domain changes. No historical accepted decision is rewritten.
No accepted **D081** evidence is changed. The private M3.2 catalog is untouched, and
`m3.2-complete` does not move. The migration chain remains `0001`–`0014` with `0015` absent, and
**no tag** is created.

## 11. What this record does not authorize

It does **not**: modify Decision 083 or Decision 084; reopen or redesign the **R58**–**R67**
architecture; revert, amend, or re-derive the reviewed target `09ee4422…`; edit the frozen review
artifact; write migration `0015`; implement the verified-evidence schema; execute Review A,
Review B, or the document adjudication; authorize **M3.3-E0**, **M3.3-E1**, **M3.3-E2**, or
**M3.4**; create any real E0 state; make any network, SEC, or HTTP request; apply migration `0014`
to the accepted private M3.2 operational catalog; write to the accepted M3.2 private evidence; move
`m3.2-complete`; or create any tag.

**Correction is not acceptance.** **R49** condition B remains **UNSATISFIED** until a fresh genuine
**Claude Fable 5 maximum** acceptance review **PASSES** and Sol/GPT accepts the corrected
implementation. The correcting session does **not** self-accept.

### Reviewer-epoch observation, recorded truthfully

The prior review packet requested Claude Fable 5; the returned report observed a harness identifier
of `claude-opus-5` and a presented model of Opus 5. **Whether that invalidates the already-failed
review is not adjudicated here, and the failed findings remain valid evidence.** For the **next**
independent formal acceptance review the owner requires a genuine Fable 5 epoch.

## 12. Next authorized action

Create this governance record, register it, commit it as **one governance-only commit** carrying no
source, test, or migration byte, and push once. Then implement **only** M-1 and MIN-1–MIN-4, re-run
**MR-M1**–**MR-M14** including the **exact** MR-M10 derivation mutant, run targeted and static
validation, run **exactly one** `make check-fast`, commit the correction as **one** implementation
commit, push once, and **return to Sol/GPT**.

```text
M3_3_D083_D084_R46_FORMAL_REVIEW_FINDINGS_OWNER_ACCEPTED_FOR_CORRECTION
M_1_MR_M10_BUILDER_PROTECTION        = ACCEPTED / GATING
MIN_1_MIGRATION_COMMENT_ACCURACY     = ACCEPTED / CORRECT NOW
MIN_2_ESTABLISHED_ZERO_RELATION      = ACCEPTED / CORRECT NOW
MIN_3_REBASELINE_PROVENANCE          = ACCEPTED / CORRECT NOW
MIN_4_RESERVE_PER_CIK_JOINT_CAP      = ACCEPTED / CORRECT NOW
MIGRATION_AUTHORIZED                 = 0014 correction only
M3_3_E0_AUTHORIZATION                = NO
R49_CONDITION_B                      = UNSATISFIED
NEXT_FORMAL_REVIEW_EPOCH             = GENUINE CLAUDE FABLE 5 MAXIMUM REQUIRED
```
