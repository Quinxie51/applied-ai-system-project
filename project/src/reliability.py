import csv
import os
from typing import Dict, List

from .embedder import anthropic_request, parse_vibe
from .recommender import recommend_songs


def _load_songs() -> List[Dict[str, str]]:
    """Load songs from the CSV located in the project data folder.

    Returns a list of dicts with string values.
    """
    base = os.path.dirname(__file__)
    csv_path = os.path.normpath(os.path.join(base, "..", "data", "songs.csv"))
    songs: List[Dict[str, str]] = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                # Normalize keys/values as strings
                songs.append({k: v for k, v in row.items()})
    except Exception:
        return []
    return songs


def reliability_check(original_query: str, top3: List[Dict[str, object]]) -> Dict[str, object]:
    """Check recommendation stability by paraphrasing the query and comparing results.

    Steps:
      1. Rephrase the original query using the Anthropic API (return only text).
      2. Parse the paraphrase into structured prefs and run recommend_songs.
      3. Compare the two top-3 lists and return stability info.
    """
    # 1) Paraphrase
    paraphrase_prompt = (
        "Rephrase this music vibe description in different words, keep the same meaning, "
        "return only the rephrased text.\n\nText: " + original_query
    )
    try:
        paraphrased_text = anthropic_request(paraphrase_prompt)
        # The API may return extra whitespace; take the first non-empty line
        paraphrased = paraphrased_text.strip().splitlines()[0].strip()
    except Exception:
        paraphrased = original_query

    # 2) Run recommend_songs on paraphrased
    prefs = parse_vibe(paraphrased)
    songs = _load_songs()
    new_top3 = recommend_songs(prefs, songs)

    # 3) Compare titles
    orig_titles = [str(item.get("title")) for item in top3]
    new_titles = [str(item.get("title")) for item in new_top3]

    overlap = len(set(orig_titles).intersection(set(new_titles)))
    stable = orig_titles == new_titles

    if overlap == 3 and stable:
        note = "3/3 songs consistent — result is stable"
    elif overlap == 3:
        note = "3/3 songs overlap but order differs — mostly stable"
    elif overlap >= 1:
        note = f"{overlap}/3 songs consistent — result is mostly stable"
    else:
        note = "0/3 songs consistent — result is unstable"

    return {"stable": stable, "overlap": overlap, "note": note}
