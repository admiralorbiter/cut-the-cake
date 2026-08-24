"""Unit and Integration Tests for Round 8 PCG Generator and Metric Discrimination."""

import sys
from pathlib import Path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import pytest
from cut_the_cake.model import PlayerModel
from cut_the_cake.contracts import AngularSectorDiscretization
from cut_the_cake.pcg_modules import build_authored_module_library, AuthoredModule
from cut_the_cake.generator import (
    ModuleAssembly,
    audit_module_assembly,
    run_corpus_discrimination_sweep,
    run_constrained_map_elites,
    extract_counterexample_galleries
)


def test_authored_module_library_construction_and_diversity():
    """Verify that the 16-module library contains the full spectrum of tactical structures."""
    disc = AngularSectorDiscretization(num_sectors=4)
    library = build_authored_module_library(disc)

    assert len(library) == 16, "Module library must contain exactly 16 authored modules."

    # Check categories
    categories = {m.category for m in library}
    assert "safe_corridor" in categories
    assert "quiescent" in categories
    assert "pie_slice" in categories
    assert "staggered" in categories
    assert "flank_choice" in categories
    assert "sniper_lane" in categories
    assert "adversarial_trap" in categories
    assert "high_concurrency" in categories
    assert "high_concurrency_solvable" in categories

    # Check multi-route branching
    multi_route = [m for m in library if len(m.routes) > 1]
    assert len(multi_route) >= 3, "Library must contain multiple modules with flank route choices."

    # Check quiescent modules
    quiescent = [m for m in library if m.is_quiescent]
    assert len(quiescent) >= 2, "Library must contain quiescent reset pocket modules."


def test_module_assembly_and_audit_evaluations():
    """Verify individual audit behaviors (A, B, C, D) on targeted test assemblies."""
    disc = AngularSectorDiscretization(num_sectors=4)
    player = PlayerModel()
    library_map = {m.module_id: m for m in build_authored_module_library(disc)}

    # 1. Fully safe chain (M01, M02, M03, M04, M01, M02)
    safe_chain = ModuleAssembly([
        library_map["M01_StraightCorridor"],
        library_map["M02_BaffledResetCorridor"],
        library_map["M03_PieSliceLeftSweep"],
        library_map["M04_PieSliceRightSweep"],
        library_map["M01_StraightCorridor"],
        library_map["M02_BaffledResetCorridor"],
    ])
    audit_safe = audit_module_assembly(safe_chain, disc, player, entry_sector=0)
    assert audit_safe.audit_a_topology is True
    assert audit_safe.audit_b_kici is True
    assert audit_safe.audit_c_transfer is True
    assert audit_safe.audit_d_local is True
    assert audit_safe.transfer_duration_s < float('inf')

    # 2. Adversarial Trap Chain (Contains M10_AlternatingZigzagTrap where K_ICI <= 1, but Transfer fails)
    trap_chain = ModuleAssembly([
        library_map["M01_StraightCorridor"],
        library_map["M10_AlternatingZigzagTrap"],
        library_map["M01_StraightCorridor"],
        library_map["M01_StraightCorridor"],
        library_map["M01_StraightCorridor"],
        library_map["M01_StraightCorridor"],
    ])
    audit_trap = audit_module_assembly(trap_chain, disc, player, entry_sector=0)
    assert audit_trap.audit_a_topology is True
    assert audit_trap.audit_b_kici is True  # K_ICI <= 2 passes!
    assert audit_trap.audit_c_transfer is False  # Transfer FAILS (Lethal aim latency)!
    assert audit_trap.audit_d_local is False

    # 3. High-Concurrency Solvable Chain (Contains M13 where K_ICI = 3, but Transfer succeeds)
    concurrency_chain = ModuleAssembly([
        library_map["M01_StraightCorridor"],
        library_map["M13_HighConcurrencySolvable"],
        library_map["M01_StraightCorridor"],
        library_map["M01_StraightCorridor"],
        library_map["M01_StraightCorridor"],
        library_map["M01_StraightCorridor"],
    ])
    audit_conc = audit_module_assembly(concurrency_chain, disc, player, entry_sector=0)
    assert audit_conc.audit_a_topology is True
    assert audit_conc.audit_b_kici is False  # K_ICI = 3 fails heuristic!
    assert audit_conc.audit_c_transfer is True  # Transfer PASSES (Deadlines staggered)!
    assert audit_conc.audit_d_local is True


def test_round8a_condition_blind_corpus_sweep_smoke():
    """Fast regression test verifying corpus sweep data structures on small sample."""
    report, results = run_corpus_discrimination_sweep(
        chain_length=6,
        n_samples=30,
        seed=123,
        oracle_subsample=5
    )
    assert report.total_samples == 30
    assert report.pass_a_count == 30


@pytest.mark.scientific
@pytest.mark.slow
def test_round8a_condition_blind_corpus_sweep_discrimination():
    """Verify that a condition-blind sweep produces statistically significant metric separation."""
    report, results = run_corpus_discrimination_sweep(
        chain_length=6,
        n_samples=1000,
        seed=123,
        oracle_subsample=20
    )

    assert report.total_samples == 1000
    assert report.pass_a_count == 1000  # Topology is valid for all combinations
    assert report.pass_b_count > 0
    assert report.pass_c_count > 0

    # Key Scientific Assertions:
    # 1. K_ICI False Positives exist (A and B and not C)
    assert report.count_a_and_b_and_not_c > 0, (
        "Discrimination sweep must identify layouts accepted by K_ICI <= 2 but rejected by Transfer!"
    )

    # 2. K_ICI False Alarms exist (A and not B and C)
    assert report.count_a_and_not_b_and_c > 0, (
        "Discrimination sweep must identify solvable layouts rejected by K_ICI > 2!"
    )

    # 3. Continuous Oracle confirmed
    assert report.sampled_oracle_count > 0
    assert report.sampled_oracle_genuine_pathology > 0


def test_round8b_constrained_map_elites_smoke():
    """Fast regression test verifying MAP-Elites execution structures on small budget."""
    disc = AngularSectorDiscretization(num_sectors=4)
    library = build_authored_module_library(disc)

    archive_c = run_constrained_map_elites(
        condition_name="Condition_C_Transfer",
        module_library=library,
        chain_length=6,
        budget=25,
        seed=42
    )
    assert archive_c.total_evaluations >= 25
    assert archive_c.occupied_cells > 0


@pytest.mark.scientific
@pytest.mark.slow
def test_round8b_constrained_map_elites_search():
    """Verify that Constrained MAP-Elites searches the 2D Pace x Redundancy behavioral archive."""
    disc = AngularSectorDiscretization(num_sectors=4)
    library = build_authored_module_library(disc)

    # Run Condition C (Transfer Certified)
    archive_c = run_constrained_map_elites(
        condition_name="Condition_C_Transfer",
        module_library=library,
        chain_length=6,
        budget=300,
        seed=42
    )

    assert archive_c.total_evaluations == 300
    assert archive_c.accepted_evaluations > 0
    assert archive_c.occupied_cells > 0
    assert archive_c.coverage_pct > 0.0

    # Verify all admitted elites in archive satisfy the Transfer constraint
    for (p_idx, r_idx), elite in archive_c.grid.items():
        assert elite.audit_a_topology is True
        assert elite.audit_c_transfer is True


def test_counterexample_gallery_extraction():
    """Verify that critical counterexample galleries are successfully extracted from corpus results."""
    report, results = run_corpus_discrimination_sweep(
        chain_length=6,
        n_samples=50,
        seed=999,
        oracle_subsample=5
    )

    galleries = extract_counterexample_galleries(results)
    assert "All_Pass_Direct" in galleries or "All_Pass_Flank" in galleries
