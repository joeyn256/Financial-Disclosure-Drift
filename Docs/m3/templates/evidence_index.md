# TEMPLATE — Public Evidence Index

**This file is a blank template. No Milestone 3 evidence exists, so no row below is filled.**
Copy it, fill it as evidence accumulates, and keep the completed copy **tracked in the repository** —
this is the one Milestone 3 evidence artifact that is public by design.

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
| Index version | `_______` |
| Owner | `_______` |
| Last updated (UTC) | `_______` |
| Private evidence root | **not recorded here, by design** |
| Backup confirmed | `YES` / `NO` — a private root with no separate owner-controlled backup is a single point of loss |

## 4. The index

| Ref | Artifact type | Phase | Status | SHA-256 | Date (UTC) | Note |
|---|---|---|---|---|---|---|
| `EV-____-___` | `_______` | `_______` | `_______` | `_______` | `_______` | `_______` |

**Artifact types**, matching the frozen template set and the run artifacts:

`request_budget` · `gate_f_checklist` · `gate_h_checklist` · `schema_drift_incident` ·
`interrupted_run_recovery` · `real_snapshot_evidence_packet` · `root_hash_approval_packet` ·
`execution_receipt` · `rehearsal_evidence_report` · `request_plan` · `recovery_state_report`

**Phases:** `M3.1A` · `M3.1B` · `M3.2A` · `M3.2B` · `M3.3A` · `M3.3B` · `M3.4A` · `M3.4B` · `M3.5`

**Statuses:** `DRAFT` · `COMPLETE` · `OWNER_SIGNED` · `SUPERSEDED` · `WITHDRAWN`

## 5. Expected coverage

Every phase must produce at least the artifacts below, and each must appear here once complete. A
missing entry for a completed phase is an M3.5 stop condition.

| Phase | Expected artifacts |
|---|---|
| **M3.1A** | `rehearsal_evidence_report` (A1–A12); one `execution_receipt` per rehearsal command |
| **M3.1B** | two `request_plan` entries with identical plan hashes; `request_budget` (M3.2A window); `gate_f_checklist`; one `execution_receipt` per dry run |
| **M3.2A** | one `execution_receipt` per live command; `interrupted_run_recovery` and `schema_drift_incident` if either occurred |
| **M3.2B** | `request_budget` (M3.2B window, derived and separately approved); `request_plan`; one `execution_receipt` per live command; `gate_h_checklist` integrating both windows |
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
| `EV-____-___` | `EV-____-___` | `_______` | `_______` |

## 7. Referencing evidence from a public decision

**A public acceptance decision may cite an entry's reference identifier and its SHA-256.** That is
sufficient to bind the decision to an exact artifact without publishing it.

**It may not quote the artifact's contents**, and specifically may not expose an unpublished root or
any substantive row — no matter how a later session phrases the request.

## 8. Owner attestation

| Field | Value |
|---|---|
| Owner | `_______` |
| Date (UTC) | `_______` |
| Every listed digest verified against its private artifact | `YES` / `NO` |
| Private evidence root backed up separately | `YES` / `NO` |
| No prohibited content in this index | `YES` / `NO` |
| Signature or recorded acceptance reference | `_______` |
