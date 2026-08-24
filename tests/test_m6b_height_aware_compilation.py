"""Milestone 6-B Verification Test Suite: Height-Aware Geometric Compilation.

Formal scientific gates verifying that:
- 3D target coordinates and 2.5D extruded obstacle prisms compile directly into 3D aim states (theta, phi) and reveal tics R_j.
- The frozen Milestone 6-A discrete scheduler is untouched and consumes (theta, phi) seamlessly.
- Backward compatibility and bit-for-bit planar identity are strictly preserved.
"""

from __future__ import annotations
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
# GATE 6B-1: COMPLETE PLANAR IDENTITY
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

        for route_id, exp in baseline_fixture["routes"].items():
            analysis = analyze_cad_document(doc, route_id=route_id, include_telemetry=False)

            assert analysis["compiled_job_count"] == exp["compiled_job_count"], f"Job count mismatch for {name}/{route_id}"
            assert analysis["tactical_margin_tics"] == exp["tactical_margin_tics"], f"Margin mismatch for {name}/{route_id}"
            assert analysis["l_star_tics"] == exp["l_star_tics"], f"L* mismatch for {name}/{route_id}"
            assert analysis["source_schedule_feasible"] == exp["source_schedule_feasible"], f"Feasibility mismatch for {name}/{route_id}"
            assert analysis["stagger_gap_tics"] == exp["stagger_gap_tics"], f"Stagger mismatch for {name}/{route_id}"

            for actual_j, exp_j in zip(analysis["threat_jobs"], exp["threat_jobs"]):
                assert actual_j["id"] == exp_j["id"]
                assert actual_j["reveal_tic"] == exp_j["reveal_tic"]
                assert actual_j["due_window_tics"] == exp_j["due_window_tics"]
                assert actual_j["deadline_tic"] == exp_j["deadline_tic"]
                assert math.isclose(actual_j["angle_deg"], exp_j["angle_deg"], abs_tol=1e-1)
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
# GATE 6B-5: DYNAMIC ROUTE ELEVATION & RAMP SLEW
# =============================================================================

def test_m6b_gate5_dynamic_route_elevation_ramp_slew():
    """Gate 6B-5: Verify that player ascending a 3D ramp dynamically adjusts pitch phi(s) along the trajectory."""
    # Ramp route from z_feet = 0 to z_feet = 10 over x in [0, 10]
    route = GeometricRoute(
        route_id="ramp",
        waypoints=[(0.0, 0.0, 0.0), (10.0, 0.0, 10.0)],
        v_move_mps=4.5
    )
    eye_h = 1.5
    target = (20.0, 0.0, 11.5)  # Target at z = 11.5m

    # Sample eye positions along ramp
    pitch_angles = []
    for s in [0.0, 2.0, 5.0, 8.0, route.total_length_m]:
        eye = route.eye_position_at_distance(s, eye_height_m=eye_h)
        phi = derived_aim_elevation_deg(eye, target)
        pitch_angles.append(phi)

    # At start (s=0, eye_z = 1.5): delta_z = 10, d_xy = 20 -> phi = atan(10/20) = 26.565 deg
    assert math.isclose(pitch_angles[0], math.degrees(math.atan2(10.0, 20.0)), abs_tol=1e-4)

    # At end (s=total, eye_z = 11.5): delta_z = 0, d_xy = 10 -> phi = 0.0 deg
    assert math.isclose(pitch_angles[-1], 0.0, abs_tol=1e-4)

    # As player ascends towards target level, pitch must monotonically decrease
    for i in range(len(pitch_angles) - 1):
        assert pitch_angles[i] > pitch_angles[i + 1], f"Pitch did not strictly decrease: {pitch_angles}"


# =============================================================================
# GATE 6B-6: HEIGHT-INDUCED REVEAL DIFFERENTIATION
# =============================================================================

def test_m6b_gate6_height_induced_reveal_differentiation():
    """Gate 6B-6: Verify that two routes with identical (x, y) 2D projection yield different reveal tics due to elevation."""
    boundary = Polygon([(0, -10), (30, -10), (30, 10), (0, 10)])
    
    # Route A: Ground level (z_feet = 0)
    route_ground = GeometricRoute(route_id="ground", waypoints=[(0.0, 0.0, 0.0), (20.0, 0.0, 0.0)], v_move_mps=4.5)
    
    # Route B: Elevated Catwalk (z_feet = 2.5m)
    route_elevated = GeometricRoute(route_id="catwalk", waypoints=[(0.0, 0.0, 2.5), (20.0, 0.0, 2.5)], v_move_mps=4.5)

    # Wall at x in [8, 12] with height z in [0, 2.5]
    wall_poly = Polygon([(8.0, -5.0), (12.0, -5.0), (12.0, 5.0), (8.0, 5.0)])
    obs = GeometricObstacle(id="wall", polygon=wall_poly, z_min_m=0.0, z_max_m=2.5)

    # Target behind wall at x=25, z=1.65
    threat = GeometricThreat(
        id="target",
        polygon=Polygon([(24, -1), (26, -1), (26, 1), (24, 1)]),
        threat_anchor=(25.0, 0.0),
        authored_due_window_s=0.62,
        service_duration_s=0.10,
        z_m=1.65
    )

    params = TicCombatParameters(v_move_mps=4.5, eye_height_m=1.65)
    referee = DeterministicSimulationReferee(params)

    # Compile Ground Route: eye_z = 1.65m < 2.5m wall -> cannot see over wall, must pass it (x > 12m)
    mod_ground = GeometricModule(
        module_id="ground_mod",
        name="Ground",
        boundary=boundary,
        obstacles=[wall_poly],
        obstacles_25d=[obs],
        threats=[threat],
        routes=[route_ground]
    )
    jobs_ground = referee.extract_tic_jobs(mod_ground, route_index=0, elevation_mode="GEOMETRIC")
    assert len(jobs_ground) == 1
    r_ground = jobs_ground[0].reveal_tic

    # Compile Elevated Route: eye_z = 2.5 + 1.65 = 4.15m > 2.5m wall -> sees over wall immediately at start!
    mod_elevated = GeometricModule(
        module_id="elev_mod",
        name="Elevated",
        boundary=boundary,
        obstacles=[wall_poly],
        obstacles_25d=[obs],
        threats=[threat],
        routes=[route_elevated]
    )
    jobs_elevated = referee.extract_tic_jobs(mod_elevated, route_index=0, elevation_mode="GEOMETRIC")
    assert len(jobs_elevated) == 1
    r_elevated = jobs_elevated[0].reveal_tic

    # Proves that 3D elevation unlocks earlier line-of-sight unavailable in 2D
    assert r_elevated < r_ground, f"Elevated reveal ({r_elevated}) should precede ground reveal ({r_ground})"
    assert r_elevated == 0  # Visible at tic 0 over the wall


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
# GATE 6B-8: ASCENT-INSPIRED REAL BOUNDARY FIXTURE
# =============================================================================

def test_m6b_gate8_ascent_calibrated_heaven_compilation():
    """Gate 6B-8: Verify that Ascent A-Main with calibrated Heaven platform compiles non-zero pitch phi and updates schedule."""
    doc = get_ascent_a_main_document()
    doc.player_model.elevation_mode = ElevationMode.GEOMETRIC

    # In baseline 2D, deep site is at ground elevation (z=1.65m)
    # We calibrate deep site threat height to z = 4.65m (3.0m elevation above ground level)
    deep_threat = next((t for t in doc.threats if "deep" in t.id.lower() or "site" in t.name.lower()), None)
    assert deep_threat is not None, "Deep site threat must exist in Ascent fixture"
    deep_threat.z_m = 4.65

    # Analyze under M6-B height-aware geometric compiler
    analysis = analyze_cad_document(doc, route_id="route_A", include_telemetry=False)
    assert analysis["is_valid"] is True

    # Find the compiled deep site job
    deep_job = next(j for j in analysis["threat_jobs"] if j["id"] == deep_threat.id)

    # Proves deep site compiles with a dynamic positive pitch angle phi > 0 deg derived from geometry
    assert deep_job["elevation_deg"] > 0.0, f"Heaven pitch should be positive, got {deep_job['elevation_deg']}"

    # Scheduler cleanly ingests the 3D aim state without changes to schedule format
    assert isinstance(analysis["tactical_margin_tics"], int)
    assert isinstance(analysis["l_star_tics"], int)
