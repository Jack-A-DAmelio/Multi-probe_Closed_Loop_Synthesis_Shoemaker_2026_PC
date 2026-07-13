"""
PC shared state object.

Author: You | Date: 2026-06-18 | Hardware Version: v0.1

Purpose:
--------
Holds all runtime state for PC-side experiment control and data ingestion.

This includes:
- incoming streamed data from Pi
- experiment status
- thread-safe data buffer for plotting
- logging / output flags
"""

import threading
from collections import deque


# =========================================================
# SHARED STATE OBJECT
# =========================================================

class PCState:
    """
    Central state container for PC server runtime.

    This object is shared across FastAPI endpoints and must be thread-safe.
    """

    def __init__(self):

        # ---------------------------------------------------------
        # EXPERIMENT CONTROL STATE
        # ---------------------------------------------------------

        self.experiment_running = False  # True when Pi streaming is active
        self.current_experiment_id = None  # identifier set by dashboard


        self.output_file_path = None       # active CSV file path
        self.refresh_rate = 1.0                # data refresh rate in seconds.
        self.modules = {}
        self.pi_address = None  # IP address of the Pi for communication




    #setters for experiment parameters-----------------------------------------
    def set_file_path(self, path: str):
        """
        Set the output file path for data logging.

        Args:
            path (str): Path to the output CSV file.
        """
        self.output_file_path = path
    def set_refresh_rate(self, rate: float):
        """
        Set the data refresh rate for the experiment.

        Args:
            rate (float): Refresh rate in seconds.
        """
        self.refresh_rate = rate
    def set_experiment_id(self, experiment_id: str):
        """
        Set the current experiment identifier.

        Args:
            experiment_id (str): Unique identifier for the experiment.
        """
        self.current_experiment_id = experiment_id
    def add_module(self, module_name: str, pin_directory):

        self.modules[module_name] = {
            "pin_directory": pin_directory,
            "latest_value": None
        }


    # pi interactions---------------------------------------
    def send_state_to_pi(self):
        """
        Send the current state to the Pi for synchronization.

        This function should handle the communication with the Pi to update its state.
        """
        # Implementation for sending state to Pi goes here
        pass
    def measure(self):
        """
        Trigger a measurement on the Pi.

        This function should handle the communication with the Pi to initiate a measurement.
        """
        # Implementation for triggering measurement on Pi goes here
        pass


    #control behavior of experiment loop thread-----------------------------------
    def start_experiment(self):
        #sets experiment_running to True and starts the experiment loop thread
        self.experiment_running = True
        return 0

    def stop_experiment(self):
        #sets experiment_running to False, which should terminate the experiment loop thread
        #send cleanup to pi
        self.experiment_running = False
        return 0 

    def get_latest_data(self, module_name: str):

        if module_name in self.modules:
            return self.modules[module_name]["latest_value"]

        return None

    def __str__(self):
        """
        Return a human-readable summary of the current PC state.
        """

        lines = [
            "========== Experiment Configuration ==========",
            f"Experiment Running : {self.experiment_running}",
            f"Experiment Name    : {self.current_experiment_id}",
            f"Output Folder      : {self.output_file_path}",
            f"Sample Rate (s)    : {self.refresh_rate}",
            f"Pi Address         : {self.pi_address}",
            "",
            "Modules:"
        ]

        if not self.modules:
            lines.append("  None")
        else:
            for name, module in self.modules.items():

                lines.append(f"  {name}")

                lines.append(
                    f"    Latest Value : {module['latest_value']}"
                )

                lines.append(
                    f"    Pin Directory: {module['pin_directory']}"
                )

        return "\n".join(lines)

PC_STATE = PCState()  # Singleton instance of the PCState class, which holds all runtime state for the server. This object is shared across FastAPI endpoints and must be thread-safe.

