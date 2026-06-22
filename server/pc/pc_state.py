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

        # Future optional expansion:
        # self.experiment_start_time = None

        # ---------------------------------------------------------
        # DATA BUFFER (STREAMING INPUT)
        # ---------------------------------------------------------

        # deque chosen for efficient append operations during streaming
        # NOTE: can be bounded later using deque(maxlen=N)
        self.probe_data = deque()

        # ---------------------------------------------------------
        # THREAD SAFETY LOCK
        # ---------------------------------------------------------

        # Ensures safe concurrent access from:
        # - /ingest endpoint (write-heavy)
        # - /latest endpoint (read-heavy)
        self.data_lock = threading.Lock()

        # ---------------------------------------------------------
        # FILE OUTPUT CONTROL
        # ---------------------------------------------------------

        self.save_to_disk_enabled = False  # allows toggling CSV logging
        self.output_file_path = None       # active CSV file path

        # ---------------------------------------------------------
        # MONITORING METADATA
        # ---------------------------------------------------------

        self.last_ingest_timestamp = None  # updated on every packet
        self.total_packets_received = 0     # simple ingestion counter


# =========================================================
# SINGLETON INSTANCE (USED BY FASTAPI)
# =========================================================

PC_STATE = PCState()