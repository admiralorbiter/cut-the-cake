"""Tactical CAD Adapter Layer [Live Interactive Source Re-analysis].

Provides fast, authoritative geometric translation and real-time discrete scheduling
analysis for interactive CAD manipulation (Milestone 2A).

Guarantees:
- Reconstructs authoritative frozen Python fixtures with zero browser-side arithmetic.
- Validates geometric preservation constraints (boundary containment, route clearance, threat isolation).
- Computes real-time raycast revelations, discrete 35 Hz deadlines, and optimal minimax lateness L*.
- Categorizes source-model verdicts into 3 strict status bands:
    1. UNSERVICEABLE (M < 0)
    2. FEASIBLE — BELOW TARGET RESERVE (0 <= M < +2)
    3. TARGET RESERVE MET (M >= +2)
- Fails closed on external engine evidence (transfer_status: 'not_run').
- Returns client revision echoes to guarantee monotonic, out-of-order-safe UI updates.
"""

from __future__ import annotations
import math
import time
from typing import Dict, Any, List, Optional, Tuple
from shapely.geometry import Polygon, Point, LineString
import shapely.affinity

from .compiler import GeometricModule, GeometricRoute, GeometricThreat, GeometricPort
from .repair import TacticalDiagnostic, diagnose_clearability, validate_repair_preservation
from .repair_benchmark import build_unserviceable_population
from .vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteTicScheduler,
    DeterministicSimulationReferee,
    SimulationController
)
from .cad_export import (
    _poly_to_coords,
    _threat_label,
    _export_geometry_struct,
    _generate_telemetry_and_events
)


def validate_candidate_obstacle_placement(
    base_module: GeometricModule,
    obstacle_idx: int,
    candidate_obstacle: Polygon,
    clearance_m: float = 0.05
) -> Tuple[bool, Optional[str]]:
    """Validate that candidate obstacle satisfies all spatial and architectural invariants."""
    if not candidate_obstacle.is_valid or candidate_obstacle.is_empty:
        return False, "Invalid or degenerate obstacle polygon geometry."

    # Invariant 1: Must be strictly contained within arena boundary
    if not candidate_obstacle.within(base_module.boundary):
        return False, "Obstacle extends outside arena room boundary."

    # Invariant 2: Clearance to other obstacles
    for idx, other_obs in enumerate(base_module.obstacles):
        if idx != obstacle_idx:
            if candidate_obstacle.intersects(other_obs):
                return False, f"Obstacle intersects existing obstacle #{idx}."

    # Invariant 3: Corridor clearance along route
    for r in base_module.routes:
        route_line = LineString(r.waypoints)
        if candidate_obstacle.distance(route_line) < clearance_m:
            return False, f"Obstacle violates corridor clearance ({clearance_m:.2f}m) to route '{r.route_id}'."

    # Invariant 4: Must not overlap threat anchors or threat polygons
    for t in base_module.threats:
        anchor_pt = Point(t.threat_anchor)
        if candidate_obstacle.distance(anchor_pt) < 0.10:
            return False, f"Obstacle encroaches on threat '{t.id}' anchor point."
        if candidate_obstacle.intersects(t.polygon):
            return False, f"Obstacle intersects threat '{t.id}' polygon."

    # Invariant 5: Clearance to entrance/exit ports
    for p in base_module.ports:
        if candidate_obstacle.distance(p.segment) < 0.20:
            return False, f"Obstacle encroaches on port '{p.id}'."

    return True, None


def analyze_candidate_geometry(
    fixture_id: str = "RepairPop_F1_StaggerDeficit_00",
    obstacle_id: int = 0,
    translation_m: float = 0.0,
    axis: str = "x",
    client_revision: int = 0,
    include_telemetry: bool = False,
    params: Optional[TicCombatParameters] = None
) -> Dict[str, Any]:
    """Authoritative Python analysis of candidate obstacle displacement.
    
    Returns candidate geometry, timing parameters, tactical margin, status band,
    and optional telemetry frames with sub-millisecond execution latency.
    """
    t_start = time.perf_counter()
    if params is None:
        params = TicCombatParameters()

    # 1. Load authoritative baseline fixture
    population = build_unserviceable_population(n_per_family=10)
    fixture_map = {m.module_id: m for m in population}
    if fixture_id not in fixture_map:
        return {
            "is_valid": False,
            "error_reason": f"Fixture '{fixture_id}' not found in canonical benchmark population.",
            "client_revision": client_revision,
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    broken_mod = fixture_map[fixture_id]
    if obstacle_id < 0 or obstacle_id >= len(broken_mod.obstacles):
        return {
            "is_valid": False,
            "error_reason": f"Invalid obstacle_id {obstacle_id}; fixture has {len(broken_mod.obstacles)} obstacles.",
            "client_revision": client_revision,
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    if axis.lower() != "x":
        return {
            "is_valid": False,
            "error_reason": f"M2A supports only 'x' axis translation; received '{axis}'.",
            "client_revision": client_revision,
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    # 2. Construct translated candidate obstacle
    orig_obs = broken_mod.obstacles[obstacle_id]
    dx = float(translation_m)
    candidate_obs = shapely.affinity.translate(orig_obs, xoff=dx, yoff=0.0)

    # 3. Validate geometric invariants
    is_valid, error_reason = validate_candidate_obstacle_placement(
        base_module=broken_mod,
        obstacle_idx=obstacle_id,
        candidate_obstacle=candidate_obs
    )

    if not is_valid:
        return {
            "is_valid": False,
            "error_reason": error_reason,
            "client_revision": client_revision,
            "translation_m": round(dx, 4),
            "runtime_ms": round((time.perf_counter() - t_start) * 1000.0, 2)
        }

    # 4. Construct candidate GeometricModule
    new_obstacles = list(broken_mod.obstacles)
    new_obstacles[obstacle_id] = candidate_obs

    candidate_mod = GeometricModule(
        module_id=f"{fixture_id}_cand_dx_{dx:+.2f}",
        name=broken_mod.name,
        boundary=broken_mod.boundary,
        obstacles=new_obstacles,
        routes=broken_mod.routes,
        threats=broken_mod.threats,
        ports=broken_mod.ports,
        category=broken_mod.category
    )

    # 5. Authoritative Physics & Discrete Scheduling Solve
    referee = DeterministicSimulationReferee(params)
    jobs = referee.extract_tic_jobs(candidate_mod, route_index=0)
    scheduler = DiscreteTicScheduler(params)
    sched_res = scheduler.solve(jobs, initial_reticle_deg=0.0)
    job_map = {j.id: j for j in jobs}
    threat_idx_map = {t.id: idx for idx, t in enumerate(candidate_mod.threats)}

    # Schedulability & Status Bands
    m_tics = sched_res.tactical_margin_tics
    dt_s = params.tic_duration_s

    if m_tics < 0:
        status_band = "UNSERVICEABLE"
        verdict = "unserviceable"
    elif m_tics < 2:
        status_band = "FEASIBLE — BELOW TARGET RESERVE"
        verdict = "serviceable"
    else:
        status_band = "TARGET RESERVE MET"
        verdict = "serviceable"

    # Threat job timing details
    threat_job_records = []
    for tid in sched_res.optimal_permutation:
        j = job_map[tid]
        c_tic = sched_res.completion_tics.get(tid, 0)
        lat_tic = sched_res.lateness_per_threat.get(tid, 0)
        lbl = _threat_label(j.id, threat_idx_map.get(j.id, 0))
        sched_end_tic = max(0, c_tic - 1)
        
        threat_job_records.append({
            "id": j.id,
            "label": lbl,
            "reveal_tic": j.reveal_tic,
            "reveal_s": round(j.reveal_tic * dt_s, 4),
            "due_window_tics": j.due_window_tics,
            "due_window_s": round(j.due_window_tics * dt_s, 4),
            "deadline_tic": j.deadline_tic,
            "deadline_s": round(j.deadline_tic * dt_s, 4),
            "angle_deg": round(j.angle_deg, 2),
            "service_duration_tics": j.service_duration_tics,
            "completion_tic": c_tic,
            "scheduled_service_end_tic": sched_end_tic,
            "realized_service_complete_tic": sched_end_tic if m_tics >= 0 else (
                sched_end_tic if sched_end_tic < min(j2.deadline_tic for j2 in jobs if sched_res.completion_tics.get(j2.id, 0) > j2.deadline_tic) else None
            ),
            "completion_s": round(c_tic * dt_s, 4),
            "lateness_tics": lat_tic
        })

    # Diagnostic bottleneck analysis
    diag = diagnose_clearability(candidate_mod, target_margin_tics=2, params=params)
    has_bn = not diag.is_serviceable
    crit_label = _threat_label(diag.critical_threat_id, threat_idx_map.get(diag.critical_threat_id, 0)) if diag.critical_threat_id else None

    # Stagger Gap
    t1_job = next((j for j in jobs if j.id.endswith("T1_L00") or "T1" in j.id), jobs[0] if len(jobs) > 0 else None)
    t2_job = next((j for j in jobs if j.id.endswith("T2_R00") or "T2" in j.id), jobs[1] if len(jobs) > 1 else None)
    
    r1_tic = t1_job.reveal_tic if t1_job else 0
    r2_tic = t2_job.reveal_tic if t2_job else 0
    stagger_gap_tics = r2_tic - r1_tic
    stagger_gap_ms = round(stagger_gap_tics * dt_s * 1000.0, 1)

    # 6. Optional Full Telemetry Generation on Commit / Drag Release
    telemetry_frames = None
    events = None
    model_episode_survived = (m_tics >= 0)
    model_death_tic = None

    if include_telemetry:
        frames, evts, summary = _generate_telemetry_and_events(candidate_mod, params)
        telemetry_frames = frames
        events = evts
        model_episode_survived = summary["model_episode_survived"]
        model_death_tic = summary["model_death_tic"]

    runtime_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    return {
        "is_valid": True,
        "client_revision": client_revision,
        "runtime_ms": runtime_ms,
        "fixture_id": fixture_id,
        "obstacle_id": obstacle_id,
        "axis": axis,
        "translation_m": round(dx, 4),
        "status_band": status_band,
        "verdict": verdict,
        "tactical_margin_tics": m_tics,
        "tactical_margin_ms": round(m_tics * dt_s * 1000.0, 1),
        "l_star_tics": sched_res.lateness_optimal_l_star_tics,
        "stagger_gap_tics": stagger_gap_tics,
        "stagger_gap_ms": stagger_gap_ms,
        "r1_reveal_tic": r1_tic,
        "r2_reveal_tic": r2_tic,
        "threat_jobs": threat_job_records,
        "diagnostic": {
            "has_bottleneck": has_bn,
            "critical_threat_id": diag.critical_threat_id,
            "critical_threat_label": crit_label,
            "controlling_occluder_obstacle_id": diag.controlling_obstacle_idx,
            "controlling_occluder_segment": (
                [[round(float(x), 4), round(float(y), 4)] for x, y in diag.controlling_edge]
                if diag.controlling_edge else None
            ),
            "lateness_deficit_tics": diag.margin_deficit_tics,
            "lateness_deficit_ms": round(diag.margin_deficit_tics * dt_s * 1000.0, 1),
            "explanation": (
                f"{crit_label} unoccludes too early. "
                f"Shift obstacle further right to introduce +{diag.margin_deficit_tics} tics of delay."
            ) if has_bn else "Scheduling margin objective satisfied (M >= +2 tics)."
        },
        "candidate_geometry": _export_geometry_struct(candidate_mod),
        "model_episode_survived": model_episode_survived,
        "model_death_tic": model_death_tic,
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
        "telemetry_frames": telemetry_frames,
        "events": events
    }
