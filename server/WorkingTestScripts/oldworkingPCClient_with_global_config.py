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

    This is where we define:
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

'''
# =========================================================
# MAIN TEST RUNNER
# =========================================================

def main():

    print("\n==============================")
    print("FULL SYSTEM TEST START")
    print("==============================")

    # Phase 1: configure experiment
    configure_experiment()

    # Phase 2: start streaming
    start_streaming()

    # Phase 3: run system
    run_streaming_test()

    # Phase 4: stop streaming
    stop_streaming()

    print("\n==============================")
    print("TEST COMPLETE")
    print("==============================")

    print("\nCheck:")
    print("- PC server console output")
    print("- experiment_data.csv")
    print("- correct probe filtering")
    print("- stable timestamps")

'''
#if __name__ == "__main__":
   # main()