"""Round 11.1: Multi-Family Micro-Arena Fixtures for External Predictive Validity (ViZDoom).

Constructs 60 independent micro-arenas across 6 distinct geometric families:
1. Family 1 — Staggered Wall Baffle: Manipulates reveal interval (r_2 - r_1)
2. Family 2 — Angular Crossfire Separation: Manipulates reticle travel Delta theta in [40°, 180°]
3. Family 3 — Multi-Aperture Burst Congestion: Manipulates simultaneous burst arrival density
4. Family 4 — 3-Threat Alternating Corridor: Manipulates sequence-dependent reticle thrashing
5. Family 5 — Deadline Compression: Manipulates hostile reaction / TTK urgency
6. Family 6 — Multi-Angle Flank Sweep: Manipulates smooth monotonic vs jagged clearing paths

All 60 micro-arenas are strictly parameter-conditioned and span M_tic in [-8, +8] tics.
"""

from __future__ import annotations
import math
from typing import List, Tuple, Dict, Optional
import numpy as np
from shapely.geometry import Polygon, LineString

from .compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricThreat,
    GeometricPort
)


# =============================================================================
# FAMILY 1: STAGGERED WALL BAFFLE (REVEAL INTERVAL)
# =============================================================================

def build_family1_staggered_wall(wall_x_m: float, index: int) -> GeometricModule:
    """Family 1: Wall position determines reveal interval r_2 - r_1."""
    boundary = Polygon([(0.0, -2.0), (8.0, -2.0), (8.0, 3.0), (0.0, 3.0)])
    obs = [
        Polygon([(wall_x_m, -0.2), (wall_x_m + 0.3, -0.2), (wall_x_m + 0.3, 1.8), (wall_x_m, 1.8)])
    ]
    threat1 = GeometricThreat(
        id="F1_T1_Left",
        polygon=Polygon([(0.3, 1.3), (0.7, 1.3), (0.7, 1.7), (0.3, 1.7)]),
        threat_anchor=(0.5, 1.5),
        authored_due_window_s=0.65,
        service_duration_s=0.10
    )
    threat2 = GeometricThreat(
        id="F1_T2_BehindWall",
        polygon=Polygon([(4.0, 1.0), (4.6, 1.0), (4.6, 1.6), (4.0, 1.6)]),
        threat_anchor=(4.3, 1.3),
        authored_due_window_s=0.65,
        service_duration_s=0.10
    )
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id=f"F1_WallBaffle_{index:02d}",
        name=f"Family 1: Wall Baffle #{index:02d} (x={wall_x_m:.2f}m)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=[threat1, threat2],
        routes=[route],
        category="Family_1_Wall_Interval",
        description="Manipulates reveal interval between T1 and T2."
    )


# =============================================================================
# FAMILY 2: ANGULAR CROSSFIRE SEPARATION (RETICLE TRAVEL)
# =============================================================================

def build_family2_angular_crossfire(angle_spread_deg: float, index: int) -> GeometricModule:
    """Family 2: Doorway opening revealing two threats at variable angular separation."""
    boundary = Polygon([(0.0, -3.5), (8.0, -3.5), (8.0, 3.5), (0.0, 3.5)])
    
    # Doorway baffle at x=2.0m with opening in y in [-0.6, 0.6]
    obs = [
        Polygon([(2.0, 0.6), (2.3, 0.6), (2.3, 3.5), (2.0, 3.5)]),
        Polygon([(2.0, -3.5), (2.3, -3.5), (2.3, -0.6), (2.0, -0.6)])
    ]
    
    # Left threat at fixed angle +30 deg relative to forward
    t1_x = 2.0 + 3.0 * math.cos(math.radians(30.0))
    t1_y = 3.0 * math.sin(math.radians(30.0))
    threat1 = GeometricThreat(
        id="F2_T1_Left",
        polygon=Polygon([(t1_x - 0.2, t1_y - 0.2), (t1_x + 0.2, t1_y - 0.2), (t1_x + 0.2, t1_y + 0.2), (t1_x - 0.2, t1_y + 0.2)]),
        threat_anchor=(t1_x, t1_y),
        authored_due_window_s=0.60,
        service_duration_s=0.10
    )

    # Right threat at variable angle: - (angle_spread - 30) deg
    theta_right = -(angle_spread_deg - 30.0)
    t2_x = 2.0 + 3.0 * math.cos(math.radians(theta_right))
    t2_y = 3.0 * math.sin(math.radians(theta_right))
    threat2 = GeometricThreat(
        id="F2_T2_Right",
        polygon=Polygon([(t2_x - 0.2, t2_y - 0.2), (t2_x + 0.2, t2_y - 0.2), (t2_x + 0.2, t2_y + 0.2), (t2_x - 0.2, t2_y + 0.2)]),
        threat_anchor=(t2_x, t2_y),
        authored_due_window_s=0.60,
        service_duration_s=0.10
    )

    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id=f"F2_Crossfire_{index:02d}",
        name=f"Family 2: Crossfire #{index:02d} (Δθ={angle_spread_deg:.0f}°)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=[threat1, threat2],
        routes=[route],
        category="Family_2_Angular_Spread",
        description="Manipulates reticle travel setup latency between two concurrent targets."
    )


# =============================================================================
# FAMILY 3: MULTI-APERTURE BURST CONGESTION (SIMULTANEOUS DENSITY)
# =============================================================================

def build_family3_aperture_congestion(stagger_m: float, index: int) -> GeometricModule:
    """Family 3: 3 threats revealed through slit apertures with variable stagger."""
    boundary = Polygon([(0.0, -3.0), (9.0, -3.0), (9.0, 3.0), (0.0, 3.0)])
    
    # 3 slit openings at x = 2.0, 2.0 + stagger, 2.0 + 2*stagger
    obs = []
    threats = []
    
    x1 = 2.0
    x2 = 2.0 + stagger_m
    x3 = 2.0 + 2.0 * stagger_m

    # Pillar baffles creating slits
    obs.append(Polygon([(1.8, 0.2), (2.0, 0.2), (2.0, 2.5), (1.8, 2.5)]))
    threats.append(GeometricThreat(
        id="F3_T1",
        polygon=Polygon([(2.8, 1.5), (3.2, 1.5), (3.2, 1.9), (2.8, 1.9)]),
        threat_anchor=(3.0, 1.7),
        authored_due_window_s=0.90,
        service_duration_s=0.10
    ))

    obs.append(Polygon([(x2 - 0.2, -2.5), (x2, -2.5), (x2, -0.2), (x2 - 0.2, -0.2)]))
    threats.append(GeometricThreat(
        id="F3_T2",
        polygon=Polygon([(x2 + 1.0, -1.9), (x2 + 1.4, -1.9), (x2 + 1.4, -1.5), (x2 + 1.0, -1.5)]),
        threat_anchor=(x2 + 1.2, -1.7),
        authored_due_window_s=0.90,
        service_duration_s=0.10
    ))

    obs.append(Polygon([(x3 - 0.2, 0.2), (x3, 0.2), (x3, 2.5), (x3 - 0.2, 2.5)]))
    threats.append(GeometricThreat(
        id="F3_T3",
        polygon=Polygon([(x3 + 1.0, 1.5), (x3 + 1.4, 1.5), (x3 + 1.4, 1.9), (x3 + 1.0, 1.9)]),
        threat_anchor=(x3 + 1.2, 1.7),
        authored_due_window_s=0.90,
        service_duration_s=0.10
    ))

    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(9.0, -1.0), (9.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (9.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id=f"F3_BurstCongestion_{index:02d}",
        name=f"Family 3: Burst Congestion #{index:02d} (stagger={stagger_m:.2f}m)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="Family_3_Burst_Density",
        description="Manipulates simultaneous arrival congestion across multi-threat burst."
    )


# =============================================================================
# FAMILY 4: 3-THREAT ALTERNATING CORRIDOR (SETUP BOTTLENECK)
# =============================================================================

def build_family4_three_threat_alternating(spacing_m: float, index: int) -> GeometricModule:
    """Family 4: Zigzag corridor (Left -> Right -> Left) with variable pillar spacing."""
    boundary = Polygon([(0.0, -2.5), (10.0, -2.5), (10.0, 2.5), (0.0, 2.5)])
    
    obs = [
        Polygon([(2.0, 0.2), (2.3, 0.2), (2.3, 2.2), (2.0, 2.2)]),
        Polygon([(2.0 + spacing_m, -2.2), (2.3 + spacing_m, -2.2), (2.3 + spacing_m, -0.2), (2.0 + spacing_m, -0.2)]),
        Polygon([(2.0 + 2*spacing_m, 0.2), (2.3 + 2*spacing_m, 0.2), (2.3 + 2*spacing_m, 2.2), (2.0 + 2*spacing_m, 2.2)])
    ]
    
    threats = [
        GeometricThreat("F4_T1_L", Polygon([(2.8, 1.2), (3.2, 1.2), (3.2, 1.6), (2.8, 1.6)]), (3.0, 1.4), authored_due_window_s=0.85, service_duration_s=0.10),
        GeometricThreat("F4_T2_R", Polygon([(2.8 + spacing_m, -1.6), (3.2 + spacing_m, -1.6), (3.2 + spacing_m, -1.2), (2.8 + spacing_m, -1.2)]), (3.0 + spacing_m, -1.4), authored_due_window_s=0.85, service_duration_s=0.10),
        GeometricThreat("F4_T3_L", Polygon([(2.8 + 2*spacing_m, 1.2), (3.2 + 2*spacing_m, 1.2), (3.2 + 2*spacing_m, 1.6), (2.8 + 2*spacing_m, 1.6)]), (3.0 + 2*spacing_m, 1.4), authored_due_window_s=0.85, service_duration_s=0.10)
    ]

    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(10.0, -1.0), (10.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (10.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id=f"F4_Alternating_{index:02d}",
        name=f"Family 4: Alternating #{index:02d} (spacing={spacing_m:.2f}m)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="Family_4_Switching_Bottleneck",
        description="Manipulates sequence-dependent reticle zigzagging costs."
    )


# =============================================================================
# FAMILY 5: DEADLINE COMPRESSION (REACTION / TTK URGENCY)
# =============================================================================

def build_family5_deadline_compression(due_window_s: float, index: int) -> GeometricModule:
    """Family 5: Fixed geometric room with parametric deadline compression."""
    boundary = Polygon([(0.0, -2.0), (8.0, -2.0), (8.0, 2.5), (0.0, 2.5)])
    obs = [
        Polygon([(1.2, -0.2), (1.5, -0.2), (1.5, 1.8), (1.2, 1.8)])
    ]
    threat1 = GeometricThreat(
        id="F5_T1_Left",
        polygon=Polygon([(0.3, 1.3), (0.7, 1.3), (0.7, 1.7), (0.3, 1.7)]),
        threat_anchor=(0.5, 1.5),
        authored_due_window_s=due_window_s,
        service_duration_s=0.10
    )
    threat2 = GeometricThreat(
        id="F5_T2_Center",
        polygon=Polygon([(4.0, 0.8), (4.6, 0.8), (4.6, 1.4), (4.0, 1.4)]),
        threat_anchor=(4.3, 1.1),
        authored_due_window_s=due_window_s,
        service_duration_s=0.10
    )
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id=f"F5_DeadlineComp_{index:02d}",
        name=f"Family 5: Deadline Compression #{index:02d} (D={due_window_s:.2f}s)",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=[threat1, threat2],
        routes=[route],
        category="Family_5_Deadline_Urgency",
        description="Manipulates hostile TTK / response deadline urgency."
    )


# =============================================================================
# FAMILY 6: MULTI-ANGLE FLANK SWEEP (SMOOTH VS JAGGED)
# =============================================================================

def build_family6_flank_sweep_smoothness(is_smooth: bool, angular_scale: float, index: int) -> GeometricModule:
    """Family 6: 3 threats arranged in smooth monotonic arc vs jagged alternating zigzag."""
    boundary = Polygon([(0.0, -3.0), (8.0, -3.0), (8.0, 3.0), (0.0, 3.0)])
    
    if is_smooth:
        # Smooth: +theta -> 0 -> -theta
        angles = [+angular_scale, 0.0, -angular_scale]
    else:
        # Jagged: +theta -> -theta -> +0.7*theta
        angles = [+angular_scale, -angular_scale, +0.7 * angular_scale]

    threats = []
    for i, ang in enumerate(angles, 1):
        dist_m = 3.5
        rad = math.radians(ang)
        tx = 2.0 + dist_m * math.cos(rad)
        ty = dist_m * math.sin(rad)
        threats.append(GeometricThreat(
            id=f"F6_T{i}",
            polygon=Polygon([(tx - 0.2, ty - 0.2), (tx + 0.2, ty - 0.2), (tx + 0.2, ty + 0.2), (tx - 0.2, ty + 0.2)]),
            threat_anchor=(tx, ty),
            authored_due_window_s=0.90,
            service_duration_s=0.10
        ))

    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    mode_str = "Smooth" if is_smooth else "Jagged"
    return GeometricModule(
        module_id=f"F6_Sweep_{mode_str}_{index:02d}",
        name=f"Family 6: {mode_str} Sweep #{index:02d} (θ_scale={angular_scale:.0f}°)",
        boundary=boundary,
        obstacles=[],
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="Family_6_Flank_Path_Smoothness",
        description="Manipulates monotonic pie slice vs jagged alternating angular clearing paths."
    )


# =============================================================================
# BENCHMARK SUITE GENERATOR (60 INDEPENDENT MICRO-ARENAS)
# =============================================================================

def build_round11_benchmark_suite() -> List[GeometricModule]:
    """Generate 60 diverse micro-arenas across all 6 geometric families."""
    arenas: List[GeometricModule] = []

    # Family 1: 10 wall positions from x=0.2m to x=2.0m
    f1_walls = np.linspace(0.2, 2.0, 10)
    for idx, wx in enumerate(f1_walls, 1):
        arenas.append(build_family1_staggered_wall(wall_x_m=float(wx), index=idx))

    # Family 2: 10 angular spreads from 30 deg to 160 deg
    f2_angles = np.linspace(30.0, 160.0, 10)
    for idx, ang in enumerate(f2_angles, 1):
        arenas.append(build_family2_angular_crossfire(angle_spread_deg=float(ang), index=idx))

    # Family 3: 10 aperture staggers from 0.0m to 1.5m
    f3_staggers = np.linspace(0.0, 1.5, 10)
    for idx, stag in enumerate(f3_staggers, 1):
        arenas.append(build_family3_aperture_congestion(stagger_m=float(stag), index=idx))

    # Family 4: 10 alternating corridor pillar spacings from 0.3m to 2.2m
    f4_spacings = np.linspace(0.3, 2.2, 10)
    for idx, sp in enumerate(f4_spacings, 1):
        arenas.append(build_family4_three_threat_alternating(spacing_m=float(sp), index=idx))

    # Family 5: 10 deadline due windows from 0.40s to 1.10s
    f5_dues = np.linspace(0.40, 1.10, 10)
    for idx, due in enumerate(f5_dues, 1):
        arenas.append(build_family5_deadline_compression(due_window_s=float(due), index=idx))

    # Family 6: 5 smooth sweeps and 5 jagged sweeps across angular scales [20°, 75°]
    f6_scales = np.linspace(20.0, 75.0, 5)
    for idx, sc in enumerate(f6_scales, 1):
        arenas.append(build_family6_flank_sweep_smoothness(is_smooth=True, angular_scale=float(sc), index=idx))
    for idx, sc in enumerate(f6_scales, 6):
        arenas.append(build_family6_flank_sweep_smoothness(is_smooth=False, angular_scale=float(sc), index=idx))

    return arenas


# Helpers for backwards compatibility & targeted Gate tests
def build_parametric_wall_arena(wall_x_m: float, name_suffix: str = "") -> GeometricModule:
    return build_family1_staggered_wall(wall_x_m, index=1)

def build_disagreement_arena_kici_blindspot() -> GeometricModule:
    """[A ∩ B ∩ ¬C]: K_static <= 2, but L*_tic > 0 (Deadly trap accepted by static concurrency)."""
    boundary = Polygon([(0.0, -3.0), (10.0, -3.0), (10.0, 3.0), (0.0, 3.0)])
    obs = [
        Polygon([(2.5, 0.2), (3.0, 0.2), (3.0, 2.0), (2.5, 2.0)]),
        Polygon([(4.0, -2.0), (4.5, -2.0), (4.5, -0.2), (4.0, -0.2)])
    ]
    threat1 = GeometricThreat(
        id="T1_LeftCross",
        polygon=Polygon([(3.5, 2.1), (4.1, 2.1), (4.1, 2.7), (3.5, 2.7)]),
        threat_anchor=(3.8, 2.4),
        authored_due_window_s=0.62,
        service_duration_s=0.10
    )
    threat2 = GeometricThreat(
        id="T2_RightCross",
        polygon=Polygon([(5.0, -2.7), (5.6, -2.7), (5.6, -2.1), (5.0, -2.1)]),
        threat_anchor=(5.3, -2.4),
        authored_due_window_s=0.62,
        service_duration_s=0.10
    )
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(10.0, -1.0), (10.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (10.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="Arena_Disagreement_BlindSpot",
        name="KICI Blind Spot Arena [A ∩ B ∩ ¬C]",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=[threat1, threat2],
        routes=[route],
        category="disagreement_class",
        description="Peak K_static=2, but L*_tic > 0 due to wide-angle reticle travel latency."
    )

def build_disagreement_arena_kici_falsealarm() -> GeometricModule:
    """[A ∩ ¬B ∩ C]: K_static > 2 (Peak=3), but L*_tic <= 0 (Solvable multi-threat rejected by KICI)."""
    boundary = Polygon([(0.0, -3.0), (12.0, -3.0), (12.0, 3.0), (0.0, 3.0)])
    threat1 = GeometricThreat(
        id="T1_CloseForward",
        polygon=Polygon([(3.0, 0.8), (3.6, 0.8), (3.6, 1.4), (3.0, 1.4)]),
        threat_anchor=(3.3, 1.1),
        authored_due_window_s=1.00,
        service_duration_s=0.10
    )
    threat2 = GeometricThreat(
        id="T2_MidLeft",
        polygon=Polygon([(6.0, 1.5), (6.6, 1.5), (6.6, 2.1), (6.0, 2.1)]),
        threat_anchor=(6.3, 1.8),
        authored_due_window_s=2.20,
        service_duration_s=0.10
    )
    threat3 = GeometricThreat(
        id="T3_FarRight",
        polygon=Polygon([(9.0, -1.8), (9.6, -1.8), (9.6, -1.2), (9.0, -1.2)]),
        threat_anchor=(9.3, -1.5),
        authored_due_window_s=3.40,
        service_duration_s=0.10
    )
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(12.0, -1.0), (12.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (12.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="Arena_Disagreement_FalseAlarm",
        name="KICI False Alarm Arena [A ∩ ¬B ∩ C]",
        boundary=boundary,
        obstacles=[],
        ports=[port_in, port_out],
        threats=[threat1, threat2, threat3],
        routes=[route],
        category="disagreement_class",
        description="Peak K_static=3, but L*_tic <= 0 due to staggered arrival deadlines."
    )

def build_large_margin_arena() -> GeometricModule:
    """Large positive margin arena (M_tic >> 0) testing policy robustness."""
    boundary = Polygon([(0.0, -2.0), (10.0, -2.0), (10.0, 2.0), (0.0, 2.0)])
    threat = GeometricThreat(
        id="T_Generous",
        polygon=Polygon([(5.0, 0.5), (5.6, 0.5), (5.6, 1.1), (5.0, 1.1)]),
        threat_anchor=(5.3, 0.8),
        authored_due_window_s=3.00,
        service_duration_s=0.10
    )
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(10.0, -1.0), (10.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (10.0, 0.0)], v_move_mps=4.5)

    return GeometricModule(
        module_id="Arena_LargeMargin",
        name="Large Tactical Margin Arena (M >> 0)",
        boundary=boundary,
        obstacles=[],
        ports=[port_in, port_out],
        threats=[threat],
        routes=[route],
        category="large_margin",
        description="High tactical margin (M_tic >> 0) solvable by all policies."
    )

