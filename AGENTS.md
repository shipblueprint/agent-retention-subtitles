# Whisper-Tools — Agent Definitions

Multi-IDE agent definitions for Cline, Roo, Claude Code, OpenCode, Pi, and compatible agents.

---

## Agents

### @orch — Whisper-Tools Orchestrator (default)

The central orchestrator. Routes transcription requests through the 4-stage pipeline: Ingest → Transcribe → Align → Render.

```
Agent: orch
Type: orchestrator
Pipeline: whisper-tools
Stages: Ingest, Transcribe, Align, Render
Trigger: @orch (default)
Skills: whisper-pipeline
```

### @whisper-pipeline — Pipeline Runner

Runs the full transcription pipeline stage-by-stage. Each stage is a CLI tool that outputs JSON. Inspects results and decides the next action.

```
Agent: whisper-pipeline
Purpose: Run stage-by-stage transcription pipeline
Input: Audio file + shotlist CSV
Output: SRT subtitles + JSON metadata
Trigger: @whisper-pipeline
Skills: whisper-pipeline
```

---

## Pipeline Flow

```
User Request ("transcribe this video", "generate SRT")
    │
    ▼
@orch (default)
    │
    ├── Stage 1: Ingest — resolve audio + load shotlist
    ├── Stage 2: Transcribe — faster-whisper word timestamps
    ├── Stage 3: Align — map words to scenes, split into chunks
    └── Stage 4: Render — write SRT + JSON
```

---

## Agent Dispatch Table

| User says | Route to |
|---|---|
| "transcribe [file]" / "generate SRT" | Full pipeline: ingest → transcribe → align → render |
| "run [stage]" / "just the transcribe step" | @whisper-pipeline (direct stage control) |
| "show config" / "check settings" | Read `scripts/config.py` |
| "batch transcribe" | Loop pipeline over files in `input/` |

---

## Skill Index

| Skill | Location | Use |
|-------|----------|-----|
| whisper-pipeline | `.opencode/skills/whisper-pipeline/` | Pipeline orchestration, stage-by-stage execution |

*Add project-specific skills under `.opencode/skills/` as needed.*
