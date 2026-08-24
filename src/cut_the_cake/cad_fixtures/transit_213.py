"""Metric Graybox Reconstruction: Modern Warfare 4 Transit 213 Center Lot / Rusting Buses.

Topological Mechanism: Multi-vehicle occluder lattice vs open parking lot exposure.
Independent Tactical Baseline: Infinity Ward official map descriptions emphasize that rusting
bus hulls divide the parking lot into tight concealed movement corridors; players crossing the
open central asphalt lot are severely exposed to long sightlines from perimeter depot and sheds.
"""

from typing import Dict, Any
from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPort,
    CADPlayerModel
)

CALIBRATION_METADATA: Dict[str, Any] = {
    "map_name": "transit_213",
    "section": "Center Parking Lot / Rusting Buses",
    "source_engine": "Infinity Ward MW4 Beta Map Overview",
    "scale_convention": "standard_metric (1 unit = 1 meter)",
    "control_points": [
        {"name": "CP1_west_entry_gate", "cad": [0.0, 0.0],  "description": "West Lot Entry Gate"},
        {"name": "CP2_north_bus_corner", "cad": [6.0, 4.0], "description": "Bus A (North) Front Corner"},
        {"name": "CP3_center_bus_corner", "cad": [10.0, -1.0], "description": "Bus B (Center) Front Corner"},
        {"name": "CP4_south_bus_corner", "cad": [14.0, -6.0], "description": "Bus C (South) Front Corner"},
        {"name": "CP5_east_depot_gate",  "cad": [26.0, 0.0], "description": "East Depot Exit Gate"}
    ]
}


def get_transit_213_document() -> CADDocument:
    """Return metric CADDocument of Transit 213 Center Lot engagement zone."""
    boundary = [
        [-4.0, -12.0],
        [32.0, -12.0],
        [32.0, 12.0],
        [-4.0, 12.0],
        [-4.0, -12.0]
    ]

    obstacles = [
        # Bus A (North Bus Hull: 10m x 2.6m)
        CADObstacle(
            id="obs_bus_north",
            name="Bus A (North Hull)",
            vertices=[[6.0, 3.5], [16.0, 3.5], [16.0, 6.0], [6.0, 6.0], [6.0, 3.5]]
        ),
        # Bus B (Center Bus Hull: 10m x 2.6m)
        CADObstacle(
            id="obs_bus_center",
            name="Bus B (Center Hull)",
            vertices=[[10.0, -2.5], [20.0, -2.5], [20.0, 0.0], [10.0, 0.0], [10.0, -2.5]]
        ),
        # Bus C (South Bus Hull: 10m x 2.6m)
        CADObstacle(
            id="obs_bus_south",
            name="Bus C (South Hull)",
            vertices=[[14.0, -8.5], [24.0, -8.5], [24.0, -6.0], [14.0, -6.0], [14.0, -8.5]]
        )
    ]

    threats = [
        # Defender 1: Depot Roof hold (holding long north lot lane)
        CADThreat(
            id="threat_depot_roof",
            name="Depot Perimeter Hold",
            polygon=[[27.8, 7.8], [28.2, 7.8], [28.2, 8.2], [27.8, 8.2], [27.8, 7.8]],
            anchor=[28.0, 8.0],
            due_window_s=0.50,
            service_duration_s=0.10
        ),
        # Defender 2: Center Shed hold (holding open central lot)
        CADThreat(
            id="threat_center_shed",
            name="Center Shed Hold",
            polygon=[[27.8, -1.2], [28.2, -1.2], [28.2, -0.8], [27.8, -0.8], [27.8, -1.2]],
            anchor=[28.0, -1.0],
            due_window_s=0.45,
            service_duration_s=0.10
        ),
        # Defender 3: South Depot hold (holding south perimeter lane)
        CADThreat(
            id="threat_south_depot",
            name="South Depot Hold",
            polygon=[[27.8, -8.2], [28.2, -8.2], [28.2, -7.8], [27.8, -7.8], [27.8, -8.2]],
            anchor=[28.0, -8.0],
            due_window_s=0.50,
            service_duration_s=0.10
        )
    ]

    routes = [
        # Route A (Blind ID): Weaves through bus lattice corridor using bus hulls for intermittent sightline cover
        CADRoute(
            id="route_A",
            name="Route A (Blinded)",
            waypoints=[[0.0, 1.8], [6.0, 1.8], [8.0, -4.5], [14.0, -4.5], [21.5, -4.5], [21.5, 1.8], [26.0, 1.8]],
            v_move_mps=4.5
        ),
        # Route B (Blind ID): Direct open push straight down the open north lot lane with zero cover
        CADRoute(
            id="route_B",
            name="Route B (Blinded)",
            waypoints=[[0.0, 8.0], [8.0, 8.0], [16.0, 8.0], [22.0, 8.0], [26.0, 8.0]],
            v_move_mps=4.5
        )
    ]

    ports = [
        CADPort(id="port_west_in", segment=[[0.0, -10.0], [0.0, 10.0]], port_type="ENTRY"),
        CADPort(id="port_east_out", segment=[[26.0, -10.0], [26.0, 10.0]], port_type="EXIT")
    ]

    return CADDocument(
        document_id="transit_213",
        name="Transit 213: Center Lot",
        description="Metric graybox reconstruction of Modern Warfare 4 Transit 213 Center Lot.",
        schema_version="cad_document_v1",
        boundary=boundary,
        obstacles=obstacles,
        routes=routes,
        threats=threats,
        ports=ports,
        player_model=CADPlayerModel(
            v_move_mps=4.5,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0
        )
    )
