# Independent Review — M3.2 G1 Navigation and Workflow Repair

**Verdict:** `M3_2_G1_INDEPENDENT_REVIEW_PASS`
**Date:** 2026-08-06
**Authority for this review:** accepted
[Decision 043](../../Decisions/decision_043_m3_2_g1_navigation_workflow_repair_authorization.md)
§11, which makes a durable review artifact prospective from stage G1 and pilots the lifecycle here.
**This artifact is evidence, not authority.** It accepts nothing. G1 acceptance is a separate owner
act, and this record grants no implementation, network, schema, or stage authority.

---

## 1. Session independence

Single session, Claude Opus 5, high effort, fresh after `/clear` — this review packet was the first
substantive project instruction. No subagent, delegated or background agent, parallel session, Git
worktree, or dynamic workflow was invoked. This session authored none of: the G1 discovery report,
Decision 043, the Decision 043 governance recording, the G1 implementation candidate, or any G1
implementation change. It remained read-only over the repository until the verdict below was
substantively complete.

## 2. Candidate identity and repository state at review

| Fact | Value |
|---|---|
| Candidate commit | `7ac33d0abd9e05bf895b38270bde476317c974be` |
| Candidate tree | `a848320f1edd159f07b112f45790a229ec48827e` |
| Subject | `Repair M3.2 navigation and review workflow` |
| Parent | `c1fbece9242356b840787dd00ad46f15bb880133` (`Authorize M3.2 navigation and workflow repair`) |
| Branch | `main`, ahead 1 / behind 0 of `origin/main` |
| `origin/main` | `c1fbece9242356b840787dd00ad46f15bb880133` — candidate unpushed |
| Tags at candidate | none |
| Working tree | clean; nothing staged; zero non-ignored untracked paths |

Every expected-state condition in the review authorization held. No mismatch, and nothing was
repaired.

## 3. Scope — exactly the seven-path ceiling

The changed-path set was derived independently from Git, not from the completion report:

`Docs/architecture_map.md` (M) · `Docs/change_impact_map.md` (M) · `Docs/decision_index.md` (M) ·
`Docs/m3/review_execution_conventions.md` (A) · `Makefile` (M) · `Milestones/STATUS.md` (M) ·
`scripts/context_snapshot.sh` (M)

Seven paths, exactly the Decision 043 §6 ceiling, **no eighth**. `git diff --summary` shows one file
creation and no mode, symlink, rename, or type change.

**Empty-diff proof against every protected surface** (`git diff c1fbece…7ac33d0 -- <path>` empty):
`src/`, `tests/`, `configs/`, `.github/`, `src/disclosure_drift/storage/migrations/`,
`Milestones/contracts/`, `Docs/Decisions/` (all of 001–043, including the registry),
`Docs/m3/m3_2_t2_implementation_authorization_packet.md`, and `Docs/m3/reviews/`.

Migration chain remains exactly `0001`–`0013`; the receipt constant remains
`m3-execution-receipt/2.0`; both tracked switches in `configs/project.yaml` remain `false`; no
operational catalog, raw object, receipt, or evidence artifact exists (`data/` holds only
`README.md`). No private path, contact address, credential, or SEC identity appears anywhere in the
added lines.

## 4. Navigation review — decision index

Thirteen rows, **030 through 042, each exactly once, in ascending order**, with no Decision 043 row —
correct, since Decision 043 §5 authorized bringing navigation current *through* Decision 042. All
fourteen link targets in the new material resolve to real files.

Every row was checked against its source record rather than read for plausibility. **All thirteen
dates and all thirteen formal outcomes match the authoritative decision files exactly.** Substantive
spot-checks confirmed: 030's proven non-substantive redaction leaving the §17 verdict unchanged;
031's owner-approved ceiling **801**; 033's restoration of this very file to its `3fbaa12d…` bytes
and its "needs its own path authorization" ruling — which Decision 043 §5 supplies; 035's fifteen-path
maximum and contract §22 T2.1–T2.6 amendment; 037's T2.5–T2.6 implementation-freeze candidate; 038's
two paths bound to candidate `6b189df1…` and added to no later stage; 040's four subphases, single
reason code, and both `NO_*_REQUIRED` determinations; 041's eight→ten envelope and two named
primitives; 042's disclosure that no T2.4 rereview artifact exists.

No authority is created. The section states the rows are "pointers only", routes existence and
approval status to `decision_registry.md` and live state to `Milestones/STATUS.md`, and the
"which record controls what" paragraph correctly separates *authorizing* from *accepting* decisions.
The table form matches the file's existing convention (222 table rows before the change).

One pre-existing correction was also made in place: the Decision 029 paragraph's "no durable §17
review artifact exists" is now scoped to the state when written. That is accurate —
`Docs/m3/reviews/m3_1_section_17_review_970e050d…md` exists and M3.1 is accepted by Decision 031.

## 5. Navigation review — change-impact map

The new M3.2 T2 section maps only accepted T2 work. Every production path, every "nearest test", and
every prohibited-path row was confirmed to exist. The stated gates are real: `make sqlite-check` is
an existing target, and `tests/unit/test_migration_provenance.py` exists and is correctly invoked for
the two surfaces that touch FK-constrained reason codes (`reference_reason_codes` is a real table
family across migrations `0001`, `0002`, `0009`, `0012`).

Nothing unrelated is represented as governed: `census_orchestrator.py` and `index_retrieval.py` are
correctly described as declined-and-prohibited Milestone 2 surfaces, and `recovery.py`,
`request_plan.py`, `receipt.py`, `request_ceiling.py`, `rehearsal.py`, and `evidence_paths.py` are
correctly listed as governed-but-unmodified. Nothing material to a T2.5 or T3 review is omitted. The
section opens by declaring itself navigation that "authorizes no edit", and routes envelope questions
to the authorizing decisions rather than to itself.

## 6. Navigation review — architecture map

The new §10 and the corrected Milestone 3 rows were checked against production code, not accepted on
description. Verified directly in source: `m3/recovery.py` imports no writer and sets
`PRAGMA query_only`; `sec/request_ceiling.py` documents and implements refusal **before** the attempt
that would exceed the ceiling; `m3/acquisition.py` refuses without an explicit
`LiveOperationAuthorization` "that no configuration key, contract acceptance, gate token, or ceiling
value can synthesize"; `storage/catalog.py` is documented as "the single logical catalog writer";
`ObservationRecorder.record` takes `members: Iterable[ArchiveMember]`; `open_recovery_state` and
`resolve_recovery_state` exist and are the only two additions; `reasons.py` carries exactly
`SOURCE_REQUIRED_OBJECT_UNAVAILABLE`; `RECOVERY_ACTIONS` and `apply_recovery_action` have **no CLI
reference**, matching the "no CLI exposure" claim; `EXIT_STAGE_NOT_ENABLED = 3` supports the
fail-closed exit-3 description, which `tests/integration/test_m3_cli.py` asserts.

Ownership, dependency direction, and interaction edges are stated correctly — §10 consumes the
Milestone 2 storage and observation layers rather than extending them, and says so. No obsolete
module name appears. No architectural claim exceeds what code and accepted decisions support, and
nothing is redesigned or refactored.

## 7. STATUS and historical preservation

**No structural rewrite.** The full heading structure of `Milestones/STATUS.md` is byte-identical
between parent and candidate; the file grows by 29 lines.

**Marker compression, with nothing lost.** `CURRENT_STAGE` 9,299 → 210 bytes; `ACTIVE_BLOCKER`
3,653 → 207; `IMPLEMENTATION_AUTHORIZATION` 3,039 → 253. These are now markers rather than embedded
reports. Preservation was tested exhaustively rather than assumed: **every one of the 17 distinct
commit/tree/artifact hashes** appearing in the three old values is still present in the candidate
file, and **every ALL-CAPS token in them survives — zero absent**. The six Decision 040 §19 open
obligations (RawStore resource limitation; progress-sink sanitization; F4 by T4; D023-O1 as a latent
fail-closed referral; operator wiring and receipt assembly at T2.5–T2.6; overall T3 acceptance) are
preserved in the narrative and in `DECISION_042_STATUS`. Counts `3053`, `333`, `18/18`, `126`, and
ceiling `801` all survive. **No unique audit-relevant fact was deleted to reach a byte target.**

**Marker integrity.** `CURRENT_STAGE`, `ACTIVE_BLOCKER`, `IMPLEMENTATION_AUTHORIZATION`,
`ACTIVE_STAGE_CONTRACT`, and `NEXT_AUTHORIZED_ACTION` each occur **exactly once** line-anchored. The
required current marker
`NEXT_AUTHORIZED_ACTION: CHATGPT_OWNER_M3_2_G1_FRESH_INDEPENDENT_REVIEW_AUTHORIZATION`
appears exactly once and carries no suffix.

**Both intended corrections are made and independently corroborated.**
(1) The accepted T2.4 single skip is now described as the fixed-literal skip in
`tests/unit/test_m23_pilot_manifest.py`. Confirmed at source — line 429 raises
`pytest.skip("snapshot_state is a fixed literal asserted before hashing")` — and by an independent
targeted run of that file together with `tests/unit/test_httpx_transport.py`: **280 passed, 1
skipped**, the skip being exactly that line, with the entire transport suite executing. CI's
dedicated "Transport suite must execute, not skip" step exists as described. Decision 042 is not
edited and its wording stands as historical.
(2) The active-contract prose now correctly states that `ACTIVE_STAGE_CONTRACT` names
`Milestones/contracts/m3_2.md`.

**Authority state is correct:** G1 is recorded as an unaccepted, local, untagged, unpushed candidate;
T2.5–T2.6 remains owner-gated, unauthorized, and not begun; both network switches remain `false`.

**The historical Milestone-2 `[sec]`-skip sentence was correctly left untouched.** Decision 043 §8
and §12 scope the skip correction to the accepted T2.4 run and preserve historical narrative; that
statement was not re-adjudicated. It is also *factually correct for its era*: the fixed-literal skip
was introduced on 2026-07-31 (commit `5c53412`), **after** the 2026-07-29 S5.1–S5.3 and 2026-07-30
S5.4 acceptances it describes, so the single skip in those runs was indeed the `[sec]` module skip.
It anchors to dated stages and counts (1661/1, 1899/1) that cannot be confused with the current
3053/1, so it creates no current operational or navigation ambiguity. **No finding.**

## 8. Context snapshot — correctness

All pre-existing fields are retained. Each required addition was verified against Git independently:
HEAD tree, HEAD parent(s) (via `rev-list --parents`, so a merge reports both and a root commit
reports none), ahead/behind against the *recorded* remote ref with no remote contact, and both
tracked network switches.

**Marker parser.** Differential fixture testing outside the repository, against the old `grep`/`sed`
implementation, confirms: single-line markers behave **identically** to before; legitimately indented
continuation lines are joined **completely**; and parsing stops at the first non-continuation — a
blank line, unindented prose, a fence, or a following `KEY:` marker, whether indented or not. On the
real ledger, all four consumed markers return byte-identical values old-vs-new (they are
single-line). On the accepted M3.2 contract the fix does real work: the `STATUS:` value grows from a
truncated 81 characters to its complete 188. A missing marker or missing file yields the empty
string, which callers render as an explicit "(marker … not found)" — the pre-existing fail-closed
behavior, unchanged.

**Config reader.** `yaml_block_value` is correctly scoped to the named top-level block: given a
fixture with `enabled:` keys in a preceding and a following block, it returns only the `network`
value, strips trailing comments, and returns empty for a missing key, block, or file. It reads only
tracked `configs/project.yaml`, states that it reads tracked values only, and correctly states that
neither switch is itself authorization. No frozen contract hash, packet digest, receipt version, or
input manifest was added.

## 9. Context snapshot — determinism and size

Measured in disposable clones outside the repository, with the sole path-dependent field
(repository root) normalised; the normalisation was validated exactly — the clone-vs-primary byte
delta equalled the path-length delta of 81 to the byte.

| State | Bare script | `make context` |
|---|---|---|
| `59374d7` pre-G1 discovery baseline, clean | 13,568 | — |
| `c1fbece` published parent, clean | **14,579** | 14,609 |
| `7ac33d0` candidate, **pre-commit** working tree | 2,795 | — |
| `7ac33d0` candidate, **committed and clean** | **2,654** | 2,684 |

1. **14,579 reproduces exactly** on the published parent.
2. **2,795 does not reproduce on the committed candidate.** It reproduces *precisely* — to the byte —
   only with the seven paths present but uncommitted, i.e. a pre-commit measurement. The committed
   candidate is **2,654** bytes.
3. **14,724 is not reproducible on any clean commit in this lineage.** It is consistent with a
   measurement taken over a non-clean working tree, since the working-tree status block is the only
   size-varying element; it is an observation artifact, not tool behavior. No defect is drawn from
   it.
4. **Dynamic fields do not vary between equivalent clean runs.** Three consecutive candidate runs and
   two parent runs were byte-identical. The output contains no timestamp, duration, or random value;
   it is a pure function of commit, refs, and working-tree state — which is exactly what a state
   snapshot must be.
5. **Deterministic enough for repeated review use.** A clean checkout at a fixed SHA yields identical
   bytes every time; variation only ever reflects real working-tree change, which is the tool's
   purpose.

**Reduction from the reproducible parent baseline: 14,579 → 2,654 bytes = 11,925 bytes removed,
81.8%.** The candidate output is 2.59 KiB, inside Decision 043 §8's ~4 KiB goal (a goal, not a
criterion).

## 10. Stage gate

`make -n stage-gate` prints exactly `make check`, then `make sqlite-check`, then `make context`.
Behavior was then exercised against a mock replicating the recipe verbatim, so no repository code was
broken to test failure paths:

- **Normal invocation:** the three gates execute in the required order.
- **`make -j8`:** the same order. Recursive sub-makes as *recipe lines* — not prerequisites — is the
  correct construction; declared prerequisites could be satisfied concurrently and lose the ordering
  Decision 043 §9 fixes.
- **Fail-closed:** a failing `check` stops the recipe before `sqlite-check` and `context` run, and
  `stage-gate` exits non-zero; a failing `sqlite-check` likewise stops before `context`. Confirmed
  under both normal and `-j8` invocation.

The `check`, `sqlite-check`, and `context` recipes are **byte-unchanged** from the parent, verified by
hashing each extracted target. `stage-gate` presents itself as a convenience and states in its own
comments that the contract and decision records remain the authority — no false elevation.

## 11. Review-execution conventions

`Docs/m3/review_execution_conventions.md` is concise (129 lines) and opens by declaring that it grants
no stage, implementation, schema, network, or live-operation authority and that accepted Decisions,
contracts, and packets control on conflict. It accurately covers every Decision 043 §10 item: session
preflight and the six declared fields; the default **STOP** on a material role/model/freshness/
independence mismatch with disclose-and-continue reserved to expressly permitted read-only discovery;
authority / execution / evidence separation with the five things a packet must still state
explicitly; packet and report compression as a default that never licenses omitting required
evidence; the reviewer-owned isolated environment with mandatory teardown **and** explicit teardown
verification; the independence boundary that keeps candidate-specific oracles and expected-result
generators out of the repository; mutation hygiene including `PYTHONDONTWRITEBYTECODE=1`,
`__pycache__` purging, proof of behavioural effect, the exact
`KILLED` / `SURVIVED_EFFECTIVE` / `SURVIVED_NO_OP` vocabulary, and restoration proved by hash *and*
clean diff; validation tiers with one normal boundary run; the durable review lifecycle; and the
prospective-only rule that historical gaps stay gaps and are never reconstructed or back-dated. No
wording converts a default into new substantive authority.

## 12. Boundary validation

One normal `make stage-gate` was run on the exact candidate. **Exit 0.** The three gates appear in
the log in the required order. Ruff check, ruff format check, and `mypy src` (76 source files) clean;
secret scan clean; repository hygiene 285 paths / 0 findings; config validation, cohort print, and
SEC help all clean; `sqlite-check` and `context` both ran.

**Full suite: 3053 passed, 1 skipped** — independently established, matching the expected historical
count. The single skip is `tests/unit/test_m23_pilot_manifest.py:429`, confirmed by targeted run. No
network access, SEC identity use, connectivity probe, operational catalog, or live operation occurred
at any point in this review. The working tree was clean and free of non-ignored untracked paths
before and after the gate.

## 13. Repeated stage-gate disclosure (F2)

The implementer disclosed running `stage-gate` twice because evidence from the first valid run was
not captured. Repository evidence supports treating this as process inefficiency only. The reflog
records the candidate created **once**, at 2026-08-06 23:03:46, as a plain `commit:` entry with **no
amend, reset, or rebase after it** — and the same reflog does record `commit (amend)` and `reset`
entries for earlier stages, so their absence here is meaningful. Exactly one commit exists after
`c1fbece`, and the working tree is byte-identical to the committed tree, leaving no residue. An
intervening edit would therefore have had to be either committed (impossible) or reverted to exactly
the committed bytes. My own independent gate on those bytes reproduces the reported result. Scope
statement: this rests on repository evidence and independent reproduction, not on direct observation
of the implementer's shell. **No further correction required.**

## 14. Findings

**BLOCKER: 0. MAJOR: 0. MINOR: 1. OPTIMIZATION: 2.**

**MINOR-1 — the reported candidate context size does not describe the committed candidate.** The
implementation packet reports 2,795 bytes. That figure reproduces only in the pre-commit working
state; the committed candidate produces **2,654** bytes (bare script) or **2,684** (`make context`).
No repository byte asserts any size, so nothing in the tree is wrong, and the actual result is
*better* than reported. It is recorded because a later acceptance record that binds 2,795 would
durably fix a figure that does not reproduce. **Correction:** bind 14,579 → 2,654 bytes, 81.8%
reduction. No repository change is needed and none was made.

**OPTIMIZATION-1.** `review_execution_conventions.md` §4 says a review is "never … conducted in the
primary checkout", which reads absolutely in a document that declares itself a set of defaults; this
review's own packet correctly directed the boundary gate to the primary checkout. A future authorized
edit could phrase it as the default it is.

**OPTIMIZATION-2.** The accepted M3.2 contract's own `STATUS:` marker — now reported in full because
the parser fix works — reads as of Decision 037 and predates accepted T2.2–T2.4. The contract is a
prohibited path for G1 and leaving it untouched was **correct**; the ledger carries live stage state.
A future authorized contract-status refresh would remove the residual staleness a reader sees in
`make context`.

## 15. Verdict

```text
M3_2_G1_INDEPENDENT_REVIEW_PASS
```

The candidate performs exactly the work Decision 043 authorized, inside the seven-path ceiling and
with no eighth path. Every navigation entry is materially faithful to its authoritative source. The
status ledger is compressed without losing a single audit-relevant fact and without structural
rewrite. The context tool is correct, bounded, deterministic, and 81.8% smaller. The stage gate
reproduces the accepted sequence and fails closed. The conventions document creates no authority. No
production, test, configuration, migration, schema, receipt, reason-code, or network byte changed, and
no live operation occurred.

**This artifact accepts nothing.** G1 remains unaccepted; T2.5–T2.6 remains owner-gated, unauthorized,
and not begun; network enablement, live SEC access, real operational-catalog creation, receipt
emission, and use of the 801 ceiling all remain unauthorized. G1 acceptance and T2.5 implementation
authorization remain separate owner judgments.

## 16. Reviewer environment and teardown

Analysis used disposable clones and mock Makefiles created outside the repository, at explicit SHAs,
with scratch data written only outside the checkout. Both were removed at the end of the review and
their removal was verified, together with the primary checkout remaining clean at `7ac33d0` with zero
non-ignored untracked paths. No repo-owned audit oracle, scenario harness, or candidate-specific
helper was created.
