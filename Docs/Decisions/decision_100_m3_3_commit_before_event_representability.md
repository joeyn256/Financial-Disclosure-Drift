# Decision 100 — PRE-E0 Category-A Commit-Before-Event Representability

```text
STATUS: ACCEPTED — OWNER RULING ON THE RESIDUAL D094 §9.2 REPRESENTABILITY GAP
DATE: 2026-08-16
OWNER: Joey authorization; Sol/GPT technical ruling
OUTCOME: M3_3_D100_COMMIT_BEFORE_EVENT_REPRESENTABILITY_CLOSED
CORRECTION_BASELINE: 7b8a03b456291778e67db0ada2fa576f97ff8e2b
PRE_E0_IMPLEMENTATION_ACCEPTANCE: PENDING SOL OWNER ACCEPTANCE
M3_3_E0_OPERATIONAL_STATE: HELD
ACCEPTED_CATALOG_MIGRATION_EXECUTION_AUTHORIZATION: NO
M3_3_E0_EXECUTION_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
```

This record dispositions **one** residual PRE-E0 MAJOR: a category-A database boundary that
Decision 094 §9.2 requires a failed E0 terminal to represent, but that the interruption-state and
schema rules as previously implemented prohibited it from representing.

It reopens nothing else. Decisions 094–099 remain binding on every point they name — the canonical
relation, the complete association set, the no-fallback and no-entity-invention rules, R96's
durable-event-derived failure terminals, R97's completion-receipt binding, R98's corrections, the
D096 projection proof, the D097 M19 disposition, the sixteen-table write set, source-bound disabled
execute constants, forward-only recovery, and the non-self-referential identity rules.

## 1. Ruling R99 — the reproduced gap

Reproduced against a disposable catalog at baseline
`7b8a03b456291778e67db0ada2fa576f97ff8e2b` with the three-file correction WIP applied:

`run_offline_metadata_parse` commits **one plan-row boundary per category-A source**, inside the
call — `census_parser_runs` and then a committed `census_plan_sources.parser_state` transition —
while every `SOURCE_DISPOSITION_RECORDED` event is appended only after that call returns. Failing
the third `_parse_source` therefore left, measured rather than inferred:

- two durably committed category-A boundaries in `census_plan_sources`, with two
  `census_parser_runs` rows;
- zero durable `SOURCE_DISPOSITION_RECORDED` events;
- a frozen terminal with `status = failed`, no `interruption_state`, and `source_results = []`.

Decision 094 §9.2 requires the failed set to contain "every durable event plus any independently
observed category-A database boundary lacking its event". Two such boundaries existed and none was
stated. Two independent causes were confirmed:

1. **Membership was gated on the call stack.** The derivation admitted a boundary row only when the
   run's in-flight interruption variable already read `after_e0_source_commit_before_event`. That
   variable advances only after the parser returns, so a failure inside the parser read
   `during_e0_source_parse` and every boundary row was dropped.
2. **A failed run could not state the window.** §8.1 conditions `failure.interruption_state` on an
   interrupted status, and §9.3 makes that state mandatory for a `ledger_event_present = false`
   row. A boundary left by a domain failure rather than an operator interrupt was therefore
   required by §9.2 and prohibited by §8.1 at the same time — including in the already-disclosed
   window *after* the parser returns, where failing the first disposition append left all
   category-A boundaries durable and the whole set unstatable.

## 2. Ruling R100 — the disposition

**`after_e0_source_commit_before_event` names a durable state, not a call-stack position.** §9.3
states it in exactly those terms: the value is required whenever "persisted category-A parser or
parser-state evidence proves a source commit occurred before its ledger append". The accepted §10.2
vocabulary therefore already represents this state with an existing value, and that exact value is
used. **No vocabulary amendment is required and none is made**: the sixteen values in
`INTERRUPTION_STATES_V4` are unchanged, and `src/disclosure_drift/m3/receipt.py` is untouched.

The dependency is inverted accordingly:

1. **Membership is derived from durable evidence alone.** The failed set is every durable
   `SOURCE_DISPOSITION_RECORDED` event plus every independently observed category-A
   `census_plan_sources.parser_state` boundary lacking one — with no gate on the caller's in-flight
   variable. A pair attested both ways is one row, attributed to its durable event.
2. **The disclosed state is derived from the resulting rows.** If any row carries
   `ledger_event_present = false`, the run discloses `after_e0_source_commit_before_event`. The
   derivation runs ahead of the tail `FAILED`/`INTERRUPTED` event, so the ledger event and the
   terminal state one interruption state rather than two.
3. **The presence rule is §8.1 widened by exactly §9.3 and no further.** A terminal carrying a
   boundary row states the window whatever its status; a terminal carrying none may state an
   interruption state only when interrupted. The validator continues to refuse any value but
   `after_e0_source_commit_before_event` wherever a boundary row appears, so the widening cannot
   carry an arbitrary state onto a failed record.
4. **The receipt is unchanged.** §10.1 conditions the *receipt's* `interruption_state` on an
   interrupted status and refuses it otherwise. A failed run states the window on the terminal,
   which §9.3 governs, and omits it from the receipt, which §10.1 governs.

Provenance is not assumed. §9.1 preflight and the under-lease recheck both refuse unless **every**
accepted plan row is still `not_started`, and both run before the run namespace exists — so a moved
plan row observed at disclosure time was moved by this run, and `parser_state_before` is
`not_started` as measured, not as invented. Only a category-A source receives a `parser_state`
transition under the accepted write set, so category B and C cannot reach the exception.

Nothing is fabricated and nothing is weakened. §9.2 is unchanged; no observation, scalar, or entity
fallback is introduced; no completion is inferred from an ambiguous state; a source with no durable
boundary and no durable event produces no row; and unreadable boundary evidence fails closed to
`UNDETERMINED / NOT COMPLETE` exactly as an unverifiable ledger already does.

## 3. Ruling R101 — the tail-event projection defect

Found while implementing R100 and fixed with it, because R100's guarantee that all durable records
of one run state one interruption state cannot hold otherwise.

The `INTERRUPTED` ledger event was appended by copying the terminal's whole `failure` object. That
object carries `catalog_state_observed`, which §10.2's closed `INTERRUPTED` projection does not
permit, so **every** such append was refused and the refusal was swallowed by the surrounding
`suppress`. An interrupted run recorded no `INTERRUPTED` event at all. The tail event is now
projected to §10.2's exact key set. `FAILED` was already projected correctly and is unchanged.

## 4. Schema representability

Every lawful combination is representable after the correction. There is no state in which accepted
durable evidence exists and the schema forces it to be omitted.

| | Durable boundary | Durable event | Disclosed |
|---|---|---|---|
| A | no | no | no row; nothing invented |
| B | — | yes | one row, `ledger_event_present = true` |
| C | yes, parser returned | no | one row, `ledger_event_present = false`, window stated |
| D | yes, still inside the parser | no | identical to C |
| E | yes | yes | exactly one row, attributed to the event |
| F | unverifiable ledger **or** unreadable boundary evidence | — | no terminal; `UNDETERMINED / NOT COMPLETE` |

Rows C and D hold on a `failed` run and on an `interrupted` one alike.

## 5. Exact implementation paths

```text
src/disclosure_drift/m3/e0.py
tests/unit/test_m3_e0.py
Docs/m3/e0_execution_record_spec.md
```

Plus this record and its registry and index rows, under §7. No other source, test, migration,
configuration, accepted evidence, historical Decision, review artifact, or private state is touched.
`src/disclosure_drift/m3/receipt.py` is deliberately **not** in this set: the accepted interruption
vocabulary does not change.

## 6. Required proof

1. A category-A failure **inside** `run_offline_metadata_parse`, after the durable database
   boundary and before it returns, produces exactly one lawful failed-set row.
2. The production terminal loader accepts that record.
3. A source is not duplicated when its ledger event is also durable.
4. A source with no durable boundary is not invented.
5. Non-category-A sources gain no exception, measured against the production classifier.
6. `source_result_counts` reconciles exactly with `source_results`.
7. Restoring either half of the pre-D100 rule makes the targeted proofs fail.

One bounded disposable mutation control per half, applied to the production source and reverted.

## 7. Governance recording

This record, one `Docs/Decisions/decision_registry.md` row, and one `Docs/decision_index.md` block
are recorded together with the implementation, in one local commit, only after all required
validation passes. Nothing is staged beyond the paths in §5 and those three governance paths.

## 8. Acts still prohibited

No accepted private-root discovery or access; no accepted-catalog open; no migration `0014`, `0015`,
or `0016`; no transition; no E0; no linkage diagnostic; no persistence bridge; no E1, E2, or M3.4;
no activation-constant change; no network, SEC, HTTP, DNS, socket, acquisition, package
installation, fetch, pull, push, or tag; no receipt or evidence rewrite; and no history rewrite.

```text
RESULT_TOKEN: M3_3_D100_COMMIT_BEFORE_EVENT_REPRESENTABILITY_CLOSED
NEXT_ACTION: SOL OWNER ACCEPTANCE REVIEW OF THE CORRECTED PRE-E0 TARGET
M3_3_E0_OPERATIONAL_STATE: HELD
```
