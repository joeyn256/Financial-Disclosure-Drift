# Decision 143 — Final Independent Pre-Canary Review

```text
STATUS: PUBLISHED — INDEPENDENT REVIEW RECORD
RECORD_TYPE: INDEPENDENT REVIEW — NO SOURCE CHANGE, NO TEST CHANGE, NO REPAIR
DATE: 2026-08-23
OWNER: Joey authorization; independent review performed by Claude Opus 5 at maximum effort
CLASSIFICATION: REVIEW OF A FROZEN TREE — FINDINGS RECORDED, DELIBERATELY NOT REPAIRED
AUTHORIZATION:
  M3_3_D143_FINAL_INDEPENDENT_PRECANARY_REVIEW_AUTHORIZED — spent by the publication of this
  record
ACCEPTED_PREDECESSOR: M3_3_D142_OWNER_ACCEPTED_FOR_FINAL_INDEPENDENT_PRECANARY_REVIEW

REVIEWED_HEAD: a41468203e69c71c9741f3e4fab2d73cf2f7aef1
REVIEWED_TREE: 8614cfc8421bbb93375066631e0616e72d074fd3

VERDICT: D143_FINAL_INDEPENDENT_PRECANARY_REVIEW_FAIL
FINDINGS: 0 BLOCKER / 2 MAJOR / 3 MINOR / 2 OBSERVATION
PARSE_BULK_REACHABILITY: PROVABLY CANARY-UNREACHABLE (case B)
CANARY_CALL_GRAPH: DETERMINED
AUTHORITY_BYPASS: NONE FOUND
NETWORK_BYPASS: NONE FOUND
VALIDATION: PASS — 5140 passed / 1 skipped / 0 failed; every static and governance gate green

CANARY_AUTHORIZED: NO
E0_EXECUTION_AUTHORIZATION: NO
MIGRATION_HEAD: 0015 — 0016 ABSENT
ALL_THREE_ACTIVATION_CONSTANTS: None
NETWORK: enabled=false, m3_acquire_enabled=false
GOVERNED_PAUSE_RESUME: NOT_IMPLEMENTED
SOURCE_AND_TEST_CHANGE: NONE
```

## 1. What this record is, and the independence attestation

It is the **final independent pre-canary review** the owner asked for after
[Decision 142](decision_142_m3_3_precanary_architecture_freeze.md) §10 froze the pre-canary
architecture. It reviews a frozen tree and **records what it found without repairing any of it**.

**Independence.** The review began from a genuinely fresh session context. It did not inherit the
Decision 141 or Decision 142 completion report's conclusion; the controlling state was
reconstructed from the repository and from live predicates rather than read out of a prior
narrative. One active session, no subagents, no delegated reasoning, no parallel sessions, no
workflow delegation. Every gate was executed in the foreground by this session.

**What it is not.** It is not a canary authorization, a repair, a redesign, a runbook correction,
an execution namespace, a launch receipt, an E0 authorization, a migration, or a network
enablement. **A FAIL verdict is not a licence to fix the findings**; Decision 142 §10 froze the
architecture, and this record deliberately leaves every finding standing for the owner.

**The question this review answered** was not *"did Decision 141 and Decision 142 report PASS?"*
It was: *does the frozen published repository independently justify proceeding to an owner decision
on authorizing the first complete-source canary, without an unresolved safety, identity,
reachability, authority, or governance defect?*

## 2. The exact reviewed baseline

Every predicate below was verified **live** before any review work, and re-verified after
validation. None differed from the frozen baseline the authorization named.

| Predicate | Required | Observed |
|---|---|---|
| branch | `main` | `main` |
| `HEAD` | `a41468203e69c71c9741f3e4fab2d73cf2f7aef1` | identical |
| tree | `8614cfc8421bbb93375066631e0616e72d074fd3` | identical |
| `origin/main` | equal to `HEAD` | equal |
| worktree | clean | clean |
| staged / untracked | none | none |
| tag at `HEAD` | none | none |
| migration head | `0015` | `0015` |
| migration `0016` | absent | absent, no file anywhere in the tree |
| `PRE_E0_CATALOG_TRANSITION_AUTHORITY` | `None` | `None`, evaluated live |
| `M3_3_E0_EXECUTION_AUTHORITY` | `None` | `None`, evaluated live |
| `STALE_WRITER_LEASE_RECOVERY_AUTHORITY` | `None` | `None`, evaluated live |
| `network.enabled` | `false` | `false`, loaded through `load_config` |
| `network.m3_acquire_enabled` | `false` | `false`, loaded through `load_config` |
| Decision 142 CI | run `32666011509`, success | `headSha` matches, conclusion `success`, both required jobs `success` |

**The verdict in section 20 applies to that tree**, `a414682` / `8614cfc`. The commit that
publishes this record is a **later, documentation-only** commit and is not the reviewed state.

## 3. Method

Read adversarially, in this order: authority constants and their call sites; the composed
external envelope end to end; the transport module and every production caller; the host power and
lid guard and its reachability; D130 containment; temporary placement; the host execution lock;
the canary entry points in `single_source_canary.py` and `cli.py`; the census orchestrator's
`_parse_bulk` call graph; the falsification tests behind each guard; and finally the governance
layer — Decisions 137, 138, 140, 141 and 142, the registry, the index, the status ledger, and the
operator runbook.

**Production reachability was proved, never assumed.** A guard that exists, is correct, and is
fully unit-tested proves nothing about a launch that never calls it — that is precisely the defect
[Decision 141](decision_141_m3_3_thunderbolt_dock_qualification.md) §3 found in
`require_launch_power_conditions`. Every claim of enforcement below was checked against the actual
call site, and one of them did not hold.

No tracked file was modified at any point during the review. The tree was `8614cfc` before the
first read and `8614cfc` after the last gate.

## 4. Authority and nonauthorization — verified

* `canary_authorized` appears in `src/` exactly once, in
  `ExternalCanaryPreflight.as_record`, as the **literal** `False`. There is no assignment, no
  parameter, no configuration key, and no environment variable that can make it anything else. A
  passing preflight prints `canary_authorized: false` and holding the object authorizes nothing.
* All three activation constants are `Final[str | None] = None` and are read, never written. Each
  execute path is guarded by its own constant and refuses when it is `None`; the tests that pin
  the source text of those declarations pass.
* **No duplicate or shadow authorization constant exists.** A search of `src/` for
  `Final[str | None] = None` returns those three declarations and nothing else; the other
  `AUTHORITY`-named constants are unrelated domain vocabulary (accession authority classes, SIC
  authority ordering, a carry-in schema version).
* **No network path is reachable.** `httpx` is never imported by the canary module graph — proved
  live, by importing `disclosure_drift.m3.single_source_canary` and `disclosure_drift.cli` in a
  fresh interpreter and inspecting `sys.modules`. The two `HttpxTransport()` construction sites
  are in `census_orchestrator` and in the `m3 acquire --live` path, and both are behind gates that
  are false in the tracked configuration. `sec/transport.py` — which *is* pulled in — contains
  protocol and dataclass definitions only and opens nothing.
* **Selecting a topology is not authorizing execution.** Decision 142 selected one; nothing in the
  tree treats that selection as an authority, and no `canary_authorized` value moved.

**No authority bypass was found.**

## 5. Acceptance lineage — D143-R1

Traced rather than assumed. Decisions 137, 138 and 140 remain `IMPLEMENTED — PENDING INDEPENDENT
REVIEW AND OWNER ACCEPTANCE`; their **code is in the tree and enforced**, and their governance
status is pending. Decision 141 is `OWNER ACCEPTED FOR CONTINUATION` under
`M3_3_D141_OWNER_ACCEPTED_FOR_CONTINUATION`, as a bounded qualification only.

Every predecessor safety predicate this review tested is **inherited and still enforced** — the
mandatory UUID assertion, the external-intent rule, the no-parent-creation rule, D130 isolation,
the five capacity floors, temporary placement, runtime volume identity, the host execution lock,
and the power and lid launch conditions. **None was found revoked, and none was found weakened by
a later record.** Decision 142 §5 preserves `USB_DIRECT` explicitly while not selecting it, which
is the one place a reader could mistake supersession for revocation, and it says so in terms.

One published inconsistency was found in the opposite direction — a still-accepted record
described as unaccepted. See MINOR-3.

## 6. The first-canary call graph

Determined, end to end.

```text
disclosure-drift m3 canary-source --mode run
  -> cli.py::_m3_canary_source_command
     -> single_source_canary.run_canary_source_command
        -> require_disposable_work_root
        -> require_external_envelope(root, observed_at, environ, asserted_uuid)   <-- one seam
             external_volume_intent / external_volume_candidate
             mandatory --require-volume-uuid check          (D140-R2)
             require_mounted_qualified_volume               (D140-R3, /Volumes intent)
             external_canary_preflight
                1 require_qualified_volume                  identity, by Volume UUID
                2 require_qualified_transport               transport class
                3 require_launch_power_conditions           AC power, lid
                4 require_outside_d130_archive              isolation
                5 verify_d130_archive                       bounded compact precheck
                6 require_launch_free_space                 185 GiB floor
                7 require_external_sqlite_tmpdir            temporary placement
                8 observe_capacity("PRE_LAUNCH")            one pure reading
        -> run_single_source_canary
             require_canary_work_root
             require_external_envelope  (again, deliberate redundancy)
             operational catalog existence
             acquire_canary_execution_lock                  host-level flock
             _run_locked -> create_world -> WorkingCatalog -> offline parse -> F0/F1/F2
```

Answering the reachability questions directly:

1. **Which entry point would be authorized?** `m3 canary-source --mode run`, launched through
   `scripts/m3/canary_launch.py` under `tmux`/`caffeinate` as runbook §28e specifies.
2. **Which preflight functions must run first?** The eight above, in that order, through the one
   composed seam all three canary modes flow through.
3. **Which parsing paths become reachable?** `m3/offline_parse.py` only —
   `_parse_source` dispatching to `_parse_bulk_submissions`, which streams through
   `_stream_bulk_submissions` and the repaired deferred historical-shard dispatch.
4. **Is `_parse_bulk` reachable?** No. Section 7.
5. **Is any network path reachable?** No. Section 4.
6. **Is any authority token required but absent?** The canary needs an owner canary authority that
   has not been issued; no code path fabricates one, and no constant substitutes for one.
7. **Is persistent state created before the refusal predicates pass?** No. `observe_capacity`
   returns a dataclass and writes nothing; the world is created only inside `_run_locked`, after
   the complete envelope and after the host lock; `--mode preflight` creates nothing, and a test
   pins that it opens no database and writes no file.

## 7. `_parse_bulk` — PROVABLY CANARY-UNREACHABLE (case B)

The carried classification was not accepted mechanically. It was re-derived, and it holds.

**The proof, by call path:**

1. `CensusOrchestrator._parse_bulk` has exactly one caller in the repository:
   `CensusOrchestrator._retrieve_and_parse`, at `census_orchestrator.py:503`.
2. `_retrieve_and_parse` has exactly one caller: `CensusOrchestrator.run`, at
   `census_orchestrator.py:267`.
3. `CensusOrchestrator` is constructed at exactly one site in the whole tree —
   `cli.py:1380`, inside `_census_command` — and that import is **function-local**, so importing
   `cli` does not even load the module.
4. `_census_command` is reached only by `command == "census"`, and the `sec` dispatcher refuses
   `census` with `_stage_refusal` when `config.network.enabled` is false. It is false.
5. `CensusOrchestrator.run`'s second statement is `self._config.require_network()` — a second,
   independent gate that raises before any transport is constructed.
6. The canary module never imports the orchestrator. Verified live: after importing
   `disclosure_drift.m3.single_source_canary` **and** `disclosure_drift.cli` in a fresh
   interpreter, no module matching `census_orchestrator` is present in `sys.modules`.
7. The canary's own bulk path is a **different function** —
   `offline_parse._parse_bulk_submissions` — which carries the
   [Decision 131](decision_131_m3_3_d128_semantic_and_operational_repair.md) shard-dispatch
   repair the orchestrator's copy still lacks. `offline_parse` has no `_parse_bulk` attribute at
   all.
8. A standing test pins the gate:
   `test_the_orchestrator_bulk_parse_stays_unreachable_without_network` asserts the defect is
   still present in the orchestrator's source **and** that `CensusOrchestrator(config).run()`
   raises `NetworkDisabledError` with a valid contact identity supplied, so the refusal proved is
   the network gate rather than the user-agent guard in front of it.

**Classification: B.** It remains an open **pre-network** blocker, deliberately unrepaired, and it
does **not** block the first complete-source canary. It was not repaired here.

## 8. The external working-root envelope

Traced as a production path, not as a set of helpers. `require_external_envelope` is the single
decision point and is called from all three canary modes
(`single_source_canary.py:1049`, `:1778`, `:1950`).

* **Protection is not opt-in.** The envelope is owed by intent (`/Volumes/<name>/`), by residence
  (device number on the nearest existing ancestor), or by assertion — any one of the three. An
  unclassifiable root raises rather than defaulting to internal.
* **An external intent never degrades.** A path under `/Volumes/<name>/` is held to the envelope
  whether or not anything is mounted there; absence is a refusal, not a reclassification.
* **Ordering is sound.** Identity precedes the transport lookup, which needs the authenticated
  volume's BSD identifier purely as a key; both precede the ~104 GB archive `stat` walk; capacity
  and temporary placement follow; the observation is last and is pure.
* **Every guard in the composed preflight is production-reachable**, including the AC-power and
  lid guard that Decision 141 §3 found unreachable. That specific defect is closed, and tests
  assert the refusal *through* `require_external_envelope` rather than against the helper.
* **The pin is taken after admission**, and an unpinnable root is refused rather than admitted as
  unknown.

One reachability gap was found, and it is not in a safety guard but in the **transport narrowing**.
See MAJOR-1.

## 9. Transport and topology — D143-R2

`dock_transport.py` is well constructed and its classification is exact:

* `USB_DIRECT` and `USB_VIA_THUNDERBOLT_DOCK` are distinct classes, and neither is ever
  reclassified as the other. Direct is *nothing above the storage device*; dock is *exactly the
  frozen ordered cascade*. Anything else is `UNQUALIFIED` and refuses.
* **A product name decides nothing.** `DOCK_PRODUCT_NAME`, the Thunderbolt-side vendor and device
  ids, firmware, link rate and route strings are recorded as evidence and are compared against
  nothing. The comparison is on USB vendor/product identity plus the storage serial plus the
  ordered hub cascade.
* **No BSD identifier is frozen or compared.** The current identifier is a momentary IORegistry
  lookup key taken from a volume that has *already* proved its UUID, and a changed disk number
  cannot refuse — asserted at unit level and again through the production envelope.
* **There is no switch that disables the transport check.** The provider is a module-global seam
  for tests only; no CLI flag, configuration key, or environment variable turns it off.
* `required_transport` **can only narrow**: an unqualified class supplied as the requirement is
  itself refused, and a demanded class that is not the observed one refuses.

**What does not hold is the enforcement of the Decision 142 §4 selection.** See MAJOR-1 and
MAJOR-2. The repository enforces *a qualified transport*; it does not enforce *the selected one*.

## 10. The mandatory UUID — D143-R3

**Enforced, exactly as required.** On any external route — intent, residence, or assertion — an
omitted `--require-volume-uuid` raises before the volume is consulted, with an explicit D140-R2
message. A value that is not `397A4D4A-9508-391E-814E-3B533C7BD049` is refused before anything is
measured. Supplying it narrows and never widens: it forces the envelope onto a root that would
otherwise classify as internal, and an internal root asserted with the external UUID is refused on
the identity check. The comparison is case-folded on the Volume UUID and is never a mount-name
check.

**No CLI, configuration, or API route makes it optional.** The only three production entry points
pass the operator's value straight through, and the refusal is raised inside the one composed seam.
One stale operator-facing *description* of the flag remains — MINOR-1 — but it changes no
behaviour, and the refusal message states the rule correctly at the point of use.

## 11. Host power and lid

**Mechanically enforced and production-reachable.** `external_canary_preflight` calls
`require_launch_power_conditions(state=host_power_state(), ...)` as its third guard. A host
reporting battery power refuses; a host reporting a closed lid refuses; an **unreadable** reading
refuses unless the operator explicitly asserts the conditions, and that assertion excuses an
unreadable reading only — a real battery reading is refused whatever is asserted.

`operator_asserts_power_conditions` is **never true in production**: no CLI flag exposes it, and
all three canary entry points leave it at its `False` default. The strict path is the only path an
operator can reach. Tests assert both refusals through the production envelope, not against the
helper.

Documentation and implementation agree in runbook §28e, which marks AC power and lid as
*mechanically* enforced at launch. Runbook §28d's older table disagrees — MINOR-2 — in the
conservative direction.

## 12. D130 isolation and temporary placement

**The D130 archive was not opened, benchmarked, or mutated by this review.**

Containment is decided on `realpath`-resolved, case-folded **path components**, which is what makes
the three aliasing cases fall out together and what keeps a merely similarly-named sibling from
being falsely refused. Three refusals: the root **is** the archive, the root lies **inside** it,
or the root **contains** it. Tests cover the archive itself, a child, a `..` path that normalizes
inward, a symlink that resolves inward, a root that would swallow the archive, and — on the other
side — a benign similarly-prefixed sibling that must **not** be refused.

The archive path is derived from the **authenticated volume's** mount point, so the newly selected
dock route reaches the same isolation check by the same derivation; nothing about the transport
changes which directory is protected. A test asserts the transport guard opens no archive byte.

`SQLITE_TMPDIR` is **validated, never set** by library code, and the environment validated is the
environment SQLite consumes: `os.environ` is the authority, and a caller-supplied mapping that
disagrees is a refusal rather than a preference. Unset or blank refuses; relative refuses;
non-existent refuses; inside D130 refuses; not on the qualified volume refuses, with a message that
names the *temporary root* rather than the working root; and a temporary root on a different volume
from the world refuses. All eight conditions are reached from the one composed preflight, so no
alternate launch path omits the check. **No real canary `SQLITE_TMPDIR` was created.**

## 13. Locking and co-tenancy

`acquire_canary_execution_lock` takes a non-blocking exclusive `flock` on an **internal** lock file
in the private evidence root, independent of `run_id`, before anything is measured or created and
after the whole envelope has held. `flock` alone decides: the file's contents are informational,
stale metadata can never block, and the kernel releases the lock when the holding process dies.
**A second complete-source canary cannot be admitted concurrently**, whatever run identity it is
given — tested, including the process-death release and the stale-metadata case.

The lock is taken on `--mode run` only. A diagnostic `--mode profile-prefix` run is not a
complete-source canary, so D140-R16 is satisfied as written, and runbook §28f.E does not overstate
the coverage — it says the mechanical part covers a second complete-source canary and that the rest
of the co-tenancy list is the operator's. Recorded as OBSERVATION-1 rather than as a finding.

**No user process was killed and no canary was launched.**

## 14. Pause and resume — D143-R4

`GOVERNED_PAUSE_RESUME = NOT_IMPLEMENTED`, and the tree agrees.

There is **no `SAFE_TO_EJECT` token or state anywhere in `src/` or `tests/`** — searched
directly. The two `resume`-named symbols that exist are unrelated: `recovery.resume_authorized` is
an acquisition-window evidence-certainty property that explicitly denies being permission, and
`acquisition.resumed` is a window-resume flag. Neither is a canary detach or reconnect.

Nothing in code or documentation implies that `kill -STOP`, sleep, a closed lid, an unmount, or a
reconnect is a governed pause or a safe detach. Runbook §28e, §28f.F and §28g.F all state the
opposite in terms, and §28g.G states that an interruption is not a pause, that the run is lost, and
that **no recovery procedure may be written**. Decision 140 §17 remains open owner work.

**This review designed and implemented no solution.**

## 15. Tests and falsification

Inspected rather than counted. The falsification classes the authorization named are genuinely
covered, and the tests kill the corresponding defects:

| Class | Covered | Note |
|---|---|---|
| wrong UUID | yes | refused before anything is measured |
| missing UUID | yes | asserts the D140-R2 refusal on every external route |
| wrong enclosure / storage serial | yes | right volume behind the wrong enclosure refuses |
| wrong cascade | yes | parametrized over several unqualified chains |
| unqualified third topology | yes | refuses, through the production envelope |
| direct versus dock distinction | yes | neither is ever reclassified as the other |
| changed BSD identifier | yes | unit **and** production-envelope non-refusal |
| battery launch | yes | through `require_external_envelope` |
| closed-lid launch | yes | through `require_external_envelope` |
| D130 root and child | yes | plus `..`, symlink, and swallow cases |
| substring decoy sibling | yes | asserted **not** falsely refused |
| `SQLITE_TMPDIR` placement | yes | unset, relative, absent, inside D130, wrong volume |
| production reachability of the transport guard | yes | a named reachability test exists |
| production reachability of the power/lid guard | yes | the D141 §3 defect is closed and pinned |
| host lock / second canary | yes | including process-death release and stale metadata |

The Decision 141 M1–M11 falsification claims were checked against the source and tests rather than
re-executed; the reviewed source is unchanged from Decision 141, and the surviving tests do kill
the defect classes those mutations described. **The reachability tests are genuine** — they assert
refusals raised *through* the composed production seam, not against the helper in isolation, which
is the property that would otherwise make a reachability claim worthless.

One test carries a stale **name** from the Decision 138 era —
`test_c1_case_2_the_uuid_argument_omitted_still_protects_the_external_root` — while its body and
docstring correctly assert the Decision 140 refusal. Cosmetic; not a finding.

The tests are also where MAJOR-1 is visible: the repository's own
`test_the_direct_topology_refuses_when_the_dock_profile_is_selected` asserts, in its second half,
that a `USB_DIRECT` attachment **is admitted** through `require_external_envelope` when nothing
narrower is demanded — which is exactly the production argument set.

## 16. Governance and runbook consistency

Cross-checked Decisions 137, 138, 140, 141 and 142, the decision registry, the decision index,
`Milestones/STATUS.md`, and the operator runbook. The check was not limited to text Decision 142
added.

**Sound.** The no-fallback rule is stated identically in Decision 142 §6, the index, the status
ledger, and runbook §28g.D. The §28d correction is complete: the mandatory rule is stated in the
prose, the preflight command example carries the flag, and the refusal list names the omission
first. The superseded §28b launch snippet is explicitly marked superseded and points to §28e. The
index states honestly that the repository recognizes two qualified topologies while the owner has
selected one, and it records that the `required_transport` pin exists so the selection can be
expressed.

**Not sound.** Runbook §28f.C presents a launch-precheck table under the categorical header *"each
is checked by the application rather than by reading this page"*, and two of its rows are not
checked by the application — MAJOR-2. Runbook §28d's Decision 137-era condition table is stale
after D141-R9 and is not marked superseded — MINOR-2. The registry's Decision 141 row still reads
`PENDING ... OWNER ACCEPTANCE` and `no acceptance token` after Decision 142 §3 accepted it —
MINOR-3.

## 17. Validation

Every command was run in the foreground by this session, against the frozen tree, which was
byte-identical (`8614cfc`) before the first and after the last.

| Gate | Result | Elapsed |
|---|---|---|
| focused safety and reachability tests (D137, D138, D140, D141, D131) | **285 passed** | 9 s |
| `ruff check .` | clean | < 1 s |
| `ruff format --check .` | 198 files already formatted | < 1 s |
| `mypy src` | no issues, 96 source files | 1 s |
| secret scan | 457 files, 0 findings | 2 s |
| repository hygiene | 459 paths, 0 findings | < 1 s |
| Markdown links | 218 documents, 2505 links, 0 unallowed broken | 1 s |
| decision section references | 4770 citations against 138 records, 0 unallowed | 1 s |
| `validate-config` | frozen definitions match, 5 cohorts | < 1 s |
| `show-cohorts` | frozen values printed | < 1 s |
| **`make check-fast`** | **exit 0 — 5140 passed / 1 skipped / 0 failed** | 252 s wall, 239.08 s suite |

**Recorded rather than tidied away:** `make check-fast` was invoked **twice**. The first
invocation's exit status was masked by a shell pipeline, so it was re-run once to obtain the status
explicitly. Both invocations were green, the gate is read-only and idempotent, no source was
modified between them, and this was not a retry after a failure.

**Not run, deliberately:** no multi-gibibyte storage requalification, no Decision 141 physical
benchmark, no D130 open, no physical detach, no E0, no canary, no network, no migration `0016`, and
no source-mutating mutation campaign.

## 18. Findings

### BLOCKER — none

### MAJOR-1 — the selected first-canary topology is not mechanically enforced

**Where.** `m3/external_working_root.py` `require_external_envelope` and
`external_canary_preflight` (`required_transport` parameter); `m3/single_source_canary.py:1049`,
`:1778`, `:1950`; `m3/dock_transport.py` `require_qualified_transport`.

**What.** [Decision 142](decision_142_m3_3_precanary_architecture_freeze.md) §4 selects
`USB_VIA_THUNDERBOLT_DOCK` as the one topology for the first complete-source canary, and §6 states
there is **no automatic and no operator fallback**. The mechanism to express that selection exists
and is correct: `required_transport` narrows, and demanding the dock while direct is attached
refuses. **No production caller supplies it.** All three entry points into the envelope pass only
`asserted_uuid`, `environ` and `observed_at`, leaving `required_transport` at its `None` default,
which `require_qualified_transport` documents as *"omitting it admits either qualified topology"*.
There is no CLI flag, configuration key, or environment variable that supplies it, and the launcher
script has no transport awareness at all.

**Consequence.** With the qualified SSD attached **directly** rather than through the qualified
dock, the whole envelope passes and the first complete-source canary starts over an unselected
topology. Nothing mechanical refuses. In particular, the operator failure mode Decision 142 §6
names — a dock preflight refusal answered by re-plugging the SSD directly — is not prevented; the
second attempt is admitted.

**Evidence.** The repository's own test states the behaviour:
`tests/unit/test_d141_dock_transport_qualification.py::test_the_direct_topology_refuses_when_the_dock_profile_is_selected`
asserts a refusal when `required_transport=TRANSPORT_DOCK` **and then asserts admission** for the
same direct attachment when nothing narrower is demanded.

**Character.** This is the same shape as the defect Decision 141 §3 found — a correct, fully tested
mechanism that no production path invokes — one level down: the guard runs, but the narrowing
argument that expresses the owner's selection never arrives. It is disclosed at the governance
level in Decision 142 §5 and in the decision index, which is why it is MAJOR rather than BLOCKER:
no *safety* guard is bypassed, `USB_DIRECT` is a genuinely qualified topology that Decision 141 §16
did not revoke, and the full envelope still runs over it. What is defeated is an explicit owner
ruling.

**Not repaired.** Decision 142 §10 froze the architecture; wiring the pin is a source change.

### MAJOR-2 — runbook §28f.C states two conditions as application-checked that are not

**Where.** `Docs/m3/operator_runbook.md` §28f.C, the launch-precheck table.

**What.** The table is introduced with *"All of these must hold, and each is checked by the
application rather than by reading this page"*. Two of its eight rows fail that claim:

* **Transport — `transport_class` is `USB_VIA_THUNDERBOLT_DOCK`.** The application checks
  membership in the two-element qualified set, not equality with the dock class. A `USB_DIRECT`
  attachment satisfies the application and violates the row.
* **Co-tenancy — no heavy competing SSD workload.** The application checks nothing of the kind, and
  §28f.E of the same section says so explicitly: *"The rest of this list is the operator's to hold:
  nothing here kills a user application."*

**Consequence.** The operator is told that the one predicate MAJOR-1 leaves unenforced is enforced
for them. Between the two findings, **nothing verifies that the first canary runs on the selected
topology** — not the application, and not an operator who trusts the table.

**Character.** This is the defect class Decision 141 §3 was created for, and the class Decision 142
§9 corrected for `--require-volume-uuid`: a runbook naming a condition as checked at launch when no
production path checks it. A partial compensating control exists — the preflight prints
`transport_class`, the row states the required value, and §28f.C tells the operator to read every
line — which is why this is MAJOR rather than BLOCKER.

**Not repaired.** The authorization for this review excludes runbook correction.

### MINOR-1 — the CLI help for `--require-volume-uuid` carries pre-D140 optionality framing

`cli.py` describes the flag as *"a work root on any external volume is ALWAYS held to the full
Decision 137 envelope ... **whether or not this is supplied**. Omitting it cannot disable a single
guard."* It never states that omission on an external route **is itself a refusal**. This is the
same meaning Decision 142 §9 corrected in two runbook places; that record could not reach this one,
because the text lives in `src/`. No mechanical effect: the code refuses, the refusal message
states the rule correctly, and the failure is closed and self-correcting at the point of use.

### MINOR-2 — runbook §28d's Decision 137-era condition table is stale and unmarked

§28d states *"Five of the twelve are mechanically verified and seven are not"* and lists condition
1, external power, as verified by the **operator**. After D141-R9, AC power and lid state are
mechanically verified at launch, and §28e says so. The table also has no transport row. The
staleness is conservative — it understates enforcement and asks the operator to check something
that is also checked — but it contradicts §28e, and unlike the superseded §28b command block it
carries no supersession marker.

### MINOR-3 — the registry's Decision 141 row contradicts Decision 142 §3 on acceptance

`Docs/Decisions/decision_registry.md` still records Decision 141 as `IMPLEMENTED — PENDING
INDEPENDENT REVIEW AND OWNER ACCEPTANCE` with **no acceptance token**, while Decision 142 §3, the
status ledger, and the decision index all record it as `OWNER ACCEPTED FOR CONTINUATION` under
`M3_3_D141_OWNER_ACCEPTED_FOR_CONTINUATION` — a token the Decision 142 row in the same table
carries as its accepted predecessor. `CLAUDE.md` names the registry as the source of truth for
current status, so a reader who consults it alone reaches the wrong conclusion about whether
D141's rulings bind. Inconsistent predecessor-acceptance semantics, resolvable by any reader who
reads the neighbouring row, and carrying no safety consequence.

### OBSERVATION-1 — the host execution lock covers `--mode run` only

A concurrent `--mode profile-prefix` run is not mechanically excluded while a complete-source
canary holds the lock, and it would consume volume space the running canary's capacity model
assumes it alone consumes. D140-R16 speaks only of complete-source canaries and the runbook does
not overstate the coverage, so this is recorded as an observation rather than a finding.

### OBSERVATION-2 — the envelope guards apply only where the envelope applies

Transport, power and lid are read only when an external requirement exists. That is deliberate —
D141-R10 keeps the accepted Decision 116 internal path free of `ioreg` and `pmset`, proved by a
test that makes both fatal — and the selected first canary is external, so every guard applies to
it. Recorded so that a future internal-root canary is not assumed to inherit them.

## 19. Limitations, classified

| # | Limitation | Classification |
|---|---|---|
| 1 | `F_FULLFSYNC` success is OS-visible only | **NON-BLOCKING BOUNDED LIMITATION.** It bounds what durability evidence means; it does not affect any launch predicate |
| 2 | No physical disconnect qualification | **NON-BLOCKING BOUNDED LIMITATION**, given continuous attachment is a stated launch condition and detachment is governed as an interruption, not a pause |
| 3 | No power-loss qualification | **NON-BLOCKING BOUNDED LIMITATION.** The AC requirement is mechanically enforced at launch, which is the available mitigation and is not a substitute for the missing evidence |
| 4 | ExFAT is non-journaled | **NON-BLOCKING BOUNDED LIMITATION.** Bounds crash semantics; the SIGKILL recovery evidence is process-crash only and is not upgraded here |
| 5 | Dock qualification is port- and profile-specific | **NON-BLOCKING BOUNDED LIMITATION**, and it is mechanically enforced: a different dock port yields a different cascade and refuses |
| 6 | Qualification mechanisms are macOS-specific | **NOT RELEVANT TO THE FIRST CANARY.** The canary host is the qualified Mac |
| 7 | No complete-source runtime has been measured | **NON-BLOCKING BOUNDED LIMITATION.** It is what the first canary exists to measure |
| 8 | Governed pause/resume is unimplemented | **NON-BLOCKING BOUNDED LIMITATION**, because it is honestly stated everywhere and no procedure pretends otherwise. It would become a blocker only if a detach were required mid-run |
| 9 | 8 GB host RAM; full-scale peak RSS unmeasured | **NON-BLOCKING BOUNDED LIMITATION.** `/usr/bin/time -l -o` captures it durably for the real run; nothing depends on a prediction |
| 10 | Full-scale `SQLITE_TMPDIR` spill unmeasured | **NON-BLOCKING BOUNDED LIMITATION.** Placement is mechanically enforced onto the same qualified volume, and free space rather than an unlinked-file walk is authoritative |
| 11 | The lid must remain physically open | **NON-BLOCKING BOUNDED LIMITATION**, enforced at launch and operator-held thereafter, as the runbook states |
| 12 | Degraded host battery, AC therefore more important | **NON-BLOCKING BOUNDED LIMITATION**, and correctly framed as raising the importance of the AC requirement rather than as a mitigation |
| 13 | `CensusOrchestrator._parse_bulk` | **PRE-NETWORK / LATER-PHASE BLOCKER.** Proven canary-unreachable in section 7; it must be repaired before any network or live-retrieval authorization |

## 20. Verdict

```text
D143_FINAL_INDEPENDENT_PRECANARY_REVIEW_FAIL
```

**Applying to the frozen tree `a41468203e69c71c9741f3e4fab2d73cf2f7aef1` /
`8614cfc8421bbb93375066631e0616e72d074fd3`.**

`PASS` was not available. Two of its stated conditions are false on this tree: the **selected dock
topology is not mechanically enforced**, and **direct attachment is not refused**. Two MAJOR
findings stand, and the verdict rules make a FAIL mandatory when any MAJOR is unresolved.

Everything else the verdict rules require **does** hold, and it is worth stating plainly rather than
burying under the failure:

* zero BLOCKER findings;
* the first-canary call graph is determined end to end;
* `_parse_bulk` is proven canary-unreachable by concrete call-path evidence;
* every **safety** guard in the envelope is production-reachable, including the one Decision 141
  found unreachable;
* the mandatory UUID semantics are enforced in code and stated correctly in the runbook;
* no authority bypass and no network bypass exists;
* D130 isolation and temporary placement are effective and correctly composed;
* pause/resume is correctly non-implemented, with no `SAFE_TO_EJECT` state anywhere;
* the full validation suite passes.

The failure is narrow and specific: **the owner's topology selection lives in prose, and one
operator-facing table says the application enforces it.**

**No finding was repaired.** Decision 142 §10 froze the pre-canary architecture, and this record
respects that freeze.

## 21. The next owner boundary

**STOP.** Return this review to the owner.

This record authorizes nothing. It does not authorize the canary, canary-world construction, an
execution namespace, a launch receipt, complete-source execution, E0, migration `0016`, network
acquisition, SEC traffic, pause/resume implementation, physical disconnect testing, or any
modification of the D130 archive. It repairs nothing and it accepts no predecessor record.

`CANARY_AUTHORIZED = NO`, unchanged. All three activation constants remain `None`, both tracked
network switches remain `false`, migration head remains `0015` with `0016` absent, and no file
under `src/` or `tests/` was touched.

## 22. Result

```text
M3_3_D143_FINAL_INDEPENDENT_PRECANARY_REVIEW_FAILED_READY_FOR_OWNER
```
