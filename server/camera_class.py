
"""
ELP USB Camera class.

Compatible with the PCState camera interface:

    camera = Camera(pin_directory)

    image, capture_time = camera.take_picture()

    camera.save_file(image, file_path)

The camera is opened once when the Camera object is created and remains open
until close() / release() is called.

The pin_directory argument is accepted for compatibility with PCState.
It is not used because the ELP camera is a USB camera rather than a GPIO device.
"""

import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

class Camera:
    """
    ELP USB camera interface for PCState.
    """

    def __init__(
        self,
        pin_directory=None,
        warmup_frames: int = 60,
        use_windows_directshow: bool = True,
        open_retry_count: int = 3,
        open_retry_delay: float = 1.0,
    ):
        # PCState passes pin_directory when creating the camera.
        # The ELP camera is USB-based, so this is not used.
        self.pin_directory = pin_directory

        # Camera configuration
        self.camera_index = int(pin_directory["Port Number"])
        self.warmup_frames = int(warmup_frames)
        self.use_windows_directshow = bool(
            use_windows_directshow
        )

        self.open_retry_count = int(
            open_retry_count
        )

        self.open_retry_delay = float(
            open_retry_delay
        )

        # OpenCV camera object
        self._camera: Optional[
            cv2.VideoCapture
        ] = None

        self._closed = False

        # Open the camera immediately.
        self._open()

        # Warm up once when the camera is initialized.
        if self.warmup_frames > 0:
            self._warmup(
                self.warmup_frames
            )

    # =========================================================
    # CAMERA OPEN / CLOSE
    # =========================================================

    def _get_backend(self) -> int:
        """
        Select the OpenCV camera backend.

        On Windows, DirectShow is generally more reliable for USB cameras.
        """

        if (
            platform.system() == "Windows"
            and self.use_windows_directshow
        ):
            return cv2.CAP_DSHOW

        return cv2.CAP_ANY

    def _open(self) -> None:
        """
        Open the USB camera with retries.
        """

        backend = self._get_backend()

        for attempt in range(
            1,
            self.open_retry_count + 1
        ):
            camera = cv2.VideoCapture(
                self.camera_index,
                backend
            )

            if camera.isOpened():
                self._camera = camera
                self._closed = False

                print(
                    f"ELP camera opened successfully "
                    f"(index={self.camera_index})"
                )

                return

            camera.release()

            if attempt < self.open_retry_count:
                print(
                    f"Could not open ELP camera "
                    f"(index={self.camera_index}). "
                    f"Retrying in "
                    f"{self.open_retry_delay:.1f} seconds..."
                )

                time.sleep(
                    self.open_retry_delay
                )

        raise RuntimeError(
            f"Could not open ELP camera with index "
            f"{self.camera_index}. "
            f"Try changing camera_index to 1, 2, or 3. "
            f"Also close other applications that may be "
            f"using the camera."
        )

    def close(self) -> None:
        """
        Release the camera.
        """

        if self._camera is not None:
            self._camera.release()
            self._camera = None

            print(
                "ELP camera released."
            )

        self._closed = True

    def release(self) -> None:
        """
        Alias for close().
        """

        self.close()

    def __del__(self):
        """
        Best-effort camera cleanup.
        """

        try:
            self.close()
        except Exception:
            pass

    # =========================================================
    # CAMERA STATE
    # =========================================================

    def is_open(self) -> bool:
        """
        Return True if the camera is currently open.
        """

        return (
            self._camera is not None
            and self._camera.isOpened()
            and not self._closed
        )

    # =========================================================
    # CAMERA WARMUP
    # =========================================================

    def _warmup(
        self,
        frame_count: int
    ) -> None:
        """
        Discard initial frames so camera settings can settle.

        This happens once when the Camera object is created.
        """

        if not self.is_open():
            raise RuntimeError(
                "Camera is not open."
            )

        frame_count = int(
            frame_count
        )

        for frame_number in range(
            frame_count
        ):
            success, _ = self._camera.read()

            if not success:
                raise RuntimeError(
                    f"Camera failed during "
                    f"warmup frame {frame_number}."
                )

        print(
            f"ELP camera warmup complete "
            f"({frame_count} frames discarded)."
        )

    # =========================================================
    # IMAGE CAPTURE
    # =========================================================

    def take_picture(
        self
    ) -> Tuple[np.ndarray, datetime]:
        """
        Capture one image.

        This method is called by PCState:

            image, capture_time = self.camera.take_picture()

        Returns
        -------
        image : numpy.ndarray
            Captured image in OpenCV BGR format.

        capture_time : datetime
            Timestamp associated with the captured frame.
        """

        if not self.is_open():
            raise RuntimeError(
                "Camera is not open."
            )

        success, image = self._camera.read()

        # Record the time immediately after OpenCV
        # successfully receives the frame.
        capture_time = datetime.now()

        if not success or image is None:
            raise RuntimeError(
                "Failed to read frame from ELP camera."
            )

        return image, capture_time

    # =========================================================
    # IMAGE SAVING
    # =========================================================

    def save_file(
        self,
        image: np.ndarray,
        file_path: str
    ) -> None:
        """
        Save an image to disk.

        This method is called by PCState:

            self.camera.save_file(
                image,
                str(camera_file)
            )
        """

        if image is None:
            raise ValueError(
                "Cannot save a None image."
            )

        path = Path(
            file_path
        )

        # Make sure the output directory exists.
        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        success = cv2.imwrite(
            str(path),
            image
        )

        if not success:
            raise RuntimeError(
                f"Failed to save camera image to: {path}"
            )

    # =========================================================
    # OPTIONAL CONVENIENCE METHODS
    # =========================================================

    def capture_and_save(
        self,
        file_path: str
    ) -> datetime:
        """
        Capture and save one image.

        Returns the actual capture timestamp.
        """

        image, capture_time = (
            self.take_picture()
        )

        self.save_file(
            image,
            file_path
        )

        return capture_time

    def get_frame_size(
        self
    ) -> Optional[Tuple[int, int]]:
        """
        Return the camera resolution.

        Returns:
            (width, height)

        Returns None if the camera is not open.
        """

        if not self.is_open():
            return None

        width = int(
            self._camera.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            self._camera.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        return width, height
