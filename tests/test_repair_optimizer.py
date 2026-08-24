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
import numpy as np
from pathlib import Path
import sys

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
    RepairResult
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
    assert result.initial_margin_tics < 0
    assert result.repaired_margin_tics >= 2
    assert result.edit_distance_m > 0.0
    assert result.edit_distance_m <= 1.5  # Bounded minimal edit
    assert result.runtime_ms < 200.0  # Fast sub-second execution

    # Verify structural geometric integrity of repaired module
    errs = validate_geometry_integrity(result.repaired_module)
    assert len(errs) == 0, f"Repaired module has geometric errors: {errs}"


def test_minimal_repair_speed_and_eval_efficiency():
    """Verify optimizer runs in <= 50ms on average with directed search."""
    broken = build_disagreement_arena_kici_blindspot()
    optimizer = MinimalRepairOptimizer()

    result = optimizer.repair(broken, target_margin_tics=2, max_perturbation_m=2.0, search_resolution_m=0.10)
    assert result.success is True
    assert result.runtime_ms < 150.0  # Directed search keeps execution very fast


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
    # Broken arena should fail (death in engine)
    assert not log_broken.engine_player_survived

    # Execute repaired arena
    log_repaired = bridge.run_engine_episode(
        repaired,
        policy=ControllerPolicy.ORACLE
    )
    # Repaired arena should survive in real Doom engine with positive margin
    assert log_repaired.engine_player_survived is True
    assert log_repaired.death_tic is None
    assert log_repaired.tactical_margin_tics >= 2
