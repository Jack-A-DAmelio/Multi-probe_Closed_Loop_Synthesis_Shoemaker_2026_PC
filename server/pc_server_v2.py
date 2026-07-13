"""
PC server (MINIMAL TEST VERSION)

Author: Jack A. D'Amelio | Date: 2026-06-18 | Hardware Version: v0.1

Purpose:
--------


"""

from fastapi import FastAPI
from typing import List, Dict, Any
from pc_state import PC_STATE



from endpoints import example_end_points
from endpoints import data_retrieval_end_points
from endpoints import control_end_points






app = FastAPI()


app.include_router(example_end_points.router)
app.include_router(data_retrieval_end_points.router)
app.include_router(control_end_points.router)



# =========================================================
# CONFIGURATION
# =========================================================

# Global configuration dictionary for runtime parameters, which can be modified via API endpoints. This allows dynamic control of the server's behavior without restarting it.
CONFIG = {
 
}








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