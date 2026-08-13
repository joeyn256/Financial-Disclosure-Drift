# Public Evidence Index — living instance

**This is the authoritative completed public evidence index, kept tracked in the repository** —
the one Milestone 3 evidence artifact that is public by design. It is the recording destination
the M3.1 contract §6, master plan §§12.1, 12.3, and M3.1 §30, and the operator runbook all name.
Rows accumulate as evidence completes; the index is append-only (§6).

**Purpose:** to make the existence, phase, status, and integrity of every private evidence artifact
publicly verifiable **without publishing any of its content**.
**Phase:** all — M3.1 through M3.5.
**Controlling records:** [Decision 027](../../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§10.1; [`milestone_03_master_plan.md`](../../../Milestones/milestone_03_master_plan.md) §12.

---

## 0. The two layers

**The repository is public. Completed operational evidence is not committed to it.**

| Layer | Contents | Location |
|---|---|---|
| **Public** | Blank templates; planning and governance records; the limitations register; non-sensitive status and navigation; **and this index** | Tracked in the repository |
| **Private** | Execution receipts; request budgets; Gate F and Gate H packets; interrupted-run records; schema-drift records; real-snapshot evidence packets; root-approval packets; raw objects; catalogs; candidate, selection, reserve, and manifest artifacts; **every unpublished governed identity** | An owner-controlled private evidence root **outside** the repository |

**This index is the bridge.** It records that an artifact exists, what kind it is, which phase
produced it, whether it passed, and its exact SHA-256 — so a reviewer can verify the artifact they
are shown privately is the artifact the public record commits to.

## 1. What may and may not appear here

**May appear:**

- artifact type, phase, and status;
- the completed artifact's own **SHA-256**;
- a **non-sensitive reference identifier** — a short opaque label the owner assigns, e.g.
  `EV-M31A-001`. It is not a path, not a filename, and not derived from any governed value;
- the date recorded, and the owner or operator who recorded it;
- a one-line non-sensitive note.

**May never appear:**

| Prohibited | Why |
|---|---|
| **An absolute private path** | It identifies a machine and a person, and `scripts/check_repo_hygiene.py` refuses it |
| **Any unpublished `root_manifest_sha256`** | Publishing an unapproved or unpublished root is exactly what the two-layer model prevents |
| **`manifest_id`, `selection_result_sha256`, `snapshot_id`, or any component digest** | Governed identities are private until publication is separately authorized |
| **Any substantive row** | Candidate, selected, reserve, quota, or disposition content |
| **The full SEC identity, a credential, a token, a cookie, or an authorization header** | Never recorded anywhere, public or private |
| **A raw response body, filing text, or an outcome value** | Prohibited at this stage entirely |
| **A receipt's contents** | Only its `receipt_id` and its own SHA-256 |

**An artifact's SHA-256 is safe to publish; the artifact is not.** That asymmetry is the whole point
of the index.

## 2. How the operator records an entry

```bash
shasum -a 256 <private-evidence-file>
```

Copy **only** the digest into the table. Assign the next reference identifier in sequence. Record the
type, phase, and status. **Do not record the path.**

**Verifying an entry later:** re-run `shasum -a 256` against the private artifact and compare to the
digest recorded here. A mismatch means the artifact changed after it was indexed, which is a
stop-and-report condition — completed evidence is immutable.

## 3. Identification

| Field | Value |
|---|---|
| Index version | 1.0 |
| Owner | Joseph Nihill (project owner) |
| Last updated (UTC) | 2026-08-03 |
| Recorder | Claude Code operator session (owner-authorized), 2026-08-03 |
| Private evidence root | **not recorded here, by design** |
| Backup confirmed | YES — same-device snapshots of the private evidence root exist through the after-step-13-token state, each verified file-by-file by SHA-256; they protect against accidental deletion only, and a separate owner-controlled off-device backup remains an owner matter |

## 4. The index

| Ref | Artifact type | Phase | Status | SHA-256 | Date (UTC) | Note |
|---|---|---|---|---|---|---|
| `EV-M31A-001` | `rehearsal_evidence_report` | M3.1A | COMPLETE | `6308576a0a7df33813239f753b31b86754f3908d63d73e6521682db06a59e1e0` | 2026-08-03 | A1–A12 acquisition rehearsal report; all twelve scenarios PASS; zero actual network counts |
| `EV-M31A-002` | `execution_receipt` | M3.1A | COMPLETE | `ea1f4be2c136827ac5d865eea0fabf73f0f716802e2ee8cd23aedf1965dbc81b` | 2026-08-03 | rehearsal receipt (`receipt_id` `1c1980429833e41f6eaf07d3df7fb5a780daab2ffe291d9a67858821a1a618d6`); actual counts 0 |
| `EV-M31B-001` | `request_plan` | M3.1B | COMPLETE | `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` | 2026-08-03 | first zero-request M3.2A plan; hash identical to `EV-M31B-002` |
| `EV-M31B-002` | `request_plan` | M3.1B | COMPLETE | `19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68` | 2026-08-03 | second dry run; byte-identical to `EV-M31B-001` |
| `EV-M31B-003` | `execution_receipt` | M3.1B | COMPLETE | `d7f602d8a537c925483cbb9b5021ca0313eb3288d26dcb7759aa9b1843f4f149` | 2026-08-03 | first planning receipt; dry run; actual counts 0 |
| `EV-M31B-004` | `execution_receipt` | M3.1B | COMPLETE | `ff116259d5f129aba94093bd0516b14fdbb4a5517538a2c29d59240823573111` | 2026-08-03 | second planning receipt; dry run; actual counts 0 |
| `EV-M31B-005` | `request_budget` | M3.1B | OWNER_SIGNED | `2d453e0b6d1b65b0d474d454e4fa1540fb615b1c78572956acdb2cfcb17cab3f` | 2026-08-03 | M3.2A window; owner-approved hard request ceiling 801, recorded 2026-08-03 |
| `EV-M31B-006` | `gate_f_checklist` | M3.1B | OWNER_SIGNED | `34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc` | 2026-08-03 | result PASS; owner-signed 2026-08-03; the step-13 readiness token is not emitted and Gate F is not begun |

**Artifact types**, matching the frozen template set and the run artifacts:

`request_budget` · `gate_f_checklist` · `gate_h_checklist` · `schema_drift_incident` ·
`interrupted_run_recovery` · `real_snapshot_evidence_packet` · `root_hash_approval_packet` ·
`execution_receipt` · `rehearsal_evidence_report` · `request_plan` · `recovery_state_report` ·
`frozen_object_identity_set` · `derived_reference_set` · `reconciliation_report`

**The last three were added by accepted
[Decision 047](../../Decisions/decision_047_m3_2_t4_operational_preflight_authorization.md) §4**,
discharging the **F4** gate that accepted Decision 032 §6.4 opened and that Decisions 034, 035, 039,
040, 042, 045, and 046 each carried forward to "no later than T4". They name, in order: the frozen
M3.2A bootstrap raw-object identity set produced at the between-windows freeze; the dependent
reference set derived from those frozen objects, which is distinct from the M3.2B `request_plan` it
feeds; and the private deterministic plan-to-catalog reconciliation report, including its
required-absence enumeration. **No fourth type was added**, and no
`operational_preflight_attestation` type exists: T4 preflight evidence stays private and is bound by
SHA-256 through the governance ledger and the owner decision rather than indexed here — the same
treatment the Gate F readiness token received (see the timing note in §8).

**Phases:** `M3.1A` · `M3.1B` · `M3.2A` · `M3.2B` · `M3.3A` · `M3.3B` · `M3.4A` · `M3.4B` · `M3.5`

**Statuses:** `DRAFT` · `COMPLETE` · `OWNER_SIGNED` · `SUPERSEDED` · `WITHDRAWN`

## 5. Expected coverage

Every phase must produce at least the artifacts below, and each must appear here once complete. A
missing entry for a completed phase is an M3.5 stop condition.

| Phase | Expected artifacts |
|---|---|
| **M3.1A** | `rehearsal_evidence_report` (A1–A12); one `execution_receipt` per rehearsal command |
| **M3.1B** | two `request_plan` entries with identical plan hashes; `request_budget` (M3.2A window); `gate_f_checklist`; one `execution_receipt` per dry run |
| **M3.2A** | one `execution_receipt` per live command; `reconciliation_report`; `frozen_object_identity_set` (the between-windows freeze); `interrupted_run_recovery` and `schema_drift_incident` if either occurred; `recovery_state_report` if a recovery inspection was recorded |
| **M3.2B** | `derived_reference_set` (derived from the frozen M3.2A objects); `request_budget` (M3.2B window, derived and separately approved); `request_plan`; one `execution_receipt` per live command; `gate_h_checklist` integrating both windows |
| **M3.3A** | `rehearsal_evidence_report` (E1–E8); one `execution_receipt` per rehearsal command |
| **M3.3B** | `real_snapshot_evidence_packet`; one `execution_receipt` per command |
| **M3.4A** | the entry point's synthetic-catalog validation record |
| **M3.4B** | `root_hash_approval_packet`; the re-derivation `execution_receipt` |
| **M3.5** | the integrated acceptance record |

## 6. Superseded entries

A corrected artifact is a **new** entry with a **new** reference identifier and a **new** digest. The
superseded entry stays in the table, marked `SUPERSEDED`, naming what replaced it.

**Rows are never deleted and never edited in place.** The index is append-only, for the same reason
raw data is (CLAUDE.md rule 6).

| Ref | Superseded by | Reason | Date (UTC) |
|---|---|---|---|
| — | — | none — no entry has been superseded | — |

## 7. Referencing evidence from a public decision

**A public acceptance decision may cite an entry's reference identifier and its SHA-256.** That is
sufficient to bind the decision to an exact artifact without publishing it.

**It may not quote the artifact's contents**, and specifically may not expose an unpublished root or
any substantive row — no matter how a later session phrases the request.

## 8. Owner attestation

| Field | Value |
|---|---|
| Owner | Joseph Nihill, project owner acting through the ChatGPT owner decision |
| Date (UTC) | 2026-08-03 |
| Every listed digest verified against its private artifact | YES — owner attestation of 2026-08-03 (instrument items 1–2 below); each digest also recomputed by the recording operator session on 2026-08-03 |
| Private evidence root backed up separately | YES — same-device verified snapshots (see §3); off-device backup remains an owner matter |
| No prohibited content in this index | YES — owner attestation of 2026-08-03 (instrument items 3–4 below); digests, types, phases, statuses, dates, and non-sensitive notes only |
| Signature or recorded acceptance reference | ChatGPT owner evidence-index attestation dated 2026-08-03, bound to public governance commit 0334294bd420a829033094080a13e4df900da078 and signed Gate F checklist SHA-256 34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc. This is a transparent recorded owner acceptance reference, not a handwritten, cryptographic, or third-party digital signature. |

**Recorded owner attestation instrument (verbatim, received 2026-08-03):**

```text
OWNER_EVIDENCE_INDEX_ATTESTATION: APPROVED
The project owner has reviewed the M3.1A and M3.1B public evidence-index entries
recorded in `Docs/m3/templates/evidence_index.md`.
The owner attests that:

1. Each indexed row refers to an accepted private evidence artifact.
2. Each listed SHA-256 matches the accepted artifact identity.
3. The index contains only permitted non-sensitive metadata.
4. No private evidence path, SEC contact identity, credential, response body,
or private receipt content is disclosed.
5. The two request-plan rows intentionally carry the same SHA-256 because two
independent planning executions produced byte-identical canonical plans.
6. The request-budget row is bound to the owner-approved hard request ceiling
of 801.
7. The Gate F checklist row is bound to the signed checklist SHA-256
34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc
and checklist result PASS.
8. At the time of this attestation, the Decision 029 §12 step-13 readiness
token has not been emitted or recorded.
9. This attestation does not authorize live SEC access, begin Gate F, finally
accept M3.1, or authorize M3.2 execution.

Owner:
Joseph Nihill, project owner acting through the ChatGPT owner decision
Date:
2026-08-03
Recorded acceptance reference:
ChatGPT owner evidence-index attestation dated 2026-08-03, bound to public
governance commit 0334294bd420a829033094080a13e4df900da078 and signed Gate F
checklist SHA-256
34fc0567dd31b75b83d8bb12f31e172c04074bd1a0a3b1487b0461d170339fbc.
This is a transparent recorded owner acceptance reference, not a handwritten,
cryptographic, or third-party digital signature.
```

**Timing note.** Instrument item 8 was true at attestation time; the Decision 029 §12 step-13
readiness token was recorded later the same day under the owner's separate step-13 authorization.
The current token state is carried by the governance ledger (`Milestones/STATUS.md`), not by this
index: the index vocabulary defines no readiness-token artifact type, so no token row is added.

**Ledger-not-index practice, and its M3.2 disposition (accepted
[Decision 065](../../Decisions/decision_065_m3_2_final_acceptance_and_closeout.md) §8,
2026-08-13).** The treatment above is this repository's general practice, not a one-off: where an
artifact's identity is already bound by SHA-256 through an accepted decision record, that decision
is the durable public binding and no index row is added. The same treatment was applied to the T4
preflight attestation, which has no `operational_preflight_attestation` type (see §4).

**M3.2 follows that practice, deliberately.** This index therefore carries **no M3.2 rows**, and the
§5 expected-coverage rows for `M3.2A` and `M3.2B` are **not** an outstanding obligation:

- **M3.2A private evidence identity and provenance are discoverable** through accepted
  [Decision 062](../../Decisions/decision_062_m3_2_terminal_failure_and_sic_endpoint_remediation.md),
  [Decision 063](../../Decisions/decision_063_m3_2_cross_namespace_receipt_chain_recovery.md),
  [Decision 064](../../Decisions/decision_064_m3_2_final_recovery_semantics_and_precloseout_hardening.md),
  Decision 065, and the accepted M3.2 contract — which between them bind the run identities, the
  receipt identities, the plan hashes, the carry-in authority digest, and the object and attempt
  counts, without publishing any artifact's contents.
- **M3.2B was not executed and is not required** for the accepted M3.2 completion state
  (Decision 065 §4), so it produced no artifact to index.

**No competing indexing convention is created by this note**, no row is added, edited, deleted, or
superseded, the append-only rule (§6) is untouched, and nothing above discloses a private path, an
SEC identity, a credential, a response body, or any prohibited content.
