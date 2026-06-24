"""
ELP USB camera capture test.

Author: Darren Co | Date: 2026-06-23 | Hardware Version: ELP USB Camera

Purpose:
--------
Imports camera functions from capture_elp_camera_image.py, opens the ELP camera,
shows a live preview window, captures one image, and saves it with a timestamp.

This file assumes capture_elp_camera_image.py is in the same folder.
"""

import capture_elp_camera_image as elp


# =========================================================
# MAIN EXECUTION
# =========================================================

elp.create_output_folder(elp.CONFIG["output_folder"])

camera = None

try:
    camera = elp.open_camera(elp.CONFIG["camera_index"])

    should_capture_image = True

    if elp.CONFIG["preview_enabled"]:
        should_capture_image = elp.run_video_preview(
            camera=camera,
            window_name=elp.CONFIG["window_name"],
        )

    if should_capture_image:
        image = elp.capture_single_image(
            camera=camera,
            warmup_frames=elp.CONFIG["warmup_frames"],
        )

        output_file_path = elp.generate_timestamped_filename(
            output_folder=elp.CONFIG["output_folder"],
            image_extension=elp.CONFIG["image_extension"],
        )

        elp.save_image(
            image=image,
            file_path=output_file_path,
        )

    else:
        print("No image was saved.")

except Exception as error:
    print("Image capture failed.")
    print(f"Error: {error}")

finally:
    # Always release the camera so other programs can use it later
    if camera is not None:
        camera.release()
        print("Camera released.")

    elp.cv2.destroyAllWindows()