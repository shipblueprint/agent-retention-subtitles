---
name: whisper-pipeline
description: Use when the user wants to transcribe audio/video and generate retention-optimized SRT subtitles with shot segmentation. Runs pipeline stages (ingest, transcribe, acoustic, segment, render) via scripts/run_stage.py with optional LLM boundary gate. Use ONLY for transcription/subtitle/SRT tasks.
version: 2.0.0
author: Whisper-Tools
---

# Whisper Pipeline — OpenCode-Orchestrated SRT Generator

OpenCode manages the pipeline stage-by-stage. Each stage is a standalone CLI script that outputs structured JSON to stdout. OpenCode reads the JSON, inspects results, and decides the next action.

## Pipeline stages

```
OpenCode                      Python CLI
───────                       ─────────
1. Decide: run ingest ──────▶ python scripts/run_stage.py ingest
   Inspect: found shotlist?           │
   ↓                                  │
2. Run transcribe  ───────────▶ python scripts/run_stage.py transcribe
   Inspect: word count, lang          │
   ↓                                  │
3. Run acoustic    ───────────▶ python scripts/run_stage.py acoustic
   Inspect: features extracted?       │
   ↓                                  │
4. Decide: segment mode ──────▶ python scripts/run_stage.py segment [--llm]
   Inspect: shot counts, sections     │
   ↓                                  │
5. Run render      ───────────▶ python scripts/run_stage.py render
   Inspect: file paths, stats         │
   ↓                                  │
6. Report to user              output/subtitles/edit.srt
                                       output/subtitles/{name}_shots.json
```

## How OpenCode orchestrates

Each stage call returns:
```json
{"status": "ok", "message": "...", "data": {...}}
```

OpenCode **reads the data** and makes decisions:

### After ingest
- If `data.shotlist` is not null → shotlist mode is active for segment
- If `data.shotlist` is null → auto-detect (Hook/Main/CTA)

### After transcribe
- Check `data.word_count`. If 0, abort — transcription failed.
- Note `data.language` and `data.confidence` for user report.

### After acoustic
- If `data.features is null` → segment will use text-only rules (less precise)
- If `data.features` has frames → acoustic scoring active

### Before segment
- OpenCode decides: pass `--llm` flag?
  - Check `config.py`: if `LLM_PROVIDER` is not `"none"`, pass `--llm`
  - LLM gate only fires for low-confidence cuts (score < `LLM_AMBIGUITY_THRESHOLD`)

### After segment
- Inspect `data.sections` dict. Expected: HOOK, MAIN, CTA (or SHOTLIST)
- If any section has 0 shots, warn user.
- If total_shots is very low (< 3), suggest reconfiguring.

### After render
- `data.srt` and `data.json` are the output file paths
- `data.stats` has per-section duration breakdown

### Error recovery
- If a stage returns `{"status": "fail", "message": "..."}`, OpenCode retries once, then reports to user with fix suggestions.
- Common failures and remedies:
  - `No audio_path in state` → user skipped ingest, run it first
  - `No words in state` → transcribe failed (CUDA OOM? try int8)
  - `No shots in state` → segment failed (check config thresholds)

## Running a single stage

```bash
python scripts/run_stage.py ingest
python scripts/run_stage.py transcribe
python scripts/run_stage.py acoustic
python scripts/run_stage.py segment          # rule-only
python scripts/run_stage.py segment --llm     # with LLM gate
python scripts/run_stage.py render
```

## State file

Stages share state via `scripts/state.json` (auto-created, auto-read).
OpenCode can also read state.json directly for inspection.

```
scripts/state.json:
{
  "audio_path": "input/my_voice.wav",
  "use_shotlist": false,
  "shotlist_rows": [],
  "words": [{"text": "...", "start": 0.0, "end": 1.2}, ...],
  "features": {"f0": [...], "times": [...], "rms": [...], "centroid": [...]},
  "hook_end_idx": 42,
  "main_end_idx": 150,
  "shots": [{"text": "...", "section": "HOOK", ...}, ...]
}
```

## Configuration

All settings in `scripts/config.py`. Key ones OpenCode should know:

| Setting | Effect | Default |
|---------|--------|---------|
| `WHISPER_MODEL` | Model size (large-v3-turbo / medium / small) | large-v3-turbo |
| `SHOTLIST_ALIGN` | Use xlsx shotlist | True |
| `LLM_PROVIDER` | "none" / "openai" / "anthropic" / "ollama" | none |
| `LLM_API_KEY` | API key for provider | "" |
| `LLM_AMBIGUITY_THRESHOLD` | Score below which LLM reviews cut | 100 |

## Output files

| File | Content |
|------|---------|
| `output/subtitles/edit.srt` | SRT subtitles with retention-optimized shot timings |
| `output/subtitles/{name}_shots.json` | Per-shot metadata with text, timestamps, score, reasons, AI image prompts |

## Files in repo

```
Whisper-Tools/
├── .opencode/
│   ├── skills/
│   │   ├── whisper/              # Original whisper reference skill
│   │   └── whisper-scripts/     # Pipeline orchestration skill (this one)
│   └── agents/
│       └── whisper-pipeline.md
├── scripts/
│   ├── run_stage.py         # CLI entry point (called by OpenCode via bash)
│   ├── stage_ingest.py      # media discovery + shotlist
│   ├── stage_transcribe.py  # faster-whisper
│   ├── stage_acoustic.py    # librosa features
│   ├── stage_segment.py     # rule + LLM shot detection
│   ├── stage_render.py      # SRT + JSON output
│   └── state.json           # auto-generated inter-stage state
├── scripts/
│   ├── config.py            # all settings
│   └── transcribe_srt.py    # legacy entry point
└── input/                   # place media here
```
