"""Threat Incompatibility Graphs and static concurrency metrics [G + C + P]."""

from __future__ import annotations
import math
from typing import List, Tuple, Dict, Set
import networkx as nx
import numpy as np

from .model import ThreatView, CombatModel, PlayerModel
from .geometry import angle_diff_deg


def angular_3d_separation_deg(t1: ThreatView, t2: ThreatView) -> float:
    """Compute true angular separation between two threat view vectors with elevation."""
    yaw1_rad = math.radians(t1.centroid_angle_deg)
    pitch1_rad = math.radians(t1.elevation_deg)
    yaw2_rad = math.radians(t2.centroid_angle_deg)
    pitch2_rad = math.radians(t2.elevation_deg)

    # Unit vectors
    v1 = np.array([
        math.cos(pitch1_rad) * math.cos(yaw1_rad),
        math.cos(pitch1_rad) * math.sin(yaw1_rad),
        math.sin(pitch1_rad)
    ])
    v2 = np.array([
        math.cos(pitch2_rad) * math.cos(yaw2_rad),
        math.cos(pitch2_rad) * math.sin(yaw2_rad),
        math.sin(pitch2_rad)
    ])
    
    cos_sim = np.clip(np.dot(v1, v2), -1.0, 1.0)
    return math.degrees(math.acos(cos_sim))


def build_threat_incompatibility_graph(
    visible_threats: List[ThreatView],
    combat_model: CombatModel,
    player_model: PlayerModel
) -> Tuple[nx.Graph, int]:
    """Construct Threat Incompatibility Graph H_p and compute K_ICI [G + C + P]."""
    G = nx.Graph()
    for tv in visible_threats:
        G.add_node(tv.threat_id, view=tv)

    n = len(visible_threats)
    for i in range(n):
        t1 = visible_threats[i]
        d1 = combat_model.damage_deadline(t1.min_distance_m)

        for j in range(i + 1, n):
            t2 = visible_threats[j]
            d2 = combat_model.damage_deadline(t2.min_distance_m)

            sep_deg = angular_3d_separation_deg(t1, t2)
            service_cost = player_model.service_cost_s(sep_deg)
            effective_deadline = min(d1, d2)

            # Conflict edge exists if player cannot swing and acquire target within deadline
            if service_cost > effective_deadline:
                G.add_edge(t1.threat_id, t2.threat_id, weight=service_cost, separation_deg=sep_deg)

    # Compute maximum clique size (K_ICI)
    if len(G.nodes) == 0:
        k_ici = 0
    else:
        cliques = list(nx.find_cliques(G))
        k_ici = max(len(c) for c in cliques) if cliques else 0

    return G, k_ici
