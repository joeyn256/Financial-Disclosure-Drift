# Decision 033 — M3.2 Correction-Pass Adjudication and Governance Cleanup

**Date:** 2026-08-04
**Status:** ACCEPTED — OWNER APPROVED 2026-08-04
**Type:** Bounded owner-adjudication and governance-cleanup record. **Not** a preregistration
deviation. It changes no hypothesis, cohort window, maturity gate, outcome definition, threshold,
seed, selection methodology, S4/S5/S6 identity, hash preimage, migration byte, implementation byte,
test byte, script byte, or configuration byte. It authorizes no implementation, no network or
CompanyFacts enablement, no live SEC access, no acquisition, no operational catalog, no use of the
M3.2A ceiling, no contract acceptance, no tag, and no history rewrite.
**Supersedes:** nothing. **Amends:** nothing — accepted [Decision 032](decision_032_m3_2_contract_corrections.md)
is **not edited**; this record stands beside it, in the convention Decision 030 §10 fixes ("after
commit, a correction is a new dated decision record — never a history rewrite and never an in-place
edit of an accepted record").
**Related:** Decisions 024 §8, 027 v0.2, 028–032;
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md);
[`Docs/m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md`](../m3/reviews/m3_2_contract_independent_review_536856325f6a655416d48276c5b93848cab388e8.md);
[`Milestones/STATUS.md`](../../Milestones/STATUS.md).
**Governs:** the owner's adjudication of the Decision 032 correction pass — acceptance of its
substantive corrections, the two bounded governance corrections it requires, and the disposition of
two recorded procedural deviations.

---

## 1. Why this record is required

The Decision 032 correction pass was published at commit
`96dea2b50b7e87243aad29032946ef8447033eb9`. Reviewing it, the owner accepted the substantive
corrections and identified two bounded governance corrections plus two procedural deviations
requiring an express disposition. Repository convention does not permit recording that adjudication
by editing accepted Decision 032: Decision 030 §10 requires a new dated decision record for any
post-commit correction, and the single precedent for an append-only note on an accepted record
(the Decision 028 §15.1 note) was itself authorized by a separate new accepted decision rather than
taken on a session's own authority. The status ledger alone is also insufficient — `Milestones/
STATUS.md` records workflow state and never carries a governance ruling of record. This record is
therefore the convention-correct durable home for the owner's adjudication.

## 2. Verified baseline

Verified live immediately before this record was written:

| Field | Value |
|---|---|
| Repository | Financial Disclosure Drift |
| Branch | `main` |
| Baseline commit (`HEAD`) | `96dea2b50b7e87243aad29032946ef8447033eb9` ("Correct M3.2 contract and record Decision 032") |
| Parent | `3fbaa12d671d0000f5b608bbf6fb271f78b4673f` ("Record independent M3.2 contract review") |
| `origin/main` | `96dea2b50b7e87243aad29032946ef8447033eb9`; `HEAD == origin/main`; no divergence |
| Working tree | clean; nothing staged; no non-ignored untracked path; `.env` ignored and never read |
| Tags | `m3.1-complete` unchanged (tag object `638a02b780d912ff7b37a2f523277b9d451a015a`, peeled `4cd2c7299ae30ca499108bd7f0a17a0adaf215f4`); no tag at HEAD |
| Protected bytes | `src`, `tests`, `scripts`, `Makefile`, `pyproject.toml`, `configs`, `.github` byte-identical to the frozen accepted M3.1 SHA `970e050deb06910adcde8588101564beb7d19c74` |
| Migration chain | contiguous through `0013`; no migration proposed or authorized here |
| Decision numbering | directory and registry end at Decision 032; **033** is the next genuinely unused number |

## 3. The owner adjudication instrument (verbatim, received 2026-08-04)

```text
OWNER_DECISION_032_CORRECTION_PASS_ADJUDICATION

The project owner accepts the substantive M3.2 contract corrections recorded in
Decision 032 and commit:

96dea2b50b7e87243aad29032946ef8447033eb9

The corrected M3.2 contract remains:

DRAFT — CORRECTED (DECISION 032) — PENDING INDEPENDENT REREVIEW AND OWNER
ACCEPTANCE

The owner accepts that:

1. F1 through F7 were substantively addressed.
2. The prior review artifact remains preserved and is not the final independent
    acceptance review.
3. A fresh non-author session using no subagents remains mandatory.
4. M3.2 implementation, network enablement, live SEC access, acquisition,
    operational-catalog creation, and ceiling use remain unauthorized.

Two bounded governance corrections remain required before the rereview:

1. Restore Docs/decision_index.md to its exact bytes at parent commit
    3fbaa12d671d0000f5b608bbf6fb271f78b4673f, because that path was not in
    the final authorized-path list.
2. Set the exact status marker:
    NEXT_AUTHORIZED_ACTION:
    FRESH_NO_SUBAGENT_INDEPENDENT_REREVIEW_OF_CORRECTED_M3_2_CONTRACT

The published correction commit used the subject:

Correct M3.2 contract and record Decision 032

rather than the task-prescribed subject:

Correct bounded M3.2 contract

The owner accepts this as a non-substantive procedural deviation. Do not amend,
rebase, reset, force-push, or otherwise rewrite the published commit.

This adjudication authorizes one bounded governance-cleanup commit and normal
fast-forward push only.

It does not authorize the independent rereview itself, contract acceptance,
implementation, network enablement, or live SEC activity.

Date:
2026-08-04
```

Owner: **Joseph Nihill, project owner acting through the ChatGPT owner decision.** This is a
transparent recorded owner decision; it is not a handwritten, cryptographic, or third-party digital
signature.

## 4. Substantive corrections accepted

The owner accepts that findings **F1 through F7** of the independent M3.2 contract review (artifact
SHA-256 `fbf8c68caa8a8a102e643ad9f0ad28758b20ed368ca7928263d6f2f89d32da57`; review commit
`3fbaa12d671d0000f5b608bbf6fb271f78b4673f`; verdict
`M3_2_CONTRACT_INDEPENDENT_REVIEW: PASS_WITH_REQUIRED_CORRECTIONS`) were **substantively
addressed** by the Decision 032 correction pass published at `96dea2b…`. The corrected contract
text stands as published; **this record changes no byte of `Milestones/contracts/m3_2.md`**, whose
status remains `DRAFT — CORRECTED (DECISION 032) — PENDING INDEPENDENT REREVIEW AND OWNER
ACCEPTANCE`.

The prior review artifact **remains preserved and unchanged**, and — as accepted Decision 032 §6
already records — it is **not** the final independent acceptance review.

## 5. Bounded governance correction 1 — `Docs/decision_index.md` restored

`Docs/decision_index.md` was edited during the Decision 032 correction pass to correct one stale
Decision-029 next-action sentence. **That path was not in the final authorized-path list**, so the
edit was a path-scope deviation. Under this adjudication the file is **restored to its exact bytes
at parent commit `3fbaa12d671d0000f5b608bbf6fb271f78b4673f`**, using the repository version from
that commit rather than any manual re-approximation, and proven byte-identical to it.

**Consequence for accepted Decision 032, recorded rather than edited.** Decision 032 §5 item 5 and
§7 list `Docs/decision_index.md` among the F5 correction targets and authorized paths. With the
restoration, that path carries no F5 correction. **Accepted Decision 032 is not amended**; this
section is the controlling record of the discrepancy, and `Milestones/contracts/README.md` remains
the sole navigation file carrying the F5 corrections. The stale Decision-029 next-action sentence
in `Docs/decision_index.md` is therefore **still present and remains an open, nonblocking
navigation-staleness item** — the index is a navigation aid that never establishes that a decision
exists or is approved, and `Milestones/STATUS.md` carries the authoritative next action. Correcting
it later requires its own explicit path authorization.

## 6. Bounded governance correction 2 — the exact next-action marker

`Milestones/STATUS.md` now carries exactly:

```text
NEXT_AUTHORIZED_ACTION: FRESH_NO_SUBAGENT_INDEPENDENT_REREVIEW_OF_CORRECTED_M3_2_CONTRACT
```

The marker occurs exactly once and is the string `scripts/context_snapshot.sh` resolves. Directly
dependent ledger prose is aligned to it so no sentence contradicts the marker. **Neither this
record nor the cleanup commit begins, authorizes, or performs the rereview**; the marker records
what must happen next, not that it has happened.

## 7. Procedural deviations adjudicated

1. **Nonconforming published commit subject — accepted.** The correction commit `96dea2b…` used the
   subject `Correct M3.2 contract and record Decision 032` rather than the task-prescribed
   `Correct bounded M3.2 contract`. The owner accepts this as a **non-substantive procedural
   deviation**. It is recorded here so the divergence between the prescribed and published subject
   is durable rather than silent.
2. **No history rewrite is authorized.** The published commit is **not** amended, rebased, reset,
   force-pushed, or otherwise rewritten. The correction is a forward commit, exactly as
   Decision 030 §10 and master plan §11 require of a pushed commit.

## 8. Authorized paths and acts

Exactly, and nothing further:

- `Docs/decision_index.md` — restoration to its `3fbaa12d…` bytes only;
- `Milestones/STATUS.md` — the exact next-action marker and directly dependent prose;
- `Docs/Decisions/decision_033_m3_2_correction_pass_adjudication.md` (this record);
- `Docs/Decisions/decision_registry.md` — the 033 row and quick-lookup entry;
- **one** bounded governance-cleanup commit with the subject `Clean up Decision 032 governance
  record`, and **one** normal fast-forward push of `main`. **No tag.**

No other tracked path changes. No implementation, test, script, migration, template,
configuration, contract, review-artifact, or private-evidence byte changes.

## 9. What this record does not do

It does not accept the M3.2 contract (T1 remains a separate owner act after the required rereview);
does not authorize or begin the rereview itself; does not authorize M3.2 implementation (T2),
implementation acceptance (T3), live-operation preflight (T4), live-operation authorization (T5),
or execution (T6); does not enable network or CompanyFacts; does not authorize any SEC contact,
connectivity test, acquisition, or operational-catalog creation or population; does not authorize
use of the M3.2A ceiling; does not edit accepted Decision 032, the review artifact, any other
accepted decision, any migration, any template, or any private evidence; does not close, open, or
edit any limitations-register entry; authorizes no history rewrite; and creates no tag.

## 10. Formal outcome

```text
M3_2_CORRECTION_PASS_ADJUDICATED_AND_CLEANED_UP
```

**Next authorized action:**
`FRESH_NO_SUBAGENT_INDEPENDENT_REREVIEW_OF_CORRECTED_M3_2_CONTRACT` — a fresh independent rereview
of the corrected `Milestones/contracts/m3_2.md` by **one** non-author session using **no
subagents**, as the owner directs; only after it passes may the owner take the T1 acceptance
decision. **The corrected contract remains unaccepted, and implementation, network enablement, and
live SEC access remain unauthorized.**
