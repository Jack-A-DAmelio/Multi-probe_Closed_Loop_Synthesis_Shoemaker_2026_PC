from dashboard_framework.pane import Pane
from dashboard_framework.widgets import (
    Display,
    NumberInput,
    Button
)


class thermocouple_setup(Pane):

    NAME = "thermocouple_setup"

    def build(self):

        # Thermocouple configuration inputs
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


        # Send configuration to the PC server
        self.send = Button(
            label="Send to PC",
            endpoint="/api/thermocouple/setup"
        )


        # Live thermocouple temperature
        self.temperature = Display(
            label="Current Temperature",
            source="/api/thermocouple/temperature"
        )