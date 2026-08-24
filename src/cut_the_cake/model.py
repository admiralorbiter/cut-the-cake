"""Core data structures and types for FPS Tactical Clearability Validator."""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import numpy as np
from shapely.geometry import Polygon, LineString, Point


class InformationRegime(str, Enum):
    """Epistemic assumption on when threat orientation becomes actionable [P + C]."""
    REVEAL_GATED = "REVEAL_GATED"   # Blind clearance: threat bearing is unknown until visual reveal (a_j = r_j)
    PRE_AIM = "PRE_AIM"             # Known aperture: threat bearing is known in advance; pre-aiming allowed (a_j = 0)



@dataclass(frozen=True)
class ThreatRegion:
    """Persistent world-space potential threat position [G]."""
    id: str
    polygon: Polygon
    label: str = ""
    elevation_class: str = "GROUND"  # GROUND, MID, HIGH
    elevation_m: float = 0.0

    @property
    def centroid(self) -> Tuple[float, float]:
        c = self.polygon.centroid
        return (c.x, c.y)


@dataclass(frozen=True)
class Port:
    """Boundary interface port on a module [G]."""
    id: str
    segment: LineString  # 2D line segment on module boundary
    normal: Tuple[float, float] = (1.0, 0.0)  # Outward normal vector
    max_depth: float = 20.0
    max_external_budget: int = 1
    allowed_cone_deg: float = 120.0  # Total angular spread allowed


@dataclass
class Module:
    """Authored spatial module with local geometry and declared ports [G]."""
    id: str
    boundary: Polygon
    obstacles: List[Polygon] = field(default_factory=list)
    threats: List[ThreatRegion] = field(default_factory=list)
    ports: List[Port] = field(default_factory=list)


@dataclass
class World:
    """Complete 2D environment containing obstacles, threats, and bounds [G]."""
    bounds: Tuple[float, float, float, float]  # min_x, min_y, max_x, max_y
    obstacles: List[Polygon] = field(default_factory=list)
    threats: List[ThreatRegion] = field(default_factory=list)
    modules: List[Module] = field(default_factory=list)


@dataclass(frozen=True)
class CombatModel:
    """Game rules, weapon lethality, and timing deadlines [C]."""
    name: str = "Standard"
    base_ttk_s: float = 0.25  # Time to kill once firing begins
    opp_reaction_s: float = 0.20  # Opponent reaction latency
    player_speed_mps: float = 4.5  # Movement speed in meters/second
    vis_threshold: float = 0.10  # Minimum visible fraction for detection

    def damage_deadline(self, range_m: float = 10.0) -> float:
        """Total duration before uninspected threat inflicts lethal damage."""
        return self.opp_reaction_s + self.base_ttk_s


@dataclass(frozen=True)
class PlayerModel:
    """Human perceptual, aiming, and reaction capabilities [P]."""
    name: str = "Standard"
    reaction_latency_s: float = 0.20
    acquisition_latency_s: float = 0.15
    aim_velocity_deg_s: float = 360.0  # Effective angular sweeping velocity
    inspect_duration_s: float = 0.10  # Duration focus must linger to clear threat

    def service_cost_s(self, angle_diff_deg: float) -> float:
        """Duration to swing aim and acquire a target at angular displacement."""
        return self.acquisition_latency_s + (abs(angle_diff_deg) / max(self.aim_velocity_deg_s, 1e-3))


@dataclass(frozen=True)
class ThreatView:
    """View-dependent observation of a threat region from eye position p [G]."""
    threat_id: str
    visible_fraction: float
    min_angle_deg: float
    max_angle_deg: float
    centroid_angle_deg: float
    min_distance_m: float
    elevation_deg: float = 0.0


@dataclass
class PlayerState:
    """Dynamic state of a player traversing a path [G + C + P]."""
    pos: Tuple[float, float]
    path_s: float
    time_s: float
    aim_angle_deg: float
    cleared_threat_ids: set[str] = field(default_factory=set)
