"""Metamorphic property tests for CADDocument analysis and scheduling.

Validates fundamental mathematical and physical relations:
1. Monotone Occluder Shift: on a constructed straight corridor, moving an occluder
   downstream cannot make reveal earlier.
2. Exact Discrete Route-Speed Scaling: r(v/2) in {2r(v) - 1, 2r(v)} by discrete time calculus.
3. Rigid-Body Transformation Invariance: rotating and translating the entire world
   preserves exact relative reveal positions, relative angular setup, deadlines, L*, and M.
4. Unrevealed-Threat Invariance: adding a completely unreleased threat (no LOS anywhere along route)
   leaves extracted jobs, L*, and M strictly identical.
"""

from __future__ import annotations
import copy
import math
import pytest

from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPlayerModel,
    get_custom_asymmetric_corridor_document,
)
from cut_the_cake.cad_adapter import (
    analyze_cad_document,
    update_route_speed,
)


def _rotate_point(x: float, y: float, cx: float, cy: float, angle_rad: float) -> list[float]:
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    dx = x - cx
    dy = y - cy
    rx = cx + dx * cos_a - dy * sin_a
    ry = cy + dx * sin_a + dy * cos_a
    return [round(rx, 4), round(ry, 4)]


def _transform_document_rigid_body(doc: CADDocument, angle_deg: float, tx: float, ty: float) -> CADDocument:
    """Rotate the entire world around (0,0) by angle_deg and translate by (tx, ty)."""
    rad = math.radians(angle_deg)
    d = copy.deepcopy(doc)

    if d.boundary:
        d.boundary = [_rotate_point(p[0] + tx, p[1] + ty, 0.0, 0.0, rad) for p in d.boundary]

    for obs in d.obstacles:
        obs.vertices = [_rotate_point(p[0] + tx, p[1] + ty, 0.0, 0.0, rad) for p in obs.vertices]

    for th in d.threats:
        th.anchor = _rotate_point(th.anchor[0] + tx, th.anchor[1] + ty, 0.0, 0.0, rad)
        if th.polygon:
            th.polygon = [_rotate_point(p[0] + tx, p[1] + ty, 0.0, 0.0, rad) for p in th.polygon]

    for r in d.routes:
        r.waypoints = [_rotate_point(p[0] + tx, p[1] + ty, 0.0, 0.0, rad) for p in r.waypoints]

    # player_model.initial_reticle_deg is local offset relative to route forward heading,
    # so rigid body rotation of both route and threats preserves this relative angle.
    return d


def _make_straight_monotonic_fixture(wall_x: float) -> CADDocument:
    """Constructed straight-line fixture with a single occluder at wall_x blocking a threat at (8.0, 2.0)."""
    return CADDocument(
        document_id=f"monotonic_fixture_{wall_x}",
        name="monotonic_fixture",
        schema_version="cad_document_v1",
        boundary=[[-2.0, -4.0], [14.0, -4.0], [14.0, 6.0], [-2.0, 6.0]],
        player_model=CADPlayerModel(
            v_move_mps=4.0,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0,
        ),
        obstacles=[
            CADObstacle(
                id="mono_wall",
                name="Monotonic Wall",
                vertices=[[wall_x, 0.2], [wall_x + 0.4, 0.2], [wall_x + 0.4, 3.0], [wall_x, 3.0]],
            )
        ],
        routes=[
            CADRoute(
                id="mono_route",
                name="Monotonic Route",
                waypoints=[[0.0, 0.0], [10.0, 0.0]],
                v_move_mps=4.0,
            )
        ],
        threats=[
            CADThreat(
                id="mono_threat",
                name="Monotonic Threat",
                polygon=[[7.8, 1.8], [8.2, 1.8], [8.2, 2.2], [7.8, 2.2]],
                anchor=[8.0, 2.0],
                due_window_s=0.6,
                service_duration_s=0.15,
            )
        ],
    )


class TestCADMetamorphicProperties:
    """Metamorphic test suite discovering algorithmic bugs via implementation invariants."""

    def test_monotone_occluder_shift(self):
        """On a straight monotonic corridor, shifting the occluding wall downstream (+x)
        must never cause the occluded threat to be revealed earlier.
        """
        doc_near = _make_straight_monotonic_fixture(wall_x=4.0)
        res_near = analyze_cad_document(doc_near, include_telemetry=False)
        assert res_near["is_valid"] is True
        r_near = res_near["threat_jobs"][0]["reveal_tic"]

        doc_far = _make_straight_monotonic_fixture(wall_x=5.5)
        res_far = analyze_cad_document(doc_far, include_telemetry=False)
        assert res_far["is_valid"] is True
        r_far = res_far["threat_jobs"][0]["reveal_tic"]

        assert r_far >= r_near, (
            f"Downstream wall shift revealed threat earlier: r_far={r_far} < r_near={r_near}"
        )

    def test_route_speed_scaling_discrete_exact(self):
        """Halving route speed v -> v/2 must satisfy discrete-time reveal relation:
        r(v/2) in { 2*r(v) - 1, 2*r(v) }.
        """
        doc_base = _make_straight_monotonic_fixture(wall_x=4.0)
        
        doc_fast, ok_f, _ = update_route_speed(doc_base, "mono_route", 4.0)
        assert ok_f is True
        res_fast = analyze_cad_document(doc_fast, include_telemetry=True)
        r_fast = res_fast["threat_jobs"][0]["reveal_tic"]
        assert r_fast > 0, "Threat must have positive reveal tic"

        doc_slow, ok_s, _ = update_route_speed(doc_base, "mono_route", 2.0)
        assert ok_s is True
        res_slow = analyze_cad_document(doc_slow, include_telemetry=True)
        r_slow = res_slow["threat_jobs"][0]["reveal_tic"]

        expected_set = {2 * r_fast - 1, 2 * r_fast}
        assert r_slow in expected_set, (
            f"Discrete speed scaling violated: r(v/2)={r_slow} not in {expected_set} (r(v)={r_fast})"
        )

    def test_rigid_body_rotation_invariance(self):
        """Verifies on the custom asymmetric corridor fixture that rotating and translating
        the entire world (geometry, route, threats, reticle) preserves tactical margin M, L*,
        and threat job due windows within numerical rounding tolerance (<= 1 tic).
        """
        doc = get_custom_asymmetric_corridor_document()
        res_base = analyze_cad_document(doc, include_telemetry=True)

        for angle in [30.0, 45.0, 90.0, 180.0, -60.0]:
            doc_rot = _transform_document_rigid_body(doc, angle_deg=angle, tx=12.5, ty=-8.2)
            res_rot = analyze_cad_document(doc_rot, include_telemetry=True)

            assert res_rot["is_valid"] is True
            # Tactical margin and L* must be invariant (within 1 tic rounding)
            assert abs(res_rot["tactical_margin_tics"] - res_base["tactical_margin_tics"]) <= 1, (
                f"Rotation by {angle} deg altered M: {res_rot['tactical_margin_tics']} vs {res_base['tactical_margin_tics']}"
            )
            assert abs(res_rot["l_star_tics"] - res_base["l_star_tics"]) <= 1

            # Assert each threat's relative due window (deadline_tic - reveal_tic) is invariant
            jobs_base = {j["id"]: j for j in res_base["threat_jobs"]}
            jobs_rot = {j["id"]: j for j in res_rot["threat_jobs"]}
            assert set(jobs_base.keys()) == set(jobs_rot.keys())
            for tid in jobs_base:
                window_base = jobs_base[tid]["deadline_tic"] - jobs_base[tid]["reveal_tic"]
                window_rot = jobs_rot[tid]["deadline_tic"] - jobs_rot[tid]["reveal_tic"]
                assert abs(window_base - window_rot) <= 1, f"Due window altered for {tid}: {window_base} vs {window_rot}"

    def test_unrevealed_threat_invariance(self):
        """Adding a threat with no line of sight anywhere along the route (completely encased in walls)
        must leave extracted jobs, L*, and tactical margin M strictly identical.
        """
        doc = get_custom_asymmetric_corridor_document()
        res_base = analyze_cad_document(doc, include_telemetry=False)
        m_base = res_base["tactical_margin_tics"]
        l_base = res_base["l_star_tics"]
        job_count_base = len(res_base["threat_jobs"])

        # Add a fully encased bunker threat at (5.0, 5.0) surrounded by walls
        doc_bunker = copy.deepcopy(doc)
        doc_bunker.obstacles.append(
            CADObstacle(
                id="bunker_box",
                name="Bunker Box",
                vertices=[[4.0, 4.0], [6.0, 4.0], [6.0, 6.0], [4.0, 6.0]],
            )
        )
        doc_bunker.threats.append(
            CADThreat(
                id="threat_bunker_isolated",
                name="Bunker Threat",
                polygon=[[4.8, 4.8], [5.2, 4.8], [5.2, 5.2], [4.8, 5.2]],
                anchor=[5.0, 5.0],
                due_window_s=0.5,
                service_duration_s=0.2,
            )
        )

        res_bunker = analyze_cad_document(doc_bunker, include_telemetry=False)
        
        # Threat is never revealed, so job compilation extracts 0 jobs for it
        extracted_ids = [j["id"] for j in res_bunker["threat_jobs"]]
        assert "threat_bunker_isolated" not in extracted_ids
        assert len(res_bunker["threat_jobs"]) == job_count_base
        assert res_bunker["l_star_tics"] == l_base
        assert res_bunker["tactical_margin_tics"] == m_base

        # Verify complete baseline-job mapping equality before and after
        jobs_base_map = {j["id"]: (j["reveal_tic"], j["deadline_tic"], j["service_duration_tics"]) for j in res_base["threat_jobs"]}
        jobs_bunker_map = {j["id"]: (j["reveal_tic"], j["deadline_tic"], j["service_duration_tics"]) for j in res_bunker["threat_jobs"]}
        assert jobs_bunker_map == jobs_base_map
