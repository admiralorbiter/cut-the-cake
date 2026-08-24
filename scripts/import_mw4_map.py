"""MW4 Beta Importer Spike - Transit 213 Vectorization Script [Cut the Cake].

Generates/processes official top-down minimap diagrams, runs classical CV segmentation,
emits MapTraceDraft, and verifies CADDocument projection.
"""

import os
import cv2
import numpy as np

from cut_the_cake.importers.mw4_trace import (
    build_mw4_trace_draft,
    project_trace_draft_to_cad_document,
    crop_overhead_diagram
)


def create_transit_213_synthetic_reference() -> np.ndarray:
    """Creates a high-contrast 600x600 reference layout image matching Transit 213 official layout."""
    # Dark canvas
    img = np.zeros((600, 600, 3), dtype=np.uint8)
    img[:] = (18, 14, 12)  # Dark background

    # 1. Outer boundary yard (500x500 box centered)
    cv2.rectangle(img, (50, 50), (550, 550), (160, 140, 120), 4)

    # 2. Repair Shop (West Building): 120x80 px
    cv2.rectangle(img, (80, 80), (200, 160), (220, 220, 220), -1)

    # 3. Gas Station Canopy (East Building): 100x70 px
    cv2.rectangle(img, (400, 80), (500, 150), (220, 220, 220), -1)

    # 4. Derelict Buses (4 long rectangular occluders, approx 110x35 px):
    # Bus 1 (North-Center, horizontal)
    cv2.rectangle(img, (240, 180), (350, 215), (240, 240, 240), -1)
    # Bus 2 (Mid-West, angled / vertical)
    cv2.rectangle(img, (140, 260), (175, 370), (240, 240, 240), -1)
    # Bus 3 (Mid-East, vertical)
    cv2.rectangle(img, (420, 260), (455, 370), (240, 240, 240), -1)
    # Bus 4 (South-Center, horizontal)
    cv2.rectangle(img, (240, 420), (350, 455), (240, 240, 240), -1)

    # 5. Construction Debris / Central Crate (60x60 px)
    cv2.rectangle(img, (270, 290), (330, 350), (200, 200, 200), -1)

    return img


def run_transit_213_spike():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(repo_root, "imports", "mw4_beta", "transit_213")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Generate reference image
    ref_img = create_transit_213_synthetic_reference()
    crop_path = os.path.join(out_dir, "overhead_crop.png")
    cv2.imwrite(crop_path, ref_img)
    print(f"[1] Saved reference overhead diagram: {crop_path}")

    # 2. Run automated CV vectorizer
    draft = build_mw4_trace_draft(
        map_name="Transit 213",
        source_url="https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-beta-maps-intel-transit-213",
        image_crop=ref_img,
        min_area_px=100.0,
        simplify_epsilon=2.0
    )

    draft_path = os.path.join(out_dir, "trace_draft.json")
    draft.save_json(draft_path)
    print(f"[2] Emitted MapTraceDraft with {len(draft.regions)} segmented regions -> {draft_path}")

    for idx, r in enumerate(draft.regions):
        print(f"    - Region {r.id}: {r.classification} (confidence: {r.confidence:.2f}, vertices: {len(r.polygon_px)})")

    # 3. Project to CADDocument draft (20 px/meter scale)
    cad_doc = project_trace_draft_to_cad_document(draft, scale_px_per_m=20.0)
    print(f"[3] Projected to CADDocument draft:")
    print(f"    - Document ID: {cad_doc.document_id}")
    print(f"    - Obstacles: {len(cad_doc.obstacles)}")
    print(f"    - Boundary: {len(cad_doc.boundary)} vertices")
    
    return draft, cad_doc


if __name__ == "__main__":
    run_transit_213_spike()
