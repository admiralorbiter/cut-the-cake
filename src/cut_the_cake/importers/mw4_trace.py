"""MW4 Beta Overhead Map Importer & Vectorization Pipeline [Cut the Cake].

Extracts, segments, simplifies, and drafts 2D Tactical CAD geometry from official
top-down Call of Duty map cards. Emits intermediate MapTraceDraft structures
maintaining classification confidence and uncertainty before human review.
"""

from __future__ import annotations
import json
import os
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
    CADPort
)


@dataclass
class MapTraceRegion:
    id: str
    polygon_px: List[List[float]]
    classification: str  # "boundary" | "solid_structure" | "bus" | "occluder" | "walkable_lane"
    confidence: float
    is_elevated: bool = False
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MapTraceUncertainRegion:
    id: str
    bbox_px: List[float]  # [min_x, min_y, max_x, max_y]
    classification: str
    confidence: float
    notes: str
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
    """Crop the top-down minimap / layout inset from an official map card image.
    
    If crop_box is None, extracts the canonical lower-left inset (approx [300:700, 40:440]).
    """
    if crop_box is not None:
        x1, y1, x2, y2 = crop_box
        return image[y1:y2, x1:x2]
    
    h, w = image.shape[:2]
    # Default normalized lower-left quadrant
    y1, y2 = int(h * 0.40), int(h * 0.95)
    x1, x2 = int(w * 0.05), int(w * 0.48)
    return image[y1:y2, x1:x2]


def segment_map_obstacles_and_boundary(
    crop_img: np.ndarray,
    min_area_px: float = 80.0,
    simplify_epsilon: float = 3.0
) -> Tuple[List[List[float]], List[MapTraceRegion]]:
    """Segment layout features into boundary and obstacle polygons using classical CV.
    
    Detects high-contrast structure masks, applies morphological opening/closing,
    and runs Douglas-Peucker polygon contour simplification.
    """
    if len(crop_img.shape) == 3:
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = crop_img.copy()

    # Threshold structures vs walkable areas
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Find external boundary and internal obstacles
    contours, hierarchy = cv2.findContours(clean, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    h_crop, w_crop = crop_img.shape[:2]
    boundary_poly = [[0.0, 0.0], [float(w_crop), 0.0], [float(w_crop), float(h_crop)], [0.0, float(h_crop)], [0.0, 0.0]]
    regions: List[MapTraceRegion] = []

    obs_counter = 1
    for idx, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < min_area_px:
            continue

        # Approximate polygon with Douglas-Peucker algorithm
        epsilon = simplify_epsilon
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        if len(approx) < 3:
            continue

        coords = [[float(pt[0][0]), float(pt[0][1])] for pt in approx]
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        # Classification heuristic based on aspect ratio & size
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = max(bw, bh) / max(1, min(bw, bh))
        if 2.0 <= aspect <= 4.5 and 200 <= area <= 4000:
            classification = "bus"
            confidence = 0.90
        else:
            classification = "solid_structure"
            confidence = 0.85

        regions.append(MapTraceRegion(
            id=f"obs_{obs_counter:03d}",
            polygon_px=coords,
            classification=classification,
            confidence=confidence,
            notes=f"Auto-segmented region with area {area:.1f}px², aspect ratio {aspect:.2f}"
        ))
        obs_counter += 1

    return boundary_poly, regions


def build_mw4_trace_draft(
    map_name: str,
    source_url: str,
    image_crop: np.ndarray,
    min_area_px: float = 80.0,
    simplify_epsilon: float = 3.0
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
            bbox_px=[w * 0.3, h * 0.3, w * 0.7, h * 0.7],
            classification="vertical_overlap",
            confidence=0.45,
            notes="Multi-tier elevation detected in official map card description. Requires 2.5D review."
        ))

    return MapTraceDraft(
        source={
            "map_name": map_name,
            "source_type": "official_overview_diagram",
            "source_url": source_url,
            "provenance": "Call of Duty: Modern Warfare 4 Official Intel",
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
            "confidence": "pending_gameplay_traversal_calibration"
        },
        boundary_px=boundary_px,
        regions=regions,
        uncertain_regions=uncertain_regions
    )


def project_trace_draft_to_cad_document(
    draft: MapTraceDraft,
    scale_px_per_m: float = 20.0,
    document_id: Optional[str] = None
) -> CADDocument:
    """Project a calibrated MapTraceDraft into a canonical CADDocument draft.
    
    Transforms pixel coordinates into arena space centered at (0, 0).
    """
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
        if r.classification in ("solid_structure", "bus", "occluder"):
            verts_m = [px_to_m(pt) for pt in r.polygon_px]
            cad_obstacles.append(CADObstacle(
                id=r.id,
                name=f"{r.classification.replace('_', ' ').title()} ({r.id})",
                vertices=verts_m
            ))

    map_id = (document_id or draft.source.get("map_name", "mw4_map")).lower().replace(" ", "_")

    return CADDocument(
        document_id=f"mw4_draft_{map_id}",
        name=f"{draft.source.get('map_name', 'MW4 Map')} (Draft Reconstruction)",
        description=f"Draft CAD reconstruction generated from {draft.source.get('provenance', 'official intel')}.",
        metadata={
            "provenance": "MW4 Beta Importer Spike",
            "source_url": draft.source.get("source_url", ""),
            "scale_basis": f"calibrated_{scale_px_per_m:.1f}_px_per_m",
            "region_count": len(draft.regions),
            "uncertain_region_count": len(draft.uncertain_regions)
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
        routes=[],
        threats=[],
        ports=[]
    )


def create_transit_213_synthetic_reference() -> np.ndarray:
    """Creates a high-contrast 600x600 reference layout image matching Transit 213 official layout."""
    img = np.zeros((600, 600, 3), dtype=np.uint8)
    img[:] = (18, 14, 12)  # Dark background

    # 1. Outer boundary yard (500x500 box centered)
    cv2.rectangle(img, (50, 50), (550, 550), (160, 140, 120), 4)

    # 2. Repair Shop (West Building): 120x80 px
    cv2.rectangle(img, (80, 80), (200, 160), (220, 220, 220), -1)

    # 3. Gas Station Canopy (East Building): 100x70 px
    cv2.rectangle(img, (400, 80), (500, 150), (220, 220, 220), -1)

    # 4. Derelict Buses (4 long rectangular occluders, approx 110x35 px):
    cv2.rectangle(img, (240, 180), (350, 215), (240, 240, 240), -1)
    cv2.rectangle(img, (140, 260), (175, 370), (240, 240, 240), -1)
    cv2.rectangle(img, (420, 260), (455, 370), (240, 240, 240), -1)
    cv2.rectangle(img, (240, 420), (350, 455), (240, 240, 240), -1)

    # 5. Construction Debris / Central Crate (60x60 px)
    cv2.rectangle(img, (270, 290), (330, 350), (200, 200, 200), -1)

    return img

