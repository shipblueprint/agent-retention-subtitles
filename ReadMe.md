# WhisperX SRT Generator

Automatic transcription and shot detection using **WhisperX** for precise phoneme-aligned timestamps.

## Quick Start

### 1. Install (One-time)
```batch
install_whisperx.bat
```

This creates a new conda environment `whisperx` with:
- Python 3.10
- PyTorch 2.2.0 with CUDA 12.1
- WhisperX (latest from GitHub)

### 2. Run
```batch
run_transcribe_srt.bat
```

### 3. Get Outputs
All files in `output/subtitles/`:
- `edit.srt` - Subtitles with shot text
- `{audio}_timing.json` - Timing data
- `{audio}_timing.jsx` - Premiere Pro script
- `{audio}_shot_debug.txt` - Debug info

---

## Requirements

| Component | Requirement |
|-----------|-------------|
| **GPU** | NVIDIA with CUDA support |
| **VRAM** | 6GB+ recommended (int8 mode uses ~1GB) |
| **Driver** | NVIDIA driver 525+ |
| **Conda** | Already installed at `D:\AI\AI_Toolkit\Conda\conda\` |

---

## Configuration

Edit `scripts/config.py` to customize:

### Model Selection
```python
WHISPER_MODEL = "large-v3-turbo"  # FASTEST (recommended)
COMPUTE_TYPE = "int8"             # ~1GB VRAM
BATCH_SIZE = 4
```

| Model | Size | VRAM (int8) | Speed |
|-------|------|-------------|-------|
| `large-v3-turbo` | ~1.5GB | ~1GB | FASTEST |
| `large-v3` | ~3GB | ~3GB | Most accurate |
| `medium` | ~1.5GB | ~1GB | Balanced |
| `small` | ~500MB | ~500MB | Fast |

### Shot Duration
```python
# Quick presets:
# "Snappy/Fast": Hook 3.0s, Main 6.0s, CTA 3.5s
# "Balanced":     Hook 3.5s, Main 7.0s, CTA 4.0s  ← DEFAULT
# "Relaxed":      Hook 4.5s, Main 8.0s, CTA 5.0s

HOOK_MAX_DURATION = 3.5   # Fast cuts for intro
MAIN_MAX_DURATION = 7.5   # Breathing room for content
CTA_MAX_DURATION = 4.0    # Energetic exit
```

### Section Detection
```python
# Phrases that mark section boundaries
HOOK_END_PHRASES = ["let's dive in", "let's get started", ...]
MAIN_END_PHRASES = ["thanks for watching", "i'll see you then", ...]
```

---

## How It Works

```
Audio Input
    │
    ▼
┌─────────────────┐
│  WhisperX       │  ← Transcribes + aligns to phonemes
│  (CUDA GPU)     │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  Section        │  ← Finds Hook/Main/CTA boundaries
│  Detection      │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  Audio Gap      │  ← Detects silence between words
│  Detection      │     for natural cut points
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  Generate       │  ← SRT, JSON, JSX, Debug
│  Outputs        │
└─────────────────┘
```

---

## Audio Gap Detection

The script detects **actual silence** between words:

```
Word timestamps from WhisperX:
  "However" ends at 1.450s
  "we" starts at 1.900s
  
  Gap = 450ms silence
  
  If gap >= 280ms → Cut here!
```

### Tuning
```python
SILENCE_THRESHOLD = 0.28    # 280ms = pro retention editing
USE_GAP_AT_85_PERCENT = True  # Cut early if gap found
```

| Threshold | Feel |
|-----------|------|
| 0.25s | Very snappy |
| 0.28s | Pro retention (default) |
| 0.30s | Natural |
| 0.35s+ | Documentary |

---

## Troubleshooting

### "CUDA out of memory"
```python
BATCH_SIZE = 2          # Lower batch
COMPUTE_TYPE = "int8"   # Use int8 mode
```

### "No module named 'whisperx'"
Run `install_whisperx.bat` again.

### "NVIDIA GPU not detected"
- Install latest NVIDIA drivers
- Verify with `nvidia-smi` in command prompt

### Section detection not working
- Check trigger phrases match your speech
- Use fallback word indices in config

---

## File Structure

```
Whisper-Tools/
├── input/                    # Place audio/video here
├── models/                   # Whisper models (optional local)
├── output/subtitles/         # Generated files
├── scripts/
│   ├── config.py            # All settings
│   ├── transcribe_srt.py    # Main script
│   └── ReadMe.md            # This file
├── install_whisperx.bat     # Install (one-time)
└── run_transcribe_srt.bat   # Run transcription
```

---

## Technical Details

### WhisperX vs Whisper
- **WhisperX** = Whisper + phoneme alignment
- Word timestamps accurate to milliseconds
- Uses faster-whisper backend
- Batch processing for speed

### CUDA Compatibility
- PyTorch 2.2.0 with CUDA 12.1
- Falls back to CUDA 11.8 if needed
- Works with NVIDIA driver 525+

### VRAM Usage
| Mode | VRAM | Speed |
|------|------|-------|
| int8 | ~1GB | Good |
| float16 | ~3GB | Faster |
