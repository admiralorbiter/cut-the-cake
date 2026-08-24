"""Metric Graybox Reconstruction: Valorant Ascent A-Main to A-Site / Wine Pocket.

Topological Mechanism: Off-angle isolation and narrow corridor entry choke.
Independent Tactical Baseline: Valorant tactical guides dictate clearing the deep Wine off-angle
pocket before committing across into A-Site; direct center rush exposes attackers to back-angle
crossfire from Wine + Generator.

Declared Model Boundary: Elevated positions (Heaven / Rafters) represent 3D verticality beyond
the frozen 2D model scope; the analyzed spatial encounter focuses on ground-level A-Main choke,
Wine pocket, and Generator hold angles.
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
    "map_name": "ascent",
    "section": "A-Main to A-Site / Wine Pocket",
    "source_engine": "Riot Games Valorant Overview Metadata",
    "scale_convention": "standard_metric (1 unit = 1 meter)",
    "control_points": [
        {"name": "CP1_amain_lobby_entry", "cad": [0.0, 0.0], "description": "A-Main Lobby Threshold"},
        {"name": "CP2_amain_choke_exit",  "cad": [14.0, 0.0], "description": "A-Main to Site Choke Threshold"},
        {"name": "CP3_wine_pocket_corner", "cad": [17.0, -5.0], "description": "Wine Off-Angle Corner"},
        {"name": "CP4_generator_edge",     "cad": [22.0, 1.0], "description": "A-Site Generator Corner"},
        {"name": "CP5_site_cross_edge",   "cad": [28.0, 0.0], "description": "A-Site Cross to Dice / Backsite"}
    ],
    "declared_model_boundary": "2D ground-plane encounter; Heaven/Rafters verticality excluded."
}


def get_ascent_a_main_document() -> CADDocument:
    """Return metric CADDocument of Valorant Ascent A-Main engagement zone."""
    boundary = [
        [-4.0, -10.0],
        [36.0, -10.0],
        [36.0, 10.0],
        [-4.0, 10.0],
        [-4.0, -10.0]
    ]

    obstacles = [
        # A-Main Left Corridor Wall (North)
        CADObstacle(
            id="obs_amain_north_wall",
            name="A-Main North Wall",
            vertices=[[-2.0, 2.0], [16.0, 2.0], [16.0, 9.0], [-2.0, 9.0], [-2.0, 2.0]]
        ),
        # A-Main Right Wall before Wine (South)
        CADObstacle(
            id="obs_amain_south_wall",
            name="A-Main South Wall",
            vertices=[[-2.0, -9.0], [12.0, -9.0], [12.0, -2.0], [-2.0, -2.0], [-2.0, -9.0]]
        ),
        # Wine Pocket Back Structure
        CADObstacle(
            id="obs_wine_structure",
            name="Wine Pocket Outer Structure",
            vertices=[[12.0, -9.0], [22.0, -9.0], [22.0, -2.0], [19.0, -2.0], [19.0, -7.0], [12.0, -7.0], [12.0, -9.0]]
        ),
        # A-Site Generator Cover Block
        CADObstacle(
            id="obs_generator_block",
            name="Generator Structure",
            vertices=[[22.0, 1.0], [26.0, 1.0], [26.0, 6.0], [22.0, 6.0], [22.0, 1.0]]
        )
    ]

    threats = [
        # Defender 1: Wine Off-Angle hold (deep right alcove)
        CADThreat(
            id="threat_wine_hold",
            name="Wine Off-Angle Hold",
            polygon=[[16.8, -5.2], [17.2, -5.2], [17.2, -4.8], [16.8, -4.8], [16.8, -5.2]],
            anchor=[17.0, -5.0],
            due_window_s=0.45,
            service_duration_s=0.10
        ),
        # Defender 2: Generator hold (holding A-Main choke exit)
        CADThreat(
            id="threat_gen_hold",
            name="Generator Site Hold",
            polygon=[[23.3, 0.3], [23.7, 0.3], [23.7, 0.7], [23.3, 0.7], [23.3, 0.3]],
            anchor=[23.5, 0.5],
            due_window_s=0.45,
            service_duration_s=0.10
        ),
        # Defender 3: Deep A-Site cross hold
        CADThreat(
            id="threat_site_deep",
            name="A-Site Deep Hold",
            polygon=[[31.8, -1.2], [32.2, -1.2], [32.2, -0.8], [31.8, -0.8], [31.8, -1.2]],
            anchor=[32.0, -1.0],
            due_window_s=0.60,
            service_duration_s=0.10
        )
    ]

    routes = [
        # Route A (Blind ID): Slices into Wine mouth first to isolate off-angle defender before advancing
        CADRoute(
            id="route_A",
            name="Route A (Blinded)",
            waypoints=[[0.0, 0.0], [8.0, 0.0], [12.0, 0.0], [14.5, -3.5], [16.5, -4.5], [17.5, -2.0], [20.0, 0.0], [28.0, 0.0]],
            v_move_mps=4.5
        ),
        # Route B (Blind ID): Direct center push straight down the choke line
        CADRoute(
            id="route_B",
            name="Route B (Blinded)",
            waypoints=[[0.0, 0.0], [8.0, 0.0], [16.0, 0.0], [22.0, 0.0], [28.0, 0.0]],
            v_move_mps=4.5
        )
    ]

    ports = [
        CADPort(id="port_amain_in", segment=[[0.0, -2.0], [0.0, 2.0]], port_type="ENTRY"),
        CADPort(id="port_site_out", segment=[[28.0, -2.0], [28.0, 2.0]], port_type="EXIT")
    ]

    return CADDocument(
        document_id="ascent_a_main",
        name="Valorant Ascent: A-Main to Wine",
        description="Metric graybox reconstruction of Valorant Ascent A-Main to A-Site / Wine pocket.",
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
