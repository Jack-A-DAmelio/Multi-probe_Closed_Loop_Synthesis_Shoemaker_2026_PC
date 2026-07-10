from dashboard_framework.pane import Pane
from dashboard_framework.widgets import NumberInput

class scale_setup(Pane):

    NAME = "heater"
    pin_directory = {}
    def build(self):

        self.temperature = NumberInput(
            label="temperature",
            default=25,
            source="http://localhost:5000/api/heater/temperature"
        )

        self.power = NumberInput(
            label="power",
            default=0,
            source="http://localhost:5000/api/heater/power"
        )