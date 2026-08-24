"""Performance & Scaling Benchmarks for Tactical CAD.

Structured into 3 decoupled measurement tracks:
- Track A (Geometry Raycasting Scaling): Evaluates line-of-sight compile scaling
  across segment tiers (50 to 5,000 segments) with bounded threat counts (2, 4, 6)
  to cleanly isolate raycast cost from scheduler combinatorial explosion.
- Track B (Exact Scheduler Factorial Scaling): Measures DiscreteTicScheduler.solve
  latency across job counts J in {2, 3, 4, 5, 6, 7, 8, 9, 10} to quantify the O(J! * J)
  permutation enumeration curve.
- Track C (Full Telemetry Simulation & Memory): Measures end-to-end interactive
  playback simulation latency and peak memory allocation.
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
    TicThreatJob,
)


def generate_scaling_document(num_segments: int, num_threats: int) -> CADDocument:
    """Generate synthetic graybox corridor with num_segments and num_threats."""
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
    geometry_threat_counts = [2, 4, 6]
    
    print("=" * 105)
    print("CUT THE CAKE - TRACK A: GEOMETRY RAYCASTING SCALING (BOUNDED THREATS J <= 6)")
    print("=" * 105)
    print(f"{'Segments':<10} | {'Threats':<8} | {'Route Tics':<11} | {'Jobs':<6} | {'Job Comp (p50/max ms)':<25} | {'Fast Tot (p50/max ms)':<22}")
    print("-" * 105)

    track_a_results = []
    for seg in segment_counts:
        for th in geometry_threat_counts:
            doc = generate_scaling_document(seg, th)
            actual_segs = sum(len(o.vertices) for o in doc.obstacles)
            params = doc.player_model.to_combat_params()
            geo_module = doc.to_geometric_module()
            referee = DeterministicSimulationReferee(params)

            route = geo_module.routes[0]
            route_tics = int(math.ceil(route.total_length_m / params.move_m_per_tic))
            jobs = referee.extract_tic_jobs(geo_module, route_index=0)
            compiled_jobs = len(jobs)

            c_p50, c_max = _timed_runs(lambda: referee.extract_tic_jobs(geo_module, route_index=0), runs=5)
            f_p50, f_max = _timed_runs(lambda: analyze_cad_document(doc, include_telemetry=False), runs=5)

            row = {
                "segments_actual": actual_segs,
                "threats_authored": th,
                "route_tics": route_tics,
                "compiled_jobs": compiled_jobs,
                "compile_p50_ms": c_p50,
                "compile_sample_max_ms": c_max,
                "fast_total_p50_ms": f_p50,
                "fast_total_sample_max_ms": f_max,
            }
            track_a_results.append(row)
            print(
                f"{actual_segs:<10} | {th:<8} | {route_tics:<11} | {compiled_jobs:<6} | "
                f"{f'{c_p50:.2f} / {c_max:.2f}':<25} | {f'{f_p50:.2f} / {f_max:.2f}':<22}"
            )

    print("\n" + "=" * 90)
    print("CUT THE CAKE - TRACK B: EXACT SCHEDULER FACTORIAL SCALING O(J! * J)")
    print("=" * 90)
    print(f"{'Compiled Jobs (J)':<20} | {'Permutations J!':<22} | {'Scheduler p50 (ms)':<20} | {'Sample Max (ms)':<18}")
    print("-" * 90)

    doc_sample = generate_scaling_document(50, 2)
    params = doc_sample.player_model.to_combat_params()
    scheduler = DiscreteTicScheduler(params)

    track_b_results = []
    for num_j in range(2, 11):
        test_jobs = [
            TicThreatJob(
                id=f"job_{i}",
                reveal_tic=i * 5,
                due_window_tics=20,
                deadline_tic=i * 5 + 20,
                angle_deg=float((i * 45) % 360),
                threat_anchor=(float(i), 2.0),
                service_duration_tics=4,
            )
            for i in range(num_j)
        ]
        perms = math.factorial(num_j)
        runs_count = 5 if num_j <= 8 else (3 if num_j == 9 else 1)
        s_p50, s_max = _timed_runs(lambda: scheduler.solve(test_jobs), runs=runs_count)

        row = {
            "num_jobs": num_j,
            "permutations_j_fact": perms,
            "scheduler_p50_ms": s_p50,
            "scheduler_sample_max_ms": s_max,
        }
        track_b_results.append(row)
        print(f"{num_j:<20} | {perms:<22} | {s_p50:<20.2f} | {s_max:<18.2f}")

    print("\n" + "=" * 90)
    print("CUT THE CAKE - TRACK C: REPRESENTATIVE FULL TELEMETRY SIMULATION")
    print("=" * 90)
    print(f"{'Segments':<10} | {'Threats':<8} | {'Route Tics':<11} | {'Jobs':<6} | {'Telemetry p50 (ms)':<20} | {'Telemetry sample_max (ms)':<26}")
    print("-" * 90)

    track_c_cells = [(50, 2), (250, 4), (500, 6), (1000, 6), (2500, 6)]
    track_c_results = []
    for seg, th in track_c_cells:
        doc = generate_scaling_document(seg, th)
        actual_segs = sum(len(o.vertices) for o in doc.obstacles)
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
        track_c_results.append(row)
        print(f"{actual_segs:<10} | {th:<8} | {route_tics:<11} | {compiled_jobs:<6} | {t_p50:<20.2f} | {t_max:<26.2f}")

    # Peak memory allocation
    print("\n" + "=" * 90)
    print("CUT THE CAKE: PEAK MEMORY ALLOCATION")
    print("=" * 90)
    tracemalloc.start()
    doc_heavy = generate_scaling_document(5000, 6)
    _ = analyze_cad_document(doc_heavy, include_telemetry=False)
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = round(peak_mem / (1024 * 1024), 2)
    print(f"Peak memory for 5000-segment / 6-threat document analysis: {peak_mb} MB")

    full_payload = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python_version": "3.12",
            "notes": "Track A isolates 2D raycasting scaling across geometry tiers. Track B measures exact scheduler factorial curve O(J! * J). Track C measures full telemetry playback."
        },
        "track_a_geometry_scaling": track_a_results,
        "track_b_scheduler_scaling": track_b_results,
        "track_c_telemetry_samples": track_c_results,
        "peak_memory_mb": peak_mb,
    }
    with open(output_path, "w") as f:
        json.dump(full_payload, f, indent=2)
    print(f"\nResults successfully written to {output_path}")
    return full_payload


if __name__ == "__main__":
    run_scaling_benchmark()
