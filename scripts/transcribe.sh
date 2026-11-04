#!/usr/bin/env bash
# Unified transcription entry point for the pipeline.
#
# The pipeline calls this script and nothing else. Engine location, virtualenv,
# device, and faster-whisper settings stay behind this boundary.
#
# Engine: faster-whisper, installed at STT_HOME (default scripts/stt-transcribe).
#
# Usage:
#   scripts/transcribe.sh ingest
#   scripts/transcribe.sh transcribe
#   scripts/transcribe.sh align
#   scripts/transcribe.sh render
#   scripts/transcribe.sh   # defaults to full pipeline? see run_stage.py

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

STT_HOME="${STT_HOME:-scripts/stt-transcribe}"

if [[ ! -d "$STT_HOME" ]]; then
  echo "STT engine not found: $STT_HOME" >&2
  echo "Link your faster-whisper install, for example:" >&2
  echo "  ln -s /path/to/stt-transcribe scripts/stt-transcribe" >&2
  echo "or set STT_HOME=/path/to/stt-transcribe" >&2
  exit 1
fi

PYTHON="$STT_HOME/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "No virtualenv python at: $PYTHON" >&2
  echo "Install the engine first (see README, Setup)." >&2
  exit 1
fi

# Clear stale proxy vars — httpx/huggingface_hub can't parse SOCKS proxies
# and will fail even when models are already cached locally.
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy

# Reuse the engine's environment (CUDA libs, HF cache, offline mode).
if [[ -f "$STT_HOME/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$STT_HOME/.env"
  set +a
fi

exec "$PYTHON" scripts/run_stage.py "$@"
EOF
chmod +x scripts/transcribe.sh
echo done