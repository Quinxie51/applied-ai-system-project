import os
import json
from typing import Dict, Optional

try:
    import anthropic
except Exception:
    anthropic = None


def _validate_and_normalize(parsed: Dict[str, Optional[object]]) -> Dict[str, Optional[object]]:
    """Validate parsed JSON against required schema and normalize invalid values to None."""
    valid = {"genre": None, "mood": None, "energy": None, "tempo_bpm": None, "era": None}

    genres = {"pop", "rock", "indie", "hiphop", "edm", "jazz", "rnb"}
    moods = {"happy", "sad", "angry", "chill", "romantic", "melancholic"}
    eras = {"80s", "90s", "2000s", "2010s", "2020s"}

    for k in valid.keys():
        v = parsed.get(k)
        if v is None:
            valid[k] = None
            continue

        # Strings: normalize
        if k in ("genre", "mood", "era"):
            try:
                s = str(v).strip()
            except Exception:
                valid[k] = None
                continue
            if k == "genre" and s.lower() in genres:
                valid[k] = s.lower()
            elif k == "mood" and s.lower() in moods:
                valid[k] = s.lower()
            elif k == "era" and s.lower() in eras:
                valid[k] = s.lower()
            else:
                valid[k] = None
        elif k == "energy":
            try:
                f = float(v)
                if 0.0 <= f <= 1.0:
                    valid[k] = f
                else:
                    valid[k] = None
            except Exception:
                valid[k] = None
        elif k == "tempo_bpm":
            try:
                t = int(v)
                if 60 <= t <= 180:
                    valid[k] = t
                else:
                    valid[k] = None
            except Exception:
                valid[k] = None

    return valid


def parse_vibe(query: str) -> Dict[str, Optional[object]]:
    """Parse a free-text vibe description into structured music attributes.

    Calls the Anthropic API (model: claude-sonnet-4-20250514) with a system
    prompt requesting a JSON object with keys: genre, mood, energy, tempo_bpm, era.

    If the API call fails or returned values are out of range/schema, values
    are set to None. API key is read from environment variable
    ANTHROPIC_API_KEY.
    """
    system_prompt = (
        "You are a music attribute extractor. Given a free-text vibe description,\n"
        "return ONLY a valid JSON object with exactly these keys:\n"
        "genre, mood, energy, tempo_bpm, era.\n\n"
        "Rules:\n"
        "- genre: one of pop, rock, indie, hiphop, edm, jazz, rnb — or null\n"
        "- mood: one of happy, sad, angry, chill, romantic, melancholic — or null\n"
        "- energy: a float between 0.0 and 1.0 representing intensity — or null\n"
        "  (0.0 = very calm, 1.0 = very intense)\n"
        "- tempo_bpm: an integer between 60 and 180 representing beats per minute — or null\n"
        "  (60 = very slow, 180 = very fast)\n"
        "- era: one of 80s, 90s, 2000s, 2010s, 2020s — or null\n\n"
        "Return ONLY the JSON object. No explanation, no markdown, no extra text."
    )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment")
        return {"genre": None, "mood": None, "energy": None, "tempo_bpm": None, "era": None}

    try:
        if anthropic is None:
            raise RuntimeError("anthropic SDK not installed")

        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": query}]
        )

        # Extract text from response
        text = ""
        if hasattr(resp, "content") and len(resp.content) > 0:
            text = resp.content[0].text if hasattr(resp.content[0], "text") else str(resp.content[0])
        else:
            text = str(resp)

        # Try to parse JSON directly from the returned text
        parsed = None
        try:
            # Find first { .. } block
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_text = text[start:end+1]
                parsed = json.loads(json_text)
        except Exception:
            parsed = None

        if not isinstance(parsed, dict):
            # Could not parse; return all-null
            return {"genre": None, "mood": None, "energy": None, "tempo_bpm": None, "era": None}

        validated = _validate_and_normalize(parsed)
        return validated

    except Exception as e:
        print(f"parse_vibe API error: {e}")
        return {"genre": None, "mood": None, "energy": None, "tempo_bpm": None, "era": None}
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
