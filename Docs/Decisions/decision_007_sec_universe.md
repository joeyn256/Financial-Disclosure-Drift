# Decision 007 — SEC Universe and Issuer Identity

**Date:** 2026-07-25
**Status:** Approved by project owner
**Governs:** Milestone 2 onward
**Related:** Decision 002 (primary outcome and company universe), Decision 008, Decision 009,
Decision 010

## 1. Canonical identity

CIK is the canonical issuer identifier. Every issuer row stores both:

| Field | Form |
|---|---|
| `cik_numeric` | Integer, no leading zeros |
| `cik_padded` | Ten-character zero-padded string |

Ticker symbols and company names are **time-bounded aliases**, never identity. They are stored in
`inventory_company_aliases` with the accession or snapshot that evidenced them.

The first ten digits of an accession number identify the **submitter** CIK. They must never be treated
automatically as the registrant CIK. An accession may have multiple registrants, each recorded in
`inventory_accession_registrants`.

## 2. Approved source hierarchy

1. SEC bulk Submissions archive
2. Quarterly and daily EDGAR master indexes
3. Per-CIK Submissions JSON
4. Accession archive package
5. Complete submission text and SGML header
6. Filing-level Inline XBRL or standalone XBRL
7. CompanyFacts, reconciliation only, disabled by default
8. Current ticker files, noncanonical aliases only

The design is bulk-first and accession-verified.

Prohibited as universe or point-in-time sources: current exchange membership, current ticker lists,
third-party company universes, current company names as canonical identity, CompanyFacts treated as
automatically point-in-time safe, and the SEC Frames API for point-in-time features.

## 3. Discovery forms

Discovered and inventoried: `10-K`, `10-K/A`, `10-KT`, `10-KT/A`.

`20-F`, `20-F/A`, `40-F`, and `40-F/A` are outside the eligible study universe. They may still be
stored as inventory rows carrying `EXCLUDED_UNSUPPORTED_FORM`, which is required so the pilot's
foreign-private-issuer negative control can exist as evidence.

## 4. Domestic issuer definition

"Domestic" means the issuer used the **domestic Form 10-K reporting regime for that accession**.
Eligibility is accession-specific and is never permanently attached to a CIK. A foreign-incorporated
issuer filing a valid Form 10-K is not excluded on incorporation grounds.

## 5. Historical coverage

Retained without exception: delisted, acquired, bankrupt, failed, and inactive issuers; issuers with
no current ticker; and issuers that changed name, ticker, SIC, or fiscal year end.

Predecessor and successor CIK histories are **never merged**. Mergers, acquisitions,
reorganizations, reverse mergers, de-SPAC events, and successor relationships are represented as
explicit edges in `inventory_company_lineage`, each with evidence and a reason code.

## 6. Sector and issuer-type rules

| Class | Treatment |
|---|---|
| Operating financial institutions | **Flagged**, not blanket-excluded. SIC 6000–6999 is not an automatic exclusion |
| Asset-backed issuers | Excluded, retained in the inventory with `EXCLUDED_ASSET_BACKED_ISSUER` |
| Registered investment companies, funds, ETFs | Excluded with `EXCLUDED_REGISTERED_INVESTMENT_COMPANY` |
| Shell and blank-check filings | Excluded with `EXCLUDED_SHELL_COMPANY` or `EXCLUDED_BLANK_CHECK_COMPANY` |
| Unknown classification | `review_required` with `REVIEW_UNKNOWN_ISSUER_TYPE` |

Shell classification is accession-specific. A CIK that was once a shell is not permanently excluded;
a post-de-SPAC transition receives `REVIEW_POST_DE_SPAC_TRANSITION`.

Every excluded or review row carries at least one machine-readable reason code. Unknown
classification must never produce silent eligibility.

## 7. Reference data

`reference_sic_codes` exists from Milestone 2.1 but is **not** populated from remembered values. The
official SIC reference data is loaded from an approved SEC source snapshot in Milestone 2.2. Any
policy-critical SIC constant used before then must carry explicit source metadata and must not
present itself as a complete taxonomy.

## 8. Revisit triggers

Reopen if the SEC changes form coverage or issuer-type disclosure, if observed shell or asset-backed
classification proves unreliable at pilot scale, or if lineage evidence is insufficient to represent
successor relationships without merging CIK histories.
