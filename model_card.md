# VibeMatch — Model Card

## Dataset description

- File: `data/songs.csv`
- Rows: 20 songs
- Columns: `title`, `artist`, `genre`, `mood`, `energy`, `tempo`, `era`
- The CSV was handcrafted for this demo to include a diverse mix across
  genres (pop, rock, indie, hiphop, edm, jazz, rnb), moods (happy, sad,
  angry, chill, romantic, melancholic), energy levels (low, medium, high),
  tempos (slow, mid, fast) and eras (80s, 90s, 2000s, 2010s, 2020s).

## How the recommender works

VibeMatch converts a user's free-text "vibe" into structured music
attributes (genre, mood, energy, tempo, era) using a small LLM step.
Each song in the dataset has those same attributes. The system scores
songs by matching attributes and returns the top-3 results.

Scoring weights:
- genre: 25
- mood: 25
- energy: 20
- tempo: 15
- era: 15

Songs that match more of the user's extracted attributes receive higher
scores and are ranked accordingly.

## How RAG is used

This project uses a Retrieval-Augmented Generation (RAG) pattern where
the "retrieval" step is implemented by `parse_vibe` — an LLM call that
extracts structured attributes from a free-text vibe. That structured
output is then used to retrieve and score songs from a local dataset.
The LLM is not asked to directly generate song recommendations; it only
provides the structured query (the retrieval artifact) for deterministic
scoring.

## Limitations and biases

- Very small dataset (20 songs): results are brittle and not representative.
- Genre and era labels are coarse and may not match user intent precisely.
- The dataset contains popular Western music and omits many cultures and
  subgenres, introducing cultural bias.
- The LLM parsing step may hallucinate or return ambiguous/null values,
  which affects recall and ranking.

## One idea for improvement

Expand the dataset and replace hard-coded attribute matching with learned
embeddings (semantic similarity) so recommendations can generalize beyond
exact label matches. Also add user feedback loops to personalize weights.
