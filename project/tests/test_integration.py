"""Integration tests for full VibeMatch pipeline."""
import sys
import csv
sys.path.insert(0, '/'.join(__file__.split('/')[:-2]))

from src.embedder import parse_vibe, parse_vibe_with_confidence
from src.recommender import recommend_songs


def load_test_songs():
    """Load songs from CSV."""
    import os
    base = os.path.dirname(__file__)
    csv_path = os.path.normpath(os.path.join(base, "..", "data", "songs.csv"))
    songs = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                songs.append({k: v for k, v in row.items()})
    except Exception as e:
        print(f"Warning: Could not load songs.csv: {e}")
        return []
    return songs


def test_dataset_valid():
    """Test that the dataset loads and is valid."""
    songs = load_test_songs()
    assert len(songs) > 0, "No songs loaded from CSV"
    assert len(songs) == 20, f"Expected 20 songs, got {len(songs)}"
    
    # Check required columns
    required_cols = ["genre", "mood", "energy", "tempo_bpm", "title", "artist", "era"]
    for song in songs:
        for col in required_cols:
            assert col in song, f"Missing column '{col}' in song {song.get('title')}"
    
    print(f"✓ test_dataset_valid passed ({len(songs)} songs loaded)")


def test_recommendation_returns_valid_structure():
    """Test that recommendation returns valid structure."""
    songs = load_test_songs()
    if not songs:
        print("⊘ test_recommendation_returns_valid_structure skipped (no songs)")
        return
    
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.9, "tempo_bpm": 150, "era": None}
    results = recommend_songs(prefs, songs, k=3)
    
    for result in results:
        assert "title" in result
        assert "artist" in result
        assert "score" in result
        assert isinstance(result["score"], (int, float))
        assert 0 <= result["score"] <= 100
        assert "reasons" in result
        assert isinstance(result["reasons"], list)
    
    print("✓ test_recommendation_returns_valid_structure passed")


def test_confidence_scoring():
    """Test that confidence scoring works."""
    parsed, confidence = parse_vibe_with_confidence("test query")
    
    assert isinstance(confidence, float), f"Expected float confidence, got {type(confidence)}"
    assert 0.0 <= confidence <= 1.0, f"Expected confidence in [0.0, 1.0], got {confidence}"
    assert isinstance(parsed, dict), f"Expected dict parsed, got {type(parsed)}"
    assert all(k in parsed for k in ["genre", "mood", "energy", "tempo_bpm", "era"])
    
    print(f"✓ test_confidence_scoring passed (confidence={confidence:.2f})")


def test_null_prefs_no_recommendations():
    """Test that all-null prefs return no recommendations."""
    songs = load_test_songs()
    if not songs:
        print("⊘ test_null_prefs_no_recommendations skipped (no songs)")
        return
    
    prefs = {"genre": None, "mood": None, "energy": None, "tempo_bpm": None, "era": None}
    results = recommend_songs(prefs, songs, k=3)
    
    assert len(results) == 0, f"Expected no results for all-null prefs, got {len(results)}"
    
    print("✓ test_null_prefs_no_recommendations passed")


if __name__ == "__main__":
    tests = [
        test_dataset_valid,
        test_recommendation_returns_valid_structure,
        test_confidence_scoring,
        test_null_prefs_no_recommendations,
    ]
    
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
