"""
Academic Publication Scanner — Crimea + Religion

Queries the OpenAlex API for academic papers that mention Crimea in
the context of religion (Orthodox Church, patriarchate, diocese,
autocephaly, Chersonesos baptism, mosques, etc.), then classifies
each paper's sovereignty framing using the shared classifier.

Output: pipelines/religious/data/academic_religious.jsonl  (one JSON object per line)

Usage:
    python pipelines/religious/scan_academic.py
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# --- Add shared utilities to import path ---
SHARED_DIR = Path(__file__).resolve().parent.parent / "_shared"
sys.path.insert(0, str(SHARED_DIR))

from sovereignty_classifier import SovereigntyClassifier  # noqa: E402
from sovereignty_signals import CRIMEA_REFERENCE           # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = DATA_DIR / "academic_religious.jsonl"

OPENALEX_API = "https://api.openalex.org/works"
CONTACT_EMAIL = "dobrovolsky94@gmail.com"
USER_AGENT = f"CrimeaAudit/1.0 (mailto:{CONTACT_EMAIL})"

# Per-page maximum that OpenAlex supports
PER_PAGE = 200

# Polite delay between requests (seconds)
REQUEST_DELAY = 0.3

# ---------------------------------------------------------------------------
# Search queries — each is sent as a filter-based search to OpenAlex.
# Strategy: use `default.search` which searches title + abstract.
# ---------------------------------------------------------------------------
SEARCH_QUERIES = [
    # Broad combined queries
    "crimea orthodox",
    "crimea patriarch",
    "crimea orthodox church",
    "crimea diocese",
    "chersonesos baptism",
    "crimea sacred",
    "crimea mosque",
    "crimea autocephaly",
    "crimea religion",
    "crimea church schism",
    "crimea tomos",
    "crimean eparchy",
    "crimea religious freedom",
    "crimea islam tatar",
    "crimea monastery",
    "crimea baptism rus",
    "crimea metropolitan",
]


# ---------------------------------------------------------------------------
# OpenAlex helpers
# ---------------------------------------------------------------------------
def openalex_search(query: str, page: int = 1) -> dict:
    """
    Search OpenAlex works using the free-text `search` parameter.
    Returns the raw JSON response dict (with 'results' and 'meta').
    """
    params = {
        "search": query,
        "per_page": str(PER_PAGE),
        "page": str(page),
        "mailto": CONTACT_EMAIL,
    }
    url = OPENALEX_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  [ERROR] OpenAlex request failed: {e}")
        return {"results": [], "meta": {"count": 0}}


def reconstruct_abstract(inverted_index: dict | None) -> str:
    """Reconstruct a plain-text abstract from OpenAlex's inverted index format."""
    if not inverted_index:
        return ""
    words: dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[k] for k in sorted(words.keys()))


def parse_work(work: dict) -> dict:
    """Extract the fields we care about from a single OpenAlex work."""
    title = (work.get("title") or "").strip()
    doi = (work.get("doi") or "").strip()
    openalex_id = work.get("id", "")
    year = work.get("publication_year") or 0
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))

    journal = ""
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    journal = src.get("display_name", "")

    return {
        "title": title,
        "doi": doi,
        "openalex_id": openalex_id,
        "year": year,
        "journal": journal,
        "abstract_snippet": abstract[:600],
        "source_api": "openalex",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    clf = SovereigntyClassifier()
    seen_ids = set()  # deduplicate by OpenAlex ID
    all_results: list[dict] = []

    print("=" * 70)
    print("Academic Scanner: Crimea + Religion (OpenAlex)")
    print(f"  Queries : {len(SEARCH_QUERIES)}")
    print(f"  Per-page: {PER_PAGE}")
    print(f"  Output  : {OUTPUT_FILE}")
    print("=" * 70)

    for qi, query in enumerate(SEARCH_QUERIES, 1):
        print(f"\n[{qi}/{len(SEARCH_QUERIES)}] Query: \"{query}\"")
        page = 1
        query_hits = 0

        while True:
            data = openalex_search(query, page=page)
            results = data.get("results", [])
            total_count = data.get("meta", {}).get("count", 0)

            if page == 1:
                print(f"  Total results from API: {total_count}")

            if not results:
                break

            for work in results:
                parsed = parse_work(work)
                oid = parsed["openalex_id"]

                # Deduplicate
                if oid in seen_ids:
                    continue
                seen_ids.add(oid)

                # Must mention Crimea somewhere in title or abstract
                text = f"{parsed['title']} {parsed['abstract_snippet']}"
                if not CRIMEA_REFERENCE.search(text):
                    continue

                # Classify sovereignty framing
                result = clf.classify(text)

                parsed["framing_label"] = result.label
                parsed["framing_confidence"] = round(result.confidence, 3)
                parsed["ua_score"] = round(result.ua_score, 3)
                parsed["ru_score"] = round(result.ru_score, 3)
                parsed["signal_count"] = len(result.signals)
                parsed["signals"] = [
                    {"matched": s.matched, "direction": s.direction, "type": s.signal_type}
                    for s in result.signals[:8]
                ]
                parsed["scan_date"] = datetime.now(timezone.utc).isoformat()
                parsed["search_query"] = query

                all_results.append(parsed)
                query_hits += 1

                icon = {
                    "ukraine": "UA",
                    "russia": "RU",
                    "disputed": "??",
                    "no_signal": "..",
                }.get(result.label, "??")
                print(f"    [{icon}] ({parsed['year']}) {parsed['title'][:72]}")

            # Paginate — OpenAlex caps at 10,000 results; we grab up to 3 pages
            if page * PER_PAGE >= min(total_count, 600):
                break
            page += 1
            time.sleep(REQUEST_DELAY)

        print(f"  => {query_hits} Crimea-related papers from this query")
        time.sleep(REQUEST_DELAY)

    # ------------------------------------------------------------------
    # Save JSONL
    # ------------------------------------------------------------------
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for rec in all_results:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nSaved {len(all_results)} records to {OUTPUT_FILE}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    label_counts = Counter(r["framing_label"] for r in all_results)
    journal_counts = Counter(r["journal"] for r in all_results if r["journal"])
    year_counts = Counter(r["year"] for r in all_results if r["year"])

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total papers found: {len(all_results)}")
    print(f"Unique OpenAlex IDs seen (including non-Crimea): {len(seen_ids)}")

    print(f"\nFraming breakdown:")
    for label in ["ukraine", "russia", "disputed", "no_signal"]:
        ct = label_counts.get(label, 0)
        pct = f"({100*ct/len(all_results):.1f}%)" if all_results else ""
        icon = {"ukraine": "UA-framing", "russia": "RU-framing", "disputed": "disputed", "no_signal": "no signal"}.get(label, label)
        print(f"  {icon:14s}: {ct:4d} {pct}")

    print(f"\nTop 15 journals:")
    for jnl, ct in journal_counts.most_common(15):
        print(f"  {ct:3d}  {jnl}")

    print(f"\nYear distribution (top 15):")
    for yr, ct in sorted(year_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {yr}: {ct}")

    # Flagged papers (Russia-framing)
    flagged = [r for r in all_results if r["framing_label"] == "russia"]
    if flagged:
        print(f"\nFLAGGED — {len(flagged)} papers with Russia-framing:")
        for r in flagged[:20]:
            print(f"  ({r['year']}) {r['title'][:75]}")
            print(f"         Journal: {r['journal'][:50]}  DOI: {r['doi']}")
            sigs = ", ".join(s["matched"] for s in r["signals"][:3])
            print(f"         Signals: {sigs}")

    # Ukraine-framing highlights
    ua_papers = [r for r in all_results if r["framing_label"] == "ukraine"]
    if ua_papers:
        print(f"\nUkraine-framing papers ({len(ua_papers)}):")
        for r in ua_papers[:20]:
            print(f"  ({r['year']}) {r['title'][:75]}")
            if r['journal']:
                print(f"         Journal: {r['journal'][:50]}")


if __name__ == "__main__":
    main()
