from fastapi import APIRouter
from fastapi.responses import FileResponse
from pc_state import PC_STATE

router = APIRouter()


@router.get("/api/get_data")
def get_data(pane: str, widget: str):

    # ===============================
    # Camera
    # ===============================



    if pane == "camera_setup":

        if widget == "Camera View":

            image_path = PC_STATE.modules.get(
                "camera",
                {}
            ).get(
                "latest_value"
            )

            if image_path is None:
                image_path = "test_image.jpg"

            return FileResponse(
                image_path,
                media_type="image/jpeg"
            )

    return {
        "error": "Unknown pane/widget"
    }


    # ===============================
    # Scale
    # ===============================

    if pane == "scale_setup":

        if widget == "Current Scale Reading":

            return {
                "Current Scale Reading":
                PC_STATE.modules.get("scale", {})
                .get("latest_value", None)
            }


    # ===============================
    # Thermocouple
    # ===============================

    if pane == "thermocouple_setup":

        if widget == "Current Temperature":

            return {
                "Current Temperature":
                PC_STATE.modules.get("thermocouple", {})
                .get("latest_value", None)
            }


    # ===============================
    # Experiment Control
    # ===============================

    if pane == "experiment_control":

        if widget == "Experiment Running":

            return {
                "Experiment Running":
                PC_STATE.experiment_running
            }


        if widget == "Current Configuration":

            return {
                "Current Configuration":
                str(PC_STATE)
            }


    return {
        "error": f"Unknown pane/widget: {pane}/{widget}"
    }


@router.get("/api/experiment/config")
def get_experiment_config():

    return {
        "Current Configuration": str(PC_STATE)
    }


@router.get("/api/experiment/status")
def get_experiment_running():

    return {
        "Experiment Running": PC_STATE.experiment_running
    }