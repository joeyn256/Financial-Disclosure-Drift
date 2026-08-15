# Decision 089 — D088 Correction Owner Adjudication and Fresh Independent Rereview Authorization

```text
STATUS: ACCEPTED — OWNER ADJUDICATION OF THE D088 CORRECTIONS AND FRESH REREVIEW AUTHORIZATION
DATE: 2026-08-15
OWNER: Sol/GPT
OUTCOME: M3_3_DECISION_088_VERIFIED_EVIDENCE_CORRECTIONS_OWNER_ACCEPTED_FOR_REREVIEW
D087_VERIFIED_EVIDENCE_SCHEMA: NOT YET OWNER ACCEPTED
D087_M_1_STATUS: CLOSED FOR REREVIEW
D087_MIN_1_STATUS: CLOSED FOR REREVIEW
D087_MIN_2_STATUS: CLOSED FOR REREVIEW
D087_MIN_3_STATUS: CLOSED FOR REREVIEW
D087_OBS_2_STATUS: CLOSED
D087_OBS_3_STATUS: CLOSED
OBS_1_STATUS: OPEN / NON-GATING / DEFERRED
OBS_A_STATUS: OPEN FOR FRESH CONTRACT REREVIEW — NEITHER PRE-ACCEPTED NOR PRE-CONDEMNED
OBS_B_STATUS: ACCEPTED NON-DEFECT OBSERVATION
FROZEN_REREVIEW_TARGET: 746648285ec84d54a2ed7deaebc73f5c64b89d3d
FROZEN_REREVIEW_TREE: 1afd1c3bbecd7f2e38aee5901dffd9214e499c4b
REREVIEW_MODEL: Claude Fable 5, maximum effort, fresh /clear epoch
CORRECTION_SESSION_MAY_REREVIEW: NO
MIGRATION_AUTHORIZED: NONE
MIGRATION_0016_AUTHORIZATION: NO
DOCUMENT_REVIEW_A_AUTHORIZATION: NO
DOCUMENT_REVIEW_B_AUTHORIZATION: NO
DOCUMENT_ADJUDICATION_AUTHORIZATION: NO
E0_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
D081_PRIVATE_EVIDENCE_ACCESS: NO
```

**This record does two things and nothing else.** It records Sol/GPT's **owner adjudication of the
Decision 088 corrections — for rereview, not for acceptance** — and it **commissions the fresh
independent acceptance rereview** of the corrected target.

**It accepts no schema, and it grants no execution authority.** No document review runs, no filing is
classified, no real evidence is created, no migration is authorized, and no network, SEC, or HTTP
request is made.

---

## 1. Entry state — verified

| Fact | Value |
|---|---|
| Branch | `main` |
| `HEAD` == `origin/main` | `746648285ec84d54a2ed7deaebc73f5c64b89d3d` |
| Tree | `1afd1c3bbecd7f2e38aee5901dffd9214e499c4b` |
| Parent — the Decision 088 authority commit | `fc972b58d92b68be9fe6fe4dbb4808a25aed45aa` |
| The D087-reviewed implementation | `8c13fc79aee649df4956643f0b24504c8cdfd2c7` |
| `m3.2-complete` | `2865a1479e4576dc18a4098c928b278812f38d00`, unmoved |
| Working tree | CLEAN |
| Migrations | `0001`–`0015` contiguous; `0016` absent |
| Tag at `HEAD` | none |

Verified read-only by Git. No fetch, pull, reset, clean, or stash.

## 2. The Decision 088 corrections — accepted **for rereview**

The correction session reported its work truthfully and completely, including the two new
observations it found in its own output. Sol/GPT accepts that report **as truthful for the purpose of
commissioning a rereview**:

```text
M3_3_DECISION_088_VERIFIED_EVIDENCE_CORRECTIONS_OWNER_ACCEPTED_FOR_REREVIEW
```

| Finding | Disposition |
|---|---|
| **M-1** — the `INSERT OR REPLACE` rewrite door | **CLOSED FOR REREVIEW** |
| **MIN-1** — cross-accession artifact binding | **CLOSED FOR REREVIEW** |
| **MIN-2** — `agreed`-state consistency, and the unprotected `verified` CHECK | **CLOSED FOR REREVIEW** |
| **MIN-3** — verified-candidate accession re-pointing | **CLOSED FOR REREVIEW** |
| **OBS-2** — the migration `0015` §1 precondition comment | **CLOSED** |
| **OBS-3** — permissive `span_location` validation | **CLOSED** |

The correction epoch reported **BLOCKER 0 / MAJOR 0 / MINOR 0** for defects it introduced, and one
routine `make check-fast` at **4210 passed / 1 pre-existing skip / 0 failed**.

**This is acceptance of the correction work for rereview. It is NOT final owner acceptance of the
verified-evidence schema**, which remains **NOT YET OWNER ACCEPTED**. "Closed for rereview" means the
owner is satisfied the finding was addressed well enough to be re-examined by an independent party —
it does not mean the finding is proven closed. **The fresh reviewer inherits no conclusion.**

## 3. M-1 — the replacement door, to be re-proved independently

The owner accepts, **for rereview only**:

```text
D087_M1_REPLACEMENT_REWRITE_DOOR = CLOSED
```

The fresh reviewer **independently re-proves** that the four evidence relations —
`document_artifacts`, `document_review_records`, `document_review_spans`, and
`document_adjudicated_evidence` — cannot be silently rewritten by conflict-resolution write idioms,
including `INSERT OR REPLACE` and the applicable `INSERT OR IGNORE` and conflict routes the accepted
migration-`0013` pattern covers. The re-proof runs against the **corrected** target through the
repository's own connection machinery, on disposable catalogs.

**Do not inherit the correction session's conclusion.** A guard that is present is not the same as a
guard that holds.

## 4. MIN-1 through MIN-3 — to be verified independently

Accepted **for rereview**, each to be re-verified from the schema rather than from the report:

| # | The claim the reviewer must test |
|---|---|
| **MIN-1** | Cross-accession binding is closed on **both** sides — a review and an adjudication must bind an artifact **registered to their own accession** |
| **MIN-2** | `agreement_state = 'agreed'` requires substantive, agreeing Review A and Review B records, and cannot be manufactured from abstentions |
| **MIN-3** | Verified candidate evidence cannot survive re-pointing to an accession lacking the required frozen adjudicated evidence |

## 5. OBS-1 — deferred, and still open

```text
OBS-1 = OPEN / NON-GATING / DEFERRED
```

Non-canonical contributor-review-id encodings may satisfy the SQL arithmetic even though the module
emits canonical, sorted, deduplicated hex identities. **No correction is authorized by this record.**

The fresh reviewer **confirms** — rather than assumes — that:

1. no **false hash-derived contributor membership** becomes expressible;
2. the module's canonical serialization remains deterministic;
3. the **authoritative** membership set remains the governed review-record set;
4. the observation remains **non-gating**.

**If any of those assumptions proves false, the reviewer classifies the resulting defect normally** —
as a BLOCKER, MAJOR, or MINOR on its actual merits, unconstrained by OBS-1's current label.

## 6. OBS-A — the `abstained` state, open for **contract** rereview

The Decision 088 session raised a **new** observation: `agreement_state = 'abstained'` is not
constrained symmetrically with the newly protected `agreement_state = 'agreed'`.

```text
OBS-A = OPEN FOR FRESH CONTRACT REREVIEW
```

**The owner neither pre-accepts the current behaviour nor pre-condemns it, and authorizes no
correction in this record.**

**The question is a contract question, not a symmetry question.** The reviewer reads the actual
accepted definitions governing `agreement_state`, abstention, Review A, Review B, and adjudication —
[Decision 082](decision_082_m3_3_d081_owner_adjudication_and_pre_e0_contracts.md) §§12.2, 12.5, 12.6;
[Decision 083](decision_083_m3_3_pre_e0_multi_registrant_correction.md) §9 (**R64**); and Decision
080's **AP-1** totality rule — and determines whether the schema's representation of `abstained`
**faithfully implements the frozen contract**.

**Do not infer the answer from the fact that `agreed` now carries a consistency rule.** Symmetry is
not itself an argument; the governing contract is.

At minimum, evaluate:

| # | Case |
|---|---|
| **A** | Both A and B abstain |
| **B** | A abstains, B asserts |
| **C** | A asserts, B abstains |
| **D** | Neither abstains, but no accepted adjudicated value results |
| **E** | Which `agreement_state` is **contractually correct** in each lawful case |
| **F** | Whether `abstained` can **misstate governed provenance**, even though it can carry neither verified credit nor an adjudicated value |

**Classification.** If the existing behaviour violates the frozen contract, classify it **MINOR or
MAJOR according to actual governed-state impact**. If it is contract-faithful, record:

```text
OBS-A = CLOSED / NON-DEFECT
```

## 7. OBS-B — defence in depth, accepted

`document_adjudicated_evidence_requires_bound_artifact` became hard to reach behaviourally once the
stronger registered-accession guards began failing earlier.

```text
OBS-B = ACCEPTED NON-DEFECT OBSERVATION
```

The invariant **may remain** as defence in depth, and **is not removed merely because another guard
usually fires first**. The reviewer confirms it is neither contradictory nor harmful. **No
independent-reachability requirement is imposed for style**, and its retention is not a finding.

## 8. The migration-checksum policy movement

Decision 088 changed migration `0015`'s bytes, so the accepted policy path moves again:

```text
0015 checksum -> migration_chain_sha256 -> selector_policy_sha256
              -> root_manifest_sha256 / manifest_id
```

Decision 088 reports that **only** those policy-chain-derived values moved and that the **eight**
substantive manifest components stayed **byte-identical** — `candidate_tables_sha256`,
`selection_result_sha256`, `source_observation_set_sha256`, `quota_definitions_sha256`,
`selected_entities_sha256`, `selected_accessions_sha256`, `reserves_sha256`, and
`quota_report_sha256` — with the canonical-JSON length unchanged.

**The fresh reviewer independently reproduces that claim.** **No additional identity movement is
authorized by this record**, and any component moving beyond the accepted policy path must be
reported.

## 9. The frozen rereview target

| Fact | Value |
|---|---|
| **Implementation target** | `746648285ec84d54a2ed7deaebc73f5c64b89d3d` |
| **Tree** | `1afd1c3bbecd7f2e38aee5901dffd9214e499c4b` |
| Pre-correction comparison point | `8c13fc79aee649df4956643f0b24504c8cdfd2c7` |
| Decision 088 authority | `fc972b58d92b68be9fe6fe4dbb4808a25aed45aa` |

**This record's own governance commit is evidence and authority ABOUT that target. It does not
replace it**, and the reviewer must not mistake the governance commit for the implementation.

The reviewer compares `8c13fc79…` to `746648285…` and independently verifies the correction is
**bounded**. **The rereview is not limited to the correction delta**: the reviewer revalidates the
**full** verified-evidence acceptance boundary, exactly as if reviewing the schema for the first
time.

## 10. The fresh-rereview requirement

| Requirement | Value |
|---|---|
| Model | **Claude Fable 5** |
| Effort | **Maximum** |
| Epoch | **Fresh `/clear`**, different from the D087/D088 session |
| Subagents, delegation, parallel review workflows | **None** |
| Inheriting the correction session's conclusions | **Prohibited** |

**The session that performed the D087 review and the D088 correction MUST NOT perform this
rereview.** It reviewed the target, then corrected it under owner authority; it is not eligible to
independently accept its own corrected work. That session's role ended when it returned to Sol/GPT.

## 11. What this record does not authorize

It does **not** accept the verified-evidence schema; correct OBS-1 or OBS-A; execute Review A, Review
B, or the adjudication; classify any real filing; populate or access any real Decision-081 evidence;
authorize **M3.3-E0**, **E1**, **E2**, or **M3.4**; authorize any network, SEC, or HTTP request;
authorize migration `0016` or any other migration; move `m3.2-complete`; or create any tag.

Both real-path feasibility gates — `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
`M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` — remain **OPEN** and are never merged into one
flag, and `REAL_ACCEPTANCE_ORDERING_ADEQUACY` remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION**.

## 12. Next authorized action

**Commission the fresh independent acceptance rereview of `746648285ec84d54a2ed7deaebc73f5c64b89d3d`
in a new `/clear` Claude Fable 5 maximum epoch, then return to Sol/GPT.**

The corrected schema needs **both** halves before document Review A can begin:

1. a **fresh independent rereview PASS**; and
2. **Sol/GPT final owner acceptance**.

```text
M3_3_DECISION_088_VERIFIED_EVIDENCE_CORRECTIONS_OWNER_ACCEPTED_FOR_REREVIEW
D087_VERIFIED_EVIDENCE_SCHEMA = NOT YET OWNER ACCEPTED
OBS-1 = OPEN / NON-GATING / DEFERRED
OBS-A = OPEN FOR FRESH CONTRACT REREVIEW
OBS-B = ACCEPTED NON-DEFECT OBSERVATION
MIGRATION_AUTHORIZED = NONE; MIGRATION 0016 = NO
M3_3_E0_AUTHORIZATION = NO
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY = PENDING FUTURE AUTHORIZED E0 VERIFICATION
```
