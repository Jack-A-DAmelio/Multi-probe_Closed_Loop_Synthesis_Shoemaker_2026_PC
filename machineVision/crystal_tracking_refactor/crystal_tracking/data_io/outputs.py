"""
Plotting and export functions.

These functions turn analysis tables and masks into saved files. They do not
change segmentation or tracking decisions.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Patch
from skimage.segmentation import find_boundaries

from crystal_tracking.segmentation.color_kmeans import convert_image_to_rgb_uint8
from crystal_tracking.data_io.file_io import save_json


def get_cluster_display_colors(number_of_clusters: int) -> np.ndarray:
    """Get display colors for k-means cluster labels."""

    color_map = plt.get_cmap("tab10")
    return np.array([color_map(cluster_index)[0:3] for cluster_index in range(number_of_clusters)])


def create_cluster_shaded_frame(
    image,
    roi_pixel_data: pd.DataFrame,
    config: Dict[str, Any],
) -> np.ndarray:
    """Create an image with ROI pixels shaded by k-means cluster label."""

    image_rgb = convert_image_to_rgb_uint8(image)
    shaded_image = image_rgb.astype(float)

    cluster_colors = get_cluster_display_colors(config["tracking_k_value"])
    alpha = config["cluster_overlay_alpha"]

    row_values = roi_pixel_data["image_row"].to_numpy()
    column_values = roi_pixel_data["image_column"].to_numpy()
    cluster_labels = roi_pixel_data["kmeans_cluster"].to_numpy()

    for cluster_number in range(1, config["tracking_k_value"] + 1):
        cluster_mask = cluster_labels == cluster_number
        cluster_rows = row_values[cluster_mask]
        cluster_columns = column_values[cluster_mask]
        cluster_color = cluster_colors[cluster_number - 1] * 255

        shaded_image[cluster_rows, cluster_columns, :] = (
            (1 - alpha) * shaded_image[cluster_rows, cluster_columns, :]
            + alpha * cluster_color
        )

    return np.round(shaded_image).astype(np.uint8)


def draw_roi_overlays(axis, circle_rois: List[Dict[str, float]], config: Dict[str, Any]) -> None:
    """Draw all ROI circles and ROI numbers on a preview axis."""

    for circle_roi in circle_rois:
        circle_patch = Circle(
            xy=(circle_roi["center_x"], circle_roi["center_y"]),
            radius=circle_roi["radius"],
            fill=False,
            linewidth=config["circle_line_width"],
        )
        axis.add_patch(circle_patch)

        axis.text(
            circle_roi["center_x"],
            circle_roi["center_y"],
            f"ROI {int(circle_roi.get('roi_index', 1))}",
            ha="center",
            va="center",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "alpha": 0.7},
        )


def save_tracking_overlay(
    image,
    roi_pixel_data: pd.DataFrame,
    labeled_components: np.ndarray,
    frame_components: pd.DataFrame,
    circle_rois: List[Dict[str, float]],
    output_file_path: str,
    config: Dict[str, Any],
) -> None:
    """Save a frame preview with k-means shading, boundaries, and crystal indices."""

    shaded_image = create_cluster_shaded_frame(
        image=image,
        roi_pixel_data=roi_pixel_data,
        config=config,
    )

    boundary_mask = find_boundaries(labeled_components, mode="outer")
    preview_image = shaded_image.copy()
    preview_image[boundary_mask, :] = np.array([255, 255, 255], dtype=np.uint8)

    cluster_colors = get_cluster_display_colors(config["tracking_k_value"])

    fig, axis = plt.subplots(figsize=tuple(config["figure_size"]))
    axis.imshow(preview_image)
    axis.set_axis_off()
    axis.set_title("Tracked crystals")

    draw_roi_overlays(axis=axis, circle_rois=circle_rois, config=config)

    if config["display_crystal_index_labels"] and len(frame_components) > 0:
        image_height = preview_image.shape[0]
        image_width = preview_image.shape[1]
        margin = int(config["crystal_index_label_margin_pixels"])

        # Labels are the actual persistent crystal_index values used in the CSV.
        # They are not temporary per-frame labels. Sorting only controls drawing
        # order and does not rename crystals.
        label_table = frame_components.sort_values(
            by=["roi_index", "centroid_y", "centroid_x"],
            ascending=[True, True, True],
        ).copy()

        for _, component_row in label_table.iterrows():
            label_x = int(component_row["min_x"])
            label_y = int(component_row["min_y"]) - margin

            # If there is no room above the crystal, place the label below the
            # bounding box. This keeps the index label off the crystal itself.
            if label_y < 0:
                label_y = int(component_row["max_y"]) + margin + 8

            label_x = min(max(label_x, 0), image_width - 1)
            label_y = min(max(label_y, 0), image_height - 1)

            label_text = str(int(component_row["crystal_index"]))

            axis.text(
                label_x,
                label_y,
                label_text,
                ha="left",
                va="center",
                fontsize=8,
                bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "alpha": 0.75},
            )

    legend_handles = []
    for cluster_number in range(1, config["tracking_k_value"] + 1):
        legend_patch = Patch(
            facecolor=cluster_colors[cluster_number - 1],
            label=f"K-means cluster {cluster_number}",
        )
        legend_handles.append(legend_patch)

    axis.legend(
        handles=legend_handles,
        loc="lower right",
        framealpha=0.9,
    )

    fig.savefig(output_file_path, dpi=config["preview_dpi"], bbox_inches="tight")
    plt.close(fig)


def create_export_table(frame_crystal_table: pd.DataFrame):
    """Create CSV-safe table by removing Python objects and huge coordinate lists."""

    columns_to_drop = [
        "region_object",
        "coordinates",
    ]

    if frame_crystal_table is None or len(frame_crystal_table) == 0:
        export_table = pd.DataFrame()
        return export_table

    export_table = frame_crystal_table.copy()

    if "coordinates" in export_table.columns:
        export_table["number_of_coordinate_pixels"] = export_table["coordinates"].apply(len)

    for column_name in columns_to_drop:
        if column_name in export_table.columns:
            export_table = export_table.drop(columns=[column_name])

    return export_table


def save_region_coordinates_json(
    frame_crystal_table: pd.DataFrame,
    output_file_path: str,
) -> None:
    """Save full coordinate lists for each Region object as JSON."""

    coordinate_records = []

    for _, row in frame_crystal_table.iterrows():
        coordinate_records.append({
            "crystal_index": int(row["crystal_index"]),
            "roi_index": int(row["roi_index"]),
            "frame_index": int(row["frame_index"]),
            "video_frame_index": int(row["video_frame_index"]),
            "time": float(row["time"]),
            "centroid": [float(row["centroid_x"]), float(row["centroid_y"])],
            "area": float(row["area"]),
            "area_unit": row["area_unit"],
            "coordinates": row["coordinates"],
        })

    save_json(coordinate_records, output_file_path)


def create_wide_growth_table(
    frame_crystal_export_table: pd.DataFrame,
    config: Dict[str, Any],
) -> pd.DataFrame:
    """Create a wide time-vs-crystal area table."""

    if len(frame_crystal_export_table) == 0:
        return pd.DataFrame()

    wide_growth_table = frame_crystal_export_table.pivot_table(
        index="time",
        columns="crystal_index",
        values="area",
        aggfunc="first",
    )

    wide_growth_table = wide_growth_table.sort_index()
    wide_growth_table.columns = [
        f"crystal_{int(column)}_area_{config['area_unit']}"
        for column in wide_growth_table.columns
    ]
    wide_growth_table = wide_growth_table.reset_index()

    return wide_growth_table


def create_tracking_summary_table(
    frame_crystal_export_table: pd.DataFrame,
    config: Dict[str, Any],
) -> pd.DataFrame:
    """Create one summary row per tracked crystal."""

    if len(frame_crystal_export_table) == 0:
        return pd.DataFrame()

    summary_rows = []

    for crystal_index, crystal_data in frame_crystal_export_table.groupby("crystal_index"):
        crystal_data = crystal_data.sort_values("time")

        first_row = crystal_data.iloc[0]
        last_row = crystal_data.iloc[-1]

        duration = float(last_row["time"] - first_row["time"])
        area_change = float(last_row["area"] - first_row["area"])
        area_change_pixels = int(last_row["area_pixels"] - first_row["area_pixels"])

        if duration != 0:
            growth_rate_area_per_time = area_change / duration
            growth_rate_pixels_per_time = area_change_pixels / duration
        else:
            growth_rate_area_per_time = np.nan
            growth_rate_pixels_per_time = np.nan

        summary_rows.append({
            "crystal_index": int(crystal_index),
            "roi_index": int(first_row["roi_index"]),
            "first_frame_index": int(first_row["frame_index"]),
            "last_frame_index": int(last_row["frame_index"]),
            "first_video_frame_index": int(first_row["video_frame_index"]),
            "last_video_frame_index": int(last_row["video_frame_index"]),
            "first_time": float(first_row["time"]),
            "last_time": float(last_row["time"]),
            "duration": float(duration),
            "number_of_observed_frames": int(len(crystal_data)),
            "first_area": float(first_row["area"]),
            "last_area": float(last_row["area"]),
            "area_change": float(area_change),
            "area_unit": config["area_unit"],
            "growth_rate_area_per_time": float(growth_rate_area_per_time),
            "first_area_pixels": int(first_row["area_pixels"]),
            "last_area_pixels": int(last_row["area_pixels"]),
            "area_change_pixels": int(area_change_pixels),
            "growth_rate_pixels_per_time": float(growth_rate_pixels_per_time),
        })

    return pd.DataFrame(summary_rows)


def save_growth_plot(
    frame_crystal_export_table: pd.DataFrame,
    output_file_path: str,
    config: Dict[str, Any],
) -> None:
    """Save a plot of converted crystal area vs time for each tracked crystal."""

    if len(frame_crystal_export_table) == 0:
        return

    fig, axis = plt.subplots(figsize=(9, 6))

    for crystal_index, crystal_data in frame_crystal_export_table.groupby("crystal_index"):
        crystal_data = crystal_data.sort_values("time")
        axis.plot(
            crystal_data["time"],
            crystal_data["area"],
            marker="o",
            linewidth=1.5,
            label=f"Crystal {int(crystal_index)}",
        )

    axis.set_xlabel(f"Time ({config['time_unit']})")
    axis.set_ylabel(f"Crystal area ({config['area_unit']})")
    axis.set_title("Tracked Crystal Growth")
    axis.legend(fontsize=8, ncols=2)

    fig.savefig(output_file_path, dpi=config["preview_dpi"], bbox_inches="tight")
    plt.close(fig)
