# Milestone 3 — Execution-Receipt Specification

**Status:** specification only. **No runtime code and no database table is created by this document.**
A runtime implementation of this specification now exists under the M3.1 contract; this document
remains the specification and creates nothing.
**Applies to:** every Milestone 3 command that runs against real inputs, and every live command
without exception.
**Controlling records:** [Decision 027](../Decisions/decision_027_m3_master_plan_and_operational_readiness.md)
§§9, 17, 18, 19, as narrowly corrected by accepted
[Decision 028](../Decisions/decision_028_m3_1_readiness_corrections.md) §§9–10, and by accepted
[Decision 029](../Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md) §5,
which registers **one additional permitted `reason_code` value**,
`OFFLINE_REHEARSAL_SCENARIO_MISMATCH`.
**Schema unchanged.** Decision 029 registers a reason-code *value*, not a schema element. Receipt
schema `m3-execution-receipt/2.0`, the field set, every field type, the `completion_status`
vocabulary, the canonicalization rule, and the `receipt_id` digest preimage are **unchanged**, and
**no migration is created or authorized**.

> **Current schema authority (accepted Decision 055 §7).** The writer now emits
> `m3-execution-receipt/3.0`, which adds one field and restates one condition; readers accept
> **both** `2.0` and `3.0`, and every existing `2.0` receipt remains byte-unchanged, valid,
> readable, and usable in a mixed-version chain. Where this document says `2.0` below it is
> describing the schema it was written against; the version dispatch, not this text, is the
> contract.
>
> **Readers additionally accept `m3-execution-receipt/4.0` (accepted Decision 094 §10.1).** It is
> emitted **only** by the two PRE-E0 operator commands, its vocabulary is version-scoped so none of
> it can enter a `2.0`/`3.0` validator, and the writer constant for every pre-existing command is
> unchanged at `3.0`. See §12.2.
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
| `index_plan_policy_version` | string | **`C:`** `dry_run`, `live` | `INDEX_PLAN_POLICY_VERSION` in force; M3.1 implementation must use `quarterly-index-instances/2.0` |
| `request_plan_schema_version` | string | **`C:`** `dry_run`, `live` | The schema version of the exact request-plan document consumed |
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
| `acquisition_window` | string | **`C:`** `dry_run`, `live` | `M3.2A` or `M3.2B`. **Each window has its own plan, budget, and ceiling** |
| `request_plan_id` | string | **`C:`** `dry_run`, `live` | That window's plan identity |
| `request_plan_sha256` | string | **`C:`** `dry_run`, `live` | The plan hash the run consumed |
| `approved_request_ceiling` | integer | **`C:`** `live` | The owner-approved hard ceiling for **that window**. Omitted from Gate F dry runs, which precede approval |
| `planned_logical_request_count` | integer | **`C:`** `dry_run`, `live` | From that window's deterministic request plan. A dry-run plan is not yet owner-approved |
| `maximum_physical_attempt_count` | integer | **`C:`** `dry_run`, `live` | From that window's deterministic request plan, **derived per route from the implemented state machine** — never from an asserted constant. A dry-run value is not yet owner-approved |
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
| `remaining_planned_logical_request_count` | integer | **`C:`** `live` when `completion_status = "stopped_at_ceiling"` | Planned logical requests left unattempted when the next physical attempt was refused |

### 4.5.1 Simulated activity is not actual activity

**A rehearsal or dry run places no request, so its actual network counts are `0` — always, without
exception.**

Scripted responses, injected retries, simulated cooldowns, and fixture-driven object counts are
**rehearsal facts, not network facts**. They belong to the **rehearsal evidence report**, which is a
separate private artifact, and they never appear in the fields above.

v0.1's rehearsal scenarios described receipts whose actual-network fields carried simulated traffic,
contradicting v0.1's own zero-request rule. **A receipt that reports a non-zero actual network count
in a non-`live` mode is a fail-closed validation error** (§14), not a reporting convention.

### 4.6 Drift outcomes

| Field | Type | Class | Meaning |
|---|---|---|---|
| `schema_drift_outcome` | string | **`C:`** `live`, `rehearsal` | One of `none`, `unknown_fields_retained`, `blocked` |
| `schema_drift_event_count` | integer | **`C:`** `live`, `rehearsal` | Total drift events, blocking and non-blocking |

**Gate F and Gate H outcomes are not receipt fields.** Each gate concludes only after the command's
receipt is immutable, so its outcome belongs in the corresponding checklist. A receipt records what
the command did; it does not retroactively claim that a later governance gate passed.

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
| `consumed_request_count_carried_forward` | integer | **`C:`** a resumed `live` run, **or** a clean carry-in root (`3.0`) | Cumulative physical attempts spent against **that window's** ceiling **before this invocation** |
| `carry_in_authority_sha256` | string | **`C:`** a clean carry-in root only (`3.0`) | SHA-256 of the canonical bytes of the one-use carry-in authority this root consumed |
| `rehearsal_evidence_reference` | string | **`C:`** `rehearsal` | The non-sensitive reference identifier of the private rehearsal evidence report holding the simulated totals (§4.5.1) |

**The two carry-in classes, stated exactly** (accepted
[Decision 055](../Decisions/decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md)
§§7.2–7.4). In `3.0`, `consumed_request_count_carried_forward` means **cumulative physical attempts
before the current invocation**, and `actual_physical_attempt_count` records **this invocation's wire
attempts only**. There are exactly three lawful shapes for a `live` receipt, and every other
combination fails closed:

| Shape | `recovery_predecessor_receipt_id` | `consumed_request_count_carried_forward` | `carry_in_authority_sha256` |
|---|---|---|---|
| Ordinary zero-baseline fresh root | absent | **omitted** | absent |
| Clean carry-in root | **absent** | **required**, non-zero | **required** |
| Resume | **present** | **required** | **absent** |

**In `3.0`**, receipt accounting additionally validates that **carried-forward plus actual is no
greater than the approved ceiling**: the ceiling bounds *cumulative* consumption, and neither figure
bounds it alone.

**This rule is dispatched on the document's own version, and is `3.0`-only.** A `2.0` receipt is
validated under the rule it was written against — `actual_physical_attempt_count` alone may not
exceed the ceiling — and that check still applies to both versions. Applying the cumulative bound to
`2.0` documents would retroactively invalidate receipts that were correct when written, which
Decision 055 §7.1 forbids: existing `2.0` receipts remain byte-unchanged, valid, readable, and
usable in mixed-version chains.

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
2. **Two accepted filename conventions exist, and both are lawful** (Decision 064 §8):

   - **Operator-selected, create-once.** A live command writes its receipt where the operator named
     it with `--receipt-out`, and the accepted M3.2 convention gives every run its own namespace —
     for example `runs/<namespace>/execution_receipt.json`. This is where the real T6 and T7
     receipts live. The path is chosen once, the file is never overwritten, and the receipt's
     identity is the `receipt_id` **inside** it, not its filename.
   - **Content-derived.** The filename is derived from `receipt_id`
     (`receipt-<receipt_id>.json`), so two identical receipts collide by identity and two different
     runs never collide. This convention is used where a receipt is filed by identity rather than
     by run.

   **A receipt is addressed by its recorded identity, never by an assumed path.** This
   specification does not claim that every receipt physically exists at
   `receipt-<receipt_id>.json`, because the accepted evidence proves otherwise: the M3.2A chain
   spans two run namespaces and its receipts carry the operator-selected name. The chain resolver
   therefore locates a predecessor by validating candidates at **both** accepted filenames in the
   accepted receipt locations beneath the governed evidence root, requiring exact `receipt_id`
   equality, and refusing on zero candidates or on two candidates that differ (Decision 063).
   Nothing is moved, copied, renamed, or synthesized to satisfy either convention.
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
   contaminated receipt that the scan must reject (offline rehearsal scenario A12(a)).
5. `reason_detail` is the only free-text field, is one short sentence, and is subject to the same
   scan.

## 10. Replay relationship

**Replay produces a receipt and changes nothing else.**

- A write-free idempotent replay emits a receipt with `completion_status = "complete"` and the same
  `resulting_*` identities as the run it replayed.
- The receipts of two replays of the same run **differ from each other** — different `receipt_id`,
  different timestamps, different elapsed seconds — while every governed identity and every document
  byte is **identical**.
- **That difference is the proof, not a defect.** Offline rehearsal scenario A12(b) asserts exactly this:
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

### 11.1 Chain arithmetic, and the consumers that must agree with it

The cumulative consumed count for a chain is:

```text
cumulative = sum(actual_physical_attempt_count over every receipt in the chain)
           + carried_forward of the single no-predecessor root only
```

The root carry-in is added **exactly once** — never `N` alone, and never once per receipt. The root
is the only receipt in a chain with no predecessor to have inherited a baseline from, which is what
makes "once, at the root" well defined rather than a convention.

**Mixed `2.0`/`3.0` chains walk identically.** A `2.0` root carries no baseline and contributes zero,
so every chain written before Decision 055 walks to exactly the count it always did.

The **receipt-chain walker**, **`m3 acquire --show-scope`**, and **every recovery and continuation
consumer** must agree with that formula. They agree by construction: there is one implementation of
the arithmetic (`walk_receipt_chain`), and each of those surfaces calls it rather than restating it.

### 11.2 The carry-in cross-check

A clean carry-in root and the operational catalog's consumption checkpoint **mutually cross-check**.
Either surface alone can be forged by editing the other, so both directions are checked:

- a root claiming a non-zero baseline while naming **no** authority has no durable record of where
  that baseline came from;
- a root naming an authority whose **checkpoint is absent** claims a burn that never committed;
- a checkpoint whose recorded baseline **differs** from the receipt's means the two disagree.

**The checkpoint is read as the whole closed document it is, not for the one figure the arithmetic
needs.** Finding a row under the expected deterministic key proves only that *something* was written
there, so the record itself is validated:

- it must parse, be a JSON object, and carry **exactly** the field set of data dictionary §5B — a
  missing field and an extra field are each refused, never ignored;
- the stored TEXT must be **byte-for-byte the canonical serialization** of the document it parses
  to. A consumption writes canonical bytes, so re-indented, re-ordered, or duplicate-key encodings
  record no burn the catalog made — and a duplicate key is otherwise invisible, because the parser
  silently keeps the last value and nothing below would ever compare the discarded one;
- every value must be well formed and internally consistent: a real schema version, an accepted
  acquisition window, a canonical `Decision NNN` authorizing reference, a route allocation keyed by
  non-empty registered routes whose counts are **non-negative integers** summing to the carried
  baseline, and a baseline within the ceiling it names;
- its embedded **authority hash must match the deterministic key it is filed under**, so a row
  describing a different burn cannot stand in for this one;
- its **plan, window, and ceiling must match the root receipt's**, and its carried baseline must
  match the root's carried-forward count;
- it must carry the **fixed Decision 055 values** — schema `m3-carry-in-authority/1.0`, window
  `M3.2A`, the frozen plan, ceiling `801`, seed `1` allocated wholly to `sec_bulk_submissions`, and
  `Decision 055` — compared literally against the same constants, through the same validator, that
  the artifact gate uses. **Agreement between the two surfaces is not authorization:** a forged
  root and a checkpoint forged to match it agree perfectly, and neither surface influences what the
  accepted values are;
- its **authorized run must resolve** to a governed acquisition run registered in that same window —
  the two writes commit in one transaction, so a checkpoint whose run does not exist records a burn
  that did not happen as described. No receipt field names a run, and none is added;
- **no two carry-in checkpoints may claim the same authorized run**: a run registers exactly once,
  so at most one authority can have burned alongside it.

Each of these is **`UNDETERMINED`**, and **`UNDETERMINED` cannot authorize continuation.** Neither
surface is ever edited to match the other.

## 12. Schema-versioning policy

1. `receipt_schema_version` is **required in every receipt** and is the first field a reader
   consults.
2. The version this document defines, and the one the **writer** emits, is:

   ```
   m3-execution-receipt/3.0
   ```

3. **Adding a conditionally-required field is a minor version increment.** Removing a field,
   renaming one, changing a type, changing a field's meaning, or **changing a field's
   classification** is a **major** increment.
4. **A new major version requires a new accepted decision record.** The v2 field set is governed by
   Decision 028 §9; it is not extended by an implementation session. The v3 field set is governed by
   accepted
   [Decision 055](../Decisions/decision_055_m3_2_carry_in_architecture_and_offline_implementation_authorization.md)
   §7, which unfroze the schema for **exactly one** backward-compatible successor and nothing else.
5. **Old receipts are never rewritten to a new schema.** A reader dispatches on the version it finds.
6. Receipt-schema evolution remains a recorded limitation
   ([`limitations_register.md`](limitations_register.md), **M3-L09**). Once the first v2 receipt
   exists, later incompatible changes would make phases non-comparable and require an explicit
   versioned reader policy.
7. **This document is at `m3-execution-receipt/3.0`.** The v1 design was corrected before any receipt
   was ever produced, so no v1 artifact exists.

### 12.1 The `2.0` → `3.0` step, and what it guarantees

`3.0` is a **major** increment because one field's meaning and classification changed, and it is
**backward compatible for readers**:

- **`2.0` receipts remain byte-unchanged, valid, readable, and usable in mixed-version chains.** They
  are **never rewritten, upgraded in place, or migrated.**
- Readers accept both versions and **dispatch on the version the document declares**. Each version is
  validated against **its own** permitted-field table: `carry_in_authority_sha256` is not a permitted
  `2.0` field, and a `2.0` receipt carrying it is refused by the closed field set.
- **Dispatch covers accounting, not only the field table.** The cumulative ceiling rule
  (carried-forward plus actual, §4.5) is a `3.0` rule; a `2.0` receipt is bounded by
  `actual_physical_attempt_count` alone, exactly as it always was. A `2.0` document whose sum
  exceeds its ceiling while its actual count does not therefore stays valid — it was correct when
  written, and refusing it now would be a rewrite of the record by refusal.
- Only the **writer** moved. Every receipt written from now on declares `3.0`.

The complete `3.0` delta over `2.0` — nothing else is added, removed, retyped, or re-moded:

| Change | Field |
|---|---|
| Meaning and condition restated | `consumed_request_count_carried_forward` — now *cumulative attempts before this invocation*, required for a resume **and** for a clean carry-in root, omitted for an ordinary zero-baseline fresh root |
| Added | `carry_in_authority_sha256` — required only on a clean carry-in root |
| Accounting rule added, `3.0`-only | carried-forward **plus** actual may not exceed the approved ceiling; `2.0` keeps its former `actual`-alone bound |

### 12.2 The `4.0` successor — version-scoped, for the two PRE-E0 commands only

Accepted
[Decision 094](../Decisions/decision_094_m3_3_pre_e0_executability_redesign.md) §10.1 adds **exactly
one** further backward-compatible reader/writer successor:

```
m3-execution-receipt/4.0
```

**Nothing that existed before changed.** `2.0` and `3.0` receipts stay byte-unchanged, keep their
existing validators and writer behaviour, and every pre-existing command still emits `3.0`. The
writer constant in §12 item 2 is unmoved. Only `m3 prepare-e0-catalog` and `m3 offline-parse` call
the explicit v4 builder, and they use a **separate class** — `ExecutionReceiptV4` cannot express a v3
field, `ExecutionReceipt` cannot express a v4 mode, and neither can be relabelled as the other
because both write their own `receipt_schema_version`.

**Every v4 vocabulary object is version-scoped.** The rule table, phase, invocation-mode tuple,
zero-network tuple, interruption tuple, and reason vocabulary are attached to the `4.0` schema, not
to a module-level tuple that a common checker consults. That is what makes the isolation mechanical
rather than conventional: a `3.0` document naming a v4-only mode or interruption state is refused by
the `3.0` table.

The complete `4.0` delta:

| Change | Detail |
|---|---|
| `phase` | fixed at `M3.3B` — the already-accepted real-execution phase, deliberately **not** a new project phase |
| Invocation modes | `offline_catalog_transition`, `offline_parse`; both are zero-network, so both counts are fixed at `0` |
| Field set | `offline_catalog_transition` permits only the common identity, migration, timing, zero-network, completion, reason, interruption, and predecessor fields; `offline_parse` additionally requires `parser_versions` and `cohort_definition_digest`. Every selection, quota, manifest, drift, route, classification, and transport field is **absent from the closed set entirely** |
| Completion statuses | `complete`, `failed`, `interrupted`. There is no `stopped_at_ceiling` — the ceiling is zero and nothing is attempted — and no `stopped_by_gate`: a refused predicate is a `failed` run with its own reason code |
| Reason vocabulary | closed and **stage-scoped**: `PRE_E0_CATALOG_TRANSITION_FAILED`, `PRE_E0_CATALOG_TRANSITION_INTERRUPTED`, `M3_3_E0_OFFLINE_PARSE_FAILED`, `M3_3_E0_OFFLINE_PARSE_INTERRUPTED`. These are deliberately **not** added to `disclosure_drift.reasons`; a `2.0`/`3.0` receipt still validates its `reason_code` against the repository registry exactly as before |
| Interruption states | the sixteen values below, `4.0`-only |

```text
before_backup                                    during_e0_source_parse
during_backup                                    after_e0_source_commit_before_event
after_backup_before_migration                    during_e0_full_index_observation_materialization
after_migration_0014_before_0015                 after_e0_full_index_observations_before_resolution
after_migration_0014_commit_before_event         during_e0_accession_resolution
after_migration_0015_commit_before_event         after_e0_resolution_before_association_materialization
after_migration_0015_before_transition_freeze    during_e0_association_materialization
                                                 after_e0_materialization_before_validation
                                                 after_e0_validation_before_freeze
```

**No terminal-record field appears in a receipt.** The relationship is deliberately one-way: the
receipt is written **first**, and the terminal record binds its `receipt_id`. That ordering is what
prevents a receipt/terminal identity cycle. The records those two commands produce are specified in
[`e0_execution_record_spec.md`](e0_execution_record_spec.md).

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
| **Enumerations valid** | `phase`, `invocation_mode`, `completion_status`, `schema_drift_outcome`, and `interruption_state` each within their fixed value sets |
| **Reason code registered** | Any `reason_code` must exist in `src/disclosure_drift/reasons.py` |
| **Prohibited-field scan** | Every §5 class scanned for, over the serialized bytes, failing closed |
| **Accounting consistency** | `actual_physical_attempt_count >= actual_logical_request_count`; in `live`, `actual_physical_attempt_count <= approved_request_ceiling`; per-route totals sum to the reported totals; in `live`, `stopped_at_ceiling` carries a positive `remaining_planned_logical_request_count` |
| **Classification completeness** | Every response accounted for in exactly one classification bucket; no residual |
| **Zero-network modes** | **`rehearsal`, `dry_run`, `offline_execution`, and `approval` receipts must report `actual_logical_request_count = 0` and `actual_physical_attempt_count = 0`.** A non-zero value is a fail-closed error, not a reporting convention (§4.5.1) |
| **Simulated totals separated** | A `rehearsal` receipt carries `rehearsal_evidence_reference` and **no** simulated traffic or object-accounting total in any actual-network or `C: live` field; those values exist only in the rehearsal evidence report |
| **Window scoping** | A `dry_run` or `live` receipt names its `acquisition_window`; a `live` receipt's ceiling and both modes' plan identities belong to that window |
| **Recovery chain** | `recovery_predecessor_receipt_id`, where present, resolves to a readable receipt |
| **Canonical form** | Re-serializing the parsed receipt reproduces the file byte-for-byte |
| **Single integrity identity** | `receipt_id` recomputes over its excluding preimage, and **no second receipt-integrity field exists** |
| **Non-contamination** | Asserted at the suite level, not per receipt: governed identities are byte-identical with receipts enabled, disabled, and varied (rehearsal **A12**) |

**Any failed check is fail-closed.** The renderer refuses to emit; the inspector exits `4`.

## 15. What this document does not do

It creates **no** runtime code, **no** module, **no** CLI command, **no** database table, **no**
migration, and **no** schema object. It changes no accepted identity, preimage, digest, or
methodology. It authorizes no implementation.

**Implementation status (current).** The receipt described here **is implemented**, in
[`src/disclosure_drift/m3/receipt.py`](../../src/disclosure_drift/m3/receipt.py), and real receipts
exist — the M3.2A chain's T6 and T7 receipts among them. The sentence this paragraph replaced said
the receipt did not exist yet and that every receipt-emitting command in
[`operator_runbook.md`](operator_runbook.md) was `PLANNED — NOT YET IMPLEMENTED`; that was true when
this specification was written and is no longer true (Decision 064 §9). This document still creates
no code: it specifies, and the module implements.

## 16. The rule, one last time

> **The receipt records the run. The manifest records the result. Nothing crosses from the first into
> the second.**
>
> Every governed identity in this project — `snapshot_id`, the candidate-table identities,
> `selection_input_sha256`, `selection_run_id`, `selection_result_sha256`, the eight component
> digests, `root_manifest_sha256`, and `manifest_id` — is computable from persisted substantive rows
> alone, on any machine, on any day, **with every receipt in existence deleted.**
