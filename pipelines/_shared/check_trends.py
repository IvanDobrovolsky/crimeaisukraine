"""
Google Trends and Ngrams analysis for Crimea sovereignty framing.

Unlike kyivnotkiev (which tracks transliteration pairs), this tracks
CO-OCCURRENCE patterns: how often "Crimea" appears near "Ukraine" vs
near "Russia" in search queries and published text.

Queries:
  Google Trends: "Crimea Ukraine" vs "Crimea Russia" (search interest)
  Google Ngrams: "Crimea Ukraine" vs "Crimea Russia" (books, 1950-2019)

Usage:
    python scripts/check_trends.py
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from audit_framework import DATA_DIR

OUTPUT_DIR = DATA_DIR / "trends"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_google_trends():
    """Compare 'Crimea Ukraine' vs 'Crimea Russia' on Google Trends."""
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("Install pytrends: pip install pytrends")
        return None

    print("=== Google Trends ===")
    pytrends = TrendReq(hl="en-US", tz=0, retries=3, backoff_factor=1.0)

    queries = [
        # Main comparison
        {
            "keywords": ["Crimea Ukraine", "Crimea Russia"],
            "timeframe": "2013-01-01 2026-04-01",
            "label": "crimea_sovereignty_worldwide",
        },
        # "Crimea is Ukraine" vs "Crimea is Russia"
        {
            "keywords": ["Crimea is Ukraine", "Crimea is Russia"],
            "timeframe": "2013-01-01 2026-04-01",
            "label": "crimea_is_sovereignty",
        },
        # Annexed Crimea vs Russian Crimea
        {
            "keywords": ["annexed Crimea", "Russian Crimea"],
            "timeframe": "2013-01-01 2026-04-01",
            "label": "crimea_framing",
        },
    ]

    results = {}
    for q in queries:
        label = q["label"]
        print(f"\n  Querying: {q['keywords']}")
        try:
            pytrends.build_payload(
                q["keywords"],
                timeframe=q["timeframe"],
                geo="",  # worldwide
            )
            df = pytrends.interest_over_time()
            if df is not None and not df.empty:
                # Drop isPartial column
                if "isPartial" in df.columns:
                    df = df.drop(columns=["isPartial"])

                # Save CSV
                csv_path = OUTPUT_DIR / f"{label}.csv"
                df.to_csv(csv_path)
                print(f"  Saved: {csv_path} ({len(df)} rows)")

                # Summary stats
                for kw in q["keywords"]:
                    if kw in df.columns:
                        mean = df[kw].mean()
                        peak = df[kw].max()
                        peak_date = df[kw].idxmax()
                        print(f"    {kw}: mean={mean:.1f}, peak={peak} ({peak_date.strftime('%Y-%m')})")

                results[label] = {
                    "keywords": q["keywords"],
                    "rows": len(df),
                    "csv": str(csv_path),
                }
            else:
                print(f"  No data returned")
            time.sleep(5)  # Rate limit
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(10)

    return results


def fetch_ngrams():
    """Check Google Ngrams for 'Crimea Ukraine' vs 'Crimea Russia' in books."""
    import requests

    print("\n=== Google Ngrams (books corpus) ===")

    queries = [
        ("Crimea Ukraine,Crimea Russia", "crimea_sovereignty_ngram"),
        ("Russian Crimea,Ukrainian Crimea", "crimea_adj_ngram"),
        ("annexed Crimea,occupied Crimea", "crimea_framing_ngram"),
    ]

    results = {}
    for query_str, label in queries:
        print(f"\n  Querying: {query_str}")
        url = "https://books.google.com/ngrams/json"
        params = {
            "content": query_str,
            "year_start": 1950,
            "year_end": 2019,
            "corpus": 26,  # English 2019
            "smoothing": 3,
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    # Convert to CSV
                    rows = []
                    terms = query_str.split(",")
                    for i, series in enumerate(data):
                        term = series.get("ngram", terms[i] if i < len(terms) else f"term_{i}")
                        for year_idx, val in enumerate(series.get("timeseries", [])):
                            year = 1950 + year_idx
                            rows.append({"year": year, "term": term, "frequency": val})

                    df = pd.DataFrame(rows)
                    csv_path = OUTPUT_DIR / f"{label}.csv"
                    df.to_csv(csv_path, index=False)
                    print(f"  Saved: {csv_path} ({len(df)} rows)")

                    # Summary
                    for term in df["term"].unique():
                        subset = df[df["term"] == term]
                        peak_row = subset.loc[subset["frequency"].idxmax()]
                        print(f"    {term}: peak freq={peak_row['frequency']:.2e} in {int(peak_row['year'])}")

                    results[label] = {
                        "query": query_str,
                        "rows": len(df),
                        "csv": str(csv_path),
                    }
                else:
                    print(f"  Empty response")
            else:
                print(f"  HTTP {resp.status_code}")
            time.sleep(2)
        except Exception as e:
            print(f"  Error: {e}")

    return results


def run():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*60}")
    print(f"  CRIMEA SOVEREIGNTY TRENDS ANALYSIS")
    print(f"  {timestamp}")
    print(f"{'='*60}")

    all_results = {}

    # Google Trends
    trends = fetch_google_trends()
    if trends:
        all_results["google_trends"] = trends

    # Ngrams
    ngrams = fetch_ngrams()
    if ngrams:
        all_results["ngrams"] = ngrams

    # Save summary
    summary_path = OUTPUT_DIR / "trends_summary.json"
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Summary: {summary_path}")
    print(f"  CSV files in: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
