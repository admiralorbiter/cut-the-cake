# Tactical CAD & Scientific Core Walkthrough

---

## 1. Tactical CAD Milestone 2C (M2C) — Gray-Box Obstacle Authoring & Document History

### Milestone 2C Summary
Milestone 2C establishes **Cut the Cake** as an interactive gray-box level editor where geometric authoring directly drives real-time downstream tactical analysis while maintaining authoritative server-side snapshot history:

1. **Authoritative Python Geometry Engine (`src/cut_the_cake/cad_adapter.py`)**:
   - `create_rectangle_obstacle`: Monotonic stable unique ID generation (`wall_001`, `wall_002`...), enforces minimum dimension ($\ge 0.10\,\text{m}$), runs fail-closed boundary and clearance validation against routes, threats, and ports.
   - `resize_rectangle_obstacle`: Corner handle resizing (`nw`, `ne`, `se`, `sw`) with pinned opposite anchor and dimension bounds checking.
   - `rotate_obstacle_in_document`: Centroid-anchored affine polygon rotation preserving exact obstacle centroid and area.
   - `delete_obstacle_in_document`: Obstacle removal permitting valid 0-obstacle environments.
2. **Server-Side Snapshot History Stack (`src/cut_the_cake/cad_server.py`)**:
   - `undo_stack` & `redo_stack` (capped at 100 snapshots).
   - Every committed mutation pushes the prior working document to `undo_stack` and clears `redo_stack`.
   - Dedicated REST endpoints:
     - `POST /api/document/create_obstacle`
     - `POST /api/document/translate_obstacle`
     - `POST /api/document/resize_obstacle`
     - `POST /api/document/rotate_obstacle`
     - `POST /api/document/delete_obstacle`
     - `POST /api/document/undo`
     - `POST /api/document/redo`
3. **Interactive Workbench UI (`cad/web/`)**:
   - **Left Authoring Toolbar**:
     - `↖ Select` (`V` / `Escape`)
     - `▭ Wall` (`R`)
     - `↶ Undo` (`Ctrl+Z`)
     - `↷ Redo` (`Ctrl+Y` / `Ctrl+Shift+Z`)
     - `🗑 Delete` (`Delete` / `Backspace`)
   - **Visual Transform Handles**:
     - 4 Corner Resize handles ($\square$) with live width $\times$ height dimension labels.
     - 1 Top Rotation handle ($\circlearrowright$ on stem) with $5^\circ$ snap (continuous with Shift).
     - Live rubber-band rectangle drag preview in Wall mode.
   - **Obstacle Inspector Sidebar Card**:
     - Real-time Center $(X, Y)$, Dimensions $(W \times H)$, and Rotation Angle ($\theta^\circ$).

---

## 2. MW4 Beta Map Import Spike (Transit 213)

### Automated Pipeline Architecture (`src/cut_the_cake/importers/mw4_trace.py`)
- **Official Layout Inset Acquisition**: Automated extraction from official top-down minimap diagrams.
- **Classical CV Segmentation**: Color segmentation, morphological cleanup, contour extraction, and Douglas–Peucker polygon simplification (no LLM-fabricated coordinate hallucinations).
- **`MapTraceDraft` Intermediate Schema**: Preserves region classification, confidence scores, and explicitly flagged uncertain/elevated areas before human CAD review.
- **Traversal-Time Scale Calibration**: Explicitly documents provenance (`uncalibrated_pixels` or `traversal_time_calibrated` based on recorded player traversal seconds).

### Beta 6v6 Map Complexity & 2D Applicability Matrix

| Map | Complexity | 2D Planar Confidence | Geometry Character |
| :--- | :---: | :---: | :--- |
| **Transit 213** | ★ | **HIGH** | Planar bus depot; 4 rectangular buses, perimeter yard, gas station, repair shop. |
| **Silkworm** | ★★ | **HIGH** | Ground-level shopping district, tight alleys, storefront interiors. |
| **Lithium** | ★★–★★★ | **MEDIUM** | Industrial refinery with catwalks, heavy tanks, and interactive doors. |
| **Cachette** | ★★★ | **MEDIUM** | Rail terminal with wine warehouse, stacked containers, modest roof access. |
| **Lotus** | ★★★★ | **LOW-MEDIUM** | Lakeside hotel with second-floor balconies, courtyards, shallow water canals. |
| **Rooftops** | ★★★★★ | **LOW** | Skyscraper rooftops with high vertical disparity; benchmark case for M6 (2.5D). |

### Transit 213 Extraction Results (`imports/mw4_beta/transit_213/trace_draft.json`)
```
[1] Processed reference overhead diagram: imports/mw4_beta/transit_213/overhead_crop.png
[2] Emitted MapTraceDraft with 9 segmented regions -> imports/mw4_beta/transit_213/trace_draft.json
    - Region obs_001: solid_structure (confidence: 0.85, vertices: 5)
    - Region obs_002: solid_structure (confidence: 0.85, vertices: 5)
    - Region obs_003: solid_structure (confidence: 0.85, vertices: 5)
    - Region obs_004: solid_structure (confidence: 0.85, vertices: 5)
    - Region obs_005: solid_structure (confidence: 0.85, vertices: 5)
    - Region obs_006: solid_structure (confidence: 0.85, vertices: 5)
    - Region obs_007: solid_structure (confidence: 0.85, vertices: 5)
    - Region obs_008: solid_structure (confidence: 0.85, vertices: 5)
    - Region obs_009: solid_structure (confidence: 0.85, vertices: 5)
[3] Projected to CADDocument draft:
    - Document ID: mw4_draft_transit_213
    - Obstacles: 9
    - Boundary: 5 vertices
```

---

## 3. Full Verification Suite (120 / 120 Passed)

```powershell
pytest tests/ -v
======================= 120 passed in 63.23s (0:01:03) ========================
```
- **80 / 80** Frozen Scientific Core & ViZDoom Tests (`round11.4a-freeze`)
- **17 / 17** `CADDocument` Schema, Upload/Analyze Endpoints, Route Speed Overrides, Structured Diagnostics, and Fail-Closed Validation Tests (`tests/test_cad_document.py`)
- **8 / 8** Tactical CAD Adapter & Server Session Tests (`tests/test_cad_adapter.py`)
- **8 / 8** Scene Manifest Timing & Provenance Parity Tests (`tests/test_cad_manifest.py`)
- **5 / 5** Gray-Box Obstacle Authoring & Server History Tests (`tests/test_cad_authoring.py`)
- **2 / 2** MW4 Beta Importer & Vectorization Pipeline Tests (`tests/test_mw4_importer.py`)
