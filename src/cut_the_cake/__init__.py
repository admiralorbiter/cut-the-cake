"""FPS Tactical Clearability Validator package."""

from .model import World, ThreatRegion, Module, Port, CombatModel, PlayerModel, ThreatView
from .geometry import distance, angle_diff_deg, heading_to_deg, is_segment_blocked
from .visibility import compute_visible_threats, compute_threat_view
from .conflicts import build_threat_incompatibility_graph
from .service_solver import solve_service_schedule
from .paths import evaluate_path_clearability
from .contracts import (
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
    solve_monolithic_module_chain_dp,
    flatten_spatial_module_chain,
    solve_raw_spatial_chain,
    ContinuousAngleTransferMap
)
from .geometry import is_quiescent_reset_pocket
from .render import format_clearability_report, render_ascii_map
from .scenarios import (
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
    scenario_12_scalar_interface_counterexample
)
from .pcg_modules import (
    AuthoredModule,
    build_authored_module_library,
    build_precertified_library,
    build_heldout_module_library,
    audit_library_continuous_oracle
)
from .generator import (
    ModuleAssembly,
    AssemblyAuditResult,
    DiscriminationCorpusReport,
    KICISweepRow,
    MapElitesArchive,
    ReplicatedMAPElitesSummary,
    PairedDifferenceStats,
    RegimeSweepRow,
    audit_module_assembly,
    audit_precertified_assembly,
    run_corpus_discrimination_sweep,
    run_kici_threshold_sweep,
    run_constrained_map_elites,
    run_replicated_map_elites,
    compute_paired_differences,
    run_combat_regime_sweep,
    extract_counterexample_galleries
)
from .compiler import (
    GeometricThreat,
    GeometricPort,
    GeometricRoute,
    GeometricModule,
    CompilationStatus,
    DualOracleRevealEngine,
    AimBearingCompiler,
    DeadlinePolicy,
    ConstantDeadlinePolicy,
    RangeDependentDeadlinePolicy,
    validate_geometry_integrity,
    compute_exact_visibility_polygon,
    certify_port_quiescence,
    CompiledRouteResult,
    CompiledModuleResult,
    GeometryToContractCompiler
)
from .fixtures_round10 import (
    build_f01_analytical_corner,
    build_f02_three_stage_pie_reveal,
    build_f02b_three_angle_sector_sweep,
    build_f03_multi_aperture_doorway,
    build_f04_disappearing_reappearing_threat,
    build_f05_two_route_flank_choice,
    build_f06_wall_perturbation_fixture,
    build_f07_visibility_flash,
    build_f07_adversarial_flash,
    build_f08_ninety_degree_turn_corner,
    build_geometric_m01_straight_corridor,
    build_geometric_m03_pie_slice_left_sweep,
    build_geometric_m04_staggered_triple_reveal,
    build_geometric_m11_rapid_crossfire_aperture,
    build_geometric_m08_high_concurrency_solvable,
    build_geometric_m07_flank_bypass_room
)
from .vizdoom_engine import (
    TicCombatParameters,
    TicThreatJob,
    DiscreteScheduleResult,
    DiscreteTicScheduler,
    ControllerPolicy,
    SimulationController,
    SimulationEpisodeLog,
    DeterministicSimulationReferee,
    NoiseSimulationHarness,
    ArenaBenchmarkRecord,
    BaselineEvaluationMetrics,
    PopulationBenchmarkReport,
    run_population_benchmark,
    evaluate_baseline_shootout
)
from .vizdoom_fixtures import (
    build_family1_staggered_wall,
    build_family2_angular_crossfire,
    build_family3_aperture_congestion,
    build_family4_three_threat_alternating,
    build_family5_deadline_compression,
    build_family6_flank_sweep_smoothness,
    build_round11_benchmark_suite,
    build_parametric_wall_arena,
    build_disagreement_arena_kici_blindspot,
    build_disagreement_arena_kici_falsealarm,
    build_large_margin_arena
)
from .vizdoom_bridge import (
    export_geometric_module_to_wad,
    RealViZDoomEpisodeLog,
    ViZDoomRealBridge,
    build_12_arena_bridge_suite,
    ResidualDecompositionRecord,
    EngineResidualReport,
    run_residual_decomposition_analysis
)

__version__ = "0.1.0"


