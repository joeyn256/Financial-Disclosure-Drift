# Decision 114 — M21 Historical Anchor Preserved and Superseded for the Live Mutation Target

```text
STATUS: ACCEPTED — OWNER RULING ON THE D113 §22 REFERRAL
DATE: 2026-08-18
OWNER: Joey authorization; Sol/GPT-5.6 owner ruling
OUTCOME: M3_3_D114_M21_LIVE_ANCHOR_SUPERSEDED
SUPERSEDES: Decision 076 §9's live audit expectation, as to M21's applicability to the current target only
E0_V3_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

This record answers the single question [Decision 113](decision_113_m3_3_compact_derived_e0_evidence.md)
§22 referred to the owner rather than deciding for itself. It disposes one mutation anchor's
applicability to the live target and nothing else. It changes no production source, no test other
than the audit test named in §4, no migration, no frozen research definition, and no evidence
record, and it grants no execution authority of any kind. Decisions 091–113 remain binding on every
point they name.

## 1. The referral, and why it is not a defect

[Decision 076](decision_076_m3_3_preacceptance_infrastructure_optimization.md) §9 makes the durable M1–M38
mutation campaign in `Docs/m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md` recoverable, and its
audit test holds every recovered anchor against the executable target so that a record which has
stopped describing that target says so instead of being trusted silently. Decision 113's sole
`make check-fast` returned 4,694 passed / 1 skipped / 1 failed, and the one failure was that
statement working correctly: the live partition had become `['M19', 'M21']` where the test expected
`['M19']`.

M21 mutates this exact text in `_materialize_full_index_registrants`:

```python
            if plain not in known:
                unbound.add(plain)
                continue
```

`known` was a preloaded set holding one string per accession in the catalog — roughly 21.5 million
strings and about 2.9 GB on E0's first planned source, on its own more than the host's whole memory
budget. Accepted [Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md) §8 required
that whole-catalog preload removed, and Decision 113 §9 removed it, replacing the membership test
with a per-accession primary-key lookup that also returns the canonical values the corroboration
verdict needs.

The predicate M21 exists to defend did not change. The **R23** §5.1 invariant is that an accession
the index lists and the authoritative accession layer does not carry is *reported*, never
manufactured; the live parser still adds it to `unbound` and skips it, and
`census_accession_observations.accession_plain` remains a foreign key into `census_accessions` that
would refuse an invented one. What moved is the text the anchor is written in, not the behaviour it
covers.

Restoring the preloaded form to make the anchor resolve would reintroduce exactly the unsafe
implementation Decision 110 §8 required removed. Adding it as dead code or a comment would be gate
gaming. Editing the immutable historical campaign artifact would rewrite accepted evidence. The
runner's report of a missing anchor was therefore the correct owner-referral behaviour, and this
record is the ruling it referred to.

## 2. Ruling R2 — M21 historical anchor preserved, live mutation target superseded

M21's historical definition, its two KILLED results, and
`Docs/m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md` remain immutable and truthful for the frozen
targets they describe. Nothing is deleted, rewritten, reclassified as a historical survivor, or made
to appear as though M21 never existed.

For the current live target only, M21 is **SUPERSEDED BY ACCEPTED DECISION 110 §8 AND DECISION 113
§9**. This is the same disposition class accepted
[Decision 097](decision_097_m3_3_m19_live_anchor_supersession_correction.md) §3 (R87) established
for M19, applied on its own facts. The live applicability partition is exactly:

```text
historical definitions recovered = 38
live anchors resolved            = 36
superseded live anchors          = ["M19", "M21"]
unexpected missing anchors       = []
```

M21's successor proof is `tests/unit/test_m3_offline_parse.py::test_an_index_only_accession_is_reported_and_never_created`
— the killing test M21's own definition names. It seeds a `company.idx` quarter listing an accession
the authoritative layer does not carry, and asserts both halves of **R23** §5.1 against the shipped
parser: the accession appears in `full_index_unbound_accessions`, and `census_accessions` carries
zero rows for it. Decision 113 §12's totality proof holds the same unbound set equal across both
evidence contracts over a fixture that carries an index row binding to nothing.

This ruling changes **only live-target applicability**. It creates no generic missing-anchor
exception. M19 keeps its own Decision 097 R87 disposition on its own grounds, M20, M22, and every
other M1–M38 anchor remain required, and a third missing anchor is a new failure that may not be
hidden under either disposition.

## 3. What this record does not do

It does not authorize restoring the preloaded accession set, or any other whole-catalog preload, in
any layer. It reopens no part of the Decision 110 streaming and memory architecture, the Decision
111 working-catalog architecture, the Decision 112 compact raw-evidence contract, or the Decision
113 resolution compaction, corroboration compaction, capacity model, or capacity preflight. It
performs no semantic or storage compaction of its own, and it does not revisit the Decision 113 §15
capacity verdict.

It does not accept, reject, or requalify the Decision 113 implementation beyond removing this one
audit blocker, and it makes no claim that historical M21 evidence is invalid, deleted, or rerun
against the current target.

## 4. Ruling R2 implementation and validation boundary

The sole executable edit authority is:

```text
tests/unit/test_audit_tooling.py
```

The corrected test must prove all of the following directly, with no unexplained literal standing in
for the disposition:

1. all 38 historical definitions still recover, in exact M1 through M38 order;
2. `verify_anchors()` returns exactly `['M19', 'M21']` against the live target;
3. each superseded anchor is pinned by target file, semantic locus, and exact anchor text, so a
   renamed, relocated, or rewritten anchor cannot inherit either disposition;
4. M19's grounds hold — the deleted candidate-layer fallback is absent and the canonical
   `census_accession_registrants` and `registrant_set_completeness` consumer source is present;
5. M21's grounds hold — the preloaded `known` membership test is absent from the live parser, the
   per-accession primary-key lookup is present, the **R23** §5.1 predicate is still written there,
   and the killing test M21's definition names still holds it; and
6. any missing anchor other than or in addition to those two fails the exact assertion.

`scripts/dev/mutation_campaign.py` is deliberately unchanged. Its `anchors_missing` field and its
nonzero owner-referral result remain truthful, and no generic `superseded` runner channel is
introduced — that would be a broader audit-tooling methodology change this record does not make.
The historical campaign artifact, production source, migrations, and every other test are likewise
unchanged.

Validation is the corrected audit module, M21's named killing test, bounded isolated non-vacuity
mutations that must fail and be restored byte-for-byte, touched-file lint and format checks, and
exactly one `make check-fast`. One local commit on top of the Decision 113 commit is authorized on
full success. No push, tag, amend, rebase, force operation, or publication is authorized.

## 5. What remains prohibited

This Decision authorizes no:

- E0-v3 namespace creation, E0 execution, first-source or three-source canary, or replay proof;
- operational-catalog mutation, private-evidence mutation, or migration `0016` — the catalog stays
  at head `0015`;
- activation of `M3_3_E0_EXECUTION_AUTHORITY`, `PRE_E0_CATALOG_TRANSITION_AUTHORITY`, or
  `STALE_WRITER_LEASE_RECOVERY_AUTHORITY`, all of which remain exactly `None`;
- network, SEC, EDGAR, HTTP, DNS, socket, acquisition, or package installation act; or
- push, pull, fetch, rebase, tag, publication, release, or history rewrite.

The request and attempt ceilings remain zero, and E0 remains operationally HELD on the Decision 113
§15 capacity verdict, which this record does not touch.

## 6. Exact next action

1. Apply the R2 correction under §4 and return the completion evidence to Sol/GPT.
2. Do not push, tag, migrate, run a canary, or infer later-stage authority.

`RESULT_TOKEN: M3_3_D114_M21_LIVE_ANCHOR_SUPERSEDED`
