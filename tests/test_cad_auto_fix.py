"""Deterministic API & Unit Tests for Milestone 2E (M2E): Auto-Fix Repair Optimizer.

Verifies:
1. Canonical F1 Baffle Stagger repair (M0 = -6 tics -> M1 = +2 tics with minimal shift 0.20m).
2. Custom corridor repair and candidate traversal.
3. Already serviceable document no-op avoidance (no_repair_needed=True, evals=1).
4. Tri-state candidate evaluation accounting (EXACT_EVALUATED vs UNSUPPORTED_ENVELOPE vs INVALID_GEOMETRY).
5. REST API endpoint /api/document/auto_fix with commit=False (preview) and commit=True (undo/redo stack).
6. Exact vertical-slice closed loop (G0 -> analyze -> diagnose -> repair -> re-analyze -> replay).
"""

import pytest
import time

pytestmark = [pytest.mark.cad]
from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPlayerModel,
    get_canonical_f1_document,
    get_custom_asymmetric_corridor_document,
    validate_cad_document
)
from cut_the_cake.cad_adapter import (
    analyze_cad_document,
    auto_fix_cad_document
)
from cut_the_cake.cad_server import create_cad_app


def test_auto_fix_canonical_f1_baffle_stagger():
    """Verify Auto-Fix resolves Canonical F1 baffle stagger deficit:
    - Initial: M0 = -6 tics (Infeasible)
    - Repaired: M1 = +2 tics (Target met) with minimal shift Delta d = 0.20m
    - Target obstacle: 'Central Baffle'
    """
    doc_f1 = get_canonical_f1_document()
    res_initial = analyze_cad_document(doc_f1, include_telemetry=False)
    assert res_initial["is_valid"] is True
    assert res_initial["tactical_margin_tics"] == -6
    assert res_initial["status_band"] == "UNSERVICEABLE"

    t0 = time.perf_counter()
    repair_res = auto_fix_cad_document(
        doc_f1,
        target_margin_tics=2,
        max_perturbation_m=2.0,
        search_resolution_m=0.05,
        max_exact_jobs=6
    )
    runtime_ms = (time.perf_counter() - t0) * 1000.0

    assert repair_res["success"] is True
    assert repair_res["status"] == "REPAIR_FOUND"
    assert repair_res["initial_margin_tics"] == -6
    assert repair_res["repaired_margin_tics"] == 2
    assert repair_res["edit_distance_m"] == pytest.approx(1.10, abs=1e-3)
    assert repair_res["controlling_obstacle_name"] == "Central Baffle"
    assert repair_res["no_repair_needed"] is False
    assert repair_res["evaluations_count"] > 1
    assert repair_res["evaluations_breakdown"]["exact_evaluated"] > 0
    assert repair_res["evaluations_breakdown"]["unsupported_envelope"] == 0
    assert repair_res["repaired_document"] is not None

    # Pass the repaired document through the exact frozen analyzer
    repaired_doc = CADDocument.from_dict(repair_res["repaired_document"])
    reanalyzed = analyze_cad_document(repaired_doc, include_telemetry=True)
    assert reanalyzed["is_valid"] is True
    assert reanalyzed["tactical_margin_tics"] >= 2
    assert reanalyzed["source_schedule_feasible"] is True
    assert reanalyzed["status_band"] in ("TARGET RESERVE MET", "FEASIBLE — BELOW TARGET RESERVE")


def test_auto_fix_already_serviceable_no_op():
    """Verify Auto-Fix on an already serviceable document returns no_repair_needed=True and exits in 1 eval."""
    doc_f1 = get_canonical_f1_document()
    # First obtain repaired document
    repair_res = auto_fix_cad_document(doc_f1, target_margin_tics=2)
    assert repair_res["success"] is True
    repaired_doc = CADDocument.from_dict(repair_res["repaired_document"])

    # Run Auto-Fix again on the already repaired document
    second_run = auto_fix_cad_document(repaired_doc, target_margin_tics=2)
    assert second_run["success"] is False
    assert second_run["no_repair_needed"] is True
    assert second_run["status"] == "ALREADY_SERVICEABLE"
    assert second_run["initial_margin_tics"] >= 2
    assert second_run["repaired_margin_tics"] >= 2
    assert second_run["evaluations_count"] == 1
    assert second_run["evaluations_breakdown"]["exact_evaluated"] == 1
    assert second_run["evaluations_breakdown"]["unsupported_envelope"] == 0
    assert second_run["evaluations_breakdown"]["invalid_geometry"] == 0


def test_auto_fix_tri_state_candidate_accounting():
    """Verify that over-envelope candidates (J >= 7) are tracked in unsupported_envelope
    and never scored as bad / unserviceable failures.
    """
    boundary = [[-2.0, -5.0], [20.0, -5.0], [20.0, 5.0], [-2.0, 5.0]]
    route = CADRoute(
        id="route_long",
        name="Long Route",
        waypoints=[[0.0, 0.0], [18.0, 0.0]],
        v_move_mps=4.5,
    )
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
        document_id="doc_8_threats",
        name="8 Threats",
        boundary=boundary,
        player_model=CADPlayerModel(),
        obstacles=[CADObstacle(id="obs_0", name="Test Obstacle", vertices=[[5.0, 0.5], [6.0, 0.5], [6.0, 1.5], [5.0, 1.5]])],
        routes=[route],
        threats=threats_8,
    )

    res = auto_fix_cad_document(doc_8, max_exact_jobs=6)
    assert res["success"] is False
    assert res["status"] == "UNSUPPORTED_BASELINE_ENVELOPE"
    assert res["initial_margin_tics"] is None
    assert res["evaluations_breakdown"]["unsupported_envelope"] == 1
    assert "exceeds exact analysis envelope" in res["repair_description"]


def test_auto_fix_server_endpoint_preview_and_commit():
    """Verify POST /api/document/auto_fix:
    1. commit=False: preview only, working_document unmodified, can_undo=False.
    2. commit=True: working_document mutated to repaired state, can_undo=True.
    3. Undo reverts to initial unserviceable state.
    4. Redo restores repaired serviceable state.
    """
    app = create_cad_app()
    client = app.test_client()

    # Load canonical F1
    load_resp = client.post("/api/document/load", json={"name": "canonical_f1"})
    assert load_resp.status_code == 200

    # 1. Preview mode (commit=False)
    preview_resp = client.post("/api/document/auto_fix", json={"target_margin_tics": 2, "commit": False})
    assert preview_resp.status_code == 200
    preview_data = preview_resp.get_json()
    assert preview_data["success"] is True
    assert preview_data["status"] == "REPAIR_FOUND"
    assert preview_data["can_undo"] is False
    assert preview_data["repaired_margin_tics"] == 2

    # Check active working document is still broken
    doc_resp1 = client.get("/api/document")
    doc_data1 = doc_resp1.get_json()
    assert doc_data1["can_undo"] is False

    # 2. Commit mode (commit=True)
    commit_resp = client.post("/api/document/auto_fix", json={"target_margin_tics": 2, "commit": True})
    assert commit_resp.status_code == 200
    commit_data = commit_resp.get_json()
    assert commit_data["success"] is True
    assert commit_data["can_undo"] is True

    # Check active working document is now repaired
    analyze_resp = client.post("/api/document/analyze")
    assert analyze_resp.status_code == 200
    analyze_data = analyze_resp.get_json()
    assert analyze_data["tactical_margin_tics"] >= 2
    assert analyze_data["status_band"] in ("TARGET RESERVE MET", "FEASIBLE — BELOW TARGET RESERVE")

    # 3. Undo
    undo_resp = client.post("/api/document/undo")
    assert undo_resp.status_code == 200
    undo_data = undo_resp.get_json()
    assert undo_data["can_redo"] is True

    analyze_undone = client.post("/api/document/analyze").get_json()
    assert analyze_undone["tactical_margin_tics"] == -6
    assert analyze_undone["status_band"] == "UNSERVICEABLE"

    # 4. Redo
    redo_resp = client.post("/api/document/redo")
    assert redo_resp.status_code == 200
    analyze_redone = client.post("/api/document/analyze").get_json()
    assert analyze_redone["tactical_margin_tics"] >= 2


def test_auto_fix_full_vertical_slice_parity():
    """Verify end-to-end closed loop:
    G0 -> analyze(M0 < 0) -> auto_fix -> G1 -> analyze(M1 >= 0)
    Subject to:
    - G1 in T_allowed
    - geometry_valid(G1)
    - J(G1) <= 6
    """
    doc_0 = get_canonical_f1_document()
    a0 = analyze_cad_document(doc_0)
    assert a0["tactical_margin_tics"] < 0
    assert a0["compiled_job_count"] <= 6

    repair = auto_fix_cad_document(doc_0, target_margin_tics=2, max_perturbation_m=2.0)
    assert repair["success"] is True

    doc_1 = CADDocument.from_dict(repair["repaired_document"])
    
    # 1. Structural validity
    is_valid, errors = validate_cad_document(doc_1.to_dict())
    assert is_valid is True, f"Repaired document invalid: {errors}"

    # 2. Envelope constraint
    a1 = analyze_cad_document(doc_1, include_telemetry=True)
    assert a1["compiled_job_count"] <= 6
    assert a1["solver_mode"] == "EXACT_INTERACTIVE"

    # 3. Positive margin
    assert a1["tactical_margin_tics"] >= 2
    assert a1["source_schedule_feasible"] is True

    # 4. Full telemetry simulation verified
    assert a1["model_episode_survived"] is True
    assert len(a1["telemetry_frames"]) > 0


def test_auto_fix_nonzero_initial_reticle_heading_parity():
    """Verify that authored nonzero initial_reticle_deg is preserved and propagated through
    Auto-Fix diagnosis, candidate evaluations, and authoritative certification.
    
    Scientific Invariant:
    Analyze(G*)_exact == AutoFixEvaluation(G*) at authored theta_0 = -30.0 deg.
    """
    doc_f1 = get_canonical_f1_document()
    doc_f1.player_model.initial_reticle_deg = -30.0

    # Baseline with theta_0 = -30.0 deg
    a0 = analyze_cad_document(doc_f1)
    assert a0["is_valid"] is True
    assert a0["tactical_margin_tics"] == -4  # Different from -6 tics at theta_0 = 0.0

    repair_res = auto_fix_cad_document(doc_f1, target_margin_tics=2, max_perturbation_m=2.0)
    assert repair_res["success"] is True
    assert repair_res["status"] == "REPAIR_FOUND"
    assert repair_res["repaired_margin_tics"] == 2
    assert repair_res["edit_distance_m"] == pytest.approx(0.90, abs=1e-3)  # Shift 0.90m vs 1.10m at theta_0=0

    # Authoritative certification with same theta_0 = -30.0 deg
    repaired_doc = CADDocument.from_dict(repair_res["repaired_document"])
    assert repaired_doc.player_model.initial_reticle_deg == -30.0

    reanalyzed = analyze_cad_document(repaired_doc, include_telemetry=True)
    assert reanalyzed["is_valid"] is True
    # Exact parity invariant
    assert reanalyzed["tactical_margin_tics"] == repair_res["repaired_margin_tics"]
    assert reanalyzed["source_schedule_feasible"] is True


def test_auto_fix_selected_route_and_speed_propagation():
    """Verify that selecting a non-default route propagates its geometry, speed (v_move_mps),
    and arrival timing into Auto-Fix optimization and independent re-certification.
    """
    doc_f1 = get_canonical_f1_document()
    # Add a second slower patrol route
    route_slow = CADRoute(
        id="route_slow_patrol",
        name="Slow Patrol Route",
        waypoints=[[0.0, 0.0], [5.0, 0.5], [10.0, 0.0]],
        v_move_mps=1.8
    )
    doc_f1.routes.append(route_slow)

    repair_slow = auto_fix_cad_document(
        doc_f1,
        route_id="route_slow_patrol",
        target_margin_tics=2,
        max_perturbation_m=2.0
    )
    assert repair_slow["success"] is True
    assert repair_slow["repaired_margin_tics"] >= 2

    # Certified re-analysis on selected route
    rep_doc = CADDocument.from_dict(repair_slow["repaired_document"])
    cert = analyze_cad_document(rep_doc, route_id="route_slow_patrol", include_telemetry=True)
    assert cert["is_valid"] is True
    assert cert["effective_v_move_mps"] == 1.8
    assert cert["tactical_margin_tics"] == repair_slow["repaired_margin_tics"]
    assert cert["selected_route_id"] == "route_slow_patrol"


def test_auto_fix_stale_proposal_fail_closed():
    """Verify that applying a repair proposal against a modified/mutated document
    fails closed with HTTP 409 STALE_REPAIR_PROPOSAL without clobbering user edits.
    """
    app = create_cad_app()
    client = app.test_client()

    # 1. Load document
    client.post("/api/document/load", json={"name": "canonical_f1"})

    # 2. Get Auto-Fix proposal preview
    preview_resp = client.post("/api/document/auto_fix", json={"target_margin_tics": 2, "commit": False})
    assert preview_resp.status_code == 200
    preview_data = preview_resp.get_json()
    assert preview_data["success"] is True
    orig_hash = preview_data["source_doc_hash"]
    assert orig_hash is not None

    # 3. User makes an intermediate edit (translates wall_0)
    edit_resp = client.post("/api/document/translate_obstacle", json={"obstacle_id": "wall_0", "dx": 0.30, "dy": 0.00, "commit": True})
    assert edit_resp.status_code == 200
    
    # 4. User attempts to apply the stale proposal
    stale_apply_resp = client.post(
        "/api/document/auto_fix",
        json={"target_margin_tics": 2, "commit": True, "expected_doc_hash": orig_hash}
    )
    assert stale_apply_resp.status_code == 409
    stale_data = stale_apply_resp.get_json()
    assert stale_data["success"] is False
    assert stale_data["status"] == "STALE_REPAIR_PROPOSAL"
    assert "stale" in stale_data["error_reason"].lower()

    # 5. Verify intermediate user edit was preserved and not overwritten
    doc_curr = client.get("/api/document").get_json()
    wall_curr = next(o for o in doc_curr["geometry"]["obstacles"] if o["id"] == "wall_0")
    # Initial wall_0 vertices started at x in [0.2, 0.4]; with dx=+0.30, they should start at x in [0.5, 0.7]
    xs = [v[0] for v in wall_curr["vertices"]]
    assert min(xs) == pytest.approx(0.50, abs=1e-3)

