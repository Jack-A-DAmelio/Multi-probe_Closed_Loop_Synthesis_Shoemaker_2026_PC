"""
Region data structures and table schemas.

This file stays small on purpose: the Region class defines the measured object,
while FRAME_COMPONENT_COLUMNS gives the rest of the workflow a consistent table
shape even when a frame contains zero detected crystals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd


@dataclass
class Region:
    """
    One connected crystal region in one video frame.

    Attributes
    ----------
    time : float
        Time of the frame.

    centroid : tuple
        Crystal centroid as (x, y), where x = image column and y = image row.

    coordinates : list
        Pixel coordinates inside the crystal as [(x, y), ...].

    area : float
        Converted area. This equals area_pixels * area_conversion_factor.
    """

    time: float
    centroid: Tuple[float, float]
    coordinates: List[Tuple[int, int]]
    area: float


# These columns are kept even when a frame has zero detected crystals.
# Without this, pandas creates a completely columnless DataFrame, and later
# overlay/export code can fail when it tries to access columns such as
# centroid_x or centroid_y.
FRAME_COMPONENT_COLUMNS = [
    "frame_index",
    "video_frame_index",
    "time",
    "time_unit",
    "image_file_name",
    "image_file_path",
    "roi_index",
    "component_label",
    "crystal_index",
    "area",
    "area_unit",
    "area_pixels",
    "area_conversion_factor",
    "equivalent_diameter_pixels",
    "centroid_x",
    "centroid_y",
    "min_x",
    "max_x",
    "min_y",
    "max_y",
    "matched_to_previous_frame",
    "previous_crystal_index",
    "match_centroid_distance_pixels",
    "match_relative_area_change",
    "matched_to_frame_index",
    "track_frame_gap",
    "tracking_match_cost",
    "region_object",
    "coordinates",
]


def create_empty_frame_component_table() -> pd.DataFrame:
    """Create an empty crystal table with the expected tracking columns."""

    return pd.DataFrame(columns=FRAME_COMPONENT_COLUMNS)
