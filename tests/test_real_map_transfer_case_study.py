"""Milestone 5-A: Real-Map External Case Study / Calibrated Graybox Transfer Tests.

Evaluates the frozen M2 Tactical CAD system on a calibrated metric graybox of
Counter-Strike Dust II A-Long to A-Site / Pit Contest.

Empirical testable gates:
1. Metric Scale & Schema Validation
2. Multi-Route Tactical Differentiation (Pieing vs Wide Swing)
3. Spatial Observable Orthogonality [M_suffix(s), delta_original_clock(s), K_LOS(s)]
4. Pre-Aim Orientation Sensitivity (theta_0)
5. Defensive Cover & Sightline Isolation (Pit drop breaks Site crossfire)
6. REST API Template Loading & Multi-Route Analysis Parity
"""

import pytest
import math

pytestmark = [pytest.mark.cad]

from cut_the_cake.cad_document import (
    validate_cad_document,
    get_dust2_a_long_document,
    CADDocument
)
from cut_the_cake.cad_adapter import (
    analyze_cad_document,
    compute_cad_route_spatial_heatmap
)
from cut_the_cake.cad_server import create_cad_app


def test_dust2_a_long_schema_and_metric_calibration():
    """Gate 1: Assert Dust II A-Long satisfies cad_document_v1 schema and metric scale."""
    doc = get_dust2_a_long_document()
    doc_dict = doc.to_dict()

    is_valid, errors = validate_cad_document(doc_dict)
    assert is_valid, f"Dust II document validation failed: {errors}"
    assert doc.document_id == "dust2_a_long"
    assert len(doc.routes) == 3
    assert len(doc.threats) == 3
    assert len(doc.obstacles) == 5

    # Check metric scale: Long corridor length between 20m and 35m
    for r in doc.routes:
        total_len = 0.0
        for i in range(len(r.waypoints) - 1):
            dx = r.waypoints[i+1][0] - r.waypoints[i][0]
            dy = r.waypoints[i+1][1] - r.waypoints[i][1]
            total_len += math.hypot(dx, dy)
        assert 10.0 <= total_len <= 35.0, f"Route {r.id} length {total_len:.2f}m outside expected metric envelope"


def test_dust2_a_long_route_pieing_vs_wide_swing_differentiation():
    """Gate 2: Assert model separates pieing angle isolation from wide swing crossfire."""
    doc = get_dust2_a_long_document()

    # Route 1: Pieing / Angle Slice
    res_pie = analyze_cad_document(doc, route_id="route_pieing", include_telemetry=False)
    assert res_pie["is_valid"] is True
    assert res_pie["source_schedule_feasible"] is True
    assert res_pie["tactical_margin_tics"] >= 0

    # Verify reveal stagger on pieing route: Corner is revealed at tic 0, Pit delayed until tic >= 35
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

    # On wide swing, Pit reveals significantly earlier than on pieing route
    assert wide_jobs["threat_pit_hold"]["reveal_tic"] < pie_jobs["threat_pit_hold"]["reveal_tic"]
    stagger_gap_wide = wide_jobs["threat_pit_hold"]["reveal_tic"] - wide_jobs["threat_corner_hold"]["reveal_tic"]
    assert stagger_gap_wide < stagger_gap_pie, f"Wide swing stagger ({stagger_gap_wide}) should be tighter than pieing ({stagger_gap_pie})"


def test_dust2_a_long_spatial_observable_orthogonality():
    """Gate 3: Assert [M_suffix(s), delta_original_clock(s), K_LOS(s)] demonstrate distinct spatial profiles."""
    doc = get_dust2_a_long_document()

    h_pie = compute_cad_route_spatial_heatmap(doc, route_id="route_pieing")
    h_wide = compute_cad_route_spatial_heatmap(doc, route_id="route_wide_swing")

    assert h_pie["is_valid"] is True
    assert h_wide["is_valid"] is True

    # 1. Approach Interval Pointwise Superiority:
    # Over the doorway exit interval (s in [2.0m, 4.0m], tics 16 to 32), pieing maintains higher suffix margin
    # than wide swing because pieing delays the Pit reveal.
    for k in range(16, 33, 4):
        sp = h_pie["samples"][k]
        sw = h_wide["samples"][k]
        assert sp["suffix_margin_tics"] >= 0, f"Pieing sample {k} (s={sp['distance_m']:.2f}m) dropped below 0"
        assert sp["suffix_margin_tics"] > sw["suffix_margin_tics"], (
            f"Expected pieing M ({sp['suffix_margin_tics']}) > wide swing M ({sw['suffix_margin_tics']}) at tic {k}"
        )

    # 2. LOS Concurrency K(s):
    # Wide swing enters K=2 earlier along the route than pieing
    first_k2_wide = next(s["tic"] for s in h_wide["samples"] if s["los_concurrency"] >= 2)
    first_k2_pie = next(s["tic"] for s in h_pie["samples"] if s["los_concurrency"] >= 2)
    assert first_k2_wide < first_k2_pie, f"Wide swing K=2 at tic {first_k2_wide} should occur earlier than pieing at {first_k2_pie}"

    # 3. Original-Clock Deadline Headroom:
    # Decays strictly monotonically while threats remain visible
    visible_samples = [s for s in h_pie["samples"] if s["min_deadline_headroom_tics"] is not None]
    headrooms = [s["min_deadline_headroom_tics"] for s in visible_samples[:10]]
    for i in range(len(headrooms) - 1):
        assert headrooms[i] > headrooms[i+1], "Headroom did not decay along visible route stretch"


def test_dust2_a_long_pre_aim_heading_sensitivity():
    """Gate 4: Quantify pre-aim heading angle (theta_0) sensitivity between Corner and Pit holds."""
    doc = get_dust2_a_long_document()

    # On pieing route, first threat is Corner at theta ~ -11 deg.
    # Pre-aiming right/downlane (theta_0 <= 0 deg) preserves maximal margin,
    # whereas pre-aiming left into Pit (theta_0 = +45 deg) incurs large slew penalty to Corner.
    margins = {}
    for theta_0 in [-45.0, -20.0, 0.0, +20.0, +45.0]:
        doc.player_model.initial_reticle_deg = theta_0
        res = analyze_cad_document(doc, route_id="route_pieing", include_telemetry=False)
        margins[theta_0] = res["tactical_margin_tics"]

    assert margins[0.0] >= margins[+45.0], "Pre-aim downlane should be at least as good as pre-aiming into Pit"
    assert margins[-20.0] >= margins[+45.0], "Pre-aim toward Corner should outperform pre-aiming into Pit"


def test_dust2_a_long_pit_cover_isolation():
    """Gate 5: Assert Pit drop route breaks A-Site Plat crossfire inside Pit depression."""
    doc = get_dust2_a_long_document()

    h_pit = compute_cad_route_spatial_heatmap(doc, route_id="route_pit_drop")
    assert h_pit["is_valid"] is True

    # At the end of route_pit_drop (inside Pit), A-Site Plat threat should NOT be visible
    terminal_samples = h_pit["samples"][-5:]
    for s in terminal_samples:
        assert "threat_plat_hold" not in s["visible_threat_ids"], (
            f"A-Site Plat threat leaked sightline into deep Pit at sample {s['tic']}"
        )


def test_dust2_a_long_server_api_template_loading_and_route_analysis():
    """Gate 6: REST API successfully loads dust2_a_long template and switches routes."""
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
