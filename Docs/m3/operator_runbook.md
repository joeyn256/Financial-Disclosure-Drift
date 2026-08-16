# Milestone 3 — Mac Operator Runbook

> **CURRENT OPERATOR STATE, 2026-08-16 — DO NOT RUN E0 OR THE CATALOG TRANSITION.** [Decision 096](../Decisions/decision_096_m3_3_final_pre_e0_rehearsal_correction_and_remediation.md) authorizes only one final bounded remediation of the Decision-094/095 implementation, including the relocated malformed-full-index proof and corrected R28 attribution. The future `prepare-e0-catalog` and `offline-parse` execute modes must land disabled (`None`); no private-root access or operator command in this runbook presently authorizes real migration, E0, linkage, later stages, or network, and no further autonomous remediation follows.


> **CURRENT STATE, 2026-08-14 — M3.3-I/R IS COMPLETE AND OWNER-ACCEPTED, AND THE NEXT ACT IS
> THE DECISION-078 PRE-E0 READ-ONLY REAL-FEASIBILITY SOURCE AUDIT. NO REAL EXECUTION IS
> AUTHORIZED AND E0 DOES NOT BEGIN.** Accepted
> [Decision 070](../Decisions/decision_070_m3_3_i_r_implementation_authorization.md) issued the bounded
> M3.3-I/R authority; accepted Decisions
> [071](../Decisions/decision_071_m3_3_i_r_methodology_gap_adjudication.md),
> [072](../Decisions/decision_072_m3_3_full_index_multi_registrant_source_correction.md),
> [073](../Decisions/decision_073_m3_3_rehearsal_snapshot_bifurcation_and_amendment_purpose_blocker.md),
> and [074](../Decisions/decision_074_m3_3_e5_reserve_rehearsal_and_real_linkage_gate.md) govern that same
> stage. **The M3.3A execution rehearsal E1–E8 has been run and passes**, the **R28** bridge is
> clean, and the mutation campaign M1–M38 is fully killed. The independent read-only ultrareview
> of the frozen executable target `6f87abc…` returned BLOCKER 0 / MAJOR 0 / MINOR 3; accepted
> [Decision 075](../Decisions/decision_075_m3_3_i_r_ultrareview_bounded_correction.md) authorized and
> applied that bounded correction; **the corrected-target rereview is COMPLETE and MIN-A is
> CLOSED.** Accepted
> [Decision 076](../Decisions/decision_076_m3_3_preacceptance_infrastructure_optimization.md) then completed
> the test, governance, and audit infrastructure and returned RET-1, **now CLOSED**. The **first**
> formal Fable 5 Maximum acceptance review returned **BLOCKER 0 / MAJOR 0 / MINOR 2**, which is
> **not an acceptance**; accepted
> [Decision 077](../Decisions/decision_077_m3_3_i_r_fable_acceptance_findings_correction.md) authorized and
> applied that bounded correction. **The fresh Fable 5 Maximum formal M3.3-I/R acceptance review
> then ran and PASSED at BLOCKER 0 / MAJOR 0 / MINOR 0 / OPTIMIZATION 0 / OBSERVATION 1** —
> immutable artifact
> [`m3_3_i_r_formal_independent_acceptance_feaeaa4.md`](reviews/m3_3_i_r_formal_independent_acceptance_feaeaa4.md),
> evidence commit `8c43edd…` — and **accepted
> [Decision 078](../Decisions/decision_078_m3_3_i_r_owner_acceptance_and_real_feasibility_audit.md) records
> Sol/GPT's formal owner acceptance: M3.3-I/R is COMPLETE and OWNER-ACCEPTED at accepted executable
> target `feaeaa4…` (tree `3d33454a…`).** **The next act is the Decision-078 pre-E0 read-only,
> zero-network real-feasibility source audit of the already-accepted M3.2 material — NOT E0**, and
> a further Opus ultrareview is neither authorized nor required. Every
> statement below that says M3.3 has not begun, that its implementation is unauthorized, that the
> next act is a separate M3.3-I/R packet or a fresh Fable acceptance review, that the E1–E8
> rehearsal has not been run, or that the corrected target is pending a fresh read-only rereview
> is **historical**. **Still true and
> unchanged:** M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 each remain a separate owner gate and **none is
> authorized**; the census parse layer is untouched; network, SEC, reacquisition, and
> private-evidence authority remain NONE; migration remains none; **two real-path feasibility gates
> are OPEN** — `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
> `M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` — which are never merged into one flag; and
> real acceptance-ordering adequacy remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION**.


**Status:** documentation only. **No step here is authorized to run against the SEC network.**
**Controlling records:** [Decision 027](../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§7, as narrowly corrected by accepted
[Decision 028](../Decisions/decision_028_m3_1_readiness_corrections.md).
**Plan:** [`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md).

This runbook is written for the project owner operating on macOS. It is sequential: work down it, and
stop at the first step that fails. It is **documentation, not authorization** — following it does not
authorize any phase.

---

## Current state — read this before running anything (Decision 064 §9; Decision 065)

> **Milestone 3.2 is COMPLETE and OWNER-ACCEPTED** (accepted
> [Decision 065](../Decisions/decision_065_m3_2_final_acceptance_and_closeout.md), 2026-08-13,
> `M3_2_FINAL_OWNER_ACCEPTANCE`), on the fresh independent final milestone acceptance review's
> `PASS` at **BLOCKER 0 / MAJOR 0 / MINOR 0**. **M3.2A SEC acquisition is COMPLETE. No further live
> SEC request is authorized.**
>
> | Fact | Value |
> |---|---|
> | Successor request identities satisfied | **75 / 75** |
> | Cumulative physical attempts | **77 / 801** |
> | Predecessor identities replayed | **0** |
> | Network window | **closed**; tracked switches `false` / `false` |
> | Audit projection | **77 / 77** — an exact deterministic reconstruction of the authoritative SQLite rows |
> | Source registry authority | **`m2.2-source-registry/1.1`** (Decision 062 §5) |
> | Execution receipt authority | writer **`m3-execution-receipt/3.0`** for every command except the two Decision 094 PRE-E0 surfaces, which emit **`4.0`**; readers accept `2.0`, `3.0`, and `4.0` (§12.2 of the receipt spec) |
> | Request plan | successor `f77e003c…`; predecessor `19be7bdc…` retired |
> | `sec_sic_code_list` exact path | the successor path SEC published; the retired `/corpfin/…` path is gone |
> | Gate H | **PASSED and owner-accepted** (Decision 065 §3), on the 30-of-30 applicable-item candidate `PASS` reproduced offline 2026-08-11 and the independent final audit |
> | Milestone 3.2 | **complete and owner-accepted**; annotated `m3.2-complete` tag created on the governance closeout commit |
> | M3.2B | **not executed / not required for accepted M3.2 completion — closed by Decision 065 §4**; not pending, no latent acquisition or network authority, never resurrectable from a historical M3.2 authorization |
> | M3.3 | **not begun; implementation not authorized** — its contract is **ACCEPTED** (accepted Decision 069, 2026-08-13, on frozen target `7bb36b8…` and the passing fresh rereview at B0/M0/MIN0) and is now the active stage contract, with **every executable-authority flag still closed**. History: Decisions 067 and 068 (both 2026-08-13) ruled OR-1/OR-2 and R13–R16, the fresh independent review of the 067-corrected text **FAILED** (B0/M1/MIN1), Decision 068 issued **R17** (fifteen-table E0 write footprint), **R18** (per-planned-source E0 dispositions), and **R16-C1**, and the rereview of the corrected text **PASSED**. **Acceptance is not implementation authorization**: the next act is a **separate owner M3.3-I/R implementation + rehearsal authorization packet** |
> | Census parse layer | **EMPTY**; `parser_state` `not_started` for all 76 plan sources. **M3.3 Owner Ruling R13** makes a bounded **offline** metadata parse the prerequisite for a real snapshot — **not** a reason to reacquire. Real execution is the separately owner-gated **M3.3-E0** (step 28a) |
> | Accepted catalog migration head | **`0013`**; current software requires `0015`. The only lawful transition is `0013 -> 0014 -> 0015` (accepted Decision 094 §5), it is **implemented and disabled**, and applying it needs a later exact owner instrument. Migration `0016` does not exist and is unauthorized |
> | PRE-E0 operator surfaces | `m3 prepare-e0-catalog` and `m3 offline-parse` **exist**; `preflight`/`verify` are read-only and usable, both `execute` modes return exit **`3`** while their source constants are `None` (step 28a) |
>
> **A separate owner gate sits on each side of M3.3-E0.** One authorization to run the real offline
> parse, an independent read-only verification of it, then a **separate** authorization to freeze a
> real candidate snapshot. **M3.3-E0 never authorizes M3.3-E1.**
>
> **Never**, on the strength of anything in this runbook: re-run the 74 already-satisfied
> retrievals; invoke another live acquisition; enable a network switch; resume from a `complete`
> receipt; use source registry `1.0`, receipt schema `2.0`, or the retired SIC URL; or run a
> reconciliation that is not transition-aware against the successor plan.
>
> **The M3.2 recovery lifecycle, as it actually is:**
>
> ```text
> acquisition → network closure → authoritative SQLite verification
>             → deterministic derived-projection synchronization if needed → Gate H
> ```
>
> `SAFE` from `m3 recovery-state` reports **evidence certainty**, never permission to acquire again.
> A completed window is `SAFE` with continuation refused, and `m3 acquire --resume-from` against a
> `complete` receipt refuses before a transport is constructed (Decision 064 §4).

---

## How to read the labels

Every command in this runbook carries exactly one label.

| Label | Meaning |
|---|---|
| **`AVAILABLE NOW`** | Implemented and accepted today. Safe to run as written. |
| **`IMPLEMENTED (M3.1)`** | Exists and runs. Implemented by the bounded Milestone 3.1 contract against the interface stated here. |
| **`PLANNED — NOT YET IMPLEMENTED (M3.1)`** | Does not exist. Its interface contract is stated so a bounded M3.1 contract implements this interface rather than inventing one. |
| **`IMPLEMENTED (M3.2)`** | Exists and runs. Implemented and accepted through the M3.2 stage contract. |
| **`PLANNED — NOT YET IMPLEMENTED (M3.3)`** | Does not exist. Belongs to a later milestone that has not begun. |
| **`MANUAL OWNER APPROVAL`** | Not a command. A decision the owner records in a template under [`templates/`](templates/request_budget.md). |
| **`VERIFICATION`** | A read-only check whose output is compared against an expectation. |
| **`RECOVERY`** | Run only after an interruption or a failure, never routinely. |

**A `PLANNED` command must never be typed.** It will not exist, and a shell will report it as
unknown. It is documented so the interface is agreed before it is built.

**An `IMPLEMENTED (M3.2)` command exists — which is not the same as being authorized to run.** The
M3.2A commands below are implemented and accepted, and the *live* ones are nevertheless exhausted:
acquisition is complete and no further SEC request is authorized (see the current-state banner
above). Read-only M3.2 commands are safe to run as written.

## What this runbook never prints

- the full `DISCLOSURE_DRIFT_SEC_USER_AGENT` value;
- any credential, token, cookie, or authorization header;
- any absolute personal path (`/Users/<name>/…`);
- any raw response body;
- any governed candidate, selected, or reserve row content;
- any unpublished root approval outside the approval packet itself.

Where a path is needed, use `"$(git rev-parse --show-toplevel)"` rather than typing one.

## Where evidence goes — the two layers

**The repository is public. Completed evidence is not committed to it.**

| Layer | What | Where |
|---|---|---|
| **Public** | Blank templates, planning records, the limitations register, and the **evidence index** | Tracked in the repository |
| **Private** | Every completed packet, checklist, receipt, request budget, raw object, catalog, and unpublished governed identity | An **owner-controlled private evidence root, outside the repository** |

After completing any evidence artifact, compute its digest and index it:

```bash
shasum -a 256 <private-evidence-file>
```

Record **only** that digest, the artifact type, the phase, the status, and a non-sensitive reference
identifier in [`templates/evidence_index.md`](templates/evidence_index.md). **Never record an
absolute private path publicly, and never paste an unpublished root anywhere.**

**The private evidence root needs a separate owner-controlled backup.** It holds the only record of
runs that cannot be re-run.

**`IMPLEMENTED (M3.1, Decision 028 §11)`**

Every M3 evidence-output command resolves its evidence root before writing and refuses a root equal
to, inside, or containing the checkout, so that symlinks cannot bypass the check. The
repository-root `.m3-private-evidence/` path is matched by a reserved `.gitignore` rule
`/.m3-private-evidence` and explicitly rejected by repository hygiene; it is never a lawful
operational evidence root.

**All three protections exist and are accepted**, and M3 evidence-output commands exist and run:
the `.gitignore` rule is in `.gitignore`, the repository-hygiene refusal is in
[`scripts/check_repo_hygiene.py`](../../scripts/check_repo_hygiene.py), and the resolved-path check
is in [`src/disclosure_drift/m3/evidence_paths.py`](../../src/disclosure_drift/m3/evidence_paths.py).
Limitations register entry **M3-L11** is `CLOSED` (2026-08-03). Corrected under accepted
[Decision 065](../Decisions/decision_065_m3_2_final_acceptance_and_closeout.md) §5 — documentary
only; no command, argument, exit code, or label changed.

---

## Routine development validation — which command to run

**`AVAILABLE NOW`** · **`VERIFICATION`** · Governed by accepted
[Decision 077](../Decisions/decision_077_m3_3_i_r_fable_acceptance_findings_correction.md) §4
(**R38**) over accepted
[Decision 076](../Decisions/decision_076_m3_3_preacceptance_infrastructure_optimization.md) §3
(**R35**) and §4.

**This section is workflow documentation.** It alters no real-operation command, grants no network
authority, and is **never** a precondition for, or a component of, an M3.3-E0, M3.3-E1, or M3.3-E2
authorization. Nothing below places a request or touches the operational evidence root.

### The recommended path

```bash
make check-fast
```

**`make check-fast` is the owner-recommended routine local full development validation** on the
project owner's current Mac. It runs the **same gate set as `make check`, in the same fixed order** —
lint, format check, full mypy, the full test suite, secret scan, hygiene check, Markdown link check,
decision section-reference check, config validation, cohort print, SEC help — differing in exactly
one respect: pytest runs across xdist workers instead of serially. **No gate is dropped, relaxed, or
reordered**, so a green `check-fast` covers what a green `check` covers.

Its pytest leg uses the Makefile defaults:

| Variable | Default | Meaning |
|---|---|---|
| `WORKERS` | `7` | xdist worker count |
| `DIST` | `worksteal` | xdist scheduling mode — seeds every worker up front, then re-balances when one runs dry |

**Both are overridable**, because both are plain `?=` defaults:

```bash
make check-fast WORKERS=4
make test-parallel WORKERS=4 DIST=load
```

**Seven workers with `worksteal` is a value measured on the project owner's machine, not a
universal constant.** A busier machine, or a runner with different core topology, should measure its
own. `loadfile` is deliberately not used here: grouping by file pins the two large test modules to
single workers and makes them the critical path.

### The conservative serial references

```bash
make check     # identical gate set, serial pytest
make test      # the suite alone, serial
```

**Neither is ever removed, and neither is weakened.** `make check` is the serial reference gate and
`make test` is the serial reference run; a bare `pytest` also stays serial, because no `-n` enters
`addopts`. **Reach for serial validation when a concrete reason requires it** — a parallel and a
serial run disagree, a test-isolation symptom appears, a debugger or `--pdb` is needed, or a reviewer
wants the unscheduled execution order. Routine correction and review packets that warrant a complete
test run should prefer `check-fast`.

### Pytest alone, either way

```bash
make test           # serial
make test-parallel  # WORKERS / DIST as above
```

### The governance reference gates

```bash
make links          # every relative Markdown link resolves to a tracked path
make decision-refs  # every "Decision NNN §N" citation names a section that exists
```

Both are already inside `make check` and `make check-fast`; run them directly when iterating on
documentation. Their acceptance invariants are `UNALLOWED_BROKEN_LINKS = 0` and
`INVALID_DECISION_SECTION_REFS = 0` — **stated as zero, never as a frozen link or citation total**
(Decision 076 §12, **P1**). Neither may be made green by editing accepted history, and every
exception is exact (Decision 076 §7).

**`make decision-refs` is an existence checker.** It proves a cited section *exists*; it cannot
prove the cited section is the *right* one. A pointer naming a real but semantically unrelated
section passes the gate and is still a defect — that remains a reviewer's job (Decision 077 §2,
**R36**).

### CI is separately governed

**CI was not switched to seven workers.** The measured optimum is machine-specific, so GitHub Actions
kept its serial run and was not altered by Decision 076 (§10). The Makefile accepts a worker override
so CI may later choose an appropriate value once measured **there** rather than assumed from here.

---

## 1. Open Terminal and enter the repository

**`AVAILABLE NOW`**

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
basename "$PWD"
```

Expect: `Financial Disclosure Drift`.

If `git rev-parse` fails you are not inside the repository. Open the project in Finder, right-click,
**Services → New Terminal at Folder**, and repeat.

## 2. Confirm branch and clean Git state

**`AVAILABLE NOW`** · **`VERIFICATION`**

```bash
make context
git status --short --untracked-files=all
```

Expect from `make context`: `Branch main`, `HEAD == origin/main  yes`, `State  clean`, the migration
chain ending at `0013_m23_manifest_lifecycle_guards.sql`, and the current stage and next authorized
action.

Expect from `git status`: **no output at all.**

**Stop if** the branch is not `main`, `HEAD != origin/main`, or anything is staged, modified, or
untracked. A dirty tree is never the starting point for a Milestone 3 phase.

## 3. Activate the virtual environment

**`AVAILABLE NOW`**

```bash
source .venv/bin/activate
command -v python
```

Expect the `python` path to end in `.venv/bin/python`.

If `.venv` does not exist:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 4. Confirm the Python version

**`AVAILABLE NOW`** · **`VERIFICATION`**

```bash
python --version
cat .python-version
```

Expect `Python 3.12.x`, matching `.python-version`.

**Stop if** they disagree. The accepted suite and the typed core assume 3.12.

## 5. Confirm the SQLite version

**`AVAILABLE NOW`** · **`VERIFICATION`**

```bash
make sqlite-check
```

Expect two values: the Python version and the SQLite version. **The SQLite version must be 3.37 or
newer** — `STRICT` tables require it, and migrations `0009` and `0012` use them.

**Stop if** SQLite is older than 3.37.

## 6. Verify the SEC extra is installed

**`AVAILABLE NOW`** · **`VERIFICATION`**

```bash
python -c "import httpx; print('httpx', httpx.__version__)"
```

Expect a version string. If it raises `ModuleNotFoundError`, the SEC extra is not installed:

```bash
python -m pip install -e ".[dev,sec]"
```

**The extra is required for M3.2 only.** M3.1 needs it installed so Gate F can assert it is present,
but M3.1 still sends nothing.

## 7. Verify ordinary and offline imports remain isolated

**`AVAILABLE NOW`** · **`VERIFICATION`**

```bash
python -m pytest -q tests/integration/test_no_network.py tests/unit/test_optional_dependencies.py
```

Expect all tests to pass. These are the assertions that ordinary package imports pull in no HTTP
client and that offline commands work without the extra.

**Stop if** either fails. Offline isolation is the property every zero-request step depends on.

## 8. Validate the SEC identity without printing it

**`AVAILABLE NOW`** · **`VERIFICATION`**

```bash
python -m disclosure_drift validate-sec-config
```

Expect a table ending with:

```
  SEC contact identity: valid; value not displayed
```

The identity comes from `DISCLOSURE_DRIFT_SEC_USER_AGENT`, resolved on demand and **never printed,
logged, or persisted**. Set it in `.env` (git-ignored) following the shape in `.env.example` —
a descriptive name and a contact address you control.

**Never `echo "$DISCLOSURE_DRIFT_SEC_USER_AGENT"`, never paste it into a chat, and never include it
in an evidence packet, a receipt, a log, or a commit.**

**Stop if** the command reports the identity invalid. Fix `.env` and re-run.

## 9. Confirm network is disabled by default

**`AVAILABLE NOW`** · **`VERIFICATION`**

The same command reports the effective network state:

```bash
python -m disclosure_drift validate-sec-config | grep -E '^  (network|companyfacts|aggregate rate|retry policy)'
```

Expect:

```
  network            : disabled (safe default)
  companyfacts       : disabled (reconciliation only)
  aggregate rate     : 4.0 requests/second, burst 1
  retry policy       : 5 transient retries, ceiling 60.0s, cooldown 600.0s
```

**Stop if** `network` reads `enabled` at any point before the single authorized M3.2 window.

## 10. Run the acquisition rehearsal (A1–A12)

**`IMPLEMENTED (M3.1)`**

```
python -m disclosure_drift m3 rehearse --scenarios all \
  --evidence-root <absolute-external-path> \
  --evidence-out <relative-path> --receipt-out <relative-path>
```

**Intended interface contract:**

| Aspect | Contract |
|---|---|
| Purpose | Run the **acquisition** scenarios A1–A12 in [`offline_rehearsal_spec.md`](offline_rehearsal_spec.md) §5 against scripted responses and synthetic fixtures. **Not** the snapshot, selection, reserve, sealing, manifest, or root scenarios — those are E1–E8 at M3.3A, where the production paths exist |
| Network | **None.** Opens no socket; asserts none was opened |
| Clock | Deterministic clock inputs supplied explicitly; nothing read from the system clock into any recorded identity |
| Arguments | `--scenarios {all,<id>[,<id>…]}`; required `--evidence-root <absolute-external-path>`; `--evidence-out <relative-path>` and `--receipt-out <relative-path>` below that root; `--config <path>` |
| Stdout | One line per scenario: the scenario id, `PASS` or `FAIL`, and the scenario title — **not** its outcome fields and **not** its reason codes, which are recorded in the stored evidence report's per-scenario `findings` list; a failing scenario adds one indented line carrying the failed assertions; then a `Rehearsal summary.` block of labelled lines (`scenarios run`, `all twelve run`, `every scenario passed`, `A_reachable agrees`, `routes measured`, `routes unmeasurable`, `simulated logical requests`, `simulated physical attempts`, `actual network requests`, `evidence reference`), one line per unmeasurable route, the evidence and receipt names, the `receipt_id`, and — only on a complete passing run — the M3.1A completion token |
| Side effects | Writes only under an isolated synthetic data root and the named evidence path |
| Exit codes | `0` all scenarios passed · `1` configuration error · `2` usage · `3` stage not enabled · `4` gate failure (any scenario failed) |
| Receipt | Emits one execution receipt per invocation, `invocation_mode = "rehearsal"`, with **actual network counts of `0`**; simulated totals go to the evidence report |

## 11. Review the acquisition-rehearsal evidence

**`IMPLEMENTED (M3.1)`** · **`VERIFICATION`**

```
python -m disclosure_drift m3 rehearse-report \
  --evidence-root <absolute-external-path> --evidence <relative-path>
```

**Interface contract:** read-only. What it prints, in this order:

1. **one line per scenario** — the scenario id, `PASS` or `FAIL`, and the scenario title. It is a
   pass/fail roster, not the ten-field matrix of
   [`offline_rehearsal_spec.md`](offline_rehearsal_spec.md) §5. The observed reason codes and the
   other observed facts are recorded in the stored evidence report's per-scenario `findings` list;
   read them there, or from the file, rather than expecting them on this screen;
2. **the route-bounds table** — one row per registered route, its derived `A_reachable`, its
   independently tested bound, and whether the two agree, followed by one line per route that could
   not be exercised and the reason it could not;
3. **four summary lines** — `all twelve recorded`, `every scenario passed`,
   `identity non-contamination`, and `A_reachable agrees`.

Exit `0` only when all twelve are recorded, all twelve passed, and the derived and tested bounds
agree. The verdict is recomputed from the stored scenario list and the stored bounds, so a report
whose own summary claims success while its scenario list disagrees still exits `4`.

**Check by hand, against [`offline_rehearsal_spec.md`](offline_rehearsal_spec.md) §5:**

- all twelve scenarios A1–A12 present, none skipped, none `xfail`ed;
- every observed reason code in the stored report's `findings` equals its expected registered code;
- **A6** proves every registered route reachable and every denied family refused;
- **A11** proves each injected abort point leaves a distinguishable state and that the resumed pass
  issues **zero** requests for an already-committed retrieval. **It does not exercise
  `m3 recovery-state` and it applies no repair**, so it demonstrates no `UNSAFE` → repair → `SAFE`
  cycle. Run `m3 recovery-state` yourself at step 27 when you actually need a determination;
- **A12** shows the receipt sample carries **none** of the prohibited fields, and the positive control
  proves the scan is not vacuous;
- **A12** shows every governed value identical with receipts disabled, enabled, and varied;
- **every rehearsal receipt reports actual network counts of `0`**;
- **`A_reachable` is derived per route and independently tested** against the worst reachable path,
  and any route the table shows as unmeasurable is a **gap in the Gate F evidence** for as long as
  that route can contribute to the ceiling — not an inert row;
- **no snapshot, selection, reserve, sealing, manifest, or root scenario appears here.**

**Stop if** any of those fails. A rehearsal finding is a design finding, and it is cheap here and
expensive later.

## 12. Perform Gate F's zero-request dry run

**`IMPLEMENTED (M3.1)`**

```
python -m disclosure_drift m3 plan-requests \
  --coverage-start 2009-01-01 --coverage-end 2026-06-30 --as-of 2026-06-30 \
  --calendar-year <YEAR> --calendar-evidence-manifest <relative-path> \
  --catalog <relative-path> --evidence-root <absolute-external-path> \
  --plan-out <relative-path> --receipt-out <relative-path>
```

**Intended interface contract:**

| Aspect | Contract |
|---|---|
| Purpose | Enumerate the **M3.2A bootstrap window's** logical requests and emit that window's request plan and hash. M3.2B derivation belongs only to the later `m3 derive-dependent-plan` command under an M3.2 contract |
| Network | **Zero requests.** Constructs no transport; resolves no host |
| Clock | Never reads today's date; all three coverage dates and the calendar year are explicit and required together |
| Arguments | `--coverage-start`, `--coverage-end`, `--as-of` (all three required together); `--calendar-year YEAR`; `--calendar-evidence-manifest <relative-path>`; `--catalog <relative-path>`; required `--evidence-root <absolute-external-path>`; `--plan-out <relative-path>` and `--receipt-out <relative-path>` below that root; `--config <path>`. **No `--reconciliation-set`, `--live`, or M3.2B mode** |
| Stdout | The per-route table — `source_id`, planned unique logical requests, maximum physical attempts, maximum new raw objects — then the totals and the **request-plan hash** |
| Side effects | Writes only the named plan file. Touches no catalog |
| Exit codes | `0` plan produced · `1` configuration error · `2` usage · `3` stage not enabled · `4` gate failure |
| Receipt | Emits one execution receipt — writer `m3-execution-receipt/3.0` since Decision 055 §7, readers accepting `2.0` and `3.0` — with `invocation_mode = "dry_run"`, zero actual request counts, the acquisition window and plan/version fields, and **no** approved ceiling or later gate outcome |

**`AVAILABLE NOW` today, and covering a strict subset:**

```bash
python -m disclosure_drift sec census --dry-run \
  --coverage-start 2009-01-01 --coverage-end 2026-06-30 --as-of 2026-06-30 \
  --calendar-year 2026
```

This makes **zero requests** and prints the quarterly index-instance plan and a `census plan hash`.
It is **not** the Gate F plan: it covers the quarterly index instances, not every route, and it emits
no execution receipt. Use it to sanity-check the coverage window; do not record it as Gate F
evidence.

## 13. Repeat the dry run and compare plan hashes

**`IMPLEMENTED (M3.1)`** · **`VERIFICATION`**

Run step 12 twice, into two different plan files, then compare:

```
shasum -a 256 <plan-file-1> <plan-file-2>
diff <plan-file-1> <plan-file-2>
```

Expect: identical SHA-256 values and **no** `diff` output.

**Stop if they differ.** Do not re-run until they agree — the disagreement is the finding, and it
means a plan input is being read from the environment or the clock rather than supplied explicitly.

## 14. Print and inspect the request budget

**`IMPLEMENTED (M3.1)`**

```
python -m disclosure_drift m3 show-budget \
  --evidence-root <absolute-external-path> --plan <relative-path>
```

**Intended interface contract:** read-only; renders the eight budget quantities per route and in
total — planned unique logical requests, maximum physical attempts, expected successful responses,
expected cache hits, expected not-modified responses, expected governed non-success responses,
maximum new raw objects, and the rate-limiter spacing floor — plus the computed hard ceiling. Exit `0`
on success.

**Transcribe the output into
[`templates/request_budget.md`](templates/request_budget.md).** Then check by hand:

- exactly one acquisition window is named;
- every route is listed; routes belonging to the other window read `n/a — other window`;
- no count is blank, and no count is a guess;
- **`A_reachable` is stated per route**, derived from the implemented state machine and
  independently tested — **never a single asserted multiplier**;
- the maximum physical attempts equals `Σ ( U(route) × A_reachable(route) )`;
- maximum new raw objects equals planned unique logical requests; cache hits were excluded before
  planning and are not subtracted again;
- the elapsed quantity is labelled a rate-limiter spacing floor, not a maximum or prediction;
- the hard ceiling equals that same sum — **no contingency, no padding**;
- for an **M3.2B** budget, the counts are **derived from the frozen M3.2A objects**, with the
  derivation provenance recorded.

## 15. Record owner approval of the exact budget and hard ceiling

**`MANUAL OWNER APPROVAL`**

Complete and sign [`templates/request_budget.md`](templates/request_budget.md) and the corresponding
rows of [`templates/gate_f_checklist.md`](templates/gate_f_checklist.md).

**The approval names two exact integers, for one window:** that window's total planned unique logical
requests, and its hard request ceiling. Both are recorded verbatim.

**Gate F approves the M3.2A window only.** The M3.2B budget does not exist yet and requires its own
owner approval, after M3.2A's objects are frozen (step 18a).

**Gate F cannot pass until Decision 028's planner-v2 correction is accepted, implemented, and
tested** — Decision 013 §1 requires coverage through the **closed 2026 Q2** quarter. The corrected
planner must classify it closed under `quarterly-index-instances/2.0`; Decision 013 is unchanged.

**No approval by implication.** Running the planner is not approving its output; a passing gate is
not an approval; and silence is not an approval.

## 16. Enable live access only for the authorized acquisition command

**`IMPLEMENTED (M3.2)`** · **owner-authorized window only** · **exhausted for M3.2A — historical reference**

Network is enabled by configuration, for one named command, for one window. The M3.2 contract names
the exact configuration path and the exact command; **this runbook does not authorize the change and
does not print the edit.**

Before enabling, confirm all of:

- Gate F checklist complete, every item `PASS`, owner-signed;
- request budget and hard ceiling approved as exact integers;
- `M3_1_GATE_F_READY_FOR_CONTROLLED_METADATA_ACQUISITION` recorded;
- independent M3.1 review passed and `m3.1-complete` created;
- an accepted M3.2 contract with an explicit network authorization;
- Gate H **pre-run** state established (step 18 below).

## 17. Confirm the command's exact network scope

**`IMPLEMENTED (M3.2)`** · **`VERIFICATION`**

```bash
python -m disclosure_drift m3 acquire --show-scope \
  --evidence-root "$EV_ROOT" \
  --plan runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/plan_first.json \
  --window M3.2A
```

`--evidence-root`, `--plan`, and `--window` are **mandatory**; omitting any of them is a usage
failure (exit `2`), not a default. `$EV_ROOT` is the governed external evidence root, supplied
locally and never written into this file (accepted Decision 061 §6.1). `--show-scope` is mutually
exclusive with `--live` and constructs no transport.

**Intended interface contract:** read-only; prints the allowed hosts, the allowed method, the exact
route allowlist, the denylist families, the approved plan hash, the approved ceiling, and the
consumed-count baseline — **and makes zero requests**. Exit `0`.

Compare its output against the Gate F evidence. **Stop on any difference**, including a difference in
the plan hash.

## 18. Start controlled acquisition

**`IMPLEMENTED (M3.2)`** · **exhausted for M3.2A — historical reference; no further live invocation
is authorized**

First, establish Gate H **pre-run** state (milestone plan §11, Gate H):

- an isolated M3.2 data root;
- a consistent SQLite backup of any accepted prior state;
- recorded available storage;
- confirmed quarantine and staging paths;
- the confirmed single-writer lock;
- **no** stale `.part` files and **no** unresolved recovery events;
- the approved plan hash saved.

Then:

```bash
python -m disclosure_drift m3 acquire \
  --config "$WINDOW_LOCAL_CONFIG" \
  --evidence-root "$EV_ROOT" \
  --plan <relative-path> --window M3.2A --live --ceiling <INT> \
  --data-root <relative-path-below-evidence-root> --catalog <relative-path-below-data-root> \
  --receipt-out <relative-path>
```

`--evidence-root`, `--plan`, `--window`, `--live`, `--ceiling`, `--data-root`, `--catalog`, and
`--receipt-out` are all **mandatory** for a live invocation; omitting any of them is a usage failure
(exit `2`). `$EV_ROOT` and `$WINDOW_LOCAL_CONFIG` are private, locally supplied values that are never
written into this file (accepted Decision 061 §6). **For the authorized M3.2A clean carry-in run, use
step 27a's exact frozen command instead of this general form** — it fixes every value.

**Intended interface contract:**

| Aspect | Contract |
|---|---|
| Purpose | Execute exactly the approved plan, metadata only |
| Network | **Live, and only here.** Requires `--live`, an enabled configuration, a valid identity, and a matching plan hash |
| Arguments | Required: `--evidence-root <absolute-external-path>`; `--plan <relative-path>`; `--window {M3.2A,M3.2B}`; `--live` (explicit, no default); `--ceiling <INT>` (must equal **that window's** approved ceiling); `--data-root <relative-path-below-evidence-root>`; `--catalog <relative-path-below-data-root>`; `--receipt-out <relative-path>`. Optional: `--config <path>` (the window-local configuration); `--resume-from <receipt>` (recovery only); `--carry-in-authority <path>` (clean-root consumed baseline only — **never a resume**, and mutually exclusive with `--resume-from`; see step 27a). There is **no `--run-id`**: a carry-in root takes its run id from the authority artifact |
| Stdout | Progress by route: planned, attempted, succeeded, classified, stored — then the totals |
| Stop behaviour | **Refuses the attempt that would exceed the ceiling**; halts aggregate traffic on `403` or unqualified `429`; fails closed on blocking schema drift |
| Side effects | Immutable raw objects; source observations; catalog rows inside their transaction; quarantine entries; one receipt |
| Exit codes | `0` complete · `1` configuration error · `2` usage · `3` stage not enabled · `4` gate failure (ceiling, drift, prohibited route, unclassified response) |
| Receipt | **Mandatory**, one per invocation, `invocation_mode = "live"` |

**Watch the running output for:** the request count against the budget, the route list staying inside
the allowlist, zero filing-body URLs, and the classification totals.

## 18a. Between the windows — freeze, derive, and obtain the second approval

**`IMPLEMENTED (M3.2)`** · then **`MANUAL OWNER APPROVAL`** · **M3.2B is not begun and is not authorized**

> **Disposition: NOT EXECUTED / NOT REQUIRED FOR ACCEPTED M3.2 COMPLETION — accepted
> [Decision 065](../Decisions/decision_065_m3_2_final_acceptance_and_closeout.md) §4.** This step is
> preserved as the planned between-windows procedure. **Do not run it as a pending action.** M3.2 is
> complete and owner-accepted, Gate H passed on the completed M3.2A evidence state, and M3.2B was
> not executed, is not pending, and carries no latent acquisition or network authority. Nothing
> here — including the `m3 derive-dependent-plan` command below — authorizes work; a new explicit
> owner authorization is required for any future acquisition resembling it.

**M3.2A acquires only the bootstrap sources. M3.2B acquires only the dependent requests derived from
what M3.2A actually retrieved.** Between them, in this exact order:

1. **Disable transport.** Verify with step 26 before doing anything else. The derivation is an
   offline act over frozen evidence.
2. **Freeze and identify the bootstrap raw objects** by their content-addressed identities.
3. **Derive** the historical-submission references **from the frozen bulk-submissions object**, and
   the entity reconciliation set from the frozen objects.
4. **Produce the second zero-request plan** — step 12's command, run again, over the frozen objects.
5. **Print and inspect the second budget** — step 14, for the M3.2B window.
6. **Obtain the owner's second exact approval** of that budget and its hard ceiling — step 15, again.

```
python -m disclosure_drift m3 derive-dependent-plan --from-window M3.2A \
  --reconciliation-set <path> --plan-out <path>
```

**Intended interface contract:** read-only over frozen objects; **zero requests**; enumerates the
historical-file references the frozen bulk-submissions object names and the supplied reconciliation
set; emits the M3.2B plan and its hash. Exit `0` on success, `4` if transport is enabled or a source
object is not frozen.

**Stop if** the derived set does not match what the frozen objects name, if transport was still
enabled, or if the owner declines the second budget. **M3.2B may not run under M3.2A's approval.**

## 19. Stop safely after any gate failure

**`IMPLEMENTED (M3.2)`** · **`RECOVERY`**

If the command exits `4`, or if you need to stop it, press `Ctrl-C` **once** and wait. The accepted
rollback order applies and must be allowed to complete:

1. new requests stop;
2. the job is marked failed with its reason code;
3. attempts and committed raw objects are preserved;
4. partial or unverifiable objects are quarantined;
5. uncommitted transactions roll back;
6. the JSONL projection is rebuilt from SQLite;
7. integrity and foreign-key checks rerun;
8. the terminating receipt is written.

**Do not press `Ctrl-C` twice**, do not `kill -9`, and **do not delete anything.** Rollback never
means deleting evidence.

## 20. Locate logs without exposing secrets or personal paths

**`AVAILABLE NOW`** · **`VERIFICATION`**

```bash
python -m disclosure_drift validate-sec-config | grep -E '^  (data root|catalog path|audit directory)'
```

The log directory is `DISCLOSURE_DRIFT_LOG_DIR` (default `./logs`, git-ignored). Read logs with a
pager rather than pasting them:

```bash
less "${DISCLOSURE_DRIFT_LOG_DIR:-./logs}"/*.log
```

**Logs never contain the SEC identity** — the client logs redacted headers only. If you ever see a
full identity in a log, **stop**: that is a leakage finding, not a formatting issue.

**When quoting a log into an evidence packet, quote the line, not the path.**

## 21. Locate raw-store provenance

**`AVAILABLE NOW`** · **`VERIFICATION`**

Raw objects live under the data root reported in step 20, content-addressed, each with a
`.lineage.json` sibling. Inspect one without opening its body:

```bash
find "$(python -c 'import os;print(os.environ.get("DISCLOSURE_DRIFT_DATA_ROOT","./data"))')" \
  -name '*.lineage.json' | head -3
```

**Read lineage files, not payloads.** A lineage file carries the identity, hashes, path, parser, and
supersession record; the payload is a raw response body and is never quoted into evidence.

## 22. Locate execution receipts

**`IMPLEMENTED (M3.1)`** · **`VERIFICATION`**

Receipts are written to the path given by `--receipt-out`, under the receipt storage policy in
[`execution_receipt_spec.md`](execution_receipt_spec.md) §7.

```
python -m disclosure_drift m3 show-receipt --receipt <relative-path>
```

**Intended interface contract:** read-only; renders the receipt's fields in a fixed order and
**fails closed** if any prohibited field is present. Exit `0` clean, `4` on a prohibited field.

## 23. Confirm actual request totals

**`IMPLEMENTED (M3.2)`** · **`VERIFICATION`**

```bash
python -m disclosure_drift m3 reconcile-requests \
  --evidence-root "$EV_ROOT" \
  --plan <relative-path> \
  --data-root <relative-path-below-evidence-root> \
  --catalog <relative-path-below-data-root> \
  --report-out <relative-path>
```

**Interface:** read-only apart from the deterministic report it writes; prints the per-state item
totals, the required absences, out-of-plan and superseded-out-of-plan observations, store findings,
drift, and blocked recovery states. Exit `0` only when every divergence is accounted for by the
plan's own rules.

**Reconciling a window whose plan lawfully moved.** Where an accepted owner decision substituted an
endpoint mid-window, the predecessor's retired identity is out of the *successor* plan and would
otherwise block reconciliation forever. Add **both** halves of the explicit binding — never one:

```bash
  --plan-transition-predecessor <relative-path-to-predecessor-plan> \
  --plan-transition-predecessor-receipt <relative-path-to-predecessor-receipt>
```

The pair goes through the same seventeen-condition verifier every other surface uses. With it, the
one superseded identity is reported under `superseded_out_of_plan` — still stored, still visible,
still failed historical evidence, satisfying nothing. Without it, that identity is an ordinary
blocking out-of-plan observation. Any *other* out-of-plan observation stays blocking either way, and
an unauthorized plan pair is refused. A transition is never inferred (Decision 064 §7).

Transcribe the result into [`templates/gate_h_checklist.md`](templates/gate_h_checklist.md), **per
window** — M3.2A and M3.2B are reconciled separately and integrated there.

**Stop if** actual exceeds planned anywhere the plan does not explain, if actual physical attempts
exceed a ceiling, if a run reaches equality with planned work unfinished, if a dependent request
appears in M3.2A, or if a bootstrap request appears in M3.2B. A complete run may lawfully finish
exactly at its ceiling.

## 24. Confirm no unresolved schema drift

**`IMPLEMENTED (M3.2)`** · **`VERIFICATION`**

```
python -m disclosure_drift m3 show-drift --run <run-id>
```

**Intended interface contract:** read-only; lists every drift event by kind, field path, affected
route, and affected raw-object identity, separating retained-unknown-field events from blocking ones.
Exit `0` only when there is **no** blocking event.

Any blocking event opens
[`templates/schema_drift_incident.md`](templates/schema_drift_incident.md) and **stops the phase**
until the owner rules. **Never resolve drift by supplying a default, coercing a type, or dropping a
row.**

## 25. Confirm the repository remains clean

**`AVAILABLE NOW`** · **`VERIFICATION`**

```bash
git status --short --untracked-files=all
make hygiene
make secrets
```

Expect: no `git status` output; both scripts reporting clean.

**Stop if** any data file, database, `.part` file, lock file, or secret is tracked or untracked-but-not-ignored.
Nothing under `data/` is ever committed except `data/README.md`.

## 26. Disable the network again after acquisition

**`IMPLEMENTED (M3.2)`** then **`AVAILABLE NOW`** to verify

Revert the configuration change from step 16, then verify. **Do this at the end of *each* window** —
after M3.2A before the derivation step 18a, and again after M3.2B before Gate H:

```bash
python -m disclosure_drift validate-sec-config | grep -E '^  network'
```

Expect `network            : disabled (safe default)`.

**Gate H does not pass while the network is still enabled**, and **the derivation in step 18a may not
begin while it is.** Record both verifications in the Gate H checklist.

## 27. Resume after an interrupted acquisition

**`IMPLEMENTED (M3.1 read-only inspector)`** · **`IMPLEMENTED (M3.2 repair)`** · **`RECOVERY`**

Work through [`templates/interrupted_run_recovery.md`](templates/interrupted_run_recovery.md) **before**
resuming anything:

```
python -m disclosure_drift m3 recovery-state \
  --evidence-root <absolute-external-path> \
  --plan <relative-path> --receipt-chain-head <relative-path> \
  --catalog <relative-path> --data-root <relative-path-below-evidence-root>
```

**Intended interface contract:** read-only over the explicit plan, receipt-chain head, catalog, and
data-root inputs; reports the last successful receipt, the interruption point, database state,
raw-store state, partial-file state, the consumed request count, and a
**safe-resume determination** of `SAFE`, `UNSAFE`, or `UNDETERMINED`. It never adopts, quarantines,
rebuilds, reconciles, resumes, or calls `observation_catalog.reconcile()`. Exit `0` only for `SAFE`.
There is no `--run` shortcut and no repair flag.

It also reports, beside the determination and separately from it: the head receipt's own completion
status, whether continuation is **permitted**, the identity-level logical remainder, and the
worst-case attempt remainder. Those last three come from the same reconciliation continuation
enforcement uses, so the screen and the enforcement cannot disagree (Decision 064 §6).

**`SAFE` is evidence certainty, not permission (Decision 064 §4).** A window that finished
successfully is `SAFE` — its state is fully established — with `continuation permitted: no` and
`continuation remaining: 0`. Resuming from it is refused before a transport is constructed. Read the
two lines together, never the determination alone.

On `UNSAFE`, stop. A separately authorized M3.2 repair command may apply the deterministic action;
then run `recovery-state` again and require `SAFE`. Inspection itself never repairs.

**Before spending a one-use repair authority, prove the action is eligible.** `m3 recover
--check-only` runs the same evaluation the applier runs, mutates nothing, opens no writer, and exits
`4` when the action would be refused:

```bash
python -m disclosure_drift m3 recover --check-only \
  --config "$OFFLINE_CONFIG" --evidence-root "$EV_ROOT" \
  --plan <relative-path> --receipt-chain-head <relative-path> \
  --catalog <relative-path-below-data-root> \
  --data-root <relative-path-below-evidence-root> \
  --run <census-run-id> --action rebuild-projection --event census_source_observations.jsonl
```

**`rebuild-projection` runs offline, over an adjudicated store.** Its eleven-condition eligibility
requires a resolved chain, an established terminal state, passing integrity, an unambiguous
observation set, no orphan or partial uncertainty, no blocked recovery state, resolved carry-in
accounting, a **disabled** network, and a projection that *lags* authoritative SQLite rather than
*diverging* from it. Adjudicate store uncertainty first, then reconstruct the projection; a
divergent projection is referred for an owner ruling and is never overwritten (Decision 064 §5).

Resume only on `SAFE`, and only where continuation is permitted:

```bash
python -m disclosure_drift m3 acquire \
  --config "$WINDOW_LOCAL_CONFIG" \
  --evidence-root "$EV_ROOT" \
  --plan <relative-path> --window <M3.2A|M3.2B> --live --ceiling <INT> \
  --data-root <relative-path-below-evidence-root> --catalog <relative-path-below-data-root> \
  --resume-from <predecessor-receipt> --receipt-out <relative-path>
```

`--window`, `--evidence-root`, `--data-root`, and `--catalog` are **mandatory** here too; a resume
that omits them is a usage failure (exit `2`).

The resumed run carries the consumed count forward against the **same** approved ceiling and names its
predecessor receipt.

**On `UNDETERMINED`, stop.** Recovery uncertainty is a stop condition, not a judgement call.

### 27a. Carrying an approved consumed baseline into a clean new run

**`T5-AUTHORIZED — DECISION 061`** · **`MANUAL OWNER APPROVAL`** · **`RECOVERY`**

**This is not a resume.** A resume continues an exact predecessor receipt; a **carry-in root** starts
a *clean* run that nonetheless begins from an owner-approved non-zero consumed baseline. The two may
never be combined, and `--carry-in-authority` together with `--resume-from` is refused as a usage
error before anything is read or created.

**T5 authorization is not T6 execution.** Accepted
[Decision 061](../Decisions/decision_061_m3_2a_clean_carry_in_live_invocation_authorization.md)
(2026-08-10) authorizes **exactly one** future invocation and freezes the command below, but it is
**non-self-executing**: the invocation is performed only under the **separate later owner execution
packet** `OWNER_M3_2_T6_CLEAN_CARRY_IN_CONTROLLED_ACQUISITION_EXECUTION_PACKET`. **Do not run this
command until that packet is issued.**

The exact frozen invocation (Decision 061 §5) — type it verbatim, adding and removing nothing:

```bash
python -m disclosure_drift m3 acquire \
  --config "$WINDOW_LOCAL_CONFIG" \
  --evidence-root "$EV_ROOT" \
  --plan runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/plan_first.json \
  --window M3.2A \
  --live \
  --ceiling 801 \
  --data-root . \
  --catalog catalogs/m3_2a_operational.sqlite3 \
  --receipt-out runs/m3_2a_clean_carry_in/execution_receipt.json \
  --carry-in-authority runs/m3_2a_clean_carry_in/carry_in_authority.json
```

`$EV_ROOT` and `$WINDOW_LOCAL_CONFIG` are the **only** non-literal tokens. They are private,
locally supplied values with fixed meanings and mandatory validation (Decision 061 §6), never
literal paths written into this file: `$EV_ROOT` is the already accepted governed external evidence
root, and `$WINDOW_LOCAL_CONFIG` is the one-operation temporary configuration of step 16, mode
`0600`, outside Git and outside the evidence root, carrying no SEC identity, setting only
`network.enabled: true` and `network.m3_acquire_enabled: true` while leaving CompanyFacts `false`,
and withdrawn on **every** termination path. There is **no `--run-id`** and **no `--resume-from`**.

The authority is a canonical-JSON artifact under schema `m3-carry-in-authority/1.0`, supplied by a
**relative path beneath the evidence root** — an absolute or escaping path is refused. It binds, all
mandatory: window `M3.2A`, the frozen request-plan SHA-256, the cumulative ceiling `801`, the
historical seed `1`, that attempt's allocation to `sec_bulk_submissions`, `Decision 055` as the
authorizing record, the authorized new run id, and the later accepted orphan-adoption decision and
evidence identities. Its identity is the SHA-256 of its own canonical bytes; it contains no
self-hash field, no secret, no identity value, no response body, and no private absolute path.

**Those bindings are compared against the accepted values, not merely for internal consistency.**
An artifact seeded at `0`, allocating the attempt to a different registered route, naming another
plan or ceiling, or citing a decision that authorized nothing is **refused** even when it agrees
with itself and with the command line — its author chose both. The orphan-adoption reference must
be a canonical `Decision NNN` that is **not** Decision 055 (which expressly neither designs nor
performs that adoption), and its evidence identity must be a lowercase 64-hex SHA-256.

**What the operator must understand before ever using it:**

1. **It is consumed exactly once.** Consumption is a deterministic `ops_checkpoints` row committed in
   the *same* transaction as the new run's registration. Both commit, or neither exists.
2. **A burned authority stays burned.** If the invocation fails *after* that commit but *before* any
   request reaches the wire, the authority is spent with zero attempts placed. **Nothing reissues it
   automatically** — no retry, no replacement, no second use. A replacement is a new owner act.
3. **Re-running the same artifact is refused**, before any transport is constructed.
4. **The run id comes from the artifact**, not from the command line and not from random generation.
5. **The ceiling is not raised.** The gate is built with ceiling `801` and consumed `1`; cumulative
   consumption is `1 + N`. There is no `802`, no additive or shadow ceiling, and no reset.
6. **The receipt records `N`, not `1 + N`.** A carry-in root's `actual_physical_attempt_count` is this
   invocation's wire attempts only; its baseline is in
   `consumed_request_count_carried_forward`, and it names the authority in
   `carry_in_authority_sha256`.

Every one of the following **refuses before a transport is constructed**: a replayed authority; a
run-id mismatch; a plan, window, ceiling, seed, or route mismatch; malformed or noncanonical bytes; a
missing binding; an unsafe or escaping artifact path; and coexistence with `--resume-from`.

**An M3.2A run with no baseline source at all is refused too.** Omitting both
`--carry-in-authority` and `--resume-from` does not fall back to a zero baseline — the command
exits `4` before it creates the operational catalog, prepares storage, or constructs anything. A
run that silently restarted the consumed count at zero is a recorded stop condition
(**M3-L16**), and the count already stands at `1` of `801`.

**Preconditions — the historical blockers are discharged; the execution gate is not.** The paragraph
this replaces recorded that no clean carry-in run could be authorized until the separately
authorized, offline, one-time, **verified orphan adoption** had executed and been accepted with zero
unresolved historical orphan mismatch (**M3-L16**), and that no carry-in artifact should be minted
until then. **That condition is satisfied and is now historical:** the adoption executed exactly once
on 2026-08-10, was independently verified, and was finally owner-accepted; **M3-L16 is `CLOSED` —
accepted [Decision 059](../Decisions/decision_059_m3_2_orphan_adoption_final_acceptance_m3_l16_closure_and_governance_synchronization.md)**;
and accepted [Decision 060](../Decisions/decision_060_m3_2_carry_in_authority_mint.md) has **already
minted** the one-use authority (schema `m3-carry-in-authority/1.0`, 571 canonical bytes, SHA-256
`d7aa206b…`), which remains **UNCONSUMED** — 1 use total, 0 consumed, 1 remaining.

**What still gates the command:** `m3 acquire --live` remains gated by the accepted ladder — both
network switches true in the window-local configuration only, a valid SEC identity, and a per-window
owner authorization. T5 is now granted by Decision 061; **the remaining gate is the separate T6
execution packet.** Before it runs, the operator must additionally, under that packet's authority:

1. **materialize the minted authority** at `runs/m3_2a_clean_carry_in/carry_in_authority.json`
   beneath `$EV_ROOT` — **create-once** (fail if it already exists), mode `0600`, a regular file and
   not a symlink, the exact canonical bytes of Decision 060 §5.1, then **recompute SHA-256 and
   require `d7aa206b…`**, then require accepted loader admission and exact binding verification
   (Decision 061 §8). Any mismatch is a **stop before consumption**;
2. complete the full frozen preflight of Decision 061 §11, **waiving nothing**.

**Neither the authority nor a replacement is ever regenerated automatically.** A replacement is a new
owner act.

## 28. Escalate an unrecognized failure

**`MANUAL OWNER APPROVAL`**

If a failure does not match any documented stop condition:

1. **stop** — issue no further command;
2. leave the data root, the catalog, and every artifact exactly as they are;
3. capture the failing command's exit code, its stdout, and the reason code — **not** the raw
   response body and **not** the identity;
4. capture `make context` output;
5. open the closest template — schema drift, interrupted-run recovery, or the phase's own checklist —
   and record the state;
6. refer it for an owner ruling.

**Never work around a failing invariant, relax a threshold, or drop failing rows** (CLAUDE.md
rule 12).

## 28a. The real offline metadata parse — M3.3-E0

**`IMPLEMENTED AND DISABLED (Decision 094)`** · **`SEPARATE OWNER GATE`**

> **Current state, accepted Decision 094 §7 as corrected by Decisions 095–096 and 099.** The two
> operator surfaces below **exist and are wired**. `preflight` and `verify` are strictly read-only
> and do real work. **`execute` returns exit `3`** on both, because each is gated by its own source
> constant and both ship as `None`:
>
> ```python
> PRE_E0_CATALOG_TRANSITION_AUTHORITY: Final[str | None] = None
> M3_3_E0_EXECUTION_AUTHORITY: Final[str | None] = None
> ```
>
> ```bash
> ./.venv/bin/disclosure-drift m3 prepare-e0-catalog --config configs/project.yaml \
>     --mode {preflight,execute,verify}
>
> ./.venv/bin/disclosure-drift m3 offline-parse --config configs/project.yaml \
>     --mode {preflight,execute,verify}
> ```
>
> **Neither command takes a path option of any kind.** The accepted private root is read from the
> fixed, unlogged environment variable `DISCLOSURE_DRIFT_EVIDENCE_ROOT`; the catalog is always
> `catalogs/m3_2a_operational.sqlite3` beneath it; and both run namespaces are internal constants.
> There is no `--evidence-root`, `--catalog`, `--data-root`, `--run-namespace`, migration list,
> force, resume, overwrite, repair, network, or output option, and the variable's **value** never
> appears in output, a log, a receipt, a ledger event, or a terminal record.
>
> **The accepted catalog is at migration head `0013` and current software requires `0015`.** The only
> lawful transition is `0013 -> 0014 -> 0015`, and it needs a **later exact owner instrument** before
> `prepare-e0-catalog execute` becomes reachable. E0 additionally requires an owner-accepted COMPLETE
> transition terminal and its own separate one-invocation release.
>
> **Reading order for these two commands:**
> [`e0_execution_record_spec.md`](e0_execution_record_spec.md) for the durable records, exit codes,
> write sets, identities, and recovery law; [`execution_receipt_spec.md`](execution_receipt_spec.md)
> §12.2 for the `m3-execution-receipt/4.0` schema they emit.
>
> **What a passing preflight means:** the predicates it measured were true when it measured them. It
> creates nothing, it authorizes nothing, and it must be repeated under the writer lease by any later
> authorized `execute`.
>
> **What `prepare-e0-catalog --mode preflight` refuses on, that an operator may not expect**
> (accepted Decision 099 **R97–R98**):
>
> - **The accepted M3.2 completion binding (§5.2 predicate 3).** The two accepted M3.2 receipts —
>   `runs/m3_2_decision_062_sic_continuation/execution_receipt.json` and
>   `runs/m3_2a_clean_carry_in/execution_receipt.json` — must be present, unaltered, and bound to the
>   fixed catalog's own run rows, attempt ledger, and accepted head observation, with cumulative
>   accounting of exactly **77** physical attempts. A moved, edited, copied, or re-hashed receipt
>   refuses; so does a catalog whose run rows disagree with them. Nothing is repaired, and no receipt
>   is copied, renamed, or synthesized to make the chain resolve. The refusal names only fixed public
>   relative names, counts, and digest prefixes.
> - **The `runs/` parent (§5.2 predicate 10).** It must **already** exist, be a real non-symlink
>   directory, and be owned by the operator running the command. Preflight will not create it.
>
> **What `--mode verify` now also reads.** Both `verify` modes open the fixed catalog read-only and
> compare its current chain, integrity, and — for E0 — its §9.4 governed-state identities against
> what the terminal record froze, and re-hash the run's verified backup. A catalog that has drifted
> since the freeze makes `verify` REFUSE. It still repairs, restores, and resumes nothing.

**The census parse layer is empty.** M3.2 acquired and stored the objects; it parsed none of them,
and `parser_state` is `not_started` for all 76 plan sources. **M3.3 Owner Ruling R13** (accepted
[Decision 067](../Decisions/decision_067_m3_3_snapshot_authority_and_offline_parse.md) §4) makes a
**bounded offline metadata parse** the prerequisite for any real candidate snapshot, and **M3.3-E0**
is the gate at which that parse runs against the accepted real private catalog.

**This is not an acquisition step.** The parse reads only already-accepted stored objects. It
constructs **no HTTP client and no transport**, makes **no request**, performs **no reacquisition or
re-retrieval**, touches **no filing body, no CompanyFacts, and no Frames**, **adds no new source
evidence**, and **never fabricates** a missing object or observation. A source accepted as failed or
unavailable **stays** failed or unavailable.

**Its durable write set is fixed by Owner Ruling R17** (accepted
[Decision 068](../Decisions/decision_068_m3_3_e0_contract_correction.md) §3; contract §10.2
item 2), **as narrowly amended by accepted
[Decision 094](../Decisions/decision_094_m3_3_pre_e0_executability_redesign.md) §6.1**: **exactly
sixteen tables** — the former fifteen plus only `census_accession_registrants`, the Decision 083
**R58** canonical relation whose writer migration `0014` assigns to E0 — plus the
`census_plan_sources.parser_state` transition for category-A sources. `census_qa_metrics` and every
index-side table stay unwritten, and the addition is one table forced by a later accepted decision,
never a general permission to widen E0. **Every planned source receives exactly one report-level R18
disposition** (Decision 068 §4): `E0_REQUIRED_PARSE`, `E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE`, or
`E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY` — with no fabricated parser run and no
`parser_state` mutation merely to complete a ledger. *(The 70 quarterly full-index sources were
category C under Decision 068; accepted
[Decision 072](../Decisions/decision_072_m3_3_full_index_multi_registrant_source_correction.md) §2
superseded that one classification — `sec_full_index_company` is candidate-substantive, category A
when usable and category B when accepted unavailable, and never category C.)*

**Do not run E0 until all of:**

- an **accepted** M3.3 contract;
- the offline parse driver implemented and rehearsed **on fixtures or disposable isolated copies
  only**, with the accepted real private catalog untouched;
- the M3.3A independent review passed;
- the accepted catalog carried to head `0015` by the `prepare-e0-catalog` transition, under **its
  own** later exact owner instrument, with a COMPLETE and owner-accepted transition terminal;
- `M3_3_E0_EXECUTION_AUTHORITY` replaced by a governed token in a **separate, reviewed,
  constant-only** source change — no flag, environment value, catalog state, receipt, or namespace
  substitutes for it;
- **separate, explicit Sol/GPT authorization naming E0** — contract acceptance is not it, a passing
  rehearsal is not it, a passing preflight is not it, and a green suite is not it.

**After E0, before anything else:** an **independent read-only verification** to the **R3** standard.
**There is no automatic progression from M3.3-E0 to M3.3-E1.** A partial or interrupted E0 is
**nonauthoritative**, **blocks**, and returns to the owner — it is never automatically resumed,
completed, repaired, or promoted, and it **never silently authorizes M3.3-E1**.

## 29. Freeze the real snapshot only after Gate H and E0

**`PLANNED — NOT YET IMPLEMENTED (M3.3)`**

The snapshot-freeze command belongs to M3.3 and is documented in the M3.3 contract when it is
written. **Do not freeze a snapshot until all of:**

- [`templates/gate_h_checklist.md`](templates/gate_h_checklist.md) complete, every item `PASS`,
  owner-signed;
- **Milestone 3.2 complete and owner-accepted, with Gate H passed and owner-accepted** — proven by
  [Decision 065](../Decisions/decision_065_m3_2_final_acceptance_and_closeout.md) §3 together with
  the current `Milestones/STATUS.md` `M3_2_GATE_H_STATUS` record. **M3.3 Owner Ruling R4**
  (2026-08-13) fixes that durable proof as the operative precondition, in place of the phase token
  `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED` this list previously named. That token was
  **never emitted**, no code path emits one, and it **is not retroactively emitted, fabricated, or
  backfilled**;
- independent M3.2 review passed and `m3.2-complete` created;
- **the real offline metadata parse completed at the M3.3-E0 gate and independently, read-only
  verified** (step 28a; **R13**, **R14**). A structurally valid but substantively empty snapshot is
  **never** an acceptable substitute for parsing;
- **network verified disabled again**;
- owner authorization to freeze a real candidate snapshot — **separate from the E0 authorization**;
- an accepted M3.3 contract.

A snapshot frozen early is not a shortcut — it is an unfrozen snapshot with a hash on it.

## 30. Never approve a root implicitly

**`MANUAL OWNER APPROVAL`**

Approval happens in exactly one place:
[`templates/root_hash_approval_packet.md`](templates/root_hash_approval_packet.md), naming the exact
`root_manifest_sha256`, signed by the owner.

**None of these is an approval:** a manifest existing; verification passing; replay succeeding; a
green suite; a created tag; an execution receipt; a passing gate; silence; or "the code ran."

**Approval attaches to one exact hash.** An identical root **re-derived** from unchanged governed
state is the **same** approved value — determinism is the point, and re-deriving invalidates nothing.
A **different** root — corrected, superseded, or produced from changed governed state — requires a
new packet and a new explicit decision, and a prior approval never carries over to it.

**The write happens through the accepted entry point, once.** That entry point is built and
independently validated against synthetic catalogs at M3.4A before it ever touches the real root.
**Manual SQL against the real catalog is prohibited**, and M3.4 is never purely documentary.

## 31. Final clean-state verification

**`AVAILABLE NOW`** · **`VERIFICATION`**

```bash
make context
git status --short --untracked-files=all
git tag -l | sort
ruff check . && ruff format --check . && mypy src && pytest -q
make sqlite-check && make secrets && make hygiene
```

Expect: `HEAD == origin/main  yes`; clean tree; the expected tag set with **no** tag moved or
deleted; every gate green.

**Stop and report** on any failure. This is the state every phase both starts and ends in.

---

## Appendix A — commands available now, in one place

| Command | Purpose |
|---|---|
| `make context` | Read-only live state: branch, HEAD, tree, tags, migrations, stage, blocker, next action |
| `make check-fast` | **The recommended routine full validation** — the `make check` gate set with parallel pytest (`WORKERS=7`, `DIST=worksteal`, both overridable) |
| `make check` | The same full acceptance gate, serial pytest — the conservative reference |
| `make test` | The suite alone, serial |
| `make test-parallel` | The suite alone, across `WORKERS` xdist workers |
| `make links` | Every relative Markdown link resolves to a tracked path (`UNALLOWED_BROKEN_LINKS = 0`) |
| `make decision-refs` | Every decision section citation names a section that **exists** (`INVALID_DECISION_SECTION_REFS = 0`) |
| `make fast` | Changed-file Ruff plus the mypy daemon; not a gate |
| `make sqlite-check` | Python and SQLite versions (floor 3.37) |
| `make secrets` | Secret scan over tracked and untracked-not-ignored text |
| `make hygiene` | No raw data, database, release artifact, or personal path tracked |
| `python -m disclosure_drift validate-config` | Configuration against the frozen definitions |
| `python -m disclosure_drift show-cohorts` | The frozen cohorts, maturity gates, and seed |
| `python -m disclosure_drift validate-sec-config` | SEC policy and identity — **identity validated, never displayed** |
| `python -m disclosure_drift sec --help` | The Milestone 2 SEC command group |
| `python -m disclosure_drift sec census --dry-run …` | The M2.2 census plan; **zero requests**; prints a census plan hash |

## Appendix B — the Milestone 3 command surface

**Every command below exists and runs.** What varies is *authority*, not existence: the M3.2A live
paths are implemented and their grants are **exhausted**, so no further SEC request may be placed on
the strength of any published record (Decision 064 §9).

| Command | Phase | Status | Purpose |
|---|---|---|---|
| `m3 rehearse` | M3.1 | **implemented** | Run the **acquisition** rehearsal A1–A12, no socket |
| `m3 rehearse-report` | M3.1 | **implemented** | Render the acquisition-rehearsal evidence matrix |
| `m3 plan-requests` | M3.1 | **implemented** | The zero-request plan for one window, and its hash |
| `m3 derive-dependent-plan` | M3.2 | **implemented** — M3.2B unauthorized | Derive the M3.2B plan from the frozen M3.2A objects; zero requests |
| `m3 show-budget` | M3.1 | **implemented** | Render the derived budget quantities and the ceiling |
| `m3 show-receipt` | M3.1 | **implemented** | Render a receipt, failing closed on a prohibited field |
| `m3 acquire --show-scope` | M3.2 | **implemented** | Print the exact network scope; zero requests |
| `m3 acquire --live` | M3.2 | **implemented — live grant exhausted; no further SEC request is authorized** | Execute the approved plan, metadata only |
| `m3 acquire --carry-in-authority` | M3.2 | **implemented — the one carry-in authority is permanently consumed** | Begin a clean run from an owner-approved consumed baseline; consumed exactly once; never a resume (step 27a) |
| `m3 acquire --resume-from` | M3.2 | **implemented — refuses a `complete` predecessor before any transport** | Continue an unfinished window from its exact predecessor receipt |
| `m3 reconcile-requests` | M3.2 | **implemented**, transition-aware | Planned versus actual, per route and total; `--plan-transition-predecessor` with `--plan-transition-predecessor-receipt` reports the owner-superseded identity separately from blocking out-of-plan observations |
| `m3 show-drift` | M3.2 | **implemented** | Every drift event, blocking ones separated |
| `m3 recovery-state` | M3.1 (used by M3.2) | **implemented** | Read-only recovery determination, continuation permission, and the identity-level remainder; never repairs |
| `m3 recover` | M3.2 | **implemented** | Apply one separately authorized deterministic repair before a fresh read-only inspection; `--check-only` reports eligibility and mutates nothing |

**Exit codes for every command above follow the accepted convention:** `0` success, `1`
configuration error, `2` usage, `3` stage not enabled, `4` gate failure.

**Implemented and disabled.** The two Decision 094 §7 PRE-E0 surfaces — `m3 prepare-e0-catalog` and
`m3 offline-parse`, each `--config … --mode {preflight,execute,verify}` — **exist**. Their
`preflight` and `verify` modes are strictly read-only and may be typed; both `execute` modes return
exit `3` while their source constants are `None` (step 28a). Neither constructs a transport on any
code path, and neither is admitted to the network-gated command set.

**Planned and not yet existing.** The rest of the M3.3 command surface — the snapshot builder/freeze
command, the execution command, and the manifest output command Decision 021 §16 deferred — is
specified in the accepted [M3.3 contract](../../Milestones/contracts/m3_3.md) §19 and **does not
exist**. **None may be typed**, and none becomes typeable on the strength of an accepted contract.

## Appendix C — the stop rule

There is one rule under all the others, and it is worth more than the rest of this document:

> **When something does not match what this runbook says it should be, stop and report it.**
> Do not adjust a threshold to make it pass. Do not delete the thing that failed. Do not re-run until
> it agrees. Do not proceed "just to see."

A stopped phase costs a day. A phase that proceeded past a mismatch costs the pilot.
