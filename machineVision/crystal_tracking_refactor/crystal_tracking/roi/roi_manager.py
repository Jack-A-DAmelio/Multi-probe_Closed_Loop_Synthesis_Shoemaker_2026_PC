"""
ROI management.

The top-level purpose of the project is crystal segmentation/tracking. The inner
ROI behavior is kept here because ROI selection is a separate concern from
k-means, connected components, and tracking.

Multiple ROIs are supported by creating:
1. roi_mask: a boolean mask where True means "analyze this pixel".
2. roi_label_mask: an integer mask where 0 means outside all ROIs, 1 means ROI 1,
   2 means ROI 2, etc.

The k-means code uses roi_mask to decide which pixels can be clustered. The
component code uses roi_label_mask to report which ROI each detected crystal
belongs to.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from matplotlib.widgets import Button, EllipseSelector
from skimage.draw import disk

from crystal_tracking.data_io.file_io import load_image, save_image


def calculate_circle_from_rough_selection(
    x_start: float,
    x_end: float,
    y_start: float,
    y_end: float,
    radius_method: str,
) -> Dict[str, float]:
    """Convert a rough user-drawn ellipse box into a true circular ROI."""

    rough_width = abs(x_end - x_start)
    rough_height = abs(y_end - y_start)

    center_x = (x_start + x_end) / 2
    center_y = (y_start + y_end) / 2

    if radius_method == "average":
        radius = (rough_width + rough_height) / 4
    elif radius_method == "minimum":
        radius = min(rough_width, rough_height) / 2
    elif radius_method == "maximum":
        radius = max(rough_width, rough_height) / 2
    else:
        raise ValueError("radius_method must be 'average', 'minimum', or 'maximum'.")

    return {
        "center_x": float(center_x),
        "center_y": float(center_y),
        "radius": float(radius),
        "x_min": float(center_x - radius),
        "x_max": float(center_x + radius),
        "y_min": float(center_y - radius),
        "y_max": float(center_y + radius),
    }


def normalize_manual_roi(raw_roi: Dict[str, Any], roi_index: int) -> Dict[str, float]:
    """Validate one manually specified ROI and add derived bounds."""

    required_keys = ["center_x", "center_y", "radius"]

    for key in required_keys:
        if key not in raw_roi:
            raise KeyError(f"Manual ROI {roi_index} is missing required key: {key}")

    radius = float(raw_roi["radius"])

    if radius <= 0:
        raise ValueError(f"Manual ROI {roi_index} must have a positive radius.")

    center_x = float(raw_roi["center_x"])
    center_y = float(raw_roi["center_y"])

    return {
        "roi_index": int(raw_roi.get("roi_index", roi_index)),
        "center_x": center_x,
        "center_y": center_y,
        "radius": radius,
        "x_min": float(center_x - radius),
        "x_max": float(center_x + radius),
        "y_min": float(center_y - radius),
        "y_max": float(center_y + radius),
    }


def create_roi_masks(
    image_shape: Tuple[int, ...],
    circle_rois: List[Dict[str, float]],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create boolean and labeled masks from one or more circular ROIs.

    Returns
    -------
    roi_mask : ndarray of bool
        True for pixels inside any ROI.

    roi_label_mask : ndarray of int
        0 outside all ROIs. Inside the ROIs, pixels are labeled with the ROI index.
        If ROIs overlap, the later ROI in circle_rois overwrites the earlier label.
    """

    image_height = image_shape[0]
    image_width = image_shape[1]

    roi_mask = np.zeros((image_height, image_width), dtype=bool)
    roi_label_mask = np.zeros((image_height, image_width), dtype=int)

    for list_position, circle_roi in enumerate(circle_rois, start=1):
        roi_index = int(circle_roi.get("roi_index", list_position))

        row_indices, column_indices = disk(
            center=(circle_roi["center_y"], circle_roi["center_x"]),
            radius=circle_roi["radius"],
            shape=(image_height, image_width),
        )

        roi_mask[row_indices, column_indices] = True
        roi_label_mask[row_indices, column_indices] = roi_index

    return roi_mask, roi_label_mask


def display_image_on_axis(axis, image, title: str) -> None:
    """Display a grayscale or color image on a matplotlib axis."""

    if image.ndim == 2:
        axis.imshow(image, cmap="gray")
    else:
        axis.imshow(image)

    axis.set_title(title)
    axis.set_axis_off()


def draw_current_roi_overlay(axis, circle_roi: Dict[str, float], old_circle_patch):
    """Draw the currently proposed circular ROI before it is accepted."""

    if old_circle_patch is not None:
        old_circle_patch.remove()

    new_circle_patch = Circle(
        xy=(circle_roi["center_x"], circle_roi["center_y"]),
        radius=circle_roi["radius"],
        fill=False,
        linewidth=2.5,
        linestyle="--",
    )

    axis.add_patch(new_circle_patch)
    axis.figure.canvas.draw_idle()

    return new_circle_patch


def draw_accepted_roi_overlay(axis, circle_roi: Dict[str, float], line_width: float):
    """Draw one accepted circular ROI and label it with its ROI index."""

    circle_patch = Circle(
        xy=(circle_roi["center_x"], circle_roi["center_y"]),
        radius=circle_roi["radius"],
        fill=False,
        linewidth=line_width,
    )
    axis.add_patch(circle_patch)

    axis.text(
        circle_roi["center_x"],
        circle_roi["center_y"],
        str(int(circle_roi.get("roi_index", 1))),
        ha="center",
        va="center",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "alpha": 0.7},
    )

    return circle_patch


def draw_all_roi_overlays(axis, circle_rois: List[Dict[str, float]], line_width: float) -> None:
    """Draw all accepted circular ROIs on an axis."""

    for circle_roi in circle_rois:
        draw_accepted_roi_overlay(axis, circle_roi, line_width)


def save_roi_preview(
    image,
    circle_rois: List[Dict[str, float]],
    output_file_path: str,
    config: Dict[str, Any],
) -> None:
    """Save a preview image showing the accepted circular ROI(s)."""

    fig, axis = plt.subplots(figsize=tuple(config["figure_size"]))
    display_image_on_axis(axis=axis, image=image, title="Accepted Circular ROI(s)")
    draw_all_roi_overlays(
        axis=axis,
        circle_rois=circle_rois,
        line_width=config["circle_line_width"],
    )
    fig.savefig(output_file_path, dpi=config["preview_dpi"], bbox_inches="tight")
    plt.close(fig)


def on_select_roi(click_event, release_event, roi_state: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Callback function for rough ROI selection."""

    if click_event.xdata is None or click_event.ydata is None:
        print("Selection started outside the image. Please try again.")
        return

    if release_event.xdata is None or release_event.ydata is None:
        print("Selection ended outside the image. Please try again.")
        return

    circle_roi = calculate_circle_from_rough_selection(
        x_start=click_event.xdata,
        x_end=release_event.xdata,
        y_start=click_event.ydata,
        y_end=release_event.ydata,
        radius_method=config["radius_method"],
    )

    if circle_roi["radius"] < config["minimum_roi_size_pixels"]:
        print("ROI is too small. Please draw a larger rough circle.")
        return

    circle_roi["roi_index"] = int(roi_state["next_roi_index"])
    roi_state["current_roi"] = circle_roi
    roi_state["current_patch"] = draw_current_roi_overlay(
        axis=roi_state["axis"],
        circle_roi=circle_roi,
        old_circle_patch=roi_state["current_patch"],
    )

    print("")
    print(f"Proposed circular ROI {roi_state['next_roi_index']}:")
    print(f"  Center x: {circle_roi['center_x']:.2f} pixels")
    print(f"  Center y: {circle_roi['center_y']:.2f} pixels")
    print(f"  Radius:   {circle_roi['radius']:.2f} pixels")
    print("Click 'Add Another ROI' to store this ROI and draw another, or 'Accept ROI(s)' to finish.")


def commit_current_roi(roi_state: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """
    Move the currently proposed ROI into the accepted ROI list.

    Returns True if a current ROI was accepted. Returns False if there was no
    current ROI to accept.
    """

    if roi_state["current_roi"] is None:
        print("No current ROI has been drawn yet.")
        return False

    accepted_roi = dict(roi_state["current_roi"])
    accepted_roi["roi_index"] = int(roi_state["next_roi_index"])
    roi_state["accepted_rois"].append(accepted_roi)

    if roi_state["current_patch"] is not None:
        roi_state["current_patch"].remove()
        roi_state["current_patch"] = None

    accepted_patch = draw_accepted_roi_overlay(
        axis=roi_state["axis"],
        circle_roi=accepted_roi,
        line_width=config["circle_line_width"],
    )
    roi_state["accepted_patches"].append(accepted_patch)

    print(f"Accepted ROI {accepted_roi['roi_index']}.")

    roi_state["current_roi"] = None
    roi_state["next_roi_index"] += 1
    roi_state["axis"].set_title(
        "Draw another rough circular ROI, or click Accept ROI(s) to continue."
    )
    roi_state["figure"].canvas.draw_idle()

    return True


def add_another_roi(event, roi_state: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Accept the current ROI and keep the selector open for another ROI."""

    commit_current_roi(roi_state, config)


def accept_rois(event, roi_state: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Accept all selected ROIs and close the selector."""

    if roi_state["current_roi"] is not None:
        commit_current_roi(roi_state, config)

    if len(roi_state["accepted_rois"]) == 0:
        print("No ROI has been accepted yet. Draw one ROI first.")
        return

    roi_state["finished"] = True
    plt.close(roi_state["figure"])


def clear_current_roi(event, roi_state: Dict[str, Any]) -> None:
    """Clear only the currently proposed ROI, leaving accepted ROIs unchanged."""

    roi_state["current_roi"] = None

    if roi_state["current_patch"] is not None:
        roi_state["current_patch"].remove()
        roi_state["current_patch"] = None

    roi_state["axis"].set_title("Current ROI cleared. Draw a new rough circular ROI.")
    roi_state["figure"].canvas.draw_idle()

    print("Current ROI cleared. Accepted ROIs were not removed.")


def choose_roi_selection_frame_record(
    frame_records: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Choose which frame/image should be shown for interactive ROI selection."""

    if len(frame_records) == 0:
        raise ValueError("No frame records are available for ROI selection.")

    selection_mode = config["roi_selection_frame"].lower().strip()

    if selection_mode == "first":
        return frame_records[0]

    if selection_mode == "last":
        return frame_records[-1]

    if selection_mode == "index":
        selected_index = int(config["roi_selection_frame_index"])

        if selected_index < 0:
            selected_index = len(frame_records) + selected_index

        if selected_index < 0 or selected_index >= len(frame_records):
            raise IndexError(
                "roi_selection_frame_index is outside the analyzed frame range. "
                f"Valid indices are 0 to {len(frame_records) - 1}."
            )

        return frame_records[selected_index]

    raise ValueError("roi_selection_frame must be 'first', 'last', or 'index'.")


def select_rois_on_image(
    image,
    roi_selection_frame_record: Dict[str, Any],
    config: Dict[str, Any],
) -> List[Dict[str, float]]:
    """
    Select one or more circular ROIs interactively.

    The selector is button-controlled. Draw a rough circular ROI, then choose:
    - Add Another ROI: stores the current ROI and keeps the preview open.
    - Accept ROI(s): stores the current ROI, if one is drawn, and starts analysis.

    This avoids pre-setting the number of ROIs. A future user can still use
    manual_rois in the JSON file when repeatable non-interactive ROIs are needed.
    """

    roi_state = {
        "image": image,
        "figure": None,
        "axis": None,
        "current_roi": None,
        "current_patch": None,
        "accepted_rois": [],
        "accepted_patches": [],
        "next_roi_index": 1,
        "finished": False,
        "ellipse_selector": None,
        "buttons": [],
    }

    figure, axis = plt.subplots(figsize=tuple(config["figure_size"]))
    plt.subplots_adjust(bottom=0.22)

    roi_state["figure"] = figure
    roi_state["axis"] = axis

    display_image_on_axis(
        axis=axis,
        image=image,
        title=(
            "Draw a rough circular ROI. Then click Add Another ROI or Accept ROI(s). "
            f"Frame {roi_selection_frame_record['frame_index']}"
        ),
    )

    roi_state["ellipse_selector"] = EllipseSelector(
        ax=axis,
        onselect=lambda click_event, release_event: on_select_roi(
            click_event,
            release_event,
            roi_state,
            config,
        ),
        useblit=True,
        button=[1],
        minspanx=config["minimum_roi_size_pixels"],
        minspany=config["minimum_roi_size_pixels"],
        spancoords="pixels",
        interactive=True,
    )

    add_button_axis = plt.axes([0.28, 0.06, 0.20, 0.08])
    accept_button_axis = plt.axes([0.50, 0.06, 0.20, 0.08])
    clear_button_axis = plt.axes([0.72, 0.06, 0.18, 0.08])

    add_button = Button(add_button_axis, "Add Another ROI")
    accept_button = Button(accept_button_axis, "Accept ROI(s)")
    clear_button = Button(clear_button_axis, "Clear Current")

    add_button.on_clicked(lambda event: add_another_roi(event, roi_state, config))
    accept_button.on_clicked(lambda event: accept_rois(event, roi_state, config))
    clear_button.on_clicked(lambda event: clear_current_roi(event, roi_state))

    # Store button references so matplotlib does not garbage collect callbacks.
    roi_state["buttons"] = [add_button, accept_button, clear_button]

    print("")
    print("Draw a rough circular ROI on the ROI-selection image/frame.")
    print(
        f"ROI selector image: analyzed frame {roi_selection_frame_record['frame_index']} | "
        f"source index {roi_selection_frame_record['video_frame_index']}"
    )
    print("After drawing an ROI, click 'Add Another ROI' or 'Accept ROI(s)'.")

    plt.show()

    if not roi_state["finished"]:
        raise RuntimeError("No ROI set was accepted. No output files were saved.")

    circle_rois = roi_state["accepted_rois"]

    print("")
    print(f"Accepted {len(circle_rois)} ROI(s). The script will reuse them for every analyzed frame.")

    return circle_rois


def get_configured_rois(
    image,
    roi_selection_frame_record: Dict[str, Any],
    config: Dict[str, Any],
) -> List[Dict[str, float]]:
    """Return ROIs from either manual config entries or the interactive selector."""

    roi_input_mode = config["roi_input_mode"].lower().strip()

    if roi_input_mode == "manual":
        circle_rois = [
            normalize_manual_roi(raw_roi, roi_index=index)
            for index, raw_roi in enumerate(config["manual_rois"], start=1)
        ]

        if len(circle_rois) == 0:
            raise ValueError("manual_rois is empty.")

        return circle_rois

    if roi_input_mode == "interactive":
        return select_rois_on_image(
            image=image,
            roi_selection_frame_record=roi_selection_frame_record,
            config=config,
        )

    raise ValueError("roi_input_mode must be 'interactive' or 'manual'.")


def create_and_save_roi_outputs(
    frame_records: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Tuple[List[Dict[str, float]], np.ndarray, np.ndarray, Dict[str, Any], Any]:
    """
    Choose/select ROIs, create masks, and save ROI preview files.

    Returns
    -------
    circle_rois, roi_mask, roi_label_mask, roi_selection_frame_record, roi_selection_image
    """

    roi_selection_frame_record = choose_roi_selection_frame_record(frame_records, config)
    roi_selection_image = load_image(roi_selection_frame_record["image_file_path"])

    circle_rois = get_configured_rois(
        image=roi_selection_image,
        roi_selection_frame_record=roi_selection_frame_record,
        config=config,
    )

    roi_mask, roi_label_mask = create_roi_masks(
        image_shape=roi_selection_image.shape,
        circle_rois=circle_rois,
    )

    roi_mask_output_path = os.path.join(config["output_folder"], "combined_roi_mask.png")
    roi_label_mask_output_path = os.path.join(config["output_folder"], "roi_label_mask.png")
    roi_preview_output_path = os.path.join(config["output_folder"], "roi_preview.png")

    save_image(
        image=roi_mask.astype(np.uint8) * 255,
        file_path=roi_mask_output_path,
    )

    # Save label mask scaled for visibility. The raw ROI numbers are also saved in metadata.
    label_mask_for_display = roi_label_mask.astype(float)
    if label_mask_for_display.max() > 0:
        label_mask_for_display = label_mask_for_display / label_mask_for_display.max() * 255

    save_image(
        image=label_mask_for_display.astype(np.uint8),
        file_path=roi_label_mask_output_path,
    )

    save_roi_preview(
        image=roi_selection_image,
        circle_rois=circle_rois,
        output_file_path=roi_preview_output_path,
        config=config,
    )

    return circle_rois, roi_mask, roi_label_mask, roi_selection_frame_record, roi_selection_image
