from openai import OpenAI
import os
import random
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

client = OpenAI()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
ANGLE_HISTORY_SIZE = int(os.getenv("ANGLE_HISTORY_SIZE", "5"))
ROTATE_BASE_ANGLE = int(os.getenv("ROTATE_BASE_ANGLE", "25"))
ROTATE_RANGE_DEGREES = int(os.getenv("ROTATE_RANGE_DEGREES", "90"))
ROTATE_MIN_ANGLE = max(0, ROTATE_BASE_ANGLE)
ROTATE_MAX_ANGLE = min(180, ROTATE_BASE_ANGLE + ROTATE_RANGE_DEGREES)


def _extract_angle(model_output: str) -> int:
    output = model_output.strip()
    match = re.search(r"-?\d+", output)
    if not match:
        raise ValueError(f"Model response did not contain an integer angle: {output!r}")
    angle = int(match.group())
    if not ROTATE_MIN_ANGLE <= angle <= ROTATE_MAX_ANGLE:
        raise ValueError(
            f"Model angle out of range: {angle}. "
            f"Expected {ROTATE_MIN_ANGLE}..{ROTATE_MAX_ANGLE}."
        )
    return angle


def choose_experiment_params(angle_history: list[int] | None = None) -> dict:
    recent_angles = (angle_history or [])[-ANGLE_HISTORY_SIZE:]
    exclude_text = ", ".join(str(a) for a in recent_angles) if recent_angles else "none"

    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": (
                    "You control an Arduino experiment with a rotate servo. "
                    f"Return exactly one integer angle from {ROTATE_MIN_ANGLE} to {ROTATE_MAX_ANGLE}."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Pick a random valid rotate angle now. "
                    f"Avoid these recent angles: {exclude_text}. "
                    f"The calibrated base orientation is {ROTATE_BASE_ANGLE}."
                ),
            },
        ],
    )

    angle = _extract_angle(response.output_text)
    if angle in recent_angles:
        allowed = [a for a in range(ROTATE_MIN_ANGLE, ROTATE_MAX_ANGLE + 1) if a not in recent_angles]
        if not allowed:
            allowed = list(range(ROTATE_MIN_ANGLE, ROTATE_MAX_ANGLE + 1))
        angle = random.choice(allowed)
    return {"angle": angle}


if __name__ == "__main__":
    params = choose_experiment_params([])
    print(f"Generated params: {params}")
