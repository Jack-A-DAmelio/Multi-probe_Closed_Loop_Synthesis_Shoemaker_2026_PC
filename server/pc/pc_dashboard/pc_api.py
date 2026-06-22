"""
PC API CLIENT (requests wrapper)
Author: Undergraduate Research Project
Date: 2026-06-18
Internal Pi-Hardware Version: v0.1

Purpose:
--------
Lightweight client for communicating with the PC server.
This module ONLY handles HTTP requests (no processing logic).
"""

import requests


# =========================================================
# DATA RETRIEVAL
# =========================================================

def latest(pc_url):
    """
    Fetch last 50 packets from PC server.

    Parameters:
        pc_url (str): Base URL of PC server

    Returns:
        list[dict]: latest streamed data packets
    """

    # HTTP GET request to PC server buffer endpoint
    return requests.get(f"{pc_url}/latest").json()


# =========================================================
# STATUS (optional endpoint)
# =========================================================

def status(pc_url):
    """
    Returns system status from PC server if available.

    Parameters:
        pc_url (str): Base URL of PC server

    Returns:
        dict: status response OR fallback unknown state
    """

    try:
        # Query optional status endpoint (may not exist in early versions)
        return requests.get(f"{pc_url}/status").json()

    except Exception:
        # Safe fallback so dashboard never crashes on missing endpoint
        return {"status": "unknown"}


# =========================================================
# EXPERIMENT CONTROL
# =========================================================

def set_experiment(pc_url, experiment_id):
    """
    Sets experiment ID on PC server.

    Parameters:
        pc_url (str): Base URL of PC server
        experiment_id (str): identifier for experiment session

    Returns:
        dict: server response confirmation
    """

    # Payload sent to PC server experiment endpoint
    payload = {"experiment_id": experiment_id}

    # POST request updates active experiment state on server
    return requests.post(
        f"{pc_url}/experiment",
        json=payload
    ).json()


# =========================================================
# FILE CONTROL
# =========================================================

def set_filename(pc_url, filename):
    """
    Sets CSV filename on PC server.

    Parameters:
        pc_url (str): Base URL of PC server
        filename (str): desired output filename (auto-appends .csv if missing)

    Returns:
        dict: server response confirmation
    """

    # Ensure consistent file format for downstream logging
    if not filename.endswith(".csv"):
        filename += ".csv"

    # Payload sent to server to update logging file
    payload = {"filename": filename}

    # POST request updates CSV file target on server
    return requests.post(
        f"{pc_url}/filename",
        json=payload
    ).json()