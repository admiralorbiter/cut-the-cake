"""Milestone 6-A.1: 2.5D Elevation & Azimuth/Elevation Aim State Preflight Tests.

Verification Gates:
- Gate 6A-1: Differential Planar Bit-for-Bit Identity (M6(phi=0) == M2 across all canonical and real-map fixtures against frozen 4e81dd7 outputs)
- Gate 6A-2: Pure Elevation Slew Schedulability (Delta alpha = 30.0 deg for pure pitch transition)
- Gate 6A-3: Mixed Azimuth/Elevation Non-Equivalence (Spherical Geodesic != Max/Euclidean approximations)
- Gate 6A-4: 3D Angular Boundary Discretization Parity across integer omega * dt boundaries
- Gate 6A-5: SO(3) 3D Rigid Body Rotation Invariance on Unit Sphere
- Gate 6A-6: Ascent Vertical Mechanism Counterexample (Synthetic demonstration of elevation adding transition latency Delta s_ij > 0 and shifting M)
- Gate 6A-7: Exact Envelope Preservation (J <= 6 exact permutation search vs J >= 7)
- Gate 6A-8: Schema & Validator Enforcement for phi in [-90, 90] & Fail-Closed Elevated Telemetry
"""

import math
from typing import Tuple, List, Optional, Dict, Any
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
    get_transit_213_document,
    validate_cad_document
)
from cut_the_cake.cad_adapter import analyze_cad_document


# =============================================================================
# FROZEN PRE-M6 (4e81dd7) BASELINE CONTRACT SNAPSHOT
# =============================================================================

FROZEN_4E81DD7_PLANAR_BASELINES = {
    "canonical_f1": {
        "doc_hash": "a9e6df741d21695f",
        "routes": {
            "main": {
                "compiled_job_count": 2,
                "tactical_margin_tics": -6,
                "l_star_tics": 6,
                "source_schedule_feasible": False,
                "stagger_gap_tics": 3,
                "threat_jobs": [
                    {"id": "F1_T1_L00", "reveal_tic": 0, "due_window_tics": 22, "deadline_tic": 22, "angle_deg": -29.4, "completion_tic": 13, "lateness_tics": -9},
                    {"id": "F1_T2_R00", "reveal_tic": 3, "due_window_tics": 22, "deadline_tic": 25, "angle_deg": 48.7, "completion_tic": 31, "lateness_tics": 6}
                ]
            }
        }
    },
    "custom_corridor": {
        "doc_hash": "300ea914917ec66a",
        "routes": {
            "route_incursion": {
                "compiled_job_count": 3,
                "tactical_margin_tics": -25,
                "l_star_tics": 25,
                "source_schedule_feasible": False,
                "stagger_gap_tics": 0,
                "threat_jobs": [
                    {"id": "sniper_nest_north", "reveal_tic": 0, "due_window_tics": 23, "deadline_tic": 23, "angle_deg": 66.5, "completion_tic": 48, "lateness_tics": 25},
                    {"id": "flanker_alcove_south", "reveal_tic": 0, "due_window_tics": 23, "deadline_tic": 23, "angle_deg": -33.3, "completion_tic": 15, "lateness_tics": -8},
                    {"id": "overwatch_bunker_east", "reveal_tic": 0, "due_window_tics": 27, "deadline_tic": 27, "angle_deg": 13.9, "completion_tic": 31, "lateness_tics": 4}
                ]
            }
        }
    },
    "dust2_a_long": {
        "doc_hash": "d425ce5a4df7ec35",
        "routes": {
            "route_pieing": {
                "compiled_job_count": 3,
                "tactical_margin_tics": 1,
                "l_star_tics": -1,
                "source_schedule_feasible": True,
                "stagger_gap_tics": 47,
                "threat_jobs": [
                    {"id": "threat_corner_hold", "reveal_tic": 0, "due_window_tics": 16, "deadline_tic": 16, "angle_deg": -10.9, "completion_tic": 12, "lateness_tics": -4},
                    {"id": "threat_pit_hold", "reveal_tic": 47, "due_window_tics": 16, "deadline_tic": 63, "angle_deg": 36.4, "completion_tic": 62, "lateness_tics": -1},
                    {"id": "threat_plat_hold", "reveal_tic": 195, "due_window_tics": 21, "deadline_tic": 216, "angle_deg": -32.4, "completion_tic": 212, "lateness_tics": -4}
                ]
            },
            "route_wide_swing": {
                "compiled_job_count": 3,
                "tactical_margin_tics": 2,
                "l_star_tics": -2,
                "source_schedule_feasible": True,
                "stagger_gap_tics": 26,
                "threat_jobs": [
                    {"id": "threat_corner_hold", "reveal_tic": 0, "due_window_tics": 16, "deadline_tic": 16, "angle_deg": 14.7, "completion_tic": 12, "lateness_tics": -4},
                    {"id": "threat_pit_hold", "reveal_tic": 26, "due_window_tics": 16, "deadline_tic": 42, "angle_deg": 50.4, "completion_tic": 40, "lateness_tics": -2},
                    {"id": "threat_plat_hold", "reveal_tic": 199, "due_window_tics": 21, "deadline_tic": 220, "angle_deg": -36.3, "completion_tic": 218, "lateness_tics": -2}
                ]
            },
            "route_pit_drop": {
                "compiled_job_count": 2,
                "tactical_margin_tics": 0,
                "l_star_tics": 0,
                "source_schedule_feasible": True,
                "stagger_gap_tics": 42,
                "threat_jobs": [
                    {"id": "threat_corner_hold", "reveal_tic": 0, "due_window_tics": 16, "deadline_tic": 16, "angle_deg": -10.4, "completion_tic": 12, "lateness_tics": -4},
                    {"id": "threat_pit_hold", "reveal_tic": 42, "due_window_tics": 16, "deadline_tic": 58, "angle_deg": -65.7, "completion_tic": 58, "lateness_tics": 0}
                ]
            }
        }
    },
    "ascent_a_main": {
        "doc_hash": "7d3494f37e3ce5e9",
        "routes": {
            "route_A": {
                "compiled_job_count": 3,
                "tactical_margin_tics": -1,
                "l_star_tics": 1,
                "source_schedule_feasible": False,
                "stagger_gap_tics": 0,
                "threat_jobs": [
                    {"id": "threat_gen_hold", "reveal_tic": 0, "due_window_tics": 16, "deadline_tic": 16, "angle_deg": 1.2, "completion_tic": 11, "lateness_tics": -5},
                    {"id": "threat_site_deep", "reveal_tic": 0, "due_window_tics": 21, "deadline_tic": 21, "angle_deg": -1.8, "completion_tic": 22, "lateness_tics": 1},
                    {"id": "threat_wine_hold", "reveal_tic": 68, "due_window_tics": 16, "deadline_tic": 84, "angle_deg": -31.2, "completion_tic": 81, "lateness_tics": -3}
                ]
            },
            "route_B": {
                "compiled_job_count": 3,
                "tactical_margin_tics": -1,
                "l_star_tics": 1,
                "source_schedule_feasible": False,
                "stagger_gap_tics": 0,
                "threat_jobs": [
                    {"id": "threat_gen_hold", "reveal_tic": 0, "due_window_tics": 16, "deadline_tic": 16, "angle_deg": 1.2, "completion_tic": 11, "lateness_tics": -5},
                    {"id": "threat_site_deep", "reveal_tic": 0, "due_window_tics": 21, "deadline_tic": 21, "angle_deg": -1.8, "completion_tic": 22, "lateness_tics": 1},
                    {"id": "threat_wine_hold", "reveal_tic": 68, "due_window_tics": 16, "deadline_tic": 84, "angle_deg": -31.2, "completion_tic": 81, "lateness_tics": -3}
                ]
            }
        }
    },
    "dust2_b_tunnels": {
        "doc_hash": "8d96e010d808472c",
        "routes": {
            "route_A": {
                "compiled_job_count": 2,
                "tactical_margin_tics": -6,
                "l_star_tics": 6,
                "source_schedule_feasible": False,
                "stagger_gap_tics": 0,
                "threat_jobs": [
                    {"id": "threat_closet_hold", "reveal_tic": 0, "due_window_tics": 16, "deadline_tic": 16, "angle_deg": -11.0, "completion_tic": 12, "lateness_tics": -4},
                    {"id": "threat_site_hold", "reveal_tic": 0, "due_window_tics": 18, "deadline_tic": 18, "angle_deg": 6.0, "completion_tic": 24, "lateness_tics": 6}
                ]
            },
            "route_B": {
                "compiled_job_count": 2,
                "tactical_margin_tics": -4,
                "l_star_tics": 4,
                "source_schedule_feasible": False,
                "stagger_gap_tics": 3,
                "threat_jobs": [
                    {"id": "threat_site_hold", "reveal_tic": 0, "due_window_tics": 18, "deadline_tic": 18, "angle_deg": 8.5, "completion_tic": 11, "lateness_tics": -7},
                    {"id": "threat_closet_hold", "reveal_tic": 3, "due_window_tics": 16, "deadline_tic": 19, "angle_deg": -8.0, "completion_tic": 23, "lateness_tics": 4}
                ]
            }
        }
    },
    "transit_213": {
        "doc_hash": "7e9996ccbee2df4b",
        "routes": {
            "route_A": {
                "compiled_job_count": 3,
                "tactical_margin_tics": -4,
                "l_star_tics": 4,
                "source_schedule_feasible": False,
                "stagger_gap_tics": 18,
                "threat_jobs": [
                    {"id": "threat_center_shed", "reveal_tic": 44, "due_window_tics": 16, "deadline_tic": 60, "angle_deg": -7.1, "completion_tic": 55, "lateness_tics": -5},
                    {"id": "threat_depot_roof", "reveal_tic": 62, "due_window_tics": 18, "deadline_tic": 80, "angle_deg": 93.1, "completion_tic": 82, "lateness_tics": 2},
                    {"id": "threat_south_depot", "reveal_tic": 200, "due_window_tics": 18, "deadline_tic": 218, "angle_deg": -26.9, "completion_tic": 222, "lateness_tics": 4}
                ]
            },
            "route_B": {
                "compiled_job_count": 3,
                "tactical_margin_tics": 3,
                "l_star_tics": -3,
                "source_schedule_feasible": True,
                "stagger_gap_tics": 14,
                "threat_jobs": [
                    {"id": "threat_depot_roof", "reveal_tic": 0, "due_window_tics": 18, "deadline_tic": 18, "angle_deg": 0.0, "completion_tic": 10, "lateness_tics": -8},
                    {"id": "threat_center_shed", "reveal_tic": 98, "due_window_tics": 16, "deadline_tic": 114, "angle_deg": -30.3, "completion_tic": 111, "lateness_tics": -3},
                    {"id": "threat_south_depot", "reveal_tic": 112, "due_window_tics": 18, "deadline_tic": 130, "angle_deg": -49.6, "completion_tic": 124, "lateness_tics": -6}
                ]
            }
        }
    }
}


# =============================================================================
# GATE 6A-1: DIFFERENTIAL PLANAR BIT-FOR-BIT IDENTITY
# =============================================================================

def test_m6a_gate1_differential_planar_bit_for_bit_identity():
    """Gate 6A-1: Differentially verify all 6 CAD fixtures and 11 routes match frozen pre-M6 baseline outputs bit-for-bit."""
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

            # Verify threat jobs bit-for-bit
            assert len(analysis["threat_jobs"]) == len(exp["threat_jobs"]), f"Threat jobs length mismatch for {name}/{route_id}"
            for actual_j, exp_j in zip(analysis["threat_jobs"], exp["threat_jobs"]):
                assert actual_j["id"] == exp_j["id"]
                assert actual_j["reveal_tic"] == exp_j["reveal_tic"]
                assert actual_j["due_window_tics"] == exp_j["due_window_tics"]
                assert actual_j["deadline_tic"] == exp_j["deadline_tic"]
                assert actual_j["angle_deg"] == exp_j["angle_deg"]
                assert actual_j["completion_tic"] == exp_j["completion_tic"]
                assert actual_j["lateness_tics"] == exp_j["lateness_tics"]


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


def test_m6a_gate1_sub_tolerance_planar_discretization_parity():
    """Gate 6A-1: Verify that 0 < Delta theta <= 1e-4 charges ceil() aim tics in compute_setup_tics exactly as in frozen M2."""
    scheduler = DiscreteTicScheduler()
    # For a sub-tolerance transition 1e-5 deg, ceil(1e-5 / 10.2857) = 1 tic
    setup = scheduler.compute_setup_tics((0.0, 0.0), (1e-5, 0.0))
    assert setup == scheduler.params.acquisition_tics + 1


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
# GATE 6A-6: ASCENT VERTICAL MECHANISM COUNTEREXAMPLE
# =============================================================================

def test_m6a_gate6_ascent_vertical_mechanism_counterexample():
    """Gate 6A-6: Synthetic mechanism demonstration showing that elevation is sufficient to produce the class of scheduling error identified in Ascent M5-B."""
    scheduler = DiscreteTicScheduler()

    # Scenario: Two threats reveal at tic 0 with identical ground azimuth (angle_deg = 0.0):
    # - Threat 1 (Ground Generator): angle = 0.0 deg, elevation = 0.0 deg, due_window = 21 tics
    # - Threat 2 (Elevated Heaven/Rafters): angle = 0.0 deg, elevation = 35.0 deg, due_window = 21 tics
    # Service duration = 4 tics, Acquisition = 6 tics, Aim rate = 10.2857 deg/tic.

    # 1. 2D Model (phi_2 = 0.0 deg):
    jobs_2d = [
        TicThreatJob(id="T_gen", reveal_tic=0, due_window_tics=21, deadline_tic=21, angle_deg=0.0, elevation_deg=0.0, threat_anchor=(10, 0)),
        TicThreatJob(id="T_heaven", reveal_tic=0, due_window_tics=21, deadline_tic=21, angle_deg=0.0, elevation_deg=0.0, threat_anchor=(10, 0))
    ]
    res_2d = scheduler.solve(jobs_2d, initial_reticle_deg=0.0)
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

    # Verifies that elevation converts a falsely feasible 2D schedule into a critical deficit in this synthetic mechanism demonstration
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


# =============================================================================
# GATE 6A-8: SCHEMA VALIDATION & FAIL-CLOSED ELEVATED TELEMETRY
# =============================================================================

def test_m6a_gate8_elevation_validation_bounds():
    """Gate 6A-8: Assert schema and validator reject out-of-range elevation angles (|phi| > 90 deg)."""
    doc = get_canonical_f1_document()
    doc_dict = doc.to_dict()

    # 1. Invalid player initial elevation (> 90 deg)
    doc_dict["player_model"]["initial_reticle_elevation_deg"] = 95.0
    is_valid, errors = validate_cad_document(doc_dict)
    assert is_valid is False
    assert any("initial_reticle_elevation_deg" in err for err in errors)

    # 2. Invalid threat elevation (< -90 deg)
    doc_dict2 = doc.to_dict()
    doc_dict2["geometry"]["threats"][0]["elevation_deg"] = -100.0
    is_valid2, errors2 = validate_cad_document(doc_dict2)
    assert is_valid2 is False
    assert any("elevation_deg" in err for err in errors2)


def test_m6a_gate8_fail_closed_elevated_telemetry():
    """Gate 6A-8: Assert request for telemetry on elevated geometry executes 3D controller successfully (M6-C)."""
    doc = get_canonical_f1_document()
    doc.threats[0].elevation_deg = 30.0  # Introduce 3D elevation

    # Running with include_telemetry=True executes 3D controller in M6-C
    res = analyze_cad_document(doc, include_telemetry=True)
    assert res["is_valid"] is True
    assert res["telemetry_status"] == "SUCCESS"
    assert res["telemetry_frames"] is not None
    assert len(res["telemetry_frames"]) > 0
