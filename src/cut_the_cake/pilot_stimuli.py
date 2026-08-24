"""Empirical Stimulus Library for Human/Self-Play Clearability Experiments.

Constructs:
1. Practice Arenas (Excluded from experimental analysis; used for pre-flight shakedown).
2. 12 Balanced Empirical Stimuli with 4 explicit feasibility-boundary-crossing pivots:
   - STIM_06 (Double Baffle):    M_rg = -5 -> M_pa = +2 (dM = +7) [Boundary Crossing]
   - STIM_07 (Spaced Baffle):    M_rg = -4 -> M_pa = +3 (dM = +7) [Boundary Crossing]
   - STIM_09 (Aperture Burst):   M_rg = -4 -> M_pa = +2 (dM = +6) [Boundary Crossing]
   - STIM_11 (Zigzag Flank):     M_rg = -6 -> M_pa = +1 (dM = +7) [Boundary Crossing]
"""

import math
from typing import List
from shapely.geometry import Polygon, LineString

from cut_the_cake.compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricThreat,
    GeometricPort
)


def build_practice_suite() -> List[GeometricModule]:
    """Construct 2 practice arenas for pre-experiment shakedown (excluded from analysis)."""
    boundary_std = Polygon([(0.0, -2.5), (8.0, -2.5), (8.0, 2.5), (0.0, 2.5)])
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route_std = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    p1 = GeometricModule(
        module_id="PRACTICE_01_Corridor",
        name="Practice: Straight Corridor",
        boundary=boundary_std,
        obstacles=[],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T_Prac1", Polygon([(2.8, -0.2), (3.2, -0.2), (3.2, 0.2), (2.8, 0.2)]), (3.0, 0.0), authored_due_window_s=1.20, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Practice"
    )

    p2 = GeometricModule(
        module_id="PRACTICE_02_CornerBaffle",
        name="Practice: Corner Baffle",
        boundary=boundary_std,
        obstacles=[Polygon([(1.5, -0.2), (1.8, -0.2), (1.8, 1.8), (1.5, 1.8)])],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T_Prac2", Polygon([(3.5, 0.8), (3.9, 0.8), (3.9, 1.2), (3.5, 1.2)]), (3.7, 1.0), authored_due_window_s=1.00, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Practice"
    )

    return [p1, p2]


def build_12_stimulus_pilot_suite() -> List[GeometricModule]:
    """Construct the 12 balanced empirical micro-arenas."""
    suite: List[GeometricModule] = []

    boundary_std = Polygon([(0.0, -2.5), (8.0, -2.5), (8.0, 2.5), (0.0, 2.5)])
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route_std = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    # 1. K0_Impossible_Ambush (M_rg = -6, M_pa = -6, dM = 0)
    suite.append(GeometricModule(
        module_id="STIM_01_K0_ImpossibleAmbush",
        name="Impossible Ambush (dM=0)",
        boundary=boundary_std,
        obstacles=[Polygon([(2.0, -0.2), (2.3, -0.2), (2.3, 2.0), (2.0, 2.0)])],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T1", Polygon([(0.3, 1.3), (0.7, 1.3), (0.7, 1.7), (0.3, 1.7)]), (0.5, 1.5), authored_due_window_s=0.40, service_duration_s=0.10),
            GeometricThreat("T2", Polygon([(4.0, 1.0), (4.6, 1.0), (4.6, 1.6), (4.0, 1.6)]), (4.3, 1.3), authored_due_window_s=0.40, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Control_K0"
    ))

    # 2. K0_Generous_Corridor (M_rg = +13, M_pa = +13, dM = 0)
    suite.append(GeometricModule(
        module_id="STIM_02_K0_GenerousCorridor",
        name="Generous Corridor (dM=0)",
        boundary=boundary_std,
        obstacles=[Polygon([(1.8, -0.2), (2.1, -0.2), (2.1, 1.8), (1.8, 1.8)])],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T1", Polygon([(0.3, 1.3), (0.7, 1.3), (0.7, 1.7), (0.3, 1.7)]), (0.5, 1.5), authored_due_window_s=0.85, service_duration_s=0.10),
            GeometricThreat("T2", Polygon([(4.0, 1.0), (4.6, 1.0), (4.6, 1.6), (4.0, 1.6)]), (4.3, 1.3), authored_due_window_s=0.85, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Control_K0"
    ))

    # 3. K0_Lethal_Crossfire (M_rg = -28, M_pa = -20, dM = +8)
    obs_doorway = [
        Polygon([(2.0, 0.6), (2.3, 0.6), (2.3, 2.5), (2.0, 2.5)]),
        Polygon([(2.0, -2.5), (2.3, -2.5), (2.3, -0.6), (2.0, -0.6)])
    ]
    t1_x = 2.0 + 3.0 * math.cos(math.radians(75.0))
    t1_y = 3.0 * math.sin(math.radians(75.0))
    t2_x = 2.0 + 3.0 * math.cos(math.radians(-75.0))
    t2_y = 3.0 * math.sin(math.radians(-75.0))
    suite.append(GeometricModule(
        module_id="STIM_03_K0_LethalCrossfire",
        name="Lethal Wide Crossfire (dM=0)",
        boundary=boundary_std,
        obstacles=obs_doorway,
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T1_L", Polygon([(t1_x-0.2, t1_y-0.2), (t1_x+0.2, t1_y-0.2), (t1_x+0.2, t1_y+0.2), (t1_x-0.2, t1_y+0.2)]), (t1_x, t1_y), authored_due_window_s=0.45, service_duration_s=0.10),
            GeometricThreat("T2_R", Polygon([(t2_x-0.2, t2_y-0.2), (t2_x+0.2, t2_y-0.2), (t2_x+0.2, t2_y+0.2), (t2_x-0.2, t2_y+0.2)]), (t2_x, t2_y), authored_due_window_s=0.45, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Control_K0"
    ))

    # 4. K0_Solvable_NarrowCrossfire (M_rg = -2, M_pa = -2, dM = 0)
    t1_x = 2.0 + 3.0 * math.cos(math.radians(15.0))
    t1_y = 3.0 * math.sin(math.radians(15.0))
    t2_x = 2.0 + 3.0 * math.cos(math.radians(-15.0))
    t2_y = 3.0 * math.sin(math.radians(-15.0))
    suite.append(GeometricModule(
        module_id="STIM_04_K0_NarrowCrossfire",
        name="Tight Narrow Crossfire (dM=0)",
        boundary=boundary_std,
        obstacles=obs_doorway,
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T1_L", Polygon([(t1_x-0.2, t1_y-0.2), (t1_x+0.2, t1_y-0.2), (t1_x+0.2, t1_y+0.2), (t1_x-0.2, t1_y+0.2)]), (t1_x, t1_y), authored_due_window_s=0.45, service_duration_s=0.10),
            GeometricThreat("T2_R", Polygon([(t2_x-0.2, t2_y-0.2), (t2_x+0.2, t2_y-0.2), (t2_x+0.2, t2_y+0.2), (t2_x-0.2, t2_y+0.2)]), (t2_x, t2_y), authored_due_window_s=0.45, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Control_K0"
    ))

    # 5. K2_Staggered_Corner (M_rg = +3, M_pa = +3, dM = 0)
    suite.append(GeometricModule(
        module_id="STIM_05_K2_CornerBoundary",
        name="Staggered Corner Boundary (dM=0)",
        boundary=boundary_std,
        obstacles=[Polygon([(1.5, -0.2), (1.8, -0.2), (1.8, 1.8), (1.5, 1.8)])],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T1", Polygon([(0.3, 1.3), (0.7, 1.3), (0.7, 1.7), (0.3, 1.7)]), (0.5, 1.5), authored_due_window_s=0.55, service_duration_s=0.10),
            GeometricThreat("T2", Polygon([(4.0, 1.0), (4.6, 1.0), (4.6, 1.6), (4.0, 1.6)]), (4.3, 1.3), authored_due_window_s=0.55, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Knowledge_K2"
    ))

    # 6. K3_Modest_Pivot (M_rg = -5 -> M_pa = +2, dM = +7) [BOUNDARY CROSSING]
    suite.append(GeometricModule(
        module_id="STIM_06_K3_ModestPivot",
        name="Modest Flank Pivot (Boundary Crossing dM=+7)",
        boundary=boundary_std,
        obstacles=[
            Polygon([(1.5, 0.4), (1.8, 0.4), (1.8, 2.5), (1.5, 2.5)]),
            Polygon([(3.0, -2.5), (3.3, -2.5), (3.3, -0.4), (3.0, -0.4)])
        ],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T1", Polygon([(2.2, 1.3), (2.6, 1.3), (2.6, 1.7), (2.2, 1.7)]), (2.4, 1.5), authored_due_window_s=0.68, service_duration_s=0.10),
            GeometricThreat("T2", Polygon([(3.7, -1.7), (4.1, -1.7), (4.1, -1.3), (3.7, -1.3)]), (3.9, -1.5), authored_due_window_s=0.68, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Knowledge_K3"
    ))

    # 7. K4_Feasible_Enhancement (M_rg = -4 -> M_pa = +3, dM = +7) [BOUNDARY CROSSING]
    suite.append(GeometricModule(
        module_id="STIM_07_K4_FeasibleEnhancement",
        name="Feasible Known Enhancement (Boundary Crossing dM=+7)",
        boundary=boundary_std,
        obstacles=[
            Polygon([(1.5, 0.4), (1.8, 0.4), (1.8, 2.5), (1.5, 2.5)]),
            Polygon([(3.5, -2.5), (3.8, -2.5), (3.8, -0.4), (3.5, -0.4)])
        ],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T1", Polygon([(2.2, 1.3), (2.6, 1.3), (2.6, 1.7), (2.2, 1.7)]), (2.4, 1.5), authored_due_window_s=0.60, service_duration_s=0.10),
            GeometricThreat("T2", Polygon([(4.2, -1.7), (4.6, -1.7), (4.6, -1.3), (4.2, -1.3)]), (4.4, -1.5), authored_due_window_s=0.60, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Knowledge_K4"
    ))

    # 8. K5_Sweep_Arc_Pivot (M_rg = +2 -> M_pa = +10, dM = +8)
    suite.append(GeometricModule(
        module_id="STIM_08_K5_SweepArcPivot",
        name="Sweep Arc Pivot (dM=+8)",
        boundary=boundary_std,
        obstacles=[
            Polygon([(1.5, 0.2), (1.8, 0.2), (1.8, 2.5), (1.5, 2.5)]),
            Polygon([(3.0, 0.2), (3.3, 0.2), (3.3, 2.5), (3.0, 2.5)])
        ],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T1", Polygon([(2.0, 1.2), (2.4, 1.2), (2.4, 1.6), (2.0, 1.6)]), (2.2, 1.4), authored_due_window_s=0.55, service_duration_s=0.10),
            GeometricThreat("T2", Polygon([(3.5, 1.2), (3.9, 1.2), (3.9, 1.6), (3.5, 1.6)]), (3.7, 1.4), authored_due_window_s=0.55, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Knowledge_K5"
    ))

    # 9. K6_Strong_Pivot_Aperture (M_rg = -4 -> M_pa = +2, dM = +6) [BOUNDARY CROSSING]
    from cut_the_cake.vizdoom_fixtures import build_family3_aperture_congestion
    f3_pivot = build_family3_aperture_congestion(stagger_m=1.40, index=2)
    suite.append(GeometricModule(
        module_id="STIM_09_K6_AperturePivot",
        name="Aperture Burst Pivot (Boundary Crossing dM=+6)",
        boundary=f3_pivot.boundary,
        obstacles=f3_pivot.obstacles,
        ports=f3_pivot.ports,
        threats=f3_pivot.threats,
        routes=f3_pivot.routes,
        category="Knowledge_K6"
    ))

    # 10. K6_Strong_Pivot_Flank (M_rg = +1 -> M_pa = +7, dM = +6)
    from cut_the_cake.vizdoom_fixtures import build_family4_three_threat_alternating
    f4_pivot = build_family4_three_threat_alternating(spacing_m=2.00, index=2)
    suite.append(GeometricModule(
        module_id="STIM_10_K6_AlternatingFlankPivot",
        name="Alternating Flank Pivot (dM=+6)",
        boundary=f4_pivot.boundary,
        obstacles=f4_pivot.obstacles,
        ports=f4_pivot.ports,
        threats=f4_pivot.threats,
        routes=f4_pivot.routes,
        category="Knowledge_K6"
    ))

    # 11. K7_Deep_Pivot_Zigzag (M_rg = -6 -> M_pa = +1, dM = +7) [BOUNDARY CROSSING]
    boundary_long = Polygon([(0.0, -2.5), (10.0, -2.5), (10.0, 2.5), (0.0, 2.5)])
    port_out_long = GeometricPort("PORT_OUT", LineString([(10.0, -1.0), (10.0, 1.0)]))
    route_long = GeometricRoute("main", [(0.0, 0.0), (10.0, 0.0)], v_move_mps=4.5)
    suite.append(GeometricModule(
        module_id="STIM_11_K7_ZigzagPivot",
        name="Deep Zigzag Pivot (Boundary Crossing dM=+7)",
        boundary=boundary_long,
        obstacles=[
            Polygon([(2.0, 0.3), (2.3, 0.3), (2.3, 2.5), (2.0, 2.5)]),
            Polygon([(3.5, -2.5), (3.8, -2.5), (3.8, -0.3), (3.5, -0.3)]),
            Polygon([(5.0, 0.3), (5.3, 0.3), (5.3, 2.5), (5.0, 2.5)])
        ],
        ports=[port_in, port_out_long],
        threats=[
            GeometricThreat("T1", Polygon([(2.6, 1.2), (3.0, 1.2), (3.0, 1.6), (2.6, 1.6)]), (2.8, 1.4), authored_due_window_s=0.98, service_duration_s=0.10),
            GeometricThreat("T2", Polygon([(4.1, -1.6), (4.5, -1.6), (4.5, -1.2), (4.1, -1.2)]), (4.3, -1.4), authored_due_window_s=0.98, service_duration_s=0.10),
            GeometricThreat("T3", Polygon([(5.6, 1.2), (6.0, 1.2), (6.0, 1.6), (5.6, 1.6)]), (5.8, 1.4), authored_due_window_s=0.98, service_duration_s=0.10)
        ],
        routes=[route_long],
        category="Knowledge_K7"
    ))

    # 12. K8_Severe_Knowledge_Gain (M_rg = -10, M_pa = -10, dM = 0)
    suite.append(GeometricModule(
        module_id="STIM_12_K8_SevereKnowledgeGain",
        name="Severe Knowledge Benefit Infeasible (dM=0)",
        boundary=boundary_std,
        obstacles=obs_doorway,
        ports=[port_in, port_out],
        threats=[
            GeometricThreat("T1_L", Polygon([(t1_x-0.2, t1_y-0.2), (t1_x+0.2, t1_y-0.2), (t1_x+0.2, t1_y+0.2), (t1_x-0.2, t1_y+0.2)]), (t1_x, t1_y), authored_due_window_s=0.35, service_duration_s=0.10),
            GeometricThreat("T2_R", Polygon([(t2_x-0.2, t2_y-0.2), (t2_x+0.2, t2_y-0.2), (t2_x+0.2, t2_y+0.2), (t2_x-0.2, t2_y+0.2)]), (t2_x, t2_y), authored_due_window_s=0.35, service_duration_s=0.10)
        ],
        routes=[route_std],
        category="Knowledge_K8"
    ))

    return suite
