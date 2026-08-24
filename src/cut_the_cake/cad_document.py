"""Tactical CAD Working Document [CADDocument / cad_document_v1].

Authoring data model representing designer-authored level geometry, route definitions,
threat placement, and player parameters. Completely separated from calculated metrics.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from shapely.geometry import Polygon, LineString, Point

from .compiler import (
    GeometricModule,
    GeometricRoute,
    GeometricThreat,
    GeometricPort
)
from .vizdoom_engine import TicCombatParameters


def _round_coords(coords: List[List[float]]) -> List[List[float]]:
    return [[round(float(x), 4), round(float(y), 4)] for x, y in coords]


@dataclass
class CADObstacle:
    """Designer-authored obstacle with a stable string identifier."""
    id: str
    name: str
    vertices: List[List[float]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "vertices": _round_coords(self.vertices)
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CADObstacle:
        return cls(
            id=str(d["id"]),
            name=str(d.get("name", d["id"])),
            vertices=_round_coords(d["vertices"])
        )

    def to_polygon(self) -> Polygon:
        return Polygon(self.vertices)


@dataclass
class CADRoute:
    """Authored traversal polyline through level geometry."""
    id: str
    name: str
    waypoints: List[List[float]]
    v_move_mps: float = 4.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "waypoints": _round_coords(self.waypoints),
            "v_move_mps": float(self.v_move_mps)
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CADRoute:
        return cls(
            id=str(d["id"]),
            name=str(d.get("name", d["id"])),
            waypoints=_round_coords(d["waypoints"]),
            v_move_mps=float(d.get("v_move_mps", 4.5))
        )

    def to_geometric_route(self) -> GeometricRoute:
        return GeometricRoute(
            route_id=self.id,
            waypoints=[(float(x), float(y)) for x, y in self.waypoints],
            v_move_mps=float(self.v_move_mps)
        )


@dataclass
class CADThreat:
    """Authored hostile threat zone and firing anchor."""
    id: str
    name: str
    polygon: List[List[float]]
    anchor: List[float]
    due_window_s: float = 0.62
    service_duration_s: float = 0.1143

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "polygon": _round_coords(self.polygon),
            "anchor": [round(float(self.anchor[0]), 4), round(float(self.anchor[1]), 4)],
            "due_window_s": float(self.due_window_s),
            "service_duration_s": float(self.service_duration_s)
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CADThreat:
        return cls(
            id=str(d["id"]),
            name=str(d.get("name", d["id"])),
            polygon=_round_coords(d["polygon"]),
            anchor=[float(d["anchor"][0]), float(d["anchor"][1])],
            due_window_s=float(d.get("due_window_s", 0.62)),
            service_duration_s=float(d.get("service_duration_s", 0.1143))
        )

    def to_geometric_threat(self) -> GeometricThreat:
        return GeometricThreat(
            id=self.id,
            polygon=Polygon(self.polygon),
            threat_anchor=(float(self.anchor[0]), float(self.anchor[1])),
            authored_due_window_s=float(self.due_window_s),
            service_duration_s=float(self.service_duration_s),
            description=self.name
        )


@dataclass
class CADPort:
    """Boundary interface port."""
    id: str
    segment: List[List[float]]
    port_type: str = "ENTRY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "segment": _round_coords(self.segment),
            "port_type": self.port_type
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CADPort:
        return cls(
            id=str(d["id"]),
            segment=_round_coords(d["segment"]),
            port_type=str(d.get("port_type", "ENTRY"))
        )

    def to_geometric_port(self) -> GeometricPort:
        return GeometricPort(
            id=self.id,
            segment=LineString(self.segment),
            port_type=self.port_type
        )


@dataclass
class CADPlayerModel:
    """Tactical player combat and movement configuration."""
    v_move_mps: float = 4.5
    omega_slew_deg_per_s: float = 360.0
    acquisition_latency_s: float = 0.15
    service_duration_s: float = 0.10
    initial_reticle_deg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "v_move_mps": float(self.v_move_mps),
            "omega_slew_deg_per_s": float(self.omega_slew_deg_per_s),
            "acquisition_latency_s": float(self.acquisition_latency_s),
            "service_duration_s": float(self.service_duration_s),
            "initial_reticle_deg": float(self.initial_reticle_deg)
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CADPlayerModel:
        return cls(
            v_move_mps=float(d.get("v_move_mps", 4.5)),
            omega_slew_deg_per_s=float(d.get("omega_slew_deg_per_s", 360.0)),
            acquisition_latency_s=float(d.get("acquisition_latency_s", 0.15)),
            service_duration_s=float(d.get("service_duration_s", 0.10)),
            initial_reticle_deg=float(d.get("initial_reticle_deg", 0.0))
        )

    def to_combat_params(self) -> TicCombatParameters:
        return TicCombatParameters(
            v_move_mps=float(self.v_move_mps),
            aim_velocity_deg_s=float(self.omega_slew_deg_per_s),
            acquisition_latency_s=float(self.acquisition_latency_s),
            inspect_duration_s=float(self.service_duration_s)
        )


@dataclass
class CADDocument:
    """Tactical CAD Working Document (cad_document_v1).
    
    Contains only designer-authored geometry and parameters.
    Never stores calculated metrics, schedules, or engine evidence.
    """
    document_id: str
    name: str
    description: str = ""
    schema_version: str = "cad_document_v1"
    metadata: Dict[str, Any] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=lambda: {
        "coordinates": "meters",
        "angles": "degrees",
        "time": "seconds"
    })
    player_model: CADPlayerModel = field(default_factory=CADPlayerModel)
    boundary: List[List[float]] = field(default_factory=list)
    obstacles: List[CADObstacle] = field(default_factory=list)
    routes: List[CADRoute] = field(default_factory=list)
    threats: List[CADThreat] = field(default_factory=list)
    ports: List[CADPort] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "document_id": self.document_id,
            "name": self.name,
            "description": self.description,
            "metadata": dict(self.metadata),
            "units": dict(self.units),
            "player_model": self.player_model.to_dict(),
            "geometry": {
                "boundary": _round_coords(self.boundary),
                "obstacles": [obs.to_dict() for obs in self.obstacles],
                "routes": [r.to_dict() for r in self.routes],
                "threats": [t.to_dict() for t in self.threats],
                "ports": [p.to_dict() for p in self.ports]
            }
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CADDocument:
        geo = d.get("geometry", {})
        return cls(
            schema_version=d.get("schema_version", "cad_document_v1"),
            document_id=str(d["document_id"]),
            name=str(d.get("name", d["document_id"])),
            description=str(d.get("description", "")),
            metadata=dict(d.get("metadata", {})),
            units=dict(d.get("units", {"coordinates": "meters", "angles": "degrees", "time": "seconds"})),
            player_model=CADPlayerModel.from_dict(d.get("player_model", {})),
            boundary=_round_coords(geo.get("boundary", [])),
            obstacles=[CADObstacle.from_dict(obs) for obs in geo.get("obstacles", [])],
            routes=[CADRoute.from_dict(r) for r in geo.get("routes", [])],
            threats=[CADThreat.from_dict(t) for t in geo.get("threats", [])],
            ports=[CADPort.from_dict(p) for p in geo.get("ports", [])]
        )

    def to_geometric_module(self) -> GeometricModule:
        """Convert CADDocument to authoritative scientific GeometricModule."""
        return GeometricModule(
            module_id=self.document_id,
            name=self.name,
            boundary=Polygon(self.boundary),
            obstacles=[obs.to_polygon() for obs in self.obstacles],
            ports=[p.to_geometric_port() for p in self.ports],
            threats=[t.to_geometric_threat() for t in self.threats],
            routes=[r.to_geometric_route() for r in self.routes],
            description=self.description
        )

    @classmethod
    def from_geometric_module(
        cls,
        geo_mod: GeometricModule,
        document_id: Optional[str] = None,
        player_model: Optional[CADPlayerModel] = None
    ) -> CADDocument:
        """Construct a clean CADDocument from an existing GeometricModule."""
        b_coords = _round_coords(list(geo_mod.boundary.exterior.coords))
        
        cad_obs = []
        for idx, obs in enumerate(geo_mod.obstacles):
            cad_obs.append(CADObstacle(
                id=f"obs_{idx}",
                name=f"Obstacle #{idx}",
                vertices=_round_coords(list(obs.exterior.coords))
            ))

        cad_routes = []
        for idx, r in enumerate(geo_mod.routes):
            cad_routes.append(CADRoute(
                id=r.route_id,
                name=f"Route {r.route_id}",
                waypoints=_round_coords(list(r.waypoints)),
                v_move_mps=r.v_move_mps
            ))

        cad_threats = []
        for idx, t in enumerate(geo_mod.threats):
            cad_threats.append(CADThreat(
                id=t.id,
                name=f"Threat {idx + 1}",
                polygon=_round_coords(list(t.polygon.exterior.coords)),
                anchor=[float(t.threat_anchor[0]), float(t.threat_anchor[1])],
                due_window_s=t.authored_due_window_s,
                service_duration_s=t.service_duration_s
            ))

        cad_ports = []
        for p in geo_mod.ports:
            cad_ports.append(CADPort(
                id=p.id,
                segment=_round_coords(list(p.segment.coords)),
                port_type=p.port_type
            ))

        return cls(
            document_id=document_id or geo_mod.module_id,
            name=geo_mod.name or geo_mod.module_id,
            description=geo_mod.description,
            boundary=b_coords,
            obstacles=cad_obs,
            routes=cad_routes,
            threats=cad_threats,
            ports=cad_ports,
            player_model=player_model or CADPlayerModel()
        )

    def save_json(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: str) -> CADDocument:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


# =============================================================================
# BUILT-IN REFERENCE DOCUMENTS
# =============================================================================

def get_canonical_f1_document() -> CADDocument:
    """Canonical Family 1 Baffle Stagger arena (exact benchmark fixture parity)."""
    from .repair_benchmark import build_unserviceable_population
    f1_mod = build_unserviceable_population(n_per_family=1)[0]
    doc = CADDocument.from_geometric_module(
        geo_mod=f1_mod,
        document_id="canonical_f1_stagger",
        player_model=CADPlayerModel(
            v_move_mps=4.5,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0
        )
    )
    if doc.obstacles:
        doc.obstacles[0].id = "wall_0"
        doc.obstacles[0].name = "Central Baffle"
    return doc


def get_custom_asymmetric_corridor_document() -> CADDocument:
    """3-threat asymmetric corridor with 2 movable pillars and non-benchmark naming."""
    return CADDocument(
        document_id="custom_asymmetric_corridor",
        name="Custom Asymmetric Corridor (3 Threats)",
        description="Multi-obstacle urban corridor with 3 distinct threat vectors and 2 adjustable cover pillars.",
        metadata={
            "provenance": "M2B Custom Document",
            "author": "Level Design Studio"
        },
        player_model=CADPlayerModel(
            v_move_mps=4.5,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0
        ),
        boundary=[
            [0.0, -3.0],
            [12.0, -3.0],
            [12.0, 3.0],
            [0.0, 3.0],
            [0.0, -3.0]
        ],
        obstacles=[
            CADObstacle(
                id="pillar_alpha",
                name="Pillar Alpha (West)",
                vertices=[
                    [1.2, 0.4],
                    [1.6, 0.4],
                    [1.6, 2.2],
                    [1.2, 2.2],
                    [1.2, 0.4]
                ]
            ),
            CADObstacle(
                id="pillar_beta",
                name="Pillar Beta (East)",
                vertices=[
                    [4.0, -2.2],
                    [4.4, -2.2],
                    [4.4, -0.4],
                    [4.0, -0.4],
                    [4.0, -2.2]
                ]
            )
        ],
        routes=[
            CADRoute(
                id="route_incursion",
                name="Tactical Incursion Route",
                waypoints=[[0.0, 0.0], [6.0, 0.0], [12.0, 0.0]],
                v_move_mps=4.5
            )
        ],
        threats=[
            CADThreat(
                id="sniper_nest_north",
                name="Sniper Nest (North)",
                polygon=[[0.5, 1.8], [1.5, 1.8], [1.5, 2.8], [0.5, 2.8], [0.5, 1.8]],
                anchor=[1.0, 2.3],
                due_window_s=0.65,
                service_duration_s=0.1143
            ),
            CADThreat(
                id="flanker_alcove_south",
                name="Flanker Alcove (South)",
                polygon=[[3.0, -2.8], [4.0, -2.8], [4.0, -1.8], [3.0, -1.8], [3.0, -2.8]],
                anchor=[3.5, -2.3],
                due_window_s=0.65,
                service_duration_s=0.1143
            ),
            CADThreat(
                id="overwatch_bunker_east",
                name="Overwatch Bunker (East)",
                polygon=[[8.0, 1.5], [9.0, 1.5], [9.0, 2.8], [8.0, 2.8], [8.0, 1.5]],
                anchor=[8.5, 2.1],
                due_window_s=0.75,
                service_duration_s=0.1143
            )
        ],
        ports=[
            CADPort(id="port_west", segment=[[0.0, -0.8], [0.0, 0.8]], port_type="ENTRY"),
            CADPort(id="port_east", segment=[[12.0, -0.8], [12.0, 0.8]], port_type="EXIT")
        ]
    )
