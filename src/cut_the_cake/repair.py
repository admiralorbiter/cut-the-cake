"""Inverse Tactical Repair & Automated Level Linter [G -> G*].

Provides:
- TacticalDiagnostic: Isolates critical threat bottlenecks, deadline deficits, and controlling occluder edges.
- VectorizedRaycaster: Fast flat-array 2D segment intersection engine using NumPy coordinate broadcasting.
- MinimalRepairOptimizer: Inverse design solver finding G* = argmin d(G, G') s.t. M(G') >= epsilon and ValidTopology(G').
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any
import numpy as np
from shapely.geometry import Polygon, LineString, Point
from shapely.affinity import translate

from .compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricThreat,
    GeometricPort,
    validate_geometry_integrity
)
from .geometry import (
    distance,
    heading_to_deg,
    normalize_angle_deg,
    angle_diff_deg,
    segments_intersect,
    extract_polygon_segments
)
from .vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteScheduleResult,
    DiscreteTicScheduler,
    DeterministicSimulationReferee
)


# =============================================================================
# FAST VECTORIZED FLAT-ARRAY RAYCASTER
# =============================================================================

class VectorizedRaycaster:
    """High-speed flat-array 2D segment intersection engine using NumPy broadcasting."""

    @staticmethod
    def extract_segment_array(obstacles: List[Polygon]) -> np.ndarray:
        """Extract all obstacle polygon segments into a flat float64 array of shape (M, 4)."""
        segs: List[Tuple[float, float, float, float]] = []
        for obs in obstacles:
            coords = list(obs.exterior.coords)
            for i in range(len(coords) - 1):
                segs.append((coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1]))
            for interior in obs.interiors:
                icoords = list(interior.coords)
                for i in range(len(icoords) - 1):
                    segs.append((icoords[i][0], icoords[i][1], icoords[i + 1][0], icoords[i + 1][1]))
        if not segs:
            return np.empty((0, 4), dtype=np.float64)
        return np.array(segs, dtype=np.float64)

    @staticmethod
    def is_los_blocked_batch(
        points: np.ndarray,  # Shape (N, 2)
        target: Tuple[float, float],  # (qx, qy)
        obstacle_segs: np.ndarray  # Shape (M, 4) -> [x3, y3, x4, y4]
    ) -> np.ndarray:  # Returns bool array of shape (N,)
        """Evaluate line-of-sight blockage from N observer points to target anchor against M obstacle segments."""
        n_pts = len(points)
        if n_pts == 0 or len(obstacle_segs) == 0:
            return np.zeros(n_pts, dtype=bool)

        qx, qy = target
        # p1: points (N, 2) -> x1, y1
        # p2: target (1, 2) -> x2, y2
        x1 = points[:, 0][:, np.newaxis]  # (N, 1)
        y1 = points[:, 1][:, np.newaxis]  # (N, 1)
        x2 = float(qx)
        y2 = float(qy)

        # Obstacle segments (1, M) -> x3, y3, x4, y4
        x3 = obstacle_segs[:, 0][np.newaxis, :]  # (1, M)
        y3 = obstacle_segs[:, 1][np.newaxis, :]  # (1, M)
        x4 = obstacle_segs[:, 2][np.newaxis, :]  # (1, M)
        y4 = obstacle_segs[:, 3][np.newaxis, :]  # (1, M)

        # Bounding box rejection
        min_x12 = np.minimum(x1, x2)
        max_x12 = np.maximum(x1, x2)
        min_y12 = np.minimum(y1, y2)
        max_y12 = np.maximum(y1, y2)

        min_x34 = np.minimum(x3, x4)
        max_x34 = np.maximum(x3, x4)
        min_y34 = np.minimum(y3, y4)
        max_y34 = np.maximum(y3, y4)

        bbox_disjoint = (
            (max_x12 < min_x34) |
            (min_x12 > max_x34) |
            (max_y12 < min_y34) |
            (min_y12 > max_y34)
        )

        # Orientation cross-products
        d1 = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
        d2 = (x4 - x3) * (y2 - y3) - (y4 - y3) * (x2 - x3)
        d3 = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
        d4 = (x2 - x1) * (y4 - y1) - (y2 - y1) * (x4 - x1)

        intersects = (~bbox_disjoint) & ((d1 * d2) < -1e-9) & ((d3 * d4) < -1e-9)
        # Blocked if intersects any obstacle segment
        return np.any(intersects, axis=1)


# =============================================================================
# TACTICAL DIAGNOSTIC (BOTTLENECK ISOLATION)
# =============================================================================

@dataclass
class TacticalDiagnostic:
    """Diagnostic isolation of the critical scheduling bottleneck and controlling geometry."""
    is_serviceable: bool
    initial_margin_tics: int
    target_margin_tics: int
    margin_deficit_tics: int
    critical_threat_id: Optional[str]
    critical_reveal_tic: Optional[int]
    critical_lateness_tics: int
    controlling_obstacle_idx: Optional[int]
    controlling_edge: Optional[Tuple[Tuple[float, float], Tuple[float, float]]]
    suggested_perturbation_normal: Optional[Tuple[float, float]]
    diagnosis_message: str


def diagnose_clearability(
    geo_module: GeometricModule,
    target_margin_tics: int = 2,
    params: Optional[TicCombatParameters] = None,
    route_index: int = 0,
    initial_reticle_deg: float = 0.0
) -> TacticalDiagnostic:
    """Analyze an unserviceable encounter to identify the critical threat and controlling occluder edge."""
    combat_params = params or TicCombatParameters()
    referee = DeterministicSimulationReferee(combat_params)
    scheduler = DiscreteTicScheduler(combat_params)

    jobs = referee.extract_tic_jobs(geo_module, route_index=route_index)
    if not jobs:
        return TacticalDiagnostic(
            is_serviceable=True,
            initial_margin_tics=999,
            target_margin_tics=target_margin_tics,
            margin_deficit_tics=0,
            critical_threat_id=None,
            critical_reveal_tic=None,
            critical_lateness_tics=-999,
            controlling_obstacle_idx=None,
            controlling_edge=None,
            suggested_perturbation_normal=None,
            diagnosis_message="No threats in module; encounter is trivially clearable."
        )

    sched_res = scheduler.solve(jobs, initial_reticle_deg=initial_reticle_deg)
    current_margin = sched_res.tactical_margin_tics
    is_serv = (current_margin >= target_margin_tics)

    if is_serv:
        return TacticalDiagnostic(
            is_serviceable=True,
            initial_margin_tics=current_margin,
            target_margin_tics=target_margin_tics,
            margin_deficit_tics=0,
            critical_threat_id=None,
            critical_reveal_tic=None,
            critical_lateness_tics=-current_margin,
            controlling_obstacle_idx=None,
            controlling_edge=None,
            suggested_perturbation_normal=None,
            diagnosis_message=f"Encounter is serviceable (M = {current_margin} tics >= {target_margin_tics} tics)."
        )

    # Find the critical threat with maximum lateness (or lowest completion margin)
    worst_lateness = -9999
    crit_threat_id = None
    for tid, lat in sched_res.lateness_per_threat.items():
        if lat > worst_lateness:
            worst_lateness = lat
            crit_threat_id = tid

    deficit = target_margin_tics - current_margin
    crit_job = next((j for j in jobs if j.id == crit_threat_id), None)
    crit_reveal_tic = crit_job.reveal_tic if crit_job else None

    # Identify controlling obstacle edge
    route = geo_module.routes[route_index]
    controlling_obs_idx = None
    controlling_edge = None
    suggested_normal = None

    if crit_job is not None and geo_module.obstacles:
        qx, qy = crit_job.threat_anchor
        # Observer position at the tic just before reveal
        reveal_s = crit_job.reveal_tic * combat_params.move_m_per_tic
        pre_reveal_s = max(0.0, reveal_s - combat_params.move_m_per_tic)
        obs_pos = route.position_at_distance(pre_reveal_s)

        # Check which obstacle segment was blocking LOS at pre_reveal_s and nearest to the sightline at reveal
        min_dist_to_ray = float('inf')
        for obs_i, obs in enumerate(geo_module.obstacles):
            segs = extract_polygon_segments([obs])
            for s1, s2 in segs:
                # Infinite ray passing through anchor (qx, qy) and obstacle segment
                if segments_intersect(obs_pos, (qx, qy), s1, s2):
                    controlling_obs_idx = obs_i
                    controlling_edge = (s1, s2)
                    break
            if controlling_obs_idx is not None:
                break

        # If not directly intersected at pre_reveal_s, find nearest obstacle vertex to reveal ray
        if controlling_obs_idx is None:
            rev_pos = route.position_at_distance(reveal_s)
            rev_line = LineString([rev_pos, (qx, qy)])
            for obs_i, obs in enumerate(geo_module.obstacles):
                d = rev_line.distance(obs)
                if d < min_dist_to_ray:
                    min_dist_to_ray = d
                    controlling_obs_idx = obs_i
                    segs = extract_polygon_segments([obs])
                    if segs:
                        controlling_edge = segs[0]

        # Compute suggested perturbation direction: normal to obstacle edge or along route direction
        if controlling_edge is not None:
            (x1, y1), (x2, y2) = controlling_edge
            edx = x2 - x1
            edy = y2 - y1
            length = math.hypot(edx, edy)
            if length > 1e-4:
                # Normal vector (-edy, edx) / length
                nx = -edy / length
                ny = edx / length
                # Orient normal towards route to extend coverage
                mid_x = (x1 + x2) / 2.0
                mid_y = (y1 + y2) / 2.0
                rev_pos = route.position_at_distance(reveal_s)
                to_route_x = rev_pos[0] - mid_x
                to_route_y = rev_pos[1] - mid_y
                if (nx * to_route_x + ny * to_route_y) < 0:
                    nx = -nx
                    ny = -ny
                suggested_normal = (float(nx), float(ny))
            else:
                suggested_normal = (1.0, 0.0)
        else:
            suggested_normal = (1.0, 0.0)

    msg = (
        f"Tactical Deficit: {deficit} tics (Initial M = {current_margin} tics, Target M = {target_margin_tics} tics). "
        f"Critical bottleneck: Threat '{crit_threat_id}' unoccludes at tic {crit_reveal_tic} "
        f"with lateness +{worst_lateness} tics."
    )

    return TacticalDiagnostic(
        is_serviceable=False,
        initial_margin_tics=current_margin,
        target_margin_tics=target_margin_tics,
        margin_deficit_tics=deficit,
        critical_threat_id=crit_threat_id,
        critical_reveal_tic=crit_reveal_tic,
        critical_lateness_tics=worst_lateness,
        controlling_obstacle_idx=controlling_obs_idx,
        controlling_edge=controlling_edge,
        suggested_perturbation_normal=suggested_normal,
        diagnosis_message=msg
    )



# =============================================================================
# STRICT GEOMETRIC PRESERVATION VALIDATOR
# =============================================================================

def validate_repair_preservation(
    orig_module: GeometricModule,
    candidate_module: GeometricModule,
    port_tol_m: float = 0.10
) -> List[str]:
    """Verify that geometric perturbations preserve boundary, topology, routes, threats, and obstacle validity."""
    errors: List[str] = []

    # 1. Boundary preservation
    if not candidate_module.boundary.equals_exact(orig_module.boundary, 1e-4):
        if not candidate_module.boundary.equals(orig_module.boundary):
            errors.append(f"Module boundary modified during repair for {candidate_module.module_id}")

    # 2. Obstacle count and area preservation
    if len(candidate_module.obstacles) != len(orig_module.obstacles):
        errors.append(f"Obstacle count changed from {len(orig_module.obstacles)} to {len(candidate_module.obstacles)}")
    for i, (orig_obs, cand_obs) in enumerate(zip(orig_module.obstacles, candidate_module.obstacles)):
        if not cand_obs.is_valid or cand_obs.is_empty:
            errors.append(f"Candidate obstacle #{i} is geometrically invalid or empty")
        elif abs(cand_obs.area - orig_obs.area) > 1e-3:
            errors.append(f"Candidate obstacle #{i} area changed from {orig_obs.area:.4f} to {cand_obs.area:.4f}")

    # 3. Obstacle containment within floorplan boundary
    for i, obs in enumerate(candidate_module.obstacles):
        if not candidate_module.boundary.buffer(1e-4).contains(obs):
            errors.append(f"Candidate obstacle #{i} extends outside module boundary")

    # 4. Obstacle disjointness (no interior overlap between obstacles)
    for i in range(len(candidate_module.obstacles)):
        for j in range(i + 1, len(candidate_module.obstacles)):
            inter = candidate_module.obstacles[i].intersection(candidate_module.obstacles[j])
            if inter.area > 1e-4:
                errors.append(f"Candidate obstacles #{i} and #{j} overlap (area={inter.area:.4f}m^2)")

    # 5. Route preservation and non-clipping
    if len(candidate_module.routes) != len(orig_module.routes):
        errors.append(f"Route count changed from {len(orig_module.routes)} to {len(candidate_module.routes)}")
    for orig_r, cand_r in zip(orig_module.routes, candidate_module.routes):
        if orig_r.route_id != cand_r.route_id or orig_r.waypoints != cand_r.waypoints:
            errors.append(f"Route definition modified for route {cand_r.route_id}")
        r_line = LineString(cand_r.waypoints)
        for i, obs in enumerate(candidate_module.obstacles):
            obs_interior = obs.buffer(-1e-3)
            if not obs_interior.is_empty and r_line.intersects(obs_interior):
                errors.append(f"Route {cand_r.route_id} clips through candidate obstacle #{i}")

    # 6. Threat preservation and non-overlap
    if len(candidate_module.threats) != len(orig_module.threats):
        errors.append(f"Threat count changed from {len(orig_module.threats)} to {len(candidate_module.threats)}")
    for orig_t, cand_t in zip(orig_module.threats, candidate_module.threats):
        if orig_t.id != cand_t.id or orig_t.threat_anchor != cand_t.threat_anchor:
            errors.append(f"Threat definition modified for threat {cand_t.id}")
        for i, obs in enumerate(candidate_module.obstacles):
            if obs.intersects(cand_t.polygon):
                inter = obs.intersection(cand_t.polygon)
                if inter.area > 1e-4:
                    errors.append(f"Candidate obstacle #{i} clips into threat polygon {cand_t.id}")

    # 7. Port preservation
    if len(candidate_module.ports) != len(orig_module.ports):
        errors.append(f"Port count changed from {len(orig_module.ports)} to {len(candidate_module.ports)}")
    for orig_p, cand_p in zip(orig_module.ports, candidate_module.ports):
        if orig_p.id != cand_p.id or list(orig_p.segment.coords) != list(cand_p.segment.coords):
            errors.append(f"Port definition modified for port {cand_p.id}")

    return errors


# =============================================================================
# MINIMAL TACTICAL REPAIR OPTIMIZER
# =============================================================================

@dataclass
class RepairResult:
    """Outcome of minimal geometric repair optimization."""
    success: bool
    repaired_module: GeometricModule
    edit_distance_m: float
    initial_margin_tics: int
    repaired_margin_tics: int
    evaluations_count: int
    runtime_ms: float
    diagnosis: TacticalDiagnostic
    repair_description: str
    no_repair_needed: bool = False


class MinimalRepairOptimizer:
    """Grid-minimal inverse tactical repair solver over declared obstacle-translation operator set T_obs."""

    def __init__(self, params: Optional[TicCombatParameters] = None):
        self.params = params or TicCombatParameters()
        self.referee = DeterministicSimulationReferee(self.params)
        self.scheduler = DiscreteTicScheduler(self.params)

    def repair(
        self,
        geo_module: GeometricModule,
        target_margin_tics: int = 2,
        max_perturbation_m: float = 1.80,
        search_resolution_m: float = 0.05,
        route_index: int = 0,
        initial_reticle_deg: float = 0.0
    ) -> RepairResult:
        """Find the grid-minimal perturbation in declared translation operator set achieving M(G*) >= target_margin."""
        t_start = time.perf_counter()

        diag = diagnose_clearability(
            geo_module,
            target_margin_tics=target_margin_tics,
            params=self.params,
            route_index=route_index,
            initial_reticle_deg=initial_reticle_deg
        )

        if diag.is_serviceable:
            t_end = time.perf_counter()
            return RepairResult(
                success=False,
                repaired_module=geo_module,
                edit_distance_m=0.0,
                initial_margin_tics=diag.initial_margin_tics,
                repaired_margin_tics=diag.initial_margin_tics,
                evaluations_count=1,
                runtime_ms=(t_end - t_start) * 1000.0,
                diagnosis=diag,
                repair_description="Module already meets tactical margin target. No repair needed.",
                no_repair_needed=True
            )

        if diag.controlling_obstacle_idx is None or not geo_module.obstacles:
            t_end = time.perf_counter()
            return RepairResult(
                success=False,
                repaired_module=geo_module,
                edit_distance_m=0.0,
                initial_margin_tics=diag.initial_margin_tics,
                repaired_margin_tics=diag.initial_margin_tics,
                evaluations_count=1,
                runtime_ms=(t_end - t_start) * 1000.0,
                diagnosis=diag,
                repair_description="Failed: No controlling obstacle found to perturb.",
                no_repair_needed=False
            )

        # Candidate obstacle indices: evaluate all declared obstacles in module
        candidate_obs_indices = list(range(len(geo_module.obstacles)))

        best_repaired_mod = None
        best_edit_dist = float('inf')
        best_margin = diag.initial_margin_tics
        best_desc = ""
        total_evals = 1

        norm_x, norm_y = diag.suggested_perturbation_normal or (1.0, 0.0)

        # Declared candidate perturbation search directions
        candidate_directions = [
            (norm_x, norm_y),             # Along computed normal towards route
            (-norm_x, -norm_y),           # Reverse normal
            (1.0, 0.0), (-1.0, 0.0),      # Coordinate X translations (+X shifts walls downstream)
            (0.0, 1.0), (0.0, -1.0)       # Coordinate Y translations
        ]

        for obs_idx in candidate_obs_indices:
            orig_obs = geo_module.obstacles[obs_idx]

            for dir_x, dir_y in candidate_directions:
                low_d = search_resolution_m
                high_d = max_perturbation_m

                displacements = np.arange(low_d, high_d + 1e-6, search_resolution_m)
                for d in displacements:
                    d_float = round(float(d), 4)
                    if d_float >= best_edit_dist:
                        break

                    total_evals += 1
                    dx = float(d_float * dir_x)
                    dy = float(d_float * dir_y)

                    # Translate obstacle
                    new_obs_poly = translate(orig_obs, xoff=dx, yoff=dy)
                    new_obstacles = list(geo_module.obstacles)
                    new_obstacles[obs_idx] = new_obs_poly

                    candidate_mod = GeometricModule(
                        module_id=f"{geo_module.module_id}_repaired",
                        name=f"{geo_module.name} (Repaired: d={d_float:.2f}m)",
                        boundary=geo_module.boundary,
                        obstacles=new_obstacles,
                        ports=geo_module.ports,
                        threats=geo_module.threats,
                        routes=geo_module.routes,
                        category=geo_module.category,
                        description=f"{geo_module.description} [Repaired with shift ({dx:+.2f}m, {dy:+.2f}m)]"
                    )

                    # Check geometric integrity & strict preservation invariants
                    errors = validate_geometry_integrity(candidate_mod)
                    if errors:
                        continue
                    pres_errs = validate_repair_preservation(geo_module, candidate_mod)
                    if pres_errs:
                        continue

                    # Compile and check tactical margin
                    jobs = self.referee.extract_tic_jobs(candidate_mod, route_index=route_index)
                    sched_res = self.scheduler.solve(jobs, initial_reticle_deg=initial_reticle_deg)
                    cand_margin = sched_res.tactical_margin_tics

                    if cand_margin >= target_margin_tics:
                        if d_float < best_edit_dist or (abs(d_float - best_edit_dist) < 1e-6 and cand_margin > best_margin):
                            best_edit_dist = d_float
                            best_repaired_mod = candidate_mod
                            best_margin = cand_margin
                            best_desc = f"Shift obstacle #{obs_idx} by {d_float:.2f}m along vector ({dir_x:+.2f}, {dir_y:+.2f}) -> Margin M = {cand_margin} tics."
                        # Found minimal satisfying displacement along this specific direction
                        break

        t_end = time.perf_counter()
        runtime_ms = (t_end - t_start) * 1000.0

        if best_repaired_mod is not None:
            return RepairResult(
                success=True,
                repaired_module=best_repaired_mod,
                edit_distance_m=best_edit_dist,
                initial_margin_tics=diag.initial_margin_tics,
                repaired_margin_tics=best_margin,
                evaluations_count=total_evals,
                runtime_ms=runtime_ms,
                diagnosis=diag,
                repair_description=best_desc,
                no_repair_needed=False
            )
        else:
            return RepairResult(
                success=False,
                repaired_module=geo_module,
                edit_distance_m=0.0,
                initial_margin_tics=diag.initial_margin_tics,
                repaired_margin_tics=diag.initial_margin_tics,
                evaluations_count=total_evals,
                runtime_ms=runtime_ms,
                diagnosis=diag,
                repair_description=f"Repair failed: Could not achieve M >= {target_margin_tics} tics within {max_perturbation_m}m perturbation budget.",
                no_repair_needed=False
            )
