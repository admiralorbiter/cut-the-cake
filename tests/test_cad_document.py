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
    get_custom_asymmetric_corridor_document,
    validate_cad_document
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


def test_cumulative_obstacle_edits_persist():
    """Sequential edits to distinct obstacles must accumulate in the working document upon commit."""
    app = create_cad_app()
    client = app.test_client()

    # Load multi-obstacle document
    client.post("/api/document/load", json={"name": "custom_corridor"})
    initial_doc = client.get("/api/document").get_json()
    init_alpha_v0 = initial_doc["geometry"]["obstacles"][0]["vertices"][0]
    init_beta_v0 = initial_doc["geometry"]["obstacles"][1]["vertices"][0]

    # 1. Move Pillar Alpha by dx = +0.50m (clear of sniper nest), commit = True
    resp1 = client.post("/api/document/translate_obstacle", json={
        "obstacle_id": "pillar_alpha",
        "dx": 0.50,
        "dy": 0.0,
        "commit": True,
        "include_telemetry": False
    })
    assert resp1.status_code == 200
    doc_after_1 = client.get("/api/document").get_json()
    assert abs(doc_after_1["geometry"]["obstacles"][0]["vertices"][0][0] - (init_alpha_v0[0] + 0.50)) < 1e-3
    assert doc_after_1["geometry"]["obstacles"][1]["vertices"][0] == init_beta_v0

    # 2. Move Pillar Beta by dx = +0.50m (clear of flanker alcove), commit = True
    resp2 = client.post("/api/document/translate_obstacle", json={
        "obstacle_id": "pillar_beta",
        "dx": 0.50,
        "dy": 0.0,
        "commit": True,
        "include_telemetry": False
    })
    assert resp2.status_code == 200
    doc_after_2 = client.get("/api/document").get_json()

    # Both edits must be present simultaneously!
    assert abs(doc_after_2["geometry"]["obstacles"][0]["vertices"][0][0] - (init_alpha_v0[0] + 0.50)) < 1e-3
    assert abs(doc_after_2["geometry"]["obstacles"][1]["vertices"][0][0] - (init_beta_v0[0] + 0.50)) < 1e-3

    # 3. Reset document -> Both return to baseline
    resp_reset = client.post("/api/document/reset")
    assert resp_reset.status_code == 200
    doc_reset = client.get("/api/document").get_json()
    assert doc_reset["geometry"]["obstacles"][0]["vertices"][0] == init_alpha_v0
    assert doc_reset["geometry"]["obstacles"][1]["vertices"][0] == init_beta_v0


def test_route_and_initial_reticle_telemetry_parity():
    """Fast source analysis and full committed playback must evaluate the exact same route and initial aim."""
    doc = get_custom_asymmetric_corridor_document()
    
    # Add a second alternative route
    doc.routes.append(CADRoute(
        id="route_flank",
        name="Flank Bypass",
        waypoints=[[0.0, -1.0], [6.0, -1.0], [12.0, -1.0]],
        v_move_mps=3.0
    ))
    doc.player_model.initial_reticle_deg = 45.0

    # Run fast analysis on route_flank
    fast_res = analyze_cad_document(doc, route_id="route_flank", include_telemetry=False)
    assert fast_res["is_valid"] is True

    # Run full committed telemetry on route_flank
    full_res = analyze_cad_document(doc, route_id="route_flank", include_telemetry=True)
    assert full_res["is_valid"] is True

    # Metrics and timing must match exactly
    assert fast_res["tactical_margin_tics"] == full_res["tactical_margin_tics"]
    assert fast_res["l_star_tics"] == full_res["l_star_tics"]
    assert len(full_res["telemetry_frames"]) > 0
    # First telemetry frame must reflect the 45 degree initial aim
    assert full_res["telemetry_frames"][0]["reticle_heading_deg"] == 45.0


def test_validate_cad_document_rejection():
    """validate_cad_document must reject duplicates, degenerate geometry, and unauthorized fields."""
    # 1. Valid document passes
    doc = get_custom_asymmetric_corridor_document()
    is_valid, errors = validate_cad_document(doc.to_dict())
    assert is_valid is True
    assert len(errors) == 0

    # 2. Reject duplicate obstacle IDs
    bad_dict = doc.to_dict()
    bad_dict["geometry"]["obstacles"].append(dict(bad_dict["geometry"]["obstacles"][0]))
    is_valid, errors = validate_cad_document(bad_dict)
    assert is_valid is False
    assert any("duplicate" in e.lower() for e in errors)

    # 3. Reject unauthorized calculated/evidence fields in authoring document
    bad_dict2 = doc.to_dict()
    bad_dict2["tactical_margin_tics"] = 2  # Not allowed in authoring document
    is_valid, errors = validate_cad_document(bad_dict2)
    assert is_valid is False
    assert any("schema error" in e.lower() for e in errors)


def test_parameter_authority_semantics():
    """threat.service_duration_s controls service requirement; player_model.service_duration_s is default template."""
    doc = get_custom_asymmetric_corridor_document()
    doc.threats[0].service_duration_s = 0.20  # Double service duration
    
    geo = doc.to_geometric_module()
    assert geo.threats[0].service_duration_s == 0.20

    from cut_the_cake.vizdoom_engine import DeterministicSimulationReferee
    params = doc.player_model.to_combat_params()
    referee = DeterministicSimulationReferee(params)
    jobs = referee.extract_tic_jobs(geo, route_index=0)
    
    # 0.20s at dt=0.02857s is 7 tics
    assert jobs[0].service_duration_tics == 7


def test_document_load_and_analyze_raw_upload_regression():
    """Verify raw CADDocument JSON upload to /api/document/load and /api/document/analyze."""
    app = create_cad_app()
    client = app.test_client()

    valid_doc = get_custom_asymmetric_corridor_document()
    valid_dict = valid_doc.to_dict()

    # 1. POST valid raw document to /api/document/load -> 200
    resp_load_ok = client.post("/api/document/load", json={"document": valid_dict})
    assert resp_load_ok.status_code == 200
    data_load = resp_load_ok.get_json()
    assert data_load["status"] == "loaded"
    assert data_load["document"]["document_id"] == valid_doc.document_id

    # 2. POST invalid raw document to /api/document/load -> 422 (not 500)
    invalid_dict = dict(valid_dict)
    invalid_dict["geometry"] = dict(invalid_dict["geometry"])
    invalid_dict["geometry"]["obstacles"] = list(invalid_dict["geometry"]["obstacles"])
    # Add duplicate obstacle ID
    invalid_dict["geometry"]["obstacles"].append(dict(invalid_dict["geometry"]["obstacles"][0]))
    resp_load_fail = client.post("/api/document/load", json={"document": invalid_dict})
    assert resp_load_fail.status_code == 422
    assert "validation failed" in resp_load_fail.get_json()["error"].lower()

    # 3. POST /api/document/analyze without payload -> analyzes active working document
    resp_analyze_active = client.post("/api/document/analyze", json={})
    assert resp_analyze_active.status_code == 200
    data_active = resp_analyze_active.get_json()
    assert data_active["is_valid"] is True
    assert data_active["document_id"] == valid_doc.document_id

    # 4. POST /api/document/analyze with invalid raw document -> 422
    resp_analyze_fail = client.post("/api/document/analyze", json={"document": invalid_dict})
    assert resp_analyze_fail.status_code == 422
    assert resp_analyze_fail.get_json()["is_valid"] is False


def test_route_speed_override_and_reveal_timing():
    """Selected route v_move_mps must override default player speed and scale reveal/deadline tics."""
    doc = CADDocument(
        document_id="route_speed_audit",
        name="Route Speed Audit Room",
        description="Test room for verifying route traversal speed override on reveal timing",
        metadata={},
        units={"coordinates": "meters", "angles": "degrees", "time": "seconds"},
        player_model=CADPlayerModel(
            v_move_mps=4.5,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0
        ),
        boundary=[[0.0, -3.0], [10.0, -3.0], [10.0, 3.0], [0.0, 3.0], [0.0, -3.0]],
        obstacles=[
            CADObstacle(
                id="blocking_wall",
                name="Blocking Wall",
                vertices=[[2.5, 0.3], [3.0, 0.3], [3.0, 2.8], [2.5, 2.8], [2.5, 0.3]]
            )
        ],
        routes=[
            CADRoute(
                id="route_fast",
                name="Fast Route (4.5 m/s)",
                waypoints=[[0.0, 0.0], [8.0, 0.0]],
                v_move_mps=4.5
            ),
            CADRoute(
                id="route_slow",
                name="Slow Route (2.25 m/s)",
                waypoints=[[0.0, 0.0], [8.0, 0.0]],
                v_move_mps=2.25
            )
        ],
        threats=[
            CADThreat(
                id="threat_hidden",
                name="Hidden Threat Behind Wall",
                polygon=[[5.0, 1.5], [6.0, 1.5], [6.0, 2.5], [5.0, 2.5], [5.0, 1.5]],
                anchor=[5.5, 2.0],
                due_window_s=0.60,
                service_duration_s=0.10
            )
        ],
        ports=[]
    )

    # 1. Fast route analysis (4.5 m/s)
    res_fast = analyze_cad_document(doc, route_id="route_fast", include_telemetry=False)
    res_fast_comm = analyze_cad_document(doc, route_id="route_fast", include_telemetry=True)
    assert res_fast["selected_route_id"] == "route_fast"
    assert res_fast["effective_v_move_mps"] == 4.5
    assert res_fast["tactical_margin_tics"] == res_fast_comm["tactical_margin_tics"]

    # 2. Slow route analysis (2.25 m/s)
    res_slow = analyze_cad_document(doc, route_id="route_slow", include_telemetry=False)
    res_slow_comm = analyze_cad_document(doc, route_id="route_slow", include_telemetry=True)
    assert res_slow["selected_route_id"] == "route_slow"
    assert res_slow["effective_v_move_mps"] == 2.25
    assert res_slow["tactical_margin_tics"] == res_slow_comm["tactical_margin_tics"]

    # 3. Exact reveal tic checks:
    # At 4.5 m/s, reveal tic is 20 (0.5714s). At 2.25 m/s, reveal tic is 40 (1.1429s).
    r_fast = res_fast["threat_jobs"][0]["reveal_tic"]
    r_slow = res_slow["threat_jobs"][0]["reveal_tic"]
    assert r_fast == 20
    assert r_slow == 40
    assert r_slow > r_fast
    assert r_slow == 2 * r_fast
    assert res_fast["threat_jobs"][0]["deadline_tic"] == 41
    assert res_slow["threat_jobs"][0]["deadline_tic"] == 61


def test_structured_generic_deadline_overload_diagnostic():
    """Negative-margin diagnostic must provide structured DEADLINE_OVERLOAD fields without guessing mechanism."""
    doc = get_canonical_f1_document()  # Broken F1 -> M = -6
    res = analyze_cad_document(doc, include_telemetry=False)
    
    assert res["is_valid"] is True
    assert res["tactical_margin_tics"] == -6
    assert res["status_band"] == "UNSERVICEABLE"
    
    diag = res["diagnostic"]
    assert diag["type"] == "DEADLINE_OVERLOAD"
    assert diag["critical_threat_id"] == "F1_T2_R00"
    assert diag["reveal_tic"] is not None
    assert diag["deadline_tic"] is not None
    assert diag["scheduled_completion_tic"] is not None
    assert diag["lateness_tics"] is not None
    assert diag["lateness_tics"] == 6
    assert "Deadline overload detected" in diag["explanation"]


def test_strict_fail_closed_geometry_rejections():
    """validate_cad_document must reject non-finite numbers, degenerate threats, and boundary breaches."""
    doc = get_custom_asymmetric_corridor_document()

    # 1. Non-finite player speed (NaN / Inf)
    bad_dict = doc.to_dict()
    bad_dict["player_model"]["v_move_mps"] = float("inf")
    is_valid, errors = validate_cad_document(bad_dict)
    assert is_valid is False

    # 2. Threat anchor outside boundary
    bad_dict2 = doc.to_dict()
    bad_dict2["geometry"]["threats"][0]["anchor"] = [100.0, 100.0]
    is_valid, errors = validate_cad_document(bad_dict2)
    assert is_valid is False
    assert any("outside boundary" in e.lower() for e in errors)

    # 3. Degenerate / zero-length route
    bad_dict3 = doc.to_dict()
    bad_dict3["geometry"]["routes"][0]["waypoints"] = [[1.0, 1.0], [1.0, 1.0]]
    is_valid, errors = validate_cad_document(bad_dict3)
    assert is_valid is False
    assert any("zero geometric length" in e.lower() for e in errors)


