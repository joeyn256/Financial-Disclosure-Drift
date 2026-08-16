# Decision 097 — M19 Live-Anchor Supersession and Exact Audit-Gate Correction

**Date:** 2026-08-16
**Status:** ACCEPTED — OWNER EXCEPTIONAL POST-D096 BLOCKER CORRECTION AUTHORITY
**Outcome:** `M3_3_D097_M19_LIVE_ANCHOR_SUPERSESSION_OWNER_ACCEPTED`
**Stage:** M3.3 PRE-E0 executability implementation
**Authority:** Sol/GPT owner adjudication on Joey's explicit instruction

The owner's instruction is:

> Fix the blocker

It approves the narrow correction recommended in the immediately preceding Sol/GPT D096 owner
handoff. This record makes that authority durable and exact. It does not revive ordinary automatic
remediation: Decision 096 correctly exhausted the normal loop, the blocker was returned to the
owner, and the owner has now explicitly authorized this one exceptional correction.

## 1. D096 result and exact blocker

The fresh Decision-096 executor ran from 2026-08-16 04:55:39 through 05:54:50 EDT in ACP session
`agent:claude:acp:f82db731-5340-46c5-9aea-f94249323ba9`, OpenClaw session
`b09d1fa0-af41-4a8a-b3f7-29a9592e9560`, and Claude harness session
`be1f01ac-e511-4f05-a68b-5633e08549c7`. Harness evidence attested 360/360 assistant records as
actual `claude-opus-5`; the session was fresh and non-resumed. Maximum was requested by the parent,
with the CLI-visible effort limitation already accepted by Decision 096 R85.

The executor completed the Decision-094/095/096 implementation and direct proof surfaces, including
Decision 096 R83/R84, but the sole final `make check-fast` attempt returned:

```text
4350 passed / 1 failed / 1 skipped
FAILED tests/unit/test_audit_tooling.py::test_all_38_anchors_resolve_against_the_live_target
observed missing anchors = ["M19"]
```

The check log's SHA-256 is
`14be287bc5c8def10b10e9fd0a11317c1c402d001b1f07c5f1d7b07ce4d8179f`. Ruff, formatting, and
mypy passed before pytest; the remaining gates were run individually and passed. No implementation
commit, push, tag, migration, E0 operation, private-root access, or network act occurred.

The blocker is a collision between two accepted records:

1. Decision 076 section 9 made the durable M1-M38 historical campaign recoverable and referred any
   missing live anchor to the owner rather than fabricating it. Its audit test expected all 38
   historical anchors to remain present in the live target.
2. Later Decision 094 section 6.5 deliberately removed the candidate-layer
   `_read_full_index_registrants` observation fallback and made the canonical
   `census_accession_registrants` relation plus `registrant_set_completeness` the only consumer
   source. Decision 096 R83 then placed malformed full-index CIK refusal at the pre-association E0
   projection, with a stronger positive/adversarial proof.

M19's historical mutation targets the deleted candidate-layer query:

```text
WHERE o.field_name = 'cik_padded' AND s.source_id = 'sec_full_index_company'
```

Restoring that query would violate Decision 094. Adding it as dead code or a comment would be gate
gaming. Editing the immutable historical campaign artifact would rewrite accepted evidence. The
runner's report of `anchors_missing = ["M19"]` was therefore the correct owner-referral behavior.

## 2. Preserved implementation WIP

The entry governance HEAD is `8ff63bff8f9552a94fbbc67ed5becf362aa776dc`, tree
`57d1c4709b3d4af8e419afd7cdfebeafcbcf1065`, parent
`4643e57e3d296ac546ff720963499bbd76c0dee9`, on `main`, three commits ahead of and zero behind
recorded `origin/main` `4ed0fc7f67c3f9b4f5750e7c24432269aed9ffc4`. Nothing is staged.

The exact unaccepted D096 WIP is preserved, not reset, cleaned, stashed, or accepted merely by this
record:

| Path | SHA-256 |
|---|---|
| `Docs/change_impact_map.md` | `795b44422aebc7bbf12bbc1f2cc7639ee234e07ec0d374c37b5193efd5c51e2d` |
| `Docs/m3/execution_receipt_spec.md` | `1c9c61255d743e687e5939c6aa858e5771f7bd1ca9b9a9fc140fefb3c1c3aa84` |
| `Docs/m3/operator_runbook.md` | `fb0acfb52fcc6359cab329f63a8f0dbb5a3fc715b40c18f30a8e4d7d4f1be5c7` |
| `Docs/sec_data_dictionary.md` | `c4bca216c96a19164a6fef6283f371bdb5346acd3fd2192cda96870eaedb5810` |
| `src/disclosure_drift/cli.py` | `e11c1274e8122b235bcbc6ddfe8f2e0657999b7926576f1f11769e2da80fdffd` |
| `src/disclosure_drift/config.py` | `719c83b4c6377a3f37ed798651cdad24bb5f031af5f7215ed4ea7a1fef7c6981` |
| `src/disclosure_drift/m3/candidate_snapshot.py` | `927043e7dc8ec19a6eb031b800b18fd9987925be7f30d164c1438621c3551cfa` |
| `src/disclosure_drift/m3/execution_rehearsal.py` | `75df01da43f063aff0ec64c4636054b564c3219edbeabaaa8d54788eb198b062` |
| `src/disclosure_drift/m3/offline_parse.py` | `2b0011e0089f7a30db6875267547d6e5d401186f8030d5dc38cd9c33d361b0b6` |
| `src/disclosure_drift/m3/receipt.py` | `9b358ed00de5779683be2cb91b52bf90d144ede0ac3322d6bd1980d2bcb7f81d` |
| `src/disclosure_drift/m3/rehearsal_world.py` | `16398c7aad4615bfd734d3c60deb5ac85e20be8fb74a9cda9d7319caf4fa799b` |
| `tests/integration/test_cli.py` | `28232ee771a67b79e37802dce80402c44ccd207381c50c3f9825aa475c923453` |
| `tests/integration/test_m3_cli.py` | `7565d81fa6497d34f5eaac444c2be84be5e31d80aa42d843cbc2a6da177e60ee` |
| `tests/unit/test_env_overrides.py` | `7d8203af141d9716c06d029092b24f19aa9d0f74befeb9aadcc6e9dcad9b6b41` |
| `tests/unit/test_m3_3_execution.py` | `9c96340de5b62e4a2960872f494f6197b9ebe558e25e8f95a6c05efb873b0723` |
| `tests/unit/test_m3_candidate_snapshot.py` | `5338655dbe12f3408c10dd751cbd02225aba4dd10c9b415dd011fd80b309be5f` |
| `tests/unit/test_m3_offline_parse.py` | `92651cd0c9c5759f11f74398b83720634bd9bc29d5fd29e3872f595128d5eeb5` |
| `tests/unit/test_m3_receipt.py` | `16e57f58dbc92e87245ea9c683d26e0e6cd65208aa8196db85908ca6a1ce1b9c` |
| `tests/unit/test_migration_provenance.py` | `d4d9507e349129aacc2d44ead5238e6ff72ee8f045c2fbd7a3436e95461896e5` |
| `Docs/m3/e0_execution_record_spec.md` | `7ae4b8423d09e2e4fd827533dff99464e9963d41c11302b68ef7271806290a08` |
| `src/disclosure_drift/m3/e0.py` | `6de8aae95f6f7a8e48546a225f576a5b8ce7d8c17ca25f55517afd2839c08b72` |
| `tests/unit/test_m3_e0.py` | `8b063a1de4348575bab999e73596df27d997e41991c658ee5a9312e33a8fc1de` |

The executor must verify every hash before editing. Any mismatch is a STOP. These bytes remain an
unaccepted candidate until the required gate, commit, and later owner review occur.

## 3. Ruling R87 — M19 historical evidence is preserved and live applicability is superseded

The M19 definition, its two historical KILLED results, and
`Docs/m3/reviews/m3_3_i_r_mutation_campaign_06bb47a.md` remain immutable and truthful for the frozen
targets they describe. Nothing is deleted, rewritten, reclassified as a historical survivor, or
made to appear as though M19 never existed.

For the current live target only, M19 is **SUPERSEDED BY DECISION 094 SECTION 6.5 AND DECISION 096
R83**. The live applicability partition is exactly:

```text
historical definitions recovered = 38
live anchors resolved = 37
superseded live anchors = ["M19"]
unexpected missing anchors = []
```

M19's successor proof is the Decision-096 R83 pre-association E0 proof in
`tests/unit/test_m3_e0.py`: a positive canonical projection, an isolated invalid full-index CIK
rendering, failure on `invalid_cik_rendering_count`, transaction rollback, no established
projection, no invented entity, and no candidate/scalar/observation fallback. This is stronger than
restoring the obsolete candidate-layer mutation because it exercises the production layer that now
owns the invariant.

No generic missing-anchor exception is created. M18, M20, and every other M1-M38 anchor remain
required. A second missing anchor is a new failure and may not be hidden under M19's disposition.

## 4. Ruling R88 — exact audit-test correction

The sole new executable edit authority is:

```text
tests/unit/test_audit_tooling.py
```

The correction must replace the stale 38-of-38 live-target assertion with a test that directly and
load-bearingly proves all of the following:

1. all 38 historical definitions still recover, in exact M1 through M38 order;
2. `verify_anchors()` returns exactly `['M19']` against the live target;
3. the missing definition is exactly M19, targeting
   `src/disclosure_drift/m3/candidate_snapshot.py`, semantic locus
   `_read_full_index_registrants`, and the frozen full-index observation query;
4. `_read_full_index_registrants`, its M19 anchor, and `sec_full_index_company` are absent from the
   live candidate builder;
5. `census_accession_registrants` and `registrant_set_completeness` remain present as the canonical
   consumer source; and
6. any missing anchor other than or in addition to M19 fails the exact assertion.

The test may be renamed to state the truthful 37-live-plus-one-superseded invariant. It may update
only directly corresponding module prose. It may not edit the mutation runner, the historical
campaign artifact, production source, another test, or any D094-D096 WIP byte.

`scripts/dev/mutation_campaign.py` is deliberately unchanged. Its current machine-readable
`anchors_missing` field and nonzero owner-referral result remain truthful. A new generic
`superseded` runner channel is unnecessary for this correction and would be a broader audit-tooling
methodology change.

## 5. Ruling R89 — one exceptional correction epoch, validation, and commit

One genuinely fresh Claude Opus 5 Maximum executor is authorized. Before substantive reading or
mutation it must attest actual `claude-opus-5`; if the model differs or cannot be truthfully
attested, it stops. The accepted CLI-visible effort limitation from Decision 096 R85 remains.

The executor must:

1. verify the exact governance HEAD supplied in its packet and every section-2 WIP hash;
2. reproduce the single M19 audit-test failure before editing;
3. edit only `tests/unit/test_audit_tooling.py`;
4. run the corrected audit module plus the Decision-096 R83 successor proof in
   `tests/unit/test_m3_e0.py` using repository Python 3.12 and with the evidence-root variable unset;
5. prove non-vacuity from the red-before/green-after transition and one bounded isolated mutation
   changing the expected superseded ID away from M19, which must fail and be fully restored;
6. run touched-file Ruff and format checks;
7. run exactly one post-correction `make check-fast`; and
8. commit only if every required check passes and no unauthorized byte changed.

The one local implementation commit is authorized with exact subject:

```text
feat: implement Decision 094 pre-E0 execution surfaces
```

It may contain only the 22 preserved D096 WIP paths in section 2 plus
`tests/unit/test_audit_tooling.py`. The executor must stage those exact paths explicitly, never use
`git add -A`, and confirm the committed diff contains no governance file from this Decision's
separate governance commit. No push, tag, amend, rebase, force operation, stash, branch, worktree,
release, or publication is authorized.

If targeted validation, mutation proof, or `make check-fast` fails, no commit is created and the
session returns blocked. This authority does not permit another automatic correction after that
failure.

## 6. Governance commit

Sol/GPT may commit this Decision and its current-state navigation overlays without staging any D096
WIP. The exact governance subject is:

```text
docs: accept Decision 097 M19 supersession correction
```

This governance commit changes no production, test, migration, configuration, accepted evidence,
or historical Decision byte. It does not itself fix the audit test or accept the implementation.

## 7. Review and acceptance boundary

A passing gate and implementation commit produce a candidate for Sol/GPT verification. They do not
activate either execute constant, apply a migration, run E0, close the linkage gate, authorize E1,
or accept the entire PRE-E0 implementation automatically.

Sol/GPT must verify actual model identity, entry hashes, the exact one-file correction, M19
specificity, R83 successor non-vacuity, the full gate, commit contents, current Git state, and the
absence of prohibited acts. Decision 094 section 12.4's owner-controlled fresh read-only independent
review boundary remains available and is neither run nor waived by this record.

## 8. Acts still prohibited

This Decision authorizes no:

- edit to `scripts/dev/mutation_campaign.py`, the historical campaign artifact, production source,
  a migration, or any test other than `tests/unit/test_audit_tooling.py`;
- accepted private-root discovery or access;
- accepted-catalog migration `0014`/`0015`, migration `0016`, transition, E0, linkage diagnostic,
  persistence bridge, E1, E2, or M3.4;
- activation of `PRE_E0_CATALOG_TRANSITION_AUTHORITY` or `M3_3_E0_EXECUTION_AUTHORITY`;
- network, SEC, HTTP, DNS, socket, acquisition, reacquisition, or package installation;
- push, tag, publication, release, or history rewrite; or
- claim that historical M19 evidence is invalid, deleted, or rerun against the current target.

The request and attempt ceilings remain zero. Both execute constants remain exactly `None`. E0
remains operationally HELD.

## 9. Exact next action

1. Commit this governance record and its clean current-state overlays without staging D096 WIP.
2. Dispatch one fresh actual-model-attested Claude Opus 5 Maximum executor under R87-R89.
3. Return the candidate or blocker to Sol/GPT for independent verification.
4. Do not migrate, run E0, or infer later-stage authority.

`RESULT_TOKEN: M3_3_D097_M19_LIVE_ANCHOR_SUPERSESSION_OWNER_ACCEPTED`
