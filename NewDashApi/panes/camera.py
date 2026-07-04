from dashboard_framework.pane import Pane
from dashboard_framework.widgets import NumberInput, Button, Status


class CameraPane(Pane):

    TITLE = "Camera"
    ORDER = 4

    def build(self):

        # ---------------------------------------------------------
        # INPUTS
        # ---------------------------------------------------------

        self.exposure_time = NumberInput(
            "Exposure Time",
            default=10,
            minimum=1,
            maximum=1000,
            units="ms"
        )

        self.filename = NumberInput(
            "Filename ID",
            default=1
        )

        # ---------------------------------------------------------
        # STATUS DISPLAY
        # ---------------------------------------------------------

        self.status = Status(
            "Ready"
        )

    def on_submit(self, values):
        """
        Called when user presses Confirm button.
        """

        exposure = values.get("Exposure Time")
        filename = values.get("Filename ID")

        # Simple placeholder logic for now
        self.status.value = (
            f"Capturing image {filename} "
            f"at {exposure} ms"
        )

    def refresh(self):
        """
        Optional periodic update.
        """
        pass