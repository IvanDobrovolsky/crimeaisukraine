"""
GDELT Sovereignty Framing Scanner

Searches GDELT DOC API for articles mentioning Crimea (2010-2026),
classifies each article's sovereignty framing, and stores violators
with source URL, title, date, and evidence.

Paginates by quarter since GDELT DOC API limits timespan per request.

Usage:
    python scripts/scan_gdelt_framing.py
    python scripts/scan_gdelt_framing.py --start 2014 --end 2026
    python scripts/scan_gdelt_framing.py --quick  # last 3 months only
"""

import argparse
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from sovereignty_classifier import SovereigntyClassifier

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

# Known domains and their countries (for .com/.org/.net)
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


def get_domain_country(domain: str) -> str:
    """Determine the country of a domain from TLD or known list."""
    domain = domain.lower().strip()
    # Check known domains first
    for known, country in KNOWN_DOMAINS.items():
        if domain == known or domain.endswith('.' + known):
            return country
    # Check TLD
    tld = domain.rsplit('.', 1)[-1] if '.' in domain else ''
    return TLD_COUNTRY.get(tld, '')

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

# Queries that surface sovereignty-relevant articles
QUERIES = [
    '"Simferopol" AND ("Ukraine" OR "Russia")',
    '"Crimea" AND ("sovereignty" OR "annexed" OR "reunified")',
    '"Republic of Crimea" AND NOT "Autonomous"',
    '"Autonomous Republic of Crimea"',
    '"Crimea" AND ("belongs to" OR "part of") AND ("Ukraine" OR "Russia")',
    '"Crimea" AND ("country code" OR "country_code" OR "classified")',
]

# Quarterly date ranges for pagination (YYYYMMDDHHMMSS format)
def generate_quarters(start_year: int, end_year: int) -> list[tuple[str, str]]:
    """Generate quarterly date ranges for GDELT API pagination."""
    quarters = []
    for year in range(start_year, end_year + 1):
        for q_start, q_end in [("0101", "0331"), ("0401", "0630"), ("0701", "0930"), ("1001", "1231")]:
            start = f"{year}{q_start}000000"
            end = f"{year}{q_end}235959"
            # Don't go past today
            if int(start[:8]) > int(datetime.now().strftime("%Y%m%d")):
                break
            quarters.append((start, end))
    return quarters


def search_gdelt(query: str, start: str = "", end: str = "", timespan: str = "") -> list[dict]:
    """Search GDELT DOC API and return article list."""
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


def main():
    parser = argparse.ArgumentParser(description="GDELT Crimea sovereignty framing scanner")
    parser.add_argument("--start", type=int, default=2010, help="Start year (default: 2010)")
    parser.add_argument("--end", type=int, default=2026, help="End year (default: 2026)")
    parser.add_argument("--quick", action="store_true", help="Quick scan: last 3 months only")
    args = parser.parse_args()

    clf = SovereigntyClassifier()
    all_results = []
    seen_urls = set()

    print("GDELT Sovereignty Framing Scanner")
    print(f"Period: {args.start}-{args.end}")
    print("=" * 60)

    if args.quick:
        # Quick mode: single timespan
        periods = [("recent", "", "", "3m")]
    else:
        # Full mode: paginate by quarter
        quarters = generate_quarters(args.start, args.end)
        periods = [(f"{q[0][:4]}Q{(int(q[0][4:6])-1)//3+1}", q[0], q[1], "") for q in quarters]

    total_api_calls = 0

    for period_label, start, end, timespan in periods:
        print(f"\n--- {period_label} ---")

        for query in QUERIES:
            articles = search_gdelt(query, start, end, timespan)
            total_api_calls += 1

            new_count = 0
            for article in articles:
                url = article.get("url", "")
                title = article.get("title", "")
                source = article.get("domain", "")
                date = article.get("seendate", "")
                language = article.get("language", "")

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Detect domain country
                domain_country = get_domain_country(source)

                # Classify based on title ONLY (not URL — URL TLDs are not framing)
                result = clf.classify(title)

                if result.label == "no_signal":
                    continue

                new_count += 1
                all_results.append({
                    "url": url,
                    "title": title,
                    "source": source,
                    "domain_country": domain_country,
                    "date": date,
                    "language": language,
                    "period": period_label,
                    "label": result.label,
                    "confidence": round(result.confidence, 3),
                    "ua_score": round(result.ua_score, 3),
                    "ru_score": round(result.ru_score, 3),
                    "signals": [
                        {"pattern": s.pattern, "matched": s.matched, "label": s.label}
                        for s in result.signals
                    ],
                })

            if new_count > 0:
                print(f"  +{new_count} from: {query[:50]}...")

            time.sleep(0.5)  # Rate limit

        # Progress
        by_label = {}
        for r in all_results:
            by_label[r["label"]] = by_label.get(r["label"], 0) + 1
        print(f"  Running total: {len(all_results)} articles | {by_label}")

    # --- Final summary ---
    by_label = {}
    by_year = {}
    for r in all_results:
        l = r["label"]
        by_label[l] = by_label.get(l, 0) + 1
        year = r.get("date", "")[:4] or r.get("period", "")[:4]
        if year:
            if year not in by_year:
                by_year[year] = {"ukraine": 0, "russia": 0, "disputed": 0, "neutral": 0}
            if l in by_year[year]:
                by_year[year][l] += 1

    print(f"\n{'=' * 60}")
    print(f"SCAN COMPLETE")
    print(f"  API calls: {total_api_calls}")
    print(f"  Articles with sovereignty signals: {len(all_results)}")
    for label, count in sorted(by_label.items()):
        icon = {"ukraine": "✅", "russia": "❌", "disputed": "⚠️", "neutral": "—"}.get(label, "?")
        print(f"  {icon} {label}: {count}")

    # Year-by-year trend
    if by_year:
        print(f"\n  Year-by-year framing:")
        for year in sorted(by_year.keys()):
            y = by_year[year]
            print(f"    {year}: UA={y['ukraine']:3d}  RU={y['russia']:3d}  disputed={y['disputed']:3d}")

    # Flagged violators — split by domain country
    flagged = [r for r in all_results if r["label"] == "russia"]
    ru_domain = [r for r in flagged if r.get("domain_country") == "Russia"]
    non_ru_domain = [r for r in flagged if r.get("domain_country") != "Russia"]

    if flagged:
        print(f"\n❌ TOTAL Russian-framing articles: {len(flagged)}")
        print(f"   From Russian domains (expected): {len(ru_domain)}")
        print(f"   From non-Russian domains (SIGNIFICANT): {len(non_ru_domain)}")

    if non_ru_domain:
        print(f"\n🔴 NON-RUSSIAN SOURCES using Russian framing ({len(non_ru_domain)}):")
        for r in non_ru_domain:
            country = r.get('domain_country') or 'Unknown'
            print(f"  [{country:10s}] {r['source']:25s} {r['title'][:55]}")
            print(f"  {'':10s}  {'':25s} {r['url']}")
            signals = ', '.join(s['matched'] for s in r['signals'][:3])
            print(f"  {'':10s}  {'':25s} Signals: {signals}")

    if ru_domain:
        print(f"\n  Russian-domain articles (noise, {len(ru_domain)}):")
        by_source = {}
        for r in ru_domain:
            by_source.setdefault(r["source"], []).append(r)
        for source, arts in sorted(by_source.items(), key=lambda x: -len(x[1]))[:10]:
            print(f"    {source}: {len(arts)} articles")

    # Save
    output = DATA / "gdelt_framing_results.json"
    with open(output, "w") as f:
        json.dump({
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "period": f"{args.start}-{args.end}",
            "total_articles": len(all_results),
            "total_api_calls": total_api_calls,
            "by_label": by_label,
            "by_year": by_year,
            "violators": [r for r in all_results if r["label"] == "russia"],
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output}")


if __name__ == "__main__":
    main()
