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
    if not 0 <= angle <= 180:
        raise HTTPException(status_code=400, detail="Angle must be between 0 and 180.")
    write_command(f"S2:{angle}")
    return {"status": "ok", "rotate_angle": angle}