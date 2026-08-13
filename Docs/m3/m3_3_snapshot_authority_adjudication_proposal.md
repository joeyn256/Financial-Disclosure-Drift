# M3.3 — Snapshot Authority Adjudication Proposal (OR-1 and OR-2)

```text
STATUS: PROPOSAL — OWNER-DISPOSED BY ACCEPTED DECISION 067 (2026-08-13) —
        HISTORICAL PROPOSAL EVIDENCE, NO AUTHORITY
```

> ## Owner disposition — read this before any table below
>
> **The owner ruled on 2026-08-13. Accepted
> [Decision 067](../Decisions/decision_067_m3_3_snapshot_authority_and_offline_parse.md) is the
> authority; this document is not, and never was.** The rulings are recorded in that decision and in
> the corrected [M3.3 contract](../../Milestones/contracts/m3_3.md) §§8.1, 10.1, 10.2. **A session
> cites Decision 067 or the contract — never this proposal — as the reason for anything.**
>
> **This document is preserved as historical proposal evidence and is not rewritten as though it had
> always been authority.** Its body below is the text as proposed. Where the owner corrected a
> proposition, an annotation marks the correction **without** editing the historical claim.
>
> | Proposal item | Owner disposition |
> |---|---|
> | **§§A–C** — the eleven-digest preimage matrix | **ADOPTED as the normative OR-1 basis**, subject to every correction below — Decision 067 §9 |
> | **§§D–F** — the 135-column source→candidate mapping | **ADOPTED as the normative OR-2 basis**, subject to eight mandatory GV2 corrections — Decision 067 §10 |
> | **§A.2.1** — `input_observation_set_sha256` ≡ `source_observation_set_sha256` | **ADOPTED.** Definitionally identical, computed twice and required to agree, fail-closed on mismatch |
> | **§A.12** — `evidence_sha256` call shape and the eight resolution digests | **ADOPTED and expanded into OR-1** — Ruling **R16**, Decision 067 §7 |
> | **OQ-1** — is the parse layer populated? | **ANSWERED: it is EMPTY.** Ruling **R13** makes a bounded **offline metadata parse** the prerequisite — option (a), under a complete prohibition list — rather than a fail-closed refusal. Real execution is separately gated at **M3.3-E0** |
> | **OQ-2** — uniformly empty `schema_fingerprint_sha256` | **ANSWERED: not acceptable on that basis.** Ruling **R14** — the parse must precede snapshot construction; only a *legitimate* zero-row parse result may use the empty-row-set digest |
> | **OQ-3** — same-catalog `snapshot_id` collision | **ANSWERED: FAIL CLOSED.** Never `INSERT OR REPLACE`, `INSERT OR IGNORE`, or a silent recognize-and-return |
> | **OQ-4** — parent-key convention | **ANSWERED: this proposal's line.** `snapshot_id` **excluded** from the seven family digests |
> | **OQ-5** — `source_observation_id` / `parsed_record_id` inside `evidence_sha256` | **ANSWERED: ALT-3 — retained.** Ruling **R15**, on the corrected premise **GR-C2** below |
> | **OQ-6** — `coverage_policy_version` | **ANSWERED: `pilot-coverage/1.0`.** Its executable home remains an open implementation-packet path question — contract §20 |
> | **OQ-7** — widen OR-1 to the §A.12 families? | **ANSWERED: yes, widened** — Ruling **R16** |
> | **OQ-8** — evidence-role vocabulary | **ANSWERED: `winning` / `competing` / `supporting`**, migration `0009`'s vocabulary. Decision 016 §4's wording is illustrative and historical |
>
> **Two propositions in this document are CORRECTED and must not be relied on.**
>
> - **GR-C1** — *"parsing is coupled to retrieval and cannot be run offline over stored objects"* is
>   **overstated**. Retrieval and parsing are coupled **only at the orchestration entry points**; the
>   parsers operate on already-materialized stored content, and payload loading, archive traversal,
>   and `CensusCatalog` persistence are **already offline-capable**. The missing capability is an
>   **offline entry point / driver** (Decision 067 §3.1).
> - **GR-C2** — *"an identical re-retrieval **or** reparse changes candidate evidence identities"* is
>   **wrong on the reparse branch**. A reparse of the **same** accepted observation row is
>   **deterministic**; only **re-retrieval** creates a new uuid4 `source_observation_id`. M3.3 forbids
>   reacquisition, so only the deterministic branch is reachable (Decision 067 §3.2).
>
> **What did not change.** This document still authorizes nothing, freezes nothing, and closes no
> limitation. **D021-L2 remains `ACTIVE`** — OR-1 being ruled supplies the missing derivation but does
> not close the entry, which needs the implemented recomputation-and-comparison step, reviewed.
> **Decision 067 is a governance authority record and is not implementation authorization**; the
> corrected contract is **not accepted**, and no M3.3 work may begin.

---

**Date:** 2026-08-13
**Produced under:** the owner's M3.3-GR governance packet of 2026-08-13, which authorized preparing
an exact, mechanically reviewable proposal for **OR-1** and **OR-2** and **expressly forbade**
deciding either. **This document decides nothing.**

**What this is.** A field-by-field and digest-by-digest proposal the owner can accept, amend, or
reject. Every entry cites the accepted record it derives from, or states explicitly that no accepted
record fixes it.

**What this is not.** Not an authority. It approves nothing, freezes nothing, closes no limitation,
and authorizes no implementation. Where it and a decision record, a migration, or a module disagree,
the decision, migration, or module controls (CLAUDE.md authority rules). **OR-1 and OR-2 remain
unresolved until the owner rules.**

> **Historical as at 2026-08-13.** The owner has since ruled; see the disposition block above. The
> paragraph immediately above states the position as at this document's own production, and is
> deliberately left byte-unchanged.

**Executive finding, stated first because it conditions everything below.** Section G records a
repository-verified fact that bounds the whole of OR-2: **no code path authorized or executed under
Milestone 3.2 writes the census *parse* layer.** `census_parser_runs`, `census_parsed_records`,
`census_structural_observations`, `census_accessions`, `census_accession_observations`,
`census_registrants`, `census_registrant_observations`,
`census_accession_field_resolutions`, `census_accession_cohort_resolutions`, and
`census_index_instances` are written only by `sec/census.py` and `sec/census_orchestrator.py`, whose
sole entry point is the **network-gated** `sec census` command, and whose parse step is coupled to
retrieval. M3.2A's acquisition path (`m3/acquisition.py` → `sec/observation_catalog.py`) writes
`census_source_observations`, `census_observation_reasons`, and `census_archive_members` and nothing
else in the census family. **Unless the owner rules otherwise, the substantive source tables the
candidate builder would read do not exist in populated form**, and the majority of the OR-2 matrix is
`UNAVAILABLE / FAIL CLOSED`. This is **OQ-1**, and it is the largest open question in this document.

> **CORRECTED — GR-C1, and OQ-1 ANSWERED (accepted Decision 067 §§3.1, 4).** The finding that the
> parse layer is unwritten is **confirmed**: M3.3-GV2 verified it **empty**, with `parser_state`
> `not_started` for all 76 plan sources. But *"whose parse step is coupled to retrieval"* overstates
> the coupling — it holds **only at the orchestration entry points**. The parsers are **pure over
> already-materialized content**, and loading, archive traversal, and `CensusCatalog` persistence are
> **already offline-capable**; what is missing is an **offline entry point / driver**. The owner
> therefore ruled **option (a)**: a bounded, network-free **offline metadata parse** over the
> already-stored objects (**R13**), after which those columns become available. **The OR-2 matrix is
> therefore not permanently `UNAVAILABLE / FAIL CLOSED`.** Real execution is separately gated at
> **M3.3-E0**.

---

## 0. Method, and the boundaries this proposal was prepared inside

**Frozen boundaries observed** (owner packet §5): no network; no reacquisition; no new parsing of
filing bodies; no CompanyFacts; no Frames; no outcome data; no S4 draft as input; no pilot membership
as an input feature; no `inventory_*` authority (migration `0009`'s header and Decision 013 §2
prohibit any `inventory_*` reference before M2.5, and nothing below references one).

**What was read to produce this:** migration `0009` (the eight candidate tables, verbatim column
lists and `CHECK`s); migrations `0002`, `0003`, `0005`, `0006`, `0008` (the census source and parse
families); `release/hashing.py`; Decisions 010, 013, 014, 016, 018, 019, 021, 023; and the
`src/disclosure_drift/` call graph for every writer of every census table named above.

**What was *not* read, and could not be:** any real catalog, any private evidence, any real
observation row. Every statement about the *real* corpus below is derived from repository code and
from `Milestones/STATUS.md`, and is flagged as requiring owner verification against the private
evidence before it is relied upon.

**Non-vacuity discipline.** Sections E and F trace in both directions — every candidate field back to
an accepted M3.2 source, and every accepted M3.2 source family forward to its use — so that a field
with no source and a source with no use are both visible rather than inferred.

---

## A. OR-1 — proposed digest and preimage matrix

### A.0 Common mechanics — proposed for every digest in this section

| Aspect | Proposed rule | Authority |
|---|---|---|
| Primitive | `release/hashing.py` `hash_table(...).normalized_content_sha256`, unmodified | D021 §5; D013 §7; packet constraint A |
| Second implementation | **None.** No parallel normalization, no alternative encoder, no re-implementation of `normalize_value` | D021 §5 |
| Multi-row call shape | `hash_table(<name>, <frozen ordered column tuple>, rows)` — column order normative, rows sorted after rendering by the primitive | D021 §5 |
| Single-row call shape | `hash_table(<name>, tuple(sorted(fields)), [fields])` | D021 §5 |
| NULL behavior | `NULL_SENTINEL` (`"\x00null"`); a SQL `NULL` never collapses into `""` | `hashing.py`; D021 §5 |
| Normalization | `normalize_value` only: `bool`→`1`/`0`; `int`→decimal; `float`→`repr(round(v,12))`; `date`→ISO; naive `datetime` refused; `str` verbatim | `hashing.py` |
| Universal exclusions | Absolute paths; SEC identity; secrets; any outcome value; any filing text; every free-text `detail`; every operational event ID; **every timestamp column** | D016 §8; D021 §5 |
| Deliberate inclusion | `acceptance_audit_date` — a calendar date and a frozen classification input, not a timestamp | D019 §10; D021 §5 |
| Physical bytes | **Never an input.** Every digest is a logical row-content digest; no SQLite page layout, file byte, library version, path, or filename enters any of them | packet constraint D; inventory CF5 |
| Approval / publication state | Never an input, at any layer | D021 §§6.3, 9, 13.4 |
| Hex form | Lowercase 64-character SHA-256, as migration `0009`'s `CHECK`s require | `0009` |

**Proposed parent-key convention, and the precedent split it resolves.** Accepted precedent points
two ways. D021 §7.1/§7.2 **include** `selection_run_id` and `snapshot_id` in the selected-entity and
selected-accession family tuples. D021 §8.1 **excludes** the parent `source_observation_id` from
`census_structural_observation_shape` — "the parent is the scoping key, not content" — and D019
§6.6.1 **excludes** `snapshot_id` and `accession_plain` from the registrant-content digest because
they "are constant within one accession's row set and would add nothing".

**This proposal follows the §8.1 / §6.6.1 line for the seven candidate-family digests**: `snapshot_id`
is the scoping key of the row set, is constant across it, and is bound **exactly once** — in
`candidate_snapshot_sha256` (§A.11) — and again by D021 §8.2's `candidate_tables_sha256`, which
already carries `snapshot_id` alongside all nine declared digests. Excluding it also removes an
ordering constraint on the builder. **The §7.1 counter-precedent is real and the owner may prefer
it**; see **OQ-4**.

---

### A.1 `coverage_window_sha256`

| Attribute | Proposal |
|---|---|
| Digest field | `pilot_candidate_snapshots.coverage_window_sha256` |
| `hash_table` name | `pilot_candidate_coverage_window` |
| Call shape | Single-row |
| Field set (sorted by key, as the shape requires) | `as_of_date`, `coverage_end`, `coverage_policy_version`, `coverage_start`, `include_open_quarter` |
| Source of every field | Caller-supplied run inputs, echoed into the row's own columns of the same names. `coverage_start` / `coverage_end` / `as_of_date` from the frozen coverage window (D013 §1: coverage 2009-01-01 → 2026-06-30, as-of `2026-06-30`); `include_open_quarter` the literal `0`, forced by `0009`'s `CHECK (include_open_quarter = 0)`; `coverage_policy_version` — **see OQ-6, no accepted value source exists** |
| Sort / key behavior | Single row; `tuple(sorted(fields))` fixes column order deterministically without a hand-frozen order |
| NULL behavior | No field is nullable at this layer; a `NULL` would render as `NULL_SENTINEL` and is a fail-closed condition, not a silent value |
| Normalization | `include_open_quarter` is stored `INTEGER` and renders `0`; dates render as stored `TEXT` (`YYYY-MM-DD`) |
| Included | The five fields above, and nothing else |
| Excluded | `census_run_id`; every timestamp; `detail`; every content digest; every count; `snapshot_state` |
| Transitive commitments | None — this is a leaf digest |
| Governing authority | D016 §1 names exactly this five-field parenthetical as "the coverage window"; D016 §8 supplies the exclusions |
| Circularity | **None.** Depends on caller inputs only |
| Collision / equivalence | Two runs over the same window under the same coverage policy produce the same value; any change to any of the five changes it |
| Two independent builds | **Identical**, unconditionally |
| Run IDs / observation IDs / timestamps / bytes / paths / approval / publication | **Cannot affect it** — none is an input |
| Recomputation at freeze | Recompute from the persisted row's own five columns; compare; `GateFailureError` on difference |
| Verification at rehearsal | E1 asserts equality after a clean rebuild; a one-field perturbation fixture per field asserts the digest moves |

---

### A.2 `input_observation_set_sha256`

**This is the entry whose relationship to Decision 021 §8.1 the owner packet §6 constraint G requires
to be settled, and it is settled here as a proposal, not a ruling.**

| Attribute | Proposal |
|---|---|
| Digest field | `pilot_candidate_snapshots.input_observation_set_sha256` |
| `hash_table` name | `census_source_observation_content` — **the identical name, column tuple, and row construction Decision 021 §8.1 already freezes** |
| Call shape | Multi-row |
| Frozen ordered column tuple | `("source_id", "request_identity", "logical_sha256", "parser_version", "schema_fingerprint_sha256", "outcome")` |
| Source of every field | `census_source_observations`, one row per **cited** observation; `schema_fingerprint_sha256` derived per D021 §8.1's frozen five-column partition rule over `census_structural_observations` |
| Row set | The **cited observation set**: the distinct union of `source_observation_id` over `pilot_candidate_entity_evidence` and `pilot_candidate_accession_evidence` for this snapshot |
| Sort / key behavior | `hash_table` sorts rendered rows; distinctness is on `source_observation_id` **before** rendering, so a repeated citation is a no-op |
| NULL behavior | `logical_sha256`, `parser_version`, and `schema_fingerprint_sha256`'s inputs are nullable in the source schema; `NULL_SENTINEL` preserves the distinction |
| Normalization | `normalize_value` only |
| Included | Exactly the six columns above |
| Excluded | The **29** other `census_source_observations` columns — 34 columns in the table, of which 5 are hashed directly and `schema_fingerprint_sha256` is derived rather than stored — per D021 §8.1's complete classification: `observation_id`, `supersedes_observation_id`, `reused_observation_id`, `attempts`, `retrieved_at_utc`, `recorded_at_utc`, `requested_url`, `final_url`, `redirects_json`, `redirect_hops_json`, `etag`, `last_modified`, `validators_sent_json`, `headers_json`, `transport_sha256`, `stored_sha256`, `content_sha256`, `transport_size_bytes`, `content_size_bytes`, `stored_size_bytes`, `storage_representation`, `relative_storage_path`, `detail`, `projected_to_audit`, `purpose`, `http_status`, `declared_content_type`, `observed_content_kind`, `content_encoding` |
| Transitive commitments | The structural shape of every cited observation, through `schema_fingerprint_sha256`; `parser_run_id` is the partition key and is **not** hashed |
| Governing authority | D016 §1 ("a hash of the actual cited `census_source_observations` content"); D016 §8 (the source-content hash list); D021 §8.1 (the exact tuple and the fingerprint rule) |
| Circularity | **None** — see §B.1 for the full argument. It hashes *census* content, never a `pilot_candidate_*` digest |
| Collision / equivalence | Two retrievals of identical content under the same request identity hash identically, by design (D021 §8.1's rationale for excluding `observation_id`) |
| Two independent builds | **Identical**, provided the cited set is identical |
| Random run IDs / observation IDs / timestamps / bytes / paths / approval / publication | **Cannot affect it** |
| Recomputation at freeze | Recompute from the persisted evidence rows' distinct `source_observation_id` set joined to `census_source_observations`; compare to the column stored at `INSERT`; **`GateFailureError` on difference** |
| Verification at rehearsal | E1 and E2 |

#### A.2.1 The G question — proposed answer: **definitionally identical**

**Proposal: `input_observation_set_sha256` and Decision 021 §8.1's `source_observation_set_sha256`
are the same digest, over the same preimage, and must be equal for any frozen snapshot.**

They are **not** assumed identical because the names resemble each other. The argument is:

1. **Same declared content.** D016 §1 defines `input_observation_set_sha256` as a hash of the actual
   **cited** `census_source_observations` content. D021 §8.1 defines the **cited observation set** and
   the exact preimage over it. Both are "the content of the observations this snapshot cites".
2. **Same authority for the column list.** D021 §8.1's tuple *is* D016 §8's source-content hash list.
   D016 §1 names no different list. There is no second accepted definition to be faithful to.
3. **Two digests over the same declared content would be exactly the "competing definitions" the
   packet §6 constraint G warns against.** If they differed only in preimage, one of them would be
   an unauthorized second derivation of the same fact.

**The timing objection, and how it is discharged.** §8.1's set is derived from `pilot_candidate_*`
evidence rows, which exist only after the snapshot row; migration `0009` requires the column from
`INSERT` onward, because `snapshot_id` depends on it. The objection is about *when the value is
known*, not about *what it is*. It is discharged by the builder's obligation, which this proposal
makes explicit and which Owner Ruling **R5** already requires operationally:

- The builder **completes its whole deterministic derivation in memory first**, producing the exact
  set of evidence rows it will write, and therefore the exact cited-observation set `S`.
- It computes `input_observation_set_sha256` over `S` **before** the `INSERT`, which is what lets
  `snapshot_id` be fixed at row creation.
- Inside the **same** authoritative transaction (R5), after the child rows are written, it
  **recomputes** the digest from the persisted evidence rows and **requires exact equality**.
- **Any difference is a `GateFailureError` and rolls back the whole transaction** (R5). A snapshot
  whose stored `input_observation_set_sha256` does not equal the digest recomputed from its own
  persisted evidence cannot exist.

That validation is **non-vacuous**: a builder that cites an observation it did not plan to cite, or
plans one it does not cite, fails closed rather than freezing an inconsistent identity. It is also
exactly what makes the digest **independently recomputable from the final persisted candidate
evidence**, which the packet §6 constraint G requires of an identity proposal.

**Consequence the owner should weigh (OQ-2).** Because `census_structural_observations` is written
only by the parse layer (§G), every cited observation in the real corpus would contribute the
**empty-row-set fingerprint** — which §8.1 expressly permits ("An observation with no structural rows
contributes the digest of the empty row set — deterministic, and distinct from any populated shape")
but which leaves `schema_fingerprint_sha256` constant across all observations and therefore carrying
**no discriminating power** in the real run. The five-column tuple's four guaranteed properties still
hold; they are simply uninformative. This is a real-corpus consequence, not a design defect, and the
owner should decide whether it is acceptable at M3.3B.

---

### A.3 `snapshot_id`

| Attribute | Proposal |
|---|---|
| Digest field | `pilot_candidate_snapshots.snapshot_id` (PRIMARY KEY) |
| `hash_table` name | `pilot_candidate_snapshot_identity` |
| Call shape | Single-row |
| Field set (sorted by key) | `candidate_policy_version`, `coverage_window_sha256`, `evidence_policy_version`, `input_observation_set_sha256`, `sic_family_mapping_version` |
| Source of every field | `coverage_window_sha256` from §A.1; `input_observation_set_sha256` from §A.2; the three policy versions from `pilot_policy.py` — `PILOT_CANDIDATE_POLICY_VERSION` (`"pilot-candidate/1.0"`), `PILOT_EVIDENCE_POLICY_VERSION` (`"pilot-evidence/1.0"`), `SIC_FAMILY_MAPPING_VERSION` (`"sic-family-mapping/0.2"`) |
| Sort / key behavior | Single row, keys sorted |
| NULL behavior | No field may be `NULL`; a `NULL` is a fail-closed condition |
| Normalization | All five are strings |
| Included | Exactly those five |
| Excluded | **`census_run_id`** (D016 §1, explicitly); every timestamp; `detail`; `snapshot_state`; both counts; every one of the eight later content digests; every path; approval and publication state |
| Transitive commitments | The five coverage-window fields, through `coverage_window_sha256`; the whole cited-observation content set and its structural shapes, through `input_observation_set_sha256` |
| Governing authority | D016 §1, which names exactly these inputs: the coverage window, the candidate/evidence/mapping policy versions, and a stable input-observation-content hash |
| Circularity | **None.** Both digest inputs are computed strictly earlier; no candidate-family digest is an input |
| Collision / equivalence | **Satisfies D016 §1's required property exactly**: same cited observations + same coverage and policies ⇒ same `snapshot_id`, whatever `census_run_id` was |
| Two independent builds | **Identical** |
| Random run IDs / observation IDs / timestamps / bytes / paths / approval / publication | **Cannot affect it** |
| Recomputation at freeze | Recompute from the persisted row's own five inputs — each of which is itself recomputed first (§A.1, §A.2) — and compare to the stored primary key |
| Verification at rehearsal | E1's "identical `snapshot_id` from identical inputs"; a `census_run_id`-only perturbation fixture must leave it unchanged |

**Operational consequence the owner must rule on (OQ-3).** `snapshot_id` is the PRIMARY KEY. The
D016 §1 property therefore means a second build from identical content in the **same** catalog
collides on insert. Rehearsal E1's "identical `snapshot_id` from identical inputs" is satisfiable only
across **separate data roots**, and in one catalog the correct production behaviour is a **fail-closed
refusal** (never `INSERT OR REPLACE`, never `INSERT OR IGNORE`, never a silent no-op that returns the
existing snapshot as though newly built). Which of *refuse* or *recognize-and-return* the owner wants
is not derivable from any accepted record.

---

### A.4–A.10 The seven `candidate_*_sha256` family digests

All seven share the mechanics in §A.0. Each is a **multi-row** `hash_table` over that family's rows
**scoped to this `snapshot_id`**, computed inside the authoritative transaction after the rows are
written and before the `building -> frozen` transition.

Common to all seven:

- **Excluded from every one:** `snapshot_id` (§A.0 convention, **OQ-4**); `recorded_at_utc` (timestamp,
  D016 §8); `detail` (free text, D016 §8); `evidence_id` (row identity, not content — D016 §8's
  "not the raw evidence rows' timestamps or IDs").
- **Circularity:** none. No family digest is an input to another; none is an input to `snapshot_id`.
- **Two independent builds:** identical, given identical rows.
- **Random run IDs, physical bytes, paths, approval state, publication state:** cannot affect any of
  them — none is an input.
- **Recomputation at freeze:** recompute from persisted rows; compare to the value about to be
  written; `GateFailureError` on difference. **Recomputation at read/verify time:** identical query,
  identical tuple.

| # | Digest | `hash_table` name | Proposed frozen ordered column tuple | Row scope |
|---|---|---|---|---|
| A.4 | `candidate_entity_table_sha256` | `pilot_candidate_entities` | `("cik_numeric", "cik_padded", "entity_tie_break_sha256", "candidate_category", "control_kind", "size_stratum", "size_evidence_level", "size_resolution_sha256", "sic_code", "industry_family", "industry_quota_eligible", "industry_evidence_level", "industry_resolution_sha256", "history_class", "history_evidence_level", "history_resolution_sha256", "currently_inactive", "eligible_original_annual_report_count", "primary_universe_eligible", "primary_universe_evidence_level", "primary_universe_resolution_sha256", "engineering_only_stress", "filing_time_name")` | every entity row for the snapshot |
| A.5 | `candidate_accession_table_sha256` | `pilot_candidate_accessions` | `("accession_plain", "accession_number_dashed", "accession_tie_break_sha256", "anchor_cik_numeric", "form_type", "is_amendment", "official_filing_date", "report_date", "acceptance_audit_date", "filing_date_evidence_level", "filing_date_resolution_sha256", "filing_date_precedence", "provisional_official_cohort", "acceptance_audit_cohort", "cohort_evidence_level", "cohort_resolution_sha256", "cohort_ambiguous", "has_xbrl", "has_inline_xbrl", "xbrl_evidence_level", "xbrl_resolution_sha256", "amendment_linkage_state", "provisional_parent_accession", "amendment_purpose_category", "amendment_purpose_evidence_level", "amendment_purpose_resolution_sha256", "amendment_purpose_quota_eligible", "base_eligible", "stress_eligible", "support_eligible", "control_eligible", "multi_registrant")` | every accession row |
| A.6 | `candidate_registrant_table_sha256` | `pilot_candidate_accession_registrants` | `("accession_plain", "registrant_cik_numeric", "registrant_cik_padded", "role", "is_anchor", "evidence_level")` | every registrant row |
| A.7 | `candidate_entity_evidence_sha256` | `pilot_candidate_entity_evidence` | `("cik_numeric", "classification_dimension", "evidence_role", "source_field", "canonical_observed_value", "policy_version", "precedence", "evidence_sha256")` | every entity-evidence row |
| A.8 | `candidate_accession_evidence_sha256` | `pilot_candidate_accession_evidence` | `("accession_plain", "classification_dimension", "evidence_role", "source_field", "canonical_observed_value", "policy_version", "precedence", "evidence_sha256")` | every accession-evidence row |
| A.9 | `candidate_entity_reasons_sha256` | `pilot_candidate_entity_reasons` | `("cik_numeric", "reason_scope", "reason_code")` | every entity-reason row |
| A.10 | `candidate_accession_reasons_sha256` | `pilot_candidate_accession_reasons` | `("accession_plain", "reason_scope", "reason_code")` | every accession-reason row |

**Per-family notes, and the constraint-H dispositions the packet requires.**

| Field named by packet §6 constraint H | Disposition | Reason |
|---|---|---|
| `snapshot_id` | **EXCLUDED** from all seven; **INCLUDED once** in `candidate_snapshot_sha256` | §A.0 convention; D021 §8.1 "the parent is the scoping key, not content"; D019 §6.6.1 "constant … would add nothing". **OQ-4** |
| `census_run_id` | **EXCLUDED everywhere**, at every layer | D016 §1; D021 §8.2 |
| `source_observation_id` | **EXCLUDED from the direct tuples; TRANSITIVELY INCLUDED** through `evidence_sha256` | D016 §4 places it inside the evidence digest; D016 §8 keeps raw evidence-row IDs out of candidate hashes. **OQ-5** |
| `parsed_record_id` | **EXCLUDED from the direct tuples; TRANSITIVELY INCLUDED** through `evidence_sha256` | identical reasoning; D019 §10 independently requires it inside candidate content identity. **OQ-5** |
| `evidence_id` | **EXCLUDED, at every layer** | Row identity, not content; not in D016 §1's content-derived-ID list; excluding it removes a random-ID contamination channel |
| `evidence_sha256` | **INCLUDED** in A.7 and A.8 | D016 §8: candidate hashes include the evidence-table SHA-256 values |
| `*_resolution_sha256` (all **eight** columns — four on entities, four on accessions) | **INCLUDED** in A.4 / A.5 | D016 §8: candidate hashes include "the candidate row's own resolution SHA-256" |
| `recorded_at_utc` | **EXCLUDED, at every layer** | D016 §8 — every timestamp |
| `detail` | **EXCLUDED, at every layer** | D016 §8 — every free-text `detail` |
| Primary keys | The **substantive** components of each PK are included as content (`cik_numeric`, `accession_plain`, `registrant_cik_numeric`, `reason_scope`, `reason_code`); the **scoping** component `snapshot_id` is not | Distinguishing content from scope is exactly the §8.1 rule |
| Materialized deterministic ordering fields | **None exist in the candidate family.** `selected_order` and `reserve_rank` are *selection*-layer columns and are already hashed there (D016 §8; D021 §§7.1, 7.2, 7.4). No candidate table carries an ordering column, so there is nothing to materialize and nothing is left to implicit row order | migration `0009`, verbatim |

**Deliberate redundancy, and why it is not double counting.** A.7/A.8 carry both the substantive
columns and `evidence_sha256`, which itself covers those columns plus the two IDs. That mirrors
D021 §7.4's accepted ruling that reserve child rows are hashed directly even though
`reserve_package_id` already binds them: "The redundancy is deliberate: it localizes a corruption to
the child family that carries it." It introduces **no second derivation** — nothing is recomputed
under a different rule — and it makes a corrupted `evidence_sha256` detectable against its own row.

---

### A.11 `candidate_snapshot_sha256`

| Attribute | Proposal |
|---|---|
| Digest field | `pilot_candidate_snapshots.candidate_snapshot_sha256` |
| `hash_table` name | `pilot_candidate_snapshot_content` |
| Call shape | Single-row |
| Field set (sorted by key) | `accession_count`, `candidate_accession_evidence_sha256`, `candidate_accession_reasons_sha256`, `candidate_accession_table_sha256`, `candidate_entity_evidence_sha256`, `candidate_entity_reasons_sha256`, `candidate_entity_table_sha256`, `candidate_registrant_table_sha256`, `coverage_window_sha256`, `entity_count`, `input_observation_set_sha256`, `snapshot_id` |
| Source of every field | The snapshot row's own columns, each already recomputed and validated in this transaction; `entity_count` / `accession_count` from `COUNT(*)` over the persisted child rows |
| Sort / key behavior | Single row, keys sorted |
| NULL behavior | Every field must be non-`NULL` at freeze; `0009`'s `frozen`-state `CHECK` independently enforces it |
| Normalization | Counts are integers; the rest are 64-hex strings |
| Included | Exactly those twelve |
| Excluded | **Itself**; `census_run_id`; `snapshot_state`; the four policy versions (transitively bound through `snapshot_id`); `invalidated_reason_code`; `created_at_utc`; `frozen_at_utc`; `invalidated_at_utc`; `detail` |
| Transitive commitments | The whole candidate row content, through the seven family digests; the coverage window, the policy versions, and the cited-observation content, through `snapshot_id` and its two digest inputs |
| Governing authority | Migration `0009` requires the column non-`NULL` at freeze; D016 §8 supplies the exclusions; D021 §8.2 consumes it as a declared digest |
| Circularity | **None**, and it excludes itself explicitly |
| Collision / equivalence | Two snapshots with identical content and policies share `snapshot_id`, all seven family digests, both counts, and therefore this value |
| Two independent builds | **Identical** |
| Random run IDs / observation IDs / timestamps / bytes / paths / approval / publication | **Cannot affect it** |
| Recomputation at freeze | Recompute from persisted rows and the eleven other recomputed values; compare; `GateFailureError` on difference |
| Verification at rehearsal | E1; and a fixture per contributing field asserting the value moves |

**Why `entity_count` and `accession_count` are inside it.** `0009`'s
`pilot_snapshot_freeze_requires_valid_state` already refuses a freeze whose declared counts differ
from the actual rows. Including them binds *the validated declaration* into identity, so a later
corruption of a count column is detectable by digest as well as by trigger — defence in depth of
exactly the kind D021 §7.4 endorses.

**Packet §6 constraint E is satisfied.** This digest does hash already-declared digest strings — but
every one of them has an exact, independently recomputable derivation stated above (§A.1, §A.2,
§A.4–A.10), and each is recomputed from persisted rows before it is consumed.

---

### A.12 Four content-derived candidate column hashes that OR-1's enumeration does not cover

The owner packet §6 enumerates eleven digests. Migration `0009` requires **four further families** of
content-derived candidate values, without which no candidate row can be written at all. Two have
accepted derivations; **two do not**. This is reported, not resolved.

| Column family | Accepted derivation? | Exact derivation, or the gap |
|---|---|---|
| `pilot_candidate_entities.entity_tie_break_sha256` | **Yes** | `SHA256(PILOT_SELECTION_SEED + "\|" + cik_padded)`, lowercase hex — D013 §6, D016 §7, implemented as `entity_selector.selection_rank` and reused unchanged |
| `pilot_candidate_accessions.accession_tie_break_sha256` | **Yes** | `SHA256(PILOT_SELECTION_SEED + "\|" + anchor_cik_padded + "\|" + accession_number_dashed)` — D018 §5.2, implemented as `accession_selector.accession_selection_rank`. The **dashed** form is canonical for hashing; associated registrant CIKs never enter it |
| `*_evidence.evidence_sha256` (2 tables) | **Partially** — D016 §4 fixes the field list, no record fixes the call shape | **Proposed:** single-row `hash_table("pilot_candidate_evidence_row", tuple(sorted(fields)), [fields])` over exactly D016 §4's list — `canonical_observed_value`, `classification_dimension`, `evidence_role`, `parsed_record_id`, `policy_version`, `precedence`, `source_field`, `source_observation_id`. Excludes `evidence_id`, `snapshot_id`, the parent key, and `recorded_at_utc`. It is a **content digest, never a unique key** |
| The eight `*_resolution_sha256` columns (`size`, `industry`, `history`, `primary_universe`; `filing_date`, `cohort`, `xbrl`, `amendment_purpose`) | **No accepted derivation exists** | **Proposed:** `hash_table("pilot_candidate_resolution", tuple(sorted(fields)), [fields])` over `classification_dimension`, `contributing_evidence_sha256`, `evidence_policy_version`, `resolved_value` — where `contributing_evidence_sha256` = `hash_table("pilot_candidate_resolution_evidence", ("evidence_role", "precedence", "evidence_sha256"), <that parent's rows for that dimension>)`. This ties the resolved value back to the exact evidence rows that produced it, as D016 §4 requires, and is recomputable from persisted rows alone |

**Finding.** OR-1's enumerated scope is **narrower than the set of preimages a builder must have** to
write a conforming candidate row. Two of the four above are unfixed by any accepted record and are
proposed here for the first time. **The owner should decide whether OR-1's ruling is widened to cover
them, or whether they are ruled separately (OQ-7).** Migration `0009` makes both non-optional:
`entity_tie_break_sha256` and `accession_tie_break_sha256` are `NOT NULL`, and each
`*_resolution_sha256` is bound by a `CHECK` making it exactly as present as its resolved value.

---

## B. OR-1 — circularity, equivalence, and contamination analysis

### B.1 The dependency graph, and its acyclicity

```text
caller inputs ──► coverage_window_sha256 ─┐
                                          ├─► snapshot_id ──► (row INSERT, state = building)
cited set S ──► input_observation_set_sha256 ─┘                        │
   ▲                                                                   ▼
   └──────── determined in memory before INSERT ──────────  child rows written
                                                                       │
                     ┌─────────────────────────────────────────────────┤
                     ▼                                                 ▼
   evidence_sha256 ──► *_resolution_sha256 ──► candidate_entity_table_sha256
                                             ├─► candidate_accession_table_sha256
                                             ├─► candidate_registrant_table_sha256
                                             ├─► candidate_entity_evidence_sha256
                                             ├─► candidate_accession_evidence_sha256
                                             ├─► candidate_entity_reasons_sha256
                                             └─► candidate_accession_reasons_sha256
                                                              │
                                                              ▼
                            candidate_snapshot_sha256 ◄── snapshot_id, coverage_window_sha256,
                                                          input_observation_set_sha256, counts
                                                              │
                                                              ▼
                              D021 §8.2 candidate_tables_sha256 (binds all nine, declared)
                                                              │
                                                              ▼
                                              root_manifest_sha256 ──► manifest_id
```

**Every edge points forward. There is no cycle.** The one edge that could look like a cycle —
`input_observation_set_sha256` depending on the evidence rows, while the evidence rows sit under a
`snapshot_id` that depends on `input_observation_set_sha256` — is not one:

- The digest hashes **`census_source_observations` content**, never a `pilot_candidate_*` row and
  never a `pilot_candidate_*` digest.
- The evidence rows contribute only the **set of `source_observation_id` values**, which the builder
  determines in memory before the `INSERT` and which the freeze validation then re-derives from the
  persisted rows and requires to match (§A.2.1).
- Under the §A.0 parent-key convention `snapshot_id` is **not** inside the family digests at all, so
  even the appearance of a back-edge is removed. Under the §7.1 alternative (**OQ-4**) the graph
  remains acyclic, because `snapshot_id` is fixed strictly before any child row exists.

### B.2 Every field has exactly one identity treatment

Applying the packet §8 item C test — `INCLUDED`, `EXCLUDED`, or `TRANSITIVELY INCLUDED`, never two —
across all **135** writable candidate columns (28 + 26 + 35 + 8 + 13 + 13 + 6 + 6, counted
per table-and-column pair against migration `0009` verbatim):

| Treatment | Count | Per table (snapshots / entities / accessions / registrants / entity-ev / accession-ev / entity-reasons / accession-reasons) |
|---|---|---|
| `INCLUDED` (direct, in exactly one digest) | **96** | 13 / 23 / 32 / 6 / 8 / 8 / 3 / 3 |
| `TRANSITIVELY INCLUDED` (through a lower digest, never also direct) | **12** | 8 / 0 / 0 / 0 / 2 / 2 / 0 / 0 |
| `EXCLUDED` (operational or scope, at every layer) | **27** | 7 / 3 / 3 / 2 / 3 / 3 / 3 / 3 |

The twelve transitively included are the five coverage-window fields and the three policy versions
(through `coverage_window_sha256` and `snapshot_id`), plus `source_observation_id` and
`parsed_record_id` on each evidence table (through `evidence_sha256`). The twenty-seven excluded are
`census_run_id`, `snapshot_state`, `invalidated_reason_code`, the four snapshot timestamps, `detail`,
the seven child-table `snapshot_id` scope keys, every `recorded_at_utc`, every child `detail`, and
both `evidence_id` columns.

**No column is both directly included and transitively included through a *different* rule.** The two
cases that come closest are deliberate redundancy under one rule, not two derivations:
`evidence_sha256` alongside its own fields (§A.4–A.10 note), and `entity_count`/`accession_count`
alongside the trigger that validates them (§A.11 note).

### B.3 The four contamination classes the packet §8 item D names

| Class | Finding |
|---|---|
| **Circular hashes** | **None.** §B.1 |
| **Unhashed substantive fields** | **None in the candidate family.** Every non-operational column of all eight tables appears in exactly one family digest. The audit is column-by-column against migration `0009`, not by column-name inference |
| **Double-counted provenance** | **Two deliberate redundancies**, both under D021 §7.4's accepted rule, both single-derivation (§B.2). **One to watch:** `source_observation_id` is bound twice by *different* digests — inside `evidence_sha256` (candidate layer) and, as the cited *set*, inside `input_observation_set_sha256`. These commit different facts (*which observation this row cites* versus *what that observation's content was*) and are not a double count; but see **OQ-5** |
| **Random-ID contamination** | **One channel closed, one channel open.** Closed: `evidence_id` and `census_run_id` are excluded everywhere. **Open by accepted authority:** `source_observation_id` and `parsed_record_id` sit inside `evidence_sha256` per D016 §4, so an identical re-retrieval or an identical reparse **would** change the candidate digests — while D021 §8.1 deliberately makes `source_observation_set_sha256` immune to exactly that. The asymmetry is real, is authorized, and is **OQ-5**. **CORRECTED — GR-C2 (Decision 067 §3.2):** the reparse half is **wrong**. An offline reparse of the **same** accepted observation row is **deterministic** and reproduces `parser_run_id` / `parsed_record_id`; **only re-retrieval** creates a new uuid4 `source_observation_id`, and M3.3 forbids reacquisition. **OQ-5 is answered ALT-3** — the fields are **retained** (**R15**) — and the residual cross-reacquisition asymmetry is recorded as limitation **D067-L1**, not repaired |
| **Timestamp contamination** | **None.** Every `recorded_at_utc`, `created_at_utc`, `frozen_at_utc`, `invalidated_at_utc`, and `retrieved_at_utc` is excluded at every layer. `acceptance_audit_date` is included as a calendar date and a classification input, per D019 §10 — the one deliberate inclusion, not an exception |
| **Alternative derivations for one field** | **None proposed.** Each of the 135 columns has exactly one proposed derivation or an explicit fail-closed gap (§D, §G) |
| **Source fields with no accepted authority** | **`coverage_policy_version`** — OQ-6. No Python constant, no `reference_policy_versions` seed row, no decision fixes a value |
| **Candidate fields with no source** | **The substantive majority** — §G, OQ-1 |

### B.4 Equivalence properties this proposal delivers

1. Two independently built snapshots from identical substantive source content and identical policy
   versions produce **identical values for all eleven digests**, regardless of `census_run_id`,
   insertion order, retrieval order, wall-clock, machine, SQLite version, or file layout.
2. No random run ID, operational event ID, timestamp, physical byte, path, approval field, or
   publication field can affect **any** of the eleven.
3. Two retrievals of identical content under the same request identity are the same content to
   `input_observation_set_sha256` (D021 §8.1) — **but not, under D016 §4, to the candidate evidence
   digests** (OQ-5). **CORRECTED — GR-C2:** this is true of **re-retrieval** only. A **reparse** of
   the same accepted observation is deterministic and changes nothing, and M3.3 forbids
   reacquisition, so the asymmetry is unreachable inside M3.3 (Decision 067 §3.2; **R15**;
   **D067-L1**).
4. Every one of the eleven is recomputable from persisted rows alone, with no caller-supplied value
   other than the frozen policy constants and the coverage window.

---

## C. OR-1 — independent recomputation and verification plan

### C.1 At freeze, inside the single authoritative R5 transaction

Ordered, and each step fails the **whole** transaction on any difference:

1. Recompute `coverage_window_sha256` from the row's own five columns; compare to the stored value.
2. Recompute the cited set `S` from the persisted evidence rows; recompute
   `input_observation_set_sha256` over `S` joined to `census_source_observations`, with each
   `schema_fingerprint_sha256` derived by D021 §8.1's frozen partition rule (including its step-4
   cross-parser-run equality requirement and its step-5 `GateFailureError`); compare to the stored
   value.
3. Recompute `snapshot_id` from the two recomputed digests and the three policy constants; compare to
   the stored primary key.
4. Recompute each `evidence_sha256` from its own row; compare. Recompute each `*_resolution_sha256`
   from the persisted evidence rows for that parent and dimension; compare.
5. Recompute each of the seven family digests from persisted rows; compare to the values about to be
   written.
6. Recompute both counts by `COUNT(*)`; compare to the declared columns.
7. Recompute `candidate_snapshot_sha256` from the twelve inputs; compare.
8. Run **every** Decision 019 §9 obligation, each failing for its own stated reason.
9. Only then perform `building -> frozen`.

**Connection mode:** the freeze is a write path and uses the writer. **Every** M3.3 verification,
replay, reconstruction, and manifest-verification path is read-only and must use a true OS-level
`SQLITE_OPEN_READONLY` connection with **no writer lease**, per Owner Ruling **R3**.

### C.2 At rehearsal (offline fixtures only)

- **Recompute-from-persisted-rows harness**, separate from the builder's own code path, reading
  through `strictly_read_only_connection` and asserting all eleven digests, byte for byte.
- **Per-field perturbation fixtures.** For each of the 96 directly included columns, a fixture that
  changes exactly that column and asserts the owning family digest **and**
  `candidate_snapshot_sha256` both move. For each of the 27 excluded columns, a fixture that changes
  exactly that column and asserts **no digest moves**. Vacuity is the failure mode these exist to
  prevent.
- **`census_run_id` invariance fixture** — two builds differing only in `census_run_id` produce the
  same `snapshot_id` and the same eleven digests (D016 §1's stated property, asserted directly).
- **Cited-set mismatch fixture** — a planned citation set differing from the persisted one fails
  closed and rolls back the whole transaction, leaving **no** partial snapshot (R5).
- **Structural-fingerprint fixtures** — identical reparse is a no-op; duplicate identical row is a
  no-op; two parser runs disagreeing on any of the five columns fails closed; an observation with no
  structural rows yields the empty-set digest and is distinct from any populated shape.
- **Write-freedom fixture** — R3: durable bytes of every pre-existing artifact, including the main
  database file, identical before and after every read-only path.

---

## D. OR-2 — proposed source → candidate field mapping matrix

**Read this section with §G open.** Every row classified `DIRECT ACCEPTED SOURCE` or
`DETERMINISTIC DERIVATION` below names a source table that, per §G, **no M3.2-authorized code path
populates**. The mapping is stated so the owner can rule on the derivation; it is **not** a claim that
the source is available.

**Classification vocabulary** (packet §7): `DIRECT ACCEPTED SOURCE` · `DETERMINISTIC DERIVATION` ·
`POLICY CONSTANT` · `CONTENT-DERIVED ID/HASH — OR-1` · `OPERATIONAL / EXCLUDED FROM IDENTITY` ·
`UNAVAILABLE / FAIL CLOSED` · `NOT APPLICABLE`.

**Universal rules proposed for every row below:** no discretionary fallback; no best effort; no manual
fill; no network fallback; exactly one governing derivation or a stated fail-closed gap; a
non-conforming input is **rejected, never normalized into conformance** (D019 §4 principle 9, §9;
contract §10).

**Proposed source read order** (deterministic, and fixed so two builds read identically):
1. `census_source_observations` (+ `census_observation_reasons`, `census_archive_members`) — provenance
   root and the cited-observation content;
2. `census_structural_observations` — schema fingerprints only;
3. `census_parsed_records` / `census_parser_runs` — parse provenance;
4. `census_registrants`, `census_registrant_observations` — entity identity and classification;
5. `census_accessions`, `census_accession_observations` — accession facts;
6. `census_accession_field_resolutions`, `census_accession_cohort_resolutions` — resolved fields and
   cohorts;
7. `census_historical_references`, `census_candidate_lineage_edges` — history-class evidence;
8. `reference_form_types`, `reference_reason_codes`, `reference_policy_versions` — reference data.

**`census_index_instances` — proposed disposition: NOT USED.** It is a *census planning and coverage*
table (`census_run_id`, `instance_key`, `year`, `quarter`, `required`, `retrieved`, `parse_usable`,
`observation_id`). It carries no candidate-column content: every field is either a census run
identity, a plan expectation, or an observation pointer already available from
`census_source_observations`. Its emptiness is therefore **AVAILABLE-AS-NONE and not a blocker**, and
it may not be populated artificially. Full trace at §E.

**`census_index_reconciliation` — proposed disposition: VALIDATION-ONLY, and unavailable.** It would
be the natural corroboration source for a `conflicting` filing-date evidence level; it is written only
by the census layer (§G) and is unavailable on the same terms.

**`inventory_*` — NOT APPLICABLE, prohibited.** Migration `0009`'s header and D013 §2 forbid any
`inventory_*` reference before M2.5; no row below references one.

### D.1 `pilot_candidate_snapshots` — 28 writable columns

| Target column | Source table.column | Transformation / accepted function | Governing record | Evidence floor | Missing / conflict behavior | Identity effect | Class |
|---|---|---|---|---|---|---|---|
| `snapshot_id` | — | §A.3 | D016 §1 | n/a | fail closed | **is** the identity | CONTENT-DERIVED — OR-1 |
| `census_run_id` | `ops_ingestion_jobs.job_id` (FK) | the M3.2A run that produced the cited observations, recorded verbatim | `0009` FK; D016 §1 | provenance | fail closed if absent | **EXCLUDED everywhere** | OPERATIONAL / EXCLUDED |
| `coverage_start` | caller | frozen `2009-01-01` | D013 §1 | n/a | fail closed | in `coverage_window_sha256` | POLICY CONSTANT |
| `coverage_end` | caller | frozen `2026-06-30` | D013 §1 | n/a | fail closed | in `coverage_window_sha256` | POLICY CONSTANT |
| `as_of_date` | caller | frozen `2026-06-30` | D013 §1 | n/a | fail closed | in `coverage_window_sha256` | POLICY CONSTANT |
| `include_open_quarter` | caller | literal `0` | D013 §1; `0009` `CHECK` | n/a | schema refuses `1` | in `coverage_window_sha256` | POLICY CONSTANT |
| `coverage_policy_version` | — | **no accepted value source** | — | — | **fail closed — OQ-6** | in `coverage_window_sha256` | **UNAVAILABLE / FAIL CLOSED** |
| `candidate_policy_version` | `pilot_policy.PILOT_CANDIDATE_POLICY_VERSION` | verbatim `"pilot-candidate/1.0"` | D016 §1; `0009` seed | n/a | fail closed | in `snapshot_id` | POLICY CONSTANT |
| `sic_family_mapping_version` | `pilot_policy.SIC_FAMILY_MAPPING_VERSION` | verbatim `"sic-family-mapping/0.2"` | D014 §4; `0009` seed | n/a | fail closed | in `snapshot_id` | POLICY CONSTANT |
| `evidence_policy_version` | `pilot_policy.PILOT_EVIDENCE_POLICY_VERSION` | verbatim `"pilot-evidence/1.0"` | D014 §1; `0009` seed | n/a | fail closed | in `snapshot_id` | POLICY CONSTANT |
| `coverage_window_sha256` | — | §A.1 | D016 §1 | n/a | fail closed | direct | CONTENT-DERIVED — OR-1 |
| `input_observation_set_sha256` | `census_source_observations` (+ `census_structural_observations`) | §A.2 | D016 §1; D021 §8.1 | cited observations must exist and be hash-valid | fail closed; rolls back | in `snapshot_id` | CONTENT-DERIVED — OR-1 |
| the seven `candidate_*_sha256` | the seven child tables | §A.4–A.10 | `0009` freeze `CHECK` | rows persisted | fail closed; rolls back | in `candidate_snapshot_sha256` | CONTENT-DERIVED — OR-1 |
| `candidate_snapshot_sha256` | — | §A.11 | `0009` freeze `CHECK` | all nine present | fail closed | terminal candidate identity | CONTENT-DERIVED — OR-1 |
| `snapshot_state` | — | `'building'` at insert; `'frozen'` as the last statement of the R5 transaction | `0009` triggers; R5 | n/a | trigger refuses any other path | contributed to D021 §8.2 as the **literal** `"frozen"` | OPERATIONAL / EXCLUDED |
| `entity_count` | `COUNT(*)` over `pilot_candidate_entities` | declared, then trigger-validated | `0009` `pilot_snapshot_freeze_requires_valid_state` | rows persisted | fail closed | in `candidate_snapshot_sha256` | DETERMINISTIC DERIVATION |
| `accession_count` | `COUNT(*)` over `pilot_candidate_accessions` | as above | as above | rows persisted | fail closed | in `candidate_snapshot_sha256` | DETERMINISTIC DERIVATION |
| `invalidated_reason_code` | `reference_reason_codes` | never written by M3.3 (no invalidation is authorized) | D016 §5; contract §36 | n/a | n/a | EXCLUDED | NOT APPLICABLE |
| `created_at_utc` | wall clock | recorded verbatim | `0009` | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |
| `frozen_at_utc` | wall clock | set at the transition | `0009` | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |
| `invalidated_at_utc` | — | never written by M3.3 | contract §36 | n/a | n/a | EXCLUDED | NOT APPLICABLE |
| `detail` | — | `''`; **never a path, never an SEC identity** | D016 §8 | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |

### D.2 `pilot_candidate_entities` — 26 writable columns

| Target column | Source table.column | Transformation / accepted function | Governing record | Evidence floor | Missing / conflict behavior | Identity effect | Class |
|---|---|---|---|---|---|---|---|
| `snapshot_id` | parent | scope key | `0009` FK | n/a | fail closed | scope, not content (§A.0) | DETERMINISTIC DERIVATION |
| `cik_numeric` | `census_registrants.cik_numeric` | verbatim | D007 canonical CIK | registrant row exists | fail closed | INCLUDED | DIRECT ACCEPTED SOURCE |
| `cik_padded` | `census_registrants.cik_padded` | canonical 10-digit zero-pad; must be the exact rendering of `cik_numeric` | D007; D019 §6.2 | as above | disagreement fails closed | INCLUDED | DETERMINISTIC DERIVATION |
| `entity_tie_break_sha256` | — | `entity_selector.selection_rank(cik_padded)` | D013 §6; D016 §7 | n/a | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `candidate_category` | `census_registrant_observations` kinds `entity_type` / `filing_status` / `sic` | D016 §2's four-condition classification into `operating` / `control` / `ineligible` | D002; D016 §2 | `provisional` | unresolved ⇒ `ineligible`, never a default to `operating` | INCLUDED | DETERMINISTIC DERIVATION |
| `control_kind` | as above | one of the four boundary-control kinds; `NULL` unless `candidate_category = 'control'` (`CHECK`) | D016 §2; D013 §3 | `provisional` | fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `size_stratum` | `census_registrant_observations` (`observation_kind` carrying the submissions `category` field) | unambiguous map to `large_accelerated` / `accelerated` / `non_accelerated_or_smaller`; the last is one combined stratum | D014 §2 | `provisional` only | blank or ambiguous ⇒ `NULL` + `review_required`; **never defaulted** | INCLUDED | DETERMINISTIC DERIVATION |
| `size_evidence_level` | as above | D014 §1's five-state vocabulary, less `verified` (unavailable at M2.3) | D014 §1 | — | missing ⇒ `unavailable`; disagreeing ⇒ `conflicting` | INCLUDED | DETERMINISTIC DERIVATION |
| `size_resolution_sha256` | the winning/competing entity-evidence rows | §A.12 resolution digest | D016 §4 | must exist iff `size_stratum` is non-`NULL` (`CHECK`) | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `sic_code` | `census_registrant_observations` kind `sic` | canonical four-digit zero-padded text (`CHECK`); `NULL` when none on record | D014 §3; `0009` | `provisional` | conflicting ⇒ `NULL` + `REVIEW_CONFLICTING_SIC` | INCLUDED | DETERMINISTIC DERIVATION |
| `industry_family` | `sic_code` | the frozen `sic-family-mapping/0.2` table, D014 §4, applied verbatim | D014 §4 | `provisional` | unmapped code ⇒ `NULL` + `review_required`; **never mapped by proximity** | INCLUDED | DETERMINISTIC DERIVATION |
| `industry_quota_eligible` | derived | `1` only when `industry_family` non-`NULL` **and** `industry_evidence_level = 'provisional'` (`CHECK`); `0` for 6712, 6719, 6798, 3826, 8731 | D014 §4; D016 §2 | `provisional` | fail closed to `0` | INCLUDED | DETERMINISTIC DERIVATION |
| `industry_evidence_level` | as `sic_code` | D014 §1 vocabulary | D014 §§1, 3 | — | as above | INCLUDED | DETERMINISTIC DERIVATION |
| `industry_resolution_sha256` | industry evidence rows | §A.12 | D016 §4 | present iff `industry_family` non-`NULL` | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `history_class` | the twelve frozen event flags versus the seven stable conditions | D014 §5, applied verbatim; **never adjusted after seeing the real distribution** | D014 §5 | `provisional` | any unresolved input ⇒ `NULL` + `review_required` | INCLUDED | DETERMINISTIC DERIVATION |
| `history_evidence_level` | as above | D014 §1 vocabulary | D014 §1 | — | as above | INCLUDED | DETERMINISTIC DERIVATION |
| `history_resolution_sha256` | history evidence rows | §A.12 | D016 §4 | present iff `history_class` non-`NULL` | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `currently_inactive` | `census_registrant_observations` kind `filing_status` | boolean; **stratification only, never a feature input** | D014 §5; D015; L19 | `provisional` | absent ⇒ `0` | INCLUDED | DIRECT ACCEPTED SOURCE |
| `eligible_original_annual_report_count` | `census_accessions` | count of eligible **original** annual reports for this CIK in window | D014 §5 (the ≥4 stable condition) | `provisional` | absent accessions ⇒ `0` | INCLUDED | DETERMINISTIC DERIVATION |
| `primary_universe_eligible` | derived | D016 §2's **four** conditions, all required; `0` for every control and for SIC 6000–6999 (`CHECK`) | D002; D016 §2 | `provisional` **only** (`CHECK`) | unresolved required evidence ⇒ `0`, fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `primary_universe_evidence_level` | as above | must be `provisional` whenever eligible (`CHECK`) | D016 §2 | — | as above | INCLUDED | DETERMINISTIC DERIVATION |
| `primary_universe_resolution_sha256` | universe evidence rows | §A.12; `NOT NULL` whenever eligible (`CHECK`) | D016 §4 | — | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `engineering_only_stress` | derived | `1` only for the engineering-only cases (6712, 6798); forces `primary_universe_eligible = 0` (`CHECK`) | D014 §4; D016 §2 | — | fail closed to `0` | INCLUDED | DETERMINISTIC DERIVATION |
| `filing_time_name` | `census_registrant_observations` kind `company_name` | canonical registrant name at filing time; **diagnostic only, never affects selection order** | D018 §13; D019 §8; `entity_selector.Candidate` | `provisional` | absent ⇒ fail closed (column is `NOT NULL`) | INCLUDED | DIRECT ACCEPTED SOURCE |
| `recorded_at_utc` | wall clock | verbatim | `0009` | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |
| `detail` | — | `''` | D016 §8 | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |

### D.3 `pilot_candidate_accessions` — 35 writable columns

| Target column | Source table.column | Transformation / accepted function | Governing record | Evidence floor | Missing / conflict behavior | Identity effect | Class |
|---|---|---|---|---|---|---|---|
| `snapshot_id` | parent | scope key | `0009` | n/a | fail closed | scope (§A.0) | DETERMINISTIC DERIVATION |
| `accession_plain` | `census_accessions.accession_plain` | 18-character plain form; **the DB/FK identity** | D018 §5.1 | accession row exists | fail closed | INCLUDED | DIRECT ACCEPTED SOURCE |
| `accession_number_dashed` | `census_accessions.accession_dashed` | canonical dashed form via `sec/identifiers.parse_accession`; **canonical for hashing and presentation** | D018 §§5.1–5.3 | as above | **plain/dashed disagreement fails closed** — never reconciled | INCLUDED | DETERMINISTIC DERIVATION |
| `accession_tie_break_sha256` | — | `accession_selector.accession_selection_rank(anchor_cik_padded, accession_number_dashed)` | D018 §5.2 | n/a | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `anchor_cik_numeric` | `census_accessions.registrant_cik_numeric` + registrant structure | the single anchor registrant; exactly one per accession | D019 §§6.1–6.2 | `provisional` | zero or many anchors fails closed at freeze | INCLUDED | DETERMINISTIC DERIVATION |
| `form_type` | `census_accessions.form_type` → `reference_form_types` | verbatim, FK-validated | D008; `0009` FK | — | unknown form fails closed | INCLUDED | DIRECT ACCEPTED SOURCE |
| `is_amendment` | `census_accessions.is_amendment` | verbatim boolean | D008; D018 §10 | — | fail closed | INCLUDED | DIRECT ACCEPTED SOURCE |
| `official_filing_date` | `census_accession_field_resolutions` (`field_name` = official filing date) | the resolved precedence-2 value | D010 §4.1; D014 §7 | `provisional` | unresolved ⇒ `NULL` **and** `filing_date_resolution_sha256` `NULL` (`CHECK`) | INCLUDED | DIRECT ACCEPTED SOURCE |
| `report_date` | `census_accessions.report_date` | verbatim calendar date | D008 | `provisional` | absent ⇒ `NULL` | INCLUDED | DIRECT ACCEPTED SOURCE |
| `acceptance_audit_date` | `census_accessions.acceptance_date_sec` | D010 §4.3's acceptance-date derivation, including the frozen after-hours cutoff (§5.2) and non-operating-day rule (§5.3) | D010 §§4.2–4.3, 5.2–5.3; D019 §5.9 | `provisional` | absent or malformed ⇒ the amendment is `unresolved_amendment`, never a resolved state | **INCLUDED — the one deliberate date inclusion** (D019 §10) | DETERMINISTIC DERIVATION |
| `filing_date_evidence_level` | as `official_filing_date` | D014 §1 vocabulary | D014 §§1, 7 | — | conflicting precedence-2 observations ⇒ `conflicting` | INCLUDED | DETERMINISTIC DERIVATION |
| `filing_date_resolution_sha256` | filing-date evidence rows | §A.12; present iff `official_filing_date` non-`NULL` (`CHECK`) | D016 §4 | — | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `filing_date_precedence` | — | the literal `2` (`CHECK` permits only `2`) — accession-header evidence is precedence 1 and is a filing-body operation prohibited throughout M2.3 | D010 §4.1; D014 §7 | — | any other value refused by schema | INCLUDED | POLICY CONSTANT |
| `provisional_official_cohort` | `census_accession_cohort_resolutions.official_filing_temporal_cohort` | frozen cohort windows from `cohorts.py`, **never redefined** | D003; D005; D010 §3 | `provisional` | ambiguous ⇒ `NULL`, `cohort_ambiguous = 1`, and `base_eligible = 0` (`CHECK`) | INCLUDED | DIRECT ACCEPTED SOURCE |
| `acceptance_audit_cohort` | `census_accession_cohort_resolutions.accepted_temporal_cohort` | as above, on the acceptance date | D010 §§3, 8 | `provisional` | as above | INCLUDED | DIRECT ACCEPTED SOURCE |
| `cohort_evidence_level` | derived | **`provisional` by design** for every M2.3 candidate — D014 §7's explicit ruling | D014 §7 | — | ambiguity is a *different* condition and blocks eligibility | INCLUDED | POLICY CONSTANT |
| `cohort_resolution_sha256` | cohort evidence rows | §A.12; present iff `provisional_official_cohort` non-`NULL` (`CHECK`) | D016 §4 | — | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `cohort_ambiguous` | derived | `1` on `indeterminate` ordering, unexplained divergence (D010 §5.1), or irreconcilable precedence-2 conflict | D010 §5.1; D014 §7 | — | fail closed to `1` | INCLUDED | DETERMINISTIC DERIVATION |
| `has_xbrl` | `census_accessions.xbrl_flag` | verbatim boolean | D008 | `provisional` | absent ⇒ `0` with `xbrl_evidence_level` ≠ `provisional` | INCLUDED | DIRECT ACCEPTED SOURCE |
| `has_inline_xbrl` | `census_accessions.inline_xbrl_flag` | verbatim boolean | D008 | `provisional` | as above | INCLUDED | DIRECT ACCEPTED SOURCE |
| `xbrl_evidence_level` | as above | D014 §1 vocabulary; `CHECK` ties `provisional` exactly to a non-`NULL` resolution hash | D014 §1 | — | fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `xbrl_resolution_sha256` | XBRL evidence rows | §A.12; the `CHECK` is an **iff** on `provisional` | D016 §4 | — | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `amendment_linkage_state` | `census_accessions` + `sec/amendments.link_amendment` | D019 §5.2's frozen five-value mapping; `NULL` iff `is_amendment = 0` (`CHECK`) | D019 §§5.1–5.8 | `provisional` | unresolved parentage ⇒ `unresolved_amendment` **and** a `REVIEW_AMENDMENT_PARENT_UNRESOLVED` reason row | INCLUDED | DETERMINISTIC DERIVATION |
| `provisional_parent_accession` | `census_accessions` | canonical **plain** stored parent form (D019 §5.7); direct parent must be present in the same snapshot | D019 §§5.4, 5.7 | `provisional` | absent parent ⇒ `unresolved_amendment` (D019 §5.6) | INCLUDED | DETERMINISTIC DERIVATION |
| `amendment_purpose_category` | metadata only | one of D014 §6's three frozen categories | D014 §6 | `provisional` or `unproven` **only** | undeterminable ⇒ `NULL`; `CHECK` ties it to the resolution hash | INCLUDED | DETERMINISTIC DERIVATION |
| `amendment_purpose_evidence_level` | as above | six-value vocabulary including `unproven` — the ordinary M2.3 case | D014 §6 | — | fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `amendment_purpose_resolution_sha256` | amendment-purpose evidence rows | §A.12; `CHECK` is an iff on the category | D016 §4 | — | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `amendment_purpose_quota_eligible` | derived | `1` only at `provisional` with a non-`NULL` category (`CHECK`); **`unproven` can never satisfy an affirmative quota** | D014 §6 | — | fail closed to `0` | INCLUDED | DETERMINISTIC DERIVATION |
| `base_eligible` | derived | `1` only when `is_amendment = 0` **and** `cohort_ambiguous = 0` **and** `provisional_official_cohort` non-`NULL` (`CHECK`) | D018 §§7, 8; `0009` | `provisional` | fail closed to `0` | INCLUDED | DETERMINISTIC DERIVATION |
| `stress_eligible` | derived | the engineering-only stress rule | D014 §4; D018 §7 | `provisional` | fail closed to `0` | INCLUDED | DETERMINISTIC DERIVATION |
| `support_eligible` | derived | includes the 2009-support / 2010-target pairing and its pre-study provenance marker | D018 §15; D019 §7 | `provisional` | missing marker where claimed ⇒ fail closed (D019 §7.5) | INCLUDED | DETERMINISTIC DERIVATION |
| `control_eligible` | derived | anchor entity is a boundary control | D013 §3; D016 §2 | `provisional` | fail closed to `0` | INCLUDED | DETERMINISTIC DERIVATION |
| `multi_registrant` | `pilot_candidate_accession_registrants` | agreement with the normalized registrant rows, subject to D019 §6.3's **single** exact-code exception | D019 §§6.1–6.5; D016 §9 | `provisional` | disagreement outside the one exception fails closed at freeze | INCLUDED | DETERMINISTIC DERIVATION |
| `recorded_at_utc` | wall clock | verbatim | `0009` | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |
| `detail` | — | `''` | D016 §8 | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |

### D.4 `pilot_candidate_accession_registrants` — 8 writable columns

| Target column | Source table.column | Transformation | Governing record | Evidence floor | Missing / conflict behavior | Identity effect | Class |
|---|---|---|---|---|---|---|---|
| `snapshot_id` | parent | scope key | `0009` | n/a | fail closed | scope (§A.0) | DETERMINISTIC DERIVATION |
| `accession_plain` | parent | scope key; FK to `pilot_candidate_accessions` | `0009` FK | n/a | fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `registrant_cik_numeric` | `census_accessions.registrant_cik_numeric` / `submitter_cik_numeric`; `census_accession_observations` | the **structural registrant set** — built only from approved census observations, no inference beyond what the parser captured | D019 §6.2; **D016 §9** | `provisional` | duplicate identity fails closed at freeze | INCLUDED | DIRECT ACCEPTED SOURCE |
| `registrant_cik_padded` | derived | canonical 10-digit rendering; bijective with the numeric form | D019 §6.2 | — | disagreement fails closed | INCLUDED | DETERMINISTIC DERIVATION |
| `role` | derived | `anchor` / `associated` / `submitter_only`; **exactly one anchor per accession** | D019 §§6.1–6.2 | `provisional` | zero or many anchors fails closed at freeze | INCLUDED | DETERMINISTIC DERIVATION |
| `is_anchor` | derived | `(role = 'anchor')` — schema `CHECK` enforces the equivalence | `0009` | — | fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `evidence_level` | derived | D014 §1 vocabulary, less `verified` | D014 §1; D019 §6.5 | — | deterministic weaker-state precedence (D019 §6.5) | INCLUDED | DETERMINISTIC DERIVATION |
| `recorded_at_utc` | wall clock | verbatim | `0009` | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |

**Note.** No `multi_registrant_resolution_sha256` column exists and **none is authorized** (D019
§6.6). The canonical sorted registrant-row set *is* the resolved representation; S5.2 computes the
D019 §6.6.1 per-accession digest at read time for validation and run identity and **never writes it
back**. The builder must not create one.

### D.5 `pilot_candidate_entity_evidence` — 13 writable columns

| Target column | Source | Transformation | Governing record | Evidence floor | Missing / conflict behavior | Identity effect | Class |
|---|---|---|---|---|---|---|---|
| `evidence_id` | builder | a stable per-row identifier; **must not be a random UUID if it is ever hashed** — under this proposal it is **excluded from every digest**, so its form is unconstrained by identity | D016 §8 | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |
| `snapshot_id` | parent | scope key | `0009` FK | n/a | fail closed | scope (§A.0) | DETERMINISTIC DERIVATION |
| `cik_numeric` | parent | scope key + content | `0009` FK | n/a | fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `classification_dimension` | derived | one of `size`, `industry`, `history`, `primary_universe`, `identity` | D016 §4; `0009` | — | fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `evidence_role` | derived | `winning` / `competing` / `supporting` | D016 §4; D019 §8.1.2 | — | absent role fails closed at freeze | INCLUDED | DETERMINISTIC DERIVATION |
| `source_observation_id` | `census_source_observations.observation_id` | verbatim pointer to the citing observation | D016 §4 | observation must exist | fail closed | **TRANSITIVELY INCLUDED** via `evidence_sha256` | DIRECT ACCEPTED SOURCE |
| `parsed_record_id` | `census_parsed_records.parsed_record_id` | verbatim; **non-null on every `identity` row** (D019 §8.1.2) | D016 §4; D019 §§8.1.2, 10 | parse record must exist | fail closed | **TRANSITIVELY INCLUDED** via `evidence_sha256` | DIRECT ACCEPTED SOURCE |
| `source_field` | the census parser's field name | verbatim; for `identity` restricted to `{former_name_relationship, ticker_change}` | D019 §8.1.1 | — | any other `identity` field fails closed at freeze | INCLUDED | DIRECT ACCEPTED SOURCE |
| `canonical_observed_value` | the observed value | canonical form; for a `ticker_change` row it is **`NULL`** (D019 §8.5); former-name payloads follow D019 §8.2's canonical JSON exactly | D019 §§8.2, 8.5 | — | strict parse; non-canonical payload fails closed | INCLUDED | DETERMINISTIC DERIVATION |
| `policy_version` | `pilot_policy.PILOT_EVIDENCE_POLICY_VERSION` | verbatim | D014 §1 | — | fail closed | INCLUDED | POLICY CONSTANT |
| `precedence` | derived | D010 §4.1 / D014 §7 precedence; `>= 1` (`CHECK`) | D010 §4.1 | — | fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `evidence_sha256` | this row | §A.12 evidence digest over D016 §4's eight fields | D016 §4 | — | fail closed | INCLUDED | CONTENT-DERIVED (§A.12) |
| `recorded_at_utc` | wall clock | verbatim | `0009` | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |

### D.6 `pilot_candidate_accession_evidence` — 13 writable columns

Identical to §D.5 in every respect, with two differences fixed by migration `0009` and D019:

- the parent key is `accession_plain`, not `cik_numeric`;
- `classification_dimension` is one of `filing_date`, `cohort`, `xbrl`, `amendment_purpose`,
  `multi_registrant`, `identity` — and **D019 §8.1.1 forbids an `identity`-dimension row on this
  table entirely**, which is a freeze obligation, not a convention.

### D.7 `pilot_candidate_entity_reasons` and `pilot_candidate_accession_reasons` — 6 columns each

| Target column | Source | Transformation | Governing record | Evidence floor | Missing / conflict behavior | Identity effect | Class |
|---|---|---|---|---|---|---|---|
| `snapshot_id` | parent | scope key | `0009` FK | n/a | fail closed | scope (§A.0) | DETERMINISTIC DERIVATION |
| `cik_numeric` / `accession_plain` | parent | scope key + content | `0009` FK | n/a | fail closed | INCLUDED | DETERMINISTIC DERIVATION |
| `reason_scope` | derived | entity: `eligibility`, `size`, `industry`, `history`, `primary_universe`, `identity`. Accession: `eligibility`, `cohort`, `xbrl`, `amendment`, `multi_registrant`, `identity`. **No `identity`-scope reason row may be written on either table** (D019 §8.1.1) | D019 §8.1.1; `0009` | — | fail closed at freeze | INCLUDED | DETERMINISTIC DERIVATION |
| `reason_code` | `reference_reason_codes` | registered codes only, FK-validated; includes `REVIEW_AMENDMENT_PARENT_UNRESOLVED` (D019 §5), `PILOT_ACCESSION_PRE_STUDY_SUPPORT` scope `cohort` (D019 §7), `REVIEW_CONFLICTING_SIC` (D014 §3) | D016 §4; D019 §§5, 7 | — | unregistered code fails closed | INCLUDED | DIRECT ACCEPTED SOURCE |
| `detail` | — | `''` | D016 §8 | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |
| `recorded_at_utc` | wall clock | verbatim | `0009` | n/a | n/a | **EXCLUDED** | OPERATIONAL / EXCLUDED |

**Reason-row generation rule proposed.** A reason row is written **exactly when** the accepted record
that defines it requires it, and **never** as free commentary: no reason row may contradict the stored
state it describes, and no fact may be represented twice in normalized form (D019 §9). The
`PILOT_ACCESSION_PRE_STUDY_SUPPORT` row must be present with the exact code and scope wherever
pre-study applicability is claimed and **absent everywhere it would be contradictory** (D019 §7).

---

## E. Source-family forward trace — every accepted M3.2 source family, and what becomes of it

| M3.2 source family | Populated by an M3.2-authorized path? | Proposed M3.3 use |
|---|---|---|
| Stored raw objects (76, hash-valid) | **Yes** — `m3/acquisition.py` + `sec/raw_store.py` | **PROVENANCE-ONLY.** The evidence root behind every observation. Never re-parsed by M3.3, never mutated |
| Quarterly full-index objects (70) | **Yes** | **PROVENANCE-ONLY** in M3.3, as stored objects. Their *content* becomes substantive only through the parse layer, which is unavailable (§G) |
| `census_source_observations` (77 rows) | **Yes** — `sec/observation_catalog.py` | **SUBSTANTIVE.** The sole content input to `input_observation_set_sha256` / `source_observation_set_sha256`, over six columns |
| `census_observation_reasons` | **Yes** | **VALIDATION-ONLY.** Provenance-quality signal; contributes to no digest |
| `census_archive_members` | **Yes** | **VALIDATION-ONLY.** Archive-to-member lineage for the bulk object; contributes to no candidate column and no digest |
| `census_structural_observations` | **No** — census parse layer only | **SUBSTANTIVE BY DESIGN, EMPTY IN FACT.** Every cited observation would contribute D021 §8.1's empty-row-set fingerprint (OQ-2) |
| `census_parser_runs`, `census_parsed_records` | **No** | Would be the parse provenance for every evidence row. **UNAVAILABLE — OQ-1** |
| `census_registrants`, `census_registrant_observations` | **No** | Would be the source of every entity identity and classification column. **UNAVAILABLE — OQ-1** |
| `census_accessions`, `census_accession_observations` | **No** | Would be the source of every accession fact. **UNAVAILABLE — OQ-1** |
| `census_accession_field_resolutions`, `census_accession_cohort_resolutions` | **No** | Would supply resolved filing dates and cohorts. **UNAVAILABLE — OQ-1** |
| `census_historical_references`, `census_malformed_historical_references`, `census_candidate_lineage_edges` | **No** | Would be history-class and succession evidence. **UNAVAILABLE — OQ-1** |
| `census_index_instances` | **No** — written only by `census_orchestrator._persist_index_instances` | **DELIBERATELY UNUSED.** Census planning/coverage only; no candidate column derives from it. Empty is correct and is **not** a blocker and **not** a reason to reacquire |
| `census_index_reconciliation` | **No** | **VALIDATION-ONLY** if it existed; unavailable |
| `census_calendar_days`, `census_qa_metrics`, `census_quarantined_records`, `census_plan_sources`, `census_recovery_*`, `census_projection_recovery_events` | mixed | **DELIBERATELY UNUSED** by the builder. Operational, calendar, or QA state; none is candidate content |
| `ops_ingestion_jobs` | **Yes** | **PROVENANCE-ONLY** — supplies `census_run_id`, which is excluded from every digest |
| `reference_form_types`, `reference_reason_codes`, `reference_policy_versions` | **Yes** (seeded by migrations) | **SUBSTANTIVE** as FK validation and policy-version cross-checks |
| T6 failed run row / receipt / observations; T7 receipt and run; the historical `stopped` run | **Yes** | **READ-ONLY, never mutated.** No candidate content |
| The S4 entity-only draft | n/a | **PROHIBITED as an input** (D021 §14; D018 §6) |
| Outcome values, filing text, CompanyFacts, Frames, pilot membership | never acquired | **PROHIBITED absolutely** (CLAUDE.md 4–5; D015; L15/L19) |

---

## F. Candidate-field backward trace — the summary

Tracing each of the **135** writable candidate columns back to accepted M3.2 source content:

| Terminus | Columns | Reachable today? |
|---|---|---|
| Caller-supplied frozen policy constants and coverage window | 12 | **Yes**, except `coverage_policy_version` (OQ-6) |
| Content-derived — the eleven OR-1 digests, the twelve §A.12 column hashes (2 tie-break + 2 `evidence_sha256` + 8 resolution), and the two counts | 25 | **Yes**, once their inputs exist |
| Operational / excluded (timestamps, `detail`, `evidence_id`, `census_run_id`, `snapshot_state`) | 18 | **Yes** |
| Scope keys (`snapshot_id` on the seven child tables) | 7 | **Yes** |
| Not written by M3.3 at all (`invalidated_reason_code`, `invalidated_at_utc`) | 2 | n/a |
| **The census parse layer** | **71** | **No — OQ-1** |

`input_observation_set_sha256` sits inside the content-derived group and is the only column whose
substantive terminus is `census_source_observations` itself; that source **is** populated, and its
`census_structural_observations` companion is not (OQ-2).

**Conclusion of the backward trace.** **71 of 135 columns — more than half the candidate schema —**
terminate in the census parse layer, which no M3.2-authorized path populates. Every remaining column
is a frozen constant, an operational field, a scope key, or a digest over the other three — that is,
the builder can construct a **structurally valid but substantively empty** snapshot today, and
nothing more.

> **CORRECTED as a statement of the future, accurate as a statement of the present (Decision 067
> §10.1).** The count and the tracing stand, and the conclusion is correct **as at M3.2's accepted
> state** — which is why a real snapshot may not be built from it. It is **not** a permanent
> property: those 71 columns become available **after the governed R13 offline parse succeeds**, and
> the accepted mapping in §D is then live rather than vacuous. A structurally valid but substantively
> empty snapshot is **never** an acceptable substitute (**R14**).

---

## G. Unavailable / fail-closed fields, and the evidence for the finding

### G.1 The parse-layer finding, stated as verifiable repository fact

| Claim | How it was verified |
|---|---|
| Only `sec/census.py` and `sec/census_orchestrator.py` write the parse layer | `grep` for `INTO <table>` across `src/`, excluding `storage/migrations/`, for all seventeen census tables |
| Their sole entry point is `cli.py`'s `sec census` command | `grep` for importers of `census_orchestrator` and `CensusCatalog` across `src/` and `tests/` |
| `sec census` is network-gated | `cli.py`: `network_commands = {"census", "ingest-pilot"}`, refused when `config.network.enabled` is false |
| ~~Parsing is coupled to retrieval and cannot be run offline over stored objects~~ **CORRECTED — GR-C1** | `census_orchestrator` builds an `HttpxTransport` and calls `_retrieve_and_parse(client, …)` per source. **The evidence supports only the narrower claim**: the coupling is at the **orchestration entry point**. M3.3-GV2 verified that the parsers themselves are **pure over materialized content** and that loading, archive traversal, and `CensusCatalog` persistence are **already offline-capable** — the missing piece is an **offline entry point / driver**, a `SMALL_EXTENSION` (Decision 067 §§2.1, 3.1; **R13**) |
| M3.2A's acquisition path never invokes it | `m3/acquisition.py` imports `sec.observation_catalog`, `sec.raw_store`, `sec.archive`; it imports nothing from `sec.census` or `sec.census_orchestrator` — its single mention of the latter is a docstring cross-reference, not a call — and it contains no reference to `census_structural_observations` |
| Tracked network switches are `false` / `false` | `Milestones/STATUS.md`; contract §2 |
| `census_index_instances` is empty | written only by `census_orchestrator._persist_index_instances`; consistent with `Milestones/STATUS.md`'s "empty by design" |

**Limit of the finding.** This is proof about **code paths and authorizations**, not an inspection of
the real catalog — no private evidence was opened, as the packet requires. **The owner must verify
against the private evidence**, read-only and under **R3**, whether the parse layer is in fact empty.
If it is populated by some path this analysis did not find, OQ-1 dissolves and §D stands as written.

> **DISCHARGED 2026-08-13.** That verification was performed as **M3.3-GV2**, strictly read-only,
> with the main database's durable SHA-256 unchanged before and after, no network, no parser
> execution, and no private mutation. **The parse layer is EMPTY**, and `parser_state` is
> `not_started` for all 76 plan sources. The owner accepted those findings
> (`M3_3_GV2_PARSE_AND_IDENTITY_VERIFICATION_OWNER_ACCEPTED`) and ruled **R13** — see the disposition
> block at the head of this document. Decision 067 §2.1 carries the accepted finding list.

### G.2 Fields marked `UNAVAILABLE / FAIL CLOSED`

| Field(s) | Why | Proposed behaviour |
|---|---|---|
| **All 71 columns whose backward trace terminates in the census parse layer** (§F) | The source tables are unpopulated by any M3.2-authorized path | **FAIL CLOSED / OWNER REVIEW REQUIRED.** No evidence may be invented, no value defaulted, no network opened. The builder must refuse to write a candidate row it cannot source |
| `pilot_candidate_snapshots.coverage_policy_version` | No Python constant, no `reference_policy_versions` seed row, no decision assigns a value | **FAIL CLOSED — OQ-6.** The column is `NOT NULL` and sits inside `coverage_window_sha256` and therefore inside `snapshot_id`; a guessed value would silently fix the snapshot's identity |
| `census_structural_observations`-derived `schema_fingerprint_sha256` | Table unpopulated | **NOT a blocker** — D021 §8.1 defines the empty case — but **OQ-2** asks whether a uniformly uninformative fingerprint is acceptable at M3.3B |
| Amendment-purpose `provisional` classifications | Definitive purpose needs filing-body evidence, prohibited throughout M2.3 | Not a gap: `unproven` is the ordinary M2.3 value and can never satisfy an affirmative quota (D014 §6) |
| Filing-time SIC | Does not exist in any approved M2.3 source (D014 §3, audit blocker B2) | Not a gap: current-SIC provisional assignment is the accepted M2.3 position; M2.5 verifies |
| Difficult-or-nonstandard package quota | D018 §14 | Stays `unproven` / `unavailable`; **reported, never satisfied** (D026-L2) |

### G.3 What must not be done about §G.2

No reacquisition. No network. No new parsing of filing bodies. No CompanyFacts. No Frames. No
`inventory_*` fallback. No artificial population of `census_index_instances`. No manual fill, no best
effort, no discretionary default. If the acquired set proves insufficient, **that is a stop-and-refer
condition, never a licence to reopen the network** (master plan M3.3 §3; contract §7).

---

## H. Exact remaining owner questions

**None of these is answered here.** Each changes what the builder does, and each is an owner act.

> **ALL EIGHT ARE NOW ANSWERED — accepted Decision 067, 2026-08-13.** The table below is the record
> of what was **asked**, preserved unchanged. The answers are in the disposition block at the head of
> this document, in Decision 067 §§4–8, and in the corrected contract §§8.1, 10.1, 10.2. **Reading a
> row below as still open is a misreading of this document.**

| ID | Question | Bears on | If unanswered |
|---|---|---|---|
| **OQ-1** | Is the census parse layer in fact unpopulated? If so, what is authorized: (a) a bounded, network-free, offline parse of the already-stored raw objects through a **new** accepted path — which the current M3.3 contract §20 does not authorize and which would need its own decision record; (b) M3.3 fails closed and refers; or (c) something else? | **All of OR-2**, and whether M3.3A can be implemented at all | OR-2 cannot be ruled meaningfully — a mapping to an empty source is vacuous |
| **OQ-2** | Is a uniformly empty `schema_fingerprint_sha256` acceptable at M3.3B, given D021 §8.1 permits the empty case but the property it was designed to protect becomes uninformative? | `input_observation_set_sha256`, `source_observation_set_sha256`, the root | The real root would be constructed over a fingerprint that discriminates nothing |
| **OQ-3** | On a rebuild in the **same** catalog, `snapshot_id` collides on the primary key. Is production behaviour **fail-closed refusal**, or **recognize-and-return the existing snapshot**? Rehearsal E1's identical-`snapshot_id` criterion is satisfiable only across separate data roots | E1; the builder's insert path; R5 | The builder has no defined behaviour for its own determinism property |
| **OQ-4** | Parent-key convention: follow D021 §8.1 / D019 §6.6.1 (this proposal — `snapshot_id` **excluded** from the seven family digests, bound once in `candidate_snapshot_sha256`), or D021 §7.1 / §7.2 (**included** in every family tuple)? | All seven family digests, and every digest above them | Two accepted precedents point opposite ways |
| **OQ-5** | `source_observation_id` and `parsed_record_id` sit inside `evidence_sha256` per D016 §4, so an identical re-retrieval or reparse changes the candidate digests — while D021 §8.1 deliberately makes the observation-set digest immune to exactly that. Is that asymmetry intended, or should both be excluded from `evidence_sha256`? | `candidate_*_evidence_sha256`, `candidate_snapshot_sha256`, and D019 §10's run identity | Rebuild determinism across an identical reparse is undefined |
| **OQ-6** | What is `coverage_policy_version`'s value and its authority? No constant, seed row, or decision supplies one | `coverage_window_sha256` → `snapshot_id` → everything | The snapshot cannot be inserted without silently inventing an identity input |
| **OQ-7** | Is OR-1's ruling widened to cover the four §A.12 column-hash families — in particular `evidence_sha256`'s call shape and the seven `*_resolution_sha256` derivations, neither of which any accepted record fixes? | Every candidate row; migration `0009` makes both non-optional | The builder cannot write a single conforming row |
| **OQ-8** | Does the accepted evidence-role vocabulary need reconciling? D016 §4 illustrates roles as `primary` / `corroborating` / `conflicting`; migration `0009` `CHECK`s `winning` / `competing` / `supporting`, and D019 §§8.1.2, 10 use the migration's vocabulary. The migration governs the persisted contract, but the divergence should be recorded rather than left as a silent mismatch | `evidence_role`, and every digest containing it | A future reviewer sees two vocabularies for one field |

---

## I. Proposed acceptance-test obligations

Proposed only. Each is stated so that it fails for its own reason and cannot pass vacuously.

1. **Per-digest preimage pinning.** One test per digest in §A, asserting the exact `hash_table` name
   and the exact ordered column tuple, byte for byte. A reordering must fail.
2. **Inclusion non-vacuity.** For each of the 96 directly included columns, a test perturbing exactly
   that column and asserting the owning digest **and** `candidate_snapshot_sha256` both change.
3. **Exclusion non-vacuity.** For each of the 27 excluded columns, a test perturbing exactly that
   column and asserting **no** digest changes. `census_run_id`, every timestamp, every `detail`, and
   both `evidence_id` columns are each covered individually.
4. **D016 §1 property.** Two builds differing only in `census_run_id` produce identical `snapshot_id`
   and identical eleven digests.
5. **Cited-set equality.** A fixture whose planned citation set differs from the persisted evidence
   rows fails closed and leaves **no** snapshot row and **no** child row (R5).
6. **`input_observation_set_sha256` ≡ `source_observation_set_sha256`.** A test asserting the two are
   equal for a frozen snapshot, computed through the accepted §8.1 path and the freeze path
   independently.
7. **Structural fingerprint.** Identical reparse is a no-op; duplicate identical row is a no-op; a
   five-column disagreement between two parser runs raises `GateFailureError`; an observation with no
   structural rows yields the empty-set digest, distinct from any populated shape.
8. **Freeze-obligation coverage.** One test per Decision 019 §9 obligation, each failing for its own
   stated reason, none incidentally.
9. **Plain/dashed disagreement** fails closed (D018 §5.3).
10. **No second hashing implementation.** A test asserting that the builder module imports
    `release/hashing.py` and defines no `sha256`/normalization helper of its own.
11. **No operational value in any identity.** A scan asserting no path, no SEC identity, no timestamp,
    and no event ID reaches any digest, at any nesting depth.
12. **R3 write-freedom.** Durable bytes of every pre-existing artifact — main database file included —
    identical before and after every read-only path; every such path opens `SQLITE_OPEN_READONLY` and
    acquires **no** writer lease.
13. **`census_index_instances` untouched.** A test asserting the builder issues no read that depends
    on it and no write to it.
14. **`inventory_*` untouched.** A test asserting no builder query names an `inventory_*` table.
15. **The unchanged S4, S5, and S6 regression suites**, run without edits (contract §26 item **14**;
    it was item 10 when this was written, before the corrected contract added four categories).

## J. Proposed rehearsal obligations (E1–E8 additions)

Proposed only; additive to `Docs/m3/offline_rehearsal_spec.md` Part II, never a relaxation of it.

| Scenario | Proposed addition |
|---|---|
| **E1** | Recompute all eleven digests from persisted rows through a **separate** harness, not the builder's own code path; assert the `census_run_id` invariance property; exercise the **OQ-3** rebuild-collision branch once the owner rules it |
| **E2** | One fixture per Decision 019 §9 obligation, each violated in isolation and each failing for its own reason; plus the plain/dashed disagreement fixture |
| **E4** | R10: prove `infeasible` and `infeasible_or_unproven` are **distinct** outcomes, and that node-limit exhaustion is never labelled proven infeasibility |
| **E5** | Reserve and disposition totality across all three variants; item 46; item 70 |
| **E6** | Reconstruction mismatch refusal across every `JointSelectionRunIdentity` field, both public entry points equally strict |
| **E7** | R5: interruption injected at each of the four authoritative boundaries — snapshot freeze, selection persistence, sealing, manifest construction — proving no partial authoritative state survives, and that a pre-existing `building` row at entry **blocks** rather than being resumed, completed, repaired, invalidated, or superseded |
| **E8** | R3 durable-byte write-freedom on the main database file across every replay; identical re-seal idempotent; differing seal refused; **D023-O1 fails closed and is referred, never resolved** (R11 / OR-11) |
| **All** | Every scenario runs against an **isolated data root**, offline, on synthetic or real-shaped fixtures only, with `invocation_mode = "offline_execution"` and zero request counts; no socket opened; no accepted S4, S5, or S6 module modified to make a scenario pass |

---

## What this document does not do

It rules on nothing. It accepts nothing, approves nothing, and freezes nothing. It creates no
snapshot, computes no real digest, reads no private evidence, opens no catalog, and touches no
network. It resolves neither OR-1 nor OR-2, and it closes no limitation — **D021-L2** in particular
remains `ACTIVE` and blocking until the owner rules. A future session may not read any table above as
a ruling: the governing record each row cites is the authority, and where no record is cited, the
entry is a **proposal awaiting one**.

> **This section still stands, in the only sense that matters: this document is still not an
> authority.** What changed on 2026-08-13 is that the owner **has** ruled, by accepted
> [Decision 067](../Decisions/decision_067_m3_3_snapshot_authority_and_offline_parse.md), and that
> record — not this one — carries the rulings. **The entries above that no accepted record then
> supported are now supported by Decision 067, and must be cited to it.**
>
> **D021-L2 remains `ACTIVE`** and is **not** closed by the ruling: OR-1 supplies the derivation that
> was missing, and closure additionally requires the implemented recomputation-and-comparison step,
> reviewed. **No limitation is closed by Decision 067**, and one is added — **D067-L1**.
