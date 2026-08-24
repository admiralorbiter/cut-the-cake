"""Procedural Level Generator, Discrimination Sweep, and Constrained MAP-Elites (Round 8).

Implements:
1. Condition-Blind Common-Corpus Discrimination Audit (Round 8A) comparing:
   - Audit A: Topology & Port Validity
   - Audit B: Static K_ICI Concurrency Heuristic (K_ICI <= 2)
   - Audit C: Composed Spatial Transfer Feasibility (ΔT_1:N < inf with aim state memory)
   - Audit D: Local-Only Transfer Audit (Each module individually feasible)
   - Audit ∞: Continuous-Angle Ground Truth Reference Oracle on sample subset
2. Path-Conditioned Constrained MAP-Elites Search (Round 8B)
3. Counterexample Gallery Extractor (Round 8C)
"""

from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from .model import PlayerModel
from .contracts import (
    PRODUCTION_NUM_SECTORS,
    AngularSectorDiscretization,
    SpatialModuleTransferMap,
    ContinuousAngleTransferMap,
    compose_spatial_transfer_maps
)
from .pcg_modules import (
    AuthoredModule,
    build_authored_module_library,
    build_precertified_library,
    build_heldout_module_library
)


@dataclass
class ModuleAssembly:
    """Represents a generated sequence of modules along a macro-route skeleton."""
    modules: List[AuthoredModule]

    @property
    def length(self) -> int:
        return len(self.modules)

    def compute_pace_proxy(self, disc: AngularSectorDiscretization, player: PlayerModel) -> float:
        """Pace Proxy: Total minimum traversable duration in seconds."""
        total = 0.0
        for m in self.modules:
            tmap = m.get_transfer_map(disc, player)
            total += tmap.traversal_duration_s
        return total

    def compute_route_redundancy(self) -> int:
        """Route Redundancy: Count of modules offering multiple candidate paths."""
        return sum(1 for m in self.modules if len(m.routes) > 1)

    def compute_quiescent_count(self) -> int:
        """Count of modules containing quiescent reset pockets."""
        return sum(1 for m in self.modules if m.is_quiescent)

    def compute_peak_k_ici(self) -> int:
        """Peak instantaneous sightline concurrency along the chain."""
        return max(m.k_ici_max for m in self.modules) if self.modules else 0

    def compute_repetition_penalty(self) -> float:
        """Structural score: reward module diversity, penalize duplicate consecutive modules."""
        ids = [m.module_id for m in self.modules]
        unique_count = len(set(ids))
        consecutive_repeats = sum(1 for i in range(len(ids) - 1) if ids[i] == ids[i + 1])
        # Score in [0, 1]: higher is more structurally diverse
        score = (unique_count / max(1, len(ids))) - 0.25 * consecutive_repeats
        return max(0.0, score)


@dataclass
class AssemblyAuditResult:
    """Audit outcomes for a single module assembly."""
    assembly: ModuleAssembly
    audit_a_topology: bool
    audit_b_kici: bool
    audit_c_transfer: bool
    audit_d_local: bool
    transfer_duration_s: float
    pace_proxy: float
    route_redundancy: int
    repetition_score: float
    peak_k_ici: int = 1
    audit_continuous_oracle: Optional[bool] = None


def audit_module_assembly(
    assembly: ModuleAssembly,
    discretization: AngularSectorDiscretization,
    player: PlayerModel,
    entry_sector: Optional[int] = None
) -> AssemblyAuditResult:
    """Run Audits A, B, C, D on a single module assembly with optimized NumPy min-plus matrix composition."""
    modules = assembly.modules
    K = discretization.num_sectors

    # Canonical level spawn aim: facing forward along path (0.0 degrees)
    if entry_sector is None:
        entry_sector = discretization.get_sector(0.0)

    # Audit A: Topology / Port matching
    audit_a = True
    for i in range(len(modules) - 1):
        if modules[i].exit_port_type != modules[i + 1].entry_port_type:
            audit_a = False
            break

    # Peak K_ICI across modules along chain
    peak_k = max(m.k_ici_max for m in modules) if modules else 0
    audit_b = (peak_k <= 2)

    # Audit D: Local-Only Transfer Audit (checks feasibility from any quiescent reset aim state)
    audit_d = all(m.get_transfer_map(discretization, player).is_feasible_from_any_reset_state() for m in modules)

    # Audit C: Fast Composed Spatial Transfer Feasibility via NumPy min-plus semiring
    if not modules:
        audit_c = False
        comp_dur = float('inf')
    else:
        cur_mat = modules[0].get_transfer_matrix(discretization, player)
        for next_mod in modules[1:]:
            next_mat = next_mod.get_transfer_matrix(discretization, player)
            # Min-plus semiring composition: C[a, c] = min_b (A[a, b] + B[b, c])
            cur_mat = np.min(cur_mat[:, :, None] + next_mat[None, :, :], axis=1)

        comp_dur = float(np.min(cur_mat[entry_sector, :]))
        audit_c = (comp_dur < float('inf'))

    pace = sum(m.get_transfer_map(discretization, player).traversal_duration_s for m in modules)
    redundancy = sum(1 for m in modules if len(m.routes) > 1)
    score = assembly.compute_repetition_penalty()

    return AssemblyAuditResult(
        assembly=assembly,
        audit_a_topology=audit_a,
        audit_b_kici=audit_b,
        audit_c_transfer=audit_c,
        audit_d_local=audit_d,
        transfer_duration_s=comp_dur,
        pace_proxy=pace,
        route_redundancy=redundancy,
        repetition_score=score,
        peak_k_ici=peak_k
    )


def audit_precertified_assembly(
    assembly: ModuleAssembly
) -> AssemblyAuditResult:
    """Lightweight audit for Precertified Library (Condition E): skips all runtime transfer map composition."""
    modules = assembly.modules

    # Audit A: Topology matching
    audit_a = True
    for i in range(len(modules) - 1):
        if modules[i].exit_port_type != modules[i + 1].entry_port_type:
            audit_a = False
            break

    peak_k = max(m.k_ici_max for m in modules) if modules else 0
    pace = sum(m.routes[0].traversal_duration_s for m in modules) if modules else 0.0
    redundancy = sum(1 for m in modules if len(m.routes) > 1)
    score = assembly.compute_repetition_penalty()

    return AssemblyAuditResult(
        assembly=assembly,
        audit_a_topology=audit_a,
        audit_b_kici=(peak_k <= 2),
        audit_c_transfer=True,
        audit_d_local=True,
        transfer_duration_s=pace,
        pace_proxy=pace,
        route_redundancy=redundancy,
        repetition_score=score,
        peak_k_ici=peak_k
    )


@dataclass
class DiscriminationCorpusReport:
    """Statistical report of the condition-blind common-corpus sweep (Round 8A)."""
    total_samples: int
    pass_a_count: int
    pass_b_count: int
    pass_c_count: int
    pass_d_count: int
    
    # Overlap / Intersection Sets
    count_a_and_b_and_not_c: int  # K_ICI False Positives (Lethal traps accepted by B)
    count_a_and_not_b_and_c: int  # K_ICI False Alarms (Solvable layouts rejected by B)
    count_c_and_d_match: int      # Chain composition equals local solvability
    count_c_diff_d: int           # Chain composition differs from local solvability
    
    # Continuous Oracle Sample Audit
    sampled_oracle_count: int
    sampled_oracle_genuine_pathology: int
    sampled_oracle_conservative_gap: int
    
    # Timings
    elapsed_seconds: float
    samples_per_second: float

    def format_report(self) -> str:
        pct = lambda c: (c / max(1, self.total_samples)) * 100.0
        lines = [
            "=======================================================================",
            "  ROUND 8A: CONDITION-BLIND COMMON-CORPUS DISCRIMINATION AUDIT",
            "=======================================================================",
            f"  • Total Assemblies Evaluated:      {self.total_samples:,} (Length N=6)",
            f"  • Evaluation Throughput:          {self.samples_per_second:,.1f} layouts/s ({self.elapsed_seconds:.2f}s total)",
            "",
            "--- INDEPENDENT PASS RATES ---",
            f"  • Audit A (Physical / Topology):   {self.pass_a_count:,} ({pct(self.pass_a_count):.2f}%)",
            f"  • Audit B (Static K_ICI <= 2):     {self.pass_b_count:,} ({pct(self.pass_b_count):.2f}%)",
            f"  • Audit C (Composed Transfer):     {self.pass_c_count:,} ({pct(self.pass_c_count):.2f}%)",
            f"  • Audit D (Local-Only Transfer):   {self.pass_d_count:,} ({pct(self.pass_d_count):.2f}%)",
            "",
            "--- METRIC DISCRIMINATION BREAKDOWN ---",
            f"  • [A ∩ B ∩ ¬C] (KICI False Positives / Blind Spot):   {self.count_a_and_b_and_not_c:,} ({pct(self.count_a_and_b_and_not_c):.2f}%)",
            f"    -> Accepted by static K_ICI <= 2, but provably MODEL-INFEASIBLE under sequential aiming latency (L* > 0)!",
            f"  • [A ∩ ¬B ∩ C] (KICI False Alarms / Over-Rejection):  {self.count_a_and_not_b_and_c:,} ({pct(self.count_a_and_not_b_and_c):.2f}%)",
            f"    -> Rejected by K_ICI > 2, but provably SOLVABLE via staggered deadline slack!",
            f"  • [C vs D] (Chain vs Local Match):  {self.count_c_and_d_match:,} ({pct(self.count_c_and_d_match):.2f}%) match, {self.count_c_diff_d:,} differ",
            "",
            "--- CONTINUOUS-ANGLE ORACLE (K=∞) SUBSAMPLE AUDIT ---",
            f"  • Subsampled Rejections Checked:   {self.sampled_oracle_count:,}",
            f"  • Confirmed True Infeasible:       {self.sampled_oracle_genuine_pathology:,} ({100.0 * self.sampled_oracle_genuine_pathology / max(1, self.sampled_oracle_count):.1f}%)",
            f"  • False Rejections (Sector Gap):   {self.sampled_oracle_conservative_gap:,} ({100.0 * self.sampled_oracle_conservative_gap / max(1, self.sampled_oracle_count):.1f}%)",
            "=======================================================================\n"
        ]
        return "\n".join(lines)


def run_corpus_discrimination_sweep(
    module_library: Optional[List[AuthoredModule]] = None,
    chain_length: int = 6,
    n_samples: int = 25000,
    seed: int = 42,
    oracle_subsample: int = 100
) -> Tuple[DiscriminationCorpusReport, List[AssemblyAuditResult]]:
    """Generate a large condition-blind corpus and run Audits A, B, C, D across every candidate."""
    disc = AngularSectorDiscretization(num_sectors=PRODUCTION_NUM_SECTORS)
    player = PlayerModel()
    library = module_library or build_authored_module_library(disc)
    rng = random.Random(seed)

    results: List[AssemblyAuditResult] = []
    t_start = time.time()

    pass_a = 0
    pass_b = 0
    pass_c = 0
    pass_d = 0
    a_b_not_c = 0
    a_not_b_c = 0
    c_d_match = 0
    c_diff_d = 0

    for _ in range(n_samples):
        # Sample chain_length modules uniformly from the 16-module library
        chosen_mods = [rng.choice(library) for _ in range(chain_length)]
        assembly = ModuleAssembly(modules=chosen_mods)
        audit = audit_module_assembly(assembly, disc, player)
        results.append(audit)

        if audit.audit_a_topology:
            pass_a += 1
        if audit.audit_b_kici:
            pass_b += 1
        if audit.audit_c_transfer:
            pass_c += 1
        if audit.audit_d_local:
            pass_d += 1

        if audit.audit_a_topology and audit.audit_b_kici and not audit.audit_c_transfer:
            a_b_not_c += 1
        if audit.audit_a_topology and not audit.audit_b_kici and audit.audit_c_transfer:
            a_not_b_c += 1

        if audit.audit_c_transfer == audit.audit_d_local:
            c_d_match += 1
        else:
            c_diff_d += 1

    t_elapsed = time.time() - t_start
    throughput = n_samples / max(1e-4, t_elapsed)

    # Subsampled Continuous-Angle Oracle validation on rejections (Audit C == False)
    rejected_c = [r for r in results if not r.audit_c_transfer]
    sample_rejections = rng.sample(rejected_c, min(oracle_subsample, len(rejected_c))) if rejected_c else []
    
    true_pathology = 0
    conservative_gap = 0

    for item in sample_rejections:
        # Check continuous oracle on each module along the chosen chain
        is_cont_solvable = True
        for m in item.assembly.modules:
            # Flatten raw continuous jobs from primary route
            raw_jobs = m.routes[0].jobs if m.routes else []
            cont_map = ContinuousAngleTransferMap(
                traversal_duration_s=m.routes[0].traversal_duration_s if m.routes else 1.0,
                jobs=raw_jobs,
                player=player
            )
            # Evaluate continuous transfer from 0 to 0
            dur = cont_map.evaluate_exact_continuous_duration(0.0, 0.0)
            if dur == float('inf'):
                is_cont_solvable = False
                break
        
        if not is_cont_solvable:
            true_pathology += 1
            item.audit_continuous_oracle = False
        else:
            conservative_gap += 1
            item.audit_continuous_oracle = True

    report = DiscriminationCorpusReport(
        total_samples=n_samples,
        pass_a_count=pass_a,
        pass_b_count=pass_b,
        pass_c_count=pass_c,
        pass_d_count=pass_d,
        count_a_and_b_and_not_c=a_b_not_c,
        count_a_and_not_b_and_c=a_not_b_c,
        count_c_and_d_match=c_d_match,
        count_c_diff_d=c_diff_d,
        sampled_oracle_count=len(sample_rejections),
        sampled_oracle_genuine_pathology=true_pathology,
        sampled_oracle_conservative_gap=conservative_gap,
        elapsed_seconds=t_elapsed,
        samples_per_second=throughput
    )

    return report, results


@dataclass
class KICISweepRow:
    """Evaluation metrics for a single K_ICI integer threshold."""
    k_threshold: int
    true_positives: int     # Transfer Feasible and Peak K <= k
    false_positives: int    # Transfer Infeasible and Peak K <= k
    true_negatives: int     # Transfer Infeasible and Peak K > k
    false_negatives: int    # Transfer Feasible and Peak K > k
    precision: float
    recall: float
    accuracy: float
    balanced_accuracy: float
    f1_score: float

    def format_row(self) -> str:
        return (
            f"| K_ICI <= {self.k_threshold:<2} | {self.true_positives:>6,} | {self.false_positives:>6,} "
            f"| {self.false_negatives:>6,} | {self.true_negatives:>6,} | {self.precision * 100.0:>6.1f}% "
            f"| {self.recall * 100.0:>6.1f}% | {self.accuracy * 100.0:>6.1f}% | {self.balanced_accuracy * 100.0:>6.1f}% | {self.f1_score:>6.3f} |"
        )


def run_kici_threshold_sweep(
    audit_results: List[AssemblyAuditResult],
    k_thresholds: Optional[List[int]] = None
) -> List[KICISweepRow]:
    """Sweep integer K_ICI thresholds (1, 2, 3, 4, 5) over a common corpus.
    
    Demonstrates that no static integer concurrency threshold can resolve the temporal
    directional information loss inherent in static sightline counting.
    """
    thresholds = k_thresholds or [1, 2, 3, 4, 5]
    rows: List[KICISweepRow] = []

    for k in thresholds:
        tp = 0
        fp = 0
        tn = 0
        fn = 0

        for r in audit_results:
            k_pass = (r.peak_k_ici <= k)
            transfer_pass = r.audit_c_transfer

            if transfer_pass and k_pass:
                tp += 1
            elif not transfer_pass and k_pass:
                fp += 1
            elif not transfer_pass and not k_pass:
                tn += 1
            elif transfer_pass and not k_pass:
                fn += 1

        prec = tp / max(1, (tp + fp))
        rec = tp / max(1, (tp + fn))
        acc = (tp + tn) / max(1, (tp + fp + tn + fn))
        tpr = rec
        tnr = tn / max(1, (tn + fp))
        bal_acc = (tpr + tnr) / 2.0
        f1 = (2.0 * prec * rec) / max(1e-6, (prec + rec))

        rows.append(KICISweepRow(
            k_threshold=k,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision=prec,
            recall=rec,
            accuracy=acc,
            balanced_accuracy=bal_acc,
            f1_score=f1
        ))

    return rows


@dataclass
class MapElitesArchive:
    """2D Behavioral Archive for Quality-Diversity Search."""
    condition_name: str
    pace_bins: int = 15          # Dimension 1: Pace Proxy [4.0s, 16.0s]
    redundancy_bins: int = 7     # Dimension 2: Route Redundancy [0, 6]
    pace_min: float = 4.0
    pace_max: float = 16.0
    grid: Dict[Tuple[int, int], AssemblyAuditResult] = field(default_factory=dict)
    total_evaluations: int = 0
    accepted_evaluations: int = 0
    recent_accepts: int = 0
    admission_trajectory: List[Tuple[int, float]] = field(default_factory=list)

    def _get_cell(self, pace: float, redundancy: int) -> Tuple[int, int]:
        p_clamped = max(self.pace_min, min(self.pace_max, pace))
        p_norm = (p_clamped - self.pace_min) / (self.pace_max - self.pace_min)
        p_idx = int(p_norm * (self.pace_bins - 1))
        r_clamped = max(0, min(self.redundancy_bins - 1, redundancy))
        return (p_idx, r_clamped)

    def try_insert(self, audit: AssemblyAuditResult) -> bool:
        """Insert candidate if it passes the condition's admission constraint and improves cell score."""
        self.total_evaluations += 1

        # Check admission constraint
        is_admitted = False
        if self.condition_name == "Condition_A_Topology" and audit.audit_a_topology:
            is_admitted = True
        elif self.condition_name == "Condition_B_KICI" and (audit.audit_a_topology and audit.audit_b_kici):
            is_admitted = True
        elif self.condition_name == "Condition_C_Transfer" and (audit.audit_a_topology and audit.audit_c_transfer):
            is_admitted = True
        elif self.condition_name == "Condition_E_Precertified" and audit.audit_a_topology:
            is_admitted = True

        if is_admitted:
            self.accepted_evaluations += 1
            self.recent_accepts += 1

        # Track trajectory every 500 evaluations unconditionally
        if self.total_evaluations % 500 == 0:
            rate = (self.recent_accepts / 500.0) * 100.0
            self.admission_trajectory.append((self.total_evaluations, rate))
            self.recent_accepts = 0

        if not is_admitted:
            return False

        cell = self._get_cell(audit.pace_proxy, audit.route_redundancy)
        if cell not in self.grid or audit.repetition_score > self.grid[cell].repetition_score:
            self.grid[cell] = audit
            return True
        return False

    @property
    def total_cells(self) -> int:
        return self.pace_bins * self.redundancy_bins

    @property
    def occupied_cells(self) -> int:
        return len(self.grid)

    @property
    def coverage_pct(self) -> float:
        return (self.occupied_cells / max(1, self.total_cells)) * 100.0

    @property
    def average_quality(self) -> float:
        if not self.grid:
            return 0.0
        return float(np.mean([res.repetition_score for res in self.grid.values()]))

    @property
    def max_quality(self) -> float:
        if not self.grid:
            return 0.0
        return float(max(res.repetition_score for res in self.grid.values()))

    @property
    def qd_score(self) -> float:
        """Quality-Diversity Score: Sum of elite quality scores across all occupied cells."""
        return float(sum(res.repetition_score for res in self.grid.values()))

    @property
    def admission_rate_pct(self) -> float:
        return (self.accepted_evaluations / max(1, self.total_evaluations)) * 100.0


def run_constrained_map_elites(
    condition_name: str,
    module_library: Optional[List[AuthoredModule]] = None,
    chain_length: int = 6,
    budget: int = 5000,
    seed: int = 42
) -> MapElitesArchive:
    """Run matched Constrained MAP-Elites evolutionary search for a given admission condition."""
    disc = AngularSectorDiscretization(num_sectors=PRODUCTION_NUM_SECTORS)
    player = PlayerModel()
    
    # For Condition E, library is pre-filtered at compile time
    if condition_name == "Condition_E_Precertified":
        raw_lib = module_library or build_authored_module_library(disc)
        library = build_precertified_library(raw_lib, disc, player)
    else:
        library = module_library or build_authored_module_library(disc)

    rng = random.Random(seed)
    archive = MapElitesArchive(condition_name=condition_name)

    def eval_candidate(ass: ModuleAssembly) -> AssemblyAuditResult:
        if condition_name == "Condition_E_Precertified":
            return audit_precertified_assembly(ass)
        return audit_module_assembly(ass, disc, player)

    # Initial random population (10% of budget)
    initial_pop_size = max(50, budget // 10)
    for _ in range(initial_pop_size):
        mods = [rng.choice(library) for _ in range(chain_length)]
        assembly = ModuleAssembly(modules=mods)
        archive.try_insert(eval_candidate(assembly))

    # Evolutionary loop
    for _ in range(budget - initial_pop_size):
        if not archive.grid:
            parent_mods = [rng.choice(library) for _ in range(chain_length)]
        else:
            elite_audit = rng.choice(list(archive.grid.values()))
            parent_mods = list(elite_audit.assembly.modules)

        # Mutate: 1-point or 2-point module replacement
        mutated_mods = list(parent_mods)
        num_mutations = rng.choice([1, 1, 2])
        for _ in range(num_mutations):
            pos = rng.randrange(chain_length)
            mutated_mods[pos] = rng.choice(library)

        child_assembly = ModuleAssembly(modules=mutated_mods)
        archive.try_insert(eval_candidate(child_assembly))

    return archive


@dataclass
class PairedDifferenceStats:
    """Paired seed difference statistics between two generator conditions."""
    comp_name: str
    mean_diff: float
    std_diff: float
    ci95_diff: Tuple[float, float]
    p_non_inferior_2pct: bool


@dataclass
class ReplicatedMAPElitesSummary:
    """Aggregated statistics across multiple paired seeds for a generator condition."""
    condition_name: str
    n_seeds: int
    mean_coverage_pct: float
    std_coverage_pct: float
    ci95_coverage_pct: Tuple[float, float]
    mean_qd_score: float
    std_qd_score: float
    ci95_qd_score: Tuple[float, float]
    mean_avg_quality: float
    mean_max_quality: float
    mean_admission_rate_pct: float
    admission_trajectory: List[Tuple[int, float]]
    seed_coverages: List[float] = field(default_factory=list)
    seed_qd_scores: List[float] = field(default_factory=list)


def run_replicated_map_elites(
    conditions: Optional[List[str]] = None,
    module_library: Optional[List[AuthoredModule]] = None,
    chain_length: int = 6,
    budget: int = 5000,
    n_seeds: int = 30,
    seed_start: int = 42
) -> Dict[str, ReplicatedMAPElitesSummary]:
    """Run replicated Constrained MAP-Elites across multiple paired seeds for rigorous statistical validation."""
    cond_list = conditions or [
        "Condition_A_Topology",
        "Condition_B_KICI",
        "Condition_C_Transfer",
        "Condition_E_Precertified"
    ]
    summaries: Dict[str, ReplicatedMAPElitesSummary] = {}

    for cond in cond_list:
        coverages = []
        qd_scores = []
        avg_qualities = []
        max_qualities = []
        admissions = []
        trajectories = []

        for s_idx in range(n_seeds):
            seed = seed_start + s_idx
            archive = run_constrained_map_elites(
                condition_name=cond,
                module_library=module_library,
                chain_length=chain_length,
                budget=budget,
                seed=seed
            )
            coverages.append(archive.coverage_pct)
            qd_scores.append(archive.qd_score)
            avg_qualities.append(archive.average_quality)
            max_qualities.append(archive.max_quality)
            admissions.append(archive.admission_rate_pct)
            if archive.admission_trajectory:
                trajectories.append([rate for _, rate in archive.admission_trajectory])

        # Compute means and 95% confidence intervals (t-critical ~ 2.045 for N=30)
        mean_cov = float(np.mean(coverages))
        std_cov = float(np.std(coverages, ddof=1)) if n_seeds > 1 else 0.0
        ci_cov = (mean_cov - 1.96 * std_cov / np.sqrt(n_seeds), mean_cov + 1.96 * std_cov / np.sqrt(n_seeds))

        mean_qd = float(np.mean(qd_scores))
        std_qd = float(np.std(qd_scores, ddof=1)) if n_seeds > 1 else 0.0
        ci_qd = (mean_qd - 1.96 * std_qd / np.sqrt(n_seeds), mean_qd + 1.96 * std_qd / np.sqrt(n_seeds))

        # Average trajectory
        if trajectories and all(len(t) > 0 for t in trajectories):
            min_len = min(len(t) for t in trajectories)
            trimmed = [t[:min_len] for t in trajectories]
            avg_traj_rates = np.mean(trimmed, axis=0)
            step_interval = 500
            avg_traj = [((i + 1) * step_interval, float(avg_traj_rates[i])) for i in range(len(avg_traj_rates))]
        else:
            avg_traj = []

        summaries[cond] = ReplicatedMAPElitesSummary(
            condition_name=cond,
            n_seeds=n_seeds,
            mean_coverage_pct=mean_cov,
            std_coverage_pct=std_cov,
            ci95_coverage_pct=ci_cov,
            mean_qd_score=mean_qd,
            std_qd_score=std_qd,
            ci95_qd_score=ci_qd,
            mean_avg_quality=float(np.mean(avg_qualities)),
            mean_max_quality=float(np.mean(max_qualities)),
            mean_admission_rate_pct=float(np.mean(admissions)),
            admission_trajectory=avg_traj,
            seed_coverages=coverages,
            seed_qd_scores=qd_scores
        )

    return summaries


def compute_paired_differences(
    summary_test: ReplicatedMAPElitesSummary,
    summary_ref: ReplicatedMAPElitesSummary,
    non_inferiority_margin: float = 2.0
) -> PairedDifferenceStats:
    """Compute paired seed differences (Test - Ref) with 95% confidence intervals and non-inferiority check."""
    diffs = np.array(summary_test.seed_coverages) - np.array(summary_ref.seed_coverages)
    n = len(diffs)
    mean_d = float(np.mean(diffs))
    std_d = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
    margin = 1.96 * std_d / np.sqrt(n)
    ci95 = (mean_d - margin, mean_d + margin)
    non_inf = ci95[0] > -non_inferiority_margin

    return PairedDifferenceStats(
        comp_name=f"{summary_test.condition_name} - {summary_ref.condition_name}",
        mean_diff=mean_d,
        std_diff=std_d,
        ci95_diff=ci95,
        p_non_inferior_2pct=non_inf
    )


@dataclass
class RegimeSweepRow:
    """Summary of metric discrimination under a specific combat parameter regime."""
    regime_name: str
    acquisition_latency_s: float
    aim_angular_vel_deg_s: float
    due_window_multiplier: float
    pass_b_rate_pct: float
    pass_c_rate_pct: float
    kici_blind_spot_rate_pct: float   # A and B and not C
    kici_false_alarm_rate_pct: float  # A and not B and C

    def format_row(self) -> str:
        return (
            f"| {self.regime_name:<18} | t_acq={self.acquisition_latency_s:.2f}s, w={self.aim_angular_vel_deg_s:.0f}°/s, mult={self.due_window_multiplier:.2f} "
            f"| {self.pass_b_rate_pct:>6.1f}% | {self.pass_c_rate_pct:>6.1f}% | {self.kici_blind_spot_rate_pct:>6.1f}% | {self.kici_false_alarm_rate_pct:>6.1f}% |"
        )


def run_combat_regime_sweep(
    module_library: Optional[List[AuthoredModule]] = None,
    chain_length: int = 6,
    n_samples: int = 10000,
    seed: int = 42
) -> List[RegimeSweepRow]:
    """Test robustness of metric discrimination across three distinct combat reaction regimes.
    
    Regimes:
    1. Slow / Forgiving:   t_acq = 0.25s, w_aim = 540 deg/s, due_mult = 1.40 (generous timing)
    2. Medium / Baseline:  t_acq = 0.15s, w_aim = 360 deg/s, due_mult = 1.00 (standard tactical)
    3. Fast / Punishing:   t_acq = 0.08s, w_aim = 240 deg/s, due_mult = 0.65 (tight reflex demand)
    """
    disc = AngularSectorDiscretization(num_sectors=PRODUCTION_NUM_SECTORS)
    rng = random.Random(seed)

    # Pre-generate sample indices across the 16 module slots
    chain_indices = [[rng.randrange(16) for _ in range(chain_length)] for _ in range(n_samples)]

    regimes = [
        ("Slow / Forgiving", PlayerModel(name="Slow", acquisition_latency_s=0.25, aim_velocity_deg_s=540.0), 1.40),
        ("Medium / Baseline", PlayerModel(name="Medium", acquisition_latency_s=0.15, aim_velocity_deg_s=360.0), 1.00),
        ("Fast / Punishing", PlayerModel(name="Fast", acquisition_latency_s=0.08, aim_velocity_deg_s=240.0), 0.65)
    ]

    rows = []
    for name, player, due_mult in regimes:
        # Build fresh scaled library for this regime
        regime_lib = build_authored_module_library(disc, due_window_multiplier=due_mult)

        pass_b = 0
        pass_c = 0
        a_b_not_c = 0
        a_not_b_c = 0

        for c_idxs in chain_indices:
            c_mods = [regime_lib[i] for i in c_idxs]
            assembly = ModuleAssembly(modules=c_mods)
            audit = audit_module_assembly(assembly, disc, player)

            if audit.audit_b_kici:
                pass_b += 1
            if audit.audit_c_transfer:
                pass_c += 1
            if audit.audit_a_topology and audit.audit_b_kici and not audit.audit_c_transfer:
                a_b_not_c += 1
            if audit.audit_a_topology and not audit.audit_b_kici and audit.audit_c_transfer:
                a_not_b_c += 1

        rows.append(RegimeSweepRow(
            regime_name=name,
            acquisition_latency_s=player.acquisition_latency_s,
            aim_angular_vel_deg_s=player.aim_velocity_deg_s,
            due_window_multiplier=due_mult,
            pass_b_rate_pct=(pass_b / n_samples) * 100.0,
            pass_c_rate_pct=(pass_c / n_samples) * 100.0,
            kici_blind_spot_rate_pct=(a_b_not_c / n_samples) * 100.0,
            kici_false_alarm_rate_pct=(a_not_b_c / n_samples) * 100.0
        ))

    return rows


def extract_counterexample_galleries(
    corpus_results: List[AssemblyAuditResult]
) -> Dict[str, List[AssemblyAuditResult]]:
    """Extract representative exemplars from critical metric discrimination sets."""
    galleries: Dict[str, List[AssemblyAuditResult]] = {
        "KICI_False_Positive": [],   # A and B and not C (Lethal crossfire trap missed by KICI)
        "KICI_False_Alarm": [],      # A and not B and C (Solvable layout falsely rejected by KICI)
        "All_Pass_Flank": [],        # A and B and C (Certified with flank routes)
        "All_Pass_Direct": []        # A and B and C (Certified with direct fast corridors)
    }

    for res in corpus_results:
        if res.audit_a_topology and res.audit_b_kici and not res.audit_c_transfer:
            if len(galleries["KICI_False_Positive"]) < 3:
                galleries["KICI_False_Positive"].append(res)
        elif res.audit_a_topology and not res.audit_b_kici and res.audit_c_transfer:
            if len(galleries["KICI_False_Alarm"]) < 3:
                galleries["KICI_False_Alarm"].append(res)
        elif res.audit_a_topology and res.audit_b_kici and res.audit_c_transfer:
            if res.route_redundancy > 0 and len(galleries["All_Pass_Flank"]) < 3:
                galleries["All_Pass_Flank"].append(res)
            elif res.route_redundancy == 0 and len(galleries["All_Pass_Direct"]) < 3:
                galleries["All_Pass_Direct"].append(res)

    return galleries

