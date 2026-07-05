"""
Stage: render
- Writes edit.srt and {name}_chunks.json to output/subtitles/
- Prints scene + chunk statistics for OpenCode

OpenCode inspects: file paths, total chunks, duration stats
"""
import os
import json


def run(state: dict, args):
    import config as cfg
    from run_stage import save_state, ok, fail

    chunks = state.get("chunks") or []
    if not chunks:
        fail("No chunks in state — run align first")

    audio_path = state.get("audio_path", "")
    scenes = state.get("scenes", [])

    subtitles_dir = os.path.join(cfg.OUTPUT_DIR, "subtitles")
    os.makedirs(subtitles_dir, exist_ok=True)

    # Write SRT (skip empty chunks — no subtitle to show)
    srt_path = os.path.join(subtitles_dir, "edit.srt")
    _write_srt(chunks, srt_path)

    # Write JSON (includes scenes + chunks for downstream tools)
    base = os.path.splitext(os.path.basename(audio_path))[0] or "audio"
    json_path = os.path.join(subtitles_dir, f"{base}_chunks.json")
    _write_json(chunks, scenes, audio_path, json_path)

    stats = _collect_stats(chunks, scenes)
    save_state(state)

    ok({
        "srt": srt_path,
        "json": json_path,
        "stats": stats,
    }, f"{stats['total']} chunks → {srt_path}")


def _write_srt(chunks, path):
    """Write SRT file. Empty chunks are skipped (no subtitle to display)."""
    with open(path, "w", encoding="utf-8") as f:
        idx = 0
        for c in chunks:
            text = (c.get("text") or "").strip()
            if not text:
                continue
            idx += 1
            start = max(0.0, c["start"])
            end = max(start + 0.001, c["end"])
            f.write(f"{idx}\n")
            f.write(f"{_ts(start)} --> {_ts(end)}\n")
            f.write(f"{text}\n\n")


def _ts(t):
    """Format seconds as HH:MM:SS,mmm (SRT timestamp)."""
    if t < 0:
        t = 0.0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write_json(chunks, scenes, audio_path, path):
    data = {
        "audio_file": audio_path,
        "scene_count": len(scenes),
        "chunk_count": len(chunks),
        "scenes": [{
            "scene_num": s["scene_num"],
            "scene_type": s["scene_type"],
            "start": s["start"],
            "end": s["end"],
            "duration": s["duration"],
            "script": s.get("script", ""),
        } for s in scenes],
        "chunks": [{
            "text": c.get("text", ""),
            "start": c["start"],
            "end": c["end"],
            "scene_num": c.get("scene_num"),
            "scene_type": c.get("scene_type", ""),
            "empty": c.get("empty", False),
        } for c in chunks],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _collect_stats(chunks, scenes):
    non_empty = [c for c in chunks if not c.get("empty") and (c.get("text") or "").strip()]
    if not non_empty:
        return {"total": 0, "scenes": len(scenes), "empty_scenes": len(scenes)}

    durs = [c["end"] - c["start"] for c in non_empty]
    empty_scene_count = sum(1 for s in scenes if not s.get("words"))

    return {
        "total": len(non_empty),
        "scenes": len(scenes),
        "empty_scenes": empty_scene_count,
        "min_duration": round(min(durs), 2),
        "max_duration": round(max(durs), 2),
        "avg_duration": round(sum(durs) / len(durs), 2),
    }
