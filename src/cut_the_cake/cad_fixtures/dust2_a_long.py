"""Calibrated Metric Graybox Reconstruction: Counter-Strike Dust II A-Long to A-Site / Pit Contest.

Authentic competitive tactical FPS engagement zone calibrated to metric scale (1 unit = 1 meter).
Demonstrates:
1. Multi-route tactical differentiation (Pieing / Angle Slice vs Wide Swing vs Pit Drop).
2. Acute crossfire vulnerability on wide open entry (Pit + Corner simultaneous line-of-sight).
3. Sightline isolation and angle serialization on left-wall pieing approach.
4. Defensive cover / pocket isolation inside Pit breaking A-Site Plat sightlines.
"""

from typing import List
from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPort,
    CADPlayerModel
)


def get_dust2_a_long_document() -> CADDocument:
    """Return calibrated metric CADDocument of Dust II A-Long engagement zone."""
    boundary = [
        [-4.0, -12.0],
        [42.0, -12.0],
        [42.0, 12.0],
        [-4.0, 12.0],
        [-4.0, -12.0]
    ]

    obstacles = [
        # Long Doors Left Wall (North of choke)
        CADObstacle(
            id="obs_doors_north_wall",
            name="Doors North Wall",
            vertices=[[-2.0, 1.2], [0.0, 1.2], [0.0, 12.0], [-2.0, 12.0], [-2.0, 1.2]]
        ),
        # Long Doors Right Wall (South of choke)
        CADObstacle(
            id="obs_doors_south_wall",
            name="Doors South Wall",
            vertices=[[-2.0, -12.0], [0.0, -12.0], [0.0, -1.2], [-2.0, -1.2], [-2.0, -12.0]]
        ),
        # Long Corner Building (Blue Container / Corner structure dividing Long from A-Site Cross)
        CADObstacle(
            id="obs_corner_building",
            name="Long Corner Structure",
            vertices=[[18.0, -12.0], [26.0, -12.0], [26.0, -0.2], [18.0, -0.2], [18.0, -12.0]]
        ),
        # Pit Lip / Side Wall (Divides Long lane from Pit depression)
        CADObstacle(
            id="obs_pit_wall",
            name="Pit Lip Wall",
            vertices=[[3.5, 2.0], [6.5, 2.0], [6.5, 3.5], [3.5, 3.5], [3.5, 2.0]]
        ),
        # A-Site Ramp / Plat Cover Box
        CADObstacle(
            id="obs_site_plat_box",
            name="A-Site Plat Box",
            vertices=[[34.0, -8.0], [37.0, -8.0], [37.0, -6.0], [34.0, -6.0], [34.0, -8.0]]
        )
    ]

    threats = [
        # Defender 1: Long Corner hold (holding edge of corner looking back at doors)
        CADThreat(
            id="threat_corner_hold",
            name="Long Corner Hold",
            polygon=[[18.3, 0.0], [18.7, 0.0], [18.7, 0.4], [18.3, 0.4], [18.3, 0.0]],
            anchor=[18.5, 0.2],
            due_window_s=0.45,
            service_duration_s=0.10
        ),
        # Defender 2: Pit hold (holding headshot angle out of Pit towards doors/corner)
        CADThreat(
            id="threat_pit_hold",
            name="Pit Headshot Hold",
            polygon=[[12.3, 5.8], [12.7, 5.8], [12.7, 6.2], [12.3, 6.2], [12.3, 5.8]],
            anchor=[12.5, 6.0],
            due_window_s=0.45,
            service_duration_s=0.10
        ),
        # Defender 3: A-Site Plat hold (holding down A-Long cross from site)
        CADThreat(
            id="threat_plat_hold",
            name="A-Site Plat Hold",
            polygon=[[33.8, -6.2], [34.2, -6.2], [34.2, -5.8], [33.8, -5.8], [33.8, -6.2]],
            anchor=[34.0, -6.0],
            due_window_s=0.60,
            service_duration_s=0.10
        )
    ]

    routes = [
        # 1. Pieing Route: Exits doors hugging left wall (y = 1.2), isolating Corner before Pit opens, then advancing to Site
        CADRoute(
            id="route_pieing",
            name="Pieing / Angle Slice Route",
            waypoints=[[0.0, 0.5], [4.0, 1.2], [16.0, 1.2], [24.0, 0.0], [28.0, -4.0]],
            v_move_mps=4.5
        ),
        # 2. Wide-Swing Route: Exits doors swinging wide right (y = -1.0), exposing to Corner + Pit crossfire simultaneously
        CADRoute(
            id="route_wide_swing",
            name="Wide Swing / Open Choke Route",
            waypoints=[[0.0, 0.0], [4.0, -1.0], [14.0, -1.0], [24.0, 0.0], [28.0, -4.0]],
            v_move_mps=4.5
        ),
        # 3. Pit Drop Route: Exits doors, drops directly into Pit (y = 5.5) to isolate Pit defender and break Site sightline
        CADRoute(
            id="route_pit_drop",
            name="Pit Drop Route",
            waypoints=[[0.0, 0.5], [4.0, 1.0], [8.0, 3.5], [12.0, 5.5]],
            v_move_mps=4.5
        )
    ]

    ports = [
        CADPort(id="port_doors_in", segment=[[0.0, -1.2], [0.0, 1.2]], port_type="ENTRY"),
        CADPort(id="port_cross_out", segment=[[26.0, -0.2], [26.0, -12.0]], port_type="EXIT")
    ]

    return CADDocument(
        document_id="dust2_a_long",
        name="Dust II: A-Long to A-Site / Pit",
        description="Calibrated metric graybox case study of Counter-Strike Dust II A-Long engagement zone.",
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
