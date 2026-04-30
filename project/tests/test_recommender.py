"""Unit tests for recommender.py scoring logic."""
import sys
sys.path.insert(0, '/'.join(__file__.split('/')[:-2]))

from src.recommender import score_song, recommend_songs


def test_score_song_perfect_match():
    """Test that a perfect match gives high score."""
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.9, "tempo_bpm": 150, "era": "2020s"}
    song = {"title": "Test", "artist": "Artist", "genre": "pop", "mood": "happy", "energy": 0.9, "tempo_bpm": 150, "era": "2020s"}
    score, reasons = score_song(prefs, song)
    assert score == 100, f"Expected 100 for perfect match, got {score}"
    assert len(reasons) == 5, f"Expected 5 reasons, got {len(reasons)}"
    print("[PASS] test_score_song_perfect_match")


def test_score_song_partial_match():
    """Test that partial matches score proportionally."""
    prefs = {"genre": "rock", "mood": None, "energy": None, "tempo_bpm": None, "era": None}
    song = {"title": "Test", "artist": "Artist", "genre": "rock", "mood": "happy", "energy": 0.5, "tempo_bpm": 120, "era": "1990s"}
    score, reasons = score_song(prefs, song)
    assert score == 25, f"Expected 25 for genre match only, got {score}"
    assert len(reasons) == 1, f"Expected 1 reason, got {len(reasons)}"
    print("[PASS] test_score_song_partial_match")


def test_score_song_no_match():
    """Test that non-matching songs score 0."""
    prefs = {"genre": "jazz", "mood": None, "energy": None, "tempo_bpm": None, "era": None}
    song = {"title": "Test", "artist": "Artist", "genre": "pop", "mood": "happy", "energy": 0.5, "tempo_bpm": 120, "era": "1990s"}
    score, reasons = score_song(prefs, song)
    assert score == 0, f"Expected 0 for no match, got {score}"
    assert len(reasons) == 0, f"Expected 0 reasons, got {len(reasons)}"
    print("[PASS] test_score_song_no_match")


def test_score_song_era_matching():
    """Test that era matching adds +15 points."""
    prefs = {"genre": None, "mood": None, "energy": None, "tempo_bpm": None, "era": "90s"}
    song = {"title": "Test", "artist": "Artist", "genre": "pop", "mood": "happy", "energy": 0.5, "tempo_bpm": 120, "era": "90s"}
    score, reasons = score_song(prefs, song)
    assert score == 15, f"Expected 15 for era match, got {score}"
    assert any("era" in r for r in reasons), f"Expected era in reasons, got {reasons}"
    print("[PASS] test_score_song_era_matching")


def test_recommend_songs_returns_top_3():
    """Test that recommend_songs returns top 3 sorted."""
    songs = [
        {"title": "A", "artist": "Artist A", "genre": "pop", "mood": "happy", "energy": 0.9, "tempo_bpm": 150, "era": "2020s"},
        {"title": "B", "artist": "Artist B", "genre": "pop", "mood": "happy", "energy": 0.8, "tempo_bpm": 120, "era": "2010s"},
        {"title": "C", "artist": "Artist C", "genre": "pop", "mood": "happy", "energy": 0.7, "tempo_bpm": 140, "era": "2000s"},
        {"title": "D", "artist": "Artist D", "genre": "pop", "mood": "happy", "energy": 0.85, "tempo_bpm": 155, "era": "2020s"},
    ]
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.9, "tempo_bpm": 150, "era": "2020s"}
    results = recommend_songs(prefs, songs, k=3)
    
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    assert results[0]["score"] >= results[1]["score"], "Results not sorted by score"
    assert results[1]["score"] >= results[2]["score"], "Results not sorted by score"
    print("[PASS] test_recommend_songs_returns_top_3")


def test_recommend_songs_filters_zero_score():
    """Test that songs with score 0 are filtered out."""
    songs = [
        {"title": "A", "artist": "Artist A", "genre": "pop", "mood": "happy", "energy": 0.9, "tempo_bpm": 150, "era": "2020s"},
        {"title": "B", "artist": "Artist B", "genre": "rock", "mood": "angry", "energy": 0.8, "tempo_bpm": 120, "era": "1990s"},
    ]
    prefs = {"genre": "jazz", "mood": None, "energy": None, "tempo_bpm": None, "era": None}
    results = recommend_songs(prefs, songs, k=3)
    
    assert len(results) == 0, f"Expected 0 results (no matches), got {len(results)}"
    print("[PASS] test_recommend_songs_filters_zero_score")


if __name__ == "__main__":
    tests = [
        test_score_song_perfect_match,
        test_score_song_partial_match,
        test_score_song_no_match,
        test_score_song_era_matching,
        test_recommend_songs_returns_top_3,
        test_recommend_songs_filters_zero_score,
    ]
    
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
