---
name: whisper-pipeline
description: Use when the user wants to transcribe audio/video and generate SRT subtitles with shot-aligned timestamps. Runs pipeline stages (ingest, transcribe, align, render) via scripts/run_stage.py.
version: 2.0.0
author: Whisper-Tools
---

# Whisper Pipeline — OpenCode-Orchestrated SRT Generator

OpenCode manages the pipeline stage-by-stage. Each stage is a standalone CLI script that outputs structured JSON to stdout. OpenCode reads the JSON, inspects results, and decides the next action.

## Pipeline stages

```
OpenCode                      Python CLI
───────                       ─────────
1. Run ingest  ─────────────▶ scripts/transcribe.sh ingest
   Inspect: audio_path, scene_count
   ↓
2. Run transcribe ──────────▶ scripts/transcribe.sh transcribe
   Inspect: word_count, language, confidence
   ↓
3. Run align ───────────────▶ scripts/transcribe.sh align
   Inspect: chunks_per_scene, empty_scenes, avg_chunk_duration
   ↓
4. Run render ──────────────▶ scripts/transcribe.sh render
   Inspect: file paths, total_chunks, stats
   ↓
5. Report to user             output/subtitles/edit.srt
                              output/subtitles/{name}_chunks.json
```

## How OpenCode orchestrates

Each stage call returns:
```json
{"status": "ok", "message": "...", "data": {...}}
```

OpenCode **reads the data** and makes decisions:

### After ingest
- If `data.scene_count > 0` → shotlist loaded, scenes ready for alignment
- Read `data.audio_path` to confirm which file

### After transcribe
- If `data.word_count == 0`, abort — no speech detected
- Note `data.language` and `data.confidence` for user report

### After align
- `data.chunks_per_scene` shows subtitle distribution
- If any scene has 0 chunks, warn user
- `data.avg_chunk_duration` should be 2-5s for readability

### After render
- `data.srt_path` — SRT file location
- `data.json_path` — JSON metadata location
- `data.total_chunks` and `data.stats` — per-scene duration breakdown

### Error recovery
- If a stage returns `{"status": "fail", "message": "..."}`, retry once, then report to user with fix suggestions
- Common failures:
  - `No audio_path in state` → run ingest first
  - `No words in state` → transcribe failed (CUDA OOM? try int8)
  - `No chunks in state` → align failed (check scene data)

## Running a single stage

```bash
scripts/transcribe.sh ingest
scripts/transcribe.sh transcribe
scripts/transcribe.sh align
scripts/transcribe.sh render
```

## State file

Stages share state via `scripts/state.json` (auto-created, auto-read).

```json
{
  "audio_path": "input/my_audio.wav",
  "scenes": [{"scene": 1, "start": 0.0, "end": 12.5, "text": "..."}],
  "words": [{"text": "hello", "start": 0.0, "end": 0.5}],
  "chunks": [{"text": "...", "start": 0.0, "end": 4.2, "scene": 1}]
}
```

## Configuration

All settings in `scripts/config.py`:

| Setting | Effect | Default |
|---------|--------|---------|
| `WHISPER_MODEL` | Model size | large-v3-turbo |
| `COMPUTE_TYPE` | int8 / float16 | int8 |
| `DEVICE` | cuda / cpu | cuda |
| `MAX_CHUNK_DURATION` | Max subtitle duration | 7.0s |
| `MAX_CHUNK_CHARS` | Max subtitle width | 84 chars |

## Output files

| File | Content |
|------|---------|
| `output/subtitles/edit.srt` | SRT subtitles with shot-timed chunks |
| `output/subtitles/{name}_chunks.json` | Per-chunk metadata with text, timestamps, scene |

## Files in repo

```
Whisper-Tools/
├── .opencode/
│   ├── agent/
│   │   ├── orch.md              # Orchestrator (primary)
│   │   └── whisper-pipeline.md  # Pipeline runner (subagent)
│   ├── pipelines/
│   │   └── whisper-tools/
│   │       └── OPENCODE.md      # Pipeline stage definition
│   └── skills/
│       └── whisper-pipeline/    # This skill
├── scripts/
│   ├── run_stage.py         # CLI entry point (called by OpenCode)
│   ├── stage_ingest.py      # Media discovery + shotlist
│   ├── stage_transcribe.py  # faster-whisper
│   ├── stage_align.py       # Word-to-scene alignment + chunking
│   ├── stage_render.py      # SRT + JSON output
│   ├── config.py            # All settings
│   └── state.json           # Auto-generated inter-stage state
├── input/                   # Place media here
└── output/subtitles/        # Generated SRT + JSON
```
