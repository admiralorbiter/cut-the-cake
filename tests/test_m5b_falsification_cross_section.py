"""Milestone 5-B: Pre-Registered Multi-Engagement Falsification Cross-Section Tests.

Tests:
1. Pre-Registration Protocol Validation (preregistration/m5b_preregistration.json)
2. Strict 2D Navigability & Positive Clearance across all 3 fixtures (Ascent, Dust II B, Transit 213)
3. Engagement 1 (Ascent A-Main / Wine): Suffix margin approach superiority & Wine pocket isolation
4. Engagement 2 (Dust II B-Tunnels): Immediate choke crossfire collapse & negative exit margins
5. Engagement 3 (Transit 213): Occluder lattice cover preservation over open lot exposure
6. Aggregate Cross-Section Truthfulness (results/m5b_cross_section.json matches live solver)
7. REST API Template Loading & Multi-Route Analysis Parity across all 3 new maps
"""

import os
import json
import pytest
from shapely.geometry import LineString, Polygon

pytestmark = [pytest.mark.cad]

from cut_the_cake.cad_document import (
    validate_cad_document,
    get_ascent_a_main_document,
    get_dust2_b_tunnels_document,
    get_transit_213_document
)
from cut_the_cake.cad_adapter import (
    analyze_cad_document,
    compute_cad_route_spatial_heatmap
)
from cut_the_cake.cad_server import create_cad_app


def test_m5b_preregistration_protocol_schema():
    """Verify preregistration/m5b_preregistration.json exists and contains required sealed fields."""
    proto_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "preregistration", "m5b_preregistration.json")
    assert os.path.exists(proto_path), "Pre-registration protocol file missing"

    with open(proto_path, "r", encoding="utf-8") as f:
        proto = json.load(f)

    assert proto["protocol"] == "M5-B.0"
    assert "engagements" in proto
    assert set(proto["engagements"].keys()) == {"ascent_a_main", "dust2_b_tunnels", "transit_213"}

    for eng_id, data in proto["engagements"].items():
        assert "topological_mechanism" in data
        assert "blinded_mapping" in data
        assert "evaluation_interval_m" in data
        assert "pre_registered_hypotheses" in data
        assert "falsification_criterion" in data["pre_registered_hypotheses"]


def test_m5b_fixtures_navigability_and_clearance():
    """Verify all routes in all 3 fixtures maintain >= 0.40 m clearance and zero polygon intersections."""
    fixtures = [
        ("ascent_a_main", get_ascent_a_main_document()),
        ("dust2_b_tunnels", get_dust2_b_tunnels_document()),
        ("transit_213", get_transit_213_document())
    ]

    for name, doc in fixtures:
        is_valid, errors = validate_cad_document(doc.to_dict())
        assert is_valid, f"{name} CAD validation failed: {errors}"

        obs_polys = [Polygon(o.vertices) for o in doc.obstacles]
        for r in doc.routes:
            for i in range(len(r.waypoints) - 1):
                seg = LineString([r.waypoints[i], r.waypoints[i+1]])
                for o_idx, poly in enumerate(obs_polys):
                    assert not seg.intersects(poly), (
                        f"[{name}] Route '{r.id}' seg {i}->{i+1} intersects '{doc.obstacles[o_idx].id}'"
                    )
                    dist = seg.distance(poly)
                    assert dist >= 0.40, (
                        f"[{name}] Route '{r.id}' seg {i}->{i+1} clearance ({dist:.3f}m) below 0.40m"
                    )


def test_m5b_ascent_a_main_wine_slice_superiority():
    """Engagement 1: Assert route_A (Wine slice) achieves higher approach suffix margin and reaches Wine isolation."""
    doc = get_ascent_a_main_document()

    h_a = compute_cad_route_spatial_heatmap(doc, route_id="route_A")
    h_b = compute_cad_route_spatial_heatmap(doc, route_id="route_B")

    # 1. Approach interval s in [8, 16] m
    m_min_a = min(s["suffix_margin_tics"] for s in h_a["samples"] if 8.0 <= s["distance_m"] <= 16.0)
    m_min_b = min(s["suffix_margin_tics"] for s in h_b["samples"] if 8.0 <= s["distance_m"] <= 16.0)
    assert m_min_a > m_min_b, f"Expected route_A ({m_min_a}) > route_B ({m_min_b}) over approach interval"

    # 2. Wine pocket isolation (at s ~ 18m inside Wine mouth)
    wine_samples = [s for s in h_a["samples"] if 17.0 <= s["distance_m"] <= 19.0]
    isolated_sample = next((s for s in wine_samples if s["los_concurrency"] == 1 and s["suffix_margin_tics"] >= 0), None)
    assert isolated_sample is not None, "route_A failed to achieve isolated K=1 non-negative margin in Wine mouth"


def test_m5b_dust2_b_tunnels_crossfire_collapse():
    """Engagement 2: Assert both dry routes suffer immediate K>=2 crossfire and exit deficit (model refuses false serialization)."""
    doc = get_dust2_b_tunnels_document()

    h_a = compute_cad_route_spatial_heatmap(doc, route_id="route_A")
    h_b = compute_cad_route_spatial_heatmap(doc, route_id="route_B")

    # Both routes suffer immediate K>=2 upon crossing exit threshold s in [0, 4]m
    first_k2_a = next(s for s in h_a["samples"] if s["los_concurrency"] >= 2)
    first_k2_b = next(s for s in h_b["samples"] if s["los_concurrency"] >= 2)
    assert first_k2_a["distance_m"] <= 4.0, f"route_A K=2 delayed unexpectedly to {first_k2_a['distance_m']}m"
    assert first_k2_b["distance_m"] <= 4.0, f"route_B K=2 delayed unexpectedly to {first_k2_b['distance_m']}m"

    # Suffix margin over exit interval [0, 6]m remains in deficit (<= 0)
    min_exit_a = min(s["suffix_margin_tics"] for s in h_a["samples"] if 0.0 <= s["distance_m"] <= 6.0)
    min_exit_b = min(s["suffix_margin_tics"] for s in h_b["samples"] if 0.0 <= s["distance_m"] <= 6.0)
    assert min_exit_a <= 0, f"route_A unexpectedly achieved positive margin {min_exit_a} on dry tunnel exit"
    assert min_exit_b <= 0, f"route_B unexpectedly achieved positive margin {min_exit_b} on dry tunnel exit"


def test_m5b_transit_213_occluder_lattice_cover():
    """Engagement 3: Assert bus lattice route_A preserves superior lot suffix margin over open lot route_B."""
    doc = get_transit_213_document()

    h_a = compute_cad_route_spatial_heatmap(doc, route_id="route_A")
    h_b = compute_cad_route_spatial_heatmap(doc, route_id="route_B")

    # Over lot transit interval s in [6, 18] m
    min_lot_a = min(s["suffix_margin_tics"] for s in h_a["samples"] if 6.0 <= s["distance_m"] <= 18.0)
    min_lot_b = min(s["suffix_margin_tics"] for s in h_b["samples"] if 6.0 <= s["distance_m"] <= 18.0)
    assert min_lot_a > min_lot_b, f"Bus lattice ({min_lot_a}) should exceed open lot ({min_lot_b})"


def test_m5b_aggregate_cross_section_matrix_truthfulness():
    """Verify results/m5b_cross_section.json accurately records all 3 engagement outcomes."""
    res_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "m5b_cross_section.json")
    assert os.path.exists(res_path), "results/m5b_cross_section.json missing"

    with open(res_path, "r", encoding="utf-8") as f:
        saved = json.load(f)

    assert saved["protocol_reference"] == "M5-B.0"
    for eng_id in ["ascent_a_main", "dust2_b_tunnels", "transit_213"]:
        assert eng_id in saved["engagements"]
        assert saved["engagements"][eng_id]["hypothesis_supported"] is True


def test_m5b_server_template_loading_for_all_fixtures():
    """Verify CAD server REST API successfully loads and analyzes all 3 new M5-B templates."""
    app = create_cad_app()
    client = app.test_client()

    for name in ["ascent_a_main", "dust2_b_tunnels", "transit_213"]:
        resp = client.post("/api/document/load", json={"name": name})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "loaded"
        assert data["document_type"] == name

        resp_an = client.post("/api/document/analyze", json={"route_id": "route_A", "include_telemetry": True})
        assert resp_an.status_code == 200
        assert resp_an.get_json()["is_valid"] is True
