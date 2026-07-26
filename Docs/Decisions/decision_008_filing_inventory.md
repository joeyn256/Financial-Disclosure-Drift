# Decision 008 — Filing Inventory and Amendment Policy

**Date:** 2026-07-25
**Status:** Approved by project owner
**Governs:** Milestone 2 onward
**Related:** Decision 007, Decision 009, Decision 010

## 1. Canonical filing identifier

The accession number is the canonical filing identifier. The inventory is **not** a flat CSV. It is a
normalized relational model with the following logical entities:

| Entity | Responsibility |
|---|---|
| `inventory_accessions` | One row per accession, with resolved temporal and eligibility state |
| `inventory_accession_registrants` | Accession-to-registrant edges; supports multiple registrants |
| `inventory_filing_documents` | Every document listed by the SEC accession index |
| `inventory_accession_observations` | Every source observation of accession metadata, append-only |
| `inventory_amendment_relationships` | Evidence-based links between accessions |
| `inventory_classifications` | Eligibility, issuer type, size stratum, industry, shell state |
| `inventory_reasons` | Reason-code assignments for eligibility, exclusion, and review |
| `inventory_company_aliases` | Time-bounded names and tickers |
| `inventory_company_lineage` | Successor and predecessor edges |
| `release_inventory_releases`, `release_membership` | Frozen release identity and contents |
| `raw_objects`, `raw_object_observations` | Raw-object lineage, per Decision 009 |
| `ops_retrieval_attempts`, `audit_parser_runs`, `audit_parser_failures` | Retrieval and parsing history |

## 2. Original and amendment rules

Every `10-K/A` and `10-KT/A` is a **separate accession**. An amendment must never:

- overwrite the original;
- replace its text;
- replace its XBRL;
- inherit the original timestamp;
- change the original cohort; or
- become an implicit "latest 10-K".

An amendment carries `inventory_role = amendment_non_target`, its own official filing date, its own
acceptance datetime, and its own authoritative and audit cohorts, per Decision 010 section 7.

### 2.1 Relationship states

Linkage must be evidence-based. Permitted states:

| State | Meaning |
|---|---|
| `amends_original` | Evidence links the amendment to a specific original accession |
| `amends_prior_amendment` | Evidence links the amendment to an earlier amendment |
| `supplements_original` | Evidence shows a supplemental relationship, not a replacement |
| `possible_amendment_of` | Candidate parentage with insufficient evidence to resolve |
| `unresolved_amendment` | Parentage cannot be established |

`possible_amendment_of` and `unresolved_amendment` both carry
`REVIEW_AMENDMENT_PARENT_UNRESOLVED`. Ambiguous parentage stays unresolved; it is never guessed.

### 2.2 Semantics that must not be conflated

- A `10-K/A` is **not** automatically a restatement.
- The XBRL amendment flag is **not** equivalent to the EDGAR `/A` form suffix. Both are recorded
  separately, and disagreement is a review condition, not a correction.
- An amendment accepted before its alleged original is `unresolved_amendment` plus review, never a
  silent reassignment.

## 3. 2009 support filings

Filings with an official filing date from 2009-01-01 through 2009-12-31 are inventoried as:

```text
temporal_cohort      = support_2009
inventory_role       = support_only
primary_target_flag  = false
```

Coverage is not automatically expanded before 2009. Missing prior support data remains missing: it
must never become zero disclosure change or any neutral value.

## 4. Eligibility roles

| Role | Reason code |
|---|---|
| Eligible original annual report | `ELIGIBLE_ORIGINAL_10K` |
| Eligible transition-period report | `ELIGIBLE_TRANSITION_10KT` |
| Support-only prior-year filing | `SUPPORT_ONLY` |
| Amendment, non-target | `AMENDMENT_NON_TARGET` |

Every non-eligible row carries at least one exclusion or review reason. No row may be excluded
without a reason, and no row may become eligible by default.

## 5. Observation and conflict policy

Accession metadata arrives from multiple sources at different times. Every observation is appended to
`inventory_accession_observations` with its source class, precedence rank, raw value, parsed value,
snapshot identity, and observation timestamp. Resolution produces a resolved value plus the source
used. Conflicting observations are preserved. Conflicts between co-authoritative accession-header
sources require review, per Decision 010 section 4.1.

Duplicate accession identity is rejected. Duplicate source observations of the same value are
recorded once per snapshot and never treated as new evidence of change.

## 6. Revisit triggers

Reopen if the SEC changes accession identity or index structure, if amendment evidence proves
insufficient at pilot scale to distinguish the five relationship states, or if multi-registrant
representation cannot be preserved without collapsing filings.
