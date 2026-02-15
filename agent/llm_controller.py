import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

client = OpenAI()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
ROTATE_BASE_ANGLE = int(os.getenv("ROTATE_BASE_ANGLE", "25"))
ROTATE_RANGE_DEGREES = int(os.getenv("ROTATE_RANGE_DEGREES", "90"))
ROTATE_MIN_ANGLE = max(0, ROTATE_BASE_ANGLE)
ROTATE_MAX_ANGLE = min(180, ROTATE_BASE_ANGLE + ROTATE_RANGE_DEGREES)

ANALYSIS_RESULTS_PATH = Path(__file__).resolve().parents[1] / "trials" / "analysis_results.json"


def _load_analysis_results() -> str:
    """Load the analysis results JSON as a formatted string."""
    if ANALYSIS_RESULTS_PATH.exists():
        with open(ANALYSIS_RESULTS_PATH) as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    return "{}"


def _extract_params(model_output: str) -> dict:
    """Extract angle and time from the model response."""
    output = model_output.strip()

    angle_match = re.search(r"angle\s*[:=]\s*(\d+)", output, re.IGNORECASE)
    if not angle_match:
        raise ValueError(f"Model response did not contain an angle: {output!r}")
    angle = int(angle_match.group(1))
    if not ROTATE_MIN_ANGLE <= angle <= ROTATE_MAX_ANGLE:
        raise ValueError(
            f"Model angle out of range: {angle}. "
            f"Expected {ROTATE_MIN_ANGLE}..{ROTATE_MAX_ANGLE}."
        )

    time_match = re.search(r"time\s*[:=]\s*(\d+)", output, re.IGNORECASE)
    if not time_match:
        raise ValueError(f"Model response did not contain a time: {output!r}")
    exposure_time = int(time_match.group(1))
    if exposure_time <= 0:
        raise ValueError(f"Model time must be positive, got {exposure_time}.")

    return {"angle": angle, "time": exposure_time}


def choose_experiment_params(angle_history: list[int] | None = None) -> dict:
    analysis_results = _load_analysis_results()

    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": (
                    "You are an AI assistant helping to run a UV light lithography experiment. "
                    "You will be given the results of previous experiments and must choose "
                    "parameters for the next experiment.\n\n"
                    "Here are the results from previous experiments:\n"
                    f"{analysis_results}"
                ),
            },
            {
                "role": "user",
                "content": (
                    "The experiment is a UV light lithography process, where the angle controls "
                    "how high the mask is relative to a UV resin base. The mask is lifted higher "
                    "if the angle is greater, and vice-versa. Another control is how long the "
                    "flashlight is on (time in seconds).\n\n"
                    "The mask is rectangular, so we want to get rectangular shapes. These are the "
                    "first few experiments. Give the parameters I should use for the next experiment "
                    "to get the most rectangular shapes. I want the experiment to be relatively "
                    "different than the others already performed.\n\n"
                    f"The angle must be an integer between {ROTATE_MIN_ANGLE} and {ROTATE_MAX_ANGLE}.\n"
                    "The time must be a positive integer (in seconds).\n\n"
                    "Reply with exactly:\n"
                    "angle: <integer>\n"
                    "time: <integer>"
                ),
            },
        ],
    )

    print(f"LLM response: {response.output_text}")
    return _extract_params(response.output_text)


if __name__ == "__main__":
    params = choose_experiment_params()
    print(f"Generated params: {params}")
