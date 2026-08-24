"""Unit tests for Round 10.2: Geometry-to-Contract Compiler Soundness & Mathematical Verification."""

import pytest
import math
import numpy as np
from shapely.geometry import Polygon, LineString, Point

import sys
from pathlib import Path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from cut_the_cake.model import PlayerModel, InformationRegime
from cut_the_cake.contracts import AngularSectorDiscretization
from cut_the_cake.compiler import (
    GeometricThreat,
    GeometricPort,
    GeometricRoute,
    GeometricModule,
    CompilationStatus,
    DualOracleRevealEngine,
    AimBearingCompiler,
    DeadlinePolicy,
    ConstantDeadlinePolicy,
    RangeDependentDeadlinePolicy,
    check_line_of_sight,
    validate_geometry_integrity,
    compute_exact_visibility_polygon,
    certify_port_quiescence,
    GeometryToContractCompiler
)
from cut_the_cake.fixtures_round10 import (
    build_f01_analytical_corner,
    build_f02_three_stage_pie_reveal,
    build_f02b_three_angle_sector_sweep,
    build_f03_multi_aperture_doorway,
    build_f04_disappearing_reappearing_threat,
    build_f05_two_route_flank_choice,
    build_f06_wall_perturbation_fixture,
    build_f07_visibility_flash,
    build_f07_adversarial_flash,
    build_f08_ninety_degree_turn_corner,
    build_geometric_m01_straight_corridor,
    build_geometric_m03_pie_slice_left_sweep,
    build_geometric_m04_staggered_triple_reveal,
    build_geometric_m11_rapid_crossfire_aperture,
    build_geometric_m08_high_concurrency_solvable,
    build_geometric_m07_flank_bypass_room
)


def test_f01_analytical_corner_exact_extraction():
    """Level 1: Verify exact mathematical agreement on analytic corner reveal timestamp and bearing."""
    f01 = build_f01_analytical_corner()
    compiler = GeometryToContractCompiler()
    res = compiler.compile(f01)

    assert res.status == CompilationStatus.VALID_FEASIBLE
    assert len(res.compiled_routes) == 1
    route_res = res.compiled_routes[0]
    assert len(route_res.compiled_jobs) == 1

    job = route_res.compiled_jobs[0]
    # Analytical corner reveal around (3.5, 0.5): x = 3.25m, v = 4.5 m/s -> r = 3.25 / 4.5 = 0.7222...s
    expected_s = 3.25
    expected_r = 3.25 / 4.5
    compiled_s = route_res.reveal_distances_m["F01_T1"]
    compiled_r = job.offset_s

    assert abs(compiled_s - expected_s) < 0.002, f"Expected {expected_s}m, got {compiled_s}m"
    assert abs(compiled_r - expected_r) < 0.0005, f"Expected {expected_r}s, got {compiled_r}s"

    # Bearing angle at (3.25, 0.0) to (4.0, 1.5): dx = 0.75, dy = 1.5 -> theta = atan2(1.5, 0.75) = 63.435 deg
    expected_bearing = math.degrees(math.atan2(1.5, 0.75))
    compiled_bearing = job.angle_deg
    assert abs(compiled_bearing - expected_bearing) < 0.5, f"Expected {expected_bearing} deg, got {compiled_bearing} deg"
    assert route_res.dense_oracle_discrepancies_ms["F01_T1"] < 1.0


def test_f02b_three_angle_sector_sweep_bearing_switching():
    """Level 2: Verify true multi-angle sector switching (-60 deg, 0 deg, +60 deg)."""
    f02b = build_f02b_three_angle_sector_sweep()
    compiler = GeometryToContractCompiler()
    res = compiler.compile(f02b)

    assert res.status == CompilationStatus.VALID_FEASIBLE
    route_res = res.compiled_routes[0]
    assert len(route_res.compiled_jobs) == 3

    theta1 = route_res.relative_angles_deg["F02B_T1"]
    theta2 = route_res.relative_angles_deg["F02B_T2"]
    theta3 = route_res.relative_angles_deg["F02B_T3"]

    # T1 is left flank (+60 deg), T2 is forward (0 deg), T3 is right flank (-60 deg)
    assert 45.0 <= theta1 <= 75.0, f"Expected left flank bearing ~+60 deg, got {theta1:.1f} deg"
    assert -15.0 <= theta2 <= 15.0, f"Expected forward bearing ~0 deg, got {theta2:.1f} deg"
    assert -75.0 <= theta3 <= -45.0, f"Expected right flank bearing ~-60 deg, got {theta3:.1f} deg"


def test_f07_adversarial_flash_smoke():
    """Fast regression test verifying flash slit extraction on a single 5mm slit."""
    compiler = GeometryToContractCompiler()
    mod = build_f07_adversarial_flash(slit_width_m=0.005, slit_center_x=3.00)
    res = compiler.compile(mod)

    assert res.compiler_valid, "Compiler failed on 5mm slit smoke test"
    route_res = res.compiled_routes[0]
    assert "F07_FlashThreat" in route_res.reveal_distances_m
    s_rev = route_res.reveal_distances_m["F07_FlashThreat"]
    assert 2.70 <= s_rev <= 3.30


@pytest.mark.scientific
@pytest.mark.slow
def test_f07_adversarial_flash_multi_phase_and_width_fuzzing():
    """Level 2: Fuzz slit widths down to 0.5mm across multiple grid phase shifts against 50um oracle."""
    compiler = GeometryToContractCompiler()
    widths_m = [0.0005, 0.001, 0.002, 0.005, 0.010, 0.020, 0.040, 0.080]
    phase_shifts_m = [0.000, 0.005, 0.013, 0.027, 0.038]

    for w in widths_m:
        for phase in phase_shifts_m:
            center_x = 3.00 + phase
            mod = build_f07_adversarial_flash(slit_width_m=w, slit_center_x=center_x)
            res = compiler.compile(mod)

            assert res.compiler_valid, f"Compiler failed on slit width {w*1000:.1f}mm phase {phase*1000:.1f}mm"
            route_res = res.compiled_routes[0]
            assert "F07_FlashThreat" in route_res.reveal_distances_m, f"Missed flash slit of width {w*1000:.1f}mm at phase {phase*1000:.1f}mm!"
            
            s_rev = route_res.reveal_distances_m["F07_FlashThreat"]
            expected_min = center_x - w/2.0 - 0.20
            expected_max = center_x + w/2.0 + 0.20
            assert expected_min <= s_rev <= expected_max

            # Verify against 100-micron localized reference oracle around the slit aperture
            r0 = mod.routes[0]
            s_dense_oracle = None
            s_search = np.linspace(max(0.0, center_x - 0.2), min(r0.total_length_m, center_x + 0.2), 4001)
            for s_val in s_search:
                pos = r0.position_at_distance(float(s_val))
                if check_line_of_sight(pos, mod.threats[0].threat_anchor, mod.obstacles):
                    s_dense_oracle = float(s_val)
                    break

            assert s_dense_oracle is not None, f"Reference oracle missed flash at {center_x}m"
            disc_ms = abs(s_rev - s_dense_oracle) / r0.v_move_mps * 1000.0
            assert disc_ms < 0.5, f"Discrepancy against reference oracle {disc_ms:.3f}ms exceeds tolerance"


def test_f06_wall_perturbation_sweep_sharp_l_star_crossing():
    """Level 4: Verify monotonic reveal translation and sharp L*=0 threshold crossing."""
    compiler = GeometryToContractCompiler()
    
    # 1. Early wall position (x=0.2m): simultaneous crossfire trap -> VALID_INFEASIBLE
    res_fail = compiler.compile(build_f06_wall_perturbation_fixture(wall_x=0.2))
    assert res_fail.status == CompilationStatus.VALID_INFEASIBLE
    assert not res_fail.tactically_feasible

    # 2. Late wall position (x=2.0m): sufficient stagger for sequential clearing -> VALID_FEASIBLE
    res_pass = compiler.compile(build_f06_wall_perturbation_fixture(wall_x=2.0))
    assert res_pass.status == CompilationStatus.VALID_FEASIBLE
    assert res_pass.tactically_feasible
    assert res_pass.transfer_map.is_feasible_from_any_reset_state()

    # Monotonic variation across sweep
    wall_positions = np.linspace(0.2, 2.2, 11)
    durations = []
    statuses = []

    for wx in wall_positions:
        res = compiler.compile(build_f06_wall_perturbation_fixture(wall_x=wx))
        durations.append(res.compiled_routes[0].reveal_times_s["F06_T2"])
        statuses.append(res.status)

    # Monotonic reveal time for T2
    for i in range(len(durations) - 1):
        assert durations[i+1] > durations[i]

    # Verify exactly one sharp transition from VALID_INFEASIBLE to VALID_FEASIBLE
    transition_count = sum(1 for i in range(len(statuses) - 1) if statuses[i] != statuses[i+1])
    assert transition_count == 1, f"Expected exactly 1 sharp threshold transition, got {transition_count}"


def test_f08_ninety_degree_turn_outgoing_heading():
    """Level 2: Verify outgoing tangent heading convention at 90-degree polyline waypoint turn."""
    f08 = build_f08_ninety_degree_turn_corner()
    compiler = GeometryToContractCompiler()
    res = compiler.compile(f08)

    assert res.compiler_valid
    route_res = res.compiled_routes[0]
    assert len(route_res.compiled_jobs) == 1

    job = route_res.compiled_jobs[0]
    # Reveal occurs at corner waypoint (4.0, 0.0) -> s = 4.0m
    assert abs(route_res.reveal_distances_m["F08_T1"] - 4.0) < 0.01

    # Outgoing forward heading is +90 deg (+Y). Target at (5, 4) has heading atan2(4, 1) = 75.96 deg.
    # Relative bearing is 75.96 - 90 = -14.04 deg.
    expected_rel_bearing = math.degrees(math.atan2(4.0, 1.0)) - 90.0
    assert abs(job.angle_deg - expected_rel_bearing) < 0.5, f"Expected {expected_rel_bearing:.2f} deg, got {job.angle_deg:.2f} deg"


def test_geometry_structural_validity_rejection():
    """Level 3: Verify pre-compilation structural validity gate catches illegal geometry and port misalignment."""
    compiler = GeometryToContractCompiler()

    # 1. Route clipping through obstacle interior
    bad_route_mod = GeometricModule(
        module_id="BAD_ROUTE",
        name="Bad Route",
        boundary=Polygon([(0, -2), (6, -2), (6, 2), (0, 2)]),
        obstacles=[Polygon([(2, -1), (4, -1), (4, 1), (2, 1)])],
        ports=[GeometricPort("PORT_IN", LineString([(0, -1), (0, 1)])), GeometricPort("PORT_OUT", LineString([(6, -1), (6, 1)]))],
        routes=[GeometricRoute("clip", [(0, 0), (6, 0)])],
        threats=[]
    )
    res_bad_route = compiler.compile(bad_route_mod)
    assert res_bad_route.status == CompilationStatus.INVALID_GEOMETRY
    assert any("clips through interior" in e for e in res_bad_route.validation_errors)

    # 2. Threat anchor outside threat polygon
    bad_anchor_mod = GeometricModule(
        module_id="BAD_ANCHOR",
        name="Bad Anchor",
        boundary=Polygon([(0, -2), (6, -2), (6, 2), (0, 2)]),
        obstacles=[],
        ports=[GeometricPort("PORT_IN", LineString([(0, -1), (0, 1)])), GeometricPort("PORT_OUT", LineString([(6, -1), (6, 1)]))],
        routes=[GeometricRoute("main", [(0, 0), (6, 0)])],
        threats=[GeometricThreat("T_BAD", Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]), threat_anchor=(5, 5))]
    )
    res_bad_anchor = compiler.compile(bad_anchor_mod)
    assert res_bad_anchor.status == CompilationStatus.INVALID_GEOMETRY
    assert any("outside threat polygon" in e for e in res_bad_anchor.validation_errors)

    # 3. Route endpoint misaligned with declared ports
    misaligned_mod = GeometricModule(
        module_id="MISALIGNED_PORT",
        name="Misaligned Port Route",
        boundary=Polygon([(0, -2), (6, -2), (6, 2), (0, 2)]),
        obstacles=[],
        ports=[GeometricPort("PORT_IN", LineString([(0, -1), (0, 1)])), GeometricPort("PORT_OUT", LineString([(6, -1), (6, 1)]))],
        routes=[GeometricRoute("misaligned", [(2.0, 0.0), (4.0, 0.0)])], # does not reach boundary ports at x=0, 6
        threats=[]
    )
    res_misaligned = compiler.compile(misaligned_mod)
    assert res_misaligned.status == CompilationStatus.INVALID_GEOMETRY
    assert any("does not align with any entry port" in e for e in res_misaligned.validation_errors)


def test_exact_visibility_polygon_quiescence_with_clearance_margin():
    """Level 3: Verify canonical radial sweep visibility polygon calculation and clearance-margin quiescence."""
    f01 = build_f01_analytical_corner()
    compiler = GeometryToContractCompiler(quiescent_clearance_m=0.05)
    res = compiler.compile(f01)

    port_in = [p for p in res.certified_ports if p.id == "PORT_IN"][0]
    assert port_in.is_quiescent_certified, "Recessed reset zone with clearance should pass exact polygon quiescence!"

    # Exposed port directly in line of sight should fail
    exposed_port = GeometricPort(
        id="PORT_EXPOSED",
        segment=LineString([(0.0, -1.0), (0.0, 1.0)]),
        reset_zone=Polygon([(3.5, -0.5), (4.5, -0.5), (4.5, 0.0), (3.5, 0.0)]) # in open view of threat
    )
    f01_exposed = GeometricModule(
        module_id="F01_EXPOSED",
        name="Exposed Port",
        boundary=f01.boundary,
        obstacles=f01.obstacles,
        ports=[exposed_port],
        threats=f01.threats,
        routes=f01.routes
    )
    res_exposed = compiler.compile(f01_exposed)
    p_exp = res_exposed.certified_ports[0]
    assert not p_exp.is_quiescent_certified, "Exposed reset zone must fail exact quiescence certification!"


@pytest.mark.slow
def test_six_representative_modules_classification_parity():
    """Level 5: Verify 100% feasibility-classification parity across six representative modules."""
    compiler = GeometryToContractCompiler()

    # 5 Feasible modules
    assert compiler.compile(build_geometric_m01_straight_corridor()).status == CompilationStatus.VALID_FEASIBLE
    assert compiler.compile(build_geometric_m03_pie_slice_left_sweep()).status == CompilationStatus.VALID_FEASIBLE
    assert compiler.compile(build_geometric_m04_staggered_triple_reveal()).status == CompilationStatus.VALID_FEASIBLE
    assert compiler.compile(build_geometric_m08_high_concurrency_solvable()).status == CompilationStatus.VALID_FEASIBLE
    assert compiler.compile(build_geometric_m07_flank_bypass_room()).status == CompilationStatus.VALID_FEASIBLE

    # 1 Infeasible trap module correctly identified
    res_m11 = compiler.compile(build_geometric_m11_rapid_crossfire_aperture())
    assert res_m11.status == CompilationStatus.VALID_INFEASIBLE
    assert res_m11.compiler_valid
    assert not res_m11.tactically_feasible


def test_two_module_exact_contract_parity():
    """Level 5: Verify exact quantitative release, bearing, and matrix parity on M01 and M03."""
    compiler = GeometryToContractCompiler()

    # M01 Straight Corridor: 1 forward threat
    res_m01 = compiler.compile(build_geometric_m01_straight_corridor())
    tmap_m01 = res_m01.transfer_map
    assert tmap_m01.traversal_duration_s == 1.0
    assert tmap_m01.get_duration(0, 0) == 1.25
    assert tmap_m01.get_duration(1, 1) == 1.00

    # M03 Pie Slice Left Sweep: Sequential L-to-C
    res_m03 = compiler.compile(build_geometric_m03_pie_slice_left_sweep())
    tmap_m03 = res_m03.transfer_map
    assert tmap_m03.traversal_duration_s == 1.5
    assert tmap_m03.get_duration(0, 0) == 2.00
    assert pytest.approx(tmap_m03.get_duration(1, 1), abs=1e-3) == 1.7992

    # Verify Pre-Aim regime recovers exact anticipatory 1.75s duration
    preaim_mat = tmap_m03.get_duration(1, 1, regime=InformationRegime.PRE_AIM)
    assert pytest.approx(preaim_mat, abs=1e-3) == 1.75
