"""
ELP USB camera image capture script.

Author: Darren Co | Date: 2026-06-23 | Hardware Version: ELP USB Camera

Purpose:
--------
Turns on an ELP digital USB camera, captures one image, and saves it
with the current date and time in the filename.

This script assumes the ELP camera appears as a normal USB webcam.
"""

import os
from datetime import datetime

import cv2


# =========================================================
# USER SETTINGS
# =========================================================

CONFIG = {
    "camera_index": 0,              # Try 0 first. If wrong camera opens, try 1, 2, etc.
    "output_folder": "raw_images",  # Keeps original camera images separate from processed data
    "image_extension": "png",       # Use png to avoid compression artifacts
    "warmup_frames": 60,            # Allows exposure/white balance to stabilize
    "preview_enabled": True,        # Shows live video before taking picture
    "window_name": "ELP Camera Live Preview",
}


# =========================================================
# CAMERA FUNCTIONS
# =========================================================

def create_output_folder(output_folder):
    """
    Create the output folder if it does not already exist.

    Parameters:
        output_folder (str): Folder path where images will be saved.

    Returns:
        None
    """

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")


def generate_timestamped_filename(output_folder, image_extension):
    """
    Generate a filename using the current date and time.

    Parameters:
        output_folder (str): Folder where the image will be saved.
        image_extension (str): Image file extension, such as 'png' or 'jpg'.

    Returns:
        str: Full file path for the saved image.
    """

    current_time = datetime.now()

    # Format example: 2026-06-23_14-35-08
    timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    filename = f"elp_camera_{timestamp}.{image_extension}"
    file_path = os.path.join(output_folder, filename)

    return file_path


def open_camera(camera_index):
    """
    Open the USB camera.

    Parameters:
        camera_index (int): Camera ID used by OpenCV.

    Returns:
        cv2.VideoCapture: OpenCV camera object.
    """

    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        raise RuntimeError(
            f"Could not open camera with index {camera_index}. "
            "Try changing camera_index to 1, 2, or 3."
        )

    print(f"Camera opened successfully with index {camera_index}")

    return camera


def capture_single_image(camera, warmup_frames):
    """
    Capture one image from the camera.

    Parameters:
        camera (cv2.VideoCapture): OpenCV camera object.
        warmup_frames (int): Number of frames to discard before saving.

    Returns:
        numpy.ndarray: Captured image as an array.
    """

    # Capture a few frames first so auto-exposure and white balance can settle
    for frame_number in range(warmup_frames):
        success, frame = camera.read()

        if not success:
            raise RuntimeError(f"Camera failed during warmup frame {frame_number}")

    success, image = camera.read()

    if not success:
        raise RuntimeError("Failed to capture image from camera")

    return image


def save_image(image, file_path):
    """
    Save the captured image to disk.

    Parameters:
        image (numpy.ndarray): Image array captured from the camera.
        file_path (str): Full output path for saved image.

    Returns:
        None
    """

    success = cv2.imwrite(file_path, image)

    if not success:
        raise RuntimeError(f"Failed to save image to: {file_path}")

    print(f"Saved image: {file_path}")

def run_video_preview(camera, window_name):
    """
    Show a live video preview before capturing an image.

    Parameters:
        camera (cv2.VideoCapture): OpenCV camera object.
        window_name (str): Name shown on the preview window.

    Returns:
        bool: True if user wants to capture an image, False if user cancels.
    """

    print("Live preview started.")
    print("Physically adjust the camera now.")
    print("Press c to capture an image.")
    print("Press q or ESC to cancel.")

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    while True:
        success, frame = camera.read()

        if not success:
            raise RuntimeError("Failed to read frame during video preview")

        # Add simple instructions directly on the video window
        cv2.putText(
            frame,
            "Press c to capture | Press q or ESC to cancel",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        cv2.imshow(window_name, frame)

        # waitKey keeps the video window responsive
        key = cv2.waitKey(1) & 0xFF

        if key == ord("c"):
            print("Capture requested.")
            cv2.destroyWindow(window_name)
            return True

        if key == ord("q") or key == 27:  # 27 is ESC
            print("Capture canceled.")
            cv2.destroyWindow(window_name)
            return False

# # =========================================================
# # MAIN EXECUTION
# # =========================================================

# create_output_folder(CONFIG["output_folder"])

# camera = None

# try:
#     camera = open_camera(CONFIG["camera_index"])

#     should_capture_image = True

#     if CONFIG["preview_enabled"]:
#         should_capture_image = run_video_preview(
#             camera=camera,
#             window_name=CONFIG["window_name"],
#         )

#     if should_capture_image:
#         image = capture_single_image(
#             camera=camera,
#             warmup_frames=CONFIG["warmup_frames"],
#         )

#         output_file_path = generate_timestamped_filename(
#             output_folder=CONFIG["output_folder"],
#             image_extension=CONFIG["image_extension"],
#         )

#         save_image(
#             image=image,
#             file_path=output_file_path,
#         )

#     else:
#         print("No image was saved.")

# except Exception as error:
#     print("Image capture failed.")
#     print(f"Error: {error}")

# finally:
#     # Always release the camera so other programs can use it later
#     if camera is not None:
#         camera.release()
#         print("Camera released.")

#     cv2.destroyAllWindows()