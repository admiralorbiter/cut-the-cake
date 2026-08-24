"""Tests for Tactical CAD Scene Manifest Contract & Provenance (Milestone 1B).

Verifies that:
1. Exported manifest validates 100% against JSON Schema (scene_manifest_v1.schema.json).
2. Explicit before/after geometry matches Python GeometricModule definitions and repair translations.
3. Timing parameters, reveal/deadline events, and Tactical Margins have zero drift.
4. External engine evidence matches the authoritative frozen Round 11.4A results.json record.
5. Post-death player coordinates in broken playback freeze at the death location.
6. Discrete event completion tics match scheduler completion tics with zero one-tic drift.
7. Exporter is 100% deterministic (reproducible byte-for-byte).
"""

import json
import os
import sys
import pytest

# Compatibility patch for PySide6/shiboken meta_path inspection on Python 3.12
try:
    import six
    for imp in sys.meta_path:
        if not hasattr(imp, "_path"):
            try:
                imp._path = None
            except Exception:
                pass
except Exception:
    pass

from jsonschema.validators import Draft7Validator

from cut_the_cake.cad_export import export_scene_manifest
from cut_the_cake.repair_benchmark import build_unserviceable_population
from cut_the_cake.repair import MinimalRepairOptimizer
from cut_the_cake.vizdoom_engine import TicCombatParameters, DiscreteTicScheduler, DeterministicSimulationReferee


@pytest.fixture(scope="module")
def schema_v1():
    schema_path = os.path.join(os.path.dirname(__file__), "..", "cad", "schema", "scene_manifest_v1.schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def canonical_manifest():
    return export_scene_manifest(
        fixture_id="RepairPop_F1_StaggerDeficit_00",
        scientific_freeze_tag="round11.4a-freeze",
        commit_sha="8a6b557"
    )


@pytest.fixture(scope="module")
def frozen_benchmark_results():
    results_path = os.path.join(os.path.dirname(__file__), "..", "results", "repair", "results.json")
    with open(results_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_manifest_schema_validation(schema_v1, canonical_manifest):
    """Manifest must strictly validate against the versioned JSON Schema."""
    validator = Draft7Validator(schema_v1)
    errors = list(validator.iter_errors(canonical_manifest))
    assert not errors, f"Schema validation errors: {[e.message for e in errors]}"
    assert canonical_manifest["schema_version"] in ("1.0", "1.1")
    assert canonical_manifest["provenance"]["scientific_freeze"] == "round11.4a-freeze"
    assert canonical_manifest["provenance"]["fixture_id"] == "RepairPop_F1_StaggerDeficit_00"
    assert canonical_manifest["provenance"]["evidence_tier"] == "native_engine_verified"


def test_explicit_before_after_geometry_export(canonical_manifest):
    """Manifest must contain authoritative broken and repaired geometry structures."""
    population = build_unserviceable_population(n_per_family=10)
    broken_mod = next(m for m in population if m.module_id == "RepairPop_F1_StaggerDeficit_00")

    # Broken geometry matches module
    bg = canonical_manifest["broken_geometry"]
    mod_b_coords = [[round(float(x), 4), round(float(y), 4)] for x, y in broken_mod.boundary.exterior.coords]
    assert bg["boundary"] == mod_b_coords
    assert len(bg["obstacles"]) == len(broken_mod.obstacles)
    assert bg["route"]["id"] == broken_mod.routes[0].route_id

    # Repaired geometry has shifted obstacle
    rg = canonical_manifest["repaired_geometry"]
    assert rg["boundary"] == bg["boundary"]
    assert len(rg["obstacles"]) == len(broken_mod.obstacles)
    
    # Check shift on obstacle 0
    obs_b = bg["obstacles"][0]["vertices"]
    obs_r = rg["obstacles"][0]["vertices"]
    assert obs_r[0][0] == pytest.approx(obs_b[0][0] + 1.10, abs=1e-3)
    assert obs_r[0][1] == pytest.approx(obs_b[0][1], abs=1e-3)


def test_exported_timing_and_margin_parity(canonical_manifest):
    """Timing parameters, reveal tics, deadline tics, and margins must have zero drift."""
    population = build_unserviceable_population(n_per_family=10)
    broken_mod = next(m for m in population if m.module_id == "RepairPop_F1_StaggerDeficit_00")
    params = TicCombatParameters()

    # Broken scenario parity
    referee = DeterministicSimulationReferee(params)
    scheduler = DiscreteTicScheduler(params)
    jobs = referee.extract_tic_jobs(broken_mod, route_index=0)
    sched_res = scheduler.solve(jobs, initial_reticle_deg=0.0)

    broken_data = canonical_manifest["broken_scenario"]
    assert broken_data["tactical_margin_tics"] == sched_res.tactical_margin_tics
    assert broken_data["l_star_tics"] == sched_res.lateness_optimal_l_star_tics
    assert broken_data["verdict"] == "unserviceable"
    assert broken_data["model_episode_survived"] is False
    assert broken_data["model_death_tic"] == 25

    # Verify per-threat job records
    job_map = {j.id: j for j in jobs}
    for item in broken_data["threat_jobs"]:
        j = job_map[item["id"]]
        assert item["reveal_tic"] == j.reveal_tic
        assert item["deadline_tic"] == j.deadline_tic
        assert item["due_window_tics"] == j.due_window_tics


def test_frozen_deadline_and_window_arithmetic(canonical_manifest):
    """Rigorous audit asserting D_j == R_j + due_window_tics with exact canonical Family 1 values."""
    # 1. Broken Scenario Audit
    b_data = canonical_manifest["broken_scenario"]
    b_jobs = {j["id"]: j for j in b_data["threat_jobs"]}
    
    # Assert due_window arithmetic
    for j in b_data["threat_jobs"]:
        assert j["deadline_tic"] == j["reveal_tic"] + j["due_window_tics"]

    t1_b = b_jobs["F1_T1_L00"]
    assert t1_b["reveal_tic"] == 0
    assert t1_b["due_window_tics"] == 22
    assert t1_b["deadline_tic"] == 22
    assert t1_b["completion_tic"] == 13
    assert t1_b["service_complete_tic"] == 12

    t2_b = b_jobs["F1_T2_R00"]
    assert t2_b["reveal_tic"] == 3
    assert t2_b["due_window_tics"] == 22
    assert t2_b["deadline_tic"] == 25
    assert t2_b["completion_tic"] == 31
    assert t2_b["service_complete_tic"] == 30

    assert b_data["model_death_tic"] == 25
    assert b_data["tactical_margin_tics"] == -6
    assert b_data["l_star_tics"] == 6

    # 2. Repaired Scenario Audit
    r_data = canonical_manifest["repaired_scenario"]
    r_jobs = {j["id"]: j for j in r_data["threat_jobs"]}

    for j in r_data["threat_jobs"]:
        assert j["deadline_tic"] == j["reveal_tic"] + j["due_window_tics"]

    t1_r = r_jobs["F1_T1_L00"]
    assert t1_r["reveal_tic"] == 0
    assert t1_r["due_window_tics"] == 22
    assert t1_r["deadline_tic"] == 22
    assert t1_r["completion_tic"] == 13
    assert t1_r["service_complete_tic"] == 12

    t2_r = r_jobs["F1_T2_R00"]
    assert t2_r["reveal_tic"] == 13
    assert t2_r["due_window_tics"] == 22
    assert t2_r["deadline_tic"] == 35
    assert t2_r["completion_tic"] == 33
    assert t2_r["service_complete_tic"] == 32

    assert r_data["model_death_tic"] is None
    assert r_data["tactical_margin_tics"] == 2
    assert r_data["l_star_tics"] == -2


def test_post_death_telemetry_freeze(canonical_manifest):
    """In broken playback, player coordinates must freeze at death rather than advancing."""
    broken_data = canonical_manifest["broken_scenario"]
    death_tic = broken_data["model_death_tic"]
    assert death_tic is not None

    frames = broken_data["telemetry_frames"]
    death_frame = frames[death_tic]
    death_pos = death_frame["player_pos"]
    death_dist = death_frame["route_dist_m"]

    # All frames after death must remain at death_pos
    for k in range(death_tic + 1, len(frames)):
        f = frames[k]
        assert f["player_pos"] == death_pos, f"Player moved after death at tic {k}!"
        assert f["route_dist_m"] == death_dist
        assert f["controller_state"] == "DEAD"
        assert f["active_target_id"] is None


def test_discrete_service_completion_event_parity(canonical_manifest):
    """SERVICE_COMPLETE event tics must match controller service_complete_tic and scheduler completion_tic."""
    repaired_data = canonical_manifest["repaired_scenario"]
    events = [e for e in repaired_data["events"] if e["type"] == "SERVICE_COMPLETE"]
    
    job_map = {j["id"]: j for j in repaired_data["threat_jobs"]}
    
    assert len(events) == len(repaired_data["threat_jobs"])
    for ev in events:
        job = job_map[ev["threat_id"]]
        # Event is emitted on the final service tic (service_complete_tic)
        assert ev["tic"] == job["service_complete_tic"], f"Event tic {ev['tic']} != service_complete_tic {job['service_complete_tic']}"
        # Scheduler completion boundary C_j marks the next operation start tic
        assert job["completion_tic"] == ev["tic"] + 1, f"Completion tic {job['completion_tic']} != event tic {ev['tic']} + 1"


def test_external_engine_evidence_matches_frozen_results(canonical_manifest, frozen_benchmark_results):
    """Manifest external engine evidence must match the canonical frozen Round 11.4A results record."""
    evidence = canonical_manifest["external_engine_evidence"]
    fixture_id = canonical_manifest["provenance"]["fixture_id"]

    rec = next(r for r in frozen_benchmark_results["records"] if r["arena_id"] == fixture_id)

    assert evidence["broken_engine_survived"] == rec["engine_broken_survived"]
    assert evidence["repaired_engine_survived"] == rec["engine_repaired_survived"]
    assert evidence["survival_flip"] == rec["survival_flip"]
    assert evidence["source_repair_success"] == rec["repair_success"]
    assert evidence["native_engine_rescued"] == rec["engine_repaired_survived"]
    assert evidence["transfer_status"] == "source_success_engine_rescued"
    assert evidence["delta_export_tics"] == rec["delta_export_tics"]
    assert evidence["delta_execution_tics"] == rec["delta_execution_tics"]
    assert evidence["delta_total_tics"] == rec["delta_total_tics"]
    assert evidence["evidence_source"] == "results/repair/results.json"
    assert evidence["evidence_tier"] == "native_engine_verified"


def test_deterministic_reproducibility():
    """Repeated calls to export_scene_manifest must be 100% identical."""
    m1 = export_scene_manifest("RepairPop_F1_StaggerDeficit_00")
    m2 = export_scene_manifest("RepairPop_F1_StaggerDeficit_00")

    json1 = json.dumps(m1, sort_keys=True)
    json2 = json.dumps(m2, sort_keys=True)
    assert json1 == json2
