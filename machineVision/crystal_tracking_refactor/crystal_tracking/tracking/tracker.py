"""
Frame-to-frame crystal tracking.

Tracking is separated from segmentation because it solves a different problem:
segmentation finds objects in one frame, while tracking decides whether a
current object is the same physical crystal seen in earlier frames.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from crystal_tracking.roi.region import create_empty_frame_component_table


def calculate_relative_area_change(previous_area: float, current_area: float) -> float:
    """Calculate absolute relative area change using the previous area."""

    if previous_area <= 0:
        return np.inf

    return abs(current_area - previous_area) / previous_area


def calculate_allowed_centroid_shift(frame_gap: int, config: Dict[str, Any]) -> float:
    """Calculate the allowed centroid shift for a potential track match."""

    base_shift = float(config["max_centroid_shift_pixels"])

    if frame_gap <= 0:
        return base_shift

    if config["scale_centroid_shift_with_frame_gap"]:
        return base_shift * frame_gap

    return base_shift


def assign_new_crystal_indices(
    frame_components: pd.DataFrame,
    next_crystal_index: int,
) -> Tuple[pd.DataFrame, int]:
    """
    Assign new crystal indices to every component in a frame.

    The column is still named crystal_index so existing CSV workflows do not
    break, but comments use "indices" for grammar.
    """

    frame_components = frame_components.copy()

    for row_index in frame_components.index:
        frame_components.loc[row_index, "crystal_index"] = next_crystal_index
        next_crystal_index += 1

    return frame_components, next_crystal_index


def match_current_frame_to_active_tracks(
    track_memory_components: pd.DataFrame,
    current_components: pd.DataFrame,
    next_crystal_index: int,
    current_frame_index: int,
    config: Dict[str, Any],
) -> Tuple[pd.DataFrame, int]:
    """
    Match current-frame crystals to recently seen tracks.

    This is more stable than matching only to the immediately previous frame.
    Each active track stores the most recent observed centroid and area for one
    crystal_index. A current crystal can inherit that same crystal index only if
    its centroid is close enough to the last known centroid and its area change
    is acceptable.

    The cost function heavily weights centroid distance because crystals are
    expected to move only slightly in image coordinates.
    """

    current_components = current_components.copy()

    if len(current_components) == 0:
        return current_components, next_crystal_index

    if track_memory_components is None or len(track_memory_components) == 0:
        return assign_new_crystal_indices(current_components, next_crystal_index)

    track_memory_components = track_memory_components.copy()

    # Keep only valid previous tracks. If tracking_memory_frames is None, old
    # tracks are remembered for the whole run. This prevents a temporarily missed
    # crystal from being assigned a new index when it is detected again near the
    # same position.
    frame_gaps = current_frame_index - track_memory_components["frame_index"].astype(int)

    if config["tracking_memory_frames"] is None:
        active_track_mask = frame_gaps > 0
    else:
        active_track_mask = frame_gaps <= int(config["tracking_memory_frames"])
        active_track_mask &= frame_gaps > 0

    active_tracks = track_memory_components.loc[active_track_mask].copy()

    if len(active_tracks) == 0:
        return assign_new_crystal_indices(current_components, next_crystal_index)

    track_indices = list(active_tracks.index)
    current_indices = list(current_components.index)

    cost_matrix = np.full(
        (len(track_indices), len(current_indices)),
        fill_value=1e9,
        dtype=float,
    )

    centroid_distance_matrix = np.full_like(cost_matrix, np.nan)
    relative_area_change_matrix = np.full_like(cost_matrix, np.nan)
    frame_gap_matrix = np.full_like(cost_matrix, np.nan)

    for track_position, track_index in enumerate(track_indices):
        track_row = active_tracks.loc[track_index]
        previous_centroid = np.array([
            track_row["centroid_x"],
            track_row["centroid_y"],
        ])
        previous_area = float(track_row["area"])
        previous_frame_index = int(track_row["frame_index"])
        frame_gap = int(current_frame_index - previous_frame_index)
        allowed_centroid_shift = calculate_allowed_centroid_shift(frame_gap, config)

        for current_position, current_index in enumerate(current_indices):
            current_row = current_components.loc[current_index]
            current_centroid = np.array([
                current_row["centroid_x"],
                current_row["centroid_y"],
            ])
            current_area = float(current_row["area"])

            centroid_distance = float(np.linalg.norm(current_centroid - previous_centroid))
            relative_area_change = calculate_relative_area_change(
                previous_area=previous_area,
                current_area=current_area,
            )

            centroid_distance_matrix[track_position, current_position] = centroid_distance
            relative_area_change_matrix[track_position, current_position] = relative_area_change
            frame_gap_matrix[track_position, current_position] = frame_gap

            centroid_ok = centroid_distance <= allowed_centroid_shift
            area_ok = relative_area_change <= config["max_relative_area_change"]

            # Keep crystals inside the same ROI unless the ROI index is unknown.
            roi_ok = True
            if "roi_index" in track_row and "roi_index" in current_row:
                roi_ok = int(track_row["roi_index"]) == int(current_row["roi_index"])

            if centroid_ok and area_ok and roi_ok:
                centroid_cost = centroid_distance / max(allowed_centroid_shift, 1e-12)
                area_cost = relative_area_change / max(config["max_relative_area_change"], 1e-12)

                # Older remembered tracks are allowed, but slightly penalized so
                # a match from the most recent frame wins when distances are similar.
                age_cost = 0.0
                if config["tracking_memory_frames"] is not None:
                    if config["tracking_memory_frames"] > 0:
                        age_cost = (frame_gap - 1) / max(config["tracking_memory_frames"], 1)

                cost_matrix[track_position, current_position] = (
                    config["distance_similarity_weight"] * centroid_cost
                    + config["area_similarity_weight"] * area_cost
                    + config["track_memory_age_weight"] * age_cost
                )

    track_match_positions, current_match_positions = linear_sum_assignment(cost_matrix)

    matched_current_indices = set()

    for track_position, current_position in zip(track_match_positions, current_match_positions):
        match_cost = cost_matrix[track_position, current_position]

        if match_cost >= 1e9:
            continue

        track_index = track_indices[track_position]
        current_index = current_indices[current_position]

        previous_crystal_index = int(active_tracks.loc[track_index, "crystal_index"])
        matched_to_frame_index = int(active_tracks.loc[track_index, "frame_index"])
        centroid_distance = centroid_distance_matrix[track_position, current_position]
        relative_area_change = relative_area_change_matrix[track_position, current_position]
        frame_gap = frame_gap_matrix[track_position, current_position]

        current_components.loc[current_index, "crystal_index"] = previous_crystal_index
        current_components.loc[current_index, "matched_to_previous_frame"] = frame_gap == 1
        current_components.loc[current_index, "previous_crystal_index"] = previous_crystal_index
        current_components.loc[current_index, "match_centroid_distance_pixels"] = centroid_distance
        current_components.loc[current_index, "match_relative_area_change"] = relative_area_change
        current_components.loc[current_index, "matched_to_frame_index"] = matched_to_frame_index
        current_components.loc[current_index, "track_frame_gap"] = frame_gap
        current_components.loc[current_index, "tracking_match_cost"] = match_cost

        matched_current_indices.add(current_index)

    for current_index in current_indices:
        if current_index not in matched_current_indices:
            current_components.loc[current_index, "crystal_index"] = next_crystal_index
            next_crystal_index += 1

    return current_components, next_crystal_index


def update_track_memory(
    track_memory_components: pd.DataFrame,
    current_components: pd.DataFrame,
    current_frame_index: int,
    config: Dict[str, Any],
) -> pd.DataFrame:
    """
    Update one-row-per-crystal track memory with the current frame observations.

    Empty current frames do not erase the memory immediately. This is what lets
    a crystal keep its crystal index if segmentation misses it for a few analyzed
    frames.
    """

    if track_memory_components is None or len(track_memory_components) == 0:
        track_memory_components = create_empty_frame_component_table()

    if len(current_components) > 0:
        current_components = current_components.copy()

        if len(track_memory_components) > 0:
            current_ids = set(current_components["crystal_index"].astype(int).tolist())
            track_memory_components = track_memory_components[
                ~track_memory_components["crystal_index"].astype(int).isin(current_ids)
            ].copy()

        track_memory_components = pd.concat(
            [track_memory_components, current_components],
            ignore_index=True,
        )

    if len(track_memory_components) == 0:
        return track_memory_components

    # If tracking_memory_frames is None, keep all remembered tracks. This keeps
    # each crystal_index reserved for the same physical crystal throughout the run.
    if config["tracking_memory_frames"] is None:
        return track_memory_components.copy()

    frame_gaps = current_frame_index - track_memory_components["frame_index"].astype(int)
    keep_mask = frame_gaps <= int(config["tracking_memory_frames"])
    keep_mask &= frame_gaps >= 0

    return track_memory_components.loc[keep_mask].copy()
