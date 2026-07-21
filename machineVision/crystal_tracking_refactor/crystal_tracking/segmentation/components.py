"""
Connected-component measurement.

K-means produces a binary mask of likely crystal pixels. This file turns that
mask into individual objects by grouping adjacent True pixels, then measures
each group as a Region.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from skimage.measure import label, regionprops

from crystal_tracking.roi.region import Region, create_empty_frame_component_table


def create_region_from_regionprops(
    region,
    frame_time: float,
    config: Dict[str, Any],
) -> Region:
    """Convert one skimage regionprops object into the requested Region class."""

    centroid_row, centroid_column = region.centroid

    coordinates_xy = [
        (int(column), int(row))
        for row, column in region.coords
    ]

    area_pixels = int(region.area)
    converted_area = area_pixels * config["area_conversion_factor"]

    crystal_region = Region(
        time=float(frame_time),
        centroid=(float(centroid_column), float(centroid_row)),
        coordinates=coordinates_xy,
        area=float(converted_area),
    )

    return crystal_region


def get_component_roi_index(region, roi_label_mask: np.ndarray) -> int:
    """
    Assign a component to the ROI containing most of its pixels.

    This supports multiple ROIs without forcing the rest of the tracking code to
    run separately for each ROI.
    """

    if roi_label_mask is None:
        return 1

    roi_values = roi_label_mask[region.coords[:, 0], region.coords[:, 1]]
    roi_values = roi_values[roi_values > 0]

    if len(roi_values) == 0:
        return 0

    unique_values, counts = np.unique(roi_values, return_counts=True)
    return int(unique_values[np.argmax(counts)])


def measure_crystals_from_binary_mask(
    binary_crystal_mask: np.ndarray,
    roi_label_mask: np.ndarray,
    frame_record: Dict[str, Any],
    config: Dict[str, Any],
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Group adjacent True pixels into connected components and measure crystals.

    Each connected component is treated as one crystal candidate. Tiny components
    are ignored because they are more likely to be noise than physical crystals.
    """

    labeled_components = label(
        binary_crystal_mask,
        connectivity=config["component_connectivity"],
    )

    component_rows = []

    for component_region in regionprops(labeled_components):
        area_pixels = int(component_region.area)

        if area_pixels < config["minimum_crystal_area_pixels"]:
            continue

        crystal_region = create_region_from_regionprops(
            region=component_region,
            frame_time=frame_record["time"],
            config=config,
        )

        centroid_x, centroid_y = crystal_region.centroid
        min_row, min_column, max_row, max_column = component_region.bbox
        roi_index = get_component_roi_index(component_region, roi_label_mask)

        component_rows.append({
            "frame_index": int(frame_record["frame_index"]),
            "video_frame_index": int(frame_record["video_frame_index"]),
            "time": float(frame_record["time"]),
            "time_unit": config["time_unit"],
            "image_file_name": os.path.basename(frame_record["image_file_path"]),
            "image_file_path": frame_record["image_file_path"],
            "roi_index": int(roi_index),
            "component_label": int(component_region.label),
            "crystal_index": -1,
            "area": float(crystal_region.area),
            "area_unit": config["area_unit"],
            "area_pixels": int(area_pixels),
            "area_conversion_factor": float(config["area_conversion_factor"]),
            "equivalent_diameter_pixels": float(component_region.equivalent_diameter_area),
            "centroid_x": float(centroid_x),
            "centroid_y": float(centroid_y),
            "min_x": int(min_column),
            "max_x": int(max_column - 1),
            "min_y": int(min_row),
            "max_y": int(max_row - 1),
            "matched_to_previous_frame": False,
            "previous_crystal_index": -1,
            "match_centroid_distance_pixels": np.nan,
            "match_relative_area_change": np.nan,
            "matched_to_frame_index": -1,
            "track_frame_gap": np.nan,
            "tracking_match_cost": np.nan,
            "region_object": crystal_region,
            "coordinates": crystal_region.coordinates,
        })

    if len(component_rows) == 0:
        return create_empty_frame_component_table(), labeled_components

    return pd.DataFrame(component_rows), labeled_components
