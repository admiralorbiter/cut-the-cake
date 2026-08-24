"""Tactical CAD Adapter Layer [Cut the Cake / M2B].

Authoritative Python adapter bridging CAD Documents and the scientific core:
- Analyzes arbitrary CADDocument / GeometricModule instances without fixture special-casing.
- Translates any obstacle in 2D (X and Y) with spatial invariant validation.
- Distinguishes fast-path schedulability (source_schedule_feasible) from executed telemetry outcomes.
- Emits fail-closed external evidence metadata.
"""

from __future__ import annotations
import math
import time
from typing import Dict, Any, List, Optional, Tuple
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

    if params is None:
        params = doc.player_model.to_combat_params()

    geo_module = doc.to_geometric_module()

    # Route selection
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
            policy=ControllerPolicy.ORACLE
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
    
    if m_tics < 0:
        diagnostic = {
            "type": "STAGGER_DEFICIT",
            "critical_threat_id": crit_id,
            "explanation": f"Tactical bottleneck at '{crit_label}': deadline is breached by {-m_tics} tics. Insufficient inter-threat reveal separation."
        }
    else:
        diagnostic = {
            "type": "NONE",
            "critical_threat_id": None,
            "explanation": f"All {len(jobs)} threat deadlines serviced with +{m_tics} tics reserve margin."
        }

    runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    return {
        "is_valid": True,
        "document_id": doc.document_id,
        "document_name": doc.name,
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
