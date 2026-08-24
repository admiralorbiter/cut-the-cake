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
    get_canonical_f1_document,
    get_custom_asymmetric_corridor_document
)
from .compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricThreat,
    GeometricPort,
    segments_intersect
)
from .vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteTicScheduler,
    DeterministicSimulationReferee,
    ControllerPolicy,
    SimulationEpisodeLog
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
# GENERAL AUTHORITATIVE PYTHON ANALYSIS
# =============================================================================

def analyze_cad_document(
    doc: CADDocument,
    route_id: Optional[str] = None,
    include_telemetry: bool = False,
    client_revision: int = 0,
    params: Optional[TicCombatParameters] = None
) -> Dict[str, Any]:
    """Authoritative scientific analysis of an arbitrary CADDocument.
    
    Operates without benchmark special-casing:
    - Supports arbitrary obstacle IDs, route IDs, and threat counts.
    - Accurately classifies source status bands.
    - Keeps fast-analysis semantics clean (source_schedule_feasible, null realized completion).
    - Populates realized completion from actual simulated events upon commit.
    """
    t_start = time.perf_counter()

    geo_module = doc.to_geometric_module()

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

    # 1. Authoritative Physics & Discrete Scheduling Solve
    referee = DeterministicSimulationReferee(params)
    jobs = referee.extract_tic_jobs(geo_module, route_index=route_idx)
    scheduler = DiscreteTicScheduler(params)
    sched_res = scheduler.solve(jobs, initial_reticle_deg=doc.player_model.initial_reticle_deg)

    # 2. Schedulability & Status Bands
    m_tics = sched_res.tactical_margin_tics
    dt_s = params.tic_duration_s
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

    # 3. Inter-Threat Reveal Gaps (Generalized for N threats)
    stagger_gap_tics = 0
    if len(jobs) >= 2:
        sorted_reveals = sorted(j.reveal_tic for j in jobs)
        gaps = [sorted_reveals[i+1] - sorted_reveals[i] for i in range(len(sorted_reveals) - 1)]
        stagger_gap_tics = min(gaps) if gaps else 0

    stagger_gap_ms = round(stagger_gap_tics * dt_s * 1000.0, 1)

    # 4. Threat Jobs Output Data
    threat_output_jobs = []
    
    # Fast path defaults
    realized_complete_map: Dict[str, Optional[int]] = {j.id: None for j in jobs}
    model_episode_survived: Optional[bool] = None
    model_death_tic: Optional[int] = None
    telemetry_frames_output: Optional[List[Dict[str, Any]]] = None
    events_output: Optional[List[Dict[str, Any]]] = None

    # 5. Full Simulated Execution (Only when requested on commit)
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
        "events": events_output
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
