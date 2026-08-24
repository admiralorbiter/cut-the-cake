"""The 11 Canonical Adversarial Scientific Fixtures [G + C + P]."""

from __future__ import annotations
import math
from typing import Dict, List, Tuple
import numpy as np
from shapely.geometry import Polygon, LineString, box

from .model import World, ThreatRegion, Module, Port, CombatModel, PlayerModel
from .geometry import simulate_corner_duel_gpa


def make_rect_poly(x0: float, y0: float, x1: float, y1: float) -> Polygon:
    return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def scenario_1_pie_slice() -> Tuple[World, List[Tuple[float, float]]]:
    """Scenario 1: Pie Slice. Three threats behind a progressive corner (A1 -> A2 -> A3). Expected: W*=1, L*<=0, Solvable."""
    wall = make_rect_poly(4.0, 0.0, 5.0, 10.0)
    t1 = ThreatRegion(id="A1", polygon=make_rect_poly(6.5, 11.5, 7.5, 12.5), label="A1: Shallow Angle")
    t2 = ThreatRegion(id="A2", polygon=make_rect_poly(8.5, 9.0, 9.5, 10.0), label="A2: Mid Angle")
    t3 = ThreatRegion(id="A3", polygon=make_rect_poly(7.0, 3.5, 8.0, 4.5), label="A3: Deep Angle")

    world = World(
        bounds=(0.0, 0.0, 15.0, 15.0),
        obstacles=[wall],
        threats=[t1, t2, t3]
    )
    path = [(1.0, 5.0), (2.0, 7.5), (3.0, 10.0), (4.5, 12.0), (8.5, 12.0)]
    return world, path


def scenario_2_triple_reveal() -> Tuple[World, List[Tuple[float, float]]]:
    """Scenario 2: Simultaneous Triple Reveal. Single threshold exposing left, center, right threats simultaneously."""
    wall_left = make_rect_poly(0.0, 5.0, 4.4, 6.0)
    wall_right = make_rect_poly(5.6, 5.0, 10.0, 6.0)
    
    t_left = ThreatRegion(id="A1_Left", polygon=make_rect_poly(-2.0, 8.0, -1.0, 9.0), label="Left Window")
    t_center = ThreatRegion(id="A2_Center", polygon=make_rect_poly(4.5, 13.0, 5.5, 14.0), label="Center Door")
    t_right = ThreatRegion(id="A3_Right", polygon=make_rect_poly(11.0, 8.0, 12.0, 9.0), label="Right Balcony", elevation_m=4.0)

    world = World(
        bounds=(-5.0, 0.0, 15.0, 16.0),
        obstacles=[wall_left, wall_right],
        threats=[t_left, t_center, t_right]
    )
    path = [(5.0, 2.0), (5.0, 5.5), (5.0, 7.5)]
    return world, path


def scenario_3_large_isovist_control() -> Tuple[World, List[Tuple[float, float]]]:
    """Scenario 3: Large-Isovist Control. Huge 400m^2 room with exactly ONE hostile aperture."""
    t1 = ThreatRegion(id="T_Solo", polygon=make_rect_poly(18.0, 18.0, 19.0, 19.0), label="Far Doorway")
    world = World(
        bounds=(0.0, 0.0, 20.0, 20.0),
        obstacles=[],
        threats=[t1]
    )
    path = [(2.0, 2.0), (10.0, 10.0)]
    return world, path


def scenario_4_tiny_multi_aperture() -> Tuple[World, List[Tuple[float, float]]]:
    """Scenario 4: Tiny Multi-Aperture Room. Small 16m^2 room with THREE independent firing openings."""
    w_bot_l = make_rect_poly(0.0, 0.0, 1.6, 0.4)
    w_bot_r = make_rect_poly(2.4, 0.0, 4.0, 0.4)
    w_left_b = make_rect_poly(0.0, 0.0, 0.4, 1.6)
    w_left_t = make_rect_poly(0.0, 2.4, 0.4, 4.0)
    w_right_b = make_rect_poly(3.6, 0.0, 4.0, 1.6)
    w_right_t = make_rect_poly(3.6, 2.4, 4.0, 4.0)
    w_top = make_rect_poly(0.0, 3.6, 4.0, 4.0)

    t1 = ThreatRegion(id="Slit_Left", polygon=make_rect_poly(-3.0, 1.5, -2.0, 2.5), label="Slit Left")
    t2 = ThreatRegion(id="Slit_Right", polygon=make_rect_poly(6.0, 1.5, 7.0, 2.5), label="Slit Right")
    t3 = ThreatRegion(id="Slit_Bottom", polygon=make_rect_poly(1.5, -3.0, 2.5, -2.0), label="Slit Bottom")

    world = World(
        bounds=(-5.0, -5.0, 10.0, 10.0),
        obstacles=[w_bot_l, w_bot_r, w_left_b, w_left_t, w_right_b, w_right_t, w_top],
        threats=[t1, t2, t3]
    )
    path = [(1.8, 1.8), (2.2, 2.2)]
    return world, path


def scenario_5_composition_resonance() -> Tuple[Module, Port, Module, Port]:
    """Scenario 5: Composition Resonance. Module A and B are each internally certified (K<=1), but unconstrained composition creates external conflict clique = 2 > 1."""
    mod_a_bound = make_rect_poly(0.0, 0.0, 10.0, 8.0)
    obs_a = [make_rect_poly(0.0, 0.0, 3.5, 8.0), make_rect_poly(6.5, 0.0, 10.0, 8.0)]
    t_a1 = ThreatRegion(id="T_A1", polygon=make_rect_poly(1.0, 4.0, 2.0, 5.0), label="Door A1")
    port_a = Port(
        id="Port_A_North",
        segment=LineString([(3.5, 8.0), (6.5, 8.0)]),
        max_external_budget=1,
        max_depth=15.0
    )
    mod_a = Module(id="Module_A", boundary=mod_a_bound, obstacles=obs_a, threats=[t_a1], ports=[port_a])

    # Module B: Internally partitioned by a vertical wall at x in [4.5, 5.5] so internal points see at most 1 threat (K_B <= 1)
    # T_B1 and T_B2 are placed wide at (0.2, 9.0) and (9.8, 9.0), creating >130 deg angular separation from Module A port -> external conflict clique = 2 > 1
    mod_b_bound = make_rect_poly(0.0, 8.0, 10.0, 20.0)
    obs_b = [make_rect_poly(4.5, 8.5, 5.5, 20.0)]  # Internal dividing wall separating left and right inside B
    t_b1 = ThreatRegion(id="T_B1_Left", polygon=make_rect_poly(0.0, 8.5, 1.0, 9.5), label="Sniper Left", elevation_m=2.0)
    t_b2 = ThreatRegion(id="T_B2_Right", polygon=make_rect_poly(9.0, 8.5, 10.0, 9.5), label="Sniper Right", elevation_m=2.0)
    port_b = Port(
        id="Port_B_South",
        segment=LineString([(3.5, 8.0), (6.5, 8.0)]),
        max_external_budget=1,
        max_depth=15.0
    )
    mod_b = Module(id="Module_B", boundary=mod_b_bound, obstacles=obs_b, threats=[t_b1, t_b2], ports=[port_b])

    return mod_a, port_a, mod_b, port_b


def scenario_6_contract_repair() -> Tuple[Module, Port, Module, Port]:
    """Scenario 6: Contract Repair. Adding an occluding baffle in Module B blocks the right sniper from Port A."""
    mod_a, port_a, mod_b, port_b = scenario_5_composition_resonance()
    # Baffle wall blocking T_B2_Right from being seen through Port A
    baffle = make_rect_poly(5.5, 8.0, 9.0, 9.5)
    mod_b.obstacles.append(baffle)
    return mod_a, port_a, mod_b, port_b


def scenario_7_nonadjacent_leak() -> Tuple[Module, Port, Module, Port, ThreatRegion]:
    """Scenario 7: Nonadjacent Leak. Ray from Module A reaches external threat in Module C without passing Port A."""
    mod_a_bound = make_rect_poly(0.0, 0.0, 6.0, 6.0)
    port_a = Port(id="Port_East", segment=LineString([(6.0, 2.0), (6.0, 4.0)]))
    mod_a = Module(id="Module_A", boundary=mod_a_bound, obstacles=[], threats=[], ports=[port_a])

    mod_b_bound = make_rect_poly(6.0, 0.0, 12.0, 6.0)
    port_b = Port(id="Port_West", segment=LineString([(6.0, 2.0), (6.0, 4.0)]))
    
    t_c = ThreatRegion(id="T_C_Sniper", polygon=make_rect_poly(15.0, 5.0, 16.0, 6.0), label="Module C Sniper")
    mod_b = Module(id="Module_B", boundary=mod_b_bound, obstacles=[], threats=[t_c], ports=[port_b])

    return mod_a, port_a, mod_b, port_b, t_c


def scenario_8_corner_duel_simulation(
    setback_a: float,
    setback_b: float,
    dt_s: float = 0.01,
    agent_radius_m: float = 0.3
) -> Tuple[float, float, float]:
    """Scenario 8: Corner-Distance Geometry via Finite-Disk Ray Simulation."""
    return simulate_corner_duel_gpa(
        corner_pt=(5.0, 5.0),
        setback_a=setback_a,
        setback_b=setback_b,
        agent_radius_m=agent_radius_m,
        vis_threshold=0.15,
        speed_mps=3.0,
        response_margin_s=0.45,
        dt_s=dt_s
    )


def scenario_9_clique_counterexample() -> Tuple[World, List[Tuple[float, float]], CombatModel, PlayerModel]:
    """Scenario 9: True C_5 5-Cycle Counterexample (ω(H)=2, exactly 5 edges, regular degree 2).

    Simultaneous release (r_j = 0.0s) forces minimum service completion = 2.05s against due date 0.40s,
    producing exact optimal maximum lateness L*(γ) = +1.65s (Unsolvable).
    """
    center = (5.0, 5.0)
    radius = 5.0
    threats = []

    # 5 threats at exactly 72 deg radial increments: 0, 72, 144, 216, 288 deg
    for idx, deg in enumerate([0.0, 72.0, 144.0, 216.0, 288.0]):
        rad = math.radians(deg)
        tx = center[0] + radius * math.cos(rad)
        ty = center[1] + radius * math.sin(rad)
        poly = make_rect_poly(tx - 0.25, ty - 0.25, tx + 0.25, ty + 0.25)
        threats.append(ThreatRegion(id=f"T_{chr(ord('A') + idx)}", polygon=poly, label=f"Threat {chr(ord('A') + idx)} ({deg}°))"))

    world = World(
        bounds=(0.0, 0.0, 10.0, 10.0),
        obstacles=[],
        threats=threats
    )
    path = [center, (center[0] + 0.01, center[1])]

    combat = CombatModel(base_ttk_s=0.20, opp_reaction_s=0.20)  # deadline = 0.40s
    player = PlayerModel(acquisition_latency_s=0.15, aim_velocity_deg_s=360.0, inspect_duration_s=0.10)

    return world, path, combat, player


def scenario_9b_matched_solvable_control() -> Tuple[World, List[Tuple[float, float]], CombatModel, PlayerModel]:
    """Scenario 9b: True 5-Threat Matched Control.

    Identical 5 threats and C_5 conflict graph (ω(H)=2) as Scenario 9, but with radial pie-slicing
    occluders staggering releases along a trajectory, yielding L*(γ) <= 0 (Solvable).
    """
    w9, _, combat, player = scenario_9_clique_counterexample()
    threats = w9.threats

    # Shields leaving slits for each threat as the path visits them sequentially
    obs = [
        make_rect_poly(4.0, 5.2, 7.5, 8.5),   # Shield between T_A and T_B
        make_rect_poly(1.5, 5.2, 3.8, 8.5),   # Shield between T_B and T_C
        make_rect_poly(1.5, 1.5, 3.8, 4.8),   # Shield between T_C and T_D
        make_rect_poly(4.0, 1.5, 7.5, 4.8),   # Shield between T_D and T_E
    ]

    world = World(
        bounds=(0.0, 0.0, 10.0, 10.0),
        obstacles=obs,
        threats=threats
    )
    # Smooth curved path orbiting center:
    # 1. Spawn at (7.0, 3.0) moving to (8.0, 4.0) (heading 45 deg, faces T_A at 31 deg, clears in 0.29s)
    # 2. Advance to (7.5, 6.0) (reveals T_B at (6.5, 9.7), clears in 0.32s)
    # 3. Advance to (5.5, 7.5) -> (2.5, 7.0) (reveals T_C at (1.0, 7.9), clears in 0.32s)
    # 4. Advance to (2.5, 3.0) (reveals T_D at (1.0, 2.1), clears in 0.32s)
    # 5. Advance to (6.0, 2.5) (reveals T_E at (6.5, 0.3), clears in 0.32s)
    path = [(7.0, 3.0), (8.0, 4.0), (7.5, 6.0), (5.5, 7.5), (2.5, 7.0), (2.5, 3.0), (6.0, 2.5)]

    return world, path, combat, player


def scenario_10_aperture_split_merge() -> Tuple[World, List[Tuple[float, float]]]:
    """Scenario 10: Aperture Split/Merge. Moving past an occluding pillar splits one threat region into two visible slivers."""
    t_wide = ThreatRegion(id="T_WideBay", polygon=make_rect_poly(2.0, 8.0, 8.0, 9.0), label="Wide Bay")
    pillar = make_rect_poly(4.5, 3.5, 5.5, 4.5)

    world = World(
        bounds=(0.0, 0.0, 10.0, 10.0),
        obstacles=[pillar],
        threats=[t_wide]
    )
    path = [(1.0, 1.0), (5.0, 1.0), (9.0, 1.0)]
    return world, path


def scenario_11_contract_insufficiency_counterexample() -> Tuple[Module, Port, Module, Port, List[Tuple[float, float]], CombatModel, PlayerModel]:
    """Scenario 11: Contract Insufficiency Counterexample.

    Module A and B satisfy the K_ICI Composable Visibility Contract (internal K <= 1, external budget = 1,
    external depth <= D_max, no escaping rays, global K_ICI <= 2).
    YET when traversed, the path exposes 3 tight, rapidly alternating threats, forcing L*(γ) > 0 (Infeasible).
    Proves that K_ICI contracts are necessary but insufficient for true tactical clearability.
    """
    mod_a_bound = make_rect_poly(0.0, 0.0, 10.0, 8.0)
    # Side walls in Module A ensuring rays cannot escape outside Port A
    obs_a = [make_rect_poly(0.0, 0.0, 3.5, 8.0), make_rect_poly(6.5, 0.0, 10.0, 8.0)]
    port_a = Port(
        id="Port_A_North",
        segment=LineString([(3.5, 8.0), (6.5, 8.0)]),
        max_external_budget=1,
        max_depth=15.0
    )
    mod_a = Module(id="Module_A", boundary=mod_a_bound, obstacles=obs_a, threats=[], ports=[port_a])

    # Module B: Corridor with side walls and 3 alternating threats
    mod_b_bound = make_rect_poly(0.0, 8.0, 10.0, 20.0)
    obs_b_left = make_rect_poly(0.0, 8.0, 3.5, 20.0)
    obs_b_right = make_rect_poly(6.5, 8.0, 10.0, 20.0)
    # Divider blocking T_B2 from being seen from Port A directly
    obs_b_div = make_rect_poly(4.5, 11.0, 6.5, 12.0)

    t_b1 = ThreatRegion(id="T_B1", polygon=make_rect_poly(3.6, 9.5, 4.4, 10.5), label="Corridor Left")
    t_b2 = ThreatRegion(id="T_B2", polygon=make_rect_poly(5.6, 12.5, 6.4, 13.5), label="Corridor Right")
    t_b3 = ThreatRegion(id="T_B3", polygon=make_rect_poly(3.6, 14.5, 4.4, 15.5), label="Corridor Left 2")

    port_b = Port(
        id="Port_B_South",
        segment=LineString([(3.5, 8.0), (6.5, 8.0)]),
        max_external_budget=1,
        max_depth=15.0
    )
    mod_b = Module(
        id="Module_B",
        boundary=mod_b_bound,
        obstacles=[obs_b_left, obs_b_right, obs_b_div],
        threats=[t_b1, t_b2, t_b3],
        ports=[port_b]
    )

    path = [(5.0, 7.0), (5.0, 9.0), (5.0, 11.5), (5.0, 14.0)]

    combat = CombatModel(base_ttk_s=0.20, opp_reaction_s=0.15)  # Tight deadline = 0.35s
    player = PlayerModel(acquisition_latency_s=0.15, aim_velocity_deg_s=360.0, inspect_duration_s=0.10)

    return mod_a, port_a, mod_b, port_b, path, combat, player


def scenario_12_scalar_interface_counterexample() -> Tuple[
    World, List[Tuple[float, float]],
    World, List[Tuple[float, float]],
    CombatModel, PlayerModel
]:
    """Scenario 12: Scalar Schedulability Interface Counterexample.

    Demonstrates an adversarial pair of modules X and Y having the exact same scalar signature Σ:
    - Identical Arrival Curve: α+(Δ) (4 jobs revealed at Δt = 0.30s increments)
    - Identical Minimum Slack: σ_min = 0.30s
    - Identical Max Setup: Θ_max = 0.539s
    - Identical Threat Count: n = 4
    - Identical Peak Concurrency: K_ICI <= 2

    YET:
    - Module X (Unidirectional Left-Flank alignment): L*(X) <= 0 (SOLVABLE)
    - Module Y (Alternating Left-Right Zigzag):        L*(Y) > 0  (UNSOLVABLE)

    Proves that scalar schedulability interfaces fail due to crosshair orientation memory,
    necessitating State-Conditioned Schedulability Interfaces Σ_p(θ_in, Δ).
    """
    combat = CombatModel(base_ttk_s=0.55, opp_reaction_s=0.15)  # d_j = 0.70s
    player = PlayerModel(acquisition_latency_s=0.15, aim_velocity_deg_s=360.0, inspect_duration_s=0.10)

    # Module X: 4 threats on the left side (x in [1.0, 3.0]), separated by horizontal baffles
    threats_x = [
        ThreatRegion(id="T_X1", polygon=make_rect_poly(1.0, 1.0, 3.0, 2.5), label="X Left 1"),
        ThreatRegion(id="T_X2", polygon=make_rect_poly(1.0, 3.8, 3.0, 5.2), label="X Left 2"),
        ThreatRegion(id="T_X3", polygon=make_rect_poly(1.0, 6.5, 3.0, 7.9), label="X Left 3"),
        ThreatRegion(id="T_X4", polygon=make_rect_poly(1.0, 9.0, 3.0, 10.4), label="X Left 4"),
    ]
    # Horizontal divider baffles extending from x=0.0 to x=4.5 at y = 3.0, 5.8, 8.4
    obs_x = [
        make_rect_poly(0.0, 2.99, 4.5, 3.01),
        make_rect_poly(0.0, 5.79, 4.5, 5.81),
        make_rect_poly(0.0, 8.39, 4.5, 8.41),
    ]
    world_x = World(bounds=(0.0, 0.0, 10.0, 12.0), obstacles=obs_x, threats=threats_x)
    path_x = [(5.0, 1.5), (5.0, 4.0), (5.0, 6.5), (5.0, 9.5)]

    # Module Y: 4 alternating threats (Left, Right, Left, Right)
    threats_y = [
        ThreatRegion(id="T_Y1", polygon=make_rect_poly(1.0, 1.0, 3.0, 2.5), label="Y Left 1"),
        ThreatRegion(id="T_Y2", polygon=make_rect_poly(7.0, 3.8, 9.0, 5.2), label="Y Right 1"),
        ThreatRegion(id="T_Y3", polygon=make_rect_poly(1.0, 6.5, 3.0, 7.9), label="Y Left 2"),
        ThreatRegion(id="T_Y4", polygon=make_rect_poly(7.0, 9.0, 9.0, 10.4), label="Y Right 2"),
    ]
    # Symmetrically matched divider baffles at the exact same tip y-coordinates
    obs_y = [
        make_rect_poly(5.5, 2.99, 10.0, 3.01),  # Blocks T_Y2 (Right) from initial position
        make_rect_poly(0.0, 5.79, 4.5, 5.81),   # Blocks T_Y3 (Left) until passing y=5.8
        make_rect_poly(5.5, 8.39, 10.0, 8.41),  # Blocks T_Y4 (Right) until passing y=8.4
    ]
    world_y = World(bounds=(0.0, 0.0, 10.0, 12.0), obstacles=obs_y, threats=threats_y)
    path_y = [(5.0, 1.5), (5.0, 4.0), (5.0, 6.5), (5.0, 9.5)]

    return world_x, path_x, world_y, path_y, combat, player


def scenario_13_nonpreemptive_blocking_counterexample() -> Tuple[List[Any], Any, PlayerModel, CombatModel]:
    """Scenario 13: Non-Preemptive Blocking DBF Counterexample.
    
    Demonstrates that the classical demand bound condition dbf(Δ) <= Δ is insufficient
    for non-preemptive single-machine scheduling 1 | r_j, s_ij | L_max.
    
    Jobs:
      J1: r1 = 0.0s, D1 = 3.0s, p1 = 2.0s
      J2: r2 = 1.0s, D2 = 2.0s, p2 = 1.0s
    
    Interval demands:
      [0, 3]: demand = 3.0 <= 3.0 (PASS)
      [1, 2]: demand = 1.0 <= 1.0 (PASS)
      [0, 1]: demand = 0.0 <= 1.0 (PASS)
      [2, 3]: demand = 0.0 <= 1.0 (PASS)
      -> dbf(Δ) <= Δ passes for all Δ >= 0!
      
    Yet no non-preemptive schedule is feasible:
      - If J1 starts at 0 -> finishes at 2, J2 starts at 2 -> finishes at 3 > D2=2 (missed by +1.0s).
      - If scheduler idles until 1 to run J2 -> finishes at 2, J1 starts at 2 -> finishes at 4 > D1=3 (missed by +1.0s).
      -> L* = +1.0s > 0 (UNSOLVABLE).
    """
    from .contracts import AngularSectorDiscretization, ThreatJob
    disc = AngularSectorDiscretization(num_sectors=4)
    player = PlayerModel(acquisition_latency_s=0.0, aim_velocity_deg_s=1e9, inspect_duration_s=0.0)
    combat = CombatModel()

    jobs = [
        ThreatJob(id="J1", release_s=0.0, deadline_s=3.0, service_s=2.0, angle_deg=0.0, sector=disc.get_sector(0.0)),
        ThreatJob(id="J2", release_s=1.0, deadline_s=2.0, service_s=1.0, angle_deg=0.0, sector=disc.get_sector(0.0)),
    ]
    return jobs, disc, player, combat


def scenario_14_infsup_nondistributivity_algebra() -> Dict[str, Any]:
    """Scenario 14: Inf-Sup Associativity Falsification on Arbitrary Discrete Curves.
    
    Proves that max-plus time convolution does not distribute over min-plus state choice:
      (f * min(g, h))(2) = 1 != min(f * g, f * h)(2) = 2.
    """
    from .contracts import demonstrate_infsup_nondistributivity
    return demonstrate_infsup_nondistributivity()

