# Decision 063 — M3.2 Cross-Namespace Receipt-Chain Recovery

**Date:** 2026-08-11
**Status:** ACCEPTED — OWNER RECOVERY-RESOLUTION REMEDIATION 2026-08-11
**Authority classification:** `M3_2_CROSS_NAMESPACE_RECEIPT_CHAIN_RECOVERY_ACCEPTED`
**Type:** Owner **remediation** record with an accompanying implementation. It records the owner's
acceptance of the **T7** live SIC continuation, the owner's adjudication of two findings that
continuation exposed, and the bounded offline correction of the receipt-chain **resolver**. It is
**offline governance and implementation only.**

**Grants no live authority.** No SEC request was made, no network switch changed, no CompanyFacts
access was opened, no acquisition was invoked, no M3.2B work was authorized, and **Gate H is not
passed and is not claimed by this record.** The single live grant of the T7 packet is exhausted, and
no further SEC request is authorized.

**Amends:** nothing in place. Decisions 001–062 remain **byte-unchanged**.
**Narrowly supersedes:** exactly one current-state statement, and nothing else — that the Decision
062 §21 one-shot audit-projection rebuild authority is available. That authority was **consumed by a
refused invocation** and is not reissued; §9 below mints a separate new one-use authority in its
place.

**Preserves unchanged:** the cumulative M3.2A ceiling **801**; the successor plan at SHA-256
`f77e003ccc0ed8f9c0e55065b3c211aa5e33c7abf86cc71cbe66d427611d890a`; the frozen predecessor plan at
`19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68`; the accepted 70-quarter coverage,
as-of date, calendar year, and evidence manifest; every route's `A_reachable`; the live source
registry `m2.2-source-registry/1.1`; the historical run's permanent non-resumability; the immutable
T6 receipt and its failed SIC observation; and every leakage, filing-body, and CompanyFacts/Frames
prohibition.

**Documentary lag preserved deliberately.** The accepted contract
[`Milestones/contracts/m3_2.md`](../../Milestones/contracts/m3_2.md) §6 still names
`m2.2-source-registry/1.0`, and remains superseded on that point by Decision 062 §5 rather than
edited. Reconciling that text — and the receipt-version wording alongside it — is reserved for the
final M3.2 closeout governance pass **after** Gate H owner acceptance, and is expressly not mixed
into this record.

---

## 1. Accepted entry state — the T7 live continuation

The owner accepts the T7 live continuation itself, under the token
`M3_2_T7_ONE_REQUEST_SIC_LIVE_CONTINUATION_OWNER_ACCEPTED`.

| Fact | Value |
|---|---|
| Run | `m3-2-acquisition-b6f8bc7f48b94e6080038db575b204e5` |
| State | `completed` |
| Logical requests | 1 |
| Physical attempts | 1 |
| Source | `sec_sic_code_list` |
| HTTP | 200 |
| Successor identities satisfied | **75 / 75** |
| Predecessor identities replayed | **0** |
| Cumulative physical attempts | **77 / 801** |
| Network window | **CLOSED** |
| Predecessor T6 run | unchanged / `failed` |
| Old-path SIC 301 observation | preserved |
| New SIC observation | `6e9d92c859bc48faa6c1c5e47c36fd8e` |
| T7 receipt | `runs/m3_2_decision_062_sic_continuation/execution_receipt.json` |
| T7 receipt SHA-256 | `ae8ace5dc62155c9dca395af238290b0bb5b99dc4e3f1741e3d8ff1c9ab9c3dd` |
| T7 receipt id | `7d72a5501f66d36af9024b80a64060668da315b8880fb5add028917d36ad12e1` |

**No further SEC request is authorized.**

## 2. Gate H state at entry

The Gate H candidate result at entry is **FAIL**, and for exactly one reason:

| Surface | Count |
|---|---|
| Authoritative SQLite observations | **77** |
| Audit projection rows | **76** |

The existing 76-row projection has already been proved a deterministic **valid prefix** of the 77
authoritative SQLite observations. The only missing projection row is the successful T7 SIC
observation. There is **no** corruption, divergence, missing raw object, missing lineage, unresolved
recovery event, network issue, or request-accounting issue, and every other applicable Gate H check
passed.

## 3. Accepted finding — cross-namespace receipt-chain resolution

The owner accepts the newly exposed implementation defect under the token
`M3_2_T7_CROSS_NAMESPACE_RECEIPT_CHAIN_RESOLUTION_FINDING_OWNER_ACCEPTED`.

**Root cause.** The accepted `m3 recover` path resolved a predecessor receipt by looking inside the
**head receipt's own directory** for `receipt-<predecessor_receipt_id>.json`. That assumption is
incompatible with the accepted per-run receipt namespaces the acquisition commands actually use:
`--receipt-out` has always let an operator name a receipt's location, and the accepted M3.2
convention gives each run its own namespace holding one `execution_receipt.json`.

T7 is the **first real receipt chain to span two namespaces**, and so the first to expose the
incompatibility:

| Role | Path |
|---|---|
| HEAD receipt | `runs/m3_2_decision_062_sic_continuation/execution_receipt.json` |
| Predecessor receipt | `runs/m3_2a_clean_carry_in/execution_receipt.json` |
| Predecessor id recorded by HEAD | `37dd811497d4a57e8b911917ed6c0426a22f443c3ddd5aeba8d4da3e076f6a7c` |

This is a **recovery-operator defect**, not evidence damage. The projection is a valid prefix, the
receipts are intact, and the chain is intact; only the locator could not see across the namespace
boundary. The correction is therefore confined to **where a predecessor may be found**, and changes
nothing about **what counts as one**.

## 4. Owner ruling — the acquisition projection flush is not required

Recorded under `M3_2_ACQUISITION_PROJECTION_FLUSH_OWNER_ADJUDICATED_NOT_REQUIRED`.

M3.2 acquisition is **not** modified to call `flush_projection`, because:

- SQLite is the authoritative source, and the audit JSONL is derived;
- the existing deterministic recovery action already reconstructs the projection from SQLite;
- live acquisition should not gain another derived-artifact write-and-failure boundary merely to
  avoid a post-network deterministic synchronization;
- Gate H already requires projection consistency before acceptance.

The normative lifecycle is therefore:

```
LIVE ACQUISITION
  → CLOSE NETWORK
  → VERIFY AUTHORITATIVE SQLITE
  → DETERMINISTIC PROJECTION SYNCHRONIZATION IF NEEDED
  → GATE H
```

**MAJ-2 of the T7 report is owner-adjudicated as NOT a separate implementation defect for M3.2**,
and acquisition is not edited to address it.

## 5. The corrected resolution semantics

A predecessor is located by its **recorded identity**, inside the governed evidence root, among the
**accepted receipt artifact locations only**. The mechanism is the minimum one compatible with the
existing conventions, and it is deterministic end to end.

**Search order**, fixed:

1. `<head receipt's directory>/receipt-<id>.json` — the existing accepted same-directory
   content-derived behaviour, tried **first** and semantically unchanged, so no chain that resolved
   before this record resolves differently after it;
2. `receipts/receipt-<id>.json` — the receipt spec §7.1 directory dedicated to receipts;
3. `runs/<namespace>/` — each run namespace, **sorted by name**, descending exactly one level.

Within each directory only the **two accepted receipt filenames** are probed: the content-derived
`receipt-<id>.json`, and the accepted per-run `execution_receipt.json`. Arbitrary JSON is never
treated as a receipt, and the search never recurses into the raw store.

**Required properties, all implemented:**

| # | Property | Behaviour |
|---|---|---|
| 1 | The explicitly supplied head receipt path remains authoritative for the chain head | unchanged |
| 2 | A predecessor is resolved by recorded `receipt_id`, never by a caller-supplied replacement | enforced |
| 3 | Resolution is confined beneath the accepted governed evidence root | enforced |
| 4 | Existing same-directory/content-derived behaviour remains supported | tried first, unchanged |
| 5 | Cross-namespace discovery searches only accepted receipt locations/patterns | two names, two roots |
| 6 | Every candidate passes the normal loader, schema, canonical-form, and identity validation | `inspect_receipt` |
| 7 | The loaded receipt's validated `receipt_id` must equal the requested id exactly | enforced |
| 8 | Zero valid matching candidate | refuse / `UNDETERMINED` |
| 9 | More than one **distinct** valid candidate | refuse (see below) |
| 10 | Symlink or path-escape candidate | refuse |
| 11 | Receipt-chain loop | refuse / `UNDETERMINED` |
| 12 | Predecessor link inconsistency | refuse |
| 13 | Receipt contents remain immutable | read-only; proved by test |
| 14 | No network | no transport constructed; proved by test |
| 15 | Resolution order is deterministic | fixed order, sorted namespaces |

**No canonical receipt copy is created to satisfy the old resolver.** Nothing is copied, renamed,
moved, rewritten, or synthesized.

### 5.1 Why byte-identical aliases resolve rather than refuse

Requirement 9 refuses more than one **distinct** valid candidate unless the accepted identity
semantics prove the files are byte-identical aliases and existing conventions already permit
aliases. Both hold, by construction rather than by concession:

- `receipt_id` is `SHA256(canonical bytes with receipt_id omitted)` (spec §13), and §14 re-checks at
  every inspection that the identity **recomputes**. Two files that both validate under one
  `receipt_id` therefore cannot differ in any field — same identity forces same preimage forces same
  canonical bytes.
- Spec §7.2 already treats a byte-identical rewrite as a **collision by identity** that succeeds
  unchanged, so an identical duplicate is an established non-conflict.

The implementation does not rely on that argument alone: it compares the candidates' canonical bytes
and returns the first in search order **only** when they are identical. Anything else is refused.
Because valid receipts cannot differ under one identity, the refusal branch is a **backstop against a
future weakening of identity validation** rather than a reachable state — and it is proved
load-bearing by a test that substitutes the loader (§7).

The **receipt-chain loop** guard is unreachable for the same structural reason: a `receipt_id` is the
digest of a preimage that *includes* `recovery_predecessor_receipt_id`, so a cycle would require each
receipt to hash a value derived from the other's hash. It is likewise retained as a backstop and
likewise proved load-bearing.

## 6. Exact implementation surface

| Path | Change |
|---|---|
| `src/disclosure_drift/m3/receipt.py` | new `resolve_predecessor_receipt`, `ReceiptChainResolutionError`, `content_derived_receipt_name`, `OPERATOR_RECEIPT_FILENAME`, `RUN_NAMESPACE_DIRNAME`, and the symlink/containment guards |
| `src/disclosure_drift/m3/recovery.py` | `walk_receipt_chain` and `inspect_recovery_state` take an optional `evidence_root` and locate predecessors through the shared resolver |
| `src/disclosure_drift/m3/acquisition.py` | `propose_continuation` and `apply_recovery_action` thread `evidence_root` through to the inspection |
| `src/disclosure_drift/cli.py` | `show-receipt`, `recovery-state`, `acquire --show-scope`, `acquire --resume-from`, and `recover` supply the resolved evidence root; `_resolve_receipt_chain` delegates location to the shared resolver |

The resolver lives in `receipt.py` because that module already owns receipt naming, loading, and the
`receipts/` directory, and sits below both chain walkers in the import graph. The `evidence_root`
parameter defaults to `None`, which restricts the search to step 1 — so every existing caller and
every existing test keeps exactly its previous behaviour, and only a caller that can prove a governed
root gains cross-namespace discovery.

**No migration. No source-registry change. No request-plan change. No SEC client change. No parser
change. No catalog schema change. No acquisition-engine change for projection flushing.**

## 7. Evidence

Thirty-one tests were added across the closest existing suites — `tests/unit/test_m3_receipt.py`,
`tests/unit/test_m3_recovery.py`, and `tests/integration/test_m3_cli.py` — covering every required
case: the unchanged same-directory chain; the real-shaped cross-namespace chain; exact identity
equality; a nonexistent predecessor; an unrelated receipt in another namespace ignored; malformed
candidates; ambiguity; symlinks; path escape; a predecessor cycle; the T7-shaped two-receipt chain
reaching the normal recovery inspection; receipt non-mutation; and the absence of any network
construction.

Each load-bearing guard was **mutation-tested**: disabling the identity check, the ambiguity check,
the symlink walk, the root-containment check, or the loop guard each fails at least one test that
otherwise passes. Every cross-namespace assertion is paired with a **negative control** using the
identical fixture with the evidence root withheld, so the fix is proved load-bearing rather than
incidentally satisfied.

Full validation: `ruff check`, `ruff format --check`, `mypy src`, the complete `pytest` suite, the
SQLite check, the secret scan, the repository-hygiene check, and `git diff --check` — all green, with
**no SEC request**.

## 8. What this record does not do

- It does **not** pass or claim Gate H.
- It does **not** authorize any SEC request, network enablement, or live acquisition.
- It does **not** authorize M3.2B, M3.3, a snapshot, a selection, a manifest, or a tag.
- It does **not** edit the accepted contract, the source registry, the request plan, the SEC client,
  the parsers, or the catalog schema.
- It does **not** reissue the Decision 062 §21 rebuild authority.

## 9. One-use audit-projection rebuild authority

The Decision 062 §21 rebuild authority was **consumed by a refused invocation** and is not reissued.
The owner mints a separate new one-use authority:

> `M3_2_DECISION_063_ONE_SHOT_AUDIT_PROJECTION_REBUILD_OWNER_AUTHORIZED`

**Exercisable only** after the corrected implementation is committed and pushed, the private-state
preflight passes unchanged, and the corrected read-only receipt-chain inspection resolves the T7 head
to its predecessor across namespaces. It authorizes **exactly one** invocation of the existing
accepted action:

```
m3 recover --action rebuild-projection
```

against the T7 run, the T7 head receipt, the successor plan, the current operational catalog, and
`census_source_observations.jsonl`. **No other recovery action.** No direct invocation of a private
primitive. No fabricated or copied receipt. No manual edit of `projected_to_audit`.

**Required result:** authoritative SQLite observations **77**; projection rows **77**;
`projected_to_audit = 1` for all **77**; projection identity and order an exact deterministic
reconstruction from SQLite; the recovery event recorded and its state resolved; receipt files, raw
objects, and lineage unchanged; attempt accounting **77 / 801** unchanged; T6 `failed` and T7
`completed` unchanged; network disabled. **Any failure is a stop.**

## 10. Next action

Re-run the **transition-aware** Gate H evidence evaluation used at T7 — not the non-transition-aware
`m3 reconcile-requests`. If every previously passing item remains `PASS` and the projection reads
**77 / 77**, emit `M3_2_GATE_H_EVIDENCE_COMPLETE_READY_FOR_OWNER_ACCEPTANCE`. The **final owner Gate H
acceptance token is not emitted by this record or by the session implementing it**; Gate H acceptance
remains an owner act.
