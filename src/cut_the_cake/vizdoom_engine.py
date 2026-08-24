"""Round 11: External Predictive Validity (ViZDoom Simulation Ladder).

Provides:
- Discrete 35 Hz Tic Clock Model (Delta t = 1/35 s = 28.5714 ms)
- Integer-tic scheduling solver (L*_tic) with sequence-dependent reticle setup
- 5 Independent Simulation Controllers (Optimal Oracle, FIFO, Nearest Angle, EDF, Left-to-Right)
- Deterministic 2D-in-3D ViZDoom micro-arena execution referee
- Noise simulation harness for empirical survival estimation and calibration
- Classical baseline extractors (K_static, sigma_min, B_work)
"""

from __future__ import annotations
import math
import itertools
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
import numpy as np
import scipy.stats
from sklearn.metrics import roc_auc_score, brier_score_loss
from shapely.geometry import Point, LineString, Polygon

from .model import PlayerModel, CombatModel, InformationRegime
from .geometry import (
    normalize_angle_deg,
    angle_diff_deg,
    spherical_aim_distance_deg,
    derived_aim_elevation_deg,
    ray_intersects_prism_25d,
    heading_to_deg,
    distance,
    segments_intersect,
    extract_polygon_segments
)
from .compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricObstacle,
    GeometricThreat,
    GeometricPort,
    GeometryToContractCompiler
)


@dataclass(frozen=True)
class TicCombatParameters:
    """Discrete simulation parameters matched to ViZDoom's 35 Hz logic clock."""
    ticrate_hz: int = 35
    units_per_meter: float = 64.0
    v_move_mps: float = 4.5
    aim_velocity_deg_s: float = 360.0
    acquisition_latency_s: float = 0.15
    inspect_duration_s: float = 0.10
    eye_height_m: float = 1.65

    @property
    def tic_duration_s(self) -> float:
        return 1.0 / self.ticrate_hz

    @property
    def move_units_per_tic(self) -> float:
        return (self.v_move_mps * self.units_per_meter) / self.ticrate_hz

    @property
    def move_m_per_tic(self) -> float:
        return self.v_move_mps / self.ticrate_hz

    @property
    def max_aim_deg_per_tic(self) -> float:
        return self.aim_velocity_deg_s / self.ticrate_hz

    @property
    def acquisition_tics(self) -> int:
        return int(math.ceil(self.acquisition_latency_s * self.ticrate_hz))

    @property
    def service_tics(self) -> int:
        return int(math.ceil(self.inspect_duration_s * self.ticrate_hz))


@dataclass
class TicThreatJob:
    """A threat instance compiled onto the discrete 35 Hz integer-tic clock."""
    id: str
    reveal_tic: int                     # R_j (first unoccluded tic)
    due_window_tics: int               # n_j (threat response deadline in tics)
    deadline_tic: int                  # D_j = R_j + n_j
    angle_deg: float                   # Relative aim azimuth bearing at reveal
    threat_anchor: Tuple[float, float] # Firing coordinate (x, y)
    service_duration_tics: int = 4
    elevation_deg: float = 0.0         # Relative aim elevation angle at reveal (M6-A)
    target_z: Optional[float] = None   # Target elevation coordinate in meters (M6-A)



@dataclass
class DiscreteScheduleResult:
    """Optimal sequence-dependent schedule on the integer-tic clock."""
    optimal_permutation: Tuple[str, ...]
    lateness_optimal_l_star_tics: int   # L*_tic (in integer tics)
    lateness_optimal_l_star_s: float    # L*_tic * (1/35) s
    tactical_margin_tics: int           # M_tic = -L*_tic
    completion_tics: Dict[str, int]
    lateness_per_threat: Dict[str, int]
    peak_static_concurrency: int        # W_static (active deadline window concurrency)
    instantaneous_los_clique: int       # K_static (peak simultaneous physical LOS)
    min_slack_tics: int                 # sigma_min = min_j (D_j - R_j - A - P)
    raw_workload_tics: int              # B_work^Ham = sum P_j + min_pi sum setup(pi)
    is_feasible: bool                   # L*_tic <= 0


class DiscreteTicScheduler:
    """Exact integer-tic sequence-dependent scheduling solver."""

    def __init__(self, params: Optional[TicCombatParameters] = None):
        self.params = params or TicCombatParameters()

    @staticmethod
    def _extract_aim_state(val: Any) -> Tuple[float, float]:
        """Extract (azimuth_deg, elevation_deg) aim state from float heading, tuple, or TicThreatJob."""
        if isinstance(val, TicThreatJob):
            return (val.angle_deg, val.elevation_deg)
        elif isinstance(val, (tuple, list)):
            if len(val) >= 2:
                return (float(val[0]), float(val[1]))
            elif len(val) == 1:
                return (float(val[0]), 0.0)
        elif isinstance(val, (int, float)):
            return (float(val), 0.0)
        return (0.0, 0.0)

    def compute_setup_tics(
        self,
        angle_from_deg: Union[float, Tuple[float, float], TicThreatJob],
        angle_to_deg: Union[float, Tuple[float, float], TicThreatJob]
    ) -> int:
        """Compute integer reticle transition setup tics: A + ceil(Delta alpha / Omega)."""
        th1, ph1 = self._extract_aim_state(angle_from_deg)
        th2, ph2 = self._extract_aim_state(angle_to_deg)
        diff = spherical_aim_distance_deg(th1, ph1, th2, ph2)
        aim_tics = int(math.ceil(diff / self.params.max_aim_deg_per_tic))
        return self.params.acquisition_tics + aim_tics

    def compute_hamiltonian_workload_tics(
        self,
        jobs: List[TicThreatJob],
        initial_reticle_deg: Union[float, Tuple[float, float]] = 0.0,
        max_exact_jobs: int = 7,
        allow_slow_solver: bool = False
    ) -> int:
        """Compute exact minimum Hamiltonian tour of setup transitions plus service dwell."""
        if not jobs:
            return 0
        if len(jobs) > max_exact_jobs and not allow_slow_solver:
            raise ValueError(
                f"Exact permutation scheduler job limit exceeded in Hamiltonian workload: "
                f"J={len(jobs)} > {max_exact_jobs}. Pass allow_slow_solver=True to allow factorial enumeration."
            )
        total_service = sum(j.service_duration_tics for j in jobs)
        min_setup_tour = float("inf")

        init_state = self._extract_aim_state(initial_reticle_deg)

        for perm in itertools.permutations(jobs):
            # First transition from initial reticle to perm[0]
            tour = self.compute_setup_tics(init_state, perm[0])
            for i in range(len(perm) - 1):
                tour += self.compute_setup_tics(perm[i], perm[i+1])
            if tour < min_setup_tour:
                min_setup_tour = tour

        return total_service + int(min_setup_tour)

    def solve(
        self,
        jobs: List[TicThreatJob],
        initial_reticle_deg: Union[float, Tuple[float, float]] = 0.0,
        instantaneous_los_clique: int = 1,
        regime: Optional[InformationRegime] = None,
        actionability_lead_tics: Optional[int] = None,
        actionability_tics: Optional[Dict[str, int]] = None,
        max_exact_jobs: int = 7,
        allow_slow_solver: bool = False
    ) -> DiscreteScheduleResult:
        """Solve optimal permutation minimizing maximum lateness L*_tic under specified information regime."""
        if not jobs:
            return DiscreteScheduleResult(
                optimal_permutation=(),
                lateness_optimal_l_star_tics=0,
                lateness_optimal_l_star_s=0.0,
                tactical_margin_tics=0,
                completion_tics={},
                lateness_per_threat={},
                peak_static_concurrency=0,
                instantaneous_los_clique=0,
                min_slack_tics=999,
                raw_workload_tics=0,
                is_feasible=True
            )

        if len(jobs) > max_exact_jobs and not allow_slow_solver:
            raise ValueError(
                f"Exact permutation scheduler job limit exceeded: J={len(jobs)} > {max_exact_jobs}. "
                f"Pass allow_slow_solver=True to allow factorial enumeration."
            )

        job_map = {j.id: j for j in jobs}
        job_ids = [j.id for j in jobs]
        n_jobs = len(jobs)

        # Baseline 1: Window Overlap W_static
        events = []
        for j in jobs:
            events.append((j.reveal_tic, +1))
            events.append((j.deadline_tic, -1))
        events.sort(key=lambda x: (x[0], -x[1]))
        peak_w = 0
        cur_w = 0
        for _, val in events:
            cur_w += val
            peak_w = max(peak_w, cur_w)

        # Baseline 2: Minimum Arrival Slack sigma_min
        min_slack = min(
            j.due_window_tics - self.params.acquisition_tics - j.service_duration_tics
            for j in jobs
        )

        # Baseline 3: Exact Hamiltonian Workload Lower Bound B_work^Ham
        b_work_ham = self.compute_hamiltonian_workload_tics(
            jobs, initial_reticle_deg, max_exact_jobs=max_exact_jobs, allow_slow_solver=allow_slow_solver
        )

        init_th, init_ph = self._extract_aim_state(initial_reticle_deg)

        # Exact sequence-dependent branch / permutation search
        best_l_star = 999999
        best_perm: Tuple[str, ...] = tuple(job_ids)
        best_completion: Dict[str, int] = {}
        best_lateness: Dict[str, int] = {}

        for perm in itertools.permutations(job_ids):
            current_time = 0
            cur_th, cur_ph = init_th, init_ph
            perm_lateness: Dict[str, int] = {}
            perm_completion: Dict[str, int] = {}
            max_l = -999999

            for j_id in perm:
                job = job_map[j_id]
                diff = spherical_aim_distance_deg(cur_th, cur_ph, job.angle_deg, job.elevation_deg)
                rot_tics = int(math.ceil(diff / self.params.max_aim_deg_per_tic)) if diff > 1e-4 else 0
                acq_tics = self.params.acquisition_tics

                # Unified actionable-information recurrence: a_j determines setup start eligibility
                if actionability_tics is not None and j_id in actionability_tics:
                    a_j = actionability_tics[j_id]
                elif actionability_lead_tics is not None:
                    a_j = max(0, job.reveal_tic - actionability_lead_tics)
                elif regime == InformationRegime.PRE_AIM:
                    a_j = 0
                else:  # Default REVEAL_GATED
                    a_j = job.reveal_tic

                rot_start = max(current_time, a_j)
                rot_finish = rot_start + rot_tics
                acq_start = max(job.reveal_tic, rot_finish)
                start_t = acq_start + acq_tics

                comp_t = start_t + job.service_duration_tics
                lateness = comp_t - job.deadline_tic

                perm_completion[j_id] = comp_t
                perm_lateness[j_id] = lateness
                max_l = max(max_l, lateness)

                current_time = comp_t
                cur_th, cur_ph = job.angle_deg, job.elevation_deg

            if max_l < best_l_star:
                best_l_star = max_l
                best_perm = perm
                best_completion = perm_completion
                best_lateness = perm_lateness

        return DiscreteScheduleResult(
            optimal_permutation=best_perm,
            lateness_optimal_l_star_tics=best_l_star,
            lateness_optimal_l_star_s=best_l_star * self.params.tic_duration_s,
            tactical_margin_tics=-best_l_star,
            completion_tics=best_completion,
            lateness_per_threat=best_lateness,
            peak_static_concurrency=peak_w,
            instantaneous_los_clique=instantaneous_los_clique,
            min_slack_tics=min_slack,
            raw_workload_tics=b_work_ham,
            is_feasible=(best_l_star <= 0)
        )
    def solve_with_actionability_lead(
        self,
        jobs: List[TicThreatJob],
        lead_tics: int,
        initial_reticle_deg: float = 0.0,
        instantaneous_los_clique: int = 1
    ) -> DiscreteScheduleResult:
        """Solve optimal schedule under uniform advance actionability lead: a_j = max(0, r_j - lead_tics)."""
        return self.solve(
            jobs=jobs,
            initial_reticle_deg=initial_reticle_deg,
            instantaneous_los_clique=instantaneous_los_clique,
            actionability_lead_tics=lead_tics
        )



# =============================================================================
# SIMULATION CONTROLLERS (POLICIES)
# =============================================================================

class ControllerPolicy(str, Enum):
    ORACLE = "ORACLE"                 # Sequence-optimal scheduler (reveal-gated L*_tic)
    PRE_AIM_ORACLE = "PRE_AIM_ORACLE" # Pre-aim oracle (pre-positions aim before reveal)
    FIFO = "FIFO"                     # First revealed, first serviced
    NEAREST_ANGLE = "NEAREST_ANGLE"   # Greedy minimal angular reticle switch
    EDF = "EDF"                       # Earliest deadline first
    LEFT_TO_RIGHT = "LEFT_TO_RIGHT"   # Static spatial left-to-right sweep




class SimulationController:
    """Base class for clearing agents executing inside the discrete ViZDoom loop."""

    def __init__(self, policy: ControllerPolicy, params: TicCombatParameters, initial_reticle_deg: float = 0.0):
        self.policy = policy
        self.params = params
        self.reticle_deg: float = float(initial_reticle_deg)
        self.current_target_id: Optional[str] = None
        self.target_state: str = "IDLE"  # IDLE, ROTATING, ACQUIRING, SERVICING
        self.state_countdown_tics: int = 0
        self.cleared_threat_ids: Set[str] = set()

    def select_next_target(
        self,
        visible_threats: Dict[str, TicThreatJob],
        scheduler_result: Optional[DiscreteScheduleResult] = None
    ) -> Optional[str]:
        """Select the next threat to service from currently revealed unserviced threats."""
        candidates = [t for t_id, t in visible_threats.items() if t_id not in self.cleared_threat_ids]
        if not candidates:
            return None

        if self.policy in (ControllerPolicy.ORACLE, ControllerPolicy.PRE_AIM_ORACLE) and scheduler_result is not None:
            for j_id in scheduler_result.optimal_permutation:
                if j_id in [c.id for c in candidates]:
                    return j_id

        elif self.policy == ControllerPolicy.FIFO:
            # Sort by earliest reveal tic
            candidates.sort(key=lambda t: t.reveal_tic)
            return candidates[0].id

        elif self.policy == ControllerPolicy.NEAREST_ANGLE:
            # Sort by smallest angular difference to current reticle
            candidates.sort(key=lambda t: angle_diff_deg(self.reticle_deg, t.angle_deg))
            return candidates[0].id

        elif self.policy == ControllerPolicy.EDF:
            # Sort by earliest deadline tic
            candidates.sort(key=lambda t: t.deadline_tic)
            return candidates[0].id

        elif self.policy == ControllerPolicy.LEFT_TO_RIGHT:
            # Sort by angle from left (+90 deg) to right (-90 deg)
            candidates.sort(key=lambda t: -t.angle_deg)
            return candidates[0].id

        return candidates[0].id

    def update_tic(
        self,
        current_tic: int,
        visible_threats: Dict[str, TicThreatJob],
        scheduler_result: Optional[DiscreteScheduleResult] = None
    ) -> Optional[str]:
        """Execute one simulation tic of player action. Returns target_id if a target was cleared this tic."""
        just_cleared_id = None

        if self.current_target_id is None or self.current_target_id in self.cleared_threat_ids:
            next_t = self.select_next_target(visible_threats, scheduler_result)
            if next_t is not None:
                self.current_target_id = next_t
                target_job = visible_threats[next_t]
                
                # Check if rotation is needed
                diff = angle_diff_deg(self.reticle_deg, target_job.angle_deg)
                if diff > 1e-4:
                    self.target_state = "ROTATING"
                    rot_tics = int(math.ceil(diff / self.params.max_aim_deg_per_tic))
                    self.state_countdown_tics = rot_tics
                else:
                    self.target_state = "ACQUIRING"
                    self.state_countdown_tics = self.params.acquisition_tics
            else:
                self.target_state = "IDLE"
                return None

        # Execute state machine countdown
        if self.target_state == "ROTATING":
            self.state_countdown_tics -= 1
            if self.state_countdown_tics <= 0:
                target_job = visible_threats[self.current_target_id]
                self.reticle_deg = target_job.angle_deg
                self.target_state = "ACQUIRING"
                self.state_countdown_tics = self.params.acquisition_tics

        elif self.target_state == "ACQUIRING":
            self.state_countdown_tics -= 1
            if self.state_countdown_tics <= 0:
                self.target_state = "SERVICING"
                target_job = visible_threats[self.current_target_id]
                self.state_countdown_tics = target_job.service_duration_tics

        elif self.target_state == "SERVICING":
            self.state_countdown_tics -= 1
            if self.state_countdown_tics <= 0:
                # Target successfully cleared!
                just_cleared_id = self.current_target_id
                self.cleared_threat_ids.add(just_cleared_id)
                self.current_target_id = None
                self.target_state = "IDLE"

        return just_cleared_id


# =============================================================================
# DETERMINISTIC SIMULATION REFEREE (VIZDOOM MICRO-ARENA HARNESS)
# =============================================================================

@dataclass
class SimulationEpisodeLog:
    """Execution telemetry recorded per micro-arena run."""
    scenario_id: str
    controller_policy: ControllerPolicy
    player_survived: bool
    death_tic: Optional[int]
    total_tics: int
    threat_reveal_tics: Dict[str, int]
    threat_clear_tics: Dict[str, int]
    threat_deadline_tics: Dict[str, int]
    cleared_threat_order: List[str]
    max_realized_lateness_tics: int
    tactical_margin_tics: int
    peak_static_concurrency: int
    min_slack_tics: int
    raw_workload_tics: int


class DeterministicSimulationReferee:
    """Simulates deterministic micro-arena combat on the 35 Hz ViZDoom clock."""

    def __init__(self, params: Optional[TicCombatParameters] = None):
        self.params = params or TicCombatParameters()
        self.scheduler = DiscreteTicScheduler(self.params)

    def extract_tic_jobs(
        self,
        geo_module: GeometricModule,
        route_index: int = 0,
        elevation_mode: str = "GEOMETRIC"
    ) -> List[TicThreatJob]:
        """Compile 2D / 2.5D geometry into integer-tic jobs via height-aware CheckSight engine queries."""
        route = geo_module.routes[route_index]
        total_tics = int(math.ceil(route.total_length_m / self.params.move_m_per_tic))

        # Build 2.5D obstacle prism list
        if geo_module.obstacles_25d:
            obs_25d = geo_module.obstacles_25d
        else:
            obs_25d = [
                GeometricObstacle(id=f"obs_{i}", polygon=p, z_min_m=0.0, z_max_m=float("inf"))
                for i, p in enumerate(geo_module.obstacles)
            ]

        # Fast planar check: if all obstacles are infinite height and route + threats have no elevation deltas
        is_pure_planar = (
            not getattr(route, "_is_3d", False)
            and all(t.z_m is None and t.elevation_deg == 0.0 for t in geo_module.threats)
            and all(math.isinf(o.z_max_m) for o in obs_25d)
            and elevation_mode != "AUTHORED"
        )
        obs_segs_2d = extract_polygon_segments(geo_module.obstacles) if is_pure_planar else []

        jobs: List[TicThreatJob] = []

        for threat in geo_module.threats:
            qx, qy = threat.threat_anchor
            qz = float(threat.z_m) if threat.z_m is not None else self.params.eye_height_m
            target_pt_3d = (float(qx), float(qy), qz)

            first_vis_tic: Optional[int] = None
            vis_angle_deg: float = 0.0
            vis_elevation_deg: float = 0.0

            for k in range(total_tics + 1):
                s = k * self.params.move_m_per_tic
                if s > route.total_length_m:
                    break

                if is_pure_planar:
                    pos = route.position_at_distance(s)
                    blocked = False
                    for s1, s2 in obs_segs_2d:
                        if segments_intersect(pos, (qx, qy), s1, s2):
                            blocked = True
                            break
                    if not blocked:
                        first_vis_tic = k
                        forward_heading = route.forward_heading_at_distance(s)
                        target_heading = heading_to_deg(pos, (qx, qy))
                        vis_angle_deg = normalize_angle_deg(target_heading - forward_heading)
                        vis_elevation_deg = 0.0
                        break
                else:
                    eye_pt = route.eye_position_at_distance(s, self.params.eye_height_m)
                    blocked = False
                    for obs in obs_25d:
                        if ray_intersects_prism_25d(eye_pt, target_pt_3d, obs.polygon, obs.z_min_m, obs.z_max_m):
                            blocked = True
                            break

                    if not blocked:
                        first_vis_tic = k
                        forward_heading = route.forward_heading_at_distance(s)
                        target_heading = heading_to_deg((eye_pt[0], eye_pt[1]), (qx, qy))
                        vis_angle_deg = normalize_angle_deg(target_heading - forward_heading)
                        if elevation_mode == "AUTHORED" or (threat.z_m is None and threat.elevation_deg != 0.0):
                            vis_elevation_deg = float(threat.elevation_deg)
                        else:
                            vis_elevation_deg = derived_aim_elevation_deg(eye_pt, target_pt_3d)
                        break

            if first_vis_tic is not None:
                due_tics = int(math.ceil(threat.authored_due_window_s * self.params.ticrate_hz))
                serv_tics = int(math.ceil(threat.service_duration_s * self.params.ticrate_hz))
                jobs.append(TicThreatJob(
                    id=threat.id,
                    reveal_tic=first_vis_tic,
                    due_window_tics=due_tics,
                    deadline_tic=first_vis_tic + due_tics,
                    angle_deg=vis_angle_deg,
                    threat_anchor=(qx, qy),
                    service_duration_tics=serv_tics,
                    elevation_deg=vis_elevation_deg,
                    target_z=threat.z_m
                ))

        jobs.sort(key=lambda j: j.reveal_tic)
        return jobs

    def compute_instantaneous_los_clique(
        self,
        geo_module: GeometricModule,
        route_index: int = 0
    ) -> int:
        """Compute peak simultaneous physical LOS count from any single point along trajectory."""
        route = geo_module.routes[route_index]
        total_tics = int(math.ceil(route.total_length_m / self.params.move_m_per_tic))
        
        if geo_module.obstacles_25d:
            obs_25d = geo_module.obstacles_25d
        else:
            obs_25d = [
                GeometricObstacle(id=f"obs_{i}", polygon=p, z_min_m=0.0, z_max_m=float("inf"))
                for i, p in enumerate(geo_module.obstacles)
            ]

        is_pure_planar = (
            not getattr(route, "_is_3d", False)
            and all(t.z_m is None for t in geo_module.threats)
            and all(math.isinf(o.z_max_m) for o in obs_25d)
        )
        obs_segs_2d = extract_polygon_segments(geo_module.obstacles) if is_pure_planar else []

        peak_simul = 0
        for k in range(total_tics + 1):
            s = k * self.params.move_m_per_tic
            if s > route.total_length_m:
                break
            
            simul_now = 0
            if is_pure_planar:
                pos = route.position_at_distance(s)
                for threat in geo_module.threats:
                    qx, qy = threat.threat_anchor
                    blocked = False
                    for s1, s2 in obs_segs_2d:
                        if segments_intersect(pos, (qx, qy), s1, s2):
                            blocked = True
                            break
                    if not blocked:
                        simul_now += 1
            else:
                eye_pt = route.eye_position_at_distance(s, self.params.eye_height_m)
                for threat in geo_module.threats:
                    qx, qy = threat.threat_anchor
                    qz = float(threat.z_m) if threat.z_m is not None else self.params.eye_height_m
                    target_pt_3d = (float(qx), float(qy), qz)
                    blocked = False
                    for obs in obs_25d:
                        if ray_intersects_prism_25d(eye_pt, target_pt_3d, obs.polygon, obs.z_min_m, obs.z_max_m):
                            blocked = True
                            break
                    if not blocked:
                        simul_now += 1

            peak_simul = max(peak_simul, simul_now)

        return peak_simul


    def run_episode(
        self,
        geo_module: GeometricModule,
        policy: ControllerPolicy = ControllerPolicy.ORACLE,
        route_index: int = 0,
        initial_reticle_deg: float = 0.0
    ) -> SimulationEpisodeLog:
        """Run one synchronous deterministic episode."""
        route = geo_module.routes[route_index]
        total_tics = int(math.ceil(route.total_length_m / self.params.move_m_per_tic))
        jobs = self.extract_tic_jobs(geo_module, route_index)
        job_map = {j.id: j for j in jobs}

        # Solve scheduling oracle
        sched_res = self.scheduler.solve(jobs, initial_reticle_deg=initial_reticle_deg)

        controller = SimulationController(policy, self.params, initial_reticle_deg=initial_reticle_deg)
        visible_threats: Dict[str, TicThreatJob] = {}
        threat_reveal_tics: Dict[str, int] = {}
        threat_clear_tics: Dict[str, int] = {}
        threat_deadline_tics: {str: int} = {j.id: j.deadline_tic for j in jobs}
        cleared_order: List[str] = []

        player_survived = True
        death_tic = None

        for k in range(total_tics + 200): # Allow tail room for servicing
            # 1. Update revelations
            for j in jobs:
                if k >= j.reveal_tic and j.id not in visible_threats:
                    visible_threats[j.id] = j
                    threat_reveal_tics[j.id] = k

            # 2. Check Hostile Deadlines (Deterministic Kill Referee)
            for j_id, j in visible_threats.items():
                if j_id not in controller.cleared_threat_ids:
                    if k >= j.deadline_tic:
                        player_survived = False
                        death_tic = k
                        break

            if not player_survived:
                break

            # 3. Update Controller Action
            just_cleared = controller.update_tic(k, visible_threats, sched_res)
            if just_cleared:
                threat_clear_tics[just_cleared] = k
                cleared_order.append(just_cleared)

            # Check if all threats cleared
            if len(controller.cleared_threat_ids) == len(jobs) and len(jobs) > 0:
                break

        # Calculate max realized lateness
        max_realized_lateness = -999
        for j in jobs:
            c_t = threat_clear_tics.get(j.id, total_tics + 999)
            lat = c_t - j.deadline_tic
            max_realized_lateness = max(max_realized_lateness, lat)

        return SimulationEpisodeLog(
            scenario_id=geo_module.module_id,
            controller_policy=policy,
            player_survived=player_survived,
            death_tic=death_tic,
            total_tics=k,
            threat_reveal_tics=threat_reveal_tics,
            threat_clear_tics=threat_clear_tics,
            threat_deadline_tics=threat_deadline_tics,
            cleared_threat_order=cleared_order,
            max_realized_lateness_tics=max_realized_lateness if jobs else 0,
            tactical_margin_tics=sched_res.tactical_margin_tics,
            peak_static_concurrency=sched_res.peak_static_concurrency,
            min_slack_tics=sched_res.min_slack_tics,
            raw_workload_tics=sched_res.raw_workload_tics
        )


# =============================================================================
# NOISE SIMULATION HARNESS (GATE 11D)
# =============================================================================

class NoiseSimulationHarness:
    """Evaluates empirical survival probabilities under stochastic motor/timing jitter."""

    def __init__(
        self,
        base_params: Optional[TicCombatParameters] = None,
        sigma_acq_s: float = 0.03,
        sigma_aim_deg_s: float = 40.0,
        sigma_aim_err_deg: float = 3.0
    ):
        self.base_params = base_params or TicCombatParameters()
        self.sigma_acq_s = sigma_acq_s
        self.sigma_aim_deg_s = sigma_aim_deg_s
        self.sigma_aim_err_deg = sigma_aim_err_deg

    def run_noisy_trials(
        self,
        geo_module: GeometricModule,
        n_trials: int = 100,
        policy: ControllerPolicy = ControllerPolicy.ORACLE,
        seed: int = 42
    ) -> float:
        """Run N noisy trials and return empirical survival probability in [0, 1]."""
        rng = np.random.default_rng(seed)
        survivals = 0

        for _ in range(n_trials):
            # Sample noisy parameters
            sample_acq_s = max(0.04, rng.normal(self.base_params.acquisition_latency_s, self.sigma_acq_s))
            sample_aim_s = max(120.0, rng.normal(self.base_params.aim_velocity_deg_s, self.sigma_aim_deg_s))
            
            trial_params = TicCombatParameters(
                ticrate_hz=self.base_params.ticrate_hz,
                units_per_meter=self.base_params.units_per_meter,
                v_move_mps=self.base_params.v_move_mps,
                aim_velocity_deg_s=sample_aim_s,
                acquisition_latency_s=sample_acq_s,
                inspect_duration_s=self.base_params.inspect_duration_s
            )

            ref = DeterministicSimulationReferee(trial_params)
            log = ref.run_episode(geo_module, policy=policy)
            if log.player_survived:
                survivals += 1

        return survivals / max(1, n_trials)


# =============================================================================
# POPULATION BENCHMARK & BASELINE SHOOTOUT (ROUND 11.1)
# =============================================================================

@dataclass
class ArenaBenchmarkRecord:
    scenario_id: str
    category: str
    tactical_margin_tics: int
    peak_static_concurrency: int
    min_slack_tics: int
    raw_workload_tics: int
    is_feas_oracle: bool
    empirical_survival: Dict[ControllerPolicy, float]
    mean_empirical_survival: float


@dataclass
class BaselineEvaluationMetrics:
    predictor_name: str
    spearman_rho: float
    roc_auc: float
    brier_score: float
    logfo_cv_roc_auc: float
    logfo_cv_brier: float
    per_family_logfo_auc: Dict[str, float]


@dataclass
class PopulationBenchmarkReport:
    total_arenas: int
    total_episodes: int
    records: List[ArenaBenchmarkRecord]
    baseline_metrics: Dict[str, BaselineEvaluationMetrics]


def compute_spearman_rho(x: List[float], y: List[float]) -> float:
    """Compute Spearman rank correlation coefficient using scipy.stats with tie handling."""
    res = scipy.stats.spearmanr(x, y)
    val = getattr(res, "statistic", getattr(res, "correlation", 0.0))
    return float(val) if not math.isnan(val) else 0.0


def compute_roc_auc(scores: List[float], labels: List[int]) -> float:
    """Compute ROC-AUC using sklearn.metrics.roc_auc_score with tie handling."""
    labels_arr = np.array(labels)
    if len(np.unique(labels_arr)) < 2:
        return 1.0
    return float(roc_auc_score(labels, scores))


def fit_univariate_logistic(x_train: np.ndarray, y_train: np.ndarray, n_iter: int = 100, lr: float = 0.05) -> Tuple[float, float]:
    """Fit simple 1D logistic regression via gradient descent."""
    beta0 = 0.0
    beta1 = 0.0
    
    # Standardize x
    mean_x = float(np.mean(x_train))
    std_x = float(np.std(x_train)) + 1e-6
    x_norm = (x_train - mean_x) / std_x

    for _ in range(n_iter):
        z = beta0 + beta1 * x_norm
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))
        grad0 = float(np.mean(p - y_train))
        grad1 = float(np.mean((p - y_train) * x_norm))
        beta0 -= lr * grad0
        beta1 -= lr * grad1

    # Convert back to unstandardized
    b1_raw = beta1 / std_x
    b0_raw = beta0 - (beta1 * mean_x / std_x)
    return (b0_raw, b1_raw)


def run_population_benchmark(
    arenas: List[GeometricModule],
    controllers: Optional[List[ControllerPolicy]] = None,
    n_trials: int = 100
) -> PopulationBenchmarkReport:
    """Run full population benchmark (60 arenas x 5 controllers x 100 trials = 30k episodes)."""
    policies = controllers or [
        ControllerPolicy.ORACLE,
        ControllerPolicy.FIFO,
        ControllerPolicy.NEAREST_ANGLE,
        ControllerPolicy.EDF,
        ControllerPolicy.LEFT_TO_RIGHT
    ]

    harness = NoiseSimulationHarness(sigma_acq_s=0.02, sigma_aim_deg_s=30.0)
    ref = DeterministicSimulationReferee()
    records: List[ArenaBenchmarkRecord] = []
    total_episodes = 0

    for mod in arenas:
        jobs = ref.extract_tic_jobs(mod)
        k_static = ref.compute_instantaneous_los_clique(mod)
        sched = ref.scheduler.solve(jobs, instantaneous_los_clique=k_static)
        
        emp_surv: Dict[ControllerPolicy, float] = {}
        for pol in policies:
            p_s = harness.run_noisy_trials(mod, n_trials=n_trials, policy=pol)
            emp_surv[pol] = p_s
            total_episodes += n_trials

        mean_s = float(np.mean(list(emp_surv.values())))
        records.append(ArenaBenchmarkRecord(
            scenario_id=mod.module_id,
            category=mod.category,
            tactical_margin_tics=sched.tactical_margin_tics,
            peak_static_concurrency=sched.instantaneous_los_clique,
            min_slack_tics=sched.min_slack_tics,
            raw_workload_tics=sched.raw_workload_tics,
            is_feas_oracle=sched.is_feasible,
            empirical_survival=emp_surv,
            mean_empirical_survival=mean_s
        ))

    # Evaluate Baseline Shootout
    baseline_metrics = evaluate_baseline_shootout(records)

    return PopulationBenchmarkReport(
        total_arenas=len(arenas),
        total_episodes=total_episodes,
        records=records,
        baseline_metrics=baseline_metrics
    )


def evaluate_baseline_shootout(records: List[ArenaBenchmarkRecord]) -> Dict[str, BaselineEvaluationMetrics]:
    """Compute comparative evaluation metrics and LOGFO cross-validation across all predictors."""
    predictors = {
        "Tactical Margin M_tic": [float(r.tactical_margin_tics) for r in records],
        "Peak Physical LOS K_static (Inverted)": [-float(r.peak_static_concurrency) for r in records],
        "Min Slack sigma_min": [float(r.min_slack_tics) for r in records],
        "Hamiltonian Workload B_work (Inverted)": [-float(r.raw_workload_tics) for r in records],
    }

    # Primary Ground Truth Target: Mean survival across the 4 non-Oracle controllers
    non_oracle_policies = [
        ControllerPolicy.FIFO,
        ControllerPolicy.NEAREST_ANGLE,
        ControllerPolicy.EDF,
        ControllerPolicy.LEFT_TO_RIGHT
    ]
    empirical_survivals = [
        float(np.mean([r.empirical_survival[p] for p in non_oracle_policies]))
        for r in records
    ]
    binary_labels = [1 if s >= 0.50 else 0 for s in empirical_survivals]
    categories = [r.category for r in records]
    unique_cats = sorted(list(set(categories)))

    results: Dict[str, BaselineEvaluationMetrics] = {}

    for name, scores in predictors.items():
        # 1. Spearman Rho with empirical continuous survival
        rho = compute_spearman_rho(scores, empirical_survivals)

        # 2. Binary classification ROC-AUC
        auc = compute_roc_auc(scores, binary_labels)

        # 3. In-sample Brier score
        b0, b1 = fit_univariate_logistic(np.array(scores), np.array(binary_labels))
        preds = 1.0 / (1.0 + np.exp(-np.clip(b0 + b1 * np.array(scores), -20.0, 20.0)))
        brier = float(brier_score_loss(binary_labels, preds))

        # 4. Leave-One-Geometry-Family-Out (LOGFO) Cross-Validation
        oof_preds = np.zeros(len(records))
        per_fam_auc: Dict[str, float] = {}

        for cat in unique_cats:
            train_idx = [i for i, c in enumerate(categories) if c != cat]
            test_idx = [i for i, c in enumerate(categories) if c == cat]

            x_train = np.array([scores[i] for i in train_idx])
            y_train = np.array([binary_labels[i] for i in train_idx])
            x_test = np.array([scores[i] for i in test_idx])
            y_test = [binary_labels[i] for i in test_idx]

            cb0, cb1 = fit_univariate_logistic(x_train, y_train)
            test_pred = 1.0 / (1.0 + np.exp(-np.clip(cb0 + cb1 * x_test, -20.0, 20.0)))
            for loc_idx, glob_idx in enumerate(test_idx):
                oof_preds[glob_idx] = test_pred[loc_idx]

            # Per-family held-out AUC
            if len(np.unique(y_test)) >= 2:
                per_fam_auc[cat] = compute_roc_auc(list(test_pred), y_test)
            else:
                per_fam_auc[cat] = 1.0

        logfo_auc = compute_roc_auc(list(oof_preds), binary_labels)
        logfo_brier = float(brier_score_loss(binary_labels, oof_preds))

        results[name] = BaselineEvaluationMetrics(
            predictor_name=name,
            spearman_rho=rho,
            roc_auc=auc,
            brier_score=brier,
            logfo_cv_roc_auc=logfo_auc,
            logfo_cv_brier=logfo_brier,
            per_family_logfo_auc=per_fam_auc
        )

    return results


