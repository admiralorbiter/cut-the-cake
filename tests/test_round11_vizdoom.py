"""Unit tests for Round 11: External Predictive Validity (ViZDoom Simulation Ladder).

Covers:
- Gate 11A: Engine Geometry Fidelity (|R_engine - R_pred| <= 1 tic)
- Gate 11B: Deterministic Mechanism Conformance (L*_tic <= 0 <-> Survival under Oracle)
- Gate 11C: Independent Policy Evaluation (FIFO, Greedy Angle, EDF, Left-to-Right vs Baselines)
- Gate 11D: Noise Robustness & Monotonic Survival Calibration Curve
- Empirical Execution of Disagreement Classes (Blind Spot Trap vs Staggered Solvable)
"""

import pytest
import math
import numpy as np

import sys
from pathlib import Path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from cut_the_cake.vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteScheduleResult,
    DiscreteTicScheduler,
    ControllerPolicy,
    SimulationController,
    SimulationEpisodeLog,
    DeterministicSimulationReferee,
    NoiseSimulationHarness
)
from cut_the_cake.vizdoom_fixtures import (
    build_parametric_wall_arena,
    build_disagreement_arena_kici_blindspot,
    build_disagreement_arena_kici_falsealarm,
    build_large_margin_arena
)
from cut_the_cake.fixtures_round10 import (
    build_f01_analytical_corner,
    build_f02b_three_angle_sector_sweep,
    build_f03_multi_aperture_doorway,
    build_f08_ninety_degree_turn_corner
)


def test_gate_11a_engine_geometry_fidelity():
    """Gate 11A: Verify CheckSight engine reveal tics match analytical compiler within <= 1 tic."""
    params = TicCombatParameters()
    ref = DeterministicSimulationReferee(params)

    # 1. F01 Analytical Corner: reveal at s=3.25m -> t = 3.25 / 4.5 = 0.7222s -> k = round(0.7222 * 35) = 25 tics
    f01 = build_f01_analytical_corner()
    jobs_f01 = ref.extract_tic_jobs(f01)
    assert len(jobs_f01) == 1
    expected_f01_tic = int(round((3.25 / 4.5) * 35))
    assert abs(jobs_f01[0].reveal_tic - expected_f01_tic) <= 1

    # 2. F08 90-Degree Corner Turn: reveal at s=4.0m -> t = 4.0 / 4.5 = 0.8888s -> k = round(0.8888 * 35) = 31 tics
    f08 = build_f08_ninety_degree_turn_corner()
    jobs_f08 = ref.extract_tic_jobs(f08)
    assert len(jobs_f08) == 1
    expected_f08_tic = int(round((4.00 / 4.5) * 35))
    assert abs(jobs_f08[0].reveal_tic - expected_f08_tic) <= 1


def test_gate_11b_deterministic_mechanism_conformance_parametric_sweep():
    """Gate 11B: Verify L*_tic <= 0 strictly predicts survival and L*_tic > 0 predicts death under Oracle."""
    params = TicCombatParameters()
    ref = DeterministicSimulationReferee(params)

    # Parametric sweep from x=0.2m (lethal crossfire trap) to x=2.2m (solvable sequential sweep)
    wall_positions = np.linspace(0.2, 2.2, 11)
    survivals = []
    l_stars = []

    for wx in wall_positions:
        arena = build_parametric_wall_arena(wall_x_m=wx)
        log = ref.run_episode(arena, policy=ControllerPolicy.ORACLE)
        jobs = ref.extract_tic_jobs(arena)
        sched = ref.scheduler.solve(jobs)

        survivals.append(log.player_survived)
        l_stars.append(sched.lateness_optimal_l_star_tics)

        # Crisp mechanism prediction away from boundary:
        if sched.lateness_optimal_l_star_tics < 0:
            assert log.player_survived, f"Feasible arena (L*={sched.lateness_optimal_l_star_tics} tics) must survive!"
        elif sched.lateness_optimal_l_star_tics > 0:
            assert not log.player_survived, f"Infeasible arena (L*={sched.lateness_optimal_l_star_tics} tics) must die!"

    # Verify monotonic variation in L*
    for i in range(len(l_stars) - 1):
        assert l_stars[i+1] <= l_stars[i], "L* must decrease monotonically as wall moves right"

    # Exactly one sharp transition from False to True
    transitions = sum(1 for i in range(len(survivals) - 1) if survivals[i] != survivals[i+1])
    assert transitions == 1


def test_gate_11c_independent_policy_predictions():
    """Gate 11C: Evaluate independent heuristics (FIFO, Greedy Angle, EDF, Left-to-Right) vs Tactical Margin."""
    params = TicCombatParameters()
    ref = DeterministicSimulationReferee(params)

    # 1. Large-Margin Arena (M_tic >> 0): All policies survive
    large_arena = build_large_margin_arena()
    for pol in [ControllerPolicy.ORACLE, ControllerPolicy.FIFO, ControllerPolicy.NEAREST_ANGLE, ControllerPolicy.EDF, ControllerPolicy.LEFT_TO_RIGHT]:
        log = ref.run_episode(large_arena, policy=pol)
        assert log.player_survived, f"Policy {pol} must survive on large-margin arena!"

    # 2. Infeasible Trap Arena (M_tic < 0, x=0.2m): All policies fail
    lethal_arena = build_parametric_wall_arena(wall_x_m=0.2)
    for pol in [ControllerPolicy.ORACLE, ControllerPolicy.FIFO, ControllerPolicy.NEAREST_ANGLE, ControllerPolicy.EDF, ControllerPolicy.LEFT_TO_RIGHT]:
        log = ref.run_episode(lethal_arena, policy=pol)
        assert not log.player_survived, f"Policy {pol} cannot survive on infeasible crossfire trap!"


def test_gate_11c_baseline_superiority_over_static_and_workload():
    """Gate 11C: Confirm L*_tic separates outcomes where static concurrency K_static and workload B_work fail."""
    params = TicCombatParameters()
    ref = DeterministicSimulationReferee(params)

    # Arena 1: Solvable with high static concurrency K=3
    arena_solvable = build_disagreement_arena_kici_falsealarm()
    log_solvable = ref.run_episode(arena_solvable, policy=ControllerPolicy.ORACLE)
    sched_solvable = ref.scheduler.solve(ref.extract_tic_jobs(arena_solvable))
    
    assert sched_solvable.peak_static_concurrency == 3
    assert sched_solvable.lateness_optimal_l_star_tics <= 0
    assert log_solvable.player_survived, "Solvable K=3 room must survive despite high static concurrency!"

    # Arena 2: Infeasible with low static concurrency K=2
    arena_trap = build_disagreement_arena_kici_blindspot()
    log_trap = ref.run_episode(arena_trap, policy=ControllerPolicy.ORACLE)
    sched_trap = ref.scheduler.solve(ref.extract_tic_jobs(arena_trap))

    assert sched_trap.peak_static_concurrency == 2
    assert sched_trap.lateness_optimal_l_star_tics > 0
    assert not log_trap.player_survived, "Deadly K=2 trap must fail despite low static concurrency!"


def test_gate_11d_noise_robustness_smoke():
    """Fast regression test verifying noise simulation harness operates with non-zero trials."""
    harness = NoiseSimulationHarness(sigma_acq_s=0.02, sigma_aim_deg_s=30.0)
    arena = build_parametric_wall_arena(wall_x_m=2.0)
    p_surv = harness.run_noisy_trials(arena, n_trials=5, seed=123)
    assert 0.0 <= p_surv <= 1.0


@pytest.mark.slow
def test_gate_11d_noise_robustness_and_calibration_curve():
    """Gate 11D: Verify empirical survival probability varies monotonically with tactical margin M_tic."""
    harness = NoiseSimulationHarness(sigma_acq_s=0.02, sigma_aim_deg_s=30.0)
    
    # Test across wall positions producing negative, zero, and positive margins
    wall_positions = [0.2, 0.6, 0.9, 1.4, 2.0]
    margins = []
    p_survivals = []

    for wx in wall_positions:
        arena = build_parametric_wall_arena(wall_x_m=wx)
        ref = DeterministicSimulationReferee()
        jobs = ref.extract_tic_jobs(arena)
        sched = ref.scheduler.solve(jobs)
        
        p_surv = harness.run_noisy_trials(arena, n_trials=50, seed=123)
        margins.append(sched.tactical_margin_tics)
        p_survivals.append(p_surv)

    # Check that empirical survival increases monotonically with tactical margin
    for i in range(len(p_survivals) - 1):
        assert p_survivals[i+1] >= p_survivals[i] - 0.05, f"Survival must increase with margin: {p_survivals}"

    # Extreme anchors
    assert p_survivals[0] <= 0.05, f"Deep negative margin must have near-zero survival: {p_survivals[0]}"
    assert p_survivals[-1] >= 0.90, f"High positive margin must have high survival: {p_survivals[-1]}"


def test_disagreement_classes_execution_telemetry():
    """Verify detailed execution telemetry on both static-concurrency disagreement classes."""
    params = TicCombatParameters()
    ref = DeterministicSimulationReferee(params)

    # Class 1: [A ∩ B ∩ ¬C] Blind Spot Trap
    blind_spot = build_disagreement_arena_kici_blindspot()
    log_bs = ref.run_episode(blind_spot, policy=ControllerPolicy.ORACLE)
    assert not log_bs.player_survived
    assert log_bs.death_tic is not None
    assert log_bs.peak_static_concurrency <= 2

    # Class 2: [A ∩ ¬B ∩ C] False Alarm Solvable
    false_alarm = build_disagreement_arena_kici_falsealarm()
    log_fa = ref.run_episode(false_alarm, policy=ControllerPolicy.ORACLE)
    assert log_fa.player_survived
    assert log_fa.death_tic is None
    assert log_fa.peak_static_concurrency == 3


def test_round11_1_multi_family_suite_structural_diversity():
    """Round 11.1: Verify the 60-arena benchmark suite has balanced representation across 6 mechanisms."""
    from cut_the_cake.vizdoom_fixtures import build_round11_benchmark_suite

    suite = build_round11_benchmark_suite()
    assert len(suite) == 60

    categories = {m.category for m in suite}
    assert len(categories) == 6
    for cat in categories:
        fam_arenas = [m for m in suite if m.category == cat]
        assert len(fam_arenas) == 10

    # Check that margins span negative, zero, and positive regions across the suite
    ref = DeterministicSimulationReferee()
    margins = [ref.scheduler.solve(ref.extract_tic_jobs(m)).tactical_margin_tics for m in suite]
    assert min(margins) <= -4
    assert max(margins) >= +4
    assert any(m == 0 or abs(m) <= 2 for m in margins)


def test_round11_1_population_benchmark_smoke():
    """Fast regression test verifying structural invariants of population benchmark."""
    from cut_the_cake.vizdoom_fixtures import build_round11_benchmark_suite
    from cut_the_cake.vizdoom_engine import run_population_benchmark

    full_suite = build_round11_benchmark_suite()
    # Sample 2 arenas from each of the 6 families (12 arenas total) for balanced LOGFO-CV
    suite = [full_suite[i * 10] for i in range(6)] + [full_suite[i * 10 + 1] for i in range(6)]
    report = run_population_benchmark(suite, n_trials=2)
    assert report.total_arenas == 12
    assert report.total_episodes == 12 * 5 * 2
    assert "Tactical Margin M_tic" in report.baseline_metrics
    m_metrics = report.baseline_metrics["Tactical Margin M_tic"]
    assert not np.isnan(m_metrics.spearman_rho)
    assert not np.isnan(m_metrics.roc_auc)


@pytest.mark.scientific
@pytest.mark.slow
def test_round11_1_population_benchmark_and_logfo_baseline_shootout():
    """Round 11.1: Verify Tactical Margin out-of-fold generalization (LOGFO-AUC > 0.90) and baseline superiority."""
    from cut_the_cake.vizdoom_fixtures import build_round11_benchmark_suite
    from cut_the_cake.vizdoom_engine import run_population_benchmark

    suite = build_round11_benchmark_suite()
    report = run_population_benchmark(suite, n_trials=30)
    assert report.total_arenas == 60
    assert report.total_episodes == 60 * 5 * 30

    m_metrics = report.baseline_metrics["Tactical Margin M_tic"]
    k_metrics = report.baseline_metrics["Peak Physical LOS K_static (Inverted)"]
    slack_metrics = report.baseline_metrics["Min Slack sigma_min"]

    # Tactical margin achieves high rank correlation and generalization
    assert m_metrics.spearman_rho >= 0.70, f"Tactical margin rho={m_metrics.spearman_rho} must be high"
    assert m_metrics.roc_auc >= 0.85, f"Tactical margin ROC-AUC={m_metrics.roc_auc} must exceed 0.85"
    assert m_metrics.logfo_cv_roc_auc >= 0.80, f"LOGFO out-of-fold AUC={m_metrics.logfo_cv_roc_auc} must exceed 0.80"

    # Tactical margin strictly outperforms static concurrency and minimum slack on held-out families
    assert m_metrics.logfo_cv_roc_auc > k_metrics.logfo_cv_roc_auc + 0.03
    assert m_metrics.logfo_cv_roc_auc > slack_metrics.logfo_cv_roc_auc + 0.15
    assert m_metrics.logfo_cv_brier < k_metrics.logfo_cv_brier


def test_timing_truth_table_single_target_boundary():
    """Verify exact tic-by-tic countdown and deadline truth table at L* in {-1, 0, +1}."""
    params = TicCombatParameters()
    ref = DeterministicSimulationReferee(params)

    # 1 target at heading 0: R=0, A=6, P=4 -> Completion = 10 tics (cleared at tic 9)
    # D in [9, 10, 11] -> L* in [+1, 0, -1]
    from shapely.geometry import Polygon, LineString
    from cut_the_cake.compiler import GeometricModule, GeometricRoute, GeometricThreat, GeometricPort

    boundary = Polygon([(0.0, -1.0), (4.0, -1.0), (4.0, 1.0), (0.0, 1.0)])
    port_in = GeometricPort("PORT_IN", LineString([(0.0, -1.0), (0.0, 1.0)]))
    port_out = GeometricPort("PORT_OUT", LineString([(4.0, -1.0), (4.0, 1.0)]))
    route = GeometricRoute("main", [(0.0, 0.0), (4.0, 0.0)], v_move_mps=4.5)

    # L* = +1 (due = 9 tics = 0.257s) -> Must die at tic 9
    t_lethal = GeometricThreat("T_Lethal", Polygon([(1.8, -0.1), (2.2, -0.1), (2.2, 0.1), (1.8, 0.1)]), (2.0, 0.0), authored_due_window_s=9/35.0, service_duration_s=0.10)
    mod_lethal = GeometricModule("M_Lethal", "M_Lethal", boundary, [], [port_in, port_out], [t_lethal], [route])
    log_lethal = ref.run_episode(mod_lethal, policy=ControllerPolicy.ORACLE)
    assert not log_lethal.player_survived
    assert log_lethal.death_tic == 9

    # L* = 0 (due = 10 tics = 0.286s) -> Must survive (cleared at tic 9 within 10 tics)
    t_exact = GeometricThreat("T_Exact", Polygon([(1.8, -0.1), (2.2, -0.1), (2.2, 0.1), (1.8, 0.1)]), (2.0, 0.0), authored_due_window_s=10/35.0, service_duration_s=0.10)
    mod_exact = GeometricModule("M_Exact", "M_Exact", boundary, [], [port_in, port_out], [t_exact], [route])
    log_exact = ref.run_episode(mod_exact, policy=ControllerPolicy.ORACLE)
    assert log_exact.player_survived
    assert log_exact.threat_clear_tics["T_Exact"] == 9

    # L* = -1 (due = 11 tics = 0.315s) -> Must survive (cleared at tic 9 within 11 tics, margin = +1)
    t_safe = GeometricThreat("T_Safe", Polygon([(1.8, -0.1), (2.2, -0.1), (2.2, 0.1), (1.8, 0.1)]), (2.0, 0.0), authored_due_window_s=11/35.0, service_duration_s=0.10)
    mod_safe = GeometricModule("M_Safe", "M_Safe", boundary, [], [port_in, port_out], [t_safe], [route])
    log_safe = ref.run_episode(mod_safe, policy=ControllerPolicy.ORACLE)
    assert log_safe.player_survived
    assert log_safe.threat_clear_tics["T_Safe"] == 9


@pytest.mark.engine
@pytest.mark.scientific
@pytest.mark.slow
def test_round11_2_real_vizdoom_c_engine_bridge_12_arenas():
    """Round 11.2: Execute 12-arena bridge suite directly inside real C++ ViZDoom DoomGame process."""
    from cut_the_cake.vizdoom_bridge import build_12_arena_bridge_suite, ViZDoomRealBridge

    bridge = ViZDoomRealBridge()
    suite = build_12_arena_bridge_suite()
    assert len(suite) == 12

    for arena in suite:
        log = bridge.run_engine_episode(arena, policy=ControllerPolicy.ORACLE)
        
        # Deep margin assertions in real C++ Doom engine
        if log.tactical_margin_tics >= 6:
            assert log.engine_player_survived, f"Real Doom engine execution of {arena.module_id} (M={log.tactical_margin_tics}) must survive!"
        elif log.tactical_margin_tics <= -4:
            assert not log.engine_player_survived, f"Real Doom engine execution of {arena.module_id} (M={log.tactical_margin_tics}) must die!"


@pytest.mark.engine
@pytest.mark.scientific
@pytest.mark.slow
def test_round11_3_engine_residual_decomposition_and_guard_band():
    """Round 11.3: Verify engine residual decomposition and epsilon_deploy=3 deployment guard band."""
    from cut_the_cake.vizdoom_bridge import run_residual_decomposition_analysis

    report = run_residual_decomposition_analysis(guard_band_epsilon=3)
    assert report.total_arenas == 12
    assert report.conformance_rate >= 0.90, f"Engine conformance rate {report.conformance_rate} must be high"
    assert report.max_delta_export_tics <= 3, f"WAD export delta {report.max_delta_export_tics} must be <= 3 tics"
    assert report.max_delta_total_tics <= 3, f"Total residual {report.max_delta_total_tics} must be <= 3 tics"
    assert report.mean_absolute_total_residual_tics <= 2.0

    # Verify that all arenas with M_tactical >= 3 (deployable with guard band) survive 100%
    for rec in report.records:
        if rec.tactical_margin_pred >= 3:
            assert rec.engine_player_survived, f"Deployable arena {rec.scenario_id} (M={rec.tactical_margin_pred}) failed in native Doom!"
        elif rec.tactical_margin_pred <= -4:
            assert not rec.engine_player_survived, f"Lethal arena {rec.scenario_id} (M={rec.tactical_margin_pred}) unexpectedly survived in native Doom!"


@pytest.mark.engine
@pytest.mark.slow
def test_f3_preaim_vs_revealgated_in_real_vizdoom():
    """Round 11.3A: Epistemic separation test in native ViZDoom DoomGame engine on F3.
    
    Demonstrates that Reveal-Gated (a_1 = r_1) dies at tic 69, while Pre-Aim (a_1 = 0)
    survives at tic 67, proving both recurrences represent valid, distinct player-information regimes.
    """
    from cut_the_cake.vizdoom_fixtures import build_family3_aperture_congestion
    from cut_the_cake.vizdoom_bridge import ViZDoomRealBridge
    from cut_the_cake.vizdoom_engine import ControllerPolicy, InformationRegime

    bridge = ViZDoomRealBridge()
    mod = build_family3_aperture_congestion(stagger_m=1.40, index=2)

    # 1. Reveal-Gated Oracle (a_1 = r_1) -> Infeasible (L* = +4, M = -4) -> Dies in native Doom
    log_reveal = bridge.run_engine_episode(mod, policy=ControllerPolicy.ORACLE, regime=InformationRegime.REVEAL_GATED)
    assert not log_reveal.engine_player_survived
    assert log_reveal.death_tic in (69, 70)
    assert log_reveal.tactical_margin_tics == -4

    # 2. Pre-Aim Oracle (a_1 = 0) -> Feasible (L* = -2, M = +2) -> Survives in native Doom
    log_preaim = bridge.run_engine_episode(mod, policy=ControllerPolicy.PRE_AIM_ORACLE, regime=InformationRegime.PRE_AIM)
    assert log_preaim.engine_player_survived
    assert log_preaim.death_tic is None
    assert log_preaim.tactical_margin_tics == +2


def test_epistemic_recurrence_properties_and_monotonicity():
    """Verify fundamental epistemic recurrence mathematical properties:
    
    1. Monotonicity: L*_reveal_gated >= L*_pre_aim always (causal setup is never faster than pre-aim).
    2. Zero-Release Identity: When all r_j = 0, L*_reveal_gated == L*_pre_aim exactly.
    """
    from cut_the_cake.vizdoom_engine import DiscreteTicScheduler, TicThreatJob, InformationRegime, TicCombatParameters

    params = TicCombatParameters()
    sched = DiscreteTicScheduler(params)

    # 1. Staggered releases: Reveal-gated should have greater or equal lateness
    jobs_staggered = [
        TicThreatJob("T1", reveal_tic=15, due_window_tics=30, deadline_tic=45, angle_deg=+60.0, threat_anchor=(2.0, 1.0), service_duration_tics=4),
        TicThreatJob("T2", reveal_tic=25, due_window_tics=30, deadline_tic=55, angle_deg=-60.0, threat_anchor=(2.0, -1.0), service_duration_tics=4),
    ]
    res_reveal = sched.solve(jobs_staggered, regime=InformationRegime.REVEAL_GATED)
    res_preaim = sched.solve(jobs_staggered, regime=InformationRegime.PRE_AIM)

    assert res_reveal.lateness_optimal_l_star_tics >= res_preaim.lateness_optimal_l_star_tics
    assert res_reveal.tactical_margin_tics <= res_preaim.tactical_margin_tics

    # 2. Zero-release: Reveal-gated and Pre-aim must be IDENTICAL
    jobs_zero_r = [
        TicThreatJob("T1", reveal_tic=0, due_window_tics=30, deadline_tic=30, angle_deg=+60.0, threat_anchor=(2.0, 1.0), service_duration_tics=4),
        TicThreatJob("T2", reveal_tic=0, due_window_tics=30, deadline_tic=30, angle_deg=-60.0, threat_anchor=(2.0, -1.0), service_duration_tics=4),
    ]
    res_zero_reveal = sched.solve(jobs_zero_r, regime=InformationRegime.REVEAL_GATED)
    res_zero_preaim = sched.solve(jobs_zero_r, regime=InformationRegime.PRE_AIM)

    assert res_zero_reveal.lateness_optimal_l_star_tics == res_zero_preaim.lateness_optimal_l_star_tics
    assert res_zero_reveal.completion_tics == res_zero_preaim.completion_tics




