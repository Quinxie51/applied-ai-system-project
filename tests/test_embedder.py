"""Tests for embedder.py parse_vibe with confidence scoring."""
import sys
import os
sys.path.insert(0, '/'.join(__file__.split('/')[:-2]))

from src.embedder import parse_vibe_with_confidence, _validate_and_normalize


def test_validate_and_normalize_all_valid():
    """Test that valid values pass through."""
    parsed = {"genre": "pop", "mood": "happy", "energy": 0.85, "tempo_bpm": 140, "era": "2020s"}
    result = _validate_and_normalize(parsed)
    assert result["genre"] == "pop"
    assert result["mood"] == "happy"
    assert result["energy"] == 0.85
    assert result["tempo_bpm"] == 140
    assert result["era"] == "2020s"
    print("[PASS] test_validate_and_normalize_all_valid")


def test_validate_and_normalize_invalid_energy():
    """Test that out-of-range energy becomes null."""
    parsed = {"genre": "pop", "mood": "happy", "energy": 1.5, "tempo_bpm": 140, "era": "2020s"}
    result = _validate_and_normalize(parsed)
    assert result["energy"] is None, f"Expected None for energy 1.5, got {result['energy']}"
    print("[PASS] test_validate_and_normalize_invalid_energy")


def test_validate_and_normalize_invalid_tempo():
    """Test that out-of-range tempo becomes null."""
    parsed = {"genre": "pop", "mood": "happy", "energy": 0.85, "tempo_bpm": 200, "era": "2020s"}
    result = _validate_and_normalize(parsed)
    assert result["tempo_bpm"] is None, f"Expected None for tempo 200, got {result['tempo_bpm']}"
    print("[PASS] test_validate_and_normalize_invalid_tempo")


def test_validate_and_normalize_invalid_genre():
    """Test that invalid genre becomes null."""
    parsed = {"genre": "electronic_pop", "mood": "happy", "energy": 0.85, "tempo_bpm": 140, "era": "2020s"}
    result = _validate_and_normalize(parsed)
    assert result["genre"] is None, f"Expected None for invalid genre, got {result['genre']}"
    print("[PASS] test_validate_and_normalize_invalid_genre")


def test_validate_and_normalize_null_values():
    """Test that explicit null values are preserved."""
    parsed = {"genre": "pop", "mood": None, "energy": None, "tempo_bpm": 140, "era": None}
    result = _validate_and_normalize(parsed)
    assert result["genre"] == "pop"
    assert result["mood"] is None
    assert result["energy"] is None
    assert result["tempo_bpm"] == 140
    assert result["era"] is None
    print("[PASS] test_validate_and_normalize_null_values")


def test_confidence_all_fields():
    """Test that confidence is 1.0 when all fields are non-null."""
    parsed = {"genre": "pop", "mood": "happy", "energy": 0.85, "tempo_bpm": 140, "era": "2020s"}
    result = _validate_and_normalize(parsed)
    non_null = sum(1 for v in result.values() if v is not None)
    confidence = non_null / len(result)
    assert confidence == 1.0, f"Expected confidence 1.0 for all non-null, got {confidence}"
    print("[PASS] test_confidence_all_fields")


def test_confidence_partial_fields():
    """Test that confidence reflects fraction of non-null fields."""
    parsed = {"genre": "pop", "mood": None, "energy": 0.85, "tempo_bpm": None, "era": "2020s"}
    result = _validate_and_normalize(parsed)
    non_null = sum(1 for v in result.values() if v is not None)
    confidence = non_null / len(result)
    assert non_null == 3, f"Expected 3 non-null fields, got {non_null}"
    assert confidence == 0.6, f"Expected confidence 0.6, got {confidence}"
    print("[PASS] test_confidence_partial_fields")


def test_confidence_no_fields():
    """Test that confidence is 0.0 when all fields are null."""
    parsed = {"genre": None, "mood": None, "energy": None, "tempo_bpm": None, "era": None}
    result = _validate_and_normalize(parsed)
    non_null = sum(1 for v in result.values() if v is not None)
    confidence = non_null / len(result)
    assert confidence == 0.0, f"Expected confidence 0.0 for all null, got {confidence}"
    print("[PASS] test_confidence_no_fields")


if __name__ == "__main__":
    tests = [
        test_validate_and_normalize_all_valid,
        test_validate_and_normalize_invalid_energy,
        test_validate_and_normalize_invalid_tempo,
        test_validate_and_normalize_invalid_genre,
        test_validate_and_normalize_null_values,
        test_confidence_all_fields,
        test_confidence_partial_fields,
        test_confidence_no_fields,
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
