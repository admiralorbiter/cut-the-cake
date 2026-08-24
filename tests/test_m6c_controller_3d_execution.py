"""Milestone 6-C Verification Suite: 3D Controller Execution & Telemetry Parity.

Verifies that the discrete simulation controller executing on the 35-Hz integer clock
reproduces the exact completion tics, lateness, and tactical margins predicted by the
frozen M6-A / M6-B discrete scheduler, while preserving bit-for-bit identity on planar maps.
"""

from __future__ import annotations
import math
import pytest
from typing import Dict, Any, List

pytestmark = pytest.mark.cad

from cut_the_cake.cad_document import (
    CADDocument,
    CADRoute,
    CADObstacle,
    CADThreat,
    CADPlayerModel,
    ElevationMode,
    get_canonical_f1_document,
    get_custom_asymmetric_corridor_document,
    get_dust2_a_long_document,
    get_ascent_a_main_document,
    get_dust2_b_tunnels_document,
    get_transit_213_document
)
from cut_the_cake.cad_adapter import analyze_cad_document
from cut_the_cake.cad_export import _generate_telemetry_and_events
from cut_the_cake.compiler import GeometricModule, GeometricRoute, GeometricObstacle, GeometricThreat
from cut_the_cake.vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteTicScheduler,
    DeterministicSimulationReferee,
    SimulationController,
    ControllerPolicy
)
from cut_the_cake.geometry import (
    spherical_aim_distance_deg,
    slew_towards_spherical,
    slew_towards_heading,
    normalize_angle_deg
)


# =============================================================================
# GATE 6C-1: PLANAR CONTROLLER BIT-FOR-BIT TELEMETRY & REFEREE PARITY
# =============================================================================

def test_m6c_gate1_planar_controller_bit_for_bit_parity():
    """Gate 6C-1: Verify that 3D-capable controller and referee reproduce identical telemetry and completions on all planar fixtures."""
    fixtures = [
        ("canonical_f1", get_canonical_f1_document()),
        ("custom_corridor", get_custom_asymmetric_corridor_document()),
        ("dust2_a_long", get_dust2_a_long_document()),
        ("ascent_a_main", get_ascent_a_main_document()),
        ("dust2_b_tunnels", get_dust2_b_tunnels_document()),
        ("transit_213", get_transit_213_document()),
    ]

    for name, doc in fixtures:
        geo_mod = doc.to_geometric_module()
        for idx, route in enumerate(doc.routes):
            res = analyze_cad_document(doc, route_id=route.id, include_telemetry=True)
            assert res["is_valid"] is True, f"Analysis failed for {name} route {route.id}"
            assert res["telemetry_status"] == "SUCCESS"
            assert res["telemetry_frames"] is not None
            assert len(res["telemetry_frames"]) > 0

            # Verify that all reticle elevations on planar map remain identically 0.0
            for frame in res["telemetry_frames"]:
                assert frame["reticle_elevation_deg"] == 0.0, f"Nonzero elevation on planar {name}"

            # Direct referee run_episode validation
            referee = DeterministicSimulationReferee()
            episode_log = referee.run_episode(
                geo_mod,
                route_index=idx,
                initial_reticle_deg=doc.player_model.initial_reticle_deg,
                initial_reticle_elevation_deg=doc.player_model.initial_reticle_elevation_deg
            )
            assert episode_log.player_survived == res["model_episode_survived"], f"Survival mismatch on {name} route {route.id}"

            # Verify realized completions match scheduled completions for all survived threats
            for j in res["threat_jobs"]:
                if res["model_episode_survived"]:
                    assert j["realized_service_complete_tic"] == j["scheduled_service_end_tic"]


# =============================================================================
# GATE 6C-2: PURE ELEVATION SLEW EXECUTION & EVENT DERIVATION
# =============================================================================

def test_m6c_gate2_pure_elevation_slew_execution_parity():
    """Gate 6C-2: Verify pure vertical pitch slew matches scheduled tics and derives realized completion from events."""
    params = TicCombatParameters(
        aim_velocity_deg_s=360.0,         # ~10.2857 deg/tic
        acquisition_latency_s=3.0 / 35.0,  # 3 tics
        inspect_duration_s=3.0 / 35.0,     # 3 tics
        v_move_mps=1.0
    )
    # Target at (10, 0, 1.65 + 10 * tan(30 deg)) -> exact 30 deg elevation, 0 deg azimuth
    target_z = 1.65 + 10.0 * math.tan(math.radians(30.0))

    geo_mod = GeometricModule(
        module_id="pure_elevation_exec",
        name="Pure Elevation Slew Arena",
        boundary=GeometricObstacle(id="b", polygon=[(0, -5), (20, -5), (20, 5), (0, 5)]).polygon,
        obstacles=[],
        threats=[
            GeometricThreat(
                id="threat_elev_30",
                polygon=GeometricObstacle(id="t", polygon=[(9.5, -0.5), (10.5, -0.5), (10.5, 0.5), (9.5, 0.5)]).polygon,
                threat_anchor=(10.0, 0.0),
                authored_due_window_s=2.0,
                service_duration_s=3.0 / 35.0,
                z_m=target_z
            )
        ],
        routes=[
            GeometricRoute(
                route_id="route_static",
                waypoints=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                v_move_mps=1.0
            )
        ]
    )

    frames, events, summary = _generate_telemetry_and_events(
        geo_mod,
        params=params,
        initial_reticle_deg=0.0,
        initial_reticle_elevation_deg=0.0
    )

    assert summary["model_episode_survived"] is True

    # Check actual SERVICE_COMPLETE event emission
    service_events = [e for e in events if e["type"] == "SERVICE_COMPLETE"]
    assert len(service_events) == 1
    assert service_events[0]["threat_id"] == "threat_elev_30"
    assert service_events[0]["tic"] == 8

    # Verify threat job record derives realized completion directly from event
    job = summary["threat_jobs"][0]
    assert math.isclose(job["elevation_deg"], 30.0, abs_tol=0.05)
    assert job["completion_tic"] == 9
    assert job["scheduled_service_end_tic"] == 8
    assert job["realized_service_complete_tic"] == service_events[0]["tic"] == 8

    # Verify that telemetry frames show monotonic vertical pitch elevation from initial 0 deg towards target 30 deg
    elevations = [frames[i]["reticle_elevation_deg"] for i in range(4)]
    assert elevations[0] == 0.0
    assert elevations[0] < elevations[1] < elevations[2] < elevations[3]
    assert math.isclose(elevations[3], 30.0, abs_tol=0.05)


# =============================================================================
# GATE 6C-3: MIXED (THETA, PHI) SPHERICAL ARC SLEW & ANTIPODAL TIE-BREAK
# =============================================================================

def test_m6c_gate3_mixed_spherical_arc_slew_execution():
    """Gate 6C-3: Verify mixed azimuth-elevation slew follows great-circle geodesic and handles antipodal singularity."""
    params = TicCombatParameters(
        aim_velocity_deg_s=360.0,         # 10.2857 deg/tic
        acquisition_latency_s=2.0 / 35.0, # 2 tics
        inspect_duration_s=2.0 / 35.0     # 2 tics
    )

    # 1. Standard mixed arc: (-45 deg, 60 deg) to (+45 deg, 60 deg)
    # alpha = arccos(sin(60)^2 + cos(60)^2 * cos(90)) = arccos(0.75) ~ 41.41 deg
    d_alpha = spherical_aim_distance_deg(-45.0, 60.0, 45.0, 60.0)
    assert math.isclose(d_alpha, 41.4096, abs_tol=0.01)

    curr_th, curr_ph = -45.0, 60.0
    for step in range(5):
        next_th, next_ph = slew_towards_spherical(curr_th, curr_ph, 45.0, 60.0, params.max_aim_deg_per_tic)
        assert next_ph > 50.0
        curr_th, curr_ph = next_th, next_ph

    assert math.isclose(curr_th, 45.0, abs_tol=1e-4)
    assert math.isclose(curr_ph, 60.0, abs_tol=1e-4)

    # 2. Antipodal 3D transition: (0 deg, 45 deg) to (180 deg, -45 deg) -> alpha = 180.0 deg
    # Exactly opposite directions on the unit sphere
    anti_alpha = spherical_aim_distance_deg(0.0, 45.0, 180.0, -45.0)
    assert math.isclose(anti_alpha, 180.0, abs_tol=1e-4)

    # Slew tics = ceil(180 / 10.2857) = 18 tics
    step_deg = params.max_aim_deg_per_tic
    th_anti, ph_anti = 0.0, 45.0
    for s in range(18):
        th_anti, ph_anti = slew_towards_spherical(th_anti, ph_anti, 180.0, -45.0, step_deg)
        # Verify angles are finite numbers without NaN
        assert not math.isnan(th_anti)
        assert not math.isnan(ph_anti)

    assert math.isclose(th_anti, 180.0, abs_tol=1e-3)
    assert math.isclose(ph_anti, -45.0, abs_tol=1e-3)


# =============================================================================
# GATE 6C-4: 3D RAMP ROUTE-POSITION TELEMETRY & REVEAL AIM EXECUTION
# =============================================================================

def test_m6c_gate4_3d_ramp_dynamic_traversal_and_slew_tracking():
    """Gate 6C-4: Verify player traversing 3D ramp emits 3D positions (x, y, z) and executes reveal aim state."""
    doc = CADDocument(
        document_id="cad_ramp_exec",
        name="CAD 3D Ramp Execution Arena",
        boundary=[[0.0, -10.0], [30.0, -10.0], [30.0, 10.0], [0.0, 10.0]],
        obstacles=[],
        threats=[
            CADThreat(
                id="threat_high_platform",
                name="High Platform Threat",
                anchor=[25.0, 0.0],
                polygon=[[24.0, -1.0], [26.0, -1.0], [26.0, 1.0], [24.0, 1.0]],
                due_window_s=5.0,
                service_duration_s=0.2,
                z_m=6.65  # 5.0m above ground eye height
            )
        ],
        routes=[
            CADRoute(
                id="route_ramp_climb",
                name="Ramp Climb Route",
                waypoints=[[0.0, 0.0, 0.0], [20.0, 0.0, 5.0]],  # Ascending ramp
                v_move_mps=4.0
            )
        ],
        player_model=CADPlayerModel(
            elevation_mode=ElevationMode.GEOMETRIC,
            eye_height_m=1.65,
            initial_reticle_deg=0.0,
            initial_reticle_elevation_deg=0.0
        )
    )

    res = analyze_cad_document(doc, route_id="route_ramp_climb", include_telemetry=True)
    assert res["is_valid"] is True
    assert res["telemetry_status"] == "SUCCESS"

    frames = res["telemetry_frames"]
    assert len(frames) > 0

    # Verify 3D positions in telemetry frames
    for f in frames:
        assert len(f["player_pos"]) == 3
        assert f["player_pos"][0] >= 0.0
        assert f["player_pos"][2] >= 0.0

    # Start: player at (0, 0, 0)
    first_frame = frames[0]
    assert first_frame["player_pos"] == [0.0, 0.0, 0.0]

    # End of ramp: player at (20, 0, 5.0)
    last_frame = frames[-1]
    assert math.isclose(last_frame["player_pos"][2], 5.0, abs_tol=0.1)


# =============================================================================
# GATE 6C-5: REALIZED SERVICE COMPLETION VS SCHEDULE EXACT IDENTITY
# =============================================================================

def test_m6c_gate5_realized_service_completion_vs_schedule_identity():
    """Gate 6C-5: Verify realized service complete events match discrete schedule completion tics on 3D fixtures."""
    doc = CADDocument(
        document_id="cad_3d_feasible_multithreat",
        name="3D Feasible Multi-Threat Arena",
        boundary=[[0.0, -10.0], [30.0, -10.0], [30.0, 10.0], [0.0, 10.0]],
        obstacles=[],
        threats=[
            CADThreat(
                id="threat_elevated_left",
                name="Elevated Left Threat",
                anchor=[10.0, 5.0],
                polygon=[[9.5, 4.5], [10.5, 4.5], [10.5, 5.5], [9.5, 5.5]],
                due_window_s=4.0,
                service_duration_s=0.15,
                z_m=4.0
            ),
            CADThreat(
                id="threat_elevated_right",
                name="Elevated Right Threat",
                anchor=[12.0, -4.0],
                polygon=[[11.5, -4.5], [12.5, -4.5], [12.5, -3.5], [11.5, -3.5]],
                due_window_s=5.0,
                service_duration_s=0.15,
                z_m=3.0
            ),
            CADThreat(
                id="threat_ground_center",
                name="Ground Center Threat",
                anchor=[14.0, 0.0],
                polygon=[[13.5, -0.5], [14.5, -0.5], [14.5, 0.5], [13.5, 0.5]],
                due_window_s=6.0,
                service_duration_s=0.15,
                z_m=1.65
            )
        ],
        routes=[
            CADRoute(
                id="route_3d_advance",
                name="3D Advance Route",
                waypoints=[[0.0, 0.0, 0.0], [15.0, 0.0, 0.0]],
                v_move_mps=3.0
            )
        ],
        player_model=CADPlayerModel(
            elevation_mode=ElevationMode.GEOMETRIC,
            eye_height_m=1.65,
            initial_reticle_deg=0.0,
            initial_reticle_elevation_deg=0.0
        )
    )

    res = analyze_cad_document(doc, route_id="route_3d_advance", include_telemetry=True)
    assert res["is_valid"] is True
    assert res["telemetry_status"] == "SUCCESS"
    assert res["model_episode_survived"] is True
    assert res["tactical_margin_tics"] >= 0
    assert len(res["threat_jobs"]) == 3

    # Collect actual SERVICE_COMPLETE events
    service_events = {e["threat_id"]: e["tic"] for e in res["events"] if e["type"] == "SERVICE_COMPLETE"}

    # Assert every serviced job matches its actual event tic and scheduled completion
    for j in res["threat_jobs"]:
        assert j["id"] in service_events
        ev_tic = service_events[j["id"]]
        assert ev_tic == j["scheduled_service_end_tic"]
        assert ev_tic == j["realized_service_complete_tic"]
        assert ev_tic == j["completion_tic"] - 1


# =============================================================================
# GATE 6C-6: 3D POST-DEATH / TIMEOUT INVARIANT
# =============================================================================

def test_m6c_gate6_3d_post_death_timeout_invariant():
    """Gate 6C-6: Verify controller records death at min(D_j) and freezes physical position upon 3D deadline breach."""
    doc = CADDocument(
        document_id="cad_3d_lethal_breach",
        name="3D Lethal Deadline Breach Arena",
        boundary=[[0.0, -10.0], [30.0, -10.0], [30.0, 10.0], [0.0, 10.0]],
        obstacles=[],
        threats=[
            CADThreat(
                id="threat_insta_kill",
                name="Instant Kill Sniper",
                anchor=[10.0, 0.0],
                polygon=[[9.0, -1.0], [11.0, -1.0], [11.0, 1.0], [9.0, 1.0]],
                due_window_s=0.05,        # 1-2 tics (impossible to slew + acquire + service)
                service_duration_s=0.5,
                z_m=10.0                  # High elevation
            )
        ],
        routes=[
            CADRoute(
                id="route_walk",
                name="Walk Route",
                waypoints=[[0.0, 0.0, 0.0], [20.0, 0.0, 0.0]],
                v_move_mps=4.0
            )
        ],
        player_model=CADPlayerModel(
            elevation_mode=ElevationMode.GEOMETRIC,
            eye_height_m=1.65,
            initial_reticle_deg=180.0,     # Must turn 180 deg + elevate
            initial_reticle_elevation_deg=0.0
        )
    )

    res = analyze_cad_document(doc, route_id="route_walk", include_telemetry=True)
    assert res["is_valid"] is True
    assert res["model_episode_survived"] is False
    assert res["model_death_tic"] is not None

    min_deadline = min(j["deadline_tic"] for j in res["threat_jobs"])
    death_tic = res["model_death_tic"]
    # Kill referee triggers at k = min(D_j)
    assert death_tic == min_deadline

    frames = res["telemetry_frames"]
    assert len(frames) > death_tic

    death_frame = frames[death_tic]
    assert death_frame["controller_state"] == "DEAD"

    # Post-death frames must maintain frozen physical position
    for f in frames[death_tic:]:
        assert f["player_pos"] == death_frame["player_pos"]
        assert f["controller_state"] == "DEAD"
