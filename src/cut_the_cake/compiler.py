"""Round 10.2: Geometry-to-Contract Compiler [G -> C -> P] (Hardened & Mathematically Verified).

Compiles raw 2D level geometry (floor polygons, wall obstacles, ports with reset zones,
threat firing anchors, and candidate routes) into certified tactical scheduling contracts
(SpatialThreatJob, SpatialModuleTransferMap, and AuthoredModule).

Includes:
- Critical-LOS candidate raycast event analysis for sub-millimeter flash detection
- Standard 2D radial / angular sweep visibility polygon (isovist) algorithm
- Explicit clearance-bounded port reset-zone quiescence certification (dist(Q, V(q)) >= epsilon_reset)
- Pre-compilation structural/physical geometric validity gating with route-to-port topological verification
- Explicit CompilationStatus separating compiler validity from tactical feasibility
- Outgoing polyline vertex tangent heading convention
"""

from __future__ import annotations
import math
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any, Callable, Set
from dataclasses import dataclass, field
import numpy as np
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from shapely.ops import unary_union

from .model import PlayerModel, CombatModel
from .geometry import (
    normalize_angle_deg,
    angle_diff_deg,
    heading_to_deg,
    distance,
    segments_intersect,
    extract_polygon_segments,
    is_segment_blocked
)
from .contracts import (
    AngularSectorDiscretization,
    SpatialThreatJob,
    SpatialRoute,
    SpatialModuleTransferMap
)
from .pcg_modules import AuthoredModule


class CompilationStatus(str, Enum):
    """Compilation status distinguishing geometric validity, extraction success, and tactical playability."""
    VALID_FEASIBLE = "VALID_FEASIBLE"          # Valid geometry, extracted, tactically feasible (Delta T < inf)
    VALID_INFEASIBLE = "VALID_INFEASIBLE"      # Valid geometry, extracted, tactically infeasible trap (Delta T = inf)
    INVALID_GEOMETRY = "INVALID_GEOMETRY"      # Structural / physical violation (route clips wall, port mismatch)
    ORACLE_DISAGREEMENT = "ORACLE_DISAGREEMENT" # Numerical extraction discrepancy between oracles


@dataclass(frozen=True)
class GeometricThreat:
    """A threat region with an explicit, canonical hostile firing anchor [G + C]."""
    id: str
    polygon: Polygon
    threat_anchor: Tuple[float, float]
    authored_due_window_s: float = 2.0
    base_ttk_s: float = 0.25
    opp_reaction_s: float = 0.20
    service_duration_s: float = 0.20
    description: str = ""

    @property
    def anchor_point(self) -> Point:
        return Point(self.threat_anchor[0], self.threat_anchor[1])


@dataclass
class GeometricPort:
    """Boundary interface port with optional wait-safe quiescent reset pocket [G]."""
    id: str
    segment: LineString
    normal: Tuple[float, float] = (1.0, 0.0)
    reset_zone: Optional[Polygon] = None
    is_quiescent_certified: bool = False
    port_type: str = "STANDARD"


@dataclass
class GeometricRoute:
    """Authored candidate polyline route traversing through module geometry [G]."""
    route_id: str
    waypoints: List[Tuple[float, float]]
    v_move_mps: float = 4.5

    def __post_init__(self):
        assert len(self.waypoints) >= 2, "A route must contain at least 2 waypoints"
        self._line = LineString(self.waypoints)
        self._length = self._line.length

    @property
    def total_length_m(self) -> float:
        return self._length

    @property
    def traversal_duration_s(self) -> float:
        return self._length / max(self.v_move_mps, 1e-4)

    def position_at_distance(self, s: float) -> Tuple[float, float]:
        """Get 2D position (x, y) at distance s along the route polyline."""
        clamped_s = max(0.0, min(self._length, s))
        pt = self._line.interpolate(clamped_s)
        return (pt.x, pt.y)

    def forward_heading_at_distance(self, s: float) -> float:
        """Get forward movement heading in degrees at distance s along the route.
        
        Convention: At waypoint vertices, uses the outgoing forward direction along the subsequent segment.
        """
        clamped_s = max(0.0, min(self._length, s))
        if clamped_s >= self._length - 1e-5:
            return heading_to_deg(self.waypoints[-2], self.waypoints[-1])

        accum = 0.0
        for i in range(len(self.waypoints) - 1):
            p1 = self.waypoints[i]
            p2 = self.waypoints[i + 1]
            seg_len = distance(p1, p2)
            if clamped_s < accum + seg_len - 1e-6:
                return heading_to_deg(p1, p2)
            elif abs(clamped_s - (accum + seg_len)) <= 1e-6:
                if i + 1 < len(self.waypoints) - 1:
                    return heading_to_deg(self.waypoints[i + 1], self.waypoints[i + 2])
                return heading_to_deg(p1, p2)
            accum += seg_len

        return heading_to_deg(self.waypoints[-2], self.waypoints[-1])


@dataclass
class GeometricModule:
    """Raw spatial module with 2D geometry, obstacles, ports, threats, and candidate routes [G]."""
    module_id: str
    name: str
    boundary: Polygon
    obstacles: List[Polygon] = field(default_factory=list)
    ports: List[GeometricPort] = field(default_factory=list)
    threats: List[GeometricThreat] = field(default_factory=list)
    routes: List[GeometricRoute] = field(default_factory=list)
    category: str = "custom"
    description: str = ""


# =============================================================================
# STRUCTURAL GEOMETRIC INTEGRITY VALIDATION
# =============================================================================

def validate_geometry_integrity(geo_module: GeometricModule, port_tol_m: float = 0.10) -> List[str]:
    """Check physical, topological, and route-to-port validity before compilation."""
    errors: List[str] = []
    b = geo_module.boundary

    if not b.is_valid or b.is_empty or b.area <= 1e-4:
        errors.append(f"Invalid or empty module boundary polygon in {geo_module.module_id}")

    # Check threat polygons and anchors
    for t in geo_module.threats:
        p_anchor = Point(t.threat_anchor)
        if not t.polygon.buffer(1e-3).contains(p_anchor):
            errors.append(f"Threat anchor {t.id} {t.threat_anchor} is outside threat polygon")
        if not b.buffer(1e-3).contains(t.polygon):
            errors.append(f"Threat polygon {t.id} is not fully contained within floorplan boundary")

    # Check obstacles
    for i, obs in enumerate(geo_module.obstacles):
        if not obs.is_valid:
            errors.append(f"Obstacle #{i} in {geo_module.module_id} is geometrically invalid")

    # Check ports
    for p in geo_module.ports:
        if not b.buffer(port_tol_m).intersects(p.segment):
            errors.append(f"Port {p.id} does not lie on or intersect the module floorplan boundary")
        if p.reset_zone is not None:
            if not b.buffer(1e-3).contains(p.reset_zone):
                errors.append(f"Reset zone on port {p.id} extends outside floorplan boundary")
            for i, obs in enumerate(geo_module.obstacles):
                obs_interior = obs.buffer(-1e-3)
                if not obs_interior.is_empty and p.reset_zone.intersects(obs_interior):
                    inter = p.reset_zone.intersection(obs_interior)
                    if inter.area > 1e-4:
                        errors.append(f"Reset zone on port {p.id} clips into obstacle #{i}")

    # Check routes
    for r in geo_module.routes:
        r_line = LineString(r.waypoints)
        # Route must be inside floorplan
        diff = r_line.difference(b.buffer(1e-3))
        if not diff.is_empty and diff.length > 1e-3:
            errors.append(f"Route {r.route_id} extends outside the floorplan boundary")

        # Route must not clip through wall interiors
        for i, obs in enumerate(geo_module.obstacles):
            obs_interior = obs.buffer(-1e-3)
            if not obs_interior.is_empty and r_line.intersects(obs_interior):
                errors.append(f"Route {r.route_id} clips through interior of obstacle #{i}")

        # Route endpoint to declared ports topological alignment check
        if geo_module.ports:
            p_start = Point(r.waypoints[0])
            p_end = Point(r.waypoints[-1])
            entry_ports = [p for p in geo_module.ports if "IN" in p.id.upper()] or [geo_module.ports[0]]
            exit_ports = [p for p in geo_module.ports if "OUT" in p.id.upper()] or [geo_module.ports[-1]]

            if not any(p_start.distance(p.segment) <= port_tol_m for p in entry_ports):
                errors.append(f"Route {r.route_id} start point {r.waypoints[0]} does not align with any entry port (tolerance={port_tol_m}m)")
            if not any(p_end.distance(p.segment) <= port_tol_m for p in exit_ports):
                errors.append(f"Route {r.route_id} end point {r.waypoints[-1]} does not align with any exit port (tolerance={port_tol_m}m)")

    return errors


# =============================================================================
# CRITICAL-LOS EVENT RAYCASTING & DUAL ORACLE ENGINE
# =============================================================================

def check_line_of_sight(
    observer_eye: Tuple[float, float],
    target_anchor: Tuple[float, float],
    obstacles: List[Polygon]
) -> bool:
    """Check physical line-of-sight between observer and hostile firing anchor.
    
    Returns True if straight sightline [observer_eye, target_anchor] is unoccluded.
    """
    if not obstacles:
        return True
    return not is_segment_blocked(observer_eye, target_anchor, obstacles)


def compute_critical_los_events(
    route: GeometricRoute,
    threat_anchor: Tuple[float, float],
    obstacles: List[Polygon],
    coarse_ds_m: float = 0.10
) -> List[float]:
    """Compute all critical route distances s where line-of-sight topology can change.
    
    Finds exact ray-vertex collinear line intersections with the route polyline.
    """
    qx, qy = threat_anchor
    candidate_s = set([0.0, route.total_length_m])

    # Add waypoint distances
    accum = 0.0
    for i in range(len(route.waypoints) - 1):
        accum += distance(route.waypoints[i], route.waypoints[i + 1])
        candidate_s.add(min(route.total_length_m, accum))

    # Add regular coarse grid
    for s_step in np.arange(0.0, route.total_length_m + coarse_ds_m, coarse_ds_m):
        candidate_s.add(min(route.total_length_m, float(s_step)))

    # Collect all obstacle vertices
    vertices: List[Tuple[float, float]] = []
    for obs in obstacles:
        coords = list(obs.exterior.coords)[:-1]
        vertices.extend(coords)
        for interior in obs.interiors:
            vertices.extend(list(interior.coords)[:-1])

    # Ray-vertex line intersection with route segments
    for vx, vy in vertices:
        dx = vx - qx
        dy = vy - qy
        if math.hypot(dx, dy) < 1e-5:
            continue
        
        # Infinite line passing through q and v: ax + by + c = 0
        a = dy
        b = -dx
        c = -(a * qx + b * qy)

        # Check intersection with each route segment
        seg_accum = 0.0
        for i in range(len(route.waypoints) - 1):
            p1 = route.waypoints[i]
            p2 = route.waypoints[i + 1]
            seg_len = distance(p1, p2)

            f1 = a * p1[0] + b * p1[1] + c
            f2 = a * p2[0] + b * p2[1] + c

            if f1 * f2 <= 0.0 and abs(f1 - f2) > 1e-8:
                t_inter = f1 / (f1 - f2)
                t_clamped = max(0.0, min(1.0, t_inter))
                s_pt = seg_accum + (t_clamped * seg_len)
                candidate_s.add(min(route.total_length_m, s_pt))

            seg_accum += seg_len

    sorted_s = sorted(list(candidate_s))
    return sorted_s


class DualOracleRevealEngine:
    """Computes exact first-reveal timestamps r_j along route polylines using dual oracles."""

    @staticmethod
    def find_first_reveal_dense(
        route: GeometricRoute,
        threat_anchor: Tuple[float, float],
        obstacles: List[Polygon],
        step_m: float = 0.002
    ) -> Optional[float]:
        """Reference Oracle: Sub-centimeter dense march finding earliest reveal distance s."""
        total_len = route.total_length_m
        num_steps = int(math.ceil(total_len / step_m)) + 1
        s_values = np.linspace(0.0, total_len, num_steps)
        obs_segs = extract_polygon_segments(obstacles)

        for s in s_values:
            pos = route.position_at_distance(float(s))
            blocked = False
            for s1, s2 in obs_segs:
                if segments_intersect(pos, threat_anchor, s1, s2):
                    blocked = True
                    break
            if not blocked:
                return float(s)
        return None

    @staticmethod
    def find_first_reveal_adaptive(
        route: GeometricRoute,
        threat_anchor: Tuple[float, float],
        obstacles: List[Polygon],
        coarse_step_m: float = 0.04,
        tol_m: float = 0.0005
    ) -> Optional[float]:
        """Practical Critical-Event Compiler: Evaluates critical-LOS candidate intervals with bisection.
        
        Guarantees sub-millimeter flash resilience across arbitrary narrow apertures.
        """
        critical_s = compute_critical_los_events(
            route, threat_anchor, obstacles, coarse_ds_m=coarse_step_m
        )
        obs_segs = extract_polygon_segments(obstacles)

        def is_visible(pos: Tuple[float, float]) -> bool:
            for s1, s2 in obs_segs:
                if segments_intersect(pos, threat_anchor, s1, s2):
                    return False
            return True

        first_vis_bracket = None
        for i in range(len(critical_s)):
            s_curr = critical_s[i]
            pos = route.position_at_distance(s_curr)
            if is_visible(pos):
                if i == 0:
                    return 0.0
                first_vis_bracket = (critical_s[i - 1], s_curr)
                break

            # Also check midpoint of interval
            if i < len(critical_s) - 1:
                s_next = critical_s[i + 1]
                s_mid = (s_curr + s_next) / 2.0
                pos_mid = route.position_at_distance(s_mid)
                if is_visible(pos_mid):
                    first_vis_bracket = (s_curr, s_mid)
                    break

        if first_vis_bracket is None:
            return None

        # Binary bisection on bracket [s_hidden, s_visible]
        s_low, s_high = first_vis_bracket
        while (s_high - s_low) > tol_m:
            s_mid = (s_low + s_high) / 2.0
            pos = route.position_at_distance(s_mid)
            if is_visible(pos):
                s_high = s_mid
            else:
                s_low = s_mid

        return s_high


# =============================================================================
# AIM BEARING COMPILER & DEADLINE POLICIES
# =============================================================================

class AimBearingCompiler:
    """Evaluates relative aim bearing theta_j at the first-reveal timestamp."""

    @staticmethod
    def compute_relative_bearing_deg(
        route: GeometricRoute,
        reveal_s: float,
        threat_anchor: Tuple[float, float]
    ) -> float:
        """Compute relative aim angle in [-180, +180] degrees relative to forward heading."""
        pos = route.position_at_distance(reveal_s)
        forward_heading = route.forward_heading_at_distance(reveal_s)
        target_heading = heading_to_deg(pos, threat_anchor)
        rel_angle = normalize_angle_deg(target_heading - forward_heading)
        return rel_angle


class DeadlinePolicy:
    """Abstract base class for threat deadline calculation."""
    def compute_due_window_s(
        self,
        threat: GeometricThreat,
        observer_pos: Tuple[float, float]
    ) -> float:
        raise NotImplementedError


class ConstantDeadlinePolicy(DeadlinePolicy):
    """Pass-through policy using the threat's authored due window (for exact model parity)."""
    def compute_due_window_s(
        self,
        threat: GeometricThreat,
        observer_pos: Tuple[float, float]
    ) -> float:
        return threat.authored_due_window_s


class RangeDependentDeadlinePolicy(DeadlinePolicy):
    """Range-dependent combat deadline policy: D_j = t_rx + TTK(range)."""
    def __init__(self, combat_model: Optional[CombatModel] = None, range_scale: float = 0.05):
        self.combat = combat_model or CombatModel()
        self.range_scale = range_scale

    def compute_due_window_s(
        self,
        threat: GeometricThreat,
        observer_pos: Tuple[float, float]
    ) -> float:
        dist = distance(observer_pos, threat.threat_anchor)
        return self.combat.opp_reaction_s + self.combat.base_ttk_s + (dist * self.range_scale)


# =============================================================================
# CANONICAL 2D RADIAL SWEEP VISIBILITY POLYGON & PORT QUIESCENCE
# =============================================================================

def _ray_segment_intersection_distance(
    qx: float, qy: float,
    dx: float, dy: float,
    p1: Tuple[float, float],
    p2: Tuple[float, float]
) -> Optional[float]:
    """Find ray parameter t >= 0 where q + t*d intersects segment [p1, p2]."""
    x1, y1 = p1
    x2, y2 = p2
    sx = x2 - x1
    sy = y2 - y1

    det = -dx * sy + dy * sx
    if abs(det) < 1e-12:
        return None

    # Solve q + t*d = p1 + u*s
    t = ((x1 - qx) * (-sy) + (y1 - qy) * sx) / det
    u = (dx * (y1 - qy) - dy * (x1 - qx)) / det

    if t >= -1e-8 and -1e-8 <= u <= 1.0 + 1e-8:
        return max(0.0, float(t))
    return None


def compute_exact_visibility_polygon(
    source_pt: Tuple[float, float],
    boundary: Polygon,
    obstacles: List[Polygon],
    r_max: float = 500.0
) -> Polygon:
    """Compute exact 2D isovist / visibility polygon from source_pt using radial angular sweep."""
    qx, qy = source_pt

    # 1. Collect all line segments from boundary and obstacles
    segments: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
    
    # Boundary segments
    coords = list(boundary.exterior.coords)[:-1]
    for i in range(len(coords)):
        segments.append((coords[i], coords[(i + 1) % len(coords)]))
    for interior in boundary.interiors:
        icoords = list(interior.coords)[:-1]
        for i in range(len(icoords)):
            segments.append((icoords[i], icoords[(i + 1) % len(icoords)]))

    # Obstacle segments
    for obs in obstacles:
        ocoords = list(obs.exterior.coords)[:-1]
        for i in range(len(ocoords)):
            segments.append((ocoords[i], ocoords[(i + 1) % len(ocoords)]))
        for interior in obs.interiors:
            icoords = list(interior.coords)[:-1]
            for i in range(len(icoords)):
                segments.append((icoords[i], icoords[(i + 1) % len(icoords)]))

    # 2. Extract unique endpoints and generate ray angles
    angles: Set[float] = set()
    eps = 1e-7

    for p1, p2 in segments:
        for pt in (p1, p2):
            ang = math.atan2(pt[1] - qy, pt[0] - qx)
            angles.add(ang)
            angles.add(ang - eps)
            angles.add(ang + eps)

    # 3. Sort angles cyclically in [-pi, pi]
    sorted_angles = sorted(list(angles))

    # 4. Cast rays along each angle and find nearest segment intersection
    vis_vertices: List[Tuple[float, float]] = []
    for ang in sorted_angles:
        dx = math.cos(ang)
        dy = math.sin(ang)

        min_t = r_max
        for p1, p2 in segments:
            t = _ray_segment_intersection_distance(qx, qy, dx, dy, p1, p2)
            if t is not None and t < min_t:
                min_t = t

        vx = qx + min_t * dx
        vy = qy + min_t * dy
        vis_vertices.append((vx, vy))

    if len(vis_vertices) < 3:
        return Polygon()

    vis_poly = Polygon(vis_vertices)
    if not vis_poly.is_valid:
        vis_poly = vis_poly.buffer(0)
    
    # Clip by boundary for safety
    vis_poly = vis_poly.intersection(boundary)
    return vis_poly


def certify_port_quiescence(
    port: GeometricPort,
    threats: List[GeometricThreat],
    obstacles: List[Polygon],
    boundary: Optional[Polygon] = None,
    clearance_m: float = 0.05
) -> bool:
    """Certify continuous geometric wait-safe quiescence with clearance margin epsilon_reset.
    
    Requires dist(Q, V(q_j)) >= clearance_m for all hostile anchors q_j.
    """
    if port.reset_zone is None:
        port.is_quiescent_certified = False
        return False

    q_poly = port.reset_zone
    if q_poly.is_empty or q_poly.area < 1e-4:
        port.is_quiescent_certified = False
        return False

    b = boundary or q_poly.buffer(100.0)

    for threat in threats:
        vis_poly = compute_exact_visibility_polygon(threat.threat_anchor, b, obstacles)
        if q_poly.intersects(vis_poly):
            port.is_quiescent_certified = False
            return False
        if q_poly.distance(vis_poly) < clearance_m:
            port.is_quiescent_certified = False
            return False

    port.is_quiescent_certified = True
    return True


# =============================================================================
# GEOMETRY-TO-CONTRACT COMPILER
# =============================================================================

@dataclass
class CompiledRouteResult:
    route_id: str
    traversal_duration_s: float
    compiled_jobs: List[SpatialThreatJob]
    reveal_distances_m: Dict[str, float]
    reveal_times_s: Dict[str, float]
    relative_angles_deg: Dict[str, float]
    due_windows_s: Dict[str, float]
    dense_oracle_discrepancies_ms: Dict[str, float]


@dataclass
class CompiledModuleResult:
    module_id: str
    name: str
    status: CompilationStatus
    compiler_valid: bool
    tactically_feasible: bool
    validation_errors: List[str]
    authored_module: Optional[AuthoredModule]
    transfer_map: Optional[SpatialModuleTransferMap]
    compiled_routes: List[CompiledRouteResult]
    certified_ports: List[GeometricPort]
    max_dense_oracle_discrepancy_ms: float

    @property
    def is_fully_certified(self) -> bool:
        """Backward compatibility helper: True if both compiler valid and tactically feasible."""
        return self.status == CompilationStatus.VALID_FEASIBLE


class GeometryToContractCompiler:
    """Compiles a GeometricModule into a validated AuthoredModule and SpatialModuleTransferMap."""

    def __init__(
        self,
        discretization: Optional[AngularSectorDiscretization] = None,
        player: Optional[PlayerModel] = None,
        deadline_policy: Optional[DeadlinePolicy] = None,
        quiescent_clearance_m: float = 0.05,
        dense_oracle_step_m: float = 0.0001
    ):
        self.disc = discretization or AngularSectorDiscretization(num_sectors=4)
        self.player = player or PlayerModel()
        self.deadline_policy = deadline_policy or ConstantDeadlinePolicy()
        self.quiescent_clearance_m = quiescent_clearance_m
        self.dense_oracle_step_m = dense_oracle_step_m

    def compile(self, geo_module: GeometricModule) -> CompiledModuleResult:
        """Compile GeometricModule -> AuthoredModule & SpatialModuleTransferMap."""
        # 1. Structural Geometric Validity Gate
        val_errors = validate_geometry_integrity(geo_module)
        if val_errors:
            return CompiledModuleResult(
                module_id=geo_module.module_id,
                name=geo_module.name,
                status=CompilationStatus.INVALID_GEOMETRY,
                compiler_valid=False,
                tactically_feasible=False,
                validation_errors=val_errors,
                authored_module=None,
                transfer_map=None,
                compiled_routes=[],
                certified_ports=geo_module.ports,
                max_dense_oracle_discrepancy_ms=0.0
            )

        compiled_routes: List[CompiledRouteResult] = []
        spatial_routes: List[SpatialRoute] = []
        max_discrepancy_ms = 0.0

        for r in geo_module.routes:
            compiled_jobs: List[SpatialThreatJob] = []
            rev_dists: Dict[str, float] = {}
            rev_times: Dict[str, float] = {}
            rel_angles: Dict[str, float] = {}
            due_wins: Dict[str, float] = {}
            discrepancies: Dict[str, float] = {}

            for threat in geo_module.threats:
                # Reveal Distance: Critical-event adaptive compiler
                s_adapt = DualOracleRevealEngine.find_first_reveal_adaptive(
                    r, threat.threat_anchor, geo_module.obstacles
                )
                
                # Reference Dense Oracle
                s_dense = DualOracleRevealEngine.find_first_reveal_dense(
                    r, threat.threat_anchor, geo_module.obstacles,
                    step_m=self.dense_oracle_step_m
                )

                if s_adapt is not None and s_dense is not None:
                    disc_ms = abs(s_adapt - s_dense) / r.v_move_mps * 1000.0
                    discrepancies[threat.id] = disc_ms
                    max_discrepancy_ms = max(max_discrepancy_ms, disc_ms)
                elif s_adapt is None and s_dense is None:
                    continue
                else:
                    disc_ms = 999.0
                    discrepancies[threat.id] = disc_ms
                    max_discrepancy_ms = max(max_discrepancy_ms, disc_ms)

                if s_adapt is None:
                    continue

                r_time_s = s_adapt / r.v_move_mps
                pos = r.position_at_distance(s_adapt)
                
                angle_deg = AimBearingCompiler.compute_relative_bearing_deg(
                    r, s_adapt, threat.threat_anchor
                )
                sector = self.disc.get_sector(angle_deg)
                due_win = self.deadline_policy.compute_due_window_s(threat, pos)
                service_s = self.player.inspect_duration_s

                job = SpatialThreatJob(
                    id=threat.id,
                    offset_s=r_time_s,
                    due_window_s=due_win,
                    service_s=service_s,
                    angle_deg=angle_deg,
                    sector=sector
                )
                compiled_jobs.append(job)

                rev_dists[threat.id] = s_adapt
                rev_times[threat.id] = r_time_s
                rel_angles[threat.id] = angle_deg
                due_wins[threat.id] = due_win

            compiled_jobs.sort(key=lambda j: j.offset_s)

            compiled_routes.append(CompiledRouteResult(
                route_id=r.route_id,
                traversal_duration_s=r.traversal_duration_s,
                compiled_jobs=compiled_jobs,
                reveal_distances_m=rev_dists,
                reveal_times_s=rev_times,
                relative_angles_deg=rel_angles,
                due_windows_s=due_wins,
                dense_oracle_discrepancies_ms=discrepancies
            ))

            spatial_routes.append(SpatialRoute(
                route_id=r.route_id,
                traversal_duration_s=r.traversal_duration_s,
                jobs=compiled_jobs
            ))

        # Certify all boundary ports using exact radial sweep visibility polygons and clearance margin
        for p in geo_module.ports:
            certify_port_quiescence(
                p, geo_module.threats, geo_module.obstacles, geo_module.boundary,
                clearance_m=self.quiescent_clearance_m
            )

        # Compute peak static concurrency
        peak_k = 1
        for cr in compiled_routes:
            if not cr.compiled_jobs:
                continue
            times = []
            for j in cr.compiled_jobs:
                times.append((j.offset_s, 1))
                times.append((j.offset_s + j.due_window_s, -1))
            times.sort(key=lambda x: (x[0], -x[1]))
            cur_k = 0
            for t, val in times:
                cur_k += val
                peak_k = max(peak_k, cur_k)

        has_quiescent_entry = any(p.is_quiescent_certified for p in geo_module.ports if "IN" in p.id.upper())
        entry_p = geo_module.ports[0].id if geo_module.ports else "PORT_IN"
        exit_p = geo_module.ports[-1].id if len(geo_module.ports) > 1 else "PORT_OUT"
        entry_p_type = geo_module.ports[0].port_type if geo_module.ports else "STANDARD"
        exit_p_type = geo_module.ports[-1].port_type if len(geo_module.ports) > 1 else "STANDARD"

        authored_mod = AuthoredModule(
            module_id=geo_module.module_id,
            name=geo_module.name,
            category=geo_module.category,
            entry_port=entry_p,
            exit_port=exit_p,
            entry_port_type=entry_p_type,
            exit_port_type=exit_p_type,
            routes=spatial_routes,
            k_ici_max=peak_k,
            is_quiescent=has_quiescent_entry,
            description=geo_module.description
        )

        tmap = authored_mod.get_transfer_map(self.disc, self.player)
        is_feas = tmap.is_feasible_from_any_reset_state()

        if max_discrepancy_ms > 5.0:
            status = CompilationStatus.ORACLE_DISAGREEMENT
        elif is_feas:
            status = CompilationStatus.VALID_FEASIBLE
        else:
            status = CompilationStatus.VALID_INFEASIBLE

        return CompiledModuleResult(
            module_id=geo_module.module_id,
            name=geo_module.name,
            status=status,
            compiler_valid=(status in [CompilationStatus.VALID_FEASIBLE, CompilationStatus.VALID_INFEASIBLE]),
            tactically_feasible=is_feas,
            validation_errors=[],
            authored_module=authored_mod,
            transfer_map=tmap,
            compiled_routes=compiled_routes,
            certified_ports=geo_module.ports,
            max_dense_oracle_discrepancy_ms=max_discrepancy_ms
        )
