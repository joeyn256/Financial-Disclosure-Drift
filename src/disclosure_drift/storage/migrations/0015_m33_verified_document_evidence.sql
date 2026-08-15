-- Disclosure Drift operational catalog, migration 0015 (M3.3 verified-evidence schema).
-- Governing records: Decision 080 section 9.3; Decision 081 R47, R48; Decision 082
-- section 11 (the schema contract) and section 12 (the protocol the schema will later
-- serve); Decision 083 R63 (the four owner dispositions); Decision 087 section 4 (the
-- implementation authorization) and sections 5-9 (the semantics enforced below).
--
-- Purpose: nothing in the catalog can hold document-level evidence. Migration 0009
-- excludes 'verified' from every candidate evidence-level CHECK by design, and there is
-- no relation anywhere for a document artifact, an independent review pass, a supporting
-- source span, or an adjudicated result. This migration creates exactly that layer, and
-- widens exactly the one constraint pair that a verified amendment purpose needs.
--
-- WHAT THIS MIGRATION DOES NOT DO. It performs no document review, classifies no filing,
-- inserts no real Decision-081 evidence, and reads nothing from the private external
-- evidence root. The four relations below are created EMPTY. Their writer is a future
-- authorized stage running the Decision 083 R64 protocol m3.3-document-evidence/1.0,
-- which is accepted but EXECUTION DEFERRED (Decision 087 section 10).
--
-- This migration is PROSPECTIVE and PRE-E0, exactly as 0014 is. Section 1's preconditions
-- are what enforce that mechanically: it is never applied to a catalog carrying real
-- candidate, selection, reserve, or manifest state, because section 8's rebuild of
-- pilot_candidate_accessions would then be a DATA migration rather than a prospective
-- schema correction -- a materially different act requiring its own authorization.
--
-- Migration 0014 is NOT rewritten, NOT squashed, and NOT re-applied. It stays at chain
-- position 0014 with its own bytes and its own checksum; this migration is a separate
-- record that an independent reviewer can accept or reject on its own (Decision 082
-- section 11.4). The section 11.4 ordering constraint -- 0014 precedes 0015 -- is a real
-- chain position here, not a comment.
--
-- Rollback is revert-and-rebuild from 0001-0014. Migrations are forward-only and no
-- down-migration is proposed.
--
-- PRIVATE-EVIDENCE-ROOT NONLEAKAGE (Decision 083 R63 item A; Decision 087 section 5.1).
-- The Complete Submission Text bytes stay in the private external evidence root and never
-- enter SQLite. No absolute EV_ROOT path, private filesystem path, local user path, or
-- scratch path is persisted, and none CAN be: every text column below carries a shape
-- CHECK that a filesystem path violates. There is deliberately no locator column at all --
-- artifact_sha256 is itself the content address, so the "only if technically required"
-- permission in R63 item A is simply not exercised. That is the strongest available form
-- of the rule rather than a relaxation of it.
--
-- WHY NO json1. contributing_review_ids_json is validated by length arithmetic, quote
-- counting, and substring containment rather than by json_each. The repository's declared
-- SQLite floor is 3.37 (storage/sqlite.py REQUIRED_SQLITE_VERSION), where JSON1 is an
-- optional compile-time extension. The arithmetic below is exact -- see section 6 -- and
-- it holds on every build the floor admits.
--
-- Seven sections:
--   1. Preconditions -- every table this migration rebuilds, and their children, empty
--   2. document_artifacts                                            (CREATE TABLE)
--   3. document_review_records                                       (CREATE TABLE)
--   4. document_review_spans                                         (CREATE TABLE)
--   5. document_adjudicated_evidence                                 (CREATE TABLE)
--   6. Adjudication provenance -- artifact binding, review binding, span backing
--   7. Immutability -- append-only, frozen at insert, for all four relations
--   8. The evidence-level extension -- pilot_candidate_accessions rebuild
PRAGMA legacy_alter_table = ON;

-- --------------------------------------------------------------------------
-- Section 1. Preconditions -- every affected table must be empty
--
-- Section 8 rebuilds pilot_candidate_accessions, which SQLite can only do by
-- create-copy-drop-rename. Five relations carry a composite foreign key into it --
-- pilot_candidate_accession_registrants, pilot_candidate_accession_evidence,
-- pilot_candidate_accession_reasons, pilot_selected_accessions, and
-- pilot_reserve_accessions -- so the drop is safe only when the whole family is empty.
--
-- The list below is migration 0014's own precondition set plus those three additional
-- children. A non-empty table means a real identity exists; RAISE(ABORT) inside the
-- migration transaction rolls the whole script back, so a catalog that fails this gate is
-- left byte-identical at 0014. Decision 087 section 15 item I makes any requirement to
-- reinterpret accepted real evidence a STOP rather than a migration path.
-- --------------------------------------------------------------------------

CREATE TEMPORARY TABLE _m0015_precondition_guard (n INTEGER PRIMARY KEY);

CREATE TEMPORARY TRIGGER _m0015_require_empty_tables
BEFORE INSERT ON _m0015_precondition_guard
BEGIN
    SELECT RAISE(ABORT, 'migration 0015 requires empty pilot_candidate_snapshots')
    WHERE EXISTS (SELECT 1 FROM pilot_candidate_snapshots);
    SELECT RAISE(ABORT, 'migration 0015 requires empty pilot_candidate_accessions')
    WHERE EXISTS (SELECT 1 FROM pilot_candidate_accessions);
    SELECT RAISE(ABORT, 'migration 0015 requires empty pilot_candidate_accession_registrants')
    WHERE EXISTS (SELECT 1 FROM pilot_candidate_accession_registrants);
    SELECT RAISE(ABORT, 'migration 0015 requires empty pilot_candidate_accession_evidence')
    WHERE EXISTS (SELECT 1 FROM pilot_candidate_accession_evidence);
    SELECT RAISE(ABORT, 'migration 0015 requires empty pilot_candidate_accession_reasons')
    WHERE EXISTS (SELECT 1 FROM pilot_candidate_accession_reasons);
    SELECT RAISE(ABORT, 'migration 0015 requires empty pilot_selection_runs')
    WHERE EXISTS (SELECT 1 FROM pilot_selection_runs);
    SELECT RAISE(ABORT, 'migration 0015 requires empty pilot_selected_accessions')
    WHERE EXISTS (SELECT 1 FROM pilot_selected_accessions);
    SELECT RAISE(ABORT, 'migration 0015 requires empty pilot_reserve_accessions')
    WHERE EXISTS (SELECT 1 FROM pilot_reserve_accessions);
    SELECT RAISE(ABORT, 'migration 0015 requires empty pilot_manifest_versions')
    WHERE EXISTS (SELECT 1 FROM pilot_manifest_versions);
END;

INSERT INTO _m0015_precondition_guard (n) VALUES (1);

DROP TRIGGER _m0015_require_empty_tables;
DROP TABLE _m0015_precondition_guard;

-- --------------------------------------------------------------------------
-- Section 2. document_artifacts -- Decision 082 section 11.2, relation 1
--
-- A governed CATALOG-METADATA relation (Decision 083 R63 item A). It identifies and binds
-- one document artifact; it does not store it. Every column is the contract's, and every
-- one carries a shape CHECK strict enough that a filesystem path cannot be written into
-- it -- which is what makes the nonleakage rule enforced rather than documented.
--
-- No foreign key to census_accessions. The Decision-081 artifacts are real accessions that
-- have no census row and will not have one until M3.3-E0 runs, which is not authorized. A
-- foreign key here would make the relation unusable for exactly the evidence it exists to
-- hold, so accession identity is constrained by shape instead.
--
-- UNIQUE (accession_plain, source_class) is the artifact-substitution guard: one accession
-- has at most one artifact per source class, so a competing artifact cannot be registered
-- alongside the bound one and silently picked up downstream.
--
-- source_class admits exactly one value today. Decision 080 R45 and Decision 082 R56 make
-- the native Complete Submission Text the accepted source; a second source class needs its
-- own owner record, and a single-value CHECK is the fail-closed way to say so.
-- --------------------------------------------------------------------------

CREATE TABLE document_artifacts (
    artifact_sha256         TEXT PRIMARY KEY
        CHECK (length(artifact_sha256) = 64 AND artifact_sha256 NOT GLOB '*[^0-9a-f]*'),
    accession_plain         TEXT NOT NULL
        CHECK (length(accession_plain) = 18 AND accession_plain NOT GLOB '*[^0-9]*'),
    source_class            TEXT NOT NULL
        CHECK (source_class IN ('complete_submission_text')),
    byte_length             INTEGER NOT NULL CHECK (byte_length > 0),
    retrieved_at_utc        TEXT NOT NULL
        CHECK (retrieved_at_utc GLOB
               '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]*Z'),
    -- The PUBLIC source identity, and the only URL-shaped column in the schema. The prefix
    -- is pinned to the public EDGAR archive host: no file: URL, no relative path, and no
    -- absolute local path can satisfy it.
    source_url              TEXT NOT NULL
        CHECK (source_url GLOB 'https://www.sec.gov/Archives/*'
               AND source_url NOT GLOB '* *'
               AND source_url NOT GLOB '*\*'),
    -- An opaque retrieval-receipt identity. The charset admits no '/', no '\', no ':', and
    -- no space, so a path can never be recorded here under the guise of provenance.
    retrieval_receipt_id    TEXT NOT NULL
        CHECK (length(retrieval_receipt_id) BETWEEN 1 AND 128
               AND retrieval_receipt_id NOT GLOB '*[^0-9a-zA-Z._-]*'),
    UNIQUE (accession_plain, source_class)
) STRICT;

CREATE INDEX idx_document_artifacts_accession
    ON document_artifacts (accession_plain);

-- --------------------------------------------------------------------------
-- Section 3. document_review_records -- Decision 082 section 11.2, relation 2
--
-- One independent review pass's record for one artifact. Decision 083 R63 item D replaces
-- the contract's single reviewer_identifier with a durable OPAQUE review-epoch identifier
-- plus reviewer role and model, and requires the package to distinguish Review A, Review B,
-- and adjudication MECHANICALLY. Both halves of that are enforced here:
--
--   * UNIQUE (accession_plain, reviewer_role) -- one record per pass per accession;
--   * document_review_records_epoch_carries_one_role -- a review epoch carries exactly one
--     role, globally.
--
-- Read together they are the proof R63 item D asks for: within an accession the three roles
-- are distinct rows, and no epoch can wear two roles, so the A, B, and adjudication records
-- of any accession necessarily carry three different review_epoch_id values. One epoch
-- reviewing all 108 artifacts is still lawful and correct -- that is the same role, many
-- accessions -- which is why the rule is stated per role rather than per row.
--
-- NO PERSONAL NAME. reviewer_model's charset admits no space, so a human name cannot be
-- written into it, and no column exists for one. A raw Claude session ID is not required
-- and has no column either: review_epoch_id is opaque by construction.
--
-- protocol_version is pinned to the Decision 083 R64 frozen string. R64's conflict
-- terminality already says a new protocol version needs a new owner authorization; pinning
-- the value makes that structural instead of advisory. Storing the version is not executing
-- the protocol (Decision 087 section 5.2).
--
-- purpose_category reuses migration 0009's frozen three-category vocabulary verbatim. The
-- abstention vocabulary is Decision 082 section 12.2's four allowed abstentions, and an
-- abstention is a RECORDED OUTCOME, never a skipped row (Decision 080 AP-1 totality).
--
-- original_form_asserted admits only 10-K and 10-KT: Decision 082 section 12.4 rule X-2,
-- which is Decision 081 R44. X-3's prohibition on substituting a fiscal-period end date for
-- a stated filing date is a protocol rule about WHICH text may be read, not a shape the
-- schema can see; the date shape is checked here and the rule stays with the protocol.
-- --------------------------------------------------------------------------

CREATE TABLE document_review_records (
    review_id               TEXT PRIMARY KEY
        CHECK (length(review_id) = 64 AND review_id NOT GLOB '*[^0-9a-f]*'),
    -- Durable and opaque (R63 item D). Never a personal name, never a raw session ID.
    review_epoch_id         TEXT NOT NULL
        CHECK (length(review_epoch_id) = 64 AND review_epoch_id NOT GLOB '*[^0-9a-f]*'),
    reviewer_role           TEXT NOT NULL
        CHECK (reviewer_role IN ('review_a', 'review_b', 'adjudication')),
    -- A model identifier such as 'claude-opus-5'. The charset excludes spaces, so this
    -- column cannot become a place to record a person.
    reviewer_model          TEXT NOT NULL
        CHECK (length(reviewer_model) BETWEEN 1 AND 64
               AND reviewer_model NOT GLOB '*[^0-9a-zA-Z._-]*'),
    -- The contract's own column, kept verbatim, and tied to reviewer_role below so the two
    -- can never disagree about which pass a record belongs to.
    review_pass             TEXT NOT NULL CHECK (review_pass IN ('A', 'B', 'ADJUDICATION')),
    artifact_sha256         TEXT NOT NULL REFERENCES document_artifacts(artifact_sha256),
    accession_plain         TEXT NOT NULL
        CHECK (length(accession_plain) = 18 AND accession_plain NOT GLOB '*[^0-9]*'),
    protocol_version        TEXT NOT NULL
        CHECK (protocol_version = 'm3.3-document-evidence/1.0'),
    decided_at_utc          TEXT NOT NULL
        CHECK (decided_at_utc GLOB
               '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]*Z'),
    purpose_category        TEXT
        CHECK (purpose_category IS NULL OR purpose_category IN (
            'administrative_or_exhibit', 'financial_or_xbrl_correction', 'narrative_or_governance')),
    abstained               INTEGER NOT NULL CHECK (abstained IN (0, 1)),
    abstention_reason       TEXT
        CHECK (abstention_reason IS NULL OR abstention_reason IN (
            'insufficient_text', 'ambiguous_text', 'not_issuer_authored', 'artifact_unreadable')),
    original_form_asserted  TEXT
        CHECK (original_form_asserted IS NULL OR original_form_asserted IN ('10-K', '10-KT')),
    original_filing_date_asserted TEXT
        CHECK (original_filing_date_asserted IS NULL
               OR original_filing_date_asserted GLOB
                  '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    original_accession_asserted TEXT
        CHECK (original_accession_asserted IS NULL
               OR (length(original_accession_asserted) = 18
                   AND original_accession_asserted NOT GLOB '*[^0-9]*')),
    review_record_sha256    TEXT NOT NULL
        CHECK (length(review_record_sha256) = 64
               AND review_record_sha256 NOT GLOB '*[^0-9a-f]*'),
    -- One record per pass per accession. This is also the artifact-substitution guard on
    -- this side: a second artifact cannot be reviewed into the same accession and role.
    UNIQUE (accession_plain, reviewer_role),
    CHECK ((reviewer_role = 'review_a') = (review_pass = 'A')),
    CHECK ((reviewer_role = 'review_b') = (review_pass = 'B')),
    CHECK ((reviewer_role = 'adjudication') = (review_pass = 'ADJUDICATION')),
    -- An abstention carries its reason, and asserts nothing (Decision 082 section 12.2).
    CHECK ((abstained = 1) = (abstention_reason IS NOT NULL)),
    CHECK (abstained = 0
           OR (purpose_category IS NULL
               AND original_form_asserted IS NULL
               AND original_filing_date_asserted IS NULL
               AND original_accession_asserted IS NULL))
) STRICT;

CREATE INDEX idx_document_review_records_accession
    ON document_review_records (accession_plain, artifact_sha256);
CREATE INDEX idx_document_review_records_epoch
    ON document_review_records (review_epoch_id);

-- Decision 083 R63 item D, enforced: a governed review epoch carries exactly one reviewer
-- role. Two passes that share an epoch identifier are not two independent passes, and this
-- is the schema refusing to record them as though they were.
CREATE TRIGGER document_review_records_epoch_carries_one_role
BEFORE INSERT ON document_review_records
BEGIN
    SELECT RAISE(ABORT,
        'a governed review epoch carries exactly one reviewer role; Review A, Review B, and adjudication must use distinct epochs')
    WHERE EXISTS (
        SELECT 1 FROM document_review_records
        WHERE review_epoch_id = NEW.review_epoch_id
          AND reviewer_role <> NEW.reviewer_role
    );
END;

-- --------------------------------------------------------------------------
-- Section 4. document_review_spans -- Decision 082 section 11.2, relation 3
--
-- Exact source-span provenance. Decision 082 section 12.5 requires verbatim text, a STABLE
-- LOCATION inside the frozen artifact, and a span hash, so that a future evidence judgment
-- is traceable to artifact, review record, span, and evidence question WITHOUT fuzzy text
-- search at acceptance time (Decision 087 section 5.3).
--
-- span_location is a byte range in the frozen artifact, written 'bytes:START-END'. A byte
-- range is the only location that is stable under an immutable artifact and mechanically
-- checkable, and its shape admits no filesystem path.
--
-- span_role names the evidence question the span answers, and section 6 requires the
-- adjudicated row's evidence_kind to be backed by spans of the matching role. NO CLASSIFIER
-- IS INVENTED HERE: the span records which text a reviewer cited, never which category a
-- machine inferred. Decision 071 IN-2 is not reversed and every Decision 082 section 12.3
-- prohibition stands.
-- --------------------------------------------------------------------------

CREATE TABLE document_review_spans (
    review_id           TEXT NOT NULL REFERENCES document_review_records(review_id),
    span_ordinal        INTEGER NOT NULL CHECK (span_ordinal >= 1),
    span_role           TEXT NOT NULL
        CHECK (span_role IN (
            'amendment_purpose', 'original_form', 'original_filing_date', 'original_accession')),
    span_text_verbatim  TEXT NOT NULL CHECK (length(span_text_verbatim) > 0),
    -- 'bytes:START-END' into the frozen artifact. Two CHECKs, because the first alone would
    -- admit stray characters between the digits.
    span_location       TEXT NOT NULL
        CHECK (span_location GLOB 'bytes:[0-9]*-[0-9]*'
               AND span_location NOT GLOB '*[^0-9a-z:-]*'),
    span_sha256         TEXT NOT NULL
        CHECK (length(span_sha256) = 64 AND span_sha256 NOT GLOB '*[^0-9a-f]*'),
    PRIMARY KEY (review_id, span_ordinal)
) STRICT;

CREATE INDEX idx_document_review_spans_role
    ON document_review_spans (review_id, span_role);

-- A span may cite only an assertion its own review record actually made. Without this a
-- record could carry original-form evidence while asserting no original form, which is
-- provenance pointing at nothing.
CREATE TRIGGER document_review_spans_require_matching_assertion
BEFORE INSERT ON document_review_spans
BEGIN
    SELECT RAISE(ABORT, 'a review span must support an assertion its review record makes')
    WHERE EXISTS (
        SELECT 1 FROM document_review_records AS r
        WHERE r.review_id = NEW.review_id
          AND (
            (NEW.span_role = 'amendment_purpose' AND r.purpose_category IS NULL)
            OR (NEW.span_role = 'original_form' AND r.original_form_asserted IS NULL)
            OR (NEW.span_role = 'original_filing_date'
                AND r.original_filing_date_asserted IS NULL)
            OR (NEW.span_role = 'original_accession'
                AND r.original_accession_asserted IS NULL)
          )
    );
END;

-- --------------------------------------------------------------------------
-- Section 5. document_adjudicated_evidence -- Decision 082 section 11.2, relation 4
--
-- The frozen final adjudication result for one accession and one evidence kind.
--
-- WHERE 'verified' IS AUTHORIZED (Decision 083 R63 item C; Decision 087 section 5.4). The
-- evidence_kind CHECK is the enforcement: 'amendment_purpose' and 'explicit_original' are
-- the only kinds this relation admits, so a verified size, industry, history, universe,
-- cohort, XBRL, control-predicate, or name/ticker row cannot be written at all -- it is
-- refused at the kind, before evidence_level is even considered.
--
-- LINKAGE (Decision 083 R63 item B; Decision 087 section 6). There is no
-- verified_amends_original state here or anywhere. This relation carries HOW STRONGLY and
-- BY WHAT PROCESS the assertion was verified; WHAT the relationship is stays
-- pilot_candidate_accessions.amendment_linkage_state = 'amends_original', whose vocabulary
-- migration 0015 does not touch.
--
-- adjudicated_value is canonical per kind: one of the three frozen categories for
-- amendment_purpose, and '<FORM>|<YYYY-MM-DD>' for explicit_original. That is a shape
-- constraint over values Decision 082 section 12.4 already defines as extractable, not a
-- new methodology. The original ACCESSION is deliberately absent from the adjudicated
-- value: rule X-4 measured it at 0/108 and says the protocol must not depend on it, so it
-- stays a recorded review assertion rather than an adjudicated output.
--
-- FAIL CLOSED. 'verified' requires agreement_state 'agreed' or 'resolved'; 'conflicting'
-- and 'abstained' can never be verified and carry no value (Decision 082 section 12.6:
-- never averaged, never majority-by-silence, never repaired).
--
-- frozen_at_utc is required at INSERT because section 7 makes the row immutable from that
-- moment: the row is written frozen, which is why no lifecycle transition is invented.
-- --------------------------------------------------------------------------

CREATE TABLE document_adjudicated_evidence (
    accession_plain     TEXT NOT NULL
        CHECK (length(accession_plain) = 18 AND accession_plain NOT GLOB '*[^0-9]*'),
    evidence_kind       TEXT NOT NULL
        CHECK (evidence_kind IN ('amendment_purpose', 'explicit_original')),
    artifact_sha256     TEXT NOT NULL REFERENCES document_artifacts(artifact_sha256),
    adjudicated_value   TEXT,
    agreement_state     TEXT NOT NULL
        CHECK (agreement_state IN ('agreed', 'resolved', 'conflicting', 'abstained')),
    -- The canonical JSON array shape, checked with substr rather than GLOB: '[' opens a
    -- character class in GLOB, so a literal-bracket pattern silently means something else.
    -- The negated class below does use GLOB, and puts ']' FIRST inside it -- anywhere else
    -- it would close the class early and the constraint would reject its own valid values.
    contributing_review_ids_json TEXT NOT NULL
        CHECK (substr(contributing_review_ids_json, 1, 2) = '["'
               AND substr(contributing_review_ids_json, -2) = '"]'
               AND contributing_review_ids_json NOT GLOB '*[^]0-9a-f",[]*'),
    evidence_level      TEXT NOT NULL
        CHECK (evidence_level IN ('verified', 'conflicting', 'unavailable')),
    adjudication_sha256 TEXT NOT NULL
        CHECK (length(adjudication_sha256) = 64
               AND adjudication_sha256 NOT GLOB '*[^0-9a-f]*'),
    frozen_at_utc       TEXT NOT NULL
        CHECK (frozen_at_utc GLOB
               '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]*Z'),
    PRIMARY KEY (accession_plain, evidence_kind),
    -- A value exists exactly when the passes reached one.
    CHECK ((agreement_state IN ('agreed', 'resolved')) = (adjudicated_value IS NOT NULL)),
    -- 'verified' is available only to an agreed or resolved outcome.
    CHECK (evidence_level <> 'verified' OR agreement_state IN ('agreed', 'resolved')),
    -- The canonical per-kind value shapes.
    CHECK (evidence_kind <> 'amendment_purpose'
           OR adjudicated_value IS NULL
           OR adjudicated_value IN (
               'administrative_or_exhibit', 'financial_or_xbrl_correction',
               'narrative_or_governance')),
    CHECK (evidence_kind <> 'explicit_original'
           OR adjudicated_value IS NULL
           OR adjudicated_value GLOB
              '10-K|[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
           OR adjudicated_value GLOB
              '10-KT|[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
) STRICT;

CREATE INDEX idx_document_adjudicated_evidence_artifact
    ON document_adjudicated_evidence (artifact_sha256);

-- --------------------------------------------------------------------------
-- Section 6. Adjudication provenance
--
-- An adjudicated row is a claim about evidence. These four triggers make the claim
-- unwritable unless the evidence is actually there, which is the difference between
-- provenance and a provenance-shaped column.
-- --------------------------------------------------------------------------

-- Artifact binding: every review this accession has must name the SAME artifact the
-- adjudication names. A cross-artifact adjudication is not an adjudication of anything.
CREATE TRIGGER document_adjudicated_evidence_requires_bound_artifact
BEFORE INSERT ON document_adjudicated_evidence
BEGIN
    SELECT RAISE(ABORT,
        'adjudicated evidence must bind the same artifact every review of that accession bound')
    WHERE EXISTS (
        SELECT 1 FROM document_review_records AS r
        WHERE r.accession_plain = NEW.accession_plain
          AND r.artifact_sha256 <> NEW.artifact_sha256
    );
END;

-- Review binding: both independent passes must exist, and a 'resolved' outcome must
-- additionally have the third adjudication record it claims to rest on (Decision 082
-- section 12.6).
CREATE TRIGGER document_adjudicated_evidence_requires_review_provenance
BEFORE INSERT ON document_adjudicated_evidence
BEGIN
    SELECT RAISE(ABORT, 'adjudicated evidence requires both independent review passes')
    WHERE NOT EXISTS (
        SELECT 1 FROM document_review_records
        WHERE accession_plain = NEW.accession_plain
          AND artifact_sha256 = NEW.artifact_sha256
          AND reviewer_role = 'review_a'
    ) OR NOT EXISTS (
        SELECT 1 FROM document_review_records
        WHERE accession_plain = NEW.accession_plain
          AND artifact_sha256 = NEW.artifact_sha256
          AND reviewer_role = 'review_b'
    );
    SELECT RAISE(ABORT, 'a resolved outcome requires the third adjudication record')
    WHERE NEW.agreement_state = 'resolved'
      AND NOT EXISTS (
        SELECT 1 FROM document_review_records
        WHERE accession_plain = NEW.accession_plain
          AND artifact_sha256 = NEW.artifact_sha256
          AND reviewer_role = 'adjudication'
    );
END;

-- The contributing set is exact, not decorative. For n review records on this
-- accession/artifact the canonical array is '["<64 hex>","<64 hex>",...]', whose length is
-- 67n + 1 and whose quote count is 2n. Those two arithmetic facts plus substring
-- containment of every one of the n distinct ids leave no room for an extra, a missing, or
-- a substituted element -- and none of it needs json1.
CREATE TRIGGER document_adjudicated_evidence_review_ids_are_exact
BEFORE INSERT ON document_adjudicated_evidence
BEGIN
    SELECT RAISE(ABORT,
        'contributing_review_ids_json must enumerate exactly the reviews of this accession and artifact')
    WHERE length(NEW.contributing_review_ids_json) <> 1 + 67 * (
        SELECT COUNT(*) FROM document_review_records
        WHERE accession_plain = NEW.accession_plain
          AND artifact_sha256 = NEW.artifact_sha256
    )
    OR (length(NEW.contributing_review_ids_json)
        - length(replace(NEW.contributing_review_ids_json, '"', ''))) <> 2 * (
        SELECT COUNT(*) FROM document_review_records
        WHERE accession_plain = NEW.accession_plain
          AND artifact_sha256 = NEW.artifact_sha256
    )
    OR EXISTS (
        SELECT 1 FROM document_review_records AS r
        WHERE r.accession_plain = NEW.accession_plain
          AND r.artifact_sha256 = NEW.artifact_sha256
          AND instr(NEW.contributing_review_ids_json, r.review_id) = 0
    );
END;

-- Span backing for a verified outcome. Decision 082 section 12.5: every non-abstaining
-- record carries at least one span, and a record whose evidence cannot be located fails
-- closed. Enforced at the point the evidence is CONSUMED, because the lawful write order is
-- review record, then its spans, then the adjudication -- the foreign keys require exactly
-- that order, and this guard refuses to skip the middle of it.
CREATE TRIGGER document_adjudicated_evidence_verified_requires_spans
BEFORE INSERT ON document_adjudicated_evidence
WHEN NEW.evidence_level = 'verified'
BEGIN
    SELECT RAISE(ABORT,
        'verified evidence requires at least one matching source span from every non-abstaining review')
    WHERE EXISTS (
        SELECT 1 FROM document_review_records AS r
        WHERE r.accession_plain = NEW.accession_plain
          AND r.artifact_sha256 = NEW.artifact_sha256
          AND r.abstained = 0
          AND NOT EXISTS (
              SELECT 1 FROM document_review_spans AS s
              WHERE s.review_id = r.review_id
                AND ((NEW.evidence_kind = 'amendment_purpose'
                      AND s.span_role = 'amendment_purpose')
                     OR (NEW.evidence_kind = 'explicit_original'
                         AND s.span_role IN ('original_form', 'original_filing_date',
                                             'original_accession')))
          )
    );
END;

-- --------------------------------------------------------------------------
-- Section 7. Immutability -- append-only, and frozen at insert
--
-- Decision 082 section 11.2: "Four new relations, each append-only and immutable once
-- frozen." Every row here is written already frozen -- an artifact's SHA is its identity, a
-- review record is a completed pass, a span is a citation into an immutable artifact, and
-- an adjudicated row carries frozen_at_utc from birth -- so "immutable once frozen" and
-- "immutable" are the same rule, and no lifecycle transition needs inventing to express it.
-- Decision 087 section 8 forbids inventing delete or update flexibility for convenience,
-- and this is the shape of that prohibition: UPDATE and DELETE are refused outright on all
-- four relations.
--
-- That single rule discharges four of the five Decision 087 section 8 protections at once:
-- a frozen review cannot be mutated in place, span provenance cannot be rewritten, an
-- artifact SHA cannot change after review, and reviewer role and epoch cannot change after
-- freeze. The fifth -- an adjudicated result changing after final freeze -- is the same
-- refusal on the fourth table.
-- --------------------------------------------------------------------------

CREATE TRIGGER document_artifacts_are_immutable_update
BEFORE UPDATE ON document_artifacts
BEGIN SELECT RAISE(ABORT, 'document_artifacts is append-only and immutable'); END;
CREATE TRIGGER document_artifacts_are_immutable_delete
BEFORE DELETE ON document_artifacts
BEGIN SELECT RAISE(ABORT, 'document_artifacts is append-only and immutable'); END;

CREATE TRIGGER document_review_records_are_immutable_update
BEFORE UPDATE ON document_review_records
BEGIN SELECT RAISE(ABORT, 'document_review_records is append-only and immutable'); END;
CREATE TRIGGER document_review_records_are_immutable_delete
BEFORE DELETE ON document_review_records
BEGIN SELECT RAISE(ABORT, 'document_review_records is append-only and immutable'); END;

CREATE TRIGGER document_review_spans_are_immutable_update
BEFORE UPDATE ON document_review_spans
BEGIN SELECT RAISE(ABORT, 'document_review_spans is append-only and immutable'); END;
CREATE TRIGGER document_review_spans_are_immutable_delete
BEFORE DELETE ON document_review_spans
BEGIN SELECT RAISE(ABORT, 'document_review_spans is append-only and immutable'); END;

CREATE TRIGGER document_adjudicated_evidence_are_immutable_update
BEFORE UPDATE ON document_adjudicated_evidence
BEGIN SELECT RAISE(ABORT, 'document_adjudicated_evidence is append-only and immutable'); END;
CREATE TRIGGER document_adjudicated_evidence_are_immutable_delete
BEFORE DELETE ON document_adjudicated_evidence
BEGIN SELECT RAISE(ABORT, 'document_adjudicated_evidence is append-only and immutable'); END;

-- Appending a span to a review whose evidence has already been adjudicated would change
-- that review's evidentiary basis after the fact. Rewriting is impossible above; this
-- closes the append-after-consumption door beside it.
CREATE TRIGGER document_review_spans_never_appended_after_adjudication
BEFORE INSERT ON document_review_spans
BEGIN
    SELECT RAISE(ABORT, 'a review consumed by adjudicated evidence can receive no further spans')
    WHERE EXISTS (
        SELECT 1 FROM document_review_records AS r
        JOIN document_adjudicated_evidence AS a
          ON a.accession_plain = r.accession_plain
         AND a.artifact_sha256 = r.artifact_sha256
        WHERE r.review_id = NEW.review_id
    );
END;

-- A review record cannot join an accession whose evidence is already frozen, for the same
-- reason: the adjudication's contributing set is exact (section 6), and a late arrival
-- would silently falsify it.
CREATE TRIGGER document_review_records_never_added_after_adjudication
BEFORE INSERT ON document_review_records
BEGIN
    SELECT RAISE(ABORT, 'an accession with frozen adjudicated evidence can receive no further reviews')
    WHERE EXISTS (
        SELECT 1 FROM document_adjudicated_evidence
        WHERE accession_plain = NEW.accession_plain
    );
END;

-- --------------------------------------------------------------------------
-- Section 8. The evidence-level extension -- pilot_candidate_accessions
--
-- Decision 080 section 9.3 and Decision 082 section 11.2 name exactly two constraints that
-- must widen before a verified value can be persisted or can satisfy a quota:
--
--   1. amendment_purpose_evidence_level's CHECK, which excludes 'verified' by design;
--   2. the amendment_purpose_quota_eligible CHECK, which requires 'provisional'.
--
-- Both are widened here, and NOTHING ELSE IS. Decision 083 R63 item C authorizes 'verified'
-- for amendment purpose and linkage only, so every other evidence-level CHECK in the schema
-- -- size, industry, history, primary_universe, filing_date, cohort, xbrl, the registrant
-- relations, and the census relation -- is left exactly as migration 0009 and migration
-- 0014 wrote it, still excluding 'verified'. Linkage needs no widening at all: R63 item B
-- reuses amendment_linkage_state = 'amends_original', whose vocabulary is untouched, and
-- carries strength in document_adjudicated_evidence instead.
--
-- SQLite cannot alter a CHECK, so this is the documented create-copy-drop-rename rebuild.
-- Every other column, CHECK, key, index, trigger, and comment is reproduced from migration
-- 0014 unchanged. This is a rebuild, not a redesign, and the R58/R59 anchor and
-- completeness invariants 0014 made structural are carried across verbatim.
--
-- NO DIGEST TUPLE IS WIDENED. No column is added, so ACCESSION_TABLE_COLUMNS is untouched
-- and candidate_accession_table_sha256 is byte-unchanged for every pre-existing row --
-- accepted Decision 084 R67, and Decision 087 section 9's required nonchange proof.
--
-- pilot_snapshot_freeze_requires_valid_state is NOT dropped and NOT rewritten. It lives on
-- pilot_candidate_snapshots, migration 0015 changes nothing it asserts, and with
-- legacy_alter_table the rename back to the original name leaves every reference in it
-- already correct. Migration 0014's early DROP existed because 0014 was replacing that
-- trigger; there is nothing to replace here, and copying accepted frozen trigger SQL into a
-- new record for no reason is exactly what 0014's own comment warned against.
-- --------------------------------------------------------------------------

CREATE TABLE pilot_candidate_accessions_m0015 (
    snapshot_id                     TEXT NOT NULL REFERENCES pilot_candidate_snapshots(snapshot_id),
    accession_plain                 TEXT NOT NULL,
    accession_number_dashed         TEXT NOT NULL,
    accession_tie_break_sha256      TEXT NOT NULL
        CHECK (length(accession_tie_break_sha256) = 64
               AND accession_tie_break_sha256 NOT GLOB '*[^0-9a-f]*'),
    -- Decision 083 R58: NULL whenever the accession does not have exactly one
    -- established substantive registrant.
    anchor_cik_numeric               INTEGER,
    -- Decision 083 R59: an unestablished set blocks candidacy entirely. The builder
    -- excludes such accessions before they reach a snapshot; the freeze guard refuses any
    -- that arrive anyway.
    registrant_set_completeness      TEXT NOT NULL
        CHECK (registrant_set_completeness IN ('established', 'unestablished')),
    form_type                        TEXT NOT NULL REFERENCES reference_form_types(form_type),
    is_amendment                     INTEGER NOT NULL CHECK (is_amendment IN (0, 1)),
    official_filing_date             TEXT,
    report_date                      TEXT,
    acceptance_audit_date            TEXT,
    filing_date_evidence_level       TEXT NOT NULL
        CHECK (filing_date_evidence_level IN
               ('provisional', 'review_required', 'conflicting', 'unavailable')),
    filing_date_resolution_sha256    TEXT
        CHECK (filing_date_resolution_sha256 IS NULL
               OR (length(filing_date_resolution_sha256) = 64
                   AND filing_date_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    filing_date_precedence           INTEGER
        CHECK (filing_date_precedence IS NULL OR filing_date_precedence = 2),
    provisional_official_cohort      TEXT
        CHECK (provisional_official_cohort IS NULL OR provisional_official_cohort IN (
            'development', 'transition', 'primary_test', 'prospective', 'monitoring')),
    acceptance_audit_cohort           TEXT
        CHECK (acceptance_audit_cohort IS NULL OR acceptance_audit_cohort IN (
            'development', 'transition', 'primary_test', 'prospective', 'monitoring')),
    cohort_evidence_level             TEXT NOT NULL
        CHECK (cohort_evidence_level IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
    cohort_resolution_sha256          TEXT
        CHECK (cohort_resolution_sha256 IS NULL
               OR (length(cohort_resolution_sha256) = 64
                   AND cohort_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    cohort_ambiguous                  INTEGER NOT NULL DEFAULT 0 CHECK (cohort_ambiguous IN (0, 1)),
    has_xbrl                          INTEGER NOT NULL DEFAULT 0 CHECK (has_xbrl IN (0, 1)),
    has_inline_xbrl                   INTEGER NOT NULL DEFAULT 0 CHECK (has_inline_xbrl IN (0, 1)),
    xbrl_evidence_level               TEXT NOT NULL
        CHECK (xbrl_evidence_level IN ('provisional', 'review_required', 'conflicting', 'unavailable')),
    xbrl_resolution_sha256            TEXT
        CHECK (xbrl_resolution_sha256 IS NULL
               OR (length(xbrl_resolution_sha256) = 64
                   AND xbrl_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    -- Decision 083 R63 item B: the vocabulary is UNCHANGED. A verified linkage reuses
    -- 'amends_original'; no verified_amends_original state exists.
    amendment_linkage_state            TEXT
        CHECK (amendment_linkage_state IS NULL OR amendment_linkage_state IN (
            'amends_original', 'amends_prior_amendment', 'supplements_original',
            'possible_amendment_of', 'unresolved_amendment')),
    provisional_parent_accession       TEXT,
    amendment_purpose_category         TEXT
        CHECK (amendment_purpose_category IS NULL OR amendment_purpose_category IN (
            'administrative_or_exhibit', 'financial_or_xbrl_correction', 'narrative_or_governance')),
    -- Decision 014 section 6: amendment purpose is marked 'provisional' or 'unproven'
    -- only during M2.3 (definitive verification is filing-body evidence, M2.5).
    -- 'unproven' is distinct from the general review_required/conflicting/unavailable
    -- vocabulary: it means the category IS assignable from metadata but not provable
    -- without document evidence -- the ordinary case for every M2.3 amendment.
    --
    -- WIDENING 1 of 2 (Decision 080 section 9.3; Decision 087 section 7). 'verified' is
    -- admitted here and NOWHERE ELSE in the schema. It is the document-level evidence
    -- Decision 014 section 1 always defined and no migration could store, and the trigger
    -- below requires a frozen adjudicated row to stand behind every use of it.
    amendment_purpose_evidence_level   TEXT NOT NULL
        CHECK (amendment_purpose_evidence_level IN
               ('provisional', 'unproven', 'review_required', 'conflicting', 'unavailable',
                'verified')),
    amendment_purpose_resolution_sha256 TEXT
        CHECK (amendment_purpose_resolution_sha256 IS NULL
               OR (length(amendment_purpose_resolution_sha256) = 64
                   AND amendment_purpose_resolution_sha256 NOT GLOB '*[^0-9a-f]*')),
    -- No amendment-purpose classification may satisfy an affirmative quota at the
    -- 'unproven' level (Decision 014 section 6); only 'provisional' could, and now
    -- 'verified' can -- see WIDENING 2 of 2 in the table CHECK below.
    amendment_purpose_quota_eligible   INTEGER NOT NULL DEFAULT 0
        CHECK (amendment_purpose_quota_eligible IN (0, 1)),
    base_eligible                      INTEGER NOT NULL DEFAULT 0 CHECK (base_eligible IN (0, 1)),
    stress_eligible                    INTEGER NOT NULL DEFAULT 0 CHECK (stress_eligible IN (0, 1)),
    support_eligible                   INTEGER NOT NULL DEFAULT 0 CHECK (support_eligible IN (0, 1)),
    control_eligible                   INTEGER NOT NULL DEFAULT 0 CHECK (control_eligible IN (0, 1)),
    multi_registrant                   INTEGER NOT NULL DEFAULT 0 CHECK (multi_registrant IN (0, 1)),
    recorded_at_utc                    TEXT NOT NULL,
    detail                             TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (snapshot_id, accession_plain),
    UNIQUE (snapshot_id, accession_number_dashed),
    CHECK (base_eligible = 0
           OR (is_amendment = 0 AND cohort_ambiguous = 0 AND provisional_official_cohort IS NOT NULL)),
    CHECK ((official_filing_date IS NULL) = (filing_date_resolution_sha256 IS NULL)),
    CHECK ((provisional_official_cohort IS NULL) = (cohort_resolution_sha256 IS NULL)),
    CHECK ((xbrl_resolution_sha256 IS NOT NULL) = (xbrl_evidence_level = 'provisional')),
    CHECK ((amendment_purpose_category IS NULL) = (amendment_purpose_resolution_sha256 IS NULL)),
    -- WIDENING 2 of 2 (Decision 080 section 9.3; Decision 082 section 11.2). A verified
    -- category may satisfy an affirmative quota; 'unproven', 'review_required',
    -- 'conflicting', and 'unavailable' still may not. The 'provisional' route is unchanged.
    CHECK (amendment_purpose_quota_eligible = 0
           OR (amendment_purpose_category IS NOT NULL
               AND amendment_purpose_evidence_level IN ('provisional', 'verified'))),
    CHECK (is_amendment = 1 OR (amendment_linkage_state IS NULL AND provisional_parent_accession IS NULL)),
    CHECK (is_amendment = 0 OR amendment_linkage_state IS NOT NULL),
    -- Decision 083 R58/R59: an anchor exists only under an established set.
    CHECK (anchor_cik_numeric IS NULL OR registrant_set_completeness = 'established'),
    -- Decision 083 R58 and Decision 072 R23 section 5.3 restated anchor-free: under an
    -- established set the anchor is present exactly when the accession is not
    -- multi-registrant.
    CHECK (registrant_set_completeness <> 'established'
           OR ((anchor_cik_numeric IS NULL) = (multi_registrant = 1)))
) STRICT;

INSERT INTO pilot_candidate_accessions_m0015 (
    snapshot_id, accession_plain, accession_number_dashed, accession_tie_break_sha256,
    anchor_cik_numeric, registrant_set_completeness, form_type, is_amendment,
    official_filing_date, report_date, acceptance_audit_date, filing_date_evidence_level,
    filing_date_resolution_sha256, filing_date_precedence, provisional_official_cohort,
    acceptance_audit_cohort, cohort_evidence_level, cohort_resolution_sha256,
    cohort_ambiguous, has_xbrl, has_inline_xbrl, xbrl_evidence_level,
    xbrl_resolution_sha256, amendment_linkage_state, provisional_parent_accession,
    amendment_purpose_category, amendment_purpose_evidence_level,
    amendment_purpose_resolution_sha256, amendment_purpose_quota_eligible, base_eligible,
    stress_eligible, support_eligible, control_eligible, multi_registrant,
    recorded_at_utc, detail)
SELECT
    snapshot_id, accession_plain, accession_number_dashed, accession_tie_break_sha256,
    anchor_cik_numeric, registrant_set_completeness, form_type, is_amendment,
    official_filing_date, report_date, acceptance_audit_date, filing_date_evidence_level,
    filing_date_resolution_sha256, filing_date_precedence, provisional_official_cohort,
    acceptance_audit_cohort, cohort_evidence_level, cohort_resolution_sha256,
    cohort_ambiguous, has_xbrl, has_inline_xbrl, xbrl_evidence_level,
    xbrl_resolution_sha256, amendment_linkage_state, provisional_parent_accession,
    amendment_purpose_category, amendment_purpose_evidence_level,
    amendment_purpose_resolution_sha256, amendment_purpose_quota_eligible, base_eligible,
    stress_eligible, support_eligible, control_eligible, multi_registrant,
    recorded_at_utc, detail
FROM pilot_candidate_accessions;

DROP TABLE pilot_candidate_accessions;
ALTER TABLE pilot_candidate_accessions_m0015 RENAME TO pilot_candidate_accessions;

CREATE INDEX idx_pilot_candidate_accessions_cohort
    ON pilot_candidate_accessions (snapshot_id, provisional_official_cohort);
CREATE INDEX idx_pilot_candidate_accessions_eligibility
    ON pilot_candidate_accessions (snapshot_id, base_eligible, stress_eligible, support_eligible, control_eligible);
CREATE INDEX idx_pilot_candidate_accessions_tie_break
    ON pilot_candidate_accessions (snapshot_id, accession_tie_break_sha256);

CREATE TRIGGER pilot_candidate_accessions_insert_guard
BEFORE INSERT ON pilot_candidate_accessions
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = NEW.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession insert requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accessions_update_guard
BEFORE UPDATE ON pilot_candidate_accessions
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession update requires a building snapshot'); END;
CREATE TRIGGER pilot_candidate_accessions_delete_guard
BEFORE DELETE ON pilot_candidate_accessions
WHEN (SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = OLD.snapshot_id) <> 'building'
BEGIN SELECT RAISE(ABORT, 'pilot candidate accession delete requires a building snapshot'); END;

-- The widening is not a licence to assert. 'verified' is a claim that adjudicated document
-- evidence exists, so it requires that evidence to actually be there and to actually say
-- so: a frozen document_adjudicated_evidence row for this accession, of kind
-- amendment_purpose, at evidence_level 'verified'. Two triggers because the false state has
-- two doors -- a row that arrives verified, and a row updated to verified.
--
-- accession_plain in the candidate layer is the 18-digit plain accession, which is the same
-- key document_adjudicated_evidence uses, so the join is direct and needs no translation.
CREATE TRIGGER pilot_candidate_accessions_verified_purpose_requires_evidence_insert
BEFORE INSERT ON pilot_candidate_accessions
WHEN NEW.amendment_purpose_evidence_level = 'verified'
BEGIN
    SELECT RAISE(ABORT,
        'a verified amendment purpose requires frozen adjudicated document evidence for that accession')
    WHERE NOT EXISTS (
        SELECT 1 FROM document_adjudicated_evidence
        WHERE accession_plain = NEW.accession_plain
          AND evidence_kind = 'amendment_purpose'
          AND evidence_level = 'verified'
    );
END;

CREATE TRIGGER pilot_candidate_accessions_verified_purpose_requires_evidence_update
BEFORE UPDATE OF amendment_purpose_evidence_level ON pilot_candidate_accessions
WHEN NEW.amendment_purpose_evidence_level = 'verified'
BEGIN
    SELECT RAISE(ABORT,
        'a verified amendment purpose requires frozen adjudicated document evidence for that accession')
    WHERE NOT EXISTS (
        SELECT 1 FROM document_adjudicated_evidence
        WHERE accession_plain = NEW.accession_plain
          AND evidence_kind = 'amendment_purpose'
          AND evidence_level = 'verified'
    );
END;

-- The rebuild is complete and the renamed table carries its original name again, so the
-- default whole-schema rename validation is restored for the rest of this connection's
-- life. The migration never leaves it relaxed.
PRAGMA legacy_alter_table = OFF;
