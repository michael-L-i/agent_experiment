"""Analyze trial images from UV lithography experiments using OpenAI vision."""

import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

TRIALS_DIR = Path(__file__).resolve().parents[1] / "trials"

SYSTEM_PROMPT = (
    "You are an expert materials-science lab assistant analysing UV lithography results. "
    "The experiment uses UV light projected through a mask onto UV resin to cure rectangular shapes, "
    "similar to photolithography. Evaluate each image of a cured substrate and return ONLY valid JSON "
    "(no markdown fences, no extra text) with exactly this schema:\n"
    "{\n"
    '  "outcome_quality": "<string: overall quality rating, e.g. poor / fair / good / excellent, with a brief reason>",\n'
    '  "resin_layout": "<string: describe the cured resin pattern — shape, coverage, edge definition, '
    'roundness of corners vs expected rectangularity, any defects or irregularities>",\n'
    '  "params": {\n'
    '    "angle": "<string or number: estimated mask/servo angle used, or \'unknown\' if not determinable>",\n'
    '    "time": "<string or number: estimated UV exposure time, or \'unknown\' if not determinable>"\n'
    "  }\n"
    "}\n"
    "Focus on: sharpness of rectangular edges, corner roundness, uniformity of cure, "
    "presence of under/over-cured regions, resin spread beyond the intended mask area, "
    "and overall fidelity to a rectangular target shape."
)


def encode_image(image_path: Path) -> str:
    """Read an image file and return its base64 encoding."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_trial(image_path: Path, trial_name: str) -> dict:
    """Send a trial image to the model and return structured JSON analysis."""
    b64_image = encode_image(image_path)

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "developer", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Analyze this UV lithography trial image ({trial_name}). "
                            "The target shapes are rectangular. Note any roundness, edge quality, "
                            "resin spread, and overall cure quality. Return JSON only."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64_image}",
                        },
                    },
                ],
            },
        ],
    )

    raw = completion.choices[0].message.content.strip()
    # Strip markdown code fences if the model wraps them
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    return json.loads(raw)


def main():
    trial_files = sorted(TRIALS_DIR.glob("trial*.png"))
    if not trial_files:
        print(f"No trial images found in {TRIALS_DIR}")
        return

    results = {}
    for img_path in trial_files:
        trial_name = img_path.stem  # e.g. "trial1"
        print(f"Analyzing {trial_name}...")
        try:
            analysis = analyze_trial(img_path, trial_name)
            results[trial_name] = analysis
            print(json.dumps(analysis, indent=2))
        except Exception as e:
            print(f"  Error analyzing {trial_name}: {e}")
            results[trial_name] = {"error": str(e)}
        print()

    # Write all results to a combined JSON file
    output_path = TRIALS_DIR / "analysis_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
