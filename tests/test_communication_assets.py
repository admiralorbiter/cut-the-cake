"""tests/test_communication_assets.py — Communication & Provenance Contract Tests.

Validates the integrity, links, terminology, and provenance of repository documentation,
media manifests, and advanced explainer assets without requiring scientific re-computation.
"""

import os
import re
import json
import math
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")
MEDIA_DIR = os.path.join(DOCS_DIR, "media")


def test_capture_manifest_integrity_and_assets_exist():
    """Verify capture_manifest.json exists and all declared assets exist on disk."""
    manifest_path = os.path.join(MEDIA_DIR, "capture_manifest.json")
    assert os.path.exists(manifest_path), f"Missing {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "assets" in data
    assert len(data["assets"]) >= 5

    for asset in data["assets"]:
        assert "id" in asset
        assert "render_class" in asset
        assert asset["render_class"] in ["EVIDENCE_REPLAY", "ILLUSTRATIVE_EXPLAINER"]
        assert "source_fixture" in asset

        # Verify GIF exists
        gif_rel = asset["gif"]
        gif_abs = os.path.join(REPO_ROOT, gif_rel)
        assert os.path.exists(gif_abs), f"Declared GIF asset does not exist: {gif_abs}"

        # Verify WebM exists
        webm_rel = asset["webm"]
        webm_abs = os.path.join(REPO_ROOT, webm_rel)
        assert os.path.exists(webm_abs), f"Declared WebM asset does not exist: {webm_abs}"

    # Verify static diagrams
    for diag in data.get("static_diagrams", []):
        svg_rel = diag["svg"]
        svg_abs = os.path.join(REPO_ROOT, svg_rel)
        assert os.path.exists(svg_abs), f"Declared SVG diagram does not exist: {svg_abs}"


def test_media_readme_matches_manifest():
    """Verify docs/media/README.md advertises only assets declared in capture_manifest.json."""
    manifest_path = os.path.join(MEDIA_DIR, "capture_manifest.json")
    readme_path = os.path.join(MEDIA_DIR, "README.md")
    assert os.path.exists(readme_path)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    with open(readme_path, "r", encoding="utf-8") as f:
        readme_text = f.read()

    manifest_ids = {asset["id"] for asset in manifest["assets"]}

    for asset_id in manifest_ids:
        assert asset_id in readme_text, f"Asset {asset_id} missing from docs/media/README.md"


def test_aim_state_terminology_s2_not_so3():
    """Verify that communication docs use S^2 / unit-sphere rather than SO(3) for aim state space."""
    target_files = [
        os.path.join(REPO_ROOT, "README.md"),
        os.path.join(DOCS_DIR, "WHAT_WE_DISCOVERED.md"),
        os.path.join(DOCS_DIR, "EVIDENCE_AND_LIMITS.md"),
        os.path.join(DOCS_DIR, "ONE_PAGE_OVERVIEW.md"),
        os.path.join(DOCS_DIR, "START_HERE.md"),
        os.path.join(DOCS_DIR, "MODEL_DERIVED_PLAYER_INTUITIONS.md"),
    ]

    misleading_patterns = [
        re.compile(r"SO\(3\)\s+geodesic\s+metric", re.IGNORECASE),
        re.compile(r"SO\(3\)\s+spherical\s+aim\s+dynamics", re.IGNORECASE),
        re.compile(r"SO\(3\)\s+Slerp", re.IGNORECASE),
        re.compile(r"on\s+SO\(3\)\s+unit\s+sphere", re.IGNORECASE),
    ]

    for filepath in target_files:
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        for pat in misleading_patterns:
            match = pat.search(content)
            assert not match, f"Misleading aim-space terminology in {os.path.basename(filepath)}: '{match.group(0)}' (should be S^2 / unit sphere)"


def test_evidence_verbs_calibration():
    """Verify that simulation results are not labeled PROVEN in evidence tables."""
    evidence_path = os.path.join(DOCS_DIR, "EVIDENCE_AND_LIMITS.md")
    assert os.path.exists(evidence_path)

    with open(evidence_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Tier 3 (Simulation Sweeps) must NOT say "--> PROVEN"
    assert not re.search(r"\[Tier 3\][^\n]+──>\s*PROVEN", content), "Simulation Tier 3 should be labeled VALIDATED IN CONTROLLED SIMULATION, not PROVEN"
    # Tier 2 (PCG Sweeps) must NOT say "--> PROVEN"
    assert not re.search(r"\[Tier 2\][^\n]+──>\s*PROVEN", content), "PCG Tier 2 should be labeled VERIFIED WITHIN MODEL, not PROVEN"


def test_advanced_evidence_lab_files_and_schema():
    """Verify explainer/advanced files exist and presentations.json contains all 8 cases."""
    adv_dir = os.path.join(REPO_ROOT, "explainer", "advanced")
    assert os.path.exists(os.path.join(adv_dir, "index.html"))
    assert os.path.exists(os.path.join(adv_dir, "advanced.js"))
    assert os.path.exists(os.path.join(adv_dir, "advanced.css"))

    pres_path = os.path.join(adv_dir, "presentations.json")
    assert os.path.exists(pres_path)

    with open(pres_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "presentations" in data
    assert len(data["presentations"]) == 8

    expected_ids = {"adv01", "adv02", "adv03", "adv04", "adv05", "adv06", "adv07", "adv08"}
    found_ids = {p["id"] for p in data["presentations"]}
    assert expected_ids == found_ids, f"Mismatch in presentation IDs: {found_ids} vs {expected_ids}"


def test_paper_readme_scope_clarification():
    """Verify paper/README.md exists and documents manuscript boundaries."""
    paper_readme = os.path.join(REPO_ROOT, "paper", "README.md")
    assert os.path.exists(paper_readme)

    with open(paper_readme, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Round 11.4A" in content
    assert "Post-Manuscript" in content or "post-manuscript" in content


def test_adv01_provenance_packet_exists_and_accurate():
    """Verify docs/media/adv01_provenance.json exists and holds authoritative M08/M11 telemetry."""
    prov_path = os.path.join(MEDIA_DIR, "adv01_provenance.json")
    assert os.path.exists(prov_path), f"Missing {prov_path}"

    with open(prov_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["asset_id"] == "adv01_three_vs_two"
    assert "horizon6_cad_simulation_referee" in data
    m08 = data["horizon6_cad_simulation_referee"]["m08"]
    m11 = data["horizon6_cad_simulation_referee"]["m11"]

    assert m08["threat_count"] == 3
    assert m08["tactical_margin_tics"] == 65
    assert m08["is_feasible"] is True

    assert m11["threat_count"] == 2
    assert m11["tactical_margin_tics"] == -29
    assert m11["is_feasible"] is False


def test_presentations_gallery_authoritative_sources_wired():
    """Verify that all 8 Advanced Evidence Lab presentations match authoritative sources."""
    pres_path = os.path.join(REPO_ROOT, "explainer", "advanced", "presentations.json")
    assert os.path.exists(pres_path)
    with open(pres_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pres_map = {p["id"]: p for p in data["presentations"]}
    assert len(pres_map) == 8

    # ADV-01: M08 & M11 (Recomputed via CAD adapter)
    from cut_the_cake.fixtures_round10 import (
        build_geometric_m08_high_concurrency_solvable,
        build_geometric_m11_rapid_crossfire_aperture,
        build_geometric_m07_flank_bypass_room,
    )
    from cut_the_cake.cad_document import CADDocument, get_canonical_f1_document
    from cut_the_cake.cad_adapter import analyze_cad_document, auto_fix_cad_document

    doc_m08 = CADDocument.from_geometric_module(build_geometric_m08_high_concurrency_solvable())
    doc_m11 = CADDocument.from_geometric_module(build_geometric_m11_rapid_crossfire_aperture())
    res_m08 = analyze_cad_document(doc_m08)
    res_m11 = analyze_cad_document(doc_m11)

    adv01 = pres_map["adv01"]
    assert adv01["provenance"] == "EVIDENCE_REPLAY"
    assert adv01["authoritative_metrics"]["room_a_margin_tics"] == res_m08["tactical_margin_tics"]
    assert adv01["authoritative_metrics"]["room_a_feasible"] == res_m08["source_schedule_feasible"]
    assert adv01["authoritative_metrics"]["room_b_margin_tics"] == res_m11["tactical_margin_tics"]
    assert adv01["authoritative_metrics"]["room_b_feasible"] == res_m11["source_schedule_feasible"]

    # ADV-02: M07 Flank Bypass (Recomputed via CAD adapter)
    doc_m07 = CADDocument.from_geometric_module(build_geometric_m07_flank_bypass_room())
    res_dir = analyze_cad_document(doc_m07, route_id="direct")
    res_flank = analyze_cad_document(doc_m07, route_id="bypass")

    adv02 = pres_map["adv02"]
    assert adv02["provenance"] == "EVIDENCE_REPLAY"
    assert adv02["authoritative_metrics"]["direct_margin_tics"] == res_dir["tactical_margin_tics"]
    assert adv02["authoritative_metrics"]["direct_feasible"] == res_dir["source_schedule_feasible"]
    assert adv02["authoritative_metrics"]["flank_margin_tics"] == res_flank["tactical_margin_tics"]
    assert adv02["authoritative_metrics"]["flank_feasible"] == res_flank["source_schedule_feasible"]

    # ADV-03: Transit 213 (Parsed from results/m5b_cross_section.json)
    adv03 = pres_map["adv03"]
    assert adv03["provenance"] == "EVIDENCE_VISUALIZATION"
    m5b_path = os.path.join(REPO_ROOT, "results", "m5b_cross_section.json")
    assert os.path.exists(m5b_path)
    with open(m5b_path, "r", encoding="utf-8") as f:
        m5b = json.load(f)
    transit_routes = m5b["engagements"]["transit_213"]["routes"]
    assert adv03["authoritative_metrics"]["open_route_global_margin"] == transit_routes["route_B"]["tactical_margin_tics"]
    assert adv03["authoritative_metrics"]["open_route_min_suffix_margin"] == transit_routes["route_B"]["min_interval_suffix_margin_tics"]
    assert adv03["authoritative_metrics"]["bus_route_global_margin"] == transit_routes["route_A"]["tactical_margin_tics"]
    assert adv03["authoritative_metrics"]["bus_route_min_suffix_margin"] == transit_routes["route_A"]["min_interval_suffix_margin_tics"]

    # ADV-04: Canonical F1 Auto-Fix (Recomputed via CAD adapter)
    doc_f1 = get_canonical_f1_document()
    res_f1 = analyze_cad_document(doc_f1)
    repair_f1 = auto_fix_cad_document(doc_f1)
    res_repaired = analyze_cad_document(CADDocument.from_dict(repair_f1["repaired_document"]))

    adv04 = pres_map["adv04"]
    assert adv04["provenance"] == "EVIDENCE_REPLAY"
    assert adv04["authoritative_metrics"]["initial_margin_tics"] == res_f1["tactical_margin_tics"]
    assert adv04["authoritative_metrics"]["repaired_margin_tics"] == res_repaired["tactical_margin_tics"]
    assert math.isclose(adv04["authoritative_metrics"]["displacement_m"], repair_f1["edit_distance_m"], abs_tol=1e-3)

    # ADV-05: Continuous vs Discrete Quantization
    adv05 = pres_map["adv05"]
    assert adv05["provenance"] == "EVIDENCE_VISUALIZATION"
    assert adv05["authoritative_metrics"]["clock_hz"] == 35
    assert adv05["authoritative_metrics"]["tic_duration_ms"] == 28.57
    assert adv05["authoritative_metrics"]["ascent_margin_change_tics"] == 0

    # ADV-06: Dust II B-Tunnels Preregistered Falsification (Parsed from m5b_cross_section.json)
    adv06 = pres_map["adv06"]
    assert adv06["provenance"] == "EVIDENCE_VISUALIZATION"
    tunnels_routes = m5b["engagements"]["dust2_b_tunnels"]["routes"]
    assert adv06["authoritative_metrics"]["route_a_margin_tics"] == tunnels_routes["route_A"]["tactical_margin_tics"]
    assert adv06["authoritative_metrics"]["route_b_margin_tics"] == tunnels_routes["route_B"]["tactical_margin_tics"]

    # ADV-07: M6-C 3D Controller Parity (Authoritative Replay)
    adv07 = pres_map["adv07"]
    assert adv07["provenance"] == "EVIDENCE_REPLAY"
    assert adv07["authoritative_metrics"]["execution_parity_rate"] == 1.0
    assert adv07["authoritative_metrics"]["threat_count"] == 3
    assert adv07["authoritative_metrics"]["parity_theorem"] == "t_j(event) == C_j - 1"

    # ADV-08: ViZDoom Transfer Residuals (Parsed from results/repair/results.json)
    adv08 = pres_map["adv08"]
    assert adv08["provenance"] == "EVIDENCE_VISUALIZATION"
    repair_json_path = os.path.join(REPO_ROOT, "results", "repair", "results.json")
    assert os.path.exists(repair_json_path)
    with open(repair_json_path, "r", encoding="utf-8") as f:
        rep_results = json.load(f)

    assert adv08["authoritative_metrics"]["source_repair_rate"] == rep_results["source_repair_success_rate"]
    assert adv08["authoritative_metrics"]["engine_transfer_efficiency"] == rep_results["engine_transfer_efficiency"]
    assert adv08["authoritative_metrics"]["family_1_transfer_efficiency"] == rep_results["family_breakdowns"]["Family_1_Stagger_Deficit"]["transfer_efficiency"]
    assert adv08["authoritative_metrics"]["family_4_transfer_efficiency"] == rep_results["family_breakdowns"]["Family_4_Triad_Congestion"]["transfer_efficiency"]



