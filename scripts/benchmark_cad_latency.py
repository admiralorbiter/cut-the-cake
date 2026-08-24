#!/usr/bin/env python3
"""Tactical CAD Authoritative Latency Benchmark Suite.

Milestone 2B.1 Verification Script.
Measures:
1. Fast-path pure Python compute latency (p50, p95, p99).
2. Local Flask REST API round-trip latency (p50, p95, p99).
3. Full committed telemetry episode simulation latency (p50, p95, p99).

Outputs summary table and writes machine-readable results to results/cad/m2b_latency.json.
"""

import os
import json
import time
import numpy as np

from cut_the_cake.cad_document import get_canonical_f1_document, get_custom_asymmetric_corridor_document
from cut_the_cake.cad_adapter import analyze_cad_document, translate_obstacle_in_document
from cut_the_cake.cad_server import create_cad_app


def run_benchmark(n_samples: int = 150) -> dict:
    f1_doc = get_canonical_f1_document()
    custom_doc = get_custom_asymmetric_corridor_document()

    # 1. Pure Python Fast-Path Analysis Latency
    compute_latencies = []
    for step in range(n_samples):
        dx = round((step % 25) * 0.05, 2)
        dy = round(((step // 25) % 5) * 0.05, 2)
        target_doc = f1_doc if step % 2 == 0 else custom_doc
        target_obs = target_doc.obstacles[0].id

        trans_doc, is_valid, _ = translate_obstacle_in_document(target_doc, target_obs, dx, dy)
        if not is_valid:
            trans_doc = target_doc

        t0 = time.perf_counter()
        res = analyze_cad_document(trans_doc, include_telemetry=False)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        compute_latencies.append(dt_ms)

    # 2. Local HTTP REST Round-Trip Latency
    app = create_cad_app()
    client = app.test_client()

    http_latencies = []
    for step in range(n_samples):
        dx = round((step % 25) * 0.05, 2)
        t0 = time.perf_counter()
        resp = client.post("/api/document/translate_obstacle", json={
            "obstacle_id": "wall_0",
            "dx": dx,
            "dy": 0.0,
            "client_revision": step,
            "include_telemetry": False,
            "commit": False
        })
        dt_ms = (time.perf_counter() - t0) * 1000.0
        http_latencies.append(dt_ms)

    # 3. Full Committed Telemetry Generation Latency (100 runs)
    telemetry_latencies = []
    for step in range(100):
        dx = round((step % 23) * 0.05, 2)
        trans_doc, is_valid, _ = translate_obstacle_in_document(f1_doc, "wall_0", dx, 0.0)
        
        t0 = time.perf_counter()
        res = analyze_cad_document(trans_doc, include_telemetry=True)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        telemetry_latencies.append(dt_ms)

    results = {
        "benchmark_name": "Tactical CAD Latency Benchmark",
        "milestone": "M2B.2",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sample_size": n_samples,
        "layers": {
            "source_analysis_compute_fast_path": {
                "unit": "milliseconds",
                "samples": len(compute_latencies),
                "p50_ms": round(float(np.percentile(compute_latencies, 50)), 3),
                "p95_ms": round(float(np.percentile(compute_latencies, 95)), 3),
                "p99_ms": round(float(np.percentile(compute_latencies, 99)), 3),
                "min_ms": round(float(np.min(compute_latencies)), 3),
                "max_ms": round(float(np.max(compute_latencies)), 3)
            },
            "flask_in_process_request_latency": {
                "unit": "milliseconds",
                "samples": len(http_latencies),
                "p50_ms": round(float(np.percentile(http_latencies, 50)), 3),
                "p95_ms": round(float(np.percentile(http_latencies, 95)), 3),
                "p99_ms": round(float(np.percentile(http_latencies, 99)), 3),
                "min_ms": round(float(np.min(http_latencies)), 3),
                "max_ms": round(float(np.max(http_latencies)), 3)
            },
            "full_telemetry_commit_35hz_sim": {
                "unit": "milliseconds",
                "samples": len(telemetry_latencies),
                "p50_ms": round(float(np.percentile(telemetry_latencies, 50)), 3),
                "p95_ms": round(float(np.percentile(telemetry_latencies, 95)), 3),
                "p99_ms": round(float(np.percentile(telemetry_latencies, 99)), 3),
                "min_ms": round(float(np.min(telemetry_latencies)), 3),
                "max_ms": round(float(np.max(telemetry_latencies)), 3)
            }
        }
    }

    print("=" * 80)
    print("CUT THE CAKE - TACTICAL CAD BENCHMARK SUITE (MILESTONE 2B.2)")
    print("=" * 80)
    print(f"{'Metric / Latency Layer':<36} | {'N':<5} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'p99 (ms)':<10}")
    print("-" * 80)
    name_map = {
        "source_analysis_compute_fast_path": "Source Analysis Fast Compute",
        "flask_in_process_request_latency": "Flask In-Process Request Latency",
        "full_telemetry_commit_35hz_sim": "Full Telemetry Commit (35Hz Sim)"
    }
    for k, v in results["layers"].items():
        name = name_map.get(k, k.replace("_", " ").title())
        print(f"{name:<36} | {v['samples']:<5} | {v['p50_ms']:<10.2f} | {v['p95_ms']:<10.2f} | {v['p99_ms']:<10.2f}")
    print("=" * 80)

    # Save artifact
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results", "cad")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "m2b_latency.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results persisted to: {out_path}")

    return results


if __name__ == "__main__":
    run_benchmark()
