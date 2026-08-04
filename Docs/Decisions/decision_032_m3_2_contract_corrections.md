# Decision 032 — M3.2 Contract Corrections and Rereview Requirement

**Date:** 2026-08-04
**Status:** ACCEPTED — OWNER APPROVED 2026-08-04
**Type:** Bounded governance-correction and owner-interpretation record. **Not** a preregistration
deviation. It changes no hypothesis, cohort window, maturity gate, outcome definition, threshold,
seed, selection methodology, S4/S5/S6 identity, hash preimage, migration byte, implementation byte,
test byte, script byte, or executable-configuration byte. It authorizes no implementation, no
network or CompanyFacts enablement, no live SEC access, no acquisition, no operational catalog, no
use of the M3.2A ceiling, no contract acceptance, and no tag.
**Supersedes:** nothing. **Amends:** only the unaccepted draft `Milestones/contracts/m3_2.md` — a
draft is correctable; no accepted decision, migration, template, or completed contract is edited.
**Related:** Decisions 024 §8, 027 v0.2, 028–031;
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Docs/m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md`](../m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's adoption of the independent M3.2 contract review's findings; the bounded
correction of the M3.2 contract draft; the procedural requirement that a fresh independent rereview
by one non-author session using no subagents precede owner acceptance; and the related status,
registry, and navigation updates.

---

## 1. Why this record is required

Decision 029 §12 step 17 produced the bounded M3.2 contract draft at commit
`536856325f6a655416d48276c5b93848cab388e8`. Under the owner's 2026-08-03 authorization, a fresh
independent session reviewed that draft and returned
`M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS` with zero BLOCKER findings, two
MAJOR findings, four MINOR findings, and one OPTIMIZATION finding. The owner has adopted the
substantive findings and issued the correction instrument recorded verbatim in §4. This record is
the durable form of that instrument and the authority for the bounded corrections it directs.

## 2. Verified baseline

Verified live immediately before this record was written:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| Baseline commit (`HEAD`) | `3fbaa12d671d0000f5b608bbf6fb271f78b4673f` ("Record independent M3.2 contract review") |
| Parent | `536856325f6a655416d48276c5b93848cab388e8` ("Draft bounded M3.2 contract") — the reviewed draft commit |
| `origin/main` | `536856325f6a655416d48276c5b93848cab388e8`; local `main` ahead by exactly the one review commit, behind zero, no divergence — the fast-forward push this record authorizes carries it |
| Working tree | clean; nothing staged; no non-ignored untracked path; `.env` ignored and never read |
| Tags | `m3.1-complete` unchanged (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`); no tag at HEAD |
| Protected bytes | `src`, `tests`, `scripts`, `Makefile`, `pyproject.toml`, `configs`, `.github` byte-identical from the frozen accepted M3.1 SHA `970e050deb06910adcde8588101564beb7d19c74` through the baseline commit (empty diff) |
| Migration chain | contiguous through `0013`; no migration is proposed or authorized here |
| Decision numbering | directory and registry both end at Decision 031; 032 is the next genuinely unused number |

## 3. The independent M3.2 contract review

| Field | Value |
|---|---|
| Artifact | `Docs/m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md` |
| Artifact SHA-256 | `fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57` |
| Review commit | `3fbaa12d671d0000f5b608bbf6fb271f78b4673f` |
| Reviewed draft commit | `536856325f6a655416d48276c5b93848cab388e8` (tree `39fd29911a130a07fe58840c3d16e0d34a295575`) |
| Reviewed contract SHA-256 | `d53547672f75124a773c17b8b49d29e69f20f2890725df80e67dfc74633ae390` |
| Verdict | `M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS` |
| Findings | zero BLOCKER; two MAJOR (F1 completion semantics; F2 boundary exactness including the unnamed network-enable change); four MINOR (F3 crash-segment accounting; F4 evidence-index vocabulary; F5 stale navigation prose; F6 sentinel naming); one OPTIMIZATION (F7 positive controls) |
| Sixty-five-question matrix | all sixty-five answered in the artifact, with F-section and I-section defects grounding the two MAJOR findings |
| Independence | fresh non-author session; non-authorship attested in the artifact; the artifact discloses that two read-only fact-gathering subagents were used, with the verdict determined directly by the session |

## 4. The owner correction instrument (verbatim, received 2026-08-04)

```text
OWNER_M3_2_CONTRACT_CORRECTION_DECISION: APPROVED
The project owner accepts the substantive findings of the M3.2 contract review
at commit:
3fbaa12d671d0000f5b608bbf6fb271f78b4673f
Review artifact SHA-256:
fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57
Substantive review disposition:
M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS
The owner adopts the following findings:

1. F1 is a MAJOR finding. The current completion language can permit false
success when required metadata is absent but the request has received a
terminal classification.
2. F2 is a MAJOR finding. The contract does not yet name an exact,
command-scoped network-enablement mechanism or the complete expected
implementation and command surface.
3. F3 is a useful nonblocking correction: uncertain attempts from a
hard-interrupted segment require an explicit conservative accounting rule.
4. F4 remains a nonblocking vocabulary issue to be resolved before the
affected M3.2 evidence artifacts are publicly indexed.
5. F5 should be corrected where the authorized navigation documents contain
stale current-state prose.
6. The accepted M3.2B unresolved-count sentinel remains authoritative. Its
historical Gate-F-specific name must be explained rather than silently
renamed.
7. Positive controls should be explicitly required for critical refusal and
nonchange boundaries.

Procedural disposition:
The review artifact is preserved as a truthful and useful correction review.
However, it does not satisfy the final independent-review prerequisite for
contract acceptance because its session used two fact-gathering subagents
despite the one-active-session restriction.
The corrected contract therefore requires a fresh independent rereview by one
non-author session using no subagents before owner acceptance.
This decision authorizes:

* bounded correction of the M3.2 contract;
* durable recording of this owner correction decision;
* related registry, status, and navigation updates;
* normal commit and fast-forward push;
* no executable implementation.

This decision does not:

* accept the M3.2 contract;
* authorize M3.2 implementation;
* authorize creation of the operational catalog;
* enable network or CompanyFacts;
* authorize live SEC access;
* authorize acquisition;
* authorize use of the M3.2A ceiling.

Owner:
Joseph Nihill, project owner acting through the ChatGPT owner decision
Date:
2026-08-04
Recorded acceptance reference:
ChatGPT owner M3.2 contract correction decision dated 2026-08-04, bound to
review commit 3fbaa12d671d0000f5b608bbf6fb271f78b4673f and review artifact
SHA-256 fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57.
This is a transparent recorded owner decision, not a handwritten,
cryptographic, or third-party digital signature.
```

Owner: **Joseph Nihill, project owner acting through the ChatGPT owner decision.** The recorded
reference above is a transparent recorded owner decision; it is not a handwritten, cryptographic,
or third-party digital signature.

## 5. Adopted findings and the corrections they direct

1. **F1 (MAJOR) — completion semantics.** The contract's §14 is corrected to distinguish
   **termination** (every planned logical request at a terminal disposition) from **successful
   completion**, which additionally requires every required object — the bulk-submissions object,
   both ticker files, the SIC list, the calendar-year filing-calendar page, every approved
   announcement-manifest entry (zero in the approved plan), and all 70 required quarterly-index
   instances — present in the raw store, hash-verified, and fully provenanced, with any
   required-object absence enumerated in the window's receipt and **expressly owner-adjudicated
   before the between-windows freeze and before any M3.2B budget approval**. A window with an
   unadjudicated absence is `completed_with_absences`, is not successfully complete, and is not
   eligible for the freeze/derivation step or Gate H. Gate H checklist item 3.3 is read under this
   standard; the frozen template itself is not edited.
2. **F2 (MAJOR) — exact boundary.** The contract's §16 now names the single command-scoped
   network-enable configuration change — a new boolean key `network.m3_acquire_enabled`
   (default `false`) in `configs/project.yaml`, mirrored by the one-field addition of
   `m3_acquire_enabled: bool = False` to `NetworkSection` in `src/disclosure_drift/config.py`;
   `m3 acquire --live` alone reads it; `network.enabled` remains `false` throughout every M3.2
   window so the M2.2 census surfaces stay refused; the key is set `true` only in the
   owner-authorized window-local configuration supplied via `DISCLOSURE_DRIFT_CONFIG` for the T6
   invocation, never in the tracked default — and enumerates the complete expected implementation
   and test surface, including CLI wiring for all six planned Appendix-B M3.2 commands
   (`m3 acquire` with `--show-scope` and `--resume-from`, `m3 derive-dependent-plan`,
   `m3 reconcile-requests`, `m3 show-drift`, `m3 recover`), the named new driver module and test
   files, and the bounded edits to the M3.1 recovery and request-plan modules. The T2 packet still
   enumerates and confirms the exact final set. **This naming is contract text for the future
   implementation; no configuration byte changes now** — `configs/project.yaml` and `config.py`
   remain byte-identical to the frozen accepted SHA until a lawful T2.
3. **F3 (nonblocking, corrected now).** §12 gains the conservative accounting rule: a hard
   interruption that wrote no terminating receipt leaves the in-flight logical request's physical
   attempts unrecorded; resume accounting must charge that request at its full per-route
   `A_reachable` against the ceiling, and where even that bound cannot be established the
   determination is `UNDETERMINED` and the run does not resume.
4. **F4 (nonblocking, deferred with a recorded gate).** §20 now requires that before any
   between-windows freeze artifact (the frozen bootstrap object-identity list; the derived
   dependent reference set) is publicly indexed, the evidence-index artifact-type vocabulary be
   extended by an authorized index edit or the artifact be assigned to an existing type by the
   contract of record. The index itself is not edited by this record.
5. **F5 (navigation staleness, corrected now).** Stale current-state prose is corrected in the
   authorized navigation documents: `Milestones/contracts/README.md` (the pre-acceptance blocks
   still describing the M3.1 implementation as not accepted, the budget and ceiling as unapproved,
   and M3-L11/M3-L12 as active Gate F blockers, and the `m3_1.md` index bullet) and the one stale
   Decision-029 next-action sentence in `Docs/decision_index.md`. The completed contract
   `m3_1.md` itself is historical record and is not edited.
6. **F6 (sentinel explained, not renamed).** `EXACT_COUNT_RESOLVED_BY_GATE_F_ZERO_REQUEST_PLAN`
   remains the authoritative accepted unresolved-count sentinel (Decision 027 §§15–16; master plan
   M3.1 §15 applies it to the M3.2B counts; Decision 030 Ruling C). The contract's §5 and §15 now
   carry an explanatory gloss — the name is historical, from Gate F where the sentinel originated —
   and no rename occurs anywhere.
7. **F7 (positive controls).** §18 now requires a non-vacuous positive control for every critical
   refusal and nonchange boundary, and §19 names the exact nonchange-proof command over the §16
   prohibited set.

## 6. Procedural rereview requirement

The 2026-08-04 review artifact is **preserved unchanged** as a truthful and useful correction
review; nothing in it is rewritten, and its findings ground this record. It does **not** satisfy
the final independent-review prerequisite for contract acceptance, because its session used two
read-only fact-gathering subagents despite the one-active-session restriction of the owner's review
instruction. **The corrected contract therefore requires a fresh independent rereview by one
non-author session using no subagents before owner acceptance.** That rereview is the next
authorized action (§10); this record does not perform it, and no session that authored the draft,
the review, or these corrections may perform it.

## 7. Authorized paths and acts

Exactly, and nothing further:

- `Docs/Decisions/decision_032_m3_2_contract_corrections.md` (this record);
- `Milestones/contracts/m3_2.md` — the §5 corrections only;
- `Docs/Decisions/decision_registry.md` — the 032 row and quick-lookup entry;
- `Milestones/STATUS.md` — current-state, next-action, and machine-marker updates;
- `Milestones/contracts/README.md` — the F5 corrections and the corrected-draft index wording;
- `Docs/decision_index.md` — the single stale next-action sentence;
- one bounded governance commit carrying exactly the paths above, and one normal fast-forward push
  of `main` (which also publishes the already-committed review commit `3fbaa12d…`). No tag.

No implementation, test, script, migration, template, executable-configuration, or private-evidence
byte changes. The review artifact is not modified.

## 8. What this record does not do

It does not accept the M3.2 contract (T1 remains a separate owner act after the required rereview);
does not authorize M3.2 implementation (T2), implementation acceptance (T3), live-operation
preflight (T4), live-operation authorization (T5), or execution (T6); does not enable network or
CompanyFacts and changes no configuration byte; does not authorize any SEC contact, connectivity
test, acquisition, or operational-catalog creation or population; does not authorize use of the
M3.2A ceiling; does not close, open, or edit any limitations-register entry; does not alter the
review artifact, any accepted decision, any migration, any template, or any private evidence; and
creates no tag.

## 9. Acceptance criteria for this record's commit

All verified before the commit: (1) the corrected contract carries every §5 correction and no other
substantive change; (2) `src`, `tests`, `scripts`, `Makefile`, `pyproject.toml`, `configs`, and
`.github` remain byte-identical to the frozen accepted SHA; (3) Decision 032 is unique — no other
decision file or registry row carries the number; (4) the registry, status ledger, and navigation
updates match this record exactly; (5) `git diff --check`, `make context`, `make secrets`, and
`make hygiene` pass over the updated tree; (6) the commit carries exactly the §7 paths; (7) the
push is a normal fast-forward publishing the review commit and this commit; (8) no tag is created;
(9) no private path, SEC identity, or private-evidence content appears in any changed file.

## 10. Formal outcome

```text
M3_2_CONTRACT_CORRECTIONS_RECORDED
```

**Next authorized action:** `INDEPENDENT_M3_2_CONTRACT_REREVIEW` — a fresh independent rereview of
the corrected `Milestones/contracts/m3_2.md` by **one** non-author session using **no subagents**,
as the owner directs; only after it passes may the owner take the T1 acceptance decision. No live
SEC access, no M3.2 implementation, and no acquisition is authorized.
