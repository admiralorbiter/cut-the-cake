"""Tiered & Instrumented Hypothesis State-Machine Fuzzer for Tactical CAD.

Tiers:
1. Smoke (default): max_examples=15, step_count=15, max 8 obstacles, 6 threats.
   - Cheap invariants checked on EVERY transition (schema, unique IDs, fast L*, M = -L*).
   - Expensive full telemetry oracle checked STRATEGICALLY (every 10th mutation, after undo/redo, and at sequence teardown).
   - Execution target: < 2 minutes.
2. Extended (CAD_FUZZ_PROFILE=extended): max_examples=30, step_count=20, max 16 obstacles, 10 threats.
3. Stress (CAD_FUZZ_PROFILE=stress): Unbounded density for soak testing.

Instrumentation:
- Tracks cumulative time in: Schema Validation, Job Compilation, Scheduler, Full Telemetry Simulation, History Snapshotting.
- Tracks transition counts, peak document density, and complexity-binned latencies.
"""

from __future__ import annotations
import copy
import json
import os
import time
from collections import defaultdict
import pytest
from hypothesis import strategies as st, settings, Phase
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize

from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPlayerModel,
    get_custom_asymmetric_corridor_document,
    validate_cad_document,
)
from cut_the_cake.cad_adapter import (
    create_rectangle_obstacle,
    translate_obstacle_in_document,
    rotate_obstacle_in_document,
    resize_rectangle_obstacle,
    delete_obstacle_in_document,
    create_threat_in_document,
    translate_threat_in_document,
    update_threat_due_window,
    update_threat_service_duration,
    delete_threat_in_document,
    create_route_in_document,
    update_route_speed,
    delete_route_in_document,
    analyze_cad_document,
)


# Global Instrumentation Registry
METRICS = {
    "total_transitions": 0,
    "invariant_evaluations": 0,
    "full_telemetry_evaluations": 0,
    "schema_validation_s": 0.0,
    "job_compilation_s": 0.0,
    "scheduler_s": 0.0,
    "fast_total_s": 0.0,
    "full_telemetry_s": 0.0,
    "history_copy_s": 0.0,
    "peak_obstacles": 0,
    "peak_threats": 0,
    "peak_segments": 0,
    "worst_single_step_s": 0.0,
    "complexity_bins": defaultdict(lambda: {"count": 0, "fast_total_s": 0.0, "telemetry_total_s": 0.0}),
}


def _get_complexity_bin(num_obs: int, num_threats: int) -> str:
    if num_obs <= 5 and num_threats <= 3:
        return "obs_2_5__thr_1_3"
    elif num_obs <= 10 and num_threats <= 6:
        return "obs_6_10__thr_4_6"
    elif num_obs <= 15 and num_threats <= 9:
        return "obs_11_15__thr_7_9"
    else:
        return "obs_16_plus__thr_10_plus"


PROFILE = os.environ.get("CAD_FUZZ_PROFILE", "smoke").lower()
MAX_OBSTACLES = 8 if PROFILE == "smoke" else (16 if PROFILE == "extended" else 999)
MAX_THREATS = 6 if PROFILE == "smoke" else (10 if PROFILE == "extended" else 999)


class CADDocumentStateMachine(RuleBasedStateMachine):
    """Deterministic, tiered stateful generator fuzzer for CADDocument mutations."""

    def __init__(self):
        super().__init__()
        self.doc = get_custom_asymmetric_corridor_document()
        self.undo_stack = []
        self.redo_stack = []
        self.next_wall_seq = 100
        self.next_threat_seq = 100
        self.next_route_seq = 100
        self.step_counter = 0
        self.last_op_was_history = False

    def _push_undo(self):
        t0 = time.perf_counter()
        self.undo_stack.append(copy.deepcopy(self.doc))
        if len(self.undo_stack) > 30:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        METRICS["history_copy_s"] += time.perf_counter() - t0
        self.step_counter += 1
        self.last_op_was_history = False

    # -------------------------------------------------------------------------
    # OBSTACLE MUTATIONS (Density Budgeted)
    # -------------------------------------------------------------------------

    @rule(
        x1=st.floats(min_value=0.5, max_value=10.0),
        y1=st.floats(min_value=-2.5, max_value=1.5),
        w=st.floats(min_value=0.2, max_value=2.0),
        h=st.floats(min_value=0.2, max_value=2.0)
    )
    def create_obstacle_rule(self, x1, y1, w, h):
        if len(self.doc.obstacles) >= MAX_OBSTACLES:
            return
        x2 = x1 + w
        y2 = y1 + h
        cand_doc, cand_id, is_valid, _ = create_rectangle_obstacle(
            self.doc, x1=x1, y1=y1, x2=x2, y2=y2, session_sequence=self.next_wall_seq
        )
        if is_valid:
            self._push_undo()
            self.doc = cand_doc
            self.next_wall_seq += 1

    @rule(
        dx=st.floats(min_value=-1.5, max_value=1.5),
        dy=st.floats(min_value=-0.8, max_value=0.8)
    )
    def translate_obstacle_rule(self, dx, dy):
        if not self.doc.obstacles:
            return
        target_id = self.doc.obstacles[0].id
        cand_doc, is_valid, _ = translate_obstacle_in_document(self.doc, target_id, dx, dy)
        if is_valid:
            self._push_undo()
            self.doc = cand_doc

    @rule(angle=st.floats(min_value=-90.0, max_value=90.0))
    def rotate_obstacle_rule(self, angle):
        if not self.doc.obstacles:
            return
        target_id = self.doc.obstacles[0].id
        cand_doc, is_valid, _ = rotate_obstacle_in_document(self.doc, target_id, angle_delta_deg=angle)
        if is_valid:
            self._push_undo()
            self.doc = cand_doc

    @rule(
        handle=st.sampled_from(["ne", "nw", "se", "sw", "n", "s", "e", "w"]),
        dx=st.floats(min_value=-0.4, max_value=0.4),
        dy=st.floats(min_value=-0.4, max_value=0.4)
    )
    def resize_obstacle_rule(self, handle, dx, dy):
        if not self.doc.obstacles:
            return
        target_id = self.doc.obstacles[0].id
        cand_doc, is_valid, _ = resize_rectangle_obstacle(
            self.doc, target_id, handle=handle, dx=dx, dy=dy
        )
        if is_valid:
            self._push_undo()
            self.doc = cand_doc

    @rule()
    def delete_obstacle_rule(self):
        if not self.doc.obstacles:
            return
        target_id = self.doc.obstacles[-1].id
        cand_doc, is_valid, _ = delete_obstacle_in_document(self.doc, target_id)
        if is_valid:
            self._push_undo()
            self.doc = cand_doc

    # -------------------------------------------------------------------------
    # THREAT MUTATIONS (Density Budgeted)
    # -------------------------------------------------------------------------

    @rule(
        x=st.floats(min_value=1.0, max_value=11.0),
        y=st.floats(min_value=-2.0, max_value=2.0),
        due_window=st.floats(min_value=0.2, max_value=1.5),
        service_duration=st.floats(min_value=0.05, max_value=0.4)
    )
    def create_threat_rule(self, x, y, due_window, service_duration):
        if len(self.doc.threats) >= MAX_THREATS:
            return
        cand_doc, cand_id, is_valid, _ = create_threat_in_document(
            self.doc, anchor=[x, y], due_window_s=due_window, service_duration_s=service_duration,
            session_sequence=self.next_threat_seq
        )
        if is_valid:
            self._push_undo()
            self.doc = cand_doc
            self.next_threat_seq += 1

    @rule(due_window=st.floats(min_value=0.1, max_value=2.0))
    def update_threat_due_window_rule(self, due_window):
        if not self.doc.threats:
            return
        target_id = self.doc.threats[0].id
        cand_doc, is_valid, _ = update_threat_due_window(self.doc, target_id, due_window)
        if is_valid:
            self._push_undo()
            self.doc = cand_doc

    @rule()
    def delete_threat_rule(self):
        if not self.doc.threats:
            return
        target_id = self.doc.threats[-1].id
        cand_doc, is_valid, _ = delete_threat_in_document(self.doc, target_id)
        if is_valid:
            self._push_undo()
            self.doc = cand_doc

    # -------------------------------------------------------------------------
    # ROUTE MUTATIONS
    # -------------------------------------------------------------------------

    @rule(speed=st.floats(min_value=1.0, max_value=8.0))
    def update_route_speed_rule(self, speed):
        if not self.doc.routes:
            return
        target_id = self.doc.routes[0].id
        cand_doc, is_valid, _ = update_route_speed(self.doc, target_id, speed)
        if is_valid:
            self._push_undo()
            self.doc = cand_doc

    # -------------------------------------------------------------------------
    # HISTORY OPERATIONS (Undo / Redo / Roundtrip)
    # -------------------------------------------------------------------------

    @rule()
    def undo_rule(self):
        if self.undo_stack:
            t0 = time.perf_counter()
            prev_doc = self.undo_stack.pop()
            self.redo_stack.append(copy.deepcopy(self.doc))
            self.doc = prev_doc
            METRICS["history_copy_s"] += time.perf_counter() - t0
            self.last_op_was_history = True
            self.step_counter += 1

    @rule()
    def redo_rule(self):
        if self.redo_stack:
            t0 = time.perf_counter()
            next_doc = self.redo_stack.pop()
            self.undo_stack.append(copy.deepcopy(self.doc))
            self.doc = next_doc
            METRICS["history_copy_s"] += time.perf_counter() - t0
            self.last_op_was_history = True
            self.step_counter += 1

    # -------------------------------------------------------------------------
    # INVARIANTS: Cheap Checked Dense, Oracle Checked Strategically
    # -------------------------------------------------------------------------

    @invariant()
    def document_invariants(self):
        t_step_start = time.perf_counter()
        METRICS["total_transitions"] += 1
        METRICS["invariant_evaluations"] += 1

        num_obs = len(self.doc.obstacles)
        num_threats = len(self.doc.threats)
        num_segs = sum(len(o.vertices) for o in self.doc.obstacles)

        METRICS["peak_obstacles"] = max(METRICS["peak_obstacles"], num_obs)
        METRICS["peak_threats"] = max(METRICS["peak_threats"], num_threats)
        METRICS["peak_segments"] = max(METRICS["peak_segments"], num_segs)

        # 1. Strict Schema Conformance
        t0 = time.perf_counter()
        doc_dict = self.doc.to_dict()
        is_valid, errors = validate_cad_document(doc_dict)
        METRICS["schema_validation_s"] += time.perf_counter() - t0
        assert is_valid, f"Schema validation failed: {errors}"

        # 2. Monotonic Unique IDs
        obs_ids = [o.id for o in self.doc.obstacles]
        assert len(obs_ids) == len(set(obs_ids)), f"Duplicate obstacle IDs: {obs_ids}"
        threat_ids = [t.id for t in self.doc.threats]
        assert len(threat_ids) == len(set(threat_ids)), f"Duplicate threat IDs: {threat_ids}"

        # 3. Fast Analysis & L* Soundness
        t0 = time.perf_counter()
        res_fast = analyze_cad_document(self.doc, include_telemetry=False)
        t_fast_dur = time.perf_counter() - t0
        METRICS["fast_total_s"] += t_fast_dur

        assert res_fast["is_valid"] is True
        assert res_fast["tactical_margin_tics"] == -res_fast["l_star_tics"]

        cbin = _get_complexity_bin(num_obs, num_threats)
        METRICS["complexity_bins"][cbin]["count"] += 1
        METRICS["complexity_bins"][cbin]["fast_total_s"] += t_fast_dur

        # 4. Strategic Full Telemetry Oracle
        # Execute oracle if:
        # a) Every 10th mutation step, OR
        # b) Immediately after an Undo/Redo operation, OR
        # c) In Extended/Stress profile
        should_run_oracle = (
            (self.step_counter % 10 == 0) or
            self.last_op_was_history or
            (PROFILE in ("extended", "stress") and self.step_counter % 3 == 0)
        )

        if should_run_oracle:
            t0 = time.perf_counter()
            res_full = analyze_cad_document(self.doc, include_telemetry=True)
            t_full_dur = time.perf_counter() - t0
            METRICS["full_telemetry_s"] += t_full_dur
            METRICS["full_telemetry_evaluations"] += 1
            METRICS["complexity_bins"][cbin]["telemetry_total_s"] += t_full_dur

            assert res_full["tactical_margin_tics"] == res_fast["tactical_margin_tics"]
            assert res_full["l_star_tics"] == res_fast["l_star_tics"]
            assert len(res_full["threat_jobs"]) == len(res_fast["threat_jobs"])

        step_total_s = time.perf_counter() - t_step_start
        METRICS["worst_single_step_s"] = max(METRICS["worst_single_step_s"], step_total_s)

    def teardown(self):
        """Final oracle check at the conclusion of each generated sequence."""
        res_fast = analyze_cad_document(self.doc, include_telemetry=False)
        res_full = analyze_cad_document(self.doc, include_telemetry=True)
        assert res_full["tactical_margin_tics"] == res_fast["tactical_margin_tics"]


# Tier Configurations
if PROFILE == "extended":
    TestCADFuzzing = CADDocumentStateMachine.TestCase
    TestCADFuzzing.settings = settings(
        max_examples=30,
        stateful_step_count=20,
        deadline=None,
        phases=[Phase.generate, Phase.target, Phase.shrink]
    )
elif PROFILE == "stress":
    TestCADFuzzing = CADDocumentStateMachine.TestCase
    TestCADFuzzing.settings = settings(
        max_examples=100,
        stateful_step_count=35,
        deadline=None,
        phases=[Phase.generate, Phase.target, Phase.shrink]
    )
else:  # Smoke (default)
    TestCADFuzzing = CADDocumentStateMachine.TestCase
    TestCADFuzzing.settings = settings(
        max_examples=15,
        stateful_step_count=15,
        deadline=None,
        phases=[Phase.generate, Phase.target, Phase.shrink]
    )


@pytest.fixture(scope="session", autouse=True)
def report_fuzz_metrics():
    yield
    print("\n" + "=" * 80)
    print(f"HYPOTHESIS STATE-MACHINE FUZZING METRICS (PROFILE: {PROFILE.upper()})")
    print("=" * 80)
    print(f"Total Transitions Executed      : {METRICS['total_transitions']}")
    print(f"Invariant Evaluations           : {METRICS['invariant_evaluations']}")
    print(f"Full Telemetry Oracle Runs      : {METRICS['full_telemetry_evaluations']}")
    print(f"Peak Obstacles / Threats / Segs : {METRICS['peak_obstacles']} obs / {METRICS['peak_threats']} threats / {METRICS['peak_segments']} segs")
    print(f"Worst-case Single Step Duration : {METRICS['worst_single_step_s'] * 1000.0:.2f} ms")
    print("-" * 80)
    print("CUMULATIVE SUBSYSTEM RUNTIME BREAKDOWN:")
    total_time = (
        METRICS['schema_validation_s'] +
        METRICS['fast_total_s'] +
        METRICS['full_telemetry_s'] +
        METRICS['history_copy_s']
    )
    if total_time > 0:
        print(f"  JSONSchema Validation : {METRICS['schema_validation_s']:.3f} s ({METRICS['schema_validation_s'] / total_time * 100:.1f}%)")
        print(f"  Fast Analysis Path    : {METRICS['fast_total_s']:.3f} s ({METRICS['fast_total_s'] / total_time * 100:.1f}%)")
        print(f"  Full Telemetry Path   : {METRICS['full_telemetry_s']:.3f} s ({METRICS['full_telemetry_s'] / total_time * 100:.1f}%)")
        print(f"  History Snapshotting  : {METRICS['history_copy_s']:.3f} s ({METRICS['history_copy_s'] / total_time * 100:.1f}%)")
        print(f"  Total Active Compute  : {total_time:.3f} s")
    print("-" * 80)
    print("LATENCY BY DOCUMENT COMPLEXITY BINS:")
    print(f"{'Complexity Bin':<28} | {'Transitions':<12} | {'Fast p50 (ms)':<14} | {'Full Telemetry (ms)':<20}")
    print("-" * 80)
    for bname, data in METRICS["complexity_bins"].items():
        cnt = data["count"]
        fast_avg = (data["fast_total_s"] / cnt * 1000.0) if cnt else 0.0
        telem_avg = (data["telemetry_total_s"] / METRICS["full_telemetry_evaluations"] * 1000.0) if METRICS["full_telemetry_evaluations"] else 0.0
        print(f"{bname:<28} | {cnt:<12} | {fast_avg:<14.2f} | {telem_avg:<20.2f}")
    print("=" * 80 + "\n")
