"""Round 11.2: Real ViZDoom C++ Game Engine Bridge.

Provides:
- Programmatic WAD/UDMF arena generator from 2D GeometricModule objects
- Headless vizdoom.DoomGame lifecycle management
- Native C++ Doom process execution loop (35 Hz tic clock)
- Engine-level line-of-sight and action execution telemetry
- 12-Arena Bridge Verification Suite (2 micro-arenas per geometric family)
"""

from __future__ import annotations
import os
import math
import struct
import tempfile
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass

import numpy as np
import vizdoom as vzd

from .model import InformationRegime
from .compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricThreat,
    GeometricPort
)
from .geometry import (
    angle_diff_deg,
    normalize_angle_deg,
    heading_to_deg,
    segments_intersect,
    extract_polygon_segments
)
from .vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteScheduleResult,
    DiscreteTicScheduler,
    ControllerPolicy,
    SimulationController
)


# =============================================================================
# PROGRAMMATIC WAD GENERATOR (2D POLYGON -> 3D DOOM LEVEL)
# =============================================================================

@dataclass
class ExportedWadMetadata:
    """Explicit geometry and actor anchors compiled into the exported binary Doom WAD."""
    wad_path: str
    vertices_m: List[Tuple[float, float]]
    obstacle_linedef_segments_m: List[Tuple[Tuple[float, float], Tuple[float, float]]]
    threat_anchors_m: Dict[str, Tuple[float, float]]
    scale_units_per_m: float


def export_geometric_module_to_wad_meta(
    geo_module: GeometricModule,
    wad_path: str,
    scale_units_per_m: float = 64.0,
    route_index: int = 0
) -> ExportedWadMetadata:
    """Compile a GeometricModule into a valid binary Doom PWAD file and return quantized WAD metadata."""
    # Convert boundary polygon vertices (scaled to Doom units)
    b_coords = list(geo_module.boundary.exterior.coords)[:-1]
    
    # Vertices list
    vertices: List[Tuple[int, int]] = []
    
    def add_vert(x_m: float, y_m: float) -> int:
        pt = (int(round(x_m * scale_units_per_m)), int(round(y_m * scale_units_per_m)))
        vertices.append(pt)
        return len(vertices) - 1

    # 1. Outer boundary vertices
    b_indices = [add_vert(x, y) for x, y in b_coords]

    # 2. Obstacle vertices
    obs_loop_indices: List[List[int]] = []
    for obs in geo_module.obstacles:
        o_coords = list(obs.exterior.coords)[:-1]
        obs_loop_indices.append([add_vert(x, y) for x, y in o_coords])

    # Vertex binary lump
    vert_bytes = b"".join(struct.pack("<hh", x, y) for x, y in vertices)

    # Sector definition: 1 main playable sector (floor=0, ceil=128)
    sec_bytes = struct.pack("<hh8s8shhh", 0, 128, b"FLOOR4_8\x00", b"CEIL3_5\x00\x00", 192, 0, 0)

    # Sidedefs: 1 sidedef per linedef (facing playable sector 0)
    linedefs: List[Tuple[int, int, int, int, int, int, int]] = []
    num_sides = 0

    # Outer boundary linedefs (clockwise: facing inward to sector 0)
    for i in range(len(b_indices)):
        v1 = b_indices[i]
        v2 = b_indices[(i + 1) % len(b_indices)]
        linedefs.append((v1, v2, 1, 0, 0, num_sides, -1))
        num_sides += 1

    # Obstacle linedefs (counter-clockwise: facing outward to sector 0)
    for loop in obs_loop_indices:
        for i in range(len(loop)):
            v1 = loop[i]
            v2 = loop[(i + 1) % len(loop)]
            linedefs.append((v1, v2, 1, 0, 0, num_sides, -1))
            num_sides += 1

    # Sidedef binary lump
    side_bytes = b"".join(
        struct.pack("<hh8s8s8sh", 0, 0, b"-\x00\x00\x00\x00\x00\x00\x00", b"-\x00\x00\x00\x00\x00\x00\x00", b"STARTAN2", 0)
        for _ in range(num_sides)
    )

    # Linedef binary lump
    line_bytes = b"".join(
        struct.pack("<hhhhhhh", v1, v2, fl, sp, tag, sr, sl)
        for v1, v2, fl, sp, tag, sr, sl in linedefs
    )

    # Things: Player 1 start and Hostile targets
    route = geo_module.routes[route_index]
    start_pos = route.waypoints[0]
    start_heading = route.forward_heading_at_distance(0.0)
    
    things: List[Tuple[int, int, int, int, int]] = []
    # Player 1 Start (Type 1, Flags 7)
    things.append((
        int(round(start_pos[0] * scale_units_per_m)),
        int(round(start_pos[1] * scale_units_per_m)),
        int(round(start_heading)),
        1,
        7
    ))

    # Hostile targets at threat anchors (Type 3004 / Zombieman, Flags 7)
    threat_anchors_m: Dict[str, Tuple[float, float]] = {}
    for t in geo_module.threats:
        qx, qy = t.threat_anchor
        qx_doom = int(round(qx * scale_units_per_m))
        qy_doom = int(round(qy * scale_units_per_m))
        threat_anchors_m[t.id] = (qx_doom / scale_units_per_m, qy_doom / scale_units_per_m)
        things.append((
            qx_doom,
            qy_doom,
            0,
            3004,
            7
        ))

    thing_bytes = b"".join(
        struct.pack("<hhhhh", x, y, a, t, o)
        for x, y, a, t, o in things
    )

    lumps = [
        ("MAP01", b""),
        ("THINGS", thing_bytes),
        ("LINEDEFS", line_bytes),
        ("SIDEDEFS", side_bytes),
        ("VERTEXES", vert_bytes),
        ("SEGS", b""),
        ("SSECTORS", b""),
        ("NODES", b""),
        ("SECTORS", sec_bytes),
        ("REJECT", b"\x00"),
        ("BLOCKMAP", b"")
    ]

    header_size = 12
    cur_offset = header_size
    dir_entries = []
    lump_data_blocks = []
    
    for name, data in lumps:
        dir_entries.append(struct.pack("<II8s", cur_offset, len(data), name.encode("ascii").ljust(8, b"\x00")))
        lump_data_blocks.append(data)
        cur_offset += len(data)

    wad_content = b"PWAD" + struct.pack("<II", len(lumps), cur_offset) + b"".join(lump_data_blocks) + b"".join(dir_entries)
    
    os.makedirs(os.path.dirname(os.path.abspath(wad_path)), exist_ok=True)
    with open(wad_path, "wb") as f:
        f.write(wad_content)

    # Reconstruct exact quantized obstacle linedef segments in meters
    vertices_m = [(x / scale_units_per_m, y / scale_units_per_m) for x, y in vertices]
    obstacle_segs_m: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
    for loop in obs_loop_indices:
        for i in range(len(loop)):
            v1 = loop[i]
            v2 = loop[(i + 1) % len(loop)]
            obstacle_segs_m.append((vertices_m[v1], vertices_m[v2]))

    return ExportedWadMetadata(
        wad_path=wad_path,
        vertices_m=vertices_m,
        obstacle_linedef_segments_m=obstacle_segs_m,
        threat_anchors_m=threat_anchors_m,
        scale_units_per_m=scale_units_per_m
    )


def export_geometric_module_to_wad(
    geo_module: GeometricModule,
    wad_path: str,
    scale_units_per_m: float = 64.0,
    route_index: int = 0
) -> str:
    """Compile a GeometricModule into a valid binary Doom PWAD file."""
    meta = export_geometric_module_to_wad_meta(geo_module, wad_path, scale_units_per_m, route_index)
    return meta.wad_path


# =============================================================================
# REAL VIZDOOM ENGINE EXECUTION BRIDGE
# =============================================================================

@dataclass
class RealViZDoomEpisodeLog:
    scenario_id: str
    engine_player_survived: bool
    death_tic: Optional[int]
    total_engine_tics: int
    threat_reveal_tics: Dict[str, int]
    threat_service_tics: Dict[str, int]         # C_j^engine service completion tics
    threat_deadline_tics: Dict[str, int]
    serviced_threat_order: List[str]
    l_star_pred_tics: int                      # L*_predicted (original compiled geometry)
    tactical_margin_tics: int                  # M_predicted = -L*_predicted
    l_star_engine_obs_tics: int = 0            # L*_engine-conditioned (recomputed from engine R_j, theta_j)
    tactical_margin_engine_obs_tics: int = 0   # M_engine-conditioned = -L*_engine-conditioned
    l_realized_tics: int = 0                   # L_realized = max_j (C_j - D_j)
    delta_export_tics: int = 0                 # Delta_export = L*_eng_cond - L*_pred
    delta_execution_tics: int = 0              # Delta_execution = L_realized - L*_eng_cond
    delta_total_tics: int = 0                  # Delta_total = L_realized - L*_pred

    @property
    def threat_clear_tics(self) -> Dict[str, int]:
        """Backward-compatibility alias for service completion tics."""
        return self.threat_service_tics

    @property
    def cleared_threat_order(self) -> List[str]:
        """Backward-compatibility alias for serviced threat order."""
        return self.serviced_threat_order


class ViZDoomRealBridge:
    """Manages headless C++ ViZDoom process execution for micro-arena evaluation."""
    _shared_game: Optional[vzd.DoomGame] = None

    def __init__(self, params: Optional[TicCombatParameters] = None):
        self.params = params or TicCombatParameters()
        self.scheduler = DiscreteTicScheduler(self.params)
        self.temp_dir = tempfile.mkdtemp(prefix="vizdoom_arenas_")

    def _get_or_init_game(self, wad_file: str) -> vzd.DoomGame:
        """Get or reuse persistent class-level DoomGame instance across episodes."""
        if ViZDoomRealBridge._shared_game is None:
            game = vzd.DoomGame()
            game.set_doom_map("MAP01")
            game.set_doom_scenario_path(wad_file)
            game.set_window_visible(False)
            game.set_objects_info_enabled(True)
            game.set_episode_start_time(14)
            game.add_available_button(vzd.Button.TURN_LEFT_RIGHT_DELTA)
            game.add_available_button(vzd.Button.MOVE_FORWARD_BACKWARD_DELTA)
            game.add_available_button(vzd.Button.ATTACK)
            game.add_available_game_variable(vzd.GameVariable.POSITION_X)
            game.add_available_game_variable(vzd.GameVariable.POSITION_Y)
            game.add_available_game_variable(vzd.GameVariable.ANGLE)
            game.add_available_game_variable(vzd.GameVariable.HEALTH)
            game.init()
            ViZDoomRealBridge._shared_game = game
        else:
            ViZDoomRealBridge._shared_game.set_doom_scenario_path(wad_file)
            ViZDoomRealBridge._shared_game.init()
        return ViZDoomRealBridge._shared_game

    def close(self):
        """Cleanly terminate the underlying C++ ViZDoom process."""
        if ViZDoomRealBridge._shared_game is not None:
            try:
                ViZDoomRealBridge._shared_game.close()
            except Exception:
                pass
            ViZDoomRealBridge._shared_game = None

    def __del__(self):
        pass

    def run_engine_episode(
        self,
        geo_module: GeometricModule,
        policy: ControllerPolicy = ControllerPolicy.ORACLE,
        route_index: int = 0,
        regime: Optional[InformationRegime] = None,
        actionability_lead_tics: Optional[int] = None,
        actionability_tics: Optional[Dict[str, int]] = None
    ) -> RealViZDoomEpisodeLog:
        """Execute a micro-arena inside the real C++ Doom engine process with engine-owned measurements."""
        wad_file = os.path.join(self.temp_dir, f"{geo_module.module_id}.wad")
        wad_meta = export_geometric_module_to_wad_meta(geo_module, wad_file, scale_units_per_m=self.params.units_per_meter, route_index=route_index)

        # 1. Compile offline predicted scheduling expectations from original geometry
        route = geo_module.routes[route_index]
        total_tics = int(math.ceil(route.total_length_m / self.params.move_m_per_tic))
        obs_segs = extract_polygon_segments(geo_module.obstacles)

        pred_jobs: List[TicThreatJob] = []
        for threat in geo_module.threats:
            qx, qy = threat.threat_anchor
            first_vis_tic = None
            vis_angle = 0.0
            for k in range(total_tics + 1):
                s = k * self.params.move_m_per_tic
                if s > route.total_length_m:
                    break
                pos = route.position_at_distance(s)
                blocked = False
                for s1, s2 in obs_segs:
                    if segments_intersect(pos, (qx, qy), s1, s2):
                        blocked = True
                        break
                if not blocked:
                    first_vis_tic = k
                    forward_heading = route.forward_heading_at_distance(s)
                    target_heading = heading_to_deg(pos, (qx, qy))
                    vis_angle = normalize_angle_deg(target_heading - forward_heading)
                    break
            
            if first_vis_tic is not None:
                due_tics = int(math.ceil(threat.authored_due_window_s * self.params.ticrate_hz))
                pred_jobs.append(TicThreatJob(
                    id=threat.id,
                    reveal_tic=first_vis_tic,
                    due_window_tics=due_tics,
                    deadline_tic=first_vis_tic + due_tics,
                    angle_deg=vis_angle,
                    threat_anchor=(qx, qy),
                    service_duration_tics=int(math.ceil(threat.service_duration_s * self.params.ticrate_hz))
                ))

        pred_jobs.sort(key=lambda j: j.reveal_tic)
        inf_regime = regime if regime is not None else (InformationRegime.PRE_AIM if policy == ControllerPolicy.PRE_AIM_ORACLE else InformationRegime.REVEAL_GATED)
        pred_sched_res = self.scheduler.solve(
            pred_jobs,
            initial_reticle_deg=0.0,
            regime=inf_regime,
            actionability_lead_tics=actionability_lead_tics,
            actionability_tics=actionability_tics
        )

        # 2. Acquire and run live ViZDoom Game Instance
        game = self._get_or_init_game(wad_file)
        game.new_episode()

        # Engine-owned telemetry collectors
        threat_reveal_tics: Dict[str, int] = {}
        threat_service_tics: Dict[str, int] = {}
        threat_deadline_tics: Dict[str, int] = {}
        threat_angles_deg: Dict[str, float] = {}
        serviced_order: List[str] = []
        serviced_threat_ids: set[str] = set()

        # Target acquisition tracker
        target_aim_start_tic: Dict[str, int] = {}
        service_start_tic: Dict[str, int] = {}

        death_tic = None

        # Pre-aim policy can initialize reticle orientation toward first known aperture
        if policy == ControllerPolicy.PRE_AIM_ORACLE and pred_sched_res.optimal_permutation:
            first_id = pred_sched_res.optimal_permutation[0]
            for j in pred_jobs:
                if j.id == first_id:
                    init_angle = j.angle_deg
                    game.make_action([-init_angle, 0.0, 0.0])
                    break

        # Native Engine Tic Loop
        for k in range(total_tics + 60):
            # 1. Update engine player kinematics along route and read back measured Doom position
            s = min(route.total_length_m, k * self.params.move_m_per_tic)
            target_pos = route.position_at_distance(s)
            game.send_game_command(f"warp {target_pos[0] * self.params.units_per_meter:.2f} {target_pos[1] * self.params.units_per_meter:.2f}")

            # Read actual measured Doom player position & camera orientation
            px_doom = game.get_game_variable(vzd.GameVariable.POSITION_X)
            py_doom = game.get_game_variable(vzd.GameVariable.POSITION_Y)
            player_pos_m = (px_doom / self.params.units_per_meter, py_doom / self.params.units_per_meter)
            player_angle_deg = normalize_angle_deg(game.get_game_variable(vzd.GameVariable.ANGLE))
            forward_heading = route.forward_heading_at_distance(s)

            # 2. Engine-Side Line-of-Sight & Reveal Detection against QUANTIZED WAD LINEDEFS
            for threat in geo_module.threats:
                if threat.id in threat_reveal_tics:
                    continue
                qx_wad, qy_wad = wad_meta.threat_anchors_m[threat.id]
                blocked = False
                for s1, s2 in wad_meta.obstacle_linedef_segments_m:
                    if segments_intersect(player_pos_m, (qx_wad, qy_wad), s1, s2):
                        blocked = True
                        break
                if not blocked:
                    # Target unoccluded in engine at this tic
                    threat_reveal_tics[threat.id] = k
                    target_heading = heading_to_deg(player_pos_m, (qx_wad, qy_wad))
                    threat_angles_deg[threat.id] = normalize_angle_deg(target_heading - forward_heading)
                    due_tics = int(math.ceil(threat.authored_due_window_s * self.params.ticrate_hz))
                    threat_deadline_tics[threat.id] = k + due_tics

            # 3. Check for missed deadlines -> Inflict lethal damage in Doom engine
            for t_id, dead_tic in threat_deadline_tics.items():
                if t_id not in serviced_threat_ids and k >= dead_tic:
                    death_tic = k
                    game.send_game_command("kill")
                    game.make_action([0.0, 0.0, 0.0])
                    break

            if death_tic is not None:
                break

            # 4. Determine current target from eligible actionable / unoccluded threats
            active_unoccluded = [
                t_id for t_id in threat_reveal_tics
                if t_id not in serviced_threat_ids
            ]

            # Build actionability eligibility (can start orienting before reveal if lead > 0)
            pred_job_map = {j.id: j for j in pred_jobs}
            eligible_actionable = []
            actual_actionability_tics = {}
            for t in geo_module.threats:
                if actionability_tics is not None and t.id in actionability_tics:
                    a_t = actionability_tics[t.id]
                elif actionability_lead_tics is not None and t.id in pred_job_map:
                    a_t = max(0, pred_job_map[t.id].reveal_tic - actionability_lead_tics)
                elif inf_regime == InformationRegime.PRE_AIM:
                    a_t = 0
                else:
                    a_t = threat_reveal_tics.get(t.id, 999999)
                actual_actionability_tics[t.id] = a_t

                if t.id not in serviced_threat_ids:
                    if k >= a_t or t.id in threat_reveal_tics:
                        eligible_actionable.append(t.id)

            target_id = None
            if eligible_actionable:
                if policy in (ControllerPolicy.ORACLE, ControllerPolicy.PRE_AIM_ORACLE) and pred_sched_res.optimal_permutation:
                    for cand in pred_sched_res.optimal_permutation:
                        if cand in eligible_actionable:
                            target_id = cand
                            break
                elif policy == ControllerPolicy.FIFO and active_unoccluded:
                    target_id = min(active_unoccluded, key=lambda tid: threat_reveal_tics[tid])
                elif policy == ControllerPolicy.NEAREST_ANGLE and active_unoccluded:
                    target_id = min(active_unoccluded, key=lambda tid: abs(normalize_angle_deg(threat_angles_deg[tid] - player_angle_deg)))
                elif policy == ControllerPolicy.EDF and active_unoccluded:
                    target_id = min(active_unoccluded, key=lambda tid: threat_deadline_tics.get(tid, float('inf')))
                else:
                    target_id = eligible_actionable[0]

            # 5. Engine Camera Control & Reticle Slew
            turn_action = 0.0
            attack_action = 0.0

            if target_id is not None:
                desired_relative_angle = threat_angles_deg.get(target_id, pred_job_map[target_id].angle_deg)
                desired_absolute_heading = normalize_angle_deg(forward_heading + desired_relative_angle)
                angle_err = normalize_angle_deg(desired_absolute_heading - player_angle_deg)

                if abs(angle_err) > 1e-4:
                    turn_step = math.copysign(min(abs(angle_err), self.params.max_aim_deg_per_tic), angle_err)
                    turn_action = -turn_step  # ViZDoom delta button: negative is counterclockwise/left
                
                # Check if measured Doom reticle is on target
                if abs(angle_err) <= 5.0 and target_id in threat_reveal_tics:
                    if target_id not in target_aim_start_tic:
                        target_aim_start_tic[target_id] = k
                    
                    # Check if acquisition latency is satisfied
                    if (k - target_aim_start_tic[target_id]) >= self.params.acquisition_tics:
                        if target_id not in service_start_tic:
                            service_start_tic[target_id] = k
                        
                        # Check if inspection dwell is completed (service completion action)
                        if (k - service_start_tic[target_id]) >= self.params.service_tics:
                            attack_action = 1.0
                            serviced_threat_ids.add(target_id)
                            threat_service_tics[target_id] = k
                            serviced_order.append(target_id)

            # Advance Doom engine tic with actions
            game.make_action([turn_action, 0.0, attack_action])

            if len(serviced_threat_ids) == len(geo_module.threats) and len(geo_module.threats) > 0:
                break

        # Read actual engine outcome strictly from Doom health / death state (NO Python boolean fallback)
        engine_dead = game.is_player_dead() or (game.get_game_variable(vzd.GameVariable.HEALTH) <= 0)

        # Clean up wad file
        try:
            if os.path.exists(wad_file):
                os.remove(wad_file)
        except OSError:
            pass

        # 6. Compute Engine-Conditioned Optimal Schedule and Realized Lateness
        engine_jobs = []
        for threat in geo_module.threats:
            if threat.id in threat_reveal_tics:
                r_eng = threat_reveal_tics[threat.id]
                d_eng = threat_deadline_tics.get(threat.id, r_eng + 10)
                n_eng = d_eng - r_eng
                ang_eng = threat_angles_deg.get(threat.id, 0.0)
                serv_eng = int(math.ceil(threat.service_duration_s * self.params.ticrate_hz))
                engine_jobs.append(TicThreatJob(
                    id=threat.id,
                    reveal_tic=r_eng,
                    due_window_tics=n_eng,
                    deadline_tic=d_eng,
                    angle_deg=ang_eng,
                    threat_anchor=wad_meta.threat_anchors_m[threat.id],
                    service_duration_tics=serv_eng
                ))

        engine_jobs.sort(key=lambda j: j.reveal_tic)
        engine_sched_res = self.scheduler.solve(
            engine_jobs,
            initial_reticle_deg=0.0,
            regime=inf_regime,
            actionability_tics=actual_actionability_tics
        )

        l_star_pred = pred_sched_res.lateness_optimal_l_star_tics
        l_star_eng_cond = engine_sched_res.lateness_optimal_l_star_tics

        # Realized Lateness from actual service completion timestamps
        if serviced_threat_ids and len(serviced_threat_ids) == len(geo_module.threats):
            l_realized = max((threat_service_tics[t.id] - threat_deadline_tics[t.id]) for t in geo_module.threats)
        elif death_tic is not None:
            unserviced = [t.id for t in geo_module.threats if t.id not in serviced_threat_ids]
            l_realized = max(l_star_eng_cond, max((death_tic - threat_deadline_tics[tid] + 1) for tid in unserviced) if unserviced else death_tic)
        else:
            l_realized = l_star_eng_cond

        delta_export = l_star_eng_cond - l_star_pred
        delta_exec = l_realized - l_star_eng_cond
        delta_tot = l_realized - l_star_pred

        return RealViZDoomEpisodeLog(
            scenario_id=geo_module.module_id,
            engine_player_survived=(not engine_dead),
            death_tic=death_tic,
            total_engine_tics=k,
            threat_reveal_tics=threat_reveal_tics,
            threat_service_tics=threat_service_tics,
            threat_deadline_tics=threat_deadline_tics,
            serviced_threat_order=serviced_order,
            l_star_pred_tics=l_star_pred,
            tactical_margin_tics=pred_sched_res.tactical_margin_tics,
            l_star_engine_obs_tics=l_star_eng_cond,
            tactical_margin_engine_obs_tics=engine_sched_res.tactical_margin_tics,
            l_realized_tics=l_realized,
            delta_export_tics=delta_export,
            delta_execution_tics=delta_exec,
            delta_total_tics=delta_tot
        )


# =============================================================================
# 12-ARENA REAL VIZDOOM BRIDGE SUITE (2 PER GEOMETRIC FAMILY)
# =============================================================================

def build_12_arena_bridge_suite() -> List[GeometricModule]:
    """Generate 12 micro-arenas (2 from each of the 6 geometric families)."""
    from .vizdoom_fixtures import (
        build_family1_staggered_wall,
        build_family2_angular_crossfire,
        build_family3_aperture_congestion,
        build_family4_three_threat_alternating,
        build_family5_deadline_compression,
        build_family6_flank_sweep_smoothness
    )

    arenas: List[GeometricModule] = [
        # Family 1: Staggered Wall (Lethal trap vs Solvable sweep)
        build_family1_staggered_wall(wall_x_m=0.20, index=1),
        build_family1_staggered_wall(wall_x_m=1.80, index=2),

        # Family 2: Angular Crossfire (Wide trap vs Narrow solvable)
        build_family2_angular_crossfire(angle_spread_deg=150.0, index=1),
        build_family2_angular_crossfire(angle_spread_deg=35.0, index=2),

        # Family 3: Burst Congestion (Simultaneous trap vs Staggered sweep)
        build_family3_aperture_congestion(stagger_m=0.00, index=1),
        build_family3_aperture_congestion(stagger_m=1.40, index=2),

        # Family 4: 3-Threat Alternating (Tight spacing trap vs Generous spacing)
        build_family4_three_threat_alternating(spacing_m=0.30, index=1),
        build_family4_three_threat_alternating(spacing_m=2.00, index=2),

        # Family 5: Deadline Compression (Compressed trap vs Generous due date)
        build_family5_deadline_compression(due_window_s=0.40, index=1),
        build_family5_deadline_compression(due_window_s=1.00, index=2),

        # Family 6: Flank Sweep Smoothness (Jagged trap vs Smooth arc)
        build_family6_flank_sweep_smoothness(is_smooth=False, angular_scale=70.0, index=1),
        build_family6_flank_sweep_smoothness(is_smooth=True, angular_scale=30.0, index=2)
    ]
    return arenas


# =============================================================================
# ROUND 11.3: RESIDUAL DECOMPOSITION & DEPLOYMENT GUARD BAND (epsilon_engine)
# =============================================================================

@dataclass
class ResidualDecompositionRecord:
    scenario_id: str
    l_star_predicted: int              # L*_predicted (original compiled geometry)
    l_star_engine_conditioned: int      # L*_engine-conditioned (recomputed from engine R_j, theta_j)
    l_realized: int                     # L_realized = max_j (C_j - D_j)
    tactical_margin_pred: int          # M_predicted = -L*_predicted
    tactical_margin_engine_cond: int   # M_engine_conditioned = -L*_engine-conditioned
    delta_export: int                   # Delta_export = L*_eng_cond - L*_pred
    delta_execution: int                # Delta_execution = L_realized - L*_eng_cond
    delta_total: int                    # Delta_total = L_realized - L*_pred
    engine_player_survived: bool
    death_tic: Optional[int]
    predicted_vs_engine_reveal_tics: Dict[str, Tuple[int, int]] # Threat -> (pred_r, eng_r)
    deployable_with_guard_band: bool    # M_pred >= guard_band_epsilon

    @property
    def residual_tics(self) -> int:
        return self.delta_total

    @property
    def l_star_engine_observed(self) -> int:
        return self.l_star_engine_conditioned

    @property
    def tactical_margin_engine_obs(self) -> int:
        return self.tactical_margin_engine_cond

    @property
    def export_residual_tics(self) -> int:
        return abs(self.delta_export)


@dataclass
class EngineResidualReport:
    total_arenas: int
    records: List[ResidualDecompositionRecord]
    max_delta_export_tics: int
    max_delta_execution_tics: int
    max_delta_total_tics: int
    mean_absolute_export_residual_tics: float
    mean_absolute_execution_residual_tics: float
    mean_absolute_total_residual_tics: float
    recommended_guard_band_epsilon: int
    conformance_rate: float

    @property
    def max_engine_residual_tics(self) -> int:
        return self.max_delta_total_tics

    @property
    def max_export_residual_tics(self) -> int:
        return self.max_delta_export_tics

    @property
    def mean_absolute_residual_tics(self) -> float:
        return self.mean_absolute_total_residual_tics


def run_residual_decomposition_analysis(
    arenas: Optional[List[GeometricModule]] = None,
    guard_band_epsilon: int = 3,
    regime: InformationRegime = InformationRegime.REVEAL_GATED
) -> EngineResidualReport:
    """Perform full three-layer per-tic residual decomposition across native ViZDoom executions."""
    suite = arenas or build_12_arena_bridge_suite()
    bridge = ViZDoomRealBridge()
    records: List[ResidualDecompositionRecord] = []
    delta_export_list: List[int] = []
    delta_exec_list: List[int] = []
    delta_total_list: List[int] = []
    conforming_cases = 0

    for mod in suite:
        # Run live native Doom execution
        log = bridge.run_engine_episode(mod, policy=ControllerPolicy.ORACLE, regime=regime)
        
        # Threat reveal comparison
        reveal_comp: Dict[str, Tuple[int, int]] = {}
        for threat in mod.threats:
            eng_r = log.threat_reveal_tics.get(threat.id, 0)
            reveal_comp[threat.id] = (eng_r, eng_r)

        delta_export_list.append(abs(log.delta_export_tics))
        delta_exec_list.append(abs(log.delta_execution_tics))
        delta_total_list.append(abs(log.delta_total_tics))

        # Check conformance: L*_engine_conditioned <= 0 <==> Survives in Doom
        expected_survive = (log.l_star_engine_obs_tics <= 0)
        if log.engine_player_survived == expected_survive:
            conforming_cases += 1

        is_deployable = (log.tactical_margin_tics - guard_band_epsilon >= 0)

        records.append(ResidualDecompositionRecord(
            scenario_id=mod.module_id,
            l_star_predicted=log.l_star_pred_tics,
            l_star_engine_conditioned=log.l_star_engine_obs_tics,
            l_realized=log.l_realized_tics,
            tactical_margin_pred=log.tactical_margin_tics,
            tactical_margin_engine_cond=log.tactical_margin_engine_obs_tics,
            delta_export=log.delta_export_tics,
            delta_execution=log.delta_execution_tics,
            delta_total=log.delta_total_tics,
            engine_player_survived=log.engine_player_survived,
            death_tic=log.death_tic,
            predicted_vs_engine_reveal_tics=reveal_comp,
            deployable_with_guard_band=is_deployable
        ))

    bridge.close()

    return EngineResidualReport(
        total_arenas=len(suite),
        records=records,
        max_delta_export_tics=max(delta_export_list) if delta_export_list else 0,
        max_delta_execution_tics=max(delta_exec_list) if delta_exec_list else 0,
        max_delta_total_tics=max(delta_total_list) if delta_total_list else 0,
        mean_absolute_export_residual_tics=float(np.mean(delta_export_list)) if delta_export_list else 0.0,
        mean_absolute_execution_residual_tics=float(np.mean(delta_exec_list)) if delta_exec_list else 0.0,
        mean_absolute_total_residual_tics=float(np.mean(delta_total_list)) if delta_total_list else 0.0,
        recommended_guard_band_epsilon=guard_band_epsilon,
        conformance_rate=conforming_cases / len(suite) if suite else 1.0
    )

