import platform
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


class Camera:
    """
    ELP USB camera object.

    Handles:
    - opening the USB camera
    - capturing images
    - saving images
    - closing the camera
    """

    def __init__(self, pin_directory):
        """
        Set up and open the camera.

        Parameters
        ----------
        pin_directory : dict
            Camera configuration dictionary.
            Expected format:
            {"Port Number": 0}
        """

        self.pin_directory = pin_directory

        camera_index = int(
            pin_directory["Port Number"]
        )

        self.camera = cv2.VideoCapture(
            camera_index
        )

        if not self.camera.isOpened():
            raise RuntimeError(
                f"Could not open camera on port {camera_index}"
            )

    # ---------------------------------------------------------
    # Camera setup
    # ---------------------------------------------------------

    def _get_camera_backend(self):
        """
        Select OpenCV backend.

        Returns
        -------
        int
            OpenCV backend constant.
        """

        if (
            platform.system() == "Windows"
            and self.config["use_windows_directshow"]
        ):
            return cv2.CAP_DSHOW

        return cv2.CAP_ANY


    def _open_camera(self, camera_index):
        """
        Open USB camera with retry logic.

        Returns
        -------
        cv2.VideoCapture
            Open camera object.
        """

        backend = self._get_camera_backend()

        retry_count = int(
            self.config["camera_open_retry_count"]
        )

        retry_delay = float(
            self.config["camera_open_retry_delay_seconds"]
        )


        for attempt in range(1, retry_count + 1):

            camera = cv2.VideoCapture(
                camera_index,
                backend
            )

            if camera.isOpened():

                print(
                    f"Camera opened successfully with index {camera_index}"
                )

                return camera


            camera.release()


            if attempt < retry_count:

                print(
                    f"Camera open failed. "
                    f"Retrying in {retry_delay} seconds..."
                )

                time.sleep(retry_delay)


        raise RuntimeError(
            f"Could not open camera index {camera_index}"
        )


    def _is_open(self):
        """
        Check whether camera is available.

        Returns
        -------
        bool
        """

        return (
            self.camera is not None
            and self.camera.isOpened()
        )


    # ---------------------------------------------------------
    # Image capture
    # ---------------------------------------------------------

    def _warmup(self, frames):
        """
        Discard initial frames.

        Parameters
        ----------
        frames : int
            Number of frames to discard.
        """

        if not self._is_open():

            raise RuntimeError(
                "Camera is not open"
            )


        for frame_number in range(int(frames)):

            success, _ = self.camera.read()

            if not success:

                raise RuntimeError(
                    f"Camera failed during warmup frame {frame_number}"
                )


    def take_picture(self):
        """
        Capture one image.

        Returns
        -------
        image : numpy.ndarray
            Captured BGR image.

        capture_time : datetime
            Capture timestamp.
        """

        if not self._is_open():

            raise RuntimeError(
                "Camera is not open"
            )


        warmup_frames = int(
            self.config.get(
                "warmup_frames",
                0
            )
        )


        if warmup_frames > 0:

            self._warmup(
                warmup_frames
            )


        success, image = self.camera.read()

        capture_time = datetime.now()


        if not success:

            raise RuntimeError(
                "Failed to capture image"
            )


        return image, capture_time


    # ---------------------------------------------------------
    # File saving
    # ---------------------------------------------------------

    def save_file(self, image, file_path):
        """
        Save image to disk.

        Parameters
        ----------
        image : numpy.ndarray
            Image from take_picture()

        file_path : str
            Destination path
        """

        Path(file_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )


        success = cv2.imwrite(
            str(file_path),
            image
        )


        if not success:

            raise RuntimeError(
                f"Failed to save image: {file_path}"
            )


        print(
            f"Saved image: {file_path}"
        )


    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------

    def close(self):
        """
        Release camera connection.
        """

        if self.camera is not None:

            self.camera.release()

            self.camera = None

            print(
                "Camera released"
            )