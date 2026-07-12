from dashboard_framework.pane import Pane
from dashboard_framework.widgets import (
    NumberInput,
    Button,
    ImageDisplay
)


class camera_setup(Pane):

    NAME = "camera_setup"

    def build(self):

        # Camera port number
        self.port = NumberInput(
            label="Port Number",
            default=0
        )

        # Send configuration to the PC server
        self.send = Button(
            label="Send to PC",
            endpoint="/api/camera/setup"
        )

        # Live camera feed
        self.camera = ImageDisplay(
            label="Camera View",
            source="/api/camera/latest"
        )