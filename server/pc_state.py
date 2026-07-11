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
        self.enabled_modules = []  # list of active module names
        self.module_pin_directories = []  # list of pin directories for each module
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
    def add_module(self, module_name: str, pin_directory: str):
        """
        Add a module to the list of enabled modules.

        Args:
            module_name (str): Name of the module to enable.
        """
        if module_name not in self.enabled_modules:
            self.enabled_modules.append(module_name)
            self.module_pin_directories[module_name] = pin_directory


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

    #dashboard_data_retrieval-----------------------------------
    def get_latest_data(self, module_name: str):
        return 0 


