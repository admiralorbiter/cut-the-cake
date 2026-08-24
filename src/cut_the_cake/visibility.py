"""Dual visibility oracles and threat perception functions [G]."""

from __future__ import annotations
import math
from typing import List, Tuple, Optional, Dict
import numpy as np
from shapely.geometry import Point, LineString, Polygon

from .model import World, ThreatRegion, ThreatView
from .geometry import (
    normalize_angle_deg,
    angle_diff_deg,
    heading_to_deg,
    distance,
    is_segment_blocked,
    sample_polygon_points
)


def compute_threat_view(
    eye_pos: Tuple[float, float],
    threat: ThreatRegion,
    obstacles: List[Polygon],
    n_samples: int = 20
) -> Optional[ThreatView]:
    """Compute view-dependent threat representation from eye position [G]."""
    samples = sample_polygon_points(threat.polygon, n_samples=n_samples)
    if not samples:
        return None

    visible_points = []
    angles = []
    distances = []

    for pt in samples:
        if not is_segment_blocked(eye_pos, pt, obstacles):
            visible_points.append(pt)
            ang = heading_to_deg(eye_pos, pt)
            angles.append(ang)
            distances.append(distance(eye_pos, pt))

    if not visible_points:
        return None

    visible_fraction = len(visible_points) / len(samples)
    
    # Calculate angular bounds carefully handling wraparound
    # Convert to unit vectors to get circular mean
    sin_sum = sum(math.sin(math.radians(a)) for a in angles)
    cos_sum = sum(math.cos(math.radians(a)) for a in angles)
    centroid_ang = math.degrees(math.atan2(sin_sum, cos_sum))

    # Compute min and max angle relative to centroid
    diffs = [normalize_angle_deg(a - centroid_ang) for a in angles]
    min_diff = min(diffs)
    max_diff = max(diffs)

    min_ang = normalize_angle_deg(centroid_ang + min_diff)
    max_ang = normalize_angle_deg(centroid_ang + max_diff)

    # If threat has elevation, calculate pitch angle
    elevation_deg = 0.0
    if threat.elevation_m > 0 and distances:
        min_dist = min(distances)
        elevation_deg = math.degrees(math.atan2(threat.elevation_m, max(min_dist, 0.5)))

    return ThreatView(
        threat_id=threat.id,
        visible_fraction=visible_fraction,
        min_angle_deg=min_ang,
        max_angle_deg=max_ang,
        centroid_angle_deg=centroid_ang,
        min_distance_m=min(distances) if distances else 0.0,
        elevation_deg=elevation_deg
    )


def compute_visible_threats(
    eye_pos: Tuple[float, float],
    world: World,
    vis_threshold: float = 0.10
) -> List[ThreatView]:
    """Return all threat regions in world whose visible fraction exceeds threshold [G]."""
    views = []
    for threat in world.threats:
        tv = compute_threat_view(eye_pos, threat, world.obstacles)
        if tv is not None and tv.visible_fraction >= vis_threshold:
            views.append(tv)
    return views


def brute_force_threat_visible(
    eye_pos: Tuple[float, float],
    threat: ThreatRegion,
    obstacles: List[Polygon]
) -> bool:
    """Independent simple brute-force visibility check for oracle cross-validation."""
    # Test line of sight to vertices and center
    test_pts = list(threat.polygon.exterior.coords) + [threat.polygon.centroid.coords[0]]
    for pt in test_pts:
        seg = LineString([eye_pos, pt])
        blocked = any(seg.intersects(obs) and not seg.touches(obs) for obs in obstacles)
        if not blocked:
            return True
    return False
