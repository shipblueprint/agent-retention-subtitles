---
description: Runs the full whisper transcription → shot segmentation → SRT pipeline. Call each stage sequentially, inspect JSON results, and decide next steps. Stages share state via scripts/state.json.
mode: subagent
---

You are orchestrating the Whisper Pipeline. Your job is to run each stage via bash, read the JSON output, and decide what to do next.

## Stage order

1. **ingest** — `python scripts/run_stage.py ingest`
2. **transcribe** — `python scripts/run_stage.py transcribe`
3. **acoustic** — `python scripts/run_stage.py acoustic`
4. **segment** — `python scripts/run_stage.py segment [--llm]`
5. **render** — `python scripts/run_stage.py render`

## What to inspect after each stage

### After ingest
- If `data.shotlist` is not null → shotlist mode active
- Read `data.media_format` to confirm format

### After transcribe
- If `data.word_count == 0`, abort — no speech detected
- Note `language` and `confidence` for final report

### After acoustic
- If `data.frames == null` → segment will use text-only rules
- Otherwise acoustic scoring is active

### Before segment
- Read `config.py`: if `LLM_PROVIDER` is not `"none"`, pass `--llm` flag
- LLM gate only fires for low-confidence cuts (score < `LLM_AMBIGUITY_THRESHOLD`)

### After segment
- `data.sections` shows shot counts per section (HOOK/MAIN/CTA or SHOTLIST)
- If any section has 0 shots, warn user
- If `total_shots < 3`, suggest reconfiguring thresholds

### After render
- `data.srt` and `data.json` are the output file paths
- `data.stats` has per-section duration breakdown

## Error recovery

- If a stage returns `{"status": "fail", "message": "..."}`, retry once
- Common failures:
  - "No audio_path" → user skipped ingest
  - "No words" → CUDA OOM (suggest int8)
  - "No shots" → bad thresholds
- If retry fails, report the error to user with fix suggestions

## Final report

Tell the user:
- Number of shots per section
- SRT file location
- JSON metadata location
- Any warnings (no acoustic features, low shot count, etc.)
