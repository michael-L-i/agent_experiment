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


def _extract_angle(model_output: str) -> int:
    output = model_output.strip()
    match = re.search(r"-?\d+", output)
    if not match:
        raise ValueError(f"Model response did not contain an integer angle: {output!r}")
    angle = int(match.group())
    if not 0 <= angle <= 180:
        raise ValueError(f"Model angle out of range: {angle}")
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
                    "Return exactly one integer angle from 0 to 180."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Pick a random valid rotate angle now. "
                    f"Avoid these recent angles: {exclude_text}."
                ),
            },
        ],
    )

    angle = _extract_angle(response.output_text)
    if angle in recent_angles:
        allowed = [a for a in range(181) if a not in recent_angles]
        if not allowed:
            allowed = list(range(181))
        angle = random.choice(allowed)
    return {"angle": angle}


if __name__ == "__main__":
    params = choose_experiment_params([])
    print(f"Generated params: {params}")
