# Whisper-Tools Pipeline

Transcribe audio/video and generate retention-optimized SRT subtitles with shot-aligned timestamps.

## Stages

1. **Ingest** — Resolve audio + load shotlist CSV
2. **Transcribe** — faster-whisper word timestamps (CUDA GPU)
3. **Align** — Map words to scenes, split into subtitle chunks
4. **Render** — Write SRT + JSON to output/subtitles/

## Commands

- `uv run python scripts/run_stage.py ingest`
- `uv run python scripts/run_stage.py transcribe`
- `uv run python scripts/run_stage.py align`
- `uv run python scripts/run_stage.py render`
