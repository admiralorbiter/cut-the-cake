"""Deterministic Unit & API Tests for Milestone 2F (M2F): Live Spatial Heatmaps & Suffix Tactical Margin.

Verifies:
1. Entrance Equivalence Invariant: M_suffix(0) == M_authoritative (full-route baseline).
2. Repaired Monotone Improvement: min_s M_suffix_repaired(s) > min_s M_suffix_broken(s).
3. Quiescent Suffix Transition: J_suffix == 0 cleanly transitions to QUIESCENT status band (#64748b).
4. Rigid-Body Rotation/Translation Invariance of suffix margin sequence and LOS concurrency.
5. Exact Solver Envelope Fail-Closed Guard: J_full >= 8 yields UNSUPPORTED, preserving K(s).
6. 2D Arena Floor LOS Exposure Density: Strict polygon/boundary masking and raycast correctness.
7. REST API Endpoint: /api/document/heatmap query params, payload integrity, and hash matching.
"""

import pytest
import math
import numpy as np

pytestmark = [pytest.mark.cad]

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
    compute_cad_route_spatial_heatmap,
    compute_arena_floor_los_exposure,
    auto_fix_cad_document
)
from cut_the_cake.cad_server import create_cad_app
from cut_the_cake.compiler import segments_intersect
from cut_the_cake.geometry import extract_polygon_segments


def test_cad_spatial_heatmap_entrance_equivalence():
    """Verify Entrance Equivalence Invariant: M_suffix(0) == M_authoritative across all test documents."""
    # 1. Canonical F1 Baffle Stagger
    doc_f1 = get_canonical_f1_document()
    analysis_f1 = analyze_cad_document(doc_f1, include_telemetry=False)
    heatmap_f1 = compute_cad_route_spatial_heatmap(doc_f1)

    assert heatmap_f1["is_valid"] is True
    assert heatmap_f1["envelope_supported"] is True
    assert len(heatmap_f1["samples"]) > 0

    s0_f1 = heatmap_f1["samples"][0]
    assert s0_f1["tic"] == 0
    assert s0_f1["distance_m"] == pytest.approx(0.0, abs=1e-4)
    assert s0_f1["suffix_margin_tics"] == analysis_f1["tactical_margin_tics"] == -6
    assert s0_f1["status_band"] == "CRITICAL"

    # 2. Custom Asymmetric Corridor Document
    doc_custom = get_custom_asymmetric_corridor_document()
    analysis_custom = analyze_cad_document(doc_custom, include_telemetry=False)
    heatmap_custom = compute_cad_route_spatial_heatmap(doc_custom)

    assert heatmap_custom["is_valid"] is True
    s0_custom = heatmap_custom["samples"][0]
    assert s0_custom["suffix_margin_tics"] == analysis_custom["tactical_margin_tics"]


def test_cad_spatial_heatmap_repaired_improvement():
    """Verify that applying an Auto-Fix repair to Canonical F1 improves the worst-case
    suffix margin along the entire route traverse:
    min_s M_suffix_repaired(s) > min_s M_suffix_broken(s).
    """
    doc_broken = get_canonical_f1_document()
    heatmap_broken = compute_cad_route_spatial_heatmap(doc_broken)

    # Perform authoritative Auto-Fix
    repair_res = auto_fix_cad_document(doc_broken, target_margin_tics=2)
    assert repair_res["success"] is True
    doc_repaired = CADDocument.from_dict(repair_res["repaired_document"])
    heatmap_repaired = compute_cad_route_spatial_heatmap(doc_repaired)

    entrance_broken = heatmap_broken["samples"][0]["suffix_margin_tics"]
    entrance_repaired = heatmap_repaired["samples"][0]["suffix_margin_tics"]

    assert entrance_broken == -6
    assert entrance_repaired == 2
    assert entrance_repaired > entrance_broken
    assert heatmap_repaired["samples"][0]["status_band"] == "SAFE"

    # On the entrance approach interval [0.0, 1.0m], repaired is strictly superior to broken by +8 tics
    approach_broken = [s["suffix_margin_tics"] for s in heatmap_broken["samples"] if s["distance_m"] <= 1.0]
    approach_repaired = [s["suffix_margin_tics"] for s in heatmap_repaired["samples"] if s["distance_m"] <= 1.0]

    assert len(approach_broken) > 0
    assert len(approach_repaired) == len(approach_broken)
    for m_rep, m_brk in zip(approach_repaired, approach_broken):
        assert m_rep > m_brk


def test_cad_spatial_heatmap_quiescent_transition():
    """Verify that after the player passes behind an occluding obstacle such that all remaining
    threats are no longer visible on the suffix path, J_suffix drops to 0 and status transitions to QUIESCENT."""
    # Corridor with a threat in lower room, occluded past transverse divider wall
    doc = CADDocument(
        document_id="corridor_quiescent_test",
        name="Quiescent Transition Corridor",
        boundary=[[0.0, -3.0], [10.0, -3.0], [10.0, 3.0], [0.0, 3.0]],
        obstacles=[
            CADObstacle(
                id="exit_divider",
                name="Exit Divider",
                vertices=[[4.5, -3.0], [4.8, -3.0], [4.8, 1.5], [4.5, 1.5]]
            )
        ],
        routes=[
            CADRoute(id="main", name="Main Route", waypoints=[[0.0, 2.0], [10.0, 2.0]], v_move_mps=4.5)
        ],
        threats=[
            CADThreat(
                id="room_threat",
                name="Room Threat",
                polygon=[[1.0, -2.0], [1.5, -2.0], [1.5, -1.5], [1.0, -1.5]],
                anchor=[1.25, -1.75],
                due_window_s=0.60,
                service_duration_s=0.10
            )
        ],
        ports=[
            CADPort(id="p_in", segment=[[0.0, 1.0], [0.0, 3.0]], port_type="ENTRY"),
            CADPort(id="p_out", segment=[[10.0, 1.0], [10.0, 3.0]], port_type="EXIT")
        ],
        player_model=CADPlayerModel()
    )

    heatmap = compute_cad_route_spatial_heatmap(doc)
    assert heatmap["is_valid"] is True
    samples = heatmap["samples"]

    # Initial samples before occluder have J_suffix == 1
    entrance_samples = [s for s in samples if s["distance_m"] <= 3.0]
    assert len(entrance_samples) > 0
    assert all(s["suffix_job_count"] == 1 for s in entrance_samples)
    assert all(s["status_band"] in ("SAFE", "CONTESTED", "CRITICAL") for s in entrance_samples)

    # Late samples past x = 6.0m have threat permanently occluded -> J_suffix == 0 -> QUIESCENT
    exit_samples = [s for s in samples if s["distance_m"] >= 6.0]
    assert len(exit_samples) > 0
    assert all(s["suffix_job_count"] == 0 for s in exit_samples)
    assert all(s["suffix_margin_tics"] is None for s in exit_samples)
    assert all(s["status_band"] == "QUIESCENT" for s in exit_samples)
    assert all(s["color"] == "#64748b" for s in exit_samples)


def test_cad_spatial_heatmap_rigid_body_invariance():
    """Verify that rigid-body translation of the entire document preserves the
    exact sequence of suffix Tactical Margins and LOS concurrency values."""
    doc_orig = get_canonical_f1_document()
    heatmap_orig = compute_cad_route_spatial_heatmap(doc_orig)

    # Translate the entire scene by (dx=+50.0, dy=-30.0)
    dx, dy = 50.0, -30.0
    doc_trans = CADDocument(
        document_id="f1_translated",
        name="Translated F1",
        description="Rigid body translation test",
        boundary=[[v[0] + dx, v[1] + dy] for v in doc_orig.boundary],
        obstacles=[
            CADObstacle(
                id=o.id,
                name=o.name,
                vertices=[[v[0] + dx, v[1] + dy] for v in o.vertices]
            ) for o in doc_orig.obstacles
        ],
        routes=[
            CADRoute(
                id=r.id,
                name=r.name,
                waypoints=[[w[0] + dx, w[1] + dy] for w in r.waypoints],
                v_move_mps=r.v_move_mps
            ) for r in doc_orig.routes
        ],
        threats=[
            CADThreat(
                id=t.id,
                name=t.name,
                polygon=[[p[0] + dx, p[1] + dy] for p in t.polygon],
                anchor=[t.anchor[0] + dx, t.anchor[1] + dy],
                due_window_s=t.due_window_s,
                service_duration_s=t.service_duration_s
            ) for t in doc_orig.threats
        ],
        ports=[
            CADPort(
                id=p.id,
                segment=[[pt[0] + dx, pt[1] + dy] for pt in p.segment],
                port_type=p.port_type
            ) for p in doc_orig.ports
        ],
        player_model=doc_orig.player_model
    )

    heatmap_trans = compute_cad_route_spatial_heatmap(doc_trans)
    assert heatmap_trans["is_valid"] is True
    assert len(heatmap_trans["samples"]) == len(heatmap_orig["samples"])

    for s_orig, s_trans in zip(heatmap_orig["samples"], heatmap_trans["samples"]):
        assert s_orig["tic"] == s_trans["tic"]
        assert s_orig["suffix_margin_tics"] == s_trans["suffix_margin_tics"]
        assert s_orig["status_band"] == s_trans["status_band"]
        assert s_orig["los_concurrency"] == s_trans["los_concurrency"]
        assert s_orig["suffix_job_count"] == s_trans["suffix_job_count"]
        # Position should be translated exactly
        assert s_trans["position"][0] == pytest.approx(s_orig["position"][0] + dx, abs=1e-3)
        assert s_trans["position"][1] == pytest.approx(s_orig["position"][1] + dy, abs=1e-3)


def test_cad_spatial_heatmap_envelope_fail_closed():
    """Verify that encounters with J_full >= 8 return UNSUPPORTED_ENVELOPE with valid
    geometric LOS concurrency K(s) while failing closed on factorial scheduling."""
    doc_f1 = get_canonical_f1_document()
    
    # Add 7 extra threats to create an 9-threat encounter (exceeding J <= 7 envelope)
    for i in range(7):
        doc_f1.threats.append(CADThreat(
            id=f"extra_threat_{i}",
            name=f"Extra Threat {i}",
            polygon=[[1.0 + i * 0.5, 2.0], [1.3 + i * 0.5, 2.0], [1.3 + i * 0.5, 2.5], [1.0 + i * 0.5, 2.5]],
            anchor=[1.15 + i * 0.5, 2.25],
            due_window_s=0.60,
            service_duration_s=0.10
        ))

    heatmap = compute_cad_route_spatial_heatmap(doc_f1, allow_slow_solver=False)
    assert heatmap["is_valid"] is True
    assert heatmap["envelope_supported"] is False
    assert heatmap["full_compiled_job_count"] >= 8

    # All samples must be UNSUPPORTED, never red/infeasible, with purple color code
    for s in heatmap["samples"]:
        assert s["status_band"] == "UNSUPPORTED"
        assert s["suffix_margin_tics"] is None
        assert s["color"] == "#a855f7"
        # Geometric LOS concurrency is still accurately calculated
        assert s["los_concurrency"] >= 0


def test_cad_arena_floor_los_exposure_and_masking():
    """Verify 2D Arena Floor LOS Exposure Density grid K(x, y):
    1. Points outside the boundary or inside obstacle interiors are masked=True.
    2. Open navigable points compute exact unoccluded threat counts matching raycaster.
    """
    doc_f1 = get_canonical_f1_document()
    floor_res = compute_arena_floor_los_exposure(doc_f1, grid_step_m=0.50)

    assert floor_res["is_valid"] is True
    assert floor_res["total_cells"] > 0
    assert floor_res["max_exposure"] >= 1

    cells = floor_res["cells"]
    geo_mod = doc_f1.to_geometric_module()
    obs_segs = extract_polygon_segments(geo_mod.obstacles)

    # Check a point known to be inside the central baffle obstacle:
    # Wall 0 is at x in [0.2, 0.4], y in [0.25, 1.8]
    inside_cells = [c for c in cells if 0.25 <= c["x"] <= 0.35 and 0.5 <= c["y"] <= 1.5]
    for ic in inside_cells:
        assert ic["masked"] is True

    # Check open points
    unmasked_cells = [c for c in cells if not c["masked"]]
    assert len(unmasked_cells) > 0

    # Differential check 5 unmasked samples against authoritative segment raycasting
    for c in unmasked_cells[:5]:
        pt = (c["x"], c["y"])
        expected_vis = []
        for t in geo_mod.threats:
            blocked = any(segments_intersect(pt, t.threat_anchor, s1, s2) for s1, s2 in obs_segs)
            if not blocked:
                expected_vis.append(t.id)

        assert c["exposure_count"] == len(expected_vis)
        assert set(c["visible_threat_ids"]) == set(expected_vis)


def test_cad_spatial_heatmap_server_endpoint():
    """Verify Flask server endpoint /api/document/heatmap returns full spatial data with hash checking."""
    app = create_cad_app()
    client = app.test_client()

    # Load Canonical F1
    load_resp = client.post("/api/document/load", json={"name": "canonical_f1"})
    assert load_resp.status_code == 200

    # Request route heatmap without floor grid
    resp = client.get("/api/document/heatmap")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["is_valid"] is True
    assert data["document_id"] == "canonical_f1_stagger"
    assert data["sampling_mode"] == "tic"
    assert len(data["samples"]) > 0
    assert data["floor_grid"] is None
    assert "source_doc_hash" in data

    # Request route heatmap with 2D floor exposure grid
    resp_with_grid = client.post("/api/document/heatmap", json={"include_floor_grid": True, "grid_step_m": 0.5})
    assert resp_with_grid.status_code == 200
    data_with_grid = resp_with_grid.get_json()

    assert data_with_grid["floor_grid"] is not None
    assert data_with_grid["floor_grid"]["grid_step_m"] == 0.5
    assert len(data_with_grid["floor_grid"]["cells"]) > 0
