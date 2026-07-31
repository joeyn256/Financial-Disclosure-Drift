# Decision 022 — M2.3 Stage S6 Reserve-Rank Applicability (crosswalk item 46)

**Date:** 2026-07-31
**Status:** ACCEPTED — OWNER APPROVED 2026-07-31
**Type:** Owner clarification of an accepted record. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged. No hypothesis, cohort window, maturity gate, outcome
definition, threshold, or seed is altered.
**Clarifies:** [Decision 021](decision_021_m23_s6_manifest_construction.md) §13.2.1 crosswalk item 46,
in its relation to Decision 021 §11.2 and item 70.
**Supersedes:** nothing. **Amends:** nothing. Decision 021 remains `ACCEPTED` and otherwise
unchanged; this record adds an applicability rule that Decision 021 left implicit, and changes no
crosswalk row, classification, count, preimage, digest, or SQL byte.
**Related:** [Decision 020](decision_020_m23_s5_4_reserve_architecture.md) §7.1 (no-compatible-reserve
ruling), §8.2 (migration `0012`), §13 (reason codes);
[Decision 013](decision_013_pilot_selection_mechanics.md) §6 (no discretionary substitution);
[Decision 016](decision_016_m23_schema_and_artifact_architecture.md) §8.
**Governs:** Milestone 2.3, Stage S6 onward.

---

## 1. Why this record exists

A fresh independent S6 implementation audit on 2026-07-31 confirmed that the earlier bounded
corrections work, and found one further conflict, recorded there as **N1**.

A lawful, accepted, terminal Stage-S5 run can exist in which **no selected target has a compatible
reserve package**:

- `run_state = 'feasible'`;
- the complete selected-entity set is persisted;
- `pilot_reserves` holds **zero rows** for the run;
- every selected target carries exactly one `pilot_selection_entity_reasons` row with
  `reason_scope = 'reserve'` and `reason_code = 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE'`.

This is not a degenerate or synthetic shape. It is the state Decision 020 §7.1 explicitly
contemplates — "**nonblocking** — the run still reaches `feasible`; §3 confirms a run with zero
reserves transitions successfully" — and migration `0012`'s disposition-completeness trigger accepts
it as a total and mutually exclusive reserve disposition state. The audit reproduced it directly from
the accepted Stage-S5.1 plan fixture, which thirty-four accepted S5 tests already rely on.

**The conflict.** Decision 021 §11.2 rules that `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` remains
nonblocking and that "a run carrying no-compatible-reserve dispositions is manifest-eligible". Such a
run therefore passes all seven §11.2 eligibility conditions and seals
`selection_result_sha256` normally. But Decision 021 §13.2.1 crosswalk **item 46 — "reserve rank"** —
is classified **D**, assigned to block 12, and rendered from `reserves.packages[].reserve_rank`. With
zero packages that leaf never exists, so the §12 item-by-item document verification finds item 46
uncovered and refuses the manifest with `GateFailureError`.

The result was that an eligible, sealed, accepted S5 run could not be manifested. The audit stopped
under Decision 021 §21 — "a §13.2.1 crosswalk item cannot be placed as classified" — and §13.3 —
"Adding, moving, or reclassifying a §10 item is an owner-level act" — and returned
`REQUIRES_OWNER_CLARIFICATION` rather than choosing a resolution. **That was the correct action**, and
this record supplies the ruling.

## 2. Frozen ruling — the owner's clarification, recorded verbatim

The project owner approves the following clarification on 2026-07-31.

1. **Crosswalk item 46 remains:** numbered 46; classified **D**; assigned to manifest block 12; and
   bound to the accepted reserve-package digest authority.
2. **Item 46's reserve-rank value is applicable once for each persisted compatible reserve package.**
3. **When a selected target has no compatible reserve package** and instead carries the persisted
   reason `REVIEW_PILOT_NO_COMPATIBLE_RESERVE`, the reserve-rank value for that target is
   **structurally not applicable**.
4. **Structural non-applicability under this ruling does not make a feasible S5 run
   manifest-ineligible.**
5. **Crosswalk item 70 remains the total reserve-coverage requirement.** Each selected target must be
   covered by exactly one of: one persisted rank-1 compatible reserve package; or one persisted
   `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition.
6. **A valid zero-package run is therefore manifest-eligible only when:** the selected-target set is
   complete; the reserve-package family is present and empty; every selected target has exactly one
   persisted disposition; every such disposition is `REVIEW_PILOT_NO_COMPATIBLE_RESERVE`; and there
   are no extra, duplicate, conflicting, or missing dispositions.
7. **Mixed runs remain valid.** Some selected targets may have rank-1 packages while other targets
   carry the no-compatible-reserve disposition.
8. **Do not create or serialize:** a synthetic reserve package; `reserve_rank = 0`;
   `reserve_rank = null`; `reserve_rank = "N/A"`; a placeholder package; or any invented reserve-rank
   value.
9. **This is an applicability clarification only.** It does not change the 81-item crosswalk, any item
   number, any classification total, item 46's digest binding, item 70, any S5 methodology, any hash
   preimage, any manifest identity, or migration SQL, and it introduces no Stage-S7 authority.
10. **This clarification is binding** and authorizes the bounded implementation described in §7.

## 3. Why resolution 1 was selected

Three resolutions were available to the owner. The first was chosen.

**Resolution 1 — rule reserve rank structurally not applicable for a target with no compatible
reserve (adopted).** It is the only one of the three that leaves every accepted record intact. It
changes no crosswalk row, no classification, no count, no preimage, and no migration byte; it
contradicts neither Decision 020 §7.1 nor Decision 021 §11.2; and it states in governance what the
data model already asserts structurally — a rank is a property *of a package*, and where the accepted
S5.4 methodology produced no package, there is no rank to record. The conflict was never a defect in
the reserve architecture or in the manifest hash contract. It was an omission in how §13.2.1 phrased a
per-package value as though it were a per-run one, and an applicability rule is the smallest correct
repair.

**Resolution 2 — make zero-package runs manifest-ineligible (rejected).** This was rejected because it
reverses two standing accepted rulings at once. Decision 020 §7.1 fixes the no-compatible-reserve
outcome as **nonblocking** and **target-specific, never a run-level state**, and Decision 021 §11.2
repeats that a run carrying such dispositions is manifest-eligible. Making the count of packages a
publication gate would convert a deliberately target-scoped, review-required annotation into a silent
run-level blocker, and would mean a pilot sample that is otherwise complete, feasible, and sealed
could never be presented to the owner for approval merely because no compatible replacement happened
to exist. It would also create a perverse incentive at M2.5: the cheapest way to make a run
publishable would be to find *some* reserve, which is exactly the discretionary substitution Decision
013 §6 forbids outright.

**Resolution 3 — invent a placeholder rank (rejected).** Serializing a synthetic package, a
`reserve_rank` of `0` or `null`, an `"N/A"` sentinel, or any other stand-in was rejected because it
would put a value into the manifest that no persisted row contains and no digest legitimately
commits. Decision 021 §13.3 forbids serializing a substantive field that no preimage binds, and
§13.2.1 is explicit that where §10 asks for records, "category T requires the values themselves; the
digest supplies the binding, not the content". A fabricated rank would also be indistinguishable, to a
later reader of the approved artifact, from a genuine rank-0 package — and the whole point of the
reserve family is that the owner can see *which* targets have no replacement. Clause 8 therefore
prohibits every form of it by name, so no implementation session can reach for one under pressure.

## 4. Why no crosswalk reclassification is required

Item 46 is **not** reclassified, renumbered, moved, or rebound. It stays **D**, stays in block 12, and
stays committed by `reserves_sha256` through the frozen §7.4 `pilot_reserves` column tuple, which
already names `reserve_rank`. The six frozen §13.2.1 counts are untouched:

```
total_section_10_items      = 81
directly_included    (D)    = 42
transitively_included(T)    = 30
operationally_excluded(X)   =  8
deferred_to_s9       (S9)   =  1
deferred_to_s10      (S10)  =  0
unclassified                =  0
```

What this record supplies is the **cardinality** of item 46, which §13.2.1 never stated: the value is
applicable **once per persisted reserve package**, not once per run and not once per selected target.
Under that reading the item is fully discharged in every run shape — by one rendered `reserve_rank`
per package where packages exist, and vacuously where the accepted methodology produced none. No
category could have expressed this, which is why the audit could not resolve it by choosing one: a
fifth category is forbidden by §13.2.1, and moving item 46 to **T** or **X** would have been a
reclassification the audit had no authority to make.

## 5. The relationship between item 46 and item 70

The two items are deliberately different obligations, and this record keeps them different.

| | Item 46 — reserve rank | Item 70 — reserve coverage |
|---|---|---|
| §10 group | Entity records | Quota report |
| Class | **D** | **D** |
| Block | 12 | 12 |
| Committed by | `reserves_sha256` names `reserve_rank` | `reserves_sha256` — the package or the disposition |
| Cardinality | **once per persisted reserve package** (this record) | **once per selected target** (unchanged) |
| Satisfiable by a disposition? | **No** — a disposition carries no rank | **Yes** — explicitly either/or |

Decision 021 already wrote item 70 with an explicit either/or: "the target's rank-1 package **or** its
`REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition". **Item 70 is therefore the total requirement and is
unchanged by this record.** Every selected target must still be covered, by exactly one of the two,
and a target with neither — or with both — remains a fail-closed condition. This record does not
relax coverage; it clarifies that *rank* is a property of the covering **package** and simply does not
exist on the covering **disposition**. Totality lives on item 70, where Decision 021 put it.

## 6. What this record does not change

Recorded so that no later session reads an applicability rule as a wider licence.

- **Decision 021 remains `ACCEPTED`** and is otherwise unchanged. Its §13.2.1 table, §15.1 SQL, §15.3
  digests, and all accepted text stand exactly as approved on 2026-07-30.
- **The 81-item crosswalk, every item number, and every classification total are unchanged.**
- **Every frozen digest preimage is unchanged** — §6.1, §§7.1–7.4, §§8.1–8.4, §9, §9.1. In particular
  `reserves_sha256` still hashes `pilot_reserves` at the frozen twelve-column tuple, which is why a
  zero-package family hashes as the empty row set: deterministic, and distinct from any populated one.
- **Manifest identity is unchanged** — `root_manifest_sha256` and `manifest_id` derive exactly as
  §9 and §9.1 fix them.
- **Canonicalization is unchanged** (§13.5), and every valid reserve-bearing manifest produces
  byte-identical component digests, `selection_result_sha256`, root, `manifest_id`, and canonical
  document bytes before and after this record.
- **Migration `0013` is unchanged** — byte-identical statement region, all nine §15.3 digests, all
  eight trigger definitions and their order.
- **No S5 methodology changes.** No second selector, contribution, reserve, role, cap, floor,
  evidence, amendment, or run-ID rule is introduced, and `reserve_selector.py`,
  `accession_selector.py`, `accession_selection_store.py`, `entity_selector.py`, and
  `entity_selection_store.py` are untouched.
- **No new reason code, policy constant, migration, CLI surface, or path** is authorized.
- **No Stage-S7, S8, S9, or S10 authority** is introduced. The S6 boundary of Decision 021 §17 stands.

## 7. Implementation consequences

This record authorizes a **strictly bounded** correction inside four already-authorized paths:
`release/pilot_manifest.py`, `sec/pilot_manifest_store.py`, `tests/unit/test_m23_pilot_manifest.py`,
and `tests/unit/test_m23_pilot_manifest_store.py`. Only the subset genuinely required may be touched.

The document-completeness verifier must distinguish **an applicable required record that is missing**
from **a reserve-rank record that is structurally not applicable because no package exists for that
target**. Applicability is derived from persisted state only — the `pilot_reserves` rows and the
reserve-scope `pilot_selection_entity_reasons` rows — never from a caller flag, a fixture parameter, a
runtime assumption, or a synthetic placeholder.

The following must hold, and §8 requires a test for each:

- every persisted reserve package carries exactly one valid `reserve_rank`, at the accepted rank
  value; a missing, duplicated, malformed, or invented rank fails closed;
- an unbound reserve-rank leaf fails closed;
- a target with **both** a package and a no-compatible-reserve disposition fails closed;
- a target with **neither** fails closed;
- duplicate packages for one target, duplicate dispositions for one target, an extra disposition, a
  missing disposition, and a substituted reason code each fail closed;
- **zero packages with complete `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` coverage is accepted**;
- **mixed package/disposition coverage is accepted**;
- reserve-bearing manifests are byte-for-byte unchanged.

**Item 46 does not become globally optional**, and the general rule that missing **D**/**T** content
fails closed is not weakened. Non-applicability is narrow, structural, and derived — it applies to the
reserve-rank value of a target the accepted S5.4 methodology gave no package, and to nothing else.

## 8. Test consequences

The audit also recorded **N2**: the S6 store fixture exposes a `with_reserve=False` path that no S6
store test exercises, which is why the zero-package boundary went unnoticed through the original
implementation, the first bounded test correction, the independent implementation review, and the
subsequent bounded correction. That dead capability must be exercised directly, so the boundary is
covered rather than merely reachable.

Required tests: a lawful zero-package run that constructs, seals, persists, verifies, and replays,
carrying no synthetic rank and a present-but-empty package family; missing, extra, duplicate, and
wrong-reason dispositions each failing closed; a target with both a package and a disposition, and a
target with neither, each failing closed; a mixed run succeeding end to end; item-46 completeness
proofs — removing or altering a rank on an existing package fails, an invented rank on a
disposition-only target fails, removing a package while leaving no disposition fails, and removing all
packages while retaining complete dispositions succeeds; and byte-identity of every hash, identity,
and canonical document for the existing reserve-bearing fixture. No test may be skipped, xfailed,
weakened, mocked past the public production boundary, or made vacuous.

## 9. Review requirement

**This record and the implementation it authorizes are not accepted by their own completion.** A
**fresh independent S6 rereview** must be run against the corrected tree, and the separate **final S6
acceptance review** must follow it. Neither may be performed by the session that recorded this
clarification or wrote the implementation, and neither may inherit that session's conclusion. Until
both pass, Stage S6 remains unaccepted, uncommitted, and untagged; the checkpoint boundary of
Decision 021 §22 — the new annotated tag `m2.3-s6-complete` supplementing the immutable
`m2.3-s5-complete` and `m2.3-s5.4-complete` — is unchanged, and CLAUDE.md rule 13 applies
independently.

## 10. Reason

The reserve architecture and the manifest hash contract were each correct, and each was independently
reviewed and approved. What was missing was a single sentence about how they meet: whether a value
defined on a reserve package is required to exist when the accepted methodology produced no package.
Left unstated, it made a lawful pilot sample unpublishable — the kind of defect that is cheap to fix
before any real data exists and expensive to discover during Stage S9 with a frozen snapshot in hand.
The audit found it, correctly declined to resolve it, and referred it. This record answers the
question in the narrowest way that leaves every accepted preimage, digest, count, and trigger exactly
where the owner approved them.

No deviation from Decisions 013–021 is made or implied. No transition metric and no final-test metric
has been viewed in connection with this record.
