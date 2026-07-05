"""
Stage: ingest
- Resolves audio path (toolstack-pipeline full.wav OR input/ folder)
- Loads shotlist CSV (scene boundaries from toolstack-pipeline S4)
- Computes cumulative scene start/end times
- Writes audio_path, shotlist_path, scenes to state

OpenCode inspects: which audio + shotlist were resolved, scene count, total duration
"""
import os
import csv
import glob


def run(state: dict, args):
    import config as cfg
    from run_stage import save_state, ok, fail

    audio_path = _resolve_audio(args, cfg)
    if not os.path.exists(audio_path):
        fail(f"Audio not found: {audio_path}")

    shotlist_path = _resolve_shotlist(args, cfg, audio_path)
    if not shotlist_path or not os.path.exists(shotlist_path):
        fail(f"Shotlist not found: {shotlist_path}")

    try:
        scenes = _load_shotlist_csv(shotlist_path)
    except Exception as e:
        fail(f"Failed to parse shotlist CSV: {e}")

    if not scenes:
        fail("Shotlist has no scenes (parsed 0 rows)")

    # Compute cumulative scene start/end times
    cursor = 0.0
    for sc in scenes:
        sc["start"] = cursor
        sc["end"] = cursor + sc["duration"]
        cursor = sc["end"]

    state["audio_path"] = audio_path
    state["shotlist_path"] = shotlist_path
    state["scenes"] = scenes
    save_state(state)

    total_dur = sum(s["duration"] for s in scenes)
    scene_types = {}
    for s in scenes:
        t = s["scene_type"] or "(none)"
        scene_types[t] = scene_types.get(t, 0) + 1

    ok({
        "audio": os.path.basename(audio_path),
        "audio_path": audio_path,
        "media_format": os.path.splitext(audio_path)[1],
        "shotlist": os.path.basename(shotlist_path),
        "shotlist_path": shotlist_path,
        "scene_count": len(scenes),
        "total_duration": round(total_dur, 2),
        "scene_types": scene_types,
        "duration_range": {
            "min": round(min(s["duration"] for s in scenes), 2),
            "max": round(max(s["duration"] for s in scenes), 2),
        },
    }, f"{len(scenes)} scenes ({total_dur:.1f}s) from {os.path.basename(shotlist_path)}")


def _resolve_audio(args, cfg):
    """Resolve audio path: --audio flag > toolstack-pipeline full.wav > input/."""
    if getattr(args, "audio", None):
        return os.path.abspath(args.audio)
    if os.path.exists(cfg.DEFAULT_AUDIO_PATH):
        return cfg.DEFAULT_AUDIO_PATH
    # Fallback: first media file in input/
    for ext in ("*.wav", "*.mp3", "*.m4a", "*.flac", "*.mp4", "*.mov", "*.mkv"):
        files = glob.glob(os.path.join(cfg.INPUT_DIR, ext))
        if files:
            return files[0]
    return cfg.DEFAULT_AUDIO_PATH  # let it fail with a clear message


def _resolve_shotlist(args, cfg, audio_path):
    """Resolve shotlist CSV: --shotlist flag > toolstack-pipeline > input/."""
    if getattr(args, "shotlist", None):
        return os.path.abspath(args.shotlist)
    if os.path.exists(cfg.SHOTLIST_PATH):
        return cfg.SHOTLIST_PATH
    # Fallback: shotlist.csv next to audio, or in input/
    base = os.path.splitext(audio_path)[0]
    candidates = [
        f"{base}.csv",
        os.path.join(os.path.dirname(audio_path), "shotlist.csv"),
        os.path.join(cfg.INPUT_DIR, "shotlist.csv"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return cfg.SHOTLIST_PATH  # let it fail with a clear message


def _load_shotlist_csv(path):
    """Parse the toolstack-pipeline shotlist.csv into a list of scene dicts."""
    scenes = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dur = _parse_duration(row.get("Duration"))
            if dur is None or dur <= 0:
                continue
            scenes.append({
                "scene_num": _parse_int(row.get("#")) or len(scenes) + 1,
                "duration": float(dur),
                "scene_type": (row.get("Scene Type") or "").strip(),
                "script": (row.get("Script / VO") or "").strip(),
                "screen_action": (row.get("Screen Action") or "").strip(),
                "zoom_target": (row.get("Zoom Target") or "").strip(),
                "zoom_level": (row.get("Zoom Level") or "").strip(),
                "cs4_asset": (row.get("CS4 Asset") or "").strip(),
                "on_screen_text": (row.get("On-Screen Text") or "").strip(),
                "transition": (row.get("Transition") or "").strip(),
                "pattern_interrupt": (row.get("Pattern Interrupt") or "").strip(),
            })
    return scenes


def _parse_int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _parse_duration(v):
    """Parse '0:10' or '10' or '10.5' into float seconds."""
    if v is None:
        return None
    s = str(v).strip().replace(",", ".")
    if not s:
        return None
    parts = s.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError:
        return None
    return None
