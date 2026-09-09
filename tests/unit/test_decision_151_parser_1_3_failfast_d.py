"""Decision 151 -- R2-C parser 1.3 and FailFast-D, proved.

The thirty-four proofs the owner packet requires (§14), in its order and under its numbers:

* **Parser** (1-9, 23): a valid CIK with an absent, null, non-string or blank current name is a
  field-level, non-blocking company-name defect; an unusable CIK is still document-fatal;
  ``formerNames`` never becomes the current name; the nested regions are read from their own
  values; ordinary documents are unchanged; the version authority pins 1.3; and neither
  truthiness nor ``str()`` coercion can validate a non-string name.
* **Shard consistency** (10, 11, 24): the narrow declaration extractor and the parser agree on
  every deficient-name parent; no parentage is manufactured; the one residual (a malformed
  top-level array) is named and contained downstream.
* **FailFast** (12-18, 25, 26): a blocking chunk cannot enter the single-pass merge or either
  level-1 worker; the failed chunk is retained; the ``/2`` intermediate receipt exposes what the
  merge observed; a blocking outcome refuses the exact deletion; a blocking committed S2 stops the
  level-2 spine before any S3 statement, fresh and resumed and after a crash; a non-blocking S2
  continues; S19 is unchanged; a name-only quarantine stays non-blocking through chunk, level 1
  and S2.
* **Restartability / status** (19-22, 31): the committed S2 witness is re-derived from its row on
  every resume; tampered or inconsistent witnesses conflict; an authentic non-blocking witness
  resumes; ``status="complete"`` is never a success predicate.
* **Contract / provenance** (27, 28, 32-34): ``/2`` round-trips and refuses incomplete or
  contradictory evidence; ``/1`` is forensic-only and writes nothing; the alien fixture and the
  two current-contract pins moved; the witness-ledger identity moved with the contract, by
  exactly the contract, and the historical ``/1`` identity handling did not.

Every world here is synthetic and test-owned. No historical estate, external volume or
pre-existing scratch is read or written.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import shutil
import sqlite3
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_c27r1_dependency_closed_subset as c27  # noqa: E402
import test_d151_c29r1_retention_aware_calibration as c29  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401
from test_d151_r19_stage_restart import _raise_once  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import offline_parse as parse  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    ChunkEvidenceError,
    read_receipt_document,
    write_once_json,
)
from disclosure_drift.m3.offline_parse import (  # noqa: E402
    _STREAMED_PARSER_STATE,
    OfflineParseError,
    PlannedSourceOutcome,
    SingleSourceOutcome,
)
from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME  # noqa: E402
from disclosure_drift.reasons import REASON_CODES  # noqa: E402
from disclosure_drift.sec.census import _stable_id  # noqa: E402
from disclosure_drift.sec.parsers import submissions as sub  # noqa: E402
from disclosure_drift.sec.parsers.base import RecordLocation  # noqa: E402
from disclosure_drift.sec.parsers.versions import PARSER_VERSIONS, parser_version_for  # noqa: E402
from disclosure_drift.sec.schema_drift import inspect_payload  # noqa: E402
from disclosure_drift.sec.source_registry import SOURCES  # noqa: E402

LOCATION = RecordLocation(
    observation_id="obs-1", source_id="sec_bulk_submissions", member_name="CIK0000000007.json"
)
NEW_CODE = "PARSER_REGISTRANT_NAME_DEFICIENT"
#: The four deficiency classes, each as a document mutation.
DEFICIENCIES: dict[str, Any] = {
    "absent": lambda document: document.pop("name"),
    "null": lambda document: document.__setitem__("name", None),
    "non_string": lambda document: document.__setitem__("name", 7),
    "blank": lambda document: document.__setitem__("name", "   \t"),
}


@pytest.fixture(autouse=True)
def _volume_seam() -> Any:
    """The calibration route's volume-identity seam, beside the shared pin."""
    patcher = pytest.MonkeyPatch()
    patcher.setattr(ewr, "macos_volume_identity", c13.synthetic_volume_provider())
    yield
    patcher.undo()


# ==========================================================================
# Shared documents and worlds
# ==========================================================================
def document(**overrides: Any) -> dict[str, Any]:
    """One ordinary primary document with a shard declaration and a former name."""
    _name, payload = c1.primary_document(
        7, filings=2, declares=(c27.shard_name(7),), shared_alias=False
    )
    payload.update(overrides)
    return payload


def deficient(klass: str, **overrides: Any) -> dict[str, Any]:
    payload = document(**overrides)
    DEFICIENCIES[klass](payload)
    return payload


def parsed(payload: dict[str, Any]) -> Any:
    return sub.parse_submissions_document(payload, LOCATION)


def name_quarantines(outcome: Any) -> list[Any]:
    return [item for item in outcome.quarantined if item.location.record_path == sub.REGION_NAME]


def members_with(mutate: dict[int, Any], **shape: Any) -> list[tuple[str, dict[str, Any]]]:
    """The shared synthetic member sequence with ``mutate[cik]`` applied to that primary."""
    shape.setdefault("members", 9)
    shape.setdefault("filings", 2)
    shape.setdefault("shards", 1)
    built = c1.entries(**shape)
    for name, payload in built:
        if name.startswith("CIK") and "-submissions-" not in name:
            cik = int(name[3:13])
            if cik in mutate:
                mutate[cik](payload)
    return built


def custom_world(root: Path, members: list[tuple[str, dict[str, Any]]]) -> tuple[Path, Any]:
    return c27.build_world(root, members)


def blank_name(payload: dict[str, Any]) -> None:
    payload["name"] = ""


def null_recent(payload: dict[str, Any]) -> None:
    payload["filings"]["recent"] = None


def malformed_declaring_parent(payload: dict[str, Any]) -> None:
    """Valid CIK, blank name, and the one residual: a non-list top-level array."""
    payload["name"] = ""
    payload["tickers"] = "not-a-list"


def production_run(tmp_path: Path, database: Path, tree: Any) -> dict[str, Any]:
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    return c13.execute_in_process(plan, tmp_path / "run", database, tree)


def estate_from_world(
    tmp_path: Path, database: Path, tree: Any, *, label: str = "successor"
) -> r19.SuccessorWorld:
    """The R19 successor estate over a CUSTOM world: chunks, level-1 intermediates, requests."""
    run = production_run(tmp_path, database, tree)
    succ = c13.merge_in_process(
        run, database, label=label, finalize=False, requirements=r19.R19B_REQUIREMENTS
    )
    r19.write_group_requests(run, succ, database)
    return r19.SuccessorWorld(
        database=database,
        run=run,
        succ=succ,
        legacy=None,
        world=succ["multipass_root"] / "successor-final",
        receipt_root=succ["multipass_root"] / "successor-receipts",
        requirements=r19.R19B_REQUIREMENTS,
    )


def chunk_catalog(run: dict[str, Any], chunk_id: str) -> Path:
    found = ce.completed_chunk_receipt(run["chunk_root"], chunk_id)
    assert found is not None
    return found[1] / WORKING_CATALOG_FILENAME


def readonly(path: Path) -> sqlite3.Connection:
    # URI-safe by the same ``Path.as_uri()`` idiom the production reader uses (D151-C31R2
    # MINOR-2): the proofs below point this helper at catalogs under URI-significant directory
    # names, where a raw ``file:{path}`` f-string truncates the path instead of addressing it.
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def inject_blocking_reduction(patch: pytest.MonkeyPatch, module: Any) -> None:
    """Make ``module._reduced_parser_run`` reach a SELF-CONSISTENT blocking terminal.

    The accepted reduction runs and writes its row; the row is then moved to ``failed`` with one
    blocking structural failure in its summary -- exactly what the accepted rule would have
    written had an input carried one -- and the returned reduction says so. Since Decision 151
    Boundary 2 refuses a failed chunk at admission, this is the only way a blocking reduced run
    can be committed at level 2, and the S2 witness verification (MINOR-1) must accept it as an
    AUTHENTIC blocking terminal rather than as a conflict.
    """
    original = module._reduced_parser_run

    def failed(
        connection: Any, aliases: Any, *, contract: Any, statement_runner: Any = None
    ) -> Any:
        reduced = original(
            connection, aliases, contract=contract, statement_runner=statement_runner
        )
        row = connection.execute(
            "SELECT summary_json FROM census_parser_runs WHERE parser_run_id = ?",
            (reduced.parser_run_id,),
        ).fetchone()
        summary = json.loads(str(row["summary_json"]))
        summary["structural_detail"]["blocking"] = 1
        summary["counts"]["structural_failures"] = 1
        summary["counts_are_trustworthy"] = False
        connection.execute(
            "UPDATE census_parser_runs SET outcome = 'failed', summary_json = ? "
            "WHERE parser_run_id = ?",
            (json.dumps(summary, sort_keys=True, separators=(",", ":")), reduced.parser_run_id),
        )
        return replace(reduced, outcome="failed", parser_state="failed", blocking_structural=1)

    patch.setattr(module, "_reduced_parser_run", failed)


def semantic_refusals(estate: r19.SuccessorWorld) -> list[str]:
    if not estate.receipt_root.is_dir():
        return []
    return sorted(
        path.name
        for path in estate.receipt_root.iterdir()
        if path.name.startswith("semantic-refusal-")
    )


def s3_statements(statements: list[str]) -> list[str]:
    return [item for item in statements if "INTO census_parsed_records" in item]


# ==========================================================================
# PARSER -- proofs 1-9 and 23
# ==========================================================================
@pytest.mark.parametrize("klass", list(DEFICIENCIES))
def test_p01_to_p04_each_deficient_name_is_a_field_level_non_blocking_defect(klass: str) -> None:
    outcome, references = parsed(deficient(klass))
    # 1-4: the structure is evaluable on its own values, and the registrant is persisted by CIK.
    assert outcome.region_state(sub.REGION_RECENT) == "valid_present"
    assert outcome.region_state(sub.REGION_FILES) == "valid_present"
    assert outcome.counts_are_trustworthy
    identities = [record.native_identity for record in outcome.records]
    assert identities[0] == "registrant:0000000007"
    assert len(identities) == 3
    assert references and references[0].is_retrievable
    # Exactly one name-field quarantine, the new code, the class in its detail, the observed
    # value retained -- and nothing blocking.
    (quarantine,) = name_quarantines(outcome)
    assert quarantine.reason_codes == (NEW_CODE,)
    assert quarantine.native_identity == "registrant:0000000007"
    assert quarantine.parser_version == "submissions-json/1.3"
    assert quarantine.detail.startswith(f"current company name is {klass}:")
    detail_words = {
        "absent": "no 'name' key",
        "null": "present and null",
        "non_string": "is a int, not a string",
        "blank": "blank after stripping",
    }
    assert detail_words[klass] in quarantine.detail
    assert quarantine.raw_excerpt == ("" if klass == "absent" else repr(deficient(klass)["name"]))
    assert "SEC_SCHEMA_REQUIRED_FIELD_MISSING" not in outcome.reason_codes
    assert not outcome.required_field_failures
    assert NEW_CODE in outcome.reason_codes
    assert not REASON_CODES[NEW_CODE].blocks_release
    assert REASON_CODES[NEW_CODE].requires_manual_review
    # The registrant record carries no current name at all, and no drift was reported for it.
    registrant = outcome.records[0]
    assert "name" not in registrant.payload
    assert "name" not in outcome.unknown_fields
    assert any(f"name is {klass}" in warning for warning in outcome.normalization_warnings)
    # The accepted state machine: quarantined, never failed.
    assert parse._parser_state_for(outcome) == "quarantined"


def test_p05_an_unusable_cik_remains_blocking_and_a_name_defect_rescues_nothing() -> None:
    outcome, references = parsed(document(cik="not-a-cik"))
    assert not outcome.records and references == ()
    assert outcome.required_field_failures == (("cik", "CIK is not canonically usable"),)
    assert outcome.quarantined[0].reason_codes == ("SEC_SCHEMA_REQUIRED_FIELD_MISSING",)
    assert outcome.region_state(sub.REGION_RECENT) == "indeterminate"
    assert not outcome.counts_are_trustworthy
    assert parse._parser_state_for(outcome) == "failed"
    # Both defects at once: the CIK refusal is the whole answer -- no name quarantine is added,
    # no name failure is folded in, and nothing is rescued.
    for klass in DEFICIENCIES:
        both, _ = parsed(deficient(klass, cik="not-a-cik"))
        assert both.required_field_failures == (("cik", "CIK is not canonically usable"),)
        assert len(both.quarantined) == 1
        assert not name_quarantines(both)
        assert NEW_CODE not in both.reason_codes
        assert parse._parser_state_for(both) == "failed"


def test_p06_former_names_never_become_the_current_company_name(tmp_path: Path) -> None:
    """The parsed record carries no current name and the census emits no company_name row."""
    for klass in DEFICIENCIES:
        outcome, _ = parsed(deficient(klass))
        registrant = outcome.records[0]
        assert "name" not in registrant.payload
        assert registrant.payload["formerNames"] == [
            {"name": "OLD 7", "from": "2018-01-01", "to": "2020-01-01"}
        ]
    # Through the accepted writer: a chunk world whose one blank-name registrant is persisted by
    # CIK with its former name, and with NO company_name observation.
    database, tree = custom_world(tmp_path, members_with({4: blank_name}))
    run = production_run(tmp_path, database, tree)
    with readonly(chunk_catalog(run, "chunk-0003")) as connection:
        registrant = connection.execute(
            "SELECT cik_numeric FROM census_registrants WHERE cik_numeric = 4"
        ).fetchone()
        kinds = {
            str(row["observation_kind"])
            for row in connection.execute(
                "SELECT observation_kind FROM census_registrant_observations WHERE cik_numeric = 4"
            )
        }
        quarantined = connection.execute(
            "SELECT reason_codes_json, record_path FROM census_quarantined_records"
        ).fetchall()
    assert registrant is not None
    assert "company_name" not in kinds
    assert "former_name" in kinds and "ticker" in kinds
    assert len(quarantined) == 1
    assert NEW_CODE in str(quarantined[0]["reason_codes_json"])
    assert str(quarantined[0]["record_path"]) == "name"


def test_p07_the_nested_regions_reflect_their_own_supplied_values() -> None:
    absent_recent = deficient("blank")
    del absent_recent["filings"]["recent"]
    outcome, _ = parsed(absent_recent)
    assert outcome.region_state(sub.REGION_RECENT) == "absent"
    assert outcome.region_state(sub.REGION_FILES) == "valid_present"
    assert not outcome.counts_are_trustworthy
    assert len(name_quarantines(outcome)) == 1
    assert parse._parser_state_for(outcome) == "failed"
    null_files = deficient("null")
    null_files["filings"]["files"] = None
    outcome, _ = parsed(null_files)
    assert outcome.region_state(sub.REGION_RECENT) == "valid_present"
    assert outcome.region_state(sub.REGION_FILES) == "null"
    assert len(name_quarantines(outcome)) == 1
    empty = deficient("absent")
    empty["filings"]["recent"] = {}
    empty["filings"]["files"] = []
    outcome, _ = parsed(empty)
    assert outcome.region_state(sub.REGION_RECENT) == "valid_empty"
    assert outcome.region_state(sub.REGION_FILES) == "valid_empty"
    assert outcome.counts_are_trustworthy
    assert len(name_quarantines(outcome)) == 1
    assert parse._parser_state_for(outcome) == "quarantined"


def test_p08_an_ordinary_document_is_unchanged() -> None:
    outcome, references = parsed(document())
    assert outcome.parser_version == "submissions-json/1.3"
    assert not outcome.quarantined and not outcome.required_field_failures
    assert outcome.records[0].payload["name"] == "SYNTHETIC 7"
    assert outcome.unknown_fields == ()
    assert not outcome.normalization_warnings
    assert outcome.counts_are_trustworthy
    assert len(references) == 1
    assert parse._parser_state_for(outcome) == "completed"
    assert outcome.reason_codes == ()


def test_p09_the_parser_version_authority_pins_one_three() -> None:
    assert sub.PARSER_VERSION == "submissions-json/1.3"
    assert PARSER_VERSIONS[sub.PARSER_ID] == "submissions-json/1.3"
    assert parser_version_for(sub.PARSER_ID) == "submissions-json/1.3"
    assert SOURCES["sec_bulk_submissions"].parser_version == "submissions-json/1.3"
    assert SOURCES["sec_submissions_entity"].parser_version == "submissions-json/1.3"
    outcome, _ = parsed(deficient("blank"))
    assert {item.parser_version for item in (*outcome.records, *outcome.quarantined)} == {
        "submissions-json/1.3"
    }


def test_p23_names_escape_the_old_gate_without_drift_or_coercion() -> None:
    assert "name" not in sub._REQUIRED_TOP_LEVEL
    assert "name" in sub._OPTIONAL_TOP_LEVEL
    for klass in DEFICIENCIES:
        drift = inspect_payload(
            deficient(klass),
            source_class="sec_submissions_document",
            required_fields=sub._REQUIRED_TOP_LEVEL,
            optional_fields=sub._OPTIONAL_TOP_LEVEL,
            array_fields=sub._ARRAY_TOP_LEVEL,
        )
        assert not drift.blocking_events
        assert "name" not in drift.retained_unknown_fields
    ordinary = inspect_payload(
        document(),
        source_class="sec_submissions_document",
        required_fields=sub._REQUIRED_TOP_LEVEL,
        optional_fields=sub._OPTIONAL_TOP_LEVEL,
        array_fields=sub._ARRAY_TOP_LEVEL,
    )
    assert ordinary.retained_unknown_fields == ()
    # Classification by membership, type and strip only: values truthiness would merge and
    # values str() would turn into names stay in their own classes.
    assert sub.classify_current_name({}) == (None, "absent")
    assert sub.classify_current_name({"name": None}) == (None, "null")
    for value in (0, 7, 1.5, True, False, [], ["ACME"], {}, {"n": "ACME"}, b"ACME"):
        assert sub.classify_current_name({"name": value}) == (None, "non_string"), value
    for text in ("", " ", "\t\n"):
        assert sub.classify_current_name({"name": text}) == (None, "blank"), text
    assert sub.classify_current_name({"name": " ACME "}) == (" ACME ", None)
    source = inspect.getsource(sub.classify_current_name).split('"""')[2]
    assert "str(" not in source and " or " not in source and "bool(" not in source
    assert sub.NAME_DEFICIENCY_CLASSES == ("absent", "null", "non_string", "blank")


# ==========================================================================
# SHARD CONSISTENCY -- proofs 10, 11 and 24
# ==========================================================================
@pytest.mark.parametrize("klass", list(DEFICIENCIES))
def test_p10_a_deficient_name_parent_is_declared_consistently_by_extractor_and_parser(
    klass: str,
) -> None:
    payload = deficient(klass)
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    padded, declared_names = parse._primary_document_declarations(raw)
    assert padded == "0000000007" and declared_names == (c27.shard_name(7),)
    outcome, references = parsed(payload)
    assert [item.name for item in references] == [c27.shard_name(7)]
    assert references[0].registrant_cik_padded == "0000000007"
    declared: dict[str, set[str]] = {}
    parse._declare_shard_parents(declared, references, frozenset({c27.shard_name(7)}))
    assert declared == {c27.shard_name(7): {"0000000007"}}
    assert parse._resolve_shard_parent(c27.shard_name(7), declared) == "0000000007"
    assert not outcome.required_field_failures


def test_p10_the_structural_preflight_binds_deficient_name_parents(tmp_path: Path) -> None:
    members = c27.members_for(
        4,
        declares={cik: (c27.shard_name(cik),) for cik in (1, 2, 3, 4)},
        shards=[(cik, 1) for cik in (1, 2, 3, 4)],
    )
    for (name, payload), klass in zip(members[4:], DEFICIENCIES, strict=True):
        assert name.startswith("CIK") and "-submissions-" not in name
        DEFICIENCIES[klass](payload)
    archive = tmp_path / "preflight.zip"
    c1.write_archive(archive, members)
    proof = parse.structural_source_preflight(archive)
    assert proof.parent_map_sound and proof.shard_members == 4 == proof.declared_shard_names
    assert proof.orphan_count == 0 and proof.duplicate_parent_count == 0


def test_p11_no_undeclared_or_contradictory_parent_is_manufactured() -> None:
    # A deficient-name parent that declares a shard whose filename contradicts it: refused.
    payload = deficient("blank")
    payload["filings"]["files"][0]["name"] = c27.shard_name(8)
    _, references = parsed(payload)
    declared: dict[str, set[str]] = {}
    parse._declare_shard_parents(declared, references, frozenset({c27.shard_name(8)}))
    assert declared == {c27.shard_name(8): {"0000000007"}}
    with pytest.raises(OfflineParseError, match="contradicts|filename encodes"):
        parse._resolve_shard_parent(c27.shard_name(8), declared)
    # A shard nobody declares stays undeclared, whatever its filename says.
    with pytest.raises(OfflineParseError, match="no primary submissions document declares"):
        parse._resolve_shard_parent(c27.shard_name(9), declared)
    # An unusable CIK declares nothing on either side, name or no name.
    raw = json.dumps(document(cik="not-a-cik"), sort_keys=True).encode("utf-8")
    padded, _names = parse._primary_document_declarations(raw)
    assert padded is None  # the preflight and the closure skip a registrant-less document
    _, references = parsed(document(cik="not-a-cik"))
    assert references == ()


def test_p24_the_malformed_array_residual_is_named_and_contained(tmp_path: Path) -> None:
    """The one residual: valid CIK, blank name, and a non-list ``tickers``.

    The extractor declares the shard (it never reads the arrays); the parser refuses the whole
    document and declares nothing; the preflight therefore reports a sound map while F0 refuses
    the shard as undeclared -- BEFORE the shard chunk parses one member. Named in the extractor's
    own docstring rather than hidden.
    """
    assert "residual" in inspect.getsource(parse._primary_document_declarations)
    payload = deficient("blank", tickers="not-a-list")
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    assert parse._primary_document_declarations(raw) == ("0000000007", (c27.shard_name(7),))
    outcome, references = parsed(payload)
    assert references == () and not outcome.records
    assert outcome.quarantined[0].reason_codes == ("SEC_SCHEMA_REQUIRED_FIELD_MISSING",)
    assert "tickers" in outcome.quarantined[0].detail
    declared: dict[str, set[str]] = {}
    parse._declare_shard_parents(declared, references, frozenset({c27.shard_name(7)}))
    assert declared == {}
    with pytest.raises(OfflineParseError, match="no primary submissions document declares"):
        parse._resolve_shard_parent(c27.shard_name(7), declared)
    # End to end: the preflight is optimistic, the chunked F0 refuses at the shard chunk.
    members = members_with({1: malformed_declaring_parent})
    database, tree = custom_world(tmp_path, members)
    assert parse.structural_source_preflight(c1.archive_of(tree)).parent_map_sound
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    assert plan.chunks[-1].region == "shard"
    with pytest.raises(OfflineParseError, match="no primary submissions document declares"):
        c13.execute_in_process(plan, tmp_path / "run", database, tree)
    assert ce.completed_chunk_receipt(tmp_path / "run" / "chunks", plan.chunks[-1].chunk_id) is None


# ==========================================================================
# FAILFAST -- proofs 12-18, 25 and 26
# ==========================================================================
def test_p12_p13_p25_a_blocking_chunk_cannot_enter_any_merge_and_is_retained(
    tmp_path: Path,
) -> None:
    database, tree = custom_world(tmp_path, members_with({5: null_recent}))
    run = production_run(tmp_path, database, tree)
    schedule = cm.derive_merge_schedule(run["plan"])
    inputs = cc.resolve_chunk_inputs(run["plan"], internal_root=run["chunk_root"])
    semantics = {item.chunk_id: cc.chunk_semantics(item) for item in inputs}
    assert semantics["chunk-0004"].blocking
    assert semantics["chunk-0004"].run_outcome == "failed"
    assert semantics["chunk-0004"].blocking_structural == 1
    assert not semantics["chunk-0000"].blocking
    failed_group = next(g for g in schedule.groups if "chunk-0004" in g.chunk_ids)
    healthy_group = next(g for g in schedule.groups if "chunk-0004" not in g.chunk_ids)
    # 25: the production level-1 worker, entered directly, refuses BEFORE its attempt exists.
    multipass_root = run["base"] / "multipass"
    multipass_root.mkdir()
    schedule_path = multipass_root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    intermediates_root = multipass_root / "intermediates"

    def request(group: cm.MergeGroup) -> tuple[cm.GroupMergeRequest, Path]:
        directory, attempt = cm.next_intermediate_attempt_directory(
            intermediates_root, group.group_id
        )
        return c13.group_request(
            run,
            schedule_path=schedule_path,
            group_id=group.group_id,
            attempt=attempt,
            attempt_directory=directory,
            database=database,
        ), directory

    failed_request, failed_directory = request(failed_group)
    with pytest.raises(cc.ChunkConsolidationError, match="BLOCKING parser terminal") as raised:
        cm.merge_group_body(failed_request)
    assert "chunk-0004" in str(raised.value)
    assert not failed_directory.exists() and not intermediates_root.exists()
    # ... the single-pass consolidator refuses before its world exists -- over its OWN plan,
    # since the single-pass cap admits nine chunks and the same source re-chunks at two ...
    single = c1x.run_chunked_f0(
        tmp_path / "single-pass",
        database,
        tree,
        chunk_members=2,
        label="sp",
        batch_size=2,
        repository=c1.PINNED,
    )
    with pytest.raises(cc.ChunkConsolidationError, match="BLOCKING parser terminal"):
        cc.consolidate_chunks(
            plan=single["plan"],
            internal_root=single["chunk_root"],
            operational_catalog=database,
            world_directory=single["base"] / "final",
            run_id="single-pass",
        )
    assert not (single["base"] / "final").exists()
    # ... a healthy group of the same plan still merges (positive control) ...
    healthy_request, healthy_directory = request(healthy_group)
    receipt = cm.merge_group_body(healthy_request)
    assert receipt.status == "complete" and not receipt.blocking
    assert healthy_directory.is_dir()
    # 13: the failed chunk world is retained exactly as it was, and read-only resolution --
    # whole-plan and group-local -- still reaches it.
    found = ce.completed_chunk_receipt(run["chunk_root"], "chunk-0004")
    assert found is not None and found[0].status == "complete"
    assert found[0].summary.run_outcome == "failed"
    (again,) = cc.resolve_contiguous_chunk_inputs(
        run["plan"], ("chunk-0004",), internal_root=run["chunk_root"]
    )
    assert again.chunk_id == "chunk-0004"
    # The admission predicate never READS a receipt's status: no attribute access in its code.
    code = inspect.getsource(cc.require_admissible_chunk_semantics).split('"""')[2]
    assert ".status" not in code and "status ==" not in code


def test_p25_the_calibration_worker_refuses_a_blocking_chunk_before_its_attempt(
    tmp_path: Path,
) -> None:
    members = c27.members_for(
        12,
        declares={cik: (c27.shard_name(cik),) for cik in (1, 3, 12)},
        shards=[(1, 1), (3, 1), (12, 1)],
    )
    for name, payload in members:
        if name == "CIK0000000002.json":
            null_recent(payload)
    database, tree = custom_world(tmp_path, members)
    plan = c27.subset_plan(tree, database, prefix=10)
    run = c27.execute_chunks_in_process(plan, tmp_path / "run", database, tree)
    partial = c27.prepared_multipass(run)
    group = next(g for g in partial["schedule"].groups if "chunk-0001" in g.chunk_ids)
    request, _path, envelope, directory = c29.group_launch(run, partial, group, database)
    with pytest.raises(cc.ChunkConsolidationError, match="BLOCKING parser terminal"):
        cm.merge_calibration_subset_group_body(request, envelope)
    assert not directory.exists()
    assert ce.completed_chunk_receipt(run["chunk_root"], "chunk-0001") is not None


def test_p14_the_intermediate_receipt_exposes_what_the_merge_observed(tmp_path: Path) -> None:
    database, tree = custom_world(tmp_path, members_with({4: blank_name}))
    run = production_run(tmp_path, database, tree)
    partial = c13.merge_in_process(run, database, finalize=False)
    inputs = {
        item.chunk_id: cc.chunk_semantics(item)
        for item in cc.resolve_chunk_inputs(run["plan"], internal_root=run["chunk_root"])
    }
    for group, receipt in zip(partial["schedule"].groups, partial["intermediates"], strict=True):
        expected_quarantined = sum(inputs[c].quarantined for c in group.chunk_ids)
        assert receipt.contract == "m3.3-chunked-f0-intermediate-receipt/2"
        assert receipt.observed_quarantined == expected_quarantined
        assert receipt.observed_blocking_structural == 0
        assert receipt.inputs_reached_blocking_terminal is False
        assert receipt.observed_run_outcome == (
            "completed_with_quarantine" if expected_quarantined else "completed"
        )
        assert receipt.observed_parser_state == _STREAMED_PARSER_STATE[receipt.observed_run_outcome]
        assert not receipt.blocking
        assert (
            cm.require_admissible_intermediate_semantics(receipt) == receipt.observed_parser_state
        )
        directory = (
            partial["intermediates_root"] / group.group_id / f"attempt-{receipt.attempt:03d}"
        )
        stored = read_receipt_document(
            directory / cm.INTERMEDIATE_RECEIPT_FILENAME, contract=cm.INTERMEDIATE_RECEIPT_CONTRACT
        )
        for key in cm._OBSERVED_SEMANTICS_KEYS:
            assert key in stored
        assert cm.IntermediateReceipt.from_record(stored) == receipt
        # The observed values are the intermediate's OWN row, not a claim.
        with readonly(directory / WORKING_CATALOG_FILENAME) as connection:
            row = connection.execute(
                "SELECT outcome, quarantined_count FROM census_parser_runs"
            ).fetchone()
        assert (str(row["outcome"]), int(row["quarantined_count"])) == (
            receipt.observed_run_outcome,
            receipt.observed_quarantined,
        )
    assert any(item.observed_quarantined == 1 for item in partial["intermediates"])


def test_p15_p29_a_blocking_outcome_refuses_the_exact_deletion_and_retains_the_worlds(
    tmp_path: Path,
) -> None:
    """Direct ``delete_calibration_group_chunk_worlds`` invocation over a blocking group.

    A blocking group cannot ordinarily acquire an intermediate at all (Boundary 2), so the
    intermediate is produced with admission's REFUSAL neutralised -- the shape a pre-Decision-151
    estate would carry -- and checkpointed; the deletion function itself then refuses, on the
    intermediate's observed semantics and on the chunk world's own receipt and row, and every
    world is byte-for-byte where it was.
    """
    members = c27.members_for(
        12,
        declares={cik: (c27.shard_name(cik),) for cik in (1, 3, 12)},
        shards=[(1, 1), (3, 1), (12, 1)],
    )
    for name, payload in members:
        if name == "CIK0000000002.json":
            null_recent(payload)
    database, tree = custom_world(tmp_path, members)
    plan = c27.subset_plan(tree, database, prefix=10)
    run = c27.execute_chunks_in_process(plan, tmp_path / "run", database, tree)
    partial = c27.prepared_multipass(run)
    group = next(g for g in partial["schedule"].groups if "chunk-0001" in g.chunk_ids)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            cm,
            "require_admissible_chunk_semantics",
            lambda inputs: tuple(cc.chunk_semantics(item) for item in inputs),
        )
        for chunk_id in group.chunk_ids:
            c29.write_witness(run, partial, chunk_id)
        receipt = c29.merge_group(run, partial, group, database)
        checkpoint = c29.write_checkpoint(run, partial, group.group_id)
    assert receipt.observed_run_outcome == "failed" and receipt.inputs_reached_blocking_terminal
    assert receipt.blocking and checkpoint.group_id == group.group_id
    worlds = {c: c29.snapshot(c29.world_of(run, c)) for c in group.chunk_ids}
    grant = c29.grant_for(partial, plan, group.group_id)
    with pytest.raises(cm.ChunkMultipassError, match="BLOCKING reduced run"):
        c29.delete_group(run, partial, group.group_id, grant)
    assert {c: c29.snapshot(c29.world_of(run, c)) for c in group.chunk_ids} == worlds
    assert not cm.calibration_group_deletion_path(c29.retained_of(partial), group.group_id).exists()
    # The intermediate is forensic: readable by the resolver, refused by every admission.
    found = cm.completed_intermediate_receipt(partial["intermediates_root"], group.group_id)
    assert found is not None and found[0] == receipt
    with pytest.raises(cm.ChunkMultipassError, match="BLOCKING reduced run"):
        cm.require_admissible_intermediate_semantics(found[0])
    # And the chunk-world predicate of the deletion refuses the failed world on its own.
    binding = next(item for item in checkpoint.chunks if item.chunk_id == "chunk-0001")
    with pytest.raises(cm.ChunkMultipassError, match="BLOCKING parser terminal"):
        cm._require_deletable_chunk_semantics(
            c29.world_of(run, "chunk-0001"), binding, binding.entries
        )
    assert inspect.getsource(cm.delete_calibration_group_chunk_worlds).index(
        "require_admissible_intermediate_semantics("
    ) < inspect.getsource(cm.delete_calibration_group_chunk_worlds).index("free_before = ")


def test_p16_p30_a_blocking_committed_s2_stops_the_spine_before_any_s3_statement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    statements: list[str] = []
    r19.install_trace(monkeypatch, statements)
    # Fresh execution: S2 commits a (self-consistent) blocking terminal; S3 never begins.
    with pytest.MonkeyPatch.context() as patch:
        inject_blocking_reduction(patch, cm)
        with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
            cm.run_successor_multipass_final(r19.production_request(estate))
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    assert semantic_refusals(estate) == ["semantic-refusal-S3-attempt-000.json"]
    assert s3_statements(statements) == []
    assert not any(p.name.startswith("stage-003-S3") for p in estate.receipt_root.iterdir())
    record = json.loads(
        (estate.receipt_root / "semantic-refusal-S3-attempt-000.json").read_text(encoding="utf-8")
    )
    assert record["contract"] == cm.L2_SEMANTIC_REFUSAL_CONTRACT
    assert record["reduced_run"]["outcome"] == "failed"
    assert record["reduced_run"]["parser_state"] == "failed"
    assert record["s3_statements_begun"] == 0 and record["refused_stage_id"] == "S3"
    # Resume from the committed S2: refused again, a second record, still no S3 statement.
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        cm.run_successor_multipass_final(r19.production_request(estate))
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    assert semantic_refusals(estate) == [
        "semantic-refusal-S3-attempt-000.json",
        "semantic-refusal-S3-attempt-001.json",
    ]
    assert s3_statements(statements) == []
    # The S2 world is preserved; its committed witness authenticates as an AUTHENTIC blocking
    # terminal (not a conflict), and no continuation is possible from it.
    with readonly(estate.catalog) as connection:
        row = connection.execute("SELECT outcome FROM census_parser_runs").fetchone()
    assert str(row["outcome"]) == "failed"


def test_p30_a_crash_between_the_s2_commit_and_its_receipt_cannot_continue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    statements: list[str] = []
    r19.install_trace(monkeypatch, statements)
    with pytest.MonkeyPatch.context() as patch:
        inject_blocking_reduction(patch, cm)
        _raise_once(
            patch,
            "_seal_stage",
            when=lambda session, ctx, stage, unit, **kw: stage.stage_id == "S2",
        )
        with pytest.raises(RuntimeError, match="_seal_stage"):
            cm.run_successor_multipass_final(r19.production_request(estate))
    # S2 is committed and receipt-pending; the resume converges the receipt and then refuses.
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    assert not any(p.name.startswith("stage-002-S2") for p in estate.receipt_root.iterdir())
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        cm.run_successor_multipass_final(r19.production_request(estate))
    assert any(p.name.startswith("stage-002-S2") for p in estate.receipt_root.iterdir())
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    assert semantic_refusals(estate) == ["semantic-refusal-S3-attempt-000.json"]
    assert s3_statements(statements) == []


def test_p17_p21_a_non_blocking_s2_continues_and_resumes(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    witness = json.loads(str(r19.applied_units(estate.catalog)[-1]["outcome_witness_json"]))
    assert witness["blocking_structural"] == 0 and witness["parser_state"] == "completed"
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached
    assert r19.stage_ids(estate.catalog) == list(r19.PRODUCTION_STAGE_IDS_10)
    assert semantic_refusals(estate) == []


def test_p18_s19_is_unchanged() -> None:
    assert frozenset({"failed"}) == canary.BLOCKING_PARSER_STATES
    assert (
        frozenset({"E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"}) == canary.BLOCKING_SOURCE_DISPOSITIONS
    )
    source = inspect.getsource(cm._stage_outcome)
    assert source.index("_derived_outcome(ctx, units)") < source.index(
        "require_f0_success(outcome)"
    )
    gate = inspect.getsource(canary.require_f0_success)
    assert "BLOCKING_PARSER_STATES" in gate and "BLOCKING_SOURCE_DISPOSITIONS" in gate
    assert cm._KIND_OUTCOME == "derive_outcome_and_require_f0_success"

    def outcome(state: str, disposition: str = "E0_REQUIRED_PARSE") -> SingleSourceOutcome:
        return SingleSourceOutcome(
            outcome=PlannedSourceOutcome(
                source_instance_id=c1.INSTANCE,
                source_id=c1.SOURCE_ID,
                disposition=disposition,  # type: ignore[arg-type]
                parser_state_before="not_started",
                parser_state_after=state,
            ),
            observation=None,
        )

    assert canary.require_f0_success(outcome("quarantined")).outcome.parser_state_after == (
        "quarantined"
    )
    assert canary.require_f0_success(outcome("completed")).outcome.parser_state_after == "completed"
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        canary.require_f0_success(outcome("failed"))
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        canary.require_f0_success(outcome("completed", "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"))


def test_p26_a_name_only_quarantine_is_non_blocking_through_chunk_level_one_and_s2(
    tmp_path: Path,
) -> None:
    database, tree = custom_world(tmp_path, members_with({4: blank_name}))
    estate = estate_from_world(tmp_path, database, tree)
    # Chunk: quarantined, not failed.
    inputs = cc.resolve_chunk_inputs(estate.run["plan"], internal_root=estate.run["chunk_root"])
    by_id = {item.chunk_id: cc.chunk_semantics(item) for item in inputs}
    assert by_id["chunk-0003"].run_outcome == "completed_with_quarantine"
    assert by_id["chunk-0003"].parser_state == "quarantined"
    assert by_id["chunk-0003"].quarantined == 1 and not by_id["chunk-0003"].blocking
    # Level 1: admitted, and the receipt says exactly that.
    assert any(
        item.observed_run_outcome == "completed_with_quarantine" and item.observed_quarantined == 1
        for item in estate.succ["intermediates"]
    )
    # Level 2: S2 is quarantined, S3 begins, S19 passes, the terminal exists, no refusal record.
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached and outcome.final_receipt is not None
    assert outcome.final_receipt["run_outcome"] == "completed_with_quarantine"
    assert outcome.final_receipt["parser_state_after"] == "quarantined"
    assert outcome.final_receipt["quarantined_records"] == 1
    assert semantic_refusals(estate) == []
    units = {
        str(row["stage_id"]): json.loads(str(row["outcome_witness_json"]))
        for row in r19.applied_units(estate.catalog)
    }
    assert units["S2"]["outcome"] == "completed_with_quarantine"
    assert units["S2"]["quarantined"] == 1 and units["S2"]["blocking_structural"] == 0
    assert units["S19"]["f0_success"] is True and units["S19"]["quarantined_records"] == 1


# ==========================================================================
# RESTARTABILITY / STATUS -- proofs 19-22 and 31
# ==========================================================================
def test_p19_the_committed_reduced_run_witness_is_re_derived_on_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    calls: list[str] = []
    original = cm._verify_reduced_run_witness

    def counted(connection: Any, ctx: Any, witness: Any) -> None:
        calls.append(str(witness["parser_run_id"]))
        original(connection, ctx, witness)

    monkeypatch.setattr(cm, "_verify_reduced_run_witness", counted)
    statements: list[str] = []
    r19.install_trace(monkeypatch, statements)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    assert calls, "the S2 witness was not re-derived on resume"
    assert any("FROM main.census_parser_runs WHERE parser_run_id = " in s for s in statements)
    expected = _stable_id(
        "parser-run",
        c1.OBSERVATION,
        estate.run["receipts"][0].execution_contract.parser_id,
        estate.run["receipts"][0].execution_contract.parser_version,
    )
    assert set(calls) == {expected}
    assert r19.stage_ids(estate.catalog)[-1] == "S3"


def _tamper(estate: r19.SuccessorWorld, sql: str, params: tuple[object, ...]) -> None:
    connection = r19.writer(estate.catalog)
    try:
        connection.execute(sql, params)
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        connection.close()


def test_p20_p31_tampered_or_inconsistent_witnesses_conflict_on_resume(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    connection = r19.writer(estate.catalog)
    try:
        original = dict(connection.execute("SELECT * FROM census_parser_runs").fetchone())
        unit = dict(
            connection.execute(
                f"SELECT * FROM main.{cm.L2_APPLIED_UNITS_TABLE} WHERE stage_id = 'S2'"  # noqa: S608
            ).fetchone()
        )
    finally:
        connection.close()
    columns = ", ".join(original)
    placeholders = ", ".join("?" for _ in original)
    summary = json.loads(str(original["summary_json"]))
    tampered_summary = json.loads(json.dumps(summary))
    tampered_summary["structural_detail"]["blocking"] = 1
    tampered_summary["counts"]["structural_failures"] = 1
    duplicates_summary = json.loads(json.dumps(summary))
    duplicates_summary["duplicate_identities"] = [["accession:forged", 2]]
    runs = "UPDATE census_parser_runs SET "
    units_table = f"UPDATE main.{cm.L2_APPLIED_UNITS_TABLE} SET "  # noqa: S608
    forged_witness = json.dumps({**json.loads(str(unit["outcome_witness_json"])), "parsed": 999})
    forged_counts = json.dumps({**summary, "counts": {**summary["counts"], "parsed": 999}})
    cases: list[tuple[str, str, tuple[object, ...], str]] = [
        ("parsed count", runs + "parsed_count = parsed_count + 1", (), "row counts"),
        ("quarantined count", runs + "quarantined_count = 3", (), "row counts"),
        ("outcome", runs + "outcome = 'completed_with_quarantine'", (), "records outcome"),
        (
            "parser version",
            runs + "parser_version = 'submissions-json/9.9'",
            (),
            "other than the authenticated contract",
        ),
        ("parser id", runs + "parser_id = 'forged'", (), "other than the authenticated contract"),
        (
            "source observation",
            runs + "source_observation_id = 'obs-other'",
            (),
            "other than the authenticated contract",
        ),
        (
            "blocking count",
            runs + "summary_json = ?",
            (json.dumps(tampered_summary),),
            "blocking structural",
        ),
        (
            "duplicate identities",
            runs + "summary_json = ?",
            (json.dumps(duplicates_summary),),
            "duplicate identities",
        ),
        ("summary counts", runs + "summary_json = ?", (forged_counts,), "summary counts disagree"),
        ("missing row", "DELETE FROM census_parser_runs", (), "0 census_parser_runs rows"),
        (
            "witness identity",
            units_table + "outcome_witness_json = ? WHERE stage_id = 'S2'",
            (forged_witness,),
            "carries identity",
        ),
    ]
    for label, sql, params, match in cases:
        _tamper(estate, sql, params)
        with pytest.raises(cm.ChunkMultipassError, match=match):
            cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
        assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"], label
        # Restore exactly, then prove the authentic witness resumes past the check.
        _tamper(estate, "DELETE FROM census_parser_runs", ())
        _tamper(
            estate,
            f"INSERT INTO census_parser_runs ({columns}) VALUES ({placeholders})",  # noqa: S608
            tuple(original.values()),
        )
        _tamper(
            estate,
            f"UPDATE main.{cm.L2_APPLIED_UNITS_TABLE} SET outcome_witness_json = ? "  # noqa: S608
            "WHERE stage_id = 'S2'",
            (unit["outcome_witness_json"],),
        )
    # A witness that records no blocking count is unverifiable, never zero.
    witness = json.loads(str(unit["outcome_witness_json"]))
    del witness["blocking_structural"]
    with pytest.raises(cm.ChunkMultipassError, match="blocking_structural"):
        cm._reduced_run_from_witness(witness)
    # The authentic non-blocking witness resumes and completes (21).
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached


def test_p31_the_published_s19_counts_are_held_to_the_re_derived_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    assert cm.run_successor_multipass_final(r19.production_request(estate)).terminal_reached
    original = cm._derived_outcome

    def moved(ctx: Any, units: Any) -> Any:
        derived = original(ctx, units)
        return replace(
            derived,
            outcome=replace(derived.outcome, parsed_records=derived.outcome.parsed_records + 1),
        )

    monkeypatch.setattr(cm, "_derived_outcome", moved)
    with pytest.raises(cm.ChunkMultipassError, match="does not re-derive.*parsed_records"):
        cm.run_successor_multipass_final(r19.production_request(estate))


def test_p22_artifact_status_complete_is_never_the_success_predicate(tmp_path: Path) -> None:
    database, tree = custom_world(tmp_path, members_with({5: null_recent}))
    run = production_run(tmp_path, database, tree)
    failed = ce.completed_chunk_receipt(run["chunk_root"], "chunk-0004")
    assert failed is not None and failed[0].status == "complete"
    (item,) = cc.resolve_contiguous_chunk_inputs(
        run["plan"], ("chunk-0004",), internal_root=run["chunk_root"]
    )
    assert cc.chunk_semantics(item).blocking
    with pytest.raises(cc.ChunkConsolidationError, match="artifact completion, not parser success"):
        cc.require_admissible_chunk_semantics((item,))
    # A receipt whose SUMMARY contradicts its manifest-bound row is refused as well: the receipt
    # is a claim, the row is the evidence.
    forged = replace(
        item,
        receipt=replace(
            item.receipt, summary=replace(item.receipt.summary, run_outcome="completed")
        ),
    )
    with pytest.raises(cc.ChunkConsolidationError, match="contradicts the evidence it binds"):
        cc.chunk_semantics(forged)
    # And a complete /2 intermediate with blocking observed semantics is refused by admission.
    healthy_database, healthy_tree = c1.build_world(
        tmp_path / "healthy", members=9, filings=2, shards=1
    )
    healthy_run = production_run(tmp_path / "healthy", healthy_database, healthy_tree)
    partial = c13.merge_in_process(healthy_run, healthy_database, finalize=False)
    receipt = partial["intermediates"][0]
    blocking = replace(
        receipt,
        observed_run_outcome="failed",
        observed_blocking_structural=2,
        inputs_reached_blocking_terminal=True,
    )
    assert blocking.status == "complete" and blocking.blocking
    with pytest.raises(cm.ChunkMultipassError, match="BLOCKING reduced run"):
        cm.require_admissible_intermediate_semantics(blocking)
    assert "artifact completion" in (cm.IntermediateReceipt.__doc__ or "")
    assert "artifact completion" in (cc.__doc__ or "")


# ==========================================================================
# CONTRACT / PROVENANCE -- proofs 27, 28, 32, 33 and 34
# ==========================================================================
def test_p27_a_slash_two_receipt_round_trips_and_refuses_incomplete_or_contradictory_evidence(
    tmp_path: Path,
) -> None:
    database, tree = c1.build_world(tmp_path, members=9, filings=2, shards=1)
    run = production_run(tmp_path, database, tree)
    partial = c13.merge_in_process(run, database, finalize=False)
    receipt = partial["intermediates"][0]
    record = dict(receipt.as_record())
    assert cm.IntermediateReceipt.from_record(record) == receipt
    for key in cm._OBSERVED_SEMANTICS_KEYS:
        without = {k: v for k, v in record.items() if k != key}
        with pytest.raises(cm.ChunkMultipassError, match="missing"):
            cm.IntermediateReceipt.from_record(without)
    with pytest.raises(cm.ChunkMultipassError, match="not an integer|is refused"):
        cm.IntermediateReceipt.from_record({**record, "observed_quarantined": "x"})
    with pytest.raises(cm.ChunkMultipassError, match="bool is required"):
        cm.IntermediateReceipt.from_record({**record, "inputs_reached_blocking_terminal": 1})
    contradictory: list[dict[str, Any]] = [
        {"observed_run_outcome": "failed"},
        {"observed_blocking_structural": 3},
        {"inputs_reached_blocking_terminal": True},
        {"observed_run_outcome": "completed_with_quarantine"},
        {"observed_run_outcome": "done"},
        {"observed_quarantined": -1},
    ]
    for change in contradictory:
        with pytest.raises(
            cm.ChunkMultipassError, match="contradictory|outside the accepted|negative"
        ):
            cm.IntermediateReceipt.from_record({**record, **change})
    # A consistent quarantined receipt is admissible; a consistent failed one is not.
    quarantined = cm.IntermediateReceipt.from_record(
        {**record, "observed_run_outcome": "completed_with_quarantine", "observed_quarantined": 2}
    )
    assert cm.require_admissible_intermediate_semantics(quarantined) == "quarantined"
    failed = cm.IntermediateReceipt.from_record(
        {
            **record,
            "observed_run_outcome": "failed",
            "observed_blocking_structural": 1,
            "inputs_reached_blocking_terminal": True,
        }
    )
    with pytest.raises(cm.ChunkMultipassError, match="BLOCKING reduced run"):
        cm.require_admissible_intermediate_semantics(failed)


def test_p28_a_slash_one_receipt_is_forensic_only_and_writes_nothing(tmp_path: Path) -> None:
    database, tree = c1.build_world(tmp_path, members=9, filings=2, shards=1)
    run = production_run(tmp_path, database, tree)
    partial = c13.merge_in_process(run, database, finalize=False)
    receipt = partial["intermediates"][0]
    legacy_record = {
        k: v for k, v in receipt.as_record().items() if k not in cm._OBSERVED_SEMANTICS_KEYS
    }
    legacy_record["contract"] = cm.LEGACY_INTERMEDIATE_RECEIPT_CONTRACT
    root = tmp_path / "legacy-intermediates"
    directory = root / "group-0000" / "attempt-000"
    directory.mkdir(parents=True)
    path = directory / cm.INTERMEDIATE_RECEIPT_FILENAME
    write_once_json(path, legacy_record)
    listing = sorted(p.name for p in directory.iterdir())
    legacy = cm.read_legacy_intermediate_receipt(path)
    assert sorted(p.name for p in directory.iterdir()) == listing
    assert legacy.contract == "m3.3-chunked-f0-intermediate-receipt/1"
    assert legacy.witness_ledger_identity == receipt.witness_ledger_identity
    assert legacy.group_id == "group-0000" and legacy.status == "complete"
    assert legacy.document_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert type(legacy) is cm.LegacyIntermediateReceipt
    for key in cm._OBSERVED_SEMANTICS_KEYS:
        assert not hasattr(legacy, key) and key not in legacy.record
    # Every ordinary reader refuses the /1 document, loudly.
    with pytest.raises(cm.ChunkMultipassError, match="does not verify"):
        cm.completed_intermediate_receipt(root, "group-0000")
    with pytest.raises(cm.ChunkMultipassError, match="missing"):
        cm.IntermediateReceipt.from_record(legacy_record)
    with pytest.raises(cm.ChunkMultipassError, match="does not verify"):
        cm.resolve_intermediate_inputs(run["plan"], partial["schedule"], intermediates_root=root)
    # The legacy reader refuses a /2 document and a /1 document that smuggles /2 keys.
    real = partial["intermediates_root"] / "group-0000" / f"attempt-{receipt.attempt:03d}"
    with pytest.raises(ChunkEvidenceError, match="carries contract"):
        cm.read_legacy_intermediate_receipt(real / cm.INTERMEDIATE_RECEIPT_FILENAME)
    smuggled = directory.parent / "attempt-001"
    smuggled.mkdir()
    write_once_json(
        smuggled / cm.INTERMEDIATE_RECEIPT_FILENAME,
        {**legacy_record, "observed_run_outcome": "completed"},
    )
    with pytest.raises(cm.ChunkMultipassError, match="no /1 writer produced"):
        cm.read_legacy_intermediate_receipt(smuggled / cm.INTERMEDIATE_RECEIPT_FILENAME)
    # An unknown version never enters admission either.
    alien = replace(receipt, contract="m3.3-chunked-f0-intermediate-receipt/9")
    with pytest.raises(cm.ChunkMultipassError, match="carries contract"):
        cm.require_admissible_intermediate_semantics(alien)


def test_p32_p33_the_alien_fixture_and_the_two_current_contract_pins_moved() -> None:
    here = Path(__file__).parent
    charge = (here / "test_d151_r19_storage_charge.py").read_text(encoding="utf-8")
    assert 'contract="m3.3-chunked-f0-intermediate-receipt/3"' in charge
    assert 'contract="m3.3-chunked-f0-intermediate-receipt/2"' not in charge
    for name in ("test_d151_c13_multipass_plan.py", "test_d151_c19_corrections.py"):
        source = (here / name).read_text(encoding="utf-8")
        assert (
            'assert cm.INTERMEDIATE_RECEIPT_CONTRACT == "m3.3-chunked-f0-intermediate-receipt/2"'
            in source
        )
        assert (
            'assert cm.INTERMEDIATE_RECEIPT_CONTRACT == "m3.3-chunked-f0-intermediate-receipt/1"'
            not in source
        )
    assert cm.INTERMEDIATE_RECEIPT_CONTRACT == "m3.3-chunked-f0-intermediate-receipt/2"
    assert cm.LEGACY_INTERMEDIATE_RECEIPT_CONTRACT == "m3.3-chunked-f0-intermediate-receipt/1"
    assert "/3" not in cm.INTERMEDIATE_RECEIPT_CONTRACT
    assert not hasattr(cm, "INTERMEDIATE_RECEIPT_CONTRACT_V3")


def _ledger_identity(witness_path: Path, contract: str, group_id: str) -> str:
    digest = hashlib.sha256()
    digest.update(f"{contract}\x1f{group_id}".encode())
    digest.update(b"\x1e")
    with readonly(witness_path) as connection:
        for row in connection.execute(
            "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "
            "FROM chunk_first_witness ORDER BY native_identity"
        ):
            digest.update("\x1f".join(str(value) for value in row).encode("utf-8"))
            digest.update(b"\x1e")
    return digest.hexdigest()


def test_p34_the_witness_ledger_identity_moved_with_the_contract_and_by_exactly_the_contract(
    tmp_path: Path,
) -> None:
    database, tree = c1.build_world(tmp_path, members=9, filings=2, shards=1)
    run = production_run(tmp_path, database, tree)
    partial = c13.merge_in_process(run, database, finalize=False)
    for group, receipt in zip(partial["schedule"].groups, partial["intermediates"], strict=True):
        witness = (
            partial["intermediates_root"]
            / group.group_id
            / f"attempt-{receipt.attempt:03d}"
            / cm.INTERMEDIATE_WITNESS_FILENAME
        )
        two = _ledger_identity(witness, cm.INTERMEDIATE_RECEIPT_CONTRACT, group.group_id)
        one = _ledger_identity(witness, cm.LEGACY_INTERMEDIATE_RECEIPT_CONTRACT, group.group_id)
        assert receipt.witness_ledger_identity == two != one
        # Deterministic: the same rows fold to the same identity every time, under either literal.
        assert _ledger_identity(witness, cm.INTERMEDIATE_RECEIPT_CONTRACT, group.group_id) == two
        assert (
            _ledger_identity(witness, cm.LEGACY_INTERMEDIATE_RECEIPT_CONTRACT, group.group_id)
            == one
        )
    # The fold is the accepted one: the contract literal is the ONLY input that moved.
    assert 'digest.update(f"{INTERMEDIATE_RECEIPT_CONTRACT}\\x1f{group.group_id}".encode())' in (
        inspect.getsource(cm._merge_group_evidence)
    )
    # A historical /1 document keeps its recorded /1 identity verbatim through the legacy reader.
    first = partial["intermediates"][0]
    legacy_record = {
        k: v for k, v in first.as_record().items() if k not in cm._OBSERVED_SEMANTICS_KEYS
    }
    legacy_record["contract"] = cm.LEGACY_INTERMEDIATE_RECEIPT_CONTRACT
    legacy_record["witness_ledger_identity"] = "1" * 64
    path = tmp_path / "historical-receipt.json"
    write_once_json(path, legacy_record)
    assert cm.read_legacy_intermediate_receipt(path).witness_ledger_identity == "1" * 64


# ==========================================================================
# D151-C31R2 CORRECTION PASS -- MINOR-2 (URI-safe reader) and MINOR-3 (durable counts)
#
# Bounded regressions over the REAL chunk_semantics connection/query path. Nothing here
# monkeypatches SQLite connection creation: the point is precisely that the URI the module
# builds is parsed by SQLite as the module intends.
# ==========================================================================
#: Exactly the columns the reader SELECTs. A test-owned catalog needs no others.
_SEMANTICS_COLUMNS = (
    "parser_run_id",
    "source_observation_id",
    "parser_id",
    "parser_version",
    "parsed_count",
    "quarantined_count",
    "outcome",
    "summary_json",
)
_CREATE_LOOSE_RUNS = (
    "CREATE TABLE census_parser_runs("
    "parser_run_id, source_observation_id, parser_id, parser_version, "
    "parsed_count, quarantined_count, outcome, summary_json)"
)
_INSERT_LOOSE_RUN = (
    "INSERT INTO census_parser_runs("
    "parser_run_id, source_observation_id, parser_id, parser_version, "
    "parsed_count, quarantined_count, outcome, summary_json) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)
#: The URI-significant directory names, and the combined case.
URI_SIGNIFICANT = ("q?mark", "h#ash", "both?q#h")


class _ValueRow:
    """A minimal ``row[column]`` stand-in for values SQLite itself can never return.

    SQLite stores a bound Python ``bool`` as integer ``0``/``1`` and hands an ordinary ``int``
    back, so a database fixture cannot present a boolean to the validator at all. This carries
    the value verbatim so the pre-conversion branches are exercised where such a value could
    actually arrive -- in-process, at the validator boundary.
    """

    def __init__(self, **values: Any) -> None:
        self._values = values

    def __getitem__(self, column: str) -> Any:
        try:
            return self._values[column]
        except KeyError:
            message = "No item with that key"
            raise IndexError(message) from None


def truncated_uri_path(catalog: Path) -> Path:
    """Where the OLD raw ``file:{path}?immutable=1`` f-string actually pointed.

    SQLite ends the URI path at the first '?' or '#', so a catalog under a directory carrying
    either character resolved to a SHORTER path -- and opened whatever was sitting there.
    """
    raw = str(catalog.resolve())
    cut = min((raw.index(c) for c in "?#" if c in raw), default=len(raw))
    return Path(raw[:cut])


def plant_decoy(path: Path, marker: str) -> None:
    """A complete, VALID-looking parser-run row at the truncated path -- a different answer."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute(_CREATE_LOOSE_RUNS)
        connection.execute(
            _INSERT_LOOSE_RUN,
            (marker, marker, marker, marker, 999_999, 999_999, "completed", "{}"),
        )
        connection.commit()
    finally:
        connection.close()


def semantics_row(catalog: Path, observation: str) -> dict[str, Any]:
    """The chunk's own parser-run row, as a plain mapping."""
    connection = readonly(catalog)
    try:
        row = connection.execute(
            "SELECT parser_run_id, source_observation_id, parser_id, parser_version, "
            "parsed_count, quarantined_count, outcome, summary_json FROM census_parser_runs "
            "WHERE source_observation_id = ?",
            (observation,),
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    return {column: row[column] for column in _SEMANTICS_COLUMNS}


def owned_catalog(directory: Path, fields: dict[str, Any], **overrides: Any) -> Path:
    """A SYNTHETIC, test-owned catalog carrying ``fields``, with ``overrides`` applied.

    ``0003_census_catalog.sql`` declares ``census_parser_runs`` STRICT with
    ``INTEGER NOT NULL CHECK(count >= 0)`` on both counts, so a malformed count cannot be
    inserted into a production schema at all -- and an INSERT that schema rejects would prove
    nothing about the READER. This table is deliberately constraint-free, in test-owned
    temporary space, so the value under test is the value the reader is actually handed. No
    production migration and no estate schema is touched.
    """
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / WORKING_CATALOG_FILENAME
    values = dict(fields)
    values.update(overrides)
    connection = sqlite3.connect(target)
    try:
        connection.execute(_CREATE_LOOSE_RUNS)
        connection.execute(_INSERT_LOOSE_RUN, tuple(values[c] for c in _SEMANTICS_COLUMNS))
        connection.commit()
    finally:
        connection.close()
    return target


def sidecars(directory: Path) -> list[str]:
    return sorted(
        p.name
        for p in directory.rglob("*")
        if p.name.endswith(("-wal", "-shm", "-journal", ".db-wal", ".db-shm"))
    )


def tree_hashes(directory: Path) -> dict[str, str]:
    return {
        str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def test_c31r2_minor2_the_immutable_reader_addresses_uri_significant_directories(
    tmp_path: Path,
) -> None:
    """MINOR-2: '?' and '#' in a directory name address the chunk's OWN catalog, not a decoy.

    The old raw ``file:{path}?immutable=1`` construction did not fail on such a path -- it
    silently SUCCEEDED against a shorter one. Each case below plants a valid-looking decoy at
    exactly that shorter path, so a regression is a wrong answer rather than an error.
    """
    database, tree = c1.build_world(tmp_path / "world", members=9, filings=2, shards=1)
    run = production_run(tmp_path / "world", database, tree)
    (item,) = cc.resolve_contiguous_chunk_inputs(
        run["plan"], ("chunk-0000",), internal_root=run["chunk_root"]
    )
    expected = cc.chunk_semantics(item)
    assert not expected.blocking

    for index, name in enumerate(URI_SIGNIFICANT):
        base = tmp_path / f"special-{index}"
        base.mkdir()
        special = base / name
        shutil.copytree(item.directory, special)
        bound = replace(item, directory=special)
        decoy_at = truncated_uri_path(bound.catalog_path)
        assert decoy_at != bound.catalog_path.resolve()
        plant_decoy(decoy_at, f"decoy-{index}")

        # The defect, demonstrated: the OLD construction reads the DECOY and reports success.
        legacy = sqlite3.connect(f"file:{bound.catalog_path.resolve()}?immutable=1", uri=True)
        try:
            legacy.row_factory = sqlite3.Row
            stolen = legacy.execute("SELECT parser_run_id FROM census_parser_runs").fetchone()
        finally:
            legacy.close()
        assert stolen["parser_run_id"] == f"decoy-{index}"

        # The correction: the real reader resolves to the intended database and its exact row.
        before = tree_hashes(special)
        observed = cc.chunk_semantics(bound)
        assert observed == expected
        assert observed.parser_run_id != f"decoy-{index}"
        assert observed.parsed == expected.parsed and observed.quarantined == expected.quarantined
        # Admission over the same input is unchanged at the special path.
        assert cc.require_admissible_chunk_semantics((bound,)) == (expected,)
        # ``immutable=1`` holds: no sidecar appeared and every input byte is unchanged.
        assert sidecars(special) == []
        assert tree_hashes(special) == before


def test_c31r2_minor2_an_unreadable_catalog_refuses_through_this_module_error(
    tmp_path: Path,
) -> None:
    """MINOR-2: every catalog-level failure becomes ChunkConsolidationError, with its cause.

    Also proves the SEMANTIC refusals are unchanged at a URI-significant path: the reader
    reaching the right row is what makes the normal blocking refusal fire there.
    """
    database, tree = custom_world(tmp_path / "world", members_with({5: null_recent}))
    run = production_run(tmp_path / "world", database, tree)
    (blocking,) = cc.resolve_contiguous_chunk_inputs(
        run["plan"], ("chunk-0004",), internal_root=run["chunk_root"]
    )
    special = tmp_path / "semantic" / "chunk?0004#x"
    special.parent.mkdir(parents=True)
    shutil.copytree(blocking.directory, special)
    bound = replace(blocking, directory=special)
    assert cc.chunk_semantics(bound).blocking
    with pytest.raises(cc.ChunkConsolidationError, match="artifact completion, not parser success"):
        cc.require_admissible_chunk_semantics((bound,))

    healthy = tmp_path / "healthy"
    healthy.mkdir()

    # 1. The catalog is absent: the failure is at connect, and it is translated.
    missing = replace(blocking, directory=healthy / "absent?q")
    with pytest.raises(cc.ChunkConsolidationError, match="could not be opened read-only") as one:
        cc.chunk_semantics(missing)
    assert isinstance(one.value.__cause__, sqlite3.Error)
    assert not isinstance(one.value, sqlite3.Error)

    # 2. The file exists but is not a database: the failure is at the query, and it is translated.
    garbage = healthy / "garbage#h"
    garbage.mkdir()
    (garbage / WORKING_CATALOG_FILENAME).write_bytes(b"this is not a SQLite database\n")
    with pytest.raises(cc.ChunkConsolidationError, match="could not be read for its parser-run"):
        cc.chunk_semantics(replace(blocking, directory=garbage))

    # 3. A real database with no census_parser_runs at all fails closed the same way.
    empty = healthy / "empty?d"
    empty.mkdir()
    connection = sqlite3.connect(empty / WORKING_CATALOG_FILENAME)
    connection.execute("CREATE TABLE unrelated(v)")
    connection.commit()
    connection.close()
    with pytest.raises(cc.ChunkConsolidationError, match="could not be read for its parser-run"):
        cc.chunk_semantics(replace(blocking, directory=empty))

    # 4. Missing COLUMN evidence fails closed too -- never defaulted, never read as zero.
    partial = healthy / "partial"
    partial.mkdir()
    connection = sqlite3.connect(partial / WORKING_CATALOG_FILENAME)
    connection.execute("CREATE TABLE census_parser_runs(parser_run_id, source_observation_id)")
    connection.commit()
    connection.close()
    with pytest.raises(cc.ChunkConsolidationError, match="could not be read for its parser-run"):
        cc.chunk_semantics(replace(blocking, directory=partial))


def test_c31r2_minor3_durable_counts_are_validated_fail_closed(tmp_path: Path) -> None:
    """MINOR-3: parsed_count / quarantined_count are proved nonnegative integers, or refused.

    The malformed fixtures keep VALID identity, parser, outcome, summary and receipt context, so
    the count check is the predicate actually reached -- an insertion, checksum or wrong-row
    failure would prove nothing.
    """
    database, tree = c1.build_world(tmp_path / "world", members=9, filings=2, shards=1)
    run = production_run(tmp_path / "world", database, tree)
    (item,) = cc.resolve_contiguous_chunk_inputs(
        run["plan"], ("chunk-0000",), internal_root=run["chunk_root"]
    )
    truth = cc.chunk_semantics(item)
    fields = semantics_row(item.catalog_path, item.receipt.source_observation_id)
    assert fields["outcome"] == "completed" and fields["quarantined_count"] == 0

    def bound(label: str, **overrides: Any) -> Any:
        directory = tmp_path / "synthetic" / label
        owned_catalog(directory, fields, **overrides)
        return replace(item, directory=directory)

    # The synthetic reader path is faithful: unmodified, it re-derives the real semantics.
    assert cc.chunk_semantics(bound("control")) == truth

    for column in ("parsed_count", "quarantined_count"):
        for label, value in (
            ("null", None),
            ("text", "12"),
            ("negative", -1),
            ("fraction", 1.5),
        ):
            candidate = bound(f"{column}-{label}", **{column: value})
            with pytest.raises(cc.ChunkConsolidationError) as excinfo:
                cc.chunk_semantics(candidate)
            message = str(excinfo.value)
            assert column in message
            assert "nonnegative integer count" in message
            assert "durable" in message

    # A bound Python bool is stored as an ordinary integer, so the DATABASE cannot present one.
    # Recorded as the real limitation it is, and proved where such a value could arrive instead.
    stored = semantics_row(
        owned_catalog(tmp_path / "synthetic" / "bool-probe", fields, parsed_count=True),
        str(fields["source_observation_id"]),
    )
    assert stored["parsed_count"] == 1 and not isinstance(stored["parsed_count"], bool)
    for column in ("parsed_count", "quarantined_count"):
        with pytest.raises(cc.ChunkConsolidationError, match="nonnegative integer count"):
            cc._row_count(cast(sqlite3.Row, _ValueRow(**{column: True})), column, label="chunk 'x'")
        with pytest.raises(cc.ChunkConsolidationError, match="carries no"):
            cc._row_count(cast(sqlite3.Row, _ValueRow()), column, label="chunk 'x'")
        assert cc._row_count(cast(sqlite3.Row, _ValueRow(**{column: 0})), column, label="l") == 0

    # POSITIVE CONTROLS, through the real reader.
    # (a) the zero boundary on both counts, with the outcome that describes it;
    zero = replace(
        item,
        receipt=replace(
            item.receipt,
            summary=replace(
                item.receipt.summary,
                run_outcome="completed",
                parsed_records=0,
                quarantined_records=0,
            ),
        ),
        directory=tmp_path / "synthetic" / "zero",
    )
    owned_catalog(zero.directory, fields, parsed_count=0, quarantined_count=0)
    assert cc.chunk_semantics(zero).parsed == 0
    assert cc.chunk_semantics(zero).quarantined == 0
    assert not cc.chunk_semantics(zero).blocking

    # (b) an ordinary successful row with a valid POSITIVE parsed_count;
    assert truth.parsed > 0 and truth.run_outcome == "completed"

    # (c) a positive quarantined_count with completed_with_quarantine, still NON-blocking.
    quarantined = replace(
        item,
        receipt=replace(
            item.receipt,
            summary=replace(
                item.receipt.summary,
                run_outcome="completed_with_quarantine",
                quarantined_records=3,
            ),
        ),
        directory=tmp_path / "synthetic" / "quarantined",
    )
    owned_catalog(
        quarantined.directory, fields, quarantined_count=3, outcome="completed_with_quarantine"
    )
    observed = cc.chunk_semantics(quarantined)
    assert observed.quarantined == 3
    assert observed.run_outcome == "completed_with_quarantine"
    assert not observed.blocking
    assert cc.require_admissible_chunk_semantics((quarantined,)) == (observed,)
