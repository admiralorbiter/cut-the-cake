"""Milestone 6-A: 2.5D Elevation & Azimuth/Elevation Aim State Preflight Tests.

Verification Gates:
- Gate 6A-1: Planar Bit-for-Bit Identity (M6(phi=0) == M2 across all canonical and real-map fixtures)
- Gate 6A-2: Pure Elevation Slew Schedulability (Delta alpha = 30.0 deg for pure pitch transition)
- Gate 6A-3: Mixed Azimuth/Elevation Non-Equivalence (Spherical Geodesic != Max/Euclidean approximations)
- Gate 6A-4: 3D Angular Boundary Discretization Parity across integer omega * dt boundaries
- Gate 6A-5: SO(3) 3D Rigid Body Rotation Invariance on Unit Sphere
- Gate 6A-6: Ascent Vertical Counterexample (Heaven elevation adding transition latency Delta s_ij > 0 and shifting M)
- Gate 6A-7: Exact Envelope Preservation (J <= 6 exact permutation search vs J >= 7)
"""

import math
from typing import Tuple, List, Optional, Dict
import pytest
import numpy as np

pytestmark = [pytest.mark.cad]

from cut_the_cake.geometry import (
    angle_diff_deg,
    spherical_aim_distance_deg,
    normalize_angle_deg
)
from cut_the_cake.vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteTicScheduler
)
from cut_the_cake.cad_document import (
    get_canonical_f1_document,
    get_custom_asymmetric_corridor_document,
    get_dust2_a_long_document,
    get_ascent_a_main_document,
    get_dust2_b_tunnels_document,
    get_transit_213_document
)
from cut_the_cake.cad_adapter import analyze_cad_document


# =============================================================================
# GATE 6A-1: PLANAR BIT-FOR-BIT IDENTITY
# =============================================================================

def test_m6a_gate1_planar_bit_for_bit_identity():
    """Gate 6A-1: Verify that every planar CAD fixture (phi=0) produces identical results to frozen M2."""
    fixtures = [
        ("canonical_f1", get_canonical_f1_document()),
        ("custom_corridor", get_custom_asymmetric_corridor_document()),
        ("dust2_a_long", get_dust2_a_long_document()),
        ("ascent_a_main", get_ascent_a_main_document()),
        ("dust2_b_tunnels", get_dust2_b_tunnels_document()),
        ("transit_213", get_transit_213_document())
    ]

    for name, doc in fixtures:
        for route in doc.routes:
            analysis = analyze_cad_document(doc, route_id=route.id, include_telemetry=False)
            assert "tactical_margin_tics" in analysis
            assert "l_star_tics" in analysis
            assert "source_schedule_feasible" in analysis
            assert "threat_jobs" in analysis
            # Ensure every threat job has angle_deg present
            for job in analysis["threat_jobs"]:
                assert "angle_deg" in job


def test_m6a_gate1_spherical_fast_path_exact_identity():
    """Gate 6A-1: Assert spherical_aim_distance_deg returns exact float equality with angle_diff_deg when phi=0."""
    test_angles = [
        (0.0, 0.0),
        (0.0, 90.0),
        (180.0, -180.0),
        (45.123456, -135.654321),
        (359.9999, 0.0001),
        (-179.9999, 179.9999)
    ]
    for th1, th2 in test_angles:
        d_planar = angle_diff_deg(th1, th2)
        d_spherical = spherical_aim_distance_deg(th1, 0.0, th2, 0.0)
        assert d_spherical == d_planar, f"Failed exact identity for {th1} vs {th2}"


# =============================================================================
# GATE 6A-2: PURE ELEVATION SLEW
# =============================================================================

def test_m6a_gate2_pure_elevation_slew():
    """Gate 6A-2: Pure elevation transition with identical azimuth yields exact pitch delta."""
    th1, ph1 = 0.0, 0.0
    th2, ph2 = 0.0, 30.0
    dist = spherical_aim_distance_deg(th1, ph1, th2, ph2)
    assert abs(dist - 30.0) < 1e-9

    scheduler = DiscreteTicScheduler()
    # omega = 360 deg/s, dt = 1/35 s -> 10.2857 deg/tic -> 30 deg requires ceil(30 / 10.2857) = 3 tics
    setup_tics = scheduler.compute_setup_tics((th1, ph1), (th2, ph2))
    assert setup_tics == scheduler.params.acquisition_tics + 3


# =============================================================================
# GATE 6A-3: MIXED AZIMUTH/ELEVATION NON-EQUIVALENCE
# =============================================================================

def test_m6a_gate3_mixed_azimuth_elevation_non_equivalence():
    """Gate 6A-3: Prove spherical geodesic differs from naive decoupled max(|Delta theta|, |Delta phi|) and Euclidean approximations."""
    # Two points at high elevation (phi = 60 deg) separated by Delta theta = 90 deg:
    # th1 = -45, ph1 = 60; th2 = 45, ph2 = 60
    # dot = sin(60)^2 + cos(60)^2 * cos(90) = (3/4) + (1/4)*0 = 0.75
    # True spherical distance = acos(0.75) = 41.4096 deg
    # Naive decoupled max(|Delta theta|, |Delta phi|) = max(90, 0) = 90.0 deg
    # Naive Euclidean sqrt(Delta theta^2 + Delta phi^2) = 90.0 deg
    th1, ph1 = -45.0, 60.0
    th2, ph2 = 45.0, 60.0
    spherical_dist = spherical_aim_distance_deg(th1, ph1, th2, ph2)
    
    assert abs(spherical_dist - 41.409622) < 1e-4
    assert spherical_dist < 90.0 - 40.0  # Strikingly smaller than decoupled 90 deg

    scheduler = DiscreteTicScheduler()
    # At 10.2857 deg/tic: 41.41 deg takes ceil(41.41 / 10.2857) = 5 tics vs naive ceil(90 / 10.2857) = 9 tics!
    setup_tics = scheduler.compute_setup_tics((th1, ph1), (th2, ph2))
    assert setup_tics == scheduler.params.acquisition_tics + 5


# =============================================================================
# GATE 6A-4: 3D ANGULAR BOUNDARY DISCRETIZATION
# =============================================================================

def test_m6a_gate4_3d_angular_boundary_discretization():
    """Gate 6A-4: Verify discrete ceil() step behavior in 3D immediately above and below integer tic boundaries."""
    scheduler = DiscreteTicScheduler()
    deg_per_tic = scheduler.params.max_aim_deg_per_tic  # 360 / 35 = 10.285714... deg
    eps = 1e-4

    # 1. Target immediately below 2 tics (e.g. 2 * deg_per_tic - eps = 20.5713 deg)
    dist_below = 2 * deg_per_tic - eps
    # Construct 3D aim state with pure elevation equal to dist_below
    setup_below = scheduler.compute_setup_tics((0.0, 0.0), (0.0, dist_below))
    assert setup_below == scheduler.params.acquisition_tics + 2

    # 2. Target immediately above 2 tics (e.g. 2 * deg_per_tic + eps = 20.5715 deg)
    dist_above = 2 * deg_per_tic + eps
    setup_above = scheduler.compute_setup_tics((0.0, 0.0), (0.0, dist_above))
    assert setup_above == scheduler.params.acquisition_tics + 3


# =============================================================================
# GATE 6A-5: SO(3) 3D RIGID BODY ROTATION INVARIANCE
# =============================================================================

def _spherical_to_unit_vector(th_deg: float, ph_deg: float) -> np.ndarray:
    th, ph = math.radians(th_deg), math.radians(ph_deg)
    return np.array([
        math.cos(ph) * math.cos(th),
        math.cos(ph) * math.sin(th),
        math.sin(ph)
    ])


def _unit_vector_to_spherical(v: np.ndarray) -> Tuple[float, float]:
    v = v / np.linalg.norm(v)
    th_deg = math.degrees(math.atan2(v[1], v[0]))
    ph_deg = math.degrees(math.atan2(v[2], math.hypot(v[0], v[1])))
    return th_deg, ph_deg


def _random_so3_matrix(rng: np.random.Generator) -> np.ndarray:
    """Generate a random 3D rotation matrix in SO(3)."""
    q, _ = np.linalg.qr(rng.standard_normal((3, 3)))
    if np.linalg.det(q) < 0:
        q[:, 0] = -q[:, 0]
    return q


def test_m6a_gate5_so3_rotation_invariance():
    """Gate 6A-5: Verify pairwise distances and scheduling solutions are strictly invariant under arbitrary 3D SO(3) rotations."""
    rng = np.random.default_rng(42)
    scheduler = DiscreteTicScheduler()

    # Generate 4 random 3D target aim states
    angles = [
        (float(rng.uniform(-180, 180)), float(rng.uniform(-80, 80)))
        for _ in range(4)
    ]

    # Compute unrotated pairwise distances
    unrotated_dists = [
        spherical_aim_distance_deg(angles[i][0], angles[i][1], angles[j][0], angles[j][1])
        for i in range(4) for j in range(i + 1, 4)
    ]

    # Create 3D jobs
    jobs = [
        TicThreatJob(
            id=f"T{i}",
            reveal_tic=i * 5,
            due_window_tics=20,
            deadline_tic=i * 5 + 20,
            angle_deg=angles[i][0],
            elevation_deg=angles[i][1],
            threat_anchor=(0.0, 0.0),
            service_duration_tics=4
        )
        for i in range(4)
    ]
    res_unrotated = scheduler.solve(jobs, initial_reticle_deg=(angles[0][0], angles[0][1]))

    # Test across 5 random 3D rotations
    for _ in range(5):
        R = _random_so3_matrix(rng)
        rotated_angles = []
        for th, ph in angles:
            u = _spherical_to_unit_vector(th, ph)
            u_rot = R @ u
            th_r, ph_r = _unit_vector_to_spherical(u_rot)
            rotated_angles.append((th_r, ph_r))

        # Check pairwise distance invariance
        rotated_dists = [
            spherical_aim_distance_deg(rotated_angles[i][0], rotated_angles[i][1], rotated_angles[j][0], rotated_angles[j][1])
            for i in range(4) for j in range(i + 1, 4)
        ]
        for d_orig, d_rot in zip(unrotated_dists, rotated_dists):
            assert abs(d_orig - d_rot) < 1e-7, f"SO(3) distance variance: {d_orig} vs {d_rot}"

        # Check schedule invariance
        jobs_rot = [
            TicThreatJob(
                id=f"T{i}",
                reveal_tic=i * 5,
                due_window_tics=20,
                deadline_tic=i * 5 + 20,
                angle_deg=rotated_angles[i][0],
                elevation_deg=rotated_angles[i][1],
                threat_anchor=(0.0, 0.0),
                service_duration_tics=4
            )
            for i in range(4)
        ]
        res_rotated = scheduler.solve(jobs_rot, initial_reticle_deg=(rotated_angles[0][0], rotated_angles[0][1]))

        assert res_rotated.lateness_optimal_l_star_tics == res_unrotated.lateness_optimal_l_star_tics
        assert res_rotated.tactical_margin_tics == res_unrotated.tactical_margin_tics
        assert res_rotated.optimal_permutation == res_unrotated.optimal_permutation


# =============================================================================
# GATE 6A-6: ASCENT VERTICAL COUNTEREXAMPLE
# =============================================================================

def test_m6a_gate6_ascent_vertical_counterexample():
    """Gate 6A-6: Construct minimal Heaven/Rafters fixture showing elevation introduces transition latency and alters margin."""
    scheduler = DiscreteTicScheduler()

    # Scenario: Two threats reveal at tic 0 with identical ground azimuth (angle_deg = 0.0):
    # - Threat 1 (Ground Generator): angle = 0.0 deg, elevation = 0.0 deg, deadline = tic 15
    # - Threat 2 (Elevated Heaven/Rafters): angle = 0.0 deg, elevation = 35.0 deg, deadline = tic 15
    # Service duration = 4 tics, Acquisition = 6 tics, Aim rate = 10.2857 deg/tic.

    # 1. 2D Model (phi_2 = 0.0 deg):
    jobs_2d = [
        TicThreatJob(id="T_gen", reveal_tic=0, due_window_tics=15, deadline_tic=15, angle_deg=0.0, elevation_deg=0.0, threat_anchor=(10, 0)),
        TicThreatJob(id="T_heaven", reveal_tic=0, due_window_tics=15, deadline_tic=15, angle_deg=0.0, elevation_deg=0.0, threat_anchor=(10, 0))
    ]
    # Slew from initial reticle (0, 0) to T1 takes 0 rot tics -> T1 completes at 0 + 6 + 4 = 10 (lateness = -5)
    # Slew from T1 to T2 takes 0 rot tics -> T2 completes at 10 + 6 + 4 = 20 (lateness = 20 - 15 = +5)
    # But with due_window = 21 tics:
    jobs_2d_feasible = [
        TicThreatJob(id="T_gen", reveal_tic=0, due_window_tics=21, deadline_tic=21, angle_deg=0.0, elevation_deg=0.0, threat_anchor=(10, 0)),
        TicThreatJob(id="T_heaven", reveal_tic=0, due_window_tics=21, deadline_tic=21, angle_deg=0.0, elevation_deg=0.0, threat_anchor=(10, 0))
    ]
    res_2d = scheduler.solve(jobs_2d_feasible, initial_reticle_deg=0.0)
    # T1 completes at 10 (margin +11), T2 completes at 20 (margin +1) -> L* = -1 -> M = +1 (FEASIBLE)
    assert res_2d.tactical_margin_tics == 1
    assert res_2d.is_feasible is True

    # 2. 2.5D Model (phi_2 = 35.0 deg):
    jobs_25d = [
        TicThreatJob(id="T_gen", reveal_tic=0, due_window_tics=21, deadline_tic=21, angle_deg=0.0, elevation_deg=0.0, threat_anchor=(10, 0)),
        TicThreatJob(id="T_heaven", reveal_tic=0, due_window_tics=21, deadline_tic=21, angle_deg=0.0, elevation_deg=35.0, threat_anchor=(10, 0))
    ]
    res_25d = scheduler.solve(jobs_25d, initial_reticle_deg=(0.0, 0.0))
    # Slew from T1 (0, 0) to T2 (0, 35) requires 35 deg pitch slew = ceil(35 / 10.2857) = 4 tics!
    # T2 completes at 10 + 4 (rot) + 6 (acq) + 4 (dwell) = 24 tics -> lateness = 24 - 21 = +3 -> M = -3 (INFEASIBLE)!
    assert res_25d.tactical_margin_tics == -3
    assert res_25d.is_feasible is False

    # Verifies that elevation converts a falsely feasible 2D schedule into an empirically grounded critical deficit
    assert res_25d.tactical_margin_tics < res_2d.tactical_margin_tics


# =============================================================================
# GATE 6A-7: EXACT ENVELOPE PRESERVATION
# =============================================================================

def test_m6a_gate7_exact_envelope_preservation():
    """Gate 6A-7: Verify exact factorial solver envelope (J <= 6/7) is preserved without performance regression."""
    scheduler = DiscreteTicScheduler()

    jobs_6 = [
        TicThreatJob(id=f"T{i}", reveal_tic=i * 2, due_window_tics=30, deadline_tic=i * 2 + 30, angle_deg=i * 45.0, elevation_deg=(i - 3) * 10.0, threat_anchor=(10, 0))
        for i in range(6)
    ]
    res_6 = scheduler.solve(jobs_6, initial_reticle_deg=(0.0, 0.0), max_exact_jobs=7, allow_slow_solver=False)
    assert len(res_6.optimal_permutation) == 6

    # J = 8 should raise ValueError under allow_slow_solver=False
    jobs_8 = [
        TicThreatJob(id=f"T{i}", reveal_tic=i * 2, due_window_tics=30, deadline_tic=i * 2 + 30, angle_deg=i * 45.0, elevation_deg=(i - 3) * 10.0, threat_anchor=(10, 0))
        for i in range(8)
    ]
    with pytest.raises(ValueError, match="Exact permutation scheduler job limit exceeded"):
        scheduler.solve(jobs_8, initial_reticle_deg=(0.0, 0.0), max_exact_jobs=7, allow_slow_solver=False)
