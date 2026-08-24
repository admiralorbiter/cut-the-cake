"""Round 10.1: Adversarial Geometric Fixture Suite & Ported Modules [G] (Hardened).

Defines 8 adversarial scientific geometric fixtures designed to test and validate
every level of the geometry-to-contract compilation hierarchy, plus 6 representative
geometric modules ported from Library 1.
"""

from __future__ import annotations
import math
from typing import List, Tuple, Optional, Dict
from shapely.geometry import Polygon, LineString, Point

from .compiler import (
    GeometricThreat,
    GeometricPort,
    GeometricRoute,
    GeometricModule
)


# =============================================================================
# ADVERSARIAL SCIENTIFIC FIXTURES
# =============================================================================

def build_f01_analytical_corner() -> GeometricModule:
    """F01: Single sharp occluding corner with exact analytical reveal timestamp.
    
    Path: y = 0 from x = 0 to x = 8 (v = 4.5 m/s).
    Threat anchor: (4.0, 1.5).
    Corner obstacle pillar: [3.0, 3.5] x [0.5, 2.0] with critical corner at (3.5, 0.5).
    Analytic ray grazing (3.5, 0.5) to (4.0, 1.5) has slope 2.0, intersecting y=0 at x = 3.25 m.
    Analytic reveal offset: s = 3.25 m, r = 3.25 / 4.5 = 0.7222 s.
    Analytic aim bearing: atan2(1.5, 0.75) = 63.435 degrees.
    """
    boundary = Polygon([(0.0, -1.5), (8.0, -1.5), (8.0, 3.0), (0.0, 3.0)])
    obs = [Polygon([(3.0, 0.5), (3.5, 0.5), (3.5, 2.0), (3.0, 2.0)])]
    threat = GeometricThreat(
        id="F01_T1",
        polygon=Polygon([(3.8, 1.3), (4.2, 1.3), (4.2, 1.7), (3.8, 1.7)]),
        threat_anchor=(4.0, 1.5),
        authored_due_window_s=2.0,
        description="Analytic corner threat"
    )
    port_in = GeometricPort(
        id="PORT_IN",
        segment=LineString([(0.0, -1.0), (0.0, 1.0)]),
        normal=(-1.0, 0.0),
        reset_zone=Polygon([(0.0, -1.0), (1.0, -1.0), (1.0, 1.0), (0.0, 1.0)])
    )
    port_out = GeometricPort(
        id="PORT_OUT",
        segment=LineString([(8.0, -1.0), (8.0, 1.0)]),
        normal=(1.0, 0.0)
    )
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="F01_AnalyticalCorner",
        name="Analytical Corner Fixture",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=[threat],
        routes=[route],
        category="analytical_benchmark",
        description="Single occluding corner with exact analytical reveal coordinate at x=3.25m."
    )


def build_f02_three_stage_pie_reveal() -> GeometricModule:
    """F02: Sequential 3-stage reveal verifying ordering r1 < r2 < r3 around staggered baffles."""
    boundary = Polygon([(0.0, -2.5), (8.0, -2.5), (8.0, 3.5), (0.0, 3.5)])
    
    obs = [
        Polygon([(2.0, 0.2), (2.5, 0.2), (2.5, 1.8), (2.0, 1.8)]),
        Polygon([(3.5, 0.2), (4.0, 0.2), (4.0, 1.8), (3.5, 1.8)]),
        Polygon([(5.0, 0.2), (5.5, 0.2), (5.5, 1.8), (5.0, 1.8)])
    ]
    threats = [
        GeometricThreat("F02_T1", Polygon([(2.6, 2.1), (3.0, 2.1), (3.0, 2.5), (2.6, 2.5)]), (2.8, 2.3), 2.0),
        GeometricThreat("F02_T2", Polygon([(4.1, 2.1), (4.5, 2.1), (4.5, 2.5), (4.1, 2.5)]), (4.3, 2.3), 2.0),
        GeometricThreat("F02_T3", Polygon([(5.6, 2.1), (6.0, 2.1), (6.0, 2.5), (5.6, 2.5)]), (5.8, 2.3), 2.0)
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -2.0), (0.0, 0.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -2.0), (8.0, 0.0)]))
    route = GeometricRoute("main", [(0.0, -1.0), (8.0, -1.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="F02_ThreeStagePieReveal",
        name="Three-Stage Pie Reveal Fixture",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="pie_slice",
        description="Verifies sequential reveal ordering r1 < r2 < r3 around staggered baffles."
    )


def build_f02b_three_angle_sector_sweep() -> GeometricModule:
    """F02B: True 3-angle multi-directional sector sweep (-60 deg, 0 deg, +60 deg)."""
    boundary = Polygon([(0.0, -2.5), (8.0, -2.5), (8.0, 2.5), (0.0, 2.5)])
    
    # Baffle on top and baffle on bottom
    obs = [
        Polygon([(1.8, 0.3), (2.2, 0.3), (2.2, 2.2), (1.8, 2.2)]),
        Polygon([(4.5, -2.2), (4.9, -2.2), (4.9, -0.3), (4.5, -0.3)])
    ]
    threats = [
        # T1: Left flank (+60 deg relative bearing at reveal x=2.0)
        GeometricThreat("F02B_T1", Polygon([(2.6, 1.3), (3.0, 1.3), (3.0, 1.7), (2.6, 1.7)]), (2.8, 1.5), 2.0),
        # T2: Forward center (0 deg relative bearing at reveal x=3.5)
        GeometricThreat("F02B_T2", Polygon([(5.8, -0.2), (6.2, -0.2), (6.2, 0.2), (5.8, 0.2)]), (6.0, 0.0), 2.0),
        # T3: Right flank (-60 deg relative bearing at reveal x=5.0)
        GeometricThreat("F02B_T3", Polygon([(5.3, -1.7), (5.7, -1.7), (5.7, -1.3), (5.3, -1.3)]), (5.5, -1.5), 2.0)
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="F02B_ThreeAngleSectorSweep",
        name="Three-Angle Sector Sweep Fixture",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="sector_sweep",
        description="Verifies true multi-angle switching across left flank (+60°), forward (0°), and right flank (-60°)."
    )


def build_f03_multi_aperture_doorway() -> GeometricModule:
    """F03: Simultaneous multi-aperture doorway with tight release clustering."""
    boundary = Polygon([(0.0, -3.0), (8.0, -3.0), (8.0, 3.0), (0.0, 3.0)])
    
    obs = [
        Polygon([(2.4, 0.4), (2.6, 0.4), (2.6, 3.0), (2.4, 3.0)]),
        Polygon([(2.4, -3.0), (2.6, -3.0), (2.6, -0.4), (2.4, -0.4)])
    ]
    threats = [
        GeometricThreat("F03_T1", Polygon([(4.8, -2.2), (5.2, -2.2), (5.2, -1.8), (4.8, -1.8)]), (5.0, -2.0), 2.0),
        GeometricThreat("F03_T2", Polygon([(4.8, 1.8), (5.2, 1.8), (5.2, 2.2), (4.8, 2.2)]), (5.0, 2.0), 2.0)
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="F03_MultiApertureDoorway",
        name="Multi-Aperture Doorway Fixture",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="concurrency_cluster",
        description="Simultaneous release cluster upon threshold crossing."
    )


def build_f04_disappearing_reappearing_threat() -> GeometricModule:
    """F04: Double pillar occlusion verifying compiler preserves the earliest first reveal."""
    boundary = Polygon([(0.0, -1.5), (8.0, -1.5), (8.0, 3.5), (0.0, 3.5)])
    
    obs = [
        Polygon([(1.5, 0.2), (2.0, 0.2), (2.0, 1.5), (1.5, 1.5)]),
        Polygon([(3.5, 0.2), (4.0, 0.2), (4.0, 1.5), (3.5, 1.5)])
    ]
    threat = GeometricThreat(
        "F04_T1",
        Polygon([(2.8, 2.3), (3.2, 2.3), (3.2, 2.7), (2.8, 2.7)]),
        (3.0, 2.5),
        2.5
    )
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="F04_DisappearingReappearingThreat",
        name="Disappearing/Reappearing Threat Fixture",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=[threat],
        routes=[route],
        category="occlusion_memory",
        description="Verifies preservation of earliest reveal timestamp across occlusion gaps."
    )


def build_f05_two_route_flank_choice() -> GeometricModule:
    """F05: Two-route room where direct path is infeasible while flank bypass is feasible."""
    boundary = Polygon([(0.0, -2.5), (8.0, -2.5), (8.0, 3.5), (0.0, 3.5)])
    
    obs = [
        Polygon([(0.0, 0.5), (7.5, 0.5), (7.5, 1.2), (0.0, 1.2)])
    ]
    threats = [
        GeometricThreat("F05_T1", Polygon([(3.8, -2.2), (4.2, -2.2), (4.2, -1.8), (3.8, -1.8)]), (4.0, -2.0), 0.30),
        GeometricThreat("F05_T2", Polygon([(3.8, -0.2), (4.2, -0.2), (4.2, 0.2), (3.8, 0.2)]), (4.0, 0.0), 0.30)
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 2.5)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 2.5)]))
    
    r_direct = GeometricRoute("direct_center", [(0.0, -0.5), (8.0, -0.5)], v_move_mps=4.5)
    r_flank = GeometricRoute("upper_flank", [(0.0, 2.0), (8.0, 2.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="F05_TwoRouteFlankChoice",
        name="Two-Route Flank Choice Fixture",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[r_direct, r_flank],
        category="flank_choice",
        description="Direct kill zone is infeasible; upper flank bypass ensures module solvability."
    )


def build_f06_wall_perturbation_fixture(wall_x: float = 1.0) -> GeometricModule:
    """F06: Parametric wall obstacle with 2 threats to test monotonic L* transition and sharp L*=0 threshold crossing.
    
    T1 is at (4.0, -1.0) (due window 1.00s).
    T2 is behind the wall at (wall_x + 1.0, 1.5) (due window 1.00s).
    As wall_x shifts, the stagger between T1 and T2 increases, crossing sharply from an infeasible
    simultaneous crossfire trap (x < 0.85m) to a feasible sequential sweep (x >= 0.85m).
    """
    boundary = Polygon([(0.0, -2.0), (8.0, -2.0), (8.0, 3.0), (0.0, 3.0)])
    obs = [Polygon([(wall_x, 0.5), (wall_x + 0.5, 0.5), (wall_x + 0.5, 2.0), (wall_x, 2.0)])]
    threats = [
        GeometricThreat("F06_T1", Polygon([(3.8, -1.2), (4.2, -1.2), (4.2, -0.8), (3.8, -0.8)]), (4.0, -1.0), 1.00),
        GeometricThreat("F06_T2", Polygon([(wall_x + 0.8, 1.3), (wall_x + 1.2, 1.3), (wall_x + 1.2, 1.7), (wall_x + 0.8, 1.7)]), (wall_x + 1.0, 1.5), 1.00)
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id=f"F06_WallPerturbation_x{wall_x:.2f}",
        name="Wall Perturbation Fixture",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="perturbation_sweep",
        description=f"Parametric wall at x={wall_x:.2f}m."
    )


def build_f08_ninety_degree_turn_corner() -> GeometricModule:
    """F08: 90-degree corner turn testing outgoing movement tangent heading convention."""
    boundary = Polygon([(0.0, -1.5), (6.0, -1.5), (6.0, 6.0), (2.5, 6.0), (2.5, 1.5), (0.0, 1.5)])
    
    # Inner corner wall flush with the turn corner at x=4.0, y in [0.0, 5.0]
    obs = [
        Polygon([(0.0, 0.0), (4.0, 0.0), (4.0, 5.0), (0.0, 5.0)])
    ]
    # Threat in upper branch revealed right at corner apex (4.0, 0.0)
    threat = GeometricThreat(
        "F08_T1",
        Polygon([(4.8, 3.8), (5.2, 3.8), (5.2, 4.2), (4.8, 4.2)]),
        (5.0, 4.0),
        2.0
    )
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(3.0, 6.0), (5.0, 6.0)]))
    # 90-degree turn polyline: (0,0) -> (4,0) -> (4,6)
    route = GeometricRoute("main", [(0.0, 0.0), (4.0, 0.0), (4.0, 6.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="F08_NinetyDegreeTurnCorner",
        name="90-Degree Turn Corner Fixture",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=[threat],
        routes=[route],
        category="corner_turn",
        description="Verifies crisp outgoing tangent heading (-14.0°) at 90° route waypoint turn."
    )


def build_f07_adversarial_flash(slit_width_m: float = 0.04, slit_center_x: float = 3.02) -> GeometricModule:
    """F07: Parameterized narrow slit aperture for flash adversary fuzzing (1mm to 80mm)."""
    boundary = Polygon([(0.0, -1.5), (8.0, -1.5), (8.0, 3.5), (0.0, 3.5)])
    x_left_end = slit_center_x - slit_width_m / 2.0
    x_right_start = slit_center_x + slit_width_m / 2.0

    obs = [
        Polygon([(0.0, 0.5), (x_left_end, 0.5), (x_left_end, 2.0), (0.0, 2.0)]),
        Polygon([(x_right_start, 0.5), (8.00, 0.5), (8.00, 2.0), (x_right_start, 2.0)])
    ]
    threat = GeometricThreat(
        "F07_FlashThreat",
        Polygon([(slit_center_x - 0.1, 2.3), (slit_center_x + 0.1, 2.3), (slit_center_x + 0.1, 2.7), (slit_center_x - 0.1, 2.7)]),
        (slit_center_x, 2.5),
        2.0
    )
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id=f"F07_VisibilityFlash_w{int(slit_width_m*1000)}mm",
        name="Visibility Flash Fixture",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=[threat],
        routes=[route],
        category="adversarial_sampler",
        description=f"{slit_width_m*1000:.1f}mm slit aperture verifying critical-LOS flash resilience."
    )


def build_f07_visibility_flash() -> GeometricModule:
    """Standard 4cm slit fixture."""
    return build_f07_adversarial_flash(slit_width_m=0.04, slit_center_x=3.02)


# =============================================================================
# 6 REPRESENTATIVE PORTED MODULES FROM LIBRARY 1
# =============================================================================

def build_geometric_m01_straight_corridor() -> GeometricModule:
    """Geometric port of M01_StraightCorridor (Safe single forward threat)."""
    boundary = Polygon([(0.0, -1.0), (4.5, -1.0), (4.5, 1.0), (0.0, 1.0)])
    threat = GeometricThreat("M01_T1", Polygon([(3.8, -0.2), (4.2, -0.2), (4.2, 0.2), (3.8, 0.2)]), (4.0, 0.0), 2.5)
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(4.5, -1.0), (4.5, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (4.5, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="M01_StraightCorridor_Geom",
        name="Straight Corridor (Geom)",
        boundary=boundary,
        obstacles=[],
        ports=[port_in, port_out],
        threats=[threat],
        routes=[route],
        category="safe_corridor"
    )


def build_geometric_m03_pie_slice_left_sweep() -> GeometricModule:
    """Geometric port of M03_PieSliceLeftSweep (Sequential L-to-C sweep)."""
    boundary = Polygon([(0.0, -1.5), (6.75, -1.5), (6.75, 2.5), (0.0, 2.5)])
    obs = [
        Polygon([(2.0, 0.2), (2.5, 0.2), (2.5, 1.8), (2.0, 1.8)])
    ]
    threats = [
        GeometricThreat("M03_T1", Polygon([(2.6, 2.1), (3.0, 2.1), (3.0, 2.5), (2.6, 2.5)]), (2.8, 2.3), 2.0),
        GeometricThreat("M03_T2", Polygon([(5.0, -0.2), (5.4, -0.2), (5.4, 0.2), (5.0, 0.2)]), (5.2, 0.0), 2.0)
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(6.75, -1.0), (6.75, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (6.75, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="M03_PieSliceLeftSweep_Geom",
        name="Pie Slice Left Sweep (Geom)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="pie_slice"
    )


def build_geometric_m04_staggered_triple_reveal() -> GeometricModule:
    """Geometric port of M04_StaggeredTripleReveal (Staggered 3-threat sequence)."""
    boundary = Polygon([(0.0, -2.0), (8.1, -2.0), (8.1, 2.5), (0.0, 2.5)])
    obs = [
        Polygon([(1.5, 0.2), (2.0, 0.2), (2.0, 1.8), (1.5, 1.8)]),
        Polygon([(3.5, 0.2), (4.0, 0.2), (4.0, 1.8), (3.5, 1.8)]),
        Polygon([(5.5, 0.2), (6.0, 0.2), (6.0, 1.8), (5.5, 1.8)])
    ]
    threats = [
        GeometricThreat("M04_T1", Polygon([(2.1, 2.0), (2.5, 2.0), (2.5, 2.4), (2.1, 2.4)]), (2.3, 2.2), 2.0),
        GeometricThreat("M04_T2", Polygon([(4.1, 2.0), (4.5, 2.0), (4.5, 2.4), (4.1, 2.4)]), (4.3, 2.2), 2.0),
        GeometricThreat("M04_T3", Polygon([(6.1, 2.0), (6.5, 2.0), (6.5, 2.4), (6.1, 2.4)]), (6.3, 2.2), 2.0)
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.1, -1.0), (8.1, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.1, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="M04_StaggeredTripleReveal_Geom",
        name="Staggered Triple Reveal (Geom)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="staggered"
    )


def build_geometric_m11_rapid_crossfire_aperture() -> GeometricModule:
    """Geometric port of M11_RapidCrossfireAperture (Infeasible rapid crossfire trap)."""
    boundary = Polygon([(0.0, -3.0), (6.0, -3.0), (6.0, 3.0), (0.0, 3.0)])
    obs = [
        Polygon([(1.8, 0.5), (2.0, 0.5), (2.0, 3.0), (1.8, 3.0)]),
        Polygon([(1.8, -3.0), (2.0, -3.0), (2.0, -0.5), (1.8, -0.5)])
    ]
    threats = [
        GeometricThreat("M11_T1", Polygon([(3.8, -2.5), (4.2, -2.5), (4.2, -2.1), (3.8, -2.1)]), (4.0, -2.3), 0.30),
        GeometricThreat("M11_T2", Polygon([(3.8, 2.1), (4.2, 2.1), (4.2, 2.5), (3.8, 2.5)]), (4.0, 2.3), 0.30)
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(6.0, -1.0), (6.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (6.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="M11_RapidCrossfireAperture_Geom",
        name="Rapid Crossfire Aperture (Geom)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="lethal_trap",
        description="Infeasible alternating crossfire trap."
    )


def build_geometric_m08_high_concurrency_solvable() -> GeometricModule:
    """Geometric port of M08_HighConcurrencySolvable (3 simultaneous threats with generous deadlines)."""
    boundary = Polygon([(0.0, -3.0), (9.0, -3.0), (9.0, 3.0), (0.0, 3.0)])
    obs = [
        Polygon([(2.0, 0.6), (2.2, 0.6), (2.2, 3.0), (2.0, 3.0)]),
        Polygon([(2.0, -3.0), (2.2, -3.0), (2.2, -0.6), (2.0, -0.6)])
    ]
    threats = [
        GeometricThreat("M08_T1", Polygon([(5.8, -2.5), (6.2, -2.5), (6.2, -2.1), (5.8, -2.1)]), (6.0, -2.3), 3.0),
        GeometricThreat("M08_T2", Polygon([(5.8, -0.2), (6.2, -0.2), (6.2, 0.2), (5.8, 0.2)]), (6.0, 0.0), 3.0),
        GeometricThreat("M08_T3", Polygon([(5.8, 2.1), (6.2, 2.1), (6.2, 2.5), (5.8, 2.5)]), (6.0, 2.3), 3.0)
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(9.0, -1.0), (9.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (9.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="M08_HighConcurrencySolvable_Geom",
        name="High Concurrency Solvable (Geom)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="high_concurrency",
        description="Peak K_ICI=3, but 100% solvable due to generous 3.0s deadline slack."
    )


def build_geometric_m07_flank_bypass_room() -> GeometricModule:
    """Geometric port of M07_FlankBypassRoom (Dual route choice)."""
    boundary = Polygon([(0.0, -2.5), (9.0, -2.5), (9.0, 3.5), (0.0, 3.5)])
    obs = [
        Polygon([(0.0, 0.5), (8.5, 0.5), (8.5, 1.2), (0.0, 1.2)])
    ]
    threats = [
        GeometricThreat("M07_CT1", Polygon([(4.3, -2.2), (4.7, -2.2), (4.7, -1.8), (4.3, -1.8)]), (4.5, -2.0), 0.35),
        GeometricThreat("M07_CT2", Polygon([(4.3, -0.2), (4.7, -0.2), (4.7, 0.2), (4.3, 0.2)]), (4.5, 0.0), 0.35)
    ]
    port_in = GeometricPort(
        "PORT_IN",
        LineString([(0.0, -1.0), (0.0, 2.5)]),
        reset_zone=Polygon([(0.0, 1.5), (1.5, 1.5), (1.5, 3.0), (0.0, 3.0)])
    )
    port_out = GeometricPort("PORT_OUT", LineString([(9.0, -1.0), (9.0, 2.5)]))
    
    r_direct = GeometricRoute("direct", [(0.0, -0.5), (9.0, -0.5)], v_move_mps=4.5)
    r_bypass = GeometricRoute("bypass", [(0.0, 2.0), (9.0, 2.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="M07_FlankBypassRoom_Geom",
        name="Flank Bypass Room (Geom)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[r_direct, r_bypass],
        category="flank_choice",
        description="Direct path contains lethal crossfire; upper bypass provides 0-threat safety."
    )
