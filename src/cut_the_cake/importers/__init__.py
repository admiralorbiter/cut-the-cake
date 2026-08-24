"""Cut the Cake Importers Package."""

from .mw4_trace import (
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
    load_or_fetch_transit_source_asset,
    run_segmentation_sensitivity_sweep
)

__all__ = [
    "MapTraceDraft",
    "MapTraceRegion",
    "MapTraceUncertainRegion",
    "crop_overhead_diagram",
    "segment_map_obstacles_and_boundary",
    "render_vector_overlay",
    "build_mw4_trace_draft",
    "project_trace_draft_to_cad_document",
    "create_synthetic_test_card",
    "create_transit_213_synthetic_fixture",
    "load_or_fetch_transit_source_asset",
    "run_segmentation_sensitivity_sweep"
]
