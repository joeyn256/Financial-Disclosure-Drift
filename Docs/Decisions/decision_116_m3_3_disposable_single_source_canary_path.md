# Decision 116 — The Disposable Single-Source Compact Canary Execution Path

```text
STATUS: ACCEPTED — OWNER IMPLEMENTATION INSTRUMENT, RULINGS R6–R13
DATE: 2026-08-18
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
OUTCOME: M3_3_D116_DISPOSABLE_SINGLE_SOURCE_EXECUTION_PATH
SUPERSEDES: Decision 113 §15's capacity disposition, as to this host only
E0_V3_EXECUTION_AUTHORIZATION: NO
REAL_CANARY_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

This record carries eight owner rulings and the bounded implementation they authorized: **R6–R9**
(§§2–4 and §12), issued 2026-08-18 with the path itself, and **R10–R13** (§§20–23), issued
2026-08-19 as a pre-acceptance correction of that implementation. It grants **no execution
authority of any kind**: all three activation constants remain `None`, migration `0016` remains
unapplied, no E0-v3 namespace exists, and the next real source parse requires a new owner instrument
that this record is not.

Decisions 091–115 remain binding on every point they name. Decision 113's compact derived-evidence
ruling — the contract `e0-compact-evidence/2`, the implicit-resolution rule, the compact
corroboration representation, and their digests — is unchanged in every particular.

## 1. The Decision 115 numbering gap

There is no `decision_115_*.md`. Decision 115 was an owner-side determination about the first real
single-source canary: it authorized the canary, and it stopped before creating a disposable world.
Like the Decision 102 gap that [Decision 103](decision_103_m3_3_e0_interruption_recovery.md) §1
records, it was issued as an owner finding rather than committed as a record. §§2–4 below restate
its accepted findings as entry state, so the committed repository carries them. The gap is expected,
not a missing file.

## 2. R6 — the capacity blocker is cleared, on this host

[Decision 113](decision_113_m3_3_compact_derived_e0_evidence.md) §15 classified the host
`LOCAL_CAPACITY_INSUFFICIENT_AFTER_D113` and §19 replaced the E0 preflight's stale disk predicate
with a requirement computed from measured densities and the planned work. Re-measured on the current
host under that same requirement:

| Term | Value |
|---|---|
| available | about `107.09 GiB` |
| required | about `90.54 GiB` |
| projected working state | about `69.33 GB` |
| overhead | about `1.05 GB` |
| governed reserve (§15) | `25 GiB` |
| projected remaining reserve | about `41.54 GiB` |
| shortfall | `0` |

Requirement identity `791618e03a8ed6028d6b0ba70f1fca4473d2434b52e99ec1ddddaec97dba2b31`.
`src/disclosure_drift/m3/capacity_plan.py` reproduces every term of it and is unchanged by this
record.

**Owner disposition.** `LOCAL_CAPACITY_INSUFFICIENT_AFTER_D113` is no longer the active host
blocker — `M3_3_D115_CAPACITY_GATE_OWNER_CLEARED`.

Two limits are part of the ruling rather than caveats on it. It is a statement about **this host at
this time**, not a permanent property of the projection; and **it is not E0-v3 authorization**.
Decision 113 §15's stop rule and its prohibition on further semantic compaction are untouched.

## 3. R7 — Decision 115 closed without executing

Decision 115 stopped before creating a disposable world, before constructing an execution command,
and before parsing any real source. No real execution attempt occurred. Its authorization is
**closed and may not be reused** — `M3_3_D115_EXECUTION_AUTHORITY_CLOSED_UNEXECUTED`. The first real
canary, the three-source canary, and the real replay proof named in Decision 113 §§16–18 all remain
**NOT RUN**.

## 4. R8 — the execution-path blocker

Decision 115 stopped because the repository had no accepted path that could run **exactly one**
governed planned source under the compact-evidence contract and be relied on to stop. Four
findings, accepted as entry state:

1. **No single-source driver.** `run_offline_metadata_parse` loads the whole plan through
   `load_planned_sources`, traverses every planned source, and has no exact one-source selector, so
   nothing but expectation stops it before source 2.
2. **The compact policy is not bound into the reachable driver.** The Decision 113 capacity model
   was measured under `e0-compact-evidence/2`, but `materialize_source_layer` constructs its
   `CensusCatalog` without an evidence argument and therefore under the full-observation default.
3. **The sidecar output is not wired.** `CompactSourceEvidence` and `CompactEvidenceSidecar` exist
   and are proved, and no reachable driver constructs either.
4. **The Decision 111 working-catalog machinery is unwired.** `working_catalog.py` holds the
   accepted run-local mechanism and no operator surface reaches it.

Confirmed blocker: `M3_3_D115_EXECUTION_PATH_BLOCKER_OWNER_CONFIRMED`. This record authorizes the
bounded implementation that closes it, and nothing beyond that.

## 5. The accepted architecture

An **additive, explicit, canary-only** operator path, clearly distinct from governed E0 execution:
the `m3 canary-source` command over `src/disclosure_drift/m3/single_source_canary.py`, plus a
one-source entry point (`select_planned_source`, `materialize_one_planned_source`) beside the
existing whole-plan driver in `src/disclosure_drift/m3/offline_parse.py`.

It is a second **entry point**, never a second parser: every parse call, identity, digest, and
durable row comes from the accepted modules. Fifteen properties are required of it, and each is
proved by test rather than asserted:

1. it accepts exactly one governed planned source, selected by `census_plan_sources.source_instance_id`;
2. the identifier must resolve in the frozen accepted plan;
3. an identifier outside the plan — including a path-shaped one — is refused, as is an ambiguous
   one; there is no path argument, no `source_id` shorthand, and no source-directory option;
4. it creates and uses an isolated Decision 111 working catalog;
5. the accepted operational catalog is opened `SQLITE_OPEN_READONLY` on every path, and no writer
   lease is taken on it;
6. it reads the immutable frozen source artifacts and writes nothing into the authoritative
   evidence root;
7. it binds `e0-compact-evidence/2` **explicitly** at the one `CensusCatalog` it constructs, so the
   full-observation default is unreachable by omission rather than merely unlikely;
8. it emits the Decision 112 §8 sidecar carrying the member manifest, the source evidence, the
   Decision 113 §8 resolution evidence, and the Decision 113 §9 corroboration evidence;
9. it terminates after exactly that source;
10. there is no loop and no continuation to a second source;
11. it returns the structured result surface §6 fixes;
12. it constructs no transport and imports no network-capable module;
13. it imports `m3/e0.py` nowhere, names no activation constant, and creates no E0 run namespace;
14. it applies no migration to any catalog;
15. it is general over planned sources — a streamed bulk archive and a single-payload artifact both
    run — so the later three-source canary and replay proof reuse it rather than growing a second
    parser architecture.

**The disposable world.** Every writable output lands beneath an operator-supplied work root that
is refused unless it lies outside the repository checkout **and** outside the private evidence root,
and is refused if it would contain that root. The world is create-once: `mkdir` without `exist_ok`,
a refused symlink, a refused pre-existing path. It holds the working catalog, its Decision 111
progress ledger, the compact sidecar, and one write-once result document. Nothing in it is promoted,
and nothing deletes it.

**Non-goals, stated so they are not read in.** No semantic compaction is added or changed; no
operational-catalog schema changes; no E0 gate is weakened, repurposed, or given an override; no
generic override is added to any governed surface; and no source plan semantics move.

## 6. Generality

The path is not written for `sec_bulk_submissions`. It accepts one valid planned source identity
and runs exactly that source: a streamed bulk archive goes through the accepted Decision 110 §8
bounded traversal, and a single-payload artifact is treated as its own single member, named by the
frozen store's own relative path — a property of the artifact rather than of the run. That is what
lets the later largest-source, median-source, and next-largest canaries and the replay proof reuse
this mechanism instead of growing a second one.

Generality is not permission. The path still fails closed against any identity the accepted plan
does not carry, and **this record authorizes executing no real source**. Its proofs run over
deterministic synthetic fixtures.

## 7. The disposable world

The separation is structural, not conventional.

**Read-only authoritative inputs.** The governed operational catalog — opened
`SQLITE_OPEN_READONLY` on every path, with no writer lease taken on it, so a held or stale lease is
not even reachable — the immutable frozen source artifacts, the accepted source plan, and the
authoritative identities.

**Writable non-authoritative outputs.** The Decision 111 run-local working catalog, its progress
ledger, the run-local compact sidecar, and one run-local result document. All four live inside one
disposable world beneath an operator-supplied work root, which is refused unless it lies outside the
repository checkout **and** outside the private evidence root, and refused if it would contain that
root. Containment is decided on fully resolved, case-folded paths, so neither a symlink nor a case
variant can launder it.

No writable output lands in the private evidence root, and no canary output mutates the operational
catalog. Nothing is promoted: the accepted `promote_working_catalog` primitive is named nowhere on
this path.

## 8. The compact-evidence contract

The path binds the accepted `e0-compact-evidence/2` contract explicitly, at the one `CensusCatalog`
it constructs. Every accepted semantic is preserved unchanged — canonical accession evidence,
canonical registrant evidence, the accession-to-registrant relation, conflict evidence, malformed
evidence, quarantine, structural failures, provenance exceptions, implicit and explicit Decision 012
resolutions, compact corroboration, and the replay identities.

**No additional semantic compaction is authorized. Semantic compaction remains closed.**

One additive, non-semantic accessor is added to the sidecar: a member-manifest identity over the
rows it already holds, folded by the **same** rule the sidecar's own identity uses, with that rule
stated once so the two cannot drift into two renderings of the same rows. It defines no new
evidence, changes nothing persisted, and is not a parallel digest definition.

## 9. The required result surface

One invocation must let a later execution report determine, without re-opening the world: the
source identity and its plan position; the source artifact identity and byte length; the terminal
disposition and both parser states; parsed, member, quarantined, and structural counts; the
canonical accession, registrant, and substantive-relation counts; the Decision 094 §9.5 totality
object; the resolution split, implicit and explicit; the corroboration counts; the member manifest
digest, the projection digest, the `ResolutionDigest`, the `CorroborationDigest`, and the compact
evidence identity; the working-catalog identity and its world-relative name; and the sidecar's
world-relative name.

Resource sampling stays an outer operator concern, and **no measurement is fabricated**: a source
with no corroboration reports an empty digest rather than an invented one. The result document
carries no absolute path — both world artifacts are named relative to the disposable world.

## 10. Create-once and rerun safety

The world directory is created with `mkdir` without `exist_ok`, which is atomic, so an identity
whose world exists is refused rather than resumed, repaired, or overwritten. A symlink at the work
root or the world path is refused before anything is created. The run identity is validated as a
filesystem-safe slug rather than trusted, because it becomes a directory name. The accepted
Decision 111 working catalog supplies its own refusal to adopt a populated file. The result
document is written with `O_CREAT | O_EXCL`, so completed run-local evidence has no window in which
it could be replaced. A successful world is never cleaned up automatically, and no promotion occurs
on any path.

No new global persistent governance state is created.

## 11. The bounded change set

Source: `src/disclosure_drift/m3/single_source_canary.py` (new); the one-source entry point and its
selector in `src/disclosure_drift/m3/offline_parse.py`; the additive sidecar accessor in
`src/disclosure_drift/m3/compact_evidence.py`; the operator surface in
`src/disclosure_drift/cli.py`. Tests: `tests/unit/test_d116_single_source_canary.py` (new).
Documentation: this record, its registry line, and the two §12 corrections.

Nothing else is touched. No migration file, no historical Decision 097 text, no M3.3 historical
contract, no mutation-campaign artifact, no immutable v1 or v2 evidence, and no SEC acquisition or
network code.

## 12. R9 — the two bounded documentation corrections

Two current-state claims had stopped being true and are corrected, and nothing else:

1. **`Docs/change_impact_map.md`** reported the live mutation-anchor partition as 38 recovered / 37
   resolved / `['M19']` superseded. Accepted
   [Decision 114](decision_114_m3_3_m21_live_anchor_supersession.md) disposed M21 as well, so the
   current partition is **38 recovered / 36 resolved / `['M19', 'M21']` superseded**, verified
   against the shipped tree by the live audit tooling rather than copied. The Decision 097-specific
   historical prose is preserved.
2. **`Milestones/STATUS.md`** still recorded `LOCAL_CAPACITY_INSUFFICIENT_AFTER_D113` as the active
   blocker. Under §2 that condition is cleared; the active blocker is now acceptance of the
   execution path. The corrected status states that Decision 115 did not execute, why it stopped,
   that E0-v3 remains unauthorized, that migration `0016` remains unapplied, and that current work
   remains M3.3 pre-E0.

Neither correction rewrites a historical claim whose date and context make it correct, and neither
is a general documentation cleanup.

## 13. What the tests must prove

**One-source boundary.** The requested plan source runs; the second planned source is untouched,
asserted on its own durable rows and its unchanged `parser_state`; an identifier outside the plan is
refused; a path-shaped identifier is refused for the same reason any non-plan value is; an ambiguous
identifier is refused; and the whole-plan driver is named nowhere on the path, so no all-source
fallback can be reached by a later edit.

**Disposable isolation.** The operational catalog is byte-identical after a run and still holds no
parse rows; every write landed in the working catalog; a work root that is, lies inside, or contains
the private evidence root is refused, as is one inside the checkout; and nothing is promoted.

**Compact contract.** The sidecar exists and states `e0-compact-evidence/2` at schema version 2; the
member manifest, source evidence, resolution evidence, and corroboration evidence are present; and
the full-observation default is excluded **by comparison** — the same one source run under the full
contract yields the identical canonical accession set and materially more observation and resolution
rows.

**Determinism.** Two independently built worlds — separate archives on disk, separate catalogs,
separate work roots, separate run identities — reach identical member-manifest, projection,
resolution, corroboration, and compact-evidence identities. This is fixture-level determinism and is
**not** authorization for another real-source run.

**Fail-closed.** A duplicate world identity is refused; a populated world is never adopted;
completed run-local evidence is never overwritten; an unlawful run identity is refused before
anything is created; and a failure leaves the operational catalog byte-identical.

**Separation.** The path imports no transport module and does not import `m3/e0.py`, proved in a
clean interpreter by differencing the module's own transitive closure; it names no activation
constant and no E0 run namespace; and no migration is applied to either catalog.

## 14. Real-data prohibition

This record authorizes implementation and tests only. **No real SEC source was parsed.** The real
`sec_bulk_submissions` artifact was not opened, no complete real source was run, no ad-hoc real
scratch proof was performed, and no D115 real-canary run identity or world was created. The next
real source execution requires a new owner instrument.

## 15. Validation

Targeted tests and touched-file lint, formatting, and type checks during implementation; then
exactly one full acceptance gate. Every full-gate invocation is reported truthfully in the session's
completion packet.

## 16. Commit authority

One local commit, conditional on the entry state passing, the implementation satisfying §§4–13, the
§12 corrections being truthful and bounded, the targeted tests passing, the final gate passing, no
real source having been executed, and only authorized files having changed. No amend of the parent,
no push, no tag, and no rebase.

## 17. Nonchanges

Preserved entire: the operational catalog's content; the private authoritative evidence; the frozen
SEC source artifacts; migration head `0015` and the absence of `0016`; all three E0 activation
constants at `None`; the absence of an E0-v3 namespace; both tracked network switches at `false`;
the Decision 110 streaming architecture; the Decision 111 working-catalog architecture; the
Decision 112 compact-evidence semantics; the Decision 113 compaction and capacity semantics; and the
Decision 114 M21 disposition.

## 18. The completion token

`M3_3_D116_DISPOSABLE_SINGLE_SOURCE_EXECUTION_PATH_READY_FOR_OWNER_REVIEW` states that the
implementation is ready for owner review. **It is not owner acceptance**, it is not an
execution-path acceptance token, it is not a canary success token, and it is not an E0-v3 token.

## 19. What this record does not do

It does not accept the implementation, does not authorize running any real source, does not reopen
Decision 113's compaction ruling or its stop rule beyond the host capacity disposition §2 states,
does not change any frozen research definition, cohort, quota, seed, or selector, does not add or
alter a migration, does not write to the private evidence root, and does not authorize a push or a
tag.

## 20. R10 — the final-gate procedure

The D116 full-gate history is **accepted**. The first `make check-fast` was terminated after the
implementation tree changed underneath it and therefore supplies no claimed verdict; the subsequent
gate, run on the final D116 tree, passed at **4,733 passed / 1 skipped / 0 failed**. No procedural
finding remains open on it, and the superseded tree is not re-run.

The rule the ruling fixes for anything that follows: **a gate is run on a finished tree.** All
source and documentation edits complete first, then exactly one `make check-fast`, and no file is
edited while it runs. A gate whose tree changed under it is reported as terminated and claims
nothing. If a final gate fails, only directly in-scope corrections are made and one further final
gate is permitted — never a recursive polish loop — and every invocation is reported truthfully.

## 21. R11 — the disposable work-root invariant is enforced at the production library boundary

**Classification: MAJOR, corrected before acceptance.**

As first implemented, the §7 work-root boundary was established at the operator entry point, and
`run_single_source_canary()` accepted an *already-validated* work root. A direct production caller
of the library function could therefore reach a location the operator surface would have refused —
the invariant existed, but it belonged to the wrapper rather than to the run.

**The rule.** The invariant belongs inside the production library execution boundary. A direct
caller of `run_single_source_canary()` must not be able to create a writable world at the
authoritative private evidence root, beneath it, at a parent that contains it, inside the repository
checkout, through a relative or unresolved disposable root, or at any other location
`require_disposable_work_root()` already prohibits. The refusal happens **before** any directory,
working catalog, sidecar, or result document exists.

**One rule, not two implementations.** `require_disposable_work_root()` remains the single place the
rule is stated, unchanged. A boundary function `require_canary_work_root()` applies that primitive to
each evidence root a run must stay clear of, and states no containment arithmetic of its own:

1. the evidence tree the run itself reads its frozen artifacts from, taken from the run's own
   `DataTree` input rather than declared beside it, so it cannot disagree with what the run opens;
2. the authoritative private evidence root the **process** declares, whenever it declares one — read
   from the environment rather than from an argument, so it is not a caller's to route around. In
   ordinary operation these are the same root, because the operator surface builds the tree from it.

The repository checkout is derived from the package's own location, and absoluteness and symlink
resolution come from the same primitive, so none of the three is declared by the caller either.

**The operator surface keeps its early refusal**, so an operator learns the rule immediately and
without a traceback. That refusal is now a convenience; the run's own is the invariant, and both go
through the one primitive so they cannot disagree about a lawful root.

**What this does not change.** Create-once world semantics, the strictly read-only handle on the
accepted catalog, the compact-contract binding, the digests, the result surface, E0, the source
plan, the migrations, and the network posture are all untouched. No architectural change beyond
sharing and enforcing the existing path-safety invariant was required or made.

**What the tests must prove.** Direct library calls — not merely operator calls — fail closed for
each prohibited category: a work root that is the private evidence root, one inside it, one that
contains it, one inside the repository checkout, a relative one, and a symlink that resolves onto
the private evidence root. For each refusal: no world directory, no working catalog, no sidecar, no
result document, and the accepted operational catalog byte-identical with no parsed rows. Also
proved: the refusal names no path; the process-declared authoritative root is refused even when the
declared tree is elsewhere, while a lawful root still runs with that variable set; one lawful direct
invocation still builds its world and its result on a tiny fixture; the operator surface and the run
refuse the identical root; the boundary calls the accepted primitive rather than restating it; and
the create-once protections stay green.

## 22. R12 — a single-payload source is one logical manifest member

**Owner accepted.** For a governed planned source whose frozen artifact is a single payload rather
than a membered archive:

- the frozen artifact **itself** is the single logical member;
- its frozen `relative_storage_path` is the deterministic logical member name;
- the compact member-manifest binding binds that artifact's governed payload identity and length
  under the **same** accepted folding semantics the manifest already uses;
- no absolute host path is part of the identity;
- the representation is deterministic across independent worlds.

This extends the accepted member representation to an already planned source class. It is **not**
new semantic compaction, **not** permission to change archive-member semantics, and **not**
permission to change the accepted digest folding rules — all three remain closed exactly as §8
states.

The proofs are preserved and pinned: independent-world digest equality for both a streamed archive
source and a single-payload source; exactly one manifest member for the single-payload source, named
by the `relative_storage_path` read back from the catalog rather than restated; the member's payload
digest and byte length equal to the source artifact's; no absolute path in the member name or the
result surface; and — pinned on a clone, so no accepted semantics move to state it — the member name
is *inside* the member-manifest identity, since altering it moves that identity while an unaltered
clone reproduces it exactly.

## 23. R13 — the two navigation entries

Both cleared before acceptance, and nothing else:

1. **`Docs/decision_index.md`** gains the repository-consistent Decision 116 navigation entry, in
   the formatting convention of the surrounding entries. No historical entry is rewritten.
2. **`Docs/change_impact_map.md`** gains a minimal Decision 116 change-set entry. §12's earlier
   authorization covered the R9 correction only, so the record's own change-set navigation was
   correctly absent until now. The entry is navigational and concise: the additive `m3
   canary-source` operator surface, single-source selection, the Decision 111 working-catalog
   wiring, the explicit `e0-compact-evidence/2` binding, the compact sidecar and digest emission,
   the E0 / network / migration separation, the §21 library-boundary work-root enforcement, the R6
   and R9 status-truth corrections, and the §22 single-payload logical-member ruling. It is not a
   historical rewrite and not a general documentation cleanup.

The correction's own change set is `src/disclosure_drift/m3/single_source_canary.py`,
`tests/unit/test_d116_single_source_canary.py`, this record, its registry line, and the two
navigation files named above. `Milestones/STATUS.md` is touched only where a statement became
factually false because of this correction, and it pre-claims no owner acceptance.

**This record is still not owner acceptance of the implementation.** §18's token states readiness
for review; the correction token `M3_3_D116_CORRECTION_READY_FOR_OWNER_ACCEPTANCE` states the same
thing about the corrected tree, and neither authorizes a real source, a push, or a tag.
