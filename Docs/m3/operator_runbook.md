# Milestone 3 — Mac Operator Runbook

**Status:** documentation only. **No step here is authorized to run against the SEC network.**
**Controlling records:** [Decision 027](../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§7, as narrowly corrected by accepted
[Decision 028](../Decisions/decision_028_m3_1_readiness_corrections.md).
**Plan:** [`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md).

This runbook is written for the project owner operating on macOS. It is sequential: work down it, and
stop at the first step that fails. It is **documentation, not authorization** — following it does not
authorize any phase, and several steps describe commands that **do not exist yet**.

---

## How to read the labels

Every command in this runbook carries exactly one label.

| Label | Meaning |
|---|---|
| **`AVAILABLE NOW`** | Implemented and accepted today. Safe to run as written. |
| **`PLANNED — NOT YET IMPLEMENTED (M3.1)`** | Does not exist. Its interface contract is stated so a bounded M3.1 contract implements this interface rather than inventing one. |
| **`PLANNED — NOT YET IMPLEMENTED (M3.2)`** | Does not exist. Same rule, for M3.2. |
| **`MANUAL OWNER APPROVAL`** | Not a command. A decision the owner records in a template under [`templates/`](templates/request_budget.md). |
| **`VERIFICATION`** | A read-only check whose output is compared against an expectation. |
| **`RECOVERY`** | Run only after an interruption or a failure, never routinely. |

**A `PLANNED` command must never be typed.** It will not exist, and a shell will report it as
unknown. It is documented so the interface is agreed before it is built.

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

**`PLANNED — NOT YET IMPLEMENTED (M3.1, Decision 028 §11)`**

Every M3 evidence-output command *will* resolve its evidence root before writing and refuse a root
equal to, inside, or containing the checkout, so that symlinks cannot bypass the check. The
repository-root `.m3-private-evidence/` path *will* be matched by a reserved `.gitignore` rule
`/.m3-private-evidence` and explicitly rejected by repository hygiene; it is never a lawful
operational evidence root.

None of these three protections exists yet: the `.gitignore` rule, the repository-hygiene refusal,
and the resolved-path CLI check are all future M3.1 contract requirements, and no M3 evidence-output
command exists. See limitations register **M3-L11**.

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

**`PLANNED — NOT YET IMPLEMENTED (M3.1)`**

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
| Stdout | One line per scenario: `id`, name, outcome, reason code; then a summary line with counts |
| Side effects | Writes only under an isolated synthetic data root and the named evidence path |
| Exit codes | `0` all scenarios passed · `1` configuration error · `2` usage · `3` stage not enabled · `4` gate failure (any scenario failed) |
| Receipt | Emits one execution receipt per invocation, `invocation_mode = "rehearsal"`, with **actual network counts of `0`**; simulated totals go to the evidence report |

## 11. Review the acquisition-rehearsal evidence

**`PLANNED — NOT YET IMPLEMENTED (M3.1)`** · **`VERIFICATION`**

```
python -m disclosure_drift m3 rehearse-report \
  --evidence-root <absolute-external-path> --evidence <relative-path>
```

**Intended interface contract:** read-only; prints the per-scenario matrix — setup, expected reason
code, observed reason code, persisted state, files, receipt, rollback, recovery, validation — plus the
identity-noncontamination result and the derived per-route `A_reachable`. Exit `0` only when all
twelve acquisition scenarios pass and the noncontamination proof holds.

**Check by hand, against [`offline_rehearsal_spec.md`](offline_rehearsal_spec.md) §5:**

- all twelve scenarios A1–A12 present, none skipped, none `xfail`ed;
- every observed reason code equals its expected registered code;
- **A6** proves every registered route reachable and every denied family refused;
- **A11** proves `m3 recovery-state` is read-only, reports `UNSAFE` before required repair and
  `SAFE` only after the isolated rehearsal applies deterministic repair, and resumes without a
  duplicate substantive write;
- **A12** shows the receipt sample carries **none** of the prohibited fields, and the positive control
  proves the scan is not vacuous;
- **A12** shows every governed value identical with receipts disabled, enabled, and varied;
- **every rehearsal receipt reports actual network counts of `0`**;
- **`A_reachable` is derived per route and independently tested** against the worst reachable path;
- **no snapshot, selection, reserve, sealing, manifest, or root scenario appears here.**

**Stop if** any of those fails. A rehearsal finding is a design finding, and it is cheap here and
expensive later.

## 12. Perform Gate F's zero-request dry run

**`PLANNED — NOT YET IMPLEMENTED (M3.1)`**

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
| Receipt | Emits one `m3-execution-receipt/2.0` receipt, `invocation_mode = "dry_run"`, with zero actual request counts, the acquisition window and plan/version fields, and **no** approved ceiling or later gate outcome |

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

**`PLANNED — NOT YET IMPLEMENTED (M3.1)`** · **`VERIFICATION`**

Run step 12 twice, into two different plan files, then compare:

```
shasum -a 256 <plan-file-1> <plan-file-2>
diff <plan-file-1> <plan-file-2>
```

Expect: identical SHA-256 values and **no** `diff` output.

**Stop if they differ.** Do not re-run until they agree — the disagreement is the finding, and it
means a plan input is being read from the environment or the clock rather than supplied explicitly.

## 14. Print and inspect the request budget

**`PLANNED — NOT YET IMPLEMENTED (M3.1)`**

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

**`PLANNED — NOT YET IMPLEMENTED (M3.2)`** · **owner-authorized window only**

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

**`PLANNED — NOT YET IMPLEMENTED (M3.2)`** · **`VERIFICATION`**

```
python -m disclosure_drift m3 acquire --show-scope
```

**Intended interface contract:** read-only; prints the allowed hosts, the allowed method, the exact
route allowlist, the denylist families, the approved plan hash, the approved ceiling, and the
consumed-count baseline — **and makes zero requests**. Exit `0`.

Compare its output against the Gate F evidence. **Stop on any difference**, including a difference in
the plan hash.

## 18. Start controlled acquisition

**`PLANNED — NOT YET IMPLEMENTED (M3.2)`**

First, establish Gate H **pre-run** state (milestone plan §11, Gate H):

- an isolated M3.2 data root;
- a consistent SQLite backup of any accepted prior state;
- recorded available storage;
- confirmed quarantine and staging paths;
- the confirmed single-writer lock;
- **no** stale `.part` files and **no** unresolved recovery events;
- the approved plan hash saved.

Then:

```
python -m disclosure_drift m3 acquire --plan <path> --window M3.2A --live --ceiling <INT> \
  --receipt-out <private-path>
```

**Intended interface contract:**

| Aspect | Contract |
|---|---|
| Purpose | Execute exactly the approved plan, metadata only |
| Network | **Live, and only here.** Requires `--live`, an enabled configuration, a valid identity, and a matching plan hash |
| Arguments | `--plan <path>`; `--window {M3.2A,M3.2B}`; `--live` (explicit, no default); `--ceiling <INT>` (must equal **that window's** approved ceiling); `--resume-from <receipt>` (recovery only); `--receipt-out <private-path>` |
| Stdout | Progress by route: planned, attempted, succeeded, classified, stored — then the totals |
| Stop behaviour | **Refuses the attempt that would exceed the ceiling**; halts aggregate traffic on `403` or unqualified `429`; fails closed on blocking schema drift |
| Side effects | Immutable raw objects; source observations; catalog rows inside their transaction; quarantine entries; one receipt |
| Exit codes | `0` complete · `1` configuration error · `2` usage · `3` stage not enabled · `4` gate failure (ceiling, drift, prohibited route, unclassified response) |
| Receipt | **Mandatory**, one per invocation, `invocation_mode = "live"` |

**Watch the running output for:** the request count against the budget, the route list staying inside
the allowlist, zero filing-body URLs, and the classification totals.

## 18a. Between the windows — freeze, derive, and obtain the second approval

**`PLANNED — NOT YET IMPLEMENTED (M3.2)`** · then **`MANUAL OWNER APPROVAL`**

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

**`PLANNED — NOT YET IMPLEMENTED (M3.2)`** · **`RECOVERY`**

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

**`PLANNED — NOT YET IMPLEMENTED (M3.1)`** · **`VERIFICATION`**

Receipts are written to the path given by `--receipt-out`, under the receipt storage policy in
[`execution_receipt_spec.md`](execution_receipt_spec.md) §7.

```
python -m disclosure_drift m3 show-receipt --receipt <relative-path>
```

**Intended interface contract:** read-only; renders the receipt's fields in a fixed order and
**fails closed** if any prohibited field is present. Exit `0` clean, `4` on a prohibited field.

## 23. Confirm actual request totals

**`PLANNED — NOT YET IMPLEMENTED (M3.2)`** · **`VERIFICATION`**

```
python -m disclosure_drift m3 reconcile-requests --plan <relative-path> --receipt <relative-path>
```

**Intended interface contract:** read-only; prints planned versus actual per route and in total, for
logical requests, physical attempts, response classifications, and raw objects; flags every
divergence. Exit `0` only when every divergence is accounted for by the plan's own rules.

Transcribe the result into [`templates/gate_h_checklist.md`](templates/gate_h_checklist.md), **per
window** — M3.2A and M3.2B are reconciled separately and integrated there.

**Stop if** actual exceeds planned anywhere the plan does not explain, if actual physical attempts
exceed a ceiling, if a run reaches equality with planned work unfinished, if a dependent request
appears in M3.2A, or if a bootstrap request appears in M3.2B. A complete run may lawfully finish
exactly at its ceiling.

## 24. Confirm no unresolved schema drift

**`PLANNED — NOT YET IMPLEMENTED (M3.2)`** · **`VERIFICATION`**

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

**`PLANNED — NOT YET IMPLEMENTED (M3.2)`** then **`AVAILABLE NOW`** to verify

Revert the configuration change from step 16, then verify. **Do this at the end of *each* window** —
after M3.2A before the derivation step 18a, and again after M3.2B before Gate H:

```bash
python -m disclosure_drift validate-sec-config | grep -E '^  network'
```

Expect `network            : disabled (safe default)`.

**Gate H does not pass while the network is still enabled**, and **the derivation in step 18a may not
begin while it is.** Record both verifications in the Gate H checklist.

## 27. Resume after an interrupted acquisition

**`PLANNED — NOT YET IMPLEMENTED (M3.1 read-only inspector; M3.2 repair/resume)`** · **`RECOVERY`**

Work through [`templates/interrupted_run_recovery.md`](templates/interrupted_run_recovery.md) **before**
resuming anything:

```
python -m disclosure_drift m3 recovery-state \
  --evidence-root <absolute-external-path> \
  --plan <relative-path> --receipt-chain-head <relative-path> \
  --catalog <relative-path> --data-root <relative-path>
```

**Intended interface contract:** read-only over the explicit plan, receipt-chain head, catalog, and
data-root inputs; reports the last successful receipt, the interruption point, database state,
raw-store state, partial-file state, the consumed request count, and a
**safe-resume determination** of `SAFE`, `UNSAFE`, or `UNDETERMINED`. It never adopts, quarantines,
rebuilds, reconciles, resumes, or calls `observation_catalog.reconcile()`. Exit `0` only for `SAFE`.
There is no `--run` shortcut and no repair flag.

On `UNSAFE`, stop. A separately authorized M3.2 repair command may apply the deterministic action;
then run `recovery-state` again and require `SAFE`. Inspection itself never repairs.

Resume only on `SAFE`:

```
python -m disclosure_drift m3 acquire --plan <relative-path> --live --ceiling <INT> \
  --resume-from <predecessor-receipt> --receipt-out <relative-path>
```

The resumed run carries the consumed count forward against the **same** approved ceiling and names its
predecessor receipt.

**On `UNDETERMINED`, stop.** Recovery uncertainty is a stop condition, not a judgement call.

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

## 29. Freeze the real snapshot only after Gate H

**`PLANNED — NOT YET IMPLEMENTED (M3.2)` → M3.3**

The snapshot-freeze command belongs to M3.3 and is documented in the M3.3 contract when it is
written. **Do not freeze a snapshot until all of:**

- [`templates/gate_h_checklist.md`](templates/gate_h_checklist.md) complete, every item `PASS`,
  owner-signed;
- `M3_2_METADATA_ACQUISITION_COMPLETE_GATE_H_PASSED` recorded;
- independent M3.2 review passed and `m3.2-complete` created;
- **network verified disabled again**;
- owner authorization to freeze a real candidate snapshot;
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
| `make check` | The full acceptance gate, in fixed order |
| `make fast` | Changed-file Ruff plus the mypy daemon; not a gate |
| `make sqlite-check` | Python and SQLite versions (floor 3.37) |
| `make secrets` | Secret scan over tracked and untracked-not-ignored text |
| `make hygiene` | No raw data, database, release artifact, or personal path tracked |
| `python -m disclosure_drift validate-config` | Configuration against the frozen definitions |
| `python -m disclosure_drift show-cohorts` | The frozen cohorts, maturity gates, and seed |
| `python -m disclosure_drift validate-sec-config` | SEC policy and identity — **identity validated, never displayed** |
| `python -m disclosure_drift sec --help` | The Milestone 2 SEC command group |
| `python -m disclosure_drift sec census --dry-run …` | The M2.2 census plan; **zero requests**; prints a census plan hash |

## Appendix B — commands planned but not implemented

**Every command in this table is `PLANNED — NOT YET IMPLEMENTED`. None of these exists. Do not type
them.**

| Planned command | Phase | Purpose |
|---|---|---|
| `m3 rehearse` | M3.1 | Run the **acquisition** rehearsal A1–A12, no socket |
| `m3 rehearse-report` | M3.1 | Render the acquisition-rehearsal evidence matrix |
| `m3 plan-requests` | M3.1 | The zero-request plan for one window, and its hash |
| `m3 derive-dependent-plan` | M3.2 | Derive the M3.2B plan from the frozen M3.2A objects; zero requests |
| `m3 show-budget` | M3.1 | Render the eight budget quantities and the ceiling |
| `m3 show-receipt` | M3.1 | Render a receipt, failing closed on a prohibited field |
| `m3 acquire --show-scope` | M3.2 | Print the exact network scope; zero requests |
| `m3 acquire --live` | M3.2 | Execute the approved plan, metadata only |
| `m3 reconcile-requests` | M3.2 | Planned versus actual, per route and total |
| `m3 show-drift` | M3.2 | Every drift event, blocking ones separated |
| `m3 recovery-state` | M3.1 (used by M3.2) | Read-only interruption state and safe-resume determination; never repairs |
| `m3 recover` | M3.2 | Apply a separately authorized deterministic repair before a fresh read-only inspection |

**Exit codes for every planned command follow the accepted convention:** `0` success, `1`
configuration error, `2` usage, `3` stage not enabled, `4` gate failure.

## Appendix C — the stop rule

There is one rule under all the others, and it is worth more than the rest of this document:

> **When something does not match what this runbook says it should be, stop and report it.**
> Do not adjust a threshold to make it pass. Do not delete the thing that failed. Do not re-run until
> it agrees. Do not proceed "just to see."

A stopped phase costs a day. A phase that proceeded past a mismatch costs the pilot.
