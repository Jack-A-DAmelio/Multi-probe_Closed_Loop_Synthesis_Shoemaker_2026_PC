from fastapi import APIRouter
from pc_server_v2 import PC_STATE
router = APIRouter()
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

@app.post("/load_experiment_config")
def load_experiment_config():
    """
    Send the current PC state to the Pi for synchronization.
    """
    #PC_STATE.send_state_to_pi()
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