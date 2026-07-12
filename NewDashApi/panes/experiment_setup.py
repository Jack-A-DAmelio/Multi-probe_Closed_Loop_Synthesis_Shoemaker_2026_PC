from dashboard_framework.pane import Pane
from dashboard_framework.widgets import (
    Display,
    TextInput,
    NumberInput,
    Dropdown,
    Checkbox,
    Button, ImageDisplay
)


class experiment_setup(Pane):
    """
    Example pane demonstrating every widget type.
    """

    NAME = "experiment_setup"

    def build(self):
        '''
        # Read-only value refreshed from a server source.
        self.temperature = Display(
            label="Temperature",
            source="/api/heater/temperature"
        )

        '''

        # User-entered text value.
        self.operator = TextInput(
            label="Experiment Name",
            default=""
        )
        self.operator = TextInput(
            label="Data Folder",
            default=""
        )
        self.operator = TextInput(
            label="Sample Name",
            default=""
        )
        # User-entered numeric value.
        self.setpoint = NumberInput(
            label="Sample Rate (s per measurement)",
            default= 60
        )

   

        # Action button.
        # When clicked, DashAdapter will gather the pane inputs
        # and send them to this endpoint.
        self.apply = Button(
            label="Send Settings to PC",
            endpoint="/load_experiment_config"
        )
   