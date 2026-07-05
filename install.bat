@echo off
cd /d "%~dp0"
echo ============================================================
echo  Whisper-Tools v2.0 - uv installer (torch GPU / cu124)
echo ============================================================
echo.
echo Syncing dependencies via uv...
uv sync
if errorlevel 1 (
    echo.
    echo [ERROR] uv sync failed. Check uv is installed and on PATH.
    pause
    exit /b 1
)
echo.
echo Verifying GPU torch:
uv run python -c "import torch; print(f'  torch={torch.__version__}'); print(f'  CUDA available: {torch.cuda.is_available()}'); print(f'  Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU only\"}')"
echo.
echo ============================================================
echo  Done. Run start-uv.bat to run the full pipeline.
echo ============================================================
pause
