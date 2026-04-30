"""VibeMatch: a small RAG-based music recommender demo.

This script loads a small songs CSV, defines three user vibe profiles,
extracts structured preferences via `parse_vibe` (the RAG step), recommends
top songs, runs a reliability check, and prints results in tables.
"""
from typing import List, Dict
import csv
import os
import logging

from tabulate import tabulate

from src.embedder import parse_vibe_with_confidence
from src.recommender import recommend_songs
from src.reliability import reliability_check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


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

    profiles = [
        "upbeat pop songs for a workout",
        "something sad and slow for a rainy day",
        "nostalgic 90s hip hop with high energy",
    ]

    all_results = []

    for query in profiles:
        print(f"\n=== Profile query: '{query}' ===")

        # RAG step: parse vibe with confidence
        prefs, confidence = parse_vibe_with_confidence(query)
        print(f"Extracted prefs (confidence: {confidence:.0%}): {prefs}")

        # Recommend (k=3)
        top3 = recommend_songs(prefs, songs, k=3)
        # Print table with rounded_outline
        rows = []
        for i, s in enumerate(top3, start=1):
            rows.append([i, s.get("title"), s.get("artist"), s.get("score"), ", ".join(s.get("reasons", []))])
        print(tabulate(rows, headers=["Rank", "Title", "Artist", "Score", "Reasons"], tablefmt="rounded_outline"))

        # Reliability
        reliability = reliability_check(query, top3, songs)
        print("Reliability:", reliability)

        all_results.append({"query": query, "prefs": prefs, "confidence": confidence, "top3": top3, "reliability": reliability})

    # Final summary
    print("\n=== Final summary of profiles ===")
    for info in all_results:
        titles = [s.get("title") for s in info["top3"]]
        print(f"{info['query']}: top -> {titles} | stable: {info['reliability']['stable']}")


if __name__ == "__main__":
    main()
