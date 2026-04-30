from typing import Dict, List, Tuple, Optional


def score_song(user_prefs: Dict[str, Optional[str]], song: Dict[str, str]) -> Tuple[int, List[str]]:
    """Score a single song against user preferences.

    Returns a tuple of (score, reasons). Score is 0-100. Reasons is a list of
    short strings describing matching attributes.
    """
    score = 0
    reasons: List[str] = []

    # Matching rules and weights
    # Matching rules and weights (preserve existing logic)
    weights = {
        "genre": 25,
        "mood": 25,
        "energy": 20,
        "tempo_bpm": 15,
        "era": 15,
    }

    for key, w in weights.items():
        pref = user_prefs.get(key)
        song_val = song.get(key)
        if pref is None:
            # Skip null preferences
            continue
        if song_val is None:
            continue

        # For tempo_bpm and energy, user_prefs may be numeric; compare appropriately
        try:
            if key == "tempo_bpm":
                # Exact match expected for this scoring (existing logic preserved)
                if int(pref) == int(song_val):
                    score += w
                    reasons.append(f"matching tempo_bpm: {song_val}")
                continue
            if key == "energy":
                # energy expected to be float; compare by equality of string-lowered values
                if float(pref) == float(song_val):
                    score += w
                    reasons.append(f"matching {key}: {song_val}")
                continue
        except Exception:
            # Fallback to string comparison below
            pass

        # Default string comparison for genre, mood, era
        if str(pref).lower() == str(song_val).lower():
            score += w
            if key == "era":
                # Add era-specific reason with explicit weight mention
                reasons.append(f"matching era: {song_val} (+15)")
            else:
                reasons.append(f"matching {key}: {song_val}")

    # Cap score at 100
    score = max(0, min(100, score))
    return int(score), reasons


def recommend_songs(user_prefs: Dict[str, Optional[str]], songs: List[Dict[str, str]], k: int = 3) -> List[Dict[str, object]]:
    """Return top 3 recommended songs for the given user preferences.

    Steps:
      1. Pre-filter: keep songs with score > 0
      2. Score all filtered songs
      3. Sort by score descending
      4. Return top 3 dicts with keys: title, artist, score, reasons
    """
    scored = []
    for song in songs:
        s, reasons = score_song(user_prefs, song)
        if s > 0:
            scored.append({"song": song, "score": s, "reasons": reasons})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:k]

    results: List[Dict[str, object]] = []
    for item in top:
        song = item["song"]
        results.append(
            {
                "title": song.get("title"),
                "artist": song.get("artist"),
                "score": item["score"],
                "reasons": item["reasons"],
            }
        )

    return results
