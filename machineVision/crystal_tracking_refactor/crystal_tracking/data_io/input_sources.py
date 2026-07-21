"""
Input-source management for single images, image sequences, folders, and MP4s.

The rest of the workflow only needs frame_records. Each record says where the
image is, what analyzed frame number it is, what original source index it came
from, and what time should be assigned to it.
"""

from __future__ import annotations

import glob
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import pandas as pd

from crystal_tracking.data_io.file_io import create_output_folder, save_image, save_table


def prepare_extracted_frame_folder(config: Dict[str, Any]) -> str:
    """Create or clear the extracted frame folder."""

    extracted_frame_folder = os.path.join(
        config["output_folder"],
        config["extracted_frame_folder_name"],
    )

    if os.path.exists(extracted_frame_folder) and config["overwrite_extracted_frames"]:
        shutil.rmtree(extracted_frame_folder)

    create_output_folder(extracted_frame_folder)

    return extracted_frame_folder


def calculate_frame_time(
    video_frame_index: int,
    saved_frame_index: int,
    video_fps: float | None,
    config: Dict[str, Any],
) -> float:
    """Calculate the time assigned to one saved frame."""

    if config["use_video_time"] and video_fps is not None and video_fps > 0:
        return config["time_start"] + video_frame_index / video_fps

    return config["time_start"] + saved_frame_index * config["manual_time_between_saved_frames"]


def extract_frames_from_mp4(config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], float | None]:
    """
    Extract selected frames from an MP4 file.

    Returns
    -------
    frame_records : list of dict
        One dictionary per saved frame. Contains processed frame index, source
        video frame index, time, and image file path.
    video_fps : float or None
        FPS reported by OpenCV. None is returned when the video FPS is invalid.
    """

    video_file_path = config["video_file_path"]

    if not os.path.exists(video_file_path):
        raise FileNotFoundError(f"Could not find MP4 file: {video_file_path}")

    output_folder = config["output_folder"]
    extracted_frame_folder = prepare_extracted_frame_folder(config)

    capture = cv2.VideoCapture(video_file_path)

    if not capture.isOpened():
        raise RuntimeError(f"Could not open video file: {video_file_path}")

    video_fps = float(capture.get(cv2.CAP_PROP_FPS))
    total_video_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if video_fps <= 0:
        video_fps = None

    frame_records: List[Dict[str, Any]] = []
    video_frame_index = 0
    saved_frame_index = 0

    print("")
    print("Extracting frames from MP4...")
    print(f"Video file: {video_file_path}")
    print(f"Reported total video frames: {total_video_frames}")
    print(f"Reported video FPS: {video_fps}")

    while True:
        success, frame_bgr = capture.read()

        if not success:
            break

        should_save_frame = video_frame_index % config["extract_every_nth_frame"] == 0

        if should_save_frame:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            frame_filename = (
                f"frame_{saved_frame_index:05d}"
                f"_video_frame_{video_frame_index:08d}.png"
            )
            frame_file_path = os.path.join(extracted_frame_folder, frame_filename)

            if config["save_extracted_frames"]:
                save_image(frame_rgb, frame_file_path)

            frame_time = calculate_frame_time(
                video_frame_index=video_frame_index,
                saved_frame_index=saved_frame_index,
                video_fps=video_fps,
                config=config,
            )

            frame_records.append({
                "frame_index": int(saved_frame_index),
                "video_frame_index": int(video_frame_index),
                "time": float(frame_time),
                "time_unit": config["time_unit"],
                "image_file_path": frame_file_path,
            })

            saved_frame_index += 1

            if config["maximum_frames_to_process"] is not None:
                if saved_frame_index >= config["maximum_frames_to_process"]:
                    break

        video_frame_index += 1

    capture.release()

    if len(frame_records) == 0:
        raise RuntimeError("No frames were extracted from the MP4 file.")

    frame_record_table = pd.DataFrame(frame_records)
    frame_record_output_path = os.path.join(output_folder, "extracted_frame_records.csv")
    save_table(frame_record_table, frame_record_output_path)

    print(f"Saved extracted-frame record table to: {frame_record_output_path}")
    print(f"Number of extracted frames: {len(frame_records)}")

    return frame_records, video_fps


def create_frame_records_from_image_paths(
    image_file_paths: List[str],
    mode_name: str,
    config: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], None]:
    """
    Create frame records from one or more already-existing image files.

    The selected order is treated as time order.
    """

    if len(image_file_paths) == 0:
        raise ValueError(f"No image files were provided for {mode_name} mode.")

    selected_image_paths = []

    for source_image_index, image_file_path in enumerate(image_file_paths):
        should_process_image = source_image_index % config["extract_every_nth_frame"] == 0

        if not should_process_image:
            continue

        if not os.path.exists(image_file_path):
            raise FileNotFoundError(f"Could not find image file: {image_file_path}")

        selected_image_paths.append((source_image_index, image_file_path))

        if config["maximum_frames_to_process"] is not None:
            if len(selected_image_paths) >= config["maximum_frames_to_process"]:
                break

    if len(selected_image_paths) == 0:
        raise RuntimeError(
            "No images were selected for analysis. Check extract_every_nth_frame "
            "and maximum_frames_to_process."
        )

    frame_records: List[Dict[str, Any]] = []

    for analyzed_frame_index, (source_image_index, image_file_path) in enumerate(selected_image_paths):
        frame_time = (
            config["time_start"]
            + analyzed_frame_index * config["manual_time_between_saved_frames"]
        )

        frame_records.append({
            "frame_index": int(analyzed_frame_index),
            "video_frame_index": int(source_image_index),
            "source_image_index": int(source_image_index),
            "time": float(frame_time),
            "time_unit": config["time_unit"],
            "image_file_path": image_file_path,
        })

    frame_record_table = pd.DataFrame(frame_records)
    frame_record_output_path = os.path.join(config["output_folder"], "input_frame_records.csv")
    save_table(frame_record_table, frame_record_output_path)

    print("")
    print(f"Using {mode_name} mode.")
    print(f"Number of input images found: {len(image_file_paths)}")
    print(f"Number of images selected for analysis: {len(frame_records)}")
    print(f"Saved input-frame record table to: {frame_record_output_path}")

    return frame_records, None


def create_frame_records_from_single_image(config: Dict[str, Any]):
    """Create a one-frame record list from a single image file."""

    return create_frame_records_from_image_paths(
        image_file_paths=[config["image_file_path"]],
        mode_name="single-image test",
        config=config,
    )


def create_frame_records_from_image_list(config: Dict[str, Any]):
    """Create frame records from a manually listed image sequence."""

    image_file_paths = list(config["image_file_paths"])

    return create_frame_records_from_image_paths(
        image_file_paths=image_file_paths,
        mode_name="image-list sequence",
        config=config,
    )


def collect_image_file_paths_from_folder(config: Dict[str, Any]) -> List[str]:
    """Collect supported image paths from the configured input folder."""

    image_folder_path = config["image_folder_path"]

    if not os.path.isdir(image_folder_path):
        raise NotADirectoryError(f"Could not find image folder: {image_folder_path}")

    allowed_extensions = {
        extension.lower()
        for extension in config["image_file_extensions"]
    }

    image_file_paths = []

    for file_path in glob.glob(os.path.join(image_folder_path, "*")):
        if os.path.isfile(file_path):
            extension = os.path.splitext(file_path)[1].lower()

            if extension in allowed_extensions:
                image_file_paths.append(file_path)

    if config["sort_image_inputs_by_name"]:
        image_file_paths = sorted(image_file_paths)

    if len(image_file_paths) == 0:
        raise RuntimeError(
            f"No supported image files were found in folder: {image_folder_path}"
        )

    return image_file_paths


def create_frame_records_from_image_folder(config: Dict[str, Any]):
    """Create frame records from every supported image in a folder."""

    image_file_paths = collect_image_file_paths_from_folder(config)

    return create_frame_records_from_image_paths(
        image_file_paths=image_file_paths,
        mode_name="image-folder sequence",
        config=config,
    )


def build_frame_records(config: Dict[str, Any]):
    """Create frame_records using the configured input mode."""

    input_mode = config["input_mode"].lower().strip()

    if input_mode == "single_image":
        return create_frame_records_from_single_image(config)

    if input_mode == "image_list":
        return create_frame_records_from_image_list(config)

    if input_mode == "image_folder":
        return create_frame_records_from_image_folder(config)

    if input_mode == "mp4":
        return extract_frames_from_mp4(config)

    raise ValueError(
        "input_mode must be 'single_image', 'image_list', 'image_folder', or 'mp4'."
    )
