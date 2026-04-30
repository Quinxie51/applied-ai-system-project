import os
import json
import re
from typing import Dict, Optional

try:
    # Typical modern anthropic SDK
    from anthropic import Client as AnthropicClient
except Exception:
    AnthropicClient = None


def _extract_json(text: str) -> Dict[str, Optional[str]]:
    """Extract the first JSON object found in text and return it as a dict.

    If extraction or parsing fails, returns an empty dict.
    """
    if not text:
        return {}
    # Find the first {...} block
    m = re.search(r"\{.*\}", text, re.DOTALL)
    candidate = m.group(0) if m else text.strip()
    try:
        data = json.loads(candidate)
        # Normalize explicit null -> None
        return {k: (v if v is not None else None) for k, v in data.items()}
    except Exception:
        return {}


def anthropic_request(prompt: str, model: str = "claude-sonnet-4-20250514", max_tokens: int = 300) -> str:
    """Send a completion request to the Anthropic API and return the raw text.

    This helper tries common SDK invocation patterns and raises exceptions on failure.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found in environment")

    # Try modern SDK pattern
    if AnthropicClient is not None:
        try:
            client = AnthropicClient(api_key=api_key)
            resp = client.create_completion(model=model, prompt=prompt, max_tokens_to_sample=max_tokens)
            # resp may be a dict-like or object with .completion
            text = getattr(resp, "completion", None) or (resp.get("completion") if isinstance(resp, dict) else None)
            if not text:
                text = str(resp)
            return text
        except Exception:
            # Fall through to try the generic import
            pass

    # Try legacy import style
    try:
        import anthropic
        client = anthropic.Client(api_key=api_key)
        resp = client.completions.create(model=model, prompt=prompt, max_tokens_to_sample=max_tokens)
        if isinstance(resp, dict):
            return resp.get("completion") or resp.get("text") or str(resp)
        return str(resp)
    except Exception as e:
        raise RuntimeError(f"Anthropic API request failed: {e}")


def parse_vibe(query: str) -> Dict[str, Optional[str]]:
    """Parse a free-text vibe description into structured music attributes.

    Calls the Anthropic API with a system prompt that requests a JSON object
    containing: genre, mood, energy, tempo, era. Each value will be one of
    the allowed options or null.

    Returns a dict with keys mapped to string values or None.
    """
    system_prompt = (
        "You are a music attribute extractor. Given a vibe description, \n"
        "return ONLY a JSON object with keys: genre, mood, energy, tempo, era.\n"
        "Each value must be one of the valid options or null if not implied.\n"
        "Valid options:\n"
        "  genre: pop, rock, indie, hiphop, edm, jazz, rnb, null\n"
        "  mood: happy, sad, angry, chill, romantic, melancholic, null\n"
        "  energy: low, medium, high, null\n"
        "  tempo: slow, mid, fast, null\n"
        "  era: 80s, 90s, 2000s, 2010s, 2020s, null\n"
    )

    prompt = f"{system_prompt}\nVibe: {query}\n\nReturn just the JSON object."
    try:
        raw = anthropic_request(prompt)
    except Exception as e:
        # Return all-null preferences on API failure
        return {"genre": None, "mood": None, "energy": None, "tempo": None, "era": None}

    parsed = _extract_json(raw)
    # Ensure all keys present, normalize 'null' to None
    keys = ["genre", "mood", "energy", "tempo", "era"]
    out: Dict[str, Optional[str]] = {}
    for k in keys:
        v = parsed.get(k)
        if isinstance(v, str) and v.lower() == "null":
            out[k] = None
        else:
            out[k] = v if v is not None else None
    return out
