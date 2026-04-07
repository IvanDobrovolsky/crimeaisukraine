"""
Scan ROOTS corpus (BLOOM training data) for Crimea framing.

ROOTS is the 1.6TB multilingual corpus used to train BLOOM.
Access is gated, but the HuggingFace Space bigscience-data/roots-search
provides a BM25 search interface we can query via gradio_client.

Usage:
    pip install gradio_client
    python scripts/scan_roots_corpus.py
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
OUT_PATH = DATA / "roots_crimea_framing.json"

# Phrase queries grouped by framing direction
# These are literal phrases because the ROOTS search is BM25-based, not regex
UKRAINE_FRAME_PHRASES = [
    "Crimea, Ukraine",
    "Autonomous Republic of Crimea",
    "annexation of Crimea",
    "illegally annexed Crimea",
    "occupied Crimea",
    "temporarily occupied Crimea",
    "Ukrainian Crimea",
    "Ukraine's Crimea",
    "Russian occupation of Crimea",
    "Crimea is part of Ukraine",
    "Crimea under Russian occupation",
    "Crimea, Ukraine",
    "Simferopol, Ukraine",
    "Sevastopol, Ukraine",
    "Крим, Україна",
    "анексія Криму",
    "окупований Крим",
    "тимчасово окупований Крим",
    "Автономна Республіка Крим",
]

RUSSIA_FRAME_PHRASES = [
    "Crimea, Russia",
    "Republic of Crimea",
    "Republic of Crimea, Russia",
    "reunification of Crimea",
    "reunification of Crimea with Russia",
    "Russian Crimea",
    "Crimea is Russian",
    "Crimea belongs to Russia",
    "return of Crimea to Russia",
    "Simferopol, Russia",
    "Sevastopol, Russia",
    "Krim, Russland",
    "Крым, Россия",
    "Республика Крым",
    "присоединение Крыма",
    "возвращение Крыма",
    "воссоединение Крыма",
    "Крым наш",
    "Крым вернулся в Россию",
]

NEUTRAL_PHRASES = [
    "Crimea",
    "Crimean peninsula",
    "Krym",
    "Крым",
    "Крим",
]


def query_roots(phrase):
    """Query the ROOTS search HuggingFace Space."""
    try:
        from gradio_client import Client
    except ImportError:
        return {"error": "gradio_client not installed. Run: pip install gradio_client"}

    try:
        client = Client("bigscience-data/roots-search")
        # The Space API takes a search query and returns count + snippets
        result = client.predict(phrase, api_name="/predict")
        return {"phrase": phrase, "result": str(result)[:1000]}
    except Exception as e:
        return {"phrase": phrase, "error": str(e)[:200]}


def main():
    print("ROOTS Corpus Crimea Framing Audit")
    print("=" * 60)
    print("Querying bigscience-data/roots-search (BLOOM training data)")

    results = {
        "source": "ROOTS (BigScience / BLOOM)",
        "access": "Gated corpus; queried via HuggingFace Space bigscience-data/roots-search",
        "date": datetime.now().isoformat()[:19],
        "ukraine_frame": [],
        "russia_frame": [],
        "neutral": [],
    }

    print("\n--- Ukraine-framing phrases ---")
    for phrase in UKRAINE_FRAME_PHRASES:
        r = query_roots(phrase)
        results["ukraine_frame"].append(r)
        print(f"  [{phrase[:50]}] → {str(r.get('result', r.get('error', '')))[:100]}")

    print("\n--- Russia-framing phrases ---")
    for phrase in RUSSIA_FRAME_PHRASES:
        r = query_roots(phrase)
        results["russia_frame"].append(r)
        print(f"  [{phrase[:50]}] → {str(r.get('result', r.get('error', '')))[:100]}")

    print("\n--- Neutral phrases ---")
    for phrase in NEUTRAL_PHRASES:
        r = query_roots(phrase)
        results["neutral"].append(r)
        print(f"  [{phrase[:50]}] → {str(r.get('result', r.get('error', '')))[:100]}")

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
