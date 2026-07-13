from fastapi import APIRouter
from pc_state import PC_STATE
router = APIRouter()

global_value = 0

@router.post("/number")
def receive_number(data: dict):
    print("oooo")
    global global_value

    submitted_value = data["Input Number"]

    global_value = submitted_value + 1

    return {
        "status": "ok",
        "result": global_value
    }


@router.get("/number/result")
def get_result():
    print("new ", global_value)
    return {
        "Server Value": global_value
    }