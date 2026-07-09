# Orchestrator — Whisper-Tools

Route transcription requests through the 4-stage pipeline:
1. Ingest — resolve audio + shotlist
2. Transcribe — faster-whisper
3. Align — word-to-scene alignment + chunking
4. Render — SRT + JSON output

Or dispatch @whisper-pipeline for direct stage control.
