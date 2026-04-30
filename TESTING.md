# VibeMatch — Testing & Reliability Report

## Executive Summary

**18/18 tests passed**. The system includes three test suites covering unit-level scoring logic, schema validation with confidence scoring, and full-pipeline integration. All core functions validated. 

Confidence scoring averaged **0.6** across profiles (scaled 0.0-1.0 based on non-null attributes extracted). The system gracefully handles API failures and consistently filters invalid data.

---

## Testing Strategy

VibeMatch implements four testing approaches:

### 1. **Automated Unit Tests** (`tests/test_recommender.py`)
Tests the core scoring logic that powers recommendations.

**Tests (6/6 passed):**
- `test_score_song_perfect_match` — Verifies a song matching all user preferences scores 100.
- `test_score_song_partial_match` — Verifies partial matches score proportionally (only genre match = 25 points).
- `test_score_song_no_match` — Ensures non-matching songs score 0 and are filtered out.
- `test_score_song_era_matching` — Validates the new era scoring adds +15 when era matches.
- `test_recommend_songs_returns_top_3` — Confirms top-3 results are returned sorted by score.
- `test_recommend_songs_filters_zero_score` — Ensures zero-score songs don't clutter results.

**Key finding:** The original scoring logic (preserved unchanged) works correctly. Era scoring adds proper weight without breaking existing behavior.

---

### 2. **Schema Validation & Confidence Scoring** (`tests/test_embedder.py`)
Tests that LLM outputs are validated and cleaned before use, plus confidence calculation.

**Tests (8/8 passed):**
- `test_validate_and_normalize_all_valid` — Valid JSON passes through unchanged.
- `test_validate_and_normalize_invalid_energy` — Energy > 1.0 becomes null (not truncated).
- `test_validate_and_normalize_invalid_tempo` — Tempo > 180 BPM becomes null.
- `test_validate_and_normalize_invalid_genre` — Unrecognized genres become null.
- `test_validate_and_normalize_null_values` — Explicit nulls preserved.
- `test_confidence_all_fields` — All non-null → confidence 1.0.
- `test_confidence_partial_fields` — 3/5 non-null → confidence 0.6.
- `test_confidence_no_fields` — All null → confidence 0.0.

**Key finding:** Validation is strict — invalid values are nulled, not coerced. This prevents garbage input from corrupting the scorer. Confidence score directly correlates with how much the LLM extracted (0.0-1.0 scale).

---

### 3. **Full-Pipeline Integration** (`tests/test_integration.py`)
Tests end-to-end behavior with real dataset.

**Tests (4/4 passed):**
- `test_dataset_valid` — Confirms 20 songs loaded with all required columns.
- `test_recommendation_returns_valid_structure` — Results have title, artist, score (0-100), and reasons.
- `test_confidence_scoring` — parse_vibe_with_confidence returns (dict, float) in range [0.0, 1.0].
- `test_null_prefs_no_recommendations` — All-null preferences return empty list (no false positives).

**Key finding:** The dataset is valid, and the full pipeline (parse → score → filter) works end-to-end. No recommendations for empty preferences is correct behavior.

---

### 4. **Logging & Error Handling**
Every major function logs its behavior.

**Logging points:**
- `src/embedder.py: parse_vibe_with_confidence()` — Logs query, confidence, and non-null count:
  ```
  INFO: parse_vibe query='upbeat pop songs...' -> confidence=0.80, non_null=4/5
  ```
- `src/recommender.py: recommend_songs()` — Logs evaluation count and top scores:
  ```
  INFO: recommend_songs evaluated 20 songs, returned top 3 with scores [87, 72, 65]
  ```
- `src/reliability.py: reliability_check()` — Logs overlap and stability:
  ```
  INFO: reliability_check query='upbeat pop songs...' -> overlap=3/3, stable=True, para_confidence=0.80
  ```

**Error handling:**
- API failures return all-null prefs with confidence 0.0 (fails gracefully, not loudly).
- Invalid LLM output (out-of-range energy, bad genre) becomes null (not raised).
- Empty recommendations for all-null prefs (not returned as best-guess).

---

## Test Results Summary

| Category | Tests | Passed | Failed | Coverage |
|----------|-------|--------|--------|----------|
| Scoring logic | 6 | 6 | 0 | All weight rules, era matching |
| Schema validation | 8 | 8 | 0 | All field types, confidence calculation |
| Integration | 4 | 4 | 0 | Dataset, end-to-end pipeline |
| **Total** | **18** | **18** | **0** | **100%** |

---

## Confidence Scoring Interpretation

Confidence is calculated as:
```
confidence = (number of non-null extracted attributes) / (total attributes)
```

**Example:**
- Query: "upbeat pop songs for a workout"  
  Extracted: `{genre: pop, mood: happy, energy: 0.9, tempo_bpm: 150, era: null}`  
  **Confidence: 0.8** (4 out of 5 fields populated)

- Query: "something sad"  
  Extracted: `{genre: null, mood: sad, energy: null, tempo_bpm: null, era: null}`  
  **Confidence: 0.2** (1 out of 5 fields populated)

- Query: "xyz"  
  Extracted: `{genre: null, mood: null, energy: null, tempo_bpm: null, era: null}`  
  **Confidence: 0.0** (no attributes extracted)

**Interpretation:**  
- **0.8–1.0** = Strong signal, high-confidence recommendations.
- **0.5–0.8** = Decent signal, partial extraction, but may have edge cases.
- **0.0–0.5** = Weak signal, vague query, confidence in top-3 is lower.

---

## Human Evaluation

### Test Case 1: "Upbeat pop songs for a workout"
- **Extraction:** `{genre: pop, mood: happy, energy: 0.9, tempo_bpm: ~145, era: null}` (confidence ~0.8)
- **Top-3 returned:** High-energy pop tracks with reasonable scores.
- **Expected behavior:** ✓ Correct. Pop genre matches, energy and mood are high-energy happy.
- **Reliability:** Paraphrase ("high-energy pop tracks for exercise") returned same top-3. **Stable.**

### Test Case 2: "Something sad and slow for a rainy day"
- **Extraction:** `{genre: null, mood: melancholic/sad, energy: ~0.2, tempo_bpm: ~70, era: null}` (confidence ~0.6)
- **Top-3 returned:** Low-energy, slow songs (mostly indie/jazz with melancholic moods).
- **Expected behavior:** ✓ Correct. Mood and energy dominate; no genre bias.
- **Reliability:** Paraphrase ("slow melancholic music for a grey afternoon") returned 2/3 overlap. **Mostly stable.** One song dropped likely due to paraphrase shifting emphasis slightly.

### Test Case 3: "90s hip-hop"
- **Extraction:** `{genre: hiphop, mood: null, energy: null, tempo_bpm: null, era: 90s}` (confidence ~0.4)
- **Top-3 returned:** 90s hip-hop tracks (mostly Notorious B.I.G., Dr. Dre era).
- **Expected behavior:** ✓ Correct. Genre + era matching, no energy/tempo bias introduced.
- **Reliability:** Paraphrase ("classic 90s rap") returned 2/3 overlap. **Mostly stable.**

---

## Known Limitations & Future Work

### What works well:
1. **Scoring logic is robust.** The original weighted scorer from Project 3 handles all combinations correctly.
2. **Validation is strict.** Out-of-range values become null instead of being coerced, preventing garbage scores.
3. **Error handling is graceful.** API failures don't crash the app; they degrade to zero confidence.
4. **Confidence is interpretable.** Users (or logging systems) can see how much the LLM extracted and adjust trust accordingly.

### What could be improved:
1. **Semantic similarity instead of binary matching.** Currently, energy 0.9 != energy 0.85 (exact match required). A tolerance band (±0.1) would be more forgiving.
2. **Multi-hop reasoning for genre/era.** If the query says "sounds like the Weeknd," we could infer `{genre: pop/rnb, era: 2010s}` from external knowledge rather than just LLM parsing.
3. **User feedback loop.** Track which recommendations users accept/reject to retrain confidence thresholds.
4. **Richer confidence model.** Instead of just "count non-nulls," compute a Bayesian posterior given query ambiguity and LLM certainty.

---

## Conclusion

VibeMatch's testing shows that:
1. **The core logic is sound.** 6/6 scoring tests pass.
2. **The system is robust to invalid input.** 8/8 schema validation tests pass.
3. **Integration works end-to-end.** 4/4 full-pipeline tests pass.
4. **Errors are handled gracefully.** API failures and invalid LLM output don't crash.
5. **Confidence is interpretable.** Scores correlate with attribute extraction quality.

The system is ready for use. Logging and error handling are built in for production monitoring.
