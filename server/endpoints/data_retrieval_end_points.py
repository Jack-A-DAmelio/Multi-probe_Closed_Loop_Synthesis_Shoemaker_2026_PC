from fastapi import APIRouter
from pc_server_v2 import PC_STATE
router = APIRouter()

@app.get("/get_data")
def get_data(module_name: str):
    """
    Retrieve the latest data for a specific module.
    """
    return PC_STATE.get_latest_data(module_name)