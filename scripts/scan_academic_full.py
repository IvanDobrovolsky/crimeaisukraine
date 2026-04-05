"""
Full OpenAlex scan — get ALL papers mentioning Crimea and cities.
Uses cursor pagination to get beyond the 25-page limit.

Usage:
    python scripts/scan_academic_full.py
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from sovereignty_classifier import SovereigntyClassifier

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
CONTACT = "dobrovolsky94@gmail.com"
API = "https://api.openalex.org/works"


def reconstruct_abstract(inv_index):
    if not inv_index:
        return ""
    words = {}
    for word, positions in inv_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[k] for k in sorted(words.keys()))


def fetch_all_pages(query, from_date="2010-01-01", to_date="2026-12-31"):
    """Fetch ALL results using cursor pagination."""
    results = []
    cursor = "*"
    page = 0

    while cursor:
        params = {
            "search": query,
            "filter": f"from_publication_date:{from_date},to_publication_date:{to_date}",
            "per_page": "200",
            "cursor": cursor,
            "mailto": CONTACT,
        }
        url = API + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": f"CrimeaAudit/1.0 (mailto:{CONTACT})"})

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

        works = data.get("results", [])
        if not works:
            break

        results.extend(works)
        cursor = data.get("meta", {}).get("next_cursor")
        page += 1

        if page % 10 == 0:
            total_available = data.get("meta", {}).get("count", "?")
            print(f"  Page {page}: {len(results)} collected (of {total_available})")

        time.sleep(0.15)

    return results


def main():
    clf = SovereigntyClassifier()

    queries = ["Crimea", "Simferopol", "Sevastopol", "Yalta", "Kerch"]

    all_papers = {}  # DOI -> paper
    output_path = DATA / "academic_full.jsonl"

    # Resume support
    done_dois = set()
    if output_path.exists():
        with open(output_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    doi = r.get("doi", "")
                    if doi:
                        done_dois.add(doi)
                except:
                    pass
        print(f"Resume: {len(done_dois)} already processed")

    outf = open(output_path, "a")
    stats = {"ukraine": 0, "russia": 0, "disputed": 0, "no_signal": 0, "skipped": 0}
    total_fetched = 0

    for query in queries:
        print(f"\nQuery: '{query}'")
        works = fetch_all_pages(query)
        print(f"  Total results: {len(works)}")

        for w in works:
            doi = w.get("doi", "") or ""
            openalex_id = w.get("id", "")

            # Dedup
            key = doi or openalex_id
            if key in done_dois or key in all_papers:
                stats["skipped"] += 1
                continue
            all_papers[key] = True
            if doi:
                done_dois.add(doi)

            title = w.get("title", "") or ""
            abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
            year = w.get("publication_year", 0)
            journal = ""
            if w.get("primary_location", {}).get("source"):
                journal = w["primary_location"]["source"].get("display_name", "")
            language = w.get("language", "")

            text = f"{title}\n{abstract}" if abstract else title

            # Classify
            if clf.has_crimea_reference(text):
                result = clf.classify(text)
                label = result.label
                signals = [
                    {"matched": s.matched, "direction": s.direction, "type": s.signal_type}
                    for s in result.signals[:5]
                ]
                ua_score = round(result.ua_score, 3)
                ru_score = round(result.ru_score, 3)
            else:
                label = "no_crimea_ref"
                signals = []
                ua_score = 0
                ru_score = 0

            stats[label] = stats.get(label, 0) + 1

            row = {
                "doi": doi,
                "openalex_id": openalex_id,
                "title": title,
                "abstract": abstract[:500] if abstract else "",
                "year": year,
                "journal": journal,
                "language": language,
                "label": label,
                "ua_score": ua_score,
                "ru_score": ru_score,
                "signals": signals,
            }

            outf.write(json.dumps(row, ensure_ascii=False) + "\n")
            outf.flush()
            total_fetched += 1

            if total_fetched % 1000 == 0:
                print(f"  Processed: {total_fetched} | {stats}")

    outf.close()

    print(f"\n{'='*60}")
    print(f"FULL ACADEMIC SCAN COMPLETE")
    print(f"  Total fetched: {total_fetched}")
    print(f"  Skipped (dedup): {stats['skipped']}")
    print(f"  By label: {stats}")

    # Summary by year
    by_year = {}
    with open(output_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                y = str(r.get("year", ""))
                label = r.get("label", "")
                if y and label in ("ukraine", "russia", "disputed"):
                    if y not in by_year:
                        by_year[y] = {"ukraine": 0, "russia": 0, "disputed": 0}
                    by_year[y][label] += 1
            except:
                pass

    print(f"\nBy year:")
    for y in sorted(by_year.keys()):
        d = by_year[y]
        total = sum(d.values())
        ru_pct = round(d["russia"] / max(total, 1) * 100)
        print(f"  {y}: UA={d['ukraine']:4d} RU={d['russia']:4d} ({ru_pct}%) DISP={d['disputed']}")

    # Save summary
    with open(DATA / "academic_full_summary.json", "w") as f:
        json.dump({
            "total_processed": total_fetched,
            "by_label": stats,
            "by_year": by_year,
        }, f, indent=2)
    print(f"\nSaved summary to data/academic_full_summary.json")


if __name__ == "__main__":
    main()
