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
    elevation_deg: float = 0.0
    z_m: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "name": self.name,
            "polygon": _round_coords(self.polygon),
            "anchor": [round(float(self.anchor[0]), 4), round(float(self.anchor[1]), 4)],
            "due_window_s": float(self.due_window_s),
            "service_duration_s": float(self.service_duration_s)
        }
        if self.elevation_deg != 0.0:
            d["elevation_deg"] = float(self.elevation_deg)
        if self.z_m is not None:
            d["z_m"] = float(self.z_m)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CADThreat:
        return cls(
            id=str(d["id"]),
            name=str(d.get("name", d["id"])),
            polygon=_round_coords(d["polygon"]),
            anchor=[float(d["anchor"][0]), float(d["anchor"][1])],
            due_window_s=float(d.get("due_window_s", 0.62)),
            service_duration_s=float(d.get("service_duration_s", 0.1143)),
            elevation_deg=float(d.get("elevation_deg", 0.0)),
            z_m=float(d["z_m"]) if "z_m" in d and d["z_m"] is not None else None
        )

    def to_geometric_threat(self) -> GeometricThreat:
        return GeometricThreat(
            id=self.id,
            polygon=Polygon(self.polygon),
            threat_anchor=(float(self.anchor[0]), float(self.anchor[1])),
            authored_due_window_s=float(self.due_window_s),
            service_duration_s=float(self.service_duration_s),
            description=self.name,
            elevation_deg=float(self.elevation_deg),
            z_m=self.z_m
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
    """Tactical player combat and movement configuration.
    
    Authority Semantics:
    - `v_move_mps`: Default player movement velocity. Overridden on a per-route basis by `CADRoute.v_move_mps`.
    - `service_duration_s`: Authoring default template for newly spawned threats. Runtime job service requirements are governed authoritatively on each threat via `CADThreat.service_duration_s`.
    - `omega_slew_deg_per_s`: Authoritative angular slewing rate in degrees per second.
    - `acquisition_latency_s`: Authoritative reaction latency upon threat reveal.
    - `initial_reticle_deg`: Starting reticle heading in degrees [0, 360).
    - `initial_reticle_elevation_deg`: Starting reticle elevation in degrees [-90, 90] (M6-A).
    - `eye_height_m`: Standard player eye height in meters (M6-A).
    """
    v_move_mps: float = 4.5
    omega_slew_deg_per_s: float = 360.0
    acquisition_latency_s: float = 0.15
    service_duration_s: float = 0.10
    initial_reticle_deg: float = 0.0
    initial_reticle_elevation_deg: float = 0.0
    eye_height_m: float = 1.65

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "v_move_mps": float(self.v_move_mps),
            "omega_slew_deg_per_s": float(self.omega_slew_deg_per_s),
            "acquisition_latency_s": float(self.acquisition_latency_s),
            "service_duration_s": float(self.service_duration_s),
            "initial_reticle_deg": float(self.initial_reticle_deg)
        }
        if self.initial_reticle_elevation_deg != 0.0:
            d["initial_reticle_elevation_deg"] = float(self.initial_reticle_elevation_deg)
        if self.eye_height_m != 1.65:
            d["eye_height_m"] = float(self.eye_height_m)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CADPlayerModel:
        return cls(
            v_move_mps=float(d.get("v_move_mps", 4.5)),
            omega_slew_deg_per_s=float(d.get("omega_slew_deg_per_s", 360.0)),
            acquisition_latency_s=float(d.get("acquisition_latency_s", 0.15)),
            service_duration_s=float(d.get("service_duration_s", 0.10)),
            initial_reticle_deg=float(d.get("initial_reticle_deg", 0.0)),
            initial_reticle_elevation_deg=float(d.get("initial_reticle_elevation_deg", 0.0)),
            eye_height_m=float(d.get("eye_height_m", 1.65))
        )

    def to_combat_params(self) -> TicCombatParameters:
        return TicCombatParameters(
            v_move_mps=float(self.v_move_mps),
            aim_velocity_deg_s=float(self.omega_slew_deg_per_s),
            acquisition_latency_s=float(self.acquisition_latency_s),
            inspect_duration_s=float(self.service_duration_s)
        )


def validate_cad_document(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Strictly validate a raw dictionary against the CADDocument authoring contract.
    
    Validation Rules:
    1. Schema conformance with cad_document_v1.schema.json (including additionalProperties: false).
    2. Version check (schema_version == "cad_document_v1").
    3. Unique string identifiers for obstacles, routes, threats, and ports.
    4. Non-degenerate boundary polygon (>= 3 points, positive area).
    5. Valid, non-degenerate obstacle polygons, fully contained within boundary.
    6. Valid threat polygons and anchors within boundary.
    7. Valid routes (>= 2 waypoints, positive total length).
    8. Finite positive numeric values for physical and combat parameters.
    
    Returns:
        (is_valid, error_messages)
    """
    import math
    errors: List[str] = []
    
    if not isinstance(data, dict):
        return False, ["Payload must be a JSON object / dictionary."]

    # 1. JSON Schema Validation (Strictly Fail-Closed)
    schema_path = os.path.join(os.path.dirname(__file__), "..", "..", "cad", "schema", "cad_document_v1.schema.json")
    if not os.path.exists(schema_path):
        return False, [f"CADDocument JSON schema definition not found at '{schema_path}'."]
    try:
        import sys
        # PySide6 six meta-path compatibility patch
        for imp in list(sys.meta_path):
            if imp.__class__.__name__ == "_SixMetaPathImporter" and not hasattr(imp, "_path"):
                imp._path = None
        import jsonschema
        with open(schema_path, "r", encoding="utf-8") as sf:
            schema_json = json.load(sf)
        validator = jsonschema.Draft7Validator(schema_json)
        for err in validator.iter_errors(data):
            field_path = ".".join(str(p) for p in err.path)
            errors.append(f"Schema error at '{field_path or 'root'}': {err.message}")
    except Exception as e:
        errors.append(f"Schema validator failure / dependency missing: {e}")

    if errors:
        return False, errors

    # 2. Schema version
    if data.get("schema_version") != "cad_document_v1":
        errors.append(f"Unsupported schema_version: '{data.get('schema_version')}'. Expected 'cad_document_v1'.")

    # 3. Parameter checks
    pm = data.get("player_model", {})
    v_move = pm.get("v_move_mps", 0)
    omega_slew = pm.get("omega_slew_deg_per_s", 0)
    if not math.isfinite(v_move) or v_move <= 0:
        errors.append("player_model.v_move_mps must be a positive finite number.")
    if not math.isfinite(omega_slew) or omega_slew <= 0:
        errors.append("player_model.omega_slew_deg_per_s must be a positive finite number.")

    geo = data.get("geometry", {})
    b_coords = geo.get("boundary", [])
    poly_b = None
    if len(b_coords) < 3:
        errors.append("Boundary must have at least 3 vertices.")
    else:
        for pt in b_coords:
            if len(pt) != 2 or not math.isfinite(pt[0]) or not math.isfinite(pt[1]):
                errors.append(f"Boundary vertex {pt} must contain finite coordinates.")
        try:
            poly_b = Polygon(b_coords)
            if not poly_b.is_valid or poly_b.area < 1e-4:
                errors.append("Boundary polygon is degenerate, self-intersecting, or zero-area.")
        except Exception as e:
            errors.append(f"Invalid boundary polygon: {e}")

    # 4. Uniqueness of IDs
    obs_list = geo.get("obstacles", [])
    obs_ids = [str(o.get("id")) for o in obs_list if "id" in o]
    if len(obs_ids) != len(set(obs_ids)):
        duplicates = [x for x in obs_ids if obs_ids.count(x) > 1]
        errors.append(f"Duplicate obstacle IDs found: {list(set(duplicates))}")

    route_list = geo.get("routes", [])
    route_ids = [str(r.get("id")) for r in route_list if "id" in r]
    if len(route_ids) != len(set(route_ids)):
        duplicates = [x for x in route_ids if route_ids.count(x) > 1]
        errors.append(f"Duplicate route IDs found: {list(set(duplicates))}")

    threat_list = geo.get("threats", [])
    threat_ids = [str(t.get("id")) for t in threat_list if "id" in t]
    if len(threat_ids) != len(set(threat_ids)):
        duplicates = [x for x in threat_ids if threat_ids.count(x) > 1]
        errors.append(f"Duplicate threat IDs found: {list(set(duplicates))}")

    port_list = geo.get("ports", [])
    port_ids = [str(p.get("id")) for p in port_list if "id" in p]
    if len(port_ids) != len(set(port_ids)):
        duplicates = [x for x in port_ids if port_ids.count(x) > 1]
        errors.append(f"Duplicate port IDs found: {list(set(duplicates))}")

    # 5. Geometric containment & validity
    for obs in obs_list:
        v = obs.get("vertices", [])
        if len(v) < 3:
            errors.append(f"Obstacle '{obs.get('id')}' has fewer than 3 vertices.")
            continue
        for pt in v:
            if len(pt) != 2 or not math.isfinite(pt[0]) or not math.isfinite(pt[1]):
                errors.append(f"Obstacle '{obs.get('id')}' contains non-finite coordinates.")
        try:
            poly_o = Polygon(v)
            if not poly_o.is_valid or poly_o.area < 1e-4:
                errors.append(f"Obstacle '{obs.get('id')}' is degenerate, self-intersecting, or zero-area.")
            elif poly_b is not None and poly_b.is_valid:
                if not poly_b.contains(poly_o) and not poly_b.covers(poly_o):
                    errors.append(f"Obstacle '{obs.get('id')}' extends outside or intersects boundary.")
        except Exception as e:
            errors.append(f"Obstacle '{obs.get('id')}' invalid geometry: {e}")

    for t in threat_list:
        v = t.get("polygon", [])
        if len(v) < 3:
            errors.append(f"Threat '{t.get('id')}' polygon has fewer than 3 vertices.")
        for pt in v:
            if len(pt) != 2 or not math.isfinite(pt[0]) or not math.isfinite(pt[1]):
                errors.append(f"Threat '{t.get('id')}' polygon contains non-finite coordinates.")
        try:
            poly_t = Polygon(v)
            if not poly_t.is_valid or poly_t.area < 1e-4:
                errors.append(f"Threat '{t.get('id')}' polygon is degenerate, self-intersecting, or zero-area.")
            elif poly_b is not None and poly_b.is_valid:
                if not poly_b.contains(poly_t) and not poly_b.covers(poly_t):
                    errors.append(f"Threat '{t.get('id')}' polygon extends outside boundary.")
        except Exception as e:
            errors.append(f"Threat '{t.get('id')}' invalid polygon: {e}")

        anchor = t.get("anchor", [])
        if len(anchor) == 2:
            if not math.isfinite(anchor[0]) or not math.isfinite(anchor[1]):
                errors.append(f"Threat '{t.get('id')}' anchor contains non-finite coordinates.")
            elif poly_b is not None and poly_b.is_valid:
                pt_a = Point(anchor[0], anchor[1])
                if not poly_b.contains(pt_a) and not poly_b.covers(pt_a):
                    errors.append(f"Threat '{t.get('id')}' anchor {anchor} is outside boundary.")
        else:
            errors.append(f"Threat '{t.get('id')}' anchor must be 2D [x, y].")

        due_win = t.get("due_window_s", 0)
        svc_dur = t.get("service_duration_s", 0)
        if not math.isfinite(due_win) or due_win <= 0:
            errors.append(f"Threat '{t.get('id')}' due_window_s must be positive and finite.")
        if not math.isfinite(svc_dur) or svc_dur <= 0:
            errors.append(f"Threat '{t.get('id')}' service_duration_s must be positive and finite.")

    for r in route_list:
        wps = r.get("waypoints", [])
        if len(wps) < 2:
            errors.append(f"Route '{r.get('id')}' must have at least 2 waypoints.")
            continue
        for pt in wps:
            if len(pt) != 2 or not math.isfinite(pt[0]) or not math.isfinite(pt[1]):
                errors.append(f"Route '{r.get('id')}' contains non-finite coordinates.")
        try:
            ls = LineString(wps)
            if ls.length < 1e-4:
                errors.append(f"Route '{r.get('id')}' has zero geometric length.")
        except Exception as e:
            errors.append(f"Route '{r.get('id')}' invalid waypoints: {e}")
        r_speed = r.get("v_move_mps", 0)
        if not math.isfinite(r_speed) or r_speed <= 0:
            errors.append(f"Route '{r.get('id')}' v_move_mps must be positive and finite.")

    for p in port_list:
        seg = p.get("segment", [])
        if len(seg) != 2:
            errors.append(f"Port '{p.get('id')}' segment must contain exactly 2 endpoints.")
            continue
        for pt in seg:
            if len(pt) != 2 or not math.isfinite(pt[0]) or not math.isfinite(pt[1]):
                errors.append(f"Port '{p.get('id')}' contains non-finite coordinates.")
        try:
            ls_p = LineString(seg)
            if ls_p.length < 1e-4:
                errors.append(f"Port '{p.get('id')}' segment has zero length.")
        except Exception as e:
            errors.append(f"Port '{p.get('id')}' invalid segment: {e}")

    return len(errors) == 0, errors


@dataclass
class CADDocument:
    """Tactical CAD Working Document (cad_document_v1).
    
    CADDocument is the canonical authoring representation. It contains strictly
    designer-authored geometry, route definitions, threat parameters, and player models.
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
    def from_dict(cls, d: Dict[str, Any], strict_validate: bool = False) -> CADDocument:
        if strict_validate:
            is_valid, errors = validate_cad_document(d)
            if not is_valid:
                raise ValueError(f"Invalid CADDocument payload: {'; '.join(errors)}")

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

    def compute_hash(self) -> str:
        """Compute stable SHA256 hex digest of document state for concurrency guarding."""
        import hashlib
        serialized = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    def to_geometric_module(self) -> GeometricModule:
        """Project CADDocument into an authoritative scientific GeometricModule.
        
        GeometricModule is a scientific analysis projection. Converting to GeometricModule
        drops authoring annotations and UI metadata not used in raycasting or scheduling.
        """
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
        """Construct a CADDocument from a GeometricModule analysis projection.
        
        Note: This is an analysis-to-authoring reconstruction. Stable obstacle IDs,
        human-readable display names, and document metadata will be generated with
        default placeholders unless overridden.
        """
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


def get_dust2_a_long_document() -> CADDocument:
    """Return calibrated metric graybox CADDocument of Counter-Strike Dust II A-Long (M5-A)."""
    from cut_the_cake.cad_fixtures.dust2_a_long import get_dust2_a_long_document as _get_dust2
    return _get_dust2()


def get_ascent_a_main_document() -> CADDocument:
    """Return metric graybox CADDocument of Valorant Ascent A-Main (M5-B)."""
    from cut_the_cake.cad_fixtures.ascent_a_main import get_ascent_a_main_document as _get_ascent
    return _get_ascent()


def get_dust2_b_tunnels_document() -> CADDocument:
    """Return metric graybox CADDocument of Dust II Upper B-Tunnels exit (M5-B)."""
    from cut_the_cake.cad_fixtures.dust2_b_tunnels import get_dust2_b_tunnels_document as _get_dust2_b
    return _get_dust2_b()


def get_transit_213_document() -> CADDocument:
    """Return metric graybox CADDocument of MW4 Transit 213 Center Lot (M5-B)."""
    from cut_the_cake.cad_fixtures.transit_213 import get_transit_213_document as _get_transit
    return _get_transit()


