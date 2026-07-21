"""
Configuration handling for the crystal tracking workflow.

The analysis settings are kept in a JSON-compatible dictionary so future users
can change behavior without editing the analysis code itself. This is easier to
review than having many hard-coded parameters spread through the methods.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    # Input mode.
    # Use "single_image" to test segmentation on one image.
    # Use "image_list" to process multiple specific image files in order.
    # Use "image_folder" to process all supported images inside one folder.
    # Use "mp4" to extract frames from one MP4 video, then track crystals over time.
    "input_mode": "image_folder",

    # Input image for single_image mode.
    "image_file_path": "/Users/darrenco/Downloads/test_crystal_image.png",

    # Input image paths for image_list mode.
    "image_file_paths": [
        "/Users/darrenco/Downloads/frame_001.png",
        "/Users/darrenco/Downloads/frame_002.png",
        "/Users/darrenco/Downloads/frame_003.png",
    ],

    # Input folder for image_folder mode.
    "image_folder_path": "/Users/darrenco/Downloads/Xtal Crop",

    # File extensions used by image_folder mode.
    "image_file_extensions": [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"],

    # If True, image_folder mode sorts file names alphabetically before analysis.
    # This is usually correct for names like frame_0001.png, frame_0002.png, etc.
    "sort_image_inputs_by_name": True,

    # Input video for mp4 mode.
    "video_file_path": "/Users/darrenco/Downloads/crystal_video.mp4",

    # Output folder. Raw images/videos are not modified.
    "output_folder": "/Users/darrenco/Downloads/Crystal_Tracking_Output",

    # Startup UI settings.
    # startup_dialog_backend controls how startup prompts are opened.
    # Options:
    # - "auto": macOS uses native AppleScript dialogs; Windows/Linux use Tkinter.
    # - "tk": force Tkinter dialogs on any operating system.
    # - "applescript": force AppleScript dialogs. Only works on macOS.
    # - "terminal": ask in the terminal instead of opening popups.
    # - "none": skip startup prompts and use config_parameters.json values.
    "startup_dialog_backend": "auto",

    # If True, a folder picker appears before analysis starts. The selected
    # folder overrides output_folder for that run.
    "ask_for_output_folder_on_start": True,

    # If True, a small startup window asks which two color channels should be
    # used for k-means clustering. The selected channels override
    # kmeans_channel_names for that run.
    "ask_for_kmeans_channels_on_start": True,

    # Extracted-frame settings.
    "extracted_frame_folder_name": "extracted_frames",
    "extract_every_nth_frame": 50,
    "maximum_frames_to_process": None,
    "overwrite_extracted_frames": True,
    "save_extracted_frames": True,

    # Time settings.
    # If use_video_time = True, time is read from video frame index / video FPS.
    # If use_video_time = False, time is calculated using manual_time_between_saved_frames.
    "use_video_time": True,
    "time_start": 0.0,
    "manual_time_between_saved_frames": 1.0,
    "time_unit": "s",

    # Area conversion.
    # The Region.area field is area_pixels * area_conversion_factor.
    # Examples:
    # - Unknown calibration: use 1.0 and area_unit = "pixels".
    # - If 1 pixel = 0.50 micrometers, use 0.50**2 = 0.25 and area_unit = "um^2".
    # - If you just want arbitrary units, use any constant and name it "a.u.".
    "area_conversion_factor": 1.0,
    "area_unit": "converted_area_units",

    # ROI settings.
    # roi_input_mode:
    # - "interactive": draw one or more circular ROIs on a selected frame.
    # - "manual": use the circles listed in manual_rois.
    "roi_input_mode": "interactive",

    # Historical setting kept for compatibility with older parameter files.
    # Interactive ROI selection is now button-controlled, so the user can draw
    # one ROI, click Add Another ROI, and stop whenever enough ROIs are selected.
    "number_of_rois": 1,

    # Manual ROIs are useful when you want repeatable analysis without redrawing.
    # The values are in pixels and follow the same coordinate convention as the outputs:
    # x = image column, y = image row.
    "manual_rois": [
        {"roi_index": 1, "center_x": 200.0, "center_y": 200.0, "radius": 100.0}
    ],

    # roi_selection_frame controls which frame/image is shown for drawing ROIs.
    # Options:
    # - "last": draw ROI on the last analyzed image/frame.
    # - "first": draw ROI on the first analyzed image/frame.
    # - "index": draw ROI on roi_selection_frame_index.
    "roi_selection_frame": "last",
    "roi_selection_frame_index": -1,

    # "average" uses the average of rough width and rough height.
    # "minimum" forces the circle to fit inside the rough selection.
    # "maximum" forces the circle to cover the rough selection.
    "radius_method": "average",
    "minimum_roi_size_pixels": 5,

    # Channel settings for k-means.
    # These control what color channels are used for clustering.
    # Examples:
    # - ["red", "green"] keeps the old red-green behavior.
    # - ["red", "blue"] tests red-blue segmentation.
    # - ["red", "yellow"] uses red and a computed yellow channel, where
    #   yellow = average(red, green).
    # Available channels are red, green, blue, yellow, cyan, magenta, brightness.
    "kmeans_channel_names": ["red", "green"],

    # K-means settings.
    # tracking_k_value = 3 means each ROI pixel is assigned to one of 3 fixed
    # color groups in the selected channel space.
    "tracking_k_value": 3,
    "kmeans_iterations": 80,
    "kmeans_random_seed": 0,

    # How to fit the fixed k-means model.
    # - "reference_frames": use selected frames only. Usually faster and stable.
    # - "all_analyzed_frames": sample from every analyzed frame. Slower but can
    #   help if the color distribution changes over time.
    "kmeans_fit_mode": "reference_frames",

    # Reference frames for MP4 or image-sequence modes, expressed as fractions
    # of the analyzed frame list. 0.50 = halfway frame, 0.75 = 3/4 frame,
    # 1.00 = final frame.
    "reference_frame_fraction_positions": [0.50, 0.75, 1.00],

    # Maximum ROI pixels sampled from each reference frame for fitting k-means.
    # Lower this for faster testing. Raise this if segmentation looks noisy.
    "maximum_pixels_per_reference_frame_for_kmeans_fit": 20000,

    # Used only when kmeans_fit_mode = "all_analyzed_frames".
    "maximum_pixels_per_frame_for_kmeans_fit": 5000,

    # Which k-means cluster should count as crystal pixels.
    # - "darkest": chooses the cluster with lowest selected-channel brightness.
    # - "brightest": chooses the cluster with highest selected-channel brightness.
    # - "manual": uses manual_crystal_cluster_numbers below.
    "crystal_cluster_selection_mode": "darkest",
    "manual_crystal_cluster_numbers": [1],

    # Color analysis settings.
    # This does not change tracking unless you also change crystal_cluster_selection_mode.
    # It controls which pixels are summarized in color_analysis_summary.csv.
    # Options:
    # - "all_roi": summarize every pixel inside the selected ROI(s).
    # - "crystal_only": summarize only pixels classified as crystal pixels.
    # - "non_crystal_only": summarize only ROI pixels not classified as crystal pixels.
    "color_analysis_pixel_filter": "all_roi",

    # Connected-component settings.
    # 1 = 4-connected pixels. Only up/down/left/right count as adjacent.
    # 2 = 8-connected pixels. Diagonal touching also counts as adjacent.
    "component_connectivity": 2,
    "minimum_crystal_area_pixels": 40,

    # Tracking settings.
    # Crystals are expected to stay nearly fixed in image coordinates. Therefore,
    # tracking primarily preserves crystal indices by nearest centroid position.
    # Area is used as a secondary check so similarly located but wildly different-sized
    # objects are less likely to be matched.
    "max_centroid_shift_pixels": 10.0,
    "max_relative_area_change": 2.0,

    # If a crystal disappears for a few frames, the tracker can still recover
    # the same crystal_index by comparing to its last known centroid.
    # Use None to remember crystals for the whole run. This is recommended when
    # crystals are stationary and should keep the same index after reappearing.
    # Use 0 to match only against the immediately previous analyzed frame.
    "tracking_memory_frames": None,

    # If True, allowed centroid shift increases with the number of missed
    # analyzed frames. For nearly stationary crystals, False is usually safer.
    "scale_centroid_shift_with_frame_gap": False,

    # Cost = distance_similarity_weight * centroid_cost
    #        + area_similarity_weight * area_cost
    #        + track_memory_age_weight * age_cost.
    # Since crystals barely move, distance gets the largest weight.
    "distance_similarity_weight": 5.0,
    "area_similarity_weight": 0.25,
    "track_memory_age_weight": 0.10,

    # Output settings.
    "save_per_frame_binary_masks": True,
    "save_per_frame_tracking_overlays": True,
    "save_region_coordinates_json": False,
    "save_growth_plot": True,
    "save_color_analysis_summary": True,

    # Crystal label settings for overlay images.
    # Labels are placed next to each crystal bounding box, not on the crystal centroid.
    "display_crystal_index_labels": True,
    "crystal_index_label_margin_pixels": 6,

    # Overlay settings.
    "figure_size": [8, 8],
    "circle_line_width": 2.5,
    "preview_dpi": 300,
    "cluster_overlay_alpha": 0.65,
}


def get_default_config() -> Dict[str, Any]:
    """Return a deep copy of the default configuration dictionary."""

    return copy.deepcopy(DEFAULT_CONFIG)


def load_config_file(config_file_path: str | Path) -> Dict[str, Any]:
    """Load user-editable settings from a JSON parameter file."""

    config_path = Path(config_file_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Could not find config file: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        loaded_config = json.load(file)

    return loaded_config


def merge_config_updates(
    base_config: Dict[str, Any],
    config_updates: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """
    Return a copy of base_config updated with user-provided settings.

    Unknown setting names raise an error instead of being silently ignored. This
    helps catch typos in the JSON parameter file.
    """

    config = copy.deepcopy(base_config)

    if config_updates is None:
        return config

    for setting_name, setting_value in config_updates.items():
        if setting_name not in config:
            raise KeyError(f"Unknown CONFIG setting: {setting_name}")

        config[setting_name] = setting_value

    return config


def build_config(
    config_file_path: str | Path | None = None,
    config_updates: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Build the final config dictionary from defaults, a JSON file, and optional overrides.

    Later inputs override earlier inputs:
    defaults < JSON parameter file < config_updates argument.
    """

    config = get_default_config()

    if config_file_path is not None:
        file_updates = load_config_file(config_file_path)
        config = merge_config_updates(config, file_updates)

    config = merge_config_updates(config, config_updates)

    return config
