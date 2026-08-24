"""Geometric primitives, raycasting, angular math, and finite-disk visibility [G]."""

from __future__ import annotations
import math
from typing import List, Tuple, Optional
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union


def normalize_angle_deg(angle: float) -> float:
    """Normalize angle to [-180, 180) degrees."""
    a = (angle + 180.0) % 360.0 - 180.0
    return a if a != -180.0 else 180.0


def angle_diff_deg(a1: float, a2: float) -> float:
    """Smallest absolute angular difference in degrees between two headings [0, 180]."""
    diff = normalize_angle_deg(a1 - a2)
    return abs(diff)


def spherical_aim_distance_deg(
    theta_i: float,
    phi_i: float,
    theta_j: float,
    phi_j: float
) -> float:
    """Compute shortest angular slew distance between two 3D aim states (theta, phi) in degrees.
    
    Guarantees bit-for-bit identity with frozen 2D angle_diff_deg when both elevations are 0.0.
    """
    if phi_i == 0.0 and phi_j == 0.0:
        return angle_diff_deg(theta_i, theta_j)  # Exact frozen M2 planar fast-path

    # 3D Spherical geodesic distance on unit sphere
    rad = math.pi / 180.0
    th_i, ph_i = theta_i * rad, phi_i * rad
    th_j, ph_j = theta_j * rad, phi_j * rad
    dot = math.sin(ph_i) * math.sin(ph_j) + math.cos(ph_i) * math.cos(ph_j) * math.cos(th_i - th_j)
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))



def heading_to_deg(from_pt: Tuple[float, float], to_pt: Tuple[float, float]) -> float:
    """Calculate heading angle in degrees from from_pt to to_pt (0 deg = +X, 90 deg = +Y)."""
    dx = to_pt[0] - from_pt[0]
    dy = to_pt[1] - from_pt[1]
    rad = math.atan2(dy, dx)
    return math.degrees(rad)


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Euclidean distance between two 2D points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
    """Fast pure-float 2D segment-segment intersection test with bounding box rejection."""
    x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4

    # Bounding box rejection
    if max(x1, x2) < min(x3, x4) or min(x1, x2) > max(x3, x4) or max(y1, y2) < min(y3, y4) or min(y1, y2) > max(y3, y4):
        return False

    d1 = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
    d2 = (x4 - x3) * (y2 - y3) - (y4 - y3) * (x2 - x3)
    d3 = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
    d4 = (x2 - x1) * (y4 - y1) - (y2 - y1) * (x4 - x1)

    return (d1 * d2 < 0.0) and (d3 * d4 < 0.0)


def derived_aim_elevation_deg(
    eye_pt: Tuple[float, float, float],
    target_pt: Tuple[float, float, float]
) -> float:
    """Compute derived aim elevation angle phi in degrees from eye position to target position."""
    dx = target_pt[0] - eye_pt[0]
    dy = target_pt[1] - eye_pt[1]
    dz = target_pt[2] - eye_pt[2]
    d_xy = math.hypot(dx, dy)
    return math.degrees(math.atan2(dz, d_xy))


def segment_crosses_prism_face_25d(
    p1: Tuple[float, float, float],
    p2: Tuple[float, float, float],
    s1: Tuple[float, float],
    s2: Tuple[float, float],
    z_min: float = 0.0,
    z_max: float = float("inf")
) -> bool:
    """Check if 3D segment [p1, p2] intersects a vertical prism face spanning 2D segment [s1, s2] and z in [z_min, z_max]."""
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    x3, y3 = s1
    x4, y4 = s2

    # Bounding box rejection in 2D
    if max(x1, x2) < min(x3, x4) or min(x1, x2) > max(x3, x4) or max(y1, y2) < min(y3, y4) or min(y1, y2) > max(y3, y4):
        return False

    # 2D cross-product orientation test
    d1 = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
    d2 = (x4 - x3) * (y2 - y3) - (y4 - y3) * (x2 - x3)
    d3 = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
    d4 = (x2 - x1) * (y4 - y1) - (y2 - y1) * (x4 - x1)

    if not ((d1 * d2 < 0.0) and (d3 * d4 < 0.0)):
        return False

    # If z_min is -inf/0 and z_max is +inf (planar infinite obstacle), crossing in 2D is guaranteed blocked
    if math.isinf(z_max) and (math.isinf(z_min) or z_min <= min(z1, z2)):
        return True

    # Compute fractional distance t in [0, 1] along ray p1 -> p2
    denom = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if abs(denom) < 1e-12:
        return False
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / denom
    if t < 0.0 or t > 1.0:
        return False

    z_cross = z1 + t * (z2 - z1)
    return (z_min - 1e-6) <= z_cross <= (z_max + 1e-6)


def ray_intersects_prism_25d(
    p1: Tuple[float, float, float],
    p2: Tuple[float, float, float],
    polygon: Polygon,
    z_min: float = 0.0,
    z_max: float = float("inf")
) -> bool:
    """Check if 3D segment [p1, p2] intersects an extruded 2.5D closed prism volume P x [z_min, z_max]."""
    x1, y1, z1 = p1
    x2, y2, z2 = p2

    pt1_2d = Point(x1, y1)
    pt2_2d = Point(x2, y2)

    # 1. Endpoint Volumetric Containment
    if (z_min - 1e-6) <= z1 <= (z_max + 1e-6) and (polygon.contains(pt1_2d) or polygon.touches(pt1_2d)):
        return True
    if (z_min - 1e-6) <= z2 <= (z_max + 1e-6) and (polygon.contains(pt2_2d) or polygon.touches(pt2_2d)):
        return True

    # 2. 2D Segment vs Polygon Intersection
    seg_2d = LineString([(x1, y1), (x2, y2)])
    if not polygon.intersects(seg_2d):
        return False

    inter = polygon.intersection(seg_2d)
    if inter.is_empty:
        return False

    d_xy_total = math.hypot(x2 - x1, y2 - y1)
    if d_xy_total < 1e-9:
        # Pure vertical segment at fixed (x, y)
        if polygon.contains(pt1_2d) or polygon.touches(pt1_2d):
            z_low, z_high = min(z1, z2), max(z1, z2)
            return z_high >= (z_min - 1e-6) and z_low <= (z_max + 1e-6)
        return False

    # Extract all geometric sub-components (Points and LineStrings)
    geoms = []
    if inter.geom_type in ("Point", "LineString"):
        geoms = [inter]
    elif inter.geom_type in ("MultiPoint", "MultiLineString", "GeometryCollection"):
        geoms = list(inter.geoms)

    for g in geoms:
        if g.geom_type == "Point":
            gx, gy = g.x, g.y
            if abs(x2 - x1) > abs(y2 - y1):
                t = (gx - x1) / (x2 - x1)
            else:
                t = (gy - y1) / (y2 - y1)
            t = max(0.0, min(1.0, t))
            z_val = z1 + t * (z2 - z1)
            if (z_min - 1e-6) <= z_val <= (z_max + 1e-6):
                return True
        elif g.geom_type == "LineString":
            coords = list(g.coords)
            for c in coords:
                cx, cy = c[0], c[1]
                if abs(x2 - x1) > abs(y2 - y1):
                    t = (cx - x1) / (x2 - x1)
                else:
                    t = (cy - y1) / (y2 - y1)
                t = max(0.0, min(1.0, t))
                z_val = z1 + t * (z2 - z1)
                if (z_min - 1e-6) <= z_val <= (z_max + 1e-6):
                    return True
            # Check if z-range of the sub-segment overlaps [z_min, z_max]
            t_vals = []
            for c in (coords[0], coords[-1]):
                if abs(x2 - x1) > abs(y2 - y1):
                    t_vals.append(max(0.0, min(1.0, (c[0] - x1) / (x2 - x1))))
                else:
                    t_vals.append(max(0.0, min(1.0, (c[1] - y1) / (y2 - y1))))
            z_sub_min = min(z1 + t_vals[0] * (z2 - z1), z1 + t_vals[1] * (z2 - z1))
            z_sub_max = max(z1 + t_vals[0] * (z2 - z1), z1 + t_vals[1] * (z2 - z1))
            if z_sub_max >= (z_min - 1e-6) and z_sub_min <= (z_max + 1e-6):
                return True

    return False


def extract_polygon_segments(obstacles: List[Polygon]) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """Extract and flatten all boundary and interior hole segments from obstacle polygons."""
    segs = []
    for obs in obstacles:
        coords = list(obs.exterior.coords)
        for i in range(len(coords) - 1):
            segs.append((coords[i], coords[i + 1]))
        for interior in obs.interiors:
            icoords = list(interior.coords)
            for i in range(len(icoords) - 1):
                segs.append((icoords[i], icoords[i + 1]))
    return segs



def is_segment_blocked(p1: Tuple[float, float], p2: Tuple[float, float], obstacles: List[Polygon]) -> bool:
    """Check if straight line segment [p1, p2] intersects any obstacle interior or boundary."""
    seg = LineString([p1, p2])
    for obs in obstacles:
        if seg.intersects(obs):
            inter = seg.intersection(obs)
            if not inter.is_empty:
                if inter.geom_type in ['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']:
                    return True
                elif inter.geom_type == 'Point':
                    pt = (inter.x, inter.y)
                    d1 = distance(p1, pt)
                    d2 = distance(p2, pt)
                    if d1 > 1e-4 and d2 > 1e-4:
                        return True
    return False


def sample_polygon_points(poly: Polygon, n_samples: int = 15) -> List[Tuple[float, float]]:
    """Sample representative points across the interior and boundary of a polygon."""
    points = []
    c = poly.centroid
    if poly.contains(c):
        points.append((c.x, c.y))
    
    exterior = poly.exterior
    coords = list(exterior.coords)[:-1]
    points.extend(coords)
    
    length = exterior.length
    if length > 0 and len(points) < n_samples:
        step = length / max(1, (n_samples - len(points)))
        for dist in np.arange(step / 2, length, step):
            pt = exterior.interpolate(dist)
            points.append((pt.x, pt.y))
            
    return points


def sample_disk_points(center: Tuple[float, float], radius_m: float = 0.3, n_radial: int = 4, n_angular: int = 8) -> List[Tuple[float, float]]:
    """Sample points across a 2D circular agent hitbox disk."""
    pts = [center]
    for r in np.linspace(radius_m * 0.3, radius_m, n_radial):
        for theta in np.linspace(0, 2 * math.pi, n_angular, endpoint=False):
            pts.append((center[0] + r * math.cos(theta), center[1] + r * math.sin(theta)))
    return pts


def compute_disk_visible_fraction(
    observer_eye: Tuple[float, float],
    target_center: Tuple[float, float],
    target_radius_m: float,
    obstacles: List[Polygon]
) -> float:
    """Compute fraction of target's circular hitbox disk visible from observer's eye [G]."""
    samples = sample_disk_points(target_center, radius_m=target_radius_m)
    if not samples:
        return 0.0
    visible_count = sum(1 for pt in samples if not is_segment_blocked(observer_eye, pt, obstacles))
    return visible_count / len(samples)


def simulate_corner_duel_gpa(
    corner_pt: Tuple[float, float],
    setback_a: float,
    setback_b: float,
    agent_radius_m: float = 0.3,
    vis_threshold: float = 0.15,
    speed_mps: float = 3.0,
    response_margin_s: float = 0.45,
    t_max_s: float = 3.0,
    dt_s: float = 0.01
) -> Tuple[float, float, float]:
    """Simulate a dynamic corner duel between finite circular agents A and B.

    Wall corner at (x_c, y_c).
    Agent A approaches horizontally: y_A = y_c + setback_a, moving from x_c - 3.0 to x_c + 3.0.
    Agent B is stationary vertically: x_B = x_c + setback_b, y_B = y_c - 2.0.

    Returns (t_A_sees_B, t_B_sees_A, GPA).
    """
    # Wall is a solid block occupying x <= x_c, y <= y_c
    wall = Polygon([
        (corner_pt[0] - 10.0, corner_pt[1] - 10.0),
        (corner_pt[0], corner_pt[1] - 10.0),
        (corner_pt[0], corner_pt[1]),
        (corner_pt[0] - 10.0, corner_pt[1])
    ])
    obstacles = [wall]

    pos_b = (corner_pt[0] + setback_b, corner_pt[1] - 2.0)
    start_x_a = corner_pt[0] - 2.0
    y_a = corner_pt[1] + setback_a

    t_a_sees_b: Optional[float] = None
    t_b_sees_a: Optional[float] = None

    for t in np.arange(0.0, t_max_s, dt_s):
        pos_a = (start_x_a + t * speed_mps, y_a)

        # Check A -> B
        v_a_to_b = compute_disk_visible_fraction(pos_a, pos_b, agent_radius_m, obstacles)
        if t_a_sees_b is None and v_a_to_b >= vis_threshold:
            t_a_sees_b = t

        # Check B -> A
        v_b_to_a = compute_disk_visible_fraction(pos_b, pos_a, agent_radius_m, obstacles)
        if t_b_sees_a is None and v_b_to_a >= vis_threshold:
            t_b_sees_a = t

        if t_a_sees_b is not None and t_b_sees_a is not None:
            break

    t_a_val = t_a_sees_b if t_a_sees_b is not None else float('inf')
    t_b_val = t_b_sees_a if t_b_sees_a is not None else float('inf')
    delta_t_geo = t_b_val - t_a_val
    gpa = delta_t_geo / response_margin_s

    return t_a_val, t_b_val, gpa


def is_quiescent_reset_pocket(
    pocket_polygon: Polygon,
    threats: List[Any],
    obstacles: List[Polygon],
    grid_step: float = 0.25,
    vis_threshold: float = 0.10
) -> bool:
    """Certify that a 2D pocket region satisfies the Quiescent Boundary Property (B_ext = 0).
    
    Verifies that for all sample points x in pocket_polygon, and every threat T_j,
    the visible fraction v(T_j, x) remains strictly below vis_threshold.
    """
    from .visibility import compute_threat_view
    minx, miny, maxx, maxy = pocket_polygon.bounds
    x = minx + grid_step / 2.0
    while x <= maxx:
        y = miny + grid_step / 2.0
        while y <= maxy:
            pt = Point(x, y)
            if pocket_polygon.contains(pt):
                for threat in threats:
                    view = compute_threat_view((x, y), threat, obstacles)
                    if view is not None and view.visible_fraction >= vis_threshold:
                        return False
            y += grid_step
        x += grid_step
    return True

