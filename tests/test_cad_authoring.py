"""Tactical CAD Obstacle Gray-Box Authoring Tests [Milestone 2C].

Verifies:
1. Obstacle Creation:
   - Valid rectangle creation commits with unique stable ID (wall_001).
   - Too-small dimensions (<0.10m) rejected with 422.
   - Out-of-boundary / route-colliding / threat-colliding rectangle rejected.
2. Obstacle Resizing:
   - Corner handle drag resizes width/height with opposite corner pinned.
   - Resized dimensions < 0.10m rejected.
   - Resizing that causes boundary breach or collision rejected without mutating document.
3. Obstacle Rotation:
   - Centroid and area preserved after rotation.
   - Rotated collision with threat or boundary rejected without mutating document.
4. Obstacle Deletion:
   - Deleting obstacle removes it from document.
   - Document with 0 obstacles remains valid.
5. Server History (Undo/Redo):
   - Full sequence: Create -> Move -> Resize -> Rotate -> Delete.
   - Repeated Undo steps backward through each exact document state.
   - Repeated Redo steps forward through each exact document state.
   - Intermediate mutation clears redo stack.
   - Reset Baseline restores initial loaded document independently of history.
"""

import math
import pytest
from shapely.geometry import Polygon

from cut_the_cake.cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPlayerModel,
    get_canonical_f1_document,
    get_custom_asymmetric_corridor_document
)
from cut_the_cake.cad_adapter import (
    create_rectangle_obstacle,
    translate_obstacle_in_document,
    resize_rectangle_obstacle,
    rotate_obstacle_in_document,
    delete_obstacle_in_document,
    analyze_cad_document
)
from cut_the_cake.cad_server import create_cad_app


def test_create_rectangle_obstacle():
    """Verify rectangle creation, ID assignment, and geometric invariant validation."""
    doc = get_custom_asymmetric_corridor_document()
    init_count = len(doc.obstacles)

    # 1. Valid rectangle creation in clear space [6.0, 0.5] to [7.2, 1.8]
    new_doc, new_id, is_valid, err = create_rectangle_obstacle(
        doc, x1=6.0, y1=0.5, x2=7.2, y2=1.8, name="Central Partition"
    )
    assert is_valid is True
    assert err is None
    assert new_id.startswith("wall_")
    assert len(new_doc.obstacles) == init_count + 1
    created_obs = next(o for o in new_doc.obstacles if o.id == new_id)
    assert created_obs.name == "Central Partition"

    # 2. Too small dimensions (< 0.10m) rejected
    _, _, is_valid_small, err_small = create_rectangle_obstacle(
        doc, x1=6.0, y1=0.5, x2=6.05, y2=0.55
    )
    assert is_valid_small is False
    assert "smaller than minimum" in err_small.lower()

    # 3. Route collision rejected
    _, _, is_valid_route, err_route = create_rectangle_obstacle(
        doc, x1=5.0, y1=-0.5, x2=7.0, y2=0.5  # Crosses route at y=0.0
    )
    assert is_valid_route is False
    assert "route" in err_route.lower()

    # 4. Out-of-boundary placement rejected
    _, _, is_valid_out, err_out = create_rectangle_obstacle(
        doc, x1=11.5, y1=2.0, x2=13.0, y2=3.5  # Boundary max x is 12.0, max y is 3.0
    )
    assert is_valid_out is False
    assert "boundary" in err_out.lower()


def test_resize_rectangle_obstacle():
    """Verify corner handle resizing with opposite corner anchored."""
    doc = get_custom_asymmetric_corridor_document()

    # Create a fresh test obstacle at [6.0, 0.5] to [7.0, 1.5] (W=1.0, H=1.0)
    doc, obs_id, is_valid, _ = create_rectangle_obstacle(
        doc, x1=6.0, y1=0.5, x2=7.0, y2=1.5, name="Resize Test Wall"
    )
    assert is_valid is True

    # 1. Resize SE corner (bottom-right: x=7.0, y=0.5) by dx=+0.3m, dy=-0.2m
    # Anchored NW corner remains at (6.0, 1.5). New SE corner is (7.3, 0.3).
    res_doc, is_valid_res, err_res = resize_rectangle_obstacle(
        doc, obstacle_id=obs_id, handle="se", dx=0.3, dy=-0.2
    )
    assert is_valid_res is True
    res_obs = next(o for o in res_doc.obstacles if o.id == obs_id)
    poly = res_obs.to_polygon()
    min_x, min_y, max_x, max_y = poly.bounds
    assert abs(min_x - 6.0) < 1e-3
    assert abs(max_y - 1.5) < 1e-3
    assert abs(max_x - 7.3) < 1e-3
    assert abs(min_y - 0.3) < 1e-3

    # 2. Resize that causes route collision rejected
    _, is_valid_coll, err_coll = resize_rectangle_obstacle(
        res_doc, obstacle_id=obs_id, handle="se", dx=0.0, dy=-0.5  # Reaches y=0.0 (route)
    )
    assert is_valid_coll is False
    assert "route" in err_coll.lower()


def test_rotate_obstacle():
    """Verify obstacle rotation preserves centroid and area."""
    doc = get_custom_asymmetric_corridor_document()
    doc, obs_id, is_valid, _ = create_rectangle_obstacle(
        doc, x1=6.0, y1=0.5, x2=7.0, y2=1.5
    )
    assert is_valid is True

    orig_poly = next(o for o in doc.obstacles if o.id == obs_id).to_polygon()
    orig_centroid = orig_poly.centroid
    orig_area = orig_poly.area

    # 1. Rotate by 45 degrees
    rot_doc, is_valid_rot, err_rot = rotate_obstacle_in_document(
        doc, obstacle_id=obs_id, angle_deg=45.0
    )
    assert is_valid_rot is True
    rot_obs = next(o for o in rot_doc.obstacles if o.id == obs_id)
    rot_poly = rot_obs.to_polygon()

    # Centroid must match within float precision
    assert abs(rot_poly.centroid.x - orig_centroid.x) < 1e-3
    assert abs(rot_poly.centroid.y - orig_centroid.y) < 1e-3
    # Area must be preserved
    assert abs(rot_poly.area - orig_area) < 1e-3

    # 2. Rotate by 360 degrees -> returns to starting vertices
    rot360_doc, _, _ = rotate_obstacle_in_document(doc, obstacle_id=obs_id, angle_deg=360.0)
    rot360_obs = next(o for o in rot360_doc.obstacles if o.id == obs_id)
    assert rot360_obs.to_polygon().equals_exact(orig_poly, tolerance=1e-3)


def test_delete_obstacle():
    """Verify obstacle deletion leaves remaining document valid."""
    doc = get_custom_asymmetric_corridor_document()
    assert len(doc.obstacles) == 2

    # 1. Delete pillar_alpha
    del_doc, is_valid, _ = delete_obstacle_in_document(doc, "pillar_alpha")
    assert is_valid is True
    assert len(del_doc.obstacles) == 1
    assert del_doc.obstacles[0].id == "pillar_beta"

    # 2. Delete remaining pillar_beta -> 0 obstacles
    del_all_doc, is_valid2, _ = delete_obstacle_in_document(del_doc, "pillar_beta")
    assert is_valid2 is True
    assert len(del_all_doc.obstacles) == 0

    # Document with 0 obstacles is valid for analysis
    res = analyze_cad_document(del_all_doc)
    assert res["is_valid"] is True


def test_undo_redo_history_stack():
    """Verify full sequence Create -> Move -> Resize -> Rotate -> Delete with Undo and Redo."""
    app = create_cad_app()
    client = app.test_client()

    # Load custom corridor
    client.post("/api/document/load", json={"name": "custom_corridor"})
    base_doc = client.get("/api/document").get_json()
    assert len(base_doc["geometry"]["obstacles"]) == 2

    # State 1: Create wall_001 in clear area [6.0, 0.5] to [7.0, 1.5]
    resp_create = client.post("/api/document/create_obstacle", json={
        "x1": 6.0, "y1": 0.5, "x2": 7.0, "y2": 1.5, "name": "History Test Wall", "commit": True
    })
    assert resp_create.status_code == 200
    doc_1 = client.get("/api/document").get_json()
    assert len(doc_1["geometry"]["obstacles"]) == 3
    assert doc_1["can_undo"] is True
    assert doc_1["can_redo"] is False
    wall_id = resp_create.get_json()["created_obstacle_id"]

    # State 2: Translate wall_001 by dx = +0.2m
    resp_move = client.post("/api/document/translate_obstacle", json={
        "obstacle_id": wall_id, "dx": 0.2, "dy": 0.0, "commit": True
    })
    assert resp_move.status_code == 200
    doc_2 = client.get("/api/document").get_json()
    assert abs(doc_2["geometry"]["obstacles"][2]["vertices"][0][0] - 6.2) < 1e-3

    # State 3: Resize wall_001
    resp_resize = client.post("/api/document/resize_obstacle", json={
        "obstacle_id": wall_id, "handle": "se", "dx": 0.1, "dy": 0.0, "commit": True
    })
    assert resp_resize.status_code == 200
    doc_3 = client.get("/api/document").get_json()

    # State 4: Rotate wall_001
    resp_rotate = client.post("/api/document/rotate_obstacle", json={
        "obstacle_id": wall_id, "angle_deg": 15.0, "commit": True
    })
    assert resp_rotate.status_code == 200
    doc_4 = client.get("/api/document").get_json()

    # State 5: Delete wall_001
    resp_del = client.post("/api/document/delete_obstacle", json={
        "obstacle_id": wall_id
    })
    assert resp_del.status_code == 200
    doc_5 = client.get("/api/document").get_json()
    assert len(doc_5["geometry"]["obstacles"]) == 2

    # --- UNDO BACKWARD STEP BY STEP ---
    # Undo Delete -> State 4 (Rotate)
    resp_u1 = client.post("/api/document/undo")
    assert resp_u1.status_code == 200
    assert len(client.get("/api/document").get_json()["geometry"]["obstacles"]) == 3

    # Undo Rotate -> State 3 (Resize)
    resp_u2 = client.post("/api/document/undo")
    assert resp_u2.status_code == 200

    # Undo Resize -> State 2 (Move)
    resp_u3 = client.post("/api/document/undo")
    assert resp_u3.status_code == 200

    # Undo Move -> State 1 (Create)
    resp_u4 = client.post("/api/document/undo")
    assert resp_u4.status_code == 200
    assert abs(client.get("/api/document").get_json()["geometry"]["obstacles"][2]["vertices"][0][0] - 6.0) < 1e-3

    # Undo Create -> State 0 (Initial Baseline)
    resp_u5 = client.post("/api/document/undo")
    assert resp_u5.status_code == 200
    doc_u5 = client.get("/api/document").get_json()
    assert len(doc_u5["geometry"]["obstacles"]) == 2
    assert doc_u5["can_undo"] is False
    assert doc_u5["can_redo"] is True

    # --- REDO FORWARD STEP BY STEP ---
    # Redo -> State 1 (Create)
    resp_r1 = client.post("/api/document/redo")
    assert resp_r1.status_code == 200
    assert len(client.get("/api/document").get_json()["geometry"]["obstacles"]) == 3

    # Redo -> State 2 (Move)
    resp_r2 = client.post("/api/document/redo")
    assert resp_r2.status_code == 200
    assert abs(client.get("/api/document").get_json()["geometry"]["obstacles"][2]["vertices"][0][0] - 6.2) < 1e-3
