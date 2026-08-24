"""Deterministic Unit & API Tests for Tactical Scenario Authoring (M2D).

Verifies route and threat creation, waypoint manipulation, parameter editing,
causal analysis recomputation, and Undo/Redo history stack preservation.
"""

import pytest
from cut_the_cake.cad_server import create_cad_app
from cut_the_cake.cad_document import CADDocument, CADRoute, CADThreat, validate_cad_document
from cut_the_cake.cad_adapter import (
    create_route_in_document,
    update_route_waypoint,
    add_route_waypoint,
    delete_route_waypoint,
    delete_route_in_document,
    update_route_speed,
    create_threat_in_document,
    translate_threat_in_document,
    update_threat_due_window,
    update_threat_service_duration,
    delete_threat_in_document,
    update_player_model,
    analyze_cad_document
)


def test_route_creation_and_waypoint_manipulation():
    """Verify route creation, adding/updating/deleting waypoints and boundary validation."""
    app = create_cad_app()
    client = app.test_client()

    client.post("/api/document/load", json={"name": "custom_corridor"})
    base_doc = client.get("/api/document").get_json()
    assert len(base_doc["geometry"]["routes"]) == 1

    # 1. Create a secondary flanking route inside boundary [0, 12] x [-3, 3]
    resp_create = client.post("/api/document/create_route", json={
        "name": "Flank Route",
        "waypoints": [[1.0, -1.0], [6.0, -1.0], [11.0, -1.0]],
        "v_move_mps": 3.0,
        "commit": True
    })
    assert resp_create.status_code == 200
    route_id = resp_create.get_json()["created_route_id"]
    assert route_id.startswith("route_")

    doc_1 = client.get("/api/document").get_json()
    assert len(doc_1["geometry"]["routes"]) == 2

    # 2. Update waypoint 1
    resp_upd = client.post("/api/document/update_route_waypoint", json={
        "route_id": route_id,
        "waypoint_idx": 1,
        "x": 6.0,
        "y": -0.5,
        "commit": True
    })
    assert resp_upd.status_code == 200
    doc_2 = client.get("/api/document").get_json()
    assert doc_2["geometry"]["routes"][1]["waypoints"][1] == [6.0, -0.5]

    # 3. Add waypoint
    resp_add = client.post("/api/document/add_route_waypoint", json={
        "route_id": route_id,
        "insert_idx": 2,
        "x": 8.0,
        "y": -0.8,
        "commit": True
    })
    assert resp_add.status_code == 200
    doc_3 = client.get("/api/document").get_json()
    assert len(doc_3["geometry"]["routes"][1]["waypoints"]) == 4

    # 4. Delete waypoint
    resp_del_wpt = client.post("/api/document/delete_route_waypoint", json={
        "route_id": route_id,
        "waypoint_idx": 2
    })
    assert resp_del_wpt.status_code == 200
    doc_4 = client.get("/api/document").get_json()
    assert len(doc_4["geometry"]["routes"][1]["waypoints"]) == 3

    # 5. Boundary violation rejection
    resp_invalid = client.post("/api/document/update_route_waypoint", json={
        "route_id": route_id,
        "waypoint_idx": 1,
        "x": 6.0,
        "y": 50.0  # Far outside boundary
    })
    assert resp_invalid.status_code == 422
    assert "within boundary" in resp_invalid.get_json()["error_reason"]


def test_route_speed_update_affects_analysis():
    """Verify route traversal speed changes dynamically scale reveal tics on occluded threats."""
    app = create_cad_app()
    client = app.test_client()

    client.post("/api/document/load", json={"name": "canonical_f1"})
    
    # 1. Base analysis at 4.5 m/s
    res_base = client.post("/api/document/analyze", json={"include_telemetry": True}).get_json()
    r_base_t2 = next(j["reveal_tic"] for j in res_base["threat_jobs"] if j["id"] == "F1_T2_R00")
    assert r_base_t2 == 3

    # 2. Halve speed to 2.25 m/s
    resp_speed = client.post("/api/document/update_route_speed", json={
        "route_id": "main",
        "v_move_mps": 2.25,
        "commit": True
    })
    assert resp_speed.status_code == 200
    res_half = resp_speed.get_json()
    r_half_t2 = next(j["reveal_tic"] for j in res_half["threat_jobs"] if j["id"] == "F1_T2_R00")

    # Reveal tic doubles from 3 to 6 tics
    assert r_half_t2 == 6


def test_threat_creation_translation_and_parameter_edits():
    """Verify threat creation, translation, due window / service duration edits."""
    app = create_cad_app()
    client = app.test_client()

    client.post("/api/document/load", json={"name": "custom_corridor"})
    doc_init = client.get("/api/document").get_json()
    initial_threat_count = len(doc_init["geometry"]["threats"])

    # 1. Create new threat T4
    resp_create = client.post("/api/document/create_threat", json={
        "name": "Corridor Ambush Threat",
        "anchor": [4.0, 1.2],
        "due_window_s": 0.50,
        "service_duration_s": 0.12,
        "commit": True
    })
    assert resp_create.status_code == 200
    t_id = resp_create.get_json()["created_threat_id"]
    doc_1 = client.get("/api/document").get_json()
    assert len(doc_1["geometry"]["threats"]) == initial_threat_count + 1

    # 2. Translate threat
    resp_move = client.post("/api/document/translate_threat", json={
        "threat_id": t_id,
        "dx": 0.5,
        "dy": 0.0,
        "commit": True
    })
    assert resp_move.status_code == 200
    doc_2 = client.get("/api/document").get_json()
    new_threat = next(t for t in doc_2["geometry"]["threats"] if t["id"] == t_id)
    assert abs(new_threat["anchor"][0] - 4.5) < 1e-3

    # 3. Update due window
    resp_dw = client.post("/api/document/update_threat_due_window", json={
        "threat_id": t_id,
        "due_window_s": 0.85,
        "commit": True
    })
    assert resp_dw.status_code == 200
    doc_3 = client.get("/api/document").get_json()
    new_threat = next(t for t in doc_3["geometry"]["threats"] if t["id"] == t_id)
    assert abs(new_threat["due_window_s"] - 0.85) < 1e-3

    # 4. Update service duration
    resp_sd = client.post("/api/document/update_threat_service_duration", json={
        "threat_id": t_id,
        "service_duration_s": 0.20,
        "commit": True
    })
    assert resp_sd.status_code == 200
    doc_4 = client.get("/api/document").get_json()
    new_threat = next(t for t in doc_4["geometry"]["threats"] if t["id"] == t_id)
    assert abs(new_threat["service_duration_s"] - 0.20) < 1e-3

    # 5. Delete threat
    resp_del = client.post("/api/document/delete_threat", json={"threat_id": t_id})
    assert resp_del.status_code == 200
    doc_5 = client.get("/api/document").get_json()
    assert len(doc_5["geometry"]["threats"]) == initial_threat_count


def test_scenario_undo_redo_full_stack():
    """Verify Undo/Redo history across route, threat, and player model mutations."""
    app = create_cad_app()
    client = app.test_client()

    client.post("/api/document/load", json={"name": "custom_corridor"})
    base_doc = client.get("/api/document").get_json()

    # Step 1: Create Route inside [0, 12] x [-3, 3]
    resp_r = client.post("/api/document/create_route", json={
        "waypoints": [[1.0, 0.0], [11.0, 0.0]],
        "commit": True
    })
    assert resp_r.status_code == 200
    r_id = resp_r.get_json()["created_route_id"]

    # Step 2: Create Threat
    resp_t = client.post("/api/document/create_threat", json={
        "anchor": [2.0, 1.0],
        "due_window_s": 0.40,
        "commit": True
    })
    assert resp_t.status_code == 200
    t_id = resp_t.get_json()["created_threat_id"]

    # Step 3: Update Player Model
    client.post("/api/document/update_player_model", json={
        "initial_reticle_deg": 45.0,
        "commit": True
    })

    doc_final = client.get("/api/document").get_json()
    assert len(doc_final["geometry"]["routes"]) == len(base_doc["geometry"]["routes"]) + 1
    assert len(doc_final["geometry"]["threats"]) == len(base_doc["geometry"]["threats"]) + 1
    assert doc_final["player_model"]["initial_reticle_deg"] == 45.0
    assert doc_final["can_undo"] is True

    # Undo x3 -> Back to baseline
    client.post("/api/document/undo")
    client.post("/api/document/undo")
    client.post("/api/document/undo")

    doc_undone = client.get("/api/document").get_json()
    assert len(doc_undone["geometry"]["routes"]) == len(base_doc["geometry"]["routes"])
    assert len(doc_undone["geometry"]["threats"]) == len(base_doc["geometry"]["threats"])
    assert doc_undone["player_model"]["initial_reticle_deg"] == base_doc["player_model"]["initial_reticle_deg"]

    # Redo x3 -> Back to final
    client.post("/api/document/redo")
    client.post("/api/document/redo")
    client.post("/api/document/redo")

    doc_redone = client.get("/api/document").get_json()
    assert len(doc_redone["geometry"]["routes"]) == len(doc_final["geometry"]["routes"])
    assert len(doc_redone["geometry"]["threats"]) == len(doc_final["geometry"]["threats"])
    assert doc_redone["player_model"]["initial_reticle_deg"] == 45.0


def test_monotonic_route_and_threat_id_allocation():
    """Verify route and threat monotonic ID allocators never reuse deleted IDs."""
    app = create_cad_app()
    client = app.test_client()

    client.post("/api/document/load", json={"name": "custom_corridor"})

    # 1. Route ID non-reuse inside [0, 12] x [-3, 3]
    resp_r1 = client.post("/api/document/create_route", json={"waypoints": [[1, 0], [11, 0]], "commit": True})
    assert resp_r1.status_code == 200
    r1 = resp_r1.get_json()["created_route_id"]
    client.post("/api/document/delete_route", json={"route_id": r1})
    resp_r2 = client.post("/api/document/create_route", json={"waypoints": [[1, 0], [11, 0]], "commit": True})
    assert resp_r2.status_code == 200
    r2 = resp_r2.get_json()["created_route_id"]
    assert r1 != r2

    # 2. Threat ID non-reuse
    resp_t1 = client.post("/api/document/create_threat", json={"anchor": [2, 1], "commit": True})
    assert resp_t1.status_code == 200
    t1 = resp_t1.get_json()["created_threat_id"]
    client.post("/api/document/delete_threat", json={"threat_id": t1})
    resp_t2 = client.post("/api/document/create_threat", json={"anchor": [2, 1], "commit": True})
    assert resp_t2.status_code == 200
    t2 = resp_t2.get_json()["created_threat_id"]
    assert t1 != t2


def test_safe_exact_solver_envelope_and_fail_closed_dispatch():
    """Verify M2D.1 safe exact solver envelope:
    - J <= 6 : EXACT_INTERACTIVE (Normal exact)
    - J == 7 : EXACT_SLOW (Allowed on explicit analyze)
    - J >= 8 : EXACT_LIMIT_EXCEEDED (Fail-closed prompt return without factorial hang)
    - Explicit allow_slow_solver=True override permits exact solve on J >= 8.
    """
    import time
    from cut_the_cake.cad_document import CADPlayerModel, CADObstacle
    from cut_the_cake.vizdoom_engine import DiscreteTicScheduler, TicThreatJob

    # 1. Construct an open corridor document with 8 visible threats along the route
    boundary = [[-2.0, -5.0], [20.0, -5.0], [20.0, 5.0], [-2.0, 5.0]]
    route = CADRoute(
        id="route_long",
        name="Long Route",
        waypoints=[[0.0, 0.0], [18.0, 0.0]],
        v_move_mps=4.5,
    )
    # 8 visible threats placed along the corridor with line-of-sight to the route
    threats_8 = [
        CADThreat(
            id=f"threat_{i}",
            name=f"Threat {i}",
            polygon=[[float(2 * i + 1) - 0.2, 2.0 - 0.2], [float(2 * i + 1) + 0.2, 2.0 - 0.2],
                     [float(2 * i + 1) + 0.2, 2.0 + 0.2], [float(2 * i + 1) - 0.2, 2.0 + 0.2]],
            anchor=[float(2 * i + 1), 2.0],
            due_window_s=0.5,
            service_duration_s=0.15,
        )
        for i in range(8)
    ]

    doc_8 = CADDocument(
        document_id="doc_envelope_test_8",
        name="Envelope Test 8 Threats",
        schema_version="cad_document_v1",
        boundary=boundary,
        player_model=CADPlayerModel(
            v_move_mps=4.5,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0,
        ),
        obstacles=[],
        routes=[route],
        threats=threats_8,
    )

    # 2. Verify J=8 fails closed promptly (< 50 ms) without factorial enumeration
    t0 = time.perf_counter()
    res_8 = analyze_cad_document(doc_8, include_telemetry=False, max_exact_jobs=7, allow_slow_solver=False)
    t_elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert t_elapsed_ms < 50.0, f"Analysis took {t_elapsed_ms:.2f} ms; should return promptly without factorial enumeration"
    assert res_8["is_valid"] is True
    assert res_8["compiled_job_count"] == 8
    assert res_8["solver_mode"] == "EXACT_LIMIT_EXCEEDED"
    assert res_8["is_exact"] is False
    assert res_8["solver_limit"] == 7
    assert res_8["status_band"] == "SOLVER_LIMIT_EXCEEDED"
    assert res_8["verdict"] == "inconclusive"
    assert res_8["tactical_margin_tics"] is None
    assert res_8["l_star_tics"] is None
    assert res_8["source_schedule_feasible"] is None
    assert res_8["diagnostic"]["type"] == "SOLVER_LIMIT_EXCEEDED"
    assert "EXACT_LIMIT_EXCEEDED" in res_8["diagnostic"]["explanation"]
    assert len(res_8["threat_jobs"]) == 8
    assert res_8["threat_jobs"][0]["completion_tic"] is None

    # 3. Verify DiscreteTicScheduler directly enforces the envelope limit
    scheduler = DiscreteTicScheduler()
    test_jobs_8 = [
        TicThreatJob(
            id=f"job_{i}",
            reveal_tic=i * 5,
            due_window_tics=20,
            deadline_tic=i * 5 + 20,
            angle_deg=0.0,
            threat_anchor=(float(i), 2.0),
            service_duration_tics=4,
        )
        for i in range(8)
    ]
    with pytest.raises(ValueError, match="Exact permutation scheduler job limit exceeded"):
        scheduler.solve(test_jobs_8, max_exact_jobs=7, allow_slow_solver=False)

    # 4. Verify explicit allow_slow_solver=True override succeeds
    res_override = analyze_cad_document(doc_8, include_telemetry=False, max_exact_jobs=7, allow_slow_solver=True)
    assert res_override["is_valid"] is True
    assert res_override["compiled_job_count"] == 8
    assert res_override["solver_mode"] == "EXACT_OVERRIDE"
    assert res_override["is_exact"] is True
    assert res_override["tactical_margin_tics"] is not None
    assert res_override["l_star_tics"] is not None
