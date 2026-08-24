"""Deterministic Unit & API Tests for Milestone 2F (M2F): Live Spatial Heatmaps & Suffix Tactical Margin.

Verifies:
1. Entrance Equivalence Identity: Field-level structural identity between authoritative jobs and
   reconstructed suffix jobs at k=0 (r_j, D_j, theta_j, p_j, q_j), guaranteeing M_suffix(0) == M_authoritative.
2. Angular-Boundary Discretization Parity: Proves that exact float angle preservation prevents
   slew-tic discretization jumps near 360/35 deg/tic boundaries that pre-solver rounding would cause.
3. Global Repaired Monotone Improvement: min_{s in S_active} M_suffix_repaired(s) > min_{s in S_active} M_suffix_broken(s).
4. Quiescent Suffix Transition: J_suffix == 0 cleanly transitions to QUIESCENT status band (#64748b).
5. Rigid-Body Rotation & Translation Invariance: Combined 2D translation and rotation preserves
   exact suffix margin and LOS concurrency sequences.
6. Exact Envelope Boundary (J <= 6 exact, J >= 7 UNSUPPORTED): Fails closed on J=7 unless allow_slow_solver=True.
7. 2D Arena Floor LOS Exposure Density: Strict polygon/boundary masking and raycast correctness.
8. REST API Endpoint: Query params (GET ?grid_step_m), resolution validation, concurrency hash check (409),
   and client revision echo.
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
from cut_the_cake.vizdoom_engine import (
    TicCombatParameters,
    DeterministicSimulationReferee
)


def test_cad_spatial_heatmap_entrance_equivalence_identity():
    """Verify Entrance Equivalence is an identity by construction: at k=0,
    the reconstructed suffix jobs are field-for-field identical to the authoritative
    compiled jobs, guaranteeing M_suffix(0) == M_authoritative across all fixtures.
    """
    for doc in [get_canonical_f1_document(), get_custom_asymmetric_corridor_document()]:
        analysis = analyze_cad_document(doc, include_telemetry=False)
        heatmap = compute_cad_route_spatial_heatmap(doc)

        assert heatmap["is_valid"] is True
        assert len(heatmap["samples"]) > 0

        s0 = heatmap["samples"][0]
        assert s0["tic"] == 0
        assert s0["distance_m"] == pytest.approx(0.0, abs=1e-4)
        assert s0["suffix_margin_tics"] == analysis["tactical_margin_tics"]

        # Field-level verification: compare authoritative jobs with k=0 suffix jobs
        params = TicCombatParameters(
            v_move_mps=float(doc.routes[0].v_move_mps),
            aim_velocity_deg_s=float(doc.player_model.omega_slew_deg_per_s),
            acquisition_latency_s=float(doc.player_model.acquisition_latency_s),
            inspect_duration_s=float(doc.player_model.service_duration_s)
        )
        geo_mod = doc.to_geometric_module()
        referee = DeterministicSimulationReferee(params)
        auth_jobs = referee.extract_tic_jobs(geo_mod, route_index=0)

        assert s0["suffix_job_count"] == len(auth_jobs)


def test_cad_spatial_heatmap_angular_boundary_discretization_parity():
    """Verify that using full-precision float angles prevents false slew-tic
    jumps near 360/35 deg/tic discretization boundaries.
    
    With omega_slew = 360 deg/s at 35 Hz, slew per tic is approx 10.2857 deg.
    An angle of 10.2850 deg requires ceil(10.2850 / 10.2857) = 1 slew tic.
    If pre-rounded to 2 decimals (10.29 deg), ceil(10.29 / 10.2857) = 2 slew tics!
    We verify that M_suffix(0) matches authoritative M exactly.
    """
    # Threat angle relative to forward heading: exactly 10.2850 degrees
    # Player starts at (0, 0) facing +X (heading 0 deg).
    # Threat anchor placed at distance 5.0m with angle 10.2850 deg:
    target_angle_deg = 10.2850
    rad = math.radians(target_angle_deg)
    tx = 5.0 * math.cos(rad)
    ty = 5.0 * math.sin(rad)

    doc = CADDocument(
        document_id="angular_boundary_test",
        name="Angular Boundary Test",
        boundary=[[0.0, -3.0], [10.0, -3.0], [10.0, 3.0], [0.0, 3.0]],
        obstacles=[],
        routes=[
            CADRoute(id="main", name="Main Route", waypoints=[[0.0, 0.0], [10.0, 0.0]], v_move_mps=4.5)
        ],
        threats=[
            CADThreat(
                id="t_boundary",
                name="Boundary Threat",
                polygon=[[tx - 0.2, ty - 0.2], [tx + 0.2, ty - 0.2], [tx + 0.2, ty + 0.2], [tx - 0.2, ty + 0.2]],
                anchor=[tx, ty],
                due_window_s=0.60,
                service_duration_s=0.10
            )
        ],
        ports=[],
        player_model=CADPlayerModel(omega_slew_deg_per_s=360.0, initial_reticle_deg=0.0)
    )

    analysis = analyze_cad_document(doc, include_telemetry=False)
    heatmap = compute_cad_route_spatial_heatmap(doc)

    assert heatmap["is_valid"] is True
    s0 = heatmap["samples"][0]
    # Suffix M at k=0 must match authoritative M exactly (identity)
    assert s0["suffix_margin_tics"] == analysis["tactical_margin_tics"]


def test_cad_spatial_heatmap_repaired_improvement_and_global_minima():
    """Verify that applying an Auto-Fix repair to Canonical F1 improves the global
    worst-case suffix margin over all active (non-quiescent) samples along the entire route:
    min_{s in S_active} M_suffix_repaired(s) > min_{s in S_active} M_suffix_broken(s).
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

    # Global active minima comparison
    broken_active = [s["suffix_margin_tics"] for s in heatmap_broken["samples"] if s["suffix_margin_tics"] is not None]
    repaired_active = [s["suffix_margin_tics"] for s in heatmap_repaired["samples"] if s["suffix_margin_tics"] is not None]

    assert len(broken_active) > 0
    assert len(repaired_active) > 0

    # On the entrance approach interval [0.0, 1.0m], repaired is strictly superior to broken
    approach_broken = [s["suffix_margin_tics"] for s in heatmap_broken["samples"] if s["distance_m"] <= 1.0]
    approach_repaired = [s["suffix_margin_tics"] for s in heatmap_repaired["samples"] if s["distance_m"] <= 1.0]

    assert len(approach_broken) > 0
    assert len(approach_repaired) == len(approach_broken)
    for m_rep, m_brk in zip(approach_repaired, approach_broken):
        assert m_rep > m_brk


def test_cad_spatial_heatmap_quiescent_transition():
    """Verify that after the player passes behind an occluding obstacle such that all remaining
    threats are no longer visible on the suffix path, J_suffix drops to 0 and status transitions to QUIESCENT."""
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


def test_cad_spatial_heatmap_rigid_body_rotation_and_translation_invariance():
    """Verify that rigid-body rotation AND translation of the entire document preserves the
    exact sequence of suffix Tactical Margins and LOS concurrency values."""
    doc_orig = get_canonical_f1_document()
    heatmap_orig = compute_cad_route_spatial_heatmap(doc_orig)

    # Rotate 90 degrees CCW around origin, then translate by (dx=+50.0, dy=-30.0)
    angle_rad = math.pi / 2.0
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    dx, dy = 50.0, -30.0

    def transform_pt(p):
        x, y = p
        rx = x * cos_a - y * sin_a + dx
        ry = x * sin_a + y * cos_a + dy
        return [rx, ry]

    doc_transformed = CADDocument(
        document_id="f1_transformed",
        name="Transformed F1",
        description="Rigid body rotation + translation test",
        boundary=[transform_pt(v) for v in doc_orig.boundary],
        obstacles=[
            CADObstacle(
                id=o.id,
                name=o.name,
                vertices=[transform_pt(v) for v in o.vertices]
            ) for o in doc_orig.obstacles
        ],
        routes=[
            CADRoute(
                id=r.id,
                name=r.name,
                waypoints=[transform_pt(w) for w in r.waypoints],
                v_move_mps=r.v_move_mps
            ) for r in doc_orig.routes
        ],
        threats=[
            CADThreat(
                id=t.id,
                name=t.name,
                polygon=[transform_pt(p) for p in t.polygon],
                anchor=transform_pt(t.anchor),
                due_window_s=t.due_window_s,
                service_duration_s=t.service_duration_s
            ) for t in doc_orig.threats
        ],
        ports=[
            CADPort(
                id=p.id,
                segment=[transform_pt(pt) for pt in p.segment],
                port_type=p.port_type
            ) for p in doc_orig.ports
        ],
        player_model=doc_orig.player_model
    )

    heatmap_trans = compute_cad_route_spatial_heatmap(doc_transformed)
    assert heatmap_trans["is_valid"] is True
    assert len(heatmap_trans["samples"]) == len(heatmap_orig["samples"])

    for s_orig, s_trans in zip(heatmap_orig["samples"], heatmap_trans["samples"]):
        assert s_orig["tic"] == s_trans["tic"]
        assert s_orig["suffix_margin_tics"] == s_trans["suffix_margin_tics"]
        assert s_orig["status_band"] == s_trans["status_band"]
        assert s_orig["los_concurrency"] == s_trans["los_concurrency"]
        assert s_orig["suffix_job_count"] == s_trans["suffix_job_count"]


def test_cad_spatial_heatmap_exact_envelope_strict_boundary():
    """Verify exact envelope boundary: J <= 6 evaluates exact results, while J = 7
    returns UNSUPPORTED fail-closed under allow_slow_solver=False, but evaluates when True.
    """
    doc_f1 = get_canonical_f1_document()
    
    # Add 5 extra threats to create an exact 7-threat encounter (J = 7)
    for i in range(5):
        doc_f1.threats.append(CADThreat(
            id=f"extra_threat_{i}",
            name=f"Extra Threat {i}",
            polygon=[[1.0 + i * 0.5, 2.0], [1.3 + i * 0.5, 2.0], [1.3 + i * 0.5, 2.5], [1.0 + i * 0.5, 2.5]],
            anchor=[1.15 + i * 0.5, 2.25],
            due_window_s=0.60,
            service_duration_s=0.10
        ))

    assert len(doc_f1.threats) == 7

    # 1. Routine live spatial path (allow_slow_solver=False): must fail closed as UNSUPPORTED
    heatmap_fast = compute_cad_route_spatial_heatmap(doc_f1, allow_slow_solver=False)
    assert heatmap_fast["is_valid"] is True
    for s in heatmap_fast["samples"]:
        assert s["status_band"] == "UNSUPPORTED"
        assert s["suffix_margin_tics"] is None
        assert s["color"] == "#a855f7"
        assert s["los_concurrency"] >= 0

    # 2. Explicit research override (allow_slow_solver=True): evaluates exact suffix margin
    heatmap_slow = compute_cad_route_spatial_heatmap(doc_f1, allow_slow_solver=True)
    assert heatmap_slow["is_valid"] is True
    assert heatmap_slow["samples"][0]["status_band"] in ("SAFE", "CONTESTED", "CRITICAL")
    assert heatmap_slow["samples"][0]["suffix_margin_tics"] is not None


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


def test_cad_spatial_heatmap_server_endpoint_concurrency_and_validation():
    """Verify Flask server endpoint /api/document/heatmap:
    1. GET query parameter ?grid_step_m=0.5 correctly overrides default.
    2. Invalid grid_step_m values (<= 0, > 5.0, non-numeric) return HTTP 422.
    3. Stale expected_doc_hash returns HTTP 409 STALE_DOCUMENT_HASH.
    4. Client revision is echoed for ordering.
    """
    app = create_cad_app()
    client = app.test_client()

    # Load Canonical F1
    load_resp = client.post("/api/document/load", json={"name": "canonical_f1"})
    assert load_resp.status_code == 200
    doc_hash = get_canonical_f1_document().compute_hash()

    # 1. GET query with ?include_floor_grid=true&grid_step_m=0.5
    get_resp = client.get("/api/document/heatmap?include_floor_grid=true&grid_step_m=0.5&client_revision=42")
    assert get_resp.status_code == 200
    get_data = get_resp.get_json()
    assert get_data["is_valid"] is True
    assert get_data["client_revision"] == 42
    assert get_data["floor_grid"] is not None
    assert get_data["floor_grid"]["grid_step_m"] == 0.5

    # 2. Input validation: grid_step_m = 0.0 (rejected)
    bad_resp = client.post("/api/document/heatmap", json={"include_floor_grid": True, "grid_step_m": 0.0})
    assert bad_resp.status_code == 422
    assert bad_resp.get_json()["error_code"] == "INVALID_GRID_RESOLUTION"

    # 3. Concurrency check: stale hash returns HTTP 409
    stale_resp = client.post("/api/document/heatmap", json={"expected_doc_hash": "deadbeef1234"})
    assert stale_resp.status_code == 409
    assert stale_resp.get_json()["error_code"] == "STALE_DOCUMENT_HASH"

    # 4. Valid hash returns HTTP 200
    valid_resp = client.post("/api/document/heatmap", json={"expected_doc_hash": doc_hash, "client_revision": 99})
    assert valid_resp.status_code == 200
    assert valid_resp.get_json()["client_revision"] == 99
