from fastapi import APIRouter
from pc_server_v2 import PC_STATE
router = APIRouter()

global_value = 0

@app.post("/number")
def receive_number(data: dict):
    print("oooo")
    global global_value

    submitted_value = data["Input Number"]

    global_value = submitted_value + 1

    return {
        "status": "ok",
        "result": global_value
    }


@app.get("/number/result")
def get_result():
    print("new ", global_value)
    return {
        "Server Value": global_value
    }