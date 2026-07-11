"""
PC server (MINIMAL TEST VERSION)

Author: Jack A. D'Amelio | Date: 2026-06-18 | Hardware Version: v0.1

Purpose:
--------


"""

from fastapi import FastAPI
from typing import List, Dict, Any
import pc_state


PC_STATE = pc_state.PCState()  # Singleton instance of the PCState class, which holds all runtime state for the server. This object is shared across FastAPI endpoints and must be thread-safe.


app = FastAPI()# Initialize FastAPI application instance. This is the server that will handle incoming HTTP requests from the Pi and dashboard clients.


# =========================================================
# CONFIGURATION
# =========================================================

# Global configuration dictionary for runtime parameters, which can be modified via API endpoints. This allows dynamic control of the server's behavior without restarting it.
CONFIG = {
 
}




# =========================================================
# API USER REQUESTS
# =========================================================

@app.get("/get_data")
def get_data(module_name: str):
    """
    Retrieve the latest data for a specific module.
    """
    return PC_STATE.get_latest_data(module_name)
# =========================================================
# API USER SUBMISSIONS
# =========================================================

#confiuring experiment parameters
@app.post("/add_module_to_pc_state")
def add_module_to_pc_state(data: dict):
    """
    Add a new module to the PC state with its corresponding pin directory.
    """
    PC_STATE.add_module(data["module_name"], data["pin_directory"])
    return {"status": "success", "message": f"Module {data['module_name']} added with pin directory {data['pin_directory']}"}

@app.post("/load_state_to_pi")
def load_state_to_pi():
    """
    Send the current PC state to the Pi for synchronization.
    """
    PC_STATE.send_state_to_pi()
    return



@app.post("/test_measurement")
def test_measurement():
    """
    
    """
    PC_STATE.measure()
    return 

# Control loop
@app.post("/start_experiment")
def start_experiment():
    """
    
    """
    PC_STATE.start_experiment()
    return 
@app.post("/stop_experiment")
def stop_experiment():
    """
    
    """
    PC_STATE.stop_experiment()
    return
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