"""Geometrically-induced single-machine real-time scheduling solver [G + C + P].

V0 MODEL ASSUMPTIONS:
1. Threat Release Time: r_j = path_reveal_s / v_move (derived from continuous ray visibility).
2. Threat Due Date / Damage Deadline: D_j = r_j + d_j_react_opp + TTK(r_j).
3. Sequence-Dependent Setup Time: c(T_i, T_j) = t_acquire + Δθ(centroid_i, centroid_j) / ω_aim.
4. Processing Time: p_j = t_inspect (non-preemptive inspection dwell).
5. Threat angle is evaluated at the first-reveal coordinate.
6. Real-time scheduling problem classification: 1 | r_j, s_ij | L_max.
"""

from __future__ import annotations
import math
from typing import List, Tuple, Dict, Set, Optional, Any, NamedTuple
from dataclasses import dataclass
import itertools

from .model import CombatModel, PlayerModel
from .geometry import angle_diff_deg


@dataclass(frozen=True)
class ThreatEvent:
    """Timeline event for a threat along a movement path [G + C]."""
    threat_id: str
    reveal_time_s: float
    deadline_time_s: float
    centroid_angle_deg: float
    elevation_deg: float = 0.0


@dataclass
class ClassicalSchedulingBaselines:
    """Standard operations-research metrics for single-machine release/deadline instances."""
    static_overlap_width: int  # Max number of mutually overlapping [r_j, D_j] intervals
    min_slack_s: float  # min_j (D_j - r_j - p_j)
    total_service_workload_s: float  # sum(p_j) + optimal_setups
    max_setup_s: float  # max_{i,j} c(T_i, T_j)


@dataclass
class ServiceScheduleResult:
    """Result of optimal service scheduling over a trajectory [G + C + P]."""
    is_solvable: bool
    optimal_max_lateness_s: float  # L*(γ) = min_π max_j (C_j - D_j)
    optimal_clearing_order: List[str]
    max_frontier_width: int  # W_L*(γ): frontier width under lateness-optimal policy
    unconstrained_min_frontier_width: int  # W*(γ) = min_π max_t |F_π(t)|
    feasible_min_frontier_width: Optional[int]  # W_feasible*(γ) = min_{π: L_max(π) <= 0} max_t |F_π(t)|
    unresolved_deadlines_missed: List[str]
    timeline: List[Dict[str, Any]]
    baselines: ClassicalSchedulingBaselines


def compute_static_overlap_width(events: List[ThreatEvent]) -> int:
    """Compute maximum number of concurrently open [r_j, D_j] deadline windows."""
    if not events:
        return 0
    endpoints = []
    for ev in events:
        endpoints.append((ev.reveal_time_s, 1))  # +1 when window opens
        endpoints.append((ev.deadline_time_s, -1))  # -1 when window closes
    # Sort endpoints; if equal times, open (+1) before close (-1)
    endpoints.sort(key=lambda x: (x[0], -x[1]))
    max_overlap = 0
    current = 0
    for _, delta in endpoints:
        current += delta
        max_overlap = max(max_overlap, current)
    return max_overlap


def solve_service_schedule(
    threat_events: List[ThreatEvent],
    combat_model: CombatModel,
    player_model: PlayerModel,
    initial_aim_deg: float = 0.0
) -> ServiceScheduleResult:
    """Exhaustive permutation solver computing L*(γ), W*(γ), W_feasible*(γ), and OR baselines [G + C + P]."""
    if not threat_events:
        baselines = ClassicalSchedulingBaselines(
            static_overlap_width=0,
            min_slack_s=0.0,
            total_service_workload_s=0.0,
            max_setup_s=0.0
        )
        return ServiceScheduleResult(
            is_solvable=True,
            optimal_max_lateness_s=0.0,
            optimal_clearing_order=[],
            max_frontier_width=0,
            unconstrained_min_frontier_width=0,
            feasible_min_frontier_width=0,
            unresolved_deadlines_missed=[],
            timeline=[],
            baselines=baselines
        )

    events = sorted(threat_events, key=lambda e: e.reveal_time_s)
    threat_ids = [e.threat_id for e in events]
    n = len(events)
    event_map = {e.threat_id: e for e in events}

    # Classical baselines
    static_w = compute_static_overlap_width(events)
    min_slack = min(e.deadline_time_s - e.reveal_time_s - player_model.inspect_duration_s for e in events)
    
    max_setup = 0.0
    for e1 in events:
        for e2 in events:
            diff = angle_diff_deg(e1.centroid_angle_deg, e2.centroid_angle_deg)
            c_val = player_model.service_cost_s(diff)
            max_setup = max(max_setup, c_val)

    best_lateness = float('inf')
    best_lateness_order: List[str] = []
    best_lateness_frontier = float('inf')
    best_missed_list: List[str] = []
    best_timeline: List[Dict[str, Any]] = []

    unconstrained_min_frontier = float('inf')
    feasible_min_frontier = float('inf')
    min_total_setup_workload = float('inf')

    # Permutation search over all n! clearing sequences (n <= 10)
    for perm in itertools.permutations(threat_ids):
        current_time = 0.0
        current_aim = initial_aim_deg
        timeline = []
        perm_lateness = -float('inf')
        missed = []
        
        service_intervals: Dict[str, Tuple[float, float]] = {}

        # Track pure setup workload along this permutation
        perm_setup_sum = 0.0
        cur_setup_aim = initial_aim_deg

        for tid in perm:
            ev = event_map[tid]
            start_inspect_time = max(current_time, ev.reveal_time_s)

            ang_diff = angle_diff_deg(current_aim, ev.centroid_angle_deg)
            tot_diff = math.hypot(ang_diff, ev.elevation_deg)
            setup_cost = player_model.service_cost_s(tot_diff)
            finish_time = start_inspect_time + setup_cost + player_model.inspect_duration_s

            lateness_j = finish_time - ev.deadline_time_s
            perm_lateness = max(perm_lateness, lateness_j)

            if finish_time > ev.deadline_time_s:
                missed.append(tid)

            service_intervals[tid] = (start_inspect_time, finish_time)

            timeline.append({
                "threat_id": tid,
                "reveal_time": ev.reveal_time_s,
                "start_time": start_inspect_time,
                "finish_time": finish_time,
                "deadline": ev.deadline_time_s,
                "lateness_s": lateness_j,
                "passed": finish_time <= ev.deadline_time_s
            })

            current_time = finish_time
            current_aim = ev.centroid_angle_deg

            # Hamiltonian setup sum
            ang_diff_setup = angle_diff_deg(cur_setup_aim, ev.centroid_angle_deg)
            tot_diff_setup = math.hypot(ang_diff_setup, ev.elevation_deg)
            perm_setup_sum += player_model.service_cost_s(tot_diff_setup)
            cur_setup_aim = ev.centroid_angle_deg

        if perm_setup_sum < min_total_setup_workload:
            min_total_setup_workload = perm_setup_sum

        # Calculate exact chronological frontier W(γ, π) = max_t |F_π(t)|
        critical_timestamps = set()
        for ev in events:
            critical_timestamps.add(ev.reveal_time_s)
        for _, finish_t in service_intervals.values():
            critical_timestamps.add(finish_t)

        max_frontier_in_perm = 0
        for t in sorted(critical_timestamps):
            active_threats = [
                tid for tid, ev in event_map.items()
                if ev.reveal_time_s <= t and (tid not in service_intervals or t < service_intervals[tid][1])
            ]
            max_frontier_in_perm = max(max_frontier_in_perm, len(active_threats))

        # 1. Track unconstrained minimum frontier width W*(γ)
        if max_frontier_in_perm < unconstrained_min_frontier:
            unconstrained_min_frontier = max_frontier_in_perm

        # 2. Track feasible minimum frontier width W_feasible*(γ)
        if perm_lateness <= 1e-6:
            if max_frontier_in_perm < feasible_min_frontier:
                feasible_min_frontier = max_frontier_in_perm

        # 3. Track lateness-optimal policy L*(γ)
        if perm_lateness < best_lateness:
            best_lateness = perm_lateness
            best_lateness_order = list(perm)
            best_lateness_frontier = max_frontier_in_perm
            best_missed_list = missed
            best_timeline = timeline
        elif abs(perm_lateness - best_lateness) < 1e-6:
            if max_frontier_in_perm < best_lateness_frontier:
                best_lateness_frontier = max_frontier_in_perm
                best_lateness_order = list(perm)
                best_missed_list = missed
                best_timeline = timeline

    # B_work = pure lower bound on uninterrupted service workload (Hamiltonian setup + processing)
    b_work = (n * player_model.inspect_duration_s) + (min_total_setup_workload if min_total_setup_workload != float('inf') else 0.0)

    baselines = ClassicalSchedulingBaselines(
        static_overlap_width=static_w,
        min_slack_s=min_slack,
        total_service_workload_s=b_work,
        max_setup_s=max_setup
    )

    return ServiceScheduleResult(
        is_solvable=(best_lateness <= 1e-6),
        optimal_max_lateness_s=best_lateness,
        optimal_clearing_order=best_lateness_order,
        max_frontier_width=int(best_lateness_frontier),
        unconstrained_min_frontier_width=int(unconstrained_min_frontier),
        feasible_min_frontier_width=int(feasible_min_frontier) if feasible_min_frontier != float('inf') else None,
        unresolved_deadlines_missed=best_missed_list,
        timeline=best_timeline,
        baselines=baselines
    )


# -----------------------------------------------------------------------------
# INDEPENDENT EXACT ORACLE: Dynamic Programming over Subsets
# -----------------------------------------------------------------------------

def solve_service_schedule_dp(
    threat_events: List[ThreatEvent],
    combat_model: CombatModel,
    player_model: PlayerModel,
    initial_aim_deg: float = 0.0
) -> Tuple[float, List[str]]:
    """Independent exact DP oracle for 1 | r_j, s_ij | L_max using Pareto frontiers over (C, L_max).

    State: (bitmask S of serviced jobs, last_serviced_job_idx) -> List[ParetoTuple(C, L_max, order)].
    """
    if not threat_events:
        return 0.0, []

    events = sorted(threat_events, key=lambda e: e.reveal_time_s)
    n = len(events)

    def add_pareto(frontier: List[Tuple[float, float, List[int]]], c_new: float, l_new: float, order_new: List[int]):
        """Add (c_new, l_new) to Pareto frontier, pruning dominated states."""
        for c_old, l_old, _ in frontier:
            if c_old <= c_new + 1e-9 and l_old <= l_new + 1e-9:
                return  # Dominated by existing tuple
        # Remove any existing tuples dominated by the new one
        pruned = [
            (c, l, ord_l) for (c, l, ord_l) in frontier
            if not (c_new <= c + 1e-9 and l_new <= l + 1e-9)
        ]
        pruned.append((c_new, l_new, order_new))
        frontier[:] = pruned

    # dp[(mask, last_idx)] -> list of (C, L_max, order)
    dp: Dict[Tuple[int, int], List[Tuple[float, float, List[int]]]] = {}

    # Base states
    for i, ev in enumerate(events):
        mask = (1 << i)
        start_t = max(0.0, ev.reveal_time_s)
        diff = angle_diff_deg(initial_aim_deg, ev.centroid_angle_deg)
        tot_diff = math.hypot(diff, ev.elevation_deg)
        setup = player_model.service_cost_s(tot_diff)
        finish_t = start_t + setup + player_model.inspect_duration_s
        lateness = finish_t - ev.deadline_time_s
        dp[(mask, i)] = [(finish_t, lateness, [i])]

    # Transition to larger subsets
    for size in range(2, n + 1):
        next_dp: Dict[Tuple[int, int], List[Tuple[float, float, List[int]]]] = {}
        for (mask, last_i), tuples in dp.items():
            last_ev = events[last_i]
            for next_i, next_ev in enumerate(events):
                if not (mask & (1 << next_i)):
                    next_mask = mask | (1 << next_i)
                    key = (next_mask, next_i)
                    if key not in next_dp:
                        next_dp[key] = []

                    diff = angle_diff_deg(last_ev.centroid_angle_deg, next_ev.centroid_angle_deg)
                    tot_diff = math.hypot(diff, next_ev.elevation_deg)
                    setup = player_model.service_cost_s(tot_diff)

                    for (c_time, l_max, order) in tuples:
                        start_t = max(c_time, next_ev.reveal_time_s)
                        finish_t = start_t + setup + player_model.inspect_duration_s
                        lateness_next = finish_t - next_ev.deadline_time_s
                        new_l_max = max(l_max, lateness_next)
                        add_pareto(next_dp[key], finish_t, new_l_max, order + [next_i])

        dp = next_dp

    full_mask = (1 << n) - 1
    best_lateness = float('inf')
    best_order_indices: List[int] = []

    for (mask, last_i), tuples in dp.items():
        if mask == full_mask:
            for (c_time, l_max, order) in tuples:
                if l_max < best_lateness:
                    best_lateness = l_max
                    best_order_indices = order

    best_threat_order = [events[i].threat_id for i in best_order_indices]
    return best_lateness, best_threat_order
