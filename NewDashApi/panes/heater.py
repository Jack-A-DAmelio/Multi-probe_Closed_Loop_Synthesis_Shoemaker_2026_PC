from dashboard_framework.pane import Pane
from dashboard_framework.widgets import NumberInput, Dropdown


class HeaterPane(Pane):

    NAME = "heater"

    TITLE = "Heater"

    API_ENDPOINT = "/api/heater"

    def build(self):

        self.temperature = NumberInput(
            label="temperature",
            default=25
        )

        self.mode = Dropdown(
            label="mode",
            options=["auto", "manual"],
            default="auto"
        )