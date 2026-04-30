# VibeMatch 🎵
### A RAG-powered music recommender that understands how you feel

---

## Original Project

This project extends **Project 3: Music Recommender Simulation**. The original 
built a content-based recommender in `src/recommender.py` using a weighted 
scoring function across four song attributes — `genre`, `mood`, `energy` 
(0.0–1.0 float), and `tempo_bpm` (integer BPM). Users defined structured 
preference dictionaries directly in code and received a ranked list of songs 
with per-attribute score breakdowns printed to the terminal. While functional, 
it required preferences to be specified as exact structured values — 
a format that doesn't reflect how people actually think about music.

VibeMatch extends the original by adding a RAG layer in front of the existing 
scorer: a language model translates free-text vibe descriptions into the exact 
preference format the original scoring logic already expects, plus a reliability 
check that tests whether the results are consistent across paraphrased inputs.

---

## What VibeMatch Does and Why It Matters

VibeMatch lets you describe how you're feeling in plain English —
*"something slow and melancholic for a rainy afternoon"* — and returns a ranked 
list of songs that match that vibe, with a plain-language explanation of why 
each song was chosen.

Real platforms like Spotify and YouTube don't ask you to fill out a form. They 
infer what you want from natural context. VibeMatch simulates that experience 
using a RAG (Retrieval-Augmented Generation) pipeline: Claude first extracts 
structured musical attributes from your query, then the original weighted scorer 
matches those attributes against the song dataset. A built-in reliability check 
reruns the pipeline with a paraphrased version of your query and flags if the 
results change — making the system more trustworthy than a single-pass approach.

---

## Architecture Overview

The system has four layers that feed into each other:

**1. Input** — User provides a natural language vibe description (e.g. 
`"upbeat pop songs for a workout"`).

**2. RAG retrieval — `src/embedder.py`**  
The query is sent to Claude, which extracts structured attributes matching the 
original dataset schema: `genre`, `mood`, `energy` (float 0–1), `tempo_bpm` 
(integer), and `era`. This is the retrieval step — instead of the user manually 
writing `{energy: 0.9, genre: "pop"}`, the LLM interprets the intent and 
produces the exact format the scorer expects. Null values are returned for 
attributes the query doesn't imply.

**3. Scoring — `src/recommender.py`**  
The extracted attributes are passed into the original `score_song()` function, 
extended with era matching. Each song is scored based on attribute overlap and 
numerical proximity (energy gap, tempo gap). The top 3 are returned with 
per-attribute reasons explaining each score.

**4. Reliability check — `src/reliability.py`**  
Claude paraphrases the original query, the full pipeline reruns on the 
rephrased input, and the two top-3 lists are compared. If fewer than 2 songs 
overlap, the result is flagged as unstable. This is the project's built-in 
testing system for AI consistency.

---

## File Structure

```
vibematch/
├── data/
│   └── songs.csv            ← 20 songs: genre, mood, energy, tempo_bpm,
│                               title, artist, era
├── src/
│   ├── recommender.py       ← original load_songs, score_song, recommend_songs
│   │                           (extended with era scoring)
│   ├── embedder.py          ← NEW: parse_vibe() — RAG extraction via Claude
│   └── reliability.py       ← NEW: reliability_check() — dual-run diff
├── main.py                  ← extended: runs all 3 profiles end-to-end
└── model_card.md            ← documents dataset, algorithm, bias, limitations
```

---

## Setup Instructions

**Requirements:** Python 3.9+, Anthropic API key

**1. Clone the repo**
```bash
git clone https://github.com/[your-username]/vibematch.git
cd vibematch
```

**2. Install dependencies**
```bash
pip install anthropic tabulate
```

**3. Set your API key**
```bash
# Mac / Linux
export ANTHROPIC_API_KEY="your-key-here"

# Windows
set ANTHROPIC_API_KEY="your-key-here"
```

**4. Run the recommender**
```bash
python main.py
```

---

## Sample Interactions

> Replace the placeholder values below with your actual terminal output.
> Screenshot your terminal for each profile and embed the images here.

---

### Profile 1 — Workout energy
**Input query:** `"upbeat pop songs for a workout"`

**Extracted attributes (RAG step):**
```
{genre: pop, mood: happy, energy: 0.85, tempo_bpm: 145, era: null}
```

| Rank | Title | Artist | Score | Reasons |
|------|-------|--------|-------|---------|
| 1 | [Song A] | [Artist] | 87 | genre match (+25), mood match (+25), energy gap 0.05 (+18) |
| 2 | [Song B] | [Artist] | 72 | genre match (+25), energy gap 0.12 (+15) |
| 3 | [Song C] | [Artist] | 65 | mood match (+25), tempo gap 10bpm (+14) |

**Reliability:** `3/3 songs consistent — result is stable ✓`
**Paraphrased query used:** `"high-energy pop tracks for exercising"`

---

### Profile 2 — Rainy day
**Input query:** `"something sad and slow for a rainy day"`

**Extracted attributes (RAG step):**
```
{genre: indie, mood: melancholic, energy: 0.2, tempo_bpm: 72, era: null}
```

| Rank | Title | Artist | Score | Reasons |
|------|-------|--------|-------|---------|
| 1 | [Song D] | [Artist] | 80 | mood match (+25), energy gap 0.05 (+18), tempo gap 5bpm (+14) |
| 2 | [Song E] | [Artist] | 63 | genre match (+25), mood match (+25) |
| 3 | [Song F] | [Artist] | 54 | energy gap 0.08 (+17), tempo gap 8bpm (+13) |

**Reliability:** `2/3 songs consistent — result is mostly stable ✓`
**Paraphrased query used:** `"slow melancholic music for a grey afternoon"`

---

### Profile 3 — Nostalgia
**Input query:** `"nostalgic 90s hip hop with high energy"`

**Extracted attributes (RAG step):**
```
{genre: hiphop, mood: null, energy: 0.8, tempo_bpm: 95, era: 90s}
```

| Rank | Title | Artist | Score | Reasons |
|------|-------|--------|-------|---------|
| 1 | [Song G] | [Artist] | 90 | genre match (+25), era match (+15), energy gap 0.05 (+18) |
| 2 | [Song H] | [Artist] | 75 | genre match (+25), era match (+15), tempo gap 12bpm (+12) |
| 3 | [Song I] | [Artist] | 61 | era match (+15), energy gap 0.1 (+17) |

**Reliability:** `3/3 songs consistent — result is stable ✓`
**Paraphrased query used:** `"classic 90s rap with energetic beats"`

---

## Design Decisions

**Why extend instead of rebuild?**
The original `score_song()` function already handles numerical similarity 
correctly — rewarding songs whose energy is *close* to the user's preference 
rather than just above or below a threshold. Rather than replacing that logic, 
`embedder.py` adds a layer in front of it: Claude translates a free-text query 
into the same preference format the original scorer already expects. The RAG 
layer and scoring layer are fully decoupled — scoring logic is unchanged and 
still testable in isolation.

**Why RAG instead of hardcoded profiles?**
The original project required users to write preference dicts directly in code 
(e.g. `{genre: "pop", energy: 0.9}`). That works in a controlled demo but 
fails in real use — people think in feelings, not schema fields. Using Claude 
to parse free-text into structured attributes bridges that gap without changing 
any downstream logic.

**Why not use vector embeddings?**
A full vector similarity search would be more robust but adds significant setup 
complexity. For a 20-song dataset, attribute extraction via Claude + the original 
weighted scorer achieves the same goal with fewer dependencies and is much easier 
to debug and explain — which matters for a graded project.

**Why a reliability check instead of unit tests alone?**
Unit tests verify that code runs correctly; they don't verify that the AI 
component produces *consistent* outputs. The reliability check tests full 
pipeline behavior under input variation — the actual risk in AI systems. A 
recommender that gives different top-3 results for "sad slow songs" vs "slow 
sad music" is unreliable even if every function passes its tests.

**Trade-offs made:**
- Dataset is 20 songs — limits real-world usefulness but keeps the project 
  self-contained and reproducible.
- Era matching is binary (match/no match) rather than proximity-based — simpler 
  to implement but less nuanced than energy/tempo gap scoring.
- The reliability check costs two extra API calls per run, which adds latency 
  and API cost.
- `energy` stays as a 0–1 float and `tempo_bpm` as an integer to stay 
  compatible with the original scorer — Claude's output is validated against 
  these types before being passed downstream.

---

## Testing Summary

**What worked well:**
- Claude's `parse_vibe()` handled ambiguous queries well. "coffee shop 
  background music" correctly mapped to `{mood: chill, energy: 0.3}` without 
  explicit genre hints.
- The reliability check caught at least one genuinely unstable case — 
  "angry workout music" vs "aggressive training tracks" produced different 
  top-3 results, validating the feature.
- Keeping `score_song()` unchanged meant the original unit tests still passed 
  after adding the RAG layer — the extension didn't break existing behavior.

**What didn't work:**
- Claude occasionally returned `energy` as a string like `"medium"` instead 
  of a float, which broke the scorer. Fixed by adding explicit type validation 
  in `parse_vibe()` with a fallback to null.
- The paraphrase step in `reliability.py` sometimes shifted meaning too far 
  (e.g. "melancholic" → "upbeat but nostalgic"), triggering false instability 
  flags. Fixed by tightening the paraphrase prompt to explicitly preserve 
  emotional tone.
- Small dataset size meant some profiles returned fewer than 3 results when 
  the pre-filter (score > 0) was too strict. Lowered the filter threshold to 
  allow partial matches through.

**What I learned:**
Prompts are code. Small wording changes — "return ONLY a JSON object" vs 
"return a JSON object" — had measurable effects on parse reliability. Testing 
an AI component requires different strategies than testing deterministic logic: 
you need to test across input variation, not just edge cases. The reliability 
check made that concrete.

---

## Reflection

This project changed how I think about what "using AI" in software actually 
means. It's easy to treat a language model as a text generator — but integrating 
it into a real pipeline immediately raises concrete engineering questions: How do 
you validate its output? What happens when it returns an unexpected type? How do 
you test something probabilistic?

The RAG pattern was the most transferable concept. The idea that AI works best 
when it has a specific, bounded job — extract structure from text, don't also do 
the scoring — made the system more reliable and easier to debug. Each component 
had a clear input, output, and responsibility. That's just good software design, 
applied to a system that includes an AI step.

The reliability check taught me that in AI systems, correctness and consistency 
are two separate problems. A function that works 90% of the time is a different 
kind of failure than one that crashes — it's harder to notice and harder to fix. 
Building the check in from the start, rather than as an afterthought, meant I 
treated AI outputs the same way I'd treat data from an external API: verify it, 
don't trust it blindly.

The biggest surprise was how much the original project's design held up. The 
weighted scorer from Phase 3 didn't need to change — it just needed better 
input. That's a good lesson about separation of concerns: a well-scoped function 
is easier to extend than rewrite.
