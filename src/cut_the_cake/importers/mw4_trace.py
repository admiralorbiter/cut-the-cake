"""MW4 Beta Overhead Map Importer & Vectorization Pipeline [Cut the Cake].

Extracts, segments, simplifies, and drafts 2D Tactical CAD geometry from official
top-down Call of Duty map cards. Emits intermediate MapTraceDraft structures
maintaining classification confidence and uncertainty before human review.
"""

from __future__ import annotations
import json
import os
import hashlib
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2

from ..cad_document import (
    CADDocument,
    CADObstacle,
    CADRoute,
    CADThreat,
    CADPlayerModel,
    CADPort,
    validate_cad_document
)


@dataclass
class MapTraceRegion:
    id: str
    polygon_px: List[List[float]]
    classification: str  # "boundary" | "solid_structure" | "occluder" | "walkable_lane"
    confidence: Optional[float] = None
    review_status: str = "unreviewed"  # "unreviewed" | "verified" | "rejected"
    is_elevated: bool = False
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MapTraceUncertainRegion:
    id: str
    bbox_px: List[float]  # [min_x, min_y, max_x, max_y]
    classification: str
    confidence: Optional[float] = None
    review_status: str = "unreviewed"
    notes: str = ""
    needs_review: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MapTraceDraft:
    schema_version: str = "map_trace_draft_v1"
    source: Dict[str, Any] = field(default_factory=dict)
    image_transform: Dict[str, Any] = field(default_factory=dict)
    calibration: Dict[str, Any] = field(default_factory=dict)
    boundary_px: List[List[float]] = field(default_factory=list)
    regions: List[MapTraceRegion] = field(default_factory=list)
    uncertain_regions: List[MapTraceUncertainRegion] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source": self.source,
            "image_transform": self.image_transform,
            "calibration": self.calibration,
            "boundary_px": self.boundary_px,
            "regions": [r.to_dict() for r in self.regions],
            "uncertain_regions": [u.to_dict() for u in self.uncertain_regions]
        }

    def save_json(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: str) -> MapTraceDraft:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        regions = [MapTraceRegion(**r) for r in data.get("regions", [])]
        uncertain = [MapTraceUncertainRegion(**u) for u in data.get("uncertain_regions", [])]
        return cls(
            schema_version=data.get("schema_version", "map_trace_draft_v1"),
            source=data.get("source", {}),
            image_transform=data.get("image_transform", {}),
            calibration=data.get("calibration", {}),
            boundary_px=data.get("boundary_px", []),
            regions=regions,
            uncertain_regions=uncertain
        )


def crop_overhead_diagram(image: np.ndarray, crop_box: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
    """Crop the top-down minimap / layout inset from an official map card image."""
    if crop_box is not None:
        x1, y1, x2, y2 = crop_box
        return image[y1:y2, x1:x2]
    
    h, w = image.shape[:2]
    # Canonical lower-left quadrant crop
    y1, y2 = int(h * 0.40), int(h * 0.95)
    x1, x2 = int(w * 0.05), int(w * 0.48)
    return image[y1:y2, x1:x2]


def segment_map_obstacles_and_boundary(
    crop_img: np.ndarray,
    min_area_px: float = 60.0,
    simplify_epsilon: float = 2.5
) -> Tuple[List[List[float]], List[MapTraceRegion]]:
    """Segment layout features into external boundary and interior obstacle polygons.
    
    Filters contour hierarchy so the outer arena boundary is isolated and NOT emitted
    as giant solid structure obstacles.
    """
    if len(crop_img.shape) == 3:
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = crop_img.copy()

    h_crop, w_crop = gray.shape[:2]
    total_area = float(h_crop * w_crop)

    # Threshold structures vs walkable floor
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Find external boundary and interior obstacles using contour tree hierarchy
    contours, hierarchy = cv2.findContours(clean, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    boundary_poly = [[0.0, 0.0], [float(w_crop), 0.0], [float(w_crop), float(h_crop)], [0.0, float(h_crop)], [0.0, 0.0]]
    regions: List[MapTraceRegion] = []

    if contours is None or len(contours) == 0:
        return boundary_poly, regions

    # 1. Identify outermost boundary contour (largest area > 0.40 * total_area)
    boundary_idx = -1
    max_area = 0.0
    for idx, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 0.40 * total_area and area > max_area:
            max_area = area
            boundary_idx = idx

    if boundary_idx >= 0:
        approx_b = cv2.approxPolyDP(contours[boundary_idx], simplify_epsilon * 1.5, True)
        if len(approx_b) >= 3:
            b_coords = [[float(pt[0][0]), float(pt[0][1])] for pt in approx_b]
            if b_coords[0] != b_coords[-1]:
                b_coords.append(b_coords[0])
            boundary_poly = b_coords

    # 2. Extract interior obstacles (excluding boundary and enclosing perimeter shells)
    obs_counter = 1
    for idx, cnt in enumerate(contours):
        if idx == boundary_idx:
            continue

        area = cv2.contourArea(cnt)
        # Skip small noise and giant enclosing boundary outlines
        if area < min_area_px or area > 0.35 * total_area:
            continue

        # Approximate polygon with Douglas-Peucker algorithm
        approx = cv2.approxPolyDP(cnt, simplify_epsilon, True)
        if len(approx) < 3:
            continue

        coords = [[float(pt[0][0]), float(pt[0][1])] for pt in approx]
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = max(bw, bh) / max(1, min(bw, bh))

        classification = "solid_structure"
        regions.append(MapTraceRegion(
            id=f"obs_{obs_counter:03d}",
            polygon_px=coords,
            classification=classification,
            confidence=None,
            review_status="unreviewed",
            notes=f"Auto-segmented region (area: {area:.1f}px², aspect: {aspect:.2f})"
        ))
        obs_counter += 1

    return boundary_poly, regions


def render_vector_overlay(
    crop_img: np.ndarray,
    draft: MapTraceDraft,
    out_path: Optional[str] = None
) -> np.ndarray:
    """Renders the extracted boundary and obstacle vector polygons directly over the source image."""
    overlay = crop_img.copy()
    if len(overlay.shape) == 2:
        overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)

    # 1. Draw boundary in bright cyan
    if draft.boundary_px and len(draft.boundary_px) >= 3:
        b_pts = np.array(draft.boundary_px, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(overlay, [b_pts], isClosed=True, color=(255, 200, 0), thickness=2)

    # 2. Draw obstacles in bright green with alpha tint
    mask = overlay.copy()
    alpha = 0.35
    for r in draft.regions:
        pts = np.array(r.polygon_px, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask, [pts], color=(0, 230, 120))
        cv2.polylines(overlay, [pts], isClosed=True, color=(0, 255, 180), thickness=2)

        # Label centroid
        m = cv2.moments(pts)
        if m["m00"] > 0:
            cx = int(m["m10"] / m["m00"])
            cy = int(m["m01"] / m["m00"])
            cv2.putText(overlay, r.id, (cx - 15, cy + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.addWeighted(mask, alpha, overlay, 1 - alpha, 0, overlay)

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        cv2.imwrite(out_path, overlay)

    return overlay


def build_mw4_trace_draft(
    map_name: str,
    source_url: str,
    image_crop: np.ndarray,
    min_area_px: float = 60.0,
    simplify_epsilon: float = 2.5,
    provenance: str = "Call of Duty: Modern Warfare 4 Official Intel"
) -> MapTraceDraft:
    """End-to-end builder extracting a MapTraceDraft from an overhead diagram image."""
    boundary_px, regions = segment_map_obstacles_and_boundary(
        crop_img=image_crop,
        min_area_px=min_area_px,
        simplify_epsilon=simplify_epsilon
    )

    h, w = image_crop.shape[:2]

    # Mark potential ambiguous/elevated zones
    uncertain_regions = []
    if "rooftops" in map_name.lower() or "lotus" in map_name.lower():
        uncertain_regions.append(MapTraceUncertainRegion(
            id="unc_001",
            bbox_px=[float(w * 0.3), float(h * 0.3), float(w * 0.7), float(h * 0.7)],
            classification="vertical_overlap",
            confidence=None,
            review_status="unreviewed",
            notes="Multi-tier elevation detected in official map card description. Requires 2.5D review."
        ))

    return MapTraceDraft(
        source={
            "map_name": map_name,
            "source_type": "official_overview_diagram",
            "source_url": source_url,
            "provenance": provenance,
            "confidence": "reference_reconstruction"
        },
        image_transform={
            "width_px": w,
            "height_px": h,
            "crop_origin": "lower_left_diagram_inset",
            "rotation_deg": 0.0
        },
        calibration={
            "scale_basis": "uncalibrated_pixels",
            "px_per_meter": None,
            "calibration_method": None,
            "confidence": "uncalibrated"
        },
        boundary_px=boundary_px,
        regions=regions,
        uncertain_regions=uncertain_regions
    )


def project_trace_draft_to_cad_document(
    draft: MapTraceDraft,
    calibration: Optional[Dict[str, Any]] = None,
    routes: Optional[List[CADRoute]] = None,
    threats: Optional[List[CADThreat]] = None,
    ports: Optional[List[CADPort]] = None,
    document_id: Optional[str] = None
) -> CADDocument:
    """Project a calibrated MapTraceDraft into a canonical CADDocument.
    
    Strictly requires explicit calibration (px_per_meter > 0) and at least one authored route
    to satisfy the cad_document_v1 schema contract. Uncalibrated drafts cannot become CADDocuments.
    """
    calib = calibration or draft.calibration
    px_per_m = calib.get("px_per_meter") if calib else None
    if px_per_m is None or float(px_per_m) <= 0.0:
        raise ValueError(
            "Cannot promote uncalibrated MapTraceDraft to CADDocument. "
            "Explicit scale calibration (px_per_meter > 0) is required."
        )

    scale_px_per_m = float(px_per_m)

    if not routes or len(routes) == 0:
        raise ValueError(
            "Cannot create valid CADDocument without at least one authored route "
            "(cad_document_v1 schema requirement)."
        )

    # Centering transformation
    b_pts = np.array(draft.boundary_px)
    min_x, min_y = np.min(b_pts, axis=0)
    max_x, max_y = np.max(b_pts, axis=0)
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0

    def px_to_m(pt: List[float]) -> List[float]:
        mx = (pt[0] - cx) / scale_px_per_m
        my = -(pt[1] - cy) / scale_px_per_m  # Invert Y
        return [round(float(mx), 3), round(float(my), 3)]

    cad_boundary = [px_to_m(pt) for pt in draft.boundary_px]

    cad_obstacles = []
    for r in draft.regions:
        if r.classification in ("solid_structure", "occluder", "bus"):
            verts_m = [px_to_m(pt) for pt in r.polygon_px]
            cad_obstacles.append(CADObstacle(
                id=r.id,
                name=f"{r.classification.replace('_', ' ').title()} ({r.id})",
                vertices=verts_m
            ))

    map_id = (document_id or draft.source.get("map_name", "mw4_map")).lower().replace(" ", "_")

    doc = CADDocument(
        document_id=f"mw4_draft_{map_id}",
        name=f"{draft.source.get('map_name', 'MW4 Map')} (Calibrated Reconstruction)",
        description=f"CAD reconstruction generated from {draft.source.get('provenance', 'official intel')}.",
        metadata={
            "provenance": f"MW4 Beta Importer ({draft.source.get('map_name', 'MW4')})",
            "author": "Cut the Cake MW4 Importer",
            "family": "mw4_reconstruction",
            "tags": ["mw4_beta", "calibrated"]
        },
        units={"coordinates": "meters", "angles": "degrees", "time": "seconds"},
        player_model=CADPlayerModel(
            v_move_mps=4.5,
            omega_slew_deg_per_s=360.0,
            acquisition_latency_s=0.15,
            service_duration_s=0.10,
            initial_reticle_deg=0.0
        ),
        boundary=cad_boundary,
        obstacles=cad_obstacles,
        routes=routes or [],
        threats=threats or [],
        ports=ports or []
    )

    is_valid, errors = validate_cad_document(doc.to_dict())
    if not is_valid:
        raise ValueError(f"Promoted CADDocument failed validation contract: {errors}")

    return doc


def create_synthetic_test_card() -> np.ndarray:
    """Creates a 600x600 synthetic map card fixture for automated importer tests."""
    img = np.zeros((600, 600, 3), dtype=np.uint8)
    img[:] = (18, 14, 12)

    # Outer yard boundary
    cv2.rectangle(img, (50, 50), (550, 550), (160, 140, 120), 4)

    # Repair Shop: 120x80 px
    cv2.rectangle(img, (80, 80), (200, 160), (220, 220, 220), -1)

    # Gas Station Canopy: 100x70 px
    cv2.rectangle(img, (400, 80), (500, 150), (220, 220, 220), -1)

    # 4 Buses
    cv2.rectangle(img, (240, 180), (350, 215), (240, 240, 240), -1)
    cv2.rectangle(img, (140, 260), (175, 370), (240, 240, 240), -1)
    cv2.rectangle(img, (420, 260), (455, 370), (240, 240, 240), -1)
    cv2.rectangle(img, (240, 420), (350, 455), (240, 240, 240), -1)

    # Central Crate
    cv2.rectangle(img, (270, 290), (330, 350), (200, 200, 200), -1)

    return img


def create_transit_213_synthetic_fixture() -> np.ndarray:
    """Creates a 480x480 synthetic layout fixture for offline deterministic CV unit tests.
    
    NOTE: This is a synthetic geometric test fixture drawn with OpenCV primitives,
    NOT the genuine downloaded official asset. Genuine assets are acquired via scripts/import_mw4_map.py.
    """
    img = np.zeros((480, 480, 3), dtype=np.uint8)
    img[:] = (22, 18, 16)  # Dark gravel canvas

    # Outer perimeter boundary fence (400x400 centered)
    cv2.rectangle(img, (40, 40), (440, 440), (120, 100, 80), 2)

    # 1. West Repair Shop: 90x65 px
    cv2.rectangle(img, (60, 60), (150, 125), (200, 200, 200), -1)

    # 2. East Gas Station Canopy: 80x55 px
    cv2.rectangle(img, (320, 65), (400, 120), (200, 200, 200), -1)

    # 3. Four Abandoned Derelict Buses (approx 85x30 px each):
    cv2.rectangle(img, (195, 140), (285, 170), (220, 220, 220), -1)
    cv2.rectangle(img, (110, 210), (140, 295), (220, 220, 220), -1)
    cv2.rectangle(img, (340, 210), (370, 295), (220, 220, 220), -1)
    cv2.rectangle(img, (195, 335), (285, 365), (220, 220, 220), -1)

    # 4. Central Crate / Freight Obstacle (50x50 px)
    cv2.rectangle(img, (215, 230), (265, 280), (180, 180, 180), -1)

    return img


def load_or_fetch_transit_source_asset(
    out_dir: str,
    allow_network: bool = True
) -> Tuple[np.ndarray, str, Dict[str, Any]]:
    """Acquires genuine Transit 213 overview card and extracts the layout crop.
    
    Strictly fail-closed: If genuine bytes are not in local cache and cannot be downloaded,
    raises RuntimeError('REAL SOURCE UNAVAILABLE'). Never synthesizes or manufactures pixels.
    """
    meta_path = os.path.join(out_dir, "source.json")
    meta: Dict[str, Any] = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    official_meta = meta.get("official_metadata", {})
    source_page = official_meta.get(
        "source_page_url",
        "https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-beta-weekend-one-intel"
    )
    asset_url = official_meta.get(
        "exact_image_asset_url",
        "https://imgs.callofduty.com/content/dam/atvi/callofduty/cod-touchui/blog/body/mw4/beta-weekend-one/MW4-BETA-WEEKEND-ONE-017.webp"
    )

    raw_path = os.path.join(out_dir, "raw_map_card.png")
    raw_webp_path = os.path.join(out_dir, "raw_map_card.webp")

    # 1. Attempt local cache load
    raw_bytes: Optional[bytes] = None
    if os.path.exists(raw_path):
        with open(raw_path, "rb") as f:
            raw_bytes = f.read()
    elif os.path.exists(raw_webp_path):
        with open(raw_webp_path, "rb") as f:
            raw_bytes = f.read()

    # 2. Attempt network fetch if allowed and cache missing
    if raw_bytes is None and allow_network:
        try:
            import requests
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CutTheCake/1.0"}
            resp = requests.get(asset_url, headers=headers, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 1000:
                raw_bytes = resp.content
                # Cache raw asset
                with open(raw_webp_path, "wb") as f:
                    f.write(raw_bytes)
        except Exception as e:
            raw_bytes = None

    # 3. Strict fail-closed: NO synthetic fallbacks in real path
    if raw_bytes is None:
        raise RuntimeError(
            "REAL SOURCE UNAVAILABLE: Genuine Transit 213 source bytes could not be retrieved from "
            f"local cache ('{raw_path}') or network ('{asset_url}')."
        )

    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    # Decode image
    from PIL import Image
    import io
    pil_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    full_card = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # 4. Crop overhead layout diagram
    # Genuine MW4 1080p card: lower-left quadrant [y: 480->1020, x: 60->600]
    crop_rect = (60, 480, 600, 1020)  # (x1, y1, x2, y2)
    h_full, w_full = full_card.shape[:2]
    x1, y1, x2, y2 = crop_rect
    x1 = max(0, min(x1, w_full))
    x2 = max(0, min(x2, w_full))
    y1 = max(0, min(y1, h_full))
    y2 = max(0, min(y2, h_full))
    crop_img = full_card[y1:y2, x1:x2]

    crop_path = os.path.join(out_dir, "transit_minimap_crop.png")
    cv2.imwrite(crop_path, crop_img)

    with open(crop_path, "rb") as f:
        crop_bytes = f.read()
    crop_sha256 = hashlib.sha256(crop_bytes).hexdigest()

    provenance_info = {
        "source_page_url": source_page,
        "exact_image_asset_url": asset_url,
        "raw_asset_sha256": raw_sha256,
        "crop_rectangle": list(crop_rect),
        "crop_dimensions": [int(crop_img.shape[1]), int(crop_img.shape[0])],
        "crop_sha256": crop_sha256
    }
    return crop_img, crop_path, provenance_info


def run_segmentation_sensitivity_sweep(
    crop_img: np.ndarray,
    thresholds: Optional[List[int]] = None,
    kernel_sizes: Optional[List[int]] = None,
    epsilons: Optional[List[float]] = None,
    min_areas: Optional[List[float]] = None
) -> Dict[str, Any]:
    """Automated sensitivity sweep measuring classical CV vectorization stability across parameter space."""
    ths = thresholds or [40, 50, 60, 70, 80]
    ks = kernel_sizes or [3, 5]
    eps = epsilons or [1.5, 2.0, 2.5, 3.0, 3.5]
    mas = min_areas or [40.0, 60.0, 80.0, 100.0]

    total_runs = len(ths) * len(ks) * len(eps) * len(mas)
    region_counts: List[int] = []
    run_records: List[Dict[str, Any]] = []

    for t in ths:
        for k in ks:
            for ep in eps:
                for ma in mas:
                    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY) if len(crop_img.shape) == 3 else crop_img.copy()
                    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                    _, thresh = cv2.threshold(blurred, t, 255, cv2.THRESH_BINARY)
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
                    clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
                    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel, iterations=1)
                    cnts, _ = cv2.findContours(clean, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                    h_c, w_c = gray.shape[:2]
                    tot_a = float(h_c * w_c)
                    valid_obs = 0
                    for c in (cnts or []):
                        a = cv2.contourArea(c)
                        if ma <= a <= 0.35 * tot_a:
                            approx = cv2.approxPolyDP(c, ep, True)
                            if len(approx) >= 3:
                                valid_obs += 1

                    region_counts.append(valid_obs)
                    run_records.append({
                        "threshold": t,
                        "kernel_size": k,
                        "epsilon": ep,
                        "min_area": ma,
                        "obstacle_count": valid_obs
                    })

    counts_arr = np.array(region_counts)
    median_count = int(np.median(counts_arr))
    stability_pct = float((counts_arr == median_count).mean() * 100.0)

    return {
        "total_evaluations": total_runs,
        "min_regions": int(counts_arr.min()),
        "max_regions": int(counts_arr.max()),
        "mean_regions": float(counts_arr.mean()),
        "median_regions": median_count,
        "modal_stability_pct": round(stability_pct, 2),
        "parameter_ranges": {
            "thresholds": ths,
            "kernel_sizes": ks,
            "epsilons": eps,
            "min_areas": mas
        }
    }

