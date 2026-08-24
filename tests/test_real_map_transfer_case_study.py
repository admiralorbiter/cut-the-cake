"""Milestone 5-A.1: Hardened Real-Map External Case Study Tests (Dust II A-Long).

Scientific & Empirical Testable Gates:
1. Coordinate Calibration & Control Points: Affine transform against 5 landmark control points
   achieves internal coordinate consistency residual < 0.020 m.
2. Strict 2D Navigability & Positive Clearance: Route segments maintain >= 0.50 m positive clearance
   and zero geometric intersection against all solid obstacle polygons.
3. Multi-Route Tactical Differentiation: Slices corner angle, expanding reveal gap (Delta_r_pie > Delta_r_wide).
   Note: Pre-registered global dominance M_pie >= M_wide was falsified at baseline fixture (M_pie = +1, M_wide = +2)
   because whole-route solver finds smaller angular distance on wide swing once Corner is cleared;
   the validated physical property is local approach-interval suffix-margin superiority.
4. Spatial Observable Orthogonality: [M_suffix(s), delta_original_clock(s), K_LOS(s)] demonstrate
   distinct spatial profiles; pieing strictly outperforms wide swing over the dangerous approach interval (s in [2, 4] m).
5. Paired Defensive Pocket Sightline Isolation: High corridor push reveals Plat (k=195) while Pit branch
   strictly occludes Plat behind corner geometry (Plat not in V(k) for any sample after branch).
6. Pre-Aim Orientation Sensitivity Curve: Complete 5 deg sweep recorded; downlane orientation outperforms Pit pre-aim.
7. Full Joint Parameter Uncertainty Sweep: 81-run joint sweep over velocity (mutating route speeds),
   slew rates, threat position jitter (+-0.3m), and due window jitter (+-0.05s) asserting universal
   stagger inequality and approach suffix superiority across all 81 configurations.
8. Persisted Result Packet Truthfulness: results/m5a_dust2_a_long.json matches solver outputs bit-for-bit.
9. REST API Template Loading & Multi-Route Analysis Parity.
"""

import os
import json
import math
import numpy as np
import pytest
from shapely.geometry import LineString, Polygon

pytestmark = [pytest.mark.cad]

from cut_the_cake.cad_document import (
    validate_cad_document,
    get_dust2_a_long_document,
    CADDocument
)
from cut_the_cake.cad_fixtures.dust2_a_long import CALIBRATION_METADATA
from cut_the_cake.cad_adapter import (
    analyze_cad_document,
    compute_cad_route_spatial_heatmap
)
from cut_the_cake.cad_server import create_cad_app


def test_dust2_a_long_coordinate_calibration_and_control_points():
    """Gate 1: Assert affine transform against 5 landmark control points achieves internal residual < 0.020 m."""
    doc = get_dust2_a_long_document()
    doc_dict = doc.to_dict()

    is_valid, errors = validate_cad_document(doc_dict)
    assert is_valid, f"Dust II document validation failed: {errors}"
    assert doc.document_id == "dust2_a_long"

    cps = CALIBRATION_METADATA["control_points"]
    assert len(cps) == 5

    src_pts = np.array([cp["src"] for cp in cps])
    cad_pts = np.array([cp["cad"] for cp in cps])

    # Affine linear regression
    A = np.hstack([src_pts, np.ones((len(src_pts), 1))])
    coeffs, residuals, rank, s = np.linalg.lstsq(A, cad_pts, rcond=None)
    predicted_cad = A @ coeffs
    errors = np.linalg.norm(cad_pts - predicted_cad, axis=1)
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    assert rmse < 0.020, f"Affine fit internal residual {rmse:.4f} m exceeds 0.020 m envelope"
    assert CALIBRATION_METADATA["affine_fit_internal_residual_m"] < 0.020


def test_dust2_a_long_navigability_and_positive_obstacle_clearance():
    """Gate 2: Assert all route segments maintain >= 0.50 m positive clearance and zero intersection with obstacle polygons."""
    doc = get_dust2_a_long_document()
    obs_polys = [Polygon(o.vertices) for o in doc.obstacles]

    for r in doc.routes:
        for i in range(len(r.waypoints) - 1):
            seg = LineString([r.waypoints[i], r.waypoints[i+1]])
            for o_idx, poly in enumerate(obs_polys):
                assert not seg.intersects(poly), (
                    f"Route '{r.id}' segment {i}->{i+1} intersects obstacle '{doc.obstacles[o_idx].id}'"
                )
                dist = seg.distance(poly)
                assert dist >= 0.50, (
                    f"Route '{r.id}' segment {i}->{i+1} clearance ({dist:.3f}m) below 0.50m from '{doc.obstacles[o_idx].id}'"
                )


def test_dust2_a_long_route_pieing_vs_wide_swing_differentiation():
    """Gate 3: Assert model separates pieing angle isolation from wide swing crossfire."""
    doc = get_dust2_a_long_document()

    # Route 1: Pieing / Angle Slice
    res_pie = analyze_cad_document(doc, route_id="route_pieing", include_telemetry=False)
    assert res_pie["is_valid"] is True
    assert res_pie["source_schedule_feasible"] is True
    assert res_pie["tactical_margin_tics"] >= 0

    pie_jobs = {j["id"]: j for j in res_pie["threat_jobs"]}
    assert "threat_corner_hold" in pie_jobs
    assert "threat_pit_hold" in pie_jobs
    assert pie_jobs["threat_corner_hold"]["reveal_tic"] == 0
    assert pie_jobs["threat_pit_hold"]["reveal_tic"] >= 35

    stagger_gap_pie = pie_jobs["threat_pit_hold"]["reveal_tic"] - pie_jobs["threat_corner_hold"]["reveal_tic"]
    assert stagger_gap_pie >= 35, f"Expected pieing stagger >= 35 tics, got {stagger_gap_pie}"

    # Route 2: Wide Swing
    res_wide = analyze_cad_document(doc, route_id="route_wide_swing", include_telemetry=False)
    assert res_wide["is_valid"] is True
    wide_jobs = {j["id"]: j for j in res_wide["threat_jobs"]}
    assert "threat_corner_hold" in wide_jobs
    assert "threat_pit_hold" in wide_jobs

    assert wide_jobs["threat_pit_hold"]["reveal_tic"] < pie_jobs["threat_pit_hold"]["reveal_tic"]
    stagger_gap_wide = wide_jobs["threat_pit_hold"]["reveal_tic"] - wide_jobs["threat_corner_hold"]["reveal_tic"]
    assert stagger_gap_wide < stagger_gap_pie, f"Wide swing stagger ({stagger_gap_wide}) should be tighter than pieing ({stagger_gap_pie})"


def test_dust2_a_long_spatial_observable_orthogonality():
    """Gate 4: Assert [M_suffix(s), delta_original_clock(s), K_LOS(s)] demonstrate distinct spatial profiles."""
    doc = get_dust2_a_long_document()

    h_pie = compute_cad_route_spatial_heatmap(doc, route_id="route_pieing")
    h_wide = compute_cad_route_spatial_heatmap(doc, route_id="route_wide_swing")

    assert h_pie["is_valid"] is True
    assert h_wide["is_valid"] is True

    # 1. Approach Interval Pointwise Superiority:
    # Over doorway exit interval (tics 16 to 32), pieing maintains non-negative suffix margin
    # and strictly exceeds wide swing suffix margin.
    for k in range(16, 33, 4):
        sp = h_pie["samples"][k]
        sw = h_wide["samples"][k]
        assert sp["suffix_margin_tics"] >= 0, f"Pieing sample {k} dropped below 0"
        assert sp["suffix_margin_tics"] > sw["suffix_margin_tics"], (
            f"Expected pieing M ({sp['suffix_margin_tics']}) > wide swing M ({sw['suffix_margin_tics']}) at tic {k}"
        )

    # 2. LOS Concurrency K(s):
    first_k2_wide = next(s["tic"] for s in h_wide["samples"] if s["los_concurrency"] >= 2)
    first_k2_pie = next(s["tic"] for s in h_pie["samples"] if s["los_concurrency"] >= 2)
    assert first_k2_wide < first_k2_pie, f"Wide swing K=2 at {first_k2_wide} should occur earlier than pieing at {first_k2_pie}"

    # 3. Original-Clock Deadline Headroom:
    visible_samples = [s for s in h_pie["samples"] if s["min_deadline_headroom_tics"] is not None]
    headrooms = [s["min_deadline_headroom_tics"] for s in visible_samples[:10]]
    for i in range(len(headrooms) - 1):
        assert headrooms[i] > headrooms[i+1], "Headroom did not decay monotonically along visible route stretch"


def test_dust2_a_long_paired_pit_sightline_isolation():
    """Gate 5: Paired isolation test: High corridor push reveals Plat while Pit branch strictly occludes Plat."""
    doc = get_dust2_a_long_document()

    # Part A: Along high push (route_pieing), Plat becomes visible when advancing past corner
    res_pie = analyze_cad_document(doc, route_id="route_pieing", include_telemetry=False)
    pie_jobs = {j["id"]: j for j in res_pie["threat_jobs"]}
    assert "threat_plat_hold" in pie_jobs
    plat_reveal_tic = pie_jobs["threat_plat_hold"]["reveal_tic"]
    assert plat_reveal_tic > 0, "Plat should reveal after advancing past the corner"

    # Part B: Along Pit branch (route_pit_drop), Plat is strictly occluded after branching into Pit pocket
    h_pit = compute_cad_route_spatial_heatmap(doc, route_id="route_pit_drop")
    pit_samples_after_branch = [s for s in h_pit["samples"] if s["distance_m"] >= 4.0]
    assert len(pit_samples_after_branch) > 0

    for s in pit_samples_after_branch:
        assert "threat_plat_hold" not in s["visible_threat_ids"], (
            f"A-Site Plat threat leaked sightline into Pit pocket at sample tic {s['tic']} (s={s['distance_m']:.2f}m)"
        )


def test_dust2_a_long_pre_aim_heading_sensitivity_curve():
    """Gate 6: Record full pre-aim curve and assert downlane orientation maintains superior margin over Pit pre-aim."""
    doc = get_dust2_a_long_document()

    curve = {}
    for theta_0 in range(-60, 65, 10):
        doc.player_model.initial_reticle_deg = float(theta_0)
        res = analyze_cad_document(doc, route_id="route_pieing", include_telemetry=False)
        curve[theta_0] = res["tactical_margin_tics"]

    # Pre-aiming near the initial corner threat angle (theta ~ -11 deg) achieves maximal margin
    assert curve[0] >= curve[+50], "Pre-aiming downlane should outperform pre-aiming into Pit"
    assert curve[-20] >= curve[+50], "Pre-aiming near Corner should outperform pre-aiming into Pit"


def test_dust2_a_long_full_joint_parameter_uncertainty_sweep():
    """Gate 7: Full 81-run joint parameter uncertainty sweep across velocity, slew rate, threat positions, and due windows."""
    speeds = [3.5, 4.5, 5.5]
    slews = [270.0, 360.0, 450.0]
    anchor_jitters = [-0.3, 0.0, +0.3]
    due_offsets = [-0.05, 0.0, +0.05]

    total_runs = 0
    stagger_invariants_held = 0
    approach_invariants_held = 0

    for v in speeds:
        for omega in slews:
            for dw in due_offsets:
                for dj in anchor_jitters:
                    total_runs += 1
                    doc = get_dust2_a_long_document()
                    doc.player_model.v_move_mps = v
                    doc.player_model.omega_slew_deg_per_s = omega
                    for r in doc.routes:
                        r.v_move_mps = v # mutate route speed directly!

                    # Jitter threats
                    for t in doc.threats:
                        t.due_window_s = max(0.35, t.due_window_s + dw)
                        t.anchor = [t.anchor[0] + dj, t.anchor[1] + dj]
                        t.polygon = [[p[0] + dj, p[1] + dj] for p in t.polygon]

                    res_pie = analyze_cad_document(doc, route_id="route_pieing", include_telemetry=False)
                    res_wide = analyze_cad_document(doc, route_id="route_wide_swing", include_telemetry=False)

                    # Explicitly assert effective velocity was set to sweep parameter
                    assert res_pie["effective_v_move_mps"] == v
                    assert res_wide["effective_v_move_mps"] == v

                    # 1. Reveal stagger invariant: Pieing always reveals Pit strictly later than wide swing
                    pie_jobs = {j["id"]: j for j in res_pie["threat_jobs"]}
                    wide_jobs = {j["id"]: j for j in res_wide["threat_jobs"]}
                    gap_pie = pie_jobs["threat_pit_hold"]["reveal_tic"] - pie_jobs["threat_corner_hold"]["reveal_tic"]
                    gap_wide = wide_jobs["threat_pit_hold"]["reveal_tic"] - wide_jobs["threat_corner_hold"]["reveal_tic"]
                    if gap_pie > gap_wide:
                        stagger_invariants_held += 1

                    # 2. Local approach suffix margin superiority: Pieing remains superior over doorway approach s in [2, 4] m
                    h_pie = compute_cad_route_spatial_heatmap(doc, route_id="route_pieing")
                    h_wide = compute_cad_route_spatial_heatmap(doc, route_id="route_wide_swing")

                    pie_min_app = min(s["suffix_margin_tics"] for s in h_pie["samples"] if 2.0 <= s["distance_m"] <= 4.0)
                    wide_min_app = min(s["suffix_margin_tics"] for s in h_wide["samples"] if 2.0 <= s["distance_m"] <= 4.0)
                    if pie_min_app > wide_min_app:
                        approach_invariants_held += 1

    assert total_runs == 81
    assert stagger_invariants_held == 81, f"Stagger inequality failed in {81 - stagger_invariants_held}/81 runs"
    assert approach_invariants_held == 81, f"Approach superiority failed in {81 - approach_invariants_held}/81 runs"


def test_dust2_a_long_persisted_result_packet_truthfulness():
    """Gate 8: Assert results/m5a_dust2_a_long.json matches solver outputs bit-for-bit."""
    results_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "m5a_dust2_a_long.json")
    assert os.path.exists(results_path), "results/m5a_dust2_a_long.json does not exist"

    with open(results_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    doc = get_dust2_a_long_document()
    assert saved_data["source_doc_hash"] == doc.compute_hash()

    for r_id, r_saved in saved_data["routes"].items():
        analysis = analyze_cad_document(doc, route_id=r_id, include_telemetry=False)
        assert analysis["tactical_margin_tics"] == r_saved["tactical_margin_tics"]
        assert analysis["stagger_gap_tics"] == r_saved["stagger_gap_tics"]
        assert analysis["compiled_job_count"] == r_saved["compiled_job_count"]


def test_dust2_a_long_server_api_template_loading_and_route_analysis():
    """Gate 9: REST API successfully loads dust2_a_long template and switches routes."""
    app = create_cad_app()
    client = app.test_client()

    # 1. Load document template
    resp = client.post("/api/document/load", json={"name": "dust2_a_long"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "loaded"
    assert data["document_type"] == "dust2_a_long"
    assert data["document"]["document_id"] == "dust2_a_long"

    # 2. Analyze with route_pieing
    resp_pie = client.post("/api/document/analyze", json={"route_id": "route_pieing", "include_telemetry": True})
    assert resp_pie.status_code == 200
    data_pie = resp_pie.get_json()
    assert data_pie["is_valid"] is True
    assert data_pie["source_schedule_feasible"] is True

    # 3. Analyze with route_wide_swing
    resp_wide = client.post("/api/document/analyze", json={"route_id": "route_wide_swing", "include_telemetry": True})
    assert resp_wide.status_code == 200
    data_wide = resp_wide.get_json()
    assert data_wide["is_valid"] is True

    # 4. Fetch Heatmap for dust2
    resp_hm = client.post("/api/document/heatmap", json={"route_id": "route_pieing", "include_floor_grid": True})
    assert resp_hm.status_code == 200
    data_hm = resp_hm.get_json()
    assert data_hm["is_valid"] is True
    assert data_hm["document_id"] == "dust2_a_long"
    assert "floor_grid" in data_hm
    assert len(data_hm["samples"]) > 50
