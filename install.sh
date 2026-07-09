#!/usr/bin/env bash
# Whisper-Tools v2.0 — uv installer (torch GPU / cu124)
set -euo pipefail

cd "$(dirname "$0")"

echo "============================================================"
echo " Whisper-Tools v2.0 - uv installer (torch GPU / cu124)"
echo "============================================================"
echo ""

# HuggingFace hub uses all_proxy which may conflict — unset if it's
# a SOCKS scheme that httpx cannot handle.
if [[ "${all_proxy:-}" == socks://* ]]; then
  echo "[info] unsetting all_proxy (SOCKS not supported by huggingface_hub)"
  unset all_proxy ALL_PROXY
fi

echo "Syncing dependencies via uv..."
uv sync
echo ""

echo "Verifying GPU torch:"
uv run python -c "
import torch
print(f'  torch={torch.__version__}')
print(f'  CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  Device: {torch.cuda.get_device_name(0)}')
else:
    print('  Device: CPU only')
"
echo ""

echo "============================================================"
echo "  Done. Run ./start-uv.sh to run the full pipeline."
echo "============================================================"
