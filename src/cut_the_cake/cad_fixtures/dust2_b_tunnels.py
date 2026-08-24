"""Metric Graybox Reconstruction: Counter-Strike Dust II Upper B-Tunnels to B-Site Exit.

Topological Mechanism: Multi-angle compressed choke-exit crossfire.
Independent Tactical Baseline: Counter-Strike tactical guides describe Upper B Tunnels as a severe
death-funnel on dry entry; exiting attackers confront simultaneous converging angles from Car,
B Platform/Closet, and Back Site.

Declared Model Expected Negative / Falsification Boundary: Because 2D geometry cannot serialize
these angles on dry entry without utility, both natural dry exit routes are predicted to suffer
immediate K_LOS >= 2 crossfire and critical suffix margin deficits (M_suffix <= 0) at the exit choke.
The model must refuse to fabricate false serialization.
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
    "map_name": "de_dust2",
    "section": "Upper B-Tunnels to B-Site Exit",
    "source_engine": "Valve Source / CS2 Overview Metadata",
    "scale_convention": "declared_hull_metric_approximation (1 Source unit = 0.01905 m)",
    "control_points": [
        {"name": "CP1_tunnel_choke_in",   "cad": [-6.0, 0.0], "description": "Upper Tunnel Inner Threshold"},
        {"name": "CP2_tunnel_exit_lip",   "cad": [0.0, 0.0],  "description": "Upper Tunnel Exit Threshold"},
        {"name": "CP3_b_car_corner",      "cad": [10.0, 5.0], "description": "B Car Cover Obstacle"},
        {"name": "CP4_b_platform_corner", "cad": [14.0, -4.0], "description": "B Platform / Closet Lip"},
        {"name": "CP5_b_site_box",        "cad": [20.0, 1.0], "description": "B Central Site Box"}
    ]
}


def get_dust2_b_tunnels_document() -> CADDocument:
    """Return metric CADDocument of Dust II Upper B-Tunnels exit engagement zone."""
    boundary = [
        [-8.0, -10.0],
        [28.0, -10.0],
        [28.0, 10.0],
        [-8.0, 10.0],
        [-8.0, -10.0]
    ]

    obstacles = [
        # Upper Tunnel North Wall (Left of choke)
        CADObstacle(
            id="obs_tunnel_north_wall",
            name="Tunnel North Wall",
            vertices=[[-8.0, 1.4], [0.0, 1.4], [0.0, 9.0], [-8.0, 9.0], [-8.0, 1.4]]
        ),
        # Upper Tunnel South Wall (Right of choke)
        CADObstacle(
            id="obs_tunnel_south_wall",
            name="Tunnel South Wall",
            vertices=[[-8.0, -9.0], [0.0, -9.0], [0.0, -1.4], [-8.0, -1.4], [-8.0, -9.0]]
        ),
        # B Car Obstacle (Left / North side)
        CADObstacle(
            id="obs_b_car",
            name="B Car Structure",
            vertices=[[10.0, 3.5], [13.0, 3.5], [13.0, 6.0], [10.0, 6.0], [10.0, 3.5]]
        ),
        # B Platform / Closet Wall (Right / South side)
        CADObstacle(
            id="obs_b_platform",
            name="B Platform Structure",
            vertices=[[14.0, -9.0], [22.0, -9.0], [22.0, -4.0], [14.0, -4.0], [14.0, -9.0]]
        ),
        # B Site Center Boxes
        CADObstacle(
            id="obs_b_site_box",
            name="B Site Box",
            vertices=[[20.0, 0.0], [23.0, 0.0], [23.0, 3.0], [20.0, 3.0], [20.0, 0.0]]
        )
    ]

    threats = [
        # Defender 1: B Car hold (holding tunnel exit from left)
        CADThreat(
            id="threat_car_hold",
            name="B Car Hold",
            polygon=[[11.3, 6.3], [11.7, 6.3], [11.7, 6.7], [11.3, 6.7], [11.3, 6.3]],
            anchor=[11.5, 6.5],
            due_window_s=0.45,
            service_duration_s=0.10
        ),
        # Defender 2: B Platform / Closet hold (holding tunnel exit from right)
        CADThreat(
            id="threat_closet_hold",
            name="B Platform / Closet Hold",
            polygon=[[14.8, -3.7], [15.2, -3.7], [15.2, -3.3], [14.8, -3.3], [14.8, -3.7]],
            anchor=[15.0, -3.5],
            due_window_s=0.45,
            service_duration_s=0.10
        ),
        # Defender 3: B Back Site hold (holding deep tunnel exit)
        CADThreat(
            id="threat_site_hold",
            name="B Back Site Hold",
            polygon=[[21.3, 3.3], [21.7, 3.3], [21.7, 3.7], [21.3, 3.7], [21.3, 3.3]],
            anchor=[21.5, 3.5],
            due_window_s=0.50,
            service_duration_s=0.10
        )
    ]

    routes = [
        # Route A (Blind ID): Exits tunnel hugging left toward Car
        CADRoute(
            id="route_A",
            name="Route A (Blinded)",
            waypoints=[[-6.0, 0.6], [0.0, 0.6], [4.0, 1.8], [9.0, 2.5], [16.0, 2.5]],
            v_move_mps=4.5
        ),
        # Route B (Blind ID): Exits tunnel swinging right toward Platform
        CADRoute(
            id="route_B",
            name="Route B (Blinded)",
            waypoints=[[-6.0, -0.6], [0.0, -0.6], [4.0, -1.8], [9.0, -2.5], [16.0, -2.5]],
            v_move_mps=4.5
        )
    ]

    ports = [
        CADPort(id="port_tunnel_in", segment=[[-6.0, -1.4], [-6.0, 1.4]], port_type="ENTRY"),
        CADPort(id="port_site_out", segment=[[16.0, -2.5], [16.0, 2.5]], port_type="EXIT")
    ]

    return CADDocument(
        document_id="dust2_b_tunnels",
        name="Dust II: Upper B-Tunnels to B-Site",
        description="Metric graybox reconstruction of Counter-Strike Dust II Upper B-Tunnels exit choke.",
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
