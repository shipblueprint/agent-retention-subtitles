# Whisper-Tools

**Automatic transcription and SRT subtitle generation** using faster-whisper. Transcribes audio/video and produces retention-optimized subtitles with shotlist-aligned scene chunking.

Built for [OpenCode](https://opencode.ai) — use via the orchestrator agent or run the pipeline stages directly.

---

## Quick Start

```bash
cd /path/to/Whisper-Tools
opencode
```

You land in `@orch` (the default orchestrator). Say:

```
"transcribe this video"
"generate SRT"
```

Or run a single stage directly:

```
@whisper-pipeline run the transcribe step
```

---

## Why only @orch shows up?

Each agent has a `mode` in its config:

| mode | What it means |
|------|---------------|
| `primary` | Loaded automatically as default agent |
| `subagent` | Not auto-loaded — dispatchable by `@name` in chat |

- **@orch** is `mode: primary` — loads on enter.
- **@whisper-pipeline** is `mode: subagent` — call via `@whisper-pipeline` in chat.

---

## Two workflows

### Workflow A: Full pipeline (via @orch)

```
You describe what to transcribe
        │
  @orch (default)
        │
  ├─ 1. Ingest — resolve audio + load shotlist
  ├─ 2. Transcribe — faster-whisper word timestamps (CUDA GPU)
  ├─ 3. Align — map words to scenes, split into subtitle chunks
  └─ 4. Render — write SRT + JSON to output/subtitles/
```

### Workflow B: Direct stage control (via @whisper-pipeline)

```
You: "@whisper-pipeline run the transcribe step"
              │
      @whisper-pipeline runs the stage directly
      (inspects JSON output, decides next step)
```

| When | Use |
|------|-----|
| Full transcription + SRT | Full pipeline → @orch |
| Debug a specific stage | @whisper-pipeline directly |
| Check config / settings | Read `scripts/config.py` |
| Batch transcribe multiple files | Loop pipeline over `input/` |

---

## All available agents

| Agent | Purpose | Invoke |
|-------|---------|--------|
| **@orch** | Orchestrator — routes requests through the pipeline | Default, or `@orch` |
| **@whisper-pipeline** | Stage-by-stage pipeline runner | `@whisper-pipeline` |

---

## Pipeline stages

| Stage | What it does | Command |
|-------|-------------|---------|
| **Ingest** | Resolve audio file + load shotlist CSV (scene boundaries) | `scripts/transcribe.sh ingest` |
| **Transcribe** | Run faster-whisper with word-level timestamps | `scripts/transcribe.sh transcribe` |
| **Align** | Map words to scenes, split into subtitle chunks (1-7s, ~80 chars) | `scripts/transcribe.sh align` |
| **Render** | Write `edit.srt` and `{name}_chunks.json` | `scripts/transcribe.sh render` |

---

## Setup (one-time)

This repo contains no Python environment. It wraps an existing faster-whisper install
(stt-transcribe) via `scripts/transcribe.sh`.

1. Install stt-transcribe (uv-based) somewhere, e.g. `/mnt/data/Liberary/ai/stt-transcribe`.
2. Link it into this repo:

```bash
ln -s /path/to/stt-transcribe scripts/stt-transcribe
```

Or point at it with an env var:

```bash
export STT_HOME=/path/to/stt-transcribe
```

3. Ensure `scripts/stt-transcribe/.env` exists (CUDA libs, HF cache, offline mode).
   The wrapper sources it automatically.

### Run stages (without OpenCode)

```bash
scripts/transcribe.sh ingest
scripts/transcribe.sh transcribe
scripts/transcribe.sh align
scripts/transcribe.sh render
```

---

## Configuration

Edit `scripts/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `WHISPER_MODEL` | large-v3-turbo | Model size (large-v3-turbo / large-v3 / medium / small) |
| `COMPUTE_TYPE` | int8 | int8 = ~1GB VRAM, float16 = ~3GB VRAM |
| `DEVICE` | cuda | cuda or cpu (auto-falls back) |
| `MAX_CHUNK_DURATION` | 7.0s | Max subtitle chunk length |
| `MAX_CHUNK_CHARS` | 84 | Max subtitle text width |
| `SILENCE_GAP_THRESHOLD` | 0.35s | Word gap considered a breath pause |

---

## Requirements

| Component | Requirement |
|-----------|-------------|
| **GPU** | NVIDIA with CUDA support |
| **VRAM** | 6GB+ recommended (int8 mode uses ~1GB) |
| **Driver** | NVIDIA driver 525+ |
| **Runtime** | Python via linked stt-transcribe (.venv) |

---

## Project structure

```
├── .opencode/
│   ├── agent/
│   │   ├── orch.md              # Orchestrator (primary)
│   │   └── whisper-pipeline.md  # Pipeline runner (subagent)
│   ├── pipelines/
│   │   └── whisper-tools/
│   │       └── OPENCODE.md      # Pipeline stage definition
│   └── skills/
│       └── whisper-pipeline/    # Pipeline orchestration skill
├── input/                       # Place audio/video here
├── output/subtitles/            # Generated SRT + JSON
├── scripts/
│   ├── transcribe.sh            # Wrapper around linked stt-transcribe
│   ├── stt-transcribe           # Symlink to faster-whisper install (gitignored)
│   ├── run_stage.py             # CLI entry point
│   ├── config.py                # All settings
│   ├── stage_ingest.py          # Media discovery + shotlist
│   ├── stage_transcribe.py      # faster-whisper
│   ├── stage_align.py           # Word-to-scene alignment + chunking
│   └── stage_render.py          # SRT + JSON output
├── AGENTS.md                    # Multi-IDE agent definitions
├── OPENCODE.md                  # OpenCode runtime instructions
├── opencode.json                # OpenCode config (default_agent: orch)
└── README.md                    # This file
```

---

## Troubleshooting

### "CUDA out of memory"
```python
# In scripts/config.py
COMPUTE_TYPE = "int8"    # Use int8 mode (~1GB VRAM)
```

### "No module named 'faster_whisper'"
Re-link `scripts/stt-transcribe` and verify its `.venv`.

### "NVIDIA GPU not detected"
- Install latest NVIDIA drivers (525+)
- Verify with `nvidia-smi`

### "HuggingFace hub error: Unknown scheme for proxy URL"
`install.sh` automatically unsets `all_proxy` if it starts with `socks://` (httpx cannot handle SOCKS schemes). If you see this error, verify with:
```bash
env | grep -i proxy
```
The workaround is to unset the SOCKS proxy before running:
```bash
unset all_proxy ALL_PROXY
./install.sh
```

### Audio gap detection
The align stage detects silence between words to create natural cut points:

```
Word timestamps from WhisperX:
  "However" ends at 1.450s
  "we" starts at 1.900s
  Gap = 450ms silence
  If gap >= 350ms → natural break!
```

Tune `SILENCE_GAP_THRESHOLD` in `scripts/config.py`:

| Threshold | Feel |
|-----------|------|
| 0.25s | Very snappy |
| 0.30s | Smooth |
| 0.35s | Natural (default) |
| 0.40s+ | Documentary pace |

---

## License

MIT
