import os
import time
from pathlib import Path

import serial
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

app = FastAPI()

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

SERIAL_PORT = os.getenv("ARDUINO_PORT", "/dev/cu.usbserial-10")
BAUD_RATE = int(os.getenv("ARDUINO_BAUD", "9600"))
arduino = None
GRIPPER_OPEN_ANGLE = 0
GRIPPER_CLOSE_ANGLE = 180
ROTATE_BASE_ANGLE = int(os.getenv("ROTATE_BASE_ANGLE", "25"))
ROTATE_RANGE_DEGREES = int(os.getenv("ROTATE_RANGE_DEGREES", "90"))
ROTATE_MIN_ANGLE = max(0, ROTATE_BASE_ANGLE)
ROTATE_MAX_ANGLE = min(180, ROTATE_BASE_ANGLE + ROTATE_RANGE_DEGREES)


@app.on_event("startup")
def connect_arduino() -> None:
    global arduino
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    # Give the board time to reset when serial opens.
    time.sleep(2)


@app.on_event("shutdown")
def disconnect_arduino() -> None:
    if arduino and arduino.is_open:
        arduino.close()


def write_command(command: str) -> None:
    if not arduino or not arduino.is_open:
        raise HTTPException(status_code=503, detail="Arduino serial connection is unavailable.")
    arduino.write(f"{command}\n".encode("utf-8"))


@app.post("/gripper/open")
def gripper_open():
    write_command(f"S1:{GRIPPER_OPEN_ANGLE}")
    return {"status": "ok", "gripper": "open", "angle": GRIPPER_OPEN_ANGLE}


@app.post("/gripper/close")
def gripper_close():
    write_command(f"S1:{GRIPPER_CLOSE_ANGLE}")
    return {"status": "ok", "gripper": "close", "angle": GRIPPER_CLOSE_ANGLE}


@app.post("/rotate/{angle}")
def rotate_servo(angle: int):
    if not ROTATE_MIN_ANGLE <= angle <= ROTATE_MAX_ANGLE:
        raise HTTPException(
            status_code=400,
            detail=f"Angle must be between {ROTATE_MIN_ANGLE} and {ROTATE_MAX_ANGLE}.",
        )
    write_command(f"S2:{angle}")
    return {
        "status": "ok",
        "rotate_angle": angle,
        "rotate_min_angle": ROTATE_MIN_ANGLE,
        "rotate_max_angle": ROTATE_MAX_ANGLE,
        "rotate_base_angle": ROTATE_BASE_ANGLE,
    }