from fastapi import APIRouter
from pc_state import PC_STATE
router = APIRouter()
# =========================================================
# API USER SUBMISSIONS
# =========================================================
@router.post("/add_module_to_pc_state")
def add_module_to_pc_state(module_name: str, data: dict):

    print("MODULE:", module_name)
    print("DATA:", data)

    PC_STATE.add_module(
        module_name=module_name,
        pin_directory=data
    )

    return {"status": "success"}

    return {"status": "success"}
@router.post("/load_state_to_pi")
def load_state_to_pi():
    """
    Send the current PC state to the Pi for synchronization.
    """
    PC_STATE.send_state_to_pi()
    return


@router.post("/load_experiment_config")
def load_experiment_config(data: dict):
    """
    Load experiment settings into the shared PC state.
    """
    print(data)
    PC_STATE.set_experiment_id(
        data["Experiment Name"]
    )
    PC_STATE.set_sample_name(
        data["Sample Name"]
    )
    PC_STATE.set_file_path(
        data["Data Folder"]
    )

    PC_STATE.set_sample_name(
        data["Sample Name"]
    )

    PC_STATE.set_refresh_rate(
        data["Sample Rate (s per measurement)"]
    )

    return {
        "status": "success"
    }

@router.post("/test_measurement")
def test_measurement():
    """
    Trigger a single measurement.
    """

    PC_STATE.test_measure()

    return {"status": "success"}

# ---------------------------------------------------------
# Experiment Control
# ---------------------------------------------------------

@router.post("/start_experiment")
def start_experiment():
    """
    Start experiment loop.
    """

    PC_STATE.start_experiment()

    return {"status": "success"}


@router.post("/stop_experiment")
def stop_experiment():
    """
    Stop experiment loop.
    """

    PC_STATE.stop_experiment()

    return {"status": "success"}