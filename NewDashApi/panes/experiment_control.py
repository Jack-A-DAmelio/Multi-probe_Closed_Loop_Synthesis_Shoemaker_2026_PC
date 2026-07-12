from dashboard_framework.pane import Pane
from dashboard_framework.widgets import (
    Display,
    Button
)


class experiment_control(Pane):

    NAME = "experiment_control"

    def build(self):

        # Indicates whether an experiment is currently running.
        self.running = Display(
            label="Experiment Running",
            source="/api/experiment/status"
        )

        # Shows the currently loaded experiment configuration.
        self.current_config = Display(
            label="Current Configuration",
            source="/api/experiment/config"
        )

        # Sends the selected hardware modules/configuration to the Pi.
        self.send_modules = Button(
            label="Send Modules to Pi",
            endpoint="/api/experiment/send_modules"
        )

        # Performs a single test measurement.
        self.test_measurement = Button(
            label="Test Measurement",
            endpoint="/api/experiment/test"
        )

        # Starts the experiment.
        self.start = Button(
            label="Start Experiment",
            endpoint="/api/experiment/start"
        )

        # Stops the experiment.
        self.stop = Button(
            label="End Experiment",
            endpoint="/api/experiment/stop"
        )

        # Cleans up hardware and software resources.
        self.cleanup = Button(
            label="Clean Up",
            endpoint="/api/experiment/cleanup"
        )