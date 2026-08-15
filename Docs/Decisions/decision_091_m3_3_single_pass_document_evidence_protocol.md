# Decision 091 — Single-Pass Document-Evidence Protocol Owner Correction

```text
STATUS: ACCEPTED — OWNER PROTOCOL CORRECTION: SINGLE-PASS DOCUMENT-EVIDENCE REVIEW
DATE: 2026-08-15
OWNER: Sol/GPT
OUTCOME: M3_3_DECISION_091_SINGLE_OPUS_EVIDENCE_REVIEW_AUTHORIZED
M3_3_SINGLE_PASS_DOCUMENT_EVIDENCE_PROTOCOL_OWNER_ACCEPTED: YES
M3_3_SINGLE_DOCUMENT_EVIDENCE_REVIEW_AUTHORIZED: YES — Claude Opus 5, maximum effort, fresh /clear epoch
REVIEW_B_EXECUTION: NOT REQUIRED / NOT AUTHORIZED — retired prospectively, never begun
CLAUDE_DOCUMENT_ADJUDICATION: NOT REQUIRED / NOT AUTHORIZED — retired prospectively, never begun
SOL_GPT_OWNER_ADJUDICATION: PENDING REVIEW COMPLETION — replaces the retired Claude adjudication stage
M3_3_D088_VERIFIED_EVIDENCE_SCHEMA_OWNER_ACCEPTED: UNCHANGED — remains valid
M3_3_MIGRATION_0015_OWNER_ACCEPTED: UNCHANGED — remains valid
M3_3_VERIFIED_EVIDENCE_INFRASTRUCTURE_COMPLETE: UNCHANGED — remains valid
SCHEMA_COMPATIBILITY_RULING: SINGLE PASS CARRIES ON THE EXISTING review_a ROLE — NO SCHEMA CHANGE
PROTOCOL_VERSION: m3.3-document-evidence/1.0 — methodology unchanged
E0_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
MIGRATION_AUTHORIZED: NONE
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
D081_PRIVATE_EVIDENCE_ACCESS: READ ONLY — for the future single-review execution epoch only
```

**This record does one thing and nothing else.** It records Sol/GPT's **prospective supersession of
the document-review execution workflow** — the dual-Claude Review A → Review B → Claude
adjudication sequence is retired before any review began, and replaced by **one** Claude Opus 5
maximum document-evidence review over all 108 frozen D081 artifacts followed by **Sol/GPT owner
adjudication**.

**It executes nothing and reopens nothing.** No document is reviewed by this record, the accepted
evidence schema and migration `0015` are untouched, and no network, SEC, or HTTP request is made.
The recording session — the Decision-090 governance session, continued — does not execute the
review.

---

## 1. Entry state — verified

| Fact | Value |
|---|---|
| Branch | `main` |
| `HEAD` == `origin/main` | `f76639dc0603f6598c5525f652208ccf49b69b53` — the Decision 090 authority commit |
| Tree | `be1d211af1f9fb86d4a1e9fb89e3ebb9ac95c736` |
| Parent | `11a4a2e8220df528dfe66d7a6771e24100c7c5ad` — the fresh-rereview publication commit |
| Frozen accepted verified-evidence implementation | `746648285ec84d54a2ed7deaebc73f5c64b89d3d` |
| `m3.2-complete` | `2865a1479e4576dc18a4098c928b278812f38d00`, unmoved |
| Working tree | CLEAN |
| Migrations | `0001`–`0015` contiguous; `0016` ABSENT |

Verified read-only by Git. No fetch, pull, reset, clean, or stash was performed.

## 2. Decision 090's acceptance remains valid — nothing is reopened

The following Decision 090 rulings are **fully accepted and unchanged**:

```text
M3_3_D088_VERIFIED_EVIDENCE_SCHEMA_OWNER_ACCEPTED
M3_3_MIGRATION_0015_OWNER_ACCEPTED
M3_3_VERIFIED_EVIDENCE_INFRASTRUCTURE_COMPLETE
OBS-1 = OPEN / DEFERRED / NON-GATING
OBS-A = CLOSED / NON-DEFECT
OBS-B = ACCEPTED NON-DEFECT
OBS-C = ACCEPTED NON-DEFECT
```

Migration `0015` is **not reopened** and the accepted evidence schema is **not modified**.
Decision 091 changes **only the future document-review execution workflow**.

## 3. The old execution workflow is retired — prospectively, before any execution

The previously planned dual-Claude sequence — Review A (Opus 5) → Review B (Fable 5) → Claude
adjudication (Opus 5) — is **superseded prospectively**. The controlling factual state at the
moment of this change, verified against the governed catalog design and the repository:

| Fact | State |
|---|---|
| Review A | **NOT started** |
| Review B | **NOT started** |
| Document adjudication | **NOT started** |
| Real review rows | **NONE created** — the four evidence relations have never held a real row |

**Therefore no accepted review evidence is invalidated or rewritten.** This is a workflow
supersession with an empty execution history, not a revision of any produced evidence.

## 4. The new single-pass protocol — controlling sequence

```text
1. ONE independent Claude document-evidence review over ALL 108 frozen D081
   Complete Submission Text artifacts.
2. Freeze and content-address the complete review output.
3. Return the frozen evidence set to Sol/GPT.
4. Sol/GPT performs OWNER ADJUDICATION / acceptance of the produced evidence,
   including disposition of ambiguous or abstained cases and the resulting
   feasibility-gate determination.
5. Only after owner adjudication may the project determine whether the
   amendment-purpose and linked-amendment feasibility gates are satisfied and
   whether E0 should be authorized.
```

There is **no second Claude review pass**, **no Review-B execution**, and **no Claude A-vs-B
adjudication epoch**. Sol/GPT's owner adjudication **replaces** the retired Claude adjudication
stage.

## 5. The single reviewer

| Requirement | Value |
|---|---|
| Model | **Claude Opus 5** |
| Effort | **Maximum** |
| Epoch | **Fresh `/clear`** — one active session |
| Structure | **No subagents, no delegation, no parallel review workflows** |

**Owner reasoning, recorded:** this stage is evidence-production work requiring direct
source-document interpretation, exact provenance extraction, conservative abstention, and faithful
application of the already-frozen protocol. Fable remains the tool for independent software/formal
acceptance review; a second 108-document evidence pass is not required.

## 6. Protocol version and methodology — unchanged

The accepted evidence methodology remains **`m3.3-document-evidence/1.0`**. Nothing in this record
redefines the purpose categories, the explicit-original/linkage rules (X-1…X-6), the source-span
requirements, the abstention vocabulary, evidence applicability, private-artifact binding, or
verified-evidence semantics. **Only the reviewer/adjudication workflow changes.**

### 6.1 Schema-compatibility ruling — single pass on the existing `review_a` role

The frozen schema's role vocabulary (`review_a` / `review_b` / `adjudication`) was examined and
**exercised on a disposable catalog** to determine whether a single pass is representable without
any schema change. Ruling, confirmed by execution:

* **The single Claude review uses the existing `reviewer_role = 'review_a'` /
  `review_pass = 'A'` identity.** A single `review_a` record per accession — asserting or
  abstaining — writes lawfully with its spans, satisfies every review-layer guard (registered
  accession binding, one-role epoch, protocol pin, span assertion-matching, strict locations), and
  the complete pass freezes under the accepted `REVIEW_A_TABLE_DOMAIN` digest. **Review-B and
  adjudication-role rows simply remain absent.**
* **No trigger at the review layer requires a second pass.** The only guards referencing
  `review_b` are the epoch-role restriction (which restricts, never requires) and the two
  `document_adjudicated_evidence` provenance triggers — and those fire **only** on
  adjudicated-evidence inserts, which the single-pass protocol does not perform: Claude
  adjudication is retired, and Sol/GPT's owner adjudication operates on the frozen returned
  output, not through that relation.
* **Migration `0015` is not altered**, not to rename roles and not for any other reason.

**Recorded consequence, for a future owner decision rather than for now:** the accepted
`document_adjudicated_evidence` relation mechanically requires both an A and a B pass before an
adjudicated row can be written. Under the single-pass protocol no such row is written, so this is
no obstacle to the authorized review; but **if a later owner decision wants owner-adjudicated
results persisted in that specific relation, it will require its own separate authorization** —
that relation cannot lawfully be populated from a single pass as accepted. The stop condition in
the owner packet ("the frozen schema literally makes single-pass output impossible") does **not**
obtain: single-pass review output is fully representable.

## 7. The single review authority

The Decision 090 §5 Review-A authorization is **superseded and replaced** by:

```text
M3_3_SINGLE_DOCUMENT_EVIDENCE_REVIEW_AUTHORIZED
```

| Boundary | Value |
|---|---|
| Reviewer | Claude Opus 5, maximum effort, fresh `/clear` epoch |
| Scope | **ALL 108** frozen D081 artifacts — exactly that set; no substitution, enlargement, or shrinkage |
| Mode | **Offline only**; private artifact root **READ ONLY**; no artifact writes; the absolute root path never printed or persisted |
| Prohibited | New acquisition; SEC; HTTP; **E0**; **Review B**; **Claude adjudication**; any schema, source, test, migration, or configuration change |

### 7.1 Review questions — the accepted M3.3-v1 set only

**A. Amendment purpose.** Only the frozen three purpose categories; every positive assertion with
exact source-span provenance; **abstain** where evidence is insufficient; no classifier, no fuzzy
inference, no invented category.

**B. Explicit original / linkage.** Only accepted explicit-original evidence; linkage never
inferred from an `/A` suffix, a shared CIK, a shared report date, filing proximity, accession
order, name similarity, or any prohibited heuristic; every positive assertion with exact
source-span provenance.

### 7.2 Totality

The one review covers exactly **108 / 108** frozen D081 artifacts: missing = 0; extra = 0;
duplicate review records = 0; artifact SHA mismatches = 0; cross-accession artifact bindings = 0;
protocol-version mismatches = 0; positive assertions lacking source provenance = 0. Difficult
documents are never skipped — **abstention is the lawful outcome where required** (AP-1 totality).

### 7.3 Output freeze

At completion the entire single-review output is frozen and content-addressed. The completion
record states: artifact count; review-record count; span count; purpose assertion counts by
category; purpose abstention count; explicit-original assertion count; explicit-original
abstention count; the review digest; the review epoch ID; model; protocol version. The private
evidence-root absolute path never appears. **The frozen output is input to Sol/GPT owner
adjudication — not to another Claude reviewer.**

## 8. Sol/GPT owner adjudication

After the single Opus review completes, **no verified evidence is automatically owner-accepted**.
The complete frozen result returns to Sol/GPT, who determines:

* whether the evidence-production run is acceptable;
* whether any abstentions or conflicts require additional bounded work;
* which results may be owner-accepted as verified evidence;
* whether all three frozen amendment-purpose categories are genuinely witnessed;
* whether explicit-original/linkage evidence supports at least **8 distinct substantive entities**;
* whether the two real feasibility gates may close;
* whether **E0** may then be authorized.

**This owner adjudication replaces the retired Claude A/B adjudication stage.**

## 9. No self-granted verified credit

The one Claude review produces **review evidence**. It does not independently grant final verified
quota credit, close either real feasibility gate, authorize E0, authorize candidate selection, or
approve a root. **Those remain owner decisions.**

## 10. What this record does not authorize

It does **not**: execute the document review in the recording session; authorize Review B or any
Claude adjudication; modify migration `0015` or any schema, source, test, or configuration byte;
authorize migration `0016`; close either feasibility gate; authorize **M3.3-E0**, **E1**, **E2**,
or **M3.4**; authorize any network, SEC, or HTTP request (`REQUEST_CEILING = 0`, new SEC requests
= 0); move `m3.2-complete`; or create any tag.

Historical Decisions 080–090 are **not rewritten**; where their text describes the retired
dual-Claude workflow, Decision 091 is the controlling record and current-state references point
here rather than editing history. Both real-path feasibility gates —
`M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
`M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` — remain **OPEN** and are never merged into one
flag, and `REAL_ACCEPTANCE_ORDERING_ADEQUACY` remains **PENDING FUTURE AUTHORIZED E0
VERIFICATION**.

## 11. Next authorized action

**Execute the single document-evidence review in a fresh Claude Opus 5 maximum `/clear` epoch
under §7, then return the frozen output to Sol/GPT for owner adjudication.** The recording
governance session stops here.

```text
M3_3_DECISION_091_SINGLE_OPUS_EVIDENCE_REVIEW_AUTHORIZED
M3_3_SINGLE_PASS_DOCUMENT_EVIDENCE_PROTOCOL_OWNER_ACCEPTED
M3_3_SINGLE_DOCUMENT_EVIDENCE_REVIEW_AUTHORIZED
REVIEW_B = NOT REQUIRED / NOT AUTHORIZED
CLAUDE_DOCUMENT_ADJUDICATION = NOT REQUIRED / NOT AUTHORIZED
SOL_GPT_OWNER_ADJUDICATION = PENDING REVIEW COMPLETION
M3_3_E0_AUTHORIZATION = NO
MIGRATION_AUTHORIZED = NONE; MIGRATION 0016 = NO
NETWORK / SEC / HTTP = NONE; REQUEST_CEILING = 0
```
