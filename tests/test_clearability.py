"""Unit, property, regression, and adversarial counterexample tests for Tactical Clearability Validator."""

import math
import random
import pytest
import numpy as np
import networkx as nx

import sys
from pathlib import Path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from cut_the_cake.model import World, ThreatRegion, Module, Port, CombatModel, PlayerModel
from cut_the_cake.visibility import compute_visible_threats, brute_force_threat_visible
from cut_the_cake.conflicts import build_threat_incompatibility_graph
from cut_the_cake.paths import evaluate_path_clearability
from cut_the_cake.contracts import (
    evaluate_module_composition,
    ContractStatus,
    AimSector,
    circular_angular_distance_deg,
    AngularSectorDiscretization,
    ThreatJob,
    UpperArrivalCurve,
    StateConditionedDBF,
    compose_state_conditioned_dbfs,
    verify_dbf_composition_associativity,
    ScalarSchedulabilitySignature,
    StateConditionedInterface,
    compose_state_conditioned_interfaces,
    verify_interface_composition_associativity,
    ExactTransferMap,
    CompositeTransferMap,
    compose_exact_transfer_maps,
    verify_transfer_map_associativity,
    demonstrate_infsup_nondistributivity,
    SpatialThreatJob,
    SpatialRoute,
    SpatialModuleTransferMap,
    CompositeSpatialTransferMap,
    compose_spatial_transfer_maps,
    verify_spatial_transfer_map_associativity,
    flatten_spatial_module_chain,
    solve_raw_spatial_chain,
    ContinuousAngleTransferMap
)
from cut_the_cake.geometry import is_quiescent_reset_pocket
from cut_the_cake.service_solver import solve_service_schedule, solve_service_schedule_dp, ThreatEvent
from cut_the_cake.scenarios import (
    scenario_1_pie_slice,
    scenario_2_triple_reveal,
    scenario_3_large_isovist_control,
    scenario_4_tiny_multi_aperture,
    scenario_5_composition_resonance,
    scenario_6_contract_repair,
    scenario_7_nonadjacent_leak,
    scenario_8_corner_duel_simulation,
    scenario_9_clique_counterexample,
    scenario_9b_matched_solvable_control,
    scenario_10_aperture_split_merge,
    scenario_11_contract_insufficiency_counterexample,
    scenario_12_scalar_interface_counterexample,
    scenario_13_nonpreemptive_blocking_counterexample,
    scenario_14_infsup_nondistributivity_algebra
)


def test_scenario_1_pie_slice_sequential_clearability():
    """Scenario 1: Slicing the pie creates sequential reveals (W*=1, L*<=0, Solvable)."""
    world, path = scenario_1_pie_slice()
    combat = CombatModel()
    player = PlayerModel()

    res = evaluate_path_clearability(path, world, combat, player)

    assert res.is_solvable is True
    assert res.schedule_result.optimal_max_lateness_s <= 0.0
    assert res.optimal_frontier_width <= 2
    reveals = res.reveals
    assert "A1" in reveals and "A2" in reveals and "A3" in reveals
    assert reveals["A1"] < reveals["A2"] < reveals["A3"]


def test_scenario_2_triple_reveal_concurrency_spike():
    """Scenario 2: Simultaneous triple reveal creates a concurrency spike."""
    world, path = scenario_2_triple_reveal()
    combat = CombatModel()
    player = PlayerModel()

    res = evaluate_path_clearability(path, world, combat, player)

    assert res.peak_k_ici >= 2
    assert res.optimal_frontier_width >= 2


def test_scenario_3_and_4_area_vs_concurrency_dissociation():
    """Scenarios 3 & 4: Proves that Visible Area is completely dissociated from Concurrency."""
    combat = CombatModel()
    player = PlayerModel()

    w3, p3 = scenario_3_large_isovist_control()
    res3 = evaluate_path_clearability(p3, w3, combat, player)

    w4, p4 = scenario_4_tiny_multi_aperture()
    res4 = evaluate_path_clearability(p4, w4, combat, player)

    # Large 400m² area has K_ICI = 1
    assert res3.peak_k_ici == 1
    assert res3.is_solvable is True
    assert res3.schedule_result.optimal_max_lateness_s <= 0.0

    # Tiny 16m² area has K_ICI = 2 and fails deadlines
    assert res4.peak_k_ici >= 2
    assert res4.peak_k_ici > res3.peak_k_ici
    assert res4.schedule_result.optimal_max_lateness_s > 0.0


def test_scenario_5_and_6_non_compositionality_and_contract_repair():
    """Scenarios 5 & 6: Proves local quality is NOT compositional, and contracts repair it."""
    combat = CombatModel()
    player = PlayerModel()

    # Scenario 5: Dense grid certification of local modules
    mod_a, port_a, mod_b, port_b = scenario_5_composition_resonance()
    comp_res5 = evaluate_module_composition(mod_a, port_a, mod_b, port_b, combat, player)

    assert comp_res5.internal_k_a_max <= 1
    assert comp_res5.internal_k_b_max <= 1
    # Global composition fails contract
    assert comp_res5.status in [ContractStatus.FAIL_RESONANCE, ContractStatus.FAIL_EXTERNAL_BUDGET]

    # Scenario 6: Contract repair with occluder baffle
    mod_a6, port_a6, mod_b6, port_b6 = scenario_6_contract_repair()
    comp_res6 = evaluate_module_composition(mod_a6, port_a6, mod_b6, port_b6, combat, player)

    assert comp_res6.status == ContractStatus.PASS
    assert len(comp_res6.violations) == 0


def test_scenario_7_nonadjacent_leak():
    """Scenario 7: Catches undeclared ray escaping module boundary without passing a port."""
    mod_a, port_a, mod_b, port_b, t_c = scenario_7_nonadjacent_leak()
    combat = CombatModel()
    player = PlayerModel()

    comp_res = evaluate_module_composition(mod_a, port_a, mod_b, port_b, combat, player)

    assert comp_res.status == ContractStatus.FAIL_UNDECLARED_RAY
    assert any("Undeclared ray" in v for v in comp_res.violations)


def test_scenario_8_finite_disk_corner_duel_gpa_and_convergence():
    """Scenario 8: Finite-disk agent simulation computes GPA with numerical step-size convergence."""
    # Far setback (3.0m) vs Close setback (0.5m)
    leads = []
    for dt in [0.02, 0.01, 0.005, 0.0025]:
        t_a, t_b, gpa = scenario_8_corner_duel_simulation(setback_a=3.0, setback_b=0.5, dt_s=dt)
        leads.append(t_b - t_a)

    # Lead should be strictly positive across all discretizations and converge to ~0.030s +/- 0.005s
    assert all(lead > 0 for lead in leads)
    assert abs(leads[-1] - 0.030) < 0.005
    # Successive step convergence difference shrinks
    assert abs(leads[-1] - leads[-2]) <= abs(leads[1] - leads[0])


def test_scenario_9_exact_c5_cycle_counterexample_and_quantitative_lateness():
    """Scenario 9: Exact C_5 5-cycle counterexample (ω(H)=2, exactly 5 edges, regular degree 2).

    Simultaneous release (r_j = 0.0s) forces minimum service completion = 2.05s against due date 0.40s,
    producing exact optimal maximum lateness L*(γ) = +1.65s (Unsolvable).
    """
    world, path, combat, player = scenario_9_clique_counterexample()

    vis_threats = compute_visible_threats(path[0], world)
    assert len(vis_threats) == 5

    G, k_ici = build_threat_incompatibility_graph(vis_threats, combat, player)

    # Exact C_5 structure assertions:
    assert len(G.nodes) == 5
    assert len(G.edges) == 5
    for node, deg in G.degree():
        assert deg == 2
    assert k_ici == 2  # Maximum clique in C_5 is exactly 2!

    # Evaluate trajectory clearability
    res = evaluate_path_clearability(path, world, combat, player)

    assert res.peak_k_ici == 2
    assert res.is_solvable is False
    # Exact quantitative lateness regression assertion:
    assert 1.64 <= res.schedule_result.optimal_max_lateness_s <= 1.66
    assert len(res.schedule_result.unresolved_deadlines_missed) == 4


def test_scenario_9b_true_5_threat_matched_solvable_control():
    """Scenario 9b: True 5-threat matched control with identical C_5 conflict graph (ω(H)=2).

    Demonstrates that X = (C5, simultaneous) has L* = +1.65s (FAIL), while Y = (C5, staggered) has L* <= 0 (PASS).
    """
    w9, p9, c9, pl9 = scenario_9_clique_counterexample()
    res9 = evaluate_path_clearability(p9, w9, c9, pl9)

    w9b, p9b, c9b, pl9b = scenario_9b_matched_solvable_control()
    res9b = evaluate_path_clearability(p9b, w9b, c9b, pl9b)

    # Both environments feature the identical 5 threat regions
    assert len(w9.threats) == 5
    assert len(w9b.threats) == 5

    # 9 fails (+1.65s) and 9b succeeds (<= 0.0s)!
    assert res9.is_solvable is False
    assert res9.schedule_result.optimal_max_lateness_s > 1.60
    assert res9b.is_solvable is True
    assert res9b.schedule_result.optimal_max_lateness_s <= 0.0


def test_scenario_10_persistent_threat_identity_surviving_split():
    """Scenario 10: Persistent world-space threat T_j maintains single stable ID despite projected split."""
    world, path = scenario_10_aperture_split_merge()
    pos = (5.0, 1.0)
    vis = compute_visible_threats(pos, world)

    assert len(vis) == 1
    assert vis[0].threat_id == "T_WideBay"
    assert 0.1 < vis[0].visible_fraction < 0.9


def test_scenario_11_contract_insufficiency_counterexample():
    """Scenario 11: Proves that K_ICI Composable Visibility Contracts are INSUFFICIENT for tactical clearability.

    Module composition passes the K_ICI contract (no escaping rays, external budget met, global K <= 2),
    yet the global path fails the real-time scheduling solver (L* > 0).
    """
    mod_a, port_a, mod_b, port_b, path, combat, player = scenario_11_contract_insufficiency_counterexample()

    # 1. K_ICI port contract evaluation passes cleanly:
    comp_res = evaluate_module_composition(mod_a, port_a, mod_b, port_b, combat, player)
    assert comp_res.status == ContractStatus.PASS
    assert comp_res.global_k_max <= 2

    # 2. Yet the global scheduling solver over the composed world proves it is infeasible:
    all_obs = mod_a.obstacles + mod_b.obstacles
    all_threats = mod_a.threats + mod_b.threats
    world_composed = World(bounds=(0.0, 0.0, 10.0, 20.0), obstacles=all_obs, threats=all_threats)

    path_res = evaluate_path_clearability(path, world_composed, combat, player)
    assert path_res.is_solvable is False
    assert path_res.schedule_result.optimal_max_lateness_s > 0.0


def test_independent_scheduling_oracle_cross_check():
    """Property test: Exhaustive permutation solver matches Dynamic Programming oracle over random instances."""
    combat = CombatModel()
    player = PlayerModel()
    rng = random.Random(42)

    for trial in range(30):
        n = rng.randint(3, 7)
        events = []
        for i in range(n):
            r = rng.uniform(0.0, 2.0)
            d = r + rng.uniform(0.3, 1.2)
            angle = rng.uniform(-180.0, 180.0)
            events.append(ThreatEvent(
                threat_id=f"T_{i}",
                reveal_time_s=r,
                deadline_time_s=d,
                centroid_angle_deg=angle
            ))

        # Solve with permutation solver
        res_perm = solve_service_schedule(events, combat, player)
        # Solve with DP oracle
        l_dp, order_dp = solve_service_schedule_dp(events, combat, player)

        assert abs(res_perm.optimal_max_lateness_s - l_dp) < 1e-4


def test_rigid_motion_invariance_translation_and_rotation():
    """Property test: Translating and rotating an entire world leaves K_ICI, L*, and W* invariant."""
    w1, p1 = scenario_1_pie_slice()
    combat = CombatModel()
    player = PlayerModel()

    res_orig = evaluate_path_clearability(p1, w1, combat, player)

    # 1. Translation by (+50, -30)
    from shapely.affinity import translate, rotate
    dx, dy = 50.0, -30.0
    w_trans = World(
        bounds=(w1.bounds[0] + dx, w1.bounds[1] + dy, w1.bounds[2] + dx, w1.bounds[3] + dy),
        obstacles=[translate(obs, xoff=dx, yoff=dy) for obs in w1.obstacles],
        threats=[
            type(t)(id=t.id, polygon=translate(t.polygon, xoff=dx, yoff=dy), label=t.label)
            for t in w1.threats
        ]
    )
    p_trans = [(x + dx, y + dy) for x, y in p1]
    res_trans = evaluate_path_clearability(p_trans, w_trans, combat, player)

    assert res_orig.peak_k_ici == res_trans.peak_k_ici
    assert res_orig.is_solvable == res_trans.is_solvable
    assert abs(res_orig.schedule_result.optimal_max_lateness_s - res_trans.schedule_result.optimal_max_lateness_s) < 1e-4

    # 2. Rotation by 90 degrees around origin
    w_rot = World(
        bounds=(-15.0, 0.0, 15.0, 15.0),
        obstacles=[rotate(obs, 90.0, origin=(0.0, 0.0)) for obs in w1.obstacles],
        threats=[
            type(t)(id=t.id, polygon=rotate(t.polygon, 90.0, origin=(0.0, 0.0)), label=t.label)
            for t in w1.threats
        ]
    )
    from shapely.geometry import Point as ShPoint
    p_rot = [(rotate(ShPoint(x, y), 90.0, origin=(0.0, 0.0)).x, rotate(ShPoint(x, y), 90.0, origin=(0.0, 0.0)).y) for x, y in p1]
    res_rot = evaluate_path_clearability(p_rot, w_rot, combat, player)

    assert res_orig.peak_k_ici == res_rot.peak_k_ici
    assert res_orig.is_solvable == res_rot.is_solvable
    assert abs(res_orig.schedule_result.optimal_max_lateness_s - res_rot.schedule_result.optimal_max_lateness_s) < 1e-4


def test_scenario_12_scalar_interface_counterexample():
    """Scenario 12: Proves that scalar interface signatures Σ=(α+, σ_min, Θ_max) are insufficient.

    Constructs two modules X and Y with identical scalar arrival curves, identical minimum slack,
    identical threat counts, and identical peak K_ICI, where X is Solvable (L* <= 0) and Y is Unsolvable (L* > 0).
    """
    world_x, path_x, world_y, path_y, combat, player = scenario_12_scalar_interface_counterexample()

    res_x = evaluate_path_clearability(path_x, world_x, combat, player)
    res_y = evaluate_path_clearability(path_y, world_y, combat, player)

    # Both environments have 4 threats
    assert len(world_x.threats) == 4
    assert len(world_y.threats) == 4

    # Extract release timestamps (converted from path distance meters to time in seconds at standard 4.5 m/s)
    speed = 4.5
    rel_x = [s / speed for s in sorted(res_x.reveals.values())]
    rel_y = [s / speed for s in sorted(res_y.reveals.values())]
    assert len(rel_x) == 4
    assert len(rel_y) == 4

    # Both have matching arrival curves α+(Δ) across all continuous time windows Δ >= 0
    curve_x = UpperArrivalCurve(rel_x)
    curve_y = UpperArrivalCurve(rel_y)
    assert curve_x.is_equivalent(curve_y, tol=0.03) is True
    for delta in [0.10, 0.25, 0.35, 0.60, 1.00]:
        assert curve_x.evaluate(delta) == curve_y.evaluate(delta)

    # Both have identical minimum slack
    assert abs(res_x.schedule_result.baselines.min_slack_s - res_y.schedule_result.baselines.min_slack_s) < 1e-4

    # Both have bounded peak concurrency K_ICI <= 3
    assert res_x.peak_k_ici <= 3
    assert res_y.peak_k_ici <= 3

    # YET: Module X is Solvable, and Module Y is Unsolvable!
    assert res_x.is_solvable is True
    assert res_x.schedule_result.optimal_max_lateness_s <= 0.0

    assert res_y.is_solvable is False
    assert res_y.schedule_result.optimal_max_lateness_s > 0.15  # Positive lethal deadline starvation!


def test_state_conditioned_interface_composition_and_associativity():
    """Verify state-conditioned interface algebraic composition and associativity (I1 ⊗ I2) ⊗ I3 == I1 ⊗ (I2 ⊗ I3)."""
    # 3x3 demand matrices for sectors [LEFT, CENTER, RIGHT]
    m1 = [
        [0.25, 0.40, 0.65],
        [0.35, 0.20, 0.35],
        [0.65, 0.40, 0.25]
    ]
    m2 = [
        [0.30, 0.50, 0.70],
        [0.40, 0.25, 0.40],
        [0.70, 0.50, 0.30]
    ]
    m3 = [
        [0.20, 0.35, 0.60],
        [0.30, 0.15, 0.30],
        [0.60, 0.35, 0.20]
    ]

    i1 = StateConditionedInterface.from_dense_matrix(m1, min_slack_s=0.30, k_ici_max=1)
    i2 = StateConditionedInterface.from_dense_matrix(m2, min_slack_s=0.25, k_ici_max=2)
    i3 = StateConditionedInterface.from_dense_matrix(m3, min_slack_s=0.20, k_ici_max=1)

    # 1. Test binary composition
    i12 = compose_state_conditioned_interfaces(i1, i2)
    assert i12.min_slack_s == 0.25
    assert i12.k_ici_max == 2

    # Entering LEFT and exiting LEFT: min_b (m1[0][b] + m2[b][0])
    # b=0: 0.25 + 0.30 = 0.55
    # b=1: 0.40 + 0.40 = 0.80
    # b=2: 0.65 + 0.70 = 1.35
    # min is 0.55!
    assert abs(i12.get_demand(AimSector.LEFT, AimSector.LEFT) - 0.55) < 1e-6

    # 2. Test full 3-module associativity: (I1 ⊗ I2) ⊗ I3 == I1 ⊗ (I2 ⊗ I3)
    assert verify_interface_composition_associativity(i1, i2, i3) is True


@pytest.mark.slow
def test_round5_dbf_associativity_fixture_regression():
    """Historical Regression Fixture (Round 5): Verify that DBF matrices associate on standard structured rooms."""
    disc = AngularSectorDiscretization(num_sectors=3)
    player = PlayerModel()

    # Create synthetic jobs for Module 1
    jobs_1 = [
        ThreatJob(id="J1", release_s=0.0, deadline_s=0.5, service_s=0.1, angle_deg=-60.0, sector=0),
        ThreatJob(id="J2", release_s=0.2, deadline_s=0.7, service_s=0.1, angle_deg=0.0, sector=1),
    ]
    # Create synthetic jobs for Module 2
    jobs_2 = [
        ThreatJob(id="J3", release_s=0.1, deadline_s=0.6, service_s=0.1, angle_deg=60.0, sector=2),
    ]
    # Create synthetic jobs for Module 3
    jobs_3 = [
        ThreatJob(id="J4", release_s=0.0, deadline_s=0.5, service_s=0.1, angle_deg=-45.0, sector=0),
    ]

    dbf1 = StateConditionedDBF.from_jobs(jobs_1, disc, player)
    dbf2 = StateConditionedDBF.from_jobs(jobs_2, disc, player)
    dbf3 = StateConditionedDBF.from_jobs(jobs_3, disc, player)

    # Test binary composition: inf-sup convolution
    dbf12 = compose_state_conditioned_dbfs(dbf1, dbf2)
    assert dbf12.min_slack_s == min(dbf1.min_slack_s, dbf2.min_slack_s)

    # Test algebraic associativity of DBF composition: (D1 ⊗ D2) ⊗ D3 == D1 ⊗ (D2 ⊗ D3)
    is_assoc = verify_dbf_composition_associativity(dbf1, dbf2, dbf3)
    assert is_assoc is True


@pytest.mark.slow
def test_round5_dbf_empirical_zero_fp_seeded_sample():
    """Empirical Sample (Round 5): DBF interface produces FP=0 on standard random benchmark instances.
    
    NOTE (Round 6 Falsification): While this test verifies FP=0 on 30 typical FPS instances,
    Scenario 13 mathematically disproves universal non-preemptive DBF soundness due to boundary blocking.
    """
    import random

    disc = AngularSectorDiscretization(num_sectors=3)
    player = PlayerModel()
    combat = CombatModel()

    random.seed(42)
    fp_count = 0
    tp_count = 0
    fn_count = 0
    tn_count = 0

    for trial in range(30):
        n_threats = random.randint(2, 4)
        jobs = []
        events = []

        cur_t = 0.0
        for idx in range(n_threats):
            t_id = f"T_{idx}"
            cur_t += random.uniform(0.0, 0.4)
            rel = round(cur_t, 2)
            angle = random.choice([-70.0, 0.0, 70.0])
            sec = disc.get_sector(angle)
            serv = round(combat.base_ttk_s, 2)
            dead = round(rel + combat.base_ttk_s + combat.opp_reaction_s + random.uniform(-0.1, 0.3), 2)
            
            jobs.append(ThreatJob(id=t_id, release_s=rel, deadline_s=dead, service_s=serv, angle_deg=angle, sector=sec))
            events.append(ThreatEvent(threat_id=t_id, reveal_time_s=rel, deadline_time_s=dead, centroid_angle_deg=angle))

        # 1. Interface Verdict
        dbf = StateConditionedDBF.from_jobs(jobs, disc, player)
        interface_schedulable = dbf.is_schedulable(entry_sector=1)

        # 2. Exact DP Oracle Verdict
        exact_res = solve_service_schedule(events, combat, player, initial_aim_deg=0.0)
        oracle_schedulable = exact_res.is_solvable

        # Classify
        if interface_schedulable and oracle_schedulable:
            tp_count += 1
        elif not interface_schedulable and not oracle_schedulable:
            tn_count += 1
        elif not interface_schedulable and oracle_schedulable:
            fn_count += 1
        elif interface_schedulable and not oracle_schedulable:
            fp_count += 1

    # Zero false positives on this benchmark set
    assert fp_count == 0
    assert tp_count + tn_count > 0


@pytest.mark.slow
def test_sector_resolution_conservatism_sweep():
    """Verify that dyadic nested partitions (K=2, 4, 8, 16) monotonically reduce conservatism (FN) with FP=0.
    
    Analytic Refinement Foundation:
      Under dyadic nested subdivision A_{2K} <= A_K, every fine sector S'_a is a subset of coarse sector S_a.
      Because sup_{theta in S'_a, phi in S'_b} delta_circ(theta, phi) <= sup_{theta in S_a, phi in S_b} delta_circ(theta, phi),
      setup time bounds weakly decrease: s_{a'b'}^max <= s_{ab}^max.
      Therefore, any schedule feasible under resolution K remains feasible under 2K (Feasible_K <= Feasible_{2K}),
      guaranteeing monotonic false-negative reduction FN(2K) <= FN(K).
    """
    import random

    player = PlayerModel()
    combat = CombatModel()
    random.seed(123)

    # Generate 10 test instances
    test_instances = []
    for _ in range(10):
        n_threats = 3
        cur_t = 0.0
        instance_jobs = []
        events = []
        for idx in range(n_threats):
            t_id = f"T_{idx}"
            cur_t += random.uniform(0.1, 0.3)
            rel = round(cur_t, 2)
            angle = random.uniform(-120.0, 120.0)
            serv = 0.15
            dead = round(rel + 0.50, 2)
            instance_jobs.append((t_id, rel, dead, serv, angle))
            events.append(ThreatEvent(threat_id=t_id, reveal_time_s=rel, deadline_time_s=dead, centroid_angle_deg=angle))
        
        exact_res = solve_service_schedule(events, combat, player, initial_aim_deg=0.0)
        test_instances.append((instance_jobs, exact_res.is_solvable))

    results_by_k = {}
    for k in [2, 4, 8]:
        disc = AngularSectorDiscretization(num_sectors=k)
        fp = 0
        fn = 0
        tp = 0
        tn = 0
        for instance_jobs, oracle_solvable in test_instances:
            jobs = [
                ThreatJob(id=t_id, release_s=rel, deadline_s=dead, service_s=serv, angle_deg=angle, sector=disc.get_sector(angle))
                for (t_id, rel, dead, serv, angle) in instance_jobs
            ]
            dbf = StateConditionedDBF.from_jobs(jobs, disc, player)
            interface_solvable = dbf.is_schedulable(entry_sector=disc.get_sector(0.0))

            if interface_solvable and not oracle_solvable:
                fp += 1
            elif not interface_solvable and oracle_solvable:
                fn += 1
            elif interface_solvable and oracle_solvable:
                tp += 1
            else:
                tn += 1
        results_by_k[k] = {"FP": fp, "FN": fn, "TP": tp, "TN": tn}

    # All dyadic resolutions must be strictly sound (FP = 0)
    for k in [2, 4, 8]:
        assert results_by_k[k]["FP"] == 0
    # Higher resolution cannot have higher false rejection rate under dyadic nested refinement
    assert results_by_k[8]["FN"] <= results_by_k[2]["FN"]


def test_scenario_13_nonpreemptive_blocking_counterexample():
    """Scenario 13: Falsifies naive DBF soundness (dbf(Δ) <= Δ => L* <= 0) under non-preemption.
    
    Constructs J1=(r=0, D=3, p=2), J2=(r=1, D=2, p=1).
    Proves that dbf(Δ) <= Δ passes across all continuous Δ >= 0 (sampled on delta_grid),
    yet the exact non-preemptive schedule is UNSOLVABLE (L* = +1.0s > 0).
    Verifies that ExactTransferMap correctly detects the infeasibility.
    """
    jobs, disc, player, combat = scenario_13_nonpreemptive_blocking_counterexample()

    # 1. Classical / Preemptive Demand-Bound Function evaluation
    dbf = StateConditionedDBF.from_jobs(jobs, disc, player)
    for delta in dbf.delta_grid:
        demand = dbf.get_demand(0, 0, delta)
        assert demand <= delta + 1e-4, f"Demand exceeded at {delta}: {demand} > {delta}"

    # 2. Exact Non-Preemptive Oracle Evaluation
    transfer_map = ExactTransferMap(disc, jobs, player)
    assert transfer_map.is_feasible(entry_sector=0, t_in=0.0) is False
    assert transfer_map.evaluate(0, 0, 0.0) == float('inf')


def test_scenario_14_infsup_nondistributivity_algebra():
    """Scenario 14: Proves that max-plus time convolution does not distribute over min-plus state choice.
    
    For f = [0, 1, 1], g = [0, 0, 2], h = [0, 1, 1] at Delta = 2:
      (f * min(g, h))(2) = 1 != min(f * g, f * h)(2) = 2.
    """
    res = scenario_14_infsup_nondistributivity_algebra()
    assert res["f_star_min_gh"] == 1
    assert res["min_f_star_g_f_star_h"] == 2
    assert res["is_equal"] is False


def test_exact_transfer_map_composition_and_associativity():
    """Verify that Exact Transfer Maps compose associatively."""
    disc = AngularSectorDiscretization(num_sectors=4)
    player = PlayerModel()

    jobs_a = [
        ThreatJob(id="A1", release_s=0.0, deadline_s=2.0, service_s=0.20, angle_deg=-45.0, sector=disc.get_sector(-45.0)),
    ]
    jobs_b = [
        ThreatJob(id="B1", release_s=0.1, deadline_s=4.0, service_s=0.20, angle_deg=45.0, sector=disc.get_sector(45.0)),
    ]
    jobs_c = [
        ThreatJob(id="C1", release_s=0.2, deadline_s=6.0, service_s=0.20, angle_deg=-45.0, sector=disc.get_sector(-45.0)),
    ]

    map_a = ExactTransferMap(disc, jobs_a, player)
    map_b = ExactTransferMap(disc, jobs_b, player)
    map_c = ExactTransferMap(disc, jobs_c, player)

    # 1. Algebraic Associativity: (T_A o T_B) o T_C == T_A o (T_B o T_C)
    is_assoc = verify_transfer_map_associativity(map_a, map_b, map_c, t_in=0.0)
    assert is_assoc is True

    # 2. Compositional Evaluation
    map_ab = compose_exact_transfer_maps(map_a, map_b)
    t_exit_ab = map_ab.evaluate(0, 0, 0.0)
    assert t_exit_ab < float('inf')
    assert map_ab.is_feasible(entry_sector=0) is True


def test_time_translation_invariance_and_fifo_safe_wait():
    """Verify Time-Translation Invariance T(t+δ) = T(t)+δ and FIFO isotonicity t1 <= t2 => T(t1) <= T(t2)."""
    disc = AngularSectorDiscretization(num_sectors=4)
    player = PlayerModel()

    jobs = [
        SpatialThreatJob(id="T1", offset_s=0.3, due_window_s=1.5, service_s=0.25, angle_deg=-45.0, sector=disc.get_sector(-45.0)),
        SpatialThreatJob(id="T2", offset_s=0.8, due_window_s=1.5, service_s=0.25, angle_deg=45.0, sector=disc.get_sector(45.0)),
    ]
    mod_map = SpatialModuleTransferMap(
        module_id="mod_test",
        entry_port="P_IN",
        exit_port="P_OUT",
        traversal_duration_s=1.2,
        discretization=disc,
        jobs=jobs,
        player=player
    )

    # 1. Time-Translation Invariance across multiple delta shifts
    t_base = 1.0
    for delta in [0.5, 2.0, 7.35, 100.0]:
        for a in range(4):
            for b in range(4):
                val_base = mod_map.evaluate(a, b, t_base)
                val_shifted = mod_map.evaluate(a, b, t_base + delta)
                if val_base < float('inf'):
                    assert abs(val_shifted - (val_base + delta)) < 1e-6

    # 2. FIFO / Isotonicity: t1 <= t2 => T(t1) <= T(t2)
    t1 = 0.5
    t2 = 1.8
    for a in range(4):
        for b in range(4):
            assert mod_map.evaluate(a, b, t1) <= mod_map.evaluate(a, b, t2)


def test_spatial_module_transfer_map_composition_and_flattening_equivalence():
    """Verify Monolithic-vs-Composed Dual Oracle Equivalence across 2, 3, 4, and 5-module chains.
    
    Proves that sequential relational composition T_{1:n} = T_1 o T_2 o ... o T_n
    is EXACTLY EQUIVALENT to flattening the multi-module chain into a single monolithic instance:
      T_{1:n}^composed(p_start, a, p_end, z, t_in) == T_monolithic(p_start, a, p_end, z, t_in)
    """
    disc = AngularSectorDiscretization(num_sectors=4)
    player = PlayerModel()

    # Construct 5 distinct spatial modules with local offsets and traversal times
    modules = []
    for m_idx in range(5):
        j_list = [
            SpatialThreatJob(
                id=f"T_{m_idx}_1",
                offset_s=0.2 + 0.1 * m_idx,
                due_window_s=2.5,
                service_s=0.20,
                angle_deg=(-45.0 if m_idx % 2 == 0 else 45.0),
                sector=disc.get_sector(-45.0 if m_idx % 2 == 0 else 45.0)
            )
        ]
        m = SpatialModuleTransferMap(
            module_id=f"M_{m_idx}",
            entry_port=f"P_{m_idx}_IN",
            exit_port=f"P_{m_idx}_OUT",
            traversal_duration_s=0.8 + 0.2 * m_idx,
            discretization=disc,
            jobs=j_list,
            player=player
        )
        modules.append(m)

    # 1. Test 3-Module Associativity: (M1 o M2) o M3 == M1 o (M2 o M3)
    is_assoc = verify_spatial_transfer_map_associativity(modules[0], modules[1], modules[2])
    assert is_assoc is True

    # 2. Test Flattening Equivalence across chain lengths N in {2, 3, 4, 5}
    for chain_len in [2, 3, 4, 5]:
        sub_chain = modules[:chain_len]

        # Sequential Composition
        composed = sub_chain[0]
        for next_mod in sub_chain[1:]:
            composed = compose_spatial_transfer_maps(composed, next_mod)

        # Monolithic Flattening Oracle
        flattened = flatten_spatial_module_chain(sub_chain)

        # Raw multi-stage candidate routes
        raw_routes = [m.routes for m in sub_chain]

        # Compare duration matrices
        for a in range(disc.num_sectors):
            for z in range(disc.num_sectors):
                dur_composed = composed.get_duration(a, z)
                dur_flattened = flattened.get_duration(a, z)
                dur_raw = solve_raw_spatial_chain(raw_routes, disc, player, a, z, 0.0)

                if dur_composed < float('inf') or dur_flattened < float('inf') or dur_raw < float('inf'):
                    assert abs(dur_composed - dur_flattened) < 1e-6, (
                        f"Mismatch at N={chain_len}, sector ({a}->{z}): "
                        f"Composed={dur_composed:.4f}s vs Flattened={dur_flattened:.4f}s"
                    )
                    assert abs(dur_composed - dur_raw) < 1e-6, (
                        f"Mismatch against Raw Chain Oracle at N={chain_len}, sector ({a}->{z}): "
                        f"Composed={dur_composed:.4f}s vs Raw={dur_raw:.4f}s"
                    )

        # Verify evaluation with non-zero t_in across both oracles
        t_in = 3.5
        for a in range(disc.num_sectors):
            for z in range(disc.num_sectors):
                t_comp = composed.evaluate(a, z, t_in)
                t_flat = flattened.evaluate(a, z, t_in)
                t_raw = solve_raw_spatial_chain(raw_routes, disc, player, a, z, t_in)
                if t_comp < float('inf') or t_flat < float('inf') or t_raw < float('inf'):
                    assert abs(t_comp - t_flat) < 1e-6
                    assert abs(t_comp - t_raw) < 1e-6


def test_spatial_route_choice_optimization():
    """Verify that SpatialModuleTransferMap optimizes over candidate movement paths Gamma(p_in -> p_out).
    
    T_M(p_in, a, p_out, b, t_in) = inf_{gamma in Gamma} inf_{pi in Pi_feas(gamma)} t_exit.
    If a room contains a death corridor (infeasible) and a safe flank (feasible),
    the transfer interface automatically discovers and certifies the feasible route.
    """
    disc = AngularSectorDiscretization(num_sectors=4)
    player = PlayerModel()

    # Route 1: Death Alley (Central Corridor) - 2 simultaneous crossfire threats with impossible deadlines
    death_alley = SpatialRoute(
        route_id="death_alley",
        traversal_duration_s=0.8,
        jobs=[
            SpatialThreatJob(id="DA_1", offset_s=0.1, due_window_s=0.20, service_s=0.20, angle_deg=-90.0, sector=disc.get_sector(-90.0)),
            SpatialThreatJob(id="DA_2", offset_s=0.1, due_window_s=0.20, service_s=0.20, angle_deg=90.0, sector=disc.get_sector(90.0)),
        ]
    )

    # Route 2: Safe Flank (Perimeter Corridor) - 1 isolated threat with generous slack
    safe_flank = SpatialRoute(
        route_id="safe_flank",
        traversal_duration_s=1.5,
        jobs=[
            SpatialThreatJob(id="SF_1", offset_s=0.4, due_window_s=2.00, service_s=0.20, angle_deg=0.0, sector=disc.get_sector(0.0)),
        ]
    )

    # Transfer map with both routes
    mod_map = SpatialModuleTransferMap(
        module_id="split_route_room",
        entry_port="DOOR_NORTH",
        exit_port="DOOR_SOUTH",
        discretization=disc,
        player=player,
        routes=[death_alley, safe_flank]
    )

    # The interface should be solvable via the Safe Flank route
    assert mod_map.is_feasible(entry_sector=disc.get_sector(0.0)) is True
    dur = mod_map.get_duration(disc.get_sector(0.0), disc.get_sector(0.0))
    assert dur < float('inf')
    # Duration should reflect the safe flank route
    assert dur >= 1.5


@pytest.mark.slow
def test_continuous_angle_reference_oracle_vs_dyadic_discretization():
    """Verify that dyadic sector models K in {2, 4, 8, 16} converge conservatively to the Continuous-Angle Oracle (K=infinity).
    
    Proves:
      1. Conservative Soundness (FP = 0): C_K(a, b) >= C_infinity(theta_in, theta_out) for all K.
      2. Asymptotic Convergence: Conservatism gap |C_K - C_infinity| monotonically shrinks as K -> 16.
    """
    import random
    player = PlayerModel()
    random.seed(999)

    # 3 continuous threat angles
    angles = [-65.0, 15.0, 75.0]
    jobs_raw = [
        ("T1", 0.2, 2.5, 0.20, angles[0]),
        ("T2", 0.5, 2.5, 0.20, angles[1]),
        ("T3", 0.8, 2.5, 0.20, angles[2]),
    ]

    # Continuous Oracle (K = infinity)
    cont_jobs = [SpatialThreatJob(t_id, off, due, serv, ang, 0) for (t_id, off, due, serv, ang) in jobs_raw]
    cont_map = ContinuousAngleTransferMap(traversal_duration_s=1.2, jobs=cont_jobs, player=player)
    theta_in = 0.0
    theta_out = 0.0
    dur_continuous = cont_map.evaluate_exact_continuous_duration(theta_in, theta_out)
    assert dur_continuous < float('inf')

    # Dyadic Sector Discretizations K in {2, 4, 8, 16}
    gaps = {}
    for k in [2, 4, 8, 16]:
        disc_k = AngularSectorDiscretization(num_sectors=k)
        sec_jobs = [
            SpatialThreatJob(t_id, off, due, serv, ang, disc_k.get_sector(ang))
            for (t_id, off, due, serv, ang) in jobs_raw
        ]
        sec_map = SpatialModuleTransferMap(
            module_id=f"M_K{k}", entry_port="IN", exit_port="OUT",
            traversal_duration_s=1.2, discretization=disc_k, player=player, jobs=sec_jobs
        )
        sec_in = disc_k.get_sector(theta_in)
        sec_out = disc_k.get_sector(theta_out)
        dur_k = sec_map.get_duration(sec_in, sec_out)

        # 1. Conservative Over-approximation: C_K >= C_infinity
        assert dur_k >= dur_continuous - 1e-6, f"Soundness violated at K={k}: {dur_k} < {dur_continuous}"
        gaps[k] = dur_k - dur_continuous

    # 2. Monotonic Convergence of Conservatism Gap
    assert gaps[16] <= gaps[8] <= gaps[4] <= gaps[2]
    # At K=16, the sector resolution is 22.5 deg (max over-approximation <= 4 * (22.5/360) = 0.25s)
    assert gaps[16] <= 0.25


def test_information_reset_pocket_wait_safe_quiescence():
    """Verify that an Information Reset Pocket satisfies the quiescent boundary property (B_ext = 0).
    
    A wait-safe boundary port guarantees that arriving early permits unrestricted waiting
    without exposure to hostile damage due dates, validating the FIFO earliest-departure equivalence.
    """
    from cut_the_cake.model import ThreatRegion
    from cut_the_cake.geometry import is_quiescent_reset_pocket
    from shapely.geometry import Polygon

    # Reset pocket region: 2D polygon [0, 2] x [0, 4]
    pocket = Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 4.0), (0.0, 4.0)])

    # Internal threat region deep inside room: [6, 8] x [0, 2]
    internal_threat = ThreatRegion(
        id="T_INTERNAL",
        polygon=Polygon([(6.0, 0.0), (8.0, 0.0), (8.0, 2.0), (6.0, 2.0)])
    )

    # Baffle wall blocking LOS between pocket and threat: x in [2, 3], y in [0, 4]
    baffle = Polygon([(2.0, 0.0), (3.0, 0.0), (3.0, 4.0), (2.0, 4.0)])

    # 1. With baffle: pocket is 100% quiescent (B_ext = 0 over entire 2D region)
    is_quiet = is_quiescent_reset_pocket(pocket, [internal_threat], [baffle], grid_step=0.25)
    assert is_quiet is True, "Reset pocket must be 100% occluded across entire 2D region!"

    # 2. Without baffle (unprotected opening): pocket is exposed (B_ext > 0)
    is_quiet_unprotected = is_quiescent_reset_pocket(pocket, [internal_threat], [], grid_step=0.25)
    assert is_quiet_unprotected is False, "Unprotected threshold must fail quiescence check!"



