"""
Main crystal tracking workflow.

Top-level purpose
-----------------
Run crystal segmentation and tracking on a single image, an image sequence, an
image folder, or an MP4 video. The workflow saves masks, overlays, per-frame
tracking tables, growth summaries, and metadata.

The lower-level implementation details are distributed into modules:
- config.py: user-editable parameters and JSON parameter loading.
- input_sources.py: image/video input handling.
- roi_manager.py: ROI selection, manual ROIs, and multiple-ROI masks.
- color_kmeans.py: channel extraction, k-means fitting, and crystal masks.
- components.py: connected-component measurement.
- tracker.py: frame-to-frame index preservation.
- outputs.py: saved tables, previews, and plots.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import numpy as np
import pandas as pd

from crystal_tracking.segmentation.color_kmeans import (
    choose_crystal_cluster_numbers,
    create_frame_cluster_table_and_binary_mask,
    create_kmeans_cutoff_table,
    fit_fixed_channel_kmeans,
    get_channel_names,
    summarize_frame_color_analysis,
)

from crystal_tracking.segmentation.components import measure_crystals_from_binary_mask

from crystal_tracking.config.settings import build_config

from crystal_tracking.data_io.file_io import (
    create_output_folder,
    load_image,
    save_image,
    save_json,
    save_table,
)

from crystal_tracking.data_io.input_sources import build_frame_records

from crystal_tracking.data_io.outputs import (
    create_export_table,
    create_tracking_summary_table,
    create_wide_growth_table,
    save_growth_plot,
    save_region_coordinates_json,
    save_tracking_overlay,
)

from crystal_tracking.roi.region import create_empty_frame_component_table
from crystal_tracking.roi.roi_manager import create_and_save_roi_outputs

from crystal_tracking.tracking.tracker import (
    match_current_frame_to_active_tracks,
    update_track_memory,
)

from crystal_tracking.ui.user_interface import apply_startup_dialogs


def run_crystal_tracking(
    config_file_path: str | None = None,
    config_updates: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Run crystal segmentation and tracking.

    Parameters
    ----------
    config_file_path : str or None
        Optional path to a JSON parameter file.

    config_updates : dict or None
        Optional dictionary of settings to update before running. Keys must
        already exist in DEFAULT_CONFIG.

    Returns
    -------
    metadata : dict
        Dictionary describing input settings, analysis settings, and output files.
    """

    config = build_config(
        config_file_path=config_file_path,
        config_updates=config_updates,
    )
    config = apply_startup_dialogs(config)

    create_output_folder(config["output_folder"])

    binary_mask_folder = os.path.join(config["output_folder"], "binary_masks")
    tracking_overlay_folder = os.path.join(config["output_folder"], "tracking_overlays")

    if config["save_per_frame_binary_masks"]:
        create_output_folder(binary_mask_folder)

    if config["save_per_frame_tracking_overlays"]:
        create_output_folder(tracking_overlay_folder)

    frame_records, video_fps = build_frame_records(config)

    (
        circle_rois,
        roi_mask,
        roi_label_mask,
        roi_selection_frame_record,
        roi_selection_image,
    ) = create_and_save_roi_outputs(frame_records=frame_records, config=config)

    print("")
    print("Fitting one fixed k-means model from selected reference frames...")

    centroids, reference_frame_records = fit_fixed_channel_kmeans(
        frame_records=frame_records,
        roi_mask=roi_mask,
        roi_label_mask=roi_label_mask,
        config=config,
    )

    crystal_cluster_numbers = choose_crystal_cluster_numbers(
        centroids=centroids,
        config=config,
    )

    kmeans_cutoff_table = create_kmeans_cutoff_table(centroids, config)
    kmeans_cutoff_table_output_path = os.path.join(
        config["output_folder"],
        "fixed_kmeans_cutoff_table.csv",
    )
    save_table(kmeans_cutoff_table, kmeans_cutoff_table_output_path)

    print("Fixed k-means reference frames:")
    for reference_record in reference_frame_records:
        print(
            f"  analyzed frame {reference_record['frame_index']} | "
            f"source frame/index {reference_record['video_frame_index']} | "
            f"time = {reference_record['time']:.3f} {config['time_unit']}"
        )

    channel_names = get_channel_names(config)
    print(f"Fixed k-means channel(s): {channel_names}")
    print("Fixed k-means centroids:")
    for cluster_number, centroid in enumerate(centroids, start=1):
        centroid_text = ", ".join(
            f"{channel_name} = {centroid[channel_position]:.2f}"
            for channel_position, channel_name in enumerate(channel_names)
        )
        print(f"  Cluster {cluster_number}: {centroid_text}")

    print(f"Crystal cluster number(s): {crystal_cluster_numbers}")
    print(f"Fixed k-means cutoff table saved to: {kmeans_cutoff_table_output_path}")

    all_frame_component_tables = []
    all_color_summary_tables = []
    track_memory_components = create_empty_frame_component_table()
    next_crystal_index = 1

    for loop_index, frame_record in enumerate(frame_records):
        print(
            f"Processing analyzed frame {loop_index + 1} of {len(frame_records)}: "
            f"source index {frame_record['video_frame_index']}"
        )

        image = load_image(frame_record["image_file_path"])

        if image.shape[0:2] != roi_mask.shape:
            raise ValueError(
                "All frames must have the same height and width as the ROI-selection frame. "
                f"Problem frame: {frame_record['image_file_path']}"
            )

        roi_pixel_data, binary_crystal_mask = create_frame_cluster_table_and_binary_mask(
            image=image,
            roi_mask=roi_mask,
            roi_label_mask=roi_label_mask,
            centroids=centroids,
            crystal_cluster_numbers=crystal_cluster_numbers,
            config=config,
        )

        color_summary = summarize_frame_color_analysis(
            roi_pixel_data=roi_pixel_data,
            frame_record=frame_record,
            config=config,
        )
        if len(color_summary) > 0:
            all_color_summary_tables.append(color_summary)

        frame_components, labeled_components = measure_crystals_from_binary_mask(
            binary_crystal_mask=binary_crystal_mask,
            roi_label_mask=roi_label_mask,
            frame_record=frame_record,
            config=config,
        )

        if len(frame_components) == 0:
            print("  No crystals passed the current mask/area filters in this frame.")

        frame_components, next_crystal_index = match_current_frame_to_active_tracks(
            track_memory_components=track_memory_components,
            current_components=frame_components,
            next_crystal_index=next_crystal_index,
            current_frame_index=int(frame_record["frame_index"]),
            config=config,
        )

        track_memory_components = update_track_memory(
            track_memory_components=track_memory_components,
            current_components=frame_components,
            current_frame_index=int(frame_record["frame_index"]),
            config=config,
        )

        all_frame_component_tables.append(frame_components)

        if config["save_per_frame_binary_masks"]:
            binary_mask_filename = f"frame_{int(frame_record['frame_index']):05d}_binary_crystal_mask.png"
            binary_mask_output_path = os.path.join(binary_mask_folder, binary_mask_filename)
            save_image(
                image=binary_crystal_mask.astype(np.uint8) * 255,
                file_path=binary_mask_output_path,
            )

        if config["save_per_frame_tracking_overlays"]:
            overlay_filename = f"frame_{int(frame_record['frame_index']):05d}_tracking_overlay.png"
            overlay_output_path = os.path.join(tracking_overlay_folder, overlay_filename)
            save_tracking_overlay(
                image=image,
                roi_pixel_data=roi_pixel_data,
                labeled_components=labeled_components,
                frame_components=frame_components,
                circle_rois=circle_rois,
                output_file_path=overlay_output_path,
                config=config,
            )

    if len(all_frame_component_tables) > 0:
        frame_crystal_table = pd.concat(all_frame_component_tables, ignore_index=True)
    else:
        frame_crystal_table = pd.DataFrame()

    if len(all_color_summary_tables) > 0:
        color_analysis_summary_table = pd.concat(all_color_summary_tables, ignore_index=True)
    else:
        color_analysis_summary_table = pd.DataFrame()

    frame_crystal_export_table = create_export_table(frame_crystal_table)
    growth_table_wide = create_wide_growth_table(frame_crystal_export_table, config)
    tracking_summary_table = create_tracking_summary_table(frame_crystal_export_table, config)

    frame_crystal_table_output_path = os.path.join(
        config["output_folder"],
        "frame_crystal_tracking_table.csv",
    )
    growth_table_wide_output_path = os.path.join(
        config["output_folder"],
        "crystal_growth_table_wide.csv",
    )
    tracking_summary_output_path = os.path.join(
        config["output_folder"],
        "crystal_tracking_summary.csv",
    )
    growth_plot_output_path = os.path.join(
        config["output_folder"],
        "tracked_crystal_growth_plot.png",
    )
    region_coordinates_output_path = os.path.join(
        config["output_folder"],
        "region_coordinates.json",
    )
    color_analysis_summary_output_path = os.path.join(
        config["output_folder"],
        "color_analysis_summary.csv",
    )
    metadata_output_path = os.path.join(
        config["output_folder"],
        "crystal_tracking_metadata.json",
    )

    save_table(frame_crystal_export_table, frame_crystal_table_output_path)
    save_table(growth_table_wide, growth_table_wide_output_path)
    save_table(tracking_summary_table, tracking_summary_output_path)

    if config["save_color_analysis_summary"]:
        save_table(color_analysis_summary_table, color_analysis_summary_output_path)

    if config["save_region_coordinates_json"]:
        save_region_coordinates_json(
            frame_crystal_table=frame_crystal_table,
            output_file_path=region_coordinates_output_path,
        )

    if config["save_growth_plot"]:
        save_growth_plot(
            frame_crystal_export_table=frame_crystal_export_table,
            output_file_path=growth_plot_output_path,
            config=config,
        )

    metadata = {
        "input_mode": config["input_mode"],
        "reported_video_fps": video_fps,
        "number_of_analyzed_frames": len(frame_records),
        "roi_input_mode": config["roi_input_mode"],
        "number_of_rois": len(circle_rois),
        "circle_rois_pixels": circle_rois,
        "roi_selection_frame": config["roi_selection_frame"],
        "roi_selection_frame_index": config["roi_selection_frame_index"],
        "roi_selection_analyzed_frame_index": int(roi_selection_frame_record["frame_index"]),
        "roi_selection_source_frame_index": int(roi_selection_frame_record["video_frame_index"]),
        "roi_selection_image_file_path": roi_selection_frame_record["image_file_path"],
        "extract_every_nth_frame": config["extract_every_nth_frame"],
        "maximum_frames_to_process": config["maximum_frames_to_process"],
        "time_start": config["time_start"],
        "use_video_time": config["use_video_time"],
        "manual_time_between_saved_frames": config["manual_time_between_saved_frames"],
        "time_unit": config["time_unit"],
        "radius_method": config["radius_method"],
        "tracking_k_value": config["tracking_k_value"],
        "kmeans_channel_names": channel_names,
        "kmeans_fit_mode": config["kmeans_fit_mode"],
        "reference_frame_fraction_positions": config["reference_frame_fraction_positions"],
        "reference_frame_records": reference_frame_records,
        "fixed_kmeans_centroids": centroids.tolist(),
        "crystal_cluster_selection_mode": config["crystal_cluster_selection_mode"],
        "crystal_cluster_numbers": crystal_cluster_numbers,
        "color_analysis_pixel_filter": config["color_analysis_pixel_filter"],
        "component_connectivity": config["component_connectivity"],
        "minimum_crystal_area_pixels": config["minimum_crystal_area_pixels"],
        "max_centroid_shift_pixels": config["max_centroid_shift_pixels"],
        "max_relative_area_change": config["max_relative_area_change"],
        "tracking_memory_frames": config["tracking_memory_frames"],
        "scale_centroid_shift_with_frame_gap": config["scale_centroid_shift_with_frame_gap"],
        "distance_similarity_weight": config["distance_similarity_weight"],
        "area_similarity_weight": config["area_similarity_weight"],
        "track_memory_age_weight": config["track_memory_age_weight"],
        "area_conversion_factor": config["area_conversion_factor"],
        "area_unit": config["area_unit"],
        "region_class_fields": ["time", "centroid", "coordinates", "area"],
        "coordinate_format": "(x, y) = (image_column, image_row)",
        "output_files": {
            "combined_roi_mask": os.path.join(config["output_folder"], "combined_roi_mask.png"),
            "roi_label_mask": os.path.join(config["output_folder"], "roi_label_mask.png"),
            "roi_preview": os.path.join(config["output_folder"], "roi_preview.png"),
            "metadata": metadata_output_path,
            "fixed_kmeans_cutoff_table": kmeans_cutoff_table_output_path,
            "frame_crystal_tracking_table": frame_crystal_table_output_path,
            "crystal_growth_table_wide": growth_table_wide_output_path,
            "crystal_tracking_summary": tracking_summary_output_path,
            "color_analysis_summary": (
                color_analysis_summary_output_path
                if config["save_color_analysis_summary"]
                else None
            ),
            "tracked_crystal_growth_plot": growth_plot_output_path,
            "region_coordinates_json": (
                region_coordinates_output_path
                if config["save_region_coordinates_json"]
                else None
            ),
            "binary_mask_folder": binary_mask_folder,
            "tracking_overlay_folder": tracking_overlay_folder,
        },
    }

    save_json(metadata, metadata_output_path)

    print("")
    print("Crystal segmentation/tracking complete.")
    print(f"ROI preview saved to:              {metadata['output_files']['roi_preview']}")
    print(f"Metadata saved to:                 {metadata_output_path}")
    print(f"Fixed k-means cutoff table saved:  {kmeans_cutoff_table_output_path}")
    print(f"Frame tracking table saved to:     {frame_crystal_table_output_path}")
    print(f"Wide growth table saved to:        {growth_table_wide_output_path}")
    print(f"Tracking summary saved to:         {tracking_summary_output_path}")

    if config["save_color_analysis_summary"]:
        print(f"Color analysis summary saved to:   {color_analysis_summary_output_path}")

    if config["save_growth_plot"]:
        print(f"Growth plot saved to:              {growth_plot_output_path}")

    if config["save_region_coordinates_json"]:
        print(f"Region coordinates saved to:       {region_coordinates_output_path}")

    if config["save_per_frame_binary_masks"]:
        print(f"Binary masks saved in:             {binary_mask_folder}")

    if config["save_per_frame_tracking_overlays"]:
        print(f"Tracking overlays saved in:        {tracking_overlay_folder}")

    return metadata
