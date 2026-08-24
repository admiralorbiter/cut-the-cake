"""Multi-Phase Scaling Benchmark for Cut the Cake CAD Engine.

Phased execution:
- Phase 1: Full 35-cell matrix (7 segment counts x 5 threat counts) measuring
  warmup-stabilized p50 and p95 latencies for Job Compilation, L* Scheduling,
  and Fast Total Analysis.
- Phase 2: Representative anchor cells for Full Telemetry simulation.
- Phase 3: Separate memory footprint profiling without timing interference.
"""

from __future__ import annotations
import json
import math
import statistics
import time
import tracemalloc
from typing import Any

from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPlayerModel,
)
from cut_the_cake.cad_adapter import analyze_cad_document
from cut_the_cake.vizdoom_engine import (
    DeterministicSimulationReferee,
    DiscreteTicScheduler,
    TicCombatParameters,
)


def generate_scaling_document(num_segments: int, num_threats: int) -> CADDocument:
    """Generate a synthetic graybox corridor with approximately num_segments and num_threats."""
    obstacles = []
    num_boxes = max(1, num_segments // 4)
    cols = int(math.ceil(math.sqrt(num_boxes)))
    rows = int(math.ceil(num_boxes / cols))

    box_idx = 0
    for r in range(rows):
        for c in range(cols):
            if box_idx >= num_boxes:
                break
            x = 2.0 + c * 1.5
            y = 1.0 + r * 1.5 if (c % 2 == 0) else -1.0 - r * 1.5
            w = 0.8
            h = 0.8
            obstacles.append(
                CADObstacle(
                    id=f"obs_bench_{box_idx}",
                    name=f"Obstacle {box_idx}",
                    vertices=[[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                )
            )
            box_idx += 1

    max_x = max(12.0, 2.0 + cols * 1.5 + 2.0)
    max_y = max(6.0, 2.0 + rows * 1.5 + 2.0)
    route = CADRoute(
        id="route_bench",
        name="Benchmark Route",
        waypoints=[[0.0, 0.0], [max_x / 2.0, 0.0], [max_x, 0.0]],
        v_move_mps=4.5,
    )

    threats = []
    for t in range(num_threats):
        tx = 2.5 + (t / max(1, num_threats - 1)) * (max_x - 5.0)
        ty = 2.2 if (t % 2 == 0) else -2.2
        threats.append(
            CADThreat(
                id=f"threat_bench_{t}",
                name=f"Threat {t}",
                polygon=[[tx - 0.2, ty - 0.2], [tx + 0.2, ty - 0.2], [tx + 0.2, ty + 0.2], [tx - 0.2, ty + 0.2]],
                anchor=[tx, ty],
                due_window_s=0.5,
                service_duration_s=0.15,
            )
        )

    boundary = [[-2.0, -max_y], [max_x + 4.0, -max_y], [max_x + 4.0, max_y], [-2.0, max_y]]

    return CADDocument(
        document_id=f"bench_s{num_segments}_t{num_threats}",
        name=f"bench_s{num_segments}_t{num_threats}",
        schema_version="cad_document_v1",
        boundary=boundary,
        player_model=CADPlayerModel(
            v_move_mps=4.5,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0,
        ),
        obstacles=obstacles,
        routes=[route],
        threats=threats,
    )


def _timed_runs(fn, runs: int = 5, warmup: int = 1) -> tuple[float, float]:
    """Run fn multiple times with warmup, returning (p50_ms, sample_max_ms)."""
    for _ in range(warmup):
        fn()
    durations = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        durations.append((time.perf_counter() - t0) * 1000.0)
    durations.sort()
    p50 = statistics.median(durations)
    sample_max = max(durations)
    return round(p50, 3), round(sample_max, 3)


def run_scaling_benchmark(output_path: str = "benchmarks/results_scaling.json") -> dict[str, Any]:
    segment_counts = [50, 100, 250, 500, 1000, 2500, 5000]
    threat_counts = [2, 4, 8, 12, 20]
    
    print("=" * 102)
    print("CUT THE CAKE - PHASE 1: GEOMETRY & THREAT SCALING (FAST ANALYSIS MATRIX)")
    print("=" * 102)
    print(f"{'Segments':<10} | {'Threats':<8} | {'Route Tics':<11} | {'Jobs':<6} | {'Job Comp (p50/max ms)':<24} | {'Sched (p50 ms)':<16} | {'Fast Tot (p50/max ms)':<22}")
    print("-" * 102)

    phase1_results = []
    for seg in segment_counts:
        for th in threat_counts:
            doc = generate_scaling_document(seg, th)
            actual_segs = sum(len(o.vertices) for o in doc.obstacles)
            params = doc.player_model.to_combat_params()
            geo_module = doc.to_geometric_module()
            referee = DeterministicSimulationReferee(params)
            scheduler = DiscreteTicScheduler(params)

            # Route tics and extracted jobs
            route = geo_module.routes[0]
            route_tics = int(math.ceil(route.total_length_m / params.move_m_per_tic))
            jobs = referee.extract_tic_jobs(geo_module, route_index=0)
            compiled_jobs = len(jobs)

            # Job compilation timing
            c_p50, c_max = _timed_runs(lambda: referee.extract_tic_jobs(geo_module, route_index=0), runs=5)
            
            # Scheduler timing (exact permutation scheduler: O(J! * J))
            s_p50, s_max = _timed_runs(lambda: scheduler.solve(jobs), runs=5)

            # Fast analysis timing
            f_p50, f_max = _timed_runs(lambda: analyze_cad_document(doc, include_telemetry=False), runs=5)

            row = {
                "segments_actual": actual_segs,
                "threats_authored": th,
                "route_tics": route_tics,
                "compiled_jobs": compiled_jobs,
                "compile_p50_ms": c_p50,
                "compile_sample_max_ms": c_max,
                "scheduler_p50_ms": s_p50,
                "scheduler_sample_max_ms": s_max,
                "fast_total_p50_ms": f_p50,
                "fast_total_sample_max_ms": f_max,
            }
            phase1_results.append(row)
            print(
                f"{actual_segs:<10} | {th:<8} | {route_tics:<11} | {compiled_jobs:<6} | "
                f"{f'{c_p50:.2f} / {c_max:.2f}':<24} | {s_p50:<16.2f} | {f'{f_p50:.2f} / {f_max:.2f}':<22}"
            )

    print("\n" + "=" * 90)
    print("CUT THE CAKE - PHASE 2: REPRESENTATIVE FULL TELEMETRY SIMULATION")
    print("=" * 90)
    print(f"{'Segments':<10} | {'Threats':<8} | {'Route Tics':<11} | {'Jobs':<6} | {'Telemetry p50 (ms)':<20} | {'Telemetry sample_max (ms)':<26}")
    print("-" * 90)

    phase2_cells = [(50, 2), (250, 4), (500, 8), (1000, 12), (2500, 20)]
    phase2_results = []
    for seg, th in phase2_cells:
        doc = generate_scaling_document(seg, th)
        actual_segs = sum(len(o.vertices) for o in doc.obstacles)
        params = doc.player_model.to_combat_params()
        geo_module = doc.to_geometric_module()
        referee = DeterministicSimulationReferee(params)
        route = geo_module.routes[0]
        route_tics = int(math.ceil(route.total_length_m / params.move_m_per_tic))
        jobs = referee.extract_tic_jobs(geo_module, route_index=0)
        compiled_jobs = len(jobs)

        t_p50, t_max = _timed_runs(lambda: analyze_cad_document(doc, include_telemetry=True), runs=3)
        row = {
            "segments_actual": actual_segs,
            "threats_authored": th,
            "route_tics": route_tics,
            "compiled_jobs": compiled_jobs,
            "telemetry_p50_ms": t_p50,
            "telemetry_sample_max_ms": t_max,
        }
        phase2_results.append(row)
        print(f"{actual_segs:<10} | {th:<8} | {route_tics:<11} | {compiled_jobs:<6} | {t_p50:<20.2f} | {t_max:<26.2f}")

    # Phase 3: Memory footprint
    print("\n" + "=" * 90)
    print("CUT THE CAKE - PHASE 3: PEAK MEMORY ALLOCATION")
    print("=" * 90)
    tracemalloc.start()
    doc_heavy = generate_scaling_document(5000, 20)
    _ = analyze_cad_document(doc_heavy, include_telemetry=False)
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = round(peak_mem / (1024 * 1024), 2)
    print(f"Peak memory for 5000-segment / 20-threat document analysis: {peak_mb} MB")

    full_payload = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python_version": "3.12",
            "notes": "Synthetic generator scales both obstacle segments and corridor length (route_tics). Scheduler is factorial O(J! * J) in compiled jobs J."
        },
        "phase1_fast_matrix": phase1_results,
        "phase2_telemetry_samples": phase2_results,
        "phase3_peak_memory_mb": peak_mb,
    }
    with open(output_path, "w") as f:
        json.dump(full_payload, f, indent=2)
    print(f"\nResults successfully written to {output_path}")
    return full_payload


if __name__ == "__main__":
    run_scaling_benchmark()
