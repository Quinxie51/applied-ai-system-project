"""VibeMatch: a small RAG-based music recommender demo.

This script loads a small songs CSV, defines three user vibe profiles,
extracts structured preferences via `parse_vibe` (the RAG step), recommends
top songs, runs a reliability check, and prints results in tables.
"""
from typing import List, Dict
import csv
import os

from tabulate import tabulate

from src.embedder import parse_vibe
from src.recommender import recommend_songs
from src.reliability import reliability_check


def load_songs(csv_path: str) -> List[Dict[str, str]]:
    """Load songs.csv into a list of dicts."""
    songs = []
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            songs.append({k: v for k, v in row.items()})
    return songs


def print_top3_table(top3: List[Dict[str, object]]) -> None:
    """Pretty-print the top-3 using tabulate."""
    rows = []
    for i, s in enumerate(top3, start=1):
        rows.append([i, s.get("title"), s.get("artist"), s.get("score"), ", ".join(s.get("reasons", []))])
    print(tabulate(rows, headers=["rank", "title", "artist", "score", "reasons"]))


def main() -> None:
    base = os.path.dirname(__file__)
    csv_path = os.path.normpath(os.path.join(base, "data", "songs.csv"))
    songs = load_songs(csv_path)

    profiles = {
        "Profile 1": "upbeat pop songs for a workout",
        "Profile 2": "something sad and slow for a rainy day",
        "Profile 3": "nostalgic 90s hip hop with high energy",
    }

    all_results = {}

    for name, query in profiles.items():
        print(f"\n=== {name}: '{query}' ===")
        # RAG step: parse vibe
        try:
            prefs = parse_vibe(query)
        except Exception as e:
            prefs = {"genre": None, "mood": None, "energy": None, "tempo": None, "era": None}
            print(f"parse_vibe failed: {e}")

        # Recommend
        top3 = recommend_songs(prefs, songs)
        print_top3_table(top3)

        # Reliability
        reliability = reliability_check(query, top3)
        print("\nReliability:")
        print(reliability)

        all_results[name] = {"query": query, "prefs": prefs, "top3": top3, "reliability": reliability}

    # Final summary
    print("\n=== Final summary of profiles ===")
    for name, info in all_results.items():
        titles = [s.get("title") for s in info["top3"]]
        print(f"{name}: top -> {titles} | stable: {info['reliability']['stable']}")


if __name__ == "__main__":
    main()
