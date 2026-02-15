import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from llm_controller import choose_experiment_params

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

SERVO_SERVER_URL = os.getenv("SERVO_SERVER_URL", "http://127.0.0.1:8000")
STEP_DELAY_SECONDS = float(os.getenv("STEP_DELAY_SECONDS", "1.0"))
CYCLE_DELAY_SECONDS = float(os.getenv("CYCLE_DELAY_SECONDS", "5.0"))
ANGLE_HISTORY_SIZE = int(os.getenv("ANGLE_HISTORY_SIZE", "5"))
ROTATE_BASE_ANGLE = int(os.getenv("ROTATE_BASE_ANGLE", "25"))


def post(path: str) -> dict:
    response = requests.post(f"{SERVO_SERVER_URL}{path}", timeout=5)
    response.raise_for_status()
    return response.json()


def run_cycle(angle_history: list[int]) -> tuple[int, int]:
    params = choose_experiment_params(angle_history)
    angle = int(params["angle"])
    exposure_time = int(params["time"])

    # Start with gripper closed.
    post("/gripper/open")
    time.sleep(STEP_DELAY_SECONDS)

    # Reset rotate servo to calibrated home for consistent orientation.
    post(f"/rotate/{ROTATE_BASE_ANGLE}")
    time.sleep(STEP_DELAY_SECONDS)

    # Change the angle first, then actuate the gripper.
    post(f"/rotate/{angle}")
    time.sleep(STEP_DELAY_SECONDS)

    # post("/gripper/open")
    # time.sleep(STEP_DELAY_SECONDS)

    # Close gripper (UV light on) and hold for the chosen exposure time.
    post("/gripper/close")

    print(f"UV exposure: sleeping {exposure_time}s at angle {angle}...")
    time.sleep(exposure_time)
    # time.sleep(5)

    post("/gripper/open")
    time.sleep(STEP_DELAY_SECONDS)

    return angle, exposure_time


if __name__ == "__main__":
    history: list[int] = []
    print(
        "Running experiment loop. Press Ctrl+C to stop. "
        f"Rotate base angle: {ROTATE_BASE_ANGLE}"
    )
    try:
        while True:
            chosen_angle, exposure_time = run_cycle(history)
            history.append(chosen_angle)
            history = history[-ANGLE_HISTORY_SIZE:]
            print(
                f"Cycle complete — angle: {chosen_angle}, "
                f"exposure: {exposure_time}s. History: {history}"
            )
            time.sleep(CYCLE_DELAY_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped by user.")
