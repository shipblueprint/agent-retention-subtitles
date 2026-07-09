# Whisper-Tools Pipeline

Automatic transcription and SRT subtitle generation using **faster-whisper** with shotlist-aligned scene chunking.

---

## Quick Start

```bash
cd /path/to/Whisper-Tools
opencode
```

You land in `@orch` (the default orchestrator). Say:

```
"transcribe this video"
"generate SRT from input/audio.wav"
```

@orch walks through: Ingest → Transcribe → Align → Render.

**Or run a single stage directly:**

```
@whisper-pipeline run the transcribe step
```

---

## Why only @orch shows up?

Each agent declares a `mode`:

| mode | What it means |
|------|---------------|
| `primary` | Loaded automatically, visible as default agent |
| `subagent` | Not auto-loaded — dispatchable by `@name` in chat |

- **@orch** is `mode: primary` — loaded on enter.
- **@whisper-pipeline** is `mode: subagent` — call via `@whisper-pipeline` in chat.

---

## Two workflows

### Full pipeline (via @orch)

```
You describe what to transcribe
        │
  @orch (default)
        │
  ├─ 1. Ingest — resolve audio + load shotlist
  ├─ 2. Transcribe — faster-whisper word timestamps
  ├─ 3. Align — map words to scenes, split into chunks
  └─ 4. Render — write SRT + JSON
```

### Direct stage control (via @whisper-pipeline)

```
You: "@whisper-pipeline run the transcribe step"
              │
      @whisper-pipeline runs the stage directly
      (inspect JSON output, decide next step)
```

---

## Pipeline stages

| # | Stage | Command | Output |
|---|-------|---------|--------|
| 1 | Ingest | `uv run python scripts/run_stage.py ingest` | Resolved audio + shotlist scenes |
| 2 | Transcribe | `uv run python scripts/run_stage.py transcribe` | Word timestamps (text, start, end) |
| 3 | Align | `uv run python scripts/run_stage.py align` | Subtitle chunks per scene |
| 4 | Render | `uv run python scripts/run_stage.py render` | `output/subtitles/edit.srt` + JSON |

---

## All available agents

| Agent | Purpose | Invoke |
|-------|---------|--------|
| **@orch** | Orchestrator — routes requests through the pipeline | Default, or `@orch` |
| **@whisper-pipeline** | Stage-by-stage pipeline runner | `@whisper-pipeline` |

---

## CLI commands

```bash
# Run full pipeline sequentially
uv run python scripts/run_stage.py ingest
uv run python scripts/run_stage.py transcribe
uv run python scripts/run_stage.py align
uv run python scripts/run_stage.py render

# With options
uv run python scripts/run_stage.py ingest --audio input/my_file.wav
uv run python scripts/run_stage.py transcribe --language en
```

---

## Configuration

All settings in `scripts/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `WHISPER_MODEL` | large-v3-turbo | Model size (large-v3-turbo / medium / small) |
| `COMPUTE_TYPE` | int8 | int8 = ~1GB VRAM, float16 = ~3GB VRAM |
| `MAX_CHUNK_DURATION` | 7.0s | Max subtitle chunk length |
| `MAX_CHUNK_CHARS` | 84 | Max subtitle text width |
| `SILENCE_GAP_THRESHOLD` | 0.35s | Word gap considered a pause |
