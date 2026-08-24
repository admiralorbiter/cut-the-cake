"""Exporter and Evidence Generator for Milestone 5-A Real-Map Case Study.

Generates deterministic results/m5a_dust2_a_long.json capturing:
1. Calibration metadata, landmark control points, and RMSE error.
2. Declared player model and threat contracts.
3. Multi-route tactical analysis outputs (jobs, reveal tics, deadlines, angles, margins).
4. Spatial heatmap metrics (entrance suffix M, first K=2 tic, min suffix margin).
5. Full pre-aim heading sensitivity sweep {-60 deg .. +60 deg}.
"""

import os
import json
from typing import Dict, Any
from cut_the_cake.cad_fixtures.dust2_a_long import (
    get_dust2_a_long_document,
    CALIBRATION_METADATA
)
from cut_the_cake.cad_adapter import (
    analyze_cad_document,
    compute_cad_route_spatial_heatmap
)


def export_m5a_results(output_path: str = "results/m5a_dust2_a_long.json") -> Dict[str, Any]:
    """Generate and persist the exact M5-A result packet."""
    doc = get_dust2_a_long_document()
    doc_hash = doc.compute_hash()

    results_data: Dict[str, Any] = {
        "milestone": "M5-A.1",
        "title": "Counter-Strike Dust II A-Long to A-Site / Pit Case Study Evidence Packet",
        "document_id": doc.document_id,
        "source_doc_hash": doc_hash,
        "calibration": CALIBRATION_METADATA,
        "combat_model": {
            "v_move_mps": float(doc.player_model.v_move_mps),
            "omega_slew_deg_per_s": float(doc.player_model.omega_slew_deg_per_s),
            "acquisition_latency_s": float(doc.player_model.acquisition_latency_s),
            "service_duration_s": float(doc.player_model.service_duration_s),
            "initial_reticle_deg": float(doc.player_model.initial_reticle_deg)
        },
        "routes": {},
        "pre_aim_sweep": {}
    }

    # Evaluate each route
    for r in doc.routes:
        analysis = analyze_cad_document(doc, route_id=r.id, include_telemetry=False)
        heatmap = compute_cad_route_spatial_heatmap(doc, route_id=r.id)

        samples = heatmap["samples"]
        k2_samples = [s for s in samples if s["los_concurrency"] >= 2]
        first_k2_tic = k2_samples[0]["tic"] if k2_samples else None
        first_k2_distance_m = k2_samples[0]["distance_m"] if k2_samples else None

        valid_m_samples = [s for s in samples if s["suffix_margin_tics"] is not None]
        min_sample = min(valid_m_samples, key=lambda s: s["suffix_margin_tics"]) if valid_m_samples else None

        results_data["routes"][r.id] = {
            "name": r.name,
            "tactical_margin_tics": analysis["tactical_margin_tics"],
            "source_schedule_feasible": analysis["source_schedule_feasible"],
            "stagger_gap_tics": analysis["stagger_gap_tics"],
            "stagger_gap_ms": analysis["stagger_gap_ms"],
            "compiled_job_count": analysis["compiled_job_count"],
            "threat_jobs": [
                {
                    "id": j["id"],
                    "label": j["label"],
                    "reveal_tic": j["reveal_tic"],
                    "deadline_tic": j["deadline_tic"],
                    "angle_deg": j["angle_deg"],
                    "service_duration_tics": j["service_duration_tics"]
                }
                for j in analysis["threat_jobs"]
            ],
            "entrance_suffix_margin_tics": samples[0]["suffix_margin_tics"] if samples else None,
            "entrance_status_band": samples[0]["status_band"] if samples else None,
            "first_k2_tic": first_k2_tic,
            "first_k2_distance_m": first_k2_distance_m,
            "min_suffix_margin_tics": min_sample["suffix_margin_tics"] if min_sample else None,
            "min_suffix_margin_distance_m": min_sample["distance_m"] if min_sample else None
        }

    # Pre-aim sensitivity sweep on pieing and wide swing
    sweep_results = {}
    for theta_0 in range(-60, 65, 5):
        doc.player_model.initial_reticle_deg = float(theta_0)
        res_pie = analyze_cad_document(doc, route_id="route_pieing", include_telemetry=False)
        res_wide = analyze_cad_document(doc, route_id="route_wide_swing", include_telemetry=False)
        sweep_results[str(theta_0)] = {
            "theta_0_deg": float(theta_0),
            "margin_pieing_tics": res_pie["tactical_margin_tics"],
            "margin_wide_swing_tics": res_wide["tactical_margin_tics"]
        }
    results_data["pre_aim_sweep"] = sweep_results

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    return results_data


if __name__ == "__main__":
    data = export_m5a_results()
    print(f"Exported M5-A results to results/m5a_dust2_a_long.json (Hash: {data['source_doc_hash']})")
