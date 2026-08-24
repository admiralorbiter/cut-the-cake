"""Tests for Round 9: Robustness, Generalization & Industrial Simplification."""

import pytest
import numpy as np

import sys
from pathlib import Path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from cut_the_cake.model import PlayerModel
from cut_the_cake.contracts import AngularSectorDiscretization
from cut_the_cake.pcg_modules import (
    build_authored_module_library,
    build_precertified_library,
    build_heldout_module_library,
    audit_library_continuous_oracle
)
from cut_the_cake.generator import (
    ModuleAssembly,
    audit_module_assembly,
    audit_precertified_assembly,
    run_corpus_discrimination_sweep,
    run_kici_threshold_sweep,
    run_constrained_map_elites,
    run_replicated_map_elites,
    compute_paired_differences,
    run_combat_regime_sweep
)


def test_adversarial_basis_continuous_oracle_smoke():
    """Fast regression test auditing adversarial basis modules (M01, M08, M10, M11) against continuous oracle."""
    disc_k8 = AngularSectorDiscretization(num_sectors=8)
    player = PlayerModel()
    library_k8 = build_authored_module_library(disc_k8)
    basis_mods = [m for m in library_k8 if m.module_id in ("M01_StraightCorridor", "M08_LongSniperAlley", "M10_AlternatingZigzagTrap", "M11_RapidCrossfireAperture")]
    report = audit_library_continuous_oracle(basis_mods, player, disc_k8)

    assert len(report) == 4
    # M01 and M08 must be feasible at K=8 with 0 false rejections
    assert report["M01_StraightCorridor"]["discrete_feasible"]
    assert report["M08_LongSniperAlley"]["discrete_feasible"]
    assert not report["M08_LongSniperAlley"]["false_rejection"]
    # M10 and M11 must be infeasible traps
    assert not report["M10_AlternatingZigzagTrap"]["discrete_feasible"]
    assert not report["M11_RapidCrossfireAperture"]["discrete_feasible"]


@pytest.mark.scientific
@pytest.mark.slow
def test_exhaustive_module_library_continuous_oracle_audit():
    """Exhaustively audit all 16 modules in Library 1 against Discrete (K=4) and Continuous (K=inf)."""
    disc = AngularSectorDiscretization(num_sectors=4)
    player = PlayerModel()
    library = build_authored_module_library(disc)

    # 1. Under Reveal-Gated regime: K=4 produces 12 feasible modules (M08 has sector gap at K=4)
    report = audit_library_continuous_oracle(library, player, disc)
    assert len(report) == 16
    assert not report["M08_LongSniperAlley"]["unsound_acceptance"]
    assert report["M08_LongSniperAlley"]["false_rejection"] # Known sector gap at coarse K=4

    # 2. Under K=8: Sector refinement completely eliminates the M08 sector gap (0 false rejections)
    disc_k8 = AngularSectorDiscretization(num_sectors=8)
    library_k8 = build_authored_module_library(disc_k8)
    report_k8 = audit_library_continuous_oracle(library_k8, player, disc_k8)
    for mod_id, data in report_k8.items():
        assert not data["false_rejection"], f"Module {mod_id} unexpectedly had false rejection at K=8!"
        assert not data["unsound_acceptance"], f"Module {mod_id} had unsound acceptance at K=8!"

    # Verify analytical composition: exactly 3 genuine geometric traps (M10, M11, M12) across all oracles
    infeasible_mods = [mod_id for mod_id, d in report_k8.items() if not d["discrete_feasible"]]
    assert len(infeasible_mods) == 3
    assert "M10_AlternatingZigzagTrap" in infeasible_mods
    assert "M11_RapidCrossfireAperture" in infeasible_mods
    assert "M12_TripleSimultaneousCrossfire" in infeasible_mods


def test_kici_integer_threshold_sweep_smoke():
    """Fast regression test verifying K_ICI threshold sweep structures on small sample."""
    disc = AngularSectorDiscretization(num_sectors=4)
    library = build_authored_module_library(disc)

    report, results = run_corpus_discrimination_sweep(
        module_library=library,
        chain_length=6,
        n_samples=30,
        seed=42,
        oracle_subsample=5
    )
    sweep_rows = run_kici_threshold_sweep(results, k_thresholds=[1, 2, 3])
    assert len(sweep_rows) == 3


@pytest.mark.scientific
@pytest.mark.slow
def test_kici_integer_threshold_sweep_roc():
    """Run K_ICI threshold sweep over candidate assemblies to verify bidirectional errors across all K."""
    disc = AngularSectorDiscretization(num_sectors=4)
    library = build_authored_module_library(disc)

    report, results = run_corpus_discrimination_sweep(
        module_library=library,
        chain_length=6,
        n_samples=1000,
        seed=42,
        oracle_subsample=20
    )

    sweep_rows = run_kici_threshold_sweep(results, k_thresholds=[1, 2, 3, 4, 5])
    assert len(sweep_rows) == 5

    # At K=1: strict filter has low recall / high FN
    row_k1 = sweep_rows[0]
    assert row_k1.k_threshold == 1
    assert row_k1.false_negatives > 0

    # At K=2: baseline
    row_k2 = sweep_rows[1]
    assert row_k2.k_threshold == 2
    assert row_k2.false_positives > 0
    assert row_k2.false_negatives > 0

    # At K=4: permissive filter has low precision / high FP
    row_k4 = sweep_rows[3]
    assert row_k4.k_threshold == 4
    assert row_k4.false_positives > 0

    # Confirm that NO static threshold achieves 0 FP and 0 FN simultaneously
    for r in sweep_rows:
        assert (r.false_positives > 0 or r.false_negatives > 0)


def test_condition_e_precertified_library_smoke():
    """Fast regression test verifying precertified library construction and assembly."""
    disc = AngularSectorDiscretization(num_sectors=4)
    player = PlayerModel()
    raw_lib = build_authored_module_library(disc)
    precert_lib = build_precertified_library(raw_lib, disc, player)
    assert len(precert_lib) == 12

    report, results = run_corpus_discrimination_sweep(
        module_library=precert_lib,
        chain_length=6,
        n_samples=30,
        seed=123
    )
    assert report.pass_c_count == 30
    assert report.pass_d_count == 30


@pytest.mark.scientific
@pytest.mark.slow
def test_condition_e_precertified_library_local_equivalence():
    """Verify that compile-time precertification produces 100% tactically feasible level assemblies."""
    disc = AngularSectorDiscretization(num_sectors=4)
    player = PlayerModel()
    raw_lib = build_authored_module_library(disc)
    precert_lib = build_precertified_library(raw_lib, disc, player)

    # Under K=4 reveal-gated, 12 modules are precertified
    assert len(precert_lib) == 12

    # Generate 500 random chains strictly from precertified library
    report, results = run_corpus_discrimination_sweep(
        module_library=precert_lib,
        chain_length=6,
        n_samples=500,
        seed=123
    )

    # All assemblies must pass Audit C (composed transfer) and Audit D (local transfer)
    assert report.pass_c_count == 500
    assert report.pass_d_count == 500
    assert report.count_a_and_b_and_not_c == 0
    assert report.count_c_and_d_match == 500


def test_replicated_map_elites_smoke():
    """Fast regression test verifying MAP-Elites execution structures."""
    disc = AngularSectorDiscretization(num_sectors=4)
    library = build_authored_module_library(disc)

    summaries = run_replicated_map_elites(
        conditions=["Condition_A_Topology"],
        module_library=library,
        chain_length=6,
        budget=25,
        n_seeds=1,
        seed_start=100
    )
    assert "Condition_A_Topology" in summaries
    assert summaries["Condition_A_Topology"].mean_coverage_pct > 0.0


@pytest.mark.scientific
@pytest.mark.slow
def test_replicated_map_elites_multi_seed_qd_scores():
    """Run small-budget replicated MAP-Elites across paired seeds to verify QD metrics and trajectories."""
    disc = AngularSectorDiscretization(num_sectors=4)
    library = build_authored_module_library(disc)

    summaries = run_replicated_map_elites(
        conditions=["Condition_A_Topology", "Condition_C_Transfer", "Condition_E_Precertified"],
        module_library=library,
        chain_length=6,
        budget=500,
        n_seeds=3,
        seed_start=100
    )

    assert "Condition_A_Topology" in summaries
    assert "Condition_C_Transfer" in summaries
    assert "Condition_E_Precertified" in summaries

    for cond, s in summaries.items():
        assert s.n_seeds == 3
        assert s.mean_coverage_pct > 0.0
        assert s.mean_qd_score > 0.0
        assert len(s.ci95_coverage_pct) == 2
        assert len(s.ci95_qd_score) == 2
        assert len(s.seed_coverages) == 3

    # Test paired seed difference calculation
    paired_ca = compute_paired_differences(summaries["Condition_C_Transfer"], summaries["Condition_A_Topology"])
    assert paired_ca.comp_name == "Condition_C_Transfer - Condition_A_Topology"
    assert isinstance(paired_ca.p_non_inferior_2pct, (bool, np.bool_))


def test_heldout_second_library_smoke():
    """Fast regression test verifying held-out library construction."""
    disc = AngularSectorDiscretization(num_sectors=4)
    heldout_lib = build_heldout_module_library(disc)
    assert len(heldout_lib) == 16


@pytest.mark.scientific
@pytest.mark.slow
def test_heldout_second_library_generalization_sweep():
    """Verify that bidirectional K_ICI discrimination failure persists on held-out Library 2."""
    disc = AngularSectorDiscretization(num_sectors=4)
    heldout_lib = build_heldout_module_library(disc)
    assert len(heldout_lib) == 16

    report, results = run_corpus_discrimination_sweep(
        module_library=heldout_lib,
        chain_length=6,
        n_samples=1000,
        seed=777,
        oracle_subsample=20
    )

    # Confirm that both failure modes persist on the newly authored geometry!
    assert report.count_a_and_b_and_not_c > 0, "Held-out library should exhibit KICI false positives!"
    assert report.count_a_and_not_b_and_c > 0, "Held-out library should exhibit KICI false alarms!"
    assert report.count_c_and_d_match == 1000, "C == D should hold on held-out library under quiescent reset!"


def test_combat_parameter_regime_smoke():
    """Fast regression test verifying combat regime evaluation."""
    disc = AngularSectorDiscretization(num_sectors=4)
    library = build_authored_module_library(disc)

    regime_rows = run_combat_regime_sweep(
        module_library=library,
        chain_length=6,
        n_samples=30,
        seed=999
    )
    assert len(regime_rows) == 3


@pytest.mark.scientific
@pytest.mark.slow
def test_combat_parameter_regime_sweep():
    """Verify that metric discrimination remains robust and yields distinct pass rates across combat regimes."""
    disc = AngularSectorDiscretization(num_sectors=4)
    library = build_authored_module_library(disc)

    regime_rows = run_combat_regime_sweep(
        module_library=library,
        chain_length=6,
        n_samples=1000,
        seed=999
    )

    assert len(regime_rows) == 3
    # Check that in all regimes, both KICI blind spots and false alarms are non-zero
    for row in regime_rows:
        assert row.pass_b_rate_pct > 0.0
        assert row.pass_c_rate_pct > 0.0
        assert row.kici_blind_spot_rate_pct > 0.0
        assert row.kici_false_alarm_rate_pct > 0.0

    # Verify that different regimes produce distinct pass rates (Slow > Medium > Fast)
    slow_row, med_row, fast_row = regime_rows[0], regime_rows[1], regime_rows[2]
    assert slow_row.pass_c_rate_pct >= med_row.pass_c_rate_pct >= fast_row.pass_c_rate_pct
    assert slow_row.pass_c_rate_pct > fast_row.pass_c_rate_pct, "Slow and Fast regimes must produce distinct pass rates!"
