# M3.3 — D088 Corrected Verified-Evidence Schema — Fresh Formal Independent Acceptance Rereview — target `7466482`

```text
REVIEW_KIND: FRESH CLAUDE FABLE 5 FORMAL INDEPENDENT ACCEPTANCE REREVIEW (Decision 089 commission)
REVIEW_TARGET: 746648285ec84d54a2ed7deaebc73f5c64b89d3d (tree 1afd1c3bbecd7f2e38aee5901dffd9214e499c4b)
PRE_CORRECTION_TARGET: 8c13fc79aee649df4956643f0b24504c8cdfd2c7 (the D087-reviewed FAIL)
D088_AUTHORITY: fc972b58d92b68be9fe6fe4dbb4808a25aed45aa
GOVERNANCE_HEAD_AT_REVIEW: cb221b6e37981fa470a7791305ca43dfc4f2ba51 (tree 1fcbe2ca…, Decision 089, governance only)
VERDICT: PASS
FINDINGS: BLOCKER 0 / MAJOR 0 / MINOR 0 / OPTIMIZATION 0 / OBSERVATION 4 (OBS-1 deferred-confirmed, OBS-A closed non-defect, OBS-B accepted non-defect, OBS-C new non-gating)
D087_M1_REPLACEMENT_REWRITE_DOOR: CLOSED — independently re-proved
RESULT_TOKEN: M3_3_D088_VERIFIED_EVIDENCE_FRESH_REREVIEW_PASSED_READY_FOR_OWNER_ACCEPTANCE
REVIEWER: Claude Fable 5 (harness model identifier `claude-fable-5`), maximum effort
MODEL_IDENTITY_GATE: PASSED — genuine Fable 5, fresh /clear epoch, authored none of the target
DATE: 2026-08-15
OWNER: Sol/GPT (rereview commissioned by owner packet under accepted Decision 089)
```

**Verdict basis in one paragraph.** The full corrected verified-evidence infrastructure at
`7466482` is formally acceptable. This epoch re-proved M-1 independently with its own probe harness
— 119/119 conflict-idiom probes across all four evidence relations, every UNIQUE/PK route, seven
`INSERT` conflict idioms plus the three upsert forms, through both the repository's governed
connection and a raw default connection, with every relation byte-identical after every refusal and
all five guard-removal kill demonstrations landing — so
`D087_M1_REPLACEMENT_REWRITE_DOOR = CLOSED`. MIN-1's registered-accession binding was re-proved on
both the review and the adjudication side (17/17), including the isolation proof that the
adjudication-side trigger refuses alone with every sibling guard dropped, and the demonstration that
the exact D087 uniform-cross-bind lifecycle reopens only when **both** binding triggers are removed.
MIN-2's `agreed` consistency was re-proved for both evidence kinds (27/27) — every abstention and
disagreement route refuses, both mutation kills land (the CHECK removed from a rebuilt disposable
table admits `verified`+`abstained`, and the dropped trigger re-admits the exact D087
`agreed`+`verified`-over-two-abstentions lifecycle). MIN-3's two-column `UPDATE OF` list was
re-proved load-bearing (13/13) — shrinking it back to one column re-points verified credit to an
evidence-less accession. OBS-2's corrected comment now matches the executable nine-table guard
exactly; OBS-3's strict byte-range CHECK passed a 22-case matrix and its removal kill. The
correction diff is **bounded** to the six accepted findings plus the authorized re-baselines and
truthful documentation; the policy-chain identity movement reproduces to the byte with all eight
substantive manifest components unmoved; the full acceptance boundary — applicability, linkage,
epochs, append-only, hashes, nonleakage, migration safety, VE-M1…M14, VE-R1…R10, positive
lifecycle, prohibited nonchange — revalidated clean; targeted validation 510/510 and one
`make check-fast` green over 4211 collected tests. OBS-A received its contract determination:
**CLOSED / NON-DEFECT** (§10 below). OBS-1 remains **OPEN / NON-GATING / DEFERRED** with all its
supporting assumptions independently confirmed. One new non-gating observation (OBS-C) is recorded.

---

## 1. Model / independence gate

| Requirement | State |
|---|---|
| Model | **Claude Fable 5**, harness identifier `claude-fable-5` — reported before substantive review |
| Effort | Maximum |
| Epoch | Fresh `/clear`; first action of the session |
| Authorship | This epoch authored none of: Decision 087, the `8c13fc7` implementation, the D087 failed review, Decision 088, the `7466482` corrections, Decision 089, or any corrected test baseline |
| Target predates epoch | Yes — `7466482` and `cb221b6` were committed and pushed before this epoch began |
| Subagents / delegation / parallel workflows | **None** — one session, no Agent tool use, no Workflow use |
| Correction-session conclusions | **Not inherited** — every closed finding re-proved by this epoch's own probe harness |

Gate result: **PASSED**.

## 2. Current governance head — verified

Verified live by `make context` (0.54 s), `scripts/verify_target.py` (1/1 PASS, 0.08 s), and direct
Git. No fetch, pull, reset, clean, or stash was performed.

| Fact | Verified value |
|---|---|
| Branch | `main` |
| `HEAD` == `origin/main` | `cb221b6e37981fa470a7791305ca43dfc4f2ba51` |
| `HEAD` tree | `1fcbe2ca1bde3235364eceea3a0801b597cfc49e` |
| `HEAD` parent | `746648285ec84d54a2ed7deaebc73f5c64b89d3d` — the frozen rereview target |
| Working tree | CLEAN |
| Migrations | `0001`–`0015` contiguous; `0016` ABSENT |
| `m3.2-complete` | annotated tag object `2865a1479e4576dc18a4098c928b278812f38d00` → commit `2185f583…`, unmoved; no tag at `HEAD` |
| Tracked network switches | `false` / `false` |

**The Decision 089 governance commit changes no implementation byte**:
`git diff --name-only 7466482..cb221b6 -- src tests configs` is **empty**; its full path set is
exactly `decision_089_…md`, `decision_registry.md`, `decision_index.md`, and
`Milestones/STATUS.md`. The working tree is byte-identical to the frozen target for every
implementation path, so the review executed against the frozen target's exact bytes.

## 3. Frozen implementation target

| Fact | Verified value |
|---|---|
| Implementation target | `746648285ec84d54a2ed7deaebc73f5c64b89d3d` |
| Tree | `1afd1c3bbecd7f2e38aee5901dffd9214e499c4b` |
| Pre-correction comparison point | `8c13fc79aee649df4956643f0b24504c8cdfd2c7` |
| Decision 088 authority commit | `fc972b58d92b68be9fe6fe4dbb4808a25aed45aa` |

## 4. Authority chain — read directly and verified linear

`3749b012` (pre-D087 entry, accepted R46 state) → `ddd582a0` (Decision 087 implementation
authority) → `8c13fc79` (original verified-evidence implementation; D087 review verdict FAIL at
MAJOR 1 / MINOR 3 / OBSERVATION 3) → `fc972b58` (Decision 088 correction authority) → `74664828`
(corrected implementation, the frozen target) → `cb221b6e` (Decision 089 rereview authority).
First-parent ancestry confirmed by `git log`; no side branches. Decisions 082 (§§11, 12.2, 12.4,
12.5, 12.6), 083 (§8 R63, §9 R64), 087, 088, and 089 were read directly, plus Decision 080's AP-1
… AP-10 protocol elements. No completion report was used as a substitute for a governing record.

## 5. Correction scope — bounded

The D088 governance commit (`fc972b58`) touches governance documents only. The implementation
correction (`fc972b58..74664828`) touches exactly the Decision 088 §10 authorized set and nothing
else:

| Path | Content | Bounded to |
|---|---|---|
| `…/0015_m33_verified_document_evidence.sql` | +7 triggers (4 replacement guards, 2 binding, 1 agreed-consistency), 2-column `UPDATE OF`, strict `span_location` CHECK, corrected §1 comment | M-1, MIN-1, MIN-2, MIN-3, OBS-2, OBS-3 |
| `tests/unit/test_m3_3_verified_document_evidence.py` | VE-R1…VE-R10 added; `verb` parameter on fixture writers; four VE-M assertions repaired where the new guards fire first; OBS-1 pinned open | the same six findings |
| `tests/unit/test_m23_pilot_manifest_store.py` | the R68 policy-chain re-baseline — three values only | authorized re-baseline |
| `Docs/sec_data_dictionary.md`, `Docs/architecture_map.md`, `Docs/change_impact_map.md`, `Milestones/STATUS.md` | truthful current state | authorized documentation |

Verified byte-for-byte: **no other `src/` path moved** between `8c13fc7` and `7466482`; `cohorts.py`,
`pilot_policy.py`, `candidate_identity.py`, `candidate_snapshot.py`, `offline_execution.py`,
`document_evidence.py`, `release/hashing.py`, `acquisition.py`, migrations `0001`–`0014`,
`Docs/preregistration.md`, Decisions 001–087, and every prior review artifact are byte-unchanged
across the correction. Trigger count moved 16 → 23 = exactly the seven authorized additions. **No
unrelated methodology or architecture change exists in the delta.**

## 6. M-1 — replacement-guard rereview: independently re-proved CLOSED

Probe harness: this epoch's own (`probe_m1.py`, structured independently of the repository suite),
run through the repository's `connect()`/`apply_migrations()` machinery on disposable catalogs —
governed connection (`foreign_keys` ON, WAL, `synchronous FULL`, `recursive_triggers` never set)
and a raw default connection. **119/119 probes passed, 0.71 s.**

- **Routes** — all six unique/PK conflict routes: `document_artifacts` PK `artifact_sha256` +
  UNIQUE (`accession_plain`,`source_class`); `document_review_records` PK `review_id` + UNIQUE
  (`accession_plain`,`reviewer_role`); `document_review_spans` composite PK; and
  `document_adjudicated_evidence` composite PK. Schema inspection confirms **no further unique
  route exists** on any of the four relations.
- **Idioms** — ordinary duplicate `INSERT`, `INSERT OR REPLACE`, `REPLACE`, `INSERT OR IGNORE`,
  `INSERT OR ROLLBACK`, `INSERT OR ABORT`, `INSERT OR FAIL`, `ON CONFLICT … DO UPDATE`,
  `ON CONFLICT … DO NOTHING` — every one refused on every route, including the digest-repair
  variant (identical value/state, new `adjudication_sha256`) that satisfies every sibling guard.
  A: first lawful insert succeeds. B: duplicates fail. C–F: `INSERT OR REPLACE` refused on all four
  relations. G: `INSERT OR IGNORE` and `DO NOTHING` are **refused**, never silent no-ops. H: the
  lawful append lifecycle remains possible after every attack.
- **State integrity** — after every refused idiom the relation's full row set compared
  byte-identical to its pre-attack snapshot.
- **Pre-freeze vs post-freeze** — replacement guards proved in isolation pre-adjudication; after
  the freeze, review/span appends die at the freeze guards and same-key replacements at the
  replacement guards: the door is closed twice over.
- **Kills** — with each guard dropped on a disposable catalog, an attack crafted to satisfy every
  sibling guard **lands**: the frozen adjudication's digest is repaired in place; a review pass is
  rewritten under its own `review_id`; a span-less (abstaining) review is re-stood under a new id
  via the UNIQUE route; span provenance is rewritten; artifact metadata is substituted. Each guard
  is individually load-bearing. (Depth note: a span-carrying review's UNIQUE-route replacement is
  additionally blocked by the span foreign keys even with the guard removed; the guard remains the
  sole protection for the same-id rewrite and for span-less reviews.)

```text
D087_M1_REPLACEMENT_REWRITE_DOOR = CLOSED
```

## 7. MIN-1 — accession ↔ artifact binding: re-proved on both sides

`probe_min1.py`, **17/17, 0.46 s**. Same-accession review/adjudication ACCEPT; cross-accession
review REFUSE (`document_review_records_bind_their_own_accession`); unregistered artifact REFUSE;
cross-accession adjudication REFUSE; cross-accession and mixed contributor sets REFUSE (exact-set
arithmetic); lawful complete lifecycles for two accessions ACCEPT. **Isolation:** with all six
sibling adjudication triggers dropped, `document_adjudicated_evidence_binds_its_own_accession`
alone still refuses the cross-bound and unregistered-artifact adjudications. **Kills:** removing
the review-side trigger lands a cross-bound review; removing **both** binding triggers reopens the
complete D087 uniform-cross-bind lifecycle ending in verified credit — the pair is exactly what
closes it. **Bypass search:** the span layer carries no artifact or accession column;
`artifact_sha256` exists in exactly the three governed carriers; UNIQUE
(`accession_plain`,`source_class`) with the single-value `source_class` CHECK means an accession
can register at most one artifact, so no competing artifact can be stood up beside the bound one;
the candidate layer joins evidence by accession only, and evidence rows are accession-bound to
their registered artifact. No bypass found.

## 8. MIN-2 — agreed-state consistency: re-proved for both kinds

`probe_min2_obsa.py`, **27/27, 1.51 s**, exercised separately for `amendment_purpose` and
`explicit_original`: two agreeing substantive passes ACCEPT (with `verified`); A-abstains/B-asserts,
A-asserts/B-abstains, both-abstain, category/form/date disagreement, and value-neither-asserted all
REFUSE `agreed` — at `verified` **and** at non-credit levels, so the rule protects the state, not
only the credit. `verified`+`conflicting` and `verified`+`abstained` REFUSED by the CHECK;
`agreed` with NULL value and `conflicting` with a value REFUSED; an invented state REFUSED by the
vocabulary CHECK; `resolved` REFUSES without the third adjudication record and ACCEPTS with it.
**Mutation kills:** (1) the `verified ⇒ agreed/resolved` CHECK excised from a rebuilt disposable
table admits `verified`+`abstained` — the exact row VE-R8's targeted negative test asserts is
refused, so that test kills the mutant and the previously unprotected guard is now proven; (2) the
dropped consistency trigger re-admits the exact D087 defect (`agreed`+`verified` over two
abstentions, zero spans). Both halves are load-bearing.

## 9. MIN-3 — verified-candidate re-pointing: re-proved

`probe_min3.py`, **13/13, 0.59 s**. Verified insert with lawful evidence ACCEPT; repoint of a
verified candidate to an evidence-less accession REFUSE; repoint to an accession whose evidence is
wrong-kind (`explicit_original` only) REFUSE; repoint to an accession whose purpose evidence is
non-`verified` REFUSE; update-to-verified without evidence REFUSE; lawful unproven→verified update
with evidence ACCEPT; ordinary non-verified repoint remains governed by the accepted building-state
rules; `INSERT` and `INSERT OR REPLACE` arriving `verified` at an evidence-less accession REFUSE.
**Structural:** the trigger reads
`BEFORE UPDATE OF amendment_purpose_evidence_level, accession_plain` — both columns named — with
the companion `BEFORE INSERT` trigger WHEN-gated on `verified`; the evidence join is on
`accession_plain` alone, so no third column can carry the dependency. **Kill:** re-creating the
trigger with the one-column list re-points verified credit to an accession with no evidence — the
added column is load-bearing. Verified applicability was not widened by the fix.

## 10. OBS-A — contract determination: CLOSED / NON-DEFECT

**Contract read directly**: Decision 082 §12.6 (as accepted by Decision 083 R64) maps outcomes to
agreement states; §12.2 defines the four allowed abstentions and makes an abstention a *recorded
outcome* under Decision 080 **AP-1** totality; §12.5/AP-9 fail a non-locatable span closed;
AP-6/AP-7 freeze and owner-accept the complete adjudication table before any consumption.

**The contractual meaning of `abstained`** is the §12.6 row "A and B both abstain": no category, no
linkage, no quota credit. It is the final state for exactly that case and no other.

| Case | Contractually correct disposition |
|---|---|
| **A** — both abstain | `abstained`; value NULL; never `verified`; contributes nothing |
| **B** — A abstains, B asserts | **third adjudication** → `resolved` (citing exact text) or `conflicting`; never `agreed`, never `abstained` |
| **C** — A asserts, B abstains | same as B, mirrored |
| **D** — neither abstains, they disagree | **third adjudication** → `resolved` or `conflicting` |
| **E** — neither abstains, no accepted value results | `conflicting` (adjudication cannot resolve, or a span fails mechanical location); value NULL; fail closed |
| **F** — adjudicator route | `resolved`, requires the third adjudication record; value present; eligible for `verified` |

**Executed schema facts** (`probe_obsa.py`, hard rails 5/5, plus the representability matrix,
1.11 s): the lawful case-A row is ADMITTED; the lawful case-B/C disposition (`resolved` +
`verified` via a third epoch) is ADMITTED; `abstained` with a non-NULL value is REFUSED (CHECK);
`abstained` + `verified` is REFUSED (CHECK); `abstained` with fewer than both passes is REFUSED
(review-provenance). The schema **can** also record `abstained` (and `conflicting`) over passes
that substantively asserted — the asymmetry Decision 088's session observed — and `resolved` over
an actually-agreeing pair when a third record exists.

**Determination.** The schema **faithfully implements the frozen contract**, and the asymmetry is
not a defect, for reasons that are the contract's rather than symmetry's:

1. **Every consequence the contract attaches to agreement states is mechanically enforced**:
   `agreed` requires genuine dual assertion (MIN-2); `resolved` requires the third record;
   `verified` requires `agreed`/`resolved` plus a matching span from every non-abstaining
   contributor; `abstained`/`conflicting` can carry no value, no `verified`, no feasibility
   contribution (§12.8 counts `agreed`/`resolved` only), no quota credit, and no candidate
   consumption. Every mislabel the schema admits is **fail-closed**: it can deny credit, never
   grant it.
2. **No accepted record assigns the schema the duty of enforcing §12.6's routing between
   non-credit states.** Decision 082 §11 (the schema contract) requires representation,
   append-only immutability, and provenance binding; R63's "must enforce" language attaches to
   verified applicability. §12.6 is the *protocol* contract — its executor is the future
   owner-commissioned R64 run, whose complete frozen table is owner-accepted (AP-7) and
   span-verified (AP-9) before consumption. The owner's own correction contract, Decision 088 §5,
   states the `abstained` and `conflicting` routes are **unchanged** — reviewed and left as they
   are.
3. **A false `abstained` cannot conceal itself.** The exact-set arithmetic forces the row to
   enumerate precisely the reviews of its accession and artifact; those rows are immutable and
   carry their assertions and spans. A mislabeled row necessarily points at the governed evidence
   that contradicts it.
4. **Wrong terminality is recoverable only the accepted way.** A mislabeled non-credit row does
   freeze its accession/kind, but conflict terminality and its owner-authorized reopening are
   exactly R64's accepted design — never a silent path.

The §12.6 routing question the schema cannot decide is not decidable by any schema: a
`conflicting` row without a third record is *lawful* (the span-location-failure route) and
*unlawful* (skipping a required third adjudication) depending on facts outside the database.

```text
OBS-A = CLOSED / NON-DEFECT
```

Recorded within this determination, for completeness rather than as defects: the same
representability reasoning covers `conflicting`-over-agreeing-passes and
`resolved`-over-agreeing-passes (both fail-closed or strictly stricter routes), and OBS-C below
records the per-kind boundary of the `agreed` consistency rule.

## 11. OBS-3 — strict byte-range validation: closed

`probe_boundary.py` matrix: ACCEPT `bytes:0-1`, `bytes:123-456`; REFUSE all twenty malformed
shapes — `bytes:1a-2b`, `bytes:a1-2`, `bytes:1-b2`, `bytes:+1-2`, `bytes:1 -2`, `bytes:1- 2`,
`bytes:/1-2`, `bytes:1.0-2`, `bytes:1-2-3`, `BYTES:1-2`, `bytes:-2`, `bytes:1-`, `bytes:-`,
`bytes:`, `bytes:12`, `chars:1-2`, `bytes:1~2`, `bytes:1-2/3`, `/etc/passwd`, `bytes:0x1-2`. The
four CHECK clauses were verified to be exactly literal-prefix + digits-and-one-hyphen +
exactly-one-hyphen + non-empty endpoints; no source-location semantics beyond strict decimal
validation exist. The CHECK-removal kill (`probe_lifecycle.py`) lands: `bytes:1a-2b` is admitted
the moment the CHECK is excised, so VE-R10's matrix is load-bearing.

## 12. OBS-2 — migration comment truth: closed

The §1 comment now claims **exactly the nine tables this migration's rebuild can reach**, and the
temporary-trigger guard enforces exactly those nine (verified by extraction:
`pilot_candidate_snapshots`, `pilot_candidate_accessions`, the three FK children
`…_registrants`/`…_evidence`/`…_reasons`, `pilot_selection_runs`, `pilot_selected_accessions`,
`pilot_reserve_accessions`, `pilot_manifest_versions`). Verified set algebra: 0015's nine =
(0014's eight − `census_parsed_records`/`census_parser_runs`) + the three children — precisely the
fact the original comment misstated, now stated truthfully with the census exclusion explained.
0015 contains no census DDL. Comment matches executable reality; no operator-safety
misrepresentation remains.

## 13. OBS-1 — deferred condition: independently confirmed, remains non-gating

All four deferral assumptions confirmed by execution: (1) **authoritative membership** is the
governed `document_review_records` set — the exact-set arithmetic refuses a substituted foreign id
(containment), an added id (length), and an omitted id (length), so no false hash-derived
contributor membership is expressible in any consuming sense; (2) the module's serialization is
**canonical, sorted, deduplicated, deterministic** (same bytes under input reordering); (3) review
identities are validated 64-lowercase-hex values, and the module **fails closed** on empty sets,
duplicates, non-hex, wrong-length, and uppercase inputs; (4) deterministic hashing is unaffected —
the seven evidence domains are distinct and route through `release/hashing.hash_table` alone. The
recorded OBS-1 fact stands: a non-canonically *ordered* JSON satisfies the SQL arithmetic
(demonstrated live), which affects representation, not membership. The corrected test suite pins
OBS-1 as open (`test_obs_1_remains_open_and_is_not_reported_as_fixed`). **OBS-1 is not fixed, not
closed, and not resolved**:

```text
OBS-1 = OPEN / NON-GATING / DEFERRED
```

## 14. OBS-B — defence in depth: confirmed non-defect

`document_adjudicated_evidence_requires_bound_artifact` is present, states an invariant
(adjudication binds what the accession's reviews bound) that is independent of registration truth,
refuses nothing lawful (every positive lifecycle passes through it), and was shown in the MIN-1
isolation probe to do real work when its siblings are absent. It is neither contradictory nor
harmful; its unreachability in the common path is a redundancy fact, not a finding. **Kept.**

## 15. Verified-evidence applicability: enforced at both layers

Schema: `evidence_kind` CHECK admits exactly `amendment_purpose` and `explicit_original` — probes
for `size`, `industry`, `history`, `primary_universe`, `cohort`, `xbrl_eligibility`,
`control_predicate`, and `name_ticker` all refuse at the kind, before `evidence_level` is
considered. Policy: `require_verified_evidence_applicable` admits exactly
`{amendment_purpose, amendment_linkage}` and refuses ten probed unauthorized dimensions including
the empty string. **No other evidence-level constraint widened**: comment lines excluded, the
candidate DDL admits `'verified'` in exactly the two authorized constraints; the
`filing_date`/`cohort`/`xbrl` evidence-level CHECKs still exclude it; the only other quoted
`'verified'` anywhere in the persisted schema is `census_plan_sources`' accepted migration-0004
**file-hash status** vocabulary (`not_verified`/`verified`/`missing`/`hash_mismatch`), byte-unchanged
history, not an evidence level. No generic escape hatch exists.

## 16. Linkage semantics: preserved

`amendment_linkage_state` keeps its accepted five-state vocabulary with `amends_original` for the
relationship; strength lives in `document_adjudicated_evidence.evidence_level = 'verified'`. No
executable `verified_amends_original` exists in schema or source — the sole textual occurrence is
the comment denying it; the vocabulary CHECK refuses it as a value (probed). The positive lifecycle
produced `amends_original` + verified provenance + quota eligibility without any new semantic
state (verified row: `('verified', 1, 'amends_original')`).

## 17. Review-epoch independence: enforced

One epoch wearing two roles REFUSED; an A or B epoch reused for adjudication REFUSED; the same
epoch reviewing a second accession in its one role ADMITTED; role/pass disagreement REFUSED;
`protocol_version` pinned by CHECK to `m3.3-document-evidence/1.0` (any other value refused) and by
the module constant. The resolved-route lifecycle carried three distinct opaque epochs. No personal
name is representable (`reviewer_model` charset excludes spaces — probed with a two-word name); no
session-ID column exists.

## 18. Append-only / freeze model: revalidated on every mutation surface

Beyond §6: `UPDATE`, `UPDATE OR REPLACE`, and `DELETE` refused outright on all four relations
(rowid-touch and column-targeted variants — role/epoch, artifact SHA, adjudicated value, span
text); review append after adjudication REFUSED; span append after consumption REFUSED; artifact
metadata immutable from insert. Every row is written frozen; no lifecycle transition or
convenience mutation path exists. The `writable_schema`/DDL route is outside the accepted 0013
threat model (schema vandalism, not a write idiom) and was used only by this review's own kill
probes on disposable catalogs.

## 19. Hash / identity discipline: intact

Seven new distinct evidence domains (`document_artifact`, `document_review_record`,
`document_review_span`, `document_adjudicated_evidence`, `document_review_a_table`,
`document_review_b_table`, `document_adjudication_table`); `document_evidence.py` imports
`hash_table` from `release/hashing.py` and performs no direct `hashlib` use, no IO, and no
environment access; `release/hashing.py` (blob `bbc2e903…`) and `candidate_identity.py` (blob
`e443ca23…`) are blob-identical from the pre-0015 R46 target `1c5b015` through `HEAD`, so
`ACCESSION_TABLE_COLUMNS` (32), `REGISTRANT_TABLE_COLUMNS` (6), and `SNAPSHOT_CONTENT_FIELDS` (12)
are unwidened by construction; VE-M12's pinned pre-0015 digest reproduces through the real
primitive; the 0014 and 0015 candidate tables carry identical column tuples and the evidence
relations ship empty. Candidate identity did not change because the evidence infrastructure
exists.

## 20. Migration-policy identity movement: independently reproduced

Endpoints verified from Git objects: pre-correction `0015` bytes hash to
`c53288947720f397cbb5e9661767bd37a67dbde76170bb7089df28d364d45593`; corrected bytes to
`d7f22999cb3e6736c765de72a1031c170f2cb5547ccaccf7469a2d3be018835f` — exactly the D088/D089 claim,
and the packaged-migration checksum equals the file digest. Line-level comparison of the
reserve-bearing manifest fixture between `fc972b5` and the target shows **exactly three** moved
values:

```text
selector_policy_sha256  2f675005… -> 2de6fd30…
root_manifest_sha256    317edeb1… -> 8c4fff82…
manifest_id             bd9cbce6… -> 5f3d0462…
```

with all **eight** substantive components byte-identical — `candidate_tables_sha256 b882a148…`,
`selection_result_sha256 1c7d8b8c…`, `source_observation_set_sha256`, `quota_definitions_sha256
0a2fd409…`, `selected_entities_sha256 86a18dac…`, `selected_accessions_sha256 541bbf7b…`,
`reserves_sha256 ac83550b…`, `quota_report_sha256 8b9bb4e4…` — and the canonical-JSON length
unchanged at 275721 (an existing block-5 row's checksum changed; no row was added). The fixture
executed live and green in targeted validation, confirming the corrected target actually produces
these values. Movement is confined to the accepted R68 path; **no other component moved.**

## 21. Private-root nonleakage: holds

`document_artifacts` carries exactly the seven contract columns — **no locator column exists**.
Probed refusals: `file:` URL, absolute and relative local paths, EDGAR-prefixed URL with a space,
non-Archives SEC URL, receipts carrying `/`, `:`, or `~`, span-location path shapes, and a
two-word `reviewer_model`. The module validator refuses `/`, `\\`, `:`, and `~` shapes and admits
clean opaque receipts; `document_evidence.py` resolves no path, opens no file, and reads no
environment variable. No `EV_ROOT` resolution, no real Decision-081 evidence, no network, SEC, or
HTTP access occurred anywhere in this review — every probe ran on synthetic identities against
disposable catalogs, and tracked network switches remain `false`/`false` with
`REQUEST_CEILING = 0` respected.

## 22. Migration 0015 — complete final review: clean

Chain position exactly `0015`, packaged inventory `0001`–`0015` contiguous, `0016` absent;
migrations `0001`–`0014` byte-unchanged (path-level Git proof). `0014 → 0015` upgrade through the
real runner applies exactly one migration on lawful empty state; a fresh build succeeds; the two
schemas are **byte-identical across all objects**; `foreign_key_check` and `integrity_check`
clean on both; `legacy_alter_table` restored to OFF; provenance records 15 contiguous rows with
the final checksum recognized on governed reopen. The empty-state precondition **refuses** a
catalog carrying a real candidate row and rolls the whole script back — the refused catalog
remains at `0014` with its row intact and zero evidence tables. The four relations carry exactly
23 triggers with the replacement/immutability families complete (4+4+4). Section 8's rebuild
reproduces the accepted 0014 candidate table with only the two authorized widenings;
`pilot_snapshot_freeze_requires_valid_state` is untouched. No accepted real state is reinterpreted
— and none exists: the evidence layer has never touched a real catalog.

## 23. VE-M1 … VE-M14: all fourteen families EFFECTIVE

All 44 VE-M tests executed green in targeted validation, and each family's protection was
independently re-derived by this epoch's probes: M1/M13 (path persistence and leakage — §21);
M2–M5 (post-freeze mutation — §§6, 18); M6 (applicability — §15); M7 (invented state — §16); M8
(bound-artifact provenance — §7); M9 (review provenance, exact set, span backing — §§7, 8); M10
(epochs — §17); M11 (artifact substitution — §§6, 7); M12 (identity — §19); M14 (no real
evidence, no IO — §21 and the empty-tables proof). **Reshaped assertions were inspected
specifically:** VE-M8's old fixture (a third record bound to another accession's artifact) is now
*unconstructible* one layer earlier; the new test asserts the review-layer refusal **and** that the
old adjudication-side trigger is kept, and the isolation probe proved that trigger still refuses
independently — the original structural guarantee did not disappear; the new mechanism is
strictly stronger. VE-M10's duplicate-record assertion moved from the UNIQUE-constraint message to
the replacement-guard message because the guard now fires first — the UNIQUE route is still
asserted structurally, and the guard additionally closes the `OR IGNORE` no-op the constraint
never could. Both changes strengthen; nothing weakened.

## 24. VE-R1 … VE-R10: load-bearing, none vacuous

Independently re-executed with this epoch's own mutations (no inheritance of the correction
report's results): **R1–R4** — each replacement guard's removal lands its exact attack (§6 kills);
**R5/R6** — binding-trigger removals land cross-bound state, and the pair reopens the full D087
lifecycle (§7); **R7** — the consistency trigger's removal re-admits `agreed`+`verified` over two
abstentions (§8); **R8** — the CHECK's removal admits `verified`+`abstained`, which the dedicated
negative test refuses, so the previously unprotected guard is now proven (§8); **R9** — the
one-column `UPDATE OF` regression re-points verified credit to an evidence-less accession (§9);
**R10** — the CHECK's removal admits `bytes:1a-2b` (§11). Every protection demonstrably refuses
the exact defect it names, and its removal demonstrably reopens it.

## 25. Positive lifecycle: admitted end to end

On synthetic disposable evidence (17/17): artifact → Review A + spans → Review B + spans →
`agreed`+`verified` adjudications for **both kinds** → verified, quota-eligible candidate carrying
`amends_original` → the `resolved` route through a genuine disagreement with a third adjudication
epoch (three distinct opaque epochs verified) → the lawful abstention routes per the §10
determination: both-abstain records `abstained`/NULL/`unavailable` and earns no candidate credit;
a one-sided abstention resolves through the third epoch to `resolved`+`verified` and lawfully
consumes candidate credit. The schema admits every lawful state the contract defines and refused
every false state probed against it.

## 26. Targeted validation and the single check-fast

| Command | Result | Elapsed |
|---|---|---|
| `make context` + `scripts/verify_target.py` | governance verified; 1/1 PASS | 0.54 s + 0.08 s |
| `probe_m1.py` | 119/119 | 0.71 s |
| `probe_min1.py` | 17/17 | 0.46 s |
| `probe_min2_obsa.py` | 27/27 | 1.51 s |
| `probe_obsa.py` | 5/5 hard rails + 9 recorded facts | 1.11 s |
| `probe_min3.py` | 13/13 | 0.59 s |
| `probe_boundary.py` | 84/84 | 0.52 s |
| `probe_migration.py` | 44/44 | 0.51 s |
| `probe_lifecycle.py` | 17/17 | 0.30 s |
| `make test PYTEST_ARGS="…verified_document_evidence …pilot_manifest_store …migration_provenance …storage_catalog …pilot_schema …multi_registrant_correction"` (serial) | **510 passed** | 43.63 s |
| `make check-fast` (run exactly once) | **green — all 11 gates** | 79.39 s |
| `pytest --collect-only -q` (collection only) | 4211 tests collected | 0.84 s |

**check-fast evidence chain, stated honestly.** This reviewer piped the run through `tail`, so the
per-gate output was truncated in the terminal capture; the run was **not** repeated (the packet
prohibits rerunning to recover output). The pass is established by: (1) `check-fast`'s gate list is
`lint format-check typecheck test-parallel secrets hygiene links decision-refs validate cohorts
sec-help` executed sequentially with make stopping at the first failure, and the captured output
ends with the **final** gate's full product (the SEC CLI help); (2) the tool reported no non-zero
exit; (3) the current collection is 4211 = the Decision 088-reported 4210 passed + 1 pre-existing
skip, and the suite ran to completion at 15:13 (`.pytest_cache/v/cache/nodeids` rewritten) while
`lastfailed` was **not** rewritten — its content is a stale 11:20 pre-correction artifact naming
since-deleted tests — which is pytest's zero-new-failures behaviour. No implementation was modified
at any point.

## 27. Prohibited nonchange: verified

Across the full `ddd582a..HEAD` delta the only `src/` changes are the two authorized new files
(migration `0015`, `document_evidence.py`) and `acquisition.py`'s single authorized constant
(`FINAL_MIGRATION_VERSION: 14 → 15`, the whole diff). `cohorts.py`, `pilot_policy.py`,
`candidate_identity.py`, `candidate_snapshot.py`, `offline_execution.py`, `release/hashing.py`,
every SEC transport/network module, migrations `0001`–`0014`, `Docs/preregistration.md`, Decisions
001–088, and every prior review artifact: byte-unchanged. `document_evidence.py` is byte-unchanged
across the D088 correction itself. Two test files outside Decision 087 §13's explicit list —
`test_m23_pilot_schema.py` and `test_m3_3_boundaries.py` — were touched by the implementation
commit with **mechanically necessary chain-head expectations only** (contiguity `0014 → 0015`;
the migration-boundary test now asserts the chain ends at `0015` and **fails on any `0016`**),
the same "chain-head expectations" genus §13 names for three sibling test files and necessarily
implied by the authorized migration; the D087 independent review examined that commit in full and
raised no boundary finding, and this review concurs. Decision 089 at `HEAD` is expected
governance. Migration `0016` ABSENT; `m3.2-complete` unmoved; no tag created; no real E0 state —
the evidence relations have never held a real row.

## 28. Findings

| Severity | Count | Items |
|---|---|---|
| BLOCKER | **0** | — |
| MAJOR | **0** | — |
| MINOR | **0** | — |
| OPTIMIZATION | **0** | — |
| OBSERVATION | **4** | OBS-1, OBS-A, OBS-B, OBS-C |

- **OBS-1** — contributor-JSON non-canonical encodings. **OPEN / NON-GATING / DEFERRED**; all four
  deferral assumptions independently confirmed (§13). Not fixed, not closed.
- **OBS-A** — the `abstained` asymmetry. **CLOSED / NON-DEFECT** by contract determination (§10).
- **OBS-B** — the bound-artifact invariant. **ACCEPTED NON-DEFECT**; kept as defence in depth (§14).
- **OBS-C** *(new, non-gating)* — the `agreed` consistency rule is scoped **per evidence kind to
  the adjudicated value**, exactly as accepted Decision 088 §5 specifies ("to carry the assertion
  the adjudicated value states, per evidence kind"). Consequently a §12.6 "every extracted
  assertion" disagreement confined to an **auxiliary** assertion — `original_accession_asserted`
  under an `explicit_original` adjudication (a field rule X-4 prohibits the protocol from
  depending on and which is deliberately absent from the adjudicated value), or the
  `original_form`/`date` fields under an `amendment_purpose` adjudication — is not a schema-level
  `agreed` refusal (demonstrated live). The credit-bearing value itself is always genuinely
  dual-asserted and span-backed; the auxiliary assertions remain visible in the immutable review
  records; routing fidelity for such cases rests with the R64 protocol execution and AP-7 owner
  acceptance, as in §10. Faithful to the owner's accepted correction formula; **no correction
  proposed and none authorized**; recorded so a future protocol-execution record can carry it
  knowingly.

**PASS standard met: BLOCKER 0 / MAJOR 0 / MINOR 0.**

## 29. Formal acceptance conditions

| Condition | State |
|---|---|
| Full corrected verified-evidence infrastructure formally acceptable | **YES** |
| All D087 findings independently closed (M-1, MIN-1, MIN-2, MIN-3, OBS-2, OBS-3) | **YES — re-proved, not inherited** |
| D088 corrections effective and bounded | **YES** |
| OBS-A contract-faithful or otherwise resolved | **YES — CLOSED / NON-DEFECT** |
| OBS-1 demonstrably non-gating | **YES — confirmed, remains open/deferred** |
| B0 / M0 / MIN0 | **YES** |

## 30. Verdict

```text
VERDICT: PASS
M3_3_D088_VERIFIED_EVIDENCE_FRESH_REREVIEW_PASSED_READY_FOR_OWNER_ACCEPTANCE
```

**A PASS is not acceptance and authorizes nothing.** Per Decision 089: the D087 verified-evidence
schema remains **NOT YET OWNER ACCEPTED** until Sol/GPT's final owner acceptance; document Review
A, Review B, and the adjudication remain **UNAUTHORIZED**; **M3.3-E0**, **E1**, **E2**, and
**M3.4** remain **UNAUTHORIZED**; the 108 real D081 review outcomes are not inserted and the D081
private evidence was not accessed; `M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN` and
`M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN` remain **OPEN** and unmerged;
`REAL_ACCEPTANCE_ORDERING_ADEQUACY` remains **PENDING FUTURE AUTHORIZED E0 VERIFICATION**;
network, SEC, and HTTP authority is **NONE** with `REQUEST_CEILING = 0`; migration `0016` is
**NOT AUTHORIZED**; `m3.2-complete` is unmoved and no tag was created.

**NEXT ACTION: RETURN TO SOL/GPT for final owner acceptance.**
