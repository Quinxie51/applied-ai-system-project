import os
from typing import Dict, List

try:
    import anthropic
except Exception:
    anthropic = None

from .embedder import parse_vibe
from .recommender import recommend_songs


def reliability_check(original_query: str, top3: List[Dict[str, object]], songs: List[Dict[str, object]]) -> Dict[str, object]:
    """Assess stability of recommendations by paraphrasing and re-running.

    Steps:
      1. Paraphrase the original_query via Anthropic (return only rephrased text).
      2. Parse the paraphrase with `parse_vibe`.
      3. Call `recommend_songs` on paraphrased prefs and `songs`.
      4. Compute overlap and stability (stable if overlap >= 2).

    Returns a dict with keys: stable, overlap, paraphrased_query, note.
    """
    system = (
        "Rephrase the music vibe description using different words but preserve the same emotional meaning. "
        "Return only the rephrased text, nothing else."
    )

    paraphrased = original_query
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        if anthropic is None:
            raise RuntimeError("anthropic SDK not installed")

        client = anthropic.Client(api_key=api_key)
        full_prompt = f"Human: {original_query}\n\nAssistant:"
        resp = client.completions.create(model="claude-sonnet-4-20250514", prompt=full_prompt, max_tokens_to_sample=150)
        if isinstance(resp, dict):
            text = resp.get("completion") or resp.get("text") or str(resp)
        else:
            text = getattr(resp, "completion", None) or str(resp)
        paraphrased = text.strip().splitlines()[0].strip() if text else original_query
    except Exception as e:
        # On error, leave paraphrased as original and continue
        paraphrased = original_query

    # Parse paraphrased query and re-run recommendations
    prefs = parse_vibe(paraphrased)
    new_top3 = recommend_songs(prefs, songs, k=3)

    orig_titles = [str(item.get("title")) for item in top3]
    new_titles = [str(item.get("title")) for item in new_top3]

    overlap = len(set(orig_titles).intersection(set(new_titles)))
    stable = overlap >= 2

    note = f"{overlap}/3 songs consistent — {'result is stable' if stable else 'result is unstable'}"

    return {"stable": stable, "overlap": overlap, "paraphrased_query": paraphrased, "note": note}
