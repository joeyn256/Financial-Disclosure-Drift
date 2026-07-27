# Decision 016 — M2.3 Schema and Artifact Architecture

**Date:** 2026-07-27
**Status:** Approved by project owner
**Type:** Implementation and provenance decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged by this record. No hypothesis, cohort window, maturity gate,
outcome definition, threshold, or seed is altered.
**Supersedes:** nothing in Decisions 001–015. Freezes the Stage S3 schema-and-artifact architecture
left open by `Docs/Decisions/decision_013_pilot_selection_mechanics.md` §2 (candidate storage) and
particularizes several design choices proposed only informally in the read-only S3 architecture
review dated 2026-07-27 (not itself a decision record). Where this record and that review disagree,
**this record controls**; the specific corrections are noted inline below.
**Governs:** Milestone 2.3, Stage S3 onward. **Authorizes no implementation.** Migration `0009`,
schema DDL, reason-code additions, selector code, and every schema/integrity/reconstruction test
remain unauthorized until a separate, explicit instruction.
**Related:** Decision 002 (primary-universe boundary), Decision 007 (canonical CIK identity),
Decision 008 (`inventory_*` tables, post-retrieval only), Decision 009 (raw-data governance, hashing
precedent), Decision 010 (cohort date-source rule), Decision 013 (pilot selection mechanics — as-of
cutoff, candidate storage boundary, selector policy, reserves and substitution, manifest hashing,
approval semantics), Decision 014 (evidence levels, SIC-family mapping, provisional cohort
assignment)

This record resolves the schema-and-artifact-architecture questions the read-only S3 review left
open for owner decision, and corrects three governance inconsistencies noted in that review's
verification section (see `Docs/Decisions/decision_002_primary_outcome.md`,
`Docs/Decisions/decision_013_pilot_selection_mechanics.md` §4, and
`Docs/Decisions/decision_registry.md`, each corrected alongside this record). Nothing here reads,
fits on, or is informed by any 2022–2026 outcome.

## 1. IDs and policy constants

- `snapshot_id`, `selection_run_id`, `reserve_package_id`, and `manifest_id` are full 64-character
  hexadecimal SHA-256 digests, **content-derived** — never random or database-assigned. This
  resolves the review's open question U-2 in favor of content-derived IDs, consistent with the
  `IndexPlan` hashing precedent (Decision 013 §7).
- **`snapshot_id` excludes the (random) `census_run_id`.** It derives instead from the coverage
  window (`coverage_start`, `coverage_end`, `as_of_date`, `include_open_quarter`,
  `coverage_policy_version`), the candidate/evidence/mapping policy versions, and a stable
  **input-observation-content hash** (a hash of the actual cited `census_source_observations`
  content, not the ingestion run that produced them). Two snapshots built from the same underlying
  observations under the same policy versions therefore carry the same `snapshot_id`, even if they
  were built by different census runs.
- Operational event IDs — `pilot_selection_run_events.event_id` and
  `pilot_projection_recovery_events.event_id` — **may be UUIDs**, because event identity is excluded
  from every deterministic hash (§8).
- The literal **24**-entity `CHECK` on `pilot_selection_runs` (feasible ⇒ `selected_entity_count =
  24`) is **kept**, resolving the review's open question U-3. A required test must assert that the
  Python pilot constants (`TOTAL_OPERATING + TOTAL_CONTROLS`, currently in `pilot.py`) sum to 24, so
  the schema-level literal and the code-level constants cannot silently diverge.
- **`PILOT_SELECTION_SEED` stays in `pilot.py` through Stage S4** and is pinned byte-for-byte by
  tests. It is **not** moved to `cohorts.py` — resolving the review's open question U-5. `cohorts.py`
  remains reserved for frozen *research* definitions (cohort windows, maturity gates, the primary
  outcome, thresholds, the bootstrap seed) per `CLAUDE.md` rule 3; the pilot selection seed is an
  engineering/provenance constant, not a research definition, and does not belong there.

## 2. Primary-universe and SIC rules

**`primary_universe_eligible` does not derive from SIC alone** (corrected 2026-07-27, fourth pass).
Per `Docs/Decisions/decision_002_primary_outcome.md`'s controlling rule, it is `true` **only** when
all of the following hold: (1) the entity is an eligible operating-company candidate, not a
boundary control; (2) required primary-universe classification evidence is sufficiently resolved;
(3) the entity's SIC is not in 6000–6999; and (4) no other Decision 002 primary-universe exclusion
applies.

- `primary_universe_eligible = false` for **all boundary controls**, regardless of SIC (condition 1
  alone excludes them): registered investment company/ETF, asset-backed issuer, shell/blank-check
  issuer, foreign-private-issuer annual-report filer.
- `primary_universe_eligible = false` for **SIC 6000–6999**, regardless of candidate category
  (condition 3 alone excludes them) — this is what makes the flag apply to the four
  operating-financial-institutions quota entities as well as the four boundary controls (eight
  total; see the corrected `Docs/Decisions/decision_002_primary_outcome.md`), for two independently
  sufficient reasons rather than one shared SIC-only rule.
- **Unresolved required universe evidence fails closed to `false`** (condition 2). A candidate with
  missing, stale, or conflicting required primary-universe classification evidence is never
  defaulted to eligible.
- **SIC 6712** (bank holding companies) may **provisionally** satisfy the operating-financial pilot
  industry quota (Decision 014 §4's engineering-only operating-financial stratum), but it is
  **engineering-only** and **primary-universe ineligible** regardless of quota satisfaction —
  quota eligibility and primary-universe eligibility are independent flags; satisfying one never
  implies the other.
- **SIC 6719, 6798, 3826, and 8731** are `review_required` and **cannot** satisfy an affirmative
  industry quota under any evidence level, consistent with Decision 014 §4's frozen
  `sic-family-mapping/0.2`.

## 3. Approved table family

Only the following tables are approved for Stage S3. No other pilot table name is authorized without
a further decision record. **No table in any group may reference any `inventory_*` table before
M2.5** — this applies to every table below without exception.

**Candidate:**

- `pilot_candidate_snapshots`
- `pilot_candidate_entities`
- `pilot_candidate_accessions`
- `pilot_candidate_accession_registrants`
- `pilot_candidate_entity_evidence`
- `pilot_candidate_accession_evidence`
- `pilot_candidate_entity_reasons`
- `pilot_candidate_accession_reasons`

**Selection:**

- `pilot_selection_runs`
- `pilot_selection_run_events`
- `pilot_selected_entities`
- `pilot_selected_entity_quota_contributions`
- `pilot_selected_accessions`
- `pilot_selected_accession_quota_contributions`
- `pilot_reserves`
- `pilot_reserve_accessions`
- `pilot_reserve_quota_contributions`
- `pilot_quota_results`
- `pilot_quota_result_members`

**Manifest:**

- `pilot_manifest_versions`
- `pilot_projection_recovery_events`

**Correction to the S3 review:** the review's recommendation (its U-4) to reuse the existing
`census_projection_recovery_events` table for pilot-manifest projection faults is **rejected**. A
**dedicated** `pilot_projection_recovery_events` table is required (§8), because a shared table
would let a pilot-manifest projection fault and a census-observation projection fault contend for
the same identifier space and detection logic that were designed around census semantics only.

**Correction to the S3 review:** the review's single-table-with-inline-evidence-columns design for
`pilot_candidate_entities`/`pilot_candidate_accessions` (e.g. `size_evidence_level`,
`size_source_observation_id` as direct columns) is **superseded** by the normalized
`pilot_candidate_entity_evidence` / `pilot_candidate_accession_evidence` tables in §4 below. The
candidate tables store only the **resolved** classification and its resolution hash; the full
evidence trail is normalized.

## 4. Evidence and reasons

- **Candidate evidence must be normalized**, one row per contributing observation, preserving:
  classification dimension (e.g. `size`, `industry`, `history`, `cohort`, `amendment_purpose`),
  evidence role (e.g. `primary`, `corroborating`, `conflicting`), source observation ID, parsed
  record ID, source field, the canonical observed value, the policy version under which it was
  read, precedence (per Decision 010 §4.1 / Decision 014 §7 where applicable), and a stable
  **evidence SHA-256** over those fields.
- **Candidate rows store resolved values and resolution hashes** — `pilot_candidate_entities` and
  `pilot_candidate_accessions` carry the resolved classification (e.g. `size_stratum`,
  `industry_family`, `provisional_official_cohort`) plus a `*_resolution_sha256` tying that
  resolved value back to the specific evidence rows in `pilot_candidate_entity_evidence` /
  `pilot_candidate_accession_evidence` that produced it. A resolved value with no supporting
  evidence row is not a valid candidate row.
- **Normalized entity/accession reason tables are authoritative.** `pilot_candidate_entity_reasons`
  and `pilot_candidate_accession_reasons` are foreign-key-constrained against
  `reference_reason_codes`, exactly as the review proposed.
- **`reason_codes_json` (where retained on any table, for cheap projection or continuity with the
  repository's existing convention) is never a second authoritative copy.** The normalized reason
  tables are the source of truth; any JSON mirror must be verifiably derivable from them, and a
  reconstruction test must assert the two agree. This corrects any reading of the S3 review that
  treated the JSON column and the normalized table as equally authoritative.

## 5. Lifecycle rules

### Snapshot

```
building ──▶ frozen ──▶ invalidated
   │                        ▲
   └────────────────────────┘
```

- `building → frozen`, `building → invalidated`, `frozen → invalidated` are the only permitted
  transitions.
- `invalidated` is **terminal**.
- **An invalidated, previously-frozen snapshot retains `frozen_at_utc`.** Invalidating a frozen
  snapshot is a fact about its later disposition, not an erasure of the fact that it was once
  frozen; `frozen_at_utc` is never cleared or overwritten on that transition.

### Selection run

```
planned ──▶ running ──▶ feasible
                   ├──▶ infeasible
                   ├──▶ infeasible_or_unproven
                   └──▶ failed ──▶ running   (explicit retry event only)
```

- `feasible`, `infeasible`, and `infeasible_or_unproven` are **terminal**.
- `failed` is **not** terminal: `failed → running` is permitted, but **only** through an explicit,
  recorded retry event in `pilot_selection_run_events` — never an implicit re-open. This corrects
  the S3 review's design, which treated all four non-`running` states as uniformly absorbing.

### Manifest

```
proposed ──▶ owner_approved ──▶ superseded
       └───▶ rejected                (terminal)
```

- `rejected` and `superseded` are **terminal**.
- **A superseded, previously-approved manifest retains its original approval fields**
  (`approval_reference`, `approved_root_sha256`, `approved_at_utc`) unchanged. Superseding an
  approved manifest records that a later manifest replaced it; it does not retract the historical
  fact that this one was approved, at that hash, at that time.

## 6. Integrity

- **Every result table must use a composite foreign key proving `selection_run_id` and
  `snapshot_id` refer to the same run/snapshot pair.** `pilot_selection_runs` carries a
  `UNIQUE (selection_run_id, snapshot_id)` constraint; every table that stores both columns
  (`pilot_selected_entities`, `pilot_selected_accessions`, `pilot_reserves`, `pilot_quota_results`,
  and their children) declares its foreign key against that composite unique, not against
  `selection_run_id` alone with an independently-checked `snapshot_id`. This prevents a
  `snapshot_id` value from silently drifting out of sync with its run.
- **Quotas use a `comparison_operator`** — `exact`, `at_least`, or `at_most` — rather than an
  implicit equality test. `pilot_quota_results.quota_result = 'pass'` is defined relative to
  whichever operator applies to that `quota_dimension`/`quota_key`, not by a single hard-coded
  `achieved_count = required_count` rule. This corrects the S3 review's `pilot_quota_results` design,
  which assumed exact-match quotas uniformly.
- **A partial unique anchor index enforces "at most one anchor" per candidate accession, but
  snapshot freeze must separately require "exactly one anchor" for every candidate accession.**
  The partial unique index alone cannot detect an accession with **zero** anchors; the freeze
  transition (Decision 013 §2, the transaction described in the S3 review §7 "Snapshot freezing")
  must include an explicit check that every `pilot_candidate_accession_registrants` group
  contributing to a frozen snapshot has exactly one `is_anchor = 1` row, and must refuse to freeze
  otherwise.
- The literal entity-count `CHECK` is **24** (§1).
- **Snapshot and manifest state constraints must be written as implications, not "iff"
  timestamp-equivalences.** Because an invalidated snapshot retains `frozen_at_utc` (§5) and a
  superseded manifest retains its approval fields (§5), a constraint of the shape
  `CHECK ((state = 'frozen') = (frozen_at_utc IS NOT NULL))` is **incorrect** — it would fail the
  moment a frozen snapshot is invalidated (state changes to `invalidated`, but `frozen_at_utc`
  remains set, so the biconditional breaks) or a manifest is superseded (state changes, but
  `approved_at_utc` remains set). The correct shape is a pair of one-directional implications, e.g.
  `CHECK (state <> 'building' OR frozen_at_utc IS NULL)` and
  `CHECK (state NOT IN ('frozen', 'invalidated') OR frozen_at_utc IS NOT NULL)` for the snapshot;
  and analogously `CHECK (state NOT IN ('owner_approved', 'superseded') OR approved_at_utc IS NOT
  NULL)` and `CHECK (state <> 'proposed' OR approved_at_utc IS NULL)` for the manifest. This
  corrects every equivalence-style `CHECK` proposed in the S3 review for these two tables.

## 7. Reserve packages

- **`pilot_reserves` represents a complete replacement package, not only a candidate issuer.** A
  reserve is identified by a content-derived `reserve_package_id` (§1) and a `reserve_rank`.
- **`pilot_reserve_accessions` stores the exact replacement accession bundle** the package would
  substitute in — every accession the reserve would contribute, with the same role fields
  (`base`/`stress`/`support`/`control`) as `pilot_selected_accessions`.
- **`pilot_reserve_quota_contributions` stores every quota contribution the package would make**,
  mirroring `pilot_selected_entity_quota_contributions` /
  `pilot_selected_accession_quota_contributions`.
- **The package signature** (`replaces_signature_sha256` / `reserve_signature_sha256` on
  `pilot_reserves`, per Decision 013 §6 as amended) covers: the signature and quota policy versions;
  entity role; control kind; size stratum; industry family; industry-quota eligibility; history
  class; the eventful-and-currently-inactive contribution; primary-universe eligibility; the
  name-change contribution; the support-pair contribution; the multi-registrant contribution; the
  XBRL-era (pre-Inline / Inline) contributions; the year/cohort (2024-original,
  2025/2026-original) contributions; the amendment-purpose contributions; the accession counts and
  roles the package supplies; and the evidence floor (the weakest evidence level across the
  package's quota-relevant classifications). This is the exact input list Decision 013 §6 requires
  and matches the S3 review §8, restated here as frozen policy rather than a recommendation.
- **Hash equality constraints are necessary but not sufficient.** A stored
  `reserve_signature_sha256 = replaces_signature_sha256` check proves the two *stored* hashes match;
  it does not by itself prove either hash was computed correctly from current content. **Acceptance
  tests must independently recompute both signatures from normalized source content** (not merely
  compare the two stored hash columns) and assert the recomputed values equal the stored ones and
  equal each other. A signature-computation defect that always emits the same (wrong) hash would
  pass a stored-hash-equality check but must be caught by recomputation.

## 8. Hash boundaries

- **Excluded from every deterministic hash, without exception:** absolute local paths; SEC identity
  (user-agent, contact address); secrets; any outcome value; any filing text; every free-text
  `detail` column; every **operational event ID** (`pilot_selection_run_events.event_id`,
  `pilot_projection_recovery_events.event_id`); and **every timestamp** column.
- **`retrieved_at_utc` is provenance-envelope data and does not enter the deterministic
  source-content hash.** This corrects the S3 review's layer-1 (source-observation) hash design,
  which included `retrieved_at_utc` in the hashed column list; it must be excluded, exactly like
  every other timestamp.
- **The source-content hash** (the layer feeding the candidate-table hash, per Decision 013 §7)
  includes exactly: the stable source ID, the request identity, the logical/decoded content hash
  (`logical_sha256`), the parser version, a **schema fingerprint** (a stable identifier for the
  structural shape the parser observed — e.g. derived from the relevant
  `census_structural_observations` region/state, so a schema-drift event changes the fingerprint),
  and the source outcome. No timestamp, header, redirect trace, or free-text detail enters it.
- **Candidate hashes include the normalized evidence and resolution hashes** from §4 — the
  evidence-table SHA-256 values and the candidate row's own resolution SHA-256 — not the raw
  evidence rows' timestamps or IDs.
- **`selected_order` and `reserve_rank` are materialized integer fields inside their respective
  hashed column lists** (the entity/accession table hash and the reserve table hash,
  respectively). This is unchanged from, and confirms, the S3 review's finding that `hash_table`
  sorts rendered rows before digesting, so any ordering that must survive into the frozen identity
  has to be an explicit hashed column, not implicit row order.
- **The serialized manifest JSON lives under the existing `releases/` tree** (`paths.py`'s
  `DataTree.releases`), resolving the review's open question U-7. No new top-level data directory is
  introduced.
- **Use the dedicated `pilot_projection_recovery_events` table** for pilot-manifest projection
  faults (§3), not `census_projection_recovery_events`.

## 9. Multi-registrant rule

- Build metadata-stage registrant evidence (`pilot_candidate_accession_registrants`,
  `pilot_candidate_accession_evidence`) **only from approved census observations** — the same
  approved M2.3 metadata sources every other candidate field draws from. No filing-body evidence,
  and no inference beyond what the census parser actually captured.
- **If the two required multi-registrant candidate accessions (Decision 013 §3) cannot be supported
  from authorized M2.3 metadata, the selector must report the multi-registrant quota as a binding
  constraint** in `pilot_quota_results` (with `eligible_pool_count` reflecting the true, possibly
  zero, count of qualifying candidates). **The quota is never silently deferred to M2.5, and no
  evidence is manufactured** to make it appear satisfiable. This confirms, as frozen policy, the S3
  review's recommendation on this point (its U-6).

## 10. Reason

Every rule above closes a specific gap the read-only S3 review either left open for an owner
decision or got wrong by proposing a plausible-but-incorrect mechanism (timestamp-equivalence
`CHECK`s that break under the retained-field lifecycle rules; a source-content hash that would have
included `retrieved_at_utc`; a single-authoritative-copy ambiguity between `reason_codes_json` and
normalized reason tables; reuse of a census-scoped recovery table for pilot-manifest faults). None
of these mechanics reads, fits on, or is informed by any 2022–2026 outcome; all are pre-registration
mechanical/provenance choices about how metadata-only candidates, selections, reserves, and
manifests are organized, hashed, and audited. This decision authorizes no schema, code, or test —
Stage S3 implementation remains gated on a separate, explicit instruction.
