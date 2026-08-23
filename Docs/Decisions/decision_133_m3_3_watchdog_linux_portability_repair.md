# Decision 133 — The Watchdog Linux Portability Repair

```text
STATUS: ACCEPTED — OWNER RULING / CROSS-PLATFORM OPERATIONAL REPAIR
RECORD_TYPE: OWNER GOVERNANCE PUBLICATION OF A COMPLETED OPERATOR-TOOL REPAIR —
  RETROSPECTIVE BY DESIGN; THE CODE SHIPPED FIRST BECAUSE THE LINUX HALF OF THE CLAIM
  COULD NOT BE ESTABLISHED ON THE DEVELOPER PLATFORM
DATE: 2026-08-22
OWNER: Joey authorization; Sol/GPT-5.6 owner rulings
CLASSIFICATION: OPERATOR_TOOL_PORTABILITY_REPAIR_ONLY
ACCEPTANCE_TOKEN: M3_3_D133_LINUX_PORTABILITY_REPAIR_OWNER_ACCEPTED
PUBLICATION_TOKEN: M3_3_D133_GOVERNANCE_PUBLICATION_AUTHORIZED
OUTCOME: D131_WATCHDOG_LINUX_COMMAND_AUTHENTICATION_REPAIRED_AND_CI_PROVEN
DEFECT_CLASS: PRODUCT_DEFECT — OPERATOR TOOLING; NOT A SEMANTIC-PIPELINE DEFECT
FAILURE_MODE: FAIL-SAFE — LEGITIMATE TARGET REFUSED; UNINTENDED TARGET NEVER SIGNALLED
D128_SEMANTIC_DISPOSITION: UNCHANGED. D129-R2'S REJECTION OF EVERY D128 COUNT STANDS ENTIRELY
D131_DISPOSITION: OPERATIONAL ACCEPTANCE RESTORED CROSS-PLATFORM; SEMANTIC ACCEPTANCE NEVER
  INVALIDATED
D132_DISPOSITION: UNAFFECTED AND UNCHANGED; NO D132 CLAIM IS REOPENED
REVERT_PERFORMED: NO — AND NONE WAS WARRANTED
SOURCE_WIDE_CLAIM: NONE
CORRECTED_CANARY_AUTHORIZATION: NO
COMPLETE_SOURCE_AUTHORIZATION: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_0016_AUTHORIZATION: NO — AND NO MIGRATION IS IMPLIED BY THIS REPAIR
PERFORMANCE_AUTHORIZATION: NO
CAPACITY_RECONCILIATION_STATUS: D129-R12 UNRESOLVED
NETWORK_AUTHORIZATION: NONE
SEC_AUTHORIZATION: NONE
HTTP_AUTHORIZATION: NONE
REQUEST_CEILING: 0
PRE_NETWORK_BLOCKER: CensusOrchestrator._parse_bulk — OPEN, DELIBERATELY UNREPAIRED
```

The owner's governance publication of the cross-platform conformance repair that four Linux CI
failures exposed in the watchdog contract
[Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §9 (D131-R6, D131-R9)
accepted.

## 1. What this record is, and what it is not

**It is a repair of operator tooling, and of nothing else.** The defect lived in
`scripts/m3/canary_watchdog.py` — the governed stop/probe/monitor surface — and specifically in how
that surface *observes* a target's command line. It did not live in a parser, a traversal, a
persistence path, a schema, or a policy constant. **No semantic result of any prior record changes
because of it.**

**It is retrospective by design, and the reason is the defect itself.** The code shipped at
`977a811b…` **without** a governance record, deliberately: the claim D133 has to make is a claim
about **Linux**, and the developer platform is macOS, where the defect is invisible by construction
(§3). A record published from macOS alone could have asserted the repair but could not have
established it. **The record therefore waited for a fresh push-triggered Ubuntu CI result**, and §7
is that result. This is a different shape from
[Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md), which entered with its
code in one commit, and from [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) and
[Decision 130](decision_130_m3_3_d128_archival_and_reclamation.md), which recorded work finished
elsewhere: here the delay is a **methodological requirement**, not a convenience.

**The failure was fail-safe, which is why no revert was warranted.** The watchdog refused to stop
legitimate targets. It did **not** signal anything it should not have (§10). A defect that withholds
an action is recoverable by repairing it; a defect that performs the wrong action against the wrong
PID is not, and the D131 design is what kept this one in the first category.

**It certifies no count and moves no semantic boundary.**
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §4 (D129-R2)'s rejection of every
D128 semantic count stands entirely, and
[Decision 132](decision_132_m3_3_bounded_real_semantic_proof.md)'s bounded real semantic proof is
untouched (§9).

**It closes no pre-network blocker and authorizes no execution.**
`CensusOrchestrator._parse_bulk` still carries the Defect A dispatch, exactly as
[Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §12 (D131-R4) left it
(§11), and nothing here authorizes a performance experiment, a capacity reconciliation, a canary,
E0, network, or a migration.

## 2. Entry state

This publication entered at the verified baseline below, which is also the commit the repair itself
produced:

| Item | Value |
|---|---|
| Branch | `main` |
| `HEAD` | `977a811ba6177828853e1b0d16b2d7fa2de29b02` |
| Tree | `91127b8cbc0431a3d9be507bc06b689812d7872e` |
| `origin/main` | equal to `HEAD`, `0` ahead / `0` behind |
| Working tree | clean; nothing staged |
| Latest governance record | [Decision 132](decision_132_m3_3_bounded_real_semantic_proof.md) |
| Decision 133 | absent |
| Migration head | `0015_m33_verified_document_evidence.sql`; `0016` absent |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` |
| `network.enabled` | `false` |
| `network.m3_acquire_enabled` | `false` |
| Request ceiling | `0` |

## 3. The root cause — D133-R1

**What the D131 watchdog asked for.** Exact command-line authentication read the target's command
line with:

```text
/bin/ps -o command= -p PID
```

**What Linux returned.** On Ubuntu with `procps`, `ps` truncates `-o command=` to **80 columns**
when its stdout is not a terminal — which is exactly what `subprocess.run(..., capture_output=True)`
gives it. A canary's command line is a virtualenv interpreter path followed by an absolute script
path, comfortably past that width, so **the expected target substring fell off the end of the
observed text**.

**What the watchdog then did, correctly.** It compared the expectation against a truncated
observation, found no match, and **failed safe**:

```text
STOP_REFUSED_TARGET_MISMATCH
```

**The consequence.** Every legitimate long-command target on Linux authenticated as a refusal and
**was never signalled**. The stop path was unusable on that platform for exactly the processes it
exists to stop.

**Why the local gate could not see it.** macOS BSD `ps` returns the whole command line in the same
condition. The developer platform therefore produced a passing observation from an unrepaired
implementation, and **no end-to-end test written on macOS could have failed**. This is a
platform-conditional escape, not a gap in the D131 validation discipline: the local gate was run and
was green, and it was green truthfully about macOS.

**The classification is `PRODUCT_DEFECT` in operator tooling.** It is **not** a
`PARSER_IMPLEMENTATION_DEFECT` and shares nothing with the two defects
[Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §§5–6 recorded. No filing, record,
accession, reference, registrant binding, or provenance value was ever affected by it.

## 4. The minimal repair — D133-R2

**The accepted repair, in full:**

```text
/bin/ps -ww -o command= -p PID
```

`-ww` requests **unlimited output width** and is honoured by **both** BSD `ps` and `procps`, so one
argv serves both platforms with no branch, no `platform.system()` test, and no second code path to
keep in agreement. **D131-R6 and D131-R9 require the *exact* command line, not a prefix of it**, and
unlimited width is what makes the observation match the contract.

**No `/proc` fallback was needed or added.** A `/proc/PID/cmdline` reader would have been a
Linux-only second implementation of an answer the portable one already gives correctly.

**What the repair deliberately does not touch:**

| Preserved contract | Status |
|---|---|
| Strictly positive PID domain (`pid > 0`, stated once in `non_targetable_pid_detail(...)`) | unchanged |
| The `-o state=` process-state probe (fixed short field; never truncated) | unchanged |
| Exact-target authentication semantics, including `STOP_REFUSED_EMPTY_EXPECT_COMMAND` | unchanged |
| `SIGINT`-only policy, with **no** `SIGTERM`/`SIGKILL` escalation | unchanged |
| `STOP_FAILED` on a surviving target, at exit `4` | unchanged |
| `ProcessLookupError` → already gone | unchanged |
| `PermissionError` → not success | unchanged |
| The `lsof -nP -a -p PID -i` intersection network probe | unchanged |
| `MEMBER_COUNT_INCONSISTENT` at exit `5` | unchanged |

**The change set is two files.** `scripts/m3/canary_watchdog.py` (`+11 / -2`, the argv plus the
docstring that records why the option is load-bearing) and
`tests/unit/test_d131_signal_and_monitor.py` (`+38 / -0`, one additive test) — `2` files, `49`
insertions, `2` deletions, published at `977a811b…`. **No production package byte, configuration,
schema, migration, or authority constant is touched.**

## 5. Regression protection — D133-R3

**The added test:**

```text
tests/unit/test_d131_signal_and_monitor.py::test_the_command_probe_asks_ps_for_unlimited_width
```

**It authenticates the actual `ps` argv, not source text.** It captures the argument vector the
probe constructs and asserts both that `-ww` is present and that the whole vector equals
`["/bin/ps", "-ww", "-o", "command=", "-p", "4242"]`, driving the probe with a stdout string longer
than `80` columns so the strip is exercised on text the unrepaired probe could not have returned
whole.

**Why the argv is the right claim, and a behavioural assertion is not.** The four originally failing
tests **still pass on macOS without `-ww`** — that is precisely how the defect escaped. A test whose
subject is the observed *behaviour* therefore cannot protect this repair on the developer platform;
only a test whose subject is the *request* can. **Asserting the argv is the one check that fails on
either platform the moment the option is dropped.**

**Mutation proof.** Removing `-ww` from the probe is **killed by that exact test**. The guard is
platform-independent and needs no Linux runner to do its job.

## 6. Local validation — D133-R4

| Item | Value |
|---|---|
| Command | `make check-fast` |
| Exit status | `0` |
| Runs | exactly once |
| Collected | `4900` |
| Passed | `4899` |
| Skipped | `1` |
| Failed | `0` |

**The single skip is pre-existing and unrelated** — `tests/unit/test_m23_pilot_manifest.py:429`, the
same skip [Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §14 recorded.

**All local gates passed**: lint, format check, full mypy, the full suite, secret scan, repository
hygiene, Markdown link check, decision section-reference check, config validation, cohort print, and
SEC help.

**The collected total moved from `4899` to `4900`**, which is the one added regression test and
nothing else.

## 7. The Linux CI proof — D133-R5

| Item | Value |
|---|---|
| Workflow | `CI` |
| Run ID | `32605572777` |
| SHA | `977a811ba6177828853e1b0d16b2d7fa2de29b02` |
| Result | **`SUCCESS`** |
| Runner | `ubuntu-latest` / `procps` |
| `SEC-enabled environment ([dev,sec]) — required` | **`SUCCESS`** |
| `Core environment (no [sec] extra)` | **`SUCCESS`** |
| Linux pytest | `4899` passed, `1` skipped, `0` failed |
| Trigger | push; **no manual workflow rerun was used** |

**The four previously failing nodes all passed**, every one of them in
`tests/unit/test_d131_signal_and_monitor.py`:

- `test_the_future_tmux_launch_shape_does_not_inherit_an_ignored_sigint`
- `test_the_watchdog_stop_actually_terminates_a_normal_target`
- `test_the_watchdog_reports_stop_failed_when_the_target_survives`
- `test_the_stop_cli_exits_four_on_stop_failed`

**The new unlimited-width regression test also passed on Linux.**

**Downstream steps that the earlier failures had prevented from running now executed and passed** —
`CLI smoke checks`, `Secret scan`, and `Repository hygiene`. A failing pytest step had been short-
circuiting them, so their green status is itself new information rather than a restatement.

**The trigger matters.** The proof is a fresh push-triggered run over the repaired tree, not a rerun
of an earlier run's jobs, so it observed the repaired bytes on a clean runner.

## 8. D131 operational acceptance restored — D133-R6

**D131's semantic acceptance was never invalidated.** Repairs A and B, the parser provenance moves,
the archive public API, and the recognized optional fields were never implicated: the Linux failures
were confined to the watchdog's command observation.

**D131's operational half was temporarily reopened**, and correctly so — Linux CI had shown that the
accepted exact-target authentication rule was not satisfied on that platform, and an accepted
operational contract that only holds on one of the governed platforms is not accepted.

**It is now closed again.** With the local validation of §6 and the green Ubuntu CI of §7:

- **D131-R6** — proven `SIGINT` delivery with exact PID and command authentication, verified
  termination, and no escalation — is **again accepted cross-platform**;
- **D131-R9** — the strict `pid > 0` domain refused before inspection, `lsof` construction, or
  signalling — is **again accepted cross-platform**.

**The watchdog now satisfies the accepted exact-target authentication rule on both macOS and Linux**,
for the currently governed environments and for no others: this record makes no claim about any
platform neither gate exercised.

## 9. D132 unaffected — D133-R7

**[Decision 132](decision_132_m3_3_bounded_real_semantic_proof.md)'s bounded real semantic proof
remains fully accepted and unchanged.** The D133 defect and its repair are operator-tooling only and
are **disjoint** from every surface D132 measured:

- shard dispatch;
- explicit parent binding;
- parser provenance;
- the restored historical accessions;
- archive-order semantic equivalence.

**No D132 claim is reopened**, no D132 figure is revised, and the `BOUNDED_REAL_SEMANTIC_FIXTURE_ONLY`
classification and the §14 (D132-R12) claim boundary stand exactly as written. The watchdog was not
an input to that proof.

## 10. Main safety and no revert — D133-R8

**No revert of D131 or D132 was warranted, and none was performed.**

**The failure mode was fail-safe.** A legitimate target was **refused**; an unintended target was
**not signalled**. The direction of the failure is the whole disposition: the watchdog withheld an
action it should have taken, rather than taking an action against the wrong process.

**Nothing was corrupted or changed.** No persisted project data was touched, no operational catalog
byte moved, and **no semantic result changed** — the defect could not, by its nature, alter what any
parser recorded.

**Reverting would have been the worse option.** It would have removed the accepted D131 repairs from
`main` in exchange for a defect that already fails closed, replacing a narrow, provable,
two-file correction with a wide one. **The minimal repair was therefore the correct disposition**,
and the D131 design — refuse rather than guess — is what made that judgement available.

## 11. Remaining blockers — D133-R9

**Carried forward exactly, unchanged by this record:**

**PRE-NETWORK BLOCKER.** `src/disclosure_drift/sec/census_orchestrator.py::_parse_bulk` still carries
historical-shard misdispatch. **No future network or live-retrieval authorization may reach it until
it is repaired** ([Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) §12,
D131-R4). That repair is **not** authorized now and **must not** be performed as a side effect of
unrelated work. It is safe today only because it sits behind `require_network()`, network is disabled
at both tracked switches at request ceiling `0`, and neither the corrected offline canary nor E0 uses
it — **unreachable is a property of the configuration, not of the code**.

**CAPACITY.** [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12)'s
corrected-run capacity reconciliation **remains unresolved**, and this record constructs no part of
it.

**D128.** [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §4 (D129-R2)'s rejection of
every D128 semantic count **remains controlling**, and §14 (D129-R8)'s four requirements for a
corrected proof are unchanged.

**None of these blocks the next bounded performance A/B experiment** — they bound what may follow it,
not whether it may be prepared.

## 12. Owner rulings D133-R1 – D133-R10

| Ruling | Content |
|---|---|
| **D133-R1** | **The root cause is `ps` output truncation on Linux.** `/bin/ps -o command= -p PID` truncates at `80` columns on Ubuntu/`procps` when stdout is a pipe, so the expected target substring could be removed from the observed command text. The watchdog then **correctly failed safe** with `STOP_REFUSED_TARGET_MISMATCH` but **could not stop legitimate long-command targets on Linux**. macOS BSD `ps` does not truncate in the same condition, so the defect **escaped the local macOS acceptance gate**. This is a `PRODUCT_DEFECT` in operator tooling, **not** a semantic-pipeline defect (§3). |
| **D133-R2** | **The accepted repair is `/bin/ps -ww -o command= -p PID`.** It restores unlimited-width command-line observation on **both** BSD `ps` and `procps`, with no platform branch. **Nothing else changes**: positive-PID domain, process-state probe, exact-target authentication semantics, `SIGINT`-only policy, `STOP_FAILED` behaviour, `ProcessLookupError` handling, `PermissionError` handling, the network probe, and `MEMBER_COUNT_INCONSISTENT` exit `5` are all unchanged. **No `/proc` fallback was needed** (§4). |
| **D133-R3** | **The regression guard authenticates the argv, not the behaviour.** `test_the_command_probe_asks_ps_for_unlimited_width` asserts the actual `ps` argument vector, and **removing `-ww` is killed by that exact test**. This matters because **the four originally Linux-failing tests still pass on macOS without `-ww`**; the argv-level guard is therefore the direct protection against recurrence on the developer platform (§5). |
| **D133-R4** | **Local validation passed.** `make check-fast` exit `0`, run **exactly once**: `4900` collected, `4899` passed, `1` skipped, `0` failed. The single skip is **pre-existing and unrelated** — `tests/unit/test_m23_pilot_manifest.py:429`. All local gates passed (§6). |
| **D133-R5** | **Linux CI proves the repair.** Workflow `CI`, run `32605572777`, SHA `977a811b…`, result **`SUCCESS`**; the SEC-enabled required job and the core-environment job both **`SUCCESS`**; Linux pytest `4899` passed, `1` skipped, `0` failed. The **four previously failing nodes all passed** under `ubuntu-latest`/`procps`, the new regression test passed, and the previously skipped downstream steps — CLI smoke, secret scan, repository hygiene — **executed and passed**. **No manual workflow rerun was used** (§7). |
| **D133-R6** | **D131's operational acceptance is restored cross-platform.** D131's **semantic** acceptance was never invalidated; its **operational/watchdog** half was temporarily reopened when Linux CI exposed the portability defect. With D133 local validation and green Ubuntu CI, **D131-R6 and D131-R9 are again accepted** for the currently governed environments, and the watchdog satisfies the accepted exact-target authentication rule on **both** macOS and Linux (§8). |
| **D133-R7** | **D132 is unaffected.** The bounded real semantic proof remains **fully accepted and unchanged**. The D133 defect and repair are operational-tooling only and are **disjoint** from shard dispatch, parent binding, parser provenance, the restored historical accessions, and archive-order semantic equivalence. **No D132 claim is reopened** (§9). |
| **D133-R8** | **No D131/D132 revert was warranted, and none was performed.** The Linux defect was **fail-safe** — legitimate target refused, unintended target not signalled. **No persisted project data was corrupted and no semantic result was changed.** The minimal repair was the correct disposition (§10). |
| **D133-R9** | **The blockers carry forward exactly.** `census_orchestrator.py::_parse_bulk` remains an open **PRE-NETWORK** blocker and no future network or live-retrieval authorization may reach it until repaired; **D129-R12**'s corrected-run capacity reconciliation **remains unresolved**; **D129-R2**'s rejection of every D128 semantic count **remains controlling**. **None of these blocks the next bounded performance A/B experiment** (§11). |
| **D133-R10** | **The next sequence is unchanged by this record.** (1) Bounded performance A/B; (2) corrected-run capacity reconciliation using the repaired parser and the adopted performance configuration; (3) **only then** an owner decision on another complete-source canary. **No complete-source canary is authorized by D133. E0 remains unauthorized. Network remains disabled** (§14). |

**The controlling earlier rulings are preserved, not replaced.** D129-R2, D129-R8, and D129-R12
stand as written; D131-R4's pre-network blocker stays open; D131-R6 and D131-R9 are restored rather
than amended — **their content is unchanged and only their platform coverage was ever in question**;
and every D132 ruling is untouched. **Every D124-R5 gate carries forward intact.**

## 13. What this record does not do

- **It does not change any semantic result.** No count, accession, record, reference, registrant
  binding, or provenance value moves.
- **It does not revisit D128.** D129-R2's rejection of every D128 semantic count stands entirely.
- **It does not reopen D132.** No claim, figure, or classification in that record changes.
- **It does not amend D131-R6 or D131-R9.** It restores their platform coverage; their content is
  unchanged.
- **It does not repair `CensusOrchestrator._parse_bulk`** (D131-R4), and repairing it remains out of
  scope and unauthorized.
- **It does not tune performance** and **does not construct a capacity model** (D129-R12 unresolved).
- **It does not change production package code, configuration, schema, or migrations.** The published
  change set is one operator script and one test file.
- **It does not authorize** a bounded performance A/B, a capacity reconciliation, another semantic
  execution, a corrected complete-source canary, any canary, any disposable world, E0, an E0
  namespace, migration `0016`, network, SEC or HTTP access, or any catalog write. **Request ceiling
  remains `0`.**
- **It does not alter any authority constant.** All three remain `None`.
- **It does not supersede any record.** Decisions 121 through 132 stand as written.
- **It does not claim any platform neither gate exercised.** The proof covers macOS and
  `ubuntu-latest`/`procps`, and says nothing about others.

## 14. The next sequence — D133-R10

1. **Bounded performance A/B.**
2. **Corrected-run capacity reconciliation** under
   [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §12 (D129-R12), using the repaired
   parser and the adopted performance configuration.
3. **Only then**, an owner decision on another complete-source canary — which
   [Decision 129](decision_129_m3_3_d128_semantic_adjudication.md) §14 (D129-R8) still requires to be
   a full rerun from scratch in a new world.

This is the same sequence [Decision 132](decision_132_m3_3_bounded_real_semantic_proof.md) §17
(D132-R13) fixed, and D133 neither advances nor reorders it. Each step requires its own owner
instrument. **No complete-source canary is authorized by D133**, **E0 remains unauthorized
throughout**, and **network remains disabled** at both tracked switches at request ceiling `0`.
Separately and independently of that sequence,
`census_orchestrator.py::_parse_bulk` must be repaired before any future network or live-retrieval
authorization may reach it; that repair is not part of this sequence and must not be performed as a
side effect of unrelated work.
