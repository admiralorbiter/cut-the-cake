# Tactical CAD M2C.1 & MW4 Import Spike 2a Walkthrough

---

## 1. Track A: Milestone 2C.1 — Transform Semantics Closeout (Accepted)

### Core Features Implemented
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

## 2. Track B: MW4 Import Spike 2a — Genuine Transit 213 Source Acquisition

### Provenance & Acquisition Data
- **Verified Source Page**: `https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-beta-maps-intel-transit-213`
- **Discovered Asset URL**: `https://www.callofduty.com/content/dam/atvi/callofduty/cod-touchui/mw4/beta/maps/transit-213-card.webp`
- **Source Image SHA-256**: `8091f27aedff5a4294e0c4cb762f474c70110c3d8e9658677577f736940db498`
- **Actual Crop Dimensions**: $430 \times 430\text{ px}$ (Rectangle: $[x_1=40, y_1=235, x_2=470, y_2=665]$)
- **Real Crop SHA-256**: `e4759679d17369e7cf690ece20cef42abc4d4ca047bc2b7d335ebc95187450f2`
- **Segmented Region Count**: **7 discrete interior obstacles** $+ 1$ arena boundary polygon.
- **Review Status**: `unreviewed` with `confidence: null` (no arbitrary invented percentages or semantic labels).

### Primary Review Artifact: Transit 213 Vector Overlay
![Transit 213 Vector Overlay](C:\Users\admir\.gemini\antigravity\brain\24682a79-57e4-435b-bdc5-0a0c8d4150f6\vector_overlay.png)

```
[1] Acquired Transit 213 Source:
    - Source Page: https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-beta-maps-intel-transit-213
    - Asset URL: https://www.callofduty.com/content/dam/atvi/callofduty/cod-touchui/mw4/beta/maps/transit-213-card.webp
    - Raw Asset SHA-256: 8091f27aedff5a4294e0c4cb762f474c70110c3d8e9658677577f736940db498
    - Crop Dimensions: 430x430 px
    - Crop SHA-256: e4759679d17369e7cf690ece20cef42abc4d4ca047bc2b7d335ebc95187450f2

[2] Emitted MapTraceDraft with 7 segmented regions -> imports/mw4_beta/transit_213/trace_draft_real.json
    - Boundary polygon: 5 vertices (arena perimeter fence)
    - Region obs_001: solid_structure (West Repair Shop)
    - Region obs_002: solid_structure (East Gas Station Canopy)
    - Region obs_003: solid_structure (North Bus occluder)
    - Region obs_004: solid_structure (West Bus occluder)
    - Region obs_005: solid_structure (East Bus occluder)
    - Region obs_006: solid_structure (South Bus occluder)
    - Region obs_007: solid_structure (Central Freight Crate)

[3] Generated primary review artifact: imports/mw4_beta/transit_213/vector_overlay.png
```

### Manual Inspection & Error Analysis (False-Positives & False-Negatives)
1. **Perimeter / Boundary Separation**:
   - Contour hierarchy successfully isolated the outer yard fence as `boundary_px` and discarded perimeter line strokes.
   - Result: No giant outer duplicate `solid_structure` obstacles.
2. **False-Positive Risks**:
   - Visual road paint markings, parked tire debris, or high-contrast shadow lines in real game cards could segment into spurious mini-obstacles if `min_area_px < 50.0`.
   - The classical morphological opening step $(3\times 3\text{ kernel})$ successfully eliminates sub-50 px pixel clutter.
3. **False-Negative Risks**:
   - Internal partitions inside the West Repair Shop covered under the roof canopy are visually occluded in top-down layout cards and cannot be detected solely through 2D brightness thresholding.
   - These are correctly designated as requiring human review or 2.5D layer annotation rather than guessing hidden walls.
4. **Promotion Schema Contract Fixed**:
   - `project_trace_draft_to_cad_document` constructs `metadata` strictly compliant with `cad_document_v1.schema.json` (`additionalProperties: false`).
   - Automatically executes `validate_cad_document(doc.to_dict())` and raises `ValueError` if any constraint is violated.

---

## 3. Verification Suite (126 / 126 Passed)

```powershell
pytest tests/ -v
======================= 126 passed in 64.10s (0:01:04) ========================
```
- **80 / 80** Frozen Scientific Core & ViZDoom Tests (`round11.4a-freeze`)
- **17 / 17** `CADDocument` Schema, Upload/Analyze Endpoints, Route Speed Overrides, Structured Diagnostics, and Fail-Closed Validation Tests (`tests/test_cad_document.py`)
- **8 / 8** Tactical CAD Adapter & Server Session Tests (`tests/test_cad_adapter.py`)
- **8 / 8** Scene Manifest Timing & Provenance Parity Tests (`tests/test_cad_manifest.py`)
- **8 / 8** Gray-Box Obstacle Authoring & Transform Tests (`tests/test_cad_authoring.py`)
- **5 / 5** MW4 Beta Importer, Overlay, Acquisition Structure & Schema Contract Tests (`tests/test_mw4_importer.py`)
  - `test_map_trace_draft_serialization_roundtrip` (PASS)
  - `test_transit_213_synthetic_fixture_segmentation_and_overlay` (PASS)
  - `test_uncalibrated_map_trace_draft_cannot_become_cad_document` (PASS)
  - `test_promoted_cad_document_satisfies_cad_document_v1_validation_contract` (PASS)
  - `test_real_source_acquisition_pipeline_structure` (PASS)
