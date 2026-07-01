"""
PC server (MINIMAL TEST VERSION)

Author: Jack A. D'Amelio | Date: 2026-06-18 | Hardware Version: v0.1

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
import time

app = FastAPI()# Initialize FastAPI application instance. This is the server that will handle incoming HTTP requests from the Pi and dashboard clients.


# =========================================================
# CONFIGURATION
# =========================================================

# Global configuration dictionary for runtime parameters, which can be modified via API endpoints. This allows dynamic control of the server's behavior without restarting it.
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

    with open(CONFIG["csv_file"], mode="w", newline="") as f: #create or overwrite the CSV file specified in the CONFIG dictionary. The 'w' mode ensures that any existing file is cleared, and 'newline=""' prevents extra blank lines on Windows systems.
        writer = csv.writer(f)

        # CSV header defines expected structure of incoming data
        writer.writerow([
            "experiment_id",
            "timestamp",
            "temperature",
            "pressure",
            "pH"
        ])


# Initialize default CSV file at server startup, this line runs when the server is first launched, ensuring that the CSV file is ready to receive data immediately.
init_csv()


# =========================================================
# API ENDPOINT: FILE CONTROL
# =========================================================
#API endpoints are functions which are run when a specific HTTP request is made to the server. The @app.post("/filename") decorator indicates that this function will handle POST requests sent to the "/filename" URL path. This endpoint allows clients (like the dashboard or Pi) to set or change the filename used for logging data to a CSV file.
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
        return {"status": "error", "message": "No filename provided"} #returns the error message to the raspberry pi if no filename is provided in the request data.

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
        return {"status": "error", "message": "No experiment_id provided"}#returns the error message to the raspberry pi if no experiment_id is provided in the request data.

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

        packets = data["batch"] if "batch" in data else [data] #checks if the incoming data contains a "batch" key. If it does, it treats the value as a list of packets; if not, it wraps the single packet in a list for uniform processing.

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

# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    """
    Launches the PC data server.

    Host:
        0.0.0.0
        Allows connections from other machines on the network.

    Port:
        8000
        Must match PC_URL used by both:
        - dashboard
        - Pi streaming logic
    """

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    ) #This line starts the Uvicorn server, which serves the FastAPI application. The 'host' parameter allows external devices on the same network to connect, and 'port' specifies the listening port. The 'reload=False' option disables automatic reloading of the server on code changes, which is suitable for production environments.