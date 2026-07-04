from dashboard_framework.pane import Pane
from dashboard_framework.widgets import NumberInput, Button, Status


class HeaterPane(Pane):

    TITLE = "Heater"
    ORDER = 5

    def build(self):

        # ---------------------------------------------------------
        # INPUTS
        # ---------------------------------------------------------

        self.temperature_setpoint = NumberInput(
            "Temperature Setpoint",
            default=25,
            minimum=0,
            maximum=200,
            units="°C"
        )

        self.ramp_rate = NumberInput(
            "Ramp Rate",
            default=1,
            minimum=0,
            maximum=50,
            units="°C/min"
        )

        # ---------------------------------------------------------
        # STATUS DISPLAY
        # ---------------------------------------------------------

        self.status = Status(
            "Idle"
        )

    def on_submit(self, values):
        """
        Called when user presses Confirm button.
        """

        temp = values.get("Temperature Setpoint")
        ramp = values.get("Ramp Rate")

        # Placeholder control logic
        self.status.value = (
            f"Heating to {temp}°C "
            f"at {ramp}°C/min"
        )

    def refresh(self):
        """
        Optional periodic update.
        """
        pass