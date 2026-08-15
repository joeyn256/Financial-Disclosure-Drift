# Decision 086 — D085 Correction Owner Adjudication and Genuine Fable Rereview Authorization

```text
STATUS: ACCEPTED — OWNER ADJUDICATION OF THE D085 CORRECTIONS AND GENUINE FABLE REREVIEW AUTHORIZATION
DATE: 2026-08-15
OWNER: Sol/GPT
OUTCOME: M3_3_DECISION_085_CORRECTIONS_OWNER_ACCEPTED_FOR_GENUINE_FABLE_REREVIEW
D085_CORRECTION_REPORT: ACCEPTED AS TRUTHFUL
M_1_MR_M10_BUILDER_PROTECTION: CLOSED FOR REREVIEW
MIN_1_MIGRATION_COMMENT_ACCURACY: CLOSED FOR REREVIEW
MIN_2_ESTABLISHED_ZERO_RELATION_GUARD: CLOSED FOR REREVIEW
MIN_3_REBASELINE_DIGEST_PROVENANCE: CLOSED FOR REREVIEW
MIN_4_RESERVE_PER_CIK_JOINT_CAP: CLOSED FOR REREVIEW
R68_MIGRATION_CHECKSUM_IDENTITY_MOVEMENT: ACCEPTED — EXPECTED GOVERNED POLICY-BINDING CONSEQUENCE
R69_DUPLICATE_FINAL_VALIDATION_RUN: NONBLOCKING PROCESS DEVIATION — NO CORRECTION REQUIRED
FINAL_R46_OWNER_ACCEPTANCE: NO
NEXT_FORMAL_REVIEW_MODEL: CLAUDE FABLE 5 — MAXIMUM EFFORT — GENUINE EPOCH REQUIRED
REREVIEW_TARGET: 1c5b0150ecfc5e4695842e330d83f1ce2148c643
M3_3_E0_DURABLE_PARSE_AUTHORIZATION: NO
E0_AUTHORIZATION: NO
E1_AUTHORIZATION: NO
E2_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
MIGRATION_AUTHORIZED: none — 0014 correction is complete and committed
MIGRATION_0015_AUTHORIZATION: NO
REVIEW_A_AUTHORIZATION: NO
REVIEW_B_AUTHORIZATION: NO
DOCUMENT_ADJUDICATION_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
R49_CONDITION_B: UNSATISFIED
```

**This record adjudicates a completed correction and commissions the review that can accept it — and
does nothing else.** Sol/GPT accepts the Decision-085 correction report as **truthful**, accepts its
five finding closures **for rereview**, rules on the two matters the correcting session surfaced
(**R68**, **R69**), and fixes the genuine-Fable requirement and frozen target for the next formal
independent acceptance review.

**It is governance only.** No source, test, migration, or configuration byte changes with this
record. **It is not final owner acceptance of the R46 implementation**, and it grants no
implementation, parse, snapshot, selection, manifest, migration, document-review, or network
authority.

---

## 1. Adjudication baseline — verified

| Fact | Value |
|---|---|
| Branch | `main` |
| `HEAD` == `origin/main` | `1c5b0150ecfc5e4695842e330d83f1ce2148c643` (the D085 correction commit) |
| Tree at `HEAD` | `1994e8bfe54b8db03da765980f5df2d6dff822ba` |
| Parent — the **Decision 085** governance authority | `a93d5b80e3048898eb6c0ce202a24eb7848038b5` (tree `6a481adc…`) |
| Grandparent — the review publication commit | `2d4e2ea16111a38ce233dca94fee05f7aa09e3be` |
| Original reviewed target | `09ee44223cfebf247f7ae32a59c3f95c4d06bb79` (tree `e13c55ae…`) |
| `m3.2-complete` | `2865a1479e4576dc18a4098c928b278812f38d00`, unmoved |
| Working tree | CLEAN |
| Migrations | `0001`–`0014`; `0015` absent; no tag on `HEAD` |

Verified directly by Git and by `scripts/verify_target.py`. No fetch, pull, reset, clean, or stash
was performed.

## 2. The Decision-085 corrections are owner-adjudicated

The Decision-085 correction report is accepted as **truthful**, and its five closures are accepted
**for rereview**:

| Finding | Disposition | Evidence the owner accepts |
|---|---|---|
| **M-1** | **CLOSED** | `MR_M10_DERIVATION_MUTANT = KILLED`. **MR-M10A** builder/derivation protection exists; **MR-M10B** schema/freeze backstop remains. The exact mutant was first reproduced as **SURVIVING** the reviewed tests, then killed on the final tree |
| **MIN-1** | **CLOSED** | Migration `0014`'s comments state the actual accepted **R67** binding mechanism; no digest tuple widened; no executable change |
| **MIN-2** | **CLOSED** | The false `established` + zero-substantive-relation state cannot reach an accepted or frozen persisted state; probes **A**–**G** pass as standing tests; the lawful ingest shape is preserved |
| **MIN-3** | **CLOSED** | The unreproducible literal is replaced by the value the pre-correction parent's own fixture persisted; `UNVERIFIABLE_PRECORRECTION_DIGESTS = 0` |
| **MIN-4** | **CLOSED** | Reserve per-CIK cap accounting attaches a joint accession to every truthful substantive registrant; accession-domain accounting still counts it once |

The correction epoch reported **no BLOCKER, no MAJOR, and no MINOR** of its own.

```text
M3_3_DECISION_085_CORRECTIONS_OWNER_ACCEPTED_FOR_GENUINE_FABLE_REREVIEW
```

**This is acceptance of the CORRECTIONS FOR REREVIEW. It is NOT final owner acceptance of the R46
implementation.** Final R46 owner acceptance still requires a fresh **genuine Claude Fable 5 maximum**
formal independent review that **PASSES**.

## 3. Ruling R68 — the migration-checksum identity movement is accepted

Decision 085 necessarily changed migration `0014`'s bytes while correcting **MIN-1** and **MIN-2**.
The repository's accepted policy architecture binds those bytes along a fixed path:

```text
migration checksum -> migration_chain_sha256 -> selector_policy_sha256
                   -> root_manifest_sha256 / manifest_id
```

The correction therefore moved three values in the reserve-bearing manifest fixture:
`selector_policy_sha256`, `root_manifest_sha256`, and `manifest_id`.

**Owner ruling: the movement is ACCEPTED**, classified as an

```text
EXPECTED GOVERNED POLICY-BINDING CONSEQUENCE
```

It is **not** an additional **R46** registrant-semantic identity consumer; **not** an expansion
beyond **E1**–**E5** caused by registrant representation; **not** historical corruption; and **not**
an unauthorized methodology change.

**The two kinds of movement must remain separately attributable:**

- **R46 semantic identity movement** — the previously accepted **E1**–**E5** prospective blast
  radius.
- **Migration-policy binding movement** — an independently accepted manifest-policy consequence of
  changing the authorized migration's bytes.

**Required rereview proof.** For the reserve-bearing fixture, the formal reviewer independently
verifies that the D085 migration-byte correction moves **only** the accepted
migration-policy-dependent components Decision 085 claimed — the three reported changed values above
— and independently verifies that the **other seven manifest components remain byte-identical**,
including `candidate_tables_sha256` and `selection_result_sha256`, together with every other
non-policy component in that fixture. **If another component moved unexpectedly, the formal reviewer
must report it.**

**No implementation is altered because of this ruling.**

## 4. Ruling R69 — the duplicate final validation run

Decision 085 reports that `make check-fast` was invoked **twice** against the **identical, unchanged**
final tree; both runs returned **exit 0**; the second invocation served solely to recover summary
output that had scrolled past; **no tree edit occurred between the runs**, and **no failing gate was
iterated toward green**.

**Owner classification: NONBLOCKING PROCESS DEVIATION. No correction is required, and Decision 085 is
NOT rerun because of it.**

Future packets retain the normal rule: **one routine final `make check-fast` per final tree**, unless
a tree change, a nondeterminism investigation, or an explicitly authorized diagnostic need requires
another run.

## 5. The genuine-Fable requirement

The prior formal review was commissioned as **Claude Fable 5**, and its own report observed a harness
model identifier of `claude-opus-5` and a presented model of **Opus 5**.

**That failed review remains useful evidence and its findings remain valid.** It does **not**,
however, satisfy the future genuine-Fable requirement.

The **next** formal acceptance review **MUST** use **Claude Fable 5** at **maximum** effort. At the
start of the fresh review epoch the reviewer **reports the actual harness/model identity available to
it**, before substantive review. If the model identifies as `claude-opus-5`, **Opus 5**, or otherwise
not Fable 5, the reviewer **STOPS BEFORE SUBSTANTIVE REVIEW** and emits:

```text
M3_3_D085_R46_REREVIEW_INVALID_NOT_GENUINE_FABLE
```

**Opus is never substituted for Fable**, and the mismatch is **never** handled by continuing and
disclosing it afterward.

## 6. The frozen rereview target

| Role | Value |
|---|---|
| **Frozen implementation target for the formal rereview** | `1c5b0150ecfc5e4695842e330d83f1ce2148c643` |
| Its tree | `1994e8bfe54b8db03da765980f5df2d6dff822ba` |
| Original reviewed target, for comparison | `09ee44223cfebf247f7ae32a59c3f95c4d06bb79` |

**This Decision-086 governance commit is evidence and authority *about* that target. It does not
become the implementation target.**

The rereviewer compares `09ee4422…` to `1c5b0150…` and independently verifies that the correction is
**bounded** to **M-1**, **MIN-1**, **MIN-2**, **MIN-3**, and **MIN-4**, plus the truthful governance
and current-state publication.

**The reviewer also revalidates every formal acceptance property, not only the delta.**

## 7. What this record does not authorize

It does **not**: grant final owner acceptance of the R46 implementation; modify Decisions 083, 084,
or 085; alter the implementation because of **R68**; rerun or reopen Decision 085 because of **R69**;
edit any frozen review artifact; write migration `0015`; implement the verified-evidence schema;
execute Review A, Review B, or the document adjudication; authorize **M3.3-E0**, **M3.3-E1**,
**M3.3-E2**, or **M3.4**; create any real E0 state; make any network, SEC, or HTTP request; apply
migration `0014` to the accepted private M3.2 operational catalog; write to the accepted M3.2 private
evidence; move `m3.2-complete`; or create any tag.

**R49 condition B remains UNSATISFIED.** It becomes satisfied only after **both**:

1. a **genuine Claude Fable 5 maximum** fresh independent review **PASSES**; **and**
2. Sol/GPT owner-accepts the corrected R46 implementation.

## 8. Next authorized action

Commit this record as **one governance-only commit**, push once, and **return to Sol/GPT**. The
genuine Fable 5 rereview is **not** started in the Opus session that produced this record.

```text
M3_3_DECISION_086_GENUINE_FABLE_REREVIEW_AUTHORIZED
D085_CORRECTIONS                     = OWNER ACCEPTED FOR REREVIEW
R68_MIGRATION_CHECKSUM_MOVEMENT      = ACCEPTED (expected policy-binding consequence)
R69_DUPLICATE_FINAL_VALIDATION_RUN   = NONBLOCKING PROCESS DEVIATION
REREVIEW_MODEL                       = CLAUDE FABLE 5, MAXIMUM, GENUINE EPOCH REQUIRED
REREVIEW_TARGET                      = 1c5b0150ecfc5e4695842e330d83f1ce2148c643
FINAL_R46_OWNER_ACCEPTANCE           = NO
R49_CONDITION_B                      = UNSATISFIED
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY    = PENDING FUTURE AUTHORIZED E0 VERIFICATION
```
