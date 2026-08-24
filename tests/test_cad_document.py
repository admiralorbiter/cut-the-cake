"""Tests for CADDocument Schema, Model, & General Analysis [Milestone 2B].

Verifies:
1. JSON Schema validation (cad_document_v1).
2. CADDocument <-> GeometricModule conversion round-trip parity.
3. Canonical F1 document baseline analysis parity.
4. Custom 3-threat corridor document analysis without fixture assumptions.
5. Generic 2D obstacle translation (X and Y directions).
6. CADDocument stores zero calculated metrics.
7. Fast analysis semantics (source_schedule_feasible, null realized_service_complete_tic).
8. Full committed telemetry populates realized completions from actual events.
9. Flask document session REST endpoints.
"""

import json
import os
import sys
import pytest

# Compatibility patch for PySide6/shiboken meta_path inspection on Python 3.12
try:
    import six
    for imp in sys.meta_path:
        if not hasattr(imp, "_path"):
            try:
                imp._path = None
            except Exception:
                pass
except Exception:
    pass

from jsonschema.validators import Draft7Validator

from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPort,
    CADPlayerModel,
    get_canonical_f1_document,
    get_custom_asymmetric_corridor_document
)
from cut_the_cake.cad_adapter import (
    analyze_cad_document,
    translate_obstacle_in_document
)
from cut_the_cake.cad_server import create_cad_app


@pytest.fixture
def cad_doc_schema():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    schema_path = os.path.join(repo_root, "cad", "schema", "cad_document_v1.schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_cad_document_schema_validation(cad_doc_schema):
    """Canonical and custom CAD documents must strictly validate against cad_document_v1 schema."""
    validator = Draft7Validator(cad_doc_schema)

    doc_f1 = get_canonical_f1_document().to_dict()
    errors_f1 = list(validator.iter_errors(doc_f1))
    assert len(errors_f1) == 0, f"F1 Schema Errors: {[e.message for e in errors_f1]}"

    doc_custom = get_custom_asymmetric_corridor_document().to_dict()
    errors_custom = list(validator.iter_errors(doc_custom))
    assert len(errors_custom) == 0, f"Custom Schema Errors: {[e.message for e in errors_custom]}"


def test_cad_document_roundtrip():
    """CADDocument must serialize to dict and convert to GeometricModule and back with zero loss."""
    doc_orig = get_custom_asymmetric_corridor_document()
    d_dict = doc_orig.to_dict()
    doc_from_dict = CADDocument.from_dict(d_dict)

    assert doc_from_dict.document_id == doc_orig.document_id
    assert len(doc_from_dict.obstacles) == len(doc_orig.obstacles)
    assert len(doc_from_dict.threats) == 3
    assert len(doc_from_dict.routes) == 1

    # Convert to GeometricModule
    geo_mod = doc_from_dict.to_geometric_module()
    assert len(geo_mod.obstacles) == 2
    assert len(geo_mod.threats) == 3

    # Reconstruct CADDocument
    doc_reconstructed = CADDocument.from_geometric_module(geo_mod, document_id="reconstructed_corridor")
    assert doc_reconstructed.document_id == "reconstructed_corridor"
    assert len(doc_reconstructed.threats) == 3


def test_canonical_f1_document_parity():
    """Canonical F1 CADDocument must analyze to exact frozen baseline values (M=-6, r2=3)."""
    doc_f1 = get_canonical_f1_document()
    res = analyze_cad_document(doc_f1, include_telemetry=False)

    assert res["is_valid"] is True
    assert res["tactical_margin_tics"] == -6
    assert res["l_star_tics"] == 6
    assert res["status_band"] == "UNSERVICEABLE"
    assert res["source_schedule_feasible"] is False
    assert len(res["threat_jobs"]) == 2
    assert res["threat_jobs"][0]["reveal_tic"] == 0
    assert res["threat_jobs"][1]["reveal_tic"] == 3
    assert res["stagger_gap_tics"] == 3


def test_custom_corridor_document_analysis_3_threats():
    """Custom corridor with 3 non-benchmark threats must analyze without special-casing."""
    doc_custom = get_custom_asymmetric_corridor_document()
    res = analyze_cad_document(doc_custom, include_telemetry=False)

    assert res["is_valid"] is True
    assert res["document_id"] == "custom_asymmetric_corridor"
    assert len(res["threat_jobs"]) == 3
    
    threat_ids = [j["id"] for j in res["threat_jobs"]]
    assert "sniper_nest_north" in threat_ids
    assert "flanker_alcove_south" in threat_ids
    assert "overwatch_bunker_east" in threat_ids
    assert res["stagger_gap_tics"] >= 0


def test_generic_2d_obstacle_translation():
    """Any obstacle can be translated in 2D (X and Y) with invariant validation."""
    doc_custom = get_custom_asymmetric_corridor_document()
    
    # 1. Valid 2D translation of pillar_alpha (+0.4m X, +0.2m Y)
    trans_doc, is_valid, err = translate_obstacle_in_document(doc_custom, "pillar_alpha", dx=0.4, dy=0.2)
    assert is_valid is True
    assert err is None
    
    res = analyze_cad_document(trans_doc)
    assert res["is_valid"] is True

    # 2. Invalid translation causing boundary breach
    _, is_valid_bad, err_bad = translate_obstacle_in_document(doc_custom, "pillar_alpha", dx=15.0, dy=0.0)
    assert is_valid_bad is False
    assert "boundary" in err_bad.lower() or "outside" in err_bad.lower()


def test_no_calculated_fields_in_cad_document():
    """CADDocument must never persist runtime metrics, schedules, or engine evidence."""
    doc_dict = get_canonical_f1_document().to_dict()
    forbidden_keys = [
        "tactical_margin_tics",
        "tactical_margin_ms",
        "l_star_tics",
        "verdict",
        "external_engine_evidence",
        "telemetry_frames",
        "events",
        "model_death_tic"
    ]
    for key in forbidden_keys:
        assert key not in doc_dict, f"Forbidden calculated key '{key}' found in CADDocument dict!"


def test_fast_analysis_semantics():
    """Fast analysis path must not guess realized outcomes and must emit source_schedule_feasible."""
    doc = get_canonical_f1_document()
    res = analyze_cad_document(doc, include_telemetry=False)

    assert res["source_schedule_feasible"] is False
    assert res["model_episode_survived"] is None
    assert res["model_death_tic"] is None
    assert res["telemetry_frames"] is None
    assert res["events"] is None

    for job in res["threat_jobs"]:
        assert job["scheduled_service_end_tic"] is not None
        assert job["realized_service_complete_tic"] is None  # Strictly null on fast path


def test_full_telemetry_commit_semantics():
    """Committed full analysis must derive realized service completion strictly from actual events."""
    doc = get_canonical_f1_document()
    
    # 1. Broken F1 -> Dies at tic 25 -> Threat 2 realized completion is None
    res_broken = analyze_cad_document(doc, include_telemetry=True)
    assert res_broken["model_episode_survived"] is False
    assert res_broken["model_death_tic"] == 25
    assert len(res_broken["telemetry_frames"]) > 0
    assert len(res_broken["events"]) > 0

    t1_job = res_broken["threat_jobs"][0]
    t2_job = res_broken["threat_jobs"][1]
    assert t1_job["realized_service_complete_tic"] == 12
    assert t2_job["realized_service_complete_tic"] is None  # Died before completion!

    # 2. Shift wall by +1.10m -> Survives -> Both threats realized
    repaired_doc, is_valid, _ = translate_obstacle_in_document(doc, "wall_0", dx=1.10, dy=0.0)
    assert is_valid is True
    res_repaired = analyze_cad_document(repaired_doc, include_telemetry=True)
    assert res_repaired["model_episode_survived"] is True
    assert res_repaired["model_death_tic"] is None

    t1_rep = res_repaired["threat_jobs"][0]
    t2_rep = res_repaired["threat_jobs"][1]
    assert t1_rep["realized_service_complete_tic"] == 12
    assert t2_rep["realized_service_complete_tic"] == 32


def test_document_session_server_endpoints():
    """Verify Flask document session REST endpoints (/api/document, /api/document/load, etc.)."""
    app = create_cad_app()
    client = app.test_client()

    # 1. Get Document
    resp_doc = client.get("/api/document")
    assert resp_doc.status_code == 200
    data_doc = resp_doc.get_json()
    assert data_doc["schema_version"] == "cad_document_v1"

    # 2. Load Custom Corridor
    resp_load = client.post("/api/document/load", json={"name": "custom_corridor"})
    assert resp_load.status_code == 200
    assert resp_load.get_json()["document_type"] == "custom_corridor"

    # 3. Generic 2D Obstacle Translation
    resp_trans = client.post("/api/document/translate_obstacle", json={
        "obstacle_id": "pillar_alpha",
        "dx": 0.35,
        "dy": 0.15,
        "client_revision": 44,
        "include_telemetry": False
    })
    assert resp_trans.status_code == 200
    data_trans = resp_trans.get_json()
    assert data_trans["is_valid"] is True
    assert data_trans["client_revision"] == 44
    assert data_trans["dx"] == 0.35
    assert data_trans["dy"] == 0.15

    # 4. Reset Document
    resp_reset = client.post("/api/document/reset")
    assert resp_reset.status_code == 200
    assert resp_reset.get_json()["status"] == "reset"
