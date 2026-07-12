from dashboard_framework.pane import Pane
from dashboard_framework.widgets import (
    Display,
    NumberInput,
    Button
)


class scale_setup(Pane):

    NAME = "scale_setup"

    def build(self):

        # Hardware configuration inputs
        self.power = NumberInput(
            label="Power",
            default=0
        )

        self.ground = NumberInput(
            label="Ground",
            default=0
        )

        self.clock_speed = NumberInput(
            label="Clock Speed",
            default=1000
        )

        self.data_transfer = NumberInput(
            label="Data Transfer",
            default=0
        )


        # Send configuration to PC server
        self.send = Button(
            label="Send to PC",
            endpoint="/api/scale/setup"
        )


        # Live scale measurement
        self.scale_reading = Display(
            label="Current Scale Reading",
            source="/api/scale/reading"
        )