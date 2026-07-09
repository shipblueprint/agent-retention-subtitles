# Whisper Pipeline Runner

Run stages sequentially: ingest → transcribe → align → render.
Each stage returns JSON on stdout. Inspect results and decide next steps.

State persists in scripts/state.json between stages.
