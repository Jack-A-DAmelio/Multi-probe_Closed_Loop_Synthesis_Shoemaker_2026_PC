"""
ELP USB camera image capture script.

Author: Darren Co / ChatGPT-assisted revision
Date: 2026-06-23
Hardware Version: ELP USB Camera
Software Version: v0.2

Purpose
-------
Open an ELP USB camera, optionally show a live preview, capture one image,
and save the raw image with a filename based on the actual capture time.

The script keeps raw camera images in a clearly named experiment folder so
images from different experiments are less likely to get mixed together.
A processed-image folder is also created, but this script does not write
processed images there. Processed images should be created by later analysis
scripts.

This script assumes the ELP camera appears as a normal USB webcam.
"""

import os
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np


# =========================================================
# USER SETTINGS
# =========================================================

CONFIG = {
    # Camera settings.
    # Try 0 first. If the wrong camera opens, try 1, 2, etc.
    "camera_index": 0,

    # On Windows, DirectShow often opens USB cameras more reliably than the
    # default OpenCV backend. Mac ignores this setting.
    "use_windows_directshow": True,

    # If the camera is busy, the script retries opening it a few times before
    # giving up. This helps when another app has just released the camera.
    "camera_open_retry_count": 3,
    "camera_open_retry_delay_seconds": 1.0,

    # Experiment/output settings.
    # base_output_folder is the parent folder for all camera experiments.
    # This default works on Mac and Windows because Path.home() uses the
    # current user's home folder.
    "base_output_folder": str(Path.home() / "ELP_Camera_Data"),

    # Change this for each experiment so raw images do not get mixed together.
    # Example: "europium_iodate_80C_trial_01"
    "experiment_name": "test_experiment",

    # This script saves raw images here:
    # base_output_folder / experiment_name / raw_image_folder_name
    "raw_image_folder_name": "raw_images",

    # This folder is created for later processed data, but this script does not
    # write processed images. Keeping it here makes the data layout explicit.
    "processed_image_folder_name": "processed_images",
    "create_processed_image_folder": True,

    # Filename settings.
    "filename_prefix": "elp_camera",
    "image_extension": "png",  # Use png to avoid compression artifacts.

    # Capture settings.
    # If True, the script saves the captured image automatically.
    # If False, the image is returned by the function but not written to disk.
    "save_images_automatically": True,

    # Warmup allows auto-exposure and auto-white-balance to settle before a
    # capture. For a controlled experiment, you may set warmup_frames to 0 after
    # the camera settings are stable.
    "warmup_frames": 60,
    "warmup_before_capture_without_preview": True,

    # If preview is enabled, pressing "c" captures the frame currently shown in
    # the preview. The script does not do a second delayed capture after that.
    "preview_enabled": True,
    "window_name": "ELP Camera Live Preview",

    # waitKey delay in milliseconds. A small value keeps the video window
    # responsive while still updating quickly.
    "preview_wait_key_delay_ms": 1,

    # Text drawn on preview window.
    "preview_instruction_text": "Press c to capture | Press q or ESC to cancel",
}


# =========================================================
# OUTPUT FOLDER AND FILENAME FUNCTIONS
# =========================================================

def create_folder(folder_path: str) -> None:
    """
    Create one folder if it does not already exist.

    Parameters
    ----------
    folder_path : str
        Folder path to create.
    """

    Path(folder_path).mkdir(parents=True, exist_ok=True)


def create_experiment_folders(config: Dict) -> Dict[str, str]:
    """
    Create the experiment output folders.

    The raw image folder is where this script saves camera images. The processed
    image folder is created only to keep the experiment layout clear for later
    analysis scripts.

    Parameters
    ----------
    config : dict
        User settings dictionary.

    Returns
    -------
    output_folders : dict
        Dictionary with experiment, raw image, and processed image folder paths.
    """

    base_output_folder = Path(config["base_output_folder"]).expanduser()
    experiment_name = str(config["experiment_name"]).strip()

    if experiment_name == "":
        raise ValueError("experiment_name cannot be blank.")

    experiment_folder = base_output_folder / experiment_name
    raw_image_folder = experiment_folder / config["raw_image_folder_name"]
    processed_image_folder = experiment_folder / config["processed_image_folder_name"]

    create_folder(str(raw_image_folder))

    if config["create_processed_image_folder"]:
        create_folder(str(processed_image_folder))

    output_folders = {
        "experiment_folder": str(experiment_folder),
        "raw_image_folder": str(raw_image_folder),
        "processed_image_folder": str(processed_image_folder),
    }

    print(f"Experiment folder: {output_folders['experiment_folder']}")
    print(f"Raw image folder:  {output_folders['raw_image_folder']}")

    if config["create_processed_image_folder"]:
        print(f"Processed folder:  {output_folders['processed_image_folder']}")

    return output_folders


def clean_image_extension(image_extension: str) -> str:
    """
    Standardize an image extension.

    Parameters
    ----------
    image_extension : str
        Extension such as "png", ".png", "jpg", or ".jpg".

    Returns
    -------
    cleaned_extension : str
        Extension without the leading period.
    """

    cleaned_extension = str(image_extension).lower().strip().lstrip(".")

    if cleaned_extension not in ["png", "jpg", "jpeg", "tif", "tiff", "bmp"]:
        raise ValueError(
            "image_extension must be one of: png, jpg, jpeg, tif, tiff, bmp."
        )

    return cleaned_extension


def generate_timestamped_filename(
    output_folder: str,
    image_extension: str,
    capture_time: datetime,
    filename_prefix: str,
) -> str:
    """
    Generate a filename using the actual image capture time.

    The timestamp is passed in from the capture function instead of created
    during saving. This keeps the filename tied to when the image was taken, not
    when the disk write happened.

    Parameters
    ----------
    output_folder : str
        Folder where the image will be saved.

    image_extension : str
        Image file extension, such as "png" or "jpg".

    capture_time : datetime
        Time when the image was captured from the camera.

    filename_prefix : str
        Start of the filename.

    Returns
    -------
    file_path : str
        Full file path for the saved image.
    """

    cleaned_extension = clean_image_extension(image_extension)

    # Format example: 2026-06-23_14-35-08-123456
    # Microseconds are included so two rapid captures do not overwrite each other.
    timestamp = capture_time.strftime("%Y-%m-%d_%H-%M-%S-%f")

    filename = f"{filename_prefix}_{timestamp}.{cleaned_extension}"
    file_path = Path(output_folder) / filename

    return str(file_path)


# =========================================================
# CAMERA FUNCTIONS
# =========================================================

def is_camera_open(camera: Optional[cv2.VideoCapture]) -> bool:
    """
    Check whether a camera object exists and is open.

    Parameters
    ----------
    camera : cv2.VideoCapture or None
        OpenCV camera object.

    Returns
    -------
    bool
        True if camera exists and is opened by OpenCV.
    """

    return camera is not None and camera.isOpened()


def get_camera_backend(config: Dict) -> int:
    """
    Choose the OpenCV camera backend.

    Returns
    -------
    int
        OpenCV backend constant.
    """

    if platform.system() == "Windows" and config["use_windows_directshow"]:
        return cv2.CAP_DSHOW

    return cv2.CAP_ANY


def open_camera(camera_index: int, config: Dict) -> cv2.VideoCapture:
    """
    Open the USB camera.

    If another program is already using the camera, OpenCV usually cannot force
    that program to release it. In that case, this function retries and then
    raises an error asking the user to close the other camera program.

    Parameters
    ----------
    camera_index : int
        Camera ID used by OpenCV.

    config : dict
        User settings dictionary.

    Returns
    -------
    camera : cv2.VideoCapture
        OpenCV camera object.
    """

    backend = get_camera_backend(config)
    retry_count = int(config["camera_open_retry_count"])
    retry_delay = float(config["camera_open_retry_delay_seconds"])

    for attempt_number in range(1, retry_count + 1):
        camera = cv2.VideoCapture(camera_index, backend)

        if camera.isOpened():
            print(f"Camera opened successfully with index {camera_index}")
            return camera

        camera.release()

        if attempt_number < retry_count:
            print(
                f"Could not open camera index {camera_index}. "
                f"Retrying in {retry_delay:.1f} seconds..."
            )
            time.sleep(retry_delay)

    raise RuntimeError(
        f"Could not open camera with index {camera_index}. "
        "Try changing camera_index to 1, 2, or 3. "
        "Also close other apps that may be using the camera, such as Zoom, "
        "Photo Booth, Teams, or another Python script."
    )


def read_camera_frame(camera: cv2.VideoCapture) -> Tuple[np.ndarray, datetime]:
    """
    Read one frame from an open camera and record the capture time.

    Parameters
    ----------
    camera : cv2.VideoCapture
        OpenCV camera object.

    Returns
    -------
    frame : numpy.ndarray
        Captured image in OpenCV BGR channel order.

    capture_time : datetime
        Time recorded immediately after OpenCV successfully reads the frame.
    """

    if not is_camera_open(camera):
        raise RuntimeError("Camera is not open. Open the camera before reading a frame.")

    success, frame = camera.read()
    capture_time = datetime.now()

    if not success:
        raise RuntimeError("Failed to read frame from camera.")

    return frame, capture_time


def warmup_camera(camera: cv2.VideoCapture, warmup_frames: int) -> None:
    """
    Discard initial frames so automatic camera settings can settle.

    For a controlled experiment, do not warm up before every image if you want
    exposure and white balance to remain as constant as possible. In that case,
    warm up once at the beginning or set warmup_frames to 0.

    Parameters
    ----------
    camera : cv2.VideoCapture
        OpenCV camera object.

    warmup_frames : int
        Number of frames to discard.
    """

    if not is_camera_open(camera):
        raise RuntimeError("Camera is not open. Open the camera before warmup.")

    warmup_frames = int(warmup_frames)

    for frame_number in range(warmup_frames):
        success, _ = camera.read()

        if not success:
            raise RuntimeError(f"Camera failed during warmup frame {frame_number}")


def capture_single_image(
    camera: cv2.VideoCapture,
    warmup_frames: int = 0,
) -> Tuple[np.ndarray, datetime]:
    """
    Capture one image from an already-open camera.

    This function is useful when another function manages opening and releasing
    the camera. It checks that the camera is open before capturing.

    Parameters
    ----------
    camera : cv2.VideoCapture
        OpenCV camera object.

    warmup_frames : int
        Number of frames to discard before capture.

    Returns
    -------
    image : numpy.ndarray
        Captured image in OpenCV BGR channel order.

    capture_time : datetime
        Time when the image was captured from the camera.
    """

    if not is_camera_open(camera):
        raise RuntimeError("Camera is not open. Cannot capture image.")

    if warmup_frames > 0:
        warmup_camera(camera=camera, warmup_frames=warmup_frames)

    image, capture_time = read_camera_frame(camera)

    return image, capture_time


def capture_single_image_from_camera_index(
    camera_index: int,
    config: Dict,
    warmup_frames: int = 0,
) -> Tuple[np.ndarray, datetime]:
    """
    Open a camera, capture one image, and release the camera.

    This is a convenience function for quick one-image capture without manually
    calling open_camera() and camera.release().

    Parameters
    ----------
    camera_index : int
        Camera ID used by OpenCV.

    config : dict
        User settings dictionary.

    warmup_frames : int
        Number of frames to discard before capture.

    Returns
    -------
    image : numpy.ndarray
        Captured image.

    capture_time : datetime
        Capture timestamp.
    """

    camera = None

    try:
        camera = open_camera(camera_index=camera_index, config=config)
        return capture_single_image(camera=camera, warmup_frames=warmup_frames)

    finally:
        if camera is not None:
            camera.release()


# =========================================================
# PREVIEW AND SAVE FUNCTIONS
# =========================================================

def save_image(image: np.ndarray, file_path: str) -> None:
    """
    Save the captured image to disk.

    Parameters
    ----------
    image : numpy.ndarray
        Image array captured from the camera.

    file_path : str
        Full output path for saved image.
    """

    create_folder(str(Path(file_path).parent))

    success = cv2.imwrite(file_path, image)

    if not success:
        raise RuntimeError(f"Failed to save image to: {file_path}")

    print(f"Saved image: {file_path}")


def add_preview_text(frame: np.ndarray, instruction_text: str) -> np.ndarray:
    """
    Add preview instructions to a copy of the frame.

    Parameters
    ----------
    frame : numpy.ndarray
        Camera frame.

    instruction_text : str
        Text to show on the preview.

    Returns
    -------
    preview_frame : numpy.ndarray
        Copy of the frame with text added.
    """

    preview_frame = frame.copy()

    # cv2.putText arguments:
    # - image to draw on
    # - text string
    # - lower-left text location in pixels: (x, y)
    # - font
    # - font scale
    # - text color in BGR order
    # - line thickness in pixels
    cv2.putText(
        preview_frame,
        instruction_text,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    return preview_frame


def run_video_preview(
    camera: cv2.VideoCapture,
    config: Dict,
) -> Tuple[bool, Optional[np.ndarray], Optional[datetime]]:
    """
    Show a live video preview before capturing an image.

    Pressing "c" captures the current preview frame. The preview loop uses
    while True because it should continue until the user chooses either capture
    or cancel.

    Parameters
    ----------
    camera : cv2.VideoCapture
        OpenCV camera object.

    config : dict
        User settings dictionary.

    Returns
    -------
    should_capture : bool
        True if user captured an image, False if user canceled.

    image : numpy.ndarray or None
        Captured image if should_capture is True.

    capture_time : datetime or None
        Capture time if should_capture is True.
    """

    if not is_camera_open(camera):
        raise RuntimeError("Camera is not open. Cannot start preview.")

    window_name = config["window_name"]
    wait_key_delay_ms = int(config["preview_wait_key_delay_ms"])

    print("Live preview started.")
    print("Physically adjust the camera now.")
    print("Press c to capture the current frame.")
    print("Press q or ESC to cancel.")

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    while True:
        frame, frame_capture_time = read_camera_frame(camera)
        preview_frame = add_preview_text(
            frame=frame,
            instruction_text=config["preview_instruction_text"],
        )

        cv2.imshow(window_name, preview_frame)

        # cv2.waitKey(delay) waits delay milliseconds for a key press and also
        # lets OpenCV update the preview window. The "& 0xFF" keeps only the
        # lowest 8 bits, which makes key comparisons more consistent.
        key = cv2.waitKey(wait_key_delay_ms) & 0xFF

        if key == ord("c"):
            print("Capture requested.")
            cv2.destroyWindow(window_name)

            # Return the exact frame that was visible when the user pressed c.
            # This avoids closing the preview and then taking a delayed second
            # image after the sample may have changed.
            return True, frame, frame_capture_time

        if key == ord("q") or key == 27:
            print("Capture canceled.")
            cv2.destroyWindow(window_name)
            return False, None, None


# =========================================================
# MAIN WORKFLOW
# =========================================================

def run_image_capture(config: Dict) -> Optional[str]:
    """
    Run the full one-image capture workflow.

    Parameters
    ----------
    config : dict
        User settings dictionary.

    Returns
    -------
    output_file_path : str or None
        Path to saved image. None if capture was canceled or saving was disabled.
    """

    output_folders = create_experiment_folders(config)
    camera = None

    try:
        camera = open_camera(
            camera_index=int(config["camera_index"]),
            config=config,
        )

        if config["preview_enabled"]:
            should_capture_image, image, capture_time = run_video_preview(
                camera=camera,
                config=config,
            )
        else:
            should_capture_image = True
            warmup_frames = 0

            if config["warmup_before_capture_without_preview"]:
                warmup_frames = int(config["warmup_frames"])

            image, capture_time = capture_single_image(
                camera=camera,
                warmup_frames=warmup_frames,
            )

        if not should_capture_image:
            print("No image was saved.")
            return None

        if not config["save_images_automatically"]:
            print("Image captured, but save_images_automatically is False.")
            return None

        output_file_path = generate_timestamped_filename(
            output_folder=output_folders["raw_image_folder"],
            image_extension=config["image_extension"],
            capture_time=capture_time,
            filename_prefix=config["filename_prefix"],
        )

        save_image(image=image, file_path=output_file_path)

        return output_file_path

    except Exception as error:
        print("Image capture failed.")
        print(f"Error: {error}")
        return None

    finally:
        # release() closes OpenCV's connection to the camera so other programs
        # can use it later.
        if camera is not None:
            camera.release()
            print("Camera released.")

        cv2.destroyAllWindows()


def main() -> None:
    """Run the image capture script using CONFIG."""

    run_image_capture(CONFIG)


if __name__ == "__main__":
    main()
