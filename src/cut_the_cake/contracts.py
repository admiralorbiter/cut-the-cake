"""Modular composition, port contracts, and dense-grid certification [G + C + P]."""

from __future__ import annotations
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from shapely.geometry import Polygon, LineString, Point

from .model import Module, Port, ThreatRegion, World, CombatModel, PlayerModel, InformationRegime
from .visibility import compute_visible_threats
from .conflicts import build_threat_incompatibility_graph
from .geometry import distance, is_segment_blocked


class ContractStatus(Enum):
    PASS = "PASS"
    FAIL_UNDECLARED_RAY = "FAIL_UNDECLARED_RAY"
    FAIL_EXTERNAL_BUDGET = "FAIL_EXTERNAL_BUDGET"
    FAIL_DEPTH = "FAIL_DEPTH"
    FAIL_RESONANCE = "FAIL_RESONANCE"


@dataclass
class CompositionValidationResult:
    """Diagnostic result of composing two modules across matching ports [G + C + P]."""
    status: ContractStatus
    module_a_id: str
    module_b_id: str
    internal_k_a_max: int
    internal_k_b_max: int
    global_k_max: int
    max_observed_external_clique: int
    max_observed_port_depth_m: float
    violations: List[str]


def sample_module_walkable_grid(
    module: Module,
    grid_spacing_m: float = 1.0
) -> List[Tuple[float, float]]:
    """Sample a deterministic uniform grid across the traversable interior of a module."""
    min_x, min_y, max_x, max_y = module.boundary.bounds
    pts = []
    for x in np.arange(min_x + grid_spacing_m / 2, max_x, grid_spacing_m):
        for y in np.arange(min_y + grid_spacing_m / 2, max_y, grid_spacing_m):
            p = Point(x, y)
            # Must be strictly inside module boundary and not inside any obstacle
            if module.boundary.contains(p):
                if not any(obs.contains(p) for obs in module.obstacles):
                    pts.append((x, y))
    if not pts:
        c = module.boundary.centroid
        pts.append((c.x, c.y))
    return pts


def check_ray_boundary_enclosure(
    eye_pos: Tuple[float, float],
    target_pos: Tuple[float, float],
    module: Module,
    all_obstacles: List[Polygon]
) -> bool:
    """Verify that an unobstructed ray escaping module passes through a declared port [G]."""
    ray_seg = LineString([eye_pos, target_pos])
    if is_segment_blocked(eye_pos, target_pos, all_obstacles):
        return True  # Blocked ray cannot violate enclosure

    # If ray escapes module boundary, it must intersect at least one port segment
    for port in module.ports:
        if ray_seg.intersects(port.segment):
            return True

    return False


def distance_from_port(port: Port, target_pt: Tuple[float, float]) -> float:
    """Measure line-of-sight penetration depth from the port boundary into external space."""
    return port.segment.distance(Point(target_pt))


def evaluate_module_composition(
    mod_a: Module,
    port_a: Port,
    mod_b: Module,
    port_b: Port,
    combat_model: CombatModel,
    player_model: PlayerModel,
    grid_spacing_m: float = 1.0
) -> CompositionValidationResult:
    """Evaluate whether composing Module A and Module B satisfies visibility contracts under dense grid certification [G + C + P]."""
    all_obs = mod_a.obstacles + mod_b.obstacles
    all_threats = mod_a.threats + mod_b.threats

    combined_poly = mod_a.boundary.union(mod_b.boundary)
    world = World(
        bounds=combined_poly.bounds,
        obstacles=all_obs,
        threats=all_threats,
        modules=[mod_a, mod_b]
    )

    # 1. Numerically certify internal concurrency across dense grid in Module A
    pts_a = sample_module_walkable_grid(mod_a, grid_spacing_m=grid_spacing_m)
    world_a = World(bounds=mod_a.boundary.bounds, obstacles=mod_a.obstacles, threats=mod_a.threats)
    internal_k_a_max = 0
    for pt in pts_a:
        vis_a = compute_visible_threats(pt, world_a, vis_threshold=combat_model.vis_threshold)
        _, k_a = build_threat_incompatibility_graph(vis_a, combat_model, player_model)
        internal_k_a_max = max(internal_k_a_max, k_a)

    # 2. Numerically certify internal concurrency across dense grid in Module B
    pts_b = sample_module_walkable_grid(mod_b, grid_spacing_m=grid_spacing_m)
    world_b = World(bounds=mod_b.boundary.bounds, obstacles=mod_b.obstacles, threats=mod_b.threats)
    internal_k_b_max = 0
    for pt in pts_b:
        vis_b = compute_visible_threats(pt, world_b, vis_threshold=combat_model.vis_threshold)
        _, k_b = build_threat_incompatibility_graph(vis_b, combat_model, player_model)
        internal_k_b_max = max(internal_k_b_max, k_b)

    # 3. Test global composition across all sample points in Module A
    global_k_max = 0
    max_ext_clique = 0
    max_port_depth = 0.0
    violations = []
    status = ContractStatus.PASS

    mod_b_threat_ids = {t.id for t in mod_b.threats}

    for pt in pts_a:
        vis_threats = compute_visible_threats(pt, world, vis_threshold=combat_model.vis_threshold)
        G, global_k = build_threat_incompatibility_graph(vis_threats, combat_model, player_model)
        global_k_max = max(global_k_max, global_k)

        # External threats from Module B visible from pt in Module A
        ext_threats = [tv for tv in vis_threats if tv.threat_id in mod_b_threat_ids]
        if ext_threats:
            G_ext, ext_k = build_threat_incompatibility_graph(ext_threats, combat_model, player_model)
            max_ext_clique = max(max_ext_clique, ext_k)

            for tv in ext_threats:
                threat_obj = next(t for t in mod_b.threats if t.id == tv.threat_id)
                c_pt = threat_obj.centroid
                
                # Check ray boundary enclosure
                if not check_ray_boundary_enclosure(pt, c_pt, mod_a, all_obs):
                    violations.append(f"Undeclared ray from {pt} to external threat {tv.threat_id}")
                    status = ContractStatus.FAIL_UNDECLARED_RAY

                # Check penetration depth from port
                depth_from_port = distance_from_port(port_a, c_pt)
                max_port_depth = max(max_port_depth, depth_from_port)
                if depth_from_port > port_a.max_depth:
                    violations.append(f"Maximum port penetration depth exceeded: {depth_from_port:.2f}m > {port_a.max_depth:.2f}m")
                    if status == ContractStatus.PASS:
                        status = ContractStatus.FAIL_DEPTH

            # Check external concurrency budget
            if ext_k > port_a.max_external_budget:
                violations.append(f"External concurrency budget exceeded at {pt}: observed external clique {ext_k} > {port_a.max_external_budget}")
                if status == ContractStatus.PASS:
                    status = ContractStatus.FAIL_EXTERNAL_BUDGET

    # Check for Visibility Resonance: where global concurrency exceeds certified internal + port budget
    if global_k_max > (internal_k_a_max + port_a.max_external_budget):
        violations.append(
            f"Visibility Resonance detected: Global K_ICI ({global_k_max}) > "
            f"Internal A ({internal_k_a_max}) + Port Budget ({port_a.max_external_budget})"
        )
        if status == ContractStatus.PASS:
            status = ContractStatus.FAIL_RESONANCE

    return CompositionValidationResult(
        status=status,
        module_a_id=mod_a.id,
        module_b_id=mod_b.id,
        internal_k_a_max=internal_k_a_max,
        internal_k_b_max=internal_k_b_max,
        global_k_max=global_k_max,
        max_observed_external_clique=max_ext_clique,
        max_observed_port_depth_m=max_port_depth,
        violations=violations
    )


# =============================================================================
# REAL-TIME CALCULUS & STATE-CONDITIONED DEMAND-BOUND INTERFACES (ROUND 5)
# =============================================================================

class AimSector(Enum):
    """Discrete player aim/crosshair orientation sectors."""
    LEFT = 0     # theta < -30 deg
    CENTER = 1   # -30 deg <= theta <= +30 deg
    RIGHT = 2    # theta > +30 deg

    @classmethod
    def from_angle_deg(cls, angle_deg: float) -> "AimSector":
        if angle_deg < -30.0:
            return cls.LEFT
        elif angle_deg > 30.0:
            return cls.RIGHT
        return cls.CENTER


def circular_angular_distance_deg(theta_1: float, theta_2: float) -> float:
    """Compute shortest geodesic distance between two angles on S^1 in [0, 180] degrees."""
    diff = abs(theta_1 - theta_2) % 360.0
    return min(diff, 360.0 - diff)


PRODUCTION_NUM_SECTORS: int = 8


class AngularSectorDiscretization:
    """Configurable angular quantization scheme supporting dyadic nested partitions K in {2, 4, 8, 16}."""
    def __init__(self, num_sectors: int = PRODUCTION_NUM_SECTORS):
        self.num_sectors = num_sectors
        if num_sectors == 3:
            self.bounds = [(-180.0, -30.0), (-30.0, 30.0), (30.0, 180.0)]
        elif num_sectors == 5:
            self.bounds = [
                (-180.0, -90.0),   # Left Flank
                (-90.0, -15.0),    # Left Forward
                (-15.0, 15.0),     # Center
                (15.0, 90.0),      # Right Forward
                (90.0, 180.0),     # Right Flank
            ]
        else:
            # Equal-width dyadic partitioning (e.g. K = 2, 4, 8, 16)
            step = 360.0 / num_sectors
            self.bounds = [(-180.0 + i * step, -180.0 + (i + 1) * step) for i in range(num_sectors)]

    def get_sector(self, angle_deg: float) -> int:
        norm = ((angle_deg + 180.0) % 360.0) - 180.0
        for idx, (low, high) in enumerate(self.bounds):
            if low <= norm <= high or (idx == self.num_sectors - 1 and norm == 180.0):
                return idx
        return 0

    def max_transition_setup_s(self, sec_a: int, sec_b: int, player: PlayerModel) -> float:
        """Conservative upper bound on setup time between two angular sectors:
        s_ab^max = t_acquire + max_{theta in S_a, phi in S_b} delta_circ(theta, phi) / omega_aim
        """
        if sec_a == sec_b:
            low, high = self.bounds[sec_a]
            max_diff = high - low
            return player.acquisition_latency_s + (max_diff / player.aim_velocity_deg_s)
        
        low_a, high_a = self.bounds[sec_a]
        low_b, high_b = self.bounds[sec_b]
        
        candidates = []
        for th in [low_a, high_a]:
            for ph in [low_b, high_b]:
                candidates.append(circular_angular_distance_deg(th, ph))
        max_circ_diff = max(candidates)
        return player.acquisition_latency_s + (max_circ_diff / player.aim_velocity_deg_s)

    def max_transition_slew_s(self, sec_a: int, sec_b: int, player: PlayerModel) -> float:
        """Compute worst-case angular slew rotation duration between two sectors."""
        if sec_a == sec_b:
            low, high = self.bounds[sec_a]
            max_diff = high - low
            return max_diff / player.aim_velocity_deg_s
        low_a, high_a = self.bounds[sec_a]
        low_b, high_b = self.bounds[sec_b]
        candidates = []
        for th in [low_a, high_a]:
            for ph in [low_b, high_b]:
                candidates.append(circular_angular_distance_deg(th, ph))
        max_circ_diff = max(candidates)
        return max_circ_diff / player.aim_velocity_deg_s



@dataclass
class UpperArrivalCurve:
    """Real-Time Calculus Upper Arrival Curve: α+(Δ) = sup_t N[t, t + Δ]."""
    release_times_s: List[float]

    def evaluate(self, delta_s: float) -> int:
        """Compute max number of events in any window of duration delta_s."""
        if not self.release_times_s:
            return 0
        times = sorted(self.release_times_s)
        max_count = 0
        for i, t_start in enumerate(times):
            t_end = t_start + delta_s
            count = sum(1 for t in times if t_start <= t <= t_end + 1e-9)
            max_count = max(max_count, count)
        return max_count

    def is_equivalent(self, other: "UpperArrivalCurve", tol: float = 1e-4) -> bool:
        """Test exact equality α_1+(Δ) == α_2+(Δ) across all continuous Δ >= 0."""
        r1 = sorted(self.release_times_s)
        r2 = sorted(other.release_times_s)
        if len(r1) != len(r2):
            return False
        # If the sorted release multisets are identical within tolerance, the curves are identical for all Δ
        return all(abs(a - b) <= tol for a, b in zip(r1, r2))


@dataclass
class ScalarSchedulabilitySignature:
    """Scalar interface signature Σ(p) = (α+, σ_min, Θ_max, K_ICI_max)."""
    arrival_curve: UpperArrivalCurve
    min_slack_s: float
    max_setup_s: float
    k_ici_max: int
    threat_count: int


@dataclass
class ThreatJob:
    """Individual threat job in a scheduling instance."""
    id: str
    release_s: float
    deadline_s: float
    service_s: float
    angle_deg: float
    sector: int


@dataclass
class StateConditionedDBF:
    """State-Conditioned Demand Bound Matrix DBF_p(Δ) = [dbf_ab(Δ)]_KxK.
    
    Each entry dbf_ab(Δ) represents the worst-case deadline-relevant service demand
    incurred over any time window of length Δ, conditional on entering with aim in sector 'a'
    and leaving with aim in sector 'b'.
    """
    discretization: AngularSectorDiscretization
    delta_grid: List[float]
    # table: matrix_table[a][b] -> List[float] of dbf values matching delta_grid
    matrix_table: Dict[Tuple[int, int], List[float]]
    min_slack_s: float
    k_ici_max: int

    @classmethod
    def from_jobs(
        cls,
        jobs: List[ThreatJob],
        discretization: AngularSectorDiscretization,
        player: PlayerModel,
        delta_grid: Optional[List[float]] = None
    ) -> "StateConditionedDBF":
        import itertools
        if delta_grid is None:
            delta_grid = [round(x, 3) for x in np.arange(0.0, 6.05, 0.05)]

        K = discretization.num_sectors
        matrix_table = {}

        for a in range(K):
            for b in range(K):
                demands = []
                for delta in delta_grid:
                    if delta == 0.0:
                        demands.append(0.0)
                        continue

                    # Search over all interval start times t in the job release set
                    max_demand = 0.0
                    if not jobs:
                        demands.append(0.0)
                        continue

                    # Potential interval start timestamps
                    t_candidates = [0.0] + [j.release_s for j in jobs]
                    for t in t_candidates:
                        # Active jobs with r_j >= t and D_j <= t + delta
                        active = [j for j in jobs if j.release_s >= t - 1e-9 and j.deadline_s <= t + delta + 1e-9]
                        if not active:
                            cost = 0.0
                        else:
                            # Solve minimal Hamiltonian path over active jobs from sector a to b
                            min_cost = float('inf')
                            for p_order in itertools.permutations(active):
                                cur_cost = discretization.max_transition_setup_s(a, p_order[0].sector, player)
                                cur_cost += p_order[0].service_s
                                for idx in range(1, len(p_order)):
                                    cur_cost += discretization.max_transition_setup_s(p_order[idx-1].sector, p_order[idx].sector, player)
                                    cur_cost += p_order[idx].service_s
                                cur_cost += discretization.max_transition_setup_s(p_order[-1].sector, b, player)
                                min_cost = min(min_cost, cur_cost)
                            cost = min_cost
                        max_demand = max(max_demand, cost)
                    demands.append(max_demand)
                matrix_table[(a, b)] = demands

        min_slack = min((j.deadline_s - j.release_s - j.service_s) for j in jobs) if jobs else 1.0
        return cls(
            discretization=discretization,
            delta_grid=delta_grid,
            matrix_table=matrix_table,
            min_slack_s=min_slack,
            k_ici_max=len(jobs)
        )

    def get_demand(self, sec_a: int, sec_b: int, delta_s: float) -> float:
        """Evaluate dbf_ab(delta_s) via step-interpolation on the grid."""
        demands = self.matrix_table.get((sec_a, sec_b))
        if not demands:
            return 0.0
        # Find nearest grid index
        idx = int(round(delta_s / 0.05))
        idx = max(0, min(idx, len(self.delta_grid) - 1))
        return demands[idx]

    def is_schedulable(self, entry_sector: int = 1) -> bool:
        """Sound Schedulability Test: check if exists exit sector b such that dbf_ab(Δ) <= Δ for all Δ."""
        K = self.discretization.num_sectors
        for b in range(K):
            feasible = True
            for idx, delta in enumerate(self.delta_grid):
                if delta > 0.0:
                    demand = self.matrix_table[(entry_sector, b)][idx]
                    if demand > delta + 1e-6:
                        feasible = False
                        break
            if feasible:
                return True
        return False


def compose_state_conditioned_dbfs(
    dbf_a: StateConditionedDBF,
    dbf_b: StateConditionedDBF
) -> StateConditionedDBF:
    """Compose two Demand Bound Interfaces via inf-sup convolution:
    
    (DBF_A ⊗ DBF_B)_ac(Δ) = min_b ( sup_{0 <= τ <= Δ} [ dbf_A,ab(τ) + dbf_B,bc(Δ - τ) ] )
    """
    K = dbf_a.discretization.num_sectors
    delta_grid = dbf_a.delta_grid
    composed_table = {}

    for a in range(K):
        for c in range(K):
            demands = []
            for delta in delta_grid:
                if delta == 0.0:
                    demands.append(0.0)
                    continue

                min_over_intermediate = float('inf')
                for b in range(K):
                    # Compute sup over time split tau in [0, delta]
                    max_over_tau = 0.0
                    for tau in delta_grid:
                        if tau <= delta + 1e-9:
                            rem = round(delta - tau, 3)
                            d_a = dbf_a.get_demand(a, b, tau)
                            d_b = dbf_b.get_demand(b, c, rem)
                            max_over_tau = max(max_over_tau, d_a + d_b)
                    min_over_intermediate = min(min_over_intermediate, max_over_tau)
                demands.append(min_over_intermediate)
            composed_table[(a, c)] = demands

    return StateConditionedDBF(
        discretization=dbf_a.discretization,
        delta_grid=delta_grid,
        matrix_table=composed_table,
        min_slack_s=min(dbf_a.min_slack_s, dbf_b.min_slack_s),
        k_ici_max=dbf_a.k_ici_max + dbf_b.k_ici_max
    )


def verify_dbf_composition_associativity(
    dbf1: StateConditionedDBF,
    dbf2: StateConditionedDBF,
    dbf3: StateConditionedDBF,
    tol: float = 1e-4
) -> bool:
    """Verify algebraic associativity of DBF composition: (D1 ⊗ D2) ⊗ D3 == D1 ⊗ (D2 ⊗ D3)."""
    left = compose_state_conditioned_dbfs(compose_state_conditioned_dbfs(dbf1, dbf2), dbf3)
    right = compose_state_conditioned_dbfs(dbf1, compose_state_conditioned_dbfs(dbf2, dbf3))

    K = dbf1.discretization.num_sectors
    for a in range(K):
        for d in range(K):
            t_left = left.matrix_table[(a, d)]
            t_right = right.matrix_table[(a, d)]
            for v1, v2 in zip(t_left, t_right):
                if abs(v1 - v2) > tol:
                    return False
    return True


# Backward-compatible StateConditionedInterface aliases for Round 4 fixtures
@dataclass
class StateConditionedInterface:
    demand_matrix: Dict[Tuple[AimSector, AimSector], float]
    min_slack_s: float
    k_ici_max: int

    @classmethod
    def from_dense_matrix(
        cls,
        matrix_3x3: List[List[float]],
        min_slack_s: float,
        k_ici_max: int
    ) -> "StateConditionedInterface":
        d = {}
        sectors = [AimSector.LEFT, AimSector.CENTER, AimSector.RIGHT]
        for i, a in enumerate(sectors):
            for j, b in enumerate(sectors):
                d[(a, b)] = matrix_3x3[i][j]
        return cls(demand_matrix=d, min_slack_s=min_slack_s, k_ici_max=k_ici_max)

    def get_demand(self, a: AimSector, b: AimSector) -> float:
        return self.demand_matrix.get((a, b), float('inf'))


def compose_state_conditioned_interfaces(
    i_a: StateConditionedInterface,
    i_b: StateConditionedInterface
) -> StateConditionedInterface:
    sectors = [AimSector.LEFT, AimSector.CENTER, AimSector.RIGHT]
    composed_matrix = {}

    for a in sectors:
        for c in sectors:
            min_cost = float('inf')
            for b in sectors:
                cost = i_a.get_demand(a, b) + i_b.get_demand(b, c)
                min_cost = min(min_cost, cost)
            composed_matrix[(a, c)] = min_cost

    return StateConditionedInterface(
        demand_matrix=composed_matrix,
        min_slack_s=min(i_a.min_slack_s, i_b.min_slack_s),
        k_ici_max=max(i_a.k_ici_max, i_b.k_ici_max)
    )


def verify_interface_composition_associativity(
    i1: StateConditionedInterface,
    i2: StateConditionedInterface,
    i3: StateConditionedInterface,
    tol: float = 1e-9
) -> bool:
    left = compose_state_conditioned_interfaces(compose_state_conditioned_interfaces(i1, i2), i3)
    right = compose_state_conditioned_interfaces(i1, compose_state_conditioned_interfaces(i2, i3))

    sectors = [AimSector.LEFT, AimSector.CENTER, AimSector.RIGHT]
    for a in sectors:
        for c in sectors:
            v_left = left.get_demand(a, c)
            v_right = right.get_demand(a, c)
            if abs(v_left - v_right) > tol:
                return False
    return True


# =============================================================================
# ROUND 6: EXACT FEASIBLE TRANSFER RELATION R_M & RELATIONAL COMPOSITION
# =============================================================================

@dataclass
class ExactTransferMap:
    """Exact Feasible Transfer Map T_M(a, b, t_in) -> t_out.
    
    Represents the exact relation R_M subseteq (S x R) x (S x R).
    T_M(a, b, t_in) gives the minimum exit timestamp from module M in aim sector b
    given entry at timestamp t_in in aim sector a, subject to all internal jobs meeting deadlines.
    If no valid non-preemptive schedule meets all deadlines, returns +inf (infeasible).
    """
    discretization: AngularSectorDiscretization
    jobs: List[ThreatJob]
    player: PlayerModel

    def evaluate(
        self,
        sec_a: int,
        sec_b: int,
        t_in: float = 0.0,
        regime: InformationRegime = InformationRegime.REVEAL_GATED
    ) -> float:
        """Compute exact infimum exit time t_out >= t_in via non-preemptive branch/permutation search."""
        if not self.jobs:
            slew = self.discretization.max_transition_slew_s(sec_a, sec_b, self.player)
            return t_in + slew

        import itertools
        best_t_out = float('inf')
        
        for perm in itertools.permutations(self.jobs):
            cur_time = t_in
            cur_sec = sec_a
            feasible = True
            
            for job in perm:
                slew = self.discretization.max_transition_slew_s(cur_sec, job.sector, self.player)
                acq = self.player.acquisition_latency_s
                if regime == InformationRegime.REVEAL_GATED:
                    start_time = max(cur_time, job.release_s) + slew + acq
                else:  # PRE_AIM
                    start_time = max(job.release_s, cur_time + slew) + acq
                finish_time = start_time + job.service_s
                
                if finish_time > job.deadline_s + 1e-9:
                    feasible = False
                    break
                
                cur_time = finish_time
                cur_sec = job.sector
                
            if feasible:
                final_slew = self.discretization.max_transition_slew_s(cur_sec, sec_b, self.player)
                exit_time = cur_time + final_slew
                best_t_out = min(best_t_out, exit_time)
                
        return best_t_out

    def is_feasible_from(self, entry_sector: int, t_in: float = 0.0) -> bool:
        """Test whether there exists at least one exit sector b with finite exit time from entry_sector."""
        for b in range(self.discretization.num_sectors):
            if self.evaluate(entry_sector, b, t_in) < float('inf'):
                return True
        return False

    def is_feasible_from_any_reset_state(self, t_in: float = 0.0) -> bool:
        """Test whether there exists ANY (a, b) pair with finite exit time (quiescent reset interface)."""
        K = self.discretization.num_sectors
        for a in range(K):
            for b in range(K):
                if self.evaluate(a, b, t_in) < float('inf'):
                    return True
        return False

    def is_feasible(self, entry_sector: Optional[int] = None, t_in: float = 0.0) -> bool:
        """Check feasibility: if entry_sector given, tests from that sector; otherwise tests from any reset state."""
        if entry_sector is not None:
            return self.is_feasible_from(entry_sector, t_in)
        return self.is_feasible_from_any_reset_state(t_in)


@dataclass
class CompositeTransferMap:
    """Composite Transfer Map representing relational composition R_A o R_B."""
    map_a: Any
    map_b: Any
    
    @property
    def discretization(self) -> AngularSectorDiscretization:
        return self.map_a.discretization

    def evaluate(self, sec_a: int, sec_c: int, t_in: float) -> float:
        K = self.discretization.num_sectors
        best_t_out = float('inf')
        for b in range(K):
            t_mid = self.map_a.evaluate(sec_a, b, t_in)
            if t_mid < float('inf'):
                t_exit = self.map_b.evaluate(b, sec_c, t_mid)
                best_t_out = min(best_t_out, t_exit)
        return best_t_out

    def is_feasible_from(self, entry_sector: int, t_in: float = 0.0) -> bool:
        for c in range(self.discretization.num_sectors):
            if self.evaluate(entry_sector, c, t_in) < float('inf'):
                return True
        return False

    def is_feasible_from_any_reset_state(self, t_in: float = 0.0) -> bool:
        K = self.discretization.num_sectors
        for a in range(K):
            for c in range(K):
                if self.evaluate(a, c, t_in) < float('inf'):
                    return True
        return False

    def is_feasible(self, entry_sector: Optional[int] = None, t_in: float = 0.0) -> bool:
        if entry_sector is not None:
            return self.is_feasible_from(entry_sector, t_in)
        return self.is_feasible_from_any_reset_state(t_in)


def compose_exact_transfer_maps(map_a: Any, map_b: Any) -> CompositeTransferMap:
    """Exact Relational Composition: (T_A o T_B)(a, c, t_in) = min_b T_B(b, c, T_A(a, b, t_in))."""
    return CompositeTransferMap(map_a, map_b)


def verify_transfer_map_associativity(
    map_a: Any,
    map_b: Any,
    map_c: Any,
    t_in: float = 0.0,
    tol: float = 1e-4
) -> bool:
    """Verify exact algebraic associativity: (T_A o T_B) o T_C == T_A o (T_B o T_C)."""
    comp_ab_c = compose_exact_transfer_maps(compose_exact_transfer_maps(map_a, map_b), map_c)
    comp_a_bc = compose_exact_transfer_maps(map_a, compose_exact_transfer_maps(map_b, map_c))
    
    K = map_a.discretization.num_sectors
    for a in range(K):
        for d in range(K):
            t1 = comp_ab_c.evaluate(a, d, t_in)
            t2 = comp_a_bc.evaluate(a, d, t_in)
            if abs(t1 - t2) > tol and not (t1 == float('inf') and t2 == float('inf')):
                return False
    return True


def demonstrate_infsup_nondistributivity() -> Dict[str, Any]:
    """Algebraic demonstration of why max-plus time convolution does not distribute over min-plus state choice.
    
    For f = [0, 1, 1], g = [0, 0, 2], h = [0, 1, 1] at Delta = 2:
    (f * min(g, h))(2) = 1 != min(f * g, f * h)(2) = 2.
    """
    f = [0, 1, 1]
    g = [0, 0, 2]
    h = [0, 1, 1]
    m = [min(g[i], h[i]) for i in range(3)]  # [0, 0, 1]
    
    # (f * m)(2) = sup_{tau in {0, 1, 2}} [f[tau] + m[2 - tau]]
    f_star_m_2 = max(f[0] + m[2], f[1] + m[1], f[2] + m[0])  # max(0+1, 1+0, 1+0) = 1
    
    # (f * g)(2)
    f_star_g_2 = max(f[0] + g[2], f[1] + g[1], f[2] + g[0])  # max(0+2, 1+0, 1+0) = 2
    # (f * h)(2)
    f_star_h_2 = max(f[0] + h[2], f[1] + h[1], f[2] + h[0])  # max(0+1, 1+1, 1+0) = 2
    min_f_star_g_h_2 = min(f_star_g_2, f_star_h_2)           # min(2, 2) = 2
    
    return {
        "f_star_min_gh": f_star_m_2,
        "min_f_star_g_f_star_h": min_f_star_g_h_2,
        "is_equal": f_star_m_2 == min_f_star_g_h_2
    }


# =============================================================================
# ROUND 7: SPATIAL PORT-TO-PORT TRANSFER SEMANTICS & FLATTENING EQUIVALENCE
# =============================================================================

@dataclass
class SpatialThreatJob:
    """Threat job with module-local revelation offset and due window.
    
    Attributes:
        id: Unique threat identifier.
        offset_s: Local revelation offset rho_j relative to entering port p_in (seconds).
        due_window_s: Damage due window d_j (seconds), so D_j(t_in) = t_in + offset_s + due_window_s.
        service_s: Inspection dwell processing duration p_j (seconds).
        angle_deg: Angular bearing from entrance/trajectory (degrees).
        sector: Discretized angular sector.
    """
    id: str
    offset_s: float
    due_window_s: float
    service_s: float
    angle_deg: float
    sector: int


@dataclass
class SpatialRoute:
    """A candidate local movement trajectory gamma from p_in to p_out."""
    route_id: str
    traversal_duration_s: float
    jobs: List[SpatialThreatJob] = field(default_factory=list)


@dataclass
class SpatialModuleTransferMap:
    """Spatial Port-to-Port Transfer Map T_M(p_in, a, p_out, b, t_in).
    
    Answers: How soon can a player enter through p_in with aim state a, traverse M,
    clear all local threats within hard deadlines along the optimal route gamma,
    and exit through p_out with aim state b?
    
    Optimization:
        T_M(p_in, a, p_out, b, t_in) = inf_{gamma in Gamma} inf_{pi in Pi_feas(gamma)} t_exit
    
    Due to Time-Translation Invariance:
        T_M(p_in, a, p_out, b, t_in + delta) = T_M(p_in, a, p_out, b, t_in) + delta
    The evaluation reduces to a static duration matrix:
        T_M(p_in, a, p_out, b, t_in) = t_in + Delta T_M(a, b)
    """
    module_id: str
    entry_port: str
    exit_port: str
    discretization: AngularSectorDiscretization
    player: PlayerModel
    routes: List[SpatialRoute] = field(default_factory=list)
    traversal_duration_s: float = 0.0
    jobs: List[SpatialThreatJob] = field(default_factory=list)
    _duration_matrices: Dict[InformationRegime, Dict[Tuple[int, int], float]] = field(default_factory=dict)
    _duration_matrix: Optional[Dict[Tuple[int, int], float]] = None

    def __post_init__(self):
        if not self.routes:
            self.routes = [SpatialRoute(
                route_id="default_route",
                traversal_duration_s=self.traversal_duration_s,
                jobs=self.jobs
            )]
        if self._duration_matrix is not None and not self._duration_matrices:
            self._duration_matrices[InformationRegime.REVEAL_GATED] = self._duration_matrix
            self._duration_matrices[InformationRegime.PRE_AIM] = self._duration_matrix
        elif not self._duration_matrices:
            self._duration_matrices[InformationRegime.REVEAL_GATED] = self._compute_duration_matrix(InformationRegime.REVEAL_GATED)
            self._duration_matrices[InformationRegime.PRE_AIM] = self._compute_duration_matrix(InformationRegime.PRE_AIM)
        self._duration_matrix = self._duration_matrices[InformationRegime.REVEAL_GATED]

    def _compute_duration_matrix(
        self,
        regime: InformationRegime = InformationRegime.REVEAL_GATED
    ) -> Dict[Tuple[int, int], float]:
        """Compute the static relative duration matrix Delta T_M(a, b) = min_{gamma} Delta T_{M, gamma}(a, b)."""
        import itertools
        K = self.discretization.num_sectors
        mat = {}

        for a in range(K):
            for b in range(K):
                best_duration = float('inf')

                for route in self.routes:
                    if not route.jobs:
                        slew = self.discretization.max_transition_slew_s(a, b, self.player)
                        route_dur = max(route.traversal_duration_s, slew)
                        best_duration = min(best_duration, route_dur)
                        continue

                    for perm in itertools.permutations(route.jobs):
                        cur_t = 0.0
                        cur_sec = a
                        feasible = True

                        for job in perm:
                            slew = self.discretization.max_transition_slew_s(cur_sec, job.sector, self.player)
                            acq = self.player.acquisition_latency_s
                            if regime == InformationRegime.REVEAL_GATED:
                                start_time = max(cur_t, job.offset_s) + slew + acq
                            else:  # PRE_AIM
                                start_time = max(job.offset_s, cur_t + slew) + acq
                            finish_time = start_time + job.service_s
                            deadline = job.offset_s + job.due_window_s

                            if finish_time > deadline + 1e-9:
                                feasible = False
                                break

                            cur_t = finish_time
                            cur_sec = job.sector

                        if feasible:
                            final_slew = self.discretization.max_transition_slew_s(cur_sec, b, self.player)
                            exit_t = max(route.traversal_duration_s, cur_t + final_slew)
                            best_duration = min(best_duration, exit_t)

                mat[(a, b)] = best_duration

        return mat

    def get_duration(
        self,
        sec_a: int,
        sec_b: int,
        regime: InformationRegime = InformationRegime.REVEAL_GATED
    ) -> float:
        """Get the static duration Delta T_M(a, b) under the specified information regime."""
        mat = self._duration_matrices.get(regime)
        if mat is None:
            mat = self._compute_duration_matrix(regime)
            self._duration_matrices[regime] = mat
        return mat.get((sec_a, sec_b), float('inf'))

    def evaluate(
        self,
        sec_a: int,
        sec_b: int,
        t_in: float = 0.0,
        regime: InformationRegime = InformationRegime.REVEAL_GATED
    ) -> float:
        """Evaluate exact exit timestamp: T_M(p_in, a, p_out, b, t_in) = t_in + Delta T_M(a, b)."""
        dur = self.get_duration(sec_a, sec_b, regime=regime)
        if dur == float('inf'):
            return float('inf')
        return t_in + dur

    def is_feasible_from(
        self,
        sec_a: int,
        regime: InformationRegime = InformationRegime.REVEAL_GATED
    ) -> bool:
        """Check if any exit sector provides a deadline-feasible traversal from entry sector sec_a."""
        for b in range(self.discretization.num_sectors):
            if self.get_duration(sec_a, b, regime=regime) < float('inf'):
                return True
        return False

    def is_feasible_from_any_reset_state(
        self,
        regime: InformationRegime = InformationRegime.REVEAL_GATED
    ) -> bool:
        """Test whether there exists ANY (a, b) pair with finite exit time (quiescent reset interface)."""
        K = self.discretization.num_sectors
        for a in range(K):
            for b in range(K):
                if self.get_duration(a, b, regime=regime) < float('inf'):
                    return True
        return False

    def is_feasible(self, sec_a: Optional[int] = None, entry_sector: Optional[int] = None) -> bool:
        """Check feasibility: if sec_a/entry_sector provided, evaluates from that sector; otherwise checks any reset state."""
        target_a = sec_a if sec_a is not None else entry_sector
        if target_a is not None:
            return self.is_feasible_from(target_a)
        return self.is_feasible_from_any_reset_state()


@dataclass
class CompositeSpatialTransferMap:
    """Composed Spatial Transfer Map representing M_1 o M_2."""
    map_1: Any
    map_2: Any

    @property
    def discretization(self) -> AngularSectorDiscretization:
        return self.map_1.discretization

    @property
    def entry_port(self) -> str:
        return self.map_1.entry_port

    @property
    def exit_port(self) -> str:
        return self.map_2.exit_port

    @property
    def traversal_duration_s(self) -> float:
        return self.map_1.traversal_duration_s + self.map_2.traversal_duration_s

    def get_duration(self, sec_a: int, sec_c: int) -> float:
        K = self.discretization.num_sectors
        best_dur = float('inf')
        for b in range(K):
            dur1 = self.map_1.get_duration(sec_a, b)
            if dur1 < float('inf'):
                dur2 = self.map_2.get_duration(b, sec_c)
                best_dur = min(best_dur, dur1 + dur2)
        return best_dur

    def evaluate(self, sec_a: int, sec_c: int, t_in: float) -> float:
        dur = self.get_duration(sec_a, sec_c)
        if dur == float('inf'):
            return float('inf')
        return t_in + dur

    def is_feasible_from(self, sec_a: int) -> bool:
        for c in range(self.discretization.num_sectors):
            if self.get_duration(sec_a, c) < float('inf'):
                return True
        return False

    def is_feasible_from_any_reset_state(self) -> bool:
        K = self.discretization.num_sectors
        for a in range(K):
            for c in range(K):
                if self.get_duration(a, c) < float('inf'):
                    return True
        return False

    def is_feasible(self, sec_a: Optional[int] = None, entry_sector: Optional[int] = None) -> bool:
        target_a = sec_a if sec_a is not None else entry_sector
        if target_a is not None:
            return self.is_feasible_from(target_a)
        return self.is_feasible_from_any_reset_state()


def compose_spatial_transfer_maps(m1: Any, m2: Any) -> CompositeSpatialTransferMap:
    """Exact Relational Spatial Composition: T_{1 o 2}(a, c, t_in) = min_b T_2(b, c, T_1(a, b, t_in))."""
    return CompositeSpatialTransferMap(m1, m2)


def verify_spatial_transfer_map_associativity(
    m1: Any,
    m2: Any,
    m3: Any,
    tol: float = 1e-4
) -> bool:
    """Verify algebraic associativity of spatial transfer maps: (M1 o M2) o M3 == M1 o (M2 o M3)."""
    comp_12_3 = compose_spatial_transfer_maps(compose_spatial_transfer_maps(m1, m2), m3)
    comp_1_23 = compose_spatial_transfer_maps(m1, compose_spatial_transfer_maps(m2, m3))

    K = m1.discretization.num_sectors
    for a in range(K):
        for d in range(K):
            d1 = comp_12_3.get_duration(a, d)
            d2 = comp_1_23.get_duration(a, d)
            if abs(d1 - d2) > tol and not (d1 == float('inf') and d2 == float('inf')):
                return False
    return True


def solve_monolithic_module_chain_dp(
    modules: List[SpatialModuleTransferMap],
    entry_sector: int,
    exit_sector: int,
    t_in: float = 0.0
) -> float:
    """Exact Dynamic Programming Oracle for Monolithic Multi-Module Chains."""
    if not modules:
        return t_in
    K = modules[0].discretization.num_sectors

    # dp[sector] = min duration to reach current portal in given sector
    dp = {s: float('inf') for s in range(K)}
    dp[entry_sector] = 0.0

    for mod in modules:
        next_dp = {s: float('inf') for s in range(K)}
        for s_in in range(K):
            if dp[s_in] == float('inf'):
                continue
            for s_out in range(K):
                dur = mod.get_duration(s_in, s_out)
                if dur < float('inf'):
                    next_dp[s_out] = min(next_dp[s_out], dp[s_in] + dur)
        dp = next_dp

    if dp[exit_sector] == float('inf'):
        return float('inf')
    return t_in + dp[exit_sector]


def flatten_spatial_module_chain(modules: List[SpatialModuleTransferMap]) -> SpatialModuleTransferMap:
    """Monolithic Flattening Oracle: Flatten a sequence of modules into a single global module."""
    assert len(modules) > 0
    first = modules[0]
    last = modules[-1]
    disc = first.discretization
    player = first.player
    K = disc.num_sectors

    # Compute duration matrix via monolithic multi-module DP
    dur_mat = {}
    for a in range(K):
        for z in range(K):
            dur_mat[(a, z)] = solve_monolithic_module_chain_dp(modules, a, z, 0.0)

    total_traversal = sum(m.traversal_duration_s for m in modules)

    return SpatialModuleTransferMap(
        module_id="flattened_chain",
        entry_port=first.entry_port,
        exit_port=last.exit_port,
        traversal_duration_s=total_traversal,
        discretization=disc,
        jobs=[],
        player=player,
        _duration_matrix=dur_mat
    )


def compute_flattened_spatial_chain_exit_time(
    module_candidate_routes: List[List[SpatialRoute]],
    discretization: AngularSectorDiscretization,
    player: PlayerModel,
    entry_sector: int,
    exit_sector: int,
    t_in: float = 0.0,
    regime: InformationRegime = InformationRegime.REVEAL_GATED
) -> float:
    """Genuinely Independent Raw-Chain Non-Preemptive Scheduling Oracle.
    
    Evaluates multi-room transfer directly from raw SpatialRoutes and SpatialThreatJobs
    WITHOUT constructing or consulting any SpatialModuleTransferMap duration matrices.
    
    For every stage k, candidate routes Gamma_k are evaluated from raw jobs by exhaustively
    searching all non-preemptive job schedules directly.
    """
    import itertools
    K = discretization.num_sectors

    # dp[sector] = earliest time to arrive at current portal in that sector
    dp = {s: float('inf') for s in range(K)}
    dp[entry_sector] = t_in

    for stage_routes in module_candidate_routes:
        next_dp = {s: float('inf') for s in range(K)}
        for route in stage_routes:
            for s_in in range(K):
                if dp[s_in] == float('inf'):
                    continue
                cur_stage_t = dp[s_in]
                for s_out in range(K):
                    if not route.jobs:
                        slew = discretization.max_transition_slew_s(s_in, s_out, player)
                        dur = max(route.traversal_duration_s, slew)
                        next_dp[s_out] = min(next_dp[s_out], cur_stage_t + dur)
                    else:
                        best_exit_t = float('inf')
                        for perm in itertools.permutations(route.jobs):
                            cur_t = cur_stage_t
                            cur_sec = s_in
                            feasible = True

                            for job in perm:
                                slew = discretization.max_transition_slew_s(cur_sec, job.sector, player)
                                acq = player.acquisition_latency_s
                                rel_release = cur_stage_t + job.offset_s
                                rel_deadline = rel_release + job.due_window_s
                                if regime == InformationRegime.REVEAL_GATED:
                                    start_time = max(cur_t, rel_release) + slew + acq
                                else:  # PRE_AIM
                                    start_time = max(rel_release, cur_t + slew) + acq
                                finish_time = start_time + job.service_s

                                if finish_time > rel_deadline + 1e-9:
                                    feasible = False
                                    break

                                cur_t = finish_time
                                cur_sec = job.sector

                            if feasible:
                                final_slew = discretization.max_transition_slew_s(cur_sec, s_out, player)
                                exit_t = max(cur_stage_t + route.traversal_duration_s, cur_t + final_slew)
                                best_exit_t = min(best_exit_t, exit_t)

                        if best_exit_t < float('inf'):
                            next_dp[s_out] = min(next_dp[s_out], best_exit_t)
        dp = next_dp

    return dp[exit_sector]


solve_raw_spatial_chain = compute_flattened_spatial_chain_exit_time



@dataclass
class ContinuousAngleTransferMap:
    """Continuous-Angle Ground Truth Reference Oracle (K = infinity).
    
    Evaluates the exact transfer duration matrix using true continuous threat angles theta_j,
    where exact aiming transition slew is q(theta_1, theta_2) = delta_circ(theta_1, theta_2) / omega_aim.
    Serves as the empirical asymptotic benchmark to measure conservatism of dyadic sector discretizations K in {2, 4, 8, 16}.
    """
    traversal_duration_s: float
    jobs: List[SpatialThreatJob]
    player: PlayerModel

    def evaluate_exact_continuous_duration(
        self,
        initial_aim_deg: float,
        final_aim_deg: float,
        regime: InformationRegime = InformationRegime.REVEAL_GATED
    ) -> float:
        """Compute the true continuous-angle minimum transfer duration."""
        if not self.jobs:
            diff = circular_angular_distance_deg(initial_aim_deg, final_aim_deg)
            slew = diff / max(self.player.aim_velocity_deg_s, 1e-3)
            return max(self.traversal_duration_s, slew)

        import itertools
        best_duration = float('inf')

        for perm in itertools.permutations(self.jobs):
            cur_t = 0.0
            cur_angle = initial_aim_deg
            feasible = True

            for job in perm:
                diff = circular_angular_distance_deg(cur_angle, job.angle_deg)
                slew = diff / max(self.player.aim_velocity_deg_s, 1e-3)
                acq = self.player.acquisition_latency_s
                if regime == InformationRegime.REVEAL_GATED:
                    start_time = max(cur_t, job.offset_s) + slew + acq
                else:  # PRE_AIM
                    start_time = max(job.offset_s, cur_t + slew) + acq
                finish_time = start_time + job.service_s
                deadline = job.offset_s + job.due_window_s

                if finish_time > deadline + 1e-9:
                    feasible = False
                    break

                cur_t = finish_time
                cur_angle = job.angle_deg

            if feasible:
                diff_final = circular_angular_distance_deg(cur_angle, final_aim_deg)
                final_slew = diff_final / max(self.player.aim_velocity_deg_s, 1e-3)
                exit_t = max(self.traversal_duration_s, cur_t + final_slew)
                best_duration = min(best_duration, exit_t)

        return best_duration




