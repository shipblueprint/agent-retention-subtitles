# Whisper-Tools Pipeline

Automatic transcription and SRT subtitle generation using faster-whisper with shotlist-aligned scene chunking.

**Output:** `output/subtitles/edit.srt` (subtitles) + `output/subtitles/{name}_chunks.json` (metadata)

## Stages

### Stage 1: Ingest
Resolve audio file and load shotlist CSV (scene boundaries from toolstack-pipeline).

```bash
scripts/transcribe.sh ingest [--audio path] [--shotlist path]
```

### Stage 2: Transcribe
Run faster-whisper with word-level timestamps. GPU (CUDA) with int8 fallback.

```bash
scripts/transcribe.sh transcribe [--language en]
```

### Stage 3: Align
Map transcribed words to scenes and split long scenes into readable subtitle chunks (1-7s, ~80 chars) at natural break points.

```bash
scripts/transcribe.sh align
```

### Stage 4: Render
Write SRT subtitles and JSON chunk metadata to `output/subtitles/`.

```bash
scripts/transcribe.sh render
```

## State

Stages share state via `scripts/state.json` (auto-created, auto-read). Each stage reads previous output and enriches the state.

## Configuration

All settings in `scripts/config.py`:
- `WHISPER_MODEL` — model size (large-v3-turbo / medium / small)
- `COMPUTE_TYPE` — int8 (~1GB VRAM) or float16 (~3GB VRAM)
- `MIN_CHUNK_DURATION` / `MAX_CHUNK_DURATION` — subtitle timing
- `MAX_CHUNK_CHARS` — subtitle text width limit
