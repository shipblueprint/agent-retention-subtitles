"""
CLI entry point for each pipeline stage.

OpenCode calls:
    uv run python scripts/run_stage.py <stage> [--option value]

Stages (run in order):
    ingest      → resolve audio + load shotlist.csv → state
    transcribe  → faster-whisper word timestamps    → state
    align       → map words to scenes + split       → state
    render      → write SRT + JSON                   → output/

State persists between stages in scripts/state.json so OpenCode can run each
stage as a separate bash call and inspect the JSON output on stdout.
"""
import sys
import os
import json
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(_SCRIPT_DIR, "state.json")

# Make scripts/ importable as top-level (so `from stage_ingest import run` works
# regardless of the cwd OpenCode invokes us from).
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "audio_path": "",
        "shotlist_path": "",
        "words": [],
        "scenes": [],
        "chunks": [],
    }


def save_state(state: dict):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)


def ok(data: dict = None, message: str = ""):
    result = {"status": "ok", "message": message}
    if data is not None:
        result["data"] = data
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0)


def fail(message: str):
    print(json.dumps({"status": "fail", "message": message}, indent=2))
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Whisper-Tools pipeline stage")
    parser.add_argument(
        "stage",
        choices=["ingest", "transcribe", "align", "render"],
        help="Stage to run",
    )
    parser.add_argument("--audio", help="Override audio path")
    parser.add_argument("--shotlist", help="Override shotlist CSV path")
    parser.add_argument("--language", help="Override language (e.g. 'en')")
    args = parser.parse_args()

    state = load_state()

    try:
        if args.stage == "ingest":
            from stage_ingest import run
            run(state, args)
        elif args.stage == "transcribe":
            from stage_transcribe import run
            run(state, args)
        elif args.stage == "align":
            from stage_align import run
            run(state, args)
        elif args.stage == "render":
            from stage_render import run
            run(state, args)
    except Exception as e:
        fail(f"{args.stage} failed: {e}")


if __name__ == "__main__":
    main()
