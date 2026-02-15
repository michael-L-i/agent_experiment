# Agent Experiment Controls

This project runs a full looped experiment with two servos:
1. Open gripper servo (fixed state)
2. Rotate second servo to an LLM-chosen random angle (0-180)
3. Close gripper servo (fixed state)

The only varying input per loop is the rotate angle.
The rotate servo is constrained to a calibrated window:
- `ROTATE_BASE_ANGLE` (home orientation)
- `ROTATE_RANGE_DEGREES` (default 90, allowed window is `base..base+range`)

## 1) Upload Arduino sketch

Upload `arduino/servo_listener/servo_listener.ino` to your Arduino Uno.

Protocol:
- `S1:<angle>` controls gripper servo on pin `9`
- `S2:<angle>` controls rotate servo on pin `10`

## 2) Configure environment

Copy `.env.example` to `.env` and set:
- `OPENAI_API_KEY`
- `ARDUINO_PORT` (for example `/dev/cu.usbserial-10` or `/dev/cu.usbmodemXXXX`)
- `ARDUINO_BAUD` (default `9600`)
- `SERVO_SERVER_URL` (default `http://127.0.0.1:8000`)
- `OPENAI_MODEL` (default `gpt-5.2`)
- `STEP_DELAY_SECONDS` (delay between open/rotate/close, default `1.0`)
- `CYCLE_DELAY_SECONDS` (delay between loops, default `5.0`)
- `ANGLE_HISTORY_SIZE` (recent angles to avoid repeating, default `5`)
- `ROTATE_BASE_ANGLE` (calibrated home orientation, example `25`)
- `ROTATE_RANGE_DEGREES` (default `90`, so `25..115` when base is `25`)

## 3) Run the FastAPI server

From `agent_experiment/server`:

`uvicorn main:app --reload`

Server endpoints:
- `POST /gripper/open`
- `POST /rotate/{angle}`
- `POST /gripper/close`

`/rotate/{angle}` enforces the safe rotate window from your calibration.

## 4) Run the experiment loop

From `agent_experiment`:

`python agent/run_experiment.py`

The loop runs until `Ctrl+C`.
Each cycle resets rotate servo to `ROTATE_BASE_ANGLE` first, then runs open -> rotate -> close.
