"""Tests for Tactical CAD Scene Manifest Contract & Exporter (Milestone 1A).

Verifies that:
1. Exported manifest validates 100% against JSON Schema (scene_manifest_v1.schema.json).
2. Manifest geometry exactly matches authoritative Python GeometricModule fixtures.
3. Timing parameters, reveal/deadline events, and Tactical Margins have zero drift.
4. Repair operator, displacement, and preservation status match MinimalRepairOptimizer.
5. Engine outcomes match canonical frozen Round 11.4A evidence.
6. Exporter is 100% deterministic (reproducible byte-for-byte).
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
from cut_the_cake.repair import MinimalRepairOptimizer, diagnose_clearability, validate_repair_preservation
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


def test_manifest_schema_validation(schema_v1, canonical_manifest):
    """Manifest must strictly validate against the versioned JSON Schema."""
    validator = Draft7Validator(schema_v1)
    errors = list(validator.iter_errors(canonical_manifest))
    assert not errors, f"Schema validation errors: {[e.message for e in errors]}"
    assert canonical_manifest["schema_version"] == "1.0"
    assert canonical_manifest["provenance"]["scientific_freeze"] == "round11.4a-freeze"
    assert canonical_manifest["provenance"]["fixture_id"] == "RepairPop_F1_StaggerDeficit_00"
    assert canonical_manifest["provenance"]["evidence_tier"] == "native_engine_verified"


def test_exported_geometry_matches_python_fixture(canonical_manifest):
    """Manifest coordinates must match Python GeometricModule definitions."""
    population = build_unserviceable_population(n_per_family=10)
    mod = next(m for m in population if m.module_id == "RepairPop_F1_StaggerDeficit_00")

    # Boundary
    mod_b_coords = [[round(float(x), 4), round(float(y), 4)] for x, y in mod.boundary.exterior.coords]
    assert canonical_manifest["geometry"]["boundary"] == mod_b_coords

    # Obstacles
    assert len(canonical_manifest["geometry"]["obstacles"]) == len(mod.obstacles)
    for idx, obs in enumerate(mod.obstacles):
        obs_coords = [[round(float(x), 4), round(float(y), 4)] for x, y in obs.exterior.coords]
        assert canonical_manifest["geometry"]["obstacles"][idx]["vertices"] == obs_coords

    # Route
    assert canonical_manifest["geometry"]["route"]["id"] == mod.routes[0].route_id
    assert canonical_manifest["geometry"]["route"]["total_length_m"] == round(mod.routes[0].total_length_m, 4)

    # Threats
    assert len(canonical_manifest["geometry"]["threats"]) == len(mod.threats)
    for idx, t in enumerate(mod.threats):
        assert canonical_manifest["geometry"]["threats"][idx]["id"] == t.id
        assert canonical_manifest["geometry"]["threats"][idx]["anchor"] == [round(float(t.threat_anchor[0]), 4), round(float(t.threat_anchor[1]), 4)]


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
    assert broken_data["engine_survived"] is False
    assert broken_data["death_tic"] is not None

    # Verify per-threat job records
    job_map = {j.id: j for j in jobs}
    for item in broken_data["threat_jobs"]:
        j = job_map[item["id"]]
        assert item["reveal_tic"] == j.reveal_tic
        assert item["deadline_tic"] == j.deadline_tic
        assert item["due_window_tics"] == j.due_window_tics


def test_repair_operator_and_displacement_parity(canonical_manifest):
    """Repair operator and displacement must match MinimalRepairOptimizer output."""
    population = build_unserviceable_population(n_per_family=10)
    broken_mod = next(m for m in population if m.module_id == "RepairPop_F1_StaggerDeficit_00")
    params = TicCombatParameters()

    optimizer = MinimalRepairOptimizer(params=params)
    repair_res = optimizer.repair(broken_mod, target_margin_tics=2)
    assert repair_res.success

    repair_data = canonical_manifest["repair"]
    assert repair_data["operator"] == "obstacle_translation"
    assert repair_data["edit_distance_m"] == round(repair_res.edit_distance_m, 4)
    assert repair_data["preservation_validated"] is True

    repaired_data = canonical_manifest["repaired_scenario"]
    assert repaired_data["tactical_margin_tics"] == repair_res.repaired_margin_tics
    assert repaired_data["tactical_margin_tics"] >= 2
    assert repaired_data["verdict"] == "serviceable"
    assert repaired_data["engine_survived"] is True
    assert repaired_data["death_tic"] is None


def test_broken_and_repaired_engine_outcomes_match_frozen_evidence(canonical_manifest):
    """External engine bridge metadata must match the canonical frozen Round 11.4A results."""
    ext = canonical_manifest["external_engine_bridge"]
    assert ext["broken_engine_survived"] is False
    assert ext["repaired_engine_survived"] is True
    assert ext["delta_export_tics"] == 0
    assert ext["delta_execution_tics"] == 0
    assert ext["delta_total_tics"] == 0
    assert ext["transfer_efficiency"] == 1.0


def test_deterministic_reproducibility():
    """Repeated calls to export_scene_manifest must be 100% identical."""
    m1 = export_scene_manifest("RepairPop_F1_StaggerDeficit_00")
    m2 = export_scene_manifest("RepairPop_F1_StaggerDeficit_00")

    json1 = json.dumps(m1, sort_keys=True)
    json2 = json.dumps(m2, sort_keys=True)
    assert json1 == json2
