# M3.3 Decision-091 Single-Pass Document-Evidence Review — Review A (Claude Opus 5)

```text
OUTCOME: M3_3_DECISION_091_SINGLE_OPUS_EVIDENCE_REVIEW_COMPLETE_READY_FOR_OWNER_ADJUDICATION
PROTOCOL_VERSION: m3.3-document-evidence/1.0
REVIEWER_ROLE: review_a          REVIEW_PASS: A          REVIEWER_MODEL: claude-opus-5
REVIEW_EPOCH_ID: 2a99c067d0df79421d4d52a1e46f863bccec8727db6a7b7de9b0ea55d18b2e62
REVIEW_A_TABLE_SHA256: d9c9d9c79a75d7808e09094fdafa189128ae522d884bb88c8fb28f0e40d89c4f
ARTIFACT_TABLE_SHA256: b84495a40b23fdc77c70c537b8cf6c9bd7675b90493fc73d55841a2ac425174e
ARTIFACTS: 108   REVIEW RECORDS: 108   SPANS: 302
PURPOSE: 99 asserted / 9 abstained
EXPLICIT ORIGINAL: 102 form / 96 date / 0 accession / 6 fully abstained
REVIEW_B: NOT EXECUTED / NOT AUTHORIZED
CLAUDE_ADJUDICATION: NOT EXECUTED / NOT AUTHORIZED
document_adjudicated_evidence ROWS: 0
VERIFIED CREDIT GRANTED: NONE     FEASIBILITY GATES CLOSED: NONE
E0 / E1 / E2 / M3.4 AUTHORIZATION: NO
NETWORK / SEC / HTTP: NONE — 0 requests, 0 attempts
```

**This artifact is review evidence, not an acceptance.** It records one independent Claude Opus 5
maximum-effort pass over all 108 frozen Decision-081 Complete Submission Text artifacts under
[Decision 091](../../Decisions/decision_091_m3_3_single_pass_document_evidence_protocol.md). It
closes no gate, grants no quota credit, and adjudicates nothing on the owner's behalf. Sol/GPT owner
adjudication is the next act.

---

## 1. Model, effort, and epoch attestation

| Fact | Value |
|---|---|
| Harness / model identifier | `claude-opus-5` (Claude Opus 5) |
| Presented model | Claude Opus 5 |
| Effort | Maximum |
| Epoch | Fresh `/clear`, one active session |
| Subagents / delegation / parallel workflows | **None used** |
| Network, SEC, HTTP | **None** — zero requests, zero attempts, zero new artifacts |
| Private evidence root | **READ ONLY**; no write, no artifact or receipt modification |
| Repository bytes during review | Unchanged until this artifact was published |

## 2. Entry state — verified live by Git

| Fact | Value |
|---|---|
| Branch | `main`, `HEAD == origin/main` |
| `HEAD` | `d213d889d8e92bb67c5858346467e18ea61e2aca` |
| Tree | `8467035e1d52454bac91e52c94b8f25b225284ab` |
| Parent | `f76639dc0603f6598c5525f652208ccf49b69b53` |
| Frozen accepted verified-evidence implementation | `746648285ec84d54a2ed7deaebc73f5c64b89d3d` |
| `m3.2-complete` annotated tag object | `2865a1479e4576dc18a4098c928b278812f38d00`, unmoved |
| Working tree at entry | CLEAN |
| Migrations | `0001`–`0015` contiguous; `0016` ABSENT |

No fetch, pull, reset, clean, or stash was performed.

## 3. Frozen artifact-set binding

Every artifact was bound by accession, SHA-256, and public source identity from the frozen
Decision-081 run before any substantive review, and re-verified by rehashing the bytes.

| Fact | Value |
|---|---|
| `EXPECTED_ARTIFACTS` | **108** |
| `sample_plan_sha256` | `ad2205dc41c5915f50188f3ddad57428d57f02ec1c9125c1b5e3d1d0691f3a23` |
| `sample_accession_set_sha256` | `d31aa49399045700dc9f0b0b59e6c139d6b98cd9c3ace93162fd70d8046415e8` |
| `artifact_manifest_sha256` (D081 receipt) | `50904ba1057a7e7168f6674327acc2e31bf6f66318d248208660be0839cd332d` |
| Sample-plan rows == measurement rows == artifact files | 108 == 108 == 108 |
| Recomputed SHA-256 matches the frozen receipt | **108 / 108** |
| Aggregate bytes recomputed vs receipt | 346,654,301 == 346,654,301 |

No artifact was substituted, added, dropped, re-downloaded, or replaced from another source. The
absolute private evidence-root path is neither printed nor persisted anywhere in this artifact, in
the catalog, or in any governed value.

## 4. Method

Each artifact's primary document was located by SGML sequence, rendered to readable prose with a
per-character map back to the artifact's own byte offsets, and read. Anchor search decided only
**which regions of a document the reviewer read** — for six documents that meant a full-document
scan when the ordinary regions carried no amendment discourse. **Every category and every original
assertion is a judgment on the issuer's own words, and each carries an exact artifact byte span.**
No keyword, substring, regex, filename, `primaryDocDescription`, or form-suffix rule assigned any
value, and no classifier was built or used (Decision 071 **IN-2** and Decision 082 §12.3 stand).

Two interpretive standards were applied consistently and are stated so the owner can accept, reject,
or refine them:

* **S-1 multi-purpose.** A single category is asserted where the issuer's own statement identifies
  ONE purpose as the reason for filing and further items are incidental to or consequential upon it.
  Where the issuer states two or more INDEPENDENT purposes falling in different frozen categories and
  neither is subordinate, the record **abstains** `ambiguous_text` — the frozen protocol supplies no
  dominance rule, and inventing one would be new methodology.
* **S-2 exhibit vehicle.** Where the entire operative act is filing, re-filing, or updating exhibits
  and no report-body disclosure is amended, the category is `administrative_or_exhibit` — unless the
  exhibit supplies or corrects substantive financial-statement, accounting, or XBRL content, which is
  `financial_or_xbrl_correction`.

Single-purpose documents whose category boundary is genuinely arguable were **asserted and flagged**
rather than abstained, with the competing category and the reason for rejecting it recorded per
document. 32 records carry that `high_judgment` flag and every one is listed in §12.

## 5. Totality proof

| Check | Result |
|---|---|
| `EXPECTED_ARTIFACTS` | 108 |
| `REVIEWED_ARTIFACTS` | **108** |
| `MISSING` | **0** |
| `EXTRA` | **0** |
| `DUPLICATE_REVIEW_A_RECORDS` | **0** |
| `ARTIFACT_SHA_MISMATCHES` | **0** |
| `CROSS_ACCESSION_ARTIFACT_BINDINGS` | **0** |
| `PROTOCOL_VERSION_MISMATCHES` | **0** |
| `POSITIVE_ASSERTIONS_WITHOUT_REQUIRED_SPANS` | **0** |
| `INVALID_SPAN_HASHES` | **0** |
| `INVALID_SPAN_LOCATIONS` | **0** |

No artifact was skipped. Every difficult document is a recorded abstention, never an omission
(Decision 080 **AP-1**).

## 6. Source-span integrity

All 302 spans were re-verified against the frozen artifacts: each `bytes:START-END` location lies
inside its artifact, the bytes at that location decode to exactly the stored verbatim text, each
span digest recomputes through `document_evidence.span_sha256`, and each span supports an assertion
its own record makes. Spans are raw artifact byte ranges, so a span over an HTML primary document
contains that document's markup — that is the exact source, not a rendering of it.

## 7. Amendment-purpose results — REVIEW-A-ONLY

| Outcome | Count | Share |
|---|---:|---:|
| **Asserted** | **99** | 91.7% |
| — `administrative_or_exhibit` | 42 | 38.9% |
| — `narrative_or_governance` | 36 | 33.3% |
| — `financial_or_xbrl_correction` | 21 | 19.4% |
| **Abstained** | **9** | 8.3% |
| — `insufficient_text` | 5 | 4.6% |
| — `ambiguous_text` | 4 | 3.7% |

Five records carry more than one purpose span where the issuer's statement is evidenced in two
places. Distinct accessions equal record counts in every category — 42, 21, and 36 — because the
schema admits exactly one Review-A record per accession.

## 8. Explicit-original results — REVIEW-A-ONLY

| Outcome | Count |
|---|---:|
| Any original assertion | **102** |
| Original **form** asserted | **102** (96 × `10-K`, 6 × `10-KT`) |
| Original **filing date** asserted | **96** |
| Original **accession** asserted | **0** |
| **Form and date together** (X-2 + X-3 pair) | **96** |
| Form asserted, date absent (partial) | 6 |
| Fully abstained (`insufficient_text`) | 6 |

`original_accession_asserted` is **0 / 108**, independently reproducing Decision 082 §12.4 rule
**X-4**'s measurement. The protocol's decision not to depend on the stated accession is confirmed by
this pass rather than assumed from D081.

## 9. Cross-tabulated diagnostics

| Split | n | purpose asserted | form + date | both questions abstained |
|---|---:|---:|---:|---:|
| **Form** `10-K/A` | 98 | 93 | 90 | 2 |
| **Form** `10-KT/A` | 10 | 6 | 6 | 3 |
| **Cohort** development | 52 | 46 | 43 | 4 |
| **Cohort** transition | 18 | 18 | 17 | 0 |
| **Cohort** primary_test | 13 | 12 | 12 | 1 |
| **Cohort** prospective | 13 | 12 | 13 | 0 |
| **Cohort** monitoring | 12 | 11 | 11 | 0 |
| **XBRL** X0 | 58 | 53 | 51 | 2 |
| **XBRL** X1 | 19 | 16 | 15 | 3 |
| **XBRL** X2 | 31 | 30 | 30 | 0 |
| **Registrants** single | 92 | 83 | 80 | 5 |
| **Registrants** multi | 16 | 16 | 16 | 0 |

The `10-KT/A` and `X1` strata carry a visibly higher abstention rate, driven by four older
small-filer documents that contain no amendment statement at all. **These are diagnostics; no review
decision was altered on the strength of any distribution.**

## 10. REVIEW_A_ONLY_FEASIBILITY_PREVIEW — amendment purpose

**This is not a gate verdict.** Only Sol/GPT may determine whether the amendment-purpose feasibility
gate closes.

All **three** frozen categories appear at least once in this review, each with source-backed
witnesses:

| Frozen category | appears | count | distinct accessions |
|---|---|---:|---:|
| administrative / certification / signature / exhibit-only | **yes** | 42 | 42 |
| financial-statement / accounting / restatement / XBRL correction | **yes** | 21 | 21 |
| narrative / business / risk / control / governance disclosure | **yes** | 36 | 36 |

Each category's witnesses span multiple cohorts and both amendment forms, and the three strongest
witnesses per category quote the issuer characterising the amendment in the category's own terms —
including one filing that describes itself verbatim as "an exhibit-only filing"
(`000117015413000083`) and another as "This Amendment is an exhibit-only filing"
(`000175392626000935`).

## 11. REVIEW_A_ONLY_FEASIBILITY_PREVIEW — linkage

**This is not a gate verdict, and no linkage is established here.** The review records what each
filing *asserts* (**X-6**); resolution against the accepted catalog is a separate later step.

| Diagnostic | Value |
|---|---:|
| Accessions asserting an accepted original form **and** an explicit filing date | **96** |
| Distinct registrant-association **sets** among those 96 | **95** |
| Distinct substantive CIKs among those 96 | **104** |
| Of the 96, multi-registrant accessions | 16 |
| By cohort | development 43, transition 17, prospective 13, primary_test 12, monitoring 11 |
| By form | `10-K/A` 90, `10-KT/A` 6 |

**`ZERO` / `EXACTLY_ONE` / `MULTIPLE` resolution is NOT computed and NOT reported.** The **R52**
association-set diagnostic resolves an asserted original against the accepted catalog, and no
accepted catalog of originals exists — M3.3-E0 has not run and is not authorized. The only
already-computed split available is D081's mechanical **M9**, which §11 of the review packet forbids
using as an evidence label and which Decision 082 **R53** already superseded for this purpose.
Computing the split from anything else would be inventing linkage, so it is left to owner
adjudication after E0.

The distinct-entity figures above are counted from the frozen D081 registrant-association metadata,
not from any linkage inference. They describe how many entities the candidate set *touches*; they do
**not** assert that any candidate resolves to a real original.

### E. Purpose-category witness table

Three source-backed witnesses per category; every asserted record carries its own span and all
are listed in Appendix A.

| category | asserted | distinct accessions | witness accession | span | issuer text |
|---|---:|---:|---|---|---|
| administrative_or_exhibit | 42 | 42 | `000000314614000009` | `bytes:17310-17425` | is being filed solely to include Exhibits 31 and 32, which were inadvertently omitted from the initial filing. |
|  |  |  | `000004907113000063` | `bytes:22909-23135` | Due to a scrivener’s error, the index to the Form 10-K filed under Item 15 did not clearly denote that Exhibit 10(t) was filed under a request for con… |
|  |  |  | `000087476125000029` | `bytes:37816-37983` | is being filed (i) to include those exhibits listed above that were inadvertently omitted from the Original Filing, and (ii) to correct the hyperlink … |
| financial_or_xbrl_correction | 21 | 21 | `000114036122002604` | `bytes:48184-48280` | to restate our financial statements as of and for the period ended December 31, 2020 |
|  |  |  | `000114420410068455` | `bytes:25691-25762` | to amend information included in “Item 6. Selected Financial Data |
|  |  |  | `000121390021033594` | `bytes:29469-29574` | to amend and restate certain items of its Annual Report on Form 10-K for the year ended December 31, 2020 |
| narrative_or_governance | 36 | 36 | `000095012311006537` | `bytes:10523-10600` | is being filed solely to replace Part III, Item 10 through Item 14. |
|  |  |  | `000095017024086880` | `bytes:36364-36712` | The purpose of this Amendment is solely to disclose the information required in Part III (Items 10, 11, 12, 13 and 14) of Form 10-K, which information… |
|  |  |  | `000095017025062260` | `bytes:57885-59460` | this Amendment No. 1 is being filed solely to: • delete the reference on the cover page of our 2024 Annual Report to the incorporation by reference of… |

### F. Potential linkage witness table

96 accessions assert **both** an accepted original form and an explicit original filing date.
Ten shown; all 96 are flagged in Appendix A and none is granted linkage credit here.

| accession | form | cohort | reg | original | form span | date span |
|---|---|---|---:|---|---|---|
| `000000314614000009` | 10-KT/A | development | 1 | 10-KT / 2014-11-25 | `bytes:17098-17164` | `bytes:17234-17281` |
| `000095012311006537` | 10-KT/A | development | 1 | 10-KT / 2010-12-29 | `bytes:10323-10374` | `bytes:10438-10487` |
| `000107997323000590` | 10-K/A | transition | 1 | 10-K / 2023-03-31 | `bytes:23063-23117` | `bytes:23221-23302` |
| `000119312510239802` | 10-K/A | development | 1 | 10-K / 2010-08-30 | `bytes:16529-16566` | `bytes:16613-16713` |
| `000119312515224858` | 10-K/A | development | 3 | 10-K / 2015-03-31 | `bytes:16661-16790` | `bytes:16661-16790` |
| `000119312526124739` | 10-K/A | monitoring | 1 | 10-K / 2026-03-25 | `bytes:16622-16688` | `bytes:16745-16837` |
| `000127653125000005` | 10-K/A | prospective | 1 | 10-K / 2024-04-16 | `bytes:17179-17297` | `bytes:17179-17297` |
| `000147793224002311` | 10-K/A | primary_test | 1 | 10-K / 2024-04-17 | `bytes:90431-90468` | `bytes:90514-90548` |
| `000162045926000022` | 10-K/A | monitoring | 1 | 10-K / 2026-03-03 | `bytes:29725-29758` | `bytes:29842-29937` |
| `000173112223001487` | 10-K/A | transition | 1 | 10-K / 2023-03-29 | `bytes:23631-23664` | `bytes:23686-23719` |

### G. All abstentions, grouped by reason


**amendment purpose — `ambiguous_text` (4)**

- `000035729411000004` (10-K/A, development) — Two of the three frozen categories are independently and explicitly asserted: (a) 'We are filing this Amendment to include the information required by Part III and not included in the Original Filing' (narrative_or_governance) and (b) 'This Amendment also includes an adjustment to assets for the Northeast and Mid-Atlantic segments ... in the Notes to Consolidated Financial Statements to correct a misclassification' (financial_or_xbrl_correction). The frozen protocol supplies no dominance or primary-purpose rule, so selecting one would be new methodology.
- `000095012310102209` (10-KT/A, development) — Three co-equal stated purposes spanning two frozen categories: (i) 'amend the report of the Company's independent auditors included in Item 8 of the Original Filing to opine on the period from inception to March 31, 2009' (financial-statement/audit content, and the issuer states the amendment 'only amends Item 8 of Part II and Item 15 of Part IV'), against (ii) filing compensation agreements as exhibits and (iii) amending the Exhibit 31.1/31.2 certifications (administrative_or_exhibit). The protocol supplies no dominance rule.
- `000137647410000009` (10-K/A, development) — Five enumerated changes spanning all three frozen categories, none subordinate: (a) format changed from the 10-KSB format to the 10-K format (administrative); (b) 'the Financial Statements and Notes, which were left out of Amendment No. 1 in error, have been included' and (c) the Subsequent Events note revised (financial_or_xbrl_correction); (d) and (e) Item 9A disclosure-controls and ICFR disclosures revised to state that controls and ICFR were not effective (narrative_or_governance). The protocol supplies no dominance rule.
- `000190359626000081` (10-K/A, monitoring) — Two independent purposes in different frozen categories, presented co-equally: '(i) include the certifications of the Company's Chief Financial Officer required by Rules 13a-14(a) and 15d-14(a) ..., which were not included in Amendment No. 1' (administrative_or_exhibit -- and here the certifications are a defect being repaired, not the routine Rule 12b-15 accompaniment) and '(ii) include the Executive Compensation section that was not previously included' (narrative_or_governance). The protocol supplies no dominance rule.

**amendment purpose — `insufficient_text` (5)**

- `000089016324000008` (10-K/A, primary_test) — The 10-K/A primary document is a complete annual report whose cover page reads 'Form 10-K'. A full-document scan of the primary document prose (185,280 chars) finds zero occurrences of '10-K/A', 'Amendment No', 'this Amendment', 'amends', 'Explanatory', 'originally filed', or 'Original Filing'. There is no issuer statement of what is amended or why.
- `000113902025000123` (10-K/A, prospective) — Amendment No. 3 on the cover page, but a full-document scan of the 75,666-char primary document finds no explanatory note and no statement of what is amended or why: 'this Amendment' 0 hits, 'originally filed' 0, 'Original Filing' 0, 'purpose of this' 0, 'restat' 0; the single 'explanatory' hit is 'other explanatory information' inside an auditor compilation report.
- `000116552710000897` (10-KT/A, development) — Full-document scan of the 182,851-char primary document: 'Amendment No' appears once, on the cover page ('Amendment No. 1 To FORM 10-KSB'); 'this Amendment' 0, 'originally filed' 0, 'Original Filing' 0, 'purpose of this' 0, 'being filed' 0. The three 'explanatory' hits are all 'explanatory paragraph' in going-concern audit-report discussion. No statement of what is amended or why.
- `000154972720000065` (10-KT/A, development) — Full-document scan of the 96,398-char primary document: 'EXPLANATORY' 0, 'Explanatory' 0, 'Amendment No' 0 (the cover heading 'AMENDMENT NO.3 to FORM 10-K' is rendered without the space), 'originally filed' 0, 'original filing' 0, 'purpose of this' 0, 'being filed' 0. The single 'restat' hit is 'prior period results have not been restated' in an accounting-standards note. The document self-labels as an 'Amended Annual Report' but never states what is amended or why.
- `000168316820002798` (10-KT/A, development) — Full-document scan of the 124,845-char primary document: 'Explanatory' 0, 'this Amendment' 0, 'originally filed' 0, 'Original Filing' 0, 'purpose of this' 0, 'being filed' 0. 'Amendment No' appears once, in the cover heading 'Amendment No. 1 to FORM 10-KT'. The six 'amend' hits are the cover-page boilerplate, an accounting-standards note, three stock-plan amendments, and 'the Exchange Act, as amended'. No statement of what is amended or why.

**explicit original — `insufficient_text` (6)**

- `000089016324000008` (10-K/A, primary_test) — No explicit identification of an original filing anywhere in the document.
- `000105291817000332` (10-K/A, development) — The document explicitly identifies what it amends -- 'its Amendment No. 1 of Annual Report on Form 10-KSB for the fiscal year ended May 31, 2007 (filed with the Securities and Exchange Commission on September 19, 2007)' -- but the named original form is Form 10-KSB, which Decision 080 R44 excludes from the accepted compatible originals (10-K / 10-KT only, with 10KSB named in the exclusion). The named target is also a prior AMENDMENT, not an original. No accepted-form original is identified anywhere, so X-2 cannot be satisfied.
- `000116552710000897` (10-KT/A, development) — No explicit identification of an original filing. The only Form 10-KSB filing reference is an exhibit incorporation-by-reference to a 2004 code-of-ethics exhibit, which identifies neither this report's original nor an accepted compatible form.
- `000137647410000009` (10-K/A, development) — No accepted-form original is explicitly identified. The document states the format was changed FROM the 10-KSB format, and 10-KSB is excluded by Decision 080 R44; the only prior filing named is 'Amendment No. 1'. A full-document scan finds zero occurrences of 'originally filed' or 'original filing', and no filing date for any original.
- `000154972720000065` (10-KT/A, development) — No explicit identification of an original filing and no filing date anywhere in the document.
- `000168316820002798` (10-KT/A, development) — No explicit identification of an original filing and no filing date anywhere in the document.

### J. Partial explicit-original evidence — form asserted, filing date absent (6)

| accession | form | cohort | asserted form | form span | issuer text |
|---|---|---|---|---|---|
| `000121390022030740` | 10-K/A | transition | 10-K | `bytes:27500-27533` | to its Annual Report on Form 10-K |
| `000135968712000022` | 10-KT/A | development | 10-KT | `bytes:23556-23611` | This Amendment No. 1 to the Annual Report on Form 10-KT |
| `000136086513000110` | 10-K/A | development | 10-K | `bytes:18394-18477` | There is no other material change to the 10-K for the year ended December 31, 2012. |
| `000152013815000055` | 10-K/A | development | 10-K | `bytes:16707-16739` | the original filing on Form 10-K |
| `000161041816000067` | 10-K/A | development | 10-K | `bytes:20633-20686` | to its Form 10-K for the year ended December 31, 2015 |
| `000173112226000061` | 10-K/A | monitoring | 10-K | `bytes:16031-16064` | to its Annual Report on Form 10-K |

### K. Structural conflicts between document text and frozen metadata

| accession | header form | condition |
|---|---|---|
| `000095012310102209` | 10-KT/A | document cover names a different form from the SEC submission header |
| `000101041213000014` | 10-KT/A | original form named in a typographic variant |
| `000105291817000332` | 10-K/A | named original form is outside the R44 accepted set; document cover names a different form from the SEC submission header |
| `000109690623001694` | 10-K/A | original form named informally |
| `000116552710000897` | 10-KT/A | document cover names a different form from the SEC submission header |
| `000127653125000005` | 10-K/A | amendment target is a prior amendment; original evidence taken from a separate issuer sentence |
| `000137647410000009` | 10-K/A | named original form is outside the R44 accepted set |
| `000152013815000055` | 10-K/A | D081 mechanical extractor produced a date this review rejects under X-3 |
| `000168316824002854` | 10-K/A | original form named in a typographic variant |

### H / I. High-judgment cases, and documents where more than one category was considered

32 records are flagged `high_judgment`; each records the competing category and why it was rejected.
The recurring boundaries, with the standard applied:

| Boundary | Accessions | Disposition |
|---|---|---|
| Exhibit vehicle vs financial-statement content | `000082148320000021`, `000172617325000021` | **cat 2** — Rule 3-09 audited financial statements required by Regulation S-X |
| Exhibit vehicle vs financial content | `000035089424000030`, `000103835712000037` | **cat 1** — clerical/derived correction, issuer states no financial effect |
| XBRL furnished vs XBRL *corrected* | `000119312512462631`, `000121390020012521`, `000136086513000110`, `000171254322000127` | **cat 1** — furnished first time; contrast `000101041213000014` (corrected XBRL) = **cat 2** |
| Reg AB servicing-compliance: body vs exhibit | `000119312513372376`, `000119312516633188` (**cat 3**, body Part III amended) vs `000119312514076334`, `000119312514076381`, `000119312516686295`, `000119312516686403`, `000119312516686413` (**cat 1**, exhibits only) | textual: whether report-body disclosure is amended |
| Wrong audit report vs unsigned audit report | `000147793224002311`, `000173112226000061` (**cat 2**) vs `000143774924021940` (**cat 1**) | wrong content vs missing signature |
| Date typo inside a financial/control item | `000121390022030740`, `000138119726000072` | **cat 1** — only a date changes; contrast `000147793223008817` (substantive Item 9A replacement) = **cat 3** |
| Governance content delivered as an exhibit | `000132587823000121` | **cat 1** — audit-committee-report exhibit substitution, no body change |
| Cause vs scope | `000143774921008101` | **cat 1** — one stated purpose, an EDGAR transmission failure, though the restored content spans all three categories. **The single clearest cause-versus-scope case in the set.** |
| Evidence outside the explanatory note | `000113902025000123` | original form + date taken from an exhibit-index footnote |
| Self-reference vs X-5 conflict | `000121390022011106` | "Form 10-K/A" read as the amendment describing itself, not a conflicting original-form statement |

The four `ambiguous_text` abstentions in §G are the documents where two or more frozen categories
were independently asserted by the issuer and the protocol supplied no way to choose.

## 12. Review freeze and digests

The complete pass was frozen and content-addressed through the accepted evidence infrastructure —
migrations `0001`–`0015` as the persisted contract and
`disclosure_drift.m3.document_evidence` for every digest, under the accepted
`REVIEW_A_TABLE_DOMAIN`. No schema byte, source byte, or test byte was changed.

| Artefact | Value |
|---|---|
| `REVIEW_A_TABLE_SHA256` | `d9c9d9c79a75d7808e09094fdafa189128ae522d884bb88c8fb28f0e40d89c4f` |
| `ARTIFACT_TABLE_SHA256` | `b84495a40b23fdc77c70c537b8cf6c9bd7675b90493fc73d55841a2ac425174e` |
| `review_epoch_id` | `2a99c067d0df79421d4d52a1e46f863bccec8727db6a7b7de9b0ea55d18b2e62` |
| Epoch preimage | `m3.3-document-evidence/1.0\|review_a\|claude-opus-5\|<sample_plan_sha256>\|<sample_accession_set_sha256>\|<artifact_manifest_sha256>\|decision-091-single-opus-pass` |
| `reviewer_model` | `claude-opus-5` |
| `protocol_version` | `m3.3-document-evidence/1.0` |
| Artifact rows / review rows / span rows | 108 / 108 / 302 |
| `document_review_records` where `reviewer_role <> 'review_a'` | **0** |
| `document_adjudicated_evidence` rows | **0** |

The review-epoch identifier is opaque and derived only from governed values; **no personal reviewer
name and no raw Claude session ID is persisted anywhere.**

**One freeze correction, disclosed in full.** The first freeze attempt derived `review_id` as the
record digest over a tuple containing `review_id` itself, so the stored `review_record_sha256` was
not reproducible from the persisted row. The §21 validation caught it, and the identity derivation
was corrected — `review_id` is now `sha256(review_epoch_id | accession)` and
`review_record_sha256` is the digest over the completed row, so both recompute independently. **No
judgment, category, assertion, abstention, or span text changed**; the judgment ledger is
append-only and was untouched. The superseded table digest was
`f88213cac883820bf04f34708dbbefb01cc5d03e6de92fcdc73aad68189d5b76`; the frozen value of record is
`d9c9d9c7…`. This is reported rather than silently replaced.

## 13. Schema and persistence validation

34 read-only checks, all passing:

* `PRAGMA integrity_check` = ok; `PRAGMA foreign_key_check` empty; migration chain `0001`–`0015`
  contiguous with `0016` absent.
* Totality 108 / 108 / 302; reviewed set equals artifact set; zero cross-accession artifact bindings;
  every artifact SHA equal to the frozen D081 value.
* All 302 spans located byte-exactly, all span digests reproducible, every span supports an
  assertion its record makes, every positive assertion carries its required span, abstained records
  assert nothing.
* Per-record and per-table digests reproducible from the persisted rows; the table digest is
  order-independent under a shuffled row set.
* Zero Review-B rows, zero adjudication-role rows, zero adjudicated-evidence rows, exactly one
  review epoch, protocol version pinned on every row.
* Append-only enforcement exercised on a disposable copy: UPDATE and DELETE refused on all four
  relations, and `INSERT OR REPLACE` and duplicate `(accession, role)` inserts both refused.
* Private-root nonleakage: no governed value carries a path character, no `$HOME` byte and no
  evidence-root directory name appears anywhere in the catalog file, every `source_url` is a public
  EDGAR archive URL, every timestamp matches the timestamp shape, every span location is a canonical
  decimal byte range.

No implementation mutation campaign was run: migration `0015` is already independently reviewed and
owner-accepted, and this epoch is evidence production.

## 14. Findings

**BLOCKER 0 — MAJOR 0 — MINOR 0 — OPTIMIZATION 0 — OBSERVATION 3.**

* **OBS-1 — the accepted record shape carries one abstention flag for two evidence questions.**
  `document_review_records` has a single `abstained` / `abstention_reason` pair, but the protocol
  asks two independent questions per artifact. 96 records assert explicit-original evidence while
  6 of those abstain on purpose, and 6 assert purpose while abstaining on the original. The accepted
  schema was used **as accepted**: `abstained = 1` only where the record asserts nothing at all
  (3 records), and a per-question abstention on a record that asserts the other question is carried
  as a NULL value with its reason recorded in this artifact. **Non-gating**, and no schema change is
  proposed or made — but the owner should know that per-question abstention reasons for mixed
  records live here rather than in the relation.
* **OBS-2 — `require_no_private_path` is not applicable to six governed columns.** The helper
  refuses `/`, `\`, `:`, and `~`. Six governed columns legitimately contain one of those:
  `source_url` and `span_text_verbatim` (documented), plus `retrieved_at_utc`, `decided_at_utc`
  (ISO-8601 `:`), `protocol_version` (`m3.3-document-evidence/1.0`), and `span_location`
  (`bytes:START-END`). Each is independently pinned by migration `0015`'s own shape CHECK, so
  nonleakage is not weakened — but the module docstring names only the URL exception, and a future
  writer applying the helper column-wise would get four spurious failures. **Non-gating,
  documentation-level; no code change made or proposed.**
* **OBS-3 — the D081 mechanical original-date extractor is confirmed defective on a concrete case.**
  For `000152013815000055` that extractor recorded `2013-08-26`, which is the **change-in-control
  date** in the issuer's own sentence, not a filing date; **X-3** forbids the substitution, and this
  review asserts the form with no date. This independently corroborates Decision 082 **R53** and is
  recorded as evidence that the supersession was correct, not as a new defect.

No BLOCKER-level evidence-integrity problem was found, and **no stop condition was triggered.**

## 15. Negative authority — what this review did not do

It did not: execute Review B; perform any Claude adjudication; write a
`document_adjudicated_evidence` row; fabricate a Review-B or adjudication-role record; weaken or
modify migration `0015`; change any source, test, migration, or configuration byte; upgrade any
candidate `evidence_level` to `verified`; grant amendment-purpose or linkage quota credit; close
either real feasibility gate; run candidate selection, E0, E1, or E2; authorize M3.4; make any
network, SEC, or HTTP request; write to the private evidence root; modify any artifact or receipt;
persist or publish the private-root path; move `m3.2-complete`; or create any tag.

Both real-path gates — `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
`M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` — remain **OPEN**, and
`REAL_ACCEPTANCE_ORDERING_ADEQUACY` remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION**.

## 16. Owner-adjudication package — what Sol/GPT needs to decide

1. Whether the two interpretive standards in §4 (**S-1** multi-purpose abstention, **S-2** exhibit
   vehicle) are accepted as applied, refined, or rejected. Everything in §H/I turns on them.
2. Whether the 9 purpose abstentions stand, or whether any of the 4 `ambiguous_text` cases should be
   resolved by a new owner dominance rule — which would be new methodology and needs its own record.
3. Whether the 6 partial explicit-original records (form, no date) may contribute anything, given
   **R48** requires form **and** date-or-accession.
4. Whether the two orthography normalizations (`Form 10KT`, `Form 10–K` with an en dash) are accepted
   as form-identity-preserving under **R44**, and whether the informal `the Company 10-K` reference
   is accepted.
5. Whether `000113902025000123`'s exhibit-index footnote is accepted as X-1 issuer-authored
   explicit-original evidence.
6. Whether, and how, the **R52** resolution of the 96 candidate assertions should be computed —
   which requires E0 to exist first.

## 17. Result

```text
M3_3_DECISION_091_SINGLE_OPUS_EVIDENCE_REVIEW_COMPLETE_READY_FOR_OWNER_ADJUDICATION
TOTALITY = 108 / 108   MISSING 0   EXTRA 0   DUPLICATES 0
SPANS = 302, ALL LOCATED BYTE-EXACTLY IN THE FROZEN ARTIFACTS
PURPOSE = 99 ASSERTED / 9 ABSTAINED; ALL THREE FROZEN CATEGORIES WITNESSED
EXPLICIT ORIGINAL = 102 FORM / 96 DATE / 0 ACCESSION / 6 ABSTAINED
REVIEW_A_TABLE_SHA256 = d9c9d9c79a75d7808e09094fdafa189128ae522d884bb88c8fb28f0e40d89c4f
FINDINGS = BLOCKER 0 / MAJOR 0 / MINOR 0 / OPTIMIZATION 0 / OBSERVATION 3
REVIEW_B = NOT EXECUTED / NOT AUTHORIZED
CLAUDE_DOCUMENT_ADJUDICATION = NOT EXECUTED / NOT AUTHORIZED
VERIFIED CREDIT = NONE; BOTH FEASIBILITY GATES REMAIN OPEN
E0 / E1 / E2 / M3.4 = NOT AUTHORIZED
NETWORK / SEC / HTTP = NONE; REQUEST_CEILING 0; NEW SEC REQUESTS 0
NEXT ACT = SOL/GPT OWNER ADJUDICATION
```

## Appendix A — complete per-document review record (108)

Purpose span locations are byte ranges into the accession's own frozen artifact. Explicit-original
form and date spans are listed in the frozen catalog and in §F, §J and §K for every surfaced case.

| # | accession | form | cohort | X | reg | purpose | purpose span | original form | original date | spans | flags |
|---:|---|---|---|---|---:|---|---|---|---|---:|---|
| 1 | `000000314614000009` | 10-KT/A | development | X1 | 1 | administrative_or_exhibit | `bytes:17310-17425` | 10-KT | 2014-11-25 | 3 | — |
| 2 | `000004907113000063` | 10-K/A | development | X0 | 1 | administrative_or_exhibit | `bytes:22909-23135` | 10-K | 2013-02-22 | 3 | — |
| 3 | `000035089424000030` | 10-K/A | primary_test | X0 | 1 | administrative_or_exhibit | `bytes:27756-28246` | 10-K | 2024-02-20 | 3 | high_judgment |
| 4 | `000035729411000004` | 10-K/A | development | X0 | 1 | *abstain: ambiguous_text* | `—` | 10-K | 2010-12-22 | 2 | high_judgment,multi_purpose |
| 5 | `000082148320000021` | 10-K/A | development | X2 | 1 | financial_or_xbrl_correction | `bytes:49951-50572` | 10-K | 2020-03-02 | 3 | high_judgment |
| 6 | `000087476125000029` | 10-K/A | prospective | X2 | 1 | administrative_or_exhibit | `bytes:37816-37983` | 10-K | 2025-03-11 | 3 | — |
| 7 | `000089016324000008` | 10-K/A | primary_test | X1 | 1 | *abstain: insufficient_text* | `—` | *abstain: insufficient_text* | — | 0 | no_amendment_statement |
| 8 | `000091228216000638` | 10-K/A | development | X0 | 1 | administrative_or_exhibit | `bytes:22943-23422` | 10-K | 2015-12-23 | 3 | — |
| 9 | `000091412117001183` | 10-K/A | development | X0 | 1 | narrative_or_governance | `bytes:26469-26822` | 10-K | 2017-03-23 | 3 | high_judgment |
| 10 | `000094667321000007` | 10-K/A | development | X2 | 1 | administrative_or_exhibit | `bytes:42266-42498` | 10-K | 2021-02-23 | 3 | — |
| 11 | `000095012310102209` | 10-KT/A | development | X0 | 1 | *abstain: ambiguous_text* | `—` | 10-K | 2009-06-29 | 2 | high_judgment,multi_purpose,form_metadata_tension |
| 12 | `000095012311006537` | 10-KT/A | development | X0 | 1 | narrative_or_governance | `bytes:10523-10600` | 10-KT | 2010-12-29 | 3 | — |
| 13 | `000095017023013914` | 10-K/A | transition | X0 | 1 | narrative_or_governance | `bytes:50101-50315` | 10-K | 2022-07-08 | 3 | high_judgment |
| 14 | `000095017024086880` | 10-K/A | primary_test | X0 | 1 | narrative_or_governance | `bytes:36364-36712` | 10-K | 2024-05-31 | 3 | — |
| 15 | `000095017025062260` | 10-K/A | prospective | X2 | 1 | narrative_or_governance | `bytes:57885-59460` | 10-K | 2025-02-26 | 3 | — |
| 16 | `000101041213000014` | 10-KT/A | development | X1 | 1 | financial_or_xbrl_correction | `bytes:10090-10190` | 10-KT | 2013-01-16 | 3 | form_orthography |
| 17 | `000101968711003121` | 10-K/A | development | X0 | 1 | financial_or_xbrl_correction | `bytes:21388-21493` | 10-K | 2011-09-07 | 4 | high_judgment |
| 18 | `000103835712000037` | 10-K/A | development | X0 | 1 | administrative_or_exhibit | `bytes:24598-24918` | 10-K | 2012-02-29 | 3 | high_judgment |
| 19 | `000105291817000332` | 10-K/A | development | X0 | 1 | administrative_or_exhibit | `bytes:8760-9117` | *abstain: insufficient_text* | — | 1 | form_outside_accepted_set,form_metadata_tension |
| 20 | `000106299315001609` | 10-K/A | development | X1 | 1 | administrative_or_exhibit | `bytes:8308-8630` | 10-K | 2015-03-16 | 3 | — |
| 21 | `000106299321008049` | 10-K/A | development | X1 | 1 | narrative_or_governance | `bytes:10954-11199` | 10-K | 2021-07-06 | 3 | — |
| 22 | `000107069813000033` | 10-KT/A | development | X0 | 1 | administrative_or_exhibit | `bytes:16722-16850` | 10-KT | 2013-03-14 | 3 | — |
| 23 | `000107997323000590` | 10-K/A | transition | X0 | 1 | narrative_or_governance | `bytes:23349-23455` | 10-K | 2023-03-31 | 3 | — |
| 24 | `000109690623001694` | 10-K/A | transition | X2 | 1 | financial_or_xbrl_correction | `bytes:44283-44494` | 10-K | 2023-08-15 | 3 | informal_form_reference |
| 25 | `000110465925102170` | 10-K/A | prospective | X2 | 1 | narrative_or_governance | `bytes:38576-38718` | 10-K | 2025-09-11 | 3 | — |
| 26 | `000110465926007405` | 10-K/A | monitoring | X2 | 1 | narrative_or_governance | `bytes:43416-43587` | 10-K | 2025-12-15 | 3 | — |
| 27 | `000113902025000123` | 10-K/A | prospective | X0 | 1 | *abstain: insufficient_text* | `—` | 10-K | 2025-04-15 | 2 | high_judgment,evidence_outside_explanatory_note |
| 28 | `000114036122002604` | 10-K/A | transition | X1 | 1 | financial_or_xbrl_correction | `bytes:48184-48280` | 10-K | 2021-03-31 | 4 | — |
| 29 | `000114420410068455` | 10-K/A | development | X0 | 1 | financial_or_xbrl_correction | `bytes:25691-25762` | 10-K | 2010-03-12 | 4 | — |
| 30 | `000114420413018795` | 10-K/A | development | X1 | 1 | administrative_or_exhibit | `bytes:28702-28985` | 10-K | 2013-03-25 | 3 | — |
| 31 | `000116552710000897` | 10-KT/A | development | X0 | 1 | *abstain: insufficient_text* | `—` | *abstain: insufficient_text* | — | 0 | no_amendment_statement,form_metadata_tension |
| 32 | `000117015413000083` | 10-K/A | development | X0 | 2 | administrative_or_exhibit | `bytes:48956-49148` | 10-K | 2013-03-11 | 3 | — |
| 33 | `000117184325001776` | 10-K/A | prospective | X0 | 1 | narrative_or_governance | `bytes:16542-16666` | 10-K | 2024-11-20 | 3 | — |
| 34 | `000119312510239802` | 10-K/A | development | X0 | 1 | narrative_or_governance | `bytes:16749-16865` | 10-K | 2010-08-30 | 3 | — |
| 35 | `000119312512173118` | 10-K/A | development | X0 | 2 | narrative_or_governance | `bytes:17022-17106` | 10-K | 2012-01-25 | 3 | — |
| 36 | `000119312512462631` | 10-K/A | development | X1 | 1 | administrative_or_exhibit | `bytes:17194-17545` | 10-K | 2012-10-15 | 3 | high_judgment |
| 37 | `000119312513134626` | 10-K/A | development | X0 | 2 | narrative_or_governance | `bytes:17833-17959` | 10-K | 2013-02-22 | 3 | — |
| 38 | `000119312513372376` | 10-K/A | development | X0 | 2 | narrative_or_governance | `bytes:15842-16468` | 10-K | 2013-03-29 | 3 | high_judgment |
| 39 | `000119312514076334` | 10-K/A | development | X0 | 2 | administrative_or_exhibit | `bytes:16319-16832` | 10-K | 2013-03-28 | 3 | high_judgment |
| 40 | `000119312514076381` | 10-K/A | development | X0 | 2 | administrative_or_exhibit | `bytes:16295-16808` | 10-K | 2013-03-28 | 3 | high_judgment |
| 41 | `000119312514200915` | 10-K/A | development | X0 | 3 | administrative_or_exhibit | `bytes:18026-18267` | 10-K | 2014-03-31 | 3 | — |
| 42 | `000119312515162273` | 10-KT/A | development | X0 | 1 | narrative_or_governance | `bytes:21249-21449` | 10-KT | 2015-02-27 | 3 | — |
| 43 | `000119312515224810` | 10-K/A | development | X0 | 3 | administrative_or_exhibit | `bytes:16415-16809` | 10-K | 2015-03-31 | 3 | — |
| 44 | `000119312515224858` | 10-K/A | development | X0 | 3 | administrative_or_exhibit | `bytes:16796-17145` | 10-K | 2015-03-31 | 3 | — |
| 45 | `000119312516633188` | 10-K/A | development | X0 | 2 | narrative_or_governance | `bytes:18093-18693` | 10-K | 2016-03-28 | 3 | high_judgment |
| 46 | `000119312516686295` | 10-K/A | development | X0 | 2 | administrative_or_exhibit | `bytes:16159-16736` | 10-K | 2016-03-30 | 3 | high_judgment |
| 47 | `000119312516686403` | 10-K/A | development | X0 | 2 | administrative_or_exhibit | `bytes:16293-16870` | 10-K | 2016-03-30 | 3 | high_judgment |
| 48 | `000119312516686413` | 10-K/A | development | X0 | 2 | administrative_or_exhibit | `bytes:16213-16790` | 10-K | 2016-03-30 | 3 | high_judgment |
| 49 | `000119312520243162` | 10-K/A | development | X0 | 2 | narrative_or_governance | `bytes:19436-19629` | 10-K | 2020-03-30 | 3 | — |
| 50 | `000119312523292717` | 10-K/A | transition | X0 | 1 | administrative_or_exhibit | `bytes:18715-19199` | 10-K | 2023-03-31 | 3 | — |
| 51 | `000119312525054051` | 10-K/A | prospective | X2 | 1 | administrative_or_exhibit | `bytes:27621-27877` | 10-K | 2025-03-12 | 3 | — |
| 52 | `000119312525107102` | 10-K/A | prospective | X2 | 1 | narrative_or_governance | `bytes:28664-28796` | 10-K | 2025-04-01 | 3 | — |
| 53 | `000119312526118635` | 10-K/A | monitoring | X2 | 1 | administrative_or_exhibit | `bytes:28836-29297` | 10-K | 2025-03-18 | 3 | — |
| 54 | `000119312526124739` | 10-K/A | monitoring | X0 | 1 | administrative_or_exhibit | `bytes:16917-17375` | 10-K | 2026-03-25 | 3 | — |
| 55 | `000119650121000012` | 10-K/A | development | X2 | 1 | narrative_or_governance | `bytes:49522-49690` | 10-K | 2021-02-26 | 3 | — |
| 56 | `000120864625000016` | 10-K/A | prospective | X0 | 2 | administrative_or_exhibit | `bytes:15198-15281` | 10-K | 2025-03-27 | 3 | — |
| 57 | `000121390020012521` | 10-K/A | development | X1 | 1 | administrative_or_exhibit | `bytes:18778-18969` | 10-K | 2020-05-14 | 3 | high_judgment |
| 58 | `000121390021033594` | 10-K/A | development | X2 | 1 | financial_or_xbrl_correction | `bytes:29469-29574` | 10-K | 2021-04-06 | 4 | — |
| 59 | `000121390022001426` | 10-K/A | transition | X1 | 1 | financial_or_xbrl_correction | `bytes:38930-39148` | 10-K | 2021-03-31 | 3 | — |
| 60 | `000121390022005759` | 10-K/A | transition | X1 | 1 | financial_or_xbrl_correction | `bytes:20028-20297` | 10-K | 2021-03-31 | 3 | — |
| 61 | `000121390022011106` | 10-K/A | transition | X1 | 1 | administrative_or_exhibit | `bytes:27216-27412` | 10-K | 2021-10-13 | 3 | high_judgment |
| 62 | `000121390022030740` | 10-K/A | transition | X2 | 1 | administrative_or_exhibit | `bytes:28297-28398` | 10-K | — | 3 | high_judgment,partial_original_evidence |
| 63 | `000121390024022780` | 10-K/A | primary_test | X2 | 1 | financial_or_xbrl_correction | `bytes:28239-28466` | 10-K | 2023-02-17 | 3 | — |
| 64 | `000127653124000008` | 10-K/A | primary_test | X0 | 1 | narrative_or_governance | `bytes:17407-17573` | 10-K | 2024-04-16 | 3 | — |
| 65 | `000127653125000005` | 10-K/A | prospective | X0 | 1 | narrative_or_governance | `bytes:16596-16983` | 10-K | 2024-04-16 | 3 | amends_prior_amendment |
| 66 | `000132587823000121` | 10-K/A | transition | X2 | 1 | administrative_or_exhibit | `bytes:47086-47498` | 10-K | 2023-03-20 | 3 | high_judgment |
| 67 | `000134512625000078` | 10-K/A | prospective | X2 | 2 | financial_or_xbrl_correction | `bytes:611926-612409` | 10-K | 2025-02-27 | 3 | — |
| 68 | `000135968712000022` | 10-KT/A | development | X0 | 1 | administrative_or_exhibit | `bytes:23725-23929` | 10-KT | — | 2 | partial_original_evidence |
| 69 | `000136086513000110` | 10-K/A | development | X1 | 1 | administrative_or_exhibit | `bytes:18252-18387` | 10-K | — | 2 | high_judgment,partial_original_evidence |
| 70 | `000137647410000009` | 10-K/A | development | X0 | 1 | *abstain: ambiguous_text* | `—` | *abstain: insufficient_text* | — | 0 | high_judgment,multi_purpose,form_outside_accepted_set |
| 71 | `000137746924000003` | 10-K/A | primary_test | X2 | 1 | financial_or_xbrl_correction | `bytes:57792-57875` | 10-K | 2024-04-12 | 3 | high_judgment |
| 72 | `000138119726000072` | 10-K/A | monitoring | X2 | 1 | administrative_or_exhibit | `bytes:43037-43492` | 10-K | 2026-02-27 | 3 | high_judgment |
| 73 | `000143774921008101` | 10-K/A | development | X2 | 1 | administrative_or_exhibit | `bytes:699519-699635` | 10-K | 2021-03-12 | 3 | high_judgment |
| 74 | `000143774923031044` | 10-K/A | transition | X2 | 1 | narrative_or_governance | `bytes:353809-354775` | 10-K | 2023-03-15 | 3 | — |
| 75 | `000143774924021940` | 10-K/A | primary_test | X2 | 1 | administrative_or_exhibit | `bytes:29835-30054` | 10-K | 2023-11-17 | 3 | — |
| 76 | `000145293617000022` | 10-K/A | development | X0 | 1 | narrative_or_governance | `bytes:42046-42136` | 10-K | 2017-03-10 | 3 | — |
| 77 | `000147793223008817` | 10-K/A | transition | X0 | 1 | narrative_or_governance | `bytes:20774-20894` | 10-K | 2023-03-31 | 3 | — |
| 78 | `000147793224002311` | 10-K/A | primary_test | X2 | 1 | financial_or_xbrl_correction | `bytes:90602-90821` | 10-K | 2024-04-17 | 3 | high_judgment |
| 79 | `000147793226002254` | 10-K/A | monitoring | X0 | 1 | narrative_or_governance | `bytes:29130-29425` | 10-K | 2025-11-13 | 3 | — |
| 80 | `000149315222009863` | 10-K/A | transition | X1 | 1 | financial_or_xbrl_correction | `bytes:60917-61191` | 10-K | 2022-03-30 | 3 | — |
| 81 | `000149315222033517` | 10-K/A | transition | X2 | 1 | narrative_or_governance | `bytes:84386-84630` | 10-K | 2022-04-13 | 3 | — |
| 82 | `000151116414000414` | 10-K/A | development | X1 | 1 | financial_or_xbrl_correction | `bytes:14823-14982` | 10-K | 2014-07-15 | 3 | high_judgment |
| 83 | `000152013815000055` | 10-K/A | development | X0 | 1 | financial_or_xbrl_correction | `bytes:16674-16879` | 10-K | — | 2 | partial_original_evidence,d081_extractor_divergence |
| 84 | `000152013826000207` | 10-K/A | monitoring | X2 | 1 | financial_or_xbrl_correction | `bytes:139063-139222` | 10-K | 2026-03-30 | 3 | — |
| 85 | `000154972720000065` | 10-KT/A | development | X1 | 1 | *abstain: insufficient_text* | `—` | *abstain: insufficient_text* | — | 0 | no_amendment_statement |
| 86 | `000155837024013150` | 10-K/A | primary_test | X2 | 1 | financial_or_xbrl_correction | `bytes:625943-626825` | 10-K | 2023-03-15 | 3 | — |
| 87 | `000155837025005691` | 10-K/A | prospective | X2 | 1 | narrative_or_governance | `bytes:54895-55145` | 10-K | 2025-04-15 | 3 | — |
| 88 | `000157873224000020` | 10-K/A | primary_test | X0 | 1 | administrative_or_exhibit | `bytes:28089-28230` | 10-K | 2024-02-27 | 3 | — |
| 89 | `000160706220000150` | 10-K/A | development | X0 | 1 | narrative_or_governance | `bytes:24363-24532` | 10-K | 2019-11-12 | 3 | — |
| 90 | `000161041816000067` | 10-K/A | development | X0 | 1 | administrative_or_exhibit | `bytes:20731-21001` | 10-K | — | 2 | partial_original_evidence |
| 91 | `000162045926000022` | 10-K/A | monitoring | X2 | 1 | narrative_or_governance | `bytes:29938-30022` | 10-K | 2026-03-03 | 3 | — |
| 92 | `000164117225007916` | 10-K/A | prospective | X0 | 1 | narrative_or_governance | `bytes:27832-28369` | 10-K | 2025-04-15 | 3 | — |
| 93 | `000165495422005693` | 10-K/A | transition | X0 | 1 | narrative_or_governance | `bytes:17631-17703` | 10-K | 2022-03-11 | 3 | — |
| 94 | `000166357722000545` | 10-K/A | transition | X2 | 1 | financial_or_xbrl_correction | `bytes:62416-62745` | 10-K | 2022-06-10 | 3 | — |
| 95 | `000167201320000065` | 10-K/A | development | X2 | 1 | administrative_or_exhibit | `bytes:44939-45232` | 10-K | 2020-02-27 | 3 | — |
| 96 | `000168316820002798` | 10-KT/A | development | X1 | 1 | *abstain: insufficient_text* | `—` | *abstain: insufficient_text* | — | 0 | no_amendment_statement |
| 97 | `000168316824002854` | 10-K/A | primary_test | X0 | 1 | narrative_or_governance | `bytes:17869-18090` | 10-K | 2024-02-22 | 3 | form_orthography |
| 98 | `000168316824005774` | 10-K/A | primary_test | X0 | 1 | narrative_or_governance | `bytes:18601-18662` | 10-K | 2024-06-27 | 3 | — |
| 99 | `000170362518000015` | 10-K/A | development | X1 | 1 | administrative_or_exhibit | `bytes:14837-14929` | 10-K | 2018-08-13 | 3 | — |
| 100 | `000171254322000127` | 10-K/A | transition | X1 | 1 | administrative_or_exhibit | `bytes:15797-15840` | 10-K | 2022-08-30 | 3 | high_judgment |
| 101 | `000172617325000021` | 10-K/A | prospective | X0 | 1 | financial_or_xbrl_correction | `bytes:34196-34730` | 10-K | 2025-03-03 | 3 | high_judgment |
| 102 | `000173112223001487` | 10-K/A | transition | X0 | 1 | narrative_or_governance | `bytes:23755-23922` | 10-K | 2023-03-29 | 3 | — |
| 103 | `000173112226000061` | 10-K/A | monitoring | X0 | 1 | financial_or_xbrl_correction | `bytes:16103-16214` | 10-K | — | 2 | high_judgment,partial_original_evidence |
| 104 | `000175392626000935` | 10-K/A | monitoring | X0 | 1 | administrative_or_exhibit | `bytes:26378-26591` | 10-K | 2026-05-20 | 3 | — |
| 105 | `000183021024000041` | 10-K/A | primary_test | X2 | 1 | narrative_or_governance | `bytes:33634-33723` | 10-K | 2024-03-15 | 3 | — |
| 106 | `000185545726000020` | 10-K/A | monitoring | X0 | 1 | narrative_or_governance | `bytes:26174-26296` | 10-K | 2026-03-31 | 3 | — |
| 107 | `000188852426006579` | 10-K/A | monitoring | X0 | 1 | administrative_or_exhibit | `bytes:29195-29346` | 10-K | 2026-03-06 | 3 | — |
| 108 | `000190359626000081` | 10-K/A | monitoring | X2 | 1 | *abstain: ambiguous_text* | `—` | 10-K | 2025-07-15 | 2 | high_judgment,multi_purpose |
