# Milestone 3 — Execution-Receipt Specification

**Status:** specification only. **No runtime code and no database table is created by this document.**
**Applies to:** every Milestone 3 command that runs against real inputs, and every live command
without exception.
**Controlling record:** [Decision 027](../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§§9, 17, 18, 19.
**Plan:** [`Milestones/milestone_03_master_plan.md`](../../Milestones/milestone_03_master_plan.md).

---

## 0. The one rule that governs everything below

> **An execution receipt is operational evidence. It is never an input to any governed identity.**
>
> No receipt, no receipt digest, no receipt identifier, and no field of any receipt may enter,
> alter, or be committed by `snapshot_id`, any candidate-table identity, `selection_input_sha256`,
> `selection_run_id`, `selection_result_sha256`, any of the eight S6 component digests,
> `root_manifest_sha256`, or `manifest_id`.

This is restated at §3, §8, §10, §11, and §13, deliberately. It is the property that keeps the
research artifact reproducible: **the moment a timestamp or a request count reaches a digest, the
manifest stops being a reproducible derivation and becomes a recording of one particular execution.**

The relationship is strictly one-way. **A receipt may reference a governed identity. A governed
identity may never reference a receipt.**

## 1. Why receipts exist

Milestone 2 could answer "what does the code do" from the code. Milestone 3 must also answer "what
did *that run* actually do" — how many requests it placed, which classes of response it saw, whether
it drifted, where it stopped, and whether it resumed from something. Today that answer lives in a
terminal scrollback, which is not evidence.

A receipt is the smallest durable artifact that answers it, carrying **counts, classifications,
versions, identifiers, and statuses** — the facts an auditor needs and an attacker cannot use.

## 2. Scope

**One receipt per command invocation**, mandatory for:

- every M3.1 rehearsal command (`invocation_mode = "rehearsal"`);
- every M3.1 zero-request dry run (`invocation_mode = "dry_run"`);
- every M3.2 live acquisition command (`invocation_mode = "live"`);
- every M3.3 offline execution command (`invocation_mode = "offline_execution"`);
- every M3.4 approval-supporting command (`invocation_mode = "approval"`).

**A live command that produces no receipt is an incomplete command, and its phase does not pass.**

Receipts are **not** produced for read-only inspection helpers that change nothing and touch no
catalog — those are covered by the receipt of the command whose output they inspect.

## 3. What a receipt is not

- **Not an approval.** A receipt records that a command ran. Approval is the owner's explicit,
  exact-hash-specific decision, recorded in
  [`templates/root_hash_approval_packet.md`](templates/root_hash_approval_packet.md).
- **Not a manifest.** The manifest is a governed artifact bound by the root. A receipt is not bound
  by anything governed and binds nothing governed.
- **Not a substantive record.** It carries no candidate row, no selected row, no reserve row, no
  filing text, and no outcome value.
- **Not an input to any digest.** Restating §0: **no receipt field, and no receipt digest, enters any
  accepted S5 or S6 identity.**
- **Not a log.** Logs are operational prose; a receipt is a fixed, versioned, machine-readable
  schedule.

## 4. Permitted fields

The complete permitted set. A field not listed here is not added without a new accepted decision.

**Every field carries exactly one classification, and there is no "optional" class:**

| Class | Meaning |
|---|---|
| **`R`** — required in all modes | Must be present in every receipt, whatever the invocation mode |
| **`C:<modes>`** — conditionally required | Must be present in the named modes; **omitted** in every other mode |
| **`P:<modes>`** — prohibited | Must be **absent** in the named modes; presence is a fail-closed validation error |

A field that is neither required nor conditionally required for the current mode is **omitted**, never
rendered as `null` or a placeholder. Validation (§14) enforces exactly this table — v0.1 described
nearly every field as optional and then validated several as mandatory, which is corrected here.

**The five invocation modes:** `rehearsal`, `dry_run`, `live`, `offline_execution`, `approval`.

### 4.1 Identity and provenance of the receipt itself

| Field | Type | Class | Meaning |
|---|---|---|---|
| `receipt_schema_version` | string | **`R`** | The receipt schema this document version defines (§12) |
| `receipt_id` | string | **`R`** | **The single integrity identity.** `SHA256(canonical receipt bytes with `receipt_id` omitted)` — see §13. Never a random value, never a timestamp |
| `command_name` | string | **`R`** | The invoked command, e.g. `m3 acquire` |
| `command_version` | string | **`R`** | The command's declared version, independent of the package version |
| `phase` | string | **`R`** | One of `M3.1A`, `M3.1B`, `M3.2A`, `M3.2B`, `M3.3A`, `M3.3B`, `M3.4A`, `M3.4B`, `M3.5` |
| `invocation_mode` | string | **`R`** | One of `rehearsal`, `dry_run`, `live`, `offline_execution`, `approval` |
| `configuration_fingerprint` | string | **`R`** | A digest over the effective non-secret configuration. **Never the configuration itself, and never any resolved secret** |

### 4.2 Policy and definition versions

| Field | Type | Class | Meaning |
|---|---|---|---|
| `source_registry_version` | string | **`C:`** `dry_run`, `live` | `M22_SOURCE_REGISTRY_VERSION` in force |
| `quota_policy_version` | string | **`C:`** `offline_execution` | `PILOT_QUOTA_POLICY_VERSION` in force |
| `joint_selector_policy_version` | string | **`C:`** `offline_execution` | `PILOT_JOINT_SELECTOR_POLICY_VERSION` in force |
| `replacement_signature_policy_version` | string | **`C:`** `offline_execution` | `PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION` in force |
| `manifest_hash_policy_version` | string | **`C:`** `offline_execution`, `approval` | `PILOT_MANIFEST_HASH_POLICY_VERSION` in force |
| `selection_input_schema_version` | string | **`C:`** `offline_execution` | `ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` in force |
| `parser_versions` | object | **`C:`** `live`, `offline_execution` | Parser identifier to version, for every parser the command used |
| `cohort_definition_digest` | string | **`C:`** `offline_execution` | A digest over the frozen cohort definitions, where the command consumes them. **Recorded as a version fact, and bound to nothing** |
| `migration_chain_head` | string | **`R`** | The highest applied migration name |

### 4.3 Timing

| Field | Type | Class | Meaning |
|---|---|---|---|
| `started_at_utc` | string | **`R`** | RFC 3339 UTC, `Z` suffix |
| `completed_at_utc` | string | **`R`** | RFC 3339 UTC, `Z` suffix |
| `elapsed_seconds` | number | **`R`** | Wall-clock duration |

**Every timestamp here is operational.** None enters a governed identity, exactly as Decision 013 §7
already excludes `generated_at` from the manifest content hash.

### 4.4 Request plan and budget

| Field | Type | Class | Meaning |
|---|---|---|---|
| `acquisition_window` | string | **`C:`** `live` | `M3.2A` or `M3.2B`. **Each window has its own plan, budget, and ceiling** |
| `request_plan_id` | string | **`C:`** `dry_run`, `live` | That window's plan identity |
| `request_plan_sha256` | string | **`C:`** `dry_run`, `live` | The plan hash the run consumed |
| `approved_request_ceiling` | integer | **`C:`** `dry_run`, `live` | The owner-approved hard ceiling for **that window** |
| `planned_logical_request_count` | integer | **`C:`** `dry_run`, `live` | From that window's approved plan |
| `maximum_physical_attempt_count` | integer | **`C:`** `dry_run`, `live` | From that window's approved plan, **derived per route from the implemented state machine** — never from an asserted constant |
| `planned_per_route` | object | **`C:`** `dry_run`, `live` | `source_id` to planned unique logical requests |

### 4.5 Actual execution accounting

**These fields record actual NETWORK activity and nothing else.**

| Field | Type | Class | Meaning |
|---|---|---|---|
| `actual_logical_request_count` | integer | **`R`** | Distinct logical **network** requests issued. **Must be `0` in `rehearsal`, `dry_run`, `offline_execution`, and `approval`** |
| `actual_physical_attempt_count` | integer | **`R`** | HTTP requests actually placed on the wire, including redirect hops, retries, and controlled post-cooldown requests. **Must be `0` in `rehearsal`, `dry_run`, `offline_execution`, and `approval`** |
| `actual_per_route` | object | **`C:`** `live` | `source_id` to actual logical requests and physical attempts |
| `response_classification_totals` | object | **`C:`** `live` | Counts keyed by `proceed`, `retry`, `retry_after`, `cooldown`, `fail`, `quarantine` — **every response is in exactly one bucket, and there is no `unclassified` bucket** |
| `status_code_totals` | object | **`C:`** `live` | Counts keyed by HTTP status |
| `raw_object_count` | integer | **`C:`** `live` | New content-addressed objects created |
| `duplicate_object_count` | integer | **`C:`** `live` | Byte-identical bodies reconciled to an existing object |
| `cache_hit_count` | integer | **`C:`** `live` | Instances already satisfied and therefore not requested |
| `not_modified_count` | integer | **`C:`** `live` | Conditional re-validations returning `304` |
| `quarantined_object_count` | integer | **`C:`** `live` | Objects quarantined and preserved |
| `redirect_hop_count` | integer | **`C:`** `live` | Validated hops followed by the policy layer |
| `cooldown_count` | integer | **`C:`** `live` | Aggregate traffic halts |

### 4.5.1 Simulated activity is not actual activity

**A rehearsal or dry run places no request, so its actual network counts are `0` — always, without
exception.**

Scripted responses, injected retries, simulated cooldowns, and fixture-driven object counts are
**rehearsal facts, not network facts**. They belong to the **rehearsal evidence report**, which is a
separate private artifact, and they never appear in the fields above.

v0.1's rehearsal scenarios described receipts whose actual-network fields carried simulated traffic,
contradicting v0.1's own zero-request rule. **A receipt that reports a non-zero actual network count
in a non-`live` mode is a fail-closed validation error** (§14), not a reporting convention.

### 4.6 Gate and drift outcomes

| Field | Type | Class | Meaning |
|---|---|---|---|
| `schema_drift_outcome` | string | **`C:`** `live`, `rehearsal` | One of `none`, `unknown_fields_retained`, `blocked` |
| `schema_drift_event_count` | integer | **`C:`** `live`, `rehearsal` | Total drift events, blocking and non-blocking |
| `gate_f_outcome` | string | **`C:`** `dry_run` | `pass`, `fail`, or `not_applicable` |
| `gate_h_outcome` | string | **`C:`** `live` | `pass`, `fail`, or `not_applicable` |

### 4.7 Resulting governed identities, recorded as references

| Field | Type | Class | Meaning |
|---|---|---|---|
| `resulting_snapshot_id` | string | **`C:`** `offline_execution` | Where the command produced one |
| `resulting_selection_run_id` | string | **`C:`** `offline_execution` | Where the command produced one |
| `resulting_selection_result_sha256` | string | **`C:`** `offline_execution` | Where the command sealed one |
| `resulting_root_manifest_sha256` | string | **`C:`** `offline_execution`, `approval` | Where the command constructed or re-derived one |
| `resulting_manifest_id` | string | **`C:`** `offline_execution`, `approval` | Where the command constructed or re-derived one |

**These are references, and the direction is one-way.** The receipt names what the run produced. **The
produced identity does not name, contain, or commit the receipt.** Recording an identity in a receipt
is not the identity depending on the receipt.

### 4.8 Completion and recovery

| Field | Type | Class | Meaning |
|---|---|---|---|
| `completion_status` | string | **`R`** | One of `complete`, `failed`, `interrupted`, `stopped_at_ceiling`, `stopped_by_gate` |
| `reason_code` | string | **`C:`** every non-`complete` status | A **registered** reason code from `src/disclosure_drift/reasons.py`. An unregistered code is a defect, not a new code |
| `reason_detail` | string | **`C:`** every non-`complete` status | One short non-secret sentence. **Never a response body and never a path** |
| `interruption_state` | string | **`C:`** `completion_status = "interrupted"` | One of `before_raw_store_write`, `after_raw_store_write_before_catalog_commit`, `after_catalog_commit`, `during_selection`, `during_manifest_write` |
| `recovery_predecessor_receipt_id` | string | **`C:`** a resumed run | The `receipt_id` this run resumed from |
| `consumed_request_count_carried_forward` | integer | **`C:`** a resumed `live` run | Physical attempts already spent against **that window's** ceiling |
| `rehearsal_evidence_reference` | string | **`C:`** `rehearsal` | The non-sensitive reference identifier of the private rehearsal evidence report holding the simulated totals (§4.5.1) |

## 5. Prohibited fields

**None of the following may appear in a receipt, in any field, under any name, in any encoding.**

| Prohibited | Why |
|---|---|
| The full SEC user-agent identity | It is a resolved secret and is never logged, printed, or persisted |
| Any email address | Personally identifying, and part of the SEC identity |
| Any credential value | Receipts are shared as evidence |
| Any API token or bearer value | Same |
| Any cookie | Same |
| Any authorization header | Same |
| Any raw response body, or an excerpt of one | Payload, not operational fact |
| Any absolute personal path | `scripts/check_repo_hygiene.py` refuses them, and they identify a machine and a person |
| Any candidate row | Substantive payload |
| Any selected entity or accession row | Substantive payload |
| Any reserve row | Substantive payload |
| Any filing text | Prohibited at this stage entirely |
| Any outcome value | Prohibited at this stage entirely |
| Any other unpublished substantive payload not already represented by a governed identity | The manifest represents the substance; the receipt represents the run |

**Encoding does not launder a prohibited value.** A hashed, truncated, base64'd, or
"partially masked" SEC identity is still the SEC identity and is still prohibited. The permitted way
to record that an identity was in force is `configuration_fingerprint`, which is a digest over
**non-secret** configuration and includes no resolved secret at all.

**Paths are recorded relative to the data root or not at all.** A receipt never contains an absolute
path.

## 6. Canonical serialization of the receipt

The receipt is serialized with the same canonical-JSON discipline the project already uses for
governed content, so that a receipt is comparable and diffable:

1. UTF-8, no byte-order mark;
2. LF line endings;
3. object keys sorted lexicographically by code point;
4. arrays in a deterministic, specified order — never iteration order;
5. no non-finite numbers; integers rendered without a decimal point;
6. UTC timestamps in RFC 3339 with a `Z` suffix;
7. relative paths only;
8. **absent fields omitted**, never rendered as `null` or as a placeholder;
9. one trailing newline.

**Reusing the canonical form is a convenience, not a coupling.** It makes receipts comparable; it
does **not** make them part of any governed preimage.

## 7. Storage location policy

**The repository is public. A receipt is never tracked in it.**

1. Receipts are written to the **owner-controlled private evidence root**, outside the repository
   working tree, in a directory dedicated to receipts.
2. The filename is **content-derived** from `receipt_id`, so two identical receipts collide by
   identity and two different runs never collide.
3. **Receipts are never committed to Git.** `scripts/check_repo_hygiene.py` already refuses tracked
   artifacts under `data/`, and the private evidence root is outside the repository entirely.
4. **Only the receipt's type, phase, status, `receipt_id`, and its own SHA-256 reach the public
   [evidence index](templates/evidence_index.md)** — never its contents, and never an absolute path.
5. A receipt is written **once** and is thereafter **immutable**. A correction is a new receipt that
   names the corrected one, never an edit.
6. An evidence packet **quotes fields** from a receipt and cites its `receipt_id`. It never embeds
   the file and never rewrites it.
7. **Private receipts require a separate owner-controlled backup** (master plan §12.4).

## 8. Retention policy

1. **Receipts are retained indefinitely.** They are the operational record of what ran.
2. **A receipt is never deleted to tidy up**, exactly as raw data is never deleted (CLAUDE.md
   rule 6).
3. A receipt describing a failed, interrupted, or ceiling-stopped run is retained **with equal
   priority** to a successful one — the failures are what recovery reasons about.
4. Retention creates no obligation on any governed identity. **Deleting every receipt in existence
   would leave every governed identity byte-identical** — which is the clearest statement of §0 that
   can be made.

## 9. Redaction policy

1. **Redaction happens at construction, not at rendering.** A prohibited value is never placed into
   the receipt object in the first place; there is no "redact before sharing" step to forget.
2. The construction path takes **non-secret inputs only**. It is never handed the resolved SEC
   identity, a credential, or a response body, so it cannot record one.
3. **A prohibited field is a fail-closed condition**, not a warning: the receipt renderer refuses to
   emit, and the inspection command exits `4`.
4. The prohibited-field scan is proven **non-vacuous** by a positive control — a deliberately
   contaminated receipt that the scan must reject (offline rehearsal scenario R19).
5. `reason_detail` is the only free-text field, is one short sentence, and is subject to the same
   scan.

## 10. Replay relationship

**Replay produces a receipt and changes nothing else.**

- A write-free idempotent replay emits a receipt with `completion_status = "complete"` and the same
  `resulting_*` identities as the run it replayed.
- The receipts of two replays of the same run **differ from each other** — different `receipt_id`,
  different timestamps, different elapsed seconds — while every governed identity and every document
  byte is **identical**.
- **That difference is the proof, not a defect.** Offline rehearsal scenario R20 asserts exactly this:
  vary every operational value and no governed identity moves.
- Replay never writes a receipt into the catalog, into the manifest document, or into any digest
  preimage.

## 11. Recovery relationship

1. A resumed run's receipt names its predecessor in `recovery_predecessor_receipt_id`, forming a
   chain back to the first attempt.
2. The chain is the evidence for
   [`templates/interrupted_run_recovery.md`](templates/interrupted_run_recovery.md): the last
   successful receipt establishes the interruption point.
3. `consumed_request_count_carried_forward` makes the ceiling cumulative across a resumed run. **A
   resume never resets the budget.**
4. A **broken chain** — a resumed run whose predecessor receipt is missing or unreadable — is a
   safe-resume determination of `UNDETERMINED`, and **`UNDETERMINED` is a stop condition.**
5. The recovery chain is operational. **It enters no governed identity**, and a run recovered from
   three interruptions produces exactly the same identities as one that ran straight through.

## 12. Schema-versioning policy

1. `receipt_schema_version` is **required in every receipt** and is the first field a reader
   consults.
2. The version this document defines is:

   ```
   m3-execution-receipt/1.0
   ```

3. **Adding a conditionally-required field is a minor version increment.** Removing a field,
   renaming one, changing a type, changing a field's meaning, or **changing a field's
   classification** is a **major** increment.
4. **A new major version requires a new accepted decision record.** The field set is frozen by
   Decision 027 §10; it is not extended by an implementation session.
5. **Old receipts are never rewritten to a new schema.** A reader dispatches on the version it finds.
6. Receipt-schema evolution is a recorded limitation
   ([`limitations_register.md`](limitations_register.md), **M3-L09**), because a version change
   during Milestone 3 would make receipts from different phases non-comparable.
7. **This document is at `m3-execution-receipt/1.0`.** The v0.2 corrections — removing
   `receipt_content_sha256`, classifying every field by invocation mode, and forcing zero actual
   network counts outside `live` — were made **before any receipt was ever produced**, so no receipt
   exists at an earlier shape and no migration is required.

## 13. The single receipt integrity identity

**There is exactly one, and it is `receipt_id`.**

```
receipt_id = SHA256( canonical receipt bytes with `receipt_id` omitted )
```

| Rule | Statement |
|---|---|
| **Name** | `receipt_id` |
| **Preimage** | The receipt's canonical bytes (§6) with the `receipt_id` field itself **excluded** |
| **Purpose** | It identifies the receipt **and** detects a receipt altered after it was written. One value serves both |
| **Scope** | **Operational only.** It proves the receipt is intact; it proves nothing about the run's content |
| **Prohibition** | **It enters no accepted S5 or S6 identity.** It is not a component digest, is not committed by `root_manifest_sha256`, is not part of `manifest_id`, and appears in no digest preimage anywhere in the project |
| **Prohibition** | It is never a manifest input, a selection input, a snapshot input, or an eligibility condition |
| **Prohibition** | It never gates approval. A valid `receipt_id` is not evidence that a root may be approved |

**The v0.1 optional `receipt_content_sha256` is removed.** It was a second digest over nearly the same
preimage as `receipt_id`, differing only in which field was excluded. Two integrity identities over
one object is ambiguous — a verifier cannot know which is authoritative — and this project's digest
discipline (Decision 021 §§6–10) admits exactly one preimage per identity. **No second
receipt-integrity field may be added without a new accepted decision.**

**Stated once more, because this is the field most likely to be mistaken for something governed:**
`receipt_id` is a checksum over an operational artifact. It has the same standing as the modification
time of a log file — useful, verifiable, and **entirely outside** the identity graph Decision 021
§§6–10 fixes.

## 14. Validation policy

Every receipt is validated at construction and again at inspection:

| Check | Rule |
|---|---|
| **Class conformance** | **Every `R` field present; every `C` field present in its named modes and absent outside them; every `P` field absent in its named modes.** This is the §4 table, enforced exactly |
| **No placeholder** | An inapplicable field is **omitted**, never `null`, an empty string, `0`, or `"N/A"` |
| **Enumerations valid** | `phase`, `invocation_mode`, `completion_status`, `schema_drift_outcome`, `gate_*_outcome`, `interruption_state` each within their fixed value sets |
| **Reason code registered** | Any `reason_code` must exist in `src/disclosure_drift/reasons.py` |
| **Prohibited-field scan** | Every §5 class scanned for, over the serialized bytes, failing closed |
| **Accounting consistency** | `actual_physical_attempt_count >= actual_logical_request_count`; `actual_physical_attempt_count <= approved_request_ceiling` for that window; per-route totals summing to the reported totals |
| **Classification completeness** | Every response accounted for in exactly one classification bucket; no residual |
| **Zero-network modes** | **`rehearsal`, `dry_run`, `offline_execution`, and `approval` receipts must report `actual_logical_request_count = 0` and `actual_physical_attempt_count = 0`.** A non-zero value is a fail-closed error, not a reporting convention (§4.5.1) |
| **Simulated totals separated** | A `rehearsal` receipt carries `rehearsal_evidence_reference` and **no** simulated traffic in any actual-network field |
| **Window scoping** | A `live` receipt names its `acquisition_window`, and its ceiling and plan hash are that window's |
| **Recovery chain** | `recovery_predecessor_receipt_id`, where present, resolves to a readable receipt |
| **Canonical form** | Re-serializing the parsed receipt reproduces the file byte-for-byte |
| **Single integrity identity** | `receipt_id` recomputes over its excluding preimage, and **no second receipt-integrity field exists** |
| **Non-contamination** | Asserted at the suite level, not per receipt: governed identities are byte-identical with receipts enabled, disabled, and varied (rehearsal **A12**) |

**Any failed check is fail-closed.** The renderer refuses to emit; the inspector exits `4`.

## 15. What this document does not do

It creates **no** runtime code, **no** module, **no** CLI command, **no** database table, **no**
migration, and **no** schema object. It changes no accepted identity, preimage, digest, or
methodology. It authorizes no implementation.

The receipt described here **does not exist yet**. A bounded M3.1 contract implements it against this
specification, and until then every command in
[`operator_runbook.md`](operator_runbook.md) that emits a receipt is labelled
`PLANNED — NOT YET IMPLEMENTED`.

## 16. The rule, one last time

> **The receipt records the run. The manifest records the result. Nothing crosses from the first into
> the second.**
>
> Every governed identity in this project — `snapshot_id`, the candidate-table identities,
> `selection_input_sha256`, `selection_run_id`, `selection_result_sha256`, the eight component
> digests, `root_manifest_sha256`, and `manifest_id` — is computable from persisted substantive rows
> alone, on any machine, on any day, **with every receipt in existence deleted.**
