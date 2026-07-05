"""
Whisper-Tools v2.0 — Shotlist-aligned subtitle generator.

Configuration is intentionally minimal. The old HOOK/MAIN/CTA + acoustic + LLM
gating machinery is gone; we now align transcripts to scenes from the
toolstack-pipeline shotlist.csv and split long scenes into readable chunks.
"""
import os

# === PATHS ====================================================================
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)  # Whisper-Tools root

# Sibling toolstack-pipeline project (where shotlist.csv and full.wav live)
_TOOLSTACK_PIPELINE_DIR = os.path.normpath(
    os.path.join(_PROJECT_DIR, "..", "toolstack-pipeline")
)

# Default shotlist CSV (from toolstack-pipeline S4)
SHOTLIST_PATH = os.path.join(_TOOLSTACK_PIPELINE_DIR, "out", "shotlist.csv")

# Default audio: toolstack-pipeline's full.wav (long-form) or shortform.wav (short-form)
DEFAULT_AUDIO_PATH = os.path.join(_TOOLSTACK_PIPELINE_DIR, "out", "audio", "full.wav")

# Input folder for ad-hoc testing (single audio + optional shotlist.csv)
INPUT_DIR = os.path.join(_PROJECT_DIR, "input")

# Output
OUTPUT_DIR = os.path.join(_PROJECT_DIR, "output")

# === WHISPER ==================================================================
WHISPER_MODEL = "large-v3-turbo"  # faster-whisper model id
COMPUTE_TYPE = "int8"             # int8 = ~1GB VRAM, float16 = ~3GB VRAM
DEVICE = "cuda"                   # "cuda" or "cpu" (auto-falls-back to cpu on failure)
LANGUAGE = None                   # None = auto-detect, or "en" / "es" / etc.

# === SUBTITLE CHUNKING ========================================================
# Scenes from the shotlist can be 5-25 seconds. We split each scene's transcript
# into readable subtitle chunks. Goals: 1-7s per chunk, ~80 chars wide, prefer
# natural break points (sentence end > clause > silence > bridge word).
MIN_CHUNK_DURATION = 1.0          # Don't create chunks shorter than this (seconds)
MAX_CHUNK_DURATION = 7.0          # Split chunks longer than this (seconds)
MAX_CHUNK_CHARS = 84              # Soft limit for subtitle text width
MAX_OVERFLOW = 0.5                # Allow N seconds past MAX to finish a sentence

# Cut-preference scoring (higher = better cut point)
CUT_SCORE_SENTENCE_END = 100      # . ? !
CUT_SCORE_CLAUSE_END = 60         # , ; — :
CUT_SCORE_SILENCE = 30            # Word gap >= SILENCE_GAP_THRESHOLD
CUT_SCORE_BRIDGE_WORD = 20        # Next word is a bridge (so/but/and/...)
CUT_PROXIMITY_BONUS = 50          # Decays with distance from target end time

SILENCE_GAP_THRESHOLD = 0.35      # Word gap (seconds) considered a breath pause
BRIDGE_WORDS = {
    "but", "so", "and", "however", "therefore", "meanwhile",
    "moreover", "furthermore", "additionally", "because", "then",
    "now", "next", "finally", "plus", "yet", "or", "nor",
}

# === STATE ====================================================================
STATE_PATH = os.path.join(_SCRIPT_DIR, "state.json")
