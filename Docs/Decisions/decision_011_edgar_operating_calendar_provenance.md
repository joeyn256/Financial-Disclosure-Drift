# Decision 011 — EDGAR Operating-Calendar Provenance

**Date:** 2026-07-26
**Status:** Approved by project owner
**Type:** Implementation and provenance decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged by this record.
**Governs:** Stage M2.2 onward
**Related:** Decision 007 (approved sources), Decision 009 (immutable observations),
Decision 010 sections 5.1–5.3 (rollover, frozen cutoff, non-operating-day acceptance)

## 1. Problem

Decision 010 makes `expected_after_cutoff_rollover` depend on a *proven* EDGAR
operating calendar. The SEC EDGAR Calendar page is an approved source, but one page
does not establish complete historical coverage for 2009 through 2026. Treating it as
a complete calendar would silently manufacture operating-day facts.

This decision replaces any implied "one page is the calendar" model with a versioned,
evidence-based derivation whose coverage is accounted date by date.

## 2. Tri-state day status

Every date resolves to exactly one of:

| Status | Meaning |
|---|---|
| `operating` | Official SEC evidence establishes that EDGAR operated on this date |
| `non_operating` | Official SEC evidence establishes that EDGAR did not operate |
| `unknown` | No sufficient official evidence exists for this date |

A Boolean calendar is prohibited. Every non-`unknown` determination retains one or
more source-observation identifiers and the derivation-rule version that produced it.

## 3. Approved evidence hierarchy

| Precedence | Evidence kind | What it can establish |
|---|---|---|
| 1 | **Date-specific SEC EDGAR announcement** — states EDGAR was closed, open, resumed operations, or treated a date as a filing holiday | Highest authority for the dates it names, `operating` or `non_operating` |
| 2 | **Annual EDGAR Calendar snapshot** | The listed federal filing holidays **only for the year that preserved snapshot explicitly covers**. Combined with precedence 3, other weekdays in that year become `operating` |
| 3 | **Official SEC general operating rule** — ordinary operations Monday through Friday except federal holidays | Weekends are `non_operating`. It does **not** by itself supply an unproven historical holiday list, so a weekday in a year with no preserved annual snapshot stays `unknown` |
| 4 | **Positive official EDGAR activity evidence** — official daily index, accepted submission, or equivalent preserved SEC metadata | `operating` for that date only. **Absence of activity never establishes `non_operating`** |

Conflict rule: when evidence disagrees, every observation is preserved, the date
resolves to `unknown`, and the release-blocking review reason
`REVIEW_CALENDAR_EVIDENCE_CONFLICT` is recorded. A conflict is never resolved by
source order alone.

## 4. Exceptional closures and exceptional operations

Special closures and special operating dates are represented explicitly and override
the ordinary weekday rule. Supported evidence types include one-off federal
observances, extra Christmas-period closures, newly recognized holidays, dates
treated as federal holidays for filing purposes, SEC announcements correcting filing
dates, and dates on which EDGAR remained operational despite broader government
disruption.

EDGAR closure is **never** inferred from: SEC offices being closed, a federal
government shutdown, an executive order closing executive departments, an absence of
filings, or a generic holiday library. Only EDGAR-specific SEC evidence may establish
an exceptional closure or an exceptional operating date.

## 5. Next-operating-day derivation

`next_operating_day(date)` returns a proven date only when **both** hold:

1. every intervening date is established `non_operating`; and
2. the returned date is established `operating`.

If any intervening or target date is `unknown`, the result is indeterminate: the
derivation raises rather than guessing, and the divergence classification falls to
`unexplained_date_divergence` with `OPERATING_CALENDAR_UNAVAILABLE`. An
indeterminate result can never support `expected_after_cutoff_rollover`.

Weekend status may be derived from the general operating rule. Historical federal
holidays and exceptional weekday closures require preserved official SEC evidence for
the relevant date or year.

## 6. Coverage accounting

Coverage is date-specific, never year-specific. Every derivation records:

- the requested coverage window;
- dates proven `operating`;
- dates proven `non_operating`;
- dates `unknown`;
- the evidence source or sources behind each determined date;
- dates with conflicting evidence;
- the parser or derivation version;
- the retrieval observations used;
- the first and last fully supported dates, if any.

A year is not "fully covered" because one annual calendar page or one closure
announcement was retrieved. Unknown dates may remain in the M2.2 census, but they
block automated rollover classification and, where relevant to an accession, block
release freezing.

## 7. Source registry corrections

1. The registered calendar location is the canonical SEC URL
   `https://www.sec.gov/submit-filings/filer-support-resources/edgar-calendar`.
   The older `/edgar/filer-information/calendar` path redirects; the HTTP layer still
   returns each redirect to the policy layer, which validates and records the hop
   before issuing the next request; the registry stores the canonical final location.
2. A distinct registered source category, `calendar_announcement`, covers exact SEC
   EDGAR closure or operating announcements. There is **no** unrestricted
   arbitrary-URL escape hatch: an announcement is retrievable only by its
   `evidence_id` in the reviewed manifest of section 8, must sit on an approved SEC
   host, is classified as calendar evidence, is stored as an immutable observation,
   and is tied to the exact affected dates.

## 8. Calendar evidence manifest

`src/disclosure_drift/sec/calendar_evidence.py` holds a versioned manifest. Each
entry records the evidence identifier, the exact official SEC URL, the affected date
or range, the asserted status, the evidence type, the title, the publication date when
available, the parser version, the source-observation relationship, and a review
status.

The manifest ships **empty of date assertions**. No date may be entered as operating
or closed without an official SEC source entry, so entries are added only after the
corresponding official evidence has been retrieved and reviewed. An entry whose
`review_status` is not `approved` supplies no determination.

## 9. Consequences for Decision 010

Decision 010 is unchanged. This record supplies the provenance and coverage rules
behind the calendar it already requires:

- rollover still requires a proven operating day, acceptance at or after the frozen
  17:30 America/New_York cutoff, and a filing date equal to the next operating day;
- a purported acceptance on a proven non-operating day still yields
  `REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY`;
- an `unknown` acceptance or target date now yields `OPERATING_CALENDAR_UNAVAILABLE`
  rather than an assumed answer.

## 10. Revisit triggers

Reopen if the SEC publishes a machine-readable operating calendar with historical
coverage, if the canonical calendar URL changes again, if conflicting evidence appears
at a material rate, or if `unknown` coverage is wide enough to affect cohort
composition.
