@echo off
cd /d "%~dp0"
echo ============================================================
echo  Whisper-Tools v2.0 - Pipeline runner
echo  Stages: ingest ^> transcribe ^> align ^> render
echo ============================================================
echo.
echo Verifying environment...
uv run --frozen python -c "import torch; print(f'  GPU: {torch.cuda.is_available()}, {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU only\"}')"
if errorlevel 1 (
    echo.
    echo [ERROR] Environment not ready. Run install.bat first.
    pause
    exit /b 1
)
echo.
echo --- Stage 1: ingest ---
uv run --frozen python scripts/run_stage.py ingest
if errorlevel 1 goto :error
echo.
echo --- Stage 2: transcribe ---
uv run --frozen python scripts/run_stage.py transcribe
if errorlevel 1 goto :error
echo.
echo --- Stage 3: align ---
uv run --frozen python scripts/run_stage.py align
if errorlevel 1 goto :error
echo.
echo --- Stage 4: render ---
uv run --frozen python scripts/run_stage.py render
if errorlevel 1 goto :error
echo.
echo ============================================================
echo  Pipeline complete. See output\subtitles\
echo ============================================================
pause
exit /b 0

:error
echo.
echo [ERROR] Pipeline failed at the stage above.
pause
exit /b 1
