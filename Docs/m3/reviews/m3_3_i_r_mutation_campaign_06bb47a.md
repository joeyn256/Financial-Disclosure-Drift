# M3.3-I/R Mutation Campaign M1–M38 — corrected executable target `06bb47a`

```text
ARTIFACT: DURABLE MUTATION-CAMPAIGN RECORD — NOT AN INDEPENDENT ACCEPTANCE REVIEW
DATE: 2026-08-14
AUTHOR: the correction-authoring session (Claude Opus 5, maximum effort, single fresh epoch)
AUTHORITY: accepted Decision 075 §6 (OBS-6), under accepted Decisions 070–074

CORRECTED_EXECUTABLE_TARGET: 06bb47a89eafc597c295a40eefd49cc71b50b0ec
TREE:                        360e778ddee91c6cf7388b93355fdcddf6442ca7
PARENT:                      6b8968f3a9ea3502471d3e9efb1268ce8cdb7385

FINAL_RESULT: 38 KILLED / 0 SURVIVORS
POSITIVE_CONTROL: PASSING
RESIDUE: ZERO
EVERY_MUTATION_DURABLY_RECOVERABLE: YES — 0 recorded NOT_DURABLY_RECOVERABLE
```

**This record exists for reviewability, not as a narrative.** Accepted Decision 075 §6 adopts
**OBS-6**: the existing campaign remains valid and is **not** retroactively upgraded to a MINOR, but
the owner requires a durable, reviewable, per-mutation record before formal acceptance. **It
authorizes nothing.** A fully killed campaign is not an ultrareview pass, not an acceptance, and not
an authorization for M3.3-E0, M3.3-E1, M3.3-E2, or M3.4.

---

## 1. Provenance of these facts — recovered, never fabricated

Decision 075 §6 forbids inventing a mutation definition. Every fact below comes from one of three
sources, and each is named:

| Fact | Source |
|---|---|
| All 38 mutation IDs, governing rules, target files, exact `old` → `new` edits, and killing test selections | The **retained campaign runner** from the implementing session's own working directory, read verbatim and unmodified (SHA-256 `b801cb053261e533261a96b4ae3353ee2d9edbfae605dacc4c1474517cf800b5`). Its `MUTATIONS` table was **executed** to render §5 below, so no definition is hand-transcribed |
| Each mutation's semantic locus (enclosing function or module scope) | Derived **mechanically** by locating each anchor in the corrected executable source and resolving the enclosing `def` / `class` by AST walk |
| Which seven mutations initially survived on target `6f87abc`, and that each was closed by a narrow added test | The committed implementer evidence record [`m3_3_i_r_rehearsal_6f87abc.md`](m3_3_i_r_rehearsal_6f87abc.md) §12, and the `M3_3_I_R_MUTATION_CAMPAIGN_STATUS` marker in `Milestones/STATUS.md` |
| Which specific test closed each of those seven | The `Group K: mutation-campaign survivors, closed narrowly` block in `tests/unit/test_m3_3_execution.py`, matched subject-for-subject against that §12 enumeration |
| Every `Reverification run (target 06bb47a)` result, the positive control, the residue check, and the final tally | A **fresh execution** of the same retained runner against the corrected executable target, performed for this record |

**No mutation is recorded `NOT_DURABLY_RECOVERABLE`.** All 38 definitions were recovered exactly,
and every anchor was located in the corrected source — which is itself evidence that the recovered
definitions match the executable target they claim to describe.

**What is NOT claimed.** The original campaign's per-mutation *console output* for target `6f87abc`
was not retained as a file. This record therefore states the original per-mutation outcome only at
the granularity the committed evidence supports: the **seven named** mutations initially survived
and were closed, and the campaign finally reported **38 killed / 0 survivors** with a passing
positive control and zero residue. Every per-mutation **KILLED** in the `Reverification run` column
is an outcome this session **observed directly**.

## 2. CAMPAIGN_IMPLEMENTATION — how mutations were applied in isolation

One deterministic source edit at a time, applied to a working-tree file, followed immediately by
that mutation's designated killing test selection.

- The runner reads **every** target file's original bytes into memory **before** any mutation runs,
  and keeps them for the whole campaign.
- Each mutation is a **single** `str.replace(old, new, 1)` — the **first** occurrence only, never a
  global substitution.
- If the anchor is **absent**, the mutation is **not** applied: it is reported `SKIP anchor not
  found` and counted as a **survivor**, so a silently stale definition can never be mistaken for a
  kill. **No mutation was skipped in the reverification run.**
- The killing selection runs under `pytest -x -q --no-header -p no:cacheprovider`.
- `PYTHONDONTWRITEBYTECODE=1` is set for every subprocess, so a restored file can never be shadowed
  by a stale `.pyc` that collides with it on `(mtime, size)`.
- A mutation is **KILLED** when its designated selection **fails**, and a **SURVIVOR** when it
  passes.
- The runner is a **temporary, session-local tool**. It is **not** added to production source, **not**
  part of the package runtime, and **not** committed; no mutated copy of any source file and no
  scratch file is committed.

## 3. POSITIVE_CONTROL — procedure and observed result

Before any mutation is applied, the runner executes **every distinct test selection** the campaign
will use, against **unmutated** source. Any failure **aborts the campaign** before a single mutation
is applied, so a selection that was already red can never be miscounted as a kill.

Observed, against corrected target `06bb47a` — **11 distinct selections, all PASS**:

```text
control tests/unit/test_m3_3_execution.py: PASS
control tests/unit/test_m3_candidate_events_and_controls.py: PASS
control tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_3_execution.py: PASS
control tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_candidate_snapshot.py: PASS
control tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py: PASS
control tests/unit/test_m3_candidate_identity.py: PASS
control tests/unit/test_m3_candidate_identity.py tests/unit/test_m3_candidate_snapshot.py: PASS
control tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py: PASS
control tests/unit/test_m3_offline_parse.py: PASS
control tests/unit/test_m3_offline_parse.py tests/unit/test_m3_3_execution.py: PASS
control tests/unit/test_m3_support_target_pairs.py tests/unit/test_m3_3_execution.py: PASS
```

## 4. SOURCE_ISOLATION, RESTORATION, and RESIDUE_CHECK

**SOURCE_ISOLATION — how the campaign proved it was mutating the intended executable source.**
Every path is resolved against the repository root that holds the corrected executable target, and
the mutation is written to that exact tracked file — never to a copy, a clone, an installed package,
or a shadow tree. The package is installed in editable (`src`) layout, so the file under test **is**
the file mutated. Three independent checks bind the campaign to the intended source: the runner
**requires** each anchor to be present in the file's original bytes and refuses to fabricate a kill
when it is not; each file's **entry SHA-256** is captured before any edit and re-verified after;
and every subprocess writes no bytecode, so no stale artifact can stand in for the mutated or the
restored file. **All 38 anchors resolved in the corrected source**, and the eleven mutated files are
exactly the executable modules this stage owns.

**RESTORATION — how the original bytes were restored after each mutation.** Each mutation's write is
wrapped in `try` / `finally`, and the `finally` clause unconditionally calls
`target.write_bytes(originals[mutation.path])` — restoring from the **in-memory byte copy taken
before the campaign**, not from a re-read, a backup file, or a VCS operation. Restoration therefore
happens even when the test run raises, and no failure path can leave a mutation in place.

**RESIDUE_CHECK — the exact final check.** After the last mutation, the runner recomputes the
SHA-256 of **every** touched file and compares it against that file's entry digest, printing
`RESIDUE in <path>` for any mismatch and failing the campaign. Observed:

```text
=== residue check ===
  zero residual mutation: yes
=== survivors: 0 ===
```

Independently confirmed after the run: `git status --short` is **empty**, `HEAD` is still
`06bb47a89eafc597c295a40eefd49cc71b50b0ec`, and the eleven mutated files carry these digests, which
are the committed target's own bytes:

| File | SHA-256 after the campaign |
|---|---|
| `src/disclosure_drift/m3/candidate_events.py` | `d1ad7cba03e118333cf933e007d61d1481db083bc37541d08d4f2c3fc64be235` |
| `src/disclosure_drift/m3/candidate_classification.py` | `0ffc9b49e953f117f164d111f95cba3f3121f9aaeafa1acdd817c74d93e7b2a8` |
| `src/disclosure_drift/m3/candidate_controls.py` | `ff410b6ab909302392d732c7dc1d39d6052be0a867538eac0631712332c574f0` |
| `src/disclosure_drift/m3/candidate_identity.py` | `cbbe0147f09195ef1989a03ebce1f2b75ddf4e395bb1c7db19f0a076631fb508` |
| `src/disclosure_drift/m3/candidate_snapshot.py` | `adcb218ac98f9889f6beb6b0907f4ac4318c07fbd73f1e62fdd9c5a763d95006` |
| `src/disclosure_drift/m3/support_target_pairs.py` | `315aa669359267eadbd2a01ecdbb6ec7ab20622d2df03d5babc33fc699774cc8` |
| `src/disclosure_drift/m3/offline_parse.py` | `e1ac49d84145a24b17fae71b7d7ef24adb0fa4f62ca2c10ff453d9a9bc7ce47d` |
| `src/disclosure_drift/m3/rehearsal_snapshot.py` | `3cf24708a121f56b5e4b10adb3e2dc6d1e9609dfa6a304d1fb4350c88c97f8be` |
| `src/disclosure_drift/m3/offline_execution.py` | `e562f79b6ca5e937c31444297e8805f143afcfe691bf3cafba25dc2e720485cc` |
| `src/disclosure_drift/m3/execution_rehearsal.py` | `3e279e7f83249b1b8b1850f8b0bf4baa2b419360c359a081a4a5bf131f47f6be` |
| `src/disclosure_drift/sec/reserve_selector.py` | `52bbed4e6c70f080d63cbec15b7c88a3869ef5e090a81484e0f8f9112be426dd` |

## 5. The mutations, M1–M38

Each entry gives the mutation ID, the governing rule, the exact target file, the exact semantic
locus, the exact mutation applied, the expected killing test selection, the observed result on each
run, whether it survived, the correction made if it initially survived, and its final status.

**Coverage by governing record.** Decision 071 (**R19**, **R20**, **R21**, **IN-2**, **IN-3**) —
M1–M17; Decision 072 (**R22**–**R24**, plus **R17**, **R18**, and **R14** containment and
disposition) — M18–M25; Decision 073 (**R27**, **R28**, plus **R5**, **OQ-3**, **R3**) — M26–M32;
Decision 074 (**R31**, **R32**, **R33**) — M33–M38.

### M1 — status flags matched as a substring instead of exact equality

| Field | Value |
|---|---|
| Mutation ID | **M1** |
| Governing rule | **R19 4.1-4.4** |
| Target file | `src/disclosure_drift/m3/candidate_events.py` |
| Semantic locus | function `_status_flags` (line 177) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
return {flag for flag, token in CANONICAL_STATUS_TOKENS.items() if token in canonical}
```

is replaced by

```python
return {flag for flag, token in CANONICAL_STATUS_TOKENS.items() if any(token in value for value in canonical)}
```

### M2 — ticker reuse admitted as succession evidence

| Field | Value |
|---|---|
| Mutation ID | **M2** |
| Governing rule | **R19 4.5** |
| Target file | `src/disclosure_drift/m3/candidate_events.py` |
| Semantic locus | module scope (line 99) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
LINEAGE_SUCCESSION_EVIDENCE_KINDS: Final[frozenset[str]] = frozenset({"company_name"})
```

is replaced by

```python
LINEAGE_SUCCESSION_EVIDENCE_KINDS: Final[frozenset[str]] = frozenset({"company_name", "ticker"})
```

### M3 — a generic lineage edge proxies the reverse-merger condition

| Field | Value |
|---|---|
| Mutation ID | **M3** |
| Governing rule | **R19 4.6** |
| Target file | `src/disclosure_drift/m3/candidate_events.py` |
| Semantic locus | module scope (line 104) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
REVERSE_MERGER_EVIDENCE_KINDS: Final[frozenset[str]] = frozenset({"reverse_merger", "de_spac"})
```

is replaced by

```python
REVERSE_MERGER_EVIDENCE_KINDS: Final[frozenset[str]] = frozenset({"reverse_merger", "de_spac", "company_name"})
```

### M4 — any report-date pair counts as a fiscal-year-end change

| Field | Value |
|---|---|
| Mutation ID | **M4** |
| Governing rule | **R19 4.7** |
| Target file | `src/disclosure_drift/m3/candidate_events.py` |
| Semantic locus | function `_fiscal_year_end_change` (line 202) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
if circular_month_day_distance(first, second) > FYE_CIRCULAR_TOLERANCE_DAYS:
```

is replaced by

```python
if circular_month_day_distance(first, second) >= 0:
```

### M5 — an unresolvable comparison silently becomes no event

| Field | Value |
|---|---|
| Mutation ID | **M5** |
| Governing rule | **R19 4.7** |
| Target file | `src/disclosure_drift/m3/candidate_events.py` |
| Semantic locus | function `_fiscal_year_end_change` (line 199) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
        if first is None or second is None:
            unresolved = True
            continue
```

is replaced by

```python
        if first is None or second is None:
            continue
```

### M6 — an ordinary amendment counts as a transition report

| Field | Value |
|---|---|
| Mutation ID | **M6** |
| Governing rule | **R19 4.8** |
| Target file | `src/disclosure_drift/m3/candidate_events.py` |
| Semantic locus | module scope (line 107) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
TRANSITION_REPORT_FORMS: Final[frozenset[str]] = frozenset({"10-KT", "10-KT/A"})
```

is replaced by

```python
TRANSITION_REPORT_FORMS: Final[frozenset[str]] = frozenset({"10-KT", "10-KT/A", "10-K/A"})
```

### M7 — an unresolved fact becomes stable rather than review_required

| Field | Value |
|---|---|
| Mutation ID | **M7** |
| Governing rule | **R19 4.13** |
| Target file | `src/disclosure_drift/m3/candidate_classification.py` |
| Semantic locus | function `classify_history` (line 215) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_candidate_snapshot.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    if detection.unresolved:
        return None, "review_required"
```

is replaced by

```python
    if detection.unresolved:
        pass
```

### M8 — the four-original stable condition is lowered

| Field | Value |
|---|---|
| Mutation ID | **M8** |
| Governing rule | **R19 4.13** |
| Target file | `src/disclosure_drift/m3/candidate_classification.py` |
| Semantic locus | module scope (line 145) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_candidate_snapshot.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
STABLE_MINIMUM_ORIGINAL_ANNUAL_REPORTS: Final = 4
```

is replaced by

```python
STABLE_MINIMUM_ORIGINAL_ANNUAL_REPORTS: Final = 1
```

### M9 — the RIC/ETF SIC set is broadened by proximity

| Field | Value |
|---|---|
| Mutation ID | **M9** |
| Governing rule | **R20 6.1/R26** |
| Target file | `src/disclosure_drift/m3/candidate_controls.py` |
| Semantic locus | module scope (line 64) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **SURVIVED**, then closed |
| Correction made | Closed by a **narrow added test**, never by weakening the mutation: `test_the_ric_etf_sic_set_is_exactly_the_two_enumerated_codes` |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
RIC_ETF_SIC_CODES: Final[frozenset[str]] = frozenset({"6722", "6726"})
```

is replaced by

```python
RIC_ETF_SIC_CODES: Final[frozenset[str]] = frozenset({"6722", "6726", "6798"})
```

### M10 — an annual report establishes the asset-backed control

| Field | Value |
|---|---|
| Mutation ID | **M10** |
| Governing rule | **R20 6.2** |
| Target file | `src/disclosure_drift/m3/candidate_controls.py` |
| Semantic locus | module scope (line 71) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
ASSET_BACKED_FORMS: Final[frozenset[str]] = frozenset({"10-D"})
```

is replaced by

```python
ASSET_BACKED_FORMS: Final[frozenset[str]] = frozenset({"10-D", "10-K"})
```

### M11 — a 20-F/A alone satisfies the foreign-private-issuer predicate

| Field | Value |
|---|---|
| Mutation ID | **M11** |
| Governing rule | **R20 6.4** |
| Target file | `src/disclosure_drift/m3/candidate_controls.py` |
| Semantic locus | function `original_forms` (line 152) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **SURVIVED**, then closed |
| Correction made | Closed by a **narrow added test**, never by weakening the mutation: `test_an_amendment_alone_never_establishes_the_foreign_private_issuer_control` |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
return frozenset(form for form in forms if not form.endswith("/A"))
```

is replaced by

```python
return frozenset(forms)
```

### M12 — an overlapping control is resolved by precedence

| Field | Value |
|---|---|
| Mutation ID | **M12** |
| Governing rule | **R20 6.5** |
| Target file | `src/disclosure_drift/m3/candidate_controls.py` |
| Semantic locus | function `classify_control_kind` (line 140) |
| Expected killing test selection | `tests/unit/test_m3_candidate_events_and_controls.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    return ControlClassification(
        control_kind=None, status="conflicting", satisfied=tuple(satisfied)
    )
```

is replaced by

```python
    return ControlClassification(
        control_kind=satisfied[0], status="resolved", satisfied=tuple(satisfied)
    )
```

### M13 — the XBRL composite resolved value drops one of its two bound facts

| Field | Value |
|---|---|
| Mutation ID | **M13** |
| Governing rule | **R21** |
| Target file | `src/disclosure_drift/m3/candidate_identity.py` |
| Semantic locus | module scope (line 186) |
| Expected killing test selection | `tests/unit/test_m3_candidate_identity.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
COMPOSITE_RESOLUTION_DIMENSIONS: Final[frozenset[str]] = frozenset({"xbrl"})
```

is replaced by

```python
COMPOSITE_RESOLUTION_DIMENSIONS: Final[frozenset[str]] = frozenset()
```

### M14 — a weaker observation displaces the strongest contributor

| Field | Value |
|---|---|
| Mutation ID | **M14** |
| Governing rule | **R16-C1** |
| Target file | `src/disclosure_drift/m3/candidate_identity.py` |
| Semantic locus | function `resolution_contributors` (line 430) |
| Expected killing test selection | `tests/unit/test_m3_candidate_identity.py tests/unit/test_m3_candidate_snapshot.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
        strongest = min(row.precedence for row in group)
```

is replaced by

```python
        strongest = max(row.precedence for row in group)
```

### M15 — disagreeing equal-authority peers still contribute

| Field | Value |
|---|---|
| Mutation ID | **M15** |
| Governing rule | **R16-C1** |
| Target file | `src/disclosure_drift/m3/candidate_identity.py` |
| Semantic locus | function `resolution_contributors` (line 432) |
| Expected killing test selection | `tests/unit/test_m3_candidate_identity.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
        if len({row.canonical_observed_value for row in peers}) > 1:
            continue
```

is replaced by

```python
        if False:
            continue
```

### M16 — the builder invents an amendment-purpose category from the form suffix

| Field | Value |
|---|---|
| Mutation ID | **M16** |
| Governing rule | **IN-2** |
| Target file | `src/disclosure_drift/m3/candidate_snapshot.py` |
| Semantic locus | function `_derive_accession` (line 1022) |
| Expected killing test selection | `tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    purpose_category: str | None = None
    purpose_level = "unproven" if is_amendment else "unavailable"
```

is replaced by

```python
    purpose_category = "administrative_or_exhibit" if is_amendment else None
    purpose_level = "provisional" if is_amendment else "unavailable"
```

### M17 — the six-distinct-entity pair quota is lowered

| Field | Value |
|---|---|
| Mutation ID | **M17** |
| Governing rule | **IN-3** |
| Target file | `src/disclosure_drift/m3/support_target_pairs.py` |
| Semantic locus | module scope (line 50) |
| Expected killing test selection | `tests/unit/test_m3_support_target_pairs.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
REQUIRED_SUPPORT_TARGET_PAIR_ENTITIES: Final = 6
```

is replaced by

```python
REQUIRED_SUPPORT_TARGET_PAIR_ENTITIES: Final = 1
```

### M18 — the full index is demoted out of the candidate-substantive set

| Field | Value |
|---|---|
| Mutation ID | **M18** |
| Governing rule | **R22** |
| Target file | `src/disclosure_drift/m3/offline_parse.py` |
| Semantic locus | module scope (line 189) |
| Expected killing test selection | `tests/unit/test_m3_offline_parse.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
        "sec_full_index_company",
    }
)

#: Category **C**
```

is replaced by

```python
    }
)

#: Category **C**
```

### M19 — full-index co-registrants never reach the candidate rows

| Field | Value |
|---|---|
| Mutation ID | **M19** |
| Governing rule | **R23 5.2** |
| Target file | `src/disclosure_drift/m3/candidate_snapshot.py` |
| Semantic locus | function `_read_full_index_registrants` (line 333) |
| Expected killing test selection | `tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
"WHERE o.field_name = 'cik_padded' AND s.source_id = 'sec_full_index_company' "
```

is replaced by

```python
"WHERE o.field_name = 'cik_padded' AND s.source_id = 'never_matches' "
```

### M20 — a submitter-only row makes multi_registrant true

| Field | Value |
|---|---|
| Mutation ID | **M20** |
| Governing rule | **R23 5.3** |
| Target file | `src/disclosure_drift/m3/candidate_snapshot.py` |
| Semantic locus | function `_derive_accession` (line 1027) |
| Expected killing test selection | `tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    multi_registrant = int(len(contributing) > 1)
```

is replaced by

```python
    multi_registrant = int(len(registrants) > 1)
```

### M21 — an index-only accession is manufactured rather than reported

| Field | Value |
|---|---|
| Mutation ID | **M21** |
| Governing rule | **R23 5.1** |
| Target file | `src/disclosure_drift/m3/offline_parse.py` |
| Semantic locus | function `_materialize_full_index_registrants` (line 619) |
| Expected killing test selection | `tests/unit/test_m3_offline_parse.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
            if plain not in known:
                unbound.add(plain)
                continue
```

is replaced by

```python
            if plain not in known:
                pass
```

### M22 — noncontributing registrants count toward the hard quota

| Field | Value |
|---|---|
| Mutation ID | **M22** |
| Governing rule | **R24** |
| Target file | `src/disclosure_drift/m3/candidate_snapshot.py` |
| Semantic locus | function `_derive_accession` (line 1026) |
| Expected killing test selection | `tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    contributing = [item for item in registrants if item["role"] in _CONTRIBUTING_REGISTRANT_ROLES]
```

is replaced by

```python
    contributing = list(registrants)
```

### M23 — write containment permits a table outside the fifteen-table footprint

| Field | Value |
|---|---|
| Mutation ID | **M23** |
| Governing rule | **R17** |
| Target file | `src/disclosure_drift/m3/offline_parse.py` |
| Semantic locus | function `authorizer` (line 418) |
| Expected killing test selection | `tests/unit/test_m3_offline_parse.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
        return sqlite3.SQLITE_DENY
```

is replaced by

```python
        return sqlite3.SQLITE_OK
```

### M24 — a category-C source is parsed and its parser_state mutated

| Field | Value |
|---|---|
| Mutation ID | **M24** |
| Governing rule | **R18** |
| Target file | `src/disclosure_drift/m3/offline_parse.py` |
| Semantic locus | function `classify_planned_source` (line 351) |
| Expected killing test selection | `tests/unit/test_m3_offline_parse.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    if source.source_id in VALIDATION_OR_PROVENANCE_ONLY_SOURCE_IDS:
        return "E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY"
```

is replaced by

```python
    if False:
        return "E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY"
```

### M25 — an unavailable source becomes a fabricated empty parse

| Field | Value |
|---|---|
| Mutation ID | **M25** |
| Governing rule | **R14** |
| Target file | `src/disclosure_drift/m3/offline_parse.py` |
| Semantic locus | function `classify_planned_source` (line 383) |
| Expected killing test selection | `tests/unit/test_m3_offline_parse.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **SURVIVED**, then closed |
| Correction made | Closed by a **narrow added test**, never by weakening the mutation: `test_an_unusable_bound_observation_stays_category_b` |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    if not observation.is_usable or not observation.has_payload:
        return "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"
```

is replaced by

```python
    if False:
        return "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"
```

### M26 — the bridge allows any difference

| Field | Value |
|---|---|
| Mutation ID | **M26** |
| Governing rule | **R28** |
| Target file | `src/disclosure_drift/m3/rehearsal_snapshot.py` |
| Semantic locus | function `compare_tracks` (line 429) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **SURVIVED**, then closed |
| Correction made | Closed by a **narrow added test**, never by weakening the mutation: `test_the_bridge_records_a_violation_rather_than_permitting_everything` |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
                    allowed = (
                        table == "pilot_candidate_accessions"
                        and column in BRIDGE_ALLOWED_ACCESSION_COLUMNS
                    )
```

is replaced by

```python
                    allowed = True
```

### M27 — the bridge allowlist is widened beyond amendment purpose

| Field | Value |
|---|---|
| Mutation ID | **M27** |
| Governing rule | **R28** |
| Target file | `src/disclosure_drift/m3/rehearsal_snapshot.py` |
| Semantic locus | module scope (line 94) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
BRIDGE_ALLOWED_ACCESSION_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "amendment_purpose_category",
```

is replaced by

```python
BRIDGE_ALLOWED_ACCESSION_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "has_inline_xbrl",
        "multi_registrant",
        "size_stratum",
        "amendment_purpose_category",
```

### M28 — the overlay reaches a non-amendment accession

| Field | Value |
|---|---|
| Mutation ID | **M28** |
| Governing rule | **R27** |
| Target file | `src/disclosure_drift/m3/rehearsal_snapshot.py` |
| Semantic locus | function `apply_synthetic_amendment_purpose` (line 225) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
        if not columns.get("is_amendment") or columns.get("amendment_purpose_category") is not None:
```

is replaced by

```python
        if columns.get("amendment_purpose_category") is not None:
```

### M29 — the overlay stipulates a category outside the frozen three

| Field | Value |
|---|---|
| Mutation ID | **M29** |
| Governing rule | **R27** |
| Target file | `src/disclosure_drift/m3/rehearsal_snapshot.py` |
| Semantic locus | function `apply_synthetic_amendment_purpose` (line 212) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    unknown = sorted(set(categories) - set(AMENDMENT_PURPOSE_CATEGORIES))
    if unknown or not categories:
```

is replaced by

```python
    unknown = []
    if unknown or not categories:
```

### M30 — a building snapshot at entry no longer blocks

| Field | Value |
|---|---|
| Mutation ID | **M30** |
| Governing rule | **R5** |
| Target file | `src/disclosure_drift/m3/candidate_snapshot.py` |
| Semantic locus | function `_refuse_existing` (line 1548) |
| Expected killing test selection | `tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    if building:
        message = (
```

is replaced by

```python
    if False:
        message = (
```

### M31 — a rebuild in the same catalog silently succeeds

| Field | Value |
|---|---|
| Mutation ID | **M31** |
| Governing rule | **OQ-3** |
| Target file | `src/disclosure_drift/m3/candidate_snapshot.py` |
| Semantic locus | function `_refuse_existing` (line 1559) |
| Expected killing test selection | `tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    if existing is not None:
        message = (
            f"candidate snapshot {snapshot_id} already exists in this catalog.
```

is replaced by

```python
    if False:
        message = (
            f"candidate snapshot {snapshot_id} already exists in this catalog.
```

### M32 — replay uses a handle that is not strictly read-only

| Field | Value |
|---|---|
| Mutation ID | **M32** |
| Governing rule | **R3** |
| Target file | `src/disclosure_drift/m3/offline_execution.py` |
| Semantic locus | function `replay_selection_write_free` (line 329) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **SURVIVED**, then closed |
| Correction made | Closed by a **narrow added test**, never by weakening the mutation: `test_the_replay_proof_observes_the_handle_rather_than_asserting_it` — **plus a production improvement**: the replay proof now probes the handle before applying `query_only`, so a convention-only reader is distinguishable from an OS-level read-only one |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
        with strictly_read_only_connection(database) as connection:
```

is replaced by

```python
        with __import__("disclosure_drift.storage.sqlite", fromlist=["connect"]).connect(
            database, writer=False
        ) as connection:
```

### M33 — E5 again requires every selected target to hold a reserve package

| Field | Value |
|---|---|
| Mutation ID | **M33** |
| Governing rule | **R31** |
| Target file | `src/disclosure_drift/m3/execution_rehearsal.py` |
| Semantic locus | function `_run_e5` (line 758) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
                shape["targets"] == shape["packages"] + shape["dispositions"],
```

is replaced by

```python
                shape["targets"] == shape["packages"],
```

### M34 — a no-compatible-reserve disposition makes a feasible selection infeasible

| Field | Value |
|---|---|
| Mutation ID | **M34** |
| Governing rule | **R31** |
| Target file | `src/disclosure_drift/m3/execution_rehearsal.py` |
| Semantic locus | function `_run_e5` (line 755) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
            probe.require(outcome.feasible, f"{label}: the run must be feasible")
```

is replaced by

```python
            probe.require(not outcome.feasible, f"{label}: the run must be feasible")
```

### M35 — a replacement's whole bundle is trimmed to manufacture compatibility

| Field | Value |
|---|---|
| Mutation ID | **M35** |
| Governing rule | **R31** |
| Target file | `src/disclosure_drift/sec/reserve_selector.py` |
| Semantic locus | function `_candidate_profiles` (line 743) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **SURVIVED**, then closed |
| Correction made | Closed by a **narrow added test**, never by weakening the mutation: `test_a_superset_replacement_bundle_is_rejected` |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
        bundle = _bundle_for(entity, accession_pool, selection_seed)
        if not _bundle_satisfies_floors(entity, bundle):
```

is replaced by

```python
        bundle = _bundle_for(entity, accession_pool, selection_seed)[:1]
        if not _bundle_satisfies_floors(entity, bundle):
```

### M36 — the boundary derivation depends on a single label rather than both

| Field | Value |
|---|---|
| Mutation ID | **M36** |
| Governing rule | **R33** |
| Target file | `src/disclosure_drift/m3/candidate_snapshot.py` |
| Semantic locus | function `_cohort_boundary` (line 937) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    official_label = cohort_label_for_value(official_filing_date)
    audit_label = cohort_label_for_value(acceptance_audit_date)
```

is replaced by

```python
    official_label = cohort_label_for_value(official_filing_date)
    audit_label = official_label
```

### M37 — a missing or malformed acceptance date silently becomes no crossing

| Field | Value |
|---|---|
| Mutation ID | **M37** |
| Governing rule | **R33** |
| Target file | `src/disclosure_drift/m3/candidate_snapshot.py` |
| Semantic locus | function `_cohort_boundary` (line 940) |
| Expected killing test selection | `tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **KILLED** |
| Correction made | none required |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    if unknown:
        return official_label, audit_label, 1, True
```

is replaced by

```python
    if unknown:
        return official_label, audit_label, 0, False
```

### M38 — an unresolved linkage is promoted to a resolved parentage claim

| Field | Value |
|---|---|
| Mutation ID | **M38** |
| Governing rule | **R32** |
| Target file | `src/disclosure_drift/m3/candidate_snapshot.py` |
| Semantic locus | function `_amendment_linkage` (line 903) |
| Expected killing test selection | `tests/unit/test_m3_candidate_snapshot.py tests/unit/test_m3_3_execution.py` |
| Original run (target `6f87abc`) | **SURVIVED**, then closed |
| Correction made | Closed by a **narrow added test**, never by weakening the mutation: `test_a_self_referential_amendment_parent_stays_unresolved` and `test_a_parent_absent_from_the_snapshot_stays_unresolved` |
| Reverification run (target `06bb47a`) | **KILLED** |
| Final status | **KILLED / no survivor** |

Exact mutation applied — the first occurrence of

```python
    if parent.plain == accession_plain or parent.plain not in originals:
        return "unresolved_amendment", None
```

is replaced by

```python
    if parent.plain == accession_plain:
        return "amends_original", parent.plain
```

## 6. FINAL_RESULT

```text
38 KILLED
0 SURVIVORS
0 SKIPPED (no anchor was missing)
0 RESIDUAL MUTATION
POSITIVE CONTROL: PASSING (11 of 11 distinct selections)
```

The seven mutations that initially survived on the original target `6f87abc` — **M9**, **M11**,
**M25**, **M26**, **M32**, **M35**, and **M38** — were each closed by a **narrow added test**, never
by weakening the mutation, relaxing an assertion, or removing a case. **M32** additionally produced
a **production** improvement: the replay proof now probes the handle before applying `query_only`,
so a convention-only reader is distinguishable from an OS-level read-only one.

## 7. What this record does not do

It **accepts nothing** and **authorizes nothing**. `M3.3-E0`, `M3.3-E1`, `M3.3-E2`, and `M3.4` each
remain a separate, unissued owner gate. Network, SEC, reacquisition, and private-evidence authority
remain **NONE**; `EV_ROOT` remains prohibited; migration remains `none`; the request ceiling remains
**0**; and `m3.2-complete` is unmoved. **Both real-path feasibility gates remain OPEN and are never
merged:**

```text
M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN
M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN
```
