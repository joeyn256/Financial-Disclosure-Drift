# Decision 060 — M3.2A One-Use Carry-In Authority Mint

**Date:** 2026-08-10
**Status:** ACCEPTED — OWNER AUTHORITY MINT 2026-08-10
**Authority classification:** `M3_2A_ONE_USE_CARRY_IN_AUTHORITY_MINTED_AND_UNCONSUMED`
**Type:** Owner **authority-mint** record. It performs the single bounded owner act that
[Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md)
§14 named as the next authorized action — `OWNER_M3_2_CARRY_IN_AUTHORITY_MINT_PACKET` — by minting
**exactly one** one-use clean-root carry-in authority under schema `m3-carry-in-authority/1.0`
([Decision 055](decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md)
§6, ruling **055-B**), fixing its canonical bytes, its external SHA-256 identity, and every binding
Decision 055 §§6.1 and 9 require. It changes no executable, test, migration, configuration,
contract, runbook, template, or reason-code byte, opens no private or governed operational state,
touches no USB archive, makes no network or SEC contact, and performs no operational act.

**Minting is not consuming, and neither is running.** This record **creates an authority artifact
and consumes nothing.** The authority is **UNCONSUMED**, remains so until a later, separately
authorized live invocation burns it, and **authorizes no invocation by itself**. It grants **no**
T6, **no** clean M3.2A run, **no** transport construction, **no** network or SEC activity, **no**
M3.2B, **no** Gate H, **no** second adoption, **no** retry, **no** resume, and **no** tag.

**Amends:** nothing in place. Decisions 001–059 remain **byte-unchanged**; Decision 055, Decision
057, Decision 058, and Decision 059 specifically are preserved **byte-identical**.
**Narrowly supersedes:** only the **current-state statements that no carry-in authority exists** and
that **minting it is the next authorized action** — in [Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md)
§§11, 13, and 14, in [`Docs/Decisions/decision_registry.md`](decision_registry.md), in
[`Milestones/STATUS.md`](../../Milestones/STATUS.md), and in the **M3-L16** forward-looking mint
references in [`Docs/m3/limitations_register.md`](../m3/limitations_register.md). Every one of those
statements was accurate when written and is preserved as **historical**; **nothing else in any
accepted record is superseded, weakened, or reopened.**
**Preserves unchanged:** the cumulative M3.2A ceiling **801** and the frozen 75-logical-request plan
at SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; the accepted
historical seed **1** and **SEC request consumption 1 of 801**; the historical run's **permanent
non-resumability** and its `UNDETERMINED` recovery classification; the absence of a terminating
receipt; Decision 057 §12's permanent prohibition on re-adoption; **M3-L16 `CLOSED — DECISION
059`**; **M3-L15** byte-for-byte; migrations `0001`–`0013`; and every network, SEC, transport,
recovery, provenance, leakage, evidence-preservation, determinism, and owner-gated-live-operation
rule not expressly addressed here.
**Related:** [Decision 055](decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md) §§5, 6, 6.1–6.5, 7, 9;
[Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md) §§5, 6, 11, 14;
[Decision 057](decision_057_m3_2_orphan_adoption_procedure_authorization.md) §12;
[Decision 056](decision_056_m3_2_carry_in_implementation_acceptance_and_m3_l14_closure.md);
[Decision 054](decision_054_m3_2_interrupted_run_closure_acceptance.md);
[Decision 051](decision_051_m3_2_post_t5_remediation_governance.md) §9;
[Decision 050](decision_050_m3_2_t5_initial_live_invocation_authorization.md) §8;
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §§5, 8, 9, 12, 17;
[`Docs/m3/limitations_register.md`](../m3/limitations_register.md) **M3-L15**, **M3-L16**;
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** what this record does and does not do (§1); the owner instrument and its ratified
prerequisites (§2); authority verification (§3); the independently derived current action (§4);
ruling **060-A**, the minted authority and its exact bindings (§5); ruling **060-B**, the authorized
new run id and the permanently non-resumable historical run (§6); ruling **060-C**, one-use
semantics, consumption, and refusal (§7); ruling **060-D**, historical request accounting (§8);
ruling **060-E**, custody and materialization (§9); ruling **060-F**, what the mint does not
authorize (§10); the limitations disposition (§11); the `9475eb3d…` standing matter (§12); the path
and publication boundary (§13); the recorded status (§14); and the formal outcome and exact next
authorized action (§15).

---

## 1. What this record does, and what it does not

**It does:**

- record the owner mint instrument and the six ratified prerequisite tokens it rests on (§2);
- verify the controlling authority live, at exact identities, before minting (§3);
- confirm **independently from repository authority** that the current authorized action is
  `OWNER_M3_2_CARRY_IN_AUTHORITY_MINT_PACKET` (§4);
- **mint exactly one** one-use clean-root carry-in authority under schema
  `m3-carry-in-authority/1.0`, fixing its **canonical bytes**, its **external SHA-256 identity**,
  and every binding Decision 055 §§6.1 and 9 require (§5);
- fix the **authorized new run id**, derived by the accepted repository mechanism, and restate that
  the historical interrupted run is **permanently non-resumable and never reused** (§6);
- fix the authority's **one-use, run-bound, window-bound, route-bound, ceiling-bound,
  consumption-bound, Decision-059-bound, evidence-manifest-bound, non-transferable,
  non-replayable** semantics, and its refusal and replacement rules (§7);
- **preserve the accepted historical SEC consumption of 1 of 801 exactly**, and forbid any
  zero-baseline restatement (§8);
- fix **custody and materialization** discipline for the artifact bytes (§9);
- state the authority boundary after the mint and name the exact next bounded owner action
  (§§10, 15).

**It does not:**

- **consume** the authority, execute anything, or start any run;
- authorize **T6**, a clean M3.2A run, transport construction, network use, DNS, or SEC contact;
- authorize **M3.2B**, **Gate H**, a **second adoption**, a **retry**, a **replay**, or a **resume**
  of the historical run;
- open, read, or mutate the operational catalog, data root, raw object, lineage intent, projection
  file, private evidence bundle, or USB archive;
- alter any limitation's state, close any limitation, or reopen a closed one;
- resolve the `9475eb3d…` publication-1 ratification question (§12);
- create any production, test, migration, configuration, reason-code, runbook, contract, or
  template byte;
- claim M3.2 completion or live readiness. **M3.2 is NOT COMPLETE**, and **live readiness is NOT
  CLAIMED.**

## 2. The owner instrument and its ratified prerequisites

The mint proceeds under the owner instrument:

```text
OWNER_M3_2_CARRY_IN_AUTHORITY_MINT_PACKET
```

issued by the project owner (Sol/GPT role) on **2026-08-10**, and naming this stage as **one**
bounded owner-governance authority-mint act with no execution content.

The six prerequisite facts the instrument recorded are **already owner-accepted** and are
independently confirmed by the repository surfaces cited at §3:

```text
M3_2_DECISION_057_ONE_SHOT_ORPHAN_ADOPTION_SUCCESS
M3_2_DECISION_057_FRESH_POST_EXECUTION_VERIFICATION_PASS
M3_2_DECISION_057_FRESH_POST_EXECUTION_VERIFICATION_OWNER_ACCEPTED
M3_2_DECISION_059_M3_L16_CLOSURE_GOVERNANCE_SYNCHRONIZATION_SUCCESS
M3_2_DECISION_059_M3_L16_CLOSURE_GOVERNANCE_SYNCHRONIZATION_ACCEPTED_FOR_FRESH_VERIFICATION
M3_2_DECISION_059_FRESH_ZERO_MINOR_PUBLICATION_VERIFICATION_PASS
M3_2_DECISION_059_FRESH_ZERO_MINOR_PUBLICATION_VERIFICATION_OWNER_ACCEPTED
```

The first three are recorded verbatim in accepted Decision 059 §2 and are the closure basis of its
ruling **059-D**. The four Decision-059 publication and verification tokens are owner-held
acceptance facts for the Decision 059 publication at commit
`fabd86ac0f881c416f77b5b3e5d7cad6f0383576`; this record transcribes them and does not re-derive
them, exactly as Decision 059 §3 transcribed the execution facts rather than reopening private
state to re-verify them.

**Decision 059 §5's condition is the operative one for this mint:** the Decision-057 one-shot orphan
adoption is **finally owner-accepted with zero unresolved historical orphan mismatch** — the exact
state Decision 055 §9 (Path B) required **before a carry-in artifact may be minted or consumed**.
That condition is satisfied, and the mint below is lawful for the first time.

## 3. Authority verification

The controlling authority was re-read in full before this record was written, at these exact
identities, verified live at the recording baseline `fabd86ac0f881c416f77b5b3e5d7cad6f0383576`
(branch `main`, `HEAD == origin/main`, clean index and worktree, ahead/behind `0/0`, no tag at
`HEAD`, tree `24cae4941b5471353419b831176591c807e66163`, parent
`a1a3b89b78ba7c24f1e82d8e47c6b9e01dac716e`):

| Authority | SHA-256 |
|---|---|
| [Decision 055](decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md) | `43c5ae4612a4e22f06ba53cf20913ba456c8a4e0f0e33397c012cdd32966727c` |
| [Decision 057](decision_057_m3_2_orphan_adoption_procedure_authorization.md) | `0bdb0e2b6e103298aaa4a11d75f5bb3e52dbfb5fc8321c14708e7196b525bc53` |
| [Decision 058](decision_058_m3_2_decision_057_final_owner_acceptance_and_execution_sequence_ratification.md) | `611c5683684e9a4b76d18324eeb23e75a75af6f917c833b2c587ad1cd3045497` |
| [Decision 059](decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md) | `6af4a8c8392542cfae7d1454747778cfb3fe4c12be8bb50becc3d6d29cee0ff5` |
| [`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) | `f8398a146b08476a270fd30f3bd53b557564ebbb9aa577ad32d72434361b4875` |
| [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) | `e421354014b75dda8763097645a4194bba38b3447e10851e6d778e7b314073a9` |
| [`Docs/Decisions/decision_registry.md`](decision_registry.md) | `b4bb8f2335a5b680bf1b145a425104822d4a3d350735fb792f8bbc0fb60b96c0` |
| [`Milestones/STATUS.md`](../../Milestones/STATUS.md) | `3366ff291b559b03928a3b39423648ea11d3efe0b8e1e6e0fd6e84b271abdac0` |

**Publication identities.** Decision 055 was published at commit
`5f4fbc479034c71eabacc9470ebd5df396335eb2` (subject `Authorize M3.2 carry-in implementation`) and
has been **byte-unchanged since**; Decision 059 was published at commit
`fabd86ac0f881c416f77b5b3e5d7cad6f0383576` (subject
`Close M3-L16 and synchronize post-adoption governance`) and is likewise byte-unchanged. Both were
confirmed by their complete file histories, each of which contains exactly one commit.

The last four hashes are the values **as read before this record's own edits**; the registry, the
ledger, and the register are inside this recording's authorized envelope (§13), so their identities
necessarily change with the commit that publishes this record. That is the same convention
Decision 055 §3 and Decision 059 followed, and it is a property of self-reference rather than a
drift.

Tracked network configuration was verified in [`configs/project.yaml`](../../configs/project.yaml):
`network.enabled: false` and `network.m3_acquire_enabled: false`, both still `false`.

The accepted carry-in implementation was read **read-only** to bind this mint to the code that will
validate it — `src/disclosure_drift/m3/acquisition.py` (the closed artifact field set, the loader,
the fixed-binding re-proof, the identity proof, and the consumption boundary),
`src/disclosure_drift/m3/recovery.py` (the fixed Decision 055 constants and the checkpoint
cross-check), and `src/disclosure_drift/m3/receipt.py` (`canonical_bytes`). **No source, test,
configuration, or migration byte was modified.** **No operational catalog, private evidence
artifact, raw object, lineage record, projection file, lease, receipt store, operational checkpoint,
or USB archive was opened by this recording — not even read-only.**

## 4. The independently derived current action

The current authorized action was derived from repository authority rather than assumed from the
owner instrument:

- accepted Decision 059 §14 records `NEXT_AUTHORIZED_ACTION: OWNER_M3_2_CARRY_IN_AUTHORITY_MINT_PACKET`;
- `Milestones/STATUS.md` carries the same marker, and its `ACTIVE_BLOCKER` names the exact binding
  set the mint must carry;
- the **M3-L16** register entry names the same act as the related future act sitting outside that
  (closed) entry;
- the decision registry's Decision 059 row names the same next action.

All four agree. There is no disagreement between repository authority and the owner instrument, so
the mint proceeds.

## 5. Ruling 060-A — the minted authority

**Exactly one** carry-in authority is minted. It is the authority Decision 055 §6 describes, carrying
the closed field set the accepted implementation enforces, and **no other authority exists, is
authorized, or may be minted without a new owner act.**

### 5.1 Canonical bytes

The artifact's **canonical bytes** are exactly the following single line, terminated by exactly one
LF:

```json
{"acquisition_window":"M3.2A","approved_request_ceiling":801,"authorized_census_run_id":"m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44","authorizing_decision_reference":"Decision 055","historical_consumed_request_count":1,"historical_route_allocation":{"sec_bulk_submissions":1},"orphan_adoption_decision_reference":"Decision 059","orphan_adoption_evidence_sha256":"981b5e420dda42e54d2622624db76f95e6072d181f549bf25ae6d05e9d942e5b","request_plan_sha256":"19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68","schema_version":"m3-carry-in-authority/1.0"}
```

**Byte-derivation rule, so the bytes are reproducible without ambiguity:** UTF-8, **no** byte-order
mark, **LF** only, keys sorted by code point at every level, no insignificant whitespace, integers
rendered without a decimal point, **no** field omitted and **no** field added, and **exactly one**
trailing newline. That is the accepted `canonical_bytes` form (`src/disclosure_drift/m3/receipt.py`
§6 canonicalization), and it yields exactly **571 bytes**.

### 5.2 External identity

```text
CARRY_IN_AUTHORITY_SHA256: d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d
CARRY_IN_AUTHORITY_BYTE_LENGTH: 571
```

The **SHA-256 of the exact canonical artifact bytes is the authority's external identity**
(Decision 055 §6.1). Consistent with that ruling there is **no self-hash field inside the artifact**:
the field set is closed to the ten bindings above, an eleventh field is refused, and the identity is
recomputed by the reader from the bytes rather than read back from inside its own preimage.

### 5.3 The bound identity set

| Binding | Bound value | Source of the accepted value |
|---|---|---|
| `schema_version` | `m3-carry-in-authority/1.0` | Decision 055 §6.1; `CARRY_IN_AUTHORITY_SCHEMA_VERSION` |
| `acquisition_window` | `M3.2A` | Decision 055 §6.1; `CARRY_IN_ACQUISITION_WINDOW` |
| `request_plan_sha256` | `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` | Decision 055 §5; contract §5 |
| `approved_request_ceiling` | `801` | Decision 055 §5 — never `802`, additive, shadowed, or reset |
| `historical_consumed_request_count` | `1` | Decision 055 §4 fact 1, §5 (historical seed `H`) |
| `historical_route_allocation` | `{"sec_bulk_submissions": 1}` | Decision 055 §4 fact 2 — compared as a **whole mapping** |
| `authorizing_decision_reference` | `Decision 055` | Decision 055 §6.1 — the record authorizing the mechanism |
| `authorized_census_run_id` | `m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44` | §6 below — new, and never the historical run |
| `orphan_adoption_decision_reference` | `Decision 059` | Decision 055 §9 and Decision 059 §11 — the accepted Path-B adoption record, necessarily not Decision 055 |
| `orphan_adoption_evidence_sha256` | `981b5e420dda42e54d2622624db76f95e6072d181f549bf25ae6d05e9d942e5b` | Decision 059 §§11, 13 — the accepted execution-evidence manifest identity |

**Decision-055 identity, in full.** The artifact's `authorizing_decision_reference` binding is the
literal `Decision 055`, which is the value the accepted implementation compares against
`CARRY_IN_AUTHORIZING_DECISION_REFERENCE`. For the record, the complete publication identity of that
authority is: file
`Docs/Decisions/decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md`,
SHA-256 `43c5ae4612a4e22f06ba53cf20913ba456c8a4e0f0e33397c012cdd32966727c`, published at commit
`5f4fbc479034c71eabacc9470ebd5df396335eb2`.

**Decision-059 identity, in full.** The artifact's `orphan_adoption_decision_reference` binding is
the literal `Decision 059`, whose complete publication identity is: file
`Docs/Decisions/decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md`,
SHA-256 `6af4a8c8392542cfae7d1454747778cfb3fe4c12be8bb50becc3d6d29cee0ff5`, published at commit
`fabd86ac0f881c416f77b5b3e5d7cad6f0383576`.

### 5.4 Validation performed before this record was written

The exact bytes at §5.1 were validated **offline** against the accepted implementation
(Decision 056's accepted candidate, unmodified), with no network, no private state, and no
operational catalog:

1. `load_carry_in_authority` **admitted** the bytes — proving they parse as UTF-8 JSON, carry exactly
   the closed field set with no missing and no unpermitted field, re-serialize **byte-identically**
   to their canonical form, carry no §6.1 prohibited content, and declare the accepted schema.
2. `require_admitted_carry_in_authority` **re-proved** the admitted object — the §6.1 content rule,
   every fixed Decision 055 binding compared **literally** against the module constants, and the
   external identity recomputed as the SHA-256 of the canonical closed document the object's own
   bindings form.
3. `verify_carry_in_authority` **passed** against invocation parameters window `M3.2A`, plan
   `19be7bdc…`, ceiling `801`, and `resuming=False`.
4. The loader's independently computed `authority_sha256` **equals** `d7aa206b…` at §5.2.

**That validation created nothing, consumed nothing, and opened no catalog.** It proves only that
the artifact **would be admitted** by the accepted code; admission is not authorization, and no
invocation was made or is permitted by it.

## 6. Ruling 060-B — the authorized new run id, and the historical run

```text
AUTHORIZED_NEW_CENSUS_RUN_ID: m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44
```

- It was generated by the **accepted repository mechanism** —
  `default_run_id_factory()` in `src/disclosure_drift/m3/acquisition.py`, which is exactly
  `f"m3-2-acquisition-{uuid.uuid4().hex}"` — and by nothing else. **No new schema, no new format,
  and no hand-chosen identifier was invented.**
- It is **bound into the authority** (§5.3) and is therefore fixed: Decision 055 §6.2 makes the
  authorized run id come **from the artifact**, replacing random generation for that invocation, and
  a registration for any other run id is refused before any transport.
- **It was not used to start a run in this stage, and no run exists under it.** No operational or
  private state was opened, written, or queried to test it.
- **Uniqueness is established without any prohibited private access.** It is enforced where it
  actually matters, at registration: `register_acquisition_run` refuses a `census_run_id` already
  present in `ops_ingestion_jobs` before any transport is constructed, so a collision fails closed
  rather than silently adopting or overwriting an existing identity. Independently, the accepted
  facts of Decision 059 §3 record the catalog as holding only the historical `stopped` M3.2A job,
  whose identity is stated below and differs. **No probe of private state was required or made.**

**The historical interrupted run.**

```text
HISTORICAL_RUN_ID:        m3-2-acquisition-e9f27d4906474378a0064b6a172f9ca0
HISTORICAL_JOB_STATE:     stopped
RESUME_AUTHORITY:         NONE — PERMANENTLY NON-RESUMABLE
REUSED_AS_NEW_RUN_ID:     NO — AND IT MAY NEVER BE
RECOVERY_CLASSIFICATION:  UNDETERMINED — UNCHANGED
TERMINATING_RECEIPT:      NONE EXISTS
```

Decision 051 §9's permanent no-resume ruling, preserved by Decision 055 and Decision 059, stands
unaltered. The historical run id is **never** the authorized run id, is never revived, and this
mint neither resumes it, retries it, replays it, nor reclassifies it. What the accepted adoption
cleared was the **raw-store/catalog orphan mismatch**, not the recovery classification — and this
record changes neither.

## 7. Ruling 060-C — one-use semantics, consumption, and refusal

The minted authority is, in substance and not merely in bookkeeping:

- **an owner authority artifact** — inert evidence of an owner grant. **It executes nothing.**
- **one-use** — it may be consumed **exactly once**, by a single later, separately authorized live
  invocation, and never again;
- **run-bound** — to `m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44` alone;
- **window-bound** — to `M3.2A` alone; a consumption attempt registering any other window is refused
  before the catalog is opened, so the one M3.2A exception can never be spent on `M3.2B`;
- **route-bound** — to the whole allocation `{"sec_bulk_submissions": 1}`, compared as a mapping, so
  a substituted, extra, or omitted route is refused;
- **ceiling-bound** — to cumulative `801`;
- **historical-consumption-bound** — to seed `1`, never `0`;
- **plan-bound** — to the frozen plan `19be7bdc…`;
- **Decision-055-bound** and **Decision-059-bound**, and **evidence-manifest-bound** to
  `981b5e42…`;
- **non-transferable to a different run**, and **non-replayable after consumption**.

**Consumption mechanics (Decision 055 §6.3, as implemented and accepted).** Consumption is the
insertion of a deterministic `ops_checkpoints` primary key inside the **same** `BEGIN IMMEDIATE`
transaction as the new run's registration. The key this authority will burn its single use in is
fixed by its identity:

```text
CARRY_IN_CONSUMPTION_CHECKPOINT_KEY:
m3_2_carry_in_authority:d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d
```

and the canonical nine-field checkpoint document it will durably record — carrying no secret, no
identity header or value, no response body, and no private absolute path — is:

```json
{"acquisition_window":"M3.2A","approved_request_ceiling":801,"authority_sha256":"d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d","authorized_census_run_id":"m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44","authorizing_decision_reference":"Decision 055","consumed_request_count_carried_forward":1,"historical_route_allocation":{"sec_bulk_submissions":1},"request_plan_sha256":"19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68","schema_version":"m3-carry-in-authority/1.0"}
```

That document is serialized by the **same** canonical rule as the artifact at §5.1 — UTF-8, no BOM,
LF only, keys sorted at every level, no insignificant whitespace, and **exactly one trailing
newline** — so the stored `checkpoint_value` is the line above plus one LF, **509** bytes in total.

**No row of that document exists today.** `ops_checkpoints` holds **0** rows (Decision 059 §3), and
this record writes none. The document is published here so a later receipt and catalog cross-check
(Decision 055 §7.5) has a public, owner-fixed expectation to be held against.

**Mismatch refusal — fail closed, before transport.** If, at consumption time, the bound run id,
route allocation, plan hash, window, ceiling, historical seed, schema, authorizing-decision
identity, orphan-adoption decision identity, or evidence-manifest identity does not match — or the
bytes are malformed or non-canonical, or a binding is missing, or the artifact path is unsafe or
escaping, or `--resume-from` is supplied alongside it, or the deterministic checkpoint key already
exists — the invocation **REFUSES and FAILS CLOSED before a transport is constructed**. None of
those refusals is recoverable in place.

**Burn-before-wire (Decision 055 §6.5).** If a pre-wire failure occurs **after** the registration
transaction commits, the authority remains **burned even with zero attempts placed**. **There is no
automatic reissue, no automatic retry, and no automatic replacement.**

**Replacement rule.** The carry-in authority **cannot be silently regenerated or replaced.** A
replacement is a **new owner act** — a further owner mint record — and never an automatic recovery,
never a session's initiative, and never implied by any failure.

## 8. Ruling 060-D — historical request accounting

The mint changes no request accounting whatsoever.

```text
SEC_PHYSICAL_REQUEST_CONSUMPTION_BEFORE_MINT:  1 / 801
MINT_EFFECT_ON_CONSUMPTION:                    NONE — NO REQUEST, NO RESERVATION, NO WIRE ACTIVITY
SEC_PHYSICAL_REQUEST_CONSUMPTION_AFTER_MINT:   1 / 801
HISTORICAL_SEED_H:                             1 — CARRIED FORWARD EXACTLY, NEVER RESET TO 0
REMAINING_TOTAL_HEADROOM:                      800
REMAINING_BULK_ROUTE_HEADROOM:                 5 — ACCOUNTING AND REPORTING ONLY, NEVER A RUNTIME REFUSAL
```

**This carry-in is not permission to start from a zero-request history.** The future clean run
begins from the accepted consumed baseline of **1**: the global `PhysicalAttemptCeiling` is
constructed with `approved_ceiling` **801** and `consumed` **1**, cumulative consumption is `1 + N`
where `N` is that invocation's own wire attempts, and there is **no `802`, no additive ceiling, no
shadow ceiling, no reset, and no reinterpretation**. A clean carry-in root receipt carries **1** in
`consumed_request_count_carried_forward`, names this authority in `carry_in_authority_sha256`,
records `actual_physical_attempt_count` as **`N` only**, and the chain walker adds the root carry-in
**exactly once** (Decision 055 §§7.4–7.5).

**The historical request is not restored, replayed, or re-attempted**, and **no SEC contact occurred
or is authorized**. The frozen 75-logical-request plan is unchanged and is never trimmed or
re-derived to fit the reduced headroom; a stop at cumulative 801 with planned work remaining remains
a lawful `stopped_at_ceiling` outcome and a Gate H failure, exactly as before.

## 9. Ruling 060-E — custody and materialization

Decision 055 §6.2 requires the CLI to take the artifact **from the governed evidence root by a safe
relative path**, under the existing escape-refusing discipline. That evidence root is **external to
this repository** (`require_external_evidence_root`) and is **governed private state**, which this
mint stage is expressly forbidden to open.

Those two facts are reconciled, not traded off:

1. **The mint fixes the authority.** Its canonical bytes (§5.1), its external SHA-256 identity
   (§5.2), and every binding (§5.3) are fixed **here**, in public governance, by the owner act. The
   artifact is fully determined and independently reproducible from this record; nothing about it is
   left to a later session's discretion.
2. **Materialization is delivery, not minting.** Writing those exact bytes to a safe relative path
   beneath the governed evidence root is a bounded **operator** step belonging to the later,
   separately authorized live-operation instrument (§15) — performed under that instrument's own
   authority, verified by recomputing the SHA-256 and requiring it to equal `d7aa206b…` before use,
   and **not performed by this record**.
3. **No repository copy is created.** No `.json` artifact is committed, and **no new directory is
   invented**: the repository already defines exactly one location for this artifact, and it is the
   governed evidence root. A second, differently located copy would create an ambiguous
   authority-of-record, which Decision 055 §6.1's single-identity rule does not permit.

**If the materialized bytes ever fail to hash to `d7aa206b…`, they are not this authority**, and the
invocation must refuse and stop rather than proceed on an artifact that was not minted here.

## 10. Ruling 060-F — what the mint does not authorize

**Decision 060 authorizes none of the following, and no session may read it as doing so:**

- **consumption of the authority it mints** — the authority is minted **UNCONSUMED**, and consuming
  it requires the later separately authorized live invocation;
- **T6** (controlled M3.2A acquisition execution) — it **additionally requires its own owner
  authorization** under the accepted contract §8, whose rung **T5** demands a separate explicit owner
  instrument naming the exact command invocation, window `M3.2A`, plan hash `19be7bdc…`, ceiling
  `801`, and the configuration change enabling network for `m3 acquire` only;
- **any clean M3.2A run**, transport construction, or `m3 acquire --live` invocation;
- **network enablement, DNS, HTTP, or SEC contact** — tracked switches remain `false`/`false`,
  CompanyFacts remains disabled and prohibited, and network enablement remains separately
  owner-gated by the exact later operation-specific authorization the contract requires;
- **M3.2B**, **Gate H**, or any live-readiness claim;
- **a second orphan adoption or any retry** — the real adoption invocation is **1 consumed /
  0 remaining**, and Decision 057 §12's prohibition on re-adoption after a committed `INSERT` stands
  permanently;
- **resume, replay, or retry of the historical run** `m3-2-acquisition-e9f27d4906474378a0064b6a172f9ca0`;
- **a second carry-in authority**, a regenerated authority, or an automatic replacement (§7);
- **any mutation** of the execution evidence bundle, catalog, projection, raw object, lineage, or USB
  archive;
- **any tag.**

Migrations remain `0001`–`0013`; the ceiling **801** is never increased, reset, shadowed, or
reinterpreted; SEC consumption remains **1 of 801**; the historical run remains permanently
non-resumable with recovery classification `UNDETERMINED`; and **live readiness is NOT claimed**.
**M3.2 is NOT COMPLETE.**

## 11. Limitations disposition

```text
M3_L14:  CLOSED — DECISION 056 — UNTOUCHED
M3_L15:  ACTIVE — UNTOUCHED AND BYTE-UNCHANGED
M3_L16:  CLOSED — DECISION 059 — UNCHANGED; ONLY ITS FORWARD-LOOKING MINT REFERENCES ARE MADE CURRENT
```

**No limitation's state is altered by this record. None is closed, none is reopened, and no new
entry is created.**

**M3-L15 — does it condition the mint, T6, or the clean run?** It was examined directly. M3-L15
records that the second-SIGTERM `delivered` latch, which suppresses a second signal during
live-acquisition cleanup, is implemented and was directly verified by process-level fault injection
but carries **no committed regression test**. Its accurately recorded conditions are:

- it places **no condition on carry-in minting** and **does not block this stage**;
- it places **no condition on T6 authorization** and states none;
- it is a **test-strength gap, not a production defect**, whose behaviour was independently confirmed
  correct; its methodology, reproducibility, security, and publication impacts are all **none**;
- its **stop condition** is narrow and unrelated to the mint: *any edit to the scoped SIGTERM
  handling that is not accompanied by a test covering second-signal suppression*. **No such edit
  occurs here** — this record changes no executable byte at all;
- it does, however, remain **`ACTIVE` for M3.2 and every later phase that runs the governed
  live-acquisition lifecycle**, so a future clean M3.2A run proceeds while it is open, exactly as the
  register states. **It is recorded, not closed, and not discharged.**

**No other active limitation blocks the mint.** M3-L01–M3-L10 remain `ACTIVE` and are live-operation
and platform risk entries that condition acquisition execution rather than governance minting; none
names carry-in minting, and none is altered here. **D023-O1** remains the sole unresolved
owner-ruling condition — `LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED` — and
is carried forward unchanged as a stop-and-refer condition that a real run may reach; it is not
triggered by this record.

**No active limitation blocks the mint itself**, so the mint proceeds.

## 12. The `9475eb3d…` standing matter

The fresh independent Decision-059 verifier determined that the ratification question attaching to
Decision 057 **publication 1** at commit `9475eb3d614aa70b3f2a04b061d63bd7ea51c030` (tree
`e0b9b12095c181ba974336399f04fc1e44eb4a11`) is:

- a **separate standing owner bookkeeping matter**;
- **non-blocking for Decision 059**;
- **non-blocking for carry-in minting.**

**That status is preserved exactly.** This record does **not** resolve it, does **not** ratify or
void that publication, and does **not** modify any historical Decision 057 fact to force a
resolution. Decision 057's bytes are unchanged, and its own recorded position — that all six
publications are recorded as fact, that publication 1's ratification remains an owner ruling neither
granted nor withheld by the record itself, and that publication 2 at `103b3d39…` is owner-ratified
as **publication fact only, which is expressly not execution acceptance** — stands unaltered.

Fresh inspection of the controlling records surfaced **no rule making that question a precondition
of the mint**: Decision 055 §9 conditions minting on the executed, verified, and accepted orphan
adoption alone, and Decision 059 §5 records that condition as satisfied. Had a contradictory
controlling rule been found, this stage would have stopped; none was.

## 13. Path and publication boundary

Exactly **four** repository paths are authorized for this recording, with **no fifth**:

1. `Docs/Decisions/decision_060_m3_2_carry_in_authority_mint.md` (this record)
2. [`Docs/Decisions/decision_registry.md`](decision_registry.md)
3. [`Milestones/STATUS.md`](../../Milestones/STATUS.md)
4. [`Docs/m3/limitations_register.md`](../m3/limitations_register.md) — **M3-L16** currency **only**,
   confined to the forward-looking statements that the carry-in mint is a still-outstanding future
   act; **no status, closure, stop-condition, or closure-evidence determination changes**, and
   **M3-L15 and every unrelated entry are preserved byte-for-byte**

[`Docs/decision_index.md`](../decision_index.md) is **not** edited, following the convention for
Decisions 050–059.

Expressly **not** edited: any accepted decision 001–059, each preserved byte-identical; the accepted
contract; the receipt specification; the operator runbook; every template and evidence index; the
SEC data dictionary; every durable review artifact; every production source; every test; every
configuration; every migration; every reason code; the `Makefile`; `pyproject.toml`; and every
script. **No private state, no governed evidence root, no operational catalog, and no USB archive is
touched.**

**Publication** is exactly **one** governance commit on `main` over those four paths, under the
subject `Mint M3.2A one-use carry-in authority`, followed by exactly **one** ordinary
fast-forward push to `origin/main`. No force, no fetch, no pull, no rebase, no squash, no amend, no
cherry-pick, no branch, no worktree, no stash, and **no history rewrite**. **NO TAG** — M3.2 is not
complete. A record cannot contain the hash of the commit that contains it, so this record's own
commit identity is established by that act.

## 14. Recorded status

```text
DECISION_060_TYPE:                OWNER AUTHORITY MINT — GOVERNANCE PUBLICATION ONLY
RECORD_IS_SELF_EXECUTING:         NO — MINTS AN AUTHORITY; GRANTS NO OPERATIONAL ACT
CARRY_IN_AUTHORITY:               MINTED — UNCONSUMED
CARRY_IN_AUTHORITY_SCHEMA:        m3-carry-in-authority/1.0
CARRY_IN_AUTHORITY_SHA256:        d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d
CARRY_IN_AUTHORITY_BYTE_LENGTH:   571
CARRY_IN_CONSUMPTION_CHECKPOINT:  m3_2_carry_in_authority:d7aa206b8ceeb01c206bed8ade0c614bf86a0aa4bb592c16407f9d94f9e06f9d — NO SUCH ROW EXISTS; ops_checkpoints REMAINS 0
CARRY_IN_USES_TOTAL:              1
CARRY_IN_USES_CONSUMED:           0
CARRY_IN_USES_REMAINING:          1
CARRY_IN_REPLACEMENT:             NEW OWNER ACT ONLY — NEVER AUTOMATIC, NEVER SILENT
WINDOW:                           M3.2A
REQUEST_PLAN:                     FROZEN — 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68, 75 LOGICAL REQUESTS
CUMULATIVE_CEILING:               801 — NEVER 802, ADDITIVE, SHADOWED, OR RESET
HISTORICAL_SEED_H:                1 — CARRIED FORWARD EXACTLY; ZERO-BASELINE START NEVER LAWFUL
ROUTE_ALLOCATION:                 sec_bulk_submissions: 1 — COMPARED AS A WHOLE MAPPING
AUTHORIZING_DECISION:             Decision 055 (43c5ae46…, PUBLISHED 5f4fbc47…)
ORPHAN_ADOPTION_DECISION:         Decision 059 (6af4a8c8…, PUBLISHED fabd86ac…)
ORPHAN_ADOPTION_EVIDENCE_SHA256:  981b5e420dda42e54d2622624db76f95e6072d181f549bf25ae6d05e9d942e5b
AUTHORIZED_NEW_RUN_ID:            m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44 — NOT STARTED, NOT REGISTERED
RUN_ID_MECHANISM:                 default_run_id_factory() — m3-2-acquisition-{uuid4 hex}; NO NEW SCHEMA INVENTED
HISTORICAL_RUN_ID:                m3-2-acquisition-e9f27d4906474378a0064b6a172f9ca0
HISTORICAL_RUN_STATE:             stopped — PERMANENTLY NON-RESUMABLE; NEVER REUSED AS THE NEW RUN ID
HISTORICAL_RUN_CLASSIFICATION:    UNDETERMINED — UNCHANGED
TERMINATING_RECEIPT:              NONE — NOT CREATED, NOT RECONSTRUCTED
SEC_REQUEST_CONSUMPTION:          1 / 801 — UNCHANGED BEFORE AND AFTER THE MINT
REMAINING_TOTAL_HEADROOM:         800
BULK_ROUTE_HEADROOM:              5 — ACCOUNTING AND REPORTING ONLY
ARTIFACT_MATERIALIZATION:         NOT PERFORMED HERE — A BOUNDED OPERATOR STEP OF THE LATER INSTRUMENT, VERIFIED BY DIGEST
PRIVATE_STATE_ACCESS:             NONE — NO CATALOG, DATA ROOT, RAW OBJECT, LINEAGE, PROJECTION, EVIDENCE BUNDLE, OR USB
EXECUTABLE_BYTES_CHANGED:         NONE
MIGRATION:                        NONE — 0001-0013 UNCHANGED
NETWORK:                          NOT AUTHORIZED — TRACKED false / false; COMPANYFACTS DISABLED
SEC_CONTACT:                      NONE OCCURRED — NONE AUTHORIZED
TRANSPORT_CONSTRUCTION:           NOT_AUTHORIZED
CLEAN_RUN:                        NOT_AUTHORIZED
T6:                               NOT_AUTHORIZED — REQUIRES ITS OWN OWNER AUTHORIZATION UNDER CONTRACT §8
M3_2B:                            NOT_AUTHORIZED
GATE_H:                           NOT_AUTHORIZED
SECOND_ADOPTION:                  NOT_AUTHORIZED — 1 CONSUMED / 0 REMAINING, PERMANENTLY
HISTORICAL_RUN_RESUME:            PROHIBITED
M3_L14:                           CLOSED — DECISION 056; UNTOUCHED
M3_L15:                           ACTIVE — UNTOUCHED, BYTE-UNCHANGED; CONDITIONS NEITHER THE MINT NOR T6
M3_L16:                           CLOSED — DECISION 059; STATE UNCHANGED BY THIS RECORD
9475eb3d_MATTER:                  SEPARATE STANDING OWNER MATTER — NONBLOCKING; NOT RESOLVED HERE
LIVE_READINESS:                   NOT_CLAIMED
TAG:                              NONE
M3_2:                             NOT_COMPLETE
```

## 15. Formal outcome and exact next authorized action

```text
FORMAL_OUTCOME: M3_2A_ONE_USE_CARRY_IN_AUTHORITY_MINTED_AND_UNCONSUMED
CARRY_IN: MINTED / UNCONSUMED
EXECUTION_AUTHORITY: NONE
NETWORK_OR_SEC_AUTHORITY: NONE
LIVE_READINESS: NOT_CLAIMED
NEXT_AUTHORIZED_ACTION: OWNER_M3_2_T5_CLEAN_CARRY_IN_LIVE_INVOCATION_AUTHORIZATION_PACKET
```

**How that next action is derived, and what it is.** The accepted contract §8 fixes the remaining
ladder: rung **T5** is *live-operation authorization (M3.2A) — one bounded acquisition operation*,
requiring **a separate, explicit owner instrument naming the exact command invocation, window
`M3.2A`, plan hash `19be7bdc…`, ceiling `801`, and the configuration change enabling network for
`m3 acquire` only*; rung **T6** is *controlled acquisition execution (M3.2A window)* and happens
**only after T5**. Decision 059 §11 states the same single gate from the other side — that T6
"additionally requires its own owner authorization under the accepted contract §8". They name one
act, not two competing ones.

The one T5 grant that has ever existed was Decision 050's
`ONE_INITIAL_M3_2A_LIVE_INVOCATION`; it was exercised, ended non-successfully, and is **exhausted**.
It is never reused, extended, or read as covering the clean carry-in run.

No token for the next packet existed anywhere in the repository, so — following the same convention
by which each accepted record names its successor, and the Decision 050 precedent pair
`OWNER_M3_2_T5_INITIAL_LIVE_INVOCATION_AUTHORIZATION_PACKET` →
`OWNER_M3_2_T5_INITIAL_LIVE_INVOCATION_EXECUTION_PACKET` — this record fixes its identity as
`OWNER_M3_2_T5_CLEAN_CARRY_IN_LIVE_INVOCATION_AUTHORIZATION_PACKET`. That instrument, and only it,
may authorize the clean carry-in M3.2A invocation that later consumes the authority minted here; a
separate execution packet follows it, on the Decision 050 pattern.

**It does not self-execute.** No session may begin it, or any part of it, before the owner issues
it. It is not begun, not drafted as authority, and not implied by this record.

**Minting is not authorization, authorization is not execution, and no execution exists to authorize
here.**

Owner: **Joseph Nihill, acting through the ChatGPT project-owner role.** This is a transparent
recorded owner decision; it is not a handwritten, cryptographic, or third-party digital signature.
