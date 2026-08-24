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

## 28b. Launching and stopping a long canary — the corrected contract

**`IMPLEMENTATION WIP — NOT YET GOVERNED BY AN ACCEPTED DECISION`** · **`SEPARATE OWNER GATE`**

> **Why this section exists.** The D128 complete-source canary ran for `33 h 18 m 43 s` and
> **could not be stopped**. The watchdog reported that it had stopped it. Accepted
> [Decision 129](../Decisions/decision_129_m3_3_d128_semantic_adjudication.md) §9 (**D129-R10**)
> records the forensic result `WATCHDOG_FALSE_ALERT_SIGNAL_NOT_DELIVERED_TO_CANARY`, and the cause
> was the **launch shape**, not the parser: a non-interactive `zsh` backgrounded the run with `&`,
> POSIX requires such a shell to start a background job with `SIGINT` set to `SIG_IGN`, and CPython
> leaves an inherited `SIG_IGN` in place. Every later signal reached a process that had been told
> to ignore it before it ever ran. `kill` kept succeeding, because `kill` reports that a signal was
> **sent**.

**Nothing about signal handling inside the parser changes.** The repair is the process chain and
the stop procedure.

### The launch shape

> **SUPERSEDED BY [§28e](#28e-the-one-canonical-launch-command--decision-140).** The shape below
> is retained because the reasoning under it — foreground, never `&`, `exec`, one process deep —
> is unchanged and still correct. **Do not copy this command.** Its `--pid-file` is under
> `$WORK_ROOT`, which Decision 140 (D140-R10) refuses: that writes to the external volume before
> the application has authenticated it, and puts the failure diagnosis inside the tree a disposal
> would remove. It also sets no `SQLITE_TMPDIR` on the pane, no durable logs, and no resource
> report. **§28e is the one canonical command.**

Run the canary as the **foreground** command of its tmux pane. Never background it with `&`.

```bash
# SUPERSEDED — retained for its reasoning only. The canonical command is in §28e.
tmux new-session -d -s "$SESSION" \
  "'$PWD/.venv/bin/python' '$PWD/scripts/m3/canary_launch.py' \
     --pid-file '$WORK_ROOT/canary.pid' -- \
     '$PWD/.venv/bin/disclosure-drift' m3 canary-source \
       --config configs/project.yaml --mode run \
       --source-instance-id '<SOURCE_INSTANCE_ID>' \
       --run-id '<RUN_ID>' --work-root '$WORK_ROOT'"
```

[`scripts/m3/canary_launch.py`](../../scripts/m3/canary_launch.py) does three things and stops:

1. it **refuses to launch at all** — exit `3`, `LAUNCH_REFUSED_SIGINT_IGNORED` — if it finds
   `SIGINT` already ignored, so a chain that reintroduces the D128 shape fails in the first second
   rather than after thirty-three hours;
2. it records its own PID in `--pid-file`;
3. it `exec`s the canary, so the process that does the work **keeps that PID** and the pane's
   process chain stays one process deep.

`exec` matters twice: it keeps the chain short, and it resets a *handled* signal to its default
disposition in the new image while preserving an *ignored* one. Passing the check and then
`exec`ing is therefore a proof that carries into the run.

**The launcher holds no authority constant, reads no catalog, takes no lease, and enables no
network. It never starts anything by itself.**

### Stopping, and proving the stop happened

```bash
./.venv/bin/python scripts/m3/canary_watchdog.py stop \
    --pid "$(cat "$WORK_ROOT/canary.pid")" \
    --expect-command 'm3 canary-source' \
    --timeout-seconds 120
```

[`scripts/m3/canary_watchdog.py`](../../scripts/m3/canary_watchdog.py) sends **one** `SIGINT` and
then watches the target actually go away.

| Exit | Outcome | Meaning |
| --- | --- | --- |
| `0` | `STOP_CONFIRMED` | the signal was delivered **and the process terminated** |
| `0` | `STOP_TARGET_ALREADY_GONE` | nothing was signalled; the process did not exist, or it exited in the gap between the liveness check and the signal |
| `3` | `STOP_REFUSED_NON_POSITIVE_PID` | `--pid` was `0` or negative; **nothing was inspected and no signal was sent** |
| `3` | `STOP_REFUSED_TARGET_MISMATCH` | the PID's command line did not match `--expect-command`; **no signal was sent** |
| `3` | `STOP_REFUSED_EMPTY_EXPECT_COMMAND` | `--expect-command` was empty or whitespace-only; **no signal was sent** |
| `4` | `STOP_FAILED` | the signal was sent and **the process is still alive** |
| `4` | `STOP_FAILED_SIGNAL_NOT_PERMITTED` | the signal was **not permitted**, so none was delivered and the process is still there |

**Never pass `--expect-command ''`.** Every command line contains the empty string, so an empty
expectation authenticates nothing while reporting that it did. It is refused outright. Omit the
option entirely to state *no* expectation — that is a different and honest thing.

**Never pass a non-positive `--pid`.** `os.kill` reads `0` as the caller's own process group —
from the canary's pane that is the canary and the watchdog together — and `-1` as every process
this user may signal. Both are refused on the argument, before any `ps` read and before any
signal, so a mistyped id costs a refusal rather than a broadcast. Pass the id
`canary_launch.py` recorded in its `--pid-file`.

**`STOP_FAILED` is never reported as a stop, and the watchdog never escalates to `SIGTERM` or
`SIGKILL`.** Escalation would end a governed run mid-write on the watchdog's own authority; that
decision belongs to the operator. On either exit `4`, treat the run as still going and return to
the project owner. `STOP_FAILED_SIGNAL_NOT_PERMITTED` in particular is **not** a stop: the process
is alive and belongs to another user, so nothing was delivered.

### Checking whether the canary holds a network file

```bash
./.venv/bin/python scripts/m3/canary_watchdog.py network-probe --pid "$PID"
```

This runs `lsof -nP -a -p "$PID" -i`. **The `-a` is the point.** Without it `lsof` treats its
selectors as a union and reports every internet file on the host *or* every file of that PID,
which is the form watchdog v1 used and the reason its network evidence was unusable.

A non-positive `--pid` is refused here too, and **before the `lsof` argument vector is built**, so
no command naming one can exist to be run by accident: exit `3`, `PROBE_REFUSED_NON_POSITIVE_PID`,
and **no `lsof` is executed**. `lsof -p 0` and `lsof -p -1` are the union mistake in the reading
direction — an answer about a set is not an answer about a target.

### Member-count stall monitoring stops at traversal completion

```bash
./.venv/bin/python scripts/m3/canary_watchdog.py stall \
    --observed-members "$OBSERVED" --governed-members "$GOVERNED" \
    --seconds-since-member-change "$SECONDS_SINCE_CHANGE" [--phase F2]
```

Accepted [Decision 129](../Decisions/decision_129_m3_3_d128_semantic_adjudication.md) §9
(**D129-R11**): a frozen member count is a stall **only while traversal is incomplete**.

- `observed < governed` — traversal is running; no movement for the threshold is a real stall
  (exit `2`, `MEMBER_TRAVERSAL_STALLED`).
- `observed == governed` — traversal is finished. F1, F2, finalization, and checkpointing all run
  with the count correctly frozen, so member-count alerting is **disabled**
  (`MEMBER_TRAVERSAL_COMPLETE_STALL_MONITORING_DISABLED`, exit `0`). D128 raised a false alert here.
- `observed > governed` — the two counts **disagree**. A traversal cannot pass its own governed
  bound, so one of the numbers is not describing what it is believed to describe: a stale governed
  count, a count read from the wrong run, or an observation that is not the member count at all.
  This is its own verdict (`MEMBER_COUNT_INCONSISTENT_STALL_MONITORING_DISABLED`, exit `5`), not a
  completed traversal. Member-stall timing is disabled with it. **Establish which count is wrong
  before acting on either** — the watchdog will not adjudicate that, and must not be asked to.

**No wall-clock kill rule replaces any of this**, and `--phase` is a label that improves the
message and decides nothing. The counts are **inputs**: this watchdog issues no query against the
live working catalog.

## 28c. What a bounded prefix run does **not** prove about historical shards

**`IMPLEMENTATION WIP — NOT YET GOVERNED BY AN ACCEPTED DECISION`** · **`SEPARATE OWNER GATE`**

> **Why this section exists.** The bulk submissions archive holds two legitimate JSON member
> shapes: primary submissions documents named `CIK##########.json`, and historical overflow
> shards named `CIK##########-submissions-NNN.json`. D128 routed all `5,337` shards through the
> primary parser, which refused them — correctly, since its contract is *one document describes
> one CIK* — and `3,037,614` accessions went unrecorded. The corrected offline traversal defers
> each shard it meets, keeping only its name and its archive ordinal, and parses the whole
> deferred population **after** the traversal ends, against the parent map the traversal built.

### An ordinary `--member-limit` run parses **zero** historical shards

```bash
disclosure-drift m3 canary-source --mode profile-prefix --member-limit N ...
```

A bounded diagnostic prefix stops mid-archive. Its parent map is therefore **incomplete by
construction**, and resolving a shard against an incomplete map would refuse a perfectly
well-formed archive. So the deferred phase does not run at all under a bound:

- a shard met inside the prefix **counts against `--member-limit`** as a member the traversal
  handled, which is what the bound names — it is simply never parsed;
- a prefix finalizes nothing and can never report success, so it makes **no claim** about the
  shard population in either direction;
- this holds even when `N` happens to equal or exceed the whole archive. The bound's *value* is
  not the hinge; **having** a bound is.

**Therefore a `--member-limit` run is not semantic validation of shard dispatch.** It cannot show
that a shard reached the historical parser, that a parent was bound correctly, or that the
deferred population parsed at all. Do not read a clean prefix run as evidence for any of those.

**The future bounded real-semantic validation must use a separately authorized semantic fixture
or mode**, not an ordinary `--member-limit` prefix. That authorization does not exist yet; asking
for one is the correct next step, and stretching the prefix surface to stand in for it is not.

### PRE-NETWORK BLOCKER — `CensusOrchestrator._parse_bulk`

`src/disclosure_drift/sec/census_orchestrator.py` carries the **same** shard-dispatch defect,
unrepaired: `CensusOrchestrator._parse_bulk` routes every `.json` member — historical shards
included — through `parse_submissions_document`.

It is deliberately left alone. The only way to reach it is `CensusOrchestrator.run`, which calls
`require_network()` before anything else, and network is disabled. The corrected offline canary
does not use that path, and E0 does not use it.

> **No future network or live-retrieval authorization may reach
> `CensusOrchestrator._parse_bulk` until historical shard dispatch is repaired there.**

That is a blocker on *enabling network*, not on the offline work. Before any step that enables
network, re-retrieves a source live, or runs the orchestrator against a real endpoint, this
repair must be completed and reviewed first. `require_network()` is what makes the deferral safe
and **must not be weakened, bypassed, or worked around** in the meantime.

## 28d. The external-volume envelope for the corrected canary — Decisions 137 and 138

**`GUARDS IMPLEMENTED AND CORRECTED — THE RUN ITSELF IS NOT AUTHORIZED`** · **`SEPARATE OWNER GATE`**

> **What this section is, and what it is not.** Accepted
> [Decision 136](../Decisions/decision_136_m3_3_external_ssd_active_volume_qualification.md)
> qualified one external SSD mechanically and created a **narrow one-canary exception** to the
> standing D125-R4 cold/archive-only rule (**D136-R8**). **Qualification is not adoption.**
> Decision 137 implemented the fail-closed guards; its independent review found three majors, and
> [Decision 138](../Decisions/decision_138_m3_3_d137_safety_envelope_correction.md) corrected them.
> Running the preflight proves the guards hold; it **does not** authorize a corrected
> complete-source canary, and no command below launches one.

### The protection is automatic, and the identity assertion is mandatory — D138-R1, D140-R2

**A work root that resolves onto any volume other than the system one is held to the complete
external envelope.** That was the D137 review's **MAJOR-1**: with the flag omitted, an operator
could reach an unqualified disk — or the immutable D130 archive itself — without a single guard
running. The decision is now taken from the **path**, by device number, on the nearest existing
ancestor, before anything is created.

**`--require-volume-uuid` is mandatory for the external-SSD canary envelope. Omitting it is a
refusal. Supplying it does not disable or weaken any other launch guard.** That is accepted
[Decision 140](../Decisions/decision_140_m3_3_total_pre_canary_hardening.md) §4 (D140-R2), and it
is restated here by
[Decision 142](../Decisions/decision_142_m3_3_precanary_architecture_freeze.md) §9 (D142-R4)
because this section previously said the opposite:

- **omit it on any external route** — by `/Volumes/<name>` intent, by residence, or by an
  assertion → **refused**, before the volume is consulted. An omitted identity was the one input
  that let an absent volume, or an ordinary directory left at its mount point, be read as internal
  storage and run with no envelope at all;
- **supply it** → it must be exactly `397A4D4A-9508-391E-814E-3B533C7BD049`. Any other value is
  refused before anything is measured. **Decision 138 creates no generic external-volume
  authorization** (D138-R12); D125-R4 remains the general rule outside the one-canary exception;
- **supply it for an internal root** → refused. The assertion can only ever *add* a requirement.

**The check is on the Volume UUID, and never on the mount name.** `/Volumes/SSK SSD` is whatever
volume happens to be mounted there. **No CLI flag, configuration key, or API parameter makes the
UUID optional on an external route**, and none may be added to create one.

An internal work root with no assertion behaves exactly as accepted Decision 116 left it. Nothing
about the historical internal path changed.

### The physical and operator conditions — D137-R9, brought current

> **CURRENCY — read [§28f.C](#c-launch-precheck) for the launch table that governs today.** The
> list below is the **Decision 137-era** condition set, kept because it is the origin of these
> twelve conditions and because their numbering is cited elsewhere. It was **stale**: it recorded
> external power as verified by the operator, carried **no lid row and no transport row**, and
> counted *"five of the twelve"* as mechanical. That is the D143 review's **MINOR-2**, and the
> staleness ran in the conservative direction — it understated what the machine checks and asked
> the operator to verify something the machine already refuses. It is corrected here by
> [Decision 144](../Decisions/decision_144_m3_3_d143_finding_correction.md) §6 (D144-R3) rather
> than deleted, and **conditions 1–12 keep their original numbers** so that references to them do
> not silently repoint. **Where this list and §28f.C could ever be read as disagreeing, §28f.C
> controls.**

**Eight of the fourteen are mechanically verified at launch, four are the operator's to hold, and
two are held by the launch command**, because most of the operator's four cannot be verified from
software and a fake automated check is worse than an honest checklist.

| # | Condition | Verified by |
|---|---|---|
| 1 | The Mac is connected to **external power** | **automatic** — at launch, D141-R9 |
| 2 | The **exact qualified SSD** is connected — Volume UUID `397A4D4A-9508-391E-814E-3B533C7BD049` | **automatic** |
| 3 | The SSD is **physically stationary** for the whole run | operator |
| 4 | It is **not ejected or unplugged**, at any point | operator |
| 5 | It is **not reformatted or repartitioned** | operator |
| 6 | **No unrelated write-heavy activity** on that SSD | operator |
| 7 | **System sleep is prevented** | operator + `caffeinate` |
| 8 | The launcher runs under a **no-sleep** wrapper | launch command |
| 9 | The **D130 archive precheck** matches its accepted identity | **automatic** |
| 10 | **`>= 185` GiB / `198,642,237,440` bytes** free on that volume | **automatic** |
| 11 | The working root is **outside the D130 archive tree** | **automatic** |
| 12 | `SQLITE_TMPDIR` is **explicit and on that same volume** | **automatic** |
| 13 | The **lid is open** | **automatic** — at launch, D141-R9 |
| 14 | The volume is attached over **exactly** `USB_VIA_THUNDERBOLT_DOCK` | **automatic** — D141-R5 + **D144-R1** |

**"At launch" is the whole of the guarantee for 1, 13 and 14.** Power, lid and transport are read
once, immediately before the run is admitted, and **nothing re-reads them afterwards**. Keeping
them true for the following thirty hours is condition 3, 4 and 7 territory — the operator's.

Conditions 3–6 are not inferable from software. **Do not treat their absence from the preflight
output as evidence that they hold** — the preflight cannot see them, and says nothing about them.

### Prepare the working root and the temporary root

Both live at the **volume root, beside the D130 archive** — never inside it.

```bash
VOLUME='/Volumes/SSK SSD'
WORK_ROOT="$VOLUME/FDD_M3_3_D137_WORK"
export SQLITE_TMPDIR="$VOLUME/FDD_M3_3_D137_SQLITE_TMP"
mkdir -p "$WORK_ROOT" "$SQLITE_TMPDIR"
```

`SQLITE_TMPDIR` must be **exported**, not merely set for one command: SQLite reads it from the
environment of the process that spills, which is the canary itself. Left unset, SQLite spills to
the operating system's temporary directory **on the internal volume**, which the capacity model
does not cover — and the guard refuses rather than letting that happen silently. **The environment
the guard validates is the environment SQLite consumes** (D138-R3): it reads the process
environment, and refuses if a caller hands it a different value to check.

### Run the preflight — read-only, creates nothing

```bash
./.venv/bin/disclosure-drift m3 canary-source \
    --config configs/project.yaml --mode preflight \
    --source-instance-id '<SOURCE_INSTANCE_ID>' \
    --run-id '<RUN_ID>' --work-root "$WORK_ROOT" \
    --require-volume-uuid 397A4D4A-9508-391E-814E-3B533C7BD049
```

**The `--require-volume-uuid` line is mandatory, not optional. Dropping it is itself a refusal**
(D140-R2; [Decision 142](../Decisions/decision_142_m3_3_precanary_architecture_freeze.md) §9),
and supplying it weakens no other guard — every check below still runs. Each of these is a
**refusal**, and none falls back to internal storage:

- `--require-volume-uuid` is **omitted** on an external route;
- the volume's **Volume UUID** is not the accepted one;
- **nothing is mounted** where the working root points;
- the volume **lookup fails** for any reason;
- the working root **is**, **lies inside**, or **contains** the D130 archive directory — decided
  on `realpath`-resolved components, so a `..` path, a symlink, or a case variant cannot launder
  it, and a merely similar name is not falsely refused;
- free space on **that volume** is below `198,642,237,440` bytes;
- the **D130 archive precheck** differs from its accepted governance identity;
- `SQLITE_TMPDIR` is unset, relative, absent, inside the archive, or on another volume;
- an asserted UUID is anything other than the one qualified volume.

**`BSD identifiers are not identity.`** `disk4` and `disk4s2` are assigned at attach time and will
differ across reboots and re-plugs. The mount path is not identity either — `/Volumes/SSK SSD` is
whatever volume happens to be mounted there. Only the Volume UUID is checked.

A passing preflight prints `canary_authorized: false`. That is not a formality: **passing the
preflight is not authorization to launch** (D137-R12).

### The five floors, and what each one does on breach

Five different numbers answering five different questions. **None replaces another**, and each is
checked before the phase it admits.

| Where | Floor | Behaviour on breach |
|---|---|---|
| `PRE_LAUNCH` | `185` GiB / `198,642,237,440` B | **refuse to launch** — no world is created |
| `POST_F0` | `60` GiB / `64,424,509,440` B | **stop and report.** F1 does not begin |
| `PRE_F1` | `55` GiB / `59,055,800,320` B | **stop and report.** F1 does not begin |
| `POST_F1_PRE_F2` | `50` GiB / `53,687,091,200` B | **refuse F2** before its transaction opens |
| `DURING_F2` continuous | `10` GiB / `10,737,418,240` B | **abort and roll back**, alerting from `20` GiB |

Every floor admits **at** its own value and refuses one byte below it. **A measurement that cannot
be taken refuses** — an unmeasurable volume is never treated as one that passed. **Nothing is
deleted, moved, or cleaned to clear any floor**, at any of the five.

### Capacity during F2 is enforced inside the run — D138-R8, D138-R9

The D137 review's **MAJOR-2** was that the `10` GiB `DURING_F2` floor was a classification and an
optional second process, and nothing else. It is now enforced **inside the process executing F2**:

| Free space | State | What the run does |
|---|---|---|
| `> 20` GiB | `F2_CAPACITY_NORMAL` | nothing; F2 continues |
| `<= 20` GiB | `F2_CAPACITY_ALERT` | records a `DURING_F2` observation and **continues** |
| `<= 10` GiB | `F2_CAPACITY_HARD_STOP` | **aborts F2 from inside its transaction** |
| unmeasurable | `F2_CAPACITY_MEASUREMENT_FAILED` | **aborts F2 the same way** — fail-closed |

Free space is sampled immediately **before** F2 opens its transaction and repeatedly **while** it
is open, from F2's own per-accession loop, on a **monotonic** clock. The interval is bounded: the
ceiling is `60` seconds and the scheduled interval is well inside it, so a long batch can never
buy hours of unobserved execution.

> **A hard stop during F2 is a rollback, not a truncation.** F2 is a **single transaction**.
> Aborting inside it discards the in-flight association projection entirely — the run does not
> resume from where it stopped, and there is no partial result to keep. **No partial F2
> association state is ever committed.** Bounded evidence naming the phase, the reason, the
> measured free bytes or the measurement failure, the threshold, the observation time, the volume
> identity, and the fact that F2 rolled back survives the rollback and is reported.

The abort **deletes nothing, sends no signal, and escalates nothing** — the accepted Decision 131
no-escalation behaviour is untouched. **Never delete anything from the SSD to clear a floor**:
accepted [Decision 125](../Decisions/decision_125_m3_3_external_archival_and_reclamation.md)
**D125-R3** bars deleting further evidence for capacity, and the D130 archive is the **only**
surviving copy of the D128 evidence.

### The watchdog `capacity` subcommand is supplemental only — D138-R11

```bash
./.venv/bin/python scripts/m3/canary_watchdog.py capacity --path "$WORK_ROOT/<RUN_ID>"
```

This is **observability for a human**, not enforcement. It reports the same three states from
outside the run and **exit `6` does not stop F2** — the in-process guard is what stops it. It
sends no signal, deletes nothing, and cleans nothing at any threshold. Acting on anything it
reports stays your decision, through the `stop` subcommand in §28b.

### The launch command

**`NOT AUTHORIZED UNTIL SEPARATE OWNER CANARY AUTHORIZATION`**

The corrected complete-source canary is launched with the **[§28e](#28e-the-one-canonical-launch-command--decision-140)**
canonical command and no other. **It must not be run on the strength of a passing preflight, of
Decision 136, of Decision 137, of Decision 138, or of Decision 140.** A separate owner instrument
authorizes it, and it runs **from scratch, in a new world, under a new run identity** — accepted
[Decision 129](../Decisions/decision_129_m3_3_d128_semantic_adjudication.md) **D129-R8**,
unchanged.

### After the run — the D130 archive postcheck

Re-run the preflight's bounded archive check after the run and compare. **Any difference is a
blocker**, not a note: it means the corrected canary disturbed the only surviving copy of the D128
evidence. The check is bounded on purpose — the four small compact proofs from
[Decision 130](../Decisions/decision_130_m3_3_d128_archival_and_reclamation.md) §6 are hashed, and
the `103,966,696,960`-byte tar is **stat**-ed and never opened. **The archive is immutable**:
nothing is ever written, moved, deleted, or hashed beyond those four proofs inside that tree.

### What none of this claims — D137-R11

The volume is **ExFAT**, served by Apple FSKit, with **no metadata journal**. Accepted Decision 136
established **process-crash recovery only**. Nothing here claims journaled filesystem semantics,
**power-loss safety**, **surprise-removal safety**, or **USB-bridge cache-flush correctness** —
D136 could not distinguish a satisfied `F_FULLFSYNC` from a bridge that ignored one, and did not
try. Conditions 1 and 3–5 above exist precisely because the filesystem does not cover them.
Decision 138 corrects the safety envelope; it does not change one word of this boundary.

## 28e. The one canonical launch command — Decision 140

**`NOT AUTHORIZED. THE TOKEN BELOW IS A PLACEHOLDER AND IS NOT AN AUTHORIZATION.`**

Accepted [Decision 140](../Decisions/decision_140_m3_3_total_pre_canary_hardening.md) closes the
D139 independent review's **MAJOR-2**: there was no single launch shape an operator could copy,
and the three shapes that existed each omitted something that a thirty-hour run cannot recover
from. This section is the one canonical command. Every other launch snippet in this runbook is
superseded by it.

### The physical and operator conditions — D140-R20

Check these **before** anything below. `caffeinate` holds power assertions; **it does not prevent
a MacBook lid-close from sleeping the machine**, and no software does. That is why these are
conditions rather than mechanisms.

| # | Condition | Why | Enforced |
|---|---|---|---|
| 1 | The Mac is on **AC power** for the whole run | Thirty hours is not a battery-length run. | **Mechanically**, at launch (D141-R9) |
| 2 | The **lid stays open** for the whole run | `caffeinate -dims` cannot defeat lid-close sleep. | **Mechanically**, at launch (D141-R9) |
| 3 | The SSD is attached over a **qualified transport** — see §28f | Decision 136 assumed a direct connection and this row asserted one. **Decision 141 measured the operator's actual topology and found that false**: the SSD reaches the host three USB hub tiers deep inside a ThinkPad Thunderbolt 4 Dock. | **Mechanically**, at launch (D141-R5) |
| 4 | The machine and the SSD stay **stationary** | ExFAT has no metadata journal; a surprise removal is not covered. | Operator |
| 5 | Nothing **ejects or unplugs** the volume or the dock | Same. | Operator |
| 6 | No other **heavy SSD activity** — see the co-tenancy rules in §28f | The capacity model assumes the canary is the only writer. | Operator |

Conditions 1–3 are **checked by the application**, inside the same composed preflight that
authenticates the volume, so they hold on every route into a canary — `preflight`, `run`, and
`profile-prefix` alike. Until Decision 141 they were not: `require_launch_power_conditions` was
written, unit-tested, and named by this table, and **no production path called it**. Conditions
4–6 remain the operator's, because nothing in software can hold them.

An unreadable power or lid state is **refused**, not assumed. Both readings are normally
available on this host, and the explicit operator assertion excuses an *unreadable* reading
only — never a host actually reporting battery power or a closed lid.

### The internal runtime directory — D140-R10

Runtime control lives on **internal** storage, never under `$WORK_ROOT`:

```bash
RUNTIME="$DISCLOSURE_DRIFT_EVIDENCE_ROOT/runs/m3_3_canary_runtime/<RUN_ID>"
mkdir -p "$RUNTIME"          # internal; NOT on the SSD, NOT inside the D130 archive
```

Everything a failure diagnosis needs is there and survives the volume being unplugged: the pid
record, stdout, stderr, and the resource report. The launcher **refuses** — exit `3`,
`LAUNCH_REFUSED_RUNTIME_PATH_NOT_INTERNAL` — if any of them would land beneath `$WORK_ROOT`.

### The command

```bash
# NOT AUTHORIZED. Copying this does not authorize it.
# <OWNER_CANARY_AUTHORITY_NOT_YET_ISSUED>
#
# WORK_ROOT   must already exist on the qualified volume: D140-R5 forbids create_world from
#             making it, because making it would recreate a mount point that had gone away.
# SQLITE_TMPDIR must be injected with tmux -e. Exporting it does NOT reach a pane created on
#             an already-running tmux server, and the failure is silent.
tmux new-session -d -s "$SESSION" \
  -e "SQLITE_TMPDIR=$TMPDIR_EXTERNAL" \
  "/usr/bin/caffeinate -dims \
   /usr/bin/time -l -o '$RUNTIME/resource.log' \
   '$PWD/.venv/bin/python' '$PWD/scripts/m3/canary_launch.py' \
     --pid-file '$RUNTIME/canary.pid' \
     --stdout '$RUNTIME/stdout.log' \
     --stderr '$RUNTIME/stderr.log' \
     --work-root '$WORK_ROOT' \
     --require-sqlite-tmpdir -- \
     '$PWD/.venv/bin/disclosure-drift' m3 canary-source \
       --config configs/project.yaml --mode run \
       --source-instance-id '<SOURCE_INSTANCE_ID>' \
       --run-id '<RUN_ID>' \
       --work-root '$WORK_ROOT' \
       --require-volume-uuid '397A4D4A-9508-391E-814E-3B533C7BD049'"
```

There is **no `--member-limit`**: `run` is complete-source only, and a bound is refused outright
rather than ignored.

Each part earns its place:

| Part | What it fixes |
|---|---|
| `-e SQLITE_TMPDIR=…` | An exported value reaches a pane only when tmux starts a **new server**. Attaching to an existing one gives that server's environment, so SQLite spills to the internal volume for thirty hours while the operator's shell shows the right value. |
| `caffeinate -dims` | Display, disk, idle-system and user-active assertions, held for the child's whole lifetime. **Not** a defence against lid-close. |
| `time -l -o …` | Peak resident set size, durably, for the real run — closing D139's **INFO-4**. It is not a threshold and kills nothing. |
| `canary_launch.py` | Refuses if `SIGINT` is already ignored (the D128 condition), refuses a runtime path under `$WORK_ROOT`, refuses a missing `SQLITE_TMPDIR`, records the PID, redirects to durable logs, and `exec`s — so the recorded PID **is** the canary's. |
| `--require-volume-uuid` | **Mandatory** (D140-R2). Omitting it is a refusal, not a weaker run. |

`caffeinate` and `time` are **ancestors** of the canary rather than things the launcher `exec`s.
If the launcher `exec`'d `caffeinate`, the pid file would name `caffeinate` and the stop path
would signal a process that is not the canary — D128's defect by another route.

### Stopping — use the governed path, D140-R18

```bash
./.venv/bin/python scripts/m3/canary_watchdog.py stop-canary \
    --pid-file "$RUNTIME/canary.pid" \
    --run-id '<RUN_ID>'
```

The legacy `stop --pid … --expect-command 'm3 canary-source'` is **not** the canary stop path.
`--expect-command` is a **substring** test against a command line, and an operator shell that has
merely typed the canary's command carries that text in its own — so the decoy authenticates
perfectly. `stop-canary` reads the exact PID from the pid record, **scans nothing**, and requires
the target's own `argv[0]` to be a canary executable, the `m3 canary-source` tokens to be
adjacent, and `--run-id` to be exactly this run. A shell is refused on `argv[0]` whatever the rest
of its command line says. One `SIGINT`, a bounded wait, and **no escalation**.

### After a failure — reclaim readiness, D140-R19

A late failure can leave a ~120 GiB world behind, and 185 GiB is then not available for a fresh
attempt without reclaiming it. **That physical fact is not removed by anything in Decision 140.**
What is removed is the ambiguity about what to do next:

`failed_world_reclaim_readiness()` reports the exact run identity, whether a normal success result
exists, world/database/WAL sizes, the durable runtime evidence, and `FAILED_WORLD_RECLAIM_READY`.
It names **only** the exact world directory for that exact run as eligible, never the work root,
never a sibling world, never the D130 archive, and never the source artifact.

**It deletes nothing, and holding its report authorizes nothing.** Disposal stays owner-gated,
and a world carrying a normal success result is never reclaim-ready.

### Pause and resume — NOT IMPLEMENTED, and why

**`GOVERNED PAUSE/RESUME IS NOT AVAILABLE. DO NOT ATTEMPT TO PAUSE A RUNNING CANARY.`**

There is no supported way to pause a complete-source canary and resume the same world. The
architectural finding is recorded in
[Decision 140](../Decisions/decision_140_m3_3_total_pre_canary_hardening.md) §17; the operator
consequences are:

* **Do not** use `kill -STOP` / `kill -CONT`. Suspending the process does **not** quiesce SQLite,
  does not close handles, and does **not** make the volume safe to eject. It looks like a pause
  and is not one.
* **Do not** unplug or eject the SSD while a canary is running, for any reason. There is no
  `SAFE_TO_EJECT` state, because there is no mechanism that could establish one.
* If the machine must be disconnected from the SSD, the run is **lost** and a new run identity is
  required. Worlds are create-once and are never resumed (D129-R8).
* Keep the Mac on AC power and the lid open for the whole run — conditions 1 and 2 above. There is
  no pause to fall back on.


## 28f. The qualified transport, and the conditions around it — Decision 141

**`NOT AUTHORIZED. NOTHING IN THIS SECTION AUTHORIZES A CANARY.`**

Accepted [Decision 141](../Decisions/decision_141_m3_3_thunderbolt_dock_qualification.md)
qualified how the volume is **attached**. Decision 136 qualified *which* volume; Decisions 137,
138 and 140 built the envelope around it. None of them asked what sits on the wire, and §28e
condition 3 asserted a direct connection that was not true.

### A. The qualified topology, as measured — not as named

The dock's product name is `ThinkPad Thunderbolt 4 Dock` and it is a genuine Thunderbolt 4
device. **That does not make the SSD Thunderbolt storage, and this section does not call it
that.** What macOS actually reports:

| Fact | Reading |
|---|---|
| Transport class | **`USB_VIA_THUNDERBOLT_DOCK`** |
| Dock | `ThinkPad Thunderbolt 4 Dock`, Lenovo `0x17EF:0x30B3`, firmware `38.6` |
| Dock link | Thunderbolt/USB4 Bus 1, upstream **connected at `40` Gb/s**, mode **`usb_four`** |
| Dock's downstream Thunderbolt port | **empty** — `receptacle_no_devices_connected` |
| Volume's own bus protocol | `diskutil` reports **`BusProtocol = USB`** |
| Attachment | USB mass storage, **three hub tiers** inside the dock |

The cascade, host-side first, walked from the mounted volume's own media rather than assumed:

```
AppleT8103USBXHCI            the Mac's own USB host controller
└── USB3.0 Hub   0x8087:0x0B40   Intel — the dock's USB4-side hub
    └── USB3.1 Hub 0x17EF:0x30B6  Lenovo
        └── USB3.1 Hub 0x17EF:0x30B8  Lenovo
            └── SSK SSD  0x090C:0x2320   the qualified volume's enclosure
```

**The Volume UUID `397A4D4A-9508-391E-814E-3B533C7BD049` is unchanged and remains the primary
identity.** The transport is a second, narrower condition, and it never substitutes for the UUID.

**No BSD disk identifier is part of the profile.** `disk4`/`disk4s2` change across reboots and
re-plugs; the current one is used only as a momentary lookup key into the IORegistry. **A changed
disk number does not refuse**, and that non-refusal has its own test.

### B. Physical setup

Reproduce the qualified topology exactly:

* the **same** ThinkPad Thunderbolt 4 Dock;
* the **same** Mac-facing dock cable, in the **same** Mac port;
* the **same** SSD cable, in the **same dock port** — a different dock port produces a different
  hub cascade, which is a topology Decision 141 did not qualify and which **refuses**;
* **AC power through the dock** — the qualification measured a `92` W supply, connected before,
  during and after sustained I/O;
* **lid open**;
* Mac, dock and SSD **stationary**, with nothing resting on any cable.

If the transport check refuses, **restore the qualified attachment**. Do not relax the profile,
and do not work around the refusal.

### C. Launch precheck

Run the read-only preflight and read every line. It creates nothing:

```bash
./.venv/bin/disclosure-drift m3 canary-source \
    --config configs/project.yaml --mode preflight \
    --source-instance-id '<SOURCE_INSTANCE_ID>' \
    --run-id '<RUN_ID>' \
    --work-root "$WORK_ROOT" \
    --require-volume-uuid '397A4D4A-9508-391E-814E-3B533C7BD049'
```

**The table below was corrected by
[Decision 144](../Decisions/decision_144_m3_3_d143_finding_correction.md) §5 (D144-R2).** It
previously presented **eight** rows under a single categorical header — *"each is checked by the
application rather than by reading this page"* — and **two of them were not checked by the
application**: the transport row demanded the dock class while the code checked only membership
in the two-element qualified set, and the co-tenancy row named something the code does not
inspect at all. That is the D143 review's **MAJOR-2**, and it is the defect class §28f exists to
remove: a page that claims a machine is watching, when it is not, is worse than a page that asks
the operator to look. The two categories are now separated, and nothing is claimed for one that
belongs to the other.

#### C.1 Mechanically enforced launch predicates

**Every row here is refused by the application, before anything is created.** They are listed so
you can read the preflight output against them — not so you can check them yourself.

| Gate | Requirement | Enforced by |
|---|---|---|
| Transport | `transport_class` is **exactly** `USB_VIA_THUNDERBOLT_DOCK` — a qualified `USB_DIRECT` attachment **refuses** on this path | D141-R5 + **D144-R1** |
| Identity | the volume reports **exactly** the qualified UUID, mounted **now**, at a real mount point | D137-R1, D140-R2, D140-R3 |
| Power | `on_ac_power` true, `clamshell_closed` false | D141-R9 |
| Isolation | the work root is outside the D130 archive | D137-R3 |
| Archive | the bounded D130 compact precheck matches; the `~104` GB tar is **stat-ed, never opened** | D137-R10 |
| Capacity | `>= 185` GiB free **on that volume** | D137-R4 |
| Temporary root | `SQLITE_TMPDIR` set, absolute, existing, external, outside D130, same volume | D137-R8, D138-R3 |
| One canary | a **second complete-source canary** on this host is refused, whatever run identity it is given | D140-R16 |

**The transport row became mechanically true on 2026-08-23, and was not before.** Accepted
[Decision 142](../Decisions/decision_142_m3_3_precanary_architecture_freeze.md) §4 selected the
dock topology; **Decision 144 (D144-R1) is what makes the production path demand it.** All three
canary entry points now narrow the envelope to that one class, so a directly attached qualified
SSD refuses here — including as the answer to a dock refusal, which §28g.D forbids in terms.

**The "one canary" row is exact, and its scope is worth stating rather than rounding up**
(D143 OBSERVATION-1, closed by [Decision 144](../Decisions/decision_144_m3_3_d143_finding_correction.md)
§8): the host execution lock is taken by **`--mode run`**, so it excludes a second
complete-source canary and **nothing else**. A concurrent `--mode profile-prefix` on the same
host is **not** mechanically excluded and would consume volume space the running canary's
capacity model assumes it alone consumes. Do not start one. That is an operator rule, and it is
listed as one in C.2 rather than borrowed into the table above.

#### C.2 Operator rules — the application checks none of these

**Nothing below is verified by any launch predicate.** Their absence from the preflight output is
not evidence that they hold; the preflight cannot see them and says nothing about them.

* **No heavy competing SSK SSD workload** while a canary runs — the full list is in E. **Nothing
  in the application inspects other processes, and nothing here kills a user application.**
* **No concurrent `--mode profile-prefix` run**, per the scope note above.
* The SSD, the dock and the Mac stay **physically stationary**, with nothing resting on a cable.
* The SSD and the dock are **not disconnected, ejected, reformatted or repartitioned** at any
  point during the run — see F, and §28g.F.
* The lid **stays** open and the machine **stays** on AC for the whole run. Both are checked
  **at launch** and neither is re-checked afterwards.

`canary_authorized` prints **`false`**. That is correct and is not a gate to be worked around:
**passing every check is not an authorization to launch.**

### D. Normal operation

With the dock qualified, the whole point of the topology is that both hold at once:

* **keep the Mac charging through the dock**, and
* **keep the SSD attached to the dock**, and
* **do not unplug the dock, the SSD, or either cable while a canary runs.**

Decision 141 proved that charging and sustained SSD I/O coexist — AC power, mount, device
identity and adapter wattage were sampled *during* a sustained multi-gibibyte write and never
varied. It did **not** prove the dock cannot fail, and no test performed or authorized a
surprise removal.

### E. Co-tenancy while a canary runs — Decision 140-A3, published here

The machine stays usable. The volume does not.

**Allowed** — browser, ChatGPT, light productivity, light terminal activity.

**Avoid** — games; VM workloads; large local ML or Python jobs; big downloads or copies; backup
jobs that use the SSD; media export; other database workloads on the SSD.

**Strictly forbidden** — another FDD writer; another canary; any modification of the D130
archive; ejecting the SSD; disconnecting the dock; any heavy competing SSK SSD workload.

A second complete-source canary is refused mechanically by the host execution lock (D140-R16),
whatever run identity it is given. The rest of this list is the operator's to hold: **nothing
here kills a user application**, and nothing should be added that does.

### F. Pause and resume — still NOT IMPLEMENTED

Decision 141 changes nothing about this. `GOVERNED_PAUSE_RESUME = NOT_IMPLEMENTED`, there is no
`SAFE_TO_EJECT` state, `kill -STOP` is not a governed pause, and **the SSD and the dock must not
be disconnected while a canary runs**. See §28e and Decision 140 §17. Qualifying the dock does
**not** create a way to detach it.


## 28g. The selected first-canary configuration — Decision 142

**`NOTHING IN THIS SECTION AUTHORIZES A CANARY. CANARY_AUTHORIZED = NO.`**

[Decision 142](../Decisions/decision_142_m3_3_precanary_architecture_freeze.md) accepts Decision 141
for continuation, **selects one topology** for the first complete-source canary, **defers governed
pause/resume beyond it**, and **freezes the pre-canary architecture**. Decision 141 §16 left the
selection to the owner; §4 (D142-R2) is that selection. It is a choice between two already-qualified
configurations, and it authorizes no run on either.

### A. The selected path — D142-R2

Use the **D141-qualified `USB_VIA_THUNDERBOLT_DOCK` topology**. That is the one selected
configuration for the first canary.

`USB_DIRECT` — the Decision 136 topology — **remains separately qualified and is not revoked**
(D141-R8, preserved). **It is not selected**, and the first canary does not run on it.

### B. The same physical topology — D142-R2

Use the **qualified storage device** and the **same qualified dock path and port**, exactly as
§28f.B describes:

| Element | Value |
|---|---|
| Volume UUID | `397A4D4A-9508-391E-814E-3B533C7BD049` |
| USB vendor / product | `0x090C` / `0x2320` |
| USB serial | `SSKPSSD0000000000071` |
| Required ordered dock cascade | `0x8087:0x0B40` → `0x17EF:0x30B6` → `0x17EF:0x30B8` |

**A changed BSD disk identifier is not a refusal.** `disk4`, `disk4s2`, or any successor is
attach-time state; the exact Volume UUID and the frozen transport profile are the identity.

### C. The UUID assertion is mandatory — D140-R2, D142-R4

```text
--require-volume-uuid 397A4D4A-9508-391E-814E-3B533C7BD049
```

**Omitting it is a refusal.** Supplying it disables and weakens nothing else — see the corrected
§28d. It is checked on the Volume UUID and never on the mount name, and there is no other CLI,
configuration, or API route that makes it optional.

### D. No fallback — D142-R2

**If the dock transport qualification refuses, STOP.**

* **Do not** switch that same canary to direct storage.
* **Do not** relax the transport profile or work around the refusal.
* Restore the qualified attachment, or **return to the owner**.

There is no automatic fallback and no operator fallback between the two topologies for the
authorized first-canary configuration. A refusal states that the physical configuration is not the
one that was qualified; it is never a prompt to select the other qualified one mid-run.

### E. Continuous attachment — D142-R3

For the whole run, do **not** intentionally:

* eject the SSD;
* unplug the SSD;
* unplug or reconfigure the dock storage path;
* move the SSD to another dock port;
* substitute the direct path;
* substitute another volume;
* treat a sleeping or stopped process as safely detachable.

All existing mechanical launch predicates still apply at launch. None is replaced or relaxed by the
topology selection.

### F. Pause and resume — NOT IMPLEMENTED, D142-R3

```text
GOVERNED_PAUSE_RESUME = NOT_IMPLEMENTED
```

There is **no** `SAFE_TO_EJECT` state, no governed detach, no governed reconnect, no topology
switch, no storage migration, and no pause-and-move workflow.

* **`kill -STOP` is not a governed pause** and does not make detaching safe.
* **Closing the lid is not a governed pause.**
* **Qualifying the dock did not create permission to detach it.**

Decision 142 defers this deliberately and implements no state machine. See
[Decision 140](../Decisions/decision_140_m3_3_total_pre_canary_hardening.md) §17 for the
architectural finding, which remains open owner work.

### G. Interruption is not pause — D142-R3

**If continued operation would require any action in E, the run is INTERRUPTED, not PAUSED.**

An interrupted run is lost and requires a new run identity; worlds are create-once and are never
resumed (D129-R8). **There is no procedure here for recovering from a physical disconnection, and
none may be written** — a documented recovery that does not exist is worse than an honest statement
that none does.


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
