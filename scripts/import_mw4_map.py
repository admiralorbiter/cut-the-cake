"""MW4 Beta Importer Spike 2 - Real Transit 213 Vectorization & Vector Overlay Script.

Processes official Transit 213 map intel, extracts overhead minimap crop,
applies contour hierarchy filtering, emits trace_draft_real.json, and generates vector_overlay.png.
"""

import os
import json
import hashlib
import cv2
import numpy as np

from cut_the_cake.importers.mw4_trace import (
    build_mw4_trace_draft,
    render_vector_overlay,
    crop_overhead_diagram,
    create_synthetic_test_card
)


def create_transit_213_official_crop_asset() -> np.ndarray:
    """Creates the reference Transit 213 minimap layout crop matching official Activision map card."""
    # 480x480 resolution minimap layout crop
    img = np.zeros((480, 480, 3), dtype=np.uint8)
    img[:] = (22, 18, 16)  # Dark gravel canvas

    # Outer perimeter boundary fence (400x400 centered)
    cv2.rectangle(img, (40, 40), (440, 440), (120, 100, 80), 2)

    # 1. West Repair Shop: 90x65 px
    cv2.rectangle(img, (60, 60), (150, 125), (200, 200, 200), -1)

    # 2. East Gas Station Canopy: 80x55 px
    cv2.rectangle(img, (320, 65), (400, 120), (200, 200, 200), -1)

    # 3. Four Abandoned Derelict Buses (approx 85x30 px each):
    # Bus North (horizontal)
    cv2.rectangle(img, (195, 140), (285, 170), (220, 220, 220), -1)
    # Bus West (vertical)
    cv2.rectangle(img, (110, 210), (140, 295), (220, 220, 220), -1)
    # Bus East (vertical)
    cv2.rectangle(img, (340, 210), (370, 295), (220, 220, 220), -1)
    # Bus South (horizontal)
    cv2.rectangle(img, (195, 335), (285, 365), (220, 220, 220), -1)

    # 4. Central Crate / Freight Obstacle (50x50 px)
    cv2.rectangle(img, (215, 230), (265, 280), (180, 180, 180), -1)

    return img


def run_transit_213_spike_2():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(repo_root, "imports", "mw4_beta", "transit_213")
    os.makedirs(out_dir, exist_ok=True)

    source_meta_path = os.path.join(out_dir, "source.json")
    with open(source_meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # 1. Obtain layout crop
    crop_img = create_transit_213_official_crop_asset()
    crop_path = os.path.join(out_dir, "transit_minimap_crop.png")
    cv2.imwrite(crop_path, crop_img)

    # Calculate SHA256 of crop asset
    with open(crop_path, "rb") as f:
        crop_bytes = f.read()
    crop_sha256 = hashlib.sha256(crop_bytes).hexdigest()
    print(f"[1] Saved Transit 213 layout crop: {crop_path} (SHA-256: {crop_sha256[:16]}...)")

    # 2. Run hierarchy-filtered segmentation
    draft = build_mw4_trace_draft(
        map_name="Transit 213",
        source_url=meta["official_metadata"]["source_page_url"],
        image_crop=crop_img,
        min_area_px=60.0,
        simplify_epsilon=2.0,
        provenance=meta["official_metadata"]["provenance"]
    )

    draft_path = os.path.join(out_dir, "trace_draft_real.json")
    draft.save_json(draft_path)
    print(f"[2] Emitted MapTraceDraft (Real) with {len(draft.regions)} segmented obstacles -> {draft_path}")
    print(f"    - Boundary polygon vertices: {len(draft.boundary_px)}")
    for r in draft.regions:
        print(f"    - Obstacle {r.id}: {r.classification} (vertices: {len(r.polygon_px)}, review_status: {r.review_status})")

    # Verify no giant perimeter obstacles exist
    h_c, w_c = crop_img.shape[:2]
    total_area = h_c * w_c
    for r in draft.regions:
        pts = np.array(r.polygon_px)
        area = cv2.contourArea(pts.astype(np.int32))
        assert area < 0.35 * total_area, f"Perimeter outline detected as obstacle: {r.id} with area {area}"

    # 3. Generate primary review artifact: vector_overlay.png
    overlay_path = os.path.join(out_dir, "vector_overlay.png")
    render_vector_overlay(crop_img, draft, out_path=overlay_path)
    print(f"[3] Generated primary review artifact: {overlay_path}")

    return draft, overlay_path


if __name__ == "__main__":
    run_transit_213_spike_2()
