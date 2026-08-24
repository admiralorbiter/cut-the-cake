"""Path sampling, reveal parameter estimation, and trajectory evaluation [G + C + P]."""

from __future__ import annotations
import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import numpy as np
from shapely.geometry import LineString, Point

from .model import World, ThreatRegion, ThreatView, CombatModel, PlayerModel
from .visibility import compute_visible_threats
from .conflicts import build_threat_incompatibility_graph
from .service_solver import ThreatEvent, solve_service_schedule, ServiceScheduleResult
from .geometry import heading_to_deg, distance


@dataclass
class TrajectorySample:
    """Evaluated spatial state at distance s along path [G + C + P]."""
    s: float
    pos: Tuple[float, float]
    time_s: float
    visible_threats: List[ThreatView]
    k_ici: int
    max_los_m: float


@dataclass
class PathClearabilityResult:
    """Full clearability diagnostic of a movement path [G + C + P]."""
    path_length_m: float
    duration_s: float
    samples: List[TrajectorySample]
    peak_k_ici: int
    reveals: Dict[str, float]  # threat_id -> reveal_s
    schedule_result: ServiceScheduleResult
    is_solvable: bool
    optimal_frontier_width: int  # W*(γ)


def evaluate_path_clearability(
    path_coords: List[Tuple[float, float]],
    world: World,
    combat_model: CombatModel,
    player_model: PlayerModel,
    step_size_m: float = 0.10,
    initial_aim_deg: Optional[float] = None
) -> PathClearabilityResult:
    """Evaluate path clearability, K_ICI progression, and optimal service schedule [G + C + P]."""
    line = LineString(path_coords)
    total_length = line.length
    if total_length == 0:
        total_length = 1e-4

    n_steps = max(2, int(total_length / step_size_m) + 1)
    s_values = np.linspace(0.0, total_length, n_steps)

    samples: List[TrajectorySample] = []
    reveals: Dict[str, float] = {}
    first_views: Dict[str, ThreatView] = {}

    if initial_aim_deg is None and len(path_coords) >= 2:
        initial_aim_deg = heading_to_deg(path_coords[0], path_coords[1])
    elif initial_aim_deg is None:
        initial_aim_deg = 0.0

    peak_k_ici = 0

    for s in s_values:
        pt = line.interpolate(s)
        pos = (pt.x, pt.y)
        t_s = s / combat_model.player_speed_mps

        vis_threats = compute_visible_threats(pos, world, vis_threshold=combat_model.vis_threshold)
        G, k_ici = build_threat_incompatibility_graph(vis_threats, combat_model, player_model)
        peak_k_ici = max(peak_k_ici, k_ici)

        max_los = max((tv.min_distance_m for tv in vis_threats), default=0.0)

        samples.append(TrajectorySample(
            s=float(s),
            pos=pos,
            time_s=t_s,
            visible_threats=vis_threats,
            k_ici=k_ici,
            max_los_m=max_los
        ))

        # Check for first reveals
        for tv in vis_threats:
            if tv.threat_id not in reveals:
                reveals[tv.threat_id] = float(s)
                first_views[tv.threat_id] = tv

    # Build threat events for the service solver
    threat_events: List[ThreatEvent] = []
    for tid, s_reveal in reveals.items():
        tv = first_views[tid]
        t_reveal = s_reveal / combat_model.player_speed_mps
        deadline_dur = combat_model.damage_deadline(tv.min_distance_m)
        t_deadline = t_reveal + deadline_dur

        threat_events.append(ThreatEvent(
            threat_id=tid,
            reveal_time_s=t_reveal,
            deadline_time_s=t_deadline,
            centroid_angle_deg=tv.centroid_angle_deg,
            elevation_deg=tv.elevation_deg
        ))

    sched_res = solve_service_schedule(
        threat_events,
        combat_model,
        player_model,
        initial_aim_deg=initial_aim_deg
    )

    return PathClearabilityResult(
        path_length_m=total_length,
        duration_s=total_length / combat_model.player_speed_mps,
        samples=samples,
        peak_k_ici=peak_k_ici,
        reveals=reveals,
        schedule_result=sched_res,
        is_solvable=sched_res.is_solvable,
        optimal_frontier_width=sched_res.max_frontier_width
    )
