# Milestones/STATUS.md — concrete-state ledger

**Purpose:** a short, current-state record of where the project stands — **Milestones 0, 1, and 2 are
formally closed; Milestone 3 master planning is complete at Decision 027 v0.2; Decisions 028 and 029
are accepted; the bounded M3.1 contract is accepted and implementation-authorized; and the M3.1
implementation is OWNER-ACCEPTED (accepted Decision 031, 2026-08-03, outcome
`M3_1_ACCEPTED_AND_COMPLETE`). Decision 029 code remediation is implemented, the
implementation is frozen at `970e050deb06910adcde8588101564beb7d19c74`, the first durable §17
review is complete and passed, and Decision 029 §12 steps 9, 10, and 11 are complete — the step 9
operational rehearsal passed with the M3.1A token emitted; the step 10 deterministic request plan
ran twice byte-identically (request-plan SHA-256
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, q = 70, 75 planned unique
logical requests, 801 maximum physical attempts); and the step 11 canonical budget display passed,
with the owner approving the exact hard request ceiling 801 on 2026-08-03. **Step 12 is signed and
complete on 2026-08-03**: the signing preflight validated the SEC contact identity at the boundary
(value never displayed) and synchronized `main` with the live remote, and the owner-signed Gate F
checklist (result `PASS`, no unresolved blocker) is durable private evidence, publicly referenced
in the evidence index. **Step 13 was owner-authorized and completed on 2026-08-03**: the Gate F
readiness token was emitted and durably recorded exactly once as immutable private evidence, bound
to the signed checklist, plan, budget, ceiling 801, and repository baseline, and the owner's
evidence-index attestation is recorded. **Step 14 is complete and passed (2026-08-03)**: the
independent M3.1 acceptance review by a fresh non-author session returned
`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS` (artifact SHA-256
`caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`, committed governance-only at
`24fba32413bb6c5dade60a64182e42510afe6f88`) with zero BLOCKER and zero MAJOR findings and three
MINOR findings the owner accepted as nonblocking. **The owner accepted M3.1 on 2026-08-03
(accepted Decision 031), step 15 recorded that acceptance, and step 16 created and pushed the
annotated `m3.1-complete` checkpoint tag** (tag object
`638a02b780d912ff7b37a2f523277b9d451a015a`, peeled to the acceptance commit
`4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`, verified locally and remotely). **Step 17 (2026-08-03,
under the owner's explicit step-17 authorization) closed M3-L11 and M3-L12 on their complete
closure-evidence lists and drafted the bounded M3.2 contract —
[`contracts/m3_2.md`](contracts/m3_2.md), `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE` —
completing the Decision 029 §12 seventeen-step sequence. The M3.2 contract is not accepted, M3.2
implementation is not authorized, live SEC access remains unauthorized, no acquisition has begun,
and no operational catalog exists.** **The independent M3.2 contract review completed 2026-08-04**
— verdict `M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS` (artifact SHA-256
`fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57`, committed governance-only at
`3fbaa12d671d0000f5b608bbf6fb271f78b4673f`) — and **accepted
[Decision 032](../Docs/Decisions/decision_032_m3_2_contract_corrections.md) (2026-08-04)** adopted
its findings and applied the bounded corrections. **The fresh independent no-subagent rereview of
the corrected contract completed 2026-08-04** — verdict
`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS` (artifact SHA-256
`91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf`, committed governance-only at
`3069b03ede9d805e9d0196a3e4c45c8cc68f42b7`; zero BLOCKER, zero MAJOR) — and **the owner accepted
the corrected contract unchanged at T1 (accepted
[Decision 034](../Docs/Decisions/decision_034_m3_2_contract_acceptance.md), 2026-08-04, outcome
`M3_2_CONTRACT_ACCEPTED_AT_T1`)**, so the contract now reads `ACCEPTED (T1) — DECISION 034
(2026-08-04) — IMPLEMENTATION NOT AUTHORIZED`. **T1 grants no later gate: M3.2 implementation
remains not authorized (T2 pending under all five Decision 024 §8 conditions) and not begun,
network and live SEC access remain unauthorized, no acquisition has occurred, and no operational
catalog exists.** **Stages T2.1, T2.2–T2.3, and T2.4 have since each been authorized, implemented,
independently reviewed, accepted, and published in that order; combined stage T2.5–T2.6 — authorized
as one combined stage by accepted
[Decision 045](../Docs/Decisions/decision_045_m3_2_t2_5_t2_6_integrated_implementation_authorization.md)
(2026-08-07, outcome `M3_2_T2_5_T2_6_INTEGRATED_IMPLEMENTATION_AUTHORIZED`) — is now IMPLEMENTED,
INDEPENDENTLY REVIEWED, ACCEPTED, AND PUBLISHED by accepted
[Decision 046](../Docs/Decisions/decision_046_m3_2_t3_acceptance_and_publication.md) (2026-08-07,
outcome `M3_2_T3_ACCEPTED_AND_PUBLISHED`, overall determination
`M3_2_T3_IMPLEMENTATION_ACCEPTED_AND_COMPLETE`), on the fresh independent T3 verdict
`M3_2_T3_CORRECTED_FREEZE_CANDIDATE_REREVIEW_PASS` and its durable artifact, with Decision 045's
implementation authority now exhausted. **The read-only T4 operational-preflight architecture
discovery then completed
(`M3_2_T4_OPERATIONAL_PREFLIGHT_ARCHITECTURE_DISCOVERY_COMPLETE`; zero BLOCKER, four MAJOR), and
accepted
[Decision 047](../Docs/Decisions/decision_047_m3_2_t4_operational_preflight_authorization.md)
(2026-08-07, outcome
`M3_2_T4_OPERATIONAL_PREFLIGHT_AUTHORIZED_AND_PRE_T4_RAWSTORE_SUBSTAGE_AUTHORIZED`) accepts it, fixes
the twelve frozen owner rulings 047-A–047-L, discharges **F4** with exactly three new evidence-index
artifact types, records limitation **M3-L13**, and authorizes one bounded two-path pre-T4 RawStore
streaming substage.** **That substage is now IMPLEMENTED, INDEPENDENTLY REVIEWED, ACCEPTED, AND
PUBLISHED** by accepted
[Decision 048](../Docs/Decisions/decision_048_m3_2_pre_t4_rawstore_acceptance_and_publication.md)
(2026-08-07, outcome `M3_2_PRE_T4_RAWSTORE_ACCEPTED_AND_PUBLISHED`), on the fresh independent verdict
`M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEW_PASS` (**BLOCKER 0 · MAJOR 0**) and its durable
artifact — **and limitation `M3-L13` is CLOSED, with F4 COMPLETE**, Decision 047's substage authority
now exhausted. **The T4 operational preflight has since been EXECUTED, and it is now ACCEPTED AND
PUBLISHED** by accepted
[Decision 049](../Docs/Decisions/decision_049_m3_2_t4_operational_preflight_acceptance.md)
(2026-08-07, outcome `M3_2_T4_OPERATIONAL_PREFLIGHT_ACCEPTED_AND_PUBLISHED`, classification
**T4 `COMPLETE_AND_ACCEPTED`**), on final findings **BLOCKER 0 · MAJOR 0 · MINOR 0 · OPTIMIZATION 0**
and with **no independent rereview required**. The acceptance is bound to two private artifacts that
stay outside Git — the T4 attestation `runs/m3_2_t4_preflight/t4_preflight_attestation.md` (SHA-256
`8483a549cf894f1d186750ec13c24b41e5279134e782ca6e28ff4514e75d10c8`) and the backup manifest
`backups/m3_2_t4_pre_window/manifest.sha256` (SHA-256
`0bb2b1d96bcefe7885d538fa054c93e4887a8a5233529538f9de39f059b84c8d`, **17** covered files) — with **no
`operational_preflight_attestation` evidence type and no public evidence-index row**. T4 left the
repository **byte-identical** and **enabled nothing**: `FREE_DISK_50_GIB_GATE: PASS`
(74,481,328,128 bytes / 69.3661 GiB against the 50.00 GiB floor), the off-device USB backup verified
**17/17** at the destination and **17/17** on scratch restore, and the disposable offline catalog
passed with migrations contiguous `0001`–`0013` and the corrected expectation
**`reference_policy_versions = 25`** now frozen (21 migration keys + 4 `seed_reference_data()` keys,
zero overlap — resolving the stale packet value of 6). The one initial M3.2A live invocation
authorized by accepted
[Decision 050](../Docs/Decisions/decision_050_m3_2_t5_initial_live_invocation_authorization.md)
was executed exactly once and ended non-successfully during archive-member lineage processing. One
physical SEC attempt completed the immutable bulk `submissions.zip` object and raw lineage; no second
request occurred. The invocation emitted no terminating receipt, committed no observation/member
lineage transaction, and left its ingestion job non-terminal with a stale lease. The governed recovery
classification remains **`UNDETERMINED`**, and the old run is **never resumable**.

Accepted [Decision 051](../Docs/Decisions/decision_051_m3_2_post_t5_remediation_governance.md)
(2026-08-08, outcome `M3_2_POST_T5_REMEDIATION_GOVERNANCE_RECORDED`) records the post-T5 owner
rulings. Accepted consumed physical attempts are **1 of 801**; remaining total headroom is **800** and
remaining bulk-route headroom is **5**. Decision 051 owner-approves, but does not yet authorize
implementation of, the bounded remediation architecture: the O(n²) archive-path correction, a
pre-send durable attempt ledger, scoped SIGTERM handling, and explicit receiptless inspection mode
only.

**That remediation is now IMPLEMENTED, INDEPENDENTLY REVIEWED, ACCEPTED, AND PUBLISHED** by accepted
[Decision 052](../Docs/Decisions/decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md)
(2026-08-08, outcome `M3_2_POST_T5_REMEDIATION_ACCEPTED_AND_PUBLISHED`), on the fresh independent
verdict `M3_2_POST_T5_REMEDIATION_INDEPENDENT_REREVIEW_PASS` (**BLOCKER 0 · MAJOR 0 · MINOR 2**) and
its durable artifact — **and Decision 051's implementation authority is now exhausted**. The accepted
candidate is the implementation commit `47de073…` plus the separate accounting-correction commit
`7dad423…` (tree `53d5342…`); the correction is a transparent separate commit, expressly instead of an
amend, rebase, squash, or history rewrite. Counterexample A resolves to **2** and counterexample B to
**1, never 6**, while the historical empty-ledger incident stays exactly **1 of 801**,
**`UNDETERMINED`**, and non-resumable. Decision 051 §11 item 4's two-run real-archive evidence was
**NOT re-run** — the private path was undisclosed — so the accepted **43.1 / 45.2-second**
measurements stand and the reviewer's equivalent-scale synthetic evidence is **never** to be cited as
real-archive evidence. Three new limitations are `ACTIVE`: **M3-L14** (receiptless ledger-coverage
cardinality evaluated per manifest), **M3-L15** (second-SIGTERM suppression unguarded by a regression
test), and **M3-L16** (no clean-run carry-in interface for the consumed baseline of 1). **M3-L16
blocks any later clean-run or live authorization, and no live readiness is claimed.**

The real interrupted state remains untouched: no ledger backfill, receipt reconstruction, lease
clear, recovery mutation, or run closure is authorized. **No network, SEC request, new live
invocation, resume, T6, M3.2B, or Gate H is authorized.** Tracked network configuration remains
**false / false** and CompanyFacts remains **false**.

Accepted
[Decision 053](../Docs/Decisions/decision_053_m3_2_interrupted_run_closure_procedure_authorization.md)
(2026-08-08, outcome `M3_2_INTERRUPTED_RUN_CLOSURE_PROCEDURE_AUTHORIZED`) fixes the exact **one-time
architecture and boundaries** for the later offline closure of that historical job to `stopped`, and
authorizes **only** a later separate exact owner execution packet. The closure will run as **one
ephemeral, hash-recorded, one-time operator procedure outside the repository**, using the accepted
`CatalogWriter` and its `batch()` transaction — the normal OS-lock and writer lifecycle — and calling
none of `prepare_operational_catalog`, `migrate()`, `seed_reference_data()`,
`finish_acquisition_run`, a live-acquisition entry point, or a transport constructor. **No permanent
production surface is created or authorized.** **Decision 053 itself performed no closure**: it opened
no catalog even read-only, read no private evidence, and mutated no operational state.

**That closure has since EXECUTED and is ACCEPTED** (accepted
[Decision 054](../Docs/Decisions/decision_054_m3_2_interrupted_run_closure_acceptance.md),
2026-08-08, outcome `M3_2_INTERRUPTED_RUN_CLOSURE_ACCEPTED`). The Decision 053 execution packet was
issued and run once, offline, and the owner accepts it as **PASS**: every Decision 053 §7.1 preflight
gate passed, **11 of 11** required synthetic cases passed, and the real transaction committed through
the accepted `CatalogWriter` and one `BEGIN IMMEDIATE` `batch()` transaction, changing exactly **three
columns of exactly one** historical M3.2A row — `job_state` `running` → **`stopped`**,
`finished_at_utc` `NULL` → one new UTC instant, and `detail` → the byte-exact 222-byte Decision 053
§6.4 closure text — with `cursor.rowcount == 1`. **1 of 84** user tables changed, **no** table's row
count changed, and the governed inventories, raw object, lineage, receipt inventory, attempt ledger,
event ledger, and every non-target column were unchanged; the lease kept its inode at mode `0600` and
ended **`released`**; integrity gates pass; the repository stayed byte-identical; and **no network,
DNS, SEC, resume, retry, replacement, receipt-construction, ledger-backfill, or orphan action
occurred**. The owner independently reverified the private evidence and a disposable immutable
read-only catalog copy. **Decision 053's one-time execution authority is now `EXHAUSTED`, and the
closure is complete and irreversible.**

**`HISTORICAL_JOB_STATE_NOW: stopped`.** Any statement elsewhere in this file or in Decision 053 that
the job is `running` or that the closure has not executed is **historical** — accurate when written,
and superseded by Decision 054 **only** as a statement of current state. Private operational state is
not self-recording, so that gap was expected residue of the correct record-then-execute-then-accept
sequence, not a governance defect.

**A truthful terminal state is not a resolution.** The closure disposes of the job honestly and does
nothing else: recovery remains **`UNDETERMINED`**, there is **no terminating receipt** (none created,
none reconstructed), historical `ops_retrieval_attempts` rows remain **0** with no backfill, accepted
consumption remains **1 of 801** (total headroom **800**; bulk-route **accounting** headroom **5**),
and the old run is **never resumable**. **`stopped` is not `completed`**, not a resolved orphan, not a
discharged recovery condition, and not continuation eligibility. **M3-L14, M3-L15, and M3-L16 remain
`ACTIVE`**, with M3-L16 still blocking every clean-run and live authorization and no live readiness
claimed. **No further operational mutation, repeat closure, network, SEC, new live invocation, T6,
M3.2B, or Gate H is authorized.**

**The M3-L16 carry-in architecture discovery has since been issued and completed as read-only
validation, and its architecture is now ACCEPTED AND BINDING** (accepted
[Decision 055](../Docs/Decisions/decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md),
2026-08-08, outcome `M3_2_CARRY_IN_ARCHITECTURE_ACCEPTED_AND_OFFLINE_IMPLEMENTATION_AUTHORIZED`; the
owner's verbatim approval was **"approve Decision 055."**). The validation independently established
four facts, all accepted: consumption is exactly **1 of cumulative ceiling 801**; that attempt is
attributable to **`sec_bulk_submissions`**; historical `ops_retrieval_attempts` rows equal **0**; and
recovery remains **`UNDETERMINED`** and **never `SAFE`** because of the **raw-store/catalog orphan
mismatch**, not because attempt evidence is ambiguous. It changed nothing, contacted nothing, and left
the baseline intact.

Decision 055 fixes eight rulings **055-A**–**055-H**. The cumulative ceiling stays exactly **801** with
historical seed **`H` = 1** and **no `802`, additive, shadow, reset, or reinterpreted ceiling**; the
frozen plan `19be7bdc…` and its full **75-logical-request** plan are unchanged; the global
`PhysicalAttemptCeiling` is constructed with `approved_ceiling` **801** and `consumed` **1**; it may
**lawfully stop the run at cumulative 801 with planned work remaining**, with **no pre-run fit gate**;
and route attribution to `sec_bulk_submissions` is **evidence and reporting only**, with **no
per-route runtime refusal and no `sec/http_client.py` change**. One **clean-root carry-in interface
that is never resume** — refusing coexistence with `--resume-from` — is carried by canonical JSON under
schema **`m3-carry-in-authority/1.0`**, identified by the SHA-256 of its exact canonical bytes with
**no circular self-hash field**, validated **before transport construction**, and **consumed exactly
once** by a deterministic `ops_checkpoints` primary key inside the **same existing `BEGIN IMMEDIATE`**
run-registration transaction — **no migration** — all-or-nothing, and **burned even on a later pre-wire
failure with no automatic reissue**. The receipt schema is unfrozen **only** for writer version
**`m3-execution-receipt/3.0`** with version dispatch: existing **`2.0`** receipts stay byte-unchanged,
valid, readable, and mixed-chain usable and are **never rewritten**; `carry_in_authority_sha256` is
required **only** on a clean carry-in root; and the chain walker adds the root carry-in **exactly
once**. **M3-L14** is pre-resolved by the **fail-closed global one-to-one reservation-consumption
rule**, under which the one-reservation/two-owned-segment counterexample **must return `UNDETERMINED`**,
never `1`/`UNSAFE`. The historical orphan takes **Path B**: a **separately authorized, offline,
one-time, verified adoption must precede any clean carry-in run**, and Decision 055 neither designs it
in executable detail nor performs it.

**Decision 055 authorizes one bounded OFFLINE implementation candidate on exactly sixteen paths with
no seventeenth** — four production (`cli.py`, `m3/acquisition.py`, `m3/recovery.py`, `m3/receipt.py`),
six normative/operator documentation, and six test paths — producing **exactly one local candidate
commit** with subject `Implement M3.2 carry-in authority and receipt v3`, **unpushed and untagged**,
followed by targeted tests with twelve mandatory non-vacuous positive controls, the full validation
gate, and a **fresh Claude Opus 5 Max non-author independent review**. **Decision 055 itself accepts no
candidate and closes no limitation**: it performs no implementation, opens no operational catalog or
private evidence, mutates no state, and grants no orphan-adoption, transport-construction, network,
SEC, resume, retry, replacement, clean-run, T6, M3.2B, or Gate H authority. **M3-L14 and M3-L16 remain
`ACTIVE` — now carrying a selected architecture and implementation authority, and NOT closed — M3-L16
still blocks every clean-run and live authorization, and M3-L15 is untouched and byte-unchanged.** The
exact next authorized action is **`CLAUDE_M3_2_DECISION_055_OFFLINE_IMPLEMENTATION_PACKET`** — the
bounded offline implementation, which does not self-execute and grants no operational-state,
orphan-adoption, network, SEC, or live authority.

The earlier bounded
**non-production** stage
**M3.2 G1 — Navigation and Workflow Repair**, authorized on a seven-path ceiling by accepted
[Decision 043](../Docs/Decisions/decision_043_m3_2_g1_navigation_workflow_repair_authorization.md)
(2026-08-06, outcome `M3_2_G1_NAVIGATION_AND_WORKFLOW_REPAIR_AUTHORIZED`), is now **COMPLETE,
ACCEPTED, AND PUBLISHED** by accepted
[Decision 044](../Docs/Decisions/decision_044_m3_2_g1_acceptance_and_publication.md) (2026-08-06,
outcome `M3_2_G1_ACCEPTED_AND_PUBLISHED`, classification `M3_2_G1_ACCEPTED_AND_COMPLETE`), on the
fresh independent review verdict `M3_2_G1_INDEPENDENT_REVIEW_PASS` and its durable artifact; it
changed no production source or test behaviour, and **G1's implementation authority is now
exhausted**. This
file records
workflow state; it never overrides a decision record, a migration, or `src/disclosure_drift/`. When
this file and an authoritative source (`Docs/Decisions/` — with
`Docs/Decisions/decision_registry.md` authoritative for which decisions exist and their approval
status — a migration, or `src/disclosure_drift/`) appear to disagree, the authoritative source
controls — see CLAUDE.md's authority rules. `Docs/decision_index.md` is a navigation aid only and is
never consulted to establish that a decision exists or is approved.

No percentages are recorded here. A stage is accepted, blocked, deferred, or not started; nothing
here is scored.

Commit hashes below are **historical checkpoint references**, current as of the last time this file
was edited. They are not live. For the current branch, HEAD, tag, and migration state, run
`scripts/context_snapshot.sh` (or `make context`) — it reads Git directly and cannot go stale the way
a hand-maintained hash can.

## Milestone closure state

Recorded by [Decision 026](../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`), on
the final fresh independent rereview
`ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT`, with **no closeout blocker
remaining**.

| Milestone | State | Closure record | Completion tag |
|---|---|---|---|
| **Milestone 0** — research question, novelty boundary, preregistration, frozen definitions, registers | **`FORMALLY_CLOSED`** | Decision 026 §6 | `m0-complete` |
| **Milestone 1** — reproducible engineering foundation | **`FORMALLY_CLOSED`** | Decision 026 §7 | `m1-complete` |
| **Milestone 2** — M2.1 offline SEC policy, M2.2 controlled live-metadata readiness, M2.3 through accepted S6 | **`FORMALLY_CLOSED`** | Decision 026 §§8–10 | `m2-complete` |
| **Milestone 3** — M3.1–M3.5 | **Master planning complete; Decisions 028–031 accepted; the bounded M3.1 contract is accepted and implementation-authorized. M3.1 is OWNER-ACCEPTED (Decision 031, 2026-08-03, outcome `M3_1_ACCEPTED_AND_COMPLETE`)** — Decision 029 code remediation implemented; the implementation is frozen at `970e050deb06910adcde8588101564beb7d19c74`, and the **first durable §17 review is complete and passed** (`M3_1_SECTION_17_REVIEW: PASS`, artifact committed at `66e4c5433a393815c74f9e3087300613a516e2fb`, owner-accepted); Decision 029 §12 step 8 prepared and validated the external evidence root and operator manifest, and the **step 9 operational rehearsal ran once on 2026-08-03 and passed** — all twelve A1–A12 scenarios PASS, zero actual SEC requests, and `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED` emitted by the canonical command; **steps 10 and 11 are complete** — two byte-identical zero-request M3.2A plans (request-plan SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, q = 70, 75 planned unique logical requests, 801 maximum physical attempts) and a passing canonical budget display, with the **owner approving the exact hard request ceiling 801 on 2026-08-03** (three response-outcome expectations deliberately unresolved); **step 12 is signed and complete (2026-08-03)** — the sole hygiene blocker was resolved by accepted Decision 030, the signing preflight validated the SEC identity and synchronized `main` (`HEAD == origin/main`), and the **owner-signed Gate F checklist** (result `PASS`; every item accepted; no unresolved blocker) is immutable private evidence with its SHA-256 recorded in the public evidence index alongside the plans, receipts, and the owner-approved request budget (ceiling 801); **step 13 owner-authorized and completed (2026-08-03)** — the Gate F readiness token emitted and recorded exactly once as immutable private evidence bound to the signed checklist, plan, budget, and ceiling, with the owner's evidence-index attestation recorded; **Gate F readiness recorded; Gate F execution not begun and live SEC access not authorized**; **step 14 complete and passed (2026-08-03)** — the independent acceptance review returned `M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS` (artifact SHA-256 `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`, commit `24fba32413bb6c5dade60a64182e42510afe6f88`); **the owner accepted M3.1 on 2026-08-03 and step 15 records that acceptance (accepted Decision 031)**; **step 16 complete (2026-08-03)** — the annotated `m3.1-complete` checkpoint created and pushed (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`, verified locally and remotely); **step 17 complete (2026-08-03)** — M3-L11 and M3-L12 `CLOSED` on their complete closure-evidence lists and the bounded M3.2 contract drafted ([`contracts/m3_2.md`](contracts/m3_2.md), `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE`), completing the Decision 029 §12 sequence. **The M3.2 contract was subsequently reviewed, corrected (accepted Decision 032), rereviewed fresh with no subagents (`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS`, 2026-08-04), and ACCEPTED unchanged at T1 (accepted Decision 034, 2026-08-04). Stages T2.1, T2.2–T2.3, T2.4, G1, and combined T2.5–T2.6 have each since been authorized, implemented, independently reviewed, accepted, and published, and overall M3.2 T3 implementation acceptance has occurred (accepted Decision 046, 2026-08-07, `M3_2_T3_ACCEPTED_AND_PUBLISHED`); T4 is complete and accepted; the one Decision-050 initial T5 invocation executed and ended non-successfully after one physical SEC attempt; Decision 051 accepts consumed count 1 of 801, keeps recovery `UNDETERMINED`, makes the old run never resumable, and records the bounded remediation architecture without yet authorizing implementation, operational-state mutation, any new live invocation, T6, M3.2B, or Gate H; and that remediation has since been implemented, independently reviewed, accepted, and published (accepted Decision 052, 2026-08-08, `M3_2_POST_T5_REMEDIATION_ACCEPTED_AND_PUBLISHED`, on the PASS rereview with BLOCKER 0 / MAJOR 0 / MINOR 2), exhausting Decision 051's implementation authority while carrying new `ACTIVE` limitations M3-L14, M3-L15, and M3-L16, granting no operational-state, network, live-run, T6, M3.2B, or Gate H authority, and claiming no live readiness; and accepted Decision 053 (2026-08-08, outcome `M3_2_INTERRUPTED_RUN_CLOSURE_PROCEDURE_AUTHORIZED`) has since fixed the exact one-time architecture and boundaries for the later offline closure of the interrupted job to `stopped` — one ephemeral, hash-recorded operator procedure outside the repository using the accepted `CatalogWriter` and its `batch()` transaction, with no permanent production surface created — while performing no closure and granting no private-evidence, catalog-open, operational-state, network, live-run, T6, M3.2B, or Gate H authority, leaving M3-L14, M3-L15, and M3-L16 `ACTIVE` and unchanged; and **that closure has since been executed exactly once, offline, under the separate Decision 053 execution packet and ACCEPTED as PASS by accepted Decision 054 (2026-08-08, outcome `M3_2_INTERRUPTED_RUN_CLOSURE_ACCEPTED`), which records `HISTORICAL_JOB_STATE_NOW: stopped`, exhausts Decision 053's one-time execution authority, and — because a truthful terminal state is not a resolution — leaves recovery `UNDETERMINED`, no terminating receipt, zero historical attempt rows, consumption at 1 of 801, the old run never resumable, and M3-L14, M3-L15, and M3-L16 `ACTIVE` and unchanged with M3-L16 still blocking every clean-run and live authorization, while granting no further operational mutation, repeat closure, network, SEC, new live invocation, T6, M3.2B, Gate H, or tag authority** | Decision 024 §5.1; Decision 027 v0.2; accepted [Decision 028](../Docs/Decisions/decision_028_m3_1_readiness_corrections.md); accepted [Decision 029](../Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md); accepted [`contracts/m3_1.md`](contracts/m3_1.md); accepted [Decision 031](../Docs/Decisions/decision_031_m3_1_acceptance.md); accepted [Decision 034](../Docs/Decisions/decision_034_m3_2_contract_acceptance.md); accepted [Decision 051](../Docs/Decisions/decision_051_m3_2_post_t5_remediation_governance.md); accepted [Decision 052](../Docs/Decisions/decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md); accepted [Decision 053](../Docs/Decisions/decision_053_m3_2_interrupted_run_closure_procedure_authorization.md); accepted [Decision 054](../Docs/Decisions/decision_054_m3_2_interrupted_run_closure_acceptance.md) | — |

**M2.3 Stage S6 is accepted and immutable at `m2.3-s6-complete`.** The three completion tags
**supplement** every earlier checkpoint tag and move, replace, or re-point none of them.

**Closure closed the milestones, not their obligations.** Every accepted limitation stays active and
is inherited by Milestone 3 — Decision 020 §19.1, Decision 021 §19, Decision 022's applicability
boundary, and Decision 023 §7's **O1**–**O4**, with **O1** still an unresolved future owner-ruling
condition (Decision 026 §12). **The project is not complete**: no live SEC pilot has been executed,
no real snapshot or real manifest exists, no root has been approved, and nothing has been published.

## Accepted baseline

- Branch: `main`.
- Closeout commit: the commit created by the 2026-07-31 governance-only closeout session
  ("Close Milestones 0 1 and 2"), carrying the three annotated completion tags `m0-complete`,
  `m1-complete`, and `m2-complete`. This file records no hash for it by design; resolve it live with
  `make context`.
- Accepted methodological checkpoint tag: `m2.3-s6-complete` -> the commit created by the 2026-07-31
  acceptance-recording session ("Complete M2.3 S6 deterministic pilot manifest"). This file records
  no hash for it by design; resolve it live with `make context`.
- Immediately preceding checkpoint tag: `m2.3-s5.4-complete` -> the commit created by the
  2026-07-30 checkpoint session ("Complete M2.3 S5.4 reserve architecture").
- Earlier checkpoint tag: `m2.3-s5-complete` -> the commit created by the 2026-07-29
  checkpoint session ("Complete M2.3 S5 joint selection checkpoint"). **`m2.3-s5-complete` and
  `m2.3-s5.4-complete` are immutable and were never moved, replaced, or re-pointed**;
  `m2.3-s5.4-complete` supplements rather than replaces `m2.3-s5-complete` (Decision 020 §§14.9, 15),
  and `m2.3-s6-complete` supplements both (Decision 021 §22, Decision 023 §8).
- Earlier accepted commits: `921f57b` ("Approve Decision 018 accession selection policy"),
  `3b01c50` ("Add repository orientation and stage-contract workflow"),
  `f490281` ("Optimize offline test execution and parallel validation").
- Earlier checkpoint tags: `m2.3-s4-complete` -> `e7157aa` ("Complete M2.3 S4 deterministic entity
  selection and persistence"); `m2.3-s3.2-complete` -> `5fb8e27`.
- Migrations end at `0013_m23_manifest_lifecycle_guards.sql`, created and accepted at Stage S6. See
  `src/disclosure_drift/storage/migrations/` for the authoritative list.

## Current phase

**Milestones 0, 1, and 2 are formally closed (Decision 026). Milestone 3 master planning is complete
at Decision 027 v0.2. Decision 028 records the accepted planner-v2, corrected A1–A12, reason-code,
receipt-v2, budget, ceiling, recovery, and M3-L11 rulings after
`INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`. The bounded M3.1 contract is accepted and
implementation-authorized, and the M3.1 implementation is **owner-accepted** (accepted Decision
031, 2026-08-03) — Decision 029
code remediation is implemented, the implementation is frozen at
`970e050deb06910adcde8588101564beb7d19c74`, and the first durable §17 review passed
(`M3_1_SECTION_17_REVIEW: PASS`, artifact committed at
`66e4c5433a393815c74f9e3087300613a516e2fb`), and Decision 029 §12 steps 9–11 are complete — the
step 9 rehearsal passed with the M3.1A token emitted, step 10 produced two byte-identical
zero-request plans (request-plan SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`),
and step 11's canonical budget display passed with the owner approving the exact hard request
ceiling 801 on 2026-08-03 — step 12 was signed and completed on 2026-08-03 (checklist result
`PASS`; the sole hygiene blocker having been resolved by accepted Decision 030), step 13
completed on 2026-08-03 under separate owner authorization with the Gate F readiness token
durably recorded, step 14 (the independent M3.1 acceptance review) completed and passed on
2026-08-03 (`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`; artifact SHA-256 `caf9f26e…`; commit
`24fba32…`), and the owner accepted M3.1 on 2026-08-03 with step 15 recording that acceptance
(accepted Decision 031, `M3_1_ACCEPTED_AND_COMPLETE`); step 16 created and pushed the annotated
`m3.1-complete` checkpoint (2026-08-03); and step 17 closed M3-L11 and M3-L12 and drafted the
bounded M3.2 contract ([`contracts/m3_2.md`](contracts/m3_2.md), then `DRAFT — PENDING OWNER
REVIEW AND ACCEPTANCE`) — while Gate F execution has not begun and live SEC access remains
unauthorized. The contract was then reviewed, corrected (accepted Decision 032), rereviewed fresh
with no subagents (`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS`, 2026-08-04), and
accepted unchanged at T1 (accepted Decision 034, 2026-08-04); M3.2 implementation remains not
authorized (T2 pending) and not begun.** The rest of this
section is the accepted historical record of how Milestone 2.3 reached that point.

M2.3 (deterministic pilot selection). Stage S4 (entity-only selection) is accepted. Decision 018
(Stage S5 accession selection policy) and Decision 019 (Stage S5 frozen-storage-to-pure-input
mapping policy) are both **approved by the project owner 2026-07-28**. Decision 020 (Stage S5.4
reserve architecture and quota-contribution membership) is **approved by the project owner
2026-07-30**.

**Stage S5.1 is accepted. Stage S5.2 is accepted. The combined S5.1–S5.3 checkpoint is
owner-accepted** (2026-07-29) and committed under the single commit boundary Decision 018 §22 fixes.
The final independent re-review's recommendation was **`ACCEPT_M23_S5_3_CHECKPOINT`**, on a final
accepted suite of **1661 passed, 1 skipped** (the one skip is pre-existing: the `[sec]` extra is not
installed). **No acceptance blocker remains.**

**Stage S5.4 (reserves) is complete and owner-accepted** (2026-07-30). Decision 020 remains
`APPROVED — OWNER APPROVED 2026-07-30`. The stage was implemented under a separately issued bounded
implementation prompt confined to twelve authorized paths, reviewed independently, corrected under
bounded fixes D1/T1/T2/T3, re-reviewed, and accepted on the final independent recommendation
**`ACCEPT_M23_S5_4_FOR_CHECKPOINT`**, on a final accepted suite of **1899 passed, 1 skipped** (same
pre-existing skip). Migration `0012_m23_selection_entity_reasons.sql` was created and accepted. Its
contract — [`Milestones/contracts/m23_s5_4.md`](contracts/m23_s5_4.md) — is now
**`ACCEPTED_AND_COMPLETE`** with **`IMPLEMENTATION_AUTHORIZATION: NO`** and **no active blocker**. The
checkpoint is tagged **`m2.3-s5.4-complete`**, supplementing the immutable `m2.3-s5-complete`. **No
active S5.4 blocker remains**, and further S5.4 change requires a new explicit owner authorization.

**Stage S6 (pilot manifest construction, terminal result identity, and the publication boundary) is
complete and owner-accepted** (2026-07-31). Its governance is accepted at **v0.5**: Decision 021 v0.5
is `ACCEPTED` (owner approved 2026-07-30), Decision 022 is `ACCEPTED` (owner approved 2026-07-31) for
crosswalk item-46 applicability, and **Decision 023 is `ACCEPTED` (owner approved 2026-07-31)** and
records acceptance itself, outcome **`M23_STAGE_S6_ACCEPTED_AND_COMPLETE`**. v0.2 applied six bounded
owner corrections issued after the focused independent governance review of v0.1; v0.3 applied one
further correction widening the structural-fingerprint tuple to five columns; v0.4 applied two
corrections issued after the focused independent governance review of v0.3 — the exhaustive 81-item
milestone-plan §10 crosswalk and the growth of migration `0013` from four triggers to five; and
**v0.5 applied one owner ruling issued after the focused independent governance review of v0.4** —
migration `0013` grows from five triggers to **eight**, closing selection-run replacement, deletion,
and identity mutation. **v0.1, v0.3, and v0.4 were each independently reviewed and none was approved;
v0.2 was never independently reviewed.** [`Milestones/contracts/m23_s6.md`](contracts/m23_s6.md) is
now `ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO`. **No stage contract currently
authorizes implementation.**

**The Milestone 2 / Milestone 3 boundary is recorded.** Decision 024
(`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED`) fixes accepted
S6 as the **final implementation stage of Milestone 2** and transfers the obligations formerly called
S7–S10 **intact** into Milestone 3 as **M3.1–M3.4**, adding **M3.5** for integrated real-pilot
acceptance and Milestone 3 closeout. **No Milestone 3 phase has begun and none is authorized**: no
publication, approval, CLI, live-metadata, real-snapshot, or Milestone 3 work exists, and no S7 or
Milestone 3 contract exists. **No S5 selection and no reserve is a published or owner-approved
input** — S6 creates only a `proposed` manifest, over fixtures. That audit, its bounded corrections,
and its rereviews are now complete, and **Milestone 2 is formally closed** (Decision 026). See
"Milestone closure state" above and "Current stage" below.

## Completed stages

- **Stage S3** — candidate/selection/manifest schema (migration `0009`). Governed by Decision 016.
- **Stage S4** — deterministic constrained entity-selector core (S4.1,
  `src/disclosure_drift/sec/entity_selector.py`) and candidate-snapshot reconstruction plus
  entity-selection persistence (S4.2, `src/disclosure_drift/sec/entity_selection_store.py`).
  Governed by Decision 013 §5 and Decision 017. Checkpointed at `m2.3-s4-complete` (`e7157aa`).
  Persists an **entity-only running draft**; `run_state` stays `running` because accession-level
  objective terms (S5) can still change the joint optimum — see
  `Docs/architecture_map.md` §5 and §6.
- **Migration `0010`** — seeds the frozen `PILOT_QUOTA_POLICY_VERSION` (Decision 017), additive only.
- **pytest-performance maintenance phase** — accepted. Nonblocking; see the maintenance note below.
- **S5 architecture preflight** — complete. Concluded that no migration-`0009` schema contradiction
  blocks S5, and that Decision 018 must exist before S5.1 implementation begins. The preflight's
  proposed rules were **proposals**, not policy; those the project owner approved are now frozen by
  Decision 018, and the record — not the preflight — is authoritative for each of them.
- **Decision 018** — approved by project owner (2026-07-28),
  `Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md`. Freezes Stage S5 accession
  selection policy: roles, caps, entity accession floors, the applicability-aware evidence penalty
  within the unchanged Decision 013 §5 objective order, canonical dashed accession identity and the
  tie-break formula, the deterministic `selected_order` rule, S4-draft disposition and a distinct
  content-derived S5 joint run, families and linked-amendment coverage, cross-cutting quota
  operationalization, node-limit/failure/retry semantics, and the S5.1–S6 stage boundaries.
  **Policy only — it authorizes no implementation and no repository code changed with it.**
- **Decision 019** — approved by project owner (2026-07-28),
  `Docs/Decisions/decision_019_m23_s5_storage_to_pure_input_mapping.md`. Approved **as written**,
  after a final independent audit whose recommendation was
  `ACCEPT_DECISION_019_FOR_OWNER_APPROVAL` (no ambiguities, no implementation blockers, no scope
  violations, total and deterministic mappings, compatible with the accepted S5.1 core, no required
  DDL, no new quota deferral, governance consistent); the audit's four documentation-precision notes
  are nonblocking and alter no approved mapping. Freezes the four storage-to-pure-input mappings —
  amendment-linkage evidence conversion, multi-registrant evidence aggregation, explicit pre-study
  support provenance, and former-name identity-evidence conversion — plus the snapshot-freeze
  obligations and the run-identity content they contribute. **Policy only — it modifies no accepted
  S5.1 artifact, authorizes no implementation, and no repository code changed with it.**
- **Stage S5.1** — pure accession-candidate and joint entity-accession selection core
  (`src/disclosure_drift/sec/accession_selector.py`) with its adversarial in-memory tests
  (`tests/unit/test_m23_accession_selector.py`). Governed by Decision 013 §5 and Decision 018.
  **Accepted** by project-owner adjudication and independent recheck. It remains the **sole
  methodological selector**; S5.2 adds no second implementation of any policy function.
  Committed at `m2.3-s5-complete` under the combined S5.1–S5.3 boundary.
- **Stage S5.2** — frozen accession reader, deterministic S5 run identity, transactional
  persistence, and deterministic reconstruction
  (`src/disclosure_drift/sec/accession_selection_store.py`) with
  `tests/unit/test_m23_accession_selection_store.py`. Governed by Decision 018 and Decision 019.
  **Accepted.** Also carries additive migration `0011` (INSERT-only, no DDL), the frozen
  `PILOT_JOINT_SELECTOR_POLICY_VERSION` constant, the five Decision 018 §21 reason codes, and the
  bounded migration-catalog test updates. Two defects found by independent review were corrected
  before acceptance: the stored-evidence-level run-identity correction, and the same-ID
  reconstruction integrity correction (both public entry points now fail closed on the same stored
  identity corruption, through one centralized comparison over every
  `JointSelectionRunIdentity` field).
- **Stage S5.3** — independent adversarial review of S5.1 and S5.2 together, and the combined
  S5.1–S5.3 acceptance checkpoint. **Complete and owner-accepted 2026-07-29.** Final independent
  recommendation **`ACCEPT_M23_S5_3_CHECKPOINT`**; final accepted suite **1661 passed, 1 skipped**;
  no implementation defects, no acceptance blockers, no scope violations. Checkpointed at
  `m2.3-s5-complete`.
- **Decision 020** — approved by project owner (2026-07-30),
  `Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md`. Freezes the Stage S5.4 architecture:
  quota-contribution membership published from the sole accepted S5.1 witness derivation; reserves,
  contributions, and members written inside the S5 run's single `running` window; reserves as
  subordinate content under the accepted S5 run ID with the input-schema version unchanged; the exact
  migration-`0012` DDL (§8.2); the enforcement-layer test scoping (§8.3); one authorized reason code;
  and the nine owner rulings (§14). Its **§19 records final acceptance of the implemented stage**.
- **Stage S5.4** — quota-contribution membership, reserve packages, replacement signatures, durable
  no-compatible-reserve dispositions, their persistence inside the existing single transaction, and
  fail-closed reconstruction. Governed by Decision 013 §6, Decision 016 §7, and Decision 020.
  **Complete and owner-accepted 2026-07-30.** Final independent recommendation
  **`ACCEPT_M23_S5_4_FOR_CHECKPOINT`**; final accepted suite **1899 passed, 1 skipped**; no acceptance
  defects, no ambiguities, no checkpoint blockers, no scope violations. Delivered across exactly twelve
  authorized paths: the additive S5.1 membership output in `sec/accession_selector.py`; the new pure
  `sec/reserve_selector.py`; contribution, member, reserve, and disposition persistence and
  reconstruction in `sec/accession_selection_store.py`; the one new reason code
  `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` in `reasons.py`; DDL-only migration
  `0012_m23_selection_entity_reasons.sql` reproducing the Decision 020 §8.2 SQL byte-for-byte; and
  seven test modules. Four defects found by independent review were corrected before acceptance
  (bounded fixes **D1, T1, T2, T3**): the filing-year derivation was centralized on the accepted-core
  helper so the reserve module holds no parser of its own and malformed non-null stored dates raise
  `GateFailureError`; persisted signatures gained independent recomputation from normalized content in
  repository tests; and multi-witness load-bearing entity contributions gained non-vacuous coverage.
  The accepted S5 selection, objective, quota results, amendment families, `selection_input_sha256`,
  and `selection_run_id` are **unchanged**, verified by running the pre-S5.4 code and the accepted code
  over the same frozen snapshot. Checkpointed at `m2.3-s5.4-complete`, supplementing the immutable
  `m2.3-s5-complete`.
- **Decision 021** — accepted by project owner (2026-07-30),
  `Docs/Decisions/decision_021_m23_s6_manifest_construction.md`, **v0.5**. Freezes the Stage S6
  architecture: every digest preimage, the root, `manifest_id` and its six-field immutability, the
  circularity exclusions and commitment closure, eligibility, the proposed-only boundary,
  reconstruction and replay, the thirteen-block document contract with the exhaustive 81-item §10
  crosswalk, the S4/S5 boundary, the complete eight-block migration-`0013` SQL and its nine digests,
  the §15.5 append-once and identity guarantee, the no-new-surfaces and CLI-narrowing rulings, and
  the S7–S10 boundary. Accepted on the fourth focused independent governance review
  (`ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL`); the first three each returned
  `REQUIRES_OWNER_CLARIFICATION`. **Remains the controlling S6 architecture record.**
- **Decision 022** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_022_m23_s6_reserve_rank_applicability.md`. The owner clarification of
  crosswalk item 46: reserve rank is applicable **once per persisted reserve package** and is
  **structurally not applicable** for a selected target carrying the persisted
  `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition instead; item 70 remains the total per-target
  coverage requirement; no synthetic package or invented rank may be created or serialized. Issued
  after a fresh independent S6 implementation audit correctly stopped under Decision 021 §§21 and
  13.3 and referred the conflict rather than resolving it. **Supersedes and amends nothing.**
- **Decision 023** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md`. Records **formal owner
  acceptance of Stage S6** (`M23_STAGE_S6_ACCEPTED_AND_COMPLETE`) on the final independent
  recommendation `ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING`; **ratifies three
  forced-consequence test paths**; records **four accepted nonblocking limitations O1–O4**; and
  authorizes exactly one commit, one push, the annotated tag `m2.3-s6-complete`, and one tag push.
  **Adds no architecture and reopens no ruling**; grants no Stage-S7 and no Milestone 3 authority.
- **Stage S6** — deterministic pilot-manifest construction, terminal result identity, and the
  publication boundary. Governed by Decision 013 §§7–8, Decision 016 §§1, 5, 8, Decision 018 §22,
  Decision 020 §§9, 11, 14.4, milestone plan §10/§16, and — controlling — Decision 021 v0.5 with
  Decision 022. **Complete and owner-accepted 2026-07-31.** Implemented under separately issued
  bounded authorizations, corrected once under Decision 022, rereviewed independently
  (`ACCEPT_M23_S6_IMPLEMENTATION_FOR_ACCEPTANCE_REVIEW`), and accepted on the final independent
  recommendation **`ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING`** — no methodological findings, no
  implementation defects, no test defects, no outstanding owner clarifications, no acceptance
  blockers. Final accepted suite **2324 passed, 2 skipped**, reproduced under the parallel and
  alternate-temp-root runs alike. Delivered across **ten** implementation and test paths: the new
  pure `release/pilot_manifest.py`; the new `sec/pilot_manifest_store.py`; DDL-only migration
  `0013_m23_manifest_lifecycle_guards.sql`, reproducing the Decision 021 §15.1 eight-block SQL
  byte-for-byte over a 10939-byte, 186-line statement region with all nine §15.3 digests; the two new
  S6 test modules; bounded edits to `test_m23_pilot_schema.py` and `test_migration_provenance.py`;
  and the three ratified forced-consequence test paths `test_storage_catalog.py`,
  `test_m23_entity_selection_store.py`, and `test_m23_accession_selection_store.py`. Unchanged and
  verified unchanged at acceptance: all 81 crosswalk rows and their totals (D 42 / T 30 / X 8 /
  S9 1 / S10 0 / unclassified 0), every hash preimage, all eight triggers, migrations `0009`–`0012`,
  and all accepted S4 and S5 behaviour. Checkpointed at `m2.3-s6-complete`, supplementing the
  immutable `m2.3-s5-complete` and `m2.3-s5.4-complete`.

- **Decision 024** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_024_m2_m3_boundary_governance.md`. The **Milestone 2 / Milestone 3
  boundary**: accepted S6 is the final implementation stage of Milestone 2; Milestone 2 consists of
  M2.1, M2.2, and M2.3 through accepted S6; **Milestone 2 is implementation-complete but not formally
  closed**, open only for the final integrated audit, bounded correction, rereview where required,
  and closeout; and the obligations formerly called S7–S10 move **intact** into Milestone 3 as
  **M3.1–M3.4**, with a new **M3.5** for integrated real-pilot acceptance and Milestone 3 closeout.
  Its §5.2 traceability table records every phase's inherited gates, prohibitions, required owner
  decision, required validation, and implementation-authorization status — **`NO` for every phase**.
  Formal outcome **`M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED`**. **Governance only**: it changed no
  production, test, migration, or configuration byte, granted no implementation authority, and
  authorized one commit and one push with **no tag**.

- **Decision 025** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_025_integrated_audit_documentation_corrections.md`. Records the **final
  independent integrated Milestones 1 and 2 audit** result `REQUIRES_BOUNDED_INTEGRATED_FIXES`, with
  **nine categories confirmed `INTEGRATED_ACCEPTANCE_CONFIRMED`** (Milestone 1, M2.1, M2.2, M2.3,
  Milestone 2 integrated, governance, reproducibility, security and leakage, test adequacy), the
  Milestone 3 boundary `GOVERNANCE_READY_IMPLEMENTATION_NOT_AUTHORIZED`, and the single
  `PROJECT_DOCUMENTATION_CLASSIFICATION: REQUIRES_BOUNDED_FIX`. **The audit found no implementation,
  methodology, migration, hashing, selection, manifest, leakage, security, or test defect.** It
  authorizes the bounded documentation correction — `Docs/sec_data_dictionary.md` extended from
  migrations `0001`–`0008` to `0001`–`0013`, covering the 22 `pilot_*` tables and the `0012`/`0013`
  trigger inventories — plus deviation-register navigation to `Docs/preregistration.md` §25. Formal
  outcome **`INTEGRATED_AUDIT_DOCUMENTATION_CORRECTIONS_AUTHORIZED`**. **Documentation and governance
  only**: no schema, migration, code, test, configuration, methodology, hash, or accepted decision
  outcome changed, and no implementation authority granted. It also records the **independence
  disclosure** that the same conversation authored Decisions 023 and 024, which establishes no
  technical defect but requires a **fresh independent verification** before closeout.

- **Decision 026** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md`. The **formal closeout of
  Milestones 0, 1, and 2**, recorded on the final fresh independent rereview
  `ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT` with **no closeout
  blocker remaining**. It records the closeout baseline, the eleven-step review chain from the
  stage-level implementation reviews through the explicit **Milestone 0** standalone audit, all
  sixteen final classifications, and what each milestone's closure covers: **Milestone 0** (§6)
  research question and framing, novelty review, preregistration, frozen cohorts, frozen outcome
  cutoffs, bootstrap seed `20260725`, the leakage register, the deviation register and D001, and the
  accepted governance foundation; **Milestone 1** (§7) repository and packaging foundation,
  configuration, cohort mirror enforcement, CLI and exit-code behaviour, offline safety, and secret
  and hygiene controls; **Milestone 2.1** (§8) offline SEC policy, identifier and temporal policy,
  response and rate-limit policy, the storage/provenance/schema-drift/release/forecast boundaries,
  and the CompanyFacts-disabled and Frames-prohibited policy; **Milestone 2.2** (§9) controlled
  live-metadata readiness, SEC identity requirements, transport isolation, deterministic request
  governance, raw-store provenance, and offline test and CI boundaries; and **Milestone 2.3 through
  S6** (§10) deterministic candidate and snapshot identity, entity and accession selection, reserves
  and dispositions, persistence, reconstruction and replay, selection-result sealing, manifest
  construction, canonical serialization, lifecycle enforcement, verification and atomicity, and the
  accepted limitations. Formal outcome **`MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`**. It
  authorizes the three annotated completion tags `m0-complete`, `m1-complete`, and `m2-complete` at
  the closeout commit, confirms every existing implementation-stage tag immutable, leaves the
  **inherited limitations register active** (§12), records the nonblocking `pilot_reserves`
  PK-superset UNIQUE presentation observation as requiring no correction (§13), and makes
  **`MILESTONE_3_MASTER_PLANNING`** the next authorized action. **Governance only**: it changed no
  production, test, migration, configuration, or CI byte, edits no earlier decision, and **grants no
  Milestone 3 implementation authority** — closure satisfies only the precondition Decision 024 §8
  imposed, and all five of that record's entry conditions still apply in full.

- **Decision 027 v0.1 (historical initial planning text)** — accepted by project owner (2026-07-31),
  `Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md`. The **Milestone 3 master
  plan and operational-readiness design**. It records the exact Milestones 0–2 closeout baseline
  verified live; confirms **Decision 024 controlling** for the M2 → M3 obligation transfer and
  **Decision 026 controlling** for the closeout; fixes the planned **M3.1–M3.5** phase map with each
  phase's network permission and completion token; introduces the **M3.1A / M3.1B** planning
  subdivision, which creates no new milestone and no new phase and takes no tag for M3.1A; requires a
  **documentation-first operator runbook** before any live access; requires the **complete offline
  rehearsal to pass before the first SEC request**; requires **one execution receipt per live
  command**; froze the **seven operational templates then present in v0.1**; requires the
  **Milestone 3 limitations register**, seeded with every inherited limitation and closing none;
  fixes the **sequential model
  and validation policy** — Opus Max for architecture, contracts, owner decisions, consequential
  methodology, focused independent reviews, exact-root approval preparation, and final integrated
  acceptance; Sonnet High or Max for bounded implementation; **Haiku nowhere on the critical path** —
  with targeted checks during implementation and one full suite plus every repository gate at each
  phase end; fixes the **one-implementation-commit-per-phase default** and the **annotated-tags-only,
  after-independent-acceptance-only** tag policy with the frozen future names `m3.1-complete`,
  `m3.2-complete`, `m3.3-complete`, `m3.4-complete`, and `m3-complete`; fixes the **focused
  independent-review policy**; confirms that **request-volume values may not be invented**, that a
  derivable count is computed from accepted offline inputs and reproduced, and that an underivable one
  is written `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` with its exact formula, its count
  dependencies, the future zero-request planning command, a hard ceiling, and mandatory owner approval
  before network enablement; confirms that **operational receipts are outside the accepted S5 and S6
  substantive identity graphs**; prohibits any execution receipt, receipt digest, timestamp, request
  count, response total, path, SEC identity, or operational state from contaminating candidate
  identity, selection identity, `selection_result_sha256`, any component digest,
  `root_manifest_sha256`, or `manifest_id`; and prohibits any full SEC identity, secret, personal
  path, raw response body, filing text, outcome value, or restricted substantive payload from
  appearing in a receipt. Formal outcome
  **`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`**. **Governance and documentation
  only**: it changed no production, test, migration, configuration, or CI byte, created no runtime
  code, CLI surface, or database table, created **no implementation contract**, and **grants no
  Milestone 3 implementation authority** — planning a phase is not authorization to begin it, all five
  Decision 024 §8 entry conditions still apply per phase, and implementation authorization remains
  `NO`. It authorized one planning/governance commit and one push, and **no tag**.
  **Next authorized action: `INDEPENDENT_M3_MASTER_PLAN_REVIEW`.**

- **Decision 027 v0.2** — accepted by project owner (2026-07-31), the **corrected** Milestone 3
  master plan. **The record has been `ACCEPTED` since v0.1; v0.2 does not change that and creates no
  second numbered decision.** v0.2 applies eleven bounded owner corrections issued after the required
  independent review of v0.1, recorded in its **§0 revision history**, superseding only the affected
  v0.1 operational-planning language: (1) **M3.1 rehearses acquisition only** — the snapshot,
  selection, reserve, sealing, manifest, and root scenarios move to **M3.3A**, under the frozen rule
  that **no scenario may be placed in a phase that lacks the production path it exercises**;
  (2) **M3.2 becomes two sequential windows** — M3.2A bootstrap, then transport disabled, objects
  frozen, dependent references **derived** from them, a second zero-request plan, and a **second
  exact owner approval**, then M3.2B — with **the 10% contingency withdrawn**; (3) **M3.3A** builds
  and rehearses the candidate-snapshot builder before **M3.3B** freezes anything real; (4) **M3.4
  always requires a bounded contract and is never documentary** — M3.4A validates a minimal
  approval-recording entry point against synthetic catalogs, M3.4B invokes it once after explicit
  approval, and **manual SQL against the real catalog is prohibited**; (5) the v0.1 derived counts,
  subtotal, plan hash, and maximum-attempt total are **withdrawn** — faithful to the accepted planner
  but **not** to Decision 013 §1 — and the resulting **`CURRENT_PLANNER_DISCREPANCY` is recorded,
  unresolved, and blocks Gate F**, with Decision 013 byte-unchanged; (6) **`A_max = 12` and
  `planned × 12` are withdrawn** — maximum reachable physical attempts is **derived per route from
  the implemented response-policy state machine and independently tested**; (7) **one** receipt
  integrity identity, `receipt_id`, with `receipt_content_sha256` **removed**; (8) every receipt field
  classified **required / conditionally required / prohibited by invocation mode**; (9) `rehearsal`
  and `dry_run` receipts report **zero actual network counts**, with simulated totals in the rehearsal
  evidence report; (10) a **two-layer evidence model** — the public repository tracks blank templates,
  planning records, the limitations register, and a new **evidence index** carrying artifact type,
  phase, status, SHA-256, and a non-sensitive reference identifier, while **completed operational
  evidence lives in an owner-controlled private evidence root outside the repository**; and (11) the
  claim that **any regeneration necessarily creates a new root is withdrawn as false** — unchanged
  governed state plus byte-identical canonical serialization produces the **same** root, an
  independently re-derived identical root **remains the same approved value**, and only a differing
  root, changed governed state, or a superseding manifest requires a new packet. **Governance and
  documentation only**: no production, test, migration, configuration, CI, or `.gitignore` byte
  changed; `Docs/Decisions/decision_013_pilot_selection_mechanics.md` is byte-unchanged; no runtime
  code, CLI surface, database table, or implementation contract was created; and **no Milestone 3
  implementation authority is granted**. It authorized one governance-only correction commit and one
  push, and **no tag**. **Next authorized action: `INDEPENDENT_M3_MASTER_PLAN_REREVIEW`.**

- **Decision 028 — accepted 2026-08-01.** The Decision 027 v0.2 rereview did not pass. Decision 028
  records the bounded reconciled corrections: planner policy
  `quarterly-index-instances/2.0`; the corrected A1–A12 matrix; future reason codes
  `SEC_REQUEST_CEILING_EXHAUSTED` and `SEC_ACQUISITION_INTERRUPTED`; ceiling equality; read-only
  M3.1 recovery inspection; `m3-execution-receipt/2.0`; corrected request-budget arithmetic; and the
  three-layer M3-L11 protection. It preserves Decision 013 and Decision 024, creates no contract,
  and grants no implementation or network authority. Its fresh independent rereview returned
  `INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`; formal outcome
  `M3_1_READINESS_CORRECTIONS_ACCEPTED`.

- **Milestone 3 master planning** — **complete at v0.2.** Delivered under Decision 027 across fourteen
  planning documents plus the navigation and status updates they require:
  [`Milestones/milestone_03_master_plan.md`](milestone_03_master_plan.md) (five phases, 36 specified
  fields each, the request-volume policy, and the mandatory contents of every future phase contract);
  [`Docs/m3/operator_runbook.md`](../Docs/m3/operator_runbook.md) (31 sequential Mac steps, every
  command labelled `AVAILABLE NOW` or `PLANNED — NOT YET IMPLEMENTED`);
  [`Docs/m3/offline_rehearsal_spec.md`](../Docs/m3/offline_rehearsal_spec.md) (**two** rehearsals —
  **A1–A12** acquisition at M3.1A before the first SEC request, and **E1–E8** execution at M3.3A
  before the real snapshot freeze — each scenario with setup, command, response, reason code,
  persisted state, files, receipt, rollback, recovery, and validation; **specified, neither
  implemented, and neither run**);
  [`Docs/m3/execution_receipt_spec.md`](../Docs/m3/execution_receipt_spec.md) (the proposed
  `m3-execution-receipt/2.0` design, one integrity identity, corrected field timing and per-mode
  classification —
  **creating no code and no table**);
  [`Docs/m3/limitations_register.md`](../Docs/m3/limitations_register.md) (**37 active entries and one
  recorded as closed**, including active **M3-L11** private-evidence protection and active
  **M3-L12** planner-v2 implementation; their owner rulings are recorded but neither is closed); and
  the **eight** templates
  under [`Docs/m3/templates/`](../Docs/m3/templates/request_budget.md), including the new public
  [`evidence_index.md`](../Docs/m3/templates/evidence_index.md). **No implementation, no contract, no
  network access, no metadata acquisition, no snapshot, no pilot run, no manifest, no approval, and no
  publication occurred; at that planning checkpoint no M3.1 contract had been drafted.**

## Bounded documentation fix — complete, rereviewed, and accepted

The fresh independent verification required by Decision 025 §§8–9 has **run**. It confirmed
**Decisions 023, 024, and 025 independently** — each `INDEPENDENT_ACCEPTANCE_CONFIRMED` — and found
**no methodological, implementation, test, or governance defect**: the migration chain, the nine
migration-`0013` digests, the 81-item crosswalk and its totals, the ten delivered S6 paths and the
three ratified forced-consequence test paths, the obligation transfer into M3.1–M3.5, the deviation
register, and the correction commit's nonchange were all reproduced independently rather than
inherited. It returned **`REQUIRES_BOUNDED_VERIFICATION_FIXES`** on exactly two documentation items:

- **DOC-1 (the closeout blocker).** `Docs/sec_data_dictionary.md` gave 21 of the 22 `pilot_*` tables
  the complete per-table schedule Decision 025 §6.1 requires;
  **`pilot_projection_recovery_events`** carried only its name, state class, and no-writer status.
- **DOC-2 (cosmetic, pre-existing).** Blank lines before registry rows `023`, `024`, and `025`
  terminated the Markdown Index table.

**Both are now corrected**, together with three non-material precision notes, under the authority
Decision 025 §6.1 already granted. **No new decision record was required and none was created.**
`Docs/sec_data_dictionary.md` gains §13.5 covering `pilot_projection_recovery_events` in full —
migration `0009`, purpose, owning stage, `Operational-only` state class, 12 columns, PK `event_id`,
FK `manifest_id` → `pilot_manifest_versions`, the exact uniqueness position, every material CHECK,
the append-only lifecycle and both immutability triggers, writer none, reader none, digest role
none, the explicit exclusion from every manifest, component-digest, selection-result, root, and
manifest-identity input, and an explicit future-stage boundary. **All 22 `pilot_*` tables now carry
the complete schedule**, and the count distinction is preserved: **21** introduced by migration
`0009`, **one** more by `0012`, **22** through `0013`.

**Documentation only.** No production, test, migration, configuration, CI, methodology, schema,
hash, or database-behaviour byte changed; Decisions 021–025, every completed contract, and
`Docs/preregistration.md` are byte-unchanged; no tag was created or moved.

**The independent rereview of this fix has since run and passed.**
`FRESH_INDEPENDENT_BOUNDED_DOCUMENTATION_REREVIEW` returned
**`ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT`**, confirming
`INTEGRATED_ACCEPTANCE_CONFIRMED` for Milestone 0, Milestone 1, M2.1, M2.2, M2.3, and Milestone 2
integrated; `INDEPENDENT_ACCEPTANCE_CONFIRMED` for Decisions 023, 024, and 025; and
`VERIFIED_COMPLETE` for the data dictionary, the deviation register, project governance,
reproducibility, security and leakage, test adequacy, and documentation — with closeout readiness
`READY_FOR_FORMAL_CLOSEOUT` and **no remaining closeout blocker**. It also explicitly completed the
outstanding **Milestone 0** closeout classification. **Milestones 0, 1, and 2 are now formally
closed** ([Decision 026](../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md)). Its one
nonblocking presentation observation — `pilot_reserves` carrying a UNIQUE that is a superset of its
own primary key, present so the run/snapshot-scoped children have a declared composite FK target —
affects no schema correctness, reproducibility, methodology, or closeout and required no correction
(Decision 026 §13). **That statement was accurate when written and is now historical.** Milestone 3
completed its M3.1 phase under `contracts/m3_1.md`: the M3.1 implementation is owner-accepted
(accepted Decision 031, 2026-08-03) and checkpointed at the annotated `m3.1-complete` tag; the
M3.2 contract exists only as an unaccepted draft (`contracts/m3_2.md`), and M3.2 remains
unauthorized and not begun.

## Current stage

**Milestones 0, 1, and 2 are `FORMALLY_CLOSED` (Decision 026,
`MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`), tagged `m0-complete`, `m1-complete`, and
`m2-complete` at the closeout commit. Milestone 3 master planning is `COMPLETE` at **Decision 027
v0.2** (`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`). Decision 028 is accepted after
`INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`, and **Decision 029 is accepted
(`M3_1_REHEARSAL_COMPLETENESS_AND_REASON_SEMANTICS_ACCEPTED`, owner approved 2026-08-02)**. The
bounded M3.1 contract is **accepted** with `IMPLEMENTATION_AUTHORIZATION: YES`, and the M3.1
implementation is **OWNER-ACCEPTED** (accepted [Decision 031](../Docs/Decisions/decision_031_m3_1_acceptance.md),
2026-08-03, outcome `M3_1_ACCEPTED_AND_COMPLETE`). The Decision 029 §11 code
remediation is implemented, the implementation is frozen at
`970e050deb06910adcde8588101564beb7d19c74`, and the **first durable §17 review** by a non-author
session is complete, passed with verdict `M3_1_SECTION_17_REVIEW: PASS`, and is owner-accepted, its
artifact committed governance-only at `66e4c5433a393815c74f9e3087300613a516e2fb`. Decision 029 §12
step 8 prepared and validated the external evidence root and operator manifest; the step 9
operational rehearsal ran once on 2026-08-03 and passed, emitting the M3.1A token; **step 10 ran
the deterministic zero-request M3.2A plan twice on 2026-08-03 with byte-identical results**
(request-plan SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; q = 70;
75 planned unique logical requests; 801 maximum physical attempts); **step 11 rendered the
canonical budget display and the owner approved the exact hard request ceiling 801 on
2026-08-03**, deliberately leaving three response-outcome expectations unresolved as
`EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN`; **accepted Decision 030 resolved the sole
step-12 hygiene blocker** by a provably non-substantive one-path provenance redaction of the §17
review artifact (verdict `M3_1_SECTION_17_REVIEW: PASS` unchanged; `make hygiene` passes with zero
findings); and **step 12 is signed and complete**: the signing preflight validated the SEC contact
identity at the canonical boundary (value never displayed), synchronized `main`
(`HEAD == origin/main` at `55cf244a00428fbc8fa38d7b70af1bac8a7c45e9`), and recorded the operator
acknowledgement, and the **owner-signed Gate F checklist** (result `PASS`; owner Joseph Nihill,
project owner acting through the ChatGPT owner decision; 2026-08-03) is immutable private
evidence, SHA-256 `34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc`, backed up
and publicly referenced in the evidence index. **Step 13 was owner-authorized and completed on
2026-08-03**: the Gate F readiness token was emitted and recorded exactly once as immutable
private evidence (SHA-256 `b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e`,
bound to the signed checklist `34fc0567…`, the plan `19be7bdc…`, the budget `2d453e0b…`, the
ceiling 801, and the checklist baseline `55cf244…`), the after-step-13 backup verified, and the
owner's evidence-index attestation of 2026-08-03 is recorded in the public index. **Step 14
completed and passed on 2026-08-03**: the independent M3.1 acceptance review by a fresh
non-author session returned `M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS` — artifact
`Docs/m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md`,
SHA-256 `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`, committed
governance-only at `24fba32413bb6c5dade60a64182e42510afe6f88` — with all validation gates green
(2739 passed, 1 pre-existing skip; the transport test ran), zero BLOCKER and zero MAJOR findings,
and three MINOR findings the owner accepted as nonblocking. **The owner accepted M3.1 on
2026-08-03** (verbatim instrument recorded by accepted
[Decision 031](../Docs/Decisions/decision_031_m3_1_acceptance.md), outcome
`M3_1_ACCEPTED_AND_COMPLETE`), and **step 15 records that acceptance in this governance-only
commit**. **Step 16 completed on 2026-08-03**: the annotated `m3.1-complete` checkpoint tag was created at
the acceptance commit and pushed (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled
target `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`, verified locally and remotely). **Step 17
completed on 2026-08-03** under the owner's explicit step-17 authorization: **M3-L11 and M3-L12
are `CLOSED`** on their complete closure-evidence lists, and the **bounded M3.2 contract is
drafted** at [`contracts/m3_2.md`](contracts/m3_2.md) with status `DRAFT — PENDING OWNER REVIEW
AND ACCEPTANCE` — completing the Decision 029 §12 seventeen-step sequence. **The token records
readiness only: Gate F execution has not begun, M3.2 implementation is not authorized, live SEC
access remains not authorized, no acquisition has begun, and no operational catalog exists. The
M3.2 contract — reviewed, corrected (accepted Decision 032), and rereviewed fresh with no
subagents (`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS`, artifact SHA-256 `91235a1a…`,
rereview commit `3069b03e…`) — is ACCEPTED unchanged at T1 (accepted Decision 034, 2026-08-04);
T1 grants no later gate, and the next authorized action is preparation and owner review of the
bounded T2 implementation-authorization packet.**
Nothing below is an active work item — the rest of this section is
the accepted record of the last implementation stage Milestone 2 closed over.

**M2.3 Stage S6 (pilot manifest construction, terminal result identity, and the publication
boundary) — complete, owner-accepted, and checkpointed.** Stage S5 is finished end to end: S5.1,
S5.2, and the combined S5.1–S5.3 checkpoint were owner-accepted 2026-07-29, and **S5.4 was
owner-accepted 2026-07-30** and checkpointed at `m2.3-s5.4-complete`. **Stage S6 was owner-accepted
2026-07-31** through
[Decision 023](../Docs/Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md) and
checkpointed at `m2.3-s6-complete`. **There is no active implementation contract**: every contract in
`Milestones/contracts/` is now `ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO`.

**What S6 delivered.** The eight component digests and `root_manifest_sha256` at their frozen
preimages; `selection_result_sha256` and its append-once sealing; `manifest_id` and its six-field
identity immutability; the complete thirteen-block pilot-manifest document, every one of the 81
atomic milestone-plan §10 items bound and asserted item by item; canonical JSON under
`DataTree.releases / "pilot"` with a content-derived filename; historical S5 reconstruction through
the accepted entry point; persistence of exactly one `proposed` manifest row atomically with its
document; public verification that re-derives everything and fails closed; write-free idempotent
replay; and DDL-only migration `0013` with its eight lifecycle, identity, replacement, and deletion
guards. **S6 creates only a `proposed` manifest, over fixtures.** No real snapshot exists, no
candidate-snapshot builder exists, no production catalog exists, and no code path approves or
publishes anything.

**Three forced-consequence test paths were ratified at acceptance** (Decision 023 §4). The S6
contract authorized seven implementation paths; migration `0013` forced three further test edits —
`tests/unit/test_storage_catalog.py` (the canonical migration chain is asserted by exact version and
name), and `tests/unit/test_m23_entity_selection_store.py` and
`tests/unit/test_m23_accession_selection_store.py` (their accepted corruption fixtures built their
preconditions with plain `UPDATE`s that trigger 8 now refuses). The final independent acceptance
review found the authorization gap and referred it rather than resolving it; the owner ratified all
three retroactively. **No production path changed, no S4 or S5 methodology changed, and no assertion
was removed, weakened, relaxed, skipped, or xfailed**; the rewritten corruption fixtures are narrower
and more fail-closed than the code they replaced. **The delivered S6 path set is therefore ten**, and
the ratification covers three named paths only — it is not a general widening.

**Accepted nonblocking S6 limitations** (Decision 023 §7). None is a defect; none requires an
implementation change.

- **O1 — an empty sole-carrier crosswalk family fails closed.** Where a §10 item has more than one
  serialized carrier, an empty family is accepted; where a family is an item's sole carrier, an empty
  family raises `GateFailureError`, as Decision 021 §21 designs. **No accepted current S5 plan
  reaches that condition.** If a lawful future run ever does, it is referred for an owner ruling —
  never resolved by reclassifying an item, adding a category, or changing a count.
- **O2 — the release root is assumed owner-controlled.** `Path.write_text` follows a symlink
  pre-positioned at the content-derived output path. Symlink-resistant publication was never an
  accepted S6 requirement. Verification still fails closed on wrong bytes, and no database row
  survives a failed write.
- **O3 — a pre-existing artifact at the content-derived path is outside the transaction's
  ownership.** Atomicity governs artifacts the current operation created: a fault leaves no new row
  and no new file. A pre-existing file at that exact name is not deleted; wrong bytes fail
  verification and an authorized retry repairs it.
- **O4 — item-46 enforcement is consistent defence in depth.** The Decision 022 applicability check
  and the per-record completeness check agree on every document; neither is vacuous. Reserve rank
  remains substantively enforced for every real package.

**Owner clarification recorded 2026-07-31 — Decision 022.** A fresh independent S6 implementation
audit confirmed the earlier bounded corrections and found one further conflict: a lawful, accepted,
feasible, sealed S5 run with **zero compatible reserve packages** — every selected target instead
carrying one persisted `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition, the shape Decision 020 §7.1
rules nonblocking and migration `0012` accepts as complete — passed all seven Decision 021 §11.2
eligibility conditions and sealed normally, but was refused at document verification because
crosswalk item 46's `reserves.packages[].reserve_rank` leaf cannot exist with zero packages. The audit
correctly stopped under Decision 021 §§21 and 13.3 and returned `REQUIRES_OWNER_CLARIFICATION`.
[Decision 022](../Docs/Decisions/decision_022_m23_s6_reserve_rank_applicability.md) is
**`ACCEPTED — OWNER APPROVED 2026-07-31`** and is the controlling record for that one point: reserve
rank is applicable **once per persisted reserve package** and is **structurally not applicable** for a
target carrying the disposition instead; **item 70 remains the total per-target coverage
requirement**; and no synthetic package, `reserve_rank = 0`, `null`, `"N/A"`, placeholder, or invented
rank may ever be created or serialized. Decision 021 remains `ACCEPTED` and otherwise unchanged — the
81-item crosswalk, its counts, every preimage, `manifest_id`, canonicalization, migration `0013`'s
bytes, its nine digests, and its eight triggers are all untouched.

**Active blocker: none.** Decision 021 v0.5 is `ACCEPTED` (owner approved 2026-07-30), Decision 022
is `ACCEPTED` (owner approved 2026-07-31), and Decision 023 is `ACCEPTED` (owner approved
2026-07-31). Both required independent reviews ran and passed — the fresh independent S6 rereview of
the corrected tree (`ACCEPT_M23_S6_IMPLEMENTATION_FOR_ACCEPTANCE_REVIEW`) and the separate final S6
acceptance review (`ACCEPT_M23_S6_FOR_OWNER_ACCEPTANCE_RECORDING`), neither performed by a session
that wrote the work it reviewed. No S5, S5.4, or S6 blocker remains.

**S6 governance was accepted at v0.5, and gated the stage in three steps — all now satisfied.**
[Decision 021](../Docs/Decisions/decision_021_m23_s6_manifest_construction.md) records the project
owner's S6 rulings and freezes the resulting architecture: the exact canonical preimage of
`selection_result_sha256` and of all eight manifest component hashes plus `root_manifest_sha256`; the
four terminal component boundaries, with the migration-`0012` reserve dispositions bound into
`reserves_sha256`; the source-content, candidate-table, quota-definition, and **eleven-field**
selector-policy allowlists, with dependency-lock, code-commit, Python-runtime, configuration,
decision-authority, and source-plan identity as **six** required explicit arguments never inferred
from Git, the environment, the interpreter, or the working tree; the `manifest_id` derivation and the
**immutability after insertion of all six manifest identity fields**; eight circularity exclusions
plus the commitment closure; fail-closed manifest eligibility; the proposed-only boundary; **the
complete pilot-manifest document contract — thirteen mandatory blocks operationalizing
[`milestone_2_3_pilot_selection_plan.md`](milestone_2_3_pilot_selection_plan.md) §10, with no
substantive serialized field left unbound by the root; S6 defines and fixture-tests the schema, S9
supplies the exact real-data instance — and the **exhaustive item-by-item §10 crosswalk** in §13.2.1
covering all **81** atomic §10 items in four categories with a frozen machine-checkable count of 42
direct, 30 transitive, 8 operationally excluded, 1 deferred to S9, 0 deferred to S10, and **0
unclassified****; the **five-column** structural-fingerprint partition rule; explicit
classification of six residual schema columns; canonical JSON under `DataTree.releases / "pilot"`;
and the complete frozen **eight-block** SQL and nine digests of one authorized future migration
`0013_m23_manifest_lifecycle_guards.sql` (§§15.1, 15.3), together with the **§15.5 append-once and
identity guarantee**. Its §3 records the **seven** schema gaps observed directly: `selection_result_sha256` is writable, overwritable, and clearable on any run in
any state **and a run can be inserted already `feasible` and already sealed**;
`pilot_manifest_versions` accepts — and approves — a manifest over a `running` or `infeasible` run,
including the permanently-`running` S4 draft; **no existing trigger protects any manifest identity
column**; **`INSERT OR REPLACE` rewrites a manifest row wholesale past every guard**, because every
existing manifest trigger is `BEFORE UPDATE` or `BEFORE DELETE` and SQLite fires no delete trigger for
replacement unless `PRAGMA recursive_triggers` is on, which this repository never sets; and — added
at v0.5 — **`pilot_selection_runs` itself is replaceable, deletable, and re-identifiable**, having no
delete guard of any kind and no trigger naming any identity column, so a sealed digest can be cleared
by `INSERT OR REPLACE`, the run removed by `DELETE`, and `selection_run_id`, `snapshot_id`, or
`selection_input_sha256` rewritten by direct `UPDATE` under either `recursive_triggers` setting.
**It authorized no implementation by itself.** Stage S6 required, in order: (1) a focused
independent governance **review of v0.5** of Decision 021 and the S6 contract — **SATISFIED
2026-07-30**, recommendation `ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL`; (2) owner acceptance of
Decision 021 v0.5 recorded in the registry — **SATISFIED 2026-07-30**; (3) a separately issued
bounded S6 implementation authorization — **SATISFIED**, issued and exercised, with one further
bounded correction authorized by Decision 022 §7.
[`Milestones/contracts/m23_s6.md`](contracts/m23_s6.md) is now `STATUS: ACCEPTED_AND_COMPLETE` with
`IMPLEMENTATION_AUTHORIZATION: NO`. It named **seven** authorized implementation paths — unchanged by
the v0.2, v0.3, v0.4, and v0.5 corrections, and preserved in the contract exactly as issued; the
delivered set is **ten**, the extra three ratified by Decision 023 §4. Every other path remains
prohibited.

**Four focused independent governance reviews have run; the fourth accepted the record.** The v0.1
review returned `REQUIRES_OWNER_CLARIFICATION` and produced owner corrections A–F, applied at v0.2;
**v0.2 was never independently reviewed**; v0.3 was reviewed on 2026-07-30 and also returned
`REQUIRES_OWNER_CLARIFICATION`, confirming the five-column fingerprint, the eleven-field §8.4 layer,
the acyclic digest graph, and the then-frozen four-block SQL and digests, while finding three
defects — an incomplete §10 crosswalk, identity immutability holding on the `UPDATE` path only, and
a "twelve blocks" heading over a thirteen-row table; v0.4 applied the two resulting owner
corrections; and the **v0.4 review**, also on 2026-07-30, returned `REQUIRES_OWNER_CLARIFICATION`
again — it accepted the crosswalk and the five-trigger manifest design and proved by direct probe
that `pilot_selection_runs` was still open to row replacement, deletion, and identity mutation.
**v0.5 applies the resulting owner ruling** and **withdraws the v0.4 five-block statement region, its
7436-byte and 129-line counts, and its concatenation digest `6bfb897c…` as a composition** — blocks
1–5 keep their exact bytes and their individual digests, which are **not** withdrawn — replacing it
with an **eight-block region of 10939 bytes over 186 lines**, digest `7f473802…`. The **v0.5 review** then returned
`ACCEPT_DECISION_021_V05_FOR_OWNER_APPROVAL` with **no governance blockers and no owner
clarifications required**, having reproduced all nine §15.3 digests from the record bytes, applied
the extracted SQL to a scratch `0001`–`0012` catalog, and run 318 adversarial assertions across all
four `recursive_triggers` × `foreign_keys` combinations. **The project owner approved Decision 021
v0.5 on 2026-07-30**, with one editorial correction to §13.2.1's explanatory arithmetic —
**74 original bullets producing 81 atomic requirements** (74 + 7 compound splits = 81) — which
changes no crosswalk row, numbering, category total, digest preimage, trigger, or SQL byte.

**The v0.4 open finding is now closed (Decision 021 §19.11).** Triggers 6, 7, and 8 —
`pilot_selection_run_replacement_guard`, `pilot_selection_run_delete_guard`, and
`pilot_selection_run_identity_guard` — close run replacement, deletion, and identity mutation
respectively. **Trigger 2 was deliberately not widened or renamed**, so the seal lifecycle and run
identity stay separate, independently testable invariants. Decision 021 **§15.5** now states the
guarantee without qualification: every new run begins unsealed, an existing run cannot be replaced, a
run cannot be deleted, the persisted run identity cannot change, sealing occurs only through the
guarded update on an already-`feasible` run, a sealed digest cannot change or clear, identical
restatement stays idempotent, `selection_input_sha256` cannot change before or after sealing, and
`selection_result_sha256` is therefore **append-once and remains recomputable from its persisted
preimage** across every direct SQLite write path. `selection_input_schema_version` needs no guard: it
is not a `pilot_selection_runs` column at all, and is supplied as the accepted code constant
`ACCESSION_SELECTION_INPUT_SCHEMA_VERSION`.

**v0.2 applied six bounded owner corrections** issued after the focused independent governance review
of v0.1 (recommendation `REQUIRES_OWNER_CLARIFICATION`, 2026-07-30): (A) six-field manifest-identity
immutability; (B) migration `0013` grows from three triggers to **four** (five at v0.4), with completely restated
normative SQL and digests — the v0.1 SQL and digests are **withdrawn**; (C) the complete manifest
document contract, citing milestone plan §10 explicitly, with the consequent extension of
`selector_policy_sha256`; (D) the structural-fingerprint partition rule; (E) explicit classification
of six residual schema columns; (F) the CLI narrowing and the complete S7–S10 boundary.

**v0.3 applies one further bounded owner correction, to the fingerprint only.** The structural tuple
widens from three columns to **five** — `region`, `state`, `observed_type`, `member_name`,
`record_path` — under the same partition-and-equality rule, and the v0.2 accepted limitation claiming
`observed_type` and `record_path` were unbound is **withdrawn and replaced** with an accurate one:
`parser_run_id` is used only for cross-run consistency checking and excluded from identity, duplicate
identical rows are collapsed, row order is excluded, and all five substantive structural fields are
bound. The eleven-field `selector_policy_sha256` layer of v0.2 is accepted and unchanged.

**v0.4 applies two further bounded owner corrections, issued after the focused independent governance
review of v0.3 returned `REQUIRES_OWNER_CLARIFICATION`.** (A) **The exhaustive milestone-plan §10
crosswalk** (§13.2.1): the review found that nineteen §10 items and four partially covered items were
neither serialized nor classified while the record claimed only two deliberate omissions, so §10 is
now enumerated **atomically** — **81 items**, every compound bullet split — each classified into
exactly one of four categories, with a frozen count of 42 direct, 30 transitive, 8 operationally
excluded, 1 deferred to S9, 0 deferred to S10, and **0 unclassified**; §13.2's "twelve blocks"
heading over a thirteen-row table is corrected to thirteen in the same pass. (B) **Migration `0013`
grows from four triggers to five**: the review demonstrated that six-field identity immutability held
on the `UPDATE` path only, because `INSERT OR REPLACE` rewrites a manifest row wholesale — identity,
lineage, all eight component digests, the root, and the state — past trigger 4 and past all four of
migration `0009`'s manifest triggers, including over an `owner_approved` manifest. Trigger 5,
`pilot_manifest_versions_replacement_guard`, closes all three uniqueness routes with `BEFORE INSERT`
predicates that hold under every pragma setting. **The crosswalk required no preimage change**, and
blocks 1–4 keep their exact bytes and digests; the **v0.3 four-block region, its 4990-byte and
88-line counts, and its concatenation digest `51151767…` are withdrawn**, replaced at v0.4 by a
five-block region of 7436 bytes over 129 lines — **itself since withdrawn as a composition at v0.5**
in favour of the eight-block region of 10939 bytes over 186 lines.

**v0.5 applies one further bounded owner ruling, issued after the focused independent governance
review of v0.4.** That review accepted the 81-item §10 crosswalk and the five-trigger manifest design
and proved by direct probe that `pilot_selection_runs` was still open on the three fronts the
manifest table had just been closed on: **row replacement**, **deletion**, and **identity mutation**.
Migration `0013` therefore grows from five triggers to **eight** — trigger 6
`pilot_selection_run_replacement_guard`, trigger 7 `pilot_selection_run_delete_guard`, and trigger 8
`pilot_selection_run_identity_guard`, the last holding `selection_run_id`, `snapshot_id`, and
`selection_input_sha256` immutable. **Trigger 2 is neither widened nor renamed**, and blocks 1–5 are
retained byte-for-byte with their individual digests, which are **not** withdrawn; only the v0.4
five-block *composition* is. Decision 021 **§15.5** now states the append-once and identity guarantee
without qualification, and **§19.11 is closed**.

**v0.1 was reviewed but never approved and never left `PROPOSED`; v0.2 was never independently
reviewed and never approved; v0.3 and v0.4 were each independently reviewed and neither was accepted
for approval. All five are the same record, so nothing downstream was invalidated by any revision.**
No earlier conclusion carried over: each review reached its own conclusion, and the v0.5 review —
the one covering the eight-trigger SQL and the §15.5 guarantee — is the one the owner approved.

**The former Stages S7–S10 are now Milestone 3; at the Decision 024 boundary none had begun.** S6 delivered machinery plus a
fixture-tested document schema. [Decision 024](../Docs/Decisions/decision_024_m2_m3_boundary_governance.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`) transfers those obligations **intact** into Milestone 3:
Gate F live-metadata readiness becomes **M3.1**; controlled metadata-only SEC acquisition with Gate H
becomes **M3.2**; the frozen real candidate snapshot, deterministic execution, the exact real-data
manifest, and **the CLI output deferred from S6** become **M3.3**; explicit owner approval of the
exact root hash becomes **M3.4**; and a new **M3.5** covers integrated real-pilot acceptance and
Milestone 3 closeout. **No gate, prohibition, owner ruling, validation requirement, identity,
methodology, or accepted limitation was removed, weakened, renumbered, or rewritten by the move.**
No later phase is reachable: no candidate-snapshot builder and no production catalog exists. **At the
Decision 024 boundary no S7 or Milestone 3 contract existed and no Milestone 3 implementation
existed** — the bounded M3.1 contract and its implementation came afterwards; **no Gate F has passed,
no live-metadata allowlist exists, and no Milestone 3 phase after M3.1 has begun.** Neither S6
acceptance nor the boundary record authorizes any of it — **assignment to Milestone 3 is not
authorization to begin Milestone 3** (Decision 023 §9; Decision 024 §8).

**Stage S5.4 is complete and accepted.**
[`Milestones/contracts/m23_s5_4.md`](contracts/m23_s5_4.md) is now **`STATUS: ACCEPTED_AND_COMPLETE`**
with **`IMPLEMENTATION_AUTHORIZATION: NO`** — it remains on record as Stage S5.4's scope statement and
authorizes no new S5.4 implementation, exactly as the S5.1 and S5.2 contracts do for their stages. Any
future S5.4 change requires a **new explicit owner authorization** and its own contract.
[`Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md`](../Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md)
remains **`APPROVED — OWNER APPROVED 2026-07-30`** and is the controlling record for reserves; its
**§19 records the final acceptance**, and its **§19.1 records the five accepted methodological
limitations**. It authorizes no further implementation.

**What S5.4 delivered and what it left frozen.** Quota-contribution membership is published from the
sole accepted S5.1 witness derivation as one additive immutable output, and is the only membership
source for every consumer. Reserves, contributions, members, and dispositions are written inside the
S5 joint run's single `running` window, in one transaction, with the `running -> feasible` transition
as its last statement. Reserves are subordinate content under the accepted S5 run ID; each package
carries its own content-derived `reserve_package_id`. Migration `0012_m23_selection_entity_reasons.sql`
was created DDL-only, adding one `STRICT` table and four triggers and reproducing the Decision 020 §8.2
SQL byte-for-byte. Unchanged and verified unchanged: the S5 selection and objective, quota results,
amendment families, `selection_input_sha256` and `selection_run_id`, migrations `0009`–`0011`, every
policy version, `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` (still `pilot-joint-selection-input/1.0`,
not bumped), and `selection_result_sha256` (still `NULL`).

**Accepted methodological limitations, recorded for monitoring** (Decision 020 §19.1). None is a
defect; none requires an implementation change.

1. **Cross-anchor amendment-family resolution** follows the accepted resolved-root accession identity
   with no added anchor-equality condition, so an entity can be credited with a linked-amendment
   contribution for a unit named after a different anchor. Deterministic, conservative, and fail-closed
   for reserve construction; it neither weakens contribution-set equality nor alters run identity.
2. **Provenance-oriented union member sets** may contain more members than a minimal witness would
   require — the accepted consequence of the witness-union ruling. No minimal-witness optimization is
   authorized.
3. **Exact target-selected versus complete-replacement bundle comparison may reduce reserve
   availability.** No discretionary trimming, subset search, or package optimization is authorized to
   obtain compatibility.
4. **The seven named signature contribution values are counts of achieved units, not Boolean
   presence.** Intentionally conservative; it further reduces availability.
5. **The schema-layer subset/superset/empty transition-test observation is nonblocking** and was
   independently validated at acceptance (exact accepted; subset, superset, and empty each refused).
   Adding repository coverage at that layer is optional and at the owner's discretion.

**The owner's recorded S5.4 rulings**, all reflected in Decision 020 §14 and honoured by the accepted
implementation: exactly one rank-1 reserve package per target where a compatible reserve exists (no
multiple ranks at M2.3); no-compatible-reserve is target-specific, review-required, nonblocking, and
neither infeasibility nor node-limit exhaustion; `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` stays
`pilot-joint-selection-input/1.0`; `selection_result_sha256` stays `NULL` through S5.4; one additive
immutable S5.1 membership output; every selected entity including controls is a reserve target; a
replacement CIK may serve different targets, at most once per target, with no global uniqueness and no
cross-target assignment problem; exactly one new reason code, `REVIEW_PILOT_NO_COMPATIBLE_RESERVE`
(`REVIEW_PILOT_RESERVE_POOL_EXHAUSTED` is **not** authorized); and `m2.3-s5-complete` is immutable,
with `m2.3-s5.4-complete` supplementing it. A tenth ruling authorized migration `0012` in principle; an
eleventh is the test-scoping clarification (Decision 020 §8.3). All are satisfied.

**The Milestone 2.3 stage contracts are all closed.** `Milestones/contracts/m23_s6.md`,
`m23_s5_4.md`, `m23_s5_2.md`, and `m23_s5_1.md` **authorize nothing**; each remains on record as its
stage's scope statement. Per [`contracts/README.md`](contracts/README.md), a completed contract
authorizes nothing further; reopening a closed stage requires a new explicit owner authorization and
its own contract. **`ACTIVE_STAGE_CONTRACT` names `Milestones/contracts/m3_2.md`** — the accepted
M3.2 contract, not the closed S6 one — and naming a path is never itself authorization:
**authorization is carried by that contract's own status and by `IMPLEMENTATION_AUTHORIZATION`
below.**

**Milestone 2 implementation is complete at accepted S6; publication work has not begun and is not
authorized.** No manifest approval, publication, CLI, live-metadata, real-snapshot, or release work is
authorized (Decision 018 §22, Decision 021 §§4, 11.1, 16, 17; Decision 023 §9; Decision 024 §8); see
`Docs/architecture_map.md` §0 and §8. **No S5 selection and no reserve is a published or
owner-approved input** — the only manifest S6 can create is `proposed`, over fixtures. The **final
independent integrated Milestones 1 and 2 audit ran, its bounded corrections and rereviews completed,
and Milestone 2 is now formally closed** (Decision 026). Closure created no publication, approval,
CLI, live-metadata, or release authority — every prohibition above still stands.

**The S4 entity-only draft is unchanged.** It stays in `running` state, remains non-publishable, and
is excluded from S5 run identity and from every manifest input. It is never promoted, mutated,
deleted, or transformed into the S5 joint run (Decision 018 §§6, 27) — a permanently-`running` S4
draft is expected residue, not an abandoned run. S5.4 read it, wrote it, and changed it in no way.

## Next authorized action

**`CLAUDE_M3_2_DECISION_055_OFFLINE_IMPLEMENTATION_PACKET`** — the owner may later issue that exact
packet. It is the **bounded OFFLINE implementation** of the accepted Decision 055 carry-in architecture
across the exact **sixteen paths** its §10 fixes, with **no seventeenth path**. **It does not
self-execute**, no session may begin it or any part of it before it is issued, and it grants **no**
operational-state, orphan-adoption, transport-construction, network, SEC, or live authority.
**Authorization is not implementation, implementation is not acceptance, and none of them discharges
M3-L14 or M3-L16.**

**The M3-L16 carry-in architecture is ACCEPTED AND BINDING** (accepted
[Decision 055](../Docs/Decisions/decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md),
2026-08-08, outcome `M3_2_CARRY_IN_ARCHITECTURE_ACCEPTED_AND_OFFLINE_IMPLEMENTATION_AUTHORIZED`; the
owner's verbatim approval was **"approve Decision 055."**). The preceding
`CLAUDE_M3_2_M3_L16_CARRY_IN_ARCHITECTURE_DISCOVERY_PACKET` was issued and completed as **read-only
validation** — it changed nothing, performed no network or SEC action, and left the repository at the
required baseline — and independently established four facts, all accepted: consumption is exactly
**1 of cumulative ceiling 801**; that attempt is attributable to **`sec_bulk_submissions`**; historical
`ops_retrieval_attempts` rows equal **0**; and recovery remains **`UNDETERMINED`** and **never `SAFE`**
because of the **raw-store/catalog orphan mismatch** rather than ambiguous attempt evidence. Remaining
total headroom is **800** and bulk-route headroom **5** — **accounting and reporting, never a runtime
refusal**. The old run is **`stopped` and permanently non-resumable**, and **no terminating receipt
exists**.

**Ruling 055-A — ceiling and plan.** The cumulative M3.2A ceiling remains exactly **801**; historical
seed **`H` = 1**, and future cumulative consumption is `H` plus new durable reservations. **No `802`
ceiling, additive ceiling, shadow ceiling, reset, or reinterpretation is permitted.** The frozen
request plan `19be7bdc…` and its **full 75-logical-request** plan remain unchanged. The global
`PhysicalAttemptCeiling` is constructed with `approved_ceiling` **801** and `consumed` **1** for the
authorized clean carry-in root, and **may lawfully stop the run at cumulative 801 with planned work
remaining** — there is **no pre-run fit gate and no false promise that all worst-case retries still
fit**. Route attribution to `sec_bulk_submissions` is **evidence and reporting only**: **no per-route
runtime refusal, and no change to `sec/http_client.py`**.

**Ruling 055-B — one-use carry-in authority.** One explicit **clean-root carry-in interface** is added.
**It is never resume** and **must refuse coexistence with `--resume-from`**. Its authority artifact has
canonical JSON bytes under schema **`m3-carry-in-authority/1.0`**, binding window `M3.2A`, the frozen
request-plan SHA-256, cumulative ceiling **801**, historical seed **1**, the route allocation of that
one attempt to `sec_bulk_submissions`, the Decision 055 identity, the authorized new run id, and the
**later accepted orphan-adoption decision identity and evidence identity** — and carrying **no secret,
identity header, response body, or private absolute path**. The **SHA-256 of its exact canonical bytes
is its external identity**, with **no circular self-hash field**. The CLI takes it from the governed
evidence root by a **safe relative path**, and the **authorized new run id comes from the artifact**,
replacing random generation for that invocation. It is **parsed, canonicalized, hashed, and validated
before transport construction**, and **consumed exactly once** by inserting a deterministic
`ops_checkpoints` primary key keyed by its SHA-256 in the **same existing `BEGIN IMMEDIATE`**
transaction as new-run registration — **no migration**. **Replay, run-id mismatch,
plan/window/ceiling/seed/route mismatch, malformed or noncanonical bytes, a conflicting resume, or a
missing binding all refuse before transport.** The registration transaction is **all-or-nothing**, and
if a later pre-wire failure occurs after commit **the authority remains burned even with zero
attempts** — **no automatic reissue or retry**. The checkpoint value preserves enough canonical safe
data for later receipt and catalog cross-checks.

**Ruling 055-C — receipt schema `3.0` and recovery arithmetic.** The receipt schema is unfrozen **only**
for this bounded change; the new **writer** schema is **`m3-execution-receipt/3.0`**. Existing **`2.0`**
receipts remain **byte-unchanged, valid, readable, and usable in mixed-version chains** — implement
**version dispatch** and **never rewrite an old receipt**. In `3.0`,
`consumed_request_count_carried_forward` means **cumulative physical attempts before the current
invocation**: required for a resume and for a clean carry-in root, omitted for an ordinary
zero-baseline fresh root. New field **`carry_in_authority_sha256`** is required **only** on a clean
carry-in root with **no predecessor and a nonzero carried-forward count**, absent on ordinary roots and
on resume receipts, and retained by the root for the chain. A clean carry-in root **omits
`recovery_predecessor_receipt_id`**, carries **1**, names the authority hash, and records
`actual_physical_attempt_count` as **current-invocation wire attempts `N` only**. Accounting validates
**carried-forward plus actual ≤ approved ceiling**. The chain walker adds the root carry-in **exactly
once** — the sum of every receipt's actual count plus only the **no-predecessor root's**
carried-forward count, **never `N` alone and never double-counted** — and `--show-scope` and every
recovery/continuation consumer must agree with it. The **catalog checkpoint and root receipt mutually
cross-check**; a missing or mismatched authority or carry-in becomes **`UNDETERMINED`** and **cannot
authorize continuation**.

**Ruling 055-D — the M3-L14 fail-closed correction.** M3-L14 is pre-resolved architecturally by a
**global one-to-one reservation-consumption rule across all owned receiptless lineage segments**: a
durable reservation may satisfy **at most one** segment. Any unmatched or multiply matchable
cardinality, duplicate reservation reuse, source/URL/run mismatch, leftover contradiction, or
**inability to establish an exact bijection** returns **`UNDETERMINED`**. The existing counterexample —
**one reservation plus two owned same-URL segments** — **must produce `UNDETERMINED`, never consumed
count 1 with `UNSAFE`**. Receiptless inspection remains inspection-only and can **never** return `SAFE`
or authorize continuation. **M3-L14 remains `ACTIVE`** until implementation, non-vacuous tests, full
validation, a fresh independent review, and separate owner closure.

**Ruling 055-E — historical orphan Path B.** **Path B is chosen**: a separately authorized, offline,
one-time, **verified orphan adoption before any clean carry-in run**. **Decision 055 does not
authorize, design in executable detail, or perform that adoption.** No adoption, quarantine,
reconciliation, catalog/raw/lineage mutation, or operational checkpoint is authorized now. A later
owner instrument must define the exact procedure, execute it once offline, independently verify it,
record acceptance, and leave **zero unresolved historical orphan mismatch** before a carry-in artifact
may be **minted or consumed** — and the carry-in authority must bind that later decision and evidence
identity. **Until then, a clean run, transport construction, network, SEC contact, and live readiness
remain prohibited.**

**Ruling 055-F — the bounded offline implementation envelope.** Exactly **sixteen paths, no
seventeenth**: production `src/disclosure_drift/cli.py`, `src/disclosure_drift/m3/acquisition.py`,
`src/disclosure_drift/m3/recovery.py`, `src/disclosure_drift/m3/receipt.py`; normative and operator
documentation [`contracts/m3_2.md`](contracts/m3_2.md), `Docs/m3/execution_receipt_spec.md`,
`Docs/m3/templates/gate_h_checklist.md`, `Docs/m3/operator_runbook.md`,
`Docs/m3/templates/interrupted_run_recovery.md`, `Docs/sec_data_dictionary.md`; and tests
`tests/unit/test_m3_acquisition.py`, `tests/unit/test_m3_recovery.py`, `tests/unit/test_m3_recover.py`,
`tests/unit/test_m3_receipt.py`, `tests/unit/test_request_ceiling.py`, and
`tests/integration/test_m3_cli.py`. The later session may create **exactly one local candidate commit**
with the exact subject `Implement M3.2 carry-in authority and receipt v3`. **It may not push and may
not tag.** Candidate acceptance, M3-L14 closure, M3-L16 closure, orphan adoption, network, live
invocation, T6, M3.2B, and Gate H each require **later separate owner acts**.

**Ruling 055-G — validation and review gates.** Targeted tests with non-vacuous positive controls are
required for: baseline `1 + N` reservations equalling cumulative `1 + N`; current-run attempt **800**
reaching cumulative **801** with the next physical attempt refused **without increment**; a **sixth
future bulk attempt not refused by any new per-route guard**, the global ceiling remaining sole runtime
enforcement; artifact replay and every mismatch refusing **before transport-factory invocation**;
atomic rollback between checkpoint insertion and run registration leaving **neither row**;
burn-before-wire staying consumed and never auto-reissued; `2.0` receipts remaining valid and readable
with exact `3.0` field conditions; the root carry-in counted **once** through mixed-version chains with
`--show-scope` agreeing; checkpoint/receipt mismatch becoming **`UNDETERMINED`**; the **M3-L14
one-reservation/two-segment counterexample becoming `UNDETERMINED`, with that test failing against
current behaviour**; prohibited-path nonchange; and network containment. Targeted validation runs while
editing, and the **full authorized gate once at stage end** — Ruff lint, Ruff format check,
`mypy src`, the full pytest suite including the SEC transport test, `make sqlite-check`, `make
secrets`, `make hygiene`, `make context`. After the frozen candidate, a **fresh Claude Opus 5 Max
non-author session** must independently review it **without modifying it**.

**Ruling 055-H — narrow supersession.** Decision 055 narrowly supersedes only four things: contract §12
where it recognizes solely predecessor-receipt carry-forward, adding the one-use non-resume carry-in
root; the prior clauses freezing `m3/receipt.py` and receipt schema `2.0`, solely for backward-
compatible schema `3.0` and version dispatch; the prior withholding of implementation, solely for the
sixteen-path offline candidate; and M3-L14's unresolved owner choice, selecting the fail-closed
one-to-one cardinality rule. **All other accepted authority remains binding** — ceiling **801**, the old
run's permanent no-resume status, no automatic continuation, fail-closed recovery, evidence
preservation, deterministic behaviour, and owner-gated live operations. Decision 050 §8's
predecessor-receipt requirement remains fully binding **for every resume**; the carry-in root is **not**
a resume.

**Decision 055 is governance only.** It performs no implementation and no operational-state mutation,
opened no operational catalog or private evidence even read-only, contacted nothing, and left tracked
network configuration at **`false` / `false`** with CompanyFacts disabled and migrations `0001`–`0013`
unchanged. **It accepts no candidate and closes no limitation.** **M3-L14 and M3-L16 remain `ACTIVE`**
— now carrying a selected architecture and an implementation authority, and **not closed** — **M3-L16
continues to block every clean-run and live authorization**, **M3-L15 is untouched and byte-unchanged**,
**live readiness is not claimed**, and **M3.2 is not complete**.

**The interrupted-run closure is EXECUTED, COMPLETE, AND ACCEPTED** (accepted
[Decision 054](../Docs/Decisions/decision_054_m3_2_interrupted_run_closure_acceptance.md), 2026-08-08,
outcome `M3_2_INTERRUPTED_RUN_CLOSURE_ACCEPTED`). The Decision 053 execution packet was issued and run
exactly once, offline. The owner accepts it as **PASS** on the full Decision 053 §§5–7 architecture and
evidence contract: every §7.1 preflight gate passed (migration head `0013` contiguous `0001`–`0013`;
`quick_check`/`integrity_check` **ok** and `foreign_key_check` **0** before and after; **exactly one**
candidate row against **one** total job row catalog-wide; **zero** attempt and **zero** event rows for
the target; no live writer holding the OS lock), **11 of 11** §7.2 synthetic cases passed against
disposable fixtures carrying a **decoy row proven untouched**, and an AST proof recorded 3 SQL
statements with exactly 1 mutating and **zero** references to any prohibited helper, entry point, or
transport constructor, with a `sys` audit hook hard-blocking socket calls throughout the real run.

The real transaction committed through the accepted `CatalogWriter` and **one `BEGIN IMMEDIATE`**
`batch()` transaction: one conditional `UPDATE` restating the row-state predicates in its own `WHERE`,
`cursor.rowcount == 1`, and exactly **three columns of exactly one** historical M3.2A row changed —
`job_state` `running` → **`stopped`**, `finished_at_utc` `NULL` → one new UTC instant, and `detail` →
the byte-exact 222-byte Decision 053 §6.4 closure text (SHA-256 `2065fb48…` → `e7872860…`), with
`job_id`, `job_kind`, `stage`, and `started_at_utc` unchanged and the job id **never recorded in
plaintext**. Blast radius: **1 of 84** user tables changed (`ops_ingestion_jobs`), **83** unchanged,
**no** row-count change in any table; attempt, event, raw-object, and observation counts all 0 → 0;
governed inventories byte-identical including `raw` at **2** files / **1,556,243,994** bytes; catalog
SHA-256 `c4f22158…` → `31b65e71…` at **unchanged** size **1,245,184** bytes; the lease present at an
**unchanged inode** (privately recorded), mode `0600`, final state **`released`** through the ordinary
acquire/release cycle with no deletion, clearing, `unlink`, replacement, manual edit, or expiry
takeover; integrity gates passing; the repository clean and byte-identical; and **no receipt creation
or reconstruction, attempt insertion, consumed-count mutation, orphan adoption, quarantine,
reconciliation, raw or lineage mutation, or network, DNS, or SEC action**. The owner independently
reverified the private evidence bundle (manifest `9aa1582e…` over four safe relative entries, all five
files mode `0600`) and a **byte-identical disposable immutable read-only** catalog copy — exactly one
ingestion job, now `stopped`, non-null finish time, byte-exact closure detail, zero attempt rows, zero
job events, quick and integrity checks ok, zero foreign-key violations — with the original catalog hash
**unchanged** by that verification.

**`HISTORICAL_JOB_STATE_NOW: stopped`. Decision 053's one-time execution authority is `EXHAUSTED`, and
the closure is complete and irreversible.** Recorded as an **OBSERVATION and not a defect**: the four
ephemeral procedure artifacts are identified by SHA-256, but their source was **correctly destroyed**
with the `mktemp -d` scratch directory — Decision 053 §7.1 required the hashes and a sanitized
protocol, not source preservation, and §5 declined a permanent surface by design. Those hashes attest
that a byte sequence ran; they do **not** permit re-deriving it, and **no reproducibility may be
invented**. **No BLOCKER, MAJOR, or MINOR finding remains.**

**A truthful terminal state is not a resolution.** Recovery remains **`UNDETERMINED`**, there is **no
terminating receipt**, historical `ops_retrieval_attempts` rows remain **0** with no backfill, accepted
consumption remains **1 of 801** (total headroom **800**; bulk-route **accounting** headroom **5**), and
the old run is **never resumable**. **`stopped` is not `completed`**, not a resolved orphan, not a
discharged recovery condition, and not continuation eligibility. **No further operational mutation or
repeat closure is authorized**, and no network, SEC request, new live invocation, resume, retry,
replacement, clean run, T6, M3.2B, or Gate H is authorized. **M3-L16 continues to block every
clean-run and live authorization**, and Decision 054 neither designs nor implements a carry-in
mechanism.

**The interrupted-run closure PROCEDURE was AUTHORIZED by** (accepted
[Decision 053](../Docs/Decisions/decision_053_m3_2_interrupted_run_closure_procedure_authorization.md),
2026-08-08, outcome `M3_2_INTERRUPTED_RUN_CLOSURE_PROCEDURE_AUTHORIZED`). Decision 053 fixes the exact
one-time architecture and boundaries for later closing the historical interrupted M3.2A T5 ingestion
job to `stopped`, and authorized only a separate exact execution packet —
`CLAUDE_M3_2_INTERRUPTED_RUN_CLOSURE_EXECUTION_PACKET`, **since issued, executed once, and accepted by
Decision 054, so that authority is now `EXHAUSTED`**. The closure ran as **one ephemeral,
hash-recorded, one-time operator procedure outside the repository** that
used the accepted `CatalogWriter` and its `batch()` transaction — the normal OS-lock and writer
lifecycle — and called none of `prepare_operational_catalog`, `migrate()`, `seed_reference_data()`,
`finish_acquisition_run`, a live-acquisition entry point, or a transport constructor. It failed closed
unless exactly one row satisfied every predicate (the exact owner-resolved job id,
`job_kind = 'm3_2_acquisition'`, `stage = 'M3.2A'`, `job_state = 'running'`,
`finished_at_utc IS NULL`, and exactly zero `ops_retrieval_attempts` rows), restated those predicates
in the single conditional `UPDATE` and required `cursor.rowcount == 1`, and changed exactly three
columns of exactly one row — `job_state` to `stopped`, `finished_at_utc` from `NULL` to one new UTC
instant, and `detail` to the fixed owner closure text. The lease kept its inode and ended
`released`; no other logical row or governed artifact changed. **No permanent production or test
surface was created or authorized**, so no implementation commit and no independent code-review cycle
for one was required. **Decision 053 itself performed no closure**: it opened no catalog even
read-only, read no private evidence, and mutated no operational state, and it granted no network, SEC,
resume, retry, replacement, clean-run, T6, M3.2B, or Gate H authority — the closure came later, under
the separate execution packet, and is accepted by Decision 054. **M3-L14, M3-L15, and M3-L16 remain
`ACTIVE` and unchanged, M3-L16 still blocks every clean-run and live authorization, and no live
readiness is claimed.** A future T5 instrument must explicitly supersede Decision 050 §9's
now-impossible preflight assumptions (consumed **0**, operational catalog absent, no prior live run);
**neither Decision 053 nor Decision 054 does so.**

**The post-T5 remediation is ACCEPTED AND COMPLETE** (accepted
[Decision 052](../Docs/Decisions/decision_052_m3_2_post_t5_remediation_acceptance_and_publication.md),
2026-08-08, outcome `M3_2_POST_T5_REMEDIATION_ACCEPTED_AND_PUBLISHED`), on the fresh independent
verdict `M3_2_POST_T5_REMEDIATION_INDEPENDENT_REREVIEW_PASS` (**BLOCKER 0 · MAJOR 0 · MINOR 2**;
artifact SHA-256 `7234ef37…` at review commit `e91b8fec…`). The accepted candidate is implementation
commit `47de073…` plus the separate accounting-correction commit `7dad423…` (tree `53d5342…`), full
accepted diff from `1e36a41` SHA-256 `a2ad82c8…`, across an exact eight-path delta.
**Decision 051's implementation authority is now `EXHAUSTED`, and no third correction loop is
authorized** — any later change, including discharging M3-L14, M3-L15, or M3-L16, needs a new explicit
owner packet.

Three conditions are carried, not discharged: **M3-L14** (receiptless ledger-coverage cardinality is
evaluated per manifest — never rely on receiptless accounting over a **non-empty** ledger as an owner
baseline until it closes), **M3-L15** (second-SIGTERM suppression is implemented and directly verified
but unguarded by a regression test), and **M3-L16** (**no clean-run carry-in interface exists for the
consumed baseline of 1**). **M3-L16 blocks any clean-run or live authorization until it closes.
Nothing here claims live readiness; the project is not ready for live operation.**

Decision 051 §11 item 4's two-run real-archive evidence was **NOT re-run** — the private path was not
disclosed to the reviewer. The accepted **43.1 / 45.2-second** measurements stand as the performance
evidence of record, and the reviewer's equivalent-scale synthetic evidence is reported as synthetic and
**may never be cited as real-archive evidence**.

The first T5 invocation is historical and exhausted. Exactly one physical SEC attempt is accepted as
consumed under the binding ceiling (**1 of 801; 800 remaining total; 5 remaining for the bulk route**).
The immutable archive and raw lineage are preserved, but the invocation has **no terminating receipt**
and **no committed observation/member transaction**. Its ingestion job was non-terminal until the
closure; **it is now `stopped`** — architecture and boundaries fixed by accepted Decision 053, executed
once under the separate execution packet, and accepted by accepted Decision 054
(`M3_2_INTERRUPTED_RUN_CLOSURE_ACCEPTED`). Recovery remains **`UNDETERMINED`** and the old run is
**never resumed**: the closure recorded truthfully *that* the job ended, never *what it accomplished*.

**Nothing further may be altered.** Do not alter the real catalog, raw object, lineage, consumed
accounting, attempt ledger, receipt state, job state, or lease — the one authorized disposition is
**complete, irreversible, and exhausted**, and no repeat closure or second disposition is authorized.
Do not reconstruct a receipt or backfill an historical attempt row. Receiptless recovery is authorized
only as an explicit read-only inspection mode and cannot classify the run `SAFE`, authorize
continuation, or mutate state. No network enablement, SEC request, new live invocation, resume, retry,
replacement, clean run, T6, M3.2B, or Gate H is authorized.

**The T4 operational preflight is EXECUTED, ACCEPTED, AND PUBLISHED** (accepted
[Decision 049](../Docs/Decisions/decision_049_m3_2_t4_operational_preflight_acceptance.md),
2026-08-07, outcome `M3_2_T4_OPERATIONAL_PREFLIGHT_ACCEPTED_AND_PUBLISHED`), on final findings
**BLOCKER 0 · MAJOR 0 · MINOR 0 · OPTIMIZATION 0**, at published baseline
`b7d83d389a92685bac776759b2af9762dc5301eb`, tree `6f54cdbccfa77def555c27c61e6ad9dd178369a0`. **No
independent rereview was required.** The acceptance is bound to exactly two private artifacts, both
**outside Git**: the T4 attestation `runs/m3_2_t4_preflight/t4_preflight_attestation.md` (SHA-256
`8483a549cf894f1d186750ec13c24b41e5279134e782ca6e28ff4514e75d10c8`, mode `600`) and the backup
manifest `backups/m3_2_t4_pre_window/manifest.sha256` (SHA-256
`0bb2b1d96bcefe7885d538fa054c93e4887a8a5233529538f9de39f059b84c8d`, mode `600`, **17** covered
files). Neither is copied into the repository, **no `operational_preflight_attestation` evidence type
is added, and no public evidence-index row is added for the T4 attestation**.

**T4 left the repository byte-identical and enabled nothing.** Accepted facts: **`FREE_DISK_50_GIB_GATE:
PASS`** on measured free storage **74,481,328,128 bytes / 69.3661 GiB** against the **50.00 GiB**
floor, with measured physical RAM **8,589,934,592 bytes / 8.00 GiB** recorded as an observation and
**no invented object-size RAM floor**; a qualifying **local external USB** backup that was
device-distinct (`st_dev`), writable, and stable throughout the complete successful execution, leaving
**pre-existing USB contents unchanged** in a **non-overwriting** new snapshot, with **destination hash
verification 17/17 PASS**, count equality PASS, **scratch restore 17/17 PASS** then deleted with
deletion proven, **`.env` excluded**, and the attestation copied separately with an exactly matching
destination SHA; and a disposable offline catalog that passed with migrations contiguous
`0001`–`0013`, `quick_check`/`integrity_check`/foreign-key checks PASS, all six reference counts PASS,
operational tables empty, and the disposable root removed. **The earlier unsuccessful T4 attempt, in
which the same USB disconnected, remains historical operational context**; it does not invalidate the
successful run, because the device was requalified and remained stable throughout the complete accepted
execution, and **it is not erased or rewritten**.

**The corrected operational expectation `reference_policy_versions = 25` is FROZEN** (Decision 049 §7)
on its accepted provenance — **21** distinct policy keys from accepted migrations `0002`–`0011` plus
**4** from `seed_reference_data()` (`universe`, `filing_inventory`, `raw_governance`, `temporal`), with
**zero** overlap. This **resolves the stale earlier packet expectation of 6**, which was incorrect. It
is **not** a defect, and **no code, migration, seed data, or governance record may be changed to obtain
another value**. The intermediate `backups/` permission issue was corrected within authorized
private-evidence scope from `0755` to `0700`, passed the final permissions gate, and **is not an open
limitation**.

**The pre-T4 RawStore streaming substage is ACCEPTED, COMPLETE, AND PUBLISHED** (accepted
[Decision 048](../Docs/Decisions/decision_048_m3_2_pre_t4_rawstore_acceptance_and_publication.md),
2026-08-07, outcome `M3_2_PRE_T4_RAWSTORE_ACCEPTED_AND_PUBLISHED`). Accepted candidate
`833a192839e888720389c4757250234b5cb219b7`, accepted tree
`c2d95badd8d137ebbb00a642d087fb03e1ec7353`, parent and Decision 047 governance baseline
`bc3d170a155aaa6c196536109ef57dd841226675`, subject `Stream raw-object storage instead of buffering
it`, **exactly two executable paths with no third**, **no tag**. The acceptance is **SHA-specific and
tree-specific** and does not transfer automatically to a later changed tree. **The fresh independent
non-author rereview PASSED and the owner accepts it**: verdict
`M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEW_PASS`, durable artifact
`Docs/m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md` (SHA-256
`7bd5a5441fc4a0218e18a5a5daddf5a53c4436a938ea942fc6f84835d265fc42`), committed alone at
`9406afbe88e83f7a0f0a52db290f9a220d01e6bc` (subject `Record independent rereview of corrected pre-T4
RawStore streaming`), establishing **BLOCKER 0 · MAJOR 0 · MINOR 2 · OPTIMIZATION 2**, **12 of 12
independent mutations `KILLED`**, **108/108 deterministic-gzip cases byte-exact**, bounded memory for
valid objects, a full suite of **3,246 passed / 1 pre-existing unrelated skip** (the fixed-literal
skip in `tests/unit/test_m23_pilot_manifest.py`), and **`tests/unit/test_httpx_transport.py` 30
passed / 0 skipped** — **with no live SEC operation**. **The first review's acceptance-blocking
`RawStore.verify()` MAJOR is CLOSED** (Decision 048 §5): trailer-truncated gzip, valid gzip plus
trailing garbage, and concatenated second members are all refused, and those refusals were proved
**not shadowed** by stored or content identity mismatches. **Limitation `M3-L13` is CLOSED — DECISION
048**, and **F4 is COMPLETE**. Four nonblocking findings are carried forward without reopening the
accepted candidate and **create no limitations-register entry**: MINOR-1
`ACCEPTED_NONBLOCKING_TEST_STRENGTH_OBSERVATION — DEFERRED`, MINOR-2
`ACCEPTED_NONBLOCKING_CORRUPT_PATH_RESOURCE_OBSERVATION — DEFERRED`, and OPTIMIZATION-1 and
OPTIMIZATION-2 `ACCEPTED_NONBLOCKING_OPTIMIZATION — DEFERRED`; any later cleanup needs separate
authority.

**Accepted [Decision 047](../Docs/Decisions/decision_047_m3_2_t4_operational_preflight_authorization.md)
(2026-08-07, outcome `M3_2_T4_OPERATIONAL_PREFLIGHT_AUTHORIZED_AND_PRE_T4_RAWSTORE_SUBSTAGE_AUTHORIZED`)**
accepts the read-only T4 operational-preflight architecture discovery
(`M3_2_T4_OPERATIONAL_PREFLIGHT_ARCHITECTURE_DISCOVERY_COMPLETE`; **zero BLOCKER, four MAJOR**) and
fixes twelve frozen owner rulings. **047-A `T4_DOES_NOT_CREATE_THE_OPERATIONAL_CATALOG`** — the real
governed catalog `catalogs/m3_2a_operational.sqlite3` must not exist at T4 and is first created
inside the first lawfully authorized M3.2A live invocation under a later T5 instrument, with **no
contract §11 amendment and no new catalog-creation CLI surface**; T4 may later exercise
`prepare_operational_catalog()` only against a disposable temporary root.
**047-B `AUTHORIZE_PRE_T4_RAWSTORE_STREAMING_SUBSTAGE`** — the whole-object buffering risk is **not**
accepted for the live window. **047-C** records **M3-L13** under the register's existing schema,
never erasing the historical limitation. **047-D discharges F4** with exactly three new artifact
types — `frozen_object_identity_set`, `derived_reference_set`, `reconciliation_report` — **no fourth
type**, and expressly **no** `operational_preflight_attestation`; T4 preflight evidence stays private
and is bound by SHA-256 through this ledger and the owner decision. **047-E** requires a **genuine
off-device or independently recoverable backup before T5** — same-device-only is insufficient — with
`.env` and the SEC identity excluded, a per-file SHA-256 manifest, source/backup verification, a
scratch-location restore test, no overwrite of the operational root, and **no new backup script**.
**047-F** fixes the substage's validation. **047-G** fixes that the future T5 authorizes **exactly
one** initial M3.2A live invocation with **no advance resume authority**, `UNDETERMINED` remaining a
stop. **047-H** imposes a conservative hard **`FREE DISK >= 50 GiB`** T5 entry floor measured
immediately before live authorization, with the unknown SEC bulk-object size never estimated as fact.
**047-I** fixes the identity procedure — validated locally, never displayed, logged, committed, placed
in an artifact or receipt, or typed inline into shell history. **047-J** requires a fresh independent
review of the RawStore substage and does not automatically require a second one for a later
governance/evidence-only T4 if no executable byte changes. **047-K** leaves Decision 046's T3
**MINOR-A** `ACCEPTED_NONBLOCKING_OBSERVATION — DEFERRED` and unmodified. **047-L** records the
progress-sink obligation **DISCHARGED** and **D023-O1 LATENT, NOT TRIGGERED, M3.3-scoped**.

**The pre-T4 RawStore streaming substage is IMPLEMENTED, INDEPENDENTLY REVIEWED, ACCEPTED, AND
PUBLISHED** (accepted Decision 048, 2026-08-07), and **Decision 047's substage authority is now
exhausted**.
Its envelope is **exactly two executable paths — `src/disclosure_drift/sec/raw_store.py` and
`tests/unit/test_raw_store.py`** — under Decision 047 §6.1's **narrow release of Decision 045 §16's
prohibition on `sec/raw_store.py` for this substage only**; every other prohibited path stays
prohibited and a third path is an immediate stop. It makes hashing, sizing, compression,
decompression, and verification incremental over bounded blocks so storage memory no longer scales
with object size, while preserving `.part` staging, content-addressed identity, no-overwrite atomic
create-once hard-link promotion, file and directory `fsync`, evidence preservation after failure,
exact deduplication, unchanged fail-closed failure handling, byte-identical deterministic gzip, and
the unchanged public `RawStore` API. **No migration, receipt-schema, reason-code, or configuration
byte changes with it**, the chain remains `0001`–`0013`, the receipt remains
`m3-execution-receipt/2.0`, both tracked network switches remain `false`, CompanyFacts remains
disabled, ceiling **801** remains unused, and no operational catalog, M3.2 run, live receipt, raw
object, or live SEC artifact exists or was created. **The substage is published by one normal
fast-forward push under Decision 048, with no tag.**

`CHATGPT_OWNER_M3_2_T4_OPERATIONAL_PREFLIGHT_ARCHITECTURE_DISCOVERY` is **discharged (2026-08-07)** —
the discovery ran read-only, changed no repository byte, and its outcome is accepted by Decision 047.

**Combined stage T2.5–T2.6 is ACCEPTED, COMPLETE, AND PUBLISHED, and overall M3.2 T3 implementation
acceptance HAS occurred** (accepted
[Decision 046](../Docs/Decisions/decision_046_m3_2_t3_acceptance_and_publication.md), 2026-08-07,
outcome `M3_2_T3_ACCEPTED_AND_PUBLISHED`; overall determination
`M3_2_T3_IMPLEMENTATION_ACCEPTED_AND_COMPLETE`). Accepted corrected candidate
`810d567ba7610b22e2ce7cd56b67b7f0e76d26fb`, verified tree
`aa7a7d4a6117160a2a4b2d1165d9b82c318cf968`, parent and published Decision 045 baseline
`f2bbbbf2a1b13e0780c3ea50d01797f78405e97b`, subject
`Complete M3.2 T2.5-T2.6 integrated implementation`, **no tag**. This is **the accepted
implementation freeze** for the combined stage. It changed **exactly eight paths inside the
fifteen-path ceiling, with no sixteenth**: `src/disclosure_drift/cli.py`,
`src/disclosure_drift/m3/__init__.py`, `src/disclosure_drift/m3/acquisition.py`,
`src/disclosure_drift/m3/request_plan.py`, `tests/integration/test_m3_cli.py`,
`tests/unit/test_m3_acquisition.py`, `tests/unit/test_m3_dependent_plan.py` (added), and
`tests/unit/test_m3_request_plan.py` — 7,707 insertions, 347 deletions. **Twenty-five prohibited
paths were independently proved byte-identical by Git blob hash**, and `git diff` over `Docs`,
`Literature`, `Milestones`, `configs`, `scripts`, `src/disclosure_drift/storage`, `pyproject.toml`,
and `Makefile` was empty.

**The fresh independent T3 corrected-candidate rereview PASSED and the owner accepts it.** Verdict
`M3_2_T3_CORRECTED_FREEZE_CANDIDATE_REREVIEW_PASS`, by a genuinely fresh non-author session using no
subagent, delegated agent, background agent, parallel session, worktree, or dynamic workflow, which
kept the candidate read-only until the substantive verdict was complete and ran every destructive
probe and mutation inside a disposable copy outside the repository that was deleted and verified
deleted. Durable artifact
`Docs/m3/reviews/m3_2_t3_corrected_freeze_candidate_independent_rereview.md` (SHA-256
`31cf05dfe6a1a157df6b05bb6788f6ec9c391742028c24bf06dd3e3fcec2e773`), committed alone at
`3794178584bd935d5718e6ec5c4279dd235c7b3d` (tree `3df60f1430c79eb9cd28f12f265b8bb9c9514234`, parent
`810d567ba7610b22e2ce7cd56b67b7f0e76d26fb`, subject `Record independent rereview of corrected M3.2 T3
freeze candidate`). It established **BLOCKER 0 · MAJOR 0 · MINOR 1 · OPTIMIZATION 1**, **14 of 14
independent mutations `KILLED`**, a full suite of **3,222 passed / 1 pre-existing unrelated skip**
(the fixed-literal skip in `tests/unit/test_m23_pilot_manifest.py`),
**`tests/unit/test_httpx_transport.py` 30 passed / 0 skipped**, and
**interruption → recovery → SAFE → resume exercised through the real CLI path with a substituted
non-network transport**, including across separate OS processes — with **no live SEC operation**.
**Therefore the T3 acceptance threshold is satisfied.**

**Two nonblocking observations are carried forward without reopening T2.5–T2.6**, and **the accepted
implementation was not modified during the recording**. **MINOR-A** — the `_execute` ordering permits
an extremely narrow interruption timing window after durable commit but before
`_committed_any = True`, potentially reporting `before_raw_store_write` despite the durable retrieval
already being committed; the reviewer demonstrated this alters **no** durable remainder
determination, attempt accounting, SAFE recovery, or resume behaviour, because those are
**evidence-derived rather than phase-label-derived** — disposition
`ACCEPTED_NONBLOCKING_OBSERVATION — DEFERRED`. **OPTIMIZATION-A** — `_window_reason_code` may use
`SEC_ACQUISITION_INTERRUPTED` as fallback for certain non-interrupted failed, stopped, or incomplete
outcomes; the reviewer found no safety consequence and no acceptance defect — disposition
`ACCEPTED_NONBLOCKING_OPTIMIZATION — DEFERRED`. **Any future cleanup of either requires separate
owner authorization.**

**Decision 045's implementation authority is exhausted** by this accepted implementation. Neither
Decision 045 nor Decision 046 authorizes further T2.5–T2.6 implementation, a further edit to the
accepted candidate's paths under Decision 045 authority, or a second combined-stage commit.

**Publication is complete.** One normal fast-forward push of `main` published, in order, the
published Decision 045 baseline `f2bbbbf2…` (already remote), the accepted candidate `810d567…`, the
accepted PASS review `3794178…`, and the Decision 046 governance commit (exact subject `Accept M3.2
T3 implementation and independent review`) — no commit amended, squashed, rebased, cherry-picked,
inserted, reset, or removed; **no tag, no release, no force push, no history rewrite**.

**Standing state, unchanged by this acceptance.** **T4 and T5 are NOT AUTHORIZED and NOT BEGUN**; both
tracked network switches remain `false`; CompanyFacts remains disabled; the migration chain remains
`0001`–`0013`; the receipt remains `m3-execution-receipt/2.0`; ceiling **801** remains unused; and no
operational catalog, M3.2 run, live receipt, raw object, live SEC artifact, request, or SEC contact
exists or may be created. **F4 — public evidence-index vocabulary for the private reconciliation
report — remains a T4 obligation.** T3 acceptance is **not** T4 acceptance, T5 authority, network
authority, or live-operation authority, and T6 and Gate H remain separate later owner acts.

`CHATGPT_OWNER_ISSUANCE_OF_M3_2_T2_5_T2_6_IMPLEMENTATION_PACKET_AFTER_DECISION_045_PUBLICATION` is
**discharged (2026-08-07)** — the owner issued that execution packet, the stage was implemented as one
candidate, independently rereviewed after correction, and accepted by Decision 046.

**Historical — the authorization the accepted implementation was built under.**
**Combined stage T2.5–T2.6 was AUTHORIZED** by accepted
[Decision 045](../Docs/Decisions/decision_045_m3_2_t2_5_t2_6_integrated_implementation_authorization.md)
(2026-08-07, outcome `M3_2_T2_5_T2_6_INTEGRATED_IMPLEMENTATION_AUTHORIZED`) as **one** combined
stage under Decision 037 and contract §22, producing **one** implementation-freeze candidate for the
independent T3 review — exact subject `Complete M3.2 T2.5-T2.6 integrated implementation`, **local
and unpushed pending T3 review, no tag**. It runs in **two internal subphases** (A: the five offline
operator surfaces, progress-sink sanitization, and dependent-plan derivation; B: `--live` wiring, the
single transport-construction site, the authorization conjunction, run registration, ceiling and
resume integration, and receipt assembly) that are **implementation checkpoints only — no Subphase-A
commit**. Its envelope is the **fifteen-path ceiling with no sixteenth path** (required: P3, P4, P5,
P8, T1, T2, T4, T5; conditional: P6, P7, T3, T6, T7; `configs/project.yaml` and `config.py` expected
byte-identical and **never** a route to live authority), and the Decision 038 and Decision 041 path
extensions **do not carry forward** — `sec/observation_catalog.py` remains prohibited, and a need for
it is a **STOP**.

**Two owner rulings were adopted before Decision 045 was first recorded**, in response to two
verification findings raised against the accepted code and schema, and are carried in its first and
only durable version. **`BLOCKER_1_RESOLUTION: A1_APPROVED`** gives M3.2 a **durable
acquisition-run identity**: for each lawful `m3 acquire --live` invocation, `m3/acquisition.py`
registers exactly one existing-table `ops_ingestion_jobs` row with `job_kind='m3_2_acquisition'` and
stage `M3.2A`/`M3.2B`, **ordered and verified before transport construction** (failure means no
transport, no request, and no attributed object), one run per invocation with a **new** identity on
resume, and durable run→observation attribution through **existing accepted relations only, proven
compatible before use** — **no migration, no new table or column, no prohibited-path edit**, and a
**STOP** if no lawful relation exists; `show-drift --run` and `recover --run` are retained, fail
closed at exit `4` on unknown, non-M3.2, unattributable, or ambiguous identity, with **no
global-drift fallback** and **no fabricated run identity**.
**`BLOCKER_2_RESOLUTION: EXHAUSTIVE_RESPONSE_EVENT_ACCOUNTING_WITH_STATUS_ZERO_SENTINEL`** retains
the invariant `sum(response_classification_totals) == sum(status_code_totals)` over an exhaustively
defined response-event universe: a followed 3xx contributes its actual status plus one `proceed`; a
lawful 304 contributes `304` + `proceed` + `not_modified_count` and never `duplicate_object_count`; a
classified no-response transport failure contributes the **receipt-local sentinel**
`status_code_totals["0"]` — "no HTTP status — transport-level failure", **not** an HTTP status code —
plus exactly one already-frozen bucket; pre-transport refusals contribute to neither total; and
`cooldown_count == response_classification_totals["cooldown"]`. All of it is produced **inside the
authorized M3 layer**, with **no receipt-schema, field, mode, vocabulary, or validator change** —
`m3/receipt.py` and `sec/http_client.py` stay byte-identical, and insufficient accepted surfaces are
a **STOP**, never an inference.

**Decision 045 authorized implementation and offline testing only.** Both tracked network switches
remain `false`, CompanyFacts remains disabled, the migration chain remains `0001`–`0013`, the receipt
remains `m3-execution-receipt/2.0`, ceiling **801** remains unused, and no operational catalog, run
row, raw object, live receipt, evidence artifact, request, or SEC contact exists or may be created.
**Overall M3.2 T3 implementation acceptance has since occurred** (accepted Decision 046, 2026-08-07),
and **T4, T5, T6, and Gate H remain separate later owner acts**. The accepted contract's stale
Decision-037-era header metadata is
**historical and is not a stop condition** — Decisions 039, 042, 044, and 045 control, and the
contract is **not** edited. The implementation session **does not edit this ledger**: the freeze
candidate's SHA is reported in its completion handoff and bound later by the T3 acceptance Decision.

`CHATGPT_OWNER_M3_2_T2_5_STAGE_AUTHORIZATION_DECISION` is **discharged (2026-08-07)** — the owner
issued that stage decision as accepted Decision 045.

**Stage G1 is ACCEPTED, COMPLETE, AND PUBLISHED** (accepted
[Decision 044](../Docs/Decisions/decision_044_m3_2_g1_acceptance_and_publication.md), 2026-08-06,
outcome `M3_2_G1_ACCEPTED_AND_PUBLISHED`; stage classification `M3_2_G1_ACCEPTED_AND_COMPLETE`).
Accepted candidate `7ac33d0abd9e05bf895b38270bde476317c974be`, accepted tree
`a848320f1edd159f07b112f45790a229ec48827e`, parent and published Decision 043 baseline
`c1fbece9242356b840787dd00ad46f15bb880133`, subject `Repair M3.2 navigation and review workflow`,
**no tag**. It changed exactly the seven authorized paths and no eighth: `Docs/decision_index.md`,
`Docs/change_impact_map.md`, `Docs/architecture_map.md`, this file, `scripts/context_snapshot.sh`,
`Makefile`, and the new `Docs/m3/review_execution_conventions.md`. **No production source, test,
configuration, migration, schema, receipt, reason-code, route, or network byte changed**; the chain
remains `0001`–`0013`, the receipt remains `m3-execution-receipt/2.0`, and both tracked network
switches remain `false`.

**The fresh independent G1 review PASSED and the owner accepts it.** Verdict
`M3_2_G1_INDEPENDENT_REVIEW_PASS`, by a genuinely fresh session that was not the implementation
session and stayed read-only until the substantive verdict was determined — zero BLOCKER, zero
MAJOR, one MINOR, two OPTIMIZATION. This is the first exercise of the Decision 043 §11 lifecycle:
the durable artifact `Docs/m3/reviews/m3_2_g1_navigation_workflow_repair_independent_review.md`
(SHA-256 `ec12e038759d61b238c3a6fb7b46627ec070651fba9084d728fb09dfd1ad958f`) was created only after
the verdict and committed alone at `983fceb27122e4c4275f9554ad001c2d0a9d8524` (tree
`2ac6a0a04973494cd561c0440652959a2c499592`, parent `7ac33d0abd9e05bf895b38270bde476317c974be`,
subject `Record independent review of M3.2 G1 navigation repair`). **No historical T2.2–T2.3 or T2.4
review artifact was reconstructed, fabricated, or back-dated**, and the prospective durable-review
convention remains in effect for later acceptance-relevant reviews.

**Accepted context-optimization evidence: `14,579` → `2,654` bytes — 11,925 removed, 81.8%** — the
independent review's reproducible measurement on the published parent and the committed candidate.
The earlier `14,724` and `2,795` observations are **superseded for acceptance evidence** and are
**not implementation defects**; both are measurement-state artifacts, and the review's MINOR-1 is
discharged by this binding with no repository change. The two OPTIMIZATION observations are recorded
in Decision 044 §5.1 as observations only and are not authorized for action.

**G1's seven-path implementation authority is exhausted.** Neither Decision 043 nor Decision 044
authorizes further G1 implementation, a further edit to those seven paths under G1 authority, or a
second G1 commit. **G1 acceptance and T2.5 implementation authorization remain separate owner
judgments**, and neither follows from the other.

**The three-commit chain is published** by one normal fast-forward push carrying, in order, the
accepted candidate `7ac33d0…`, the review commit `983fceb…`, and the Decision 044 acceptance commit
(exact subject `Accept and publish M3.2 G1`) — no commit inserted, rewritten, squashed, amended,
rebased, reset, or removed; **no tag, no release, no force push, no history rewrite**.

**The bounded non-production stage M3.2 G1 — Navigation and Workflow Repair is AUTHORIZED** by
accepted
[Decision 043](../Docs/Decisions/decision_043_m3_2_g1_navigation_workflow_repair_authorization.md)
(2026-08-06, outcome `M3_2_G1_NAVIGATION_AND_WORKFLOW_REPAIR_AUTHORIZED`), which accepts the
read-only post-T2.4 workflow-efficiency discovery recommendation
`RECOMMEND_MINIMAL_OPTIMIZATION_BEFORE_T2_5`. **G1 sits outside the contract T-series** and alters
no T2 cadence, completion, or methodology, and no accepted contract meaning. Its envelope is a
**seven-path ceiling, not a requirement to edit every path** — `Docs/decision_index.md`,
`Docs/change_impact_map.md`, `Docs/architecture_map.md`, this file, `scripts/context_snapshot.sh`,
`Makefile`, and the new `Docs/m3/review_execution_conventions.md` — with **no eighth path**, **no
production source or test behaviour change**, **at most one implementation commit** carrying the
exact subject `Repair M3.2 navigation and review workflow`, and **no tag**. Decision 043 §5
supersedes the [Decision 033](../Docs/Decisions/decision_033_m3_2_correction_pass_adjudication.md)
§5 navigation-preservation instruction **partially and prospectively**, solely so far as necessary
to perform this repair: historical decisions remain immutable, and navigation aids remain aids that
defer to accepted decisions, the contract, and this ledger. Decision 043 §11 makes the durable
independent-review artifact **prospective from G1** and expressly forbids reconstructing,
fabricating, or back-dating the missing historical T2.2–T2.3 and T2.4 review artifacts. **G1
acceptance and T2.5 implementation authorization remain separate owner judgments.**

**Combined stage T2.5–T2.6 was AUTHORIZED as one combined stage — and is now implemented,
independently rereviewed, accepted, and published.** Neither T2.4 acceptance nor Decision 043
authorized it; its separate explicit owner stage authorization is accepted
[Decision 045](../Docs/Decisions/decision_045_m3_2_t2_5_t2_6_integrated_implementation_authorization.md)
(2026-08-07, outcome `M3_2_T2_5_T2_6_INTEGRATED_IMPLEMENTATION_AUTHORIZED`), and its acceptance and
publication are accepted
[Decision 046](../Docs/Decisions/decision_046_m3_2_t3_acceptance_and_publication.md) (2026-08-07,
outcome `M3_2_T3_ACCEPTED_AND_PUBLISHED`). The requirement that **no session could begin the stage
from Decision 045, from its publication, or from this ledger alone** was satisfied: the separate
owner-issued execution packet preceded all executable work.

**Stage T2.4 is ACCEPTED, COMPLETE, AND PUBLISHED** (accepted
[Decision 042](../Docs/Decisions/decision_042_m3_2_t2_4_acceptance_and_publication.md), 2026-08-06,
outcome `M3_2_T2_4_ACCEPTED_AND_PUBLISHED`; stage classification
`M3_2_T2_4_ACCEPTED_AND_COMPLETE`). Accepted candidate
`625c03d6931e01acc99946ca3924f1cda4da6b76`, accepted tree
`816fd392df859106b9ba21b684f9b4a8061461fc`, parent and Decision 041 governance baseline
`4897bb1d8fc5be5cd6d12be941204e377bbfa5a4`, subject
`Implement M3.2 T2.4 recovery and reconciliation`, exactly **eight** changed paths, **no tag**.

**The fresh independent corrected-candidate rereview PASSED and the owner accepts it.** Verdict
`M3_2_T2_4_CORRECTED_CANDIDATE_REREVIEW_PASS`, executed by a fresh independent session on Claude
Opus 5 at Max effort, with **zero BLOCKER, zero MAJOR, and zero MINOR** findings, the mandatory
separate-OS-process durability challenge **PASS**, an independent mutation campaign **18/18
killed**, targeted validation **333 passed**, the full suite **3053 passed / 1 pre-existing
intentional skip**, and static gates clean. **That single skip was the pre-existing fixed-literal
skip in `tests/unit/test_m23_pilot_manifest.py`** (`snapshot_state is a fixed literal asserted
before hashing`); **the HTTPX transport tests executed and did not skip**, so contract §18's
requirement that the `[sec]` extra be installed with `tests/unit/test_httpx_transport.py` running
was satisfied, and CI enforces it independently with a dedicated "Transport suite must execute, not
skip" step. Decision 042's `[sec]`-extra wording therefore **understated** the validation actually
performed; it is historical and is not edited, and T2.4 acceptance is unaffected (Decision 043
§12). The rereview
reached the repository through the owner's supplied acceptance evidence; **no rereview artifact
file was previously recorded here, and Decision 042 creates, reconstructs, or back-dates none** —
no artifact path and no artifact SHA-256 is asserted, because none exists to assert.

**The owner accepts four things** (Decision 042 §4): the corrected T2.4 candidate; the independent
corrected-candidate rereview; **Decision 041's recovery-state primitive implementation as
satisfying the authorized corrective design** — the additive public pair `open_recovery_state` and
`resolve_recovery_state`, the generic `t2_4_recovery_action` vocabulary, the caller-supplied
already-registered `ops_ingestion_jobs.job_id` run-identity ruling, the corrected thirteen-step
write-ahead sequence, and the eight fixed failure outcomes; and **T2.4 as complete and accepted**.
**T2.4 acceptance does not itself grant T2.5, T2.6, network, operational-catalog, live-SEC, or
801-ceiling execution authority.**

**The accepted candidate's eight paths sit inside the Decision 041 ten-path maximum with no
eleventh path**: `src/disclosure_drift/m3/acquisition.py`, `src/disclosure_drift/m3/__init__.py`,
`src/disclosure_drift/reasons.py`, `src/disclosure_drift/sec/observation_catalog.py`,
`tests/unit/test_m3_acquisition.py`, `tests/unit/test_m3_recover.py`,
`tests/unit/test_observation_catalog.py`, and `tests/unit/test_reasons.py`.
`src/disclosure_drift/m3/recovery.py` and `tests/unit/test_m3_recovery.py` were **not** edited,
which the maximum-not-requirement rule permits. The candidate changes **no** migration,
receipt-schema, configuration, contract, packet, decision, script, template, CI, or documentation
byte: the chain remains exactly `0001`–`0013`, the receipt remains `m3-execution-receipt/2.0`, and
both tracked network switches remain `false`.

**Publication is complete.** One normal fast-forward push of `main` published, in order, the
accepted candidate `625c03d6…` and the Decision 042 acceptance-and-publication governance commit
(exact subject `Accept and publish M3.2 T2.4`). The candidate was **not** rewritten, amended,
squashed, rebased, reset, or cherry-picked — the governance change was created on top of it. **No
tag, no release, no force push, no history rewrite.**

**Three determinations stay distinct.** Stage acceptance; publication of that stage; and **overall
Milestone 3.2 T3 implementation acceptance, which had NOT occurred at that acceptance**. Combined
stage T2.5–T2.6 was then owner-gated and had not begun (it has since been authorized by accepted
Decision 045 and accepted and published by accepted Decision 046, which also records the overall T3
determination `M3_2_T3_IMPLEMENTATION_ACCEPTED_AND_COMPLETE`); **T4 and each per-window T5 remain
separate later owner acts and are not authorized**.

**The T2.4 recovery-state primitive authority and path-envelope amendment are RECORDED** (accepted
[Decision 041](../Docs/Decisions/decision_041_m3_2_t2_4_recovery_state_primitive_authority.md),
2026-08-06, outcome `M3_2_T2_4_RECOVERY_STATE_PRIMITIVE_AUTHORITY_RECORDED`), recording verbatim
the owner instrument `OWNER_DECISION_041_M3_2_T2_4_RECOVERY_STATE_PRIMITIVE_AUTHORITY: APPROVED`.

**The correction the following paragraphs describe is complete, accepted, and published** — the
history below is the accepted record of why Decision 041 was required, not an open work item. The
independent T2.4 audit established that the first candidate's post-mutation
event-recording failure prohibition was **in-memory only**, and the owner-authorized read-only
feasibility determination returned
`M3_2_T2_4_DURABLE_RECOVERY_LIFECYCLE_NOT_FEASIBLE_WITHIN_CURRENT_AUTHORITY`. Decision 041 §2
**accepts that outcome** on seven grounds: no accepted callable resolves an exact generic
`census_recovery_states` row; the sole existing resolver is embedded in `rebuild_audit_projection`;
it is hard-filtered to `audit_projection_interrupted`; it resolves every blocked projection state
for a run rather than one exact primary-key identity; it performs a projection rebuild and other
unrelated mutations; it resolves **during** the mutation, before recovery-event recording; and
**three of the four T2.4 recovery actions have no resolver at all**. **The schema is sufficient;
the missing capability is an accepted exact primitive.** The feasibility session's use of Claude
Opus 5 rather than Claude Fable 5, and the independent-audit report's absence from that session,
are accepted as **non-material and nonblocking** (§3).

**The T2.4 envelope is amended from eight paths to exactly ten.** Decision 041 §4 amends Decision
040 §11 **for the T2.4 correction only**, adding `src/disclosure_drift/sec/observation_catalog.py`
and `tests/unit/test_observation_catalog.py` to the four existing production paths
(`src/disclosure_drift/m3/acquisition.py`, `src/disclosure_drift/m3/recovery.py`,
`src/disclosure_drift/m3/__init__.py`, `src/disclosure_drift/reasons.py`) and four existing test
paths (`tests/unit/test_m3_acquisition.py`, `tests/unit/test_m3_recover.py`,
`tests/unit/test_m3_recovery.py`, `tests/unit/test_reasons.py`). Decision 040 §12 is amended
**only** to release `observation_catalog.py` for the narrow additions below; **no other previously
prohibited path is released**, the ten paths are a **maximum rather than a requirement to edit
every path**, and an eleventh path is an immediate stop. **Decision 038 has no authority over
T2.4** and is not the source of this release.

**Exactly two additive public primitives are authorized** in `observation_catalog.py` (§5), with
every existing public and private function retaining its accepted semantics and **no existing
resolver, reconciliation function, recorder, schema, or projection behavior rewritten to simulate
the new authority**: `open_recovery_state` (nonempty inputs; verifies `census_run_id` identifies an
existing `ops_ingestion_jobs.job_id`; inserts exactly one `census_recovery_states` row with
`resolution_state = 'blocked'` addressed by the full primary key
`(census_run_id, recovery_state_id)`; raises on missing run, duplicate identity, constraint
failure, or failed write; writes nothing to `census_recovery_events` or
`census_projection_recovery_events`; **no silent skip when a run ID is absent**) and
`resolve_recovery_state` (updates only the exact primary-key row; requires it currently blocked;
performs **no** scenario filtering, projection rebuild, or repair; updates no sibling state; writes
no event row; returns success only when exactly one blocked row was resolved; treats zero affected
rows as failure; **must not bulk-resolve by run or scenario**).

**Vocabulary, identity, sequence, and failure semantics are fixed.** The applier uses the generic
state scenario `t2_4_recovery_action`, stored **only** in `census_recovery_states` and never
inserted into the CHECK-constrained `census_recovery_events` (§6). Every mutating recovery action
requires a **caller-supplied, already registered `ops_ingestion_jobs.job_id`**, refusing before
mutation when it is absent, empty, unresolvable, not a lawful existing governed run, or when a
blocked T2.4 state already exists for that run; T2.4 may not create an ingestion-job row, invoke
the private census-orchestrator job creator, fabricate a job identity, substitute a receipt ID,
create a new recovery-run identity model, or create a real operational run — though tests may
create lawful temporary catalog fixtures (§7). The **corrected thirteen-step write-ahead sequence**
(§8) commits and fresh-connection verifies the block **before** mutation, records the actual event
through `record_recovery_events` with `census_run_id=None` so no second recovery-state row is
created, and resolves the exact state **only after** event recording succeeds; **opening the block
is not itself a recovery event**. Eight failure outcomes are fixed (§9), a committed resolution
whose readback cannot complete leaves that invocation `UNDETERMINED`, and **no in-memory flag may
be the only continuation prohibition**.

**Dispositions unchanged** (§11): `NO_NEW_MIGRATION_REQUIRED` (chain exactly `0001`–`0013`),
`NO_RECEIPT_SCHEMA_CHANGE_REQUIRED` (`m3-execution-receipt/2.0` frozen), exactly one T2.4
reason-code addition, no alias, no route or source-authority change, no configuration change.

**The candidate and unpublished history — discharged.** The superseded first candidate
`5cba2863f47df09c83564258be897a4fd71cf6be` (tree `e3c47528e6059c7b8e10369846934c56e3b8eabe`) was
never accepted, never pushed, and never tagged; it is historical only and is on no branch and no
tag. Decision 041 was recorded and published **from a disposable governance clone without changing
the primary checkout** (§12). The separate correction packet was then issued and executed exactly
as §12 permitted — the primary checkout fetched the published Decision 041 baseline, the candidate
was verified still exactly `5cba2863…`, its code delta was preserved, local `main` moved to that
baseline through **one controlled soft reset**, the corrections were applied, and **exactly one**
corrected implementation commit was created with the subject
`Implement M3.2 T2.4 recovery and reconciliation`. That corrected commit is the accepted candidate
`625c03d6931e01acc99946ca3924f1cda4da6b76`. **No published history was changed at any point.**

**The nine continuing correction obligations are discharged** (§13) — durable post-mutation
fail-closed behavior; exact durable in-flight identity or `UNDETERMINED` classification;
preservation of the multiple-possible-in-flight basis; exhaustive continuation-state partitioning;
blocking of hash mismatch and invalid archive lineage; stray-lineage adoption coverage;
symlink-sweep alignment; refusal-reason coverage; and snapshot-counter documentation — resolved by
the corrected candidate and confirmed by the fresh independent corrected-candidate rereview
(`M3_2_T2_4_CORRECTED_CANDIDATE_REREVIEW_PASS`; zero BLOCKER, zero MAJOR, zero MINOR), which
accepted Decision 042 adopts. **Mutation 02 remains accepted as a proven no-op.**

**Stage T2.4 was AUTHORIZED — and is now implemented, corrected, independently rereviewed,
accepted, and published at candidate `625c03d6…` under accepted Decision 042** (stage authorization
accepted
[Decision 040](../Docs/Decisions/decision_040_m3_2_t2_4_implementation_authorization.md),
2026-08-06, outcome `M3_2_T2_4_IMPLEMENTATION_AUTHORIZED`), recording verbatim the owner
instrument `OWNER_DECISION_040_M3_2_T2_4_IMPLEMENTATION_AUTHORIZATION: APPROVED`. The decision:
**accepts the read-only T2.4 discovery outcome**
`M3_2_T2_4_IMPLEMENTATION_PACKET_DISCOVERY_COMPLETE`; **authorizes T2.4 as one coherent stage
with four internal subphases** — T2.4-A catalog-authoritative reconstruction (fresh-store
adoption from the durable catalog; predecessor-process in-memory state discarded; quarantined,
failed, and unverifiable observations excluded from reuse; immutable evidence re-verified at the
point of reuse), T2.4-B deterministic read-only reconciliation and drift inspection (item-level
state in deterministic plan order across seventeen distinguished states; mutates nothing),
T2.4-C the continuation proposal and conditional reuse (bound to predecessor receipt-chain
identity, exact plan hash, window, and approved ceiling; cumulative consumption without reset;
conservative full-`A_reachable` charge for at most one identifiable receiptless in-flight
request; `UNDETERMINED` fail-closed with continuation prohibited; validators only from a lawful
verified predecessor; a 304 satisfies only through accepted immutable-evidence and lineage
verification, and an unreconciled 304 fails closed with `SOURCE_SNAPSHOT_REUSE_UNRECONCILED`;
continuation authorization and execution remain later separate acts), and T2.4-D the explicit
recovery-action library boundary (four deterministic action classes; never automatic; exactly
one explicitly requested action, re-verified immediately before acting; **no CLI exposure during
T2.4**); **approves exactly one new registered reason code**
`SOURCE_REQUIRED_OBJECT_UNAVAILABLE` (integrity; `blocks_release` true; `requires_manual_review`
true; attached to a required non-quarterly-index M3.2A logical request whose committed
observation is terminally failed or quarantined; quarterly-index codes unchanged; no second
code) — resolving the singleton bootstrap-absence reason-authority obligation; **fixes the
dispositions** `NO_NEW_MIGRATION_REQUIRED` (chain exactly `0001`–`0013`) and
`NO_RECEIPT_SCHEMA_CHANGE_REQUIRED` (`m3-execution-receipt/2.0` frozen; no receipt emitted in
T2.4); **names the durable reconciliation source** (`census_source_observations`,
`census_observation_reasons`, `census_archive_members`, the accepted recovery tables, and the
governed object and staging trees); **fixes the accounting-vocabulary ruling**
(already-satisfied exclusion → the future receipt's `cache_hit_count`; lawful 304 → the future
`not_modified_count`; byte-identical 200 → the future `duplicate_object_count`) and the
three-part cumulative attempt-accounting formula with its `UNDETERMINED` fallback; **rules F4
non-blocking for T2.4** (due no later than T4 and before the first affected artifact is publicly
indexed); and **fixes the exact eight-path maximum envelope** —
`src/disclosure_drift/m3/acquisition.py`, `src/disclosure_drift/m3/recovery.py`,
`src/disclosure_drift/m3/__init__.py`, `src/disclosure_drift/reasons.py`,
`tests/unit/test_m3_acquisition.py`, `tests/unit/test_m3_recover.py` (the one authorized new
test file), `tests/unit/test_m3_recovery.py`, and `tests/unit/test_reasons.py` — **expressly
adding `tests/unit/test_reasons.py` to the Decision 035 envelope for T2.4 only**, a narrow,
stage-scoped higher-authority amendment (the historical T2 packet remains byte-identical at
SHA-256 `62120146…`; **Decision 038 has no authority over T2.4**; any further path is an
immediate stop before the path is touched). T2.4 uses **at most one implementation commit**
with the exact subject `Implement M3.2 T2.4 recovery and reconciliation`, local until
implementation completion, ChatGPT owner review, **one fresh independent no-subagent stage
audit**, correction and rereview where required, and the separate owner acceptance and
publication authorization; **no T2.4 stage tag**; **T2.5–T2.6 may not begin until T2.4 is
accepted and published**.

**The combined T2.2–T2.3 stage is ACCEPTED AND COMPLETE** (accepted
[Decision 039](../Docs/Decisions/decision_039_m3_2_t2_2_t2_3_stage_acceptance.md), 2026-08-06,
outcome `M3_2_T2_2_T2_3_ACCEPTED_AND_COMPLETE`). Accepted candidate
`6b189df1651ec3674ec7f96a1f5d66f488c654a9`, accepted tree
`8850e1e45e9471bbb8b94612da67715e932a496f`, published baseline and parent
`feb9e134307a9551475f243dc0c1ddcecc89ffde`, subject
`Implement M3.2 T2.2-T2.3 acquisition foundation`, exactly six paths, **no tag**.

**The final independent technical rereview is complete and its findings are adopted.** A fresh
non-author session using no subagents returned
`M3_2_T2_2_T2_3_SECOND_CORRECTED_INDEPENDENT_REREVIEW: PASS_WITH_REQUIRED_CORRECTIONS` with **zero
BLOCKER**, and the owner determines every technical PASS condition met: archive transport and
candidate-owned archive-member lineage **memory-bounded** (3,211,570-byte heap peak against a
71,303,168-byte expansion across 68 members — 3.06× the largest member, 4.5 % of total expanded
content, at most 2 members simultaneously live); archive-member persistence **single-pass,
deterministic, and transactional**; failed member enumeration or insertion leaving **no partial
catalog transaction** (12 rollback and reuse-boundary probes); correct archive reuse, supersession,
immutable-object preservation, and lineage reconciliation; ZIP fixtures deterministic and
independent of wall clock, locale, timezone, and building platform (five timezones, five processes,
15 consecutive clean runs of the previously flaky classes); bounded operational-error outputs
disclosing no private path or payload (five injected failure classes); request-plan, route,
ceiling, completion, recovery-observability, and no-network boundaries **fail-closed**; required
static, targeted, mutation, determinism, and full-suite validation passed (ruff, format, strict
mypy, targeted 272, full suite **2938 passed / 1 skipped twice consecutively**, all twelve required
mutation checks load-bearing); and **no live SEC access, operational catalog, receipt, evidence
artifact, or ceiling usage**. The rereview withheld a clean PASS **solely** because two
implementation paths lay outside the last durably recorded envelope — a governance-record defect
requiring **no code change**.

**Accepted [Decision 038](../Docs/Decisions/decision_038_m3_2_t2_2_t2_3_path_envelope_amendment.md)
(2026-08-05, outcome `M3_2_T2_2_T2_3_PATH_ENVELOPE_AMENDMENT_RECORDED`) resolved that defect**,
narrowly authorizing `src/disclosure_drift/sec/observation_catalog.py` and
`tests/unit/test_observation_catalog.py` for the combined T2.2–T2.3 stage only, bound to and
limited by the exact changes in candidate `6b189df1…`/tree `8850e1e4…`, and ratifying the earlier
explicit owner correction authorization granted **before** those paths were edited. Decision 039
accepts Decision 038 as the **controlling higher-authority amendment** for those paths and
purposes. Decision 038's governance commit is `27842965ed5a8fcccbf5fbb3c3c63ff2c2e798ba`
(tree `6bead61920ad947d35b300e9d81634ca5c767358`).

**Publication is authorized** — one **normal fast-forward push** of `main` publishing, in order,
the candidate `6b189df1…`, the Decision 038 commit `27842965…`, and the Decision 039 acceptance
commit, permitted only after Decision 039 is durably recorded, the registry and this ledger agree,
candidate bytes are unchanged, the contract and packet hashes are unchanged, `origin/main` is
verified an **ancestor** of local `HEAD`, the branch is behind by zero with no divergence, and
governance validation passes. **No tag is authorized for this stage**, and no force push, history
rewrite, rebase, squash, or amend.

**Three determinations are kept distinct.** Stage acceptance; publication of that stage; and
**overall Milestone 3.2 T3 implementation acceptance, which had NOT occurred at that acceptance**.
Accepting one stage of the four-stage cadence does not accept the milestone's implementation. **T2.4
and combined T2.5–T2.6 remained owner-gated, unauthorized, and not begun at that acceptance** (stage
T2.4 has since been authorized by accepted Decision 040 and, after the Decision 041 correction and a
passing fresh independent rereview, **accepted and published** by accepted Decision 042, 2026-08-06;
combined T2.5–T2.6 has since been authorized by accepted Decision 045 and **accepted and published**
by accepted Decision 046, 2026-08-07, which also records the overall T3 determination — see the
marker block above); **T4 and each per-window T5 remain separate later owner acts and are not
authorized**.

**Standing state, unchanged by this acceptance.** Both tracked network switches remain `false`
(`network.enabled`, `network.m3_acquire_enabled`). **No transport, real operational catalog,
receipt, evidence artifact, raw object, token, request, attempt, hostname lookup, socket operation,
SEC contact, or acquisition exists or has occurred**; ceiling 801 remains unused; no Gate H has
passed; no stage tag exists. **Seven obligations remained open** at that acceptance for later authorized stages (the first —
singleton bootstrap-absence reason authority — has since been resolved by accepted Decision 040
§4, which approves the `SOURCE_REQUIRED_OBJECT_UNAVAILABLE` code): owner
adjudication of singleton bootstrap-absence reason authority before the T2.4 absence enumeration;
catalog-authoritative adoption after quarantine at T2.4; conditional-request and 304/cache-resume
handling at T2.4; the accepted `RawStore` resource limitation as a T4 preflight and
integrated-candidate-review concern; sanitization or exclusion of untrusted progress-sink messages
before any later receipt or indexed-artifact use; F4 evidence-index vocabulary resolution no later
than T4; and **D023-O1, unchanged, as a latent fail-closed referral condition**.

**Superseded prior markers.** Discharged 2026-08-06:
`CHATGPT_OWNER_REISSUANCE_OF_M3_2_T2_4_CORRECTION_PACKET_AFTER_DECISION_041_PUBLICATION` — the
exact T2.4 correction packet, since reissued and executed, producing the corrected candidate
`625c03d6931e01acc99946ca3924f1cda4da6b76`, which the fresh independent corrected-candidate
rereview passed (`M3_2_T2_4_CORRECTED_CANDIDATE_REREVIEW_PASS`) and the owner then accepted and
published under accepted Decision 042 (2026-08-06, outcome `M3_2_T2_4_ACCEPTED_AND_PUBLISHED`).
Discharged 2026-08-06:
`CHATGPT_OWNER_ISSUANCE_OF_M3_2_T2_4_IMPLEMENTATION_PACKET_AFTER_DECISION_040_PUBLICATION` — the
exact T2.4 implementation packet, since issued and implemented as the superseded first candidate
`5cba2863f47df09c83564258be897a4fd71cf6be`, which the independent T2.4 audit and the read-only
feasibility determination established required correction under accepted Decision 041
(2026-08-06, outcome `M3_2_T2_4_RECOVERY_STATE_PRIMITIVE_AUTHORITY_RECORDED`). Discharged
2026-08-06:
`CHATGPT_OWNER_M3_2_T2_4_IMPLEMENTATION_AUTHORIZATION_AFTER_T2_2_T2_3_PUBLICATION` — the owner's
separate T2.4 implementation-authorization act, since taken as accepted Decision 040 (2026-08-06,
outcome `M3_2_T2_4_IMPLEMENTATION_AUTHORIZED`) and durably recorded and published under the
owner's governance-recording packet. Discharged 2026-08-06:
`CHATGPT_OWNER_ACCEPTANCE_AND_PUSH_DECISION_FOR_M3_2_T2_2_T2_3_AFTER_DECISION_038_RECORDING` — the
owner's acceptance and push decision, since taken as accepted Decision 039. Discharged 2026-08-05:
`CHATGPT_PREPARATION_OF_COMBINED_M3_2_T2_2_T2_3_IMPLEMENTATION_PACKET` — preparation and owner
review of the exact **combined T2.2–T2.3** implementation packet, since issued and implemented as
the accepted candidate above.

**The remaining stages are consolidated** (accepted
[Decision 037](../Docs/Decisions/decision_037_m3_2_remaining_stage_combination.md), 2026-08-04,
outcome `M3_2_REMAINING_STAGES_COMBINED`) — issued as the separate explicit owner decision
Decision 035 §7 item 8 requires before any stages may be combined. The cadence is now **four
stages in total**, one complete and three remaining:

| Stage | State | Exact commit subject |
|---|---|---|
| **T2.1** — configuration and fail-closed command-authority layer | **complete, accepted, published** (Decision 036) | `Implement M3.2 T2.1 authority layer` |
| **T2.2–T2.3 (combined)** — catalog, immutable storage, and acquisition engine | **ACCEPTED AND COMPLETE** (Decision 039) at candidate `6b189df1…`; independently rereviewed; envelope amendment recorded (Decision 038); publication authorized by one normal fast-forward push, **no tag** | `Implement M3.2 T2.2-T2.3 acquisition foundation` |
| **T2.4** — recovery, reconciliation, and drift control | later owner-gated stage | `Implement M3.2 T2.4 recovery and reconciliation` |
| **T2.5–T2.6 (combined)** — operator surfaces and integrated implementation candidate | **AUTHORIZED and NOT BEGUN** (Decision 045, 2026-08-07); produces the **implementation-freeze candidate** for independent T3 review; requires the separate owner-issued execution packet before any executable work | `Complete M3.2 T2.5-T2.6 integrated implementation` |

Each remaining stage gets its own exact packet, produces **at most one commit** that stays local
until ChatGPT review and acceptance, then one normal fast-forward push; the next stage may not
begin before the prior is accepted and published; **the three remaining candidates may not be
combined further** without a new explicit owner decision; and **no interim stage tag or T3 tag is
authorized**. A combined stage may use internal validation subphases but yields one coherent
candidate — within T2.2–T2.3 no owner review is required between the catalog/storage and
acquisition-engine subphases **unless** an authorized-path expansion, migration, new reason code,
or frozen-receipt-schema insufficiency appears necessary, the accepted architecture cannot be
implemented as written, or a BLOCKER or relevant MAJOR finding arises — each an immediate stop.
Decision 037 supersedes **only** the T2 packet's remaining-stage cadence and commit-boundary
provisions; the packet is byte-unchanged (SHA-256 `62120146…`) and all its other requirements
remain controlling. Post-amendment contract SHA-256
`c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7`.

`CHATGPT_PREPARATION_OF_M3_2_T2_2_IMPLEMENTATION_PACKET` is **superseded (2026-08-04)** by the
combined-stage marker above, under accepted Decision 037.

**Stage T2.1 is complete** (accepted
[Decision 036](../Docs/Decisions/decision_036_m3_2_t2_1_stage_completion.md), 2026-08-04, outcome
`M3_2_T2_1_ACCEPTED_AND_PUBLISHED`): the configuration and fail-closed command-authority layer was
implemented within its exact six-path authorization, reviewed, owner-accepted, and **published** at
commit `7b2ffe643a2e2e600f148592fc9f8ded5695a279` (parent
`9730f8b564f49b8fdba76da31cf6d2fa0b6aacc6`) by one normal fast-forward push with **no tag**.
Targeted validation was **126 passed, with no skipped and no xfailed test**, alongside clean ruff,
format, mypy, secrets, hygiene, and diff-check gates. **Both tracked network switches remain
`false`** (`network.enabled` unchanged in semantics; `network.m3_acquire_enabled` added with a
tracked default of `false` and consumed by no code path yet), **all six M3.2 command surfaces
remain fail-closed** at exit 3 without traceback, and **no transport, operational catalog, receipt,
evidence artifact, raw object, token, logical request, physical attempt, hostname lookup, socket
operation, or SEC contact occurred**. **The remaining stages — combined T2.2–T2.3, separate T2.4,
and combined T2.5–T2.6 under accepted Decision 037 — remain owner-gated and unauthorized**,
`NETWORK_AUTHORIZATION` remains `NONE`, the ceiling **801 remains unused**, and no implementation
beyond T2.1 has begun. Accepted [Decision 035](../Docs/Decisions/decision_035_m3_2_t2_staged_implementation_authorization.md)
remains the controlling staged T2 authorization, including its §6 fifteen-path maximum envelope —
a ceiling, not a grant, with any out-of-subset need an immediate stop for new owner adjudication.

`CHATGPT_ISSUANCE_OF_M3_2_T2_1_IMPLEMENTATION_PACKET` is **discharged (2026-08-04)** — the packet
was issued, the stage was implemented, accepted, and published. Its historical statement follows:
the ChatGPT owner issues the exact
T2.1 implementation packet. **No implementation session may begin without it.** The owner
authorized staged M3.2 T2 implementation on 2026-08-04 (accepted
[Decision 035](../Docs/Decisions/decision_035_m3_2_t2_staged_implementation_authorization.md),
instrument `OWNER_M3_2_T2_IMPLEMENTATION_AUTHORIZATION: APPROVED_WITH_STAGE_LIMIT`, outcome
`M3_2_T2_STAGED_IMPLEMENTATION_AUTHORIZED`), which: approves **T2 packet revision v2** (SHA-256
`621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599`) as the controlling
implementation plan and preserves it unchanged; determines **all five Decision 024 §8 entry
conditions satisfied** for the bounded staged implementation; fixes the **fifteen-path maximum T2
envelope** (packet §5 P1–P8, T1–T7) subject to narrower per-stage subsets, with any out-of-subset
need an **immediate stop for new owner adjudication**; **amends contract §22** to the six-stage
**T2.1–T2.6** commit and review cadence (at most one commit per stage with the exact packet §6
subject; no interim commit inside a stage; each stage commit local until ChatGPT reviews and
accepts it, then one normal fast-forward push; no next stage before the prior is reviewed,
accepted, and published; no combining stages; **no stage tag and no T3 tag**; the T2.6 commit as
the implementation-freeze candidate) — **staging and commit governance only**, altering no route,
plan, ceiling, storage, recovery, evidence, or live-operation rule; and grants **immediate
executable authority for stage T2.1 alone**, bounded to `configs/project.yaml`,
`src/disclosure_drift/config.py`, `src/disclosure_drift/cli.py`,
`src/disclosure_drift/m3/__init__.py`, `tests/integration/test_m3_cli.py`, and
`tests/unit/test_config.py`. **Stages T2.2–T2.6 remain owner-gated and are not authorized to
begin.** T2.1 may implement only the tracked-default `network.m3_acquire_enabled: false`, the one
`NetworkSection` field, strict fail-closed configuration behaviour, parser and dispatch skeletons
for all six M3.2 surfaces, refusal behaviour including the `m3 acquire --live` refusal skeleton,
proof that no transport can be constructed and that M2.2 commands remain governed only by
`network.enabled`, and the named T2.1 tests and positive controls — and **must not** implement
acquisition, storage integration, reconciliation, drift processing, recovery repair,
dependent-plan derivation, receipt emission, or transport construction, nor invent any fake
machine-readable "T3 accepted" or "T5 authorized" boolean, token, bypass, or hard-coded
authorization. **No implementation has begun**; network, CompanyFacts, live SEC access,
acquisition, operational-catalog creation, and ceiling-801 use all remain unauthorized; the **F4
evidence-index vocabulary decision remains open and is due no later than T4** and before the
first affected artifact is publicly indexed.

`CHATGPT_OWNER_REVIEW_OF_M3_2_T2_IMPLEMENTATION_AUTHORIZATION_PACKET` is **discharged
(2026-08-04)** — the owner reviewed and approved packet revision v2 and issued the staged T2
authorization recorded above. Its historical statement follows: the ChatGPT owner's
review of the prepared T2 packet,
[`Docs/m3/m3_2_t2_implementation_authorization_packet.md`](../Docs/m3/m3_2_t2_implementation_authorization_packet.md)
(`DRAFT T2 IMPLEMENTATION-AUTHORIZATION PACKET — PENDING CHATGPT OWNER REVIEW`;
`IMPLEMENTATION AUTHORIZATION: NOT GRANTED`), prepared 2026-08-04 under
`OWNER_M3_2_T2_PACKET_PREPARATION_AUTHORIZATION: APPROVED` and **revised the same day to v2 under
the owner's detailed preparation instruction** — v2 supersedes the v1 draft in place at the same
path (v1 preserved in history at commit `60865c0…`), and this marker supersedes the interim
`OWNER_M3_2_T2_IMPLEMENTATION_AUTHORIZATION_DECISION` marker for the same owner act. The v2
packet audits the five Decision 024 §8 entry conditions and concludes
`READY_FOR_OWNER_T2_DECISION`; enumerates the exact fifteen authorized implementation paths
(eight production, seven test) and keeps both conditional surfaces
(`sec/census_orchestrator.py`, `sec/index_retrieval.py`) declined and prohibited; dispositions
all six planned commands in full; proposes six bounded stages T2.1–T2.6 with **one commit per
stage and a ChatGPT owner review boundary between stages — adopting that cadence requires the
owner's T2 instrument to amend the accepted contract §22 one-commit default, an adjudication the
packet routes to the owner rather than resolving**; fixes stage-specific model routing; carries
R1, F3, and F4 in full; and reproduces the proposed T2 instrument unissued. **Preparing the
packet authorized nothing and approved nothing** — T2 is ungranted until the owner issues that
instrument, and no executable byte may change before then. T3 (implementation acceptance), T4
(live-operation preflight), and each per-window T5 remain separate later owner acts.
**Nothing in this file authorizes a session to begin M3.2 implementation, enable SEC network
access or CompanyFacts, contact the SEC, begin acquisition, create or populate an operational
catalog, use the ceiling 801, or create any tag.**

`PREPARE_M3_2_T2_IMPLEMENTATION_AUTHORIZATION_PACKET` is **discharged (2026-08-04)** — the packet
described above was prepared, governance-only, changing no executable byte. Its historical
statement follows: preparation, for owner review, of the
bounded M3.2 T2 implementation-authorization packet (accepted
[Decision 034](../Docs/Decisions/decision_034_m3_2_contract_acceptance.md) §13; Decision 024 §8;
[`contracts/m3_2.md`](contracts/m3_2.md) §8, T2 row), as the owner directs. The packet must
satisfy all five Decision 024 §8 entry conditions and must carry the Decision 034 §6 R1 content:
the physical persistence location for item-level absent-object identities; the physical
representation of the `completed_with_absences` governance classification; the deterministic
linkage among the frozen receipt, the operational catalog, `m3 reconcile-requests`, and the
Gate H reconciliation; and tests proving `m3-execution-receipt/2.0` remains frozen with its
completion-status enumeration not silently extended. **Preparing or drafting the packet
authorizes nothing and approves nothing** — it must return to the ChatGPT owner for a separate
explicit T2 implementation-authorization decision, and no implementation may begin before that
decision. T3 (implementation acceptance), T4 (live-operation preflight), and T5 (per-window
live-operation authorization) remain separate later owner acts.
**Nothing in this file authorizes a session to begin M3.2 implementation, to enable SEC network
access or CompanyFacts, to begin acquisition, to create or populate an operational catalog, or to
create any tag.**

`FRESH_NO_SUBAGENT_INDEPENDENT_REREVIEW_OF_CORRECTED_M3_2_CONTRACT` is **discharged
(2026-08-04)**. The fresh independent rereview of the corrected contract by one non-author
session using no subagents completed 2026-08-04 with verdict
`M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS` — zero BLOCKER, zero MAJOR, one MINOR (R1,
the receipt-enumeration surface, carried forward as mandatory T2-packet content by Decision 034
§6), one OPTIMIZATION (R2, nonblocking) — recorded in the durable artifact
`Docs/m3/reviews/m3_2_corrected_contract_independent_rereview_3bf9987dd72e1531da2f678fbbef735f37aefcf4.md`
(SHA-256 `91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf`, committed
governance-only at `3069b03ede9d805e9d0196a3e4c45c8cc68f42b7`), with independence, no-subagent
execution, and the container-continuity disclosure attested in the artifact's §1. **The owner
then accepted the corrected contract unchanged at T1** (accepted Decision 034, 2026-08-04,
`M3_2_CONTRACT_ACCEPTED_AT_T1`); acceptance grants no T2/T3/T4/T5 authority, enables no network
or CompanyFacts, and authorizes no acquisition, operational catalog, ceiling-801 use, or tag.

`CHATGPT_OWNER_REVIEW_AND_ACCEPTANCE_DECISION_FOR_M3_2_CONTRACT_DRAFT` is **discharged as a
correction decision (2026-08-04)**. The owner ordered the independent contract review of the
initial draft; it completed 2026-08-04 with verdict
`M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS` — zero BLOCKER; two MAJOR
(F1, completion semantics permitting false success; F2, boundary exactness including the unnamed
command-scoped network-enable change); four MINOR; one OPTIMIZATION — recorded in the durable
artifact
`Docs/m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md`
(SHA-256 `fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57`, committed
governance-only at `3fbaa12d671d0000f5b608bbf6fb271f78b4673f`). The owner adopted the findings in
the 2026-08-04 correction instrument recorded verbatim in accepted Decision 032
(`M3_2_CONTRACT_CORRECTIONS_RECORDED`), and the bounded corrections are applied: §14 separates
termination from successful completion and requires every required object present, hash-verified,
and fully provenanced, with any required-object absence enumerated in the window's receipt and
expressly owner-adjudicated before the between-windows freeze and before any M3.2B budget
approval; §16 names the single command-scoped network-enable configuration change
(`network.m3_acquire_enabled`, default `false`, read only by `m3 acquire --live`, with
`network.enabled` remaining `false` throughout every M3.2 window) and the complete expected
implementation and test surface including all six planned M3.2 commands; §12 gains the
conservative accounting rule for a hard-interrupted segment's unrecorded attempts; §20 gates
public indexing of the between-windows freeze artifacts on an authorized index-vocabulary
extension; §§5 and 15 explain the historical Gate-F-named unresolved-count sentinel without
renaming it; §18 requires a non-vacuous positive control for every critical refusal and
nonchange boundary; §19 names the exact nonchange proof; and the stale current-state prose in
[`contracts/README.md`](contracts/README.md) is corrected. **The review artifact is preserved unchanged
as a truthful correction review; per the owner's procedural ruling it does not satisfy the
acceptance-prerequisite review because its session used two read-only fact-gathering subagents
under the one-active-session restriction, so the corrected draft requires the fresh no-subagent
rereview above.** The correction decision authorizes no implementation, no network or
CompanyFacts enablement, no live SEC access, no acquisition, no operational catalog, and no use
of the M3.2A ceiling; implementation, test, script, and executable-configuration bytes remain
byte-identical to the frozen accepted SHA `970e050deb06910adcde8588101564beb7d19c74`.

`DECISION_029_SECTION_12_STEP_17` is **discharged — the seventeen-step sequence is complete.**
Under the owner's explicit step-17 authorization of 2026-08-03: **M3-L11 and M3-L12 were closed**
in the limitations register, each on its own complete closure-evidence list (bounded
implementation and tests in the frozen accepted tree; full validation; independent M3.1
acceptance `M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`; owner acceptance recorded by accepted
Decision 031; and the committed checkpoint — the verified annotated `m3.1-complete` tag), with
the Decision 030 Ruling D sequencing distinction preserved and Decision 013 byte-for-byte
unchanged; and the **bounded M3.2 contract was drafted** at
[`contracts/m3_2.md`](contracts/m3_2.md), status `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE`,
`IMPLEMENTATION_AUTHORIZATION: NO`, `NETWORK_AUTHORIZATION: NONE`. The draft implements master
plan M3.2 §§1–36 and global §16: the frozen M3.2A inputs (plan `19be7bdc…`, budget `2d453e0b…`,
ceiling 801, 75 logical requests, 70 quarterly indexes, 75 raw objects, 0 cache hits, no
contingency, 200.0 s spacing floor), strict stop-before-overflow, the accepted route allowlist
and denylist, redirect/attempt bounds, boundary-only SEC-identity handling, immutable raw-object
capture, per-command receipts, interruption and recovery behaviour, zero filing-body /
CompanyFacts / Frames / outcome access, no pilot selection during acquisition, the six-transition
owner gate ladder (T1 contract acceptance → T2 implementation authorization → T3 implementation
acceptance → T4 live-operation preflight → T5 separate per-window owner live-operation
authorization → T6 controlled execution, then canonical Gate H), and the M3.2B dependency
boundary (no planning before the M3.2A freeze; separately derived plan and budget; a separate
owner ceiling approval; no inheritance of the M3.2A ceiling). D023-O1 is carried forward as a
mandatory stop-and-refer condition. **The draft accepts nothing, implements nothing, enables
nothing, and contacts no SEC host.**

`DECISION_029_SECTION_12_STEP_16` is **discharged.** Under the owner's explicit step-16
authorization of 2026-08-03, the annotated checkpoint tag `m3.1-complete` was created exactly
once at the acceptance commit `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4` with the
convention-consistent annotation "Complete M3.1 acceptance checkpoint" (tag object
`638a02b780d912ff7b37a2f523277b9d451a015a`), pushed as the single ref
`refs/tags/m3.1-complete`, and verified locally and remotely (matching tag objects; matching
peeled targets; `HEAD == origin/main`; every prior tag unchanged; no tracked file changed; no
commit created).

`DECISION_029_SECTION_12_STEP_15` is **discharged.** Under the owner's explicit step-15
authorization of 2026-08-03, the owner's M3.1 acceptance is durably recorded: accepted
[Decision 031](../Docs/Decisions/decision_031_m3_1_acceptance.md) (`ACCEPTED — OWNER APPROVED
2026-08-03`, outcome `M3_1_ACCEPTED_AND_COMPLETE`) carries the verbatim owner instrument
(`OWNER_M3_1_ACCEPTANCE_DECISION: APPROVED`, 2026-08-03), bound to the independent-review commit
`24fba32413bb6c5dade60a64182e42510afe6f88` and review-artifact SHA-256
`caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`; the decision registry gains
row 031; M3-L11 and M3-L12 move to `CLOSURE-READY PENDING STEP 16` (neither closed — the
committed checkpoint tag is the sole remaining closure criterion); and this ledger records the
position. The acceptance commit is governance-only: implementation and test bytes remain
byte-identical to the frozen accepted SHA `970e050deb06910adcde8588101564beb7d19c74`. It creates
no tag and authorizes no Gate F execution, no live SEC access, and no M3.2 work.

`DECISION_029_SECTION_12_STEP_14` is **discharged.** The independent M3.1 acceptance review ran
on 2026-08-03 under explicit owner authorization, performed by a fresh session that authored none
of the M3.1 implementation, governance, review, rehearsal, planning, budget, checklist, token,
index, or status work. From a fresh external independent clone it re-ran the full phase-end
validation (ruff, format, mypy, full suite 2739 passed / 1 pre-existing skip with the transport
test run, sqlite-check, secrets, hygiene, context — all green), recomputed every accepted private
and public evidence SHA-256, independently reproduced the route witnesses, plan determinism, and
ceiling arithmetic (801 = 31 + 11 × 70), and answered all forty adversarial questions in the
accepting direction, including the step-13 token-mechanism and living-evidence-index authority
questions. Verdict: `M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`, with zero BLOCKER, zero MAJOR,
three MINOR findings (an environmental disk-exhaustion incident with a clean re-run;
same-device-only backups; the superseded M3-L12 register wording), and zero OPTIMIZATION
findings. Its durable artifact is
`Docs/m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md`
(SHA-256 `caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e`), committed
governance-only at `24fba32413bb6c5dade60a64182e42510afe6f88`. The review recorded a verdict
only; the owner's separate acceptance followed and is recorded by Decision 031.

`DECISION_029_SECTION_12_STEP_13` is **discharged.** The owner explicitly authorized step 13 on
2026-08-03. Every precondition was independently reverified read-only immediately beforehand (the
signed checklist's identity and `PASS` result; the exact acceptance reference; the operator
acknowledgement; the owner's evidence-index attestation; SEC identity valid at the boundary with
the value never displayed; network and CompanyFacts disabled; secrets, hygiene, and context
green; implementation bytes unchanged; zero live SEC requests; no prior token artifact or
emission). No canonical command exists for this token — the literal appears nowhere in the
implementation — so the recording used the repository's established governance-evidence
mechanism: a create-once, immutable private record in the evidence root's M3.1B run directory,
3,982 bytes, 62 lines, SHA-256
`b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e`, carrying the token literal
exactly once in its emitted-token field and binding it to the signed checklist
(`34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc`), the request plan
(`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`), the request budget
(`2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f`), the approved hard request
ceiling 801, the checklist baseline `55cf244a00428fbc8fa38d7b70af1bac8a7c45e9`, the public
step-12 recording commit `0334294bd420a829033094080a13e4df900da078`, and the date 2026-08-03 —
together with this public ledger marker. The after-step-13-token local backup verified completely
(14 files, every SHA-256 matching; `.env` excluded). The owner's evidence-index attestation is
recorded verbatim in the index's §8. The immutable signed checklist is unaltered: its signing-time
statement that the token was then unemitted remains historically correct. **The token records
readiness only.**

`DECISION_029_SECTION_12_STEP_12` is **signed and complete.** The final signing preflight
(2026-08-03) validated the owner-approved SEC contact identity at the canonical boundary
(`SEC contact identity: valid; value not displayed`; the value lives only in the ignored local
configuration and is never printed), synchronized `main` by one authorized, ancestry-proven,
normal fast-forward push and verified `HEAD == origin/main` at
`55cf244a00428fbc8fa38d7b70af1bac8a7c45e9`, and recorded the operator-runbook acknowledgement.
The owner then signed the checklist on 2026-08-03 — Owner **Joseph Nihill, project owner acting
through the ChatGPT owner decision**; Gate F result **`PASS`**; recorded acceptance reference
bound to the repository baseline `55cf244a00428fbc8fa38d7b70af1bac8a7c45e9`, the request-plan
SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, the request-budget
SHA-256 `2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f`, and the sanitized §17
review SHA-256 `9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3` (a transparent
recorded owner acceptance reference, not a handwritten, cryptographic, or third-party digital
signature). The **signed checklist** was instantiated once, immutably, in the evidence root's
M3.1B run directory — 23,463 bytes, 284 lines, SHA-256
`34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc` — with every template field
populated, every item `PASS`, no unresolved blocker, the operator acknowledgement and the
Decision 030 dispositions included, and the two explicit step-13 boundary lines preserved (the
readiness token **not emitted**; Gate F authorization **not granted**; the token literal occurs
nowhere in the artifact). The after-step-12-signed local backup verified completely (13 files,
every SHA-256 matching; `.env` excluded), and the public evidence index
([`Docs/m3/templates/evidence_index.md`](../Docs/m3/templates/evidence_index.md) — the recording
destination the M3.1 contract §6, master plan §§12.1/12.3 and M3.1 §30, and the operator runbook
name) now carries the eight non-sensitive M3.1A/M3.1B rows `EV-M31A-001`–`EV-M31B-006`,
including the signed checklist's digest; its §8 owner attestation remains pending.

The next required owner action: **review the bounded M3.2 contract draft and accept, correct, or
decline it** (transition T1 of the draft's §8 gate ladder), ordering its independent contract
review as the owner directs. Acceptance would be T1 only: M3.2 implementation authorization (T2,
under all five Decision 024 §8 conditions), implementation acceptance (T3), live-operation
preflight (T4), and each per-window live-operation authorization (T5) all remain separate,
explicit, later owner acts. No session may accept the contract, begin implementation, enable SEC
network access, or begin acquisition without them.

**The step-12 hygiene blocker is resolved.** Accepted
[Decision 030](../Docs/Decisions/decision_030_gate_f_step_12_owner_rulings_and_hygiene_remediation.md)
(`ACCEPTED — OWNER APPROVED 2026-08-03`, outcome
`GATE_F_STEP_12_OWNER_RULINGS_AND_HYGIENE_REMEDIATION_ACCEPTED`) authorized exactly one provably
non-substantive redaction of the machine-local absolute path material in the §17 review
artifact's clone-provenance sentence. The pre-redaction artifact identity
`sha256:73cb1eacf0fb5e29a8a1c2ea871692068caf3ebdc48cae161d6aef677ba8f3a3` remains the historical
identity of the owner-accepted review (its introducing commit is retained; history was not
rewritten); the sanitized tracked identity is
`sha256:9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3`. A normalized
comparison proved in both directions that the sole change is the approved substitution; the
verdict `M3_1_SECTION_17_REVIEW: PASS` occurs exactly once, unchanged; no completion-token
literal was added; implementation, test, script, and configuration bytes remain byte-identical to
the frozen reviewed SHA; the hygiene scanner was not weakened and no allowlist was created; and
`make hygiene` now passes with zero findings while `make secrets` continues to pass. Decision 030
also records the owner's Gate F interpretation rulings: the three request-budget response-outcome
markers are **permitted and nonblocking** (all §3 route counts resolved; the expectations are
intentionally resolved during controlled acquisition; no integer guessed);
**`M3-L12 GATE-F-FACING REQUIREMENT: SATISFIED`** — Gate-F-facing requirement satisfied;
administrative closure deferred to the later M3.1 acceptance and checkpoint sequence — blocking
neither checklist preparation, the owner step-12 signature, the step-13 readiness token, nor
beginning Gate F after valid step-13 authorization; and
**`D023-O1: LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED`**, stop-and-refer
if a lawful real run ever reaches it.

`DECISION_029_SECTION_12_STEP_9` is **discharged.** The single authorized offline operational
rehearsal ran on 2026-08-03 at `2026-08-03T12:35:01Z`, exit status `0`. All twelve A1–A12 scenarios
passed; `passed`, `complete`, `a_reachable_agrees`, and `a_reachable_fully_tested` are all true;
derived and tested route-key sets are equal across all nine routes with `unmeasured_routes` empty;
`actual_logical_request_count` and `actual_physical_attempt_count` are both `0`; and the canonical
command emitted `M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED`, durably captured. Its three immutable
artifacts live under the external evidence root at
`runs/m3_1a_rehearsal_970e050deb06910adcde8588101564beb7d19c74/` — evidence report
`sha256:6308576a0a7df33813239f753b31b86754f3908d63d73e6521682db06a59e1e0`, receipt
`sha256:ea1f4be2c136827ac5d865eea0fabf73f0f716802e2ee8cd23aedf1965dbc81b` (`receipt_id`
`1c1980429833e41f6eaf07d3df7fb5a780daab2ffe291d9a67858821a1a618d6`), and stdout log
`sha256:4b42f95e4a00d5865eeb05ccc9f06fe08c51c68f07c56d5512d441c2ee7118ce`. The absolute private path
is never recorded here.

`DECISION_029_SECTION_12_STEP_10` is **discharged.** Under owner-supplied plan inputs (coverage
2009-01-01 → 2026-06-30, as-of 2026-06-30, calendar year 2026, an explicitly empty operator
calendar-evidence manifest, and a nonexistent operational catalog), `m3 plan-requests` ran exactly
twice on 2026-08-03 to different immutable output names and produced **byte-identical plans**:
request-plan SHA-256 `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` for both
files, under schema `m3-request-plan/1.0` and planner policy `quarterly-index-instances/2.0`. The
plan enumerates the seven M3.2A bootstrap routes with **q = 70** required quarterly-index
instances (2009QTR1–2026QTR2, including the closed 2026 Q2 required by Decision 013 §1), zero
already-satisfied instances, **75 planned unique logical requests**, **801 maximum physical
attempts**, 75 maximum new raw objects, 0 expected cache hits, and a 200.0-second rate-limiter
spacing floor. Both dry-run receipts validate (`invocation_mode` `dry_run`; actual logical-request
and physical-attempt counts both `0`). The accepted classification is
`STEP_10_PASS_BYTE_IDENTICAL`. The artifacts are immutable under the external evidence root at
`runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/` — both plans
`sha256:19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, receipts
`sha256:d7f602d8a537c925483cbb9b5021ca0313eb3288d26dcb7759aa9b1843f4f149` and
`sha256:ff116259d5f129aba94093bd0516b14fdbb4a5517538a2c29d59240823573111`, stdout logs
`sha256:e3bf5650871bde150dde4a2fe48f0bfbbb26e821a52750a9e90f000b2396cfff` and
`sha256:660e9c01396af9dfa471f160c6a11e8ecbee04b45db97f410286a02fa7d43bce`. The absolute private
path is never recorded here.

`DECISION_029_SECTION_12_STEP_11` is **discharged.** The read-only canonical `m3 show-budget`
command rendered the stored plan's eight governed budget quantities and the derived hard request
ceiling **801** (`31 + (11 × 70) = 801`), captured at
`runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/show_budget_stdout.log`
(`sha256:0e6722dcd960c54a49e4a1af44a5c15587d03109b262c7ee471a46b8071db508`); the accepted
classification is `STEP_11_BUDGET_DISPLAY_PASS`. **The owner approved the exact plan-bound hard
request ceiling 801 on 2026-08-03**, bound to request-plan SHA-256
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`, with 75 planned unique logical
requests, 75 maximum new raw objects, 0 expected cache hits, and no contingency allowance. **Three
response-outcome quantities remain deliberately unresolved** as
`EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN` by the owner's ruling — expected successful
responses, expected not-modified responses, and expected governed non-success responses; no
integer was approved or invented for them. The approval completes step 11 only: it does not
complete or sign the Gate F checklist, does not emit the readiness token, and does not authorize
live SEC access.

**Step 12 preparation is complete; the owner signature is outstanding.** The refreshed
after-step-11 local backup of the external evidence root verified completely (11 files, every
SHA-256 matching, including the canonical budget display and all step-9 and step-10 evidence),
and the private **M3.2A request-budget document** was then created once, immutably, in the
evidence root's M3.1B run directory — 21,633 bytes, 307 lines, SHA-256
`2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f` — recording the plan-derived
quantities, the per-route independently tested `A_reachable` witnesses, the verbatim owner ceiling
approval of 2026-08-03, and the three deliberately unresolved response-outcome markers. The
after-step-12-prep local backup then verified completely (12 files, every SHA-256 matching, budget
document included). **Both backups are same-device protection against accidental deletion only,
not an off-device or device-loss backup; a separate owner-controlled off-device backup remains an
owner matter.** The proposed completed Gate F checklist was prepared with every supported
non-owner field populated and returned for the owner's step-12 signature decision; **no owner
field was signed, the checklist was not written to the repository or the evidence root, the
readiness token was not emitted, and Gate F was not begun.** The one blocker that preparation
referred for owner adjudication — a machine-local absolute path in the committed §17 review
artifact's clone-provenance sentence — **is resolved by accepted Decision 030** (see the next
section): the redaction is proven non-substantive, the review verdict is unchanged, and
`make hygiene` now passes with zero findings.

`FIRST_DURABLE_M3_1_SECTION_17_REVIEW` is **discharged and historical.** The M3.1 implementation was
frozen at `970e050deb06910adcde8588101564beb7d19c74`; a session that wrote none of the M3.1 work
produced
[`Docs/m3/reviews/m3_1_section_17_review_970e050deb06910adcde8588101564beb7d19c74.md`](../Docs/m3/reviews/m3_1_section_17_review_970e050deb06910adcde8588101564beb7d19c74.md)
with the verdict **`M3_1_SECTION_17_REVIEW: PASS`**; that artifact was committed governance-only at
`66e4c5433a393815c74f9e3087300613a516e2fb`, with the implementation bytes unchanged across that
commit; and the project owner accepted the review and its artifact.

`INDEPENDENT_M3_1_CONTRACT_REVIEW` is likewise **discharged and historical**: `contracts/m3_1.md` was
reviewed, corrected, and accepted with `IMPLEMENTATION_AUTHORIZATION: YES`.

The
[Decision 029](../Docs/Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md)
§12 sequence is **complete — all seventeen steps discharged**. The M3.1A rehearsal token, the two
byte-identical zero-request plans, the passing canonical budget display, the owner-approved hard
request ceiling 801, the Decision 030 hygiene remediation and Gate F interpretation rulings, the
validated SEC contact identity (value never displayed), the operator acknowledgement, the
owner-signed Gate F checklist (result `PASS`, SHA-256 `34fc0567…`), the owner's evidence-index
attestation, the Gate F readiness-token record (SHA-256 `b06ae373…`, token emitted exactly once),
the passed independent step-14 acceptance review (verdict
`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS`; artifact SHA-256 `caf9f26e…`; commit `24fba32…`),
the owner's M3.1 acceptance recorded by accepted Decision 031 (`M3_1_ACCEPTED_AND_COMPLETE`),
the verified annotated `m3.1-complete` checkpoint (step 16; tag object `638a02b7…`, peeled
`4cd2c72…`), and the step-17 closure recording and bounded M3.2 contract draft
([`contracts/m3_2.md`](contracts/m3_2.md)) all exist as durable evidence, with the evidence-root
states backed up same-device through the after-step-13-token snapshot and the public evidence
index carrying the non-sensitive references and the recorded owner attestation. **The readiness
token records readiness only: Gate F execution has not begun, and no live SEC access is
authorized.** M3.1 is **owner-accepted and checkpointed**; the M3.2 contract is **an unaccepted
draft**; M3.2 onward is **not authorized**.

Milestones 0, 1, and 2 are formally closed
([Decision 026](../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md),
`MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`), the closeout commit is pushed, and the three
annotated completion tags `m0-complete`, `m1-complete`, and `m2-complete` exist at it. **Milestone 3
master planning is complete at Decision 027 v0.2; accepted Decisions 028 and 029 are correction and
remediation records, not implementation contracts; and the separate M3.1 contract is accepted and
implementation-authorized, with its implementation present in the tree but not accepted.**

**The Decision 028 review chain produced the required pass.** The Decision 027 v0.1 review's eleven
corrections were recorded at v0.2. Later bounded documentation corrections were committed and pushed
at `c91af08`; they are not “uncommitted.” The subsequent focused architecture review and Sol
reconciliation found additional issues: M3-L12 is an inherited planner defect, A5 and A11 need
registered reasons, A1–A12 need corrected semantics, receipts must become v2 before the first
receipt exists, budget and ceiling language must be repaired, and M3-L11 needs three-layer
implementation protection. Accepted Decision 028 records those rulings, and its fresh rereview
returned `INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`.

**The focused rereview must verify** (Decision 027 §23):

- all Decision 024 obligations are represented **exactly once**;
- each M3 phase has complete inputs, outputs, permissions, stop conditions, validation, recovery,
  tokens, and checkpoint policy;
- **every corrected subdivision is internally consistent** — M3.1A rehearses only acquisition,
  M3.2's two windows each carry their own plan and approval, M3.3A precedes M3.3B, and M3.4 is never
  documentary;
- **no scenario is placed in a phase that lacks the production path it exercises**;
- the operator runbook is executable as documentation **without pretending planned commands already
  exist**;
- **no withdrawn count, plan hash, `A_max`, or contingency survives anywhere as an accepted value**;
- M3-L12 is correctly classified as an inherited implementation defect; Decision 013 is unchanged;
  the total order and `quarterly-index-instances/2.0` boundary are complete;
- request budgeting excludes cache hits before planning, never subtracts them twice, records maximum
  new raw objects correctly, and labels the rate-limiter expression only as a spacing floor;
- ceiling equality is `actual <= ceiling`, with a complete reconciled plan separately required;
- execution receipts use `m3-execution-receipt/2.0`, have feasible field timing, cannot contaminate
  accepted identities, and carry exactly one integrity identity;
- the corrected A1–A12 matrix, both new reason codes, and M3.1/M3.2 recovery ownership are internally
  executable and fail closed;
- M3-L11's ignore, hygiene, resolved-path, ancestor, and symlink protections are complete as future
  contract requirements;
- the two-layer evidence model is applied consistently across the master plan and every template;
- templates and limitations are complete;
- **no implementation authority was granted**;
- **no live access occurred.**

That sequence is complete through Decision 028 §14 step 4: Decision 028 passed review, was accepted,
validated, and checkpointed, and the bounded M3.1 contract has since been reviewed, corrected, and
**accepted** with `IMPLEMENTATION_AUTHORIZATION: YES` under all five Decision 024 §8 conditions.

**No Milestone 3 implementation authority exists beyond the bounded M3.1 grant.** Closure satisfied
only the precondition Decision 024 §8 imposed. All five Decision 024 §8 conditions are now satisfied
for M3.1 (a separate accepted governance record — Decision 028; a bounded implementation contract —
`contracts/m3_1.md`; explicit owner authorization under the 2026-08-01 delegation; exact path
authorization in §§6–7; and inherited prerequisite gates via Decision 026), so
`IMPLEMENTATION_AUTHORIZATION` reads `YES` for M3.1 and the M3.1 contract is **accepted**. The five
conditions remain unsatisfied for every later phase, whose authorization stays `NO`, and **no live
SEC access, real pilot execution, real snapshot, real manifest construction, root approval, or
publication is authorized.** **No Gate F has passed, the M3.3A execution rehearsal (E1–E8) has not
been run (the M3.1A acquisition rehearsal A1–A12 ran and passed on 2026-08-03), no live acquisition
occurred, and no Gate H has passed.**

**Two conditions remain owner-facing.** **D023-O1** is inherited and referred only if a real run
reaches it. **M3-L12**'s owner ruling is recorded (Decision 028 §4) and its planner-v2 correction
is implemented in the frozen reviewed tree — the accepted step-10 plan's required-quarter set
includes the **closed** 2026 Q2 exactly as Decision 013 §1 requires, under
`quarterly-index-instances/2.0` — while the register entry remains `ACTIVE` until independent
M3.1 acceptance and a committed checkpoint; Decision 013 remains byte-for-byte unchanged.

**Historical — the approval path that closed the first two gates.**
S6 governance is drafted and has been through **three** full review cycles: the v0.1 review returned
`REQUIRES_OWNER_CLARIFICATION` and produced six bounded corrections applied at v0.2; v0.3 widened the
structural-fingerprint tuple to five columns; the v0.3 review **also** returned
`REQUIRES_OWNER_CLARIFICATION`, producing the two corrections v0.4 applied; and the v0.4 review
returned it a **third** time, producing the v0.5 ruling that grows migration `0013` to eight
triggers. **v0.2 was never independently reviewed, and no completed review covers the eight-trigger
SQL or the §15.5 guarantee, so the review may not inherit an earlier recommendation.** Decision 021
v0.5 freezes the manifest, document, and terminal-result architecture, including the **exhaustive
81-item §10 crosswalk** (§13.2.1) and the complete **eight-block** migration-`0013` SQL (§15.1) with
its **nine** normative digests, byte and line counts, and concatenation rule (§15.3), and
`Milestones/contracts/m23_s6.md` was `BLOCKED_PENDING_DECISION_021` at the time and is now
`READY_FOR_IMPLEMENTATION`. The review covered that exact SQL and its digests, the **§15.5 append-once and identity guarantee** and its nine clauses, the
crosswalk and its frozen counts, every digest preimage in Decision 021 §§6–9 **including the
eleven-field §8.4 selector-policy layer and the §8.1 five-column fingerprint rule**, the §10
circularity exclusions and the §10.1 commitment closure, the §9.2 six-field identity-immutability
ruling, and the §13 document contract. After it, in order: owner approval of Decision 021 v0.5
recorded in the registry, then separately issued bounded S6 implementation prompts. **All three
gates closed**, the stage was implemented and independently accepted, and Decision 023 records the
result. The S6 handoff conditions in
[`Milestones/contracts/m23_s5_4.md`](contracts/m23_s5_4.md) record which prerequisites S5.4 already
satisfied; the fifth — `selection_result_sha256` — is now settled by Decision 021 §6, which populates
it at S6 under the existing `pilot-manifest/1.0` policy. No further S5.4 work is authorized without a
new explicit owner authorization.

## Deferred stages

- **S5.4 (reserves)** — no longer deferred and no longer current: **complete and owner-accepted
  2026-07-30**, checkpointed at `m2.3-s5.4-complete`. See "Completed stages" and "Current stage".
- **S6 (pilot manifest construction)** — no longer deferred and no longer current: **complete and
  owner-accepted 2026-07-31**, checkpointed at `m2.3-s6-complete`. See "Completed stages" and
  "Current stage". No manifest approval, publication, CLI, or release work is authorized (Decision
  018 §22, Decision 021 §§11.1, 16, 17; Decision 023 §9); see `Docs/architecture_map.md` §8.
- **The former Stages S7–S10** — **no longer Milestone 2 stages.** Decision 024 §5.1 transferred them
  **intact** into Milestone 3: Gate F live-metadata readiness → **M3.1**; controlled metadata-only SEC
  acquisition with Gate H → **M3.2**; the frozen real candidate snapshot, deterministic execution, the
  exact real-data manifest, and the CLI output deferred from S6 → **M3.3**; explicit owner approval of
  the exact root hash → **M3.4**. A new **M3.5** covers integrated real-pilot acceptance and Milestone
  3 closeout. **Every gate, prohibition, owner ruling, validation requirement, identity, methodology,
  and accepted limitation is preserved.** None has begun; none is authorized; none is reachable — no
  candidate-snapshot builder and no production catalog exists, and no S7 or Milestone 3 contract
  exists.
- **Milestone 2 / Milestone 3 boundary governance** — **complete.** Recorded in Decision 024,
  `ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED`. Governance
  only; it authorized no implementation and no tag.
- **Final independent integrated Milestones 1 and 2 audit** — **complete.** Read-only and
  adversarial; it returned `REQUIRES_BOUNDED_INTEGRATED_FIXES` with nine categories
  `INTEGRATED_ACCEPTANCE_CONFIRMED` and one bounded documentation finding, recorded in Decision 025.
  It recorded no closeout and authorized no implementation.
- **Bounded correction, independent verification, final bounded fix, and fresh rereview** —
  **complete.** The rereview returned
  `ACCEPT_BOUNDED_FIXES_AND_AUTHORIZE_MILESTONES_0_1_AND_2_FORMAL_CLOSEOUT` with no remaining
  closeout blocker, and explicitly completed the outstanding **Milestone 0** classification.
- **Formal Milestone 0, Milestone 1, and Milestone 2 closeout** — **complete.** Recorded in
  [Decision 026](../Docs/Decisions/decision_026_milestones_0_1_2_final_closeout.md),
  `ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`.
  Governance only; it authorized one commit, one push, and the three annotated completion tags
  `m0-complete`, `m1-complete`, and `m2-complete`, and granted no implementation authority.
- **Milestone 3 master planning and governance** — **complete at v0.2.** Recorded in
  [Decision 027](../Docs/Decisions/decision_027_m3_master_plan_and_operational_readiness.md),
  `ACCEPTED — OWNER APPROVED 2026-07-31`, outcome
  `M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`. Planning and documentation only; the
  v0.1 recording and the v0.2 correction each authorized one commit and one push, **no tag**, and
  granted no implementation authority. Neither implemented, contracted, enabled network access,
  acquired metadata, snapshotted, ran a pilot, built a manifest, approved a root, or published —
  Decision 026 §§19–20 observed in full.
- **Independent Milestone 3 master-plan review** — **complete for v0.1.** Its eleven corrections are
  applied and recorded in Decision 027 §0.
- **Independent Milestone 3 master-plan REREVIEW** — **complete; it passed**
  (`INDEPENDENT_M3_MASTER_PLAN_REREVIEW: PASS`, recorded by accepted Decision 028). Read-only and
  focused, by a session that authored neither v0.1 nor the v0.2 corrections; it recorded no
  acceptance of implementation and authorized none.
- **Milestone 3 implementation** — **the bounded M3.1 phase is complete and OWNER-ACCEPTED
  (accepted Decision 031, 2026-08-03, outcome `M3_1_ACCEPTED_AND_COMPLETE`); its implementation is
  frozen at `970e050deb06910adcde8588101564beb7d19c74`.**
  Decision 029 code remediation is complete, and the first durable §17 review passed
  (`M3_1_SECTION_17_REVIEW: PASS`, artifact committed at
  `66e4c5433a393815c74f9e3087300613a516e2fb`, owner-accepted). The Decision 029 §12 step 9
  operational rehearsal ran once on 2026-08-03 and passed, emitting the M3.1A token; steps 10 and
  11 completed on 2026-08-03 — two byte-identical zero-request plans (request-plan SHA-256
  `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`) and the owner-approved hard
  request ceiling 801; step 12 was signed and completed on 2026-08-03 — its sole hygiene blocker
  resolved by accepted Decision 030, the signing preflight satisfied, and the owner-signed Gate F
  checklist (result `PASS`, SHA-256 `34fc0567…`) durably recorded and publicly referenced in the
  evidence index; step 13 completed on 2026-08-03 under separate owner authorization — the Gate F
  readiness token recorded exactly once (record SHA-256 `b06ae373…`); step 14 (the independent
  acceptance review) completed and passed on 2026-08-03 (`M3_1_INDEPENDENT_ACCEPTANCE_REVIEW:
  PASS`; artifact SHA-256 `caf9f26e…`; commit `24fba32…`); and the owner accepted M3.1 on
  2026-08-03, recorded at step 15 by accepted Decision 031. Step 16 created and pushed the
  annotated `m3.1-complete` checkpoint (2026-08-03; tag object `638a02b7…`, peeled `4cd2c72…`),
  and step 17 closed M3-L11 and M3-L12 and drafted the bounded M3.2 contract
  ([`contracts/m3_2.md`](contracts/m3_2.md), `DRAFT — PENDING OWNER REVIEW AND ACCEPTANCE`),
  completing the Decision 029 §12 sequence. Gate F execution has not begun. Every later
  Milestone 3 phase is **not
  started and not authorized**, requiring all five Decision 024 §8 entry conditions per phase.

## Nonblocking maintenance notes

- The pytest-performance maintenance phase (parallel/offline test execution optimization, commit
  `f490281`) is accepted and does not gate S5. It changed test execution mechanics only, not any
  frozen definition, decision, or migration.

## Accepted nonblocking notes carried forward from S5.3

None of these blocks the accepted checkpoint, and none is to be addressed by changing implementation
outside a future authorized stage.

- **S5.4 requires an explicit ruling or a public pure-output design for the quota-contribution
  membership** used by reserve/replacement signatures. This was an S5.4 input, not an S5.3 gap.
  **Resolved and closed** by Decision 020 §§5–6 and the accepted S5.4 implementation: membership is
  published from the accepted S5.1 witness derivation as one additive immutable output.
- **`selection_result_sha256` remained NULL at S5.3.** Accepted; populating it was not an S5.3
  obligation. **Owner ruling recorded 2026-07-29: it remained NULL through S5.4** (Decision 020 §9).
  The open S6 question (Decision 020 §14.4) was **settled by Decision 021 §6 and is now
  implemented and accepted**: Stage S6 seals it under the existing `pilot-manifest/1.0` policy at a
  frozen fourteen-field preimage, append-once on every direct SQLite write path (migration `0013`
  triggers 1 and 2, widened by triggers 6, 7, and 8 at v0.5), and Decision 021 §15.5's guarantee that
  it also **remains recomputable from its persisted preimage** was proven against the migration as
  written. It is `NULL` in any catalog no S6 seal has run against, and **no production catalog
  exists**. **Closed.**
- **Quota-contribution and quota-member rows remain intentionally absent at S5.2.** **Closed at
  S5.4**: all three membership families are now written inside the S5 run's single `running` window,
  in the same transaction as the selection, exactly as Decision 020 requires.
- **The node-budget count observation is nonblocking.**
- **The difficult-or-nonstandard-package quota remains an M2.5 verification obligation** (Decision
  018 §14) — excluded from hard feasibility, never proxied, never reported as satisfied.

## Machine-readable markers

The markers below are consumed by `scripts/context_snapshot.sh`. Write each as `KEY: value` at the
start of a line. The script reads the first match and joins any **indented continuation lines** that
follow it, stopping at the first line that is not a continuation — so a marker never absorbs the
paragraph, fence, or marker after it. It does not otherwise parse Markdown structure.

**Per-stage `M3_2_*_STAGE_STATUS` and `DECISION_0NN_STATUS` markers state the position as at that
stage's or record's own acceptance.** Where such a marker says overall M3.2 T3 implementation
acceptance has not occurred, or that a later stage remains owner-gated, that is its historical
position and is not re-adjudicated here: **T3 acceptance has since occurred** (accepted Decision 046,
2026-08-07, `M3_2_T3_ACCEPTED_AND_PUBLISHED`), and `CURRENT_STAGE`,
`IMPLEMENTATION_AUTHORIZATION`, and `NEXT_AUTHORIZED_ACTION` carry the current position.

**The same rule governs `DECISION_053_STATUS`.** It states the position as at Decision 053's own
acceptance, when the interrupted M3.2A T5 ingestion job was still `running` and the closure had not
executed. That is its **historical** position and is deliberately left byte-unchanged. The closure has
since executed exactly once and is accepted (accepted Decision 054, 2026-08-08,
`M3_2_INTERRUPTED_RUN_CLOSURE_ACCEPTED`); **`M3_2_INTERRUPTED_RUN_CLOSURE_STATUS` and
`DECISION_054_STATUS` carry the current position — `HISTORICAL_JOB_STATE_NOW: stopped`.** Private
operational state is not self-recording, so a pre-execution marker never updates itself; the gap is
expected residue of the correct record-then-execute-then-accept sequence, not a contradiction.

**The same rule governs the trailing next-action pointer inside
`M3_2_INTERRUPTED_RUN_CLOSURE_STATUS`.** It names
`CLAUDE_M3_2_M3_L16_CARRY_IN_ARCHITECTURE_DISCOVERY_PACKET` as the next action, which was the position
at Decision 054's acceptance. **That discovery was subsequently issued and completed as read-only
validation, and accepted Decision 055 (2026-08-08,
`M3_2_CARRY_IN_ARCHITECTURE_ACCEPTED_AND_OFFLINE_IMPLEMENTATION_AUTHORIZED`) adjudicates it.** That
pointer is therefore **historical** and is deliberately left byte-unchanged;
`M3_2_CARRY_IN_ARCHITECTURE_STATUS`, `DECISION_055_STATUS`, `CURRENT_STAGE`, `ACTIVE_BLOCKER`,
`IMPLEMENTATION_AUTHORIZATION`, and `NEXT_AUTHORIZED_ACTION` carry the current position —
`CLAUDE_M3_2_DECISION_055_OFFLINE_IMPLEMENTATION_PACKET`.

**The same rule governs Decision 056 §10's next-action pointer and the
`M3_L14_M3_L15_M3_L16_STATUS` marker.** Decision 056 §10 names
`CLAUDE_M3_2_ORPHAN_ADOPTION_ARCHITECTURE_DISCOVERY_PACKET`, which was the position at its own
acceptance. **That read-only discovery was subsequently issued and completed, and accepted Decision
057 (2026-08-09, `M3_2_ORPHAN_ADOPTION_PROCEDURE_ARCHITECTURE_ACCEPTED`) adjudicates it** — confirming
one **MAJOR** correction to the discovery's write contract and fixing the exact later procedure. That
pointer is therefore **historical** and is deliberately left byte-unchanged in Decision 056 itself.
Likewise, `M3_L14_M3_L15_M3_L16_STATUS` states the position as at accepted Decision 055 and is
preserved byte-unchanged; **M3-L14 has since closed under Decision 056**, and **M3-L16 now carries the
Decision 057 procedure architecture while remaining `ACTIVE` and blocking**.
`Docs/m3/limitations_register.md`, `DECISION_056_CURRENT_STATE`, `DECISION_057_STATUS`,
`DECISION_057_CURRENT_STATE`, `M3_2_ORPHAN_ADOPTION_ARCHITECTURE_STATUS`, `CURRENT_STAGE`,
`ACTIVE_BLOCKER`, `IMPLEMENTATION_AUTHORIZATION`, and `NEXT_AUTHORIZED_ACTION` carry the current
position — `CLAUDE_M3_2_DECISION_057_FINAL_FRESH_INDEPENDENT_REVIEW_PACKET`. **Accepting a procedure
architecture is not performing the adoption**: Decision 057 is non-self-executing, authorizes no
invocation, and a separate owner execution packet is still required after its final fresh independent
review passes and the owner rules on publication. **The Decision 057 candidate has now been corrected
twice before publication** — the second bounded remediation on 2026-08-09 fixed two proof-layer
**MAJOR** defects the first fresh review found (a false claim that no second generated instant exists
anywhere in a correct run, and an impossible demand that deleting the `cursor.rowcount == 1` guard be
caught by a non-vacuous mutation) together with four related **MINOR** ambiguities. Both remediations
left the accepted central architecture unchanged, granted no execution authority, and changed no
executable, test, migration, configuration, contract, runbook, or template byte; **no third automatic
correction loop is permitted**.

**A marker is a compact pointer to current state; the narrative sections above carry the history and
the evidence.** `CURRENT_STAGE`, `ACTIVE_BLOCKER`, and `IMPLEMENTATION_AUTHORIZATION` are held short
deliberately (Decision 043 §8). Nothing was deleted to shorten them: the per-stage and per-decision
markers in this block, and the narrative above, retain every commit identity, hash, count,
disposition, and open obligation they previously restated.

`ACTIVE_STAGE_CONTRACT` is resolved by the script as a **file path**, whose own `STATUS:` marker is
then reported. It therefore always names a real contract file — it is not a place to record "none".
It currently names **`Milestones/contracts/m3_2.md`**, the accepted M3.2 contract. **Whether any
implementation is authorized is carried by `IMPLEMENTATION_AUTHORIZATION` here and by the named
contract's own status**, never by the fact that the marker names a path. No M3.2 contract T-series
implementation stage is currently authorized.

The `MILESTONE_0_STATUS`, `MILESTONE_1_STATUS`, `MILESTONE_2_STATUS`, `MILESTONE_3_STATUS`,
`DECISION_026_STATUS`, `DECISION_027_STATUS`, and `DECISION_028_STATUS` markers use the same
single-line `KEY: value` form. The
snapshot script reads only `CURRENT_STAGE`, `ACTIVE_BLOCKER`, `ACTIVE_STAGE_CONTRACT`, and
`NEXT_AUTHORIZED_ACTION`; the rest are for a reader or a future tool, and adding one changes no
script behaviour.

```
MILESTONE_0_STATUS: FORMALLY_CLOSED — Decision 026 section 6; annotated tag m0-complete; frozen research definitions and standing limitations remain binding
MILESTONE_1_STATUS: FORMALLY_CLOSED — Decision 026 section 7; annotated tag m1-complete
MILESTONE_2_STATUS: FORMALLY_CLOSED — Decision 026 sections 8 to 10; accepted implementation ends at M2.3 Stage S6; annotated tag m2-complete; no live SEC pilot was executed
MILESTONE_3_STATUS: MASTER PLANNING COMPLETE; DECISIONS 028 THROUGH 031 ACCEPTED; M3.1 CONTRACT ACCEPTED AND IMPLEMENTATION-AUTHORIZED; M3.1 IMPLEMENTATION FROZEN AT 970e050deb06910adcde8588101564beb7d19c74 AND OWNER-ACCEPTED (DECISION 031, 2026-08-03, OUTCOME M3_1_ACCEPTED_AND_COMPLETE); DECISION 029 CODE REMEDIATION COMPLETE; FIRST DURABLE SECTION 17 REVIEW COMPLETE AND PASSED; DECISION 029 SECTION 12 STEPS 8 TO 11 COMPLETE; M3.1A TOKEN EMITTED AND DURABLY CAPTURED; TWO BYTE-IDENTICAL M3.2A PLANS WITH REQUEST-PLAN SHA-256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68; OWNER-APPROVED HARD REQUEST CEILING 801 ON 2026-08-03; DECISION 030 ACCEPTED 2026-08-03 AND THE SOLE STEP-12 HYGIENE BLOCKER RESOLVED BY A PROVEN NON-SUBSTANTIVE REDACTION (REVIEW VERDICT UNCHANGED; HYGIENE PASSES); STEP 12 SIGNED AND COMPLETE ON 2026-08-03 WITH CHECKLIST RESULT PASS AND THE SIGNED CHECKLIST DURABLY RECORDED; STEP 13 OWNER-AUTHORIZED AND COMPLETE ON 2026-08-03 WITH THE GATE F READINESS TOKEN EMITTED AND RECORDED EXACTLY ONCE; GATE F READINESS RECORDED; GATE F EXECUTION NOT BEGUN AND LIVE SEC ACCESS NOT AUTHORIZED; STEP 14 COMPLETE AND PASSED ON 2026-08-03 (M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS; ARTIFACT SHA-256 caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e; REVIEW COMMIT 24fba32413bb6c5dade60a64182e42510afe6f88); OWNER ACCEPTED M3.1 ON 2026-08-03 AND STEP 15 RECORDED THE ACCEPTANCE (DECISION 031); STEP 16 COMPLETE ON 2026-08-03 — ANNOTATED M3.1-COMPLETE TAG CREATED AND PUSHED (TAG OBJECT 638a02b780d912ff7b37a2f523277b9d451a015a; PEELED TARGET 4cd2c7299ae30ca499108bd7f0a17a0adaf215f4); STEP 17 COMPLETE ON 2026-08-03 — M3-L11 AND M3-L12 CLOSED ON THEIR COMPLETE CLOSURE-EVIDENCE LISTS AND THE BOUNDED M3.2 CONTRACT DRAFTED (Milestones/contracts/m3_2.md); THE DECISION 029 SECTION 12 SEQUENCE IS COMPLETE; INDEPENDENT M3.2 CONTRACT REVIEW COMPLETE 2026-08-04 (M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS; ARTIFACT SHA-256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57; REVIEW COMMIT 3fbaa12d671d0000f5b608bbf6fb271f78b4673f); DECISION 032 ACCEPTED 2026-08-04 AND THE BOUNDED CONTRACT CORRECTIONS APPLIED (M3.2 CONTRACT NOW DRAFT — CORRECTED (DECISION 032) — PENDING INDEPENDENT REREVIEW AND OWNER ACCEPTANCE); FRESH INDEPENDENT NO-SUBAGENT REREVIEW COMPLETE 2026-08-04 (M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS; ARTIFACT SHA-256 91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf; REREVIEW COMMIT 3069b03ede9d805e9d0196a3e4c45c8cc68f42b7; ZERO BLOCKER; ZERO MAJOR); M3.2 CONTRACT ACCEPTED UNCHANGED AT T1 (ACCEPTED DECISION 034, 2026-08-04, OUTCOME M3_2_CONTRACT_ACCEPTED_AT_T1); STAGED T2 IMPLEMENTATION AUTHORIZATION GRANTED AND EXERCISED STAGE BY STAGE (ACCEPTED DECISION 035), WITH STAGES T2.1 (ACCEPTED DECISION 036), COMBINED T2.2-T2.3 (ACCEPTED DECISION 039), AND T2.4 (ACCEPTED DECISION 042, 2026-08-06, OUTCOME M3_2_T2_4_ACCEPTED_AND_PUBLISHED, AT CANDIDATE 625c03d6931e01acc99946ca3924f1cda4da6b76) EACH ACCEPTED, COMPLETE, AND PUBLISHED AND EACH GRANT EXHAUSTED; COMBINED T2.5-T2.6 AUTHORIZED BY ACCEPTED DECISION 045 (2026-08-07, OUTCOME M3_2_T2_5_T2_6_INTEGRATED_IMPLEMENTATION_AUTHORIZED), IMPLEMENTED AS ONE CANDIDATE, INDEPENDENTLY REREVIEWED PASS, AND ACCEPTED AND PUBLISHED BY ACCEPTED DECISION 046 (2026-08-07, OUTCOME M3_2_T3_ACCEPTED_AND_PUBLISHED, AT ACCEPTED CANDIDATE 810d567ba7610b22e2ce7cd56b67b7f0e76d26fb AND TREE aa7a7d4a6117160a2a4b2d1165d9b82c318cf968), WITH DECISION 045'S IMPLEMENTATION AUTHORITY EXHAUSTED; OVERALL M3.2 T3 IMPLEMENTATION ACCEPTANCE HAS OCCURRED (M3_2_T3_IMPLEMENTATION_ACCEPTED_AND_COMPLETE); T4 COMPLETE AND ACCEPTED; THE ONE DECISION-050 INITIAL T5 INVOCATION EXECUTED ONCE AND ENDED NON-SUCCESSFULLY AFTER ONE PHYSICAL SEC ATTEMPT; DECISION 051 ACCEPTS CONSUMED COUNT 1 OF 801 WITH TOTAL HEADROOM 800 AND BULK-ROUTE HEADROOM 5; RECOVERY UNDETERMINED; OLD RUN NEVER RESUMABLE; REMEDIATION ARCHITECTURE RECORDED BUT IMPLEMENTATION REQUIRES A SEPARATE PACKET; NO OPERATIONAL-STATE MUTATION, NETWORK, NEW LIVE INVOCATION, T6, M3.2B, OR GATE H AUTHORIZED
M3_1_FROZEN_IMPLEMENTATION_SHA: 970e050deb06910adcde8588101564beb7d19c74 — the reviewed implementation tree; implementation bytes are unchanged at the governance commit that recorded the review
M3_1_SECTION_17_REVIEW_STATUS: COMPLETE — VERDICT M3_1_SECTION_17_REVIEW: PASS; artifact Docs/m3/reviews/m3_1_section_17_review_970e050deb06910adcde8588101564beb7d19c74.md; produced by a session that wrote none of the M3.1 work; committed governance-only at 66e4c5433a393815c74f9e3087300613a516e2fb; review and artifact accepted by the project owner; this marker is authoritative over any earlier wording elsewhere that predates the review
M3_1A_REHEARSAL_STATUS: COMPLETE AND PASSED — Decision 029 section 12 step 9 executed exactly once on 2026-08-03 at 12:35:01Z under explicit owner authorization, exit status 0; all twelve A1-A12 scenarios PASS; passed, complete, a_reachable_agrees, and a_reachable_fully_tested all true; derived and tested route-key sets equal across nine routes; unmeasured_routes empty; actual_logical_request_count 0 and actual_physical_attempt_count 0; no live SEC access; receipt completion_status complete with no reason_code; M3_1A_OFFLINE_OPERATOR_REHEARSAL_PASSED emitted by the canonical command and durably captured; artifacts immutable under the external evidence root at runs/m3_1a_rehearsal_970e050deb06910adcde8588101564beb7d19c74/ with report sha256 6308576a0a7df33813239f753b31b86754f3908d63d73e6521682db06a59e1e0, receipt sha256 ea1f4be2c136827ac5d865eea0fabf73f0f716802e2ee8cd23aedf1965dbc81b, and stdout log sha256 4b42f95e4a00d5865eeb05ccc9f06fe08c51c68f07c56d5512d441c2ee7118ce; not rerunnable
M3_1A_EVIDENCE_BACKUP_STATUS: SAME-DEVICE SNAPSHOTS COMPLETE THROUGH STEP 13 — the external evidence root is snapshotted locally after step 9, after step 10, after step 11, after step-12 preparation, after the step-12 signature, and after the step-13 token recording; the after-step-11 snapshot (11 files), the after-step-12-prep snapshot (12 files, including the private request-budget document), the after-step-12-signed snapshot (13 files, including the owner-signed Gate F checklist), and the after-step-13-token snapshot (14 files, including the readiness-token record) each verified file-by-file by SHA-256 on 2026-08-03, include all step-9 artifacts, and exclude the ignored local configuration file; these snapshots are same-device protection against accidental deletion only, not an off-device or device-loss backup, and a separate owner-controlled off-device backup remains an owner matter; no absolute private path is recorded here
M3_1B_PLAN_STATUS: COMPLETE AND ACCEPTED — STEP_10_PASS_BYTE_IDENTICAL; m3 plan-requests ran exactly twice on 2026-08-03 to different immutable output names under owner-supplied explicit inputs (coverage 2009-01-01 to 2026-06-30, as-of 2026-06-30, calendar year 2026, explicitly empty operator calendar-evidence manifest, operational catalog nonexistent at planning); byte-identical plans with request_plan_sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68 under m3-request-plan/1.0 and quarterly-index-instances/2.0; q 70 (2009QTR1 to 2026QTR2 including closed 2026 Q2 per Decision 013 section 1); already-satisfied instances 0; planned unique logical requests 75; maximum physical attempts 801; maximum new raw objects 75; expected cache hits 0; rate-limiter spacing floor 200.0 seconds; both dry-run receipts validate with zero actual request counts; the runs are not rerunnable
M3_1B_CEILING_APPROVAL_STATUS: STEP 11 COMPLETE — STEP_11_BUDGET_DISPLAY_PASS; the canonical m3 show-budget stdout is durably captured with sha256 0e6722dcd960c54a49e4a1af44a5c15587d03109b262c7ee471a46b8071db508; OWNER_CEILING_APPROVAL APPROVED received 2026-08-03 for the exact plan-bound hard request ceiling 801 bound to request-plan sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68, with planned unique logical requests 75, maximum new raw objects 75, expected cache hits 0, and no contingency allowance; three response-outcome quantities remain deliberately unresolved as EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN (expected successful, expected not-modified, expected governed non-success) with no integer approved or invented; the approval does not complete or sign the Gate F checklist, does not emit the readiness token, and does not authorize live SEC access
M3_1B_BUDGET_DOCUMENT_STATUS: CREATED 2026-08-03 — the private M3.2A request-budget document was instantiated once, immutably, from Docs/m3/templates/request_budget.md into the external evidence root's M3.1B run directory (runs/m3_1b_plan_970e050deb06910adcde8588101564beb7d19c74/request_budget.md); 21633 bytes, 307 lines, sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f; it records the plan-derived quantities, the per-route independently tested A_reachable witnesses, the verbatim owner ceiling approval of 2026-08-03, and the three deliberately unresolved response-outcome markers; the public evidence-index entry is deliberately deferred to the owner; the absolute private path is never recorded here
STEP_12_PREPARATION_STATUS: COMPLETE AND DISCHARGED — the proposed checklist was prepared with every supported non-owner field populated; the sole adjudicable finding was resolved by accepted Decision 030 (proven non-substantive one-path redaction; review verdict M3_1_SECTION_17_REVIEW: PASS unchanged; make hygiene passing); the owner-side signing-preflight acts were completed on 2026-08-03 (SEC identity validated at the boundary with the value never displayed; main synchronized by one ancestry-proven normal push; operator acknowledgement recorded) and the owner signed the checklist; see STEP_12_SIGNATURE_STATUS
STEP_12_SIGNATURE_STATUS: SIGNED AND COMPLETE 2026-08-03 — owner Joseph Nihill, project owner acting through the ChatGPT owner decision; Gate F checklist result PASS with every template field populated, every item PASS, and no unresolved blocker; recorded acceptance reference bound to repository baseline 55cf244a00428fbc8fa38d7b70af1bac8a7c45e9, request-plan sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68, request-budget sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f, and sanitized section 17 review sha256 9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3 (a transparent recorded owner acceptance reference, not a handwritten, cryptographic, or third-party digital signature); the signed checklist is immutable private evidence in the M3.1B run directory of the external evidence root, 23463 bytes, 284 lines, sha256 34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc, containing the operator acknowledgement, the Decision 030 dispositions, and the two explicit step-13 boundary lines; the readiness-token literal occurs nowhere in it, which was correct at signing time; step 13 was subsequently owner-authorized and completed on 2026-08-03 (see M3_1_GATE_F_READINESS_TOKEN_STATUS); Gate F execution is not begun and not authorized
M3_1_GATE_F_READINESS_TOKEN_STATUS: EMITTED AND RECORDED EXACTLY ONCE ON 2026-08-03 UNDER EXPLICIT OWNER STEP-13 AUTHORIZATION — no canonical command exists for this token (the literal appears nowhere in the implementation), so the recording is the repository's established governance-evidence mechanism: a create-once immutable private record in the evidence root's M3.1B run directory (3982 bytes, 62 lines, sha256 b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e) carrying the token literal exactly once in its emitted-token field, bound to the signed checklist sha256 34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc, request-plan sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68, request-budget sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f, hard request ceiling 801, checklist baseline 55cf244a00428fbc8fa38d7b70af1bac8a7c45e9, and public step-12 recording commit 0334294bd420a829033094080a13e4df900da078, plus this public ledger marker; the token records readiness only and authorizes no live SEC access, no Gate F execution, no M3.1 final acceptance, and no M3.2; every step-13 precondition was independently reverified read-only immediately before recording; not re-emittable
M3_1_INDEPENDENT_ACCEPTANCE_REVIEW_STATUS: COMPLETE AND PASSED — Decision 029 section 12 step 14 executed 2026-08-03 under explicit owner authorization by a fresh non-author session; verdict M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS; artifact Docs/m3/reviews/m3_1_independent_acceptance_review_04ce708fd46dbcf1c2fc355f16325ecea9e1f47a.md with sha256 caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e, committed governance-only at 24fba32413bb6c5dade60a64182e42510afe6f88; all validation gates green in a fresh external independent clone (2739 passed, 1 pre-existing skip; transport test ran; secrets and hygiene clean); every accepted private-evidence SHA-256 recomputed and matched; zero BLOCKER, zero MAJOR, three MINOR findings accepted by the owner as nonblocking (Decision 031), zero OPTIMIZATION; the review recorded a verdict only and did not itself accept M3.1
M3_1_ACCEPTANCE_STATUS: OWNER-ACCEPTED 2026-08-03 — recorded by accepted Decision 031 (outcome M3_1_ACCEPTED_AND_COMPLETE) at Decision 029 section 12 step 15; verbatim owner instrument OWNER_M3_1_ACCEPTANCE_DECISION: APPROVED bound to review commit 24fba32413bb6c5dade60a64182e42510afe6f88 and review-artifact sha256 caf9f26e6a2690a05a9d6a238d5572533b858789638b35a24da06c64a4c5ae4e; accepts the frozen implementation 970e050deb06910adcde8588101564beb7d19c74 (tree d0c3c94cbf9128eaf0fdb1ef58179d9977d718d3), the signed Gate F checklist sha256 34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc, the readiness-token record sha256 b06ae373a184ee73c84b78a52b4761432403600a47038e972ecf1b894b0c9c8e, the request plans sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68, the request budget sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f, and the exact hard request ceiling 801; the annotated m3.1-complete checkpoint was subsequently created and pushed at the acceptance commit under the owner's step-16 authorization (2026-08-03; tag object 638a02b780d912ff7b37a2f523277b9d451a015a); Gate F execution not begun; live SEC access not authorized; M3.2 not authorized and not begun
DECISION_031_STATUS: ACCEPTED — OWNER APPROVED 2026-08-03; outcome M3_1_ACCEPTED_AND_COMPLETE; records the owner's final M3.1 acceptance and its evidence bindings; accepts the step-14 review's three MINOR findings as nonblocking; sets M3-L11 and M3-L12 to CLOSURE-READY PENDING STEP 16 without closing either; creates no tag and grants no network, Gate F-execution, acquisition, or M3.2 authority
M3_2_CONTRACT_REVIEW_STATUS: COMPLETE 2026-08-04 — independent, adversarial review of the initial M3.2 contract draft at 536856325f6a655416d48276c5b93848cab388e8 by a fresh non-author session under the owner's 2026-08-03 authorization; verdict M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS; zero BLOCKER, two MAJOR (F1 completion semantics; F2 boundary exactness including the unnamed command-scoped network-enable change), four MINOR (F3 crash-segment accounting; F4 evidence-index vocabulary; F5 stale navigation prose; F6 sentinel naming), one OPTIMIZATION (F7 positive controls); all sixty-five adversarial questions answered and the four owner concerns determined (completion concern confirmed as F1; migration/catalog concern passed with no new migration needed; network-enable concern confirmed as part of F2; the unresolved-count sentinel correct as used); durable artifact Docs/m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md, sha256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57, committed governance-only at 3fbaa12d671d0000f5b608bbf6fb271f78b4673f; the artifact is preserved unchanged as a truthful correction review, and per the owner's Decision 032 procedural ruling it does not satisfy the acceptance-prerequisite review because its session used two read-only fact-gathering subagents; zero live SEC access; the review accepted nothing and authorized nothing
DECISION_040_STATUS: ACCEPTED — OWNER APPROVED 2026-08-06; outcome M3_2_T2_4_IMPLEMENTATION_AUTHORIZED; records verbatim the owner instrument OWNER_DECISION_040_M3_2_T2_4_IMPLEMENTATION_AUTHORIZATION: APPROVED — accepts the read-only T2.4 discovery outcome M3_2_T2_4_IMPLEMENTATION_PACKET_DISCOVERY_COMPLETE; authorizes stage T2.4 (recovery, reconciliation, resume boundaries, and drift control) as one coherent stage with four internal subphases (T2.4-A catalog-authoritative reconstruction; T2.4-B deterministic read-only reconciliation and drift inspection; T2.4-C continuation proposal and conditional reuse; T2.4-D the explicit recovery-action library boundary with no CLI exposure); approves exactly one new registered reason code SOURCE_REQUIRED_OBJECT_UNAVAILABLE (integrity; blocks_release true; requires_manual_review true; decision reference Docs/Decisions/decision_040_m3_2_t2_4_implementation_authorization.md); fixes NO_NEW_MIGRATION_REQUIRED (chain exactly 0001-0013) and NO_RECEIPT_SCHEMA_CHANGE_REQUIRED (m3-execution-receipt/2.0 frozen); rules F4 non-blocking for T2.4 (due no later than T4); fixes the exact eight-path maximum envelope, expressly adding tests/unit/test_reasons.py to the Decision 035 envelope for T2.4 only (narrow, stage-scoped higher-authority amendment; historical T2 packet byte-identical; Decision 038 has no authority over T2.4); fixes the one-commit rule with exact subject Implement M3.2 T2.4 recovery and reconciliation and the review ladder (implementation completion; ChatGPT owner review; one fresh independent no-subagent stage audit; correction and rereview where required; separate owner acceptance and publication authorization); and authorizes NO implementation before the separate exact T2.4 implementation packet is issued
M3_2_T2_4_STAGE_STATUS: ACCEPTED AND COMPLETE — PUBLISHED (stage authorized by accepted Decision 040, 2026-08-06, outcome M3_2_T2_4_IMPLEMENTATION_AUTHORIZED; correction authority recorded by accepted Decision 041, 2026-08-06, outcome M3_2_T2_4_RECOVERY_STATE_PRIMITIVE_AUTHORITY_RECORDED; accepted and published by accepted Decision 042, 2026-08-06, outcome M3_2_T2_4_ACCEPTED_AND_PUBLISHED, stage classification M3_2_T2_4_ACCEPTED_AND_COMPLETE); accepted candidate 625c03d6931e01acc99946ca3924f1cda4da6b76, accepted tree 816fd392df859106b9ba21b684f9b4a8061461fc, parent and Decision 041 governance baseline 4897bb1d8fc5be5cd6d12be941204e377bbfa5a4, subject Implement M3.2 T2.4 recovery and reconciliation, exactly eight changed paths (m3/acquisition.py, m3/__init__.py, reasons.py, sec/observation_catalog.py, tests/unit/test_m3_acquisition.py, tests/unit/test_m3_recover.py, tests/unit/test_observation_catalog.py, tests/unit/test_reasons.py) inside the Decision 041 ten-path maximum with NO ELEVENTH PATH and with m3/recovery.py and tests/unit/test_m3_recovery.py deliberately unedited as that maximum permits, NO TAG. The fresh independent corrected-candidate rereview returned M3_2_T2_4_CORRECTED_CANDIDATE_REREVIEW_PASS on Claude Opus 5 at Max effort in a fresh independent session with zero BLOCKER, zero MAJOR, and zero MINOR, the mandatory separate-OS-process durability challenge PASS, an independent mutation campaign 18/18 killed, targeted validation 333 passed, full suite 3053 passed / 1 pre-existing intentional skip - that skip being the pre-existing fixed-literal skip in tests/unit/test_m23_pilot_manifest.py, with the HTTPX transport tests executed and not skipped, so Decision 042's [sec]-extra wording understated the validation actually performed and stands as historical wording (Decision 043 section 12) - and clean static gates; that rereview reached the repository through the owner's supplied acceptance evidence and NO REREVIEW ARTIFACT FILE WAS PREVIOUSLY RECORDED HERE, so Decision 042 creates, reconstructs, or back-dates none and asserts no artifact path and no artifact SHA-256. The owner accepts the corrected candidate, the independent rereview, Decision 041's recovery-state primitive implementation as satisfying the authorized corrective design, and T2.4 as complete and accepted; the nine Decision 041 §13 continuing correction obligations are discharged and mutation 02 remains accepted as a proven no-op. The superseded first candidate 5cba2863f47df09c83564258be897a4fd71cf6be (tree e3c47528e6059c7b8e10369846934c56e3b8eabe) was never accepted, pushed, or tagged, is historical only, and is on no branch and no tag; no published history was changed. Published by one normal fast-forward push of main carrying, in order, the accepted candidate and the Decision 042 governance commit, with no tag, no release, no force push, and no history rewrite. T2.4 ACCEPTANCE DOES NOT ITSELF GRANT T2.5, T2.6, NETWORK, OPERATIONAL-CATALOG, LIVE-SEC, OR 801-CEILING EXECUTION AUTHORITY; combined T2.5-T2.6 remains owner-gated and has not begun; overall M3.2 T3 implementation acceptance has not occurred
DECISION_041_STATUS: ACCEPTED — OWNER APPROVED 2026-08-06; outcome M3_2_T2_4_RECOVERY_STATE_PRIMITIVE_AUTHORITY_RECORDED; records verbatim the owner instrument OWNER_DECISION_041_M3_2_T2_4_RECOVERY_STATE_PRIMITIVE_AUTHORITY: APPROVED — accepts the read-only durable-lifecycle feasibility outcome M3_2_T2_4_DURABLE_RECOVERY_LIFECYCLE_NOT_FEASIBLE_WITHIN_CURRENT_AUTHORITY on seven grounds (no accepted callable resolves an exact generic census_recovery_states row; the sole existing resolver is embedded in rebuild_audit_projection; it is hard-filtered to audit_projection_interrupted; it resolves every blocked projection state for a run rather than one exact primary-key identity; it performs a projection rebuild and other unrelated mutations; it resolves during the mutation, before recovery-event recording; three of the four T2.4 recovery actions have no resolver at all), determining that the schema is sufficient and the missing capability is an accepted exact primitive, and accepting the feasibility session's use of Claude Opus 5 rather than Claude Fable 5 and the independent-audit report's absence from that session as non-material and nonblocking; amends the Decision 040 §11 eight-path T2.4 envelope to exactly ten tracked paths for the T2.4 correction only, adding src/disclosure_drift/sec/observation_catalog.py and tests/unit/test_observation_catalog.py, and amends Decision 040 §12 only to release observation_catalog.py for the narrow additions authorized here, with no other previously prohibited path released, the ten paths a maximum rather than a requirement to edit every path, and an eleventh path an immediate stop; authorizes exactly two additive public recovery-state primitives in observation_catalog.py — open_recovery_state (verifies census_run_id identifies an existing ops_ingestion_jobs.job_id; inserts exactly one census_recovery_states row with resolution_state blocked addressed by the full primary key; raises on missing run, duplicate identity, constraint failure, or failed write; writes nothing to census_recovery_events or census_projection_recovery_events; no silent skip when a run ID is absent) and resolve_recovery_state (updates only the exact primary-key row; requires it currently blocked; performs no scenario filtering, projection rebuild, or repair; updates no sibling state; writes no event row; returns success only when exactly one blocked row was resolved; treats zero affected rows as failure; must not bulk-resolve by run or scenario) — with every existing public and private function retaining its accepted semantics and no existing resolver, reconciliation function, recorder, schema, or projection behavior rewritten to simulate the new authority; fixes the generic state scenario t2_4_recovery_action stored only in census_recovery_states and never inserted into the CHECK-constrained census_recovery_events; fixes the run-identity ruling requiring a caller-supplied already-registered ops_ingestion_jobs.job_id with five pre-mutation refusal conditions and six express prohibitions on minting, fabricating, or substituting a run identity; fixes the corrected thirteen-step write-ahead sequence in which the block is committed and fresh-connection verified before mutation, the actual event is recorded with census_run_id=None so no second recovery-state row is created, exact resolution happens only after event recording succeeds, and opening the block is expressly not itself a recovery event; fixes eight failure outcomes, rules a committed resolution whose readback cannot complete UNDETERMINED for that invocation, and fixes that no in-memory flag may be the only continuation prohibition; fixes fifteen required primitive tests with tests/unit/test_observation_catalog.py editable only to prove the new pair; leaves NO_NEW_MIGRATION_REQUIRED (chain exactly 0001-0013), NO_RECEIPT_SCHEMA_CHANGE_REQUIRED (m3-execution-receipt/2.0 frozen), exactly one T2.4 reason-code addition, no alias, no route or source-authority change, and no configuration change unchanged; rules that the candidate remains local, unaccepted, unpushed, and untagged and may not be pushed, that this record is recorded and published from a disposable governance clone without changing the primary checkout, and that a separate later correction packet may authorize one controlled soft reset onto the published Decision 041 baseline and exactly one corrected implementation commit, with the old unaccepted SHA not preserved by a branch or tag and no authority to change published history; and requires nine sustained independent-audit findings still to be resolved by the correction, with mutation 02 accepted as a proven no-op
DECISION_042_STATUS: ACCEPTED — OWNER APPROVED 2026-08-06; outcome M3_2_T2_4_ACCEPTED_AND_PUBLISHED; records the owner's acceptance-and-publication ruling for Milestone 3.2 implementation stage T2.4 (Recovery, Reconciliation, Resume Boundaries, and Drift Control), reproducing the operative owner acceptance text without alteration — there is no separately supplied signed instrument block for Decision 042 and none is invented; accepts the fresh independent corrected-candidate rereview verdict M3_2_T2_4_CORRECTED_CANDIDATE_REREVIEW_PASS (Claude Opus 5; Max effort; fresh independent session; zero BLOCKER; zero MAJOR; zero MINOR; mandatory separate-OS-process durability challenge PASS; independent mutation campaign 18/18 killed; targeted validation 333 passed; full suite 3053 passed / 1 pre-existing intentional skip; static gates clean), noting expressly that the rereview reached the repository through the owner's supplied acceptance evidence, that no rereview artifact file was previously recorded here, and that none is created, reconstructed, or back-dated and no artifact path or SHA-256 is asserted; accepts the corrected T2.4 candidate 625c03d6931e01acc99946ca3924f1cda4da6b76 (tree 816fd392df859106b9ba21b684f9b4a8061461fc; parent and Decision 041 governance baseline 4897bb1d8fc5be5cd6d12be941204e377bbfa5a4; subject Implement M3.2 T2.4 recovery and reconciliation) with its exactly eight changed paths inside the Decision 041 ten-path maximum and no eleventh path, changing no migration, receipt-schema, configuration, contract, packet, decision, script, template, CI, or documentation byte; accepts Decision 041's recovery-state primitive implementation as satisfying the authorized corrective design; accepts T2.4 as complete and accepted with classification M3_2_T2_4_ACCEPTED_AND_COMPLETE; authorizes one normal fast-forward push publishing in order the accepted candidate and the Decision 042 governance commit with exact subject Accept and publish M3.2 T2.4, the candidate not rewritten, amended, squashed, rebased, reset, or cherry-picked and the governance change created on top of it, permitted only after durable recording, registry and ledger agreement, unchanged candidate bytes, unchanged contract and packet hashes, a staged path set of exactly the three authorized governance paths, and passing governance validation; NO TAG, no release, no force push, no --force-with-lease, no history rewrite, rebase, squash, or amend; keeps stage acceptance, publication, and overall M3.2 T3 implementation acceptance distinct and records that T3 ACCEPTANCE HAS NOT OCCURRED; carries forward unchanged the six Decision 040 §19 obligations (accepted RawStore resource limitation as a T4 concern; sanitization or exclusion of untrusted progress-sink messages; F4 no later than T4; D023-O1 as a latent fail-closed referral condition; operator wiring and receipt assembly during T2.5-T2.6; overall independent T3 acceptance after the combined T2.5-T2.6 freeze candidate); governance only - no executable byte changes with this record; edits no accepted decision (032-041 byte-unchanged), no contract, no packet, no review artifact, no migration, no template, no configuration, no reason code, no receipt schema, and no Docs/decision_index.md; and grants NO T2.5 or T2.6 implementation, does not begin T2.5, enables neither network.enabled nor network.m3_acquire_enabled nor CompanyFacts, and grants no SEC contact, connectivity testing, live SEC request, live acquisition, real operational catalog, operational m3 acquire execution, receipt emission, private reconciliation-report creation, evidence indexing, use of the 801 ceiling, M3.2B activity, any T3/T4/T5 authority not already separately granted, Gate H or M3.3 work, migration, receipt-schema change, further reason code, eleventh path, or tag
DECISION_043_STATUS: ACCEPTED — OWNER APPROVED 2026-08-06; outcome M3_2_G1_NAVIGATION_AND_WORKFLOW_REPAIR_AUTHORIZED; records the owner instrument OWNER_DECISION_043_M3_2_G1_NAVIGATION_AND_WORKFLOW_REPAIR_AUTHORIZATION: APPROVED, accepting the read-only post-T2.4 workflow-efficiency discovery recommendation RECOMMEND_MINIMAL_OPTIMIZATION_BEFORE_T2_5 and authorizing one bounded non-production stage, M3.2 G1 (Navigation and Workflow Repair), outside the contract T-series; fixes the hard semantic boundary (no SEC acquisition, planning, route/source, recovery, reconciliation, attempt-accounting, ceiling, receipt, reason-code, schema, migration, network-configuration, methodology, or contract-meaning change, and no production source or test behaviour change), the seven-path implementation ceiling with no eighth path, the R1 navigation repair, the R2 marker and context repair, the R3 make stage-gate, the R4 review-execution conventions, and the R5 prospective durable-review-artifact lifecycle; supersedes the Decision 033 section 5 navigation-preservation instruction partially and prospectively, solely so far as necessary for this repair, leaving historical decisions immutable and navigation aids non-authoritative; records three historical observations without editing Decision 042; rejects or defers a repo-owned audit harness, a second context command, a mutation framework, a frozen-input manifest, a STATUS.md structural rewrite, an m3/acquisition.py split, and any production refactor; governance only, changing no executable byte, creating no tag, and granting no T2.5, T2.6, network, CompanyFacts, live-SEC, operational-catalog, ceiling-801, migration, receipt, reason-code, production-behaviour, T3/T4/T5, Gate H, or M3.3+ authority
DECISION_044_STATUS: ACCEPTED — OWNER APPROVED 2026-08-06; outcome M3_2_G1_ACCEPTED_AND_PUBLISHED; records the owner instrument OWNER_DECISION_044_M3_2_G1_ACCEPTANCE_AND_PUBLICATION: APPROVED — accepts the G1 implementation candidate 7ac33d0abd9e05bf895b38270bde476317c974be (tree a848320f1edd159f07b112f45790a229ec48827e; parent c1fbece9242356b840787dd00ad46f15bb880133) and its exactly-seven-path change set with no eighth path; accepts the fresh independent review verdict M3_2_G1_INDEPENDENT_REVIEW_PASS and binds its durable artifact Docs/m3/reviews/m3_2_g1_navigation_workflow_repair_independent_review.md, sha256 ec12e038759d61b238c3a6fb7b46627ec070651fba9084d728fb09dfd1ad958f, at review commit 983fceb27122e4c4275f9554ad001c2d0a9d8524 (tree 2ac6a0a04973494cd561c0440652959a2c499592); accepts the Decision 043 R1-R5 implementation and G1 as COMPLETE and ACCEPTED, classification M3_2_G1_ACCEPTED_AND_COMPLETE; binds the reproduced context-optimization evidence 14,579 to 2,654 bytes (81.8 percent) and records the earlier 14,724 and 2,795 observations as superseded for acceptance evidence and not implementation defects; preserves Decision 043 section 12's historical skip ruling without editing Decision 042; exhausts G1's seven-path implementation authority while keeping the prospective durable-review-artifact convention in effect; reopens none of the deferred items (STATUS structural rewrite, acquisition.py split, repo-owned audit harness, second context command, mutation framework, frozen-input manifest); authorizes exactly three governance paths, one governance commit with subject Accept and publish M3.2 G1, and one normal fast-forward push publishing the three-commit chain with no tag, no force push, and no history rewrite; governance only, changing no executable byte, editing no Decision 001-043, and granting no T2.5, T2.6, network, CompanyFacts, live-SEC, operational-catalog, ceiling-801, migration, receipt, reason-code, production-behaviour, T3/T4/T5, Gate H, or M3.3+ authority
M3_2_G1_STAGE_STATUS: ACCEPTED AND COMPLETE — PUBLISHED (stage authorized by accepted Decision 043, 2026-08-06, outcome M3_2_G1_NAVIGATION_AND_WORKFLOW_REPAIR_AUTHORIZED; accepted and published by accepted Decision 044, 2026-08-06, outcome M3_2_G1_ACCEPTED_AND_PUBLISHED, stage classification M3_2_G1_ACCEPTED_AND_COMPLETE); accepted candidate 7ac33d0abd9e05bf895b38270bde476317c974be, accepted tree a848320f1edd159f07b112f45790a229ec48827e, parent and published Decision 043 baseline c1fbece9242356b840787dd00ad46f15bb880133, subject Repair M3.2 navigation and review workflow, exactly seven changed paths inside the seven-path Decision 043 section 6 ceiling with NO EIGHTH PATH (Docs/decision_index.md, Docs/change_impact_map.md, Docs/architecture_map.md, Milestones/STATUS.md, scripts/context_snapshot.sh, Makefile, and the new Docs/m3/review_execution_conventions.md), NO TAG. NO production source, test, configuration, migration, schema, receipt, reason-code, route, source-authority, contract, packet, or accepted-decision byte changed - the chain remains 0001-0013, the receipt remains m3-execution-receipt/2.0, and both tracked network switches remain false. The fresh independent review returned M3_2_G1_INDEPENDENT_REVIEW_PASS with zero BLOCKER, zero MAJOR, one MINOR, and two OPTIMIZATION, by a genuinely fresh session that was not the implementation session and remained read-only until the substantive verdict was determined; this is the first exercise of the Decision 043 section 11 durable-review lifecycle - artifact Docs/m3/reviews/m3_2_g1_navigation_workflow_repair_independent_review.md, sha256 ec12e038759d61b238c3a6fb7b46627ec070651fba9084d728fb09dfd1ad958f, created only after the verdict and committed alone at 983fceb27122e4c4275f9554ad001c2d0a9d8524 (tree 2ac6a0a04973494cd561c0440652959a2c499592, parent 7ac33d0abd9e05bf895b38270bde476317c974be, subject Record independent review of M3.2 G1 navigation repair) - with NO historical T2.2-T2.3 or T2.4 review artifact reconstructed, fabricated, or back-dated, and the prospective durable-review convention remaining in effect for later acceptance-relevant reviews. Accepted context-optimization evidence: 14,579 to 2,654 bytes, 11,925 removed, 81.8 percent; the earlier 14,724 and 2,795 observations are SUPERSEDED for acceptance evidence and are NOT implementation defects (both are measurement-state artifacts; the review's MINOR-1 is discharged by this binding with no repository change, and the two OPTIMIZATION observations are recorded as observations only and are not authorized for action). Decision 043 section 12's historical skip ruling is preserved unchanged - the accepted T2.4 single skip was the fixed-literal tests/unit/test_m23_pilot_manifest.py skip, the HTTPX transport tests executed, Decision 042's wording is not edited, and the older Milestone-2-era [sec] sentence remains historical and correctly outside G1's adjudication scope. G1'S SEVEN-PATH IMPLEMENTATION AUTHORITY IS EXHAUSTED: neither Decision 043 nor Decision 044 authorizes further G1 implementation, a further edit to those seven paths under G1 authority, or a second G1 commit. Published by one normal fast-forward push of main carrying, in order, the accepted candidate, the review commit, and the Decision 044 acceptance commit, with no tag, no release, no force push, and no history rewrite. G1 ACCEPTANCE DOES NOT ITSELF GRANT T2.5, T2.6, NETWORK, OPERATIONAL-CATALOG, LIVE-SEC, OR 801-CEILING AUTHORITY; combined T2.5-T2.6 remains owner-gated, unauthorized, and not begun; overall M3.2 T3 implementation acceptance has not occurred
DECISION_045_STATUS: ACCEPTED — OWNER APPROVED 2026-08-07; outcome M3_2_T2_5_T2_6_INTEGRATED_IMPLEMENTATION_AUTHORIZED; records the owner instrument OWNER_DECISION_045_M3_2_T2_5_T2_6_INTEGRATED_IMPLEMENTATION_AUTHORIZATION: APPROVED, authorizing combined Milestone 3.2 stage T2.5-T2.6 (Operator Surfaces and Integrated Implementation Candidate) as ONE stage under Decision 037 and contract section 22, producing ONE implementation-freeze candidate with exact subject Complete M3.2 T2.5-T2.6 integrated implementation, local and unpushed pending T3 review, NO TAG, with two internal subphases that are implementation checkpoints only and no Subphase-A commit; fixes the exact operator interfaces for m3 acquire --show-scope, m3 acquire --live, m3 derive-dependent-plan, m3 reconcile-requests (--receipt REMOVED, --data-root REQUIRED), the private reconciliation report (--report-out; private, not publicly indexed, so F4 remains a T4 obligation), m3 show-drift, and m3 recover, superseding conflicting or incomplete argument lists in the historical T2 packet while preserving its substantive requirements and leaving that packet byte-identical at sha256 621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599; carries two owner rulings adopted BEFORE first recording in response to two verification findings raised against the accepted code and schema, so no defective version was ever recorded, committed, published, or accepted - BLOCKER_1_RESOLUTION: A1_APPROVED gives M3.2 a durable acquisition-run identity registered by P3 as exactly one existing-table ops_ingestion_jobs row per lawful live invocation with job_kind='m3_2_acquisition' and stage M3.2A or M3.2B, ordered and verified BEFORE transport construction (on failure no transport, no physical request, and no attributed object), one run per invocation with a NEW identity on resume, and durable run-to-observation attribution through existing accepted relations only, proven compatible before use, with NO migration, NO new table or column, NO prohibited-path edit, and a STOP if no lawful relation exists, retaining m3 show-drift --run and m3 recover --run scoped to an existing M3.2 acquisition run, failing closed at exit 4 on unknown, non-M3.2, unattributable, or ambiguous identity, with NO global-drift fallback and NO fabricated run identity; and BLOCKER_2_RESOLUTION: EXHAUSTIVE_RESPONSE_EVENT_ACCOUNTING_WITH_STATUS_ZERO_SENTINEL retaining the invariant sum(response_classification_totals) == sum(status_code_totals) over an exhaustively defined response-event universe in which a followed 3xx contributes its actual status plus one proceed, a lawful 304 contributes status 304 plus proceed plus not_modified_count and never duplicate_object_count, a classified no-response transport failure contributes the receipt-local sentinel status_code_totals["0"] meaning no HTTP status - transport-level failure (NOT an HTTP status code, and never used for a real response) plus exactly one already-frozen bucket, pre-transport refusals contribute to neither total, and cooldown_count == response_classification_totals["cooldown"], all produced inside the authorized M3 layer with NO receipt-schema, field, mode, vocabulary, or validator change and with sec/http_client.py and m3/receipt.py byte-identical, insufficient accepted surfaces being a STOP rather than an inference; reaffirms the fifteen-path ceiling with NO SIXTEENTH PATH (required P3, P4, P5, P8, T1, T2, T4, T5; conditional P6, P7, T3, T6, T7; configs/project.yaml and config.py expected byte-identical and never a route to live authority), the prohibited-path list expressly NOT inheriting the Decision 038 and 041 extensions, the frozen receipt authority m3-execution-receipt/2.0 with only m3 acquire --live and m3 derive-dependent-plan emitting receipts and NO receipt on a pre-execution refusal, the Decision 040 section 6 count-vocabulary bindings, the now-DUE progress-sink sanitization obligation with its mandatory absolute-path and email positive control, resume semantics, the required validation, high-risk test, and effective-mutation campaigns, and the freeze-candidate acceptance conditions; rules the stale accepted-contract header historical metadata and NOT a stop condition with Decisions 039, 042, 044, and 045 controlling and the contract NOT edited at unchanged sha256 c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7; rules that the implementation session does NOT edit Milestones/STATUS.md, the freeze SHA being reported in the completion handoff and bound later by the T3 acceptance Decision; fixes the governance sequence Decision 045, implementation, one local candidate, fresh independent T3 review, durable artifact on PASS, Decision 046 acceptance, one fast-forward publication, with no intermediate T2.5 acceptance and an in-envelope correction authorized by an owner correction packet without a new Decision; governance only - no executable byte changes with this record; edits no accepted decision (001-044 byte-unchanged), no contract, no packet, no review artifact, no migration, no template, no configuration, no reason code, no receipt schema, and no Docs/decision_index.md; and grants NO network or CompanyFacts enablement, NO SEC identity use, DNS lookup, connectivity test, or request, NO real operational catalog, run row, raw object, live receipt, or evidence artifact, NO ceiling-801 use, NO M3.2A or M3.2B execution, and NO T3, T4, T5, T6, Gate H, or M3.3+ authority
M3_2_T2_5_T2_6_STAGE_STATUS: ACCEPTED AND COMPLETE — PUBLISHED (stage authorized by accepted Decision 045, 2026-08-07, outcome M3_2_T2_5_T2_6_INTEGRATED_IMPLEMENTATION_AUTHORIZED, on the published baseline 37866d3de8207528b42b3a207187d02404582370; accepted and published by accepted Decision 046, 2026-08-07, outcome M3_2_T3_ACCEPTED_AND_PUBLISHED, overall determination M3_2_T3_IMPLEMENTATION_ACCEPTED_AND_COMPLETE); accepted corrected candidate 810d567ba7610b22e2ce7cd56b67b7f0e76d26fb, verified tree aa7a7d4a6117160a2a4b2d1165d9b82c318cf968, parent and published Decision 045 baseline f2bbbbf2a1b13e0780c3ea50d01797f78405e97b, subject Complete M3.2 T2.5-T2.6 integrated implementation, NO TAG, and NO STATUS edit by the implementation session; exactly EIGHT changed paths inside the fifteen-path ceiling with NO SIXTEENTH PATH (cli.py, m3/__init__.py, m3/acquisition.py, m3/request_plan.py, tests/integration/test_m3_cli.py, tests/unit/test_m3_acquisition.py, tests/unit/test_m3_dependent_plan.py added, tests/unit/test_m3_request_plan.py; 7707 insertions, 347 deletions), with twenty-five prohibited paths independently proved byte-identical by Git blob hash and an empty diff over Docs, Literature, Milestones, configs, scripts, src/disclosure_drift/storage, pyproject.toml, and Makefile; the delivered scope is the six operator surfaces, the M3.2 acquisition-run identity and attribution, receipt assembly under the frozen m3-execution-receipt/2.0, dependent-plan derivation with plan hash 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68 byte-reproducible, progress-sink sanitization, resume wiring, and integrated validation; DECISION 045'S IMPLEMENTATION AUTHORITY IS EXHAUSTED by this accepted implementation and no further T2.5-T2.6 implementation, further edit to those paths under Decision 045 authority, or second combined-stage commit is authorized; both tracked network switches remain false, CompanyFacts remains disabled, the migration chain remains 0001-0013, ceiling 801 remains unused, and no operational catalog, run row, raw object, live receipt, evidence artifact, request, or SEC contact exists or may be created; overall M3.2 T3 implementation acceptance HAS occurred, and T4, T5, T6, and Gate H remain separate later owner acts that are NOT AUTHORIZED and NOT BEGUN
M3_2_T3_REVIEW_STATUS: COMPLETE AND PASSED — fresh independent corrected-freeze-candidate rereview executed 2026-08-07 by a non-author session on Claude Opus 5 at Max effort with no subagent, delegated agent, background agent, parallel session, worktree, or dynamic workflow; verdict M3_2_T3_CORRECTED_FREEZE_CANDIDATE_REREVIEW_PASS; durable artifact Docs/m3/reviews/m3_2_t3_corrected_freeze_candidate_independent_rereview.md with sha256 31cf05dfe6a1a157df6b05bb6788f6ec9c391742028c24bf06dd3e3fcec2e773, committed alone at 3794178584bd935d5718e6ec5c4279dd235c7b3d (tree 3df60f1430c79eb9cd28f12f265b8bb9c9514234, parent 810d567ba7610b22e2ce7cd56b67b7f0e76d26fb, subject Record independent rereview of corrected M3.2 T3 freeze candidate); reviewed candidate 810d567ba7610b22e2ce7cd56b67b7f0e76d26fb at tree aa7a7d4a6117160a2a4b2d1165d9b82c318cf968; BLOCKER 0, MAJOR 0, MINOR 1, OPTIMIZATION 1; 14 of 14 independent mutations KILLED with zero SURVIVED_EFFECTIVE and zero SURVIVED_NO_OP; full suite 3222 passed / 1 pre-existing unrelated skip (the fixed-literal skip in tests/unit/test_m23_pilot_manifest.py); tests/unit/test_httpx_transport.py 30 passed / 0 skipped; interruption to recovery to SAFE to resume exercised through the real CLI path with a substituted non-network transport, including across separate OS processes; prior MAJOR-1, MINOR-1, and MINOR-2 all CLOSED on independent evidence; the candidate was read-only until the substantive verdict and every destructive probe and mutation ran in a disposable copy outside the repository that was deleted and verified deleted; NO LIVE SEC OPERATION OCCURRED and the review accepted nothing and authorized nothing — acceptance is Decision 046
DECISION_046_STATUS: ACCEPTED — OWNER APPROVED 2026-08-07; outcome M3_2_T3_ACCEPTED_AND_PUBLISHED; the owner determination was issued as the Decision 046 recording packet itself and carries NO separately named OWNER_DECISION_046 instrument token, and none is invented; accepts the corrected combined T2.5-T2.6 implementation candidate 810d567ba7610b22e2ce7cd56b67b7f0e76d26fb at verified tree aa7a7d4a6117160a2a4b2d1165d9b82c318cf968 on parent f2bbbbf2a1b13e0780c3ea50d01797f78405e97b as THE ACCEPTED IMPLEMENTATION FREEZE for the combined stage; accepts the fresh independent T3 rereview verdict M3_2_T3_CORRECTED_FREEZE_CANDIDATE_REREVIEW_PASS and binds its artifact sha256 31cf05dfe6a1a157df6b05bb6788f6ec9c391742028c24bf06dd3e3fcec2e773 at review commit 3794178584bd935d5718e6ec5c4279dd235c7b3d; carries forward MINOR-A (the _execute ordering permits an extremely narrow interruption window after durable commit but before _committed_any = True, potentially reporting before_raw_store_write despite a committed durable retrieval, demonstrated to alter no durable remainder determination, attempt accounting, SAFE recovery, or resume because those are evidence-derived rather than phase-label-derived) as ACCEPTED_NONBLOCKING_OBSERVATION — DEFERRED and OPTIMIZATION-A (_window_reason_code may use SEC_ACQUISITION_INTERRUPTED as fallback for certain non-interrupted failed, stopped, or incomplete outcomes, with no safety consequence and no acceptance defect) as ACCEPTED_NONBLOCKING_OPTIMIZATION — DEFERRED, without reopening T2.5-T2.6, without modifying the accepted implementation, and with any future cleanup requiring separate owner authorization; declares M3_2_T3_IMPLEMENTATION_ACCEPTED_AND_COMPLETE and EXHAUSTS Decision 045's implementation authority; authorizes exactly one normal fast-forward push publishing, in order, the Decision 045 baseline, the accepted candidate, the accepted PASS review, and the Decision 046 governance commit (exact subject Accept M3.2 T3 implementation and independent review), with no amendment, squash, rebase, cherry-pick, insertion, reset, removal, force push, or history rewrite and NO TAG; governance only - no executable byte changes with this record; edits no accepted decision (001-045 byte-unchanged), no contract, no packet, no review artifact, no navigation map, no runbook, no template, no evidence file, and no source, test, configuration, or migration byte; grants NO T4 acceptance, T5 authority, network or CompanyFacts enablement, SEC contact, live acquisition, real operational catalog, receipt emission, ceiling-801 use, migration, receipt-schema, reason-code, production-behavior, tag, T6, Gate H, or M3.3+ authority; F4 remains a T4 obligation; next action CHATGPT_OWNER_M3_2_T4_OPERATIONAL_PREFLIGHT_ARCHITECTURE_DISCOVERY, a planning and discovery action only
DECISION_047_STATUS: ACCEPTED — OWNER APPROVED 2026-08-07; outcome M3_2_T4_OPERATIONAL_PREFLIGHT_AUTHORIZED_AND_PRE_T4_RAWSTORE_SUBSTAGE_AUTHORIZED; the owner determination was issued as the Decision 047 authorization packet itself and carries NO separately named OWNER_DECISION_047 instrument token, and none is invented (the Decision 046 convention); accepts the read-only T4 operational-preflight architecture discovery M3_2_T4_OPERATIONAL_PREFLIGHT_ARCHITECTURE_DISCOVERY_COMPLETE (zero BLOCKER, four MAJOR) and fixes twelve frozen owner rulings 047-A through 047-L: 047-A T4_DOES_NOT_CREATE_THE_OPERATIONAL_CATALOG (catalogs/m3_2a_operational.sqlite3 must not exist at T4 and is first created inside the first lawfully authorized M3.2A live invocation under a later T5 instrument; no contract section 11 amendment and no new catalog-creation CLI surface; T4 may exercise prepare_operational_catalog only against a disposable temporary root); 047-B AUTHORIZE_PRE_T4_RAWSTORE_STREAMING_SUBSTAGE; 047-C record M3-L13 under the register's existing schema and never erase the historical limitation; 047-D discharge F4 with exactly three new evidence-index artifact types frozen_object_identity_set, derived_reference_set, and reconciliation_report, no fourth type, expressly no operational_preflight_attestation, T4 preflight evidence staying private and bound by SHA-256 through the ledger; 047-E a genuine off-device or independently recoverable backup REQUIRED before T5, same-device-only insufficient, .env and SEC identity excluded, per-file SHA-256 manifest, source/backup verification, scratch-location restore test, no overwrite of the operational root, no new backup script; 047-F targeted, static, one-full-suite, secrets/hygiene/context validation plus a fresh independent review before owner acceptance; 047-G the future T5 authorizes exactly ONE initial M3.2A live invocation with no advance resume authority and UNDETERMINED remaining a stop; 047-H a conservative hard T5 entry floor FREE DISK >= 50 GiB measured immediately before live authorization, with the unknown SEC bulk-object size never estimated as fact; 047-I the identity validated locally but never displayed, logged, committed, placed in an artifact or receipt, or typed inline into shell history; 047-J a fresh independent review required for the RawStore substage and not automatically required for a later governance/evidence-only T4 if no executable byte changes; 047-K Decision 046's T3 MINOR-A stays ACCEPTED_NONBLOCKING_OBSERVATION — DEFERRED and unmodified; 047-L progress-sink DISCHARGED and D023-O1 LATENT, NOT TRIGGERED, M3.3-scoped; authorizes one bounded pre-T4 RawStore streaming substage across exactly two executable paths src/disclosure_drift/sec/raw_store.py and tests/unit/test_raw_store.py, narrowly releasing Decision 045 section 16's prohibition on sec/raw_store.py for this substage only with every other prohibited path unchanged and a third path an immediate stop; authorizes exactly five governance paths (this record, the registry, this ledger, Docs/m3/templates/evidence_index.md, Docs/m3/limitations_register.md) with no sixth, and two separate local commits with no push and no tag; it is NOT T4 execution, NOT T4 acceptance, NOT T5/T6/Gate H authority, and NOT network or live-operation authority, and it edits no Decision 001-046
DECISION_048_STATUS: ACCEPTED — OWNER APPROVED 2026-08-07; outcome M3_2_PRE_T4_RAWSTORE_ACCEPTED_AND_PUBLISHED; the owner determination was issued as the Decision 048 recording packet itself and carries NO separately named OWNER_DECISION_048 instrument token, and none is invented (the Decision 046/047 convention); fixes eleven rulings 048-A through 048-K: 048-A accepts the corrected pre-T4 RawStore streaming candidate 833a192839e888720389c4757250234b5cb219b7 (tree c2d95badd8d137ebbb00a642d087fb03e1ec7353; parent and Decision 047 governance baseline bc3d170a155aaa6c196536109ef57dd841226675; subject Stream raw-object storage instead of buffering it) across its exact two-path envelope src/disclosure_drift/sec/raw_store.py and tests/unit/test_raw_store.py with no third path, the acceptance being SHA-specific and tree-specific and not transferring automatically to a later changed tree, and records that the candidate removes full-object buffering while preserving the deterministic stored representation, content and stored identities, durability and atomic create-once semantics, deduplication and collision semantics, and the unchanged public RawStore API, and corrects verify() so the exact immutable gzip representation is structurally validated; 048-B accepts the fresh independent non-author rereview (artifact Docs/m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md, sha256 7bd5a5441fc4a0218e18a5a5daddf5a53c4436a938ea942fc6f84835d265fc42, review commit 9406afbe88e83f7a0f0a52db290f9a220d01e6bc, verdict M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEW_PASS, BLOCKER 0, MAJOR 0, MINOR 2, OPTIMIZATION 2, 12/12 independent mutations KILLED, 108/108 deterministic-gzip cases byte-exact, bounded memory for valid objects, full suite 3246 passed / 1 pre-existing unrelated skip, tests/unit/test_httpx_transport.py 30 passed / 0 skipped), the substantive acceptance threshold BLOCKER 0 and MAJOR 0 being satisfied; 048-C closes the first review's acceptance-blocking RawStore.verify() MAJOR because trailer-truncated gzip, valid gzip plus trailing garbage, and concatenated second gzip members are all refused and the rereviewer proved those refusals are not shadowed by stored or content identity mismatches, so no further RawStore correction is required before T4; 048-D carries MINOR-1 as ACCEPTED_NONBLOCKING_TEST_STRENGTH_OBSERVATION — DEFERRED (the committed suite contains no isolated mutation killer for the content_sha256 comparison; production enforcement is independently demonstrated correct, no production correctness defect exists, the accepted candidate is not reopened to add one redundant test, and any later test-strength cleanup requires separate authority); 048-E carries MINOR-2 as ACCEPTED_NONBLOCKING_CORRUPT_PATH_RESOURCE_OBSERVATION — DEFERRED (zlib may retain a large trailing-garbage tail in unused_data while verifying an already-corrupt object; invalid objects remain correctly refused, lawful verification remains bounded-memory, RawStore.verify() has zero production callers, the M3.2 live storage path does not rely on it, and no live-operation safety defect requiring T4 remediation is established); 048-F and 048-G carry OPTIMIZATION-1 (the unconsumed_tail final guard is redundant because the bounded decompression loop drains it, is harmless and fail-closed, and is not removed now) and OPTIMIZATION-2 (SnapshotStore.load_payload() uses a whole-file read but is outside the M3.2 live acquisition and storage critical path and appears nowhere in the m3 package, so T4 scope is not broadened) as ACCEPTED_NONBLOCKING_OPTIMIZATION — DEFERRED, and none of the four findings creates a limitations-register entry; 048-H closes M3-L13 under the register's existing schema on its seven-item closure-evidence list (Decision 047 authorization bc3d170, accepted implementation 833a192, accepted tree c2d95bad, independent PASS artifact and its sha256 7bd5a544, review commit 9406afb, and owner acceptance by Decision 048), preserving the historical description, updating register totals to 35 open and 4 closed, and closing no other limitation with D023-O1 unchanged; 048-I accepts Decision 047 and its F4 three-type vocabulary extension for publication exactly as recorded with no fourth type and expressly no operational_preflight_attestation, Docs/m3/templates/evidence_index.md being byte-unchanged by this record and no further F4 change required before T4 execution; 048-J records that Decision 047 provides the governing T4 authorization but T4 OPERATIONAL EXECUTION HAS NOT YET OCCURRED and still requires a separate exact ChatGPT-owner execution packet; and 048-K fixes the negative authority; authorizes exactly four governance paths (this record, the registry, this ledger, Docs/m3/limitations_register.md) with no fifth, one governance commit with exact subject Accept pre-T4 RawStore correction and independent rereview, and one normal fast-forward publication push of the lineage e391ff3 then bc3d170 then 833a192 then 9406afb then this record, push only main to origin/main with no force, no force-with-lease, no rebase, no squash, no amend, no cherry-pick, no replacement branch, and no history rewrite; NO TAG; governance only - no executable byte changes with this record; edits no accepted decision (001-047 byte-unchanged), no review artifact, no contract, no packet, no template, no migration, no configuration, no reason code, no receipt schema, no test, and no Docs/decision_index.md; and grants NO T4 execution, no real operational catalog creation, no real SEC identity validation, no off-device backup execution, no T5, no T6, no network enablement, no CompanyFacts, no live SEC access, no DNS lookup, no connectivity testing, no HTTP or socket activity, no request attempt, no consumption of ceiling 801, no resume, no M3.2B derivation, no Gate H, no new executable change, no additional test change, and no tag
M3_2_PRE_T4_RAWSTORE_SUBSTAGE_STATUS: ACCEPTED AND COMPLETE — accepted Decision 048, 2026-08-07, outcome M3_2_PRE_T4_RAWSTORE_ACCEPTED_AND_PUBLISHED; accepted candidate 833a192839e888720389c4757250234b5cb219b7, accepted tree c2d95badd8d137ebbb00a642d087fb03e1ec7353, parent and Decision 047 governance baseline bc3d170a155aaa6c196536109ef57dd841226675, subject Stream raw-object storage instead of buffering it, exactly two executable paths (src/disclosure_drift/sec/raw_store.py, tests/unit/test_raw_store.py) with no third, NO TAG; acceptance is SHA-specific and tree-specific and does not transfer automatically to a later changed tree; independent rereview verdict M3_2_PRE_T4_RAWSTORE_CORRECTED_INDEPENDENT_REREVIEW_PASS with zero BLOCKER and zero MAJOR, artifact Docs/m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md sha256 7bd5a5441fc4a0218e18a5a5daddf5a53c4436a938ea942fc6f84835d265fc42 at review commit 9406afbe88e83f7a0f0a52db290f9a220d01e6bc; the first review's acceptance-blocking RawStore.verify() MAJOR is CLOSED (trailer-truncated gzip, valid gzip plus trailing garbage, and concatenated second members all refused, proved not shadowed by stored or content identity mismatches); MINOR-1, MINOR-2, OPTIMIZATION-1, and OPTIMIZATION-2 carried as accepted nonblocking and deferred with no limitations-register entry; published by one authorized normal fast-forward push of the four-commit sequence above the published Decision 046 baseline e391ff3aa088b14b4be03457f5a13c0292253c86; Decision 047's substage implementation authority is exhausted; this is substage acceptance only - T4 OPERATIONAL EXECUTION HAS NOT OCCURRED and T5 and T6 remain unauthorized and not begun
M3_L13_STATUS: CLOSED — DECISION 048, 2026-08-07; closed under accepted Decision 048 section 7 (ruling 048-H) on the entry's own closure-evidence list, every item satisfied: Decision 047 authorization bc3d170a155aaa6c196536109ef57dd841226675; accepted corrected implementation 833a192839e888720389c4757250234b5cb219b7; accepted candidate tree c2d95badd8d137ebbb00a642d087fb03e1ec7353; independent PASS artifact Docs/m3/reviews/m3_2_pre_t4_rawstore_corrected_independent_rereview.md; artifact sha256 7bd5a5441fc4a0218e18a5a5daddf5a53c4436a938ea942fc6f84835d265fc42; review commit 9406afbe88e83f7a0f0a52db290f9a220d01e6bc; and the owner's separate acceptance recorded in Decision 048. The historical description is preserved and never erased (Decision 047 ruling 047-C). Register totals recomputed to 35 open, 4 closed; no other limitation is closed and D023-O1 remains LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED. Its two accepted nonblocking observations (Decision 048 sections 6.1 and 6.2) are carried on the entry and create no register entry of their own. HISTORICAL RECORD AS ORIGINALLY RAISED: RawStore.store() buffered the complete decoded object body in one Python bytearray on every call including compress=False where the buffer was never read, and read the entire promoted file back with Path.read_bytes() for stored_sha256 and stored_size_bytes, with an additional bytes(buffer) copy, whole compressed output, and whole decompressed round-trip copy on the compress=True path; measured directly on an 8 MiB payload in 512 KiB chunks with tracemalloc at peak 2.12x object size for compress=False and 3.80x for compress=True; RawStore.verify() and the existing-object deduplication branch performed the same whole-file reads; the Decision 047 section 6 two-path correction is IMPLEMENTED LOCALLY but the entry is NOT CLOSED — closure requires the fresh independent non-author review and the owner's separate acceptance; no research definition, identity, hash preimage, or stored byte changes, and the public RawStore API is unchanged
DECISION_038_STATUS: ACCEPTED — OWNER APPROVED 2026-08-05; outcome M3_2_T2_2_T2_3_PATH_ENVELOPE_AMENDMENT_RECORDED; records verbatim the owner instrument OWNER_DECISION_038_M3_2_T2_2_T2_3_PATH_ENVELOPE_AMENDMENT: APPROVED; the durable record of the previously granted owner path-envelope adjudication, whose absence was the sole PASS-blocking finding of the final independent rereview; amends Decision 035 section 6, the T2 packet section 5 fifteen-path maximum, and the unchanged-envelope statements in Decisions 036 and 037 FOR THE COMBINED T2.2-T2.3 STAGE ONLY, adding exactly two paths - src/disclosure_drift/sec/observation_catalog.py (widen ObservationRecorder.record members from an eager sequence boundary to a compatible single-pass iterable boundary and consume archive-member lineage lazily inside the observation's own transaction, preserving existing sequence-caller compatibility and deterministic order, lineage validation, rollback, reuse, and supersession behaviour) and tests/unit/test_observation_catalog.py (the direct tests proving those properties) - bound to and limited by the exact changes in candidate 6b189df1651ec3674ec7f96a1f5d66f488c654a9 and tree 8850e1e45e9471bbb8b94612da67715e932a496f; ratifies the earlier explicit owner correction authorization of 2026-08-05 granted before those paths were edited and states expressly that this is not retrospective self-widening by an implementation agent; is the higher-authority narrow amendment with partial supersession only, leaving the ceiling-not-grant character of the envelope, the immediate-stop rule for any further out-of-subset need, the stage cadence, the commit boundaries, and every other declined and prohibited surface in force; edits no accepted decision in place (032-037 byte-unchanged), preserves the T2 packet byte-identical at sha256 621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599 which must not be silently rewritten, and does not edit the accepted contract (sha256 c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7); governance only - no executable byte changes with this record; authorizes no further edit to either added path, adds neither path to T2.4 or T2.5-T2.6 authority, broadens no other stage envelope, and grants no operator CLI wiring, no T2.4, no T3/T4/T5, no network or CompanyFacts enablement, no SEC contact or connectivity testing, no acquisition, no receipt or evidence creation, no operational-catalog creation, no use of ceiling 801, no Gate H, no tag, and no push; it neither accepts nor publishes the implementation candidate
DECISION_039_STATUS: ACCEPTED — OWNER APPROVED 2026-08-06; outcome M3_2_T2_2_T2_3_ACCEPTED_AND_COMPLETE; records verbatim the owner instrument OWNER_DECISION_039_M3_2_T2_2_T2_3_STAGE_ACCEPTANCE_AND_PUBLICATION_AUTHORIZATION: APPROVED; accepts the combined Milestone 3.2 implementation stage T2.2-T2.3 (Catalog, Immutable Storage, and Acquisition Engine) at candidate 6b189df1651ec3674ec7f96a1f5d66f488c654a9, tree 8850e1e45e9471bbb8b94612da67715e932a496f, published baseline and parent feb9e134307a9551475f243dc0c1ddcecc89ffde, exactly six paths; adopts the final independent no-subagent adversarial technical rereview's ten findings including memory-bounded archive transport and candidate-owned lineage, single-pass deterministic transactional archive-member persistence, no partial catalog transaction on failed enumeration or insertion, correct reuse/supersession/immutable-object preservation/lineage reconciliation, clock-locale-timezone-platform-independent ZIP fixtures, no private-path or payload disclosure through bounded operational-error outputs, fail-closed plan/route/ceiling/completion/recovery-observability/no-network boundaries, passing static/targeted/mutation/determinism/full-suite validation, and no live SEC access or operational artifact; records that accepted Decision 038 (governance commit 27842965ed5a8fcccbf5fbb3c3c63ff2c2e798ba) cured the sole PASS-blocking governance-record defect and accepts it as the controlling higher-authority amendment for src/disclosure_drift/sec/observation_catalog.py and tests/unit/test_observation_catalog.py; authorizes one normal fast-forward push publishing in order the candidate, the Decision 038 commit, and the Decision 039 acceptance commit, only after durable recording, register and ledger agreement, unchanged candidate bytes, unchanged contract and packet hashes, origin/main verified an ancestor of local HEAD, behind zero with no divergence, and passing governance validation; NO TAG IS AUTHORIZED FOR THIS STAGE; keeps stage acceptance, publication, and overall M3.2 T3 implementation acceptance distinct and records that T3 ACCEPTANCE HAS NOT OCCURRED; governance only - no executable byte changes with this record; edits no accepted decision (032-038 byte-unchanged), no contract, no packet, no review artifact, no migration, no configuration, no reason code, no receipt schema, and no Docs/decision_index.md; grants no T2.4, does not carry the Decision 038 path expansion into T2.4 or T2.5-T2.6, and grants no repair/reconciliation/drift/resume, operator CLI wiring, conditional requests or 304 or cache resume, singleton bootstrap-absence reason resolution, F4 resolution, D023-O1 modification, network or CompanyFacts enablement, SEC contact or connectivity testing, real operational-catalog creation, receipts, private evidence, acquisition, use of ceiling 801, or any tag, force push, history rewrite, rebase, squash, or amend
M3_2_T2_2_T2_3_STAGE_STATUS: ACCEPTED AND COMPLETE — accepted Decision 039, 2026-08-06, outcome M3_2_T2_2_T2_3_ACCEPTED_AND_COMPLETE; accepted candidate 6b189df1651ec3674ec7f96a1f5d66f488c654a9, accepted tree 8850e1e45e9471bbb8b94612da67715e932a496f, published baseline and parent feb9e134307a9551475f243dc0c1ddcecc89ffde, subject Implement M3.2 T2.2-T2.3 acquisition foundation, exactly six paths (m3/__init__.py, m3/acquisition.py, sec/observation_catalog.py, tests/integration/test_m3_cli.py, tests/unit/test_m3_acquisition.py, tests/unit/test_observation_catalog.py), NO TAG. Final independent no-subagent adversarial rereview verdict M3_2_T2_2_T2_3_SECOND_CORRECTED_INDEPENDENT_REREVIEW: PASS_WITH_REQUIRED_CORRECTIONS with zero BLOCKER, its ten findings adopted by Decision 039; the sole PASS-blocking issue was the absence of a durable path-envelope amendment, cured by accepted Decision 038 (governance commit 27842965ed5a8fcccbf5fbb3c3c63ff2c2e798ba, tree 6bead61920ad947d35b300e9d81634ca5c767358). Published by one authorized normal fast-forward push of the three-commit sequence with no tag. Superseded candidates 41f5f62870b0133fe91cc630e9d0040c0e027002 and 73448f28217b0b73164bed179cf577164027adf8 are historical only and are on no branch. This is stage acceptance only: overall M3.2 T3 implementation acceptance has not occurred, and T2.4 and combined T2.5-T2.6 remain owner-gated, unauthorized, and not begun
DECISION_037_STATUS: ACCEPTED — OWNER APPROVED 2026-08-04; outcome M3_2_REMAINING_STAGES_COMBINED; the separate explicit owner decision Decision 035 section 7 item 8 requires before any stages may be combined; consolidates the remaining T2 work into combined T2.2-T2.3 (Catalog, Immutable Storage and Acquisition Engine; subject Implement M3.2 T2.2-T2.3 acquisition foundation), separate T2.4 (Recovery, Reconciliation and Drift Control; subject Implement M3.2 T2.4 recovery and reconciliation), and combined T2.5-T2.6 (Operator Surfaces and Integrated Implementation Candidate; subject Complete M3.2 T2.5-T2.6 integrated implementation), so the cadence is four stages in total with T2.1 already complete; at most one commit per stage, each local until ChatGPT review and acceptance then one normal fast-forward push, no next stage before the prior is accepted and published, no further combination without a new explicit owner decision, and no interim stage tag or T3 tag; the combined T2.5-T2.6 commit is the implementation-freeze candidate for independent T3 review, replacing the former standalone T2.6 commit; a combined stage may use internal validation subphases but yields one coherent candidate, and within T2.2-T2.3 no owner review is required between the catalog/storage and acquisition-engine subphases unless an authorized-path expansion, migration, new reason code, or frozen-receipt-schema insufficiency appears necessary, the accepted architecture cannot be implemented as written, or a BLOCKER or relevant MAJOR finding arises — each an immediate stop; supersedes only the T2 packet's remaining-stage cadence and commit-boundary provisions, leaving the packet byte-unchanged at sha256 621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599 with every other requirement controlling; amends contract section 22 plus the consequent authority metadata, post-amendment contract sha256 c526335b91ddb75877e66ecef3255dce6c4c27e60ae0c5a7286228935d42edb7; preserves the fifteen-path envelope, routes and sources, plan/budget/ceiling-801 identities, raw-object and catalog semantics, the frozen receipt schema, recovery and completion semantics, evidence requirements, independent T3 review, T4 preflight, per-window T5, and Gate H; changes no executable byte; edits no accepted decision (032-036 untouched), no packet, and no review artifact; and authorizes no implementation of T2.2-T2.3 or any later stage, no acquisition.py, no operational catalog, no storage integration, no scripted or live transport, no receipt emission, no network or CompanyFacts enablement, no SEC connectivity testing, no live SEC access, no acquisition, no ceiling-801 use, no T3/T4/T5 or Gate H execution, no migration, no receipt-schema change, no new reason code, and no tag
M3_2_T2_1_STAGE_STATUS: COMPLETE — OWNER-ACCEPTED AND PUBLISHED 2026-08-04 — accepted Decision 036, outcome M3_2_T2_1_ACCEPTED_AND_PUBLISHED; stage T2.1 (configuration and fail-closed command-authority layer) implemented within its exact six-path authorization, reviewed, accepted, and published at commit 7b2ffe643a2e2e600f148592fc9f8ded5695a279 (parent 9730f8b564f49b8fdba76da31cf6d2fa0b6aacc6; tree 0ae3cb0ba8bd9484c02f8920e2ed44c30a96a87e; subject Implement M3.2 T2.1 authority layer) by one normal fast-forward push with no tag; changed exactly configs/project.yaml, src/disclosure_drift/config.py, src/disclosure_drift/cli.py, src/disclosure_drift/m3/__init__.py, tests/integration/test_m3_cli.py, tests/unit/test_config.py and no seventh path; tests/integration/test_no_network.py, tests/conftest.py, m3/receipt.py, reasons.py, every migration, and all of Docs and Milestones proven byte-identical across the stage commit; targeted validation 126 passed with no skipped and no xfailed test, plus clean ruff, ruff format, mypy, secrets, hygiene, and diff-check gates; delivered network.m3_acquire_enabled with tracked default false, network.enabled still false with unchanged semantics, the two switches independent in both directions under strict unknown-field rejection with no environment fallback, all six M3.2 command surfaces recognized and every one fail-closed at exit 3 without traceback, no switch combination reaching or constructing transport across the full six-row conjunction, no fake T3/T4/T5/readiness/owner-authorization state, and M2.2 commands still controlled only by network.enabled; no transport, operational catalog, receipt, evidence artifact, raw object, token, logical request, physical attempt, hostname lookup, socket operation, or SEC contact occurred; findings M1 and M2 accepted as nonblocking and optimization O1 corrected before acceptance; the remaining stages — combined T2.2-T2.3, separate T2.4, and combined T2.5-T2.6 under accepted Decision 037 — remain owner-gated and unauthorized
M3_2_T2_AUTHORIZATION_STATUS: STAGED T2 IMPLEMENTATION AUTHORIZED — STAGE T2.1 ONLY (HISTORICAL AS ISSUED; ITS CADENCE CLAUSE IS SUPERSEDED BY ACCEPTED DECISION 037, WHICH CONSOLIDATES THE REMAINING STAGES INTO COMBINED T2.2-T2.3, SEPARATE T2.4, AND COMBINED T2.5-T2.6, AND MAKES THE COMBINED T2.5-T2.6 COMMIT THE IMPLEMENTATION-FREEZE CANDIDATE; DECISION 035 REMAINS CONTROLLING FOR THE STAGED T2 AUTHORIZATION AND THE FIFTEEN-PATH ENVELOPE, AND STAGE T2.1 IS NOW COMPLETE UNDER DECISION 036) — accepted Decision 035, owner approved 2026-08-04, outcome M3_2_T2_STAGED_IMPLEMENTATION_AUTHORIZED; owner instrument OWNER_M3_2_T2_IMPLEMENTATION_AUTHORIZATION: APPROVED_WITH_STAGE_LIMIT recorded verbatim, bound to repository baseline 8dd4a1675019a9a885b04703d18e0274173f52c3 and T2 packet revision v2 sha256 621201464ffd0e236b90aefe3cd9f587b1c4873011e32df2aef596c7ff314599; T2 packet revision v2 ACCEPTED as the controlling implementation plan and preserved unchanged; all five Decision 024 section 8 entry conditions determined satisfied for the bounded staged implementation; maximum T2 envelope fixed at packet section 5 P1 through P8 and T1 through T7 (fifteen paths) subject to narrower per-stage subsets, with the declined and prohibited surfaces still prohibited and any out-of-subset need an immediate stop for new owner adjudication; contract section 22 amended to the six-stage T2.1 through T2.6 commit and review cadence (at most one commit per stage using the exact packet section 6 subject; no interim commit inside a stage without a separate owner interruption ruling; each stage commit local until ChatGPT reviews and accepts it; then one normal fast-forward push; the next stage may not begin before the prior stage is reviewed, accepted, and published; stages may not be combined; no stage tag and no T3 tag; the T2.6 commit is the implementation-freeze candidate for the independent T3 review) — staging and commit governance only, altering no route, source, plan, ceiling, storage semantic, recovery semantic, evidence requirement, or live-operation authority; IMMEDIATE EXECUTABLE AUTHORITY IS STAGE T2.1 ONLY, bounded to exactly six paths — configs/project.yaml, src/disclosure_drift/config.py, src/disclosure_drift/cli.py, src/disclosure_drift/m3/__init__.py, tests/integration/test_m3_cli.py, tests/unit/test_config.py; STAGES T2.2 THROUGH T2.6 REMAIN OWNER-GATED AND ARE NOT AUTHORIZED TO BEGIN; T2.1 may implement only the tracked-default network.m3_acquire_enabled false, the one NetworkSection field m3_acquire_enabled bool False, strict parsing and fail-closed configuration behavior, parser and command-dispatch skeletons for all six M3.2 command surfaces, refusal behavior for unavailable or unauthorized command paths, the m3 acquire --live refusal skeleton, proof that no transport can be constructed by the T2.1 implementation, proof that existing M2.2 commands remain governed only by network.enabled, and the T2.1 tests and positive controls named by the packet; T2.1 must not implement acquisition, storage integration, reconciliation, drift processing, recovery repair, dependent-plan derivation, receipt emission, or transport construction, and must not invent a fake machine-readable T3-accepted or T5-authorized boolean, token, bypass, or hard-coded authorization; no implementation-stage test may contact the SEC or use the real SEC identity; network.enabled remains false and unchanged and network.m3_acquire_enabled may not be committed true; post-amendment contract sha256 7a3fe7ff8503268c57081a45ae756989c2c2348c427842b4d2193acd04582b03; R1 accepted and binding where applicable; F3 accepted and binding for T2.4; F4 evidence-index vocabulary additions NOT accepted and remaining a separate governance decision due no later than T4 and before the first affected artifact is publicly indexed; NO IMPLEMENTATION HAS BEGUN and a separate exact T2.1 execution packet from ChatGPT is still required before any implementation session; the decision grants no T3, T4, T5, or T6, no network or CompanyFacts enablement, no SEC connectivity testing, no HTTP request, no live SEC access, no operational catalog, no ceiling-801 use, no M3.2A or M3.2B execution, no Gate H, no migration, no receipt-schema change, no new reason code, no tag, and no M3.3 or later work
DECISION_035_STATUS: ACCEPTED — OWNER APPROVED 2026-08-04; outcome M3_2_T2_STAGED_IMPLEMENTATION_AUTHORIZED; the durable recording the owner instrument requires as a precondition to acting on it; amends the accepted M3.2 contract section 22 only (the six-stage cadence) plus the directly consequent authority metadata; edits no accepted decision (032, 033, 034 untouched) and preserves the T2 packet and both M3.2 review artifacts unchanged; changes no executable byte — src, tests, configs, migrations, and templates remain byte-identical to the frozen accepted M3.1 SHA 970e050deb06910adcde8588101564beb7d19c74; grants staged T2 authority for stage T2.1 only and creates no tag
M3_2_T2_PACKET_STATUS: ACCEPTED AS THE CONTROLLING IMPLEMENTATION PLAN (revision v2; accepted Decision 035, 2026-08-04; preserved unchanged — its own header retains the as-submitted draft wording by the artifact-preservation convention, and this ledger plus Decision 035 carry its accepted disposition) — Docs/m3/m3_2_t2_implementation_authorization_packet.md, revision v2 of 2026-08-04, prepared under OWNER_M3_2_T2_PACKET_PREPARATION_AUTHORIZATION: APPROVED (preparation only; approval expressly withheld) and revised the same day under the owner's detailed preparation instruction, superseding the v1 draft in place (v1 preserved in history at commit 60865c044c6d6e005be3cb3ad81da56bff87392b); formal state M3_2_T2_PACKET_PREPARED_FOR_OWNER_REVIEW; readiness conclusion READY_FOR_OWNER_T2_DECISION; IMPLEMENTATION AUTHORIZATION NOT GRANTED; NETWORK_AUTHORIZATION NONE; audits the five Decision 024 section 8 entry conditions (1, 2, 5 satisfied; 3 is the requested decision; 4 the proposed enumeration); proposes exactly fifteen authorized paths — production configs/project.yaml (one key network.m3_acquire_enabled, default false, never committed true), src/disclosure_drift/config.py (one NetworkSection field), src/disclosure_drift/m3/acquisition.py (the only new module, carrying the driver plus reconciliation and drift logic per contract section 16), src/disclosure_drift/cli.py, src/disclosure_drift/m3/request_plan.py (M3.2B derivation; plan hash 19be7bdc… must reproduce), src/disclosure_drift/m3/recovery.py (repair applier; inspector unchanged), src/disclosure_drift/reasons.py (reserved — an unregistered condition is a stop condition, never a code invented under T2), src/disclosure_drift/m3/__init__.py; tests tests/unit/test_m3_acquisition.py, tests/unit/test_m3_dependent_plan.py, tests/unit/test_m3_recover.py (new) plus bounded edits to tests/integration/test_m3_cli.py, tests/unit/test_m3_request_plan.py, tests/unit/test_m3_recovery.py, tests/unit/test_config.py; sec/census_orchestrator.py and sec/index_retrieval.py DECLINED and prohibited; dispositions all six planned commands in full; proposes stages T2.1–T2.6 with one commit per stage, exact commit subjects, per-stage ChatGPT owner review boundaries, stage-specific model routing, and stage tags prohibited — the per-stage commit cadence requires the owner's T2 instrument to amend the accepted contract section 22 one-commit default, routed to the owner unresolved; carries R1 (catalog-resident item-level absences; completed_with_absences as a governance classification outside the frozen receipt; plan-hash linkage; non-vacuous frozen-schema tests), F3 (conservative accounting; full per-route A_reachable charge; UNDETERMINED stop; eight kill-point tests), and F4 (proposed new types frozen_object_identity_set, derived_reference_set, reconciliation_report; recovery_state_report mapped to the existing type; no aggregate packet type; owner decision required before first public indexing and no later than the T4 preflight boundary); names seven stop-and-return conditions; includes the eleven-row network conjunction table with every partial combination refusing before transport construction; and reproduces the proposed T2 owner instrument unissued; the packet grants no T2, changes no executable byte, enables no network or CompanyFacts, authorizes no SEC contact, acquisition, operational catalog, ceiling-801 use, M3.2B work, Gate H, or tag
M3_2_CONTRACT_REREVIEW_STATUS: COMPLETE 2026-08-04 — fresh independent rereview of the corrected M3.2 contract by one non-author session using no subagents (Decision 032 section 6; Decision 033 section 10); verdict M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS; zero BLOCKER, zero MAJOR, one MINOR (R1 — the receipt-enumeration surface, carried forward as mandatory T2-packet content by Decision 034 section 6), one OPTIMIZATION (R2 — nonblocking); artifact Docs/m3/reviews/m3_2_corrected_contract_independent_rereview_3bf9987dd72e1531da2f678fbbef735f37aefcf4.md, sha256 91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf, committed governance-only at 3069b03ede9d805e9d0196a3e4c45c8cc68f42b7; independence, no-subagent execution, and the container-continuity disclosure attested in the artifact section 1; zero live SEC access; the rereview accepted nothing and authorized nothing
DECISION_034_STATUS: ACCEPTED — OWNER APPROVED 2026-08-04; outcome M3_2_CONTRACT_ACCEPTED_AT_T1; records the owner's verbatim T1 acceptance instrument ACCEPT_M3_2_CORRECTED_CONTRACT_AT_T1 bound to the PASS rereview (artifact sha256 91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf; rereview commit 3069b03ede9d805e9d0196a3e4c45c8cc68f42b7); accepts the corrected contract unchanged at T1 (accepted-text sha256 75e7e5a11f6e02933c878894091b4a38cef609a1568a6095b0dbb2841e23d8d3; post-acceptance file sha256 a5ac0e8d042d90a7cff43a476258523ab71977b4b3d50ffe6777424720ae4ab2, status/authority metadata only); accepts R1 as nonblocking and mandates the four-part T2-packet content; accepts R2 as nonblocking with no contract edit; preserves every residual limitation open; grants no T2/T3/T4/T5 authority, no network or CompanyFacts enablement, no live SEC access, no connectivity testing, no acquisition, no operational catalog, no ceiling-801 use, no tag, and no push
DECISION_033_STATUS: ACCEPTED — OWNER APPROVED 2026-08-04; outcome M3_2_CORRECTION_PASS_ADJUDICATED_AND_CLEANED_UP; records the owner's verbatim 2026-08-04 adjudication of the Decision 032 correction pass published at 96dea2b50b7e87243aad29032946ef8447033eb9: findings F1 through F7 accepted as substantively addressed; the prior review artifact preserved and expressly not the final independent acceptance review; a fresh non-author no-subagent rereview still mandatory; Docs/decision_index.md restored to its exact bytes at parent commit 3fbaa12d671d0000f5b608bbf6fb271f78b4673f because that path was outside the final authorized-path list (so Decision 032 sections 5.5 and 7 name an F5 correction target that now carries no correction, recorded in Decision 033 section 5 rather than by editing the accepted record, and the stale Decision-029 next-action sentence in the index remains an open nonblocking navigation-staleness item needing its own path authorization); the exact next-action marker corrected; the nonconforming published commit subject accepted as a non-substantive procedural deviation; no history rewrite authorized and none performed; accepted Decision 032 not edited; the corrected M3.2 contract remains unaccepted and byte-unchanged; implementation, network and CompanyFacts enablement, live SEC access, acquisition, operational-catalog creation, and ceiling use all remain unauthorized; creates no tag
DECISION_032_STATUS: ACCEPTED — OWNER APPROVED 2026-08-04; outcome M3_2_CONTRACT_CORRECTIONS_RECORDED; records the owner's verbatim 2026-08-04 correction instrument bound to review commit 3fbaa12d671d0000f5b608bbf6fb271f78b4673f and review-artifact sha256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57; adopts findings F1 through F7 and authorizes the bounded correction of the M3.2 contract draft, this durable recording, the related registry, status, and navigation updates, and one normal fast-forward push; requires a fresh independent rereview of the corrected contract by one non-author session using no subagents before owner acceptance; accepts no contract, authorizes no implementation, changes no executable byte, enables no network or CompanyFacts, authorizes no live SEC access, no acquisition, no operational catalog, and no use of the M3.2A ceiling; creates no tag
M3_1_CHECKPOINT_STATUS: COMPLETE — Decision 029 section 12 step 16 executed 2026-08-03 under explicit owner authorization; annotated tag m3.1-complete created exactly once at the acceptance commit 4cd2c7299ae30ca499108bd7f0a17a0adaf215f4 with annotation "Complete M3.1 acceptance checkpoint" (tag object 638a02b780d912ff7b37a2f523277b9d451a015a); pushed as the single ref refs/tags/m3.1-complete and verified locally and remotely (matching tag objects and peeled targets; HEAD == origin/main; every prior tag unchanged; no tracked file changed; no commit created); Decision 029 section 12 steps 1 through 16 discharged
M3_L11_M3_L12_STATUS: CLOSED 2026-08-03 — both entries closed under the owner's explicit Decision 029 section 12 step-17 closure authorization, each on its complete closure-evidence list (bounded implementation and tests in the frozen accepted tree 970e050deb06910adcde8588101564beb7d19c74; full validation; independent M3.1 acceptance M3_1_INDEPENDENT_ACCEPTANCE_REVIEW: PASS; owner acceptance recorded by accepted Decision 031; and the verified m3.1-complete checkpoint, tag object 638a02b780d912ff7b37a2f523277b9d451a015a, peeled 4cd2c7299ae30ca499108bd7f0a17a0adaf215f4); the Decision 030 Ruling D sequencing distinction is preserved (Gate-F-facing requirement satisfied before signing; administrative closure at the completed acceptance-and-checkpoint sequence); Decision 013 byte-for-byte unchanged; register totals 35 open, 3 closed; D023-O1 unchanged — LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED
M3_2_CONTRACT_STATUS: ACCEPTED (T1) — DECISION 034 (2026-08-04) — IMPLEMENTATION NOT AUTHORIZED — Milestones/contracts/m3_2.md drafted 2026-08-03 at Decision 029 section 12 step 17 under the owner's explicit step-17 authorization and corrected once on 2026-08-04 under accepted Decision 032 (independent contract review verdict M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS; review artifact sha256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57; review commit 3fbaa12d671d0000f5b608bbf6fb271f78b4673f; corrected sections 1, 2, 4, 5, 12, 14, 15, 16, 18, 19, 20, and 25); rereviewed fresh with no subagents on 2026-08-04 (M3_2_CORRECTED_CONTRACT_INDEPENDENT_REREVIEW: PASS; artifact sha256 91235a1a58f94692d5607908e5fa1e2e3adc11722a0a417fc6d47798f3fefacf; rereview commit 3069b03ede9d805e9d0196a3e4c45c8cc68f42b7; zero BLOCKER; zero MAJOR; R1 MINOR carried as mandatory T2-packet content by Decision 034 section 6; R2 OPTIMIZATION nonblocking); accepted unchanged at T1 by accepted Decision 034 (2026-08-04; accepted-text sha256 75e7e5a11f6e02933c878894091b4a38cef609a1568a6095b0dbb2841e23d8d3; post-acceptance file sha256 a5ac0e8d042d90a7cff43a476258523ab71977b4b3d50ffe6777424720ae4ab2 reflecting the Decision-034-authorized status/authority-metadata update only); bounded to master plan M3.2 sections 1-36 and global section 16; carries the frozen M3.2A inputs (request-plan sha256 19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68; request-budget sha256 2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f; owner-approved hard request ceiling 801; 75 planned unique logical requests; 70 required quarterly-index instances; 75 maximum new raw objects; 0 expected cache hits; no contingency; 200.0-second spacing floor), strict stop-before-overflow, the accepted route allowlist and denylist, boundary-only SEC-identity handling, immutable raw-object and receipt requirements, interruption and recovery behaviour, zero filing-body/CompanyFacts/Frames/outcome access, the six-transition owner gate ladder (T1 contract acceptance, T2 implementation authorization, T3 implementation acceptance, T4 live-operation preflight, T5 separate per-window owner live-operation authorization, T6 controlled execution, then canonical Gate H), and the M3.2B dependency boundary (separately derived plan, budget, and owner ceiling approval after the M3.2A freeze; no inheritance of the M3.2A ceiling); IMPLEMENTATION_AUTHORIZATION NO; NETWORK_AUTHORIZATION NONE; T1 acceptance grants no T2/T3/T4/T5 authority — the contract implements nothing, enables nothing, and contacts no SEC host until each later section-8 transition is separately granted
M3_EVIDENCE_INDEX_STATUS: LIVE — Docs/m3/templates/evidence_index.md is the completed public evidence index (the recording destination named by contract m3_1.md section 6, master plan sections 12.1/12.3 and M3.1 section 30, and the operator runbook); rows EV-M31A-001 through EV-M31B-006 recorded 2026-08-03 covering the rehearsal report and receipt, both request plans, both planning receipts, the owner-signed request budget, and the owner-signed Gate F checklist; digests, types, phases, statuses, dates, and non-sensitive notes only; no private path, identity, or receipt content; the section 8 owner attestation is recorded verbatim (owner Joseph Nihill, 2026-08-03, bound to commit 0334294bd420a829033094080a13e4df900da078 and checklist sha256 34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc); the index vocabulary defines no readiness-token artifact type, so the token is recorded in this ledger and as private evidence only
DECISION_030_STATUS: ACCEPTED — OWNER APPROVED 2026-08-03; outcome GATE_F_STEP_12_OWNER_RULINGS_AND_HYGIENE_REMEDIATION_ACCEPTED; authorizes exactly one proven non-substantive redaction of the section 17 review artifact's clone-provenance path material (pre-redaction sha256 73cb1eacf0fb5e29a8a1c2ea871692068caf3ebdc48cae161d6aef677ba8f3a3 remains the historical identity; sanitized sha256 9c40a82934ec52227202f0160d49fc5acd0e53f61af86d6f53b6e0b26e041fe3 is the current tracked identity; verdict unchanged; history not rewritten; scanner not weakened; no allowlist); rules the three request-budget response-outcome markers permitted and nonblocking with no integer guessed; records M3-L12 GATE-F-FACING REQUIREMENT: SATISFIED with administrative closure deferred to the later M3.1 acceptance and checkpoint sequence; records D023-O1: LATENT FAIL-CLOSED REFERRAL CONDITION — NONBLOCKING UNLESS TRIGGERED; signs no checklist, emits no token, and grants no network, Gate F, or M3.2 authority
DECISION_026_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; outcome MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED; controls formal closeout and completion tags; grants no Milestone 3 authority
DECISION_027_STATUS: v0.2; ACCEPTED — OWNER APPROVED 2026-07-31; outcome M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED; controls the accepted Milestone 3 master plan as narrowly corrected by accepted Decision 028; grants no implementation authority
DECISION_029_STATUS: ACCEPTED — OWNER APPROVED 2026-08-02; outcome M3_1_REHEARSAL_COMPLETENESS_AND_REASON_SEMANTICS_ACCEPTED; narrowly supersedes two Decision 028 clauses only; controls the per-route full-path A_reachable witness (a zero U never waives it), the rehearsal-only manifest-resolution fixture, the single code OFFLINE_REHEARSAL_SCENARIO_MISMATCH (integrity, blocks_release true, requires_manual_review false by owner ruling), the four-predicate M3.1A token gate, and the first durable section 17 review artifact; changes no receipt schema field or digest preimage; creates no migration; grants no network authority and no tag
DECISION_028_STATUS: ACCEPTED — OWNER APPROVED 2026-08-01; outcome M3_1_READINESS_CORRECTIONS_ACCEPTED; independent rereview PASS; records planner-v2, corrected A1-A12, two future reason codes, receipt-v2, budget, ceiling, recovery-ownership, and M3-L11 rulings; grants no implementation or network authority
DECISION_051_STATUS: ACCEPTED — OWNER APPROVED 2026-08-08; outcome M3_2_POST_T5_REMEDIATION_GOVERNANCE_RECORDED; records the interrupted-T5 facts and owner adjudication; accepts exactly one consumed physical attempt under ceiling 801 with total headroom 800 and bulk-route headroom 5; accepts exact durable evidence before the full-A_reachable ambiguity fallback; adopts pre-send durable ops_retrieval_attempts reservation for future sends without historical backfill; owner-approves the later bounded remediation architecture of the O(n²) archive-path fix, pre-send durable attempt ledger, scoped SIGTERM handling, and explicit receiptless inspection mode only, while withholding implementation until a separate exact packet; preserves the old run as UNDETERMINED and never resumable, with eventual stopped closure requiring separate operational-mutation authority; preserves Decision 050's predecessor-receipt requirement for any continuation and grants receiptless inspection no SAFE, resume, repair, adoption, reconciliation, receipt construction, or mutation authority; requires implementation validation and one fresh independent no-subagent rereview before any later live ruling; grants no network, SEC request, new live invocation, resume, T6, M3.2B, Gate H, state mutation, stale-lease clear, attempt-row backfill, consumed-count mutation, receipt creation, tag, or implementation in this recording stage
DECISION_052_STATUS: ACCEPTED — OWNER APPROVED 2026-08-08; outcome M3_2_POST_T5_REMEDIATION_ACCEPTED_AND_PUBLISHED; the owner determination was issued as the Decision 052 recording packet itself and carries NO separately named OWNER_DECISION_052 instrument token, and none is invented; accepts the corrected post-T5 remediation candidate at implementation commit 47de0738f836958e86e31557b24834fd4f1a3436 plus the separate accounting-correction commit 7dad4231650f5699ded3e8a550d14633d0372f82 (tree 53d5342e753c7c33fdca9222a2e70115ff3234c5), full accepted diff from 1e36a41 sha256 a2ad82c8e4e440398fcd62a01c8ea6a95a9f9b458d6ce8f7d05bc6f07bbb3d9b, across an exact eight-path delta inside the Decision 051 four-production/five-test maximum, the acceptance being SHA-, tree-, and hash-specific; records the correction as a transparent separate commit expressly instead of an amend, rebase, squash, or history rewrite; accepts the fresh independent no-subagent rereview M3_2_POST_T5_REMEDIATION_INDEPENDENT_REREVIEW_PASS with BLOCKER 0, MAJOR 0, MINOR 2, artifact Docs/m3/reviews/m3_2_post_t5_remediation_independent_rereview.md sha256 7234ef37a1b8be8e1f8f23ba7debcfcd0373b6123cfafc723723feb0b2990bff at review commit e91b8fecfe7d1ac586b4a9da0e502e65571217c8, the artifact being advisory and accepting nothing; accepts all four Decision 051 section 7 production changes as implemented on 20,192 randomized archive differential cases with zero divergence over 296 end-to-end archives with ordered lineage preserved, mutation evidence of 20 mutations with 18 killed, one provably equivalent, and one narrow test gap, and validation of targeted 601 passed, SEC transport 123 passed, full suite 3315 passed and 1 skipped, with ruff, format-check, mypy, sqlite-check, secrets, hygiene, and context all passing; accepts counterexample A resolving to 2 and counterexample B to 1 and never 6, with the historical empty-ledger incident unchanged at 1 of 801, UNDETERMINED, and non-resumable, and no ledger backfill; records that Decision 051 section 11 item 4's two-run real-archive evidence was NOT re-run because the private path was undisclosed, that the accepted 43.1 and 45.2-second measurements stand, and that the reviewer's equivalent-scale synthetic evidence may never be cited as real-archive evidence; accepts MINOR F1 and MINOR F2 as documented nonblocking limitations without a third correction loop and records observation O1 as a mandatory later live-readiness obligation, carried as new ACTIVE entries M3-L14, M3-L15, and M3-L16, with O2/O3/O4 recorded at section 10 and creating no register entry; exhausts Decision 051 implementation authority; preserves Decision 050 section 8's predecessor-receipt requirement and Decision 051 sections 8-9's receiptless and no-resume boundaries unchanged; grants no operational-state, lease, receipt, attempt-backfill, run-closure, resume, retry, replacement, clean-run, network, SEC, new live invocation, T6, M3.2B, or Gate H authority, claims no live readiness, and creates no tag
M3_2_POST_T5_REMEDIATION_STATUS: ACCEPTED AND COMPLETE — PUBLISHED (architecture and maximum envelope owner-approved by accepted Decision 051, 2026-08-08, outcome M3_2_POST_T5_REMEDIATION_GOVERNANCE_RECORDED; implemented at 47de0738f836958e86e31557b24834fd4f1a3436 and corrected at 7dad4231650f5699ded3e8a550d14633d0372f82, tree 53d5342e753c7c33fdca9222a2e70115ff3234c5, on the published Decision 051 baseline and parent 1e36a41c6fa67e552f8687414f8f33898ed1aca2; accepted and published by accepted Decision 052, 2026-08-08, outcome M3_2_POST_T5_REMEDIATION_ACCEPTED_AND_PUBLISHED); accepted file hashes acquisition.py a108c18c9e8702a07806c0b933bf5f11adbe2037f4198ca8e1e6c31a9e0e2190, recovery.py 1f7a8fce4ab166fcd3f828092abc8425424b20862e10421a887601522f4ca309, test_m3_acquisition.py 44c017e68da6ea40451c183825b62e4faa66e9406b7ebaf2dbe6041b0ede82f0, test_m3_recovery.py bd17a6fafe174628fbc4c72cc697b6e753f971d68cb0f5300ca3c8a15f42d029; exact eight-path delta - sec/archive.py, m3/acquisition.py, m3/recovery.py, cli.py, tests/unit/test_sec_archive.py, tests/unit/test_m3_acquisition.py, tests/unit/test_m3_recovery.py, tests/integration/test_m3_cli.py - with tests/unit/test_m3_recover.py unneeded and unchanged and tests/integration/test_no_network.py byte-identical and passing; no migration, receipt module, raw store, observation catalog, storage catalog, HTTP client, response policy, configuration, reason code, parser version, dependency, CI, script, evidence index, or governance byte changed; Decision 051 implementation authority EXHAUSTED and no third correction loop authorized
M3_L14_M3_L15_M3_L16_STATUS: ACTIVE — three new limitations recorded by accepted Decision 052, 2026-08-08, none discharged. M3-L14 carries rereview finding F1: receiptless ledger-coverage cardinality is evaluated independently per manifest, so one reservation can cover multiple owned same-URL segments - measured 1 reservation plus 2 owned segments reporting 1/UNSAFE rather than the durable floor 2/UNDETERMINED; it is absent from the real incident whose ledger is empty, unreachable on the governed reserve-before-send path as currently constructed, and can never authorize continuation because receiptless mode never returns SAFE; hard standing condition - before receiptless accounting over a NON-EMPTY ledger is ever relied on as an owner baseline, either correct reservation consumption to one-reservation-per-segment or fail such unmatched cardinality to UNDETERMINED. M3-L15 carries finding F2: second-SIGTERM suppression is implemented and was directly verified by process-level fault injection but no regression test guards it; a deferred one-test gap, not a production defect, and the accepted stage is not reopened for it. M3-L16 carries observation O1: no non-resume clean-run carry-in interface exists for the historical consumed baseline of 1; it is outside Decision 051's four-change scope and is not a defect in the accepted candidate, but it BLOCKS ANY LATER CLEAN-RUN OR LIVE AUTHORIZATION - no clean new run may be authorized until an exact owner-approved carry-in mechanism is available and validated, and no record or session may claim live readiness. Decision 052's further nonblocking observations O2, O3, and O4 are recorded at Decision 052 section 10 and create no register entry. Accepted Decision 053, 2026-08-08, leaves all three entries ACTIVE and byte-unchanged - it creates no limitations-register entry, discharges nothing, and neither designs nor implements any M3-L16 carry-in mechanism; the M3-L16 discovery from the closure work is useful planning evidence only. Accepted Decision 054, 2026-08-08, likewise leaves all three entries ACTIVE and byte-unchanged: accepting the completed one-time interrupted-run closure discharges nothing, creates no register entry, and neither designs nor implements an M3-L16 consumed-baseline carry-in mechanism, and M3-L16 continues to block every clean-run and live authorization. Accepted Decision 055, 2026-08-08, then SELECTS the architecture for M3-L14 and M3-L16 and authorizes one bounded OFFLINE sixteen-path implementation candidate, and updates only the status and authority text of those two entries - M3-L15 is preserved BYTE-FOR-BYTE and no entry closes. M3-L14 now reads ACTIVE - ARCHITECTURE SELECTED, IMPLEMENTATION AUTHORIZED, NOT CLOSED on the fail-closed global one-to-one reservation-consumption rule, under which a durable reservation may satisfy at most one owned receiptless lineage segment and any unmatched or multiply matchable cardinality, duplicate reuse, source/URL/run mismatch, leftover contradiction, or inability to establish an exact bijection returns UNDETERMINED, so the measured 1-reservation/2-owned-segment counterexample must return UNDETERMINED rather than 1/UNSAFE. M3-L16 now reads ACTIVE - BLOCKS LATER LIVE AUTHORIZATION; ARCHITECTURE SELECTED, IMPLEMENTATION AUTHORIZED, NOT CLOSED on Decision 055 rulings 055-A, 055-B, 055-C, and 055-E - ceiling 801 unchanged with historical seed H = 1 and no 802/additive/shadow/reset ceiling and no pre-run fit gate; one clean-root carry-in interface that is NEVER resume, refuses coexistence with --resume-from, is carried by canonical JSON under schema m3-carry-in-authority/1.0, is identified by the SHA-256 of its exact canonical bytes with no circular self-hash field, is validated before transport construction, and is consumed exactly once by a deterministic ops_checkpoints primary key inside the same existing BEGIN IMMEDIATE run-registration transaction with NO migration, all-or-nothing and burned even on a later pre-wire failure with no automatic reissue; writer receipt schema m3-execution-receipt/3.0 with version dispatch, byte-unchanged and mixed-chain-usable 2.0 receipts, a carry_in_authority_sha256 required only on a clean carry-in root, and a chain walker adding the root carry-in exactly once; and Path B, under which a separately authorized offline one-time VERIFIED orphan adoption must precede any clean carry-in run and is neither designed in executable detail nor performed by Decision 055. Selecting an architecture is NOT closing an entry: both still require the implementation, its non-vacuous tests, full validation, a fresh independent Opus 5 Max non-author review, and a separate owner closure act, and M3-L16 additionally requires the accepted orphan adoption. The next authorized action CLAUDE_M3_2_DECISION_055_OFFLINE_IMPLEMENTATION_PACKET is the bounded OFFLINE implementation only; it does not self-execute and grants no operational-state, orphan-adoption, transport-construction, network, SEC, or live authority - authorization is not implementation, implementation is not acceptance, and none of them discharges M3-L14 or M3-L16
DECISION_053_STATUS: ACCEPTED — OWNER AUTHORIZATION RECORDED 2026-08-08; outcome M3_2_INTERRUPTED_RUN_CLOSURE_PROCEDURE_AUTHORIZED; the owner determination was issued as the Decision 053 recording packet itself and carries NO separately named OWNER_DECISION_053 instrument token, and none is invented; records six owner-verified repository observations at baseline 628087b82bc3cfa356166e6f9cba076f7154ac17 - CatalogWriter holds a process-lifetime fcntl.flock whose kernel release on process death leaves the persisted JSON state="held" as stale metadata rather than an active time-based ownership claim; ordinary acquisition opens the existing lease path under LOCK_EX|LOCK_NB and overwrites the stale payload in place while ordinary release records state="released", so no deletion, clearing, unlink, expiry takeover, or manual lease act is needed or permitted; prepare_operational_catalog is prohibited for this closure because it calls migrations and seeding and would rewrite reference-table rows including reference_policy_versions.recorded_at_utc; finish_acquisition_run is under-constrained for a one-time irreversible disposition, enforcing no rowcount, job kind, prior state, or null prior finish time; no current supported public CLI or API performs only the closure and the two existing live call sites both occur after transport construction; and the historical accepted facts are unchanged at 1 of 801 consumed, zero historical ops_retrieval_attempts rows, no terminating receipt, recovery UNDETERMINED, permanently non-resumable, eventual truthful job state stopped; rules that a permanent production CLI/API or source change is NOT required for exactly one historical disposition and would add unnecessary durable operator surface, so the later execution uses one ephemeral, hash-recorded, one-time operator procedure outside the repository that imports and uses the accepted CatalogWriter and its batch() transaction and therefore the normal OS-lock and writer lifecycle, and calls none of prepare_operational_catalog, migrate(), seed_reference_data(), finish_acquisition_run, any live-acquisition entry point, or any transport constructor; fixes the fail-closed selection predicates inside one BEGIN IMMEDIATE writer transaction, the same row-state predicates restated in the single conditional UPDATE with cursor.rowcount == 1, the only three intended column effects on exactly one row, the fixed public closure detail text, and the lease-inode-unchanged and final-released boundary with ordinary WAL/SHM churn allowed; fixes the preflight, eleven-case synthetic-rehearsal, and postcondition evidence contract the later packet must impose; disposes closure findings F-1 and F-2 as MAJOR accepted and resolved architecturally, F-4 as a MAJOR observation with the permanent surface declined as unnecessary, F-3 as a MAJOR planning constraint for M3-L16 accepted only as a later design constraint and not acted on here, F-5 and F-6 as MINOR planning observations, and F-7 as a deferred OPTIMIZATION with locking unaltered, creating no limitations-register entry; authorizes exactly three governance paths, one governance commit Authorize M3.2 interrupted-run closure procedure, one normal fast-forward push, and no tag; grants NO private-evidence read, NO real catalog open even read-only, NO real closure, NO operational-state mutation, NO production or test implementation, and NO lease, receipt, ledger-backfill, orphan, resume, retry, replacement, clean-run, network, SEC, new live invocation, T6, M3.2B, or Gate H authority, and claims no live readiness
DECISION_054_STATUS: ACCEPTED — OWNER APPROVED 2026-08-08; outcome M3_2_INTERRUPTED_RUN_CLOSURE_ACCEPTED; the owner determination was issued as the Decision 054 recording packet itself and carries NO separately named OWNER_DECISION_054 instrument token, and none is invented; GOVERNANCE RECORDING ONLY - it performs no operational mutation, no live acquisition, and no SEC action, and the mutation it accepts happened earlier under the separate Decision 053 execution packet; accepts that one-time OFFLINE closure execution as PASS and reconciles the repository's intentionally stale pre-execution running / not-executed statements to the owner-verified truth stopped, those statements having been accurate when written and remaining historical rather than wrong because private operational state is not self-recording; accepts every Decision 053 section 7.1 preflight gate as passed at migration head 0013 contiguous 0001-0013 with quick_check and integrity_check ok and foreign_key_check 0 before and after, exactly one candidate row against one total job row catalog-wide, zero attempt and zero event rows for the target, no live writer holding the OS lock, and the private catalog, lock directory, and job id resolved without printing or committing any private path, identifier, identity value, or raw body, with independent corroboration that the job start precedes the single accepted physical SEC attempt by 68.773 seconds and the raw lineage records attempts=1, HTTP 200, zero redirect hops, and stored_new; accepts 11 of 11 required section 7.2 synthetic cases PASS against disposable fixtures carrying a decoy row matching predicates 2-5 proven untouched, plus an AST proof of 3 SQL statements with exactly 1 mutating and zero references to prepare_operational_catalog, migrate, seed_reference_data, finish_acquisition_run, any live-acquisition entry point, transport constructor, or recovery mutation surface, and a sys audit hook hard-blocking socket.connect, getaddrinfo, bind, and sendto throughout the real run; accepts the real transaction as committed through the accepted CatalogWriter and one BEGIN IMMEDIATE batch() transaction importing only CatalogWriter and utc_now, with one conditional UPDATE restating the row-state predicates in its own WHERE, cursor.rowcount exactly 1, and exactly three columns of exactly one historical M3.2A row changed - job_state running to stopped, finished_at_utc NULL to one new UTC instant, and detail to the fixed owner closure text at sha256 2065fb487c5b47c4820313e3cd9cb5c2faf5be36889c455394b495008df563ea to e787286044080627d2267b96400321428e5539593866234a41fc60bda5724476, 222 bytes and byte-exact to Decision 053 section 6.4 - with job_id, job_kind, stage, and started_at_utc unchanged and the job id never recorded in plaintext; accepts the blast radius of 1 of 84 user tables changed (ops_ingestion_jobs) with 83 unchanged and no row-count change in any table, attempt, event, raw-object, and observation counts all 0 to 0, governed inventories byte-identical including raw at 2 files and 1,556,243,994 bytes, catalog sha256 c4f2215866c953384c3e573211afe8a35c43080552e4cc58cfb96d7261e3e421 to 31b65e7132e65ae483afb294730f2ed2439ca3c8a2f53ee2e8fb50200034cb5b at unchanged size 1,245,184 bytes, the lease present at an unchanged privately recorded inode at mode 0600 with final state released through the ordinary acquire/release cycle and no deletion, clearing, unlink, replacement, manual edit, or expiry takeover, ordinary WAL/SHM checkpointing permitted, integrity gates passing, the repository clean and byte-identical, and no receipt creation or reconstruction, attempt insertion, consumed-count mutation, orphan adoption, quarantine, reconciliation, raw or lineage mutation, or network, DNS, or SEC action; accepts the owner's independent reverification of the private manifest and its four entries, the 11/11 synthetic record, the table-by-table comparison, and a byte-identical disposable immutable read-only catalog copy containing exactly one ingestion job now stopped with non-null finish time and the byte-exact closure detail, zero attempt rows, zero job events, quick and integrity checks ok, and zero foreign-key violations, with the original catalog hash unchanged by that verification; records the private bundle identities manifest 9aa1582e9cc6aba646dcbe36f01476d4b731af9d37847e51dd204b82706cbade, closure_evidence.md dd3e25ca00232b4564642b17c242d536e23a977b49bb029afedfb04bafcf6c77 at 5,344 bytes, state_before.json b1404e6d14e76889dd059d00c4a76e63848efd5d903d4829c0851124dca1a498 at 14,635 bytes, state_after.json 56df1f0bd117e66d1c324d5a6149300d2b6b59629ad5f1962a37dc16059d2fb2 at 14,108 bytes, and synthetic_results.json babddcb8a1b59cbd105a32403f06ae8b52253058f7e569649eda72f19956c214 at 1,988 bytes, all five mode 0600 with the manifest verifying over four safe relative entries, all recomputed and matched, the evidence remaining outside Git and unaltered; records as an OBSERVATION and not a defect that the four ephemeral procedure artifacts are identified by sha256 but their source was correctly destroyed with the mktemp scratch directory because Decision 053 section 7.1 required the hashes and a sanitized protocol rather than source preservation and section 5 declined a permanent surface by design, so those hashes attest that a byte sequence ran but do not permit re-deriving it and no reproducibility may be invented, creating no limitations-register entry; records that no BLOCKER, MAJOR, or MINOR finding remains; exhausts Decision 053's one-time execution authority as EXHAUSTED and IRREVERSIBLE with no repeat closure authorized; preserves recovery UNDETERMINED, no terminating receipt created or reconstructed, zero historical ops_retrieval_attempts rows with no backfill, consumption 1 of 801 with total headroom 800 and bulk-route accounting headroom 5, and the old run never resumable, stopped being neither completed nor a resolved orphan nor a discharged recovery condition nor continuation eligibility; leaves M3-L14, M3-L15, and M3-L16 ACTIVE and byte-unchanged with M3-L16 continuing to block every clean-run and live authorization; authorizes exactly three governance paths, one governance commit Accept M3.2 interrupted-run closure, one normal fast-forward push, and no tag; grants NO further operational-state mutation, repeat closure, resume, retry, replacement, receipt, attempt-backfill, consumed-count, lease, orphan, production or test implementation, clean-run, network, SEC, new live invocation, T6, M3.2B, or Gate H authority, and claims no live readiness
M3_2_INTERRUPTED_RUN_CLOSURE_STATUS: EXECUTED, COMPLETE, AND ACCEPTED — HISTORICAL_JOB_STATE_NOW stopped (procedure architecture and boundaries fixed by accepted Decision 053, 2026-08-08, outcome M3_2_INTERRUPTED_RUN_CLOSURE_PROCEDURE_AUTHORIZED; executed exactly once offline under the separate CLAUDE_M3_2_INTERRUPTED_RUN_CLOSURE_EXECUTION_PACKET; accepted as PASS by accepted Decision 054, 2026-08-08, outcome M3_2_INTERRUPTED_RUN_CLOSURE_ACCEPTED, which satisfies Decision 051 section 9's requirement for a separate offline state disposition). Supersedes, as a statement of CURRENT state only, every earlier running / not-executed statement in this file and in Decision 053 sections 1 and 11 - those were accurate when written and remain historical, not wrong, because private operational state is not self-recording. Accepted evidence: all Decision 053 section 7.1 preflight gates passed at migration head 0013 contiguous 0001-0013, quick_check and integrity_check ok and foreign_key_check 0 before and after, exactly one candidate row against one total job row catalog-wide, zero attempt and zero event rows for the target, and no live writer holding the OS lock; 11 of 11 section 7.2 synthetic cases PASS against disposable fixtures carrying a decoy row matching predicates 2-5 proven untouched; AST proof of 3 SQL statements with exactly 1 mutating and zero references to any prohibited helper, live-acquisition entry point, transport constructor, or recovery mutation surface; a sys audit hook hard-blocking socket calls throughout the real run; one BEGIN IMMEDIATE CatalogWriter batch() transaction with one conditional UPDATE restating the row-state predicates and cursor.rowcount exactly 1; exactly three columns of exactly one row changed - job_state running to stopped, finished_at_utc NULL to one new UTC instant, detail to the byte-exact 222-byte Decision 053 section 6.4 closure text (sha256 2065fb48 to e7872860) - with job_id, job_kind, stage, and started_at_utc unchanged and the job id never recorded in plaintext; 1 of 84 user tables changed (ops_ingestion_jobs), 83 unchanged, no row-count change in any table, attempt, event, raw-object, and observation counts all 0 to 0; governed inventories byte-identical including raw at 2 files and 1,556,243,994 bytes; catalog sha256 c4f22158 to 31b65e71 at unchanged size 1,245,184 bytes; lease present at an unchanged privately recorded inode at mode 0600, final state released via the ordinary acquire/release cycle with no deletion, clearing, unlink, replacement, manual edit, or expiry takeover; integrity gates passing; repository clean and byte-identical; and no receipt creation or reconstruction, attempt insertion, consumed-count mutation, orphan adoption, quarantine, reconciliation, raw or lineage mutation, or network, DNS, or SEC action. The owner independently reverified the private manifest 9aa1582e over four safe relative entries with all five files mode 0600, the 11/11 synthetic record, the table-by-table comparison, and a byte-identical disposable immutable read-only catalog copy - exactly one ingestion job now stopped with non-null finish time and the byte-exact closure detail, zero attempt rows, zero job events, quick and integrity checks ok, zero foreign-key violations - with the original catalog hash unchanged by that verification. OBSERVATION, not a defect: the four ephemeral procedure artifacts are identified by sha256 but their source was correctly destroyed with the mktemp scratch directory, since Decision 053 required the hashes and a sanitized protocol rather than source preservation and declined a permanent surface by design - the hashes attest a byte sequence ran but do not permit re-deriving it, and no reproducibility may be invented; this creates no limitations-register entry. No BLOCKER, MAJOR, or MINOR finding remains. A truthful terminal state is NOT a resolution: recovery remains UNDETERMINED, there is no terminating receipt, historical ops_retrieval_attempts rows remain 0 with no backfill, accepted consumption remains 1 of 801 with total headroom 800 and bulk-route accounting headroom 5, and the old run is NEVER resumable - stopped is not completed, not a resolved orphan, not a discharged recovery condition, and not continuation eligibility. Decision 053's one-time execution authority is EXHAUSTED, the closure is IRREVERSIBLE, and no repeat closure or further operational mutation is authorized. No permanent production or test surface was created. The exact next authorized action is CLAUDE_M3_2_M3_L16_CARRY_IN_ARCHITECTURE_DISCOVERY_PACKET
DECISION_055_STATUS: ACCEPTED — OWNER APPROVED 2026-08-08; outcome M3_2_CARRY_IN_ARCHITECTURE_ACCEPTED_AND_OFFLINE_IMPLEMENTATION_AUTHORIZED; the owner's approval is verbatim "approve Decision 055." and the substance was issued as the Decision 055 recording packet itself, carrying NO separately named OWNER_DECISION_055 instrument token, and none is invented; GOVERNANCE RECORDING ONLY - it performs no implementation, no operational-state mutation, and no SEC action, opens no operational catalog or private evidence even read-only, and accepts NO candidate and closes NO limitation; accepts the four facts the completed read-only validation independently established - consumption exactly 1 of cumulative ceiling 801, that attempt attributable to sec_bulk_submissions, historical ops_retrieval_attempts rows equal 0, and recovery remaining UNDETERMINED and never SAFE because of the raw-store/catalog ORPHAN MISMATCH rather than ambiguous attempt evidence - so remaining total headroom is 800 and bulk-route headroom 5 as accounting and reporting only and never a runtime refusal, the old run is stopped and permanently non-resumable, no terminating receipt exists, and the validation changed nothing, contacted nothing, and left the baseline intact; ruling 055-A keeps the cumulative M3.2A ceiling at exactly 801 with historical seed H = 1 and future cumulative consumption H plus new durable reservations, permits NO 802 ceiling, additive ceiling, shadow ceiling, reset, or reinterpretation, leaves the frozen request plan 19be7bdc and its full 75-logical-request plan unchanged, constructs the global PhysicalAttemptCeiling with approved_ceiling 801 and consumed 1 for the authorized clean carry-in root, permits the global ceiling to lawfully stop the run at cumulative 801 with planned work remaining with NO pre-run fit gate and no false promise that worst-case retries fit, and makes route attribution to sec_bulk_submissions evidence and reporting only with NO per-route runtime refusal and NO change to sec/http_client.py; ruling 055-B adds one explicit clean-root carry-in interface that is NEVER resume and must refuse coexistence with --resume-from, whose authority artifact has canonical JSON bytes under schema m3-carry-in-authority/1.0 binding window M3.2A, the frozen request-plan SHA-256, cumulative ceiling 801, historical seed 1, the route allocation of that one attempt to sec_bulk_submissions, the Decision 055 identity, the authorized new run id, and the later accepted orphan-adoption decision identity and evidence identity, with no secret, identity header, response body, or private absolute path, whose external identity is the SHA-256 of its exact canonical bytes with NO circular self-hash field, taken by the CLI from the governed evidence root by a safe relative path with the authorized new run id coming from the artifact and replacing random generation for that invocation, parsed and canonicalized and hashed and validated BEFORE transport construction, and consumed EXACTLY ONCE by inserting a deterministic ops_checkpoints primary key keyed by its SHA-256 in the SAME existing BEGIN IMMEDIATE transaction as new-run registration with NO migration, refusing before transport on replay, run-id mismatch, plan/window/ceiling/seed/route mismatch, malformed or noncanonical bytes, a conflicting resume, or a missing binding, with an all-or-nothing registration transaction and the authority remaining BURNED even if a later pre-wire failure occurs after commit with zero attempts and NO automatic reissue or retry, and a checkpoint value preserving enough canonical safe data for later receipt and catalog cross-checks; ruling 055-C unfreezes the receipt schema only for this bounded change to writer schema m3-execution-receipt/3.0, keeps existing 2.0 receipts byte-unchanged, valid, readable, and usable in mixed-version chains through version dispatch and never rewrites an old receipt, redefines consumed_request_count_carried_forward in 3.0 as cumulative physical attempts before the current invocation - required for resume and for a clean carry-in root and omitted for an ordinary zero-baseline fresh root - adds carry_in_authority_sha256 required ONLY on a clean carry-in root with no predecessor and a nonzero carried-forward count and absent on ordinary roots and resume receipts with the root retaining it for the chain, makes a clean carry-in root omit recovery_predecessor_receipt_id, carry 1, name the authority hash, and record actual_physical_attempt_count as current-invocation wire attempts N only, validates carried-forward plus actual as no greater than the approved ceiling, makes the receipt-chain walker add the root carry-in EXACTLY ONCE as the sum of every receipt actual count plus only the no-predecessor root carried-forward count and never N alone and never double-counted, requires show-scope and every recovery/continuation consumer to agree with that walker, and makes the catalog checkpoint and root receipt mutually cross-check with a missing or mismatched authority or carry-in becoming UNDETERMINED and unable to authorize continuation; ruling 055-D pre-resolves M3-L14 architecturally by a global one-to-one reservation-consumption rule across all owned receiptless lineage segments in which a durable reservation may satisfy AT MOST ONE segment and any unmatched or multiply matchable cardinality, duplicate reservation reuse, source/URL/run mismatch, leftover contradiction, or inability to establish an exact bijection returns UNDETERMINED, requires the existing one-reservation-plus-two-owned-same-URL-segment counterexample to produce UNDETERMINED and never consumed count 1 with UNSAFE, keeps receiptless inspection inspection-only and never SAFE and never continuation-authorizing, and leaves M3-L14 ACTIVE until implementation, non-vacuous tests, full validation, fresh independent review, and separate owner closure; ruling 055-E chooses Path B for the historical orphan - a separately authorized, offline, one-time, VERIFIED orphan adoption before any clean carry-in run - which Decision 055 does NOT authorize, design in executable detail, or perform, authorizing NO adoption, quarantine, reconciliation, catalog/raw/lineage mutation, or operational checkpoint now, requiring a later owner instrument to define the exact procedure, execute it once offline, independently verify it, record acceptance, and leave ZERO unresolved historical orphan mismatch before a carry-in artifact may be minted or consumed, requiring the carry-in authority to bind that later adoption decision and evidence identities, and prohibiting clean run, transport construction, network, SEC, and live readiness until then; ruling 055-F authorizes one bounded OFFLINE implementation candidate on at most SIXTEEN paths with NO seventeenth - production src/disclosure_drift/cli.py, src/disclosure_drift/m3/acquisition.py, src/disclosure_drift/m3/recovery.py, src/disclosure_drift/m3/receipt.py; normative and operator documentation Milestones/contracts/m3_2.md, Docs/m3/execution_receipt_spec.md, Docs/m3/templates/gate_h_checklist.md, Docs/m3/operator_runbook.md, Docs/m3/templates/interrupted_run_recovery.md, Docs/sec_data_dictionary.md; and tests tests/unit/test_m3_acquisition.py, tests/unit/test_m3_recovery.py, tests/unit/test_m3_recover.py, tests/unit/test_m3_receipt.py, tests/unit/test_request_ceiling.py, tests/integration/test_m3_cli.py - permitting EXACTLY ONE local candidate commit with exact subject "Implement M3.2 carry-in authority and receipt v3" with NO push and NO tag, and requiring later separate owner acts for candidate acceptance, M3-L14 closure, M3-L16 closure, orphan adoption, network, live invocation, T6, M3.2B, and Gate H; ruling 055-G requires targeted tests and non-vacuous positive controls for baseline 1 plus N reservations equalling cumulative 1 plus N, current-run attempt 800 reaching cumulative 801 with the next physical attempt refused without increment, a sixth future bulk attempt NOT refused by a new per-route guard with the global ceiling remaining sole runtime enforcement, artifact replay and all mismatches refusing before transport-factory invocation, atomic rollback between checkpoint insertion and run registration leaving NEITHER row, burn-before-wire remaining consumed and never auto-reissued, v2.0 receipts remaining valid and readable with exact v3.0 field conditions, the root carry-in counted once through mixed-version chains with show-scope agreeing, checkpoint/receipt mismatch becoming UNDETERMINED, the M3-L14 counterexample becoming UNDETERMINED with that test FAILING against current behaviour, prohibited-path nonchange, and network containment, plus targeted validation while editing and the full authorized gate once at stage end (Ruff lint, Ruff format check, mypy src, full pytest including the sec transport test, make sqlite-check, make secrets, make hygiene, make context), then a fresh Claude Opus 5 Max non-author session independently reviewing the frozen candidate WITHOUT modifying it; ruling 055-H narrowly supersedes ONLY four things - contract section 12 where it recognizes only predecessor-receipt carry-forward by adding the one-use non-resume carry-in root, the prior clauses freezing receipt.py and receipt schema 2.0 solely for backward-compatible schema 3.0 and version dispatch, the prior withholding of implementation solely for the sixteen-path offline candidate, and M3-L14's unresolved owner choice by selecting the fail-closed one-to-one cardinality rule - leaving all other accepted authority binding including ceiling 801, old-run permanent no-resume, no automatic continuation, fail-closed recovery, evidence preservation, deterministic behaviour, and owner-gated live operations, not widening Decision 051's narrow supersession of Decision 032 F3 and Decision 040 section 7, and keeping Decision 050 section 8's predecessor-receipt requirement fully binding for every resume since the carry-in root is not a resume; authorizes exactly four governance paths - this record, the registry, Milestones/STATUS.md, and Docs/m3/limitations_register.md for M3-L14 and M3-L16 status and authority text only with M3-L15 preserved BYTE-FOR-BYTE - with no fifth and expressly not Docs/decision_index.md, one governance commit "Authorize M3.2 carry-in implementation", one normal fast-forward push, and no tag; grants NO implementation performed here, NO operational-state mutation, NO orphan adoption, NO transport construction, NO network or SEC contact, NO resume, retry, replacement, or clean run, NO T6, M3.2B, or Gate H authority, and claims NO live readiness
M3_2_CARRY_IN_ARCHITECTURE_STATUS: ACCEPTED AND BINDING; OFFLINE IMPLEMENTATION AUTHORIZED; NOT IMPLEMENTED, NOT REVIEWED, NOT ACCEPTED — accepted Decision 055, 2026-08-08, outcome M3_2_CARRY_IN_ARCHITECTURE_ACCEPTED_AND_OFFLINE_IMPLEMENTATION_AUTHORIZED, on the owner's verbatim approval "approve Decision 055." The preceding CLAUDE_M3_2_M3_L16_CARRY_IN_ARCHITECTURE_DISCOVERY_PACKET was issued and completed as READ-ONLY validation that changed nothing, performed no network or SEC action, and left the repository at the required baseline; it independently established, and Decision 055 accepts, that consumption is exactly 1 of cumulative ceiling 801, that the attempt is attributable to sec_bulk_submissions, that historical ops_retrieval_attempts rows equal 0, and that recovery remains UNDETERMINED and never SAFE because of the raw-store/catalog ORPHAN MISMATCH rather than ambiguous attempt evidence. Accepted accounting: historical seed H = 1, remaining total headroom 800, remaining bulk-route headroom 5 as accounting and reporting only and never a runtime refusal, old run stopped and permanently non-resumable, no terminating receipt in existence. Fixed architecture: ceiling exactly 801 with no 802/additive/shadow/reset/reinterpreted ceiling, the frozen plan 19be7bdc and its full 75-logical-request plan unchanged, PhysicalAttemptCeiling constructed with approved_ceiling 801 and consumed 1, the global ceiling free to lawfully stop the run at cumulative 801 with planned work remaining and NO pre-run fit gate, route attribution evidence-and-reporting-only with NO per-route runtime refusal and NO sec/http_client.py change; one clean-root carry-in interface that is NEVER resume and refuses coexistence with --resume-from, carried by canonical JSON under schema m3-carry-in-authority/1.0 with its external identity the SHA-256 of its exact canonical bytes and NO circular self-hash field, supplied from the governed evidence root by a safe relative path, supplying the authorized new run id in place of random generation, validated before transport construction, and consumed EXACTLY ONCE by a deterministic ops_checkpoints primary key inside the SAME existing BEGIN IMMEDIATE run-registration transaction with NO migration, all-or-nothing and BURNED even on a later pre-wire failure with NO automatic reissue; writer receipt schema m3-execution-receipt/3.0 with version dispatch, byte-unchanged, valid, readable, mixed-chain-usable 2.0 receipts that are never rewritten, carry_in_authority_sha256 required only on a clean carry-in root with no predecessor and a nonzero carried-forward count, a clean carry-in root that omits recovery_predecessor_receipt_id, carries 1, names the authority hash, and records actual_physical_attempt_count as current-invocation wire attempts N only, and a chain walker adding the root carry-in EXACTLY ONCE with show-scope and every recovery/continuation consumer agreeing and any checkpoint/receipt mismatch becoming UNDETERMINED; the M3-L14 fail-closed global one-to-one reservation-consumption rule under which the 1-reservation/2-owned-segment counterexample must return UNDETERMINED and never 1/UNSAFE; and Path B, under which a separately authorized offline one-time VERIFIED orphan adoption must precede any clean carry-in run and is neither designed in executable detail nor performed by Decision 055. Authorized next work: ONE bounded OFFLINE implementation candidate on exactly SIXTEEN paths with no seventeenth, ONE local commit "Implement M3.2 carry-in authority and receipt v3" with no push and no tag, twelve mandatory non-vacuous positive controls, the full validation gate, and a fresh Claude Opus 5 Max non-author independent review of the frozen candidate. NOT YET DONE and NOT authorized by Decision 055: the implementation itself, candidate acceptance, M3-L14 closure, M3-L16 closure, the orphan adoption, network, SEC contact, transport construction, a clean run, T6, M3.2B, and Gate H. Live readiness is NOT claimed
DECISION_057_STATUS: ACCEPTED — OWNER APPROVED 2026-08-09; outcome M3_2_ORPHAN_ADOPTION_PROCEDURE_ARCHITECTURE_ACCEPTED; the owner determination was issued as the Decision 057 recording packet itself and carries NO separately named OWNER_DECISION_057 instrument token, and none is invented; the authorizing instruction is the owner's verbatim response to the prior recommendation, "Okay fix the major and run a new review.", which is authority to prepare this governance candidate and its fresh review and is NOT authority for operational execution; GOVERNANCE RECORDING ONLY and EXPLICITLY NON-SELF-EXECUTING - it performs no adoption, no simulation against private state, no operational-state mutation, and no SEC action, opens no operational catalog, data root, raw object, lineage intent, receipt inventory, writer lease, or private evidence even read-only, changes no executable or test byte, and grants NO operational invocation; adjudicates the completed Decision 056 section 10 read-only orphan-adoption architecture discovery and records its central contract assertion - that a successful adoption adds exactly one new row and leaves every other table unchanged - as a CONFIRMED MAJOR ERROR, replaced by the corrected binding contract that the successful path adds one census_source_observations row AND one census_projection_recovery_events row ending resolved, transitions the new observation's projected_to_audit 0 to 1, ATOMICALLY REPLACES audit/sec/census_source_observations.jsonl rather than appending, spans THREE separately committed SQLite transactions (observation INSERT; blocked incident INSERT; final flag-plus-incident-resolution UPDATE), is NOT atomic end to end, has NO source suppressing the incident row after the orphan INSERT, and ends with a final UPDATE that resolves EVERY blocked event for the projection path so a pre-existing blocked event must fail preflight - every one of those facts verified by direct read-only inspection of the committed baseline at observation_catalog.py lines 126, 299, 335, 342, 343, 344, 350, 558-595, 617, 634, 648, 650, 651, 655-671, 676-683, 686, 687, 689-700, 701-710, 1101, 1108-1115, 1116, 1351, 1372-1387, 1400-1411, 1423, 1492, 1514, storage/sqlite.py line 100, storage/catalog.py lines 107, 336, and 338, snapshots.py lines 139-140 and 144, migration 0002 lines 57-58, and migration 0008 lines 56-57, 145, and 445-460; ruling 057-A fixes the corrected two-table, two-row, three-transaction contract; ruling 057-B retains ARCHITECTURE C CORRECTED - one ephemeral, SHA-256-recorded, one-time procedure in mktemp scratch OUTSIDE the repository, using accepted _observation_from_intent UNCHANGED as sole verifier and ONE GUARDED INSERT inside CatalogWriter.batch guarded in-transaction against a duplicate observation_id or relative_storage_path, whose EXACT persisted row is fixed by section 5.1 - enter one CatalogWriter.batch BEGIN IMMEDIATE, reassert BOTH guards on that same connection inside that transaction because the preflight readings are pre-transaction reads and do not discharge them, then and only then capture EXACTLY ONE recorded_at_utc = utc_now(), execute ONE direct INSERT over the accepted OBSERVATION_COLUMNS with values that are EXACTLY ObservationRecorder._row(verified_observation, recorded_at_utc) where verified_observation is the UNMODIFIED verifier return and the tuple is never hand-built, reordered, re-serialized, extended, or partially overridden, and REQUIRE cursor.rowcount == 1 with anything else raising inside the transaction so it rolls back and nothing commits, that check being KEPT IN THE REAL PROCEDURE as defense-in-depth and treated as a DIRECTLY ASSERTED AND EVIDENCED INVARIANT rather than a branch expected to fire, then EXIT the CatalogWriter.batch context and COMMIT transaction 1 before anything else happens - with ObservationRecorder.record itself PROHIBITED because it opens transaction(self.writer.connection) at line 343 and would nest a second BEGIN IMMEDIATE inside CatalogWriter.batch and raise rather than write, so record and _row are cited ONLY as the accepted ROW-SHAPE precedent and never as a surface the procedure invokes, and with both guards being ONE-USE REFUSALS that STOP and refer to the owner rather than UPDATE, INSERT OR REPLACE, INSERT OR IGNORE, upsert, delete, retry, or replay, so NO path in the procedure revises or replaces an existing row; with a MANDATORY subsequent rebuild_audit_projection(connection, destination) call in the SAME authorized process invocation but ONLY AFTER the CatalogWriter.batch context has exited and transaction 1 has committed, NEVER inside the batch - because the rebuild opens its own transactions at lines 686 and 1116 and transaction() issues BEGIN IMMEDIATE unconditionally - and supplying NEITHER census_run_id NOR fault_hook, both keyword-only defaults at lines 638-639, since a supplied census_run_id would enable the census_recovery_states UPDATE that ruling 057-C forbids and fault_hook belongs only to the disposable synthetic suite, NO permanent production surface and NO tracked procedure, and never calling apply_recovery_action, reconcile, _recover_orphan, RawStore.quarantine, RawStore.reconcile, prepare_operational_catalog, migrate, seed_reference_data, or any receipt, checkpoint, run-registration, transport, or live-acquisition function, because _recover_orphan falls through on ANY verifier failure to RawStore.quarantine which MOVES the governed raw object and its lineage intent; ruling 057-C accepts the hardcoded verifier detail "verified adoption after raw promotion and before catalog commit" unchanged, accepts outcome stored_new and the observation_id, retrieved_at_utc, and all identity, hash, and size values exactly from governed lineage and verifier output with nothing supplied, defaulted, corrected, or re-derived EXCEPT recorded_at_utc, which is the SOLE catalog value the PROCEDURE ITSELF generates and the sole newly generated value IN THE OBSERVATION ROW - captured ONCE inside transaction 1 and only after both guards pass, never taken from the lineage intent, a caller argument, an environment value, or a second clock read, and never confused with retrieved_at_utc which comes from the governed intent unchanged; the scope is deliberate, because transactions 2 and 3 generate the LIBRARY-OWNED detected_at_utc, resolved_at_utc, event_id, rebuild_identity, and projection_sha256, none of which is the procedure's to supply or suppress - with every persisted value being EXACTLY the ObservationRecorder._row serialization of the unmodified verifier result plus that one captured instant written over the accepted OBSERVATION_COLUMNS and no column added, dropped, reordered, re-serialized, or overridden, and with projected_to_audit inserted as the literal 0 that _row fixes at line 593 and NOT pre-set to 1, since transaction 3's rebuild is what moves it 0 to 1 and pre-setting it would make that transition unobservable and would falsely satisfy the terminal flag postcondition - the verifier itself supplying only 32 of the 34 columns because SourceObservation carries neither projected_to_audit nor recorded_at_utc; and requires ZERO census_observation_reasons rows, ZERO census_archive_members rows, NO record_recovery_events and NO open_recovery_state call, NO census_recovery_states row, and NO receipt, checkpoint, attempt, ingestion-job, or run-registration row; ruling 057-D fixes an eleven-item CONJUNCTIVE FAIL-CLOSED preflight - accepted repository baseline clean with tracked network false/false and CompanyFacts disabled; migration head 0013 with quick_check, integrity_check, and foreign_key_check clean; historical job stopped, historical ops_retrieval_attempts count zero, no receipt manufactured; exactly one orphan, zero catalog_row_without_object conditions, zero stray lineage intents; audit projection valid BEFORE adoption; ZERO resolution_state='blocked' rows CATALOG-WIDE as a deliberately stronger STRONG OWNER RULING than the code's path-scoped checks at lines 693, 1095, and 1110 because the resolution UPDATE is path-scoped and would silently resolve a pre-existing unrelated incident; no row already holding the target observation_id or relative_storage_path; lineage schema, path, request-identity, registry, storage-representation, hash, and size verification all passing THROUGH _observation_from_intent and not a reimplementation; no live writer holding the OS lock re-verified immediately before the real transaction; the synthetic suite passing FIRST; and the procedure SHA-256 recorded privately before it runs - with private absolute paths, identifiers, identity values, and raw bodies resolved without printing or committing them, and any mismatch, ambiguity, or unavailable proof a STOP before any write; ruling 057-E fixes the exact successful terminal delta - census_source_observations N to N+1, target flag 0 to 1 with ALL flags 1, the target row's persisted tuple EXACTLY ObservationRecorder._row(verified_observation, recorded_at_utc) under OBSERVATION_COLUMNS with its recorded_at_utc equal to the SINGLE instant the PROCEDURE captured in transaction 1 - a postcondition scoped to the observation row and to the procedure's own generation, and expressly NOT a claim that no other instant exists in the run, since a correct rebuild ALSO generates two LIBRARY-OWNED instants, the incident row's detected_at_utc at observation_catalog.py line 1130 and its resolved_at_utc at line 673, both EXPECTED, both REQUIRED to be separately evidenced, and NEITHER required to equal the other nor recorded_at_utc, with inequality among them NEVER a failure, every pre-existing logical row value unchanged, census_projection_recovery_events plus 1 terminal resolved with non-NULL resolved_at_utc and projection_sha256 equal to the new projection file digest, ZERO blocked rows catalog-wide, projection JSONL N to N+1 lines validating with no temporary residue, all other census_* and ops_* row counts and content unchanged, raw object and lineage SHA-256, size, inode, and location unchanged, orphan count 1 to 0, catalog_row_without_object 0, attempts 0, no receipt and no checkpoint, repository unchanged, network still disabled, and the receiptless terminal determination expected UNSAFE SOLELY because no predecessor receipt exists and NEVER because the adoption failed, with the old run permanently non-resumable, UNSAFE never authorizing resumption, SAFE neither expected nor capable of authorizing anything since receiptless inspection is structurally unable to return it, and the CURRENT pre-execution recovery state remaining UNDETERMINED; ruling 057-F classifies fail-closed the six interruption points - before the observation commit is NO-OP; after the observation commit and before the incident insert is ADOPTED, PROJECTION UNRECONCILED; after the blocked incident insert and before the file replace is ADOPTED, RECOVERY BLOCKED; after the file replace and before the directory fsync is ADOPTED, REPLACEMENT NOT PROVEN DURABLE; after the fsync and before the final SQLite update is ADOPTED, FLAGS AND INCIDENT UNRESOLVED; after the final update is CANDIDATE SUCCESS confirmed only by the full terminal check - forbids any claim of end-to-end atomicity while recording that the INSERT transaction and the final rebuild transaction are each locally atomic, forbids claiming successful completion unless EVERY terminal postcondition passes, records that states 2 through 5 are unfinished projection reconciliation rather than adoption failures so the observation must never be re-adopted, and binds points 3, 4, and 5 to the committed fault hooks after_rebuild_temporary_durable_before_replace, after_rebuild_replace_before_directory_fsync, and after_rebuild_directory_fsync_before_catalog_update so each is provable rather than reasoned about; ruling 057-G fixes FIFTEEN non-vacuous synthetic cases against disposable fixtures before the real catalog is touched - healthy fixture with valid projection and zero blocked rows as a positive control reproducing the full terminal delta INCLUDING field-by-field equality of the persisted target tuple with ObservationRecorder._row(verified_observation, recorded_at_utc) under OBSERVATION_COLUMNS, exactly ONE PROCEDURE-captured instant proven to be that row's recorded_at_utc, the TWO library-owned instants separately observed as present and non-NULL with NO equality asserted between them or against recorded_at_utc, and the ACTUAL successful cursor.rowcount asserted directly from the real cursor to be 1 rather than assumed; blocked observed MID-FLIGHT via fault hook proving blocked to resolved rather than inferring it; orphan sorting last; orphan sorting middle and first; pre-existing observation values proven unchanged field by field; negative table assertions for observation reasons, archive members, further recovery events, recovery states, and every ops_* table; verifier failure preserving the object and lineage in place with ZERO writes; duplicate observation_id; duplicate relative_storage_path; two orphans; lock contention; transaction fault; a fault at each of the three projection fault points; a MANDATORY non-vacuous CONTRAST proving a reconcile/quarantine variant would MOVE a disposable fixture object and never the governed real one; and a MANDATORY additive FIFTEENTH case with two distinct limbs - a MUTATION limb, non-vacuous, in which mutating or removing section 5.1's ROW CONSTRUCTION MUST fail the suite, with a hand-built, reordered, or re-serialized tuple, a recorded_at_utc taken from the lineage intent or a caller argument, a SECOND PROCEDURE clock read USED FOR THE OBSERVATION ROW'S recorded_at_utc (scoped to the procedure's own reads, since the library's expected reads must NOT be counted against it), and a projected_to_audit pre-set to 1 each shown to be CAUGHT, plus a nested ObservationRecorder.record call inside CatalogWriter.batch shown to RAISE rather than write; and an ASSERTION limb in which the REAL cursor.rowcount is asserted to be 1 on the successful path and that observed value is evidenced. The blanket non-vacuity rule is corrected accordingly: it binds EVERY behaviourally reachable row-shape, timestamp, flag, and nested-transaction mutation, but the cursor.rowcount == 1 guard is a STATICALLY AND DIRECTLY ASSERTED INVARIANT, not a required negative-mutation demonstration, because under the accepted plain INSERT and schema a permitted insert yields exactly 1 and every other accepted outcome raises before the check is reached - so REMOVING that check CANNOT be caught by a behaviourally non-vacuous mutation, any packet demanding that it be is REFUSED, and what is required instead is that the check STAYS in the real procedure as defense-in-depth and that the actual successful cursor result is asserted and evidenced - cases 1 through 14 being preserved as accepted and NOT renumbered; ruling 057-H requires a private mode-0600 execution bundle and manifest outside Git over safe relative names only, carrying at minimum the accepted Decision 057 commit identity once published, the procedure SHA-256, safe before/after counts, the incident event_id, the detected_condition, detected and resolved UTC instants, projection digests S0 and S1, a safe table-delta summary, raw and lineage before/after hashes, sizes, and inodes WITHOUT private absolute paths, synthetic case results, integrity results, repository/configuration/network assertions, an explicit termination classification, and the transaction-1 captured recorded_at_utc together with the assertions that the persisted target row equalled ObservationRecorder._row under OBSERVATION_COLUMNS and that cursor.rowcount was 1, all recorded as SAFE values never beside a private absolute path or identity value, and NEVER placing private paths, user identity values, .env contents, raw SEC bodies, credentials, or the raw object in Git, and CORRECTS that Decision 055 section 6.1's required carry-in binding is to the EVENTUAL ACCEPTED orphan-adoption decision identity and the ACCEPTED EVIDENCE-MANIFEST SHA-256, NOT to this architecture record; ruling 057-I OVERRIDES the remediation addendum's unbounded "retry to success" recommendation - Decision 057 performs and authorizes no real invocation, the next action after this candidate is its fresh independent non-author review, after a passing review and a separate owner publication ruling a SEPARATE OWNER EXECUTION PACKET is still required, that later packet may authorize EXACTLY ONE REAL process invocation - one that touches the GOVERNED catalog, data root, raw object, or lineage intent - and NO SECOND, attempting BOTH the adoption and one mandatory rebuild_audit_projection call, with the counting stated unambiguously: the mandatory disposable synthetic preflight suite runs BEFORE, OUTSIDE, and WITHOUT ANY ACCESS TO that governed state, is NOT the single real adoption invocation, is NOT counted against it, and is NOT authorized by Decision 057 either, since this record remains architecture-only and makes nothing performable, NO retry loop, auto-retry, auto-resume, automatic relaunch, or "retry until success" is authorized under any failure point, any exception, interruption, uncertainty, or failed postcondition STOPS and refers to the owner, a PROVEN-uncommitted observation INSERT requires NEW owner authority for any later adoption attempt, a committed OR uncertain INSERT means the adoption must NEVER be rerun with only read-only classification permitted and only a separate explicit rebuild-only recovery ruling able to authorize further mutation, and NO manual UPDATE or DELETE of an incident row is authorized under any circumstance; leaves M3-L14 CLOSED and untouched, M3-L15 ACTIVE and BYTE-UNCHANGED, and M3-L16 ACTIVE and BLOCKING with only its current authority, status, mitigation, and closure text updated; authorizes exactly four governance paths - this record, the registry, Milestones/STATUS.md, and Docs/m3/limitations_register.md for M3-L16 text only - with no fifth and expressly not Docs/decision_index.md; RESERVES but does NOT authorize the future governance publication subject "Authorize M3.2 orphan-adoption procedure architecture", records that publication is NOT authorized by the authoring task and has NOT occurred, and leaves the record an UNCOMMITTED CANDIDATE with nothing staged, committed, pushed, or tagged; and grants NO orphan adoption, execution, operational-state mutation, raw/lineage/catalog/receipt mutation, carry-in minting or consumption, transport construction, network, SEC contact, live acquisition, resume, retry, replacement run, clean run, T6, M3.2B, Gate H, or tag authority, and claims NO live readiness
M3_2_ORPHAN_ADOPTION_ARCHITECTURE_STATUS: ACCEPTED AND BINDING; NON-SELF-EXECUTING; NOT AUTHORIZED, NOT EXECUTED, NOT VERIFIED, NOT ACCEPTED AS PERFORMED - accepted Decision 057, 2026-08-09, outcome M3_2_ORPHAN_ADOPTION_PROCEDURE_ARCHITECTURE_ACCEPTED. The preceding CLAUDE_M3_2_ORPHAN_ADOPTION_ARCHITECTURE_DISCOVERY_PACKET authorized by Decision 056 section 10 was issued and completed as READ-ONLY work; Decision 057 adjudicates it, CONFIRMS ONE MAJOR CORRECTION to its central write contract, and fixes the exact later procedure. Corrected binding contract: TWO TABLES, TWO ROWS, THREE SEPARATELY COMMITTED TRANSACTIONS - one census_source_observations row, one census_projection_recovery_events row ending resolved with non-NULL resolved_at_utc, projected_to_audit 0 to 1, and an ATOMICALLY REPLACED JSONL projection - and end-to-end adoption plus projection rebuild is NOT atomic. Fixed architecture: ARCHITECTURE C CORRECTED, one ephemeral SHA-256-recorded one-time procedure in mktemp scratch outside the repository, accepted _observation_from_intent unchanged as SOLE verifier, ONE guarded INSERT inside CatalogWriter.batch whose EXACT persisted row is now fixed - both guards reasserted in-transaction on the batch connection, then ONE captured recorded_at_utc = utc_now() as the SOLE value THE PROCEDURE ITSELF generates and the sole newly generated value IN THE OBSERVATION ROW - a scope that does NOT deny the TWO LIBRARY-OWNED instants a correct rebuild necessarily generates, detected_at_utc and resolved_at_utc, which are EXPECTED, must be SEPARATELY EVIDENCED, and are required to equal NEITHER each other NOR recorded_at_utc - values EXACTLY ObservationRecorder._row(verified_observation, recorded_at_utc) over the accepted OBSERVATION_COLUMNS with projected_to_audit inserted as 0, and a REQUIRED cursor.rowcount == 1 kept as defense-in-depth and asserted directly from the real cursor, with ObservationRecorder.record itself PROHIBITED because it opens its own transaction and would nest a second BEGIN IMMEDIATE inside CatalogWriter.batch, and with both guards being ONE-USE REFUSALS carrying no update, upsert, or replay path - MANDATORY rebuild_audit_projection(connection, destination) in the SAME authorized process invocation but ONLY AFTER the CatalogWriter.batch context exits and transaction 1 commits, NEVER inside the batch, since the rebuild opens its own transactions, and supplying NEITHER census_run_id NOR fault_hook, NO permanent production surface, and the governed recovery surface (apply_recovery_action, reconcile, _recover_orphan, RawStore.quarantine, RawStore.reconcile) plus prepare_operational_catalog, migrate, seed_reference_data, and every receipt, checkpoint, run-registration, and transport function NEVER called, because _recover_orphan quarantines - and therefore MOVES - the governed raw object on any verifier failure. Also fixed: the exact content rulings; the eleven-item conjunctive fail-closed preflight including ZERO blocked rows CATALOG-WIDE as a strong owner ruling; the exact terminal delta with the receiptless determination expected UNSAFE solely for absence of a predecessor receipt and never SAFE and never resumption; the six-point fail-closed fault classification bound to the three committed rebuild fault hooks; fifteen synthetic cases, non-vacuous for EVERY behaviourally reachable row-shape, timestamp, flag, and nested-transaction mutation, including the mandatory reconcile/quarantine contrast on a disposable fixture and the additive fifteenth case whose MUTATION limb must FAIL if the ROW CONSTRUCTION is mutated or removed, while the cursor.rowcount == 1 guard is instead a DIRECTLY ASSERTED AND EVIDENCED INVARIANT whose deletion is expressly NOT required to be caught by a mutation - a permitted plain INSERT yields 1 and every other accepted outcome raises first - so its ASSERTION limb evidences the real successful cursor result instead; and the private mode-0600 evidence contract, whose eventual ACCEPTED adoption decision identity and ACCEPTED evidence-manifest SHA-256 - not this architecture record - are what a later carry-in authority must bind under Decision 055 section 6.1. Owner ruling on retries: EXACTLY ONE later REAL invocation touching the GOVERNED catalog or object may be authorized and NO SECOND, the disposable synthetic preflight suite running before, outside, and without access to that governed state being NEITHER that invocation NOR counted against it NOR authorized by this record; NO retry loop, auto-retry, auto-resume, or automatic relaunch; any exception, interruption, uncertainty, or failed postcondition STOPS and refers to the owner; a proven-uncommitted INSERT needs NEW owner authority; a committed or uncertain INSERT means NEVER re-adopt, read-only classification only, and only a separate rebuild-only recovery ruling may mutate; NO manual incident-row UPDATE or DELETE. NOT YET DONE and NOT authorized by Decision 057: the adoption itself, its execution packet, its independent verification, its acceptance, M3-L16 closure, carry-in minting or consumption, network, SEC contact, transport construction, a clean run, T6, M3.2B, and Gate H. Accepting a procedure architecture is NOT performing the adoption and is NOT closing M3-L16. Live readiness is NOT claimed. CANDIDATE PROVENANCE: the uncommitted Decision 057 candidate has been CORRECTED TWICE before publication, each time under a bounded owner instrument. FIRST REMEDIATION, 2026-08-09: fixed one owner-identified MAJOR omission - the record fixed _observation_from_intent as verifier and a guarded INSERT inside CatalogWriter.batch but did NOT mandate the full persisted row construction, so a later direct INSERT could have complied with the prose while persisting a different tuple or failing to prove exactly one row; it added section 4.4, section 5.1, content rulings 8 through 10, the terminal row-shape postcondition, evidence item 14, the additive fifteenth synthetic case, and the section 4.2 precision fix that record and _row are cited ONLY as row-shape precedent. SECOND REMEDIATION, 2026-08-09, the EXCEPTIONAL and FINAL automatic correction: the fresh independent review of the first-remediated candidate found TWO FURTHER MAJOR defects, both in the PROOF LAYER rather than the architecture - (a) section 8 asserted that "no second generated instant exists anywhere in the run", which is FALSE, because a correct rebuild necessarily generates two further library-owned instants, the blocked event's detected_at_utc at observation_catalog.py line 1130 and its resolved_at_utc at line 673, each made must-exist by migration 0008 lines 456 and 459; and (b) section 10 demanded that deleting the cursor.rowcount == 1 guard be caught by a behaviourally non-vacuous mutation, which is IMPOSSIBLE under the accepted plain INSERT and schema shape - and corrected those plus FOUR related MINOR ambiguities: the batch must exit and transaction 1 must commit before rebuild_audit_projection is called; the real second-limb call shape is pinned to rebuild_audit_projection(connection, destination) with neither census_run_id nor fault_hook; the zero-reason and zero-archive-member rulings are re-grounded in the procedure executing exactly one direct census_source_observations INSERT and no reason or member statement, rather than in loops internal to the prohibited ObservationRecorder.record; and the counting of "exactly one invocation" is disambiguated so the disposable synthetic preflight suite is neither the real adoption invocation nor counted against it nor authorized now. It added section 4.2.1, section 5.1 step 6, and section 12 clause 9, and rewrote the affected loci in sections 5, 5.1, 6, 7, 8, 10, 11, 15, and 16. BOTH remediations left the ACCEPTED CENTRAL ORPHAN-ADOPTION ARCHITECTURE UNCHANGED, granted NO execution authority, changed no executable, test, migration, configuration, contract, runbook, or template byte, and touched no operational state. NO THIRD AUTOMATIC CORRECTION LOOP IS PERMITTED; any further defect returns to the owner. The exact next authorized action is CLAUDE_M3_2_DECISION_057_FINAL_FRESH_INDEPENDENT_REVIEW_PACKET, which is read-only and non-self-executing
CURRENT_STAGE: M3.2 ORPHAN-ADOPTION PROCEDURE ARCHITECTURE ACCEPTED — DECISION 057 (2026-08-09), NON-SELF-EXECUTING; THE CARRY-IN IMPLEMENTATION REMAINS ACCEPTED AT CANDIDATE 2c18e89b73048a6cf7ce8cd528325f2a0c50a9ac AND TREE 6f77deaf0aaf4be3e365d3d0be8c22a89c737802 (DECISION 056); M3-L14 CLOSED; M3-L16 ACTIVE AND BLOCKING WITH THE ADOPTION NEITHER AUTHORIZED NOR PERFORMED AND SEPARATE OWNER CLOSURE OUTSTANDING; M3.2 NOT COMPLETE; LIVE READINESS NOT CLAIMED
ACTIVE_BLOCKER: M3-L16 AND THE UNADOPTED HISTORICAL ORPHAN BLOCK EVERY CLEAN-RUN AND LIVE AUTHORIZATION. THE CARRY-IN MECHANISM IS IMPLEMENTED, VALIDATED, INDEPENDENTLY REVIEWED, CORRECTED ONCE, OWNER-VERIFIED, AND ACCEPTED BY DECISION 056, AND THE ORPHAN-ADOPTION PROCEDURE ARCHITECTURE IS NOW FIXED BY DECISION 057 — BUT DECISION 057 IS NON-SELF-EXECUTING AND AUTHORIZES NO INVOCATION, SO THE ORPHAN REMAINS UNADOPTED. CARRY-IN ACCOUNTING ALONE CANNOT CLEAR THE RAW-STORE/CATALOG ORPHAN MISMATCH. RECOVERY REMAINS UNDETERMINED, CONSUMPTION REMAINS 1 OF 801, THE OLD RUN IS NEVER RESUMABLE, AND NO CARRY-IN AUTHORITY MAY BE MINTED OR CONSUMED BEFORE THE SEPARATELY AUTHORIZED OFFLINE ONE-TIME VERIFIED ORPHAN ADOPTION IS EXECUTED UNDER A SEPARATE OWNER EXECUTION PACKET, INDEPENDENTLY VERIFIED, ACCEPTED, AND M3-L16 IS SEPARATELY CLOSED
DECISION_022_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; controls crosswalk item 46 reserve-rank applicability only
DECISION_023_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; outcome M23_STAGE_S6_ACCEPTED_AND_COMPLETE; controls S6 acceptance, delivered-path ratification, limitations O1-O4, and checkpoint authorization
DECISION_024_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; outcome M2_M3_BOUNDARY_GOVERNANCE_ACCEPTED; controls the M2 to M3 phase boundary and five entry conditions; grants no implementation authority
DECISION_025_STATUS: ACCEPTED — OWNER APPROVED 2026-07-31; outcome INTEGRATED_AUDIT_DOCUMENTATION_CORRECTIONS_AUTHORIZED
IMPLEMENTATION_AUTHORIZATION: NONE — DECISION 055'S OFFLINE IMPLEMENTATION AUTHORITY IS EXHAUSTED BY THE DECISION 056 ACCEPTED CANDIDATE. DECISION 056'S READ-ONLY ORPHAN-ADOPTION ARCHITECTURE DISCOVERY HAS COMPLETED AND IS ADJUDICATED BY DECISION 057, WHICH IS NON-SELF-EXECUTING AND AUTHORIZES NEXT ONLY ITS OWN FINAL FRESH INDEPENDENT NON-AUTHOR REVIEW; NO SOURCE, TEST, DOCUMENTATION, MIGRATION, CONFIGURATION, REASON-CODE, OPERATIONAL-STATE, ORPHAN-ADOPTION, TRANSPORT, NETWORK, SEC, CLEAN-RUN, T6, M3.2B, GATE H, OR TAG WORK IS AUTHORIZED
ACTIVE_STAGE_CONTRACT: Milestones/contracts/m3_2.md
NEXT_AUTHORIZED_ACTION: CLAUDE_M3_2_DECISION_057_FINAL_FRESH_INDEPENDENT_REVIEW_PACKET

DECISION_056_CURRENT_STATE: ACCEPTED 2026-08-09 — CANDIDATE 2c18e89b73048a6cf7ce8cd528325f2a0c50a9ac AT TREE 6f77deaf0aaf4be3e365d3d0be8c22a89c737802; DECISION 055 IMPLEMENTATION AUTHORITY EXHAUSTED; M3-L14 CLOSED; M3-L16 ACTIVE AND BLOCKING WITH IMPLEMENTATION ACCEPTED BUT VERIFIED ORPHAN ADOPTION AND SEPARATE OWNER CLOSURE OUTSTANDING; LIVE READINESS NOT CLAIMED; TRACKED NETWORK FALSE/FALSE; COMPANYFACTS DISABLED; NO OPERATIONAL-STATE, ORPHAN-ADOPTION, TRANSPORT, NETWORK, SEC, CLEAN-RUN, T6, M3.2B, GATE H, OR TAG AUTHORITY. ITS SECTION 10 NEXT-ACTION POINTER CLAUDE_M3_2_ORPHAN_ADOPTION_ARCHITECTURE_DISCOVERY_PACKET IS NOW HISTORICAL: THAT DISCOVERY WAS ISSUED AND COMPLETED AS READ-ONLY WORK AND IS ADJUDICATED BY ACCEPTED DECISION 057; NEXT_AUTHORIZED_ACTION CARRIES THE CURRENT POSITION

DECISION_057_CURRENT_STATE: ACCEPTED 2026-08-09 — OUTCOME M3_2_ORPHAN_ADOPTION_PROCEDURE_ARCHITECTURE_ACCEPTED; EXPLICITLY NON-SELF-EXECUTING AND GRANTING NO OPERATIONAL INVOCATION; RECORDED AS AN UNCOMMITTED GOVERNANCE CANDIDATE WHOSE PUBLICATION IS NOT AUTHORIZED BY THE AUTHORING TASK AND HAS NOT OCCURRED; CORRECTED TWICE BEFORE PUBLICATION UNDER BOUNDED OWNER INSTRUMENTS, THE SECOND AND FINAL AUTOMATIC REMEDIATION FIXING TWO PROOF-LAYER MAJORS FOUND BY THE FIRST FRESH REVIEW PLUS FOUR RELATED MINORS, WITH THE ACCEPTED CENTRAL ARCHITECTURE UNCHANGED AND NO THIRD AUTOMATIC CORRECTION LOOP PERMITTED; M3-L16 ACTIVE AND BLOCKING WITH THE ADOPTION NEITHER AUTHORIZED NOR PERFORMED; NO CARRY-IN AUTHORITY MINTED OR CONSUMED; CONSUMPTION 1 OF 801; OLD RUN NEVER RESUMABLE; RECOVERY UNDETERMINED; LIVE READINESS NOT CLAIMED; TRACKED NETWORK FALSE/FALSE; COMPANYFACTS DISABLED; NO OPERATIONAL-STATE, ORPHAN-ADOPTION, EXECUTION, TRANSPORT, NETWORK, SEC, CLEAN-RUN, T6, M3.2B, GATE H, COMMIT, PUSH, OR TAG AUTHORITY
```
