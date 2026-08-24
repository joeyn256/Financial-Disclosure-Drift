# Decision 147 — The Decision 146 Code-Continuity and Pre-Canary Finding Correction

```text
STATUS: PUBLISHED — CORRECTION RECORD, ALL D146 FINDINGS CLOSED OR EXPLICITLY DISPOSED
RECORD_TYPE: CORRECTION OF A FAILED INDEPENDENT REVIEW — SOURCE, TEST AND GOVERNANCE
DATE: 2026-08-24
OWNER: Joey authorization; correction performed by Claude Opus 5 at maximum effort
CLASSIFICATION: MECHANISM CORRECTION — A FALSE MECHANICAL CLAIM MADE TRUE, NOT NARROWED
AUTHORIZATION:
  M3_3_D147_D146_FINDING_CORRECTION_AUTHORIZED — spent by the publication of this record
OWNER_ADJUDICATION_CONSUMED:
  M3_3_D146_OWNER_ADJUDICATED_D147_CORRECTION_AUTHORIZED
ACCEPTED_REVIEW_BASELINE: D146_FINAL_INDEPENDENT_POST_D145_PRECANARY_REVIEW_FAIL

D146_PUBLICATION_HEAD: bf3acfe8080d94f5b4f41ccf231a2593da3f4309
D146_PUBLICATION_TREE: 12ef771c66d1a40889040b5a4a29dedf6133832b
D146_REVIEWED_HEAD:    69a73d99a2aa5aafeb905d3fcfd40dba6f88e68d
D146_REVIEWED_TREE:    1ab21d76913e367d972b024c5c1fb006160d52b6
D146_CI_RUN:           32686414965 — SUCCESS, both mandatory jobs

FINDINGS_CONSUMED: 0 BLOCKER / 1 MAJOR / 2 MINOR / 7 OBSERVATION
FINDINGS_CLOSED:   1 MAJOR / 2 MINOR — none omitted, none deferred, none narrowed away
OBSERVATIONS:      7 of 7 explicitly disposed — 6 ACCEPTED as recorded, 1 CLOSED with MINOR-2

REPOSITORY_CODE_IDENTITY: IMPLEMENTED — git HEAD commit + git HEAD tree, derived, never declared
CLEAN_TREE_CONTRACT: IMPLEMENTED — dirty tracked paths and untracked non-ignored paths both refuse
PHASE_RESTART_CONTRACT: m3.3-canary-phase-restart/1 -> /2

MAJOR_PHASES: F0, F1, F2 — UNCHANGED
QUALIFIED_MAJOR_RESTART_BOUNDARIES: 2 of 2 — F0->F1, F1->F2 — UNCHANGED
PHASE_BOUNDARY_RAM_RECLAMATION: IMPLEMENTED — UNCHANGED
GOVERNED_PAUSE_RESUME: NOT_IMPLEMENTED — UNCHANGED
SAFE_TO_EJECT: NOT_IMPLEMENTED — UNCHANGED

PARSE_BULK_REACHABILITY: PROVABLY CANARY-UNREACHABLE — UNCHANGED, UNREPAIRED
CANARY_AUTHORIZED: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_HEAD: 0015 — 0016 ABSENT
ALL_THREE_ACTIVATION_CONSTANTS: None
NETWORK: enabled=false, m3_acquire_enabled=false
```

## 1. What this record is, and what it is not

It is the **correction of every finding**
[Decision 146](decision_146_m3_3_final_independent_post_d145_precanary_review.md) recorded against
the frozen Decision 145 tree, performed under the owner's adjudication of those findings and in a
session that did not write either record.

**The owner sustained `D146-MAJOR-1` and chose the harder of the two remedies.** Decision 146 offered
the owner a choice: *bind a genuine semantic code identity*, or *narrow Decision 145 §12's claim to
what its digest actually does*. The owner chose the first, in terms:

> Implement genuine mechanical repository continuity. … Do **NOT** merely weaken Decision 145's claim.

So Decision 145 §12's sentence — that the mechanism prevents, *mechanically*, "a process continuing
from a revision whose governing semantics moved" — **is now true of the implementation**, rather than
being edited until it was true of a weaker one. That is the whole of this record's ambition, and the
reason it touches source at all.

**What it is not.** It is not a canary authorization, a canary world, an execution namespace, a
launch receipt, an E0 authorization, a network enablement, a migration, or an architecture
expansion. It creates no physical-detach right, no pause/resume, and no new capacity threshold. It
does not rewrite [Decision 145](decision_145_m3_3_governed_major_phase_restart.md), it does not
rewrite [Decision 146](decision_146_m3_3_final_independent_post_d145_precanary_review.md), and it
does not rewrite [Decision 126](decision_126_m3_3_complete_first_source_final_preflight.md).
**`CANARY_AUTHORIZED` remains `NO`.**

## 2. Entry state

Verified live before anything was read for the purpose of changing it:

```text
branch      main
HEAD        bf3acfe8080d94f5b4f41ccf231a2593da3f4309
tree        12ef771c66d1a40889040b5a4a29dedf6133832b
origin/main bf3acfe8080d94f5b4f41ccf231a2593da3f4309   (equal; 0 ahead / 0 behind)
worktree    clean — nothing staged, nothing untracked
tag at HEAD none

CI run      32686414965 @ bf3acfe — conclusion SUCCESS
            "SEC-enabled environment ([dev,sec]) — required"  success
            "Core environment (no [sec] extra)"               success

migration head 0015; 0016 absent
PRE_E0_CATALOG_TRANSITION_AUTHORITY   None
M3_3_E0_EXECUTION_AUTHORITY           None
STALE_WRITER_LEASE_RECOVERY_AUTHORITY None
network.enabled = false; network.m3_acquire_enabled = false
canary_authorized = false
```

Every material predicate matched the authorization's expected baseline. Nothing was repaired or
reinterpreted to make it match.

## 3. `D146-MAJOR-1` — what was wrong, restated exactly

`phase_execution_identity()` folded ten frozen constants plus `disclosure_drift.__version__`. That
version string is the literal `"0.1.0"` and has been touched by exactly one commit in the entire
history — `fa16668`, the Milestone 1 foundation. Decision 146 proved the consequence by mutation
rather than arguing it: with the accepted `POST_F0` capacity floor relaxed `60 -> 1` GiB **and** the
admission-side predecessor-status guard deleted outright, the digest was **bit-identical** at
`ef0b492c03ccd5b154eca8c0c3cd27463cab0686ac69b34a89b0fc66a339a69b`. An exhaustive search of `src/`
found no git SHA, no source digest and no build identity anywhere.

**The digest was sound for the constants it bound. The claim drawn from it was not.** A successor
process could continue a predecessor's checkpoint under source that had changed arbitrarily, and
nothing in the repository would notice.

## 4. `D147-R1` — the repository code identity

**BINDING.** A canary phase derives, in its own process, the identity of the Git repository its
running source was imported from, and folds it into the execution identity a successor is admitted
against.

The mechanism is `src/disclosure_drift/m3/repository_identity.py`, a new module of its own for the
same reason `canary_runtime.py` is one: it asks the host a question — *which source is this?* — that
is neither a phase contract, nor a volume, nor a parse. It carries its own contract identity,
`m3.3-canary-repository-identity/1`.

```text
RepositoryIdentity
  contract              m3.3-canary-repository-identity/1
  head_sha              git rev-parse HEAD          — the HISTORY identity
  tree_sha              git rev-parse HEAD^{tree}   — the CONTENT identity
  dirty_tracked_paths   git status --porcelain=v1 --untracked-files=no
  untracked_paths       git ls-files --others --exclude-standard
```

**Both `head_sha` and `tree_sha`, because they answer different questions.** Two commits can carry
the same tree — an amend that changed only a message, a rebase that moved a parent — so a tree
comparison alone would admit a history that moved, and a commit comparison alone would refuse a
continuation whose content is byte-identical without being able to say so. Decision 147 records
both, compares both, and can name both in a refusal.

**Four properties make it a measurement rather than a declaration.**

1. **Derived from the executing source, not from the working directory.** The repository is found by
   asking Git to walk upward from *this module's own file* — the rule
   `_package_repository_root()` already used. The current working directory is never read: a phase is
   launched from wherever the operator happens to be standing, and that is not evidence about which
   code is running.
2. **The repository is authenticated, not merely found.** Git walks upward, so an installed copy of
   the package sitting inside some unrelated repository would otherwise yield that repository's
   identity — a *real* identity of the *wrong* code. `canary_phases.py` and `single_source_canary.py`
   must be **tracked files** of the repository that was found, checked with
   `git ls-files --error-unmatch`. `repository_identity.py` itself is deliberately not in that list:
   including it would authenticate nothing further, and an uncommitted copy of it is already refused
   by the clean-tree contract in §5.
3. **No operator-supplied SHA, on any surface.** Neither `run_single_source_canary_phase` nor
   `run_canary_source_command` takes a repository revision parameter, the CLI defines no such flag,
   and no environment variable is consulted. A declared identity would make the continuity contract a
   statement of intent; this makes it a measurement.
4. **Every Git invocation is a read.** The module can issue exactly three subcommands —
   `rev-parse`, `status`, `ls-files` — and that is proved from its own AST rather than promised in a
   docstring. It never checks out, stashes, resets, cleans, fetches or pulls, on any path.

## 5. `D147-R2` — the clean-tree contract, and the untracked rule stated explicitly

**BINDING.** A phase refuses to begin if the repository it is executing from has an ambiguous
working tree. Ambiguity is two things, kept separate because they are different failures:

* a **modified tracked path** — the running implementation may differ from the `tree_sha` the
  checkpoint is about to record, which would make the record worth nothing;
* an **untracked, non-ignored path** — a file no commit describes, which can sit anywhere on the
  import path and therefore change what executes.

**Ignored paths are not ambiguity, and that is a decision rather than an oversight.** `__pycache__`
exists the moment the package is imported; a virtual environment and a build directory exist in every
working checkout. The repository's own **tracked** `.gitignore` is what declares those paths
irrelevant, and a contract that refused them could never admit anything. The boundary is therefore
exactly this: *what the repository has committed a policy about is governed by that policy; what it
has said nothing about is refused.* The test suite proves both halves — an ignored `.pyc` leaves a
tree clean, and an untracked `src/disclosure_drift/m3/extra.py` does not.

**A refusal here is terminal, and is not a resumable pause.** Nothing is checked out, stashed, reset,
fetched, cleaned or repaired; no world is created; control returns to the operator with the exact
ambiguity named, repository-relative and bounded. The same is true of a refusal for a *changed*
identity at a phase boundary.

**Where the gate runs.** First, before the work root, the volume, the dock, the power state or the
host lock — because a process that cannot say which revision it is has no business touching the
operator's hardware, and because a refusal there costs nothing and reaches nothing.

## 6. `D147-R3` — execution identity binds both halves

**BINDING.** `phase_execution_identity()` folds the declared execution contract **and** the
repository code identity. Neither replaces the other: the repository identity is the backstop that
catches *any* source change, and the declared inputs are what let a reader see which policy values a
continuation is actually protected against — which is what a bare content hash cannot say.

The complete fold, **seventeen** inputs — counted from the source rather than by hand, and pinned
by a test so this number cannot drift the way `D146-MINOR-1`'s did:

| Input | What it is |
| --- | --- |
| `canary_contract`, `restart_contract`, `evidence_contract` | the three contract identities |
| `resolution_scope` | the accepted Decision 012 resolution scope |
| `required_transport`, `qualified_volume_uuid` | the D144-R1 narrowing and the D140-R2 volume |
| `batch_size` | when rows become durable |
| `launch_minimum_free_bytes` | F0 admission floor |
| `post_f0_minimum_free_bytes` | **added** — the post-F0 invariant |
| `pre_f1_minimum_free_bytes` | F1 admission floor |
| `pre_f2_minimum_free_bytes` | F2 admission floor |
| `f2_alert_free_bytes` | **added** — the continuous F2 alert |
| `f2_hard_floor_free_bytes` | **added** — the continuous F2 hard stop |
| `package_version` | the declared build version, kept |
| `repository_identity_contract` | **added** — how the code identity was derived |
| `repository_head_sha` | **added** — the commit the code is running from |
| `repository_tree_sha` | **added** — the content that commit names |

`cache_bytes` remains deliberately absent: accepted
[Decision 119](decision_119_m3_3_cache_bound_persistence_and_prefix_diagnostic.md) proves the page-cache
budget moves no row, no ordering, no digest and no identity, so folding it would refuse continuations
that are provably fine. That exclusion is itself tested, so the widened fold did not sweep it up.

## 7. `D147-R4` — the checkpoint records the identity, and the successor recomputes it

**BINDING.** `PhaseCheckpoint` carries `repository_head_sha` and `repository_tree_sha` as **named
fields**, and `require_phase_admission` compares them **field by field** in addition to comparing the
aggregate digest.

The redundancy is the point. A digest of seventeen inputs refuses correctly and explains nothing; a
refusal that cannot be diagnosed sends an operator looking in the wrong place. The named comparisons
therefore run **first** and the aggregate digest **last**, so a moved revision reports the moved
revision:

```text
the repository_head_sha this process would continue under does not match the one phase 'f0'
recorded at its terminal: expected <A>, observed <B>. … The run is refused and nothing was
started, nothing was checked out or repaired, and this is not a resumable pause
```

**Each phase recomputes, in its own process, from its own source.** F0 records the identity it ran
under; F1 derives it again and refuses if it moved; F2 does the same. No successor reads the
predecessor's recorded identity as its own — that is mutation `M5`/`M6` in §12, and both are killed.

**`PHASE_RESTART_CONTRACT` moves `m3.3-canary-phase-restart/1 -> /2`.** A version-1 checkpoint
describes a phase that ran without recording which revision it ran, which is exactly the state a
version-2 successor must not continue from. The bump makes that refusal mechanical rather than a
missing-field accident — and both refusals are tested. **No real canary world exists, so no
checkpoint anywhere is invalidated by this.**

## 8. `D146-MINOR-1` — the capacity policy inventory

Decision 145 §12 said the digest folded "the **four** capacity floors"; it folded **three**. The
owner instructed that the inventory be re-derived independently rather than the count edited, and
that a value which can materially alter governed phase behaviour be bound unless there is a concrete
reason not to. The complete inventory of execution-governing capacity values on the F0/F1/F2 path:

| Constant | Value | Kind | Folded |
| --- | --- | --- | --- |
| `LAUNCH_MINIMUM_FREE_BYTES` | 185 GiB | **admission floor** — F0 | yes (already) |
| `POST_F0_MINIMUM_FREE_BYTES` | 60 GiB | **post-phase invariant** — hard, stop-and-report (D138-R5) | **yes, added** |
| `PRE_F1_MINIMUM_FREE_BYTES` | 55 GiB | **admission floor** — F1, re-enforced at the boundary | yes (already) |
| `PRE_F2_MINIMUM_FREE_BYTES` | 50 GiB | **admission floor** — F2, re-enforced inside the F2 process | yes (already) |
| `F2_ALERT_FREE_BYTES` | 20 GiB | **continuous warning** — decides the state a capacity observation reports | **yes, added** |
| `F2_HARD_FLOOR_FREE_BYTES` | 10 GiB | **continuous hard predicate** — rolls F2's single transaction back | **yes, added** |
| `PHASE_MINIMUM_FREE_BYTES` | mapping | a derived label→floor mapping; every value in it is folded by name | n/a |
| `WORKING_CATALOG_CACHE_BYTES` | 512 MiB | execution parameter, **provably evidence-neutral** (D119) | **no, deliberately** |

**Six, named individually rather than counted.** `F2_ALERT` is a report rather than a stop, and was
folded anyway: it decides the state token a capacity observation carries into the checkpoint payload
and the run's result document, which is governed output. **No value was invented and no accepted
value was changed** — every number above is the already-accepted one at its already-accepted meaning.

The inventory is **mechanical, not prose**: a test enumerates every `*_FREE_BYTES` and
`*_CACHE_BYTES` name declared by `external_working_root` and `single_source_canary` and fails unless
each is either folded or explicitly excluded with a recorded reason. A seventh capacity constant
added later cannot silently escape the execution contract.

## 9. `D146-MINOR-2` and `D146-OBS-5` — the Decision 126 rationale, historical versus binding

The `PRE_F2_MINIMUM_FREE_BYTES` docstring restated, in the present tense, two
[Decision 126](decision_126_m3_3_complete_first_source_final_preflight.md) §7 rationale sentences
that Decision 145 had made false. Decision 146 named one as `MINOR-2` and the other as `OBS-5`;
**both are corrected together**, and the docstring now separates the two kinds of statement
explicitly.

**Marked HISTORICAL — true of the pre-Decision-145 whole-run shape, and no longer true of the phased
one:**

1. *"F1 returns and F2 begins in consecutive statements, so there is no window an outside process
   can occupy"* — on the phased path there **is** a window: F1's process exits and F2's starts.
2. *"Nothing durable changes at the boundary, so an observer cannot tell 'F1 finished' from 'F2 is
   about to open' by reading state"* — F1 now writes a durable terminal checkpoint, and reading it is
   exactly how a successor tells those two states apart.

Both remain true of the surviving whole-run path, and the docstring says so.

**Marked CURRENT AND BINDING — the two reasons that carry `D126-R6`, untouched:** a signal from
outside is advisory where admission has to be dispositive; and free space sampled at any instant
before the call describes a different instant than the one that matters. **Only the path that is
about to open the transaction can decline to open it.**

**`D126-R6` is honoured, and nothing about the gate moved.** The dispositive pre-F2 check runs in the
F2 **process**, inside F2's own `write_containment`, one statement before `_f2` — proved from the
module's AST rather than from the docstring that describes it. The `50` GiB value, the strict
comparison, and the whole-run call site are unchanged. **Decision 126 itself is not rewritten**: it
recorded what was true of the shape it governed, and its requirement stands.

## 10. Observation dispositions — all seven

| ID | Disposition | Basis |
| --- | --- | --- |
| `D146-OBS-1` | **ACCEPTED THREAT-MODEL LIMITATION** — no contradiction with a binding contract found | No digest of the working-catalog **file** is recorded or compared at attach; what is enforced is the migration chain, via `_verify_attached`, which refuses before admission is reached. Substituting a file requires write access inside the disposable world, and an actor with it can equally rewrite the ledger and the checkpoint. The boundary is now **asserted** rather than assumed: a test proves `attach_world` calls no digest and that `PhaseCheckpoint` carries no working-catalog digest field. The threat model was **not** widened |
| `D146-OBS-2` | **ACCEPTED IMPLEMENTATION-SHAPE LIMITATION** — non-exploitable, not redesigned | Checkpoint create-once is a lock-serialized read-then-write rather than an `O_EXCL` create. The host execution lock is acquired in `run_single_source_canary_phase` before any phase work and released only when the process leaves it, so a second canary process on this host cannot begin a phase at all and can never reach the window. Tested: a held lock refuses a phase and leaves no world |
| `D146-OBS-3` | **CLOSED with a focused test; no architecture change** | `migration_head` is compared in `require_phase_admission` but `_verify_attached` refuses a moved chain first, making the admission comparison defensive. The review's reading is correct; what was missing was a test that the defensive comparison is real. One was added, against the primitive directly, because the production path cannot reach it |
| `D146-OBS-4` | **ACCEPTED DEFENSIVE REDUNDANCY — kept** | The admission-side predecessor-status guard is unreachable, disclosed by Decision 145 §19 and confirmed by mutation in Decision 146. It is **not** deleted: a status the write-side guard already refuses is exactly what a future write path could stop refusing, and removing a reader's check to improve a mutation score trades an invariant for a number. A test now pins both guards in place |
| `D146-OBS-5` | **CLOSED together with `MINOR-2`** | See §9. Both now-false rationale sentences are marked historical in the source; the historical Decision 126 artifact is **not** rewritten |
| `D146-OBS-6` | **CARRIED FORWARD as a future authorization boundary** | `--mode run` remains reachable and is **not** removed by this record. Mode selection stays a governance boundary; §11 states the constraint the future authorization must carry, unchanged from Decision 146 §9 |
| `D146-OBS-7` | **ACCEPTED FAIL-CLOSED LIMITATION — correction refused, with evidence** | `process_is_live_canary` does not authenticate `argv[0]`, unlike `authenticate_canary_process`, so a decoy command line reads as *alive* and produces a spurious **refusal**. The owner's escape clause required that any correction "clearly cannot weaken process authentication"; **it demonstrably would.** The two helpers answer questions whose safe directions are opposite: authentication decides whether to **signal**, where permissiveness signals the wrong process, so it must be strict; this decides whether a predecessor is **gone**, where `True` refuses a successor and `False` admits one — so an `argv[0]` condition would make `True` harder to reach and could admit a successor while its predecessor was still writing the working catalog. That is the dangerous direction. The asymmetry is **correct**, and a test now pins it so a future "fix" fails rather than lands |

## 11. What is unchanged — and the future mode boundary, carried forward verbatim in substance

**The phase inventory, the boundaries, and the reclamation property are untouched.**

```text
MAJOR PHASES                        F0, F1, F2                       (three, unchanged)
F0 -> F1                            QUALIFIED_MAJOR_RESTART_BOUNDARY (unchanged)
F1 -> F2                            QUALIFIED_MAJOR_RESTART_BOUNDARY (unchanged)
post-F2                             TERMINAL_PROCESS_EXIT_EXPECTED   (unchanged)
old process exits before successor  enforced                         (unchanged)
old PID proved gone                 enforced                         (unchanged)
successor has a different PID       observed by the parent           (unchanged)
successor reauthenticates its world FULL, plus its own code identity (WIDENED, not weakened)
PHASE_BOUNDARY_RAM_RECLAMATION      IMPLEMENTED                      (unchanged)
GOVERNED_PAUSE_RESUME               NOT_IMPLEMENTED                  (unchanged)
SAFE_TO_EJECT                       NOT_IMPLEMENTED                  (unchanged)
```

**No physical-detach rights are created.** The external volume must stay attached to the selected
topology for the whole sequence.

**Every topology and safety invariant still holds at every phase**, re-proved rather than assumed:
`FIRST_CANARY_REQUIRED_TRANSPORT = USB_VIA_THUNDERBOLT_DOCK`, the exact qualified Volume UUID, the
accepted storage identity, the ordered dock cascade, AC power, an open lid, the D130 exclusion, the
external `SQLITE_TMPDIR` rule, the phase-specific capacity gates, the host execution lock, the
checkpoint identity, no automatic fallback and no operator fallback to `USB_DIRECT`. A changed BSD
disk identifier remains non-authoritative.

**`census_orchestrator._parse_bulk` remains `CANARY-UNREACHABLE`** — unrepaired, and re-traced
including through the module this record adds.

**The future real-canary authorization boundary, unchanged from Decision 146 §9.** It MUST authorize
only `--mode phase-f0`, `--mode phase-f1` and `--mode phase-f2`, each in its **own OS process**, in
the sequence *phase-f0 → clean exit → prove old process gone → phase-f1 → clean exit → prove old
process gone → phase-f2 → terminal clean exit*. It MUST **forbid** `--mode run` for the authorized
real canary, and an invocation of `--mode run` against it is **OUTSIDE AUTHORITY**. Decision 147 does
not remove `--mode run` from the program.

## 12. Falsification

Ten reversible, source-isolated mutations, each applied alone, exercised against the D144, D145 and
D147 suites, and restored byte-identically — verified by SHA-256 and by an empty `git diff` over the
source tree before publication.

| ID | Mutation | File | Verdict | Killed by |
| --- | --- | --- | --- | --- |
| `M1` | repository `HEAD`/tree removed from the execution identity | `single_source_canary.py` | **KILLED** | 1 failed, 12 passed |
| `M2` | the repository identity helper returns a constant | `repository_identity.py` | **KILLED** | 1 failed |
| `M3` | successor admission stops comparing repository identity | `canary_phases.py` | **KILLED** | 1 failed, 24 passed |
| `M4` | the dirty-tree refusal is bypassed | `repository_identity.py` | **KILLED** | 1 failed, 7 passed |
| `M5` | F1 inherits the predecessor's code identity instead of recomputing | `single_source_canary.py` | **KILLED** | 1 failed, 24 passed |
| `M6` | F2 inherits the predecessor's code identity instead of recomputing | `single_source_canary.py` | **KILLED** | 1 failed, 25 passed |
| `M7` | a bound capacity policy input (`POST_F0`) is omitted from the contract | `single_source_canary.py` | **KILLED** | 1 failed, 18 passed |
| `M8` | phase decomposition collapses — a live predecessor no longer refuses | `single_source_canary.py` | **KILLED** | 1 failed, 111 passed |
| `M9` | the selected dock transport narrowing is dropped on the phase path | `single_source_canary.py` | **KILLED** | 1 failed, 46 passed |
| `M10` | `_parse_bulk` becomes reachable from the phase path | `single_source_canary.py` | **KILLED** | 1 failed, 50 passed |

`M2` is the mutation that would have survived before this record: a helper returning a constant is
exactly what `disclosure_drift.__version__` was. `M1` is `D146-MAJOR-1` itself, reintroduced and
caught.

**Zero surviving load-bearing mutations.** No defensive or unreachable mutation was included in this
set; the one Decision 146 identified as unreachable — the admission-side predecessor-status guard —
is **kept** under `D146-OBS-4` and is honestly reported as unreachable rather than mutated into a
manufactured kill.

## 13. Validation

**One `make check-fast`, over the published tree, exit `0`.**

```text
lint             ruff check .                        All checks passed
format-check     ruff format --check .               203 files already formatted
typecheck        mypy src                            no issues in 98 source files
test-parallel    pytest, 7 xdist workers             5290 passed, 1 skipped   245.18s
secrets          check_no_secrets.py                 467 files scanned, 0 findings
hygiene          check_repo_hygiene.py               469 paths checked, 0 findings
links            check_markdown_links.py             223 documents, 2612 links, 0 unallowed
decision-refs    check_decision_section_refs.py      4912 citations against 143 records
validate         config validation                   PASS
cohorts          frozen cohort print                 PASS
sec-help         SEC CLI help                        PASS
```

**What the new tests prove**, in `tests/unit/test_d147_repository_code_identity.py` (55 tests) and
the changed `tests/unit/test_d145_phase_restart.py` (68 tests):

* **the identity is measured**, not declared — the package's derived `HEAD` and tree equal `git
  rev-parse` run independently by the test against this very checkout;
* **two commits give two identities** — a real temporary repository, a tracked governing-content
  change, a second commit, and both halves of the identity move;
* **an amend moves the commit and leaves the tree**, which is why both are recorded;
* **a modified tracked path, a staged-but-uncommitted path, and an untracked non-ignored path each
  make the tree ambiguous**, and an **ignored** `.pyc` does not;
* **the clean-tree gate refuses a real dirty identity and repairs nothing** — the repository is
  byte-identical afterwards — and **admits a clean one**, so the gate can be passed as well as
  failed;
* **the digest moves** when the repository moves, and when any of the six bound capacity values
  moves; **the page-cache budget still moves nothing**; and the **exact seventeen-input key set** is
  compared against the source's own AST;
* **F1 and F2 each refuse a predecessor from another commit, and from another tree**, naming
  expected and observed; the **same revision admits the whole sequence**; a **version-1 checkpoint**
  and a checkpoint **missing the identity fields** are both refused;
* **the production path derives the identity exactly once, itself** — no entry point takes a
  repository revision, and no CLI flag exists to supply one;
* **end to end, in real processes**: a governing tracked file committed between F0 and F1 makes F1
  refuse, with F0's checkpoint intact and F1's absent; a dirty published checkout refuses and
  creates no world; an untracked module refuses; and a repository that merely *encloses* the code
  refuses;
* **the pre-F2 gate is still the F2 process's first statement inside its own transaction context**,
  proved from the AST; **the three phases are still three real OS processes**, now each reporting the
  measured `HEAD` of the published checkout they ran from; **the qualified dock still passes** while
  `USB_DIRECT`, a wrong UUID, battery power and a closed lid all still refuse at every phase; and
  **`_parse_bulk` is still unreachable**, re-traced through the new module.

## 14. What this record does not authorize

It does not authorize the canary. It does not authorize `--mode run`, or any phase mode, against a
real canary world. It does not authorize E0, the pre-E0 catalog transition, stale-writer-lease
recovery, SEC acquisition, either network switch, migration `0016`, opening D130 archive content, a
physical storage disconnection, or a re-run of the D141 multi-gibibyte qualification. It mints no
activation constant: all three remain `None`. It confers **no acceptance** on Decision 145, on
Decision 146, or on any earlier record — Decisions 137 and 138 remain implemented pending
independent review and owner acceptance, and Decisions 140 and 141 remain accepted for continuation
only.

**A passing preflight still prints `canary_authorized: false`.**

## 15. Next required action

Return this record, with Decision 145 and Decision 146, to GPT-5.6 Sol for owner adjudication.
**Do not start the canary.** The independent re-review of this correction must be performed by a
session that did not write it — this session did, and is therefore forbidden to perform it.
