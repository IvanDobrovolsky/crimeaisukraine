"""
GDELT Sovereignty Framing Scanner

Searches GDELT DOC API for articles mentioning Crimea (2010-2026),
classifies each article's sovereignty framing using the Rust classifier,
and stores violators with source URL, title, date, and evidence.

Stage 1: GDELT API → article titles → Rust crimea-classify
Stage 2: LLM verification (separate script: llm_verify.py)

Usage:
    python pipelines/media/scan_gdelt_framing.py
    python pipelines/media/scan_gdelt_framing.py --start 2014 --end 2026
    python pipelines/media/scan_gdelt_framing.py --quick  # last 3 months only
"""

import argparse
import csv
import json
import subprocess
import tempfile
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).parent.parent.parent
DATA = PROJECT / "data"
SCANNER = PROJECT / "c4_sovereignty" / "scanner" / "target" / "release" / "crimea-classify"

# TLD → country mapping for major domains
TLD_COUNTRY = {
    'ru': 'Russia', 'su': 'Russia', 'ua': 'Ukraine', 'by': 'Belarus',
    'de': 'Germany', 'fr': 'France', 'it': 'Italy', 'es': 'Spain',
    'uk': 'UK', 'pl': 'Poland', 'cz': 'Czechia', 'nl': 'Netherlands',
    'tr': 'Turkey', 'cn': 'China', 'jp': 'Japan', 'kr': 'South Korea',
    'in': 'India', 'br': 'Brazil', 'ae': 'UAE', 'il': 'Israel',
    'ge': 'Georgia', 'kz': 'Kazakhstan', 'az': 'Azerbaijan',
    'md': 'Moldova', 'lv': 'Latvia', 'lt': 'Lithuania', 'ee': 'Estonia',
}

KNOWN_DOMAINS = {
    'bbc.com': 'UK', 'bbc.co.uk': 'UK', 'reuters.com': 'UK',
    'nytimes.com': 'US', 'washingtonpost.com': 'US', 'cnn.com': 'US',
    'theguardian.com': 'UK', 'dw.com': 'Germany', 'aljazeera.com': 'Qatar',
    'rt.com': 'Russia', 'sputniknews.com': 'Russia',
    'pravda.com.ua': 'Ukraine', 'kyivindependent.com': 'Ukraine',
    'eurointegration.com.ua': 'Ukraine', 'ukrinform.net': 'Ukraine',
    'ura.news': 'Russia', 'gazeta.ru': 'Russia', 'rbc.ru': 'Russia',
    'meduza.io': 'Russia', 'novayagazeta.eu': 'Russia',
}

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

QUERIES = [
    '"Simferopol" AND ("Ukraine" OR "Russia")',
    '"Crimea" AND ("sovereignty" OR "annexed" OR "reunified")',
    '"Republic of Crimea" AND NOT "Autonomous"',
    '"Autonomous Republic of Crimea"',
    '"Crimea" AND ("belongs to" OR "part of") AND ("Ukraine" OR "Russia")',
    '"Crimea" AND ("country code" OR "country_code" OR "classified")',
]


def get_domain_country(domain: str) -> str:
    domain = domain.lower().strip()
    for known, country in KNOWN_DOMAINS.items():
        if domain == known or domain.endswith('.' + known):
            return country
    tld = domain.rsplit('.', 1)[-1] if '.' in domain else ''
    return TLD_COUNTRY.get(tld, '')


def generate_quarters(start_year: int, end_year: int) -> list[tuple[str, str]]:
    quarters = []
    for year in range(start_year, end_year + 1):
        for q_start, q_end in [("0101", "0331"), ("0401", "0630"), ("0701", "0930"), ("1001", "1231")]:
            start = f"{year}{q_start}000000"
            end = f"{year}{q_end}235959"
            if int(start[:8]) > int(datetime.now().strftime("%Y%m%d")):
                break
            quarters.append((start, end))
    return quarters


def search_gdelt(query: str, start: str = "", end: str = "", timespan: str = "") -> list[dict]:
    params = {
        "query": query,
        "format": "json",
        "maxrecords": "250",
        "sort": "DateDesc",
        "mode": "ArtList",
    }
    if start and end:
        params["startdatetime"] = start
        params["enddatetime"] = end
    elif timespan:
        params["timespan"] = timespan

    url = GDELT_DOC_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "CrimeaAudit/1.0 (research)"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data.get("articles", [])
    except Exception as e:
        print(f"    Error: {e}")
        return []


def classify_with_rust(articles: list[dict]) -> dict[str, dict]:
    """Run Rust crimea-classify on article titles. Returns {url: classification}."""
    if not articles:
        return {}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as inp:
        for a in articles:
            json.dump({"text": a["title"], "url": a["url"], "file": "gdelt"}, inp)
            inp.write("\n")
        inp_path = inp.name

    out_path = inp_path + ".classified"

    result = subprocess.run(
        [str(SCANNER), "--input", inp_path, "--output", out_path, "--threads", "4"],
        capture_output=True, text=True
    )

    classifications = {}
    try:
        with open(out_path) as f:
            for line in f:
                r = json.loads(line)
                classifications[r["url"]] = r
    except FileNotFoundError:
        print(f"  Classifier error: {result.stderr[:200]}")

    Path(inp_path).unlink(missing_ok=True)
    Path(out_path).unlink(missing_ok=True)

    return classifications


def main():
    parser = argparse.ArgumentParser(description="GDELT Crimea sovereignty framing scanner")
    parser.add_argument("--start", type=int, default=2010, help="Start year (default: 2010)")
    parser.add_argument("--end", type=int, default=2026, help="End year (default: 2026)")
    parser.add_argument("--quick", action="store_true", help="Quick scan: last 3 months only")
    args = parser.parse_args()

    if not SCANNER.exists():
        print(f"ERROR: Rust classifier not found at {SCANNER}")
        print("Run: cd c4_sovereignty/scanner && cargo build --release --bin crimea-classify")
        return

    all_articles = []
    seen_urls = set()

    print("GDELT Sovereignty Framing Scanner (Rust classifier)")
    print(f"Period: {args.start}-{args.end}")
    print("=" * 60)

    if args.quick:
        periods = [("recent", "", "", "3m")]
    else:
        quarters = generate_quarters(args.start, args.end)
        periods = [(f"{q[0][:4]}Q{(int(q[0][4:6])-1)//3+1}", q[0], q[1], "") for q in quarters]

    total_api_calls = 0

    # Stage 1a: Fetch all articles from GDELT
    for period_label, start, end, timespan in periods:
        print(f"\n--- {period_label} ---")
        for query in QUERIES:
            articles = search_gdelt(query, start, end, timespan)
            total_api_calls += 1

            for article in articles:
                url = article.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                all_articles.append({
                    "url": url,
                    "title": article.get("title", ""),
                    "source": article.get("domain", ""),
                    "date": article.get("seendate", ""),
                    "language": article.get("language", ""),
                    "period": period_label,
                    "domain_country": get_domain_country(article.get("domain", "")),
                })

            time.sleep(0.5)

        print(f"  Total articles so far: {len(all_articles)}")

    print(f"\n{'=' * 60}")
    print(f"GDELT fetch complete: {len(all_articles)} unique articles, {total_api_calls} API calls")

    # Stage 1b: Classify all titles with Rust classifier
    print(f"\nClassifying {len(all_articles)} titles with Rust crimea-classify...")
    classifications = classify_with_rust(all_articles)

    # Merge classifications back
    all_results = []
    for article in all_articles:
        cls = classifications.get(article["url"], {})
        label = cls.get("label", "no_signal")
        if label == "no_signal":
            continue
        article["label"] = label
        article["ru_score"] = cls.get("ru_score", 0)
        article["ua_score"] = cls.get("ua_score", 0)
        article["is_quoted"] = cls.get("is_quoted", False)
        article["framing_type"] = cls.get("framing_type", "")
        article["source_type"] = cls.get("source_type", "")
        all_results.append(article)

    # Summary
    by_label = {}
    by_year = {}
    for r in all_results:
        l = r["label"]
        by_label[l] = by_label.get(l, 0) + 1
        year = r.get("date", "")[:4] or r.get("period", "")[:4]
        if year:
            if year not in by_year:
                by_year[year] = {"ukraine": 0, "russia": 0, "disputed": 0}
            if l in by_year[year]:
                by_year[year][l] += 1

    print(f"\nCLASSIFICATION COMPLETE")
    print(f"  Total articles scanned: {len(all_articles)}")
    print(f"  Articles with sovereignty signals: {len(all_results)}")
    for label, count in sorted(by_label.items()):
        icon = {"ukraine": "✅", "russia": "❌", "disputed": "⚠️"}.get(label, "?")
        print(f"  {icon} {label}: {count}")

    if by_year:
        print(f"\n  Year-by-year framing:")
        for year in sorted(by_year.keys()):
            y = by_year[year]
            print(f"    {year}: UA={y['ukraine']:3d}  RU={y['russia']:3d}  disputed={y['disputed']:3d}")

    flagged = [r for r in all_results if r["label"] == "russia"]
    ru_domain = [r for r in flagged if r.get("domain_country") == "Russia"]
    non_ru_domain = [r for r in flagged if r.get("domain_country") != "Russia"]

    if flagged:
        print(f"\n❌ TOTAL Russian-framing articles: {len(flagged)}")
        print(f"   From Russian domains (expected): {len(ru_domain)}")
        print(f"   From non-Russian domains (SIGNIFICANT): {len(non_ru_domain)}")

    # Save endorsers CSV
    endorsers_path = DATA / "media_russia_endorses.csv"
    with open(endorsers_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "domain", "country", "source_type", "framing_type", "ru_score", "title"])
        for r in flagged:
            writer.writerow([
                r["url"], r["source"], r.get("domain_country", ""),
                r.get("source_type", ""), r.get("framing_type", ""),
                r.get("ru_score", 0), r["title"]
            ])
    print(f"\nEndorsers saved to {endorsers_path} ({len(flagged)} rows)")

    # Save full results
    output = DATA / "gdelt_framing_results.json"
    with open(output, "w") as f:
        json.dump({
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "classifier": "rust crimea-classify (91 signals)",
            "period": f"{args.start}-{args.end}",
            "total_articles_fetched": len(all_articles),
            "total_api_calls": total_api_calls,
            "articles_with_signals": len(all_results),
            "by_label": by_label,
            "by_year": by_year,
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)
    print(f"Full results saved to {output}")


if __name__ == "__main__":
    main()
