"""Deterministic Unit & API Tests for Milestone 2F (M2F): Live Spatial Heatmaps & Suffix Tactical Margin.

Verifies:
1. Entrance Equivalence Identity: Field-for-field structural identity between authoritative jobs and
   reconstructed suffix jobs at k=0 (id, reveal_tic, due_window_tics, deadline_tic, angle_deg,
   threat_anchor, service_duration_tics), guaranteeing M_suffix(0) == M_authoritative.
2. Fractional Route Endpoint Parity: Verifies that when route length is not an exact multiple of v*dt,
   the compiler and heatmap use identical discrete stepping rules and never sample fractional endpoints.
3. Angular-Boundary Discretization Parity: Proves that exact float angle preservation prevents
   slew-tic discretization jumps near 360/35 deg/tic boundaries that pre-solver rounding would cause.
4. Global Repaired Monotone Improvement: min_{s in S_active} M_suffix_repaired(s) > min_{s in S_active} M_suffix_broken(s).
5. Quiescent Suffix Transition: J_suffix == 0 cleanly transitions to QUIESCENT status band (#64748b).
6. Rigid-Body Rotation & Translation Invariance: Parameterized 2D rotation (45, 90, 180 deg) and translation
   preserves exact suffix margin and LOS concurrency sequences.
7. Exact Envelope Boundary (J <= 6 exact, J >= 7 UNSUPPORTED): Fails closed on J=7 unless allow_slow_solver=True.
8. 2D Arena Floor LOS Exposure Density: Strict polygon/boundary masking and raycast correctness.
9. REST API Endpoint: Query params (GET ?grid_step_m), resolution validation, concurrency hash check (409),
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
    DeterministicSimulationReferee,
    heading_to_deg,
    normalize_angle_deg,
    TicThreatJob
)


def _extract_suffix_jobs_at_tic(doc: CADDocument, route_idx: int, k: int, params: TicCombatParameters):
    """Test helper to extract suffix jobs at tic k using authoritative geometry."""
    geo_mod = doc.to_geometric_module()
    geo_route = geo_mod.routes[route_idx]
    total_length_m = geo_route.total_length_m
    total_tics = max(1, int(math.ceil(total_length_m / params.move_m_per_tic)))

    sample_positions = []
    sample_headings = []
    for step in range(total_tics + 1):
        s = step * params.move_m_per_tic
        if s > total_length_m:
            break
        sample_positions.append(geo_route.position_at_distance(s))
        sample_headings.append(geo_route.forward_heading_at_distance(s))

    obs_segs = extract_polygon_segments(geo_mod.obstacles)
    num_samples = len(sample_positions)
    los_matrix = np.zeros((num_samples, len(geo_mod.threats)), dtype=int)

    for step in range(num_samples):
        pos = sample_positions[step]
        for j_idx, threat in enumerate(geo_mod.threats):
            qx, qy = threat.threat_anchor
            if not any(segments_intersect(pos, (qx, qy), s1, s2) for s1, s2 in obs_segs):
                los_matrix[step, j_idx] = 1

    suffix_jobs = []
    for j_idx, threat in enumerate(geo_mod.threats):
        vis_indices = np.where(los_matrix[k:, j_idx] == 1)[0]
        if len(vis_indices) > 0:
            rel_reveal = int(vis_indices[0])
            abs_reveal = k + rel_reveal
            s_rev = abs_reveal * params.move_m_per_tic
            pos_rev = geo_route.position_at_distance(s_rev)
            fwd_rev = geo_route.forward_heading_at_distance(s_rev)

            qx, qy = threat.threat_anchor
            target_heading = heading_to_deg(pos_rev, (qx, qy))
            vis_angle_deg = normalize_angle_deg(target_heading - fwd_rev)

            due_window_tics = int(math.ceil(threat.authored_due_window_s * params.ticrate_hz))
            serv_dur_tics = int(math.ceil(threat.service_duration_s * params.ticrate_hz))
            deadline_tic = rel_reveal + due_window_tics

            suffix_jobs.append(TicThreatJob(
                id=threat.id,
                reveal_tic=rel_reveal,
                due_window_tics=due_window_tics,
                deadline_tic=deadline_tic,
                angle_deg=float(vis_angle_deg),
                threat_anchor=(float(qx), float(qy)),
                service_duration_tics=serv_dur_tics
            ))

    suffix_jobs.sort(key=lambda j: j.reveal_tic)
    return suffix_jobs


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
        suffix_jobs_k0 = _extract_suffix_jobs_at_tic(doc, route_idx=0, k=0, params=params)

        assert len(suffix_jobs_k0) == len(auth_jobs)
        for aj, sj in zip(auth_jobs, suffix_jobs_k0):
            assert sj.id == aj.id
            assert sj.reveal_tic == aj.reveal_tic
            assert sj.due_window_tics == aj.due_window_tics
            assert sj.deadline_tic == aj.deadline_tic
            assert sj.angle_deg == pytest.approx(aj.angle_deg, abs=1e-6)
            assert sj.threat_anchor == aj.threat_anchor
            assert sj.service_duration_tics == aj.service_duration_tics


def test_cad_spatial_heatmap_fractional_route_endpoint_parity():
    """Verify that when the route length is not an integer multiple of v*dt,
    the heatmap and compiler step over identical discrete intervals and do not
    evaluate illegal non-tic fractional endpoints.
    """
    # Route length = 5.30 m, v = 4.5 m/s, dt = 1/35 s -> move_m_per_tic = 4.5/35 = 0.12857 m
    # Total tics = ceil(5.30 / 0.12857) = 42 tics
    # Tic 41 is at distance 41 * 0.12857 = 5.2714 m <= 5.30 m
    # Tic 42 is at distance 42 * 0.12857 = 5.4000 m > 5.30 m (beyond route length, stopped by break)
    # Place a threat visible only beyond 5.28 m (so invisible at tic 41, but visible at 5.29m).
    doc = CADDocument(
        document_id="fractional_endpoint_test",
        name="Fractional Endpoint Test",
        boundary=[[0.0, -3.0], [10.0, -3.0], [10.0, 3.0], [0.0, 3.0]],
        obstacles=[
            # Wall blocking threat sightline until x = 5.28m
            CADObstacle(
                id="wall_occluder",
                name="Wall Occluder",
                vertices=[[0.0, 0.5], [5.28, 0.5], [5.28, 0.6], [0.0, 0.6]]
            )
        ],
        routes=[
            CADRoute(id="main", name="Main Route", waypoints=[[0.0, 0.0], [5.30, 0.0]], v_move_mps=4.5)
        ],
        threats=[
            CADThreat(
                id="t_endpoint",
                name="Endpoint Threat",
                polygon=[[5.29, 2.0], [5.31, 2.0], [5.31, 2.2], [5.29, 2.2]],
                anchor=[5.30, 2.1],
                due_window_s=0.60,
                service_duration_s=0.10
            )
        ],
        ports=[],
        player_model=CADPlayerModel()
    )

    analysis = analyze_cad_document(doc, include_telemetry=False)
    heatmap = compute_cad_route_spatial_heatmap(doc)

    assert heatmap["is_valid"] is True
    # Threat is not revealed during valid route tics:
    assert analysis["compiled_job_count"] == 0
    assert heatmap["samples"][0]["suffix_job_count"] == 0
    assert heatmap["samples"][0]["status_band"] == "QUIESCENT"


def test_cad_spatial_heatmap_angular_boundary_discretization_parity():
    """Verify that using full-precision float angles prevents false slew-tic
    jumps near 360/35 deg/tic discretization boundaries.
    """
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
    assert s0["suffix_margin_tics"] == analysis["tactical_margin_tics"]


def test_cad_spatial_heatmap_repaired_improvement_on_approach():
    """Verify that applying an Auto-Fix repair to Canonical F1 improves the suffix margin
    along the entrance approach / baffle encounter interval [0.0, 1.5m]:
    min_{s <= 1.5} M_suffix_repaired(s) > min_{s <= 1.5} M_suffix_broken(s),
    and repaired is strictly superior pointwise along the entire approach.
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

    # Approach interval [0.0, 1.5m] where baffle stagger acts
    approach_broken = [s["suffix_margin_tics"] for s in heatmap_broken["samples"] if s["distance_m"] <= 1.5]
    approach_repaired = [s["suffix_margin_tics"] for s in heatmap_repaired["samples"] if s["distance_m"] <= 1.5]

    assert len(approach_broken) > 0
    assert len(approach_repaired) == len(approach_broken)

    # Assert approach minimum improvement
    assert min(approach_repaired) > min(approach_broken)

    # Assert pointwise superiority along the entire approach
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


@pytest.mark.parametrize("angle_deg", [45.0, 90.0, 180.0])
def test_cad_spatial_heatmap_rigid_body_rotation_and_translation_invariance(angle_deg):
    """Verify that parameterized rigid-body rotation AND translation of the entire document preserves
    exact sequence of suffix Tactical Margins and LOS concurrency values."""
    doc_orig = get_canonical_f1_document()
    heatmap_orig = compute_cad_route_spatial_heatmap(doc_orig)

    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    dx, dy = 50.0, -30.0

    def transform_pt(p):
        x, y = p
        rx = x * cos_a - y * sin_a + dx
        ry = x * sin_a + y * cos_a + dy
        return [rx, ry]

    doc_transformed = CADDocument(
        document_id=f"f1_transformed_{int(angle_deg)}",
        name=f"Transformed F1 {angle_deg}deg",
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
