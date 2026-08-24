"""Export canonical Python GeometricModules, Calibration, and Practice into versioned TrialSpec JSON.

This maintains Python as the single authoritative source of scientific truth.
The browser Three.js runtime executes this spec without recalculating compiler models.
"""

import os
import sys
import json
import time
import math
from pathlib import Path
from typing import Dict, Any, List

# Add src to python path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fps_clearability.compiler import GeometricModule, GeometricRoute, GeometricThreat, GeometricPort
from fps_clearability.pilot_stimuli import build_12_stimulus_pilot_suite, build_practice_suite
from fps_clearability.vizdoom_engine import (
    TicCombatParameters,
    DiscreteTicScheduler,
    DeterministicSimulationReferee,
    InformationRegime
)
from shapely.geometry import Polygon, LineString


def build_vertical_slice_practice_suite() -> List[GeometricModule]:
    """Construct 2 purpose-built practice rooms:
    1. Single-corner task training (learn auto-movement + aim + hold-to-service).
    2. Double-angle sequencing practice (learn 2-target clear order).
    """
    boundary_std = Polygon([(0.0, -2.5), (8.0, -2.5), (8.0, 2.5), (0.0, 2.5)])
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(8.0, -1.0), (8.0, 1.0)]))
    route_std = GeometricRoute("main", [(0.0, 0.0), (8.0, 0.0)], v_move_mps=4.5)

    # 1. Single Corner Practice: Left obstacle wall unoccludes one threat in the upper pocket
    p1 = GeometricModule(
        module_id="PRACTICE_01_SingleCorner",
        name="Practice 1: Single Corner Clearance",
        boundary=boundary_std,
        obstacles=[Polygon([(2.0, -0.2), (2.3, -0.2), (2.3, 2.2), (2.0, 2.2)])],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat(
                "T_Prac1",
                Polygon([(3.5, 0.8), (4.0, 0.8), (4.0, 1.3), (3.5, 1.3)]),
                (3.75, 1.05),
                authored_due_window_s=1.20,
                service_duration_s=0.10
            )
        ],
        routes=[route_std],
        category="Practice"
    )

    # 2. Two-Angle Sequencing Practice: Staggered top and bottom obstacles
    p2 = GeometricModule(
        module_id="PRACTICE_02_DoubleAngle",
        name="Practice 2: Double Angle Sequencing",
        boundary=boundary_std,
        obstacles=[
            Polygon([(1.8, 0.0), (2.1, 0.0), (2.1, 2.2), (1.8, 2.2)]),
            Polygon([(3.6, -2.2), (3.9, -2.2), (3.9, 0.0), (3.6, 0.0)])
        ],
        ports=[port_in, port_out],
        threats=[
            GeometricThreat(
                "T1_Left",
                Polygon([(3.0, 0.8), (3.4, 0.8), (3.4, 1.2), (3.0, 1.2)]),
                (3.2, 1.0),
                authored_due_window_s=1.00,
                service_duration_s=0.10
            ),
            GeometricThreat(
                "T2_Right",
                Polygon([(5.0, -1.2), (5.4, -1.2), (5.4, -0.8), (5.0, -0.8)]),
                (5.2, -1.0),
                authored_due_window_s=1.20,
                service_duration_s=0.10
            )
        ],
        routes=[route_std],
        category="Practice"
    )

    return [p1, p2]


def serialize_module(mod: GeometricModule, params: TicCombatParameters, scheduler: DiscreteTicScheduler, ref: DeterministicSimulationReferee) -> Dict[str, Any]:
    """Serialize a single GeometricModule into exact 3D polygon & scheduling specification."""
    # Boundary vertices
    b_coords = list(mod.boundary.exterior.coords)[:-1]
    boundary_pts = [{"x": float(x), "y": float(y)} for x, y in b_coords]

    # Obstacles
    obstacles_data = []
    for obs in mod.obstacles:
        o_coords = list(obs.exterior.coords)[:-1]
        obstacles_data.append([{"x": float(x), "y": float(y)} for x, y in o_coords])

    # Route polyline
    route = mod.routes[0]
    route_pts = [{"x": float(x), "y": float(y)} for x, y in route.waypoints]

    # Offline compiler scheduling
    jobs = ref.extract_tic_jobs(mod)
    sched_rg = scheduler.solve(jobs, regime=InformationRegime.REVEAL_GATED)
    sched_pa = scheduler.solve(jobs, regime=InformationRegime.PRE_AIM)

    threats_data = []
    for t in mod.threats:
        tx, ty = t.threat_anchor
        threat_job = next((j for j in jobs if j.id == t.id), None)
        r_tic = threat_job.reveal_tic if threat_job else 0
        r_ms = round(r_tic * (1000.0 / params.ticrate_hz), 1)
        d_win_tics = int(round(t.authored_due_window_s * params.ticrate_hz))
        d_win_ms = round(t.authored_due_window_s * 1000.0, 1)
        d_abs_tic = r_tic + d_win_tics
        d_abs_ms = round(d_abs_tic * (1000.0 / params.ticrate_hz), 1)

        threats_data.append({
            "id": t.id,
            "anchor": {"x": float(tx), "y": float(ty)},
            "reveal_tic": r_tic,
            "reveal_ms": r_ms,
            "due_window_s": float(t.authored_due_window_s),
            "due_window_tics": d_win_tics,
            "due_window_ms": d_win_ms,
            "deadline_tic": d_abs_tic,
            "deadline_ms": d_abs_ms,
            "service_duration_s": float(t.service_duration_s),
            "service_tics": int(round(t.service_duration_s * params.ticrate_hz))
        })

    # Find ell* (critical knowledge lead)
    # ell* is minimum lead l such that M(l) >= 0
    ell_star_tics = None
    ell_star_ms = None
    for lead in range(0, 30):
        s_lead = scheduler.solve(jobs, actionability_lead_tics=lead)
        if s_lead.is_feasible:
            ell_star_tics = lead
            ell_star_ms = round(lead * (1000.0 / params.ticrate_hz), 1)
            break

    return {
        "module_id": mod.module_id,
        "name": mod.name,
        "category": mod.category,
        "boundary": boundary_pts,
        "obstacles": obstacles_data,
        "route": {
            "route_id": route.route_id,
            "waypoints": route_pts,
            "v_move_mps": float(route.v_move_mps),
            "total_length_m": float(route.total_length_m),
            "duration_s": float(route.total_length_m / route.v_move_mps),
            "total_tics": int(math.ceil((route.total_length_m / route.v_move_mps) * params.ticrate_hz))
        },
        "threats": threats_data,
        "canonical_schedule": {
            "m_reveal_tics": sched_rg.tactical_margin_tics,
            "m_reveal_ms": round(sched_rg.tactical_margin_tics * (1000.0 / params.ticrate_hz), 1),
            "is_reveal_feasible": sched_rg.is_feasible,
            "m_preaim_tics": sched_pa.tactical_margin_tics,
            "m_preaim_ms": round(sched_pa.tactical_margin_tics * (1000.0 / params.ticrate_hz), 1),
            "is_preaim_feasible": sched_pa.is_feasible,
            "delta_m_knowledge_tics": sched_pa.tactical_margin_tics - sched_rg.tactical_margin_tics,
            "delta_m_knowledge_ms": round((sched_pa.tactical_margin_tics - sched_rg.tactical_margin_tics) * (1000.0 / params.ticrate_hz), 1),
            "ell_star_tics": ell_star_tics,
            "ell_star_ms": ell_star_ms
        }
    }


def generate_trial_spec():
    params = TicCombatParameters()
    scheduler = DiscreteTicScheduler(params)
    ref = DeterministicSimulationReferee(params)

    # 1. Practice Modules
    practice_modules = build_vertical_slice_practice_suite()
    practice_specs = [serialize_module(m, params, scheduler, ref) for m in practice_modules]

    # 2. Canonical Pilot 12 Stimuli
    suite = build_12_stimulus_pilot_suite()
    suite_specs = [serialize_module(m, params, scheduler, ref) for m in suite]

    # Vertical slice flagship encounter: STIM_06 (Double Baffle Pivot: M_rg = -5 -> M_pa = +2, ell* = 5 tics / 143 ms)
    stim_06_spec = next(s for s in suite_specs if s["module_id"] == "STIM_06_K3_ModestPivot")

    trial_spec = {
        "schema_version": "2.0.0",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "physics_constants": {
            "ticrate_hz": params.ticrate_hz,
            "tic_duration_ms": round(1000.0 / params.ticrate_hz, 4),
            "v_move_mps": params.v_move_mps,
            "nominal_acquisition_latency_s": params.acquisition_latency_s,
            "nominal_aim_velocity_deg_s": params.aim_velocity_deg_s,
            "nominal_service_duration_s": params.inspect_duration_s,
            "nominal_service_tics": params.service_tics,
            "aim_tolerance_deg": 12.0,
            "player_eye_height_m": 1.70,
            "wall_height_m": 2.60,
            "target_radius_m": 0.22,
            "target_height_m": 1.10
        },
        "calibration_protocol": {
            "reaction_stage": {
                "name": "Acquisition Latency Calibration",
                "instructions": "Keep crosshair centered on the reticle dot. When an amber target appears at close range, click it immediately.",
                "n_trials": 10,
                "angular_offsets_deg": [-12, -8, -4, 4, 8, 12, -6, 6, -10, 10],
                "min_delay_s": 0.8,
                "max_delay_s": 2.2
            },
            "slew_stage": {
                "name": "Aim Slew Rate Calibration",
                "instructions": "When the target jumps to a wide angle (+/-30 deg, +/-60 deg, +/-90 deg), snap to it as fast as possible and hold left click.",
                "angles_deg": [-30, 30, -60, 60, -90, 90]
            }
        },
        "practice_arenas": practice_specs,
        "vertical_slice_encounter": stim_06_spec,
        "pilot_suite_manifest": [
            {
                "module_id": s["module_id"],
                "name": s["name"],
                "category": s["category"],
                "m_reveal_tics": s["canonical_schedule"]["m_reveal_tics"],
                "m_preaim_tics": s["canonical_schedule"]["m_preaim_tics"],
                "ell_star_tics": s["canonical_schedule"]["ell_star_tics"]
            }
            for s in suite_specs
        ],
        "all_stimuli": suite_specs
    }

    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "trial_spec_v1.json"
    out_js_file = out_dir / "trial_spec_data.js"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(trial_spec, f, indent=2)

    with open(out_js_file, "w", encoding="utf-8") as f:
        f.write("window.TRIAL_SPEC = " + json.dumps(trial_spec, indent=2) + ";\n")

    print(f"Exported TrialSpec v2.0 to: {out_file} and {out_js_file}")
    print(f"  Practice Arenas: {len(practice_specs)}")
    print(f"  Vertical Slice Arena: {stim_06_spec['module_id']} (M_rg={stim_06_spec['canonical_schedule']['m_reveal_tics']}t, ell*={stim_06_spec['canonical_schedule']['ell_star_tics']}t)")
    print(f"  Full Stimuli Suite: {len(suite_specs)}")


if __name__ == "__main__":
    generate_trial_spec()
