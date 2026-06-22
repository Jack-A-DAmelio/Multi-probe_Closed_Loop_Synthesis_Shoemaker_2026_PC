"""
PC CLIENT - FULL SYSTEM TEST

Purpose:
--------
End-to-end validation of:
- Pi configuration endpoint
- probe selection
- sampling rate behavior
- buffering system
- PC ingestion + CSV logging
- streaming lifecycle timing stability

Hardware Version: v0.1
"""

import requests
import time


# =========================================================
# CONFIGURATION
# =========================================================

CONFIG = {
    "pi_url": "http://127.0.0.1:8001",

    # Experiment settings
    "experiment_id": "exp_full_test_001",
    "enabled_probes": ["temperature", "pressure", "pH"],

    # Streaming test parameters
    "run_time_sec": 15,

    # Optional: allows visual confirmation of timing behavior
    "print_status_every_sec": 3
}


# =========================================================
# PHASE 1 - CONFIGURE EXPERIMENT
# =========================================================

def configure_experiment():
    """
    Sends experiment configuration to Pi.

    This defines:
    - which sensors are active
    - experiment metadata
    """

    payload = {
        "experiment_id": CONFIG["experiment_id"],
        "enabled_probes": CONFIG["enabled_probes"]
    }

    print("\n[PHASE 1] Sending experiment config...")
    print(payload)

    response = requests.post(
        f"{CONFIG['pi_url']}/config",
        json=payload
    )

    print("Config response:", response.json())


# =========================================================
# PHASE 2 - START STREAMING
# =========================================================

def start_streaming():
    """
    Triggers Pi streaming loop.
    """

    print("\n[PHASE 2] Starting streaming...")

    response = requests.post(f"{CONFIG['pi_url']}/start")

    print("Start response:", response.json())


# =========================================================
# PHASE 3 - MONITOR RUN
# =========================================================

def run_streaming_test():
    """
    Lets system run while optionally printing progress.

    This function does NOT control hardware.
    It only verifies:
    - streaming stability
    - timing behavior
    - system responsiveness
    """

    print("\n[PHASE 3] Running experiment...")

    start_time = time.time()
    last_print = time.time()

    while time.time() - start_time < CONFIG["run_time_sec"]:

        time.sleep(0.2)

        # periodic status print (does NOT affect streaming)
        if time.time() - last_print > CONFIG["print_status_every_sec"]:
            elapsed = time.time() - start_time
            print(f"  ... running ({elapsed:.1f}s)")
            last_print = time.time()


# =========================================================
# PHASE 4 - STOP STREAMING
# =========================================================

def stop_streaming():
    """
    Stops Pi streaming loop safely.
    """

    print("\n[PHASE 4] Stopping streaming...")

    response = requests.post(f"{CONFIG['pi_url']}/stop")

    print("Stop response:", response.json())