"""
Stage: transcribe
- Runs faster-whisper on the audio file with word-level timestamps
- Writes words (text, start, end) to state

OpenCode inspects: word_count, detected language, confidence, audio duration
"""
import os


def run(state: dict, args):
    from faster_whisper import WhisperModel
    import config as cfg
    from run_stage import save_state, ok, fail

    audio_path = state.get("audio_path")
    if not audio_path or not os.path.exists(audio_path):
        fail("No audio_path in state — run ingest first")

    model_name = cfg.WHISPER_MODEL
    compute_type = cfg.COMPUTE_TYPE
    device = cfg.DEVICE
    language = getattr(args, "language", None) or cfg.LANGUAGE

    # Try GPU first, fall back to CPU on any failure (e.g., no CUDA, OOM)
    try:
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
    except Exception:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")

    segments, info = model.transcribe(audio_path, word_timestamps=True, language=language)

    words = []
    for segment in segments:
        if segment.words:
            for w in segment.words:
                text = w.word.strip()
                if text:
                    words.append({
                        "text": text,
                        "start": float(w.start),
                        "end": float(w.end),
                    })

    state["words"] = words
    save_state(state)

    duration = round(words[-1]["end"] if words else 0.0, 2)
    ok({
        "word_count": len(words),
        "language": info.language,
        "confidence": round(info.language_probability, 3),
        "duration": duration,
        "device": device,
        "model": model_name,
    }, f"{len(words)} words, language={info.language} ({info.language_probability:.2f}), {duration}s")
