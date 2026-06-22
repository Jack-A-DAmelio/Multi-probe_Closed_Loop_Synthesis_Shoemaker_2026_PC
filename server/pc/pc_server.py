"""
PC server (MINIMAL TEST VERSION)

Author: Undergraduate Research Project | Date: 2026-06-18 | Hardware Version: v0.1

Purpose:
--------
Receives streamed data from the Pi and handles:
- in-memory buffering for live visualization
- CSV logging for offline analysis

This server acts as the central data collection layer
between the Pi hardware and the PC dashboard.
"""

from fastapi import FastAPI
from typing import List, Dict, Any
import csv
import os
import time

app = FastAPI()


# =========================================================
# CONFIGURATION
# =========================================================

# Global configuration dictionary for runtime parameters
CONFIG = {
    "csv_file": "experiment_data.csv",  # active output file for logging
    "experiment_id": None               # current experiment identifier
}


# =========================================================
# IN-MEMORY DATA STORAGE
# =========================================================

# Stores raw incoming packets for quick retrieval by dashboard
data_store: List[Dict[str, Any]] = []


# =========================================================
# API ENDPOINT: LATEST DATA
# =========================================================

@app.get("/latest")
def latest():
    """
    Returns most recent 50 packets from memory buffer.

    Returns:
        list[dict]: last 50 streamed packets
    """
    return data_store[-50:]


# =========================================================
# CSV INITIALIZATION
# =========================================================

def init_csv():
    """
    Reinitializes CSV file using current CONFIG["csv_file"].

    This is called whenever a new experiment is started
    or when the output filename is changed.

    NOTE:
    This overwrites the file header each time it is called.
    """

    with open(CONFIG["csv_file"], mode="w", newline="") as f:
        writer = csv.writer(f)

        # CSV header defines expected structure of incoming data
        writer.writerow([
            "experiment_id",
            "timestamp",
            "temperature",
            "pressure",
            "pH"
        ])


# Initialize default CSV file at server startup
init_csv()


# =========================================================
# API ENDPOINT: FILE CONTROL
# =========================================================

@app.post("/filename")
def set_filename(data: dict):
    """
    Sets output CSV filename for logging.

    Parameters:
        data (dict): expects {"filename": str}

    Returns:
        dict: status message + active filename
    """

    filename = data.get("filename")

    if not filename:
        return {"status": "error", "message": "No filename provided"}

    # Ensure consistent file format
    if not filename.endswith(".csv"):
        filename += ".csv"

    CONFIG["csv_file"] = filename

    # Reset CSV file for new experiment logging
    init_csv()

    return {
        "status": "ok",
        "csv_file": CONFIG["csv_file"]
    }


# =========================================================
# API ENDPOINT: EXPERIMENT CONTROL
# =========================================================

@app.post("/experiment")
def set_experiment(data: dict):
    """
    Sets the active experiment identifier.

    Parameters:
        data (dict): expects {"experiment_id": str}

    Returns:
        dict: status + stored experiment_id
    """

    experiment_id = data.get("experiment_id")

    if not experiment_id:
        return {"status": "error", "message": "No experiment_id provided"}

    CONFIG["experiment_id"] = experiment_id

    return {
        "status": "ok",
        "experiment_id": CONFIG["experiment_id"]
    }


# =========================================================
# API ENDPOINT: DATA INGESTION
# =========================================================

@app.post("/ingest")
def ingest(data: dict):
    """
    Receives streamed data packets from Pi and stores them.

    Supports:
    - single packet ingestion
    - batch packet ingestion

    Data is stored in:
    - in-memory buffer (data_store)
    - CSV file (for persistence)

    Parameters:
        data (dict): packet or batch of packets

    Returns:
        dict: status of ingestion
    """

    print("\n--- INGEST RECEIVED ---")

    try:

        # ---------------------------------------------------------
        # HANDLE SINGLE OR BATCH PACKET FORMAT
        # ---------------------------------------------------------

        packets = data["batch"] if "batch" in data else [data]

        for packet in packets:

            sample = packet.get("sample", {})

            # Experiment ID fallback priority:
            # 1. packet-level experiment_id
            # 2. server CONFIG experiment_id
            # 3. fallback string
            experiment_id = packet.get(
                "experiment_id",
                CONFIG.get("experiment_id", "unknown")
            )

            timestamp = packet.get("timestamp", time.time())

            # Store full packet in memory for dashboard access
            data_store.append(packet)

            # -----------------------------------------------------
            # APPEND TO CSV FILE (persistent storage)
            # -----------------------------------------------------

            with open(CONFIG["csv_file"], mode="a", newline="") as f:
                writer = csv.writer(f)

                writer.writerow([
                    experiment_id,
                    timestamp,
                    sample.get("temperature"),
                    sample.get("pressure"),
                    sample.get("pH")
                ])

    except Exception as e:
        print("Ingest error:", e)
        return {"status": "error", "message": str(e)}

    return {"status": "ok"}