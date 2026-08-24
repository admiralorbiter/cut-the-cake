"""Authored 2D Level Module Library for Procedural Generation (Round 8).

Defines 16 distinct authored modules spanning safe corridors, tactical flank rooms,
sniper alleys, high-concurrency crossfires, and adversarial sequencing traps.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import numpy as np

from .model import PlayerModel
from .contracts import (
    AngularSectorDiscretization,
    SpatialThreatJob,
    SpatialRoute,
    SpatialModuleTransferMap,
    ContinuousAngleTransferMap
)


@dataclass
class AuthoredModule:
    """Authored level module for PCG assembly."""
    module_id: str
    name: str
    category: str
    entry_port: str = "PORT_IN"
    exit_port: str = "PORT_OUT"
    entry_port_type: str = "STANDARD"
    exit_port_type: str = "STANDARD"
    routes: List[SpatialRoute] = field(default_factory=list)
    k_ici_max: int = 1
    is_quiescent: bool = False
    description: str = ""
    _transfer_maps: Dict[Tuple[int, float, float, float], SpatialModuleTransferMap] = field(default_factory=dict, repr=False)
    _matrices: Dict[Tuple[int, float, float, float], np.ndarray] = field(default_factory=dict, repr=False)

    def _cache_key(self, discretization: AngularSectorDiscretization, player: PlayerModel) -> Tuple[int, float, float, float]:
        return (discretization.num_sectors, round(player.acquisition_latency_s, 4), round(player.aim_velocity_deg_s, 2), round(player.inspect_duration_s, 4))

    def get_transfer_matrix(
        self,
        discretization: AngularSectorDiscretization,
        player: PlayerModel
    ) -> np.ndarray:
        """Get or build the compiled NumPy (K, K) duration matrix for ultra-fast min-plus composition."""
        key = self._cache_key(discretization, player)
        if key in self._matrices:
            return self._matrices[key]
        tmap = self.get_transfer_map(discretization, player)
        K = discretization.num_sectors
        mat = np.full((K, K), float('inf'))
        for a in range(K):
            for b in range(K):
                mat[a, b] = tmap.get_duration(a, b)
        self._matrices[key] = mat
        return mat

    def get_transfer_map(
        self,
        discretization: AngularSectorDiscretization,
        player: PlayerModel
    ) -> SpatialModuleTransferMap:
        """Get or build the compiled SpatialModuleTransferMap for this module."""
        key = self._cache_key(discretization, player)
        if key in self._transfer_maps:
            return self._transfer_maps[key]

        # Map sector assignments according to the given discretization
        mapped_routes = []
        for r in self.routes:
            mapped_jobs = [
                SpatialThreatJob(
                    id=j.id,
                    offset_s=j.offset_s,
                    due_window_s=j.due_window_s,
                    service_s=player.inspect_duration_s,
                    angle_deg=j.angle_deg,
                    sector=discretization.get_sector(j.angle_deg)
                )
                for j in r.jobs
            ]
            mapped_routes.append(
                SpatialRoute(
                    route_id=r.route_id,
                    traversal_duration_s=r.traversal_duration_s,
                    jobs=mapped_jobs
                )
            )

        tmap = SpatialModuleTransferMap(
            module_id=self.module_id,
            entry_port=self.entry_port,
            exit_port=self.exit_port,
            traversal_duration_s=mapped_routes[0].traversal_duration_s if mapped_routes else 1.0,
            discretization=discretization,
            player=player,
            routes=mapped_routes
        )
        self._transfer_maps[key] = tmap
        return tmap


def build_authored_module_library(
    disc: Optional[AngularSectorDiscretization] = None,
    due_window_multiplier: float = 1.0
) -> List[AuthoredModule]:
    """Construct the 16-module authored library using frozen tactical parameters under production K=8."""
    disc = disc or AngularSectorDiscretization(num_sectors=8)
    modules: List[AuthoredModule] = []

    # 1. Straight Corridor (Safe single forward threat)
    modules.append(AuthoredModule(
        module_id="M01_StraightCorridor",
        name="Straight Corridor",
        category="safe_corridor",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=False,
        description="Single forward threat at 0 deg with generous due window.",
        routes=[
            SpatialRoute("main", 1.0, [
                SpatialThreatJob("M01_T1", 0.3, 2.5, 0.20, 0.0, disc.get_sector(0.0))
            ])
        ]
    ))

    # 2. Baffled Reset Corridor (Quiescent portal with baffle)
    modules.append(AuthoredModule(
        module_id="M02_BaffledResetCorridor",
        name="Baffled Reset Corridor",
        category="quiescent",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=True,
        description="Quiescent entry reset pocket; 1 threat behind baffle.",
        routes=[
            SpatialRoute("main", 1.2, [
                SpatialThreatJob("M02_T1", 0.4, 2.5, 0.20, -30.0, disc.get_sector(-30.0))
            ])
        ]
    ))

    # 3. Pie Slice Left Sweep (Sequential L-to-C clearable)
    modules.append(AuthoredModule(
        module_id="M03_PieSliceLeftSweep",
        name="Pie Slice Left Sweep",
        category="pie_slice",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=False,
        description="Two sequential threats revealed left-to-center (-45 deg -> 0 deg).",
        routes=[
            SpatialRoute("main", 1.5, [
                SpatialThreatJob("M03_T1", 0.2, 2.0, 0.20, -45.0, disc.get_sector(-45.0)),
                SpatialThreatJob("M03_T2", 0.6, 2.0, 0.20, 0.0, disc.get_sector(0.0))
            ])
        ]
    ))

    # 4. Pie Slice Right Sweep (Sequential R-to-C clearable)
    modules.append(AuthoredModule(
        module_id="M04_PieSliceRightSweep",
        name="Pie Slice Right Sweep",
        category="pie_slice",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=False,
        description="Two sequential threats revealed right-to-center (+45 deg -> 0 deg).",
        routes=[
            SpatialRoute("main", 1.5, [
                SpatialThreatJob("M04_T1", 0.2, 2.0, 0.20, 45.0, disc.get_sector(45.0)),
                SpatialThreatJob("M04_T2", 0.6, 2.0, 0.20, 0.0, disc.get_sector(0.0))
            ])
        ]
    ))

    # 5. Staggered Dual Threat (Time-spaced swing)
    modules.append(AuthoredModule(
        module_id="M05_StaggeredDualThreat",
        name="Staggered Dual Threat",
        category="staggered",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=False,
        description="Two threats spaced in time (0.2s, 0.9s) at -60 deg and +60 deg.",
        routes=[
            SpatialRoute("main", 1.6, [
                SpatialThreatJob("M05_T1", 0.2, 2.0, 0.20, -60.0, disc.get_sector(-60.0)),
                SpatialThreatJob("M05_T2", 0.9, 2.0, 0.20, 60.0, disc.get_sector(60.0))
            ])
        ]
    ))

    # 6. Flank Bypass Room (Lethal central alley vs safe flank)
    modules.append(AuthoredModule(
        module_id="M06_FlankBypassRoom",
        name="Flank Bypass Room",
        category="flank_choice",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=2,
        is_quiescent=False,
        description="Death center corridor (lethal crossfire) vs safe perimeter flank.",
        routes=[
            SpatialRoute("center_death", 0.9, [
                SpatialThreatJob("M06_DA1", 0.1, 0.20, 0.20, -90.0, disc.get_sector(-90.0)),
                SpatialThreatJob("M06_DA2", 0.1, 0.20, 0.20, 90.0, disc.get_sector(90.0))
            ]),
            SpatialRoute("flank_safe", 1.8, [
                SpatialThreatJob("M06_FS1", 0.5, 2.0, 0.20, 0.0, disc.get_sector(0.0))
            ])
        ]
    ))

    # 7. Open Atrium Flank (Central open floor vs upper catwalk)
    modules.append(AuthoredModule(
        module_id="M07_OpenAtriumFlank",
        name="Open Atrium Flank",
        category="flank_choice",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=2,
        is_quiescent=False,
        description="Open floor (2 crossfire threats) vs elevated catwalk (1 isolated threat).",
        routes=[
            SpatialRoute("open_floor", 1.4, [
                SpatialThreatJob("M07_OF1", 0.2, 0.35, 0.20, -60.0, disc.get_sector(-60.0)),
                SpatialThreatJob("M07_OF2", 0.2, 0.35, 0.20, 60.0, disc.get_sector(60.0))
            ]),
            SpatialRoute("catwalk_flank", 2.0, [
                SpatialThreatJob("M07_CW1", 0.6, 2.2, 0.20, 15.0, disc.get_sector(15.0))
            ])
        ]
    ))

    # 8. Long Sniper Alley (Distant tight deadline)
    modules.append(AuthoredModule(
        module_id="M08_LongSniperAlley",
        name="Long Sniper Alley",
        category="sniper_lane",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=False,
        description="Single distant sniper aperture at 0 deg with 0.40s due window.",
        routes=[
            SpatialRoute("main", 2.2, [
                SpatialThreatJob("M08_T1", 0.5, 0.40, 0.20, 0.0, disc.get_sector(0.0))
            ])
        ]
    ))

    # 9. Staggered Triple Reveal (Smooth 3-threat arc)
    modules.append(AuthoredModule(
        module_id="M09_StaggeredTripleReveal",
        name="Staggered Triple Reveal",
        category="staggered",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=False,
        description="Three sequential threats revealed in a smooth arc (-90 -> 0 -> +90 deg).",
        routes=[
            SpatialRoute("main", 2.0, [
                SpatialThreatJob("M09_T1", 0.2, 2.0, 0.20, -90.0, disc.get_sector(-90.0)),
                SpatialThreatJob("M09_T2", 0.7, 2.0, 0.20, 0.0, disc.get_sector(0.0)),
                SpatialThreatJob("M09_T3", 1.2, 2.0, 0.20, 90.0, disc.get_sector(90.0))
            ])
        ]
    ))

    # 10. Alternating Zigzag Trap (K_ICI <= 2 PASS, Transfer FAIL)
    modules.append(AuthoredModule(
        module_id="M10_AlternatingZigzagTrap",
        name="Alternating Zigzag Trap",
        category="adversarial_trap",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=False,
        description="Rapid alternating L-R-L reveals (-75, +75, -75 deg) with impossible aim latency.",
        routes=[
            SpatialRoute("main", 1.5, [
                SpatialThreatJob("M10_T1", 0.1, 0.40, 0.20, -75.0, disc.get_sector(-75.0)),
                SpatialThreatJob("M10_T2", 0.2, 0.45, 0.20, 75.0, disc.get_sector(75.0)),
                SpatialThreatJob("M10_T3", 0.3, 0.50, 0.20, -75.0, disc.get_sector(-75.0)),
            ])
        ]
    ))

    # 11. Rapid Crossfire Aperture (K_ICI <= 2 PASS, Transfer FAIL)
    modules.append(AuthoredModule(
        module_id="M11_RapidCrossfireAperture",
        name="Rapid Crossfire Aperture",
        category="adversarial_trap",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=False,
        description="Two threats at -85 deg and +85 deg revealed 0.05s apart with 0.22s deadlines.",
        routes=[
            SpatialRoute("main", 1.2, [
                SpatialThreatJob("M11_T1", 0.10, 0.22, 0.20, -85.0, disc.get_sector(-85.0)),
                SpatialThreatJob("M11_T2", 0.15, 0.22, 0.20, 85.0, disc.get_sector(85.0))
            ])
        ]
    ))

    # 12. Triple Simultaneous Crossfire (K_ICI = 3 FAIL, Transfer FAIL)
    modules.append(AuthoredModule(
        module_id="M12_TripleSimultaneousCrossfire",
        name="Triple Simultaneous Crossfire",
        category="high_concurrency",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=3,
        is_quiescent=False,
        description="Three threats visible simultaneously with tight deadlines (K_ICI=3, Unsolvable).",
        routes=[
            SpatialRoute("main", 1.8, [
                SpatialThreatJob("M12_T1", 0.1, 0.30, 0.20, -90.0, disc.get_sector(-90.0)),
                SpatialThreatJob("M12_T2", 0.1, 0.30, 0.20, 0.0, disc.get_sector(0.0)),
                SpatialThreatJob("M12_T3", 0.1, 0.30, 0.20, 90.0, disc.get_sector(90.0))
            ])
        ]
    ))

    # 13. High Concurrency Solvable (K_ICI = 3 FAIL, Transfer PASS - False Alarm)
    modules.append(AuthoredModule(
        module_id="M13_HighConcurrencySolvable",
        name="High Concurrency Solvable",
        category="high_concurrency_solvable",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=3,
        is_quiescent=False,
        description="Three simultaneous sightlines (K_ICI=3) but with generous staggered deadlines (1.5s, 2.5s, 3.5s).",
        routes=[
            SpatialRoute("main", 2.0, [
                SpatialThreatJob("M13_T1", 0.1, 1.5, 0.20, -45.0, disc.get_sector(-45.0)),
                SpatialThreatJob("M13_T2", 0.1, 2.5, 0.20, 0.0, disc.get_sector(0.0)),
                SpatialThreatJob("M13_T3", 0.1, 3.5, 0.20, 45.0, disc.get_sector(45.0))
            ])
        ]
    ))

    # 14. Double Baffled Pillbox (Quiescent double chamber)
    modules.append(AuthoredModule(
        module_id="M14_DoubleBaffledPillbox",
        name="Double Baffled Pillbox",
        category="quiescent",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=True,
        description="Two baffled quiescent sub-chambers, each with 1 isolated threat.",
        routes=[
            SpatialRoute("main", 2.4, [
                SpatialThreatJob("M14_T1", 0.3, 2.5, 0.20, -45.0, disc.get_sector(-45.0)),
                SpatialThreatJob("M14_T2", 1.2, 2.5, 0.20, 45.0, disc.get_sector(45.0))
            ])
        ]
    ))

    # 15. Narrow Pinch Chokepoint (Fast pace corridor)
    modules.append(AuthoredModule(
        module_id="M15_NarrowPinchChokepoint",
        name="Narrow Pinch Chokepoint",
        category="safe_corridor",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=1,
        is_quiescent=False,
        description="Fast chokepoint corridor with 2 sequential forward threats (0 deg, 15 deg).",
        routes=[
            SpatialRoute("main", 1.0, [
                SpatialThreatJob("M15_T1", 0.2, 2.0, 0.20, 0.0, disc.get_sector(0.0)),
                SpatialThreatJob("M15_T2", 0.5, 2.0, 0.20, 15.0, disc.get_sector(15.0))
            ])
        ]
    ))

    # 16. Wide Angle Flank Arena (Frontal assault vs safe perimeter loop)
    modules.append(AuthoredModule(
        module_id="M16_WideAngleFlankArena",
        name="Wide Angle Flank Arena",
        category="flank_choice",
        entry_port="PORT_IN",
        exit_port="PORT_OUT",
        k_ici_max=2,
        is_quiescent=False,
        description="Frontal assault (2 crossfire threats) vs wide perimeter loop (0 threats, 3.0s).",
        routes=[
            SpatialRoute("frontal_assault", 1.2, [
                SpatialThreatJob("M16_FA1", 0.2, 0.35, 0.20, -80.0, disc.get_sector(-80.0)),
                SpatialThreatJob("M16_FA2", 0.2, 0.35, 0.20, 80.0, disc.get_sector(80.0))
            ]),
            SpatialRoute("perimeter_safe_loop", 3.0, [])
        ]
    ))
    if due_window_multiplier != 1.0:
        for m in modules:
            new_routes = []
            for r in m.routes:
                new_jobs = [
                    SpatialThreatJob(
                        id=j.id,
                        offset_s=j.offset_s,
                        due_window_s=j.due_window_s * due_window_multiplier,
                        service_s=j.service_s,
                        angle_deg=j.angle_deg,
                        sector=j.sector
                    )
                    for j in r.jobs
                ]
                new_routes.append(SpatialRoute(r.route_id, r.traversal_duration_s, new_jobs))
            m.routes = new_routes

    return modules


def audit_library_continuous_oracle(
    modules: List[AuthoredModule],
    player: PlayerModel,
    discretization: Optional[AngularSectorDiscretization] = None
) -> Dict[str, Dict[str, Any]]:
    """Exhaustively audit every module against both Discrete Sector (K=8) and Dense Continuous Angle (K=infinity) oracles.
    
    Evaluates continuous feasibility across a dense 2.0-degree continuous boundary grid (91 angles in [-90, +90] deg).
    """
    disc = discretization or AngularSectorDiscretization(num_sectors=8)
    report = {}
    dense_entry_angles = np.linspace(-90.0, 90.0, 91)

    for mod in modules:
        tmap = mod.get_transfer_map(disc, player)
        is_discrete_feas = tmap.is_feasible_from_any_reset_state()
        
        # Check continuous oracle across all candidate routes on dense boundary grid
        is_cont_feas = False
        min_cont_dur = float('inf')
        for r in mod.routes:
            # Map r.jobs with exact service_s = player.inspect_duration_s
            mapped_jobs = [
                SpatialThreatJob(
                    id=j.id,
                    offset_s=j.offset_s,
                    due_window_s=j.due_window_s,
                    service_s=player.inspect_duration_s,
                    angle_deg=j.angle_deg,
                    sector=disc.get_sector(j.angle_deg)
                )
                for j in r.jobs
            ]
            cont_map = ContinuousAngleTransferMap(
                traversal_duration_s=r.traversal_duration_s,
                jobs=mapped_jobs,
                player=player
            )
            # Evaluate across all dense entry angles (testing target exit angles)
            for angle_in in dense_entry_angles:
                target_exits = [float(angle_in)] + [j.angle_deg for j in r.jobs]
                for angle_out in target_exits:
                    dur = cont_map.evaluate_exact_continuous_duration(float(angle_in), float(angle_out))
                    if dur < float('inf'):
                        is_cont_feas = True
                        min_cont_dur = min(min_cont_dur, dur)

        # Check for false rejection (Discrete says infeasible, but Continuous is feasible)
        is_false_rejection = (not is_discrete_feas and is_cont_feas)
        # Check for unsoundness (Discrete says feasible, but Continuous is infeasible)
        is_unsound = (is_discrete_feas and not is_cont_feas)

        report[mod.module_id] = {
            "name": mod.name,
            "category": mod.category,
            "discrete_feasible": is_discrete_feas,
            "continuous_feasible": is_cont_feas,
            "false_rejection": is_false_rejection,
            "unsound_acceptance": is_unsound,
            "min_continuous_duration_s": min_cont_dur
        }

    return report


def build_precertified_library(
    modules: List[AuthoredModule],
    disc: Optional[AngularSectorDiscretization] = None,
    player: Optional[PlayerModel] = None
) -> List[AuthoredModule]:
    """Condition E: Precertified Library containing only locally deadline-feasible modules.
    
    Acts as a compile-time authoring linter: filters out locally infeasible modules upfront.
    Checks feasibility from any quiescent reset aim state.
    """
    disc = disc or AngularSectorDiscretization(num_sectors=8)
    player = player or PlayerModel()
    return [m for m in modules if m.get_transfer_map(disc, player).is_feasible_from_any_reset_state()]


def build_heldout_module_library(
    disc: Optional[AngularSectorDiscretization] = None,
    due_window_multiplier: float = 1.0
) -> List[AuthoredModule]:
    """Construct a held-out second library (Library 2) with 16 newly authored modules for generalization testing."""
    disc = disc or AngularSectorDiscretization(num_sectors=8)
    modules = []

    # H01: Curved Corridor (Gentle 30-deg curve, 1 threat, K_ICI=1, feasible)
    modules.append(AuthoredModule(
        module_id="H01_CurvedCorridor",
        name="Curved Corridor",
        category="safe_corridor",
        k_ici_max=1,
        is_quiescent=False,
        description="Gentle curve with 1 threat at 30 deg.",
        routes=[
            SpatialRoute("main", 1.1, [
                SpatialThreatJob("H01_T1", 0.3, 2.5, 0.20, 30.0, disc.get_sector(30.0))
            ])
        ]
    ))

    # H02: Baffled S-Chamber (Quiescent S-bend, 1 threat behind baffle, feasible)
    modules.append(AuthoredModule(
        module_id="H02_BaffledSChamber",
        name="Baffled S-Chamber",
        category="quiescent",
        k_ici_max=1,
        is_quiescent=True,
        description="S-bend entry reset pocket; 1 threat behind corner.",
        routes=[
            SpatialRoute("main", 1.4, [
                SpatialThreatJob("H02_T1", 0.5, 2.5, 0.20, -45.0, disc.get_sector(-45.0))
            ])
        ]
    ))

    # H03: T-Intersection Split (Dual route choice, feasible)
    modules.append(AuthoredModule(
        module_id="H03_TIntersectionSplit",
        name="T-Intersection Split",
        category="flank_choice",
        k_ici_max=1,
        is_quiescent=False,
        description="Left branch vs right branch around central pillar.",
        routes=[
            SpatialRoute("left_branch", 1.3, [
                SpatialThreatJob("H03_L1", 0.3, 2.0, 0.20, -45.0, disc.get_sector(-45.0))
            ]),
            SpatialRoute("right_branch", 1.3, [
                SpatialThreatJob("H03_R1", 0.3, 2.0, 0.20, 45.0, disc.get_sector(45.0))
            ])
        ]
    ))

    # H04: Elevated Overlook (High ground single threat, feasible)
    modules.append(AuthoredModule(
        module_id="H04_ElevatedOverlook",
        name="Elevated Overlook",
        category="sniper_lane",
        k_ici_max=1,
        is_quiescent=False,
        description="Single elevated sniper threat at 0 deg with 0.50s due window.",
        routes=[
            SpatialRoute("main", 1.8, [
                SpatialThreatJob("H04_T1", 0.4, 0.50, 0.20, 0.0, disc.get_sector(0.0))
            ])
        ]
    ))

    # H05: Asymmetric Pincer (Two staggered threats at -30 deg, +80 deg, feasible)
    modules.append(AuthoredModule(
        module_id="H05_AsymmetricPincer",
        name="Asymmetric Pincer",
        category="staggered",
        k_ici_max=1,
        is_quiescent=False,
        description="Two threats spaced in time (0.2s, 1.0s) at -30 deg and +80 deg.",
        routes=[
            SpatialRoute("main", 1.7, [
                SpatialThreatJob("H05_T1", 0.2, 2.2, 0.20, -30.0, disc.get_sector(-30.0)),
                SpatialThreatJob("H05_T2", 1.0, 2.2, 0.20, 80.0, disc.get_sector(80.0))
            ])
        ]
    ))

    # H06: Double Window Killzone (Lethal center vs safe perimeter, feasible via flank)
    modules.append(AuthoredModule(
        module_id="H06_DoubleWindowKillzone",
        name="Double Window Killzone",
        category="flank_choice",
        k_ici_max=2,
        is_quiescent=False,
        description="Direct window lane (2 crossfire threats) vs covered basement flank.",
        routes=[
            SpatialRoute("direct_window", 1.0, [
                SpatialThreatJob("H06_W1", 0.1, 0.22, 0.20, -70.0, disc.get_sector(-70.0)),
                SpatialThreatJob("H06_W2", 0.1, 0.22, 0.20, 70.0, disc.get_sector(70.0))
            ]),
            SpatialRoute("basement_flank", 2.2, [
                SpatialThreatJob("H06_BF1", 0.6, 2.5, 0.20, 0.0, disc.get_sector(0.0))
            ])
        ]
    ))

    # H07: Deep Recess Flank (Wide flank around center, feasible)
    modules.append(AuthoredModule(
        module_id="H07_DeepRecessFlank",
        name="Deep Recess Flank",
        category="flank_choice",
        k_ici_max=1,
        is_quiescent=False,
        description="Central lane vs deep outer flank.",
        routes=[
            SpatialRoute("direct_lane", 1.5, [
                SpatialThreatJob("H07_DL1", 0.3, 0.40, 0.20, 0.0, disc.get_sector(0.0))
            ]),
            SpatialRoute("outer_flank", 2.5, [])
        ]
    ))

    # H08: Corner Blind Trap (Model-infeasible trap: K_ICI <= 2 PASS, Transfer FAIL)
    modules.append(AuthoredModule(
        module_id="H08_CornerBlindTrap",
        name="Corner Blind Trap",
        category="adversarial_trap",
        k_ici_max=1,
        is_quiescent=False,
        description="Two rapid corner threats revealed 0.04s apart (-80 -> +80 deg) with impossible due dates.",
        routes=[
            SpatialRoute("main", 1.2, [
                SpatialThreatJob("H08_T1", 0.05, 0.20, 0.20, -80.0, disc.get_sector(-80.0)),
                SpatialThreatJob("H08_T2", 0.09, 0.20, 0.20, 80.0, disc.get_sector(80.0))
            ])
        ]
    ))

    # H09: Quad Aperture Staggered (4 sequential threats in smooth sweep, feasible)
    modules.append(AuthoredModule(
        module_id="H09_QuadApertureStaggered",
        name="Quad Aperture Staggered",
        category="staggered",
        k_ici_max=1,
        is_quiescent=False,
        description="Four sequential threats revealed in a sweeping arc (-60, -20, +20, +60 deg).",
        routes=[
            SpatialRoute("main", 2.4, [
                SpatialThreatJob("H09_T1", 0.2, 2.0, 0.20, -60.0, disc.get_sector(-60.0)),
                SpatialThreatJob("H09_T2", 0.7, 2.0, 0.20, -20.0, disc.get_sector(-20.0)),
                SpatialThreatJob("H09_T3", 1.2, 2.0, 0.20, 20.0, disc.get_sector(20.0)),
                SpatialThreatJob("H09_T4", 1.7, 2.0, 0.20, 60.0, disc.get_sector(60.0))
            ])
        ]
    ))

    # H10: Alternating Pinball (Model-infeasible trap: K_ICI <= 2 PASS, Transfer FAIL)
    modules.append(AuthoredModule(
        module_id="H10_AlternatingPinball",
        name="Alternating Pinball",
        category="adversarial_trap",
        k_ici_max=1,
        is_quiescent=False,
        description="Rapid 3-threat alternating L-R-L sequence with tight deadlines.",
        routes=[
            SpatialRoute("main", 1.6, [
                SpatialThreatJob("H10_T1", 0.1, 0.38, 0.20, -85.0, disc.get_sector(-85.0)),
                SpatialThreatJob("H10_T2", 0.2, 0.42, 0.20, 85.0, disc.get_sector(85.0)),
                SpatialThreatJob("H10_T3", 0.3, 0.46, 0.20, -85.0, disc.get_sector(-85.0))
            ])
        ]
    ))

    # H11: Dense Crossfire Solvable (K_ICI = 4 FAIL, Transfer PASS - False Alarm!)
    modules.append(AuthoredModule(
        module_id="H11_DenseCrossfireSolvable",
        name="Dense Crossfire Solvable",
        category="high_concurrency_solvable",
        k_ici_max=4,
        is_quiescent=False,
        description="Four simultaneous sightlines (K_ICI=4) with generous staggered due dates (1.8s to 4.0s).",
        routes=[
            SpatialRoute("main", 2.2, [
                SpatialThreatJob("H11_T1", 0.1, 1.8, 0.20, -60.0, disc.get_sector(-60.0)),
                SpatialThreatJob("H11_T2", 0.1, 2.5, 0.20, -15.0, disc.get_sector(-15.0)),
                SpatialThreatJob("H11_T3", 0.1, 3.2, 0.20, 15.0, disc.get_sector(15.0)),
                SpatialThreatJob("H11_T4", 0.1, 4.0, 0.20, 60.0, disc.get_sector(60.0))
            ])
        ]
    ))

    # H12: Simultaneous Quad Crossfire (K_ICI = 4 FAIL, Transfer FAIL)
    modules.append(AuthoredModule(
        module_id="H12_SimultaneousQuadCrossfire",
        name="Simultaneous Quad Crossfire",
        category="high_concurrency",
        k_ici_max=4,
        is_quiescent=False,
        description="Four simultaneous sightlines with impossible 0.25s due dates.",
        routes=[
            SpatialRoute("main", 2.0, [
                SpatialThreatJob("H12_T1", 0.1, 0.25, 0.20, -90.0, disc.get_sector(-90.0)),
                SpatialThreatJob("H12_T2", 0.1, 0.25, 0.20, -30.0, disc.get_sector(-30.0)),
                SpatialThreatJob("H12_T3", 0.1, 0.25, 0.20, 30.0, disc.get_sector(30.0)),
                SpatialThreatJob("H12_T4", 0.1, 0.25, 0.20, 90.0, disc.get_sector(90.0))
            ])
        ]
    ))

    # H13: Baffled Depot (Quiescent freight depot, feasible)
    modules.append(AuthoredModule(
        module_id="H13_BaffledDepot",
        name="Baffled Depot",
        category="quiescent",
        k_ici_max=1,
        is_quiescent=True,
        description="Two baffled freight rooms, each with 1 threat.",
        routes=[
            SpatialRoute("main", 2.0, [
                SpatialThreatJob("H13_T1", 0.4, 2.5, 0.20, -30.0, disc.get_sector(-30.0)),
                SpatialThreatJob("H13_T2", 1.2, 2.5, 0.20, 30.0, disc.get_sector(30.0))
            ])
        ]
    ))

    # H14: Triple Pillar Arena (Dual route: pillar cover vs open hall, feasible)
    modules.append(AuthoredModule(
        module_id="H14_TriplePillarArena",
        name="Triple Pillar Arena",
        category="flank_choice",
        k_ici_max=2,
        is_quiescent=False,
        description="Open center (2 crossfire threats) vs pillar-to-pillar safe flank.",
        routes=[
            SpatialRoute("open_center", 1.2, [
                SpatialThreatJob("H14_OC1", 0.1, 0.30, 0.20, -75.0, disc.get_sector(-75.0)),
                SpatialThreatJob("H14_OC2", 0.1, 0.30, 0.20, 75.0, disc.get_sector(75.0))
            ]),
            SpatialRoute("pillar_flank", 2.0, [
                SpatialThreatJob("H14_PF1", 0.5, 2.5, 0.20, 0.0, disc.get_sector(0.0))
            ])
        ]
    ))

    # H15: Fast Bypass Tunnel (Fast corridor with 1 forward threat, feasible)
    modules.append(AuthoredModule(
        module_id="H15_FastBypassTunnel",
        name="Fast Bypass Tunnel",
        category="safe_corridor",
        k_ici_max=1,
        is_quiescent=False,
        description="Fast tunnel with 1 forward threat at 0 deg.",
        routes=[
            SpatialRoute("main", 0.9, [
                SpatialThreatJob("H15_T1", 0.2, 2.2, 0.20, 0.0, disc.get_sector(0.0))
            ])
        ]
    ))

    # H16: Multi-Level Ramp (Dual route: ramp bypass vs low floor, feasible)
    modules.append(AuthoredModule(
        module_id="H16_MultiLevelRamp",
        name="Multi-Level Ramp",
        category="flank_choice",
        k_ici_max=2,
        is_quiescent=False,
        description="Low floor (2 threats) vs upper service ramp (0 threats, 2.8s).",
        routes=[
            SpatialRoute("low_floor", 1.3, [
                SpatialThreatJob("H16_LF1", 0.2, 0.32, 0.20, -85.0, disc.get_sector(-85.0)),
                SpatialThreatJob("H16_LF2", 0.2, 0.32, 0.20, 85.0, disc.get_sector(85.0))
            ]),
            SpatialRoute("upper_ramp", 2.8, [])
        ]
    ))
    if due_window_multiplier != 1.0:
        for m in modules:
            new_routes = []
            for r in m.routes:
                new_jobs = [
                    SpatialThreatJob(
                        id=j.id,
                        offset_s=j.offset_s,
                        due_window_s=j.due_window_s * due_window_multiplier,
                        service_s=j.service_s,
                        angle_deg=j.angle_deg,
                        sector=j.sector
                    )
                    for j in r.jobs
                ]
                new_routes.append(SpatialRoute(r.route_id, r.traversal_duration_s, new_jobs))
            m.routes = new_routes

    return modules

