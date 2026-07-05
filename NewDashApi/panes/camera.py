from dashboard_framework.pane import Pane
from dashboard_framework.widgets import NumberInput, Dropdown


class CameraPane(Pane):

    NAME = "camera"

    TITLE = "Camera"

    API_ENDPOINT = "/api/camera"
    def build(self):

        self.exposure = NumberInput(
            label="exposure",
            default=100
        )

        self.gain = NumberInput(
            label="gain",
            default=1.0
        )

        self.mode = Dropdown(
            label="mode",
            options=["normal", "high_speed"],
            default="normal"
        )