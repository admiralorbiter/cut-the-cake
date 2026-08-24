"""Tests for MW4 Beta Overhead Map Importer & Vectorization Pipeline."""

import os
import json
import cv2
import numpy as np
import pytest

from cut_the_cake.importers.mw4_trace import (
    MapTraceDraft,
    MapTraceRegion,
    MapTraceUncertainRegion,
    crop_overhead_diagram,
    segment_map_obstacles_and_boundary,
    render_vector_overlay,
    build_mw4_trace_draft,
    project_trace_draft_to_cad_document,
    create_synthetic_test_card,
    create_transit_213_synthetic_fixture,
    load_or_fetch_transit_source_asset
)
from cut_the_cake.cad_document import CADRoute, validate_cad_document


def test_map_trace_draft_serialization_roundtrip(tmp_path):
    """Verify MapTraceDraft serialization and deserialization with unreviewed status."""
    draft = MapTraceDraft(
        source={
            "map_name": "Transit 213",
            "source_type": "official_overview_diagram",
            "source_url": "https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-beta-maps-intel-transit-213",
            "provenance": "Official Call of Duty Intel",
            "confidence": "reference_reconstruction"
        },
        image_transform={"width_px": 600, "height_px": 600, "rotation_deg": 0.0},
        calibration={"scale_basis": "uncalibrated_pixels", "px_per_meter": None},
        boundary_px=[[0.0, 0.0], [600.0, 0.0], [600.0, 600.0], [0.0, 600.0], [0.0, 0.0]],
        regions=[
            MapTraceRegion(
                id="obs_001",
                polygon_px=[[240.0, 180.0], [350.0, 180.0], [350.0, 215.0], [240.0, 215.0], [240.0, 180.0]],
                classification="solid_structure",
                confidence=None,
                review_status="unreviewed",
                notes="Central North Structure"
            )
        ],
        uncertain_regions=[
            MapTraceUncertainRegion(
                id="unc_001",
                bbox_px=[100.0, 100.0, 200.0, 200.0],
                classification="possible_interior",
                confidence=None,
                review_status="unreviewed",
                notes="Overhead roof occludes ground path"
            )
        ]
    )

    save_path = str(tmp_path / "test_trace_draft.json")
    draft.save_json(save_path)

    loaded = MapTraceDraft.load_json(save_path)
    assert loaded.source["map_name"] == "Transit 213"
    assert len(loaded.regions) == 1
    assert loaded.regions[0].id == "obs_001"
    assert loaded.regions[0].classification == "solid_structure"
    assert loaded.regions[0].confidence is None
    assert loaded.regions[0].review_status == "unreviewed"
    assert len(loaded.uncertain_regions) == 1


def test_transit_213_synthetic_fixture_segmentation_and_overlay(tmp_path):
    """Verify hierarchy-filtered segmentation on Transit 213 deterministic synthetic fixture."""
    crop_img = create_transit_213_synthetic_fixture()
    assert crop_img.shape == (480, 480, 3)

    draft = build_mw4_trace_draft(
        map_name="Transit 213",
        source_url="https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-beta-maps-intel-transit-213",
        image_crop=crop_img,
        min_area_px=60.0,
        simplify_epsilon=2.0
    )

    assert draft.source["map_name"] == "Transit 213"
    assert len(draft.boundary_px) >= 4
    # Exactly 7 discrete interior obstacles: 2 buildings + 4 buses + 1 crate
    assert len(draft.regions) == 7

    # Verify no perimeter outline is emitted as a giant obstacle
    total_area = 480 * 480
    for r in draft.regions:
        pts = np.array(r.polygon_px, dtype=np.int32)
        area = float(cv2.contourArea(pts))
        assert area < 0.35 * total_area, f"Perimeter outline emitted as obstacle {r.id}"

    # Verify vector overlay generation
    overlay_path = str(tmp_path / "test_overlay.png")
    overlay = render_vector_overlay(crop_img, draft, out_path=overlay_path)
    assert os.path.exists(overlay_path)
    assert overlay.shape == crop_img.shape


def test_uncalibrated_map_trace_draft_cannot_become_cad_document():
    """Verify that an uncalibrated MapTraceDraft cannot silently become a CADDocument."""
    crop_img = create_transit_213_synthetic_fixture()
    draft = build_mw4_trace_draft(
        map_name="Transit 213",
        source_url="https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-beta-maps-intel-transit-213",
        image_crop=crop_img
    )

    # 1. Uncalibrated draft must raise ValueError
    with pytest.raises(ValueError, match="Cannot promote uncalibrated MapTraceDraft"):
        project_trace_draft_to_cad_document(draft)

    # 2. Missing routes must raise ValueError
    with pytest.raises(ValueError, match="at least one authored route"):
        project_trace_draft_to_cad_document(
            draft,
            calibration={"px_per_meter": 20.0, "scale_basis": "traversal_calibrated"},
            routes=[]
        )


def test_promoted_cad_document_satisfies_cad_document_v1_validation_contract():
    """Verify that a promoted CADDocument strictly passes validate_cad_document() without schema errors."""
    crop_img = create_transit_213_synthetic_fixture()
    draft = build_mw4_trace_draft(
        map_name="Transit 213",
        source_url="https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-beta-maps-intel-transit-213",
        image_crop=crop_img
    )

    test_route = CADRoute(id="route_alpha", name="Main Lane", waypoints=[[-5.0, 0.0], [5.0, 0.0]])
    cad_doc = project_trace_draft_to_cad_document(
        draft,
        calibration={"px_per_meter": 20.0, "scale_basis": "traversal_calibrated"},
        routes=[test_route]
    )

    doc_dict = cad_doc.to_dict()
    is_valid, errors = validate_cad_document(doc_dict)
    assert is_valid is True, f"Validation failed on promoted CADDocument: {errors}"
    assert len(errors) == 0
    assert cad_doc.document_id == "mw4_draft_transit_213"
    assert len(cad_doc.obstacles) == len(draft.regions)
    assert len(cad_doc.routes) == 1


def test_real_source_acquisition_pipeline_structure(tmp_path):
    """Verify source asset acquisition, crop rectangle extraction, and SHA-256 calculation."""
    # Run acquisition in isolated directory
    meta = {
        "official_metadata": {
            "source_page_url": "https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-beta-maps-intel-transit-213",
            "exact_image_asset_url": "https://www.callofduty.com/content/dam/atvi/callofduty/cod-touchui/mw4/beta/maps/transit-213-card.webp"
        }
    }
    with open(tmp_path / "source.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)

    crop_img, crop_path, prov = load_or_fetch_transit_source_asset(str(tmp_path))
    assert os.path.exists(crop_path)
    assert len(prov["raw_asset_sha256"]) == 64
    assert len(prov["crop_sha256"]) == 64
    assert prov["crop_dimensions"] == [430, 430]
    assert crop_img.shape == (430, 430, 3)
