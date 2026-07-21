"""
Color-channel extraction, fixed k-means fitting, and pixel classification.

K-means is used here as a repeatable color-space segmentation method:
1. Select only pixels inside the ROI mask.
2. Convert each selected pixel into the configured color-channel values
   such as red-green, red-blue, or red-yellow.
3. Fit one fixed k-means model from selected reference frames.
4. Reuse those same centroids for every frame so cluster numbers mean the same
   thing over time.
5. Convert the selected crystal cluster(s) into a binary crystal mask.
6. Connected-component analysis later groups adjacent True pixels in that mask
   into individual crystals.

This file deliberately does not do ROI drawing or frame-to-frame tracking. It
only handles color information and masks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans2

from crystal_tracking.data_io.file_io import load_image


CHANNEL_DISPLAY_NAMES = {
    "red": "red",
    "green": "green",
    "blue": "blue",
    "yellow": "yellow",
    "cyan": "cyan",
    "magenta": "magenta",
    "brightness": "brightness",
}


def convert_image_to_rgb_uint8(image) -> np.ndarray:
    """Convert an image array to 8-bit RGB."""

    if image.ndim == 2:
        raise ValueError("Color k-means requires a color image, but this image is grayscale.")

    if image.ndim != 3:
        raise ValueError("Image must have shape (rows, columns, channels).")

    if image.shape[2] < 3:
        raise ValueError("Image must have at least 3 channels.")

    image_rgb = image[:, :, 0:3]

    if image_rgb.dtype == np.uint8:
        return image_rgb

    image_rgb_float = image_rgb.astype(float)

    if image_rgb.dtype == np.uint16:
        image_rgb_float = image_rgb_float / 65535 * 255
    elif np.nanmax(image_rgb_float) <= 1.0:
        image_rgb_float = image_rgb_float * 255
    else:
        image_rgb_float = np.clip(image_rgb_float, 0, 255)

    return np.round(image_rgb_float).astype(np.uint8)


def compute_channel_values(image_rgb: np.ndarray, channel_name: str) -> np.ndarray:
    """
    Return a 2D image of one requested channel.

    The camera directly provides red, green, and blue. The other channels are
    simple derived channels. For example, yellow is calculated as the average of
    red and green, which is useful when the color separation is not aligned with
    one raw RGB channel.
    """

    normalized_name = channel_name.lower().strip()

    red = image_rgb[:, :, 0].astype(float)
    green = image_rgb[:, :, 1].astype(float)
    blue = image_rgb[:, :, 2].astype(float)

    if normalized_name == "red":
        return red

    if normalized_name == "green":
        return green

    if normalized_name == "blue":
        return blue

    if normalized_name == "yellow":
        return (red + green) / 2

    if normalized_name == "cyan":
        return (green + blue) / 2

    if normalized_name == "magenta":
        return (red + blue) / 2

    if normalized_name == "brightness":
        return (red + green + blue) / 3

    valid_names = ", ".join(CHANNEL_DISPLAY_NAMES)
    raise ValueError(f"Unknown channel '{channel_name}'. Valid channels: {valid_names}.")


def get_channel_names(config: Dict[str, Any]) -> List[str]:
    """Read and validate the configured k-means channel names."""

    channel_names = [str(name).lower().strip() for name in config["kmeans_channel_names"]]

    if len(channel_names) < 1:
        raise ValueError("kmeans_channel_names must contain at least one channel.")

    for channel_name in channel_names:
        if channel_name not in CHANNEL_DISPLAY_NAMES:
            valid_names = ", ".join(CHANNEL_DISPLAY_NAMES)
            raise ValueError(f"Unknown channel '{channel_name}'. Valid channels: {valid_names}.")

    return channel_names


def extract_roi_channel_values(
    image,
    roi_mask: np.ndarray,
    roi_label_mask: np.ndarray,
    config: Dict[str, Any],
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Extract ROI pixel rows, columns, ROI indices, and configured channel values.

    This replaces the older hard-coded red-green extraction. To use another
    channel pair, change kmeans_channel_names in config_parameters.json.
    """

    image_rgb = convert_image_to_rgb_uint8(image)

    if roi_label_mask.shape != roi_mask.shape:
        raise ValueError("roi_label_mask and roi_mask must have the same shape.")

    row_indices, column_indices = np.where(roi_mask)
    channel_names = get_channel_names(config)

    roi_pixel_data = pd.DataFrame({
        "image_row": row_indices,
        "image_column": column_indices,
        "roi_index": roi_label_mask[row_indices, column_indices].astype(int),
    })

    channel_arrays = []

    for channel_name in channel_names:
        channel_image = compute_channel_values(image_rgb, channel_name)
        channel_values = channel_image[row_indices, column_indices].astype(float)
        roi_pixel_data[channel_name] = channel_values
        channel_arrays.append(channel_values)

    channel_values_array = np.column_stack(channel_arrays).astype(float)

    return roi_pixel_data, channel_values_array


def choose_kmeans_reference_frame_records(
    frame_records: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Choose which frames are used to fit the fixed k-means model."""

    if len(frame_records) == 1:
        return frame_records

    fit_mode = config["kmeans_fit_mode"].lower().strip()

    if fit_mode == "all_analyzed_frames":
        return frame_records

    if fit_mode != "reference_frames":
        raise ValueError("kmeans_fit_mode must be 'reference_frames' or 'all_analyzed_frames'.")

    reference_indices = []
    last_index = len(frame_records) - 1

    for fraction in config["reference_frame_fraction_positions"]:
        fraction = float(fraction)
        fraction = min(max(fraction, 0.0), 1.0)
        reference_index = int(round(fraction * last_index))
        reference_indices.append(reference_index)

    # Remove duplicates while preserving sorted frame order.
    reference_indices = sorted(set(reference_indices))

    return [frame_records[index] for index in reference_indices]


def sample_channel_values_for_kmeans_fit(
    frame_records: List[Dict[str, Any]],
    roi_mask: np.ndarray,
    roi_label_mask: np.ndarray,
    config: Dict[str, Any],
) -> np.ndarray:
    """
    Sample ROI pixels from selected frames to fit the fixed k-means model.

    We sample instead of using every pixel because videos can contain millions of
    ROI pixels. A random but seeded subset keeps the fit fast while preserving a
    representative color distribution.
    """

    sampled_arrays = []
    random_generator = np.random.default_rng(config["kmeans_random_seed"])

    fit_mode = config["kmeans_fit_mode"].lower().strip()

    if fit_mode == "all_analyzed_frames":
        maximum_sample_size = config["maximum_pixels_per_frame_for_kmeans_fit"]
    else:
        maximum_sample_size = config["maximum_pixels_per_reference_frame_for_kmeans_fit"]

    for frame_record in frame_records:
        image = load_image(frame_record["image_file_path"])

        if image.shape[0:2] != roi_mask.shape:
            raise ValueError(
                "All frames must have the same height and width as the ROI-selection frame. "
                f"Problem frame: {frame_record['image_file_path']}"
            )

        _, channel_values = extract_roi_channel_values(
            image=image,
            roi_mask=roi_mask,
            roi_label_mask=roi_label_mask,
            config=config,
        )

        if len(channel_values) > maximum_sample_size:
            sample_indices = random_generator.choice(
                len(channel_values),
                size=maximum_sample_size,
                replace=False,
            )
            channel_values = channel_values[sample_indices]

        sampled_arrays.append(channel_values)

    return np.vstack(sampled_arrays)


def sort_centroids_by_channel_brightness(centroids: np.ndarray) -> np.ndarray:
    """
    Sort k-means centroids so cluster 1 is darkest and highest cluster is brightest.

    Brightness here means the sum of the configured channel values. With the
    default red-green channels, this is red + green. With red-blue, it is
    red + blue. This keeps cluster numbering stable enough for the "darkest" and
    "brightest" crystal-cluster selection modes.
    """

    brightness_score = centroids.sum(axis=1)
    sorted_order = np.argsort(brightness_score)

    return centroids[sorted_order, :]


def create_kmeans_cutoff_table(
    centroids: np.ndarray,
    config: Dict[str, Any],
) -> pd.DataFrame:
    """
    Create pairwise nearest-centroid cutoff equations for the fixed k-means model.

    For two clusters, the boundary is the hyperplane halfway between their
    centroids. In a two-channel space this is a line. In a three-channel space
    this is a plane.
    """

    cutoff_rows = []
    channel_names = get_channel_names(config)

    for first_index in range(len(centroids)):
        for second_index in range(first_index + 1, len(centroids)):
            first_centroid = centroids[first_index]
            second_centroid = centroids[second_index]
            midpoint = (first_centroid + second_centroid) / 2
            normal_vector = second_centroid - first_centroid

            cutoff_row = {
                "cluster_a": int(first_index + 1),
                "cluster_b": int(second_index + 1),
                "cutoff_equation": (
                    "sum(normal_i * (channel_i - midpoint_i)) = 0; "
                    "the sign tells which centroid is closer"
                ),
            }

            for channel_position, channel_name in enumerate(channel_names):
                cutoff_row[f"cluster_a_center_{channel_name}"] = float(first_centroid[channel_position])
                cutoff_row[f"cluster_b_center_{channel_name}"] = float(second_centroid[channel_position])
                cutoff_row[f"midpoint_{channel_name}"] = float(midpoint[channel_position])
                cutoff_row[f"normal_{channel_name}"] = float(normal_vector[channel_position])

            cutoff_rows.append(cutoff_row)

    return pd.DataFrame(cutoff_rows)


def fit_fixed_channel_kmeans(
    frame_records: List[Dict[str, Any]],
    roi_mask: np.ndarray,
    roi_label_mask: np.ndarray,
    config: Dict[str, Any],
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Fit one fixed k-means color model and return the reference-frame records.

    This function intentionally fits the model once, before the frame loop. That
    is important for tracking because a cluster number should mean the same
    color group in every frame. If we refit k-means separately for each frame,
    cluster 1 could mean a dark crystal in one frame and background in another.

    The steps are:
    1. Choose reference frames from the analyzed image sequence.
    2. Use the ROI mask to collect only pixels inside the region(s) we care about.
    3. Convert those pixels into the configured channel space, such as red-green
       or red-blue.
    4. Fit k-means to those sampled pixels.
    5. Sort centroids from darkest to brightest so cluster numbering is easier
       to interpret and manual cluster selection is repeatable.
    """

    reference_frame_records = choose_kmeans_reference_frame_records(frame_records, config)

    channel_values = sample_channel_values_for_kmeans_fit(
        frame_records=reference_frame_records,
        roi_mask=roi_mask,
        roi_label_mask=roi_label_mask,
        config=config,
    )

    # scipy.cluster.vq.kmeans2 uses NumPy's legacy random state for minit="points".
    # Setting this seed makes the selected starting points reproducible.
    np.random.seed(config["kmeans_random_seed"])

    centroids, _ = kmeans2(
        data=channel_values,
        k=config["tracking_k_value"],
        iter=config["kmeans_iterations"],
        minit="points",
    )

    centroids = sort_centroids_by_channel_brightness(centroids)

    return centroids, reference_frame_records


def assign_pixels_to_kmeans_centroids(
    channel_values: np.ndarray,
    centroids: np.ndarray,
) -> np.ndarray:
    """
    Assign each ROI pixel to the nearest fixed k-means centroid.

    The output is 1-based because cluster labels are shown to the user as
    cluster 1, cluster 2, etc. This avoids mixing Python's internal 0-based
    indexing with user-facing cluster numbers.
    """

    distances = np.sqrt(
        np.sum(
            (channel_values[:, None, :] - centroids[None, :, :]) ** 2,
            axis=2,
        )
    )

    cluster_labels = np.argmin(distances, axis=1) + 1

    return cluster_labels


def choose_crystal_cluster_numbers(
    centroids: np.ndarray,
    config: Dict[str, Any],
) -> List[int]:
    """Choose which k-means cluster number or numbers become the crystal mask."""

    selection_mode = config["crystal_cluster_selection_mode"].lower().strip()

    if selection_mode == "manual":
        crystal_cluster_numbers = list(config["manual_crystal_cluster_numbers"])

    elif selection_mode == "darkest":
        brightness_score = centroids.sum(axis=1)
        crystal_cluster_numbers = [int(np.argmin(brightness_score) + 1)]

    elif selection_mode == "brightest":
        brightness_score = centroids.sum(axis=1)
        crystal_cluster_numbers = [int(np.argmax(brightness_score) + 1)]

    else:
        raise ValueError("crystal_cluster_selection_mode must be 'darkest', 'brightest', or 'manual'.")

    valid_cluster_numbers = set(range(1, config["tracking_k_value"] + 1))

    for cluster_number in crystal_cluster_numbers:
        if cluster_number not in valid_cluster_numbers:
            raise ValueError(
                f"manual_crystal_cluster_numbers contains {cluster_number}, "
                f"but valid cluster numbers are 1 to {config['tracking_k_value']}."
            )

    return crystal_cluster_numbers


def create_frame_cluster_table_and_binary_mask(
    image,
    roi_mask: np.ndarray,
    roi_label_mask: np.ndarray,
    centroids: np.ndarray,
    crystal_cluster_numbers: List[int],
    config: Dict[str, Any],
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Assign one frame's ROI pixels to k-means clusters and build a crystal mask.

    K-means itself only labels ROI pixels by color cluster. The binary mask is
    created afterward by marking selected cluster numbers as crystal pixels.
    Connected-component analysis uses this mask in the next step.
    """

    roi_pixel_data, channel_values = extract_roi_channel_values(
        image=image,
        roi_mask=roi_mask,
        roi_label_mask=roi_label_mask,
        config=config,
    )

    cluster_labels = assign_pixels_to_kmeans_centroids(
        channel_values=channel_values,
        centroids=centroids,
    )

    roi_pixel_data["kmeans_cluster"] = cluster_labels
    roi_pixel_data["is_crystal_pixel"] = np.isin(cluster_labels, crystal_cluster_numbers)

    image_height = image.shape[0]
    image_width = image.shape[1]

    binary_crystal_mask = np.zeros((image_height, image_width), dtype=bool)

    is_crystal_pixel = roi_pixel_data["is_crystal_pixel"].to_numpy()
    crystal_rows = roi_pixel_data.loc[is_crystal_pixel, "image_row"].to_numpy()
    crystal_columns = roi_pixel_data.loc[is_crystal_pixel, "image_column"].to_numpy()

    binary_crystal_mask[crystal_rows, crystal_columns] = True

    return roi_pixel_data, binary_crystal_mask


def filter_color_analysis_pixels(
    roi_pixel_data: pd.DataFrame,
    config: Dict[str, Any],
) -> pd.DataFrame:
    """Filter ROI pixels for optional crystal-only or non-crystal-only color analysis."""

    pixel_filter = config["color_analysis_pixel_filter"].lower().strip()

    if pixel_filter == "all_roi":
        return roi_pixel_data.copy()

    if pixel_filter == "crystal_only":
        return roi_pixel_data.loc[roi_pixel_data["is_crystal_pixel"]].copy()

    if pixel_filter == "non_crystal_only":
        return roi_pixel_data.loc[~roi_pixel_data["is_crystal_pixel"]].copy()

    raise ValueError(
        "color_analysis_pixel_filter must be 'all_roi', 'crystal_only', or 'non_crystal_only'."
    )


def summarize_frame_color_analysis(
    roi_pixel_data: pd.DataFrame,
    frame_record: Dict[str, Any],
    config: Dict[str, Any],
) -> pd.DataFrame:
    """
    Summarize color values by frame, ROI, cluster, and crystal-pixel status.

    This avoids saving every pixel value by default, but still gives enough
    information to compare crystal pixels vs non-crystal pixels across time.
    """

    filtered_data = filter_color_analysis_pixels(roi_pixel_data, config)
    channel_names = get_channel_names(config)

    if len(filtered_data) == 0:
        return pd.DataFrame()

    group_columns = ["roi_index", "kmeans_cluster", "is_crystal_pixel"]

    summary = (
        filtered_data
        .groupby(group_columns, dropna=False)
        .agg(
            pixel_count=("image_row", "size"),
            **{
                f"{channel_name}_mean": (channel_name, "mean")
                for channel_name in channel_names
            },
            **{
                f"{channel_name}_std": (channel_name, "std")
                for channel_name in channel_names
            },
        )
        .reset_index()
    )

    summary.insert(0, "frame_index", int(frame_record["frame_index"]))
    summary.insert(1, "video_frame_index", int(frame_record["video_frame_index"]))
    summary.insert(2, "time", float(frame_record["time"]))
    summary.insert(3, "time_unit", config["time_unit"])
    summary.insert(4, "color_analysis_pixel_filter", config["color_analysis_pixel_filter"])

    return summary
