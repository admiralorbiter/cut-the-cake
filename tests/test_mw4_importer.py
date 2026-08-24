"""Tests for MW4 Beta Overhead Map Importer & Vectorization Pipeline."""

import os
import numpy as np
import pytest

from cut_the_cake.importers.mw4_trace import (
    MapTraceDraft,
    MapTraceRegion,
    MapTraceUncertainRegion,
    crop_overhead_diagram,
    segment_map_obstacles_and_boundary,
    build_mw4_trace_draft,
    project_trace_draft_to_cad_document,
    create_transit_213_synthetic_reference
)


def test_map_trace_draft_serialization_roundtrip(tmp_path):
    """Verify MapTraceDraft serialization and deserialization."""
    draft = MapTraceDraft(
        source={
            "map_name": "Transit 213",
            "source_type": "official_overview_diagram",
            "source_url": "https://www.callofduty.com/blog/2026/08/transit-213",
            "provenance": "Official Call of Duty Intel",
            "confidence": "reference_reconstruction"
        },
        image_transform={"width_px": 600, "height_px": 600, "rotation_deg": 0.0},
        calibration={"scale_basis": "uncalibrated_pixels", "px_per_meter": None},
        boundary_px=[[0.0, 0.0], [600.0, 0.0], [600.0, 600.0], [0.0, 600.0], [0.0, 0.0]],
        regions=[
            MapTraceRegion(
                id="bus_001",
                polygon_px=[[240.0, 180.0], [350.0, 180.0], [350.0, 215.0], [240.0, 215.0], [240.0, 180.0]],
                classification="bus",
                confidence=0.92,
                notes="Central North Bus"
            )
        ],
        uncertain_regions=[
            MapTraceUncertainRegion(
                id="unc_001",
                bbox_px=[100.0, 100.0, 200.0, 200.0],
                classification="possible_interior",
                confidence=0.60,
                notes="Overhead roof occludes ground path"
            )
        ]
    )

    save_path = str(tmp_path / "test_trace_draft.json")
    draft.save_json(save_path)

    loaded = MapTraceDraft.load_json(save_path)
    assert loaded.source["map_name"] == "Transit 213"
    assert len(loaded.regions) == 1
    assert loaded.regions[0].id == "bus_001"
    assert loaded.regions[0].classification == "bus"
    assert len(loaded.uncertain_regions) == 1


def test_transit_213_classical_segmentation_and_draft():
    """Verify classical CV segmentation on Transit 213 diagram."""
    ref_img = create_transit_213_synthetic_reference()
    assert ref_img.shape == (600, 600, 3)

    draft = build_mw4_trace_draft(
        map_name="Transit 213",
        source_url="https://www.callofduty.com/blog/2026/08/transit-213",
        image_crop=ref_img,
        min_area_px=100.0,
        simplify_epsilon=2.0
    )

    assert draft.source["map_name"] == "Transit 213"
    assert len(draft.boundary_px) >= 4
    assert len(draft.regions) >= 5  # 4 buses + repair shop + gas station + crate

    # Check projection to CADDocument
    cad_doc = project_trace_draft_to_cad_document(draft, scale_px_per_m=20.0)
    assert cad_doc.document_id == "mw4_draft_transit_213"
    assert len(cad_doc.obstacles) == len(draft.regions)
    assert cad_doc.metadata["provenance"] == "MW4 Beta Importer Spike"
