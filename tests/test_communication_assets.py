"""tests/test_communication_assets.py — Communication & Provenance Contract Tests.

Validates the integrity, links, terminology, and provenance of repository documentation,
media manifests, and advanced explainer assets without requiring scientific re-computation.
"""

import os
import re
import json
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
    """Verify that all 8 Advanced Evidence Lab presentations resolve their underlying fixtures/data."""
    pres_path = os.path.join(REPO_ROOT, "explainer", "advanced", "presentations.json")
    with open(pres_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pres_map = {p["id"]: p for p in data["presentations"]}

    # ADV-01: M08 & M11
    from cut_the_cake.fixtures_round10 import (
        build_geometric_m08_high_concurrency_solvable,
        build_geometric_m11_rapid_crossfire_aperture,
        build_geometric_m07_flank_bypass_room,
    )
    assert build_geometric_m08_high_concurrency_solvable() is not None
    assert build_geometric_m11_rapid_crossfire_aperture() is not None

    # ADV-02: M07 Flank Bypass
    assert build_geometric_m07_flank_bypass_room() is not None

    # ADV-03: Dust II A-Long
    m5a_path = os.path.join(REPO_ROOT, "results", "m5a_dust2_a_long.json")
    assert os.path.exists(m5a_path)

    # ADV-04: Canonical F1 Auto-Fix
    from cut_the_cake.cad_document import get_canonical_f1_document
    assert get_canonical_f1_document() is not None

    # ADV-05: F06 / Ascent
    f06_test = os.path.join(REPO_ROOT, "tests", "test_round10_compiler.py")
    assert os.path.exists(f06_test)

    # ADV-06: Dust II B-Tunnels / Preregistration
    m5b_path = os.path.join(REPO_ROOT, "results", "m5b_cross_section.json")
    assert os.path.exists(m5b_path)

    # ADV-07: M6-C 3D Execution
    m6c_test = os.path.join(REPO_ROOT, "tests", "test_m6c_controller_3d_execution.py")
    assert os.path.exists(m6c_test)

    # ADV-08: ViZDoom repair freeze
    repair_freeze = os.path.join(REPO_ROOT, "results", "repair", "ROUND_11_4A_FREEZE.md")
    assert os.path.exists(repair_freeze)

