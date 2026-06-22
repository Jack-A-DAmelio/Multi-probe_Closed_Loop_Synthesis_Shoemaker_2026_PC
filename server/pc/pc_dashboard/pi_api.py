"""
PI API CLIENT (requests wrapper)
Author: Undergraduate Research Project
Date: 2026-06-18
Internal Pi-Hardware Version: v0.1

Purpose:
--------
Lightweight interface for controlling the Pi acquisition server.
Handles experiment configuration and streaming control via HTTP.
"""

import requests


# =========================================================
# CONFIGURE EXPERIMENT
# =========================================================

def configure_experiment(pi_url, experiment_id, enabled_probes):
    """
    Sends experiment configuration to Pi server.

    Parameters:
        pi_url (str): Base URL of Pi server
        experiment_id (str): Unique identifier for experiment session
        enabled_probes (list[str]): List of active sensors/probes

    Returns:
        dict: JSON response from Pi server
    """

    # Payload defines experiment metadata and which sensors are active
    payload = {
        "experiment_id": experiment_id,
        "enabled_probes": enabled_probes
    }

    # Debug prints help confirm configuration before sending
    print("\n[CONFIG] Sending experiment config...")
    print(payload)

    # HTTP POST triggers config update on Pi server
    response = requests.post(f"{pi_url}/config", json=payload)

    return response.json()


# =========================================================
# START STREAMING
# =========================================================

def start_streaming(pi_url):
    """
    Starts data acquisition on Pi server.

    Parameters:
        pi_url (str): Base URL of Pi server

    Returns:
        dict: JSON response confirming streaming state
    """

    print("\n[START] Starting streaming...")  # user-visible debug log

    # POST request triggers hardware acquisition loop
    response = requests.post(f"{pi_url}/start")

    return response.json()


# =========================================================
# STOP STREAMING
# =========================================================

def stop_streaming(pi_url):
    """
    Stops data acquisition on Pi server.

    Parameters:
        pi_url (str): Base URL of Pi server

    Returns:
        dict: JSON response confirming stop state
    """

    print("\n[STOP] Stopping streaming...")  # user-visible debug log

    # POST request halts acquisition loop on Pi
    response = requests.post(f"{pi_url}/stop")

    return response.json()