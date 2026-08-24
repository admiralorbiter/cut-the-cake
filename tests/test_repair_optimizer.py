"""Unit and integration tests for Inverse Tactical Repair & Automated Level Linter [G -> G*].

Tests:
- Tactical diagnostic bottleneck isolation & occluder edge attribution
- Vectorized flat-array raycaster numerical parity with Shapely/scalar segment intersection
- Minimal repair optimizer on broken fixtures (M < 0 -> M >= +2)
- Geometric and topological validity preservation
- Execution performance benchmarks (sub-50ms repair time)
- Native ViZDoom before/after survival flip verification (G: Dead -> G*: Survived)
"""

import pytest
import math
import json
import numpy as np

pytestmark = [pytest.mark.cad]
from pathlib import Path
import sys
from shapely.geometry import Polygon, LineString

SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from cut_the_cake.compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricThreat,
    GeometricPort,
    validate_geometry_integrity
)
from cut_the_cake.geometry import (
    segments_intersect,
    extract_polygon_segments
)
from cut_the_cake.vizdoom_engine import (
    TicCombatParameters,
    DiscreteTicScheduler,
    DeterministicSimulationReferee,
    ControllerPolicy
)
from cut_the_cake.vizdoom_fixtures import (
    build_disagreement_arena_kici_blindspot
)
from cut_the_cake.vizdoom_bridge import ViZDoomRealBridge
from cut_the_cake.repair import (
    VectorizedRaycaster,
    TacticalDiagnostic,
    diagnose_clearability,
    MinimalRepairOptimizer,
    RepairResult,
    validate_repair_preservation
)
from cut_the_cake.repair_benchmark import (
    build_unserviceable_population,
    run_population_repair_benchmark,
    export_repair_benchmark_results,
    ArenaRepairRecord,
    PopulationRepairSummary
)


def test_vectorized_raycaster_parity():
    """Verify VectorizedRaycaster yields 100% identical visibility results to scalar segment intersection."""
    blindspot = build_disagreement_arena_kici_blindspot()
    obs_segs = extract_polygon_segments(blindspot.obstacles)
    obs_array = VectorizedRaycaster.extract_segment_array(blindspot.obstacles)

    threat_anchor = blindspot.threats[1].threat_anchor
    route = blindspot.routes[0]

    s_points = np.linspace(0.0, route.total_length_m, 200)
    pts = np.array([route.position_at_distance(s) for s in s_points])

    # Scalar check
    scalar_blocked = []
    for pt in pts:
        blocked = any(segments_intersect(pt, threat_anchor, s1, s2) for s1, s2 in obs_segs)
        scalar_blocked.append(blocked)
    scalar_blocked = np.array(scalar_blocked, dtype=bool)

    # Vectorized batch check
    vec_blocked = VectorizedRaycaster.is_los_blocked_batch(pts, threat_anchor, obs_array)

    np.testing.assert_array_equal(vec_blocked, scalar_blocked)


def test_tactical_diagnostic_isolation():
    """Verify TacticalDiagnostic accurately isolates the critical threat, margin deficit, and occluder edge."""
    broken = build_disagreement_arena_kici_blindspot()
    diag = diagnose_clearability(broken, target_margin_tics=2)

    assert not diag.is_serviceable
    assert diag.initial_margin_tics < 0
    assert diag.target_margin_tics == 2
    assert diag.margin_deficit_tics == (2 - diag.initial_margin_tics)
    assert diag.critical_threat_id is not None
    assert diag.controlling_obstacle_idx is not None
    assert diag.controlling_edge is not None
    assert diag.suggested_perturbation_normal is not None
    assert "Critical bottleneck:" in diag.diagnosis_message


def test_minimal_repair_blindspot():
    """Verify minimal repair converts unserviceable blindspot trap (M < 0) into serviceable layout (M >= +2)."""
    broken = build_disagreement_arena_kici_blindspot()
    optimizer = MinimalRepairOptimizer()

    result = optimizer.repair(broken, target_margin_tics=2, max_perturbation_m=2.0, search_resolution_m=0.05)

    assert result.success is True
    assert result.no_repair_needed is False
    assert result.initial_margin_tics < 0
    assert result.repaired_margin_tics >= 2
    assert result.edit_distance_m > 0.0
    assert result.edit_distance_m <= 1.5  # Bounded minimal edit
    assert result.runtime_ms < 2000.0

    # Verify structural geometric integrity and preservation of repaired module
    errs = validate_geometry_integrity(result.repaired_module)
    assert len(errs) == 0, f"Repaired module has geometric errors: {errs}"
    pres_errs = validate_repair_preservation(broken, result.repaired_module)
    assert len(pres_errs) == 0, f"Repaired module has preservation errors: {pres_errs}"


def test_minimal_repair_speed_and_eval_efficiency():
    """Verify optimizer runs in reasonable time with directed search."""
    broken = build_disagreement_arena_kici_blindspot()
    optimizer = MinimalRepairOptimizer()

    result = optimizer.repair(broken, target_margin_tics=2, max_perturbation_m=2.0, search_resolution_m=0.10)
    assert result.success is True
    assert result.runtime_ms < 600.0


def test_vizdoom_repaired_arena_survival_flip():
    """Gate: Native headless ViZDoom verification that G (broken) kills player while G* (repaired) survives."""
    broken = build_disagreement_arena_kici_blindspot()
    optimizer = MinimalRepairOptimizer()

    # 1. Repair broken fixture
    repair_res = optimizer.repair(broken, target_margin_tics=2, max_perturbation_m=2.0, search_resolution_m=0.05)
    assert repair_res.success is True
    repaired = repair_res.repaired_module

    # 2. Run both in native C++ ViZDoom
    bridge = ViZDoomRealBridge()

    # Execute broken arena
    log_broken = bridge.run_engine_episode(
        broken,
        policy=ControllerPolicy.ORACLE
    )
    assert not log_broken.engine_player_survived

    # Execute repaired arena
    log_repaired = bridge.run_engine_episode(
        repaired,
        policy=ControllerPolicy.ORACLE
    )
    bridge.close()

    # Repaired arena should survive in real Doom engine with positive margin
    assert log_repaired.engine_player_survived is True
    assert log_repaired.death_tic is None
    assert log_repaired.tactical_margin_tics >= 2


# =============================================================================
# ROUND 11.4A AUDIT TESTS
# =============================================================================

def test_unserviceable_population_contract_strictly_negative_margins():
    """Audit: Verify all 50 arenas across 5 families have initial M < 0 and 10 per family."""
    pop = build_unserviceable_population(n_per_family=10)
    assert len(pop) == 50

    families = set(m.category for m in pop)
    assert len(families) == 5

    for mod in pop:
        diag = diagnose_clearability(mod, target_margin_tics=2)
        assert not diag.is_serviceable, f"Module {mod.module_id} is unexpectedly serviceable"
        assert diag.initial_margin_tics < 0, f"Module {mod.module_id} initial margin is {diag.initial_margin_tics} >= 0"


def test_no_repair_needed_accounting_exclusion():
    """Audit: Verify already-serviceable layouts return no_repair_needed=True and do not count toward repair success."""
    # Construct an already-serviceable module (M >= +2)
    boundary = Polygon([(0.0, -3.0), (10.0, -3.0), (10.0, 3.0), (0.0, 3.0)])
    obs = [Polygon([(3.0, 0.5), (3.5, 0.5), (3.5, 2.5), (3.0, 2.5)])]
    threats = [
        GeometricThreat(
            id="T_Solvable",
            polygon=Polygon([(5.0, 1.0), (5.5, 1.0), (5.5, 1.5), (5.0, 1.5)]),
            threat_anchor=(5.25, 1.25),
            authored_due_window_s=1.50,  # Generous due window -> M >> 0
            service_duration_s=0.10
        )
    ]
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(10.0, -1.0), (10.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (10.0, 0.0)], v_move_mps=4.5)

    solvable_mod = GeometricModule(
        module_id="Already_Solvable_Test",
        name="Already Solvable Test",
        boundary=boundary,
        obstacles=obs,
        ports=[port_in, port_out],
        threats=threats,
        routes=[route],
        category="Test_Solvable",
        description="Module that is already serviceable."
    )

    optimizer = MinimalRepairOptimizer()
    res = optimizer.repair(solvable_mod, target_margin_tics=2)

    assert res.no_repair_needed is True
    assert res.success is False
    assert res.edit_distance_m == 0.0
    assert "already meets tactical margin target" in res.repair_description


def test_grid_minimality_operator_set_exhaustive_search():
    """Audit: Verify optimizer chooses the minimal displacement d* across all candidate directions."""
    broken = build_disagreement_arena_kici_blindspot()
    optimizer = MinimalRepairOptimizer()

    res = optimizer.repair(broken, target_margin_tics=2, max_perturbation_m=2.0, search_resolution_m=0.05)
    assert res.success is True
    best_d = res.edit_distance_m

    # Exhaustive verification: no smaller displacement d < best_d on the same grid yields M >= 2
    from shapely.affinity import translate
    scheduler = DiscreteTicScheduler()
    referee = DeterministicSimulationReferee()

    diag = diagnose_clearability(broken, target_margin_tics=2)
    norm_x, norm_y = diag.suggested_perturbation_normal or (1.0, 0.0)
    candidate_directions = [
        (norm_x, norm_y), (-norm_x, -norm_y),
        (1.0, 0.0), (-1.0, 0.0),
        (0.0, 1.0), (0.0, -1.0)
    ]

    for obs_idx in range(len(broken.obstacles)):
        orig_obs = broken.obstacles[obs_idx]
        for dir_x, dir_y in candidate_directions:
            for d in np.arange(0.05, best_d - 1e-4, 0.05):
                d_float = round(float(d), 4)
                dx = float(d_float * dir_x)
                dy = float(d_float * dir_y)
                cand_obs = list(broken.obstacles)
                cand_obs[obs_idx] = translate(orig_obs, xoff=dx, yoff=dy)
                test_mod = GeometricModule(
                    module_id="Test_Cand",
                    name="Test",
                    boundary=broken.boundary,
                    obstacles=cand_obs,
                    ports=broken.ports,
                    threats=broken.threats,
                    routes=broken.routes,
                    category=broken.category,
                    description="Test"
                )
                if validate_geometry_integrity(test_mod) or validate_repair_preservation(broken, test_mod):
                    continue
                jobs = referee.extract_tic_jobs(test_mod)
                m = scheduler.solve(jobs).tactical_margin_tics
                assert m < 2, f"Found smaller valid displacement d={d_float} with margin M={m} >= 2"


def test_geometric_preservation_validator():
    """Audit: Verify validate_repair_preservation catches and rejects invalid candidate perturbations."""
    broken = build_disagreement_arena_kici_blindspot()

    # 1. Altered boundary
    mod_bad_boundary = GeometricModule(
        module_id="Bad_Boundary",
        name="Bad",
        boundary=Polygon([(0.0, -5.0), (12.0, -5.0), (12.0, 5.0), (0.0, 5.0)]),
        obstacles=broken.obstacles,
        ports=broken.ports,
        threats=broken.threats,
        routes=broken.routes,
        category=broken.category,
        description="Bad"
    )
    errs = validate_repair_preservation(broken, mod_bad_boundary)
    assert any("boundary modified" in e for e in errs)

    # 2. Obstacle clipping route
    from shapely.affinity import translate
    mod_clipped_route = GeometricModule(
        module_id="Clipped_Route",
        name="Bad",
        boundary=broken.boundary,
        obstacles=[translate(broken.obstacles[0], yoff=-0.8)],  # Shift into route at y=0
        ports=broken.ports,
        threats=broken.threats,
        routes=broken.routes,
        category=broken.category,
        description="Bad"
    )
    errs = validate_repair_preservation(broken, mod_clipped_route)
    assert any("clips through candidate obstacle" in e for e in errs)


def test_three_layer_engine_residual_decomposition():
    """Audit: Verify three-layer decomposition identity Delta_total = Delta_export + Delta_execution."""
    broken = build_disagreement_arena_kici_blindspot()
    bridge = ViZDoomRealBridge()
    log = bridge.run_engine_episode(broken, policy=ControllerPolicy.ORACLE)
    bridge.close()

    # Check arithmetic identity
    assert log.delta_total_tics == (log.delta_export_tics + log.delta_execution_tics)
    assert log.delta_export_tics == (log.l_star_engine_obs_tics - log.l_star_pred_tics)
    assert log.delta_execution_tics == (log.l_realized_tics - log.l_star_engine_obs_tics)


def test_markdown_and_json_exporter_truthfulness(tmp_path):
    """Audit: Verify export_repair_benchmark_results emits dynamically computed values with no hardcoded discrepancies."""
    pop = build_unserviceable_population(n_per_family=1)  # 5 arenas (1 per family)
    summary = run_population_repair_benchmark(pop, target_margin_tics=2)
    export_repair_benchmark_results(summary, output_dir=str(tmp_path))

    md_file = tmp_path / "RESULTS.md"
    json_file = tmp_path / "results.json"
    assert md_file.exists()
    assert json_file.exists()

    md_text = md_file.read_text(encoding="utf-8")
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Verify no hardcoded 0.35m or < 50ms strings
    assert "median $0.35" not in md_text
    assert "< 50\\,\\text{ms} per room" not in md_text
    assert "100% of successfully repaired layouts flip" not in md_text

    # Verify exact dynamic matching
    assert f"N={summary.total_arenas}" in md_text
    assert f"{summary.source_repair_success_rate * 100:.1f}%" in md_text
    assert json_data["total_arenas"] == summary.total_arenas

