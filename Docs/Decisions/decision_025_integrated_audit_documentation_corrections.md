# Decision 025 — Integrated Audit Documentation Corrections and Independent Verification Handoff

**Date:** 2026-07-31
**Status:** ACCEPTED — OWNER APPROVED 2026-07-31
**Type:** Documentation-correction and verification-handoff decision. **Not** a preregistration
deviation; `Docs/preregistration.md` is unchanged by this record and was not edited. It changes no
schema, migration, database behaviour, production code, test, configuration, methodology, selection
rule, reserve rule, manifest rule, hash preimage, accepted decision outcome, or S4/S5/S6 behaviour.
**Supersedes:** nothing. **Amends:** nothing. Decisions 021, 022, 023, and 024 all remain `ACCEPTED`,
unchanged, and controlling for what they govern.
**Related:** [Decision 016](decision_016_m23_schema_and_artifact_architecture.md),
[Decision 019](decision_019_m23_s5_storage_to_pure_input_mapping.md),
[Decision 020](decision_020_m23_s5_4_reserve_architecture.md),
[Decision 021](decision_021_m23_s6_manifest_construction.md),
[Decision 022](decision_022_m23_s6_reserve_rank_applicability.md),
[Decision 023](decision_023_m23_s6_acceptance_and_path_ratification.md),
[Decision 024](decision_024_m2_m3_boundary_governance.md); `Docs/preregistration.md` §25.
**Governs:** the bounded documentation corrections the final integrated audit required, and the
handoff to fresh independent verification.

---

## 1. Why this record exists

The final independent integrated audit of Milestones 1 and 2 returned:

```
REQUIRES_BOUNDED_INTEGRATED_FIXES
```

It found **no** implementation, methodology, migration, hashing, selection, manifest, leakage,
security, or test defect. What it found was one bounded documentation defect, one navigation gap,
and one independence disclosure. This record accepts those findings, authorizes the corrections, and
fixes the sequence that follows.

## 2. The audit's confirmed classifications

Integrated acceptance was confirmed in every engineering and governance category:

| Category | Classification |
|---|---|
| Milestone 1 | `INTEGRATED_ACCEPTANCE_CONFIRMED` |
| Milestone 2.1 | `INTEGRATED_ACCEPTANCE_CONFIRMED` |
| Milestone 2.2 | `INTEGRATED_ACCEPTANCE_CONFIRMED` |
| Milestone 2.3 | `INTEGRATED_ACCEPTANCE_CONFIRMED` |
| Milestone 2 as an integrated system | `INTEGRATED_ACCEPTANCE_CONFIRMED` |
| Project governance | `INTEGRATED_ACCEPTANCE_CONFIRMED` |
| Project reproducibility | `INTEGRATED_ACCEPTANCE_CONFIRMED` |
| Project security and leakage | `INTEGRATED_ACCEPTANCE_CONFIRMED` |
| Project test adequacy | `INTEGRATED_ACCEPTANCE_CONFIRMED` |
| Milestone 3 boundary | `GOVERNANCE_READY_IMPLEMENTATION_NOT_AUTHORIZED` |

Supporting evidence the audit reproduced independently rather than inheriting: every manifest
component digest, `selection_result_sha256`, `root_manifest_sha256`, and `manifest_id` rebuilt from
persisted rows using column tuples transcribed from Decision 021's own text; all nine migration-`0013`
digests over a 10939-byte, 186-line region; the migration chain contiguous, idempotent on
reapplication, and foreign-key clean; the frozen cohort windows, cutoffs, and seed `20260725` exact,
with mirror divergence failing closed; and a clean Git history with no data, secret, or personal path
ever committed.

## 3. The one bounded classification

```
PROJECT_DOCUMENTATION_CLASSIFICATION: REQUIRES_BOUNDED_FIX
```

## 4. The documentation defect, stated exactly

`Docs/sec_data_dictionary.md` declared its scope as **"the operational SQLite catalog and the frozen
Parquet release tables"**, but documented only the earlier SEC-ingestion and census schema — that is,
migrations `0001`–`0008`. It carried **zero** references to any `pilot_*` table.

Omitted from a document whose declared scope covered them:

- the **twenty-one `pilot_*` tables introduced by migration `0009`**;
- the policy-reference rows added by migrations `0010` and `0011`;
- the **one further table** and four lifecycle triggers added by migration `0012`
  (`pilot_selection_entity_reasons`), bringing the catalog to **twenty-two `pilot_*` tables**;
- the **eight lifecycle and manifest triggers** added by migration `0013`.

**This was a documentation-currency defect, not a verification blocker.** The audit verified every
methodology, control, deviation, risk, and acceptance obligation from the migrations (which are
ground truth, byte-immutable, and provenance-tracked), the accepted decisions, the production code,
and the tests. Nothing was unverifiable for want of the dictionary. But a milestone should not close
with its own schema documentation describing less than half the schema it claims to describe.

## 5. The navigation defect

`Docs/preregistration.md` §25 is the project's **deviation register** — it states the fields every
deviation must record and currently holds one entry, **Deviation D001** (the Decision 010
cohort-assignment date-source rule, prospective and outcome-blind). The register exists and is
correct; live navigation simply did not point at it clearly enough for a reader to find it, and the
integrated audit had to locate it by search.

## 6. Authorized corrections

1. **Update `Docs/sec_data_dictionary.md`** so its title, version, status, and scope accurately
   describe the operational SQLite catalog **through migration `0013`**, adding detailed coverage of
   the pilot layer: every table with its migration, purpose, owning stage, primary key, identity
   columns, foreign keys, uniqueness constraints, material CHECK constraints, lifecycle and
   mutability rules, accepted writer, accepted reader or reconstruction path, digest contribution,
   and state class; the migration-`0012` and migration-`0013` trigger inventories; the S4/S5/S6
   boundary; the identity-versus-operational-envelope distinction; and a migration-to-dictionary
   coverage table for `0001`–`0013`. Existing M2.1/M2.2 material is preserved unchanged.
2. **Add deviation-register navigation** to `Docs/decision_index.md`.
3. **Add a pointer to `Docs/preregistration.md` §25** in CLAUDE.md's reading order.
4. **Update live status, registry, contract-index, and change-impact navigation** where the
   correction makes an existing statement incomplete.

**The dictionary must not redefine methodology or infer behaviour.** Migrations are the schema
ground truth; accepted decisions govern methodology and semantics; the dictionary describes and
cross-references them and defines nothing of its own.

## 7. What this correction does not change

Nothing in the following was touched, and nothing in it may be changed by a documentation session:

**schema; migrations; database behaviour; production code; tests; configuration; CI; methodology;
selection rules; reserve rules; manifest rules; hash preimages; accepted decision outcomes; and S4,
S5, or S6 behaviour.**

Also unchanged: `Docs/preregistration.md` itself, Decisions 021–024, and every completed contract.
The correction is documentation and governance recording only, and grants **no implementation
authority**.

## 8. The independence disclosure

The integrated auditor disclosed, unprompted, that **the same conversation had authored Decisions 023
and 024** and their governance edits. The project's own discipline — Decision 022 §9, Decision 023
§2, and Decision 024 §5.2 — holds that no reviewer may review work it wrote.

The owner records the following:

1. **This establishes no technical defect.** The audit's substantive findings rest on
   independently reproduced evidence — digests recomputed from persisted rows, migrations applied to
   a scratch catalog, Git history inspected directly — not on the auditor's own prior authorship.
2. **It does, however, prevent final closeout from resting solely on that session's governance
   assessment** of Decisions 023 and 024.
3. **A fresh session must independently verify them.** That session must not be the one that
   authored Decisions 023, 024, or 025, or these documentation corrections, and it may not inherit
   their conclusions.

Disclosing the limitation rather than absorbing it is the behaviour this project's review discipline
is designed to produce, and it is recorded here as such.

## 9. Required sequence

1. **Complete this bounded correction** and commit the correction checkpoint (§11).
2. **`FRESH_INDEPENDENT_INTEGRATED_CORRECTION_AND_GOVERNANCE_VERIFICATION`** — a fresh independent
   session verifies the corrected data dictionary against migrations `0001`–`0013`, the
   deviation-register navigation, Decisions 023, 024, and 025, that no implementation behaviour
   changed, and the integrated audit's decisive conclusions.
3. **Bounded fixes and rereview**, if that verification returns findings.
4. **Formal closeout of Milestones 1 and 2** — a separate governance-only session, **only after
   verification passes**. It controls the closeout tags; this record authorizes none.
5. **Milestone 3 planning** only after closeout, and Milestone 3 implementation only under
   Decision 024 §8's five entry conditions.

**Milestones 1 and 2 remain open until step 4 completes.**

## 10. Formal outcome

```
INTEGRATED_AUDIT_DOCUMENTATION_CORRECTIONS_AUTHORIZED
```

## 11. Checkpoint authorization

The project owner authorizes, for this correction and no other purpose:

1. **one documentation and governance commit**;
2. **one push to `origin/main`**.

**No tag is authorized.** `m2.3-s6-complete`, `m2.3-s5.4-complete`, and `m2.3-s5-complete` are
immutable and are never moved, replaced, or re-pointed. CLAUDE.md rule 13 applies independently.

## 12. No implementation authority

This record grants none. No Milestone 3 phase is authorized, no contract is created, no live SEC
access, real candidate snapshot, real pilot selection, real manifest construction, root approval, or
publication is permitted, and no accepted stage is reopened.

## 13. Reason

The engineering was found sound in every category the audit examined, and the one thing standing
between it and closeout was a document that had quietly fallen a milestone behind the schema it
described. That is worth fixing before closeout rather than after, because a data dictionary is read
by whoever arrives next — and the next arrival is Milestone 3, which will build live acquisition
against exactly the tables the dictionary had stopped describing. The deviation-register pointer is
smaller still, but the same argument applies: a register nobody can find is a register that stops
being used.

The independence disclosure is recorded rather than resolved here on purpose. A project that has
stopped an audit for a missing boundary record and referred a three-path scope gap rather than
absorbing it should not close two milestones on a governance assessment that its own rules say was
not independent. One focused review costs little and removes the last asterisk.

No deviation from Decisions 013–024 is made or implied. No transition metric and no final-test metric
has been viewed in connection with this record.
