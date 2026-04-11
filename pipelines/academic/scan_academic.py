"""
Academic Publication Sovereignty Scanner

Searches OpenAlex (free, 250M+ papers) and CrossRef (free, DOI metadata)
for academic publications mentioning Crimea, classifies their sovereignty
framing, and flags violators with DOI/URL evidence.

Sources:
  - OpenAlex API (https://docs.openalex.org/) — free, no key needed
  - CrossRef API (https://api.crossref.org/) — free, polite pool

Usage:
    python scripts/scan_academic.py
    python scripts/scan_academic.py --source openalex --start 2010
    python scripts/scan_academic.py --source crossref --start 2014
"""

import argparse
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from sovereignty_classifier import SovereigntyClassifier

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"

OPENALEX_API = "https://api.openalex.org/works"
CROSSREF_API = "https://api.crossref.org/works"

CONTACT_EMAIL = "dobrovolsky94@gmail.com"


def search_openalex(query: str, from_year: int, page: int = 1, per_page: int = 100) -> list[dict]:
    """Search OpenAlex for works matching query."""
    params = {
        "search": query,
        "filter": f"from_publication_date:{from_year}-01-01",
        "sort": "publication_date:desc",
        "per_page": str(per_page),
        "page": str(page),
        "mailto": CONTACT_EMAIL,
    }
    url = OPENALEX_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": f"CrimeaAudit/1.0 (mailto:{CONTACT_EMAIL})"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data.get("results", [])
    except Exception as e:
        print(f"  OpenAlex error: {e}")
        return []


def search_crossref(query: str, from_year: int, offset: int = 0, rows: int = 100) -> list[dict]:
    """Search CrossRef for works matching query."""
    params = {
        "query": query,
        "filter": f"from-pub-date:{from_year}-01-01",
        "sort": "published",
        "order": "desc",
        "rows": str(rows),
        "offset": str(offset),
        "mailto": CONTACT_EMAIL,
    }
    url = CROSSREF_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": f"CrimeaAudit/1.0 (mailto:{CONTACT_EMAIL})"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data.get("message", {}).get("items", [])
    except Exception as e:
        print(f"  CrossRef error: {e}")
        return []


def parse_openalex_work(work: dict) -> dict:
    """Extract relevant fields from an OpenAlex work."""
    title = work.get("title", "") or ""
    doi = work.get("doi", "") or ""
    url = doi or work.get("id", "")
    year = work.get("publication_year", 0)
    journal = ""
    if work.get("primary_location", {}).get("source"):
        journal = work["primary_location"]["source"].get("display_name", "")
    abstract = ""
    if work.get("abstract_inverted_index"):
        # Reconstruct abstract from inverted index
        inv = work["abstract_inverted_index"]
        words = {}
        for word, positions in inv.items():
            for pos in positions:
                words[pos] = word
        abstract = " ".join(words[k] for k in sorted(words.keys()))

    return {
        "title": title,
        "url": url,
        "doi": doi,
        "year": year,
        "journal": journal,
        "abstract": abstract[:500],
        "source_api": "openalex",
    }


def parse_crossref_work(work: dict) -> dict:
    """Extract relevant fields from a CrossRef work."""
    title = ""
    if work.get("title"):
        title = work["title"][0] if work["title"] else ""
    doi = work.get("DOI", "")
    url = f"https://doi.org/{doi}" if doi else work.get("URL", "")
    year = 0
    if work.get("published", {}).get("date-parts"):
        parts = work["published"]["date-parts"][0]
        year = parts[0] if parts else 0
    journal = ""
    if work.get("container-title"):
        journal = work["container-title"][0] if work["container-title"] else ""
    abstract = work.get("abstract", "")[:500]

    return {
        "title": title,
        "url": url,
        "doi": doi,
        "year": year,
        "journal": journal,
        "abstract": abstract,
        "source_api": "crossref",
    }


SEARCH_QUERIES = [
    "Crimea sovereignty",
    "Crimea annexed Ukraine",
    "Crimea Russia territory",
    "Republic of Crimea",
    "Crimean peninsula political status",
    "Simferopol Ukraine Russia",
]


def main():
    parser = argparse.ArgumentParser(description="Academic publication Crimea sovereignty scanner")
    parser.add_argument("--source", choices=["openalex", "crossref", "both"], default="both")
    parser.add_argument("--start", type=int, default=2010, help="Start year (default: 2010)")
    parser.add_argument("--max-pages", type=int, default=3, help="Max pages per query (default: 3)")
    args = parser.parse_args()

    clf = SovereigntyClassifier()
    all_results = []
    seen_dois = set()

    print("Academic Publication Sovereignty Scanner")
    print(f"Source: {args.source} | Period: {args.start}-present")
    print("=" * 60)

    for query in SEARCH_QUERIES:
        print(f"\nQuery: {query}")

        # OpenAlex
        if args.source in ("openalex", "both"):
            for page in range(1, args.max_pages + 1):
                works = search_openalex(query, args.start, page)
                if not works:
                    break

                for work in works:
                    parsed = parse_openalex_work(work)
                    doi = parsed["doi"]
                    if doi and doi in seen_dois:
                        continue
                    if doi:
                        seen_dois.add(doi)

                    # Classify title + abstract
                    text = f"{parsed['title']}\n{parsed['abstract']}"
                    if not clf.has_crimea_reference(text):
                        continue

                    result = clf.classify(text)
                    if result.label == "no_signal":
                        continue

                    parsed["label"] = result.label
                    parsed["confidence"] = round(result.confidence, 3)
                    parsed["ua_score"] = round(result.ua_score, 3)
                    parsed["ru_score"] = round(result.ru_score, 3)
                    parsed["signals"] = [
                        {"matched": s.matched, "label": s.direction}
                        for s in result.signals[:5]
                    ]
                    all_results.append(parsed)

                    icon = {"ukraine": "✅", "russia": "❌", "disputed": "⚠️", "neutral": "—"}.get(result.label, "?")
                    print(f"  {icon} [{result.label:8s}] ({parsed['year']}) {parsed['title'][:65]}")

                time.sleep(0.2)

        # CrossRef
        if args.source in ("crossref", "both"):
            for offset in range(0, args.max_pages * 100, 100):
                works = search_crossref(query, args.start, offset)
                if not works:
                    break

                for work in works:
                    parsed = parse_crossref_work(work)
                    doi = parsed["doi"]
                    if doi and doi in seen_dois:
                        continue
                    if doi:
                        seen_dois.add(doi)

                    text = f"{parsed['title']}\n{parsed['abstract']}"
                    if not clf.has_crimea_reference(text):
                        continue

                    result = clf.classify(text)
                    if result.label == "no_signal":
                        continue

                    parsed["label"] = result.label
                    parsed["confidence"] = round(result.confidence, 3)
                    parsed["ua_score"] = round(result.ua_score, 3)
                    parsed["ru_score"] = round(result.ru_score, 3)
                    parsed["signals"] = [
                        {"matched": s.matched, "label": s.direction}
                        for s in result.signals[:5]
                    ]
                    all_results.append(parsed)

                    icon = {"ukraine": "✅", "russia": "❌", "disputed": "⚠️", "neutral": "—"}.get(result.label, "?")
                    print(f"  {icon} [{result.label:8s}] ({parsed['year']}) {parsed['title'][:65]}")

                time.sleep(0.5)  # CrossRef asks for polite crawling

    # --- Summary ---
    by_label = {}
    by_year = {}
    for r in all_results:
        l = r["label"]
        by_label[l] = by_label.get(l, 0) + 1
        y = str(r.get("year", ""))
        if y:
            if y not in by_year:
                by_year[y] = {"ukraine": 0, "russia": 0, "disputed": 0, "neutral": 0}
            if l in by_year[y]:
                by_year[y][l] += 1

    print(f"\n{'=' * 60}")
    print(f"SCAN COMPLETE: {len(all_results)} papers with sovereignty signals")
    for label, count in sorted(by_label.items()):
        icon = {"ukraine": "✅", "russia": "❌", "disputed": "⚠️", "neutral": "—"}.get(label, "?")
        print(f"  {icon} {label}: {count}")

    if by_year:
        print(f"\n  Year-by-year:")
        for year in sorted(by_year.keys()):
            y = by_year[year]
            total = sum(y.values())
            if total > 0:
                print(f"    {year}: UA={y['ukraine']:3d}  RU={y['russia']:3d}  disputed={y['disputed']:3d}  (total={total})")

    # Flagged
    flagged = [r for r in all_results if r["label"] == "russia"]
    if flagged:
        print(f"\n❌ FLAGGED — {len(flagged)} papers using Russian framing:")
        for r in flagged[:15]:
            print(f"  ({r['year']}) {r['title'][:70]}")
            print(f"    {r['journal'][:40]}  DOI: {r['doi']}")

    # Save
    output = DATA / "academic_framing_results.json"
    with open(output, "w") as f:
        json.dump({
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "period": f"{args.start}-present",
            "sources": args.source,
            "total_papers": len(all_results),
            "by_label": by_label,
            "by_year": by_year,
            "violators": flagged,
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output}")


if __name__ == "__main__":
    main()
