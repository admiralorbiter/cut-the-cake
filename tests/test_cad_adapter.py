"""Tests for Tactical CAD Adapter Layer & Server [Milestone 2A].

Verifies:
1. dx = 0.00 m exactly reproduces frozen Broken source values (r2=3, D2=25, L*=6, M=-6).
2. dx = 1.10 m exactly reproduces frozen Repaired source values (r2=13, D2=35, L*=-2, M=+2).
3. Monotonicity of r2 and M across 0.05 m interactive translation steps.
4. Preservation of deadline invariant D_j = r_j + Delta D_j.
5. Rejection of invalid spatial translations (boundary breach, corridor collision).
6. Fail-closed external engine evidence (transfer_status: 'not_run').
7. Client revision echo integrity.
8. Full telemetry generation on drag commit.
9. Flask HTTP endpoints (/api/health, /api/analyze, /api/fixture/...).
"""

import json
import pytest

from cut_the_cake.cad_adapter import analyze_candidate_geometry
from cut_the_cake.cad_server import create_cad_app


def test_adapter_zero_translation_matches_frozen_broken():
    """Translation dx = 0.00m must reproduce frozen Broken source values exactly."""
    res = analyze_candidate_geometry(
        fixture_id="RepairPop_F1_StaggerDeficit_00",
        obstacle_id=0,
        translation_m=0.0,
        axis="x"
    )
    assert res["is_valid"] is True
    assert res["status_band"] == "UNSERVICEABLE"
    assert res["tactical_margin_tics"] == -6
    assert res["l_star_tics"] == 6
    assert res["r1_reveal_tic"] == 0
    assert res["r2_reveal_tic"] == 3
    assert res["stagger_gap_tics"] == 3
    assert res["source_schedule_feasible"] is False
    assert res["model_episode_survived"] is None
    assert res["external_engine_evidence"]["transfer_status"] == "not_run"
    assert res["external_engine_evidence"]["broken_engine_survived"] is None


def test_adapter_target_repair_translation_matches_frozen_repaired():
    """Translation dx = 1.10m must reproduce frozen Repaired source values exactly."""
    res = analyze_candidate_geometry(
        fixture_id="RepairPop_F1_StaggerDeficit_00",
        obstacle_id=0,
        translation_m=1.10,
        axis="x"
    )
    assert res["is_valid"] is True
    assert res["status_band"] == "TARGET RESERVE MET"
    assert res["tactical_margin_tics"] == 2
    assert res["l_star_tics"] == -2
    assert res["r1_reveal_tic"] == 0
    assert res["r2_reveal_tic"] == 13
    assert res["stagger_gap_tics"] == 13
    assert res["source_schedule_feasible"] is True
    assert res["model_episode_survived"] is None


def test_adapter_intermediate_monotonicity_sweep():
    """Interactive drag sweep in 0.05m steps must exhibit monotonic delay and margin progression."""
    prev_r2 = -1
    prev_margin = -999
    seen_bands = set()

    for step in range(0, 23):  # 0.00m to 1.10m
        dx = round(step * 0.05, 2)
        res = analyze_candidate_geometry(
            fixture_id="RepairPop_F1_StaggerDeficit_00",
            obstacle_id=0,
            translation_m=dx,
            axis="x"
        )
        assert res["is_valid"] is True, f"Failed at dx={dx}: {res.get('error_reason')}"
        
        r2 = res["r2_reveal_tic"]
        m = res["tactical_margin_tics"]
        band = res["status_band"]
        seen_bands.add(band)

        assert r2 >= prev_r2, f"r2 decreased at dx={dx}: {r2} < {prev_r2}"
        assert m >= prev_margin, f"Margin decreased at dx={dx}: {m} < {prev_margin}"

        prev_r2 = r2
        prev_margin = m

    # Must cover both UNSERVICEABLE and TARGET RESERVE MET
    assert "UNSERVICEABLE" in seen_bands
    assert "TARGET RESERVE MET" in seen_bands


def test_adapter_deadline_invariant_preservation():
    """For every candidate displacement, D_j == r_j + due_window_tics must strictly hold."""
    for dx in [0.0, 0.25, 0.55, 0.85, 1.10]:
        res = analyze_candidate_geometry(
            fixture_id="RepairPop_F1_StaggerDeficit_00",
            obstacle_id=0,
            translation_m=dx,
            axis="x"
        )
        assert res["is_valid"] is True
        for job in res["threat_jobs"]:
            assert job["deadline_tic"] == job["reveal_tic"] + job["due_window_tics"]
            assert job["completion_tic"] == job["scheduled_service_end_tic"] + 1


def test_adapter_geometric_rejection_of_invalid_translations():
    """Invalid translations must fail closed without returning scientific metrics."""
    # Out of boundary (right)
    res_right = analyze_candidate_geometry(
        fixture_id="RepairPop_F1_StaggerDeficit_00",
        obstacle_id=0,
        translation_m=10.0,
        axis="x"
    )
    assert res_right["is_valid"] is False
    assert "outside" in res_right["error_reason"].lower() or "boundary" in res_right["error_reason"].lower()

    # Out of boundary (left)
    res_left = analyze_candidate_geometry(
        fixture_id="RepairPop_F1_StaggerDeficit_00",
        obstacle_id=0,
        translation_m=-2.0,
        axis="x"
    )
    assert res_left["is_valid"] is False

    # Unsupported axis
    res_axis = analyze_candidate_geometry(
        fixture_id="RepairPop_F1_StaggerDeficit_00",
        obstacle_id=0,
        translation_m=0.5,
        axis="z"
    )
    assert res_axis["is_valid"] is False
    assert "axis" in res_axis["error_reason"].lower()


def test_adapter_client_revision_echo():
    """Server must echo client revision to avoid out-of-order stale application."""
    res = analyze_candidate_geometry(
        fixture_id="RepairPop_F1_StaggerDeficit_00",
        obstacle_id=0,
        translation_m=0.55,
        client_revision=104
    )
    assert res["client_revision"] == 104


def test_adapter_full_telemetry_generation_on_commit():
    """include_telemetry=True must generate per-tic frames and discrete events."""
    res = analyze_candidate_geometry(
        fixture_id="RepairPop_F1_StaggerDeficit_00",
        obstacle_id=0,
        translation_m=1.10,
        include_telemetry=True
    )
    assert res["is_valid"] is True
    assert res["telemetry_frames"] is not None
    assert len(res["telemetry_frames"]) > 10
    assert res["events"] is not None
    assert len(res["events"]) > 0


def test_cad_server_flask_endpoints():
    """Verify Flask HTTP REST endpoints (/api/health, /api/analyze, /api/fixture/...)."""
    app = create_cad_app()
    client = app.test_client()

    # 1. Health
    resp_health = client.get("/api/health")
    assert resp_health.status_code == 200
    assert resp_health.get_json()["status"] == "ok"

    # 2. Fixture
    resp_fix = client.get("/api/fixture/RepairPop_F1_StaggerDeficit_00")
    assert resp_fix.status_code == 200
    assert resp_fix.get_json()["schema_version"] in ("1.0", "1.1")

    # 3. Analyze valid
    resp_analyze = client.post("/api/analyze", json={
        "fixture_id": "RepairPop_F1_StaggerDeficit_00",
        "obstacle_id": 0,
        "translation_m": 0.55,
        "axis": "x",
        "client_revision": 12,
        "include_telemetry": False
    })
    assert resp_analyze.status_code == 200
    data = resp_analyze.get_json()
    assert data["is_valid"] is True
    assert data["client_revision"] == 12
    assert data["r2_reveal_tic"] > 3

    # 4. Analyze invalid
    resp_invalid = client.post("/api/analyze", json={
        "fixture_id": "RepairPop_F1_StaggerDeficit_00",
        "obstacle_id": 0,
        "translation_m": 25.0,
        "axis": "x"
    })
    assert resp_invalid.status_code == 422
    assert resp_invalid.get_json()["is_valid"] is False
