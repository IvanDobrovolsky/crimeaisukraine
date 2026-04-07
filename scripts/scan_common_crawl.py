"""
Scan Common Crawl for Crimea-related URLs across years.

Uses the Common Crawl CDX Index API to find URLs mentioning "crimea"
in the URL path from each monthly crawl. This reveals which domains
were indexing Crimean content over time.

This is URL/domain-level only — not full text. For text, use
scan_training_corpora.py which runs on HF mirrors of CC derivatives.

Usage:
    python scripts/scan_common_crawl.py [--years 2014,2016,2018,2020,2022,2024]
"""

import json
import time
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from collections import Counter

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
OUT_PATH = DATA / "common_crawl_crimea.json"

HEADERS = {"User-Agent": "CrimeaAudit/1.0 (dobrovolsky94@gmail.com)"}


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None


def get_cc_indexes():
    """Get list of available Common Crawl monthly indexes."""
    data = fetch("https://index.commoncrawl.org/collinfo.json")
    if not data:
        return []
    return json.loads(data)


def query_cdx(cc_id, url_pattern, max_results=5000):
    """Query a single CC monthly index for URLs matching pattern."""
    base = f"https://index.commoncrawl.org/{cc_id}-index"
    params = {
        "url": url_pattern,
        "output": "json",
        "limit": max_results,
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"

    results = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line in resp:
                line = line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    results.append(json.loads(line))
                except Exception:
                    pass
    except Exception as e:
        return {"error": str(e)[:200], "results": results}

    return {"results": results}


def analyze_year(cc_id, year):
    """Analyze one year of CC for Crimean domain patterns."""
    print(f"\n--- {cc_id} ({year}) ---")

    patterns = [
        "*crimea*",
        "*simferopol*",
        "*sevastopol*",
    ]

    all_urls = []
    for pattern in patterns:
        result = query_cdx(cc_id, pattern, max_results=2000)
        if "results" in result:
            all_urls.extend(result["results"])
            print(f"  {pattern}: {len(result['results'])} urls")
        time.sleep(1)

    # Analyze: domain tld distribution
    tld_counts = Counter()
    domain_counts = Counter()

    for url_entry in all_urls:
        url = url_entry.get("url", "")
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or ""
            # TLD
            parts = host.split(".")
            if len(parts) >= 2:
                tld = parts[-1]
                tld_counts[tld] += 1
            domain_counts[host] += 1
        except Exception:
            pass

    return {
        "cc_id": cc_id,
        "year": year,
        "total_urls": len(all_urls),
        "tld_distribution": dict(tld_counts.most_common(15)),
        "top_domains": dict(domain_counts.most_common(20)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="2014,2016,2018,2020,2022,2024",
                        help="Comma-separated years to sample")
    args = parser.parse_args()

    target_years = [int(y) for y in args.years.split(",")]

    print("Common Crawl Crimea URL Analysis")
    print("=" * 60)
    print(f"Target years: {target_years}")

    # Get all available indexes
    all_indexes = get_cc_indexes()
    if not all_indexes:
        print("ERROR: Could not fetch CC index list")
        return

    # Pick one index per target year (use first crawl of the year)
    selected = {}
    for idx in all_indexes:
        cc_id = idx.get("id", "")
        # Format: CC-MAIN-YYYY-WW
        parts = cc_id.split("-")
        if len(parts) >= 4 and parts[2].isdigit():
            year = int(parts[2])
            if year in target_years and year not in selected:
                selected[year] = cc_id

    print(f"\nSelected indexes:")
    for year, cc_id in sorted(selected.items()):
        print(f"  {year}: {cc_id}")

    # Query each
    results = []
    for year in sorted(selected.keys()):
        cc_id = selected[year]
        try:
            result = analyze_year(cc_id, year)
            results.append(result)
            # Save after each
            with open(OUT_PATH, "w") as f:
                json.dump({
                    "date": datetime.now().isoformat()[:19],
                    "results": results,
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"{'year':>6s} {'total URLs':>12s} {'top TLDs':40s}")
    for r in results:
        top3_tlds = ", ".join(f"{t}={c}" for t, c in list(r["tld_distribution"].items())[:3])
        print(f"{r['year']:>6d} {r['total_urls']:>12,} {top3_tlds}")

    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
