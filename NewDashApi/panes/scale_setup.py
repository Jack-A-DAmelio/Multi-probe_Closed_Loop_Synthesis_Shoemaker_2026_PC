from dashboard_framework.pane import Pane
from dashboard_framework.widgets import (
    Display,
    NumberInput,
    Button, TextInput
)


class scale_setup(Pane):

    NAME = "scale_setup"

    def build(self):

        # Hardware configuration inputs
        self.power = TextInput(
            label="name",
            default="200g Scale"
        )
        self.sda = NumberInput(
            label="SDA_Pin",
            default=2
        )

        self.scl = NumberInput(
            label="SCL_Pin",
            default=3
        )

        self.i2c_address = TextInput(
            label="i2c_address",
            default="0x2A"
        )

        self.samples = NumberInput(
            label="Samples",
            default=10
        )
        self.active_channel = NumberInput(
            label="active_channel",
            default=1
        )
        self.channel = NumberInput(
            label="channel",
            default=1
        )


        # Send configuration to PC server
        self.send = Button(
            label="Send to PC",
            endpoint="/add_module_to_pc_state?module_name=scale"
        )


        # Live scale measurement
        self.scale_reading = Display(
            label="Current Scale Reading",
            source="/api/get_data"
        )