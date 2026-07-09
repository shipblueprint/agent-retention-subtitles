#!/usr/bin/env bash
# Whisper-Tools v2.0 — Pipeline runner (Linux)
# Stages: ingest > transcribe > align > render
set -euo pipefail

cd "$(dirname "$0")"

echo "============================================================"
echo " Whisper-Tools v2.0 - Pipeline runner"
echo " Stages: ingest > transcribe > align > render"
echo "============================================================"
echo ""

echo "Verifying environment..."
uv run --frozen python -c "
import torch
if torch.cuda.is_available():
    print(f'  GPU: {torch.cuda.get_device_name(0)}')
else:
    print('  GPU: NOT AVAILABLE (CPU fallback)')
" 2>/dev/null || {
  echo "[ERROR] Environment not ready. Run install.sh first."
  exit 1
}
echo ""

echo "--- Stage 1: ingest ---"
uv run --frozen python scripts/run_stage.py ingest
echo ""

echo "--- Stage 2: transcribe ---"
uv run --frozen python scripts/run_stage.py transcribe
echo ""

echo "--- Stage 3: align ---"
uv run --frozen python scripts/run_stage.py align
echo ""

echo "--- Stage 4: render ---"
uv run --frozen python scripts/run_stage.py render
echo ""

echo "============================================================"
echo "  Pipeline complete. See output/subtitles/"
echo "============================================================"
