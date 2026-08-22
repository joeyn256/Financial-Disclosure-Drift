# Decision 131 — The D128 Semantic and Operational Repair

```text
STATUS: ACCEPTED — OWNER RULING / IMPLEMENTATION VALIDATED
RECORD_TYPE: OWNER GOVERNANCE PUBLICATION OF AN IMPLEMENTED AND VALIDATED REPAIR —
  PUBLISHED WITH THE CODE IT DESCRIBES, IN THE SAME COMMIT
DATE: 2026-08-22
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
ACCEPTANCE_TOKEN: M3_3_D131_FINAL_REPOSITORY_VALIDATION_OWNER_ACCEPTED
PUBLICATION_TOKEN: M3_3_D131_PUBLICATION_AUTHORIZED
OUTCOME: D128_SEMANTIC_DEFECTS_REPAIRED_IN_CODE_AND_VALIDATED_IN_REPOSITORY
D128_SEMANTIC_DISPOSITION: D128_SEMANTIC_REPAIR_REQUIRED — DISCHARGED IN CODE ONLY.
  D129-R2'S REJECTION OF EVERY D128 COUNT STANDS ENTIRELY AND IS NOT REVISITED
SCOPE: THE REPAIR, ITS TESTS, ITS OPERATOR SURFACE, AND ITS REPOSITORY VALIDATION —
  NOT A SEMANTIC PROOF AGAINST THE REAL SOURCE, NOT A PERFORMANCE RESULT,
  NOT A CAPACITY MODEL, AND NOT AN EXECUTION AUTHORIZATION
SEMANTIC_VALIDATION_STATUS: NOT PERFORMED — REQUIRES ITS OWN OWNER INSTRUMENT
CORRECTED_CANARY_AUTHORIZATION: NO
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO — AND NO MIGRATION IS REQUIRED BY THIS REPAIR
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
PRE_NETWORK_BLOCKER: CensusOrchestrator._parse_bulk — OPEN, DELIBERATELY UNREPAIRED
```

The owner's governance publication of the D131 repair of the two blocking
`PARSER_IMPLEMENTATION_DEFECT` findings [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
recorded against the complete-first-source canary `m3_3_d128_complete_first_source_v1`, together
with the watchdog, monitoring, provenance, and operator-surface corrections that record required.

## 1. What this record is, and what it is not

**It is published with its code, not after it.** Unlike [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
and [Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md), which were retrospective
records of work that had already finished elsewhere, D131's implementation, its tests, and this
record enter the repository in **the same commit**. The record and the artifact it describes are
therefore verifiable against each other by inspection.

**It repairs defects in code. It does not certify a count.** [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
§4 (D129-R2) rejected every D128 count, and **that rejection stands entirely and is not revisited
here.** D131 changes what the implementation will do on a future run; it says nothing about what any
past run recorded, and it produces no new count of its own.

**It is not a semantic proof against the real source.** No corrected parse of the real bulk archive
was performed, and §11 rules explicitly that an ordinary `--member-limit` prefix **cannot** serve as
one. The bounded real semantic proof is the *next* stage and needs its own owner instrument.

**It is not a performance result and not a capacity model.** §13 records that no tuning of any kind
occurred, and [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12)
continues to require a *new* corrected-run capacity reconciliation that this record does not
construct.

**It closes no pre-network blocker.** §12 records `CensusOrchestrator._parse_bulk` as carrying the
same dispatch defect, **deliberately unrepaired**, and rules that no future network authorization
may reach it until it is.

## 2. Entry state

The implementation, the validation, and this publication all entered at the same verified baseline:

| Item | Value |
|---|---|
| Branch | `main` |
| `HEAD` | `75973a0b0d4a30f22e0a3d64212d0cd54f2bdf9e` |
| `origin/main` | identical to `HEAD`, ahead/behind `0/0` |
| Latest decision | Decision 130 |
| Migration head | `0015`; `0016` absent and unapplied |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` |
| `network.enabled` | `false` |
| `network.m3_acquire_enabled` | `false` |

## 3. The D128 root cause, and what D131 repairs

[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) rejected D128's semantic counts on
two implementation defects, both classified `PARSER_IMPLEMENTATION_DEFECT`:

1. **Defect A — dispatch (§5, D129-R3).** `5,337` legitimate historical submission shards matching
   the tracked `HISTORICAL_FILE_NAME_PATTERN` `^CIK[0-9]{10}-submissions-[0-9]{3}\.json$` were routed
   through `parse_submissions_document(...)` instead of the historical submissions parser, and were
   rejected — correctly, because that parser's contract is *one document describes one CIK* and a
   shard is not that document. **The defect was the dispatch, not the rejection.** It cost
   `5,102,087` shard accessions, of which `2,064,473` were recovered elsewhere and **`3,037,614` are
   genuinely absent** from a real universe of `19,034,205` — an omitted share of `15.96%`. The
   omission fell almost entirely on one arm of the temporal comparison: Form 10-K family `9.11%`
   absent in the development cohort `2010`–`2021` against `0.25%` in the evaluation cohort
   `2022`–`2026`, roughly a `36x` differential, recorded as a **structural confound**.

2. **Defect B — binding (§6, D129-R4).** Historical references in the bulk observation were stamped
   with **one observation-wide registrant CIK** rather than each reference's declaring parent. All
   `5,337` of `5,337` `census_historical_references` rows received one incorrect CIK where `4,144`
   distinct registrants were represented, and the compounding hazard was that the guard tested only
   uniqueness — one consistently wrong candidate passed as confidently as a right one.

**D131 corrects those two implementation defects**, and carries the four further corrections
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) required alongside them: the
recognized optional fields (§6), watchdog `SIGINT` delivery (§9), post-traversal monitoring (§10),
and the parser provenance those changes make necessary (§7).

## 4. Historical shard dispatch — Repair A

The bulk traversal in `src/disclosure_drift/m3/offline_parse.py` now distinguishes the two member
shapes the archive actually holds, and routes each to the parser whose contract it satisfies.

**What the corrected traversal does.**

- The bulk archive distinguishes **primary submissions documents** from **historical shards**, and a
  historical shard **never reaches** `parse_submissions_document(...)`.
- Shard **payloads are not retained during the primary traversal**. Meeting a shard records only its
  `member_ordinal` and `member_name` in a frozen `_DeferredHistoricalShard`, and the bytes in hand
  are dropped with every other member's.
- Parent declarations are learned from the **explicit primary declaration** — `filings.files[].name`
  — folded into a parent map as each primary document is parsed.
- Deferred shards are **reopened by exact archive member name** after the traversal ends, when the
  parent map is complete.
- The existing `parse_historical_submissions(...)` is used. No second historical parser was written.
- Deferred shards execute in **original governed archive ordinal order**, so the correction
  introduces no ordering of its own.
- **Archive ordering does not change semantic output.** Parent-before-child and child-before-parent
  produce the same result, which is [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md)
  §7 (D129-R6) read literally.

**D129-R5 remains controlling, and is implemented as written.** The explicit parent
`filings.files[].name` declaration is **authoritative**. The CIK embedded in a shard's filename is
**corroborative only**: `_shard_filename_cik(...)` may confirm a declaration and may refuse one that
contradicts it, and it is never the source of a binding. `_resolve_shard_parent(...)` **fails closed**
on all three failure shapes — no declaring parent, more than one distinct declaring parent, and a
filename CIK contradicting the declared parent — and a declaration naming a member the archive does
not carry simply never keys a shard, so "the parent declared some other file" arrives as the
missing-declaration refusal.

**Every parent is resolved before any member is reopened.** A refusal therefore costs no
decompression and cannot leave half the deferred population parsed and the other half refused.

**Bounded residency is a permanent property, not an incidental one — D131-R5.** The deferred record
holds **no payload** by construction, and the parent map is bounded by the *shard* population rather
than the *declaration* population: a declaration is retained only when the archive carries a member
of exactly that name. Both are the accepted [Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md)
§8 boundedness applied to the new phase rather than an approximation of it, and the repository
carries a live per-boundary residency test that fails on any per-member state introduced into the
bulk generator.

**Direct tests.** `tests/unit/test_d131_historical_shard_dispatch.py` — `46` tests.

## 5. Per-reference parent binding — Repair B

**The reference carries its own parent.** `HistoricalFileReference` in
`src/disclosure_drift/sec/parsers/submissions.py` gained a **required** field with no default,
`registrant_cik_padded`, set by the document that actually declared the entry. A required field is
the point: a construction site cannot omit it and silently inherit somebody else's registrant.

- **Persistence writes that per-reference CIK.** `CensusCatalog._insert_historical_references` in
  `src/disclosure_drift/sec/census.py` now normalizes the reference's own parent CIK instead of
  resolving one value per observation from the lowest-`parsed_record_id` registrant record.
- **No observation-wide CIK is reused anywhere.** The former per-observation lookup is deleted, not
  merely bypassed.
- **Valid and malformed historical-reference persistence both preserve parent identity.** A
  malformed entry is stamped with the same declaring parent and preserved in
  `census_malformed_historical_references` with its raw entry intact.
- **A reverse lookup requires exact member identity and filename corroboration**, and a **uniformly
  wrong persisted identity is rejected** rather than passing a uniqueness test.
- An unusable parent CIK **raises** rather than substituting a value: the alternative to failing is
  writing a reference under somebody else's registrant, which is the defect being repaired.

**No migration was needed.** `registrant_cik_padded` already exists on both tables and is already
part of the primary key, so the corrected value lands in a column the schema already contracted.
**The persisted schema is unchanged and migration `0016` is neither required nor authorized.**

**A performance note, recorded so it is not rediscovered as a regression.** The former per-observation
resolution existed because an earlier per-reference lookup repeated an identical sort of every parsed
record of the source — the accepted D111 remediation. The corrected value comes from the reference
itself, so **no lookup, ordering, or per-reference scan is involved** and that cost does not return.

## 6. Optional SEC source drift — D131-R1

[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §8 (D129-R7) accepted three
legitimate optional non-semantic SEC fields and deferred any code change to D131. D131 registers
them:

| Field | Where |
|---|---|
| `lei` | optional top-level registrant field |
| `filings.recent.core_type` | recognized `filings.recent` key |
| `filings.recent.isXBRLNumeric` | recognized `filings.recent` key |

**Recognition is exactly recognition, and nothing more.** `core_type` and `isXBRLNumeric` are
registered in a new `KNOWN_OPTIONAL_RECENT_FIELDS` tuple, deliberately **not** in
`ACCESSION_ARRAY_FIELDS`, because that registry carries a **list-shape contract**: a member of it
that is present but is not a list is a blocking `malformed_nested_array` event that quarantines the
entire `filings.recent` block. Registering the two new fields there would have **invented a new
refusal by the act of recognizing a field** — a strictly worse outcome than the drift report it was
meant to silence.

The separation is explicit in the source. `ACCESSION_ARRAY_FIELDS` answers *"is this key's list
shape part of the contract?"*; `RECOGNIZED_RECENT_FIELDS` — the union — answers *"do we know this
key?"* and is what every unknown-field walker reads. `inspect_payload(...)` receives the two
questions from two arguments, so recognizing a field cannot smuggle in a shape refusal.

**Neither field becomes required**, a document without them parses exactly as before, and **no
accession identity, registrant identity, cohort, or preregistered methodology definition changes.**

## 7. Parser provenance — D131-R2 and D131-R8

D131 changes observable parser output and known-field behaviour, so the prior version strings may
not continue to describe the corrected implementations. Both move:

| Parser | Before | After | Why |
|---|---|---|---|
| `submissions-json` | `1.1` | **`1.2`** | recognized-field set and per-record `unknown_fields` change; `HistoricalFileReference` gains a required field its persistence writes |
| `submissions-historical` | `1.0` | **`1.1`** | the shard parser reads the same recognized-field union, so every emitted record's `unknown_fields` moved with it |

**The version table derives, it does not duplicate.** `PARSER_VERSIONS` in
`src/disclosure_drift/sec/parsers/versions.py` is built by **importing** each parser module's own
constant, and `SourceSpec.parser_version` is a property that reads it. The registration for
`sec_submissions_historical` carries no pinned expectation, so it derives; `_validate_parser_identity`
fails closed at import if a registration and an implementation ever disagree.

**No migration is required.** `census_parsed_records.unknown_fields_json` is a pre-existing `TEXT`
column carrying JSON; its content semantics move and its DDL does not.

**Existing operational and catalog provenance recorded under prior parser versions remains
historical truth and is NOT rewritten.** No `UPDATE` of any `parser_version` exists anywhere in
`src/`, and none is authorized. A row recorded under `submissions-json/1.1` correctly describes the
implementation that produced it.

**Future conditional reuse must fail closed when parser versions are incompatible**, and does:
`versions_agree(...)` is an exact match with `None` never agreeing, `require_parser_version(...)`
refuses before provenance is written, and `evaluate_reuse(...)` fails on `parser_compatibility_known`
so the refusal is attributable rather than incidental. **A stale version is refused in both
directions** — being merely *older than the last version anybody remembered* is not a defence.

**A corrected disposable canary may use the corrected parser versions.** That is a statement about
which versions such a run would record, not an authorization to run one.

**Direct tests.** `tests/unit/test_parser_version_authority.py` — `35` tests, both literals pinned
and the whole chain from implementation constant to registered source walked end to end.

## 8. The archive public API — D131-R3

The bounded exact named-member archive reader is now **owned by the public `sec.archive` surface**,
as `iter_named_members(...)`, rather than by private archive-helper imports reached from
`offline_parse`. The deferred phase reopens shards through that one public surface, so the defences
applied on reopen are **the same implementation** the primary traversal applied rather than a second
expression of the same answers in another module.

It preserves, by construction:

- **archive refusal, type, and size protections** — names canonicalized first, non-regular members
  refused, declared size and expansion ratio checked before a byte is read;
- **exact requested-member identity** — a name that is absent, or that resolves to more than one
  entry, is refused rather than skipped;
- **deterministic requested order** — the caller's sequence is the yield order, and a repeated name
  is refused rather than read twice;
- **bounded one-member-at-a-time payload behaviour** — one member is read, yielded, and dropped
  before the next is opened;
- **no network**, and nothing written to disk.

What is deliberately **not** re-applied is the archive-level *cumulative* expansion cap: those bytes
were already admitted under it during the full traversal, and re-counting a subset from zero would
compare part of an archive against a whole-archive limit.

**Direct tests.** `tests/unit/test_sec_archive.py` — `66` tests, of which `11` are new and cover
order, targeting, absence, ambiguity, repetition, traversal names, directory entries, oversize,
implausible ratio, corruption, and one-payload-at-a-time residency.

## 9. Signal and watchdog repair — D131-R6, D131-R9

**The D128 diagnosis, restated.** [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §9
(D129-R10) recorded forensic result `WATCHDOG_FALSE_ALERT_SIGNAL_NOT_DELIVERED_TO_CANARY`: the D128
chain launched as a background job from **non-interactive `zsh`**, which POSIX requires to start the
job with `SIGINT` set to `SIG_IGN`, and CPython leaves an inherited `SIG_IGN` in place. `kill -INT`
had no effect, and `/usr/bin/time` recorded **zero** received signals.

**The corrected future governed launch** — `scripts/m3/canary_launch.py`:

- the run is a **foreground** process, not a backgrounded job;
- the process chain is **`exec`-based**, so the PID recorded is the PID that runs;
- the launcher **refuses** when it reads an inherited `SIGINT = SIG_IGN` rather than launching into
  the D128 condition;
- the PID file identifies the **actual `exec`-preserved target**;
- the launcher holds no authority constant, reads no catalog, takes no lease, and enables no network.

**The corrected stop** — `scripts/m3/canary_watchdog.py`:

- authenticates the **exact PID and command line**; an unreadable or non-matching command line
  refuses rather than signals, and an empty or whitespace-only `--expect-command` is refused outright
  because `"" in observed` holds for every process on the machine;
- sends **`SIGINT` only**, once;
- **verifies actual termination** rather than treating a successful `kill(2)` return as proof;
- performs **no escalation to `SIGTERM` or `SIGKILL`** — a surviving target returns `STOP_FAILED`
  (exit `4`) and the run is treated as still going;
- handles the liveness/signal race: `ProcessLookupError` is **already gone**, and `PermissionError`
  is **not success** — it is `STOP_FAILED_SIGNAL_NOT_PERMITTED` (exit `4`);
- a process that has exited but not yet been reaped is a **zombie**, and is not read as alive;
- the network probe uses the **selector intersection** `lsof -nP -a -p PID -i`. The `-a` is the
  point: without it `lsof` unions its selectors and answers a question nobody asked, which is the
  form watchdog v1 used and the reason its network evidence was unusable.

**The positive-PID rule — D131-R9.** The target PID domain is strictly `pid > 0`. `os.kill` reads
`0` as the caller's own process group — from the canary's pane, that is the canary and the watchdog
together — and `-1` as every process the user may signal; `lsof -p 0` and `lsof -p -1` are the same
mistake in the reading direction. **A non-positive PID is refused before any process inspection,
before any `lsof` construction, and before any signalling.** The domain is written down **once**, in
`non_targetable_pid_detail(...)`, and both PID-taking operations read it, so the rule cannot be
relaxed at one call site without the other noticing.

| Outcome | Exit | Meaning |
|---|---|---|
| `STOP_REFUSED_NON_POSITIVE_PID` | `3` | nothing was inspected and **no signal was sent** |
| `PROBE_REFUSED_NON_POSITIVE_PID` | `3` | refused **before the `lsof` vector is built**; **no `lsof` is executed** |

**Direct tests.** `tests/unit/test_d131_signal_and_monitor.py` — `42` tests, including a real
`tmux`-pane launch shape, real disposable targets, and the non-positive-PID domain proved for both
`0` and `-1` at the function, CLI, and centralization levels.

## 10. Monitoring — D131-R10

[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §10 (D129-R11) recorded that D128's
`13` post-traversal stall alerts were **false**: the member counter had correctly reached its
terminal value while F1 and F2 legitimately continued. The corrected monitor states three relations
and refuses to guess between them:

| Relation | Verdict | Exit |
|---|---|---|
| `observed < governed` | traversal running; a frozen count for the threshold is a real stall | `2` |
| `observed == governed` | traversal finished; member-count alerting is **disabled** | `0` |
| `observed > governed` | the two counts **disagree** — `MEMBER_COUNT_INCONSISTENT` | `5` |

**Exit `5` is a claim about the monitor's own inputs, and nothing else.** It terminates only the
monitor invocation; it **sends no signal**, it **does not stop the canary**, and it is **distinct**
from a stall alert, from a refusal, and from `STOP_FAILED`. A traversal cannot pass its own governed
bound, so one of the two numbers is not describing what it is believed to describe — a stale governed
count, a count read from the wrong run, or an observation that is not the member count at all — and
stall timing is disabled rather than applied to numbers that do not agree.

**No F1/F2 automatic wall-clock kill rule was added**, and none is authorized. A phase label cannot
turn an alert into a silence, and nothing here queries the working catalog.

## 11. Prefix semantics — D131-R7

**An ordinary `--member-limit` diagnostic prefix executes zero deferred historical shards.**

This is a property of the corrected design rather than a limitation of a particular bound. A prefix
stops mid-archive, so its parent map is **incomplete by construction**, and resolving a shard against
an incomplete map would refuse a well-formed archive. A shard met inside the prefix counts against
the bound as a member the traversal handled — which is what `--member-limit` names — and is simply
never parsed. A prefix finalizes nothing and can never report success, so it carries **no claim about
the shard population either way**.

**Therefore an ordinary prefix run CANNOT be used as the bounded real semantic proof of Repair A.**
A run that parses zero shards cannot demonstrate that shards are parsed correctly, and reading a
clean prefix as evidence of the repair would repeat D128's error in the opposite direction — taking a
completion signal for a semantic result. **That proof requires a separately authorized semantic
fixture or mode**, and it is the next stage.

## 12. The pre-network blocker — D131-R4

**`src/disclosure_drift/sec/census_orchestrator.py::_parse_bulk` still carries the historical-shard
dispatch defect.** It is the twin of the path Repair A corrected, and it was **deliberately not
repaired** in D131.

**Why that is safe today.** The orchestrator path sits behind `require_network()`; network is
disabled at both tracked switches with request ceiling `0`; the corrected offline canary does not use
that path; and E0 does not use it. The defect is therefore **presently unreachable**.

**Why it is recorded as a blocker anyway.** Unreachable is a property of the current configuration,
not of the code. The moment a live-retrieval path is authorized, that function becomes reachable and
would reproduce Defect A against real data.

> **OWNER RULE — no future network or live-retrieval authorization may reach
> `CensusOrchestrator._parse_bulk` until its historical-shard dispatch is repaired.**

**This is not a blocker to D131 acceptance**, and it is **not to be repaired now**: repairing it
would expand an accepted, validated change set after its validation, which is precisely the shape of
change this project refuses.

## 13. Performance and capacity

**No D131 performance tuning occurred.** Nothing changed in: SQLite cache settings; batching;
checkpoint cadence; WAL mode; `synchronous` durability; index architecture; multiprocessing or
writer topology; or the [Decision 127](decision_127_m3_3_pre_f2_admission_guard.md) pre-F2 admission
gate.

**Current free space is informational only.** It is an input to a capacity model and never a
substitute for one.

**[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12) remains
controlling**: a corrected-run capacity reconciliation is required before **any** new complete-source
execution authorization, and D131 does not construct it. **That reconciliation is not the next
stage** — see §15.

## 14. Validation history

D131 was implemented and validated through seven distinct passes:

| # | Pass | Result |
|---|---|---|
| 1 | Implementation WIP | code and tests written |
| 2 | Fresh independent review | findings raised |
| 3 | Correction pass | findings addressed |
| 4 | Fresh bounded rereview | remaining findings raised |
| 5 | Final two corrections | `submissions-historical/1.1`; the `pid > 0` domain |
| 6 | Final independent delta recheck | `D131_FINAL_DELTA_PASS` — both corrections mutation-authenticated, WIP byte-identical across the review |
| 7 | Final repository validation | `make check-fast`, **exit `0`**, run **exactly once** |

**The final repository validation.**

| Gate | Result |
|---|---|
| `ruff check` | all checks passed |
| `ruff format --check` | `191` files already formatted |
| `mypy` strict over `src` | no issues in `93` source files |
| `pytest -n 7 --dist worksteal` | **`4898` passed, `1` skipped, `0` failed**, `4899` collected |
| secret scan | `439` files, `0` findings |
| repository hygiene | `441` paths, `0` findings |
| Markdown links | `207` documents, `2157` links, `0` unallowed |
| decision section references | `4702` citations against `127` records |
| `validate-config` | configuration valid |
| `show-cohorts` | frozen definitions printed, seed `20260725` |
| `sec --help` | command group printed |

**The single skip was pre-existing and unrelated** — `tests/unit/test_m23_pilot_manifest.py:429`,
*"snapshot_state is a fixed literal asserted before hashing"*. It is not a D131 test and does not
concern any D131 surface.

## 15. Owner rulings D131-R1 – D131-R11

| Ruling | Content |
|---|---|
| **D131-R1** | **`lei`, `filings.recent.core_type`, and `filings.recent.isXBRLNumeric` are recognized non-blockingly.** Recognition places a field in the known set and **does not** give it a list-shape contract it did not have: registering the two `filings.recent` fields under `ACCESSION_ARRAY_FIELDS` would have made a present scalar a blocking `malformed_nested_array` event and quarantined the whole block — a new refusal invented by the act of recognizing a field. Neither becomes required, and no accession identity, registrant identity, cohort, or preregistered methodology definition changes (§6). Implements [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §8 (D129-R7). |
| **D131-R2** | **`submissions-json` becomes `1.2`; no migration is required.** The recognized-field set and per-record `unknown_fields` moved, so the version must say so. `census_parsed_records.unknown_fields_json` is a pre-existing `TEXT` column; its content semantics move and its DDL does not (§7). |
| **D131-R3** | **The exact named-member archive reader belongs on the public archive surface.** `iter_named_members(...)` is owned by `sec.archive`, not by private helper imports in `offline_parse`, so the reopen applies the same defences the primary traversal applied through one implementation. It preserves refusal/type/size protections, exact member identity, deterministic requested order, absent-and-ambiguous refusal, one-member-at-a-time residency, and no network (§8). |
| **D131-R4** | **The `census_orchestrator` twin dispatch defect is deferred as an explicit PRE-NETWORK blocker.** `CensusOrchestrator._parse_bulk` still carries the Defect A dispatch and is **deliberately unrepaired**. It is presently unreachable behind `require_network()`, and neither the corrected offline canary nor E0 uses it. **No future network or live-retrieval authorization may reach that path until its historical-shard dispatch is repaired.** This is **not** a blocker to D131 acceptance, and it is not to be repaired now (§12). |
| **D131-R5** | **Permanent shard-bearing bounded-residency protection is required and is present.** The deferred record holds **no payload**; the parent map is bounded by the shard population rather than the declaration population; and every parent is resolved before any member is reopened. Accepted [Decision 110](decision_110_m3_3_e0_successor_safety_remediation.md) §8 boundedness is a property of the corrected traversal, not an approximation of one, and a live per-boundary residency test fails on any per-member state introduced into the bulk generator (§4). |
| **D131-R6** | **Watchdog exact-target hardening is accepted.** Foreground `exec`-based launch that refuses an inherited `SIGINT = SIG_IGN`; a PID file naming the `exec`-preserved target; exact PID and command authentication with an empty expectation refused outright; **`SIGINT` only**; verified termination rather than a trusted `kill(2)` return; **no `SIGTERM`/`SIGKILL` escalation**, so a survivor is `STOP_FAILED`; `ProcessLookupError` as already-gone and `PermissionError` as failure; and the `lsof -nP -a -p PID -i` selector **intersection** (§9). Implements [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §9 (D129-R10). |
| **D131-R7** | **Ordinary `--member-limit` prefixes parse zero deferred shards**, because a prefix's parent map is incomplete by construction. **A prefix therefore CANNOT serve as the bounded real semantic proof of Repair A**; that proof requires a separately authorized semantic fixture or mode. A prefix finalizes nothing, can never report success, and carries no claim about the shard population either way (§11). |
| **D131-R8** | **`submissions-historical` becomes `1.1`.** The shard parser reads the same recognized-field union, so every emitted record's `unknown_fields` and the persisted `unknown_fields_json` moved with it. Leaving it at `1.0` would let `versions_agree(...)` call a pre-D131 artifact compatible with an implementation that no longer produces it. **No migration is required**, and **existing provenance recorded under prior versions is historical truth and is NOT rewritten** (§7). |
| **D131-R9** | **The watchdog PID domain is strictly `pid > 0`.** A non-positive PID is refused **before** any process inspection, any `lsof` construction, and any signalling, by **one** definition both PID-taking operations read. `STOP_REFUSED_NON_POSITIVE_PID` and `PROBE_REFUSED_NON_POSITIVE_PID` both exit `3`, send nothing, and execute no `lsof` (§9). |
| **D131-R10** | **Monitor exit code `5` is accepted for the `observed > governed` inconsistency.** `MEMBER_COUNT_INCONSISTENT` disables stall timing, invents no kill rule, and queries no catalog. **Exit `5` terminates only the monitor invocation** — it sends no signal, does not stop the canary, and is distinct from a stall alert, a refusal, and `STOP_FAILED` (§10). Extends [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §10 (D129-R11). |
| **D131-R11** | **Operator documentation must enumerate the non-positive-PID stop and probe refusals.** The runbook's `stop` exit-code table carries `STOP_REFUSED_NON_POSITIVE_PID` at exit `3` with no signal sent, and the network-probe section carries `PROBE_REFUSED_NON_POSITIVE_PID` at exit `3` with no `lsof` executed. An operator-visible refusal the operator surface does not name is an incomplete surface (§9). |

**The controlling D129 rulings are preserved, not replaced.** D129-R5 remains the authoritative
child-binding rule and D131 §4 implements it; D129-R6 remains the order-independence invariant and
D131 §4 satisfies it; D129-R7 is implemented by D131-R1; D129-R10 is implemented by D131-R6; D129-R11
is extended by D131-R10; **D129-R2's rejection of every D128 count stands entirely**; **D129-R8's
four requirements for a corrected proof are unchanged**; and **D129-R12 continues to require a
corrected-run capacity reconciliation this record does not construct.**

## 16. What this record does not do

- **It does not certify any D128 count.** D129-R2's rejection stands entirely.
- **It does not prove the repair against the real source.** No corrected parse of the real bulk
  archive was performed, and D131-R7 rules that an ordinary prefix cannot stand in for one.
- **It does not repair `CensusOrchestrator._parse_bulk`** (D131-R4), and repairing it now is
  expressly out of scope.
- **It does not tune performance** and **does not construct a capacity model** (§13).
- **It does not authorize** a corrected complete-source canary, any canary, any disposable world,
  E0, migration `0016`, network, SEC or HTTP access, or any catalog write. **Request ceiling remains
  `0`.**
- **It does not alter any authority constant.** All three remain `None`.
- **It does not supersede any record.** Decisions 121 through 130 stand as written, and **every
  D124-R5 gate carries forward intact**.
- **It does not rewrite persisted provenance.** Rows recorded under prior parser versions correctly
  describe the implementations that produced them.

## 17. The next sequence

1. **Bounded real semantic proof** of the corrected shard dispatch and per-reference parent binding —
   requiring a separately authorized semantic fixture or mode, because D131-R7 rules that an ordinary
   prefix parses zero shards.
2. **Bounded performance A/B.**
3. **Corrected-run capacity reconciliation** (D129-R12).
4. **Only then**, an owner decision on another complete-source canary.

Each step requires its own owner instrument. **E0 remains unauthorized throughout**, and reaching
step 4 is not reaching E0.
