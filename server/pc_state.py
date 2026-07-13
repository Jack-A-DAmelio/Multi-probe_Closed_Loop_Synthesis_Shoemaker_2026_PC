"""
PC shared state object.
"""

from collections import deque
import threading
import time
import os
import csv
from datetime import datetime
from pathlib import Path
import requests


class PCState:

    def __init__(self):

        # Experiment state
        self.experiment_running = False
        self.current_experiment_id = None

        # Data output
        self.output_file_path = None
        self.refresh_rate = 1.0

        # Hardware state
        self.modules = {}
        self.pi_address = None

        # Thread management
        self._experiment_thread = None
        self._lock = threading.Lock()


    # ---------------------------------------------------------
    # Configuration setters
    # ---------------------------------------------------------

    def set_file_path(self, path: str):
        self.output_file_path = path


    def set_refresh_rate(self, rate: float):
        self.refresh_rate = rate


    def set_experiment_id(self, experiment_id: str):
        self.current_experiment_id = experiment_id


    def add_module(self, module_name: str, pin_directory):

        self.modules[module_name] = {
            "pin_directory": pin_directory,
            "latest_value": None
        }


    # ---------------------------------------------------------
    # PI COMMUNICATION
    # ---------------------------------------------------------

    def send_state_to_pi(self):

        if self.pi_address is None:
            raise RuntimeError("Pi address not configured")


        payload = {
            "modules": self.modules
        }


        response = requests.post(
            f"http://{self.pi_address}/configure",
            json=payload,
            timeout=5
        )


        response.raise_for_status()

        return response.json()



    def measure(self):

        if self.pi_address is None:
            raise RuntimeError("Pi address not configured")


        response = requests.post(
            f"http://{self.pi_address}/measure",
            timeout=5
        )


        response.raise_for_status()

        return response.json()



    def cleanup(self):

        if self.pi_address is None:
            return


        requests.post(
            f"http://{self.pi_address}/cleanup",
            timeout=5
        )



    # ---------------------------------------------------------
    # EXPERIMENT LOOP
    # ---------------------------------------------------------

    def start_experiment(self):

        if self.experiment_running:
            return


        # Make sure output directory exists
        if self.output_file_path is None:
            raise RuntimeError(
                "Output file path not configured"
            )


        Path(self.output_file_path).mkdir(
            parents=True,
            exist_ok=True
        )


        # Send hardware configuration
        self.send_state_to_pi()


        self.experiment_running = True


        self._experiment_thread = threading.Thread(
            target=self._experiment_loop,
            daemon=True
        )


        self._experiment_thread.start()


def _experiment_loop(self):

    filename = (
        Path(self.output_file_path)
        /
        f"experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )


    with open(
        filename,
        "w",
        newline=""
    ) as file:


        writer = csv.writer(file)


        writer.writerow(
            [
                "measurement_name",
                "measure",
                "timestamp"
            ]
        )


        while self.experiment_running:

            try:

                # Request one synchronized measurement cycle from Pi
                data = self.measure()


                timestamp = data.get(
                    "timestamp",
                    time.time()
                )


                measurements = data.get(
                    "measurements",
                    {}
                )


                # Loop through all hardware results
                for measurement_name, value in measurements.items():


                    # Update live dashboard state
                    with self._lock:

                        if measurement_name in self.modules:

                            self.modules[
                                measurement_name
                            ][
                                "latest_value"
                            ] = value


                    # Save measurement
                    writer.writerow(
                        [
                            measurement_name,
                            value,
                            timestamp
                        ]
                    )


                file.flush()


            except Exception as e:

                print(
                    "EXPERIMENT LOOP ERROR:",
                    repr(e)
                )


            time.sleep(
                self.refresh_rate
            )


    def stop_experiment(self):

        self.experiment_running = False


        if self._experiment_thread:

            self._experiment_thread.join(
                timeout=5
            )


        self.cleanup()



    # ---------------------------------------------------------
    # Access
    # ---------------------------------------------------------

    def get_latest_data(self, module_name: str):

        if module_name in self.modules:
            return self.modules[module_name]["latest_value"]

        return None



    def __str__(self):

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



PC_STATE = PCState()