"""
Unified Sovereignty Framing Pilot — 2020-2021

Searches ALL Crimea mentions across GDELT (media) and OpenAlex (academic),
deduplicates, classifies each with 81 sovereignty signals, outputs one
unified dataset.

Usage:
    python scripts/scan_pilot.py
    python scripts/scan_pilot.py --start 2020 --end 2021
    python scripts/scan_pilot.py --start 2022 --end 2026
"""

import argparse
import json
import time
import urllib.request
import urllib.parse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from sovereignty_classifier import SovereigntyClassifier

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"

CONTACT_EMAIL = "dobrovolsky94@gmail.com"

# ── GDELT ──────────────────────────────────────────────

GDELT_API = "https://api.gdeltproject.org/api/v2/doc/doc"

# TLD → country
TLD_COUNTRY = {
    'ru': 'Russia', 'su': 'Russia', 'ua': 'Ukraine', 'by': 'Belarus',
    'de': 'Germany', 'fr': 'France', 'it': 'Italy', 'es': 'Spain',
    'uk': 'UK', 'co.uk': 'UK', 'pl': 'Poland', 'cz': 'Czechia',
    'nl': 'Netherlands', 'tr': 'Turkey', 'cn': 'China', 'jp': 'Japan',
    'kr': 'South Korea', 'in': 'India', 'br': 'Brazil', 'ae': 'UAE',
    'il': 'Israel', 'ge': 'Georgia', 'kz': 'Kazakhstan', 'md': 'Moldova',
    'lv': 'Latvia', 'lt': 'Lithuania', 'ee': 'Estonia', 'fi': 'Finland',
    'se': 'Sweden', 'no': 'Norway', 'dk': 'Denmark', 'at': 'Austria',
    'ch': 'Switzerland', 'be': 'Belgium', 'pt': 'Portugal', 'ro': 'Romania',
    'bg': 'Bulgaria', 'hu': 'Hungary', 'sk': 'Slovakia', 'hr': 'Croatia',
    'rs': 'Serbia', 'si': 'Slovenia', 'gr': 'Greece', 'ie': 'Ireland',
}

KNOWN_DOMAINS = {
    'bbc.com': 'UK', 'bbc.co.uk': 'UK', 'reuters.com': 'UK',
    'nytimes.com': 'US', 'washingtonpost.com': 'US', 'cnn.com': 'US',
    'theguardian.com': 'UK', 'ft.com': 'UK', 'telegraph.co.uk': 'UK',
    'dw.com': 'Germany', 'aljazeera.com': 'Qatar', 'aljazeera.net': 'Qatar',
    'france24.com': 'France', 'lemonde.fr': 'France',
    'rt.com': 'Russia', 'sputniknews.com': 'Russia', 'ura.news': 'Russia',
    'gazeta.ru': 'Russia', 'rbc.ru': 'Russia', 'meduza.io': 'Russia',
    'pravda.com.ua': 'Ukraine', 'kyivindependent.com': 'Ukraine',
    'ukrinform.net': 'Ukraine', 'unian.net': 'Ukraine',
    'globalsecurity.org': 'US', 'voanews.com': 'US',
}


def get_domain_country(domain: str) -> str:
    domain = domain.lower().strip()
    for known, country in KNOWN_DOMAINS.items():
        if domain == known or domain.endswith('.' + known):
            return country
    parts = domain.rsplit('.', 2)
    if len(parts) >= 2:
        tld2 = '.'.join(parts[-2:])
        if tld2 in TLD_COUNTRY:
            return TLD_COUNTRY[tld2]
    tld = parts[-1]
    return TLD_COUNTRY.get(tld, '')


def generate_quarters(start_year: int, end_year: int) -> list[tuple[str, str]]:
    quarters = []
    for year in range(start_year, end_year + 1):
        for qs, qe in [("0101", "0331"), ("0401", "0630"), ("0701", "0930"), ("1001", "1231")]:
            start = f"{year}{qs}000000"
            end = f"{year}{qe}235959"
            if int(start[:8]) > int(datetime.now().strftime("%Y%m%d")):
                break
            quarters.append((start, end))
    return quarters


def fetch_gdelt(query: str, start: str, end: str) -> list[dict]:
    params = {
        "query": query, "format": "json", "maxrecords": "250",
        "sort": "DateDesc", "mode": "ArtList",
        "startdatetime": start, "enddatetime": end,
    }
    url = GDELT_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "CrimeaAudit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()).get("articles", [])
    except Exception as e:
        print(f"    GDELT error: {e}")
        return []


def collect_gdelt(start_year: int, end_year: int) -> list[dict]:
    """Collect all Crimea mentions from GDELT."""
    print(f"\n{'='*60}")
    print(f"GDELT: Collecting Crimea articles {start_year}-{end_year}")
    print(f"{'='*60}")

    # Broad query — get everything mentioning Crimea
    queries = ['"Crimea"', '"Crimée"', '"Krim"']
    quarters = generate_quarters(start_year, end_year)
    articles = []
    seen = set()

    for qi, (qs, qe) in enumerate(quarters):
        label = f"{qs[:4]}Q{(int(qs[4:6])-1)//3+1}"
        print(f"\n  {label}:", end="", flush=True)

        for query in queries:
            results = fetch_gdelt(query, qs, qe)
            new = 0
            for a in results:
                url = a.get("url", "")
                if url in seen:
                    continue
                seen.add(url)
                new += 1
                articles.append({
                    "source_type": "media",
                    "source_api": "gdelt",
                    "url": url,
                    "title": a.get("title", ""),
                    "domain": a.get("domain", ""),
                    "domain_country": get_domain_country(a.get("domain", "")),
                    "date": a.get("seendate", ""),
                    "language": a.get("language", ""),
                    "text": a.get("title", ""),  # GDELT only gives titles
                })
            print(f" +{new}", end="", flush=True)
            time.sleep(0.5)

    print(f"\n\n  Total GDELT articles: {len(articles)}")
    return articles


# ── OpenAlex ───────────────────────────────────────────

OPENALEX_API = "https://api.openalex.org/works"


def fetch_openalex(query: str, from_date: str, page: int) -> tuple[list[dict], int]:
    params = {
        "search": query,
        "filter": f"from_publication_date:{from_date}",
        "sort": "publication_date:desc",
        "per_page": "200",
        "page": str(page),
        "mailto": CONTACT_EMAIL,
    }
    url = OPENALEX_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": f"CrimeaAudit/1.0 (mailto:{CONTACT_EMAIL})"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            total = data.get("meta", {}).get("count", 0)
            return data.get("results", []), total
    except Exception as e:
        print(f"    OpenAlex error: {e}")
        return [], 0


def reconstruct_abstract(inv_index: dict) -> str:
    if not inv_index:
        return ""
    words = {}
    for word, positions in inv_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[k] for k in sorted(words.keys()))


def collect_openalex(start_year: int, end_year: int, max_pages: int = 25) -> list[dict]:
    """Collect all Crimea mentions from OpenAlex."""
    print(f"\n{'='*60}")
    print(f"OpenAlex: Collecting Crimea papers {start_year}-{end_year}")
    print(f"{'='*60}")

    from_date = f"{start_year}-01-01"
    to_date = f"{end_year}-12-31"
    articles = []
    seen_dois = set()

    # Search with broad query
    for query in ["Crimea", "Крым", "Крим"]:
        print(f"\n  Query: '{query}'")
        page = 1
        while page <= max_pages:
            works, total = fetch_openalex(query, from_date, page)
            if not works:
                break

            if page == 1:
                print(f"    Total available: {total}")

            for work in works:
                doi = work.get("doi", "") or ""
                year = work.get("publication_year", 0)

                # Filter to our date range
                if year and (year < start_year or year > end_year):
                    continue

                if doi and doi in seen_dois:
                    continue
                if doi:
                    seen_dois.add(doi)

                title = work.get("title", "") or ""
                abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
                text = f"{title}\n{abstract}" if abstract else title

                journal = ""
                if work.get("primary_location", {}).get("source"):
                    journal = work["primary_location"]["source"].get("display_name", "")

                articles.append({
                    "source_type": "academic",
                    "source_api": "openalex",
                    "url": doi or work.get("id", ""),
                    "title": title,
                    "domain": journal,
                    "domain_country": "",  # journals don't have TLDs
                    "date": str(year),
                    "language": work.get("language", ""),
                    "text": text,
                    "doi": doi,
                    "journal": journal,
                })

            print(f"    Page {page}: +{len(works)} works", flush=True)
            page += 1
            time.sleep(0.2)

    print(f"\n  Total OpenAlex papers: {len(articles)}")
    return articles


# ── Unified pipeline ───────────────────────────────────

def dedup_key(article: dict) -> str:
    """Generate dedup key from title + URL."""
    raw = (article.get("title", "") + article.get("url", "")).lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Unified Crimea sovereignty framing pilot")
    parser.add_argument("--start", type=int, default=2020)
    parser.add_argument("--end", type=int, default=2021)
    parser.add_argument("--skip-gdelt", action="store_true", help="Skip GDELT (faster)")
    parser.add_argument("--skip-academic", action="store_true", help="Skip OpenAlex (faster)")
    parser.add_argument("--max-pages", type=int, default=25, help="Max OpenAlex pages per query")
    args = parser.parse_args()

    clf = SovereigntyClassifier()

    # 1. Collect
    all_articles = []
    if not args.skip_gdelt:
        all_articles.extend(collect_gdelt(args.start, args.end))
    if not args.skip_academic:
        all_articles.extend(collect_openalex(args.start, args.end, args.max_pages))

    # 2. Deduplicate
    seen = {}
    deduped = []
    for a in all_articles:
        key = dedup_key(a)
        if key not in seen:
            seen[key] = True
            deduped.append(a)

    print(f"\n{'='*60}")
    print(f"Collected: {len(all_articles)} → Deduped: {len(deduped)}")

    # 3. Filter to Crimea references only
    crimea_refs = [a for a in deduped if clf.has_crimea_reference(a.get("text", ""))]
    print(f"With Crimea reference: {len(crimea_refs)}")

    # 4. Classify
    results = []
    for a in crimea_refs:
        result = clf.classify(a["text"])
        a["label"] = result.label
        a["confidence"] = round(result.confidence, 3)
        a["ua_score"] = round(result.ua_score, 3)
        a["ru_score"] = round(result.ru_score, 3)
        a["signal_count"] = len(result.signals)
        a["signals"] = [
            {"matched": s.matched, "direction": s.direction,
             "type": s.signal_type, "weight": s.weight}
            for s in result.signals
        ]
        # Drop full text from output (keep it small)
        a.pop("text", None)
        results.append(a)

    # 5. Summary
    by_label = {}
    by_source = {}
    by_year = {}
    by_country = {}
    for r in results:
        l = r["label"]
        by_label[l] = by_label.get(l, 0) + 1
        st = r["source_type"]
        by_source.setdefault(st, {}).setdefault(l, 0)
        by_source[st][l] += 1
        year = r.get("date", "")[:4]
        if year:
            by_year.setdefault(year, {}).setdefault(l, 0)
            by_year[year][l] += 1
        country = r.get("domain_country", "") or "Unknown"
        if l == "russia":
            by_country[country] = by_country.get(country, 0) + 1

    print(f"\n{'='*60}")
    print(f"PILOT RESULTS: {args.start}-{args.end}")
    print(f"{'='*60}")
    print(f"  Total classified: {len(results)}")
    for l, c in sorted(by_label.items(), key=lambda x: -x[1]):
        icon = {"ukraine": "✅", "russia": "❌", "disputed": "⚠️", "no_signal": "·"}.get(l, "?")
        print(f"  {icon} {l}: {c}")

    print(f"\n  By source:")
    for src, labels in by_source.items():
        print(f"    {src}: {labels}")

    print(f"\n  By year:")
    for year in sorted(by_year.keys()):
        print(f"    {year}: {by_year[year]}")

    # Russia-framing by country
    if by_country:
        print(f"\n  Russia-framing articles by domain country:")
        for country, count in sorted(by_country.items(), key=lambda x: -x[1]):
            flag = "  (expected)" if country == "Russia" else " ← SIGNIFICANT" if country and country != "Unknown" else ""
            print(f"    {country or 'Unknown':20s}: {count}{flag}")

    # Non-Russian violators
    non_ru = [r for r in results if r["label"] == "russia" and r.get("domain_country") not in ("Russia", "")]
    if non_ru:
        print(f"\n  🔴 NON-RUSSIAN sources using Russian framing ({len(non_ru)}):")
        for r in non_ru[:20]:
            print(f"    [{r.get('domain_country','?'):10s}] {r['title'][:60]}")
            print(f"    {'':12s} {r['url']}")
            sigs = ", ".join(s["matched"] for s in r["signals"][:3])
            print(f"    {'':12s} Signals: {sigs}")

    # 6. Save
    output = DATA / f"pilot_{args.start}_{args.end}.json"
    with open(output, "w") as f:
        json.dump({
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "period": f"{args.start}-{args.end}",
            "total_collected": len(all_articles),
            "total_deduped": len(deduped),
            "total_with_crimea": len(crimea_refs),
            "total_classified": len(results),
            "by_label": by_label,
            "by_source": by_source,
            "by_year": by_year,
            "by_country_russia_framing": by_country,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {output}")


if __name__ == "__main__":
    main()
