# Decision 075 — M3.3-I/R Ultrareview Bounded Correction

```text
STATUS: ACCEPTED — OWNER M3.3-I/R ULTRAREVIEW BOUNDED CORRECTION
DATE: 2026-08-14
OWNER: Sol/GPT
OUTCOME: M3_3_I_R_ULTRAREVIEW_FINDINGS_OWNER_ACCEPTED_FOR_BOUNDED_CORRECTION
IMPLEMENTATION_AUTHORIZATION: BOUNDED — THE THREE MINOR CORRECTIONS AND THE TWO ADOPTED
  OBSERVATION STRENGTHENINGS BELOW, AND NOTHING ELSE
REAL_PRIVATE_PARSE_AUTHORIZATION: NO
REAL_SNAPSHOT_AUTHORIZATION: NO
REAL_SELECTION_AUTHORIZATION: NO
MANIFEST_ROOT_CONSTRUCTION_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
PRIVATE_EVIDENCE_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: none
REQUEST_CEILING: 0
```

**This record accepts the M3.3-I/R ultrareview's findings and authorizes exactly the bounded
corrections they require.** It reopens **no** architecture and **no** methodology. It creates no
stage, changes no selector, changes no quota, changes no schema, and changes no real-path fact.

**It authorizes no real execution.** M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 all remain separate,
unissued owner gates; network, SEC, reacquisition, and private-evidence access remain **NONE**;
`EV_ROOT` remains prohibited; migration remains `none`; the request ceiling remains **0**; and
`m3.2-complete` remains immutable.

**Where this record and an earlier governing record disagree**, it controls only on the points it
names. Decisions 001–074 remain accepted and byte-unchanged, and Decisions 070–074 remain
controlling for everything they govern.

---

## 1. The reviewed target and the verdict

The independent read-only ultrareview ran against the frozen executable I/R target and its
implementer evidence commit:

| Fact | Value |
|---|---|
| Ultrareview executable target | `6f87abc6a8601bb5dc9029d2b113351e34f9e948` (tree `f1dc77269eeac12f4fd2432d5aa4e45acbcd28f1`) |
| Implementer evidence commit | `6b8968f3a9ea3502471d3e9efb1268ce8cdb7385` (tree `1d8d5e3ab2574527d845da35f1d22406f3af243e`) |
| Immutable implementer evidence artifact | [`Docs/m3/reviews/m3_3_i_r_rehearsal_6f87abc.md`](../m3/reviews/m3_3_i_r_rehearsal_6f87abc.md) |
| Verdict | **BLOCKER 0 · MAJOR 0 · MINOR 3 · OPTIMIZATION 0 · OBSERVATION 6** |

```text
M3_3_I_R_ULTRAREVIEW_B0_M0_MIN3_OWNER_ACCEPTED_FOR_BOUNDED_CORRECTION
```

## 2. What the ultrareview confirmed, and the owner accepts

The owner accepts the ultrareview's architectural conclusion in full. The following are
**correct** and are **not reopened** by this record: **R31** / **E5**; **R32**; **R33**; **R34**;
**IMP-1**; **IMP-2**; **IMP-3**; Track A; Track B; **R28**; the accepted joint selector, unchanged;
the 2009/2010 pair; persistence, run identity, and reconstruction; the **R3** replay standard; the
seal / manifest separation; Decision 023 **O1**; the CLI real-gate refusals; and the network and
private-data boundary.

**No architecture reopening and no methodology reopening is authorized.**

## 3. The three accepted MINOR findings

Each is **accepted** and each requires exactly the bounded correction named.

### 3.1 MIN-1 — stale current-state pointers in `Docs/decision_index.md`

Two rows in [`Docs/decision_index.md`](../decision_index.md) read as **current** while stating
positions that later accepted records have moved:

- The **R18** row stated the 70 quarterly full-index sources as category **C**, deliberately
  untouched. That classification was **narrowly superseded** by accepted
  [Decision 072](decision_072_m3_3_full_index_multi_registrant_source_correction.md) §2, Ruling
  **R22**. Corrected by the same narrow-supersession model already used elsewhere in the
  repository: `sec_full_index_company` is **candidate-substantive**, and each plan-bound
  full-index source is category **A** when usable and category **B** when accepted unavailable,
  and **never category C**. **Decision 068 is not rewritten historically**, and R18's report-level
  disposition mechanics remain authoritative except for that narrow classification.
- The `coverage_policy_version` row left the **current** executable-home question looking
  unresolved. The row may accurately record that Decision 067 §8 alone did not fix it; it now
  additionally carries the current pointer to accepted
  [Decision 070](decision_070_m3_3_i_r_implementation_authorization.md) §4, which fixes the
  canonical executable home as `PILOT_COVERAGE_POLICY_VERSION` in
  `src/disclosure_drift/pilot_policy.py` at `pilot-coverage/1.0`.

The index is **not** restructured, and no other row is rewritten.

### 3.2 MIN-2 — broken Decision 070–074 links in the contracts README

The five Decision 070–074 links in the current-state banner of
[`Milestones/contracts/README.md`](../../Milestones/contracts/README.md) used `../Docs/Decisions/…`
where the file's own directory depth requires `../../Docs/Decisions/…`. All five are corrected and
mechanically verified to resolve, and every markdown file in the original I/R delta plus this
correction is link-checked. **No link text and no decision semantics is altered for style.**

### 3.3 MIN-3 — an incomplete generated real-gate payload

`ExecutionRehearsalReport.as_payload()` in `src/disclosure_drift/m3/execution_rehearsal.py`
generated `real_amendment_purpose_feasibility_gate` but omitted the independently governed second
gate. `real_linked_amendment_feasibility_gate` is added beside it, at `OPEN`.

**The two gates remain separate.** They are **never** replaced by a generic
`real_feasibility_gate` or by any merged field, and `real_builder_feasibility_proved` is retained
as a **third, separate** claim that neither gate stands in for. The fixture-only
`m3 rehearse-execution` summary prints both gates **by name**, on their own lines, beside the
retained builder-feasibility line.

## 4. Report-schema version — owner compatibility ruling

**The existing execution-rehearsal report schema version is NOT bumped.** It remains
`m3-3a-execution-rehearsal-report/1.0`.

**Reason.** MIN-3 is an **additive completion of an already-governed real-gate status block**. It
does not reinterpret an existing key, remove a key, rename a key, alter scenario semantics, alter
selector behavior, alter the persisted database schema, or grant authority. Bumping the version
would misrepresent an omission-repair as a contract change.

## 5. Adopted observation strengthenings

Neither is a correctness finding. The owner adopts the smallest direct improvement of each,
**because this correction already changes tests**.

- **OBS-1 — direct IMP-3 proof.** A direct assertion proves the unrelated synthetic `10-D` census
  accession (a) exists in the census / source-history layer, (b) does **not** appear in
  `pilot_candidate_accessions`, and (c) appears in `excluded_form_counts` with the expected
  deterministic count — while **R20** can still read the same row as source-history evidence for
  the asset-backed predicate. **Test-only**: IMP-3 production code is not changed unless the direct
  test exposes an actual defect, and it did not.
- **OBS-3 — local strict-subset E5 proof.** The accepted M2.3 reserve-selector suite already proves
  strict-subset rejection. Because **R31** / **E5** is approval-critical, one direct M3.3
  I/R-level test is added beside the existing strict-superset test, proving that a **strict
  subset** replacement bundle yields **no compatible package**, through the **same** accepted
  `build_reserve_packages` entry point. `reserve_selector.py` is **not** altered and no
  reserve-signature logic is duplicated. The M3.3-specific suite now directly proves **both**
  directions.

## 6. OBS-6 — the durable mutation-campaign record

OBS-6 is **not** retroactively upgraded to a MINOR, and the existing M1–M38 campaign remains valid.
Before formal Fable acceptance, however, the owner requires a **durable, reviewable** campaign
record, created after the corrected executable target is frozen at
`Docs/m3/reviews/m3_3_i_r_mutation_campaign_<CORRECTED_EXECUTABLE_SHORT_SHA>.md`.

The temporary mutation runner is **not** added to production source; no mutated copy of source and
no scratch file is committed; and mutation tooling is **not** part of the package runtime. Campaign
facts are **recovered**, never fabricated: any mutation whose exact definition cannot be truthfully
recovered is recorded as `NOT_DURABLY_RECOVERABLE` and stops for owner referral rather than being
invented.

## 7. The original implementer evidence is immutable

[`Docs/m3/reviews/m3_3_i_r_rehearsal_6f87abc.md`](../m3/reviews/m3_3_i_r_rehearsal_6f87abc.md) is
**not edited**. It is historical implementer evidence for executable target `6f87abc`. Because this
correction creates a **new** executable target, a **new** rehearsal evidence artifact is created for
the corrected SHA and supersedes the old one **only as evidence for the corrected target**.

## 8. What is unchanged

No methodology change. No selector change. No quota change. No migration. No real-feasibility
change. No schema change, persisted or reported. No change to any accepted Decision 070–074 ruling,
all of which remain immutable and controlling. No limitation is closed. `m3.2-complete` is unmoved,
and no tag is created.

**Both real-path gates remain OPEN**, independently auditable, and never merged:

```text
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
REAL_ACCEPTANCE_ORDERING_ADEQUACY = PENDING FUTURE AUTHORIZED E0 VERIFICATION
```

**E0, E1, and E2 remain unauthorized.**

## 9. What this record does not authorize

It does **not**: authorize the real offline parse (**M3.3-E0**) or progression to **M3.3-E1** or
**M3.3-E2**; authorize a real snapshot, selection, manifest, or root; approve a root or begin
**M3.4**; enable network access; authorize an SEC request, reacquisition, or re-retrieval;
authorize a migration; authorize reading, resolving, or mutating `EV_ROOT`, the accepted real
private catalog, or any M3.2 private evidence; reopen any architecture or methodology conclusion
the ultrareview confirmed; close either real-path feasibility gate; supply **OR-6**, **OR-7**,
**OR-9**, or **OR-11**; pre-resolve Decision 023 **O1**; close any limitation; move
`m3.2-complete`; or create any tag.

**It is not an acceptance of the corrected target.** A passing correction, a green suite, a passing
E1–E8 rehearsal, a commit, or a push is **not** an ultrareview pass and **not** a Fable acceptance.

## 10. Next authorized action

Return to Sol/GPT. Sol/GPT will issue a **fresh read-only ultrareview-rereview** against the
corrected executable SHA. Only after that returns **B0 / M0 / MIN0** will Sol/GPT issue the fresh
independent formal-acceptance packet. **No E0.**

```text
M3_3_I_R_ULTRAREVIEW_BOUNDED_CORRECTION_READY_FOR_REREVIEW
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
```
