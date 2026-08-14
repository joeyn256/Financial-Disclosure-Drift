# Decision 076 — M3.3 Pre-Acceptance Test, Governance, and Audit Infrastructure Optimization

```text
STATUS: ACCEPTED — OWNER M3.3 PRE-ACCEPTANCE INFRASTRUCTURE OPTIMIZATION
DATE: 2026-08-14
OWNER: Sol/GPT
OUTCOME: M3_3_DECISION_076_INFRASTRUCTURE_OPTIMIZED_READY_FOR_FRESH_FABLE_ACCEPTANCE
IMPLEMENTATION_AUTHORIZATION: BOUNDED — TEST-EXECUTION SCHEDULING, GOVERNANCE VALIDATION
  TOOLING, AND AUDIT REPRODUCIBILITY TOOLING, AND NOTHING ELSE
REAL_PRIVATE_PARSE_AUTHORIZATION: NO
REAL_SNAPSHOT_AUTHORIZATION: NO
REAL_SELECTION_AUTHORIZATION: NO
MANIFEST_ROOT_CONSTRUCTION_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
PRIVATE_EVIDENCE_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: none
REQUEST_CEILING: 0
```

**This record governs a bounded infrastructure stage.** It follows the owner's acceptance of the
MIN-A reference correction and precedes the fresh Fable 5 Maximum formal M3.3-I/R acceptance. It
changes no research definition, no methodology, no selector, no quota, no schema, no evidence
identity, and no authorization. It adds tooling and changes how the existing test suite is
scheduled.

**It authorizes no real execution.** M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 all remain separate,
unissued owner gates. Both real-path feasibility gates remain **OPEN** and unmerged.

## 1. Scope and status

Decision 076 does **not** reopen the MIN-A correction accepted at commit `96336ca`. That correction
stands as accepted: five Decision 075 citations corrected across three authorized files, production
AST and non-comment token stream identical, test executable bytecode identical, exactly one changed
constant, 140 assertions unchanged.

This record authorizes three separable pieces of work and one governance synchronization:

1. **Test-execution optimization.** A seven-worker parallel pytest path and a `check-fast` gate,
   with the serial path preserved unchanged as the reference.
2. **Governance validation tooling.** Two pure-standard-library repository gates, one for relative
   Markdown links and one for decision section citations.
3. **Audit reproducibility tooling.** A target-verification helper and a mutation-campaign runner
   held outside the package runtime, with machine-readable output.
4. **Governance synchronization.** This record, the registry, the decision index, and the status
   ledger.

## 2. Measured performance baseline

Measured on the project owner's 8-core machine at the entry baseline `96336ca`.

A serial full suite runs about **221 seconds**. Every non-pytest gate combined runs in about
**2.4 seconds** — lint 0.08, format check 0.03, mypy 0.64, secret scan 0.69, hygiene 0.17, config
validation 0.29, cohort print 0.24, SEC help 0.25. pytest is therefore approximately **98%** of a
full check, and it is the only component whose scheduling is worth changing.

Effort is deliberately **not** spent optimizing the static gates. Their aggregate cost is
negligible against pytest, and micro-optimizing them would buy nothing while adding risk.

## 3. R35 — Seven-Worker Full-Suite Development Standard

**Cite as:** *Decision 076 R35 — Seven-Worker Full-Suite Development Standard.*

The local development default for a full parallel suite is **seven workers**. A routine full pytest
execution on the owner's current machine must hold a **three-run median below 80.0 seconds**,
achieved without deleting tests, skipping tests, marking anything `xfail`, changing assertions for
speed, changing production methodology, weakening process-level tests, replacing subprocess tests
with mocks for timing, or changing any test's meaning.

Seven is a **measured local optimum, not a constant**. It is expressed as an overridable Make
variable precisely because it is machine-specific; a busier machine or a differently-shaped CI
runner is expected to choose its own value.

## 4. The serial reference path and `make check-fast`

The serial path is **preserved and never deleted**. `make test` continues to run an ordinary serial
pytest, and `make check` continues to run the same gates it always ran with serial pytest. xdist is
an optimization; a suite only ever observed under a scheduler has isolation that is assumed rather
than checked, so the unscheduled execution stays available for debugging, for `--pdb`, and for any
parallel/serial disagreement.

`make check-fast` is the owner-recommended routine full-validation command. It differs from
`make check` in exactly one respect — the parallel pytest path replaces the serial one. The same
gates run, in the same order, with nothing dropped, relaxed, or reordered.

Parallelism is **never** made mandatory. No `-n` enters `addopts`, so a bare `pytest` invocation
stays serial, and CI is not forced onto a worker count measured on different hardware.

The scheduling mode is `worksteal`, chosen by measurement rather than preference: at seven workers,
`worksteal` ran 60.75s and the previous implicit `load` ran 72.68s, both producing an identical
3949 passed / 1 skipped / 0 failed. `loadfile` is prohibited for this repository — grouping by file
pins the two large modules to single workers and makes them the bottleneck.

## 5. Markdown relative-link gate

`scripts/check_markdown_links.py`, exposed as `make links`, makes a broken relative Markdown link
structurally detectable rather than discoverable only when a reader follows it.

It resolves relative file targets against the containing document, ignores external schemes and
protocol-relative targets, treats a pure `#anchor` as an anchor rather than a path, strips a
fragment from a file target before resolving the file half, reads inline links and ordinary
reference definitions, and does not treat anything inside a fenced code block or an inline code
span as live navigation. A target resolves when it names a tracked path or a directory containing
one; filesystem existence alone is insufficient, since an untracked file resolves only on its
author's machine.

**Acceptance invariant: `UNALLOWED_BROKEN_LINKS = 0`.** No total link count is frozen; each run
reports the total its exact invocation observed.

## 6. Decision section-reference gate

`scripts/check_decision_section_refs.py`, exposed as `make decision-refs`, catches the defect class
that produced MIN-A: text citing a decision record by a section the record does not have.

The grammar was fixed **after** inventorying what the repository actually writes, not before. Three
section conventions are in live use and all three are cited:

1. **Numbered headings** — the dominant convention, and the only one Decision 075 uses.
2. **Ordered-list items under a numbered heading.** Decision 020 §14 records nine owner rulings as
   list items, and its fourth is cited as §14.4; Decision 021 §19 records eleven accepted
   limitations, and its eleventh is cited as §19.11.
3. **Numbered lines inside a fenced verbatim owner instrument.** Decision 040 §4 *is* the
   instrument, and citations into it name sections beyond that record's own ten headings.

Convention 3 is a deliberate widening with a stated cost: in a record quoting a long numbered list,
more bare integers count as sections than its own headings define, so detection there is weaker. It
is accepted because a gate that reports false failures against accepted history gets switched off,
which would be a worse outcome than reduced sensitivity in those specific records.

Decisions 001–006 predate the numbered convention and use prose headings. Nothing cites them by
section, so they need no exception.

**Acceptance invariant: `INVALID_DECISION_SECTION_REFS = 0`.** No reference count is frozen.

## 7. Exception discipline for both gates

Neither gate may be made green by rewriting accepted history. Immutable committed evidence, accepted
decision records, and accepted stage contracts are **not** edited to satisfy a checker introduced
afterwards.

Every exception in either gate is **exact**: it names one source file and one literal target or one
decision-and-section pair, with a reason and a governing status. **No wildcard, no pattern, no
directory-wide waiver, and no per-line escape marker exists in either gate.**

An exception entry that matches nothing **fails** the gate. A standing exemption for a defect that
is gone, or one whose target was mistyped and never matched anything, is itself a defect, and the
list cannot rot into a blanket exemption.

Exceptions are recorded in two classes, and the distinction is load-bearing:

* **Class 1 — immutable history.** The citation or link is wrong and the document may not be
  rewritten.
* **Class 2 — OPEN DEFECT.** The defect is live and correctable, but correcting it is outside this
  record's authorized paths. It is recorded, printed on every run, and returned to the owner. It is
  **not** an accepted exception, and the gate's output says so in those words.

## 8. Target-verification helper

`scripts/verify_target.py` replaces the eight-to-ten Git commands every review packet otherwise
re-runs and transcribes by hand. It verifies requested invariants — working tree clean, HEAD,
`origin/main` agreement, target tree, target parent, tag object, and an optional evidence-only child
relationship — and returns nonzero on any mismatch.

It **never** fetches, pulls, or mutates Git state, and it hard-codes no milestone-specific SHA:
every expectation is supplied by the caller.

## 9. Mutation-campaign runner and machine-readable output

The mutation runner lives outside the package runtime, under `scripts/dev/`. It is **never**
imported by production package code and is not part of the shipped package.

It operates only on an explicitly supplied disposable target, refuses the authoritative repository
unless an explicit disposable-target condition is satisfied, restores source after each mutation,
verifies source isolation and zero residue, supports positive controls, and emits machine-readable
JSON alongside the existing Markdown artifact.

The M1–M38 definitions are **recovered** from the durable campaign record at
`Docs/m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md`, never re-invented from vanished session
state, and that historical artifact is not modified. Any definition that cannot be truthfully
recovered is recorded as non-recoverable and stops for owner referral rather than being fabricated.

No wall-clock timestamp enters any governed deterministic project identity. **The JSON is audit
tooling and evidence; it is never selection methodology.**

The runner's arrival does **not** by itself require re-running the full campaign. The prior fresh
independent rereview already reproduced 38 killed, 0 survivors, 0 residue. This stage validates the
runner, not the campaign; whether a full rerun is warranted is the future acceptance reviewer's
call.

## 10. CI boundary

Local development optimization and CI optimization are **separate questions**, and this record
settles only the first.

The measured seven-worker optimum is specific to the owner's machine. CI is **not** switched to it,
and CI is **not** altered to force this stage through. The Makefile accepts a worker override so CI
may later choose an appropriate value from its own environment, once that value is measured there
rather than assumed from here.

## 11. Deferred optimizations

The following are **explicitly not implemented** by this record and are returned as
**DEFERRED — REQUIRES SEPARATE OWNER ARCHITECTURE DECISION**:

1. Redefining `evidence_reference` to remove the disposable SQLite byte digest.
2. Changing any governed receipt or evidence identity semantics.
3. Changing selection-result identity.
4. Changing snapshot or manifest identity.
5. Creating a new governance rule for self-recording a commit SHA.
6. DuckDB migration.
7. Production database changes.
8. Network changes.

The `evidence_reference` observation is useful, but changing canonical evidence semantics
immediately before a formal acceptance is the wrong risk trade.

## 12. Process rules P1–P7

Adopted for future review packets. These are **process** rules; they change no methodology.

1. **P1 — invariants over environment-dependent totals.** Require `broken == 0`, `failed == 0`, or
   an expected semantic set equality; do not require a reviewer to reproduce an incidental total
   such as a link or test count unless that total is itself governed. Require the reviewer to
   report the observed count and the exact command.
2. **P2 — real evidence root versus synthetic root.** Distinguish the owner's real evidence root,
   which is prohibited unless separately authorized, from a disposable synthetic rehearsal root,
   which is permitted and required for fixture-only rehearsal. Never write the ambiguous blanket
   phrase while simultaneously requiring a synthetic root.
3. **P3 — defect-in-correction handling.** If a correction introduces a new defect, classify it
   normally and return it to the owner. Do not treat it as out of scope merely because the original
   finding was closed.
4. **P4 — claim provenance labels.** Distinguish `INDEPENDENTLY_REPRODUCED`,
   `COMMITTED_EVIDENCE_VERIFIED`, `SOURCE_INSPECTION_ONLY`, and
   `INHERITED_FROM_ACCEPTED_PRIOR_REVIEW`. Never blur "the artifact says X" with "the reviewer
   reproduced X".
5. **P5 — gate timings.** Report elapsed time for meaningful gates, especially pytest, mutation
   campaigns, rehearsal scenarios, static checks, and audit tooling.
6. **P6 — machine-readable first.** Before asking a reviewer to parse a long Markdown evidence
   artifact by hand, check whether a machine-readable companion exists and use it.
7. **P7 — mechanical A/B branches.** State explicit, mechanically testable branches. Do not infer
   equivalence from similar English wording.

## 13. Findings returned to the owner

The section-reference gate found defects on its first run that no prior review had surfaced. They
are recorded as exact exceptions, printed on every run, and returned here. **Decision 076 does not
authorize correcting any of them.**

**Class 2 — OPEN DEFECTS in the live M3.3-I/R target.** Four citations of the same class as MIN-A,
which swept only Decision 075 citations and therefore left these standing:

```text
src/disclosure_drift/m3/execution_rehearsal.py   Decision 074 §3.1   (R31 is §2; the content is §2.1)
src/disclosure_drift/m3/offline_parse.py         Decision 071 §13    (071 has §1-§9; R25 is Decision 072 §5)
tests/unit/test_m3_offline_parse.py              Decision 071 §13    (same citation as the source module)
tests/unit/test_m3_3_boundaries.py               Decision 071 §11    (071 has §1-§9; intended target not inferable)
```

Correcting these requires its own bounded owner authorization, exactly as MIN-A did.

**Class 1 — wrong citations inside immutable accepted records.** Not correctable and not corrected:

```text
Docs/Decisions/decision_047_...md        Decision 032 §6.4   (032 §6 is prose; no numbered items)
Docs/Decisions/decision_063_...md        Decision 062 §21    (062 has §1-§14)
Docs/Decisions/decision_065_...md        Decision 062 §21    (062 has §1-§14)
Docs/Decisions/decision_registry.md      Decision 062 §21, Decision 032 §6.4  (mirrors its sources)
Docs/m3/templates/evidence_index.md      Decision 032 §6.4
Milestones/contracts/m3_2.md             Decision 065 §20    (065 has §1-§11)
```

**A correction to this record's own premise, recorded rather than smoothed over.** Of the five
pre-correction MIN-A references, an existence-based gate detects **three**, not five. Decision 075
genuinely has a section 6 — *OBS-6, the durable mutation-campaign record* — so the two bare
section-6 citations were **semantically** wrong while remaining **structurally** valid. Only the
`6.1` and `6.2` forms name sections that do not exist. No gate of this class can catch a citation
that points at a real but wrong section; that remains a reviewer's job.

**Two broken Markdown links** in immutable M3.2 review evidence, already known, are carried as
Class 1 exceptions and are not repaired.

## 14. What this record does not authorize

It authorizes no real execution, no network use, no SEC contact, no reacquisition, no private
evidence access, no migration, and no tag.

It does not modify production application logic, accepted selectors, selection stores, candidate
methodology, replay semantics, seal semantics, manifest hashing, migrations, network configuration,
the preregistration, or real E0/E1/E2 behavior.

It does not close either real-path feasibility gate.
`M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
`M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` both remain **ACTIVE** and are never merged into
one flag. It is not a Fable acceptance and claims none. `m3.2-complete` remains unmoved.

## 15. Next authorized action

Return to Sol/GPT. The owner will issue one fresh Fable 5 Maximum formal M3.3-I/R acceptance packet
against the final post-Decision-076 target. No further ultrareview, no Fable session, and no
M3.3-E0 work starts on the strength of this record.
