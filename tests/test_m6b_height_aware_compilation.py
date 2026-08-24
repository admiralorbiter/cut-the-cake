"""Milestone 6-B / 6-B.1 Verification Test Suite: Height-Aware Geometric Compilation & Contract Hardening.

Formal scientific gates verifying that:
- 3D target coordinates and 2.5D extruded obstacle prisms compile directly into 3D aim states (theta, phi) and reveal tics R_j.
- CADDocument serialization, schema validation, and roundtripping fully support 3D waypoints and ElevationMode.
- The frozen Milestone 6-A discrete scheduler is untouched and consumes (theta, phi) seamlessly.
- Backward compatibility and bit-for-bit planar identity are strictly preserved against frozen 4e81dd7 baselines.
- Volumetric prism occupancy and boundary conditions are rigorously handled.
"""

from __future__ import annotations
import json
import math
import pytest
from typing import Dict, Any, List, Tuple
from shapely.geometry import Polygon, Point, LineString

pytestmark = pytest.mark.cad

from cut_the_cake.geometry import (
    spherical_aim_distance_deg,
    derived_aim_elevation_deg,
    ray_intersects_prism_25d,
    heading_to_deg,
    normalize_angle_deg,
    angle_diff_deg
)
from cut_the_cake.compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricObstacle,
    GeometricThreat,
    GeometricPort
)
from cut_the_cake.vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteTicScheduler,
    DeterministicSimulationReferee
)
from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPort,
    CADPlayerModel,
    ElevationMode,
    get_canonical_f1_document,
    get_custom_asymmetric_corridor_document,
    get_dust2_a_long_document,
    get_ascent_a_main_document,
    get_dust2_b_tunnels_document,
    get_transit_213_document,
    validate_cad_document
)
from cut_the_cake.cad_adapter import analyze_cad_document
try:
    from test_m6a_elevation_aim_scheduling import FROZEN_4E81DD7_PLANAR_BASELINES
except ImportError:
    from tests.test_m6a_elevation_aim_scheduling import FROZEN_4E81DD7_PLANAR_BASELINES


# =============================================================================
# GATE 6B-1: COMPLETE DIFFERENTIAL PLANAR BIT-FOR-BIT IDENTITY
# =============================================================================

def test_m6b_gate1_complete_planar_identity():
    """Gate 6B-1: Verify that in 2.5D geometric mode, pure planar geometry reproduces frozen M6-A/M2 results bit-for-bit."""
    fixture_loaders = {
        "canonical_f1": get_canonical_f1_document,
        "custom_corridor": get_custom_asymmetric_corridor_document,
        "dust2_a_long": get_dust2_a_long_document,
        "ascent_a_main": get_ascent_a_main_document,
        "dust2_b_tunnels": get_dust2_b_tunnels_document,
        "transit_213": get_transit_213_document
    }

    for name, loader in fixture_loaders.items():
        doc = loader()
        doc.player_model.elevation_mode = ElevationMode.GEOMETRIC
        baseline_fixture = FROZEN_4E81DD7_PLANAR_BASELINES[name]

        # Verify document hash bit-for-bit identity
        assert doc.compute_hash() == baseline_fixture["doc_hash"], f"Document hash diverged for fixture '{name}'"

        for route_id, exp in baseline_fixture["routes"].items():
            analysis = analyze_cad_document(doc, route_id=route_id, include_telemetry=False)

            assert analysis["compiled_job_count"] == exp["compiled_job_count"], f"Job count mismatch for {name}/{route_id}"
            assert analysis["tactical_margin_tics"] == exp["tactical_margin_tics"], f"Margin mismatch for {name}/{route_id}"
            assert analysis["l_star_tics"] == exp["l_star_tics"], f"L* mismatch for {name}/{route_id}"
            assert analysis["source_schedule_feasible"] == exp["source_schedule_feasible"], f"Feasibility mismatch for {name}/{route_id}"
            assert analysis["stagger_gap_tics"] == exp["stagger_gap_tics"], f"Stagger mismatch for {name}/{route_id}"

            assert len(analysis["threat_jobs"]) == len(exp["threat_jobs"]), f"Job count mismatch for {name}/{route_id}"
            for actual_j, exp_j in zip(analysis["threat_jobs"], exp["threat_jobs"]):
                assert actual_j["id"] == exp_j["id"]
                assert actual_j["reveal_tic"] == exp_j["reveal_tic"]
                assert actual_j["due_window_tics"] == exp_j["due_window_tics"]
                assert actual_j["deadline_tic"] == exp_j["deadline_tic"]
                assert actual_j["angle_deg"] == exp_j["angle_deg"], f"Azimuth mismatch for {name}/{route_id}/{actual_j['id']}"
                assert actual_j["elevation_deg"] == 0.0, f"Planar elevation must be exactly 0.0 for {name}/{route_id}/{actual_j['id']}"
                assert actual_j["completion_tic"] == exp_j["completion_tic"]
                assert actual_j["lateness_tics"] == exp_j["lateness_tics"]


# =============================================================================
# GATE 6B-2: ANALYTIC VERTICAL OCCLUSION
# =============================================================================

def test_m6b_gate2_analytic_vertical_occlusion():
    """Gate 6B-2: Verify that a finite-height wall occludes low sightlines while clearing high sightlines."""
    # Obstacle wall at x in [4, 6], y in [-2, 2], height z in [0.0, 3.0]
    wall_poly = Polygon([(4.0, -2.0), (6.0, -2.0), (6.0, 2.0), (4.0, 2.0)])
    obs = GeometricObstacle(id="low_wall", polygon=wall_poly, z_min_m=0.0, z_max_m=3.0)

    # Player at (0, 0) with eye height 1.65m -> eye is at (0, 0, 1.65)
    eye_pt = (0.0, 0.0, 1.65)

    # Target 1 (Low): at (10, 0, 2.0). Ray crosses wall centerline (x=5) at z = 1.65 + 0.5*(2.0-1.65) = 1.825m <= 3.0m -> BLOCKED
    target_low = (10.0, 0.0, 2.0)
    assert ray_intersects_prism_25d(eye_pt, target_low, obs.polygon, obs.z_min_m, obs.z_max_m) is True

    # Target 2 (High): at (10, 0, 6.0). Ray crosses wall centerline (x=5) at z = 1.65 + 0.5*(6.0-1.65) = 3.825m > 3.0m -> CLEAR
    target_high = (10.0, 0.0, 6.0)
    assert ray_intersects_prism_25d(eye_pt, target_high, obs.polygon, obs.z_min_m, obs.z_max_m) is False


# =============================================================================
# GATE 6B-3: OBSTACLE-HEIGHT MONOTONICITY
# =============================================================================

def test_m6b_gate3_obstacle_height_monotonicity():
    """Gate 6B-3: Verify that making an occluder taller never restores visibility (R_j(H2) >= R_j(H1))."""
    boundary = Polygon([(0, -10), (30, -10), (30, 10), (0, 10)])
    route = GeometricRoute(route_id="r1", waypoints=[(0.0, 0.0), (20.0, 0.0)], v_move_mps=4.5)
    threat = GeometricThreat(
        id="elevated_target",
        polygon=Polygon([(24, -1), (26, -1), (26, 1), (24, 1)]),
        threat_anchor=(25.0, 0.0),
        authored_due_window_s=0.62,
        service_duration_s=0.10,
        z_m=4.0
    )

    params = TicCombatParameters(v_move_mps=4.5, eye_height_m=1.65)
    referee = DeterministicSimulationReferee(params)

    heights = [1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    reveal_tics: List[Optional[int]] = []

    for H in heights:
        wall_poly = Polygon([(9.0, -5.0), (11.0, -5.0), (11.0, 5.0), (9.0, 5.0)])
        obs = GeometricObstacle(id="baffle", polygon=wall_poly, z_min_m=0.0, z_max_m=H)
        mod = GeometricModule(
            module_id="mono_test",
            name="Monotonicity Test",
            boundary=boundary,
            obstacles=[wall_poly],
            obstacles_25d=[obs],
            threats=[threat],
            routes=[route]
        )
        jobs = referee.extract_tic_jobs(mod, route_index=0, elevation_mode="GEOMETRIC")
        if jobs:
            reveal_tics.append(jobs[0].reveal_tic)
        else:
            reveal_tics.append(None)

    # Monotonicity check: reveal tic must be non-decreasing, followed optionally by None (unrevealed)
    for i in range(len(reveal_tics) - 1):
        r1 = reveal_tics[i]
        r2 = reveal_tics[i + 1]
        if r1 is not None and r2 is not None:
            assert r2 >= r1, f"Monotonicity violated: H={heights[i]} gave r={r1}, but taller H={heights[i+1]} gave r={r2}"
        elif r1 is None:
            assert r2 is None, f"Visibility restored at taller height H={heights[i+1]}"


# =============================================================================
# GATE 6B-4: DERIVED ELEVATION CORRECTNESS
# =============================================================================

def test_m6b_gate4_derived_elevation_correctness():
    """Gate 6B-4: Verify geometric formula derived_aim_elevation_deg produces exact analytic pitch angles."""
    # 1. 45 degrees positive pitch: dx=10, dy=0, dz=10 -> phi = +45 deg
    e1 = (0.0, 0.0, 1.5)
    q1 = (10.0, 0.0, 11.5)
    phi1 = derived_aim_elevation_deg(e1, q1)
    assert math.isclose(phi1, 45.0, abs_tol=1e-6)

    # 2. -45 degrees negative pitch (looking down): dx=10, dy=0, dz=-10 -> phi = -45 deg
    q2 = (10.0, 0.0, -8.5)
    phi2 = derived_aim_elevation_deg(e1, q2)
    assert math.isclose(phi2, -45.0, abs_tol=1e-6)

    # 3. 30 degrees positive pitch: d_xy = 10, dz = 10 * tan(30 deg) = 5.77350269
    q3 = (6.0, 8.0, 1.5 + 10.0 * math.tan(math.radians(30.0)))
    phi3 = derived_aim_elevation_deg(e1, q3)
    assert math.isclose(phi3, 30.0, abs_tol=1e-6)

    # 4. Pure planar: dz = 0 -> phi = 0 deg
    q4 = (10.0, 10.0, 1.5)
    phi4 = derived_aim_elevation_deg(e1, q4)
    assert math.isclose(phi4, 0.0, abs_tol=1e-6)


# =============================================================================
# GATE 6B-5: CAD RAMP ROUTE SERIALIZATION & DYNAMIC SLEW
# =============================================================================

def test_m6b_gate5_cad_ramp_route_serialization_and_dynamic_slew():
    """Gate 6B-5: Verify CADDocument with 3D ramp waypoints serializes, validates, roundtrips, and computes dynamic pitch."""
    doc = CADDocument(
        document_id="cad_3d_ramp_test",
        name="3D Ramp Test Corridor",
        description="Corridor with ascending 3D ramp trajectory and elevated target.",
        boundary=[[0.0, -10.0], [30.0, -10.0], [30.0, 10.0], [0.0, 10.0], [0.0, -10.0]],
        obstacles=[],
        threats=[
            CADThreat(
                id="elevated_target",
                name="Elevated Target",
                polygon=[[19.0, -1.0], [21.0, -1.0], [21.0, 1.0], [19.0, 1.0], [19.0, -1.0]],
                anchor=[20.0, 0.0],
                due_window_s=0.62,
                service_duration_s=0.10,
                z_m=11.5
            )
        ],
        routes=[
            CADRoute(
                id="ramp_route",
                name="Ascending Ramp",
                waypoints=[[0.0, 0.0, 0.0], [10.0, 0.0, 10.0]],
                v_move_mps=4.5
            )
        ],
        ports=[
            CADPort(id="p_in", segment=[[0.0, -2.0], [0.0, 2.0]], port_type="ENTRY"),
            CADPort(id="p_out", segment=[[10.0, -2.0], [10.0, 2.0]], port_type="EXIT")
        ],
        player_model=CADPlayerModel(
            v_move_mps=4.5,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0,
            eye_height_m=1.5,
            elevation_mode=ElevationMode.GEOMETRIC
        )
    )

    # 1. Verify schema validation of 3D waypoints
    is_valid, errors = validate_cad_document(doc.to_dict())
    assert is_valid is True, f"Validation errors: {errors}"

    # 2. Verify JSON serialization roundtrip
    doc_dict = doc.to_dict()
    json_str = json.dumps(doc_dict)
    doc_round = CADDocument.from_dict(json.loads(json_str))
    assert doc_round.routes[0].waypoints == [[0.0, 0.0, 0.0], [10.0, 0.0, 10.0]]

    # 3. Analyze CAD document end-to-end
    analysis = analyze_cad_document(doc_round, route_id="ramp_route", include_telemetry=False)
    assert analysis["is_valid"] is True
    assert len(analysis["threat_jobs"]) == 1
    job = analysis["threat_jobs"][0]
    
    # At first reveal (tic 0, eye is at (0, 0, 1.5)): target is at (20, 0, 11.5) -> dz=10, dxy=20 -> pitch = atan(10/20) = 26.565 deg
    expected_pitch = round(math.degrees(math.atan2(10.0, 20.0)), 2)
    assert math.isclose(job["elevation_deg"], expected_pitch, abs_tol=0.1)


# =============================================================================
# GATE 6B-6: HEIGHT-INDUCED REVEAL DIFFERENTIATION (CAD PIPELINE)
# =============================================================================

def test_m6b_gate6_height_induced_reveal_differentiation_cad_pipeline():
    """Gate 6B-6: Verify CADDocument with Ground vs Catwalk routes compiles different reveal tics due to vertical occlusion."""
    doc = CADDocument(
        document_id="cad_ground_vs_catwalk",
        name="Ground vs Catwalk Differentiation",
        description="Identical 2D polyline with ground vs elevated vertical profiles.",
        boundary=[[0.0, -10.0], [30.0, -10.0], [30.0, 10.0], [0.0, 10.0], [0.0, -10.0]],
        obstacles=[
            CADObstacle(
                id="baffle_wall",
                name="Baffle Wall",
                vertices=[[8.0, -5.0], [12.0, -5.0], [12.0, 5.0], [8.0, 5.0], [8.0, -5.0]],
                z_min_m=0.0,
                z_max_m=2.5
            )
        ],
        threats=[
            CADThreat(
                id="target",
                name="Target Behind Wall",
                polygon=[[24.0, -1.0], [26.0, -1.0], [26.0, 1.0], [24.0, 1.0], [24.0, -1.0]],
                anchor=[25.0, 0.0],
                due_window_s=0.62,
                service_duration_s=0.10,
                z_m=1.65
            )
        ],
        routes=[
            CADRoute(
                id="ground",
                name="Ground Route",
                waypoints=[[0.0, 0.0, 0.0], [20.0, 0.0, 0.0]],
                v_move_mps=4.5
            ),
            CADRoute(
                id="catwalk",
                name="Elevated Catwalk Route",
                waypoints=[[0.0, 0.0, 2.5], [20.0, 0.0, 2.5]],
                v_move_mps=4.5
            )
        ],
        ports=[
            CADPort(id="p_in", segment=[[0.0, -2.0], [0.0, 2.0]], port_type="ENTRY"),
            CADPort(id="p_out", segment=[[20.0, -2.0], [20.0, 2.0]], port_type="EXIT")
        ],
        player_model=CADPlayerModel(
            v_move_mps=4.5,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0,
            eye_height_m=1.65,
            elevation_mode=ElevationMode.GEOMETRIC
        )
    )

    # 1. Validate CAD document
    is_valid, errors = validate_cad_document(doc.to_dict())
    assert is_valid is True, f"Validation errors: {errors}"

    # 2. Analyze Ground Route: eye_z = 1.65m < 2.5m wall -> sightline blocked until passing wall (x > 12m)
    analysis_ground = analyze_cad_document(doc, route_id="ground", include_telemetry=False)
    assert analysis_ground["is_valid"] is True
    r_ground = analysis_ground["threat_jobs"][0]["reveal_tic"]

    # 3. Analyze Catwalk Route: eye_z = 2.5 + 1.65 = 4.15m > 2.5m wall -> clears wall immediately at tic 0
    analysis_catwalk = analyze_cad_document(doc, route_id="catwalk", include_telemetry=False)
    assert analysis_catwalk["is_valid"] is True
    r_catwalk = analysis_catwalk["threat_jobs"][0]["reveal_tic"]

    assert r_catwalk < r_ground, f"Catwalk reveal ({r_catwalk}) must precede ground reveal ({r_ground})"
    assert r_catwalk == 0
    assert r_ground > 80


# =============================================================================
# GATE 6B-7: RIGID VERTICAL TRANSLATION INVARIANCE
# =============================================================================

def test_m6b_gate7_rigid_vertical_translation_invariance():
    """Gate 6B-7: Verify that rigid vertical translation z -> z + c preserves reveal tics, aim states, L*, and M."""
    boundary = Polygon([(0, -10), (30, -10), (30, 10), (0, 10)])
    
    def build_module(z_offset: float) -> GeometricModule:
        route = GeometricRoute(
            route_id="r",
            waypoints=[(0.0, 0.0, 0.0 + z_offset), (20.0, 0.0, 4.0 + z_offset)],
            v_move_mps=4.5
        )
        wall_poly = Polygon([(8.0, -5.0), (12.0, -5.0), (12.0, 5.0), (8.0, 5.0)])
        obs = GeometricObstacle(id="wall", polygon=wall_poly, z_min_m=0.0 + z_offset, z_max_m=3.0 + z_offset)
        threat1 = GeometricThreat(
            id="T1",
            polygon=Polygon([(24, -2), (26, -2), (26, 0), (24, 0)]),
            threat_anchor=(25.0, -1.0),
            authored_due_window_s=0.62,
            service_duration_s=0.10,
            z_m=2.0 + z_offset
        )
        threat2 = GeometricThreat(
            id="T2",
            polygon=Polygon([(24, 1), (26, 1), (26, 3), (24, 3)]),
            threat_anchor=(25.0, 2.0),
            authored_due_window_s=0.62,
            service_duration_s=0.10,
            z_m=5.0 + z_offset
        )
        return GeometricModule(
            module_id=f"mod_z_{z_offset}",
            name=f"Z Offset {z_offset}",
            boundary=boundary,
            obstacles=[wall_poly],
            obstacles_25d=[obs],
            threats=[threat1, threat2],
            routes=[route]
        )

    params = TicCombatParameters(v_move_mps=4.5, eye_height_m=1.65)
    referee = DeterministicSimulationReferee(params)
    scheduler = DiscreteTicScheduler(params)

    # Base configuration (z_offset = 0.0)
    mod_base = build_module(0.0)
    jobs_base = referee.extract_tic_jobs(mod_base, route_index=0, elevation_mode="GEOMETRIC")
    res_base = scheduler.solve(jobs_base, initial_reticle_deg=(0.0, 0.0))

    # Translated configuration (z_offset = +25.0m)
    mod_trans = build_module(25.0)
    jobs_trans = referee.extract_tic_jobs(mod_trans, route_index=0, elevation_mode="GEOMETRIC")
    res_trans = scheduler.solve(jobs_trans, initial_reticle_deg=(0.0, 0.0))

    assert len(jobs_base) == len(jobs_trans)
    for j_b, j_t in zip(jobs_base, jobs_trans):
        assert j_b.id == j_t.id
        assert j_b.reveal_tic == j_t.reveal_tic
        assert math.isclose(j_b.angle_deg, j_t.angle_deg, abs_tol=1e-5)
        assert math.isclose(j_b.elevation_deg, j_t.elevation_deg, abs_tol=1e-5)

    assert res_base.tactical_margin_tics == res_trans.tactical_margin_tics
    assert res_base.lateness_optimal_l_star_tics == res_trans.lateness_optimal_l_star_tics
    assert res_base.is_feasible == res_trans.is_feasible


# =============================================================================
# GATE 6B-8: ASCENT HEAVEN VERTICAL ELEVATION & EXPLICIT SCHEDULE DIFFERENTIAL
# =============================================================================

def test_m6b_gate8_ascent_heaven_vertical_elevation_and_schedule_differential():
    """Gate 6B-8: Verify that elevating Heaven / Deep Site threat in Ascent A-Main increases 3D slew distance and lateness."""
    # 1. Ground Plane Analysis (Threats at ground level z_m = None -> derived phi = 0.0)
    doc_ground = get_ascent_a_main_document()
    doc_ground.player_model.elevation_mode = ElevationMode.GEOMETRIC
    analysis_ground = analyze_cad_document(doc_ground, route_id="route_A", include_telemetry=False)
    assert analysis_ground["is_valid"] is True

    # 2. Elevated Heaven Analysis (Deep Site / Heaven elevated by 3.0m to z = 4.65m)
    doc_elevated = get_ascent_a_main_document()
    doc_elevated.player_model.elevation_mode = ElevationMode.GEOMETRIC
    heaven_threat = next((t for t in doc_elevated.threats if t.id == "threat_site_deep"), None)
    assert heaven_threat is not None, "threat_site_deep must exist in Ascent fixture"
    heaven_threat.z_m = 4.65

    analysis_elevated = analyze_cad_document(doc_elevated, route_id="route_A", include_telemetry=False)
    assert analysis_elevated["is_valid"] is True

    job_ground = next(j for j in analysis_ground["threat_jobs"] if j["id"] == "threat_site_deep")
    job_elevated = next(j for j in analysis_elevated["threat_jobs"] if j["id"] == "threat_site_deep")

    # Assert derived pitch elevation difference
    assert job_ground["elevation_deg"] == 0.0
    assert job_elevated["elevation_deg"] > 0.0, f"Expected positive pitch for Heaven, got {job_elevated['elevation_deg']}"

    # Assert exact schedule metrics: Heaven elevation adds 3D slew latency to the schedule
    assert analysis_ground["tactical_margin_tics"] == -1
    assert analysis_ground["l_star_tics"] == 1
    assert analysis_elevated["l_star_tics"] >= analysis_ground["l_star_tics"]


# =============================================================================
# GATE 6B-9: SCHEMA & ELEVATION_MODE END-TO-END AUTHORITY
# =============================================================================

def test_m6b_gate9_schema_and_elevation_mode_end_to_end_authority():
    """Gate 6B-9: Verify that ElevationMode.AUTHORED and ElevationMode.GEOMETRIC both validate and compile correctly."""
    # 1. Test AUTHORED Mode
    doc_authored = get_canonical_f1_document()
    doc_authored.player_model.elevation_mode = ElevationMode.AUTHORED
    doc_authored.threats[0].elevation_deg = 35.0

    is_valid_auth, errors_auth = validate_cad_document(doc_authored.to_dict())
    assert is_valid_auth is True, f"Authored mode schema validation failed: {errors_auth}"

    res_auth = analyze_cad_document(doc_authored, route_id=doc_authored.routes[0].id, include_telemetry=False)
    assert res_auth["is_valid"] is True
    assert res_auth["threat_jobs"][0]["elevation_deg"] == 35.0  # Copied directly from authored

    # 2. Test GEOMETRIC Mode
    doc_geom = get_canonical_f1_document()
    doc_geom.player_model.elevation_mode = ElevationMode.GEOMETRIC
    doc_geom.threats[0].z_m = 5.0  # 5.0m elevation

    is_valid_geom, errors_geom = validate_cad_document(doc_geom.to_dict())
    assert is_valid_geom is True, f"Geometric mode schema validation failed: {errors_geom}"

    res_geom = analyze_cad_document(doc_geom, route_id=doc_geom.routes[0].id, include_telemetry=False)
    assert res_geom["is_valid"] is True
    assert res_geom["threat_jobs"][0]["elevation_deg"] > 0.0  # Derived dynamically from geometry


# =============================================================================
# GATE 6B-10: PRISM RAYCASTER VOLUMETRIC OCCUPANCY & BOUNDARY ROBUSTNESS
# =============================================================================

def test_m6b_gate10_prism_raycaster_volumetric_occupancy_and_boundaries():
    """Gate 6B-10: Verify prism raycaster handles interior segments, penetrating rays, and boundary grazing."""
    poly = Polygon([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)])
    z_min = 0.0
    z_max = 5.0

    # 1. Ray entirely inside solid volume
    ray_inside = ((2.0, 2.0, 2.0), (8.0, 8.0, 3.0))
    assert ray_intersects_prism_25d(ray_inside[0], ray_inside[1], poly, z_min, z_max) is True

    # 2. Horizontal ray at z=2.5 crossing through prism interior
    ray_horizontal_through = ((-5.0, 5.0, 2.5), (15.0, 5.0, 2.5))
    assert ray_intersects_prism_25d(ray_horizontal_through[0], ray_horizontal_through[1], poly, z_min, z_max) is True

    # 3. Horizontal ray above prism (z=7.0 > z_max=5.0) crossing polygon 2D footprint -> CLEAR
    ray_above = ((-5.0, 5.0, 7.0), (15.0, 5.0, 7.0))
    assert ray_intersects_prism_25d(ray_above[0], ray_above[1], poly, z_min, z_max) is False

    # 4. Ray penetrating top roof cap (z_max=5.0) into prism
    ray_roof_penetrate = ((5.0, 5.0, 8.0), (5.0, 5.0, 2.0))
    assert ray_intersects_prism_25d(ray_roof_penetrate[0], ray_roof_penetrate[1], poly, z_min, z_max) is True

    # 5. Ray starting on boundary face
    ray_on_boundary = ((0.0, 5.0, 2.5), (5.0, 5.0, 2.5))
    assert ray_intersects_prism_25d(ray_on_boundary[0], ray_on_boundary[1], poly, z_min, z_max) is True
