from dashboard_framework.pane import Pane
from dashboard_framework.widgets import (
    Display,
    TextInput,
    NumberInput,
    Dropdown,
    Checkbox,
    Button, ImageDisplay
)


class example_pane(Pane):
    """
    Example pane demonstrating every widget type.
    """

    NAME = "heater"

    def build(self):

        # Read-only value refreshed from a server source.
        self.temperature = Display(
            label="Temperature",
            source="/api/heater/temperature"
        )

        # Read-only status text refreshed from a server source.
        self.status = Display(
            label="Status",
            source="/api/heater/status"
        )

        # User-entered text value.
        self.operator = TextInput(
            label="Operator Name",
            default=""
        )

        # User-entered numeric value.
        self.setpoint = NumberInput(
            label="Temperature Setpoint",
            default=500
        )

        # User-selected option.
        self.mode = Dropdown(
            label="Operating Mode",
            options=[
                "AUTO",
                "MANUAL",
                "OFF"
            ],
            default="AUTO"
        )

        # User-controlled true/false value.
        self.enabled = Checkbox(
            label="Enable Heater",
            default=False
        )

        # Action button.
        # When clicked, DashAdapter will gather the pane inputs
        # and send them to this endpoint.
        self.apply = Button(
            label="Apply Settings",
            endpoint="/api/heater/apply"
        )
        self.camera = ImageDisplay(
        label="Camera View",
        source="/api/camera/latest"
        )