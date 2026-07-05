"""
Stage: align
- Maps transcribed words to scenes from shotlist (by timestamp)
- Splits long scenes (5-25s) into readable subtitle chunks (1-7s, ~80 chars)
- Writes chunks to state

This stage replaces the old acoustic + segment stages. We no longer detect
shot boundaries from audio features — the shotlist already defines them. We
just need to align transcript words to scene time ranges and break long scenes
into subtitle-sized chunks at natural language break points.

OpenCode inspects: chunks per scene, empty scenes, avg chunk duration
"""


def run(state: dict, args):
    from run_stage import save_state, ok, fail

    words = state.get("words") or []
    scenes = state.get("scenes") or []

    if not words:
        fail("No words in state — run transcribe first")
    if not scenes:
        fail("No scenes in state — run ingest first")

    # 1) Assign each word to the scene it falls into (by start timestamp)
    for sc in scenes:
        sc["words"] = []
    for w in words:
        sc = _find_scene(scenes, w["start"])
        if sc is None:
            continue
        sc["words"].append(w)

    # 2) Split each scene's words into subtitle chunks
    chunks = []
    for sc in scenes:
        scene_chunks = _split_scene_into_chunks(sc)
        for c in scene_chunks:
            c["scene_num"] = sc["scene_num"]
            c["scene_type"] = sc["scene_type"]
        chunks.extend(scene_chunks)

    # 3) Stats for OpenCode inspection
    empty_scenes = [sc["scene_num"] for sc in scenes if not sc["words"]]
    chunks_per_scene = {}
    for c in chunks:
        n = c["scene_num"]
        chunks_per_scene[n] = chunks_per_scene.get(n, 0) + 1

    non_empty = [c for c in chunks if not c.get("empty") and c.get("text", "").strip()]
    avg_dur = (
        round(sum(c["end"] - c["start"] for c in non_empty) / len(non_empty), 2)
        if non_empty else 0.0
    )

    state["chunks"] = chunks
    save_state(state)

    msg = f"{len(chunks)} chunks across {len(scenes)} scenes (avg {avg_dur}s)"
    if empty_scenes:
        msg += f" — {len(empty_scenes)} empty scene(s): {empty_scenes}"

    ok({
        "total_chunks": len(chunks),
        "non_empty_chunks": len(non_empty),
        "scenes_total": len(scenes),
        "scenes_empty": empty_scenes,
        "chunks_per_scene": chunks_per_scene,
        "avg_chunk_duration": avg_dur,
    }, msg)


def _find_scene(scenes, t):
    """Find the scene whose [start, end) contains time t."""
    for sc in scenes:
        if sc["start"] <= t < sc["end"]:
            return sc
    # If t exceeds total duration, attach to last scene
    if scenes and t >= scenes[-1]["end"]:
        return scenes[-1]
    return None


def _split_scene_into_chunks(scene):
    """
    Split a scene's words into subtitle chunks.

    Strategy:
    - If scene duration <= MAX_CHUNK_DURATION: single chunk
    - Otherwise: greedy forward scan, picking the best cut point within
      [MIN_CHUNK_DURATION, MAX_CHUNK_DURATION + MAX_OVERFLOW] of chunk start
    - Cut score weights: sentence end > clause end > silence gap > bridge word
      > proximity to target end time
    - If resulting text > MAX_CHUNK_CHARS, hard-split at word boundary
    """
    import config as cfg

    words = scene["words"]
    if not words:
        # No transcript for this scene (e.g., end screen). Emit empty chunk so
        # render can preserve scene timing in JSON.
        return [{
            "text": "",
            "start": scene["start"],
            "end": scene["end"],
            "words": [],
            "empty": True,
        }]

    scene_end = scene["end"]

    if scene_end - words[0]["start"] <= cfg.MAX_CHUNK_DURATION:
        return [{
            "text": " ".join(w["text"] for w in words),
            "start": words[0]["start"],
            "end": words[-1]["end"],
            "words": words,
            "empty": False,
        }]

    chunks = []
    cur_start_idx = 0

    while cur_start_idx < len(words):
        chunk_start_time = words[cur_start_idx]["start"]
        target_end_time = chunk_start_time + cfg.MAX_CHUNK_DURATION
        min_end_time = chunk_start_time + cfg.MIN_CHUNK_DURATION
        max_end_time = chunk_start_time + cfg.MAX_CHUNK_DURATION + cfg.MAX_OVERFLOW

        best_end_idx = None
        best_score = -1.0

        for i in range(cur_start_idx, len(words)):
            w_end = words[i]["end"]
            if w_end < min_end_time:
                continue
            if w_end > max_end_time:
                break
            score = _score_cut(words, i, target_end_time)
            if score > best_score:
                best_score = score
                best_end_idx = i

        # No acceptable cut point: force-split at first word past MAX_CHUNK_DURATION
        if best_end_idx is None:
            for i in range(cur_start_idx, len(words)):
                if words[i]["end"] > chunk_start_time + cfg.MAX_CHUNK_DURATION:
                    best_end_idx = i
                    break
            if best_end_idx is None:
                best_end_idx = len(words) - 1

        chunk_words = words[cur_start_idx:best_end_idx + 1]
        text = " ".join(w["text"] for w in chunk_words)

        if len(text) > cfg.MAX_CHUNK_CHARS:
            sub_chunks = _split_by_chars(chunk_words, cfg.MAX_CHUNK_CHARS)
            chunks.extend(sub_chunks)
        else:
            chunks.append({
                "text": text,
                "start": chunk_words[0]["start"],
                "end": chunk_words[-1]["end"],
                "words": chunk_words,
                "empty": False,
            })

        cur_start_idx = best_end_idx + 1

    return chunks


def _score_cut(words, i, target_end_time):
    """Score how good a cut after word i is. Higher = better."""
    import config as cfg

    score = 0.0
    w = words[i]
    raw = w["text"]
    stripped = raw.rstrip()

    # Sentence end (. ? !)
    if stripped.endswith((".", "?", "!", "。", "？", "！")):
        score += cfg.CUT_SCORE_SENTENCE_END
    # Clause end (, ; — : )
    elif stripped.endswith((",", ";", "—", "：", ":")):
        score += cfg.CUT_SCORE_CLAUSE_END

    # Next word is a bridge word (starts a new thought)
    if i + 1 < len(words):
        next_text = words[i + 1]["text"].lower().lstrip("'\"")
        if next_text in cfg.BRIDGE_WORDS:
            score += cfg.CUT_SCORE_BRIDGE_WORD

        # Silence gap after this word
        gap = words[i + 1]["start"] - w["end"]
        if gap >= cfg.SILENCE_GAP_THRESHOLD:
            score += cfg.CUT_SCORE_SILENCE

    # Proximity to target end time (closer = better)
    distance = abs(w["end"] - target_end_time)
    score += max(0.0, cfg.CUT_PROXIMITY_BONUS - distance * 25.0)

    return score


def _split_by_chars(chunk_words, max_chars):
    """Hard-split a chunk by character count, preserving word boundaries."""
    chunks = []
    cur = []
    cur_len = 0

    for w in chunk_words:
        w_text = w["text"]
        add_len = len(w_text) + (1 if cur else 0)
        if cur and cur_len + add_len > max_chars:
            chunks.append({
                "text": " ".join(x["text"] for x in cur),
                "start": cur[0]["start"],
                "end": cur[-1]["end"],
                "words": cur,
                "empty": False,
            })
            cur = [w]
            cur_len = len(w_text)
        else:
            cur.append(w)
            cur_len += add_len

    if cur:
        chunks.append({
            "text": " ".join(x["text"] for x in cur),
            "start": cur[0]["start"],
            "end": cur[-1]["end"],
            "words": cur,
            "empty": False,
        })
    return chunks
