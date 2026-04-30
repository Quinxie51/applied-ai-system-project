# VibeMatch System Architecture Diagram

```mermaid
graph LR
    A["👤 User Input<br/>Natural Language Vibe<br/>e.g. 'sad rainy day music'"] -->|Query| B["🤖 RAG Extraction<br/>embedder.py<br/>parse_vibe()"]
    
    B -->|Confidence Score| C["📊 Confidence Check<br/>(0.0-1.0)<br/>All fields populated?"]
    C -->|Extracted Prefs| D["🎵 Scoring Engine<br/>recommender.py<br/>score_song()"]
    
    E["💾 Song Database<br/>data/songs.csv<br/>20 songs"]
    E -->|Genre, Mood, Energy,<br/>Tempo, Era| D
    
    D -->|Top 3 Scored Songs<br/>+ Reasons| F["✅ Results<br/>Ready for Check"]
    
    F -->|Original Query +<br/>Top 3| G["🔄 Reliability Check<br/>reliability.py<br/>Paraphrase Query"]
    
    G -->|Paraphrased Query| B
    B -->|Re-extract| H["🎵 Re-score<br/>Top 3 Again"]
    
    H -->|Compare Overlap| I["📈 Stability Assessment<br/>2+ songs match?<br/>stable = true/false"]
    
    I -->|Final Results<br/>+ Confidence<br/>+ Stability| J["📋 Output to User<br/>Ranked recommendations<br/>with explanations"]
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#fce4ec
    style F fill:#e0f2f1
    style G fill:#fff3e0
    style H fill:#e8f5e9
    style I fill:#f3e5f5
    style J fill:#c8e6c9
```

## Data Flow Explanation

1. **User Input (Blue)** — Natural language query describing musical vibe
2. **RAG Extraction (Orange)** — Claude LLM extracts structured attributes (genre, mood, energy, tempo_bpm, era) from free-text query
3. **Confidence Check (Purple)** — Measures what fraction of attributes were successfully extracted (0.0-1.0)
4. **Scoring Engine (Green)** — Original Project 3 weighted scorer matches extracted attributes against song database
5. **Song Database (Pink)** — 20-row CSV with titles, artists, and metadata
6. **Results Ready (Teal)** — Top 3 songs with explanations of why they matched
7. **Reliability Check (Orange)** — Paraphrases original query and reruns the full pipeline
8. **Re-score (Green)** — Extracts attributes from paraphrase and scores again
9. **Stability Assessment (Purple)** — Compares two top-3 lists; if 2+ songs overlap, result is marked stable=true
10. **Final Output (Green)** — User receives recommendations with confidence and stability scores

## Key Design Decisions

- **Modular Layers**: Each component (extraction, scoring, reliability check) is independent and testable
- **Confidence as Quality Signal**: Guides downstream decisions (show results vs. ask for clarification)
- **Paraphrase-Based Reliability**: Tests consistency without needing ground truth labels or human evaluation
- **Explainability**: Every recommendation includes per-attribute scoring reasons (why this song matched)
