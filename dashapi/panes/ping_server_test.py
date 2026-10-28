# panes/test_pane.py

from dashboard_framework.pane import Pane
from dashboard_framework.widgets import (
    NumberInput,
    Button,
    Display
)


class ping_server_test(Pane):
    """
    Simple test pane.

    User enters a number.
    Button sends it to the server.
    Display shows the server response.
    """

    NAME = "number_test"

    def build(self):

        # User enters a number.
        self.input_number = NumberInput(
            label="Input Number",
            default=0
        )


        # Button sends all pane inputs to the server.
        self.send_number = Button(
            label="Send Number",
            endpoint="/number"
        )


        # Displays live response from server.
        self.response = Display(
            label="Server Value",
            source="/number/result"
        )