# Tactical CAD M2C.1 & MW4 Import Spike 2 Walkthrough

---

## 1. Track A: Milestone 2C.1 — Transform Semantics Closeout

### Changes Implemented
1. **Monotonic Session Wall ID Allocation (`src/cut_the_cake/cad_adapter.py`, `src/cut_the_cake/cad_server.py`)**:
   - `active_state["next_wall_sequence"]` maintains a monotonic sequence counter across the entire editor session.
   - Deleting an obstacle and creating a new one advances the sequence (e.g. `wall_001` deleted $\to$ next wall allocated is `wall_002`, never reusing `wall_001`).
   - Undo/Redo operations traverse history without decrementing or corrupting the allocation counter.
2. **Explicit Rotation Semantics**:
   - `rotate_obstacle_in_document` supports both `target_angle_deg` (absolute orientation from initial heading) and `angle_delta_deg`.
   - Repeated absolute orientation requests (e.g. rotating $20^\circ$ then setting $35^\circ$) land exactly at $35^\circ$ rather than compounding.
3. **Local Oriented Rectangle Resizing**:
   - `resize_rectangle_obstacle` projects handle displacements onto the local orthogonal basis vectors $(\mathbf{u}_1, \mathbf{u}_2)$ of the rotated polygon.
   - Resizing a rotated obstacle preserves its exact orientation angle and keeps the opposite anchor corner pinned.
   - Browser client (`cad/web/app.js`) positions resize handles directly on the 4 actual oriented vertices rather than on an axis-aligned bounding box.

---

## 2. Track B: MW4 Import Spike 2 — Real Transit 213 Source & Vector Overlay

### Real-Image Extraction & Hierarchy Filtering (`src/cut_the_cake/importers/mw4_trace.py`)
- **Contour Tree Hierarchy Isolation**:
  - The outer yard perimeter is detected and categorized as `boundary_px`.
  - Nested boundary perimeter shells are filtered out, preventing outer walls from being emitted as giant duplicate `solid_structure` obstacles.
  - Exactly **7 discrete interior obstacles** extracted: West Repair Shop, East Gas Station Canopy, 4 Derelict Buses, and Central Crate.
- **Truthful Intermediate Schema (`MapTraceDraft`)**:
  - Classification: `"solid_structure"` / `"occluder"`.
  - Confidence: `null` with `review_status: "unreviewed"` (no arbitrary made-up confidence percentages).
  - Explicit uncertain region tracking.
- **Strict CADDocument Promotion Boundary**:
  - Magic `20 px/m` default removed.
  - `project_trace_draft_to_cad_document` raises `ValueError` if `draft` is uncalibrated or if zero routes are provided.
- **Audited 6-Map Metadata (`imports/mw4_beta/*/source.json`)**:
  - Separates official Activision factual descriptions from Cut the Cake 2D suitability inferences.
  - Lotus corrected to battle-scarred Korean fishing village with tanks, docks, and water.

### Primary Review Artifact: Real Transit 213 Vector Overlay
![Transit 213 Classical CV Vector Overlay](C:\Users\admir\.gemini\antigravity\brain\24682a79-57e4-435b-bdc5-0a0c8d4150f6\vector_overlay.png)

```
[1] Saved Transit 213 layout crop: imports/mw4_beta/transit_213/transit_minimap_crop.png (SHA-256: 4ccbdf6f7c36cc07...)
[2] Emitted MapTraceDraft (Real) with 7 segmented obstacles -> imports/mw4_beta/transit_213/trace_draft_real.json
    - Boundary polygon vertices: 5
    - Obstacle obs_001: solid_structure (vertices: 5, review_status: unreviewed)
    - Obstacle obs_002: solid_structure (vertices: 5, review_status: unreviewed)
    - Obstacle obs_003: solid_structure (vertices: 5, review_status: unreviewed)
    - Obstacle obs_004: solid_structure (vertices: 5, review_status: unreviewed)
    - Obstacle obs_005: solid_structure (vertices: 5, review_status: unreviewed)
    - Obstacle obs_006: solid_structure (vertices: 5, review_status: unreviewed)
    - Obstacle obs_007: solid_structure (vertices: 5, review_status: unreviewed)
[3] Generated primary review artifact: imports/mw4_beta/transit_213/vector_overlay.png
```

---

## 3. Verification Suite (124 / 124 Passed)

```powershell
pytest tests/ -v
======================= 124 passed in 63.35s (0:01:03) ========================
```
- **80 / 80** Frozen Scientific Core & ViZDoom Tests (`round11.4a-freeze`)
- **17 / 17** `CADDocument` Schema, Upload/Analyze Endpoints, Route Speed Overrides, Structured Diagnostics, and Fail-Closed Validation Tests (`tests/test_cad_document.py`)
- **8 / 8** Tactical CAD Adapter & Server Session Tests (`tests/test_cad_adapter.py`)
- **8 / 8** Scene Manifest Timing & Provenance Parity Tests (`tests/test_cad_manifest.py`)
- **8 / 8** Gray-Box Obstacle Authoring & Transform Tests (`tests/test_cad_authoring.py`)
  - `test_monotonic_wall_id_allocation_no_reuse` (PASS)
  - `test_rotation_target_angle_and_delta_composition` (PASS)
  - `test_rotate_then_resize_preserves_orientation` (PASS)
  - `test_undo_redo_history_stack` (PASS)
- **3 / 3** MW4 Beta Importer, Overlay & Boundary Gate Tests (`tests/test_mw4_importer.py`)
  - `test_map_trace_draft_serialization_roundtrip` (PASS)
  - `test_transit_213_real_crop_segmentation_and_overlay` (PASS)
  - `test_uncalibrated_map_trace_draft_cannot_become_cad_document` (PASS)
