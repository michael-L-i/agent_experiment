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


def post(path: str) -> dict:
    response = requests.post(f"{SERVO_SERVER_URL}{path}", timeout=5)
    response.raise_for_status()
    return response.json()


def run_cycle(angle_history: list[int]) -> int:
    params = choose_experiment_params(angle_history)
    angle = int(params["angle"])

    post("/gripper/open")
    time.sleep(STEP_DELAY_SECONDS)

    post(f"/rotate/{angle}")
    time.sleep(STEP_DELAY_SECONDS)

    post("/gripper/close")
    return angle


if __name__ == "__main__":
    history: list[int] = []
    print("Running experiment loop. Press Ctrl+C to stop.")
    try:
        while True:
            chosen_angle = run_cycle(history)
            history.append(chosen_angle)
            history = history[-ANGLE_HISTORY_SIZE:]
            print(f"Cycle complete with angle {chosen_angle}. History: {history}")
            time.sleep(CYCLE_DELAY_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped by user.")
