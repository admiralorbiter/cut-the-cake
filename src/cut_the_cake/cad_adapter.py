"""Tactical CAD Adapter Layer [Cut the Cake / M2B].

Authoritative Python adapter bridging CAD Documents and the scientific core:
- Analyzes arbitrary CADDocument / GeometricModule instances without fixture special-casing.
- Translates any obstacle in 2D (X and Y) with spatial invariant validation.
- Distinguishes fast-path schedulability (source_schedule_feasible) from executed telemetry outcomes.
- Emits fail-closed external evidence metadata.
"""

from __future__ import annotations
import math
import numpy as np
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from shapely.geometry import Polygon, Point, LineString
import shapely.affinity

from .cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPlayerModel,
    get_canonical_f1_document,
    get_custom_asymmetric_corridor_document,
    validate_cad_document
)
from .compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricThreat,
    GeometricPort,
    segments_intersect
)
from .geometry import (
    extract_polygon_segments,
    heading_to_deg,
    normalize_angle_deg
)
from .vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteTicScheduler,
    DeterministicSimulationReferee,
    ControllerPolicy,
    SimulationEpisodeLog
)
from .repair import (
    diagnose_clearability,
    TacticalDiagnostic,
    validate_repair_preservation
)


# Cached canonical documents for fast zero-overhead analysis
_DOCUMENT_CACHE: Dict[str, CADDocument] = {
    "canonical_f1": get_canonical_f1_document(),
    "RepairPop_F1_StaggerDeficit_00": get_canonical_f1_document(),
    "custom_corridor": get_custom_asymmetric_corridor_document(),
    "custom_asymmetric_corridor": get_custom_asymmetric_corridor_document()
}


# =============================================================================
# GEOMETRIC INVARIANT VALIDATION
# =============================================================================

def validate_candidate_obstacle_in_module(
    base_module: GeometricModule,
    obstacle_idx: int,
    candidate_obstacle: Polygon
) -> Tuple[bool, Optional[str]]:
    """Strictly validates geometric invariants for candidate obstacle placement."""
    if not candidate_obstacle.is_valid or candidate_obstacle.is_empty or candidate_obstacle.area <= 1e-4:
        return False, "Candidate obstacle polygon is invalid, empty, or has zero area."

    # 1. Must be strictly contained within arena boundary
    if not base_module.boundary.buffer(1e-4).contains(candidate_obstacle):
        return False, "Candidate obstacle extends outside arena boundary polygon."

    # 2. Minimum clearance to route polylines (0.05m clearance margin)
    clearance_m = 0.05
    for r in base_module.routes:
        route_line = LineString(r.waypoints)
        if route_line.distance(candidate_obstacle) < clearance_m:
            return False, f"Candidate obstacle encroaches on route '{r.route_id}' corridor (clearance < {clearance_m}m)."

    # 3. Minimum clearance to threat firing anchors and threat polygons (0.10m margin)
    threat_clearance_m = 0.10
    for t in base_module.threats:
        p_anchor = Point(t.threat_anchor)
        if p_anchor.distance(candidate_obstacle) < threat_clearance_m:
            return False, f"Candidate obstacle occludes firing anchor of threat '{t.id}'."
        if t.polygon.distance(candidate_obstacle) < 0.02:
            return False, f"Candidate obstacle intersects spawn polygon of threat '{t.id}'."

    # 4. Clearance to boundary ports
    for p in base_module.ports:
        if p.segment.distance(candidate_obstacle) < 0.10:
            return False, f"Candidate obstacle blocks port '{p.id}'."

    # 5. Clearance to all other obstacles
    for idx, other_obs in enumerate(base_module.obstacles):
        if idx != obstacle_idx:
            if other_obs.intersects(candidate_obstacle):
                return False, f"Candidate obstacle intersects obstacle #{idx}."

    return True, None


def generate_next_obstacle_id(doc: CADDocument, session_sequence: Optional[int] = None) -> str:
    """Generate a unique monotonic obstacle ID (e.g. wall_001, wall_002)."""
    existing_ids = {obs.id for obs in doc.obstacles}
    counter = max(1, session_sequence if session_sequence is not None else 1)
    while True:
        candidate_id = f"wall_{counter:03d}"
        if candidate_id not in existing_ids:
            return candidate_id
        counter += 1


def create_rectangle_obstacle(
    doc: CADDocument,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    obstacle_id: Optional[str] = None,
    name: Optional[str] = None,
    session_sequence: Optional[int] = None
) -> Tuple[CADDocument, Optional[str], bool, Optional[str]]:
    """Creates a new axis-aligned rectangle obstacle and validates against spatial invariants."""
    min_x = min(float(x1), float(x2))
    max_x = max(float(x1), float(x2))
    min_y = min(float(y1), float(y2))
    max_y = max(float(y1), float(y2))

    width = max_x - min_x
    height = max_y - min_y

    if width < 0.10 or height < 0.10:
        return doc, None, False, f"Obstacle dimensions ({width:.2f}m x {height:.2f}m) are smaller than minimum allowed (0.10m x 0.10m)."

    verts = [
        [round(min_x, 4), round(min_y, 4)],
        [round(max_x, 4), round(min_y, 4)],
        [round(max_x, 4), round(max_y, 4)],
        [round(min_x, 4), round(max_y, 4)],
        [round(min_x, 4), round(min_y, 4)]
    ]
    cand_poly = Polygon(verts)

    geo_mod = doc.to_geometric_module()
    is_valid, error_reason = validate_candidate_obstacle_in_module(geo_mod, obstacle_idx=-1, candidate_obstacle=cand_poly)
    if not is_valid:
        return doc, None, False, error_reason

    obs_id = obstacle_id if obstacle_id else generate_next_obstacle_id(doc, session_sequence=session_sequence)
    obs_name = name if name else f"Wall ({obs_id})"

    new_obstacles = list(doc.obstacles) + [
        CADObstacle(
            id=obs_id,
            name=obs_name,
            vertices=verts
        )
    ]

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=new_obstacles,
        routes=doc.routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, obs_id, True, None


def translate_obstacle_in_document(
    doc: CADDocument,
    obstacle_id: str,
    dx: float,
    dy: float = 0.0
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Applies a 2D (dx, dy) translation to the specified obstacle and validates spatial invariants."""
    obs_idx = -1
    for idx, obs in enumerate(doc.obstacles):
        if obs.id == obstacle_id:
            obs_idx = idx
            break

    if obs_idx == -1:
        return doc, False, f"Obstacle ID '{obstacle_id}' not found in document '{doc.document_id}'."

    # Construct candidate polygon
    orig_obs = doc.obstacles[obs_idx]
    orig_poly = orig_obs.to_polygon()
    cand_poly = shapely.affinity.translate(orig_poly, xoff=float(dx), yoff=float(dy))

    # Validate against module invariants
    geo_mod = doc.to_geometric_module()
    is_valid, error_reason = validate_candidate_obstacle_in_module(geo_mod, obs_idx, cand_poly)
    if not is_valid:
        return doc, False, error_reason

    # Build updated CADDocument
    new_obstacles = list(doc.obstacles)
    new_verts = [[round(float(x), 4), round(float(y), 4)] for x, y in list(cand_poly.exterior.coords)]
    new_obstacles[obs_idx] = CADObstacle(
        id=orig_obs.id,
        name=orig_obs.name,
        vertices=new_verts
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=new_obstacles,
        routes=doc.routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def resize_rectangle_obstacle(
    doc: CADDocument,
    obstacle_id: str,
    handle: Any,
    dx: float,
    dy: float
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Resizes an obstacle in its local oriented coordinate frame preserving its orientation and opposite pinned corner."""
    obs_idx = -1
    for idx, obs in enumerate(doc.obstacles):
        if obs.id == obstacle_id:
            obs_idx = idx
            break

    if obs_idx == -1:
        return doc, False, f"Obstacle ID '{obstacle_id}' not found in document '{doc.document_id}'."

    orig_obs = doc.obstacles[obs_idx]
    verts_raw = [np.array(v, dtype=float) for v in orig_obs.vertices]
    if len(verts_raw) < 4:
        return doc, False, "Obstacle has fewer than 4 vertices."

    # 4 unique corners
    corners = verts_raw[:-1] if np.allclose(verts_raw[0], verts_raw[-1]) else verts_raw
    if len(corners) != 4:
        return doc, False, "Obstacle is not a 4-corner polygon."

    # Determine drag index
    if isinstance(handle, int) or (isinstance(handle, str) and handle.isdigit()):
        drag_idx = int(handle) % 4
    else:
        h = str(handle).lower()
        c_pts = np.array(corners)
        c_center = np.mean(c_pts, axis=0)
        if h in ("se", "bottom_right"):
            target_dir = np.array([1.0, -1.0])
        elif h in ("nw", "top_left"):
            target_dir = np.array([-1.0, 1.0])
        elif h in ("ne", "top_right"):
            target_dir = np.array([1.0, 1.0])
        elif h in ("sw", "bottom_left"):
            target_dir = np.array([-1.0, -1.0])
        elif h in ("e", "right"):
            target_dir = np.array([1.0, 0.0])
        elif h in ("w", "left"):
            target_dir = np.array([-1.0, 0.0])
        elif h in ("n", "top"):
            target_dir = np.array([0.0, 1.0])
        elif h in ("s", "bottom"):
            target_dir = np.array([0.0, -1.0])
        else:
            target_dir = np.array([1.0, -1.0])

        dots = [np.dot(pt - c_center, target_dir) for pt in corners]
        drag_idx = int(np.argmax(dots))

    opp_idx = (drag_idx + 2) % 4
    v_opp = corners[opp_idx]
    v_drag = corners[drag_idx]

    adj1_idx = (opp_idx + 1) % 4
    adj2_idx = (opp_idx + 3) % 4

    e1 = corners[adj1_idx] - v_opp
    e2 = corners[adj2_idx] - v_opp
    len1 = float(np.linalg.norm(e1))
    len2 = float(np.linalg.norm(e2))
    if len1 < 1e-4 or len2 < 1e-4:
        return doc, False, "Degenerate obstacle edge length."

    u1 = e1 / len1
    u2 = e2 / len2

    v_drag_new = v_drag + np.array([float(dx), float(dy)])
    d = v_drag_new - v_opp

    new_len1 = float(np.dot(d, u1))
    new_len2 = float(np.dot(d, u2))

    if abs(new_len1) < 0.10 or abs(new_len2) < 0.10:
        return doc, False, f"Resized dimensions ({abs(new_len1):.2f}m x {abs(new_len2):.2f}m) are smaller than minimum allowed (0.10m x 0.10m)."

    new_v_opp = v_opp
    new_adj1 = v_opp + new_len1 * u1
    new_drag = v_opp + new_len1 * u1 + new_len2 * u2
    new_adj2 = v_opp + new_len2 * u2

    res_corners = [None] * 4
    res_corners[opp_idx] = new_v_opp.tolist()
    res_corners[adj1_idx] = new_adj1.tolist()
    res_corners[drag_idx] = new_drag.tolist()
    res_corners[adj2_idx] = new_adj2.tolist()
    res_corners.append(res_corners[0])

    new_verts = [[round(float(pt[0]), 4), round(float(pt[1]), 4)] for pt in res_corners]
    cand_poly = Polygon(new_verts)
    if not cand_poly.is_valid or cand_poly.area < 1e-4:
        return doc, False, "Invalid non-simple polygon generated."

    geo_mod = doc.to_geometric_module()
    is_valid, error_reason = validate_candidate_obstacle_in_module(geo_mod, obs_idx, cand_poly)
    if not is_valid:
        return doc, False, error_reason

    new_obstacles = list(doc.obstacles)
    new_obstacles[obs_idx] = CADObstacle(
        id=orig_obs.id,
        name=orig_obs.name,
        vertices=new_verts
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=new_obstacles,
        routes=doc.routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def rotate_obstacle_in_document(
    doc: CADDocument,
    obstacle_id: str,
    angle_deg: Optional[float] = None,
    angle_delta_deg: Optional[float] = None,
    target_angle_deg: Optional[float] = None
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Rotates an obstacle by angle_deg or to target_angle_deg around its centroid and validates spatial invariants."""
    obs_idx = -1
    for idx, obs in enumerate(doc.obstacles):
        if obs.id == obstacle_id:
            obs_idx = idx
            break

    if obs_idx == -1:
        return doc, False, f"Obstacle ID '{obstacle_id}' not found in document '{doc.document_id}'."

    orig_obs = doc.obstacles[obs_idx]
    orig_poly = orig_obs.to_polygon()

    if target_angle_deg is not None:
        coords = list(orig_poly.exterior.coords)
        if len(coords) >= 2:
            dx = coords[1][0] - coords[0][0]
            dy = coords[1][1] - coords[0][1]
            curr_angle = float(np.degrees(np.arctan2(dy, dx)))
        else:
            curr_angle = 0.0
        rot_delta = float(target_angle_deg) - curr_angle
    elif angle_delta_deg is not None:
        rot_delta = float(angle_delta_deg)
    elif angle_deg is not None:
        rot_delta = float(angle_deg)
    else:
        return doc, False, "No angle specified."

    cand_poly = shapely.affinity.rotate(orig_poly, rot_delta, origin='centroid', use_radians=False)

    geo_mod = doc.to_geometric_module()
    is_valid, error_reason = validate_candidate_obstacle_in_module(geo_mod, obs_idx, cand_poly)
    if not is_valid:
        return doc, False, error_reason

    new_verts = [[round(float(x), 4), round(float(y), 4)] for x, y in list(cand_poly.exterior.coords)]
    new_obstacles = list(doc.obstacles)
    new_obstacles[obs_idx] = CADObstacle(
        id=orig_obs.id,
        name=orig_obs.name,
        vertices=new_verts
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=new_obstacles,
        routes=doc.routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def delete_obstacle_in_document(
    doc: CADDocument,
    obstacle_id: str
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Deletes an obstacle from the document."""
    obs_idx = -1
    for idx, obs in enumerate(doc.obstacles):
        if obs.id == obstacle_id:
            obs_idx = idx
            break

    if obs_idx == -1:
        return doc, False, f"Obstacle ID '{obstacle_id}' not found in document '{doc.document_id}'."

    new_obstacles = [obs for obs in doc.obstacles if obs.id != obstacle_id]
    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=new_obstacles,
        routes=doc.routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


# =============================================================================
# M2D TACTICAL SCENARIO AUTHORING (ROUTES, THREATS, PLAYER MODEL)
# =============================================================================

def generate_next_route_id(doc: CADDocument, session_sequence: Optional[int] = None) -> Tuple[str, int]:
    """Generates a monotonic route identifier (e.g. route_001)."""
    curr_seq = session_sequence if session_sequence is not None else 1
    existing_ids = {r.id for r in doc.routes}
    while f"route_{curr_seq:03d}" in existing_ids:
        curr_seq += 1
    cand_id = f"route_{curr_seq:03d}"
    return cand_id, curr_seq + 1


def create_route_in_document(
    doc: CADDocument,
    route_id: Optional[str] = None,
    name: Optional[str] = None,
    waypoints: Optional[List[List[float]]] = None,
    v_move_mps: float = 4.5,
    session_sequence: Optional[int] = None
) -> Tuple[CADDocument, str, bool, Optional[str]]:
    """Creates an authored polyline route and validates boundary containment."""
    if not waypoints or len(waypoints) < 2:
        return doc, "", False, "Route must contain at least 2 waypoints."

    # Validate numeric waypoints
    pts = []
    for pt in waypoints:
        if len(pt) != 2 or not math.isfinite(pt[0]) or not math.isfinite(pt[1]):
            return doc, "", False, f"Invalid waypoint coordinates: {pt}"
        pts.append([round(float(pt[0]), 4), round(float(pt[1]), 4)])

    # Check total length
    total_len = 0.0
    for i in range(len(pts) - 1):
        total_len += math.hypot(pts[i+1][0] - pts[i][0], pts[i+1][1] - pts[i][1])
    if total_len < 1e-3:
        return doc, "", False, "Route polyline has zero total length."

    # Validate boundary containment
    poly_b = Polygon(doc.boundary)
    line = LineString(pts)
    if not poly_b.contains(line) and not poly_b.covers(line):
        return doc, "", False, "Route waypoints must lie completely within boundary."

    if route_id is None:
        cand_id, _ = generate_next_route_id(doc, session_sequence)
    else:
        cand_id = route_id
        if any(r.id == cand_id for r in doc.routes):
            return doc, "", False, f"Route ID '{cand_id}' already exists."

    r_name = name or f"Route ({cand_id})"
    new_route = CADRoute(
        id=cand_id,
        name=r_name,
        waypoints=pts,
        v_move_mps=float(v_move_mps)
    )

    new_routes = list(doc.routes) + [new_route]
    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=new_routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, cand_id, True, None


def update_route_waypoint(
    doc: CADDocument,
    route_id: str,
    waypoint_idx: int,
    x: float,
    y: float
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Updates a single waypoint in an authored route."""
    r_idx = -1
    for idx, r in enumerate(doc.routes):
        if r.id == route_id:
            r_idx = idx
            break
    if r_idx == -1:
        return doc, False, f"Route '{route_id}' not found."

    orig_route = doc.routes[r_idx]
    if waypoint_idx < 0 or waypoint_idx >= len(orig_route.waypoints):
        return doc, False, f"Waypoint index {waypoint_idx} out of range [0, {len(orig_route.waypoints)-1}]."

    new_pts = [list(pt) for pt in orig_route.waypoints]
    new_pts[waypoint_idx] = [round(float(x), 4), round(float(y), 4)]

    # Validate boundary containment
    poly_b = Polygon(doc.boundary)
    line = LineString(new_pts)
    if not poly_b.contains(line) and not poly_b.covers(line):
        return doc, False, "Updated waypoint must lie within boundary."

    new_routes = list(doc.routes)
    new_routes[r_idx] = CADRoute(
        id=orig_route.id,
        name=orig_route.name,
        waypoints=new_pts,
        v_move_mps=orig_route.v_move_mps
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=new_routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def add_route_waypoint(
    doc: CADDocument,
    route_id: str,
    x: float,
    y: float,
    insert_idx: Optional[int] = None
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Appends or inserts a new waypoint into an existing route."""
    r_idx = -1
    for idx, r in enumerate(doc.routes):
        if r.id == route_id:
            r_idx = idx
            break
    if r_idx == -1:
        return doc, False, f"Route '{route_id}' not found."

    orig_route = doc.routes[r_idx]
    new_pts = [list(pt) for pt in orig_route.waypoints]
    new_pt = [round(float(x), 4), round(float(y), 4)]

    if insert_idx is not None and 0 <= insert_idx <= len(new_pts):
        new_pts.insert(insert_idx, new_pt)
    else:
        new_pts.append(new_pt)

    poly_b = Polygon(doc.boundary)
    line = LineString(new_pts)
    if not poly_b.contains(line) and not poly_b.covers(line):
        return doc, False, "New waypoint must lie within boundary."

    new_routes = list(doc.routes)
    new_routes[r_idx] = CADRoute(
        id=orig_route.id,
        name=orig_route.name,
        waypoints=new_pts,
        v_move_mps=orig_route.v_move_mps
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=new_routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def delete_route_waypoint(
    doc: CADDocument,
    route_id: str,
    waypoint_idx: int
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Deletes a waypoint, ensuring at least 2 waypoints remain."""
    r_idx = -1
    for idx, r in enumerate(doc.routes):
        if r.id == route_id:
            r_idx = idx
            break
    if r_idx == -1:
        return doc, False, f"Route '{route_id}' not found."

    orig_route = doc.routes[r_idx]
    if len(orig_route.waypoints) <= 2:
        return doc, False, "Cannot delete waypoint: Route must maintain at least 2 waypoints."

    if waypoint_idx < 0 or waypoint_idx >= len(orig_route.waypoints):
        return doc, False, f"Waypoint index {waypoint_idx} out of range."

    new_pts = [pt for idx, pt in enumerate(orig_route.waypoints) if idx != waypoint_idx]

    new_routes = list(doc.routes)
    new_routes[r_idx] = CADRoute(
        id=orig_route.id,
        name=orig_route.name,
        waypoints=new_pts,
        v_move_mps=orig_route.v_move_mps
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=new_routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def delete_route_in_document(
    doc: CADDocument,
    route_id: str
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Deletes an authored route from the document."""
    if len(doc.routes) <= 1:
        return doc, False, "Cannot delete the only route in the document (cad_document_v1 schema contract requires >= 1 route)."

    r_idx = -1
    for idx, r in enumerate(doc.routes):
        if r.id == route_id:
            r_idx = idx
            break
    if r_idx == -1:
        return doc, False, f"Route '{route_id}' not found."

    new_routes = [r for r in doc.routes if r.id != route_id]
    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=new_routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def update_route_speed(
    doc: CADDocument,
    route_id: str,
    v_move_mps: float
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Updates the authored traversal speed of a route."""
    if not math.isfinite(v_move_mps) or v_move_mps <= 0.0:
        return doc, False, f"Invalid route speed '{v_move_mps}'. Must be a positive finite number."

    r_idx = -1
    for idx, r in enumerate(doc.routes):
        if r.id == route_id:
            r_idx = idx
            break
    if r_idx == -1:
        return doc, False, f"Route '{route_id}' not found."

    orig_route = doc.routes[r_idx]
    new_routes = list(doc.routes)
    new_routes[r_idx] = CADRoute(
        id=orig_route.id,
        name=orig_route.name,
        waypoints=orig_route.waypoints,
        v_move_mps=float(v_move_mps)
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=new_routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def generate_next_threat_id(doc: CADDocument, session_sequence: Optional[int] = None) -> Tuple[str, int]:
    """Generates a monotonic threat identifier (e.g. T1, T2, threat_001)."""
    curr_seq = session_sequence if session_sequence is not None else 1
    existing_ids = {t.id for t in doc.threats}
    while f"T{curr_seq}" in existing_ids:
        curr_seq += 1
    cand_id = f"T{curr_seq}"
    return cand_id, curr_seq + 1


def create_threat_in_document(
    doc: CADDocument,
    threat_id: Optional[str] = None,
    name: Optional[str] = None,
    anchor: Optional[List[float]] = None,
    polygon: Optional[List[List[float]]] = None,
    due_window_s: float = 0.62,
    service_duration_s: float = 0.1143,
    session_sequence: Optional[int] = None
) -> Tuple[CADDocument, str, bool, Optional[str]]:
    """Creates an authored hostile threat zone and firing anchor."""
    if not anchor or len(anchor) != 2 or not math.isfinite(anchor[0]) or not math.isfinite(anchor[1]):
        return doc, "", False, "Invalid threat anchor coordinates."

    anch = [round(float(anchor[0]), 4), round(float(anchor[1]), 4)]

    # If polygon not specified, create a 0.8x0.8m bounding footprint centered around anchor
    if not polygon or len(polygon) < 3:
        hx, hy = 0.4, 0.4
        poly_pts = [
            [anch[0] - hx, anch[1] - hy],
            [anch[0] + hx, anch[1] - hy],
            [anch[0] + hx, anch[1] + hy],
            [anch[0] - hx, anch[1] + hy],
            [anch[0] - hx, anch[1] - hy]
        ]
    else:
        poly_pts = [[round(float(x), 4), round(float(y), 4)] for x, y in polygon]
        if poly_pts[0] != poly_pts[-1]:
            poly_pts.append(poly_pts[0])

    # Validate containment within boundary
    poly_b = Polygon(doc.boundary)
    pt_anch = Point(anch)
    poly_t = Polygon(poly_pts)

    if not poly_b.contains(pt_anch) and not poly_b.covers(pt_anch):
        return doc, "", False, f"Threat anchor {anch} must lie within boundary."
    if not poly_b.contains(poly_t) and not poly_b.covers(poly_t):
        return doc, "", False, "Threat region must lie within boundary."

    if not math.isfinite(due_window_s) or due_window_s <= 0.0:
        return doc, "", False, "due_window_s must be a positive finite number."
    if not math.isfinite(service_duration_s) or service_duration_s <= 0.0:
        return doc, "", False, "service_duration_s must be a positive finite number."

    if threat_id is None:
        cand_id, _ = generate_next_threat_id(doc, session_sequence)
    else:
        cand_id = threat_id
        if any(t.id == cand_id for t in doc.threats):
            return doc, "", False, f"Threat ID '{cand_id}' already exists."

    t_name = name or f"Threat {cand_id}"
    new_threat = CADThreat(
        id=cand_id,
        name=t_name,
        polygon=poly_pts,
        anchor=anch,
        due_window_s=float(due_window_s),
        service_duration_s=float(service_duration_s)
    )

    new_threats = list(doc.threats) + [new_threat]
    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=doc.routes,
        threats=new_threats,
        ports=doc.ports
    )
    return updated_doc, cand_id, True, None


def translate_threat_in_document(
    doc: CADDocument,
    threat_id: str,
    dx: float,
    dy: float
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Translates a threat anchor and region in 2D."""
    t_idx = -1
    for idx, t in enumerate(doc.threats):
        if t.id == threat_id:
            t_idx = idx
            break
    if t_idx == -1:
        return doc, False, f"Threat '{threat_id}' not found."

    orig_threat = doc.threats[t_idx]
    new_anch = [round(orig_threat.anchor[0] + dx, 4), round(orig_threat.anchor[1] + dy, 4)]
    new_poly = [[round(x + dx, 4), round(y + dy, 4)] for x, y in orig_threat.polygon]

    poly_b = Polygon(doc.boundary)
    pt_anch = Point(new_anch)
    poly_t = Polygon(new_poly)

    if not poly_b.contains(pt_anch) and not poly_b.covers(pt_anch):
        return doc, False, f"Translated threat anchor {new_anch} must lie within boundary."
    if not poly_b.contains(poly_t) and not poly_b.covers(poly_t):
        return doc, False, "Translated threat region must lie within boundary."

    new_threats = list(doc.threats)
    new_threats[t_idx] = CADThreat(
        id=orig_threat.id,
        name=orig_threat.name,
        polygon=new_poly,
        anchor=new_anch,
        due_window_s=orig_threat.due_window_s,
        service_duration_s=orig_threat.service_duration_s
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=doc.routes,
        threats=new_threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def update_threat_geometry(
    doc: CADDocument,
    threat_id: str,
    polygon: List[List[float]],
    anchor: Optional[List[float]] = None
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Updates the polygon footprint and optionally anchor of a threat."""
    t_idx = -1
    for idx, t in enumerate(doc.threats):
        if t.id == threat_id:
            t_idx = idx
            break
    if t_idx == -1:
        return doc, False, f"Threat '{threat_id}' not found."

    orig_threat = doc.threats[t_idx]
    new_poly = [[round(float(x), 4), round(float(y), 4)] for x, y in polygon]
    if new_poly[0] != new_poly[-1]:
        new_poly.append(new_poly[0])

    new_anch = anchor if anchor is not None else orig_threat.anchor
    new_anch = [round(float(new_anch[0]), 4), round(float(new_anch[1]), 4)]

    poly_b = Polygon(doc.boundary)
    pt_anch = Point(new_anch)
    poly_t = Polygon(new_poly)

    if not poly_b.contains(pt_anch) and not poly_b.covers(pt_anch):
        return doc, False, f"Threat anchor {new_anch} must lie within boundary."
    if not poly_b.contains(poly_t) and not poly_b.covers(poly_t):
        return doc, False, "Threat region must lie within boundary."

    new_threats = list(doc.threats)
    new_threats[t_idx] = CADThreat(
        id=orig_threat.id,
        name=orig_threat.name,
        polygon=new_poly,
        anchor=new_anch,
        due_window_s=orig_threat.due_window_s,
        service_duration_s=orig_threat.service_duration_s
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=doc.routes,
        threats=new_threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def update_threat_due_window(
    doc: CADDocument,
    threat_id: str,
    due_window_s: float
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Updates the due window (Delta Dj) of a threat."""
    if not math.isfinite(due_window_s) or due_window_s <= 0.0:
        return doc, False, "due_window_s must be a positive finite number."

    t_idx = -1
    for idx, t in enumerate(doc.threats):
        if t.id == threat_id:
            t_idx = idx
            break
    if t_idx == -1:
        return doc, False, f"Threat '{threat_id}' not found."

    orig_threat = doc.threats[t_idx]
    new_threats = list(doc.threats)
    new_threats[t_idx] = CADThreat(
        id=orig_threat.id,
        name=orig_threat.name,
        polygon=orig_threat.polygon,
        anchor=orig_threat.anchor,
        due_window_s=float(due_window_s),
        service_duration_s=orig_threat.service_duration_s
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=doc.routes,
        threats=new_threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def update_threat_service_duration(
    doc: CADDocument,
    threat_id: str,
    service_duration_s: float
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Updates the service duration (sj) of a threat."""
    if not math.isfinite(service_duration_s) or service_duration_s <= 0.0:
        return doc, False, "service_duration_s must be a positive finite number."

    t_idx = -1
    for idx, t in enumerate(doc.threats):
        if t.id == threat_id:
            t_idx = idx
            break
    if t_idx == -1:
        return doc, False, f"Threat '{threat_id}' not found."

    orig_threat = doc.threats[t_idx]
    new_threats = list(doc.threats)
    new_threats[t_idx] = CADThreat(
        id=orig_threat.id,
        name=orig_threat.name,
        polygon=orig_threat.polygon,
        anchor=orig_threat.anchor,
        due_window_s=orig_threat.due_window_s,
        service_duration_s=float(service_duration_s)
    )

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=doc.routes,
        threats=new_threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def delete_threat_in_document(
    doc: CADDocument,
    threat_id: str
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Deletes a threat from the document."""
    t_idx = -1
    for idx, t in enumerate(doc.threats):
        if t.id == threat_id:
            t_idx = idx
            break
    if t_idx == -1:
        return doc, False, f"Threat '{threat_id}' not found."

    new_threats = [t for t in doc.threats if t.id != threat_id]
    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=doc.player_model,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=doc.routes,
        threats=new_threats,
        ports=doc.ports
    )
    return updated_doc, True, None


def update_player_model(
    doc: CADDocument,
    initial_reticle_deg: Optional[float] = None,
    v_move_mps: Optional[float] = None,
    omega_slew_deg_per_s: Optional[float] = None,
    acquisition_latency_s: Optional[float] = None,
    service_duration_s: Optional[float] = None
) -> Tuple[CADDocument, bool, Optional[str]]:
    """Updates player movement and combat parameters in the document."""
    pm = doc.player_model
    new_pm = CADPlayerModel(
        v_move_mps=float(v_move_mps) if v_move_mps is not None else pm.v_move_mps,
        omega_slew_deg_per_s=float(omega_slew_deg_per_s) if omega_slew_deg_per_s is not None else pm.omega_slew_deg_per_s,
        acquisition_latency_s=float(acquisition_latency_s) if acquisition_latency_s is not None else pm.acquisition_latency_s,
        service_duration_s=float(service_duration_s) if service_duration_s is not None else pm.service_duration_s,
        initial_reticle_deg=float(initial_reticle_deg) if initial_reticle_deg is not None else pm.initial_reticle_deg
    )

    if new_pm.v_move_mps <= 0.0 or not math.isfinite(new_pm.v_move_mps):
        return doc, False, "v_move_mps must be a positive finite number."
    if new_pm.omega_slew_deg_per_s <= 0.0 or not math.isfinite(new_pm.omega_slew_deg_per_s):
        return doc, False, "omega_slew_deg_per_s must be a positive finite number."

    updated_doc = CADDocument(
        document_id=doc.document_id,
        name=doc.name,
        description=doc.description,
        metadata=dict(doc.metadata),
        units=dict(doc.units),
        player_model=new_pm,
        boundary=doc.boundary,
        obstacles=doc.obstacles,
        routes=doc.routes,
        threats=doc.threats,
        ports=doc.ports
    )
    return updated_doc, True, None


# =============================================================================
# GENERAL AUTHORITATIVE PYTHON ANALYSIS
# =============================================================================

def analyze_cad_document(
    doc: CADDocument,
    route_id: Optional[str] = None,
    params: Optional[TicCombatParameters] = None,
    client_revision: Optional[int] = None,
    include_telemetry: bool = False,
    max_exact_jobs: int = 7,
    allow_slow_solver: bool = False
) -> Dict[str, Any]:
    """Analyze a CAD document by compiling geometry against player motion and solving schedule.
    
    Safe Exact-Solver Envelope (M2D.1):
    - J <= 6 : EXACT_INTERACTIVE (Fast path < 10 ms)
    - J == 7 : EXACT_SLOW (Exact solve permitted but classified slow, ~80 ms; unsuitable for high-frequency interactive recomputation)
    - J >= 8 : EXACT_LIMIT_EXCEEDED (Fail-closed prompt return to avoid factorial hang, unless allow_slow_solver=True)
    """
    t_start = time.perf_counter()

    # Document-level schema and structural validation
    doc_dict = doc.to_dict()
    is_valid, errors = validate_cad_document(doc_dict)
    if not is_valid:
        return {
            "is_valid": False,
            "error_reason": f"Document schema validation failed: {'; '.join(errors)}",
            "client_revision": client_revision,
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    geo_module = doc.to_geometric_module()

    if not doc.routes:
        return {
            "is_valid": False,
            "error_reason": "No routes authored in CAD document.",
            "client_revision": client_revision,
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    # Route selection & effective combat parameters
    route_idx = 0
    if route_id is not None:
        found = False
        for idx, r in enumerate(doc.routes):
            if r.id == route_id:
                route_idx = idx
                found = True
                break
        if not found:
            return {
                "is_valid": False,
                "error_reason": f"Route ID '{route_id}' not found in document '{doc.document_id}'.",
                "client_revision": client_revision,
                "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
            }

    selected_route = doc.routes[route_idx]
    if params is None:
        effective_v_move = float(selected_route.v_move_mps) if (selected_route.v_move_mps and selected_route.v_move_mps > 0) else float(doc.player_model.v_move_mps)
        params = TicCombatParameters(
            v_move_mps=effective_v_move,
            aim_velocity_deg_s=float(doc.player_model.omega_slew_deg_per_s),
            acquisition_latency_s=float(doc.player_model.acquisition_latency_s),
            inspect_duration_s=float(doc.player_model.service_duration_s)
        )

    # 1. Authoritative Physics Extraction
    referee = DeterministicSimulationReferee(params)
    jobs = referee.extract_tic_jobs(geo_module, route_index=route_idx)
    num_jobs = len(jobs)
    dt_s = params.tic_duration_s

    # 2. Solver Envelope & Dispatch Guard (M2D.1)
    if num_jobs <= 6:
        solver_mode = "EXACT_INTERACTIVE"
        is_exact = True
        limit_exceeded = False
    elif num_jobs == 7:
        solver_mode = "EXACT_SLOW"
        is_exact = True
        limit_exceeded = False
    else:
        if allow_slow_solver or num_jobs <= max_exact_jobs:
            solver_mode = "EXACT_OVERRIDE"
            is_exact = True
            limit_exceeded = False
        else:
            solver_mode = "EXACT_LIMIT_EXCEEDED"
            is_exact = False
            limit_exceeded = True

    # 3. Inter-Threat Reveal Gaps (Generalized for N threats)
    stagger_gap_tics = 0
    if len(jobs) >= 2:
        sorted_reveals = sorted(j.reveal_tic for j in jobs)
        gaps = [sorted_reveals[i+1] - sorted_reveals[i] for i in range(len(sorted_reveals) - 1)]
        stagger_gap_tics = min(gaps) if gaps else 0

    stagger_gap_ms = round(stagger_gap_tics * dt_s * 1000.0, 1)

    # 4. Handle Limit-Exceeded Case Promptly (Fail-Closed)
    if limit_exceeded:
        threat_output_jobs = []
        for j in jobs:
            lbl = next((t.name for t in doc.threats if t.id == j.id), j.id)
            threat_output_jobs.append({
                "id": j.id,
                "label": lbl,
                "reveal_tic": j.reveal_tic,
                "reveal_s": round(j.reveal_tic * dt_s, 4),
                "due_window_tics": j.due_window_tics,
                "due_window_s": round(j.due_window_tics * dt_s, 4),
                "deadline_tic": j.deadline_tic,
                "deadline_s": round(j.deadline_tic * dt_s, 4),
                "angle_deg": round(j.angle_deg, 1),
                "service_duration_tics": j.service_duration_tics,
                "completion_tic": None,
                "scheduled_service_end_tic": None,
                "realized_service_complete_tic": None,
                "completion_s": None,
                "lateness_tics": None
            })

        diagnostic = {
            "type": "SOLVER_LIMIT_EXCEEDED",
            "critical_threat_id": None,
            "critical_threat_label": None,
            "reveal_tic": None,
            "deadline_tic": None,
            "scheduled_completion_tic": None,
            "lateness_tics": None,
            "explanation": (
                f"EXACT_LIMIT_EXCEEDED: Authoring produced {num_jobs} active revealed threats along route '{selected_route.id}'. "
                f"Exact permutation scheduler is limited to J <= {max_exact_jobs} to prevent interactive factorial server hang "
                f"(J={num_jobs} requires {math.factorial(num_jobs):,} permutations). "
                f"Simplify route sightlines or enable offline solver override."
            )
        }

        runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        return {
            "is_valid": True,
            "document_id": doc.document_id,
            "document_name": doc.name,
            "selected_route_id": selected_route.id,
            "effective_v_move_mps": params.v_move_mps,
            "client_revision": client_revision,
            "runtime_ms": runtime_ms,
            "status_band": "SOLVER_LIMIT_EXCEEDED",
            "verdict": "inconclusive",
            "tactical_margin_tics": None,
            "tactical_margin_ms": None,
            "l_star_tics": None,
            "compiled_job_count": num_jobs,
            "solver_mode": solver_mode,
            "is_exact": is_exact,
            "solver_limit": max_exact_jobs,
            "source_schedule_feasible": None,
            "stagger_gap_tics": stagger_gap_tics,
            "stagger_gap_ms": stagger_gap_ms,
            "threat_jobs": threat_output_jobs,
            "diagnostic": diagnostic,
            "candidate_document": doc.to_dict(),
            "external_engine_evidence": {
                "evidence_source": "none",
                "evidence_tier": "source_model",
                "broken_engine_survived": None,
                "repaired_engine_survived": None,
                "survival_flip": None,
                "source_repair_success": None,
                "native_engine_rescued": None,
                "transfer_status": "not_run",
                "delta_export_tics": None,
                "delta_execution_tics": None,
                "delta_total_tics": None
            },
            "model_episode_survived": None,
            "model_death_tic": None,
            "telemetry_frames": None,
            "events": None
        }

    # 5. Discrete Scheduling Solve
    scheduler = DiscreteTicScheduler(params)
    sched_res = scheduler.solve(
        jobs,
        initial_reticle_deg=doc.player_model.initial_reticle_deg,
        max_exact_jobs=max(max_exact_jobs, num_jobs),
        allow_slow_solver=True
    )

    # 6. Schedulability & Status Bands
    m_tics = sched_res.tactical_margin_tics
    source_schedule_feasible = (m_tics >= 0)

    if m_tics < 0:
        status_band = "UNSERVICEABLE"
        verdict = "unserviceable"
    elif m_tics < 2:
        status_band = "FEASIBLE — BELOW TARGET RESERVE"
        verdict = "serviceable"
    else:
        status_band = "TARGET RESERVE MET"
        verdict = "serviceable"

    # 7. Threat Jobs Output Data
    threat_output_jobs = []
    
    # Fast path defaults
    realized_complete_map: Dict[str, Optional[int]] = {j.id: None for j in jobs}
    model_episode_survived: Optional[bool] = None
    model_death_tic: Optional[int] = None
    telemetry_frames_output: Optional[List[Dict[str, Any]]] = None
    events_output: Optional[List[Dict[str, Any]]] = None

    # 8. Full Simulated Execution (Only when requested on commit)
    if include_telemetry:
        from .cad_export import _generate_telemetry_and_events
        telemetry_frames, events, stats = _generate_telemetry_and_events(
            geo_module=geo_module,
            params=params,
            policy=ControllerPolicy.ORACLE,
            route_index=route_idx,
            initial_reticle_deg=doc.player_model.initial_reticle_deg
        )
        model_episode_survived = stats.get("model_episode_survived", False)
        model_death_tic = stats.get("model_death_tic")
        telemetry_frames_output = telemetry_frames
        events_output = events

        # Populate realized completions strictly from actual controller events
        for ev in events:
            if ev.get("type") == "SERVICE_COMPLETE":
                realized_complete_map[ev["threat_id"]] = ev["tic"]

    for j in jobs:
        c_tic = sched_res.completion_tics.get(j.id, 0)
        lat_tic = sched_res.lateness_per_threat.get(j.id, 0)
        sched_end_tic = max(0, c_tic - 1)
        lbl = next((t.name for t in doc.threats if t.id == j.id), j.id)

        threat_output_jobs.append({
            "id": j.id,
            "label": lbl,
            "reveal_tic": j.reveal_tic,
            "reveal_s": round(j.reveal_tic * dt_s, 4),
            "due_window_tics": j.due_window_tics,
            "due_window_s": round(j.due_window_tics * dt_s, 4),
            "deadline_tic": j.deadline_tic,
            "deadline_s": round(j.deadline_tic * dt_s, 4),
            "angle_deg": round(j.angle_deg, 1),
            "service_duration_tics": j.service_duration_tics,
            "completion_tic": c_tic,
            "scheduled_service_end_tic": sched_end_tic,
            "realized_service_complete_tic": realized_complete_map.get(j.id),
            "completion_s": round(c_tic * dt_s, 4),
            "lateness_tics": lat_tic
        })

    # Diagnostic bottleneck explanation
    crit_id = max(sched_res.lateness_per_threat.items(), key=lambda x: x[1])[0] if sched_res.lateness_per_threat else None
    crit_label = next((t.name for t in doc.threats if t.id == crit_id), crit_id)
    crit_job = next((j for j in jobs if j.id == crit_id), None)
    
    if m_tics < 0:
        c_tic = sched_res.completion_tics.get(crit_id, 0)
        lat_tic = sched_res.lateness_per_threat.get(crit_id, 0)
        reveal_tic = crit_job.reveal_tic if crit_job else 0
        deadline_tic = crit_job.deadline_tic if crit_job else 0
        diagnostic = {
            "type": "DEADLINE_OVERLOAD",
            "critical_threat_id": crit_id,
            "critical_threat_label": crit_label,
            "reveal_tic": reveal_tic,
            "deadline_tic": deadline_tic,
            "scheduled_completion_tic": c_tic,
            "lateness_tics": lat_tic,
            "explanation": f"Deadline overload detected at '{crit_label}' (id: '{crit_id}'): revealed at tic {reveal_tic}, deadline at tic {deadline_tic}, scheduled completion at tic {c_tic} (lateness: +{lat_tic} tics, L* = {sched_res.lateness_optimal_l_star_tics} tics). Schedulability infeasible under current geometry."
        }
    else:
        diagnostic = {
            "type": "NONE",
            "critical_threat_id": None,
            "critical_threat_label": None,
            "reveal_tic": None,
            "deadline_tic": None,
            "scheduled_completion_tic": None,
            "lateness_tics": None,
            "explanation": f"All {len(jobs)} threat deadlines serviced with +{m_tics} tics reserve margin."
        }

    runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    return {
        "is_valid": True,
        "document_id": doc.document_id,
        "document_name": doc.name,
        "selected_route_id": selected_route.id,
        "effective_v_move_mps": params.v_move_mps,
        "client_revision": client_revision,
        "runtime_ms": runtime_ms,
        "status_band": status_band,
        "verdict": verdict,
        "tactical_margin_tics": m_tics,
        "tactical_margin_ms": round(m_tics * dt_s * 1000.0, 1),
        "l_star_tics": sched_res.lateness_optimal_l_star_tics,
        "compiled_job_count": num_jobs,
        "solver_mode": solver_mode,
        "is_exact": is_exact,
        "solver_limit": max_exact_jobs,
        "source_schedule_feasible": source_schedule_feasible,
        "stagger_gap_tics": stagger_gap_tics,
        "stagger_gap_ms": stagger_gap_ms,
        "threat_jobs": threat_output_jobs,
        "diagnostic": diagnostic,
        "candidate_document": doc.to_dict(),
        "external_engine_evidence": {
            "evidence_source": "none",
            "evidence_tier": "source_model",
            "broken_engine_survived": None,
            "repaired_engine_survived": None,
            "survival_flip": None,
            "source_repair_success": None,
            "native_engine_rescued": None,
            "transfer_status": "not_run",
            "delta_export_tics": None,
            "delta_execution_tics": None,
            "delta_total_tics": None
        },
        "model_episode_survived": model_episode_survived,
        "model_death_tic": model_death_tic,
        "telemetry_frames": telemetry_frames_output,
        "events": events_output,
        "heatmap_available": True
    }


# =============================================================================
# BACKWARD-COMPATIBILITY ADAPTER HELPER
# =============================================================================

def analyze_candidate_geometry(
    fixture_id: str = "canonical_f1",
    obstacle_id: int = 0,
    translation_m: float = 0.0,
    axis: str = "x",
    client_revision: int = 0,
    include_telemetry: bool = False,
    params: Optional[TicCombatParameters] = None
) -> Dict[str, Any]:
    """Compatibility adapter taking fixture ID and obstacle index."""
    t_start = time.perf_counter()

    doc = _DOCUMENT_CACHE.get(fixture_id)
    if doc is None:
        if fixture_id.startswith("RepairPop_"):
            doc = get_canonical_f1_document()
        else:
            return {
                "is_valid": False,
                "error_reason": f"Document / Fixture '{fixture_id}' not found.",
                "client_revision": client_revision,
                "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
            }

    if obstacle_id < 0 or obstacle_id >= len(doc.obstacles):
        return {
            "is_valid": False,
            "error_reason": f"Invalid obstacle_id {obstacle_id}; document has {len(doc.obstacles)} obstacles.",
            "client_revision": client_revision,
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    target_obs_id = doc.obstacles[obstacle_id].id
    dx = float(translation_m) if axis.lower() == "x" else 0.0
    dy = float(translation_m) if axis.lower() == "y" else 0.0

    if axis.lower() not in ("x", "y"):
        return {
            "is_valid": False,
            "error_reason": f"Axis must be 'x' or 'y'; received '{axis}'.",
            "client_revision": client_revision,
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    trans_doc, is_valid, error_reason = translate_obstacle_in_document(doc, target_obs_id, dx, dy)
    if not is_valid:
        return {
            "is_valid": False,
            "error_reason": error_reason,
            "client_revision": client_revision,
            "translation_m": round(translation_m, 4),
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    res = analyze_cad_document(
        doc=trans_doc,
        include_telemetry=include_telemetry,
        client_revision=client_revision,
        params=params
    )
    # Echo requested translation parameter
    res["translation_m"] = round(translation_m, 4)
    res["obstacle_id"] = obstacle_id
    res["axis"] = axis
    
    # Backwards compatibility key for r1 / r2
    if len(res["threat_jobs"]) >= 1:
        res["r1_reveal_tic"] = res["threat_jobs"][0]["reveal_tic"]
    if len(res["threat_jobs"]) >= 2:
        res["r2_reveal_tic"] = res["threat_jobs"][1]["reveal_tic"]
    
    # Backwards compatibility candidate geometry
    res["candidate_geometry"] = {
        "boundary": trans_doc.boundary,
        "obstacles": [
            {
                "id": obs.id,
                "name": obs.name,
                "vertices": obs.vertices
            }
            for obs in trans_doc.obstacles
        ],
        "route": {
            "route_id": trans_doc.routes[0].id,
            "waypoints": trans_doc.routes[0].waypoints,
            "total_length_m": 10.0
        },
        "threats": [
            {
                "id": t.id,
                "label": t.name,
                "polygon": t.polygon,
                "anchor": t.anchor
            }
            for t in trans_doc.threats
        ]
    }
    return res
# =============================================================================
# AUTO-FIX MIXED-INITIATIVE REPAIR OPTIMIZER (M2E)
# =============================================================================
 
def auto_fix_cad_document(
    doc: CADDocument,
    target_margin_tics: int = 2,
    max_perturbation_m: float = 2.0,
    search_resolution_m: float = 0.05,
    max_exact_jobs: int = 6,
    route_id: Optional[str] = None,
    params: Optional[TicCombatParameters] = None
) -> Dict[str, Any]:
    """Execute grid-minimal Auto-Fix repair optimization on a CADDocument.
 
    M2E Candidate Evaluation Tri-State Policy:
    - EXACT_EVALUATED (J <= max_exact_jobs): Exact schedule evaluated, L*, M computed.
    - UNSUPPORTED_ENVELOPE (J > max_exact_jobs): Candidate excluded from consideration without penalty.
    - INVALID_GEOMETRY: Boundary or clearance violation rejected.
    """
    t_start = time.perf_counter()
 
    # Route resolution & combat parameter extraction (identically to analyze_cad_document)
    if not doc.routes:
        runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        return {
            "success": False,
            "status": "INVALID_INITIAL_DOCUMENT",
            "error_reason": "Document has no authored routes.",
            "initial_margin_tics": None,
            "repaired_margin_tics": None,
            "edit_distance_m": 0.0,
            "target_margin_tics": target_margin_tics,
            "controlling_obstacle_id": None,
            "controlling_obstacle_name": None,
            "translation_vector": [0.0, 0.0],
            "repair_description": "Document has no authored routes.",
            "repaired_document": None,
            "evaluations_count": 0,
            "evaluations_breakdown": {"exact_evaluated": 0, "unsupported_envelope": 0, "invalid_geometry": 1},
            "runtime_ms": runtime_ms,
            "no_repair_needed": False,
            "initial_analysis": None,
            "repaired_analysis": None
        }

    route_idx = 0
    if route_id is not None:
        found = False
        for idx, r in enumerate(doc.routes):
            if r.id == route_id:
                route_idx = idx
                found = True
                break
        if not found:
            runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            return {
                "success": False,
                "status": "INVALID_ROUTE",
                "error_reason": f"Route ID '{route_id}' not found in document '{doc.document_id}'.",
                "initial_margin_tics": None,
                "repaired_margin_tics": None,
                "edit_distance_m": 0.0,
                "target_margin_tics": target_margin_tics,
                "controlling_obstacle_id": None,
                "controlling_obstacle_name": None,
                "translation_vector": [0.0, 0.0],
                "repair_description": f"Route ID '{route_id}' not found in document.",
                "repaired_document": None,
                "evaluations_count": 0,
                "evaluations_breakdown": {"exact_evaluated": 0, "unsupported_envelope": 0, "invalid_geometry": 1},
                "runtime_ms": runtime_ms,
                "no_repair_needed": False,
                "initial_analysis": None,
                "repaired_analysis": None
            }

    selected_route = doc.routes[route_idx]
    if params is None:
        effective_v_move = float(selected_route.v_move_mps) if (selected_route.v_move_mps and selected_route.v_move_mps > 0) else float(doc.player_model.v_move_mps)
        combat_params = TicCombatParameters(
            v_move_mps=effective_v_move,
            aim_velocity_deg_s=float(doc.player_model.omega_slew_deg_per_s),
            acquisition_latency_s=float(doc.player_model.acquisition_latency_s),
            inspect_duration_s=float(doc.player_model.service_duration_s)
        )
    else:
        combat_params = params

    initial_reticle_deg = float(doc.player_model.initial_reticle_deg)

    # Initial authoritative analysis
    initial_analysis = analyze_cad_document(
        doc,
        route_id=selected_route.id,
        params=combat_params,
        include_telemetry=False,
        max_exact_jobs=max_exact_jobs
    )
 
    if not initial_analysis.get("is_valid", False):
        runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        return {
            "success": False,
            "status": "INVALID_INITIAL_DOCUMENT",
            "error_reason": initial_analysis.get("error_reason", "Document validation failed."),
            "initial_margin_tics": None,
            "repaired_margin_tics": None,
            "edit_distance_m": 0.0,
            "target_margin_tics": target_margin_tics,
            "controlling_obstacle_id": None,
            "controlling_obstacle_name": None,
            "translation_vector": [0.0, 0.0],
            "repair_description": "Initial document failed validation.",
            "repaired_document": None,
            "evaluations_count": 1,
            "evaluations_breakdown": {
                "exact_evaluated": 0,
                "unsupported_envelope": 0,
                "invalid_geometry": 1
            },
            "runtime_ms": runtime_ms,
            "no_repair_needed": False,
            "initial_analysis": initial_analysis,
            "repaired_analysis": None
        }
 
    initial_margin = initial_analysis.get("tactical_margin_tics")
    solver_mode = initial_analysis.get("solver_mode")
    compiled_jobs = initial_analysis.get("compiled_job_count", 0)
 
    # Check if over initial solver envelope (M2D.1 fail-closed boundary)
    if solver_mode == "EXACT_LIMIT_EXCEEDED" or initial_margin is None or compiled_jobs > max_exact_jobs:
        runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        return {
            "success": False,
            "status": "UNSUPPORTED_BASELINE_ENVELOPE",
            "error_reason": f"Initial document has {compiled_jobs} threats, exceeding exact envelope J <= {max_exact_jobs}.",
            "initial_margin_tics": None,
            "repaired_margin_tics": None,
            "edit_distance_m": 0.0,
            "target_margin_tics": target_margin_tics,
            "controlling_obstacle_id": None,
            "controlling_obstacle_name": None,
            "translation_vector": [0.0, 0.0],
            "repair_description": f"Initial encounter exceeds exact analysis envelope (J={compiled_jobs} > {max_exact_jobs}).",
            "repaired_document": None,
            "evaluations_count": 1,
            "evaluations_breakdown": {
                "exact_evaluated": 0,
                "unsupported_envelope": 1,
                "invalid_geometry": 0
            },
            "runtime_ms": runtime_ms,
            "no_repair_needed": False,
            "initial_analysis": initial_analysis,
            "repaired_analysis": None
        }
 
    # Check if already serviceable
    if initial_margin >= target_margin_tics:
        runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        return {
            "success": False,
            "status": "ALREADY_SERVICEABLE",
            "error_reason": None,
            "initial_margin_tics": initial_margin,
            "repaired_margin_tics": initial_margin,
            "edit_distance_m": 0.0,
            "target_margin_tics": target_margin_tics,
            "controlling_obstacle_id": None,
            "controlling_obstacle_name": None,
            "translation_vector": [0.0, 0.0],
            "repair_description": f"Document already meets target margin (M = {initial_margin} tics >= {target_margin_tics} tics). No repair needed.",
            "repaired_document": doc.to_dict(),
            "evaluations_count": 1,
            "evaluations_breakdown": {
                "exact_evaluated": 1,
                "unsupported_envelope": 0,
                "invalid_geometry": 0
            },
            "runtime_ms": runtime_ms,
            "no_repair_needed": True,
            "initial_analysis": initial_analysis,
            "repaired_analysis": initial_analysis
        }
 
    # If no obstacles to move
    if not doc.obstacles:
        runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        return {
            "success": False,
            "status": "NO_CONTROLLING_OBSTACLES",
            "error_reason": "No obstacles found in document to perturb.",
            "initial_margin_tics": initial_margin,
            "repaired_margin_tics": initial_margin,
            "edit_distance_m": 0.0,
            "target_margin_tics": target_margin_tics,
            "controlling_obstacle_id": None,
            "controlling_obstacle_name": None,
            "translation_vector": [0.0, 0.0],
            "repair_description": "Failed: Document has no obstacles available to reposition.",
            "repaired_document": doc.to_dict(),
            "evaluations_count": 1,
            "evaluations_breakdown": {
                "exact_evaluated": 1,
                "unsupported_envelope": 0,
                "invalid_geometry": 0
            },
            "runtime_ms": runtime_ms,
            "no_repair_needed": False,
            "initial_analysis": initial_analysis,
            "repaired_analysis": None
        }
 
    referee = DeterministicSimulationReferee(combat_params)
    scheduler = DiscreteTicScheduler(combat_params)
 
    geo_base = doc.to_geometric_module()
    diag = diagnose_clearability(
        geo_base,
        target_margin_tics=target_margin_tics,
        params=combat_params,
        route_index=route_idx,
        initial_reticle_deg=initial_reticle_deg
    )
 
    norm_x, norm_y = diag.suggested_perturbation_normal or (1.0, 0.0)
    candidate_directions = [
        (norm_x, norm_y),
        (-norm_x, -norm_y),
        (1.0, 0.0), (-1.0, 0.0),
        (0.0, 1.0), (0.0, -1.0)
    ]
 
    # Deduplicate directions
    unique_dirs = []
    for dx, dy in candidate_directions:
        l = math.hypot(dx, dy)
        if l < 1e-4:
            continue
        ndx, ndy = round(dx / l, 4), round(dy / l, 4)
        if (ndx, ndy) not in unique_dirs:
            unique_dirs.append((ndx, ndy))
 
    # Prioritize controlling obstacle index if found
    candidate_obs_indices = list(range(len(doc.obstacles)))
    if diag.controlling_obstacle_idx is not None and 0 <= diag.controlling_obstacle_idx < len(doc.obstacles):
        # Move controlling obstacle to front of search
        candidate_obs_indices.remove(diag.controlling_obstacle_idx)
        candidate_obs_indices.insert(0, diag.controlling_obstacle_idx)
 
    best_repaired_doc: Optional[CADDocument] = None
    best_edit_dist = float('inf')
    best_margin = initial_margin
    best_obs_id = None
    best_obs_name = None
    best_trans_vec = [0.0, 0.0]
    best_desc = ""
 
    eval_breakdown = {
        "exact_evaluated": 1,  # initial run
        "unsupported_envelope": 0,
        "invalid_geometry": 0
    }
 
    displacements = np.arange(search_resolution_m, max_perturbation_m + 1e-6, search_resolution_m)
 
    for obs_idx in candidate_obs_indices:
        target_obs = doc.obstacles[obs_idx]
        obs_id = target_obs.id
        obs_name = target_obs.name
 
        for dir_x, dir_y in unique_dirs:
            for d in displacements:
                d_float = round(float(d), 4)
                if d_float >= best_edit_dist:
                    break
 
                shift_x = round(float(d_float * dir_x), 4)
                shift_y = round(float(d_float * dir_y), 4)
 
                cand_doc, is_valid, err_msg = translate_obstacle_in_document(doc, obs_id, shift_x, shift_y)
                if not is_valid:
                    eval_breakdown["invalid_geometry"] += 1
                    continue
 
                # Compile threat jobs on candidate
                cand_geo = cand_doc.to_geometric_module()
                pres_errs = validate_repair_preservation(geo_base, cand_geo)
                if pres_errs:
                    eval_breakdown["invalid_geometry"] += 1
                    continue
 
                cand_jobs = referee.extract_tic_jobs(cand_geo, route_index=route_idx)
                cand_num_jobs = len(cand_jobs)
 
                if cand_num_jobs > max_exact_jobs:
                    eval_breakdown["unsupported_envelope"] += 1
                    continue
 
                eval_breakdown["exact_evaluated"] += 1
                try:
                    cand_sched = scheduler.solve(
                        cand_jobs,
                        initial_reticle_deg=initial_reticle_deg,
                        max_exact_jobs=max_exact_jobs,
                        allow_slow_solver=False
                    )
                    cand_margin = cand_sched.tactical_margin_tics
                except ValueError:
                    eval_breakdown["unsupported_envelope"] += 1
                    continue
 
                if cand_margin >= target_margin_tics:
                    if d_float < best_edit_dist or (abs(d_float - best_edit_dist) < 1e-6 and cand_margin > best_margin):
                        best_edit_dist = d_float
                        best_repaired_doc = cand_doc
                        best_margin = cand_margin
                        best_obs_id = obs_id
                        best_obs_name = obs_name
                        best_trans_vec = [shift_x, shift_y]
                        best_desc = (
                            f"Shift '{obs_name}' by {d_float:.2f}m along vector ({dir_x:+.2f}, {dir_y:+.2f}) "
                            f"(dx={shift_x:+.2f}m, dy={shift_y:+.2f}m) -> Margin M = {cand_margin} tics."
                        )
                    # Found minimal perturbation along this specific ray
                    break
 
    total_evals = sum(eval_breakdown.values())
    runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
 
    if best_repaired_doc is not None:
        # Authoritative independent re-certification via analyze_cad_document
        cert_analysis = analyze_cad_document(
            best_repaired_doc,
            route_id=selected_route.id,
            params=combat_params,
            include_telemetry=True,
            max_exact_jobs=max_exact_jobs
        )
        cert_margin = cert_analysis.get("tactical_margin_tics")
 
        if not cert_analysis.get("is_valid", False) or cert_margin is None or cert_margin < target_margin_tics:
            # Certification rejected candidate
            return {
                "success": False,
                "status": "CERTIFICATION_FAILED",
                "error_reason": (
                    f"Optimizer candidate L* achieved M = {best_margin}, but authoritative "
                    f"certification analysis returned M = {cert_margin} (< target {target_margin_tics} tics)."
                ),
                "initial_margin_tics": initial_margin,
                "repaired_margin_tics": cert_margin,
                "edit_distance_m": best_edit_dist,
                "target_margin_tics": target_margin_tics,
                "controlling_obstacle_id": best_obs_id,
                "controlling_obstacle_name": best_obs_name,
                "translation_vector": best_trans_vec,
                "repair_description": f"Certification rejected candidate: M={cert_margin} < target {target_margin_tics}.",
                "repaired_document": best_repaired_doc.to_dict(),
                "evaluations_count": total_evals,
                "evaluations_breakdown": eval_breakdown,
                "runtime_ms": runtime_ms,
                "no_repair_needed": False,
                "initial_analysis": initial_analysis,
                "repaired_analysis": cert_analysis
            }
 
        return {
            "success": True,
            "status": "REPAIR_FOUND",
            "error_reason": None,
            "initial_margin_tics": initial_margin,
            "repaired_margin_tics": cert_margin,
            "edit_distance_m": best_edit_dist,
            "target_margin_tics": target_margin_tics,
            "controlling_obstacle_id": best_obs_id,
            "controlling_obstacle_name": best_obs_name,
            "translation_vector": best_trans_vec,
            "repair_description": best_desc,
            "repaired_document": best_repaired_doc.to_dict(),
            "evaluations_count": total_evals,
            "evaluations_breakdown": eval_breakdown,
            "runtime_ms": runtime_ms,
            "no_repair_needed": False,
            "initial_analysis": initial_analysis,
            "repaired_analysis": cert_analysis
        }
    else:
        return {
            "success": False,
            "status": "REPAIR_NOT_FOUND",
            "error_reason": f"Could not achieve M >= {target_margin_tics} tics within {max_perturbation_m}m budget.",
            "initial_margin_tics": initial_margin,
            "repaired_margin_tics": initial_margin,
            "edit_distance_m": 0.0,
            "target_margin_tics": target_margin_tics,
            "controlling_obstacle_id": None,
            "controlling_obstacle_name": None,
            "translation_vector": [0.0, 0.0],
            "repair_description": f"Repair failed: Could not achieve M >= {target_margin_tics} tics within {max_perturbation_m}m perturbation budget across {total_evals} candidate evaluations.",
            "repaired_document": doc.to_dict(),
            "evaluations_count": total_evals,
            "evaluations_breakdown": eval_breakdown,
            "runtime_ms": runtime_ms,
            "no_repair_needed": False,
            "initial_analysis": initial_analysis,
            "repaired_analysis": None
        }


# =============================================================================
# MILESTONE 2F: LIVE SPATIAL HEATMAP & SUFFIX TACTICAL MARGIN
# =============================================================================

def compute_cad_route_spatial_heatmap(
    doc: CADDocument,
    route_id: Optional[str] = None,
    params: Optional[TicCombatParameters] = None,
    allow_slow_solver: bool = False,
    max_exact_jobs: int = 7
) -> Dict[str, Any]:
    """Compute discrete-tic counterfactual suffix Tactical Margin and LOS metrics along authored route (M2F-A).
    
    Mathematical Invariants:
    1. Entrance Equivalence: M_suffix(0) == M_authoritative (identical full-route baseline).
    2. Suffix Formulation: Suffix at tic k re-evaluates remaining reveal timeline [k, N] with
       due windows and authored initial_reticle_deg.
    3. 5-Band Status Classification:
       - QUIESCENT: J_suffix == 0 (no upcoming threats on suffix) -> #64748b
       - SAFE: J_suffix > 0 and M_suffix >= +2 -> #22c55e
       - CONTESTED: J_suffix > 0 and 0 <= M_suffix < 2 -> #eab308
       - CRITICAL: J_suffix > 0 and M_suffix < 0 -> #ef4444
       - UNSUPPORTED: J_full > 6 (unless slow solver explicitly allowed) -> #a855f7
    4. Orthogonal Metrics:
       - Suffix M: -L*(suffix_jobs; theta_0)
       - Minimum active deadline headroom delta_min(k) = min_{j in A_k} (D_j - k)
       - Instantaneous LOS Concurrency K(k) = sum_j LOS[k, j]
    """
    t_start = time.perf_counter()

    doc_dict = doc.to_dict()
    is_valid, errors = validate_cad_document(doc_dict)
    if not is_valid:
        return {
            "is_valid": False,
            "error_reason": f"Document schema validation failed: {'; '.join(errors)}",
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    if not doc.routes:
        return {
            "is_valid": False,
            "error_reason": "No routes authored in CAD document.",
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    route_idx = 0
    if route_id is not None:
        found = False
        for idx, r in enumerate(doc.routes):
            if r.id == route_id:
                route_idx = idx
                found = True
                break
        if not found:
            return {
                "is_valid": False,
                "error_reason": f"Route ID '{route_id}' not found in document '{doc.document_id}'.",
                "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
            }

    selected_route = doc.routes[route_idx]
    if params is None:
        effective_v_move = float(selected_route.v_move_mps) if (selected_route.v_move_mps and selected_route.v_move_mps > 0) else float(doc.player_model.v_move_mps)
        params = TicCombatParameters(
            v_move_mps=effective_v_move,
            aim_velocity_deg_s=float(doc.player_model.omega_slew_deg_per_s),
            acquisition_latency_s=float(doc.player_model.acquisition_latency_s),
            inspect_duration_s=float(doc.player_model.service_duration_s)
        )

    geo_module = doc.to_geometric_module()
    geo_route = geo_module.routes[route_idx]
    dt_s = params.tic_duration_s
    total_length_m = geo_route.total_length_m
    total_tics = max(1, int(math.ceil(total_length_m / params.move_m_per_tic)))

    referee = DeterministicSimulationReferee(params)
    full_jobs = referee.extract_tic_jobs(geo_module, route_index=route_idx)
    num_full_jobs = len(full_jobs)
    full_job_map = {j.id: j for j in full_jobs}

    obs_segs = extract_polygon_segments(geo_module.obstacles)

    # 1. Precompute Route Line-of-Sight Matrix LOS[k, j]
    num_threats = len(geo_module.threats)
    los_matrix = np.zeros((total_tics + 1, num_threats), dtype=int)
    sample_positions = []
    sample_headings = []
    sample_distances = []

    for k in range(total_tics + 1):
        s_k = min(k * params.move_m_per_tic, total_length_m)
        pos_k = geo_route.position_at_distance(s_k)
        heading_k = geo_route.forward_heading_at_distance(s_k)
        sample_distances.append(s_k)
        sample_positions.append(pos_k)
        sample_headings.append(heading_k)

        for j_idx, threat in enumerate(geo_module.threats):
            qx, qy = threat.threat_anchor
            blocked = False
            for s1, s2 in obs_segs:
                if segments_intersect(pos_k, (qx, qy), s1, s2):
                    blocked = True
                    break
            if not blocked:
                los_matrix[k, j_idx] = 1

    # 2. Solver Envelope Policy
    is_envelope_unsupported = (num_full_jobs > 6 and not allow_slow_solver and num_full_jobs > max_exact_jobs)

    scheduler = DiscreteTicScheduler(params)
    samples: List[Dict[str, Any]] = []

    for k in range(total_tics + 1):
        s_k = sample_distances[k]
        pos_k = sample_positions[k]
        heading_k = sample_headings[k]

        # Active visible threats at current position
        active_threat_indices = [j_idx for j_idx in range(num_threats) if los_matrix[k, j_idx] == 1]
        active_threat_ids = [geo_module.threats[j_idx].id for j_idx in active_threat_indices]
        los_k = len(active_threat_ids)

        # Minimum active deadline headroom delta_min(k)
        headrooms = []
        for t_id in active_threat_ids:
            if t_id in full_job_map:
                fj = full_job_map[t_id]
                headrooms.append(fj.deadline_tic - k)
        min_headroom_tics = min(headrooms) if headrooms else None

        # Build suffix encounter starting at tic k
        suffix_jobs: List[TicThreatJob] = []
        for j_idx, threat in enumerate(geo_module.threats):
            # Scan forward from k to find first visible tic on suffix
            vis_indices = np.where(los_matrix[k:, j_idx] == 1)[0]
            if len(vis_indices) > 0:
                rel_reveal = int(vis_indices[0])  # relative to k
                abs_reveal = k + rel_reveal
                s_rev = min(abs_reveal * params.move_m_per_tic, total_length_m)
                pos_rev = geo_route.position_at_distance(s_rev)
                fwd_rev = geo_route.forward_heading_at_distance(s_rev)

                qx, qy = threat.threat_anchor
                target_heading = heading_to_deg(pos_rev, (qx, qy))
                vis_angle_deg = normalize_angle_deg(target_heading - fwd_rev)

                due_window_tics = int(math.ceil(threat.authored_due_window_s * params.ticrate_hz))
                serv_dur_tics = int(math.ceil(threat.service_duration_s * params.ticrate_hz))
                deadline_tic = rel_reveal + due_window_tics

                suffix_jobs.append(TicThreatJob(
                    id=threat.id,
                    reveal_tic=rel_reveal,
                    due_window_tics=due_window_tics,
                    deadline_tic=deadline_tic,
                    angle_deg=round(vis_angle_deg, 2),
                    threat_anchor=(float(qx), float(qy)),
                    service_duration_tics=serv_dur_tics
                ))

        suffix_jobs.sort(key=lambda j: j.reveal_tic)
        num_suffix_jobs = len(suffix_jobs)

        if is_envelope_unsupported:
            status_band = "UNSUPPORTED"
            suffix_margin_tics = None
            color = "#a855f7"
        elif num_suffix_jobs == 0:
            status_band = "QUIESCENT"
            suffix_margin_tics = None
            color = "#64748b"
        else:
            try:
                sched_res = scheduler.solve(
                    suffix_jobs,
                    initial_reticle_deg=doc.player_model.initial_reticle_deg,
                    allow_slow_solver=True
                )
                suffix_margin_tics = sched_res.tactical_margin_tics
                if suffix_margin_tics < 0:
                    status_band = "CRITICAL"
                    color = "#ef4444"
                elif suffix_margin_tics < 2:
                    status_band = "CONTESTED"
                    color = "#eab308"
                else:
                    status_band = "SAFE"
                    color = "#22c55e"
            except Exception:
                status_band = "UNSUPPORTED"
                suffix_margin_tics = None
                color = "#a855f7"

        samples.append({
            "tic": k,
            "time_s": round(k * dt_s, 4),
            "distance_m": round(float(s_k), 4),
            "position": [round(float(pos_k[0]), 4), round(float(pos_k[1]), 4)],
            "forward_heading_deg": round(float(heading_k), 1),
            "los_concurrency": los_k,
            "visible_threat_ids": active_threat_ids,
            "suffix_job_count": num_suffix_jobs,
            "suffix_margin_tics": suffix_margin_tics,
            "min_deadline_headroom_tics": min_headroom_tics,
            "status_band": status_band,
            "color": color
        })

    runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
    doc_hash = doc.compute_hash()

    return {
        "is_valid": True,
        "document_id": doc.document_id,
        "source_doc_hash": doc_hash,
        "route_id": selected_route.id,
        "sampling_mode": "tic",
        "tic_duration_s": dt_s,
        "total_tics": total_tics,
        "total_length_m": round(float(total_length_m), 4),
        "v_move_mps": params.v_move_mps,
        "full_compiled_job_count": num_full_jobs,
        "envelope_supported": not is_envelope_unsupported,
        "samples": samples,
        "runtime_ms": runtime_ms
    }


def compute_arena_floor_los_exposure(
    doc: CADDocument,
    grid_step_m: float = 0.25
) -> Dict[str, Any]:
    """Compute 2D arena floor Line-of-Sight Exposure Density field K(x, y) (M2F-B).
    
    Epistemic Boundary:
    - Measures instantaneous geometric LOS exposure count: K(x, y) = |{j: LOS((x, y), q_j) == 1}|.
    - Strictly does NOT represent tactical margin or feasibility.
    - Masks points outside the boundary polygon or inside obstacle interior polygons.
    """
    t_start = time.perf_counter()

    doc_dict = doc.to_dict()
    is_valid, errors = validate_cad_document(doc_dict)
    if not is_valid:
        return {
            "is_valid": False,
            "error_reason": f"Document schema validation failed: {'; '.join(errors)}",
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    geo_module = doc.to_geometric_module()
    boundary_poly = geo_module.boundary
    minx, miny, maxx, maxy = boundary_poly.bounds
    obs_polys = geo_module.obstacles
    obs_segs = extract_polygon_segments(obs_polys)

    xs = np.arange(minx, maxx + 1e-4, grid_step_m)
    ys = np.arange(miny, maxy + 1e-4, grid_step_m)

    grid_cells: List[Dict[str, Any]] = []
    max_exposure = 0

    for y in ys:
        for x in xs:
            pt = Point(float(x), float(y))
            # Boundary containment and obstacle interior check
            if not boundary_poly.contains(pt) or any(obs.contains(pt) for obs in obs_polys):
                grid_cells.append({
                    "x": round(float(x), 3),
                    "y": round(float(y), 3),
                    "masked": True,
                    "exposure_count": 0,
                    "visible_threat_ids": []
                })
            else:
                vis_threats = []
                for threat in geo_module.threats:
                    qx, qy = threat.threat_anchor
                    blocked = False
                    for s1, s2 in obs_segs:
                        if segments_intersect((float(x), float(y)), (qx, qy), s1, s2):
                            blocked = True
                            break
                    if not blocked:
                        vis_threats.append(threat.id)

                exp_cnt = len(vis_threats)
                if exp_cnt > max_exposure:
                    max_exposure = exp_cnt

                grid_cells.append({
                    "x": round(float(x), 3),
                    "y": round(float(y), 3),
                    "masked": False,
                    "exposure_count": exp_cnt,
                    "visible_threat_ids": vis_threats
                })

    runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
    doc_hash = doc.compute_hash()

    return {
        "is_valid": True,
        "document_id": doc.document_id,
        "source_doc_hash": doc_hash,
        "grid_step_m": grid_step_m,
        "bounds": [round(minx, 3), round(miny, 3), round(maxx, 3), round(maxy, 3)],
        "nx": len(xs),
        "ny": len(ys),
        "total_cells": len(grid_cells),
        "max_exposure": max_exposure,
        "cells": grid_cells,
        "runtime_ms": runtime_ms
    }
