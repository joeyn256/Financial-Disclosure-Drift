# Decision 012 — Accession observation resolution

**Status:** approved
**Date:** 2026-07-26
**Type:** implementation and provenance decision
**Stage:** Milestone 2, Stage M2.2-R2.3
**Supersedes:** nothing. Extends Decisions 008, 010, and 011 without altering them.
**Preregistration:** unchanged. This record defines *how* canonical accession fields are
derived from preserved observations. It does not change any hypothesis, cohort window,
maturity gate, outcome definition, threshold, or seed.

Policy version identifier: `accession-resolution/1.0`

---

## 1. Problem

A single accession is described by more than one official SEC source, and the same
source is retrieved more than once over the life of the project. Before this decision
the census took the first value written for each accession field and ignored later
disagreement. First-write-wins makes the canonical record depend on ingestion order,
which is not a property of the evidence, and it silently discards conflicts that ought
to stop the study.

## 2. Core principles

1. **Every source-native observation is immutable.** Resolution never edits, replaces,
   or deletes an observation. Conflicting observations are all retained.
2. **Canonical fields are derived views.** `census_accessions` holds a *projection* of
   the observation set. The observations remain the evidence.
3. **Resolution is deterministic and order-independent.** Running the same observation
   set in any ingestion order yields byte-identical canonical values, unresolved
   statuses, and resolution hashes.
4. **Recency is not authority.** A later retrieval time alone never promotes a value.
   Only an explicitly identified official correction, or a higher source-authority
   class, may supersede an earlier value.
5. **Authority is explicit.** Source class, correction evidence, snapshot version, and
   observation identity are recorded, never inferred at read time.
6. **Equal authority with conflicting values is unresolved.** The system does not guess,
   average, or prefer by timestamp.
7. **An unresolved material field blocks downstream use that depends on it.** Blocking
   is scoped to the dependency: an unresolved report date does not block work that does
   not read the report date.

## 3. Field-level resolution

Resolution is performed **per field**, never by choosing a whole-record winner. Two
sources may each be authoritative for different fields of the same accession, and a
correction may touch one field only.

Fields resolved independently:

| Field | Material | Notes |
|---|---|---|
`form` | yes | Drives eligibility and the amendment universe. |
`official_filing_date` | yes | Authoritative for cohort assignment (Decision 010). |
`report_date` | no | Conflicts stay unresolved and reviewed. |
`acceptance_timestamp` | no | Conflicts stay unresolved and reviewed; audit-only cohort. |
`registrant_cik` | yes | Never merged across CIKs. |
`submitter_cik` | no | Retained separately from the registrant CIK. |
`primary_document_metadata` | no | Metadata only; never turned into a URL. |
`amendment_relationship` | yes | Amendment identity and parentage. |

Acceptance timestamp and report date are **not** material for blocking cohort
assignment, but a conflict in either is still recorded, still unresolved, and still
requires review. They are not silently settled.

## 4. Source-authority classes

Narrowest official source closest to the filing metadata wins, subject to preserved
correction evidence.

| Class | Level | Sources | Status |
|---|---|---|---|
`filing_level_metadata` | 1 | Official filing-level or accession-level SEC metadata | **deferred** |
`entity_submissions` | 2 | `sec_submissions_entity`, `sec_submissions_historical`, `sec_bulk_submissions` | active |
`full_index` | 3 | `sec_full_index_company` | active |
`identity_alias` | 4 | `sec_company_tickers`, `sec_company_tickers_exchange` | aliases only |

**Level 1 is deferred for Stage M2.2.** Obtaining accession-level or filing-level
metadata would require retrieving an accession index page or a complete-submission
file, both of which Stage M2.2 prohibits. Resolution therefore begins at level 2. The
class is defined now so that adding it in a later milestone is a data change rather than
a policy change.

Level 4 carries **no filing-field authority whatsoever**. A ticker or exchange file may
never resolve a form, a date, or a CIK. It contributes identity aliases only, and a
shared ticker or name never merges two CIKs (Decision 007).

Within one class:

* an explicitly identified SEC correction, or a later official source *version*, may
  supersede an earlier value;
* an ordinary later retrieval of the same living source does **not** override a
  conflict unless the versioned policy identifies it as a correction;
* identical authority with conflicting values produces `unresolved`.

## 5. Correction evidence

A correction is an explicit, recorded artifact, not a heuristic. It is identified by
either a `DATE AS OF CHANGE`-style official change marker carried in the source
metadata, or a preserved correction observation identifier supplied to the resolver. A
value promoted by a correction records the correction evidence identifier, so any
canonical value can be traced to the artifact that justified it.

Absent correction evidence, two observations of the same living source that disagree are
a conflict, not an update.

## 6. Filing-date corrections and cohorts

When the resolved official filing date changes:

1. every prior filing-date observation is preserved;
2. the authoritative cohort is recomputed with the canonical temporal helper
   (`cohort_label_for_value`), never by hand;
3. prior cohort observations are retained alongside the new one;
4. date divergence is recorded (Decision 010);
5. cohort-boundary crossing is recorded where the cohort label changes;
6. **entry into or exit from the 2024 primary-test cohort requires explicit approval.**
   The resolver marks such a transition as requiring approval and blocks it until an
   approval marker is supplied. The 2024 cohort is not touched automatically.
7. the result is independent of ingestion order.

## 7. Persisted resolution output

For each accession and field, the catalog records:

* field name;
* resolved value, or `unresolved` with its status;
* resolution policy version (`accession-resolution/1.0`);
* winning observation identifiers where resolved;
* all competing observation identifiers;
* source-authority class of the winner;
* correction evidence identifier where one applied;
* conflict reason codes;
* resolution timestamp;
* deterministic resolution hash covering the ordered competing observation set, the
  policy version, and the outcome.

The resolution hash excludes the resolution timestamp, so re-resolving an unchanged
observation set reproduces the same hash.

## 8. Reason codes

| Code | Blocks release | Meaning |
|---|---|---|
`ACCESSION_FIELD_RESOLVED` | no | A single authoritative value was established. |
`ACCESSION_FIELD_RESOLVED_BY_CORRECTION` | no | An official correction superseded an earlier value. |
`ACCESSION_FIELD_UNRESOLVED_EQUAL_AUTHORITY` | yes | Equal-authority sources disagree. |
`ACCESSION_FIELD_CONFLICT_MATERIAL` | yes | A material field is unresolved. |
`ACCESSION_FIELD_CONFLICT_NON_MATERIAL` | no, review | A non-material field is unresolved. |
`ACCESSION_COHORT_BOUNDARY_CROSSED` | yes | A correction moved the accession across a cohort boundary. |
`ACCESSION_2024_COHORT_TRANSITION_REQUIRES_APPROVAL` | yes | Entry into or exit from the primary-test cohort. |
`ACCESSION_REGISTRANT_CONFLICT_PRESERVED` | yes | Registrant CIK observations disagree; no merge performed. |
`ACCESSION_SUBMITTER_DIFFERS_FROM_REGISTRANT` | no, review | Submitter and registrant CIK differ; retained as a review signal. |

## 9. What this decision does not do

* It does not merge CIK identities under any circumstance.
* It does not delete, overwrite, or reorder observations.
* It does not authorize retrieving accession index pages, primary documents,
  complete-submission files, or XBRL packages.
* It does not change any frozen cohort window, maturity gate, or the bootstrap seed.
* It does not modify `Docs/preregistration.md`.

## 10. Verification

Acceptance requires, for every conflict class, running the observation set in both
ingestion orders and asserting identical canonical values, identical unresolved
statuses, and identical resolution hashes. The classes covered are: corrected versus
original filing dates, equal-authority filing-date conflict, form conflict, registrant
conflict, submitter conflict, report-date conflict, acceptance-time conflict, amendment
relationship conflict, same-cohort correction, cross-cohort correction, entry into 2024,
and exit from 2024.
